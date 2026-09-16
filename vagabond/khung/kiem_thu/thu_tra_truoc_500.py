# -*- coding: utf-8 -*-
"""#500: phiếu trả trước vào bước kế bằng NÚT của workflow, không gán tay.

Ca thật 16/09/2026. Bản v408 (03/09 19:00) đặt thẳng
`pe.workflow_state = "Chờ FIN kiểm tra"` ngay trước `insert`. Frappe soi
đường duyệt lúc lưu, chứng từ MỚI thì không nhận bước chuyển nào, nên ném:

    "Không được phép chuyển trạng thái quy trình từ Nháp sang Chờ FIN kiểm tra"

`tao_phieu` ném lỗi thì cả giao dịch lùi: mất phiếu, mất tệp vừa đính. Đo
trên site thật: phiếu cuối cùng lập được qua màn này là APP-26-09-050 lúc
03/09 17:38, tức một tiếng rưỡi TRƯỚC bản v408. Từ đó tới 16/09 không lập
được phiếu nào.

Các ca dưới đây GỌI THẬT hàm chứ không dò chuỗi (điều 16). Riêng ca cuối
dùng phép dò chuỗi, và chỉ dùng cho đúng một việc không chạy được ở tầng
khung: chốt "không còn chỗ nào tự gán workflow_state lên phiếu mới nữa".
"""
import json
import io
import os
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import tra_truoc as tt
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MA_NGUON = io.open(os.path.join(GOC, "tra_truoc.py"), encoding="utf-8").read()


class Phieu(object):
	"""Phiếu giả, đủ để đo: nó nhớ trạng thái lúc lưu và lúc đẩy bước."""

	def __init__(self, buoc=None):
		self.name = "APP-26-09-999"
		self.flags = NS()
		self.workflow_state = buoc
		self.paid_from = "TK1"
		self.paid_to = "TK2"
		self.nhat_ky = []
		self.da_luu = buoc

	def get(self, k, *a):
		return getattr(self, k, a[0] if a else None)

	def insert(self, **k):
		# Ghi lai trang thai DUNG LUC LUU. Day la con so bat loi cu.
		self.nhat_ky.append(("insert", self.workflow_state))

	def as_json(self):
		return json.dumps({"doctype": "Payment Entry", "name": self.name})

	def reload(self):
		self.workflow_state = self.da_luu


def db_gia():
	db = NS(savepoint=lambda *a: None, rollback=lambda **k: None)
	for k in ("before_commit", "after_commit", "before_rollback", "after_rollback"):
		setattr(db, k, NS(_functions=[]))
	return db


@ca("#500: đẩy bước bằng đúng nút Gửi kiểm tra, không gán tay trạng thái")
def _day_dung_nut():
	pe = Phieu(tt.TT_NHAP)
	goi = []

	def gia_lap(doc, nut):
		goi.append(nut)
		la("payload là JSON của phiếu", json.loads(doc)["name"], pe.name)
		pe.da_luu = tt.TT_CHO_FIN

	with patch.object(tt, "_co_o_workflow", lambda: True), \
			patch.object(tt.frappe, "db", db_gia(), create=True), \
			patch.dict("sys.modules", {"frappe.model.workflow": NS(apply_workflow=gia_lap)}):
		buoc, loi = tt._gui_kiem_tra(pe)
	la("bấm đúng một nút", goi, [tt.NUT_GUI])
	la("phiếu vào bước kế", buoc, tt.TT_CHO_FIN)
	la("không có câu nhắc thừa", loi, "")


@ca("#500: đẩy bước hỏng thì GIỮ phiếu ở Nháp, không ném lỗi ra ngoài")
def _day_hong_van_giu_phieu():
	pe = Phieu(tt.TT_NHAP)

	def no(doc, nut):
		pe.workflow_state = tt.TT_CHO_FIN
		raise Exception("Validation lỗi sau khi đổi object")

	with patch.object(tt, "_co_o_workflow", lambda: True), \
			patch.object(tt.frappe, "db", db_gia(), create=True), \
			patch.object(tt.frappe, "log_error", lambda *a, **k: None, create=True), \
			patch.dict("sys.modules", {"frappe.model.workflow": NS(apply_workflow=no)}):
		buoc, loi = tt._gui_kiem_tra(pe)
	la("phiếu vẫn ở Nháp", buoc, tt.TT_NHAP)
	dung("có nhắc tên phiếu", pe.name in loi)
	dung("có chỉ đường bấm Gửi kiểm tra", "Gửi kiểm tra" in loi)
	dung("dặn đừng lập lại phiếu mới", "đừng lập lại" in loi)


@ca("#500: hệ chưa có workflow thì không gọi apply_workflow, giữ nguyên bước")
def _khong_co_workflow():
	pe = Phieu(tt.TT_NHAP)

	def no(doc, nut):
		raise AssertionError("không được gọi khi hệ chưa có workflow")

	with patch.object(tt, "_co_o_workflow", lambda: False), \
			patch.dict("sys.modules", {"frappe.model.workflow": NS(apply_workflow=no)}):
		buoc, loi = tt._gui_kiem_tra(pe)
	la("giữ nguyên bước", buoc, tt.TT_NHAP)
	la("không có câu nhắc", loi, "")


@ca("#500: tao_phieu LƯU phiếu ở Nháp rồi mới đẩy bước, đúng thứ tự đó")
def _thu_tu_luu_roi_moi_day():
	"""Lưu trước, đẩy sau. Đảo thứ tự là quay lại đúng lỗi cũ."""
	pe = Phieu(tt.TT_NHAP)
	thu_tu = []

	def day(doc):
		thu_tu.append("day")
		doc.workflow_state = tt.TT_CHO_FIN
		return tt.TT_CHO_FIN, ""

	don = NS(name="DMH-2026-00396", supplier="NCC", grand_total=1620000,
		docstatus=1, get=lambda k, *a: {"status": "To Receive and Bill",
			"advance_paid": 0, "per_billed": 0, "supplier_name": "NCC"}.get(k, a[0] if a else None))
	bo = [
		patch.object(tt, "_chan", lambda: None),
		patch.object(tt, "_dung_phieu", lambda *a: pe),
		patch.object(tt, "_ghi_chu", lambda *a: None),
		patch.object(tt, "_gan_tep", lambda *a: thu_tu.append("gan_tep")),
		patch.object(tt, "_gui_kiem_tra", day),
		patch.object(tt, "_bao_ke_toan", lambda *a: thu_tu.append(a[-1])),
		patch.object(tt.frappe, "db", NS(exists=lambda *a: True,
			get_value=lambda *a, **k: "1121 - TV"), create=True),
		patch.object(tt.frappe, "get_doc", lambda *a: don, create=True),
		patch.object(tt.frappe, "parse_json", lambda s: [], create=True),
	]
	for b in bo:
		b.start()
	try:
		pe.insert = lambda **k: (thu_tu.append("insert"),
			pe.nhat_ky.append(("insert", pe.workflow_state)))
		ra = tt.tao_phieu(don="DMH-2026-00396", so_tien=1620000,
			nguon_tien="MB", loai_chung_tu="Bảng báo giá",
			tep=[{"ma": "FILE-1"}])
	finally:
		for b in bo:
			b.stop()
	la("lưu phiếu trước rồi mới đẩy bước", thu_tu[:2], ["insert", "gan_tep"])
	dung("đẩy bước sau khi đã lưu", thu_tu.index("day") > thu_tu.index("insert"))
	la("lúc LƯU phiếu còn ở Nháp", pe.nhat_ky[0][1], tt.TT_NHAP)
	la("kết quả trả về đúng bước", ra["trang_thai"], tt.TT_CHO_FIN)
	la("có cờ đã gửi", ra["da_gui"], 1)
	la("giao đúng FIN", thu_tu[-1], tt.VAI_FIN)
	dung("câu báo nói đang chờ kế toán", "chờ kế toán kiểm tra" in ra["nhan"])


@ca("#500: đẩy không được thì câu báo NÓI THẬT, không bảo là đã gửi")
def _cau_bao_noi_that():
	pe = Phieu(tt.TT_NHAP)
	bao = []
	don = NS(name="DMH-2026-00396", supplier="NCC", grand_total=1620000,
		docstatus=1, get=lambda k, *a: {"status": "To Receive and Bill",
			"advance_paid": 0, "per_billed": 0, "supplier_name": "NCC"}.get(k, a[0] if a else None))
	bo = [
		patch.object(tt, "_chan", lambda: None),
		patch.object(tt, "_dung_phieu", lambda *a: pe),
		patch.object(tt, "_ghi_chu", lambda *a: None),
		patch.object(tt, "_gan_tep", lambda *a: None),
		patch.object(tt, "_gui_kiem_tra", lambda doc: (tt.TT_NHAP, "Phiếu %s đang ở Nháp." % doc.name)),
		patch.object(tt, "_bao_ke_toan", lambda *a: bao.append(a[-1])),
		patch.object(tt.frappe, "db", NS(exists=lambda *a: True,
			get_value=lambda *a, **k: "1121 - TV"), create=True),
		patch.object(tt.frappe, "get_doc", lambda *a: don, create=True),
		patch.object(tt.frappe, "parse_json", lambda s: [], create=True),
	]
	for b in bo:
		b.start()
	try:
		ra = tt.tao_phieu(don="DMH-2026-00396", so_tien=1620000,
			nguon_tien="MB", loai_chung_tu="Bảng báo giá",
			tep=[{"ma": "FILE-1"}])
	finally:
		for b in bo:
			b.stop()
	la("trả về đúng bước thật", ra["trang_thai"], tt.TT_NHAP)
	la("cờ đã gửi phải là 0", ra["da_gui"], 0)
	la("nháp giao AP Officer", bao, ["AP Officer"])
	dung("KHÔNG nói đã chờ kế toán", "chờ kế toán kiểm tra" not in ra["nhan"])


@ca("#500: không còn chỗ nào tự gán workflow_state lên phiếu mới")
def _khong_con_gan_tay():
	"""Phép dò chuỗi, dùng đúng một lần cho thứ không chạy được ở tầng khung.

	`_dung_phieu` gọi `get_payment_entry` của ERPNext, mà máy chạy kiểm thử
	tầng khung không có erpnext. Không dựng lại được nên chốt bằng mã nguồn.
	"""
	# Chi dem dong LENH GAN that, khong dem cau van trong chu thich: doan
	# giai thich cua `_gui_kiem_tra` co nhac lai nguyen van cach lam cu.
	gan = [d for d in MA_NGUON.splitlines()
		if d.strip().startswith(("pe.workflow_state =", "pe.workflow_state="))]
	la("không còn dòng lệnh gán thẳng trạng thái", gan, [])
	dung("có gọi apply_workflow", "apply_workflow(pe.as_json(), NUT_GUI)" in MA_NGUON)
	# Tên nút phải khớp Workflow Transition thật của "Duyệt phiếu chi APP".
	la("tên nút đúng từng dấu", tt.NUT_GUI, "Gửi kiểm tra")
	la("tên bước đúng từng dấu", tt.TT_CHO_FIN, "Chờ FIN kiểm tra")
