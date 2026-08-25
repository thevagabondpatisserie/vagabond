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


# ------------------------------------------------------ van an toàn quét đêm
#
# Anh Việt chốt 25/08/2026: trần mềm 200 bắn cảnh báo, trần cứng 3000 ngắt
# hẳn tác vụ.

# Trần cứng dùng chung hằng số của `diem_han` để chỉ có MỘT chỗ chỉnh.
#
# Với luồng này 3000 là trần chống thảm hoạ chứ không phải trần vận hành:
# cả tiệm tặng nhiều nhất chừng trăm hộp một mùa. Chạm tới ba nghìn nghĩa
# là bộ lọc đã hỏng chứ không phải tự nhiên đông khách.
from vagabond.diem_han import GIOI_HAN_MOT_DEM as TRAN_CUNG

# Trần mềm: vẫn chạy nhưng ghi nhật ký để có người nhìn sớm.
TRAN_MEM = 200

# Nhắc trước bao nhiêu ngày so với ngày kết thúc đợt.
NGAY_NHAC_TRUOC = 3


def _phieu_chua_lien_he():
	"""Phiếu chưa ai gọi, thuộc đợt ĐANG CHẠY, và ngày giao đã cận.

	Chỉ lấy đợt đang chạy. Đợt đã đóng mà còn hiện lên là mỗi mùa sau lại
	đội thêm một lớp việc chết không ai dọn.
	"""
	from frappe.utils import add_days

	dot = frappe.get_all(
		DT_DOT, filters={"trang_thai_dot": "Dang chay"},
		fields=["name", "den_ngay"], limit_page_length=0)
	moc = add_days(nowdate(), NGAY_NHAC_TRUOC)
	gan = [d["name"] for d in dot
		if not d["den_ngay"] or str(d["den_ngay"]) <= str(moc)]
	if not gan:
		return []
	return frappe.get_all(
		DT,
		filters={"dot": ["in", gan], "huy": 0, "tt_lien_he": "Chua lien he"},
		fields=["name", "dot", "ten_khach", "bo_phan_lam", "nguoi_lam",
			"khach_cua"],
		limit_page_length=0,
	)


def quet_dem(chay_that=0):
	"""Rà phiếu tặng quà chưa liên hệ rồi nhắc người phụ trách.

	MẶC ĐỊNH CHẠY THỬ. Phải truyền chay_that=1 mới thật sự nhắc.

	Cùng khuôn với `diem_han.het_han`, và cùng lý do: một đêm chạy nhầm thì
	không lùi lại được những cái chuông đã kêu trên điện thoại người thật.
	"""
	ds = _phieu_chua_lien_he()

	if len(ds) > TRAN_CUNG:
		# DỪNG LẠI, không chạy tiếp. Âm thầm chạy tiếp là ba nghìn cái chuông.
		frappe.log_error(
			message=(
				"Nhịp quét tặng quà đêm nay gặp %d phiếu chưa liên hệ, vượt "
				"trần cứng %d nên đã dừng, KHÔNG nhắc ai cả.\n\n"
				"Cả tiệm tặng nhiều nhất chừng trăm hộp một mùa, nên con số "
				"này gần như chắc chắn là bộ lọc hỏng hoặc một đợt cũ bị bật "
				"lại trạng thái Đang chạy. Nhờ anh chị kiểm màn Đợt tặng quà "
				"trước khi bật lại nhịp." % (len(ds), TRAN_CUNG)
			),
			title="tang_qua: quet dem vuot tran cung, da dung",
		)
		return {"dung": 1, "so_dong": len(ds), "vi_sao": "vượt trần cứng"}

	if len(ds) > TRAN_MEM:
		# Trần mềm: vẫn chạy, nhưng để lại vết cho người nhìn.
		frappe.log_error(
			message=(
				"Nhịp quét tặng quà đêm nay gặp %d phiếu chưa liên hệ, vượt "
				"trần mềm %d. Vẫn chạy, nhưng con số này cao hơn hẳn một mùa "
				"quà bình thường nên nhờ anh chị ngó qua." % (len(ds), TRAN_MEM)
			),
			title="tang_qua: quet dem vuot tran mem",
		)

	if not chay_that:
		return {"chay_thu": 1, "se_nhac": len(ds), "tran_mem": TRAN_MEM,
			"tran_cung": TRAN_CUNG}

	from vagabond import giao_viec

	nhac, da_co_roi = 0, 0
	for p in ds:
		try:
			nguoi, mo_ta = giao_viec._ai_phai_lam(frappe.get_doc(DT, p["name"]))
			if not nguoi:
				continue
			# MỘT PHIẾU MỘT ĐÊM MỘT LẦN NHẮC, và không nhắc lại đêm sau.
			#
			# `giao_viec.giao` bỏ qua người đã có việc mở nên KHÔNG đẻ thêm
			# ToDo, nhưng nó vẫn bắn chuông ở mọi lần gọi. Nhịp này chạy hằng
			# đêm, nên để nguyên là mỗi sáng Sales lại nhận đúng cái chuông của
			# hôm qua, và tới ngày thứ ba thì không ai đọc chuông nữa.
			#
			# Nên chỉ bắn chuông khi thật sự có người MỚI được giao. Việc vẫn
			# được gắn lại để ô Assigned To bên Desk không rơi.
			da_co = giao_viec._dang_giao(DT, p["name"])
			moi_that = [u for u in nguoi if u not in da_co]
			giao_viec.giao(DT, p["name"], nguoi, mo_ta, bao=1 if moi_that else 0)
			if moi_that:
				nhac += 1
			else:
				da_co_roi += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(),
				"tang_qua: nhac phieu %s loi" % p["name"])
	return {"da_nhac": nhac, "da_giao_tu_truoc": da_co_roi, "so_dong": len(ds)}


def quet_dem_tu_dong():
	"""Điểm gọi của bộ lập lịch. Chạy THẬT.

	Đặt 6 giờ sáng chứ không nửa đêm: đây là việc nhắc người đi làm, nhắc
	lúc 2 giờ sáng thì tới 8 giờ thông báo đã trôi mất trong danh sách.
	"""
	try:
		return quet_dem(chay_that=1)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tang_qua: quet dem tu dong loi")
		return {"loi": 1}


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
