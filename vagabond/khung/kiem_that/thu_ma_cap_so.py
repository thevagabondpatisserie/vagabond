# -*- coding: utf-8 -*-
"""Ca kiểm TÍCH HỢP cho việc cấp mã lệnh sản xuất và mã lô (#206, PR #220).

Vì sao phải có tầng này cho việc cấp số
---------------------------------------
Bộ kiểm tầng khung đã chốt phần thuần: hình dạng đuôi số, mốc bảo toàn, phép
đọc ngày trong mã. Nhưng việc cấp số THẬT đi qua `tabSeries` với khoá dòng
của MariaDB, qua thứ tự chạy hook `autoname` của Frappe (lớp trước, hook
sau, xem frappe/model/naming.py `set_new_name` và `Document.run_method`), và
qua chuỗi validate của Work Order và Batch trong ERPNext. Ba thứ đó bộ kiểm
tay không không nhìn thấy. Codex yêu cầu trên PR #220: kiểm trên Frappe
thật cho bộ đếm thiếu, bộ đếm lệch, migrate lặp lại, cấp liên tiếp, lỗi cấp
số phải báo rõ, và mã lô người gõ phải giữ nguyên.

Mọi ca chạy trong điểm lưu của `nen.py`: lệnh, lô, dòng đếm đều lùi lại
hết sau ca. Không ca nào chạm dữ liệu quá khứ, không ca nào đổi tên phiếu
đang có.

VỀ "CẤP ĐỒNG THỜI": một phiên Frappe chỉ có MỘT kết nối cơ sở dữ liệu, nên
ca ở đây chỉ chứng minh được hai lượt cấp NỐI TIẾP trong cùng giao dịch ra
hai số khác nhau và tăng dần. Hai kết nối cùng lúc thì dựa vào `SELECT ...
FOR UPDATE` trong `frappe.model.naming.getseries`; ca này KHÔNG chứng minh
được điều đó, và nói thẳng như vậy trong tên ca.
"""

import frappe
from frappe.utils import nowdate

from vagabond import ma_phieu_sx as mp
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import (
	ca, cong_ty, dung, khong_nem, la, mot_kho,
)


# ------------------------------------------------------------ dựng dữ liệu


def _uom():
	for t in ("Nos", "Cái", "Gram", "Unit"):
		if frappe.db.exists("UOM", t):
			return t
	return frappe.db.get_value("UOM", {}, "name")


def _nhom_hang():
	for t in ("Nguyên vật liệu", "All Item Groups"):
		if frappe.db.exists("Item Group", t):
			return t
	return frappe.db.get_value("Item Group", {"is_group": 0}, "name")


def _mon_thu(ma, theo_lo=0):
	"""Một mã hàng thử, theo tồn kho. Đặt tên rõ là của ca kiểm."""
	if frappe.db.exists("Item", ma):
		return ma
	it = frappe.new_doc("Item")
	it.item_code = ma
	it.item_name = "Ca kiem tich hop %s" % ma
	it.item_group = _nhom_hang()
	it.stock_uom = _uom()
	it.is_stock_item = 1
	it.include_item_in_manufacturing = 1
	if theo_lo:
		it.has_batch_no = 1
		# create_new_batch PHAI la 1: erpnext/stock/doctype/batch/batch.py
		# Batch.autoname() la phuong thuc lop, chay TRUOC hook autoname cua
		# vagabond (xem Document.hook.compose trong frappe/model/document.py:
		# fn cua lop chay truoc, hook cua app chay sau). Item.create_new_batch=0
		# lam autoname loi rieng ngay "Batch ID is mandatory" TRUOC KHI hook
		# dat_ten_lo kip chay, khong lien quan gi den dung/sai cua hook. Dat 1
		# de autoname cua lop tu cap batch_id tam (hash), roi hook dat_ten_lo
		# ghi de lai dung khuon LO-yymmdd-nnnnnn ngay sau do.
		it.create_new_batch = 1
	it.flags.ignore_permissions = True
	it.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Item", it.name))
	return it.name


def _bom_thu(tp, nvl, cty):
	bom = frappe.new_doc("BOM")
	bom.item = tp
	bom.company = cty
	bom.quantity = 1
	bom.is_active = 1
	bom.is_default = 1
	bom.rm_cost_as_per = "Valuation Rate"
	bom.append("items", {"item_code": nvl, "qty": 1, "uom": _uom(), "rate": 1})
	bom.flags.ignore_permissions = True
	bom.insert(ignore_permissions=True)
	bom.submit()
	nen._DA_TAO.append(("BOM", bom.name))
	return bom


def _lenh_thu(tp, bom, kho, cty, so_luong=1):
	"""Insert MỘT Work Order thật. Ném lỗi thì để ném ra."""
	wo = frappe.new_doc("Work Order")
	wo.production_item = tp
	wo.bom_no = bom.name
	wo.qty = so_luong
	wo.company = cty
	wo.fg_warehouse = kho
	wo.wip_warehouse = kho
	wo.source_warehouse = kho
	wo.skip_transfer = 1
	wo.flags.ignore_permissions = True
	wo.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Work Order", wo.name))
	return wo


def _lo_thu(ma, batch_id=None):
	"""Insert MỘT Batch thật. `batch_id` có thì là lô NGƯỜI gõ số."""
	lo = frappe.new_doc("Batch")
	lo.item = ma
	if batch_id:
		lo.batch_id = batch_id
	lo.flags.ignore_permissions = True
	lo.insert(ignore_permissions=True)
	nen._DA_TAO.append(("Batch", lo.name))
	return lo


def _nen_lenh():
	cty = cong_ty()
	kho = mot_kho(cty)
	dung("site có kho lá để dựng lệnh thử", bool(kho))
	nvl = _mon_thu("KTTH-NVL-CAP-SO")
	tp = _mon_thu("KTTH-TP-CAP-SO")
	bom = _bom_thu(tp, nvl, cty)
	return cty, kho, tp, bom


def _dang_o(khoa):
	return mp._dong_dem_dang_co(khoa)


def _dat_dong_dem(khoa, so):
	"""Đặt dòng đếm trong điểm lưu. Chỉ dùng trong ca kiểm; lùi lại sau ca."""
	if _dang_o(khoa) is None:
		frappe.db.sql("insert into `tabSeries` (`name`, `current`) values (%s, %s)", (khoa, so))
	else:
		frappe.db.sql("update `tabSeries` set `current`=%s where `name`=%s", (so, khoa))


def _xoa_dong_dem(khoa):
	frappe.db.sql("delete from `tabSeries` where `name`=%s", (khoa,))


def _nem_gi(nhan, ham):
	"""Chạy và trả về CÂU LỖI. Không ném gì thì ca đỏ, vì ở đây lỗi là điều mong."""
	try:
		ham()
	except Exception as e:
		return nen.cau_loi(e)
	dung(nhan + ": đáng lẽ phải bị chặn mà lại lọt", False)
	return ""


# ------------------------------------------------------------ mã lệnh


@ca("cap ma lenh: WO moi mang LSX-ddmmyy-nnnnnn theo ngay may chu, va so noi tiep dong dem")
def _lenh_theo_ngay():
	cty, kho, tp, bom = _nen_lenh()
	if _dang_o(mp.KHOA_LENH) is None:
		# Site chưa migrate bản này thì dựng dòng đếm đúng đường thật, không
		# chèn số tay: after_migrate cũng gọi đúng hàm này.
		khong_nem("dựng dòng đếm bằng dat_moc_bo_dem", mp.dat_moc_bo_dem)
	truoc = _dang_o(mp.KHOA_LENH)
	dung("có dòng đếm LSX", truoc is not None)
	wo = khong_nem("insert Work Order", lambda: _lenh_thu(tp, bom, kho, cty))
	if not wo:
		return
	dung("mã theo kiểu ngày: " + wo.name, mp.la_ma_theo_ngay(wo.name, "LSX"))
	la("ngày trong mã là ngày máy chủ", mp.ngay_tao_trong_ma(wo.name, "LSX"), str(nowdate()))
	la("đuôi số nối tiếp dòng đếm", mp.duoi_so_cua(wo.name), int(truoc) + 1)
	la("dòng đếm tăng đúng một", _dang_o(mp.KHOA_LENH), int(truoc) + 1)
	dung("đuôi ít nhất sáu chữ số", len(wo.name.split("-")[-1]) >= mp.SO_CHU_SO)
	la("lệnh có thật trong sổ", frappe.db.exists("Work Order", wo.name), wo.name)


@ca("cap noi tiep hai lenh trong cung giao dich: hai so khac nhau va tang dan (KHONG chung minh duoc hai ket noi cung luc)")
def _hai_lenh_noi_tiep():
	cty, kho, tp, bom = _nen_lenh()
	if _dang_o(mp.KHOA_LENH) is None:
		khong_nem("dựng dòng đếm", mp.dat_moc_bo_dem)
	a = khong_nem("insert lệnh 1", lambda: _lenh_thu(tp, bom, kho, cty))
	b = khong_nem("insert lệnh 2", lambda: _lenh_thu(tp, bom, kho, cty))
	if not (a and b):
		return
	dung("hai mã khác nhau", a.name != b.name)
	la("lệnh sau hơn lệnh trước đúng một", mp.duoi_so_cua(b.name), mp.duoi_so_cua(a.name) + 1)


@ca("bo dem THIEU: insert WO bi CHAN voi cau ro, khong co lenh nao lot ra voi ma kieu cu")
def _bo_dem_thieu():
	cty, kho, tp, bom = _nen_lenh()
	so_lenh = frappe.db.count("Work Order")
	_xoa_dong_dem(mp.KHOA_LENH)
	la("dòng đếm đã bị gỡ (trong điểm lưu)", _dang_o(mp.KHOA_LENH), None)
	loi = _nem_gi("insert WO khi thiếu dòng đếm", lambda: _lenh_thu(tp, bom, kho, cty))
	dung("câu lỗi nói là không cấp được mã: " + loi, "Không cấp được mã lệnh sản xuất" in loi)
	dung("và nói rõ vì sao", "chưa được dựng" in loi)
	dung("và nói dữ liệu chưa mất", "chưa mất" in loi)
	la("không lệnh nào được ghi", frappe.db.count("Work Order"), so_lenh)
	la("không có lệnh mang mã naming_series lọt ra",
		frappe.db.count("Work Order", {"name": ["like", "LSX-__-__-%"], "creation": [">=", nowdate()]}), 0)
	la("dòng đếm không bị getseries tự dựng ở 1", _dang_o(mp.KHOA_LENH), None)


@ca("bo dem LECH thap hon ma da cap: dat_moc_bo_dem NANG len, khong ha, chay lai lan hai giu nguyen")
def _bo_dem_lech():
	cty, kho, tp, bom = _nen_lenh()
	if _dang_o(mp.KHOA_LENH) is None:
		khong_nem("dựng dòng đếm", mp.dat_moc_bo_dem)
	wo = khong_nem("insert một lệnh để có mã đã cấp", lambda: _lenh_thu(tp, bom, kho, cty))
	if not wo:
		return
	moc = mp.moc_bao_toan(mp._cac_ten_cung_ho(mp.KHOA_LENH), [])
	dung("mốc bảo toàn không nhỏ hơn đuôi lệnh vừa cấp", moc >= mp.duoi_so_cua(wo.name))
	# Kéo dòng đếm về THẤP HƠN mốc để có LỆCH thật. Trên site trống, lệnh đầu
	# tiên vừa cấp có đuôi = 1, nên kéo cứng về 1 không tạo ra lệch nào (mốc
	# cũng là 1) và dat_moc_bo_dem() đúng đắn báo "giữ nguyên" chứ không phải
	# hỏng. Trừ đi 1 so với đuôi vừa cấp (không dưới 0) mới chắc chắn thấp
	# hơn mốc bất kể site trống hay đã có lịch sử.
	thap = max(0, mp.duoi_so_cua(wo.name) - 1)
	_dat_dong_dem(mp.KHOA_LENH, thap)
	la("dòng đếm đã bị kéo xuống dưới mốc (trong điểm lưu)", _dang_o(mp.KHOA_LENH), thap)
	kq1 = khong_nem("dat_moc_bo_dem lần một", mp.dat_moc_bo_dem) or {}
	dung("lần một báo nâng: %r" % kq1.get(mp.KHOA_LENH), "nang" in str(kq1.get(mp.KHOA_LENH)))
	dung("dòng đếm được nâng lên ít nhất bằng mốc", (_dang_o(mp.KHOA_LENH) or 0) >= moc)
	sau1 = _dang_o(mp.KHOA_LENH)
	kq2 = khong_nem("dat_moc_bo_dem lần hai", mp.dat_moc_bo_dem) or {}
	dung("lần hai giữ nguyên: %r" % kq2.get(mp.KHOA_LENH), "giu nguyen" in str(kq2.get(mp.KHOA_LENH)))
	la("chạy lại không đổi số", _dang_o(mp.KHOA_LENH), sau1)
	# Dong dem dang CAO hon moc thi khong bao gio bi ha.
	_dat_dong_dem(mp.KHOA_LENH, int(sau1) + 500)
	khong_nem("dat_moc_bo_dem khi dòng đếm cao hơn mốc", mp.dat_moc_bo_dem)
	la("không hạ dòng đếm", _dang_o(mp.KHOA_LENH), int(sau1) + 500)
	# Va lenh ke tiep van tang: lay so sau khi nang, khong lay so 1.
	wo2 = khong_nem("insert lệnh sau khi nâng", lambda: _lenh_thu(tp, bom, kho, cty))
	if wo2:
		dung("lệnh mới mang số lớn hơn mọi lệnh cũ", mp.duoi_so_cua(wo2.name) > mp.duoi_so_cua(wo.name))


@ca("so ke tiep da co nguoi mang: hook nhay qua, khong trung ma, khong nem")
def _so_da_co_nguoi_mang():
	cty, kho, tp, bom = _nen_lenh()
	if _dang_o(mp.KHOA_LENH) is None:
		khong_nem("dựng dòng đếm", mp.dat_moc_bo_dem)
	a = khong_nem("insert lệnh 1", lambda: _lenh_thu(tp, bom, kho, cty))
	if not a:
		return
	# Keo dong dem lui mot: so ke tiep se dung bang so cua lenh 1 vua tao.
	_dat_dong_dem(mp.KHOA_LENH, mp.duoi_so_cua(a.name) - 1)
	b = khong_nem("insert lệnh 2 khi số kế tiếp đã có người mang", lambda: _lenh_thu(tp, bom, kho, cty))
	if not b:
		return
	dung("không trùng mã", b.name != a.name)
	la("nhảy qua số đã có, lấy số kế", mp.duoi_so_cua(b.name), mp.duoi_so_cua(a.name) + 1)


@ca("migrate lap lai: dung() chay hai lan lien khong loi, lan hai khong doi gi")
def _migrate_lap_lai():
	kq1 = khong_nem("dung() lần một", mp.dung) or {}
	kq2 = khong_nem("dung() lần hai", mp.dung) or {}
	for k in ("Work Order", "bo_dem"):
		dung("lần một có kết quả cho %s" % k, k in kq1)
		dung("không mục nào báo lỗi lần một: %r" % kq1.get(k), kq1.get(k) != "loi")
		dung("không mục nào báo lỗi lần hai: %r" % kq2.get(k), kq2.get(k) != "loi")
	bd2 = kq2.get("bo_dem") or {}
	for khoa in (mp.KHOA_LENH, mp.KHOA_LO):
		dung("lần hai dòng %s giữ nguyên: %r" % (khoa, bd2.get(khoa)), "giu nguyen" in str(bd2.get(khoa)))


# ------------------------------------------------------------ mã lô


@ca("ma lo: lo MAY dat mang LO-yymmdd-nnnnnn; lo NGUOI go so giu nguyen so nha cung cap")
def _lo_may_va_lo_nguoi():
	ma = _mon_thu("KTTH-NVL-THEO-LO", theo_lo=1)
	if _dang_o(mp.KHOA_LO) is None:
		khong_nem("dựng dòng đếm LO", mp.dat_moc_bo_dem)
	truoc = _dang_o(mp.KHOA_LO)
	may = khong_nem("insert Batch không gõ số", lambda: _lo_thu(ma))
	if may:
		dung("lô máy đặt theo khuôn: " + may.name, mp.la_ma_lo_may_dat(may.name))
		la("batch_id và name là một", may.batch_id, may.name)
		la("đuôi nối tiếp dòng đếm", mp.duoi_so_cua(may.name), int(truoc) + 1)
	nguoi = khong_nem("insert Batch có số nhà cung cấp", lambda: _lo_thu(ma, "NCC-KTTH-2026-001"))
	if nguoi:
		la("giữ nguyên số người gõ", nguoi.name, "NCC-KTTH-2026-001")
		la("batch_id cũng giữ", nguoi.batch_id, "NCC-KTTH-2026-001")
	la("lô người gõ KHÔNG tiêu số của dòng đếm", _dang_o(mp.KHOA_LO), int(truoc) + (1 if may else 0))


@ca("bo dem LO thieu: lo may dat bi CHAN voi cau ro, lo nguoi go van tao duoc")
def _bo_dem_lo_thieu():
	ma = _mon_thu("KTTH-NVL-THEO-LO", theo_lo=1)
	so_lo = frappe.db.count("Batch")
	_xoa_dong_dem(mp.KHOA_LO)
	loi = _nem_gi("insert Batch máy đặt khi thiếu dòng đếm", lambda: _lo_thu(ma))
	dung("câu lỗi nói không cấp được mã lô: " + loi, "Không cấp được mã lô" in loi)
	dung("và nói vì sao", "chưa được dựng" in loi)
	la("không lô nào lọt ra", frappe.db.count("Batch"), so_lo)
	nguoi = khong_nem("lô người gõ vẫn tạo được dù thiếu dòng đếm", lambda: _lo_thu(ma, "NCC-KTTH-2026-002"))
	if nguoi:
		la("đúng số người gõ", nguoi.name, "NCC-KTTH-2026-002")
