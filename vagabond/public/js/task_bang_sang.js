/* Form Task trên Desk, chỉ cho Task sinh từ màn Việc hôm nay (v516).
 *
 * Codex #356: ô "Lý do bỏ qua" là ô chỉ đọc, nên quản lý đổi trạng thái
 * sang Cancelled ngay trên Desk luôn bị máy chặn vì thiếu lý do. Nút này là
 * đường đúng: chọn lý do (lấy từ máy chủ, một nguồn LY_DO_BO_QUA) và số ngày
 * nhắc lại (kẹp theo luật), rồi gọi vagabond.phan_tich.bo_qua_viec. Máy chủ
 * vẫn soát lại quyền, lý do và ngày; nút chỉ là lối vào.
 */
frappe.ui.form.on('Task', {
  refresh: function (frm) {
    var d = frm.doc || {};
    if (frm.is_new() || !d.vgb_goi_y_khoa) return;
    if (['Open', 'Working', 'Pending Review', 'Overdue'].indexOf(d.status) < 0) return;
    frappe.call({
      method: 'vagabond.phan_tich.viec',
      args: { name: d.name },
      callback: function (r) {
        var v = (r && r.message) || {};
        if (v.quyen !== 'quan_ly') return;
        frm.add_custom_button('Bỏ qua việc này', function () { vgbBoQuaViec(frm, v); });
      }
    });
  }
});

function vgbBoQuaViec(frm, v) {
  var ly = v.ly_do_bo_qua || [];
  var toiDa = Number(v.bo_qua_toi_da) || 7;
  var ngay = [1, 3, 7, 14, 30].filter(function (n) { return n <= toiDa; });
  var d = new frappe.ui.Dialog({
    title: 'Bỏ qua việc này',
    fields: [
      { fieldname: 'ly_do', fieldtype: 'Select', label: 'Lý do', reqd: 1,
        options: [''].concat(ly.map(function (x) { return x.ten; })).join('\n') },
      { fieldname: 'so_ngay', fieldtype: 'Select', label: 'Nhắc lại sau', reqd: 1,
        options: ngay.map(function (n) { return n + ' ngày'; }).join('\n'), default: ngay[ngay.length - 1] + ' ngày',
        description: 'Tới ngày đó nhận định hiện lại ở Cần giao nếu số vẫn vượt ngưỡng.' }
    ],
    primary_action_label: 'Bỏ qua',
    primary_action: function (val) {
      var k = (ly.filter(function (x) { return x.ten === val.ly_do; })[0] || {}).k;
      if (!k) return frappe.msgprint('Chọn một lý do trong danh sách.');
      frappe.call({
        method: 'vagabond.phan_tich.bo_qua_viec',
        args: { name: frm.doc.name, ly_do: k, so_ngay: parseInt(val.so_ngay, 10) || 1 },
        freeze: true,
        callback: function () {
          d.hide();
          frappe.show_alert({ message: 'Đã bỏ qua việc này', indicator: 'orange' });
          frm.reload_doc();
        }
      });
    }
  });
  d.show();
}
