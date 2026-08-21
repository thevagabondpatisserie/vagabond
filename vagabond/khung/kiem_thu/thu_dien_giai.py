"""Ca kiem cho o Dien giai cua phieu tien.

Su co that 21/08/2026: anh Viet in Chung tu thanh toan APP-26-08-534 thi o
Dien giai ra nguyen cau tieng Anh cua ERPNext, trong khi ma nguon cua minh
ro rang co ghi cau tieng Viet day du.

Nguyen nhan doc duoc trong ma nguon ERPNext version-16,
erpnext/accounts/doctype/payment_entry/payment_entry.py:

    def set_remarks(self):
        if self.custom_remarks:
            return
        ...
        self.set("remarks", "\\n".join(remarks))

Ham nay nam trong validate(). Nghia la MOI LAN luu phieu, ERPNext DUNG LAI
o Dien giai va ghi de len cau cua minh, tru khi co `custom_remarks`.

Vi sao phai bat co chu khong ghi lai sau khi luu: phieu tien cua tiem con
duoc luu lai nhieu lan nua sau do - duyet workflow ba cap, dinh kem uy nhiem
chi, sua so tien. Ghi lai sau insert thi chi dung duoc lan dau; bat co thi
dung mai.

Loi nay an vao CA NAM luong sinh Payment Entry, nen phai co ca kiem doc
thang ma nguon de tu nay khong ai gan thang pe.remarks nua.
"""

import ast
import os

from vagabond import chung_tu_tien
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Nam luong sinh Payment Entry, dung ten tep de sau nay con doi chieu.
LUONG_TIEN = (
	"tra_truoc.py",      # tra truoc nha cung cap theo don mua
	"ho_so_tt.py",       # thanh toan cong no NCC va hoan ung
	"hoan_tien.py",      # hoan tien khach
	"don_huy.py",        # hoan tien don Pancake da huy
	"chung_tu_tien.py",  # noi giu ham dung chung
)


class _Meta:
	def __init__(self, co=True):
		self.co = co

	def has_field(self, ten):
		return self.co


class _Phieu(dict):
	"""Ban gia lap toi thieu cua mot Document Frappe."""

	def __init__(self, co_o_co=True):
		super().__init__()
		self.meta = _Meta(co_o_co)

	def __getattr__(self, ten):
		return self.get(ten)

	def __setattr__(self, ten, gia_tri):
		if ten == "meta":
			super().__setattr__(ten, gia_tri)
		else:
			self[ten] = gia_tri


@ca("dien giai: ghi cau cua minh VA bat co chong ERPNext ghi de")
def _dat():
	pe = _Phieu()
	chung_tu_tien.dat_dien_giai(pe, "Trả trước cho đơn mua DMH-2026-00174-1")
	la("cau duoc ghi", pe.get("remarks"), "Trả trước cho đơn mua DMH-2026-00174-1")
	la("co chong ghi de da bat", pe.get("custom_remarks"), 1)


@ca("dien giai: cau rong thi khong dung gi, khong bat co bua")
def _rong():
	pe = _Phieu()
	pe["remarks"] = "cau cu"
	chung_tu_tien.dat_dien_giai(pe, "   ")
	la("giu nguyen cau cu", pe.get("remarks"), "cau cu")
	dung("khong bat co", not pe.get("custom_remarks"))


@ca("dien giai: gop nhieu dong trang thanh mot khoang, cat theo do dai")
def _gon():
	pe = _Phieu()
	chung_tu_tien.dat_dien_giai(pe, "  dòng một\n\n  dòng hai\t\tdòng ba  ")
	la("gop khoang trang", pe.get("remarks"), "dòng một dòng hai dòng ba")
	pe2 = _Phieu()
	chung_tu_tien.dat_dien_giai(pe2, "x" * 5000)
	la("cat dung do dai", len(pe2.get("remarks")), chung_tu_tien.DAI_DIEN_GIAI)


@ca("dien giai: noi them van giu co, khong lam mat cau cu")
def _noi_them():
	pe = _Phieu()
	pe["remarks"] = "Amount VNĐ 3600000.0 paid to ABC"
	chung_tu_tien.them_dien_giai(pe, "Trả trước cho đơn mua DMH-2026-00174-1.")
	dung("con cau cu", "3600000.0" in pe.get("remarks"))
	dung("co cau moi", "DMH-2026-00174-1" in pe.get("remarks"))
	la("co chong ghi de da bat", pe.get("custom_remarks"), 1)


@ca("dien giai: ban ERPNext khong co o custom_remarks thi van khong no")
def _khong_co_o():
	pe = _Phieu(co_o_co=False)
	chung_tu_tien.dat_dien_giai(pe, "vẫn ghi được câu này")
	la("cau van duoc ghi", pe.get("remarks"), "vẫn ghi được câu này")
	dung("khong bat co bua", not pe.get("custom_remarks"))


@ca("dien giai: chan hoi quy - KHONG luong nao duoc gan thang pe.remarks")
def _khong_gan_thang():
	# Ca nay doc thang ma nguon. Ham thuan o tren van xanh ke ca khi ai do
	# quay lai gan thang pe.remarks o mot luong, luc do chi ca nay bat duoc.
	pham = []
	for ten_tep in LUONG_TIEN:
		duong = os.path.join(GOC, ten_tep)
		with open(duong, encoding="utf-8") as f:
			cay = ast.parse(f.read())
		for nut in ast.walk(cay):
			if not isinstance(nut, ast.Assign):
				continue
			for dich in nut.targets:
				if not isinstance(dich, ast.Attribute) or dich.attr != "remarks":
					continue
				# Chi soi bien ten `pe`, tuc Payment Entry. Purchase Invoice
				# va Stock Entry khong co net set_remarks nay.
				if isinstance(dich.value, ast.Name) and dich.value.id == "pe":
					# Rieng chung_tu_tien la noi giu ham dung chung, duoc phep.
					if ten_tep != "chung_tu_tien.py":
						pham.append("%s dòng %d" % (ten_tep, nut.lineno))
	la("khong con cho nao gan thang pe.remarks", pham, [])


@ca("dien giai: ca nam luong deu goi qua chung_tu_tien")
def _du_nam_luong():
	thieu = []
	for ten_tep in LUONG_TIEN:
		if ten_tep == "chung_tu_tien.py":
			continue
		with open(os.path.join(GOC, ten_tep), encoding="utf-8") as f:
			s = f.read()
		if "dat_dien_giai" not in s and "them_dien_giai" not in s:
			thieu.append(ten_tep)
	la("khong luong nao bo sot", thieu, [])
