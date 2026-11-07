"""v644: Đọc lại thư gốc / đọc lại nguồn hỏng khi tệp không in dòng tổng.

Site thật 07/11/2026 sau deploy v643: bấm Đọc lại thư gốc nguồn ShopeeFood
DSN-2611-06355 báo "Column 'tong_tep' cannot be null". Lần nhận đầu đi qua
insert (Frappe tự đổi None thành 0 cho ô số) nên không lộ; đọc lại một nguồn
có sẵn ghi bằng db_set (câu UPDATE thẳng) mà cột số là NOT NULL.

Ca cũ thu_doi_soat_khop_579 "đọc lại nguồn lỗi chuyển dòng bản cũ thành Đã
thay" đã chạy đúng đường này với kết quả không có dòng tổng, nhưng db_set giả
nhận None im lặng nên che lỗi. Ca dưới đây chạy cùng đường và soi chính
những gì db_set nhận, đối chiếu với kiểu ô trong JSON doctype.
"""
import json
import os
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la

_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "vagabond", "doctype",
	"vagabond_doi_soat_nguon", "vagabond_doi_soat_nguon.json")


def _o_so_json():
	with open(_JSON, encoding="utf-8") as f:
		return {x["fieldname"] for x in json.load(f)["fields"]
			if x.get("fieldtype") in ("Int", "Float", "Currency", "Percent", "Check")}


@ca("v644: danh sách ô số của Nguồn đối soát đọc đúng từ JSON doctype, có tổng trên tệp")
def _():
	from vagabond import doi_soat_vendor as V

	la("trùng tuyệt đối ô số trong JSON", set(V.o_so_nguon()), _o_so_json())
	dung("có tổng trên tệp và các ô tiền", {"tong_tep", "tien_hang", "phi", "thuc_nhan", "so_dong"} <= set(V.o_so_nguon()))


@ca("v644: ô số rỗng về 0, ô chữ và ngày rỗng giữ nguyên, số 0 giữ nguyên")
def _():
	from vagabond import doi_soat_vendor as V

	ra = V.so_khong_rong(dict(tong_tep=None, phi=0, thuc_nhan=5, ngay_tien_ve=None, communication=None),
		{"tong_tep", "phi", "thuc_nhan"})
	la("kết quả", ra, dict(tong_tep=0, phi=0, thuc_nhan=5, ngay_tien_ve=None, communication=None))


def _doc_lai(kq):
	"""Chạy đúng _ghi_nguon(co_san=...) như nút Đọc lại thư gốc, trả dict db_set nhận."""
	from vagabond import doi_soat_vendor as V

	viec = []
	nguon = NS(name="N1", trang_thai="Cần xử lý", db_set=lambda d: viec.append(d), reload=lambda: None)

	def xem_truoc(kq, ct, dn=None):
		return dict(so=dict(moi=0, trung=0, loi=0), loi=[], canh_bao=[], trang_thai="Đã nhận",
			tong=dict(tien_hang=4561287, phi=671879, thuc_nhan=3889408), dong=[])
	with patch.object(V.frappe.db, "sql", lambda *a, **k: [], create=True), \
			patch.object(V.frappe.db, "count", lambda *a, **k: 0, create=True), \
			patch.object(V.frappe.db, "get_value", lambda *a, **k: {"du_lieu": "{}", "so_dong": 17, "thuc_nhan": 3178363,
				"name": "N1", "duong_vao": "Từ thư", "kenh_nhan": "Hộp thư đối soát"}, create=True), \
			patch.object(V.frappe.db, "delete", lambda *a, **k: None, create=True), \
			patch.object(V.frappe.db, "savepoint", lambda n: None, create=True), \
			patch.object(V.frappe, "get_doc", lambda *a, **k: nguon, create=True), \
			patch.object(V.frappe.utils, "now", lambda: "2026-11-07 18:06:17", create=True), \
			patch.object(V, "_da_nhan", lambda ct, kq: {}), patch.object(V.khop, "xem_truoc", xem_truoc), \
			patch.object(V, "da_tu_choi_khoa", lambda *a, **k: False), \
			patch.object(V, "_doi_chieu", lambda n: None):
		V._ghi_nguon("CT", dict(ten="Shopeefood_06-11-2026.csv", sha256="s"), kq, None, "Hộp thư đối soát",
			"/private/files/x.csv", None, co_san="N1", them={"duong_vao": "Từ thư"})
	return viec[0]


@ca("v644: Đọc lại thư gốc nguồn ShopeeFood (tệp không in dòng tổng) không ghi ô số rỗng vào cơ sở dữ liệu")
def _():
	from vagabond import doi_soat_mau as Mau
	from vagabond import doi_soat_vendor as V

	kq = Mau.ket_qua("shopeefood", "tien_ban", "ShopeeFood", "SHOPEEFOOD")
	dung("tệp ShopeeFood không có dòng tổng", not (kq.get("tong") or {}).get("thuc_nhan"))
	ghi = _doc_lai(kq)
	rong = sorted(k for k in _o_so_json() if k in ghi and ghi[k] is None)
	la("không ô số nào mang None (cột NOT NULL)", rong, [])
	la("tổng trên tệp ghi 0 như lúc nhận lần đầu", ghi.get("tong_tep"), 0)
	la("số mới vẫn ghi đủ", (ghi["tien_hang"], ghi["phi"], ghi["thuc_nhan"]), (4561287, 671879, 3889408))
	dung("không ghi lại mã băm và công ty", "sha256" not in ghi and "company" not in ghi)
	dung("lối ghi lại dùng một cửa", V.so_khong_rong.__name__ in __import__("inspect").getsource(V._ghi_nguon))


@ca("v644: tệp CÓ in dòng tổng thì đọc lại vẫn ghi đúng tổng trên tệp")
def _():
	from vagabond import doi_soat_mau as Mau

	kq = Mau.ket_qua("grabfood", "tien_ban", "GrabFood", "GRABFOOD:X")
	kq["tong"] = dict(thuc_nhan=668915)
	la("tổng trên tệp", _doc_lai(kq).get("tong_tep"), 668915)
