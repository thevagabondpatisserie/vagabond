"""v645: giảm 50.000 đ cho đơn đầu tiên đặt qua web của một số điện thoại.

Anh Việt 08/11/2026 (duyệt mẫu cùng ngày): "giảm 50k cho đơn hàng đầu tiên của
số điện thoại đó đặt qua web, bắt nhập OTP ... Anh không muốn nhân viên
marketing chăm lo mấy cái mục này nữa, AI sẽ tự làm". Anh chốt ba điều:
- Đơn đầu tiên là số đó CHƯA TỪNG có đơn web (đơn đã huỷ không tính); khách
  từng mua ở quầy hay qua Pancake vẫn được giảm lần đầu đặt web.
- Không cộng với mã ưu đãi khác: máy so, giữ cái giảm nhiều hơn.
- Tiền bánh từ 300.000 đ.

Không phải chương trình khuyến mãi trong ERP: không mã, không lượt, không ai
phải bật tắt. Xác thực số dùng đúng phiên Thành viên (mã Zalo, cookie
vgb_thanh_vien sống 30 ngày, thanh_vien.gui_ma và xac_thuc), không có cửa OTP
thứ hai; số trên đơn phải trùng số của phiên.

"Một lần" dựa vào bản ghi đơn web: đơn tạo xong là số đó đã có đơn web. Hai
đơn cùng số gửi cùng lúc thì don_hang.tao_don khoá theo số và xét lại ngay
trước khi ghi bản ghi.

Phép THUẦN tách khỏi phần chạm Frappe để kiểm không cần site.
"""

GIAM = 50000
TOI_THIEU = 300000
TEN = "Ưu đãi đơn đầu tiên trên web"

# Trạng thái trả cho trang đặt bánh (kho-banh.js đọc đúng các chữ này).
KHONG = "khong"                 # đã có đơn web, hay số chưa đủ: không hiện thẻ
CHUA_MO = "chua_mo"             # chưa cấu hình gửi mã Zalo: không hiện thẻ
CHUA_DU_TIEN = "chua_du_tien"   # tiền bánh dưới ngưỡng: thẻ nói còn thiếu
CAN_XAC_THUC = "can_xac_thuc"   # đủ điều kiện, chưa xác thực số
DU = "du"                       # đã xác thực đúng số: được giảm

# Đơn web ở các trạng thái này vẫn tính là "đã đặt web".
TRANG_THAI_HUY = "Da huy"


def chin_so(s):
	"""Chín chữ số cuối của một số di động Việt Nam, rỗng khi không đọc được.
	Cùng cách lib.sdt_so: 0901234567, 84901234567, +84 901 234 567 là một. THUẦN."""
	x = "".join(ch for ch in str(s or "") if ch.isdigit())
	if x.startswith("84") and len(x) == 11:
		x = x[2:]
	elif x.startswith("0") and len(x) == 10:
		x = x[1:]
	return x if len(x) == 9 else ""


def bien_the(s):
	"""Các cách số đó có thể nằm trong ô dien_thoai của đơn web (lưu nguyên chữ
	số khách gõ). THUẦN."""
	x = chin_so(s)
	return sorted({"0" + x, "84" + x, x}) if x else []


def trang_thai(sdt, da_dat_web, sdt_phien, tien_banh, otp_mo):
	"""Trạng thái ưu đãi đơn đầu tiên của một giỏ. THUẦN."""
	x = chin_so(sdt)
	if not x or da_dat_web:
		return KHONG
	if not otp_mo:
		return CHUA_MO
	if int(tien_banh or 0) < TOI_THIEU:
		return CHUA_DU_TIEN
	if chin_so(sdt_phien) != x:
		return CAN_XAC_THUC
	return DU


def tron(uu, tt, co_ma):
	"""Ghép ưu đãi đơn đầu tiên với ưu đãi của mã hay chương trình tự áp: không
	cộng, giữ cái giảm nhiều hơn (bằng nhau thì giữ mã khách gõ, khỏi tốn
	một lần đầu). Trả (ưu đãi dùng, cờ bỏ mã). THUẦN.

	`uu` là kết quả khuyen_mai.ap_web; mã sai (ly_do) thì giữ nguyên để trang
	báo lỗi mã như cũ."""
	uu = dict(uu or {})
	if tt != DU or uu.get("ly_do"):
		return uu, False
	if int(uu.get("tong_giam") or 0) >= GIAM:
		return uu, False
	ra = {"tong_giam": GIAM, "ap": [{"ma": "", "ten": TEN, "giam": GIAM, "dien_giai": "", "don_dau": 1}],
		"ma": "", "ly_do": "", "kq": None, "don_dau": 1}
	return ra, bool(co_ma)


def phan_hoi(tt):
	"""Phần don_dau trả cho trang. THUẦN."""
	return {"trang_thai": tt, "giam": GIAM, "toi_thieu": TOI_THIEU}


# ------------------------------------------------------------------ chạm hệ

def da_dat_web(sdt):
	import frappe

	ds = bien_the(sdt)
	if not ds:
		return False
	return bool(frappe.db.exists("Vagabond Don Web", {"dien_thoai": ["in", ds], "trang_thai": ["!=", TRANG_THAI_HUY]}))


def sdt_phien():
	"""Số của phiên Thành viên đang mở trên trình duyệt này, rỗng khi chưa đăng
	nhập. Lỗi đọc thì coi như chưa đăng nhập (không bao giờ cho giảm oan)."""
	import frappe

	try:
		from vagabond import thanh_vien

		return thanh_vien._so_phien() or ""
	except Exception:
		frappe.log_error(title="Vagabond: đọc phiên thành viên cho ưu đãi đơn đầu", message=frappe.get_traceback())
		return ""


def otp_mo():
	from vagabond.lib import cfg

	return bool((cfg().get("zns_template_otp") or "").strip())


def xet(sdt, tien_banh):
	"""Trạng thái ưu đãi đơn đầu tiên của số này, đọc site."""
	x = chin_so(sdt)
	if not x:
		return KHONG
	return trang_thai(sdt, da_dat_web(sdt), sdt_phien(), tien_banh, otp_mo())


def khoa_so(sdt):
	"""Khoá tệp theo số: hai đơn cùng số gửi cùng lúc thì đơn sau chờ đơn trước
	ghi xong bản ghi, rồi xét lại thì thấy số đã có đơn web."""
	from frappe.utils.synchronization import filelock

	return filelock("vgb_don_dau_" + (chin_so(sdt) or "x"), timeout=20)
