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


@ca("bước hoá đơn mua: phải bật cờ thì Frappe mới gọi hàm tô màu của mình")
def _co_cho_to_nhap():
	"""Ngày 04/09/2026, lộ ra khi mở danh sách thật sau khi deploy v420.

	Frappe chặn trước: với doctype có ghi sổ, tờ đang nháp trả thẳng về
	"Nháp" và tờ đã huỷ trả về "Đã huỷ", KHÔNG hề gọi `get_indicator` của
	mình, trừ khi bật đúng hai cờ này. Thiếu chúng thì tờ đã ghi sổ hiện
	đúng nhãn mới, còn 3.170 tờ nháp vẫn trơ trơ một chữ "Nháp" - tức là
	đúng cái đông người ta cần phân biệt nhất.

	Cổng xanh và ca kiểm xanh đều không bắt được, vì chỗ chặn nằm trong mã
	của Frappe chứ không nằm trong mã của mình.
	"""
	j = _doc("vagabond/public/js/minvoice_list.js")
	dung("có bật cờ cho tờ nháp", "has_indicator_for_draft = 1" in j)
	dung("có bật cờ cho tờ đã huỷ", "has_indicator_for_cancelled = 1" in j)
	than = j.split("ganTrangThaiMuaHang")[1]
	dung(
		"bật cờ TRƯỚC khi khai hàm tô màu",
		than.index("has_indicator_for_draft") < than.index("CU.get_indicator = function"),
	)


@ca("bước hoá đơn mua: xét lệch hoá đơn điện tử thẳng từ số")
def _lech_tu_so():
	"""Bản thuần này để phần nạp lại hàng loạt không phải mở từng tờ.

	Phải giữ đúng luật của dung_lai_hddt: con số đáng tin là tổng tiền trừ
	thuế, chứ không phải ô tiền trước thuế. Ngày 27/08/2026 bản v319 neo
	vào ô tiền trước thuế và làm hỏng 5 tờ thật ngay lượt chạy đầu.
	"""
	dung("khớp thì không lệch",
		B.lech_tu_so(1100, 100, 0, 1000, 0, 1) == 0)
	dung("lệch quá ngưỡng thì báo lệch",
		B.lech_tu_so(1100, 100, 0, 900, 0, 1) == 1)
	dung("trừ giảm giá trước khi so",
		B.lech_tu_so(1100, 100, 0, 1200, 200, 1) == 0)
	dung("lấy tổng trừ thuế chứ không lấy ô tiền trước thuế",
		B.lech_tu_so(1100, 100, 555, 1000, 0, 1) == 0)
	dung("không có tổng thì mới quay về ô tiền trước thuế",
		B.lech_tu_so(0, 0, 1000, 1000, 0, 1) == 0)
	dung("không có mốc nào để so thì KHÔNG kết luận là lệch",
		B.lech_tu_so(0, 0, 0, 12345, 0, 1) == 0)


@ca("bước hoá đơn mua: nạp lại hàng loạt chỉ đụng tờ nháp còn trống ô")
def _nap_lai():
	"""Ngày 04/09/2026: deploy v421 xong mới thấy 3.168 trên 3.170 tờ nháp
	vẫn trống ô bước, vì ô chỉ được tính lúc lưu tờ. Không ai mở lại ba
	nghìn tờ để bấm lưu, nên phải nạp lại một lượt lúc chuyển cấu trúc.

	Ba điều kiện phải giữ, ca kiểm này chốt luôn kẻo bản sau sửa mất:
	chỉ tờ còn nháp, chỉ tờ còn trống ô, và không làm xê dịch ngày sửa.
	"""
	s = _doc("vagabond/buoc_hoa_don_mua.py")
	than = s.split("def nap_lai_hang_loat(")[1]
	dung("chỉ nhận tờ còn nháp", '"docstatus": 0' in than)
	dung("chỉ nhận tờ còn trống ô bước", 'TRUONG: ["in", ["", None]]' in than)
	dung("không làm xê dịch ngày sửa của ai", "update_modified=False" in than)
	dung("chỉ ghi đúng một ô, không lưu cả tờ",
		"frappe.db.set_value" in than and "get_doc(" not in than)
	dung("nuốt lỗi, không làm chết lượt chuyển cấu trúc",
		"frappe.log_error" in than)

	p = _doc("vagabond/patches/dong_bo_cau_truc.py")
	dung("đã cắm vào lượt chuyển cấu trúc",
		"buoc_hoa_don_mua.nap_lai_hang_loat()" in p)
