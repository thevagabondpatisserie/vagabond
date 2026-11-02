/* v630: kho của trang Bánh sỉ (/banh-si) bản Vue (anh Việt chốt 02/11/2026).

   Hai lớp: người ngoài thấy trang hợp tác KHÔNG có giá và form đăng ký; khách
   sỉ đã duyệt đăng nhập bằng mã Zalo (cookie riêng vgb_khach_si, phiên Guest)
   rồi đặt theo bảng giá RIÊNG của mình.

   Mọi số tiền của đơn đã gửi đọc từ máy chủ (banh_si.dat, banh_si.toi). Số
   tạm tính trước khi gửi là bản HIỆN: giá lấy từ bảng giá máy chủ trả trong
   phiên, máy chủ đọc lại giá riêng lúc lập đơn và không nhận giá từ đây.
   Không v-html: chữ của khách và của Marketing luôn là chữ. */
import {reactive} from '../lib/vue.esm-browser.prod.js';
import {t} from '../kho/chu.js';
import {doc as docApi, ghi as ghiApi} from '../kho/api.js';

const PHUT_HOI = 8000, LAN_HOI_TOI_DA = 90, SL_TOI_DA = 5000;

function homNayVN() { return new Intl.DateTimeFormat('en-CA', {timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit'}).format(new Date()); }
function uuid() {
  try { if (window.crypto && crypto.randomUUID) return crypto.randomUUID(); } catch (e) { /* trình duyệt cũ */ }
  return 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g, () => (Math.random() * 16 | 0).toString(16));
}

/* Môi trường: ca kiểm thay mạng, đồng hồ, hẹn giờ. */
const MT = {ghi: ghiApi, doc: docApi, hen: (f, ms) => setTimeout(f, ms), huyHen: id => clearTimeout(id), homNay: homNayVN, uuid};
export function datMoiTruong(m) { Object.assign(MT, m || {}); }

export const LOAI_HINH = [['cafe', 'bsi_lh_cafe', 'Quán cà phê'], ['khach_san', 'bsi_lh_ks', 'Khách sạn'], ['nha_hang', 'bsi_lh_nh', 'Nhà hàng'], ['khac', 'bsi_lh_khac', 'Khác']];
export const LUONG = [['duoi_50', 'bsi_luong_1', 'Dưới 50 cái'], ['50_200', 'bsi_luong_2', '50 - 200 cái'], ['tren_200', 'bsi_luong_3', 'Trên 200 cái']];

export const SI = reactive({
  man: 'cho',            /* cho | ngoai | dat | tai_khoan | xong */
  otp: 1,
  dk: {ten_quan: '', mst: '', sdt: '', loai_hinh: '', luong: '', ghi_chu: '', gui: false, xong: '', loi: '', maLan: ''},
  dn: {mo: false, sdt: '', ma: '', buoc: 'sdt', gui: false, loi: '', song: 0},
  toi: null,
  ngay: '', sl: {}, ghiChu: '', dangGui: false, loi: '', maLan: '', bao: '',
  kq: null, trangThai: '', lanHoi: 0, henHoi: null,
  qrNo: null, dangQr: false, loiQr: '',
  dangQrDon: '', loiQrDon: ''
});

/* ---------------- phép thuần (ca kiểm gọi thẳng) ---------------- */
export function chuanSdt(s) { let x = String(s || '').replace(/[\s.()+-]/g, ''); if (x.startsWith('84')) x = '0' + x.slice(2); return /^0[35789][0-9]{8}$/.test(x) ? x : ''; }
export function congNgay(iso, n) {
  const p = String(iso || '').split('-').map(Number);
  const d = new Date(Date.UTC(p[0], (p[1] || 1) - 1, p[2] || 1) + n * 86400000);
  return d.toISOString().slice(0, 10);
}
export function dm(iso) { const p = String(iso || '').slice(0, 10).split('-'); return p.length === 3 ? p[2] + '/' + p[1] : ''; }
const THU = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
export function thu(iso) { const p = String(iso || '').split('-').map(Number); return THU[new Date(Date.UTC(p[0], p[1] - 1, p[2])).getUTCDay()]; }
/* Sáu ngày giao đầu tiên còn nhận, bắt đầu từ ngày sớm nhất máy chủ trả. */
export function dsNgay(som, so = 6) { return som ? Array.from({length: so}, (_, i) => congNgay(som, i)) : []; }
export function tienVN(n) { return Math.round(Number(n) || 0).toLocaleString('vi-VN').replace(/,/g, '.') + ' đ'; }
export function kepSl(v) { const n = Math.floor(Number(String(v).replace(/[^0-9]/g, '')) || 0); return Math.max(0, Math.min(SL_TOI_DA, n)); }

export function dongChon() {
  const mon = (SI.toi && SI.toi.mon) || [];
  return mon.filter(m => (SI.sl[m.ma] || 0) > 0).map(m => ({ma: m.ma, ten: m.ten, sl: SI.sl[m.ma], gia: m.gia, tien: m.gia * SI.sl[m.ma]}));
}
export function tamTinh() {
  const d = dongChon();
  return {so_mon: d.length, so_cai: d.reduce((a, x) => a + x.sl, 0), tong: d.reduce((a, x) => a + x.tien, 0)};
}
export function loiTruocGui() {
  if (!SI.ngay) return t('bsi_loi_ngay', 'Chọn ngày giao.');
  if (SI.toi && SI.ngay < SI.toi.ngay_som) return t('bsi_loi_ngay_som', 'Ngày giao sớm nhất là {ngay}.', {ngay: dm(SI.toi.ngay_som)});
  if (!dongChon().length) return t('bsi_loi_mon', 'Chọn ít nhất một món với số lượng lớn hơn 0.');
  return '';
}

/* ---------------- hành động ---------------- */
function docLoi(kq) {
  try { return JSON.parse((kq && kq._server_messages) || '[]').map(x => JSON.parse(x).message).join(' '); } catch (e) { return ''; }
}

export async function khoiDong() {
  try { const s = await MT.doc('vagabond.banh_si.san_sang'); SI.otp = s && s.otp ? 1 : 0; } catch (e) { SI.otp = 1; }
  await napToi();
}

export async function napToi() {
  let r = null;
  try { r = await MT.doc('vagabond.banh_si.toi'); } catch (e) { r = null; }
  if (!r || !r.ok) { SI.toi = null; if (SI.man !== 'xong') SI.man = 'ngoai'; return r; }
  SI.toi = r;
  if (!SI.ngay || SI.ngay < r.ngay_som) SI.ngay = r.ngay_som;
  const co = new Set((r.mon || []).map(m => m.ma));
  for (const k of Object.keys(SI.sl)) if (!co.has(k)) delete SI.sl[k];
  if (SI.man === 'cho' || SI.man === 'ngoai') SI.man = 'dat';
  return r;
}

export function chonNgay(iso) { SI.ngay = iso; SI.loi = ''; }
export function datSl(ma, v) { SI.sl[ma] = kepSl(v); SI.loi = ''; SI.bao = ''; }
export function cong(ma, d) { datSl(ma, (SI.sl[ma] || 0) + d); }

/* "Đặt lại như đơn trước": số lượng đơn cũ, giá hôm nay (máy chủ đã lọc món
   thôi bán). Không mang giá cũ. */
export function datLai() {
  const dt = SI.toi && SI.toi.don_truoc;
  if (!dt) return;
  SI.sl = {};
  for (const d of dt.dong || []) SI.sl[d.ma] = kepSl(d.sl);
  SI.bao = dt.bo ? t('bsi_dat_lai_bo', 'Đã chép đơn {ma}. {so} món thôi bán nên không chép.', {ma: dt.ma, so: dt.bo})
    : t('bsi_dat_lai_xong', 'Đã chép số lượng đơn {ma}, giá theo bảng giá hôm nay.', {ma: dt.ma});
  SI.loi = '';
}

export async function guiDon() {
  if (SI.dangGui) return;
  const loi = loiTruocGui();
  if (loi) { SI.loi = loi; return; }
  SI.maLan = SI.maLan || MT.uuid();
  SI.dangGui = true; SI.loi = '';
  try {
    const kq = await MT.ghi('vagabond.banh_si.dat', {ma_lan_gui: SI.maLan, du_lieu: {ngay: SI.ngay, ghi_chu: SI.ghiChu.trim(),
      dong: dongChon().map(d => ({ma: d.ma, sl: d.sl}))}});
    if (!kq || !kq.ma) throw new Error(docLoi(kq) || t('bsi_loi_gui', 'Chưa gửi được đơn. Kiểm tra mạng rồi bấm lại, đơn không bị gửi trùng.'));
    SI.kq = kq; SI.man = 'xong'; SI.trangThai = kq.trang_thai; SI.lanHoi = 0; SI.maLan = ''; SI.sl = {}; SI.ghiChu = '';
    if (kq.trang_thai === 'cho_tt') henHoi();
    napToi();
  } catch (e) { SI.loi = e.message || t('bsi_loi_gui', 'Chưa gửi được đơn. Kiểm tra mạng rồi bấm lại, đơn không bị gửi trùng.'); }
  finally { SI.dangGui = false; }
}

export async function hoiTrangThai() {
  if (!SI.kq) return;
  SI.lanHoi += 1;
  try {
    const r = await MT.ghi('vagabond.banh_si.trang_thai_don', {ma: SI.kq.ma});
    if (r && r.trang_thai) SI.trangThai = r.trang_thai;
  } catch (e) { /* mạng chập chờn: hỏi lại lượt sau */ }
  if (SI.trangThai === 'cho_tt' && SI.lanHoi < LAN_HOI_TOI_DA) henHoi();
}
function henHoi() { SI.henHoi = MT.hen(hoiTrangThai, PHUT_HOI); }
export function dungHoi() { if (SI.henHoi) MT.huyHen(SI.henHoi); SI.henHoi = null; }

export async function moQrNo() {
  if (SI.dangQr) return;
  SI.dangQr = true; SI.loiQr = '';
  try {
    const r = await MT.ghi('vagabond.banh_si.qr_no', {});
    if (!r || !r.ok) throw new Error(docLoi(r) || t('bsi_qr_loi', 'Chưa tạo được mã QR. Gọi Sales để nhận phiếu thanh toán.'));
    SI.qrNo = r.phieu || [];
    if (SI.toi && r.no) SI.toi.no = r.no;
  } catch (e) { SI.loiQr = e.message; }
  finally { SI.dangQr = false; }
}

/* Codex #531 f4: mở lại QR của MỘT đơn trả trước chưa chuyển tiền (khách đã
   tải lại trang hoặc sang Tài khoản nên SI.kq rỗng). Chỉ gửi mã đơn; máy chủ
   kiểm đơn thuộc khách phiên này và tự tính số tiền, trả đúng hình dạng của
   banh_si.dat nên dùng lại màn kết quả và nhịp hỏi trạng thái. */
export function donChoChuyen() {
  return ((SI.toi && SI.toi.sap_giao) || []).filter(d => d.tra_truoc && d.trang_thai === 'cho_tt' && Number(d.con_lai) > 0);
}
export async function moQrDon(ma) {
  if (SI.dangQrDon) return;
  SI.dangQrDon = ma; SI.loiQrDon = '';
  try {
    const r = await MT.ghi('vagabond.banh_si.qr_don', {ma});
    if (!r || !r.ma) throw new Error(docLoi(r) || t('bsi_qr_don_loi', 'Chưa mở được mã QR của đơn. Tải lại trang rồi thử lại.'));
    dungHoi();
    SI.kq = r; SI.trangThai = r.trang_thai; SI.lanHoi = 0; SI.man = 'xong';
    if (r.trang_thai === 'cho_tt') henHoi();
  } catch (e) { SI.loiQrDon = e.message || t('bsi_qr_don_loi', 'Chưa mở được mã QR của đơn. Tải lại trang rồi thử lại.'); }
  finally { SI.dangQrDon = ''; }
}

/* Đăng ký hợp tác (người ngoài). */
export function loiDangKy() {
  const d = SI.dk;
  if (d.ten_quan.trim().length < 2) return t('bsi_dk_loi_ten', 'Điền tên quán hoặc tên công ty.');
  if (!chuanSdt(d.sdt)) return t('bsi_dk_loi_sdt', 'Điền số điện thoại di động có Zalo.');
  if (d.mst.trim() && !/^[0-9]{10}([-]?[0-9]{3})?$|^[0-9]{12}$/.test(d.mst.replace(/[\s.]/g, ''))) return t('bsi_dk_loi_mst', 'Mã số thuế gồm 10 số, để trống nếu chưa có.');
  if (!d.loai_hinh) return t('bsi_dk_loi_loai', 'Chọn loại hình.');
  if (!d.luong) return t('bsi_dk_loi_luong', 'Chọn lượng bánh dự kiến mỗi tuần.');
  return '';
}
export async function guiDangKy() {
  const d = SI.dk;
  if (d.gui) return;
  const loi = loiDangKy();
  if (loi) { d.loi = loi; return; }
  d.maLan = d.maLan || MT.uuid();
  d.gui = true; d.loi = '';
  try {
    const r = await MT.ghi('vagabond.banh_si.dang_ky', {ma_lan_gui: d.maLan, du_lieu: {ten_quan: d.ten_quan.trim(), mst: d.mst.trim(),
      sdt: d.sdt.trim(), loai_hinh: d.loai_hinh, luong: d.luong, ghi_chu: d.ghi_chu.trim()}});
    if (!r || !r.ok) throw new Error(docLoi(r) || t('bsi_dk_loi_gui', 'Chưa gửi được. Bấm gửi lại hoặc gọi cho chúng tôi.'));
    d.xong = r.ma || 'ok';
  } catch (e) { d.loi = e.message; }
  finally { d.gui = false; }
}

/* Đăng nhập bằng mã Zalo. */
const LY_DO = {
  chua_mo_si: ['bsi_dn_chua_mo', 'Số này chưa được mở đặt sỉ. Đăng ký hợp tác bên dưới, Sales sẽ gọi lại.'],
  can_doi_chieu: ['bsi_dn_doi_chieu', 'Số này đang gắn với nhiều khách. Gọi Sales để đối chiếu.'],
  gui_qua_nhieu: ['bsi_dn_qua_nhieu', 'Đã gửi nhiều mã. Chờ 30 phút rồi thử lại.'],
  khong_gui_duoc: ['bsi_dn_khong_gui', 'Chưa gửi được mã qua Zalo. Kiểm tra số có dùng Zalo rồi thử lại.'],
  ma_khong_dung: ['bsi_dn_sai_ma', 'Mã chưa đúng. Kiểm tra tin Zalo rồi gõ lại.'],
  ma_het_han: ['bsi_dn_het_han', 'Mã đã hết hạn. Bấm gửi lại mã.'],
  sai_qua_nhieu: ['bsi_dn_sai_nhieu', 'Gõ sai quá nhiều lần. Bấm gửi lại mã mới.'],
  chua_mo: ['bsi_dn_tat', 'Đăng nhập bằng Zalo đang tạm tắt. Gọi Sales để đặt hàng.']
};
function cauLyDo(ly) { const x = LY_DO[ly]; return x ? t(x[0], x[1]) : t('bsi_dn_loi', 'Chưa đăng nhập được. Thử lại sau ít phút.'); }

export async function guiMa() {
  const d = SI.dn;
  if (d.gui) return;
  if (!chuanSdt(d.sdt)) { d.loi = t('bsi_dk_loi_sdt', 'Điền số điện thoại di động có Zalo.'); return; }
  d.gui = true; d.loi = '';
  try {
    const r = await MT.ghi('vagabond.banh_si.gui_ma', {sdt: d.sdt.trim()});
    if (r && r.ok) { d.buoc = 'ma'; d.song = r.song_giay || 300; } else d.loi = cauLyDo(r && r.ly_do);
  } catch (e) { d.loi = cauLyDo(''); }
  finally { d.gui = false; }
}
export async function xacThuc() {
  const d = SI.dn;
  if (d.gui) return;
  if (!/^[0-9]{6}$/.test(String(d.ma || '').trim())) { d.loi = t('bsi_dn_6so', 'Mã gồm 6 số.'); return; }
  d.gui = true; d.loi = '';
  try {
    const r = await MT.ghi('vagabond.banh_si.xac_thuc', {sdt: d.sdt.trim(), ma: String(d.ma).trim()});
    if (r && r.ok) { d.mo = false; d.buoc = 'sdt'; d.ma = ''; await napToi(); }
    else d.loi = cauLyDo(r && r.ly_do);
  } catch (e) { d.loi = cauLyDo(''); }
  finally { d.gui = false; }
}
export async function thoat() {
  try { await MT.ghi('vagabond.banh_si.thoat', {}); } catch (e) { /* vẫn đưa về trang ngoài */ }
  dungHoi();
  Object.assign(SI, {toi: null, man: 'ngoai', sl: {}, kq: null, qrNo: null, ngay: '', loiQrDon: ''});
}
export function sangMan(m) { SI.man = m; SI.loi = ''; SI.loiQrDon = ''; if (m !== 'xong') dungHoi(); }
