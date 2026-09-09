/* #245: nội dung nằm đúng khe của trang order; lỗi CMS không ngăn đặt bánh. */
(function () {
  'use strict';
  const tieuDeGoc = {};
  document.querySelectorAll('[data-vgb-tieu-de]').forEach(g => { tieuDeGoc[g.dataset.vgbTieuDe] = g.innerHTML; });
  function ve(nd) {
    document.querySelectorAll('[data-vgb-tieu-de]').forEach(g => {
      const k = (nd.khoi || []).find(x => x.loai === 'tieu_de_muc' && x.vi_tri === g.dataset.vgbTieuDe);
      if (k?.hien) g.textContent = k.tieu_de; else g.innerHTML = tieuDeGoc[g.dataset.vgbTieuDe];
      if (k) g.dataset.khoi = k.id;
    });
    document.querySelectorAll('[data-vgb-vi-tri]').forEach(g => {
      window.VgbKhoi.ve(g, {khoi: (nd.khoi || []).filter(k => k.loai !== 'tieu_de_muc' && (k.vi_tri || 'cuoi_trang') === g.dataset.vgbViTri)});
    });
  }
  if (window.vgbXemThu) {
    window.addEventListener('message', e => {
      if (e.origin !== location.origin || e.source !== parent || e.data?.loai !== 'vgb-noi-dung') return;
      ve(e.data.noi_dung);
      document.querySelectorAll('[data-khoi]').forEach(k => {
        k.classList.toggle('vgb-dang-chon', k.dataset.khoi === e.data.chon);
        k.onclick = suKien => { suKien.preventDefault(); parent.postMessage({loai:'vgb-chon-khoi',id:k.dataset.khoi}, location.origin); };
      });
    });
    parent.postMessage({loai:'vgb-san-sang'}, location.origin);
    return;
  }
  fetch('/api/method/vagabond.noi_dung_web.cong_khai', {headers: {Accept: 'application/json'}})
    .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(d => { if (!d.message) throw new Error('Thiếu nội dung'); ve(d.message); })
    .catch(e => { console.error('Không tải được nội dung giới thiệu website:', e); });
}());
