/* #227: chọn mẫu đầu phiếu 5% nhưng dòng mang mẫu 8% vẫn tính 8%.
   Giữ thuế nhiều mức, đồng thời cho người dùng chọn rõ khi muốn áp cả đơn.
   Bỏ mẫu từng món bằng chuỗi rỗng để core dùng mẫu đầu phiếu. Không chọn
   template 5% ngoài danh mục món: core có thể đổi nó về 8% khi lưu. */
function vgbTheoThueDauPhieu(frm) {
	if (!Number(frm.doc.vgb_thue_theo_mau)) return;
	(frm.doc.items || []).forEach(function (dong) {
		dong.item_tax_template = '';
		dong.item_tax_rate = '{}';
	});
}

function vgbThueDonMua(frm) {
	frm.set_df_property('taxes', 'read_only', Number(frm.doc.vgb_thue_theo_mau) ? 1 : 0);
	/* Core gọi lại hàm tính này sau khi tải mẫu theo đơn giá. Chặn trên
	   đúng instance PO để phản hồi chậm không nạp lại 8% trên màn hình. */
	if (!frm.cscript.vgbDaGiuThue) {
		var tinhGoc = frm.cscript.calculate_taxes_and_totals;
		frm.cscript.calculate_taxes_and_totals = function () {
			vgbTheoThueDauPhieu(frm);
			return tinhGoc.apply(this, arguments);
		};
		frm.cscript.vgbDaGiuThue = true;
	}
	frm.set_df_property('taxes_and_charges', 'description',
		'Bật Dùng mẫu thuế đầu phiếu cho mọi món để áp cả đơn. Tắt để dùng thuế riêng từng món.');
	var cot = frm.fields_dict.items && frm.fields_dict.items.grid;
	if (cot) {
		cot.update_docfield_property('item_tax_template', 'in_list_view', 1);
		cot.update_docfield_property('item_tax_template', 'label', 'Mẫu thuế từng món');
	}
	if (frm.doc.docstatus !== 0 || !frm.doc.taxes_and_charges) return;
	frm.add_custom_button('Áp mẫu thuế đã chọn cho mọi dòng', function () {
		var tenMau = frm.doc.taxes_and_charges, congTy = frm.doc.company;
		frappe.confirm('Áp ' + frappe.utils.escape_html(tenMau) + ' cho mọi dòng? Mẫu thuế riêng hiện có sẽ được thay trên đơn này.', async function () {
			if (frm.doc.docstatus !== 0 || frm.doc.taxes_and_charges !== tenMau || frm.doc.company !== congTy) return;
			await frm.set_value('vgb_thue_theo_mau', 1);
			if (!Number(frm.doc.vgb_thue_theo_mau)) return;
			vgbTheoThueDauPhieu(frm);
			await frm.trigger('calculate_taxes_and_totals');
			frm.refresh_field('items');
			frappe.show_alert({message: 'Các dòng đã dùng mẫu thuế đầu phiếu. Kiểm tổng rồi lưu đơn.', indicator: 'green'});
		});
	});
}

frappe.ui.form.on('Purchase Order', {
	refresh: vgbThueDonMua,
	vgb_thue_theo_mau: async function (frm) {
		frm.set_df_property('taxes', 'read_only', Number(frm.doc.vgb_thue_theo_mau) ? 1 : 0);
		if (Number(frm.doc.vgb_thue_theo_mau)) {
			if (frm.doc.shipping_rule) {
				await frm.set_value('vgb_thue_theo_mau', 0);
				frappe.msgprint('Đơn có quy tắc phí vận chuyển riêng. Giữ thuế từng món để không mất phí.');
				return;
			}
			// Cùng nguồn với máy chủ: bỏ cả bảng thuế đã chỉnh tay trước đó.
			await frm.trigger('taxes_and_charges');
		}
		vgbTheoThueDauPhieu(frm);
		await frm.trigger('calculate_taxes_and_totals');
		frm.refresh_field('items');
	},
	taxes_and_charges: function (frm) {
		vgbThueDonMua(frm);
		if ((frm.doc.items || []).some(function (r) { return r.item_tax_template; })) {
			frappe.show_alert({message: 'Đơn có thuế riêng từng món. Muốn đổi toàn bộ, bấm Áp mẫu thuế đã chọn cho mọi dòng.', indicator: 'orange'}, 10);
		}
	}
});
