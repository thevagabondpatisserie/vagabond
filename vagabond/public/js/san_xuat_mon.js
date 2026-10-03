/* Kho của MÓN ĐẦU RA, không phải kho cố định cho nguyên liệu dùng chung. */
frappe.ui.form.on('Item', {
	setup: function (frm) {
		frm.set_query('custom_kho_nguyen_lieu_sx', function () {
			return {filters: {is_group: 0, disabled: 0}};
		});
	},
	// v564: bo ao ma hang ngay tren Desk (anh Viet chot 03/10/2026). May chu
	// kiem quyen va hang rao; nut chi la loi vao. Xem vagabond/bo_ao.py.
	refresh: function (frm) {
		if (frm.is_new() || frm.doc.is_stock_item) return;
		var vai = ['System Manager', 'Giám đốc', 'AP Giám đốc', 'Manufacturing Manager'];
		if (!vai.some(function (v) { return frappe.user.has_role(v); })) return;
		frm.add_custom_button('Bỏ ảo (có tồn kho trở lại)', function () {
			frappe.call({
				method: 'vagabond.bo_ao.xem', args: {ma: frm.doc.name},
				callback: function (r) {
					var k = r.message || {};
					if (k.chan) { frappe.msgprint(k.chan); return; }
					var d = new frappe.ui.Dialog({
						title: 'Bỏ ảo ' + frm.doc.name,
						fields: [
							{fieldtype: 'HTML', options: '<div style="line-height:1.6">' + frappe.utils.escape_html(k.tong_ket || '') + '<br>Chỉ áp từ nay, lệnh và phiếu kho đã có giữ nguyên.</div>'},
							{fieldtype: 'Small Text', fieldname: 'ly_do', label: 'Lý do bỏ ảo', reqd: 1}
						],
						primary_action_label: 'Bỏ ảo',
						primary_action: function (v) {
							d.hide();
							frappe.call({
								method: 'vagabond.bo_ao.chay', args: {ma: frm.doc.name, ly_do: v.ly_do, chay_that: 1},
								freeze: true,
								callback: function (r2) { frappe.msgprint((r2.message || {}).tong_ket || 'Đã bỏ ảo.'); frm.reload_doc(); }
							});
						}
					});
					d.show();
				}
			});
		});
	}
});
