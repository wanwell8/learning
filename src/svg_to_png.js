// Rasterize SVG files to high-DPI PNGs using Playwright (chromium).
const path = require('path');
const fs = require('fs');
const { chromium } = require('/opt/node22/lib/node_modules/playwright');

const FIGS = [
  { svg: 'figures/figure_2_envelopes.svg',   png: 'figures/figure_2_envelopes.png',   w: 1200, h: 760 },
  { svg: 'figures/figure_3_sensitivity.svg', png: 'figures/figure_3_sensitivity.png', w: 1100, h: 640 },
  { svg: 'figures/figure_4_convergence.svg', png: 'figures/figure_4_convergence.png', w: 1200, h: 580 },
  { svg: 'figures/figure_5_heatmap.svg',     png: 'figures/figure_5_heatmap.png',     w: 1040, h: 760 },
];

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ deviceScaleFactor: 2 });
  for (const f of FIGS) {
    const page = await ctx.newPage();
    await page.setViewportSize({ width: f.w, height: f.h });
    const svg = fs.readFileSync(f.svg, 'utf8');
    const html = `<!doctype html><html><body style="margin:0;padding:0;background:#fff;">${svg}</body></html>`;
    await page.setContent(html, { waitUntil: 'load' });
    // ensure svg fills viewport
    await page.evaluate(() => {
      const svg = document.querySelector('svg');
      svg.setAttribute('width', '100%');
      svg.setAttribute('height', '100%');
      document.body.style.width = '100vw';
      document.body.style.height = '100vh';
    });
    await page.screenshot({ path: f.png, omitBackground: false, fullPage: false });
    await page.close();
    const sz = fs.statSync(f.png).size;
    console.log(`[ok] ${f.png}  (${(sz/1024).toFixed(1)} KB)`);
  }
  await browser.close();
})();
