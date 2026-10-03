# -*- coding: utf-8 -*-
"""v564: bỏ ảo một mã hàng (anh Việt chốt 03/10/2026, việc số 2).

Phép THUẦN của bo_ao.py; giao diện chạy thật ở hanh_vi/bo_ao_564.js.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
from vagabond import bo_ao as B  # noqa: E402


@ca("v564: dòng cha của mã bỏ ảo thì chặn nổ, bỏ công thức con, bỏ cờ phantom; chạy lại không đổi gì")
def _dong_cha():
	la("dong phantom", B.viec_dong_cha(0, "BOM-BTP-001", 1), {"do_not_explode": 1, "bom_no": "", "is_phantom_item": 0})
	la("dong da dung", B.viec_dong_cha(1, "", 0), {})
	la("chi thieu chan no", B.viec_dong_cha(0, "", 0), {"do_not_explode": 1})
	la("bom_no chi co khoang trang coi nhu rong", B.viec_dong_cha(1, "  ", 0), {})


@ca("v564: mã theo lô hay số máy thì dừng, báo làm tay; mã lạ thì báo không tìm thấy")
def _chan():
	dung("theo lo", "làm tay" in B.cau_chan("M1", 1, 0, False))
	dung("theo so may", "theo số máy" in B.cau_chan("M1", 0, 1, False))
	dung("khong co ma", "Không tìm thấy" in B.cau_chan("M1", 0, 0, True))
	la("binh thuong thi duoc", B.cau_chan("M1", 0, 0, False), "")


@ca("v564: danh sách giữ tồn đọc an toàn, thêm không trùng")
def _giu_ton():
	la("rong", B.doc_giu_ton(None), [])
	la("rac", B.doc_giu_ton("{khong phai json"), [])
	la("khong phai danh sach", B.doc_giu_ton('{"a":1}'), [])
	la("doc va sap xep", B.doc_giu_ton('["B2","A1","A1",""]'), ["A1", "B2"])
	la("them khong trung", B.them_giu_ton(["A1"], "A1"), ["A1"])
	la("them moi", B.them_giu_ton(["A1"], "B2"), ["A1", "B2"])


@ca("v564: câu tổng kết nói rõ vượt chặn ERPNext, mã đã có tồn thì không làm gì")
def _tong_ket():
	dung("da co ton", "không cần" in B.tong_ket("M1", 1, 0, 0, 0, False))
	c = B.tong_ket("M1", 0, 1, 3, 4, True)
	dung("so lieu", "3 dòng" in c and "dựng lại 4" in c)
	dung("noi vuot chan", "vượt chặn" in c)
	dung("khong vuot chan thi khong noi", "vượt chặn" not in B.tong_ket("M1", 0, 1, 3, 4, False))


@ca("v564: chuyển Phantom và patch phantom chừa mã đã bỏ ảo, không biến về ảo")
def _chua_giu_ton():
	import io
	import os

	goc = os.path.dirname(os.path.abspath(B.__file__))
	ph = io.open(os.path.join(goc, "phantom.py"), encoding="utf-8").read()
	pa = io.open(os.path.join(goc, "patches", "no_phantom_chuan.py"), encoding="utf-8").read()
	# Do chuoi chi chot loi chua: hai ham do chay tren site that (can bang BOM).
	dung("phantom bo ma giu ton khoi BTP", "- giu)" in ph and "chang_cua_ma[ma] = CHANG_C1" in ph)
	dung("patch chuyen ma bo qua giu ton", "or b.item in giu:" in pa)
	dung("patch gan co coi giu ton la giu ton", "| set(danh_sach_giu_ton())" in pa)
