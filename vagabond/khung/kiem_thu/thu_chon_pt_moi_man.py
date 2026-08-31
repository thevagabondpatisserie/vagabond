# -*- coding: utf-8 -*-
"""Chọn phương thức thanh toán phải làm được ở MỌI đường vào, và nhãn không gãy.

Sự cố 31/08/2026, chị Loan Anh bắt được, anh Việt chuyển lại
--------------------------------------------------------------
Cùng một tờ hoá đơn 92243 của Ms.Tâm, hai đường vào cho hai kết quả:

  - Bấm thẳng vào dòng trong danh sách hoá đơn của quầy: màn KHOÁ ô chọn
    phương thức thanh toán, bảo "bấm Sửa hoá đơn rồi nhập mã OTP quản lý".
  - Tìm đúng mã đơn đó ở ô tìm kiếm: mở màn Chi tiết đơn, có ô chọn bình
    thường, không đòi gì cả.

Đường thứ nhất chính là đường thu ngân đi hàng ngày. Nên hàng ngày họ gặp
một cánh cửa khoá, còn cánh cửa mở thì nằm ở chỗ phải biết mới tìm ra.

Gốc: điều kiện mở ô chọn bên màn bill quầy chỉ tính bill TẠM TÍNH. Đơn
Pancake đồng bộ về là bill nháp thường nên rơi vào nhánh khoá.

Đáng nói là MÁY CHỦ chưa bao giờ đòi OTP cho việc này: `ban_hang.pos_chot`
ghi rõ "chọn phương thức thanh toán vẫn tự do, đó là nghiệp vụ bình thường,
không dính gì đến tiền của bill". Hàng rào nằm ở màn hình, và nó chỉ chặn
người làm thật chứ không chặn ai khác.

Bộ ca này chốt cả hai đầu: điều kiện mở ô chọn, và luật nhãn không gãy.
"""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la


def _bep():
	from vagabond import don_huy

	return os.path.join(
		os.path.dirname(os.path.abspath(don_huy.__file__)), "public", "js", "bep")


def _doc(ten):
	return io.open(os.path.join(_bep(), ten), encoding="utf-8").read()


@ca("chọn phương thức: đơn nháp CHƯA có phương thức thì mở ô chọn, không đòi OTP")
def _():
	s = _doc("10-bill-quay.js")
	dung("có tính đến đơn chưa có phương thức", "var chuaCoPt = nhap &&" in s)
	dung("đọc đúng ô phương thức", "!d.vgb_pt_thanh_toan" in s)
	dung("bill đã huỷ thì không mở", "!d.vgb_huy" in s)
	# Doc DUNG dong dat `choChon`. Truoc do ca kiem chi do chuoi "|| chuaCoPt"
	# trong ca tep, ma chuoi do con nam o cau tieu de nua, nen go mat hang rao
	# that thi ca kiem van xanh. Da thu nguoc va bat duoc chinh no.
	m = re.search(r"var choChon = ([^;]+);", s)
	dung("có dòng đặt choChon", bool(m))
	dung("chính dòng đó có nhánh chưa có phương thức", "chuaCoPt" in (m.group(1) if m else ""))


@ca("chọn phương thức: lưu được mà KHÔNG phải ghi sổ")
def _():
	# Don Pancake ve app truoc khi khach chuyen tien la ca hang ngay. Bat
	# thu ngan bam Ghi so mot the la ep ho chot doanh thu som.
	s = _doc("10-bill-quay.js")
	dung("có nút lưu riêng", 'id="pbLuuPt"' in s)
	dung("nút lưu có gắn tay bấm", "getElementById('pbLuuPt')" in s)
	# Di qua dung cua cu, khong mo cua moi cho tien.
	i = s.index("getElementById('pbLuuPt')")
	doan = s[i:i + 700]
	dung("đi qua cửa cũ pos_chot", "vagabond.ban_hang.pos_chot" in doan)
	for cam in ("pos_ghi_so", "submit"):
		dung("nút lưu KHÔNG ghi sổ: %s" % cam, cam not in doan)


@ca("chọn phương thức: nói rõ đang thiếu gì, không để thu ngân tự đoán")
def _():
	s = _doc("10-bill-quay.js")
	dung("có câu nhắc", "chưa chọn phương thức thanh toán" in s)
	dung("nói rõ không cần OTP", "Không cần mã OTP" in s)


@ca("chọn phương thức: đổi phương thức ĐÃ CÓ thì vẫn phải qua Sửa hoá đơn")
def _():
	# Do la dung vao tien da thu cua khach, khac han voi dien vao cho trong.
	s = _doc("10-bill-quay.js")
	dung("vẫn còn nhánh khoá", "🔒 Hoá đơn đã thu tiền của khách nên khoá lại" in s)
	dung("vẫn còn nút Sửa hoá đơn", 'id="pbSua"' in s)
	# `chuaCoPt` phai co dieu kien "chua co phuong thuc", neu bo di thi moi
	# don nhap deu mo toang ke ca don da thu tien.
	m = re.search(r"var chuaCoPt = ([^;]+);", s)
	dung("có bắt buộc ô phương thức còn trống", bool(m) and "!d.vgb_pt_thanh_toan" in m.group(1))


@ca("hai đường vào một tờ hoá đơn phải cùng cho chọn phương thức")
def _():
	"""Đường bấm dòng và đường ô tìm không được nói hai kiểu khác nhau."""
	bill = _doc("10-bill-quay.js")
	ds = _doc("08-doanh-so-sales.js")
	# Man Chi tiet don: luon ve o chon, khong dieu kien.
	dung("màn Chi tiết đơn có ô chọn", 'id="dsvPt"' in ds)
	# Man bill quay: gio cung ve o chon cho don nhap chua co phuong thuc.
	dung("màn bill quầy có ô chọn", 'id="pbPt"' in bill)
	mb = re.search(r"var choChon = ([^;]+);", bill)
	dung("màn bill quầy mở cho đơn chưa có phương thức",
		bool(mb) and "chuaCoPt" in mb.group(1))


@ca("nhãn nhỏ: không nhãn nào được gãy ruột giữa chừng")
def _():
	"""Anh Việt chụp màn hình 31/08/2026: "Có uỷ nhiệm chi" gãy làm hai dòng.

	Màn hình điện thoại hẹp nên gần như dòng nào cũng dính. Gốc là các nhãn
	nằm trong một khối chữ thường, trình duyệt ngắt dòng theo TỪ chứ không
	theo nhãn.
	"""
	s = _doc("40-phieu-hoan-huy.js")
	dung("có hàm dựng hàng nhãn chung", "function phNhanHang(" in s)
	i = s.index("function phNhanHang(")
	than = s[i:i + 900]
	dung("khối bọc là flex có xuống dòng", "flex-wrap:wrap" in than)
	dung("mỗi nhãn không gãy ruột", "white-space:nowrap" in than)
	# Khong con dong nhan nao dung ghep chuoi tay ben ngoai ham nay.
	dung("danh sách phiếu gọi hàm chung", "phNhanHang([" in s)


@ca("nhãn nhỏ: các màn cũ vốn đã chốt nowrap, không được bỏ đi")
def _():
	# Hai man nay da co san luat do tu truoc; ca kiem giu lai de lan sau
	# khong ai vo tinh go ra.
	for ten, ham in (("08-doanh-so-sales.js", "function dsChip("),
			("10-bill-quay.js", "var the = function (bg, fg, chu)")):
		s = _doc(ten)
		i = s.index(ham)
		dung("%s giữ nowrap" % ten, "white-space:nowrap" in s[i:i + 400])
