/* Phần dùng CHUNG cho trang Cài đặt Vagabond trên Desk và màn "Cài đặt lõi và API"
 * trên app (v570).
 *
 * Anh Việt 04/10/2026: *"Mỗi lần em thêm gì trong trang này thì phải thêm cả
 * trên bản desk và bản app."* Nên mọi phép quyết định nội dung (chip tình trạng
 * kết nối, chip đầu mục, thẻ tóm tắt dữ liệu app tự ghi, ô tìm cài đặt, nhãn và
 * giải thích loại tin Zalo, tìm ngân hàng) nằm ở MỘT tệp này. Desk nạp nó trong
 * vagabond_settings.js, app nạp nó trong bep/51-cai-dat-loi.js. Sửa một chỗ là
 * cả hai nơi đổi theo.
 *
 * Tệp được nạp bằng thẻ script có thể hai lần trong một trang, nên chỉ dùng var
 * và không ghi đè khi đã có.
 */
if (typeof VGB_CD === 'undefined' || !VGB_CD || !VGB_CD.tinhTrang) {
// v562 Codex #417, #423: Loại tin và Chủ đề chỉ chọn từ danh mục (hai ô này
// read_only, không gõ tay được); máy chủ vẫn kiểm lại lúc lưu.
var VGB_ZALO_DANH_MUC = {
	loai_tin: ['thong_bao', 'viec', 'canh_bao', 'ban_tin', 'phat_hanh'],
	chu_de: ['kho', 'san_xuat', 'cong_no', 'ban_hang', 'don_web', 'dat_ban', 'phat_hanh'],
};
// v568: anh Việt 04/10/2026, kèm ảnh hộp Chọn loại tin chỉ có mã ban_tin,
// canh_bao...: *"không có subtext để biết tin đó là tin gì"*. Mã vẫn là giá trị
// lưu (máy chủ kiểm theo mã); người dùng thấy tên, biểu tượng và một dòng giải
// thích. Tên và biểu tượng loại tin phải trùng kenh_zalo.LOAI (ca kiểm chốt).
var VGB_ZALO_NHAN = {
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
	var ZALO_DANH_MUC = VGB_ZALO_DANH_MUC, ZALO_NHAN = VGB_ZALO_NHAN;
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

	// v579: anh Việt 06/10/2026, kèm ảnh bảng Nhóm nhận tin trên Desk chật nửa
	// cột, chỉ thấy "ERP ...", "zgr-d...", "thong...": *"Lỗi hiển thị, quá khó để
	// nhập liệu"*. Mỗi nhóm thành một thẻ đọc được, không hiện mã. Một nguồn cho
	// cả Desk và app.
	function tachMa(s) { return String(s || '').split(/[,;]/).map(function (x) { return x.trim(); }).filter(Boolean); }
	function tenMaZalo(cot, ma) { return ((ZALO_NHAN[cot] || {})[ma] || ['', ma])[1]; }
	function theNhomZalo(r) {
		r = r || {};
		var lt = tachMa(r.loai_tin).map(function (x) { return tenMaZalo('loai_tin', x); });
		var cd = tachMa(r.chu_de).map(function (x) { return tenMaZalo('chu_de', x); });
		var coNhom = co(r.chat_id), bat = parseInt(r.bat, 10) === 1;
		return {
			ten: co(r.ten_nhom) ? String(r.ten_nhom).trim() : 'Nhóm chưa đặt tên',
			loai: lt.length ? lt.join(', ') : 'Mọi loại tin',
			chu_de: cd.length ? cd.join(', ') : 'Mọi chủ đề',
			im: co(r.im_tu) && co(r.im_den) ? 'Từ ' + r.im_tu + ' đến ' + r.im_den + ' chỉ gửi Cảnh báo, tin khác gom gửi sau' : 'Không đặt giờ im',
			trang: !coNhom ? 'no' : (bat ? 'ok' : 'off'),
			ghi: !coNhom ? 'Chưa chọn nhóm Zalo' : (bat ? 'Đang nhận tin' : 'Đang tắt'),
			guiThu: coNhom,
		};
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
		ZALO_NHAN: ZALO_NHAN, ZALO_DANH_MUC: ZALO_DANH_MUC, theNhomZalo: theNhomZalo, tachMa: tachMa };
})();

if (typeof window !== 'undefined') window.VGB_CD = VGB_CD;
}
if (typeof module !== 'undefined' && module.exports) module.exports = VGB_CD;
