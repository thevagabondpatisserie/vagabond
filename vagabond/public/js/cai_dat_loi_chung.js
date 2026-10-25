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
// v596: điều kiện nạp lại dựa trên tongHop, hàm mới nhất; trang còn giữ bản cũ
// trong bộ nhớ (chưa tải lại sau deploy) vẫn nạp được bản mới.
// v604: thêm Tin nhận; điều kiện nạp lại đổi sang hàm mới nhất (tinTheoBoPhan).
if (typeof VGB_CD === 'undefined' || !VGB_CD || !VGB_CD.tinTheoBoPhan) {
// v562 Codex #417, #423: Loại tin và Chủ đề chỉ chọn từ danh mục (hai ô này
// read_only, không gõ tay được); máy chủ vẫn kiểm lại lúc lưu.
var VGB_ZALO_DANH_MUC = {
	loai_tin: ['thong_bao', 'viec', 'canh_bao', 'ban_tin', 'phat_hanh'],
	chu_de: ['kho', 'san_xuat', 'cong_no', 'ban_hang', 'hoa_don', 'don_web', 'dat_ban', 'phat_hanh', 'he_thong'],
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
		ban_hang: ['🎂', 'Bán hàng', 'Đơn bán, chốt ca quầy.'],
		// v602: tách khỏi Bán hàng để chuông kẹt hoá đơn vào đúng nhóm kế toán.
		hoa_don: ['🧾', 'Hoá đơn', 'Đơn chưa ghi sổ được, hoá đơn điện tử chưa xuất. Nên chọn kèm loại Cảnh báo.'],
		don_web: ['🌐', 'Đơn web', 'Đơn đặt bánh trên trang web.'],
		dat_ban: ['🪑', 'Đặt bàn', 'Khách đặt bàn tại cửa hàng.'],
		phat_hanh: ['🚀', 'Phát hành app', 'Tin bản mới của app.'],
		// v597: còi báo động thư hỏng đi Zalo thay webhook Lark nhóm quản trị.
		he_thong: ['🛠️', 'Hệ thống', 'Sự cố máy chủ, ví dụ thư không gửi được. Nên chọn kèm loại Cảnh báo.'],
	},
};
// v604: anh Việt 18/10/2026 bỏ thư cảnh báo nội bộ, mọi tin đi nhóm Zalo; mỗi nhóm
// tích đúng những tin cần nhận. Bản sao của kenh_zalo.TIN (mã -> [bộ phận, tên,
// giải thích]); ca thu_tin_zalo_604 so từng chữ với bản Python, sửa một bên phải
// sửa bên kia. Mã chỉ là giá trị lưu, người dùng chỉ thấy tên và giải thích.
var VGB_ZALO_BO_PHAN = ['Ban giám đốc', 'Hoá đơn, kế toán', 'Bán hàng, cửa hàng', 'Bếp', 'Thu mua', 'Kho', 'Hệ thống'];
var VGB_ZALO_TIN = {
	bgd_bao_cao_ngay: ['Ban giám đốc', 'Báo cáo cuối ngày (23:30)', '23:30 mỗi tối: doanh thu, giảm giá, sửa huỷ, điểm cần để ý. Nhóm nhận đừng đặt giờ im lúc 23:30.'],
	hd_ket_ghi_so: ['Hoá đơn, kế toán', 'Kẹt ghi sổ, kẹt hoá đơn cuối ngày', '20 và 45 phút sau giờ chạy cuối ngày, và 07:30 sáng hôm sau, còn đơn chưa ghi sổ.'],
	hd_don_chua_ghi_so: ['Hoá đơn, kế toán', 'Đơn chưa ghi sổ còn sót lúc 23:55', '23:55 mỗi ngày, còn đơn bán chưa ghi sổ được.'],
	hd_hddt_sot: ['Hoá đơn, kế toán', 'Đã ghi sổ mà chưa xuất hoá đơn điện tử', '23:55 mỗi ngày, còn tờ đã ghi sổ mà chưa có hoá đơn điện tử.'],
	hd_giu_ngay_cu: ['Hoá đơn, kế toán', 'Hoá đơn ngày cũ bị giữ lại, không phát hành', 'Khi chuỗi cuối ngày giữ hoá đơn lại vì còn nợ ngày cũ chưa đối soát.'],
	hd_trung: ['Hoá đơn, kế toán', 'Đơn có hoá đơn trùng (doanh thu tính đôi)', '02:00 mỗi đêm, có đơn mang từ hai hoá đơn bán hàng trở lên.'],
	hd_dau_vao: ['Hoá đơn, kế toán', 'Hoá đơn đầu vào m-invoice tắc nhịp hoặc trùng', '08:25 mỗi sáng, hoá đơn mua vào chưa dựng được chứng từ hoặc có chứng từ trùng.'],
	kt_tra_truoc_erp: ['Hoá đơn, kế toán', 'Khoản trả trước chờ duyệt', 'Thu mua gửi một khoản đã trả trước khi lên ERP, chờ kế toán duyệt.'],
	kt_hoan_tien: ['Hoá đơn, kế toán', 'Yêu cầu hoàn tiền chờ chi', 'Sales gửi yêu cầu hoàn tiền cho khách, chờ kế toán chuyển khoản.'],
	kt_de_nghi_chi: ['Hoá đơn, kế toán', 'Đề nghị chi chờ duyệt hoặc bị trả lại', 'Đề nghị chi chuyển sang bước duyệt kế tiếp, hoặc bị trả về người lập.'],
	kt_tra_truoc_kiem: ['Hoá đơn, kế toán', 'Phiếu trả trước chờ kiểm', 'Có phiếu trả trước nhà cung cấp chờ kế toán kiểm tra.'],
	kt_diem_het_han: ['Hoá đơn, kế toán', 'Điểm khách hết hạn: máy tự dừng vì chạm trần', '05:00 sáng, số khách tới hạn đốt điểm vượt mức an toàn nên máy chưa đốt.'],
	kt_hop_dong_dc: ['Hoá đơn, kế toán', 'Hợp đồng vừa điều chỉnh', 'Sales vừa chốt một lần điều chỉnh hợp đồng so với bản gốc.'],
	kt_xuat_huy_gia_von: ['Hoá đơn, kế toán', 'Xuất huỷ đã ghi sổ, kèm giá vốn', 'Phiếu xuất huỷ vừa ghi sổ: kho, lý do, tên hàng và giá vốn đã trừ.'],
	kt_kiem_ke_lech: ['Hoá đơn, kế toán', 'Kiểm kê đã ghi sổ, kèm giá trị chênh lệch', 'Kiểm kê vừa điều chỉnh tồn: tên hàng lệch và giá trị chênh lệch đã vào sổ.'],
	kt_tien_chua_gan: ['Hoá đơn, kế toán', 'Tiền vào tài khoản công ty chưa gắn chứng từ (08:00)', '08:00 mỗi sáng: khoản tiền vào tài khoản chính công ty quá 24 giờ mà chưa thuộc đơn hay phiếu nào.'],
	bh_don_web_treo: ['Bán hàng, cửa hàng', 'Đơn web treo quá 30 phút chưa vào Pancake', 'Đơn đặt bánh trên web quá 30 phút mà chưa tạo được trên Pancake.'],
	bh_ton_web_loi: ['Bán hàng, cửa hàng', 'Lỗi kiểm tồn khi khách đặt web', 'Phép kiểm tồn bánh lỗi lúc khách đặt; Sales kiểm lại tồn trước khi xác nhận.'],
	bh_ahamove_huy: ['Bán hàng, cửa hàng', 'Tài xế Ahamove huỷ hoặc giao thất bại', 'Tài xế huỷ hoặc giao không được, vận đơn về Chờ giao để phân công lại.'],
	bh_dat_ban: ['Bán hàng, cửa hàng', 'Đặt bàn mới', 'Khách vừa gửi yêu cầu đặt bàn, chờ cửa hàng xác nhận.'],
	bh_dat_ban_xac_nhan: ['Bán hàng, cửa hàng', 'Đặt bàn đã xác nhận', 'Quản lý vừa xác nhận một đặt bàn: ngày giờ, tên, số điện thoại, số khách.'],
	bh_dat_ban_huy: ['Bán hàng, cửa hàng', 'Đặt bàn đã huỷ', 'Quản lý vừa huỷ một đặt bàn, kèm lý do đã báo khách.'],
	bh_dat_ban_sap_toi: ['Bán hàng, cửa hàng', 'Đặt bàn còn 3 giờ mà chưa xác nhận', 'Mỗi 15 phút: yêu cầu đặt bàn còn chờ xác nhận khi chỉ còn 3 giờ tới giờ khách đến.'],
	bh_thong_tin_hd_sai: ['Bán hàng, cửa hàng', 'Thông tin xuất hoá đơn sai, đơn chưa ghi sổ', 'm-invoice từ chối thông tin người mua (email, mã số thuế, tên): đơn nào, sai chỗ nào để Sales sửa.'],
	bh_tiec: ['Bán hàng, cửa hàng', 'Đăng ký tiệc mới', 'Khách vừa đăng ký vé tiệc, chờ cửa hàng xác nhận.'],
	bh_pancake_lech_tong: ['Bán hàng, cửa hàng', 'Đơn web lệch tổng tiền trên Pancake', 'Tổng tiền trên Pancake khác số máy chủ chốt; Sales kiểm trước khi gửi mã QR.'],
	bh_ahamove_phi: ['Bán hàng, cửa hàng', 'Không lấy được phí giao Ahamove', 'Trang đặt bánh không tính được phí giao vì Ahamove không trả lời.'],
	bh_don_web_moi: ['Bán hàng, cửa hàng', 'Đơn web mới đã vào Pancake', 'Khách vừa đặt trên web: giờ nhận, món, tổng tiền, miễn phí giao hay không.'],
	bep_ke_hoach_sx: ['Bếp', 'Kế hoạch sản xuất hôm nay (05:00)', '05:00 sáng, kế hoạch sản xuất trong ngày đã sẵn, bếp đọc rồi chốt.'],
	bep_lenh_sx_xuat_nvl: ['Bếp', 'Lệnh sản xuất đã xuất nguyên liệu', 'Phiếu sản xuất vừa ghi sổ: thành phẩm và nguyên liệu đã trừ kho.'],
	bep_ycsx_moi: ['Bếp', 'Yêu cầu sản xuất mới', 'Bộ phận vừa gửi yêu cầu sản xuất cho bếp: món, số lượng, ngày cần; cần trong hôm nay thì ghi GẤP.'],
	bep_ycsx_huy: ['Bếp', 'Yêu cầu sản xuất bị huỷ', 'Yêu cầu sản xuất đã gửi bếp vừa bị huỷ, bếp bỏ khỏi kế hoạch.'],
	bep_ycsx_ngay_mai: ['Bếp', 'Tổng yêu cầu sản xuất cho ngày mai (20:30)', '20:30 mỗi tối, một tin mỗi bếp: cộng món và số lượng của các yêu cầu cần ngày mai.'],
	tm_yeu_cau_mua: ['Thu mua', 'Yêu cầu mua hàng mới', 'Bộ phận vừa lập yêu cầu mua: tên hàng, số lượng, ngày cần.'],
	tm_don_mua_moi: ['Thu mua', 'Đơn mua hàng vừa đặt', 'Đơn mua vừa ghi sổ: nhà cung cấp, ngày hẹn về, tên hàng, tổng tiền.'],
	tm_don_mua_tre_hen: ['Thu mua', 'Đơn mua trễ hẹn chưa về đủ (08:00)', '08:00 mỗi sáng, đơn mua đã qua ngày hẹn mà hàng chưa về đủ.'],
	tm_hang_ve_chua_hoa_don: ['Thu mua', 'Hàng về quá 3 ngày chưa có hoá đơn (08:25)', '08:25 mỗi sáng, phiếu nhập đã ghi sổ quá 3 ngày mà chưa có hoá đơn mua.'],
	kho_nhap_cho_kiem: ['Kho', 'Phiếu nhập chờ kho đếm và ghi sổ', 'Có phiếu nhập còn nháp chờ kho đếm hàng rồi ghi sổ.'],
	kho_da_nhap: ['Kho', 'Đã nhập hàng vào kho', 'Phiếu nhập vừa ghi sổ: tên hàng, số lượng, lệch so với đơn mua, hạn lô.'],
	kho_da_chuyen: ['Kho', 'Đã chuyển hàng giữa kho', 'Phiếu điều chuyển vừa ghi sổ: kho đi, kho đến, tên hàng, số lượng.'],
	kho_da_nhan_chuyen: ['Kho', 'Kho nhận đã xác nhận hàng điều chuyển', 'Kho nhận vừa xác nhận số thực nhận; nhận thiếu thì báo kèm dòng lệch.'],
	kho_chuyen_chua_nhan: ['Kho', 'Hàng chuyển tới quá 2 giờ chưa xác nhận', 'Mỗi giờ: phiếu điều chuyển đã ghi sổ từ 2 giờ mà kho nhận chưa xác nhận.'],
	kho_ycdc_moi: ['Kho', 'Yêu cầu điều chuyển mới', 'Bộ phận vừa gửi yêu cầu chuyển hàng giữa kho: kho đi, kho đến, tên hàng, ngày cần.'],
	kho_ycdc_treo: ['Kho', 'Yêu cầu điều chuyển treo quá 2 ngày (08:00)', '08:00 mỗi sáng: yêu cầu điều chuyển đã gửi quá 2 ngày mà chưa chuyển xong.'],
	kho_nhan_thieu_ton: ['Kho', 'Nhận hàng không được vì kho xuất chưa đủ hàng', 'Kho nhận bấm xác nhận mà kho xuất chưa đủ hàng trên máy: tên hàng, kho, số lượng còn thiếu.'],
	kho_huy_cho_ghi_so: ['Kho', 'Phiếu xuất huỷ chờ ghi sổ', 'Có phiếu xuất huỷ còn nháp chờ người có quyền ghi sổ.'],
	kho_da_huy: ['Kho', 'Đã xuất huỷ', 'Phiếu xuất huỷ vừa ghi sổ: kho, lý do, tên hàng, số lượng.'],
	kho_xuat_noi_bo: ['Kho', 'Đã xuất dùng nội bộ', 'Phiếu xuất nội bộ vừa ghi sổ: mục đích, tên hàng, số lượng.'],
	kho_giao_si: ['Kho', 'Đã xuất giao khách sỉ', 'Phiếu giao hàng sỉ vừa ghi sổ: khách, kho, tên hàng, số lượng.'],
	kho_kiem_ke_cho_duyet: ['Kho', 'Phiếu kiểm kê chờ duyệt', 'Phiếu kiểm kê vừa chuyển sang Chờ duyệt, kèm các dòng lệch.'],
	kho_kiem_ke_da_ghi_so: ['Kho', 'Kiểm kê đã ghi sổ', 'Phiếu kiểm kê đã ghi sổ điều chỉnh tồn, kèm các dòng lệch.'],
	kho_lo_sap_het_han: ['Kho', 'Lô sắp hết hạn trong 3 ngày (07:00)', '07:00 mỗi sáng, một tin mỗi kho: lô còn tồn mà hết hạn trong 3 ngày.'],
	kho_ton_duoi_muc: ['Kho', 'Tồn kho dưới mức tối thiểu (07:00)', '07:00 mỗi sáng, một tin mỗi kho: món có tồn thấp hơn mức tối thiểu đã khai.'],
	ht_email_loi: ['Hệ thống', 'Email của tiệm không gửi được', 'Trong một giờ có từ 5 thư lỗi; báo lại sau 3 giờ nếu còn lỗi.'],
	ht_phat_hanh: ['Hệ thống', 'Bản tin cập nhật app sau mỗi deploy', 'App vừa lên bản mới: thêm gì, bộ phận cần làm gì.'],
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
	var ZALO_DANH_MUC = VGB_ZALO_DANH_MUC, ZALO_NHAN = VGB_ZALO_NHAN, ZALO_TIN = VGB_ZALO_TIN, ZALO_BO_PHAN = VGB_ZALO_BO_PHAN;
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

	// v591: Zalo không gửi tên nhóm. App và Desk phải gọi cùng một chat_id bằng
	// cùng mã ngắn, nếu không quản trị viên không thể đối chiếu mã bot vừa trả lời.
	function maNhomZalo(chatId) {
		var ma = String(chatId || '').trim();
		if (/^zgr-/i.test(ma)) ma = ma.slice(4);
		return ma.slice(-4).toUpperCase();
	}
	function nhanNhomZalo(x) {
		x = x || {};
		var nhan = 'Nhóm Zalo mã ' + maNhomZalo(x.chat_id);
		if (x.dang_luu) nhan += ' (đang lưu' + (x.ten ? ': ' + x.ten : '') + ')';
		else if ((x.dang_gan || []).length) nhan += ' (đang dùng)';
		return nhan;
	}

	// Mỗi kết nối: đủ các ô "can" (hoặc đủ một nhóm trong "canMot") là đã khai;
	// có ô "bat" mà đang tắt thì vàng. "toi" là ô để nhảy tới khi bấm chip.
	var KET_NOI = [
		{ hau: 'Không xuất được hoá đơn điện tử.', ten: 'Hoá đơn điện tử m-invoice', can: ['minvoice_host', 'minvoice_username', 'minvoice_password'], toi: 'minvoice_host', muc: 'sec_minvoice' },
		// Codex #433: đủ mọi khe khoá mà sepay._cac_khoa() chấp nhận; webhook chạy được
		// chỉ với khe thứ hai hay thứ ba thì vẫn là đã khai.
		{ hau: 'Tiền chuyển khoản không tự về app, phải đối chiếu tay.', ten: 'SePay ngân hàng', canMot: [['sepay_khoa'], ['sepay_khoa_2'], ['sepay_hmac'], ['sepay_hmac_2'], ['sepay_hmac_3']], bat: 'sepay_bat', toi: 'sepay_bat', muc: 'sec_sepay' },
		{ hau: 'Không kéo được đơn Pancake về doanh số.', ten: 'Pancake', can: ['pancake_api_key', 'pancake_shop_id'], toi: 'pancake_api_key', muc: 'sec_pancake' },
		// Codex #433 vòng 3: "đã khai" phải đủ MỌI ô máy chủ đòi, không thì chip xanh
		// cho một cấu hình chắc chắn hỏng. Mỗi dòng ghi chỗ máy chủ kiểm.
		// van_don.py: key(ahamove_api_key) and ahamove_base and ahamove_mobile
		{ hau: 'Không báo phí giao và không đặt xe Ahamove từ app được.', ten: 'Ahamove', can: ['ahamove_api_key', 'ahamove_mobile', 'ahamove_base'], toi: 'ahamove_api_key', muc: 'sec_aha' },
		{ hau: 'Không gợi ý địa chỉ và không tính được khoảng cách giao.', ten: 'Goong bản đồ', can: ['goong_api_key'], toi: 'goong_api_key', muc: 'sec_goong' },
		// van_don._greensm_dat_don: client_id, client_secret và token_url. be_token
		// không có dòng Python nào đọc, nên không làm chip xanh được.
		{ hau: 'Không đặt xe GreenSM từ app được.', ten: 'GreenSM', can: ['greensm_client_id', 'greensm_client_secret', 'greensm_token_url'], toi: 'greensm_client_id', muc: 'sec_gsm' },
		// Codex #435 vòng 7: kenh_zalo.chon_nhom bỏ dòng tắt hoặc thiếu mã chat; không
		// còn nhóm nào nhận thì mọi tin tự động bị bỏ âm thầm, nên phải có ít nhất
		// một nhóm đang bật và có mã chat mới là đã khai.
		{ hau: 'Các nhóm Zalo không nhận tin tự động.', ten: 'Zalo bắn tin nhóm', can: ['zalo_bot_token'], canNhom: 'zalo_nhom', bat: 'zalo_bot_bat', toi: 'zalo_bot_bat', muc: 'sec_zalo_bot' },
		// zalo.py: làm mới token cần App ID, App Secret và Refresh Token.
		// Codex #435: zalo.gui_tin từ chối khi không có mã mẫu ZNS, nên phải có ít
		// nhất một mẫu (OTP đăng nhập, đòi tiền, trừ điểm) mới là đã khai.
		{ hau: 'Không gửi được mã OTP, tin đòi tiền, tin trừ điểm cho khách.', ten: 'Zalo ZNS gửi khách', can: ['zalo_app_id', 'zalo_app_secret', 'zalo_refresh_token'],
			canMot: [['zns_template_otp'], ['zns_template_thanh_toan'], ['zns_template_diem']], toi: 'zalo_app_id', muc: 'sec_zalo' },
		// whatsapp.gui_mau từ chối khi không có tên mẫu; nơi gọi duy nhất dùng mẫu thanh toán.
		{ hau: 'Không gửi được yêu cầu thanh toán qua WhatsApp.', ten: 'WhatsApp', can: ['wa_phone_id', 'wa_token', 'wa_template_thanh_toan'], toi: 'wa_phone_id', muc: 'sec_wa' },
		// thong_bao.py gửi bằng khoá riêng VAPID; thiếu là "chua co khoa VAPID".
		{ hau: 'Điện thoại nhân viên không nhận thông báo đẩy.', ten: 'Thông báo đẩy', can: ['push_khoa_cong_khai', 'push_khoa_rieng'], toi: 'push_khoa_cong_khai', muc: 'sec_push' },
		{ hau: 'Quảng cáo Meta không đo được đơn từ web.', ten: 'Meta Pixel', can: ['meta_pixel_id'], toi: 'meta_pixel_id', muc: 'sec_meta_pixel' },
		{ hau: 'Quầy không in ngầm được, mỗi lần in phải bấm hộp in.', ten: 'Máy in QZ Tray', can: ['qz_chung_thu', 'qz_khoa_rieng'], toi: 'qz_chung_thu', muc: 'sec_qz' },
		{ hau: 'Nút trợ lý trong app không trả lời được.', ten: 'Trợ lý hướng dẫn', can: ['tro_ly_khoa'], bat: 'tro_ly_bat', toi: 'tro_ly_bat', muc: 'sec_tro_ly' },
		{ hau: 'Không tự dịch nội dung web sang tiếng Anh được.', ten: 'Dịch Gemini', can: ['gemini_api_key'], toi: 'gemini_api_key', muc: 'sec_ai' },
	];

	function duKhai(doc, k) {
		if (k.can && !k.can.every(function (f) { return co(doc[f]); })) return false;
		if (k.canMot && !k.canMot.some(function (nh) { return nh.every(function (f) { return co(doc[f]); }); })) return false;
		// Cùng luật với kenh_zalo.chon_nhom: dòng phải đang bật và có mã chat.
		if (k.canNhom && !(doc[k.canNhom] || []).some(function (r) { return r && bat(r.bat) && co(r.chat_id); })) return false;
		return true;
	}

	// v596: ô đầu tiên còn thiếu của một kết nối, theo đúng thứ tự máy chủ đòi.
	function oThieu(doc, k) {
		var i;
		for (i = 0; k.can && i < k.can.length; i++) if (!co(doc[k.can[i]])) return k.can[i];
		if (k.canMot && !k.canMot.some(function (nh) { return nh.every(function (f) { return co(doc[f]); }); })) return k.canMot[0][0];
		if (k.canNhom) return k.canNhom;
		return '';
	}

	// v596: lỗi cụ thể của TỪNG Ô, để màn tô đỏ đúng ô và nói cách sửa. Nguồn duy
	// nhất: chip đỏ của kết nối cũng đọc từ đây (không tự dò lại chỗ khác).
	// Codex 3d0b446: máy chủ thật của Ahamove cho đối tác là partner-api.ahamove.com
	// (tài liệu môi trường của Ahamove, khớp mô tả ô trên doctype). api.ahamove.com
	// là sai chỗ. v608 (Codex 4337249728): máy chủ đã chịu đuôi /v3 (lib.aha_url bỏ
	// đuôi đó trước khi nối), nên ô này cũng phải nhận, cùng một luật chuẩn hoá.
	var AHAMOVE_THAT = 'https://partner-api.ahamove.com';
	function chuanBaseAhamove(base) {
		var b = String(base || '').trim().replace(/\/+$/, '').toLowerCase();
		while (/\/v3$/.test(b)) b = b.replace(/\/v3$/, '').replace(/\/+$/, '');
		return b;
	}
	function loiAhamove(base) {
		var b = chuanBaseAhamove(base);
		if (!b) return null;
		if (/apistg/.test(b)) {
			return { ghi: 'đang trỏ máy chủ chạy thử, phí giao thật sẽ lỗi',
				cau: 'Đây là máy chủ chạy thử. Đổi thành ' + AHAMOVE_THAT + ' để báo phí giao thật.' };
		}
		if (b !== AHAMOVE_THAT) {
			return { ghi: 'địa chỉ API chưa đúng, phí giao sẽ lỗi',
				cau: 'Không phải máy chủ thật của Ahamove. Chạy thật dùng ' + AHAMOVE_THAT + '.' };
		}
		return null;
	}
	function loiTruong(doc) {
		doc = doc || {};
		var ra = {};
		var aha = loiAhamove(doc.ahamove_base);
		if (aha) ra.ahamove_base = aha.cau;
		return ra;
	}

	// Trạng thái: ok xanh, no xám (chưa khai), off vàng (khai rồi nhưng tắt), err đỏ.
	// v597: THUẦN, bản JS của kenh_zalo.chon_nhom: có nhóm bật, có mã chat, nhận (loại, chủ đề) không.
	// v604: cùng luật Tin nhận với kenh_zalo.chon_nhom: nhóm đã tích tin thì chỉ nhận
	// đúng tin đã tích (bỏ qua loại, chủ đề); tin không mã không tới nhóm đó.
	function coNhomZalo(doc, loai, chuDe, maTin) {
		var tach = function (s) { return String(s || '').split(/[,;]/).map(function (x) { return x.trim(); }).filter(Boolean); };
		return ((doc || {}).zalo_nhom || []).some(function (r) {
			if (!r || !bat(r.bat) || !co(r.chat_id)) return false;
			var tn = tach(r.tin_nhan);
			if (tn.length) return !!maTin && tn.indexOf(maTin) >= 0;
			var lt = tach(r.loai_tin), cd = tach(r.chu_de);
			return (!lt.length || lt.indexOf(loai) >= 0) && (!cd.length || !chuDe || cd.indexOf(chuDe) >= 0);
		});
	}

	function tinhTrang(doc, bayGio) {
		doc = doc || {};
		var ra = KET_NOI.map(function (k) {
			var tr = !duKhai(doc, k) ? 'no' : (k.bat && !bat(doc[k.bat]) ? 'off' : 'ok');
			var ghi = tr === 'no' ? 'chưa khai' : (tr === 'off' ? 'đã khai, đang tắt' : 'đã khai');
			// v596: bấm "Khai" phải tới đúng ô còn thiếu, không phải ô đầu của mục.
			var toi = tr === 'no' ? (oThieu(doc, k) || k.toi) : (tr === 'off' ? k.bat : k.toi);
			var aha = k.ten === 'Ahamove' ? loiAhamove(doc.ahamove_base) : null;
			if (aha) { tr = 'err'; ghi = aha.ghi; toi = 'ahamove_base'; }
			return { ten: k.ten, trang: tr, ghi: ghi, toi: toi, muc: k.muc, hau: k.hau || '' };
		});
		// Còi báo động: hú trong 24 giờ qua là đỏ, kể cả khi đã khai đủ.
		var luc = co(doc.email_bao_dong_lan_cuoi) ? Date.parse(String(doc.email_bao_dong_lan_cuoi).replace(' ', 'T')) : NaN;
		var gio = isNaN(luc) ? null : Math.floor(((bayGio || Date.now()) - luc) / 3600000);
		// v597: đường báo là một nhóm Zalo nhận Cảnh báo chủ đề Hệ thống.
		// v604: anh Việt 18/10/2026 bỏ thư dự phòng (ô Email nhận thư cảnh báo không
		// còn là đường báo); đường duy nhất là nhóm Zalo nhận tin thư hỏng.
		var coDuong = coNhomZalo(doc, 'canh_bao', 'he_thong', 'ht_email_loi');
		// Codex #490: máy chủ (kenh_zalo.bao) không gửi gì khi công tắc Zalo Bot tắt, mà
		// thư dự phòng đã bỏ, nên có nhóm mà bot tắt thì chưa có đường báo thật: vàng.
		var botBat = bat(doc.zalo_bot_bat);
		var thu = { ten: 'Thư cảnh báo', toi: 'zalo_bot_bat', muc: 'sec_zalo_bot', hau: 'Email của tiệm hỏng mà không nhóm Zalo nào được báo.' };
		if (gio !== null && gio >= 0 && gio < 24) {
			thu.trang = 'err'; thu.ghi = 'hú còi ' + (gio === 0 ? 'chưa tới 1 giờ' : gio + ' giờ') + ' trước';
		} else if (coDuong && botBat) {
			thu.trang = 'ok'; thu.ghi = 'đã khai';
		} else if (coDuong) {
			thu.trang = 'off'; thu.ghi = 'đã khai, Zalo Bot đang tắt';
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

	// v596: tóm tắt cho đầu màn Cài đặt (app và Desk dùng chung). Trả số theo màu,
	// một câu tiếng Việt chỉ nêu phần khác 0, và danh sách việc cần xử lý xếp đỏ,
	// vàng, xám. Chỉ đếm kết nối thật, không đoán "ổn" cho phần không có kết nối.
	var CHU_MAU = { ok: 'ổn', no: 'chưa khai', off: 'đang tắt', err: 'đang lỗi' };
	function tongHop(ds) {
		ds = ds || [];
		var dem = { ok: 0, no: 0, off: 0, err: 0 };
		ds.forEach(function (t) { if (dem[t.trang] !== undefined) dem[t.trang]++; });
		var phan = ['ok', 'no', 'off', 'err'].filter(function (k) { return dem[k]; })
			.map(function (k) { return dem[k] + ' ' + CHU_MAU[k]; });
		return {
			dem: dem, tong: ds.length,
			cau: ds.length + ' kết nối' + (phan.length ? ': ' + phan.join(', ') : ''),
			can: xepTinhTrang(ds).filter(function (t) { return t.trang !== 'ok'; }),
		};
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
	var GHI_CHU_TIN = 'Tích tin nào thì nhóm nhận tin đó. Không tích tin nào thì nhóm nhận theo Loại tin và Chủ đề như cũ.';
	// v604: tên tin theo mã; mã lạ (đã bỏ khỏi danh mục) hiện câu chung, không lộ mã.
	function tenTin(ma) { return (ZALO_TIN[ma] || [null, 'Tin không còn trong danh mục'])[1]; }
	// Danh mục tin gom theo bộ phận, đúng thứ tự BO_PHAN rồi thứ tự trong bảng.
	function tinTheoBoPhan() {
		return ZALO_BO_PHAN.map(function (bp) {
			return { bo_phan: bp, tin: Object.keys(ZALO_TIN).filter(function (m) { return ZALO_TIN[m][0] === bp; })
				.map(function (m) { return { ma: m, ten: ZALO_TIN[m][1], giai_thich: ZALO_TIN[m][2] }; }) };
		}).filter(function (x) { return x.tin.length; });
	}
	// Tóm tắt Tin nhận cho thẻ nhóm: tối đa 3 tên rồi "và N tin nữa" (điều 17).
	function tomTatTin(s) {
		var ds = tachMa(s);
		if (!ds.length) return '';
		var ten = ds.slice(0, 3).map(tenTin);
		return ds.length + ' tin: ' + ten.join(', ') + (ds.length > 3 ? ' và ' + (ds.length - 3) + ' tin nữa' : '');
	}
	function theNhomZalo(r) {
		r = r || {};
		var lt = tachMa(r.loai_tin).map(function (x) { return tenMaZalo('loai_tin', x); });
		var cd = tachMa(r.chu_de).map(function (x) { return tenMaZalo('chu_de', x); });
		var coNhom = co(r.chat_id), bat = parseInt(r.bat, 10) === 1;
		var tin = tomTatTin(r.tin_nhan);
		return {
			ten: co(r.ten_nhom) ? String(r.ten_nhom).trim() : 'Nhóm chưa đặt tên',
			// v604: nhóm đã tích Tin nhận thì thẻ nói tin, không nói loại, chủ đề (không dùng nữa).
			tin: tin,
			loai: tin ? 'Không dùng, nhóm nhận theo Tin nhận' : (lt.length ? lt.join(', ') : 'Mọi loại tin'),
			chu_de: tin ? 'Không dùng, nhóm nhận theo Tin nhận' : (cd.length ? cd.join(', ') : 'Mọi chủ đề'),
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
		tongHop: tongHop, loiTruong: loiTruong, oThieu: oThieu,
		NHAN_CHON: NHAN_CHON, KET_NOI: KET_NOI, docJson: docJson, nganHangTheoBin: nganHangTheoBin, timNganHang: timNganHang, moToi: moToi, xepTinhTrang: xepTinhTrang, kiemCapNganHang: kiemCapNganHang,
		ZALO_NHAN: ZALO_NHAN, ZALO_DANH_MUC: ZALO_DANH_MUC, theNhomZalo: theNhomZalo, tachMa: tachMa,
		maNhomZalo: maNhomZalo, nhanNhomZalo: nhanNhomZalo,
		ZALO_TIN: ZALO_TIN, ZALO_BO_PHAN: ZALO_BO_PHAN, coNhomZalo: coNhomZalo, tenTin: tenTin, tinTheoBoPhan: tinTheoBoPhan,
		tomTatTin: tomTatTin, GHI_CHU_TIN: GHI_CHU_TIN };
})();

if (typeof window !== 'undefined') window.VGB_CD = VGB_CD;
}
if (typeof module !== 'undefined' && module.exports) module.exports = VGB_CD;
