# -*- coding: utf-8 -*-
"""Tiền tố mã bill theo điểm bán, và phép khớp tiền khi nội dung không có mã.

Anh Việt 31/08/2026:

    *"Nội dung chuyển khoản phải ra luôn trên QR code để khách quét là có
    luôn, máy tự đối soát trong 2 giây luôn để thu ngân khỏi phải nhìn tin
    nhắn báo chuyển khoản mới là xịn! Anh đề xuất thêm về tiền tố mã đơn thì
    đơn ở Trần Cao Vân sẽ mang mã TCV thay vì VGB, NVHTN thì là NVH còn ở
    307/1 Nguyễn Văn Trỗi Sales Online thì tiền tố là SOL."*

Ba nhóm ca kiểm ở đây:

* `ma_bill` sinh và đọc đúng tiền tố, và KHÔNG bao giờ đánh rơi tiền tố VGB
  của hơn hai nghìn bill cũ.
* `khop_tien` chỉ nhận cặp một một, hai bill cùng số tiền trong cùng khung
  giờ thì trả về dạng phân vân chứ không chọn bừa.
* Màn hình và máy chủ đọc CÙNG một bảng tiền tố, không nơi nào chép lại.

Nhóm thứ ba quan trọng ngang hai nhóm đầu: cái hỏng lặp đi lặp lại của repo
này không phải phép sai, mà là hai nơi giữ hai bản của cùng một bảng rồi
lệch nhau lúc nào không ai hay.
"""

import io
import os
import re

from vagabond import khop_tien, ma_bill
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	# .../vagabond/vagabond/ma_bill.py -> lui hai bac la goc cay ma nguon.
	return os.path.dirname(os.path.dirname(os.path.abspath(ma_bill.__file__)))


def _js(ten):
	return io.open(
		os.path.join(_goc(), "vagabond", "public", "js", "bep", ten), encoding="utf-8"
	).read()


def _py(ten):
	return io.open(os.path.join(_goc(), "vagabond", ten), encoding="utf-8").read()


# ------------------------------------------------------ tiền tố theo điểm bán


@ca("ma_bill: mỗi điểm bán ra đúng tiền tố anh Việt chốt")
def _tien_to():
	la("Trần Cao Vân", ma_bill.tien_to_cua("TCV"), "TCV")
	la("NVHTN", ma_bill.tien_to_cua("NVHTN"), "NVH")
	la("Sales Online", ma_bill.tien_to_cua("SALES"), "SOL")


@ca("ma_bill: điểm lạ thì rơi về VGB chứ không ra mã trần")
def _tien_to_la():
	# Trả rỗng là sinh ra mã năm ký tự trần, dò trong sao kê sẽ khớp bừa.
	la("điểm chưa khai", ma_bill.tien_to_cua("XYZ"), "VGB")
	la("không truyền gì", ma_bill.tien_to_cua(None), "VGB")
	la("chuỗi rỗng", ma_bill.tien_to_cua("  "), "VGB")


@ca("ma_bill: viết thường viết hoa đều ra một tiền tố")
def _tien_to_hoa():
	la("tcv thường", ma_bill.tien_to_cua("tcv"), "TCV")
	la("có khoảng trắng", ma_bill.tien_to_cua(" nvhtn "), "NVH")


# ------------------------------------------------------------ đọc mã trong sao kê


@ca("ma_bill: nhận cả bốn tiền tố, VGB giữ vĩnh viễn cho bill cũ")
def _hop_le():
	dung("bill cũ VGB", ma_bill.hop_le("VGBQ4PFX"))
	dung("bill TCV", ma_bill.hop_le("TCVQ4PFX"))
	dung("bill NVH", ma_bill.hop_le("NVHQ4PFX"))
	dung("bill SOL", ma_bill.hop_le("SOLQ4PFX"))


@ca("ma_bill: chuỗi rác mang chữ B I O Z 0 1 2 không còn khớp bừa")
def _chat():
	# Bảng chữ sinh mã cố tình thiếu bảy ký tự này, nên phép dò cũng chặt
	# theo. Mẫu cũ VGB[A-Z0-9]{5} thì "TCVB1OZ0" cũng khớp.
	dung("có chữ B", not ma_bill.hop_le("TCVBBBBB"))
	dung("có số 0", not ma_bill.hop_le("TCV00000"))
	dung("có chữ O", not ma_bill.hop_le("VGBOOOOO"))
	for c in "BIOZ012":
		dung("ký tự %s không nằm trong bảng sinh mã" % c, c not in ma_bill.CHU_SINH)


@ca("ma_bill: đuôi thiếu hoặc thừa ký tự đều không nhận")
def _dai():
	dung("thiếu một ký tự", not ma_bill.hop_le("TCVQ4PF"))
	dung("thừa một ký tự", not ma_bill.hop_le("TCVQ4PFXA"))
	dung("chỉ có tiền tố", not ma_bill.hop_le("TCV"))
	dung("rỗng", not ma_bill.hop_le(""))


@ca("ma_bill: tách được tiền tố ra khỏi đuôi")
def _tach():
	la("tách TCVQ4PFX", ma_bill.tach_tien_to("TCVQ4PFX"), ("TCV", "Q4PFX"))
	la("mã hỏng thì rỗng", ma_bill.tach_tien_to("XXX"), ("", ""))


@ca("ma_bill: mã cũ VGB thì KHÔNG đoán bừa ra điểm bán")
def _diem():
	# Trước ngày đổi tiền tố mọi điểm đều dùng chung VGB, đoán là đoán sai.
	la("mã cũ", ma_bill.diem_cua_ma("VGBQ4PFX"), "")
	la("mã TCV", ma_bill.diem_cua_ma("TCVQ4PFX"), "TCV")
	la("mã hỏng", ma_bill.diem_cua_ma("nothing"), "")


@ca("ma_bill: dò được mã nằm lẫn trong một dòng sao kê thật")
def _do_trong_dong():
	dong = "Q00033k5p6  VAGABOND1 1  QR TCVQ4PFX Ma GD ACSP/ XR703682"
	la("tìm ra đúng một mã", ma_bill.RE_MA.findall(dong), ["TCVQ4PFX"])


# --------------------------------------------------------------- khớp theo tiền


@ca("khop_tien: sai lệch một đồng vẫn coi là cùng số tiền")
def _cung_tien():
	dung("bằng nhau", khop_tien.cung_tien(230000, 230000))
	dung("lệch một đồng", khop_tien.cung_tien(230000, 230001))
	dung("lệch nghìn đồng thì không", not khop_tien.cung_tien(230000, 231000))


@ca("khop_tien: khung giờ nới trước nhiều hơn sau")
def _cua_so():
	# Khách quét mã rồi mới bấm chuyển, hoặc thu ngân chốt bill sau khi tiền
	# đã về, nên nới cả hai chiều nhưng không đối xứng.
	dung("tiền về trước 40 phút", khop_tien.trong_cua_so(600, 560))
	dung("tiền về sau 10 phút", khop_tien.trong_cua_so(600, 610))
	dung("tiền về trước 50 phút thì ngoài", not khop_tien.trong_cua_so(600, 550))
	dung("tiền về sau 30 phút thì ngoài", not khop_tien.trong_cua_so(600, 630))


@ca("khop_tien: một bill một giao dịch thì nhận chắc")
def _mot_mot():
	kq = khop_tien.de_xuat(
		[{"ma": "A", "tien": 230000, "phut": 600}],
		[{"ten": "GD1", "tien": 230000, "phut": 595}],
	)
	la("nhận chắc", sorted(kq["chac"].keys()), ["A"])
	la("không phân vân", kq["phan_van"], {})


@ca("khop_tien: hai bill cùng số tiền cùng khung giờ thì KHÔNG chọn bừa")
def _phan_van():
	# Gạch nhầm một giao dịch vào sai bill là sai doanh thu của cả hai bill,
	# mà sai doanh thu thì khó lần ra hơn nhiều so với để trống.
	kq = khop_tien.de_xuat(
		[{"ma": "A", "tien": 230000, "phut": 600}, {"ma": "B", "tien": 230000, "phut": 605}],
		[{"ten": "GD1", "tien": 230000, "phut": 598}],
	)
	la("không nhận chắc bill nào", kq["chac"], {})
	la("cả hai bill đều phân vân", sorted(kq["phan_van"].keys()), ["A", "B"])


@ca("khop_tien: một bill soi ra hai giao dịch thì cũng phân vân")
def _hai_gd():
	kq = khop_tien.de_xuat(
		[{"ma": "A", "tien": 230000, "phut": 600}],
		[{"ten": "GD1", "tien": 230000, "phut": 590}, {"ten": "GD2", "tien": 230000, "phut": 605}],
	)
	la("không nhận chắc", kq["chac"], {})
	la("hai đường phân vân", len(kq["phan_van"]["A"]), 2)


@ca("khop_tien: khác số tiền hoặc ngoài khung giờ thì không ghép")
def _khong_ghep():
	kq = khop_tien.de_xuat(
		[{"ma": "A", "tien": 230000, "phut": 600}],
		[{"ten": "GD1", "tien": 231000, "phut": 598}, {"ten": "GD2", "tien": 230000, "phut": 400}],
	)
	la("không nhận chắc", kq["chac"], {})
	la("không phân vân", kq["phan_van"], {})


@ca("khop_tien: danh sách rỗng thì trả rỗng, không nổ")
def _rong():
	kq = khop_tien.de_xuat([], [])
	la("chắc rỗng", kq["chac"], {})
	la("phân vân rỗng", kq["phan_van"], {})
	kq = khop_tien.de_xuat(None, None)
	la("truyền None cũng rỗng", kq["chac"], {})


# ------------------------------------------------- một nơi giữ, không nơi nào chép


@ca("ban_hang đọc mẫu mã bill từ ma_bill, không tự viết lại")
def _mot_noi_giu():
	s = _py("ban_hang.py")
	dung("có lấy RE_MA từ ma_bill", "RE_MA_BILL = ma_bill.RE_MA" in s)
	dung(
		"không còn mẫu VGB tự viết trong ban_hang",
		not re.search(r're\.compile\(r"VGB\[A-Z0-9\]', s),
	)


@ca("màn tính tiền đọc bảng tiền tố từ máy chủ, không chép bảng")
def _man_doc_bang():
	s = _js("09-tinh-tien-quay.js")
	dung("posTienTo lấy từ CFGBH", "c.ma_tien_to" in s)
	dung(
		"không còn nối cứng chuỗi VGB vào mã sinh ra",
		"return 'VGB' + s;" not in s,
	)
	cfg = _py("ban_hang.py")
	dung("máy chủ có gửi bảng tiền tố xuống", '"ma_tien_to": dict(ma_bill.TIEN_TO_DIEM)' in cfg)
	dung("máy chủ có gửi bảng chữ sinh mã xuống", '"ma_chu_sinh": ma_bill.CHU_SINH' in cfg)


@ca("chip Chờ tiền về chỉ đỏ khi máy chủ thật sự chặn")
def _chip_do():
	# 31/08/2026: chip đỏ suốt cả màn dù không bill nào bị chặn, anh Việt
	# tưởng cả điểm Quận 1 bị kẹt. Phép quyết định nằm bên ghi_so_dieu_kien,
	# màn hình chỉ đọc ly_do_treo chứ không tự đoán.
	s = _js("10-bill-quay.js")
	dung("chip đỏ soi ly_do_treo", "r.ly_do_treo === 'chua_ve_tien'" in s)
	dung("có nói được đường khớp theo số tiền", "sepay_duong === 'so_tien'" in s)
	dung(
		"chip lọc Chờ tiền về cũng soi cùng một ô",
		"{ k: 'cho_tien', nhan: '⏳ Chờ tiền về', loc: function (r) { return r.ly_do_treo === 'chua_ve_tien'; } }" in s,
	)


@ca("khớp theo số tiền KHÔNG mở cổng ghi sổ")
def _khong_mo_cong():
	# Một nơi tính một nơi kiểm (QT-19). Nơi kiểm vẫn là ghi_so_dieu_kien,
	# khớp theo số tiền chỉ làm sáng màn hình.
	s = _py("ghi_so_dieu_kien.py")
	dung("ghi_so_dieu_kien không đụng tới khop_tien", "khop_tien" not in s)
	dung("ghi_so_dieu_kien không đụng tới ma_bill", "ma_bill" not in s)


@ca("hai mô đun mới đều THUẦN, không kéo theo Frappe")
def _thuan():
	for ten in ("ma_bill.py", "khop_tien.py"):
		s = _py(ten)
		dung("%s không import frappe" % ten, "import frappe" not in s)
		dung("%s không import requests" % ten, "import requests" not in s)
