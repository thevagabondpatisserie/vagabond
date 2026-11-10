"""Danh sach diem ban - mot noi khai duy nhat (anh Viet 12/08/2026).

Truoc day ba diem ban duoc khai o BA CHO khac nhau trong ma nguon:
DIEM_BAN_HDDT ben ban_hang (ma, ten, quay, nguon don), QUAY_DS ben
khuyen_mai (ma, ten), va DIEM_BAN ben bao_cao (ma, ten, dia chi). Ba cho
nay con dat ten khac nhau cho cung mot diem: "District 1 - Tran Cao Van"
o cho nay, "District 1" o cho kia.

Hai cai gia phai tra: mo chi nhanh thu tu la sua ma nguon roi deploy - ma
moi lan deploy la mot lan co the sai; va sua mot cho quen hai cho con lai
thi hai noi noi khac nhau, dung cai bay da lam mat 37 hoa don hom 10/08.

Nay gom ve mot noi, cat trong Vagabond Settings duoi dang JSON. Khong dung
doctype rieng vi danh sach nay chi vai dong va gan nhu khong bao gio doi -
mot bang moi keo theo di tru, quyen han, man danh sach, khong dang.

An toan khi deploy: chua ai luu gi thi doc ra MAC_DINH, tuc y nguyen ba
diem cu. Deploy khong lam thay doi hanh vi cua he thong.
"""

import json
import re

import frappe
from frappe.utils import cint, flt

from vagabond import so_do_ban
from vagabond.lib import cfg, cfg_o

TRUONG = "vgb_diem_ban"

# Ba diem dang chay. Vua la gia tri khoi tao, vua la luoi do khi cau hinh
# tren Settings bi trong hoac hong dinh dang.
MAC_DINH = [
	{
		"ma": "SALES",
		"ten": "Sales Online",
		"ten_ngan": "Sales Online",
		"quay": "",
		"phu": "Đơn online Pancake và các sàn",
		"anh": "/assets/vagabond/images/quay-sales.jpg",
		"dia_chi": "307/1 Nguyễn Văn Trỗi, Phường 1, Quận Tân Bình",
		"mst": "",
		"ky_hieu": "",
		"nguon": ["Pancake", "GrabFood", "BeFood", "GreenSM Food", "ShopeeFood", "Khách sỉ"],
		"bat": 1,
		"thu_tu": 1,
	},
	{
		"ma": "TCV",
		# Giu dung ten cu tren man tinh tien de thu ngan khong thay la.
		"ten": "The Vagabond District 1",
		"ten_ngan": "District 1",
		"quay": "TCV",
		"phu": "9 Trần Cao Vân",
		"anh": "/assets/vagabond/images/quay-tcv.jpg",
		"dia_chi": "9 Trần Cao Vân, Quận 1",
		"mst": "",
		"ky_hieu": "",
		"nguon": ["Tại chỗ", "Mang về"],
		"bat": 1,
		"thu_tu": 2,
	},
	{
		"ma": "NVHTN",
		"ten": "Nhà Văn Hóa Thanh Niên",
		"ten_ngan": "NVHTN",
		"quay": "NVHTN",
		"phu": "Quầy NVHTN",
		"anh": "/assets/vagabond/images/quay-nvhtn.jpg",
		"dia_chi": "21 Phạm Ngọc Thạch, Quận 3",
		"mst": "",
		"ky_hieu": "",
		"nguon": ["Tại chỗ", "Mang về"],
		"bat": 1,
		"thu_tu": 3,
	},
]

from vagabond.vai_cua_hang import VAI_QLCH

QUYEN_SUA = {"System Manager", "Accounts Manager", "Sales Manager", VAI_QLCH}

# v631 (anh Viet 02/11/2026, duyet mau "Diem ban tu nhan theo tai khoan va
# bang gia rieng NVH"):
#   - Moi diem khai "Nhan vien dung diem nay" (tai khoan dang nhap). Mo Tinh
#     tien la vao thang diem cua minh, khong con bam nham the diem khac (ca
#     Gia Bao bam nham Sales Online khi dang dung District 1).
#   - Moi diem co the co BANG GIA RIENG (mot Price List ban ra). Mon co gia
#     trong bang do thi quay do ban gia do; mon chua khai thi ban gia chung
#     (standard_rate) nhu cu. May chu tinh lai gia theo diem khi luu bill nen
#     khong ai sua tay duoc.
TIEN_TO_BANG_GIA = "Giá riêng "


def loc_bo_bang_rieng():
	"""Điều kiện price_list loại các bảng giá riêng của điểm bán. Mọi câu đọc
	"giá bán niêm yết" từ Item Price mà không chỉ rõ bảng giá phải kèm điều kiện
	này, không thì giá riêng NVH lọt thành giá chung (v631, Codex PR #532)."""
	return ["not like", TIEN_TO_BANG_GIA + "%"]
SO_NGAY_GOI_Y = 30
GIA_TOI_DA = 100000000


def ten_bang_gia(ma):
	"""THUAN: ten Price List rieng cua mot diem. Dat theo MA diem (khong doi
	khi doi ten hien thi) de cau hinh cu van tro dung bang."""
	return TIEN_TO_BANG_GIA + str(ma or "").strip().upper()


def _ds_nguoi(v):
	"""THUAN: danh sach tai khoan dung diem, bo trung, bo rong, giu thu tu."""
	if isinstance(v, str):
		v = [x for x in re.split(r"[\s,;]+", v) if x]
	ra = []
	for x in v or []:
		x = str(x or "").strip()
		if x and x not in ra:
			ra.append(x)
	return ra


def _chuan(d, i=0):
	"""Mot dong cau hinh bat ky ve dung khuon, thieu truong nao thi bu."""
	ma = str(d.get("ma") or "").strip().upper()
	ten = str(d.get("ten") or "").strip() or ma
	nguon = d.get("nguon")
	if isinstance(nguon, str):
		nguon = [x.strip() for x in nguon.replace(",", "\n").splitlines() if x.strip()]
	nguon_ds = [str(x).strip() for x in (nguon or []) if str(x).strip()]
	# Ma quay LUON bang ma diem. Ca he quy mot hoa don ve diem ban bang
	# cach doc vgb_quay roi tra theo MA DIEM (bao_cao._diem, ke_toan,
	# khuyen_mai._hop_kenh). De hai truong lech nhau la bao cao ra dong 0
	# dong con doanh thu that gom vao mot khoa khong ten, va khuyen mai
	# gioi han quay khong bao gio khop bill nao.
	co_quay = cint(d.get("co_quay") if d.get("co_quay") is not None else (1 if str(d.get("quay") or "").strip() else 0))
	def _dau(tien_to):
		for n in nguon_ds:
			if n.lower().startswith(tien_to):
				return n
		return ""
	return {
		"ma": ma,
		"ten": ten,
		"ten_ngan": str(d.get("ten_ngan") or "").strip() or ten,
		"co_quay": 1 if co_quay else 0,
		"quay": ma if co_quay else "",
		"tai_cho": _dau("tại chỗ"),
		"mang_ve": _dau("mang về"),
		"anh": str(d.get("anh") or "").strip(),
		"phu": str(d.get("phu") or "").strip(),
		"dia_chi": str(d.get("dia_chi") or "").strip(),
		# v647: sơ đồ bàn theo khu (màn In QR tại bàn lưu, màn Tính tiền đọc
		# chung) và địa chỉ in dưới standee QR bàn.
		"so_do_ban": so_do_ban.chuan_so_do(d.get("so_do_ban")),
		"dia_chi_qr": str(d.get("dia_chi_qr") or "").strip(),
		"mst": str(d.get("mst") or "").strip(),
		"ky_hieu": str(d.get("ky_hieu") or "").strip(),
		"kho_tang": str(d.get("kho_tang") or "").strip(),
		"nguon": nguon_ds,
		"nhan_vien": _ds_nguoi(d.get("nhan_vien")),
		# Man Cai dat gui gia_rieng 1/0; cau hinh da luu mang san ten bang.
		"bang_gia": (ten_bang_gia(ma) if cint(d.get("gia_rieng")) else "") if d.get("gia_rieng") is not None
			else str(d.get("bang_gia") or "").strip(),
		"bat": 1 if cint(d.get("bat") if d.get("bat") is not None else 1) else 0,
		"thu_tu": cint(d.get("thu_tu") or (i + 1)),
	}


def ds(chi_bat=False):
	"""Toan bo diem ban, da chuan hoa va sap theo thu tu.

	chi_bat: chi lay diem dang bat. Cac man nghiep vu nen dung chi_bat=True;
	rieng bao cao va man Cai dat thi lay het, vi so lieu cu cua mot diem da
	dong van phai xem lai duoc.
	"""
	try:
		tho = json.loads((cfg_o(TRUONG) or "").strip() or "[]")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "diem_ban: cau hinh hong dinh dang")
		tho = []
	if not isinstance(tho, list) or not tho:
		tho = MAC_DINH
	ra = [_chuan(d, i) for i, d in enumerate(tho)]
	ra = [d for d in ra if d["ma"]]
	if not ra:
		ra = [_chuan(d, i) for i, d in enumerate(MAC_DINH)]
	ra.sort(key=lambda d: (d["thu_tu"], d["ma"]))
	return [d for d in ra if d["bat"]] if chi_bat else ra


def theo_ma(ma):
	ma = str(ma or "").strip().upper()
	for d in ds():
		if d["ma"] == ma:
			return d
	return None


def ma_theo_quay(quay):
	"""Ma diem ban tu ma quay. Quay de trong nghia la Sales Online."""
	q = str(quay or "").strip().upper()
	for d in ds():
		if d["quay"] == q:
			return d["ma"]
	return "SALES" if not q else q


def ten_diem():
	"""Bang tra ma -> ten ngan, dung cho bao cao va chip tren app."""
	return {d["ma"]: d["ten_ngan"] for d in ds()}


def diem_cua_nguoi(ds_diem, user):
	"""THUAN: ma cac diem DANG BAT ma tai khoan nay duoc khai dung."""
	user = str(user or "").strip()
	return [d["ma"] for d in ds_diem if d.get("bat") and user and user in (d.get("nhan_vien") or [])]


def doc_gia(v):
	"""THUAN: o gia nguoi go tay (hoac o Excel) ve so dong, None la de trong.

	Chiu moi cach go hop ly: 70000, 70.000, 70,000, "70 000 đ", 70000.0 tu
	Excel. Go sai thi nem ValueError voi cau doc duoc."""
	if v is None:
		return None
	if isinstance(v, (int, float)):
		so = float(v)
	else:
		t = str(v).strip().lower().replace("đ", "").replace("vnd", "").strip()
		if not t or t == "trống":
			return None
		t = re.sub(r"[\s.,]", "", t)
		if not t.isdigit():
			raise ValueError("Giá \"%s\" không phải số tiền. Gõ số, ví dụ 70000 hoặc 70.000." % str(v).strip())
		so = float(t)
	if so <= 0:
		return None
	if so != int(so) or so >= GIA_TOI_DA:
		raise ValueError("Giá %s không hợp lệ. Gõ số tiền đồng, dưới 100 triệu." % str(v).strip())
	return int(so)


def ap_gia_diem(items, rows, gia, mien=()):
	"""THUAN: dat lai gia cac dong theo bang gia rieng cua diem.

	items la dong may khach gui (de khuyen mai tinh tren gia that), rows la
	dong se ghi vao hoa don, cung thu tu. mien la chi so cac dong combo ma
	MAY CHU da xac nhan (dong_combo_tao, dong_giu_gia_sua): combo co gia rieng
	cua no. Nhan combo do may khach tu gui KHONG duoc mien (Codex PR #532:
	gui combo "bat ky" kem gia 1 dong la lot gia diem). Mon chua co gia o
	diem nay giu gia may khach gui (gia chung). Tra so dong da doi."""
	doi = 0
	if not gia:
		return 0
	mien = set(mien or ())
	for i, r in enumerate(items or []):
		if i in mien:
			continue
		ma = str(r.get("item_code") or "").strip()
		if ma not in gia:
			continue
		if flt(r.get("rate")) != flt(gia[ma]):
			doi += 1
		r["rate"] = gia[ma]
		if rows is not None and i < len(rows):
			rows[i]["rate"] = gia[ma]
	return doi


def ap_gia_chung(items, rows, gia, mien, gia_chung, bo_qua=()):
	"""THUAN: dong KHONG co gia rieng o diem (va khong phai combo da xac nhan,
	khong phai ma bo_qua nhu phi giao) phai dung gia chung trong danh muc
	(Item.standard_rate, dung nguon may quay dang dung). Codex PR #532 vong 3:
	quan ly bo gia rieng cua mot mon, hay tat bang gia cua diem, ma gio cu con
	gia rieng cu thi truoc day may chu giu nguyen gia cu. Mon chua co gia
	chung (0) thi khong dung. Tra so dong da doi."""
	doi = 0
	mien = set(mien or ())
	gia = gia or {}
	for i, r in enumerate(items or []):
		ma = str(r.get("item_code") or "").strip()
		if i in mien or ma in gia or ma in bo_qua:
			continue
		g = flt((gia_chung or {}).get(ma))
		if not g:
			continue
		if flt(r.get("rate")) != g:
			doi += 1
		r["rate"] = g
		if rows is not None and i < len(rows):
			rows[i]["rate"] = g
	return doi


def gia_dong_combo(dong, ma):
	"""THUAN: gia mot mon thanh phan trong combo, doc tu cau hinh combo tren
	MAY CHU (cot gia_goc cua dong combo; man quay dat dung so nay khi bam
	combo). Tien giam cua combo do khuyen mai tinh rieng (combo_ap). Tra 0 neu
	combo khong khai gia cho mon do (Codex PR #532 vong 7)."""
	ma = str(ma or "").strip()
	return max([flt(x.get("gia_goc")) for x in (dong or []) if x.get("item_code") == ma] or [0])


def dat_gia_dong_combo(r, dong):
	"""THUAN: dong gio co ma combo da kiem thanh phan. Dat gia theo cau hinh
	combo cua may chu; combo khong khai gia cho mon thi BO danh dau combo de
	dong nay tinh nhu mon thuong (gia diem, gia chung). Tra 1 neu gia may khach
	gui lech gia may chu."""
	g = gia_dong_combo(dong, r.get("item_code"))
	if not g:
		r["combo_ma"] = ""
		return 0
	lech = 1 if flt(r.get("rate")) != g else 0
	r["rate"] = g
	return lech


def dong_combo_tao(items):
	"""THUAN: dong combo duoc giu gia khi LUU bill moi. Chi dong co ma combo
	(combo_ma): vong dung dong cua tao_don_tay da doc Vagabond Combo va chan
	mon khong thuoc combo do truoc khi goi ham nay."""
	return {i for i, r in enumerate(items or []) if r.get("combo_ma")}


def dong_giu_gia_sua(items, dong_cu):
	"""THUAN: dong GIU GIA khi SUA bill (Codex PR #532 vong 5). Chinh sach: dong
	da luu tren hoa don (dong_goc co trong dong_cu doc tu MAY CHU) giu dung gia
	da chot voi khach luc lap bill, ke ca khi quan ly doi bang gia diem sau do;
	sua ghi chu hay them mon khong lam doi gia dong cu. Dong gui kem combo_ma
	thi vong dung dong cua pos_sua_don kiem thanh phan truoc khi luu. Chi dong
	THEM MOI (khong dong_goc) moi theo gia diem hien hanh. Doi gia dong cu van
	di qua luat OTP sua gia nhu truoc v631.

	Codex PR #532 vong 6: dong_goc chi la TEN dong do may khach gui. Dong gui
	len phai cung MA MON voi dong goc tren may chu moi duoc giu gia; gui
	dong_goc cua ly tra kem ma banh khac la mon THEM MOI, theo gia diem."""
	ra = set()
	for i, r in enumerate(items or []):
		if r.get("combo_ma"):
			ra.add(i)
			continue
		cu = (dong_cu or {}).get(r.get("dong_goc") or "")
		ma = str(r.get("item_code") or "").strip()
		if cu and ma == str(cu.get("item_code") or "").strip():
			ra.add(i)
	return ra


def doc_gia_chung(items, bo=()):
	"""Gia chung danh muc (Item.standard_rate) cua cac mon trong gio, tru ma
	trong bo (mon co gia diem). Cham he: doc DB."""
	ma = sorted({str(r.get("item_code") or "").strip() for r in items or []} - set(bo) - {""})
	if not ma:
		return {}
	return {x["name"]: x["standard_rate"] for x in frappe.get_all("Item", filters={"name": ["in", ma]}, fields=["name", "standard_rate"])}


# Câu máy chủ trả khi bảng giá của điểm đổi sau lúc máy quầy đọc giá. Màn quầy
# dò đúng câu đầu này để đọc lại giá rồi cho thu ngân xem tổng mới (Codex PR #532).
GIA_VUA_DOI = "Bảng giá của điểm vừa đổi"


def cau_gia_vua_doi(n):
	return "%s: %d món đã sang giá mới. Màn đã cập nhật, kiểm lại tổng tiền với khách rồi bấm lưu lại." % (GIA_VUA_DOI, n)


def gia_rieng(ma):
	"""Bang gia rieng cua mot diem: {ma mon: gia}. Diem khong co bang gia
	rieng thi tra rong (ban gia chung)."""
	d = theo_ma(ma)
	if not d or not d.get("bang_gia"):
		return {}
	return gia_dang_ap(_dong_gia_diem(d["bang_gia"]), _hom_nay())


def _hom_nay():
	from frappe.utils import nowdate

	return str(nowdate())


def _dong_gia_diem(bang, mon=None, chi_ban=True):
	"""Moi dong Item Price cua bang gia diem, KE CA dong da khoa han. Mot cho
	doc duy nhat; loc dong dang ap thi qua gia_dang_ap / ke_hoach_gia."""
	loc = {"price_list": bang}
	if chi_ban:
		loc["selling"] = 1
	if mon:
		loc["item_code"] = mon
	return frappe.get_all("Item Price", filters=loc,
		fields=["name", "item_code", "price_list_rate", "valid_from", "valid_upto", "modified"],
		order_by="modified asc", limit_page_length=0)


def _ngay(x):
	"""THUAN: chuoi hay date -> date, sai thi None."""
	from datetime import date

	if isinstance(x, date):
		return x
	t = str(x or "")
	try:
		return date.fromisoformat(t[:10]) if len(t) >= 10 else None
	except ValueError:
		return None


def con_han(r, ngay):
	"""THUAN: dong Item Price dang ap ngay `ngay` (chua toi han bat dau thi
	chua ap, qua han ket thuc thi thoi ap) va gia duong."""
	n = _ngay(ngay)
	tu, den = _ngay(r.get("valid_from")), _ngay(r.get("valid_upto"))
	return not (tu and tu > n) and not (den and den < n) and flt(r.get("price_list_rate")) > 0


def chon_dong_dang_ap(rows, ngay):
	"""THUAN: {ma mon: dong} dang ap. Nhieu dong cung hieu luc thi lay dong co
	ngay bat dau muon nhat, roi dong sua sau cung (cung luat banh_si.chon_gia)."""
	ra = {}
	for r in rows or []:
		if not con_han(r, ngay):
			continue
		khoa = (str(_ngay(r.get("valid_from")) or ""), str(r.get("modified") or ""))
		cu = ra.get(r.get("item_code"))
		if not cu or khoa > (str(_ngay(cu.get("valid_from")) or ""), str(cu.get("modified") or "")):
			ra[r.get("item_code")] = r
	return ra


def gia_dang_ap(rows, ngay):
	"""THUAN: {ma mon: gia} dang ap ngay `ngay`. Dong da khoa han (bo gia
	rieng) khong tinh nhung van nam trong so de tra lai (QT-20)."""
	return {ma: flt(r.get("price_list_rate")) for ma, r in chon_dong_dang_ap(rows, ngay).items()}


def ke_hoach_gia(rows, gia, ngay):
	"""THUAN: tu cac dong gia cua MOT mon o mot diem ra viec can lam, KHONG
	BAO GIO XOA dong nao (QT-20, Codex #532). Tra (gia_cu, sua, khoa, them):
	  sua  = (ten dong, gia moi) dat lai gia dong dang ap, hoac None;
	  khoa = [{name, valid_upto, valid_from?}] khoa han toi hom qua: bo gia
	         rieng, hoac dong dang ap thua;
	  them = True khi phai them dong moi (chua co dong dang ap).
	Gia trong la bo gia rieng: khoa han dong dang ap, mon ve gia chung."""
	from datetime import timedelta

	n = _ngay(ngay)
	r0 = next(iter(chon_dong_dang_ap(rows, n).values()), None)
	gia_cu = flt(r0.get("price_list_rate")) if r0 else 0
	if flt(gia or 0) == gia_cu:
		return gia_cu, None, [], False
	hom_qua = str(n - timedelta(days=1))

	def khoa(r):
		k = {"name": r["name"], "valid_upto": hom_qua}
		tu = _ngay(r.get("valid_from"))
		if not tu or str(tu) > hom_qua:
			# Dong khai hom nay roi bo hom nay: lui ngay bat dau de han hop le.
			k["valid_from"] = hom_qua
		return k

	thua = [khoa(r) for r in rows or [] if r is not r0 and con_han(r, n)]
	if gia:
		if r0:
			return gia_cu, (r0["name"], flt(gia)), thua, False
		return gia_cu, None, thua, True
	return gia_cu, None, ([khoa(r0)] if r0 else []) + thua, False


def gia_rieng_cua_quay(quay):
	"""Bang gia rieng theo ma quay tren hoa don. Don online (quay trong) thi
	khong co bang rieng."""
	q = str(quay or "").strip()
	return gia_rieng(ma_theo_quay(q)) if q else {}


def nguon_cua(ma):
	d = theo_ma(ma)
	return list(d["nguon"]) if d else []


def quay_dang_bat():
	"""Ma quay cua cac diem co quay (bo Sales Online vi khong mang ma quay)."""
	return [d["quay"] for d in ds(chi_bat=True) if d["quay"]]


# ------------------------------------------------------------------ man app


@frappe.whitelist()
def danh_sach():
	"""Man Cai dat doc danh sach diem ban."""
	from vagabond.ban_hang import _kiem_quyen, _cong_ty

	_kiem_quyen()
	return {
		"diem": ds(),
		"kho_tang": frappe.get_all('Warehouse', filters={'company': _cong_ty(), 'is_group': 0, 'disabled': 0},
			fields=['name', 'company'], order_by='name'),
		"sua_duoc": 1 if QUYEN_SUA & set(frappe.get_roles()) else 0,
		"nguon_co_san": nguon_co_san(),
		# v631: goi y nguoi dung diem tu bill 30 ngay, va danh sach tai khoan
		# de them tay; ten hien cho tai khoan da khai.
		"goi_y": goi_y_nhan_vien(),
		"nguoi_dung": _nguoi_dung_he(),
		"tien_to_bang_gia": TIEN_TO_BANG_GIA,
	}


# Nguon don co san de bam chon tren app. Truoc day la o nhap tay tung dong:
# go thieu mot dau la nguon do khong khop voi hoa don nao ca, ma khong ai
# bao loi - hoa don cu the nam ngoai moi diem ban.
NGUON_MAU = [
	{"v": "Tại chỗ", "ic": "🏬"},
	{"v": "Mang về", "ic": "🥡"},
	{"v": "Pancake", "ic": "💬"},
	{"v": "GrabFood", "lg": "/files/pt-grab.png"},
	{"v": "BeFood", "lg": "/files/pt-befood.png"},
	{"v": "GreenSM Food", "lg": "/files/pt-greensm.png"},
	{"v": "ShopeeFood", "lg": "/files/pt-shopee4.png"},
	{"v": "Khách sỉ", "ic": "🏢"},
]


def _bieu_tuong(n):
	thap = str(n or "").lower()
	if thap.startswith("tại chỗ"):
		return "🏬"
	if thap.startswith("mang về"):
		return "🥡"
	return "🧾"


def nguon_co_san():
	"""Nguon de bam chon: bang mau, nguon dang khai, va nguon co that.

	Phai gop ca nguon DA NAM TREN HOA DON that: neu chi hien bang mau thi
	mot nguon cu do quay tung go tay se khong con duong chon lai, sua mot
	diem ban la vo tinh cat nguon do khoi he.
	"""
	ra, da_co = [], {}
	for m in NGUON_MAU:
		da_co[m["v"]] = 1
		ra.append({"v": m["v"], "lg": m.get("lg") or "", "ic": m.get("ic") or ""})

	def them(n):
		n = str(n or "").strip()
		if not n or n in da_co:
			return
		da_co[n] = 1
		ra.append({"v": n, "lg": "", "ic": _bieu_tuong(n)})

	def _ten_moi(n):
		"""Ten nguon cu tren hoa don cu doi ve ten dang dung.

		Hai hoa don da gui hom 09 va 11/08 con mang ten "Tại chỗ - Trần Cao
		Vân" va "Mang về - Nguyễn Văn Trỗi" - Frappe khoa truong nguon sau
		khi gui nen khong sua lai duoc. Neu khong doi ten o day thi man Diem
		ban bay ra hai chip nguon cu vo chu, ai do bam vao la nguon da bo
		song lai.
		"""
		try:
			from vagabond.ban_hang import NGUON_CU

			return NGUON_CU.get(n, n)
		except Exception:
			return n

	dang_khai = ds()
	for d in dang_khai:
		for n in d["nguon"]:
			them(n)
	try:
		rows = frappe.db.sql(
			"select distinct custom_nguon from `tabSales Invoice` "
			"where ifnull(custom_nguon, '') != ''"
		)
		for r in rows:
			them(_ten_moi(r[0]))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "diem_ban: khong doc duoc nguon that")

	# Nguon dang thuoc diem nao, de man hinh bao truoc thay vi de nguoi
	# dung bam Luu roi moi an loi tu may chu.
	# Mot nguon nay co the thuoc NHIEU diem co quay ("Tại chỗ" chung cho ca
	# hai quay), nen goi ra danh sach chu khong con la mot ma don le.
	chu = {}
	for d in dang_khai:
		for n in d["nguon"]:
			chu.setdefault(n, []).append(d["ma"])
	for x in ra:
		ds_chu = chu.get(x["v"]) or []
		x["cua"] = ", ".join(ds_chu)
		x["cua_ds"] = ds_chu
	return ra


def diem_cua_nguon(nguon):
	"""Cac diem ban dang khai nguon nay. Nguon dung chung thi tra nhieu ma."""
	n = str(nguon or "").strip()
	return [d["ma"] for d in ds(chi_bat=True) if n in d["nguon"]]


def _kiem(ra):
	"""Chan cac cau hinh se lam lech so lieu, TRUOC khi luu."""
	if not ra:
		frappe.throw("Phải có ít nhất một điểm bán.")
	ma_da_co, quay_da_co = {}, {}
	for d in ra:
		if d.get('kho_tang'):
			from vagabond.ban_hang import _cong_ty
			from vagabond.hang_tang_kho import kiem_kho
			kiem_kho(d['kho_tang'], _cong_ty())
		if not d["ma"]:
			frappe.throw("Có điểm bán chưa đặt mã.")
		if not d["ma"].replace("_", "").isalnum() or not d["ma"].isascii():
			frappe.throw(
				"Mã điểm bán %s không hợp lệ. Chỉ dùng chữ không dấu, số và gạch "
				"dưới - mã này đi vào tên tệp, đường dẫn và báo cáo." % d["ma"]
			)
		if d["ma"] in ma_da_co:
			frappe.throw("Mã điểm bán %s bị trùng." % d["ma"])
		ma_da_co[d["ma"]] = 1
		# Hai diem cung ma quay thi moi bill deu bi dem cho ca hai, doanh thu
		# nhan doi ma khong ai nhin ra.
		if d["quay"]:
			if d["quay"] in quay_da_co:
				frappe.throw(
					"Mã quầy %s đang gán cho cả %s và %s. Mỗi quầy chỉ thuộc một "
					"điểm bán." % (d["quay"], quay_da_co[d["quay"]], d["ma"])
				)
			quay_da_co[d["quay"]] = d["ma"]
	# KHONG con kiem nguon dung chung nua. MOI nguon deu gan duoc cho moi
	# diem ban, ke ca diem nhan don online (anh Viet 15/08/2026: *"mo tinh
	# nang de gan cac nguon nay duoc cho moi diem ban"*).
	#
	# Truoc day cho nay chan nguon dung chung voi diem online vi so hoa don
	# dien tu xuat hai lan. Nay khong con ly do:
	#   - Ca he quy hoa don ve diem ban bang vgb_quay chu khong bang ten
	#     nguon (ma_theo_quay). Bill quay mang ma quay, don online de trong
	#     va roi ve dung diem online duy nhat.
	#   - Khoa xuat hoa don dien tu cung da chuyen sang dem theo ma quay
	#     (ban_hang.TRUONG_HDDT_QUAY), khong con dem theo ten nguon.
	#   - He chi cho DUNG MOT diem online (kiem ngay ben duoi), nen khong
	#     bao gio co hai diem cung "khong mang ma quay" de lan nhau.
	# Man Nhap don tay van bat chon diem ban khi nguon thuoc nhieu diem, nen
	# khong con duong nao de mot don roi nham cho.
	online = [d for d in ra if not d["quay"]]
	if len(online) != 1:
		frappe.throw(
			"Phải có ĐÚNG MỘT điểm bán nhận đơn online, hiện đang có %d. Đơn "
			"online không mang mã quầy nào nên cả hệ quy hết về một điểm; để "
			"hai điểm online thì điểm thứ hai luôn ra 0 đồng trong báo cáo."
			% len(online)
		)
	if not [d for d in ra if d["bat"]]:
		frappe.throw("Phải còn ít nhất một điểm bán đang dùng.")
	# v631: gia rieng chi ap cho bill quay (may chu tinh lai theo ma quay).
	# Don online di qua san, Pancake, web voi gia rieng cua kenh do.
	for d in online:
		if d["bang_gia"]:
			frappe.throw("Điểm %s nhận đơn online nên không dùng bảng giá riêng. Đơn online theo giá của từng kênh." % d["ten_ngan"])
	trong = [d["ma"] for d in ra if d["bat"] and not d["nguon"]]
	if trong:
		frappe.throw(
			"Điểm bán %s đang dùng mà chưa khai nguồn đơn nào. Không có nguồn "
			"thì hoá đơn của điểm đó không lọc ra để xuất hoá đơn điện tử "
			"được, mà màn Cuối ngày vẫn hiện là đang bật." % ", ".join(trong)
		)


def _dang_dung(ma):
	"""Diem ban da co hoa don chua - de chan xoa, chi cho tat."""
	d = theo_ma(ma)
	if not d:
		return 0
	try:
		if d["quay"]:
			return frappe.db.count("Sales Invoice", {"vgb_quay": d["quay"]})
		return frappe.db.count("Sales Invoice", {"vgb_quay": ["in", ["", None]]})
	except Exception:
		return 0


@frappe.whitelist()
def luu(diem=None):
	"""Luu lai danh sach diem ban tu man Cai dat."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not QUYEN_SUA & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới sửa được danh sách điểm bán.")
	if isinstance(diem, str):
		diem = frappe.parse_json(diem or "[]")
	diem = giu_truong_rieng(diem, ds())
	ra = [_chuan(d, i) for i, d in enumerate(diem or [])]
	ra = [d for d in ra if d["ma"]]
	_kiem(ra)

	# Diem da co hoa don thi khong duoc bien mat khoi danh sach: mat dong
	# khai la bao cao khong con biet ma do la cua ai, va chuoi cuoi ngay
	# khong con biet nguon nao thuoc ve no.
	ma_moi = {d["ma"] for d in ra}
	for cu in ds():
		if cu["ma"] not in ma_moi and _dang_dung(cu["ma"]):
			frappe.throw(
				"Điểm bán %s đã có hoá đơn nên không bỏ khỏi danh sách được. "
				"Muốn ngừng dùng thì tắt nó đi, số liệu cũ vẫn xem lại được."
				% cu["ma"]
			)

	_theo_kip_nguon(ds(), ra)
	for d in ra:
		if d["bang_gia"]:
			_bao_dam_bang_gia(d["bang_gia"])
	frappe.db.set_single_value(
		"Vagabond Settings", TRUONG, json.dumps(ra, ensure_ascii=False, indent=1)
	)
	frappe.db.commit()
	_ghi_vet(
		"Sửa danh sách điểm bán: %s"
		% ", ".join("%s%s" % (d["ma"], "" if d["bat"] else " (tắt)") for d in ra)
	)
	return {"diem": ds(), "sua_duoc": 1, "nguon_co_san": nguon_co_san()}


# v647: trường do màn khác lưu (In QR tại bàn), màn Cài đặt điểm bán không gửi.
TRUONG_RIENG = ("so_do_ban", "dia_chi_qr")


def giu_truong_rieng(moi, cu):
	"""THUAN: dòng màn Cài đặt gửi lên không có trường riêng thì giữ giá trị đã
	lưu của đúng điểm đó, để lưu danh sách điểm bán không xoá sơ đồ bàn."""
	theo_ma = {str(d.get("ma") or "").strip().upper(): d for d in cu or []}
	ra = []
	for d in moi or []:
		d = dict(d or {})
		c = theo_ma.get(str(d.get("ma") or "").strip().upper())
		for k in TRUONG_RIENG:
			if k not in d and c:
				d[k] = c.get(k)
		ra.append(d)
	return ra


def dat_truong(ma, cap, vet=""):
	"""Ghi vài trường riêng của MỘT điểm (v647: sơ đồ bàn), giữ nguyên mọi
	trường và mọi điểm khác. Chỉ nhận trường trong TRUONG_RIENG."""
	ma = str(ma or "").strip().upper()
	cap = {k: v for k, v in (cap or {}).items() if k in TRUONG_RIENG}
	ra = ds()
	d = next((x for x in ra if x["ma"] == ma), None)
	if not d:
		frappe.throw("Không thấy điểm bán %s." % ma)
	d.update(cap)
	ra = [_chuan(x, i) for i, x in enumerate(ra)]
	frappe.db.set_single_value("Vagabond Settings", TRUONG, json.dumps(ra, ensure_ascii=False, indent=1))
	frappe.db.commit()
	if vet:
		_ghi_vet(vet)
	return d


def _theo_kip_nguon(cu, moi):
	"""Doi ten mot nguon don thi keo theo cau hinh xuat hoa don dien tu.

	Cau hinh do (MInvoice Phat Hanh Settings.nguon) luu TEN NGUON chu khong
	luu ma diem ban. Sua mot dong nguon o day ma khong keo theo la tu do
	tro hoa don dien tu ngung xuat cho nguon do, im lang, cho den khi ai do
	tinh co mo man Cuoi ngay bam Luu.
	"""
	try:
		stg = frappe.get_doc("MInvoice Phat Hanh Settings")
		dang = [x.strip() for x in str(stg.get("nguon") or "").replace(",", "\n").splitlines() if x.strip()]
	except Exception:
		return
	if not dang:
		return
	cu_theo_ma = {d["ma"]: d["nguon"] for d in cu}
	doi = False
	for d in moi:
		nguon_cu = cu_theo_ma.get(d["ma"])
		if nguon_cu is None or nguon_cu == d["nguon"]:
			continue
		# Chi thay khi diem do dang duoc bat XUAT HDDT (toan bo nguon cu cua
		# no dang nam trong danh sach), de khong tu dung bat cho diem dang tat.
		if not nguon_cu or not all(n in dang for n in nguon_cu):
			continue
		dang = [n for n in dang if n not in nguon_cu] + list(d["nguon"])
		doi = True
	if not doi:
		return
	try:
		frappe.db.set_value(
			"MInvoice Phat Hanh Settings",
			"MInvoice Phat Hanh Settings",
			"nguon",
			"\n".join(dict.fromkeys(dang)),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "diem_ban: cap nhat nguon xuat HDDT")


def _ghi_vet(viec):
	"""Doi mot cau hinh anh huong tien bac thi phai biet ai doi, luc nao."""
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Vagabond Settings",
				"reference_name": "Vagabond Settings",
				"content": "%s - %s" % (viec, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass


# ------------------------------------------------------------------ v631: nguoi dung diem va bang gia rieng


def goi_y_nhan_vien(so_ngay=SO_NGAY_GOI_Y):
	"""Goi y "Nhan vien dung diem nay": ai da tao bill o quay do trong 30 ngay
	qua, nhieu bill truoc. {ma diem: [{user, ten, so}]}. Quan ly chi can bam
	Luu; bo chip la bo nguoi do khoi diem."""
	from frappe.utils import add_days, nowdate

	ra = {}
	try:
		rows = frappe.db.sql(
			"select vgb_quay, owner, count(*) so from `tabSales Invoice` "
			"where docstatus = 1 and is_return = 0 and posting_date >= %s and ifnull(vgb_quay, '') != '' "
			"group by vgb_quay, owner order by so desc",
			(add_days(nowdate(), -int(so_ngay)),), as_dict=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "diem_ban: khong doc duoc goi y nhan vien")
		return ra
	ten = _ten_nguoi([r["owner"] for r in rows])
	for r in rows:
		ma = ma_theo_quay(r["vgb_quay"])
		ra.setdefault(ma, []).append({"user": r["owner"], "ten": ten.get(r["owner"]) or r["owner"], "so": cint(r["so"])})
	return ra


def _ten_nguoi(users):
	users = [u for u in dict.fromkeys(users or []) if u]
	if not users:
		return {}
	return {u["name"]: u["full_name"] or u["name"] for u in frappe.get_all(
		"User", filters={"name": ["in", users]}, fields=["name", "full_name"], limit_page_length=0)}


def _nguoi_dung_he():
	"""Tai khoan noi bo dang bat, de quan ly "+ Them nguoi" bang o tim."""
	return [{"user": u["name"], "ten": u["full_name"] or u["name"]} for u in frappe.get_all(
		"User", filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Administrator", "Guest"]]},
		fields=["name", "full_name"], order_by="full_name asc", limit_page_length=500)]


def _bao_dam_bang_gia(ten):
	"""Tao Price List ban ra cho diem neu chua co. Chay lai bao nhieu lan cung duoc."""
	if not ten or frappe.db.exists("Price List", ten):
		return ten
	frappe.get_doc({"doctype": "Price List", "price_list_name": ten, "selling": 1, "buying": 0,
		"enabled": 1, "currency": "VND"}).insert(ignore_permissions=True)
	return ten


def _sua_gia_duoc():
	return bool(QUYEN_SUA & set(frappe.get_roles()))


def _diem_co_bang(ma):
	d = theo_ma(ma)
	if not d:
		frappe.throw("Không có điểm bán %s." % (ma or "(trống)"))
	if not d["bang_gia"]:
		frappe.throw("Điểm %s đang bán giá chung. Bật Giá riêng ở Cài đặt, Điểm bán trước." % d["ten_ngan"])
	return d


@frappe.whitelist()
def bang_gia_diem(ma):
	"""Man Bang gia theo diem ban: moi mon ban, gia chung, gia rieng cua diem,
	so da ban o diem trong 30 ngay."""
	from vagabond.ban_hang import _kiem_quyen
	from frappe.utils import add_days, nowdate

	_kiem_quyen()
	d = _diem_co_bang(ma)
	gia = gia_dang_ap(_dong_gia_diem(d["bang_gia"]), _hom_nay())
	da_ban = {}
	if d["quay"]:
		for r in frappe.db.sql(
				"select sii.item_code, sum(sii.qty) sl from `tabSales Invoice Item` sii "
				"join `tabSales Invoice` si on si.name = sii.parent "
				"where si.docstatus = 1 and si.is_return = 0 and si.vgb_quay = %s and si.posting_date >= %s "
				"group by sii.item_code", (d["quay"], add_days(nowdate(), -SO_NGAY_GOI_Y)), as_dict=True):
			da_ban[r["item_code"]] = flt(r["sl"])
	mon = []
	for it in frappe.get_all("Item", filters={"is_sales_item": 1, "disabled": 0, "has_variants": 0},
			fields=["name", "item_name", "item_group", "standard_rate", "image"], order_by="item_name asc", limit_page_length=0):
		# Ảnh món để người sửa giá nhận ra món (AGENTS.md mục 2b.4, Codex PR #532).
		mon.append({"ma": it["name"], "ten": it["item_name"], "nhom": it["item_group"] or "", "anh": it.get("image") or "",
			"gia_chung": flt(it["standard_rate"]), "gia_diem": flt(gia.get(it["name"])),
			"da_ban": da_ban.get(it["name"], 0)})
	return {"diem": {"ma": d["ma"], "ten": d["ten"], "ten_ngan": d["ten_ngan"], "bang_gia": d["bang_gia"]},
		"mon": mon, "sua_duoc": 1 if _sua_gia_duoc() else 0, "so_ngay": SO_NGAY_GOI_Y}


def chuan_thay_doi(thay_doi, ma_hop_le):
	"""THUAN: [(ma mon, gia hoac None la bo gia rieng)] tu danh sach may
	khach gui. Ma la khong co trong danh muc thi bao ten, khong im lang bo."""
	if isinstance(thay_doi, str):
		thay_doi = json.loads(thay_doi or "[]")
	ra, la = [], []
	for x in thay_doi or []:
		ma = str((x or {}).get("ma") or "").strip()
		if not ma:
			continue
		if ma not in ma_hop_le:
			la.append(ma)
			continue
		try:
			ra.append((ma, doc_gia(x.get("gia"))))
		except ValueError as e:
			raise ValueError("%s: %s" % (ma, e))
	if la:
		raise ValueError("Không có món %s trong danh mục món bán. Tải lại bảng rồi sửa tiếp." % ", ".join(la[:5]))
	return list(dict(ra).items())


@frappe.whitelist(methods=["POST"])
def luu_gia(ma, thay_doi=None):
	"""Luu cac o gia rieng da doi. Gia trong la bo gia rieng (khoa han, khong xoa dong) (mon ve gia
	chung). Moi lan doi ghi vet tren mon: ai doi, luc nao, gia cu, gia moi."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not _sua_gia_duoc():
		frappe.throw("Chỉ quản lý cửa hàng, Sales quản lý hoặc kế toán mới sửa được giá bán.")
	d = _diem_co_bang(ma)
	_bao_dam_bang_gia(d["bang_gia"])
	hop_le = set(frappe.get_all("Item", filters={"is_sales_item": 1, "disabled": 0}, pluck="name", limit_page_length=0))
	try:
		ds_doi = chuan_thay_doi(thay_doi, hop_le)
	except ValueError as e:
		frappe.throw(str(e))
	so = 0
	for mon, gia in ds_doi:
		so += 1 if dat_gia_diem(d, mon, gia) else 0
	frappe.db.commit()
	return {"so": so}


def dat_gia_diem(d, mon, gia):
	"""Dat (hoac bo, khoa han khi gia rong) gia rieng cua mot mon o mot diem, ghi vet.
	Mot cho duy nhat cho ca man Bang gia lan man Tao mat hang. Tra True khi
	gia that su doi."""
	_bao_dam_bang_gia(d["bang_gia"])
	hn = _hom_nay()
	gia_cu, sua, khoa, them = ke_hoach_gia(_dong_gia_diem(d["bang_gia"], mon, chi_ban=False), gia, hn)
	if not (sua or khoa or them):
		return False
	# Khong xoa dong gia nao (QT-20): bo gia rieng hay dong thua thi khoa han
	# toi hom qua, dong van con de tra lai ai dat gia bao nhieu, tu ngay nao.
	for k in khoa:
		frappe.db.set_value("Item Price", k["name"], {x: v for x, v in k.items() if x != "name"})
	if sua:
		frappe.db.set_value("Item Price", sua[0], "price_list_rate", sua[1])
	if them:
		frappe.get_doc({"doctype": "Item Price", "item_code": mon, "price_list": d["bang_gia"],
			"price_list_rate": gia}).insert(ignore_permissions=True)
	_ghi_vet_gia(mon, d, gia_cu, gia)
	return True


def diem_co_gia_rieng():
	"""Cac diem dang bat co bang gia rieng, cho man Tao mat hang hien o gia."""
	return [{"ma": d["ma"], "ten": d["ten"], "ten_ngan": d["ten_ngan"]} for d in ds(chi_bat=True) if d["bang_gia"] and d["quay"]]


def cau_vet_gia(ten_diem, cu, moi):
	"""THUAN: dong ghi vet doi gia, vi du "Giá riêng NVHTN: 95.000 -> 70.000"."""
	def t(x):
		return "{:,.0f}".format(flt(x)).replace(",", ".") if flt(x) else "giá chung"
	return "Giá riêng %s: %s -> %s" % (ten_diem, t(cu), t(moi))


def _ghi_vet_gia(mon, d, cu, moi):
	try:
		frappe.get_doc({"doctype": "Comment", "comment_type": "Info", "reference_doctype": "Item",
			"reference_name": mon, "content": "%s - %s" % (cau_vet_gia(d["ten_ngan"], cu, moi), frappe.session.user)}
		).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "diem_ban: ghi vet doi gia")


COT_EXCEL = ("Mã món", "Tên món", "Nhóm món", "Giá chung", "Giá riêng")


def doc_bang_excel(dong):
	"""THUAN: tu cac dong Excel (dong dau la tieu de) ra [{ma, gia}].

	Tim cot theo TEN tieu de (Ma mon, Gia rieng...) chu khong theo vi tri,
	de nguoi dien chen them cot hay doi thu tu van doc dung. O gia trong
	nghia la ve gia chung."""
	dong = [list(r or []) for r in (dong or [])]
	if not dong:
		raise ValueError("Tệp Excel trống.")
	dau = [str(x or "").strip().lower() for x in dong[0]]
	def cot(*ten):
		for i, x in enumerate(dau):
			if any(x.startswith(t) for t in ten):
				return i
		return -1
	c_ma, c_gia = cot("mã món", "ma mon"), cot("giá riêng", "gia rieng")
	if c_ma < 0 or c_gia < 0:
		raise ValueError("Không thấy cột \"Mã món\" và \"Giá riêng\" ở dòng đầu. Tải Excel mẫu từ màn này rồi điền vào đó.")
	ra = []
	for i, r in enumerate(dong[1:], start=2):
		ma = str(r[c_ma] if c_ma < len(r) and r[c_ma] is not None else "").strip()
		if not ma:
			continue
		v = r[c_gia] if c_gia < len(r) else None
		try:
			ra.append({"ma": ma, "gia": doc_gia(v)})
		except ValueError as e:
			raise ValueError("Dòng %d (%s): %s" % (i, ma, e))
	return ra


@frappe.whitelist()
def xuat_excel_gia(ma):
	"""Tai Excel bang gia cua diem: moi mon ban, de dien cot Gia rieng roi nap lai."""
	import base64
	from frappe.utils.xlsxutils import make_xlsx

	kq = bang_gia_diem(ma)
	dong = [list(COT_EXCEL[:4]) + [COT_EXCEL[4] + " " + kq["diem"]["ten_ngan"]]]
	for m in kq["mon"]:
		dong.append([m["ma"], m["ten"], m["nhom"], m["gia_chung"] or None, m["gia_diem"] or None])
	tep = make_xlsx(dong, "Bang gia")
	return {"ten_file": "bang-gia-%s.xlsx" % kq["diem"]["ma"].lower(), "b64": base64.b64encode(tep.getvalue()).decode()}


@frappe.whitelist(methods=["POST"])
def nap_excel_gia(ma, b64=None):
	"""Doc tep Excel nguoi dung nap, tra cac o gia de man hien thanh "da doi"
	cho nguoi dung xem lai roi moi bam Luu. KHONG luu o buoc nay."""
	import base64
	import io

	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not _sua_gia_duoc():
		frappe.throw("Chỉ quản lý cửa hàng, Sales quản lý hoặc kế toán mới sửa được giá bán.")
	_diem_co_bang(ma)
	try:
		from openpyxl import load_workbook

		wb = load_workbook(io.BytesIO(base64.b64decode(b64 or "")), read_only=True, data_only=True)
		dong = [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]
	except Exception:
		frappe.throw("Không đọc được tệp. Chọn đúng tệp Excel (.xlsx) tải từ màn Bảng giá theo điểm bán.")
	try:
		return {"thay_doi": doc_bang_excel(dong)}
	except ValueError as e:
		frappe.throw(str(e))
