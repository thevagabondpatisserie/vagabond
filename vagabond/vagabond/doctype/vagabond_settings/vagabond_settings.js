// v562 (#410): nút cho phần Bắn tin vào nhóm Zalo. Chỉ quản trị mở được
// Cài đặt này, máy chủ cũng kiểm lại quyền ở từng hàm.
// v562 Codex #417, #423: Loại tin và Chủ đề chỉ chọn từ danh mục (hai ô này
// read_only, không gõ tay được); máy chủ vẫn kiểm lại lúc lưu.
const ZALO_DANH_MUC = {
	loai_tin: ['thong_bao', 'viec', 'canh_bao', 'ban_tin', 'phat_hanh'],
	chu_de: ['kho', 'san_xuat', 'cong_no', 'ban_hang', 'don_web', 'dat_ban', 'phat_hanh'],
};
// v568: anh Việt 04/10/2026, kèm ảnh hộp Chọn loại tin chỉ có mã ban_tin,
// canh_bao...: *"không có subtext để biết tin đó là tin gì"*. Mã vẫn là giá trị
// lưu (máy chủ kiểm theo mã); người dùng thấy tên, biểu tượng và một dòng giải
// thích. Tên và biểu tượng loại tin phải trùng kenh_zalo.LOAI (ca kiểm chốt).
const ZALO_NHAN = {
	loai_tin: {
		thong_bao: ['ℹ️', 'Thông báo', 'Tin cho biết, không cần làm gì: chứng từ đã ghi sổ, đơn đã giao.'],
		viec: ['✅', 'Việc cần làm', 'Có việc chờ người trong nhóm xử lý, ví dụ khoản trả trước chờ duyệt. Việc xong trước giờ gửi thì máy bỏ, không nhắc nữa.'],
		canh_bao: ['🚨', 'Cảnh báo', 'Sự cố cần xử lý ngay. Đây là loại DUY NHẤT vẫn gửi trong giờ im của nhóm.'],
		ban_tin: ['📊', 'Bản tin', 'Báo cáo định kỳ, ví dụ số liệu cuối ngày. Tin gom sau giờ im vẫn tới đủ, không phụ thuộc lựa chọn này.'],
		phat_hanh: ['🚀', 'Phát hành', 'App có bản mới: thêm gì, bộ phận cần làm gì.'],
	},
	chu_de: {
		kho: ['📦', 'Kho', 'Nhập, xuất, điều chuyển, kiểm kê, ngưỡng tồn.'],
		san_xuat: ['🧑‍🍳', 'Sản xuất', 'Phiếu yêu cầu, lệnh sản xuất, bảng bếp.'],
		cong_no: ['💳', 'Công nợ', 'Phải thu, phải trả, khoản chờ duyệt chi.'],
		ban_hang: ['🎂', 'Bán hàng', 'Đơn bán, hoá đơn, chốt ca quầy.'],
		don_web: ['🌐', 'Đơn web', 'Đơn đặt bánh trên trang web.'],
		dat_ban: ['🪑', 'Đặt bàn', 'Khách đặt bàn tại cửa hàng.'],
		phat_hanh: ['🚀', 'Phát hành app', 'Tin bản mới của app.'],
	},
};
function zalo_chon(frm, cdt, cdn, truong) {
	const row = locals[cdt][cdn];
	const dang = (row[truong] || '').split(/[,;]/).map(s => s.trim()).filter(Boolean);
	const nhan = ZALO_NHAN[truong];
	const e = frappe.utils.escape_html;
	const html = '<div class="vgbz-goi">Không tích ô nào là nhóm nhận <b>tất cả</b> ' +
		(truong === 'loai_tin' ? 'loại tin.' : 'chủ đề.') + '</div>' +
		ZALO_DANH_MUC[truong].map(v => {
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

// ====================================================================
// v568: quy hoạch lại trang Cài đặt Vagabond.
//
// Anh Việt 04/10/2026, kèm hai ảnh trang Cài đặt: *"những phần mã code ở đầu
// này có ẩn đi hay thu gọn lại được không? Chữ hướng dẫn thì không có dấu
// tiếng Việt. Quy hoạch lại thành các field, các ô, chip lọc, chip chọn, chip
// trạng thái... sao cho khoa học nhất, logic nhất"*.
//
// Phần dưới chỉ đổi CÁCH HIỂN THỊ. Không ô nào đổi tên, không giá trị nào đổi
// cách lưu: công tắc vẫn lưu 0/1, chip chọn vẫn lưu đúng giá trị cũ của ô Chọn
// (ví dụ "Cuon chieu"), chip ngân hàng vẫn ghi mã BIN vào ô cũ.
//
// Phép THUẦN gom trong VGB_CD để kiểm thử bằng node không cần Frappe
// (khung/kiem_thu/hanh_vi/cai_dat_568.js). Phần chạm form nằm cuối tệp.
// ====================================================================
var VGB_CD = (function () {
	function boDau(s) {
		return String(s == null ? '' : s).toLowerCase()
			.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd');
	}
	function co(v) { return v !== undefined && v !== null && String(v).trim() !== ''; }
	function bat(v) { return parseInt(v, 10) === 1; }
	function docJson(s) {
		if (!co(s)) return null;
		try { return JSON.parse(s); } catch (e) { return undefined; }
	}

	// Ô Chọn lưu giá trị không dấu từ trước; chip chỉ hiện nhãn có dấu.
	var NHAN_CHON = {
		diem_chu_ky: [['Tat', 'Không hết hạn'], ['Cuon chieu', 'Cuốn chiếu N tháng'], ['Cuoi nam', 'Chốt cuối năm'], ['Ngay ky niem', 'Ngày kỷ niệm']],
	};
	// Codex #433: danh mục ngân hàng lấy từ MỘT nguồn là tai_khoan.NGAN_HANG
	// (gọi vagabond.tai_khoan.danh_sach), không giữ danh sách thứ hai ở đây.
	function nganHangTheoBin(ds, bin) {
		bin = String(bin || '').trim();
		return (ds || []).filter(function (n) { return n.bin === bin; })[0] || null;
	}
	// Cùng luật với máy chủ tai_khoan.kiem_cap_ngan_hang (ca kiểm chốt hai bên khớp).
	function kiemCapNganHang(bin, ten) {
		bin = String(bin || '').trim(); ten = String(ten || '').trim();
		if (!bin) return ten ? 'Có Tên ngân hàng thì phải có Mã BIN (để trống cả hai là dùng MB mặc định).' : null;
		if (!/^\d{6}$/.test(bin)) return 'Mã BIN ngân hàng phải đúng 6 chữ số.';
		if (!ten) return 'Có Mã BIN thì phải có Tên ngân hàng hiện cho khách.';
		return null;
	}
	function timNganHang(tu, ds) {
		var cac = boDau(tu).split(/\s+/).filter(Boolean);
		if (!cac.length) return [];
		return (ds || []).filter(function (n) {
			var s = boDau(n.ten + ' ' + n.ma + ' ' + n.bin);
			return cac.every(function (c) { return s.indexOf(c) >= 0; });
		}).slice(0, 8);
	}

	// Mỗi kết nối: đủ các ô "can" (hoặc đủ một nhóm trong "canMot") là đã khai;
	// có ô "bat" mà đang tắt thì vàng. "toi" là ô để nhảy tới khi bấm chip.
	var KET_NOI = [
		{ ten: 'Hoá đơn điện tử m-invoice', can: ['minvoice_host', 'minvoice_username', 'minvoice_password'], toi: 'minvoice_host', muc: 'sec_minvoice' },
		// Codex #433: đủ mọi khe khoá mà sepay._cac_khoa() chấp nhận; webhook chạy được
		// chỉ với khe thứ hai hay thứ ba thì vẫn là đã khai.
		{ ten: 'SePay ngân hàng', canMot: [['sepay_khoa'], ['sepay_khoa_2'], ['sepay_hmac'], ['sepay_hmac_2'], ['sepay_hmac_3']], bat: 'sepay_bat', toi: 'sepay_bat', muc: 'sec_sepay' },
		{ ten: 'Pancake', can: ['pancake_api_key', 'pancake_shop_id'], toi: 'pancake_api_key', muc: 'sec_pancake' },
		// Codex #433 vòng 3: "đã khai" phải đủ MỌI ô máy chủ đòi, không thì chip xanh
		// cho một cấu hình chắc chắn hỏng. Mỗi dòng ghi chỗ máy chủ kiểm.
		// van_don.py: key(ahamove_api_key) and ahamove_base and ahamove_mobile
		{ ten: 'Ahamove', can: ['ahamove_api_key', 'ahamove_mobile', 'ahamove_base'], toi: 'ahamove_api_key', muc: 'sec_aha' },
		{ ten: 'Goong bản đồ', can: ['goong_api_key'], toi: 'goong_api_key', muc: 'sec_goong' },
		// van_don._greensm_dat_don: client_id, client_secret và token_url. be_token
		// không có dòng Python nào đọc, nên không làm chip xanh được.
		{ ten: 'GreenSM', can: ['greensm_client_id', 'greensm_client_secret', 'greensm_token_url'], toi: 'greensm_client_id', muc: 'sec_gsm' },
		// Codex #435 vòng 7: kenh_zalo.chon_nhom bỏ dòng tắt hoặc thiếu mã chat; không
		// còn nhóm nào nhận thì mọi tin tự động bị bỏ âm thầm, nên phải có ít nhất
		// một nhóm đang bật và có mã chat mới là đã khai.
		{ ten: 'Zalo bắn tin nhóm', can: ['zalo_bot_token'], canNhom: 'zalo_nhom', bat: 'zalo_bot_bat', toi: 'zalo_bot_bat', muc: 'sec_zalo_bot' },
		// zalo.py: làm mới token cần App ID, App Secret và Refresh Token.
		// Codex #435: zalo.gui_tin từ chối khi không có mã mẫu ZNS, nên phải có ít
		// nhất một mẫu (OTP đăng nhập, đòi tiền, trừ điểm) mới là đã khai.
		{ ten: 'Zalo ZNS gửi khách', can: ['zalo_app_id', 'zalo_app_secret', 'zalo_refresh_token'],
			canMot: [['zns_template_otp'], ['zns_template_thanh_toan'], ['zns_template_diem']], toi: 'zalo_app_id', muc: 'sec_zalo' },
		// whatsapp.gui_mau từ chối khi không có tên mẫu; nơi gọi duy nhất dùng mẫu thanh toán.
		{ ten: 'WhatsApp', can: ['wa_phone_id', 'wa_token', 'wa_template_thanh_toan'], toi: 'wa_phone_id', muc: 'sec_wa' },
		// thong_bao.py gửi bằng khoá riêng VAPID; thiếu là "chua co khoa VAPID".
		{ ten: 'Thông báo đẩy', can: ['push_khoa_cong_khai', 'push_khoa_rieng'], toi: 'push_khoa_cong_khai', muc: 'sec_push' },
		{ ten: 'Meta Pixel', can: ['meta_pixel_id'], toi: 'meta_pixel_id', muc: 'sec_meta_pixel' },
		{ ten: 'Máy in QZ Tray', can: ['qz_chung_thu', 'qz_khoa_rieng'], toi: 'qz_chung_thu', muc: 'sec_qz' },
		{ ten: 'Trợ lý hướng dẫn', can: ['tro_ly_khoa'], bat: 'tro_ly_bat', toi: 'tro_ly_bat', muc: 'sec_tro_ly' },
		{ ten: 'Dịch Gemini', can: ['gemini_api_key'], toi: 'gemini_api_key', muc: 'sec_ai' },
	];

	function duKhai(doc, k) {
		if (k.can && !k.can.every(function (f) { return co(doc[f]); })) return false;
		if (k.canMot && !k.canMot.some(function (nh) { return nh.every(function (f) { return co(doc[f]); }); })) return false;
		// Cùng luật với kenh_zalo.chon_nhom: dòng phải đang bật và có mã chat.
		if (k.canNhom && !(doc[k.canNhom] || []).some(function (r) { return r && bat(r.bat) && co(r.chat_id); })) return false;
		return true;
	}

	// Trạng thái: ok xanh, no xám (chưa khai), off vàng (khai rồi nhưng tắt), err đỏ.
	function tinhTrang(doc, bayGio) {
		doc = doc || {};
		var ra = KET_NOI.map(function (k) {
			var tr = !duKhai(doc, k) ? 'no' : (k.bat && !bat(doc[k.bat]) ? 'off' : 'ok');
			var ghi = tr === 'no' ? 'chưa khai' : (tr === 'off' ? 'đã khai, đang tắt' : 'đã khai');
			return { ten: k.ten, trang: tr, ghi: ghi, toi: k.toi, muc: k.muc };
		});
		// Còi báo động: hú trong 24 giờ qua là đỏ, kể cả khi đã khai đủ.
		var luc = co(doc.email_bao_dong_lan_cuoi) ? Date.parse(String(doc.email_bao_dong_lan_cuoi).replace(' ', 'T')) : NaN;
		var gio = isNaN(luc) ? null : Math.floor(((bayGio || Date.now()) - luc) / 3600000);
		var coDuong = co(doc.email_canh_bao) || co(doc.webhook_bao_dong);
		var thu = { ten: 'Thư cảnh báo', toi: 'email_canh_bao', muc: 'sec_gui_thu' };
		if (gio !== null && gio >= 0 && gio < 24) {
			thu.trang = 'err'; thu.ghi = 'hú còi ' + (gio === 0 ? 'chưa tới 1 giờ' : gio + ' giờ') + ' trước';
		} else if (coDuong) {
			thu.trang = 'ok'; thu.ghi = 'đã khai';
		} else {
			thu.trang = 'no'; thu.ghi = 'chưa khai';
		}
		ra.push(thu);
		return ra;
	}

	// Thứ tự HIỆN chip trên thanh: việc cần để ý lên trước (đỏ, vàng, xám rồi mới
	// xanh), giữ nguyên thứ tự gốc trong cùng một màu. Thanh chỉ hiện hai dòng
	// (Codex #435), nên chip cần xử lý phải nằm trong hai dòng đó.
	var THU_TU_MAU = { err: 0, off: 1, no: 2, ok: 3 };
	function xepTinhTrang(ds) {
		return (ds || []).map(function (t, i) { return { t: t, i: i }; }).sort(function (a, b) {
			return (THU_TU_MAU[a.t.trang] - THU_TU_MAU[b.t.trang]) || (a.i - b.i);
		}).map(function (x) { return x.t; });
	}

	// Chip trên đầu từng mục: kết nối của mục đó, hoặc số công tắc đang bật.
	var CONG_TAC_MUC = { sec_vgb_tu_dong: ['tu_xuat_hddt', 'tu_ghi_so_bat', 'hang_tang_xuat_kho_that'] };
	function tinhTrangMuc(doc, bayGio) {
		var ra = {};
		tinhTrang(doc, bayGio).forEach(function (t) { ra[t.muc] = { trang: t.trang, ghi: t.ghi }; });
		Object.keys(CONG_TAC_MUC).forEach(function (m) {
			var ds = CONG_TAC_MUC[m];
			var n = ds.filter(function (f) { return bat((doc || {})[f]); }).length;
			ra[m] = { trang: n ? 'ok' : 'no', ghi: 'Đang bật ' + n + '/' + ds.length };
		});
		return ra;
	}

	// Codex #433 (AGENTS.md điều 17): khối chỉ đọc không kéo dài vô hạn. Hiện vài
	// dòng đầu, phần còn lại thành một dòng "và N nữa".
	var TOI_DA_DONG = 3;
	function catDong(the) {
		if (the.dong && the.dong.length > TOI_DA_DONG) {
			the.con = the.dong.length - TOI_DA_DONG;
			the.dong = the.dong.slice(0, TOI_DA_DONG);
		}
		return the;
	}

	function duoiSo(s) {
		s = String(s || '').trim();
		return s.length > 4 ? '…' + s.slice(-4) : s;
	}

	// Dữ liệu app tự ghi: mỗi ô thành một thẻ hoặc một dòng tóm tắt, kèm
	// đường mở đúng màn sửa trong app. Ô hỏng định dạng thì báo đỏ, không nổ.
	function tomTat(doc) {
		doc = doc || {};
		var diem = docJson(doc.vgb_diem_ban);
		var tenDiem = {};
		(Array.isArray(diem) ? diem : []).forEach(function (d) { if (d && d.ma) tenDiem[d.ma] = d.ten || d.ma; });
		function tenNguon(n) {
			n = String(n || '');
			if (n.indexOf('@diem:') === 0) return tenDiem[n.slice(6)] || ('Điểm ' + n.slice(6));
			if (n === '@phieu_cong_no') return 'Phiếu đòi nợ khách sỉ';
			return n;
		}
		var the = [];
		var dong = [];

		var tk = docJson(doc.vgb_tai_khoan_nhan);
		var tkThe = { ten: 'Tài khoản nhận chuyển khoản', duong: '/tai-khoan-ke-toan', dong: [] };
		if (tk === undefined) { tkThe.phu = 'Dữ liệu hỏng định dạng, mở app để khai lại'; tkThe.loi = 1; }
		else if (!tk) { tkThe.phu = 'Chưa khai, mọi điểm bán dùng tài khoản mặc định của máy'; }
		else {
			var md = tk.mac_dinh || {};
			tkThe.phu = 'Mặc định: ' + (md.bank || '?') + ' ' + duoiSo(md.stk);
			(tk.theo_nguon || []).forEach(function (x) {
				tkThe.dong.push({ trai: tenNguon(x.nguon), giua: (x.bank || '') + ' ' + duoiSo(x.stk),
					trang: (x.dung === undefined || bat(x.dung)) ? 'ok' : 'no',
					nhan: (x.dung === undefined || bat(x.dung)) ? 'Dùng' : 'Tắt' });
			});
		}
		the.push(catDong(tkThe));

		var dbThe = { ten: 'Điểm bán', duong: '/diem-ban', dong: [] };
		if (diem === undefined) { dbThe.phu = 'Dữ liệu hỏng định dạng'; dbThe.loi = 1; }
		else if (!diem || !diem.length) { dbThe.phu = 'Chưa khai'; }
		else {
			var coQuay = diem.filter(function (d) { return bat(d.co_quay); }).length;
			dbThe.phu = diem.length + ' điểm, ' + coQuay + ' điểm có quầy';
			diem.forEach(function (d) {
				dbThe.dong.push({ trai: d.ten || d.ma, giua: d.ma || '', trang: bat(d.co_quay) ? 'ok' : 'no', nhan: bat(d.co_quay) ? 'Có quầy' : 'Không quầy' });
			});
		}
		the.push(catDong(dbThe));

		var pt = docJson(doc.vgb_pt_thanh_toan_ds);
		var ptThe = { ten: 'Phương thức thanh toán', duong: '/phuong-thuc-thanh-toan', chip: [] };
		if (pt === undefined) { ptThe.phu = 'Dữ liệu hỏng định dạng'; ptThe.loi = 1; }
		else if (!pt || !pt.length) { ptThe.phu = 'Chưa khai'; }
		else {
			var dangBat = pt.filter(function (x) { return x && (x.bat === undefined || bat(x.bat)); });
			ptThe.phu = pt.length + ' phương thức, ' + dangBat.length + ' đang bật';
			dangBat.slice(0, 6).forEach(function (x) { ptThe.chip.push(x.nhan || x.ten || ''); });
			if (dangBat.length > 6) ptThe.chip.push('+' + (dangBat.length - 6));
		}
		the.push(ptThe);

		function demDs(o, ten, donVi, duong) {
			var v = docJson(doc[o]);
			var r = { ten: ten, duong: duong || '/phan-he-cai-dat', o: o };
			if (v === undefined) {
				// Có ô từ trước lưu dạng chữ thường (ví dụ danh sách mã điểm), không phải mã hỏng.
				r.ghi = String(doc[o]).slice(0, 60);
			} else if (v === null || (Array.isArray(v) && !v.length) || (typeof v === 'object' && !Object.keys(v).length)) {
				r.ghi = 'Chưa khai'; r.trong = 1;
			} else if (Array.isArray(v)) {
				r.ghi = v.length + ' ' + donVi;
			} else {
				r.ghi = 'Đã khai';
			}
			return r;
		}
		dong.push(demDs('vgb_may_in', 'Danh sách máy in', 'máy', '/may-in'));
		dong.push(demDs('vgb_mau_in_quay', 'Mẫu in của quầy', 'mẫu', '/mau-in'));
		dong.push(demDs('vgb_can_tem', 'Cân in tem', 'cân'));
		var nhip = docJson(doc.vgb_pancake_nhip);
		var nhipDong = { ten: 'Nhịp kéo đơn Pancake', duong: '/phan-he-cai-dat', o: 'vgb_pancake_nhip' };
		if (nhip && typeof nhip === 'object') {
			nhipDong.ghi = co(nhip.loi) ? 'Lần gần nhất báo lỗi' : ('Kéo được lần cuối ' + (nhip.ok_luc_nao || '?'));
			if (co(nhip.loi)) nhipDong.loi = 1;
		} else { nhipDong.ghi = 'Chưa chạy'; nhipDong.trong = 1; }
		dong.push(nhipDong);
		dong.push(demDs('vgb_hddt_quay', 'Điểm bán tự xuất hoá đơn điện tử', 'điểm'));
		dong.push(demDs('vgb_kpi_cau_hinh', 'Cấu hình KPI', 'mục', '/kpi-bang-chi-tieu'));
		dong.push(demDs('vgb_kho_sap', 'Ngưỡng kho', 'mục'));
		dong.push(demDs('vgb_nhap_khach_tien_do', 'Tiến độ nhập danh sách khách', 'đợt'));
		var qbm = { gioi_han: 'Giới hạn theo quyền', tat_ca: 'Ai cũng bỏ được', khong: 'Không ai bỏ được' };
		dong.push({ ten: 'Quyền bỏ món khỏi bill', duong: '/quyen-quay', o: 'vgb_quyen_bo_mon',
			ghi: co(doc.vgb_quyen_bo_mon) ? (qbm[doc.vgb_quyen_bo_mon] || doc.vgb_quyen_bo_mon) : 'Chưa khai', trong: co(doc.vgb_quyen_bo_mon) ? 0 : 1 });
		return { the: the, dong: dong };
	}

	// Nhảy tới một ô: mở đúng tab chứa ô, mở mục đang thu gọn, rồi mới cuộn.
	// Codex #433 vòng 3. Frappe 16.36 tự làm hai bước đầu trong scroll_to_field,
	// nhưng tự làm ở đây thì không phụ thuộc phiên bản Frappe, và có ca kiểm chạy được.
	function moToi(frm, fn) {
		var f = frm.get_field ? frm.get_field(fn) : (frm.fields_dict || {})[fn];
		if (!f) return false;
		if (f.tab && f.tab.is_active && !f.tab.is_active()) f.tab.set_active();
		if (f.section && f.section.is_collapsed && f.section.is_collapsed()) f.section.collapse(false);
		frm.scroll_to_field(fn);
		return true;
	}

	// Ô tìm: khớp mọi từ (bỏ dấu) trong nhãn, mô tả, tên tab, tên mục.
	function timTruong(tu, ds) {
		var cac = boDau(tu).split(/\s+/).filter(Boolean);
		if (!cac.length) return [];
		return (ds || []).map(function (x) {
			var nhan = boDau(x.nhan), toan = nhan + ' ' + boDau(x.mo) + ' ' + boDau(x.tab) + ' ' + boDau(x.muc);
			if (!cac.every(function (c) { return toan.indexOf(c) >= 0; })) return null;
			var diem = 0;
			cac.forEach(function (c) { if (nhan.indexOf(c) >= 0) diem += 10; });
			if (nhan.indexOf(cac[0]) === 0) diem += 5;
			return { x: x, diem: diem };
		}).filter(Boolean).sort(function (a, b) { return b.diem - a.diem; }).slice(0, 8).map(function (r) { return r.x; });
	}

	return { boDau: boDau, tinhTrang: tinhTrang, tinhTrangMuc: tinhTrangMuc, tomTat: tomTat, timTruong: timTruong,
		NHAN_CHON: NHAN_CHON, KET_NOI: KET_NOI, docJson: docJson, nganHangTheoBin: nganHangTheoBin, timNganHang: timNganHang, moToi: moToi, xepTinhTrang: xepTinhTrang, kiemCapNganHang: kiemCapNganHang,
		ZALO_NHAN: ZALO_NHAN, ZALO_DANH_MUC: ZALO_DANH_MUC };
})();
if (typeof module !== 'undefined' && module.exports) module.exports = VGB_CD;

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
			veThanh(frm);
			veChipMuc(frm);
			veMatKhau(frm);
			veChipChon(frm);
			veDuLieuApp(frm);
		},
		diem_chu_ky(frm) { veChipChon(frm); },
		ngan_hang_bin(frm) { veChipChon(frm); },
	});
	// Chỉ cho ca kiểm node (hanh_vi/cai_dat_568.js); trên trình duyệt không có module.
	if (typeof module !== 'undefined' && module.exports) module.exports._desk = { veNganHang: veNganHang, veChipMuc: veChipMuc, veThanh: veThanh };
})();
