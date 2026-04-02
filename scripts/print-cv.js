/**
 * print-cv.js — render the Jekyll CV page to PDF using Puppeteer.
 *
 * Expects the Jekyll site to already be built (_site/) and served locally.
 * Usage (started by the GitHub Actions workflow, or manually):
 *
 *   python3 -m http.server 4000 --directory _site &
 *   node scripts/print-cv.js
 *
 * Compact print styles live in assets/css/cv-print.css and are injected
 * at render time — the live web page is completely unaffected.
 */

const puppeteer = require("puppeteer");
const path = require("path");
const fs = require("fs");

const CV_URL = "http://localhost:4000/cv/";
const OUT_DIR = path.join(__dirname, "..", "assets", "pdf");
const OUT_FILE = path.join(OUT_DIR, "cv.pdf");
const PRINT_CSS_FILE = path.join(__dirname, "..", "assets", "css", "cv-print.css");

(async () => {
  fs.mkdirSync(OUT_DIR, { recursive: true });

  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--disable-setuid-sandbox"],
    headless: "new",
  });

  try {
    const page = await browser.newPage();

    // A4 width in px at 96 dpi ≈ 794px — keeps Bootstrap md breakpoint active
    // so col-md-2 / col-md-10 stay side-by-side (our print CSS also forces this).
    await page.setViewport({ width: 794, height: 1123 });

    console.log(`Navigating to ${CV_URL} …`);
    await page.goto(CV_URL, { waitUntil: "networkidle0", timeout: 30000 });

    // Give web fonts a moment to finish painting
    await new Promise((r) => setTimeout(r, 1500));

    // Inject compact print styles from the standalone CSS file
    await page.addStyleTag({ path: PRINT_CSS_FILE });

    console.log(`Generating PDF → ${OUT_FILE}`);
    await page.pdf({
      path: OUT_FILE,
      format: "A4",
      // Margins are set here (not via @page CSS) to avoid Puppeteer/CSS conflicts.
      // Bottom is slightly larger to make room for the page-number footer.
      margin: { top: "1.1cm", right: "1.4cm", bottom: "1.6cm", left: "1.4cm" },
      printBackground: false,
      displayHeaderFooter: true,
      headerTemplate: "<span></span>",
      footerTemplate: `
        <div style="
          font-family: Arial, sans-serif;
          font-size: 9pt;
          color: #666666;
          width: 100%;
          text-align: right;
          padding-right: 1.4cm;
          box-sizing: border-box;
        ">
          <span class="pageNumber"></span>&thinsp;/&thinsp;<span class="totalPages"></span>
        </div>`,
    });

    console.log("Done.");
  } finally {
    await browser.close();
  }
})();
