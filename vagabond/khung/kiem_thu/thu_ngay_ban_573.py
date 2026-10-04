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


class _Bill(dict):
	"""Đủ dùng cho ngay_ban.ghi_khi_doi: meta.has_field, get, set."""

	class meta:
		@staticmethod
		def has_field(f):
			return f == ngay_ban.TRUONG

	def set(self, k, v):
		self[k] = v


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
	c = _csdl(bills)
	a, b = _chay(c)
	with a, b:
		kk = kiem_kho.da_ban("TCV", ngay).get(MA, 0)
		kb = kiem_banh._dem_don_khac(ngay, {MA})[0].get(MA, 0)
	return kk, kb


def _duyet_hom_sau(bill, ngay_moi):
	"""Đúng hai dòng của _doi_ngay_ban_nhap chạm ngày: ghi ngày gốc rồi đổi."""
	ngay_ban.ghi_khi_doi(bill)
	bill["posting_date"] = ngay_moi


@ca("v573: hàng tặng out bill ngày 1, duyệt ngày 2: Kiểm kho và Kiểm bánh chỉ trừ ngày 1, ngày 2 không trừ lại")
def _():
	b = _Bill(name="HDB-T1", posting_date=N1)
	la("trước duyệt, ngày 1 (kiểm kho, kiểm bánh)", _dem([b], N1), (1, 1))
	_duyet_hom_sau(b, N2)
	la("sau duyệt, ngày 1 vẫn 1", _dem([b], N1), (1, 1))
	la("sau duyệt, ngày 2 không trừ thêm", _dem([b], N2), (0, 0))
	la("ngày ghi sổ đã sang ngày 2", b["posting_date"], N2)


@ca("v573: đổi ngày hai lần vẫn nhớ ngày bán đầu tiên")
def _():
	b = _Bill(name="HDB-T2", posting_date=N1)
	_duyet_hom_sau(b, N2)
	_duyet_hom_sau(b, "2026-10-05")
	la("ngày bán gốc", b[ngay_ban.TRUONG], N1)
	la("chỉ ngày 1 trừ", [_dem([b], n) for n in (N1, N2, "2026-10-05")], [(1, 1), (0, 0), (0, 0)])


@ca("v573: bill thường không đổi ngày vẫn đếm theo ngày ghi sổ, bill khác ngày không lẫn")
def _():
	a = _Bill(name="HDB-A", posting_date=N1, qty=2)
	b = _Bill(name="HDB-B", posting_date=N2, qty=3)
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
	s = open(os.path.join(GOC, "vagabond", "ban_hang.py"), encoding="utf-8").read()
	i = s.index("def _doi_ngay_ban_nhap")
	than = s[i:s.index("\ndef ", i + 5)]
	dung("_doi_ngay_ban_nhap ghi ngày gốc trước khi đổi",
		0 <= than.find("ngay_ban.ghi_khi_doi(si)") < than.find("si.posting_date = str(moi)"))
