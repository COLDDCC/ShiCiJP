const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const BASE = process.env.BASE || 'http://localhost:8000';
(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {}),
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'] });
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(BASE + '/');
    await page.locator('#vocab-search').fill('猫');
    await page.waitForFunction(() => document.querySelectorAll('#vocab-matches a').length > 0);
    const first = await page.locator('#vocab-matches a').first().getAttribute('href');
    await page.locator('#vocab-matches a').first().click();
    assert.ok(page.url().endsWith(first));
    const add = page.locator('[data-review-action="learning"]');
    await add.click();
    assert.equal(await add.getAttribute('aria-pressed'), 'true');
    await page.reload();
    assert.equal(await add.getAttribute('aria-pressed'), 'true');
    const other = await context.newPage();
    await other.goto(BASE + first);
    await other.locator('[data-review-action="known"]').click();
    await page.waitForFunction(() => document.querySelector('[data-review-action="known"]').getAttribute('aria-pressed') === 'true');
    await other.locator('[data-review-action="known"]').click(); // Undo into review.
    await other.close();
    await page.goto(BASE + '/jlpt/review/');
    await page.locator('#review-card').waitFor({ state: 'visible' });
    assert.equal(await page.locator('#review-answer').isVisible(), false);
    await page.locator('#review-reveal').focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('#review-answer').isVisible(), true);
    await page.locator('#review-again').click();
    assert.equal(await page.locator('#review-answer').isVisible(), false);
    await page.locator('#review-known').click();
    assert.equal(await page.locator('#review-empty').isVisible(), true);
    await page.locator('#review-history summary').click();
    await page.locator('#review-known-list button').first().click();
    assert.equal(await page.locator('#review-card').isVisible(), true);
    await page.goto(BASE + '/');
    assert.ok((await page.locator('#home-review-count').textContent()).startsWith('1 个待复习'));
    await page.locator('#vocab-search').fill('ねこ');
    await page.waitForFunction(() => document.querySelectorAll('#vocab-matches a').length > 0);
    await page.locator('#vocab-search').press('Enter');
    await page.waitForURL('**/jlpt/vocabulary/?q=*');
    await page.waitForFunction(() => document.getElementById('results').textContent.includes('猫'));
    for (const width of [1440, 390, 320]) {
      await page.setViewportSize({ width, height: 844 });
      for (const path of ['/', first, '/jlpt/review/']) {
        await page.goto(BASE + path, { waitUntil: 'domcontentloaded' });
        if (path.endsWith('/review/')) await page.locator('#review-card').waitFor();
        const overflow = await page.evaluate(() => ({scroll: document.documentElement.scrollWidth, width: innerWidth, elements: [...document.querySelectorAll('body *')].map(e => ({tag: e.tagName, id:e.id, cls: String(e.className).slice(0,70), right:Math.round(e.getBoundingClientRect().right), left:Math.round(e.getBoundingClientRect().left)})).filter(e => e.right > innerWidth + 1 || e.left < -1).slice(0,12)}));
        assert.ok(overflow.scroll <= overflow.width, `${width}px ${path} ${JSON.stringify(overflow)}`);
      }
    }
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.reload();
    assert.equal(await page.locator('#review-card').isVisible(), true);
    assert.equal(errors.length, 0, JSON.stringify(errors));
    const denied = await browser.newContext();
    await denied.addInitScript(() => { Storage.prototype.setItem = () => { throw Error('Quota'); }; });
    const blocked = await denied.newPage();
    await blocked.goto(BASE + first);
    await blocked.locator('[data-review-action="learning"]').click();
    assert.ok((await blocked.locator('[data-review-status]').textContent()).includes('无法读写'));
    assert.equal(await blocked.locator('[data-review-action="learning"]').getAttribute('aria-pressed'), 'false');
    await denied.close();
    console.log('PASS: search → word → save/reload → cross-tab recognition → review/reveal/restore; keyboard, 1440/390/320px, dark mode, storage failure');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
