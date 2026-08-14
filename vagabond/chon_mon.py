"""Bo chon mon dung chung cho ca he thong.

Anh Viet 14/08/2026: *"Chỗ chọn danh mục hàng hoá thì anh nhớ là em đã hứa là
đồng bộ ở tất cả các nơi đều giống như nhau đó là có hình ảnh của món nữa,
giờ thì sao lại không có hình món gì cả. Em làm triệt để lại phần này nhé.
Chắc phải đưa cái bảng chọn món này thành 1 cái trong kiến trúc backend của
em?"*

Nen tu day tro di CHI CO MOT cho tra ve danh sach mon cho moi bang chon
trong app. Ham nay LUON tra kem hinh anh; man nao quen hoi hinh cung van co
hinh. Muon them mot truong cho bang chon thi sua o day, khong sua rai rac.

Hai nguon gop lai lam mot:
  - Item trong danh muc: hinh o Item.image, gia o bang gia ban mac dinh;
  - Bao Gia Thu Vien: mon thiet ke rieng va cac khoan phi, khong nam trong
    kho nhung van phai chon duoc y het mon thuong.
"""

import frappe
from frappe.utils import flt

# Nhom khong bao gio duoc bay ra bang chon ban hang: nguyen lieu, ban thanh
# pham, bao bi, cong cu. Truoc day moi man tu chep lai danh sach nay, lech
# nhau luc nao khong biet - gio de mot cho.
NHOM_AN = [
	"Nguyên vật liệu Thô",
	"Bán thành phẩm Bánh",
	"Bán thành phẩm Nước",
	"Nhân bán thành phẩm",
	"Công cụ Dụng cụ",
	"Bao bì",
	"Văn phòng phẩm",
	"Tài sản Cố định",
]

TEP_ANH_MAC_DINH = ""


def _bang_gia_ban():
	return (
		frappe.db.get_single_value("Selling Settings", "selling_price_list")
		or "Standard Selling"
	)


def _gia_ban(ma_ds):
	"""Gia ban niem yet cua mot loat mon, lay ban moi nhat."""
	if not ma_ds:
		return {}
	ra = {}
	for g in frappe.get_all(
		"Item Price",
		filters={
			"item_code": ["in", ma_ds],
			"price_list": _bang_gia_ban(),
			"selling": 1,
		},
		fields=["item_code", "price_list_rate", "uom"],
		order_by="modified desc",
	):
		ra.setdefault(g["item_code"], g)
	return ra


def _sach(s, dai=400):
	return frappe.utils.strip_html(str(s or "")).strip()[:dai]


def _tu_item(it, gia):
	g = gia.get(it["name"]) or {}
	return {
		"ma": it["name"],
		"nguon": "item",
		"loai": "Món",
		"ten": it.get("item_name") or it["name"],
		"ten_en": "",
		"nhom": it.get("item_group") or "",
		"hinh": it.get("image") or "",
		"gia": flt(g.get("price_list_rate")) or flt(it.get("standard_rate")),
		"dvt": g.get("uom") or it.get("stock_uom") or "",
		"dvt_en": "",
		"mo_ta": _sach(it.get("description")),
		"mo_ta_en": "",
		"di_ung_vi": "",
		"di_ung_en": "",
		"kich_thuoc": "",
		"gia_chu_vi": "",
		"gia_chu_en": "",
		"tim": "%s %s" % (it["name"], it.get("item_name") or ""),
	}


def _tu_thu_vien(t):
	return {
		"ma": t["name"],
		"nguon": "thu_vien",
		"loai": t.get("loai") or "Món",
		"ten": t.get("ten_vi") or t["name"],
		"ten_en": t.get("ten_en") or "",
		"nhom": t.get("nhom") or ("Phí và dịch vụ" if t.get("loai") != "Món" else "Món thiết kế riêng"),
		"hinh": t.get("hinh") or "",
		"gia": flt(t.get("don_gia")),
		"dvt": t.get("dvt_vi") or "",
		"dvt_en": t.get("dvt_en") or "",
		"mo_ta": _sach(t.get("mo_ta_vi"), 900),
		"mo_ta_en": _sach(t.get("mo_ta_en"), 900),
		"di_ung_vi": t.get("di_ung_vi") or "",
		"di_ung_en": t.get("di_ung_en") or "",
		"kich_thuoc": t.get("kich_thuoc") or "",
		"gia_chu_vi": t.get("gia_chu_vi") or "",
		"gia_chu_en": t.get("gia_chu_en") or "",
		"ma_item": t.get("ma_item") or "",
		"tim": "%s %s %s" % (t.get("ten_vi") or "", t.get("ten_en") or "", t.get("nhom") or ""),
	}


@frappe.whitelist()
def nguon(tim=None, nhom=None, gioi_han=800, ke_thu_vien=0, chi_thu_vien=0):
	"""Danh sach mon cho bang chon, LUON kem hinh anh.

	ke_thu_vien = 1 thi gop them Thu vien bao gia vao (man bao gia dung).
	chi_thu_vien = 1 thi chi lay Thu vien (man quan ly thu vien dung).
	"""
	mon = []

	if not int(chi_thu_vien or 0):
		dk = ["i.disabled = 0", "i.is_sales_item = 1"]
		tham = {}
		if NHOM_AN:
			dk.append("i.item_group not in %(an)s")
			tham["an"] = NHOM_AN
		if nhom:
			dk.append("i.item_group = %(nhom)s")
			tham["nhom"] = nhom
		if tim:
			dk.append("(i.item_name like %(tim)s or i.name like %(tim)s)")
			tham["tim"] = "%%%s%%" % tim
		ds = frappe.db.sql(
			"""select i.name, i.item_name, i.item_group, i.stock_uom, i.image,
				i.description, i.standard_rate
			from `tabItem` i where %s order by i.item_name limit %d"""
			% (" and ".join(dk), int(gioi_han or 800)),
			tham,
			as_dict=True,
		)
		gia = _gia_ban([x["name"] for x in ds])
		mon += [_tu_item(x, gia) for x in ds]

	if int(ke_thu_vien or 0) or int(chi_thu_vien or 0):
		loc = {"dung": 1}
		if nhom:
			loc["nhom"] = nhom
		tv = frappe.get_all(
			"Bao Gia Thu Vien",
			filters=loc,
			fields=[
				"name", "loai", "nhom", "ten_vi", "ten_en", "ma_item", "hinh",
				"kich_thuoc", "don_gia", "dvt_vi", "dvt_en", "gia_chu_vi",
				"gia_chu_en", "mo_ta_vi", "mo_ta_en", "di_ung_vi", "di_ung_en",
			],
			order_by="thu_tu asc, ten_vi asc",
			limit_page_length=0,
		)
		if tim:
			t = str(tim).lower()
			tv = [
				x for x in tv
				if t in ((x.get("ten_vi") or "") + " " + (x.get("ten_en") or "")).lower()
			]
		# Mon thu vien co ma_item ma chua co hinh thi keo hinh tu Item ve, de
		# khong bao gio co dong nao thieu anh tren bang chon.
		thieu = [x["ma_item"] for x in tv if x.get("ma_item") and not x.get("hinh")]
		anh = {}
		if thieu:
			for it in frappe.get_all(
				"Item", filters={"name": ["in", thieu]}, fields=["name", "image"],
				limit_page_length=0,
			):
				if it.get("image"):
					anh[it["name"]] = it["image"]
		for x in tv:
			if not x.get("hinh") and anh.get(x.get("ma_item")):
				x["hinh"] = anh[x["ma_item"]]
		mon = [_tu_thu_vien(x) for x in tv] + mon

	dem = {}
	for m in mon:
		k = m["nhom"] or "Chưa phân nhóm"
		dem[k] = dem.get(k, 0) + 1
	nhom_ds = [{"ten": k, "so": v} for k, v in sorted(dem.items(), key=lambda x: -x[1])]

	return {
		"nhom": nhom_ds,
		"mon": mon,
		"so_thieu_anh": len([m for m in mon if not m["hinh"]]),
	}


@frappe.whitelist()
def thieu_anh(gioi_han=200):
	"""Mon ban ra chua co anh, de ai do bo sung dan. Bang chon van chay
	binh thuong voi mon chua co anh, chi la nhin kem hap dan."""
	ds = frappe.get_all(
		"Item",
		filters={
			"disabled": 0,
			"is_sales_item": 1,
			"image": ["in", ["", None]],
			"item_group": ["not in", NHOM_AN],
		},
		fields=["name", "item_name", "item_group"],
		order_by="item_group asc, item_name asc",
		limit_page_length=int(gioi_han or 200),
	)
	theo_nhom = {}
	for x in ds:
		theo_nhom.setdefault(x["item_group"], []).append(x["item_name"])
	return {
		"so": len(ds),
		"theo_nhom": [
			{"nhom": k, "so": len(v), "vd": v[:5]}
			for k, v in sorted(theo_nhom.items(), key=lambda x: -len(x[1]))
		],
	}
