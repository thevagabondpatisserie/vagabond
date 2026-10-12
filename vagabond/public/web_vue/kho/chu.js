/* Kho NỘI DUNG của web bản Vue: nhãn chữ marketing sửa ở /bien-tap-web, chữ
   riêng từng món, liên hệ, khối nội dung, cửa hàng, điểm nhận.

   Thay cho bộ ba chu.js + cua-hang.js + xem-thu.js của trang cũ. Ở trang cũ
   chữ được VÁ vào DOM sau khi vẽ (data-vgb-chu), nên chỗ nào vẽ lại mà quên
   gọi vgbApChu là chữ quay về mặc định. Ở đây mọi chữ đọc từ kho phản ứng:
   nhãn đổi là chỗ nào dùng nhãn đó tự vẽ lại, không có chỗ nào "quên gọi".

   Luật giữ nguyên trang cũ (#367, v532, v586):
   - Nhãn trống hoặc chưa tải thì dùng chữ mặc định trong mã.
   - Chữ của marketing chỉ là CHỮ: Vue tự thoát ký tự, không có v-html nào
     nhận chữ marketing.
   - Số điện thoại trong câu đổi theo thẻ Liên hệ (vgbThayDienThoai cũ).
   - Mạng xã hội: chưa tải thì link mặc định, đã tải thì đúng link marketing
     khai, để trống là ẩn (Codex #453). */
import {reactive} from '../lib/vue.esm-browser.prod.js';
import {linkHopLe} from './thuan.js';

export const DT_GOC = '0931 224 334';

export const ND = reactive({
  daTai: false,
  nhan: {},
  san_pham: {},
  lien_he: null,
  khoi: [],
  thong_tin: {},
  diem_nhan: null,
  ve: {},
  /* Đang được nhúng trong khung xem thử của trình biên tập. */
  xemThu: false,
  /* Khối đang được chọn trong trình biên tập (tô viền). */
  khoiChon: ''
});

function dienThoai() {
  const lh = ND.lien_he;
  return (lh && lh.dien_thoai) || '';
}

export function thayDienThoai(s) {
  const dt = dienThoai();
  return dt && dt !== DT_GOC ? String(s).split(DT_GOC).join(dt) : String(s);
}

/* t(khoa, macDinh, thay): chữ cho khách. `thay` điền chỗ {ten}. */
export function t(khoa, macDinh, thay) {
  const n = ND.nhan[khoa];
  const chu = typeof n === 'string' && n.trim() ? n : macDinh;
  return thayDienThoai(String(chu || '').replace(/\{([a-z_]+)\}/g, (goc, k) =>
    (thay && Object.prototype.hasOwnProperty.call(thay, k) ? String(thay[k]) : goc)));
}

/* Chữ riêng của một món (tên, mô tả, tầng hương, khẩu phần, nhãn mùa). */
export function tMon(ma, truong, macDinh) {
  const nd = ND.san_pham || {};
  const chu = Object.prototype.hasOwnProperty.call(nd, ma) && nd[ma] && nd[ma][truong];
  return typeof chu === 'string' && chu.trim() ? chu : (macDinh || '');
}

export function mxh(k, macDinh) {
  return ND.lien_he ? linkHopLe(ND.lien_he[k]) : (macDinh || '');
}

export function telSo() {
  const lh = ND.lien_he || {};
  const so = String(lh.dien_thoai_so || lh.dien_thoai || '').replace(/[^0-9+]/g, '');
  return so || '0931224334';
}
export function telChu() { return dienThoai() || DT_GOC; }

export function apNoiDung(nd) {
  if (!nd || typeof nd !== 'object') return;
  ND.nhan = nd.nhan || {};
  ND.san_pham = nd.san_pham || {};
  ND.lien_he = nd.lien_he || null;
  ND.khoi = Array.isArray(nd.khoi) ? nd.khoi : [];
  ND.thong_tin = nd.thong_tin || {};
  ND.diem_nhan = Array.isArray(nd.diem_nhan) ? nd.diem_nhan : null;
  ND.ve = nd.ve || {};
  ND.daTai = true;
}

/* Đang nằm trong khung xem thử của trình biên tập (?bien_tap=1 trong iframe). */
export function laXemThu(win) {
  try { return win.parent !== win && new URLSearchParams(win.location.search).get('bien_tap') === '1'; }
  catch (e) { return false; }
}

export function napNoiDung(win = window) {
  ND.xemThu = laXemThu(win);
  if (ND.xemThu) {
    /* Trình biên tập gửi bản nháp qua postMessage, không tải bản công khai. */
    win.addEventListener('message', e => {
      if (e.origin !== win.location.origin || e.source !== win.parent || !e.data) return;
      if (e.data.loai !== 'vgb-noi-dung') return;
      apNoiDung(e.data.noi_dung);
      ND.khoiChon = e.data.chon || '';
      win.dispatchEvent(new CustomEvent('vgb-xem-thu-chon', {detail: {noi_dung: e.data.noi_dung, chon: ND.khoiChon}}));
    });
    win.parent.postMessage({loai: 'vgb-san-sang'}, win.location.origin);
    return Promise.resolve();
  }
  return win.fetch('/api/method/vagabond.noi_dung_web.cong_khai', {headers: {Accept: 'application/json'}})
    .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(d => { if (!d.message) throw new Error('Thiếu nội dung'); apNoiDung(d.message); })
    .catch(e => { /* Lỗi CMS không được chặn đặt bánh: giữ chữ mặc định. */
      if (win.console) win.console.error('Không tải được nội dung website:', e); });
}

/* Bấm vào một khối trong khung xem thử thì báo trình biên tập chọn khối đó. */
export function chonKhoi(id, win = window) {
  if (!ND.xemThu || !id) return;
  win.parent.postMessage({loai: 'vgb-chon-khoi', id}, win.location.origin);
}
