"""v643 (còn tồn v604): nhịp đồng bộ kiểm bánh đụng người ghi khác (Frappe ném
TimestampMismatchError) thì lùi và làm lại một lần, không ghi Error Log.

Trên site 31/10 tới 06/11/2026: 15 dòng Error Log "Vagabond: dong bo kiem banh
loi", tất cả là "KB-<ngày> has been modified after you have opened it", hai
lần ghi cách nhau dưới một giây."""
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la


class TimestampMismatchError(Exception):
	pass


@ca("v643 đồng bộ kiểm bánh: bị người ghi khác chen thì lùi, làm lại một lần; lỗi khác vẫn ném; lần hai vẫn đụng thì trả bảng, không ghi Error Log")
def _dung():
	import frappe
	from vagabond import kiem_banh as kb

	lan, lui, log = [], [], []

	def mot(seq):
		def f(ngay=None):
			lan.append(ngay)
			x = seq.pop(0)
			if isinstance(x, Exception):
				raise x
			return x
		return f

	with patch.object(frappe.db, "rollback", lambda *a, **k: lui.append(1), create=True), \
			patch.object(frappe, "log_error", lambda *a, **k: log.append(k.get("title") or (a[0] if a else "")), create=True), \
			patch.object(kb, "bang", lambda ngay=None: {"bang": "hien_co"}):
		with patch.object(kb, "_dong_bo_mot_lan", mot([TimestampMismatchError("KB-2026-11-06 modified"), {"bang": "moi"}])):
			la("đụng lần đầu: làm lại, ra bảng mới", kb.dong_bo("2026-11-06"), {"bang": "moi"})
		la("chạy hai lần, lùi một lần", (len(lan), len(lui)), (2, 1))
		lan.clear(); lui.clear()
		with patch.object(kb, "_dong_bo_mot_lan", mot([TimestampMismatchError("a"), TimestampMismatchError("b")])):
			la("đụng hai lần: trả bảng hiện có", kb.dong_bo("2026-11-06"), {"bang": "hien_co"})
		la("không thử lần ba", len(lan), 2)
		lan.clear(); lui.clear()
		with patch.object(kb, "_dong_bo_mot_lan", mot([TimestampMismatchError("a"), TimestampMismatchError("b")])):
			kb.dong_bo_tu_dong()
		la("nhịp tự động không ghi Error Log khi chỉ bị chen", log, [])
		with patch.object(kb, "_dong_bo_mot_lan", mot([ValueError("hỏng thật")])):
			kb.dong_bo_tu_dong()
		la("lỗi thật vẫn ghi Error Log", log, ["Vagabond: dong bo kiem banh loi"])
		lan.clear(); lui.clear()
		with patch.object(kb, "_dong_bo_mot_lan", mot([ValueError("hỏng thật")])):
			try:
				kb.dong_bo("2026-11-06")
				dung("lỗi thật phải ném", False)
			except ValueError:
				pass
		la("lỗi thật không lùi, không làm lại", (len(lan), len(lui)), (1, 0))


@ca("Codex #546 vòng 4: chốt ngày mà hai lần đồng bộ đều bị chen thì DỪNG, không chuyển tồn sang mai trên số cũ; một lần chen thì chốt bình thường")
def _chot():
	import frappe
	from types import SimpleNamespace as NS
	from vagabond import kiem_banh as kb

	viec = []

	class Dung(Exception):
		pass

	def lay_mai(ngay):
		viec.append("mai")
		raise Dung()

	def chay(seq):
		viec.clear()
		doc = NS(tinh_trang="Dang mo", reload=lambda: viec.append("reload"), dong=[])

		def mot(ngay=None):
			x = seq.pop(0)
			viec.append("dong_bo")
			if isinstance(x, Exception):
				raise x
			return x
		with patch.object(frappe, "get_doc", lambda *a, **k: doc, create=True), \
				patch.object(frappe.db, "rollback", lambda *a, **k: viec.append("lui"), create=True), \
				patch.object(kb, "bang", lambda ngay=None: {"bang": "cu"}), \
				patch.object(kb, "_dong_bo_mot_lan", mot), patch.object(kb, "_lay_hoac_tao", lay_mai):
			try:
				kb.chot_ngay("2026-11-06")
				return "chốt xong"
			except Dung:
				return "đi tiếp tới bước chuyển tồn"
			except frappe.ValidationError as e:
				return "dừng: " + str(e)
	ra = chay([TimestampMismatchError("a"), TimestampMismatchError("b")])
	dung("hai lần bị chen: dừng, báo chốt lại (%s)" % ra, ra.startswith("dừng:") and "bấm Chốt lại" in ra)
	la("không đọc lại bảng, không chuyển tồn", [x for x in viec if x in ("reload", "mai")], [])
	ra = chay([TimestampMismatchError("a"), {"bang": "moi"}])
	la("một lần bị chen: làm lại được thì chốt tiếp", (ra, viec), ("đi tiếp tới bước chuyển tồn", ["dong_bo", "lui", "dong_bo", "reload", "mai"]))
	la("THUẦN: lớp lỗi riêng là lỗi kiểm dữ liệu (ValidationError)", issubclass(kb.DongBoBiChen, frappe.ValidationError), True)
