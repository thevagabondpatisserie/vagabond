/* #245: lỗi nội dung marketing không được ngăn khách đặt bánh. */
(function () {
  'use strict';
  const goc = document.getElementById('noi-dung-marketing');
  function hienTheoDuong() { goc.hidden = !!location.hash && location.hash !== '#/' && location.hash !== '#danh-muc-banh'; }
  window.addEventListener('hashchange', hienTheoDuong);
  window.addEventListener('popstate', hienTheoDuong);
  document.addEventListener('click', () => setTimeout(hienTheoDuong, 0));
  hienTheoDuong();
  fetch('/api/method/vagabond.noi_dung_web.cong_khai', {headers: {Accept: 'application/json'}})
    .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(d => { if (!d.message) throw new Error('Thiếu nội dung'); window.VgbKhoi.ve(goc, d.message); })
    .catch(e => { console.error('Không tải được nội dung giới thiệu website:', e); });
}());
