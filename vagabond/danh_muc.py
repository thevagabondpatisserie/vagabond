# -*- coding: utf-8 -*-
"""Danh muc san pham: mo mot ma hang moi trong 7 quyet dinh (anh Viet 12/08/2026).

Man Item goc cua ERPNext co hon 80 truong. Ke toan, thu mua va giam doc mo
ra la khong biet bat dau tu dau, nen ket qua la 1.428 ma hang voi 30 nhom,
33 tien to, 27 ma khong theo khuon nao, va co ma ERPNext tu sinh kieu
"9ZKKL9YXG7BU" - dau vet cua nhung lan tao voi giua gio.

Man nay chi hoi BAY thu anh Viet chot:

  1. Nhom mon        2. Loai hang       3. Ten mat hang
  4. Quy cach / size 5. Gia ban         6. Bep hoac vi tri (neu can)
  7. Mo ta ngan (neu da co)

Con lai may tu dat theo LOAI HANG, dung luat anh Viet soan:

  Thanh pham       cho ban,  quan ly ton kho
  Nguyen vat lieu  cho mua,  quan ly ton kho
  Ban thanh pham   khong mua khong ban, quan ly ton kho
  Dich vu          khong quan ly ton kho

Ma hang KHONG go tay. May doc tien to dang dung THAT cua nhom do roi cap
so tiep theo. Khong cai cung bang tien to trong ma nguon: danh muc that
dang co 33 tien to, cai cung la vua sai vua phai deploy moi them duoc nhom.
"""

import re
import unicodedata

import frappe
from frappe.model.naming import getseries
from frappe.utils import cint, flt

QUYEN_TAO = {
	"System Manager",
	"Accounts Manager",
	"Sales Manager",
	"Item Manager",
	"Purchase Manager",
	"Purchase User",
	"Stock Manager",
}

SO_CHU_SO = 5
MAU_MA = re.compile(r"^([A-Z]{2,6})(\d{4,6})$")

# Luat anh Viet soan ngay 12/08/2026. "mua", "ban", "ton" la ba co
# is_purchase_item, is_sales_item, is_stock_item cua ERPNext.
LOAI_HANG = [
	{
		"k": "thanh_pham",
		"ten": "Thành phẩm",
		"mo": "Bánh, nước, món bán cho khách.",
		"mua": 0, "ban": 1, "ton": 1,
	},
	{
		"k": "nvl",
		"ten": "Nguyên vật liệu",
		"mo": "Bột, bơ, trái cây, bao bì - hàng mua về để làm.",
		"mua": 1, "ban": 0, "ton": 1,
	},
	{
		"k": "btp",
		"ten": "Bán thành phẩm",
		"mo": "Nhân, cốt, sốt bếp tự làm rồi để dùng tiếp.",
		"mua": 0, "ban": 0, "ton": 1,
	},
	{
		"k": "dich_vu",
		"ten": "Dịch vụ",
		"mo": "Phí giao hàng, phí trang trí - không có gì để đếm tồn.",
		"mua": 0, "ban": 1, "ton": 0,
	},
]


def _loai(k):
	for x in LOAI_HANG:
		if x["k"] == k:
			return x
	return LOAI_HANG[0]


def _kiem_quyen():
	from vagabond.ban_hang import _kiem_quyen as kq

	kq()


def _duoc_tao():
	return bool(QUYEN_TAO & set(frappe.get_roles()))


# --------------------------------------------------------------- ten va ma


def khong_dau(s):
	s = unicodedata.normalize("NFD", str(s or ""))
	s = "".join(c for c in s if unicodedata.category(c) != "Mn")
	return s.replace("đ", "d").replace("Đ", "D")


def chuan_ten(s):
	"""Ten ve dang de so sanh: bo dau, bo dau cau, gop khoang trang."""
	s = khong_dau(s).lower()
	s = re.sub(r"[^a-z0-9]+", " ", s)
	return " ".join(s.split())


def tien_to_nhom(nhom):
	"""Tien to ma dang dung THAT cua mot nhom hang.

	Doc tu chinh danh muc chu khong tra bang cai cung: danh muc that dang
	co 33 tien to, ma nguon chi biet 13. Nhom nao chua co ma nao thi tra ve
	rong, luc do man hinh hoi nguoi dung go tien to mot lan.
	"""
	try:
		rows = frappe.get_all(
			"Item", filters={"item_group": nhom}, fields=["name"], limit_page_length=0
		)
	except Exception:
		return ""
	dem = {}
	for r in rows:
		m = MAU_MA.match((r.get("name") or "").strip().upper())
		if m:
			dem[m.group(1)] = dem.get(m.group(1), 0) + 1
	if not dem:
		return ""
	return sorted(dem.items(), key=lambda x: (-x[1], x[0]))[0][0]


def _ma_moi(tt):
	"""Ma tiep theo cua mot tien to.

	getseries dem trong bang tabSeries, cung bo dem ma naming series cua
	ERPNext dang dung, nen khong dam vao day ma da cap. Van kiem lai su ton
	tai: bo dem co the tut lai sau neu ai do tung tao ma tay.
	"""
	tt = str(tt or "").strip().upper()
	if not tt:
		frappe.throw("Chưa biết tiền tố mã của nhóm này. Điền giúp em một lần.")
	for _ in range(60):
		ma = "%s%s" % (tt, getseries(tt, SO_CHU_SO))
		if not frappe.db.exists("Item", ma):
			return ma
	frappe.throw("Không cấp được mã mới cho tiền tố %s, thử lại giúp em." % tt)


def _ten_day_du(loai, ten, quy_cach):
	"""Ten hien tren bill va bao cao.

	Quy cach chi duoc gan vao ten cua hang BAN RA. O hang mua vao, quy cach
	la bao bi cua nha cung cap: hom 04/08 Fuji doi tu tui 1 kg sang hai tui
	500 gram, san pham khong doi ma ten mon lap tuc thanh sai. Ben hang ban
	ra thi nguoc lai, con so chinh la san pham: banh 110 gram khac banh 150
	gram (anh Viet chot 04/08/2026).
	"""
	ten = " ".join(str(ten or "").split())
	qc = " ".join(str(quy_cach or "").split())
	if qc and loai["ban"]:
		return "%s, %s" % (ten, qc)
	return ten


# --------------------------------------------------------------- man app


@frappe.whitelist()
def cai_dat():
	_kiem_quyen()
	nhom = frappe.get_all(
		"Item Group",
		filters={"is_group": 0},
		fields=["name", "custom_bep_phu_trach"],
		order_by="name asc",
		limit_page_length=0,
	)
	return {
		"nhom": [
			{"ten": r["name"], "bep": r.get("custom_bep_phu_trach") or ""} for r in nhom
		],
		"loai": LOAI_HANG,
		"tao_duoc": 1 if _duoc_tao() else 0,
		"co_bep": 1 if _co_truong("Item", "custom_bep_phu_trach") else 0,
	}


def _co_truong(dt, fieldname):
	try:
		return bool(frappe.get_meta(dt).get_field(fieldname))
	except Exception:
		return False


def _dvt_quen(nhom):
	"""Don vi tinh dang dung nhieu nhat trong nhom, de goi y."""
	try:
		rows = frappe.get_all(
			"Item", filters={"item_group": nhom}, fields=["stock_uom"], limit_page_length=0
		)
	except Exception:
		return ""
	dem = {}
	for r in rows:
		u = (r.get("stock_uom") or "").strip()
		if u:
			dem[u] = dem.get(u, 0) + 1
	if not dem:
		return ""
	return sorted(dem.items(), key=lambda x: (-x[1], x[0]))[0][0]


@frappe.whitelist()
def xem_truoc(nhom=None, loai=None, ten=None, quy_cach=None):
	"""Ma va ten may se dat, kem canh bao - hien ngay khi nguoi dung dang go.

	Chi XEM, khong cap ma that: cap ma o day thi moi lan go them mot chu la
	dot mat mot so trong day, ngay lam viec la thung mot khoang lon.
	"""
	_kiem_quyen()
	nhom = str(nhom or "").strip()
	l = _loai(loai)
	tt = tien_to_nhom(nhom) if nhom else ""
	so = 0
	if tt:
		try:
			so = cint(frappe.db.get_value("Series", tt, "current")) + 1
		except Exception:
			so = 0
	canh_bao = []
	if nhom and not tt:
		canh_bao.append(
			"Nhóm \"%s\" chưa có mã hàng nào theo khuôn nên máy chưa đoán được "
			"tiền tố. Điền tiền tố giúp em một lần, các món sau tự theo." % nhom
		)
	qc = " ".join(str(quy_cach or "").split())
	if qc and not l["ban"]:
		canh_bao.append(
			"Quy cách của hàng mua vào không nên nằm trong tên món: hôm nhà cung "
			"cấp đổi túi 1 kg thành hai túi 500 gram là tên món thành sai. Em ghi "
			"quy cách xuống phần mô tả, còn quy đổi đơn vị thì khai ở bảng quy đổi."
		)
	return {
		"tien_to": tt,
		"ma_du_kien": ("%s%s" % (tt, str(so).zfill(SO_CHU_SO))) if (tt and so) else "",
		"ten_day_du": _ten_day_du(l, ten, qc),
		"dvt_goi_y": _dvt_quen(nhom) if nhom else "",
		"canh_bao": canh_bao,
		"trung": tim_trung(ten=ten, quy_cach=quy_cach, nhom=nhom, loai=loai),
	}


@frappe.whitelist()
def tim_trung(ten=None, quy_cach=None, nhom=None, loai=None, so_dong=8):
	"""Mon da co ten gan giong. Ra TRUOC khi nguoi dung bam Tao.

	Danh muc that dang co 172 cap ten chuan hoa giong het nhau. Bat o day
	re hon nhieu so voi gop ma sau: gop ma la phai keo theo moi hoa don,
	phieu nhap kho va lich su ban hang da tro toi.
	"""
	_kiem_quyen()
	day_du = _ten_day_du(_loai(loai), ten, quy_cach)
	goc = chuan_ten(day_du)
	if len(goc) < 3:
		return []
	tu = [t for t in goc.split() if len(t) > 2]
	if not tu:
		tu = goc.split()
	# Loc so bo o may chu bang mot tu dai nhat, roi so khop chinh xac o day.
	moi = sorted(tu, key=len, reverse=True)[0]
	try:
		rows = frappe.db.sql(
			"""
			select name, item_name, item_group, disabled
			from `tabItem`
			where item_name like %s
			limit 400
			""",
			("%" + moi + "%",),
			as_dict=True,
		)
	except Exception:
		return []
	ra = []
	for r in rows:
		c = chuan_ten(r.get("item_name"))
		if not c:
			continue
		if c == goc:
			muc, vi = 3, "trùng y hệt tên"
		elif goc in c or c in goc:
			muc, vi = 2, "tên nằm gọn trong nhau"
		else:
			chung = set(c.split()) & set(goc.split())
			if len(chung) < max(2, len(goc.split()) - 1):
				continue
			muc, vi = 1, "gần giống"
		ra.append(
			{
				"ma": r["name"],
				"ten": r.get("item_name") or r["name"],
				"nhom": r.get("item_group") or "",
				"tat": 1 if cint(r.get("disabled")) else 0,
				"muc": muc,
				"vi_sao": vi,
			}
		)
	ra.sort(key=lambda x: (-x["muc"], x["ten"]))
	return ra[: max(1, min(30, cint(so_dong) or 8))]


@frappe.whitelist()
def tao(
	nhom=None,
	loai=None,
	ten=None,
	quy_cach=None,
	gia_ban=None,
	bep=None,
	mo_ta=None,
	dvt=None,
	tien_to=None,
	bo_qua_trung=0,
):
	"""Mo mot ma hang moi."""
	_kiem_quyen()
	if not _duoc_tao():
		frappe.throw("Chỉ kế toán, thu mua hoặc giám đốc mới mở được mã hàng mới.")

	nhom = str(nhom or "").strip()
	if not nhom:
		frappe.throw("Chưa chọn nhóm món.")
	if not frappe.db.exists("Item Group", nhom):
		frappe.throw("Không có nhóm món \"%s\"." % nhom)
	if cint(frappe.db.get_value("Item Group", nhom, "is_group")):
		frappe.throw(
			"\"%s\" là nhóm cha, không gắn món thẳng vào được. Chọn nhóm con giúp em."
			% nhom
		)

	l = _loai(loai)
	ten = " ".join(str(ten or "").split())
	if len(ten) < 3:
		frappe.throw("Tên mặt hàng ngắn quá, gõ đủ tên giúp em.")
	qc = " ".join(str(quy_cach or "").split())
	day_du = _ten_day_du(l, ten, qc)

	if not cint(bo_qua_trung):
		trung = [t for t in tim_trung(ten=ten, quy_cach=qc, nhom=nhom, loai=loai) if t["muc"] >= 3]
		if trung:
			frappe.throw(
				"Đã có mã %s tên \"%s\" (nhóm %s). Dùng lại mã đó, hoặc bấm Tạo "
				"lần nữa nếu chắc chắn đây là món khác."
				% (trung[0]["ma"], trung[0]["ten"], trung[0]["nhom"])
			)

	tt = str(tien_to or "").strip().upper() or tien_to_nhom(nhom)
	if not tt:
		frappe.throw(
			"Nhóm \"%s\" chưa có tiền tố mã. Điền tiền tố (2 đến 6 chữ in hoa "
			"không dấu) giúp em một lần." % nhom
		)
	if not re.match(r"^[A-Z]{2,6}$", tt):
		frappe.throw("Tiền tố mã chỉ gồm 2 đến 6 chữ in hoa không dấu, ví dụ BAWS.")

	# ERPNext co the dang duoc dat "Dat ten hang hoa theo" = Day so. Luc do
	# no de len ma minh vua cap va tra ve mot ma khac han - nguoi tao nhin
	# man hinh thay mot ma, trong kho lai la ma khac.
	if str(frappe.db.get_default("item_naming_by") or "").strip() == "Naming Series":
		frappe.throw(
			"Thiết lập kho đang để \"Đặt tên hàng hoá theo\" = Dãy số, nên "
			"ERPNext sẽ đè lên mã em vừa cấp. Nhờ anh chị đổi về Mã hàng trong "
			"Thiết lập kho rồi quay lại giúp em."
		)

	ma = _ma_moi(tt)
	dv = str(dvt or "").strip() or _dvt_quen(nhom) or "Cái"
	if not frappe.db.exists("UOM", dv):
		frappe.throw("Chưa có đơn vị tính \"%s\" trong hệ thống." % dv)

	doc = frappe.new_doc("Item")
	doc.item_code = ma
	doc.item_name = day_du
	doc.item_group = nhom
	doc.stock_uom = dv
	doc.is_stock_item = l["ton"]
	doc.is_sales_item = l["ban"]
	doc.is_purchase_item = l["mua"]
	doc.description = str(mo_ta or "").strip() or day_du
	if qc and not l["ban"]:
		# Quy cach cua hang mua vao khong vao ten thi phai nam o mot cho doc
		# duoc, khong thi mat luon thong tin nguoi tao vua go.
		doc.description = ("%s\nQuy cách: %s" % (doc.description, qc)).strip()
	if flt(gia_ban):
		doc.standard_rate = flt(gia_ban)
	if bep and _co_truong("Item", "custom_bep_phu_trach"):
		doc.set("custom_bep_phu_trach", bep)
	doc.flags.ignore_permissions = True
	doc.insert()
	frappe.db.commit()
	if doc.name != ma:
		# Khong im lang: ma tren man hinh va ma trong kho phai la mot.
		frappe.msgprint(
			"ERPNext đặt mã <b>%s</b> chứ không phải %s như em dự kiến. Kiểm tra "
			"lại Thiết lập kho giúp em." % (doc.name, ma)
		)

	return {
		"ma": doc.name,
		"ten": doc.item_name,
		"nhom": doc.item_group,
		"dvt": doc.stock_uom,
		"gia_ban": flt(doc.standard_rate),
		"ban": cint(doc.is_sales_item),
		"mua": cint(doc.is_purchase_item),
		"ton": cint(doc.is_stock_item),
	}


@frappe.whitelist()
def day_sang_pancake(item_code):
	"""Nut Dong bo Pancake tren man Danh muc san pham."""
	_kiem_quyen()
	if not _duoc_tao():
		frappe.throw("Chỉ kế toán, thu mua hoặc giám đốc mới đẩy mã sang Pancake được.")
	from vagabond import pancake_sp

	return pancake_sp.tao_tren_pancake(item_code)


@frappe.whitelist()
def gan_day(so_dong=30):
	"""May ma vua mo, de nguoi tao xem lai va bam dong bo Pancake."""
	_kiem_quyen()
	rows = frappe.get_all(
		"Item",
		fields=["name", "item_name", "item_group", "stock_uom", "standard_rate", "disabled"],
		order_by="creation desc",
		limit_page_length=max(1, min(200, cint(so_dong) or 30)),
	)
	return {"mon": rows, "tao_duoc": 1 if _duoc_tao() else 0}
