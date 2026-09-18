# -*- coding: utf-8 -*-
"""v507: man Xuat kho phuc vu ban hang.

Ca kiem dung lai dung chuoi thao tac cua quay: mo bang dem, go so CON LAI,
bam luu. Khong goi them ham nao ngoai chuoi do.

SO LIEU LAY TU SITE THAT ngay 16/09/2026, khong bia: Kho D1 dang giu
BPKG00011 Hop 2 Banh Entremet 3.920 cai, BPKG00016 Ly giay 14oz 3.570 cai,
NVLT00156 40.855 don vi. Ba ma nay du ba nhom khac nhau nen du de soi ca
phan chia tai khoan.
"""

import json
from types import SimpleNamespace
from unittest.mock import patch

from vagabond import bo_phan, xuat_kho, xuat_noi_bo
from vagabond import xuat_phuc_vu_ban as xp
from vagabond.khung.kiem_thu.nen import ca, dung, la

KHO = "Kho D1 - TV"

# Nhom mon that cua tung ma, doc tu danh muc Mon tren site.
NHOM_THAT = {
	"BPKG00011": "Bao bì",
	"BPKG00016": "Bao bì",
	"CCDC00014": "Công cụ Dụng cụ",
	"NVLT00156": "Nguyên vật liệu Thô",
	"BTPN00001": "Bán thành phẩm Nước",
	"BAEN00043": "Bánh lạnh",
}


def _dong(ma, ton_so, con_lai, nhom=None):
	return {
		"ma": ma,
		"nhom": NHOM_THAT.get(ma, "") if nhom is None else nhom,
		"ton_so": ton_so,
		"con_lai": con_lai,
	}


# ------------------------------------------------------- phep tinh goc


@ca("v507: so da dung la ton tren so tru con lai thuc te")
def _phep_tinh():
	la("dùng 120 trong 3.920", xp.da_dung(3920, 3800), 120.0)
	la("không dùng cái nào", xp.da_dung(3920, 3920), 0.0)
	la("dùng hết", xp.da_dung(400, 0), 400.0)
	la("số lẻ vẫn ra đúng", xp.da_dung(40855, 40312.5), 542.5)


@ca("v507: chua dem thi bo qua chu khong phai loi")
def _chua_dem():
	# Bang dem liet ke MOI ma dang co ton, ma mot tuan thi khong phai ma nao
	# cung dung toi. Bat go so cho ca nhung ma khong dung la buoc nguoi ta
	# go bua cho xong man.
	la("ô trống", xp.soat_mot_dong(_dong("BPKG00011", 3920, None)), ("bo_qua", ""))
	la("chuỗi rỗng", xp.soat_mot_dong(_dong("BPKG00011", 3920, "")), ("bo_qua", ""))
	la("đếm đúng bằng sổ",
		xp.soat_mot_dong(_dong("BPKG00011", 3920, 3920)), ("bo_qua", ""))


@ca("v507: dem it hon so thi ghi vao phieu")
def _co_hang_di_ra():
	viec, cau = xp.soat_mot_dong(_dong("BPKG00011", 3920, 3800))
	la("ghi", viec, "ghi")
	la("không có gì để nhắc", cau, "")


@ca("v507: dem NHIEU hon so thi khong nhan, va chi duong sang Kiem ke")
def _dem_nhieu_hon():
	# Bien no thanh mot dong xuat AM la lam hong so kho va lam hong ca gia
	# von binh quan. Cho do phai di duong kiem ke.
	viec, cau = xp.soat_mot_dong(_dong("BPKG00011", 3920, 4000))
	la("không nhận", viec, "hong")
	dung("nói rõ đếm ra bao nhiêu và sổ ghi bao nhiêu",
		"4000" in cau and "3920" in cau)
	dung("chỉ đúng chỗ cần đến", "Kiểm kê" in cau)
	dung("nói rõ đó không phải hàng đã dùng", "không phải là" in cau)


@ca("v507: so am thi khong nhan")
def _so_am():
	viec, cau = xp.soat_mot_dong(_dong("BPKG00011", 3920, -5))
	la("không nhận", viec, "hong")
	dung("nói rõ vì sao", "số âm" in cau)


# --------------------------------------------- pham vi nhom mon


@ca("v507: banh thanh pham khong di qua man nay, va may noi ro vi sao")
def _banh_ngoai_pham_vi():
	# Anh Viet chot 16/09/2026: banh de nguyen, xu bang viec bat tru kho cho
	# hoa don ban. Man nay tru luon la banh bi tru hai lan.
	dung("bánh lạnh ngoài phạm vi", not xp.trong_pham_vi("Bánh lạnh"))
	dung("thành phẩm bánh ngoài phạm vi", not xp.trong_pham_vi("Thành phẩm Bánh"))
	cau = xp.vi_sao_ngoai_pham_vi("Thành phẩm Bánh")
	dung("nói rõ đi đường hoá đơn bán", "hoá đơn bán" in cau)
	dung("cảnh báo trừ kho hai lần", "hai lần" in cau)
	# Nhom la khong biet cung phai co cau tra loi, im lang la te nhat.
	dung("nhóm lạ vẫn có câu giải thích",
		len(xp.vi_sao_ngoai_pham_vi("Nhóm chưa từng thấy")) > 20)


@ca("v507: dung nam nhom trong pham vi, moi nhom mot nhan tai khoan")
def _pham_vi():
	la("bao bì là chi phí bán hàng",
		xp.nhom_theo_ten("Bao bì")["nhan"], xp.NHAN_CHI_PHI)
	la("công cụ dụng cụ là chi phí bán hàng",
		xp.nhom_theo_ten("Công cụ Dụng cụ")["nhan"], xp.NHAN_CHI_PHI)
	la("văn phòng phẩm là chi phí bán hàng",
		xp.nhom_theo_ten("Văn phòng phẩm")["nhan"], xp.NHAN_CHI_PHI)
	la("nguyên liệu là giá vốn",
		xp.nhom_theo_ten("Nguyên vật liệu Thô")["nhan"], xp.NHAN_GIA_VON)
	la("bán thành phẩm là giá vốn",
		xp.nhom_theo_ten("Bán thành phẩm Nước")["nhan"], xp.NHAN_GIA_VON)
	la("bao bì ưu tiên 6412", xp.nhom_theo_ten("Bao bì")["tk"][0], "6412")
	la("nguyên liệu ưu tiên 632",
		xp.nhom_theo_ten("Nguyên vật liệu Thô")["tk"][0], "632")


@ca("v507: dong mang nhom ngoai pham vi thi bi chan ngay o phep soat")
def _chan_o_phep_soat():
	viec, cau = xp.soat_mot_dong(_dong("BAEN00043", 36, 30))
	la("không nhận", viec, "hong")
	dung("kèm mã hàng", "BAEN00043" in cau)


# ------------------------------------------------- soat ca bang


@ca("v507: soat HET moi dong roi moi tra loi, khong dung o dong hong dau")
def _soat_het():
	# Quay dem ca bang roi bam luu. Bao tung loi mot la bat ho bam luu nam
	# lan.
	se_ghi, nhac = xp.soat_bang_dem([
		_dong("BPKG00011", 3920, 3800),
		_dong("BPKG00016", 3570, 4000),
		_dong("NVLT00156", 40855, -1),
		_dong("CCDC00014", 1900, 1900),
		_dong("BAEN00043", 36, 30),
	])
	la("một dòng có hàng đi ra", len(se_ghi), 1)
	la("đúng dòng đó", se_ghi[0]["ma"], "BPKG00011")
	la("đúng số lượng", se_ghi[0]["sl"], 120.0)
	la("ba câu nhắc, không phải một", len(nhac), 3)


@ca("v507: bang chua dem dong nao thi noi ro, khong de phieu rong")
def _bang_rong():
	se_ghi, nhac = xp.soat_bang_dem([
		_dong("BPKG00011", 3920, None),
		_dong("BPKG00016", 3570, ""),
	])
	la("không có dòng nào", len(se_ghi), 0)
	la("có nhắc", len(nhac), 1)
	dung("nói phải làm gì", "gõ số còn lại" in nhac[0].lower()
		or "Gõ số còn lại" in nhac[0])


# ------------------------------------------- goi y va dien giai


@ca("v507: doan bo phan chiu chi phi tu ten kho")
def _goi_y_bo_phan():
	la("Kho D1", xp.bo_phan_goi_y("Kho D1 - TV"), "Cửa hàng D1")
	la("Kho Sales Online", xp.bo_phan_goi_y("Kho Sales Online - TV"),
		"Sales và bán sỉ")
	la("Kho NVHTN", xp.bo_phan_goi_y("Kho NVHTN - TV"), "Cửa hàng NVHTN")
	la("kho không đoán được", xp.bo_phan_goi_y("Kho tổng 307 - TV"), "")
	la("rỗng", xp.bo_phan_goi_y(""), "")


@ca("v507: dien giai doc duoc ngay tren ban may tinh")
def _dien_giai():
	cau = xp.ghi_chu_phieu("Kho D1", "Cửa hàng D1", "chốt tuần 37")
	dung("có tên màn", "Xuất kho phục vụ bán hàng" in cau)
	dung("có kho", "Kho D1" in cau)
	dung("có bộ phận", "Cửa hàng D1" in cau)
	dung("có ghi chú", "chốt tuần 37" in cau)
	dung("không ghi chú vẫn đọc được",
		"Xuất kho phục vụ bán hàng" in xp.ghi_chu_phieu("Kho D1", "", ""))


# ------------------------------------- chay that qua cua `luu`


class ToGia(SimpleNamespace):
	"""Phieu gia, chi giu lai nhung gi ca kiem can soi.

	`flags` phai co that chu khong duoc roi vao `__getattr__`: ma that gan
	`doc.flags.ignore_permissions`, ma gan thuoc tinh len None thi no.
	"""

	def __init__(self, **k):
		super().__init__(**k)
		self.flags = SimpleNamespace()

	def __getattr__(self, ten):
		return None

	def get(self, ten, mac_dinh=None):
		return getattr(self, ten, mac_dinh)

	def append(self, ten, du):
		if getattr(self, ten, None) is None:
			setattr(self, ten, [])
		getattr(self, ten).append(dict(du))

	def insert(self, ignore_permissions=False):
		self.name = "PXB-GIA-LAP"
		return self


def _tai_khoan_gia():
	"""Cay tai khoan rut gon, dung so that tren site."""
	return [
		{"name": "6412 - Chi phí vật liệu, bao bì - TV", "account_number": "6412"},
		{"name": "6413 - Chi phí dụng cụ, đồ dùng - TV", "account_number": "6413"},
		{"name": "632 - Giá vốn hàng bán - TV", "account_number": "632"},
		{"name": "6428 - Chi phí bằng tiền khác - TV", "account_number": "6428"},
	]


# Ton THAT trong Bin cua tung ma, dung cho ca kiem. Ca kiem nao muon app noi
# doi ve ton_so thi cu gui ton_so khac di, may chu phai lay so o day.
TON_THAT = {
	"BPKG00011": 3920, "BPKG00016": 3570, "CCDC00014": 1900,
	"NVLT00156": 40855, "BTPN00001": 4960, "BAEN00043": 36,
}


def _chay_luu(dong, bp="Cửa hàng D1", tai_khoan=None, ton_that=None, phieu_cho=None):
	"""Chay chinh `xp.luu`, chi chan phan cham co so du lieu."""
	giu = {}
	ton = TON_THAT if ton_that is None else ton_that

	def _get_all(dt, **k):
		if dt == "Account":
			return _tai_khoan_gia() if tai_khoan is None else tai_khoan
		if dt == "Item":
			ma = k.get("filters", {}).get("name", [None, []])[1]
			return [{"name": m, "item_group": NHOM_THAT.get(m, "")} for m in ma]
		if dt == "Bin":
			ma = k.get("filters", {}).get("item_code", [None, []])[1]
			return [{"item_code": m, "actual_qty": ton[m]} for m in ma if m in ton]
		if dt == "Stock Entry":
			giu["loc_phieu_cho"] = k.get("filters", {})
			return [{"name": phieu_cho}] if phieu_cho else []
		return []

	def _new_doc(dt):
		t = ToGia()
		giu["to"] = t
		return t

	gia = SimpleNamespace(
		get_all=_get_all,
		new_doc=_new_doc,
		db=SimpleNamespace(
			get_value=lambda dt, n, f=None, **k: {"abbr": "TV"}.get(f, "Kho D1"),
			exists=lambda dt, n: True,
			commit=lambda: None,
		),
		throw=lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[0])),
	)
	with patch.object(xp, "frappe", gia), \
			patch.object(xuat_kho, "_duoc_xuat", lambda: None), \
			patch.object(xuat_kho, "_cong_ty", lambda: "CTY"), \
			patch.object(xuat_kho, "_chan_qua_ton", lambda kho, sach: None), \
			patch.object(xuat_kho, "_tk_chi_phi", lambda ct: "632 - Giá vốn hàng bán - TV"), \
			patch.object(bo_phan, "la_bo_phan_hop_le", lambda t: bool((t or "").strip())), \
			patch.object(bo_phan, "ten_that", lambda t, vt: "%s - %s" % (t, vt)):
		ra = xp.luu(kho=KHO, bo_phan_chiu=bp, ghi_chu="chốt tuần", dong=json.dumps(dong))
	return ra, giu.get("to")


@ca("v507: luu that - moi nhom mon ve dung tai khoan cua no")
def _luu_dung_tai_khoan():
	ra, t = _chay_luu([
		_dong("BPKG00011", 3920, 3800),
		_dong("CCDC00014", 1900, 1850),
		_dong("NVLT00156", 40855, 40000),
	])
	la("lập được phiếu", ra["ok"], 1)
	la("ba dòng", len(t.items), 3)
	tk = {d["item_code"]: d["expense_account"] for d in t.items}
	la("bao bì vào 6412", tk["BPKG00011"], "6412 - Chi phí vật liệu, bao bì - TV")
	la("công cụ dụng cụ vào 6413", tk["CCDC00014"],
		"6413 - Chi phí dụng cụ, đồ dùng - TV")
	la("nguyên liệu vào 632", tk["NVLT00156"], "632 - Giá vốn hàng bán - TV")
	sl = {d["item_code"]: d["qty"] for d in t.items}
	la("số lượng bao bì", sl["BPKG00011"], 120.0)
	la("số lượng nguyên liệu", sl["NVLT00156"], 855.0)
	la("phiếu là bản nháp chờ ghi sổ", ra["trang_thai"], "Chờ ghi sổ")
	la("mang đúng mã của màn này", t.vgb_muc_dich_xuat, xuat_kho.MA_PHUC_VU_BAN)
	la("mọi dòng mang bộ phận của điểm bán",
		{d["cost_center"] for d in t.items}, {"Cửa hàng D1 - TV"})


@ca("v507: luu that - nhom mon doc tu danh muc, KHONG tin app gui len")
def _khong_tin_app():
	# App gui gi thi gui, cai quyet dinh tai khoan ghi so phai doc tu danh
	# muc Mon. Tin app la mo duong cho mot dong banh thanh pham di vao phieu
	# nay voi nhan "Bao bi".
	loi = ""
	try:
		_chay_luu([_dong("BAEN00043", 36, 30, nhom="Bao bì")])
	except AssertionError as e:
		loi = str(e)
	dung("bị chặn", "BAEN00043" in loi)
	dung("chặn đúng lý do", "hoá đơn bán" in loi)


@ca("v507: luu that - dong chua dem khong vao phieu")
def _chua_dem_khong_vao_phieu():
	ra, t = _chay_luu([
		_dong("BPKG00011", 3920, 3800),
		_dong("BPKG00016", 3570, None),
		_dong("CCDC00014", 1900, 1900),
	])
	la("chỉ một dòng vào phiếu", len(t.items), 1)
	la("đúng dòng đó", t.items[0]["item_code"], "BPKG00011")
	la("máy báo đúng số dòng", ra["so_dong"], 1)


@ca("v507: luu that - chua chon bo phan thi khong luu")
def _thieu_bo_phan():
	loi = ""
	try:
		_chay_luu([_dong("BPKG00011", 3920, 3800)], bp="")
	except AssertionError as e:
		loi = str(e)
	dung("có chặn", "bộ phận" in loi.lower())


@ca("v507: ton tren so lay tu Bin luc luu, KHONG tin ton_so app gui len")
def _khong_tin_ton_so():
	# Codex bat tren PR #341: ton co 100, app gui ton_so 90 va con_lai 80
	# thi phai xuat 20 chu khong phai 10. Ton_so app gui co the cu hoac bi
	# sua, `_chan_qua_ton` chi chan xuat VUOT ton, khong bat duoc xuat THIEU.
	ra, t = _chay_luu(
		[_dong("BPKG00011", 90, 80)],
		ton_that={"BPKG00011": 100},
	)
	la("xuất theo tồn thật, không theo tồn app gửi", t.items[0]["qty"], 20.0)


@ca("v507: app gui ton_so cao hon ton that de xuat qua tay thi bi chan")
def _ton_so_bia_cao():
	# Chieu nguoc lai: app khai ton_so 200 trong khi Bin chi co 100, con_lai
	# 80. Tin app la xuat 120 tu mot kho chi co 100. May chu dat lai ton_so
	# theo Bin nen chi xuat 20, khong can nem loi.
	ra, t = _chay_luu([_dong("BPKG00011", 200, 80)], ton_that={"BPKG00011": 100})
	la("chỉ xuất 20 theo tồn thật", t.items[0]["qty"], 20.0)


@ca("v507: chon tai khoan khop CHINH XAC, 6328 khong cuop cho cua 632")
def _tai_khoan_chinh_xac():
	# Codex bat tren PR #341: startswith("632") nhan luon "6328 - Hao hut"
	# neu no dung truoc trong danh sach, va nguyen lieu vao thang hao hut.
	co_6328_truoc = [
		{"name": "6328 - Hao hụt - TV", "account_number": "6328"},
		{"name": "632 - Giá vốn hàng bán - TV", "account_number": "632"},
	]
	la("có 632 thì lấy đúng 632 dù 6328 đứng trước",
		xuat_kho.chon_tai_khoan(co_6328_truoc, ("632", "621")),
		"632 - Giá vốn hàng bán - TV")
	chi_co_6328 = [
		{"name": "6328 - Hao hụt - TV", "account_number": "6328"},
		{"name": "621 - Chi phí NVL trực tiếp - TV", "account_number": "621"},
	]
	la("không có 632 thì tụt về 621 chứ không lấy 6328",
		xuat_kho.chon_tai_khoan(chi_co_6328, ("632", "621")),
		"621 - Chi phí NVL trực tiếp - TV")
	la("hết dãy thì trả None để người gọi tự lùi",
		xuat_kho.chon_tai_khoan(chi_co_6328, ("632",)), None)
	# Khop theo ten khi o account_number trong: khuon "632 - ..." cua tiem.
	theo_ten = [{"name": "632 - Giá vốn hàng bán - TV", "account_number": ""}]
	la("khớp theo tên khi thiếu số",
		xuat_kho.chon_tai_khoan(theo_ten, ("632",)), "632 - Giá vốn hàng bán - TV")
	# Chay that qua luu voi cay tai khoan co 6328 dung truoc.
	ra, t = _chay_luu([_dong("NVLT00156", 40855, 40000)], tai_khoan=co_6328_truoc + _tai_khoan_gia())
	la("nguyên liệu vào 632, không vào 6328",
		t.items[0]["expense_account"], "632 - Giá vốn hàng bán - TV")


@ca("v507: bo_phieu chi bo phieu cua man nay")
def _bo_phieu_dung_pham_vi():
	# Codex bat tren PR #341: khong co dong kiem nay thi cua nay bo duoc ca
	# phieu xuat dung noi bo hay phieu dieu chuyen nhap cua nguoi khac.
	gia = SimpleNamespace(
		get_doc=lambda dt, n: ToGia(docstatus=0, vgb_muc_dich_xuat="marketing", vgb_huy=0, owner="ai_do"),
		throw=lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[0])),
		session=SimpleNamespace(user="ai_do"),
	)
	loi = ""
	with patch.object(xp, "frappe", gia), \
			patch.object(xuat_kho, "_duoc_xuat", lambda: None), \
			patch.object(xuat_kho, "duoc_duyet", lambda: True):
		try:
			xp.bo_phieu("X", "thu")
		except AssertionError as e:
			loi = str(e)
	dung("từ chối phiếu của màn khác", "không phải phiếu xuất kho phục vụ bán hàng" in loi)


@ca("v507: chi_tiet tra ai ghi so va luc nao cho to da ghi so")
def _ai_ghi_so():
	# Codex bat tren PR #341: khong co hai o nay thi man xem phieu khong bao
	# gio noi duoc ai da tru kho.
	def _to(docstatus):
		t = ToGia(name="PXB-1", docstatus=docstatus, vgb_huy=0, owner="quay@x",
			modified_by="ketoan@x", modified="2026-09-17 09:30:00.123456",
			posting_date="2026-09-17", from_warehouse=KHO, remarks="", total_outgoing_value=0)
		t.items = []
		return t

	def _gv(dt, n, f=None, **k):
		return {"quay@x": "Quầy D1", "ketoan@x": "Chị Dung"}.get(n, n)

	for ds, mong_nguoi in ((1, "Chị Dung"), (0, "")):
		gia = SimpleNamespace(
			get_doc=lambda dt, n, _ds=ds: _to(_ds),
			db=SimpleNamespace(get_value=_gv),
			session=SimpleNamespace(user="quay@x"),
		)
		with patch.object(xp, "frappe", gia), \
				patch.object(xuat_kho, "_duoc_xuat", lambda: None), \
				patch.object(xuat_kho, "duoc_duyet", lambda: False), \
				patch.object(xuat_kho, "anh_theo_ma", lambda ma: {}):
			r = xp.chi_tiet("PXB-1")
		la("người ghi sổ (docstatus %s)" % ds, r["nguoi_ghi_so"], mong_nguoi)
		la("lúc ghi sổ (docstatus %s)" % ds, r["luc_ghi_so"], "2026-09-17 09:30" if ds else "")


# ------------------------- hai man khong duoc keo phieu cua nhau


@ca("v507: hai man cung ghi vao mot o, moi man phai loc DUNG ma cua minh")
def _khong_keo_phieu_cua_nhau():
	# Ngay 02/09/2026 man Xuat dung noi bo tung mac dung loi nay voi Xuat
	# huy. Them man thu ba ma giu cach loc cu la lap lai lan nua.
	giu = {}

	def _bat(mo_dun):
		def _get_all(dt, **k):
			giu[mo_dun] = k.get("filters") or {}
			return []
		return _get_all

	gia_xp = SimpleNamespace(get_all=_bat("moi"), db=SimpleNamespace(
		get_value=lambda *a, **k: "", count=lambda *a, **k: 0))
	with patch.object(xp, "frappe", gia_xp), \
			patch.object(xuat_kho, "_duoc_xuat", lambda: None):
		xp.ds_phieu()

	gia_nb = SimpleNamespace(get_all=_bat("noi_bo"), db=SimpleNamespace(
		get_value=lambda *a, **k: "", count=lambda *a, **k: 0))
	with patch.object(xuat_noi_bo, "frappe", gia_nb), \
			patch.object(xuat_kho, "_duoc_xuat", lambda: None):
		xuat_noi_bo.ds_phieu()

	la("màn mới lọc đúng mã của mình",
		giu["moi"].get("vgb_muc_dich_xuat"), xuat_kho.MA_PHUC_VU_BAN)
	loc_nb = giu["noi_bo"].get("vgb_muc_dich_xuat")
	la("màn nội bộ dùng phép loại trừ", loc_nb[0], "not in")
	dung("và loại đúng mã của màn mới", xuat_kho.MA_PHUC_VU_BAN in loc_nb[1])
	dung("vẫn loại ô rỗng như cũ", "" in loc_nb[1])


@ca("v507: ghi so phieu cua man kia thi bi chan o ca hai chieu")
def _ghi_so_cheo():
	def _phieu(ma_muc_dich):
		return ToGia(docstatus=0, vgb_muc_dich_xuat=ma_muc_dich, vgb_huy=0)

	gia = SimpleNamespace(
		get_doc=lambda dt, n: _phieu(xuat_kho.MA_PHUC_VU_BAN),
		throw=lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[0])),
	)
	loi = ""
	with patch.object(xuat_noi_bo, "frappe", gia), \
			patch.object(xuat_kho, "duoc_duyet", lambda: True):
		try:
			xuat_noi_bo.ghi_so("X")
		except AssertionError as e:
			loi = str(e)
	dung("màn nội bộ từ chối phiếu của màn mới", "phục vụ bán hàng" in loi)

	gia2 = SimpleNamespace(
		get_doc=lambda dt, n: _phieu("marketing"),
		throw=lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[0])),
	)
	loi2 = ""
	with patch.object(xp, "frappe", gia2), \
			patch.object(xuat_kho, "duoc_duyet", lambda: True):
		try:
			xp.ghi_so("Y")
		except AssertionError as e:
			loi2 = str(e)
	dung("màn mới từ chối phiếu của màn nội bộ",
		"không phải phiếu xuất kho phục vụ bán hàng" in loi2)


@ca("v507: mot kho chi co MOT phieu cho ghi so, lap lai thi bi chan")
def _mot_kho_mot_phieu_cho():
	# Codex bat tren PR #344: mat phan hoi HTTP roi bam lai, hoac hai nguoi
	# cung chot mot kho, la hai phieu nhap cung so da dung. Ca hai deu ghi
	# so thi ton 100 dem 80 bi tru hai lan con 60.
	loi = ""
	try:
		_chay_luu([_dong("BPKG00011", 3920, 3800)], phieu_cho="PXB-CU")
	except AssertionError as e:
		loi = str(e)
	dung("bị chặn", bool(loi))
	dung("nói tên phiếu đang chờ", "PXB-CU" in loi)
	dung("chỉ đường: ghi sổ hoặc bỏ phiếu đó trước", "Ghi sổ hoặc bỏ phiếu đó" in loi)
	# Khong co phieu cho thi lap binh thuong, va bo loc phai dung MA cua man
	# nay, dung kho nay, chi phieu nhap chua bo.
	ra, t = _chay_luu([_dong("BPKG00011", 3920, 3800)])
	la("không có phiếu chờ thì lập được", ra["ok"], 1)


@ca("v507: bo loc phieu cho ghi so: dung ma man nay, dung kho, chi nhap chua bo")
def _loc_phieu_cho():
	giu = {}

	def _get_all(dt, **k):
		giu["loc"] = k.get("filters")
		return []

	with patch.object(xp, "frappe", SimpleNamespace(get_all=_get_all)):
		la("chưa có thì trả rỗng", xp._phieu_cho_cua_kho("Kho D1 - TV"), "")
	loc = giu["loc"]
	la("đúng mã màn", loc.get("vgb_muc_dich_xuat"), xuat_kho.MA_PHUC_VU_BAN)
	la("đúng kho", loc.get("from_warehouse"), "Kho D1 - TV")
	la("chỉ bản nháp", loc.get("docstatus"), 0)
	la("chưa bị bỏ", loc.get("vgb_huy"), 0)


@ca("v507: bang dem ghim kho da hoi, cau tra loi ve muon cua kho khac thi bo")
def _ghim_kho_da_hoi():
	# Codex bat tren PR #344. Day la phep DO CHUOI, khong phai chay: chot
	# rang lenh goi bang_dem dung bien ghim, va sau await co phep so lai
	# voi kho dang chon truoc khi ghi. Chay that tren trinh duyet chua co.
	import io
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	j = io.open(os.path.join(goc, "public", "js", "bep", "46-xuat-phuc-vu-ban.js"), encoding="utf-8").read()
	than = j.split("async function napBang()")[1].split("async function")[0]
	dung("ghim kho trước khi chờ", "var khoHoi = st.kho;" in than)
	dung("gọi máy chủ bằng kho đã ghim", "bang_dem', { kho: khoHoi }" in than)
	dung("về muộn mà kho đã đổi thì bỏ", than.count("if (st.kho !== khoHoi) return;") == 2)
	dung("ghi bảng theo kho đã ghim", "XPV.bangKho = khoHoi;" in than)
	dung("không còn chỗ nào gán bangKho = st.kho", "XPV.bangKho = st.kho" not in than)


@ca("v508: man Xuat kho phuc vu ban hang co duong dan rieng, F5 khong roi ve phan he")
def _co_duong_dan_rieng():
	# v507 len site 18/09/2026: bam o thi vao duoc, nhung URL van la
	# /phan-he-xuat-kho vi bang duong dan (may sinh tu duong_app.MAN) khong
	# co XKPV. Khai o duong_app.MAN la NGUON DUY NHAT, bang JS phai theo.
	import io
	import os
	from vagabond import duong_app
	dung("duong_app.MAN có XKPV", any(k[0] == "XKPV" for k in duong_app.MAN))
	la("slug đúng", duong_app.DUONG.get("xuat-kho-phuc-vu-ban-hang"), "XKPV")
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	j = io.open(os.path.join(goc, "public", "js", "bep", "02-trang-chu.js"), encoding="utf-8").read()
	dung("bảng JS có slug", "'xuat-kho-phuc-vu-ban-hang': 'XKPV'" in j)
