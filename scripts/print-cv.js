/**
 * print-cv.js — render the Jekyll CV page to PDF using Puppeteer.
 *
 * Expects the Jekyll site to already be built (_site/) and served locally.
 * Usage (started by the GitHub Actions workflow, or manually):
 *
 *   python3 -m http.server 4000 --directory _site &
 *   node scripts/print-cv.js
 */

const puppeteer = require("puppeteer");
const path = require("path");
const fs = require("fs");

const CV_URL = "http://localhost:4000/cv/";
const OUT_DIR = path.join(__dirname, "..", "assets", "pdf");
const OUT_FILE = path.join(OUT_DIR, "cv.pdf");

// CSS injected at print time to produce a clean, printer-friendly PDF.
// Hides interactive UI chrome; forces white background; keeps badge colours.
const PRINT_CSS = `
  /* Hide navigation and UI chrome */
  nav.navbar,
  footer,
  #back-to-top,
  #light-toggle,
  .theme-toggle,
  #cv-pdf-download,
  .social-icons,
  .header-bar {
    display: none !important;
  }

  /* Reset page chrome */
  body {
    background: #ffffff !important;
    padding-top: 0 !important;
    margin-top: 0 !important;
  }

  /* Readable link colours */
  a {
    color: #1a1a1a !important;
    text-decoration: none !important;
  }

  /* cv-year badge: keep colour in PDF */
  .cv-year {
    background-color: #2698ba !important;
    color: #ffffff !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  /* Sensible table layout */
  table {
    width: 100%;
    border-collapse: collapse;
    page-break-inside: auto;
  }
  tr { page-break-inside: avoid; page-break-after: auto; }
  td, th { padding: 4px 8px; }

  /* Prevent orphaned headings */
  h2, h3 { page-break-after: avoid; }

  /* Tighten up vertical whitespace for print */
  .container, .container-md {
    max-width: 100% !important;
    padding: 0 1cm !important;
  }
`;

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
    headless: "new",
  });

  try {
    const page = await browser.newPage();

    // Set a print-like viewport
    await page.setViewport({ width: 794, height: 1123 });

    console.log(`Navigating to ${CV_URL} …`);
    await page.goto(CV_URL, { waitUntil: "networkidle0", timeout: 30000 });

    // Give webfonts a moment to paint
    await new Promise((r) => setTimeout(r, 1500));

    // Inject print-friendly overrides
    await page.addStyleTag({ content: PRINT_CSS });

    console.log(`Generating PDF → ${OUT_FILE}`);
    await page.pdf({
      path: OUT_FILE,
      format: "A4",
      margin: { top: "1.5cm", right: "1.5cm", bottom: "1.5cm", left: "1.5cm" },
      printBackground: true,
      displayHeaderFooter: false,
    });

    console.log("Done.");
  } finally {
    await browser.close();
  }
})();
