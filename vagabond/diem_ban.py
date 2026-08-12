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

import frappe
from frappe.utils import cint

from vagabond.lib import cfg

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

QUYEN_SUA = {"System Manager", "Accounts Manager", "Sales Manager"}


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
		"mst": str(d.get("mst") or "").strip(),
		"ky_hieu": str(d.get("ky_hieu") or "").strip(),
		"nguon": nguon_ds,
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
		tho = json.loads((cfg().get(TRUONG) or "").strip() or "[]")
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
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	return {
		"diem": ds(),
		"sua_duoc": 1 if QUYEN_SUA & set(frappe.get_roles()) else 0,
		"nguon_co_san": nguon_co_san(),
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
	ma_da_co, quay_da_co, nguon_da_co = {}, {}, {}
	for d in ra:
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
		for n in d["nguon"]:
			# Nguon dung chung giua cac diem CO QUAY thi khong sao: hoa don
			# quay nao cung mang vgb_quay nen ca he van tra ve dung diem. Nho
			# vay "Tai cho" va "Mang ve" khong con phai dinh ten chi nhanh
			# vao duoi nua (anh Viet 12/08/2026).
			#
			# Nhung diem ONLINE thi khong: don online khong mang ma quay nao,
			# neu no dung chung nguon voi mot diem khac thi khong con gi de
			# phan biet, va hoa don dien tu se xuat cho ca hai.
			cu = nguon_da_co.get(n)
			if cu and (not d["quay"] or not cu[1]):
				frappe.throw(
					"Nguồn đơn \"%s\" đang gán cho cả %s và %s, mà %s là điểm "
					"nhận đơn online. Đơn online không mang mã quầy nên không "
					"còn cách nào tách hai điểm, hoá đơn điện tử sẽ xuất hai lần."
					% (n, cu[0], d["ma"], cu[0] if not cu[1] else d["ma"])
				)
			if not cu:
				nguon_da_co[n] = (d["ma"], 1 if d["quay"] else 0)
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
	frappe.db.set_single_value(
		"Vagabond Settings", TRUONG, json.dumps(ra, ensure_ascii=False, indent=1)
	)
	frappe.db.commit()
	_ghi_vet(
		"Sửa danh sách điểm bán: %s"
		% ", ".join("%s%s" % (d["ma"], "" if d["bat"] else " (tắt)") for d in ra)
	)
	return {"diem": ds(), "sua_duoc": 1, "nguon_co_san": nguon_co_san()}


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
