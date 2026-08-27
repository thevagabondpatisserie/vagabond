# -*- coding: utf-8 -*-
"""Chip "Không ghi sổ được" trên mọi màn tính tiền.

Anh Việt 27/08/2026:

    *"Em thêm 1 chip lọc 'Không ghi sổ được' để lọc các đơn không đủ điều
    kiện ghi sổ (thiếu phương thức thanh toán,...) để các bạn điền, bổ sung
    ngay trước 23h mỗi ngày. Chip này cần có ở mọi màn tính tiền của các
    điểm bán."*

Hai nhóm ca kiểm ở đây:

* Phép THUẦN `ghi_so_dieu_kien.ly_do` trả đúng lý do, và trả đúng MỘT lý do
  ưu tiên khi đơn thiếu nhiều thứ.
* Chip có mặt ở CẢ HAI màn danh sách hoá đơn, và cả hai màn đọc cùng một ô
  `ly_do_treo` do máy chủ tính, chứ không màn nào tự đoán lấy.

Ca kiểm thứ hai quan trọng không kém ca đầu: cái hỏng đã nhiều lần không
phải là phép sai, mà là hai màn nói hai câu khác nhau về cùng một đơn.
"""

import io
import os

from vagabond import ghi_so_dieu_kien
from vagabond.khung.kiem_thu.nen import ca, dung, la

CK = "Chuyển khoản"
CAN_MA = set(["GrabFood", "ShopeeFood", "Thẻ - ShinhanBank"])
PT_ONLINE = set([CK, "Tiền mặt", "GrabFood", "ShopeeFood", "Công nợ"])


def _js(ten):
	goc = os.path.dirname(os.path.dirname(os.path.abspath(ghi_so_dieu_kien.__file__)))
	return io.open(
		os.path.join(goc, "vagabond", "public", "js", "bep", ten), encoding="utf-8"
	).read()


def _py(ten):
	goc = os.path.dirname(os.path.abspath(ghi_so_dieu_kien.__file__))
	return io.open(os.path.join(goc, ten), encoding="utf-8").read()


def _don(**kw):
	"""Một đơn đã đủ điều kiện ghi sổ. Ca kiểm bẻ từng ô một."""
	d = {
		"docstatus": 0,
		"vgb_huy": 0,
		"vgb_tam_tinh": 0,
		"vgb_pt_thanh_toan": "Tiền mặt",
		"vgb_ma_tham_chieu": "",
		"sepay_du": 0,
		"customer": "KH-LE",
		"grand_total": 100000,
	}
	d.update(kw)
	return d


def _ly_do(d, **kw):
	kw.setdefault("pt_hop_le", PT_ONLINE)
	kw.setdefault("pt_can_ma", CAN_MA)
	kw.setdefault("khach_le", "KH-LE")
	return ghi_so_dieu_kien.ly_do(d, **kw)


# ------------------------------------------------------------- phép thuần


@ca("đơn đủ điều kiện thì không có lý do treo nào")
def _():
	la("đơn đủ", _ly_do(_don()), "")


@ca("chưa chọn phương thức thanh toán thì báo chua_pt")
def _():
	la("để trống", _ly_do(_don(vgb_pt_thanh_toan="")), "chua_pt")
	la("toàn dấu cách", _ly_do(_don(vgb_pt_thanh_toan="   ")), "chua_pt")
	la("ô rỗng hẳn", _ly_do(_don(vgb_pt_thanh_toan=None)), "chua_pt")


@ca("phương thức không nằm trong danh sách của nguồn thì báo pt_sai_nguon")
def _():
	la("BeFood không có trong nguồn này", _ly_do(_don(vgb_pt_thanh_toan="BeFood")), "pt_sai_nguon")


@ca("không đọc được danh sách phương thức thì THÔI KHÔNG KIỂM, không báo bừa")
def _():
	# Thà im còn hơn dán chữ "phương thức sai nguồn" lên một đơn bình thường
	# chỉ vì máy chủ đọc cấu hình hỏng.
	la("không đọc được danh sách thì im", _ly_do(_don(vgb_pt_thanh_toan="BeFood"), pt_hop_le=None), "")


@ca("chuyển khoản chưa về tiền và chưa có mã thì báo chua_ve_tien")
def _():
	la("chuyển khoản trắng tay", _ly_do(_don(vgb_pt_thanh_toan=CK)), "chua_ve_tien")


@ca("chuyển khoản đã đủ tiền thì qua, dù ô mã còn trống")
def _():
	# Máy tự điền mã giao dịch lúc ghi sổ (xem _soat_sepay), nên đủ tiền là
	# đủ điều kiện. Báo treo ở đây là bắt Sales đi tìm một mã không cần tìm.
	la("SePay đủ tiền", _ly_do(_don(vgb_pt_thanh_toan=CK, sepay_du=1)), "")


@ca("chuyển khoản có mã tham chiếu tay thì qua, dù ngân hàng chưa khớp")
def _():
	la("có mã gõ tay", _ly_do(_don(vgb_pt_thanh_toan=CK, vgb_ma_tham_chieu="FT2608")), "")


@ca("phương thức bắt buộc có mã mà để trống thì báo thieu_ma")
def _():
	la("GrabFood chưa có mã", _ly_do(_don(vgb_pt_thanh_toan="GrabFood")), "thieu_ma")
	la("GrabFood đã có mã", _ly_do(_don(vgb_pt_thanh_toan="GrabFood", vgb_ma_tham_chieu="GF-689")), "")


@ca("phương thức không bắt buộc mã thì để trống vẫn qua")
def _():
	la("tiền mặt không cần mã", _ly_do(_don(vgb_pt_thanh_toan="Tiền mặt")), "")


@ca("bán công nợ cho khách lẻ tức là chưa chọn khách")
def _():
	la("nợ khách lẻ", _ly_do(_don(vgb_pt_thanh_toan="Công nợ", customer="KH-LE")), "thieu_khach_no")
	la("nợ mà bỏ trống khách", _ly_do(_don(vgb_pt_thanh_toan="Công nợ", customer="")), "thieu_khach_no")
	la("nợ có khách thật", _ly_do(_don(vgb_pt_thanh_toan="Công nợ", customer="CTY-OSHIMA")), "")


@ca("phiếu tạm tính là nghiệp vụ bình thường, có lý do riêng chứ không lẫn")
def _():
	la("tạm tính", _ly_do(_don(vgb_tam_tinh=1, vgb_pt_thanh_toan="")), "tam_tinh")


@ca("hoá đơn đã ghi sổ hoặc đã huỷ thì không nằm trong nhóm treo")
def _():
	la("đã ghi sổ", _ly_do(_don(docstatus=1, vgb_pt_thanh_toan="")), "")
	la("đã huỷ ghi sổ", _ly_do(_don(docstatus=2, vgb_pt_thanh_toan="")), "")
	la("huỷ mềm", _ly_do(_don(vgb_huy=1, vgb_pt_thanh_toan="")), "")


@ca("đơn đủ điều kiện nhưng ngoài chuỗi tự ghi sổ thì vẫn phải nói ra")
def _():
	# Đây là loại đơn nguy hiểm nhất: nhìn màn hình thấy bình thường, 23h máy
	# không nhặt, sáng hôm sau không ai biết nó ở đâu.
	la("đủ nhưng ngoài chuỗi", _ly_do(_don(), trong_chuoi=False), "ngoai_chuoi")


@ca("thiếu nhiều thứ thì nói cái người ta sửa được trước, không nói ngoài chuỗi")
def _():
	la("thiếu pt thì nói thiếu pt", _ly_do(_don(vgb_pt_thanh_toan=""), trong_chuoi=False), "chua_pt")
	la("chưa về tiền thì nói chưa về tiền", _ly_do(_don(vgb_pt_thanh_toan=CK), trong_chuoi=False), "chua_ve_tien")


@ca("cờ đọc được cả kiểu số, chuỗi và luận lý")
def _():
	la("cờ dạng chuỗi", _ly_do(_don(vgb_pt_thanh_toan=CK, sepay_du="1")), "")
	la("cờ dạng luận lý", _ly_do(_don(vgb_pt_thanh_toan=CK, sepay_du=True)), "")
	la("cờ rỗng", _ly_do(_don(vgb_pt_thanh_toan=CK, sepay_du=None)), "chua_ve_tien")
	la("docstatus dạng chuỗi", _ly_do(_don(docstatus="1", vgb_pt_thanh_toan="")), "")


@ca("mọi mã lý do đều có câu tiếng Việt, không mã nào lọt ra màn hình trần")
def _():
	for m in ghi_so_dieu_kien.THU_TU:
		dung("mã %s phải có câu tiếng Việt" % m, ghi_so_dieu_kien.chu(m))
	la("bảng lý do và thứ tự phải khớp nhau", set(ghi_so_dieu_kien.THU_TU), set(ghi_so_dieu_kien.LY_DO.keys()))


@ca("đếm và xếp lý do bỏ qua đơn ghi sổ được")
def _():
	ds = ["chua_pt", "", "chua_pt", "ngoai_chuoi", None]
	la("đếm", ghi_so_dieu_kien.dem(ds), {"chua_pt": 2, "ngoai_chuoi": 1})
	la("xếp", ghi_so_dieu_kien.xep(ds), ["chua_pt", "ngoai_chuoi"])


@ca("xếp lý do theo THU_TU chứ không theo thứ tự gặp")
def _():
	la(
		"xếp theo THU_TU",
		ghi_so_dieu_kien.xep(["ngoai_chuoi", "chua_pt", "tam_tinh"]),
		["tam_tinh", "chua_pt", "ngoai_chuoi"],
	)


# --------------------------------------------- chip có mặt ở MỌI màn tính tiền


@ca("cả hai màn danh sách hoá đơn đều có chip Không ghi sổ được")
def _():
	for ten in ("10-bill-quay.js", "08-doanh-so-sales.js"):
		m = _js(ten)
		dung("%s phải có chip Không ghi sổ được" % ten, "Không ghi sổ được" in m)
		dung("%s phải đọc ô ly_do_treo" % ten, "ly_do_treo" in m)


@ca("màn hình KHÔNG tự đoán điều kiện ghi sổ, chỉ đọc ô máy chủ tính")
def _():
	# Màn nào tự viết lại luật là màn đó sẽ lệch với máy vào một ngày nào đó.
	# Chip chỉ được nhìn ô `ly_do_treo`, không được tự ghép điều kiện.
	for ten in ("10-bill-quay.js", "08-doanh-so-sales.js"):
		m = _js(ten)
		for dong in m.splitlines():
			if "Không ghi sổ được" not in dong:
				continue
			dung(
				"%s: chip Không ghi sổ được phải lọc theo ly_do_treo" % ten,
				"ly_do_treo" in dong,
			)


@ca("chip bỏ phiếu tạm tính ra, vì tạm tính chưa tới lúc ghi sổ")
def _():
	for ten in ("10-bill-quay.js", "08-doanh-so-sales.js"):
		m = _js(ten)
		for dong in m.splitlines():
			if "Không ghi sổ được" not in dong:
				continue
			dung("%s: chip phải chừa phiếu tạm tính ra" % ten, "tam_tinh" in dong)


@ca("máy chủ gắn lý do treo cho CẢ hai màn, dùng chung một hàm")
def _():
	m = _py("ban_hang.py")
	la("chỉ được có một hàm gắn lý do", m.count("def _gan_ly_do_treo("), 1)
	# Gọi trong pos_ds_bill (mọi điểm bán) và trong bang_doanh_so (màn Sales).
	dung("phải gọi ở cả hai màn", m.count("_gan_ly_do_treo(") >= 3)


@ca("phép quyết định nằm ở tệp thuần, ban_hang không tự chép lại luật")
def _():
	m = _py("ban_hang.py")
	dung("ban_hang phải gọi phép thuần", "ghi_so_dieu_kien.ly_do(" in m)
	# Bảng câu chữ chỉ được có một bản, ở tệp thuần.
	la("câu chữ không được chép sang ban_hang", m.count('"Chưa chọn phương thức thanh toán"'), 0)


@ca("tệp thuần không import gì, chạy được trên máy CI tay không")
def _():
	m = _py("ghi_so_dieu_kien.py")
	for dong in m.splitlines():
		t = dong.strip()
		dung(
			"ghi_so_dieu_kien.py không được import gì: %s" % t,
			not (t.startswith("import ") or t.startswith("from ")),
		)


@ca("pos_ds_bill và bang_doanh_so đều đọc các ô mà phép thuần cần")
def _():
	m = _py("ban_hang.py")
	# Thiếu một ô là phép thuần đọc ra None rồi kết luận sai mà không ai biết.
	for o in ('"customer"', '"vgb_tam_tinh"', '"custom_pancake_id"', '"vgb_quay"'):
		dung("ban_hang.py phải đọc ô %s" % o, o in m)
