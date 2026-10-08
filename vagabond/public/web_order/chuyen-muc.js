/* #367: nội dung chiến dịch/tuyển dụng từ bản CMS đã xuất bản, không tính
   giảm giá ở trình duyệt. Dùng DOM text, ảnh và liên kết đã qua chuẩn hóa.

   v586 (Minh Vũ đề xuất, anh Việt duyệt 07/10/2026): thêm thẻ Tiệc có đăng
   ký, ưu đãi hiện điều kiện (đơn tối thiểu, khung giờ, ghi chú), tuyển dụng
   hiện yêu cầu và quyền lợi. Hàm vẽ MỘT thẻ (vgbTheMuc) dùng chung cho trang
   khách và khung "Khách sẽ thấy" của trình biên tập, để hai nơi không lệch. */
(function(){
  'use strict';
  const LOAI = ['uu_dai', 'tuyen_dung', 'tiec'];
  let noiDung = {khoi: []};
  const trangThai = {uu_dai: {tim: '', nhom: ''}, tuyen_dung: {tim: '', nhom: ''}, tiec: {tim: '', nhom: ''}};
  const chu = (k, s) => window.vgbChu ? window.vgbChu(k, s) : (((window.vgbNhan || {})[k]) || s);
  function tao(t, c, s) { const e = document.createElement(t); e.className = c || ''; if (s) e.textContent = s; return e; }
  function ngayVN() { return new Intl.DateTimeFormat('en-CA', {timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit'}).format(new Date()); }
  function anToan(u) { return typeof u === 'string' && !/[\s\\]/.test(u) && ((u[0] === '/' && u[1] !== '/') || u[0] === '#' || /^https:\/\/[^/@]+(?:\/|$)/.test(u)); }
  const RE_EMAIL = /^[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
  const ngay = s => String(s || '').split('-').reverse().join('/');
  const gio = s => String(s || '').replace(/^0(\d)/, '$1').replace(':', 'g');
  const tien = s => String(parseInt(s, 10) || 0).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' đ';
  const dong = s => String(s || '').split('\n').map(x => x.trim()).filter(Boolean);

  /* Mục nào khách được thấy hôm nay. Trình biên tập dùng ĐÚNG phép này để
     nói "Khách đang thấy" hay "Đã hết hạn, khách không thấy". */
  function khachThay(k, homNay) {
    if (!k.hien) return false;
    if (k.loai === 'tiec') return !k.bat_dau || k.bat_dau >= homNay;
    return !k.ket_thuc || k.ket_thuc >= homNay;
  }

  /* Dòng điều kiện của ưu đãi: "Đơn từ 500.000 đ · Khung giờ 7g00 - 21g00". */
  function dieuKien(k) {
    const ra = [];
    if (k.don_toi_thieu && +k.don_toi_thieu > 0) ra.push(chu('cm_don_tu', 'Đơn từ') + ' ' + tien(k.don_toi_thieu));
    if (k.gio_bat_dau && k.gio_ket_thuc) ra.push(chu('cm_khung_gio', 'Khung giờ') + ' ' + gio(k.gio_bat_dau) + ' - ' + gio(k.gio_ket_thuc));
    return ra.join(' · ');
  }

  function veVe(k, ctx) {
    const da = +((ctx.ve || {})[k.id] || 0);
    if (!k.so_ve) return {con: null, chu: ''};
    const con = Math.max(0, +k.so_ve - da);
    return {con, chu: con ? chu('cm_con_ve', 'Còn {so} vé').replace('{so}', con) : chu('cm_het_ve', 'Đã hết vé')};
  }

  function moDangKy(k, khung, nut, ctx, conVe) {
    if (khung.querySelector('.cm-dk')) return;
    nut.hidden = true;
    const f = tao('form', 'cm-dk');
    const o = (nhan, ten, kieu, them) => { const l = tao('label', '', nhan); const i = tao(kieu === 'area' ? 'textarea' : 'input'); if (kieu !== 'area') i.type = kieu; i.setAttribute('name', ten); Object.assign(i, them || {}); l.append(i); f.append(l); return i; };
    const ten = o(chu('cm_dk_ten', 'Họ tên'), 'ten', 'text', {required: true, autocomplete: 'name', maxLength: 120});
    const sdt = o(chu('cm_dk_sdt', 'Số điện thoại'), 'sdt', 'tel', {required: true, autocomplete: 'tel', inputMode: 'numeric'});
    const toi = Math.min(10, conVe == null ? 10 : conVe);
    const so = o(chu('cm_dk_so_ve', 'Số vé') + ' (1 - ' + toi + ')', 'so_ve', 'number', {required: true, min: 1, max: toi, value: '1'});
    const ghi = o(chu('cm_dk_ghi_chu', 'Ghi chú (không bắt buộc)'), 'ghi_chu', 'area', {maxLength: 500});
    const bao = tao('p', 'cm-dk-bao'); bao.setAttribute('role', 'status');
    const gui = tao('button', 'cm-nut', chu('cm_dk_gui', 'Gửi đăng ký')); gui.type = 'submit';
    f.append(tao('p', 'cm-dk-luu-y', chu('cm_dk_luu_y', 'Gửi đăng ký chưa phải đã có vé. Chúng tôi sẽ gọi xác nhận và hướng dẫn thanh toán.')), gui, bao);
    let ma = '';
    f.onsubmit = async e => {
      e.preventDefault();
      if (ctx.xemTruoc) { bao.textContent = 'Đây là bản xem trước, không gửi đăng ký.'; return; }
      ma = ma || (window.crypto && crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g, () => (Math.random() * 16 | 0).toString(16)));
      gui.disabled = true; bao.textContent = chu('cm_dk_dang_gui', 'Đang gửi...');
      try {
        const r = await fetch('/api/method/vagabond.tiec_web.dang_ky', {method: 'POST', headers: {'Content-Type': 'application/json', Accept: 'application/json'},
          body: JSON.stringify({du_lieu: {tiec_id: k.id, ten: ten.value, sdt: sdt.value, so_ve: so.value, ghi_chu: ghi.value}, ma_lan_gui: ma})});
        const d = await r.json();
        if (!r.ok || d.exc) {
          let loi = chu('cm_dk_loi', 'Chưa gửi được. Kiểm tra mạng rồi bấm Gửi lại.');
          try { const m = JSON.parse(d._server_messages || '[]').map(x => JSON.parse(x).message); if (m.length) loi = m.join(' '); } catch (_) { /* giữ câu chung */ }
          if (r.status === 429) loi = chu('cm_dk_nhieu', 'Quý khách gửi nhiều lần quá. Vui lòng thử lại sau ít phút.');
          throw new Error(loi);
        }
        f.replaceChildren(tao('p', 'cm-dk-xong', chu('cm_dk_xong', 'Đã nhận đăng ký, mã {ma}. Chúng tôi sẽ gọi xác nhận và hướng dẫn thanh toán.').replace('{ma}', d.message.ma)));
      } catch (er) { bao.textContent = er.message; gui.disabled = false; }
    };
    khung.append(f);
  }

  /* Vẽ MỘT thẻ. ctx: {homNay, ve, lienHe, xemTruoc}. */
  function theMuc(k, ctx) {
    ctx = ctx || {};
    const loai = k.loai, homNay = ctx.homNay || ngayVN();
    const muc = tao('article', 'cm-the cm-' + loai); muc.dataset.khoi = k.id;
    if (k.anh && anToan(k.anh)) { const im = tao('img', 'cm-anh'); im.src = k.anh; im.alt = k.mo_ta_anh || ''; im.loading = 'lazy'; muc.append(im); }
    else if (loai !== 'tuyen_dung') { const nen = tao('div', 'cm-anh cm-anh-nen'); nen.setAttribute('aria-hidden', 'true'); nen.append(tao('span', '', k.tieu_de)); muc.append(nen); }
    const nd = tao('div', 'cm-noi-dung'); nd.append(tao('p', 'cm-nhan', k.nhan || k.nhom), tao('h2', '', k.tieu_de));
    if (loai === 'tiec') {
      const thoi = [k.bat_dau ? ngay(k.bat_dau) : '', k.gio_bat_dau && k.gio_ket_thuc ? gio(k.gio_bat_dau) + ' - ' + gio(k.gio_ket_thuc) : ''].filter(Boolean).join(' · ');
      if (thoi) nd.append(tao('p', 'cm-ngay', thoi));
      if (k.dia_diem) nd.append(tao('p', 'cm-thong-tin', k.dia_diem));
      nd.append(tao('p', 'cm-gia', +k.gia_ve > 0 ? tien(k.gia_ve) + ' / ' + chu('cm_ve', 'vé') : chu('cm_mien_phi', 'Miễn phí')));
    } else {
      if (k.bat_dau > homNay) nd.append(tao('p', 'cm-trang-thai', chu('sap_dien_ra', 'Sắp diễn ra')));
      if (k.bat_dau || k.ket_thuc) nd.append(tao('p', 'cm-ngay', [k.bat_dau, k.ket_thuc].filter(Boolean).map(ngay).join(' - ')));
    }
    nd.append(tao('p', 'cm-doan', k.noi_dung));
    if (loai === 'uu_dai') {
      if (k.ma_uu_dai) nd.append(tao('p', 'cm-ma', chu('ma_uu_dai', 'Mã ưu đãi') + ': ' + k.ma_uu_dai));
      const dk = dieuKien(k);
      if (dk) nd.append(tao('p', 'cm-dieu-kien', dk));
    }
    /* Ưu đãi: ghi chú điều kiện; tuyển dụng: yêu cầu và quyền lợi; tiệc:
       những gì bao gồm. Mỗi dòng một ý, hiện thành danh sách. */
    const ds = dong(loai === 'uu_dai' ? k.dieu_kien : k.yeu_cau);
    if (ds.length) {
      if (loai !== 'uu_dai') nd.append(tao('p', 'cm-nhan', loai === 'tiec' ? chu('cm_bao_gom', 'Bao gồm') : chu('cm_yeu_cau', 'Yêu cầu và quyền lợi')));
      const ul = tao('ul', 'cm-ds'); ds.forEach(x => ul.append(tao('li', '', x))); nd.append(ul);
    }
    if (loai === 'tuyen_dung' && !k.ket_thuc) nd.append(tao('p', 'cm-ngay', chu('chua_han', 'Nhận hồ sơ đến khi đủ người')));
    if (loai === 'tuyen_dung') nd.append(tao('p', 'cm-thong-tin', [k.noi_lam, k.hinh_thuc].filter(Boolean).join(' · ')));
    if (loai === 'tiec') {
      const v = veVe(k, ctx), han = k.han_ban || k.bat_dau;
      if (v.chu) nd.append(tao('p', 'cm-trang-thai', v.chu));
      if (k.han_ban) nd.append(tao('p', 'cm-ngay', chu('cm_han_dk', 'Đăng ký trước') + ' ' + ngay(k.han_ban)));
      if (han && han < homNay) nd.append(tao('p', 'cm-trang-thai', chu('cm_het_han_dk', 'Đã hết hạn đăng ký')));
      else if (v.con !== 0) {
        const nut = tao('button', 'cm-nut', chu('cm_dang_ky', 'Đăng ký tham gia')); nut.type = 'button';
        nut.onclick = () => moDangKy(k, nd, nut, ctx, v.con);
        nd.append(nut);
      }
    } else {
      let duong = anToan(k.lien_ket) ? k.lien_ket : '';
      const email = k.email || ((ctx.lienHe || {}).email) || '';
      if (loai === 'tuyen_dung' && !duong && RE_EMAIL.test(email)) duong = 'mailto:' + email + '?subject=' + encodeURIComponent('Ứng tuyển - ' + k.tieu_de);
      if (duong) { const a = tao('a', 'cm-nut', k.nut || (loai === 'tuyen_dung' ? chu('ung_tuyen', 'Ứng tuyển vị trí này') : chu('xem_chi_tiet_muc', 'Xem chi tiết'))); a.href = duong; nd.append(a); }
    }
    muc.append(nd);
    return muc;
  }

  function ctxTrang() { return {homNay: ngayVN(), ve: noiDung.ve || {}, lienHe: (noiDung.thong_tin || {}).lien_he || {}, xemTruoc: !!window.vgbXemThu}; }

  function veMuc(loai) {
    const g = document.getElementById('noi-' + loai); if (!g) return;
    g.replaceChildren();
    const ctx = ctxTrang(), tt = trangThai[loai];
    const ds = (noiDung.khoi || []).filter(k => k.loai === loai && (window.vgbXemThu || khachThay(k, ctx.homNay)));
    const loc = tao('div', 'cm-loc'), tim = tao('input'); tim.type = 'search'; tim.placeholder = chu('tim_muc', 'Tìm theo tên, nhóm hoặc nơi làm'); tim.setAttribute('aria-label', tim.placeholder); tim.value = tt.tim;
    const the = tao('div', 'cm-danh-sach');
    function veThe() {
      the.replaceChildren();
      const locDs = ds.filter(k => (!tt.nhom || k.nhom === tt.nhom) && [k.tieu_de, k.nhom, k.noi_lam, k.dia_diem, k.noi_dung].join(' ').toLocaleLowerCase('vi').includes(tt.tim.toLocaleLowerCase('vi')));
      if (!locDs.length) {
        const rong = {uu_dai: 'Chưa có ưu đãi trong nhóm này. Quý khách có thể xem các nhóm khác.', tiec: 'Chưa có tiệc nào đang mở. Quý khách vui lòng quay lại sau.', tuyen_dung: 'Chưa có vị trí phù hợp trong nhóm này. Quý khách vui lòng quay lại sau.'};
        the.append(tao('p', 'cm-rong', chu(loai + '_rong', rong[loai]))); return;
      }
      locDs.forEach(k => the.append(theMuc(k, ctx)));
    }
    tim.oninput = () => { tt.tim = tim.value; veThe(); };
    if (ds.length > 3) loc.append(tim);
    const chips = tao('div', 'cm-chips');
    const nhom = [...new Set(ds.map(k => k.nhom).filter(Boolean))];
    if (nhom.length) ['', ...nhom].forEach(n => { const b = tao('button', '', n || chu('tat_ca_muc', 'Tất cả')); b.setAttribute('aria-pressed', String(n === tt.nhom)); b.onclick = () => { tt.nhom = n; veMuc(loai); }; chips.append(b); });
    g.append(loc, chips, the); veThe();
    /* Thẻ Tiệc trên thanh chọn chỉ hiện khi có tiệc khách thấy được. */
    if (loai === 'tiec') { const t = document.querySelector('[data-tab="tiec"]'); if (t) t.hidden = !ds.length; }
  }
  const veHet = () => LOAI.forEach(veMuc);
  window.vgbTheMuc = theMuc;
  window.vgbKhachThayMuc = khachThay;
  window.vgbDieuKienUuDai = dieuKien;
  window.vgbVeChuyenMuc = nd => { noiDung = nd; veHet(); };
  document.addEventListener('vgb-nhan', veHet);
})();
