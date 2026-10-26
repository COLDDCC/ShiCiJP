const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../public/js/review-store.js'), 'utf8');
function setup(initial = null, fail = '') {
  let raw = initial;
  const listeners = new Map();
  const window = {
    addEventListener(type, fn) { listeners.set(type, [...(listeners.get(type) || []), fn]); },
    dispatchEvent(event) { for (const fn of listeners.get(event.type) || []) fn(event); }
  };
  const context = { window, CustomEvent: class { constructor(type) { this.type = type; } },
    localStorage: {
      getItem() { if (fail === 'read') throw Error('Denied'); return raw; },
      setItem(key, value) { if (fail === 'write') throw Error('Quota'); raw = value; }
    } };
  vm.runInNewContext(source, context);
  return { store: window.ShiciReview, raw: () => raw, window };
}
test('queue and recognition survive reloading without merging different readings', () => {
  const { store, raw } = setup();
  const a = store.id({ expression: '一日', reading: 'いちにち' });
  const b = store.id({ expression: '一日', reading: 'ついたち' });
  assert.notEqual(a, b);
  assert.equal(store.set(a, 'learning').ok, true);
  assert.equal(store.set(b, 'known').ok, true);
  const restored = setup(raw()).store;
  assert.equal(restored.read().words[a], 'learning');
  assert.equal(restored.read().words[b], 'known');
  restored.set(a, null);
  assert.equal(restored.read().words[a], undefined);
  assert.equal(restored.read().words[b], 'known');
});
test('malformed records are preserved rather than silently overwritten', () => {
  for (const raw of ['broken', '{"version":9,"words":{}}', '{"version":1,"words":{"bad":"known"}}']) {
    const s = setup(raw);
    assert.equal(s.store.read().ok, false);
    assert.equal(s.store.set('["猫","ねこ"]', 'learning').ok, false);
    assert.equal(s.raw(), raw);
  }
});
test('read and write failures return an error without a false saved state', () => {
  for (const fail of ['read', 'write']) {
    const s = setup(null, fail);
    assert.equal(s.store.set('["猫","ねこ"]', 'learning').ok, false);
    assert.equal(s.raw(), null);
  }
});
test('successful mutations and cross-tab events notify consumers', () => {
  const s = setup(); let changes = 0;
  s.window.addEventListener('shici-review-change', () => changes++);
  s.store.set('["猫","ねこ"]', 'learning');
  s.window.dispatchEvent({ type: 'storage', key: 'shici.n5.review.v1' });
  s.window.dispatchEvent({ type: 'storage', key: 'unrelated' });
  assert.equal(changes, 2);
});
