(() => {
  'use strict';
  const field = document.getElementById('vocab-search');
  const results = document.getElementById('vocab-matches');
  const status = document.getElementById('vocab-search-status');
  const norm = text => text.normalize('NFKC').toLocaleLowerCase().trim();
  let promise = null, generation = 0, timer;
  function words() {
    if (!promise) promise = fetch('/jlpt/vocabulary/data/n5.json').then(r => {
      if (!r.ok) throw Error('词库暂时无法读取');
      return r.json();
    }).then(data => {
      if (!Array.isArray(data.words)) throw Error('词库格式异常');
      return data.words;
    }).catch(error => { promise = null; throw error; });
    return promise;
  }
  async function search() {
    const version = ++generation, query = norm(field.value);
    results.replaceChildren();
    if (!query) { status.textContent = '日语、假名或中文；按 Enter 打开完整词库。'; return; }
    status.textContent = '正在查找 N5 词汇…';
    try {
      const data = await words();
      if (version !== generation) return;
      const matches = data.filter(w => norm(`${w.expression} ${w.reading} ${w.meaning_zh}`).includes(query));
      for (const word of matches.slice(0, 5)) {
        const li = document.createElement('li'), link = document.createElement('a');
        link.href = word.url;
        link.textContent = `${word.expression} · ${word.reading} — ${word.meaning_zh}`;
        li.append(link); results.append(li);
      }
      status.textContent = matches.length ? `N5 找到 ${matches.length} 条，显示前 ${Math.min(5, matches.length)} 条；中文内容待审核。` : 'N5 暂无匹配，可在完整词库切换其他等级。';
    } catch {
      if (version === generation) status.textContent = '快速搜索暂不可用，仍可按 Enter 打开完整词库。';
    }
  }
  field.addEventListener('input', () => { generation++; clearTimeout(timer); timer = setTimeout(search, 120); });
  function count() {
    const state = window.ShiciReview.read();
    const target = document.getElementById('home-review-count');
    target.textContent = state.ok ? `${Object.values(state.words).filter(s => s === 'learning').length} 个待复习 · 仅存当前浏览器` : '本地记录暂不可用';
  }
  count();
  window.addEventListener('shici-review-change', count);
})();
