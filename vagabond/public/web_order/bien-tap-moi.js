/* v586: trình biên tập website THEO VIỆC (Minh Vũ đề xuất, anh Việt duyệt
   07/10/2026).

   Vì sao có tệp này: bảng biên tập cũ là một trình dựng trang theo khối.
   Muốn đăng một vị trí tuyển dụng, người soạn phải chọn "loại khối", chọn
   "vị trí", rồi điền một bộ ô chung cho mọi loại (Dòng giới thiệu, Tiêu đề,
   Nội dung...). Minh Vũ dùng thử và nói thẳng là khó dùng quá.

   Trình mới chia theo việc: Ưu đãi, Tiệc, Tuyển dụng, Cửa hàng, Trang và chữ,
   Liên hệ. Mỗi thẻ là danh sách có nhãn trạng thái, công tắc "Hiện trên web",
   nút Sửa, Xoá; bấm Sửa ra form chỉ gồm đúng các ô của loại đó. Lưu là khách
   thấy ngay (máy chủ ghi cả bản công khai lẫn bản nháp, chỉ phần vừa sửa).
   Trình cũ vẫn mở được ở thẻ Nâng cao cho ảnh bìa, câu hỏi thường gặp, kênh
   đặt hàng, nội dung bánh, chính sách và lịch sử.

   Mọi chữ của người soạn đi qua textContent, không thành HTML. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  function tao(the, lop, chu) { const e = document.createElement(the); if (lop) e.className = lop; if (chu != null && chu !== '') e.textContent = chu; return e; }

  const THE = [
    {k: 'uu_dai', ten: 'Ưu đãi', mo: 'Thêm, sửa, ẩn chương trình khuyến mãi', them: '+ Thêm ưu đãi', luu: 'Lưu ưu đãi', ten_muc: 'ưu đãi', dau: 'Danh sách ưu đãi'},
    {k: 'tiec', ten: 'Tiệc', mo: 'Tạo tiệc, đặt giá vé, số vé, hạn đăng ký', them: '+ Thêm tiệc', luu: 'Lưu tiệc', ten_muc: 'tiệc', dau: 'Danh sách tiệc'},
    {k: 'tuyen_dung', ten: 'Tuyển dụng', mo: 'Vị trí đang tuyển, hạn nhận hồ sơ', them: '+ Thêm vị trí', luu: 'Lưu vị trí', ten_muc: 'vị trí', dau: 'Danh sách tuyển dụng'},
    {k: 'cua_hang', ten: 'Cửa hàng', mo: 'Địa chỉ, giờ mở cửa, hotline, chỉ đường', them: '+ Thêm cửa hàng', luu: 'Lưu cửa hàng', ten_muc: 'cửa hàng', dau: 'Danh sách cửa hàng'},
    {k: 'chu', ten: 'Trang và chữ', mo: 'Tiêu đề từng trang, khẩu hiệu, chân trang, câu nhắc'},
    {k: 'lien_he', ten: 'Liên hệ', mo: 'Điện thoại, email, mạng xã hội, công ty'},
  ];
  const LOAI_MUC = ['uu_dai', 'tiec', 'tuyen_dung'];
  const HINH_THUC = ['Toàn thời gian', 'Bán thời gian', 'Thời vụ'];

  let B = null;            // dữ liệu máy chủ (bang_moi): bản khách đang thấy
  let the = 'uu_dai';
  let sua = null;          // {loai, muc, moi, dau, goc} khi đang mở form
  let ban = false;
  let chuSua = {};         // thẻ Trang và chữ: {khoá: chữ mới} chưa lưu
  let lhDoi = false;       // thẻ Liên hệ đang có chữ chưa lưu
  let timChu = '', nhomChu = '', timMuc = '';

  /* ------------------------------------------------------------ phép nhỏ */
  const ngayVN = s => s ? String(s).split('-').reverse().join('/') : '';
  const gio = s => String(s || '').replace(/^0(\d)/, '$1').replace(':', 'g');
  const tien = s => String(parseInt(s, 10) || 0).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' đ';
  const THU = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];
  function thu(s) { const p = String(s || '').split('-').map(Number); if (p.length !== 3 || !p[0]) return ''; return THU[new Date(Date.UTC(p[0], p[1] - 1, p[2])).getUTCDay()]; }
  function maMoi(loai) { return loai.replace('_', '-') + '-' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
  const homNay = () => (B && B.hom_nay) || new Date().toISOString().slice(0, 10);

  /* Nhãn trạng thái, trùng ĐÚNG phép trang_thai_muc ở máy chủ (có ca kiểm
     chạy cùng một bảng mẫu cho hai bên). */
  function trangThai(k, hn) {
    const bd = k.bat_dau || '', kt = k.ket_thuc || '';
    if (k.loai === 'tiec') {
      if (bd && bd < hn) return ['het', 'Đã diễn ra'];
      const han = k.han_ban || bd;
      if (han && han < hn) return ['het', 'Hết hạn đăng ký'];
      return ['dang', 'Đang mở đăng ký'];
    }
    if (kt && kt < hn) return ['het', k.loai === 'uu_dai' ? 'Đã kết thúc' : 'Hết hạn nhận hồ sơ'];
    if (k.loai === 'uu_dai' && bd && bd > hn) return ['sap', 'Sắp diễn ra'];
    return ['dang', k.loai === 'uu_dai' ? 'Đang diễn ra' : 'Đang tuyển'];
  }
  function khachThay(k) { return window.vgbKhachThayMuc ? window.vgbKhachThayMuc(k, homNay()) : !!k.hien; }
  function chuCongTac(k) {
    if (!k.hien) return 'Khách không thấy';
    if (!khachThay(k)) return 'Đã hết hạn, khách không thấy';
    return trangThai(k, homNay())[0] === 'sap' ? 'Khách thấy nhãn Sắp diễn ra' : 'Khách đang thấy';
  }
  function moTa(k) {
    if (k.loai === 'uu_dai') {
      return [k.ma_uu_dai ? 'Mã ' + k.ma_uu_dai : '', +k.don_toi_thieu > 0 ? 'Đơn từ ' + tien(k.don_toi_thieu) : '',
        k.gio_bat_dau ? gio(k.gio_bat_dau) + ' - ' + gio(k.gio_ket_thuc) : '',
        k.bat_dau || k.ket_thuc ? [ngayVN(k.bat_dau), ngayVN(k.ket_thuc)].filter(Boolean).join(' - ') : 'không giới hạn ngày'].filter(Boolean).join(' · ');
    }
    if (k.loai === 'tuyen_dung') {
      return [k.noi_lam || 'Chưa chọn nơi làm', k.hinh_thuc, k.ket_thuc ? 'hạn ' + ngayVN(k.ket_thuc) : 'tới khi đủ người'].filter(Boolean).join(' - ');
    }
    const da = +((B.ve || {})[k.id] || 0);
    return [k.bat_dau ? thu(k.bat_dau) + ', ' + ngayVN(k.bat_dau) : 'Chưa chọn ngày', k.gio_bat_dau ? gio(k.gio_bat_dau) + ' - ' + gio(k.gio_ket_thuc) : '',
      k.dia_diem, +k.gia_ve > 0 ? tien(k.gia_ve) + '/vé' : 'Miễn phí',
      k.so_ve ? 'Đã đăng ký ' + da + '/' + k.so_ve + ' vé' : 'Đã đăng ký ' + da + ' vé'].filter(Boolean).join(' · ');
  }

  /* ------------------------------------------------------------ máy chủ */
  function bao(chu, loi) { const e = $('bt-trang-thai'); if (!e) return; e.textContent = chu || ''; e.className = 'bt-trang-thai' + (loi ? ' loi' : chu ? ' ok' : ''); }
  async function api(ham, duLieu) {
    const cau = {credentials: 'same-origin', headers: {Accept: 'application/json'}};
    if (duLieu) {
      cau.method = 'POST'; cau.headers['Content-Type'] = 'application/json';
      const m = document.querySelector('meta[name=csrf-token]'); if (m) cau.headers['X-Frappe-CSRF-Token'] = m.content;
      cau.body = JSON.stringify(duLieu);
    }
    const r = await fetch('/api/method/vagabond.noi_dung_web.' + ham, cau);
    let d = {};
    try { d = await r.json(); } catch (_) { /* phản hồi không phải JSON: dùng câu chung */ }
    if (!r.ok || d.exc) {
      let chu = 'Chưa lưu được. Kiểm tra mạng rồi bấm lưu lại; chữ đang gõ vẫn còn trên màn.';
      if (r.status === 403) chu = 'Phiên đăng nhập hết hạn hoặc tài khoản chưa có quyền Marketing. Đăng nhập lại để tiếp tục.';
      try { const tb = JSON.parse(d._server_messages || '[]').map(s => JSON.parse(s).message); if (tb.length) chu = tb.join(' '); } catch (_) { /* giữ câu có hướng xử lý */ }
      throw new Error(chu);
    }
    return d.message;
  }
  function khoa(b) { ban = b; const g = $('bt-moi'); if (g) g.setAttribute('aria-busy', b ? 'true' : 'false'); }
  async function tai() {
    khoa(true); bao('Đang tải nội dung...');
    try { B = await api('bang_moi'); bao(B.nhap_chua_xuat_ban ? 'Mục Nâng cao còn thay đổi chưa xuất bản. Các thẻ ở đây luôn hiện bản khách đang thấy.' : ''); }
    catch (e) { bao(e.message, true); }
    finally { khoa(false); }
    ve();
  }
  async function ghi(ham, duLieu, xong) {
    if (ban) return false;
    khoa(true); bao('Đang lưu...');
    try { B = await api(ham, duLieu); bao(xong); return true; }
    catch (e) { bao(e.message, true); return false; }
    finally { khoa(false); }
  }

  /* Hộp hỏi trong trang (không dùng window.confirm: chặn cả trang và bộ kiểm). */
  function hoi(tieuDe, noiDung, nut, nguy) {
    return new Promise(xong => {
      const nen = tao('div', 'bt-hop-nen'); nen.setAttribute('role', 'dialog'); nen.setAttribute('aria-modal', 'true');
      const hop = tao('div', 'bt-hop'); hop.append(tao('h3', '', tieuDe), tao('p', '', noiDung));
      const co = tao('button', nguy ? 'bt-nut nguy' : 'bt-nut chinh', nut); co.type = 'button'; co.dataset.hopCo = '1';
      const thoi = tao('button', 'bt-nut', 'Thôi'); thoi.type = 'button'; thoi.dataset.hopThoi = '1';
      const tra = v => { nen.remove(); xong(v); };
      co.onclick = () => tra(true); thoi.onclick = () => tra(false);
      const hang = tao('div', 'bt-hang-nut'); hang.append(co, thoi); hop.append(hang); nen.append(hop);
      document.body.append(nen);
      co.focus();
    });
  }
  function dangDoi() {
    if (sua) return JSON.stringify(sua.muc) !== sua.goc;
    return lhDoi || Object.keys(chuSua).length > 0;
  }
  async function roiDi() {
    if (!dangDoi()) return true;
    return hoi('Bỏ thay đổi chưa lưu?', 'Những gì vừa gõ chưa được lưu và sẽ mất.', 'Bỏ thay đổi', true);
  }

  /* ------------------------------------------------------------ khung */
  function demThe(k) {
    if (!B) return '';
    if (LOAI_MUC.includes(k)) return String(B.khoi.filter(x => x.loai === k).length);
    if (k === 'cua_hang') return String((B.thong_tin.cua_hang || []).length);
    return '';
  }
  function veThe() {
    const g = $('bt-the'); if (!g) return;
    g.replaceChildren();
    THE.forEach(t => {
      const b = tao('button', 'bt-o-the' + (t.k === the ? ' dang' : '')); b.type = 'button';
      b.setAttribute('role', 'tab'); b.setAttribute('aria-selected', String(t.k === the)); b.dataset.the = t.k;
      const dau = tao('span', 'bt-ten-the', t.ten); const so = demThe(t.k); if (so) dau.append(tao('span', 'bt-dem', so));
      b.append(dau, tao('span', 'bt-mo-the', t.mo));
      b.onclick = async () => { if (t.k === the && !sua) return; if (!await roiDi()) return; the = t.k; sua = null; chuSua = {}; lhDoi = false; timMuc = ''; ve(); };
      g.append(b);
    });
    const nc = tao('button', 'bt-o-the bt-nang-cao'); nc.type = 'button'; nc.dataset.the = 'nang_cao';
    nc.append(tao('span', 'bt-ten-the', 'Nâng cao'), tao('span', 'bt-mo-the', 'Ảnh bìa, câu hỏi, kênh đặt hàng, nội dung bánh, chính sách, lịch sử'));
    nc.onclick = async () => { if (!await roiDi()) return; moNangCao(true); };
    g.append(nc);
  }
  function ve() {
    veThe();
    const g = $('bt-noi'); if (!g) return;
    g.replaceChildren();
    if (!B) return;
    let noi;
    if (sua) noi = LOAI_MUC.includes(sua.loai) ? formMuc() : formCuaHang();
    else if (LOAI_MUC.includes(the)) noi = dsMuc(the);
    else if (the === 'cua_hang') noi = dsCuaHang();
    else if (the === 'lien_he') noi = formLienHe();
    else noi = theChu();
    g.append(noi);
    /* Việc cần phần tử đã nằm trong trang (khung xem trước) chạy sau khi gắn. */
    if (noi._sauKhiGan) noi._sauKhiGan();
  }

  /* ------------------------------------------------------------ ô nhập */
  function o(nhan, giaTri, doi, tuy) {
    tuy = tuy || {};
    const l = tao('label', 'bt-o'); l.append(tao('span', 'bt-nhan', nhan));
    const i = tao(tuy.nhieuDong ? 'textarea' : 'input');
    if (!tuy.nhieuDong) i.type = tuy.kieu || 'text';
    if (tuy.nhieuDong) i.rows = tuy.dong || 3;
    i.value = giaTri == null ? '' : String(giaTri);
    if (tuy.goi) i.placeholder = tuy.goi;
    if (tuy.ten) i.setAttribute('name', tuy.ten);
    if (tuy.so) i.inputMode = 'numeric';
    i.oninput = () => { if (tuy.so) i.value = i.value.replace(/[^0-9]/g, ''); doi(i.value); };
    l.append(i);
    if (tuy.chu) l.append(tao('span', 'bt-goi-y', tuy.chu));
    if (tuy.rong) l.className += ' rong';
    return l;
  }
  function chip(nhan, luaChon, chon, doi, nhieu, chu) {
    const g = tao('div', 'bt-o'); g.append(tao('span', 'bt-nhan', nhan));
    const hang = tao('div', 'bt-chips'); hang.setAttribute('role', nhieu ? 'group' : 'radiogroup');
    const dang = () => (nhieu ? String(chon() || '').split(' / ').filter(Boolean) : [chon()]);
    luaChon.forEach(lc => {
      const b = tao('button', 'bt-chip', lc); b.type = 'button'; b.dataset.chip = lc;
      const veChip = () => { const on = dang().includes(lc); b.className = 'bt-chip' + (on ? ' dang' : ''); b.setAttribute('aria-pressed', String(on)); };
      b.onclick = () => {
        let ds = dang();
        if (nhieu) ds = ds.includes(lc) ? ds.filter(x => x !== lc) : luaChon.filter(x => ds.includes(x) || x === lc);
        else ds = ds[0] === lc ? [''] : [lc];
        doi(nhieu ? ds.join(' / ') : ds[0]);
        hang.querySelectorAll('[data-chip]').forEach(x => x._ve && x._ve());
      };
      b._ve = veChip; veChip(); hang.append(b);
    });
    g.append(hang);
    if (chu) g.append(tao('span', 'bt-goi-y', chu));
    return g;
  }
  function congTac(nhan, bat, doi, phu) {
    const l = tao('label', 'bt-cong-tac');
    const i = tao('input'); i.type = 'checkbox'; i.checked = !!bat; i.setAttribute('role', 'switch');
    const nut = tao('span', 'bt-cong-tac-nut'); nut.setAttribute('aria-hidden', 'true');
    const chu = tao('span', 'bt-cong-tac-chu'); const p = tao('span', 'bt-phu', phu ? phu(!!bat) : '');
    chu.append(tao('b', '', nhan), p);
    i.onchange = () => { doi(i.checked); if (phu) p.textContent = phu(i.checked); };
    l.append(i, nut, chu);
    return l;
  }
  function muc(so, ten) { const h = tao('h3', 'bt-muc'); h.append(tao('span', 'bt-so', String(so)), tao('span', '', ten)); return h; }
  function oAnh(m, xem) {
    const g = tao('div', 'bt-o'); g.append(tao('span', 'bt-nhan', 'Ảnh (không bắt buộc)'));
    const hang = tao('div', 'bt-hang-anh');
    const anh = tao('img', 'bt-anh-nho'); anh.alt = ''; if (m.anh) anh.src = m.anh; anh.hidden = !m.anh;
    const tep = tao('input'); tep.type = 'file'; tep.accept = 'image/png,image/jpeg,image/webp';
    const bo = tao('button', 'bt-nut nho', 'Bỏ ảnh'); bo.type = 'button'; bo.hidden = !m.anh;
    bo.onclick = () => { m.anh = ''; anh.hidden = true; bo.hidden = true; xem(); };
    tep.onchange = async () => {
      const f = tep.files && tep.files[0]; if (!f) return;
      if (f.size > 10 * 1024 * 1024) { bao('Chọn ảnh dưới 10 MB.', true); return; }
      khoa(true); bao('Đang tải ảnh...');
      try {
        const form = new FormData(); form.append('file', f);
        const m2 = document.querySelector('meta[name=csrf-token]');
        const r = await fetch('/api/method/vagabond.noi_dung_web.tai_anh', {method: 'POST', credentials: 'same-origin', headers: m2 ? {'X-Frappe-CSRF-Token': m2.content} : {}, body: form});
        const d = await r.json();
        if (!r.ok || !d.message || !d.message.url) throw new Error('Không tải được ảnh. Chọn PNG, JPG hoặc WebP dưới 10 MB.');
        m.anh = d.message.url; anh.src = m.anh; anh.hidden = false; bo.hidden = false; xem();
        bao('Đã tải ảnh. Bấm lưu để gắn ảnh vào trang.');
      } catch (e) { bao(e.message, true); } finally { khoa(false); }
    };
    hang.append(anh, tep, bo); g.append(hang);
    g.append(tao('span', 'bt-goi-y', 'Ảnh ngang 1920 x 1080 (16:9) hiện trọn, không bị cắt. Để trống thì web tự dựng nền theo màu thương hiệu.'));
    return g;
  }

  /* ------------------------------------------------------------ danh sách */
  function dsMuc(loai) {
    const t = THE.find(x => x.k === loai);
    const g = tao('section', 'bt-ds'); g.setAttribute('aria-label', t.dau);
    const dau = tao('div', 'bt-dau-ds');
    const them = tao('button', 'bt-nut chinh', t.them); them.type = 'button'; them.dataset.them = loai;
    them.onclick = () => moForm(loai, null);
    dau.append(them);
    const ds = B.khoi.filter(k => k.loai === loai);
    if (ds.length > 6) {
      const tim = tao('input', 'bt-tim'); tim.type = 'search'; tim.placeholder = 'Tìm theo tên, mã, nơi làm...'; tim.value = timMuc;
      tim.setAttribute('aria-label', 'Tìm trong ' + t.dau.toLowerCase());
      tim.oninput = () => { timMuc = tim.value; veHang(); };
      dau.append(tim);
    }
    g.append(dau);
    const hang = tao('div', 'bt-hang');
    function veHang() {
      hang.replaceChildren();
      const q = timMuc.trim().toLocaleLowerCase('vi');
      const loc = ds.filter(k => !q || [k.tieu_de, k.ma_uu_dai, k.noi_lam, k.dia_diem, k.nhom].join(' ').toLocaleLowerCase('vi').includes(q));
      if (!ds.length) hang.append(tao('p', 'bt-rong', 'Chưa có ' + t.ten_muc + ' nào. Bấm "' + t.them.replace('+ ', '') + '" để tạo cái đầu tiên.'));
      else if (!loc.length) hang.append(tao('p', 'bt-rong', 'Không thấy ' + t.ten_muc + ' nào khớp "' + timMuc + '".'));
      loc.forEach(k => hang.append(dongMuc(k)));
    }
    veHang();
    g.append(hang);
    return g;
  }
  function dongMuc(k) {
    const d = tao('article', 'bt-dong'); d.dataset.muc = k.id;
    const trai = tao('div', 'bt-dong-trai');
    const [ma, chuTT] = trangThai(k, homNay());
    const nhan = tao('div', 'bt-nhan-hang');
    nhan.append(tao('span', 'bt-tt ' + ma, chuTT));
    if (!k.hien) nhan.append(tao('span', 'bt-tt an', 'Đang ẩn'));
    trai.append(nhan, tao('h3', 'bt-ten', k.tieu_de || '(chưa đặt tên)'), tao('p', 'bt-meta', moTa(k)));
    const phai = tao('div', 'bt-dong-phai');
    const ct = congTac('Hiện trên web', k.hien, async bat => {
      const moi = Object.assign({}, k, {hien: bat});
      /* Lưu hỏng thì vẽ lại cũng đưa công tắc về đúng trạng thái máy chủ. */
      await ghi('luu_muc', {muc: moi, dau_cu: B.dau[k.id]}, bat ? 'Đã bật. ' + (khachThay(moi) ? 'Khách thấy ngay.' : 'Mục đã hết hạn nên khách vẫn không thấy.') : 'Đã ẩn. Khách không thấy nữa.');
      ve();
    }, () => chuCongTac(k));
    ct.dataset.congTac = k.id;
    const nut = tao('div', 'bt-hang-nut');
    const s = tao('button', 'bt-nut vien', 'Sửa'); s.type = 'button'; s.dataset.sua = k.id; s.onclick = () => moForm(k.loai, k);
    const x = tao('button', 'bt-nut chu-do', 'Xoá'); x.type = 'button'; x.dataset.xoa = k.id;
    x.onclick = async () => {
      const t = THE.find(y => y.k === k.loai);
      if (!await hoi('Xoá ' + t.ten_muc + ' "' + k.tieu_de + '"?', 'Khách sẽ không thấy nữa. Bản cũ vẫn khôi phục được ở Nâng cao, mục Lịch sử xuất bản.', 'Xoá', true)) return;
      await ghi('xoa_muc_web', {id_muc: k.id, dau_cu: B.dau[k.id]}, 'Đã xoá ' + t.ten_muc + ' "' + k.tieu_de + '".');
      ve();
    };
    nut.append(s, x);
    phai.append(ct, nut);
    d.append(trai, phai);
    return d;
  }

  /* ------------------------------------------------------------ form mục */
  function macDinh(loai) {
    const goc = {id: maMoi(loai), loai: loai, vi_tri: loai, hien: true, tieu_de: '', noi_dung: '', anh: '', mo_ta_anh: ''};
    if (loai === 'uu_dai') return Object.assign(goc, {nhom: '', ma_uu_dai: '', don_toi_thieu: '', bat_dau: homNay(), ket_thuc: '', gio_bat_dau: '', gio_ket_thuc: '', dieu_kien: ''});
    if (loai === 'tuyen_dung') return Object.assign(goc, {noi_lam: '', hinh_thuc: 'Toàn thời gian', ket_thuc: '', yeu_cau: '', email: (B.lien_he || {}).email || ''});
    return Object.assign(goc, {bat_dau: '', gio_bat_dau: '', gio_ket_thuc: '', dia_diem: '', gia_ve: '', so_ve: '', han_ban: '', yeu_cau: ''});
  }
  async function moForm(loai, k) {
    if (!await roiDi()) return;
    const m = k ? JSON.parse(JSON.stringify(k)) : macDinh(loai);
    sua = {loai: loai, muc: m, moi: !k, dau: k ? B.dau[k.id] : '', goc: JSON.stringify(m)};
    ve();
    if (window.scrollTo) try { window.scrollTo(0, 0); } catch (_) { /* trình duyệt cũ */ }
  }
  function tenCuaHang() { return (B.thong_tin.cua_hang || []).filter(c => c.ten).map(c => c.ten); }
  function noiChon(nhan, truong, m, xem, chuKhac) {
    const ds = tenCuaHang();
    const g = tao('div', 'bt-nhom-o');
    const khac = o(chuKhac, ds.includes(m[truong]) ? '' : m[truong], v => { m[truong] = v; veLai(); xem(); }, {chu: 'Để trống nếu đã chọn ở trên.'});
    const c = chip(nhan, ds, () => m[truong], v => { m[truong] = v; const i = khac.querySelector('input'); if (i) i.value = ''; xem(); }, false);
    function veLai() { c.querySelectorAll('[data-chip]').forEach(x => x._ve && x._ve()); }
    g.append(c, khac);
    return g;
  }
  /* Hình thức: chip chọn nhiều, cộng ô ghi thêm. Chữ cũ gõ tay (ví dụ "Toàn
     thời gian, ca sáng sớm") không trùng chip nào thì nằm ở ô ghi thêm, không
     bị mất khi bấm chip. */
  function oHinhThuc(m, xem) {
    const tach = () => String(m.hinh_thuc || '').split(' / ').map(x => x.trim()).filter(Boolean);
    let khac = tach().filter(x => !HINH_THUC.includes(x)).join(' / ');
    const ghep = chips => [...HINH_THUC.filter(x => chips.includes(x)), ...(khac ? [khac] : [])].join(' / ');
    const g = tao('div', 'bt-nhom-o');
    g.append(
      chip('Hình thức', HINH_THUC, () => tach().filter(x => HINH_THUC.includes(x)).join(' / '), v => { m.hinh_thuc = ghep(v.split(' / ')); xem(); }, true, 'Chọn một hoặc nhiều hình thức.'),
      o('Ghi thêm về ca làm (không bắt buộc)', khac, v => { khac = v.trim(); m.hinh_thuc = ghep(tach()); xem(); }, {ten: 'hinh_thuc_khac', goi: 'ca sáng sớm', chu: 'Ví dụ: ca sáng sớm, cuối tuần.'}),
    );
    return g;
  }
  function formMuc() {
    const loai = sua.loai, m = sua.muc, t = THE.find(x => x.k === loai);
    const khung = tao('section', 'bt-form-khung');
    const lui = tao('button', 'bt-lui', '← ' + t.dau.toUpperCase()); lui.type = 'button';
    lui.onclick = async () => { if (!await roiDi()) return; sua = null; ve(); };
    const tieu = tao('h2', 'bt-tieu-form', (sua.moi ? 'Thêm ' : 'Sửa ') + t.ten_muc);
    const f = tao('form', 'bt-form'); f.noValidate = true;
    const xemKhung = tao('aside', 'bt-xem'); xemKhung.append(tao('p', 'bt-nhan-xem', 'Khách sẽ thấy'));
    const xemNoi = tao('div', 'bt-xem-noi'); xemKhung.append(xemNoi);
    let dkEl = null;
    const xem = () => {
      xemNoi.replaceChildren();
      if (window.vgbTheMuc) xemNoi.append(window.vgbTheMuc(m, {homNay: homNay(), ve: B.ve, lienHe: B.lien_he, xemTruoc: true}));
      if (dkEl) { const c = window.vgbDieuKienUuDai ? window.vgbDieuKienUuDai(m) : ''; dkEl.replaceChildren(tao('span', '', 'Khách sẽ thấy điều kiện: '), tao('b', '', c || 'Không có điều kiện, áp dụng cả ngày.')); }
    };
    const dat = truong => v => { m[truong] = v; xem(); };

    if (loai === 'tuyen_dung') {
      f.append(
        o('Tên vị trí', m.tieu_de, dat('tieu_de'), {ten: 'tieu_de', goi: 'Thợ làm bánh (Pâtissier)', chu: 'Ví dụ: Thợ làm bánh (Pâtissier)'}),
        noiChon('Nơi làm', 'noi_lam', m, xem, 'Hoặc gõ nơi làm khác'),
        oHinhThuc(m, xem),
        o('Hạn nhận hồ sơ (không bắt buộc)', m.ket_thuc, dat('ket_thuc'), {kieu: 'date', ten: 'ket_thuc', chu: 'Qua ngày này web tự ẩn vị trí. Để trống là nhận tới khi đủ người.'}),
        o('Mô tả công việc', m.noi_dung, dat('noi_dung'), {nhieuDong: true, ten: 'noi_dung', chu: 'Một hai câu nói công việc chính.'}),
        o('Yêu cầu và quyền lợi (không bắt buộc)', m.yeu_cau, dat('yeu_cau'), {nhieuDong: true, dong: 5, ten: 'yeu_cau', goi: 'Có kinh nghiệm làm bánh 1 năm trở lên\nĐược ăn bánh mỗi ngày', chu: 'Mỗi dòng một ý, web hiện thành danh sách.'}),
        o('Email nhận hồ sơ', m.email, dat('email'), {kieu: 'email', ten: 'email', goi: 'tuyendung@thevagabondpatisserie.com', chu: 'Ứng viên bấm Ứng tuyển là mở thư gửi về email này. Cần có email trước khi bật hiện.'}),
      );
    } else if (loai === 'uu_dai') {
      f.append(
        muc(1, 'Nội dung'),
        o('Tên ưu đãi', m.tieu_de, dat('tieu_de'), {ten: 'tieu_de', goi: 'Giảm 10% bánh sinh nhật'}),
        o('Mô tả ngắn', m.noi_dung, dat('noi_dung'), {nhieuDong: true, ten: 'noi_dung', chu: 'Một hai câu nói khách được gì.'}),
        o('Nhóm (không bắt buộc)', m.nhom, dat('nhom'), {ten: 'nhom', goi: 'Sinh nhật', chu: 'Khách lọc ưu đãi theo nhóm, ví dụ Sinh nhật, Thành viên, Mùa lễ.'}),
        muc(2, 'Mã và điều kiện'),
        o('Mã ưu đãi (không bắt buộc)', m.ma_uu_dai, v => { m.ma_uu_dai = v.toUpperCase(); xem(); }, {ten: 'ma_uu_dai', goi: 'SINHNHAT10', chu: 'Khách đọc mã này cho nhân viên hoặc gõ khi đặt.'}),
        o('Đơn từ (không bắt buộc)', m.don_toi_thieu, dat('don_toi_thieu'), {so: true, ten: 'don_toi_thieu', goi: '500000', chu: 'Gõ số tiền, không cần dấu chấm. Để trống là không cần đơn tối thiểu.'}),
        muc(3, 'Thời gian áp dụng'),
      );
      const ngay = tao('div', 'bt-hai-cot');
      ngay.append(o('Ngày bắt đầu', m.bat_dau, dat('bat_dau'), {kieu: 'date', ten: 'bat_dau'}),
        o('Ngày kết thúc', m.ket_thuc, dat('ket_thuc'), {kieu: 'date', ten: 'ket_thuc', chu: 'Hết ngày này web tự chuyển sang Đã kết thúc và ẩn ưu đãi.'}));
      const gioK = tao('div', 'bt-hai-cot');
      gioK.append(o('Từ giờ (không bắt buộc)', m.gio_bat_dau, dat('gio_bat_dau'), {kieu: 'time', ten: 'gio_bat_dau', chu: 'Bỏ trống cả hai ô giờ là áp dụng cả ngày.'}),
        o('Đến giờ', m.gio_ket_thuc, dat('gio_ket_thuc'), {kieu: 'time', ten: 'gio_ket_thuc'}));
      dkEl = tao('p', 'bt-tom-tat'); dkEl.dataset.dieuKien = '1';
      f.append(ngay, gioK, dkEl,
        o('Ghi chú điều kiện khác (không bắt buộc)', m.dieu_kien, dat('dieu_kien'), {nhieuDong: true, ten: 'dieu_kien', goi: 'Không cộng dồn với ưu đãi khác', chu: 'Mỗi dòng một điều, chỉ để khách đọc. Ví dụ: Không cộng dồn với ưu đãi khác.'}),
        muc(4, 'Ảnh và hiển thị'), oAnh(m, xem));
    } else {
      f.append(
        muc(1, 'Thông tin tiệc'),
        o('Tên tiệc', m.tieu_de, dat('tieu_de'), {ten: 'tieu_de', goi: 'Tiệc trà chiều mùa thu'}),
        o('Mô tả', m.noi_dung, dat('noi_dung'), {nhieuDong: true, ten: 'noi_dung', chu: 'Vài câu về không khí, chủ đề, ai dẫn tiệc.'}),
        o('Bao gồm (không bắt buộc)', m.yeu_cau, dat('yeu_cau'), {nhieuDong: true, ten: 'yeu_cau', goi: '5 món bánh theo mùa\nMột ly trà hoặc cà phê', chu: 'Mỗi dòng một ý, web hiện thành danh sách.'}),
        muc(2, 'Thời gian và địa điểm'),
      );
      const ngay = tao('div', 'bt-hai-cot');
      ngay.append(o('Ngày diễn ra', m.bat_dau, dat('bat_dau'), {kieu: 'date', ten: 'bat_dau', chu: 'Qua ngày này web tự ẩn tiệc.'}), tao('span', ''));
      const gioK = tao('div', 'bt-hai-cot');
      gioK.append(o('Từ giờ', m.gio_bat_dau, dat('gio_bat_dau'), {kieu: 'time', ten: 'gio_bat_dau'}), o('Đến giờ', m.gio_ket_thuc, dat('gio_ket_thuc'), {kieu: 'time', ten: 'gio_ket_thuc'}));
      f.append(ngay, gioK, noiChon('Địa điểm', 'dia_diem', m, xem, 'Hoặc gõ địa điểm khác'),
        muc(3, 'Vé và đăng ký'));
      const ve2 = tao('div', 'bt-hai-cot');
      ve2.append(o('Giá vé (không bắt buộc)', m.gia_ve, dat('gia_ve'), {so: true, ten: 'gia_ve', goi: '350000', chu: 'Để trống là miễn phí.'}),
        o('Số vé (không bắt buộc)', m.so_ve, dat('so_ve'), {so: true, ten: 'so_ve', goi: '40', chu: 'Để trống là không giới hạn. Web hiện số vé còn lại.'}));
      f.append(ve2, o('Hạn đăng ký (không bắt buộc)', m.han_ban, dat('han_ban'), {kieu: 'date', ten: 'han_ban', chu: 'Qua ngày này web ngừng nhận đăng ký. Để trống là nhận tới ngày diễn ra.'}));
      if (!sua.moi) {
        const da = +((B.ve || {})[m.id] || 0);
        const p = tao('p', 'bt-tom-tat'); p.append(tao('span', '', 'Đã có ' + da + ' vé đăng ký. '));
        const a = tao('a', '', 'Xem danh sách đăng ký ↗'); a.href = '/app/vagabond-dang-ky-tiec?tiec_id=' + encodeURIComponent(m.id); a.target = '_blank'; a.rel = 'noopener';
        p.append(a); f.append(p);
      }
      f.append(muc(4, 'Ảnh và hiển thị'), oAnh(m, xem));
    }
    f.append(congTac('Hiện trên web', m.hien, dat('hien'), bat => bat ? 'Lưu xong khách thấy ngay' : 'Lưu xong vẫn ẩn, bật lên khi sẵn sàng'));
    const hang = tao('div', 'bt-hang-nut bt-chan-form');
    const luu = tao('button', 'bt-nut chinh', t.luu); luu.type = 'submit'; luu.dataset.luu = '1';
    const huy = tao('button', 'bt-nut vien', 'Huỷ'); huy.type = 'button'; huy.onclick = () => lui.onclick();
    hang.append(luu, huy); f.append(hang);
    f.onsubmit = async e => {
      if (e && e.preventDefault) e.preventDefault();
      if (!m.tieu_de.trim()) { bao('Điền tên ' + t.ten_muc + ' trước khi lưu.', true); return; }
      if (loai === 'tiec' && m.hien && !m.bat_dau) { bao('Chọn ngày diễn ra tiệc trước khi bật hiện trên web.', true); return; }
      if (Boolean(m.gio_bat_dau) !== Boolean(m.gio_ket_thuc)) { bao('Điền cả hai ô giờ, hoặc bỏ trống cả hai.', true); return; }
      const ok = await ghi('luu_muc', {muc: m, dau_cu: sua.dau}, 'Đã lưu ' + t.ten_muc + ' "' + m.tieu_de + '". ' + (m.hien ? (khachThay(m) ? 'Khách thấy ngay.' : 'Mục đã hết hạn nên khách chưa thấy.') : 'Đang ẩn, khách chưa thấy.'));
      if (ok) { sua = null; ve(); }
    };
    const luoi = tao('div', 'bt-luoi-form'); luoi.append(f, xemKhung);
    khung.append(lui, tieu, luoi);
    khung._sauKhiGan = xem;
    return khung;
  }

  /* ------------------------------------------------------------ cửa hàng */
  function dsCuaHang() {
    const t = THE.find(x => x.k === 'cua_hang');
    const g = tao('section', 'bt-ds'); g.setAttribute('aria-label', t.dau);
    const them = tao('button', 'bt-nut chinh', t.them); them.type = 'button'; them.dataset.them = 'cua_hang';
    them.onclick = () => moCuaHang(-1);
    const dau = tao('div', 'bt-dau-ds'); dau.append(them);
    g.append(dau, tao('p', 'bt-chu-phu', 'Cửa hàng bật "Hiện trên web" có mục riêng ở cuối trang đặt bánh. Điểm bật "Nhận bánh tại đây" hiện ở bước Tự lấy trong giỏ hàng.'));
    const hang = tao('div', 'bt-hang');
    const ds = B.thong_tin.cua_hang || [];
    if (!ds.length) hang.append(tao('p', 'bt-rong', 'Chưa có cửa hàng nào.'));
    /* Cùng luật với noi_dung_web.diem_nhan: tắt hết thì trang khách ẩn Tự đến lấy. */
    if (!ds.some(c => c.nhan_banh && String(c.dia_chi || '').trim() && String(c.ten || '').trim())) g.append(tao('p', 'bt-loi bt-canh-diem', 'Chưa nơi nào bật "Nhận bánh tại đây": khách sẽ không chọn được Tự đến lấy, chỉ còn giao tận nơi.'));
    ds.forEach((c, i) => {
      const d = tao('article', 'bt-dong'); d.dataset.muc = c.id;
      const trai = tao('div', 'bt-dong-trai'), nhan = tao('div', 'bt-nhan-hang');
      nhan.append(tao('span', 'bt-tt dang', c.loai === 'bep' ? 'Bếp' : 'Cửa hàng'));
      if (c.nhan_banh) nhan.append(tao('span', 'bt-tt sap', 'Nhận bánh tại đây'));
      trai.append(nhan, tao('h3', 'bt-ten', c.ten), tao('p', 'bt-meta', [c.dia_chi, c.gio_mo_cua ? c.gio_mo_cua.split('\n')[0] : 'chưa có giờ mở cửa', c.hotline].filter(Boolean).join(' · ')));
      const phai = tao('div', 'bt-dong-phai');
      const ct = congTac('Hiện trên web', c.hien, async bat => {
        const moi = ds.map((x, j) => j === i ? Object.assign({}, x, {hien: bat}) : x);
        await ghi('luu_thong_tin', {phan: 'cua_hang', gia_tri: moi, dau_cu: B.dau_thong_tin.cua_hang}, bat ? 'Đã bật. Khách thấy cửa hàng này ở cuối trang.' : 'Đã ẩn cửa hàng khỏi trang.');
        ve();
      }, bat => bat ? 'Khách đang thấy' : 'Khách không thấy');
      ct.dataset.congTac = c.id;
      const nut = tao('div', 'bt-hang-nut');
      const s = tao('button', 'bt-nut vien', 'Sửa'); s.type = 'button'; s.dataset.sua = c.id; s.onclick = () => moCuaHang(i);
      const x = tao('button', 'bt-nut chu-do', 'Xoá'); x.type = 'button'; x.dataset.xoa = c.id;
      x.onclick = async () => {
        if (!await hoi('Xoá "' + c.ten + '"?', c.nhan_banh ? 'Đây đang là điểm nhận bánh. Xoá thì khách không chọn tự lấy ở đây được nữa.' : 'Khách sẽ không thấy cửa hàng này nữa.', 'Xoá', true)) return;
        await ghi('luu_thong_tin', {phan: 'cua_hang', gia_tri: ds.filter((_, j) => j !== i), dau_cu: B.dau_thong_tin.cua_hang}, 'Đã xoá "' + c.ten + '".');
        ve();
      };
      nut.append(s, x); phai.append(ct, nut); d.append(trai, phai); hang.append(d);
    });
    g.append(hang);
    return g;
  }
  async function moCuaHang(i) {
    if (!await roiDi()) return;
    const c = i >= 0 ? JSON.parse(JSON.stringify(B.thong_tin.cua_hang[i])) :
      {id: 'cua-hang-' + Date.now().toString(36), ten: '', dia_chi: '', gio_mo_cua: '', hotline: '', chi_duong: '', loai: 'cua_hang', nhan_banh: false, hien: true};
    sua = {loai: 'cua_hang', muc: c, moi: i < 0, chiSo: i, dau: B.dau_thong_tin.cua_hang, goc: JSON.stringify(c)};
    ve();
  }
  function formCuaHang() {
    const c = sua.muc, t = THE.find(x => x.k === 'cua_hang');
    const khung = tao('section', 'bt-form-khung');
    const lui = tao('button', 'bt-lui', '← ' + t.dau.toUpperCase()); lui.type = 'button';
    lui.onclick = async () => { if (!await roiDi()) return; sua = null; ve(); };
    const f = tao('form', 'bt-form'); f.noValidate = true;
    const dat = truong => v => { c[truong] = v; };
    f.append(
      o('Tên cửa hàng', c.ten, dat('ten'), {ten: 'ten', goi: 'Cửa hàng Sài Gòn'}),
      chip('Loại', ['Cửa hàng', 'Bếp'], () => (c.loai === 'bep' ? 'Bếp' : 'Cửa hàng'), v => { c.loai = v === 'Bếp' ? 'bep' : 'cua_hang'; }, false),
      o('Địa chỉ', c.dia_chi, dat('dia_chi'), {ten: 'dia_chi', goi: '9 Trần Cao Vân, P. Sài Gòn'}),
      o('Giờ mở cửa (không bắt buộc)', c.gio_mo_cua, dat('gio_mo_cua'), {nhieuDong: true, ten: 'gio_mo_cua', goi: 'Thứ 2 - Thứ 6: 7:00 - 21:00\nThứ 7, Chủ nhật: 7:30 - 22:00', chu: 'Mỗi dòng một khung giờ.'}),
      o('Hotline riêng (không bắt buộc)', c.hotline, dat('hotline'), {kieu: 'tel', ten: 'hotline', goi: B.lien_he.dien_thoai, chu: 'Để trống là dùng số chung ở thẻ Liên hệ.'}),
      o('Link chỉ đường (không bắt buộc)', c.chi_duong, dat('chi_duong'), {kieu: 'url', ten: 'chi_duong', goi: 'https://maps.app.goo.gl/...', chu: 'Mở Google Maps, tìm cửa hàng, bấm Chia sẻ rồi chép đường dẫn vào đây.'}),
      congTac('Nhận bánh tại đây', c.nhan_banh, dat('nhan_banh'), bat => bat ? 'Khách chọn được điểm này ở bước Tự lấy trong giỏ hàng' : 'Không hiện ở bước Tự lấy'),
      congTac('Hiện trên web', c.hien, dat('hien'), bat => bat ? 'Lưu xong khách thấy ngay ở cuối trang' : 'Lưu xong vẫn ẩn'),
    );
    const hang = tao('div', 'bt-hang-nut bt-chan-form');
    const luu = tao('button', 'bt-nut chinh', t.luu); luu.type = 'submit'; luu.dataset.luu = '1';
    const huy = tao('button', 'bt-nut vien', 'Huỷ'); huy.type = 'button'; huy.onclick = () => lui.onclick();
    hang.append(luu, huy); f.append(hang);
    f.onsubmit = async e => {
      if (e && e.preventDefault) e.preventDefault();
      if (!c.ten.trim()) { bao('Điền tên cửa hàng trước khi lưu.', true); return; }
      const ds = (B.thong_tin.cua_hang || []).slice();
      if (sua.chiSo >= 0) ds[sua.chiSo] = c; else ds.push(c);
      const ok = await ghi('luu_thong_tin', {phan: 'cua_hang', gia_tri: ds, dau_cu: sua.dau}, 'Đã lưu "' + c.ten + '". Khách thấy ngay.');
      if (ok) { sua = null; ve(); }
    };
    khung.append(lui, tao('h2', 'bt-tieu-form', (sua.moi ? 'Thêm ' : 'Sửa ') + 'cửa hàng'), f);
    return khung;
  }

  /* ------------------------------------------------------------ liên hệ */
  function formLienHe() {
    const lh = Object.assign({}, B.lien_he);
    const goc = JSON.stringify(lh);
    const khung = tao('section', 'bt-form-khung');
    const f = tao('form', 'bt-form'); f.noValidate = true;
    const dat = truong => v => { lh[truong] = v; lhDoi = JSON.stringify(lh) !== goc; };
    const AN = 'Để trống là ẩn ở chân trang và biên nhận.';
    const ds = [['zalo', 'Zalo', 'https://zalo.me/...', 'Nút Nhắn Zalo ở biên nhận. Để trống là dùng số điện thoại ở trên làm Zalo.'],
      ['messenger', 'Messenger', 'https://m.me/...', AN], ['facebook', 'Facebook', 'https://facebook.com/...', AN],
      ['instagram', 'Instagram', 'https://instagram.com/...', AN], ['tiktok', 'TikTok', 'https://www.tiktok.com/@...', AN]];
    f.append(
      muc(1, 'Liên lạc'),
      o('Số điện thoại', lh.dien_thoai, dat('dien_thoai'), {kieu: 'tel', ten: 'dien_thoai', goi: '0931 224 334', chu: 'Đổi ở đây là đổi ở đầu trang, chân trang, nút gọi và mọi câu nhắc gọi trên web.'}),
      o('Email', lh.email, dat('email'), {kieu: 'email', ten: 'email', goi: 'hello@thevagabondpatisserie.com', chu: 'Hiện ở chân trang. Vị trí tuyển dụng mới tự điền sẵn email này.'}),
      muc(2, 'Mạng xã hội'),
    );
    ds.forEach(([k, nhan, goi, chu]) => f.append(o(nhan, lh[k], dat(k), {kieu: 'url', ten: k, goi: goi, chu: chu})));
    f.append(muc(3, 'Công ty'));
    const pn = B.phap_nhan || {};
    const the2 = tao('div', 'bt-chi-doc');
    the2.append(tao('b', '', pn.ten || ''), tao('p', '', 'Mã số thuế ' + (pn.mst || '')));
    (pn.dia_chi || []).forEach(d => the2.append(tao('p', '', d.ten + ': ' + d.dia_chi)));
    the2.append(tao('span', 'bt-goi-y', 'Thông tin đăng ký kinh doanh in ở chân mọi trang. Muốn đổi thì báo kế toán và anh Việt, không sửa ở đây.'));
    f.append(the2);
    const hang = tao('div', 'bt-hang-nut bt-chan-form');
    const luu = tao('button', 'bt-nut chinh', 'Lưu liên hệ'); luu.type = 'submit'; luu.dataset.luu = '1';
    hang.append(luu); f.append(hang);
    f.onsubmit = async e => {
      if (e && e.preventDefault) e.preventDefault();
      const ok = await ghi('luu_lien_he', {gia_tri: lh, dau_cu: B.dau_lien_he}, 'Đã lưu liên hệ. Khách thấy ngay ở mọi trang.');
      if (ok) { lhDoi = false; ve(); }
    };
    khung.append(f);
    return khung;
  }

  /* ------------------------------------------------------------ trang và chữ */
  const choDien = s => (String(s || '').match(/\{[a-z_]+\}/g) || []).sort();
  function loiChu(khoa, chu) {
    if (!chu.trim()) return '';
    const mau = (B.nhan_mau[khoa] || {}).mac_dinh || '';
    const thieu = choDien(mau).filter(x => !choDien(chu).includes(x));
    if (thieu.length) return 'Giữ nguyên ' + thieu.join(', ') + ': máy điền số vào chỗ này.';
    const la = choDien(chu).filter(x => !choDien(mau).includes(x));
    if (la.length) return 'Máy không hiểu ' + la.join(', ') + '. Xoá đi hoặc dùng đúng chỗ điền có sẵn.';
    return '';
  }
  function theChu() {
    const g = tao('section', 'bt-chu');
    const nhomTen = B.nhom_nhan || {};
    const tatCa = Object.entries(B.nhan_mau).map(([k, v]) => ({k, ten: v.ten, mac_dinh: v.mac_dinh, nhom: nhomTen[v.nhom || ''] || 'Khác', nhieu: !!v.nhieu_dong || k.indexOf('dat_ban_') === 0}));
    const dau = tao('div', 'bt-dau-ds');
    const tim = tao('input', 'bt-tim'); tim.type = 'search'; tim.placeholder = 'Gõ câu đang thấy trên web, ví dụ Đặt bánh trước'; tim.value = timChu;
    tim.setAttribute('aria-label', 'Tìm câu chữ trên web');
    dau.append(tim);
    g.append(dau, tao('p', 'bt-chu-phu', 'Để trống một câu là dùng chữ mặc định. Chỗ trong ngoặc nhọn như {so} là máy điền số, giữ nguyên.'));
    const chips = tao('div', 'bt-chips');
    const nhom = [...new Set(tatCa.map(x => x.nhom))];
    ['', ...nhom].forEach(n => {
      const so = tatCa.filter(x => !n || x.nhom === n).length;
      const b = tao('button', 'bt-chip' + (n === nhomChu ? ' dang' : ''), (n || 'Tất cả') + ' · ' + so); b.type = 'button'; b.dataset.nhomChu = n || 'tat_ca';
      b.setAttribute('aria-pressed', String(n === nhomChu));
      b.onclick = () => { nhomChu = n; ve(); };
      chips.append(b);
    });
    g.append(chips);
    const hang = tao('div', 'bt-hang-chu');
    const TOI_DA = 60;
    function veHang() {
      hang.replaceChildren();
      const q = timChu.trim().toLocaleLowerCase('vi');
      const loc = tatCa.filter(x => (!nhomChu || x.nhom === nhomChu) && (!q || [x.ten, x.mac_dinh, B.nhan[x.k] || '', chuSua[x.k] || ''].join(' ').toLocaleLowerCase('vi').includes(q)));
      loc.sort((a, b) => (B.nhan[b.k] ? 1 : 0) - (B.nhan[a.k] ? 1 : 0));
      if (!loc.length) { hang.append(tao('p', 'bt-rong', 'Không thấy câu nào khớp "' + timChu + '".')); return; }
      loc.slice(0, TOI_DA).forEach(x => {
        const d = tao('div', 'bt-dong-chu'); d.dataset.khoa = x.k;
        const dangCo = Object.prototype.hasOwnProperty.call(chuSua, x.k) ? chuSua[x.k] : (B.nhan[x.k] || '');
        const dau2 = tao('div', 'bt-nhan-hang');
        dau2.append(tao('b', '', x.ten), tao('span', 'bt-tt an', x.nhom));
        if (B.nhan[x.k]) dau2.append(tao('span', 'bt-tt dang', 'Đã sửa'));
        const loi = tao('span', 'bt-loi');
        const i = tao(x.nhieu ? 'textarea' : 'input'); if (!x.nhieu) i.type = 'text'; else i.rows = 2;
        i.value = dangCo; i.placeholder = x.mac_dinh; i.setAttribute('aria-label', x.ten);
        i.oninput = () => {
          const cu = B.nhan[x.k] || '';
          if (i.value === cu) delete chuSua[x.k]; else chuSua[x.k] = i.value;
          loi.textContent = loiChu(x.k, i.value);
          veChan();
        };
        const md = tao('span', 'bt-goi-y', 'Mặc định: ' + x.mac_dinh);
        const ve2 = tao('button', 'bt-nut nho', 'Về mặc định'); ve2.type = 'button'; ve2.hidden = !dangCo;
        ve2.onclick = () => { i.value = ''; i.oninput(); ve2.hidden = true; };
        loi.textContent = loiChu(x.k, dangCo);
        d.append(dau2, i, md, loi, ve2);
        hang.append(d);
      });
      if (loc.length > TOI_DA) hang.append(tao('p', 'bt-rong', 'Còn ' + (loc.length - TOI_DA) + ' câu nữa. Gõ vào ô tìm để thu hẹp.'));
    }
    tim.oninput = () => { timChu = tim.value; veHang(); };
    const chan = tao('div', 'bt-chan-luu'); chan.hidden = true;
    const dem = tao('span', '');
    const luu = tao('button', 'bt-nut chinh', 'Lưu'); luu.type = 'button'; luu.dataset.luu = '1';
    const bo = tao('button', 'bt-nut vien', 'Bỏ thay đổi'); bo.type = 'button';
    function veChan() {
      const n = Object.keys(chuSua).length;
      chan.hidden = !n; dem.textContent = n + ' câu đã sửa, chưa lưu';
      luu.textContent = 'Lưu ' + n + ' câu';
    }
    bo.onclick = () => { chuSua = {}; ve(); };
    luu.onclick = async () => {
      const loi = Object.keys(chuSua).map(k => loiChu(k, chuSua[k])).filter(Boolean);
      if (loi.length) { bao('Còn câu chưa hợp lệ: ' + loi[0], true); return; }
      const thay = {}; Object.keys(chuSua).forEach(k => { thay[k] = [B.nhan[k] || '', chuSua[k]]; });
      const n = Object.keys(thay).length;
      const ok = await ghi('luu_nhan', {thay: thay}, 'Đã lưu ' + n + ' câu. Khách thấy ngay khi tải lại trang.');
      if (ok) { chuSua = {}; ve(); }
    };
    chan.append(dem, luu, bo);
    veHang(); veChan();
    g.append(hang, chan);
    return g;
  }

  /* ------------------------------------------------------------ nâng cao */
  function moNangCao(mo) {
    const moi = $('bt-moi'), cu = $('bt-cu');
    if (!moi || !cu) return;
    moi.hidden = mo; cu.hidden = !mo;
    document.body.className = mo ? 'bt-che-do-cu' : 'bt-che-do-moi';
    if (mo) { const t = $('tai-lai'); if (t) t.click(); }
    else { sua = null; chuSua = {}; lhDoi = false; tai(); }
  }

  function batDau() {
    const ve2 = $('bt-ve-moi'); if (ve2) ve2.onclick = () => moNangCao(false);
    if (window.addEventListener) window.addEventListener('beforeunload', e => { if (dangDoi()) { e.preventDefault(); e.returnValue = ''; } });
    tai();
  }
  window.VgbBienTapMoi = {trangThai: trangThai, moTa: moTa, batDau: batDau};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', batDau);
  else if ($('bt-moi')) batDau();
}());
