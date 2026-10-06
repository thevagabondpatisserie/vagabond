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
      window.VgbKhoi.ve(g, {khoi: (nd.khoi || []).filter(k => !['tieu_de_muc','kenh_dat_hang','zalo_oa','nut_kenh','uu_dai','tuyen_dung'].includes(k.loai) && (k.vi_tri || 'cuoi_trang') === g.dataset.vgbViTri)});
    });
    /* v532: nhãn cố định (tab, nút đầu trang) và các câu có số. Máy chủ đã
       ghép mặc định vào cong_khai; trong preview bản nháp có thể thiếu khoá
       hoặc để trống, khi đó giữ chữ gốc trong HTML. textContent: chữ của
       marketing không thành HTML. */
    const nhan = nd.nhan || {};
    document.querySelectorAll('[data-vgb-nhan]').forEach(g => {
      const k = g.dataset.vgbNhan;
      if (!(k in nhanGoc)) nhanGoc[k] = g.textContent;
      const chu = typeof nhan[k] === 'string' && nhan[k].trim() ? nhan[k] : nhanGoc[k];
      if (g.textContent !== chu) g.textContent = chu;
    });
    if (window.vgbVeKenhNoi) window.vgbVeKenhNoi(nd);
    if (window.vgbVeChuyenMuc) window.vgbVeChuyenMuc(nd);
    window.vgbSanPham = nd.san_pham || {};
    window.vgbNhan = nhan;
    if (window.vgbApChu) window.vgbApChu();
    document.dispatchEvent(new CustomEvent('vgb-nhan'));
  }
  const nhanGoc = {};
  if (window.vgbXemThu) {
    window.addEventListener('message', e => {
      if (e.origin !== location.origin || e.source !== parent || e.data?.loai !== 'vgb-noi-dung') return;
      ve(e.data.noi_dung);
      const chon=(e.data.noi_dung.khoi||[]).find(k=>k.id===e.data.chon);
      if(chon&&['uu_dai','tuyen_dung'].includes(chon.loai)&&typeof window.go==='function'&&window.location.hash!=='#/'+chon.loai.replace('_','-'))window.go(chon.loai);
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
