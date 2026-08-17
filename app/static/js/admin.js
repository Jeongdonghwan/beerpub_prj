/* admin.js — 목록 행 드래그앤드랍 순서 변경 (바닐라 HTML5 DnD) */
(function () {
  'use strict';

  var tbody = document.getElementById('sortBody');
  if (!tbody) return;

  var url = tbody.getAttribute('data-url');
  var csrf = tbody.getAttribute('data-csrf');
  var dragging = null;
  var orderBefore = null;

  function rowIds() {
    return Array.prototype.map.call(tbody.querySelectorAll('tr[data-id]'), function (r) {
      return parseInt(r.getAttribute('data-id'), 10);
    });
  }

  tbody.addEventListener('dragstart', function (e) {
    var row = e.target.closest('tr[data-id]');
    if (!row) return;
    dragging = row;
    orderBefore = rowIds();
    row.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', row.getAttribute('data-id'));
  });

  tbody.addEventListener('dragover', function (e) {
    if (!dragging) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    var over = e.target.closest('tr[data-id]');
    if (!over || over === dragging) return;
    var rect = over.getBoundingClientRect();
    var after = e.clientY > rect.top + rect.height / 2;
    over.parentNode.insertBefore(dragging, after ? over.nextSibling : over);
  });

  tbody.addEventListener('drop', function (e) { e.preventDefault(); });

  tbody.addEventListener('dragend', function () {
    if (!dragging) return;
    var row = dragging;
    dragging = null;
    row.classList.remove('dragging');
    var ids = rowIds();
    if (orderBefore && ids.join(',') === orderBefore.join(',')) return; /* 변화 없음 */

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf },
      body: JSON.stringify({ ids: ids })
    })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function () {
        row.classList.add('saved');
        setTimeout(function () { row.classList.remove('saved'); }, 900);
      })
      .catch(function () {
        alert('순서 저장에 실패했습니다. 페이지를 새로고침합니다.');
        location.reload();
      });
  });
})();
