// v562 (#410): nút cho phần Bắn tin vào nhóm Zalo. Chỉ quản trị mở được
// Cài đặt này, máy chủ cũng kiểm lại quyền ở từng hàm.
// v562 Codex #417, #423: Loại tin và Chủ đề chỉ chọn từ danh mục (hai ô này
// read_only, không gõ tay được); máy chủ vẫn kiểm lại lúc lưu.
// v570: phép thuần (VGB_CD, danh mục và nhãn loại tin Zalo) nằm ở tệp dùng chung
// /assets/vagabond/js/cai_dat_loi_chung.js, cùng tệp màn "Cài đặt lõi và API" của
// app nạp. Hai nơi không giữ hai bản.
function vgb_nap_cd_chung() {
	if (window.VGB_CD && window.VGB_CD.tinhTrang) return Promise.resolve(window.VGB_CD);
	if (window.__vgb_cd_nap) return window.__vgb_cd_nap;
	window.__vgb_cd_nap = new Promise(function (ok, hong) {
		var s = document.createElement('script');
		s.src = '/assets/vagabond/js/cai_dat_loi_chung.js?t=' + Date.now();
		s.onload = function () { ok(window.VGB_CD); };
		s.onerror = function () { window.__vgb_cd_nap = null; hong(new Error('Không nạp được tệp cài đặt dùng chung.')); };
		document.head.appendChild(s);
	});
	return window.__vgb_cd_nap;
}
function zalo_chon(frm, cdt, cdn, truong) {
	const row = locals[cdt][cdn];
	const dang = (row[truong] || '').split(/[,;]/).map(s => s.trim()).filter(Boolean);
	const nhan = VGB_CD.ZALO_NHAN[truong];
	const e = frappe.utils.escape_html;
	const html = '<div class="vgbz-goi">Không tích ô nào là nhóm nhận <b>tất cả</b> ' +
		(truong === 'loai_tin' ? 'loại tin.' : 'chủ đề.') + '</div>' +
		VGB_CD.ZALO_DANH_MUC[truong].map(v => {
			const n = nhan[v] || ['', v, ''];
			return '<label class="vgbz-dong"><input type="checkbox" value="' + e(v) + '"' + (dang.includes(v) ? ' checked' : '') + '>' +
				'<span class="vgbz-ic">' + e(n[0]) + '</span><span><b>' + e(n[1]) + '</b><small>' + e(n[2]) + '</small></span></label>';
		}).join('') +
		'<style>.vgbz-goi{font-size:13px;color:var(--text-muted);margin-bottom:8px}' +
		'.vgbz-dong{display:flex;align-items:flex-start;gap:12px;min-height:56px;padding:10px 8px;border-top:1px solid var(--border-color);cursor:pointer;margin:0}' +
		'.vgbz-dong input{margin-top:3px;width:18px;height:18px;flex:none}.vgbz-ic{font-size:18px;line-height:22px;flex:none}' +
		'.vgbz-dong b{display:block;font-size:14px}.vgbz-dong small{display:block;font-size:13px;color:var(--text-muted);line-height:1.4}</style>';
	const d = new frappe.ui.Dialog({
		title: truong === 'loai_tin' ? 'Nhóm này nhận loại tin nào?' : 'Nhóm này nhận chủ đề nào?',
		fields: [{ fieldname: 'ds', fieldtype: 'HTML', options: html }],
		primary_action_label: 'Xong',
		primary_action() {
			const chon = d.$wrapper.find('.vgbz-dong input:checked').map((i, x) => x.value).get();
			frappe.model.set_value(cdt, cdn, truong, chon.join(', '));
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
				.on('click', () => vgb_nap_cd_chung().then(() => zalo_chon(frm, cdt, cdn, f)));
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


(function () {
	if (typeof frappe === 'undefined' || !frappe.ui || !frappe.ui.form) return;
	var esc = function (s) { return frappe.utils.escape_html(String(s == null ? '' : s)); };
	var CSS = [
		'.vgb-cd .vgbc-bar{background:var(--card-bg,#fff);border:1px solid var(--border-color,#e2e6e9);border-radius:12px;padding:16px 18px;margin:0 0 14px}',
		'.vgb-cd .vgbc-tim{width:100%;min-height:44px;border:1px solid var(--border-color,#cfd6db);border-radius:10px;padding:0 14px;font-size:15px;background:var(--control-bg,#f4f5f6)}',
		'.vgb-cd .vgbc-kq{margin-top:8px}',
		'.vgb-cd .vgbc-nh .vgbc-kq a,.vgb-cd .vgbc-kq a{display:flex;align-items:center;min-height:44px;padding:6px 10px;border-radius:8px;color:inherit;text-decoration:none;gap:8px;font-size:14px}',
		'.vgb-cd .vgbc-kq a:hover{background:var(--fg-hover-color,#f4f5f6)}',
		'.vgb-cd .vgbc-kq small{color:var(--text-muted,#6b737b);font-size:13px}',
		'.vgb-cd .vgbc-h{font-weight:600;font-size:15px;margin:14px 0 2px}',
		'.vgb-cd .vgbc-mo{font-size:13px;color:var(--text-muted,#6b737b);margin-bottom:10px}',
		'.vgb-cd .vgbc-chips{display:flex;flex-wrap:wrap;gap:8px}',
		'.vgb-cd .vgbc-chip{display:inline-flex;align-items:center;gap:7px;min-height:36px;padding:6px 12px;border-radius:999px;font-size:13px;font-weight:500;border:1px solid transparent;cursor:pointer;line-height:1.2}',
		'.vgb-cd .vgbc-chip.nho{min-height:26px;padding:2px 10px;font-size:13px;cursor:default}',
		'.vgb-cd .vgbc-chip i{width:8px;height:8px;border-radius:50%;flex:none}',
		'.vgb-cd .vgbc-ok{background:#e9f7ef;color:#1e6b3c;border-color:#c6ead4}.vgb-cd .vgbc-ok i{background:#22a05a}',
		'.vgb-cd .vgbc-no{background:#f3f4f6;color:#5b636b;border-color:#e2e5e8}.vgb-cd .vgbc-no i{background:#a3abb2}',
		'.vgb-cd .vgbc-off{background:#fff6e5;color:#8a5a00;border-color:#f6dfaa}.vgb-cd .vgbc-off i{background:#e0a100}',
		'.vgb-cd .vgbc-err{background:#fdecec;color:#a42424;border-color:#f6caca}.vgb-cd .vgbc-err i{background:#d93636}',
		'.vgb-cd .vgbc-seg{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 4px}',
		'.vgb-cd .vgbc-seg button{min-height:44px;padding:0 14px;border-radius:9px;border:1px solid var(--border-color,#d8dde1);background:var(--card-bg,#fff);font-size:13px;color:inherit}',
		'.vgb-cd .vgbc-seg button.on{background:#171717;color:#fff;border-color:#171717}',
		'.vgb-cd .vgbc-anchon select{display:none}',
		'.vgb-cd .vgbc-anchon-in{display:none}',
		// Công tắc thay hộp tích: chỉ đổi hình, ô vẫn là checkbox, vẫn lưu 0/1.
		/* v571: tren site that Frappe ep o tich 18px va o .input-area la flex rong 26px,
		   nen cong tac chi con nua hinh tron va de len chu nhan (do 04/10/2026). Phai
		   noi rong hop chua va ep kich thuoc bang !important; thu truc tiep tren site
		   thi cong tac du 42x24. Bo gia lap node khong tinh CSS nen bang chung la anh
		   chup site that dinh tren PR. */
		'.vgb-cd .frappe-control[data-fieldtype="Check"] .input-area{flex:none!important;width:auto!important;min-width:52px}',
		'.vgb-cd .frappe-control[data-fieldtype="Check"] input[type="checkbox"]{width:42px!important;min-width:42px!important;max-width:42px!important;height:24px!important;min-height:24px}',
		'.vgb-cd .frappe-control[data-fieldtype="Check"] input[type="checkbox"]{-webkit-appearance:none;appearance:none;width:42px;height:24px;border-radius:12px;background:#cfd6db;position:relative;border:0;margin:0 10px 0 0;cursor:pointer;flex:none;vertical-align:middle;transition:background .15s}',
		'.vgb-cd .frappe-control[data-fieldtype="Check"] input[type="checkbox"]::after{content:"";position:absolute;width:18px;height:18px;border-radius:50%;background:#fff;top:3px;left:3px;transition:left .15s;box-shadow:0 1px 2px rgba(0,0,0,.2)}',
		'.vgb-cd .frappe-control[data-fieldtype="Check"] input[type="checkbox"]:checked{background:#22a05a}',
		'.vgb-cd .frappe-control[data-fieldtype="Check"] input[type="checkbox"]:checked::after{left:21px}',
		'.vgb-cd .frappe-control[data-fieldtype="Check"] label{display:flex;align-items:center;min-height:44px}',
		'.vgb-cd .vgbc-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}',
		'.vgb-cd .vgbc-card{border:1px solid var(--border-color,#e2e6e9);border-radius:10px;padding:14px}',
		'.vgb-cd .vgbc-card b{font-size:14px}',
		'.vgb-cd .vgbc-card .p{font-size:13px;color:var(--text-muted,#6b737b);margin:2px 0 8px}',
		'.vgb-cd .vgbc-r{display:flex;align-items:center;gap:8px;justify-content:space-between;font-size:13px;min-height:36px;border-top:1px dashed var(--border-color,#eceef0)}',
		'.vgb-cd .vgbc-r span.g{font-family:var(--font-stack-monospace,monospace);color:var(--text-muted,#6b737b)}',
		'.vgb-cd .vgbc-lnk{display:inline-flex;align-items:center;min-height:44px;font-size:13px;font-weight:500}',
		'.vgb-cd .vgbc-dong{display:flex;align-items:center;justify-content:space-between;min-height:48px;border-top:1px solid var(--border-color,#eef0f2);font-size:14px;gap:12px}',
		'.vgb-cd .vgbc-dong small{color:var(--text-muted,#6b737b);font-size:13px}',
		'.vgb-cd .section-head .vgbc-chip{margin-left:10px;vertical-align:middle}',
		// Codex #435: chip bấm được để nhảy tới ô phải cao đủ 44px cho ngón tay.
		'.vgb-cd .vgbc-chip[data-toi]{min-height:44px}',
		// Codex #435 vòng 7: nút hành động của ô ngân hàng cũng đủ 44px.
		'.vgb-cd .vgbc-thu-lai,.vgb-cd .vgbc-dung-khac{min-height:44px;padding:0 14px}',
		// Codex #435: thanh tình trạng chỉ hai dòng (2 x 44px + khe 8px), phần còn
		// lại sau nút Xem đủ.
		'.vgb-cd .vgbc-tt.gon{max-height:96px;overflow:hidden}',
		'.vgb-cd .vgbc-xem{min-height:44px;margin-top:4px;padding:0 4px;background:none;border:0;color:var(--text-color,#1f272e);font-weight:600;font-size:13px;cursor:pointer;text-decoration:underline}',
	].join('');

	function chip(tr, chu, nho, toi) {
		return '<span class="vgbc-chip ' + (nho ? 'nho ' : '') + 'vgbc-' + tr + '"' + (toi ? ' data-toi="' + esc(toi) + '"' : '') +
			' role="' + (toi ? 'button' : 'note') + '"><i></i>' + esc(chu) + '</span>';
	}

	function chiMuc(frm) {
		// Danh bạ cho ô tìm: mỗi ô có nhãn kèm tên tab và tên mục chứa nó.
		var ds = [], tab = '', muc = '';
		(frm.meta.fields || []).forEach(function (df) {
			if (df.fieldtype === 'Tab Break') { tab = df.label || ''; return; }
			if (df.fieldtype === 'Section Break') { muc = df.label || ''; return; }
			if (df.fieldtype === 'Column Break' || df.hidden || !df.label) return;
			ds.push({ fn: df.fieldname, nhan: df.label, mo: df.description || '', tab: tab, muc: muc });
		});
		return ds;
	}

	function veThanh(frm) {
		var $w = $(frm.layout.wrapper);
		var $tabs = $w.find('.form-tabs-list').first();
		var $bar = $w.find('.vgbc-bar');
		if (!$bar.length) {
			$bar = $('<div class="vgbc-bar">' +
				'<input class="vgbc-tim" type="search" placeholder="Tìm cài đặt: mã QR, Ahamove, máy in, điểm thành viên...">' +
				'<div class="vgbc-kq"></div>' +
				'<div class="vgbc-h">Tình trạng kết nối</div>' +
				'<div class="vgbc-mo">Bấm một ô để nhảy tới phần cài đặt đó. Xanh là đã khai đủ, xám là chưa khai, vàng là đã khai nhưng đang tắt, đỏ là vừa có sự cố.</div>' +
				'<div class="vgbc-chips vgbc-tt gon"></div><button type="button" class="vgbc-xem"></button></div>');
			if ($tabs.length) $bar.insertBefore($tabs); else $bar.prependTo($w);
			$bar.on('input', '.vgbc-tim', function () {
				var kq = VGB_CD.timTruong(this.value, chiMuc(frm));
				$bar.find('.vgbc-kq').html(kq.map(function (x) {
					return '<a href="#" data-toi="' + esc(x.fn) + '"><b>' + esc(x.nhan) + '</b><small>' + esc(x.tab) + ' › ' + esc(x.muc) + '</small></a>';
				}).join('') || (this.value.trim() ? '<small>Không thấy cài đặt nào khớp.</small>' : ''));
			});
			$bar.on('click', '[data-toi]', function (e) {
				e.preventDefault();
				VGB_CD.moToi(frm, $(this).attr('data-toi'));
			});
			$bar.on('click', '.vgbc-xem', function () {
				frm.__vgb_mo_tt = !frm.__vgb_mo_tt;
				veThanh(frm);
			});
		}
		var ds = VGB_CD.xepTinhTrang(VGB_CD.tinhTrang(frm.doc));
		var $tt = $bar.find('.vgbc-tt');
		$tt.html(ds.map(function (t) {
			return chip(t.trang, t.ten + (t.trang === 'err' ? ': ' + t.ghi : ''), 0, t.toi);
		}).join(''));
		if (frm.__vgb_mo_tt) $tt.removeClass('gon'); else $tt.addClass('gon');
		var can = ds.filter(function (t) { return t.trang !== 'ok'; }).length;
		$bar.find('.vgbc-xem').text(frm.__vgb_mo_tt ? 'Thu gọn'
			: 'Xem đủ ' + ds.length + ' kết nối' + (can ? ' (' + can + ' cần để ý, đã xếp lên đầu)' : ''));
	}

	function veChipMuc(frm) {
		var tt = VGB_CD.tinhTrangMuc(frm.doc);
		(frm.layout.sections || []).forEach(function (s) {
			var fn = s.df && s.df.fieldname;
			if (!fn || !s.head) return;
			s.head.find('.vgbc-chip').remove();
			// Codex #435: trên Frappe 16, s.head CHÍNH LÀ .section-head (con duy nhất là
			// .collapse-indicator), nên tìm .section-head bên trong nó luôn ra rỗng và
			// chip không bao giờ hiện. Gắn thẳng vào s.head.
			var $h = s.head.is && s.head.is('.section-head') ? s.head : s.head.find('.section-head').first();
			if (tt[fn] && $h.length) $h.append(chip(tt[fn].trang, tt[fn].ghi, 1));
		});
	}

	function veMatKhau(frm) {
		(frm.meta.fields || []).forEach(function (df) {
			if (df.fieldtype !== 'Password' || !frm.fields_dict[df.fieldname]) return;
			var $l = frm.fields_dict[df.fieldname].$wrapper.find('.control-label').first();
			$l.find('.vgbc-chip').remove();
			var c = frm.doc[df.fieldname] && String(frm.doc[df.fieldname]).trim() !== '';
			$l.append(' ' + chip(c ? 'ok' : 'no', c ? 'Đã khai' : 'Chưa khai', 1));
		});
	}

	function veChipChon(frm) {
		Object.keys(VGB_CD.NHAN_CHON).forEach(function (fn) {
			var f = frm.fields_dict[fn];
			if (!f) return;
			var $ci = f.$wrapper.find('.control-input').first();
			$ci.addClass('vgbc-anchon');
			f.$wrapper.find('.vgbc-seg').remove();
			var $seg = $('<div class="vgbc-seg"></div>').insertBefore($ci);
			VGB_CD.NHAN_CHON[fn].forEach(function (p) {
				$('<button type="button"></button>').text(p[1]).toggleClass('on', frm.doc[fn] === p[0])
					.appendTo($seg).on('click', function () { frm.set_value(fn, p[0]); });
			});
		});
		veNganHang(frm);
	}

	// Ô chọn ngân hàng có tìm nhanh, danh mục từ máy chủ (tai_khoan.NGAN_HANG).
	// Hai ô Mã BIN và Tên hiện cho khách để chỉ đọc, chỉ đổi qua ô này, nên
	// không thể lệch nhau và không ai gõ tay sai một số.
	function veNganHang(frm) {
		var f = frm.fields_dict.ngan_hang_bin;
		if (!f) return;
		f.$wrapper.find('.vgbc-nh').remove();
		// Ô BIN gốc LUÔN ẩn: chỉ đổi qua danh mục, để Mã BIN và Tên hiện cho khách
		// không lệch nhau (Codex #435). Không để ô BIN read_only trong doctype: Frappe
		// ẩn cả ô read_only khi trống, mất luôn ô chọn.
		f.$wrapper.find('.control-input').first().addClass('vgbc-anchon-in');
		var $k = $('<div class="vgbc-nh"></div>').appendTo(f.$wrapper);
		// Khi chưa có danh mục (đang tải hoặc tải hỏng) vẫn cho THẤY mã đang lưu,
		// không để khung trống (Codex #433 vòng 3), nhưng không cho gõ tay.
		function dangLuu() {
			var bin = String(frm.doc.ngan_hang_bin || '').trim();
			return bin ? chip('no', 'Đang lưu: ' + (frm.doc.ngan_hang_hien_thi || 'chưa có tên') + ' · BIN ' + bin, 1) : chip('no', 'Chưa chọn ngân hàng', 1);
		}
		function ve(ds) {
			var hien = VGB_CD.nganHangTheoBin(ds, frm.doc.ngan_hang_bin);
			// Codex #435 vòng 6: BIN đang lưu mà ngoài danh mục (ngân hàng khai tay)
			// KHÔNG phải lỗi: vẫn dùng được, chỉ báo vàng và giữ nguyên.
			$k.html('<div class="vgbc-chips" style="margin:6px 0">' +
				(hien ? chip('ok', 'Đang dùng: ' + hien.ten, 1)
					: (frm.doc.ngan_hang_bin ? chip('off', 'Đang dùng: ' + (frm.doc.ngan_hang_hien_thi || 'chưa có tên') + ' · BIN ' + frm.doc.ngan_hang_bin + ', khai ngoài danh mục', 1)
						: chip('no', 'Chưa chọn ngân hàng', 1))) +
				'</div><input class="vgbc-tim" type="search" placeholder="Gõ tên ngân hàng để đổi: MB, Vietcombank, OCB..."><div class="vgbc-kq"></div>' +
				'<button type="button" class="vgbc-xem vgbc-khac">Ngân hàng không có trong danh sách?</button><div class="vgbc-khac-o"></div>');
			// Ngân hàng ngoài danh mục: khai CẢ HAI ô một lượt (BIN 6 số và tên hiện
			// cho khách), máy chủ kiểm lại bằng tai_khoan.kiem_cap_ngan_hang.
			$k.on('click', '.vgbc-khac', function () {
				$k.find('.vgbc-khac-o').html('<div class="vgbc-mo">Mã BIN là 6 chữ số ngân hàng dùng cho mã QR (hỏi ngân hàng hoặc xem trên app ngân hàng). Tên là chữ khách thấy dưới mã QR.</div>' +
					'<input class="vgbc-tim vgbc-bin-moi" inputmode="numeric" maxlength="6" placeholder="Mã BIN, 6 chữ số">' +
					'<input class="vgbc-tim vgbc-ten-moi" placeholder="Tên ngân hàng hiện cho khách">' +
					'<button type="button" class="btn btn-xs btn-default vgbc-dung-khac">Dùng ngân hàng này</button><div class="vgbc-loi-khac"></div>');
			});
			$k.on('click', '.vgbc-dung-khac', function () {
				var bin = String($k.find('.vgbc-bin-moi').val() || '').trim();
				var ten = String($k.find('.vgbc-ten-moi').val() || '').trim();
				var loi = VGB_CD.kiemCapNganHang(bin, ten);
				if (loi) { $k.find('.vgbc-loi-khac').html(chip('err', loi, 1)); return; }
				frm.set_value('ngan_hang_bin', bin);
				frm.set_value('ngan_hang_hien_thi', ten);
			});
			$k.on('input', '.vgbc-tim', function () {
				var kq = VGB_CD.timNganHang(this.value, ds);
				$k.find('.vgbc-kq').html(kq.map(function (n) {
					return '<a href="#" data-bin="' + esc(n.bin) + '"><b>' + esc(n.ten) + '</b><small>' + esc(n.ma) + ' · BIN ' + esc(n.bin) + '</small></a>';
				}).join('') || (this.value.trim() ? '<small>Không thấy ngân hàng nào khớp.</small>' : ''));
			});
			$k.on('click', '[data-bin]', function (e) {
				e.preventDefault();
				var n = VGB_CD.nganHangTheoBin(ds, $(this).attr('data-bin'));
				if (!n) return;
				frm.set_value('ngan_hang_bin', n.bin);
				frm.set_value('ngan_hang_hien_thi', n.ten);
			});
		}
		if (frm.__vgb_nh) { ve(frm.__vgb_nh); return; }
		$k.html('<div class="vgbc-chips" style="margin:6px 0">' + dangLuu() + '</div><div class="vgbc-mo">Đang tải danh mục ngân hàng...</div>');
		// Tải hỏng (mất mạng, máy chủ lỗi): hiện mã đang lưu, báo rõ và có nút Thử
		// lại; muốn đổi ngân hàng thì phải tải được danh mục (Codex #435).
		function hong() {
			$k.html('<div class="vgbc-chips" style="margin:6px 0">' + dangLuu() + chip('err', 'Không tải được danh mục ngân hàng', 1) +
				'</div><button type="button" class="btn btn-xs btn-default vgbc-thu-lai">Thử lại</button>' +
				'<div class="vgbc-mo">Ngân hàng đang lưu vẫn dùng bình thường. Muốn đổi thì bấm Thử lại để chọn từ danh mục.</div>');
			$k.on('click', '.vgbc-thu-lai', function () { veNganHang(frm); });
		}
		frappe.call({ method: 'vagabond.tai_khoan.danh_sach' }).then(function (r) {
			var ds = ((r && r.message) || {}).ngan_hang;
			if (!ds || !ds.length) return hong();
			frm.__vgb_nh = ds;
			ve(frm.__vgb_nh);
		}, hong);
	}

	function veDuLieuApp(frm) {
		var f = frm.fields_dict.html_du_lieu_app;
		if (!f) return;
		var t = VGB_CD.tomTat(frm.doc);
		var lnk = function (d) { return '<a class="vgbc-lnk" target="_blank" rel="noopener" href="' + esc(d) + '">Sửa ở app ›</a>'; };
		var html = '<div class="vgbc-cards">' + t.the.map(function (c) {
			return '<div class="vgbc-card"><b>' + esc(c.ten) + '</b><div class="p">' + (c.loi ? chip('err', c.phu, 1) : esc(c.phu)) + '</div>' +
				(c.dong || []).map(function (r) {
					return '<div class="vgbc-r"><span>' + esc(r.trai) + '</span><span class="g">' + esc(r.giua) + '</span>' + chip(r.trang, r.nhan, 1) + '</div>';
				}).join('') +
				(c.con ? '<div class="vgbc-r"><small>và ' + c.con + ' tài khoản, điểm bán nữa. Xem đủ ở app.</small></div>' : '') +
				(c.chip && c.chip.length ? '<div class="vgbc-chips" style="gap:6px">' + c.chip.map(function (x) { return chip('no', x, 1); }).join('') + '</div>' : '') +
				'<div>' + lnk(c.duong) + '</div></div>';
		}).join('') + '</div><div style="margin-top:12px">' + t.dong.map(function (r) {
			return '<div class="vgbc-dong"><span>' + esc(r.ten) + ' <small>· ' + (r.loi ? '' : esc(r.ghi)) + '</small>' +
				(r.loi ? chip('err', r.ghi, 1) : '') + '</span>' + lnk(r.duong) + '</div>';
		}).join('') + '</div>';
		f.$wrapper.html(html);
	}

	frappe.ui.form.on('Vagabond Settings', {
		onload(frm) {
			if (!document.getElementById('vgb-cd-css')) $('<style id="vgb-cd-css"></style>').text(CSS).appendTo('head');
		},
		refresh(frm) {
			$(frm.wrapper).addClass('vgb-cd');
			vgb_nap_cd_chung().then(function () {
				veThanh(frm);
				veChipMuc(frm);
				veMatKhau(frm);
				veChipChon(frm);
				veDuLieuApp(frm);
			}, function (e) { frappe.show_alert({ message: e.message, indicator: 'orange' }); });
		},
		diem_chu_ky(frm) { vgb_nap_cd_chung().then(function () { veChipChon(frm); }); },
		ngan_hang_bin(frm) { vgb_nap_cd_chung().then(function () { veChipChon(frm); }); },
	});
	// Chỉ cho ca kiểm node (hanh_vi/cai_dat_568.js); trên trình duyệt không có module.
	if (typeof module !== 'undefined' && module.exports) module.exports._desk = { veNganHang: veNganHang, veChipMuc: veChipMuc, veThanh: veThanh };
})();
