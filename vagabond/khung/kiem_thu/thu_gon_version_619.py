# -*- coding: utf-8 -*-
"""v619: gọn lịch sử máy ghi trên hoá đơn bán, xoá lịch sử ngắn của màn web.

Anh Việt chọn 28/10/2026: cơ sở dữ liệu 1,62 GB trên trần 2 GB, hơn một
phần ba là lịch sử sửa hoá đơn bán do máy ghi, mỗi lần chụp lại cả bảng món
cũ lẫn mới. Quá 30 ngày thì bỏ hai ảnh chụp đó, GIỮ ai đổi, lúc nào, trường
nào đổi. Lịch sử do người sửa không đụng. Lịch sử trang web, mùa vụ, nội dung
web giữ 30 ngày.

Bản giả lập cơ sở dữ liệu dưới đây giữ đúng ba hành vi mà mã thật dựa vào:
commit xoá ROW_COUNT của câu trước, rollback trả lại mọi thay đổi từ lần
commit trước, và câu lệnh chọn đọc đúng các điều kiện lọc (không lọc dễ tính
hơn mã thật, vì như thế ca kiểm sẽ xanh cả khi mã quên một điều kiện).
"""

import json
from unittest.mock import patch

from vagabond import don_dep_db as dd
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la, nem

CU = "2026-07-01 10:00:00"     # 45 ngày trước ngày cố định 15/08
MOI = "2026-08-10 10:00:00"    # 5 ngày trước
MAY = "Administrator"
NGUOI = "thu.ngan@example.com"


def _dl(them=None, bot_dong=False):
	"""Dữ liệu lịch sử giống bản ERPNext ghi khi máy dựng lại bảng món."""
	dong = {"item_code": "BANH-01", "qty": 2, "rate": 450000, "description": "Bánh mùa thu " * 40}
	d = {
		"changed": [["status", "Draft", "Unpaid"], ["docstatus", 0, 1]],
		"row_changed": [["taxes", 0, "x1", [["tax_amount", 1, 2]]]],
		"added": [] if bot_dong else [["items", dict(dong, name="moi%d" % i)] for i in range(3)],
		"removed": [] if bot_dong else [["items", dict(dong, name="cu%d" % i)] for i in range(3)],
		"data_import": None,
	}
	d.update(them or {})
	return json.dumps(d, indent=1)


# Bản giả lập chỉ hiểu ĐÚNG ba câu lệnh này trên bảng lịch sử, và câu nào khác
# (đổi "and" thành "or", bỏ một điều kiện) thì ném lỗi chứ không tự lọc hộ.
# Đột biến "xoá ngắn không lọc loại" từng lọt vì bản giả lập cũ tự lọc theo
# tham số, bỏ qua chính câu lệnh. Bench chạy lại ba câu này trên MariaDB thật.
CAU_CHON = ("select name, data, creation from `tabVersion` where ref_doctype = %s and owner in %s and creation < %s"
	" and length(data) > %s and (creation > %s or (creation = %s and name > %s)) order by creation, name limit %s")
CAU_SUA = "update `tabVersion` set data = %s where name = %s and ref_doctype = %s and owner in %s"
CAU_XOA = "delete from `tabVersion` where ref_doctype = %s and creation < %s limit %s"


class DbVersion:
	def __init__(self, dong):
		self.dong = {r["name"]: dict(r) for r in dong}
		self.chung = {}
		self._chot = json.dumps([self.dong, self.chung])
		self.lenh = []
		self._vua_xoa = 0
		self.hong_update_thu = None
		self._dem_update = 0

	def sql(self, cau, tham=None, as_dict=False, **k):
		c = " ".join(str(cau).split())
		t = c.lower()
		self.lenh.append(c)
		if ("`tabversion`" in t and not t.startswith(("delete from `tabversion` where creation", "optimize"))
				and c not in (CAU_CHON, CAU_SUA, CAU_XOA)):
			raise AssertionError("câu lệnh lạ trên bảng lịch sử: " + c)
		if c == CAU_CHON:
			dt, chu, moc, nguong, tao, tao2, ten, gioi = tham
			dung("con trỏ dùng cùng một giờ tạo cho hai vế", tao == tao2)
			kq = [Doi(name=r["name"], data=r["data"], creation=r["creation"])
				for r in sorted(self.dong.values(), key=lambda r: (str(r["creation"]), r["name"]))
				if r["ref_doctype"] == dt and r["owner"] in chu and str(r["creation"]) < str(moc)
				and len(r["data"].encode("utf-8")) > nguong
				and (str(r["creation"]) > str(tao) or (str(r["creation"]) == str(tao) and r["name"] > ten))]
			return kq[:gioi]
		if c == CAU_SUA:
			self._dem_update += 1
			if self.hong_update_thu and self._dem_update == self.hong_update_thu:
				raise RuntimeError("Lock wait timeout")
			data, ten, dt, chu = tham
			r = self.dong.get(ten)
			if r and r["ref_doctype"] == dt and r["owner"] in chu:
				r["data"] = data
			return []
		if c == CAU_XOA:
			dt, moc, gioi = tham
			xoa = [n for n, r in sorted(self.dong.items()) if r["ref_doctype"] == dt and str(r["creation"]) < str(moc)][:gioi]
			for n in xoa:
				del self.dong[n]
			self._vua_xoa = len(xoa)
			return []
		if t.startswith("delete"):
			self._vua_xoa = 0
			return []
		if t.startswith("select row_count()"):
			return [[self._vua_xoa]]
		if t.startswith("optimize"):
			return [("db.tabVersion", "optimize", "status", "OK")]
		return []

	def get_global(self, khoa):
		return self.chung.get(khoa)

	def set_global(self, khoa, gt):
		self.lenh.append("set_global " + khoa)
		self.chung[khoa] = gt

	def commit(self):
		self.lenh.append("commit")
		self._vua_xoa = 0
		self._chot = json.dumps([self.dong, self.chung])

	def rollback(self):
		self.lenh.append("rollback")
		self.dong, self.chung = json.loads(self._chot)
		self._vua_xoa = 0


def _v(ten, dt="Sales Invoice", owner=MAY, creation=CU, data=None):
	return dict(name=ten, ref_doctype=dt, owner=owner, creation=creation, data=data if data is not None else _dl())


@ca("v619 gọn dữ liệu: bỏ ảnh chụp dòng con, giữ nguyên ai đổi trường nào")
def _gon_thuan():
	goc = _dl()
	moi, bot = dd.gon_du_lieu(goc, "2026-08-15")
	dung("có gọn", moi is not None and bot > 0)
	d, g = json.loads(moi), json.loads(goc)
	la("giữ trường đổi", d["changed"], g["changed"])
	la("giữ dòng con đổi", d["row_changed"], g["row_changed"])
	la("giữ khoá khác", "data_import" in d, True)
	la("bỏ ảnh chụp", (d["added"], d["removed"]), ([], []))
	la("ghi lại đã bỏ mấy dòng", d[dd.DAU_GON], {"added": 3, "removed": 3, "ngay": "2026-08-15"})
	dung("ngắn hơn hẳn", len(moi) < len(goc) / 3)
	la("gọn lần hai thì để nguyên", dd.gon_du_lieu(moi), (None, 0))
	la("không có dòng con thì để nguyên", dd.gon_du_lieu(_dl(bot_dong=True)), (None, 0))
	for xau in (None, "", "khong phai json", "[1,2]", "{}", 12):
		la("dữ liệu lạ %r" % (xau,), dd.gon_du_lieu(xau), (None, 0))


@ca("v619 gọn lịch sử máy ghi: chỉ lịch sử của máy, quá 30 ngày, đúng hoá đơn bán")
def _gon_dung_pham_vi():
	ngan = json.dumps({"changed": [["status", "Draft", "Paid"]], "added": [["items", {"a": 1}]], "removed": []})
	db = DbVersion([
		_v("a-may-cu"),
		_v("b-nguoi-cu", owner=NGUOI),
		_v("c-may-moi", creation=MOI),
		_v("d-hd-mua", dt="Purchase Invoice"),
		_v("e-ngan", data=ngan),
		_v("f-da-gon", data=dd.gon_du_lieu(_dl(), "2026-08-01")[0] + " " * 5000),
	])
	truoc = json.loads(json.dumps(db.dong))
	with patch.object(dd.frappe, "db", db):
		kq = dd.gon_lich_su_may("Sales Invoice")
	la("gọn đúng một lịch sử", kq["so_dong"], 1)
	dung("có báo số byte bớt", kq["byte"] > 0)
	la("không mất dòng nào", sorted(db.dong), sorted(truoc))
	for ten in ("b-nguoi-cu", "c-may-moi", "d-hd-mua", "e-ngan", "f-da-gon"):
		la("để nguyên " + ten, db.dong[ten]["data"], truoc[ten]["data"])
	d = json.loads(db.dong["a-may-cu"]["data"])
	la("lịch sử máy cũ: bỏ ảnh chụp", (d["added"], d["removed"]), ([], []))
	la("lịch sử máy cũ: giữ trường đổi", d["changed"], json.loads(truoc["a-may-cu"]["data"])["changed"])
	dung("không có câu xoá nào", not [c for c in db.lenh if c.lower().startswith("delete")])


@ca("v619 gọn theo lô có trần, mỗi dòng đọc một lần, hết thì dừng")
def _gon_theo_lo():
	db = DbVersion([_v("v%05d" % i) for i in range(1200)])
	with patch.object(dd.frappe, "db", db):
		kq = dd.gon_lich_su_may("Sales Invoice", lo=500)
	la("gọn đủ 1200", kq["so_dong"], 1200)
	chon = [c for c in db.lenh if c.lower().startswith("select name, data")]
	la("ba lô có dòng và một lần đọc rỗng", len(chon), 4)
	la("commit sau mỗi lô", db.lenh.count("commit"), 3)
	db2 = DbVersion([_v("v%05d" % i) for i in range(1200)])
	with patch.object(dd.frappe, "db", db2):
		kq2 = dd.gon_lich_su_may("Sales Invoice", lo=500, tran=700)
	la("không vượt trần", kq2["so_dong"], 700)
	la("còn lại để đêm sau", sum(1 for r in db2.dong.values() if dd.DAU_GON not in r["data"]), 500)
	db3 = DbVersion([_v("v%05d" % i, data=_dl(bot_dong=True) + " " * 5000) for i in range(30)])
	with patch.object(dd.frappe, "db", db3):
		kq3 = dd.gon_lich_su_may("Sales Invoice", lo=10)
	la("dòng dài mà không có gì để gọn không làm vòng lặp kẹt", kq3["so_dong"], 0)
	la("đọc qua mỗi dòng một lần", len([c for c in db3.lenh if c.lower().startswith("select name, data")]), 4)


@ca("v619 lỗi giữa lô thì trả lại cả lô, không commit nửa chừng")
def _gon_loi():
	db = DbVersion([_v("v%03d" % i) for i in range(8)])
	db.hong_update_thu = 6
	with patch.object(dd.frappe, "db", db):
		nem("lỗi được ném ra", lambda: dd.gon_lich_su_may("Sales Invoice", lo=4), RuntimeError)
	la("lô đầu đã commit vẫn gọn", sum(1 for r in db.dong.values() if dd.DAU_GON in r["data"]), 4)
	dung("đã rollback lô hỏng", "rollback" in db.lenh)
	la("lô hỏng còn nguyên", [dd.DAU_GON in db.dong["v%03d" % i]["data"] for i in range(4, 8)], [False] * 4)


@ca("v619 lịch sử màn web và mùa vụ giữ 30 ngày, lịch sử chứng từ không bao giờ bị xoá")
def _version_ngan():
	la("mốc", dd.VERSION_NGAN, {"Web Page": 30, "Vagabond Mua Vu": 30, "Vagabond Noi Dung Web": 30})
	la("chỉ gọn hoá đơn bán", dd.GON_MAY_GHI, {"Sales Invoice": 30})
	la("chỉ lịch sử của máy", dd.NGUOI_MAY, ("Administrator",))
	db = DbVersion([
		_v("w-cu", dt="Web Page"), _v("w-moi", dt="Web Page", creation=MOI),
		_v("si-cu", dt="Sales Invoice"), _v("mv-cu", dt="Vagabond Mua Vu", owner=NGUOI),
	])
	with patch.object(dd.frappe, "db", db):
		la("xoá một trang web cũ", dd.don_version_ngan("Web Page"), 1)
		la("xoá mùa vụ cũ kể cả người sửa", dd.don_version_ngan("Vagabond Mua Vu"), 1)
		nem("không nhận doctype chưa khai", lambda: dd.don_version_ngan("Sales Invoice"), ValueError)
	la("còn lại", sorted(db.dong), ["si-cu", "w-moi"])
	with patch.dict(dd.VERSION_NGAN, {"Sales Invoice": 30}):
		nem("khai chứng từ vào diện xoá ngắn là chặn", dd.kiem_an_toan, ValueError)
	with patch.object(dd, "KHOA_BO", ("added", "removed", "changed")):
		nem("thêm khoá được bỏ là chặn", dd.kiem_an_toan, ValueError)


@ca("v619 nhịp đêm chạy đủ việc mới, một việc hỏng không kéo theo việc khác, gọn tệp khi bớt nhiều")
def _nhip_dem():
	ds = [_v("si%04d" % i) for i in range(1500)] + [_v("w%03d" % i, dt="Web Page") for i in range(3)]
	db = DbVersion(ds)
	with patch.object(dd.frappe, "db", db), patch.object(dd, "NGUONG_GON_BYTE", 1000):
		ket = dd.don_dep_hang_ngay()
	la("gọn đủ", ket["Gọn lịch sử máy ghi Sales Invoice"], 1500)
	la("xoá trang web", ket["Lịch sử Web Page"], 3)
	for dt in dd.BANG_DON:
		dung("vẫn chạy bảng cũ " + dt, dt in ket)
	dung("có gọn tệp", any(c.lower().startswith("optimize") for c in db.lenh))
	db2 = DbVersion([_v("w%03d" % i, dt="Web Page") for i in range(3)])
	goc = db2.sql

	def hong(cau, *a, **k):
		if str(cau).lower().startswith("select name, data"):
			raise RuntimeError("Table is marked as crashed")
		return goc(cau, *a, **k)

	db2.sql = hong
	with patch.object(dd.frappe, "db", db2), patch.object(dd.frappe, "log_error") as log:
		ket2 = dd.don_dep_hang_ngay()
	la("việc hỏng báo chưa biết", ket2["Gọn lịch sử máy ghi Sales Invoice"], None)
	la("việc khác vẫn xong", ket2["Lịch sử Web Page"], 3)
	dung("có ghi lỗi", log.call_count >= 1)
	dung("bớt ít thì không gọn tệp", not any(c.lower().startswith("optimize") for c in db2.lenh))


def _hang(bang, ten, **nd):
	return [bang, dict(nd, name=ten, idx=1, creation="2026-07-01 10:00:0%s" % ten[-1], modified="x" + ten)]


@ca("v619 Codex 4400115947: máy đổi món thật thì giữ dấu vết, chỉ bỏ cặp dòng dựng lại y hệt")
def _giu_doi_that():
	# Tái hiện trên ad524507: thay món A bằng món B cùng giá thì sau khi gọn
	# lịch sử không còn chữ BANH-A lẫn BANH-B.
	thay = json.dumps({"changed": [], "added": [_hang("items", "n1", item_code="BANH-B", rate=450000)],
		"removed": [_hang("items", "o1", item_code="BANH-A", rate=450000)]})
	la("chỉ có đổi món thật: để nguyên", dd.gon_du_lieu(thay), (None, 0))
	tron = json.dumps({"changed": [],
		"added": [_hang("items", "n%d" % i, item_code="BANH-0", qty=1) for i in range(3)]
			+ [_hang("items", "n9", item_code="BANH-B", qty=1)],
		"removed": [_hang("items", "o9", item_code="BANH-A", qty=1)]
			+ [_hang("items", "o%d" % i, item_code="BANH-0", qty=1) for i in range(3)]})
	moi, bot = dd.gon_du_lieu(tron, "2026-10-28")
	d = json.loads(moi)
	la("giữ dòng thêm thật", [x[1]["item_code"] for x in d["added"]], ["BANH-B"])
	la("giữ dòng bớt thật", [x[1]["item_code"] for x in d["removed"]], ["BANH-A"])
	la("ghi số cặp đã bỏ", d[dd.DAU_GON], {"added": 3, "removed": 3, "ngay": "2026-10-28"})
	so_luong = json.dumps({"added": [_hang("items", "n1", item_code="BANH-0", qty=2)],
		"removed": [_hang("items", "o1", item_code="BANH-0", qty=1)]})
	la("đổi số lượng là đổi thật: để nguyên", dd.gon_du_lieu(so_luong), (None, 0))
	thue = json.dumps({"added": [_hang("items", "n1", item_code="BANH-0"),
		_hang("item_wise_tax_details", "t1", item_row="n1", tax_amount=36000)],
		"removed": [_hang("items", "o1", item_code="BANH-0"),
		_hang("item_wise_tax_details", "t0", item_row="o1", tax_amount=36000)]})
	d = json.loads(dd.gon_du_lieu(thue)[0])
	la("dòng thuế trỏ tới dòng món dựng lại cũng là cặp y hệt", (d["added"], d["removed"]), ([], []))
	thue_doi = json.dumps({"added": [_hang("item_wise_tax_details", "t1", item_row="n1", tax_amount=40000)],
		"removed": [_hang("item_wise_tax_details", "t0", item_row="o1", tax_amount=36000)]})
	la("tiền thuế đổi là đổi thật", dd.gon_du_lieu(thue_doi), (None, 0))
	khac_bang = json.dumps({"added": [_hang("items", "n1", qty=1)], "removed": [_hang("payment_schedule", "o1", qty=1)]})
	la("khác bảng không ghép cặp", dd.gon_du_lieu(khac_bang), (None, 0))


@ca("v619 Codex 4400115951: dòng đã đọc không chiếm trần đêm sau, con trỏ lưu cùng lô")
def _con_tro():
	# Tái hiện trên ad524507: ba lịch sử gọn xong vẫn dài (trường đổi lớn), trần
	# 2 mỗi đêm: đêm một gọn 2, đêm hai gọn 0 và dòng thứ ba không bao giờ gọn.
	lon = [["remarks", "a" * 3000, "b" * 3000]]
	db = DbVersion([_v("v%d" % i, creation="2026-07-0%d 10:00:00" % (i + 1), data=_dl({"changed": lon})) for i in range(3)])
	with patch.object(dd.frappe, "db", db):
		la("đêm một gọn 2", dd.gon_lich_su_may("Sales Invoice", tran=2)["so_dong"], 2)
		la("đêm hai gọn nốt 1", dd.gon_lich_su_may("Sales Invoice", tran=2)["so_dong"], 1)
		la("đêm ba không còn gì", dd.gon_lich_su_may("Sales Invoice", tran=2)["so_dong"], 0)
	la("con trỏ dừng ở dòng cuối", db.chung[dd.CON_TRO % "Sales Invoice"], "2026-07-03 10:00:00|v2")
	chon = [c for c in db.lenh if c.lower().startswith("select name, data")]
	la("đêm ba chỉ một lần đọc rỗng", len(chon), 4)
	# Lỗi giữa lô thì con trỏ không tiến, đêm sau đọc lại đúng lô đó.
	db2 = DbVersion([_v("v%d" % i, creation="2026-07-0%d 10:00:00" % (i + 1)) for i in range(4)])
	db2.hong_update_thu = 3
	with patch.object(dd.frappe, "db", db2):
		nem("lỗi lô hai", lambda: dd.gon_lich_su_may("Sales Invoice", lo=2), RuntimeError)
		la("con trỏ ở cuối lô một", db2.chung[dd.CON_TRO % "Sales Invoice"], "2026-07-02 10:00:00|v1")
		db2.hong_update_thu = None
		la("đêm sau gọn đúng lô hai", dd.gon_lich_su_may("Sales Invoice", lo=2)["so_dong"], 2)
	la("đủ bốn dòng đã gọn", sum(1 for r in db2.dong.values() if dd.DAU_GON in r["data"]), 4)
	for xau in (None, "", "khong co vach", 12):
		la("con trỏ hỏng %r thì đọc từ đầu" % (xau,), dd._doc_con_tro(xau), dd.CON_TRO_DAU)
	la("con trỏ đúng", dd._doc_con_tro("2026-07-02 10:00:00|v1"), ("2026-07-02 10:00:00", "v1"))
