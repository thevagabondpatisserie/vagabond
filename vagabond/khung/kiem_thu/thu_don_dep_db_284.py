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
			xin = int(tham[-1]) if tham and len(tham) > 1 else self.con_lai
			self._vua_xoa = min(xin, self.con_lai)
			self.con_lai -= self._vua_xoa
			return []
		if thap.startswith("optimize"):
			return [("db.tabVersion", "optimize", "note", "recreate + analyze"), ("db.tabVersion", "optimize", "status", "OK")]
		if thap.startswith("select row_count()"):
			return [[self._vua_xoa]]
		return []

	def commit(self):
		self.lenh.append("commit")
		# Đây là dòng quan trọng nhất của tệp này. Xem BẪY MỘT ở đầu tệp.
		self._vua_xoa = 0

	def rollback(self):
		self.lenh.append('rollback')
		self.con_lai += self._vua_xoa
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
	la("bảng hỏng báo chưa biết, không phải 0", ket["Notification Log"], None)
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


@ca('#284 đọc số dòng lỗi phải lùi lô chưa commit, không báo xóa 0')
def _doc_so_hong():
	db = DbGia(6000)
	goc = db.sql
	def hong(cau, *a, **kw):
		if str(cau).lower().startswith('select row_count'):
			raise RuntimeError('Không đọc được số dòng')
		return goc(cau, *a, **kw)
	db.sql = hong
	with patch.object(dd.frappe, 'db', db):
		nem('lỗi không biến thành 0', lambda: dd.don_mot_bang('Version'), RuntimeError)
	la('dòng của lô được trả lại', db.con_lai, 6000)
	dung('không commit lô không biết số', 'commit' not in db.lenh)
	dung('đã rollback', 'rollback' in db.lenh)


@ca("#284 OPTIMIZE phải đọc status, không nhận error rows là thành công")
def _gon_ket_qua():
	for rows, mong in [
		([('db.tabVersion', 'optimize', 'error', 'Operation failed')], False),
		([('db.tabVersion', 'optimize', 'status', 'Operation failed')], False),
		([], False),
		([('thieu',)], False),
		([('db.tabVersion', 'optimize', 'note', 'recreate'), ('db.tabVersion', 'optimize', 'status', 'OK')], True),
	]:
		db = DbGia()
		db.sql = lambda *a, **k: rows
		with patch.object(dd.frappe, 'db', db), patch.object(dd.frappe, 'log_error') as log:
			la('đọc kết quả ' + repr(rows), dd.gon_tep('tabVersion'), mong)
			la('lỗi phải được ghi', log.call_count, 0 if mong else 1)


@ca("#284 ROW_COUNT âm phải rollback, không commit lô")
def _so_am():
	db = DbGia(6000)
	goc = db.sql
	db.sql = lambda cau, *a, **k: [[-1]] if str(cau).lower().startswith('select row_count') else goc(cau, *a, **k)
	with patch.object(dd.frappe, 'db', db):
		nem('số âm không rõ kết quả', lambda: dd.don_mot_bang('Version'), ValueError)
	la('không mất dòng', db.con_lai, 6000)
	dung('không commit', 'commit' not in db.lenh)
	dung('đã rollback', 'rollback' in db.lenh)


@ca("#284 đăng ký API dọn chỉ POST, API xem giữ mặc định")
def _dang_ky_post():
	la('cửa xóa', dd.don_dep_ngay_bay_gio.__vgb_methods__, ['POST'])
	la('cửa xem', dd.do_dung_luong.__vgb_methods__, None)


@ca("#284 DELETE loại lịch sử và payload chứng từ được bảo vệ")
def _giu_dau_vet():
	for dt, cot in [('Version', 'ref_doctype'), ('Deleted Document', 'deleted_doctype')]:
		db = DbGia(0)
		lenh = []
		goc = db.sql
		def sql(cau, tham=None, **k):
			if str(cau).lower().startswith('delete'):
				lenh.append((cau, tham))
			return goc(cau, tham, **k)
		db.sql = sql
		with patch.object(dd.frappe, 'db', db):
			dd.don_mot_bang(dt)
		cau, tham = lenh[0]
		dung('lọc đúng cột ' + dt, ('`%s` not in %%s' % cot) in cau)
		la('tập bảo vệ đúng', set(tham[1]), dd.KHONG_DUOC_DON)
