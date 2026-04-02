#!/usr/bin/env python3
"""
fetch_publications.py — sync publications from ORCID + Google Scholar → papers.bib

Strategy:
  1. Fetch the list of DOIs from ORCID (reliable, authenticated public API).
  2. For each DOI, enrich metadata from Crossref (best source for titles,
     author lists, journal names, volumes, pages).
  3. Optionally supplement with Google Scholar to catch preprints / conference
     papers that may not be on ORCID yet.
  4. Merge with the existing papers.bib: entries whose DOI is already present
     are left completely untouched (preserving manually added fields like
     `abbr`, `annotation`, `selected`, etc.). Only genuinely new papers are
     appended.
  5. Write the merged database back to papers.bib, sorted year-descending.

Dependencies (pip install):
    requests
    scholarly          # for Google Scholar; install once with: pip install scholarly
    bibtexparser       # v1.x (pip install "bibtexparser<2")

Usage:
    python scripts/fetch_publications.py           # normal run
    python scripts/fetch_publications.py --dry-run # print new entries, don't write
"""

import argparse
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import requests

# ── Configuration ────────────────────────────────────────────────────────────

GOOGLE_SCHOLAR_ID = "dU-qQwQAAAAJ"
ORCID_ID          = "0000-0001-7845-1088"

BIB_FILE = Path(__file__).parent.parent / "_bibliography" / "papers.bib"

# Polite delay between API calls (seconds)
API_DELAY = 0.8

# Email for Crossref "polite pool" (faster rate limits when provided)
CROSSREF_EMAIL = "hilda.sandstroem@tum.de"

# Map full journal names → BibTeX abbr used in al-folio badge pills.
# Add entries here as needed; missing journals get no abbr (set manually later).
JOURNAL_ABBR = {
    "Nature": "Nature",
    "Science": "Science",
    "Science Advances": "Sci. Adv.",
    "Proceedings of the National Academy of Sciences": "PNAS",
    "Proceedings of the National Academy of Sciences of the United States of America": "PNAS",
    "ACS Earth and Space Chemistry": "ACSESC",
    "The Journal of Physical Chemistry A": "JPCA",
    "The Journal of Physical Chemistry B": "JPCB",
    "The Journal of Physical Chemistry C": "JPCC",
    "Physical Chemistry Chemical Physics": "PCCP",
    "Advanced Science": "Adv. Sci.",
    "Atmospheric Chemistry and Physics": "ACP",
    "Geoscientific Model Development": "GMD",
    "Astrobiology": "Astrobiology",
    "Diagnostic Microbiology and Infectious Disease": "DMID",
    "QRB Discovery": "QRB",
    "ACS ES&T Air": "ACS ES&T Air",
    "Journal of Chemical Theory and Computation": "JCTC",
    "The Journal of Chemical Physics": "JCP",
    "Journal of Chemical Physics": "JCP",
    "Journal of the American Chemical Society": "JACS",
    "Angewandte Chemie International Edition": "Angew. Chem.",
    "Chemistry – A European Journal": "Chem. Eur. J.",
    "ChemPhysChem": "ChemPhysChem",
    "Faraday Discussions": "Faraday Discuss.",
    "npj Computational Materials": "npj Comput. Mater.",
    "ACS Central Science": "ACS Cent. Sci.",
    "Journal of Computational Chemistry": "J. Comput. Chem.",
    "International Journal of Quantum Chemistry": "Int. J. Quantum Chem.",
}

# ── BibTeX utilities ──────────────────────────────────────────────────────────

def _ascii_fold(text: str) -> str:
    """Strip diacritics and non-ASCII for BibTeX key generation."""
    nfd = unicodedata.normalize("NFD", text)
    return "".join(c for c in nfd if unicodedata.category(c) != "Mn" and ord(c) < 128)


def make_bib_key(author_str: str, year: str, journal: str) -> str:
    """Generate a key like 'Sandstrom2024AdvSci'."""
    first_author = author_str.split(" and ")[0].strip()
    # Handle "Family, Given" or "Given Family" formats
    if "," in first_author:
        family = first_author.split(",")[0].strip()
    else:
        parts = first_author.split()
        family = parts[-1] if parts else first_author
    family = _ascii_fold(family).replace(" ", "")

    # Journal key: capitalised initials of each significant word
    stop = {"and", "of", "the", "in", "for", "on", "a", "an", "&"}
    words = re.sub(r"[^a-zA-Z\s]", " ", journal).split()
    jkey = "".join(w[0].upper() for w in words if w.lower() not in stop)[:5]

    return f"{family}{year}{jkey}"


def _unique_key(desired: str, existing_keys: set) -> str:
    """Append a letter suffix to make the key unique."""
    if desired not in existing_keys:
        return desired
    for suffix in "abcdefghijklmnopqrstuvwxyz":
        candidate = desired + suffix
        if candidate not in existing_keys:
            return candidate
    return desired + "_dup"


def normalize_doi(doi: str) -> Optional[str]:
    """Lowercase, strip URL prefix."""
    if not doi:
        return None
    doi = doi.strip().lower()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi)
    return doi


# ── Load / write papers.bib ───────────────────────────────────────────────────

def load_existing_bib(path: Path) -> Tuple[List[dict], Dict[str, dict]]:
    """
    Returns (all_entries, doi_index) where doi_index maps normalised DOI → entry.
    Entries without a DOI are included in all_entries but not in doi_index.
    """
    try:
        import bibtexparser
    except ImportError:
        sys.exit("Install bibtexparser:  pip install 'bibtexparser<2'")

    if not path.exists():
        return [], {}

    with path.open(encoding="utf-8") as fh:
        db = bibtexparser.load(fh)

    doi_index = {}
    for entry in db.entries:
        doi = normalize_doi(entry.get("doi", ""))
        if doi:
            doi_index[doi] = entry
    return db.entries, doi_index


def write_bib(entries: List[dict], path: Path) -> None:
    try:
        import bibtexparser
        from bibtexparser.bwriter import BibTexWriter
        from bibtexparser.bibdatabase import BibDatabase
    except ImportError:
        sys.exit("Install bibtexparser:  pip install 'bibtexparser<2'")

    db = BibDatabase()
    db.entries = entries

    writer = BibTexWriter()
    writer.indent = "  "
    writer.order_entries_by = None   # preserve order we set manually
    writer.add_trailing_comma = False

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        fh.write(writer.write(db))
    print(f"Written {len(entries)} entries → {path}")


# ── Crossref ──────────────────────────────────────────────────────────────────

def crossref_lookup(doi: str) -> Optional[dict]:
    """Fetch full work metadata from Crossref by DOI."""
    url = f"https://api.crossref.org/works/{doi}"
    headers = {"User-Agent": f"fetch_publications/1.0 (mailto:{CROSSREF_EMAIL})"}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json().get("message", {})
    except Exception as exc:
        print(f"  [Crossref] {doi}: {exc}")
        return None


def parse_crossref(msg: dict) -> dict:
    """Convert a Crossref message dict into a flat metadata dict."""
    # Title
    title_list = msg.get("title", [])
    title = title_list[0] if title_list else ""

    # Authors — "Given Family" format for BibTeX
    authors = []
    for a in msg.get("author", []):
        given  = a.get("given", "").strip()
        family = a.get("family", "").strip()
        if given and family:
            authors.append(f"{given} {family}")
        elif family:
            authors.append(family)
    author_str = " and ".join(authors)

    # Journal
    container = msg.get("container-title", [])
    journal = container[0] if container else ""

    # Year
    pub_date = msg.get("published", msg.get("published-print", msg.get("published-online", {})))
    date_parts = pub_date.get("date-parts", [[None]])
    year = str(date_parts[0][0]) if date_parts and date_parts[0] else ""

    # Volume, pages, DOI
    volume = str(msg.get("volume", ""))
    pages  = msg.get("page", "")
    doi    = msg.get("DOI", "")

    # arXiv link from relation or alternative-id
    arxiv = ""
    for ref in msg.get("relation", {}).get("has-preprint", []):
        if "arxiv" in ref.get("id", "").lower():
            arxiv = re.sub(r".*arxiv\.org/(abs/)?", "", ref["id"])
            break

    return {
        "title":   title,
        "author":  author_str,
        "journal": journal,
        "year":    year,
        "volume":  volume,
        "pages":   pages,
        "doi":     doi,
        "arxiv":   arxiv,
    }


# ── ORCID ─────────────────────────────────────────────────────────────────────

def fetch_orcid_dois(orcid_id: str) -> List[str]:
    """Return all DOIs listed on the ORCID profile."""
    url = f"https://pub.orcid.org/v3.0/{orcid_id}/works"
    headers = {"Accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
    except Exception as exc:
        print(f"[ORCID] Failed to fetch works: {exc}")
        return []

    dois = []
    for group in r.json().get("group", []):
        for summary in group.get("work-summary", []):
            for ext_id in summary.get("external-ids", {}).get("external-id", []):
                if ext_id.get("external-id-type") == "doi":
                    doi = normalize_doi(ext_id.get("external-id-value", ""))
                    if doi and doi not in dois:
                        dois.append(doi)
    print(f"[ORCID] Found {len(dois)} DOIs")
    return dois


# ── Google Scholar ────────────────────────────────────────────────────────────

def fetch_scholar_dois(scholar_id: str) -> List[str]:
    """
    Try to pull DOIs from Google Scholar.  Scholar aggressively rate-limits
    automated access, so failures are caught and logged rather than fatal.
    Returns a (possibly empty) list of DOIs not already known.
    """
    try:
        from scholarly import scholarly as sch
    except ImportError:
        print("[Scholar] scholarly not installed — skipping.  pip install scholarly")
        return []

    print("[Scholar] Fetching author profile (may be slow / blocked) …")
    try:
        author = sch.search_author_id(scholar_id)
        sch.fill(author, sections=["publications"])
    except Exception as exc:
        print(f"[Scholar] Failed to fetch author: {exc}")
        return []

    dois = []
    for pub in author.get("publications", []):
        try:
            sch.fill(pub)
            time.sleep(API_DELAY)
        except Exception:
            pass
        doi = normalize_doi(pub.get("bib", {}).get("doi", ""))
        if doi and doi not in dois:
            dois.append(doi)

    print(f"[Scholar] Resolved {len(dois)} DOIs")
    return dois


# ── Build new BibTeX entry ────────────────────────────────────────────────────

def build_entry(meta: dict, existing_keys: Set[str]) -> dict:
    """Turn Crossref metadata into an al-folio–ready BibTeX entry dict."""
    doi  = normalize_doi(meta["doi"])
    year = meta.get("year", "")
    journal = meta.get("journal", "")

    key = _unique_key(
        make_bib_key(meta.get("author", "Unknown"), year, journal),
        existing_keys,
    )
    existing_keys.add(key)

    entry = {
        "ENTRYTYPE":    "article",
        "ID":           key,
        "author":       meta.get("author", ""),
        "title":        meta.get("title", ""),
        "journal":      journal,
        "year":         year,
        "doi":          doi or "",
        "html":         f"https://doi.org/{doi}" if doi else "",
        "bibtex_show":  "true",
        "dimensions":   "true",
    }
    if meta.get("volume"):
        entry["volume"] = meta["volume"]
    if meta.get("pages"):
        entry["pages"] = meta["pages"]
    if meta.get("arxiv"):
        entry["arxiv"] = meta["arxiv"]

    abbr = JOURNAL_ABBR.get(journal, "")
    if abbr:
        entry["abbr"] = abbr

    return entry


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print new entries without writing to disk")
    parser.add_argument("--no-scholar", action="store_true",
                        help="Skip Google Scholar (faster; use if Scholar blocks)")
    args = parser.parse_args()

    # 1. Load what we already have
    existing_entries, doi_index = load_existing_bib(BIB_FILE)
    existing_keys = {e["ID"] for e in existing_entries}
    print(f"Loaded {len(existing_entries)} existing entries "
          f"({len(doi_index)} with DOIs)")

    # 2. Collect DOIs from ORCID + Scholar
    new_dois = []  # type: List[str]
    for doi in fetch_orcid_dois(ORCID_ID):
        if doi not in doi_index:
            new_dois.append(doi)

    if not args.no_scholar:
        for doi in fetch_scholar_dois(GOOGLE_SCHOLAR_ID):
            if doi not in doi_index and doi not in new_dois:
                new_dois.append(doi)

    print(f"\nNew DOIs to add: {len(new_dois)}")
    if not new_dois:
        print("Nothing new — papers.bib is up to date.")
        return

    # 3. Enrich each new DOI via Crossref and build entries
    new_entries = []
    for doi in new_dois:
        print(f"  Crossref → {doi} …")
        msg = crossref_lookup(doi)
        time.sleep(API_DELAY)
        if not msg:
            print(f"    [!] Crossref returned nothing for {doi} — skipping")
            continue
        meta = parse_crossref(msg)
        meta["doi"] = doi   # use normalised form
        entry = build_entry(meta, existing_keys)
        new_entries.append(entry)
        print(f"    ✓  {entry['ID']}: {meta['title'][:60]}")

    if args.dry_run:
        print("\n── Dry-run output ──────────────────────────────────────")
        try:
            import bibtexparser
            from bibtexparser.bwriter import BibTexWriter
            from bibtexparser.bibdatabase import BibDatabase
            db = BibDatabase()
            db.entries = new_entries
            writer = BibTexWriter()
            writer.indent = "  "
            print(writer.write(db))
        except ImportError:
            import pprint
            pprint.pprint(new_entries)
        return

    # 4. Merge: new entries first (most recent), then existing
    # Sort new entries by year descending before prepending
    new_entries.sort(key=lambda e: int(e.get("year", 0)), reverse=True)
    merged = new_entries + existing_entries

    # 5. Write back
    write_bib(merged, BIB_FILE)
    print(f"\nDone. Added {len(new_entries)} new publication(s).")


if __name__ == "__main__":
    main()
