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
    {k: 'uu_dai', ten: 'Ưu đãi', mo: 'Lấy từ ERP, chỉ xem ở đây', them: '+ Thêm ưu đãi', luu: 'Lưu ưu đãi', ten_muc: 'ưu đãi', dau: 'Danh sách ưu đãi'},
    /* v647 (anh Việt 10/11/2026): banner ảnh Marketing tự thiết kế, ba chỗ đã chốt. */
    {k: 'banner', ten: 'Banner', mo: 'Ảnh quảng cáo ở đầu trang, giỏ hàng, sau khi đặt xong', them: '+ Thêm banner', luu: 'Lưu banner', ten_muc: 'banner', dau: 'Danh sách banner'},
    /* v644 (anh Việt duyệt 07/11/2026): ảnh, mô tả, tầng hương vị từng bánh quản ở đây. */
    {k: 'banh', ten: 'Bánh', mo: 'Ảnh, mô tả, tầng hương vị từng bánh'},
    {k: 'tiec', ten: 'Tiệc', mo: 'Tạo tiệc, đặt giá vé, số vé, hạn đăng ký', them: '+ Thêm tiệc', luu: 'Lưu tiệc', ten_muc: 'tiệc', dau: 'Danh sách tiệc'},
    /* v630 (anh Việt chốt 02/11/2026): bánh thiết kế riêng, khách cọc 50% trên web. */
    {k: 'thiet_ke_rieng', ten: 'Thiết kế riêng', mo: 'Tác phẩm đặt riêng: size, giá gồm VAT, trang trí, số ngày đặt trước', them: '+ Thêm tác phẩm', luu: 'Lưu tác phẩm', ten_muc: 'tác phẩm', dau: 'Danh sách tác phẩm'},
    {k: 'tuyen_dung', ten: 'Tuyển dụng', mo: 'Lấy từ app ERP, đổi ảnh từng vị trí ở đây', them: '+ Thêm vị trí', luu: 'Lưu vị trí', ten_muc: 'vị trí', dau: 'Danh sách tuyển dụng'},
    {k: 'cau_hoi', ten: 'Câu hỏi ứng tuyển', mo: 'Câu hỏi trong form ứng tuyển, phúc lợi chung'},
    {k: 'cua_hang', ten: 'Cửa hàng', mo: 'Địa chỉ, giờ mở cửa, hotline, chỉ đường', them: '+ Thêm cửa hàng', luu: 'Lưu cửa hàng', ten_muc: 'cửa hàng', dau: 'Danh sách cửa hàng'},
    {k: 'chu', ten: 'Trang và chữ', mo: 'Tiêu đề từng trang, khẩu hiệu, chân trang, câu nhắc'},
    {k: 'lien_he', ten: 'Liên hệ', mo: 'Điện thoại, email, mạng xã hội, công ty'},
  ];
  const LOAI_MUC = ['uu_dai', 'tiec', 'tuyen_dung', 'thiet_ke_rieng', 'banner'];
  /* v647: chỗ đặt banner. Mã trùng noi_dung_web.VI_TRI_BANNER, chữ là tên khách
     thấy trên trang để Minh Vũ nhận ra ngay. */
  const CHO_BANNER = [
    {ma: 'dau_trang', ten: 'Đầu trang', mo: 'Dưới thanh tiêu đề, trước các tab bánh. Ai vào trang cũng thấy.'},
    {ma: 'gio_hang', ten: 'Giỏ hàng', mo: 'Màn Thông tin đơn hàng, ngay trên phần tổng tiền.'},
    {ma: 'dat_xong', ten: 'Đặt xong', mo: 'Hiện ngay sau khi khách gửi đơn thành công.'},
    {ma: 'club', ten: 'Trang thành viên', mo: 'Ảnh lớn trên trang đăng nhập The Vagabond Club. Banner thứ nhất là ảnh dọc bên trái, banner thứ hai là ảnh nhỏ bên phải.'},
  ];
  const tenCho = ma => (CHO_BANNER.find(c => c.ma === ma) || {}).ten || '';
  const HINH_THUC = ['Toàn thời gian', 'Bán thời gian', 'Thời vụ'];

  let B = null;            // dữ liệu máy chủ (bang_moi): bản khách đang thấy
  let the = 'uu_dai';
  let sua = null;          // {loai, muc, moi, dau, goc} khi đang mở form
  let ban = false;
  let chuSua = {};         // thẻ Trang và chữ: {khoá: chữ mới} chưa lưu
  let lhDoi = false;       // thẻ Liên hệ đang có chữ chưa lưu
  let fSua = null;         // v625 thẻ Câu hỏi ứng tuyển: bản đang sửa {cau_hoi, phuc_loi, gioi_thieu}
  let fGoc = '';           // bản gốc (JSON) để biết có thay đổi chưa lưu
  let fMo = -1;            // câu đang mở để sửa
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
    if (k.loai === 'thiet_ke_rieng') return ['dang', 'Đang nhận đặt'];
    if (k.loai === 'banner') {
      if (kt && kt < hn) return ['het', 'Đã hết hạn'];
      if (bd && bd > hn) return ['sap', 'Chưa tới ngày hiện'];
      return ['dang', 'Đang hiện'];
    }
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
  function khachThay(k) {
    if (k.loai === 'banner') return !!k.hien && !!k.anh && trangThai(k, homNay())[0] === 'dang';
    return window.vgbKhachThayMuc ? window.vgbKhachThayMuc(k, homNay()) : !!k.hien;
  }
  function chuCongTac(k) {
    if (!k.hien) return 'Khách không thấy';
    if (k.loai === 'banner' && !k.anh) return 'Chưa có ảnh, khách không thấy';
    if (k.loai === 'banner' && trangThai(k, homNay())[0] === 'sap') return 'Chưa tới ngày, khách chưa thấy';
    if (!khachThay(k)) return 'Đã hết hạn, khách không thấy';
    return trangThai(k, homNay())[0] === 'sap' ? 'Khách thấy nhãn Sắp diễn ra' : 'Khách đang thấy';
  }
  function moTa(k) {
    if (k.loai === 'banner') {
      return [tenCho(k.vi_tri) || 'Chưa chọn chỗ đặt', k.lien_ket ? 'bấm mở ' + k.lien_ket : 'không có link',
        k.bat_dau || k.ket_thuc ? [ngayVN(k.bat_dau), ngayVN(k.ket_thuc)].filter(Boolean).join(' - ') : 'không giới hạn ngày',
        k.anh_dt ? 'có ảnh điện thoại' : 'dùng chung ảnh máy tính'].join(' · ');
    }
    if (k.loai === 'uu_dai') {
      return [k.ma_uu_dai ? 'Mã ' + k.ma_uu_dai : '', +k.don_toi_thieu > 0 ? 'Đơn từ ' + tien(k.don_toi_thieu) : '',
        k.gio_bat_dau ? gio(k.gio_bat_dau) + ' - ' + gio(k.gio_ket_thuc) : '',
        k.bat_dau || k.ket_thuc ? [ngayVN(k.bat_dau), ngayVN(k.ket_thuc)].filter(Boolean).join(' - ') : 'không giới hạn ngày'].filter(Boolean).join(' · ');
    }
    if (k.loai === 'thiet_ke_rieng') {
      const kc = k.kich_co || [];
      return [kc.length ? kc.map(x => x.ten + ' ' + tien(x.gia)).join(', ') : 'Chưa có size', 'đặt trước ' + (k.so_ngay || 7) + ' ngày',
        (k.trang_tri || []).length + ' trang trí'].join(' · ');
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
  async function api(ham, duLieu, moDun) {
    const cau = {credentials: 'same-origin', headers: {Accept: 'application/json'}};
    if (duLieu) {
      cau.method = 'POST'; cau.headers['Content-Type'] = 'application/json';
      const m = document.querySelector('meta[name=csrf-token]'); if (m) cau.headers['X-Frappe-CSRF-Token'] = m.content;
      cau.body = JSON.stringify(duLieu);
    }
    const r = await fetch('/api/method/vagabond.' + (moDun || 'noi_dung_web') + '.' + ham, cau);
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
    if (fSua && JSON.stringify(fSua) !== fGoc) return true;
    if (bSua && JSON.stringify(bSua) !== bGoc) return true;
    return lhDoi || Object.keys(chuSua).length > 0;
  }
  async function roiDi() {
    if (!dangDoi()) return true;
    return hoi('Bỏ thay đổi chưa lưu?', 'Những gì vừa gõ chưa được lưu và sẽ mất.', 'Bỏ thay đổi', true);
  }

  /* ------------------------------------------------------------ khung */
  function demThe(k) {
    if (!B) return '';
    if (k === 'uu_dai') return String((B.uu_dai_erp || []).length);
    if (k === 'tuyen_dung') return String((B.tuyen_dung_erp || []).length);
    if (LOAI_MUC.includes(k)) return String(B.khoi.filter(x => x.loai === k).length);
    if (k === 'cua_hang') return String((B.thong_tin.cua_hang || []).length);
    if (k === 'cau_hoi') return String(((B.tuyen_dung_form || {}).cau_hoi || []).length);
    if (k === 'banh') return B.banh_cho_anh ? String(B.banh_cho_anh) : '';
    return '';
  }
  /* Codex PR #547: đang lưu hay đang tải ảnh thì không đổi thẻ, không đổi bánh.
     Đổi giữa chừng là dựng lại bản sửa từ dữ liệu cũ trước khi máy chủ trả lời,
     rồi lần Lưu sau ghi đè bản vừa lưu. */
  function choXong() {
    if (!ban) return false;
    bao('Đang lưu hoặc tải ảnh. Chờ xong rồi chuyển.');
    return true;
  }
  function veThe() {
    const g = $('bt-the'); if (!g) return;
    g.replaceChildren();
    THE.forEach(t => {
      const b = tao('button', 'bt-o-the' + (t.k === the ? ' dang' : '')); b.type = 'button';
      b.setAttribute('role', 'tab'); b.setAttribute('aria-selected', String(t.k === the)); b.dataset.the = t.k;
      const dau = tao('span', 'bt-ten-the', t.ten); const so = demThe(t.k); if (so) dau.append(tao('span', 'bt-dem', so));
      b.append(dau, tao('span', 'bt-mo-the', t.mo));
      b.onclick = async () => { if (t.k === the && !sua) return; if (choXong()) return; if (!await roiDi()) return; the = t.k; sua = null; chuSua = {}; lhDoi = false; timMuc = ''; fSua = null; fMo = -1; bSua = null; bGoc = ''; BB = null; bBao = ''; ve(); };
      g.append(b);
    });
    const nc = tao('button', 'bt-o-the bt-nang-cao'); nc.type = 'button'; nc.dataset.the = 'nang_cao';
    nc.append(tao('span', 'bt-ten-the', 'Nâng cao'), tao('span', 'bt-mo-the', 'Ảnh bìa, câu hỏi, kênh đặt hàng, nội dung bánh, chính sách, lịch sử'));
    nc.onclick = async () => { if (choXong()) return; if (!await roiDi()) return; moNangCao(true); };
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
    else if (the === 'cau_hoi') noi = theCauHoi();
    else if (the === 'banh') noi = theBanh();
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
  /* v630: MỘT chỗ tải ảnh công khai (form mục và ảnh thẻ tuyển dụng cùng gọi). */
  async function taiAnhLen(f) {
    if (f.size > 10 * 1024 * 1024) throw new Error('Chọn ảnh dưới 10 MB.');
    const form = new FormData(); form.append('file', f);
    const m2 = document.querySelector('meta[name=csrf-token]');
    const r = await fetch('/api/method/vagabond.noi_dung_web.tai_anh', {method: 'POST', credentials: 'same-origin', headers: m2 ? {'X-Frappe-CSRF-Token': m2.content} : {}, body: form});
    let d = {};
    try { d = await r.json(); } catch (_) { /* phản hồi không phải JSON: dùng câu chung */ }
    if (!r.ok || !d.message || !d.message.url) {
      let chu = 'Không tải được ảnh. Chọn PNG, JPG hoặc WebP dưới 10 MB.';
      try { const tb = JSON.parse(d._server_messages || '[]').map(x => JSON.parse(x).message); if (tb.length) chu = tb.join(' '); } catch (_) { /* giữ câu chung */ }
      throw new Error(chu);
    }
    return d.message.url;
  }
  /* v647: thêm `truong`, `nhan`, `goiY` để banner có hai ô ảnh (máy tính, điện thoại). */
  function oAnh(m, xem, truong, nhan, goiY) {
    truong = truong || 'anh';
    const g = tao('div', 'bt-o'); g.append(tao('span', 'bt-nhan', nhan || 'Ảnh (không bắt buộc)'));
    if (truong !== 'anh') g.dataset.oAnh = truong;
    const hang = tao('div', 'bt-hang-anh');
    const anh = tao('img', 'bt-anh-nho'); anh.alt = ''; if (m[truong]) anh.src = m[truong]; anh.hidden = !m[truong];
    const tep = tao('input'); tep.type = 'file'; tep.accept = 'image/png,image/jpeg,image/webp'; tep.dataset.tepAnh = truong;
    const bo = tao('button', 'bt-nut nho', 'Bỏ ảnh'); bo.type = 'button'; bo.hidden = !m[truong];
    bo.onclick = () => { m[truong] = ''; anh.hidden = true; bo.hidden = true; xem(); };
    tep.onchange = async () => {
      const f = tep.files && tep.files[0]; if (!f) return;
      khoa(true); bao('Đang tải ảnh...');
      try {
        m[truong] = await taiAnhLen(f); anh.src = m[truong]; anh.hidden = false; bo.hidden = false; xem();
        bao('Đã tải ảnh. Bấm lưu để gắn ảnh vào trang.');
      } catch (e) { bao(e.message, true); } finally { khoa(false); }
    };
    hang.append(anh, tep, bo); g.append(hang);
    g.append(tao('span', 'bt-goi-y', goiY || 'Ảnh ngang 1920 x 1080 (16:9) hiện trọn, không bị cắt. Để trống thì web tự dựng nền theo màu thương hiệu.'));
    return g;
  }

  /* ------------------------------------------------------------ danh sách */
  /* v589 (anh Việt 09/10/2026): ưu đãi lấy từ ERP, nguồn duy nhất. Thẻ này
     chỉ xem: tạo, sửa, bật tắt ở app ERP, chương trình khuyến mãi tích "Hiện
     trên website". Ưu đãi gõ tay trước đây vẫn nằm trong dữ liệu nhưng không
     còn ra trang khách. */
  function dsUuDaiErp() {
    const g = tao('section', 'bt-ds'); g.setAttribute('aria-label', 'Danh sách ưu đãi');
    const dau = tao('div', 'bt-dau-ds');
    const mo = tao('a', 'bt-nut chinh', 'Mở Chương trình khuyến mãi trên ERP'); mo.setAttribute('href', '/khuyen-mai'); mo.setAttribute('target', '_blank'); mo.setAttribute('rel', 'noopener');
    dau.append(mo);
    g.append(dau);
    g.append(tao('p', 'bt-rong', 'Ưu đãi trên web lấy thẳng từ ERP. Tạo hoặc sửa chương trình ở app: Bán hàng, Chương trình khuyến mãi, bật mục Website. Bật, tắt hay hết hạn trên ERP là web đổi theo ngay, không nhập lại ở đây.'));
    const hang = tao('div', 'bt-hang');
    const ds = B.uu_dai_erp || [];
    if (!ds.length) hang.append(tao('p', 'bt-rong', 'Chưa có chương trình nào bật Hiện trên website.'));
    ds.forEach(k => {
      const d = tao('article', 'bt-dong'); d.dataset.mucErp = k.ma_ctkm || k.id;
      const trai = tao('div', 'bt-dong-trai');
      const nhan = tao('div', 'bt-nhan-hang');
      nhan.append(tao('span', 'bt-tt ' + (k.khach_thay ? 'dang' : 'het'), k.trang_thai_erp || ''));
      if (!k.dung_web) nhan.append(tao('span', 'bt-tt an', 'Chỉ dùng tại cửa hàng'));
      trai.append(nhan, tao('h3', 'bt-ten', k.tieu_de || '(chưa đặt tên)'), tao('p', 'bt-meta', moTa(k)));
      d.append(trai);
      hang.append(d);
    });
    g.append(hang);
    return g;
  }

  /* v622 (anh Việt 30/10/2026): vị trí tuyển dụng lấy từ app ERP (Nhân sự,
     Tuyển dụng), nguồn duy nhất như ưu đãi. Thẻ này chỉ xem; bật tắt trên app
     là web đổi theo, ứng viên bấm Ứng tuyển mở form ghi thẳng vào app. */
  function dsTuyenDungErp() {
    const g = tao('section', 'bt-ds'); g.setAttribute('aria-label', 'Danh sách tuyển dụng');
    const dau = tao('div', 'bt-dau-ds');
    const mo = tao('a', 'bt-nut chinh', 'Mở Tuyển dụng trên app'); mo.setAttribute('href', '/tuyen-dung'); mo.setAttribute('target', '_blank'); mo.setAttribute('rel', 'noopener');
    dau.append(mo);
    g.append(dau);
    g.append(tao('p', 'bt-rong', 'Vị trí tuyển dụng trên web lấy thẳng từ app. Thêm, sửa nội dung hoặc bật tắt vị trí ở app: Nhân sự, Tuyển dụng. Ảnh thẻ của từng vị trí đổi ngay ở đây, khách thấy liền. Ứng viên bấm Ứng tuyển là mở form, hồ sơ về thẳng app, không qua email.'));
    const hang = tao('div', 'bt-hang');
    const ds = B.tuyen_dung_erp || [];
    if (!ds.length) hang.append(tao('p', 'bt-rong', 'Chưa có vị trí nào trên app.'));
    ds.forEach(k => {
      const d = tao('article', 'bt-dong'); d.dataset.mucErp = k.ma_vi_tri || k.id;
      const trai = tao('div', 'bt-dong-trai');
      const nhan = tao('div', 'bt-nhan-hang');
      nhan.append(tao('span', 'bt-tt ' + (k.khach_thay ? 'dang' : 'het'), k.trang_thai_erp || ''));
      trai.append(nhan, tao('h3', 'bt-ten', k.tieu_de || '(chưa đặt tên)'), tao('p', 'bt-meta', moTa(k)));
      d.append(trai, anhTuyenDung(k));
      hang.append(d);
    });
    g.append(hang);
    return g;
  }

  /* v630 (Minh Vũ 02/11/2026): ảnh thẻ của từng vị trí, đổi ngay ở đây. Ảnh
     lưu thẳng vào vị trí trên app (nguồn duy nhất), khách thấy liền. */
  function anhTuyenDung(k) {
    const ma = k.ma_vi_tri || k.ma;
    const phai = tao('div', 'bt-dong-phai bt-anh-vi-tri');
    const anh = tao('img', 'bt-anh-nho'); anh.alt = 'Ảnh thẻ ' + (k.tieu_de || ''); anh.hidden = !k.anh_the; if (k.anh_the) anh.src = k.anh_the;
    const ghiChu = tao('span', 'bt-goi-y', k.anh_web ? 'Ảnh tải riêng cho vị trí này' : 'Ảnh tự chọn theo bộ phận');
    ghiChu.dataset.nguonAnh = ma;
    const tep = tao('input'); tep.type = 'file'; tep.accept = 'image/png,image/jpeg,image/webp'; tep.hidden = true; tep.dataset.tepAnh = ma;
    const doi = tao('button', 'bt-nut nho', 'Đổi ảnh'); doi.type = 'button'; doi.dataset.doiAnh = ma;
    doi.setAttribute('aria-label', 'Đổi ảnh thẻ của ' + (k.tieu_de || 'vị trí'));
    doi.onclick = () => { if (!ban) tep.click(); };
    tep.onchange = async () => {
      const f = tep.files && tep.files[0]; if (!f || ban) return;
      khoa(true); bao('Đang tải ảnh...');
      let url = '';
      try { url = await taiAnhLen(f); } catch (e) { bao(e.message, true); } finally { khoa(false); }
      if (url && await ghi('doi_anh_tuyen_dung', {ma_vi_tri: ma, anh: url}, 'Đã đổi ảnh của ' + (k.tieu_de || 'vị trí') + '. Khách tải lại trang sẽ thấy ảnh mới.')) ve();
    };
    const nut = tao('div', 'bt-hang-nut'); nut.append(doi);
    if (k.anh_web) {
      const veTuChon = tao('button', 'bt-nut nho', 'Dùng ảnh tự chọn'); veTuChon.type = 'button'; veTuChon.dataset.anhTuChon = ma;
      veTuChon.onclick = async () => {
        if (await ghi('doi_anh_tuyen_dung', {ma_vi_tri: ma, anh: ''}, 'Đã trả ' + (k.tieu_de || 'vị trí') + ' về ảnh tự chọn theo bộ phận.')) ve();
      };
      nut.append(veTuChon);
    }
    phai.append(anh, ghiChu, nut, tep);
    return phai;
  }

  function dsMuc(loai) {
    if (loai === 'uu_dai') return dsUuDaiErp();
    if (loai === 'tuyen_dung') return dsTuyenDungErp();
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
    if (loai === 'banner') return Object.assign(goc, {vi_tri: 'gio_hang', anh_dt: '', lien_ket: '/thanh-vien', bat_dau: homNay(), ket_thuc: ''});
    if (loai === 'thiet_ke_rieng') return Object.assign(goc, {nhan: '', yeu_cau: '', dieu_kien: 'Giá đã gồm VAT.', so_ngay: '7',
      kich_co: [{ten: 'S', mo_ta: '', gia: ''}], trang_tri: []});
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
  /* v630: danh sách dòng nhiều ô (size, trang trí của tác phẩm thiết kế riêng).
     cot: [khoá, nhãn, gợi ý, là số]. Thêm, bỏ dòng tại chỗ, không mở hộp riêng. */
  function dsDong(m, truong, cot, mau, nhanThem, toiDa, xem) {
    const g = tao('div', 'bt-ds-dong'); g.dataset.dsDong = truong;
    function ve() {
      g.replaceChildren();
      (m[truong] || []).forEach((d, i) => {
        const hang = tao('div', 'bt-dong-o'); hang.dataset.dongO = truong + '-' + i;
        cot.forEach(([k, nhan, goi, so]) => hang.append(o(nhan, d[k], v => { d[k] = v; xem(); }, {ten: truong + '_' + k + '_' + i, goi, so: !!so})));
        const bo = tao('button', 'bt-nut chu-do nho', 'Bỏ dòng'); bo.type = 'button'; bo.dataset.boDong = truong + '-' + i;
        bo.onclick = () => { m[truong].splice(i, 1); ve(); xem(); };
        hang.append(bo); g.append(hang);
      });
      if ((m[truong] || []).length < toiDa) {
        const them = tao('button', 'bt-nut vien', nhanThem); them.type = 'button'; them.dataset.themDong = truong;
        them.onclick = () => { m[truong] = (m[truong] || []).concat([Object.assign({}, mau)]); ve(); xem(); };
        g.append(them);
      }
    }
    ve();
    return g;
  }
  /* Kiểm sớm trên trình duyệt; máy chủ kiểm lại đủ (noi_dung_web.chuan_tkr). */
  function loiTacPham(m) {
    const kc = m.kich_co || [];
    if (!kc.length) return 'Thêm ít nhất một size có giá.';
    const ten = kc.map(x => String(x.ten || '').trim().toLowerCase());
    if (ten.some(x => !x)) return 'Mỗi size cần có tên.';
    if (new Set(ten).size !== ten.length) return 'Tên size bị trùng.';
    if (kc.some(x => !(parseInt(String(x.gia).replace(/[^0-9]/g, ''), 10) > 0))) return 'Mỗi size cần giá gồm VAT lớn hơn 0.';
    if (!(parseInt(m.so_ngay, 10) >= 7)) return 'Số ngày đặt trước tối thiểu là 7.';
    if ((m.trang_tri || []).some(x => !String(x.ten || '').trim())) return 'Mỗi trang trí cần có tên.';
    return '';
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
      if (m.loai === 'thiet_ke_rieng') xemNoi.append(tao('p', 'bt-tom-tat', m.tieu_de ? m.tieu_de + ': ' + moTa(m) : 'Điền tên và size để xem tóm tắt.'));
      else if (m.loai === 'banner') xemNoi.append(xemBanner(m));
      else if (window.vgbTheMuc) xemNoi.append(window.vgbTheMuc(m, {homNay: homNay(), ve: B.ve, lienHe: B.lien_he, xemTruoc: true}));
      if (dkEl) { const c = window.vgbDieuKienUuDai ? window.vgbDieuKienUuDai(m) : ''; dkEl.replaceChildren(tao('span', '', 'Khách sẽ thấy điều kiện: '), tao('b', '', c || 'Không có điều kiện, áp dụng cả ngày.')); }
    };
    const dat = truong => v => { m[truong] = v; xem(); };

    if (loai === 'banner') {
      const cho = chip('Chỗ đặt banner', CHO_BANNER.map(c => c.ten), () => tenCho(m.vi_tri),
        v => { const c = CHO_BANNER.find(x => x.ten === v); m.vi_tri = c ? c.ma : ''; const p = cho.querySelector('[data-mo-cho]'); if (p) p.textContent = c ? c.mo : ''; xem(); }, false);
      const moCho = tao('span', 'bt-goi-y', (CHO_BANNER.find(c => c.ma === m.vi_tri) || {}).mo || 'Chọn một chỗ.'); moCho.dataset.moCho = '1';
      cho.append(moCho);
      const ngay = tao('div', 'bt-hai-cot');
      ngay.append(o('Hiện từ ngày (không bắt buộc)', m.bat_dau, dat('bat_dau'), {kieu: 'date', ten: 'bat_dau', chu: 'Để trống là hiện ngay khi lưu.'}),
        o('Đến hết ngày (không bắt buộc)', m.ket_thuc, dat('ket_thuc'), {kieu: 'date', ten: 'ket_thuc', chu: 'Qua ngày này web tự gỡ banner. Để trống là hiện tới khi tắt.'}));
      f.append(
        muc(1, 'Tên và chỗ đặt'),
        o('Tên banner', m.tieu_de, dat('tieu_de'), {ten: 'tieu_de', goi: 'Cập nhật sinh nhật nhận quà', chu: 'Chỉ để nhận ra trong danh sách này, khách không thấy.'}),
        cho,
        muc(2, 'Ảnh'),
        oAnh(m, xem, 'anh', 'Ảnh máy tính', 'Ảnh ngang 1600 x 500 (tỉ lệ 16:5), PNG, JPG hoặc WebP dưới 10 MB. Ảnh hiện trọn, không bị cắt. Bắt buộc trước khi bật hiện.'),
        oAnh(m, xem, 'anh_dt', 'Ảnh điện thoại (không bắt buộc)', 'Ảnh 1080 x 720 (tỉ lệ 3:2) cho màn hình điện thoại, chữ to hơn để đọc được. Để trống thì điện thoại dùng ảnh máy tính.'),
        o('Mô tả ảnh', m.mo_ta_anh, dat('mo_ta_anh'), {ten: 'mo_ta_anh', goi: 'Cập nhật ngày sinh để nhận quà bánh vào sinh nhật', chu: 'Chữ chính trên banner. Dùng cho người khiếm thị và hiện thay khi ảnh chưa tải được.'}),
        muc(3, 'Khi khách bấm và ngày hiện'),
        o('Mở trang khi bấm', m.lien_ket, dat('lien_ket'), {ten: 'lien_ket', goi: '/thanh-vien', chu: '/thanh-vien là trang thành viên: khách xác minh số qua Zalo rồi khai ngày sinh. Để trống thì banner không bấm được.'}),
        ngay);
    } else if (loai === 'tuyen_dung') {
      f.append(
        o('Tên vị trí', m.tieu_de, dat('tieu_de'), {ten: 'tieu_de', goi: 'Thợ làm bánh (Pâtissier)', chu: 'Ví dụ: Thợ làm bánh (Pâtissier)'}),
        noiChon('Nơi làm', 'noi_lam', m, xem, 'Hoặc gõ nơi làm khác'),
        oHinhThuc(m, xem),
        o('Hạn nhận hồ sơ (không bắt buộc)', m.ket_thuc, dat('ket_thuc'), {kieu: 'date', ten: 'ket_thuc', chu: 'Qua ngày này web tự ẩn vị trí. Để trống là nhận tới khi đủ người.'}),
        o('Mô tả công việc', m.noi_dung, dat('noi_dung'), {nhieuDong: true, ten: 'noi_dung', chu: 'Một hai câu nói công việc chính.'}),
        o('Yêu cầu và quyền lợi (không bắt buộc)', m.yeu_cau, dat('yeu_cau'), {nhieuDong: true, dong: 5, ten: 'yeu_cau', goi: 'Có kinh nghiệm làm bánh 1 năm trở lên\nĐược ăn bánh mỗi ngày', chu: 'Mỗi dòng một ý, web hiện thành danh sách.'}),
        o('Email nhận hồ sơ', m.email, dat('email'), {kieu: 'email', ten: 'email', goi: 'tuyendung@thevagabondpatisserie.com', chu: 'Ứng viên bấm Ứng tuyển là mở thư gửi về email này. Cần có email trước khi bật hiện.'}),
      );
    } else if (loai === 'thiet_ke_rieng') {
      f.append(
        muc(1, 'Nội dung'),
        o('Tên tác phẩm', m.tieu_de, dat('tieu_de'), {ten: 'tieu_de', goi: 'Croquembouche'}),
        o('Mô tả ngắn trên thẻ', m.nhan, dat('nhan'), {ten: 'nhan', goi: 'Tháp choux caramel, hoa lan trắng.', chu: 'Một câu khách đọc ở danh sách tác phẩm.'}),
        o('Câu chuyện', m.noi_dung, dat('noi_dung'), {nhieuDong: true, ten: 'noi_dung', chu: 'Vài câu về nguồn gốc, cách làm, dịp dùng.'}),
        o('Bánh gồm gì (không bắt buộc)', m.yeu_cau, dat('yeu_cau'), {nhieuDong: true, dong: 4, ten: 'yeu_cau', goi: 'Hoa lan trắng tươi cắm trên tháp\nĐế nougatine caramel', chu: 'Mỗi dòng một ý, web hiện thành danh sách.'}),
        muc(2, 'Size và giá đã gồm VAT'),
        dsDong(m, 'kich_co', [['ten', 'Tên size', 'S'], ['mo_ta', 'Kích thước, số bánh', '35-40 cm, 110-120 bánh'], ['gia', 'Giá gồm VAT (đồng)', '5940000', true]],
          {ten: '', mo_ta: '', gia: ''}, '+ Thêm size', 8, xem),
        o('Ghi chú dưới size (không bắt buộc)', m.dieu_kien, dat('dieu_kien'), {ten: 'dieu_kien', goi: 'Chiều cao không tính bục trắng. Giá đã gồm VAT.'}),
        muc(3, 'Trang trí'),
        dsDong(m, 'trang_tri', [['ten', 'Tên trang trí', 'Hoa lan trắng'], ['gia_them', 'Giá cộng thêm (đồng)', '0', true], ['nhom', 'Nhóm (chọn một trong nhóm)', 'Hoa']],
          {ten: '', gia_them: '0', nhom: ''}, '+ Thêm trang trí', 10, xem),
        tao('p', 'bt-goi-y', 'Cùng nhóm thì khách chỉ chọn một, ví dụ nhóm Hoa: Hoa lan trắng, Hoa theo màu tiệc, Không hoa. Để trống nhóm là món thêm độc lập như Thêm bục trắng. Trang trí đầu mỗi nhóm được chọn sẵn.'),
        muc(4, 'Đặt trước và cọc'),
        o('Số ngày đặt trước tối thiểu', m.so_ngay, dat('so_ngay'), {so: true, ten: 'so_ngay', goi: '7', chu: 'Không dưới 7 ngày. Khách cọc 50% (làm tròn lên tới nghìn), trả phần còn lại khi nhận bánh.'}),
        muc(5, 'Ảnh và hiển thị'), oAnh(m, xem));
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
      if (loai === 'banner') {
        const loiBn = loiBanner(m);
        if (loiBn) { bao(loiBn, true); return; }
      }
      if (loai === 'tiec' && m.hien && !m.bat_dau) { bao('Chọn ngày diễn ra tiệc trước khi bật hiện trên web.', true); return; }
      if (loai === 'thiet_ke_rieng') {
        const loiTkr = loiTacPham(m);
        if (loiTkr) { bao(loiTkr, true); return; }
      }
      if (Boolean(m.gio_bat_dau) !== Boolean(m.gio_ket_thuc)) { bao('Điền cả hai ô giờ, hoặc bỏ trống cả hai.', true); return; }
      const ok = await ghi('luu_muc', {muc: m, dau_cu: sua.dau}, 'Đã lưu ' + t.ten_muc + ' "' + m.tieu_de + '". ' + (m.hien ? (khachThay(m) ? 'Khách thấy ngay.' : 'Mục đã hết hạn nên khách chưa thấy.') : 'Đang ẩn, khách chưa thấy.'));
      if (ok) { sua = null; ve(); }
    };
    const luoi = tao('div', 'bt-luoi-form'); luoi.append(f, xemKhung);
    khung.append(lui, tieu, luoi);
    khung._sauKhiGan = xem;
    return khung;
  }

  /* v647: kiểm banner trước khi gửi, trùng luật noi_dung_web._kiem_banner. */
  function loiBanner(m) {
    if (!CHO_BANNER.some(c => c.ma === m.vi_tri)) return 'Chọn chỗ đặt banner: Đầu trang, Giỏ hàng hoặc Đặt xong.';
    if (m.hien && !m.anh) return 'Tải ảnh máy tính trước khi bật hiện trên web.';
    if (m.bat_dau && m.ket_thuc && m.bat_dau > m.ket_thuc) return 'Ngày kết thúc không được trước ngày bắt đầu.';
    return '';
  }
  /* Xem trước: hai khung máy tính và điện thoại, đúng ảnh khách sẽ thấy. */
  function xemBanner(m) {
    const g = tao('div', 'bt-xem-banner');
    [['Máy tính', m.anh], ['Điện thoại', m.anh_dt || m.anh]].forEach(([ten, url]) => {
      const o2 = tao('figure', 'bt-xem-banner-o'); o2.append(tao('figcaption', '', ten + (ten === 'Điện thoại' && !m.anh_dt && m.anh ? ' (dùng ảnh máy tính)' : '')));
      if (url) { const i = tao('img', ''); i.src = url; i.alt = m.mo_ta_anh || ''; o2.append(i); }
      else o2.append(tao('p', 'bt-rong', 'Chưa có ảnh.'));
      g.append(o2);
    });
    g.append(tao('p', 'bt-tom-tat', 'Hiện ở: ' + (tenCho(m.vi_tri) || 'chưa chọn chỗ') + '. ' + (m.lien_ket ? 'Bấm mở ' + m.lien_ket + '.' : 'Không bấm được.')));
    return g;
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
    the2.append(tao('span', 'bt-goi-y', 'Thông tin đăng ký kinh doanh in ở chân mọi trang. Muốn đổi thì báo Kế toán và quản trị hệ thống, không sửa ở đây.'));
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

  /* ------------------------------------------------------------ câu hỏi ứng tuyển */
  /* v625 (anh Việt 31/10/2026): Minh Vũ sửa câu hỏi của form /ung-tuyen ở đây,
     không cần quyền màn Tuyển dụng (không thấy hồ sơ ứng viên). Mặc định là 14
     câu của form Lark. Họ tên, số điện thoại, vị trí là câu gốc (ổ khoá): sửa
     chữ được, không xoá, luôn bắt buộc, vì app cần để gọi ứng viên. Loại câu,
     bước, câu khoá đọc từ máy chủ (tuyen_dung_mau), không chép cứng ở đây.
     Máy chủ (tuyen_dung_form.chuan_form) là nơi quyết; ở đây chỉ chặn sớm. */
  function mauForm() { return B.tuyen_dung_mau || {loai: {}, loai_tu_chon: [], buoc: {}, khoa_xoa: [], khong_cho_ai: [], loai_theo_ma: {}}; }
  function batDauSuaForm() {
    if (fSua) return;
    const g = B.tuyen_dung_form || mauForm().mac_dinh || {cau_hoi: [], phuc_loi: [], gioi_thieu: ''};
    fSua = JSON.parse(JSON.stringify({cau_hoi: g.cau_hoi || [], phuc_loi: g.phuc_loi || [], gioi_thieu: g.gioi_thieu || ''}));
    fGoc = JSON.stringify(fSua);
  }
  function maCauMoi() {
    let ma = '';
    do { ma = 'c_' + Math.random().toString(36).slice(2, 8).replace(/[^a-z0-9]/g, 'x').padEnd(6, 'x'); } while (fSua.cau_hoi.some(c => c.ma === ma));
    return ma;
  }
  function tenLoai(loai) { const l = mauForm().loai[loai]; return l ? l.ten : loai; }
  function theCauHoi() {
    batDauSuaForm();
    const M = mauForm(), g = tao('section', 'bt-ds bt-cau-hoi'); g.setAttribute('aria-label', 'Câu hỏi ứng tuyển');
    const dau = tao('div', 'bt-dau-ds');
    const luu = tao('button', 'bt-nut chinh', 'Lưu và đăng'); luu.type = 'button'; luu.dataset.luuForm = '1';
    const hoan = tao('button', 'bt-nut vien', 'Hoàn tác'); hoan.type = 'button'; hoan.dataset.hoanTac = '1';
    const xem = tao('a', 'bt-nut vien', 'Xem trang thật ↗'); xem.setAttribute('href', '/ung-tuyen'); xem.setAttribute('target', '_blank'); xem.setAttribute('rel', 'noopener');
    dau.append(luu, hoan, xem); g.append(dau);
    const doi = JSON.stringify(fSua) !== fGoc;
    g.append(tao('p', 'bt-rong', doi ? 'Có thay đổi chưa lưu. Bấm Lưu và đăng để ứng viên thấy ngay.'
      : 'Câu hỏi của form ứng tuyển trên web. Bấm một câu để sửa. Câu có ổ khoá là câu gốc: sửa chữ được, không xoá được vì app cần để gọi ứng viên.'));
    const ds = fSua.cau_hoi;
    const buoc = Object.keys(M.buoc || {1: 'Về bạn', 2: 'Kinh nghiệm', 3: 'Mong muốn'}).map(Number).sort();
    g.append(tao('p', 'bt-nhan-hang bt-dem-cau', ds.length + ' câu · ' + buoc.length + ' bước'));
    buoc.forEach(so => {
      g.append(tao('h3', 'bt-muc', 'Bước ' + so + ' · ' + ((M.buoc || {})[so] || '')));
      const hang = tao('div', 'bt-hang');
      ds.forEach((c, i) => {
        if ((+c.buoc || 1) !== so) return;
        hang.append(dongCau(c, i));
        if (fMo === i) hang.append(formCau(c, i));
      });
      if (!hang.children.length) hang.append(tao('p', 'bt-rong', 'Chưa có câu nào ở bước này.'));
      g.append(hang);
    });
    const them = tao('button', 'bt-nut vien', '+ Thêm câu hỏi'); them.type = 'button'; them.dataset.themCau = '1';
    them.onclick = () => {
      if (ds.length >= (M.toi_da_cau || 30)) { bao('Form tối đa ' + (M.toi_da_cau || 30) + ' câu. Bớt câu ít dùng trước.', true); return; }
      ds.push({ma: maCauMoi(), hoi: '', goi_y: '', loai: 'chu', lua_chon: [], cho_khac: false, bat_buoc: false, buoc: 3, vi_tri: [], ai: true});
      fMo = ds.length - 1; ve();
    };
    g.append(them);
    g.append(tao('h3', 'bt-muc', 'Lời giới thiệu đầu form'));
    g.append(o('Hiện dưới tên bước 1', fSua.gioi_thieu, v => { fSua.gioi_thieu = v; }, {nhieuDong: true, dong: 3, chu: 'Một hai câu về tiệm và lời nhắc điền nhanh. Để trống thì không hiện.'}));
    g.append(tao('h3', 'bt-muc', 'Phúc lợi chung'));
    g.append(o('Mỗi dòng một phúc lợi', (fSua.phuc_loi || []).join('\n'), v => { fSua.phuc_loi = v.split('\n').map(x => x.trim()).filter(Boolean); },
      {nhieuDong: true, dong: 4, chu: 'Hiện ở mục Quyền lợi của mọi vị trí trên web, sau quyền lợi riêng ghi trên phiếu Vị trí.'}));
    luu.onclick = async () => {
      const loi = kiemForm(fSua);
      if (loi) { bao(loi, true); return; }
      const ok = await ghi('luu_form_tuyen_dung', {gia_tri: fSua, dau_cu: B.dau_tuyen_dung_form || ''}, 'Đã lưu câu hỏi ứng tuyển. Ứng viên thấy ngay ở trang Ứng tuyển.');
      if (ok) { fSua = null; fMo = -1; ve(); }
    };
    hoan.onclick = async () => {
      if (JSON.stringify(fSua) === fGoc) return;
      if (!await hoi('Bỏ thay đổi chưa lưu?', 'Câu hỏi quay về bản ứng viên đang thấy.', 'Bỏ thay đổi', true)) return;
      fSua = null; fMo = -1; ve();
    };
    return g;
  }
  /* Chặn sớm những lỗi chắc chắn máy chủ sẽ trả về (chuan_form vẫn là nơi quyết). */
  function kiemForm(f) {
    for (let i = 0; i < f.cau_hoi.length; i++) {
      const c = f.cau_hoi[i];
      if (String(c.hoi || '').trim().length < 3) return 'Câu ' + (i + 1) + ' chưa có chữ. Điền câu hỏi ứng viên thấy.';
      if ((c.loai === 'chon_mot' || c.loai === 'chon_nhieu') && (c.lua_chon || []).filter(x => String(x).trim()).length < 2) return 'Câu "' + c.hoi + '" là câu chọn, cần ít nhất 2 lựa chọn.';
    }
    return '';
  }
  function dongCau(c, i) {
    const M = mauForm(), khoa = (M.khoa_xoa || []).includes(c.ma);
    const d = tao('article', 'bt-dong bt-dong-cau' + (fMo === i ? ' dang-sua' : '')); d.dataset.cau = c.ma;
    const trai = tao('div', 'bt-dong-trai');
    const nhan = tao('div', 'bt-nhan-hang');
    nhan.append(tao('span', 'bt-tt dang', tenLoai(c.loai)));
    if (c.bat_buoc) nhan.append(tao('span', 'bt-tt sap', 'Bắt buộc'));
    if ((c.vi_tri || []).length) nhan.append(tao('span', 'bt-tt an', 'Chỉ ' + c.vi_tri.length + ' vị trí'));
    if (khoa) nhan.append(tao('span', 'bt-tt an', '🔒 Câu gốc'));
    trai.append(nhan, tao('h3', 'bt-ten', (i + 1) + '. ' + (c.hoi || '(chưa có chữ)')));
    if (c.goi_y) trai.append(tao('p', 'bt-meta', c.goi_y));
    const phai = tao('div', 'bt-hang-nut');
    /* Lên, xuống trong cùng bước; câu đầu bước bấm lên là sang cuối bước trước. */
    const a = fSua.cau_hoi, so = +c.buoc || 1, cacBuoc = Object.keys(M.buoc || {1: 1, 2: 2, 3: 3}).map(Number).sort();
    const cungBuoc = a.map((x, j) => j).filter(j => (+a[j].buoc || 1) === so), vi = cungBuoc.indexOf(i);
    const diChuyen = huong => {
      const j = cungBuoc[vi + huong];
      if (j != null) { [a[i], a[j]] = [a[j], a[i]]; fMo = fMo === i ? j : fMo === j ? i : fMo; }
      else {
        const b = cacBuoc[cacBuoc.indexOf(so) + huong]; if (!b) return;
        const [x] = a.splice(i, 1); x.buoc = b;
        if (huong < 0) a.push(x); else a.unshift(x);
        fMo = fMo === i ? a.indexOf(x) : -1;
      }
      ve();
    };
    const dau = vi === 0 && cacBuoc.indexOf(so) === 0, cuoi = vi === cungBuoc.length - 1 && cacBuoc.indexOf(so) === cacBuoc.length - 1;
    const len = tao('button', 'bt-nut nho', '↑'); len.type = 'button'; len.setAttribute('aria-label', 'Đưa câu lên trên'); len.disabled = dau; len.dataset.lenCau = c.ma;
    const xuong = tao('button', 'bt-nut nho', '↓'); xuong.type = 'button'; xuong.setAttribute('aria-label', 'Đưa câu xuống dưới'); xuong.disabled = cuoi; xuong.dataset.xuongCau = c.ma;
    len.onclick = () => diChuyen(-1); xuong.onclick = () => diChuyen(1);
    const suaNut = tao('button', 'bt-nut nho', fMo === i ? 'Đóng' : 'Sửa'); suaNut.type = 'button'; suaNut.dataset.suaCau = c.ma;
    suaNut.onclick = () => { fMo = fMo === i ? -1 : i; ve(); };
    phai.append(len, xuong, suaNut);
    if (!khoa) {
      const xoa = tao('button', 'bt-nut nho chu-do', 'Xoá'); xoa.type = 'button'; xoa.dataset.xoaCau = c.ma;
      xoa.onclick = async () => {
        if (!await hoi('Xoá câu này?', '"' + (c.hoi || 'Câu mới') + '" sẽ không còn trong form. Câu trả lời cũ trên hồ sơ ứng viên vẫn giữ.', 'Xoá câu', true)) return;
        fSua.cau_hoi.splice(i, 1); fMo = -1; ve();
      };
      phai.append(xoa);
    }
    d.append(trai, phai);
    return d;
  }
  function formCau(c, i) {
    const M = mauForm(), coDinh = Object.prototype.hasOwnProperty.call(M.loai_theo_ma || {}, c.ma), khoa = (M.khoa_xoa || []).includes(c.ma);
    const f = tao('div', 'bt-form bt-form-cau'); f.dataset.formCau = c.ma;
    f.append(o('Câu hỏi ứng viên thấy', c.hoi, v => { c.hoi = v; }, {ten: 'hoi', chu: 'Viết như đang hỏi trực tiếp, ví dụ "Bạn có thể đi làm từ ngày nào?".'}));
    f.append(o('Dòng gợi ý dưới câu (không bắt buộc)', c.goi_y, v => { c.goi_y = v; }, {ten: 'goi_y', nhieuDong: true, dong: 2,
      chu: c.loai === 'so_tien' ? 'Máy tự thêm "Vị trí này từ ..." theo mức lương trên phiếu Vị trí.' : 'Giải thích ngắn để ứng viên trả lời đúng ý.'}));
    if (coDinh) {
      f.append(tao('p', 'bt-goi-y', 'Loại câu trả lời: ' + tenLoai(c.loai) + '. Câu có sẵn của hệ thống nên giữ loại này để app đổ đúng vào hồ sơ.'));
    } else {
      const ten = {}; (M.loai_tu_chon || []).forEach(k => { ten[(M.loai[k] || {}).ten || k] = k; });
      const nguoc = k => (M.loai[k] || {}).ten || k;
      f.append(chip('Loại câu trả lời', Object.keys(ten), () => nguoc(c.loai), v => { if (v) c.loai = ten[v]; ve(); }, false,
        (M.loai[c.loai] || {}).mo || ''));
    }
    if (c.loai === 'chon_mot' || c.loai === 'chon_nhieu') {
      f.append(o('Các lựa chọn, mỗi dòng một lựa chọn', (c.lua_chon || []).join('\n'), v => { c.lua_chon = v.split('\n').map(x => x.trim()).filter(Boolean); },
        {ten: 'lua_chon', nhieuDong: true, dong: 4, chu: 'Ít nhất 2, nhiều nhất 12 lựa chọn. Ứng viên bấm chip để chọn.'}));
      if (c.loai === 'chon_mot') f.append(congTac('Cho ghi "Khác"', c.cho_khac, v => { c.cho_khac = v; }, b => b ? 'Có thêm chip Khác... để ứng viên tự ghi' : 'Ứng viên chỉ chọn trong danh sách'));
    }
    if (khoa) f.append(tao('p', 'bt-goi-y', 'Câu gốc luôn bắt buộc và hỏi ở mọi vị trí.'));
    else {
      f.append(congTac('Bắt buộc trả lời', c.bat_buoc, v => { c.bat_buoc = v; }, b => b ? 'Ứng viên phải điền mới bấm Tiếp tục được' : 'Ứng viên bỏ trống được'));
    }
    const tenBuoc = Object.keys(M.buoc || {}).map(k => k + ' · ' + M.buoc[k]);
    f.append(chip('Nằm ở bước', tenBuoc, () => tenBuoc.find(x => +x.split(' ')[0] === (+c.buoc || 1)), v => { if (v) c.buoc = +v.split(' ')[0]; ve(); }, false,
      'Đổi bước là câu chuyển sang nhóm của bước đó.'));
    if (!khoa) {
      const vt = (B.tuyen_dung_erp || []).map(k => ({ma: k.ma_vi_tri || k.ma, ten: k.tieu_de}));
      const tenVt = vt.map(x => x.ten);
      f.append(chip('Hỏi ở vị trí nào', tenVt, () => vt.filter(x => (c.vi_tri || []).includes(x.ma)).map(x => x.ten).join(' / '),
        v => { const chon = String(v || '').split(' / ').filter(Boolean); c.vi_tri = vt.filter(x => chon.includes(x.ten)).map(x => x.ma); }, true,
        'Không chọn vị trí nào là hỏi ở mọi vị trí, kể cả vị trí mở sau này.'));
    }
    if ((M.khong_cho_ai || []).includes(c.ma)) {
      f.append(tao('p', 'bt-goi-y', 'AI không bao giờ dùng câu này khi chấm hồ sơ.'));
    } else {
      f.append(congTac('Cho AI dùng câu này khi chấm', c.ai, v => { c.ai = v; },
        b => b ? (c.loai === 'so_tien' ? 'AI so số tiền này với mức lương của vị trí' : 'AI đọc câu trả lời này cùng CV khi tóm tắt và chấm') : 'AI bỏ qua câu này'));
    }
    return f;
  }

  /* ------------------------------------------------------------ nâng cao */
  function moNangCao(mo) {
    const moi = $('bt-moi'), cu = $('bt-cu');
    if (!moi || !cu) return;
    moi.hidden = mo; cu.hidden = !mo;
    document.body.className = mo ? 'bt-che-do-cu' : 'bt-che-do-moi';
    if (mo) { const t = $('tai-lai'); if (t) t.click(); }
    else { sua = null; chuSua = {}; lhDoi = false; fSua = null; fMo = -1; tai(); }
  }


  /* ------------------------------------------------------------ thẻ Bánh (v644)
     Anh Việt 07/11/2026: Very Berry hiện 4 ảnh giống nhau vì ảnh ghép từ hồ sơ
     món từng size và Pancake. Nay mỗi BÁNH (mọi size dùng chung) một bộ ảnh,
     một mô tả, một bảng tầng hương vị, sửa ở đây (máy chủ: banh_web.py). Bánh
     chỉ tới đây khi có người bấm Đưa lên web ở màn Danh mục sản phẩm; chưa có
     ảnh thì khách chưa thấy. Lưu là khách thấy ngay. */
  const CHO_ANH = 'Chờ ảnh', DANG_HIEN = 'Đang hiện', DA_AN = 'Đã ẩn';
  const TT_BANH = {'Chờ ảnh': 'sap', 'Đang hiện': 'dang', 'Đã ẩn': 'an'};
  let BB = null, bTai = false, banhChon = '', banhLoc = '', banhTim = '', bSua = null, bGoc = '', bBao = '';
  function banhDangChon() { return BB && BB.banh.find(x => x.khoa === banhChon) || null; }
  function banSua(x) { return x ? {anh: x.anh.map(a => ({url: a.url})), mo_ta: x.mo_ta || '', tang: x.tang || '', hien: x.trang_thai === DANG_HIEN} : null; }
  function moBanh(x) {
    banhChon = x ? x.khoa : ''; bBao = '';
    bSua = banSua(x);
    bGoc = bSua ? JSON.stringify(bSua) : '';
  }
  async function taiBanh() {
    if (bTai) return;
    bTai = true;
    try {
      BB = await api('ds_bien_tap', null, 'banh_web');
      const dang = banhDangChon() || BB.banh[0] || null;
      moBanh(dang);
    } catch (e) { bao(e.message, true); BB = {banh: [], dem: {}}; }
    finally { bTai = false; }
    if (the === 'banh') ve();
  }
  function chuSize(x) {
    const ds = (x.sizes || []).map(s => s.cm ? s.cm + ' cm' : 'một cỡ');
    return ds.length ? 'Size ' + ds.join(', ') : (x.ma_hang || []).join(', ');
  }
  function theBanh() {
    const g = tao('section', 'bt-banh'); g.setAttribute('aria-label', 'Bánh trên web');
    if (!BB) { g.append(tao('p', 'bt-rong', 'Đang tải danh sách bánh...')); taiBanh(); return g; }
    g.append(tao('p', 'bt-chu-phu', 'Mỗi bánh một bộ ảnh dùng chung cho mọi size. Giá, size, tồn lấy từ ERP. Bánh mới tới đây khi có người bấm Đưa lên web ở màn Danh mục sản phẩm trên app. Lưu là khách thấy ngay.'));
    const dem = BB.dem || {};
    const chips = tao('div', 'bt-chips');
    [['', 'Tất cả', BB.banh.length], [CHO_ANH, CHO_ANH, dem[CHO_ANH] || 0], [DANG_HIEN, DANG_HIEN, dem[DANG_HIEN] || 0], [DA_AN, DA_AN, dem[DA_AN] || 0]].forEach(([k, ten, so]) => {
      const b = tao('button', 'bt-chip' + (k === banhLoc ? ' dang' : ''), ten + ' · ' + so); b.type = 'button';
      b.dataset.locBanh = k || 'tat_ca'; b.setAttribute('aria-pressed', String(k === banhLoc));
      b.onclick = () => { banhLoc = k; ve(); };
      chips.append(b);
    });
    const dau = tao('div', 'bt-dau-ds');
    const tim = tao('input', 'bt-tim'); tim.type = 'search'; tim.placeholder = 'Tìm tên bánh hoặc mã'; tim.value = banhTim;
    tim.setAttribute('aria-label', 'Tìm bánh'); tim.setAttribute('name', 'tim_banh');
    dau.append(tim);
    const khung = tao('div', 'bt-banh-khung');
    const ds = tao('div', 'bt-banh-ds');
    function veDs() {
      ds.replaceChildren();
      const q = banhTim.trim().toLocaleLowerCase('vi');
      const loc = BB.banh.filter(x => (!banhLoc || x.trang_thai === banhLoc) && (!q || (x.ten + ' ' + (x.ma_hang || []).join(' ')).toLocaleLowerCase('vi').includes(q)));
      if (!BB.banh.length) { ds.append(tao('p', 'bt-rong', 'Chưa có bánh nào. Bấm Đưa lên web ở màn Danh mục sản phẩm trên app để thêm bánh.')); return; }
      if (!loc.length) { ds.append(tao('p', 'bt-rong', 'Không thấy bánh nào khớp.')); return; }
      loc.forEach(x => {
        const b = tao('button', 'bt-banh-mon' + (x.khoa === banhChon ? ' dang' : '')); b.type = 'button'; b.dataset.banh = x.khoa;
        b.setAttribute('aria-pressed', String(x.khoa === banhChon));
        if (x.anh.length) { const i = tao('img'); i.src = x.anh[0].url; i.alt = ''; b.append(i); }
        else b.append(tao('span', 'bt-banh-trong', '+'));
        const chu = tao('span', 'bt-banh-chu'); chu.append(tao('b', '', x.ten), tao('small', '', chuSize(x) + ' · ' + x.anh.length + ' ảnh'));
        b.append(chu, tao('span', 'bt-tt ' + (TT_BANH[x.trang_thai] || 'an'), x.trang_thai));
        /* Codex PR #547: đang lưu hay đang tải ảnh thì không cho đổi bánh, để
           phản hồi máy chủ luôn về đúng bản sửa đang mở (ba vòng rà cho thấy
           mọi cách đổi bánh giữa chừng đều làm lệch bản sửa với máy chủ). */
        b.onclick = async () => {
          if (x.khoa === banhChon) return;
          if (choXong()) return;
          if (!await roiDi()) return;
          moBanh(x); ve();
        };
        ds.append(b);
      });
    }
    tim.oninput = () => { banhTim = tim.value; veDs(); };
    veDs();
    khung.append(ds, chiTietBanh());
    g.append(chips, dau, khung);
    return g;
  }
  function chiTietBanh() {
    const g = tao('div', 'bt-banh-ct');
    const x = banhDangChon();
    if (!x || !bSua) { g.append(tao('p', 'bt-rong', 'Chọn một bánh để thêm ảnh và mô tả.')); return g; }
    g.append(tao('h3', 'bt-ten', x.ten), tao('p', 'bt-meta', chuSize(x) + ' · giá và tồn theo ERP'));
    const nhanAnh = tao('span', 'bt-nhan', 'Ảnh của bánh (tối đa 5, ảnh đầu là ảnh bìa)');
    const luoi = tao('div', 'bt-anh-luoi');
    function nut(chu, nhan, lam, an) {
      const b = tao('button', 'bt-nut nho', chu); b.type = 'button'; b.setAttribute('aria-label', nhan); b.title = nhan;
      if (an) b.hidden = true;
      b.onclick = () => { lam(); ve(); };
      return b;
    }
    bSua.anh.forEach((a, i) => {
      const o = tao('div', 'bt-anh-o'); o.dataset.anhI = String(i);
      const hinh = tao('div', 'bt-anh-hinh'); const im = tao('img'); im.src = a.url; im.alt = 'Ảnh ' + (i + 1) + ' của ' + x.ten; hinh.append(im);
      if (!i) hinh.append(tao('span', 'bt-anh-bia', 'Ảnh bìa'));
      const hang = tao('div', 'bt-anh-nut');
      hang.append(
        nut('◀', 'Đưa ảnh ' + (i + 1) + ' lên trước', () => { const t = bSua.anh.splice(i, 1)[0]; bSua.anh.splice(i - 1, 0, t); }, i === 0),
        nut('▶', 'Đưa ảnh ' + (i + 1) + ' ra sau', () => { const t = bSua.anh.splice(i, 1)[0]; bSua.anh.splice(i + 1, 0, t); }, i === bSua.anh.length - 1),
        nut('Làm bìa', 'Đặt ảnh ' + (i + 1) + ' làm ảnh bìa', () => { const t = bSua.anh.splice(i, 1)[0]; bSua.anh.unshift(t); }, i === 0),
        nut('✕', 'Bỏ ảnh ' + (i + 1), () => { bSua.anh.splice(i, 1); if (!bSua.anh.length) bSua.hien = false; }));
      o.append(hinh, hang);
      luoi.append(o);
    });
    if (bSua.anh.length < 5) {
      const l = tao('label', 'bt-anh-o bt-anh-them');
      const f = tao('input'); f.type = 'file'; f.accept = 'image/png,image/jpeg,image/webp'; f.multiple = true; f.setAttribute('name', 'anh_banh');
      f.onchange = () => taiAnhBanh(x.khoa, Array.prototype.slice.call(f.files || []));
      l.append(f, tao('b', '', '+'), tao('span', '', 'Tải ảnh'));
      luoi.append(l);
    }
    g.append(nhanAnh, luoi);
    if (bBao) { const c = tao('p', 'bt-canh-banh', bBao); c.setAttribute('role', 'status'); g.append(c); }
    const hai = tao('div', 'bt-hai-cot');
    hai.append(
      o('Mô tả', bSua.mo_ta, v => { bSua.mo_ta = v; }, {nhieuDong: true, dong: 5, ten: 'mo_ta_banh', chu: 'Vài câu khách đọc khi mở bánh.'}),
      o('Tầng hương vị', bSua.tang, v => { bSua.tang = v; }, {nhieuDong: true, dong: 5, ten: 'tang_banh', goi: 'Vỏ sô cô la đen - Dark chocolate shell', chu: 'Mỗi dòng một tầng: tên tầng - giải thích. Tối đa 12 dòng.'}));
    g.append(hai);
    const ct = congTac('Hiện trên web', bSua.hien, v => {
      if (v && !bSua.anh.length) { bSua.hien = false; bBao = 'Thêm ít nhất một ảnh trước khi bật Hiện trên web.'; ve(); return; }
      bSua.hien = v;
    }, v => (v ? 'Khách thấy bánh này khi có tồn hoặc nhận đặt' : (bSua.anh.length ? 'Khách không thấy bánh này. ERP và Pancake không đổi' : 'Thêm ảnh rồi bật, khách mới thấy')));
    ct.dataset.congTacBanh = '1';
    g.append(ct);
    const hang = tao('div', 'bt-hang-nut');
    const luu = tao('button', 'bt-nut chinh', 'Lưu bánh'); luu.type = 'button'; luu.dataset.luuBanh = '1';
    luu.onclick = () => luuBanh(x.khoa);
    const xem = tao('a', 'bt-nut', 'Xem như khách'); xem.href = '/banh'; xem.target = '_blank'; xem.rel = 'noopener';
    hang.append(luu, xem);
    g.append(hang);
    return g;
  }
  async function taiAnhBanh(khoaBanh, tep) {
    if (ban || !tep.length) return;
    /* Codex PR #547: ảnh vừa tải chỉ ghép vào bản sửa ĐANG MỞ của đúng bánh
       đã tải (theo khoá bánh, kể cả khi người dùng sang bánh khác rồi quay
       lại: bản sửa mới phải nhận ảnh, không thì Lưu bánh xoá ảnh đó). Đang mở
       bánh khác thì ảnh vẫn vào bánh đã tải (máy chủ đã lưu), không ghép. */
    const dangMo = () => (banhChon === khoaBanh ? bSua : null);
    for (const f of tep) {
      const d0 = dangMo();
      if (d0 && d0.anh.length >= 5) { bBao = 'Mỗi bánh tối đa 5 ảnh. Bỏ bớt một ảnh rồi tải tiếp.'; break; }
      khoa(true); bao('Đang tải ảnh...');
      try {
        const u = await taiAnhLen(f);
        const r = await api('them_anh', {khoa: khoaBanh, url: u}, 'banh_web');
        BB = r;
        if (!dangMo()) {
          const t = (BB.banh.find(x => x.khoa === khoaBanh) || {}).ten || '';
          bao(r.trung ? 'Ảnh vừa tải giống một ảnh đã có của bánh ' + t + '.' : 'Đã thêm ảnh vào bánh ' + t + '.');
          continue;
        }
        /* Codex PR #547: chỉ ghép ĐÚNG ảnh vừa tải. Máy chủ trả cả bộ đã lưu,
           trong đó còn ảnh người dùng vừa bỏ ở bản đang sửa; ghép cả bộ là kéo
           ảnh đã bỏ trở lại. */
        if (r.trung) {
          if (bSua.anh.some(b => b.url === r.trung)) bBao = 'Ảnh vừa tải giống một ảnh đã có của bánh này, máy không thêm lần nữa.';
          else { bSua.anh.push({url: r.trung}); bBao = 'Ảnh vừa tải giống một ảnh đã có sẵn của bánh này, máy đưa ảnh đó trở lại. Bấm Lưu bánh để giữ.'; }
        } else {
          bBao = '';
          const uMoi = r.them || u;
          if (!bSua.anh.some(b => b.url === uMoi)) {
            bSua.anh.push({url: uMoi});
            const g0 = JSON.parse(bGoc); g0.anh.push({url: uMoi}); bGoc = JSON.stringify(g0);
          }
        }
        bao(r.trung ? '' : 'Đã thêm ảnh. Bấm Lưu bánh nếu vừa đổi thứ tự, mô tả hay bật hiện.');
      } catch (e) { bao(e.message, true); break; }
      finally { khoa(false); }
    }
    ve();
  }
  async function luuBanh(khoaBanh) {
    if (ban || !bSua) return;
    if (bSua.hien && !bSua.anh.length) { bBao = 'Thêm ít nhất một ảnh trước khi bật Hiện trên web.'; ve(); return; }
    khoa(true); bao('Đang lưu...');
    /* Codex PR #547: người dùng gõ tiếp trong lúc chờ thì giữ chữ mới, chỉ dời
       mốc "đã lưu" sang bản máy chủ vừa nhận; không thay cả bản sửa. */
    const sua = bSua, gui = JSON.stringify(bSua);
    try {
      BB = await api('luu', {khoa: khoaBanh, anh: sua.anh, mo_ta: sua.mo_ta, tang: sua.tang, trang_thai: sua.hien ? DANG_HIEN : DA_AN}, 'banh_web');
      if (B) B.banh_cho_anh = (BB.dem || {})[CHO_ANH] || 0;
      const x = BB.banh.find(y => y.khoa === khoaBanh) || null;
      const hien = x && x.trang_thai === DANG_HIEN;
      if (banhChon !== khoaBanh || bSua !== sua) bao('Đã lưu bánh ' + ((x && x.ten) || '') + '.');
      else if (JSON.stringify(bSua) !== gui) {
        bGoc = JSON.stringify(banSua(x));
        bao('Đã lưu bản lúc bấm Lưu. Còn thay đổi gõ trong lúc lưu, bấm Lưu bánh lần nữa.');
      } else {
        moBanh(x);
        bao(hien ? 'Đã lưu. Khách thấy ngay.' : 'Đã lưu. Bánh đang ẩn với khách.');
      }
    } catch (e) { bao(e.message, true); }
    finally { khoa(false); }
    ve();
  }
  function batDau() {
    const ve2 = $('bt-ve-moi'); if (ve2) ve2.onclick = () => moNangCao(false);
    if (window.addEventListener) window.addEventListener('beforeunload', e => { if (dangDoi()) { e.preventDefault(); e.returnValue = ''; } });
    tai();
  }
  /* v630: bảng Nâng cao mở thẳng một thẻ (khối Tuyển dụng cũ chỉ đường sang thẻ Tuyển dụng). */
  function moThe(k) { if (THE.some(x => x.k === k)) the = k; moNangCao(false); }
  window.VgbBienTapMoi = {trangThai: trangThai, moTa: moTa, batDau: batDau, moThe: moThe, loiTacPham: loiTacPham, loiBanner: loiBanner};
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', batDau);
  else if ($('bt-moi')) batDau();
}());
