(() => {
  'use strict';
  const $ = id => document.getElementById(id), store = window.ShiciReview;
  let words = [], order = [], current = null, ready = false, saving = false;
  function answer(open) {
    $('review-answer').hidden = !open;
    $('review-reveal').textContent = open ? '隐藏释义' : '显示释义';
    $('review-reveal').setAttribute('aria-expanded', String(open));
  }
  function render() {
    const state = store.read();
    $('review-card').hidden = true;
    $('review-empty').hidden = true;
    $('review-history').hidden = true;
    if (!state.ok) { $('review-status').textContent = state.message; return; }
    if (!ready) return;
    const queued = words.filter(w => state.words[store.id(w)] === 'learning');
    const ids = new Set(queued.map(store.id));
    order = order.filter(id => ids.has(id));
    for (const word of queued) if (!order.includes(store.id(word))) order.push(store.id(word));
    current = words.find(w => store.id(w) === order[0]) || null;
    const known = words.filter(w => state.words[store.id(w)] === 'known');
    $('review-status').textContent = `待复习 ${queued.length} 个 · 已认识 ${known.length} 个`;
    if (current) {
      $('review-card').hidden = false;
      $('review-word').textContent = current.expression;
      $('review-reading').textContent = current.reading;
      $('review-meaning').textContent = current.meaning_zh;
      $('review-example').textContent = current.example_ja;
      $('review-translation').textContent = current.example_zh;
      $('review-link').href = current.url;
      answer(false);
    } else {
      $('review-empty').hidden = false;
      $('review-empty-title').textContent = known.length ? '这轮复习完成了' : '还没有待复习的词';
    }
    $('review-known-list').replaceChildren();
    $('review-history').hidden = !known.length;
    $('review-history-label').textContent = `已认识 ${known.length} 个 · 可重新加入复习`;
    for (const word of known) {
      const li = document.createElement('li'), a = document.createElement('a'), button = document.createElement('button');
      a.href = word.url; a.textContent = `${word.expression} · ${word.reading}`;
      button.type = 'button'; button.className = 'learn-button'; button.textContent = '重新复习';
      button.setAttribute('aria-label', `重新复习 ${word.expression}`);
      button.addEventListener('click', () => change(word, 'learning'));
      li.append(a, button); $('review-known-list').append(li);
    }
  }
  function change(word, state) {
    saving = true;
    const result = store.set(store.id(word), state);
    saving = false;
    if (!result.ok) { $('review-status').textContent = result.message; return; }
    render();
    if (current) $('review-reveal').focus({ preventScroll: true });
    else {
      $('review-status').textContent = '本轮已完成，所有已认识的词仍保存在当前浏览器。';
      $('review-empty').querySelector('a').focus({ preventScroll: true });
    }
  }
  async function load() {
    $('review-retry').hidden = true;
    $('review-status').textContent = '正在读取复习记录…';
    try {
      const response = await fetch('/jlpt/vocabulary/data/n5.json');
      if (!response.ok) throw Error('Unavailable');
      const data = await response.json();
      if (!Array.isArray(data.words)) throw Error('Invalid data');
      words = data.words; ready = true; render();
    } catch {
      $('review-status').textContent = '词库暂时无法读取，你的复习记录仍保留在浏览器中。';
      $('review-retry').hidden = false;
    }
  }
  $('review-retry').addEventListener('click', load);
  $('review-reveal').addEventListener('click', () => answer($('review-answer').hidden));
  $('review-known').addEventListener('click', () => { if (current) change(current, 'known'); });
  $('review-again').addEventListener('click', () => {
    if (!current) return;
    order.push(order.shift()); render(); $('review-reveal').focus({ preventScroll: true });
  });
  window.addEventListener('shici-review-change', () => { if (!saving) render(); });
  load();
})();
