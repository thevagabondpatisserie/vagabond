# -*- coding: utf-8 -*-
"""Bảng BTP bánh ổ giả cho ca kiểm (v653).

Từ v653 btp.py không còn lưu cả bảng Single: mọi cửa khoá đúng dòng bằng
`select ... for update`, ghi bằng UPDATE một dòng, thêm dòng bằng db_insert,
và ghi Nhật ký BTP. Bản giả này chạy ĐÚNG các câu đó trên một danh sách dòng
(dict truy cập bằng dấu chấm), để ca kiểm gọi hàm THẬT của btp.py, kiem_banh.py
mà không dò chuỗi. Câu SQL lạ đi tiếp xuống hàm sql đang có (của ca gọi).

Dùng:
    with BangBTP(cua.btp.dong) as b:
        kiem_banh.luu_o(...)
    b.nhat_ky   # các dòng Nhật ký BTP đã ghi
    b.moc       # các lần đổi mốc "BTP bếp cập nhật"
"""

import re
import unittest.mock as um

import frappe

from vagabond.khung.kiem_thu.nen import Doi


class BangBTP(object):
	def __init__(self, dong, nguoi="kiemthu@vagabond"):
		self.dong = dong
		self.nhat_ky = []
		self.moc = []
		self.cau = []
		self.nguoi = nguoi
		self._p = []

	# ------------------------------------------------------------ SQL
	def _ten(self, d):
		if not d.get("name"):
			d["name"] = "btp-" + str(d.get("ma_hang"))
		return d["name"]

	def sql(self, cau, gt=None, *a, **k):
		q = " ".join(str(cau).split())
		ql = q.lower()
		self.cau.append((q, gt))
		if "`tabbtp banh o dong`" not in ql and "`tabnhat ky btp`" not in ql:
			return self._goc(cau, gt, *a, **k)
		if ql.startswith("select ma_hang, so_btp, so_decor, ten_banh from `tabbtp banh o dong`"):
			can = set(gt["ma"])
			return [(d.ma_hang, d.get("so_btp"), d.get("so_decor"), d.get("ten_banh")) for d in self.dong if d.ma_hang in can]
		if ql.startswith("select ma_hang from `tabbtp banh o dong`"):
			can = set(gt["ma"])
			return [(d.ma_hang,) for d in self.dong if d.ma_hang in can]
		if ql.startswith("select name, ma_hang, ten_banh, so_btp"):
			for d in self.dong:
				if d.ma_hang == gt["ma"]:
					self._ten(d)
					return [Doi({x: d.get(x) for x in ("name", "ma_hang", "ten_banh", "so_btp", "so_decor", "decor_da_lam",
						"so_refill", "refill_tu", "refill_den")})]
			return []
		if ql.startswith("select ifnull(max(idx), 0)"):
			return [(len(self.dong),)]
		if ql.startswith("update `tabbtp banh o dong` set so_btp = ifnull(so_btp, 0) -"):
			for d in self.dong:
				if d.ma_hang == gt["ma"]:
					d["so_btp"] = (d.get("so_btp") or 0) - gt["n"]
					d["so_decor"] = (d.get("so_decor") or 0) - gt["n"]
					d["decor_da_lam"] = (d.get("decor_da_lam") or 0) + gt["n"]
			return []
		if ql.startswith("update `tabbtp banh o dong` set `"):
			cot = re.findall(r"`(\w+)` = %\((\w+)\)s", q)
			for d in self.dong:
				if self._ten(d) == gt["ten"]:
					for c, k2 in cot:
						d[c] = gt[k2]
			return []
		if ql.startswith("delete from `tabbtp banh o dong`"):
			self.dong[:] = [d for d in self.dong if self._ten(d) != gt["ten"]]
			return []
		if "from `tabnhat ky btp` n join" in ql:
			moi = {}
			for r in self.nhat_ky:
				if r["ma_hang"] in gt["ma"] and r["truong"] in gt["o"]:
					moi[(r["ma_hang"], r["truong"])] = r
			return [Doi(v) for v in moi.values()]
		raise AssertionError("bảng BTP giả chưa hiểu câu: " + q)

	# ------------------------------------------------------------ new_doc
	def new_doc(self, dt_, *a, **k):
		if dt_ == "Nhat Ky BTP":
			return _Ghi(self.nhat_ky, {"doctype": dt_})
		if dt_ == "BTP Banh O Dong":
			return _Them(self.dong, {"doctype": dt_})
		return self._new_doc(dt_, *a, **k)

	def __enter__(self):
		self._goc = frappe.db.sql
		self._new_doc = getattr(frappe, "new_doc", lambda *a, **k: Doi())
		self._p = [
			um.patch.object(frappe.db, "sql", self.sql, create=True),
			um.patch.object(frappe.db, "set_single_value", lambda *a, **k: self.moc.append(a[1]), create=True),
			um.patch.object(frappe.db, "commit", lambda *a, **k: None, create=True),
			um.patch.object(frappe, "new_doc", self.new_doc, create=True),
			um.patch.object(frappe, "generate_hash", lambda *a, **k: "hash1", create=True),
			um.patch.object(frappe.session, "user", self.nguoi),
		]
		for p in self._p:
			p.start()
		return self

	def __exit__(self, *a):
		for p in reversed(self._p):
			p.stop()
		return False


class _Ghi(object):
	def __init__(self, kho, v):
		self.kho, self.v = kho, dict(v)
		self.flags = Doi()
		self.name = "NK-%d" % (len(kho) + 1)

	def update(self, x):
		self.v.update(x)

	def insert(self, **k):
		self.kho.append(dict(self.v, name=self.name))
		return self


class _Them(object):
	def __init__(self, kho, v):
		self.kho, self.v = kho, dict(v)
		self.name = None

	def update(self, x):
		self.v.update(x)
		self.name = "btp-" + str(self.v.get("ma_hang"))

	def db_insert(self, *a, **k):
		self.kho.append(Doi(dict(self.v, name=self.name)))
		return self
