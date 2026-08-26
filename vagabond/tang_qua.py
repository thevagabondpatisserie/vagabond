# -*- coding: utf-8 -*-
"""Luồng Tặng quà khách VIP: thay bảng tính, không thay cách làm việc.

Anh Việt đặt bài 25/08/2026, dựa trên bảng tính thật của chị Loan Anh, năm
sheet, 347 dòng, bốn mùa quà: Tết Ất Tỵ 2025, Trung thu 2025, Giáng sinh
2025, Tết Bính Ngọ 2026 và Trung thu 2026.

Bốn điều bảng tính nói mà đề bài không nói, và cả bốn đều đổi thiết kế
--------------------------------------------------------------------------
1. "Khách của ai" và "Phụ trách" là HAI cột khác nhau. Cột đầu chỉ có ba
   giá trị (Chị Thảo, Anh Việt, Anh Felix), đó là người GIỮ QUAN HỆ. Cột sau
   chỉ có hai giá trị (Sales, Marketing), đó là bộ phận ĐI LÀM. Gộp một là
   mất hẳn một chiều thông tin, và lúc chia việc thì máy không biết bắn cho
   ai.

2. Hai trục trạng thái chạy độc lập thật. Dòng "Nam Le" có Đã liên hệ đồng
   thời Đã tặng. Dòng "Anh Quân" có Đã liên hệ, ghi chú "hẹn lại sau Tết",
   trạng thái tặng vẫn trống. Nên KHÔNG có luật "phải liên hệ xong mới được
   tặng".

3. Lời chúc có luật xưng hô theo phân loại. Ô NOTE trong sheet Tết Bính Ngọ
   ghi nguyên văn: "Nhóm nghệ sỹ cú pháp ghi thay chữ Anh/Chị bằng chữ Nghệ
   sỹ. Nhóm hoa hậu thay bằng Hoa Hậu/Á Hậu/Nam Vương. Các nhóm khác tuỳ
   theo title (Đạo diễn, Nhà Thiết Kế, Doanh nhân)". Nên biến trong mẫu
   không chỉ có tên khách.

4. Phân loại khách là danh mục SỐNG. "Cigar & Bar" mới xuất hiện ở mùa
   Trung thu 2026, tức là danh mục còn đẻ tiếp. Viết cứng vào một ô Select
   là mỗi mùa lại phải deploy một lần.

Vì sao ba tầng chứ không một doctype có bảng con
------------------------------------------------
Yêu cầu "chọn nhiều món quà trong cùng một lần tặng" đòi mỗi khách có bảng
quà riêng. Nếu danh sách khách cũng là bảng con của đợt thì thành bảng con
nằm trong bảng con, mà Frappe không cho. Cộng hai lý do nghiệp vụ:

  - ToDo của Frappe trỏ vào một chứng từ thật qua `reference_name`. Dòng
    bảng con không phải chứng từ nên không giao việc đích danh được, mà
    giao việc chính là yêu cầu của anh Việt.
  - Một dòng bảng tính là một việc có vòng đời riêng: liên hệ, hẹn giờ,
    giao, xác nhận. Đó là chứng từ chứ không phải một ô dữ liệu.

HAI Ô SỐ ĐIỆN THOẠI, KHÔNG PHẢI MỘT (anh Việt chốt 25/08/2026)
--------------------------------------------------------------
Đây là quyết định quan trọng nhất của cả tệp.

Trong bảng tính, ô số điện thoại lẫn lộn hai thứ khác hẳn nhau: số của
CHÍNH khách, và số của người nhận thay (trợ lý, quản gia, bảo vệ, lễ tân).
Xem "0972741266 - Na (Trợ Lý)" hay "093 2554338 (chị Linh quản gia)".

Gộp một ô thì hoặc là shipper không gọi được ai, hoặc là tin nhắn chúc mừng
bay vào máy trợ lý. Nên tách hẳn:

  `sdt_khach`  số của chính khách. Dùng để định danh, và là số DUY NHẤT
               được phép gửi tin Zalo.
  `sdt_nhan`   số người nhận thực tế. Shipper gọi số này. TUYỆT ĐỐI không
               gửi tin Zalo vào đây.

Cả hai đều đi qua `sdt_boc.boc()` chứ không gọi thẳng `lib.sdt()`. Lý do
đầy đủ nằm ở đầu tệp `vagabond/sdt_boc.py`.

Tin Zalo tặng quà: ĐANG TẮT
---------------------------
Anh Việt chốt 25/08/2026 tắt cho đợt đầu. Cổng đã dựng đủ ở đây nhưng
`_duoc_gui_zns` luôn trả về không cho tới khi bật cờ trong Vagabond
Settings. Lý do: mẫu ZNS phải được Zalo duyệt trước, và bộ tham số của mẫu
do người tạo mẫu đặt tên; gửi sai tên một tham số là Zalo từ chối cả tin.
Dùng `zalo.thu_mau()` đọc bộ tham số trước, hàm đó không tốn tin nào.
"""

import re

# ------------------------------------------------------------ phần thuần
#
# Đặt trên `import frappe` để bộ kiểm thử tầng khung chạy được ở CI mà
# không cần site. Ca kiểm ở khung/kiem_thu/thu_tang_qua.py.

DT = "Vagabond Tang Qua VIP"
DT_DOT = "Vagabond Dot Tang Qua"
DT_NHOM = "Vagabond Nhom Khach VIP"
DT_MAU = "Vagabond Mau Loi Chuc"

TT_TANG = ("Chua tang", "Dang xu ly", "Da tang")
TT_LIEN_HE = ("Chua lien he", "Da lien he")
BO_PHAN = ("Sales", "Marketing")

XUNG_HO_MD = "Anh/Chị"

# Bốn biến được dùng trong mẫu lời chúc. Không nhiều hơn.
#
# Giới hạn bốn là có chủ ý: mỗi biến thêm vào là một chỗ mẫu có thể vỡ khi
# dữ liệu thiếu, mà thiệp thì in ra giấy rồi gửi khách, không sửa lại được.
BIEN_MAU = ("xung_ho", "ten_khach", "don_vi", "nam")


def xung_ho_cua(title_rieng=None, xung_ho_nhom=None):
	"""Xưng hô dùng trong lời chúc. THUẦN.

	Ba nấc, theo đúng ghi chú của chị Loan Anh trong bảng tính: title riêng
	của từng người thắng, không có thì lấy theo nhóm, vẫn không có thì rơi
	về Anh/Chị.

	Rơi về Anh/Chị chứ KHÔNG để trống: một tấm thiệp in ra mà thiếu chữ xưng
	hô đọc lên thành hỗn, và không ai kiểm lại được sau khi đã gửi đi.
	"""
	for x in (title_rieng, xung_ho_nhom):
		x = str(x or "").strip()
		if x:
			return x
	return XUNG_HO_MD


def rap_loi_chuc(mau, xung_ho=None, ten_khach=None, don_vi=None, nam=None):
	"""Ráp mẫu lời chúc thành câu thật. THUẦN.

	Biến thiếu dữ liệu thì bỏ CẢ DÒNG chứa biến đó, không để lại chỗ trống.

	Vì sao bỏ cả dòng chứ không thay bằng chuỗi rỗng: mẫu Trung thu có dòng
	"Gửi tới {don_vi}", mà quá nửa số dòng trong bảng tính bỏ trống ô Đơn vị.
	Thay bằng rỗng thì in ra "Gửi tới ." trên thiệp gửi khách VIP.
	"""
	s = str(mau or "")
	if not s.strip():
		return ""
	gia_tri = {
		"xung_ho": str(xung_ho or "").strip(),
		"ten_khach": str(ten_khach or "").strip(),
		"don_vi": str(don_vi or "").strip(),
		"nam": str(nam or "").strip() if nam else "",
	}
	giu = []
	for dong in s.split("\n"):
		thieu = [b for b in BIEN_MAU
			if ("{%s}" % b) in dong and not gia_tri.get(b)]
		if thieu:
			continue
		for b in BIEN_MAU:
			dong = dong.replace("{%s}" % b, gia_tri[b])
		giu.append(dong)
	# Gộp các dòng trống liên tiếp còn lại sau khi cắt, để thiệp không bị
	# một khoảng hở lớn giữa hai đoạn.
	ra = re.sub(r"\n{3,}", "\n\n", "\n".join(giu))
	return ra.strip()


def bien_con_thieu(mau):
	"""Biến lạ trong một mẫu. THUẦN. Rỗng nghĩa là mẫu dùng được.

	Chặn lúc soạn mẫu chứ không chặn lúc in: người soạn mẫu gõ {ten} thay
	vì {ten_khach} thì cả đợt quà in ra thiệp còn nguyên dấu ngoặc nhọn.
	"""
	co = set(re.findall(r"\{([a-z_]+)\}", str(mau or "")))
	return sorted(co - set(BIEN_MAU))


def duoc_gui_zns(p, bat_zns=0):
	"""Phiếu này có được gửi tin Zalo không. THUẦN. Trả về (được, vì sao không).

	Năm cửa, đủ cả năm mới cho gửi. Mỗi cửa là một lần đã suýt gửi nhầm.

	Cửa quan trọng nhất là cửa `chinh_chu`: số bóc ra có thể hoàn toàn đúng
	mà vẫn là số của trợ lý. Xem sdt_boc.py.
	"""
	if not bat_zns:
		return 0, "tin nhắn tặng quà đang tắt theo cấu hình"
	if p.get("huy"):
		return 0, "phiếu đã huỷ"
	if not (p.get("sdt_khach") or "").strip():
		return 0, "chưa đọc ra số điện thoại của chính khách"
	if (p.get("sdt_khach_loai") or "") != "di_dong":
		return 0, "số bàn không nhận được tin Zalo"
	if not p.get("chinh_chu"):
		return 0, "số này không phải số chính chủ của khách"
	if p.get("zns_da_gui"):
		return 0, "phiếu này đã gửi tin rồi"
	return 1, ""


def cau_chan_zns(vi_sao):
	"""Câu hiện dưới nút gửi tin khi cổng đóng. THUẦN. Theo QT-24."""
	if not vi_sao:
		return ""
	them = {
		"chưa đọc ra số điện thoại của chính khách":
			" Nhờ anh chị điền ô SĐT khách VIP rồi lưu lại.",
		"số bàn không nhận được tin Zalo":
			" Nhờ anh chị xin thêm số di động của khách.",
		"số này không phải số chính chủ của khách":
			" Nhờ anh chị gọi tay, hoặc điền số riêng của khách vào ô SĐT khách VIP.",
		"phiếu này đã gửi tin rồi":
			" Muốn gửi lại thì nhờ quản lý mở khoá.",
	}.get(vi_sao, "")
	return "Chưa gửi tin được: %s.%s" % (vi_sao, them)


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, flt, now_datetime, nowdate

from vagabond import sdt_boc

# Ai được vào phân hệ CRM. Anh Việt chốt 25/08/2026: Marketing và Sales
# Manager giữ quyền sửa, Sales User lập và sửa phiếu của mình.
#
# Không tự chế danh sách vai riêng cho từng màn: bài học từ hop_qua.py ngày
# 21/08/2026, chị Loan Anh bị chặn ở màn Tuỳ biến hộp vì chỗ đó dựng một
# danh sách vai riêng và bỏ sót đúng vai chị ấy đang giữ.
QUYEN_CRM = {
	"System Manager",
	"Sales Manager",
	"Sales User",
	"Marketing",
}


def _kiem_quyen(viec="vào phân hệ CRM chăm sóc khách"):
	if not QUYEN_CRM & set(frappe.get_roles()):
		frappe.throw(
			"Tài khoản của bạn không có quyền %s. Phân hệ này mở cho Sales và "
			"Marketing. Cần dùng thì báo anh Việt cấp thêm chức vụ Marketing "
			"trong màn Quản lý người dùng." % viec
		)


def _bat_zns():
	"""Cờ bật tin Zalo tặng quà. MẶC ĐỊNH TẮT, anh Việt chốt 25/08/2026."""
	try:
		from vagabond.lib import cfg

		return cint((cfg() or {}).get("bat_zns_tang_qua") or 0)
	except Exception:
		return 0


# ------------------------------------------------------ bóc số vào phiếu


def _ap_boc_sdt(doc):
	"""Bóc hai ô số thô vào các ô đã sạch. Gọi từ validate.

	Chạy lại được không giới hạn lần: bóc lần thứ mười trên cùng một ô ra
	cùng kết quả, nên vá luật xong thì quét lại cả sổ được.
	"""
	khach = sdt_boc.boc(doc.get("sdt_khach_tho"))
	nhan = sdt_boc.boc(doc.get("sdt_nhan_tho"))

	doc.sdt_khach = khach["sdt"]
	doc.sdt_khach_loai = khach["loai"]
	doc.sdt_nhan = nhan["sdt"]
	doc.sdt_nhan_loai = nhan["loai"]
	# Người nghe máy đọc từ ô NGƯỜI NHẬN, vì đó mới là ô hay chứa tên trợ lý.
	doc.nguoi_nghe_may = nhan["nguoi_nghe"] or khach["nguoi_nghe"]

	# Chính chủ xét trên ô SĐT KHÁCH VIP, không xét ô người nhận.
	#
	# Ô người nhận vốn ĐƯỢC PHÉP là số trợ lý, đó là công dụng của nó. Xét
	# nhầm sang ô đó là mọi phiếu có trợ lý đều bị khoá gửi tin, kể cả khi
	# số riêng của khách đã điền đầy đủ ngay bên cạnh.
	doc.chinh_chu = 1 if (khach["sdt"] and khach["chinh_chu"]) else 0

	loi = []
	if khach["canh_bao"]:
		loi.append("SĐT khách VIP: %s" % khach["canh_bao"])
	if nhan["canh_bao"] and (doc.get("sdt_nhan_tho") or "").strip():
		loi.append("SĐT người nhận: %s" % nhan["canh_bao"])
	# Ô khách trống mà ô người nhận có số: nói thẳng ra, vì đây đúng là cái
	# bẫy mà hai ô sinh ra để tránh.
	if not khach["sdt"] and nhan["sdt"]:
		loi.append(
			"Mới có số người nhận thay, chưa có số riêng của khách. Shipper "
			"gọi được nhưng hệ thống sẽ không gửi tin nhắn nào."
		)
	doc.canh_bao_sdt = "\n".join(loi)


# ---------------------------------------------------------- ráp lời chúc


def _ap_loi_chuc(doc):
	"""Dựng lại ô lời chúc từ mẫu. Gọi từ validate."""
	if doc.get("sua_tay"):
		# Sales đã bẻ mẫu cho riêng dòng này. Vẫn dựng ô mẫu để còn đối
		# chiếu, nhưng cái in ra là ô gõ tay, xem `loi_chuc_in`.
		pass
	mau = ""
	if doc.get("mau_loi_chuc"):
		mau = frappe.db.get_value(DT_MAU, doc.mau_loi_chuc, "noi_dung") or ""
	elif doc.get("dot"):
		md = frappe.db.get_value(DT_DOT, doc.dot, "mau_loi_chuc_md")
		if md:
			doc.mau_loi_chuc = md
			mau = frappe.db.get_value(DT_MAU, md, "noi_dung") or ""
	if not mau:
		doc.loi_chuc = ""
		return

	xh_nhom = ""
	if doc.get("phan_loai"):
		xh_nhom = frappe.db.get_value(DT_NHOM, doc.phan_loai, "xung_ho") or ""
	nam = frappe.db.get_value(DT_DOT, doc.dot, "nam") if doc.get("dot") else ""
	doc.loi_chuc = rap_loi_chuc(
		mau,
		xung_ho=xung_ho_cua(doc.get("title_rieng"), xh_nhom),
		ten_khach=doc.get("ten_khach"),
		don_vi=doc.get("don_vi"),
		nam=nam,
	)


def loi_chuc_in(doc):
	"""Câu THẬT SỰ in lên thiệp. Ô gõ tay thắng ô dựng từ mẫu."""
	tay = (doc.get("loi_chuc_sua_tay") or "").strip()
	if doc.get("sua_tay") and tay:
		return tay
	return (doc.get("loi_chuc") or "").strip()


# -------------------------------------------------------------- hook doc


def truoc_khi_luu(doc, method=None):
	"""Hook validate của Vagabond Tang Qua VIP."""
	_ap_boc_sdt(doc)
	_ap_loi_chuc(doc)

	# Đóng dấu thời điểm liên hệ. Chỉ đóng khi trạng thái vừa đổi sang Đã
	# liên hệ, và KHÔNG bao giờ ghi đè dấu cũ: dấu đầu tiên mới trả lời được
	# câu "phiếu này nằm bao lâu mới có người gọi".
	if doc.get("tt_lien_he") == "Da lien he" and not doc.get("ngay_lien_he"):
		doc.ngay_lien_he = now_datetime()
	if doc.get("tt_tang") == "Da tang" and not doc.get("ngay_tang"):
		doc.ngay_tang = nowdate()

	# Huỷ mềm theo QT-20: giữ nguyên bản ghi, chỉ bật cờ. Nhưng bắt phải nói
	# lý do, không thì ba tháng sau không ai biết vì sao khách này bị bỏ.
	if cint(doc.get("huy")) and not (doc.get("ly_do_huy") or "").strip():
		frappe.throw(
			"Huỷ một phiếu tặng quà thì phải ghi lý do, để sau này còn tra "
			"lại vì sao khách này không được tặng. Nhờ anh chị điền ô Lý do huỷ."
		)


def _kiem_mau(doc, method=None):
	"""Hook validate của Vagabond Mau Loi Chuc. Chặn biến lạ ngay lúc soạn."""
	la = bien_con_thieu(doc.get("noi_dung"))
	if la:
		frappe.throw(
			"Mẫu có biến không dùng được: %s. Chỉ bốn biến sau chạy: "
			"{xung_ho}, {ten_khach}, {don_vi}, {nam}. Nhờ anh chị sửa lại "
			"rồi lưu." % ", ".join("{%s}" % x for x in la)
		)


# ------------------------------------------------------------ cửa cho app


@frappe.whitelist()
def ds_dot():
	"""Danh sách đợt tặng quà, kèm ba con số đếm lại từ phiếu con.

	Đếm lại chứ không cất sẵn trong bản ghi đợt, theo QT-19: máy chủ chốt
	số. Cất sẵn thì mỗi lần sửa một phiếu lại phải nhớ cộng trừ vào đợt, và
	quên một lần là con số sai vĩnh viễn mà không ai biết.
	"""
	_kiem_quyen()
	dot = frappe.get_all(
		DT_DOT,
		fields=["name", "ten_dot", "dip", "nam", "trang_thai_dot",
			"tu_ngay", "den_ngay", "ngan_sach"],
		order_by="trang_thai_dot asc, modified desc",
		limit_page_length=60,
	)
	if not dot:
		return {"ds": []}

	dem = {}
	for p in frappe.get_all(
		DT, filters={"dot": ["in", [d["name"] for d in dot]], "huy": 0},
		fields=["dot", "tt_tang", "tt_lien_he"], limit_page_length=0,
	):
		o = dem.setdefault(p["dot"], {"tong": 0, "da_tang": 0, "da_lh": 0})
		o["tong"] += 1
		if p["tt_tang"] == "Da tang":
			o["da_tang"] += 1
		if p["tt_lien_he"] == "Da lien he":
			o["da_lh"] += 1

	for d in dot:
		d.update(dem.get(d["name"], {"tong": 0, "da_tang": 0, "da_lh": 0}))
	return {"ds": dot}


@frappe.whitelist()
def danh_sach(dot=None, loc="", nhom="", tim=""):
	"""Phiếu tặng quà trong một đợt, đã lọc, kèm số đếm cho từng chip.

	Đếm chip TRƯỚC khi lọc, để con số trên chip là số thật của cả đợt chứ
	không phải số dòng đang hiện. Cùng cách màn Việc cần làm đang làm.
	"""
	_kiem_quyen()
	ma_dot = (dot or "").strip()
	if not ma_dot:
		frappe.throw("Chưa chọn đợt tặng quà. Nhờ anh chị mở lại từ màn danh sách đợt.")

	tat_ca = frappe.get_all(
		DT,
		filters={"dot": ma_dot},
		fields=["name", "ten_khach", "don_vi", "phan_loai", "title_rieng",
			"khach", "khach_cua", "bo_phan_lam", "nguoi_lam",
			"sdt_khach", "sdt_khach_loai", "sdt_nhan", "nguoi_nghe_may",
			"chinh_chu", "canh_bao_sdt", "dia_chi", "gio_giao",
			"ghi_chu_van_chuyen", "tt_tang", "tt_lien_he", "ngay_tang",
			"huy", "ghi_chu", "zns_da_gui"],
		order_by="modified desc",
		limit_page_length=0,
	)
	mon_theo_phieu = _mon_theo_phieu([x["name"] for x in tat_ca])
	for x in tat_ca:
		x["mon"] = mon_theo_phieu.get(x["name"], [])
		x["tom_mon"] = ", ".join(
			"%s x%d" % (m["ten_mon"] or m["mon"], m["so_luong"]) for m in x["mon"]
		)

	con = [x for x in tat_ca if not cint(x["huy"])]
	dem = {
		"tat_ca": len(con),
		"chua_lien_he": sum(1 for x in con if x["tt_lien_he"] != "Da lien he"),
		"chua_tang": sum(1 for x in con if x["tt_tang"] != "Da tang"),
		"da_tang": sum(1 for x in con if x["tt_tang"] == "Da tang"),
		"sdt_loi": sum(1 for x in con if x["canh_bao_sdt"]),
		"da_huy": sum(1 for x in tat_ca if cint(x["huy"])),
	}

	k = (loc or "").strip() or "tat_ca"
	hien = tat_ca if k == "da_huy" else con
	if k == "chua_lien_he":
		hien = [x for x in hien if x["tt_lien_he"] != "Da lien he"]
	elif k == "chua_tang":
		hien = [x for x in hien if x["tt_tang"] != "Da tang"]
	elif k == "da_tang":
		hien = [x for x in hien if x["tt_tang"] == "Da tang"]
	elif k == "sdt_loi":
		hien = [x for x in hien if x["canh_bao_sdt"]]
	elif k == "da_huy":
		hien = [x for x in hien if cint(x["huy"])]

	nh = (nhom or "").strip()
	if nh:
		hien = [x for x in hien if (x["phan_loai"] or "") == nh]

	t = (tim or "").strip().lower()
	if t:
		hien = [x for x in hien if t in (x["ten_khach"] or "").lower()
			or t in (x["don_vi"] or "").lower()
			or t in (x["sdt_khach"] or "")
			or t in (x["sdt_nhan"] or "")]

	# Việc chưa ai gọi lên đầu, rồi tới chưa tặng.
	hien.sort(key=lambda x: (
		0 if x["tt_lien_he"] != "Da lien he" else 1,
		0 if x["tt_tang"] != "Da tang" else 1,
		x["ten_khach"] or "",
	))

	dem_nhom = {}
	for x in con:
		if x["phan_loai"]:
			dem_nhom[x["phan_loai"]] = dem_nhom.get(x["phan_loai"], 0) + 1

	return {
		"ds": hien,
		"dem": dem,
		"loc": k,
		"nhom": nh,
		"tim": t,
		"chip_nhom": [{"k": a, "so": b} for a, b in
			sorted(dem_nhom.items(), key=lambda i: -i[1])],
		"dot": frappe.db.get_value(
			DT_DOT, ma_dot, ["name", "ten_dot", "trang_thai_dot"], as_dict=1),
	}


def _mon_theo_phieu(ma_phieu):
	"""Món quà của nhiều phiếu, MỘT truy vấn cho cả màn."""
	ra = {}
	if not ma_phieu:
		return ra
	for m in frappe.get_all(
		"Vagabond Tang Qua VIP Mon",
		filters={"parent": ["in", ma_phieu], "parenttype": DT},
		fields=["parent", "mon", "ten_mon", "so_luong", "ghi_chu_mon"],
		order_by="parent asc, idx asc",
		limit_page_length=0,
	):
		ra.setdefault(m["parent"], []).append(m)
	return ra


@frappe.whitelist()
def doi_trang_thai(ma, truc, gia_tri):
	"""Đổi MỘT trục trạng thái của MỘT phiếu, ngay trên danh sách.

	Vì sao có cửa riêng chứ không bắt mở form: người trực điện thoại gọi
	xong sáu mươi cuộc thì bấm sáu mươi lần. Bắt mở và đóng sáu mươi cái
	form là lý do người ta quay lại dùng Excel.

	Hai trục hoàn toàn độc lập, không trục nào kéo theo trục nào. Dữ liệu
	thật đã có dòng tặng rồi mà chưa từng liên hệ, và ngược lại.
	"""
	_kiem_quyen("sửa phiếu tặng quà")
	t, v = (truc or "").strip(), (gia_tri or "").strip()
	if t == "tang":
		if v not in TT_TANG:
			frappe.throw("Trạng thái tặng không hợp lệ: %s" % v)
		truong = "tt_tang"
	elif t == "lien_he":
		if v not in TT_LIEN_HE:
			frappe.throw("Trạng thái liên hệ không hợp lệ: %s" % v)
		truong = "tt_lien_he"
	else:
		frappe.throw("Chỉ đổi được trục tang hoặc lien_he.")

	doc = frappe.get_doc(DT, ma)
	if cint(doc.huy):
		frappe.throw(
			"Phiếu này đã huỷ nên không đổi trạng thái được. Nhờ anh chị bỏ "
			"dấu Đã huỷ trong phiếu trước, rồi bấm lại."
		)
	setattr(doc, truong, v)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ma": doc.name, "tt_tang": doc.tt_tang, "tt_lien_he": doc.tt_lien_he,
		"ngay_tang": str(doc.ngay_tang or "")[:10]}


@frappe.whitelist()
def xem_truoc_loi_chuc(mau=None, phan_loai=None, title_rieng=None,
		ten_khach=None, don_vi=None, nam=None):
	"""Ráp thử một lời chúc để màn hình hiện ra ngay lúc đang gõ.

	CHỈ ĐỌC, không ghi gì. Người nhập thấy ngay câu sẽ in lên thiệp, chứ
	không phải lưu xong rồi mới biết mẫu vỡ.
	"""
	_kiem_quyen()
	noi_dung = ""
	if mau:
		noi_dung = frappe.db.get_value(DT_MAU, mau, "noi_dung") or ""
	xh_nhom = ""
	if phan_loai:
		xh_nhom = frappe.db.get_value(DT_NHOM, phan_loai, "xung_ho") or ""
	return {
		"loi_chuc": rap_loi_chuc(
			noi_dung,
			xung_ho=xung_ho_cua(title_rieng, xh_nhom),
			ten_khach=ten_khach, don_vi=don_vi, nam=nam,
		),
		"xung_ho": xung_ho_cua(title_rieng, xh_nhom),
	}


@frappe.whitelist()
def thu_boc_sdt(tho=None):
	"""Bóc thử một ô số điện thoại để màn hình hiện kết quả ngay lúc gõ.

	CHỈ ĐỌC, thuần tính toán, không chạm cơ sở dữ liệu. Đây là khung xanh
	dưới ô số trên app: người nhập THẤY NGAY máy đọc ra số gì và ai nghe
	máy, chứ không phải lưu xong rồi mới biết máy hiểu sai.
	"""
	_kiem_quyen()
	return sdt_boc.boc(tho)


@frappe.whitelist()
def danh_muc():
	"""Nhóm khách, mẫu lời chúc và người phụ trách, cho các ô chọn trên app.

	Trả về ĐỦ để màn hình dựng ô chọn mà không phải gọi thêm lần nào. Theo
	QT-31, mọi ô ở đây đều là ô chọn trỏ vào danh mục thật, không ô gõ.
	"""
	_kiem_quyen()
	return {
		"nhom": frappe.get_all(
			DT_NHOM, filters={"con_dung": 1},
			fields=["name", "xung_ho", "xung_ho_phu"],
			order_by="uu_tien asc, name asc", limit_page_length=0),
		"mau": frappe.get_all(
			DT_MAU, filters={"con_dung": 1},
			fields=["name", "ten_mau", "dip"],
			order_by="dip asc, name asc", limit_page_length=0),
		"bo_phan": list(BO_PHAN),
		"tt_tang": list(TT_TANG),
		"tt_lien_he": list(TT_LIEN_HE),
		"bat_zns": _bat_zns(),
	}


@frappe.whitelist()
def chi_tiet(ma):
	"""Một phiếu đầy đủ, kèm câu chặn gửi tin đã dịch sẵn cho màn hình."""
	_kiem_quyen()
	doc = frappe.get_doc(DT, ma)
	d = doc.as_dict()
	duoc, vi_sao = duoc_gui_zns(d, _bat_zns())
	d["zns_duoc_gui"] = duoc
	d["zns_vi_sao"] = cau_chan_zns(vi_sao)
	d["loi_chuc_in"] = loi_chuc_in(d)
	return d


# --------------------------------------------- KHÔNG CÒN NHỊP QUÉT ĐÊM
#
# Trước 26/08/2026 chỗ này có `quet_dem` và `quet_dem_tu_dong`: mỗi sáng 6
# giờ rà phiếu chưa liên hệ rồi nhắc người phụ trách, kèm hai trần an toàn
# 200 và 3000.
#
# Anh Việt chốt 26/08/2026 GỠ HẲN, cùng lần tắt giao việc tự động. Lý do:
# nhịp đó nhắc bằng cách gọi `giao_viec.giao`, tức là nó cũng đẻ ra phân
# công cho cả bộ phận chứ không chỉ bắn một cái chuông. Mà ba vai được coi
# là Sales gồm Sales User, Sales Manager và Bộ phận đặt hàng thì phủ rộng
# tới cả kế toán, nên sáng nào cũng có người nhận việc không phải của mình.
#
# Hai trần an toàn cũng đi theo, và không tiếc: chúng chỉ tồn tại để đỡ cho
# chính nhịp này.
#
# Muốn biết phiếu nào chưa ai gọi thì mở màn Tặng quà khách VIP, bấm chip
# "Chưa liên hệ". Con số ở đó máy chủ đếm lại mỗi lần mở, luôn đúng, và
# không làm phiền ai.
#
# ĐỪNG dựng lại nhịp này rồi mới hỏi. Nếu sau này thật sự cần nhắc, thì
# nhắc ĐÍCH DANH người trong ô Người làm, và chỉ bắn thông báo chứ không
# giao việc.


# Trường mà màn hình ĐƯỢC PHÉP ghi. Danh sách trắng, không phải danh sách đen.
#
# Vì sao trắng chứ không đen: các ô `sdt_khach`, `chinh_chu`, `loi_chuc`,
# `zns_da_gui` đều do máy chủ tự tính. Nhận bừa cả gói người ta gửi lên là
# mở đúng cái cửa cho một màn hình sửa tay đặt cờ chính chủ bằng 1 rồi bắn
# tin vào máy trợ lý. Thêm một ô mới thì thêm tên vào đây, quên thì ô đó
# lặng lẽ không lưu chứ không lặng lẽ ghi sai.
TRUONG_MAN_GHI = (
	"dot", "khach", "ten_khach", "phan_loai", "title_rieng", "don_vi",
	"khach_cua", "bo_phan_lam", "nguoi_lam",
	"sdt_khach_tho", "sdt_nhan_tho",
	"dia_chi", "gio_giao", "ghi_chu_van_chuyen",
	"mau_loi_chuc", "sua_tay", "loi_chuc_sua_tay",
	"tt_tang", "ngay_tang", "tt_lien_he",
	"huy", "ly_do_huy", "ghi_chu",
)


@frappe.whitelist()
def luu(ma=None, du_lieu=None):
	"""Lưu một phiếu tặng quà từ app. Máy chủ chốt, màn hình chỉ gửi chữ.

	Không cho app gọi thẳng `frappe.client.insert`: bóc lại số điện thoại,
	ráp lại lời chúc và chặn quyền đều phải chạy ở đây. Đi đường chung thì
	ba việc đó vẫn chạy (chúng nằm trong validate), nhưng app sẽ ghi được
	cả những ô máy chủ tự tính, và đó là cửa mở cho sai số lặng lẽ.
	"""
	import json

	_kiem_quyen("lập hoặc sửa phiếu tặng quà")
	d = du_lieu
	if isinstance(d, str):
		d = json.loads(d or "{}")
	d = d or {}

	doc = frappe.get_doc(DT, ma) if ma else frappe.new_doc(DT)
	for truong in TRUONG_MAN_GHI:
		if truong in d:
			setattr(doc, truong, d.get(truong))

	if "mon" in d:
		doc.set("mon", [])
		for m in (d.get("mon") or []):
			if not (m or {}).get("mon"):
				continue
			doc.append("mon", {
				"mon": m["mon"],
				"so_luong": cint(m.get("so_luong")) or 1,
				"ghi_chu_mon": m.get("ghi_chu_mon") or "",
			})

	if not (doc.get("mon") or []):
		frappe.throw(
			"Phiếu tặng quà nào cũng phải có ít nhất một món. Nhờ anh chị "
			"bấm Thêm món rồi lưu lại."
		)

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ma": doc.name, "ten_khach": doc.ten_khach}


# ------------------------------------------------------- nạp danh mục lần đầu
#
# Phân loại khách là ô BẮT BUỘC trên phiếu. Danh mục rỗng thì Sales mở form
# ra không lưu được một dòng nào, tức là tính năng deploy xong vẫn không
# dùng được. Nên nạp sẵn đúng những nhóm ĐÃ CÓ THẬT trong bảng tính.
#
# Xưng hô lấy nguyên văn ghi chú của chị Loan Anh: "Nhóm nghệ sỹ cú pháp ghi
# thay chữ Anh/Chị bằng chữ Nghệ sỹ. Nhóm hoa hậu thay bằng Hoa Hậu/Á Hậu/
# Nam Vương. Các nhóm khác tuỳ theo title."
#
#   (tên nhóm, xưng hô, xưng hô phụ, thứ tự)
NHOM_NAP_SAN = (
	("Nghệ sĩ", "Nghệ sỹ", "", 10),
	("Nhóm Hoa Hậu", "Hoa Hậu", "Á Hậu/Nam Vương", 20),
	("Influencer", "Anh/Chị", "", 30),
	("Nhóm Kinh Doanh", "Anh/Chị", "Doanh nhân", 40),
	("Cigar & Bar", "Anh/Chị", "", 50),
	("Khách sỉ", "Anh/Chị", "", 60),
	("Khách VIP mua nhiều", "Anh/Chị", "", 70),
	("Báo chí - Tạp chí", "Anh/Chị", "", 80),
)

# Mẫu Tết chép NGUYÊN VĂN từ ô merge trong sheet Tết Bính Ngọ 2026.
MAU_NAP_SAN = (
	{
		"ma_mau": "LC-TET-CHUAN", "ten_mau": "Tết - mẫu chuẩn", "dip": "Tet",
		"noi_dung": (
			"CUNG CHÚC TÂN XUÂN\n\n"
			"Mến gửi {xung_ho} {ten_khach},\n\n"
			"Chút phong vị ngọt lành cho ngày khởi xuân {nam}.\n"
			"Cầu chúc {xung_ho} cùng gia đình một năm mới "
			"An Nhiên - Tự Tại - Cát Tường.\n"
			"Mong những khoảnh khắc sum vầy thêm phần thi vị!\n\n"
			"Tâm ý,\nThe Vagabond Patisserie"
		),
	},
	{
		"ma_mau": "LC-TRUNGTHU-CHUAN", "ten_mau": "Trung thu - mẫu chuẩn",
		"dip": "Trung thu",
		"noi_dung": (
			"The Vagabond kính chúc {xung_ho} {ten_khach} và gia đình một mùa "
			"trăng đoàn viên thật an lành, và gởi lời tri ân {xung_ho} đã luôn "
			"ủng hộ tiệm bánh.\n\n"
			"Từ đội ngũ của The Vagabond."
		),
	},
	{
		"ma_mau": "LC-GIANGSINH-CHUAN", "ten_mau": "Giáng sinh - mẫu chuẩn",
		"dip": "Giang sinh",
		"noi_dung": (
			"Wishing you a Christmas season overflowing with Love and Laughter\n"
			"- from The Vagabond with love -"
		),
	},
)


def nap_danh_muc():
	"""Nạp danh mục lần đầu. Gọi từ after_migrate. LẶP LẠI ĐƯỢC.

	CHỈ THÊM, không bao giờ sửa và không bao giờ xoá. Marketing đổi xưng hô
	của một nhóm trên app rồi mà lần deploy sau máy ghi đè lại thì đó là
	một tấm thiệp in sai gửi khách VIP, và không ai hiểu vì sao nó quay về
	giá trị cũ.
	"""
	them = {"nhom": 0, "mau": 0}
	for ten, xh, xh_phu, uu_tien in NHOM_NAP_SAN:
		if frappe.db.exists(DT_NHOM, ten):
			continue
		try:
			d = frappe.get_doc({
				"doctype": DT_NHOM, "ten_nhom": ten, "xung_ho": xh,
				"xung_ho_phu": xh_phu, "uu_tien": uu_tien, "con_dung": 1,
			})
			d.flags.ignore_permissions = True
			d.insert(ignore_permissions=True)
			them["nhom"] += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(),
				"tang_qua: nap nhom %s loi" % ten)

	for m in MAU_NAP_SAN:
		if frappe.db.exists(DT_MAU, m["ma_mau"]):
			continue
		try:
			d = frappe.get_doc(dict(doctype=DT_MAU, con_dung=1, **m))
			d.flags.ignore_permissions = True
			d.insert(ignore_permissions=True)
			them["mau"] += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(),
				"tang_qua: nap mau %s loi" % m["ma_mau"])
	return them


# =========================================================================
# Nhân bản đợt và thêm khách hàng loạt (anh Việt đặt bài 26/08/2026)
# =========================================================================


def ma_dot_moi(ma_cu, nam_moi):
	"""Sinh mã đợt cho mùa sau từ mã đợt cũ. THUẦN.

	Mã đợt trong hệ có dạng "TET-2026" hay "TRUNGTHU-2025". Đổi đúng cụm số
	năm ở CUỐI mã, không đụng tới phần chữ. Mã không có đuôi năm thì nối
	thêm năm vào, chứ không đoán bừa.
	"""
	goc = str(ma_cu or "").strip()
	nam = str(nam_moi or "").strip()
	if not goc:
		return nam
	if not nam:
		return goc
	phan = goc.rsplit("-", 1)
	if len(phan) == 2 and phan[1].isdigit() and len(phan[1]) == 4:
		return phan[0] + "-" + nam
	return goc + "-" + nam


def ten_dot_moi(ten_cu, nam_cu, nam_moi):
	"""Tên đợt cho mùa sau. THUẦN. Thay số năm cũ trong tên nếu có."""
	ten = str(ten_cu or "").strip()
	nam_cu = str(nam_cu or "").strip()
	nam_moi = str(nam_moi or "").strip()
	if ten and nam_cu and nam_moi and nam_cu in ten:
		return ten.replace(nam_cu, nam_moi)
	if ten and nam_moi:
		return "%s (%s)" % (ten, nam_moi)
	return ten


# Những ô KHÔNG được chép sang đợt mới. Chép sang là mùa mới mở ra đã thấy
# khách nào cũng "Đã tặng", và không ai biết con số đó là của năm nào.
O_KHONG_CHEP = (
	"tt_tang", "ngay_tang", "tt_lien_he", "ngay_lien_he",
	"huy", "ly_do_huy", "hoa_don",
	"zns_da_gui", "zns_ma_theo_doi", "nguoi_gui_zns",
	"loi_chuc",
)

# Những ô CÓ chép. Liệt kê thẳng chứ không chép cả bản ghi: chép cả bản ghi
# là một ngày nào đó phiên khác thêm một ô trạng thái mới và nó lặng lẽ
# theo sang mùa sau.
O_CHEP = (
	"khach", "ten_khach", "phan_loai", "title_rieng", "don_vi", "hang_khach",
	"khach_cua", "bo_phan_lam", "nguoi_lam",
	"sdt_khach_tho", "sdt_nhan_tho",
	"dia_chi", "gio_giao", "ghi_chu_van_chuyen",
	"ghi_chu",
)


@frappe.whitelist()
def nhan_ban_dot(ma_dot=None, nam_moi=None, ten_moi=None, chep_qua=0):
	"""Nhân bản một đợt tặng quà sang mùa sau, kèm cả danh sách khách.

	Nút Duplicate mặc định của Frappe chỉ chép được BẢN GHI ĐỢT, vì danh
	sách khách ở đây là chứng từ riêng chứ không phải bảng con (lý do nằm ở
	đầu tệp này). Nên phải có hàm riêng, không thì mùa nào cũng gõ lại 347
	dòng.

	Mặc định KHÔNG chép món quà: quà Trung thu khác quà Tết, chép sang là
	Marketing phải xoá từng dòng. Muốn chép thì truyền `chep_qua=1`.
	"""
	_kiem_quyen("nhân bản đợt tặng quà")
	ma_dot = (ma_dot or "").strip()
	if not ma_dot or not frappe.db.exists(DT_DOT, ma_dot):
		frappe.throw("Không tìm thấy đợt tặng quà %s." % (ma_dot or ""))

	cu = frappe.get_doc(DT_DOT, ma_dot)
	nam = cint(nam_moi) or (cint(cu.get("nam")) + 1)
	ma_moi = ma_dot_moi(ma_dot, nam)
	if frappe.db.exists(DT_DOT, ma_moi):
		frappe.throw(
			"Đã có đợt mang mã %s rồi. Mở đợt đó ra dùng tiếp, hoặc đặt năm "
			"khác." % ma_moi
		)

	moi = frappe.new_doc(DT_DOT)
	moi.ma_dot = ma_moi
	moi.ten_dot = (ten_moi or "").strip() or ten_dot_moi(
		cu.get("ten_dot"), cu.get("nam"), nam)
	moi.dip = cu.get("dip")
	moi.nam = nam
	# Mở ra ở dạng Nhập, KHÔNG phải Đang chạy. Đợt Đang chạy là đợt được
	# phép xuất hoá đơn quà, mà đợt vừa nhân bản thì chưa ai soát dòng nào.
	moi.trang_thai_dot = "Nhap"
	moi.mau_loi_chuc_md = cu.get("mau_loi_chuc_md")
	moi.ngan_sach = cu.get("ngan_sach")
	moi.ghi_chu = "Nhân bản từ đợt %s." % ma_dot
	moi.nguoi_tao = frappe.session.user
	moi.flags.ignore_permissions = True
	moi.insert(ignore_permissions=True)

	ds = frappe.get_all(
		DT, filters={"dot": ma_dot}, fields=["name"],
		order_by="creation asc", limit_page_length=0,
	)
	so_chep = 0
	for r in ds:
		try:
			p = frappe.get_doc(DT, r["name"])
			if cint(p.get("huy")):
				continue
			n = frappe.new_doc(DT)
			n.dot = ma_moi
			for o in O_CHEP:
				n.set(o, p.get(o))
			n.tt_tang = TT_TANG[0]
			n.tt_lien_he = TT_LIEN_HE[0]
			n.mau_loi_chuc = cu.get("mau_loi_chuc_md") or p.get("mau_loi_chuc")
			if cint(chep_qua):
				for m in (p.get("mon") or []):
					n.append("mon", {
						"mon": m.get("mon"),
						"so_luong": cint(m.get("so_luong")) or 1,
						"ghi_chu_mon": m.get("ghi_chu_mon") or "",
					})
			n.flags.ignore_permissions = True
			n.insert(ignore_permissions=True)
			so_chep += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(),
				"tang_qua: nhan ban phieu %s" % r["name"])

	frappe.db.commit()
	return {
		"ok": 1,
		"ma": ma_moi,
		"so_chep": so_chep,
		"loi_nhan": (
			"Đã dựng đợt %s và chép sang %s khách. Đợt mới đang ở trạng thái "
			"Nhập, soát xong thì chuyển sang Đang chạy.%s"
			% (ma_moi, so_chep,
			   "" if cint(chep_qua) else " Món quà chưa chép, mỗi mùa một loại quà.")
		),
	}


@frappe.whitelist()
def khach_co_hang(tu_khoa="", hang="", dot="", so_dong=200):
	"""Khách CÓ HẠNG thành viên, để quản lý tick hàng loạt vào đợt.

	Anh Việt chốt 26/08/2026: danh mục khách thân thiết của tiệm chính là
	bảng hạng thành viên, không phải một nhóm khách riêng bên ERPNext.

	Đánh dấu sẵn người ĐÃ có trong đợt để màn hình không cho tick lại, chứ
	không lọc họ ra: người dùng cần thấy là họ đã có rồi.
	"""
	_kiem_quyen("chọn khách vào đợt tặng quà")
	loc = {"disabled": 0, "vgb_hang": ["is", "set"]}
	if (hang or "").strip():
		loc["vgb_hang"] = (hang or "").strip()
	tu = (tu_khoa or "").strip()
	ds = frappe.get_all(
		"Customer",
		filters=loc,
		or_filters=(
			{"name": ["like", "%" + tu + "%"], "customer_name": ["like", "%" + tu + "%"]}
			if tu else None
		),
		fields=["name", "customer_name", "customer_group", "vgb_hang"],
		order_by="customer_name asc",
		limit_page_length=cint(so_dong) or 200,
	)

	da_co = set()
	if (dot or "").strip():
		for r in frappe.get_all(
			DT, filters={"dot": (dot or "").strip()},
			fields=["khach"], limit_page_length=0,
		):
			if r.get("khach"):
				da_co.add(r["khach"])

	return {
		"ds": [{
			"ma": r["name"],
			"ten": r.get("customer_name") or r["name"],
			"nhom": r.get("customer_group") or "",
			"hang": r.get("vgb_hang") or "",
			"da_co": 1 if r["name"] in da_co else 0,
		} for r in ds],
		"hang": [h["name"] for h in frappe.get_all(
			"Vagabond Hang Khach", filters={"bat": 1},
			fields=["name"], limit_page_length=0)],
	}


@frappe.whitelist()
def them_hang_loat(dot=None, khach=None, mon=None, phan_loai=None,
		bo_phan_lam=None, khach_cua=None):
	"""Thêm nhiều khách vào một đợt trong một lần bấm.

	Bỏ qua người đã có trong đợt thay vì ném lỗi: quản lý tick lại một người
	đã có là chuyện thường, và ném lỗi giữa chừng thì nửa danh sách vào được
	nửa kia không, mà người bấm không biết nửa nào.
	"""
	import json as _json

	_kiem_quyen("thêm khách vào đợt tặng quà")
	ma_dot = (dot or "").strip()
	if not ma_dot or not frappe.db.exists(DT_DOT, ma_dot):
		frappe.throw("Không tìm thấy đợt tặng quà %s." % (ma_dot or ""))

	if isinstance(khach, str):
		khach = _json.loads(khach or "[]")
	khach = [str(k).strip() for k in (khach or []) if str(k or "").strip()]
	if not khach:
		frappe.throw("Chưa tick khách nào.")

	if isinstance(mon, str):
		mon = _json.loads(mon or "[]")
	mon = [m for m in (mon or []) if (m or {}).get("mon")]

	da_co = set()
	for r in frappe.get_all(DT, filters={"dot": ma_dot}, fields=["khach"],
			limit_page_length=0):
		if r.get("khach"):
			da_co.add(r["khach"])

	dot_doc = frappe.get_doc(DT_DOT, ma_dot)
	them, bo_qua, hong = 0, 0, []
	for k in khach:
		if k in da_co:
			bo_qua += 1
			continue
		try:
			kh = frappe.db.get_value(
				"Customer", k, ["customer_name", "vgb_hang"], as_dict=True) or {}
			n = frappe.new_doc(DT)
			n.dot = ma_dot
			n.khach = k
			n.ten_khach = kh.get("customer_name") or k
			n.hang_khach = kh.get("vgb_hang") or ""
			n.phan_loai = (phan_loai or "").strip() or None
			n.bo_phan_lam = (bo_phan_lam or "").strip() or None
			n.khach_cua = (khach_cua or "").strip() or None
			n.mau_loi_chuc = dot_doc.get("mau_loi_chuc_md")
			n.tt_tang = TT_TANG[0]
			n.tt_lien_he = TT_LIEN_HE[0]
			for m in mon:
				n.append("mon", {
					"mon": m["mon"],
					"so_luong": cint(m.get("so_luong")) or 1,
					"ghi_chu_mon": m.get("ghi_chu_mon") or "",
				})
			n.flags.ignore_permissions = True
			n.insert(ignore_permissions=True)
			them += 1
			da_co.add(k)
		except Exception as e:
			hong.append("%s: %s" % (k, str(e)[:120]))
			frappe.log_error(frappe.get_traceback(),
				"tang_qua: them hang loat %s" % k)

	frappe.db.commit()
	return {
		"ok": 1,
		"them": them,
		"bo_qua": bo_qua,
		"hong": hong,
		"loi_nhan": "Đã thêm %s khách vào đợt %s.%s%s" % (
			them, ma_dot,
			" Bỏ qua %s người đã có sẵn." % bo_qua if bo_qua else "",
			" %s dòng lỗi, xem nhật ký." % len(hong) if hong else "",
		),
	}


# =========================================================================
# Tự lập đợt và nhập danh sách NGAY TRÊN APP (anh Việt 26/08/2026)
#
# Trước bản này màn Đợt tặng quà rỗng thì chỉ có một câu "Mở Desk tạo một
# đợt". Desk là màn quản trị, Sales và Marketing không vào, mà cũng không
# nên vào. Nên mùa quà nào cũng phải nhờ người khác mở hộ một bản ghi rồi
# mới làm được việc của mình.
# =========================================================================

# Mã đợt sinh từ dịp, để mọi mùa cùng dịp xếp cạnh nhau trong danh sách.
TIEN_TO_DIP = {
	"Tet": "TET",
	"Trung thu": "TRUNGTHU",
	"Giang sinh": "GIANGSINH",
	"Sinh nhat": "SINHNHAT",
	"Tri an": "TRIAN",
	"Khac": "DOT",
}

DIP = tuple(TIEN_TO_DIP.keys())
TT_DOT = ("Nhap", "Dang chay", "Da dong")


def ma_dot_tu_dip(dip, nam):
	"""Mã đợt sinh từ dịp và năm. THUẦN.

	Sinh ở MỘT chỗ duy nhất, và cùng khuôn với `ma_dot_moi` dùng khi nhân
	bản. Hai chỗ tự ghép chuỗi thì sớm muộn một chỗ ghép khác, và nút nhân
	bản sẽ không nhận ra đuôi năm để thay.
	"""
	tien_to = TIEN_TO_DIP.get(str(dip or "").strip()) or TIEN_TO_DIP["Khac"]
	n = str(cint(nam) or "").strip()
	return (tien_to + "-" + n) if n else tien_to


def ten_dot_goi_y(dip, nam):
	"""Tên đợt gợi ý sẵn cho người lập, vẫn sửa được. THUẦN."""
	d = str(dip or "").strip()
	ten = {
		"Tet": "Tết", "Trung thu": "Trung thu", "Giang sinh": "Giáng sinh",
		"Sinh nhat": "Sinh nhật", "Tri an": "Tri ân",
	}.get(d, "Đợt tặng quà")
	n = cint(nam)
	return ("%s %s" % (ten, n)) if n else ten


@frappe.whitelist()
def luu_dot(ma=None, du_lieu=None):
	"""Lập hoặc sửa một đợt tặng quà từ app.

	Mã đợt do MÁY CHỦ sinh từ dịp và năm, app không gửi lên. Cho app tự đặt
	mã thì hai người mở hai đợt Trung thu 2026 với hai mã khác nhau, và từ
	đó trở đi không ai gộp lại được nữa.

	Sửa đợt thì KHÔNG đổi mã, dù người dùng có đổi dịp hay năm: mã là thứ 34
	phiếu con đang trỏ vào.
	"""
	import json as _json

	_kiem_quyen("lập hoặc sửa đợt tặng quà")
	d = du_lieu
	if isinstance(d, str):
		d = _json.loads(d or "{}")
	d = d or {}

	dip = str(d.get("dip") or "").strip()
	if dip and dip not in DIP:
		frappe.throw("Dịp %s không có trong danh mục." % dip)
	nam = cint(d.get("nam")) or cint(nowdate()[:4])
	tt = str(d.get("trang_thai_dot") or "").strip() or "Nhap"
	if tt not in TT_DOT:
		frappe.throw("Trạng thái đợt %s không hợp lệ." % tt)

	ma = (ma or "").strip()
	if ma:
		doc = frappe.get_doc(DT_DOT, ma)
	else:
		doc = frappe.new_doc(DT_DOT)
		doc.ma_dot = ma_dot_tu_dip(dip or "Khac", nam)
		if frappe.db.exists(DT_DOT, doc.ma_dot):
			frappe.throw(
				"Đã có đợt %s rồi. Mở đợt đó ra dùng tiếp, hoặc đổi năm."
				% doc.ma_dot
			)
		doc.nguoi_tao = frappe.session.user

	doc.ten_dot = str(d.get("ten_dot") or "").strip() or ten_dot_goi_y(dip, nam)
	doc.dip = dip or None
	doc.nam = nam
	doc.trang_thai_dot = tt
	doc.tu_ngay = d.get("tu_ngay") or None
	doc.den_ngay = d.get("den_ngay") or None
	doc.mau_loi_chuc_md = d.get("mau_loi_chuc_md") or None
	doc.ngan_sach = flt(d.get("ngan_sach"))
	doc.ghi_chu = str(d.get("ghi_chu") or "").strip()
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ma": doc.name, "ten_dot": doc.ten_dot,
		"trang_thai_dot": doc.trang_thai_dot}


@frappe.whitelist()
def danh_muc_dot():
	"""Danh mục cho form lập đợt: dịp, trạng thái, mẫu lời chúc."""
	_kiem_quyen()
	try:
		mau = frappe.get_all(
			DT_MAU, filters={"con_dung": 1},
			fields=["name", "ten_mau", "dip"],
			order_by="dip asc, name asc", limit_page_length=0)
	except Exception:
		mau = []
	return {
		"dip": [{"k": x, "ten": ten_dot_goi_y(x, 0)} for x in DIP],
		"trang_thai": [
			{"k": "Nhap", "ten": "Nháp, chưa cho xuất quà"},
			{"k": "Dang chay", "ten": "Đang chạy"},
			{"k": "Da dong", "ten": "Đã đóng"},
		],
		"mau": mau,
		"nam": cint(nowdate()[:4]),
	}


# ------------------------------------------------- nhập danh sách bằng cách dán
#
# Chị Loan Anh giữ danh sách trên bảng tính. Bắt gõ lại 34 dòng vào app là
# cách chắc chắn nhất để không ai dùng app. Nên mở đường dán thẳng.

# Thứ tự cột, chốt cứng và in ra ngay trên màn hình cho người dán nhìn thấy.
COT_DAN = ("ten_khach", "so_luong", "dia_chi", "sdt_nhan_tho",
	"ghi_chu_van_chuyen", "ghi_chu")

COT_DAN_NHAN = ("Tên khách", "Số lượng", "Địa chỉ",
	"SĐT hoặc người nhận", "Ghi chú giao hàng", "Ghi chú")


def tach_dan(van_ban):
	"""Tách chữ dán từ bảng tính thành từng dòng, từng ô. THUẦN.

	Nhận cả TAB lẫn dấu chấm phẩy làm dấu ngăn cột. KHÔNG nhận dấu phẩy:
	địa chỉ ở đây gần như dòng nào cũng có dấu phẩy, lấy phẩy làm dấu ngăn
	là vỡ hết địa chỉ mà người dán không hiểu vì sao.

	Bỏ dòng trống và bỏ dòng tiêu đề (dòng đầu có chữ "tên khách").
	"""
	ra = []
	for dong in str(van_ban or "").replace("\r\n", "\n").replace("\r", "\n").split("\n"):
		if not dong.strip():
			continue
		o = dong.split("\t") if "\t" in dong else dong.split(";")
		o = [x.strip() for x in o]
		if not any(o):
			continue
		if not ra and "tên khách" in o[0].lower().replace("  ", " "):
			continue
		ra.append(o)
	return ra


def doc_dong_dan(o):
	"""Một dòng đã tách thành tự điển đúng tên ô. THUẦN.

	Thiếu cột thì để trống chứ không nổ: người dán hay quét thiếu cột cuối,
	và bắt họ dán lại cả bảng vì thiếu ô Ghi chú là vô ích.
	"""
	d = {}
	for i, ten in enumerate(COT_DAN):
		d[ten] = (o[i] if i < len(o) else "").strip()
	sl = "".join(c for c in d.get("so_luong", "") if c.isdigit())
	d["so_luong"] = int(sl) if sl else 1
	return d


@frappe.whitelist()
def xem_truoc_dan(van_ban=None):
	"""CHỈ ĐỌC: dán vào trông sẽ ra những dòng nào.

	Bắt buộc xem trước rồi mới cho nạp. Dán nhầm cột là ba mươi tư cái tên
	khách nằm trong ô địa chỉ, mà lúc đó gỡ ra tốn hơn nhập tay từ đầu.
	"""
	_kiem_quyen("nhập danh sách tặng quà")
	dong = [doc_dong_dan(o) for o in tach_dan(van_ban)]
	return {
		"cot": list(COT_DAN_NHAN),
		"so_dong": len(dong),
		"tong_qua": sum(x["so_luong"] for x in dong),
		"thieu_ten": [i + 1 for i, x in enumerate(dong) if not x["ten_khach"]],
		"ds": dong[:200],
	}


@frappe.whitelist()
def nap_dan(dot=None, van_ban=None, mon=None, phan_loai=None,
		bo_phan_lam=None, khach_cua=None):
	"""Nạp danh sách đã dán vào một đợt.

	Bỏ qua dòng không có tên khách thay vì ném lỗi giữa chừng: ném giữa
	chừng thì nửa danh sách vào được nửa kia không, mà người bấm không biết
	nửa nào.
	"""
	import json as _json

	_kiem_quyen("nhập danh sách tặng quà")
	ma_dot = (dot or "").strip()
	if not ma_dot or not frappe.db.exists(DT_DOT, ma_dot):
		frappe.throw("Không tìm thấy đợt tặng quà %s." % (ma_dot or ""))

	dong = [doc_dong_dan(o) for o in tach_dan(van_ban)]
	if not dong:
		frappe.throw("Chưa dán dòng nào.")

	if isinstance(mon, str):
		mon = _json.loads(mon or "[]")
	mon = [m for m in (mon or []) if (m or {}).get("mon")]
	if not mon:
		frappe.throw(
			"Chưa chọn món quà. Mỗi phiếu tặng quà phải có ít nhất một món, "
			"nên nhập danh sách cũng phải chọn món chung trước."
		)

	dot_doc = frappe.get_doc(DT_DOT, ma_dot)
	them, bo_qua, hong = 0, 0, []
	for i, x in enumerate(dong):
		if not x["ten_khach"]:
			bo_qua += 1
			continue
		try:
			n = frappe.new_doc(DT)
			n.dot = ma_dot
			n.ten_khach = x["ten_khach"]
			n.phan_loai = (phan_loai or "").strip() or None
			n.bo_phan_lam = (bo_phan_lam or "").strip() or "Sales"
			n.khach_cua = (khach_cua or "").strip() or None
			n.dia_chi = x["dia_chi"]
			# Số dán vào là số SHIPPER GỌI, nên vào ô người nhận chứ không
			# vào ô số riêng của khách. Ô số riêng là ô duy nhất được phép
			# gửi tin Zalo, nhét nhầm vào đó là tin chúc bay vào máy trợ lý.
			n.sdt_nhan_tho = x["sdt_nhan_tho"]
			n.ghi_chu_van_chuyen = x["ghi_chu_van_chuyen"]
			n.ghi_chu = x["ghi_chu"]
			n.mau_loi_chuc = dot_doc.get("mau_loi_chuc_md")
			n.tt_tang = TT_TANG[0]
			n.tt_lien_he = TT_LIEN_HE[0]
			for m in mon:
				n.append("mon", {
					"mon": m["mon"],
					"so_luong": cint(x["so_luong"]) or cint(m.get("so_luong")) or 1,
					"ghi_chu_mon": m.get("ghi_chu_mon") or "",
				})
			n.flags.ignore_permissions = True
			n.insert(ignore_permissions=True)
			them += 1
		except Exception as e:
			hong.append("dòng %s (%s): %s" % (i + 1, x["ten_khach"], str(e)[:120]))
			frappe.log_error(frappe.get_traceback(),
				"tang_qua: nap dan dong %s" % (i + 1))

	frappe.db.commit()
	return {
		"ok": 1, "them": them, "bo_qua": bo_qua, "hong": hong,
		"loi_nhan": "Đã thêm %s khách vào đợt %s.%s%s" % (
			them, ma_dot,
			" Bỏ qua %s dòng không có tên khách." % bo_qua if bo_qua else "",
			" %s dòng lỗi." % len(hong) if hong else ""),
	}
