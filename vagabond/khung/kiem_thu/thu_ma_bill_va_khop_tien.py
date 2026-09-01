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


def _www(ten):
	return io.open(os.path.join(_goc(), "vagabond", "www", ten), encoding="utf-8").read()


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
	dung(
		"chip lọc Chờ tiền về cũng soi cùng một ô",
		"{ k: 'cho_tien', nhan: '⏳ Chờ tiền về', loc: function (r) { return r.ly_do_treo === 'chua_ve_tien'; } }" in s,
	)


@ca("máy KHÔNG tự đoán khoản tiền theo khung giờ")
def _khong_tu_doan():
	# Anh Việt 01/09/2026: *"máy cũng không cần phải đoán qua khung giờ vì
	# rất rủi ro đoán nhầm"*. Ca kiểm này chốt việc đó lại: `pos_ds_bill`
	# tuyệt đối không được gọi phép ghép tự động.
	s = _py("ban_hang.py")
	than = s[s.index("def pos_ds_bill("):]
	than = than[: than.index("\ndef ")]
	dung("pos_ds_bill không gọi _khop_theo_tien", "_khop_theo_tien(" not in than)
	# Và màn hình cũng không còn đường nào tự sáng xanh theo số tiền.
	j = _js("09-tinh-tien-quay.js")
	dung("màn tính tiền không còn biến đường khớp", "posSepayDuong" not in j)
	dung("không còn nhánh tự xanh theo số tiền", "'so_tien'" not in j)


@ca("nút Dò tiền chuyển khoản: máy đề xuất, người quyết định")
def _nut_do_tien():
	s = _py("ban_hang.py")
	dung("có cửa liệt kê", "def pos_do_tien(" in s)
	dung("có cửa gắn tay", "def pos_gan_tien(" in s)
	# Gắn tay PHẢI để lại vết, không thì cuối tháng không ai biết ai gắn.
	dung("gắn xong ghi lại vào ghi chú đối soát", "Thu ngân dò tay" in s)
	# Và phải chặn hai hoá đơn cùng ôm một khoản tiền.
	dung(
		"chặn một khoản gắn cho hai hoá đơn",
		"Một khoản tiền chỉ thuộc về" in s,
	)
	j = _js("09-tinh-tien-quay.js")
	dung("màn hình có nút", "data-dotien" in j)
	dung("có bảng dò tiền", "function posSheetDoTien(" in j)
	dung("bill chưa lưu thì không gắn được", "if (!t || !siName) return;" in j)


@ca("khớp theo số tiền KHÔNG mở cổng ghi sổ")
def _khong_mo_cong():
	# Một nơi tính một nơi kiểm (QT-19). Nơi kiểm vẫn là ghi_so_dieu_kien.
	s = _py("ghi_so_dieu_kien.py")
	dung("ghi_so_dieu_kien không đụng tới khop_tien", "khop_tien" not in s)
	dung("ghi_so_dieu_kien không đụng tới ma_bill", "ma_bill" not in s)


@ca("nguồn food app cũng hiện nút chọn phương thức thanh toán")
def _pt_food_app():
	# Bên Dễ 01/09/2026: *"các food app nó không có nút chọn phương thức,
	# khi lưu hoá đơn nó để là thanh toán chuyển khoản, chờ tiền về"*.
	j = _js("09-tinh-tien-quay.js")
	dung(
		"khối nút phương thức nằm ngoài nhánh laApp",
		"'</div>' +\n    (laApp" in j,
	)
	dung("đơn của sàn vẫn gửi phương thức lên máy chủ", "pt: posDon.pt || ''" in j)


@ca("phương thức được nắn về đúng nguồn ngay lúc sửa")
def _nan_tai_cho():
	# Phép nắn vốn đã có nhưng chỉ chạy lúc ghi sổ, nên bill nằm ở trạng thái
	# nháp cả ngày với phương thức sai và các bạn tưởng hệ thống hỏng.
	s = _py("ban_hang.py")
	dung("có phép nắn tại chỗ", "def _nan_pt_tai_cho(" in s)
	dung("bill tạm tính thì không nắn", 'if cint(si.get("vgb_tam_tinh")):' in s)
	# Hai cua sua bill deu phai goi, khong duoc chi mot cua.
	la("nắn ở cả hai cửa sửa bill", s.count("\n\t_nan_pt_tai_cho(si)"), 2)


@ca("màn Cài đặt kêu lên khi điểm bán chưa khai tài khoản riêng")
def _canh_bao_tai_khoan():
	# Ba tài khoản ảo của ba điểm bán đã biến mất khỏi cấu hình lúc nào không
	# ai hay (anh Việt 01/09/2026). Cái hỏng thật sự là nó biến mất lặng lẽ.
	s = _py("tai_khoan.py")
	dung("máy chủ có đếm điểm còn thiếu", '"thieu_diem": thieu_diem' in s)
	j = _js("17-cai-dat.js")
	dung("màn hình có hiện cảnh báo", "tkData.thieu_diem" in j)
	dung("cảnh báo nói rõ hậu quả", "không tách được tiền của nơi nào" in j)


@ca("hai mô đun mới đều THUẦN, không kéo theo Frappe")
def _thuan():
	for ten in ("ma_bill.py", "khop_tien.py"):
		s = _py(ten)
		dung("%s không import frappe" % ten, "import frappe" not in s)
		dung("%s không import requests" % ten, "import requests" not in s)


# ============================== 01/09/2026: anh Việt sửa lại ba chỗ em làm sai


@ca("mã bill tự chữa khi tiền tố lệch")
def _tu_chua_ma():
	# Sáng 01/09 anh Việt: *"mã chuyển khoản thì lại có chữ TCV VGB... mà
	# trong đơn thì lại không có chữ TCV"*. Máy quầy đang mở từ trước lần
	# deploy nên bảng tiền tố trong đầu nó là bảng cũ, mã sinh ra vẫn mang
	# VGB dù đang đứng ở Trần Cao Vân.
	j = _js("09-tinh-tien-quay.js")
	dung("có phép tự chữa mã", "posDon.bill = posMaBill();" in j)
	dung("chỉ chữa khi bảng tiền tố đã về", "posCoBangTienTo()" in j)
	# Giỏ hàng có món rồi thì khách có thể đã quét mã QR. Đổi mã lúc đó là
	# đổi nội dung khách vừa chuyển.
	dung("chỉ chữa khi giỏ hàng còn trống", "!posDon.mon.length" in j)


@ca("cấu hình bán hàng không giữ mãi trong đầu màn hình")
def _cfg_tuoi():
	# Sửa Cài đặt mà quầy không thấy thì sửa cũng như không: ba tài khoản ảo
	# khai lúc 08h mà máy quầy đang mở vẫn sinh QR vào tài khoản chung.
	j = _js("08-doanh-so-sales.js")
	dung("có hạn dùng cho cấu hình", "CFGBH_HAN" in j)
	dung("quá hạn thì đọc lại", "(Date.now() - CFGBH_LUC) > CFGBH_HAN" in j)


@ca("dò tiền xổ ra cả sao kê của điểm bán, không chỉ khoản đúng số tiền")
def _do_tien_ca_ngay():
	# Anh Việt 01/09/2026: *"nút Dò tay thì cài thêm để vừa dò tự động, vừa
	# phải xổ ra danh sách giao dịch ngày hôm đó chuyển khoản vào tài khoản
	# ảo của điểm bán, nhân viên click vào rồi chọn từ danh sách để gắn"*.
	s = _py("ban_hang.py")
	dung("có phép lọc sao kê theo điểm", "def _gd_cua_diem(" in s)
	dung("cửa dò tiền dùng phép đó", "gds, tk = _gd_cua_diem(ngay, diem)" in s)
	dung("đánh dấu khoản đúng số tiền", '"khop":' in s)
	dung("nói rõ khoản nào đã có chủ", "def _gd_da_co_chu(" in s)
	j = _js("09-tinh-tien-quay.js")
	dung("màn hình nói rõ đang soi tài khoản nào", "tk_rieng" in j)
	dung("khoản đã gắn cho hoá đơn khác thì không bấm được", "g.cua_bill" in j)


@ca("dấu nhận tài khoản ảo bỏ ba chữ VQR ở đầu")
def _dau_tk():
	# Ngân hàng ghi "Q00033k5p6" cho tài khoản "VQRQ00033k5p6". Đối chiếu cả
	# chuỗi thì không dòng sao kê nào khớp.
	s = _py("ban_hang.py")
	dung("có hàm cắt tiền tố VQR", "def _dau_tk(" in s)
	dung("cắt đúng ba chữ VQR", 't[3:] if t.startswith("VQR") else t' in s)


@ca("gắn tay lệch số tiền thì KHÔNG chặn, nhưng phải ghi rõ số lệch")
def _gan_lech():
	# Chặn là sai: khách trả gộp hai bill, hay trả chẵn cho tiền lẻ, là máy
	# chặn mất đường đối soát duy nhất còn lại.
	s = _py("ban_hang.py")
	dung("không còn câu chặn lệch tiền", "Hai số không bằng nhau nên máy" not in s)
	dung("có ghi số lệch vào ghi chú đối soát", "Lệch %s đ so với hoá đơn" in s)


@ca("màn hình khách bày ảnh món, và vẫn giữ nguyên ranh giới riêng tư")
def _man_khach():
	j = _js("25-man-hinh-khach.js")
	dung("gói tin mang ảnh món", "anh: String(m.anh || '')" in j)
	# Ranh giới riêng tư của màn này không được nới ra một ly nào.
	for o in ("don.sdt", "don.khach_ma", "don.khach_hang", "don.khach_no",
	          "don.diemVe", "don.xh", "don.ten"):
		dung("gói tin không đụng %s" % o, o not in j)
	t = _www("man-hinh-khach.html")
	dung("trang khách vẽ ảnh món", 'class="anh"' in t)
	dung("món không có ảnh thì ra ô chữ cái đầu", 'class="chu"' in t)
	dung("có chế độ thử không cần thu ngân", "thu=1" in t)
	dung("trang khách vẫn không gọi API nào", "/api/method" not in t and "frappe.call" not in t)


@ca("mã QR trên màn hình khách vào ĐÚNG tài khoản của điểm bán")
def _qr_dung_tk():
	# Để rỗng mã điểm là ba hàm rơi về tài khoản mặc định, nên màn hình khách
	# bày QR vào tài khoản chung trong khi màn thu ngân bày QR vào tài khoản
	# riêng của điểm. Hai màn một bên một nẻo, tiền về sai chỗ.
	j = _js("25-man-hinh-khach.js")
	dung("nội dung chuyển khoản theo điểm", "posNoiDungCk(don.bill, maDiem, nguon)" in j)
	dung("tài khoản theo điểm", "posTaiKhoan(nguon, maDiem)" in j)
	dung("đường dẫn QR theo điểm", "posQrUrl(nd, phaiThu, nguon, maDiem)" in j)


@ca("màn hình khách KHÔNG bày thông tin khách, dù ở bất kỳ màn nào")
def _man_khach_kin():
	# Anh Việt chốt 01/09/2026 sau đề xuất của Gemini: màn này quay thẳng ra
	# hàng người đang xếp hàng, nên không tên, không số điện thoại, không hạng
	# thành viên, không số dư điểm. Khách vẫn biết mình được ưu đãi qua dòng
	# "Giảm giá thành viên", và biết mình được cộng điểm ở màn Cảm ơn.
	t = _www("man-hinh-khach.html")
	for cam in ("customer-phone", "customer-name", "tier-badge", "customer-avatar",
	            "sdt", "hang_the", "du_sau", "du_truoc"):
		dung("trang khách không có %s" % cam, cam not in t)
	dung("có dòng nói phần giảm đến từ đâu", "g.giam_vi" in t)
	dung("màn Cảm ơn nói số điểm vừa cộng", "điểm vào thẻ thành viên" in t)
	dung("chỉ lấy số điểm vừa cộng, không lấy số dư", "g.diem" in t)


@ca("số điểm gửi sang màn khách là điểm VỪA CỘNG, không phải số dư")
def _diem_vua_cong():
	j = _js("09-tinh-tien-quay.js")
	dung("lấy đúng ô tích của hoá đơn này", "r.diem && r.diem.tich" in j)
	dung("không gửi số dư sang", "du_sau" not in j.split("cfdCamOn")[1][:300])


@ca("ảnh món dùng thẻ img ảnh thật, ô trống không mang chữ cái")
def _anh_that():
	# Anh Việt 01/09/2026: *"hình ảnh sản phẩm phải dùng thẻ img hiển thị ảnh
	# thật, KHÔNG dùng các ô vuông chứa chữ cái"*.
	t = _www("man-hinh-khach.html")
	dung("vẽ ảnh bằng thẻ img", '<img class="anh" src=' in t)
	dung("ô trống không còn chữ cái đầu", "charAt(0).toUpperCase()" not in t)
	# Nhưng ô trống PHẢI còn: 192 trên 506 món đang bán chưa có ảnh, bỏ hẳn ô
	# đi thì ảnh hỏng sẽ ra biểu tượng ảnh vỡ ngay trước mặt khách.
	dung("vẫn còn ô tròn màu nhạt làm lưới đỡ", 'class="chu"' in t)


@ca("logo phải là thẻ img trỏ vào tệp thật, không vẽ lại bằng SVG hay CSS")
def _logo_that():
	# Anh Việt 01/09/2026: *"TUYỆT ĐỐI KHÔNG sử dụng code (SVG/CSS) để tự vẽ
	# lại logo của The Vagabond. Phải sử dụng thẻ img chuẩn"*.
	t = _www("man-hinh-khach.html")
	dung("logo là thẻ img", "'<img' + (lop" in t)
	# Nền xanh robin egg thì phải là bản logo NỀN TRONG SUỐT, không phải bản
	# in nền trắng đục: bản in dán lên nền xanh thành một miếng trắng vuông.
	dung("trỏ vào tệp logo thật", "/files/logo.png" in t)
	dung("có lưới đỡ khi tệp logo hỏng", "/files/logo-in.png" in t)
	# Không được có SVG vẽ chữ trong trang này.
	dung("không có svg tự vẽ trong trang khách", "<svg" not in t.lower())
	dung("không có tên thương hiệu dựng bằng text SVG", "letter-spacing=" not in t)
