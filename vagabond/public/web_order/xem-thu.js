/* Editor xem chính trang order. Chặn gửi đơn trước khi mã đặt bánh được nạp. */
(function () {
  'use strict';
  if (window.parent === window || new URLSearchParams(location.search).get('bien_tap') !== '1') return;
  window.vgbXemThu = true;
  const tai = window.fetch.bind(window);
  window.fetch = function (duong, tuyChon) {
    const phuongThuc = String(tuyChon?.method || (duong instanceof Request ? duong.method : 'GET')).toUpperCase();
    if (!['GET', 'HEAD'].includes(phuongThuc)) return Promise.reject(new Error('Bản xem trước không gửi đơn hay lưu dữ liệu.'));
    return tai(duong, tuyChon);
  };
  document.addEventListener('submit', e => e.preventDefault(), true);
  document.addEventListener('click', e => {
    const a = e.target.closest('a');
    if (a && a.getAttribute('href') && !a.getAttribute('href').startsWith('#')) e.preventDefault();
  }, true);
  document.addEventListener('DOMContentLoaded', () => document.body.classList.add('vgb-xem-thu'));
})();
