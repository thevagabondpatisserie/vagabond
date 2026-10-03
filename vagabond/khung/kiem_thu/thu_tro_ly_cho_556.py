# -*- coding: utf-8 -*-
"""v556: trợ lý chờ mô hình đủ lâu, quá giờ thì báo câu dễ hiểu.

03/10/2026 anh Việt hỏi "Quy trình hoàn tiền cho khách?" hai lần, cả hai
nhận "Lỗi máy chủ (mã 500)". Error Log trên site: ReadTimeout tới
api.anthropic.com, read timeout=12. Trợ lý dùng TIMEOUT chung 12 giây của
lib (đặt cho API ngắn), mà từ v554 tư liệu sổ tay dài hơn nên câu trả lời
hay quá 12 giây, lỗi mạng lọt ra thành 500.

Ca dưới nạp THẬT vagabond/tro_ly.py với requests, lib giả (CI không có
requests), rồi gọi đúng hàm gọi mô hình. Không gọi thêm hàm nào khác.
"""

import importlib.util
import os
import sys
import types

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la
from vagabond.khung.kiem_thu.thu_tro_ly import GOI


class _HetGio(Exception):
	pass


class _MatMang(Exception):
	pass


def _nap(post):
	"""Nạp tro_ly.py với requests giả có hàm post cho trước."""
	fr = gia_lap()
	rq = types.ModuleType("requests")
	rq.Timeout = _HetGio
	rq.ConnectionError = _MatMang
	rq.post = post
	lib = types.ModuleType("vagabond.lib")
	lib.TIMEOUT = 12
	lib.cfg = lambda: {}
	lib.key = lambda c, k: "khoa-gia"
	vch = types.ModuleType("vagabond.vai_cua_hang")
	vch.VAI_QLCH = "Quản lý cửa hàng"
	cu = {k: sys.modules.get(k) for k in ("requests", "vagabond.lib", "vagabond.vai_cua_hang")}
	sys.modules.update({"requests": rq, "vagabond.lib": lib, "vagabond.vai_cua_hang": vch})
	try:
		sp = importlib.util.spec_from_file_location("tro_ly_thu_556", os.path.join(GOI, "tro_ly.py"))
		m = importlib.util.module_from_spec(sp)
		sp.loader.exec_module(m)
	finally:
		for k, v in cu.items():
			if v is None:
				sys.modules.pop(k, None)
			else:
				sys.modules[k] = v
	return m, fr


def _goi(m):
	return m._goi_mo_hinh({"tro_ly_mo_hinh": "mo-hinh-gia"}, "Quy trình hoàn tiền cho khách?", "tư liệu", None)


@ca("v556: trợ lý chờ mô hình lâu hơn 12 giây chung, dưới trần 120 giây của máy web")
def _cho_du_lau():
	da = {}

	def post(*a, **k):
		da["timeout"] = k.get("timeout")

		class R:
			status_code = 200

			def json(self):
				return {"content": [{"type": "text", "text": "Có ba trường hợp hoàn tiền"}]}
		return R()

	m, _ = _nap(post)
	tra_loi, _mh = _goi(m)
	la("câu trả lời đi qua", tra_loi, "Có ba trường hợp hoàn tiền")
	dung("chờ ít nhất 30 giây", (da["timeout"] or 0) >= 30)
	dung("chờ dưới 120 giây", (da["timeout"] or 999) < 120)


@ca("v556: mô hình quá giờ hay mất mạng thì báo câu tiếng Việt, không lọt lỗi 500")
def _qua_gio_bao_de_hieu():
	for loi in (_HetGio, _MatMang):
		def post(*a, **k):
			raise loi("Read timed out. (read timeout=12)")
		m, fr = _nap(post)
		try:
			_goi(m)
			dung("phải dừng khi %s" % loi.__name__, False)
		except fr.ValidationError as e:
			dung("câu báo nói trả lời quá lâu (%s)" % loi.__name__, "quá lâu" in str(e))
			dung("câu báo chỉ cách gỡ (%s)" % loi.__name__, "Gửi lại" in str(e) and "Sổ tay" in str(e))
		except Exception as e:  # lỗi thô lọt ra thành 500
			dung("lọt lỗi thô %s" % type(e).__name__, False)
