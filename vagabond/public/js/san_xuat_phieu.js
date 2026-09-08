/* #206: Khải phải chọn PSX mỗi lần trên Desktop. Chỉ gợi ý cho phiếu
   mới, giữ mẫu đã chọn tay và rút gợi ý nếu chuyển sang nghiệp vụ khác. */
(function () {
	var MAU = 'PSX-.YYYY.-';
	async function mac_dinh(frm) {
		if (!frm.is_new() || frm._vgb_sx_dat_mau) return;
		var o = frappe.meta.get_docfield('Stock Entry', 'naming_series', frm.doc.name);
		var goc = o.default || '', hien_tai = frm.doc.naming_series || '', moi, muc_dich = frm.doc.purpose;
		if (frm.doc.purpose === 'Manufacture') {
			if (hien_tai && hien_tai !== goc) return;
			frm._vgb_sx_mau_goc = hien_tai || goc;
			frm._vgb_sx_mau_tu_dong = true;
			moi = MAU;
		} else {
			if (!frm._vgb_sx_mau_tu_dong || hien_tai !== MAU) return;
			moi = frm._vgb_sx_mau_goc || goc;
			frm._vgb_sx_mau_tu_dong = false;
		}
		frm._vgb_sx_dat_mau = true;
		try { await frm.set_value('naming_series', moi); }
		finally { frm._vgb_sx_dat_mau = false; }
		if (frm.doc.purpose !== muc_dich) return mac_dinh(frm);
	}
	frappe.ui.form.on('Stock Entry', {
		onload: mac_dinh,
		purpose: mac_dinh,
		naming_series: function (frm) {
			if (!frm._vgb_sx_dat_mau) frm._vgb_sx_mau_tu_dong = false;
		}
	});
})();
