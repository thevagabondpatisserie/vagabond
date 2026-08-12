# -*- coding: utf-8 -*-
"""Nhap khach hang le tu Fabi CRM (anh Viet 12/08/2026).

Fabi xuat ra 56.960 dong. Anh Viet chot chi lay nguoi CO PHAT SINH, tuc
41.516 nguoi sau khi bo cac dong khong doc duoc so dien thoai.

Ba cai bay da tim thay khi doc file, va cach bit:

  1. Cot "Sinh nhat" gan nhu toan rac. 49.963 dong co ghi ma chi 7.733 dong
     co nam sinh trong khoang 1920 den 2015; phan con lai la NGAY DANG KY bi
     Fabi ghi nham (17.956 dong nam 2025, 8.249 dong nam "0021"). Nhap thang
     la he chuc mung sinh nhat sai cho hon 40.000 nguoi. Chi nhan dong co
     nam sinh hop ly, con lai de trong.

  2. Truong mobile_no cua Customer la READ ONLY, ERPNext keo tu Contact
     chinh sang. Ghi thang vao do thi lan sau ai mo khach ra bam Luu la no
     bi xoa trang - dung cai da lam 1.545 khach doanh nghiep dang co tren
     he khong ai co so dien thoai. Phai tao Contact that roi tro lam lien
     he chinh.

  3. Cung mot nguoi co the dang nam san tren he. Khoa chong trung la SO
     DIEN THOAI da chuan hoa, khong phai ten: ten khach la truong go tay,
     co khoang trang thua va viet hoa lan lon.

Chay nen theo lo. Tien do cat o Vagabond Settings de mo lai man hinh van
doc duoc, va chay lai thi bo qua nguoi da nhap chu khong tao ban trung.
"""

import csv
import io
import json
import re

import frappe
from frappe.utils import cint, flt, getdate

from vagabond.lib import cfg, sdt

TRUONG_TIEN_DO = "vgb_nhap_khach_tien_do"
NHOM_MAC_DINH = "Khách lẻ"
KHU_VUC = "Vietnam"
LO = 200

# Cot bat buoc trong tep da lam sach. Thieu mot cot la dung ngay, khong
# nhap nua chung roi moi phat hien thieu du lieu.
COT = [
	"sdt", "ten", "sinh_nhat", "gioi_tinh", "email",
	"dia_chi", "thanh_pho", "zalo", "tags",
	"lan_cuoi", "lan_dau", "ngay_dang_ky", "kenh_dang_ky", "nha_hang",
	"da_tieu", "so_lan", "ngay_chua_ve",
]

QUYEN = {"System Manager", "Accounts Manager", "Sales Manager"}


def _kiem_quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới được nhập danh sách khách hàng.")


# Chuan hoa so dien thoai nay o vagabond/lib.py, dung chung ca he. Giu ten
# cu o day de nhung cho da goi khong phai sua.
sdt_chuan = sdt


def _ngay(s):
	s = str(s or "").strip()
	if not s:
		return None
	try:
		return getdate(s)
	except Exception:
		return None


def _hang_theo_tien(bang, tien):
	"""Hang cao nhat ma so tien nay voi toi."""
	dat = ""
	for h in sorted(bang, key=lambda x: flt(x.get("chi_tieu_tu"))):
		if flt(tien) >= flt(h.get("chi_tieu_tu")):
			dat = h["name"]
	return dat


def _bang_hang():
	return frappe.get_all(
		"Vagabond Hang Khach",
		filters={"bat": 1, "loai": "Theo chi tieu"},
		fields=["name", "chi_tieu_tu"],
	)


def _da_co_theo_sdt():
	"""Bang tra so dien thoai -> ma khach, dung cho ca lan chay lai.

	Doc mot lan roi giu trong bo nho: hoi tung dong mot la 41.516 luot truy
	van, cham gap nhieu lan ma khong duoc gi them.
	"""
	ra = {}
	rows = frappe.db.sql(
		"""
		select dl.link_name ma, c.mobile_no, c.phone
		from `tabContact` c
		join `tabDynamic Link` dl on dl.parent = c.name
		where dl.link_doctype = 'Customer' and dl.parenttype = 'Contact'
		""",
		as_dict=True,
	)
	for r in rows:
		for s in (r.get("mobile_no"), r.get("phone")):
			k = sdt_chuan(s)
			if k and k not in ra:
				ra[k] = r["ma"]
	for r in frappe.db.sql(
		"select name, mobile_no from `tabCustomer` where ifnull(mobile_no,'') != ''",
		as_dict=True,
	):
		k = sdt_chuan(r.get("mobile_no"))
		if k and k not in ra:
			ra[k] = r["name"]
	return ra


def _tach_ten(ten):
	"""Ho va ten cho Contact. Fabi cho mot o duy nhat nen tach o khoang cuoi."""
	t = re.sub(r"\s+", " ", str(ten or "").strip())
	if not t:
		return "Khách", ""
	phan = t.split(" ")
	if len(phan) == 1:
		return phan[0], ""
	return " ".join(phan[:-1]), phan[-1]


def _truong_fabi(d):
	"""Cac truong mang tu Fabi sang, dung chung cho ca tao moi lan bu them.

	Tach ra mot cho vi hai duong deu can: tao moi thi ghi het, con khach da
	co thi chi bu vao o dang trong. Hai ban sao la mot ngay nao do sua mot
	ben quen ben kia, roi cung mot khach nhap hai lan ra hai ket qua.
	"""
	return {
		"vgb_chi_tieu_cu": flt(d.get("da_tieu")),
		"vgb_so_don_cu": cint(d.get("so_lan")),
		"vgb_lan_cuoi_cu": _ngay(d.get("lan_cuoi")),
		"vgb_lan_dau_cu": _ngay(d.get("lan_dau")),
		"vgb_ngay_dang_ky": _ngay(d.get("ngay_dang_ky")),
		"vgb_kenh_dang_ky": str(d.get("kenh_dang_ky") or "").strip()[:140],
		"vgb_cua_hang_cu": str(d.get("nha_hang") or "").strip()[:140],
		"vgb_zalo_id": str(d.get("zalo") or "").strip()[:140],
		"vgb_tags": str(d.get("tags") or "").strip()[:500],
		"vgb_sinh_nhat": _ngay(d.get("sinh_nhat")),
		"vgb_dia_chi_cu": (d.get("dia_chi") or "")[:500],
	}


def _tao_mot(d, bang_hang):
	"""Tao mot khach le kem lien he. Tra ma khach."""
	ten = re.sub(r"\s+", " ", str(d.get("ten") or "").strip())
	# KHONG dat ten bien la "sdt": trung ten voi ham chuan hoa da import o
	# dau tep, che mat no trong ca than ham.
	so = d["sdt"]
	if not ten:
		ten = "Khách %s" % so[-4:]
	tieu = flt(d.get("da_tieu"))

	kh = frappe.new_doc("Customer")
	kh.update(
		{
			"customer_name": ten[:140],
			"customer_type": "Individual",
			"customer_group": NHOM_MAC_DINH,
			"territory": KHU_VUC,
			"vgb_hang": _hang_theo_tien(bang_hang, tieu) or None,
		}
	)
	kh.update({k: v for k, v in _truong_fabi(d).items() if v not in (None, "", 0)})
	gt = (d.get("gioi_tinh") or "").strip()
	if gt in ("Male", "Female"):
		kh.gender = gt
	kh.flags.ignore_permissions = True
	kh.insert(ignore_permissions=True)

	ho, dem = _tach_ten(ten)
	lh = frappe.new_doc("Contact")
	lh.update({"first_name": ho[:140], "last_name": dem[:140], "mobile_no": so, "is_primary_contact": 1})
	em = (d.get("email") or "").strip()
	if em and "@" in em:
		lh.append("email_ids", {"email_id": em[:140], "is_primary": 1})
	lh.append("phone_nos", {"phone": so, "is_primary_mobile_no": 1})
	lh.append("links", {"link_doctype": "Customer", "link_name": kh.name})
	lh.flags.ignore_permissions = True
	lh.insert(ignore_permissions=True)

	# Tro lam lien he chinh thi ERPNext moi keo so dien thoai sang Customer.
	# Ghi thang vao mobile_no ma khong lam buoc nay thi lan sau ai mo khach
	# ra bam Luu la so bien mat.
	frappe.db.set_value(
		"Customer",
		kh.name,
		{"customer_primary_contact": lh.name, "mobile_no": so},
		update_modified=False,
	)
	return kh.name


def _cap_nhat_mot(ma, d, bang_hang):
	"""Khach da co san: chi BU vao o dang trong, khong de len cai dang dung.

	Chay lai lan hai lan ba deu an toan, va ai da sua tay tren app thi lan
	nhap sau khong xoa mat cong cua ho.
	"""
	moi = _truong_fabi(d)
	cu = frappe.db.get_value("Customer", ma, list(moi.keys()) + ["vgb_hang"], as_dict=True) or {}
	dat = {}
	for k, v in moi.items():
		if v in (None, "", 0):
			continue
		hien = cu.get(k)
		if hien in (None, "", 0) or (isinstance(hien, str) and not hien.strip()):
			dat[k] = v
	if not cu.get("vgb_hang"):
		h = _hang_theo_tien(bang_hang, flt(dat.get("vgb_chi_tieu_cu") or cu.get("vgb_chi_tieu_cu")))
		if h:
			dat["vgb_hang"] = h
	if dat:
		frappe.db.set_value("Customer", ma, dat, update_modified=False)
	return bool(dat)


# ------------------------------------------------------------------ tien do


def _doc_tien_do():
	try:
		t = json.loads((cfg().get(TRUONG_TIEN_DO) or "").strip() or "{}")
		return t if isinstance(t, dict) else {}
	except Exception:
		return {}


def _ghi_tien_do(t):
	frappe.db.set_single_value(
		"Vagabond Settings", TRUONG_TIEN_DO, json.dumps(t, ensure_ascii=False)
	)
	frappe.db.commit()


@frappe.whitelist()
def tien_do():
	_kiem_quyen()
	return _doc_tien_do()


# ------------------------------------------------------------------- chay


def _doc_tep(file_url):
	doc = frappe.get_doc("File", {"file_url": file_url})
	noi_dung = doc.get_content()
	if isinstance(noi_dung, bytes):
		noi_dung = noi_dung.decode("utf-8-sig")
	rows = list(csv.DictReader(io.StringIO(noi_dung)))
	if not rows:
		frappe.throw("Tệp không có dòng nào.")
	thieu = [c for c in COT if c not in rows[0]]
	if thieu:
		frappe.throw("Tệp thiếu cột: %s" % ", ".join(thieu))
	return rows


def chay(file_url, tu=0, gioi_han=0):
	"""Chay nen. tu: dong bat dau, de chay tiep sau khi dut giua chung."""
	rows = _doc_tep(file_url)
	bang_hang = _bang_hang()
	da_co = _da_co_theo_sdt()
	t = {
		"tep": file_url,
		"tong": len(rows),
		"vi_tri": cint(tu),
		"tao": 0,
		"cap_nhat": 0,
		"bo_qua": 0,
		"loi": [],
		"xong": 0,
		"bat_dau": str(frappe.utils.now()),
	}
	cu = _doc_tien_do()
	if cu.get("tep") == file_url and cint(tu):
		for k in ("tao", "cap_nhat", "bo_qua"):
			t[k] = cint(cu.get(k))
	_ghi_tien_do(t)

	het = len(rows) if not cint(gioi_han) else min(len(rows), cint(tu) + cint(gioi_han))
	i = cint(tu)
	while i < het:
		d = rows[i]
		i += 1
		try:
			s = sdt_chuan(d.get("sdt"))
			if not s:
				t["bo_qua"] += 1
				continue
			d = dict(d)
			d["sdt"] = s
			ma = da_co.get(s)
			if ma:
				if _cap_nhat_mot(ma, d, bang_hang):
					t["cap_nhat"] += 1
				else:
					t["bo_qua"] += 1
			else:
				da_co[s] = _tao_mot(d, bang_hang)
				t["tao"] += 1
		except Exception:
			frappe.db.rollback()
			if len(t["loi"]) < 50:
				t["loi"].append("dòng %d (%s): %s" % (i, d.get("sdt"), frappe.get_traceback().splitlines()[-1][:180]))
			else:
				t["bo_qua"] += 1
		if i % LO == 0:
			frappe.db.commit()
			t["vi_tri"] = i
			_ghi_tien_do(t)
	frappe.db.commit()
	t["vi_tri"] = i
	t["xong"] = 1 if i >= len(rows) else 0
	t["ket_thuc"] = str(frappe.utils.now())
	_ghi_tien_do(t)
	return t


@frappe.whitelist()
def bat_dau(file_url=None, tu=0, gioi_han=0, chay_ngay=0):
	"""Man Cai dat bam nut Nhap. chay_ngay: chay thang, dung de thu mot lo nho."""
	_kiem_quyen()
	file_url = (file_url or "").strip()
	if not file_url:
		frappe.throw("Chưa chọn tệp khách hàng.")
	if not frappe.db.exists("File", {"file_url": file_url}):
		frappe.throw("Không tìm thấy tệp %s trên hệ thống." % file_url)
	_doc_tep(file_url)
	if cint(chay_ngay):
		return chay(file_url, tu=tu, gioi_han=gioi_han)
	frappe.enqueue(
		"vagabond.nhap_khach.chay",
		queue="long",
		timeout=18000,
		file_url=file_url,
		tu=cint(tu),
		gioi_han=cint(gioi_han),
	)
	return {"da_xep_hang": 1, "tep": file_url}


# ------------------------------------------------- tra khach theo so dien thoai
#
# Dung cho don Pancake dong bo ve (anh Viet 12/08/2026): truoc day moi don
# online deu do vao gio chung "Khach le Online", ten va so dien thoai that
# chi nam trong o ghi chu. Khach mua ca nam khong tich duoc diem nao, con
# nhan vien thi phai go tay lai neu muon gan dung nguoi.
#
# Nay co danh sach 41.423 khach that roi thi tra thang theo so dien thoai.


def tim_theo_sdt(sdt):
	"""Ma khach mang so dien thoai nay. Khong co thi tra rong.

	Tra cuu bang MOT cau truy van chu khong dung bang tra dung san: ham nay
	goi cho tung don mot trong chuoi dong bo 15 phut, dung bang tra la moi
	lan chay lai phai doc ca 41.000 lien he.
	"""
	s = sdt_chuan(sdt)
	if not s:
		return ""
	# So co the dang nam duoi dang 0xxxxxxxxx hoac 84xxxxxxxxx, ca hai deu
	# tung duoc nhap vao he. So sanh ca hai cho chac.
	dang = [s, "84" + s[1:], "+84" + s[1:]]
	rows = frappe.db.sql(
		"""
		select dl.link_name ma
		from `tabContact` c
		join `tabDynamic Link` dl on dl.parent = c.name
		where dl.link_doctype = 'Customer' and dl.parenttype = 'Contact'
		  and (c.mobile_no in %(dang)s or c.phone in %(dang)s)
		limit 1
		""",
		{"dang": tuple(dang)},
		as_dict=True,
	)
	if rows:
		return rows[0]["ma"]
	rows = frappe.db.sql(
		"select name from `tabCustomer` where mobile_no in %(dang)s limit 1",
		{"dang": tuple(dang)},
		as_dict=True,
	)
	return rows[0]["name"] if rows else ""


def tao_khach_le(sdt, ten="", nguon=""):
	"""Tao mot khach le moi tu so dien thoai. Tra ma khach, hoac rong."""
	s = sdt_chuan(sdt)
	if not s:
		return ""
	d = {
		"sdt": s,
		"ten": re.sub(r"\s+", " ", str(ten or "").strip()),
		"da_tieu": 0,
		"lan_cuoi": "",
		"sinh_nhat": "",
		"gioi_tinh": "",
		"email": "",
		"dia_chi": "",
	}
	ma = _tao_mot(d, _bang_hang())
	if ma and nguon:
		try:
			frappe.db.set_value("Customer", ma, "vgb_ma_cu", str(nguon)[:140], update_modified=False)
		except Exception:
			pass
	return ma


def khach_cho_don(sdt, ten="", nguon=""):
	"""Tim khach theo so dien thoai, chua co thi tao moi. Tra ma khach.

	Loi thi tra RONG chu khong nem: mot don online khong gan duoc khach van
	phai vao doanh thu, khong duoc chan ca chuoi dong bo vi mot so dien
	thoai la lung.
	"""
	try:
		s = sdt_chuan(sdt)
		if not s:
			return ""
		ma = tim_theo_sdt(s)
		if ma:
			return ma
		return tao_khach_le(s, ten, nguon)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "nhap_khach: gan khach cho don")
		return ""


# ------------------------------------------------- ra soat so dien thoai da co
#
# Anh Viet 12/08/2026: "so dien thoai nhieu khi bi +84, 84 o dau, em viet code
# de thong nhat dong bo ve ERP thi se bien thanh so 0 o dau het nhe".
#
# Chuan hoa o duong VAO da lam roi (vagabond/lib.py). Ham nay lo phan da nam
# san trong co so du lieu: quet Contact va Customer, dua moi so ve dang
# 0xxxxxxxxx. Chay lai bao nhieu lan cung duoc, so da dung thi khong dung toi.


@frappe.whitelist()
def ra_soat_sdt(sua=0):
	"""Xem (hoac sua) cac so dien thoai chua ve dang 0xxxxxxxxx.

	sua=0 chi xem truoc, sua=1 moi ghi that. Luon xem truoc mot lan roi hay
	sua: doi so dien thoai cua 41.000 nguoi la viec khong lui lai duoc.
	"""
	_kiem_quyen()
	sua = cint(sua)
	doi, hong = [], []

	rows = frappe.db.sql(
		"""
		select name, mobile_no, phone
		from `tabContact`
		where ifnull(mobile_no, '') != '' or ifnull(phone, '') != ''
		""",
		as_dict=True,
	)
	for r in rows:
		dat = {}
		for truong in ("mobile_no", "phone"):
			cu = (r.get(truong) or "").strip()
			if not cu:
				continue
			moi = sdt(cu)
			if not moi:
				hong.append({"bang": "Contact", "ten": r["name"], "truong": truong, "gia_tri": cu})
				continue
			if moi != cu:
				dat[truong] = moi
		if dat:
			doi.append({"bang": "Contact", "ten": r["name"], "dat": dat})
			if sua:
				frappe.db.set_value("Contact", r["name"], dat, update_modified=False)

	rows = frappe.db.sql(
		"select name, mobile_no from `tabCustomer` where ifnull(mobile_no, '') != ''",
		as_dict=True,
	)
	for r in rows:
		cu = (r.get("mobile_no") or "").strip()
		moi = sdt(cu)
		if not moi:
			hong.append({"bang": "Customer", "ten": r["name"], "truong": "mobile_no", "gia_tri": cu})
			continue
		if moi != cu:
			doi.append({"bang": "Customer", "ten": r["name"], "dat": {"mobile_no": moi}})
			if sua:
				frappe.db.set_value("Customer", r["name"], "mobile_no", moi, update_modified=False)

	# Bang con Contact Phone: ERPNext keo mobile_no cua Contact tu day len,
	# nen sua o tren ma bo qua bang nay thi lan sau ai mo lien he ra bam Luu
	# la so cu quay lai.
	rows = frappe.db.sql(
		"select name, parent, phone from `tabContact Phone` where ifnull(phone, '') != ''",
		as_dict=True,
	)
	for r in rows:
		cu = (r.get("phone") or "").strip()
		moi = sdt(cu)
		if not moi:
			hong.append({"bang": "Contact Phone", "ten": r["parent"], "truong": "phone", "gia_tri": cu})
			continue
		if moi != cu:
			doi.append({"bang": "Contact Phone", "ten": r["parent"], "dat": {"phone": moi}})
			if sua:
				frappe.db.set_value("Contact Phone", r["name"], "phone", moi, update_modified=False)

	if sua:
		frappe.db.commit()
	return {
		"da_sua": 1 if sua else 0,
		"so_phai_doi": len(doi),
		"so_khong_doc_duoc": len(hong),
		"doi": doi[:200],
		"hong": hong[:200],
	}


# --------------------------------------------- gan lai khach cho hoa don cu
#
# Anh Viet 12/08/2026: "em cong bu lai nhe".
#
# Hoa don Pancake tao truoc 12/08 deu mang gio chung "Khach le Online", ten
# va so dien thoai that chi nam trong o ghi chu remarks dang
#   "Pancake #91476 - Nguyen Van A - 0901557462"
# Ham nay doc so do ra, tim hoac tao khach, gan lai vao hoa don, roi cong bu
# diem theo hang cua khach.
#
# BA DIEU PHAI GIU:
#   1. Chi dung voi hoa don dang mang GIO CHUNG. Hoa don sales da gan dung
#      nguoi thi khong dung toi.
#   2. Doi customer tren hoa don DA GUI khong duoc di qua ORM (Frappe chan),
#      ma di thang xuong bang. Truong customer khong vao so cai - so lieu ke
#      toan khong doi mot dong, chi doi hoa don do thuoc ve ai.
#   3. Cong diem qua dung mot cua khach_hang._ghi_so_diem, va co khoa chong
#      cong hai lan (_da_tich). Chay lai bao nhieu lan cung ra mot ket qua.

def _sdt_tu_remarks(s):
	"""So dien thoai nam cuoi chuoi ghi chu cua hoa don Pancake.

	Ghi chu co dang "Pancake #91476 - Nguyen Van A - 0901557462", nhung so
	co the co khoang trang o giua ("+84 901 557 462") va ten khach cung co
	the co dau gach ngang. Nen thu tu chac den long:
	  1. Phan sau dau gach ngang CUOI CUNG, ghep ca cum.
	  2. Ca chuoi, phong khi khong co dau gach nao.
	  3. Tung manh mot, tu phai qua trai.
	"""
	t = str(s or "").strip()
	if not t:
		return ""
	if " - " in t:
		x = sdt(t.rsplit(" - ", 1)[1])
		if x:
			return x
	# Ca chuoi chi ra so khi trong chuoi khong con chu so nao khac, nen chi
	# dung duoc khi ghi chu ngan. Van thu, re tien.
	x = sdt(t)
	if x:
		return x
	for manh in reversed(re.split(r"[\s\-]+", t)):
		x = sdt(manh)
		if x:
			return x
	return ""


@frappe.whitelist()
def gan_lai_khach_cu(tu_ngay=None, gioi_han=0, cong_diem=1, chay_thu=1):
	"""Gan lai khach cho cac hoa don Pancake dang mang gio chung.

	chay_thu=1 chi dem va liet ke, khong ghi gi. Luon chay thu mot lan roi
	moi chay that: day la viec dong den diem cua khach, tuc la tien.
	"""
	from vagabond.ban_hang import KHACH_LE
	from vagabond.khach_hang import _da_tich, _ghi_so_diem, _hang_cua

	_kiem_quyen()
	chay_thu = cint(chay_thu)
	cong_diem = cint(cong_diem)
	gioi_han = cint(gioi_han)

	dk = {"customer": KHACH_LE, "docstatus": 1, "vgb_huy": 0, "custom_pancake_id": ["is", "set"]}
	if tu_ngay:
		dk["posting_date"] = [">=", str(tu_ngay)]
	ds = frappe.get_all(
		"Sales Invoice",
		filters=dk,
		fields=["name", "posting_date", "grand_total", "remarks", "custom_pancake_display_id"],
		order_by="posting_date asc, name asc",
		limit_page_length=gioi_han or 0,
	)

	kq = {
		"chay_thu": chay_thu,
		"tim_thay": len(ds),
		"gan_duoc": 0,
		"tao_khach_moi": 0,
		"khong_ra_so": 0,
		"diem_cong": 0,
		"so_don_cong_diem": 0,
		"vi_du": [],
		"loi": [],
	}
	bang_hang = _bang_hang()

	for r in ds:
		try:
			so = _sdt_tu_remarks(r.get("remarks"))
			if not so:
				kq["khong_ra_so"] += 1
				continue
			ma = tim_theo_sdt(so)
			moi = 0
			if not ma:
				if chay_thu:
					kq["tao_khach_moi"] += 1
					kq["gan_duoc"] += 1
					if len(kq["vi_du"]) < 20:
						kq["vi_du"].append({"don": r["name"], "sdt": so, "khach": "(sẽ tạo mới)"})
					continue
				ten = ""
				m = re.match(r"^Pancake #\S+\s*-\s*(.*?)(?:\s*-\s*[\d+][\d\s.]*)?$", str(r.get("remarks") or ""))
				if m:
					ten = m.group(1).strip()
				ma = _tao_mot({"sdt": so, "ten": ten, "da_tieu": 0}, bang_hang)
				moi = 1
			if moi:
				kq["tao_khach_moi"] += 1
			kq["gan_duoc"] += 1
			if len(kq["vi_du"]) < 20:
				kq["vi_du"].append({"don": r["name"], "sdt": so, "khach": ma})

			if chay_thu:
				continue

			# Hoa don da gui: doi thang duoi bang. Truong customer khong vao
			# so cai nen so lieu ke toan khong doi mot dong.
			frappe.db.set_value("Sales Invoice", r["name"], "customer", ma, update_modified=False)

			if cong_diem and not _da_tich(r["name"]):
				hang = _hang_cua(ma)
				ty_le = flt((hang or {}).get("tich_diem"))
				diem = round(flt(r.get("grand_total")) * ty_le / 100.0) if ty_le > 0 else 0
				if diem > 0:
					_ghi_so_diem(
						ma, diem, "Tich tu hoa don", r["name"],
						"Cộng bù khi gắn lại khách cho hoá đơn cũ. Hạng %s, tích %s%% của %s đ"
						% ((hang or {}).get("name"), ty_le, r.get("grand_total")),
					)
					kq["diem_cong"] += diem
					kq["so_don_cong_diem"] += 1
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			if len(kq["loi"]) < 30:
				kq["loi"].append("%s: %s" % (r["name"], frappe.get_traceback().splitlines()[-1][:150]))
	if not chay_thu:
		frappe.db.commit()
	return kq
