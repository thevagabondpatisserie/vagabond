"""v645: giảm 50.000 đ cho đơn đầu tiên đặt qua web của một số điện thoại.

Anh Việt 08/11/2026 (duyệt mẫu cùng ngày): "giảm 50k cho đơn hàng đầu tiên của
số điện thoại đó đặt qua web, bắt nhập OTP ... Anh không muốn nhân viên
marketing chăm lo mấy cái mục này nữa, AI sẽ tự làm". Anh chốt ba điều:
- Đơn đầu tiên là số đó CHƯA TỪNG có đơn web (đơn đã huỷ không tính); khách
  từng mua ở quầy hay qua Pancake vẫn được giảm lần đầu đặt web.
- Không cộng với mã ưu đãi khác: máy so, giữ cái giảm nhiều hơn.
- Tiền bánh từ 300.000 đ.

Không phải chương trình khuyến mãi trong ERP: không mã, không lượt. Xác thực
số dùng đúng phiên Thành viên (mã Zalo, cookie
vgb_thanh_vien sống 30 ngày, thanh_vien.gui_ma và xac_thuc), không có cửa OTP
thứ hai; số trên đơn phải trùng số của phiên.

"Một lần" dựa vào bản ghi đơn web: đơn tạo xong là số đó đã có đơn web. Hai
đơn cùng số gửi cùng lúc thì don_hang.tao_don khoá theo số và xét lại ngay
trước khi ghi bản ghi.

Anh Việt 08/11/2026 (sau khi xem bản đầu): thêm công tắc trong màn Khuyến mãi
của app, chọn chỗ hiển thị (thẻ ở bước thanh toán, thẻ trên trang Ưu đãi) và
chọn có bắt xác thực số bằng mã Zalo hay không. Cài đặt nằm trong một ô ẩn của
Cài đặt Vagabond (`O_CAI_DAT`, JSON), sửa ở app: Bán hàng, Khuyến mãi.

Phép THUẦN tách khỏi phần chạm Frappe để kiểm không cần site.
"""

import json

GIAM = 50000
TOI_THIEU = 300000
TEN = "Ưu đãi đơn đầu tiên trên web"
O_CAI_DAT = "vgb_don_dau_web"

# Mặc định đúng bản anh Việt duyệt mẫu: đang chạy, giảm 50.000 đ cho tiền bánh
# từ 300.000 đ, bắt xác thực mã Zalo, hiện ở bước thanh toán và trang Ưu đãi.
MAC_DINH = {"bat": 1, "giam": GIAM, "toi_thieu": TOI_THIEU, "can_otp": 1,
	"hien_thanh_toan": 1, "hien_uu_dai": 1}
GIAM_MIN, GIAM_MAX = 1000, 1000000
TOI_THIEU_MAX = 20000000

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


def _co(v):
	"""Ô bật tắt người gửi lên: 1, "1", True, "true", "co" là bật. THUẦN."""
	if isinstance(v, str):
		return v.strip().lower() in ("1", "true", "co", "có", "yes", "on")
	try:
		return bool(int(v or 0))
	except (TypeError, ValueError):
		return False


def _so(v):
	"""Số tiền người gõ: 50000, "50.000", "50,000 đ" đều ra 50000; không đọc
	được thì None. THUẦN."""
	if isinstance(v, bool):
		return None
	if isinstance(v, (int, float)):
		return int(v)
	x = "".join(ch for ch in str(v or "") if ch.isdigit())
	return int(x) if x else None


def chuan(x=None, nghiem=False):
	"""Cài đặt ưu đãi đơn đầu tiên đã làm sạch. `x` là dict hay chuỗi JSON (ô
	lưu trên site), thiếu ô nào lấy mặc định ô đó. `nghiem`: lúc LƯU thì số sai
	báo ValueError bằng câu đọc được; lúc ĐỌC thì lặng lẽ về mặc định (ô hỏng
	không được làm gãy trang đặt bánh). Bắt mã Zalo thì thẻ ở bước thanh toán
	luôn hiện, vì khách xác thực ngay trong thẻ đó. THUẦN."""
	if isinstance(x, str):
		try:
			x = json.loads(x or "{}")
		except ValueError:
			if nghiem:
				raise ValueError("Cài đặt ưu đãi đơn đầu tiên không đọc được. Tải lại màn rồi lưu lại.")
			x = {}
	if not isinstance(x, dict):
		x = {}
	ra = dict(MAC_DINH)
	for k in ("bat", "can_otp", "hien_thanh_toan", "hien_uu_dai"):
		if k in x:
			ra[k] = 1 if _co(x[k]) else 0
	giam = _so(x["giam"]) if "giam" in x else GIAM
	toi = _so(x["toi_thieu"]) if "toi_thieu" in x else TOI_THIEU
	loi = ""
	if giam is None or not GIAM_MIN <= giam <= GIAM_MAX:
		loi = "Mức giảm từ 1.000 đ tới 1.000.000 đ."
	elif toi is None or not 0 <= toi <= TOI_THIEU_MAX:
		loi = "Tiền bánh tối thiểu từ 0 tới 20.000.000 đ."
	elif toi <= giam:
		loi = "Tiền bánh tối thiểu phải lớn hơn mức giảm, để đơn không bao giờ âm tiền."
	if loi:
		if nghiem:
			raise ValueError(loi)
		giam, toi = GIAM, TOI_THIEU
	ra["giam"], ra["toi_thieu"] = int(giam), int(toi)
	if ra["can_otp"]:
		ra["hien_thanh_toan"] = 1
	return ra


def trang_thai(sdt, da_dat_web, sdt_phien, tien_banh, otp_mo, ch=None):
	"""Trạng thái ưu đãi đơn đầu tiên của một giỏ. THUẦN.

	Tắt ưu đãi thì KHONG. Không bắt mã Zalo thì số khách gõ chưa có đơn web là
	đủ, không cần phiên Thành viên, không cần cấu hình gửi mã."""
	ch = chuan(ch)
	x = chin_so(sdt)
	if not ch["bat"] or not x or da_dat_web:
		return KHONG
	if ch["can_otp"] and not otp_mo:
		return CHUA_MO
	if int(tien_banh or 0) < ch["toi_thieu"]:
		return CHUA_DU_TIEN
	if ch["can_otp"] and chin_so(sdt_phien) != x:
		return CAN_XAC_THUC
	return DU


def tron(uu, tt, co_ma, giam=GIAM):
	"""Ghép ưu đãi đơn đầu tiên với ưu đãi của mã hay chương trình tự áp: không
	cộng, giữ cái giảm nhiều hơn (bằng nhau thì giữ mã khách gõ, khỏi tốn
	một lần đầu). Trả (ưu đãi dùng, cờ bỏ mã). THUẦN.

	`uu` là kết quả khuyen_mai.ap_web; mã sai (ly_do) thì giữ nguyên để trang
	báo lỗi mã như cũ."""
	uu = dict(uu or {})
	if tt != DU or uu.get("ly_do"):
		return uu, False
	giam = int(giam or 0)
	if giam <= 0 or int(uu.get("tong_giam") or 0) >= giam:
		return uu, False
	ra = {"tong_giam": giam, "ap": [{"ma": "", "ten": TEN, "giam": giam, "dien_giai": "", "don_dau": 1}],
		"ma": "", "ly_do": "", "kq": None, "don_dau": 1}
	return ra, bool(co_ma)


def phan_hoi(tt, ch=None):
	"""Phần don_dau trả cho trang: trạng thái, số tiền, có bắt mã Zalo không,
	có hiện thẻ ở bước thanh toán không. THUẦN."""
	ch = chuan(ch)
	return {"trang_thai": tt, "giam": ch["giam"], "toi_thieu": ch["toi_thieu"],
		"can_otp": ch["can_otp"], "hien": ch["hien_thanh_toan"]}


def tien(n):
	"""50000 -> "50.000đ", cùng cách khuyen_mai.mo_ta_muc_giam. THUẦN."""
	return "{:,}".format(int(n or 0)).replace(",", ".") + "đ"


def the_uu_dai(ch=None):
	"""Thẻ trên trang Ưu đãi (cùng dạng khuyen_mai.the_web: dòng đầu điều kiện
	là mức giảm). Tắt ưu đãi hay không chọn chỗ hiển thị này thì None. THUẦN."""
	ch = chuan(ch)
	if not ch["bat"] or not ch["hien_uu_dai"]:
		return None
	dk = ["Giảm " + tien(ch["giam"]),
		"Chỉ áp cho đơn đầu tiên đặt trên web của mỗi số điện thoại."]
	if ch["can_otp"]:
		dk.append("Xác thực số điện thoại bằng mã Zalo ở bước thanh toán.")
	dk.append("Không cộng chung với mã ưu đãi khác; máy giữ mức giảm lớn hơn.")
	return {
		"id": "don-dau-web", "loai": "uu_dai", "vi_tri": "uu_dai", "hien": True, "nguon": "erp",
		"tieu_de": TEN, "noi_dung": "Lần đầu đặt bánh trên web, quý khách được giảm " + tien(ch["giam"]) + ".",
		"anh": "", "mo_ta_anh": TEN, "nhom": "Ưu đãi", "ma_uu_dai": "",
		"don_toi_thieu": ch["toi_thieu"] or "", "bat_dau": "", "ket_thuc": "",
		"gio_bat_dau": "", "gio_ket_thuc": "", "dieu_kien": "\n".join(dk), "dung_web": 1,
	}


def dong_bien_tap(ch=None):
	"""Dòng cho danh sách ưu đãi của trình biên tập web (cùng dạng
	khuyen_mai.ds_web_bien_tap): Marketing thấy ưu đãi này đang hiện hay không
	và biết sửa ở đâu. THUẦN."""
	ch = chuan(ch)
	the = the_uu_dai(dict(ch, bat=1, hien_uu_dai=1))
	if not ch["bat"]:
		tt = "Đang tắt trong app, khách không thấy"
	elif not ch["hien_uu_dai"]:
		tt = "Không hiện trên trang Ưu đãi" + (" (vẫn hiện ở bước thanh toán)" if ch["hien_thanh_toan"] else "")
	else:
		tt = "Khách đang thấy"
	return dict(the, ma_ctkm="", khach_thay=1 if (ch["bat"] and ch["hien_uu_dai"]) else 0, trang_thai_erp=tt)


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


def doc_o():
	"""Chuỗi đang lưu trong ô cài đặt, đọc thẳng bảng Singles (ô vừa ghi đọc
	lại được ngay, kể cả trước khi migrate tạo ô). Chưa từng lưu thì rỗng.
	KHÔNG nuốt lỗi như lib.cfg_o (Codex #548): đọc hỏng phải nổi lên để
	cau_hinh coi như tắt, không lẫn với "chưa lưu" rồi chạy theo mặc định."""
	import frappe

	ds = frappe.db.sql("select value from `tabSingles` where doctype=%s and field=%s",
		("Vagabond Settings", O_CAI_DAT))
	return (ds[0][0] or "") if ds else ""


def cau_hinh():
	"""Cài đặt đang dùng. Ô chưa lưu thì mặc định bản duyệt mẫu; đọc lỗi thì
	coi như TẮT: không bao giờ cho giảm oan."""
	import frappe

	try:
		return chuan(doc_o())
	except Exception:
		frappe.log_error(title="Vagabond: đọc cài đặt ưu đãi đơn đầu", message=frappe.get_traceback())
		return chuan({"bat": 0})


def xet(sdt, tien_banh, ch=None):
	"""Trạng thái ưu đãi đơn đầu tiên của số này, đọc site."""
	ch = cau_hinh() if ch is None else chuan(ch)
	x = chin_so(sdt)
	if not x or not ch["bat"]:
		return KHONG
	return trang_thai(sdt, da_dat_web(sdt), sdt_phien() if ch["can_otp"] else "", tien_banh,
		otp_mo() if ch["can_otp"] else True, ch)


def khoa_so(sdt):
	"""Khoá tệp theo số: hai đơn cùng số gửi cùng lúc thì đơn sau chờ đơn trước
	ghi xong bản ghi, rồi xét lại thì thấy số đã có đơn web."""
	from frappe.utils.synchronization import filelock

	return filelock("vgb_don_dau_" + (chin_so(sdt) or "x"), timeout=20)


# ------------------------------------------------------------- cửa cho app

import frappe  # noqa: E402


@frappe.whitelist()
def doc_cai_dat():
	"""Màn Khuyến mãi trong app: cài đặt hiện tại và gửi mã Zalo đã mở chưa."""
	from vagabond import khuyen_mai

	khuyen_mai._kiem_quyen()
	return {"cai_dat": cau_hinh(), "otp_mo": 1 if otp_mo() else 0, "mac_dinh": dict(MAC_DINH)}


@frappe.whitelist()
def luu_cai_dat(cai_dat=None):
	"""Lưu cài đặt từ app. Cùng quyền sửa chương trình khuyến mãi. Số sai báo
	câu đọc được, không lưu."""
	from vagabond import khuyen_mai

	khuyen_mai._kiem_quyen_sua()
	try:
		ch = chuan(cai_dat, nghiem=True)
	except ValueError as e:
		frappe.throw(str(e))
	frappe.db.set_single_value("Vagabond Settings", O_CAI_DAT, json.dumps(ch, ensure_ascii=False, sort_keys=True))
	frappe.db.commit()
	return {"cai_dat": ch, "otp_mo": 1 if otp_mo() else 0}
