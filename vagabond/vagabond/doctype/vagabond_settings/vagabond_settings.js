// v559 (#410): nút cho phần Bắn tin vào nhóm Zalo. Chỉ quản trị mở được
// Cài đặt này, máy chủ cũng kiểm lại quyền ở từng hàm.
frappe.ui.form.on('Vagabond Settings', {
	refresh(frm) {
		frm.add_custom_button('Nối Zalo Bot', () => {
			frappe.call({ method: 'vagabond.kenh_zalo.dang_ky_webhook', freeze: true })
				.then(r => { const m = r.message || {}; frappe.msgprint({ message: m.loi_nhan || '', indicator: m.ok ? 'green' : 'orange' }); frm.reload_doc(); });
		}, 'Zalo');
		// v559 Codex #413: Zalo lưu đường nhận kể cả khi gọi thử thất bại, nên có nút kiểm lại.
		frm.add_custom_button('Kiểm lại đường nhận', () => {
			frappe.call({ method: 'vagabond.kenh_zalo.kiem_webhook', freeze: true })
				.then(r => { const m = r.message || {}; frappe.msgprint({ message: m.loi_nhan || '', indicator: m.ok ? 'green' : 'orange' }); frm.reload_doc(); });
		}, 'Zalo');
		frm.add_custom_button('Xem trước tin mẫu', () => {
			frappe.call({ method: 'vagabond.kenh_zalo.xem_truoc', args: { loai: 'viec' } })
				.then(r => frappe.msgprint('<pre style="white-space:pre-wrap">' + frappe.utils.escape_html((r.message || {}).tin || '') + '</pre>', 'Xem trước, chưa gửi'));
		}, 'Zalo');
		frm.add_custom_button('Gửi thử tới một nhóm', () => {
			const ds = (frm.doc.zalo_nhom || []).filter(r => r.chat_id).map(r => r.ten_nhom);
			if (!ds.length) { frappe.msgprint('Chưa có nhóm nào có mã chat.'); return; }
			frappe.prompt({ fieldname: 'nhom', fieldtype: 'Select', label: 'Nhóm', options: ds, reqd: 1 }, (v) => {
				const r = (frm.doc.zalo_nhom || []).find(x => x.ten_nhom === v.nhom);
				frappe.call({ method: 'vagabond.kenh_zalo.gui_thu', args: { chat_id: r.chat_id }, freeze: true })
					.then(x => frappe.show_alert({ message: (x.message || {}).loi_nhan || 'Đã gửi', indicator: 'green' }));
			}, 'Gửi tin thử thật', 'Gửi');
		}, 'Zalo');
	}
});
