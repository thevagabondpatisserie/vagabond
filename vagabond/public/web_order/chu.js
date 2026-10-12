/* #367: mỗi chỗ chữ có khóa riêng trong Marketing Studio. Chỉ thay chữ,
   không thay giá, tồn, mã món, URL hoặc HTML bằng nội dung người soạn. */
/* v586: số gọi lấy từ thẻ Liên hệ (Settings, nguồn #367). Mặc định của rất
   nhiều câu còn chép cứng số cũ ("gọi 0931 224 334"), nên đổi số ở thẻ Liên
   hệ thì mọi câu có số cũ đều đổi theo, không phải sửa từng câu. */
var VGB_DT_GOC = '0931 224 334';
function vgbThayDienThoai(s) {
  var dt = typeof window !== 'undefined' && window.vgbDienThoai;
  return dt && dt !== VGB_DT_GOC ? String(s).split(VGB_DT_GOC).join(dt) : s;
}
function chuWeb(khoa, macDinh, thay) {
  var nhan = (typeof window !== 'undefined' && window.vgbNhan) || {};
  var chu = typeof nhan[khoa] === 'string' && nhan[khoa].trim() ? nhan[khoa] : macDinh;
  return vgbThayDienThoai(String(chu || '').replace(/\{([a-z_]+)\}/g, function (goc, k) {
    return thay && Object.prototype.hasOwnProperty.call(thay, k) ? String(thay[k]) : goc;
  }));
}
/* Áp thẻ Liên hệ lên trang: đường gọi tel:, chữ số trong đường gọi và các
   biểu tượng mạng xã hội ở chân trang (để trống là ẩn). Chỉ đổi khi có số. */
/* v586 (Codex #453): MỘT nguồn cho link mạng xã hội. Chưa tải được thẻ Liên hệ
   thì dùng link mặc định của trang; đã tải thì đúng link marketing khai, để
   trống là '' (ẩn), không quay về tài khoản cũ. */
function vgbLinkHopLe(u) { u = String(u || ''); return (/^https:\/\/[^\s/@\\]+(\/|$)/.test(u) && !/\s/.test(u)) ? u : ''; }
function vgbMxh(k, macDinh) {
  var lh = typeof window !== 'undefined' && window.vgbLienHeDaTai;
  return lh ? vgbLinkHopLe(lh[k]) : (macDinh || '');
}
function vgbApLienHe(lh) {
  if (typeof document === 'undefined' || !lh) return;
  window.vgbLienHeDaTai = lh;
  var so = String(lh.dien_thoai_so || lh.dien_thoai || '').replace(/[^0-9+]/g, '');
  if (lh.dien_thoai && so) {
    var cu = window.vgbDienThoai || VGB_DT_GOC;
    window.vgbDienThoai = lh.dien_thoai;
    document.querySelectorAll('[href="tel:0931224334"]').forEach(function (a) { a.setAttribute('data-vgb-tel', '1'); });
    document.querySelectorAll('[data-vgb-tel]').forEach(function (a) {
      a.setAttribute('href', 'tel:' + so);
      (a.childNodes || []).forEach(function (n) {
        if (n.nodeType === 3 && n.nodeValue.indexOf(cu) >= 0) n.nodeValue = n.nodeValue.split(cu).join(lh.dien_thoai);
      });
    });
  }
  document.querySelectorAll('[data-vgb-mxh]').forEach(function (a) {
    var u = vgbLinkHopLe(lh[a.getAttribute('data-vgb-mxh')]);
    if (u) { a.setAttribute('href', u); a.hidden = false; }
    else a.hidden = true;
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
      .then(function (d) { window.vgbNhan = d.message.nhan; vgbApLienHe(d.message.lien_he); document.dispatchEvent(new CustomEvent('vgb-nhan')); })
      .catch(function () { /* Mạng lỗi vẫn giữ nội dung mặc định trong trang. */ }).finally(function () { clearTimeout(hetCho); sanSang(); });
  });
}());
