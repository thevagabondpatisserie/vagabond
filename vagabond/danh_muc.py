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


def _series_hien(tt):
	"""Bo dem hien tai cua mot tien to.

	tabSeries la BANG THUAN, khong phai DocType - frappe.db.get_value
	("Series", ...) tra ve loi "Khong tim thay DocType Series". Phai doc
	thang bang SQL.
	"""
	try:
		r = frappe.db.sql("select `current` from `tabSeries` where name = %s", (tt,))
		return cint(r[0][0]) if r else 0
	except Exception:
		return 0


def _moc_lon_nhat(tt):
	"""So lon nhat da dung that trong danh muc cho tien to nay."""
	try:
		rows = frappe.db.sql("select name from `tabItem` where name like %s", (tt + "%",))
	except Exception:
		return 0
	mx = 0
	for r in rows:
		m = MAU_MA.match((r[0] or "").strip().upper())
		if m and m.group(1) == tt:
			mx = max(mx, cint(m.group(2)))
	return mx


def _so_ke_tiep(tt):
	return max(_series_hien(tt), _moc_lon_nhat(tt)) + 1


def _dong_bo_series(tt):
	"""Keo bo dem len bang so lon nhat da dung that.

	tabSeries co the chua he co dong nao cho tien to nay: 1.428 ma hang
	hien tai duoc tao bang nhieu duong khac nhau, co ma tao tay. Khong keo
	bo dem len truoc thi getseries tra ve 1, dam thang vao ma da co - ma
	vong thu lai vai chuc lan cung khong du de vuot qua mot nhom hai tram
	mon.
	"""
	mx = _moc_lon_nhat(tt)
	if mx <= _series_hien(tt):
		return
	try:
		frappe.db.sql(
			"insert into `tabSeries` (name, `current`) values (%s, %s) "
			"on duplicate key update `current` = greatest(`current`, %s)",
			(tt, mx, mx),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "danh_muc: khong dong bo duoc bo dem %s" % tt)


def _ma_moi(tt):
	"""Ma tiep theo cua mot tien to.

	getseries dem trong bang tabSeries, cung bo dem ma naming series cua
	ERPNext dang dung, nen khong dam vao day ma da cap. Van kiem lai su ton
	tai: bo dem co the tut lai sau neu ai do tung tao ma tay.
	"""
	tt = str(tt or "").strip().upper()
	if not tt:
		frappe.throw("Chưa biết tiền tố mã của nhóm này. Vui lòng điền một lần.")
	_dong_bo_series(tt)
	for _ in range(60):
		ma = "%s%s" % (tt, getseries(tt, SO_CHU_SO))
		if not frappe.db.exists("Item", ma):
			return ma
	frappe.throw("Không cấp được mã mới cho tiền tố %s, vui lòng thử lại." % tt)


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
	so = _so_ke_tiep(tt) if tt else 0
	canh_bao = []
	if nhom and not tt:
		canh_bao.append(
			'Nhóm "%s" chưa có mã hàng nào theo khuôn nên máy chưa đoán được tiền tố. Vui lòng điền tiền tố một lần, các món sau tự theo.' % nhom
		)
	qc = " ".join(str(quy_cach or "").split())
	if qc and not l["ban"]:
		canh_bao.append(
			"Quy cách của hàng mua vào không nên nằm trong tên món: hôm nhà cung cấp đổi túi 1 kg thành hai túi 500 gram là tên món thành sai. Nên ghi quy cách xuống phần mô tả, còn quy đổi đơn vị thì khai ở bảng quy đổi."
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
			'"%s" là nhóm cha, không gắn món thẳng vào được. Vui lòng chọn nhóm con.'
			% nhom
		)

	l = _loai(loai)
	ten = " ".join(str(ten or "").split())
	if len(ten) < 3:
		frappe.throw("Tên mặt hàng ngắn quá, vui lòng gõ đủ tên.")
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
			'Nhóm "%s" chưa có tiền tố mã. Vui lòng điền tiền tố (2 đến 6 chữ in hoa không dấu) một lần.' % nhom
		)
	if not re.match(r"^[A-Z]{2,6}$", tt):
		frappe.throw("Tiền tố mã chỉ gồm 2 đến 6 chữ in hoa không dấu, ví dụ BAWS.")

	# ERPNext co the dang duoc dat "Dat ten hang hoa theo" = Day so. Luc do
	# no de len ma minh vua cap va tra ve mot ma khac han - nguoi tao nhin
	# man hinh thay mot ma, trong kho lai la ma khac.
	if str(frappe.db.get_default("item_naming_by") or "").strip() == "Naming Series":
		frappe.throw(
			'Thiết lập kho đang để "Đặt tên hàng hoá theo" = Dãy số, nên ERPNext sẽ đè lên mã hệ thống vừa cấp. Nhờ anh chị đổi về Mã hàng trong Thiết lập kho rồi quay lại.'
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
			"ERPNext đặt mã <b>%s</b> chứ không phải %s như hệ thống dự kiến. Vui lòng kiểm tra lại Thiết lập kho." % (doc.name, ma)
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
def day_sang_pancake(item_code, cho_phep_gia_0=0):
	"""Nut Dong bo Pancake tren man Danh muc san pham."""
	_kiem_quyen()
	if not _duoc_tao():
		frappe.throw("Chỉ kế toán, thu mua hoặc giám đốc mới đẩy mã sang Pancake được.")
	from vagabond import pancake_sp

	return pancake_sp.tao_tren_pancake(item_code, cho_phep_gia_0=cho_phep_gia_0)


@frappe.whitelist()
def kiem_ma_tren_pancake(item_code):
	"""Nút "Kiểm lại": tra tình trạng một mã bên Pancake, KHÔNG tạo gì.

	Có cửa này vì bản gia cố 05/09/2026 trả về trạng thái "chưa rõ" khi lệnh
	tạo đã gửi mà không nghe được trả lời. Lúc đó việc đúng là đi kiểm, chứ
	không phải bấm tạo lần nữa.
	"""
	_kiem_quyen()
	from vagabond import pancake_sp

	return pancake_sp.trang_thai_tren_pancake(item_code)


@frappe.whitelist()
def gan_day(so_dong=30, tim="", trang=1):
	"""Tìm mã để đẩy sang Pancake. Mặc định là mấy mã vừa mở gần đây.

	VÌ SAO PHẢI CÓ Ô TÌM (Codex nêu 05/09/2026)
	--------------------------------------------
	Bản cũ chỉ trả về mấy mã mới nhất, trần 200. Mã cũ hơn thì không có
	đường nào mở lại để đẩy.

	Và bản cũ chưa được màn hình nào gọi tới, nên trên app chỉ đẩy được đúng
	cái mã VỪA tạo trong phiên đó: tải lại trang là nút biến mất. Uyên tạo
	mã hôm trước, hôm sau muốn đẩy thì không có cửa nào.

	Nay: gõ mã hoặc gõ tên để tìm bất kỳ mã nào, có phân trang.

	Mã ngừng dùng hoặc không phải hàng bán vẫn hiện ra để người ta biết nó
	tồn tại, nhưng mang cờ `day_duoc = 0`. Máy chủ chốt cờ đó chứ không để
	màn hình tự đoán, và `pancake_sp` chặn lần nữa lúc đẩy thật.
	"""
	_kiem_quyen()
	from vagabond import pancake_ket_qua as pkq

	moi_trang = max(1, min(200, cint(so_dong) or 30))
	trang = max(1, cint(trang) or 1)
	tu = (tim or "").strip()

	loc = {}
	if tu:
		loc = {"name": ["like", "%%%s%%" % tu]}
	truong = ["name", "item_name", "item_group", "stock_uom", "standard_rate",
		"disabled", "is_sales_item"]
	rows = frappe.get_all(
		"Item", filters=loc, fields=truong,
		order_by="creation desc",
		limit_start=(trang - 1) * moi_trang, limit_page_length=moi_trang,
	)
	# Gõ tên món thì tìm thêm theo tên, rồi gộp lại theo mã cho khỏi trùng.
	if tu and len(rows) < moi_trang:
		da_co = set(r["name"] for r in rows)
		for r in frappe.get_all(
			"Item", filters={"item_name": ["like", "%%%s%%" % tu]}, fields=truong,
			order_by="creation desc", limit_page_length=moi_trang - len(rows),
		):
			if r["name"] not in da_co:
				rows.append(r)

	for r in rows:
		r["day_duoc"] = 1 if pkq.duoc_xuat_ban(r.get("disabled"), r.get("is_sales_item")) else 0

	return {
		"mon": rows,
		"tao_duoc": 1 if _duoc_tao() else 0,
		"trang": trang,
		"moi_trang": moi_trang,
		"con_nua": 1 if len(rows) >= moi_trang else 0,
		"tim": tu,
	}
