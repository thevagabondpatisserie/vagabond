# -*- coding: utf-8 -*-
"""v684 (anh Việt 22/11/2026): tin Zalo xác nhận đơn đặt bánh trên web.

Chốt: giờ gửi theo luật Zalo; một đơn một tin; khoá Đang gửi trước khi gọi Zalo
và không gửi lại lượt đã chết; đọc bộ tham số từ chính mẫu đã duyệt; nút mang
đúng token biên nhận của đơn, token cất mã hoá và xoá sau khi xong; chưa khai mã
mẫu thì không làm gì; tao_don THẬT gọi xếp tin đúng lúc Pancake nhận đơn.
"""

import contextlib
import json
import sys
import types
from datetime import datetime, timedelta

from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la

SNAP = {"nguoi_dat": {"ho_ten": "Nguyễn Văn An", "dien_thoai": "0901234567"}, "ngay_nhan": "2026-11-24 14:00",
	"tu_lay": False, "phi": {"trang_thai": "chinh_xac", "phi_khach": 36000}, "mon": []}


@ca("v684 tin xác nhận đơn, phần thuần: giờ gửi 6h tới 22h, chữ trạng thái thanh toán, lý do không gửi, lượt treo")
def _():
	from vagabond import tin_xac_nhan_don as t
	la("giờ", [t.trong_gio(datetime(2026, 11, 22, h, m)) for h, m in ((5, 59), (6, 0), (21, 59), (22, 0), (23, 30))],
		[False, True, True, False, False])
	la("trạng thái", [t.nhan_thanh_toan(x) for x in ("", None, "Thu thieu", "Da thu", "la")],
		["Chờ thanh toán", "Chờ thanh toán", "Đã trả một phần", "Đã thanh toán", "Chờ thanh toán"])
	la("lý do", [t.ly_do_bo({"trang_thai": "Da huy"}, "849", True, True), t.ly_do_bo({}, "849", False, True),
		t.ly_do_bo({}, "", True, True), t.ly_do_bo({}, "849", True, False), t.ly_do_bo({"trang_thai": "Da nhan"}, "849", True, True)],
		["Đơn đã huỷ trước khi tới giờ gửi.", "Chưa khai mã mẫu Zalo xác nhận đơn ở Cài đặt.",
			"Đơn không có số điện thoại hợp lệ.", "Không còn đường dẫn biên nhận của đơn để gắn vào nút.", ""])
	b = datetime(2026, 11, 22, 10, 0)
	la("treo", [t.treo(b - timedelta(minutes=29), b), t.treo(b - timedelta(minutes=31), b), t.treo(None, b)], [False, True, True])


@ca("v684 tin xác nhận đơn: giá trị điền mẫu lấy từ MỘT nguồn với biên nhận (ngày nhận, cách nhận) và số thu online; nút mang token")
def _():
	from vagabond import don_web, tin_xac_nhan_don as t
	from vagabond import thanh_toan_web_thuan as ttt
	bg = {"name": "DW-2611-00123", "pancake_display_id": "91500", "tien_banh": 900000, "trang_thai_phi": "chinh_xac",
		"thanh_toan": "bank", "trang_thai": "Da nhan", "vgb_tt_trang_thai": ""}
	tom = don_web.tom_tat_bien_nhan(bg, SNAP)
	g = t.gia_tri(bg, SNAP, tom, "T" * 43)
	la("giá trị", g, {"ten_khach": "Nguyễn Văn An", "ma_don": "91500", "ngay_nhan": " ".join(x for x in (tom["ngay_nhan"], tom["khung_gio"]) if x),
		"cach_nhan": tom["cach_nhan"], "so_tien": int(ttt.tien_ban_ghi(bg, SNAP)["online"]), "trang_thai": "Chờ thanh toán", "ma_xem": "T" * 43})
	la("số tiền là tiền bánh cộng phí", g["so_tien"], 936000)
	chua_ro = dict(SNAP, phi={"trang_thai": "chua_ro"})
	la("phí chưa rõ: số thu online là tiền bánh", t.gia_tri(dict(bg, trang_thai_phi="chua_ro"), chua_ro, tom, "x")["so_tien"], 900000)
	la("chưa có mã Pancake thì mã yêu cầu", t.gia_tri(dict(bg, pancake_display_id=""), SNAP, tom, "x")["ma_don"], "DW-2611-00123")


@ca("v684 tin xác nhận đơn: ô mới neo đúng chỗ có thật (sau cước GreenSM trên Don Web, sau mã mẫu OTP trong Cài đặt), có hàm quét 5 phút")
def _():
	import os
	from vagabond import don_quay, tin_xac_nhan_don as t
	dw = [f["fieldname"] for f in don_quay.TRUONG_MOI["Vagabond Don Web"]]
	la("neo Don Web", t.TRUONG_MOI["Vagabond Don Web"][0]["insert_after"] in dw, True)
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	js = json.load(open(os.path.join(goc, "vagabond", "doctype", "vagabond_settings", "vagabond_settings.json"), encoding="utf-8"))
	la("neo Cài đặt", t.TRUONG_MOI["Vagabond Settings"][0]["insert_after"] in [f.get("fieldname") for f in js["fields"]], True)
	hk = open(os.path.join(goc, "hooks.py"), encoding="utf-8").read()
	dung("lịch 5 phút", '"vagabond.tin_xac_nhan_don.quet"' in hk)
	tt = open(os.path.join(goc, "truong_tu_them.py"), encoding="utf-8").read()
	dung("dựng ô sau nhóm don_quay", tt.index("tin_xac_nhan_don.TRUONG_MOI") > tt.index("don_quay.TRUONG_MOI"))


class _Db(object):
	"""Bảng Don Web giả: get_value, set_value, sql for update, get_all theo bộ lọc đơn giản."""

	def __init__(self, rows):
		self.rows = rows
		self.commit_n = 0

	def get_value(self, dt, ten, truong):
		return (self.rows.get(ten) or {}).get(truong)

	def set_value(self, dt, ten, gt, update_modified=True):
		self.rows[ten].update(gt)

	def sql(self, q, args=(), as_dict=False):
		r = self.rows.get(args[0])
		return [Doi(dict(r))] if r else []

	def commit(self):
		self.commit_n += 1

	def rollback(self):
		pass


@contextlib.contextmanager
def _moi_truong(rows, mau="701234", gio=datetime(2026, 11, 22, 10, 0), tham_so=None, tra_zalo=None, doc_ok=True):
	import frappe
	from vagabond import tin_xac_nhan_don as t, zalo
	import vagabond.lib as lib

	vet = types.SimpleNamespace(gui=[], enq=[], auth={}, log=[])
	db = _Db(rows)
	pw = types.ModuleType("frappe.utils.password")
	pw.set_encrypted_password = lambda dt, ten, v, f: vet.auth.__setitem__((ten, f), v)
	pw.get_decrypted_password = lambda dt, ten, f, raise_exception=True: vet.auth.get((ten, f))
	pw.remove_encrypted_password = lambda dt, ten, f: vet.auth.pop((ten, f), None)

	def get_all(dt, filters=None, fields=None, order_by=None, limit_page_length=0):
		ra = []
		for ten, r in rows.items():
			ok = True
			for k, v in (filters or {}).items():
				if isinstance(v, list):
					ok = ok and r.get(k) is not None and r.get(k) < v[1]
				else:
					ok = ok and r.get(k) == v
			if ok:
				ra.append(Doi(dict(r, name=ten)))
		return ra

	ts = tham_so if tham_so is not None else [{"name": n, "type": "STRING", "maxLength": 50, "require": True}
		for n in ("ten_khach", "ma_don", "ngay_nhan", "cach_nhan", "trang_thai", "ma_xem")] + [
		{"name": "so_tien", "type": "CURRENCY", "maxLength": 20, "require": True}]
	cu = {"db": getattr(frappe, "db", None), "enqueue": getattr(frappe, "enqueue", None), "get_all": frappe.get_all,
		"log_error": frappe.log_error, "pw": sys.modules.get("frappe.utils.password"), "bay_gio": t._bay_gio,
		"cfg": lib.cfg, "doc_mau": zalo.doc_mau, "gui_mau": zalo.gui_mau, "token_cua": None}
	from vagabond import don_web
	cu["token_cua"] = don_web.token_cua
	frappe.db = db
	frappe.enqueue = lambda *a, **k: vet.enq.append(k.get("ten"))
	frappe.get_all = get_all
	frappe.log_error = lambda *a, **k: vet.log.append(a)
	frappe.get_traceback = getattr(frappe, "get_traceback", lambda: "")
	sys.modules["frappe.utils.password"] = pw
	t._bay_gio = lambda: gio
	lib.cfg = lambda: {"zns_template_xac_nhan_don": mau}
	zalo.doc_mau = lambda m: {"ok": 1, "tham_so": ts} if doc_ok else {"ok": 0, "loi": "mất mạng"}

	def gui_mau(c, so, m, data, dau):
		vet.gui.append({"so": so, "mau": m, "data": data, "dau": dau, "tt_luc_goi": dict(rows)[dau[7:]].get("vgb_zxn")})
		return tra_zalo or {"error": 0, "data": {"msg_id": "x"}}
	zalo.gui_mau = gui_mau
	don_web.token_cua = lambda bg, nonce: "TOK-" + nonce
	try:
		yield vet, db
	finally:
		frappe.db, frappe.enqueue, frappe.get_all, frappe.log_error = cu["db"], cu["enqueue"], cu["get_all"], cu["log_error"]
		if cu["pw"] is None:
			sys.modules.pop("frappe.utils.password", None)
		else:
			sys.modules["frappe.utils.password"] = cu["pw"]
		t._bay_gio, lib.cfg, zalo.doc_mau, zalo.gui_mau = cu["bay_gio"], cu["cfg"], cu["doc_mau"], cu["gui_mau"]
		don_web.token_cua = cu["token_cua"]


def _dong(**k):
	r = {"vgb_zxn": None, "trang_thai": "Da nhan", "dien_thoai": "0901234567", "snapshot": json.dumps(SNAP),
		"pancake_display_id": "91500", "vgb_tt_trang_thai": "", "thanh_toan": "bank", "tien_banh": 900000,
		"trang_thai_phi": "chinh_xac", "creation": datetime(2026, 11, 22, 9, 0)}
	r.update(k)
	return r


@ca("v684 tin xác nhận đơn: xếp một lần, cất token mã hoá, gửi đúng số, đúng mẫu, nút mang token; xong thì xoá token; gửi lại lần hai không gửi")
def _():
	from vagabond import tin_xac_nhan_don as t
	rows = {"DW-1": _dong()}
	with _moi_truong(rows) as (vet, db):
		la("xếp", t.xep(Doi(name="DW-1"), "n1"), True)
		la("trạng thái chờ, token mã hoá", (rows["DW-1"]["vgb_zxn"], vet.auth.get(("DW-1", "vgb_zxn_ma")), vet.enq), ("Cho gui", "TOK-n1", ["DW-1"]))
		la("xếp lại (khách bấm trùng)", t.xep(Doi(name="DW-1"), "n1"), False)
		la("gửi", t.gui("DW-1"), "da_gui")
		g = vet.gui[0]
		la("số, mẫu, khoá chống trùng", (g["so"], g["mau"], g["dau"]), ("84901234567", "701234", "vgb-xn-DW-1"))
		la("dòng đã khoá Đang gửi trước khi gọi Zalo", g["tt_luc_goi"], "Dang gui")
		la("nút mang token, tiền là chữ số", (g["data"]["ma_xem"], g["data"]["so_tien"], g["data"]["trang_thai"]), ("TOK-n1", "936000", "Chờ thanh toán"))
		la("xong: Đã gửi, xoá token", (rows["DW-1"]["vgb_zxn"], ("DW-1", "vgb_zxn_ma") in vet.auth), ("Da gui", False))
		la("gửi lần hai", t.gui("DW-1"), "khong_cho")
		la("chỉ một tin", len(vet.gui), 1)


@ca("v684 tin xác nhận đơn: chưa khai mã mẫu thì không cất token, không xếp; ngoài giờ thì chờ; đơn huỷ thì bỏ; Zalo từ chối thì Lỗi và xoá token")
def _():
	from vagabond import tin_xac_nhan_don as t
	rows = {"DW-1": _dong()}
	with _moi_truong(rows, mau="") as (vet, db):
		la("không mẫu", (t.xep(Doi(name="DW-1"), "n1"), vet.auth, rows["DW-1"]["vgb_zxn"]), (False, {}, None))
	rows = {"DW-2": _dong()}
	with _moi_truong(rows, gio=datetime(2026, 11, 22, 23, 10)) as (vet, db):
		t.xep(Doi(name="DW-2"), "n2")
		la("23h10: chưa gửi", (t.gui("DW-2"), t.quet(), vet.gui, rows["DW-2"]["vgb_zxn"]), ("ngoai_gio", 0, [], "Cho gui"))
	with _moi_truong(rows, gio=datetime(2026, 11, 23, 6, 5)) as (vet, db):
		vet.auth[("DW-2", "vgb_zxn_ma")] = "TOK-n2"
		rows["DW-2"]["vgb_tt_trang_thai"] = "Da thu"
		la("6h05: nhịp quét gửi, trạng thái đọc lúc gửi", (t.quet(), vet.gui[0]["data"]["trang_thai"]), (1, "Đã thanh toán"))
	rows = {"DW-3": _dong(trang_thai="Da huy", vgb_zxn="Cho gui")}
	with _moi_truong(rows) as (vet, db):
		vet.auth[("DW-3", "vgb_zxn_ma")] = "TOK"
		la("đơn huỷ", (t.gui("DW-3"), rows["DW-3"]["vgb_zxn"], vet.gui, vet.auth), ("bo", "Bo qua", [], {}))
	rows = {"DW-4": _dong(vgb_zxn="Cho gui")}
	with _moi_truong(rows, tra_zalo={"error": -108, "message": "Phone number invalid"}) as (vet, db):
		vet.auth[("DW-4", "vgb_zxn_ma")] = "TOK"
		la("Zalo từ chối", (t.gui("DW-4"), rows["DW-4"]["vgb_zxn"], vet.auth), ("loi", "Loi", {}))
		dung("lý do có mã lỗi", "-108" in rows["DW-4"]["vgb_zxn_loi"])


@ca("v684 tin xác nhận đơn: không đọc được mẫu thì CHƯA gửi, giữ Chờ gửi và token; mẫu đòi tham số lạ thì Lỗi; lượt Đang gửi chết không gửi lại; chờ quá 3 ngày thì bỏ")
def _():
	from vagabond import tin_xac_nhan_don as t
	rows = {"DW-5": _dong(vgb_zxn="Cho gui")}
	with _moi_truong(rows, doc_ok=False) as (vet, db):
		vet.auth[("DW-5", "vgb_zxn_ma")] = "TOK"
		la("đọc mẫu hỏng", (t.gui("DW-5"), rows["DW-5"]["vgb_zxn"], vet.gui, ("DW-5", "vgb_zxn_ma") in vet.auth), ("cho", "Cho gui", [], True))
	rows = {"DW-6": _dong(vgb_zxn="Cho gui")}
	with _moi_truong(rows, tham_so=[{"name": "ma_khuyen_mai", "type": "STRING", "maxLength": 20, "require": True}]) as (vet, db):
		vet.auth[("DW-6", "vgb_zxn_ma")] = "TOK"
		la("tham số lạ", (t.gui("DW-6"), rows["DW-6"]["vgb_zxn"], vet.gui), ("loi", "Loi", []))
	gio = datetime(2026, 11, 22, 10, 0)
	rows = {"DW-7": _dong(vgb_zxn="Dang gui", vgb_zxn_luc=gio - timedelta(minutes=45)),
		"DW-8": _dong(vgb_zxn="Dang gui", vgb_zxn_luc=gio - timedelta(minutes=5)),
		"DW-9": _dong(vgb_zxn="Cho gui", creation=gio - timedelta(days=4))}
	with _moi_truong(rows, gio=gio) as (vet, db):
		t.quet()
		la("treo 45 phút: Lỗi, không gửi lại", (rows["DW-7"]["vgb_zxn"], vet.gui), ("Loi", []))
		la("đang gửi 5 phút: để yên", rows["DW-8"]["vgb_zxn"], "Dang gui")
		la("chờ 4 ngày: bỏ", rows["DW-9"]["vgb_zxn"], "Bo qua")


@ca("v684 tao_don THẬT: Pancake nhận đơn thì xếp tin xác nhận đúng một lần với nonce của lần gửi; Pancake từ chối thì không")
def _():
	from vagabond import tin_xac_nhan_don as t
	from vagabond.khung.kiem_thu.thu_don_web_367 import _Tra, _don, _moi_truong_tao_don
	goi = []
	cu = t.xep
	t.xep = lambda bg, nonce: goi.append((bg.name, nonce)) or True
	try:
		vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "1"}}))
		d = _don()
		la("đơn thành", tao_don(d).get("ok"), 1)
		la("xếp một lần, đúng nonce", goi, [("DW-2609-00001", "N" * 24)])
		del goi[:]
		vet2, tao_don2 = _moi_truong_tao_don(lambda v: _Tra(400, {"success": False, "message": "từ chối"}))
		tao_don2(_don())
		la("Pancake từ chối: không xếp", goi, [])
	finally:
		t.xep = cu
