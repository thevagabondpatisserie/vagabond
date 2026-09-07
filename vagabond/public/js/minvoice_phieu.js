// #227: kết quả gửi không rõ phải được đối chiếu, có vết, trước khi gửi lại.
frappe.ui.form.on('Sales Invoice', {
	refresh: function (frm) {
		if (!frm.doc.vgb_hddt_cho_doi_chieu) return;
		frm.set_intro('Lần gửi HĐĐT chưa có kết quả chắc chắn. Kiểm M-Invoice theo mã phiếu ' + frm.doc.name + ' trước khi gửi lại.', 'orange');
		if (!['System Manager', 'Accounts Manager', 'Giám đốc', 'AP Giám đốc'].some(function (vai) { return frappe.user.has_role(vai); })) return;
		frm.add_custom_button('Đối chiếu và mở lại gửi HĐĐT', function () {
			frappe.prompt([
				{fieldname: 'da_doi_chieu', label: 'Đã kiểm M-Invoice theo mã phiếu và xác nhận CHƯA có hoá đơn', fieldtype: 'Check', reqd: 1},
				{fieldname: 'ly_do', label: 'Kết quả đối chiếu, người kiểm và thời điểm', fieldtype: 'Small Text', reqd: 1}
			], function (gia_tri) {
				frappe.call({method: 'vagabond.minvoice_an_toan.mo_lai', args: {
					phieu: frm.doc.name, ly_do: gia_tri.ly_do, da_doi_chieu: gia_tri.da_doi_chieu
				}, freeze: true, callback: function () { frm.reload_doc(); }});
			}, 'Mở lại sau đối chiếu', 'Xác nhận mở lại');
		});
	}
});
