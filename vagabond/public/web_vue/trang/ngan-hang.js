/* v684 (BẢN 2 mục 3.2): mở app ngân hàng để chuyển khoản. THUẦN.

   Dịch vụ: VietQR.io deeplink (Casso), gói miễn phí, không đăng ký (anh Việt
   duyệt 22/11/2026). Link dạng
     https://dl.vietqr.io/pay?app=<mã app>&ba=<số TK>@<mã NH>&am=<số tiền>&tn=<nội dung>&url=<quay về>
   Link CHỈ mang tài khoản Vagabond, số tiền, nội dung có mã đơn: không có
   thông tin của khách.

   Danh sách app lấy theo bảng hỗ trợ của VietQR.io (api.vietqr.io/v2/
   android-app-deeplinks và ios-app-deeplinks, đọc 22/11/2026), riêng iOS và
   Android. Danh sách ngân hàng KHÔNG thay cho danh sách app. `tu_dien` là app
   tự điền sẵn số tiền và nội dung; các app khác chỉ mở được app. */

export const DL = 'https://dl.vietqr.io/pay';

/* [mã app, tên hiện, có trên Android, có trên iOS, tự điền] */
export const APP = [
  ['mb', 'MB Bank', 1, 1, 1], ['vcb', 'Vietcombank', 1, 1, 0], ['tcb', 'Techcombank', 1, 1, 0],
  ['bidv', 'BIDV', 1, 1, 1], ['icb', 'VietinBank', 1, 1, 1], ['acb', 'ACB', 1, 1, 1], ['tpb', 'TPBank', 1, 1, 0],
  ['ocb', 'OCB OMNI', 1, 1, 1], ['vpb', 'VPBank NEO', 1, 1, 0], ['vib-2', 'MyVIB', 1, 1, 0], ['shb', 'SHB SAHA', 1, 1, 0],
  ['lpb', 'LPBank', 1, 1, 0], ['seab', 'SeABank', 1, 1, 0], ['scb', 'SCB', 1, 1, 0], ['cake', 'CAKE', 1, 1, 0],
  ['hdb', 'HDBank', 1, 1, 0], ['vba', 'Agribank Plus', 1, 1, 0], ['timo', 'Timo', 1, 1, 0], ['shbvn', 'Shinhan SOL', 1, 1, 0],
  ['nab', 'Nam A Bank', 1, 0, 0], ['abb', 'ABBank', 1, 1, 0], ['eib', 'Eximbank EDigi', 1, 1, 0], ['coopbank', 'Co-opBank', 1, 1, 0],
  ['pvcb', 'PVConnect', 1, 1, 0], ['wvn', 'Woori WON', 1, 1, 0], ['klb', 'KienlongBank Plus', 1, 1, 0], ['bvb', 'BAOVIET Smart', 1, 1, 0],
  ['vab', 'Vietbank Digital', 1, 1, 0], ['ncb', 'NCB iziMobile', 1, 1, 0], ['acb-biz', 'ACB ONE Biz', 1, 1, 0], ['mbv', 'MBV Bank', 1, 1, 0],
  ['pbvn', 'PB engage', 1, 1, 0], ['sgicb', 'SAIGONBANK', 1, 1, 0], ['cimb', 'Octo by CIMB', 1, 1, 0],
].map(([ma, ten, android, ios, tuDien]) => ({ma, ten, android: !!android, ios: !!ios, tuDien: !!tuDien}));

/* Bảy ô trên lưới (logo trong repo, logo-nh/); còn lại ở ô "Khác". Tên ngắn cho ô
   rộng 1/4 màn 390 px (chữ 13 điểm không bị cắt); tên đủ ở nút Mở app và bảng Khác. */
export const LUOI = ['mb', 'vcb', 'tcb', 'bidv', 'icb', 'acb', 'tpb'];
export const TEN_NGAN = {mb: 'MB', vcb: 'VCB', tcb: 'Techcom', bidv: 'BIDV', icb: 'Vietin', acb: 'ACB', tpb: 'TPBank'};
export const LOGO = ma => (LUOI.includes(ma) ? '/assets/vagabond/web_vue/banh/logo-nh/' + ma + '.webp' : '');

export function heDieuHanh(ua) {
  const s = String(ua || '');
  if (/iPhone|iPad|iPod/i.test(s)) return 'ios';
  if (/Android/i.test(s)) return 'android';
  return '';
}
export const dienThoai = ua => !!heDieuHanh(ua);

/* App mở được trên hệ điều hành này (máy không rõ hệ: mọi app). */
export function appCho(he) {
  return APP.filter(a => (he === 'ios' ? a.ios : he === 'android' ? a.android : true));
}
export const timApp = (ma, he) => appCho(he).find(a => a.ma === ma) || null;

const boDau = s => String(s || '').toLowerCase().replace(/đ/g, 'd').normalize('NFD').replace(/[̀-ͯ]/g, '');
export function locApp(ds, q) {
  const k = boDau(q).trim();
  return k ? ds.filter(a => boDau(a.ten).includes(k) || a.ma.includes(k)) : ds;
}

/* Link mở app. Thiếu số tài khoản, mã ngân hàng hay số tiền thì không dựng (null). */
export function linkMoApp(app, ck, so, quayVe) {
  const stk = String((ck || {}).stk || '').replace(/\s+/g, '');
  const nh = String((ck || {}).ma_nh || '').trim().toLowerCase();
  const tien = Math.round(Number(so) || 0);
  if (!app || !/^[a-z0-9-]{2,12}$/.test(app.ma) || !/^\d{4,20}$/.test(stk) || !/^[a-z0-9]{2,12}$/.test(nh) || tien <= 0) return null;
  const q = new URLSearchParams({app: app.ma, ba: stk + '@' + nh, am: String(tien), tn: String((ck || {}).noi_dung || '').slice(0, 50)});
  if ((ck || {}).ten) q.set('bn', String(ck.ten).slice(0, 50));
  if (quayVe && /^https:\/\/[^/@?#]+\/[^?#]*$/.test(quayVe)) q.set('url', quayVe);
  return DL + '?' + q.toString();
}
