# -*- coding: utf-8 -*-
"""Rà lỗi logic phân hệ sản xuất 03/09/2026 (v402).

Đo trên site thật: 47 lệnh sản xuất, 46 huỷ, 0 hoàn tất, 0 phiếu Manufacture
ghi sổ, 37 phiếu nháp mồ côi, 74 trên 116 công thức có bảng nổ chứa lá là mã
không quản tồn. Các ca ở đây canh đúng những chỗ đã gây ra con số đó, để
không phiên nào lỡ tay đưa chúng quay lại.
"""

import io
import os

from vagabond import ke_hoach_sx as kh
from vagabond import kho_san_xuat as ksx
from vagabond.patches import no_phantom_chuan as np
from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


def _js(ten):
	return io.open(os.path.join(GOI, "public", "js", "bep", ten), encoding="utf-8").read()


def _goc(ten):
	return io.open(os.path.join(os.path.dirname(GOI), ten), encoding="utf-8").read()


# ------------------------------------------------ còn làm trừ phần đã lệnh


@ca("v402 còn làm trừ cả số đã ra lệnh, không chỉ trừ tồn")
def _():
	la("cần 10 tồn 2 lệnh 8: hết", kh.con_lam_sau_lenh(10, 2, 8), 0.0)
	la("cần 10 tồn 2 lệnh 5: còn 3", kh.con_lam_sau_lenh(10, 2, 5), 3.0)
	la("lệnh vượt không ra âm", kh.con_lam_sau_lenh(10, 2, 20), 0.0)
	la("không quản tồn thì 0", kh.con_lam_sau_lenh(10, 0, 0, quan_ton=False), 0.0)


@ca("v402 thẻ kế hoạch dùng con_lam_sau_lenh, không dùng con_phai_lam trần")
def _():
	src = _py("ke_hoach_sx.py")
	i = src.index("def _dong(ma, ten_mon, dvt, can, da_lenh")
	j = src.index("def _thanh_phan(", i)
	the = src[i:j]
	dung("thẻ gọi con_lam_sau_lenh", '"con_lam": con_lam_sau_lenh(' in the)
	dung("thẻ hết gọi kiểu cũ", '"con_lam": con_phai_lam(' not in the)


@ca("v402 tao_lenh dừng khi mọi dòng đã ra lệnh đủ, kể cả khi gửi kèm số")
def _():
	src = _py("ke_hoach_sx.py")
	dung("có hàng rào", "if not any(flt(c) > 0 for c in cac_con):" in src)
	i_rao = src.index("if not any(flt(c) > 0 for c in cac_con):")
	i_chia = src.index("phan, doi = chia_so_luong(cac_con, so_luong)")
	dung("rào đứng trước phép chia", i_rao < i_chia)


# ------------------------------------------------ hai cờ bắt buộc của lệnh


@ca("v402 lệnh từ kế hoạch luôn nổ nhiều cấp và không qua kho dở dang")
def _():
	src = _py("ke_hoach_sx.py")
	i_ham = src.index("def _tao_mot_lenh(")
	i_tao = src.index("ten_lenh = doc.create_work_order(mon)")
	doan = src[i_ham:i_tao]
	dung("use_multi_level_bom = 1", 'mon["use_multi_level_bom"] = 1' in doan)
	dung("skip_transfer = 1", 'mon["skip_transfer"] = 1' in doan)
	# Hai dong nay phai dung SAU ca hai nhanh dung `mon`, tuc sau
	# prepare_data_for_sub_assembly_items, khong thi nhanh BTP lai bi ERPNext
	# ghi de ve 0.
	i_sub = doan.index("prepare_data_for_sub_assembly_items")
	dung("đặt sau nhánh BTP", doan.index('mon["use_multi_level_bom"] = 1') > i_sub)


@ca("v402 lệnh từ kế hoạch từ chối mã không quản tồn và kho điểm bán")
def _():
	src = _py("ke_hoach_sx.py")
	i_ham = src.index("def _tao_mot_lenh(")
	i_tao = src.index("ten_lenh = doc.create_work_order(mon)")
	doan = src[i_ham:i_tao]
	dung("chặn phantom", 'frappe.db.get_value("Item", ma_mon, "is_stock_item")' in doan)
	dung("chặn kho ngoài bếp", "kho_chon not in _cac_kho_chon()" in doan)


@ca("v402 app không còn hỏi hệ để quyết nổ mấy cấp")
def _():
	src = _js("05-san-xuat.js")
	i = src.index("async function mfgNoNhieuCap()")
	than = src[i:i + 80]
	dung("trả 1 thẳng", "return 1;" in than)
	dung("hết gọi trang_thai trong hàm này", "phantom.trang_thai" not in than)


# ------------------------------------------------------ hoàn tất một cửa


@ca("v402 hai ô hoàn tất ra hai số đúng luật hao hụt của ERPNext")
def _():
	la("cân thiếu: giữ số làm, hạ số nhập", ksx.so_hoan_tat(1000, 900), (1000.0, 900.0))
	la("cân đủ", ksx.so_hoan_tat(1000, 1000), (1000.0, 1000.0))
	la("cân dư: nhập đủ số cân", ksx.so_hoan_tat(1000, 1100), (1100.0, 1100.0))
	la("không gõ ô cân thì bằng số làm", ksx.so_hoan_tat(500, None), (500.0, 500.0))
	la("cân 0 coi như không gõ", ksx.so_hoan_tat(500, 0), (500.0, 500.0))


@ca("v402 app hoàn tất qua một cửa máy chủ, không insert rồi submit rời")
def _():
	src = _js("05-san-xuat.js")
	i = src.index("async function mfgHoanTatMot(")
	j = src.index("async function", i + 10)
	than = src[i:j]
	dung("gọi hoan_tat_phieu", "vagabond.kho_san_xuat.hoan_tat_phieu" in than)
	dung("hết frappe.client.insert phiếu kho", "frappe.client.insert', { doc: se }" not in than)
	dung("app không tự đặt fg_completed_qty", "se.fg_completed_qty" not in than)


@ca("v402 máy tự làm BTP tươi chỉ với mã còn theo tồn")
def _():
	src = _js("05-san-xuat.js")
	i = src.index("async function freshOf(")
	j = src.index("async function", i + 10)
	than = src[i:j]
	dung("đọc is_stock_item", "'is_stock_item'" in than)
	dung("lọc theo cả hai cờ", "r.custom_lam_tuoi && r.is_stock_item" in than)


@ca("v402 màn BTP cần làm nhập về kho nguyên liệu")
def _():
	src = _js("05-san-xuat.js")
	i = src.index("async function scrMfgBtp(")
	j = src.index("async function", i + 10)
	dung("a.fg = mfg.src", "a.fg = mfg.src;" in src[i:j])


@ca("v402 màn kế hoạch chỉ gửi số lượng khi bếp thật sự gõ")
def _():
	src = _js("38-ke-hoach-sx.js")
	i = src.index("async function khsxTaoLenh(")
	j = src.index("async function", i + 10)
	dung("so_luong theo daGo", "so_luong: daGo ? sl : null" in src[i:j])


# -------------------------------------------------- patch phantom chuẩn


@ca("v402 dựng lại bảng nổ theo thứ tự con trước cha sau")
def _():
	con_cua = {"banh": ["glaze"], "glaze": ["gelatine"], "gelatine": [], "crumble": []}
	tt = np.thu_tu_dung_lai(con_cua)
	la("đủ bốn", sorted(tt), ["banh", "crumble", "gelatine", "glaze"])
	dung("gelatine trước glaze", tt.index("gelatine") < tt.index("glaze"))
	dung("glaze trước bánh", tt.index("glaze") < tt.index("banh"))


@ca("v402 vòng lặp công thức không làm treo, mỗi BOM ra đúng một lần")
def _():
	tt = np.thu_tu_dung_lai({"a": ["b"], "b": ["a"], "c": ["x_khong_co"]})
	la("ba BOM", sorted(tt), ["a", "b", "c"])
	la("không lặp", len(tt), 3)


@ca("v402 lá hỏng là mã không quản tồn hoặc mã đã tắt, không lặp")
def _():
	la("bắt đủ", np.la_hong(["NVL1", "BTP9", "NVL2", "BTP9", "TAT1"], {"BTP9"}, {"TAT1"}),
		["BTP9", "TAT1"])
	la("sạch thì rỗng", np.la_hong(["NVL1"], {"BTP9"}, set()), [])


@ca("v402 patch phantom chuẩn được đăng ký và không ném lỗi ra migrate")
def _():
	dung("có trong patches.txt", "vagabond.patches.no_phantom_chuan" in _goc("vagabond/patches.txt"))
	src = _py("patches/no_phantom_chuan.py")
	dung("mỗi bước bọc try", src.count("except Exception:") >= 5)
	dung("bật is_phantom_bom", '"is_phantom_bom", 1' in src)
	dung("bật is_phantom_item", '"is_phantom_item"] = 1' in src)


@ca("v402 hoan_tat_phieu có trong danh sách cửa ngõ")
def _():
	dung("đã đăng ký", '"hoan_tat_phieu"' in _py("khung/kiem_thu/thu_cua_ngo.py"))
