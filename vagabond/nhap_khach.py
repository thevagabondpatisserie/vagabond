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

from vagabond.lib import cfg

TRUONG_TIEN_DO = "vgb_nhap_khach_tien_do"
NHOM_MAC_DINH = "Khách lẻ"
KHU_VUC = "Vietnam"
LO = 200

# Cot bat buoc trong tep da lam sach. Thieu mot cot la dung ngay, khong
# nhap nua chung roi moi phat hien thieu du lieu.
COT = [
	"sdt", "ten", "sinh_nhat", "gioi_tinh", "email",
	"dia_chi", "thanh_pho", "zalo", "tags", "lan_cuoi", "da_tieu", "so_lan",
]

QUYEN = {"System Manager", "Accounts Manager", "Sales Manager"}


def _kiem_quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới được nhập danh sách khách hàng.")


# Dau so di dong Viet Nam that su dang phat hanh, hai chu so sau so 0.
#
# Phai liet ke tung dau so chu khong chi kiem "bat dau bang 3 5 7 8 9":
# trong tep Fabi co so 0300136435, dau so 030 khong ton tai o Viet Nam
# (day la ma so thue bi go nham vao o so dien thoai). Kiem lo tay thi tao
# ra mot khach ma ca doi khong nhan duoc tin nhan nao.
DAU_SO = frozenset(
	"32 33 34 35 36 37 38 39 52 55 56 58 59 70 76 77 78 79 "
	"81 82 83 84 85 86 87 88 89 90 91 92 93 94 96 97 98 99".split()
)


def sdt_chuan(s):
	"""So di dong Viet Nam ve dang 0xxxxxxxxx. Khong doc duoc thi tra rong.

	Tra rong chu KHONG doan bua: mot so sai mot chu so la ca doi khach do
	khong nhan duoc tin nhan nao, ma khong ai biet vi sao.
	"""
	x = "".join(ch for ch in str(s or "") if ch.isdigit())
	# Chi cat ma quoc gia khi phan con lai du dai. "84xxxxxxxxx" la so co
	# ma vung, con "0084..." hay so bat dau bang 84 nhung ngan thi khong.
	if x.startswith("84") and len(x) > 10:
		x = x[2:]
	x = x.lstrip("0")
	if len(x) == 9 and x[:2] in DAU_SO:
		return "0" + x
	return ""


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


def _tao_mot(d, bang_hang):
	"""Tao mot khach le kem lien he. Tra ma khach."""
	ten = re.sub(r"\s+", " ", str(d.get("ten") or "").strip())
	sdt = d["sdt"]
	if not ten:
		ten = "Khách %s" % sdt[-4:]
	tieu = flt(d.get("da_tieu"))

	kh = frappe.new_doc("Customer")
	kh.update(
		{
			"customer_name": ten[:140],
			"customer_type": "Individual",
			"customer_group": NHOM_MAC_DINH,
			"territory": KHU_VUC,
			"vgb_chi_tieu_cu": tieu,
			"vgb_lan_cuoi_cu": _ngay(d.get("lan_cuoi")),
			"vgb_sinh_nhat": _ngay(d.get("sinh_nhat")),
			"vgb_dia_chi_cu": (d.get("dia_chi") or "")[:500],
			"vgb_hang": _hang_theo_tien(bang_hang, tieu) or None,
		}
	)
	gt = (d.get("gioi_tinh") or "").strip()
	if gt in ("Male", "Female"):
		kh.gender = gt
	kh.flags.ignore_permissions = True
	kh.insert(ignore_permissions=True)

	ho, dem = _tach_ten(ten)
	lh = frappe.new_doc("Contact")
	lh.update({"first_name": ho[:140], "last_name": dem[:140], "mobile_no": sdt, "is_primary_contact": 1})
	em = (d.get("email") or "").strip()
	if em and "@" in em:
		lh.append("email_ids", {"email_id": em[:140], "is_primary": 1})
	lh.append("phone_nos", {"phone": sdt, "is_primary_mobile_no": 1})
	lh.append("links", {"link_doctype": "Customer", "link_name": kh.name})
	lh.flags.ignore_permissions = True
	lh.insert(ignore_permissions=True)

	# Tro lam lien he chinh thi ERPNext moi keo so dien thoai sang Customer.
	# Ghi thang vao mobile_no ma khong lam buoc nay thi lan sau ai mo khach
	# ra bam Luu la so bien mat.
	frappe.db.set_value(
		"Customer",
		kh.name,
		{"customer_primary_contact": lh.name, "mobile_no": sdt},
		update_modified=False,
	)
	return kh.name


def _cap_nhat_mot(ma, d, bang_hang):
	"""Khach da co san: chi bu them cai dang thieu, khong de len cai dang dung."""
	cu = frappe.db.get_value(
		"Customer", ma,
		["vgb_chi_tieu_cu", "vgb_sinh_nhat", "vgb_hang", "vgb_dia_chi_cu"],
		as_dict=True,
	) or {}
	dat = {}
	tieu = flt(d.get("da_tieu"))
	if tieu and not flt(cu.get("vgb_chi_tieu_cu")):
		dat["vgb_chi_tieu_cu"] = tieu
	sn = _ngay(d.get("sinh_nhat"))
	if sn and not cu.get("vgb_sinh_nhat"):
		dat["vgb_sinh_nhat"] = sn
	dc = (d.get("dia_chi") or "").strip()
	if dc and not (cu.get("vgb_dia_chi_cu") or "").strip():
		dat["vgb_dia_chi_cu"] = dc[:500]
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
