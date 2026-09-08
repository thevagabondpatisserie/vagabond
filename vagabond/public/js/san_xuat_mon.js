/* Kho của MÓN ĐẦU RA, không phải kho cố định cho nguyên liệu dùng chung. */
frappe.ui.form.on('Item', {
	setup: function (frm) {
		frm.set_query('custom_kho_nguyen_lieu_sx', function () {
			return {filters: {is_group: 0, disabled: 0}};
		});
	}
});
