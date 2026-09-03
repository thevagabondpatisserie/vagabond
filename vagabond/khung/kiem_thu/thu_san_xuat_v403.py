# -*- coding: utf-8 -*-
"""Đợt hai của phantom chuẩn (v403, 03/09/2026).

Sau khi v402 chạy trên site, còn 13 công thức giữ lá Egg yolk, Gelatine
mass, Coffee liquid vì dòng cha trỏ vào công thức con phiên bản cũ đã tắt.
Các ca ở đây canh phép chọn công thức con và phép chia loại lá hỏng, để báo
cáo sau migrate nói đúng cái nào là lỗi máy, cái nào bếp phải khai công thức,
cái nào không sao (nước).
"""

import io
import os

from vagabond.patches import no_phantom_chuan as np
from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _goc(ten):
	return io.open(os.path.join(os.path.dirname(GOI), ten), encoding="utf-8").read()


DANG_CHAY = {"BOM-A-002", "BOM-B-001"}


@ca("v403 dòng cha đang trỏ công thức đang chạy thì giữ nguyên")
def _giu():
	la("giữ bản đang chạy", np.chon_bom_con("BOM-A-002", "BOM-A-002", DANG_CHAY), "BOM-A-002")
	# Đang trỏ bản đang chạy nhưng không phải bản mặc định: vẫn giữ, không ép.
	la("giữ bản đang chạy không mặc định", np.chon_bom_con("BOM-B-001", "BOM-B-002", DANG_CHAY), "BOM-B-001")


@ca("v403 dòng cha trỏ công thức đã tắt thì trỏ lại về bản mặc định")
def _tro_lai():
	la("trỏ lại bản mặc định", np.chon_bom_con("BOM-A-001", "BOM-A-002", DANG_CHAY), "BOM-A-002")


@ca("v403 dòng cha chưa trỏ thì lấy bản mặc định, không có mặc định thì để yên")
def _chua_tro():
	la("chưa trỏ thì lấy mặc định", np.chon_bom_con("", "BOM-A-002", DANG_CHAY), "BOM-A-002")
	la("không có gì thì None", np.chon_bom_con(None, None, DANG_CHAY), None)
	la("tắt mà không có mặc định thì None", np.chon_bom_con("BOM-A-001", None, DANG_CHAY), None)


@ca("v403 lá hỏng chia ba loại, nước không tính là hỏng")
def _chia_loai():
	kq = np.phan_loai_la(
		["NVL-BOT", "NUOC", "GELATINE", "CARAMEL", "TRUNG-TAT", "GELATINE"],
		phantom_co_bom={"GELATINE"},
		phantom_khong_bom={"CARAMEL"},
		tat={"TRUNG-TAT"})
	la("ba loại", kq, {"phantom_con_bom": ["GELATINE"], "phantom_chua_co_bom": ["CARAMEL"],
		"tat": ["TRUNG-TAT"]})


@ca("v403 bảng nổ sạch thì báo cáo rỗng, không in loại trống")
def _sach():
	la("sạch", np.phan_loai_la(["NVL-BOT", "NUOC"], {"GELATINE"}, {"CARAMEL"}, set()), {})
	la("rỗng", np.phan_loai_la([], {"GELATINE"}, set(), set()), {})


@ca("v403 patch phantom chuẩn được ghi lại vào patches.txt để chạy đợt hai")
def _dang_ky():
	dong = [d.strip() for d in _goc("vagabond/patches.txt").splitlines()]
	dung("có dòng đợt hai", "vagabond.patches.no_phantom_chuan #v403" in dong)
	dung("dòng đợt một còn nguyên", "vagabond.patches.no_phantom_chuan #v402" in dong)
