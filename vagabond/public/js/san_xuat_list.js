/* Khải cần tìm việc theo trạng thái, ngày và kho ngay trên Desk (#206).
   Bộ lọc và số đếm đi qua API có quyền của Frappe 16.27.1. Không đếm
   trang đang tải rồi trình như tổng toàn hệ; không xoá thiết lập lõi. */
(function () {
	var KHAI = {
		'Work Order': {
			ngay: 'planned_start_date', kho: 'source_warehouse',
			truong: ['item_name', 'production_item', 'source_warehouse', 'qty',
				'produced_qty', 'process_loss_qty', 'stock_uom', 'status', 'docstatus'],
			trang: [
				['Nháp', [['docstatus', '=', 0]]],
				['Chưa làm', [['docstatus', '=', 1], ['status', 'in', ['Not Started', 'Submitted', 'Stock Reserved', 'Stock Partially Reserved']]]],
				['Đang làm', [['docstatus', '=', 1], ['status', '=', 'In Process']]],
				['Đã xong', [['docstatus', '=', 1], ['status', '=', 'Completed']]],
				['Đã dừng', [['status', '=', 'Stopped']]],
				['Đã đóng', [['status', '=', 'Closed']]],
				['Đã huỷ', [['docstatus', '=', 2]]]
			]
		},
		'Production Plan': {
			ngay: 'posting_date', truong: ['status', 'docstatus'],
			trang: [
				['Nháp', [['docstatus', '=', 0]]],
				['Chưa làm', [['docstatus', '=', 1], ['status', '=', 'Submitted']]],
				['Đã yêu cầu vật tư', [['status', '=', 'Material Requested']]],
				['Đang làm', [['status', '=', 'In Process']]],
				['Đã xong', [['status', '=', 'Completed']]],
				['Đã đóng', [['status', '=', 'Closed']]],
				['Đã huỷ', [['docstatus', '=', 2]]]
			]
		},
		'BOM': {
			truong: [], giu_chip: true,
			trang: [
				['Nháp', [['docstatus', '=', 0]]],
				['Đang dùng', [['docstatus', '=', 1], ['is_active', '=', 1], ['is_default', '=', 1]]],
				['Còn hiệu lực', [['docstatus', '=', 1], ['is_active', '=', 1]]],
				['Bản cũ', [['docstatus', '=', 1], ['is_active', '=', 0]]],
				['Đã huỷ', [['docstatus', '=', 2]]]
			]
		},
		'Item Alternative': {
			truong: ['vgb_muc', 'vgb_ten_mon', 'vgb_ten_thay_the', 'two_way'],
			trang: ['Dùng được', 'Cần xem', 'Không thay được'].map(function (s) {
				return [s, [['vgb_muc', '=', s]]];
			})
		}
	};
	var TEN = {Draft: 'Nháp', Submitted: 'Chưa làm', 'Not Started': 'Chưa làm',
		'In Process': 'Đang làm', Completed: 'Đã xong', Stopped: 'Đã dừng',
		Closed: 'Đã đóng', Cancelled: 'Đã huỷ', 'Stock Reserved': 'Đã giữ nguyên liệu',
		'Stock Partially Reserved': 'Đã giữ một phần', 'Material Requested': 'Đã yêu cầu vật tư'};
	function chuan(dt, ds) { return ds.map(function (f) { return [dt].concat(f); }); }
	function bo_nhom(ds, dt, truong) {
		return ds.filter(function (f) { return f[0] !== dt || truong.indexOf(f[1]) < 0; });
	}
	function giong(a, b) {
		return JSON.stringify(a.map(JSON.stringify).sort()) === JSON.stringify(b.map(JSON.stringify).sort());
	}
	function chip(doc, dt) {
		if (dt === 'Item Alternative') {
			var muc = doc.vgb_muc || 'Chưa kiểm tra';
			return [muc, {'Dùng được': 'green', 'Cần xem': 'orange', 'Không thay được': 'red'}[muc] || 'gray', 'vgb_muc,=,' + (doc.vgb_muc || '')];
		}
		if (+doc.docstatus === 2) return ['Đã huỷ', 'gray', 'docstatus,=,2'];
		if (+doc.docstatus === 0) return ['Nháp', 'orange', 'docstatus,=,0'];
		var s = doc.status || '';
		return [TEN[s] || s || 'Chưa có trạng thái',
			{Completed: 'green', 'In Process': 'blue', Stopped: 'red', Closed: 'gray'}[s] || 'orange', 'status,=,' + s];
	}
	function nhom_trang(dt, khai) {
		var ds = [['Tất cả trạng thái', []]].concat(khai.trang);
		var truong = [];
		khai.trang.forEach(function (c) { c[1].forEach(function (f) {
			if (truong.indexOf(f[0]) < 0) truong.push(f[0]);
		}); });
		return {ten: 'Trạng thái', truong: truong, dem: true, ds: ds.map(function (c) { return [c[0], chuan(dt, c[1])]; })};
	}
	async function ap_loc(lv, nhom, loc) {
		if (lv._vgb_sx_dang_loc) return;
		lv._vgb_sx_dang_loc = true;
		try {
			var giu = bo_nhom(lv.filter_area.get(), lv.doctype, nhom.truong);
			await lv.filter_area.clear(false);
			await lv.filter_area.add(giu.concat(loc), false);
			lv.start = 0;
			lv.filter_area.trigger_refresh = true;
			await lv.refresh();
		} finally { lv.filter_area.trigger_refresh = true; lv._vgb_sx_dang_loc = false; }
	}
	function ve(lv, khai) {
		if (!lv.page || !lv.page.main || !lv.filter_area) return;
		var dt = lv.doctype, tat_ca = lv.filter_area.get();
		if (!lv._vgb_sx_hop) {
			lv._vgb_sx_hop = $('<div class="vgb-sx-loc"></div>').prependTo(lv.page.main);
		}
		var hop = lv._vgb_sx_hop.empty();
		hop.css({padding: '12px 16px', borderBottom: '1px solid var(--border-color)'});
		var nhom = [nhom_trang(dt, khai)];
		if (khai.ngay) {
			var hom = frappe.datetime.get_today(), mai = frappe.datetime.add_days(hom, 1), sau = frappe.datetime.add_days(hom, 7);
			var f = khai.ngay, gio = dt === 'Work Order';
			function khoang(tu, den) { return [[dt, f, '>=', tu + (gio ? ' 00:00:00' : '')], [dt, f, '<', den + (gio ? ' 00:00:00' : '')]]; }
			nhom.push({ten: gio ? 'Ngày dự kiến' : 'Ngày lập kế hoạch', truong: [f], ds: [
				['Mọi ngày', []], ['Hôm nay', khoang(hom, mai)], ['Ngày mai', khoang(mai, frappe.datetime.add_days(mai, 1))],
				['7 ngày tới', khoang(hom, sau)]]});
		}
		var so_phien = lv._vgb_sx_phien = (lv._vgb_sx_phien || 0) + 1;
		nhom.forEach(function (n) {
			var hang = $('<div></div>').css({display: 'flex', flexWrap: 'wrap', gap: '6px', alignItems: 'center', marginBottom: '8px'}).appendTo(hop);
			$('<strong></strong>').text(n.ten).css({minWidth: '100px', fontSize: '13px'}).appendTo(hang);
			var hien = tat_ca.filter(function (f) { return f[0] === dt && n.truong.indexOf(f[1]) >= 0; });
			n.ds.forEach(function (c) {
				var nut = $('<button type="button" class="btn btn-default btn-sm"></button>').text(c[0]).appendTo(hang);
				nut.css({borderRadius: '18px', minHeight: '36px'}).attr('aria-pressed', String(giong(hien, c[1])));
				nut.toggleClass('btn-primary', giong(hien, c[1]));
				nut.on('click', function () { ap_loc(lv, n, c[1]).catch(function () { frappe.msgprint('Chưa đổi được bộ lọc. Thử lại hoặc dùng Bộ lọc phía trên.'); }); });
				if (n.dem) {
					nut.text(c[0] + ' (…)');
					frappe.db.count(dt, {filters: bo_nhom(tat_ca, dt, n.truong).concat(c[1])}).then(function (so) {
						if (lv._vgb_sx_phien === so_phien) nut.text(c[0] + ' (' + (so == null ? '?' : so) + ')');
					}).catch(function () { if (lv._vgb_sx_phien === so_phien) nut.text(c[0] + ' (?)').attr('title', 'Chưa lấy được số đếm'); });
				}
			});
		});
		if (khai.kho) {
			var kho = tat_ca.filter(function (f) { return f[0] === dt && f[1] === khai.kho; });
			var hang_kho = $('<div></div>').css({display: 'flex', gap: '8px', alignItems: 'center'}).appendTo(hop);
			$('<strong>Kho nguồn</strong>').appendTo(hang_kho);
			$('<button type="button" class="btn btn-default btn-sm"></button>').text(kho.length ? String(kho[0][3]) : 'Chọn kho…').appendTo(hang_kho).on('click', function () {
				frappe.prompt({fieldname: 'kho', label: 'Kho nguyên liệu', fieldtype: 'Link', options: 'Warehouse', reqd: 1,
					get_query: function () { return {filters: {is_group: 0, disabled: 0}}; }}, function (v) {
					ap_loc(lv, {truong: [khai.kho]}, [[dt, khai.kho, '=', v.kho]]).catch(function () { frappe.msgprint('Chưa đổi được bộ lọc kho.'); });
				}, 'Lọc theo kho nguồn', 'Lọc');
			});
			if (kho.length) $('<button type="button" class="btn btn-link btn-sm">Bỏ lọc kho</button>').appendTo(hang_kho).on('click', function () { ap_loc(lv, {truong: [khai.kho]}, []).catch(function () { frappe.msgprint('Chưa bỏ được bộ lọc kho.'); }); });
		}
		$('<div class="text-muted small"></div>').css('margin-top', '8px').text(dt === 'Item Alternative'
			? 'Tình trạng cấu hình từ lần kiểm gần nhất; tồn thực dùng phải kiểm theo kho và lô khi hoàn tất.'
			: 'Số đếm theo bộ lọc khác đang chọn và quyền của bạn. Trạng thái lệnh không xác nhận đủ nguyên liệu.').appendTo(hop);
	}
	Object.keys(KHAI).forEach(function (dt) {
		var cu = frappe.listview_settings[dt] || {}, khai = KHAI[dt];
		if (cu._vgb_sx_da_gan) return;
		var on = cu.onload, ref = cu.refresh;
		var moi = Object.assign({}, cu, {_vgb_sx_da_gan: true,
			add_fields: Array.from(new Set((cu.add_fields || []).concat(khai.truong))),
			onload: function (lv) { if (on) on.call(this, lv); ve(lv, khai); },
			refresh: function (lv) { if (ref) ref.call(this, lv); ve(lv, khai); }
		});
		if (!khai.giu_chip) {
			moi.has_indicator_for_draft = true; moi.has_indicator_for_cancelled = true;
			moi.get_indicator = function (doc) { return chip(doc, dt); };
		}
		if (dt === 'Work Order') {
			moi.formatters = Object.assign({}, cu.formatters || {}, {
				production_item: function (value, df, doc) {
					// Frappe 16.27.1 list_view.js: get_subject_text giữ Link,
					// get_link_element gán textContent/title. HTML ở đây hiện thành mã.
					var ma = String(doc.production_item || value || '');
					var ten = String(doc.item_name || ma);
					return ten && ma && ten !== ma ? ten + ' (' + ma + ')' : ten || ma;
				}
			});
		}
		frappe.listview_settings[dt] = moi;
	});
})();
