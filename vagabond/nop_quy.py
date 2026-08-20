# -*- coding: utf-8 -*-
"""Phiếu nộp quỹ tiền mặt: gom ca đã chốt, bảng kê mệnh giá, hai bên ký tay.

Nửa sau của luồng dòng tiền (nửa đầu là `ca_quay.py`). Cửa hàng trưởng gom
các ca đã chốt trong ngày, đếm tiền theo mệnh giá, ký tay trên màn hình,
mang tiền về; kế toán hoặc giám đốc đếm lại, ký nhận, phiếu khoá cứng và
các ca bên trong chuyển thành Đã nộp quỹ.

Vì sao kỳ vọng lấy theo số ĐẾM lúc chốt ca chứ không theo số máy
----------------------------------------------------------------
Tiền kỳ vọng của phiếu = tổng tiền mặt thu ngân ĐẾM ĐƯỢC lúc chốt các ca,
trừ tiền lẻ để lại cho ca sau. Không lấy theo doanh thu máy, vì lệch giữa
máy và số đếm đã bị bắt ở tầng CA kèm lý do rồi; tầng phiếu này chỉ hỏi
đúng một câu: số tiền đếm được lúc chốt có về tới quỹ nguyên vẹn không.
Trộn hai tầng là hết truy được lệch nằm ở khúc bán hàng hay khúc vận
chuyển tiền.

Chữ ký
------
Ký tay trên màn hình, lưu thẳng ảnh nét ký (data URL) vào phiếu. Nút ký
nhận chỉ dành cho vai kế toán và giám đốc, chặn ở MÁY CHỦ chứ không chỉ ẩn
nút: ẩn nút thì gọi thẳng API vẫn lọt. Ký nhận xong phiếu khoá cứng, kể cả
bảng mệnh giá, vì biên bản đã có chữ ký hai bên mà còn sửa được số là vô
nghĩa pháp lý.
"""

import base64
import json

import frappe
from frappe.utils import cint, flt, now_datetime, nowdate

from vagabond import ca_quay

NQ = "Vagabond Nop Quy"

TT_NHAP = "Nháp"
TT_CHO_KY = "Chờ ký nhận"
TT_DA_NOP = "Đã nộp quỹ"

NHAN_TRANG_THAI = {
	TT_NHAP: "Nháp",
	TT_CHO_KY: "Chờ ký nhận",
	TT_DA_NOP: "Đã nộp quỹ",
}

# Vai được ký NHẬN tiền. Bên giao là người lập phiếu, không cần vai riêng:
# ai đứng quầy cũng có thể phải mang tiền về quỹ.
VAI_KY_NHAN = {"System Manager", "Accounts Manager", "AP Kiểm soát (FIN)", "AP Giám đốc"}

# Mệnh giá tiền giấy đang lưu thông, từ lớn tới nhỏ. 200đ và 500đ bỏ ra
# ngoài: thực tế quầy bánh không cầm hai tờ đó, thêm vào chỉ làm bảng dài.
MENH_GIA = (500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000)

# Lệch bàn giao dưới mức này không bắt lý do, cùng ngưỡng với tầng ca.
NGUONG_LECH = ca_quay.NGUONG_LECH


# ============================================================ phép THUẦN


def doc_bang_ke(tho):
	"""Đọc bảng kê mệnh giá thành danh sách sạch. THUẦN.

	Nhận JSON dạng {"500000": 3, "200000": 1, ...} hoặc danh sách
	[{"menh_gia":..., "so_to":...}]. Mệnh giá lạ hay số tờ âm là gõ nhầm,
	chặn thẳng.
	"""
	if isinstance(tho, str):
		tho = json.loads(tho or "{}")
	if isinstance(tho, dict):
		tho = [{"menh_gia": k, "so_to": v} for k, v in tho.items()]
	ra = []
	for d in tho or []:
		mg = cint(d.get("menh_gia"))
		so = cint(d.get("so_to"))
		if mg not in MENH_GIA:
			raise ValueError("Mệnh giá %s không có trong bảng kê." % mg)
		if so < 0:
			raise ValueError("Số tờ của mệnh giá %s là số âm." % mg)
		if so == 0:
			continue
		ra.append({"menh_gia": mg, "so_to": so, "thanh_tien": float(mg * so)})
	ra.sort(key=lambda d: -d["menh_gia"])
	return ra


def tong_bang_ke(bang):
	"""Tổng tiền mặt thực nhận theo bảng kê. THUẦN."""
	return sum(flt(d.get("thanh_tien")) for d in bang or [])


def tinh_ky_vong(tien_dem_cac_ca, tien_le_giu_lai=0.0):
	"""Tiền kỳ vọng nộp = tổng tiền mặt đếm của các ca trừ tiền để lại. THUẦN."""
	tong = sum(flt(x) for x in tien_dem_cac_ca or [])
	giu = flt(tien_le_giu_lai)
	if giu < 0:
		raise ValueError("Tiền lẻ để lại không thể là số âm.")
	if giu > tong:
		raise ValueError("Tiền lẻ để lại (%s) nhiều hơn tổng tiền mặt của các ca (%s)." % (int(giu), int(tong)))
	return tong - giu


def can_ly_do(lech, nguong=NGUONG_LECH):
	"""Lệch bàn giao này có bắt buộc gõ lý do không. THUẦN."""
	return abs(flt(lech)) >= flt(nguong)


def duoc_ky_nhan(cac_vai):
	"""Người mang các vai này có được ký nhận tiền không. THUẦN."""
	return bool(VAI_KY_NHAN & set(cac_vai or []))


def la_chu_ky(anh):
	"""Chuỗi này có phải ảnh chữ ký data URL không. THUẦN.

	Chỉ nhận ảnh PNG hoặc JPEG nhúng thẳng. Không nhận đường dẫn hay chữ
	thường: chữ ký mà là text thì ai gõ hộ ai cũng được.
	"""
	a = (anh or "").strip()
	return a.startswith("data:image/png;base64,") or a.startswith("data:image/jpeg;base64,")


# ========================================================= chạm vào hệ


def _kiem_quyen():
	from vagabond.ban_hang import _kiem_quyen as kq

	kq()


@frappe.whitelist()
def ca_cho_nop(tu_ngay=None, den_ngay=None):
	"""Các ca đã chốt, chưa vào phiếu nào, để màn lập phiếu bày ra chọn."""
	_kiem_quyen()
	loc = {"trang_thai": ca_quay.TT_DA_CHOT, "phieu_nop": ["in", ["", None]]}
	if tu_ngay and den_ngay:
		loc["ngay"] = ["between", [tu_ngay, den_ngay]]
	ds = frappe.get_all(
		ca_quay.CA,
		filters=loc,
		fields=["name", "quay", "ngay", "mo_luc", "chot_luc", "tien_mat_dem",
			"tien_le_dau_ca", "tong_lech", "nguoi_chot"],
		order_by="chot_luc asc",
		limit_page_length=100,
	)
	return {"ds": ds}


@frappe.whitelist()
def tao(ds_ca, bang_ke, tien_le_giu_lai=0, ly_do_lech="", ghi_chu="", chu_ky_ben_giao=""):
	"""Lập phiếu nộp quỹ từ các ca đã chốt.

	`ds_ca` là JSON danh sách mã ca. `bang_ke` là JSON bảng mệnh giá. Có
	chữ ký bên giao thì phiếu vào thẳng Chờ ký nhận; chưa ký thì nằm Nháp.

	Mỗi ca chỉ vào được một phiếu: kiểm ở đây bằng ô `phieu_nop` trên ca,
	ghi ngay trong cùng giao dịch để hai người lập phiếu cùng lúc không
	gom trùng ca của nhau.
	"""
	_kiem_quyen()
	if isinstance(ds_ca, str):
		ds_ca = json.loads(ds_ca or "[]")
	ds_ca = [str(x).strip() for x in (ds_ca or []) if str(x).strip()]
	if not ds_ca:
		frappe.throw("Chưa chọn ca nào để nộp.")

	dong_ca = []
	for ma in ds_ca:
		d = frappe.db.get_value(
			ca_quay.CA, ma,
			["name", "quay", "ngay", "trang_thai", "tien_mat_dem", "phieu_nop"],
			as_dict=True,
		)
		if not d:
			frappe.throw("Không thấy ca %s." % ma)
		if d.trang_thai != ca_quay.TT_DA_CHOT:
			frappe.throw("Ca %s đang ở trạng thái %s, chỉ nộp được ca Đã chốt." % (ma, d.trang_thai))
		if (d.phieu_nop or "").strip():
			frappe.throw("Ca %s đã nằm trong phiếu %s rồi." % (ma, d.phieu_nop))
		dong_ca.append(d)

	try:
		bang = doc_bang_ke(bang_ke)
		ky_vong = tinh_ky_vong([d.tien_mat_dem for d in dong_ca], tien_le_giu_lai)
	except ValueError as e:
		frappe.throw(str(e))

	thuc_nhan = tong_bang_ke(bang)
	lech = thuc_nhan - ky_vong
	if can_ly_do(lech) and not (ly_do_lech or "").strip():
		return {
			"can_ly_do": 1,
			"ky_vong": ky_vong,
			"thuc_nhan": thuc_nhan,
			"lech": lech,
			"nhac": "Thực nhận lệch %s đồng so với kỳ vọng. Gõ lý do rồi lập lại." % int(lech),
		}

	co_ky = la_chu_ky(chu_ky_ben_giao)
	doc = frappe.get_doc({
		"doctype": NQ,
		"ngay": nowdate(),
		"trang_thai": TT_CHO_KY if co_ky else TT_NHAP,
		"nguoi_giao": frappe.session.user,
		"ten_nguoi_giao": frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user,
		"giao_luc": now_datetime() if co_ky else None,
		"chu_ky_ben_giao": chu_ky_ben_giao if co_ky else "",
		"tien_le_giu_lai": flt(tien_le_giu_lai),
		"tien_ky_vong": ky_vong,
		"tong_thuc_nhan": thuc_nhan,
		"lech": lech,
		"ly_do_lech": (ly_do_lech or "").strip(),
		"ghi_chu": (ghi_chu or "").strip(),
	})
	for d in dong_ca:
		doc.append("ca", {
			"ca": d.name, "quay": d.quay, "ngay": d.ngay,
			"tien_mat_dem": flt(d.tien_mat_dem),
		})
	for d in bang:
		doc.append("menh_gia", d)
	doc.insert(ignore_permissions=True)
	# Đóng dấu ca thuộc phiếu NGAY, trong cùng giao dịch với insert: hai
	# người cùng lập phiếu thì người sau vấp phải ô phieu_nop đã có.
	for d in dong_ca:
		frappe.db.set_value(ca_quay.CA, d.name, "phieu_nop", doc.name, update_modified=False)
	frappe.db.commit()
	return {"ma": doc.name, "trang_thai": doc.trang_thai, "ky_vong": ky_vong,
		"thuc_nhan": thuc_nhan, "lech": lech}


@frappe.whitelist()
def ky_giao(ma, chu_ky):
	"""Bên giao ký bổ sung cho phiếu còn Nháp."""
	_kiem_quyen()
	doc = frappe.get_doc(NQ, ma)
	if doc.trang_thai != TT_NHAP:
		frappe.throw("Phiếu đang ở trạng thái %s, không ký giao lại được." % doc.trang_thai)
	if not la_chu_ky(chu_ky):
		frappe.throw("Chữ ký không hợp lệ. Ký tay lại trên màn hình giúp em.")
	doc.chu_ky_ben_giao = chu_ky
	doc.giao_luc = now_datetime()
	doc.trang_thai = TT_CHO_KY
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ma": doc.name, "trang_thai": doc.trang_thai}


@frappe.whitelist()
def ky_nhan(ma, chu_ky):
	"""Kế toán hoặc giám đốc ký nhận tiền. Phiếu khoá cứng từ đây.

	Chặn vai ở máy chủ: ẩn nút trên màn chỉ là lịch sự, đây mới là cửa.
	"""
	if not duoc_ky_nhan(frappe.get_roles()):
		frappe.throw("Chỉ kế toán hoặc giám đốc được ký nhận tiền.")
	doc = frappe.get_doc(NQ, ma)
	if doc.trang_thai != TT_CHO_KY:
		frappe.throw("Phiếu đang ở trạng thái %s, chưa hoặc không còn chờ ký nhận." % doc.trang_thai)
	if not la_chu_ky(chu_ky):
		frappe.throw("Chữ ký không hợp lệ. Ký tay lại trên màn hình giúp em.")
	if frappe.session.user == doc.nguoi_giao:
		frappe.throw("Bên giao và bên nhận không được là cùng một người.")
	doc.chu_ky_ben_nhan = chu_ky
	doc.nguoi_nhan = frappe.session.user
	doc.ten_nguoi_nhan = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	doc.nhan_luc = now_datetime()
	doc.trang_thai = TT_DA_NOP
	doc.save(ignore_permissions=True)
	for d in doc.ca:
		frappe.db.set_value(ca_quay.CA, d.ca, "trang_thai", ca_quay.TT_DA_NOP, update_modified=False)
	frappe.db.commit()
	return {"ma": doc.name, "trang_thai": doc.trang_thai, "nhan_luc": str(doc.nhan_luc)}


def _dong_danh_sach(d):
	return {
		"name": d.name, "ngay": str(d.ngay), "trang_thai": d.trang_thai,
		"nguoi_giao": d.ten_nguoi_giao or d.nguoi_giao,
		"nguoi_nhan": d.ten_nguoi_nhan or d.nguoi_nhan or "",
		"tien_ky_vong": flt(d.tien_ky_vong), "tong_thuc_nhan": flt(d.tong_thuc_nhan),
		"lech": flt(d.lech), "so_ca": cint(d.get("so_ca")),
	}


def _loc_danh_sach(trang_thai=None, tu_ngay=None, den_ngay=None, tim=""):
	loc = {}
	if trang_thai:
		loc["trang_thai"] = trang_thai
	if tu_ngay and den_ngay:
		loc["ngay"] = ["between", [tu_ngay, den_ngay]]
	elif tu_ngay:
		loc["ngay"] = [">=", tu_ngay]
	return loc


@frappe.whitelist()
def danh_sach(trang_thai=None, tu_ngay=None, den_ngay=None, tim="", so_dong=200):
	"""Danh sách phiếu nộp quỹ, kèm số đếm cho chip trạng thái."""
	_kiem_quyen()
	ds = frappe.get_all(
		NQ,
		filters=_loc_danh_sach(trang_thai, tu_ngay, den_ngay),
		fields=["name", "ngay", "trang_thai", "nguoi_giao", "ten_nguoi_giao",
			"nguoi_nhan", "ten_nguoi_nhan", "tien_ky_vong", "tong_thuc_nhan", "lech"],
		order_by="creation desc",
		limit=cint(so_dong) or 200,
	)
	q = (tim or "").strip().lower()
	if q:
		ds = [d for d in ds if q in (
			(d.name or "") + " " + (d.ten_nguoi_giao or "") + " " + (d.nguoi_giao or "")
		).lower()]
	# Số ca của từng phiếu: một câu hỏi cho cả trang, không hỏi từng phiếu.
	so_ca = {}
	if ds:
		for r in frappe.get_all(
			"Vagabond Nop Quy Ca",
			filters={"parent": ["in", [d.name for d in ds]]},
			fields=["parent"],
			limit_page_length=0,
		):
			so_ca[r.parent] = so_ca.get(r.parent, 0) + 1
	for d in ds:
		d["so_ca"] = so_ca.get(d.name, 0)
	# Đếm chip trên TOÀN BỘ tập khớp ngày, không phải trang đang xem.
	dem = {"": 0}
	for r in frappe.get_all(
		NQ, filters=_loc_danh_sach(None, tu_ngay, den_ngay),
		fields=["trang_thai"], limit_page_length=0,
	):
		dem[r.trang_thai] = dem.get(r.trang_thai, 0) + 1
		dem[""] += 1
	return {"ds": [_dong_danh_sach(d) for d in ds], "dem": dem}


@frappe.whitelist()
def chi_tiet(ma):
	"""Một phiếu, đủ bảng mệnh giá, các ca, và hai chữ ký."""
	_kiem_quyen()
	doc = frappe.get_doc(NQ, ma)
	return {
		"ma": doc.name,
		"ngay": str(doc.ngay),
		"trang_thai": doc.trang_thai,
		"nguoi_giao": doc.nguoi_giao,
		"ten_nguoi_giao": doc.ten_nguoi_giao or doc.nguoi_giao,
		"giao_luc": str(doc.giao_luc or ""),
		"nguoi_nhan": doc.nguoi_nhan or "",
		"ten_nguoi_nhan": doc.ten_nguoi_nhan or "",
		"nhan_luc": str(doc.nhan_luc or ""),
		"tien_le_giu_lai": flt(doc.tien_le_giu_lai),
		"tien_ky_vong": flt(doc.tien_ky_vong),
		"tong_thuc_nhan": flt(doc.tong_thuc_nhan),
		"lech": flt(doc.lech),
		"ly_do_lech": doc.ly_do_lech or "",
		"ghi_chu": doc.ghi_chu or "",
		"co_ky_giao": 1 if (doc.chu_ky_ben_giao or "").strip() else 0,
		"co_ky_nhan": 1 if (doc.chu_ky_ben_nhan or "").strip() else 0,
		"chu_ky_ben_giao": doc.chu_ky_ben_giao or "",
		"chu_ky_ben_nhan": doc.chu_ky_ben_nhan or "",
		"duoc_ky_nhan": 1 if duoc_ky_nhan(frappe.get_roles()) else 0,
		"ca": [
			{"ca": d.ca, "quay": d.quay, "ngay": str(d.ngay), "tien_mat_dem": flt(d.tien_mat_dem)}
			for d in doc.ca
		],
		"menh_gia": [
			{"menh_gia": cint(d.menh_gia), "so_to": cint(d.so_to), "thanh_tien": flt(d.thanh_tien)}
			for d in doc.menh_gia
		],
	}


@frappe.whitelist()
def xuat_excel(trang_thai="", tu_ngay=None, den_ngay=None, tim="", so_dong=500):
	"""Danh sách phiếu nộp quỹ ra Excel, đúng bộ lọc đang xem trên màn."""
	_kiem_quyen()
	kq = danh_sach(trang_thai=trang_thai, tu_ngay=tu_ngay, den_ngay=den_ngay,
		tim=tim, so_dong=so_dong)
	rows = kq.get("ds") or []
	bang = [
		["PHIẾU NỘP QUỸ TIỀN MẶT"],
		["Xuất lúc", str(now_datetime())[:19],
			"Bộ lọc", NHAN_TRANG_THAI.get(trang_thai, "Tất cả") if trang_thai else "Tất cả",
			"Từ ngày", tu_ngay or "(không)", "Đến ngày", den_ngay or "(không)"],
		["Số phiếu", len(rows),
			"Tổng thực nhận", sum(flt(r.get("tong_thuc_nhan")) for r in rows),
			"Tổng lệch", sum(flt(r.get("lech")) for r in rows)],
		[],
		["Mã phiếu", "Ngày", "Trạng thái", "Số ca", "Bên giao", "Bên nhận",
			"Tiền kỳ vọng", "Thực nhận", "Lệch"],
	]
	for r in rows:
		bang.append([
			r.get("name") or "", r.get("ngay") or "",
			r.get("trang_thai") or "", cint(r.get("so_ca")),
			r.get("nguoi_giao") or "", r.get("nguoi_nhan") or "",
			flt(r.get("tien_ky_vong")), flt(r.get("tong_thuc_nhan")), flt(r.get("lech")),
		])
	from frappe.utils.xlsxutils import make_xlsx

	tep = make_xlsx(bang, "Nop quy tien mat")
	noi_dung = tep.getvalue() if hasattr(tep, "getvalue") else tep
	return {
		"ten_file": "nop-quy-tien-mat-%s.xlsx" % nowdate(),
		"b64": base64.b64encode(noi_dung).decode(),
		"so_dong": len(rows),
	}


# ================================================== BIÊN BẢN PDF


def _tien(n):
	"""1234567 thành 1.234.567 theo lối kế toán Việt Nam. THUẦN."""
	return "{:,.0f}".format(flt(n)).replace(",", ".")


def chu_so_tien(so):
	"""Đọc số tiền bằng chữ cho biên bản. THUẦN.

	`cong_no.py` có một bản y hệt, nhưng KHÔNG import từ đó: cong_no kéo
	ban_hang, ban_hang mở đầu bằng `import requests`, mà máy chạy CI của
	GitHub không cài gói ngoài nào - đầu workflow đã dặn bộ kiểm thử phải
	chạy tay không. Chính dây chuyền import đó đã làm đỏ 3 ca trên PR #2
	trong khi máy local xanh. Một hàm đọc số thì không có quyền kéo theo
	thư viện mạng.
	"""
	so = int(round(flt(so)))
	if so == 0:
		return "Không đồng"
	don_vi = ["", "nghìn", "triệu", "tỷ", "nghìn tỷ"]
	so_chu = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]

	def doc_ba(n, day_du):
		tram, chuc, dv = n // 100, (n // 10) % 10, n % 10
		ra = []
		if tram or day_du:
			ra.append(so_chu[tram] + " trăm")
		if chuc == 0 and dv and (tram or day_du):
			ra.append("lẻ")
		elif chuc == 1:
			ra.append("mười")
		elif chuc > 1:
			ra.append(so_chu[chuc] + " mươi")
		if dv:
			if chuc > 1 and dv == 1:
				ra.append("mốt")
			elif chuc >= 1 and dv == 5:
				ra.append("lăm")
			else:
				ra.append(so_chu[dv])
		return " ".join(x for x in ra if x)

	cum = []
	n = so
	while n > 0:
		cum.append(n % 1000)
		n //= 1000
	phan = []
	for i in range(len(cum) - 1, -1, -1):
		if cum[i] == 0:
			continue
		phan.append(doc_ba(cum[i], i != len(cum) - 1) + (" " + don_vi[i] if don_vi[i] else ""))
	ra = " ".join(phan).strip()
	return (ra[0].upper() + ra[1:] + " đồng") if ra else "Không đồng"


def _html_bien_ban(d):
	"""Dựng HTML biên bản bàn giao tiền mặt theo thể thức hành chính. THUẦN
	theo nghĩa chỉ đọc dict `d`, không hỏi thêm hệ.

	Thể thức: quốc hiệu tiêu ngữ giữa trang, tên biên bản in hoa, hai bên
	giao nhận, bảng kê mệnh giá, tổng bằng số và bằng chữ, hai chữ ký. Chữ
	"BÊN GIAO" trái "BÊN NHẬN" phải theo đúng lối biên bản hai bên.
	"""
	def ky(anh, ten, luc):
		o = ""
		if anh:
			o += "<img src='%s' style='height:64px;max-width:200px;object-fit:contain'><br>" % anh
		else:
			o += "<div style='height:64px'></div>"
		o += "<b>%s</b>" % (ten or "")
		if luc:
			o += "<br><span style='font-size:11px;color:#333'>Ký lúc %s</span>" % str(luc)[:16]
		return o

	dong_mg = ""
	for m in d.get("menh_gia") or []:
		dong_mg += (
			"<tr><td style='text-align:right'>%s</td>"
			"<td style='text-align:center'>%s</td>"
			"<td style='text-align:right'>%s</td></tr>"
			% (_tien(m["menh_gia"]), cint(m["so_to"]), _tien(m["thanh_tien"]))
		)
	dong_ca = ""
	for c in d.get("ca") or []:
		dong_ca += (
			"<tr><td>%s</td><td style='text-align:center'>%s</td>"
			"<td style='text-align:center'>%s</td>"
			"<td style='text-align:right'>%s</td></tr>"
			% (c["ca"], c["quay"], c["ngay"], _tien(c["tien_mat_dem"]))
		)

	lech = flt(d.get("lech"))
	khoi_lech = ""
	if abs(lech) >= 1:
		khoi_lech = (
			"<p style='margin:6px 0'>Chênh lệch so với kỳ vọng: <b>%s%s đồng</b> (%s)."
			" Lý do: %s</p>"
			% ("+" if lech > 0 else "-", _tien(abs(lech)),
				"thừa" if lech > 0 else "thiếu",
				frappe.utils.escape_html(d.get("ly_do_lech") or "(chưa ghi)"))
		)

	return """
<div style="font-family:'Times New Roman',Times,serif;font-size:13px;color:#000;line-height:1.55">
	<table style="width:100%%;border-collapse:collapse"><tr>
		<td style="width:42%%;text-align:center;vertical-align:top;font-size:12px">
			<b>THE VAGABOND P&Acirc;TISSERIE</b><br>Số: %(ma)s
		</td>
		<td style="text-align:center;vertical-align:top">
			<b>CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</b><br>
			<b>Độc lập - Tự do - Hạnh phúc</b><br>
			<span style="display:inline-block;border-top:1px solid #000;width:180px;margin-top:2px"></span>
		</td>
	</tr></table>
	<p style="text-align:right;font-style:italic;margin:10px 0 0">Ngày %(ngay_chu)s</p>
	<h2 style="text-align:center;margin:14px 0 4px;font-size:17px">BIÊN BẢN BÀN GIAO TIỀN MẶT</h2>
	<p style="text-align:center;margin:0 0 12px;font-style:italic">(Kèm bảng kê mệnh giá và danh sách ca làm việc)</p>

	<p style="margin:4px 0"><b>Bên giao (Bên A):</b> Ông/Bà %(ben_giao)s, đại diện cửa hàng.</p>
	<p style="margin:4px 0"><b>Bên nhận (Bên B):</b> Ông/Bà %(ben_nhan)s, đại diện kế toán/quỹ.</p>
	<p style="margin:10px 0 4px">Hai bên cùng kiểm đếm và bàn giao số tiền mặt thu tại quầy theo các ca làm việc sau:</p>

	<table style="width:100%%;border-collapse:collapse;margin:4px 0" border="1" cellpadding="5">
		<tr style="background:#f2f2f2"><th>Mã ca</th><th>Quầy</th><th>Ngày</th><th>Tiền mặt đếm lúc chốt (đ)</th></tr>
		%(dong_ca)s
	</table>
	<p style="margin:6px 0">Tiền lẻ để lại quầy cho ca sau: <b>%(giu_lai)s đồng</b>.
	Số tiền kỳ vọng bàn giao: <b>%(ky_vong)s đồng</b>.</p>

	<p style="margin:10px 0 4px"><b>Bảng kê mệnh giá thực nhận:</b></p>
	<table style="width:70%%;border-collapse:collapse;margin:4px 0" border="1" cellpadding="5">
		<tr style="background:#f2f2f2"><th>Mệnh giá (đ)</th><th>Số tờ</th><th>Thành tiền (đ)</th></tr>
		%(dong_mg)s
		<tr><td colspan="2" style="text-align:right"><b>Tổng cộng</b></td>
		<td style="text-align:right"><b>%(thuc_nhan)s</b></td></tr>
	</table>
	<p style="margin:6px 0">Tổng số tiền thực nhận (bằng số): <b>%(thuc_nhan)s đồng</b>.</p>
	<p style="margin:6px 0">Bằng chữ: <b><i>%(bang_chu)s</i></b>.</p>
	%(khoi_lech)s
	<p style="margin:10px 0 4px">Biên bản được lập khi hai bên đã cùng kiểm đếm, có giá trị làm chứng từ
	gốc cho việc ghi sổ quỹ tiền mặt. Bên nhận chịu trách nhiệm về số tiền kể từ thời điểm ký nhận.</p>

	<table style="width:100%%;border-collapse:collapse;margin-top:18px"><tr>
		<td style="width:50%%;text-align:center;vertical-align:top">
			<b>BÊN GIAO</b><br><span style="font-style:italic;font-size:11.5px">(Ký, ghi rõ họ tên)</span><br>%(ky_giao)s
		</td>
		<td style="text-align:center;vertical-align:top">
			<b>BÊN NHẬN</b><br><span style="font-style:italic;font-size:11.5px">(Ký, ghi rõ họ tên)</span><br>%(ky_nhan)s
		</td>
	</tr></table>
</div>""" % {
		"ma": d.get("ma") or "",
		"ngay_chu": _ngay_chu(d.get("ngay") or ""),
		"ben_giao": frappe.utils.escape_html(d.get("ten_nguoi_giao") or ""),
		"ben_nhan": frappe.utils.escape_html(d.get("ten_nguoi_nhan") or "................................"),
		"dong_ca": dong_ca or "<tr><td colspan='4' style='text-align:center'>(không có ca)</td></tr>",
		"giu_lai": _tien(d.get("tien_le_giu_lai")),
		"ky_vong": _tien(d.get("tien_ky_vong")),
		"dong_mg": dong_mg or "<tr><td colspan='3' style='text-align:center'>(trống)</td></tr>",
		"thuc_nhan": _tien(d.get("tong_thuc_nhan")),
		"bang_chu": chu_so_tien(d.get("tong_thuc_nhan")),
		"khoi_lech": khoi_lech,
		"ky_giao": ky(d.get("chu_ky_ben_giao"), d.get("ten_nguoi_giao"), d.get("giao_luc")),
		"ky_nhan": ky(d.get("chu_ky_ben_nhan"), d.get("ten_nguoi_nhan"), d.get("nhan_luc")),
	}


def _ngay_chu(ngay):
	"""2026-08-20 thành 'ngày 20 tháng 08 năm 2026'. THUẦN."""
	s = str(ngay or "")[:10]
	if len(s) == 10 and s[4] == "-":
		return "%s tháng %s năm %s" % (s[8:10], s[5:7], s[0:4])
	return s


@frappe.whitelist()
def xuat_pdf(ma):
	"""Tờ biên bản PDF khổ A4, trả về base64 cho app tải xuống."""
	_kiem_quyen()
	d = chi_tiet(ma)
	from frappe.utils.pdf import get_pdf

	khung = (
		"<html><head><meta charset='utf-8'>"
		"<style>@page{margin:16mm 15mm}body{margin:0}</style></head><body>"
		+ _html_bien_ban(d) + "</body></html>"
	)
	noi_dung = get_pdf(khung, options={"page-size": "A4", "orientation": "Portrait"})
	return {
		"ten_file": "Bien-ban-ban-giao-%s.pdf" % str(ma).replace("/", "-"),
		"b64": base64.b64encode(noi_dung).decode(),
		"kieu": "application/pdf",
	}
