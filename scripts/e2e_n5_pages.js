// Generate pages and serve public/ first. Requires Playwright; CHROMIUM is optional.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const BASE = process.env.BASE || 'http://localhost:8000';
(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}),
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    const overview = '/jlpt/vocabulary/n5/';
    await page.goto(BASE + overview);
    const group = await page.locator('a[href*="group-numbers"]').getAttribute('href');
    await page.goto(BASE + group);
    const word = await page.locator('[data-word] a').first().getAttribute('href');
    for (const width of [1440, 390, 320]) {
      await page.setViewportSize({ width, height: 900 });
      for (const path of [overview, group, word, '/']) {
        const response = await page.goto(BASE + path);
        assert.equal(response.status(), 200, path);
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${width}px ${path} overflow`);
      }
    }
    await page.goto(BASE + group);
    await page.locator('#word-filter').fill('不可能找到这个词');
    assert.equal(await page.locator('[data-word]:visible').count(), 0);
    assert.equal(await page.locator('#filter-empty').isVisible(), true);
    await page.locator('#word-filter').fill('');
    assert.ok(await page.locator('[data-word]:visible').count() > 0);
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.goto(BASE + word);
    assert.ok((await page.locator('main').textContent()).includes('待审核'));
    assert.equal(errors.length, 0, JSON.stringify(errors));
    const noJS = await browser.newContext({ javaScriptEnabled: false });
    const plain = await noJS.newPage();
    await plain.goto(BASE + group);
    assert.ok(await plain.locator('[data-word]').count() > 0);
    assert.equal(await plain.locator('#word-filter').isVisible(), false);
    await plain.goto(BASE + word);
    assert.equal(await plain.locator('h1').count(), 1);
    assert.ok((await plain.locator('main').textContent()).includes('例句'));
    await noJS.close();
    console.log('PASS: N5 overview/group/word, 1440/390/320px, filtering, dark mode, no-JS content');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
