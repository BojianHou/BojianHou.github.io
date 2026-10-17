// Screenshots of the built site at desktop and phone widths, plus basic layout checks.
// Usage: node scripts/site_tools/screens.mjs <outdir>   (expects the site served at http://localhost:4000)
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const out = process.argv[2] || 'screens';
fs.mkdirSync(path.join(out, 'screens'), { recursive: true });
const base = 'http://localhost:4000';
const pages = ['/', '/publications/', '/news/', '/awards/', '/services/', '/resume/'];
const viewports = [
  { name: 'desktop', width: 1280, height: 800 },
  { name: 'phone', width: 390, height: 844 },
];
const report = [];
const browser = await chromium.launch();
for (const vp of viewports) {
  for (const scheme of ['light', 'dark']) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, colorScheme: scheme, deviceScaleFactor: 1 });
    const page = await ctx.newPage();
    const errors = [];
    page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
    page.on('pageerror', (e) => errors.push(String(e)));
    for (const p of pages) {
      if (scheme === 'dark' && !['/', '/publications/'].includes(p)) continue;
      const resp = await page.goto(base + p, { waitUntil: 'networkidle' });
      await page.waitForTimeout(400);
      const slug = (p === '/' ? 'home' : p.replace(/\//g, '')) + `-${vp.name}${scheme === 'dark' ? '-dark' : ''}`;
      await page.screenshot({ path: path.join(out, 'screens', slug + '-fold.png') });
      await page.screenshot({ path: path.join(out, 'screens', slug + '-full.png'), fullPage: true });
      const metrics = await page.evaluate(() => ({
        overflowX: document.documentElement.scrollWidth > window.innerWidth + 1,
        scrollWidth: document.documentElement.scrollWidth,
        height: document.documentElement.scrollHeight,
        brokenImages: [...document.images].filter((i) => i.complete && i.naturalWidth === 0).map((i) => i.getAttribute('src')),
        articles: document.querySelectorAll('article.pub').length,
        title: document.title,
      }));
      report.push({ page: p, viewport: vp.name, scheme, status: resp && resp.status(), ...metrics, errors: [...errors] });
      errors.length = 0;
    }
    if (scheme === 'light') {
      // exercise the topic filter and the news toggle
      await page.goto(base + '/publications/#topic=llm', { waitUntil: 'networkidle' });
      await page.waitForTimeout(300);
      const visible = await page.evaluate(() => [...document.querySelectorAll('article.pub')].filter((a) => !a.hidden && a.offsetParent !== null).length);
      await page.screenshot({ path: path.join(out, 'screens', `publications-${vp.name}-filter-llm.png`), fullPage: false });
      report.push({ check: 'filter #topic=llm', viewport: vp.name, visible });
      await page.goto(base + '/', { waitUntil: 'networkidle' });
      const before = await page.evaluate(() => document.querySelectorAll('.news-item:not([hidden])').length);
      const btn = await page.$('.news-toggle');
      if (btn) await btn.click();
      const after = await page.evaluate(() => document.querySelectorAll('.news-item:not([hidden])').length);
      report.push({ check: 'news toggle', viewport: vp.name, before, after });
    }
    await ctx.close();
  }
}
await browser.close();
fs.writeFileSync(path.join(out, 'screens_report.json'), JSON.stringify(report, null, 1));
console.log(JSON.stringify(report, null, 1));
