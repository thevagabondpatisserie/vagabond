/* MỘT cửa gọi máy chủ cho web bản Vue.

   - GET cho các phép đọc công khai (tồn bánh, cấu hình, phí giao...).
   - POST kèm mã CSRF: khách vãng lai là Guest nên Frappe miễn, nhưng nhân
     viên đang đăng nhập mà mở trang thì PHẢI có, thiếu là 400 (bài học cũ).
     Mã lấy từ thẻ meta do get_context đặt, rồi mới tới frappe.csrf_token.
   - Đang ở khung xem thử của trình biên tập thì KHÔNG gửi gì có ghi: không
     gửi đơn, không giữ lượt ưu đãi (thay xem-thu.js của trang cũ). */
import {ND} from './chu.js';

function maCsrf(doc = document, win = window) {
  const m = doc.querySelector && doc.querySelector('meta[name="csrf-token"]');
  const v = m && m.getAttribute('content');
  if (v && v !== 'None' && !/\{\{/.test(v)) return v;
  const tk = win.csrf_token || (win.frappe && win.frappe.csrf_token);
  return tk && tk !== 'None' ? tk : '';
}

export async function doc(phuong, thamSo) {
  const q = thamSo ? '?' + new URLSearchParams(thamSo).toString() : '';
  const r = await fetch('/api/method/' + phuong + q, {headers: {Accept: 'application/json'}, credentials: 'same-origin'});
  if (!r.ok) throw new Error('HTTP ' + r.status);
  const j = await r.json();
  return j && Object.prototype.hasOwnProperty.call(j, 'message') ? j.message : j;
}

export async function ghi(phuong, than, {choXemThu = false} = {}) {
  if (ND.xemThu && !choXemThu) throw new Error('Bản xem trước không gửi đơn hay lưu dữ liệu.');
  const head = {'Content-Type': 'application/json', Accept: 'application/json'};
  const tk = maCsrf();
  if (tk) head['X-Frappe-CSRF-Token'] = tk;
  const r = await fetch('/api/method/' + phuong, {method: 'POST', headers: head, credentials: 'same-origin', body: JSON.stringify(than || {})});
  const j = await r.json();
  return j && Object.prototype.hasOwnProperty.call(j, 'message') ? j.message : j;
}
