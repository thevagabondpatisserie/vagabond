"""Kiem thu xuyen suot: khung phai ra Y HET duong cu.

Cac ca o day goi CHINH khai bao that (BANG_PO, BANG_HOA_DON_MUA) qua CHINH
ham that (khung.ds.dung), chi thay cho doc co so du lieu bang mot tap du
lieu gia. Roi doi chieu tung con so voi hai ham cu ds_po va ds_hoa_don_mua.

Day la cai chan cuoi cung cho tieu chuan so 10: chung nao con hai duong
chay song song, hai duong phai ra cung mot ket qua. Ngay nao mot ai do sua
mot ben ma quen ben kia, bo kiem thu nay do.
"""

from vagabond import ke_toan, mua_hang
from vagabond.khung import ds as khung_ds
from vagabond.khung.kiem_thu import nen
from vagabond.khung.kiem_thu.nen import ca, don_mua, dung, hoa_don_mua, la


def _dat_po(ds):
	nen.BANG_GIA["Purchase Order"] = ds


def _dat_hdm(ds):
	nen.BANG_GIA["Purchase Invoice"] = ds


def _so_po(nhan, **tham):
	cu = mua_hang.ds_po(so_ngay=tham.get("so_ngay", 60),
		tu_khoa=tham.get("tu_khoa", ""), nhom=tham.get("chip"))
	moi = khung_ds.dung(mua_hang.BANG_PO, dict(tham))
	la(nhan + " - số dòng hiện", len(moi["dong"]), len(cu["don"]))
	la(nhan + " - tổng dòng", moi["tong_dong"], cu["tong_dong"])
	la(nhan + " - số dòng bị giấu", moi["bi_cat"], cu["bi_cat"])
	la(nhan + " - tổng tiền", moi["tom_tat"][1]["gt"], cu["tong_tien"])
	for k, v in (cu["dem"] or {}).items():
		la(nhan + " - đếm chip %r" % k, moi["chip"]["dem"].get(k, 0), v)
	la(nhan + " - đúng dòng đúng thứ tự",
		[o["name"] for o in moi["dong"]], [o["name"] for o in cu["don"]])


def _so_hdm(nhan, **tham):
	cu = ke_toan.ds_hoa_don_mua(so_ngay=tham.get("so_ngay", 60),
		tu_khoa=tham.get("tu_khoa", ""), nhom=tham.get("chip"))
	moi = khung_ds.dung(ke_toan.BANG_HOA_DON_MUA, dict(tham))
	la(nhan + " - số dòng hiện", len(moi["dong"]), len(cu["hd"]))
	la(nhan + " - tổng dòng", moi["tong_dong"], cu["tong_dong"])
	la(nhan + " - số dòng bị giấu", moi["bi_cat"], cu["bi_cat"])
	la(nhan + " - tổng tiền", moi["tom_tat"][1]["gt"], cu["tong"])
	la(nhan + " - còn nợ", moi["tom_tat"][2]["gt"], cu["con_no"])
	for k, v in (cu["dem"] or {}).items():
		la(nhan + " - đếm chip %r" % k, moi["chip"]["dem"].get(k, 0), v)
	la(nhan + " - đúng dòng đúng thứ tự",
		[o["name"] for o in moi["dong"]], [o["name"] for o in cu["hd"]])
	la(nhan + " - số ngày trễ khớp từng dòng",
		[o["tre_ngay"] for o in moi["dong"]], [o["tre_ngay"] for o in cu["hd"]])


def _tap_po(n):
	ds = []
	for i in range(n):
		ds.append(don_mua(
			i,
			docstatus=[1, 1, 0, 2][i % 4],
			per_received=[0, 45.5, 100, 100][i % 4],
			per_billed=[0, 0, 30, 100][i % 4],
			status=["To Receive and Bill", "Closed", "Completed", "To Bill"][i % 4],
			schedule_date="2026-08-%02d" % (1 + i % 28),
			grand_total=1000.0 * (i % 97) + 0.5 * (i % 3),
			vgb_huy=1 if i % 23 == 0 else 0,
		))
	return ds


def _tap_hdm(n):
	ds = []
	for i in range(n):
		ds.append(hoa_don_mua(
			i,
			posting_date="2026-08-%02d" % (1 + i % 28),
			due_date="2026-08-%02d" % (1 + i % 28),
			docstatus=[1, 1, 0, 2][i % 4],
			outstanding_amount=[0, 500.75, 1000, 0][i % 4],
			grand_total=1000.0 * (i % 89) + 0.25 * (i % 4),
			vgb_huy=1 if i % 19 == 0 else 0,
			amended_from="HDM-2026-00001" if i % 11 == 0 else "",
		))
	return ds


# ------------------------------------------------------------------- ca

@ca("đơn mua: hai đường ra y hệt nhau trên tập nhỏ")
def _():
	_dat_po(_tap_po(40))
	_so_po("40 đơn")


@ca("đơn mua: hai đường ra y hệt khi tập lớn hơn trần")
def _():
	_dat_po(_tap_po(700))
	_so_po("700 đơn")


@ca("đơn mua: hai đường ra y hệt khi bấm từng chip")
def _():
	_dat_po(_tap_po(400))
	for chip in ["nhap", "cho_nhan", "nhan_mot_phan", "tre_hen",
			"cho_hoa_don", "xong", "dong", "huy"]:
		_so_po("chip " + chip, chip=chip)


@ca("đơn mua: hai đường ra y hệt khi gõ tìm")
def _():
	_dat_po(_tap_po(300))
	_so_po("tìm một từ", tu_khoa="hùng")


@ca("đơn mua: tập rỗng không làm sập đường nào")
def _():
	_dat_po([])
	_so_po("không đơn nào")


@ca("hoá đơn mua: hai đường ra y hệt nhau trên tập nhỏ")
def _():
	_dat_hdm(_tap_hdm(40))
	_so_hdm("40 tờ")


@ca("hoá đơn mua: hai đường ra y hệt khi tập lớn hơn trần")
def _():
	_dat_hdm(_tap_hdm(900))
	_so_hdm("900 tờ")


@ca("hoá đơn mua: hai đường ra y hệt khi bấm từng chip, kể cả chip phụ Đã sửa")
def _():
	_dat_hdm(_tap_hdm(400))
	for chip in ["nhap", "qua_han", "con_no", "da_tra", "da_sua", "huy"]:
		_so_hdm("chip " + chip, chip=chip)


@ca("hoá đơn mua: hai đường ra y hệt khi gõ tìm")
def _():
	_dat_hdm(_tap_hdm(300))
	_so_hdm("tìm một từ", tu_khoa="đào")


@ca("hoá đơn mua: tập rỗng không làm sập đường nào")
def _():
	_dat_hdm([])
	_so_hdm("không tờ nào")


# ------------------------------------------- cac chan rieng cua tang khung

@ca("cổng quyền chặn thật, không phải chặn cho có")
def _():
	import frappe
	cu = frappe.get_roles
	frappe.get_roles = lambda *a, **k: ["Cashier"]
	try:
		_dat_hdm(_tap_hdm(10))
		hong = 0
		try:
			khung_ds.dung(ke_toan.BANG_HOA_DON_MUA, {"so_ngay": 60})
		except Exception as e:
			hong = 1
			dung("báo lỗi bằng tiếng Việt", "kế toán" in str(e))
		la("người không có vai bị chặn", hong, 1)
	finally:
		frappe.get_roles = cu


@ca("mã màn lạ ném lỗi tiếng Việt chứ không nổ ra tiếng Anh")
def _():
	hong = 0
	try:
		khung_ds.lay_bang("KHONGCO")
	except Exception as e:
		hong = 1
		dung("câu tiếng Việt", "màn danh sách" in str(e))
	la("mã lạ bị chặn", hong, 1)


@ca("đường xuất đầy đủ lấy hết dòng, đường màn hình thì cắt")
def _():
	_dat_hdm(_tap_hdm(900))
	man = khung_ds.dung(ke_toan.BANG_HOA_DON_MUA, {"so_ngay": 60})
	day = khung_ds.dung(ke_toan.BANG_HOA_DON_MUA, {"so_ngay": 60}, day_du=1)
	la("màn nhận tối đa trần", len(man["dong"]), 300)
	la("màn báo đúng số dòng bị giấu", man["bi_cat"], 600)
	la("đường đầy đủ lấy hết", len(day["dong"]), 900)
	la("đường đầy đủ không báo cắt", day["bi_cat"], 0)
	la("tiền thật hai đường bằng nhau dù số dòng khác nhau",
		man["tom_tat"][1]["gt"], day["tom_tat"][1]["gt"])


@ca("danh bạ chỉ trả về màn mà người đang đăng nhập được vào")
def _():
	# Quản trị thấy hết. Kiểm bao gồm chứ không kiểm bằng: danh bạ còn dài
	# thêm mỗi lần thêm một màn, chốt cứng danh sách là ca này hỏng mỗi lần
	# ai đó làm đúng việc của mình.
	ra = {x["ma"] for x in khung_ds.danh_ba()}
	la("có hai màn mẫu ban đầu", {"PO", "HDM"} <= ra, True)
	la("có phân hệ Danh mục", {"DMSP", "DMKHO", "DMTK"} <= ra, True)

	# Và điều ca này thật sự muốn kiểm: danh bạ LỌC theo quyền.
	import frappe

	cu = frappe.get_roles
	try:
		frappe.get_roles = lambda *a, **k: ["Cashier"]
		it = {x["ma"] for x in khung_ds.danh_ba()}
		la("vai không liên quan thì danh bạ trống trơn", it, set())

		# Bếp xem được danh mục hàng ngày, KHÔNG xem được giá mua và tài khoản.
		frappe.get_roles = lambda *a, **k: ["Bếp phó"]
		bep = {x["ma"] for x in khung_ds.danh_ba()}
		la("bếp xem được danh mục sản phẩm", "DMSP" in bep, True)
		la("bếp xem được công thức định mức", "DMBOM" in bep, True)
		la("bếp KHÔNG xem được giá mua", "DMGIA" in bep, False)
		la("bếp KHÔNG xem được tài khoản kế toán", "DMTK" in bep, False)
		la("bếp KHÔNG xem được hồ sơ khách hàng", "DMKH" in bep, False)
	finally:
		frappe.get_roles = cu


@ca("hợp đồng dữ liệu trả về đủ mọi khoá màn hình cần")
def _():
	_dat_po(_tap_po(10))
	kq = khung_ds.dung(mua_hang.BANG_PO, {"so_ngay": 60})
	for k in ["ma", "ten", "cot", "dong", "cong", "tom_tat", "chip", "loc",
			"tong_dong", "bi_cat", "gioi_han", "sap", "bieu_do", "tu", "den"]:
		dung("có khoá %s" % k, k in kq)
	for c in kq["cot"]:
		dung("cột %s có kiểu hợp lệ" % c["k"],
			c["kieu"] in ("chu", "tien", "so", "phan_tram", "ngay", "chip"))
