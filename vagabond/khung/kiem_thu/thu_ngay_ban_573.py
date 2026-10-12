# -*- coding: utf-8 -*-
"""v573: hàng tặng duyệt hôm sau bị trừ số bán hai lần (Dễ báo 04/10/2026).

Chuỗi thật của cửa hàng: tối ngày 1 out bill 1 Croissant bằng Hàng tặng, bill
nằm nháp chờ duyệt, bảng Kiểm kho ngày 1 trừ 1 cái. Sáng ngày 2 anh Việt duyệt,
máy đổi ngày bill sang ngày 2 để ghi sổ và phát hành HĐĐT, bảng Kiểm kho ngày 2
trừ thêm 1 cái nữa.

Ca kiểm chạy THẬT hai hàm đếm `kiem_kho.da_ban` và `kiem_banh._dem_don_khac`,
câu SQL của chúng chạy trên sqlite trong bộ nhớ (chỉ đổi cú pháp tham số
%(x)s sang :x). Bill đổi ngày đúng bằng hàm `ngay_ban.ghi_khi_doi` mà
`ban_hang._doi_ngay_ban_nhap` gọi, không chép tay ngày bán gốc vào dữ liệu.
"""
import datetime
import os
import re
import sqlite3
from unittest.mock import patch

from vagabond.khung.kiem_thu import nen
from vagabond.khung.kiem_thu.nen import ca, dung, la

nen.gia_lap()

from vagabond import ngay_ban  # noqa: E402
from vagabond import kiem_kho  # noqa: E402
from vagabond import kiem_banh  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
N1, N2 = "2026-10-03", "2026-10-04"
MA = "BANU00015"


_KHO = {}  # cơ sở dữ liệu giả: tên bill -> bản đã lưu


class _Bill(dict):
	"""Đủ dùng cho ngay_ban: meta.has_field, get, set, flags, is_new, doctype, name."""

	doctype = "Sales Invoice"

	class meta:
		@staticmethod
		def has_field(f):
			return f == ngay_ban.TRUONG

	def __init__(self, *a, **k):
		super().__init__(*a, **k)
		self.flags = {}

	@property
	def name(self):
		return self["name"]

	def set(self, k, v):
		self[k] = v

	def is_new(self):
		return self["name"] not in _KHO


def _doc_db(dt, ten, truong):
	return (_KHO.get(ten) or {}).get(truong)


def _luu(b):
	"""Mô phỏng doc.save(): chạy hook validate thật rồi ghi xuống, xoá cờ."""
	with patch.object(kiem_kho.frappe.db, "get_value", _doc_db, create=True):
		ngay_ban.chan_ghi_tay(b)
	_KHO[b.name] = dict(b)
	b.flags = {}
	return b


def _moi(**k):
	"""Bill mới lưu lần đầu (out bill tại quầy)."""
	return _luu(_Bill(**k))


def _csdl(bills):
	c = sqlite3.connect(":memory:")
	c.row_factory = sqlite3.Row
	c.execute("create table `tabSales Invoice` (name text, docstatus int, vgb_huy int, vgb_tam_tinh int,"
		" vgb_quay text, posting_date text, vgb_ngay_ban text, custom_nguon text, custom_pancake_display_id text)")
	c.execute("create table `tabSales Invoice Item` (parent text, item_code text, qty real)")
	for b in bills:
		c.execute("insert into `tabSales Invoice` values (?,?,?,?,?,?,?,?,?)", (b["name"], b.get("docstatus", 0),
			0, 0, "TCV", b["posting_date"], b.get(ngay_ban.TRUONG), b.get("custom_nguon", "Tại quầy"), None))
		c.execute("insert into `tabSales Invoice Item` values (?,?,?)", (b["name"], MA, b.get("qty", 1)))
	return c


def _chay(c):
	def sql(cau, thamso=None, as_dict=False, **k):
		_s = lambda v: str(v) if isinstance(v, datetime.date) else v
		if isinstance(thamso, (tuple, list)):
			cau, ts = cau.replace("%s", "?"), [_s(v) for v in thamso]
		else:
			cau = re.sub(r"%\((\w+)\)s", r":\1", cau)
			ts = {kk: _s(v) for kk, v in (thamso or {}).items()}
		rows = c.execute(cau, ts).fetchall()
		return [nen.Doi(dict(r)) for r in rows]

	def get_all(dt, filters=None, fields=None, **k):
		if dt == "Sales Invoice":  # đường cũ trước v573, chỉ để đo số liệu trước khi sửa
			q = ("select name, custom_nguon, custom_pancake_display_id from `tabSales Invoice`"
				" where posting_date = ? and docstatus < 2 and ifnull(vgb_huy, 0) = 0")
			return [nen.Doi(dict(r)) for r in c.execute(q, [str(filters["posting_date"])]).fetchall()]
		ten = sorted((filters or {}).get("parent", ["in", []])[1])
		q = "select parent, item_code, qty from `tabSales Invoice Item` where parent in (%s)" % ",".join("?" * len(ten))
		return [nen.Doi(dict(r)) for r in c.execute(q, ten).fetchall()]

	fr = kiem_kho.frappe
	return patch.object(fr.db, "sql", sql), patch.object(fr, "get_all", get_all)


def _dem(bills, ngay):
	"""Đếm trên bản ĐÃ LƯU của từng bill, như máy chủ đọc cơ sở dữ liệu."""
	c = _csdl([_KHO.get(x["name"], x) for x in bills])
	a, b = _chay(c)
	with a, b:
		kk = kiem_kho.da_ban("TCV", ngay).get(MA, 0)
		kb = kiem_banh._dem_don_khac(ngay, {MA})[0].get(MA, 0)
	return kk, kb


def _duyet_hom_sau(bill, ngay_moi):
	"""Đúng chuỗi của _doi_ngay_ban_nhap: ghi ngày gốc, đổi ngày, lưu (qua hook)."""
	with patch.object(kiem_kho.frappe.db, "get_value", _doc_db, create=True):
		ngay_ban.ghi_khi_doi(bill)
	bill["posting_date"] = ngay_moi
	_luu(bill)


@ca("v573: hàng tặng out bill ngày 1, duyệt ngày 2: Kiểm kho và Kiểm bánh chỉ trừ ngày 1, ngày 2 không trừ lại")
def _():
	b = _moi(name="HDB-T1", posting_date=N1)
	la("trước duyệt, ngày 1 (kiểm kho, kiểm bánh)", _dem([b], N1), (1, 1))
	_duyet_hom_sau(b, N2)
	la("sau duyệt, ngày 1 vẫn 1", _dem([b], N1), (1, 1))
	la("sau duyệt, ngày 2 không trừ thêm", _dem([b], N2), (0, 0))
	la("ngày ghi sổ đã sang ngày 2", b["posting_date"], N2)


@ca("v573: đổi ngày hai lần vẫn nhớ ngày bán đầu tiên")
def _():
	b = _moi(name="HDB-T2", posting_date=N1)
	_duyet_hom_sau(b, N2)
	_duyet_hom_sau(b, "2026-10-05")
	la("ngày bán gốc", b[ngay_ban.TRUONG], N1)
	la("chỉ ngày 1 trừ", [_dem([b], n) for n in (N1, N2, "2026-10-05")], [(1, 1), (0, 0), (0, 0)])


@ca("v573: bill thường không đổi ngày vẫn đếm theo ngày ghi sổ, bill khác ngày không lẫn")
def _():
	a = _moi(name="HDB-A", posting_date=N1, qty=2)
	b = _moi(name="HDB-B", posting_date=N2, qty=3)
	la("ngày 1", _dem([a, b], N1), (2, 2))
	la("ngày 2", _dem([a, b], N2), (3, 3))


@ca("v573: thuoc_ngay (Python) và dk_sql (SQL) cùng nghĩa trên mọi tổ hợp ngày")
def _():
	ca_ = [(N1, None), (N2, None), (N2, N1), (N1, N1), (N1, N2), ("2026-10-05", N1)]
	for i, (pd, nb) in enumerate(ca_):
		b = _Bill(name="X%d" % i, posting_date=pd)
		if nb:
			b[ngay_ban.TRUONG] = nb
		for n in (N1, N2, "2026-10-05"):
			la("%s/%s ngày %s" % (pd, nb, n), _dem([b], n)[0], 1 if ngay_ban.thuoc_ngay(b, n) else 0)


@ca("v573 (Codex #438): Desk/API gửi sẵn ngày bán vào bill mới thì bị bỏ, bill đếm theo ngày ghi sổ")
def _():
	# Chuỗi Codex mô tả: payload tự chế có vgb_ngay_ban ngày khác.
	b = _moi(name="HDB-F1A", posting_date=N2, **{ngay_ban.TRUONG: N1})
	la("ô ngày bán bị bỏ", b.get(ngay_ban.TRUONG), None)
	la("ngày 1 không bị kéo số sang", _dem([b], N1), (0, 0))
	la("ngày ghi sổ vẫn trừ", _dem([b], N2), (1, 1))


@ca("v573 (Codex #438): sửa tay ô ngày bán trên bill đang lưu thì trả về giá trị đang lưu")
def _():
	b = _moi(name="HDB-F1B", posting_date=N1)
	_duyet_hom_sau(b, N2)
	b[ngay_ban.TRUONG] = "2026-10-05"
	_luu(b)
	la("giữ ngày gốc máy ghi", _KHO["HDB-F1B"][ngay_ban.TRUONG], N1)
	la("chỉ ngày 1 trừ", [_dem([b], n) for n in (N1, N2, "2026-10-05")], [(1, 1), (0, 0), (0, 0)])


@ca("v573 (Codex #438): gửi kèm ngày giả ngay trước khi duyệt cũng không lọt, máy lấy ngày đang lưu")
def _():
	b = _moi(name="HDB-F1C", posting_date=N1)
	b[ngay_ban.TRUONG] = "2026-09-01"
	_duyet_hom_sau(b, N2)
	la("ngày gốc là ngày ghi sổ cũ", _KHO["HDB-F1C"][ngay_ban.TRUONG], N1)
	la("không dồn về ngày giả", _dem([b], "2026-09-01"), (0, 0))


@ca("v573 (Codex #438): gia_tri_giu chỉ nhận giá trị khi máy ghi")
def _():
	la("máy ghi", ngay_ban.gia_tri_giu(None, N1, True), N1)
	la("ngoài gửi, bill mới", ngay_ban.gia_tri_giu(None, N1, False), None)
	la("ngoài gửi, đã có", ngay_ban.gia_tri_giu(N1, N2, False), N1)
	la("ngoài xoá", ngay_ban.gia_tri_giu(N1, None, False), N1)


@ca("v573: đổi ngày thì đo lại cả ngày bán gốc trên bảng Kiểm bánh")
def _():
	la("ba ngày", ngay_ban.cac_ngay_phai_do(N1, N2, N1), [N1, N2])
	la("có ngày gốc khác", ngay_ban.cac_ngay_phai_do(N2, "2026-10-05", N1), [N2, "2026-10-05", N1])
	la("bỏ rỗng", ngay_ban.cac_ngay_phai_do(None, N2, ""), [N2])


@ca("v573: không còn chỗ đếm số bán Kiểm kho, Kiểm bánh lọc thẳng theo ngày ghi sổ")
def _():
	for tep, ham in (("kiem_kho.py", "def da_ban"), ("kiem_banh.py", "def _dem_don_khac")):
		s = open(os.path.join(GOC, "vagabond", tep), encoding="utf-8").read()
		i = s.index(ham)
		than = s[i:s.index("\ndef ", i + 5)]
		# Đột biến M2 (04/10 đọc theo điều 17b): chỉ dò "ngay_ban.dk_sql" thì
		# khớp cả docstring, nên phải dò đúng lời gọi và cấm mọi dạng lọc thẳng.
		dung("%s gọi ngay_ban.dk_sql" % tep, 'ngay_ban.dk_sql("si")' in than)
		dung("%s không lọc posting_date trực tiếp" % tep,
			not re.search(r"posting_date\s*=\s*%", than) and '"posting_date": str(ngay)' not in than)
	h = open(os.path.join(GOC, "vagabond", "hooks.py"), encoding="utf-8").read()
	dung("hook validate chặn ghi tay đã đăng ký", '"vagabond.ngay_ban.chan_ghi_tay"' in h)
	s = open(os.path.join(GOC, "vagabond", "ban_hang.py"), encoding="utf-8").read()
	i = s.index("def _doi_ngay_ban_nhap")
	than = s[i:s.index("\ndef ", i + 5)]
	dung("_doi_ngay_ban_nhap ghi ngày gốc trước khi đổi",
		0 <= than.find("ngay_ban.ghi_khi_doi(si)") < than.find("si.posting_date = str(moi)"))


@ca("v576 (Codex #440): bảng mùa vụ đếm kênh khác theo ngày bán gốc, bill duyệt sau ngày cuối mùa không biến mất")
def _():
	from vagabond import mua_vu

	c = sqlite3.connect(":memory:")
	c.row_factory = sqlite3.Row
	c.execute("create table `tabSales Invoice` (name text, docstatus int, vgb_huy int, posting_date text,"
		" vgb_ngay_ban text, custom_nguon text, custom_pancake_display_id text)")
	c.execute("create table `tabSales Invoice Item` (parent text, item_code text, qty real)")
	# Mùa 01/10 đến 03/10. Bill tặng bán ngày 03/10, duyệt 04/10 (ngoài mùa).
	for ten, pd, nb, sl in (("HDB-M1", "2026-10-04", "2026-10-03", 1), ("HDB-M2", "2026-10-02", None, 2),
			("HDB-M3", "2026-10-04", None, 5)):
		c.execute("insert into `tabSales Invoice` values (?,?,?,?,?,?,?)", (ten, 1, 0, pd, nb, "Hàng tặng", None))
		c.execute("insert into `tabSales Invoice Item` values (?,?,?)", (ten, "BASS001", sl))
	a, b = _chay(c)
	with a, b, patch.object(mua_vu, "frappe", kiem_kho.frappe):
		ra = mua_vu._dem_kenh_khac_ngay("2026-10-01", "2026-10-03")
	la("ngày 03/10 giữ bill duyệt hôm sau", ra.get(("BASS001", "2026-10-03"), {}).get("so"), 1)
	la("ngày 02/10 bill thường", ra.get(("BASS001", "2026-10-02"), {}).get("so"), 2)
	la("bill bán ngoài mùa không lọt vào", sorted(k[1] for k in ra), ["2026-10-02", "2026-10-03"])
