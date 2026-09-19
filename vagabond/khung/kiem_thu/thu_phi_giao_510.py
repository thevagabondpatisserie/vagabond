# -*- coding: utf-8 -*-
"""v510: phi giao thu cua khach la MOT dong qty 1, khong phai 4 x 1.000.

Loan Anh 18/09/2026: ben Pancake bam phi van chuyen 1.000 d x so luong, sang
app mon "Phi Dich Vu Van Chuyen" chi co nut cong so luong nen bill ra
"4 x 1.000" va hoa don dien tu chep y nguyen. Sua bang cach gom ve MOT nguon:
phi_giao.gom chay tren moi duong ghi (lap don tay, sua bill), man quay va
man sua bill thi hoi so tien thay vi them dong.
"""

import io
import os
import re

from vagabond import phi_giao
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(*duong):
	return io.open(os.path.join(GOC, *duong), encoding="utf-8").read()


@ca("v510: phi giao 4 x 1.000 gom thanh 1 x 4.000")
def _gom_so_luong():
	rows = [
		{"item_code": "BANH01", "qty": 4, "rate": 160000},
		{"item_code": "DVBH00001", "qty": 4, "rate": 1000},
	]
	kq = phi_giao.gom(rows, 0)
	la("còn hai dòng", len(kq), 2)
	la("bánh giữ nguyên", kq[0], rows[0])
	la("phí giao qty 1", kq[1]["qty"], 1)
	la("phí giao rate bằng tổng tiền", kq[1]["rate"], 4000)


@ca("v510: nhieu dong phi giao va o phi giao rieng cong don, dat cuoi")
def _cong_don():
	rows = [
		{"item_code": "DVBH00001", "qty": 2, "rate": 5000, "description": "Phí giao\nghi chú"},
		{"item_code": "BANH01", "qty": 1, "rate": 100000},
		{"item_code": "dvbh00001", "qty": 1, "rate": 3000, "amount": 3000},
	]
	kq = phi_giao.gom(rows, 7000)
	la("hai dòng", len(kq), 2)
	la("bánh lên đầu", kq[0]["item_code"], "BANH01")
	la("tổng 10.000 + 3.000 + 7.000", kq[1]["rate"], 20000)
	la("qty 1", kq[1]["qty"], 1)
	la("mã chuẩn hoa", kq[1]["item_code"], "DVBH00001")
	la("giữ description dòng đầu", kq[1]["description"], "Phí giao\nghi chú")
	dung("bỏ amount cũ để máy tính lại", "amount" not in kq[1])


@ca("v510: khong co phi giao thi khong sinh dong, phi 0 thi bo dong")
def _khong_phi():
	rows = [{"item_code": "BANH01", "qty": 1, "rate": 100000}]
	la("không thêm gì", phi_giao.gom(rows, 0), rows)
	la("rows rỗng phí ship 0", phi_giao.gom([], 0), [])
	la("chỉ phí ship", phi_giao.gom([], 12000), [{"item_code": "DVBH00001", "qty": 1, "rate": 12000.0}])
	la("dòng phí giao 0 đồng bị bỏ", phi_giao.gom([{"item_code": "DVBH00001", "qty": 3, "rate": 0}], 0), [])
	la("chuỗi số vẫn cộng được", phi_giao.gom([{"item_code": "DVBH00001", "qty": "2", "rate": "1500"}], "500")[0]["rate"], 3500)


@ca("v510: moi duong ghi hoa don deu goi phi_giao.gom - mot nguon duy nhat")
def _mot_nguon():
	s = _doc("vagabond", "ban_hang.py")
	dung("tao_don_tay gom", re.search(r"def tao_don_tay\(.*?_pg\.gom\(rows, phi_ship\)", s, re.S) is not None)
	dung("pos_sua gom", re.search(r"giu_dong_sua\(si, r, d\)\)\n\s*# Phi giao gom.*?_pg\.gom\(rows, 0\)", s, re.S) is not None)
	dung("không còn chỗ tự append dòng phí giao qty 1 từ phi_ship", "rows.append({\"item_code\": _item_phi_giao(), \"qty\": 1, \"rate\": flt(phi_ship)})" not in s)
	dung("phi_giao.py không import frappe", "frappe" not in _doc("vagabond", "phi_giao.py"))
	la("mã item khớp ban_hang", phi_giao.MA_PHI_GIAO, re.search(r'MA_PHI_GIAO = "([^"]+)"', s).group(1))


@ca("v510: man quay va man sua bill hoi SO TIEN khi chon mon phi giao")
def _man_hinh():
	q = _doc("vagabond", "public", "js", "bep", "09-tinh-tien-quay.js")
	dung("có hàm nhận diện", "function posLaPhiGiao(ma)" in q)
	dung("mã khớp máy chủ", "var POS_MA_PHI_GIAO = '%s'" % phi_giao.MA_PHI_GIAO in q)
	dung("chọn món phí giao thì hỏi tiền, không thêm dòng", "if (posLaPhiGiao(o.value)) { posHoiPhiGiao(); return 0; }" in q)
	dung("số tiền ghi vào ô Phí giao", "posDon.ship = n ? String(n) : ''" in q)
	dung("dòng phí giao trong giỏ có lời nhắc sửa số tiền", "không bấm cộng số lượng" in q)
	b = _doc("vagabond", "public", "js", "bep", "10-bill-quay.js")
	dung("sửa bill: phí giao hỏi tiền", "if (posLaPhiGiao(o.value)) {" in b and "posSua.mon[c].qty = 1" in b)


@ca("v510 Codex F1: ha tien phi giao tren bill da in tam tinh phai xin OTP")
def _otp_ha_phi_giao():
	# Tai hien finding Codex tren PR #347: hai danh sach deu co DVBH00001 qty 1,
	# _theo_ma chi so so luong nen khong thay "bot", pos_sua ghi rate thap hon
	# ma khong OTP. Ca nay dung DUNG chuoi: si da in tam tinh, muc gioi_han.
	from unittest.mock import patch

	from vagabond import quyen_quay

	si = {"vgb_tam_tinh": 1, "items": [{"item_code": "DVBH00001", "qty": 1, "rate": 4000}]}
	with patch.object(quyen_quay, "muc", return_value="gioi_han"), patch.object(
		quyen_quay.frappe.db, "get_value", return_value="Phí Dịch Vụ Vận Chuyển", create=True
	):
		can, vs = quyen_quay.can_otp(si, [{"item_code": "DVBH00001", "qty": 1, "rate": 3000}])
		dung("hạ 4.000 xuống 3.000 phải OTP", can)
		dung("lý do nói tới phí giao", "Phí Dịch Vụ Vận Chuyển" in vs or "phí" in vs.lower())
		can2, _ = quyen_quay.can_otp(si, [{"item_code": "DVBH00001", "qty": 1, "rate": 5000}])
		dung("tăng lên 5.000 không cần OTP", not can2)
		can3, _ = quyen_quay.can_otp(si, [{"item_code": "DVBH00001", "qty": 1, "rate": 4000}])
		dung("giữ nguyên không cần OTP", not can3)


@ca("v510 Codex F2: man sua bill THAY so tien phi giao, khong cong don")
def _thay_khong_cong():
	b = _doc("vagabond", "public", "js", "bep", "10-bill-quay.js")
	dung("không còn phép cộng rate*qty + n", "* flt0(posSua.mon[c].qty) + n" not in b)
	dung("ghi đè rate bằng số vừa nhập", "posSua.mon[c].rate = n; posSua.mon[c].qty = 1;" in b)
	dung("hộp thoại điền sẵn số hiện có", "posPhiGiaoHienCo(posSua.mon)" in b)
