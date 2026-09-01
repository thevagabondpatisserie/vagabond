# -*- coding: utf-8 -*-
"""Khách trên một đơn phải hiện được ở MỌI màn xem lại đơn.

Anh Việt 01/09/2026, kèm ảnh chụp màn Chi tiết đơn:

    *"Em chữa thêm 1 lỗi đó là đơn mà xem lại thì không thấy được thông tin
    khách hàng hiển thị trên đơn ở mọi màn luôn."*

Cùng ngày anh đặt luôn quy tắc chung: *"nói chung về nguồn đơn, phương thức
thanh toán, món,... mọi tính năng đều cần có ở mọi màn tính tiền điểm bán"*.

Vì sao lỗi này sống lâu mà không ai bắt: dữ liệu VỐN CÓ SẴN từ đầu, nằm
trong ô ghi chú của hoá đơn theo khuôn

    <nguồn> #<mã đơn> - <tên khách>[ - <số điện thoại>][ - Quầy <mã>]

Nhưng mỗi màn tự đọc một kiểu. Màn Sales `split(' - ')[1]`, màn bill quầy
không đọc gì cả. Nên cùng một tờ hoá đơn mở hai đường ra hai kết quả khác
nhau, và không phép kiểm nào nói được điều đó.

Bộ ca kiểm này chốt ba thứ:

* Máy chủ tách khách bằng ĐÚNG MỘT hàm, và mọi cửa trả danh sách đơn đều gọi
  hàm đó (QT-19).
* Màn hình đọc bằng ĐÚNG MỘT hàm, không màn nào tự tách lại bằng `split` thô.
* Bốn màn xem lại đơn đều có chỗ bày khách ra.

Ca kiểm tầng khung nên chỉ đọc nguồn và soi chuỗi, không cần Frappe, không
cần site, không cần mạng.
"""

import io
import os
import re

from vagabond import hoan_tien
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	# .../vagabond/vagabond/hoan_tien.py -> lui hai bậc là gốc cây mã nguồn.
	return os.path.dirname(os.path.dirname(os.path.abspath(hoan_tien.__file__)))


def _py(ten):
	return io.open(os.path.join(_goc(), "vagabond", ten), encoding="utf-8").read()


def _js(ten):
	return io.open(
		os.path.join(_goc(), "vagabond", "public", "js", "bep", ten), encoding="utf-8"
	).read()


# --------------------------------------------------- phép tách, thuần, không site


@ca("tách ghi chú: lấy đúng tên và số điện thoại của khách")
def _tach_du():
	ten, so = hoan_tien.tach_ghi_chu_don("Pancake #91759 - Loan Anh - 0933751352")
	la("tên", ten, "Loan Anh")
	la("số", so, "0933751352")


@ca("tách ghi chú: đuôi Quầy KHÔNG được hiểu thành số điện thoại")
def _tach_bo_duoi_quay():
	# Đây đúng là chỗ `split(' - ')[2]` thô của màn Sales đọc sai: nó lấy
	# nguyên chữ "Quầy TCV" rồi dán vào ô số điện thoại của khách.
	ten, so = hoan_tien.tach_ghi_chu_don("Mang về #TEST-01 - Chị Dung - Quầy TCV")
	la("tên", ten, "Chị Dung")
	la("số rỗng chứ không phải chữ Quầy", so, "")


@ca("tách ghi chú: đơn không ghi gì thì trả rỗng chứ không nổ")
def _tach_rong():
	la("chuỗi rỗng", hoan_tien.tach_ghi_chu_don(""), ("", ""))
	la("None", hoan_tien.tach_ghi_chu_don(None), ("", ""))
	la("không có dấu gạch", hoan_tien.tach_ghi_chu_don("Pancake #123"), ("", ""))


# ------------------------------------------------- một chỗ tính ở tầng máy chủ


@ca("máy chủ: có đúng một hàm gắn khách vào dòng đơn")
def _co_ham_chung():
	s = _py("ban_hang.py")
	dung("ban_hang có hàm gan_khach_vao_dong", "def gan_khach_vao_dong(" in s)
	dung(
		"hàm đó gọi lại phép tách sẵn chứ không viết lại lần hai",
		"tach_ghi_chu_don" in s.split("def gan_khach_vao_dong(")[1][:1600],
	)


@ca("máy chủ: bốn cửa trả danh sách đơn đều gọi hàm chung")
def _moi_cua_deu_goi():
	# Thiếu một cửa là màn ăn theo cửa đó lại trắng thông tin khách, đúng
	# cái bệnh anh Việt báo. Đếm bằng tên hàm chứ không đếm dòng, để phiên
	# sau đổi chỗ gọi vẫn không làm hỏng ca kiểm.
	bh = _py("ban_hang.py")
	la("ban_hang gọi ba lần: danh sách bill, doanh số, tìm đơn",
		bh.count("gan_khach_vao_dong(") - 1, 3)
	dung("kế toán gọi", "gan_khach_vao_dong(" in _py("ke_toan.py"))
	dung("tìm đơn để hoàn gọi", "gan_khach_vao_dong(" in _py("don_huy.py"))


@ca("máy chủ: danh sách bill quầy có đọc về các ô khách")
def _pos_ds_bill_du_o():
	s = _py("ban_hang.py")
	kh = s.split("def pos_ds_bill(")[1][:2600]
	for o in ("remarks", "customer_name", "vgb_khach_no", "customer"):
		dung("pos_ds_bill đọc %s" % o, '"%s"' % o in kh)


@ca("máy chủ: bảng doanh số có đọc về các ô khách")
def _bang_doanh_so_du_o():
	s = _py("ban_hang.py")
	kh = s.split("def bang_doanh_so(")[1][:3000]
	for o in ("remarks", "customer_name", "vgb_khach_no", "customer"):
		dung("bang_doanh_so đọc %s" % o, '"%s"' % o in kh)


@ca("máy chủ: khách gộp dùng chung KHÔNG được coi là hồ sơ khách")
def _khach_gop_khong_ra_ma():
	# "Khách lẻ Online" là một giỏ chung của cả tiệm. Đưa mã đó lên màn hình
	# là bày ra thẻ thành viên của một người không có thật, và tệ hơn là
	# cộng dồn điểm của mọi khách vãng lai vào một hồ sơ.
	s = _py("ban_hang.py")
	than = s.split("def gan_khach_vao_dong(")[1][:1800]
	dung("có chặn khách gộp", "KHACH_LE" in than)
	dung("chặn cả Khách bán lẻ", "Khách bán lẻ" in than)


# ------------------------------------------------ một chỗ đọc ở tầng màn hình


@ca("màn hình: có đúng một hàm đọc khách, đặt ở tệp nền")
def _js_co_ham_chung():
	s = _js("00-nen.js")
	dung("có khachTrenDon", "function khachTrenDon(" in s)
	dung("có khachMotDong", "function khachMotDong(" in s)


@ca("màn hình: không màn nào còn tự tách ghi chú bằng split thô")
def _js_khong_split_tho():
	# `(r.remarks || '').split(' - ')` là đúng dòng mã đã làm bill quầy hiện
	# chữ "Quầy TCV" vào ô số điện thoại. Cấm nó quay lại.
	xau = re.compile(r"\(\s*\w+\.remarks\s*\|\|\s*''\s*\)\s*\.split\(")
	for ten in ("08-doanh-so-sales.js", "10-bill-quay.js", "12-van-don.js"):
		la("%s không split thô" % ten, len(xau.findall(_js(ten))), 0)


@ca("màn hình: bốn màn xem lại đơn đều bày khách ra")
def _bon_man_deu_bay():
	la("danh sách và chi tiết đơn Sales",
		_js("08-doanh-so-sales.js").count("khachTrenDon(") >= 2, True)
	s10 = _js("10-bill-quay.js")
	dung("danh sách bill quầy có khách", "khachTrenDon(" in s10)
	dung("chi tiết bill quầy có khách", "khachMotDong(" in s10)
	dung("màn lập phiếu hoàn có khách", "khachMotDong(" in _js("40-phieu-hoan-huy.js"))


@ca("màn hình: chi tiết bill quầy có xin thẻ thành viên")
def _bill_quay_co_the():
	# Đây là chỗ hổng nặng nhất trước 01/09/2026: cùng một hoá đơn, mở bên
	# Sales thì ra thẻ và điểm, mở bên quầy thì trắng trơn.
	s = _js("10-bill-quay.js")
	dung("có gọi thẻ trên đơn", "vagabond.khach_hang.the_tren_don" in s)
	dung("có chỗ trống để nhét thẻ", 'id="pbThe"' in s)


# --------------------------------------- đồng bộ tính năng giữa các màn tính tiền


@ca("màn nhập đơn tay gắn được khách thành viên")
def _nhap_tay_gan_khach():
	# Trước 01/09/2026 màn này chỉ có ba ô chữ, tên và số rơi vào ghi chú,
	# nên đơn ghi ở đây KHÔNG tích điểm cho khách, dù máy chủ đã nhận mã
	# khách từ lâu.
	s = _js("08-doanh-so-sales.js")
	dung("có nút chọn khách", "dstKhachChon" in s)
	dung("có nút bỏ khách", "dstKhachBo" in s)
	dung("gửi mã khách lên máy chủ", "khach_ma: dsTay.khach_ma" in s)
	bh = _py("ban_hang.py")
	dung("máy chủ vẫn nhận tham số đó", "khach_ma" in bh.split("def tao_don_tay(")[1][:900])


@ca("màn nhập đơn tay có khoá bấm hai lần như màn quầy")
def _nhap_tay_khoa_bam():
	s = _js("08-doanh-so-sales.js")
	dung("có cờ khoá", "var dstDangLuu = false;" in s)
	dung("có chặn lượt bấm thứ hai", "if (dstDangLuu) return;" in s)
	dung("mở khoá khi lỗi", s.count("dstDangLuu = false") >= 3)


@ca("màn quầy không ép cứng Tiền mặt khi phương thức đó bị tắt")
def _khong_ep_tien_mat():
	# Gõ cứng chuỗi 'Tiền mặt' làm đường lui thì ai tắt phương thức đó trong
	# Cài đặt là màn tính tiền không nút nào sáng, bấm Thu tiền thì máy chủ
	# ném lỗi. Phải lấy phần tử đầu danh sách làm đường lui.
	s = _js("09-tinh-tien-quay.js")
	dung("có kiểm Tiền mặt còn bật không", "p.v === 'Tiền mặt'" in s)
	dung("có đường lui theo danh sách", "(dsPt[0] && dsPt[0].v)" in s)
