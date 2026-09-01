# -*- coding: utf-8 -*-
"""Ca làm việc mở cho MỌI điểm bán, kể cả điểm không có quầy.

Anh Việt 01/09/2026:

    *"Bên chỗ màn Sales online em dựng luôn cái mở ca đóng ca đi để đếm
    tiền. Tiền mặt kênh này có tiền shipper thu về, khách vãng lai cũng có
    thể ghé mua chỗ sales online mua mang đi rồi trả tiền mặt... người thu
    tiền là các bạn sales hoặc Loan Anh là sales manager, rồi cũng làm phiếu
    nộp quỹ hàng ngày hoặc gộp ngày về cho kế toán, y chang hết mà."*

Nghe thì chỉ là gỡ một hàng rào trên màn hình. Thật ra dưới hàng rào đó có
bốn cái bẫy, ba cái đụng tới tiền:

1. Doanh thu ca đọc bằng ô `vgb_quay` trên hoá đơn. Hoá đơn Sales Online để
   TRỐNG ô đó, nên kết quả ra rỗng và bảng đối soát báo toàn bộ tiền thu
   ngân đếm được là "thừa không rõ nguồn". Ca nào cũng lệch, ca nào cũng
   phải bịa lý do.
2. Phiếu nộp quỹ có hai đường: theo CA và theo NGÀY. Đường NGÀY chặn nộp
   trùng bằng ô điểm bán, nhưng đường CA không hề ghi ô đó, nên hai đường
   không thấy nhau. Cùng một ngày của cùng một điểm nộp được hai lần, sổ
   quỹ ghi gấp đôi tiền có thật. Chưa nổ chỉ vì tới nay bảng ca còn rỗng.
3. Bảng đối soát gom cả tiền bên thứ ba đang giữ và tiền khách còn nợ. Ở
   quầy thì phiền, ở Sales Online thì hỏng hẳn vì phần lớn doanh thu là
   tiền các sàn giữ.
4. Danh sách phương thức đếm mù lấy bộ của quầy, nên Sales Online thấy Thẻ
   Payoo và Grab Dine-Out mà thiếu các phương thức app mình dùng thật.

Ca kiểm ở đây chốt cả bốn. Toàn phép thuần và soi chuỗi, không cần Frappe,
không cần site, không cần mạng.
"""

import io
import os

from vagabond import ca_quay
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	return os.path.dirname(os.path.dirname(os.path.abspath(ca_quay.__file__)))


def _py(ten):
	return io.open(os.path.join(_goc(), "vagabond", ten), encoding="utf-8").read()


def _js(ten):
	return io.open(
		os.path.join(_goc(), "vagabond", "public", "js", "bep", ten), encoding="utf-8"
	).read()


# ----------------------------------------------- phép thuần: tách tiền trong két


@ca("lọc trong két: tiền bên thứ ba giữ không vào bảng đối soát")
def _tach_ngoai_ket():
	pt = {"Tiền mặt": 1200000, "Chuyển khoản": 800000, "Grab Dine-Out": 450000, "Công nợ": 300000}
	trong, ngoai = ca_quay.loc_trong_ket(pt, {"Grab Dine-Out", "Công nợ"})
	la("trong két còn hai dòng", sorted(trong), ["Chuyển khoản", "Tiền mặt"])
	la("tiền mặt giữ nguyên", trong["Tiền mặt"], 1200000)
	la("ngoài két đúng hai dòng", sorted(ngoai), ["Công nợ", "Grab Dine-Out"])
	la("Grab giữ 450k", ngoai["Grab Dine-Out"], 450000)


@ca("lọc trong két: không có gì ngoài két thì giữ nguyên cả bảng")
def _tach_rong():
	pt = {"Tiền mặt": 500000}
	trong, ngoai = ca_quay.loc_trong_ket(pt, set())
	la("giữ nguyên", trong, {"Tiền mặt": 500000.0})
	la("ngoài két rỗng", ngoai, {})


@ca("lọc trong két: bảng rỗng không nổ")
def _tach_bang_rong():
	la("None", ca_quay.loc_trong_ket(None, {"Công nợ"}), ({}, {}))
	la("dict rỗng", ca_quay.loc_trong_ket({}, None), ({}, {}))


@ca("đối soát: đơn tặng bị loại ra thì ca không còn lệch giả")
def _tang_khong_lam_lech():
	# Ca thật: bán 2 triệu tiền mặt và tặng một bánh 450k. Thu ngân đếm đúng
	# 2 triệu. Nếu hàng tặng nằm trong bảng thì máy báo thiếu 450k và bắt gõ
	# lý do, mỗi ca một lần.
	pt = {"Tiền mặt": 2000000, "Hàng tặng": 450000}
	trong, _ = ca_quay.loc_trong_ket(pt, {"Hàng tặng"})
	bang = ca_quay.ghep_doi_soat(trong, {"Tiền mặt": 2000000}, 0)
	la("chỉ còn một dòng", len(bang), 1)
	la("không lệch", ca_quay.tong_lech(bang), 0)
	la("không phải gõ lý do", ca_quay.can_ly_do(bang), False)


# --------------------------------------------- máy chủ đọc theo ĐIỂM BÁN


@ca("doanh thu ca KHÔNG được lọc bằng ô quầy trên hoá đơn")
def _khong_loc_bang_vgb_quay():
	# Đây là cái bẫy số một. Lọc `vgb_quay = "SALES"` thì ra rỗng, vì hoá đơn
	# Sales Online để trống ô đó theo quy ước cũ của hệ.
	s = _py("ca_quay.py")
	than = s.split("def _doanh_thu_he_thong(")[1][:2600]
	dung('không còn lọc "vgb_quay": quay', '"vgb_quay": quay' not in than)
	dung("dùng phép lọc theo điểm bán dùng chung", "_loc_diem_ban(" in than)


@ca("ca_quay nạp ban_hang TRONG hàm, không ở đầu tệp")
def _nap_tai_cho():
	# ban_hang mở đầu bằng `import requests`. Đặt ở đầu tệp là cả bộ kiểm thử
	# tầng khung đỏ trên máy CI tay không. Ba ca đỏ ngày 20/08/2026.
	# Ghép chuỗi từ hai mảnh chứ không viết liền: phép chặn tự động ở
	# thu_ma_vach.py lọt qua MỌI tệp ca kiểm và nhặt ra tên mô đun đứng sau
	# chữ "from vagabond import". Viết liền thì chính dòng khẳng định này bị
	# đọc thành một lệnh nhập thật, và ca kiểm đó đỏ oan.
	NAP = "from vagabond " + "import "
	s = _py("ca_quay.py")
	dau = s.split("\ndef ")[0]
	dung("đầu tệp không nạp ban_hang", (NAP + "ban_hang") not in dau)
	dung("nạp trong hàm đọc doanh thu",
		(NAP + "ban_hang as _bh") in s.split("def _doanh_thu_he_thong(")[1][:1800])


@ca("điểm không quầy đọc theo NGÀY hoá đơn, không theo giờ tạo")
def _moc_thoi_gian():
	# Đơn Sales Online về theo nhịp đồng bộ, giờ tạo là giờ máy kéo về chứ
	# không phải giờ bán. Lọc theo giờ tạo thì ca nuốt đơn hôm qua và bỏ sót
	# đơn vừa bán.
	than = _py("ca_quay.py").split("def _doanh_thu_he_thong(")[1][:2600]
	dung("có nhánh theo loại điểm", "_co_quay(" in than)
	dung("điểm có quầy vẫn dùng giờ tạo", '"creation"' in than)
	dung("điểm không quầy dùng ngày hoá đơn", '"posting_date"' in than)


@ca("phương thức đếm mù lấy theo điểm bán, không cứng bộ của quầy")
def _pt_theo_diem():
	s = _py("ca_quay.py")
	dung("có hàm riêng", "def _pt_cua_diem(" in s)
	than = s.split("def _pt_cua_diem(")[1][:1400]
	dung("điểm có quầy lấy bộ quầy", "ten_quay()" in than)
	dung("điểm không quầy lấy bộ online", "ten_online()" in than)
	dung("bỏ phương thức không mang tiền vào két", "_ngoai_ket()" in than)
	dung("tiền mặt luôn còn lại", "TIEN_MAT not in pt" in than)
	dung("tinh_trang gọi hàm đó", "_pt_cua_diem(quay)" in s)


@ca("chốt ca tách tiền ngoài két ra khỏi bảng đối soát")
def _chot_tach_ngoai_ket():
	than = _py("ca_quay.py").split("def chot_ca(")[1][:2600]
	dung("có gọi lọc trong két", "loc_trong_ket(" in than)
	dung("trả phần ngoài két về màn hình", '"ngoai_ket"' in than)


@ca("mở ca có chặn hai người mở cùng lúc")
def _chan_mo_doi():
	# Một quầy vật lý thì chỉ một máy đứng đó. Sales Online thì nhiều người
	# cùng mở app trên nhiều máy, hai ca chồng nhau là doanh thu đếm hai lần.
	than = _py("ca_quay.py").split("def mo_ca(")[1][:2200]
	dung("đếm lại sau khi ghi", "frappe.db.count(CA" in than)
	dung("ném lỗi khi có hơn một ca mở", "> 1" in than)


# ----------------------------------------- chống nộp quỹ hai lần cho một ngày


@ca("phiếu nộp quỹ đường CA có ghi điểm bán")
def _phieu_ca_co_diem():
	# Thiếu ô này thì phiếu lập theo ca không bao giờ khớp bộ lọc chống nộp
	# trùng, và cùng một ngày nộp được hai lần: một theo ca, một theo ngày.
	than = _py("nop_quy.py").split("def tao(")[1][:4200]
	dung("có suy ra điểm bán từ các ca", "diem_ca" in than)
	dung("ghi vào phiếu", '"diem_ban": diem_phieu' in than)


@ca("phiếu nộp quỹ đường CA có chạy phép chống nộp trùng")
def _phieu_ca_chan_trung():
	than = _py("nop_quy.py").split("def tao(")[1][:4200]
	dung("gọi phép tìm phiếu trùm", "_phieu_trum(" in than)
	dung("chặn ca của nhiều điểm trộn vào một phiếu", "len(diem_ca) > 1" in than)


# ------------------------------------------------------- màn hình


@ca("màn tính tiền vẽ khối ca cho mọi điểm bán")
def _man_ve_ca():
	js = _js("09-tinh-tien-quay.js")
	dung("khối ca không còn điều kiện quầy",
		"if (posCoQuay()) html += '<div class=\"card\" id=\"posCaKhoi\"" not in js)
	dung("vẫn còn khối ca", 'id="posCaKhoi"' in js)
	dung("không còn thoát sớm", "if (!posCoQuay()) return;\n  var tt = document" not in js)


@ca("màn tính tiền nghe theo Cài đặt điểm bán về danh sách nguồn")
def _nguon_theo_cai_dat():
	# Trước đó điểm có quầy thì màn bỏ qua cấu hình và nối cứng toàn bộ nguồn
	# sàn của cả hệ. Màn Cài đặt nói một đằng, màn tính tiền làm một nẻo.
	js = _js("09-tinh-tien-quay.js")
	than = js.split("function posDsCheDo(")[1][:2200] if "function posDsCheDo(" in js else js[:0]
	dung("không còn lọc nguồn bằng tên gõ cứng",
		"n.v.indexOf('Tại chỗ') !== 0 && n.v.indexOf('Mang về') !== 0" not in js)
	dung("đọc nguồn của chính điểm", "nguon.filter(" in than or "them.map(bay)" in than)
