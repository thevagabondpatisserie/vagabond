# -*- coding: utf-8 -*-
"""Đề nghị chi nội bộ: cổng vào cho nhân viên thường, nối vào luồng AP đã có.

Anh Việt đặt bài 19/08/2026: nhân viên xin tạm ứng, xin hoàn tiền khi mua
lặt vặt (đồ cúng, nước đá), hoặc đề nghị chi thẳng cho người bán nằm ngoài
luồng mua hàng định kỳ.

Vì sao mô đun này MỎNG, và cố ý mỏng
------------------------------------
Hệ đã có ba đường tiền ra: `Vagabond Ho So TT` cho công nợ nhà cung cấp và
hoàn ứng, `Payment Entry` có workflow ba cấp, `Vagabond Hoan Tien` cho khách.
Riêng Hồ sơ TT đã có sẵn loại "Hoàn ứng" đúng cho khoản lẻ không hoá đơn, đã
có tài khoản người thụ hưởng, cờ có hoá đơn VAT từng dòng, TK Nợ TK Có từng
dòng, dò SePay khớp giao dịch và sinh Payment Entry.

Nếu mô đun này tự sinh bút toán riêng thì thành đường tiền ra THỨ TƯ. Bốn
đường song song thì sớm muộn cũng lệch nhau, và không còn ai trả lời được
câu "tháng này công ty chi ra bao nhiêu" bằng một chỗ duy nhất.

Nên ở đây chỉ làm đúng khúc đang thiếu: cái form nhẹ để bạn bếp, bạn quầy
lập được, và đường dẫn từ đó sang Hồ sơ TT. Toàn bộ phần kế toán giao lại
cho `ho_so_tt.py` như hiện nay.

Vì sao đặt trong repo chứ không làm Client Script
------------------------------------------------
Client Script và Workflow dựng tay đều nằm trong cơ sở dữ liệu: git không
thấy, kiểm thử không chạm tới, phiên Cowork khác không nhìn thấy để tránh,
và không lùi lại được bằng một lần deploy. Dự án này đã mất code thật hai
lần vì đúng loại vấn đề đó.

Bốn điểm anh Việt chốt 19/08/2026
---------------------------------
1. Ngưỡng 2.000.000đ: trên ngưỡng thì thêm một cấp giám đốc duyệt.
2. Tách tạm ứng khỏi chi phí: "Ứng lương" và "Tạm ứng cash back" không phải
   chi phí mà là khoản phải thu, nên ra một trường riêng.
3. Chặn trùng số hoá đơn.
4. Chặn phân loại tài sản cố định, chỉ sang luồng mua hàng.
"""

import frappe
from frappe.utils import cint, flt, getdate, now_datetime, nowdate

DT = "Vagabond De Nghi Chi"
HO_SO_TT = "Vagabond Ho So TT"
PI = "Purchase Invoice"

# --------------------------------------------------------------- vai duyệt
#
# Theo VAI chứ không theo tên người. Kiểm trên site 19/08/2026: Uyên đang giữ
# "AP Officer", chị Dung giữ "AP Kiểm soát (FIN)", anh Việt và Dễ giữ "AP
# Giám đốc". Ba vai này đã có sẵn và đang chạy workflow của Payment Entry.
#
# Viết cứng tên người vào đây thì Uyên nghỉ phép là cả tiệm tắc, và người
# mới vào không duyệt được cho tới khi có người sửa mã. Gán vai thì xong.
VAI_DUYET = {"AP Officer", "Purchase Manager", "System Manager"}
VAI_GIAM_DOC = {"AP Giám đốc", "System Manager"}
VAI_KE_TOAN = {"AP Kiểm soát (FIN)", "Accounts Manager", "System Manager"}

# ------------------------------------------------------------ loại nghiệp vụ
#
# Anh Việt chốt tách 19/08/2026. Danh sách 33 phân loại ban đầu có lẫn "Ứng
# lương" và "Tạm ứng cash back". Hai khoản đó KHÔNG phải chi phí, chúng là
# khoản công ty phải thu lại của người nhận. Để chung một danh sách thì chị
# Dung phải tự nhớ mà định khoản khác đi cho hai dòng đó, mỗi phiếu một lần
# nhớ, và quên một lần là chi phí bị khai khống.
NV_CHI_PHI = "Chi phí"
NV_TAM_UNG = "Tạm ứng"
NV_HOAN_UNG = "Hoàn ứng"
LOAI_NGHIEP_VU = (NV_CHI_PHI, NV_TAM_UNG, NV_HOAN_UNG)

# Phân loại tạm ứng, tách ra từ danh sách gốc.
PL_TAM_UNG = ("Ứng lương", "Tạm ứng cash back")

# ------------------------------------------------- phân loại và tài khoản
#
# Ánh xạ phân loại sang tài khoản kế toán, khai một lần ở đây thay vì để chị
# Dung quyết lại mỗi phiếu. Hai phiếu giống nhau mà vào hai tài khoản khác
# nhau là chuyện đã từng xảy ra khi không có bảng này.
#
# Số tài khoản chứ không phải tên: tên thì ai đổi cũng được, còn số hiệu là
# thứ đã chốt theo Thông tư 99/2025.
#
# Đây là GỢI Ý, không phải quyết định. Chị Dung sửa được trên từng phiếu, và
# ba dòng đánh dấu (*) dưới đây thì chị nên xem lại vì bản chất còn tuỳ ca.
TK_THEO_PHAN_LOAI = {
	"Mua đồ cúng": "6428",
	"Mua nguyên vật liệu": "621",          # (*) nhập kho thì phải qua 152
	"Mua công cụ dụng cụ": "6423",
	"Mua đồng phục nhân viên": "6423",
	"Phí giặt ủi": "6427",
	"Phí in ấn": "6427",
	"Phí sửa chữa bảo trì": "6427",
	"Mua máy móc-tài sản cố định": None,   # chặn, xem CHAN_TSCD
	"Vận chuyển": "6417",
	"Nộp thuế": "6425",
	"Phí công tác": "6428",
	"Quảng cáo-marketing": "6418",
	"Tiếp khách-quà cáp": "6428",
	"Tiền thuê nhà": "6427",
	"Phí an ninh": "6427",
	"Phí ngân hàng": "635",
	"Trả lãi vay": "635",
	"Tiền bảo hiểm": "6427",               # (*) bảo hiểm xã hội thì về 6421
	"Tiền điện": "6427",
	"Tiền nước": "6427",
	"Tiền điện thoại": "6427",
	"Tiền internet": "6427",
	"Tiền lương": "6421",                  # (*) lương thật phải đi qua 334
	"Tiền rác-vệ sinh môi trường": "6427",
	"Chi cho event": "6418",
	"Tiền hoa hồng-môi giới": "6418",
	"Phí phần mềm-bản quyền": "6427",
	"Khảo sát thị trường": "6418",
	"Tiền thưởng-phúc lợi nhân viên": "6421",
	"Chi phí quản lý doanh nghiệp": "6428",
	"Thuê thiết bị máy móc": "6427",
}

PHAN_LOAI = tuple(TK_THEO_PHAN_LOAI.keys())

# Phân loại không được đi đường chi lặt vặt. Tài sản cố định cần đơn mua
# hàng, cần theo dõi khấu hao, cần hồ sơ tài sản; nhét nó vào một phiếu hoàn
# tiền là mất cả ba thứ đó.
CHAN_TSCD = {"Mua máy móc-tài sản cố định"}

# Khoản không có hoá đơn GTGT thì không được trừ khi quyết toán thuế TNDN.
# Cây tài khoản đã có sẵn một chỗ đúng cho việc này, dùng luôn thay vì để
# lẫn vào chi phí thường rồi cuối năm ngồi bóc tách lại.
TK_KHONG_HOA_DON = "6429"

# ------------------------------------------------------------ chứng từ thuế
CT_CO_VAT = "Có hoá đơn VAT"
CT_KHONG_VAT = "Không hoá đơn VAT"

# ---------------------------------------------------------- hình thức chi
HT_NHAN_VIEN = "Hoàn tiền cho nhân viên"
HT_NCC = "Thanh toán cho nhà cung cấp"

PT_TIEN_MAT = "Tiền mặt"
PT_CHUYEN_KHOAN = "Chuyển khoản"

# ------------------------------------------------------------- trạng thái
TT_NHAP = "Nhap"
TT_CHO_DUYET = "Cho duyet"
TT_CHO_GIAM_DOC = "Cho giam doc"
TT_CHO_KE_TOAN = "Cho ke toan"
TT_HOAN_TAT = "Hoan tat"
TT_TRA_LAI = "Bi tra lai"

NHAN_TRANG_THAI = {
	TT_NHAP: "Nháp",
	TT_CHO_DUYET: "Chờ mua hàng duyệt",
	TT_CHO_GIAM_DOC: "Chờ giám đốc duyệt",
	TT_CHO_KE_TOAN: "Chờ kế toán hạch toán",
	TT_HOAN_TAT: "Hoàn tất",
	TT_TRA_LAI: "Bị trả lại",
}

# Anh Việt chốt 19/08/2026. Từ ngưỡng này trở lên thì thêm một cấp giám đốc.
# Một phiếu 50 nghìn tiền đá và một phiếu 50 triệu mua máy không nên đi cùng
# một đường.
NGUONG_GIAM_DOC = 2000000.0


# ============================================================ phép THUẦN
#
# Các hàm dưới đây không chạm vào Frappe, nên kiểm thử được không cần site.


def la_tam_ung(loai_nghiep_vu):
	"""Phiếu này là tạm ứng hay là chi phí. THUẦN."""
	return (loai_nghiep_vu or "").strip() == NV_TAM_UNG


def can_giam_doc_duyet(so_tien, nguong=NGUONG_GIAM_DOC):
	"""Số tiền này có phải qua cấp giám đốc không. THUẦN.

	Lấy mốc là LỚN HƠN HOẶC BẰNG ngưỡng. Đúng 2 triệu chẵn thì vẫn phải lên
	giám đốc: mốc tròn là mốc người ta hay bám vào để lách, nên để mốc nằm
	trong phần bị kiểm chứ không nằm ngoài.
	"""
	return flt(so_tien) >= flt(nguong)


def buoc_ke_tiep(so_tien, nguong=NGUONG_GIAM_DOC):
	"""Duyệt xong ở bước mua hàng thì rơi vào đâu. THUẦN."""
	return TT_CHO_GIAM_DOC if can_giam_doc_duyet(so_tien, nguong) else TT_CHO_KE_TOAN


def tk_goi_y(phan_loai, chung_tu_thue):
	"""Tài khoản chi phí gợi ý cho phiếu này. THUẦN.

	Trả về số hiệu tài khoản, hoặc None nếu không gợi ý được.

	Không có hoá đơn GTGT thì khoản đó không được trừ khi quyết toán thuế
	TNDN, nên gợi ý thẳng 6429 bất kể phân loại là gì. Chị Dung sửa được:
	có những khoản mua của hộ kinh doanh dưới ngưỡng vẫn được trừ nếu lập
	bảng kê, nên đây là gợi ý chứ không phải luật.
	"""
	if (chung_tu_thue or "").strip() == CT_KHONG_VAT:
		return TK_KHONG_HOA_DON
	return TK_THEO_PHAN_LOAI.get((phan_loai or "").strip())


def can_chon_ncc(hinh_thuc, chung_tu_thue):
	"""Phiếu này có bắt buộc chọn nhà cung cấp không. THUẦN.

	Đây là chỗ bản mô tả ban đầu hở. Mô tả chỉ mở ô chọn nhà cung cấp ở
	nhánh "Thanh toán cho nhà cung cấp". Nhưng khi bạn nhân viên bỏ tiền túi
	mua VÀ lấy hoá đơn VAT mang tên Vagabond, thì hoá đơn đó là của NGƯỜI
	BÁN còn tiền thì trả lại cho NHÂN VIÊN: hai đối tượng khác nhau trên
	cùng một phiếu.

	Thiếu nhà cung cấp thì không lập được hoá đơn mua hàng, mà không có hoá
	đơn mua hàng thì khoản đó không lên bảng kê mua vào 01-2/GTGT và thuế
	đầu vào không khấu trừ được.
	"""
	return (
		(hinh_thuc or "").strip() == HT_NCC
		or (chung_tu_thue or "").strip() == CT_CO_VAT
	)


def thieu_gi(phieu):
	"""Phiếu còn thiếu những gì trước khi gửi đi duyệt. THUẦN.

	`phieu` là dict. Trả về danh sách câu tiếng Việt, rỗng nghĩa là đủ.

	Gom hết vào một hàm thuần thay vì rải `frappe.throw` khắp nơi: như vậy
	màn hình nhắc được CẢ danh sách còn thiếu trong một lần, thay vì người
	lập sửa một cái rồi bấm lại mới biết còn thiếu cái nữa.
	"""
	p = phieu or {}
	thieu = []

	if not (p.get("ten_khoan_chi") or "").strip():
		thieu.append("Tên khoản chi")
	if flt(p.get("so_tien")) <= 0:
		thieu.append("Số tiền yêu cầu phải lớn hơn 0")
	if not p.get("ngay_can_tt"):
		thieu.append("Ngày cần thanh toán")

	nv = (p.get("loai_nghiep_vu") or "").strip()
	if nv not in LOAI_NGHIEP_VU:
		thieu.append("Loại nghiệp vụ")
	elif nv == NV_CHI_PHI:
		pl = (p.get("phan_loai") or "").strip()
		if not pl:
			thieu.append("Phân loại chi tiêu")
		elif pl not in TK_THEO_PHAN_LOAI:
			thieu.append("Phân loại chi tiêu không nằm trong danh mục")

	ht = (p.get("hinh_thuc") or "").strip()
	if ht not in (HT_NHAN_VIEN, HT_NCC):
		thieu.append("Hình thức thụ hưởng")

	ct = (p.get("chung_tu_thue") or "").strip()
	if ct not in (CT_CO_VAT, CT_KHONG_VAT):
		thieu.append("Chứng từ thuế")
	elif ct == CT_CO_VAT:
		if not (p.get("so_hoa_don") or "").strip():
			thieu.append("Số hoá đơn")
		if not p.get("ngay_hoa_don"):
			thieu.append("Ngày hoá đơn")
		if not (p.get("mst") or "").strip():
			thieu.append("Mã số thuế người bán")

	if can_chon_ncc(ht, ct) and not (p.get("nha_cung_cap") or "").strip():
		thieu.append(
			"Nhà cung cấp (hoá đơn VAT phải gắn người bán thì mới lên được "
			"bảng kê mua vào)"
		)

	if (p.get("phuong_thuc") or "").strip() == PT_CHUYEN_KHOAN:
		for o, ten in (
			("ten_tk", "Tên chủ tài khoản"),
			("so_tk", "Số tài khoản"),
			("ngan_hang", "Ngân hàng"),
		):
			if not (p.get(o) or "").strip():
				thieu.append(ten)

	return thieu


def ly_do_chan(phieu):
	"""Phiếu này có bị chặn thẳng không, và vì sao. THUẦN.

	Khác `thieu_gi` ở chỗ: thiếu thì bổ sung là xong, còn bị chặn thì phải
	đi đường khác. Trả về câu giải thích, hoặc None nếu không chặn.
	"""
	p = phieu or {}
	pl = (p.get("phan_loai") or "").strip()
	if pl in CHAN_TSCD:
		return (
			"Khoản này là tài sản cố định nên không đi đường đề nghị chi lặt "
			"vặt được. Tài sản cố định cần đơn mua hàng, cần theo dõi khấu hao "
			"và cần hồ sơ tài sản, nhét vào một phiếu hoàn tiền là mất cả ba. "
			"Anh chị lập Đơn mua hàng giúp em, hoặc nhắn Uyên để Uyên lập."
		)
	if la_tam_ung((p.get("loai_nghiep_vu") or "")) and (
		(p.get("chung_tu_thue") or "").strip() == CT_CO_VAT
	):
		return (
			"Tạm ứng thì chưa phát sinh chi phí nên chưa có hoá đơn VAT. Nếu "
			"đã có hoá đơn rồi thì đây là khoản hoàn ứng chứ không phải tạm "
			"ứng, anh chị đổi Loại nghiệp vụ giúp em."
		)
	return None


def khoa_trung_hoa_don(mst, so_hoa_don, ngay_hoa_don):
	"""Khoá nhận dạng một tờ hoá đơn. THUẦN.

	Ba yếu tố: mã số thuế người bán, số hoá đơn, ngày hoá đơn. Cùng bộ ba
	này là cùng một tờ.

	Bỏ dấu cách và đưa về chữ hoa để "HD 0123" và "hd0123" không lọt thành
	hai tờ khác nhau.
	"""
	if not (so_hoa_don or "").strip():
		return None
	sach = lambda x: "".join((x or "").split()).upper()
	return "%s|%s|%s" % (sach(mst), sach(so_hoa_don), getdate(ngay_hoa_don) if ngay_hoa_don else "")


def duoc_duyet_khong(trang_thai, vai_nguoi_bam, la_nguoi_lap):
	"""Người này có được bấm duyệt ở bước hiện tại không. THUẦN.

	Trả về (được, lý do nếu không được).

	Hai luật cứng, lấy nguyên từ `ho_so_tt.py` vì chúng đã đúng ở đó:
	duyệt phải đúng thứ tự không nhảy cóc, và người lập không tự duyệt phiếu
	của chính mình.
	"""
	vai = set(vai_nguoi_bam or [])
	can = {
		TT_CHO_DUYET: VAI_DUYET,
		TT_CHO_GIAM_DOC: VAI_GIAM_DOC,
		TT_CHO_KE_TOAN: VAI_KE_TOAN,
	}.get(trang_thai)

	if not can:
		return False, "Phiếu đang ở trạng thái %s nên không có gì để duyệt." % (
			NHAN_TRANG_THAI.get(trang_thai) or trang_thai
		)
	if not (vai & can):
		return False, "Bước này cần vai %s." % " hoặc ".join(sorted(can))
	# System Manager là anh Việt, cho tự duyệt vì không còn ai trên nữa.
	if la_nguoi_lap and "System Manager" not in vai:
		return False, "Người lập phiếu không tự duyệt phiếu của chính mình được."
	return True, ""


def loai_ho_so_tt(hinh_thuc, chung_tu_thue):
	"""Đề nghị này đổ sang Hồ sơ thanh toán loại nào. THUẦN.

	Ba loại của `ho_so_tt.py`, chép lại đúng ý nghĩa gốc ở đó:
	    NCC         công ty nợ nhà cung cấp, trả thẳng cho họ
	    Hoan ung HD nhân viên đã ứng tiền mua hàng CÓ hoá đơn
	    Hoan ung    khoản lẻ KHÔNG hoá đơn
	"""
	if (hinh_thuc or "").strip() == HT_NCC:
		return "NCC"
	if (chung_tu_thue or "").strip() == CT_CO_VAT:
		return "Hoan ung HD"
	return "Hoan ung"


# ========================================================= chạm vào hệ


def _vai(nguoi=None):
	"""Tập vai của một người."""
	return set(frappe.get_roles(nguoi or frappe.session.user))


def _so_tep(ma_phieu):
	"""Đếm tệp đã đính vào phiếu.

	Đếm thẳng bảng File chứ không tin vào trường Attach trên phiếu: trường
	Attach thì người lập đính rồi gỡ ra vẫn lưu được. Cách này lấy nguyên từ
	`hoan_tien.chan_thieu_uy_nhiem_chi`, đã chạy đúng ở đó.
	"""
	return frappe.db.count("File", {"attached_to_doctype": DT, "attached_to_name": ma_phieu})


def _tk_lan_truoc(nguoi):
	"""Tài khoản ngân hàng người này khai ở phiếu gần nhất.

	Anh Việt chốt 19/08/2026 dùng cách này thay vì hồ sơ Employee, vì site
	chưa cài HRMS nên doctype Employee đang có 0 bản ghi, không có số tài
	khoản nhân viên nào để mà lấy.

	Lần đầu gõ tay, từ lần sau máy tự điền. Cùng cơ chế với gợi ý tài khoản
	trong luồng hoàn tiền khách.
	"""
	cu = frappe.db.get_value(
		DT,
		{"nguoi_tao": nguoi, "so_tk": ["is", "set"]},
		["ten_tk", "so_tk", "ngan_hang"],
		as_dict=True,
		order_by="creation desc",
	)
	return {k: v for k, v in (cu or {}).items() if v}


def _tk_nha_cung_cap(ma_ncc):
	"""Tài khoản ngân hàng của nhà cung cấp.

	ERPNext để tài khoản ngân hàng ở doctype riêng là `Bank Account`, KHÔNG
	để trên hồ sơ Supplier. Site đang có 132 bản ghi gắn với nhà cung cấp.
	Vì vậy `fetch_from` thuần của Frappe không lấy được, phải đọc bằng mã.
	"""
	if not ma_ncc:
		return {}
	tk = frappe.db.get_value(
		"Bank Account",
		{"party_type": "Supplier", "party": ma_ncc},
		["account_name", "bank_account_no", "bank"],
		as_dict=True,
		order_by="is_default desc, modified desc",
	)
	if not tk:
		return {}
	return {
		"ten_tk": tk.get("account_name") or "",
		"so_tk": tk.get("bank_account_no") or "",
		"ngan_hang": tk.get("bank") or "",
	}


def _ma_tk_theo_so_hieu(so_hieu, cong_ty=None):
	"""Đổi số hiệu tài khoản thành mã Account thật trên site.

	Bảng ánh xạ ghi số hiệu (6427) chứ không ghi mã đầy đủ ("6427 - Chi phí
	dịch vụ mua ngoài - TV): tên và hậu tố công ty thì ai đổi cũng được, còn
	số hiệu là thứ đã chốt theo Thông tư 99/2025.
	"""
	if not so_hieu:
		return None
	loc = {"account_number": so_hieu, "is_group": 0, "disabled": 0}
	if cong_ty:
		loc["company"] = cong_ty
	return frappe.db.get_value("Account", loc, "name")


def trung_hoa_don(doc):
	"""Tờ hoá đơn này đã nằm ở phiếu khác hoặc hoá đơn mua nào chưa.

	Hai bạn cùng chụp một tờ bill, hoặc một người nộp lại lần hai sau khi bị
	trả lại. Trả về danh sách mã chứng từ đã có, rỗng nghĩa là chưa trùng.
	"""
	khoa = khoa_trung_hoa_don(doc.get("mst"), doc.get("so_hoa_don"), doc.get("ngay_hoa_don"))
	if not khoa:
		return []

	da_co = []
	loc = {
		"so_hoa_don": doc.get("so_hoa_don"),
		"trang_thai": ["!=", TT_TRA_LAI],
		"name": ["!=", doc.get("name") or ""],
	}
	for k in frappe.get_all(DT, filters=loc, fields=["name", "mst", "ngay_hoa_don"]):
		if khoa_trung_hoa_don(k.get("mst"), doc.get("so_hoa_don"), k.get("ngay_hoa_don")) == khoa:
			da_co.append(k["name"])

	if doc.get("nha_cung_cap"):
		da_co += [
			h["name"]
			for h in frappe.get_all(
				PI,
				filters={
					"bill_no": doc.get("so_hoa_don"),
					"supplier": doc.get("nha_cung_cap"),
					"docstatus": ["<", 2],
				},
				fields=["name"],
			)
		]
	return da_co


def truoc_khi_luu(doc, method=None):
	"""Điền hộ những gì điền được, và chặn những gì phải chặn. Gọi từ before_validate."""
	if not doc.get("nguoi_tao"):
		doc.nguoi_tao = frappe.session.user
	if not doc.get("trang_thai"):
		doc.trang_thai = TT_NHAP

	chan = ly_do_chan(doc.as_dict() if hasattr(doc, "as_dict") else doc)
	if chan:
		frappe.throw(chan)

	# Tạm ứng thì không có phân loại chi phí, xoá đi cho khỏi lẫn vào báo cáo.
	if la_tam_ung(doc.get("loai_nghiep_vu")):
		doc.phan_loai = None

	# Tài khoản gợi ý: chỉ điền khi kế toán chưa tự chọn. Đè lên lựa chọn của
	# chị Dung là lỗi nặng hơn hẳn việc để trống.
	if not doc.get("tk_chi_phi"):
		ma = _ma_tk_theo_so_hieu(
			tk_goi_y(doc.get("phan_loai"), doc.get("chung_tu_thue")), doc.get("company")
		)
		if ma:
			doc.tk_chi_phi = ma

	# Tài khoản nhận tiền: lấy của nhà cung cấp, hoặc của chính người lập.
	if not (doc.get("so_tk") or "").strip():
		goi_y = (
			_tk_nha_cung_cap(doc.get("nha_cung_cap"))
			if (doc.get("hinh_thuc") or "") == HT_NCC
			else _tk_lan_truoc(doc.get("nguoi_tao"))
		)
		for k, v in (goi_y or {}).items():
			if not doc.get(k):
				doc.set(k, v)


@frappe.whitelist()
def goi_y_tai_khoan(hinh_thuc=None, nha_cung_cap=None):
	"""Màn hình hỏi tài khoản nhận tiền nên điền sẵn gì."""
	if (hinh_thuc or "") == HT_NCC:
		return _tk_nha_cung_cap(nha_cung_cap)
	return _tk_lan_truoc(frappe.session.user)


@frappe.whitelist()
def gui_duyet(ma_phieu):
	"""Nhân viên bấm Gửi duyệt."""
	doc = frappe.get_doc(DT, ma_phieu)
	if doc.trang_thai not in (TT_NHAP, TT_TRA_LAI):
		frappe.throw(
			"Phiếu đang ở trạng thái %s nên không gửi duyệt lại được."
			% (NHAN_TRANG_THAI.get(doc.trang_thai) or doc.trang_thai)
		)
	if doc.nguoi_tao != frappe.session.user and "System Manager" not in _vai():
		frappe.throw("Chỉ người lập phiếu mới gửi phiếu này đi duyệt được.")

	thieu = thieu_gi(doc.as_dict())
	if thieu:
		frappe.throw("Còn thiếu: %s." % ", ".join(thieu))

	# Ảnh bill hoặc hoá đơn: bắt buộc trước khi gửi đi duyệt. Uyên ngồi xa
	# quầy, cái duy nhất chị có để quyết là tấm ảnh người lập chụp.
	if not _so_tep(ma_phieu):
		frappe.throw(
			"Phải đính kèm ảnh bill, hoá đơn hoặc ảnh hàng hoá trước khi gửi "
			"duyệt. Bấm nút đính kèm ở góc phải rồi gửi lại giúp em."
		)

	trung = trung_hoa_don(doc.as_dict())
	if trung:
		frappe.throw(
			"Số hoá đơn %s đã nằm ở %s rồi. Nếu đây là tờ khác thì anh chị "
			"kiểm lại số hoá đơn và ngày giúp em."
			% (doc.so_hoa_don, ", ".join(trung))
		)

	doc.trang_thai = TT_CHO_DUYET
	doc.gui_luc = now_datetime()
	doc.save(ignore_permissions=True)
	return {"ok": 1, "trang_thai": doc.trang_thai}


@frappe.whitelist()
def duyet(ma_phieu, ghi_chu=None):
	"""Duyệt một bước. Ai bấm thì hệ tự biết đang ở bước nào."""
	doc = frappe.get_doc(DT, ma_phieu)
	duoc, vi_sao = duoc_duyet_khong(
		doc.trang_thai, _vai(), doc.nguoi_tao == frappe.session.user
	)
	if not duoc:
		frappe.throw(vi_sao)

	nguoi, luc = frappe.session.user, now_datetime()

	if doc.trang_thai == TT_CHO_DUYET:
		# Uyên chi tiền thật ở bước này, nên uỷ nhiệm chi phải có trước khi
		# chuyển sang kế toán. Đếm tệp lần hai chứ không tin lần đếm lúc gửi:
		# giữa hai lần đó phiếu đã đi qua tay người khác.
		if cint(doc.get("phuong_thuc") == PT_CHUYEN_KHOAN) and _so_tep(ma_phieu) < 2:
			frappe.throw(
				"Chuyển sang kế toán thì phải có uỷ nhiệm chi hoặc biên lai "
				"chuyển khoản đính kèm. Đính thêm rồi bấm lại giúp em."
			)
		doc.duyet_boi, doc.duyet_luc = nguoi, luc
		doc.trang_thai = buoc_ke_tiep(doc.so_tien)
	elif doc.trang_thai == TT_CHO_GIAM_DOC:
		doc.gd_boi, doc.gd_luc = nguoi, luc
		doc.trang_thai = TT_CHO_KE_TOAN
	else:
		doc.kt_boi, doc.kt_luc = nguoi, luc
		doc.trang_thai = TT_HOAN_TAT

	if (ghi_chu or "").strip():
		doc.ghi_chu = ((doc.ghi_chu or "") + "\n" + ghi_chu).strip()
	doc.save(ignore_permissions=True)
	return {"ok": 1, "trang_thai": doc.trang_thai}


@frappe.whitelist()
def tra_lai(ma_phieu, ly_do):
	"""Trả phiếu về cho người lập, bắt buộc ghi lý do."""
	if not (ly_do or "").strip():
		frappe.throw("Phải ghi lý do trả lại thì người lập mới biết đường sửa.")
	doc = frappe.get_doc(DT, ma_phieu)
	duoc, vi_sao = duoc_duyet_khong(
		doc.trang_thai, _vai(), doc.nguoi_tao == frappe.session.user
	)
	if not duoc:
		frappe.throw(vi_sao)
	doc.trang_thai = TT_TRA_LAI
	doc.ly_do_tra_lai = ly_do.strip()
	doc.tra_lai_boi = frappe.session.user
	doc.tra_lai_luc = now_datetime()
	doc.save(ignore_permissions=True)
	return {"ok": 1, "trang_thai": doc.trang_thai}


@frappe.whitelist()
def danh_sach(trang_thai="", so_dong=100):
	"""Danh sách phiếu cho màn hình.

	Nhân viên thường chỉ thấy phiếu của chính mình. Ba vai duyệt thấy hết.
	Lọc ở MÁY CHỦ chứ không lọc trên màn: lọc trên màn thì số đếm sẽ chỉ đếm
	phần đã kéo về, và người khéo tay vẫn xem được phiếu của người khác.
	"""
	loc = {}
	if (trang_thai or "").strip() and trang_thai != "tat_ca":
		loc["trang_thai"] = trang_thai
	if not (_vai() & (VAI_DUYET | VAI_GIAM_DOC | VAI_KE_TOAN)):
		loc["nguoi_tao"] = frappe.session.user

	ds = frappe.get_all(
		DT,
		filters=loc,
		fields=[
			"name", "ten_khoan_chi", "loai_nghiep_vu", "phan_loai", "so_tien",
			"ngay_can_tt", "hinh_thuc", "nha_cung_cap", "chung_tu_thue",
			"phuong_thuc", "trang_thai", "nguoi_tao", "creation", "ho_so_tt",
		],
		order_by="creation desc",
		limit_page_length=max(1, min(500, cint(so_dong) or 100)),
	)
	for d in ds:
		d["nhan_trang_thai"] = NHAN_TRANG_THAI.get(d["trang_thai"]) or d["trang_thai"]
		d["can_giam_doc"] = 1 if can_giam_doc_duyet(d["so_tien"]) else 0
	return {"ds": ds, "nguong_giam_doc": NGUONG_GIAM_DOC}


@frappe.whitelist()
def danh_muc():
	"""Danh mục cho màn hình đổ vào các ô chọn."""
	return {
		"loai_nghiep_vu": list(LOAI_NGHIEP_VU),
		"phan_loai": list(PHAN_LOAI),
		"phan_loai_tam_ung": list(PL_TAM_UNG),
		"hinh_thuc": [HT_NHAN_VIEN, HT_NCC],
		"chung_tu_thue": [CT_CO_VAT, CT_KHONG_VAT],
		"phuong_thuc": [PT_TIEN_MAT, PT_CHUYEN_KHOAN],
		"nguong_giam_doc": NGUONG_GIAM_DOC,
		"nhac_ncc": "Nếu chưa có nhà cung cấp trong danh mục, anh chị liên hệ Uyên để tạo mã giúp.",
	}
