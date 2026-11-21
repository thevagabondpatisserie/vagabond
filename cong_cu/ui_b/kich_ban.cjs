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
    await t.waitForTimeout(200); } },
  /* Codex #604: biểu tượng lớp vẽ chèn vào nút không được đổi đích cú bấm. Dựng hộp giống
     mfgSheetHoanTat (05-san-xuat.js): hàm bấm kiểm THẲNG e.target.hasAttribute('data-y'). Bấm
     đúng vào biểu tượng rồi vào chữ, cả hai phải chạy hành động. */
  { ten: 'bam-bieu-tuong', cho: '.gwrap', pham_vi: '#thuBam', mo: async function (t) {
    await t.evaluate(function () {
      window.__bam = 0;
      var ov = document.createElement('div'); ov.className = 'sh'; ov.id = 'thuBam';
      ov.innerHTML = '<div class="shb" style="padding:18px 16px"><div style="font-weight:700;margin-bottom:8px">Hoàn tất lệnh</div>' +
        '<button class="btn gr" data-y>✅ Hoàn tất</button></div>';
      ov.onclick = function (e) { if (e.target.hasAttribute('data-y')) window.__bam++; };
      document.body.appendChild(ov);
    });
    await t.waitForTimeout(150); },
    kiem: async function (t, bat) {
      var loi = [];
      var bt = await t.evaluate(function () {
        var b = document.querySelector('#thuBam [data-y]'), ic = b.querySelector('.uidau'), rb = b.getBoundingClientRect();
        var ri = ic ? ic.getBoundingClientRect() : null;
        return { coIc: !!ic, ix: ri ? ri.left + ri.width / 2 : rb.left + 30, iy: ri ? ri.top + ri.height / 2 : rb.top + rb.height / 2, cx: rb.right - 20, cy: rb.top + rb.height / 2 };
      });
      if (bat && !bt.coIc) loi.push('emoji đầu nút chưa đổi thành biểu tượng');
      await t.mouse.click(bt.ix, bt.iy);
      var n1 = await t.evaluate(function () { return window.__bam; });
      await t.mouse.click(bt.cx, bt.cy);
      var n2 = await t.evaluate(function () { return window.__bam; });
      if (n1 !== 1) loi.push('bấm vào biểu tượng của nút không chạy hành động (đếm ' + n1 + ')');
      if (n2 !== 2) loi.push('bấm vào chữ của nút không chạy hành động (đếm ' + n2 + ')');
      return loi;
    } },
  /* Codex #604: phần tử vai trò nút có xử lý phím RIÊNG (như tiêu đề dài của đầu trang ui-b,
     uiBDauTrang ở 81-ui-b.js) thì bộ phím chung của hộp không được bấm hộ thêm. Dựng lại đúng
     cách uiBDauTrang gắn: role=button, tabindex, aria-expanded, onclick và onkeydown cùng đổi. */
  { ten: 'phim-rieng', cho: '.gwrap', pham_vi: '#thuPhim', mo: async function (t) {
    await t.evaluate(function () {
      var w = document.createElement('div'); w.id = 'thuPhim';
      w.setAttribute('style', 'position:fixed;left:12px;right:12px;top:120px;z-index:60;background:#fff;padding:12px');
      w.innerHTML = '<b role="button" tabindex="0" aria-expanded="false" style="display:block;min-height:44px;font-size:17px">Tiêu đề dài bấm để mở</b>';
      var b = w.querySelector('b');
      var doi = function () { var mo = b.classList.toggle('mo'); b.setAttribute('aria-expanded', mo ? 'true' : 'false'); };
      b.onclick = doi;
      b.onkeydown = function (e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); doi(); } };
      document.body.appendChild(w);
    }); },
    kiem: async function (t) {
      await t.focus('#thuPhim b');
      await t.keyboard.press('Enter');
      var a1 = await t.getAttribute('#thuPhim b', 'aria-expanded');
      await t.keyboard.press('Enter');
      var a2 = await t.getAttribute('#thuPhim b', 'aria-expanded');
      return (a1 === 'true' && a2 === 'false') ? [] : ['Enter trên nút có phím riêng: lần 1 ' + a1 + ', lần 2 ' + a2 + ' (phải true rồi false)'];
    } }
];
