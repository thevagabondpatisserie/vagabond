# -*- coding: utf-8 -*-
"""Kiem kho theo diem ban: ton dau, nhap theo dot, da ban, co the ban.

Anh Viet 02/09/2026: *"Trong man kiem banh theo ngay em cho them 2 tab nua
la Kiem banh 9 TCV va tab Kiem banh NVHTN dum anh voi cac truong ton dau,
nhap banh (chia ra cac dot: dot 1, dot 2, dot 3,...), da ban (tu dong bo
realtime tu hoa don ban hang sang), co the ban,... so co the ban nay se
hien thi sang man tinh tien luon ke ben moi mon khi ma thu ngan tim mon de
bam cho khach de biet mon do con hay khong. (Anh se dung man nay luon de
kiem xuat nhap ton cho D1 chu khong dung cai man nhap kho em lam, cho
tien)"*

Khac gi voi bang "Kiem banh ngay" da co
---------------------------------------
Bang cu dem banh cua BEP theo NGAY GIAO, nguon so la don Pancake. No tra
loi cau "hom nay con nhan duoc bao nhieu don nua".

Bang nay dem banh TRONG TU cua MOT QUAY, nguon so la hoa don ban ra tai
chinh quay do. No tra loi cau "ngay luc nay tren quay con bao nhieu cai".
Hai cau hoi khac nhau nen hai bang khong tron vao nhau duoc.

Ba dieu phai giu
----------------
1. Cot "da ban" KHONG SUA TAY. May doc thang tu hoa don ban ra cua dung
   quay do trong dung ngay do. Mo cua cho sua tay la mo cua cho lech.
2. Hoa don con NHAP (docstatus 0) van tinh la da ban. Thu ngan bam mon cho
   khach la cai banh do roi khoi tu, ke toan chua ghi so khong lam no quay
   lai. Cung mot le voi bai hoc v377.
3. Ton dau ngay mai lay theo SO KIEM TAY neu co nguoi kiem, khong co thi
   lay so may tinh. Nguoi dem tu bao gio cung dung hon phep tru.

Vi sao khong lam bang doctype kiem ke cua ERPNext
-------------------------------------------------
Kiem ke ERPNext ghi thang vao so cai kho va can quyen Stock Manager, moi
lan luu la mot but toan. Bang nay la so tay cua quay, sales bam tren dien
thoai vai chuc lan mot ngay. Hai muc dich khac han nhau. Muon dua so nay
vao so cai thi van phai qua phieu kiem ke that, va do la viec rieng.
"""

import json

import frappe
from frappe.utils import add_days, cint, getdate, now_datetime

DT = "Vagabond Kiem Kho Diem"
DT_DONG = "Vagabond Kiem Kho Dong"

SO_DOT = 6
O_NHAP = tuple("nhap_%d" % i for i in range(1, SO_DOT + 1))

# Cot nguoi duoc sua tay. "da ban", "co the ban", "lech" khong nam trong
# day - do la ca ly do bang nay ton tai.
SUA_DUOC = frozenset(("ton_dau", "hong", "dieu_chinh", "kiem_tay", "ghi_chu")) | frozenset(O_NHAP)

TT_BAN = "Dang ban"
TT_CHOT = "Da chot"

# Ma may TU THEM vao bang khi thay co ban ra. Chi banh, vi neu tu them ca
# ca phe, tra, topping thi bang cua mot quay dai vai tram dong va khong ai
# doc noi. Nhung thu khac van THEM TAY duoc, va them roi thi may van dem.
TIEN_TO_TU_THEM = ("BAWC", "BAWS", "BANU", "BAEN", "BACF", "BASS")

QUYEN_SUA = {"System Manager", "Accounts Manager", "Sales Manager"}


# ----------------------------------------------------------- phan THUAN
# Khong cham Frappe, kiem thu duoc tren may CI tay khong.

def la_banh(ma):
	"""Ma nay co phai loai may tu dua vao bang khong. THUAN."""
	return str(ma or "").strip().upper().startswith(TIEN_TO_TU_THEM)


def ten_phieu(diem, ngay):
	"""Ten phieu cua mot diem trong mot ngay. THUAN."""
	return "KKD-%s-%s" % (str(diem or "").strip().upper(), ngay)


def tong_nhap(o):
	"""Cong sau dot nhap lai. THUAN. Nhan dict hoac doc row."""
	t = 0
	for k in O_NHAP:
		t += cint((o.get(k) if hasattr(o, "get") else getattr(o, k, 0)) or 0)
	return t


def tinh_co_the_ban(ton_dau, nhap, da_ban, hong, dieu_chinh):
	"""Con lai tren quay. THUAN.

	Khong ep ve khong: so am la dau hieu co cai da ban ma khong ai ghi
	nhap, va do chinh la thu can nhin thay chu khong phai thu can giau.
	"""
	return cint(ton_dau) + cint(nhap) - cint(da_ban) - cint(hong) + cint(dieu_chinh)


def tinh_lech(kiem_tay, co_kiem, co_the_ban):
	"""Kiem tay tru so may. THUAN. Chua ai kiem thi tra 0."""
	if not co_kiem:
		return 0
	return cint(kiem_tay) - cint(co_the_ban)


def dot_ke_tiep(o):
	"""Dot nhap trong dau tien, 0 neu sau dot da day. THUAN."""
	for i, k in enumerate(O_NHAP, start=1):
		if not cint((o.get(k) if hasattr(o, "get") else getattr(o, k, 0)) or 0):
			return i
	return 0


def dang_theo_doi(o):
	"""Dong nay da co ai khai so chua. THUAN.

	Dong may TU THEM vi thay co ban ra ma chua ai khai ton dau, chua ai ghi
	dot nhap nao, thi KHONG phai la dong dang theo doi ton. Con lai cua no
	la mot so am vo nghia (bang dung so da ban), va man tinh tien ma ve chip
	"het" cho nhung dong do la chan ban ca tu banh trong ngay dau bat bang.

	Co nguoi cham vao mot o bat ky la tu do tro di dong duoc theo doi that.
	"""
	lay = (lambda k: (o.get(k) if hasattr(o, "get") else getattr(o, k, 0)) or 0)
	if cint(lay("theo_doi")):
		return True
	# Luoi do cho phieu dung truoc khi co co `theo_doi`: co so khai la co
	# theo doi. Khong co luoi nay thi cac phieu cua ngay 02/09 mat chip.
	return bool(cint(lay("ton_dau")) or tong_nhap(o) or cint(lay("hong")) or cint(lay("dieu_chinh")))


def con_lai_ngay_mai(kiem_tay, co_kiem, co_the_ban):
	"""So chay sang ton dau ngay mai. THUAN.

	Co nguoi dem tu thi lay so nguoi dem. Nguoi dem bao gio cung dung hon
	phep tru, vi phep tru khong biet cai banh roi xuong san.
	"""
	so = cint(kiem_tay) if co_kiem else cint(co_the_ban)
	return max(0, so)


# ------------------------------------------------------ phan cham Frappe

def _diem_co_quay():
	"""Cac diem ban co quay that, theo thu tu cau hinh."""
	from vagabond import diem_ban

	return [d for d in diem_ban.ds(chi_bat=True) if d["quay"]]


def _kiem_diem(diem):
	ma = str(diem or "").strip().upper()
	for d in _diem_co_quay():
		if d["ma"] == ma:
			return d
	frappe.throw("Điểm bán %s không có quầy bán trực tiếp." % (ma or "(trống)"))


def _duoc_sua():
	vai = set(frappe.get_roles())
	from vagabond.vai_cua_hang import VAI_QLCH

	return bool(vai & (QUYEN_SUA | {VAI_QLCH}))


def _chan_neu_khong_duoc_sua():
	if not _duoc_sua():
		frappe.throw("Anh chị không có quyền sửa bảng kiểm kho.")


def da_ban(diem, ngay):
	"""{ma_hang: so luong} ban ra tai quay nay trong ngay nay.

	docstatus < 2 - bill con NHAP van tinh, xem dieu 2 dau tep.
	vgb_huy = 0   - bill da huy tra hang ve tu.
	vgb_tam_tinh  - phieu tam tinh chua phai ban, khong tru.
	"""
	try:
		r = frappe.db.sql(
			"""select sii.item_code as ma, sum(sii.qty) as sl
			from `tabSales Invoice Item` sii
			join `tabSales Invoice` si on si.name = sii.parent
			where si.docstatus < 2
			  and ifnull(si.vgb_huy, 0) = 0
			  and ifnull(si.vgb_tam_tinh, 0) = 0
			  and ifnull(si.vgb_quay, '') = %s
			  and si.posting_date = %s
			group by sii.item_code""",
			(str(diem or "").strip().upper(), getdate(ngay)),
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "kiem_kho: dem da ban loi")
		return {}
	ra = {}
	for d in r:
		ma = str(d.get("ma") or "").strip()
		if not ma:
			continue
		ra[ma] = ra.get(ma, 0) + cint(d.get("sl"))
	return ra


def _ten_hang(ds_ma):
	if not ds_ma:
		return {}
	try:
		r = frappe.get_all(
			"Item", filters={"name": ["in", list(ds_ma)]},
			fields=["name", "item_name"], limit_page_length=0, ignore_permissions=True,
		)
	except Exception:
		return {}
	return {d["name"]: d.get("item_name") or d["name"] for d in r}


def _phieu_truoc(diem, ngay):
	"""Phieu cua ngay lien truoc, de keo ton dau sang."""
	ma = ten_phieu(diem, add_days(getdate(ngay), -1))
	if frappe.db.exists(DT, ma):
		return frappe.get_doc(DT, ma)
	return None


def _lay_hoac_tao(diem, ngay):
	d = _kiem_diem(diem)
	ngay = getdate(ngay)
	ma = ten_phieu(d["ma"], ngay)
	if frappe.db.exists(DT, ma):
		return frappe.get_doc(DT, ma)
	doc = frappe.new_doc(DT)
	doc.diem = d["ma"]
	doc.ngay = ngay
	doc.tinh_trang = TT_BAN
	cu = _phieu_truoc(d["ma"], ngay)
	if cu:
		for r in cu.dong:
			ton = con_lai_ngay_mai(r.kiem_tay, _co_kiem(r), r.co_the_ban)
			if not ton and not la_banh(r.ma_hang):
				# Mon them tay ma het sach thi khong keo sang, de bang
				# ngay moi khong dai them vi nhung dong bang khong.
				continue
			doc.append("dong", {
				"ma_hang": r.ma_hang, "ten_banh": r.ten_banh, "ton_dau": ton,
				"theo_doi": 1 if dang_theo_doi(r) else 0,
			})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc


def _co_kiem(r):
	"""Dong nay da co nguoi dem tay chua.

	Khong the lay "kiem_tay > 0" lam dau hieu: dem duoc con SO KHONG cung
	la mot ket qua dem, va do la ket qua hay gap nhat cuoi ngay. Nen giu
	rieng mot co `da_kiem`.
	"""
	return 1 if cint(r.get("da_kiem") if hasattr(r, "get") else getattr(r, "da_kiem", 0) or 0) else 0


def _tinh_lai(doc, ban=None):
	"""Do lai cot may cho ca phieu. Tra ve True neu co gi doi."""
	if ban is None:
		ban = da_ban(doc.diem, doc.ngay)
	doi = False
	co = {r.ma_hang for r in doc.dong}
	# Ban ra ma khong co dong -> them dong, khong duoc de mat so da ban.
	thieu = [m for m in ban if m not in co and la_banh(m)]
	if thieu:
		ten = _ten_hang(thieu)
		for m in sorted(thieu):
			doc.append("dong", {"ma_hang": m, "ten_banh": ten.get(m) or m})
			doi = True
	for r in doc.dong:
		db = cint(ban.get(r.ma_hang) or 0)
		ctb = tinh_co_the_ban(r.ton_dau, tong_nhap(r), db, r.hong, r.dieu_chinh)
		lc = tinh_lech(r.kiem_tay, _co_kiem(r), ctb)
		if cint(r.da_ban) != db or cint(r.co_the_ban) != ctb or cint(r.lech) != lc:
			r.da_ban, r.co_the_ban, r.lech = db, ctb, lc
			doi = True
	return doi


def _luu_may(doc, ban=None):
	"""Cap nhat cot may roi ghi xuong, chi ghi khi that su co doi."""
	if doc.tinh_trang == TT_CHOT:
		return doc
	if _tinh_lai(doc, ban):
		doc.save(ignore_permissions=True)
		frappe.db.commit()
	return doc


def _ra_dong(r):
	return {
		"ma_hang": r.ma_hang,
		"ten_banh": r.ten_banh or r.ma_hang,
		"ton_dau": cint(r.ton_dau),
		"nhap": [cint(r.get(k) or 0) for k in O_NHAP],
		"tong_nhap": tong_nhap(r),
		"da_ban": cint(r.da_ban),
		"hong": cint(r.hong),
		"dieu_chinh": cint(r.dieu_chinh),
		"co_the_ban": cint(r.co_the_ban),
		"kiem_tay": cint(r.kiem_tay),
		"da_kiem": _co_kiem(r),
		"theo_doi": 1 if dang_theo_doi(r) else 0,
		"lech": cint(r.lech),
		"ghi_chu": r.ghi_chu or "",
	}


@frappe.whitelist()
def diem_ds():
	"""Cac tab diem ban cho man hinh. Mo them chi nhanh la co tab moi."""
	return [
		{"ma": d["ma"], "ten": d["ten_ngan"] or d["ten"], "phu": d["phu"] or d["dia_chi"]}
		for d in _diem_co_quay()
	]


@frappe.whitelist()
def bang(diem, ngay=None):
	"""Bang kiem kho cua mot diem trong mot ngay, cot may da do lai."""
	ngay = getdate(ngay) if ngay else getdate()
	doc = _lay_hoac_tao(diem, ngay)
	doc = _luu_may(doc)
	return {
		"diem": doc.diem,
		"ngay": str(doc.ngay),
		"tinh_trang": doc.tinh_trang,
		"chot_luc": str(doc.chot_luc or ""),
		"sua_duoc": 1 if (_duoc_sua() and doc.tinh_trang != TT_CHOT) else 0,
		"so_dot": SO_DOT,
		"ghi_chu": doc.ghi_chu or "",
		"dong": [_ra_dong(r) for r in sorted(doc.dong, key=lambda x: str(x.ma_hang or ""))],
	}


@frappe.whitelist()
def luu_o(diem, ngay, ma_hang, truong, gia_tri):
	"""Sua mot o tren dien thoai."""
	_chan_neu_khong_duoc_sua()
	truong = str(truong or "").strip()
	if truong not in SUA_DUOC:
		frappe.throw("Cột này máy tự tính, không sửa tay được.")
	doc = _lay_hoac_tao(diem, ngay)
	if doc.tinh_trang == TT_CHOT:
		frappe.throw("Ngày này đã chốt sổ, không sửa nữa.")
	for r in doc.dong:
		if r.ma_hang != ma_hang:
			continue
		if truong == "ghi_chu":
			r.ghi_chu = str(gia_tri or "")[:500]
		elif truong == "kiem_tay":
			# Chuoi rong nghia la xoa lan dem, khong phai dem duoc khong.
			if str(gia_tri or "").strip() == "":
				r.kiem_tay, r.da_kiem = 0, 0
			else:
				r.kiem_tay, r.da_kiem = max(0, cint(gia_tri)), 1
		elif truong == "dieu_chinh":
			r.dieu_chinh = cint(gia_tri)  # cot nay duoc am, do la nghia cua no
		else:
			r.set(truong, max(0, cint(gia_tri)))
		# Co nguoi cham vao dong nay, tu day tro di no duoc theo doi that.
		r.theo_doi = 1
		_tinh_lai(doc)
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return _ra_dong([x for x in doc.dong if x.ma_hang == ma_hang][0])
	frappe.throw("Không thấy mã %s trong bảng." % ma_hang)


@frappe.whitelist()
def them_dong(diem, ngay, ma_hang):
	"""Them mot ma vao bang cua ngay dang xem."""
	_chan_neu_khong_duoc_sua()
	ma_hang = str(ma_hang or "").strip()
	if not ma_hang:
		frappe.throw("Thiếu mã hàng.")
	if not frappe.db.exists("Item", ma_hang):
		frappe.throw("Không có mã %s trong danh mục Hàng hoá." % ma_hang)
	doc = _lay_hoac_tao(diem, ngay)
	if doc.tinh_trang == TT_CHOT:
		frappe.throw("Ngày này đã chốt sổ, không thêm dòng nữa.")
	if any(r.ma_hang == ma_hang for r in doc.dong):
		frappe.throw("Mã này đã có trong bảng.")
	# Them tay la mot quyet dinh cua nguoi, nen dong nay theo doi ngay.
	doc.append("dong", {
		"ma_hang": ma_hang, "theo_doi": 1,
		"ten_banh": _ten_hang([ma_hang]).get(ma_hang) or ma_hang,
	})
	_tinh_lai(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1}


@frappe.whitelist()
def xoa_dong(diem, ngay, ma_hang):
	"""Go mot dong go nham - chi khi dong do trang tron."""
	_chan_neu_khong_duoc_sua()
	doc = _lay_hoac_tao(diem, ngay)
	if doc.tinh_trang == TT_CHOT:
		frappe.throw("Ngày này đã chốt sổ, không xoá dòng nữa.")
	for r in doc.dong:
		if r.ma_hang != ma_hang:
			continue
		if cint(r.ton_dau) or tong_nhap(r) or cint(r.da_ban) or cint(r.hong) or cint(r.dieu_chinh):
			frappe.throw("Mã %s đang có số, không xoá được. Xoá số về 0 trước đã." % ma_hang)
		doc.remove(r)
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"ok": 1}
	frappe.throw("Không thấy mã %s trong bảng." % ma_hang)


@frappe.whitelist()
def tim_mon(diem=None, tu_khoa="", ngay=None):
	"""Tim ma de them tay vao bang. Bo qua nhung ma da co trong bang."""
	tu = str(tu_khoa or "").strip()
	if len(tu) < 2:
		return []
	da_co = set()
	try:
		doc = _lay_hoac_tao(diem, ngay) if diem else None
		if doc:
			da_co = {r.ma_hang for r in doc.dong}
	except Exception:
		da_co = set()
	try:
		r = frappe.get_all(
			"Item",
			or_filters=[["name", "like", "%" + tu + "%"], ["item_name", "like", "%" + tu + "%"]],
			filters={"disabled": 0},
			fields=["name", "item_name"], limit_page_length=30, ignore_permissions=True,
		)
	except Exception:
		return []
	return [
		{"ma_hang": d["name"], "ten_banh": d.get("item_name") or d["name"]}
		for d in r if d["name"] not in da_co
	]


@frappe.whitelist()
def chot(diem, ngay=None):
	"""Chot so cuoi ngay. So con lai chay sang ton dau ngay mai."""
	_chan_neu_khong_duoc_sua()
	ngay = getdate(ngay) if ngay else getdate()
	doc = _lay_hoac_tao(diem, ngay)
	if doc.tinh_trang == TT_CHOT:
		frappe.throw("Ngày %s đã chốt rồi." % ngay)
	_tinh_lai(doc)
	doc.tinh_trang = TT_CHOT
	doc.chot_luc = now_datetime()
	doc.chot_boi = frappe.session.user
	doc.save(ignore_permissions=True)

	mai = getdate(add_days(ngay, 1))
	ma_mai = ten_phieu(doc.diem, mai)
	sau = frappe.get_doc(DT, ma_mai) if frappe.db.exists(DT, ma_mai) else None
	if sau is not None and sau.tinh_trang == TT_CHOT:
		frappe.throw(
			"Ngày %s đã chốt sổ rồi nên không nhận tồn đầu từ ngày %s được. "
			"Anh chị mở lại ngày %s trước." % (mai, ngay, mai)
		)
	if sau is None:
		sau = frappe.new_doc(DT)
		sau.diem, sau.ngay, sau.tinh_trang = doc.diem, mai, TT_BAN
	cu = {r.ma_hang: r for r in sau.dong}
	for r in doc.dong:
		ton = con_lai_ngay_mai(r.kiem_tay, _co_kiem(r), r.co_the_ban)
		if r.ma_hang in cu:
			cu[r.ma_hang].ton_dau = ton
		elif ton or la_banh(r.ma_hang):
			sau.append("dong", {
				"ma_hang": r.ma_hang, "ten_banh": r.ten_banh, "ton_dau": ton,
				"theo_doi": 1 if dang_theo_doi(r) else 0,
			})
	_tinh_lai(sau)
	if sau.get("__islocal") or not sau.name:
		sau.insert(ignore_permissions=True)
	else:
		sau.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ngay_mai": str(mai)}


@frappe.whitelist()
def con_lai(diem, ngay=None):
	"""{ma_hang: so con} cho man tinh tien - nhe, goi lien tuc duoc.

	Khong dung doc day du va khong ghi gi xuong: man tinh tien goi cai nay
	moi lan thu ngan mo o tim mon, ghi xuong o day la ghi vai chuc lan mot
	phut cho mot con so chi de nhin.
	"""
	d = _kiem_diem(diem)
	ngay = getdate(ngay) if ngay else getdate()
	ma = ten_phieu(d["ma"], ngay)
	if not frappe.db.exists(DT, ma):
		return {}
	try:
		dong = frappe.get_all(
			DT_DONG, filters={"parent": ma, "parenttype": DT},
			fields=["ma_hang", "theo_doi", "ton_dau", "hong", "dieu_chinh"] + list(O_NHAP),
			limit_page_length=0, ignore_permissions=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "kiem_kho: con lai loi")
		return {}
	ban = da_ban(d["ma"], ngay)
	ra = {}
	for r in dong:
		# Dong chua ai khai thi KHONG bao so ra man tinh tien. Xem
		# `dang_theo_doi`.
		if not dang_theo_doi(r):
			continue
		ra[r["ma_hang"]] = tinh_co_the_ban(
			r["ton_dau"], tong_nhap(r), ban.get(r["ma_hang"]) or 0, r["hong"], r["dieu_chinh"]
		)
	return ra
