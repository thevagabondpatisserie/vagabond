"""v643 bench: hộp thư đối soát trên ERPNext thật.

Tầng khung đã kiểm các phép thuần (bù ô Sender, giờ nhận, chặng đăng nhập,
đơn vị ShopeeFood) và đường _xu_ly với Frappe giả. Ở đây chứng minh trên site
dựng thật: ô Cài đặt mới có sau migrate và đã gieo, thư chuyển tiếp từ
account@ bị chặn khi Cài đặt chưa khai hộp nội bộ rồi bấm Kiểm lại thư (đúng
cửa doc_lai_thu, khoá get_lock, tệp .eml đã cất) thì nhận, và tệp ShopeeFood
ghi đồng trong thư vào thành nguồn Từ thư đúng số tiền.

Mã đơn trong thư mẫu đổi theo lượt chạy để mã băm tệp không trùng.
"""
import base64
from pathlib import Path
from unittest.mock import patch

import frappe

from vagabond import doi_soat_thu as dst
from vagabond import doi_soat_vendor as dv
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen

THU = Path(__file__).resolve().parents[1] / "kiem_thu" / "mau_doi_soat" / "dkim"


@ca("v643 bench: ô Hộp thư nội bộ được chuyển tiếp có trên Cài đặt lõi sau migrate, đã gieo hai địa chỉ, không ghi lỗi")
def _():
	dung("có ô", frappe.get_meta(dst.CAI_DAT).has_field("ds_thu_noi_bo"))
	la("cấu hình đọc được hai địa chỉ mặc định", dst.cau_hinh()["noi_bo"], list(dst.NOI_BO_MAC_DINH))
	la("không có lỗi gieo", frappe.db.count("Error Log", {"method": "Đối soát hộp thư: gieo hộp thư nội bộ"}), 0)


def _thu_account():
	"""Thư account@ mẫu, CSV ShopeeFood ghi đồng, mã đơn đổi theo lượt."""
	goc = (THU / "noi_bo_account.eml").read_bytes()
	dau, than = goc.split(b"\r\n\r\n", 1)
	cu = than.split(b"Content-Transfer-Encoding: base64\r\n\r\n", 1)[1].split(b"\r\n--NB643--", 1)[0]
	csv = base64.b64decode(cu)
	duoi = frappe.generate_hash(length=6)
	csv = csv.replace(b"06116-900000001", ("06116-6431%s" % duoi).encode()).replace(b"06116-900000007",
		("06116-6437%s" % duoi).encode())
	return goc.replace(cu, base64.b64encode(csv)).replace(b"<nb643@mail.example>", ("<nb643-%s@mail.example>" % duoi).encode())


@ca("v643 bench: thư account@ bị chặn khi chưa khai hộp nội bộ; Kiểm lại thư thì nhận, ShopeeFood ghi đồng vào đúng tiền")
def _():
	cty, _tk, _mau = _nen()
	tho = _thu_account()
	ch = dst.cau_hinh()
	with patch.object(dv, "_cong_ty", return_value=cty):
		ten = dst._xu_ly(tho, "643", dict(ch, noi_bo=[]))
	_DA_TAO.append((dst.DT_THU, ten))
	t = frappe.db.get_value(dst.DT_THU, ten, ["ket_qua", "xong", "tep_goc"], as_dict=True)
	la("chưa khai: bị chặn, đã xong, cất bản gốc", (t.ket_qua, t.xong, bool(t.tep_goc)), (dst.KQ_CHAN, 1, True))
	with patch.object(dv, "_cong_ty", return_value=cty):
		r = dst.doc_lai_thu(ten)
	la("Kiểm lại thư theo Cài đặt hiện tại: nhận", r.ket_qua, dst.KQ_XAC_THUC)
	t = frappe.db.get_value(dst.DT_THU, ten, ["doi_tac", "ky_boi", "ly_do"], as_dict=True)
	la("sổ thư ghi chuyển tiếp nội bộ, không ghi chữ ký số", (t.doi_tac, t.ky_boi or ""), (dst.NGUON_NOI_BO, ""))
	dung("lý do nói có đăng nhập", "có đăng nhập" in (t.ly_do or ""))
	ng = frappe.get_all(dst.DT_NGUON, filters={"thu": ten}, fields=["name", "vendor", "duong_vao", "so_dong", "thuc_nhan",
		"trang_thai", "du_lieu"])
	for x in ng:
		_DA_TAO.append((dst.DT_NGUON, x.name))
	la("một nguồn ShopeeFood đường Từ thư", [(x.vendor, x.duong_vao) for x in ng], [("ShopeeFood", dst.DV_THU)])
	la("hai đơn, thực nhận theo đồng", (int(ng[0].so_dong), int(ng[0].thuc_nhan)) if ng else None, (2, 115967 + 711045))
	dung("ghi chú đơn vị nói đồng", bool(ng) and "theo đồng" in (ng[0].du_lieu or ""))
