# -*- coding: utf-8 -*-
"""Kiem thu: bao cao phai xem duoc NGAY TRONG NGAY BAN HANG.

Anh Viet 01/09/2026: *"Em xem gap lai toan bo cac bao cao trong phan he bao
cao nhu bao cao xem mon. Hom qua con xem duoc sao hom nay khong thay gi het.
Sua o backend de chay tron tru cho moi diem ban, ke toan xem hang ngay nua.
Theo anh du doan loi thi la qua ngay moi thong ke duoc ngay hom sau, chu
khong realtime duoc."*

Anh doan DUNG. Do so lieu tren site sang 01/09/2026:

    docstatus 0 (chua ghi so)  179 don   71.846.298 d
    docstatus 1 (da ghi so)      3 don    1.882.448 d

Bao cao chi lay docstatus 1 nen ca man hinh gan nhu trong. Khong phai bao
cao hong, cung khong phai bug moi: no van chay dung nhu ngay dau viet ra.
Chi la gia dinh ban dau sai voi cach tiem lam that - quay ban ca ngay, ke
toan ghi so cuoi ngay hoac sang hom sau.

CACH CHUA VA VI SAO CHUA KIEU DO

Khong bo han hang rao docstatus, cung khong giu nguyen. Mac dinh TINH CA don
chua ghi so de nhin duoc trong ngay, nhung LUON dem rieng va noi ro tren man
hinh bao nhieu don, bao nhieu tien dang cho ghi so. Mot con so bao cao ma
khong biet no gom nhung gi thi nguy hiem hon la khong co bao cao.

Rieng bao cao thue dau ra deo co "chot": con so do di thang ra to khai, phai
bang so tren so.

BON CHO DE HONG THAM, bo ca kiem nay canh dung bon cho do:

1. Ky truoc phai dem theo DUNG cong tac cua ky nay, khong thi bao cao luon
   bao "tang manh" du khong ban them dong nao.
2. Chip loc nguon don va phuong thuc phai doc tu TAT CA don, khong thi tat
   cong tac di la chip bien mat, nguoi dung tuong app hong.
3. Bang ke phai co cot Ghi so, khong thi ke toan cong nham don chua ghi so
   vao so lieu chot.
4. Cot canh bao "Thieu ma tham chieu" khong duoc bao tren don chua ghi so:
   tien chua ve thi chua co ma la binh thuong.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import bao_cao as bc

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


class _Dong(dict):
	"""Gia lap frappe._dict: doc duoc bang cham lan bang .get()."""

	def __getattr__(self, k):
		return self.get(k)


def _bo(*cac):
	return [_Dong(x) for x in cac]


# ------------------------------------------------------- 1. cong tac mac dinh

@ca("Bao cao: cong tac don chua ghi so, mac dinh theo tung bao cao")
def _cong_tac():
	la("chua chon thi bao cao thuong BAT", bc._mac_dinh_nhap({}, None), 1)
	la("chua chon thi bao cao chot TAT", bc._mac_dinh_nhap({"chot": 1}, None), 0)
	la("chuoi rong cung la chua chon", bc._mac_dinh_nhap({}, ""), 1)
	la("chuoi rong tren bao cao chot", bc._mac_dinh_nhap({"chot": 1}, ""), 0)
	# Nguoi xem da bam thi y ho thang, ke ca tren bao cao thue: ho co the
	# dang muon uoc luong thue phai nop cua rieng ngay hom nay.
	la("nguoi xem bat thi bat", bc._mac_dinh_nhap({"chot": 1}, "1"), 1)
	la("nguoi xem tat thi tat", bc._mac_dinh_nhap({}, "0"), 0)
	la("so 1 khong phai chuoi", bc._mac_dinh_nhap({}, 1), 1)
	la("so 0 khong phai chuoi", bc._mac_dinh_nhap({}, 0), 0)


@ca("Bao cao: chi bao cao thue moi duoc dat chot")
def _ai_duoc_chot():
	co = sorted(b["ma"] for b in bc.DANH_SACH if b.get("chot"))
	# Dat chot cho mot bao cao van hanh la lai dung cai loi dang chua: ke
	# toan mo ra giua ngay lai thay trong.
	la("dung mot bao cao mang chot", co, ["BC12"])


# ------------------------------------------------------------- 2. hai ham loc

@ca("Bao cao: loc va dem don chua ghi so")
def _loc_va_dem():
	hd = _bo(
		{"_nhap": 1, "grand_total": 100},
		{"_nhap": 0, "grand_total": 50},
		{"_nhap": 1, "grand_total": 25},
	)
	la("bat thi giu nguyen", len(bc._loc_nhap(hd, 1)), 3)
	la("tat thi con don da ghi so", len(bc._loc_nhap(hd, 0)), 1)
	la("dem duoc so don cho", bc._do_nhap(hd)[0], 2)
	la("dem duoc tien cho", bc._do_nhap(hd)[1], 125.0)
	la("khong co don nhap thi bang khong", bc._do_nhap(bc._loc_nhap(hd, 0)),
	   (0, 0.0))
	# Dem PHAI chay tren tap day du, khong phai tap da loc. Goi nham thu tu
	# la dai canh bao im lang dung luc can noi nhat.
	m = _doc("vagabond", "bao_cao.py")
	i = m.find("def chay(")
	than = m[i:i + 2600]
	dung("chay: dem truoc, loc sau", than.find("_do_nhap(tat_ca)") <
	     than.find("_loc_nhap(tat_ca"))


# --------------------------------------------------------- 3. tang hoa don

@ca("Bao cao: doc hoa don lay ca don chua ghi so va gan co")
def _doc_hoa_don():
	m = _doc("vagabond", "bao_cao.py")
	i = m.find("def _hoa_don(")
	than = m[i:m.find("\ndef _loc_nhap(")]
	dung("khong con khoa cung docstatus 1", '"docstatus": 1,' not in than)
	dung("lay ca 0 va 1", '"docstatus": ["in", [0, 1]]' in than)
	dung("co xin cot docstatus ve", '"docstatus",' in than)
	dung("gan co _nhap", 'r["_nhap"]' in than)
	dung("gan nhan ghi so", 'r["ghi_so"]' in than)
	# Hai thu nay khong bao gio duoc tinh, du cong tac bat hay tat.
	dung("van bo don tam tinh", 'vgb_tam_tinh' in than)
	dung("van bo don da huy", 'vgb_huy' in than)


# ------------------------------------------- 4. ba cho de hong tham, canh dung

@ca("Bao cao: ky truoc dem theo dung cong tac cua ky nay")
def _ky_truoc_cung_luat():
	m = _doc("vagabond", "bao_cao.py")
	i = m.find("def _ss_tong(")
	than = m[i:m.find("\n@frappe.whitelist()", i)]
	dung("_ss_tong nhan cong tac", "nhap=1)" in m[i:i + 200])
	dung("ky truoc cung loc theo cong tac", "_loc_nhap(_hoa_don(" in than)
	# Hai cho goi _ss_tong deu phai truyen cong tac xuong.
	la("moi cho goi deu truyen nhap", m.count("_ss_tong(ky, t, d, tong, len(hd)"), 2)
	dung("danh_sach truyen nhap", "diem=diem, nhap=n)" in m)
	dung("chay truyen nhap", "pt=pt, nhap=n)" in m)
	# Bang so sanh tung dong cung phai loc, khong thi cot Ky truoc phong len.
	dung("bang so sanh tung dong cung loc",
	     "_loc_nhap(_hoa_don(tt, dd, diem=diem, nguon=nguon, pt=pt), n)" in m)


@ca("Bao cao: chip loc doc tu tat ca don, tat cong tac khong lam mat chip")
def _chip_khong_bien_mat():
	m = _doc("vagabond", "bao_cao.py")
	dung("nguon_loc doc tu tat ca", 'for r in tat_ca if (r.custom_nguon' in m)
	dung("pt_loc doc tu tat ca", 'for r in tat_ca if (r.vgb_pt_thanh_toan' in m)


@ca("Bao cao: ba bang ke deu co cot Ghi so")
def _bang_ke_co_cot_ghi_so():
	m = _doc("vagabond", "bao_cao.py")
	for ten, moc in (("BC13", "def _bc_ke_hoa_don("),
	                 ("BC14", "def _bc_ke_dong_mon("),
	                 ("BC16", "def _bc_ke_thanh_toan(")):
		i = m.find(moc)
		than = m[i:m.find("\ndef ", i + 10)]
		dung(ten + " co cot Ghi so", '("ghi_so", "Ghi sổ", "chu")' in than)
		dung(ten + " co gia tri Ghi so", '"ghi_so": r.get("ghi_so")' in than)


@ca("Bao cao BC16: khong bao thieu ma tham chieu tren don chua ghi so")
def _bc16_khong_bao_oan():
	hd = _bo(
		{"name": "A", "posting_date": "2026-09-01", "_nhap": 1,
		 "vgb_pt_thanh_toan": "Chuyển khoản", "vgb_ma_tham_chieu": "",
		 "grand_total": 100, "ghi_so": bc.NHAN_NHAP},
		{"name": "B", "posting_date": "2026-09-01", "_nhap": 0,
		 "vgb_pt_thanh_toan": "Chuyển khoản", "vgb_ma_tham_chieu": "",
		 "grand_total": 200, "ghi_so": bc.NHAN_GHI},
		{"name": "C", "posting_date": "2026-09-01", "_nhap": 1,
		 "vgb_pt_thanh_toan": "Chuyển khoản", "vgb_ma_tham_chieu": "FT9",
		 "grand_total": 300, "ghi_so": bc.NHAN_NHAP},
		{"name": "D", "posting_date": "2026-09-01", "_nhap": 1,
		 "vgb_pt_thanh_toan": "Chuyển khoản", "vgb_ma_tham_chieu": "ft9",
		 "grand_total": 400, "ghi_so": bc.NHAN_NHAP},
	)
	canh = {r["hoa_don"]: r["canh_bao"] for r in bc._bc_ke_thanh_toan(hd)["dong"]}
	la("don chua ghi so khong bi bao thieu ma", canh["A"], "")
	la("don da ghi so van bi bao thieu ma", canh["B"], "Thiếu mã tham chiếu")
	# Ma trung thi VAN phai bao, ke ca tren don chua ghi so: mot lan chuyen
	# khoan bi gach cho hai don la sai ngay tu luc gach, khong doi ghi so.
	la("ma trung van bao tren don chua ghi so", canh["C"], "Mã dùng 2 lần")
	la("ma trung khong phan biet hoa thuong", canh["D"], "Mã dùng 2 lần")
	la("cot Ghi so len tung dong", canh and
	   [r["ghi_so"] for r in bc._bc_ke_thanh_toan(hd)["dong"]].count(bc.NHAN_NHAP), 3)


@ca("Bao cao BC05: don chua ghi so co o rieng, khong don vao dong ton dong")
def _bc05_tach_o():
	hd = _bo(
		{"custom_hddt_so": "", "_nhap": 1, "grand_total": 100},
		{"custom_hddt_so": "", "_nhap": 0, "grand_total": 50},
		{"custom_hddt_so": "7", "custom_hddt_trang_thai": "Đã ký",
		 "_nhap": 0, "grand_total": 20},
	)
	gom = {r["trang_thai"]: r["so_hd"] for r in bc._bc_hddt(hd)["dong"]}
	la("don chua ghi so dung o rieng", gom.get("Chưa ghi sổ nên chưa xuất được"), 1)
	la("ton dong that su van dung mot", gom.get("Chưa xuất hoá đơn điện tử"), 1)
	la("don da xuat khong bi dong", gom.get("Đã ký"), 1)


# ------------------------------------------------------ 5. cua ngo va Excel

@ca("Bao cao: ba cua ngo deu nhan cong tac, va Excel ghi lai cong tac do")
def _cua_ngo():
	m = _doc("vagabond", "bao_cao.py")
	for ten in ("danh_sach", "chay", "xuat_excel"):
		i = m.find("def %s(" % ten)
		dung(ten + " nhan tham so nhap", "nhap=None)" in m[i:i + 300])
	i = m.find("def chay(")
	than = m[i:m.find("\n@frappe.whitelist()", i)]
	for k in ('"nhap": n', '"chot":', '"so_nhap": so_nhap', '"tien_nhap": tien_nhap'):
		dung("chay tra ve " + k, k in than)
	dung("chay gui kem danh sach diem ban", '"diem_ban": _diem_ban()' in than)
	i = m.find("def danh_sach(")
	than = m[i:m.find("\n@frappe.whitelist()", i)]
	for k in ('"nhap": n', '"so_nhap": so_nhap', '"tien_nhap": tien_nhap'):
		dung("danh_sach tra ve " + k, k in than)
	# File Excel phai TU NOI no dang o che do nao. Ke toan luu file lai, ba
	# thang sau mo ra ma khong biet no gom don chua ghi so hay khong thi con
	# so do khong dung duoc vao viec gi.
	i = m.find("def xuat_excel(")
	than = m[i:]
	dung("Excel truyen cong tac xuong", "nhap=nhap," in than)
	dung("Excel ghi ro dang o che do nao", "Chỉ đơn đã ghi sổ" in than)
	dung("Excel ghi so don chua ghi so", "Đơn chưa ghi sổ trong kỳ" in than)


# ----------------------------------------------------------- 6. man hinh app

@ca("Man bao cao: khong con go cung ba diem ban")
def _man_diem_dong():
	js = _doc("vagabond", "public", "js", "bep", "14-bao-cao.js")
	i = js.find("var BC_DIEM")
	than = js[i:js.find("function bcThamSo(")]
	# Ba ma nay tung nam thang trong tep. Mo them mot diem ban thi hang chip
	# thieu mat mot cai ma khong ai biet, vi khong co gi bao dong.
	for ma in ("'SALES'", "'TCV'", "'NVHTN'"):
		dung("khong con go cung " + ma, ma not in than)
	dung("co ham dung hang chip tu may chu", "function bcHangDiem(" in js)
	dung("chip diem lay tu bcDsDiem", "bcDsDiem" in js)
	# Ca hai man deu phai nhan danh sach diem ban ve, khong thi mo thang vao
	# man xem mot bao cao la hang chip tut ve ban du phong.
	la("hai man deu nhan danh sach diem", js.count("bcDsDiem = kq.diem_ban"), 2)


@ca("Man bao cao: chip cong tac va dai canh bao")
def _man_cong_tac():
	js = _doc("vagabond", "public", "js", "bep", "14-bao-cao.js")
	dung("co chip bat tat", "data-bcnhap" in js)
	dung("chip co bat su kien", "closest('[data-bcnhap]')" in js)
	dung("co ham ve dai canh bao", "function bcDaiNhap(" in js)
	la("ca hai man deu ve dai", js.count("bcThanhKy() + bcDaiNhap(kq)"), 2)
	# Chua bam thi KHONG duoc gui gi ca. Gui san 1 la ep bao cao thue phai
	# tinh don chua ghi so, dung cai minh vua cat cong de tranh.
	dung("chua chon thi khong gui", "if (bcNhap !== null) o.nhap = bcNhap;" in js)
	dung("chip theo trang thai may chu tra ve", "function bcNhapDangBat(" in js)
	dung("nhan trang thai tu may chu", "bcNhapMayChu = kq.nhap;" in js)
	# Dai canh bao phai co CA HAI ve. Chi ve mot ve la nua kia im lang.
	i = js.find("function bcDaiNhap(")
	than = js[i:js.find("\nfunction ", i + 10)]
	dung("ve dang tinh vao", "Đang tính cả" in than)
	dung("ve dang bo ra", "Đang bỏ ngoài" in than)
	dung("khong don chua ghi so thi im", "if (!so) return '';" in than)
	# Man bao cao thue phai noi ro vi sao no khac cac man con lai.
	dung("man chot co loi nhac khai thue", "đi thẳng ra tờ khai thuế" in js)


@ca("Man duyet don hang tang: ba ho chip ba mau")
def _chip_tang_ba_mau():
	js = _doc("vagabond", "public", "js", "bep", "41-duyet-don-tang.js")
	dung("ham chip nhan mau", "function dtgHangChip(thuoc, dsc, dem, chon, nhanTatCa, mau)" in js)
	for mau in ("'#4338ca'", "'#0d9488'", "'#b45309'"):
		dung("co mau " + mau, mau in js)
	dung("mau truyen xuong nut", "chon === o.k, false, mau" in js)
