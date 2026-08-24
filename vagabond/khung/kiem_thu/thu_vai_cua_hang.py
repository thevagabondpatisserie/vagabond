"""Kiem thu: vai "Quan ly cua hang" va cac cua no mo ra.

Ngay 24/08/2026 ban Le Hoang De bao khong chinh duoc cau hinh may in. Ban
ay la quan ly cua hang kiem giam doc van hanh, ho so vai la
`VGB - Quan ly cua hang`, nhung ho so do khong co vai nao nam trong
`may_in.QUYEN_SUA`.

Goc van de: he khong co VAI nao mang nghia "quan ly cua hang", chi co mot
HO SO ten nhu vay. Nen moi lan can mo mot man cho vai tro do, nguoi ta lai
muon tam mot vai khac cho xong (Sales Manager, Accounts Manager), va muon
nham mot lan la mo them ca dong cua khong lien quan.

Bo ca kiem duoi day chot:
  1. Phep tinh vai con thieu chay dung
  2. Vai moi CO mat o cac cua van hanh
  3. Vai moi KHONG mat o cac cua ke toan va so sach - day la ca quan
     trong nhat, vi no chan viec mo rong am tham ve sau
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	p = os.path.join(GOI, ten)
	if not os.path.exists(p):
		return ""
	return io.open(p, encoding="utf-8").read()


def _nap_thuan():
	ma = _doc("vai_cua_hang.py")
	moc = "# ------------------------------------------------------- phan can Frappe"
	assert moc in ma, "vai_cua_hang.py doi cau truc"
	ns = {}
	exec(compile(ma.split(moc)[0], "vai_cua_hang_thuan", "exec"), ns)
	return ns


V = _nap_thuan()
VAI = V["VAI_QLCH"]

# Cac cua VAN HANH cua hang: vai moi phai co mat.
CUA_VAN_HANH = (
	("may_in.py", "QUYEN_SUA"),          # cau hinh may in - viec goc cua ban De
	("diem_ban.py", "QUYEN_SUA"),        # diem ban
	("quyen_quay.py", "QUYEN_SUA"),      # quyen tai quay
	("pt_thanh_toan.py", "QUYEN_SUA"),   # phuong thuc thanh toan
	("nhap_khach.py", "QUYEN"),          # nhap khach
	("viec_can_lam.py", "VAI_QUAN_LY"),  # viec can lam cap quan ly
)

# Cac cua KE TOAN va SO SACH: vai moi TUYET DOI khong duoc co mat.
# Quan ly cua hang khong phai ke toan. Rieng hai cua hoa don thi cham toi
# hoa don dien tu da gui co quan thue, dung dieu 11.
CUA_KE_TOAN = (
	("but_toan.py", "QUYEN_XEM"),
	("but_toan.py", "QUYEN_LAP"),
	("but_toan.py", "QUYEN_GHI"),
	("chung_tu.py", "QUYEN_HUY"),
	("chung_tu.py", "QUYEN_KHOA_SO"),
	("ban_hang.py", "QUYEN_SUA_NGAY"),
	("ban_hang.py", "QUYEN_HDDT_THAY_THE"),
	("ho_so_tt.py", "VAI_FIN"),
	("hoan_tien.py", "VAI_KE_TOAN"),
	("nop_quy.py", "VAI_KY_NHAN"),
	("tai_khoan.py", "QUYEN_SUA"),
	("tai_san.py", "QUYEN_XEM"),
	("tai_san.py", "QUYEN_SUA"),
	("de_nghi_chi.py", "VAI_DUYET"),
)


def _khoi_hang_so(tep, ten):
	"""Cat dung dong khai hang so ra, khong lay ca tep."""
	ma = _doc(tep)
	moc = "\n%s = " % ten
	if moc not in ma:
		return ""
	return ma.split(moc)[1].split("\n\n")[0]


# ------------------------------------------------------------ phan thuan

@ca("phép tính vai còn thiếu: hồ sơ trống thì thiếu đủ cả ba")
def _():
	la("thiếu ba vai", V["vai_can_co"]([]), sorted([VAI] + list(V["VAI_THEM_SAN"])))


@ca("phép tính vai còn thiếu: hồ sơ đã đủ thì không đòi thêm gì")
def _():
	da_co = [VAI] + list(V["VAI_THEM_SAN"])
	la("không thiếu gì", V["vai_can_co"](da_co), [])


@ca("phép tính vai còn thiếu: chỉ đòi phần chưa có, không đụng vai khác")
def _():
	# Ho so that cua ban De co muoi vai. Ham chi duoc doi phan thieu, va
	# tuyet doi khong duoc tra ve lenh bot vai nao.
	that = ["AP Giám đốc", "Bộ phận đặt hàng", "Manufacturing User",
			"Stock User", "Sales User", "Kiểm kê viên"]
	thieu = V["vai_can_co"](that)
	la("chỉ còn thiếu hai", thieu, sorted([VAI, "Stock Manager"]))


@ca("phép tính vai còn thiếu: bỏ qua ô trống và khoảng trắng thừa")
def _():
	la("vẫn nhận ra vai đã có", V["vai_can_co"]([VAI, "", None, "  "]),
	   sorted(list(V["VAI_THEM_SAN"])))


# --------------------------------------------------- cua van hanh phai mo

@ca("vai quản lý cửa hàng có mặt ở mọi cửa vận hành cửa hàng")
def _():
	thieu = []
	for tep, ten in CUA_VAN_HANH:
		if "VAI_QLCH" not in _khoi_hang_so(tep, ten):
			thieu.append("%s.%s" % (tep, ten))
	la("không cửa vận hành nào còn khoá", thieu, [])


@ca("mọi mô đun dùng vai đều lấy từ một chỗ, không chép chuỗi")
def _():
	# Chep tay chuoi "VGB - Quan ly cua hang" vao sau mo dun la sau co hoi
	# go sai chinh ta, ma go sai thi phep kiem im lang cho khong ai vao.
	xau = []
	for tep, _ten in CUA_VAN_HANH:
		ma = _doc(tep)
		if 'from vagabond.vai_cua_hang import VAI_QLCH' not in ma:
			xau.append(tep)
		if '"%s"' % VAI in ma:
			xau.append("%s chép chuỗi thay vì import" % tep)
	la("không mô đun nào chép chuỗi", xau, [])


# ------------------------------------------- cua ke toan phai van dong

@ca("vai quản lý cửa hàng KHÔNG lọt vào cửa kế toán và sổ sách nào")
def _():
	"""Ca kiem quan trong nhat cua tep nay.

	Anh Viet 24/08/2026: "xem con quyen gi chua mo thi em mo het cho ban
	ay luon". Em mo phan VAN HANH, va co y KHONG mo phan ke toan: quan ly
	cua hang khong phai ke toan, va hai cua hoa don thi cham toi hoa don
	dien tu da gui co quan thue - dung dieu 11.

	Neu sau nay anh Viet quyet mo them thi sua danh sach o day truoc, roi
	ca kiem se noi cho biet con cho nao chua dong bo.
	"""
	lot = []
	for tep, ten in CUA_KE_TOAN:
		if "VAI_QLCH" in _khoi_hang_so(tep, ten):
			lot.append("%s.%s" % (tep, ten))
	la("không cửa kế toán nào bị mở", lot, [])


# ------------------------------------------------ ham dung vai an toan

@ca("hàm dựng vai chỉ thêm, không bao giờ bớt")
def _():
	ma = _doc("vai_cua_hang.py")
	# Bot vai la lay mat quyen cua nguoi dang lam viec. Ho so nay co the
	# da duoc ai do them vai bang tay tren Desk.
	for cam in ('.remove(', 'roles = [', 'set("roles"'):
		dung("không có %s" % cam, cam not in ma)
	dung("chỉ append thêm", 'append("roles"' in ma)


@ca("hàm dựng vai chạy lại được nhiều lần mà không đổi gì thêm")
def _():
	ma = _doc("vai_cua_hang.py")
	dung("có kiểm tồn tại trước khi tạo vai", 'exists("Role", VAI_QLCH)' in ma)
	dung("thiếu rỗng thì thoát sớm", "if not thieu:" in ma)


@ca("có lưu lại người dùng sau khi thêm vai vào hồ sơ")
def _():
	# Bang roles cua User duoc validate() dung lai TU HO SO moi lan luu.
	# Them vai vao ho so ma khong luu lai User thi phien lam viec cua ho
	# van chua co vai moi.
	ma = _doc("vai_cua_hang.py")
	dung("có hàm lưu lại người dùng", "def _luu_lai_nguoi_dung(" in ma)
	dung("lọc đúng người theo hồ sơ", '"role_profile_name": HO_SO_NHAN' in ma)
	dung("chỉ gọi khi thật sự có thêm vai", "if them:" in ma)


@ca("hàm dựng vai không bao giờ làm hỏng after_migrate")
def _():
	# Hong o day la hong ca lan deploy, ma phan quyen thi sua tay tren
	# Desk van duoc. Khong dang danh doi.
	ma = _doc("vai_cua_hang.py")
	than = ma.split("def dung(")[1].split("\ndef ")[0]
	dung("có lưới đỡ", "except Exception:" in than)
	dung("lỗi ghi vào Error Log", "log_error" in than)
	dung("được gọi từ after_migrate", "vai_cua_hang.dung()" in _doc("truong_tu_them.py"))
