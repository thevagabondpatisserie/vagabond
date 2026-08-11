/* Khoa xoa chung tu - phan tren Desk (anh Viet 11/08/2026)

Backend da chan cung bang hook on_trash, nen file nay khong phai lop bao ve
- no chi lo phan nguoi dung nhin thay: bo nut Xoa khoi menu cho do ai bam
vao roi an loi, va thay vao do nut Huy phieu cho ban nhap.

Viet mot lan cho MOI doctype trong danh sach, khong lam tung form: lam tung
form thi hom nao them loai chung tu moi lai quen mot cho. */

frappe.provide('vgb');

vgb.KHOA_XOA = [
  'Sales Invoice', 'POS Invoice', 'Purchase Invoice',
  'Payment Entry', 'Journal Entry',
  'Sales Order', 'Purchase Order',
  'Delivery Note', 'Purchase Receipt', 'Stock Entry', 'Stock Reconciliation'
];

vgb.bo_nut_xoa = function (frm) {
  // Menu duoc dung lai moi lan refresh nen phai go lai moi lan, khong the
  // go mot phat luc dau.
  try {
    var m = frm.page && frm.page.menu;
    if (!m) return;
    m.find('a.grey-link').each(function () {
      var t = ($(this).text() || '').trim();
      if (t === 'Delete' || t === 'Xoá' || t === 'Xóa') $(this).parent().remove();
    });
  } catch (e) { /* menu doi hinh thi thoi, backend van chan */ }
};

vgb.the_da_huy = function (frm) {
  if (!frm.doc.vgb_huy) return;
  var ly_do = frm.doc.vgb_huy_ly_do || 'không ghi lý do';
  var boi = frm.doc.vgb_huy_boi || '';
  frm.dashboard.clear_headline();
  frm.dashboard.set_headline(
    '<span style="color:#b42318"><b>Phiếu đã huỷ.</b> Lý do: ' +
    frappe.utils.escape_html(ly_do) +
    (boi ? ' — ' + frappe.utils.escape_html(boi) : '') +
    '</span>'
  );
  frm.page.set_indicator('Đã huỷ', 'red');
};

vgb.nut_huy = function (frm) {
  if (frm.doc.docstatus !== 0 || frm.is_new()) return;
  if (frm.doc.vgb_huy) {
    frm.add_custom_button('Gỡ dấu huỷ', function () {
      frappe.confirm('Gỡ dấu huỷ, phiếu này dùng lại bình thường?', function () {
        frappe.call({
          method: 'vagabond.chung_tu.bo_danh_dau_huy',
          args: { doctype: frm.doctype, name: frm.doc.name },
          freeze: true,
          callback: function () { frm.reload_doc(); }
        });
      });
    });
    return;
  }
  frm.add_custom_button('Huỷ phiếu', function () {
    var d = new frappe.ui.Dialog({
      title: 'Huỷ phiếu ' + frm.doc.name,
      fields: [
        {
          fieldtype: 'HTML',
          options:
            '<div style="color:#475467;line-height:1.6">Phiếu vẫn nằm nguyên trong hệ thống, ' +
            'chỉ được đánh dấu là đã huỷ và bị loại khỏi các số liệu. Không ai xoá được ' +
            'chứng từ khỏi hệ thống này.</div>'
        },
        { fieldtype: 'Small Text', fieldname: 'ly_do', label: 'Lý do huỷ', reqd: 1 }
      ],
      primary_action_label: 'Huỷ phiếu',
      primary_action: function (v) {
        d.hide();
        frappe.call({
          method: 'vagabond.chung_tu.huy_phieu_nhap',
          args: { doctype: frm.doctype, name: frm.doc.name, ly_do: v.ly_do },
          freeze: true,
          callback: function () { frm.reload_doc(); }
        });
      }
    });
    d.show();
  });
};

vgb.KHOA_XOA.forEach(function (dt) {
  frappe.ui.form.on(dt, {
    refresh: function (frm) {
      vgb.bo_nut_xoa(frm);
      vgb.the_da_huy(frm);
      vgb.nut_huy(frm);
    }
  });
});
