"""Kiem thu BO KHUNG cua tung thu muc doctype trong repo (v290).

Vi sao co tep nay
-----------------
Ngay 23/08/2026 deploy v289 hong ngay o buoc migrate:

    ModuleNotFoundError: No module named
    'vagabond.vagabond.doctype.vagabond_nhan_banh_dong.vagabond_nhan_banh_dong'
    ImportError: Module import failed for Vagabond Nhan Banh Dong

Nguyen nhan: hai bang CON cua doctype moi chi co tep .json ma thieu tep .py
cung ten. Frappe bat buoc MOI doctype phai co mot mo dun Python cung ten, ke
ca bang con (istable), vi `doctype.on_update` goi `run_module_method` de tim
`on_doctype_update`. Thieu tep do thi migrate nga giua chung.

Cai gia phai tra: site bi khoa trong 38 giay roi Frappe Cloud tu khoi phuc
ve ban cu. Khong mat du lieu, nhung ca dot deploy phai lam lai.

Vi sao cong tam cong doan KHONG bat duoc: cong do chay phep thuan, khong
dung Frappe that va khong mo phong migrate. Ca kiem duoi day la hang rao thay
the: no doc thang thu muc doctype tren dia, khong can Frappe, khong can site.
"""

import io
import json
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
THU_MUC = os.path.join(GOI, "vagabond", "doctype")


def _cac_doctype():
	"""Danh sach (ten thu muc, duong dan) cua moi doctype trong repo."""
	if not os.path.isdir(THU_MUC):
		return []
	ra = []
	for ten in sorted(os.listdir(THU_MUC)):
		d = os.path.join(THU_MUC, ten)
		if not os.path.isdir(d) or ten.startswith("_") or ten.startswith("."):
			continue
		if not os.path.exists(os.path.join(d, "%s.json" % ten)):
			continue
		ra.append((ten, d))
	return ra


@ca("mọi thư mục doctype đều có đủ ba tệp bộ khung, kể cả bảng con")
def _():
	# Bay da sap that ngay 23/08/2026: bang con chi co .json, migrate nga voi
	# ModuleNotFoundError. Frappe doi MOI doctype co mo dun Python cung ten.
	thieu = []
	for ten, d in _cac_doctype():
		for tep in ("__init__.py", "%s.py" % ten):
			if not os.path.exists(os.path.join(d, tep)):
				thieu.append("%s thiếu %s" % (ten, tep))
	la("không doctype nào thiếu tệp bộ khung", thieu, [])


@ca("tệp .py của mỗi doctype khai đúng lớp Document theo tên chuẩn của Frappe")
def _():
	# Frappe suy ten lop bang cach BO DAU CACH va dau gach ngang, GIU NGUYEN
	# hoa thuong (frappe/model/base_document.py::get_controller). Nen
	# "Vagabond CTKM" -> "VagabondCTKM" chu KHONG phai "VagabondCtkm".
	#
	# Ban dau tep nay dung .title() va bao hong 11 doctype von dang chay tot,
	# trong do co VagabondCTKM va VagabondOTP. Mot ca kiem bao hong cai dang
	# dung con te hon khong co ca kiem, vi lan sau khong ai tin no nua.
	hong = []
	for ten, d in _cac_doctype():
		p = os.path.join(d, "%s.py" % ten)
		if not os.path.exists(p):
			continue
		src = io.open(p, encoding="utf-8").read()
		try:
			ten_dt = json.load(io.open(os.path.join(d, "%s.json" % ten), encoding="utf-8")).get("name") or ""
		except Exception:
			hong.append("%s: không đọc được tệp json" % ten)
			continue
		mong = ten_dt.replace(" ", "").replace("-", "")
		if not mong:
			continue
		if not re.search(r"class\s+%s\s*\(" % re.escape(mong), src):
			hong.append("%s: mong lớp %s" % (ten, mong))
	la("không doctype nào khai sai tên lớp", hong, [])


@ca("tên thư mục doctype khớp với tên doctype khai trong tệp json")
def _():
	# Frappe dung ten thu muc de dung duong dan import. Lech mot ky tu la
	# migrate nga y het ca tren, chi khac dong bao loi.
	hong = []
	for ten, d in _cac_doctype():
		try:
			ten_dt = json.load(io.open(os.path.join(d, "%s.json" % ten), encoding="utf-8")).get("name") or ""
		except Exception:
			continue
		mong = re.sub(r"[^a-z0-9]+", "_", ten_dt.lower()).strip("_")
		if mong and mong != ten:
			hong.append("thư mục %s nhưng doctype tên %r" % (ten, ten_dt))
	la("không thư mục nào lệch tên", hong, [])


@ca("bộ kiểm đọc được ít nhất vài chục doctype, không phải quét trượt thư mục")
def _():
	# Neu duong dan sai thi ba ca tren deu XANH ma khong soi gi ca. Ca nay
	# chot rang bo kiem that su nhin thay cac doctype.
	dung("tìm thấy thư mục doctype", os.path.isdir(THU_MUC))
	dung("đọc được trên 20 doctype", len(_cac_doctype()) > 20)
