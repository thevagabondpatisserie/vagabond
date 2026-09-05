# -*- coding: utf-8 -*-
"""Ca kiểm cho đường đẩy mã hàng sang Pancake (issue 204, bản gia cố).

BỐI CẢNH
--------
Uyên phản ánh bấm nút đồng bộ sang Pancake mà không thấy chạy. Nguyên nhân
lịch sử của lần bấm 31/08 tới nay CHƯA xác định được, vì đường Uyên bấm nằm
ở một Server Script không nằm trong git. Nhưng khi rà lại phần trong git thì
Codex chỉ ra năm chỗ hỏng thật, và tệp này canh cả năm.

NĂM ĐIỀU MỖI CA DƯỚI ĐÂY CANH
-----------------------------
1. Tìm phải khớp KHÍT mã, không lấy mã chứa chuỗi đó. Pancake tìm kiểu chứa,
   nên hỏi SLOP00015 sẽ trả về cả SLOP00015C và SLOP00015S. Ba mã đó là ba
   thứ khác nhau. Danh mục thật ngày 05/09 có đúng ba mã này.
2. Hai bản trở lên cùng một mã là XUNG ĐỘT, không phải "đã có". Danh mục
   thật đang có mã "1" mang 11 sản phẩm và mã "2" mang 6 sản phẩm.
3. Chưa rõ kết quả thì KHÔNG được thử lại. Đây là ca quan trọng nhất: gửi
   lệnh tạo xong mà mạng đứt, rồi bấm lại, là đẻ ra mã thứ hai bên Pancake.
4. Giá 0 không được âm thầm đẩy đi.
5. Mã ngừng dùng hoặc không phải hàng bán không được xuất bản.

Mọi ca chạy trên phép THUẦN và trên văn bản tệp: không cần Frappe, không
cần site, không cần mạng, không cần thư viện requests.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.pancake_ket_qua import (
	KQ_CHUA_CO, KQ_CHUA_RO, KQ_DA_CO, KQ_DA_TAO, KQ_LOI, KQ_THIEU_GIA,
	KQ_XUNG_DOT, duoc_tao, duoc_thu_lai, duoc_xuat_ban, gia_dung_de_day,
	khop_chinh_xac, thong_bao, xep_ket_qua_tim,
)

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(*ten):
	with io.open(os.path.join(GOI, *ten), encoding="utf-8") as f:
		return f.read()


SP = _doc("pancake_sp.py")
DM = _doc("danh_muc.py")
JS = _doc("public", "js", "bep", "17-cai-dat.js")


# --------------------------------------------- 1. Khop khit, khong khop chua


@ca("tim ma: chi lay ban khop KHIT, khong lay ma chua chuoi do")
def _khop_khit():
	# Ba ma nay deu co that ben Pancake ngay 05/09/2026.
	ds = [
		{"display_id": "SLOP00015"},
		{"display_id": "SLOP00015C"},
		{"display_id": "SLOP00015S"},
	]
	la("hoi SLOP00015 chi ra mot ban", len(khop_chinh_xac(ds, "SLOP00015")), 1)
	la("hoi SLOP00015C chi ra mot ban", len(khop_chinh_xac(ds, "SLOP00015C")), 1)
	la("hoi ma khong co thi ra rong", len(khop_chinh_xac(ds, "SLOP00099")), 0)


@ca("tim ma: khong phan biet hoa thuong va khoang trang")
def _hoa_thuong():
	ds = [{"display_id": " bawc00148 "}]
	la("thuong va co khoang trang van khop", len(khop_chinh_xac(ds, "BAWC00148")), 1)
	la("ma rong thi khong khop gi", len(khop_chinh_xac(ds, "")), 0)
	la("ma rong thi khong khop gi ke ca None", len(khop_chinh_xac(ds, None)), 0)


# ------------------------------------------- 2. Nhieu ban la XUNG DOT


@ca("nhieu ban cung mot ma la xung dot, khong phai da co")
def _xung_dot():
	la("khong ban nao", xep_ket_qua_tim(0), KQ_CHUA_CO)
	la("dung mot ban", xep_ket_qua_tim(1), KQ_DA_CO)
	la("hai ban", xep_ket_qua_tim(2), KQ_XUNG_DOT)
	# Danh muc that ngay 05/09: ma "1" mang 11 san pham, ma "2" mang 6.
	la("muoi mot ban nhu ma so 1", xep_ket_qua_tim(11), KQ_XUNG_DOT)
	la("sau ban nhu ma so 2", xep_ket_qua_tim(6), KQ_XUNG_DOT)


@ca("chi trang thai chua co moi duoc phep tao")
def _chi_chua_co():
	dung("chua co thi tao", duoc_tao(KQ_CHUA_CO))
	la("da co thi khong tao", duoc_tao(KQ_DA_CO), False)
	la("xung dot thi khong tao", duoc_tao(KQ_XUNG_DOT), False)
	la("chua ro thi khong tao", duoc_tao(KQ_CHUA_RO), False)
	la("loi thi cung khong tu tao lai o day", duoc_tao(KQ_LOI), False)


# ------------------------- 3. DIEU CAM: chua ro thi KHONG duoc thu lai


@ca("chua ro ket qua thi KHONG duoc thu lai")
def _chua_ro():
	# Day la ca quan trong nhat cua tep. Gui lenh tao xong ma mang dut thi
	# Pancake rat co the DA nhan. Thu lai mu la de ra ma thu hai.
	la("chua ro khong duoc thu lai", duoc_thu_lai(KQ_CHUA_RO), False)
	dung("loi that thi duoc thu lai", duoc_thu_lai(KQ_LOI))
	la("da tao roi thi khong thu lai", duoc_thu_lai(KQ_DA_TAO), False)
	la("xung dot khong duoc thu lai", duoc_thu_lai(KQ_XUNG_DOT), False)


@ca("dut mang sau khi gui lenh tao phai thanh chua ro, khong phai loi")
def _dut_mang():
	# Soi van ban: nhanh bat loi quanh requests.post phai tra ve KQ_CHUA_RO.
	i = SP.find("r = requests.post(")
	dung("tim thay cho goi tao", i > 0)
	doan = SP[i:i + 1200]
	dung("co bat loi quanh cho goi tao", "except Exception:" in doan)
	dung("bat duoc thi tra ve chua ro", "KQ_CHUA_RO" in doan)
	la("khong duoc tra ve loi o cho nay", "KQ_LOI" in doan.split("except Exception:", 1)[1][:400], False)


@ca("quet do khong duoc doc thanh ma chua ton tai")
def _quet_do():
	dung("ham tim tra ve ca co quet du chua", "return [], False" in SP)
	dung("quet du thi tra ve True", "return kq.khop_chinh_xac(ds, ma), True" in SP)
	dung("cham tran trang thi bao chua du", "return kq.khop_chinh_xac(ds, ma), False" in SP)
	dung("ben goi co chan khi quet do", "if not du:" in SP)


# --------------------------------------------------- 4. Gia


@ca("gia 0 khong duoc am tham day di")
def _gia_khong():
	duoc, vi_sao = gia_dung_de_day(0, False)
	la("gia 0 thi chan", duoc, False)
	la("va noi ro vi sao", vi_sao, KQ_THIEU_GIA)
	duoc2, _ = gia_dung_de_day(0, True)
	dung("co y thi van cho", duoc2)
	duoc3, _ = gia_dung_de_day(550000, False)
	dung("co gia thi cho", duoc3)
	duoc4, _ = gia_dung_de_day(None, False)
	la("gia rong cung bi chan", duoc4, False)
	duoc5, _ = gia_dung_de_day("hong", False)
	la("gia hong cung bi chan", duoc5, False)


@ca("gia lay tu bang gia ban truoc, khong lay thang standard_rate")
def _gia_bang():
	dung("co doc bang gia ban", "selling_price_list" in SP)
	dung("co doc Item Price", '"Item Price"' in SP)
	dung("standard_rate chi la duong lui", "it.standard_rate" in SP)


# ------------------------------------ 5. Ma ngung dung, ma khong ban


@ca("ma ngung dung hoac khong phai hang ban thi khong xuat ban")
def _ngung_dung():
	la("ngung dung thi khong", duoc_xuat_ban(1, 1), False)
	la("khong phai hang ban thi khong", duoc_xuat_ban(0, 0), False)
	dung("hang ban dang chay thi duoc", duoc_xuat_ban(0, 1))
	la("vua ngung vua khong ban", duoc_xuat_ban(1, 0), False)


@ca("may chu chot co day_duoc, khong de man hinh tu doan")
def _co_day_duoc():
	dung("gan_day tra ve co day_duoc", '"day_duoc"' in DM or "day_duoc" in DM)
	dung("pancake_sp chan lan nua luc day that", "duoc_xuat_ban" in SP)


# ------------------------------------------- Khoa chong hai nguoi cung bam


@ca("co khoa theo shop va ma, dung phep nguyen tu")
def _khoa():
	dung("co ham giu khoa", "def _giu_khoa" in SP)
	dung("dung setnx la phep nguyen tu", "setnx" in SP)
	dung("khoa co han", "expire" in SP)
	dung("co nha khoa trong finally", "finally:" in SP and "_nha_khoa" in SP)


# ------------------------------------------- Man hinh: bo cau bao mac dinh


@ca("man hinh khong con roi ve cau bao thanh cong mac dinh")
def _bo_xong():
	la("khong con chu Xong. mac dinh", "|| 'Xong.'" in JS, False)
	dung("thay bang cau chua xac minh", "Chưa xác minh" in JS)


@ca("man hinh co duong tim lai ma cu de day")
def _tim_ma_cu():
	dung("co o tim", "dmTimMa" in JS)
	dung("co goi gan_day", "vagabond.danh_muc.gan_day" in JS)
	dung("co nut kiem lai", "kiem_ma_tren_pancake" in JS)
	dung("co phan trang", "dmTimTrang" in JS)
	# Chua ro khong duoc to xanh, vi to xanh la bao thanh cong.
	dung("chua ro to mau canh bao", "chua_ro" in JS)


@ca("khong co cho nao tu bam day lai sau khi chua ro")
def _khong_tu_day_lai():
	# Soi ham day mot ma: sau khi nhan ket qua, khong duoc tu goi lai chinh no.
	i = JS.find("async function dmDayMot(")
	dung("tim thay ham day mot ma", i > 0)
	than = JS[i:JS.find("async function dmKiemMot(")]
	la("khong tu goi lai chinh no", than.count("dmDayMot("), 1)


@ca("nut Kiem lai chi doc, khong tao gi")
def _kiem_chi_doc():
	i = DM.find("def kiem_ma_tren_pancake")
	dung("tim thay cua kiem lai", i > 0)
	than = DM[i:i + 700]
	dung("goi ham chi doc", "trang_thai_tren_pancake" in than)
	la("khong goi ham tao", "tao_tren_pancake" in than, False)


# ------------------------------------------------------- Cau chu cho nguoi


@ca("cau bao noi dung viec, khong bia thanh cong")
def _cau_bao():
	dung("xung dot noi ro so ban", "2" in thong_bao(KQ_XUNG_DOT, "SLOP00016", 2))
	dung("chua ro noi la chua xac minh", "CHƯA XÁC MINH" in thong_bao(KQ_CHUA_RO, "X"))
	dung("chua ro bao dung bam tao lan nua",
		"đừng bấm tạo lần nữa" in thong_bao(KQ_CHUA_RO, "X"))
	dung("trang thai la thi van noi chua xac minh",
		"Chưa xác minh" in thong_bao("troi oi", "X"))
	dung("da tao thi noi da tao", "Đã tạo" in thong_bao(KQ_DA_TAO, "X"))
