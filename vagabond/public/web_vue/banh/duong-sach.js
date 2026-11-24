/* v692 (anh Việt 24/11/2026): bỏ "/banh#" trong mọi link của trang đặt bánh.

   Trên tên miền khách (thevagabondpatisserie.com, www., order.) mỗi màn có
   đường sạch:  /  /dat-truoc  /tuyen-dung/<mã>  /banh/<bánh>  /gio-hang ...
   Máy chủ phát cùng một trang cho mọi đường này (ten_mien.la_duong_spa).

   Tên miền khác (tên miền thử của Frappe Cloud, trang xem trước của trình biên
   tập) vẫn dùng #/ như cũ, vì ở đó /tuyen-dung là màn app nội bộ.

   Link cũ đã gửi khách (/banh#/uu-dai, /banh?diem=..&ban=..#/in-store in trên QR
   bàn) vẫn mở được: lúc nạp trang, địa chỉ tự đổi sang đường sạch, giữ chuỗi
   hỏi (?ban=, ?utm_...).

   Mọi hàm ở đây THUẦN, nhận chuỗi, trả chuỗi, để kiểm không cần trình duyệt.
   Đường "màn" (route) luôn có dạng "/x/y", giống phần sau dấu # của bản cũ. */

export const MIEN_SACH = ['thevagabondpatisserie.com', 'www.thevagabondpatisserie.com', 'order.thevagabondpatisserie.com'];

export function laMienSach(host) {
  return MIEN_SACH.includes(String(host || '').toLowerCase());
}

/* Đường màn từ "#/x" hay "/x" (cả "#/" và "" là trang chủ "/"). */
export function chuanMan(h) {
  const s = String(h || '').replace(/^#/, '');
  return s && s !== '/' ? (s[0] === '/' ? s : '/' + s) : '/';
}

/* Màn đang mở. Đường sạch: đọc pathname, "/banh" cũ là trang chủ. Bản cũ: đọc hash. */
export function manHienTai(sach, pathname, hash) {
  if (!sach) return chuanMan(hash);
  const p = String(pathname || '/').replace(/\/+$/, '') || '/';
  return p === '/banh' ? '/' : p;
}

/* Địa chỉ đưa vào history cho màn h (dạng "#/x" hay "/x"). Bản cũ giữ đường trang
   hiện tại rồi gắn #/x như trước v692. */
export function diaChiMan(sach, h, pathname, search) {
  const m = chuanMan(h), q = String(search || '');
  if (sach) return m + q;
  return String(pathname || '') + q + (m === '/' ? '' : '#' + m);
}

/* Link cũ cần đổi khi nạp trang trên tên miền khách, hoặc '' nếu đã sạch.
   /banh#/x -> /x ; /banh -> / ; /<gì đó>#/x -> /x (link chia sẻ chép từ bản cũ). */
export function doiLinkCu(sach, pathname, hash, search) {
  if (!sach) return '';
  const h = String(hash || ''), q = String(search || '');
  if (/^#\//.test(h)) return chuanMan(h) + q;
  const p = String(pathname || '/').replace(/\/+$/, '');
  if (p === '/banh') return '/' + q;
  return '';
}

/* Thuộc tính href của thẻ <a> trỏ tới màn h: đường sạch thì "/x" (giữ chuột
   phải, "Sao chép liên kết" ra link sạch), nơi khác giữ "#/x" như cũ. */
export function hrefMan(sach, h) {
  return sach ? chuanMan(h) : '#' + chuanMan(h);
}

/* Link tuyệt đối để chia sẻ một màn, theo đúng kiểu đường đang dùng. */
export function linkChiaSe(sach, h, origin, pathname, search) {
  return String(origin || '') + diaChiMan(sach, h, pathname, search);
}
