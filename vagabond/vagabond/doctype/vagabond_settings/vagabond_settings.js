// v562 (#410): nút cho phần Bắn tin vào nhóm Zalo. Chỉ quản trị mở được
// Cài đặt này, máy chủ cũng kiểm lại quyền ở từng hàm.
// v562 Codex #417, #423: Loại tin và Chủ đề chỉ chọn từ danh mục (hai ô này
// read_only, không gõ tay được); máy chủ vẫn kiểm lại lúc lưu.
const ZALO_DANH_MUC = {
	loai_tin: ['thong_bao', 'viec', 'canh_bao', 'ban_tin', 'phat_hanh'],
	chu_de: ['kho', 'san_xuat', 'cong_no', 'ban_hang', 'don_web', 'dat_ban', 'phat_hanh'],
};
function zalo_chon(frm, cdt, cdn, truong) {
	const row = locals[cdt][cdn];
	const dang = (row[truong] || '').split(/[,;]/).map(s => s.trim()).filter(Boolean);
	const d = new frappe.ui.Dialog({
		title: truong === 'loai_tin' ? 'Chọn loại tin (bỏ trống là nhận tất)' : 'Chọn chủ đề (bỏ trống là nhận tất)',
		fields: [{ fieldname: 'chon', fieldtype: 'MultiCheck', columns: 2,
			options: ZALO_DANH_MUC[truong].map(v => ({ label: v, value: v, checked: dang.includes(v) })) }],
		primary_action_label: 'Xong',
		primary_action(v) {
			frappe.model.set_value(cdt, cdn, truong, (v.chon || []).join(', '));
			d.hide();
		},
	});
	d.show();
}
function zalo_chon_nhom(frm, cdt, cdn) {
	let ds = [];
	try { ds = JSON.parse(frm.doc.zalo_chat_moi || '[]'); } catch (e) { ds = []; }
	ds = ds.filter(x => String(x.loai || '').toUpperCase() === 'GROUP');
	if (!ds.length) {
		frappe.msgprint('Chưa có nhóm nào nhắn bot. Thêm bot vào nhóm Zalo, @nhắc bot một lần, rồi tải lại trang.');
		return;
	}
	const nhan = x => (x.ten || 'Nhóm không tên') + ' (' + x.chat_id + ')';
	// Codex #425 vòng 11: tới 20 nhóm, ô chọn phải gõ tìm được (Autocomplete), không xổ danh sách kéo.
	frappe.prompt({ fieldname: 'nhom', fieldtype: 'Autocomplete', label: 'Gõ tên nhóm để tìm', reqd: 1, options: ds.map(nhan) }, (v) => {
		const x = ds.find(y => nhan(y) === v.nhom);
		if (!x) { frappe.msgprint('Chọn đúng một nhóm trong danh sách gợi ý.'); return; }
		frappe.model.set_value(cdt, cdn, 'chat_id', x.chat_id);
		if (!locals[cdt][cdn].ten_nhom) frappe.model.set_value(cdt, cdn, 'ten_nhom', x.ten || '');
	}, 'Chọn nhóm đã nhắn bot', 'Chọn');
}
frappe.ui.form.on('Vagabond Kenh Zalo', {
	form_render(frm, cdt, cdn) {
		const g = frm.fields_dict.zalo_nhom.grid.grid_rows_by_docname[cdn];
		if (!g || !g.grid_form) return;
		// Ô read_only để trống thì Frappe ẩn cả ô, nên nút đặt ở đầu khung dòng.
		const khung = $(g.grid_form.wrapper);
		if (khung.find('.zalo-chon').length) return;
		const hang = $('<div class="zalo-chon" style="margin:8px 0;display:flex;gap:8px"></div>').prependTo(khung.find('.form-area').first().length ? khung.find('.form-area').first() : khung);
		// v562 Codex #425: mã chat chỉ chọn từ các NHÓM đã nhắn bot, không gõ tay.
		$('<button class="btn btn-xs btn-default"></button>').text('Chọn nhóm đã nhắn bot').appendTo(hang)
			.on('click', () => zalo_chon_nhom(frm, cdt, cdn));
		[['loai_tin', 'Chọn loại tin'], ['chu_de', 'Chọn chủ đề']].forEach(([f, nhan]) => {
			$('<button class="btn btn-xs btn-default"></button>').text(nhan).appendTo(hang)
				.on('click', () => zalo_chon(frm, cdt, cdn, f));
		});
	},
});
frappe.ui.form.on('Vagabond Settings', {
	refresh(frm) {
		frm.add_custom_button('Nối Zalo Bot', () => {
			frappe.call({ method: 'vagabond.kenh_zalo.dang_ky_webhook', freeze: true })
				.then(r => { const m = r.message || {}; frappe.msgprint({ message: m.loi_nhan || '', indicator: m.ok ? 'green' : 'orange' }); frm.reload_doc(); });
		}, 'Zalo');
		// v562 Codex #413: Zalo lưu đường nhận kể cả khi gọi thử thất bại, nên có nút kiểm lại.
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
			frappe.prompt({ fieldname: 'nhom', fieldtype: 'Autocomplete', label: 'Gõ tên nhóm để tìm', options: ds, reqd: 1 }, (v) => {
				const r = (frm.doc.zalo_nhom || []).find(x => x.ten_nhom === v.nhom);
				if (!r) { frappe.msgprint('Chọn đúng một nhóm trong danh sách gợi ý.'); return; }
				frappe.call({ method: 'vagabond.kenh_zalo.gui_thu', args: { chat_id: r.chat_id }, freeze: true })
					.then(x => frappe.show_alert({ message: (x.message || {}).loi_nhan || 'Đã gửi', indicator: 'green' }));
			}, 'Gửi tin thử thật', 'Gửi');
		}, 'Zalo');
	}
});
