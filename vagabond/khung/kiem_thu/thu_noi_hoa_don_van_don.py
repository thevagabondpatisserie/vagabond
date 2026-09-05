# -*- coding: utf-8 -*-
"""Ca kiểm cho việc nối lại ô hoá đơn của vận đơn đã tồn tại (issue 201).

BỐI CẢNH
--------
Anh Việt báo gấp 05/09/2026: Sales mất niềm tin vì đơn Pancake đồng bộ về
thiếu thông tin. Đếm được tám ngày liền, từ 29/08 tới 05/09, 391 vận đơn
mà không một cái nào nối được hoá đơn, kể cả những đơn thực sự có hoá đơn.

Nguyên nhân: ô hoá đơn chỉ được gán đúng một lần, lúc tạo vận đơn mới.
Nhịp vận đơn chạy 5 phút một lần, nhịp hoá đơn chạy 30 phút một lần, nên
vận đơn gần như luôn ra đời trước hoá đơn, tìm không thấy gì, và không có
đường nào quay lại lấp.

BỐN ĐIỀU MỖI CA DƯỚI ĐÂY CANH
-----------------------------
1. Ô trống thì được lấp.
2. Ô đã có thì KHÔNG bị ghi đè, kể cả khi tìm thấy một hoá đơn khác.
3. Vận đơn đã đóng sổ thì không nối.
4. **Lấp hoá đơn KHÔNG được làm đổi tiền thu hộ.** Đây là ca quan trọng
   nhất của tệp này, đọc phần dưới để biết vì sao.

VÌ SAO CÓ CA THỨ TƯ
-------------------
Bản chẩn đoán đầu tiên của phiên này đã đề xuất: lấp hoá đơn xong thì tính
lại tiền thu hộ theo hoá đơn, vì 51 trên 57 vận đơn ngày 05/09 có tiền thu
hộ bằng 0 và trông như là sai. Codex phản đối, và Codex đúng.

Soi lại 42 đơn có tiền thu hộ bằng 0 và có hoá đơn khớp: cả 42 hoá đơn đều
còn ở dạng chưa ghi sổ, nên số còn lại trên hoá đơn mặc định bằng tổng tiền
và không nói lên điều gì về việc khách đã trả hay chưa. Phương thức thanh
toán của chúng là chuyển khoản 33, OnePay 5, thẻ 2, công nợ 1, hàng tặng 1.
Không một đơn nào là tiền mặt. Shipper không phải thu đồng nào là ĐÚNG.

Hàm _cod_tu_don đã chặn việc này từ trước, và ghi chú của nó nhắc lại sự cố
13/08/2026: đơn chị Hậu 700.000 và đơn Oshima 1.480.000 hiện trong đối soát
COD dù khách đã chuyển khoản. Tính lại tiền thu hộ theo hoá đơn là dựng lại
đúng cái bẫy đó, lần này trên 42 đơn cùng một lúc.

Ca thứ tư đọc thẳng văn bản tệp van_don.py để chốt điều cấm lại, để sau này
không ai vô tình mở nó ra.

Mọi ca chạy trên phép THUẦN và trên văn bản tệp: không cần Frappe, không
cần site, không cần mạng, không cần thư viện requests.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.van_don import (
	TT_KHONG_NOI_HOA_DON, nen_noi_hoa_don, nen_tim_hoa_don,
)

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


VD = _doc("van_don.py")

# Cat rieng than ham _noi_lai_hoa_don de soi. Cat toi dinh nghia ham ke tiep.
_TU = VD.split("def _noi_lai_hoa_don(", 1)
THAN = _TU[1].split("\ndef ", 1)[0] if len(_TU) > 1 else ""


# ------------------------------------------------- 1. O trong thi duoc lap


@ca("o hoa don trong thi duoc lap")
def _o_trong():
	dung("khong co gi thi di tim", nen_tim_hoa_don("", "Chờ giao"))
	dung("None cung la trong", nen_tim_hoa_don(None, "Chờ giao"))
	dung("chi co khoang trang van la trong", nen_tim_hoa_don("   ", "Chờ giao"))
	dung("tim thay hoa don thi lap", nen_noi_hoa_don("", "ACC-SINV-2026-00123", "Chờ giao"))


@ca("lap duoc cho ca don cho khach lay")
def _cho_khach_lay():
	# Chin ma don anh Viet gui deu o trang thai nay, deu diem TCV. Nhanh cap
	# nhat cu chi chay cho "Cho giao" va "Dang giao", nen nhom nay truot het.
	dung("cho khach lay van duoc noi",
		nen_noi_hoa_don("", "ACC-SINV-2026-00123", "Chờ khách lấy"))
	dung("da giao roi van duoc noi",
		nen_noi_hoa_don("", "ACC-SINV-2026-00123", "Đã giao"))
	dung("khong giao duoc van duoc noi",
		nen_noi_hoa_don("", "ACC-SINV-2026-00123", "Không giao được"))


# ------------------------------------------ 2. O da co thi khong ghi de


@ca("o hoa don da co thi khong bao gio bi ghi de")
def _khong_ghi_de():
	la("da co thi khong di tim nua", nen_tim_hoa_don("ACC-SINV-2026-00001", "Chờ giao"), False)
	# Nguoi gan tay mot to khac han: van phai giu nguyen cua ho.
	la("tim thay to khac cung khong duoc thay",
		nen_noi_hoa_don("ACC-SINV-2026-00001", "ACC-SINV-2026-99999", "Chờ giao"), False)


@ca("khong tim thay hoa don thi khong lap gi")
def _khong_tim_thay():
	la("si rong", nen_noi_hoa_don("", "", "Chờ giao"), False)
	la("si None", nen_noi_hoa_don("", None, "Chờ giao"), False)
	la("si chi co khoang trang", nen_noi_hoa_don("", "  ", "Chờ giao"), False)


# ------------------------------------------- 3. Van don da dong so


@ca("van don da dong so thi khong noi")
def _dong_so():
	for tt in TT_KHONG_NOI_HOA_DON:
		la("trang thai %s khong di tim" % tt, nen_tim_hoa_don("", tt), False)
		la("trang thai %s khong lap" % tt,
			nen_noi_hoa_don("", "ACC-SINV-2026-00123", tt), False)


@ca("hai chu huy that su nam trong bang")
def _hai_chu_huy():
	# Doctype Van Don khai trang thai la "Huỷ" co dau. Cac cho khac trong
	# repo con viet "Da huy" khong dau. Bang phai om ca hai cach viet, neu
	# khong thi mot to da huy van bi noi lai hoa don.
	dung("co ban co dau", "Huỷ" in TT_KHONG_NOI_HOA_DON)
	dung("co ban khong dau", "Da huy" in TT_KHONG_NOI_HOA_DON)


# ------------------------- 4. DIEU CAM: khong duoc dung toi tien thu ho


@ca("lap hoa don khong duoc lam doi tien thu ho")
def _cam_dung_tien_thu_ho():
	dung("tim thay than ham _noi_lai_hoa_don", len(THAN) > 200)
	# Than ham chi duoc phep ghi DUY NHAT o hoa_don. Thay chu tien_thu_ho
	# trong phan lenh la co nguoi da mo lai cai bay 13/08.
	lenh = []
	for dong in THAN.split("\n"):
		nghia = dong.split("#", 1)[0]
		lenh.append(nghia)
	ma = "\n".join(lenh)
	# Bo phan docstring, vi docstring co nhac ten o do de giai thich dieu cam.
	if ma.count('"""') >= 2:
		dau = ma.index('"""')
		cuoi = ma.index('"""', dau + 3) + 3
		ma = ma[:dau] + ma[cuoi:]
	la("phan lenh khong nhac tien_thu_ho", "tien_thu_ho" in ma, False)
	la("phan lenh khong goi _cod_tu_don", "_cod_tu_don" in ma, False)


@ca("chi ghi dung mot o vao co so du lieu")
def _chi_mot_o():
	# set_value duy nhat, va o duoc ghi phai la "hoa_don".
	la("chi mot lenh ghi", THAN.count("frappe.db.set_value"), 1)
	dung("o duoc ghi la hoa_don", '"hoa_don", si_name' in THAN)


@ca("moi lan lap deu ghi nhat ky dong bo")
def _co_nhat_ky():
	dung("co goi nhat ky", "nhat_ky.ghi_nhieu" in THAN)
	dung("viec ghi ro rang", "Noi lai hoa don" in THAN)


# ------------------------------------------- Vong dong bo goi dung cho


@ca("vong dong bo co doc o hoa don ve va co goi ham noi lai")
def _vong_dong_bo():
	# Khong doc o hoa_don ve thi khong the biet no dang trong hay da co, va
	# ham noi lai se lap de len gia tri nguoi ta gan tay.
	dung("co doc o hoa_don trong vong", '\t\t\t\t"hoa_don",\n' in VD)
	dung("co goi ham noi lai", "_noi_lai_hoa_don(cu, pid," in VD)
	dung("co dem so lan noi", '"noi_hoa_don": noi_hd' in VD)
