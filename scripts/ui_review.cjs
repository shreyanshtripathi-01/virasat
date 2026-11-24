/* Development-only browser review. No JavaScript from this file is served. */
const { chromium } = require('playwright-core');
const fs = require('node:fs');
const path = require('node:path');
const base = process.env.UI_BASE || 'http://127.0.0.1:8003';
const out = process.env.UI_OUT || 'docs/ui_review/after-phase15';
const issues = [];
const sizes = [[360, 740], [768, 1024], [1366, 768]];
const routes = [
  ['home', '/'], ['browse', '/products/'],
  ['detail', '/product/1/madhubani-lotus-wall-painting/'],
  ['login', '/accounts/login/'], ['register', '/accounts/register/'],
  ['craft', '/craft/madhubani/'], ['category', '/category/accessories/'],
  ['artisan', '/artisans/3/'], ['about', '/about/'], ['impact', '/impact/'],
  ['offline', '/offline/'], ['filtered', '/products/?craft=1&verified_only=on&sort=price_asc'],
  ['empty', '/products/?q=no-such-piece'],
];
async function inspect(page, name, width) {
  const result = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth,
    broken: [...document.images].filter(i => i.complete && !i.naturalWidth).map(i => i.src),
    ids: [...document.querySelectorAll('[id]')].map(e => e.id),
  }));
  if (result.scroll > width + 1) issues.push(`${name}: overflow ${result.scroll}/${width}`);
  if (result.broken.length) issues.push(`${name}: broken images ${result.broken}`);
  if (new Set(result.ids).size !== result.ids.length) issues.push(`${name}: duplicate IDs`);
}
(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome-stable', headless: true, args: ['--no-sandbox'] });
  for (const [width, height] of sizes) {
    const context = await browser.newContext({ viewport: { width, height }, serviceWorkers: 'block' });
    const page = await context.newPage();
    page.on('pageerror', error => issues.push(error.message));
    for (const [name, route] of routes) {
      const response = await page.goto(base + route, { waitUntil: 'networkidle' });
      if (response.status() !== 200) issues.push(`${name}: HTTP ${response.status()}`);
      await page.evaluate(() => document.fonts.ready);
      await page.evaluate(async () => {
        for (const image of document.images) image.loading = 'eager';
        await Promise.all([...document.images].map(image => image.decode().catch(() => {})));
      });
      await inspect(page, `${name}-${width}`, width);
      await page.screenshot({ path: path.join(out, `${name}-${width}.png`), fullPage: true });
      if (name === 'home') await page.screenshot({ path: path.join(out, `home-viewport-${width}.png`) });
      console.log(`${name} ${width}: HTTP ${response.status()}`);
    }
    if (width === 360) {
      await page.goto(base + '/products/');
      await page.getByRole('button', { name: 'Filters', exact: true }).click();
      await page.locator('#filterDrawer.show').waitFor();
      await page.screenshot({ path: path.join(out, 'filters-open-360.png') });
      await page.getByRole('button', { name: 'Close filters' }).click();
      await page.locator('#filterDrawer.show').waitFor({ state: 'hidden' });
      await page.getByRole('button', { name: 'Open site menu' }).click();
      await page.locator('#mobileNav.show').waitFor();
      await page.locator('#mobileNav').getByRole('link', { name: 'Browse pieces', exact: true }).click();
      await page.waitForURL('**/products/');
    }
    await page.goto(base + '/product/1/madhubani-lotus-wall-painting/');
    await page.getByRole('tab', { name: 'Care', exact: true }).click();
    if (!await page.locator('#care').isVisible()) issues.push('Care tab does not open');
    await page.getByRole('tab', { name: /Reviews/ }).click();
    if (!await page.locator('#reviews').isVisible()) issues.push('Reviews tab does not open');
    await context.close();
  }
  await browser.close();
  fs.writeFileSync(path.join(out, 'review.json'), JSON.stringify({ sizes, routes, issues }, null, 2));
  console.log('ISSUES:', issues);
  if (issues.length) process.exitCode = 1;
})().catch(error => { console.error(error); process.exit(1); });
