/* Phép chấm THUẦN của máy chụp: nhận số đo lấy từ trang, trả danh sách lỗi. Tách riêng để kiểm
 * được bằng node không cần trình duyệt (Codex #599: phép kiểm phải chứng minh được nó biết đỏ). */
'use strict';

var PHONG_CHUAN = ['Be Vietnam Pro', 'Doto'];

/* dung: [{ho, dam}] phông và độ đậm chữ trên màn đang KHAI.
 * mat:  [{ho, dam, trang_thai}] các mặt phông của trang (document.fonts), trang_thai là
 *       'loaded', 'unloaded', 'loading' hoặc 'error'.
 * Tên phông khai trong CSS không chứng minh trình duyệt vẽ bằng phông đó: tệp phông hỏng thì
 * trình duyệt lặng lẽ vẽ bằng phông hệ thống. Nên mỗi cặp (họ, độ đậm) đang dùng phải có một
 * mặt phông ĐÃ TẢI XONG, và không mặt nào ở trạng thái lỗi. */
function danhGiaPhong(dung, mat) {
  var loi = [];
  var la = {};
  (dung || []).forEach(function (d) { if (PHONG_CHUAN.indexOf(d.ho) < 0) la[d.ho] = 1; });
  if (Object.keys(la).length) loi.push('phông lạ: ' + Object.keys(la).join(', '));
  var hong = (mat || []).filter(function (m) { return m.trang_thai === 'error'; });
  if (hong.length) loi.push('tệp phông tải lỗi: ' + hong.map(function (m) { return m.ho + ' ' + m.dam; }).join(', '));
  var thieu = {};
  (dung || []).forEach(function (d) {
    if (PHONG_CHUAN.indexOf(d.ho) < 0) return;
    var co = (mat || []).some(function (m) { return m.ho === d.ho && String(m.dam) === String(d.dam) && m.trang_thai === 'loaded'; });
    if (!co) thieu[d.ho + ' ' + d.dam] = 1;
  });
  if (Object.keys(thieu).length) loi.push('phông chưa tải được nên chữ đang vẽ bằng phông khác: ' + Object.keys(thieu).join(', '));
  if (!(dung || []).length) loi.push('không đo được phông nào: màn không có chữ hoặc phép đo hỏng');
  return loi;
}

/* taiHong: [{duong, ma}] tài nguyên của app (/assets/vagabond/...) tải không được. */
function danhGiaTaiNguyen(taiHong) {
  return (taiHong || []).length ? ['tài nguyên tải hỏng: ' + taiHong.slice(0, 4).map(function (t) { return t.duong + ' (' + t.ma + ')'; }).join('; ')] : [];
}

/* Lớp vẽ đã gắn đủ chưa (Codex #600). soThe: số thẻ style#vgbUiB; css: nội dung của nó;
 * nhomDom: các mã nhóm đang có trên màn (data-nhom, data-uinhom). Phải đúng một thẻ, có bảng
 * biến chung, và mỗi nhóm đang hiện phải có luật màu riêng: nạp sai thứ tự thì bảng kiểu vẫn
 * có nhưng mất phần sinh từ dữ liệu, mắt thường chỉ thấy nhóm nào cũng một màu. */
function danhGiaLopVe(soThe, css, nhomDom) {
  var loi = [];
  if (soThe !== 1) loi.push('số bảng kiểu giao diện mới là ' + soThe + ', phải đúng 1');
  if (soThe >= 1 && String(css || '').indexOf('html.ui-b{') < 0) loi.push('bảng kiểu thiếu bảng biến chung');
  /* Hai ô đặc biệt của trang chủ có kiểu riêng, không dùng màu nhóm: Việc cần làm (thẻ
     Midnight) và Sổ tay. */
  var RIENG = ['VCL', 'SOTAY'];
  var thieu = (nhomDom || []).filter(function (k) { return RIENG.indexOf(k) < 0 &&  String(css || '').indexOf('[data-uinhom="' + k + '"]') < 0; });
  if (soThe >= 1 && thieu.length) loi.push('bảng kiểu thiếu màu của nhóm: ' + thieu.join(', '));
  return loi;
}

module.exports = { danhGiaPhong: danhGiaPhong, danhGiaTaiNguyen: danhGiaTaiNguyen, danhGiaLopVe: danhGiaLopVe, PHONG_CHUAN: PHONG_CHUAN };
