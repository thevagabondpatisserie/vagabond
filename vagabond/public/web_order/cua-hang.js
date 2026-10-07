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
    /* v586: liên hệ và cửa hàng trước, để câu chữ vẽ sau đã có số gọi mới. */
    if (typeof window.vgbApLienHe === 'function') window.vgbApLienHe(nd.lien_he);
    veCuaHang(nd.thong_tin || {}, nd.lien_he || {});
    if (window.vgbVeKenhNoi) window.vgbVeKenhNoi(nd);
    if (window.vgbVeChuyenMuc) window.vgbVeChuyenMuc(nd);
    window.vgbSanPham = nd.san_pham || {};
    window.vgbNhan = nhan;
    if (window.vgbApChu) window.vgbApChu();
    document.dispatchEvent(new CustomEvent('vgb-nhan'));
  }
  const nhanGoc = {};
  /* v586: mục "Ghé cửa hàng" và điểm nhận bánh, từ thẻ Cửa hàng của trình
     biên tập. Chữ của người soạn đi qua textContent. */
  function veCuaHang(tt, lh) {
    const ds = Array.isArray(tt.cua_hang) ? tt.cua_hang : null;
    if (!ds) return;
    if (typeof window.capNhatDiemNhan === 'function') window.capNhatDiemNhan(ds.filter(c => c.nhan_banh && c.dia_chi).map(c => ({n: c.ten, a: c.dia_chi})));
    const khung = document.getElementById('cuaHangWeb'), g = document.getElementById('cuaHangDs');
    if (!khung || !g) return;
    const tao = (t, c, s) => { const e = document.createElement(t); if (c) e.className = c; if (s) e.textContent = s; return e; };
    const chu = (k, s) => (typeof window.chuWeb === 'function' ? window.chuWeb(k, s) : s);
    const hien = ds.filter(c => c.hien && c.dia_chi);
    g.replaceChildren();
    hien.forEach(c => {
      const the = tao('article', 'cw-the');
      the.append(tao('h3', '', c.ten), tao('p', 'cw-dia-chi', c.dia_chi));
      if (c.gio_mo_cua) the.append(tao('p', 'cw-gio', c.gio_mo_cua));
      const hang = tao('div', 'cw-nut');
      const dt = c.hotline || lh.dien_thoai || '';
      const so = String(dt).replace(/[^0-9+]/g, '');
      if (so) { const a = tao('a', '', chu('cua_hang_goi', 'Gọi') + ' ' + dt); a.href = 'tel:' + so; hang.append(a); }
      if (/^https:\/\/[^\s/@\\]+(\/|$)/.test(c.chi_duong || '') && !/\s/.test(c.chi_duong)) { const a = tao('a', '', chu('cua_hang_chi_duong', 'Chỉ đường') + ' ↗'); a.href = c.chi_duong; a.target = '_blank'; a.rel = 'noopener'; hang.append(a); }
      the.append(hang);
      g.append(the);
    });
    khung.hidden = !hien.length;
  }
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
