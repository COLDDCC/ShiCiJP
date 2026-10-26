(() => {
  'use strict';
  const KEY = 'shici.n5.review.v1';
  const message = '复习记录暂时无法读写，请检查浏览器的本地存储设置。';
  const id = word => JSON.stringify([word.expression, word.reading]);
  function read() {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw === null) return { ok: true, words: {} };
      const data = JSON.parse(raw);
      if (data.version !== 1 || !data.words || typeof data.words !== 'object' || Array.isArray(data.words)) throw Error('Invalid record');
      const words = {};
      for (const [key, value] of Object.entries(data.words)) {
        const pair = JSON.parse(key);
        if (!Array.isArray(pair) || pair.length !== 2 || !pair.every(x => typeof x === 'string') || !['learning', 'known'].includes(value)) throw Error('Invalid word');
        words[key] = value;
      }
      return { ok: true, words };
    } catch { return { ok: false, words: {}, message }; }
  }
  function set(key, state) {
    const snapshot = read();
    if (!snapshot.ok) return snapshot;
    try {
      const pair = JSON.parse(key);
      if (!Array.isArray(pair) || pair.length !== 2 || !pair.every(x => typeof x === 'string') || !['learning', 'known', null].includes(state)) throw Error('Invalid change');
      if (state === null) delete snapshot.words[key];
      else snapshot.words[key] = state;
      localStorage.setItem(KEY, JSON.stringify({ version: 1, words: snapshot.words }));
      window.dispatchEvent(new CustomEvent('shici-review-change'));
      return { ok: true };
    } catch { return { ok: false, message }; }
  }
  window.ShiciReview = Object.freeze({ id, read, set });
  window.addEventListener('storage', event => {
    if (event.key === KEY || event.key === null) window.dispatchEvent(new CustomEvent('shici-review-change'));
  });
})();
