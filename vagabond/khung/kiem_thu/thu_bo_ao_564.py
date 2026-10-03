# -*- coding: utf-8 -*-
"""v564: bỏ ảo một mã hàng (anh Việt chốt 03/10/2026, việc số 2).

Phép THUẦN của bo_ao.py; giao diện chạy thật ở hanh_vi/bo_ao_564.js.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
from vagabond import bo_ao as B  # noqa: E402


@ca("v564: dòng cha của mã bỏ ảo thì chặn nổ, bỏ công thức con, bỏ cờ phantom; chạy lại không đổi gì")
def _dong_cha():
	la("dong phantom", B.viec_dong_cha(0, "BOM-BTP-001", 1), {"do_not_explode": 1, "bom_no": "", "is_phantom_item": 0})
	la("dong da dung", B.viec_dong_cha(1, "", 0), {})
	la("chi thieu chan no", B.viec_dong_cha(0, "", 0), {"do_not_explode": 1})
	la("bom_no chi co khoang trang coi nhu rong", B.viec_dong_cha(1, "  ", 0), {})


@ca("v564: mã theo lô hay số máy thì dừng, báo làm tay; mã lạ thì báo không tìm thấy")
def _chan():
	dung("theo lo", "làm tay" in B.cau_chan("M1", 1, 0, False))
	dung("theo so may", "theo số máy" in B.cau_chan("M1", 0, 1, False))
	dung("khong co ma", "Không tìm thấy" in B.cau_chan("M1", 0, 0, True))
	la("binh thuong thi duoc", B.cau_chan("M1", 0, 0, False), "")


@ca("v564: danh sách giữ tồn đọc an toàn, thêm không trùng")
def _giu_ton():
	la("rong", B.doc_giu_ton(None), [])
	la("rac", B.doc_giu_ton("{khong phai json"), [])
	la("khong phai danh sach", B.doc_giu_ton('{"a":1}'), [])
	la("doc va sap xep", B.doc_giu_ton('["B2","A1","A1",""]'), ["A1", "B2"])
	la("them khong trung", B.them_giu_ton(["A1"], "A1"), ["A1"])
	la("them moi", B.them_giu_ton(["A1"], "B2"), ["A1", "B2"])


@ca("v564: câu tổng kết nói rõ vượt chặn ERPNext, mã đã có tồn thì không làm gì")
def _tong_ket():
	dung("da co ton", "không cần" in B.tong_ket("M1", 1, 0, 0, 0, False))
	c = B.tong_ket("M1", 0, 1, 3, 4, True)
	dung("so lieu", "3 dòng" in c and "dựng lại 4" in c)
	dung("noi vuot chan", "vượt chặn" in c)
	dung("khong vuot chan thi khong noi", "vượt chặn" not in B.tong_ket("M1", 0, 1, 3, 4, False))


@ca("v564: chuyển Phantom và patch phantom chừa mã đã bỏ ảo, không biến về ảo")
def _chua_giu_ton():
	import io
	import os

	goc = os.path.dirname(os.path.abspath(B.__file__))
	ph = io.open(os.path.join(goc, "phantom.py"), encoding="utf-8").read()
	pa = io.open(os.path.join(goc, "patches", "no_phantom_chuan.py"), encoding="utf-8").read()
	# Do chuoi chi chot loi chua: hai ham do chay tren site that (can bang BOM).
	dung("phantom bo ma giu ton khoi BTP", "- giu)" in ph and "chang_cua_ma[ma] = CHANG_C1" in ph)
	dung("patch chuyen ma bo qua giu ton", "or b.item in giu:" in pa)
	dung("patch gan co coi giu ton la giu ton", "| set(danh_sach_giu_ton())" in pa)


@ca("v564 Codex #427 F1: mã không tồn kho mà không thuộc luồng phantom thì dừng, không bật tồn kho")
def _khong_phai_ao():
	dung("ma dich vu bi chan", "không phải mã ảo" in B.cau_khong_phai_ao("PHI-VC", 0, 0, 0))
	la("co cong thuc ao thi duoc", B.cau_khong_phai_ao("M1", 0, 1, 0), "")
	la("co dong cha ao thi duoc", B.cau_khong_phai_ao("M1", 0, 0, 2), "")
	la("da la hang ton thi khong chan o day", B.cau_khong_phai_ao("M1", 1, 0, 0), "")


def _frappe_gia_chay(hong_o=None, dong_cha=None):
	"""Dựng một site giả đủ cho bo_ao.chay: mã PHI-VC hoặc mã ảo BTP1 có cha CHA1."""
	import frappe

	nhat_ky = []

	class Dict(dict):
		__getattr__ = dict.get

	class Db(object):
		def get_value(self, dt, ten, truong=None, as_dict=False):
			if dt == "Item":
				return Dict(name=ten, item_name=ten, is_stock_item=0, has_batch_no=0, has_serial_no=0)
			return 1

		def exists(self, *a, **k):
			return True

		def get_default(self, k):
			return "[]"

		def set_default(self, k, v):
			nhat_ky.append(("set_default", k))

		def set_value(self, dt, ten, *a, **k):
			nhat_ky.append(("set_value", dt, ten))

		def commit(self):
			nhat_ky.append(("commit",))

		def rollback(self):
			nhat_ky.append(("rollback",))

	def get_all(dt, filters=None, **k):
		f = filters or {}
		if dt == "BOM" and f.get("is_phantom_bom"):
			return [] if f.get("item") == "PHI-VC" else [Dict(name="BOM-BTP1")]
		if dt == "BOM":
			return [Dict(name="BOM-BTP1"), Dict(name="CHA1"), Dict(name="ONG1")]
		if dt == "BOM Item" and f.get("item_code"):
			if f["item_code"] == "PHI-VC":
				return []
			return dong_cha if dong_cha is not None else [Dict(name="r1", parent="CHA1", do_not_explode=0,
				bom_no="BOM-BTP1", is_phantom_item=1)]
		if dt == "BOM Item":
			trong = set((f.get("parent") or ["in", []])[1])
			return [x for x in [Dict(parent="ONG1", bom_no="CHA1")] if x.parent in trong]
		return []

	class Bom(object):
		def __init__(self, ten):
			self.ten = ten

		def update_exploded_items(self, save=True):
			if self.ten == hong_o:
				raise Exception("thieu gia nguyen lieu")
			nhat_ky.append(("dung_lai", self.ten))

		def add_comment(self, *a):
			nhat_ky.append(("comment",))

	cu = {}
	moi = {"db": Db(), "get_all": get_all, "get_doc": lambda dt, ten: Bom(ten),
		"log_error": lambda *a, **k: None, "clear_cache": lambda *a, **k: None,
		"clear_document_cache": lambda *a, **k: None, "get_traceback": lambda: ""}
	for k, v in moi.items():
		cu[k] = getattr(frappe, k, None)
		setattr(frappe, k, v)

	def tra():
		for k, v in cu.items():
			setattr(frappe, k, v)
	return nhat_ky, tra


@ca("v564 Codex #427 F1: chạy thật trên mã dịch vụ PHI-VC thì dừng, không ghi dòng nào")
def _chay_ma_dich_vu():
	import frappe

	nk, tra = _frappe_gia_chay()
	try:
		loi = ""
		try:
			B.chay("PHI-VC", "thu", 1)
		except frappe.ValidationError as e:
			loi = str(e)
		dung("bi chan", "không phải mã ảo" in loi)
		la("khong ghi gi", [x for x in nk if x[0] in ("set_value", "set_default", "commit")], [])
	finally:
		tra()


@ca("v564 Codex #427 F2: dựng lại một công thức hỏng thì quay lui hết, không commit, báo lỗi")
def _chay_hong_quay_lui():
	import frappe

	nk, tra = _frappe_gia_chay(hong_o="ONG1")
	try:
		loi = ""
		try:
			B.chay("BTP1", "lam san cat tu", 1)
		except frappe.ValidationError as e:
			loi = str(e)
		dung("bao loi co ten cong thuc hong", "ONG1" in loi and "quay lui" in loi)
		dung("co rollback", ("rollback",) in nk)
		dung("khong commit", ("commit",) not in nk)
		dung("rollback sau khi ghi ma hang", nk.index(("rollback",)) > nk.index(("set_value", "Item", "BTP1")))
	finally:
		tra()
	nk, tra = _frappe_gia_chay()
	try:
		kq = B.chay("BTP1", "lam san cat tu", 1)
		dung("dung lai con truoc cha sau", nk.index(("dung_lai", "CHA1")) < nk.index(("dung_lai", "ONG1")))
		dung("thanh cong thi commit, khong rollback", ("commit",) in nk and ("rollback",) not in nk)
		la("ten da dung lai", sorted(kq["da_dung_lai"]), ["CHA1", "ONG1"])
	finally:
		tra()


@ca("v564 Codex #427 F2: câu báo hỏng gọn, quá 5 công thức thì nói còn bao nhiêu")
def _cau_hong():
	ds = [{"bom": "B%d" % i, "vi_sao": "x"} for i in range(7)]
	c = B.cau_hong("M1", ds)
	dung("noi so", "7 công thức hỏng" in c and "và 2 công thức nữa" in c and "B5" not in c)
	da, hong = B.dung_lai_lan_luot(["A", "B", "C"], lambda t: 1 / 0 if t == "B" else None)
	la("gom dung", (da, [x["bom"] for x in hong]), (["A", "C"], ["B"]))
