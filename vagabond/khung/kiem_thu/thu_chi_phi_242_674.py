# -*- coding: utf-8 -*-
"""v674 Bảng kê 242, phiếu xuất CCDC phân bổ nhiều tháng, khuôn bút toán nháp tháng.

Ca chốt (tầng khung, phép thuần và hành vi với Frappe giả):
  - lịch phân bổ cộng lại ĐÚNG nguyên giá, tháng cuối gánh phần lẻ đồng;
  - số cần phân bổ tháng M = luỹ kế tới M trừ số đã phân bổ: tháng lỡ thì tự bù,
    kế toán phân bổ tay một phần thì máy trừ đi, không bao giờ vượt nguyên giá;
  - ô Đã phân bổ trước = 0 là giá trị hợp lệ, không bị thay mặc định (H8 loại 14);
  - phiếu xuất CCDC: thiếu cách phân bổ, thiếu số tháng, món khác nhóm đều bị chặn;
  - bút toán tháng cân, hai dòng mỗi khoản cùng gắn khoản;
  - khuôn bút toán nháp: bản nháp bị sửa tay thì máy dừng, không ghi đè; bản đã
    ghi sổ hoặc đã bỏ thì lập tờ mới; dấu không phụ thuộc thứ tự và kiểu số;
  - quyền: thiếu vai thì ném PermissionError.
"""

import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import but_toan_nhap as BN  # noqa: E402
from vagabond import chi_phi_242 as C  # noqa: E402
from vagabond import xuat_noi_bo as X  # noqa: E402


@ca("v674 lịch phân bổ: cộng đúng nguyên giá, tháng cuối gánh phần lẻ; số tháng hay giá trị 0 thì không có lịch")
def _lich():
	l = C.lich_phan_bo(1000000, 3)
	la("ba tháng", l, [333333, 333333, 333334])
	la("cộng lại", sum(l), 1000000)
	la("một tháng", C.lich_phan_bo(650000, 1), [650000])
	la("số tháng 0", C.lich_phan_bo(650000, 0), [])
	la("nguyên giá 0", C.lich_phan_bo(0, 6), [])
	la("số lẻ đồng làm tròn", sum(C.lich_phan_bo(1000000.4, 7)), 1000000)


@ca("v674 cần phân bổ: tháng đầu, tháng lỡ tự bù, phân bổ tay trừ đi, không vượt, khoản chưa khai hay đã ngừng là 0")
def _can():
	k = {"nguyen_gia": 1200000, "so_ky": 12, "ky_bat_dau": "2026-11", "trang_thai": ""}
	la("trước tháng bắt đầu", C.can_phan_bo(k, "2026-10", 0), 0)
	la("tháng đầu", C.can_phan_bo(k, "2026-11", 0), 100000)
	la("lỡ tháng 11, tháng 12 bù", C.can_phan_bo(k, "2026-12", 0), 200000)
	la("kế toán đã phân bổ tay 150.000", C.can_phan_bo(k, "2026-12", 150000), 50000)
	la("phân bổ tay vượt lịch thì tháng này 0", C.can_phan_bo(k, "2026-12", 500000), 0)
	la("quá hạn lịch: phần còn lại", C.can_phan_bo(k, "2028-05", 1100000), 100000)
	la("đủ rồi", C.can_phan_bo(k, "2028-05", 1200000), 0)
	la("chưa khai", C.can_phan_bo(dict(k, so_ky=None), "2026-12", 0), 0)
	la("đã ngừng", C.can_phan_bo(dict(k, trang_thai=C.TT_NGUNG), "2026-12", 0), 0)
	la("chứng từ gốc huỷ", C.can_phan_bo(dict(k, trang_thai=C.TT_HUY), "2026-12", 0), 0)


@ca("v674 trạng thái hiện: chờ khai, đang phân bổ, đã xong; ngừng và huỷ giữ nguyên")
def _tt():
	k = {"nguyen_gia": 300000, "so_ky": 3, "ky_bat_dau": "2026-11", "trang_thai": ""}
	la("đang", C.trang_thai_hien(k, 100000), C.TT_DANG)
	la("xong", C.trang_thai_hien(k, 300000), C.TT_XONG)
	la("chưa khai", C.trang_thai_hien(dict(k, so_ky=0), 0), C.TT_CHO)
	la("ngừng", C.trang_thai_hien(dict(k, trang_thai=C.TT_NGUNG), 0), C.TT_NGUNG)
	la("huỷ", C.trang_thai_hien(dict(k, trang_thai=C.TT_HUY), 300000), C.TT_HUY)


@ca("v674 khai: 0 ở Đã phân bổ trước hợp lệ; số tháng ngoài 1..36, thiếu tháng bắt đầu, âm, vượt nguyên giá đều nhắc")
def _khai():
	la("hợp lệ với 0", C.kiem_khai(12, 1000000, 0, "2026-11"), [])
	dung("37 tháng", C.kiem_khai(37, 1000000, 0, "2026-11"))
	dung("0 tháng", C.kiem_khai(0, 1000000, 0, "2026-11"))
	dung("thiếu tháng", C.kiem_khai(6, 1000000, 0, ""))
	dung("tháng sai dạng", C.kiem_khai(6, 1000000, 0, "2026-13"))
	dung("âm", C.kiem_khai(6, 1000000, -1, "2026-11"))
	dung("vượt nguyên giá", C.kiem_khai(6, 1000000, 1000001, "2026-11"))
	la("vượt nguyên giá: số vượt", C.vuot_nguyen_gia(1000000, 200000, 700000, 150000), 50000)
	la("không vượt", C.vuot_nguyen_gia(1000000, 0, 700000, 300000), 0)


@ca("v674 bút toán tháng: hai dòng mỗi khoản cùng gắn khoản, Nợ tài khoản chi phí, Có 242, cân; số 0 bỏ")
def _dong():
	d = C.dong_but_toan_thang([
		{"khoan": "CP242-00001", "so_tien": 100000, "tk_chi_phi": "6273 - X - TV", "bo_phan": "Bếp Pastry - TV", "dien_giai": "Khuôn ring"},
		{"khoan": "CP242-00002", "so_tien": 0, "tk_chi_phi": "6413 - X - TV", "bo_phan": "Cửa hàng D1 - TV"},
		{"khoan": "CP242-00003", "so_tien": 50000.4, "tk_chi_phi": "6423 - X - TV", "bo_phan": "Kế toán - TV"},
	], "242 - Chi phí chờ phân bổ - TV", "2026-11")
	la("bốn dòng", len(d), 4)
	la("cân", BN.kiem_can(d), "")
	la("dòng Nợ khoản 1", (d[0]["account"], d[0]["debit"], d[0]["khoan"]), ("6273 - X - TV", 100000, "CP242-00001"))
	la("dòng Có 242 khoản 1", (d[1]["account"], d[1]["credit"], d[1]["khoan"]), ("242 - Chi phí chờ phân bổ - TV", 100000, "CP242-00001"))
	dung("diễn giải có tháng", "11/2026" in d[0]["user_remark"])


@ca("v674 chip bảng kê: đếm trạng thái và nguồn trên cùng một tập; khoảng ngày tháng này, 3 tháng, năm nay")
def _chip():
	rows = [{"trang_thai_hien": C.TT_CHO, "nguon_loai": C.NGUON_HD}, {"trang_thai_hien": C.TT_DANG, "nguon_loai": C.NGUON_XUAT},
		{"trang_thai_hien": C.TT_DANG, "nguon_loai": C.NGUON_HD}]
	d = C.gom_dem(rows)
	la("trạng thái", (d["trang_thai"][""], d["trang_thai"][C.TT_DANG], d["trang_thai"][C.TT_CHO]), (3, 2, 1))
	la("nguồn", (d["nguon"][C.NGUON_HD], d["nguon"][C.NGUON_XUAT]), (2, 1))
	la("tháng này", C.loc_khoang("2026-11-02", "thang", "2026-11-18"), True)
	la("tháng trước không vào tháng này", C.loc_khoang("2026-10-31", "thang", "2026-11-18"), False)
	la("3 tháng gồm tháng 9", C.loc_khoang("2026-09-01", "3thang", "2026-11-18"), True)
	la("3 tháng bỏ tháng 8", C.loc_khoang("2026-08-31", "3thang", "2026-11-18"), False)
	la("năm nay", C.loc_khoang("2026-01-01", "nam", "2026-11-18"), True)
	la("tất cả", C.loc_khoang("2020-01-01", "", "2026-11-18"), True)


@ca("v674 phiếu xuất CCDC: thiếu cách phân bổ, thiếu số tháng, 1 tháng nhiều kỳ đều chặn; mục đích khác không hỏi; None không thành mặc định")
def _xuat():
	la("mục đích khác", X.thieu_phan_bo("marketing", None, None), [])
	dung("thiếu cách", X.thieu_phan_bo("ccdc", None, None))
	la("một lần đủ", X.thieu_phan_bo("ccdc", X.PB_MOT_LAN, None), [])
	dung("nhiều tháng thiếu số", X.thieu_phan_bo("ccdc", X.PB_NHIEU_KY, None))
	dung("nhiều tháng số rỗng", X.thieu_phan_bo("ccdc", X.PB_NHIEU_KY, ""))
	dung("nhiều tháng 1 tháng", X.thieu_phan_bo("ccdc", X.PB_NHIEU_KY, 1))
	dung("nhiều tháng 37", X.thieu_phan_bo("ccdc", X.PB_NHIEU_KY, 37))
	la("nhiều tháng 12", X.thieu_phan_bo("ccdc", X.PB_NHIEU_KY, "12"), [])
	la("món khác nhóm", X.mon_khong_phai_ccdc([{"ma": "A", "ten": "Khuôn", "nhom": "Công cụ Dụng cụ"},
		{"ma": "B", "ten": "Bột mì", "nhom": "Nguyên vật liệu Thô"}]), ["Bột mì"])
	dung("mục đích ccdc có trong danh mục", X.muc_dich_theo_ma("ccdc") is not None)


@ca("v674 khuôn bút toán nháp: dấu không phụ thuộc thứ tự và kiểu số; sửa tay thì dừng; đã ghi sổ hay đã bỏ thì lập mới")
def _khuon():
	a = [{"account": "6273", "cost_center": "B", "debit": 1000000, "credit": 0, "khoan": "K1"},
		{"account": "242", "cost_center": "B", "debit": 0, "credit": 1000000.0, "khoan": "K1"}]
	b = list(reversed([dict(x) for x in a]))
	la("cùng dấu khi đảo thứ tự và đổi kiểu số", BN.dau_ban(a), BN.dau_ban(b))
	c = [dict(x) for x in a]
	c[0]["debit"] = 900000
	c[1]["credit"] = 900000
	dung("khác số là khác dấu", BN.dau_ban(a) != BN.dau_ban(c))
	may = BN.dau_ban(a)
	la("chưa có", BN.trang_thai_ban_ghi(None, may), BN.TT_CHUA)
	la("nháp đúng dấu", BN.trang_thai_ban_ghi({"docstatus": 0, "dau": may}, may), BN.TT_NHAP)
	la("nháp khác dấu", BN.trang_thai_ban_ghi({"docstatus": 0, "dau": BN.dau_ban(c)}, may), BN.TT_SUA_TAY)
	la("đã ghi sổ", BN.trang_thai_ban_ghi({"docstatus": 1, "dau": BN.dau_ban(c)}, may), BN.TT_GHI)
	la("đã bỏ mềm", BN.trang_thai_ban_ghi({"docstatus": 0, "vgb_huy": 1, "dau": may}, may), BN.TT_BO)
	la("việc: sửa tay thì dừng", BN.viec_khi_lap(BN.TT_SUA_TAY), "dung")
	la("việc: nháp máy thì cập nhật", BN.viec_khi_lap(BN.TT_NHAP), "cap_nhat")
	la("việc: đã ghi sổ thì lập tờ mới", BN.viec_khi_lap(BN.TT_GHI), "moi")
	la("việc: đã bỏ thì lập tờ mới", BN.viec_khi_lap(BN.TT_BO), "moi")


@ca("v674 khuôn bút toán: cân, mỗi dòng đúng một bên dương; tháng YYYY-MM; cuối tháng nhuận")
def _can_bang():
	la("lệch", bool(BN.kiem_can([{"debit": 10, "credit": 0}, {"debit": 0, "credit": 9}])), True)
	la("dòng hai bên", bool(BN.kiem_can([{"debit": 10, "credit": 10}, {"debit": 0, "credit": 0}])), True)
	la("dòng âm", bool(BN.kiem_can([{"debit": -10, "credit": 0}, {"debit": 0, "credit": -10}])), True)
	la("một dòng", bool(BN.kiem_can([{"debit": 10, "credit": 0}])), True)
	la("đúng", BN.kiem_can([{"debit": 10, "credit": 0}, {"debit": 0, "credit": 10}]), "")
	la("tháng sai", BN.ky_hop_le("2026-13"), None)
	la("tháng sai dạng", BN.ky_hop_le("2026/11"), None)
	la("cuối tháng 2 năm nhuận", str(BN.ngay_cuoi_thang("2028-02")), "2028-02-29")
	la("cuối tháng 12", str(BN.ngay_cuoi_thang("2026-12")), "2026-12-31")
	la("cộng tháng qua năm", BN.cong_thang("2026-11", 3), "2027-02")
	la("trừ tháng qua năm", BN.cong_thang("2026-01", -1), "2025-12")
	la("số tháng giữa", BN.so_thang_giua("2026-11", "2027-02"), 3)


@ca("v674 quyền: thiếu vai thì ném lỗi quyền; có vai Kế toán thì qua")
def _quyen():
	import frappe

	with um.patch.object(frappe, "get_roles", lambda *a: ["Marketing"], create=True):
		nem("Marketing không lập được bút toán", lambda: BN.kiem_quyen(BN.QUYEN_LAP, "lập bút toán"))
		dung("Marketing không ghi sổ", not BN.co_quyen(BN.QUYEN_GHI))
	with um.patch.object(frappe, "get_roles", lambda *a: ["Accounts User"], create=True):
		BN.kiem_quyen(BN.QUYEN_LAP, "lập bút toán")
		dung("Accounts User lập được mà không ghi sổ", BN.co_quyen(BN.QUYEN_LAP) and not BN.co_quyen(BN.QUYEN_GHI))
	with um.patch.object(frappe, "get_roles", lambda *a: ["Accounts Manager"], create=True):
		dung("Accounts Manager ghi sổ", BN.co_quyen(BN.QUYEN_GHI))
