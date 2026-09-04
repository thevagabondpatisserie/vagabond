# -*- coding: utf-8 -*-
"""Ba lỗi vừa còn lại của phân hệ sản xuất (v409, 04/09/2026).

Ba việc trong bản rà v397 chưa ai sửa, nay gom một đợt:

1. Hoàn tất một lệnh làm hai lần thì cả hai mẻ dùng chung một số lô, mẻ sau
   mang ngày giờ sản xuất và hạn dùng của mẻ đầu.
2. `_bep_cua_mon` chỉ đọc ô Bếp phụ trách trên MÓN, món chưa khai là trả
   None và phiếu rơi về kho mặc định của ERPNext chứ không về kho bếp, trong
   khi app thì lâu nay vẫn suy theo NHÓM HÀNG.
3. Bảy hàm mở ra ngoài của btp.py chưa có tên trong danh sách cửa ngõ, tức
   một decorator bám nhầm là không phép kiểm nào bắt được.
"""

import io
import os

from vagabond import kho_san_xuat as ksx
from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _js(ten):
	return io.open(os.path.join(GOI, "public", "js", "bep", ten), encoding="utf-8").read()


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


def _goc(ten):
	return io.open(os.path.join(os.path.dirname(GOI), ten), encoding="utf-8").read()


# ------------------------------------------------- bếp suy từ nhóm hàng


@ca("v409 đọc được mã bếp lẫn tên bếp người gõ, không phân biệt hoa thường")
def _doc_chu():
	la("mã thẳng", ksx.bep_tu_chuoi("pastry"), "pastry")
	la("có hoa có khoảng trắng", ksx.bep_tu_chuoi("  Baker "), "baker")
	la("tên hiển thị", ksx.bep_tu_chuoi("Bếp Pastry"), "pastry")
	la("để trống", ksx.bep_tu_chuoi(""), None)
	la("chữ lạ", ksx.bep_tu_chuoi("Bếp bánh mì"), None)


@ca("v409 nhóm hàng chưa khai bếp thì leo lên nhóm cha mà lấy")
def _leo_nhom():
	bep = {"Bánh": "Pastry"}
	cha = {"Bánh Ổ": "Bánh", "Entremets": "Bánh Ổ"}
	la("chính nhóm có khai", ksx.bep_theo_nhom("Bánh", bep, cha), "pastry")
	la("cha có khai", ksx.bep_theo_nhom("Bánh Ổ", bep, cha), "pastry")
	la("ông có khai", ksx.bep_theo_nhom("Entremets", bep, cha), "pastry")
	la("không ai khai", ksx.bep_theo_nhom("Nguyên liệu", bep, cha), None)


@ca("v409 cây nhóm hàng bị nối vòng cũng không treo, đúng nếp 8 tầng của app")
def _khong_treo():
	cha = {"A": "B", "B": "A"}
	la("vòng lặp trả None", ksx.bep_theo_nhom("A", {}, cha), None)
	sau = {"N%d" % i: "N%d" % (i + 1) for i in range(0, 12)}
	la("quá 8 tầng thì thôi", ksx.bep_theo_nhom("N0", {"N11": "Baker"}, sau), None)
	la("trong 8 tầng thì tới", ksx.bep_theo_nhom("N0", {"N5": "Baker"}, sau), "baker")


@ca("v409 máy chủ đọc ô trên món TRƯỚC rồi mới suy theo nhóm hàng")
def _thu_tu_doc():
	src = _py("kho_san_xuat.py")
	than = src.split("def _bep_cua_mon(")[1].split("\n@frappe.whitelist")[0]
	i_mon = than.index('"custom_bep_phu_trach"')
	i_nhom = than.index('"item_group"')
	dung("đọc món trước", i_mon < i_nhom)
	dung("có gọi phép leo nhóm", "bep_theo_nhom(" in than)


# --------------------------------------------- mẻ không dùng lại sau ghi sổ


@ca("v409 mẻ đã bị trừ trên phiếu ghi sổ thì không được dùng lại")
def _me_da_ghi_so():
	src = _js("05-san-xuat.js")
	than = src.split("async function mfgBatchOf(")[1].split("\nasync function bomOf")[0]
	dung("có hỏi bảng dòng phiếu kho", "'Stock Entry Detail'" in than)
	dung("chỉ tính phiếu đã ghi sổ", "docstatus: 1" in than)
	dung("lấy nhiều mẻ chứ không phải một", "limit_page_length: 20" in than)
	dung("lọc bằng phép thuần", "mfgMeChuaGhiSo(" in than)


@ca("v409 hỏi không được thì giữ nếp cũ, không đẻ mẻ mới làm lệch tem")
def _duong_lui():
	src = _js("05-san-xuat.js")
	than = src.split("async function mfgBatchOf(")[1].split("\nasync function bomOf")[0]
	cuoi = than.split("catch (e)")[-1]
	dung("trả về mẻ mới nhất chứ không trả rỗng", "return ten[0];" in cuoi)


@ca("v409 phép thuần chọn mẻ nằm ngay cạnh, đọc là thấy luật")
def _co_phep_thuan():
	src = _js("05-san-xuat.js")
	dung("có hàm thuần", "function mfgMeChuaGhiSo(cacMe, daGhiSo)" in src)
	i_thuan = src.index("function mfgMeChuaGhiSo(")
	i_dung = src.index("async function mfgBatchOf(")
	dung("khai trước khi dùng", i_thuan < i_dung)


# ------------------------------------------------------ cửa ngõ của btp.py


@ca("v409 bảy hàm mở ra ngoài của btp.py đã có tên trong danh sách cửa ngõ")
def _cua_ngo_btp():
	from vagabond.khung.kiem_thu import thu_cua_ngo

	ds = thu_cua_ngo.CUA_NGO.get("btp.py")
	dung("có mục btp.py", bool(ds))
	la("đủ bảy tên", sorted(ds), sorted([
		"bang_btp", "gieo_tu_kiem_banh", "luu_btp", "luu_decor", "quyen_btp",
		"them_ma_btp", "xoa_ma_btp",
	]))


@ca("v409 có dòng patch mới để Frappe Cloud chạy migrate chứ không chỉ pull")
def _patch():
	dong = [d.strip() for d in _goc("vagabond/patches.txt").splitlines()]
	dung("có dòng v409", "vagabond.patches.dong_bo_cau_truc #v409" in dong)
	dung("dòng cũ còn nguyên", "vagabond.patches.dong_bo_cau_truc #v408" in dong)
