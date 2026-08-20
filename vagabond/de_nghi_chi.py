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
# Da chi: TIEN DA RA THAT khoi tai khoan, do doi soat SePay xac nhan chu
# khong do ai bam. Them 20/08/2026 cung lan noi webhook OCB.
TT_DA_CHI = "Da chi"

NHAN_TRANG_THAI = {
	TT_NHAP: "Nháp",
	TT_CHO_DUYET: "Chờ mua hàng duyệt",
	TT_CHO_GIAM_DOC: "Chờ giám đốc duyệt",
	TT_CHO_KE_TOAN: "Chờ kế toán hạch toán",
	TT_HOAN_TAT: "Hoàn tất",
	TT_DA_CHI: "Đã chi",
	TT_TRA_LAI: "Bị trả lại",
}

# Chip tren man Danh sach. Anh Viet 20/08/2026 goi ten nam chip: Nhap, Cho
# duyet, Cho chi, Da chi, Da huy.
#
# Vi sao GOM chu khong doi ten trang thai: chuoi duyet ba cap (mua hang,
# giam doc tu 2 trieu, ke toan) la thu anh Viet chot hom 19/08 va dang chay
# dung. Doi trang thai la doi ca chuoi do. Nen giu nguyen ben duoi, con
# chip chi la cach GOM lai cho de nhin.
CHIP_TRANG_THAI = (
	("tat_ca", "Tất cả", None),
	("nhap", "Nháp", (TT_NHAP,)),
	("cho_duyet", "Chờ duyệt", (TT_CHO_DUYET, TT_CHO_GIAM_DOC)),
	("cho_chi", "Chờ chi", (TT_CHO_KE_TOAN, TT_HOAN_TAT)),
	("da_chi", "Đã chi", (TT_DA_CHI,)),
	("da_huy", "Đã huỷ", (TT_TRA_LAI,)),
)

# Chip loc thoi gian.
CHIP_THOI_GIAN = (
	("30", "30 ngày"),
	("7", "7 ngày"),
	("90", "90 ngày"),
	("0", "Tất cả"),
)


def trang_thai_theo_chip(chip):
	"""Chip nay ung voi nhung trang thai nao. THUAN.

	Tra ve None nghia la khong loc (chip Tat ca).
	"""
	for k, _ten, ds in CHIP_TRANG_THAI:
		if k == (chip or "").strip():
			return list(ds) if ds else None
	return None

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


def tien_phieu(phieu):
	"""Số tiền thật của một phiếu, dù là phiếu cũ hay phiếu mới. THUẦN.

	Vì sao phải có hàm này chứ không đọc thẳng một trường
	------------------------------------------------------
	Đổi sang bảng kê nhiều dòng đẻ ra một cái bẫy im lặng: `so_tien` trên
	phiếu cha vẫn còn đó, nhưng phiếu lập từ 20/08/2026 để nó bằng 0 vì tiền
	đã nằm ở các dòng. Bất kỳ chỗ nào còn đọc `so_tien` sẽ thấy 0.

	Chỗ nguy nhất là `buoc_ke_tiep`: đọc 0 thì MỌI phiếu mới, dù 50 triệu,
	đều rơi thẳng xuống kế toán và không bao giờ qua tay giám đốc. Không báo
	lỗi gì cả, phiếu vẫn chạy trơn tru, và cấp duyệt biến mất trong im lặng.

	Nên gom về một hàm: có bảng kê thì cộng bảng kê, không có thì mới đọc
	trường cũ.
	"""
	tong = cong_bang_ke(phieu)
	if tong > 0:
		return tong
	p = phieu or {}
	return flt(p.get("tong_tien")) or flt(p.get("so_tien"))


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


# ==================================================== bảng kê nhiều dòng
#
# Anh Việt 19/08/2026: *"Hiện tại hệ thống đang là 1 phiếu = 1 khoản chi.
# Việc này quá mất thời gian. Em hãy cấu trúc lại theo dạng Master-Detail
# (1 phiếu = Nhiều khoản chi)."*
#
# Bộ phận mua hàng đi chợ một buổi về có mười mấy hoá đơn lẻ. Trước hôm nay
# đó là mười mấy phiếu, mỗi phiếu gõ lại đúng một bộ tên tài khoản, số tài
# khoản, ngân hàng giống hệt nhau, rồi Uyên duyệt mười mấy lần.


def cac_dong(phieu):
	"""Bảng kê của phiếu, luôn trả về list. THUẦN.

	Nhận cả dict lẫn Document, và cả trường hợp chưa có dòng nào.
	"""
	p = phieu or {}
	ds = p.get("cac_khoan") if hasattr(p, "get") else None
	if not ds:
		return []
	ra = []
	for d in ds:
		ra.append(d if isinstance(d, dict) else (d.as_dict() if hasattr(d, "as_dict") else dict(d)))
	return ra


def cong_bang_ke(phieu):
	"""Tổng tiền của phiếu, cộng từ bảng kê. THUẦN.

	Đây là con số DUY NHẤT được dùng để so với ngưỡng giám đốc duyệt. Màn
	hình có tự cộng để hiện cho người gõ thấy ngay, nhưng số đó không bao giờ
	được tin (QT-19): sửa một dòng trong công cụ nhà phát triển của trình
	duyệt là hạ được một phiếu 50 triệu xuống dưới ngưỡng 2 triệu và đi thẳng
	qua mặt giám đốc.
	"""
	return sum(flt(d.get("so_tien")) for d in cac_dong(phieu))


def thieu_gi_dong(dong, so_thu_tu, la_hd_vat=False, phai_co_tep=False, co_tep=True):
	"""Một dòng bảng kê còn thiếu gì. THUẦN.

	`la_hd_vat` và `phai_co_tep` đọc từ Danh mục loại chứng từ chứ không so
	chuỗi với chữ "Hoá đơn VAT", vì đổi tên một dòng danh mục thì không được
	phép làm im lặng tắt mất ba ô hoá đơn. Xem `vagabond_loai_chung_tu.py`.
	"""
	d = dong or {}
	stt = "Khoản %s" % so_thu_tu
	thieu = []

	if not (d.get("noi_dung") or "").strip():
		thieu.append("%s: chưa ghi nội dung chi" % stt)
	if flt(d.get("so_tien")) <= 0:
		thieu.append("%s: số tiền phải lớn hơn 0" % stt)

	pl = (d.get("phan_loai") or "").strip()
	if not pl:
		thieu.append("%s: chưa chọn phân loại chi phí" % stt)
	elif pl not in TK_THEO_PHAN_LOAI and pl not in PL_TAM_UNG:
		thieu.append("%s: phân loại \"%s\" không nằm trong danh mục" % (stt, pl))

	if not (d.get("loai_chung_tu") or "").strip():
		thieu.append("%s: chưa chọn loại chứng từ" % stt)

	if la_hd_vat:
		if not (d.get("so_hoa_don") or "").strip():
			thieu.append("%s: hoá đơn VAT thì phải có số hoá đơn" % stt)
		if not d.get("ngay_hoa_don"):
			thieu.append("%s: hoá đơn VAT thì phải có ngày hoá đơn" % stt)
		if not (d.get("mst") or "").strip():
			thieu.append("%s: hoá đơn VAT thì phải có mã số thuế người bán" % stt)

	if phai_co_tep and not co_tep:
		thieu.append("%s: loại chứng từ này bắt buộc đính kèm tệp" % stt)

	return thieu


def can_tru_tam_ung(tien_tam_ung, da_hoan_ung):
	"""Còn nợ bao nhiêu sau khi cấn trừ. THUẦN.

	Trả về (con_no, cong_ty_no_lai, cau_nhac).

	CỐ Ý KHÔNG chặn khi hoàn ứng vượt tạm ứng. Nhân viên ứng 2 triệu rồi
	tiêu 2 triệu 3 là chuyện bình thường ngoài đời, và lúc đó công ty nợ lại
	họ 300 nghìn. Chặn ở đây là bắt người ta khai gian cho khớp con số, mà
	một khi đã khai gian một lần thì cả bảng cấn trừ không còn dùng được.
	"""
	ung = flt(tien_tam_ung)
	hoan = flt(da_hoan_ung)
	con = ung - hoan
	if con > 0.5:
		return con, 0.0, "Còn %s đ chưa hoàn ứng." % _tien(con)
	if con < -0.5:
		return 0.0, -con, "Đã tiêu vượt tạm ứng %s đ, công ty trả lại phần này." % _tien(-con)
	return 0.0, 0.0, "Đã hoàn ứng đủ."


def _tien(v):
	"""Số tiền cho người Việt đọc. THUẦN."""
	try:
		return "{:,.0f}".format(flt(v)).replace(",", ".")
	except Exception:
		return str(v)


def thieu_gi(phieu):
	"""Phiếu còn thiếu những gì trước khi gửi đi duyệt. THUẦN.

	`phieu` là dict. Trả về danh sách câu tiếng Việt, rỗng nghĩa là đủ.

	Gom hết vào một hàm thuần thay vì rải `frappe.throw` khắp nơi: như vậy
	màn hình nhắc được CẢ danh sách còn thiếu trong một lần, thay vì người
	lập sửa một cái rồi bấm lại mới biết còn thiếu cái nữa.
	"""
	p = phieu or {}
	thieu = []
	dm = p.get("_dm_chung_tu") or {}

	if not p.get("ngay_can_tt"):
		thieu.append("Ngày cần thanh toán")

	nv = (p.get("loai_nghiep_vu") or "").strip()
	if nv not in LOAI_NGHIEP_VU:
		thieu.append("Loại nghiệp vụ")

	# Bảng kê. Từ 20/08/2026 đây mới là chỗ chứa nội dung, số tiền, phân loại
	# và hoá đơn; các trường cùng tên trên phiếu cha chỉ còn để đọc phiếu cũ.
	ds = cac_dong(p)
	if not ds:
		thieu.append("Bảng kê chưa có khoản chi nào, bấm Thêm khoản chi giúp em")
	for i, d in enumerate(ds, 1):
		mo = dm.get((d.get("loai_chung_tu") or "").strip()) or {}
		thieu.extend(
			thieu_gi_dong(
				d, i,
				la_hd_vat=bool(mo.get("la_hoa_don_vat")),
				phai_co_tep=bool(mo.get("bat_buoc_tep")),
				co_tep=bool(d.get("_co_tep")),
			)
		)

	ht = (p.get("hinh_thuc") or "").strip()
	if ht not in (HT_NHAN_VIEN, HT_NCC):
		thieu.append("Hình thức thụ hưởng")

	# Có hoá đơn VAT thì phải gắn được người bán, nếu không thì tờ hoá đơn
	# không lên bảng kê mua vào được. Trước đây đọc cờ trên phiếu; nay đọc
	# từ CÁC DÒNG, vì một phiếu giờ có thể vừa có dòng có hoá đơn vừa không.
	if co_hoa_don_vat(p) and ht == HT_NCC and not (p.get("nha_cung_cap") or "").strip():
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


def co_hoa_don_vat(phieu):
	"""Phiếu có ít nhất một dòng mang hoá đơn VAT không. THUẦN.

	Đọc theo CỜ của Danh mục loại chứng từ, truyền vào qua `_dm_chung_tu`.
	Không so chuỗi với chữ "Hoá đơn VAT": xem lý do trong
	`vagabond_loai_chung_tu.py`.
	"""
	p = phieu or {}
	dm = p.get("_dm_chung_tu") or {}
	for d in cac_dong(p):
		if (dm.get((d.get("loai_chung_tu") or "").strip()) or {}).get("la_hoa_don_vat"):
			return True
	return False


def ly_do_chan(phieu):
	"""Phiếu này có bị chặn thẳng không, và vì sao. THUẦN.

	Khác `thieu_gi` ở chỗ: thiếu thì bổ sung là xong, còn bị chặn thì phải
	đi đường khác. Trả về câu giải thích, hoặc None nếu không chặn.
	"""
	p = phieu or {}
	# Soi TỪNG DÒNG, không soi trường phan_loai trên phiếu cha nữa. Một phiếu
	# mười dòng mà dòng thứ bảy là cái máy đánh trứng thì vẫn phải chặn, chứ
	# không phải chỉ chặn khi cả phiếu là tài sản cố định.
	for i, d in enumerate(cac_dong(p), 1):
		if (d.get("phan_loai") or "").strip() in CHAN_TSCD:
			return (
				"Khoản %s là tài sản cố định nên không đi đường đề nghị chi lặt "
				"vặt được. Tài sản cố định cần đơn mua hàng, cần theo dõi khấu hao "
				"và cần hồ sơ tài sản, nhét vào một phiếu hoàn tiền là mất cả ba. "
				"Anh chị tách khoản đó ra và lập Đơn mua hàng giúp em, hoặc nhắn "
				"Uyên để Uyên lập." % i
			)
	if la_tam_ung((p.get("loai_nghiep_vu") or "")) and co_hoa_don_vat(p):
		return (
			"Tạm ứng thì chưa phát sinh chi phí nên chưa có hoá đơn VAT. Nếu "
			"đã có hoá đơn rồi thì đây là khoản hoàn ứng chứ không phải tạm "
			"ứng, anh chị đổi Loại nghiệp vụ giúp em."
		)
	# Hoàn ứng thì phải nói rõ hoàn cho lần tạm ứng nào, nếu không thì bảng
	# cấn trừ không bao giờ khớp và không ai biết nhân viên còn nợ bao nhiêu.
	nv = (p.get("loai_nghiep_vu") or "").strip()
	if nv == NV_HOAN_UNG and not (p.get("thuoc_tam_ung") or "").strip():
		return (
			"Phiếu hoàn ứng phải chỉ rõ nó hoàn cho lần tạm ứng nào. Bấm ô "
			"\"Thuộc mã Tạm ứng\" rồi chọn phiếu tạm ứng của anh chị giúp em. "
			"Nếu khoản này không phải hoàn ứng thì đổi Loại nghiệp vụ sang Chi phí."
		)
	if nv != NV_HOAN_UNG and (p.get("thuoc_tam_ung") or "").strip():
		return (
			"Chỉ phiếu Hoàn ứng mới gắn được vào một mã tạm ứng. Anh chị đổi "
			"Loại nghiệp vụ sang Hoàn ứng, hoặc bỏ ô Thuộc mã Tạm ứng đi giúp em."
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


DM_CT = "Vagabond Loai Chung Tu"

# Bộ khởi tạo danh mục loại chứng từ. Chỉ tạo khi thiếu, KHÔNG đè lên dòng
# kế toán đã sửa: danh mục này chị Dung tự thêm bớt được, và một lần deploy
# không được phép xoá công sức đó.
DM_CT_MAC_DINH = (
	# (tên, là hoá đơn VAT, bắt buộc tệp, thứ tự)
	("Hoá đơn VAT", 1, 1, 10),
	("Hoá đơn bán lẻ", 0, 1, 20),
	("Phiếu thu của người bán", 0, 1, 30),
	("Báo giá", 0, 1, 40),
	("Hợp đồng", 0, 1, 50),
	("Biên bản", 0, 1, 60),
	("Bảng kê không hoá đơn", 0, 0, 70),
	("Không có chứng từ", 0, 0, 80),
)


def dung_danh_muc_chung_tu():
	"""Tạo các dòng danh mục còn thiếu. LẶP LẠI ĐƯỢC, gọi bao nhiêu lần cũng được."""
	for ten, vat, tep, tt in DM_CT_MAC_DINH:
		if frappe.db.exists(DM_CT, ten):
			continue
		d = frappe.get_doc({
			"doctype": DM_CT, "ten": ten, "la_hoa_don_vat": vat,
			"bat_buoc_tep": tep, "dang_dung": 1, "thu_tu": tt,
		})
		d.flags.ignore_permissions = True
		d.insert(ignore_permissions=True)


def _dm_chung_tu():
	"""Ánh xạ tên loại chứng từ sang hai cờ của nó.

	Đọc một lần rồi truyền vào các hàm THUẦN qua khoá `_dm_chung_tu`, để
	`thieu_gi` và `ly_do_chan` vẫn kiểm thử được mà không cần site.
	"""
	ra = {}
	try:
		for r in frappe.get_all(
			DM_CT, fields=["name", "la_hoa_don_vat", "bat_buoc_tep"], limit_page_length=0
		):
			ra[r["name"]] = {
				"la_hoa_don_vat": cint(r.get("la_hoa_don_vat")),
				"bat_buoc_tep": cint(r.get("bat_buoc_tep")),
			}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "de_nghi_chi: doc danh muc chung tu loi")
	return ra


def _kem_dm(doc):
	"""Bản dict của phiếu, có kèm danh mục chứng từ để các hàm THUẦN dùng."""
	d = doc.as_dict() if hasattr(doc, "as_dict") else dict(doc or {})
	d["_dm_chung_tu"] = _dm_chung_tu()
	return d


def trung_hoa_don(doc):
	"""Tờ hoá đơn này đã nằm ở phiếu khác hoặc hoá đơn mua nào chưa.

	Hai bạn cùng chụp một tờ bill, hoặc một người nộp lại lần hai sau khi bị
	trả lại. Trả về danh sách mã chứng từ đã có, rỗng nghĩa là chưa trùng.
	"""
	ma_minh = doc.get("name") or ""
	ds = cac_dong(doc)
	# Phiếu một dòng lập trước 20/08/2026 vẫn giữ hoá đơn trên phiếu cha, nên
	# vẫn phải soi. Bỏ nhánh này là mở lại đúng cái cửa mà hàm này sinh ra để
	# đóng, chỉ cho những tờ hoá đơn cũ.
	if not ds and (doc.get("so_hoa_don") or "").strip():
		ds = [{
			"mst": doc.get("mst"), "so_hoa_don": doc.get("so_hoa_don"),
			"ngay_hoa_don": doc.get("ngay_hoa_don"),
		}]

	da_co = []
	# Trùng NGAY TRONG một phiếu: hai bạn cùng chụp một tờ bill rồi cùng dán
	# vào một phiếu. Đây là ca mới sinh ra do đổi sang nhiều dòng, và không
	# một phép kiểm nào tra cơ sở dữ liệu bắt được nó.
	trong_phieu = {}
	for i, d in enumerate(ds, 1):
		khoa = khoa_trung_hoa_don(d.get("mst"), d.get("so_hoa_don"), d.get("ngay_hoa_don"))
		if not khoa:
			continue
		if khoa in trong_phieu:
			da_co.append("chính phiếu này, khoản %s và khoản %s" % (trong_phieu[khoa], i))
			continue
		trong_phieu[khoa] = i

		# Phiếu khác trên hệ.
		for k in frappe.get_all(
			"Vagabond De Nghi Chi Dong",
			filters={"so_hoa_don": d.get("so_hoa_don"), "parent": ["!=", ma_minh]},
			fields=["parent", "mst", "ngay_hoa_don"],
			limit_page_length=0,
		):
			if khoa_trung_hoa_don(k.get("mst"), d.get("so_hoa_don"), k.get("ngay_hoa_don")) != khoa:
				continue
			if frappe.db.get_value(DT, k["parent"], "trang_thai") == TT_TRA_LAI:
				continue
			da_co.append(k["parent"])

		# Phiếu cũ một dòng, hoá đơn còn nằm trên phiếu cha.
		for k in frappe.get_all(
			DT,
			filters={
				"so_hoa_don": d.get("so_hoa_don"),
				"trang_thai": ["!=", TT_TRA_LAI],
				"name": ["!=", ma_minh],
			},
			fields=["name", "mst", "ngay_hoa_don"],
			limit_page_length=0,
		):
			if khoa_trung_hoa_don(k.get("mst"), d.get("so_hoa_don"), k.get("ngay_hoa_don")) == khoa:
				da_co.append(k["name"])

		# Hoá đơn mua đã vào sổ.
		if doc.get("nha_cung_cap"):
			da_co += [
				h["name"]
				for h in frappe.get_all(
					PI,
					filters={
						"bill_no": d.get("so_hoa_don"),
						"supplier": doc.get("nha_cung_cap"),
						"docstatus": ["<", 2],
					},
					fields=["name"],
					limit_page_length=0,
				)
			]
	# Giữ thứ tự nhìn thấy, bỏ trùng lặp: một phiếu bị nhắc hai lần trong câu
	# báo lỗi thì người đọc tưởng là hai phiếu khác nhau.
	ra, thay = [], set()
	for x in da_co:
		if x not in thay:
			thay.add(x)
			ra.append(x)
	return ra


def truoc_khi_luu(doc, method=None):
	"""Điền hộ những gì điền được, và chặn những gì phải chặn. Gọi từ before_validate."""
	if not doc.get("nguoi_tao"):
		doc.nguoi_tao = frappe.session.user
	if not doc.get("trang_thai"):
		doc.trang_thai = TT_NHAP

	chan = ly_do_chan(_kem_dm(doc))
	if chan:
		frappe.throw(chan)

	# TỔNG TIỀN CỘNG LẠI Ở ĐÂY, mỗi lần lưu, không nhận số từ màn hình.
	#
	# Đây là con số quyết định phiếu có phải lên giám đốc duyệt hay không.
	# Nhận số của máy khách thì sửa một dòng trong công cụ nhà phát triển của
	# trình duyệt là hạ được phiếu 50 triệu xuống dưới ngưỡng 2 triệu và đi
	# thẳng qua mặt giám đốc. Đúng tinh thần QT-19.
	doc.tong_tien = cong_bang_ke(doc)
	# Soi guong sang truong `so_tien` cu.
	#
	# Hai ly do, va ly do thu hai moi la ly do that. Mot: truong do dang la
	# bat buoc trong doctype, khong dien thi khong luu duoc phieu nao ca - da
	# vap that tren site ngay 20/08/2026 voi MandatoryError. Hai: van con the
	# co doan ma nao do doc `so_tien` ma em chua tim ra het; de no bang 0 thi
	# doan ay doc ra 0 va im lang tinh sai. Ghi dung so vao day thi du co bo
	# sot cho nao, cho do van doc ra con so dung.
	#
	# Van KHONG duoc dung `so_tien` de quyet dinh gi ca: moi phep quyet dinh
	# di qua `tien_phieu()`. Day chi la ban sao cho an toan.
	if doc.tong_tien:
		doc.so_tien = doc.tong_tien

	dm = _dm_chung_tu()
	for d in doc.get("cac_khoan") or []:
		mo = dm.get((d.get("loai_chung_tu") or "").strip()) or {}
		# Tài khoản chi phí của TỪNG DÒNG. Chỉ điền khi kế toán chưa tự chọn:
		# đè lên lựa chọn của chị Dung là lỗi nặng hơn hẳn việc để trống.
		if not d.get("tk_chi_phi"):
			ma = _ma_tk_theo_so_hieu(
				tk_goi_y(
					d.get("phan_loai"),
					CT_CO_VAT if mo.get("la_hoa_don_vat") else CT_KHONG_VAT,
				),
				doc.get("company"),
			)
			if ma:
				d.tk_chi_phi = ma
		# Dòng không phải hoá đơn VAT thì ba ô hoá đơn phải sạch. Người lập
		# gõ số hoá đơn rồi đổi loại chứng từ sang Báo giá, số cũ nằm lại và
		# sẽ đi khoá trùng của một tờ hoá đơn không tồn tại.
		if not mo.get("la_hoa_don_vat"):
			d.so_hoa_don = None
			d.ngay_hoa_don = None
			d.mst = None
			d.ten_ban = None
			d.dia_chi_ban = None

	# Tạm ứng thì không có phân loại chi phí, xoá đi cho khỏi lẫn vào báo cáo.
	if la_tam_ung(doc.get("loai_nghiep_vu")):
		doc.phan_loai = None

	# Nội dung chuyển khoản: sinh từ mã phiếu, và chỉ sinh khi phiếu ĐÃ có
	# mã (lần lưu đầu tiên thì chưa). Đây là thứ duy nhất phép đối soát bám
	# vào, nên nó phải luôn khớp với mã phiếu chứ không ai gõ tay.
	if doc.get("name") and not (doc.get("noi_dung_ck") or "").strip():
		doc.noi_dung_ck = noi_dung_ck(doc.name)

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

	# Tệp đính kèm: đếm một lần rồi gắn cờ vào từng dòng. Hệ đang đính tệp
	# vào cả PHIẾU chứ chưa đính theo dòng, nên ở đây cờ là chung cho mọi
	# dòng. Khi nào đính theo dòng thì chỉ phải đổi đúng chỗ này.
	d_dict = _kem_dm(doc)
	co_tep = bool(_so_tep(ma_phieu))
	for d in d_dict.get("cac_khoan") or []:
		d["_co_tep"] = co_tep

	thieu = thieu_gi(d_dict)
	if thieu:
		frappe.throw("Còn thiếu: %s." % "; ".join(thieu))

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
			"Có hoá đơn trong bảng kê đã nằm ở %s rồi. Nếu đây là tờ khác thì "
			"anh chị kiểm lại số hoá đơn và ngày giúp em." % ", ".join(trung)
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
		doc.trang_thai = buoc_ke_tiep(tien_phieu(doc))
	elif doc.trang_thai == TT_CHO_GIAM_DOC:
		doc.gd_boi, doc.gd_luc = nguoi, luc
		doc.trang_thai = TT_CHO_KE_TOAN
	else:
		doc.kt_boi, doc.kt_luc = nguoi, luc
		doc.trang_thai = TT_HOAN_TAT

	if (ghi_chu or "").strip():
		doc.ghi_chu = ((doc.ghi_chu or "") + "\n" + ghi_chu).strip()
	doc.save(ignore_permissions=True)
	return {
		"ok": 1, "trang_thai": doc.trang_thai,
		"nhan_trang_thai": NHAN_TRANG_THAI.get(doc.trang_thai) or doc.trang_thai,
	}


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
def ds_man(chip="tat_ca", so_ngay=30, tim="", so_dong=100):
	"""Danh sách phiếu cho MÀN DANH SÁCH, kèm số đếm từng chip.

	Anh Việt 20/08/2026: *"Bất kỳ phân hệ nào có nút Tạo phiếu thì bắt buộc
	phải có màn hình Danh sách để xem lại."*

	Con số trên chip là số THẬT của cả sổ trong khoảng thời gian đang chọn,
	không phải số dòng đang hiện. Đếm theo đúng ô tìm đang gõ, nếu không thì
	gõ "Nước" ra 3 dòng mà chip vẫn báo 40 và người đọc không biết tin cái
	nào (bài học từ màn Hoàn tiền).
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	goc = {}
	# Người thường chỉ thấy phiếu của mình. Mua hàng, giám đốc, kế toán thấy
	# hết, vì họ là người duyệt và người chi.
	if not (_vai() & (VAI_DUYET | VAI_GIAM_DOC | VAI_KE_TOAN)):
		goc["nguoi_tao"] = frappe.session.user
	sn = cint(so_ngay)
	if sn > 0:
		goc["creation"] = [">=", frappe.utils.add_days(nowdate(), -sn)]

	hoac = None
	tim = (tim or "").strip()
	if tim:
		hoac = [["name", "like", "%" + tim + "%"], ["ten_khoan_chi", "like", "%" + tim + "%"]]

	loc = dict(goc)
	tt = trang_thai_theo_chip(chip)
	if tt:
		loc["trang_thai"] = ["in", tt]

	ds = frappe.get_all(
		DT, filters=loc, or_filters=hoac,
		fields=[
			"name", "ten_khoan_chi", "loai_nghiep_vu", "so_tien", "tong_tien",
			"trang_thai", "nguoi_tao", "creation", "ngay_can_tt", "phuong_thuc",
			"hinh_thuc", "nha_cung_cap", "ma_gd", "ngay_da_chi", "thuoc_tam_ung",
		],
		order_by="creation desc",
		limit_page_length=max(1, min(500, cint(so_dong) or 100)),
	)
	dem_dong = {}
	if ds:
		for r in frappe.get_all(
			"Vagabond De Nghi Chi Dong",
			filters={"parent": ["in", [d["name"] for d in ds]]},
			fields=["parent"], limit_page_length=0,
		):
			dem_dong[r["parent"]] = dem_dong.get(r["parent"], 0) + 1
	for d in ds:
		d["nhan_trang_thai"] = NHAN_TRANG_THAI.get(d["trang_thai"]) or d["trang_thai"]
		d["tien"] = tien_phieu(d)
		d["so_khoan"] = dem_dong.get(d["name"], 0)
		d["tieu_de"] = d.get("ten_khoan_chi") or "(chưa đặt tên)"
		if d["so_khoan"] > 1:
			d["tieu_de"] += " và %s khoản khác" % (d["so_khoan"] - 1)

	# Đếm chip: một truy vấn cho mỗi chip, trên cùng bộ lọc gốc.
	dem = {}
	for k, _ten, nhom in CHIP_TRANG_THAI:
		l2 = dict(goc)
		if nhom:
			l2["trang_thai"] = ["in", list(nhom)]
		dem[k] = len(frappe.get_all(
			DT, filters=l2, or_filters=hoac, fields=["name"], limit_page_length=0
		))
	return {
		"ds": ds, "dem": dem, "chip": chip, "so_ngay": sn, "tim": tim,
		"chip_trang_thai": [{"k": k, "ten": t} for k, t, _n in CHIP_TRANG_THAI],
		"chip_thoi_gian": [{"k": k, "ten": t} for k, t in CHIP_THOI_GIAN],
		"duoc_duyet": 1 if (_vai() & (VAI_DUYET | VAI_GIAM_DOC | VAI_KE_TOAN)) else 0,
		"nguong_giam_doc": NGUONG_GIAM_DOC,
	}


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
			"tong_tien", "thuoc_tam_ung",
			"ngay_can_tt", "hinh_thuc", "nha_cung_cap", "chung_tu_thue",
			"phuong_thuc", "trang_thai", "nguoi_tao", "creation", "ho_so_tt",
		],
		order_by="creation desc",
		limit_page_length=max(1, min(500, cint(so_dong) or 100)),
	)
	# Số dòng và tiêu đề rút gọn: danh sách phải nói được "phiếu này có mấy
	# khoản" mà không phải mở từng phiếu ra.
	dem, dau = {}, {}
	if ds:
		for r in frappe.get_all(
			"Vagabond De Nghi Chi Dong",
			filters={"parent": ["in", [d["name"] for d in ds]]},
			fields=["parent", "noi_dung", "idx"],
			order_by="parent asc, idx asc",
			limit_page_length=0,
		):
			dem[r["parent"]] = dem.get(r["parent"], 0) + 1
			dau.setdefault(r["parent"], r.get("noi_dung") or "")
	for d in ds:
		d["nhan_trang_thai"] = NHAN_TRANG_THAI.get(d["trang_thai"]) or d["trang_thai"]
		d["so_khoan"] = dem.get(d["name"], 0)
		d["tien"] = tien_phieu(d)
		d["can_giam_doc"] = 1 if can_giam_doc_duyet(d["tien"]) else 0
		# Tiêu đề: phiếu mới lấy nội dung khoản đầu, phiếu cũ lấy trường cũ.
		d["tieu_de"] = dau.get(d["name"]) or d.get("ten_khoan_chi") or "(chưa đặt tên)"
		if d["so_khoan"] > 1:
			d["tieu_de"] += " và %s khoản khác" % (d["so_khoan"] - 1)
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
		# Danh mục loại chứng từ, kèm hai cờ. Màn hình bật ba ô hoá đơn theo
		# cờ `la_hoa_don_vat` chứ không so tên, để đổi tên dòng danh mục
		# không làm im lặng tắt mất ba ô đó.
		"loai_chung_tu": _ds_chung_tu(),
		"nguong_giam_doc": NGUONG_GIAM_DOC,
		"nhac_ncc": "Nếu chưa có nhà cung cấp trong danh mục, anh chị liên hệ Uyên để tạo mã giúp.",
	}


@frappe.whitelist()
def tao(du_lieu=None, gui_luon=0):
	"""Lập một đề nghị chi từ APP. Ai cũng lập được.

	Anh Việt 19/08/2026: *"nút Tạo yêu cầu thanh toán nội bộ em cho vào phân
	hệ đặt hàng dùm anh và cho mọi nhân viên đều nhìn thấy để làm khi các bạn
	mua hàng"*.

	Trước hàm này, phiếu chỉ lập được trên Desk. Mà anh Việt đã chốt từ
	13/08: *"anh thấy thao tác trên desktop bị rối quá nên mình làm trên
	app"*. Bạn bếp và bạn quầy mua chai nước mắm thì không ai mở Desk.

	Hàm này CỐ Ý mỏng: nó chỉ đổ dữ liệu vào doctype rồi lưu. Mọi luật
	nghiệp vụ - tài khoản hạch toán theo phân loại, chặn tài sản cố định,
	bắt buộc số hoá đơn khi có VAT - đều nằm ở `truoc_khi_luu` và chạy qua
	hook before_validate. Viết lại luật ở đây là mở đường cho hai bộ luật
	lệch nhau, mà một trong hai sẽ sai vào một ngày không ai để ý.
	"""
	d = frappe.parse_json(du_lieu) if isinstance(du_lieu, str) else (du_lieu or {})
	if not isinstance(d, dict):
		frappe.throw("Dữ liệu gửi lên không đúng định dạng.")

	dong = d.get("cac_khoan") or []
	if isinstance(dong, str):
		dong = frappe.parse_json(dong) or []
	if not isinstance(dong, list) or not dong:
		frappe.throw(
			"Bảng kê chưa có khoản chi nào. Bấm \"+ Thêm khoản chi\" rồi ghi ít "
			"nhất một khoản giúp em."
		)
	# Chặn phiếu khổng lồ ngay tại cổng. 200 dòng là đã quá xa mọi nhu cầu
	# thật của một buổi đi chợ, mà lại đủ để làm nghẽn cả lần lưu.
	if len(dong) > 200:
		frappe.throw(
			"Một phiếu tối đa 200 khoản, phiếu này có %s. Anh chị tách ra làm "
			"nhiều phiếu giúp em." % len(dong)
		)

	doc = frappe.new_doc(DT)
	for f in (
		"loai_nghiep_vu", "dien_giai", "hinh_thuc", "nha_cung_cap",
		"phuong_thuc", "ten_tk", "so_tk", "ngan_hang", "thuoc_tam_ung",
		"ghi_chu",
	):
		v = d.get(f)
		doc.set(f, (str(v).strip() if isinstance(v, str) else v) or None)
	doc.ngay_can_tt = d.get("ngay_can_tt") or None
	doc.nguoi_tao = frappe.session.user

	for k in dong:
		if not isinstance(k, dict):
			continue
		doc.append("cac_khoan", {
			"noi_dung": str(k.get("noi_dung") or "").strip() or None,
			"so_tien": flt(k.get("so_tien")),
			"phan_loai": str(k.get("phan_loai") or "").strip() or None,
			"loai_chung_tu": str(k.get("loai_chung_tu") or "").strip() or None,
			"so_hoa_don": str(k.get("so_hoa_don") or "").strip() or None,
			"ngay_hoa_don": k.get("ngay_hoa_don") or None,
			"mst": str(k.get("mst") or "").strip() or None,
			"ten_ban": str(k.get("ten_ban") or "").strip() or None,
			"dia_chi_ban": str(k.get("dia_chi_ban") or "").strip() or None,
			"ghi_chu": str(k.get("ghi_chu") or "").strip() or None,
		})
	# Tên phiếu cho dễ tìm trên Desk. KHÔNG dùng làm số liệu: mọi con số đọc
	# từ bảng kê.
	doc.ten_khoan_chi = (
		str((dong[0] or {}).get("noi_dung") or "").strip() or "Đề nghị chi"
	)[:130]
	doc.trang_thai = TT_NHAP
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	# Nội dung chuyển khoản chỉ dựng được SAU khi phiếu có mã: doctype này
	# đánh mã theo format nên lúc before_validate chạy thì `name` còn trống.
	frappe.db.set_value(DT, doc.name, "noi_dung_ck", noi_dung_ck(doc.name), update_modified=False)
	doc.noi_dung_ck = noi_dung_ck(doc.name)
	frappe.db.commit()

	# Gửi duyệt luôn thì đi qua ĐÚNG hàm gui_duyet, không tự đặt trạng thái.
	# Hàm đó giữ luật ai duyệt trước ai duyệt sau và mốc 2 triệu; đặt tay ở
	# đây là lách mất cả hai.
	if cint(gui_luon):
		gui_duyet(doc.name)
		doc.reload()
	return {
		"ok": 1, "ma": doc.name, "trang_thai": doc.trang_thai,
		"nhan_trang_thai": NHAN_TRANG_THAI.get(doc.trang_thai) or doc.trang_thai,
	}


def _ds_chung_tu():
	"""Danh mục loại chứng từ cho màn hình, kèm hai cờ.

	Tự dựng danh mục nếu site còn trống, để lần deploy đầu tiên không rơi vào
	cảnh màn hình có ô chọn mà trong ô không có gì.
	"""
	try:
		if not frappe.db.count(DM_CT):
			dung_danh_muc_chung_tu()
			frappe.db.commit()
		return [
			{
				"ten": r["name"],
				"la_hoa_don_vat": cint(r.get("la_hoa_don_vat")),
				"bat_buoc_tep": cint(r.get("bat_buoc_tep")),
			}
			for r in frappe.get_all(
				DM_CT,
				filters={"dang_dung": 1},
				fields=["name", "la_hoa_don_vat", "bat_buoc_tep", "thu_tu"],
				order_by="thu_tu asc, name asc",
				limit_page_length=0,
			)
		]
	except Exception:
		frappe.log_error(frappe.get_traceback(), "de_nghi_chi: doc danh muc chung tu loi")
		return []


# ------------------------------------------------------ cấn trừ hoàn ứng


def _tong_hoan_ung(ma_tam_ung):
	"""Đã hoàn ứng bao nhiêu cho một phiếu tạm ứng.

	CHỈ tính phiếu chưa bị trả lại. Một phiếu hoàn ứng bị Uyên trả về để sửa
	thì chưa phải là tiền đã quyết toán, mà tính nó vào là bảng cấn trừ báo
	nhân viên đã trả xong trong khi thực tế chưa.
	"""
	if not ma_tam_ung:
		return 0.0
	tong = 0.0
	for r in frappe.get_all(
		DT,
		filters={
			"thuoc_tam_ung": ma_tam_ung,
			"trang_thai": ["!=", TT_TRA_LAI],
		},
		fields=["name", "tong_tien", "so_tien"],
		limit_page_length=0,
	):
		tong += flt(r.get("tong_tien")) or flt(r.get("so_tien"))
	return tong


@frappe.whitelist()
def tam_ung_cua_toi(nguoi=None):
	"""Các phiếu tạm ứng còn dư nợ của một người, để chọn khi lập hoàn ứng.

	Anh Việt 19/08/2026 đặt ô "Thuộc mã Tạm ứng" để *"sau này làm luồng cấn
	trừ hoàn ứng"*. Hàm này là mặt đọc của ô đó.

	Chỉ liệt kê phiếu ĐÃ HOÀN TẤT: tạm ứng chưa chi thì chưa có tiền trong
	tay ai, hoàn ứng cho nó là hoàn một khoản chưa tồn tại.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	nguoi = (nguoi or "").strip() or frappe.session.user
	# Người thường chỉ thấy tạm ứng của chính mình. Mua hàng và kế toán thấy
	# của mọi người, vì họ là người lập hộ và người đối chiếu.
	if nguoi != frappe.session.user and not (
		_vai() & (VAI_DUYET | VAI_GIAM_DOC | VAI_KE_TOAN)
	):
		nguoi = frappe.session.user

	ra = []
	for r in frappe.get_all(
		DT,
		filters={
			"loai_nghiep_vu": NV_TAM_UNG,
			"nguoi_tao": nguoi,
			"trang_thai": TT_HOAN_TAT,
		},
		fields=["name", "ten_khoan_chi", "tong_tien", "so_tien", "creation", "ngay_can_tt"],
		order_by="creation desc",
		limit_page_length=0,
	):
		ung = flt(r.get("tong_tien")) or flt(r.get("so_tien"))
		hoan = _tong_hoan_ung(r["name"])
		con, cong_ty_no, nhac = can_tru_tam_ung(ung, hoan)
		ra.append({
			"ma": r["name"],
			"ten": r.get("ten_khoan_chi") or "",
			"ngay": str(r.get("creation") or "")[:10],
			"da_ung": ung,
			"da_hoan_ung": hoan,
			"con_no": con,
			"cong_ty_no_lai": cong_ty_no,
			"nhac": nhac,
		})
	return {"ds": ra, "nguoi": nguoi}


@frappe.whitelist()
def chi_tiet(ma_phieu=None):
	"""Một phiếu đầy đủ, kèm bảng kê và tình trạng cấn trừ."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not frappe.db.exists(DT, ma_phieu):
		frappe.throw(
			"Không tìm thấy phiếu %s. Quay lại danh sách rồi mở phiếu khác "
			"giúp em." % ma_phieu
		)
	doc = frappe.get_doc(DT, ma_phieu)
	if doc.nguoi_tao != frappe.session.user and not (
		_vai() & (VAI_DUYET | VAI_GIAM_DOC | VAI_KE_TOAN)
	):
		frappe.throw("Phiếu này của người khác nên anh chị không mở được.")

	ra = doc.as_dict()
	for k in list(ra.keys()):
		if k.startswith("_"):
			ra.pop(k, None)
	ra["nhan_trang_thai"] = NHAN_TRANG_THAI.get(doc.trang_thai) or doc.trang_thai
	# Bù cho phiếu lập thẳng trên Desk, hoặc phiếu cũ lập trước 20/08/2026.
	if not (ra.get("noi_dung_ck") or "").strip():
		ra["noi_dung_ck"] = noi_dung_ck(doc.name)
		frappe.db.set_value(DT, doc.name, "noi_dung_ck", ra["noi_dung_ck"], update_modified=False)
	# Tính lại ở máy chủ chứ không trả trường đã lưu: nếu vì lý do gì đó
	# trường `tong_tien` lệch với bảng kê thì màn hình phải thấy số ĐÚNG.
	ra["tien"] = tien_phieu(ra)
	ra["can_giam_doc"] = 1 if can_giam_doc_duyet(ra["tien"]) else 0
	ra["so_tep"] = _so_tep(ma_phieu)
	# Nút Duyệt chỉ vẽ khi MÁY CHỦ nói người đang xem duyệt được ở BƯỚC HIỆN
	# TẠI. Không để màn hình tự suy theo vai: luật thật còn có "người lập
	# không tự duyệt phiếu của chính mình", mà màn hình thì không biết ai lập.
	duoc, vi_sao = duoc_duyet_khong(
		doc.trang_thai, _vai(), doc.nguoi_tao == frappe.session.user
	)
	ra["duoc_duyet_buoc_nay"] = 1 if duoc else 0
	ra["vi_sao_khong_duyet"] = "" if duoc else vi_sao
	ra["tep"] = [
		{"url": f["file_url"], "ten": f["file_name"]}
		for f in frappe.get_all(
			"File",
			filters={"attached_to_doctype": DT, "attached_to_name": ma_phieu},
			fields=["file_url", "file_name"],
			limit_page_length=0,
		)
	]

	# Cấn trừ. Phiếu tạm ứng thì nhìn xuống, phiếu hoàn ứng thì nhìn lên.
	ra["can_tru"] = None
	if (doc.loai_nghiep_vu or "") == NV_TAM_UNG:
		hoan = _tong_hoan_ung(ma_phieu)
		con, cong_ty_no, nhac = can_tru_tam_ung(ra["tien"], hoan)
		ra["can_tru"] = {
			"vai": "tam_ung", "da_ung": ra["tien"], "da_hoan_ung": hoan,
			"con_no": con, "cong_ty_no_lai": cong_ty_no, "nhac": nhac,
			"phieu_hoan": frappe.get_all(
				DT,
				filters={"thuoc_tam_ung": ma_phieu, "trang_thai": ["!=", TT_TRA_LAI]},
				fields=["name", "tong_tien", "so_tien", "trang_thai"],
				limit_page_length=0,
			),
		}
	elif doc.get("thuoc_tam_ung"):
		g = frappe.db.get_value(
			DT, doc.thuoc_tam_ung, ["name", "tong_tien", "so_tien"], as_dict=True
		) or {}
		ung = flt(g.get("tong_tien")) or flt(g.get("so_tien"))
		hoan = _tong_hoan_ung(doc.thuoc_tam_ung)
		con, cong_ty_no, nhac = can_tru_tam_ung(ung, hoan)
		ra["can_tru"] = {
			"vai": "hoan_ung", "ma_tam_ung": doc.thuoc_tam_ung, "da_ung": ung,
			"da_hoan_ung": hoan, "con_no": con, "cong_ty_no_lai": cong_ty_no,
			"nhac": nhac,
		}
	return ra


# ------------------------------------------- chuyển phiếu cũ sang bảng kê


def chuyen_phieu_mot_dong():
	"""Đưa mỗi phiếu một dòng cũ thành một phiếu có đúng một dòng bảng kê.

	QT-20 cấm xoá vĩnh viễn, nên hàm này KHÔNG xoá gì cả: các trường cũ trên
	phiếu cha vẫn nằm nguyên đó, chỉ thêm một dòng bảng kê chép lại đúng nội
	dung ấy. Phiếu cũ mở ra vẫn đọc được, và từ nay đọc được bằng cùng một
	màn hình với phiếu mới.

	LẶP LẠI ĐƯỢC: phiếu nào đã có dòng thì bỏ qua. Chạy lần thứ hai không
	sinh ra dòng thứ hai.

	Ánh xạ loại chứng từ: cờ cũ chỉ có hai giá trị, có VAT và không VAT. Có
	VAT thì về dòng "Hoá đơn VAT", không VAT thì về "Bảng kê không hoá đơn"
	chứ KHÔNG về "Không có chứng từ" - phiếu cũ nào cũng đã bắt buộc đính
	kèm ảnh bill rồi, nên nói là không có chứng từ thì sai với thực tế.
	"""
	da_co = set()
	for r in frappe.get_all(
		"Vagabond De Nghi Chi Dong", fields=["parent"], limit_page_length=0
	):
		da_co.add(r["parent"])

	chuyen, bo_qua = 0, 0
	for r in frappe.get_all(
		DT,
		fields=[
			"name", "ten_khoan_chi", "so_tien", "phan_loai", "chung_tu_thue",
			"so_hoa_don", "ngay_hoa_don", "mst", "tk_chi_phi",
		],
		limit_page_length=0,
	):
		if r["name"] in da_co:
			bo_qua += 1
			continue
		co_vat = (r.get("chung_tu_thue") or "").strip() == CT_CO_VAT
		loai = "Hoá đơn VAT" if co_vat else "Bảng kê không hoá đơn"
		if not frappe.db.exists(DM_CT, loai):
			loai = None
		try:
			# Ghi thẳng vào bảng con, KHÔNG qua doc.save(): save sẽ chạy
			# before_validate, mà hàm đó có thể chặn phiếu cũ vì luật nay đã
			# khác luật lúc phiếu được lập. Một lần migrate không được phép
			# làm phiếu lịch sử không lưu lại được.
			dong = frappe.get_doc({
				"doctype": "Vagabond De Nghi Chi Dong",
				"parent": r["name"],
				"parenttype": DT,
				"parentfield": "cac_khoan",
				"idx": 1,
				"noi_dung": r.get("ten_khoan_chi") or "Khoản chi",
				"so_tien": flt(r.get("so_tien")),
				"phan_loai": r.get("phan_loai") or None,
				"loai_chung_tu": loai,
				"tk_chi_phi": r.get("tk_chi_phi") or None,
				"so_hoa_don": r.get("so_hoa_don") if co_vat else None,
				"ngay_hoa_don": r.get("ngay_hoa_don") if co_vat else None,
				"mst": r.get("mst") if co_vat else None,
				"ghi_chu": "Chuyển tự động từ phiếu một dòng ngày 20/08/2026.",
			})
			dong.flags.ignore_permissions = True
			dong.db_insert()
			frappe.db.set_value(
				DT, r["name"], "tong_tien", flt(r.get("so_tien")), update_modified=False
			)
			chuyen += 1
		except Exception:
			frappe.log_error(
				frappe.get_traceback(), "de_nghi_chi: chuyen phieu %s loi" % r["name"]
			)
	if chuyen:
		frappe.db.commit()
	return {"chuyen": chuyen, "bo_qua": bo_qua}


# ================================ đối soát ngân hàng cho phiếu TTNB
#
# Anh Việt 20/08/2026: *"Khi phiếu đã được duyệt và kế toán đi tiền từ ngân
# hàng OCB, em hãy nối logic Webhook SePay (tương tự luồng hoàn tiền MB) vào
# phiếu TTNB này. Khi dòng tiền ra khớp, hệ thống tự động đổi trạng thái
# phiếu thành 'Đã chi'."*
#
# Cùng một cơ chế với luồng hoàn tiền, và cố ý dùng lại đúng bài học của nó:
# một dòng tiền ra chỉ khớp cho MỘT phiếu (xem v238), và tiền đã ra là SỰ
# THẬT nên ghi xuống ngay chứ không gộp vào một giao dịch cơ sở dữ liệu với
# việc khác (xem v234).

BT = "Bank Transaction"


def noi_dung_ck(ma_phieu):
	"""Nội dung chuyển khoản cho một phiếu. THUẦN.

	Chính chuỗi này là thứ duy nhất phép đối soát bám vào, nên nó phải chứa
	nguyên mã phiếu và không được có dấu tiếng Việt: nhiều ngân hàng bỏ dấu
	hoặc cắt bớt nội dung, và một mã bị cắt là một phiếu không bao giờ tự
	khớp được.
	"""
	return ("THE VAGABOND %s" % (ma_phieu or "")).strip()


def khop_noi_dung(mo_ta, ma_phieu):
	"""Nội dung chuyển khoản này có mang mã phiếu kia không. THUẦN.

	Bỏ mọi ký tự không phải chữ và số ở cả hai bên rồi mới so. Ngân hàng hay
	thay dấu gạch ngang bằng dấu cách, hoặc bỏ hẳn, nên "TTNB-26-08-00001"
	và "TTNB 26 08 00001" phải là một.
	"""
	sach = lambda x: "".join(ch for ch in str(x or "").upper() if ch.isalnum())
	m = sach(ma_phieu)
	return bool(m) and m in sach(mo_ta)


def _gd_da_chiem_ttnb(tru_phieu=None):
	"""Giao dịch nào đã được một phiếu TTNB khác chiếm.

	Bài học v238 của luồng hoàn tiền, mang nguyên sang đây: một dòng tiền ra
	trên sao kê là MỘT lần tiền rời khỏi tài khoản. Cho hai phiếu cùng trỏ
	vào nó là ghi nhận hai lần chi cho một lần chuyển.
	"""
	loc = {"trang_thai": ["!=", TT_TRA_LAI], "ma_gd": ["!=", ""]}
	if tru_phieu:
		loc["name"] = ["!=", tru_phieu]
	ra = {}
	for r in frappe.get_all(DT, filters=loc, fields=["name", "ma_gd"], limit_page_length=0):
		ma = (r.get("ma_gd") or "").strip()
		if ma:
			ra.setdefault(ma, r["name"])
	return ra


def _phieu_cho_chi():
	"""Các phiếu đã duyệt xong, đang chờ tiền ra.

	CHỈ những phiếu đã qua hết chuỗi duyệt. Phiếu còn ở Nháp hoặc còn chờ
	duyệt mà tự nhảy sang Đã chi vì ngân hàng tình cờ có một khoản trùng nội
	dung là chuyện không được phép xảy ra.
	"""
	return frappe.get_all(
		DT,
		filters={"trang_thai": ["in", [TT_CHO_KE_TOAN, TT_HOAN_TAT]]},
		fields=["name", "tong_tien", "so_tien", "trang_thai"],
		limit_page_length=0,
	)


@frappe.whitelist()
def doi_soat(so_ngay=30):
	"""Tìm dòng tiền RA trên sao kê khớp với phiếu TTNB đang chờ chi.

	Chạy được bằng tay từ màn Danh sách, và chạy theo giờ qua
	`doi_soat_tu_dong`.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ds = _phieu_cho_chi()
	if not ds:
		return {"da_khop": 0, "xem_xet": [], "ghi_chu": "Không có phiếu nào đang chờ chi."}

	try:
		gds = frappe.db.sql(
			"""select name, description, withdrawal, date, reference_number
			from `tabBank Transaction`
			where docstatus < 2 and ifnull(withdrawal, 0) > 0
			  and date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)""",
			(cint(so_ngay) or 30,),
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "de_nghi_chi: doc sao ke loi")
		return {"da_khop": 0, "xem_xet": [], "ghi_chu": "Chưa đọc được sao kê ngân hàng."}

	da_chiem = _gd_da_chiem_ttnb()
	da, xem = 0, []
	for d in ds:
		tien = flt(d.get("tong_tien")) or flt(d.get("so_tien"))
		for g in gds:
			mo_ta = "%s %s" % (g.get("description") or "", g.get("reference_number") or "")
			if not khop_noi_dung(mo_ta, d["name"]):
				continue
			chu_cu = da_chiem.get(g["name"])
			if chu_cu and chu_cu != d["name"]:
				xem.append({
					"phieu": d["name"], "giao_dich": g["name"],
					"trung_voi": chu_cu, "tien_phieu": tien,
					"tien_chuyen": flt(g["withdrawal"]),
				})
				continue
			# Khớp nội dung rồi vẫn phải so TIỀN. Nội dung đúng mà số tiền
			# lệch nghĩa là kế toán chuyển thiếu hoặc thừa, và đó là việc
			# người phải xem chứ không phải máy tự đánh dấu xong.
			if abs(flt(g["withdrawal"]) - tien) > 1:
				xem.append({
					"phieu": d["name"], "giao_dich": g["name"],
					"tien_phieu": tien, "tien_chuyen": flt(g["withdrawal"]),
				})
				continue
			da_chiem[g["name"]] = d["name"]
			frappe.db.set_value(DT, d["name"], {
				"trang_thai": TT_DA_CHI,
				"ma_gd": g["name"],
				"ngay_da_chi": now_datetime(),
			})
			# Ghi xuống NGAY. Tiền đã ra là sự thật, không được để chung một
			# giao dịch cơ sở dữ liệu với bất kỳ việc nào có thể hỏng.
			frappe.db.commit()
			da += 1
			break
	return {
		"da_khop": da, "xem_xet": xem, "so_phieu_quet": len(ds),
		"ghi_chu": "" if da or xem else "Chưa có dòng tiền ra nào khớp phiếu đang chờ chi.",
	}


def doi_soat_tu_dong():
	"""Chạy theo giờ. Tự thoát nếu không có phiếu nào chờ."""
	try:
		frappe.set_user("Administrator")
		doi_soat()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "de_nghi_chi: doi soat tu dong loi")


def khi_co_giao_dich(ma_bt):
	"""Gọi ngay sau khi webhook SePay ghi một dòng sao kê mới.

	Nhờ vậy phiếu chuyển sang Đã chi trong vài giây thay vì chờ tới nhịp
	chạy theo giờ. Hàm này KHÔNG BAO GIỜ được nem lỗi ra ngoài: webhook đã
	ghi xong dòng tiền rồi, làm hỏng phản hồi trả về cho SePay là khiến họ
	gửi lại mãi.
	"""
	try:
		g = frappe.db.get_value(
			BT, ma_bt, ["name", "withdrawal", "description", "reference_number"], as_dict=True
		)
		if not g or flt(g.get("withdrawal")) <= 0:
			return
		mo_ta = "%s %s" % (g.get("description") or "", g.get("reference_number") or "")
		da_chiem = _gd_da_chiem_ttnb()
		if da_chiem.get(g["name"]):
			return
		for d in _phieu_cho_chi():
			if not khop_noi_dung(mo_ta, d["name"]):
				continue
			tien = flt(d.get("tong_tien")) or flt(d.get("so_tien"))
			if abs(flt(g["withdrawal"]) - tien) > 1:
				return
			frappe.db.set_value(DT, d["name"], {
				"trang_thai": TT_DA_CHI,
				"ma_gd": g["name"],
				"ngay_da_chi": now_datetime(),
			})
			frappe.db.commit()
			return
	except Exception:
		frappe.log_error(frappe.get_traceback(), "de_nghi_chi: khop ngay sau webhook loi")
