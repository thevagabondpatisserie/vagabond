/* Mặc định cho lệnh mới; lệnh đã lưu chỉ đọc, không sửa kho khi mở màn.
   ERPNext có thao tác riêng để đổi kho dòng. Giữ lựa chọn đó, cảnh báo
   chênh lệch để Khải xác nhận trước khi backflush. */
(function () {
	function esc(s) { return frappe.utils.escape_html(String(s == null ? '' : s)); }
	function theo_doi_chon_tay(frm) {
		var f = frm.fields_dict.source_warehouse;
		if (f && f.$input) f.$input.off('.vgb_sx').on('input.vgb_sx awesomplete-selectcomplete.vgb_sx', function () {
			frm._vgb_sx_chon_tay = true;
		});
	}
	async function mac_dinh(frm) {
		if (!frm.is_new() || !frm.doc.production_item || frm._vgb_sx_chon_tay) return;
		var ma = frm.doc.production_item, ten = frm.doc.name;
		var phien = frm._vgb_sx_phien = (frm._vgb_sx_phien || 0) + 1;
		// Chờ cả get_item_details của ERPNext, tránh hai phản hồi đè nhau.
		await new Promise(function (x) { frappe.after_ajax(x); });
		var r = await frappe.db.get_value('Item', ma, 'custom_kho_nguyen_lieu_sx');
		if (frm._vgb_sx_phien !== phien || frm.doc.name !== ten || frm.doc.production_item !== ma || !frm.is_new() || frm._vgb_sx_chon_tay) return;
		var kho = r.message && r.message.custom_kho_nguyen_lieu_sx;
		if (kho) {
			await frm.set_value('source_warehouse', kho);
			frm._vgb_sx_kho_mon = kho;
		} else if (frm._vgb_sx_kho_mon && frm.doc.source_warehouse === frm._vgb_sx_kho_mon) {
			await frm.set_value('source_warehouse', '');
			frm._vgb_sx_kho_mon = '';
		}
	}
	function hien(frm, r) {
		var e = esc, html = '<div><b>Kho nguyên liệu:</b> ' + e(r.kho_nguon || 'Chưa chọn') +
			' · <b>Kho thành phẩm:</b> ' + e(r.kho_dich || 'Chưa chọn') + '</div>';
		html += '<div>Đã nhập ' + e(r.da_lam) + ' · Hao hụt ' + e(r.hao_hut) + ' · Còn theo lệnh ' + e(r.con_lai) + ' ' + e(r.don_vi) + '</div>';
		if (r.qua_wip) html += '<div>Luồng qua kho dở dang: ' + e(r.kho_wip || 'Chưa chọn') + '. Kiểm tra phiếu chuyển nguyên liệu liên quan.</div>';
		if (r.so_khac_kho) {
			html += '<div><b>Cần kiểm tra ' + e(r.so_khac_kho) + ' dòng khác kho đầu lệnh:</b> ' +
				r.dong.filter(function (d) { return d.khac_kho; }).map(function (d) {
					return e(d.ten) + ' (' + e(d.ma) + ') → ' + e(d.kho);
				}).join('; ') + '. Không tự đổi kho của lệnh đã lưu.</div>';
		}
		html += '<div class="text-muted">Số liệu của lần lưu gần nhất. Chưa xác nhận đủ nguyên liệu hoặc lô khả dụng.</div>';
		var hop = frm.dashboard.parent.find('.vgb-sx-thong-tin');
		if (hop.length) hop.html(html);
		else frm.dashboard.add_section('<div class="vgb-sx-thong-tin">' + html + '</div>', 'Kho và tiến độ sản xuất');
	}
	frappe.ui.form.on('Work Order', {
		onload: function (frm) { frm._vgb_sx_chon_tay = !!frm.doc.source_warehouse; frm._vgb_sx_kho_mon = ''; theo_doi_chon_tay(frm); },
		production_item: function (frm) { return mac_dinh(frm); },
		refresh: function (frm) {
			theo_doi_chon_tay(frm);
			if (frm.is_new()) return mac_dinh(frm);
			var ten = frm.doc.name;
			var phien = frm._vgb_sx_doc = (frm._vgb_sx_doc || 0) + 1;
			frappe.call({method: 'vagabond.san_xuat_desktop.chi_tiet', args: {ten: ten}}).then(function (r) {
				if (frm.doc.name === ten && frm._vgb_sx_doc === phien && r.message) hien(frm, r.message);
			}).catch(function () { frappe.show_alert({message: 'Chưa tải được thông tin kho của lệnh. Tải lại trước khi hoàn tất.', indicator: 'orange'}); });
		}
	});
})();
