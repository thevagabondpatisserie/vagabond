# -*- coding: utf-8 -*-
"""Màn Việc cần làm: gom việc đang chờ MỘT người, lọc theo vai ở MÁY CHỦ.

Anh Việt đặt bài 20/08/2026: *"Hiện tại màn hình này đang hiển thị sai đối
tượng (Kế toán đang phải nhìn thấy cả Phiếu nhập kho của Bếp/Kho). Em hãy
viết lại logic query để phiếu chỉ hiển thị đúng người, đúng bước."*

Vì sao chuyển hẳn về máy chủ
----------------------------
Bản cũ gom việc ngay trên máy khách bằng một loạt lời gọi `getList`, và phần
lớn KHÔNG lọc theo vai chút nào. Dòng lấy Phiếu nhập kho nháp chỉ có điều
kiện `docstatus: 0`, không một chữ nào về vai, nên chị Dung mở màn ra là
thấy nguyên phiếu kho của bếp.

Lọc theo vai mà đặt ở máy khách thì không phải là lọc, đó là trang trí: sửa
vài dòng trong công cụ nhà phát triển của trình duyệt là xem được việc của
người khác. Nên toàn bộ ma trận nằm ở đây, và màn hình chỉ vẽ lại thứ máy
chủ đã lọc.

Lớp Assignee (v243)
-------------------
Anh Việt còn yêu cầu *"mỗi phiếu sinh ra phải được gắn cho đúng một/một nhóm
Assignee cụ thể"*. Việc đó nằm ở `vagabond/giao_viec.py`, làm sau và deploy
riêng đúng như đã hẹn. Hai tệp phải nói CÙNG một câu: luật "ai phải làm"
bên đó soi đúng vào các bộ lọc dưới đây. Sửa một bên mà quên bên kia là để
màn Việc cần làm và ô Assigned To của Desk cãi nhau, và lúc đó không ai tin
cái nào nữa.
"""

import frappe
from frappe.utils import cint, getdate, nowdate

# ------------------------------------------------------------------ vai
#
# Tên vai lấy từ site thật, không bịa: kiểm ngày 19/08/2026 thì Uyên giữ
# "AP Officer", chị Dung giữ "AP Kiểm soát (FIN)", anh Việt và Dễ giữ
# "AP Giám đốc".
VAI_KE_TOAN = {"AP Kiểm soát (FIN)", "Accounts Manager", "Accounts User"}
VAI_THU_MUA = {"AP Officer", "Purchase User", "Purchase Manager", "Bộ phận đặt hàng"}
VAI_KHO = {"Stock User", "Stock Manager", "Kiểm kê viên", "Nhan hang dieu chuyen"}
VAI_GIAM_DOC = {"AP Giám đốc", "System Manager"}
from vagabond.vai_cua_hang import VAI_QLCH

VAI_QUAN_LY = {"Sales Manager", VAI_QLCH}

# Hai tập vai thêm 25/08/2026 cho luồng Tặng quà khách VIP.
#
# `VAI_SALES` lấy đúng bộ đã dùng nhất quán khắp repo (ban_hang.QUYEN_BAN_HANG,
# van_don.QUYEN_SALES, khuyen_mai.QUYEN_KM), không tự chế bộ mới: hai danh
# sách cho cùng một việc thì sớm muộn cũng lệch nhau, và người chịu là Sales.
VAI_SALES = {"Sales User", "Sales Manager", "Bộ phận đặt hàng"}

# Vai Marketing do MÃ NGUỒN dựng, xem vai_cua_hang.BANG_VAI. Trước 25/08/2026
# cả hệ KHÔNG có vai nào mang nghĩa Marketing, mà cột "Phụ trách" trong bảng
# tặng quà thì chỉ nhận đúng hai giá trị Sales và Marketing. Không có vai thì
# cả nhóm Marketing mở màn này ra sẽ thấy trống trơn mà không ai hiểu vì sao.
from vagabond.vai_cua_hang import VAI_MARKETING

VAI_MKT = {VAI_MARKETING}

# Loại phiếu. Khoá dùng cho chip, nhãn dùng để hiện.
#
# Thứ tự ở đây CHÍNH LÀ thứ tự chip trên màn: việc gấp và việc tiền đứng
# trước, việc giấy tờ đứng sau.
LOAI_PHIEU = (
	("chuyen_kho", "Chuyển kho", "📦"),
	("san_xuat", "Yêu cầu sản xuất", "🎂"),
	("nhap_kho", "Nhập kho", "📥"),
	("xuat_kho", "Xuất kho", "📤"),
	("kiem_ke", "Kiểm kê", "🧮"),
	("tang_qua", "Tặng quà khách VIP", "🎁"),
	("ycmh", "Yêu cầu mua hàng", "🛒"),
	("de_nghi_chi", "Đề nghị chi", "🧾"),
	("hoan_tien", "Hoàn tiền", "💸"),
	("ho_so_tt", "Hồ sơ thanh toán", "🏦"),
	("don_mua", "Đơn mua quá hẹn", "⚠️"),
)

# ==================================================== MA TRẬN PHÂN LUỒNG
#
# Anh Việt chốt 20/08/2026. Mỗi loại phiếu khai rõ nhóm vai nào được thấy.
# Ai không thuộc nhóm nào thì không thấy loại đó, chấm hết.
#
# Đọc bảng này là đọc được cả chính sách, không phải lần mò trong mã.
MA_TRAN = {
	# Kho và bếp: việc hàng hoá.
	"chuyen_kho": VAI_KHO | VAI_QUAN_LY | VAI_GIAM_DOC,
	"san_xuat": VAI_KHO | VAI_GIAM_DOC,
	"nhap_kho": VAI_KHO | VAI_THU_MUA | VAI_GIAM_DOC,
	"xuat_kho": VAI_KHO | VAI_GIAM_DOC,
	# Kiểm kê chờ CHỐT SỔ là bước giá trị, nên kế toán có phần ở đây. Đây là
	# ngoại lệ DUY NHẤT cho phép kế toán thấy phiếu kho, đúng như anh Việt
	# dặn: "trừ khi có bước chờ Kế toán duyệt giá trị".
	"kiem_ke": VAI_KHO | VAI_KE_TOAN | VAI_GIAM_DOC,
	# CRM. Tặng quà khách VIP là việc của Sales và Marketing, kho và bếp
	# KHÔNG thấy: danh sách này có số điện thoại riêng của khách VIP.
	"tang_qua": VAI_SALES | VAI_MKT | VAI_QUAN_LY | VAI_GIAM_DOC,
	# Thu mua.
	"ycmh": VAI_THU_MUA | VAI_GIAM_DOC,
	"don_mua": VAI_THU_MUA | VAI_GIAM_DOC,
	# Tiền. Kho và bếp KHÔNG thấy.
	"de_nghi_chi": VAI_THU_MUA | VAI_KE_TOAN | VAI_GIAM_DOC,
	"hoan_tien": VAI_KE_TOAN | VAI_GIAM_DOC,
	"ho_so_tt": VAI_KE_TOAN | VAI_THU_MUA | VAI_GIAM_DOC,
}


def vai_cua(nguoi=None):
	return set(frappe.get_roles(nguoi or frappe.session.user))


def thay_duoc(loai, vai):
	"""Người mang bộ vai này có thấy loại phiếu kia không. THUẦN.

	Vai không nằm trong ma trận thì KHÔNG thấy. Mặc định là đóng chứ không
	phải mở: thêm một loại phiếu mới mà quên khai vai thì nó ẩn với mọi
	người, chứ không hiện ra với cả tiệm.
	"""
	can = MA_TRAN.get(loai)
	if not can:
		return False
	return bool(set(vai or []) & can)


def _tre(ngay):
	"""Quá hẹn chưa. THUẦN."""
	if not ngay:
		return False
	try:
		return getdate(ngay) < getdate(nowdate())
	except Exception:
		return False


# ------------------------------------------------------- người này giữ kho nào
def _kho_cua(nguoi=None):
	"""Kho mà người này phụ trách. Rỗng nghĩa là không giữ kho nào.

	Đọc từ ĐÚNG trường màn hình cũ đã đọc (`custom_kho_phu_trach` trên User,
	là chuỗi các kho cách nhau bằng dấu phẩy), để không đẻ ra luật thứ hai.
	"""
	try:
		v = frappe.db.get_value("User", nguoi or frappe.session.user, "custom_kho_phu_trach")
		return [x.strip() for x in str(v or "").split(",") if x.strip()]
	except Exception:
		return []


def _bo_phan(nguoi=None):
	"""Bộ phận của người này, cũng đọc đúng trường màn hình cũ đọc."""
	try:
		u = frappe.db.get_value(
			"User", nguoi or frappe.session.user,
			["custom_phong_ban", "custom_bo_phan"], as_dict=True,
		) or {}
		return (u.get("custom_phong_ban") or u.get("custom_bo_phan") or "").strip()
	except Exception:
		return ""


# ======================================================== các nguồn việc
#
# Mỗi hàm trả về danh sách việc của MỘT loại phiếu. Hàm nào lỗi thì bỏ qua
# loại đó chứ không làm sập cả màn: người ta mở màn Việc cần làm là để làm
# việc, mất một nhóm còn hơn trắng màn hình.


def _viec_chuyen_kho(vai, kho):
	ra = []
	loc = {
		"material_request_type": "Material Transfer",
		"docstatus": 1,
		"status": ["in", ["Pending", "Partially Ordered"]],
	}
	# Kho mình giữ thì phải SOẠN hàng. Không giữ kho nào thì không có việc
	# soạn, chứ không phải thấy hết mọi kho.
	if kho:
		l2 = dict(loc)
		l2["set_from_warehouse"] = ["in", kho]
		for x in frappe.get_all(
			"Material Request", filters=l2,
			fields=["name", "set_from_warehouse", "set_warehouse", "schedule_date"],
			order_by="schedule_date asc", limit_page_length=60,
		):
			ra.append({
				"loai": "chuyen_kho", "ma": x["name"],
				"nhom": "Kho bạn giữ phải soạn hàng",
				"phu": "%s → %s" % (x.get("set_from_warehouse") or "", x.get("set_warehouse") or ""),
				"ngay": str(x.get("schedule_date") or ""),
				"tt": "tre_hen" if _tre(x.get("schedule_date")) else "cho_soan",
			})
		l3 = dict(loc)
		l3["set_warehouse"] = ["in", kho]
		da = {r["ma"] for r in ra}
		for x in frappe.get_all(
			"Material Request", filters=l3,
			fields=["name", "set_from_warehouse", "set_warehouse", "schedule_date", "per_ordered"],
			order_by="schedule_date asc", limit_page_length=60,
		):
			if x["name"] in da or not (x.get("per_ordered") or 0) > 0:
				continue
			ra.append({
				"loai": "chuyen_kho", "ma": x["name"],
				"nhom": "Hàng đã chuyển, chờ bạn xác nhận nhận",
				"phu": "%s → %s" % (x.get("set_from_warehouse") or "", x.get("set_warehouse") or ""),
				"ngay": str(x.get("schedule_date") or ""),
				"tt": "cho_nhan",
			})
	return ra


def _viec_san_xuat(vai, bo_phan):
	if not bo_phan or not bo_phan.startswith("Bếp"):
		return []
	ra = []
	for x in frappe.get_all(
		"Material Request",
		filters={
			"material_request_type": "Manufacture", "docstatus": 1,
			"status": ["in", ["Pending", "Partially Ordered"]],
			"custom_bep_nhan": bo_phan,
		},
		fields=["name", "schedule_date", "bo_phan_yeu_cau"],
		order_by="schedule_date asc", limit_page_length=60,
	):
		ra.append({
			"loai": "san_xuat", "ma": x["name"], "nhom": "Bếp bạn phải làm",
			"phu": x.get("bo_phan_yeu_cau") or "", "ngay": str(x.get("schedule_date") or ""),
			"tt": "tre_hen" if _tre(x.get("schedule_date")) else "cho_lam",
		})
	return ra


def _viec_nhap_kho(vai, kho):
	ra = []
	for x in frappe.get_all(
		"Purchase Receipt", filters={"docstatus": 0},
		fields=["name", "supplier_name", "posting_date", "set_warehouse"],
		order_by="posting_date asc", limit_page_length=60,
	):
		# Lọc theo kho mình giữ. Bản cũ KHÔNG có dòng này, nên ai mở màn
		# cũng thấy toàn bộ phiếu nhập nháp của cả tiệm - đúng chỗ anh Việt
		# kêu. Người giữ kho thì thấy kho mình; thu mua và giám đốc thấy hết.
		if kho and (vai & VAI_KHO) and not (vai & (VAI_THU_MUA | VAI_GIAM_DOC)):
			if x.get("set_warehouse") and x["set_warehouse"] not in kho:
				continue
		ra.append({
			"loai": "nhap_kho", "ma": x["name"], "nhom": "Phiếu nhập kho chờ đếm hàng",
			"phu": x.get("supplier_name") or "", "ngay": str(x.get("posting_date") or ""),
			"tt": "cho_nhan",
		})
	return ra


def _viec_xuat_kho(vai, kho, nguoi):
	ra = []
	for x in frappe.get_all(
		"Stock Entry",
		filters={"docstatus": 0, "purpose": ["in", ["Material Transfer", "Material Issue"]]},
		fields=["name", "from_warehouse", "to_warehouse", "posting_date", "owner"],
		order_by="creation desc", limit_page_length=60,
	):
		cua_toi = x.get("owner") == nguoi or (kho and x.get("from_warehouse") in kho)
		if not cua_toi:
			continue
		ra.append({
			"loai": "xuat_kho", "ma": x["name"], "nhom": "Phiếu xuất nháp chờ ghi sổ",
			"phu": "%s → %s" % (x.get("from_warehouse") or "", x.get("to_warehouse") or ""),
			"ngay": str(x.get("posting_date") or ""), "tt": "ban_nhap",
		})
	return ra


def _viec_kiem_ke(vai):
	ra = []
	for x in frappe.get_all(
		"Phieu Kiem Ke", filters={"trang_thai": "Chờ duyệt"},
		fields=["name", "kho", "ngay_kiem"], order_by="ngay_kiem asc", limit_page_length=40,
	):
		ra.append({
			"loai": "kiem_ke", "ma": x["name"], "nhom": "Phiếu kiểm kê chờ chốt sổ",
			"phu": x.get("kho") or "", "ngay": str(x.get("ngay_kiem") or ""), "tt": "cho_duyet",
		})
	return ra


def _viec_de_nghi_chi(vai):
	"""Đề nghị chi, CHỈ những bước đúng vai người đang xem.

	Thu mua thấy bước chờ mua hàng duyệt. Kế toán thấy bước chờ kế toán.
	Giám đốc thấy bước chờ giám đốc. Không ai phải lội qua bước của người
	khác.
	"""
	from vagabond import de_nghi_chi as dn

	buoc = []
	if vai & VAI_THU_MUA or vai & VAI_GIAM_DOC:
		buoc.append(dn.TT_CHO_DUYET)
	if vai & VAI_GIAM_DOC:
		buoc.append(dn.TT_CHO_GIAM_DOC)
	if vai & VAI_KE_TOAN or vai & VAI_GIAM_DOC:
		buoc.append(dn.TT_CHO_KE_TOAN)
	if not buoc:
		return []
	ra = []
	for x in frappe.get_all(
		dn.DT, filters={"trang_thai": ["in", buoc]},
		fields=["name", "ten_khoan_chi", "tong_tien", "so_tien", "trang_thai", "ngay_can_tt"],
		order_by="ngay_can_tt asc", limit_page_length=60,
	):
		ra.append({
			"loai": "de_nghi_chi", "ma": x["name"],
			"nhom": dn.NHAN_TRANG_THAI.get(x["trang_thai"]) or x["trang_thai"],
			"phu": x.get("ten_khoan_chi") or "",
			"tien": float(x.get("tong_tien") or x.get("so_tien") or 0),
			"ngay": str(x.get("ngay_can_tt") or ""),
			"tt": "tre_hen" if _tre(x.get("ngay_can_tt")) else "cho_duyet",
		})
	return ra


def _viec_hoan_tien(vai):
	from vagabond import hoan_tien as ht

	ra = []
	for x in frappe.get_all(
		ht.DT, filters={"trang_thai": ["in", ["Cho chi", "Da doi soat"]]},
		fields=["name", "khach", "so_tien", "trang_thai", "creation"],
		order_by="creation asc", limit_page_length=60,
	):
		ra.append({
			"loai": "hoan_tien", "ma": x["name"],
			"nhom": "Phiếu hoàn tiền chờ chi" if x["trang_thai"] == "Cho chi"
			else "Phiếu hoàn tiền chờ kết thúc",
			"phu": x.get("khach") or "", "tien": float(x.get("so_tien") or 0),
			"ngay": str(x.get("creation") or "")[:10],
			"tt": "cho_chi" if x["trang_thai"] == "Cho chi" else "cho_ket_thuc",
		})
	return ra


def _viec_don_mua(vai):
	ra = []
	for x in frappe.get_all(
		"Purchase Order",
		filters={
			"docstatus": 1, "status": ["not in", ["Closed", "Completed"]],
			"schedule_date": ["<", nowdate()],
		},
		fields=["name", "supplier_name", "schedule_date", "trang_thai_pnk"],
		order_by="schedule_date asc", limit_page_length=30,
	):
		if (x.get("trang_thai_pnk") or "") == "Đã nhập đủ":
			continue
		ra.append({
			"loai": "don_mua", "ma": x["name"], "nhom": "Đơn mua quá hẹn chưa nhập đủ",
			"phu": x.get("supplier_name") or "", "ngay": str(x.get("schedule_date") or ""),
			"tt": "qua_han",
		})
	return ra


def _viec_tang_qua(vai, nguoi):
	"""Phiếu tặng quà khách VIP đang chờ người này.

	Gom theo ĐÚNG hai trục trạng thái, thành hai nhóm việc riêng: chưa ai
	gọi, và đã gọi rồi mà quà chưa đi. Hai trục chạy độc lập nên KHÔNG có
	luật "phải liên hệ xong mới được tặng" - dữ liệu thật đã có dòng tặng
	rồi mà chưa từng liên hệ, và ngược lại.

	Chỉ lấy phiếu của đợt ĐANG CHẠY. Đợt đã đóng mà còn hiện lên là mỗi mùa
	sau lại đội thêm một lớp việc chết không ai dọn.
	"""
	from vagabond.tang_qua import DT, DT_DOT

	dang_chay = frappe.get_all(
		DT_DOT, filters={"trang_thai_dot": "Dang chay"},
		fields=["name", "ten_dot", "den_ngay"], limit_page_length=0)
	if not dang_chay:
		return []
	ten_dot = {d["name"]: d["ten_dot"] for d in dang_chay}
	han_dot = {d["name"]: d["den_ngay"] for d in dang_chay}

	# Ai thấy được gì. Theo quyết định anh Việt chốt 25/08/2026 cho câu hỏi
	# khách lẻ không gán người phụ trách: phiếu VÔ CHỦ dồn về Sales Manager
	# chứ không rơi vào khoảng không.
	rong_tam_mat = bool(vai & (VAI_QUAN_LY | VAI_GIAM_DOC))

	ra = []
	for x in frappe.get_all(
		DT,
		filters={"dot": ["in", list(ten_dot)], "huy": 0},
		fields=["name", "dot", "ten_khach", "don_vi", "phan_loai",
			"khach_cua", "nguoi_lam", "bo_phan_lam",
			"tt_tang", "tt_lien_he", "canh_bao_sdt"],
		order_by="modified asc", limit_page_length=200,
	):
		cua_minh = nguoi in (x.get("khach_cua"), x.get("nguoi_lam"))
		vo_chu = not (x.get("khach_cua") or x.get("nguoi_lam"))
		if not rong_tam_mat and not cua_minh:
			# Người thường chỉ thấy phiếu của mình. Phiếu vô chủ chỉ hiện
			# với quản lý, đúng như quyết định ở trên.
			continue

		if x["tt_lien_he"] != "Da lien he":
			tt = "tre_hen" if _tre(han_dot.get(x["dot"])) else "chua_lien_he"
			nhom = "Khách VIP chưa ai liên hệ"
		elif x["tt_tang"] != "Da tang":
			tt = "tre_hen" if _tre(han_dot.get(x["dot"])) else "chua_tang"
			nhom = "Đã liên hệ, quà chưa đi"
		else:
			continue

		phu = " - ".join(p for p in (x.get("don_vi"), x.get("phan_loai")) if p)
		if vo_chu and rong_tam_mat:
			phu = (phu + " - chưa gán người phụ trách").strip(" -")
		ra.append({
			"loai": "tang_qua", "ma": x["name"],
			"nhom": "%s (%s)" % (nhom, ten_dot.get(x["dot"], x["dot"])),
			"phu": "%s%s" % (x.get("ten_khach") or "",
				(" - " + phu) if phu else ""),
			"ngay": str(han_dot.get(x["dot"]) or ""),
			"tt": tt,
		})
	return ra


NHAN_TT = {
	"cho_nhan": "chờ nhận", "cho_soan": "chờ soạn", "tre_hen": "trễ hẹn",
	"cho_lam": "chờ làm", "ban_nhap": "bản nháp", "cho_duyet": "chờ duyệt",
	"cho_chi": "chờ chi", "cho_ket_thuc": "chờ kết thúc", "qua_han": "quá hẹn",
	"chua_lien_he": "chưa liên hệ", "chua_tang": "chưa tặng",
}
MAU_TT = {
	"tre_hen": "#c0392b", "qua_han": "#c0392b", "cho_soan": "#c77700",
	"cho_duyet": "#c77700", "cho_nhan": "#0a8f9e", "cho_lam": "#7a4bbf",
	"ban_nhap": "#8a8f98", "cho_chi": "#b3261e", "cho_ket_thuc": "#0a8a4a",
	"chua_lien_he": "#c77700", "chua_tang": "#7a4bbf",
}


@frappe.whitelist()
def danh_sach(loai="", trang_thai=""):
	"""Việc đang chờ NGƯỜI ĐANG ĐĂNG NHẬP, đã lọc theo ma trận phân luồng."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	nguoi = frappe.session.user
	vai = vai_cua(nguoi)
	kho = _kho_cua(nguoi)
	bp = _bo_phan(nguoi)

	nguon = [
		("chuyen_kho", lambda: _viec_chuyen_kho(vai, kho)),
		("san_xuat", lambda: _viec_san_xuat(vai, bp)),
		("nhap_kho", lambda: _viec_nhap_kho(vai, kho)),
		("xuat_kho", lambda: _viec_xuat_kho(vai, kho, nguoi)),
		("kiem_ke", lambda: _viec_kiem_ke(vai)),
		("de_nghi_chi", lambda: _viec_de_nghi_chi(vai)),
		("hoan_tien", lambda: _viec_hoan_tien(vai)),
		("don_mua", lambda: _viec_don_mua(vai)),
		("tang_qua", lambda: _viec_tang_qua(vai, nguoi)),
	]

	tat_ca = []
	for ma_loai, fn in nguon:
		# CỔNG DUY NHẤT. Không thấy loại này thì không chạy luôn truy vấn,
		# vừa đúng vừa đỡ tốn.
		if not thay_duoc(ma_loai, vai):
			continue
		try:
			tat_ca.extend(fn() or [])
		except Exception:
			frappe.log_error(frappe.get_traceback(), "viec_can_lam: gom %s loi" % ma_loai)

	dich_danh = _giao_dich_danh(nguoi)
	for v in tat_ca:
		v["nhan_tt"] = NHAN_TT.get(v.get("tt"), v.get("tt") or "")
		v["mau"] = MAU_TT.get(v.get("tt"), "#8a8f98")
		# Dòng nào máy đã GIAO đích danh cho người này thì đánh dấu, để tách
		# khỏi những dòng chỉ hiện ra vì họ có vai đó. Hai chuyện khác nhau:
		# "việc của bộ phận tôi" và "việc giao cho tôi".
		v["cua_toi"] = 1 if v.get("ma") in dich_danh else 0

	# Đếm chip TRƯỚC khi lọc, để con số trên chip là số thật của cả sổ chứ
	# không phải số dòng đang hiện.
	dem_loai, dem_tt = {}, {}
	for v in tat_ca:
		dem_loai[v["loai"]] = dem_loai.get(v["loai"], 0) + 1
	loai = (loai or "").strip()
	trong_loai = [v for v in tat_ca if not loai or v["loai"] == loai]
	for v in trong_loai:
		dem_tt[v["tt"]] = dem_tt.get(v["tt"], 0) + 1

	tt = (trang_thai or "").strip()
	hien = [v for v in trong_loai if not tt or v["tt"] == tt]
	# Việc trễ hẹn lên đầu, rồi tới hạn gần nhất.
	hien.sort(key=lambda v: (0 if v.get("tt") in ("tre_hen", "qua_han") else 1, v.get("ngay") or "9"))

	return {
		"ds": hien,
		"tong": len(tat_ca),
		"dem_loai": dem_loai,
		"dem_trang_thai": dem_tt,
		"loai": loai,
		"trang_thai": tt,
		# Chỉ trả về chip của loại người này ĐƯỢC THẤY. Bày ra chip rồi bấm
		# vào không có gì là một cách nói dối nhẹ nhàng.
		"chip_loai": [
			{"k": k, "ten": t, "ic": i}
			for k, t, i in LOAI_PHIEU if thay_duoc(k, vai) and dem_loai.get(k)
		],
		"chip_trang_thai": [
			{"k": k, "ten": NHAN_TT.get(k, k)} for k in
			sorted(dem_tt.keys(), key=lambda x: (0 if x in ("tre_hen", "qua_han") else 1, x))
		],
		"vai_chinh": _ten_vai(vai),
		"so_dich_danh": sum(1 for v in tat_ca if v.get("cua_toi")),
	}


def _giao_dich_danh(nguoi):
	"""Mã phiếu đang được GIAO đích danh cho người này (ToDo còn mở).

	Một truy vấn cho cả màn, không phải một truy vấn cho mỗi dòng.
	"""
	try:
		return {
			t["reference_name"]
			for t in frappe.get_all(
				"ToDo",
				filters={"allocated_to": nguoi, "status": "Open"},
				fields=["reference_name"],
				limit_page_length=0,
			)
			if t.get("reference_name")
		}
	except Exception:
		return set()


def _ten_vai(vai):
	"""Một chữ mô tả người này đang đứng ở vai nào, để màn hình nói cho họ biết."""
	if vai & VAI_GIAM_DOC:
		return "Giám đốc"
	if vai & VAI_KE_TOAN:
		return "Kế toán"
	if vai & VAI_THU_MUA:
		return "Thu mua"
	if vai & VAI_KHO:
		return "Kho và bếp"
	if vai & VAI_QUAN_LY:
		return "Quản lý cửa hàng"
	return "Nhân viên"
