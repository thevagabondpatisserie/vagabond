/* Form Nha cung cap tren Desk: tai khoan nhan tien (v515, 21/09/2026).
 *
 * Vi sao: anh Viet chup form Desk, tab Ket noi co the "Tai khoan ngan hang"
 * nhung khong co nut them, cung khong o nao nhap so tai khoan. Uyen can
 * so tai khoan de phieu chi, phieu tra truoc in ra cho ke toan chuyen.
 *
 * Ghi qua DUNG MOT cong vagabond.ncc.luu_tai_khoan nhu app, de giu luat da
 * chot o v509: tai khoan da co phieu chi tro toi thi khong sua de, may tao
 * ban moi lam mac dinh. Khong tu tao Bank Account o day.
 */
frappe.ui.form.on('Supplier', {
  refresh: function (frm) {
    if (frm.is_new()) return;
    frappe.call({
      method: 'vagabond.ncc.tai_khoan',
      args: { ncc: frm.doc.name },
      callback: function (r) {
        var tk = (r && r.message) || {};
        var dong = tk.so_tk
          ? 'Tài khoản nhận tiền: <b>' + frappe.utils.escape_html(tk.so_tk) + '</b>' +
            (tk.ngan_hang ? ' · ' + frappe.utils.escape_html(tk.ngan_hang) : '') +
            (tk.chu_tk ? ' · ' + frappe.utils.escape_html(tk.chu_tk) : '')
          : 'Chưa có tài khoản nhận tiền. Phiếu chi cho nhà này in ra sẽ trống phần số tài khoản.';
        frm.dashboard.set_headline_alert(dong, tk.so_tk ? 'blue' : 'orange');
        if (!tk.sua) return;
        frm.add_custom_button(tk.so_tk ? 'Sửa tài khoản nhận tiền' : 'Thêm tài khoản nhận tiền', function () {
          vgbNccTkDialog(frm, tk);
        });
      }
    });
  }
});

function vgbNccTkDialog(frm, tk) {
  var d = new frappe.ui.Dialog({
    title: tk.so_tk ? 'Sửa tài khoản nhận tiền' : 'Thêm tài khoản nhận tiền',
    fields: [
      { fieldname: 'chu_tk', fieldtype: 'Data', label: 'Chủ tài khoản', default: tk.chu_tk || '',
        description: 'Để trống thì lấy tên nhà cung cấp.' },
      { fieldname: 'so_tk', fieldtype: 'Data', label: 'Số tài khoản', reqd: 1, default: tk.so_tk || '' },
      { fieldname: 'ngan_hang', fieldtype: 'Link', options: 'Bank', label: 'Ngân hàng', reqd: 1, default: tk.ngan_hang || '' }
    ],
    primary_action_label: 'Lưu tài khoản',
    primary_action: function (v) {
      frappe.call({
        method: 'vagabond.ncc.luu_tai_khoan',
        args: { ncc: frm.doc.name, so_tk: v.so_tk, ngan_hang: v.ngan_hang, chu_tk: v.chu_tk || '' },
        freeze: true,
        callback: function () {
          d.hide();
          frappe.show_alert({ message: 'Đã lưu tài khoản nhận tiền', indicator: 'green' });
          frm.reload_doc();
        }
      });
    }
  });
  d.show();
}
