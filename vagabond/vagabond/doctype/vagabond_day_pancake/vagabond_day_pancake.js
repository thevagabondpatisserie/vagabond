frappe.ui.form.on('Vagabond Day Pancake', {
  refresh(frm) {
    if (!['System Manager', 'Giám đốc', 'AP Giám đốc'].some(r => frappe.user_roles.includes(r))) return;
    if (!['chua_ro', 'dang_gui', 'da_tao', 'da_co', 'xung_dot'].includes(frm.doc.trang_thai)) return;
    frm.add_custom_button('Đối soát và mở lại', () => {
      const d = new frappe.ui.Dialog({
        title: 'Đối soát với Pancake trước khi mở lại',
        fields: [
          {fieldtype: 'HTML', options: '<p>Chỉ mở lại khi đã có bằng chứng Pancake không tạo mã hoặc đã xóa mã và không còn xử lý yêu cầu cũ. Tìm kiếm rỗng chưa đủ. Mở sai có thể tạo trùng mã.</p>'},
          {fieldname: 'ly_do', label: 'Lý do mở lại', fieldtype: 'Small Text', reqd: 1},
          {fieldname: 'bang_chung', label: 'Bằng chứng hoặc mã hỗ trợ từ Pancake', fieldtype: 'Small Text', reqd: 1},
          {fieldname: 'xac_nhan_chua_tao', label: 'Tôi đã xác minh Pancake không còn mã và không còn xử lý yêu cầu cũ', fieldtype: 'Check', reqd: 1}
        ],
        primary_action_label: 'Lưu đối soát và mở lại',
        async primary_action(values) {
          await frappe.call({method: 'vagabond.pancake_sp.doi_soat_luot', args: {ten: frm.doc.name, ...values}, freeze: true});
          d.hide(); await frm.reload_doc();
        }
      });
      d.show();
    });
  }
});
