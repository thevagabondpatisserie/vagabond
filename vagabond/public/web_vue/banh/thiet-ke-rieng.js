/* v630: tab "Thiết kế riêng" của trang đặt bánh bản Vue (anh Việt duyệt mẫu
   m1 ngày 02/11/2026). Tác phẩm (Croquembouche...) do Marketing khai ở trình
   biên tập web, khối loai = thiet_ke_rieng, đọc từ ND.khoi như Tiệc.

   Ba bước: danh sách tác phẩm, trang một tác phẩm (size, bánh gồm gì, thời
   gian), đặt cọc (ngày, trang trí, ghi chú, ảnh tham khảo, nơi nhận) rồi QR
   cọc 50%. Số trên phần tóm tắt trước khi gửi là bản HIỆN tạm (kho/thuan.js
   tkrTinh, cùng luật với máy chủ); sau khi gửi mọi con số đọc từ máy chủ
   (thiet_ke_rieng.dat), không tính lại ở đây.

   Không v-html: chữ của Marketing và của khách luôn là chữ. */
import {h, reactive} from '../lib/vue.esm-browser.prod.js';
import {ND, t, telSo} from '../kho/chu.js';
import {ghi as ghiApi} from '../kho/api.js';
import {tienVN, tkrTinh, tkrNgaySomNhat, tkrSoNgay, tkrTuGia, tkrBatTrangTri} from '../kho/thuan.js';

export const LOAI_TKR = 'thiet_ke_rieng';
const PHUT_HOI = 8000, LAN_HOI_TOI_DA = 90;

function homNayVN() { return new Intl.DateTimeFormat('en-CA', {timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit'}).format(new Date()); }
function uuid() {
  try { if (window.crypto && crypto.randomUUID) return crypto.randomUUID(); } catch (e) { /* trình duyệt cũ */ }
  return 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g, () => (Math.random() * 16 | 0).toString(16));
}
async function taiTepThat(phuong, tep) {
  const f = new FormData(); f.append('tep', tep);
  const m = document.querySelector('meta[name="csrf-token"]');
  const v = m && m.getAttribute('content');
  const r = await fetch('/api/method/' + phuong, {method: 'POST', credentials: 'same-origin',
    headers: v && v !== 'None' && !/\{\{/.test(v) ? {'X-Frappe-CSRF-Token': v} : {}, body: f});
  let d = {};
  try { d = await r.json(); } catch (e) { /* không phải JSON */ }
  if (!r.ok || !d.message) {
    let chu = t('tkr_anh_loi', 'Chưa gửi được ảnh. Chọn ảnh JPG, PNG hoặc WebP dưới 8 MB.');
    try { const tb = JSON.parse(d._server_messages || '[]').map(x => JSON.parse(x).message); if (tb.length) chu = tb.join(' '); } catch (e) { /* giữ câu chung */ }
    throw new Error(chu);
  }
  return d.message;
}

/* Môi trường: ca kiểm thay mạng, đồng hồ và hẹn giờ. */
const MT = {ghi: ghiApi, taiTep: taiTepThat, hen: (f, ms) => setTimeout(f, ms), huyHen: id => clearTimeout(id), homNay: homNayVN, uuid};
export function datMoiTruong(m) { Object.assign(MT, m || {}); }

export const TKR = reactive({
  id: '', buoc: 'xem', kc: '', tt: [], ngay: '', gio: '', ghiChu: '', diem: '', ten: '', sdt: '',
  maAnh: '', tenAnh: '', dangTaiAnh: false, loi: '', dangGui: false, kq: null, trangThai: '', nhanTT: '',
  tv: {mo: false, ten: '', sdt: '', gui: false, xong: false, loi: ''}, maLan: '', lanHoi: 0, henHoi: null
});

/* ---------------- dữ liệu ---------------- */
export function dsTacPham() {
  return (ND.khoi || []).filter(k => k.loai === LOAI_TKR && (k.hien || ND.xemThu) && (k.kich_co || []).length);
}
export function tacPhamDangMo() { return dsTacPham().find(k => k.id === TKR.id) || null; }
export function diemNhan() { return Array.isArray(ND.diem_nhan) ? ND.diem_nhan.filter(d => d && d.id) : []; }

/* Mở một tác phẩm: chọn sẵn size đầu và trang trí đầu mỗi nhóm (Hoa lan
   trắng là trang trí đã gồm trong giá). Đổi tác phẩm là bỏ đơn đang soạn. */
export function moTacPham(id) {
  if (TKR.id === id && TKR.kc) return;
  dungHoi();
  const tp = (ND.khoi || []).find(k => k.loai === LOAI_TKR && k.id === id) || null;
  Object.assign(TKR, {id, buoc: 'xem', kc: tp && tp.kich_co && tp.kich_co.length ? tp.kich_co[Math.min(1, tp.kich_co.length - 1)].ten : '',
    tt: [], ngay: '', gio: '', ghiChu: '', maAnh: '', tenAnh: '', loi: '', dangGui: false, kq: null, trangThai: '', nhanTT: '', maLan: ''});
  TKR.tv = {mo: false, ten: '', sdt: '', gui: false, xong: false, loi: ''};
  const daNhom = new Set();
  ((tp && tp.trang_tri) || []).forEach(x => { if (x.nhom && !daNhom.has(x.nhom)) { daNhom.add(x.nhom); TKR.tt.push(x.ten); } });
  const dn = diemNhan(); if (dn.length === 1) TKR.diem = dn[0].id;
}
export function veDanhSach() { dungHoi(); TKR.id = ''; TKR.buoc = 'xem'; }
export function chonKichCo(ten) { TKR.kc = ten; TKR.loi = ''; }
export function batTrangTri(ten) { TKR.tt = tkrBatTrangTri(tacPhamDangMo(), TKR.tt, ten); TKR.loi = ''; }
export function tamTinh() { return tkrTinh(tacPhamDangMo(), TKR.kc, TKR.tt); }
export function ngaySom() { return tkrNgaySomNhat(MT.homNay(), tacPhamDangMo()); }
export function sangDat() {
  if (!TKR.ngay || TKR.ngay < ngaySom()) TKR.ngay = '';
  TKR.buoc = 'dat'; TKR.loi = '';
}

/* Câu lỗi kiểm ở máy khách trước khi gửi (máy chủ vẫn kiểm lại hết). */
export function loiTruocGui() {
  const g = tamTinh();
  if (g.loi) return g.loi;
  if (!TKR.ngay) return t('tkr_loi_ngay', 'Chọn ngày cần bánh.');
  if (TKR.ngay < ngaySom()) return t('tkr_loi_ngay_som', 'Ngày sớm nhất còn nhận là {ngay}.', {ngay: dm(ngaySom())});
  if (!TKR.diem) return t('tkr_loi_noi_nhan', 'Chọn nơi nhận bánh.');
  if (!TKR.ten.trim() || !/^0[35789][0-9]{8}$/.test(chuanSdt(TKR.sdt))) return t('tkr_loi_lien_he', 'Điền họ tên và số điện thoại di động hợp lệ.');
  return '';
}
function chuanSdt(s) { let x = String(s || '').replace(/[\s.()+-]/g, ''); if (x.startsWith('84')) x = '0' + x.slice(2); return x; }
function dm(iso) { const p = String(iso || '').split('-'); return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : ''; }

export async function guiDon() {
  if (TKR.dangGui) return;
  if (ND.xemThu) { TKR.loi = t('tkr_xem_thu', 'Đây là bản xem trước, không gửi đơn.'); return; }
  const loi = loiTruocGui();
  if (loi) { TKR.loi = loi; return; }
  TKR.maLan = TKR.maLan || MT.uuid();
  TKR.dangGui = true; TKR.loi = '';
  try {
    const kq = await MT.ghi('vagabond.thiet_ke_rieng.dat', {ma_lan_gui: TKR.maLan, du_lieu: {
      tac_pham: TKR.id, kich_co: TKR.kc, trang_tri: TKR.tt.slice(), ngay: TKR.ngay, gio: TKR.gio,
      ghi_chu: TKR.ghiChu.trim(), diem_nhan: TKR.diem, ten: TKR.ten.trim(), sdt: TKR.sdt.trim(), ma_anh: TKR.maAnh}});
    if (!kq || !kq.ma || !kq.qr) throw new Error(docLoi(kq) || t('tkr_loi_gui', 'Chưa gửi được đơn. Kiểm tra mạng rồi bấm lại, đơn không bị gửi trùng.'));
    TKR.kq = kq; TKR.buoc = 'qr'; TKR.trangThai = 'cho_coc'; TKR.nhanTT = ''; TKR.lanHoi = 0;
    henHoi();
  } catch (e) { TKR.loi = e.message || t('tkr_loi_gui', 'Chưa gửi được đơn. Kiểm tra mạng rồi bấm lại, đơn không bị gửi trùng.'); }
  finally { TKR.dangGui = false; }
}
function docLoi(kq) {
  try { const tb = JSON.parse((kq && kq._server_messages) || '[]').map(x => JSON.parse(x).message); return tb.join(' '); } catch (e) { return ''; }
}

/* Hỏi máy chủ tiền cọc đã về chưa, mỗi 8 giây, tối đa khoảng 12 phút. */
export async function hoiTrangThai() {
  if (!TKR.kq) return;
  TKR.lanHoi += 1;
  try {
    const r = await MT.ghi('vagabond.thiet_ke_rieng.trang_thai_don', {ma: TKR.kq.ma, khoa: TKR.kq.khoa});
    if (r && r.trang_thai) { TKR.trangThai = r.trang_thai; TKR.nhanTT = r.nhan || ''; }
  } catch (e) { /* mạng chập chờn: hỏi lại lượt sau */ }
  if (TKR.trangThai === 'cho_coc' && TKR.lanHoi < LAN_HOI_TOI_DA) henHoi();
}
function henHoi() { TKR.henHoi = MT.hen(hoiTrangThai, PHUT_HOI); }
function dungHoi() { if (TKR.henHoi) MT.huyHen(TKR.henHoi); TKR.henHoi = null; }

export async function chonAnh(tep) {
  if (!tep) return;
  if (tep.size > 8 * 1024 * 1024) { TKR.loi = t('tkr_anh_lon', 'Ảnh lớn hơn 8 MB, chọn ảnh nhỏ hơn.'); return; }
  TKR.dangTaiAnh = true; TKR.loi = '';
  try { const r = await MT.taiTep('vagabond.thiet_ke_rieng.tai_anh_mau', tep); TKR.maAnh = r.ma_anh || ''; TKR.tenAnh = tep.name || 'ảnh'; }
  catch (e) { TKR.maAnh = ''; TKR.tenAnh = ''; TKR.loi = e.message; }
  finally { TKR.dangTaiAnh = false; }
}

export async function guiTuVan() {
  const v = TKR.tv;
  if (ND.xemThu) { v.loi = t('tkr_xem_thu', 'Đây là bản xem trước, không gửi đơn.'); return; }
  if (!v.ten.trim() || !/^0[35789][0-9]{8}$/.test(chuanSdt(v.sdt))) { v.loi = t('tkr_loi_lien_he', 'Điền họ tên và số điện thoại di động hợp lệ.'); return; }
  v.gui = true; v.loi = '';
  try {
    const r = await MT.ghi('vagabond.thiet_ke_rieng.nho_tu_van', {du_lieu: {tac_pham: TKR.id, ten: v.ten.trim(), sdt: v.sdt.trim()}});
    if (!r || !r.ok) throw new Error(docLoi(r) || t('tkr_tv_loi', 'Chưa gửi được. Bấm gửi lại hoặc gọi cho chúng tôi.'));
    v.xong = true;
  } catch (e) { v.loi = e.message; }
  finally { v.gui = false; }
}

/* ---------------- điều hướng ---------------- */
export function moTkr(id, win = window) {
  const url = win.location.pathname + win.location.search + '#/thiet-ke-rieng' + (id ? '/' + encodeURIComponent(id) : '');
  win.history.pushState({vgb: 1}, '', url);
  win.dispatchEvent(new win.PopStateEvent('popstate', {state: {vgb: 1}}));
  if (win.scrollTo) win.scrollTo(0, 0);
}

/* ---------------- giao diện ---------------- */
const lines = s => String(s || '').split('\n').map(x => x.trim()).filter(Boolean);
const anToan = u => typeof u === 'string' && !/[\s\\]/.test(u) && !u.startsWith('/private/') && ((u[0] === '/' && u[1] !== '/') || /^https:\/\/[^/@]+(?:\/|$)/.test(u));
const nut = (lop, chu, bam, them) => h('button', Object.assign({class: lop, type: 'button', onClick: bam}, them || {}), chu);

function theTacPham(k) {
  const so = (k.kich_co || []).length;
  return h('button', {class: 'tkr-the', type: 'button', 'data-tkr': k.id, onClick: () => moTkr(k.id)}, [
    h('span', {class: 'tkr-the-anh'}, anToan(k.anh) ? [h('img', {src: k.anh, alt: k.mo_ta_anh || '', loading: 'lazy'})] : [h('span', null, k.tieu_de)]),
    h('span', {class: 'tkr-the-chu'}, [
      h('b', {class: 'tkr-ten'}, k.tieu_de),
      k.nhan ? h('span', {class: 'tkr-mo'}, k.nhan) : null,
      h('span', {class: 'tkr-gia'}, t('tkr_tu_gia', 'Từ {gia}', {gia: tienVN(tkrTuGia(k))}) + ' · ' + t('tkr_so_size', '{so} size', {so})),
      h('span', {class: 'tkr-nhan'}, t('tkr_dat_truoc_ngay', 'Đặt trước {so} ngày', {so: tkrSoNgay(k)}))])
  ]);
}

function veDs() {
  const ds = dsTacPham();
  const dau = [h('div', {class: 'meta'}, [h('span', {class: 'num'}, [h('span', null, t('tkr_meta', '03 / Thiết kế riêng'))]), h('span', null, t('tkr_meta_phai', 'Bếp làm riêng cho tiệc'))]),
    h('h1', {class: 'h1'}, [t('tkr_tieu_de', 'Pièce montée'), h('em', null, t('tkr_tieu_de_phu', 'Tác phẩm cho tiệc cưới, tiệc lớn'))]),
    h('p', {class: 'tkr-lead'}, t('tkr_loi_dau', 'Mỗi chiếc làm riêng theo ngày tiệc của quý khách. Đặt cọc để giữ lịch bếp.'))];
  let than;
  if (!ND.daTai && !ND.xemThu) than = [h('p', {class: 'cm-rong', role: 'status'}, ND.loiTai ? t('tkr_loi_tai', 'Chưa tải được danh sách tác phẩm. Tải lại trang hoặc gọi cho chúng tôi.') : t('tkr_dang_tai', 'Đang tải các tác phẩm...'))];
  else if (!ds.length) than = [h('p', {class: 'cm-rong'}, t('tkr_rong', 'Chưa có tác phẩm nào nhận đặt trên web. Gọi cho chúng tôi để được tư vấn.'))];
  else than = [h('div', {class: 'tkr-ds'}, ds.map(theTacPham))];
  return h('div', {class: 'tkr-khung', id: 'tkr-ds'}, [h('section', {class: 'hero tkr-hero-ds'}, dau), ...than]);
}

function veSize(tp) {
  return h('div', {class: 'tkr-sz', role: 'radiogroup', 'aria-label': t('tkr_chon_size', 'Chọn size')}, (tp.kich_co || []).map(x =>
    h('button', {type: 'button', role: 'radio', 'aria-checked': String(TKR.kc === x.ten), class: TKR.kc === x.ten ? 'on' : '', 'data-size': x.ten,
      onClick: () => chonKichCo(x.ten)}, [h('b', null, x.ten), h('span', null, x.mo_ta || ''), h('i', null, tienVN(x.gia))])));
}

function veTuVan(tp) {
  const v = TKR.tv;
  if (!v.mo) return nut('tkr-nut2', t('tkr_nho_tu_van', 'Nhờ Sales tư vấn trước'), () => { v.mo = true; }, {'data-tkr-tv': '1'});
  if (v.xong) return h('p', {class: 'tkr-xong', role: 'status'}, t('tkr_tv_xong', 'Đã nhận. Sales sẽ gọi quý khách trong giờ làm việc.'));
  const o = (nhan, k, kieu, them) => h('label', {class: 'tkr-o'}, [nhan, h('input', Object.assign({type: kieu, value: v[k], onInput: e => { v[k] = e.target.value; }}, them))]);
  return h('form', {class: 'tkr-tv', 'data-tkr-tv-form': '1', onSubmit: e => { e.preventDefault(); guiTuVan(); }}, [
    h('p', {class: 'tkr-tv-chu'}, t('tkr_tv_mo', 'Để lại tên và số điện thoại, Sales gọi lại tư vấn {ten}.', {ten: tp.tieu_de})),
    o(t('tkr_ho_ten', 'Họ tên'), 'ten', 'text', {autocomplete: 'name', maxlength: 120, name: 'tv_ten'}),
    o(t('tkr_sdt', 'Số điện thoại'), 'sdt', 'tel', {autocomplete: 'tel', inputmode: 'numeric', name: 'tv_sdt'}),
    h('button', {class: 'tkr-nut', type: 'submit', disabled: v.gui}, v.gui ? t('tkr_dang_gui', 'Đang gửi...') : t('tkr_tv_gui', 'Gửi cho Sales')),
    v.loi ? h('p', {class: 'tkr-loi', role: 'alert'}, v.loi) : null]);
}

function veXem(tp) {
  const gom = lines(tp.yeu_cau);
  return h('article', {class: 'tkr-tp', id: 'tkr-tp', 'data-tkr-buoc': 'xem'}, [
    h('div', {class: 'tkr-hero'}, [anToan(tp.anh) ? h('img', {src: tp.anh, alt: tp.mo_ta_anh || '', loading: 'eager'}) : null,
      nut('tkr-lui', '←', () => moTkr(''), {'aria-label': t('tkr_ve_ds', 'Về danh sách tác phẩm')}),
      h('div', {class: 'tkr-hero-chu'}, [h('p', {class: 'tkr-nho'}, t('tkr_ten_tab', 'Thiết kế riêng')), h('h1', null, tp.tieu_de)])]),
    h('div', {class: 'tkr-than'}, [
      tp.noi_dung ? h('p', {class: 'tkr-lead'}, tp.noi_dung) : null,
      h('p', {class: 'tkr-lbl'}, t('tkr_chon_size', 'Chọn size')), veSize(tp),
      tp.dieu_kien ? h('p', {class: 'tkr-note'}, tp.dieu_kien) : h('p', {class: 'tkr-note'}, t('tkr_gia_vat', 'Giá đã gồm VAT.')),
      gom.length ? h('p', {class: 'tkr-lbl'}, t('tkr_gom_gi', 'Bánh gồm gì')) : null,
      gom.length ? h('ul', {class: 'tkr-gom'}, gom.map(x => h('li', null, x))) : null,
      h('p', {class: 'tkr-lbl'}, t('tkr_thoi_gian', 'Thời gian')),
      h('p', {class: 'tkr-li'}, t('tkr_thoi_gian_chu', 'Đặt trước ít nhất {so} ngày. Nhận tại cửa hàng.', {so: tkrSoNgay(tp)})),
      nut('tkr-nut', t('tkr_chon_ngay_dat', 'Chọn ngày và đặt cọc'), sangDat, {'data-tkr-dat': '1'}),
      veTuVan(tp)])
  ]);
}

function veDat(tp) {
  const g = tamTinh(), som = ngaySom(), dn = diemNhan();
  const kc = (tp.kich_co || []).find(x => x.ten === TKR.kc) || {};
  const o = (nhan, k, kieu, them) => h('label', {class: 'tkr-o'}, [nhan, h(kieu === 'area' ? 'textarea' : 'input',
    Object.assign(kieu === 'area' ? {} : {type: kieu}, {value: TKR[k], onInput: e => { TKR[k] = e.target.value; TKR.loi = ''; }}, them))]);
  return h('article', {class: 'tkr-tp tkr-dat', id: 'tkr-dat', 'data-tkr-buoc': 'dat'}, [
    h('div', {class: 'tkr-bar'}, [nut('tkr-lui2', '← ' + tp.tieu_de + ' · ' + TKR.kc, () => { TKR.buoc = 'xem'; }, {'data-tkr-quay-lai': '1'}),
      h('span', null, t('tkr_buoc_2', 'Bước 2/3'))]),
    h('div', {class: 'tkr-than'}, [
      h('p', {class: 'tkr-lbl'}, t('tkr_ngay_tiec', 'Ngày cần bánh')),
      h('div', {class: 'tkr-hai'}, [o(t('tkr_ngay', 'Ngày'), 'ngay', 'date', {min: som, name: 'tkr_ngay', 'data-tkr-ngay': '1'}),
        o(t('tkr_gio', 'Giờ (không bắt buộc)'), 'gio', 'time', {name: 'tkr_gio'})]),
      h('p', {class: 'tkr-note'}, t('tkr_ngay_som', 'Ngày sớm nhất còn nhận: {ngay}.', {ngay: dm(som)})),
      (tp.trang_tri || []).length ? h('p', {class: 'tkr-lbl'}, t('tkr_trang_tri', 'Trang trí')) : null,
      (tp.trang_tri || []).length ? h('div', {class: 'cm-chips tkr-chips'}, tp.trang_tri.map(x => h('button', {type: 'button', 'aria-pressed': String(TKR.tt.includes(x.ten)),
        'data-tt': x.ten, onClick: () => batTrangTri(x.ten)}, x.ten + (+x.gia_them > 0 ? ' + ' + tienVN(x.gia_them) : '')))) : null,
      o(t('tkr_ghi_chu_bep', 'Ghi chú cho bếp (không bắt buộc)'), 'ghiChu', 'area', {maxlength: 500, rows: 3, name: 'tkr_ghi_chu',
        placeholder: t('tkr_ghi_chu_goi_y', 'Ví dụ: tiệc cưới, tông kem và vàng.')}),
      h('label', {class: 'tkr-anh-chon'}, [TKR.dangTaiAnh ? t('tkr_dang_tai_anh', 'Đang gửi ảnh...') : (TKR.tenAnh ? t('tkr_da_co_anh', 'Đã gửi ảnh tham khảo: {ten}', {ten: TKR.tenAnh}) : t('tkr_gui_anh', '+ Gửi ảnh tham khảo')),
        h('input', {type: 'file', accept: 'image/jpeg,image/png,image/webp', class: 'tkr-an', onChange: e => chonAnh(e.target.files && e.target.files[0])})]),
      h('p', {class: 'tkr-lbl'}, t('tkr_nhan_banh', 'Nhận bánh')),
      dn.length ? h('div', {class: 'cm-chips tkr-chips', role: 'radiogroup'}, dn.map(d => h('button', {type: 'button', 'aria-pressed': String(TKR.diem === d.id), 'data-diem': d.id,
        title: d.a, onClick: () => { TKR.diem = d.id; TKR.loi = ''; }}, d.n))) : h('p', {class: 'tkr-loi'}, t('tkr_chua_diem', 'Chưa có điểm nhận bánh. Gọi cho chúng tôi để đặt.')),
      h('p', {class: 'tkr-note'}, t('tkr_chi_tu_lay', 'Bánh thiết kế riêng nhận tại cửa hàng. Cần giao tận nơi thì nhờ Sales tư vấn.')),
      h('p', {class: 'tkr-lbl'}, t('tkr_lien_he', 'Thông tin liên hệ')),
      h('div', {class: 'tkr-hai'}, [o(t('tkr_ho_ten', 'Họ tên'), 'ten', 'text', {autocomplete: 'name', maxlength: 120, name: 'tkr_ten'}),
        o(t('tkr_sdt', 'Số điện thoại'), 'sdt', 'tel', {autocomplete: 'tel', inputmode: 'numeric', name: 'tkr_sdt'})]),
      h('div', {class: 'tkr-sum', 'data-tkr-tong': '1'}, g.loi ? [h('p', null, g.loi)] : [
        h('div', null, [h('span', null, t('tkr_dong_size', '{ten} size {size} (gồm VAT)', {ten: tp.tieu_de, size: TKR.kc})), h('span', null, tienVN(kc.gia || 0))]),
        g.tong !== (+kc.gia || 0) ? h('div', null, [h('span', null, t('tkr_dong_trang_tri', 'Trang trí thêm')), h('span', null, tienVN(g.tong - (+kc.gia || 0)))]) : null,
        h('div', {class: 't'}, [h('span', null, t('tkr_coc_hom_nay', 'Đặt cọc 50% hôm nay')), h('b', {'data-tkr-coc': '1'}, tienVN(g.coc))]),
        h('div', null, [h('span', null, t('tkr_tra_khi_nhan', 'Trả khi nhận bánh')), h('span', null, tienVN(g.con_lai))])]),
      h('button', {class: 'tkr-nut', type: 'button', disabled: TKR.dangGui || TKR.dangTaiAnh, 'data-tkr-gui': '1', onClick: guiDon},
        TKR.dangGui ? t('tkr_dang_gui', 'Đang gửi...') : t('tkr_coc_qr', 'Đặt cọc qua QR')),
      TKR.loi ? h('p', {class: 'tkr-loi', role: 'alert', 'data-tkr-loi': '1'}, TKR.loi) : null,
      h('p', {class: 'tkr-note'}, t('tkr_luu_y_coc', 'Tiền cọc giữ lịch bếp cho ngày tiệc. Đổi ngày hoặc huỷ, quý khách gọi Sales.'))])
  ]);
}

function veQr() {
  const k = TKR.kq, q = k.qr || {}, da = TKR.trangThai && TKR.trangThai !== 'cho_coc';
  return h('article', {class: 'tkr-tp tkr-qr', id: 'tkr-qr', 'data-tkr-buoc': 'qr'}, [
    h('div', {class: 'tkr-bar'}, [h('span', null, t('tkr_ma_don', 'Mã đơn {ma}', {ma: k.ma})), h('span', null, t('tkr_buoc_3', 'Bước 3/3'))]),
    h('div', {class: 'tkr-than'}, [
      h('p', {class: 'tkr-tt ' + (da ? 'ok' : 'cho'), role: 'status', 'data-tkr-tt': TKR.trangThai || 'cho_coc'},
        da ? t('tkr_da_coc', 'Đã nhận cọc. Sales sẽ gọi xác nhận đơn với quý khách.') : t('tkr_cho_coc', 'Đang chờ tiền cọc về. Trang tự cập nhật sau khi chuyển khoản.')),
      da ? null : h('div', {class: 'tkr-qr-o'}, [q.anh ? h('img', {src: q.anh, alt: t('tkr_qr_alt', 'Mã QR chuyển khoản tiền cọc'), width: 220, height: 220}) : null]),
      h('dl', {class: 'tkr-ck'}, [
        h('dt', null, t('tkr_so_tien_coc', 'Số tiền cọc')), h('dd', {'data-tkr-qr-tien': '1'}, tienVN(q.so_tien)),
        h('dt', null, t('tkr_noi_dung_ck', 'Nội dung chuyển khoản')), h('dd', {'data-tkr-qr-nd': '1'}, q.noi_dung),
        h('dt', null, t('tkr_ngan_hang', 'Ngân hàng')), h('dd', null, q.ngan_hang),
        h('dt', null, t('tkr_so_tk', 'Số tài khoản')), h('dd', null, q.stk),
        h('dt', null, t('tkr_ten_tk', 'Tên tài khoản')), h('dd', null, q.ten_tk)]),
      h('div', {class: 'tkr-sum'}, [
        h('div', null, [h('span', null, t('tkr_tong_don', 'Tổng đơn (gồm VAT)')), h('span', null, tienVN(k.tong))]),
        h('div', {class: 't'}, [h('span', null, t('tkr_coc', 'Cọc')), h('b', null, tienVN(k.coc))]),
        h('div', null, [h('span', null, t('tkr_tra_khi_nhan', 'Trả khi nhận bánh')), h('span', null, tienVN(k.con_lai))])]),
      h('p', {class: 'tkr-note'}, t('tkr_giu_ma', 'Ghi đúng nội dung {ma} để máy nhận ra tiền cọc. Cần hỗ trợ gọi {so}.', {ma: k.ma, so: telSo()}))])
  ]);
}

export const ThietKeRieng = {
  name: 'ThietKeRieng',
  render() {
    const tp = TKR.id ? tacPhamDangMo() : null;
    if (TKR.id && !tp) {
      if (!ND.daTai && !ND.xemThu) return h('p', {class: 'cm-rong', role: 'status'}, t('tkr_dang_tai', 'Đang tải các tác phẩm...'));
      return h('div', {class: 'tkr-khung'}, [h('p', {class: 'cm-rong'}, t('tkr_het', 'Tác phẩm này không còn nhận đặt trên web.')),
        nut('cm-nut', t('tkr_xem_khac', 'Xem các tác phẩm khác'), () => moTkr(''))]);
    }
    if (!tp) return veDs();
    if (TKR.buoc === 'qr' && TKR.kq) return veQr();
    if (TKR.buoc === 'dat') return veDat(tp);
    return veXem(tp);
  }
};
