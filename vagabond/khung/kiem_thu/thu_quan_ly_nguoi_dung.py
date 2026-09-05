# -*- coding: utf-8 -*-
"""Ca kiểm cho hai lỗi im lặng của màn Quản lý người dùng (05/09/2026).

Cả hai đều cùng một họ: MÀN HÌNH NÓI MỘT ĐẰNG, HỆ THỐNG LÀM MỘT NẺO, và
không câu báo nào kêu lên.

LỖI MỘT: xếp gói xong quyền không vào.
  Khung dựng lại danh sách vai từ bộ vai mẫu mỗi lần lưu tài khoản, nên vai
  vừa ghi bị xoá ngay trong cùng lượt lưu. Màn hình vẫn báo thành công. Đo
  ra 22 trên 35 tài khoản đang bị buộc bộ vai mẫu, tức là màn này vô hiệu
  với hai phần ba số người. Anh Việt gặp ngày 05/09; lần 21/08 hỏng cùng lý
  do mà lúc đó chỉ ghi được triệu chứng.

LỖI HAI: người có tài khoản mà màn hình bảo chưa có.
  Danh sách chỉ lấy tài khoản nội bộ, còn đường mời tài khoản mới lại chặn
  theo MỌI loại. Bốn shipper của tiệm là tài khoản web nên không hiện, mà
  tạo mới thì báo đã có rồi. Không có đường nào đi tiếp.

Vòng soát thứ nhất chỉ có ca kiểm ĐỌC MÃ NGUỒN, nên không chứng minh được
hành vi. Codex nói đúng chỗ đó. Các ca dưới đây gọi thẳng hàm thật với một
lớp dữ liệu giả, và ba lỗ hổng Codex tìm ra đều có ca riêng canh.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import BANG_GIA, Doi, ca, dung, gia_lap, la, nem

gia_lap()

# Mô đun nguoi_dung kéo theo nhan_su, mà nhan_su lấy lớp User của khung.
# Bản Frappe giả trong nen.py không có nhánh core, nên dựng tạm ở đây chứ
# không sửa nen.py, kẻo đụng vào nền của mọi bộ kiểm khác.
import sys  # noqa: E402
import types  # noqa: E402

for _ten in ("frappe.core", "frappe.core.doctype", "frappe.core.doctype.user",
		"frappe.core.doctype.user.user"):
	if _ten not in sys.modules:
		sys.modules[_ten] = types.ModuleType(_ten)
if not hasattr(sys.modules["frappe.core.doctype.user.user"], "User"):
	sys.modules["frappe.core.doctype.user.user"].User = type("User", (object,), {})
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test"

from vagabond import nguoi_dung as nd  # noqa: E402

GOI_TEP = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	with io.open(os.path.join(GOI_TEP, ten), encoding="utf-8") as f:
		return f.read()


ND = _doc("nguoi_dung.py")
JS = _doc(os.path.join("public", "js", "bep", "20-danh-muc-quyen.js"))


# ------------------------------------------------------------ lớp giả lập

class _Dong(dict):
	"""Một dòng vai trong bảng con roles."""

	def __getattr__(self, k):
		try:
			return self[k]
		except KeyError:
			raise AttributeError(k)


class _UserGia(object):
	"""Bản giả của doc User, đủ để _dat_vai chạy thật.

	Bắt chước đúng cái đang cắn: nếu còn bộ vai mẫu lúc lưu thì khung DỰNG
	LẠI danh sách vai từ bộ mẫu, xoá sạch vai vừa ghi. Không mô phỏng chỗ
	này thì ca kiểm không bao giờ thấy được lỗi thật.
	"""

	def __init__(self, ten, vai, bo_mau=None, vai_cua_bo_mau=None, ep_them=None):
		self.name = ten
		self.roles = [_Dong({"role": r}) for r in sorted(vai)]
		self.role_profiles = [
			_Dong({"role_profile": b}) for b in (bo_mau or [])
		]
		self.role_profile_name = (bo_mau or [None])[0]
		self._vai_bo_mau = set(vai_cua_bo_mau or ())
		# Vai bi mot co che NGOAI bo vai mau nhoi tro lai luc luu. Dung de
		# do hang rao hau kiem: no phai bat duoc ca thu minh chua biet ten.
		self._ep_them = set(ep_them or ())
		self.so_lan_luu = 0

	def get(self, k, mac_dinh=None):
		return getattr(self, k, mac_dinh)

	def set(self, k, v):
		setattr(self, k, v)

	def append(self, k, gia_tri):
		getattr(self, k).append(_Dong(gia_tri))

	def save(self, **k):
		self.so_lan_luu += 1
		# Đây là hành vi thật của khung: còn buộc bộ mẫu thì vai bị dựng lại.
		if self.role_profiles or self.role_profile_name:
			self.roles = [_Dong({"role": r}) for r in sorted(self._vai_bo_mau)]
		if self._ep_them:
			co = {r.role for r in self.roles} | self._ep_them
			self.roles = [_Dong({"role": r}) for r in sorted(co)]

	def vai(self):
		return {r.role for r in self.roles}


class _Canh(object):
	"""Thay tạm frappe.get_doc, _vai_cua, _vai_co_that trong lúc chạy ca."""

	def __init__(self, doc, moi_vai):
		self.doc = doc
		self.moi_vai = set(moi_vai)
		self.cu = {}

	def __enter__(self):
		self.cu = {
			"get_doc": nd.frappe.get_doc,
			"_vai_cua": nd._vai_cua,
			"_vai_co_that": nd._vai_co_that,
			"_chan_leo_quyen": nd._chan_leo_quyen,
		}
		nd.frappe.get_doc = lambda *a, **k: self.doc
		nd._vai_cua = lambda email: self.doc.vai()
		nd._vai_co_that = lambda: self.moi_vai
		nd._chan_leo_quyen = lambda *a, **k: None
		return self

	def __exit__(self, *a):
		nd.frappe.get_doc = self.cu["get_doc"]
		nd._vai_cua = self.cu["_vai_cua"]
		nd._vai_co_that = self.cu["_vai_co_that"]
		nd._chan_leo_quyen = self.cu["_chan_leo_quyen"]
		return False


class _Site(object):
	"""Thay tạm lớp đọc User cho danh_sach và danh_sach_goi."""

	def __init__(self, users, vai_theo_nguoi, moi_vai):
		self.users = users
		self.vai_theo_nguoi = vai_theo_nguoi
		self.moi_vai = set(moi_vai)
		self.cu = {}

	def __enter__(self):
		self.cu = {
			"get_all": nd.frappe.get_all,
			"_vai_cua": nd._vai_cua,
			"_vai_co_that": nd._vai_co_that,
			"_kiem": nd._kiem,
			"_la_quan_tri": nd._la_quan_tri,
			"get_value": nd.frappe.db.get_value,
		}

		def _get_all(dt, **k):
			if dt != "User":
				return []
			loc = k.get("filters") or {}
			ra = []
			for u in self.users:
				if "enabled" in loc and int(u["enabled"]) != int(loc["enabled"]):
					continue
				if "user_type" in loc and u["user_type"] != loc["user_type"]:
					continue
				ra.append(Doi(u))
			if k.get("pluck"):
				return [r[k["pluck"]] for r in ra]
			return ra

		nd.frappe.get_all = _get_all
		nd._vai_cua = lambda email: set(self.vai_theo_nguoi.get(email, ()))
		nd._vai_co_that = lambda: self.moi_vai
		nd._kiem = lambda *a, **k: None
		nd._la_quan_tri = lambda *a, **k: True
		nd.frappe.db.get_value = lambda dt, ten, truong=None, **k: ten
		return self

	def __exit__(self, *a):
		nd.frappe.get_all = self.cu["get_all"]
		nd._vai_cua = self.cu["_vai_cua"]
		nd._vai_co_that = self.cu["_vai_co_that"]
		nd._kiem = self.cu["_kiem"]
		nd._la_quan_tri = self.cu["_la_quan_tri"]
		nd.frappe.db.get_value = self.cu["get_value"]
		return False


def _nguoi(email, loai="System User", bat=1):
	return {
		"name": email, "full_name": email.split("@")[0], "enabled": bat,
		"last_active": None, "mobile_no": "", "phone": "",
		"creation": "2026-08-02 14:43:00", "user_type": loai,
	}


VAI_SALES = ["Sales User", "Bộ phận đặt hàng", "Nhan hang dieu chuyen", "Kiểm kê viên"]
MOI_VAI = set(VAI_SALES) | {"Shipper", "Sales Manager", "Customer", "Supplier", "All"}


# ------------------------------------------------- phép thuần xác định phạm vi

@ca("tai khoan noi bo luon thuoc pham vi man quan ly nguoi dung")
def _pham_vi_noi_bo():
	dung("khong vai nao van thuoc", nd.trong_pham_vi_quan_ly("System User", set()))


@ca("tai khoan web co vai trong goi thi thuoc pham vi")
def _pham_vi_web_co_vai():
	dung("shipper thuoc", nd.trong_pham_vi_quan_ly("Website User", {"Shipper"}))


@ca("khach cong thong tin KHONG lot vao man quan ly nhan su")
def _pham_vi_khach():
	# Customer va Supplier khong nam trong VAI_NEN, nen phep cu "co vai nao
	# ngoai vai nen" se keo ca khach vao day. Cong dat hang cho khach dang
	# duoc dung, nen day la chuyen sap xay ra chu khong phai chuyen xa.
	dung("khach khong thuoc", not nd.trong_pham_vi_quan_ly("Website User", {"Customer"}))
	dung("nha cung cap khong thuoc",
		not nd.trong_pham_vi_quan_ly("Website User", {"Supplier"}))
	dung("khong vai nao cung khong thuoc",
		not nd.trong_pham_vi_quan_ly("Website User", set()))


# ------------------------------------------------------- hành vi của _dat_vai

@ca("go bo vai mau CA KHI vai da dung san, khong thi bo mau van nam quyen")
def _go_bo_mau_khi_khong_co_delta():
	# Ca hay gap nhat: bo vai mau bung ra dung bang vai cua goi, nen khong co
	# vai nao can them hay go. Ban dau thoat som o day, nen bo mau van con
	# nguyen va hom nao co nguoi sua bo mau dung chung la quyen doi theo.
	doc = _UserGia("a@vgb", set(VAI_SALES), bo_mau=["VGB - Sales"],
		vai_cua_bo_mau=set(VAI_SALES))
	with _Canh(doc, MOI_VAI):
		them, go = nd._dat_vai("a@vgb", set(VAI_SALES), set(VAI_SALES))
	la("khong them vai nao", them, [])
	la("khong go vai nao", go, [])
	la("bang con bo vai mau da rong", list(doc.role_profiles), [])
	la("ten bo vai mau da xoa", doc.role_profile_name, None)
	dung("co luu lai", doc.so_lan_luu >= 1)
	la("vai van du sau khi luu", doc.vai(), set(VAI_SALES))


@ca("khong co bo vai mau va vai da dung thi khong luu vo ich")
def _khong_luu_vo_ich():
	doc = _UserGia("b@vgb", set(VAI_SALES))
	with _Canh(doc, MOI_VAI):
		them, go = nd._dat_vai("b@vgb", set(VAI_SALES), set(VAI_SALES))
	la("khong them", them, [])
	la("khong go", go, [])
	la("khong luu lan nao", doc.so_lan_luu, 0)


@ca("xep goi cho nguoi dang bi buoc bo vai mau thi vai moi phai vao that")
def _xep_goi_qua_bo_mau():
	doc = _UserGia("c@vgb", set(VAI_SALES), bo_mau=["VGB - Sales"],
		vai_cua_bo_mau=set(VAI_SALES))
	can = set(VAI_SALES) | {"Sales Manager"}
	with _Canh(doc, MOI_VAI):
		them, go = nd._dat_vai("c@vgb", can, MOI_VAI - {"Customer", "Supplier", "All"})
	la("them dung mot vai", them, ["Sales Manager"])
	dung("Sales Manager da vao that", "Sales Manager" in doc.vai())


@ca("vai dang le phai go ma van con thi phai keu len, khong duoc im")
def _hau_kiem_chieu_go():
	# Ban dau hau kiem chi soi vai CON THIEU. Nguoi da bi rut quyen ma van
	# dung duoc quyen do con nguy hon vai chua vao, vi man hinh bao da rut
	# xong roi. O day gia lap mot co che NGOAI bo vai mau nhoi Sales Manager
	# tro lai luc luu: bo vai mau la thu duy nhat minh da tim ra hom nay,
	# khong co gi bao dam no la thu duy nhat ton tai. Hang rao phai bat duoc
	# ca nhung thu chua biet ten.
	doc = _UserGia("d@vgb", set(VAI_SALES) | {"Sales Manager"},
		ep_them={"Sales Manager"})

	def _chay():
		with _Canh(doc, MOI_VAI):
			nd._dat_vai("d@vgb", set(VAI_SALES),
				MOI_VAI - {"Customer", "Supplier", "All"})

	nem("phai nem loi vi Sales Manager con sot lai", _chay)


@ca("vai moi khong vao duoc thi cung phai keu len")
def _hau_kiem_chieu_them():
	# Chieu con lai: vai vua ghi bi thu gi do xoa ngay trong luot luu. Day
	# dung la cai anh Viet gap voi Loan Anh ngay 05/09.
	doc = _UserGia("e@vgb", set(VAI_SALES), bo_mau=["VGB - Sales"],
		vai_cua_bo_mau=set(VAI_SALES))
	# Bo mau khong chiu roi ra: dung de do rieng hang rao hau kiem.
	doc.set("khong_go_duoc", 1)
	cu_go = nd._go_bo_vai_mau
	nd._go_bo_vai_mau = lambda d: []
	try:
		def _chay():
			with _Canh(doc, MOI_VAI):
				nd._dat_vai("e@vgb", set(VAI_SALES) | {"Sales Manager"},
					MOI_VAI - {"Customer", "Supplier", "All"})

		nem("phai nem loi vi Sales Manager khong vao duoc", _chay)
	finally:
		nd._go_bo_vai_mau = cu_go


# ------------------------------------------------- hành vi của hai màn danh sách

def _site_mau():
	users = [
		_nguoi("noibo@vgb"),
		_nguoi("shipper@vgb", "Website User"),
		_nguoi("khach@vgb", "Website User"),
		_nguoi("web-khong-vai@vgb", "Website User"),
	]
	vai = {
		"noibo@vgb": set(VAI_SALES),
		"shipper@vgb": {"Shipper"},
		"khach@vgb": {"Customer"},
		"web-khong-vai@vgb": set(),
	}
	return users, vai


@ca("danh sach hien shipper la tai khoan web, giau khach cong thong tin")
def _danh_sach_pham_vi():
	users, vai = _site_mau()
	with _Site(users, vai, MOI_VAI):
		ra = nd.danh_sach()
	co = {r["email"] for r in ra["rows"]}
	dung("shipper hien ra", "shipper@vgb" in co)
	dung("nguoi noi bo hien ra", "noibo@vgb" in co)
	dung("khach KHONG hien ra", "khach@vgb" not in co)
	dung("tai khoan web khong vai KHONG hien mac dinh",
		"web-khong-vai@vgb" not in co)


@ca("go dung nguyen email thi tim ra ca nguoi ngoai pham vi")
def _tim_dung_email():
	# Day la duong ma cau bao trung chi toi. Khong co duong nay thi cau bao
	# lai dua nguoi dung vao dung ngo cut cu. Site that dang co hai tai
	# khoan web khong vai nao roi vao ca nay.
	users, vai = _site_mau()
	with _Site(users, vai, MOI_VAI):
		ra = nd.danh_sach(tu_khoa="web-khong-vai@vgb")
	co = {r["email"] for r in ra["rows"]}
	dung("tim dung email thi ra", "web-khong-vai@vgb" in co)
	dong = [r for r in ra["rows"] if r["email"] == "web-khong-vai@vgb"][0]
	la("co danh dau la ngoai pham vi", dong["ngoai_pham_vi"], 1)
	dung("khong tinh vao tong so", ra["tat_ca"] <= 2)


@ca("hai man phai dem shipper giong nhau, khong duoc man 4 nguoi man 0 nguoi")
def _hai_man_khop_nhau():
	users, vai = _site_mau()
	with _Site(users, vai, MOI_VAI):
		ds = nd.danh_sach()
		goi = nd.danh_sach_goi()
	so_ds = len([r for r in ds["rows"] if "Shipper" in r["vai"]])
	so_goi = 0
	for g in goi["goi"]:
		if g["k"] == "shipper":
			so_goi = g["so_nguoi"]
	la("man danh sach dem duoc 1 shipper", so_ds, 1)
	la("man quan ly quyen dem cung so", so_goi, so_ds)


@ca("man quan ly quyen cung khong dem khach cong thong tin")
def _goi_khong_dem_khach():
	users, vai = _site_mau()
	with _Site(users, vai, MOI_VAI):
		goi = nd.danh_sach_goi()
	ten = []
	for g in goi["goi"]:
		ten += list(g.get("nguoi") or [])
	dung("khong co khach trong bat ky goi nao",
		not [t for t in ten if "khach" in str(t)])


# ------------------------------------------------------- neo trong mã nguồn

@ca("hai man dung chung mot phep xac dinh pham vi, khong ai tu che rieng")
def _dung_chung_phep():
	i = ND.find("def danh_sach_goi(")
	than = ND[i:ND.find("\ndef ", i + 10)]
	dung("man quan ly quyen goi phep chung",
		"trong_pham_vi_quan_ly(" in than)
	dung("khong con loc thang System User trong cau truy van",
		'"user_type": "System User"' not in than)


@ca("man hien ro nguoi lot vao chi vi tim dung email")
def _nhan_tren_man():
	dung("co nhan tai khoan web", "tài khoản web" in JS)
	dung("co nhan ngoai danh sach", "ngoai_pham_vi" in JS)


@ca("cau bao trung chi duong bang o tim kiem chu khong noi chung chung")
def _cau_bao_trung():
	i = ND.find("def moi(")
	than = ND[i:ND.find("\ndef ", i + 10)]
	dung("noi ro ten nguoi", "full_name" in than)
	dung("noi ro loai tai khoan", "tài khoản web" in than)
	dung("noi ro dang bat hay tat", '"bật" if cint' in than)
	dung("chi duong bang o tim kiem", "ô tìm kiếm" in than)
	dung("khong con bao tim chung chung trong danh sach",
		"tìm người này trong danh sách" not in than)
