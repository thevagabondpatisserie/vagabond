# -*- coding: utf-8 -*-
"""Quan ly nguoi dung va quyen, lam tren app cho anh Viet, chi Dung va De.

Anh Viet 14/08/2026: "ma tran quyen cua em lam cung hoi roi, anh hy vong em
co the lam no mot cach de thao tac nhat co the".

Vi sao khong bay thang ma tran vai tro cua Frappe ra app: site nay co 40 vai
tro dang bat, trong do 25 vai la cua ERPNext ma tiem khong dung toi. Doc mot
bang 40 dong roi tu tick la viec cua nguoi quen he thong, khong phai viec
cua nguoi quan ly cua hang.

Cach lam o day: GOI CHUC VU. Moi goi la mot cum vai tro da chon san theo dung
cong viec that o tiem (Ban hang, Bep, Kho, Ke toan, Giam doc...). Gan nguoi
vao goi la xong, khong phai biet "Stock Manager" la gi. Ai can khac goi thi
mo phan chi tiet ra chinh le tung vai.

Nguyen tac an toan:
  - Chi dong vao cac vai NAM TRONG goi (VAI_QUAN_LY). Vai nao khong thuoc goi
    nao thi khong bao gio bi go, du nguoi do doi goi. Nho vay khong lam mat
    cac vai dac biet ai do da gan tay tren desk.
  - Chi System Manager moi cap hay go duoc System Manager. Nguoi co quyen
    quan ly nguoi dung ma khong phai System Manager thi khong tu nang minh
    len duoc.
  - Khong ai tu tat tai khoan cua chinh minh.
"""

import json

import frappe

from vagabond.quyen_phan_he import ROLE_GIAM_DOC, ROLE_THU_MUA

from frappe.utils import cint, now_datetime

from vagabond.nhan_su import link_app, thu_moi_html, _lien_ket_dat_mat_khau

VAI_QUAN_TRI = "System Manager"
VAI_QLND = "Quản lý người dùng"

BO_QUA_USER = {"Administrator", "Guest"}

# Vai he thong Frappe tu gan cho ai cung co, khong phai quyen nghiep vu nen
# khong bay ra man hinh cho roi mat.
VAI_NEN = {
	"All", "Guest", "Desk User", "Blogger", "Newsletter Manager", "Inbox User",
	"Prepared Report User", "Script Manager", "Dashboard Manager", "Report Manager",
	"Knowledge Base Contributor", "Knowledge Base Editor", "Website Manager",
	"Workspace Manager", "Translator", "Employee Self Service",
}


# Goi chuc vu. Thu tu o day la thu tu hien tren app: viec nhieu nguoi lam
# nhat len truoc, quyen nang nhat xuong duoi.
GOI = [
	{
		"k": "sales",
		"bac": 2,
		"ten": "Bán hàng (Sales)",
		"icon": "🎂",
		"mo_ta": "Nhận đơn, lên vận đơn, đối soát COD cuối ngày, tra cứu khách hàng.",
		"lam_duoc": [
			"Tạo đơn và sửa đơn trong ngày",
			"Lên vận đơn, gán shipper, đối soát COD",
			"Xem và sửa hồ sơ khách hàng",
			"Đặt hàng nguyên vật liệu, nhận hàng điều chuyển, kiểm kê",
		],
		"vai": ["Sales User", "Bộ phận đặt hàng", "Nhan hang dieu chuyen", "Kiểm kê viên"],
	},
	{
		"k": "salesql",
		"bac": 4,
		"ten": "Quản lý bán hàng",
		"icon": "👑",
		"mo_ta": "Như Bán hàng, thêm quyền sửa đơn ngày cũ, khuyến mãi và xem báo cáo.",
		"lam_duoc": [
			"Mọi quyền của Bán hàng",
			"Sửa hoặc huỷ đơn của ngày đã qua",
			"Tạo và tắt chương trình khuyến mãi, voucher",
			"Xem toàn bộ phân hệ Báo cáo",
		],
		"vai": [
			"Sales Manager", "Sales User", "Bộ phận đặt hàng", "Nhan hang dieu chuyen",
			"Kiểm kê viên", "VGB - Quản lý khuyến mãi", "Vagabond Bao cao",
		],
	},
	{
		"k": "bep",
		"bac": 2,
		"ten": "Bếp và Sản xuất",
		"icon": "🧑‍🍳",
		"mo_ta": "Lệnh sản xuất, bán thành phẩm, kiểm bánh, đặt nguyên liệu.",
		"lam_duoc": [
			"Nhận và chốt lệnh sản xuất, ghi bán thành phẩm",
			"Kiểm bánh cuối ngày",
			"Đặt hàng nguyên vật liệu",
			"Đếm kiểm kê",
		],
		"vai": ["Manufacturing User", "Bếp phó", "Bộ phận đặt hàng", "Kiểm kê viên"],
	},
	{
		"k": "kho",
		"bac": 2,
		"ten": "Kho và Nhận hàng",
		"icon": "📦",
		"mo_ta": "Nhận hàng điều chuyển, đếm kiểm kê, đặt hàng.",
		"lam_duoc": [
			"Nhận hàng điều chuyển giữa các kho",
			"Đếm kiểm kê",
			"Đặt hàng nguyên vật liệu",
		],
		"vai": ["Nhan hang dieu chuyen", "Bộ phận đặt hàng", "Kiểm kê viên"],
	},
	{
		"k": "khoql",
		"bac": 4,
		"ten": "Quản lý kho",
		"icon": "🏷️",
		"mo_ta": "Như Kho, thêm quyền duyệt phiếu xuất và chốt kiểm kê.",
		"lam_duoc": [
			"Mọi quyền của Kho và Nhận hàng",
			"Duyệt phiếu xuất huỷ và xuất điều chuyển",
			"Chốt phiếu kiểm kê, lệch tồn ghi vào sổ",
			"Tra tồn kho mọi kho",
		],
		"vai": [
			"Stock Manager", "Stock User", "Nhan hang dieu chuyen",
			"Bộ phận đặt hàng", "Kiểm kê viên",
		],
	},
	{
		"k": "shipper",
		"bac": 1,
		"ten": "Shipper",
		"icon": "🛵",
		"mo_ta": "Chỉ thấy tuyến giao của mình, xác nhận giao và tiền thu hộ.",
		"lam_duoc": [
			"Xem tuyến giao được phân cho mình",
			"Chụp ảnh giao hàng, xác nhận đã giao",
			"Khai tiền thu hộ và chi phí xăng xe",
		],
		"vai": ["Shipper"],
	},
	{
		"k": "muahang",
		"bac": 3,
		"ten": "Thu mua",
		"icon": "🛒",
		"mo_ta": "Đơn đặt hàng, danh mục nhà cung cấp, hoá đơn mua, lập hồ sơ thanh toán.",
		"lam_duoc": [
			"Gom yêu cầu thành đơn đặt hàng nhà cung cấp",
			"Quản lý danh mục nhà cung cấp và gán nhà cung cấp cho mặt hàng",
			"Đối chiếu hoá đơn mua với phiếu nhập kho",
			"Lập hồ sơ thanh toán (APP) gửi kế toán duyệt",
		],
		"vai": [
			ROLE_THU_MUA, "Purchase User", "Bộ phận đặt hàng", "Mua hàng R&D",
			"Kiểm kê viên",
		],
	},
	{
		"k": "ketoan",
		"bac": 5,
		"ten": "Kế toán",
		"icon": "🧮",
		"mo_ta": "Hồ sơ thanh toán, công nợ, đối soát, hoá đơn điện tử, báo cáo.",
		"lam_duoc": [
			"Duyệt hồ sơ thanh toán ở cấp kế toán",
			"Lập hồ sơ thanh toán, hồ sơ hoàn ứng",
			"Xem công nợ phải thu và phải trả, đối soát SePay",
			"Xem toàn bộ phân hệ Báo cáo",
		],
		"vai": [
			"Accounts User", "AP Kiểm soát (FIN)", "Purchase User", "Vagabond Bao cao",
		],
	},
	{
		"k": "ketoantruong",
		"bac": 6,
		"ten": "Kế toán trưởng",
		"icon": "📊",
		"mo_ta": "Như Kế toán, thêm quyền ghi sổ, huỷ chứng từ và khoá sổ.",
		"lam_duoc": [
			"Mọi quyền của Kế toán",
			"Ghi sổ và huỷ ghi sổ hoá đơn, phiếu chi",
			"Khoá sổ kỳ cũ",
			"Đặt hàng và duyệt đơn mua",
		],
		"vai": [
			"Accounts Manager", "Accounts User", "AP Kiểm soát (FIN)",
			"Purchase Manager", "Purchase User", "Vagabond Bao cao",
		],
	},
	{
		"k": "giamdoc",
		"bac": 7,
		"ten": "Giám đốc",
		"icon": "🎩",
		"mo_ta": "Duyệt chi cấp cuối, xem toàn bộ báo cáo, không sửa chứng từ.",
		"lam_duoc": [
			"Duyệt chi hồ sơ thanh toán ở cấp giám đốc",
			"Xem toàn bộ phân hệ Báo cáo",
			"Xem công nợ, doanh số, giá vốn",
		],
		"vai": [
			ROLE_GIAM_DOC, "AP Giám đốc", "Vagabond Bao cao", "Sales Manager",
			"Accounts User",
		],
	},
	{
		"k": "chucongty",
		"bac": 9,
		"ten": "Chủ công ty",
		"icon": "🔑",
		"mo_ta": "Toàn quyền, kể cả Cài đặt và màn Quản lý người dùng này.",
		"lam_duoc": [
			"Toàn bộ hệ thống, không giới hạn phân hệ nào",
			"Mời tài khoản mới, gán và gỡ quyền",
			"Sửa cấu hình hệ thống, khoá sổ, xoá dữ liệu",
		],
		"vai": ["System Manager", VAI_QLND],
	},
]

GOI_THEO_KEY = {g["k"]: g for g in GOI}

# Tap hop moi vai nam trong goi. Chi nhung vai nay moi bi man hinh nay dong
# vao; vai ngoai danh sach giu nguyen mai mai.
VAI_QUAN_LY = set()
for _g in GOI:
	VAI_QUAN_LY |= set(_g["vai"])


def trong_pham_vi_quan_ly(loai_tk, vai_nguoi):
	"""Người này có thuộc phạm vi màn Quản lý người dùng không.

	PHÉP THUẦN, không chạm Frappe, để hai màn dùng chung một điều kiện.

	Tài khoản nội bộ thì luôn thuộc: họ được tạo ra để làm việc trong hệ
	thống. Tài khoản web thì CHỈ thuộc khi đang giữ ít nhất một vai nằm
	trong các gói chức vụ, tức là người của tiệm.

	Không dùng phép "có vai nào ngoài vai nền" ở đây. Vai Customer và
	Supplier của cổng thông tin không nằm trong vai nền, nên phép đó sẽ kéo
	cả khách hàng vào màn quản lý nhân sự, và người quản lý có thể vô tình
	tắt tài khoản hay đổi quyền của khách. Cổng đặt hàng cho khách đang
	được dựng nên đây là chuyện sắp xảy ra, không phải chuyện xa.
	"""
	if str(loai_tk or "") == "System User":
		return True
	return bool(set(vai_nguoi or ()) & VAI_QUAN_LY)


def _vai_toi(nguoi=None):
	return set(frappe.get_roles(nguoi))


def _la_quan_tri():
	return VAI_QUAN_TRI in _vai_toi()


def _kiem(viec="quản lý người dùng"):
	v = _vai_toi()
	if VAI_QUAN_TRI in v or VAI_QLND in v:
		return
	frappe.throw("Tài khoản của bạn không có quyền %s." % viec)


def _vai_co_that():
	"""Vai nao that su ton tai tren site. Goi co the khai du vai chua tao."""
	ds = frappe.get_all("Role", filters={"disabled": 0}, pluck="name")
	return set(ds)


def _vai_cua(email):
	rows = frappe.get_all(
		"Has Role", filters={"parent": email, "parenttype": "User"}, pluck="role"
	)
	return set(rows)


def _doan_goi(vai_nguoi):
	"""Goi nao khop nhat voi bo vai dang co.

	Khop = du toan bo vai cua goi (trong so vai co that tren site).

	Chon theo BAC truoc, so vai sau. Truoc do chi so sanh so vai nen anh Viet
	- co System Manager - lai bi doan thanh "Thu mua", vi goi Thu mua co bon
	vai con goi Chu cong ty chi co hai. Xep nguoi theo so luong vai la sai:
	quyen nang khong do bang so dong.
	"""
	co_that = _vai_co_that()
	tot = None
	for g in GOI:
		can = set(g["vai"]) & co_that
		if not can:
			continue
		if not (can <= vai_nguoi):
			continue
		if tot is None:
			tot = g
			continue
		if (g.get("bac", 0), len(can)) > (
			tot.get("bac", 0), len(set(tot["vai"]) & co_that)
		):
			tot = g
	return tot


def _thua_so_voi_goi(vai_nguoi, goi):
	"""Vai nghiep vu dang co ma goi khong bao gom."""
	if not goi:
		return sorted(vai_nguoi & VAI_QUAN_LY)
	return sorted((vai_nguoi & VAI_QUAN_LY) - set(goi["vai"]))


# ------------------------------------------------------------------ doc


@frappe.whitelist()
def danh_sach(tu_khoa=None, chip=None, goi=None):
	_kiem("xem danh sách người dùng")
	# LẤY MỌI LOẠI TÀI KHOẢN, không lọc theo loại nữa.
	#
	# Bản cũ chỉ lấy tài khoản nội bộ, nên bốn shipper của tiệm không hiện ở
	# đây, vì họ được tạo dưới dạng tài khoản web hồi dựng site 02/08/2026.
	# Trong khi đó đường mời tài khoản mới lại chặn theo MỌI loại. Kết quả là
	# màn hình nói người này chưa có tài khoản, còn lúc tạo thì máy báo đã có
	# rồi, và không có cách nào đi tiếp. Anh Việt gặp đúng ca này ngày
	# 05/09/2026 khi tạo tài khoản cho một shipper.
	#
	# Một màn quản lý người dùng mà giấu người dùng thì tệ hơn là không có.
	users = frappe.get_all(
		"User",
		fields=["name", "full_name", "enabled", "last_active", "mobile_no",
			"phone", "creation", "user_type"],
		limit_page_length=0,
	)
	co_that = _vai_co_that()
	tim_dung_email = (tu_khoa or "").strip().lower()
	rows = []
	dem = {"dang_lam": 0, "da_tat": 0, "chua_dang_nhap": 0, "chua_gan": 0, "tuy_chinh": 0}
	for u in users:
		if u.name in BO_QUA_USER:
			continue
		vai = _vai_cua(u.name)
		# Tài khoản web chỉ hiện khi giữ vai thuộc một gói chức vụ, tức là
		# người của tiệm. Dùng chung phép với màn Quản lý quyền để hai màn
		# không bao giờ đếm khác nhau.
		trong = trong_pham_vi_quan_ly(u.user_type, vai)
		# NGOẠI LỆ: gõ đúng nguyên email thì luôn tìm ra, kể cả người ngoài
		# phạm vi. Không có lối này thì câu báo "email đã có tài khoản rồi,
		# anh chị tìm trong danh sách" lại chỉ tới chỗ không tìm được, đúng
		# cái ngõ cụt mà bản này sinh ra để dẹp. Trên site thật đang có hai
		# tài khoản web không vai nào rơi vào ca này.
		if not trong and u.name.lower() != tim_dung_email:
			continue
		g = _doan_goi(vai)
		thua = _thua_so_voi_goi(vai, g)
		nghiep_vu = sorted((vai & co_that) - VAI_NEN)
		r = {
			"email": u.name,
			"ten": u.full_name or u.name,
			"sdt": u.mobile_no or u.phone or "",
			"bat": cint(u.enabled),
			"goi": g["k"] if g else "",
			"goi_ten": g["ten"] if g else "Chưa xếp gói",
			"goi_icon": g["icon"] if g else "❔",
			"vai": nghiep_vu,
			"so_vai": len(nghiep_vu),
			"vai_thua": thua,
			"loai": u.user_type,
			"la_tk_web": 0 if u.user_type == "System User" else 1,
			"ngoai_pham_vi": 0 if trong else 1,
			"lan_cuoi": u.last_active,
			"tao_luc": u.creation,
		}
		# Người lọt vào chỉ vì gõ đúng email thì KHÔNG tính vào các con số
		# trên đầu màn, kẻo tổng số nhảy lung tung theo ô tìm kiếm.
		if trong:
			if not cint(u.enabled):
				dem["da_tat"] += 1
			else:
				dem["dang_lam"] += 1
			if not u.last_active:
				dem["chua_dang_nhap"] += 1
			if not nghiep_vu:
				dem["chua_gan"] += 1
			if thua:
				dem["tuy_chinh"] += 1
		rows.append(r)

	# Tách người ngoài phạm vi ra, cho họ đi vòng qua mọi bộ lọc: đã gõ đúng
	# nguyên email thì phải thấy, không thì lại thành ngõ cụt.
	ngoai = [r for r in rows if r["ngoai_pham_vi"]]
	rows = [r for r in rows if not r["ngoai_pham_vi"]]
	tat_ca = len(rows)

	if chip == "dang_lam":
		rows = [r for r in rows if r["bat"]]
	elif chip == "da_tat":
		rows = [r for r in rows if not r["bat"]]
	elif chip == "chua_dang_nhap":
		rows = [r for r in rows if not r["lan_cuoi"]]
	elif chip == "chua_gan":
		rows = [r for r in rows if not r["vai"]]
	elif chip == "tuy_chinh":
		rows = [r for r in rows if r["vai_thua"]]

	if goi:
		rows = [r for r in rows if r["goi"] == goi]

	if tu_khoa:
		k = (tu_khoa or "").strip().lower()
		rows = [
			r for r in rows
			if k in (r["ten"] or "").lower()
			or k in (r["email"] or "").lower()
			or k in (r["sdt"] or "").lower()
		]

	co_roi = {r["email"] for r in rows}
	rows = rows + [r for r in ngoai if r["email"] not in co_roi]

	rows.sort(key=lambda r: (0 if r["bat"] else 1, (r["ten"] or "").lower()))
	dem_goi = {}
	for r in rows:
		dem_goi[r["goi"]] = dem_goi.get(r["goi"], 0) + 1
	return {
		"rows": rows,
		"dem": dem,
		"tat_ca": tat_ca,
		"dem_goi": dem_goi,
		"goi": [
			{"k": g["k"], "ten": g["ten"], "icon": g["icon"], "mo_ta": g["mo_ta"]}
			for g in GOI
		],
		"la_quan_tri": 1 if _la_quan_tri() else 0,
	}


@frappe.whitelist()
def danh_sach_goi():
	"""Man Quan ly quyen: bay tung goi kem viec lam duoc va so nguoi dang giu."""
	_kiem("xem quản lý quyền")
	co_that = _vai_co_that()
	# Lấy MỌI loại tài khoản đang bật rồi lọc bằng đúng phép mà màn danh
	# sách người dùng đang dùng. Bản cũ lọc thẳng System User trong câu truy
	# vấn, nên sau khi màn kia hiện bốn shipper là tài khoản web thì màn này
	# vẫn báo gói Shipper có 0 người. Hai màn nói hai số khác nhau về cùng
	# một nhóm người là lỗi tự nó, không cần ai bấm mới lộ.
	users = frappe.get_all(
		"User", filters={"enabled": 1}, fields=["name", "user_type"],
		limit_page_length=0,
	)
	dem = {}
	nguoi_theo_goi = {}
	for row in users:
		u = row.name
		if u in BO_QUA_USER:
			continue
		vai_u = _vai_cua(u)
		if not trong_pham_vi_quan_ly(row.user_type, vai_u):
			continue
		g = _doan_goi(vai_u)
		k = g["k"] if g else ""
		dem[k] = dem.get(k, 0) + 1
		nguoi_theo_goi.setdefault(k, []).append(
			frappe.db.get_value("User", u, "full_name") or u
		)
	ra = []
	for g in GOI:
		thieu = [v for v in g["vai"] if v not in co_that]
		ra.append({
			"k": g["k"],
			"ten": g["ten"],
			"icon": g["icon"],
			"mo_ta": g["mo_ta"],
			"lam_duoc": g["lam_duoc"],
			"vai": g["vai"],
			"vai_thieu": thieu,
			"so_nguoi": dem.get(g["k"], 0),
			"nguoi": sorted(nguoi_theo_goi.get(g["k"], []))[:12],
		})
	return {
		"goi": ra,
		"chua_xep": dem.get("", 0),
		"nguoi_chua_xep": sorted(nguoi_theo_goi.get("", []))[:20],
		"vai_khac": sorted((co_that - VAI_QUAN_LY) - VAI_NEN),
		"la_quan_tri": 1 if _la_quan_tri() else 0,
	}


@frappe.whitelist()
def chi_tiet(email):
	_kiem("xem hồ sơ người dùng")
	u = frappe.db.get_value(
		"User", email,
		["name", "full_name", "first_name", "last_name", "enabled", "last_active",
		 "mobile_no", "phone", "creation", "user_type"],
		as_dict=True,
	)
	if not u:
		frappe.throw("Không thấy tài khoản %s." % email)
	vai = _vai_cua(email)
	co_that = _vai_co_that()
	g = _doan_goi(vai)
	return {
		"email": u.name,
		"ten": u.full_name or u.name,
		"ho": u.first_name or "",
		"dem": u.last_name or "",
		"bat": cint(u.enabled),
		"sdt": u.mobile_no or u.phone or "",
		"lan_cuoi": u.last_active,
		"tao_luc": u.creation,
		"goi": g["k"] if g else "",
		"goi_ten": g["ten"] if g else "Chưa xếp gói",
		"lam_duoc": g["lam_duoc"] if g else [],
		"vai": sorted((vai & co_that) - VAI_NEN),
		"vai_thua": _thua_so_voi_goi(vai, g),
		"vai_chon_duoc": sorted((co_that - VAI_NEN)),
		"la_quan_tri": 1 if _la_quan_tri() else 0,
		"la_toi": 1 if email == frappe.session.user else 0,
	}


# ------------------------------------------------------------------ ghi


def _chan_leo_quyen(vai_moi, vai_cu):
	"""Nguoi khong phai System Manager thi khong duoc dong vao vai quan tri."""
	if _la_quan_tri():
		return
	nhay = {VAI_QUAN_TRI, "Administrator"}
	if (set(vai_moi) & nhay) != (set(vai_cu) & nhay):
		frappe.throw(
			"Chỉ tài khoản Chủ công ty mới cấp hoặc gỡ được quyền quản trị hệ thống."
		)


def _go_bo_vai_mau(doc):
	"""Gỡ bộ vai mẫu khỏi một tài khoản. Trả về danh sách bộ đã gỡ.

	VÌ SAO PHẢI GỠ, đây là lỗi im lặng nhất từng gặp ở phân hệ này:

	Khung dựng LẠI toàn bộ danh sách vai từ bộ vai mẫu mỗi lần lưu tài
	khoản. Nên vai mình vừa ghi bằng tay bị xoá sạch ngay trong cùng lượt
	lưu đó. Bản ghi vẫn lưu thành công, dấu thời gian vẫn đổi, màn hình vẫn
	báo "đã xếp gói", chỉ có quyền là không vào.

	Ngày 05/09/2026 anh Việt cấp quyền cho một người và máy báo thành công
	trong khi vai không hề vào; lần thử ngày 21/08/2026 cũng hỏng đúng vì
	lý do này mà lúc đó chỉ ghi lại được triệu chứng "ô nhập vai không lưu".
	Đo ra 22 trên 35 tài khoản đang bị buộc bộ vai mẫu, tức là màn Quản lý
	quyền đang vô hiệu với hai phần ba số người mà vẫn báo thành công.

	Gói chức vụ của app là nguồn sự thật về quyền, nên bộ vai mẫu phải nhường
	đường. Gỡ chứ không sửa bộ mẫu: bộ mẫu dùng chung nhiều người, sửa nó là
	đụng tới người không liên quan.
	"""
	da_go = [r.role_profile for r in (doc.get("role_profiles") or [])]
	if doc.get("role_profile_name"):
		if doc.role_profile_name not in da_go:
			da_go.append(doc.role_profile_name)
		doc.role_profile_name = None
	if doc.get("role_profiles"):
		doc.set("role_profiles", [])
	return da_go


def _dat_vai(email, vai_can, cham_vao):
	"""Dat lai vai cho mot nguoi, CHI trong pham vi cham_vao.

	cham_vao: tap vai duoc phep them hoac go o luot nay. Vai ngoai tap nay
	giu nguyen. Tra ve (them, go).
	"""
	co_that = _vai_co_that()
	cham_vao = set(cham_vao) & co_that
	vai_can = set(vai_can) & co_that
	dang_co = _vai_cua(email)

	them = sorted((vai_can & cham_vao) - dang_co)
	go = sorted((dang_co & cham_vao) - vai_can)
	if them or go:
		_chan_leo_quyen(sorted((dang_co | set(them)) - set(go)), sorted(dang_co))

	doc = frappe.get_doc("User", email)
	# Gỡ bộ vai mẫu LUÔN LUÔN, kể cả khi vai hiện tại đã đúng gói rồi.
	#
	# Đây chính là ca hay gặp nhất: bộ vai mẫu bung ra đúng bằng vai của
	# gói, nên không có vai nào cần thêm hay gỡ. Nếu thoát sớm ở đây thì màn
	# hình báo "gói đã đúng" trong khi quyền thật vẫn do bộ mẫu nắm. Hôm nào
	# có người sửa bộ mẫu dùng chung là quyền của người này đổi theo mà
	# không ai đụng vào họ. Bộ "VGB - Sales" đang buộc 4 tài khoản.
	da_go = _go_bo_vai_mau(doc)
	if not them and not go and not da_go:
		return [], []
	giu = [r.role for r in doc.roles if r.role not in cham_vao]
	doc.set("roles", [])
	for r in sorted(set(giu) | (vai_can & cham_vao)):
		doc.append("roles", {"role": r})
	doc.save(ignore_permissions=True)
	# Doc lai tu co so du lieu chu KHONG tin bien trong bo nho: neu con thu
	# gi ghi de vai luc luu thi phai lo ra ngay day, dung de man hinh bao
	# thanh cong roi nguoi dung phat hien sau.
	vai_sau = _vai_cua(email)
	con_thieu = sorted((vai_can & cham_vao) - vai_sau)
	# Kiểm CẢ HAI CHIỀU. Vai đáng lẽ phải gỡ mà vẫn còn thì cũng nguy hệt
	# vai chưa vào, thậm chí nguy hơn: người đã bị rút quyền vẫn dùng được
	# quyền đó, mà màn hình báo đã rút xong.
	con_sot = sorted(set(go) & vai_sau)
	if con_thieu or con_sot:
		phan = []
		if con_thieu:
			phan.append("%s vẫn chưa vào" % ", ".join(con_thieu))
		if con_sot:
			phan.append("%s đáng lẽ phải gỡ mà vẫn còn" % ", ".join(con_sot))
		frappe.throw(
			"Lưu quyền cho %s không ăn: %s. Thường là do tài khoản còn bị "
			"buộc theo một bộ vai mẫu của hệ thống. Anh chị báo kỹ thuật, "
			"đừng bấm lại vì bấm lại cũng vậy."
			% (email, "; ".join(phan))
		)
	return them, go


@frappe.whitelist()
def dat_goi(email, goi):
	"""Xep mot nguoi vao goi chuc vu."""
	_kiem("đổi quyền người dùng")
	g = GOI_THEO_KEY.get(goi)
	if not g:
		frappe.throw("Không có gói chức vụ %s." % goi)
	if not frappe.db.exists("User", email):
		frappe.throw("Không thấy tài khoản %s." % email)
	them, go = _dat_vai(email, g["vai"], VAI_QUAN_LY)
	_ghi_vet("Xếp %s vào gói %s" % (email, g["ten"]))
	return {
		"ok": 1,
		"goi_ten": g["ten"],
		"them": them,
		"go": go,
		"loi_nhan": "Đã xếp %s vào gói %s." % (email, g["ten"])
		+ (" Thêm %d quyền." % len(them) if them else "")
		+ (" Gỡ %d quyền." % len(go) if go else "")
		+ ("" if (them or go) else " Bộ quyền vốn đã đúng, không đổi gì."),
	}


@frappe.whitelist()
def sua_quyen_le(email, vai):
	"""Che do chi tiet: dat thang danh sach vai nghiep vu."""
	_kiem("đổi quyền người dùng")
	if isinstance(vai, str):
		vai = json.loads(vai)
	if not frappe.db.exists("User", email):
		frappe.throw("Không thấy tài khoản %s." % email)
	co_that = _vai_co_that()
	cham_vao = (co_that - VAI_NEN)
	them, go = _dat_vai(email, vai, cham_vao)
	_ghi_vet("Sửa quyền lẻ cho %s" % email)
	return {"ok": 1, "them": them, "go": go, "loi_nhan": "Đã lưu quyền cho %s." % email}


@frappe.whitelist()
def bat_tat(email, bat):
	_kiem("bật tắt tài khoản")
	if email in BO_QUA_USER:
		frappe.throw("Không đụng vào tài khoản hệ thống được.")
	if email == frappe.session.user and not cint(bat):
		frappe.throw("Không tự tắt tài khoản của chính mình được.")
	u = frappe.db.get_value("User", email, ["name", "full_name"], as_dict=True)
	if not u:
		frappe.throw("Không thấy tài khoản %s." % email)
	if not _la_quan_tri() and VAI_QUAN_TRI in _vai_cua(email):
		frappe.throw("Chỉ Chủ công ty mới bật tắt được tài khoản quản trị.")
	doc = frappe.get_doc("User", email)
	doc.enabled = 1 if cint(bat) else 0
	doc.save(ignore_permissions=True)
	_ghi_vet("%s tài khoản %s" % ("Bật" if cint(bat) else "Tắt", email))
	return {
		"ok": 1,
		"bat": cint(bat),
		"loi_nhan": "Đã %s tài khoản %s." % ("bật" if cint(bat) else "tắt", u.full_name or email),
	}


@frappe.whitelist()
def moi(email, ten, goi=None, sdt=None, gui_thu=1):
	"""Tao tai khoan moi va gui thu moi dat mat khau."""
	_kiem("mời tài khoản mới")
	email = (email or "").strip().lower()
	ten = (ten or "").strip()
	if not email or "@" not in email:
		frappe.throw("Email không hợp lệ.")
	if not ten:
		frappe.throw("Chưa nhập họ tên.")
	cu = frappe.db.get_value(
		"User", email, ["full_name", "user_type", "enabled"], as_dict=True
	)
	if cu:
		# Câu báo lỗi phải nói RA cái đang chặn và làm gì tiếp (QT-24). Bản cũ
		# chỉ nói "đã có tài khoản rồi" trong khi tài khoản đó không hiện ở
		# danh sách, nên người dùng đứng im không biết đi đường nào.
		#
		# Chỉ đường bằng Ô TÌM KIẾM chứ không bảo "tìm trong danh sách": tài
		# khoản web chưa có vai nào thì không nằm trong danh sách mặc định,
		# nhưng gõ đúng nguyên email vào ô tìm là ra. Nói chung chung thì lại
		# đẩy người dùng vào đúng ngõ cụt cũ.
		frappe.throw(
			"Email %s đã có tài khoản rồi: %s, loại %s, đang %s. %s"
			% (
				email,
				cu.full_name or "chưa đặt tên",
				"nội bộ" if cu.user_type == "System User" else "tài khoản web",
				"bật" if cint(cu.enabled) else "tắt",
				"Anh chị dán nguyên email %s vào ô tìm kiếm ở đầu màn để mở "
				"người này ra rồi xếp gói chức vụ, không cần tạo mới." % email
				if cint(cu.enabled)
				else "Tài khoản đang tắt. Anh chị dán nguyên email %s vào ô tìm "
				"kiếm ở đầu màn để mở người này ra, bật lại rồi xếp gói."
				% email,
			)
		)
	g = GOI_THEO_KEY.get(goi) if goi else None
	if goi and not g:
		frappe.throw("Không có gói chức vụ %s." % goi)
	if g and VAI_QUAN_TRI in g["vai"] and not _la_quan_tri():
		frappe.throw("Chỉ Chủ công ty mới mời được tài khoản Chủ công ty.")

	phan = ten.split()
	doc = frappe.get_doc({
		"doctype": "User",
		"email": email,
		"first_name": " ".join(phan[:-1]) or ten,
		"last_name": phan[-1] if len(phan) > 1 else "",
		"mobile_no": (sdt or "").strip() or None,
		"user_type": "System User",
		"enabled": 1,
		"send_welcome_email": 1 if cint(gui_thu) else 0,
	})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)

	them = []
	if g:
		them, _ = _dat_vai(email, g["vai"], VAI_QUAN_LY)
	_ghi_vet("Mời tài khoản %s (%s)" % (email, g["ten"] if g else "chưa xếp gói"))
	return {
		"ok": 1,
		"email": email,
		"so_quyen": len(them),
		"loi_nhan": "Đã tạo tài khoản %s%s.%s" % (
			email,
			" với gói %s" % g["ten"] if g else "",
			" Thư mời đặt mật khẩu đã gửi tới hộp thư đó." if cint(gui_thu) else
			" Chưa gửi thư mời, bấm Gửi lại thư khi cần.",
		),
	}


@frappe.whitelist()
def gui_lai_thu(email):
	_kiem("gửi lời mời")
	u = frappe.db.get_value("User", email, ["name", "full_name", "enabled"], as_dict=True)
	if not u:
		frappe.throw("Không thấy tài khoản %s." % email)
	if not u.enabled:
		frappe.throw("Tài khoản đang tắt, bật lên rồi hãy gửi thư.")
	doc = frappe.get_doc("User", email)
	frappe.sendmail(
		recipients=doc.email,
		subject="Tài khoản app The Vagabond Pâtisserie",
		message=thu_moi_html(doc.full_name or "", _lien_ket_dat_mat_khau(doc), link_app()),
		delayed=False,
		retry=3,
	)
	_ghi_vet("Gửi lại thư mời cho %s" % email)
	return {"ok": 1, "loi_nhan": "Đã gửi thư mời tới %s." % email}


def _ghi_vet(viec):
	"""Ghi lai ai lam gi, de sau nay con truy."""
	try:
		frappe.get_doc({
			"doctype": "Comment",
			"comment_type": "Info",
			"reference_doctype": "User",
			"reference_name": frappe.session.user,
			"content": "[Quản lý người dùng] %s lúc %s"
			% (viec, now_datetime().strftime("%d/%m/%Y %H:%M")),
		}).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "vagabond: ghi vet quan ly nguoi dung")
