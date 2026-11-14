/* v658 (anh Việt chọn A ngày 14/11/2026): tab "Vé sự kiện" thay tab Tiệc.

   Sự kiện vẫn do Marketing tạo ở trình biên tập web (khối loai = tiec, thêm
   loại Tiệc / Ra mắt món / Diễn giả), máy chủ vẫn là tiec_web.dang_ky: khách
   giữ chỗ, nhận mã vé, Sales gọi xác nhận và thu tiền như trước. Chưa thu tiền
   trên web, nên mọi câu ở đây nói "giữ chỗ", không nói "đã mua vé".

   Số chỗ còn do máy chủ tính (ND.ve, khoá khi đăng ký), trang chỉ hiện và chặn
   chọn quá số còn. Không v-html: chữ của Marketing và của khách luôn là chữ. */
import {h, reactive} from '../lib/vue.esm-browser.prod.js';
import {ND, t, mxh} from '../kho/chu.js';
import {ghi} from '../kho/api.js';
import {khachThay, veVe, anToan, ngay, dong as dongChu, DoanGap, NhanMon} from './noi-dung.js';

/* Trùng noi_dung_web.LOAI_SU_KIEN (ca thu_ve_su_kien_658 chốt). Trống là Tiệc. */
export const LOAI_SU_KIEN = {tiec: 'Tiệc', ra_mat: 'Ra mắt món', dien_gia: 'Diễn giả'};
export const VE_TOI_DA = 10;
const THU = ['CN', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7'];
const THANG = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(n => 'Tháng ' + n);

function homNayVN() { return new Intl.DateTimeFormat('en-CA', {timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit'}).format(new Date()); }
const tien = n => String(Math.round(+n || 0)).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + 'đ';
const gio = s => String(s || '').replace(/^0(\d)/, '$1').replace(':', 'g');
export const loaiCua = k => (LOAI_SU_KIEN[k.loai_su_kien] ? k.loai_su_kien : 'tiec');

/* Ô ngày của thẻ: tháng, ngày, thứ. THUẦN. */
export function oNgay(s) {
  const p = String(s || '').split('-');
  if (p.length !== 3) return null;
  const d = new Date(+p[0], +p[1] - 1, +p[2]);
  return {thang: THANG[d.getMonth()], ngay: p[2], thu: THU[d.getDay()]};
}
/* Sự kiện khách thấy: đang hiện, chưa diễn ra (khachThay cùng luật với chuyên
   mục cũ), xếp ngày gần trước. THUẦN theo ND.khoi. */
export function dsSuKien(homNay = homNayVN()) {
  return (ND.khoi || []).filter(k => k.loai === 'tiec' && (ND.xemThu || khachThay(k, homNay)))
    .sort((a, b) => String(a.bat_dau || '9999').localeCompare(String(b.bat_dau || '9999')) || String(a.gio_bat_dau || '').localeCompare(String(b.gio_bat_dau || '')));
}
/* Còn nhận giữ chỗ không và vì sao. THUẦN. */
export function trangThaiVe(k, homNay) {
  const v = veVe(k), han = k.han_ban || k.bat_dau;
  if (han && han < homNay) return {mo: false, nut: t('vsk_het_han', 'Hết hạn đăng ký'), con: v.con};
  if (v.con === 0) return {mo: false, nut: t('vsk_het_ve', 'Hết vé'), con: 0};
  return {mo: true, nut: t('vsk_chon_ve', 'Chọn vé'), con: v.con};
}
/* Số vé tối đa một lần giữ chỗ: không quá số còn, không quá 10. THUẦN. */
export const veToiDa = con => Math.max(0, Math.min(VE_TOI_DA, con == null ? VE_TOI_DA : con));

/* Kết quả và mã lần gửi giữ THEO TỪNG sự kiện: khách đóng sheet giữa lúc gửi rồi
   mở sự kiện khác thì trả lời muộn của lần trước không hiện nhầm mã vé sang sự
   kiện này; mở lại sự kiện đã giữ chỗ thì thấy lại mã vé. */
export const VSK = reactive({loai: '', mo: '', so: 1, ten: '', sdt: '', ghi: '', bao: '', dangGui: '', xong: {}, maGui: {}});
function moSheet(k) {
  Object.assign(VSK, {mo: k.id, so: 1, bao: ''});
  try { document.body.style.overflow = 'hidden'; } catch (e) { /* node */ }
}
export function dongSheet() {
  VSK.mo = '';
  try { document.body.style.overflow = ''; } catch (e) { /* node */ }
}
function uuid() {
  try { if (window.crypto && crypto.randomUUID) return crypto.randomUUID(); } catch (e) { /* trình duyệt cũ */ }
  return 'xxxxxxxx-xxxx-4xxx-8xxx-xxxxxxxxxxxx'.replace(/x/g, () => (Math.random() * 16 | 0).toString(16));
}
export async function giuCho(k) {
  if (ND.xemThu) { VSK.bao = t('vsk_xem_thu', 'Đây là bản xem trước, không gửi giữ chỗ.'); return; }
  const id = k.id;
  VSK.maGui[id] = VSK.maGui[id] || uuid();
  VSK.dangGui = id; VSK.bao = t('vsk_dang_gui', 'Đang gửi...');
  let bao = '';
  try {
    const m = await ghi('vagabond.tiec_web.dang_ky', {du_lieu: {tiec_id: id, ten: VSK.ten, sdt: VSK.sdt, so_ve: VSK.so, ghi_chu: VSK.ghi}, ma_lan_gui: VSK.maGui[id]});
    if (!m || !m.ma) throw new Error(t('vsk_loi', 'Chưa gửi được. Kiểm tra mạng rồi bấm Giữ chỗ lại.'));
    VSK.xong[id] = m.ma;
  } catch (er) { bao = er.message || t('vsk_loi', 'Chưa gửi được. Kiểm tra mạng rồi bấm Giữ chỗ lại.'); }
  if (VSK.dangGui === id) VSK.dangGui = '';
  /* Câu báo chỉ hiện nếu khách vẫn đang mở đúng sự kiện này. */
  if (VSK.mo === id) VSK.bao = bao;
}

function theSuKien(k, homNay) {
  const o = oNgay(k.bat_dau), tt = trangThaiVe(k, homNay);
  const thoi = k.gio_bat_dau && k.gio_ket_thuc ? gio(k.gio_bat_dau) + ' - ' + gio(k.gio_ket_thuc) : '';
  const mo = String(k.nhan || '').trim() || String(k.noi_dung || '').split('\n')[0];
  const cho = tt.con == null ? '' : tt.con ? t('vsk_con_cho', 'Còn {so} chỗ', {so: tt.con}) : t('vsk_het_cho', 'Hết chỗ');
  return h('article', {class: 'tkr-the vsk-the' + (tt.mo ? '' : ' vsk-het'), 'data-vsk': k.id}, [
    h('span', {class: 'vsk-ngay', 'aria-hidden': o ? null : 'true'}, o ? [h('i', null, o.thang), h('b', null, o.ngay), h('i', null, o.thu)] : [h('i', null, t('vsk_chua_ngay', 'Sắp có ngày'))]),
    h('span', {class: 'tkr-the-chu'}, [
      h('span', {class: 'vsk-loai'}, LOAI_SU_KIEN[loaiCua(k)]),
      h('b', {class: 'tkr-ten'}, k.tieu_de),
      thoi || mo ? h('span', {class: 'tkr-mo vsk-mo'}, [thoi, thoi && mo ? ' · ' : '', mo].join('')) : null,
      h('span', {class: 'tkr-gia'}, [+k.gia_ve > 0 ? tien(k.gia_ve) + ' / ' + t('vsk_ve', 'vé') : t('vsk_mien_phi', 'Miễn phí'), cho ? ' · ' + cho : ''].join('')),
      h('button', {class: 'vsk-nut', type: 'button', disabled: !tt.mo, onClick: () => moSheet(k)}, tt.nut)])
  ]);
}

function chiTietSuKien(k, tt) {
  const ra = [];
  if (k.anh && anToan(k.anh)) ra.push(h('img', {class: 'vsk-sh-anh', src: k.anh, alt: k.mo_ta_anh || '', loading: 'lazy'}));
  if (k.dia_diem) ra.push(h('p', {class: 'vsk-sh-dia'}, k.dia_diem));
  if (k.han_ban && tt.mo) ra.push(h('p', {class: 'vsk-sh-han'}, t('cm_han_dk', 'Đăng ký trước') + ' ' + ngay(k.han_ban)));
  if (k.noi_dung) ra.push(h('div', {class: 'vsk-sh-chuyen'}, [h('p', {class: 'vsk-sh-nhan'}, t('cm_cau_chuyen', 'Câu chuyện')), h(DoanGap, {chu: k.noi_dung})]));
  const ds = dongChu(k.yeu_cau);
  if (ds.length) ra.push(h('div', {class: 'vsk-sh-mon'}, [h('p', {class: 'vsk-sh-nhan'}, [t('cm_bao_gom', 'Bao gồm'), ' · ', ds.length + ' ' + t('cm_mon', 'món')].join('')), h(NhanMon, {ds})]));
  return ra;
}

function sheetVe(k, homNay) {
  if (!k) return null;
  const tt = trangThaiVe(k, homNay), toi = veToiDa(tt.con), o = oNgay(k.bat_dau);
  if (VSK.so > toi) VSK.so = Math.max(1, toi);
  const dau = h('div', {class: 'vsk-sh-dau'}, [
    h('p', {class: 'vsk-loai'}, LOAI_SU_KIEN[loaiCua(k)]),
    h('h2', null, k.tieu_de),
    h('p', {class: 'vsk-sh-ngay'}, [o ? o.thu + ', ' + o.ngay + '/' + String(k.bat_dau).slice(5, 7) : '', k.gio_bat_dau && k.gio_ket_thuc ? ' · ' + gio(k.gio_bat_dau) + ' - ' + gio(k.gio_ket_thuc) : ''].join(''))]);
  /* Codex #566 vòng 3: mọi thông tin Marketing nhập cho sự kiện (ảnh, địa điểm,
     hạn đăng ký, câu chuyện, danh sách Bao gồm) phải đọc được ở sheet, như thẻ
     Tiệc cũ (TheTiec) từng hiện. Ca F49 chốt từng trường. */
  const chiTiet = chiTietSuKien(k, tt);
  const dong = h('button', {class: 'vsk-dong', type: 'button', 'aria-label': t('vsk_dong', 'Đóng'), onClick: dongSheet}, '✕');
  let than;
  if (VSK.xong[k.id]) {
    than = [h('div', {class: 'vsk-xong', role: 'status'}, [
      h('p', null, t('vsk_xong_1', 'Đã giữ chỗ. Mã vé của quý khách:')),
      h('b', {class: 'vsk-ma'}, VSK.xong[k.id]),
      h('p', null, t('vsk_xong_2', 'Chúng tôi sẽ gọi xác nhận và hướng dẫn thanh toán. Đến cửa, quý khách đọc mã vé này.')),
      h('button', {class: 'vsk-nut vsk-nut-lon', type: 'button', onClick: dongSheet}, t('vsk_xong_dong', 'Xong'))])];
  } else {
    const o2 = (nhan, khoa, kieu, them) => h('label', {class: 'vsk-o'}, [nhan, h('input', Object.assign({type: kieu, value: VSK[khoa], onInput: e => { VSK[khoa] = e.target.value; }}, them))]);
    than = [
      h('div', {class: 'vsk-so'}, [
        h('span', null, t('vsk_so_ve', 'Số vé')),
        h('div', {class: 'vsk-dem'}, [
          h('button', {type: 'button', 'aria-label': t('vsk_bot', 'Bớt một vé'), disabled: VSK.so <= 1, onClick: () => { VSK.so = Math.max(1, VSK.so - 1); }}, '−'),
          h('b', {'aria-live': 'polite'}, String(VSK.so)),
          h('button', {type: 'button', 'aria-label': t('vsk_them', 'Thêm một vé'), disabled: VSK.so >= toi, onClick: () => { VSK.so = Math.min(toi, VSK.so + 1); }}, '+')])]),
      tt.con != null ? h('p', {class: 'vsk-goi-y'}, t('vsk_con_cho', 'Còn {so} chỗ', {so: tt.con})) : null,
      h('p', {class: 'vsk-tong'}, [h('span', null, t('vsk_tam_tinh', 'Tạm tính')), h('b', null, +k.gia_ve > 0 ? tien(+k.gia_ve * VSK.so) : t('vsk_mien_phi', 'Miễn phí'))]),
      h('form', {class: 'vsk-form', onSubmit: e => { e.preventDefault(); if (tt.mo && VSK.dangGui !== k.id) giuCho(k); }}, [
        o2(t('vsk_ho_ten', 'Họ tên'), 'ten', 'text', {required: true, autocomplete: 'name', maxlength: 120}),
        o2(t('vsk_sdt', 'Số điện thoại'), 'sdt', 'tel', {required: true, autocomplete: 'tel', inputmode: 'numeric'}),
        o2(t('vsk_ghi_chu', 'Ghi chú (không bắt buộc)'), 'ghi', 'text', {maxlength: 500}),
        h('p', {class: 'vsk-luu-y'}, t('vsk_luu_y', 'Giữ chỗ trước, chưa phải trả tiền trên web. Chúng tôi gọi xác nhận và hướng dẫn thanh toán. Đổi hoặc huỷ vé, quý khách liên hệ chúng tôi.')),
        h('button', {class: 'vsk-nut vsk-nut-lon', type: 'submit', disabled: !tt.mo || VSK.dangGui === k.id}, t('vsk_giu_cho', 'Giữ chỗ {so} vé', {so: VSK.so})),
        h('p', {class: 'vsk-bao', role: 'status'}, VSK.bao)])];
  }
  return h('div', {class: 'vsk-nen', onClick: e => { if (e.target === e.currentTarget) dongSheet(); }}, [
    h('div', {class: 'vsk-sheet', role: 'dialog', 'aria-modal': 'true', 'aria-label': k.tieu_de}, [dong, dau, ...chiTiet, ...than])]);
}

export const VeSuKien = {
  name: 'VeSuKien',
  render() {
    const homNay = homNayVN(), ds = dsSuKien(homNay);
    const coLoai = Object.keys(LOAI_SU_KIEN).filter(l => ds.some(k => loaiCua(k) === l));
    if (VSK.loai && !coLoai.includes(VSK.loai)) VSK.loai = '';
    const loc = ds.filter(k => !VSK.loai || loaiCua(k) === VSK.loai);
    const dau = [h('div', {class: 'meta'}, [h('span', {class: 'num'}, [h('span', null, t('vsk_meta', '04 / Vé sự kiện'))]), h('span', null, t('vsk_meta_phai', 'Diễn ra tại The Vagabond'))]),
      h('h1', {class: 'h1'}, [t('vsk_tieu_de', 'Sự kiện'), h('em', null, t('vsk_tieu_de_phu', 'Tiệc, ra mắt món mới, buổi trò chuyện'))]),
      h('p', {class: 'tkr-lead'}, t('vsk_loi_dau', 'Đăng ký trước để giữ chỗ. Chúng tôi gọi xác nhận, đến cửa quý khách đọc mã vé.'))];
    let than;
    if (!ND.daTai && !ND.xemThu) than = [h('p', {class: 'cm-rong', role: 'status'}, ND.loiTai ? t('vsk_loi_tai', 'Chưa tải được sự kiện. Tải lại trang hoặc gọi cho chúng tôi.') : t('vsk_dang_tai', 'Đang tải sự kiện...'))];
    else if (!ds.length) {
      const zalo = mxh('zalo'), ig = mxh('instagram');
      than = [h('p', {class: 'cm-rong vsk-rong'}, [t('vsk_rong', 'Chưa có sự kiện nào mở đăng ký. Theo dõi The Vagabond để nhận tin sự kiện mới:'), ' ',
        zalo ? h('a', {href: zalo, target: '_blank', rel: 'noopener noreferrer'}, 'Zalo OA') : null, zalo && ig ? ' · ' : '',
        ig ? h('a', {href: ig, target: '_blank', rel: 'noopener noreferrer'}, 'Instagram') : null])];
    } else {
      than = [
        coLoai.length > 1 ? h('div', {class: 'cm-chips vsk-chips'}, ['', ...coLoai].map(l => h('button', {type: 'button', 'aria-pressed': String(l === VSK.loai), onClick: () => { VSK.loai = l; }},
          l ? LOAI_SU_KIEN[l] : t('tat_ca_muc', 'Tất cả')))) : null,
        h('div', {class: 'tkr-ds vsk-ds'}, loc.map(k => theSuKien(k, homNay)))];
    }
    const dangMo = VSK.mo ? ds.find(k => k.id === VSK.mo) : null;
    return h('div', {class: 'tkr-khung vsk-khung', id: 'vsk-ds'}, [h('section', {class: 'hero tkr-hero-ds'}, dau), ...than, sheetVe(dangMo, homNay)]);
  }
};
