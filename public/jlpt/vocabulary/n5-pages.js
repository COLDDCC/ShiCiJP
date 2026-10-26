(() => {
  'use strict';
  const input = document.getElementById('word-filter');
  if (!input) return;
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
})();
