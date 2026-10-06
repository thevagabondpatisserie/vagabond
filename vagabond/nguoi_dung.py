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
Tu v582 (06/10/2026) mot nguoi giu duoc NHIEU goi, quyen cong don.

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


# Goi chuc vu theo PHAN HE (anh Viet chot 06/10/2026, docs/quyen-theo-phan-he.md).
#
# Moi nguoi nhan goi theo bo phan; nguoi kiem viec nhan HAI goi va quyen
# duoc CONG DON (dat_goi nhan danh sach goi). Thu tu o day la thu tu hien
# tren app: viec nhieu nguoi lam nhat len truoc, quyen nang nhat xuong duoi.
#
# Buoc 1 chi GOM quyen dang co theo bo phan, khong bot quyen cua ai, tru 8
# diem anh Viet da chot (quay tao don ban, Sales giu sua bang gia va co
# khuyen mai, ke toan toan quyen kho va san xuat, giam doc toan quyen...).
_DAT_HANG = ["Bộ phận đặt hàng", "Nhan hang dieu chuyen", "Kiểm kê viên"]
_SALES = ["Sales User", "Sales Manager", "VGB - Quản lý khuyến mãi", "Vagabond Bao cao"] + _DAT_HANG

GOI = [
	{
		"k": "quay",
		"bac": 2,
		"ten": "Quầy",
		"icon": "🏪",
		"mo_ta": "Bán quầy, tạo đơn bán, nhận hàng điều chuyển, đặt hàng, kiểm kê.",
		"lam_duoc": [
			"Bán quầy và tạo đơn bán",
			"Nhận hàng điều chuyển giữa các kho",
			"Đặt hàng nguyên vật liệu, đếm kiểm kê",
		],
		"vai": ["Sales User"] + _DAT_HANG,
	},
	{
		"k": "sales",
		"bac": 3,
		"ten": "Sales",
		"icon": "🎂",
		"mo_ta": "Đơn bán, khách hàng và bảng giá, khuyến mãi, công nợ phải thu, báo cáo bán.",
		"lam_duoc": [
			"Tạo và sửa đơn, lên vận đơn, đối soát COD",
			"Sửa khách hàng và bảng giá, chạy khuyến mãi",
			"Công nợ phải thu: gom phiếu, khớp tay theo giao dịch, đính UNC",
			"Xem phân hệ Báo cáo",
		],
		"vai": list(_SALES),
	},
	{
		"k": "qlch",
		"bac": 4,
		"ten": "Quản lý cửa hàng",
		"icon": "👑",
		"mo_ta": "Như Quầy và Sales, thêm ca, đơn treo, chốt kiểm kê và xuất huỷ.",
		"lam_duoc": [
			"Mọi quyền của Quầy và Sales",
			"Quản lý ca, đơn treo, máy in cửa hàng",
			"Chốt kiểm kê, duyệt xuất huỷ",
		],
		"vai": ["VGB - Quản lý cửa hàng", "Stock Manager"] + _SALES,
	},
	{
		"k": "bep",
		"bac": 2,
		"ten": "Bếp",
		"icon": "🧑‍🍳",
		"mo_ta": "Lệnh sản xuất, bán thành phẩm, kiểm bánh, đặt nguyên liệu, kiểm kê.",
		"lam_duoc": [
			"Nhận và chốt lệnh sản xuất, ghi bán thành phẩm",
			"Kiểm bánh cuối ngày",
			"Đặt hàng nguyên vật liệu, đếm kiểm kê",
		],
		"vai": ["Manufacturing User", "Bếp phó", "Bộ phận đặt hàng", "Kiểm kê viên"],
	},
	{
		"k": "bepql",
		"bac": 4,
		"ten": "Quản lý sản xuất",
		"icon": "🍰",
		"mo_ta": "Như Bếp, thêm duyệt sản xuất và mua hàng R&D.",
		"lam_duoc": [
			"Mọi quyền của Bếp",
			"Duyệt kế hoạch và lệnh sản xuất",
			"Đặt mua hàng R&D",
		],
		"vai": [
			"Manufacturing Manager", "Manufacturing User", "Bếp phó",
			"Bộ phận đặt hàng", "Kiểm kê viên", "Mua hàng R&D",
		],
	},
	{
		"k": "kho",
		"bac": 4,
		"ten": "Kho",
		"icon": "📦",
		"mo_ta": "Nhập xuất kho, danh mục món, chốt kiểm kê.",
		"lam_duoc": [
			"Nhập, xuất, điều chuyển kho",
			"Duyệt phiếu xuất huỷ, chốt kiểm kê",
			"Sửa danh mục món",
		],
		"vai": ["Stock Manager", "Stock User", "Item Manager", "Mua hàng R&D"] + _DAT_HANG,
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
		"k": "marketing",
		"bac": 2,
		"ten": "Marketing",
		"icon": "📣",
		"mo_ta": "Việc Marketing, đặt hàng, nhận hàng điều chuyển, kiểm kê.",
		"lam_duoc": [
			"Việc cần làm của Marketing, tặng quà khách VIP",
			"Đặt hàng, nhận hàng điều chuyển, kiểm kê",
		],
		"vai": ["Marketing"] + _DAT_HANG,
	},
	{
		"k": "muahang",
		"bac": 4,
		"ten": "Thu mua",
		"icon": "🛒",
		"mo_ta": "Đơn mua, nhà cung cấp, hoá đơn mua, nối phiếu kho, lập hồ sơ thanh toán.",
		"lam_duoc": [
			"Gom yêu cầu thành đơn đặt hàng nhà cung cấp",
			"Quản lý nhà cung cấp, đối chiếu và nối hoá đơn mua với phiếu kho",
			"Lập hồ sơ thanh toán (APP) gửi kế toán duyệt",
		],
		"vai": [
			ROLE_THU_MUA, "Purchase User", "Purchase Manager", "AP Officer",
			"Sua hoa don mua (noi phieu kho)", "Item Manager", "Stock Manager", "Stock User",
			"Bộ phận đặt hàng", "Mua hàng R&D", "Kiểm kê viên",
		],
	},
	{
		"k": "ketoan",
		"bac": 6,
		"ten": "Kế toán",
		"icon": "🧮",
		"mo_ta": "Toàn quyền kế toán, kho và sản xuất: ghi sổ, công nợ, giá vốn, chứng từ.",
		"lam_duoc": [
			"Ghi sổ, huỷ ghi sổ, khoá sổ, phiếu thu chi, công nợ thu và trả",
			"Giá vốn, công thức, toàn quyền chứng từ kho và sản xuất",
			"Xem và sửa khách hàng, đơn bán, đơn mua",
			"Xem toàn bộ phân hệ Báo cáo",
		],
		"vai": [
			"Accounts Manager", "Accounts User", "AP Kiểm soát (FIN)",
			"Purchase Manager", "Purchase User", "Sales Manager", "Sales Master Manager",
			"Stock Manager", "Stock User", "Manufacturing Manager", "Manufacturing User",
			"Item Manager", "VGB - Quản lý công thức", "Vagabond Bao cao",
			"Bộ phận đặt hàng", "Kiểm kê viên",
		],
	},
	{
		"k": "nhansu",
		"bac": 5,
		"ten": "Quản lý người dùng",
		"icon": "🪪",
		"mo_ta": "Mời tài khoản, xếp gói chức vụ, bật tắt tài khoản. Không cấp được quyền quản trị.",
		"lam_duoc": [
			"Mời tài khoản mới, gửi lại thư đặt mật khẩu",
			"Xếp người vào gói chức vụ, bật tắt tài khoản",
		],
		"vai": [VAI_QLND],
	},
	{
		"k": "giamdoc",
		"bac": 8,
		"ten": "Giám đốc",
		"icon": "🎩",
		"mo_ta": "Toàn quyền nghiệp vụ mọi phân hệ, duyệt chi cấp cuối. Không gồm cấu hình hệ thống.",
		"lam_duoc": [
			"Mọi quyền của mọi gói ở trên",
			"Duyệt chi hồ sơ thanh toán ở cấp giám đốc",
			"Quản lý người dùng",
		],
		# Điền ở dưới: hợp của mọi gói nghiệp vụ (anh Việt 06/10/2026 điểm 8).
		"vai": [ROLE_GIAM_DOC, "AP Giám đốc"],
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

# Giám đốc = hợp mọi gói nghiệp vụ (trừ Shipper và vai quản trị hệ thống).
for _g in GOI:
	if _g["k"] not in ("giamdoc", "chucongty", "shipper"):
		for _v in _g["vai"]:
			if _v not in GOI[-2]["vai"]:
				GOI[-2]["vai"].append(_v)

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


def doan_cac_goi(vai_nguoi, co_that):
	"""Moi goi nguoi nay dang giu tron, bo nhung goi da nam gon trong goi khac.

	PHEP THUAN, khong cham Frappe. Tra ve danh sach goi, goi nang nhat dau.

	Tu 06/10/2026 mot nguoi giu duoc NHIEU goi (anh Viet chot: quyen cong
	don, vi du De la Quan ly cua hang kiem Quan ly nguoi dung). Nen khong con
	"doan mot goi" nua: lay moi goi ma nguoi do co du vai, roi bo goi nao
	da nam tron trong mot goi khac cung khop (Quay nam trong Sales, Bep nam
	trong Quan ly san xuat, moi goi nghiep vu nam trong Giam doc). Neu khong
	bo, Giam doc se hien thanh mot chuoi muoi goi.

	Khop = du toan bo vai cua goi trong so vai co that tren site. Goi khong
	co vai nao ton tai tren site thi khong bao gio khop.
	"""
	vai_nguoi = set(vai_nguoi or ())
	khop = []
	for g in GOI:
		can = set(g["vai"]) & set(co_that or ())
		if can and can <= vai_nguoi:
			khop.append((g, can))
	ra = []
	for i, (g, can) in enumerate(khop):
		bi_nuot = False
		for j, (h, can_h) in enumerate(khop):
			if i == j:
				continue
			if can < can_h:
				bi_nuot = True
			elif can == can_h and (h.get("bac", 0), -j) > (g.get("bac", 0), -i):
				# Hai goi trung y vai: giu goi bac cao hon, bang bac thi goi dung truoc.
				bi_nuot = True
			if bi_nuot:
				break
		if not bi_nuot:
			ra.append(g)
	ra.sort(key=lambda g: -g.get("bac", 0))
	return ra


def ten_cac_goi(cac_goi):
	return " + ".join(g["ten"] for g in cac_goi) if cac_goi else "Chưa xếp gói"


def vai_cua_cac_goi(cac_goi):
	"""Hop vai cua cac goi. PHEP THUAN."""
	ra = set()
	for g in cac_goi or ():
		ra |= set(g["vai"])
	return ra


def doc_cac_goi(goi):
	"""Nhan goi dang chuoi "a,b", JSON '["a","b"]' hoac danh sach. Tra ve goi.

	PHEP THUAN. Khoa la thi nem ValueError kem ten khoa, de ben goi bao dung
	cai sai. Trung khoa thi gop. Giu thu tu nguoi dung chon.
	"""
	if goi is None:
		return []
	if isinstance(goi, str):
		t = goi.strip()
		if t.startswith("["):
			goi = json.loads(t)
		else:
			goi = [x for x in t.split(",")]
	ra, da = [], set()
	for k in goi:
		k = str(k or "").strip()
		if not k or k in da:
			continue
		if k not in GOI_THEO_KEY:
			raise ValueError(k)
		da.add(k)
		ra.append(GOI_THEO_KEY[k])
	return ra


def _doan_goi(vai_nguoi):
	"""Goi nang nhat nguoi nay dang giu (giu cho cho cu)."""
	ds = doan_cac_goi(vai_nguoi, _vai_co_that())
	return ds[0] if ds else None


def _thua_so_voi_goi(vai_nguoi, cac_goi):
	"""Vai nghiep vu dang co ma KHONG goi nao nguoi do giu bao gom."""
	if isinstance(cac_goi, dict):
		cac_goi = [cac_goi]
	return sorted((set(vai_nguoi) & VAI_QUAN_LY) - vai_cua_cac_goi(cac_goi))


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
		cg = doan_cac_goi(vai, co_that)
		g = cg[0] if cg else None
		thua = _thua_so_voi_goi(vai, cg)
		nghiep_vu = sorted((vai & co_that) - VAI_NEN)
		r = {
			"email": u.name,
			"ten": u.full_name or u.name,
			"sdt": u.mobile_no or u.phone or "",
			"bat": cint(u.enabled),
			"goi": g["k"] if g else "",
			"cac_goi": [x["k"] for x in cg],
			"goi_ten": ten_cac_goi(cg),
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

	# Tách RIÊNG người khớp đúng nguyên email, cho đi vòng qua mọi bộ lọc.
	#
	# Vòng trước chỉ mở lối này cho người NGOÀI phạm vi, nên vẫn còn ngõ cụt:
	# màn giữ nguyên chip và gói đang chọn khi đổi ô tìm kiếm, nên đang đứng ở
	# nhóm Đang làm mà tìm một tài khoản ĐÃ TẮT thì vẫn không thấy, dù làm
	# đúng y lời câu báo trùng. Người nội bộ đã tắt và shipper đã tắt đều mắc.
	# Gõ đúng nguyên email là ý định rõ ràng tới mức không bộ lọc nào được
	# phép chắn, bất kể người đó thuộc loại nào.
	khop_email = [r for r in rows if r["email"].lower() == tim_dung_email] if tim_dung_email else []
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
		# Người giữ nhiều gói hiện ở MỌI gói họ giữ.
		rows = [r for r in rows if goi in r["cac_goi"]]

	if tu_khoa:
		k = (tu_khoa or "").strip().lower()
		rows = [
			r for r in rows
			if k in (r["ten"] or "").lower()
			or k in (r["email"] or "").lower()
			or k in (r["sdt"] or "").lower()
		]

	co_roi = {r["email"] for r in rows}
	rows = rows + [r for r in khop_email if r["email"] not in co_roi]

	rows.sort(key=lambda r: (0 if r["bat"] else 1, (r["ten"] or "").lower()))
	dem_goi = {}
	for r in rows:
		for k in (r["cac_goi"] or [""]):
			dem_goi[k] = dem_goi.get(k, 0) + 1
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
		cg = doan_cac_goi(vai_u, co_that)
		ten_u = frappe.db.get_value("User", u, "full_name") or u
		# Người giữ hai gói được đếm ở CẢ HAI gói, khớp với bộ lọc gói của
		# màn danh sách người dùng.
		for k in ([x["k"] for x in cg] or [""]):
			dem[k] = dem.get(k, 0) + 1
			nguoi_theo_goi.setdefault(k, []).append(ten_u)
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
	cg = doan_cac_goi(vai, co_that)
	g = cg[0] if cg else None
	lam = []
	for x in cg:
		for viec in x["lam_duoc"]:
			if viec not in lam:
				lam.append(viec)
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
		"cac_goi": [x["k"] for x in cg],
		"goi_ten": ten_cac_goi(cg),
		"lam_duoc": lam,
		"vai": sorted((vai & co_that) - VAI_NEN),
		"vai_thua": _thua_so_voi_goi(vai, cg),
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


def _doc_goi_hoac_bao(goi):
	try:
		return doc_cac_goi(goi)
	except ValueError as e:
		frappe.throw("Không có gói chức vụ %s." % e)


@frappe.whitelist()
def dat_goi(email, goi):
	"""Xep mot nguoi vao MOT HAY NHIEU goi chuc vu, quyen cong don.

	goi: mot khoa ("sales"), chuoi "qlch,nhansu" hoac danh sach JSON.
	Vai cua nguoi do trong pham vi goi = HOP vai cac goi chon; vai ngoai
	moi goi giu nguyen nhu cu.
	"""
	_kiem("đổi quyền người dùng")
	cac = _doc_goi_hoac_bao(goi)
	if not cac:
		frappe.throw("Chưa chọn gói chức vụ nào.")
	if not frappe.db.exists("User", email):
		frappe.throw("Không thấy tài khoản %s." % email)
	them, go = _dat_vai(email, vai_cua_cac_goi(cac), VAI_QUAN_LY)
	ten = ten_cac_goi(cac)
	_ghi_vet("Xếp %s vào gói %s" % (email, ten))
	return {
		"ok": 1,
		"goi_ten": ten,
		"cac_goi": [g["k"] for g in cac],
		"them": them,
		"go": go,
		"loi_nhan": "Đã xếp %s vào gói %s." % (email, ten)
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
	cac = _doc_goi_hoac_bao(goi) if goi else []
	vai_moi = vai_cua_cac_goi(cac)
	g = {"ten": ten_cac_goi(cac)} if cac else None
	if VAI_QUAN_TRI in vai_moi and not _la_quan_tri():
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
		them, _ = _dat_vai(email, vai_moi, VAI_QUAN_LY)
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
