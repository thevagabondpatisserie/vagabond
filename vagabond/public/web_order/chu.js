/* #367: mỗi chỗ chữ có khóa riêng trong Marketing Studio. Chỉ thay chữ,
   không thay giá, tồn, mã món, URL hoặc HTML bằng nội dung người soạn. */
function chuWeb(khoa, macDinh, thay) {
  var nhan = (typeof window !== 'undefined' && window.vgbNhan) || {};
  var chu = typeof nhan[khoa] === 'string' && nhan[khoa].trim() ? nhan[khoa] : macDinh;
  return String(chu || '').replace(/\{([a-z_]+)\}/g, function (goc, k) {
    return thay && Object.prototype.hasOwnProperty.call(thay, k) ? String(thay[k]) : goc;
  });
}
function htmlChuWeb(khoa, macDinh, thay) {
  return chuWeb(khoa, macDinh, thay).replace(/[&<>"']/g, function (c) {
    return {'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c];
  });
}
function chuMonWeb(ma, truong, macDinh) {
  var nd = (typeof window !== 'undefined' && window.vgbSanPham) || {};
  var chu = Object.prototype.hasOwnProperty.call(nd, ma) && nd[ma][truong];
  return typeof chu === 'string' && chu.trim() ? chu : (macDinh || '');
}
(function () {
  'use strict';
  function apNhan(goc) {
    (goc || document).querySelectorAll('[data-vgb-chu]').forEach(function (e) {
      if (!e.dataset.vgbGoc) e.dataset.vgbGoc = e.textContent;
      e.textContent = chuWeb(e.dataset.vgbChu, e.dataset.vgbGoc);
    });
    ['placeholder', 'aria-label', 'title', 'alt'].forEach(function (thuocTinh) {
      document.querySelectorAll('[data-vgb-' + thuocTinh + ']').forEach(function (e) {
        var ma = 'data-vgb-goc-' + thuocTinh;
        if (!e.hasAttribute(ma)) e.setAttribute(ma, e.getAttribute(thuocTinh) || '');
        e.setAttribute(thuocTinh, chuWeb(e.getAttribute('data-vgb-' + thuocTinh), e.getAttribute(ma)));
      });
    });
  }
  window.vgbApChu = apNhan;
  document.addEventListener('vgb-nhan', function () { apNhan(); });
  var sanSang; window.vgbChuSanSang = new Promise(function (x) { sanSang = x; });
  document.addEventListener('DOMContentLoaded', function () {
    apNhan();
    // Trang đặt bánh đã có cua-hang.js nạp cùng bản công khai và khối.
    if (document.querySelector('[data-vgb-vi-tri]') || window.vgbXemThu) { sanSang(); return; }
    var hetCho = setTimeout(sanSang, 3000);
    fetch('/api/method/vagabond.noi_dung_web.cong_khai', {headers:{Accept:'application/json'}})
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (d) { window.vgbNhan = d.message.nhan; document.dispatchEvent(new CustomEvent('vgb-nhan')); })
      .catch(function () { /* Mạng lỗi vẫn giữ nội dung mặc định trong trang. */ }).finally(function () { clearTimeout(hetCho); sanSang(); });
  });
}());
