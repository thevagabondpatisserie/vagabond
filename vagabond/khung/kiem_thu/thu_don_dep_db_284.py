# -*- coding: utf-8 -*-
"""Kiểm thử #284: nhịp dọn bảng nhật ký không được xoá nhầm và không được im.

Hai cái bẫy của việc này, và vì sao mỗi cái có ca riêng.

BẪY MỘT: ROW_COUNT() ĐỌC SAU COMMIT THÌ LUÔN LÀ 0.
Trong MariaDB, COMMIT cũng là một câu lệnh, nên sau nó ROW_COUNT() nói về
chính COMMIT chứ không về câu DELETE trước đó. Viết nhầm thứ tự thì vòng lặp
thấy "xoá được 0 dòng", dừng ngay ở lô đầu, và nhịp đêm chạy đều mỗi đêm mà
không dọn gì cả. Không một lỗi nào được ghi, không một cảnh báo nào nổi lên,
đúng kiểu hỏng mà nhìn vào đâu cũng thấy đang chạy (bài học 26/08/2026).

Nên bản giả lập database dưới đây CỐ Ý dựng lại đúng hành vi đó: `commit()`
xoá dấu vết của câu trước. Một bản giả lập dễ tính hơn, kiểu luôn trả về số
dòng vừa xoá bất kể gọi lúc nào, sẽ xanh cả khi code sai, và đó lại là bẫy
"ca kiểm tự che mất lỗi" đã ghi trong docs/bai-hoc-su-co.md.

BẪY HAI: XOÁ KHÔNG CÓ LIMIT.
Bảng tabVersion đang có hàng trăm nghìn dòng. Một câu DELETE không LIMIT sẽ
khoá bảng nhiều phút, và nếu rơi vào giờ bán hàng thì quầy không tính tiền
được. Ca kiểm chốt cả hai vế: câu lệnh phải mang LIMIT, và số dòng xoá trong
một lần chạy không bao giờ vượt trần.

GHI CHÚ CHO NGƯỜI SỬA SAU: đừng gọi thêm hàm nào "cho chắc" trước khi đo.
Chuỗi thao tác ở đây đúng bằng chuỗi mà scheduler chạy, không hơn.
"""

from unittest.mock import patch

from vagabond import don_dep_db as dd
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem


class DbGia:
	"""Bản giả lập database, cố ý bắt chước MariaDB ở đúng chỗ hay sai."""

	def __init__(self, con_lai=0, hong=False):
		self.con_lai = int(con_lai)
		self.hong = hong
		self.lenh = []
		self._vua_xoa = 0

	def sql(self, cau, tham=None, **k):
		if self.hong:
			raise RuntimeError("Access denied for OPTIMIZE")
		c = " ".join(str(cau).split())
		self.lenh.append(c)
		thap = c.lower()
		if thap.startswith("delete"):
			# Không có LIMIT thì câu lệnh chỉ có một tham số, và ở đây ta
			# dựng lại đúng hậu quả thật: xoá sạch một phát.
			xin = int(tham[1]) if tham and len(tham) > 1 else self.con_lai
			self._vua_xoa = min(xin, self.con_lai)
			self.con_lai -= self._vua_xoa
			return []
		if thap.startswith("select row_count()"):
			return [[self._vua_xoa]]
		return []

	def commit(self):
		self.lenh.append("commit")
		# Đây là dòng quan trọng nhất của tệp này. Xem BẪY MỘT ở đầu tệp.
		self._vua_xoa = 0


def _chay(con_lai, **k):
	db = DbGia(con_lai)
	with patch.object(dd.frappe, "db", db):
		so = dd.don_mot_bang("Version", **k)
	return so, db


@ca("#284 số ngày giữ đúng như anh Việt chốt 12/09/2026")
def _so_ngay():
	la("Version", dd.BANG_DON["Version"], 180)
	la("Notification Log", dd.BANG_DON["Notification Log"], 30)
	la("Deleted Document", dd.BANG_DON["Deleted Document"], 180)
	la("đúng ba bảng", sorted(dd.BANG_DON), ["Deleted Document", "Notification Log", "Version"])


@ca("#284 chặn cứng: không doctype nghiệp vụ nào lọt vào diện dọn")
def _chan_cung():
	dung("cấu hình hiện tại sạch", dd.kiem_an_toan() is True)
	for dt in ("Sales Invoice", "MInvoice Invoice", "GL Entry", "Payment Entry"):
		nem("chặn " + dt, lambda dt=dt: dd.kiem_an_toan({dt: 30}), ValueError)
	dung("hoá đơn điện tử nằm trong danh sách chặn", "MInvoice Invoice" in dd.KHONG_DUOC_DON)


@ca("#284 tên bảng chỉ nhận doctype đã khai, vì nó nối thẳng vào câu lệnh")
def _ten_bang():
	la("bảng có dấu cách", dd.ten_bang("Notification Log"), "tabNotification Log")
	la("bảng thường", dd.ten_bang("Version"), "tabVersion")
	for xau in ("Sales Invoice", "Version`; drop table x; --", "", None):
		nem("chặn %r" % (xau,), lambda x=xau: dd.ten_bang(x), ValueError)


@ca("#284 câu xoá luôn mang LIMIT và không bao giờ vượt trần một lần chạy")
def _co_limit():
	so, db = _chay(200000, lo=2000, tran=50000)
	xoa = [c for c in db.lenh if c.lower().startswith("delete")]
	dung("có câu xoá", bool(xoa))
	for c in xoa:
		dung("mang LIMIT: " + c, " limit %s" in c.lower())
		dung("mốc ngày là tham số, không nối chuỗi", "creation < %s" in c.lower())
	la("không vượt trần", so, 50000)
	la("đúng 25 lô", len(xoa), 25)


@ca("#284 đọc ROW_COUNT trước commit, không thì nhịp đêm chạy mà không dọn gì")
def _truoc_commit():
	so, db = _chay(6000, lo=2000, tran=50000)
	la("dọn hết 6000 dòng cũ", so, 6000)
	# Thứ tự bắt buộc trong MỘT lô: delete, rồi đọc số, rồi mới commit.
	i = [n for n, c in enumerate(db.lenh) if c.lower().startswith("delete")][0]
	la("ngay sau xoá là đọc số", db.lenh[i + 1].lower(), "select row_count()")
	la("rồi mới commit", db.lenh[i + 2], "commit")


@ca("#284 hết dòng cũ thì dừng, không chạy thêm câu xoá rỗng")
def _dung_dung_luc():
	so, db = _chay(2500, lo=2000, tran=50000)
	la("xoá đúng số còn lại", so, 2500)
	la("đúng hai lô, không có lô thứ ba", len([c for c in db.lenh if c.lower().startswith("delete")]), 2)


@ca("#284 chỉ gọn tệp khi vừa xoá đủ nhiều")
def _nguong_gon():
	dung("dưới ngưỡng thì không", dd.can_gon(dd.NGUONG_GON - 1) is False)
	dung("đúng ngưỡng thì có", dd.can_gon(dd.NGUONG_GON) is True)
	_, db_it = _chay(100)
	dung("xoá ít: không gọn tệp", not [c for c in db_it.lenh if c.lower().startswith("optimize")])
	_, db_nhieu = _chay(20000)
	dung("xoá nhiều: có gọn tệp", bool([c for c in db_nhieu.lenh if c.lower().startswith("optimize")]))


@ca("#284 thiếu quyền OPTIMIZE chỉ là không co được tệp, không làm hỏng nhịp dọn")
def _gon_hong():
	with patch.object(dd.frappe, "db", DbGia(hong=True)):
		la("trả về False chứ không ném", dd.gon_tep("tabVersion"), False)
	# Và nhịp dọn vẫn phải báo đúng số dòng đã xoá được trước đó.
	db = DbGia(20000)
	goc = db.sql

	def sql_gon_hong(cau, tham=None, **k):
		if str(cau).lower().strip().startswith("optimize"):
			raise RuntimeError("Access denied for OPTIMIZE")
		return goc(cau, tham, **k)

	db.sql = sql_gon_hong
	with patch.object(dd.frappe, "db", db):
		la("vẫn báo đủ số đã xoá", dd.don_mot_bang("Version"), 20000)


@ca("#284 một bảng hỏng không kéo theo hai bảng còn lại")
def _mot_bang_hong():
	db = DbGia(3000)

	def sql_ken(cau, tham=None, **k):
		if "tabNotification Log" in str(cau):
			raise RuntimeError("Table is marked as crashed")
		return DbGia.sql(db, cau, tham, **k)

	db.sql = sql_ken
	with patch.object(dd.frappe, "db", db):
		ket = dd.don_dep_hang_ngay()
	la("bảng hỏng báo 0", ket["Notification Log"], 0)
	dung("hai bảng kia vẫn chạy", ket["Version"] > 0 or ket["Deleted Document"] > 0)
	la("đủ ba bảng trong kết quả", sorted(ket), sorted(dd.BANG_DON))


@ca("#284 hai cửa mở ra ngoài đều tự kiểm System Manager ở dòng đầu")
def _chan_quyen():
	with patch.object(dd.frappe, "get_roles", lambda *a, **k: ["Sales User"]):
		nem("chặn bấm tay", dd.don_dep_ngay_bay_gio, dd.frappe.ValidationError)
		nem("chặn đo dung lượng", dd.do_dung_luong, dd.frappe.ValidationError)
	# Và chặn TRƯỚC khi chạm database, chứ không phải chặn sau khi đã xoá.
	db = DbGia(9999)
	with patch.object(dd.frappe, "get_roles", lambda *a, **k: ["Sales User"]):
		with patch.object(dd.frappe, "db", db):
			try:
				dd.don_dep_ngay_bay_gio()
			except Exception:
				pass
	la("không một câu lệnh nào chạy", db.lenh, [])
