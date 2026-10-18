// Rasterize scripts/site_tools/overviews/*.svg (with the site's fonts) to PNG; then run overview_diagrams.py webp <outdir>.
// Usage: node scripts/site_tools/render_overviews.mjs <outdir> [chromium executable]
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const here = path.dirname(new URL(import.meta.url).pathname);
const root = path.resolve(here, '../..');
const out = process.argv[2] || path.join(here, 'overviews', 'png');
fs.mkdirSync(out, { recursive: true });
// fonts are inlined as data URLs: a page set with setContent cannot load file:// URLs
const font = (f) => 'data:font/woff2;base64,' + fs.readFileSync(path.join(root, 'assets/fonts', f)).toString('base64');
const fonts = `
@font-face{font-family:Geist;src:url(${font('Geist-Variable.woff2')}) format("woff2");font-weight:100 900}
@font-face{font-family:"Bricolage Grotesque";src:url(${font('BricolageGrotesque-Variable.woff2')}) format("woff2");font-weight:200 800}
html,body{margin:0;background:#fff}`;
const browser = await chromium.launch(process.argv[3] ? { executablePath: process.argv[3] } : {});
const page = await browser.newPage({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
for (const f of fs.readdirSync(path.join(here, 'overviews')).filter((f) => f.endsWith('.svg'))) {
  const svg = fs.readFileSync(path.join(here, 'overviews', f), 'utf8');
  await page.setContent(`<!doctype html><html><head><style>${fonts}</style></head><body>${svg}</body></html>`, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await page.screenshot({ path: path.join(out, f.replace('.svg', '.png')), clip: { x: 0, y: 0, width: 1280, height: 800 } });
  console.log(f);
}
await browser.close();
