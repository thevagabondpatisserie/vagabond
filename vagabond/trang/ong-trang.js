/* =============================================================
   ÔNG TRĂNG XUỐNG CHƠI — dán vào ô "Script" của Web Page
   (Frappe: Trang web → mở trang → phần Script, nhớ TICK "Add Script")

   ⚠ SỬA KHỐI CẤU HÌNH NGAY BÊN DƯỚI TRƯỚC KHI PHÁT HÀNH.
   ============================================================= */

(function () {
  "use strict";

  /* ==========================================================
     CẤU HÌNH — chỉ sửa ở đây
     ========================================================== */
  var CH = {

    // Số hotline hiện trên header và chân trang.
    hotline: 'DIEN_VAO_DAY',

    // Đường dẫn Web Form nhận đăng ký.
    // Tạo theo hướng dẫn ở HUONG-DAN-DUA-LEN-FRAPPE.md, mục 3.
    // Tham số ?goi= để form biết khách chọn gói nào.
    form: '/dang-ky-ong-trang',

    // Ba gói vé. so_cho chính là số chỗ bị trừ khỏi 40.
    goi_ve: [
      { ma: 'le',     ten: 'Vé lẻ',   so_cho: 1, gia: 550000,  mo_ta: '1 khách' },
      { ma: 'combo2', ten: 'Combo 2', so_cho: 2, gia: 1000000, mo_ta: '2 khách · tiết kiệm 100.000đ' },
      { ma: 'combo4', ten: 'Combo 4', so_cho: 4, gia: 1800000, mo_ta: '4 khách · tiết kiệm 400.000đ', tot_nhat: true }
    ],

    // Tổng số chỗ. Chỉ dùng để hiển thị.
    suc_chua: 40
  };

  /* ========================================================== */

  function $(id) { return document.getElementById(id); }
  function tien(n) { return new Intl.NumberFormat('vi-VN').format(n) + 'đ'; }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[<>&"]/g, function (c) {
      return { '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;' }[c];
    });
  }

  function dung() {
    if (!$('otcGoi')) return;   // không phải trang này thì thôi

    /* ---- cảnh báo khi chưa cấu hình xong ---- */
    if (/^DIEN_VAO_DAY/.test(CH.hotline)) {
      $('otcWarn').innerHTML =
        '<div class="otc--warn"><b>⚠ Trang chưa sẵn sàng để gửi khách.</b> ' +
        'Còn thiếu số hotline trong ô <code>Script</code> của Web Page. ' +
        'Dải này tự biến mất khi điền xong.</div>';
    }

    /* ---- hotline ---- */
    $('otcHotline').textContent = CH.hotline;
    $('otcTel').href = 'tel:' + String(CH.hotline).replace(/\s/g, '');

    /* ---- ba gói vé ----
       Mỗi gói dẫn sang Web Form, mang theo mã gói và số chỗ.
       Web Form đọc hai tham số này để điền sẵn, khách khỏi chọn lại. */
    $('otcGoi').innerHTML = CH.goi_ve.map(function (g) {
      var url = CH.form
              + '/new?goi=' + encodeURIComponent(g.ma)
              + '&so_cho='  + encodeURIComponent(g.so_cho);
      return '<a href="' + url + '" class="' + (g.tot_nhat ? 'tot' : '') + '"'
           + ' data-cho="' + g.so_cho + '">'
           + (g.tot_nhat ? '<span class="otc--nhan">Tiết kiệm nhất</span>' : '')
           + '<span class="i"><b>' + esc(g.ten) + '</b><span>' + esc(g.mo_ta) + '</span></span>'
           + '<span class="g">' + tien(g.gia) + '</span>'
           + '<span class="mui">→</span></a>';
    }).join('');

    /* ---- hỏi Frappe còn bao nhiêu chỗ ----
       Gọi hàm đếm ở phía máy chủ. Chưa dựng hàm đó thì bỏ qua trong im lặng —
       thà không hiện số còn hơn hiện số sai. */
    if (window.frappe && frappe.call) {
      frappe.call({
        method: 'frappe.client.get_count',
        args: {
          doctype: 'Dang Ky Su Kien',
          filters: [
            ['su_kien', '=', 'Ông Trăng Xuống Chơi'],
            ['trang_thai', 'in', ['Đã thanh toán', 'Chờ thanh toán']]
          ]
        },
        callback: function () { /* xem ghi chú bên dưới */ }
      });
    }
  }

  /* Frappe nạp Script của Web Page trước khi thân trang dựng xong,
     nên phải đợi DOM sẵn sàng. */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', dung);
  } else {
    dung();
  }
})();

/* =============================================================
   GHI CHÚ VỀ SỐ CHỖ CÒN LẠI

   frappe.client.get_count chỉ đếm được SỐ BẢN GHI, không cộng được
   cột số chỗ. Mà ta cần tổng SỐ CHỖ (một đơn Combo 4 là 4 chỗ).

   Hai cách, chọn một:

   A. Cách không cần code (khuyên dùng lúc đầu)
      Bỏ hẳn phần hiển thị số chỗ còn lại. Nhân viên xem trong Desk,
      sắp hết thì tự đóng Web Form lại. Với 40 vé bán trong 2 tuần thì
      cách này đủ, và không có gì để hỏng.

   B. Cách chính xác theo thời gian thực
      Cần một Server Script loại API trả về tổng số chỗ đã bán.
      Xem HUONG-DAN-DUA-LEN-FRAPPE.md mục 6. Chỉ nên làm sau khi
      bản đơn giản đã chạy ổn.
   ============================================================= */
