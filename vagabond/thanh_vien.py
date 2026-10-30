"""#245: màn thành viên dùng phiên OTP của Claude và sổ điểm thật tại quầy.

Cookie HttpOnly giữ vé phiên ngoài JavaScript; dữ liệu khách luôn lấy từ
số đã xác thực, không nhận mã Customer từ trình duyệt.

v621 (anh Việt 30/10/2026): trang thành viên mới (ảnh đại diện, hồ sơ, ví quà,
mã thành viên) và quà chào mừng tại quầy: khách quét mã ở quầy, xác minh số
qua Zalo, khai tên, ngày sinh, đồng ý nhận tin Zalo, nhận ngay một mã giảm
(chương trình khuyen_mai.CTKM_QUA). Mã dùng ngay trên hoá đơn đang tính, không
dùng trong ngày thì còn dùng được trong 7 ngày. Mỗi số điện thoại nhận một
lần, cả khách cũ.

Phép THUẦN (chuẩn hoá ô khách gõ, đọc ảnh, đếm hồ sơ) tách khỏi phần chạm
Frappe để kiểm không cần site.
"""
import base64
import binascii
import json
import re
import secrets
from datetime import date

import frappe
from frappe.rate_limiter import rate_limit
from vagabond.lib import cfg, key

COOKIE = 'vgb_thanh_vien'

# Quà chào mừng: dùng ngay hôm nay hoặc trong 7 ngày tới (anh Việt 30/10/2026).
QUA_SO_NGAY = 7
# Ngày sinh không khai năm thì lưu năm nhuận này (vgb_sinh_nhat là ô Date);
# kịch bản sinh nhật chỉ đọc ngày và tháng, màn không hiện năm này.
NAM_AN = 1904
# Hình bánh có sẵn làm ảnh đại diện (ảnh nằm trong web_order, không tải lên).
ANH_MAU = ('croissant', 'entremet', 'lop-banh', 'quay')
# Món hay chọn: mã lưu và chữ hiện. Thứ tự là thứ tự trên màn.
SO_THICH = (
	('croissant', 'Croissant và bánh mì'),
	('entremet', 'Entremet'),
	('banh_kem', 'Bánh kem sinh nhật'),
	('tart', 'Tart'),
	('do_uong', 'Đồ uống'),
)
# Ảnh đại diện máy khách đã thu về 512 px JPEG; vài chục KB là đủ.
ANH_TOI_DA = 400 * 1024
CAU_HOI_TV = (
	"Đồng ý nhận tin từ The Vagabond Pâtisserie qua Zalo: quà sinh nhật, voucher, "
	"báo đơn bánh. Tắt lúc nào cũng được trong trang thành viên."
)
DT_HO_SO = "Vagabond Ho So CRM"
VI_LICH_SU = 20      # số mã đã dùng/hết hạn/đã huỷ hiện trong Ví quà
VI_CON_TOI_DA = 200  # trần an toàn cho mã chưa dùng của một khách
COT_TV = ("ten_goi", "email_khach", "so_thich", "anh_dai_dien", "anh_mau", "dy_zalo", "qua_chao_mung")


# ------------------------------------------------------------------ THUẦN

def chuan_ten(s):
	"""Tên khách tự gõ. THUẦN. Trả (tên, lỗi)."""
	t = re.sub(r"\s+", " ", str(s or "")).strip()
	if not t:
		return "", "thieu_ten"
	if len(t) > 60 or not re.search(r"[^\W\d_]", t):
		return "", "ten_khong_dung"
	return t, ""


def ten_that(ten):
	"""Tên trên hồ sơ khách, bỏ tên máy tự đặt khi dựng khách lẻ ("Khách 3412",
	nhap_khach._tao_mot) để ô tên trên trang không điền sẵn tên giả. THUẦN."""
	t = str(ten or "").strip()
	return "" if re.fullmatch(r"Khách \d{4}", t) else t


def chuan_sinh_nhat(ngay, thang, nam=None, hom_nay=None):
	"""Ngày sinh từ ba ô. THUẦN. Trả (date hoặc None, lỗi).

	Năm không bắt buộc: để trống thì lưu NAM_AN (năm nhuận, nhận được 29/02).
	Ô người gõ là đầu vào không tin được: nhận "05", " 5 ", 5; năm phải là năm
	sinh hợp lý (không sau hôm nay, không trước 1920).
	"""
	def so(x):
		x = str(x if x is not None else "").strip()
		return int(x) if re.fullmatch(r"\d{1,4}", x) else None
	d, m, y = so(ngay), so(thang), so(nam)
	if d is None and m is None and not str(nam or "").strip():
		return None, ""
	if d is None or m is None:
		return None, "ngay_sinh_thieu"
	if str(nam or "").strip() and y is None:
		return None, "ngay_sinh_khong_dung"
	hn = hom_nay or date.today()
	if y is not None and not (1920 <= y <= hn.year):
		return None, "ngay_sinh_khong_dung"
	try:
		ra = date(y or NAM_AN, m, d)
	except ValueError:
		return None, "ngay_sinh_khong_dung"
	if y is not None and ra > hn:
		return None, "ngay_sinh_khong_dung"
	return ra, ""


def hien_sinh_nhat(v):
	"""{ngay, thang, nam} cho ô trên màn. THUẦN. Năm ẩn (NAM_AN) thì để trống."""
	if not v:
		return {"ngay": "", "thang": "", "nam": ""}
	if not isinstance(v, date):
		try:
			v = date.fromisoformat(str(v)[:10])
		except ValueError:
			return {"ngay": "", "thang": "", "nam": ""}
	return {"ngay": v.day, "thang": v.month, "nam": "" if v.year == NAM_AN else v.year}


def chuan_email(s):
	"""Email không bắt buộc. THUẦN. Trả (email, lỗi)."""
	e = str(s or "").strip().lower()
	if not e:
		return "", ""
	if len(e) > 140 or not re.fullmatch(r"[^@\s,;<>]+@[^@\s,;<>]+\.[a-z]{2,}", e):
		return "", "email_khong_dung"
	return e, ""


def chuan_so_thich(ds):
	"""Danh sách món hay chọn: chỉ giữ mã đã biết, không trùng, đúng thứ tự màn. THUẦN."""
	if isinstance(ds, str):
		try:
			ds = json.loads(ds)
		except ValueError:
			ds = [x for x in ds.split(",")]
	co = {str(x).strip() for x in (ds or []) if str(x).strip()}
	return [m for m, _ in SO_THICH if m in co]


def doc_anh(du_lieu):
	"""Ảnh đại diện máy khách gửi lên dạng data URL JPEG. THUẦN.

	Trả (bytes, lỗi). Chỉ nhận JPEG thật (đọc ba byte đầu, không tin phần đuôi
	tên hay kiểu khai), tối đa ANH_TOI_DA.
	"""
	s = str(du_lieu or "")
	m = re.fullmatch(r"data:image/jpeg;base64,([A-Za-z0-9+/=\s]+)", s)
	if not m:
		return None, "anh_khong_dung"
	if len(m.group(1)) > ANH_TOI_DA * 4 // 3 + 16:
		return None, "anh_qua_lon"
	try:
		raw = base64.b64decode(re.sub(r"\s", "", m.group(1)), validate=True)
	except (binascii.Error, ValueError):
		return None, "anh_khong_dung"
	if len(raw) > ANH_TOI_DA:
		return None, "anh_qua_lon"
	if not raw.startswith(b"\xff\xd8\xff"):
		return None, "anh_khong_dung"
	return raw, ""


def muc_ho_so(hs):
	"""Hồ sơ đã khai được mấy mục và còn thiếu gì để nhận quà. THUẦN.

	hs: {ten, sinh_nhat, dong_y, anh, so_thich}. Quà cần đủ ba mục bắt buộc:
	tên, ngày sinh, đồng ý nhận tin Zalo (anh Việt 30/10/2026).
	"""
	hs = hs or {}
	muc = [("ten", bool(hs.get("ten"))), ("sinh_nhat", bool(hs.get("sinh_nhat"))), ("dong_y", bool(hs.get("dong_y"))),
		("anh", bool(hs.get("anh"))), ("so_thich", bool(hs.get("so_thich")))]
	return {
		"du": sum(1 for _, co in muc if co),
		"tong": len(muc),
		"thieu_qua": [k for k, co in muc[:3] if not co],
	}


def trang_thai_voucher(v, hom_nay):
	"""Một mã trong ví: dung_duoc, da_dung, het_han, da_huy. THUẦN."""
	tt = (v or {}).get("trang_thai") or ""
	if tt == "Da dung":
		return "da_dung"
	if tt == "Da huy":
		return "da_huy"
	han = (v or {}).get("han_dung")
	if han:
		if not isinstance(han, date):
			try:
				han = date.fromisoformat(str(han)[:10])
			except ValueError:
				han = None
		if han and han < hom_nay:
			return "het_han"
	return "dung_duoc"


# ------------------------------------------------------------------ chạm hệ

def _dn():
	"""dang_nhap kéo requests: nạp trong thân hàm để mô đun nạp được ở máy CI
	không có requests (ca kiểm thuần chạy không cần mạng)."""
	from vagabond import dang_nhap

	return dang_nhap


def _khong_cache():
	frappe.local.response_headers['Cache-Control'] = 'private, no-store'


def _hom_nay():
	from frappe.utils import getdate, nowdate

	return getdate(nowdate())


def _so_phien():
	return _dn()._phien(frappe.request.cookies.get(COOKIE))


def _khach_cua_so(noi_dia):
	"""Khách của số đã xác thực. Trả (khach_dict, lý do). Nhiều hồ sơ cùng số
	thì không đoán, để cửa hàng đối chiếu."""
	ds = frappe.get_all('Customer', filters={'mobile_no': noi_dia, 'disabled': 0},
		fields=['name', 'customer_name', 'vgb_hang', 'vgb_sinh_nhat', 'creation'], limit_page_length=2)
	if len(ds) > 1:
		return None, 'can_doi_chieu'
	return (ds[0] if ds else None), ''


def _ho_so_tv(khach):
	"""Phần trang thành viên của hồ sơ CRM (đọc, không tạo)."""
	return frappe.db.get_value(DT_HO_SO, khach, list(COT_TV), as_dict=True) or {}


def _anh_data_url(duong):
	"""Ảnh đại diện riêng tư trả về dạng data URL (chỉ cho chính chủ qua toi)."""
	if not duong:
		return ""
	try:
		ten = frappe.db.get_value("File", {"file_url": duong}, "name")
		if not ten:
			return ""
		raw = frappe.get_doc("File", ten).get_content()
		if isinstance(raw, str):
			raw = raw.encode("latin-1")
		if not raw or len(raw) > ANH_TOI_DA or not raw.startswith(b"\xff\xd8\xff"):
			return ""
		return "data:image/jpeg;base64," + base64.b64encode(raw).decode()
	except Exception:
		return ""


def _ctkm_qua():
	from vagabond import khuyen_mai

	return frappe.db.get_value("Vagabond CTKM", khuyen_mai.CTKM_QUA,
		["name", "ten", "cach_ma", "bat", "kieu_giam", "gia_tri", "hd_toi_thieu", "tu_ngay", "den_ngay", "han_ma"],
		as_dict=True)


def _mo_ta_ma(km_cache, ctkm):
	from vagabond.zalo_kich_ban import mo_ta_uu_dai

	if ctkm not in km_cache:
		km_cache[ctkm] = frappe.db.get_value("Vagabond CTKM", ctkm,
			["name", "ten", "kieu_giam", "gia_tri", "hd_toi_thieu"], as_dict=True) or {}
	return mo_ta_uu_dai(km_cache[ctkm])


def _vi(khach, hom_nay):
	from vagabond.zalo_kich_ban import ngay_vn

	cot = ["ma", "ctkm", "ten_ctkm", "trang_thai", "han_dung", "ngay_dung"]
	# Mã CHƯA DÙNG lấy riêng, không cắt theo 20 mã mới nhất: khách nhiều mã
	# đã dùng hay đã huỷ (tin Zalo thử lại phát rồi huỷ) không được đẩy mã còn
	# hạn ra khỏi ví (Codex PR #517 vòng 11). Chỉ phần lịch sử bị giới hạn.
	con = frappe.get_all("Vagabond Voucher", filters={"danh_cho": khach, "trang_thai": "Chua dung"},
		fields=cot, order_by="creation desc", limit_page_length=VI_CON_TOI_DA)
	cu = frappe.get_all("Vagabond Voucher", filters={"danh_cho": khach, "trang_thai": ["!=", "Chua dung"]},
		fields=cot, order_by="creation desc", limit_page_length=VI_LICH_SU)
	ds = list(con) + list(cu)
	km, ra = {}, []
	for v in ds:
		ten_ud, dk = _mo_ta_ma(km, v.ctkm)
		ra.append({"ma": v.ma, "ten": v.ten_ctkm or "", "uu_dai": ten_ud, "dieu_kien": dk,
			"han": ngay_vn(v.han_dung) if v.han_dung else "", "trang_thai": trang_thai_voucher(v, hom_nay),
			"ngay_dung": ngay_vn(v.ngay_dung) if v.ngay_dung else ""})
	# Dùng được lên đầu, rồi sắp mở/đã dùng.
	thu_tu = {"dung_duoc": 0, "da_dung": 1, "het_han": 2, "da_huy": 3}
	ra.sort(key=lambda x: thu_tu.get(x["trang_thai"], 9))
	# Mã dùng được giữ đủ; lịch sử (đã dùng, hết hạn, đã huỷ) tối đa VI_LICH_SU.
	dung = [x for x in ra if x["trang_thai"] == "dung_duoc"]
	return dung + [x for x in ra if x["trang_thai"] != "dung_duoc"][:VI_LICH_SU]


def _tien_do(khach):
	from vagabond import khach_hang

	bang = [h for h in (khach_hang.bang_hang().get("hang") or []) if (h.get("loai") or "Theo chi tieu") == "Theo chi tieu"]
	so_thang = max([int(h.get("so_thang_xet") or 12) for h in bang] or [12])
	tien = float((khach_hang._chi_tieu([khach], so_thang).get(khach) or {}).get("tien") or 0)
	td = khach_hang.tien_do_hang(bang, tien)
	ten_tiep = ""
	if td["tiep"]:
		ten_tiep = frappe.db.get_value("Vagabond Hang Khach", td["tiep"], "ten_hang") or td["tiep"]
	return {"da_mua": tien, "so_thang": so_thang, "hang_tiep": ten_tiep, "con_thieu": td["con_thieu"],
		"ty_le": td["ty_le"]}


@frappe.whitelist(allow_guest=True)
def san_sang():
	ra = {'otp':bool(cfg().get('zns_template_otp')), 'qua':{'mo':0, 'uu_dai':''}}
	# v621: trang quà ở quầy và bảng in cần giá trị quà trước khi khách đăng
	# nhập. Chỉ đọc chương trình; lỗi đọc không được làm hỏng trang đăng nhập.
	try:
		from vagabond.zalo_kich_ban import ctkm_phat_duoc, mo_ta_uu_dai

		km = _ctkm_qua() or {}
		han, _ = ctkm_phat_duoc(km, _hom_nay(), QUA_SO_NGAY)
		ra['qua'] = {'mo':1 if han else 0, 'uu_dai':mo_ta_uu_dai(km)[0] if km else ''}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thanh_vien: đọc quà chào mừng")
	return ra


@frappe.whitelist(allow_guest=True, methods=['POST'])
@rate_limit(limit=12, seconds=600)
def gui_ma(sdt):
	if not cfg().get('zns_template_otp'):
		return {'ok':0, 'ly_do':'chua_mo'}
	r = _dn().gui_ma(sdt)
	return {'ok':r.get('ok',0), 'ly_do':r.get('ly_do',''), 'song_giay':r.get('song_giay',0)}


@frappe.whitelist(allow_guest=True, methods=['POST'])
@rate_limit(limit=30, seconds=600)
def xac_thuc(sdt, ma):
	r = _dn().xac_thuc(sdt, ma)
	if not r.get('ok'):
		return {'ok':0, 'ly_do':r.get('ly_do','ma_khong_dung')}
	# Frappe auth.CookieManager.set_cookie: không đặt domain, cookie chỉ ở
	# đúng hostname khách đăng nhập, không chia sẻ sang app/ERP subdomain.
	frappe.local.cookie_manager.set_cookie(COOKIE, r['token'], httponly=True,
		secure=True, samesite='Strict', max_age=_dn().PHIEN_SONG_NGAY*86400)
	_khong_cache()
	return {'ok':1}


@frappe.whitelist(allow_guest=True, methods=['POST'])
def thoat():
	_dn().thoat(frappe.request.cookies.get(COOKIE))
	frappe.local.cookie_manager.delete_cookie(COOKIE)
	_khong_cache()
	return {'ok':1}


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=30, seconds=600)
def toi():
	_khong_cache()
	so = _so_phien()
	if not so:
		return {'ok':0,'ly_do':'chua_dang_nhap'}
	noi_dia = _dn()._sdt_noi_dia(so)
	kh, ly = _khach_cua_so(noi_dia)
	if ly:
		return {'ok':0,'ly_do':ly}
	kh = kh or {}
	hang = frappe.db.get_value('Vagabond Hang Khach', kh.get('vgb_hang'),
		['ten_hang','anh','mo_ta','giam_gia','tich_diem'], as_dict=True) if kh.get('vgb_hang') else None
	from vagabond.diem_otp import _so_du
	diem = _so_du(kh['name']) if kh else 0
	c = cfg(); k = key(c, 'pancake_api_key')
	don, don_loi = [], False
	don_chua_mo = not (k and c.pancake_shop_id)
	if k and c.pancake_shop_id:
		try:
			don = _dn()._don_pancake(c, k, noi_dia, bao_loi=True)
			don_loi = False
		except Exception:
			# Điểm/hạng vẫn đọc được; lỗi nguồn đơn không được giả làm lịch sử rỗng.
			don_loi = True
	ra = {'ok':1, 'ten':kh.get('customer_name',''), 'sdt':noi_dia, 'hang':hang,
		'diem':diem, 'don':don, 'don_loi':don_loi, 'don_chua_mo':don_chua_mo, 'co_ho_so':bool(kh)}
	ra.update(_phan_moi(kh, noi_dia))
	return ra


def _phan_moi(kh, noi_dia):
	"""Phần v621 của toi(): hồ sơ, ảnh, ví quà, quà chào mừng, tiến độ hạng."""
	hn = _hom_nay()
	km = _ctkm_qua() or {}
	from vagabond.zalo_kich_ban import ctkm_phat_duoc, mo_ta_uu_dai, ngay_vn

	han_qua, _ = ctkm_phat_duoc(km, hn, QUA_SO_NGAY)
	qua = {"mo": 1 if han_qua else 0, "uu_dai": mo_ta_uu_dai(km)[0] if km else "", "han": ngay_vn(han_qua) if han_qua else "",
		"so_ngay": QUA_SO_NGAY, "da_nhan": 0}
	if not kh:
		hs = muc_ho_so({})
		return {"ho_so": {"ten": "", "sinh_nhat": hien_sinh_nhat(None), "email": "", "so_thich": [], "dong_y_zalo": 0,
			"anh_mau": ""}, "anh": "", "muc": hs, "vi": [], "qua": qua, "tien_do": None, "ma_tv": "", "tu_nam": ""}
	tv = _ho_so_tv(kh["name"])
	so_thich = chuan_so_thich(tv.get("so_thich"))
	anh = _anh_data_url(tv.get("anh_dai_dien"))
	ho_so = {"ten": tv.get("ten_goi") or ten_that(kh.get("customer_name")), "sinh_nhat": hien_sinh_nhat(kh.get("vgb_sinh_nhat")),
		"email": tv.get("email_khach") or "", "so_thich": so_thich,
		"dong_y_zalo": 1 if (tv.get("dy_zalo") or "") == "Đồng ý" else 0,
		"anh_mau": tv.get("anh_mau") if tv.get("anh_mau") in ANH_MAU else ""}
	muc = muc_ho_so({"ten": tv.get("ten_goi") or "", "sinh_nhat": kh.get("vgb_sinh_nhat"), "dong_y": ho_so["dong_y_zalo"],
		"anh": anh or ho_so["anh_mau"], "so_thich": so_thich})
	vi = _vi(kh["name"], hn)
	if _qua_da_cap(kh["name"], noi_dia, tv.get("qua_chao_mung")):
		qua["da_nhan"] = 1
	tao = kh.get("creation")
	return {"ho_so": ho_so, "anh": anh, "muc": muc, "vi": vi, "qua": qua, "tien_do": _tien_do(kh["name"]),
		"vi_cho": len(vi_du_dieu_kien(kh, noi_dia, hn)),
		"ma_tv": kh["name"], "tu_nam": str(tao)[:4] if tao else ""}


def _khach_hoac_tao(so, ten=""):
	"""Khách của phiên; chưa có hồ sơ thì dựng khách lẻ từ số đã xác thực."""
	noi_dia = _dn()._sdt_noi_dia(so)
	kh, ly = _khach_cua_so(noi_dia)
	if ly:
		return None, ly
	if kh:
		return kh["name"], ""
	from vagabond.nhap_khach import tao_khach_le, tim_theo_sdt

	# Số nằm ở danh bạ một khách khác (khách sỉ, người liên hệ) mà hồ sơ không
	# mang số này: không tự gắn và không dựng trùng, để cửa hàng đối chiếu.
	if tim_theo_sdt(noi_dia):
		return None, "can_doi_chieu"
	ma = tao_khach_le(noi_dia, ten)
	return (ma, "") if ma else (None, "khong_tao_duoc")


@frappe.whitelist(allow_guest=True, methods=['POST'])
@rate_limit(limit=20, seconds=600)
def luu_ho_so(dat=None):
	"""Khách tự sửa hồ sơ: tên gọi, ngày sinh, email, món hay chọn, hình bánh
	làm ảnh đại diện, đồng ý nhận tin Zalo. Chỉ hồ sơ của số đã xác thực."""
	_khong_cache()
	so = _so_phien()
	if not so:
		return {'ok':0, 'ly_do':'chua_dang_nhap'}
	dat = json.loads(dat) if isinstance(dat, str) else (dat or {})
	ten, loi = chuan_ten(dat.get("ten"))
	if loi:
		return {'ok':0, 'ly_do':loi}
	sn, loi = chuan_sinh_nhat(dat.get("ngay"), dat.get("thang"), dat.get("nam"), _hom_nay())
	if loi:
		return {'ok':0, 'ly_do':loi}
	email, loi = chuan_email(dat.get("email"))
	if loi:
		return {'ok':0, 'ly_do':loi}
	anh_mau = str(dat.get("anh_mau") or "").strip()
	if anh_mau and anh_mau not in ANH_MAU:
		return {'ok':0, 'ly_do':'anh_khong_dung'}
	khach, ly = _khach_hoac_tao(so, ten)
	if not khach:
		return {'ok':0, 'ly_do':ly}
	from vagabond import crm

	crm._ho_so(khach, tao=True)
	v = {"ten_goi": ten, "email_khach": email, "so_thich": json.dumps(chuan_so_thich(dat.get("so_thich")))}
	if anh_mau:
		cu = _ho_so_tv(khach).get("anh_dai_dien")
		_xoa_anh(cu)
		v.update({"anh_mau": anh_mau, "anh_dai_dien": ""})
	frappe.db.set_value(DT_HO_SO, khach, v, update_modified=True)
	if sn:
		frappe.db.set_value("Customer", khach, "vgb_sinh_nhat", sn, update_modified=False)
	elif "ngay" in dat and "thang" in dat:
		# Biểu mẫu gửi đủ ô mà cả ba trống: khách chủ động xoá ngày sinh, lưu
		# đúng như vậy chứ không giữ ngày cũ (Codex PR #517 vòng 12). Lời gọi
		# không gửi ô ngày sinh (chỉ đổi hình bánh) thì giữ nguyên.
		frappe.db.set_value("Customer", khach, "vgb_sinh_nhat", None, update_modified=False)
	_ghi_dong_y(khach, dat.get("dong_y_zalo"))
	frappe.db.commit()
	return {'ok':1}


def _ghi_dong_y(khach, dong_y):
	"""Ô đồng ý trên trang: tích là Đồng ý; bỏ tích chỉ ghi Từ chối khi trước đó
	đã Đồng ý (rút lại). Một chỗ ghi duy nhất có nhật ký: crm.ghi_dong_y_noi."""
	from vagabond import crm

	co = str(dong_y).strip().lower() in ("1", "true", "yes")
	cu = (frappe.db.get_value(DT_HO_SO, khach, "dy_zalo") or "")
	if co and cu != "Đồng ý":
		crm.ghi_dong_y_noi(khach, {"Zalo": "Đồng ý"}, "Web", cau_hoi=CAU_HOI_TV, nguoi="Guest")
	elif not co and cu == "Đồng ý":
		crm.ghi_dong_y_noi(khach, {"Zalo": "Từ chối"}, "Web", cau_hoi=CAU_HOI_TV, nguoi="Guest")


def _xoa_anh(duong):
	if not duong:
		return
	for ten in frappe.get_all("File", filters={"file_url": duong}, pluck="name"):
		frappe.delete_doc("File", ten, ignore_permissions=True, force=True)


@frappe.whitelist(allow_guest=True, methods=['POST'])
@rate_limit(limit=10, seconds=600)
def doi_anh(du_lieu=None):
	"""Ảnh đại diện khách tải lên (máy khách đã thu về 512 px JPEG). Lưu tệp
	RIÊNG TƯ gắn với hồ sơ khách; chỉ chính chủ đọc lại qua toi()."""
	_khong_cache()
	so = _so_phien()
	if not so:
		return {'ok':0, 'ly_do':'chua_dang_nhap'}
	raw, loi = doc_anh(du_lieu)
	if loi:
		return {'ok':0, 'ly_do':loi}
	khach, ly = _khach_hoac_tao(so)
	if not khach:
		return {'ok':0, 'ly_do':ly}
	from vagabond import crm

	crm._ho_so(khach, tao=True)
	cu = _ho_so_tv(khach).get("anh_dai_dien")
	f = frappe.get_doc({"doctype": "File", "file_name": "thanh-vien-%s.jpg" % secrets.token_hex(8), "is_private": 1,
		"content": raw, "attached_to_doctype": "Customer", "attached_to_name": khach})
	f.insert(ignore_permissions=True)
	frappe.db.set_value(DT_HO_SO, khach, {"anh_dai_dien": f.file_url, "anh_mau": ""}, update_modified=True)
	if cu and cu != f.file_url:
		_xoa_anh(cu)
	frappe.db.commit()
	return {'ok':1}


@frappe.whitelist(allow_guest=True, methods=['POST'])
@rate_limit(limit=10, seconds=600)
def nhan_qua(quay=None):
	"""Cấp mã quà chào mừng cho số đã xác thực. Gọi lại trả đúng mã cũ.

	Một số điện thoại một lần, cả khách cũ (anh Việt 30/10/2026). Khoá dòng hồ
	sơ CRM của khách trước khi kiểm, nên hai lượt bấm cùng lúc không ra hai mã.
	"""
	_khong_cache()
	so = _so_phien()
	if not so:
		return {'ok':0, 'ly_do':'chua_dang_nhap'}
	from vagabond import crm, khuyen_mai
	from vagabond.zalo_kich_ban import cat, ctkm_phat_duoc, mo_ta_uu_dai, ngay_vn

	km = _ctkm_qua()
	han, _ = ctkm_phat_duoc(km, _hom_nay(), QUA_SO_NGAY)
	if not han:
		return {'ok':0, 'ly_do':'qua_chua_mo'}
	noi_dia = _dn()._sdt_noi_dia(so)
	if khuyen_mai._la_sdt_nhan_vien(noi_dia):
		return {'ok':0, 'ly_do':'nhan_vien'}
	kh, ly = _khach_cua_so(noi_dia)
	if ly or not kh:
		return {'ok':0, 'ly_do':ly or 'ho_so_thieu', 'thieu':[] if ly else ['ten', 'sinh_nhat', 'dong_y']}
	khach = kh["name"]
	crm._ho_so(khach, tao=True)
	frappe.db.sql("select name from `tabVagabond Ho So CRM` where name = %s for update", (khach,))
	tv = _ho_so_tv(khach)
	muc = muc_ho_so({"ten": tv.get("ten_goi"), "sinh_nhat": kh.get("vgb_sinh_nhat"),
		"dong_y": (tv.get("dy_zalo") or "") == "Đồng ý"})
	if muc["thieu_qua"]:
		return {'ok':0, 'ly_do':'ho_so_thieu', 'thieu':muc["thieu_qua"]}
	ten_ud = mo_ta_uu_dai(km)[0]
	cu = _qua_da_cap(khach, noi_dia, tv.get("qua_chao_mung"))
	if cu:
		return {'ok':1, 'cu':1, 'ma':cu.ma, 'uu_dai':ten_ud, 'han':ngay_vn(cu.han_dung) if cu.han_dung else "",
			'trang_thai':trang_thai_voucher(cu, _hom_nay())}
	quay = str(quay or "").strip().upper()[:20]
	ma = khuyen_mai._sinh_ma_moi(1)[0]
	frappe.get_doc({"doctype": "Vagabond Voucher", "ma": ma, "ctkm": km.name, "ten_ctkm": cat(km.ten, 140),
		"trang_thai": "Chua dung", "han_dung": han, "khach": cat(tv.get("ten_goi") or kh.customer_name, 140),
		"sdt": noi_dia, "danh_cho": khach, "quay": quay,
		"gui_cho": cat("Quà chào mừng trang thành viên" + ((" tại quầy " + quay) if quay else ""), 140)}).insert(ignore_permissions=True)
	from frappe.utils import now_datetime

	frappe.db.set_value(DT_HO_SO, khach, {"qua_chao_mung": ma, "qua_luc": now_datetime(), "qua_quay": quay},
		update_modified=True)
	frappe.db.commit()
	return {'ok':1, 'cu':0, 'ma':ma, 'uu_dai':ten_ud, 'han':ngay_vn(han), 'trang_thai':'dung_duoc'}


def _qua_da_cap(khach, noi_dia, ma_ho_so):
	"""Mã quà chào mừng đã cấp cho khách hay cho số này (mọi trạng thái, kể cả
	đã huỷ: một số một lần)."""
	from vagabond import khuyen_mai

	cot = ["ma", "trang_thai", "han_dung"]
	if ma_ho_so:
		v = frappe.db.get_value("Vagabond Voucher", ma_ho_so, cot, as_dict=True)
		if v:
			return v
	for dk in ({"ctkm": khuyen_mai.CTKM_QUA, "danh_cho": khach}, {"ctkm": khuyen_mai.CTKM_QUA, "sdt": noi_dia}):
		ds = frappe.get_all("Vagabond Voucher", filters=dk, fields=cot, order_by="creation asc", limit_page_length=1)
		if ds:
			return ds[0]
	return None


# ------------------------------------------------------------------ VOUCHER THÀNH VIÊN (v623)
#
# Anh Việt 30/10/2026: voucher dành cho thành viên cài ngay trong phiếu
# Chương trình khuyến mãi (ô Đối tượng có sẵn: hạng, nhóm khách, khách chỉ
# định), bật "Phát vào Ví quà thành viên", chọn Dịp phát (Mọi lúc / Tháng
# sinh nhật) và Số lần nhận (Một lần / Mỗi năm một lần). Khách đủ điều kiện
# mở trang thành viên là mã TỰ HIỆN trong Ví quà, thu ngân áp như mã quà
# chào mừng, không phải chờ Zalo. Mã chỉ tạo khi khách mở ví, nên không
# phát thừa cho người không ghé.

VI_DIP = ("Moi luc", "Thang sinh nhat")
VI_SO_LAN = ("Mot lan", "Moi nam mot lan")
VI_HAN_MAC_DINH = 30
COT_CTKM_VI = ["name", "ten", "cach_ma", "bat", "kieu_giam", "gia_tri", "hd_toi_thieu", "tu_ngay", "den_ngay",
	"han_ma", "doi_tuong", "hang_khach", "nhom_khach", "vi_phat", "vi_dip", "vi_so_lan", "vi_han_ngay"]


def ky_vi(km, sinh_nhat, hom_nay):
	"""Dịp phát của một chương trình Ví quà có tới chưa. THUẦN.

	Trả (ok, lý do, ngày cuối của dịp). Tháng sinh nhật: chỉ trong đúng tháng
	sinh nhật của khách, mã dùng tới hết tháng đó. Mọi lúc: không có ngày cuối
	theo dịp (hạn tính theo số ngày đã đặt).
	"""
	from calendar import monthrange
	from vagabond.zalo_kich_ban import ngay_cua

	dip = (km or {}).get("vi_dip") or "Moi luc"
	if dip == "Thang sinh nhat":
		sn = ngay_cua(sinh_nhat)
		if not sn:
			return False, "chua_co_sinh_nhat", None
		if sn.month != hom_nay.month:
			return False, "chua_toi_thang_sinh_nhat", None
		return True, "", date(hom_nay.year, hom_nay.month, monthrange(hom_nay.year, hom_nay.month)[1])
	return True, "", None


def moc_so_lan(km, hom_nay):
	"""Từ ngày nào thì tính là "đã nhận trong kỳ". THUẦN. None là tính mọi lúc
	(Một lần); Mỗi năm một lần tính từ 01/01 năm nay."""
	if ((km or {}).get("vi_so_lan") or "Mot lan") == "Moi nam mot lan":
		return date(hom_nay.year, 1, 1)
	return None


def da_nhan_trong_ky(ds_voucher, moc):
	"""Khách đã có mã của chương trình trong kỳ chưa. THUẦN. Tính mọi trạng
	thái (đã dùng, đã huỷ, gửi qua Zalo): một kỳ một mã."""
	from vagabond.zalo_kich_ban import ngay_cua

	for v in ds_voucher or []:
		if moc is None:
			return True
		d = ngay_cua((v or {}).get("creation"))
		if d is None or d >= moc:
			return True
	return False


def han_ma_vi(km, hom_nay, cuoi_dip):
	"""Ngày hết hạn của mã Ví quà. THUẦN. None là chương trình không phát
	được hôm nay (chưa tới ngày, đã hết, đang tắt). Không vượt ngày cuối dịp."""
	from vagabond.zalo_kich_ban import ctkm_phat_duoc, so_nguyen

	so_ngay = (cuoi_dip - hom_nay).days if cuoi_dip else (so_nguyen(km.get("vi_han_ngay")) or VI_HAN_MAC_DINH)
	han, _ = ctkm_phat_duoc(km, hom_nay, max(1, so_ngay))
	if han and cuoi_dip and han > cuoi_dip:
		han = cuoi_dip
	return han


def _ds_ctkm_vi():
	try:
		return frappe.get_all("Vagabond CTKM", filters={"vi_phat": 1, "bat": 1, "cach_ma": "Ma dung mot lan"},
			fields=COT_CTKM_VI, order_by="uu_tien asc, ten asc", limit_page_length=50)
	except Exception:
		# Site chưa migrate (chưa có ô vi_phat): trang thành viên vẫn phải lên.
		return []


def ma_vi_trong_ky(km, khach, hom_nay):
	"""Các mã của chương trình đã cấp cho khách trong kỳ (Ví quà hay Zalo)."""
	moc = moc_so_lan(km, hom_nay)
	ds = frappe.get_all("Vagabond Voucher", filters={"ctkm": km.get("name"), "danh_cho": khach},
		fields=["ma", "trang_thai", "han_dung", "creation"], order_by="creation desc", limit_page_length=20)
	return [v for v in ds if da_nhan_trong_ky([v], moc)]


LY_VI = {
	"chua_co_sinh_nhat": "khách chưa khai ngày sinh",
	"chua_toi_thang_sinh_nhat": "chưa tới tháng sinh nhật của khách",
}


def xet_vi(km, khach, sinh_nhat, sdt, hom_nay, la_nv=None):
	"""Khách có đủ điều kiện nhận mã Ví quà của chương trình hôm nay không,
	CHƯA xét đã nhận trong kỳ. Trả (hạn mã, lý do). Một nguồn cho trang thành
	viên (cap_vi_tv) và tin Zalo cùng chương trình (Codex PR #520): dịp phát,
	số nhân viên, đối tượng như quầy, hạn kẹp theo dịp và chương trình."""
	from vagabond import khuyen_mai

	ok, ly, cuoi = ky_vi(km, sinh_nhat, hom_nay)
	if not ok:
		return None, LY_VI.get(ly, ly)
	if la_nv is None:
		la_nv = khuyen_mai._la_sdt_nhan_vien(sdt)
	# Số nhân viên không nhận quà khách (giống quà chào mừng), trừ chương
	# trình cài cho đúng đối tượng Nhân viên.
	if la_nv and (km.get("doi_tuong") or "Moi khach") != "Nhan vien":
		return None, "số điện thoại của nhân viên"
	ok_dt, ly_dt = khuyen_mai._hop_doi_tuong(km, khach, sdt)
	if not ok_dt:
		return None, ly_dt
	han = han_ma_vi(km, hom_nay, cuoi)
	if not han:
		return None, "chương trình chưa tới ngày, đã hết hoặc đang tắt"
	return han, ""


def khoa_ho_so(khach):
	"""Khoá dòng hồ sơ CRM của khách tới hết giao dịch. Trang thành viên và
	tin Zalo cùng khoá đúng dòng này trước khi xét "đã nhận trong kỳ" nên hai
	kênh chạy cùng lúc không ra hai mã (Codex PR #520)."""
	from vagabond import crm

	crm._ho_so(khach, tao=True)
	frappe.db.sql("select name from `tabVagabond Ho So CRM` where name = %s for update", (khach,))


def vi_du_dieu_kien(kh, noi_dia, hom_nay):
	"""Các chương trình Ví quà khách đủ điều kiện mà chưa nhận trong kỳ.
	Trả [(chương trình, hạn mã)]. Cùng phép kiểm đối tượng với quầy."""
	from vagabond import khuyen_mai

	ds = [km for km in _ds_ctkm_vi() if km.get("name") != khuyen_mai.CTKM_QUA]
	if not ds or not kh:
		return []
	la_nv = khuyen_mai._la_sdt_nhan_vien(noi_dia)
	ra = []
	for km in ds:
		han, _ = xet_vi(km, kh["name"], kh.get("vgb_sinh_nhat"), noi_dia, hom_nay, la_nv)
		if not han:
			continue
		if ma_vi_trong_ky(km, kh["name"], hom_nay):
			continue
		ra.append((km, han))
	return ra


@frappe.whitelist(allow_guest=True, methods=['POST'])
@rate_limit(limit=20, seconds=600)
def cap_vi_tv():
	"""Cấp mã cho mọi chương trình Ví quà khách đủ điều kiện. Trang gọi ngay
	sau khi đọc hồ sơ, khách không phải bấm. Khoá dòng hồ sơ CRM trước khi
	kiểm nên hai thẻ mở cùng lúc không ra hai mã."""
	_khong_cache()
	so = _so_phien()
	if not so:
		return {'ok':0, 'ly_do':'chua_dang_nhap'}
	from vagabond import khuyen_mai
	from vagabond.zalo_kich_ban import cat, mo_ta_uu_dai, ngay_vn

	noi_dia = _dn()._sdt_noi_dia(so)
	kh, ly = _khach_cua_so(noi_dia)
	if ly or not kh:
		return {'ok':1, 'moi':[]}
	khach = kh["name"]
	khoa_ho_so(khach)
	tv = _ho_so_tv(khach)
	moi = []
	for km, han in vi_du_dieu_kien(kh, noi_dia, _hom_nay()):
		ma = khuyen_mai._sinh_ma_moi(1)[0]
		frappe.get_doc({"doctype": "Vagabond Voucher", "ma": ma, "ctkm": km.name, "ten_ctkm": cat(km.ten, 140),
			"trang_thai": "Chua dung", "han_dung": han, "khach": cat(tv.get("ten_goi") or kh.customer_name, 140),
			"sdt": noi_dia, "danh_cho": khach, "gui_cho": "Ví quà thành viên"}).insert(ignore_permissions=True)
		moi.append({"ma": ma, "ten": km.ten or "", "uu_dai": mo_ta_uu_dai(km)[0], "han": ngay_vn(han)})
	frappe.db.commit()
	return {'ok':1, 'moi':moi}


# Chương trình mặc định khi site chưa có (anh Việt 30/10/2026: giảm 20.000đ).
CTKM_QUA_MAC_DINH = {
	"ten": "Quà chào mừng thành viên", "cach_thuc": "Giam tong hoa don", "bat": 1, "uu_tien": 10,
	"cong_don": 1, "kieu_giam": "So tien", "gia_tri": 20000, "pham_vi": "Ca hoa don",
	"doi_tuong": "Moi khach", "cach_ma": "Ma dung mot lan",
	"ghi_chu": "Khách khai hồ sơ trên trang thành viên (tên, ngày sinh, đồng ý nhận tin Zalo) nhận một mã. "
		"Mỗi số điện thoại một lần. Mã dùng ngay hoặc trong 7 ngày, chỉ cho chính người nhận.",
}


def dam_bao_ctkm_qua():
	"""Dựng chương trình Quà chào mừng nếu chưa có. Trả True khi vừa dựng."""
	from vagabond import khuyen_mai

	if frappe.db.exists("Vagabond CTKM", khuyen_mai.CTKM_QUA):
		return False
	d = dict(CTKM_QUA_MAC_DINH, doctype="Vagabond CTKM", ma_ctkm=khuyen_mai.CTKM_QUA, nguoi_tao="Administrator")
	frappe.get_doc(d).insert(ignore_permissions=True)
	return True
