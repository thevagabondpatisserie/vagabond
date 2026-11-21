/* Danh sách màn máy chụp mở được. Mỗi màn: tên, cách mở, và đã chuyển sang giao diện
 * mới hay chưa (chua_chuyen: true thì khi bật chỉ ghi "Chưa chuyển", không chấm chuẩn mới). */
'use strict';
module.exports = [
  { ten: 'trang-chu', cho: '.gwrap' },
  { ten: 'dang-nhap', cho: '#vgb .lgw', du_lieu: { 'frappe.auth.get_logged_user': { message: 'Guest' } } },
  { ten: 'tai-khoan', cho: '.gwrap', mo: async function (t) { await t.click('#vgbAcc'); await t.waitForSelector('#acOut'); } },
  { ten: 'nhom-ban-hang', cho: '.gwrap', mo: async function (t) { await t.click('.gt[data-nhom="BH"]'); await t.waitForSelector('#vgbBack'); } },
  { ten: 'hop-xac-nhan', cho: '.gwrap', mo: async function (t) { await t.click('#vgbAcc'); await t.waitForSelector('#acOut'); await t.click('#acOut'); await t.waitForSelector('.sh [data-y]'); } },
  { ten: 'nhom-khach-hang', cho: '.gwrap', mo: async function (t) { await t.click('.gt[data-nhom="KHG"]'); await t.waitForSelector('#vgbBack'); } },
  { ten: 'viec-can-lam', cho: '.gwrap', chua_chuyen: true, mo: async function (t) { await t.click('.gt.vcl'); await t.waitForSelector('#vgbBack'); await t.waitForTimeout(300); } },
  { ten: 'tim-nghiep-vu', cho: '.gwrap', mo: async function (t) { await t.fill('.vgbtim', 'công nợ'); await t.waitForSelector('#vgbKQ .hub'); } },
  { ten: 'ghim-da-co', cho: '.vgbgo', du_lieu: { 'vagabond.ghim.lay': { message: { ghim: ['POS', 'VD', 'KK', 'CN'] } } } },
  { ten: 'so-tay', cho: '.gwrap', chua_chuyen: true, mo: async function (t) { await t.click('.gt[data-nhom="SOTAY"]'); await t.waitForSelector('#vgbBack'); await t.waitForTimeout(300); } },
  /* Đầu trang đủ bốn nút với tiêu đề dài: ca khó của điện thoại hẹp (bản 4 mục 4). Thân màn thuộc PR 5. */
  { ten: 'dau-trang-bon-nut', cho: '.gwrap', chua_chuyen: true, mo: async function (t) {
    await t.click('.gt[data-nhom="KHAC"]'); await t.waitForSelector('[data-go="CDTDH"]'); await t.click('[data-go="CDTDH"]'); await t.waitForSelector('#vgbAct'); await t.waitForTimeout(300); } },
  /* Màn thuộc PR 2, chưa chuyển: máy chụp vẫn mở để lấy đường chuẩn và bắt lỗi do nền chung gây ra. */
  { ten: 'tinh-tien-chon-quay', cho: '.gwrap', chua_chuyen: true, mo: async function (t) {
    await t.click('.gt[data-nhom="BH"]'); await t.waitForSelector('[data-go="POS"]'); await t.click('[data-go="POS"]'); await t.waitForTimeout(500); } },
  { ten: 'nhom-ke-toan', cho: '.gwrap', mo: async function (t) { await t.click('.gt[data-nhom="KT"]'); await t.waitForSelector('#vgbBack'); } },
  /* Codex UI04, UI05 (21/11): hộp chọn ghim mở từ trang chủ chưa ghim gì. Kiểm cả bàn phím: hộp là
     dialog có tên, focus vào khung hộp, Escape đóng đúng hộp đó và trả focus về nút đã mở. */
  { ten: 'chon-ghim', cho: '.vgbgthemn', du_lieu: { 'vagabond.ghim.lay': { message: { ghim: [] } } },
    mo: async function (t) { await t.click('.vgbgthemn'); await t.waitForSelector('.sh [data-hc]'); },
    /* Phép kiểm bàn phím không phụ thuộc giao diện: chạy ở chế độ bật. Chế độ tắt chỉ chụp để so
       điểm ảnh với main (main chưa có Escape, chạy ở đó là chặn luôn lượt chụp gốc). */
    kiem: async function (t, bat) {
      var loi = [];
      if (!bat) return loi;
      var d = await t.evaluate(function () {
        var ov = document.querySelectorAll('.sh'); ov = ov[ov.length - 1];
        return { role: ov && ov.getAttribute('role'), ten: ov && ov.getAttribute('aria-label'),
          trong: !!(ov && ov.contains(document.activeElement)) };
      });
      if (d.role !== 'dialog' || !d.ten) loi.push('hộp chọn ghim không phải dialog có tên (role ' + d.role + ', tên ' + d.ten + ')');
      if (!d.trong) loi.push('mở hộp mà focus không vào hộp');
      await t.keyboard.press('Escape');
      await t.waitForTimeout(150);
      var s = await t.evaluate(function () {
        var a = document.activeElement;
        return { con: document.querySelectorAll('.sh').length, mo: !!(a && a.classList && a.classList.contains('vgbgthemn')) };
      });
      if (s.con) {
        loi.push('Escape không đóng hộp chọn ghim');
        await t.click('.sh .x');
        await t.waitForTimeout(150);
      }
      if (!s.mo) loi.push('đóng hộp mà focus không về nút "Chọn ô để ghim"');
      /* Mở lại để chụp và đo đúng hộp. */
      await t.click('.vgbgthemn'); await t.waitForSelector('.sh [data-hc]');
      return loi;
    } },
  /* Codex UI05: Trợ lý, nút đóng phải 44 và đọc "Đóng". Không gửi câu hỏi. */
  { ten: 'tro-ly', cho: '.gwrap', mo: async function (t) {
    /* Giao diện mới mở bằng nút đầu trang, giao diện cũ bằng nút nổi. */
    await t.click((await t.$('#vgbTl')) ? '#vgbTl' : '#tlNut'); await t.waitForSelector('#tlDong', { state: 'visible' }); },
    kiem: async function (t, bat) {
      if (!bat) return [];
      var d = await t.evaluate(function () { var b = document.getElementById('tlDong'); return b && b.getAttribute('aria-label'); });
      return d === 'Đóng' ? [] : ['nút đóng Trợ lý đọc "' + d + '", phải là "Đóng"'];
    } },
  /* Codex UI03: thanh đáy chung. Dựng lại ĐÚNG markup thanh đáy của Tính tiền (09-tinh-tien-quay.js)
     và Đối soát nhà cung cấp (52-doi-soat-vendor.js) trên trang chủ, để đo lớp vẽ chung của .vf mà
     không cần dữ liệu quầy. Đây là phép thử thành phần, không thay kịch bản màn Tính tiền (PR 2). */
  { ten: 'thanh-day', cho: '.gwrap', pham_vi: '#thuVf', mo: async function (t) {
    await t.evaluate(function () {
      var mau = [
        '<div style="display:flex;gap:8px"><button class="btn gh" style="flex:0 0 34%;margin:0">🖨 Tạm tính</button><button class="btn" style="flex:1;margin:0">💰 Thu tiền 0 đ</button></div>',
        '<div style="display:flex;gap:8px"><button class="btn gh" style="flex:0 0 34%;margin:0">🖨 Tạm tính</button><button class="btn" style="flex:1;margin:0">💰 Thu tiền 12.345.000 đ</button></div>',
        '<div style="display:flex;gap:8px"><button class="btn" style="margin:0;flex:1">Đọc hộp thư ngay</button><button class="btn gh" style="margin:0;flex:1">↑ Tải file (cần duyệt)</button></div>',
        '<button class="btn" style="margin:0">Lưu phiếu</button>'
      ];
      var w = document.createElement('div');
      w.id = 'thuVf';
      w.setAttribute('style', 'position:fixed;left:0;right:0;bottom:0;z-index:50');
      w.innerHTML = mau.map(function (m) { return '<div class="vf">' + m + '</div>'; }).join('');
      document.body.appendChild(w);
    });
    await t.waitForTimeout(100); } },
  /* Codex UI02: số trên ô nhóm 0, 9, 99, 999, 1.339 và số dài hơn, ô Việc cần làm 99+. Gắn số vào
     đúng thẻ số của trang chủ rồi để lớp vẽ tự xếp, như khi số đếm từ máy chủ về. */
  { ten: 'so-tren-o', cho: '.gwrap', mo: async function (t) {
    await t.evaluate(function () {
      var so = { DH: '9', SX: '1339', NK: '99', XK: '999', KK: '12345', BH: '0', KHG: '1234567', GH: '99999' };
      Object.keys(so).forEach(function (k) {
        var o = document.querySelector('.gt[data-nhom="' + k + '"]');
        if (!o) return;
        var gb = o.querySelector('.gb');
        if (!gb) { gb = document.createElement('span'); gb.className = 'gb'; o.insertBefore(gb, o.firstChild); }
        gb.textContent = so[k];
      });
      var v = document.getElementById('vgbSoVCL');
      if (v) { v.textContent = '99+'; v.style.display = ''; }
    });
    await t.waitForTimeout(200); } }
];
