/* v630: trang Bánh sỉ (/banh-si) bản Vue, mẫu m2 anh Việt duyệt 02/11/2026.

   Ba màn: (1) trang hợp tác công khai, KHÔNG hiện giá, form đăng ký; (2) đặt
   hàng sỉ sau khi đăng nhập mã Zalo: ngày giao, bảng giá riêng, đặt lại như
   đơn trước; (3) tài khoản: công nợ và QR gộp, đơn sắp giao, lịch sử.
   Mọi chữ qua t(khoá, mặc định) trong sổ nhãn; không v-html. */
import {createApp, h} from '../lib/vue.esm-browser.prod.js';
import {t, napNoiDung, telSo, telChu} from '../kho/chu.js';
import {LOGO} from '../banh/anh.js';
import {SI, LOAI_HINH, LUONG, khoiDong as khoiDongKho, dsNgay, dm, thu, tienVN, tamTinh, chonNgay, datSl, cong,
  datLai, guiDon, moQrNo, moQrDon, donChoChuyen, guiDangKy, guiMa, xacThuc, thoat, sangMan} from './kho-si.js';

const anToan = u => typeof u === 'string' && !/[\s\\]/.test(u) && !u.startsWith('/private/') && ((u[0] === '/' && u[1] !== '/') || /^https:\/\/[^/@]+(?:\/|$)/.test(u));
const nut = (lop, chu, bam, them) => h('button', Object.assign({class: lop, type: 'button', onClick: bam}, them || {}), chu);
const chip = (on, chu, bam, them) => h('button', Object.assign({type: 'button', class: 'si-chip' + (on ? ' on' : ''), 'aria-pressed': String(!!on), onClick: bam}, them || {}), chu);
const nhanO = (nhan, o) => h('label', {class: 'si-o'}, [h('small', null, nhan), o]);

function dauTrang() {
  const toi = SI.toi;
  return h('header', null, [h('div', {class: 'hd wrap si-hd'}, [
    h('a', {class: 'logo-anh', href: '/banh'}, [h('img', {src: LOGO, alt: t('dat_banh_913466c0d', 'The Vagabond Pâtisserie'), width: 63, height: 26})]),
    toi ? h('nav', {class: 'si-nav'}, [
      nut(SI.man === 'dat' ? 'on' : '', t('bsi_tab_dat', 'Đặt hàng'), () => sangMan('dat'), {'data-si-tab': 'dat'}),
      nut(SI.man === 'tai_khoan' ? 'on' : '', t('bsi_tab_tk', 'Tài khoản'), () => sangMan('tai_khoan'), {'data-si-tab': 'tai_khoan'})])
      : nut('si-dn-nut', t('bsi_dang_nhap', 'Đăng nhập sỉ'), () => { SI.dn.mo = true; SI.dn.loi = ''; }, {'data-si-mo-dn': '1'})
  ])]);
}

/* ---------------- (1) trang ngoài ---------------- */
function veDangNhap() {
  const d = SI.dn;
  if (!d.mo) return null;
  if (!SI.otp) return h('section', {class: 'si-the', id: 'siDangNhap'}, [h('p', null, t('bsi_dn_tat', 'Đăng nhập bằng Zalo đang tạm tắt. Gọi Sales để đặt hàng.'))]);
  return h('section', {class: 'si-the', id: 'siDangNhap'}, [
    h('p', {class: 'si-lbl'}, t('bsi_dn_tieu_de', 'Đăng nhập khách sỉ')),
    d.buoc === 'sdt'
      ? h('form', {onSubmit: e => { e.preventDefault(); guiMa(); }}, [
        nhanO(t('bsi_dn_sdt', 'Số Zalo đã đăng ký'), h('input', {type: 'tel', inputmode: 'tel', autocomplete: 'tel', name: 'si_dn_sdt', value: d.sdt,
          onInput: e => { d.sdt = e.target.value; d.loi = ''; }})),
        h('button', {class: 'si-btn', type: 'submit', disabled: d.gui, 'data-si-gui-ma': '1'}, d.gui ? t('bsi_dang_gui', 'Đang gửi...') : t('bsi_dn_gui_ma', 'Gửi mã qua Zalo'))])
      : h('form', {onSubmit: e => { e.preventDefault(); xacThuc(); }}, [
        nhanO(t('bsi_dn_ma', 'Mã xác thực 6 số'), h('input', {inputmode: 'numeric', autocomplete: 'one-time-code', maxlength: 6, name: 'si_dn_ma', value: d.ma,
          onInput: e => { d.ma = e.target.value; d.loi = ''; }})),
        h('button', {class: 'si-btn', type: 'submit', disabled: d.gui, 'data-si-xac-thuc': '1'}, d.gui ? t('bsi_dang_gui', 'Đang gửi...') : t('bsi_dn_xac_nhan', 'Xác nhận')),
        nut('si-btn2', t('bsi_dn_doi_so', 'Đổi số khác'), () => { d.buoc = 'sdt'; d.ma = ''; d.loi = ''; })]),
    d.loi ? h('p', {class: 'si-loi', role: 'alert', 'data-si-loi-dn': '1'}, d.loi) : null,
    h('p', {class: 'si-note'}, t('bsi_dn_chu', 'Chỉ số đã được Sales mở đặt sỉ mới nhận mã. Không cần mật khẩu.'))]);
}

function veDangKy() {
  const d = SI.dk;
  if (d.xong) return h('section', {class: 'si-the si-xong', id: 'siDangKyXong', role: 'status'}, [
    h('p', {class: 'si-lbl'}, t('bsi_dk_da_nhan', 'Đã nhận đăng ký')),
    h('p', null, t('bsi_dk_cam_on', 'Cảm ơn {ten}. Sales gọi lại trong một ngày làm việc để gửi bảng giá và mở tài khoản.', {ten: d.ten_quan.trim()}))]);
  const o = (k, nhan, them) => nhanO(nhan, h('input', Object.assign({value: d[k], name: 'si_dk_' + k, onInput: e => { d[k] = e.target.value; d.loi = ''; }}, them)));
  return h('form', {class: 'si-the', id: 'siDangKy', onSubmit: e => { e.preventDefault(); guiDangKy(); }}, [
    h('p', {class: 'si-lbl'}, t('bsi_dk_tieu_de', 'Đăng ký hợp tác')),
    o('ten_quan', t('bsi_dk_ten', 'Tên quán hoặc công ty'), {maxlength: 140, autocomplete: 'organization', placeholder: t('bsi_dk_ten_vd', 'Ví dụ: Café Lá Me')}),
    o('mst', t('bsi_dk_mst', 'Mã số thuế (để xuất hoá đơn VAT, không bắt buộc)'), {inputmode: 'numeric', maxlength: 16}),
    o('sdt', t('bsi_dk_sdt', 'Số điện thoại Zalo (dùng để đăng nhập sau này)'), {type: 'tel', inputmode: 'tel', autocomplete: 'tel'}),
    h('p', {class: 'si-lbl'}, t('bsi_dk_loai', 'Loại hình')),
    h('div', {class: 'si-chips', role: 'radiogroup'}, LOAI_HINH.map(([k, kk, md]) => chip(d.loai_hinh === k, t(kk, md), () => { d.loai_hinh = k; d.loi = ''; }, {'data-si-loai': k}))),
    h('p', {class: 'si-lbl'}, t('bsi_dk_luong', 'Dự kiến mỗi tuần')),
    h('div', {class: 'si-chips', role: 'radiogroup'}, LUONG.map(([k, kk, md]) => chip(d.luong === k, t(kk, md), () => { d.luong = k; d.loi = ''; }, {'data-si-luong': k}))),
    nhanO(t('bsi_dk_ghi_chu', 'Ghi chú (không bắt buộc)'), h('textarea', {rows: 2, maxlength: 500, name: 'si_dk_ghi_chu', value: d.ghi_chu, onInput: e => { d.ghi_chu = e.target.value; }})),
    h('button', {class: 'si-btn', type: 'submit', disabled: d.gui, 'data-si-gui-dk': '1'}, d.gui ? t('bsi_dang_gui', 'Đang gửi...') : t('bsi_dk_gui', 'Gửi đăng ký')),
    d.loi ? h('p', {class: 'si-loi', role: 'alert', 'data-si-loi-dk': '1'}, d.loi) : null,
    h('p', {class: 'si-note'}, t('bsi_dk_note', 'Sales gọi lại trong một ngày làm việc, gửi bảng giá và mở tài khoản.'))]);
}

function veNgoai() {
  return h('main', {class: 'wrap si-main', id: 'siNgoai'}, [
    h('div', {class: 'meta'}, [h('span', null, t('bsi_meta_trai', 'Hợp tác')), h('span', null, t('bsi_meta_phai', 'Bánh sỉ'))]),
    h('h1', {class: 'h1 si-h1'}, [t('bsi_tieu_de', 'Bánh cho quán của bạn'), h('em', null, t('bsi_tieu_de_phu', 'Quán cà phê, khách sạn, nhà hàng'))]),
    veDangNhap(),
    h('p', {class: 'si-lbl'}, t('bsi_vi_sao', 'Vì sao chọn Vagabond')),
    h('ul', {class: 'si-li'}, [
      h('li', null, t('bsi_ly_do_1', 'Bảng giá riêng cho từng quán, Sales gửi sau khi gọi lại')),
      h('li', null, t('bsi_ly_do_2', 'Đặt trên web, giao từ ngày thứ ba kể từ ngày đặt')),
      h('li', null, t('bsi_ly_do_3', 'Xuất hoá đơn VAT theo mã số thuế')),
      h('li', null, t('bsi_ly_do_4', 'Thanh toán cuối kỳ cho đối tác lâu năm'))]),
    veDangKy(),
    h('p', {class: 'si-note'}, t('bsi_goi', 'Cần hỏi thêm, gọi {so}.', {so: telChu()}))]);
}

/* ---------------- (2) đặt hàng ---------------- */
function veDat() {
  const toi = SI.toi, mon = toi.mon || [], tt = tamTinh(), ngay = dsNgay(toi.ngay_som);
  if (!mon.length) return h('main', {class: 'wrap si-main', id: 'siDat'}, [
    h('h1', {class: 'h1 si-h1'}, [toi.ten, h('em', null, t('bsi_khach_si', 'Khách sỉ'))]),
    h('p', {class: 'si-the', 'data-si-rong': '1'}, t('bsi_chua_gia', 'Sales chưa mở giá món nào cho quý khách. Gọi {so} để Sales gửi bảng giá.', {so: telChu()}))]);
  const dt = toi.don_truoc, choCk = donChoChuyen();
  return h('main', {class: 'wrap si-main', id: 'siDat'}, [
    h('h1', {class: 'h1 si-h1 si-h1-nho'}, [toi.ten, h('em', null, toi.cuoi_ky ? t('bsi_cuoi_ky', 'Khách sỉ, trả cuối kỳ {so} ngày', {so: toi.ky_no}) : t('bsi_tra_truoc', 'Khách sỉ, chuyển khoản trước khi giao'))]),
    choCk.length ? h('p', {class: 'si-note si-bao', role: 'status', 'data-si-nhac-cho-tt': '1'}, [
      choCk.length > 1 ? t('bsi_nhac_cho_ck_n', '{so} đơn đang chờ chuyển khoản.', {so: choCk.length}) : t('bsi_nhac_cho_ck', 'Đơn {ma} đang chờ chuyển khoản.', {ma: choCk[0].ma}),
      ' ', h('a', {href: '#', onClick: e => { e.preventDefault(); sangMan('tai_khoan'); }}, t('bsi_xem_ma_qr', 'Xem mã QR'))]) : null,
    h('p', {class: 'si-lbl'}, t('bsi_ngay_giao', 'Ngày giao')),
    h('div', {class: 'si-chips', role: 'radiogroup'}, ngay.map(n => chip(SI.ngay === n, thu(n) + ' ' + dm(n), () => chonNgay(n), {'data-si-ngay': n}))),
    h('label', {class: 'si-o si-o-ngay'}, [h('small', null, t('bsi_ngay_khac', 'Ngày khác')), h('input', {type: 'date', min: toi.ngay_som, value: SI.ngay, name: 'si_ngay',
      onInput: e => chonNgay(e.target.value)})]),
    h('p', {class: 'si-note'}, t('bsi_ngay_note', 'Giao sớm nhất sau {so} ngày kể từ ngày đặt.', {so: toi.so_ngay})),
    dt && (dt.dong || []).length ? nut('si-btn2', t('bsi_dat_lai', 'Đặt lại như đơn {ngay}', {ngay: dm(dt.ngay)}), datLai, {'data-si-dat-lai': '1'}) : null,
    SI.bao ? h('p', {class: 'si-note si-bao', role: 'status'}, SI.bao) : null,
    h('table', {class: 'si-tbl'}, [h('tbody', null, mon.map(m => h('tr', {'data-si-mon': m.ma}, [
      h('td', {class: 'si-anh'}, anToan(m.anh) ? [h('img', {src: m.anh, alt: '', loading: 'lazy'})] : [h('span', null, '🥐')]),
      h('td', {class: 'n'}, [m.ten, h('small', null, (m.dvt ? m.dvt + ' · ' : '') + tienVN(m.gia))]),
      h('td', {class: 'q'}, [h('span', {class: 'si-qty'}, [
        nut('', '−', () => cong(m.ma, -1), {'aria-label': t('bsi_bot', 'Bớt một'), 'data-si-tru': m.ma, disabled: !(SI.sl[m.ma] > 0)}),
        h('input', {inputmode: 'numeric', 'aria-label': t('bsi_so_luong', 'Số lượng'), value: String(SI.sl[m.ma] || 0), 'data-si-sl': m.ma,
          onInput: e => datSl(m.ma, e.target.value)}),
        nut('', '+', () => cong(m.ma, 1), {'aria-label': t('bsi_them', 'Thêm một'), 'data-si-cong': m.ma})])])])))]),
    nhanO(t('bsi_ghi_chu', 'Ghi chú cho đơn (không bắt buộc)'), h('textarea', {rows: 2, maxlength: 500, name: 'si_ghi_chu', value: SI.ghiChu, onInput: e => { SI.ghiChu = e.target.value; }})),
    h('div', {class: 'si-sum', 'data-si-tong': '1'}, [
      h('div', null, [h('span', null, t('bsi_so_cai', '{so} cái, {mon} món', {so: tt.so_cai, mon: tt.so_mon})), h('span', null, tienVN(tt.tong))]),
      h('div', null, [h('span', null, t('bsi_giao', 'Giao theo ngày đã chọn')), h('span', null, SI.ngay ? thu(SI.ngay) + ' ' + dm(SI.ngay) : '')]),
      h('div', {class: 't'}, [h('span', null, t('bsi_tong_tam', 'Tạm tính (đã gồm VAT)')), h('b', {'data-si-tam': '1'}, tienVN(tt.tong))]),
      h('div', null, [h('span', null, t('bsi_thanh_toan', 'Thanh toán')), h('span', null, toi.cuoi_ky ? t('bsi_tt_cuoi_ky', 'Cuối kỳ ({so} ngày)', {so: toi.ky_no}) : t('bsi_tt_truoc', 'Chuyển khoản qua QR sau khi đặt'))])]),
    h('button', {class: 'si-btn', type: 'button', disabled: SI.dangGui, 'data-si-gui': '1', onClick: guiDon},
      SI.dangGui ? t('bsi_dang_gui', 'Đang gửi...') : t('bsi_dat_don', 'Đặt đơn giao {ngay}', {ngay: SI.ngay ? thu(SI.ngay) + ' ' + dm(SI.ngay) : ''})),
    SI.loi ? h('p', {class: 'si-loi', role: 'alert', 'data-si-loi': '1'}, SI.loi) : null,
    h('p', {class: 'si-note'}, t('bsi_vat_note', 'Giá đã gồm VAT. Hoá đơn VAT tách thuế theo từng món, xuất theo mã số thuế của quán.'))]);
}

function veQr(q, nhan) {
  return h('div', {class: 'si-qr'}, [
    q.anh ? h('img', {src: q.anh, alt: nhan, width: 220, height: 220}) : h('p', {class: 'si-loi'}, t('bsi_qr_khong_ve', 'Không vẽ được mã QR. Chuyển tay theo thông tin bên dưới.')),
    h('dl', {class: 'si-ck'}, [
      h('dt', null, t('bsi_so_tien', 'Số tiền')), h('dd', {'data-si-qr-tien': '1'}, tienVN(q.so_tien)),
      h('dt', null, t('bsi_noi_dung', 'Nội dung chuyển khoản')), h('dd', {'data-si-qr-nd': '1'}, q.noi_dung),
      h('dt', null, t('bsi_ngan_hang', 'Ngân hàng')), h('dd', null, q.ngan_hang),
      h('dt', null, t('bsi_so_tk', 'Số tài khoản')), h('dd', null, q.stk),
      h('dt', null, t('bsi_ten_tk', 'Tên tài khoản')), h('dd', null, q.ten_tk)])]);
}

function veXong() {
  const k = SI.kq, cho = SI.trangThai === 'cho_tt';
  return h('main', {class: 'wrap si-main', id: 'siXong'}, [
    h('div', {class: 'meta'}, [h('span', null, t('bsi_ma_don', 'Mã đơn {ma}', {ma: k.ma})), h('span', null, t('bsi_giao_ngay', 'Giao {ngay}', {ngay: dm(k.ngay)}))]),
    h('p', {class: 'si-tt ' + (cho ? 'cho' : 'ok'), role: 'status', 'data-si-tt': SI.trangThai},
      cho ? t('bsi_cho_tt', 'Đơn đã nhận. Chuyển khoản theo mã QR để giữ đơn, trang tự cập nhật khi tiền về.')
        : (k.tra_truoc ? t('bsi_da_tt', 'Đã nhận tiền. Sales xác nhận ngày giao với quý khách.') : t('bsi_da_nhan_no', 'Đơn đã nhận, thanh toán cuối kỳ. Sales xác nhận ngày giao với quý khách.'))),
    cho && k.qr ? veQr(k.qr, t('bsi_qr_alt', 'Mã QR chuyển khoản đơn sỉ')) : null,
    h('div', {class: 'si-sum'}, [
      ...(k.dong || []).map(d => h('div', null, [h('span', null, d.ten + ' x ' + d.sl), h('span', null, tienVN(d.tien))])),
      h('div', null, [h('span', null, t('bsi_chua_vat', 'Tiền hàng chưa VAT')), h('span', null, tienVN(k.chua_vat))]),
      h('div', null, [h('span', null, t('bsi_vat', 'VAT')), h('span', {'data-si-vat': '1'}, tienVN(k.vat))]),
      h('div', {class: 't'}, [h('span', null, t('bsi_tong_don', 'Tổng đơn (đã gồm VAT)')), h('b', {'data-si-kq-tong': '1'}, tienVN(k.tong))])]),
    nut('si-btn2', t('bsi_ve_dat', 'Đặt đơn khác'), () => sangMan('dat'), {'data-si-ve-dat': '1'}),
    nut('si-btn2', t('bsi_xem_tk', 'Xem tài khoản'), () => sangMan('tai_khoan'))]);
}

/* ---------------- (3) tài khoản ---------------- */
/* Codex #531 f4: đơn trả trước chưa chuyển tiền, mỗi đơn một nút mở lại QR. */
function dongChoChuyen(d) {
  return h('tr', {'data-si-cho-tt': d.ma}, [h('td', {class: 'n'}, [thu(d.ngay) + ' ' + dm(d.ngay) + ' · ' + d.ma,
    h('small', null, t('bsi_dong_cho_ck', '{so} cái, cần chuyển {tien}', {so: d.so_cai, tien: tienVN(d.con_lai)}))]),
  h('td', {class: 'p'}, [h('button', {class: 'si-btn2', type: 'button', disabled: !!SI.dangQrDon, 'data-si-qr-don': d.ma,
    onClick: () => moQrDon(d.ma)}, SI.dangQrDon === d.ma ? t('bsi_dang_tao', 'Đang tạo mã...') : t('bsi_tt_qr', 'Thanh toán qua QR'))])]);
}
function dongDon(d) {
  return h('tr', {'data-si-don': d.ma}, [h('td', {class: 'n'}, [thu(d.ngay) + ' ' + dm(d.ngay) + ' · ' + d.ma,
    h('small', null, t('bsi_dong_don', '{so} cái, {tt}', {so: d.so_cai, tt: d.nhan}))]), h('td', {class: 'p'}, tienVN(d.tong))]);
}
function veTaiKhoan() {
  const toi = SI.toi, no = toi.no;
  const khoiNo = toi.cuoi_ky && no ? [
    h('div', {class: 'meta'}, [h('span', null, t('bsi_cong_no', 'Công nợ')), h('span', null, t('bsi_ky', 'Kỳ {so} ngày', {so: toi.ky_no}))]),
    h('div', {class: 'h1 si-h1 si-so', 'data-si-no': '1'}, [tienVN(no.tong),
      h('em', null, no.tong > 0 ? (no.han_gan ? t('bsi_han_gan', 'Còn phải trả, hạn gần nhất {ngay}', {ngay: dm(no.han_gan)}) : t('bsi_con_tra', 'Còn phải trả')) : t('bsi_het_no', 'Không còn hoá đơn chưa trả'))]),
    no.so_qua_han ? h('p', {class: 'si-loi'}, t('bsi_qua_han', '{so} hoá đơn đã quá hạn.', {so: no.so_qua_han})) : null,
    no.tong > 0 ? h('button', {class: 'si-btn', type: 'button', disabled: SI.dangQr, 'data-si-qr-no': '1', onClick: moQrNo},
      SI.dangQr ? t('bsi_dang_tao', 'Đang tạo mã...') : t('bsi_tt_qr', 'Thanh toán qua QR')) : null,
    SI.loiQr ? h('p', {class: 'si-loi', role: 'alert'}, SI.loiQr) : null,
    ...(SI.qrNo || []).map(p => h('div', {class: 'si-the', 'data-si-phieu': p.ma_phieu}, [
      h('p', {class: 'si-note'}, t('bsi_phieu_no', 'Phiếu {ma}: {so} hoá đơn, còn {tien}', {ma: p.ma_phieu, so: (p.hoa_don || []).length, tien: tienVN(p.con_thieu)})),
      veQr(p.qr || {}, t('bsi_qr_no_alt', 'Mã QR thanh toán công nợ'))])),
    (no.dong || []).length ? h('p', {class: 'si-lbl'}, t('bsi_hd_chua_tra', 'Hoá đơn chưa trả')) : null,
    (no.dong || []).length ? h('table', {class: 'si-tbl'}, [h('tbody', null, no.dong.slice(0, 30).map(d => h('tr', {'data-si-hd': d.hoa_don}, [
      h('td', {class: 'n'}, [d.hoa_don, h('small', {class: d.han && d.han < toi.hom_nay ? 'amber' : ''}, d.han ? t('bsi_han', 'Hạn {ngay}', {ngay: dm(d.han)}) : '')]),
      h('td', {class: 'p'}, d.phieu ? t('bsi_trong_phieu', 'trong phiếu {ma}', {ma: d.phieu}) : tienVN(d.tien))])))]) : null,
    /* Codex #531 v8: bảng chỉ vẽ 30 dòng, tổng và QR tính đủ: nói rõ phần không hiện. */
    (no.dong || []).length > 30 ? h('p', {class: 'si-note', 'data-si-hd-con': '1'}, t('bsi_hd_con', 'Còn {so} hoá đơn nữa không hiện ở đây, đã tính trong tổng và mã QR.', {so: no.dong.length - 30})) : null] : [];
  const choCk = donChoChuyen();
  return h('main', {class: 'wrap si-main', id: 'siTaiKhoan'}, [
    h('h1', {class: 'h1 si-h1 si-h1-nho'}, [toi.ten, h('em', null, t('bsi_tai_khoan', 'Tài khoản khách sỉ'))]),
    choCk.length ? h('p', {class: 'si-lbl'}, t('bsi_cho_ck', 'Đơn chờ chuyển khoản')) : null,
    choCk.length ? h('table', {class: 'si-tbl'}, [h('tbody', null, choCk.map(dongChoChuyen))]) : null,
    SI.loiQrDon ? h('p', {class: 'si-loi', role: 'alert', 'data-si-loi-qr-don': '1'}, SI.loiQrDon) : null,
    ...khoiNo,
    h('p', {class: 'si-lbl'}, t('bsi_sap_giao', 'Đơn sắp giao')),
    (toi.sap_giao || []).length ? h('table', {class: 'si-tbl'}, [h('tbody', null, toi.sap_giao.map(dongDon))]) : h('p', {class: 'si-note'}, t('bsi_chua_don', 'Chưa có đơn nào sắp giao.')),
    h('p', {class: 'si-lbl'}, t('bsi_lich_su', 'Lịch sử đơn')),
    (toi.lich_su || []).length ? h('table', {class: 'si-tbl'}, [h('tbody', null, toi.lich_su.map(dongDon))]) : h('p', {class: 'si-note'}, t('bsi_chua_lich_su', 'Chưa có đơn đã giao.')),
    nut('si-btn2', t('bsi_thoat', 'Đăng xuất'), thoat, {'data-si-thoat': '1'}),
    h('p', {class: 'si-note'}, t('bsi_hd_note', 'Hoá đơn VAT gửi qua email kế toán của quán. Cần bản in, gọi {so}.', {so: telChu()}))]);
}

export const TrangSi = {
  name: 'TrangSi',
  render() {
    let than;
    if (SI.man === 'cho') than = h('main', {class: 'wrap si-main'}, [h('p', {class: 'si-note', role: 'status'}, t('bsi_dang_tai', 'Đang tải...'))]);
    else if (SI.man === 'xong' && SI.kq) than = veXong();
    else if (SI.toi && SI.man === 'tai_khoan') than = veTaiKhoan();
    else if (SI.toi) than = veDat();
    else than = veNgoai();
    return h('div', {class: 'si'}, [dauTrang(), than,
      h('footer', {class: 'wrap si-chan'}, [h('a', {href: '/banh'}, t('bsi_ve_banh', 'Về trang đặt bánh')), ' · ', h('a', {href: 'tel:' + telSo()}, telChu())])]);
  }
};

export function khoiDong(goc = '#app') {
  try { document.title = t('bsi_title', 'Bánh sỉ cho quán - The Vagabond Pâtisserie'); } catch (e) { /* không có DOM */ }
  napNoiDung(window);
  khoiDongKho();
  return createApp(TrangSi).mount(goc);
}
