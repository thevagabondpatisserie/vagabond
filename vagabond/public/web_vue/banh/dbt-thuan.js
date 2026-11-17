/* v667 (anh Việt duyệt 17/11/2026): phép THUẦN của tab "Đặc biệt tuần này".
   Luật trùng dac_biet_tuan.py ở máy chủ (máy chủ chặn lại khi gửi đơn).
   Mọi giờ là giờ Việt Nam, chuỗi "YYYY-MM-DDTHH:MM" so theo thứ tự chữ.
   Không import gì để chạy được trong ca kiểm node. */

/* Giờ Việt Nam của một thời điểm, không phụ thuộc múi giờ của máy khách. */
export function lucVN(d) {
  const p = {};
  new Intl.DateTimeFormat('en-GB', {timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23'}).formatToParts(d || new Date()).forEach(x => { p[x.type] = x.value; });
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
}
/* Cùng khoá bánh của thẻ Bánh (banh_web.khoa_banh): chữ thường, gọn khoảng trắng. */
export const khoaBanh = ten => String(ten || '').normalize('NFC').toLowerCase().split(/\s+/).filter(Boolean).join(' ').slice(0, 140);

/* Đợt khách đang thấy: mục đầu tiên đang bật, trong khoảng ngày hiện. */
export function dotDangHien(khoi, homNay) {
  return (khoi || []).find(k => k && k.loai === 'dac_biet_tuan' && k.hien === true
    && !(k.bat_dau && k.bat_dau > homNay) && !(k.ket_thuc && k.ket_thuc < homNay)) || null;
}
export function trangThaiDot(k, luc) {
  if (luc < (k.mo_don || '')) return 'chua_mo';
  if (luc >= (k.chot_don || '')) return 'da_chot';
  return 'mo';
}
/* Mốc đang diễn ra: mốc cuối cùng đã tới giờ bắt đầu; chưa tới mốc nào thì -1. */
export function mocHienTai(k, luc) {
  let i = -1;
  (k.moc || []).forEach((m, j) => { if (m.luc && m.luc <= luc) i = j; });
  return i;
}
const msCua = s => { const m = String(s || '').match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/); return m ? Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]) : NaN; };
/* Đếm ngược tới giờ chốt đơn: từ 24 giờ trở lên đếm số ngày trọn (3 ngày 5 giờ
   là "3 ngày"), dưới 24 giờ đếm theo giờ làm tròn lên (40 phút là "1 giờ").
   Đã chốt hoặc thiếu giờ thì null. */
export function demNguoc(k, luc) {
  const con = msCua(k.chot_don) - msCua(luc);
  if (!(con > 0)) return null;
  const GIO = 3600000;
  return con >= 24 * GIO ? {so: Math.floor(con / (24 * GIO)), don_vi: 'ngay'} : {so: Math.ceil(con / GIO), don_vi: 'gio'};
}
/* Mốc mở đơn để ghi "MỞ ĐƠN T2 16/11": mốc có đúng giờ mở đơn, không có thì mốc đầu. */
export function mocMoDon(k) {
  const ds = k.moc || [];
  return ds.find(m => m.luc === k.mo_don) || ds[0] || null;
}
/* {khoa: Set(mã size)} theo danh mục bánh đang có trên trang. */
export function maTheoKhoa(dot, cakes) {
  const ra = {};
  ((dot && dot.mon_dt) || []).forEach(m => {
    const c = (cakes || []).find(x => khoaBanh(x.k) === m.khoa);
    if (c) ra[m.khoa] = new Set(c.sizes.map(s => s.id));
  });
  return ra;
}
export function khoaCuaMa(maKhoa, id) {
  return Object.keys(maKhoa || {}).find(k => maKhoa[k].has(id)) || '';
}
/* Giỏ có món của đợt không. */
export function gioCoMonDot(cart, maKhoa) {
  return (cart || []).some(o => !!khoaCuaMa(maKhoa, o.id));
}
/* Ngày iso có bị khoá vì giỏ có món của đợt mà ngày đó không phải ngày giao. */
export function ngayBiKhoa(dot, cart, maKhoa, iso) {
  return !!dot && gioCoMonDot(cart, maKhoa) && !(dot.ngay_giao || []).includes(iso);
}
/* Số còn nhận của một món có số lượng tối đa (null: không giới hạn). */
export function conSuat(m, daDat, trongGio) {
  if (!m || !m.toi_da) return null;
  return Math.max(0, parseInt(m.toi_da, 10) - (Number((daDat || {})[m.khoa]) || 0) - (Number(trongGio) || 0));
}
/* Trạng thái nút của một món: mo, chua_mo, da_chot (gồm hết suất). */
export function trangThaiMon(dot, m, luc, daDat) {
  const tt = trangThaiDot(dot, luc);
  if (tt !== 'mo') return tt;
  const con = conSuat(m, daDat, 0);
  return con !== null && con <= 0 ? 'da_chot' : 'mo';
}
