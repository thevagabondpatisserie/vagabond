# -*- coding: utf-8 -*-
"""Ca kiểm cho bước xử lý của hoá đơn mua hiện trên màn danh sách."""

import io
import os

from vagabond import buoc_hoa_don_mua as B
from vagabond.khung.kiem_thu.nen import ca, dung


def _doc(duong):
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	return io.open(os.path.join(os.path.dirname(goc), duong), encoding="utf-8").read()


def _d(ma="", pnk="", kho=1):
	return {"item_code": ma, "purchase_receipt": pnk, "qua_kho": kho}


@ca("bước hoá đơn mua: thiếu mã hàng chặn hết các bước sau")
def _thieu_ma():
	dung("một dòng trống mã là thiếu mã hàng",
		B.buoc_cua_to([_d("NVL1", "PNK-1"), _d("")]) == B.B_THIEU_MA)
	dung("thiếu mã thì xét trước cả lệch hoá đơn điện tử",
		B.buoc_cua_to([_d("")], lech_hddt=1) == B.B_THIEU_MA)
	dung("đủ mã thì không còn là thiếu mã",
		B.buoc_cua_to([_d("NVL1", "PNK-1")]) != B.B_THIEU_MA)


@ca("bước hoá đơn mua: lệch hoá đơn điện tử xét trước bước nối phiếu")
def _lech():
	dung("đủ mã mà lệch thì báo lệch",
		B.buoc_cua_to([_d("NVL1", "")], lech_hddt=1) == B.B_LECH_HDDT)
	dung("hết lệch thì mới xuống bước nối phiếu",
		B.buoc_cua_to([_d("NVL1", "")], lech_hddt=0) == B.B_CHUA_NOI)


@ca("bước hoá đơn mua: dòng không qua kho không bao giờ tính là thiếu phiếu")
def _khong_qua_kho():
	"""Đây đúng là cái bẫy đã làm kẹt Uyên suốt tháng 8.

	Tờ chỉ có hàng đã nối phiếu và một dòng phí vận chuyển thì là tờ SẠCH,
	chờ kế toán ghi sổ. Nếu dòng phí bị tính là thiếu phiếu nhập thì mọi tờ
	có phí ship vĩnh viễn nằm ở bước chờ nối, không bao giờ ra.
	"""
	to = [_d("NVL1", "PNK-1", kho=1), _d("DVVC", "", kho=0)]
	dung("hàng đã nối, còn lại là dịch vụ thì tờ sạch",
		B.buoc_cua_to(to) == B.B_CHO_GHI_SO)
	dung("chỉ dòng qua kho mới bị đòi phiếu nhập",
		B.buoc_cua_to([_d("NVL1", "", kho=1), _d("DVVC", "", kho=0)]) == B.B_CHUA_NOI)


@ca("bước hoá đơn mua: tờ sạch thì chờ ghi sổ")
def _sach():
	dung("mọi dòng hàng đã có phiếu",
		B.buoc_cua_to([_d("A", "PNK-1"), _d("B", "PNK-1")]) == B.B_CHO_GHI_SO)
	dung("tờ rỗng cũng coi là chờ ghi sổ, không nghẽn",
		B.buoc_cua_to([]) == B.B_CHO_GHI_SO)


@ca("bước hoá đơn mua: hạn trả bằng ngày lập thì KHÔNG gọi là quá hạn")
def _han_tra():
	"""Ngày 04/09/2026: 62 trên 63 tờ đã ghi sổ có hạn trả trùng ngày hạch
	toán, vì 525 nhà cung cấp không ai được khai điều khoản thanh toán.
	Gọi hết là quá hạn thì chữ đó thành hằng số và mất nghĩa.
	"""
	dung("hạn bằng ngày lập là chưa khai điều khoản",
		B.han_tra_that("2026-09-03", "2026-09-03") == 0)
	dung("hạn sau ngày lập mới là hạn thật",
		B.han_tra_that("2026-09-03", "2026-09-30") == 1)
	dung("thiếu ngày thì không kết luận",
		B.han_tra_that("", "2026-09-30") == 0)


@ca("bước hoá đơn mua: màu không được đỏ hết")
def _mau():
	dung("việc đang chặn dây chuyền là đỏ", B.mau_cua_buoc(B.B_THIEU_MA) == "red")
	dung("chờ người khác là cam", B.mau_cua_buoc(B.B_CHUA_NOI) == "orange")
	dung("tờ sẵn sàng là xanh", B.mau_cua_buoc(B.B_CHO_GHI_SO) == "blue")
	so_do = len([1 for b in B.DS_BUOC if B.mau_cua_buoc(b) == "red"])
	dung("không quá hai bước mang màu đỏ", so_do <= 2)


@ca("bước hoá đơn mua: đã nối đủ dây từ máy chủ ra tới màn danh sách")
def _noi_day():
	s = _doc("vagabond/buoc_hoa_don_mua.py")
	dung("có khai trường mới", "TRUONG_MOI" in s and '"vgb_buoc"' in s)
	dung("trường để chế độ chỉ đọc", '"read_only": 1' in s)
	dung("hàm đặt bước nuốt lỗi, không làm rớt việc lưu",
		"frappe.log_error" in s.split("def dat_buoc(")[1])
	dung("chỉ tính cho tờ còn nháp",
		'cint(doc.get("docstatus")) != 0' in s.split("def dat_buoc(")[1])

	h = _doc("vagabond/hooks.py")
	dung("hook đã cắm vào lượt lưu hoá đơn mua",
		"vagabond.buoc_hoa_don_mua.dat_buoc" in h)

	t = _doc("vagabond/truong_tu_them.py")
	dung("trường mới được dựng lúc chuyển cấu trúc",
		"buoc_hoa_don_mua.TRUONG_MOI" in t)

	j = _doc("vagabond/public/js/minvoice_list.js")
	dung("màn danh sách có tô màu trạng thái", "get_indicator" in j)
	dung("màn danh sách kéo về ô bước xử lý", "'vgb_buoc'" in j)
	for b in B.DS_BUOC:
		dung("màn danh sách biết bước %s" % b, b in j)
	dung("màn danh sách không tự tính lại bước",
		"item_code" not in j.split("ganTrangThaiMuaHang")[1][:3000])
	dung("tờ đã ghi sổ thì đọc số dư chứ không đọc ô bước",
		"outstanding_amount" in j)
	dung("không dùng dấu gạch dài", "—" not in j and "–" not in j)
