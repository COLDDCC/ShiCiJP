(() => {
  'use strict';
  const input = document.getElementById('word-filter');
  if (input) {
    const rows = [...document.querySelectorAll('[data-word]')];
    const normalize = value => value.normalize('NFKC').toLocaleLowerCase().trim();
    const values = rows.map(row => normalize(row.textContent));
    input.closest('.n5-filter').hidden = false;
    input.addEventListener('input', () => {
      const query = normalize(input.value);
      let count = 0;
      rows.forEach((row, index) => {
        row.hidden = !values[index].includes(query);
        if (!row.hidden) count++;
      });
      document.getElementById('filter-status').textContent = `${count} / ${rows.length} 条词汇`;
      document.getElementById('filter-empty').hidden = count !== 0;
    });
  }
  const controls = document.querySelector('[data-review-id]');
  if (!controls || !window.ShiciReview) return;
  const store = window.ShiciReview, id = controls.dataset.reviewId;
  const status = controls.querySelector('[data-review-status]');
  controls.hidden = false;
  function refresh() {
    const state = store.read(), value = state.words[id];
    for (const button of controls.querySelectorAll('button')) {
      const action = button.dataset.reviewAction;
      button.disabled = !state.ok;
      button.setAttribute('aria-pressed', String(value === action));
      button.textContent = action === 'learning' ? (value === action ? '移出复习' : '加入复习') : (value === action ? '已认识 · 撤销' : '标记认识');
    }
    status.textContent = !state.ok ? state.message : value === 'known' ? '已标记认识，可在「我的复习」中重新加入。' : value === 'learning' ? '已加入复习，记录仅存当前浏览器。' : '记录仅存当前浏览器。';
  }
  controls.addEventListener('click', event => {
    const button = event.target.closest('[data-review-action]');
    if (!button) return;
    const state = store.read(), action = button.dataset.reviewAction;
    const target = state.words[id] === action ? (action === 'known' ? 'learning' : null) : action;
    const result = store.set(id, target);
    if (!result.ok) status.textContent = result.message;
  });
  refresh();
  window.addEventListener('shici-review-change', refresh);
})();
