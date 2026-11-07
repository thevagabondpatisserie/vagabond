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
