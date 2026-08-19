"""Doi soat co "da tao chung tu" cua m-invoice voi chung tu that co trong so.

Vi sao co mo dun nay
--------------------
Ngay 19/08/2026, tim hoa don hoan ve di Uc (Viet Thinh C26THV so 3) thi phat
hien no da bi danh dau `da_tao_chung_tu = 1` ma trong ERP khong he co chung tu
nao. Quet rong ra ca 49.294 ban ghi m-invoice, rieng nhom hoa don AM co 13
cai, va ket qua nhu sau:

    khong co chung tu nao       11 hoa don      61.111.356 d
    co chung tu nhung sai dau    1 hoa don      56.460.090 d   (Grab)
    co chung tu nhung thieu thue 1 hoa don         402.600 d   (Green Ball)

Trong 11 cai bi nuot co hai hoa don DAU RA cua chinh minh, tong 16.460.000 d,
tuc hoa don dieu chinh giam doanh thu. Khong ghi so thi doanh thu dang cao
hon thuc te.

Cai co dang so nhat khong phai la con so, ma la chuyen co `da_tao_chung_tu`
duoc bat len trong khi khong co gi duoc tao ra. Bat co la loi hua "cai nay
xong roi", ma loi hua do dang sai. Khong ai biet, vi khong ai doi chieu.

Mo dun nay lam dung mot viec: doi chieu loi hua voi su that, va goi ten tung
kieu sai. Chi DOC, khong sua gi. Sua hay khong la viec cua ke toan - dung
quy tac cua anh Viet ngay 13/08/2026 ve du lieu cu.
"""

import frappe
from frappe.utils import add_days, cint, flt, nowdate

from vagabond import mua_dich_vu as md

PI = "Purchase Invoice"
SI = "Sales Invoice"

# Bao nhieu ngay tinh nguoc tu hom nay, khi khong ai truyen khoang ngay.
SO_NGAY_MAC_DINH = 180

# Doc mot lan bao nhieu ma hoa don, de cau lenh IN khong phinh qua to.
CO_LO = 200

KHONG_CO = "khong_co_chung_tu"
DA_HUY = "chung_tu_da_huy"

# Bon ma con lai dung chung tu vung tu voi `mua_dich_vu.chan_doan_lech`, de
# hai cho khong bao gio noi hai giong khac nhau ve cung mot kieu sai.
KHOP = "khop"
DAU_NGUOC = "dau_nguoc"
THIEU_THUE = "thieu_dong_thue"
LECH_KHAC = "lech_khac"

MO_TA = {
	KHONG_CO: "Đã đánh dấu tạo chứng từ nhưng không tìm thấy chứng từ nào",
	DA_HUY: "Chứng từ đã bị huỷ, hoá đơn coi như chưa vào sổ",
	DAU_NGUOC: "Hoá đơn âm nhưng chứng từ ghi dương, hoặc ngược lại",
	THIEU_THUE: "Các dòng hàng đúng số, chứng từ thiếu dòng thuế",
	LECH_KHAC: "Tổng chứng từ lệch tổng hoá đơn, chưa xếp được nguyên nhân",
	KHOP: "Khớp",
}


# ------------------------------------------------------------ phep THUAN


def xep_loai(dau, chung_tu):
	"""Hoa don nay dang o tinh trang nao. THUAN.

	`chung_tu` la danh sach dict {"ten", "tong", "tong_thue", "docstatus"}.
	Nhieu chung tu cho mot hoa don thi cong lai roi moi doi chieu: co truong
	hop ke toan tach mot hoa don thanh hai phieu theo tai khoan, tong van
	phai bang.

	Chung tu da huy (docstatus 2) khong tinh la co. Hoa don co chung tu
	nhung tat ca deu da huy thi ket qua khac han voi hoa don chua bao gio co
	chung tu, nen tach thanh hai ma rieng.
	"""
	ds = chung_tu or []
	con = [c for c in ds if cint(c.get("docstatus")) != 2]
	if not con:
		return DA_HUY if ds else KHONG_CO
	tong = sum([flt(c.get("tong")) for c in con])
	thue = sum([flt(c.get("tong_thue")) for c in con])
	return md.chan_doan_lech(dau, tong, thue)


def dang_lo(ma):
	"""Ma nay co phai chuyen can nguoi nhin khong. THUAN."""
	return ma != KHOP


def mo_ta(ma):
	"""Cau tieng Viet cho mot ma. THUAN."""
	return MO_TA.get(ma) or ma


def gom_theo_ma(hang):
	"""Dem tung ma va cong tien tuyet doi cua no. THUAN.

	Tien lay theo tri tuyet doi vi bang nay de do do lon van de, ma hoa don
	am cong voi hoa don duong thi trie tieu nhau, nhin ra so nho gia tao.
	"""
	bang = {}
	for h in hang or []:
		ma = h.get("xep_loai")
		o = bang.setdefault(ma, {"ma": ma, "mo_ta": mo_ta(ma), "so_hoa_don": 0, "tien": 0.0})
		o["so_hoa_don"] += 1
		o["tien"] += abs(flt(h.get("tong_tien")))
	return sorted(bang.values(), key=lambda o: -o["tien"])


# ------------------------------------------------------------ cham vao he


def _chia_lo(ds, co=CO_LO):
	"""Cat danh sach thanh tung lo nho."""
	return [ds[i:i + co] for i in range(0, len(ds), co)]


def _chung_tu_theo_ma(ma_hoa_don):
	"""Doc het chung tu tro ve cac ma hoa don nay, ca mua lan ban."""
	bang = {}
	for dt in (PI, SI):
		for lo in _chia_lo(list(ma_hoa_don)):
			for d in frappe.db.get_all(
				dt,
				filters={"custom_minvoice_id": ["in", lo]},
				fields=[
					"name", "docstatus", "custom_minvoice_id",
					"base_grand_total", "base_total_taxes_and_charges",
				],
			):
				bang.setdefault(d["custom_minvoice_id"], []).append({
					"loai_chung_tu": dt,
					"ten": d["name"],
					"docstatus": d["docstatus"],
					"tong": d["base_grand_total"],
					"tong_thue": d["base_total_taxes_and_charges"],
				})
	return bang


@frappe.whitelist()
def bao_cao(tu_ngay=None, den_ngay=None, chi_van_de=1, gioi_han=3000):
	"""Doi chieu co da_tao_chung_tu voi chung tu that. CHI DOC.

	Khong truyen ngay thi lay 180 ngay gan nhat. `chi_van_de = 0` thi tra ve
	ca nhung hoa don da khop, dung khi muon dem tong.
	"""
	if not frappe.has_permission(PI, "read"):
		frappe.throw("Cần quyền đọc Hoá đơn mua hàng mới xem được báo cáo này.")
	den_ngay = den_ngay or nowdate()
	tu_ngay = tu_ngay or add_days(den_ngay, -SO_NGAY_MAC_DINH)
	gioi_han = cint(gioi_han) or 3000

	hoa_don = frappe.db.get_all(
		"MInvoice Invoice",
		filters={
			"da_tao_chung_tu": 1,
			"ngay_lap": ["between", [tu_ngay, den_ngay]],
		},
		fields=[
			"name", "loai", "ky_hieu", "so_hd", "ngay_lap", "nguoi_mua_ban",
			"tien_truoc_thue", "tien_thue", "tong_tien",
		],
		limit_page_length=gioi_han,
		order_by="ngay_lap desc",
	)
	co_chung_tu = _chung_tu_theo_ma([h["name"] for h in hoa_don])

	hang = []
	for h in hoa_don:
		ds = co_chung_tu.get(h["name"]) or []
		ma = xep_loai(h, ds)
		hang.append({
			"ma_hoa_don": h["name"],
			"loai": h["loai"],
			"ky_hieu": h["ky_hieu"],
			"so_hd": h["so_hd"],
			"ngay_lap": str(h["ngay_lap"] or ""),
			"doi_tac": (h["nguoi_mua_ban"] or "")[:60],
			"tien_truoc_thue": flt(h["tien_truoc_thue"]),
			"tien_thue": flt(h["tien_thue"]),
			"tong_tien": flt(h["tong_tien"]),
			"xep_loai": ma,
			"mo_ta": mo_ta(ma),
			"chung_tu": [c["ten"] for c in ds],
			"tong_chung_tu": sum([
				flt(c["tong"]) for c in ds if cint(c["docstatus"]) != 2
			]),
		})

	tom_tat = gom_theo_ma(hang)
	if cint(chi_van_de):
		hang = [h for h in hang if dang_lo(h["xep_loai"])]
	return {
		"tu_ngay": str(tu_ngay),
		"den_ngay": str(den_ngay),
		"da_quet": len(hoa_don),
		"co_van_de": len([h for h in hang if dang_lo(h["xep_loai"])]),
		"tom_tat": tom_tat,
		"hang": hang,
	}
