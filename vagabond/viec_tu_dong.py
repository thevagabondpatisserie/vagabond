# -*- coding: utf-8 -*-
"""v646: Cài đặt tự động hoá, việc máy soạn sẵn (anh Việt duyệt bản vẽ 09/11/2026).

Vì sao có tệp này
-----------------
Bếp Pastry báo máy "Đếm hôm nay" chia 10 món giống hệt nhau năm sáng liền
(KK-26-00072 tới KK-26-00080). Gốc là phiếu nằm Chờ duyệt mà không ai được
nhắc. Anh Việt muốn một chỗ trong phân hệ Cài đặt để bật các luồng tự động
mang tính kiểm soát cho mọi kho, mọi bộ phận, và chốt hướng ngày 09/11:

    *"Anh muốn nó là việc cụ thể luôn để cho nhân viên chỉ việc bấm vào là
    làm á. Như là lệnh sản xuất có thể tự động tạo luôn được không? Chỉ việc
    nhập số."*

Nên mỗi dòng ở đây là một VIỆC máy soạn sẵn rồi đưa vào Việc cần làm của
đúng người, không phải một cảnh báo. Tin Zalo chỉ là đường mở thẳng vào
việc; quá hạn mới báo lên cấp trên. Anh chốt giữ một lần bấm Chốt kế hoạch
của bếp trưởng mỗi sáng (máy không tự tạo lệnh lúc 5 giờ).

Luật ô số (anh duyệt cùng bản vẽ)
---------------------------------
Số ĐẾM (kiểm kê, số làm ra, tiền trong két) máy để trống cho người nhập, số
của máy chỉ hiện sau khi nhập: điền sẵn thì người ta bấm Đồng ý cho qua và
mất đúng cái kiểm soát cần có. Số ĐẶT, số CHUYỂN thì máy tính hộ, người sửa.

Cấu trúc
--------
`VIEC` là sổ đăng ký DUY NHẤT của các việc: tên, mô tả, giờ, hạn, ai nhận.
Màn app, bảng trên Desk (Cài đặt lõi, tab Tự động hoá) và nhịp chạy đều đọc
từ đây. Giá trị anh sửa nằm ở bảng con `Vagabond Viec Tu Dong` của Vagabond
Settings; ô nào trống hay điền hỏng thì lấy mặc định của sổ đăng ký.

Phần THUẦN (không chạm Frappe) đứng trước vạch, phần chạm hệ đứng sau.
"""

import re

import frappe
from frappe.utils import add_days, cint, flt, get_datetime, getdate, now_datetime, nowdate

from vagabond import kenh_zalo

BANG = "Vagabond Viec Tu Dong"
CAI_DAT = "Vagabond Settings"
TRUONG_BANG = "viec_tu_dong"

QUYEN_SUA = ("System Manager", "AP Giám đốc", "Giám đốc")
QUYEN_XEM = QUYEN_SUA + ("Manufacturing Manager", "Stock Manager", "Sales Manager",
	"Accounts Manager", "Purchase Manager", "VGB - Quản lý cửa hàng")

BO_PHAN = ("Bếp", "Kho", "Thu mua", "Bán hàng", "Quầy", "Kế toán")

# Kiểu hạn: "luc" là giờ trong ngày (07:00), "sau_gio" là số giờ kể từ lúc
# phiếu vào trạng thái chờ (24 giờ). Trống là việc không có hạn riêng.
VIEC = (
	{
		"ma": "lenh_tu_ke_hoach", "bo_phan": "Bếp", "icon": "📋",
		"ten": "Lệnh sản xuất từ kế hoạch",
		"mo": "Bếp không phải tự lập lệnh từng món.",
		"may": "0:00 lập kế hoạch nháp từ các phiếu yêu cầu sản xuất. 5:00 nhắn nhóm Bếp và đưa việc Chốt kế hoạch vào Việc cần làm của bếp trưởng.",
		"nguoi": "Bếp trưởng mở kế hoạch, sửa số nếu cần, bấm Chốt kế hoạch một lần: máy tạo lệnh cho mọi món còn phải làm, đúng kho từng món.",
		"o": "san", "gio": "00:00", "gio_sua": 0, "han": "07:00", "han_kieu": "luc",
		"bao": "Quá hạn chưa ra lệnh nào: nhắn nhóm Bếp.",
		"mac_dinh": 1, "co_san": 1, "man": "KHSX",
	},
	{
		"ma": "ghi_nhan_cuoi_ca", "bo_phan": "Bếp", "icon": "✅",
		"ten": "Ghi nhận sản lượng cuối ca",
		"mo": "Thiếu bước này thì kho thành phẩm sai, giá vốn sai.",
		"may": "Từ giờ chạy, đưa việc Ghi nhận sản lượng vào Việc cần làm của bếp, mở thẳng danh sách lệnh hôm nay kèm ảnh món và số kế hoạch.",
		"nguoi": "Tổ trưởng bếp bấm ✓ trên từng lệnh, nhập số cân được thật. Ô số làm ra để trống, máy không điền sẵn.",
		"o": "trong", "gio": "19:00", "gio_sua": 1, "han": "22:00", "han_kieu": "luc",
		"bao": "Quá hạn còn lệnh chưa ghi: nhắn nhóm Bếp, mỗi bếp một tin.",
		"mac_dinh": 1, "co_san": 0, "man": "MFG",
	},
	{
		"ma": "chuyen_nvl", "bo_phan": "Kho", "icon": "📦",
		"ten": "Chuyển nguyên liệu cho kế hoạch",
		"mo": "Bếp có đủ hàng trước giờ vào ca.",
		"may": "Ngay sau khi có kế hoạch hôm nay, máy gửi phiếu xin chuyển nguyên liệu từ Kho tổng 307 sang kho từng bếp, đúng bảng nguyên liệu của kế hoạch.",
		"nguoi": "Thủ kho mở việc trong Việc cần làm, soạn hàng theo phiếu, sửa số nếu thiếu hàng, bấm Soạn hàng. Bếp bấm Đã nhận hàng.",
		"o": "san", "gio": "00:15", "gio_sua": 1, "han": "05:00", "han_kieu": "luc",
		"bao": "Quá hạn chưa chuyển: nhắn nhóm Kho.",
		"mac_dinh": 1, "co_san": 0, "man": "VCL",
	},
	{
		"ma": "dem_hom_nay", "bo_phan": "Kho", "icon": "🧮",
		"ten": "Đếm hôm nay",
		"mo": "Mỗi sáng đếm 10 món mỗi kho bếp, món đắt đếm dày hơn.",
		"may": "7:30 chia 10 món cho mỗi kho theo hạng A, B, C và nhắn nhóm Bếp tên các món cần đếm.",
		"nguoi": "Tổ trưởng kho, bếp bấm Đếm hôm nay, nhập số đếm, bấm Chốt phiếu. Máy không hiện số tồn trên máy trước khi nhập.",
		"o": "trong", "gio": "07:30", "gio_sua": 0, "han": "", "han_kieu": "",
		"bao": "",
		"mac_dinh": 1, "co_san": 1, "man": "KK",
	},
	{
		"ma": "duyet_kiem_ke", "bo_phan": "Kho", "icon": "🔎",
		"ten": "Duyệt, ghi sổ phiếu kiểm kê",
		"mo": "Phiếu chờ duyệt lâu thì tồn trên máy vẫn sai.",
		"may": "Ngay khi bếp chốt phiếu, việc Phiếu kiểm kê chờ chốt sổ hiện trong Việc cần làm của quản lý kho, kèm các dòng lệch.",
		"nguoi": "Quản lý kho xem dòng lệch và lý do, chọn tài khoản máy gợi ý, bấm Ghi sổ.",
		"o": "", "gio": "", "gio_sua": 0, "han": "24", "han_kieu": "sau_gio", "han2": "48",
		"bao": "Quá hạn bậc 1: nhắn nhóm Kho. Quá bậc 2: nhắn Ban giám đốc.",
		"mac_dinh": 1, "co_san": 0, "man": "KK",
	},
	{
		"ma": "ycmh_tu_dong", "bo_phan": "Kho", "icon": "🛒",
		"ten": "Yêu cầu mua khi hàng sắp hết",
		"mo": "Không cần khai hạn mức: máy đọc lượng dùng thật của từng kho.",
		"may": "Giờ chạy, máy đọc lượng dùng 14 ngày qua của từng kho mua hàng. Món chỉ còn đủ dùng dưới số ngày đặt ở đây thì máy soạn nháp yêu cầu mua đủ dùng số ngày thứ hai, mỗi kho một phiếu.",
		"nguoi": "Người giữ kho mở việc Yêu cầu mua máy soạn trong Việc cần làm, sửa số, bấm Gửi duyệt. Phiếu không ai đụng tới thì máy xoá sau 2 ngày.",
		"o": "san", "gio": "06:00", "gio_sua": 1, "han": "10:00", "han_kieu": "luc",
		"nguong": 3, "du": 7,
		"bao": "Quá hạn còn nháp: nhắn nhóm Kho.",
		"mac_dinh": 1, "co_san": 0, "man": "VCL",
	},
	{
		"ma": "gom_yeu_cau_mua", "bo_phan": "Thu mua", "icon": "🧺",
		"ten": "Gom yêu cầu mua thành đơn mua",
		"mo": "Năm phiếu xin cùng một món thành một dòng, chia sẵn theo nhà cung cấp.",
		"may": "Từ giờ chạy, máy gom mọi yêu cầu mua các bộ phận đã gửi mà chưa duyệt, theo nhà cung cấp mặc định, cộng theo món, kèm tồn kho tổng và hàng đang chờ về.",
		"nguoi": "Thu mua mở Gom yêu cầu mua, sửa số mua, bấm Chốt cho từng nhà cung cấp: máy duyệt các phiếu xin và lập đơn mua. Gửi đơn cho nhà cung cấp vẫn là nút riêng.",
		"o": "san", "gio": "09:00", "gio_sua": 1, "han": "15:00", "han_kieu": "luc",
		"bao": "Lúc giờ chạy và lúc hạn còn yêu cầu chưa gom: nhắn nhóm Thu mua.",
		"mac_dinh": 1, "co_san": 0, "man": "GOMMUA",
	},
	{
		"ma": "du_chi_dot", "bo_phan": "Thu mua", "icon": "💸",
		"ten": "Dự chi công nợ đợt 10 và 20",
		"mo": "Không còn bảng Excel dự chi: máy soạn sẵn đợt trả nhà cung cấp từ dư nợ ERP.",
		"may": "Ngày 7 và 17, từ giờ chạy, máy soạn đợt nháp cho ngày 10 hoặc 20: mọi hoá đơn mua còn nợ (trừ phí sàn cấn trừ), hạn dự tính theo số ngày được nợ, tờ tới hạn điền sẵn trả hết. Nhắn nhóm Thu mua.",
		"nguoi": "Uyên mở Dự chi công nợ, thương lượng từng nhà cung cấp: Trả hết hoặc gõ số trả từng hoá đơn, máy tính phần gia hạn. Bấm Gửi duyệt. Giám đốc duyệt xong máy lập APP luôn.",
		"o": "san", "gio": "09:00", "gio_sua": 1, "han": "17:00", "han_kieu": "luc",
		"bao": "Lúc soạn xong: nhắn nhóm Thu mua.",
		"mac_dinh": 1, "co_san": 0, "man": "DUCHI",
	},
	{
		"ma": "ycsx_thieu", "bo_phan": "Bán hàng", "icon": "🎂",
		"ten": "Yêu cầu sản xuất cho bánh đang thiếu",
		"mo": "Khách đã đặt mà bếp chưa có lệnh làm.",
		"may": "Giờ chạy, so số khách đã đặt ngày mai với tồn và số bếp đã lên, đưa việc Bánh thiếu ngày mai vào Việc cần làm của Sales.",
		"nguoi": "Sales mở việc, bấm Gợi ý từ hệ thống ở bước chọn món, sửa số, gửi bếp trước kế hoạch 0:00.",
		"o": "san", "gio": "17:00", "gio_sua": 1, "han": "21:00", "han_kieu": "luc",
		"bao": "Lúc giờ chạy và lúc hạn còn thiếu: nhắn nhóm Bán hàng.",
		"mac_dinh": 1, "co_san": 0, "man": "VCL",
	},
	{
		"ma": "chot_ca", "bo_phan": "Quầy", "icon": "🧾",
		"ten": "Chốt ca",
		"mo": "Lệch két phải giải trình ngay trong ngày.",
		"may": "Lúc chốt ca, máy giữ sẵn doanh thu theo máy, chuyển khoản, thẻ, nhưng không hiện số tiền mặt hệ thống.",
		"nguoi": "Thu ngân đếm két, nhập tiền mặt đếm được, bấm Chốt ca. Lệch từ 50.000 đ máy nhắn Ban giám đốc.",
		"o": "trong", "gio": "", "gio_sua": 0, "han": "", "han_kieu": "",
		"bao": "",
		"mac_dinh": 1, "co_san": 1, "chi_xem": 1, "man": "POS",
	},
	{
		"ma": "khop_tien", "bo_phan": "Kế toán", "icon": "🏦",
		"ten": "Khớp tiền chuyển khoản với bill",
		"mo": "Tiền chưa gắn bill là sổ thu sai.",
		"may": "Tiền về qua SePay, máy tự ghép với bill có cùng số tiền và nội dung. Bill chuyển khoản chưa khớp nằm ở màn Đối soát chuyển khoản.",
		"nguoi": "Kế toán, quản lý cửa hàng mở Đối soát chuyển khoản, chọn giao dịch đúng cho từng bill còn lại.",
		"o": "san", "gio": "", "gio_sua": 0, "han": "", "han_kieu": "",
		"bao": "",
		"mac_dinh": 1, "co_san": 1, "chi_xem": 1, "man": "DSCK",
	},
)

MA = tuple(v["ma"] for v in VIEC)


# ================================================================== THUẦN


def chuan_gio(s):
	"""Giờ người gõ tay về dạng "HH:MM". Hỏng thì trả chuỗi rỗng. THUẦN.

	Ô cài đặt người điền tay là đầu vào không tin được (v608): nhận "7",
	"07", "7h", "7g", "7:5", "07:05", "19h30", "19g30", "7.30", " 7 : 30 ".
	"""
	t = str(s if s is not None else "").strip().lower().replace(" ", "")
	if not t:
		return ""
	m = re.match(r"^(\d{1,2})(?:[:hg.](\d{0,2}))?(?:p|ph|phut|phút)?$", t)
	if not m:
		return ""
	gio = int(m.group(1))
	phut = int(m.group(2)) if m.group(2) else 0
	if gio > 23 or phut > 59:
		return ""
	return "%02d:%02d" % (gio, phut)


def chuan_so_gio(s):
	"""Số giờ người gõ ("24", "24h", "24 giờ", "2 ngày") về số nguyên dương. Hỏng: 0. THUẦN."""
	t = str(s if s is not None else "").strip().lower()
	if not t:
		return 0
	m = re.match(r"^(\d{1,4})\s*(h|g|giờ|gio|tiếng|tieng|ngày|ngay)?$", t)
	if not m:
		return 0
	n = int(m.group(1))
	if m.group(2) in ("ngày", "ngay"):
		n *= 24
	return n if 0 < n <= 24 * 30 else 0


def phut_cua(gio):
	"""Phút kể từ nửa đêm của "HH:MM"; hỏng trả None. THUẦN."""
	g = chuan_gio(gio)
	if not g:
		return None
	h, m = g.split(":")
	return int(h) * 60 + int(m)


def den_gio(gio, bay_gio, cua_so=60):
	"""Đang trong cửa sổ chạy của một giờ hẹn chưa. THUẦN.

	Nhịp chạy 15 phút một lần, nên cửa sổ một giờ cho bốn lượt cơ hội: máy
	bận hay khởi động lại một lượt vẫn còn lượt sau. Việc nào chạy nhiều
	lượt phải tự chống trùng (khoá tin, khoá đã làm trong ngày).
	"""
	p = phut_cua(gio)
	if p is None:
		return False
	bay = bay_gio.hour * 60 + bay_gio.minute
	return p <= bay < p + cua_so


def da_qua(gio, bay_gio):
	"""Đã qua giờ hẹn trong ngày chưa. THUẦN."""
	p = phut_cua(gio)
	if p is None:
		return False
	return bay_gio.hour * 60 + bay_gio.minute >= p


def qua_so_gio(moc, bay_gio, so_gio):
	"""Từ mốc tới giờ đã quá số giờ chưa. THUẦN (moc, bay_gio là datetime)."""
	if not moc or not so_gio:
		return False
	return (bay_gio - moc).total_seconds() >= so_gio * 3600


def gop_cau_hinh(dong, viec=VIEC):
	"""Sổ đăng ký + giá trị anh sửa -> cấu hình dùng thật. THUẦN.

	dong: [{"ma","bat","gio","han","han2"}] đọc từ bảng con. Mã lạ bị bỏ.
	Ô trống hay điền hỏng thì lấy mặc định, không bao giờ để một việc chạy
	với giờ rỗng. Việc chi_xem (đã có màn riêng) luôn bật.
	"""
	theo_ma = {}
	for d in dong or []:
		ma = (d.get("ma") or "").strip()
		if ma:
			theo_ma[ma] = d
	ra = []
	for v in viec:
		c = dict(v)
		d = theo_ma.get(v["ma"])
		c["bat"] = cint(v.get("mac_dinh"))
		if d is not None and d.get("bat") is not None and not v.get("chi_xem"):
			c["bat"] = 1 if cint(d.get("bat")) else 0
		if v.get("gio_sua") and d is not None:
			c["gio"] = chuan_gio(d.get("gio")) or v.get("gio") or ""
		if v.get("han_kieu") == "luc" and d is not None:
			c["han"] = chuan_gio(d.get("han")) or v.get("han") or ""
		elif v.get("han_kieu") == "sau_gio":
			mac = cint(v.get("han"))
			h1 = chuan_so_gio(d.get("han")) if d is not None else 0
			c["han"] = str(h1 or mac)
			if v.get("han2"):
				mac2 = cint(v.get("han2"))
				h2 = chuan_so_gio(d.get("han2")) if d is not None else 0
				c["han2"] = str(h2 or mac2)
				if cint(c["han2"]) <= cint(c["han"]):
					# Bậc hai phải sau bậc một, không thì giám đốc nhận tin trước quản lý kho.
					c["han2"] = str(cint(c["han"]) + max(mac2 - mac, 1))
		if v.get("nguong"):
			n1 = cint(d.get("so_ngay_con")) if d is not None else 0
			n2 = cint(d.get("so_ngay_du")) if d is not None else 0
			c["nguong"] = n1 if 0 < n1 <= 60 else cint(v["nguong"])
			c["du"] = n2 if 0 < n2 <= 90 else cint(v["du"])
			if c["du"] <= c["nguong"]:
				# Mua đủ dùng phải dài hơn ngưỡng báo, không thì sáng nào cũng soạn lại.
				c["du"] = c["nguong"] + max(cint(v["du"]) - cint(v["nguong"]), 1)
		ra.append(c)
	return ra


def kiem_luu(ma, gio=None, han=None, han2=None, so_ngay_con=None, so_ngay_du=None):
	"""Kiểm giá trị anh gõ trước khi ghi. Trả (giá trị đã chuẩn, câu lỗi). THUẦN.

	Gõ hỏng thì báo lỗi rõ chứ không lặng lẽ thay bằng mặc định: anh gõ 25:00
	mà máy cất 07:00 thì anh tưởng đã lưu đúng ý.
	"""
	v = next((x for x in VIEC if x["ma"] == ma), None)
	if not v:
		return None, "Không có việc tự động mã %s." % ma
	ra = {}
	if gio is not None and str(gio).strip() != "":
		if not v.get("gio_sua"):
			return None, "Giờ chạy của việc này cố định, không sửa được ở đây."
		g = chuan_gio(gio)
		if not g:
			return None, "Giờ chạy \"%s\" chưa đúng. Gõ kiểu 19:00 hoặc 19h." % gio
		ra["gio"] = g
	if han is not None and str(han).strip() != "":
		if v.get("han_kieu") == "luc":
			g = chuan_gio(han)
			if not g:
				return None, "Giờ hạn \"%s\" chưa đúng. Gõ kiểu 22:00 hoặc 22h." % han
			ra["han"] = g
		elif v.get("han_kieu") == "sau_gio":
			n = chuan_so_gio(han)
			if not n:
				return None, "Số giờ \"%s\" chưa đúng. Gõ kiểu 24 hoặc 2 ngày." % han
			ra["han"] = str(n)
		else:
			return None, "Việc này không có hạn riêng."
	if han2 is not None and str(han2).strip() != "":
		if not v.get("han2"):
			return None, "Việc này không có bậc báo thứ hai."
		n = chuan_so_gio(han2)
		if not n:
			return None, "Số giờ \"%s\" chưa đúng. Gõ kiểu 48 hoặc 2 ngày." % han2
		ra["han2"] = str(n)
	for k, nhan, tran in (("so_ngay_con", "Số ngày còn dùng", 60), ("so_ngay_du", "Số ngày mua đủ dùng", 90)):
		gt = so_ngay_con if k == "so_ngay_con" else so_ngay_du
		if gt is None or str(gt).strip() == "":
			continue
		if not v.get("nguong"):
			return None, "Việc này không có ô số ngày."
		n = chuan_so_gio(str(gt).replace("ngày", "").strip())
		if not n or n > tran:
			return None, "%s \"%s\" chưa đúng. Gõ số ngày từ 1 tới %d." % (nhan, gt, tran)
		ra[k] = n
	if v.get("nguong") and ("so_ngay_con" in ra or "so_ngay_du" in ra):
		n1 = cint(ra.get("so_ngay_con") or v.get("nguong"))
		n2 = cint(ra.get("so_ngay_du") or v.get("du"))
		if n2 <= n1:
			return None, "Số ngày mua đủ dùng phải lớn hơn số ngày còn dùng (đang %d và %d)." % (n1, n2)
	if v.get("han2") and ("han" in ra or "han2" in ra):
		h1 = cint(ra.get("han") or v.get("han"))
		h2 = cint(ra.get("han2") or v.get("han2"))
		if h2 <= h1:
			return None, "Bậc báo Ban giám đốc phải sau bậc báo nhóm Kho (đang %d giờ và %d giờ)." % (h1, h2)
	return ra, ""


def mo_ta_han(c):
	"""Chữ ngắn cho cột Quá hạn thì. THUẦN."""
	if c.get("han_kieu") == "luc" and c.get("han"):
		return "Quá %s" % c["han"]
	if c.get("han_kieu") == "sau_gio" and c.get("han"):
		ra = "Quá %s giờ" % c["han"]
		if c.get("han2"):
			ra += ", rồi %s giờ" % c["han2"]
		return ra
	return ""


def bep_cua_bo_phan(bo_phan):
	"""Mã bếp ("pastry", "baker") từ bộ phận người dùng ("Bếp Pastry"). THUẦN."""
	t = str(bo_phan or "").lower()
	for ma in ("pastry", "baker"):
		if ma in t:
			return ma
	return ""


def dong_viec(loai, ma, nhom, phu, ngay, qua_han):
	"""Một dòng cho màn Việc cần làm, đúng khuôn viec_can_lam. THUẦN."""
	return {"loai": loai, "ma": ma, "nhom": nhom, "phu": phu, "ngay": str(ngay or ""),
		"tt": "qua_han" if qua_han else "cho_lam"}


# ============================================================ PHẦN CHẠM HỆ


def _doc_bang():
	try:
		return frappe.get_all(BANG, filters={"parent": CAI_DAT, "parenttype": CAI_DAT},
			fields=["name", "ma", "bat", "gio", "han", "han2", "so_ngay_con", "so_ngay_du", "idx"], order_by="idx asc",
			limit_page_length=0)
	except Exception:
		return []


def cau_hinh():
	"""Cấu hình dùng thật, theo mã. Đọc hỏng thì dùng mặc định của sổ đăng ký."""
	return {c["ma"]: c for c in gop_cau_hinh(_doc_bang())}


def bat(ma):
	"""Việc này đang bật không. Đọc hỏng thì coi như ĐANG BẬT: các nhịp cũ đã
	chạy từ trước v646, một lỗi đọc cài đặt không được làm chúng lặng lẽ tắt."""
	try:
		c = cau_hinh().get(ma)
		return bool(c and c.get("bat"))
	except Exception:
		return True


def _co_vai(quyen):
	return bool(set(frappe.get_roles()) & set(quyen))


def _chan(quyen):
	if not _co_vai(quyen):
		frappe.throw("Bạn chưa được mở màn Cài đặt tự động hoá. Nhờ quản trị cấp quyền.",
			frappe.PermissionError)


def _hom_nay_tu_toi():
	ngay = getdate(nowdate())
	return ngay, "%s 00:00:00" % ngay, "%s 00:00:00" % add_days(ngay, 1)


def _lenh_hom_nay_chua_ghi(bep=""):
	"""Lệnh sản xuất làm hôm nay còn chưa ghi đủ số làm ra."""
	from vagabond.ke_hoach_sx import TRANG_THAI_XONG
	from vagabond.kho_san_xuat import bep_cua_kho

	ngay, tu, toi = _hom_nay_tu_toi()
	ds = frappe.get_all("Work Order", filters={"docstatus": 1, "status": ["not in", list(TRANG_THAI_XONG)],
		"planned_start_date": [">=", tu]}, fields=["name", "production_item", "item_name", "qty",
		"produced_qty", "stock_uom", "fg_warehouse", "source_warehouse", "planned_start_date"],
		limit_page_length=0)
	ra = []
	for w in ds:
		if str(w.get("planned_start_date") or "") >= toi:
			continue
		if flt(w.get("produced_qty")) >= flt(w.get("qty")) - 0.0005:
			continue
		b = bep_cua_kho(w.get("fg_warehouse") or "") or bep_cua_kho(w.get("source_warehouse") or "") or ""
		if bep and b and b != bep:
			continue
		w["bep"] = b
		ra.append(w)
	return ra


def _ke_hoach_hom_nay():
	"""(tên phiếu kế hoạch hôm nay, số món chưa có lệnh, số lệnh đã ra)."""
	from vagabond import ke_hoach_sx as khsx

	ngay = getdate(nowdate())
	ten = khsx._phieu_cua_ngay(ngay)
	if not ten:
		return "", 0, 0
	con = 0
	for d in frappe.get_all("Production Plan Item", filters={"parent": ten, "parenttype": "Production Plan"},
			fields=["planned_qty", "ordered_qty"], limit_page_length=0):
		if flt(d.get("planned_qty")) - flt(d.get("ordered_qty")) > 0.0005:
			con += 1
	da_lenh = frappe.db.count("Work Order", {"production_plan": ten, "docstatus": ["<", 2]})
	return ten, con, da_lenh


# --------------------------------------------------- nguồn việc cho Việc cần làm


def viec_ke_hoach():
	"""Việc Chốt kế hoạch: kế hoạch hôm nay còn món chưa có lệnh."""
	c = cau_hinh().get("lenh_tu_ke_hoach") or {}
	if not c.get("bat"):
		return []
	ten, con, _ = _ke_hoach_hom_nay()
	if not ten or not con:
		return []
	qua = da_qua(c.get("han"), now_datetime())
	return [dong_viec("ke_hoach_sx", ten, "Bếp: việc máy soạn sẵn",
		"Chốt kế hoạch hôm nay: %d món chưa có lệnh · hạn %s" % (con, c.get("han") or ""),
		nowdate(), qua)]


def viec_ghi_nhan(bo_phan=""):
	"""Việc Ghi nhận sản lượng: từ giờ chạy, lệnh hôm nay chưa ghi số làm ra."""
	c = cau_hinh().get("ghi_nhan_cuoi_ca") or {}
	bay = now_datetime()
	if not c.get("bat") or not da_qua(c.get("gio"), bay):
		return []
	ds = _lenh_hom_nay_chua_ghi(bep_cua_bo_phan(bo_phan))
	if not ds:
		return []
	return [dong_viec("ghi_nhan_sx", "Lệnh %s" % getdate(nowdate()).strftime("%d/%m"),
		"Bếp: việc máy soạn sẵn",
		"Ghi nhận sản lượng: %d lệnh hôm nay chưa ghi số làm ra · hạn %s" % (len(ds), c.get("han") or ""),
		nowdate(), da_qua(c.get("han"), bay))]


def _banh_thieu_ngay_mai(cache=True):
	"""Món khách đặt ngày mai còn thiếu (đọc goi_y_ycsx), giữ 10 phút cho đỡ tốn."""
	from vagabond import goi_y_ycsx

	ngay = add_days(getdate(nowdate()), 1)
	khoa = "vgb_vtd_ycsx_thieu:%s" % ngay
	if cache:
		try:
			v = frappe.cache().get_value(khoa)
			if v is not None:
				return v
		except Exception:
			pass
	kq = goi_y_ycsx.goi_y(str(ngay)) or {}
	ds = [{"ma": d.get("ma_hang"), "ten": d.get("ten_banh") or d.get("ma_hang"), "can": flt(d.get("can"))}
		for d in kq.get("dong") or [] if flt(d.get("can")) > 0]
	try:
		frappe.cache().set_value(khoa, ds, expires_in_sec=600)
	except Exception:
		pass
	return ds


def viec_ycsx_thieu():
	"""Việc Bánh thiếu ngày mai: từ giờ chạy, Sales còn món chưa lên yêu cầu."""
	c = cau_hinh().get("ycsx_thieu") or {}
	bay = now_datetime()
	if not c.get("bat") or not da_qua(c.get("gio"), bay):
		return []
	ds = _banh_thieu_ngay_mai()
	if not ds:
		return []
	ngay = add_days(getdate(nowdate()), 1)
	return [dong_viec("ycsx_thieu", "Ngày %s" % ngay.strftime("%d/%m"), "Bán hàng: việc máy soạn sẵn",
		"Bánh khách đặt còn thiếu: %d món · gửi bếp trước %s" % (len(ds), c.get("han") or ""),
		ngay, da_qua(c.get("han"), bay))]


def viec_gom_mua():
	"""Việc Gom yêu cầu mua: từ giờ chạy, còn yêu cầu mua đã gửi chưa gom."""
	from vagabond import gom_mua

	c = cau_hinh().get("gom_yeu_cau_mua") or {}
	bay = now_datetime()
	if not c.get("bat") or not da_qua(c.get("gio"), bay):
		return []
	so_mon, so_phieu = gom_mua.dem_cho_gom()
	if not so_mon:
		return []
	return [dong_viec("gom_mua", "Gom yêu cầu mua", "Thu mua: việc máy soạn sẵn",
		"%d món từ %d phiếu chờ gom thành đơn mua · hạn %s" % (so_mon, so_phieu, c.get("han") or ""),
		nowdate(), da_qua(c.get("han"), bay))]


# Dấu "máy soạn" trên phiếu yêu cầu mua (Codex 549): mọi chỗ đếm, nhắc và dọn
# phiếu máy soạn đều lọc theo dấu này, không theo người tạo. Người tạo
# Administrator còn khớp cả phiếu tay của quản trị và phiếu sản xuất, chuyển
# kho của luồng khác; dọn theo người tạo là xoá nhầm chứng từ thật.
TRUONG_MOI = {
	"Material Request": [
		{
			"fieldname": "vgb_may_soan",
			"label": "Máy soạn",
			"fieldtype": "Check",
			"insert_after": "material_request_type",
			"read_only": 1,
			"no_copy": 1,
			"description": "Máy soạn theo lượng dùng 14 ngày. Để nháp quá 2 ngày mà không ai sửa thì máy tự xoá.",
		},
	],
}


def loc_may_soan(**them):
	"""Bộ lọc DUY NHẤT cho phiếu yêu cầu mua máy soạn."""
	loc = {"material_request_type": "Purchase", "vgb_may_soan": 1}
	loc.update(them)
	return loc


def viec_ycmh_nhap(kho=None, xem_het=False):
	"""Phiếu yêu cầu mua máy soạn còn nháp: người giữ kho đó gửi; thu mua thấy hết."""
	c = cau_hinh().get("ycmh_tu_dong") or {}
	if not c.get("bat") or not (kho or xem_het):
		return []
	loc = loc_may_soan(docstatus=0)
	if kho:
		loc["set_warehouse"] = ["in", list(kho)]
	ra = []
	for x in frappe.get_all("Material Request", filters=loc, fields=["name", "set_warehouse", "transaction_date"],
			order_by="transaction_date asc", limit_page_length=40):
		ra.append(dong_viec("ycmh_nhap", x["name"], "Kho: yêu cầu mua máy soạn",
			"Hàng sắp hết ở %s, sửa số rồi bấm Gửi duyệt" % (x.get("set_warehouse") or ""),
			x.get("transaction_date"), da_qua(c.get("han"), now_datetime())))
	return ra


# ----------------------------------------------------------------- nhịp chạy


def _lam_mot_lan(khoa):
	"""Khoá "đã làm hôm nay" trong bộ nhớ đệm. Mất bộ nhớ đệm thì việc chạy
	lại lượt sau; mọi việc gọi qua đây đều tự chống trùng ở tầng dưới."""
	try:
		return bool(frappe.cache().get_value(khoa))
	except Exception:
		return False


def _danh_dau(khoa):
	try:
		frappe.cache().set_value(khoa, 1, expires_in_sec=2 * 86400)
	except Exception:
		pass


def _chua_bao(khoa):
	"""Khoá này chưa báo lần nào. Nhịp 15 phút gọi lại cùng khoá nhiều lượt;
	kenh_zalo tự chống gửi trùng, nhưng nhóm chưa khai thì mỗi lượt lại ghi
	một Error Log, nên chặn thêm ở đây bằng khoá đã báo."""
	return not _lam_mot_lan("vgb_vtd_tin:%s" % khoa)


def _da_bao(khoa):
	"""Ghi sổ tin ngay rồi mới đặt khoá đã báo: đặt khoá trước mà giao dịch
	sau đó lùi thì tin mất và lượt sau cũng không gửi lại."""
	frappe.db.commit()
	_danh_dau("vgb_vtd_tin:%s" % khoa)


def _url(duong):
	try:
		return frappe.utils.get_url(duong)
	except Exception:
		return duong


def lam_chuyen_nvl(c, bay):
	"""Giờ chạy: gửi phiếu xin chuyển nguyên liệu của kế hoạch hôm nay."""
	from vagabond import ke_hoach_sx as khsx

	if not den_gio(c.get("gio"), bay):
		return
	ngay = getdate(nowdate())
	khoa = "vgb_vtd_chuyen_nvl:%s" % ngay
	if _lam_mot_lan(khoa):
		return
	ten = khsx._phieu_cua_ngay(ngay)
	if not ten:
		return
	kq = khsx.xin_chuyen_nvl(ten) or {}
	moi = kq.get("phieu") or []
	da_gui, dong = [], []
	for m in moi:
		try:
			d = frappe.get_doc("Material Request", m)
			d.flags.ignore_permissions = True
			d.submit()
			frappe.db.commit()
			da_gui.append(m)
			dong.append("%s: %s → %s, %d dòng" % (m, d.get("set_from_warehouse") or "Kho tổng 307",
				d.get("set_warehouse") or (d.items[0].warehouse if d.items else ""), len(d.items or [])))
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "viec_tu_dong: gửi phiếu chuyển %s" % m)
	_danh_dau(khoa)
	if da_gui:
		khoa = "vtd-nvl:%s" % ngay
		if _chua_bao(khoa):
			kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "Phiếu chuyển nguyên liệu cho kế hoạch %s" % ten,
				["Máy đã gửi %d phiếu xin chuyển từ Kho tổng 307 sang kho bếp:" % len(da_gui)] + dong +
				["Mở Việc cần làm, soạn hàng theo phiếu rồi bấm Soạn hàng."],
				link=_url("/app/material-request?material_request_type=Material%20Transfer"),
				khoa=khoa, nguon=ten, ma_tin="kho_chuyen_nvl_may_soan")
			_da_bao(khoa)


def lam_chuyen_nvl_han(c, bay):
	"""Giờ hạn: phiếu chuyển máy gửi hôm nay mà kho chưa chuyển hàng."""
	if not den_gio(c.get("han"), bay):
		return
	ngay = getdate(nowdate())
	ds = frappe.get_all("Material Request", filters={"material_request_type": "Material Transfer",
		"docstatus": 1, "status": "Pending", "owner": "Administrator", "transaction_date": ngay},
		fields=["name", "set_warehouse"], limit_page_length=0)
	if not ds:
		return
	khoa = "vtd-nvl-han:%s" % ngay
	if _chua_bao(khoa):
		kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "Phiếu chuyển nguyên liệu quá %s chưa soạn" % c.get("han"),
			["%d phiếu máy gửi hôm nay chưa chuyển hàng, bếp sắp vào ca:" % len(ds)] +
			["%s → %s" % (d.name, d.get("set_warehouse") or "") for d in ds[:10]],
			link=_url("/app/material-request?material_request_type=Material%20Transfer&status=Pending"),
			khoa=khoa, ma_tin="kho_chuyen_nvl_chua_soan")
		_da_bao(khoa)


def lam_ke_hoach_han(c, bay):
	"""Giờ hạn: kế hoạch hôm nay chưa ra lệnh nào."""
	if not den_gio(c.get("han"), bay):
		return
	ten, con, da_lenh = _ke_hoach_hom_nay()
	if not ten or not con or da_lenh:
		return
	khoa = "vtd-chua-chot:%s" % ten
	if _chua_bao(khoa):
		kenh_zalo.bao_hoac_ghi_loi("viec", "san_xuat", "Kế hoạch sản xuất hôm nay chưa chốt",
			["Kế hoạch %s còn %d món chưa có lệnh, đã quá %s." % (ten, con, c.get("han")),
				"Bếp trưởng mở Kế hoạch sản xuất, bấm Chốt kế hoạch để máy tạo lệnh."],
			link=_url("/app/production-plan/%s" % ten), khoa=khoa, nguon=ten,
			ma_tin="bep_chua_chot_ke_hoach")
		_da_bao(khoa)


def lam_ghi_nhan_han(c, bay):
	"""Giờ hạn cuối ca: lệnh hôm nay chưa ghi số làm ra, một tin mỗi bếp."""
	from vagabond.tin_ton_sx import ten_bep

	if not den_gio(c.get("han"), bay):
		return
	ngay = getdate(nowdate())
	theo_bep = {}
	for w in _lenh_hom_nay_chua_ghi():
		theo_bep.setdefault(w.get("bep") or "", []).append(w)
	for bep, ds in sorted(theo_bep.items()):
		dong = ["%s: %d lệnh hôm nay chưa ghi số làm ra, đã quá %s." % (ten_bep(bep), len(ds), c.get("han"))]
		dong += ["%s: %s" % (w.name, w.get("item_name") or w.get("production_item")) for w in ds[:10]]
		dong.append("Mở Lệnh sản xuất, bấm ✓ trên từng lệnh và nhập số cân được thật.")
		khoa = "vtd-ghi-nhan:%s:%s" % (bep or "khac", ngay)
		if _chua_bao(khoa):
			kenh_zalo.bao_hoac_ghi_loi("viec", "san_xuat", "Lệnh hôm nay chưa ghi nhận sản lượng", dong,
				link=_url("/app/work-order?status=In%20Process"), khoa=khoa,
				ma_tin="bep_chua_ghi_nhan")
			_da_bao(khoa)


def lam_duyet_kiem_ke(c, bay):
	"""Mỗi lượt: phiếu kiểm kê nằm Chờ duyệt quá bậc 1 (nhóm Kho), quá bậc 2 (Ban giám đốc).

	Mốc tính là lần sửa cuối của phiếu: phiếu đã Chờ duyệt thì không ai sửa
	nữa cho tới lúc duyệt, nên đó chính là lúc bếp bấm Chốt phiếu."""
	h1, h2 = cint(c.get("han")), cint(c.get("han2"))
	if not h1:
		return
	for p in frappe.get_all("Phieu Kiem Ke", filters={"trang_thai": "Chờ duyệt"},
			fields=["name", "kho", "ngay_kiem", "modified"], limit_page_length=200):
		moc = get_datetime(p.modified)
		ten_kho = p.get("kho") or ""
		if h2 and qua_so_gio(moc, bay, h2):
			khoa = "vtd-kk2:%s" % p.name
			if _chua_bao(khoa):
				kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "Phiếu kiểm kê chờ duyệt quá %d giờ" % h2,
					["%s, %s, kiểm ngày %s: quản lý kho chưa duyệt." % (p.name, ten_kho, getdate(p.ngay_kiem).strftime("%d/%m")),
						"Phiếu chưa ghi sổ thì tồn trên máy vẫn là số cũ và lịch đếm của kho bị lệch."],
					link=_url("/app/phieu-kiem-ke/%s" % p.name), khoa=khoa, nguon=p.name,
					ma_tin="bgd_kiem_ke_qua_han")
				_da_bao(khoa)
		if qua_so_gio(moc, bay, h1):
			khoa = "vtd-kk1:%s" % p.name
			if _chua_bao(khoa):
				kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "Phiếu kiểm kê chờ duyệt quá %d giờ" % h1,
					["%s, %s, kiểm ngày %s." % (p.name, ten_kho, getdate(p.ngay_kiem).strftime("%d/%m")),
						"Quản lý kho mở Kiểm kê, xem dòng lệch rồi bấm Ghi sổ."],
					link=_url("/app/phieu-kiem-ke/%s" % p.name), khoa=khoa, nguon=p.name,
					ma_tin="kho_kiem_ke_qua_han")
				_da_bao(khoa)


def lam_ycsx_thieu(c, bay):
	"""Giờ chạy và giờ hạn: món khách đặt ngày mai còn thiếu."""
	lan = "gio" if den_gio(c.get("gio"), bay) else ("han" if den_gio(c.get("han"), bay) else "")
	if not lan:
		return
	ds = _banh_thieu_ngay_mai(cache=False)
	if not ds:
		return
	ngay = add_days(getdate(nowdate()), 1)
	dong = ["%d món khách đã đặt cho %s còn thiếu so với tồn và số bếp đã lên:" % (len(ds), ngay.strftime("%d/%m"))]
	dong += ["%s: thiếu %s" % (d["ten"], ("%g" % d["can"])) for d in ds[:10]]
	if lan == "han":
		dong.append("Đã tới %s mà chưa gửi bếp. Kế hoạch 0:00 chỉ gom các yêu cầu đã gửi." % c.get("han"))
	dong.append("Mở Việc cần làm, bấm Gợi ý từ hệ thống ở bước chọn món rồi gửi bếp.")
	khoa = "vtd-ycsx:%s:%s" % (ngay, lan)
	if _chua_bao(khoa):
		kenh_zalo.bao_hoac_ghi_loi("viec", "san_xuat", "Bánh khách đặt ngày mai còn thiếu", dong,
			link=_url("/app/material-request/new"), khoa=khoa, ma_tin="bh_banh_thieu_ngay_mai")
		_da_bao(khoa)


def can_mua_them(ton, dang_ve, dung_ngay, nguong, du):
	"""Số cần mua thêm cho một món ở một kho, theo lượng dùng thật. THUẦN.

	ton: tồn thực; dang_ve: đã đặt chưa về cộng đã xin chưa đặt (Bin
	ordered_qty + indented_qty, để không xin trùng); dung_ngay: lượng dùng
	trung bình một ngày. Còn đủ dùng từ `nguong` ngày trở lên thì 0; không
	thì mua đủ dùng `du` ngày. Món không ai dùng thì không bao giờ xin."""
	dung_ngay = flt(dung_ngay)
	if dung_ngay <= 0:
		return 0
	co = flt(ton) + flt(dang_ve)
	if co / dung_ngay >= flt(nguong):
		return 0
	return round(max(dung_ngay * flt(du) - co, 0), 3)


SO_NGAY_DO = 14
SO_NGAY_MUA_GAN = 90


def goi_y_mua(nguong, du):
	"""{kho: [(ma, ten, dvt, số)]}: món sắp hết ở các kho có nhận hàng mua 90 ngày qua.

	Chỉ xét cặp (món, kho) đã từng nhận hàng mua ở đó: bánh, bán thành phẩm
	không bao giờ lọt vào yêu cầu mua. Lượng dùng là tổng xuất ra (dòng sổ
	kho âm, chưa huỷ) trong 14 ngày chia 14."""
	hom_nay = getdate(nowdate())
	cap = frappe.db.sql("""select distinct pri.item_code as ma, pri.warehouse as kho
		from `tabPurchase Receipt Item` pri join `tabPurchase Receipt` pr on pr.name = pri.parent
		where pr.docstatus = 1 and pr.posting_date >= %(tu)s and pri.warehouse is not null""",
		{"tu": add_days(hom_nay, -SO_NGAY_MUA_GAN)}, as_dict=True)
	if not cap:
		return {}
	cac_ma = sorted({c.ma for c in cap})
	cac_kho = sorted({c.kho for c in cap})
	dung = {(r.ma, r.kho): flt(r.sl) for r in frappe.db.sql("""select item_code as ma, warehouse as kho,
			-sum(actual_qty) as sl from `tabStock Ledger Entry`
		where is_cancelled = 0 and actual_qty < 0 and posting_date >= %(tu)s
			and item_code in %(ma)s and warehouse in %(kho)s
		group by item_code, warehouse""", {"tu": add_days(hom_nay, -SO_NGAY_DO), "ma": tuple(cac_ma),
		"kho": tuple(cac_kho)}, as_dict=True)}
	bin_ = {(b.item_code, b.warehouse): b for b in frappe.get_all("Bin", filters={"item_code": ["in", cac_ma],
		"warehouse": ["in", cac_kho]}, fields=["item_code", "warehouse", "actual_qty", "ordered_qty", "indented_qty"],
		limit_page_length=0)}
	hs = {i.name: i for i in frappe.get_all("Item", filters={"name": ["in", cac_ma], "disabled": 0,
		"is_purchase_item": 1}, fields=["name", "item_name", "stock_uom"], limit_page_length=0)}
	ra = {}
	for c in cap:
		if c.ma not in hs:
			continue
		b = bin_.get((c.ma, c.kho)) or {}
		sl = can_mua_them(b.get("actual_qty"), flt(b.get("ordered_qty")) + flt(b.get("indented_qty")),
			dung.get((c.ma, c.kho), 0) / SO_NGAY_DO, nguong, du)
		if sl > 0:
			ra.setdefault(c.kho, []).append((c.ma, hs[c.ma].item_name or c.ma, hs[c.ma].stock_uom, sl))
	return ra


def lam_ycmh_tu_dong(c, bay):
	"""Giờ chạy: soạn nháp yêu cầu mua cho món sắp hết, mỗi kho một phiếu. Giờ hạn: nhắc phiếu còn nháp."""
	ngay = getdate(nowdate())
	if den_gio(c.get("gio"), bay):
		khoa = "vgb_vtd_ycmh:%s" % ngay
		if _lam_mot_lan(khoa):
			return
		dong = []
		for kho, cac in sorted(goi_y_mua(c.get("nguong"), c.get("du")).items()):
			if frappe.db.exists("Material Request", loc_may_soan(docstatus=0, transaction_date=ngay, set_warehouse=kho)):
				continue
			try:
				mr = frappe.new_doc("Material Request")
				mr.material_request_type = "Purchase"
				mr.vgb_may_soan = 1
				mr.company = frappe.db.get_value("Warehouse", kho, "company")
				mr.transaction_date = ngay
				mr.schedule_date = add_days(ngay, 1)
				mr.set_warehouse = kho
				for ma, ten, dvt, sl in cac:
					mr.append("items", {"item_code": ma, "qty": sl, "uom": dvt, "stock_uom": dvt,
						"conversion_factor": 1, "warehouse": kho, "schedule_date": add_days(ngay, 1)})
				mr.flags.ignore_permissions = True
				mr.insert()
				frappe.db.commit()
				dong.append("%s: %s, %d món (%s)" % (mr.name, kho, len(mr.items), ", ".join(x[1] for x in cac[:4])))
			except Exception:
				frappe.db.rollback()
				frappe.log_error(frappe.get_traceback(), "viec_tu_dong: soạn yêu cầu mua kho %s" % kho)
		_danh_dau(khoa)
		if dong:
			khoa = "vtd-ycmh:%s" % ngay
			if _chua_bao(khoa):
				kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "Yêu cầu mua máy soạn cho hàng sắp hết",
					["Theo lượng dùng 14 ngày qua, còn đủ dùng dưới %s ngày. Máy đã soạn nháp:" % c.get("nguong")] + dong +
					["Người giữ kho mở Việc cần làm, sửa số rồi bấm Gửi duyệt."],
					link=_url("/app/material-request?docstatus=0"), khoa=khoa, ma_tin="kho_ycmh_may_soan")
				_da_bao(khoa)
	elif den_gio(c.get("han"), bay):
		ds = frappe.get_all("Material Request", filters=loc_may_soan(docstatus=0, transaction_date=ngay), pluck="name")
		if ds:
			khoa = "vtd-ycmh-han:%s" % ngay
			if _chua_bao(khoa):
				kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "Yêu cầu mua máy soạn còn nháp",
					["%d phiếu nháp sáng nay chưa gửi duyệt: %s." % (len(ds), ", ".join(ds[:8])),
						"Không gửi thì thu mua không gom được, hàng có thể hết giữa ca."],
					link=_url("/app/material-request?docstatus=0"), khoa=khoa, ma_tin="kho_ycmh_may_soan")
				_da_bao(khoa)


def lam_gom_mua(c, bay):
	"""Giờ chạy và giờ hạn: còn yêu cầu mua chờ gom thì nhắn nhóm Thu mua."""
	from vagabond import gom_mua

	lan = "gio" if den_gio(c.get("gio"), bay) else ("han" if den_gio(c.get("han"), bay) else "")
	if not lan:
		return
	so_mon, so_phieu = gom_mua.dem_cho_gom()
	if not so_mon:
		return
	ngay = getdate(nowdate())
	khoa = "vtd-gom:%s:%s" % (ngay, lan)
	if _chua_bao(khoa):
		dong = ["%d món từ %d phiếu yêu cầu mua đang chờ gom thành đơn mua." % (so_mon, so_phieu)]
		if lan == "han":
			dong.append("Đã quá %s. Bộ phận đang chờ hàng." % c.get("han"))
		dong.append("Mở Gom yêu cầu mua, sửa số rồi bấm Chốt cho từng nhà cung cấp.")
		kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "Yêu cầu mua chờ gom thành đơn", dong,
			link=_url("/app/material-request?material_request_type=Purchase&docstatus=1"), khoa=khoa, ma_tin="tm_gom_mua")
		_da_bao(khoa)


def lam_du_chi(c, bay):
	"""v653 (#555): ngày 7 và 17 soạn đợt dự chi nháp, nhắn nhóm Thu mua."""
	from vagabond import du_chi

	du_chi.lam_soan_tu_dong(c, bay)


SO_NGAY_GIU_NHAP = 2


def don_nhap_may_soan(bay):
	"""Xoá phiếu nháp máy soạn mà không ai đụng tới sau 2 ngày.

	Chỉ phiếu yêu cầu mua mang dấu Máy soạn, còn NHÁP (chưa gửi, không có bút
	toán nào), VÀ lần sửa cuối vẫn là máy: ai đã mở ra sửa một chữ thì phiếu
	là của người đó, giữ. Không lọc theo người tạo (Codex 549): nháp tay của
	Administrator, phiếu sản xuất, chuyển kho không bao giờ bị xoá ở đây."""
	moc = add_days(getdate(nowdate()), -SO_NGAY_GIU_NHAP)
	ds = frappe.get_all("Material Request", filters=loc_may_soan(docstatus=0, owner="Administrator",
		modified_by="Administrator", transaction_date=["<", moc]), pluck="name", limit_page_length=200)
	for ten in ds:
		frappe.delete_doc("Material Request", ten, ignore_permissions=True, force=True)
	return len(ds)


# Việc nào có hành động nào. Việc đã có màn riêng (chi_xem) không có ở đây.
HANH_DONG = (
	("lenh_tu_ke_hoach", lam_ke_hoach_han),
	("ghi_nhan_cuoi_ca", lam_ghi_nhan_han),
	("chuyen_nvl", lam_chuyen_nvl),
	("chuyen_nvl", lam_chuyen_nvl_han),
	("duyet_kiem_ke", lam_duyet_kiem_ke),
	("ycmh_tu_dong", lam_ycmh_tu_dong),
	("gom_yeu_cau_mua", lam_gom_mua),
	("du_chi_dot", lam_du_chi),
	("ycsx_thieu", lam_ycsx_thieu),
)


def _gieo_bang():
	"""Thêm dòng còn thiếu vào bảng trên Desk, để anh sửa được cả trên Desk.

	Chỉ THÊM, không sửa dòng đã có. Chạy trong nhịp (quyền Administrator)."""
	co = {d.get("ma") for d in _doc_bang()}
	thieu = [v for v in VIEC if v["ma"] not in co]
	if not thieu:
		return 0
	idx = len(co)
	for v in thieu:
		idx += 1
		frappe.get_doc({"doctype": BANG, "parent": CAI_DAT, "parenttype": CAI_DAT,
			"parentfield": TRUONG_BANG, "idx": idx, "ma": v["ma"], "ten": v["ten"],
			"bo_phan": v["bo_phan"], "bat": cint(v.get("mac_dinh")), "gio": v.get("gio") or "",
			"han": v.get("han") or "", "han2": v.get("han2") or "", "so_ngay_con": cint(v.get("nguong")),
			"so_ngay_du": cint(v.get("du"))}).db_insert()
	return len(thieu)


def chay():
	"""Nhịp 15 phút: chạy các việc đang bật, mỗi việc một giao dịch riêng.

	Việc nào lỗi thì lùi đúng giao dịch của việc đó, ghi Error Log rồi chạy
	tiếp việc sau. Không nuốt lỗi rồi để worker commit nửa chừng (bài học
	scheduler wrapper trong docs/bai-hoc-su-co.md)."""
	if getattr(frappe.flags, "vagabond_kiem_that", False):
		return
	try:
		frappe.set_user("Administrator")
	except Exception:
		pass
	try:
		if _gieo_bang():
			frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "viec_tu_dong: gieo bảng")
	cfg = cau_hinh()
	bay = now_datetime()
	try:
		if don_nhap_may_soan(bay):
			frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "viec_tu_dong: xoá nháp máy soạn")
	for ma, fn in HANH_DONG:
		c = cfg.get(ma) or {}
		if not c.get("bat"):
			continue
		try:
			fn(c, bay)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "viec_tu_dong: %s" % ma)


# ------------------------------------------------------------ màn app


def _tinh_hinh(c):
	"""Một dòng tình hình hôm nay cho cột Gần nhất, kèm màu. Lỗi thì im."""
	ma = c["ma"]
	if not c.get("bat"):
		return "Đang tắt", "x"
	bay = now_datetime()
	if ma == "lenh_tu_ke_hoach":
		ten, con, da = _ke_hoach_hom_nay()
		if not ten:
			return "Hôm nay chưa có kế hoạch", "x"
		if con and da_qua(c.get("han"), bay) and not da:
			return "%s: %d món chưa có lệnh, quá hạn" % (ten, con), "r"
		return "%s: %d lệnh đã ra, %d món chưa có lệnh" % (ten, da, con), ("y" if con else "g")
	if ma == "ghi_nhan_cuoi_ca":
		n = len(_lenh_hom_nay_chua_ghi())
		if not n:
			return "Lệnh hôm nay đã ghi đủ", "g"
		return "%d lệnh hôm nay chưa ghi" % n, ("r" if da_qua(c.get("han"), bay) else "y")
	if ma == "chuyen_nvl":
		ngay = getdate(nowdate())
		tong = frappe.db.count("Material Request", {"material_request_type": "Material Transfer",
			"owner": "Administrator", "transaction_date": ngay, "docstatus": 1})
		cho = frappe.db.count("Material Request", {"material_request_type": "Material Transfer",
			"owner": "Administrator", "transaction_date": ngay, "docstatus": 1, "status": "Pending"})
		if not tong:
			return "Hôm nay máy chưa gửi phiếu nào", "x"
		return "Hôm nay %d phiếu, %d chưa chuyển" % (tong, cho), ("y" if cho else "g")
	if ma == "duyet_kiem_ke":
		n = frappe.db.count("Phieu Kiem Ke", {"trang_thai": "Chờ duyệt"})
		return ("%d phiếu đang chờ duyệt" % n) if n else "Không phiếu nào chờ", ("y" if n else "g")
	if ma == "dem_hom_nay":
		n = frappe.db.count("Phieu Kiem Ke", {"ngay_kiem": nowdate(), "trang_thai": ["!=", "Đã huỷ"]})
		return "Hôm nay %d phiếu đếm" % n, ("g" if n else "y")
	if ma == "ycsx_thieu":
		if not da_qua(c.get("gio"), bay):
			return "Chạy lúc %s" % c.get("gio"), "x"
		n = len(_banh_thieu_ngay_mai())
		return ("%d món ngày mai còn thiếu" % n) if n else "Ngày mai đủ bánh", ("y" if n else "g")
	if ma == "ycmh_tu_dong":
		n = frappe.db.count("Material Request", loc_may_soan(docstatus=0, transaction_date=nowdate()))
		return ("Sáng nay %d phiếu nháp chờ gửi" % n) if n else "Không phiếu nháp nào chờ", ("y" if n else "g")
	if ma == "gom_yeu_cau_mua":
		from vagabond import gom_mua

		so_mon, so_phieu = gom_mua.dem_cho_gom()
		if not so_mon:
			return "Không còn yêu cầu chờ gom", "g"
		return "%d món từ %d phiếu chờ gom" % (so_mon, so_phieu), ("r" if da_qua(c.get("han"), bay) else "y")
	if ma == "du_chi_dot":
		from vagabond import du_chi

		nd = du_chi.ngay_dot_ke_tiep(getdate(nowdate()))
		ten = frappe.db.get_value(du_chi.DT, du_chi.ma_dot(nd), ["trang_thai", "tong_tra"], as_dict=True)
		if not ten:
			return "Đợt %s soạn ngày %s" % (nd.strftime("%d/%m"), du_chi.ngay_soan(nd).strftime("%d/%m")), "x"
		return "Đợt %s: %s, trả %s đ" % (nd.strftime("%d/%m"), du_chi.NHAN.get(ten.trang_thai, ten.trang_thai),
			du_chi.dinh_dang(ten.tong_tra)), ("g" if ten.trang_thai == du_chi.TT_DA_CHOT else "y")
	return "Đang chạy ở màn riêng", "g"


@frappe.whitelist()
def ds():
	"""Màn Cài đặt tự động hoá: mọi việc, cấu hình đang dùng, tình hình hôm nay."""
	_chan(QUYEN_XEM)
	ra = []
	for c in gop_cau_hinh(_doc_bang()):
		x = dict(c)
		x["mo_ta_han"] = mo_ta_han(c)
		try:
			x["tinh_hinh"], x["mau"] = _tinh_hinh(c)
		except Exception:
			x["tinh_hinh"], x["mau"] = "", "x"
		ra.append(x)
	return {"sua": 1 if _co_vai(QUYEN_SUA) else 0, "viec": ra, "bo_phan": list(BO_PHAN)}


@frappe.whitelist(methods=["POST"])
def luu(ma, bat=None, gio=None, han=None, han2=None, so_ngay_con=None, so_ngay_du=None):
	"""Ghi một việc: bật tắt, giờ chạy, hạn. Chỉ Giám đốc và Quản trị.

	Ghi thẳng vào dòng của bảng con rồi đẩy mốc sửa của trang Cài đặt, để ai
	đang mở trang đó trên Desk bấm Lưu sẽ bị báo trang đã đổi, không đè mất."""
	_chan(QUYEN_SUA)
	moi, loi = kiem_luu(ma, gio, han, han2, so_ngay_con, so_ngay_du)
	if loi:
		frappe.throw(loi)
	v = next(x for x in VIEC if x["ma"] == ma)
	if bat is not None and str(bat) != "":
		if v.get("chi_xem"):
			frappe.throw("Việc này chạy ở màn riêng, bật tắt ở đó.")
		moi["bat"] = 1 if cint(bat) else 0
	if not moi:
		return {"ok": 1}
	co = {d.get("ma"): d for d in _doc_bang()}
	if ma in co:
		frappe.db.set_value(BANG, co[ma]["name"], moi)
	else:
		dong = {"doctype": BANG, "parent": CAI_DAT, "parenttype": CAI_DAT, "parentfield": TRUONG_BANG,
			"idx": len(co) + 1, "ma": ma, "ten": v["ten"], "bo_phan": v["bo_phan"],
			"bat": cint(v.get("mac_dinh")), "gio": v.get("gio") or "", "han": v.get("han") or "",
			"han2": v.get("han2") or "", "so_ngay_con": cint(v.get("nguong")), "so_ngay_du": cint(v.get("du"))}
		dong.update(moi)
		frappe.get_doc(dong).db_insert()
	try:
		frappe.db.set_value(CAI_DAT, CAI_DAT, "modified", now_datetime(), update_modified=False)
		frappe.clear_document_cache(CAI_DAT, CAI_DAT)
	except Exception:
		pass
	return {"ok": 1, "viec": next(c for c in gop_cau_hinh(_doc_bang()) if c["ma"] == ma)}
