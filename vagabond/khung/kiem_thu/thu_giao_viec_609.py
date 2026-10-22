# -*- coding: utf-8 -*-
"""v609: giao việc không còn qua assign_to.add của Frappe, nên không còn thư
"đã phân công nhiệm vụ mới" (anh Việt 22/10/2026: 40 thư trong 8 phút).

Ca gọi THẬT giao_viec.giao với một lớp Frappe giả, đếm ToDo được ghi và chốt
bằng AST rằng tệp không còn import assign_to.
"""

import ast
import os
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import giao_viec as gv  # noqa: E402

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class _Site(object):
	def __init__(self, doc_duoc=True):
		self.todo = []
		self.chia_se = []
		self.doc_duoc = doc_duoc
		self.loi = []

	def get_doc(self, d):
		site = self

		class _TD(object):
			def __init__(self, d):
				self.d = dict(d)

			def insert(self, ignore_permissions=False):
				site.todo.append((self.d, ignore_permissions))

		return _TD(d)

	def vao(self):
		fr = sys.modules["frappe"]
		share = types.SimpleNamespace(add=lambda dt, n, u, flags=None: self.chia_se.append((dt, n, u, flags)))
		db = types.SimpleNamespace(set_value=lambda *a, **k: None, get_value=lambda *a, **k: None)
		return [
			um.patch.object(fr, "get_doc", self.get_doc),
			um.patch.object(fr, "has_permission", lambda dt, p, doc=None, user=None: self.doc_duoc, create=True),
			um.patch.object(fr, "share", share, create=True),
			um.patch.object(fr, "db", db),
			um.patch.object(fr, "log_error", lambda *a, **k: self.loi.append(a)),
			um.patch.object(fr.session, "user", "uyen@vgb"),
			um.patch.object(gv, "_dang_giao", lambda dt, n: set()),
			um.patch.object(gv, "go_giao", lambda dt, n, tru=None: None),
			um.patch.object(gv, "_dong_bo_nhan", lambda dt, n: None),
			um.patch.object(gv, "_bao", lambda *a, **k: None),
		]


def _chay(site, ham):
	ps = site.vao()
	for p in ps:
		p.start()
	try:
		return ham()
	finally:
		for p in reversed(ps):
			p.stop()


@ca("v609 giao việc: mỗi người một dòng ToDo ghi thẳng, đủ ô, không qua assign_to.add")
def _ghi_thang():
	site = _Site()
	kq = _chay(site, lambda: gv.giao("Purchase Receipt", "PNK-1", ["a@vgb", "b@vgb", "a@vgb"], "chờ đếm", han="2026-10-23", bao=0))
	la("hai người, hai dòng", kq, {"giao": 2, "moi": 2})
	la("đúng hai ToDo", len(site.todo), 2)
	d, ip = site.todo[0]
	la("ô ToDo", (d["doctype"], d["allocated_to"], d["reference_type"], d["reference_name"], d["description"],
		d["status"], d["date"], d["assigned_by"]),
		("ToDo", "a@vgb", "Purchase Receipt", "PNK-1", "chờ đếm", "Open", "2026-10-23", "uyen@vgb"))
	dung("ghi bỏ qua quyền (hook chạy giữa luồng lưu)", ip)
	la("đã đọc được thì không chia sẻ thêm", site.chia_se, [])


@ca("v609 giao việc: người chưa đọc được chứng từ thì được chia sẻ quyền đọc, lỗi chia sẻ không chặn")
def _chia_se():
	site = _Site(doc_duoc=False)
	_chay(site, lambda: gv.giao("Material Request", "YCMH-1", ["c@vgb"], "duyệt", bao=0))
	la("chia sẻ cho đúng người", [(x[0], x[1], x[2]) for x in site.chia_se], [("Material Request", "YCMH-1", "c@vgb")])
	dung("bỏ qua quyền chia sẻ", site.chia_se[0][3] == {"ignore_share_permission": True})
	site = _Site(doc_duoc=False)
	fr = sys.modules["frappe"]
	ps = site.vao()
	for p in ps:
		p.start()
	try:
		with um.patch.object(fr, "share", types.SimpleNamespace(add=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))):
			kq = gv.giao("Material Request", "YCMH-2", ["c@vgb"], "duyệt", bao=0)
	finally:
		for p in reversed(ps):
			p.stop()
	la("ToDo vẫn ghi dù chia sẻ lỗi", (kq["giao"], len(site.todo)), (1, 1))
	dung("lỗi chia sẻ chỉ ghi log", len(site.loi) == 1)


@ca("v609 giao việc: tệp không còn đụng assign_to của Frappe (nguồn duy nhất của thư giao việc)")
def _ast():
	src = open(os.path.join(GOI, "giao_viec.py"), encoding="utf-8").read()
	cay = ast.parse(src)
	imp = [ast.unparse(n) for n in ast.walk(cay) if isinstance(n, (ast.Import, ast.ImportFrom)) and "assign_to" in ast.unparse(n)]
	la("không import assign_to", imp, [])
	goi = [ast.unparse(n) for n in ast.walk(cay) if isinstance(n, ast.Call) and "assign_to" in ast.unparse(n.func)]
	la("không gọi assign_to", goi, [])
	# ToDo ghi qua đúng một hàm, và giao() gọi hàm đó.
	ham = [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "_them_viec"]
	la("có _them_viec", len(ham), 1)
	g = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "giao")
	dung("giao() ghi qua _them_viec", any(isinstance(n, ast.Call) and ast.unparse(n.func) == "_them_viec" for n in ast.walk(g)))
