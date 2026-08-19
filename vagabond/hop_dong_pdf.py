# -*- coding: utf-8 -*-
"""HOP DONG MUA BAN HANG HOA: sinh to phap ly tu bao gia da chot.

Anh Viet 18/08/2026: "Hien tai he thong moi chi sinh duoc Thu bao gia. Anh
can bo sung tinh nang Tao hop dong tu Bao gia da chot."

Vi sao mot to rieng chu khong in them mot trang vao bao gia
-----------------------------------------------------------
Bao gia va hop dong tra loi hai cau hoi khac han. Bao gia noi "hang nay
gia bao nhieu" va co the sua lai vong hai vong ba. Hop dong noi "hai ben
cam ket dieu gi va toa an nao xu neu cai nhau", va mot khi da ky thi
khong sua duoc nua.

Nen to hop dong chup lai (snapshot) thong tin Ben A tai thoi diem ky, chu
khong tro sang ho so khach hang. Sang nam khach doi ten cong ty hay doi
nguoi dai dien thi hop dong cu van phai doc ra dung cai da ky.

Ba lua chon anh Viet chot 18/08/2026
------------------------------------
  loai to        HOP DONG MUA BAN HANG HOA, so hieu HDMB. Mau anh gui de
                 tieu de "dich vu" nhung than bai lai ghi "mua ban hang
                 hoa" va vien dan Luat Thuong mai - nen chuan hoa theo
                 than bai chu khong theo tieu de.
  Dieu 2         chia hai dot theo dung o Dat coc tren bao gia, khong cung
                 50/50. So tien dot 1 tinh LAI o may chu (QT-19).
  so hop dong    giu dung mau cu: 20260818/HDMB/MOI-VGB

Cai chua lam: chu ky dien tu. Anh Viet yeu cau trinh bay phuong an truoc,
xem tai lieu du an claude/phuong-an-ky-dien-tu.md.
"""

import base64
import unicodedata

import frappe
from frappe.utils import cint, flt, getdate, nowdate

from vagabond.cong_no import _chu_so_tien, _tien_vn

DT = "Hop Dong Ban Hang"
DT_BG = "Bao Gia Ban Hang"

# Ai duoc dung to hop dong. Cung bo quyen voi phan he hop dong dang chay,
# nap tu do chu khong chep lai - hai ban song song thi lech nhau luc nao
# khong hay (bai hoc tu vgbGo 16/08/2026).


def _quyen(sua=False):
	from vagabond.hop_dong import QUYEN

	if not QUYEN & set(frappe.get_roles()):
		frappe.throw(
			"Hợp đồng chỉ mở cho Sales, Thu mua, Kế toán và Giám đốc. "
			"Cần xem thì báo anh Việt cấp thêm chức vụ trong màn Quản lý người dùng."
		)


# ------------------------------------------------------------- phep thuan

def _khong_dau(s):
	"""Bo dau tieng Viet. THUAN, chi dung thu vien chuan.

	Co ban giong danh_muc.khong_dau, nhung KHONG nap tu do: mo dun danh_muc
	keo theo frappe.model, ma cong kiem truoc deploy chay tren may khong co
	bench. Mot ham bay dong de doi lay mot phep tinh kiem thu duoc la doi
	hoi.
	"""
	s = unicodedata.normalize("NFD", str(s or ""))
	s = "".join(c for c in s if unicodedata.category(c) != "Mn")
	return s.replace("đ", "d").replace("Đ", "D")


# Hai nhom tu bi bo khi rut ten viet tat.
#
# Nhom mot: loai hinh doanh nghiep. Cong ty nao cung co nen khong phan biet
# duoc ai voi ai.
TU_LOAI_HINH = {
	"CONG", "TY", "TNHH", "CO", "PHAN", "CP", "MTV", "MOT", "THANH", "VIEN",
	"DOANH", "NGHIEP", "TU", "NHAN", "HO", "KINH", "SO", "CHI", "NHANH",
	"VN", "VIETNAM", "VIET", "NAM", "AND", "VA", "GROUP", "HOLDINGS",
	"CORPORATION", "CORP", "COMPANY", "LIMITED", "LTD", "JSC", "INC",
}

# Nhom hai: nganh nghe. Day la nhom anh Viet bat duoc loi 18/08/2026:
# "CONG TY TNHH TU VAN GIAI PHAP SECOMM" ra "VAN" chu khong phai "SECOMM".
#
# Ly do loi: bo duoc "TU" nhung giu lai "VAN" (cua chu "VAN" trong "tu van"),
# roi thay tu dau tien chi 3 chu nen tuong do la mot cum viet tat.
#
# Ten cong ty Viet Nam gan nhu luon co dang: loai hinh + nganh nghe + TEN
# RIENG. Bo ca hai nhom dau thi con lai dung cai can lay.
TU_NGANH_NGHE = {
	"TUVAN", "VAN", "GIAI", "PHAP", "THUONG", "MAI", "DICH", "VU", "SAN",
	"XUAT", "NHAP", "KHAU", "DAU", "PHAT", "TRIEN", "XAY", "DUNG", "KY",
	"THUAT", "CONGNGHE", "NGHE", "GIAO", "DUC", "DAO", "TAO", "VAN", "TAI",
	"LOGISTICS", "SOLUTIONS", "SOLUTION", "SERVICES", "SERVICE", "TRADING",
	"TECHNOLOGY", "TECH", "CONSULTING", "COSMETICS", "FOOD", "FOODS",
	"BEVERAGE", "MEDIA", "AGENCY", "PATISSERIE", "BAKERY", "RESTAURANT",
	"HOTEL", "TRAVEL", "TOUR", "TOURS", "REAL", "ESTATE", "PROPERTY",
	"DEVELOPMENT", "INVESTMENT", "MANAGEMENT", "INTERNATIONAL", "GLOBAL",
	"THUCPHAM", "THUC", "PHAM", "MY", "NGHIENCUU", "NGHIEN", "CUU",
}


def viet_tat_khach(ten):
	"""Cum viet tat cua ten cong ty, dung trong so hop dong. THUAN.

	"CONG TY TNHH TU VAN GIAI PHAP SECOMM"  -> "SECOMM"
	"CONG TY TNHH M.O.I COSMETICS"          -> "MOI"
	"CONG TY TNHH ELLE VIET NAM"            -> "ELLE"
	"CONG TY TNHH PATISSERIE VAGABOND"      -> "VAGABOND"

	Cach lam: ten cong ty Viet Nam gan nhu luon co dang loai hinh, roi nganh
	nghe, roi TEN RIENG. Bo hai nhom dau thi con lai dung cai can lay.

	Bo het ca hai nhom ma khong con gi (vi du "CONG TY TNHH THUONG MAI") thi
	lui ve lay tu CUOI CUNG cua phan da bo loai hinh - trong tieng Viet ten
	rieng nam o cuoi, khong nam o dau.

	Day chi la GOI Y. Nguoi lap sua tay duoc truoc khi ky, nen tha doan hoi
	tho con hon bat ho go tay tu dau.
	"""
	tho = str(ten or "").replace(".", "").replace(",", " ").replace("-", " ")
	tu = [t for t in tho.split() if t]
	if not tu:
		return ""
	# Buoc mot: bo loai hinh doanh nghiep.
	con = [t for t in tu if _khong_dau(t).upper() not in TU_LOAI_HINH]
	if not con:
		con = tu
	# Buoc hai: bo nganh nghe. Neu bo het thi giu nguyen buoc mot.
	rieng = [t for t in con if _khong_dau(t).upper() not in TU_NGANH_NGHE]
	if not rieng:
		rieng = con[-1:]

	# Con dung MOT tu thi lay nguyen tu do, con nhieu tu thi ghep chu cai
	# dau. Khong doan them gi nua.
	#
	# Truoc do co mot nhanh "tu dau viet hoa ngan thi lay nguyen", de bat
	# cac cum nhu MOI hay KFC. Nhanh do thua va con hai: "JU YOUNG ISU
	# FUTURE GROW" bi cat con "JU". Bo di thi MOI va KFC van dung, vi sau
	# khi bo nganh nghe chung chi con dung mot tu.
	if len(rieng) == 1:
		ra = _khong_dau(rieng[0]).upper()
	else:
		ra = "".join(_khong_dau(t)[0] for t in rieng if _khong_dau(t))
	ra = "".join(c for c in ra.upper() if c.isalnum())
	return ra[:12]


def so_hop_dong(ngay, ten_khach, loai="HDMB"):
	"""Sinh so hop dong theo mau anh Viet chot. THUAN.

	20260818/HDMB/MOI-VGB. Ngay viet lien, ma loai, roi viet tat ten khach
	gach noi VGB.
	"""
	try:
		d = getdate(ngay)
		phan_ngay = "%04d%02d%02d" % (d.year, d.month, d.day)
	except Exception:
		phan_ngay = str(ngay or "").replace("-", "")[:8]
	vt = viet_tat_khach(ten_khach)
	return "%s/%s/%s-VGB" % (phan_ngay, loai, vt) if vt else "%s/%s/VGB" % (phan_ngay, loai)


def chia_hai_dot(tong, phan_tram_dot1):
	"""Chia gia tri hop dong thanh hai dot. THUAN.

	Tra ve (tien_dot1, tien_dot2). Hai so cong lai PHAI bang dung tong, nen
	dot 2 lay phan con lai chu khong nhan phan tram lan nua - nhan hai lan
	thi lam tron hai lan va hop dong lech vai dong bac.

	Phan tram ngoai khoang 0..100 bi keo ve trong khoang: mot hop dong ghi
	"dot 1 tra 150%" la thu khong duoc phep in ra.
	"""
	tong = flt(tong)
	pt = flt(phan_tram_dot1)
	if pt < 0:
		pt = 0.0
	if pt > 100:
		pt = 100.0
	dot1 = round(tong * pt / 100.0)
	return dot1, tong - dot1


# Anh Viet 18/08/2026: *"Cam dung em-dash: trong van ban tieng Viet, thay
# toan bo dau em-dash thanh dau gach ngang tieu chuan cho toan bo van ban"*.
#
# Ma nguon cua app khong con dau nao loai nay, nhung to hop dong in ra ca
# nhung chu do NGUOI GO: ten mon tren bao gia, dieu kien thanh toan, ghi
# chu... Nguoi go tren may Mac hay Word rat de sinh ra dau dai, va lam sach
# tung o mot thi kieu gi cung sot. Nen chan o mot cho duy nhat: moi chu di
# vao to in deu chay qua _esc.
DAU_DAI = {
	"\u2013": "-",   # en dash
	"\u2014": "-",   # em dash
	"\u2012": "-",   # figure dash
	"\u2015": "-",   # horizontal bar
	"\u2212": "-",   # minus sign
	"\u2010": "-",   # hyphen
	"\u2011": "-",   # non-breaking hyphen
}


def don_dau_dai(s):
	"""Doi moi kieu gach dai ve gach ngang thuong. THUAN."""
	t = str(s or "")
	for k, v in DAU_DAI.items():
		t = t.replace(k, v)
	return t


def _esc(s):
	return (
		don_dau_dai(s)
		.replace("&", "&amp;")
		.replace("<", "&lt;")
		.replace(">", "&gt;")
	)


def _br(s):
	return _esc(s).replace("\n", "<br>")


# Xung ho phai bo khoi o ky (anh Viet 18/08/2026): "Phai ghi ro ho va ten
# chu khong ghi Ms." O ky la cho phap ly, khong phai cho chao hoi.
XUNG_HO = ("MS.", "MS", "MR.", "MR", "MRS.", "MRS", "MISS", "ONG", "BA", "ANH", "CHI")


def _bo_xung_ho(ten):
	"""Bo Ms., Mr., Ong, Ba... o dau ten. THUAN.

	Ho so khach hay luu ten kieu "Ms.Trang Pham" vi do la cach Sales go khi
	nhan tin. Dua nguyen si vao o ky hop dong thi to giay thanh khong dung
	the thuc.
	"""
	t = str(ten or "").strip()
	if not t:
		return ""
	# Tach ca truong hop khong co dau cach sau dau cham: "Ms.Trang Pham".
	tho = t.replace(".", ". ")
	tu = [x for x in tho.split() if x]
	while tu and _khong_dau(tu[0]).upper().rstrip(".") + ("." if tu[0].endswith(".") else "") in XUNG_HO:
		tu.pop(0)
	if not tu:
		return t
	return " ".join(tu)


def _ngay_en(d):
	"""Ngay thang kieu Anh, dung cho phan song ngu."""
	thang = ("January", "February", "March", "April", "May", "June", "July",
	         "August", "September", "October", "November", "December")
	try:
		x = getdate(d)
		return "%d %s %d" % (x.day, thang[x.month - 1], x.year)
	except Exception:
		return "..... ..... ....."


def _ngay_vn(d):
	try:
		x = getdate(d)
		return "ngày %02d tháng %02d năm %d" % (x.day, x.month, x.year)
	except Exception:
		return "ngày ..... tháng ..... năm ....."


# ------------------------------------------------------------- doc du lieu

def _ben_b():
	"""Thong tin Ben B, lay tu Cai dat bao gia - khai mot noi dung ca hai to."""
	from vagabond.bao_gia import _cd

	c = _cd()
	# Uu tien khoi NGUOI KY khai rieng cho hop dong; khong khai thi moi lui
	# ve khoi nguoi lien he cua to bao gia.
	#
	# Anh Viet 18/08/2026: *"hien em dang lay thong tin email va so dien
	# thoai cua Loan Anh gan cho anh la sao"*. Dung vay: ba o dai_dien_ban,
	# dt_ban, email_ban la nguoi lien he cua to bao gia, Loan Anh khai ten
	# minh vao do la dung viec cua no. To hop dong thi phai lay nguoi dat
	# but ky, va so dien thoai email di kem phai la cua chinh nguoi do.
	return {
		"ten": c.get("ten_ban") or "CÔNG TY TNHH PATISSERIE VAGABOND",
		"mst": c.get("mst_ban") or "",
		"dia_chi": c.get("dia_chi_ban") or "",
		"dai_dien": c.get("nguoi_ky_ban") or c.get("dai_dien_ban") or "",
		"chuc_vu": c.get("chuc_vu_ky_ban") or c.get("chuc_vu_ban") or "Giám đốc",
		"dien_thoai": c.get("dt_ky_ban") or c.get("dt_ban") or "",
		"email": c.get("email_ky_ban") or c.get("email_ban") or "",
		"ngan_hang": c.get("ngan_hang_vi") or "",
		# Giu rieng de goi y cho man tao hop dong, khong lan voi o tren.
		"ky_ten": c.get("nguoi_ky_ban") or "",
		"ky_chuc_vu": c.get("chuc_vu_ky_ban") or "Giám đốc",
		"ky_dt": c.get("dt_ky_ban") or "",
		"ky_email": c.get("email_ky_ban") or "",
	}


@frappe.whitelist()
def chi_tiet(name):
	"""Mot hop dong, du thu de man hinh ve va de dung to PDF."""
	_quyen()
	if not frappe.db.exists(DT, name):
		frappe.throw("Không tìm thấy hợp đồng %s. Anh chị mở lại danh sách giúp em." % name)
	d = frappe.get_doc(DT, name).as_dict()
	for k in list(d.keys()):
		if k.startswith("_"):
			d.pop(k, None)
	d["ben_b"] = _ben_b()
	d["so_goi_y"] = so_hop_dong(d.get("ngay_ky") or nowdate(), d.get("ten_khach") or "")
	dot1, dot2 = chia_hai_dot(d.get("gia_tri"), d.get("dat_coc_pt"))
	d["tien_dot1"] = dot1
	d["tien_dot2"] = dot2
	d["dong_bao_gia"] = []
	if d.get("bao_gia") and frappe.db.exists(DT_BG, d["bao_gia"]):
		bg = frappe.get_doc(DT_BG, d["bao_gia"])
		d["dong_bao_gia"] = [
			{
				"ten_mon": r.ten_mon,
				"dvt": r.dvt,
				"so_luong": flt(r.so_luong),
				"don_gia": flt(r.don_gia),
				"thanh_tien": flt(r.thanh_tien),
				"thue_pt": flt(r.get("thue_pt")),
			}
			for r in (bg.dong or [])
		]
		# Bang tach thue cua to hop dong lay DUNG phep cua to bao gia, khong
		# tu cong lai lan hai: hai noi cung cong thi hai noi se lech nhau
		# vao mot ngay khong ai doan truoc.
		try:
			from vagabond.bao_gia import tom_tat_thue as _tt_bg

			d["tom_tat_thue"] = _tt_bg(bg.as_dict())
		except Exception:
			d["tom_tat_thue"] = None
		d["bg_thue_pt"] = flt(bg.thue_pt)
		d["bg_gia_da_gom_vat"] = cint(bg.gia_da_gom_vat)
		d["bg_giao_hang"] = bg.giao_hang or ""
	# Nguoi ky ben B: KHONG lui ve o "dai dien" cua Cai dat bao gia nua.
	#
	# Nghiem thu 18/08/2026 bat duoc: o do dang ghi "Loan Anh / Sales
	# Manager", tuc la ban Sales, dung y cai anh Viet cam: *"khong duoc lay
	# mac dinh ten cua ban Sales"*. O do la nguoi lien he tren to bao gia,
	# khong phai nguoi dat but ky hop dong.
	#
	# De trong thi to in ra cham cham de nguoi ta dien tay, va man tao hop
	# dong do san bang nguoi ky cua hop dong gan nhat (xem goi_y_hop_dong).
	if not (d.get("chuc_vu_ky_b") or "").strip():
		d["chuc_vu_ky_b"] = "Giám đốc"
	d["co_phu_luc_scan"] = 1 if d.get("phu_luc_scan") else 0
	return d


# ------------------------------------------------------------------ to PDF

def _bang_hang(d):
	"""Bang Dieu 1. Lay tung dong tu bao gia nguon neu con, khong thi mot dong gop."""
	dong = d.get("dong_bao_gia") or []
	# To tron nhieu muc thue thi KHONG duoc ghi mot con so phan tram o day:
	# ghi "da gom VAT 8%" trong khi trong bang co ca dong 10% va dong 0% la
	# noi sai voi khach. Truong hop do chi ghi "da gom VAT", con chi tiet
	# tung muc nam o cac dong tach thue ngay duoi.
	tt0 = d.get("tom_tat_thue") or None
	nhieu_muc = bool(tt0) and len([
		m for m in tt0["theo_muc"] if flt(m["tien_hang"]) or flt(m["tien_thue"])
	]) > 1
	vat = ""
	if d.get("bg_gia_da_gom_vat") or flt(d.get("bg_thue_pt")):
		if nhieu_muc:
			vat = "<br>(đã gồm VAT)"
		else:
			vat = "<br>(đã gồm VAT %s%%)" % (
				_tien_vn(d.get("bg_thue_pt")) if flt(d.get("bg_thue_pt")) else "8"
			)
	def _th(vi, en, rong="", canh="center"):
		return (
			'<th style="border:1px solid #000;padding:5px 6px;text-align:%s;%s">'
			"%s<div style=\"font-style:italic;color:#555;font-weight:normal;"
			'font-size:10.5px">%s</div></th>' % (canh, rong, vi, en)
		)

	th = (
		'<tr style="background:#f2f2f2">'
		+ _th("STT", "No.", "width:36px")
		+ _th("Tên hàng", "Description", "", "left")
		+ _th("ĐVT", "Unit", "width:56px")
		+ _th("Số lượng", "Qty", "width:62px")
		+ _th("Đơn giá%s" % vat, "Unit price", "width:100px")
		+ _th("Thành tiền%s" % vat, "Amount", "width:110px")
		+ "</tr>"
	)
	hang = []
	if dong:
		for i, x in enumerate(dong, 1):
			hang.append(
				'<tr><td style="border:1px solid #000;padding:5px 6px;text-align:center">%d.</td>'
				'<td style="border:1px solid #000;padding:5px 6px">%s</td>'
				'<td style="border:1px solid #000;padding:5px 6px;text-align:center">%s</td>'
				'<td style="border:1px solid #000;padding:5px 6px;text-align:center">%s</td>'
				'<td style="border:1px solid #000;padding:5px 6px;text-align:right">%s</td>'
				'<td style="border:1px solid #000;padding:5px 6px;text-align:right">%s</td></tr>'
				% (i, _esc(x["ten_mon"]), _esc(x.get("dvt") or ""), _tien_vn(x["so_luong"]),
				   _tien_vn(x["don_gia"]), _tien_vn(x["thanh_tien"]))
			)
	else:
		hang.append(
			'<tr><td style="border:1px solid #000;padding:5px 6px;text-align:center">1.</td>'
			'<td style="border:1px solid #000;padding:5px 6px">%s</td>'
			'<td style="border:1px solid #000;padding:5px 6px;text-align:center">Gói</td>'
			'<td style="border:1px solid #000;padding:5px 6px;text-align:center">1</td>'
			'<td style="border:1px solid #000;padding:5px 6px;text-align:right">%s</td>'
			'<td style="border:1px solid #000;padding:5px 6px;text-align:right">%s</td></tr>'
			% (_esc(d.get("ten") or "Hàng hoá theo báo giá đính kèm"),
			   _tien_vn(d.get("gia_tri")), _tien_vn(d.get("gia_tri")))
		)
	tong = (
		'<tr><td colspan="5" style="border:1px solid #000;padding:5px 6px;text-align:right;'
		'font-weight:bold">TỔNG TIỀN%s'
		'<div style="font-style:italic;color:#555;font-weight:normal;font-size:10.5px">'
		"TOTAL</div></td>"
		'<td style="border:1px solid #000;padding:5px 6px;text-align:right;font-weight:bold">%s</td></tr>'
		% (vat.replace("<br>", " "), _tien_vn(d.get("gia_tri")))
	)
	# Ba dong khach hay hoi, in ngay duoi dong TONG TIEN (anh Viet
	# 18/08/2026): *"nhieu khach ho yeu cau so tien truoc thue va so tien
	# sau thue, so tien thue"*.
	if tt0:
		def _dong_cong(vi, en, tien, dam=False):
			return (
				'<tr><td colspan="5" style="border:1px solid #000;padding:4px 6px;'
				'text-align:right;%s">%s'
				'<div style="font-style:italic;color:#555;font-weight:normal;'
				'font-size:10px">%s</div></td>'
				'<td style="border:1px solid #000;padding:4px 6px;text-align:right;%s">%s</td></tr>'
				% ("font-weight:bold" if dam else "", _esc(vi), _esc(en),
				   "font-weight:bold" if dam else "", _tien_vn(tien))
			)

		muc = [m for m in tt0["theo_muc"] if flt(m["tien_hang"]) or flt(m["tien_thue"])]
		tong += _dong_cong("Cộng tiền hàng chưa thuế", "Subtotal excluding VAT", tt0["tien_hang"])
		if len(muc) > 1:
			for m in muc:
				tong += _dong_cong(
					"Thuế GTGT %g%% trên %s" % (flt(m["thue_pt"]), _tien_vn(m["tien_hang"])),
					"VAT %g%%" % flt(m["thue_pt"]), m["tien_thue"],
				)
			tong += _dong_cong("Cộng tiền thuế GTGT", "Total VAT", tt0["tien_thue"])
		else:
			tong += _dong_cong(
				"Thuế GTGT %g%%" % (flt(muc[0]["thue_pt"]) if muc else 0),
				"VAT", tt0["tien_thue"],
			)
		tong += _dong_cong(
			"TỔNG CỘNG ĐÃ GỒM THUẾ", "Total including VAT", tt0["tong_cong"], dam=True
		)
	return (
		'<table style="width:100%;border-collapse:collapse;font-size:11.5px;margin:8px 0">'
		+ th + "".join(hang) + tong + "</table>"
	)


def _o_ben(nhan, nhan_en, b):
	"""Khoi thong tin mot ben, song ngu, dung khuon mau anh Viet gui."""
	dong = [
		("Tên công ty", "Company", b.get("ten")),
		("Địa chỉ", "Address", b.get("dia_chi")),
		("Mã số thuế", "Tax code", b.get("mst")),
		# Bo xung ho o CA khoi thong tin ben, khong chi o ky. Ho so khach
		# hay luu "Ms.Trang Pham" vi do la cach Sales go khi nhan tin, ma
		# to hop dong thi khong ghi Ms. o cho nao ca.
		("Đại diện", "Representative", _bo_xung_ho(b.get("dai_dien"))),
		("Chức vụ", "Title", b.get("chuc_vu")),
	]
	if b.get("dien_thoai"):
		dong.append(("Điện thoại", "Tel", b.get("dien_thoai")))
	if b.get("email"):
		dong.append(("Email", "Email", b.get("email")))
	if b.get("ngan_hang"):
		dong.append(("Tài khoản", "Bank details", b.get("ngan_hang")))
	than = "".join(
		'<tr><td style="padding:2px 0;width:150px;vertical-align:top">%s'
		'<div style="font-style:italic;color:#555;font-size:11px">%s</div></td>'
		'<td style="padding:2px 0;vertical-align:top">: %s</td></tr>'
		% (_esc(k), _esc(k_en), _br(v or "..........."))
		for k, k_en, v in dong
	)
	return (
		'<div style="margin:11px 0 3px">'
		'<div style="font-weight:bold">%s</div>'
		'<div style="font-style:italic;color:#555;font-size:11px">%s</div></div>'
		'<table style="width:100%%;font-size:12px;border-collapse:collapse">%s</table>'
		% (_esc(nhan), _esc(nhan_en), than)
	)


def cau_dieu_2(tong, pt1, n1=3, n2=3):
	"""Cau chu cua Dieu 2, chia hai dot hoac tra mot lan. THUAN, song ngu.

	Tach han ra khoi _html vi day chinh la cho vua vo khi nghiem thu v215:
	cau "Ben A thanh toan 100% gia tri Hop dong" co dau phan tram khong
	duoc thoat, nen Python doc "% g" thanh mot o dinh dang va nem loi
	"must be real number, not str". Ca to hop dong tra ve 500.

	Bo kiem truoc do khong bat duoc vi khong ca nao dung tay to voi coc
	bang 0. Nay phep nay THUAN nen kiem duoc ca hai nhanh ma khong can site.
	"""
	tong = flt(tong)
	pt1 = flt(pt1)
	n1 = cint(n1) or 3
	n2 = cint(n2) or 3
	dot1, dot2 = chia_hai_dot(tong, pt1)

	def _dot(vi, en):
		return (
			'<div style="margin:4px 0 0 14px">%s</div>'
			'<div style="margin:1px 0 0 14px;font-style:italic;color:#555">%s</div>'
			% (vi, en)
		)

	if pt1 <= 0 or pt1 >= 100:
		return _dot(
			"Bên A thanh toán 100%% giá trị Hợp đồng, tương đương số tiền "
			"<b>%s VNĐ</b> (Bằng chữ: %s), chậm nhất trước %02d (%s) ngày bàn "
			"giao hàng hóa theo lịch giao hàng đã được hai Bên thống nhất."
			% (_tien_vn(tong), _chu_so_tien(tong), n2, _so_chu(n2)),
			"Party A shall pay 100%% of the Contract value, equivalent to "
			"<b>VND %s</b>, at the latest %02d (%s) days before the delivery date "
			"agreed by both Parties." % (_tien_vn(tong), n2, _so_chu_en(n2)),
		)
	return _dot(
		"Đợt 01: Bên A thanh toán %s%% giá trị Hợp đồng, tương đương số tiền "
		"<b>%s VNĐ</b> (Bằng chữ: %s), trong vòng %02d (%s) ngày kể từ ngày Hợp "
		"đồng được hai Bên ký kết."
		% (_tien_vn(pt1), _tien_vn(dot1), _chu_so_tien(dot1), n1, _so_chu(n1)),
		"Instalment 01: Party A shall pay %s%% of the Contract value, equivalent "
		"to <b>VND %s</b>, within %02d (%s) days from the signing date."
		% (_tien_vn(pt1), _tien_vn(dot1), n1, _so_chu_en(n1)),
	) + _dot(
		"Đợt 02: Bên A thanh toán %s%% giá trị Hợp đồng còn lại, tương đương số "
		"tiền <b>%s VNĐ</b> (Bằng chữ: %s), chậm nhất trước %02d (%s) ngày bàn "
		"giao hàng hóa theo lịch giao hàng đã được hai Bên thống nhất."
		% (_tien_vn(100.0 - pt1), _tien_vn(dot2), _chu_so_tien(dot2), n2, _so_chu(n2)),
		"Instalment 02: Party A shall pay the remaining %s%% of the Contract "
		"value, equivalent to <b>VND %s</b>, at the latest %02d (%s) days before "
		"the delivery date agreed by both Parties."
		% (_tien_vn(100.0 - pt1), _tien_vn(dot2), n2, _so_chu_en(n2)),
	)


def _so_chu_en(n):
	"""Doc mot so nho bang chu tieng Anh, dung cho "03 (three) days". THUAN."""
	bang = {
		1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
		7: "seven", 8: "eight", 9: "nine", 10: "ten", 14: "fourteen",
		15: "fifteen", 20: "twenty", 30: "thirty",
	}
	return bang.get(cint(n), str(cint(n)))


# ------------------------------------------------------- to hop dong song ngu
#
# Anh Viet 18/08/2026 chot ba dieu ve the thuc:
#
#   font        Arial cho ca hop dong lan phu luc. Truoc do dung Times New
#               Roman, va chu "PHU LUC 01" bi vo font tren ban PDF.
#   dau gach    khong dung en dash, chi dung gach ngang thuong. Day cung la
#               quy uoc trinh bay chung cua tiem.
#   song ngu    dich toan bo sang tieng Anh, dat NGAY DUOI phan tieng Viet
#               tuong ung, in nghieng.
#
# Cach dung song ngu o day di theo dung nep to bao gia: MOT cua duy nhat
# sinh chu tieng Anh, nen khong the co chuyen mot doan quen ban tieng Anh
# hay mot doan quen in nghieng. Bai hoc tu to bao gia 15/08/2026: khi co ba
# cho ghep chu Anh thang vao HTML thi to in ra nua nghieng nua dung.

# Xau phong lay tu vagabond/phong_chu.py de bao gia va hop dong khong bao
# gio lech nhau. Doc chu thich dai o day neu thac mac vi sao phai mang
# theo bo phong rieng: server chi co Liberation Sans 1.07.4, ban do thieu
# chu tieng Viet co dau thanh nen wkhtmltopdf muon tam DejaVu Sans cho
# rieng nhung chu do, thanh ra hai kieu chu lech nhau trong cung mot tu.
from vagabond.phong_chu import NGAN_XEP as FONT_TO  # noqa: E402

# Anh Viet 18/08/2026, lan thu hai: *"hien tai van bi loi font (co ve no
# khong phai la font ARIAL, anh dinh kem luon cho em cai font ne)"*.
#
# Em da tai mot to PDF THAT do site sinh ra ve roi doc xem trong do nhung
# nhung phong gi. Ket qua:
#
#     LiberationSans, LiberationSans-Bold, LiberationSans-Italic,
#     LiberationSans-BoldItalic, DejaVuSans, DejaVuSans-Bold
#
# Doc ra hai dieu. Mot, may chu CO SAN Liberation Sans du bon kieu. Do la
# ban thay the do rong khop tung ly voi Arial, in ra nhin nhu Arial that,
# nen khai "Arial" roi de fontconfig thay bang no la dung y do. Khong
# thieu phong.
#
# Hai, VAN CON mot phan chu roi ve DejaVu Sans. Do moi la cho anh nhin ra
# "loi font": trong cung mot to co hai kieu chu. Nguyen nhan la cau CSS cu
# chi liet ke mot so the (body, td, th, div, p, span, b, i, table). The nao
# ngoai danh sach do - li, ul, strong, em, small, h1 den h6 - thi khong
# nhan font-family nao ca va roi ve phong mac dinh cua may chu.
#
# Da thu huong nhet phong vao tep: wkhtmltopdf ve chu thanh duong thay vi
# nhung phong, to hop dong phinh tu 69 KB len 3,4 MB va khong con copy
# duoc chu. May chu da co san phong thi khong dang doi nhu vay.
def khung_style(phong=None):
	"""Cau CSS ap font cho MOI the trong to in.

	Dung dau sao chu khong liet ke ten the: chi can mot the nam ngoai danh
	sach la cho do roi ve phong khac, va trong mot to hop dong thi hai kieu
	chu canh nhau nhin ra ngay.
	"""
	return "*{font-family:%s}" % (phong or FONT_TO)


def _en(chu):
	"""Mot doan tieng Anh: in nghieng, mau nhat hon. Rong thi tra ve rong."""
	chu = (chu or "").strip()
	if not chu:
		return ""
	return '<div style="font-style:italic;color:#555;margin:1px 0 0">%s</div>' % chu


def vi_en(vi, en, dam=False):
	"""Mot cap cau Viet - Anh. THUAN."""
	kieu = "font-weight:bold;" if dam else ""
	return '<div style="%smargin:5px 0 0">%s</div>%s' % (kieu, vi, _en(en))


def _gach(vi, en):
	"""Mot gach dau dong song ngu.

	Dung GACH NGANG THUONG chu khong phai en dash - quy uoc trinh bay cua
	tiem, va anh Viet nhac lai 18/08/2026 cho rieng to hop dong.
	"""
	return (
		'<div style="margin:5px 0 0 0;padding-left:14px;text-indent:-14px">- %s</div>'
		'<div style="margin:1px 0 0 14px;font-style:italic;color:#555">%s</div>'
		% (vi, en)
	)


def _html(name):
	"""To hop dong mua ban hang hoa song ngu, cau truc hanh chinh Viet Nam."""
	d = chi_tiet(name)
	b = dict(d["ben_b"])
	# O "Dai dien" cua khoi thong tin Ben B phai la NGUOI KY, khong phai o
	# "dai dien" khai trong Cai dat bao gia.
	#
	# Nghiem thu tren site that 18/08/2026: o do dang ghi "Loan Anh / Sales
	# Manager". Anh Viet: *"khong duoc lay mac dinh ten cua ban Sales"*.
	# Chan ngay tai day, la cho DUY NHAT chu chay ra giay, nen du du lieu
	# vao co ban the nao thi to in ra van sach.
	#
	# De trong thi in cham cham, nhin la biet con thieu. Con hon in ten ban
	# Sales ra roi ky gui khach.
	b["dai_dien"] = (d.get("nguoi_ky_b") or "").strip()
	b["chuc_vu"] = (d.get("chuc_vu_ky_b") or "").strip() or "Giám đốc"
	# So dien thoai va email in canh ten phai la CUA CHINH NGUOI KY do,
	# khong thi to hop dong ghi ten Giam doc ma so may thi cua ban Sales.
	if (d.get("dt_ky_b") or "").strip():
		b["dien_thoai"] = d["dt_ky_b"].strip()
	if (d.get("email_ky_b") or "").strip():
		b["email"] = d["email_ky_b"].strip()
	# Ben A cung mot luat: khai nguoi ky rieng thi in nguoi do, khong khai
	# thi lui ve nguoi lien he chup tu to bao gia.
	a = {
		"ten": d.get("ten_khach"),
		"mst": d.get("ma_so_thue"),
		"dia_chi": d.get("dia_chi"),
		"dai_dien": (d.get("nguoi_ky_a") or "").strip() or d.get("dai_dien"),
		"chuc_vu": (d.get("chuc_vu_ky_a") or "").strip() or d.get("chuc_vu"),
		"dien_thoai": (d.get("dt_ky_a") or "").strip() or d.get("dien_thoai"),
		"email": (d.get("email_ky_a") or "").strip() or d.get("email"),
	}
	so = d.get("so_hop_dong") or d["so_goi_y"]
	pt1 = flt(d.get("dat_coc_pt"))
	n1 = cint(d.get("ngay_dot1")) or 3
	n2 = cint(d.get("ngay_dot2")) or 3
	tong = flt(d.get("gia_tri"))
	dot1, dot2 = chia_hai_dot(tong, pt1)

	def dieu(so_dieu, tua_vi, tua_en):
		return (
			'<div style="margin:14px 0 4px">'
			'<div style="font-weight:bold;text-transform:uppercase">ĐIỀU %d: %s</div>'
			'<div style="font-style:italic;color:#555;text-transform:uppercase">'
			"ARTICLE %d: %s</div></div>" % (so_dieu, _esc(tua_vi), so_dieu, _esc(tua_en))
		)

	ra = []
	ra.append(
		'<div style="text-align:center;line-height:1.5">'
		'<div style="font-weight:bold;font-size:13px">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>'
		'<div style="font-weight:bold;font-size:12.5px;text-decoration:underline">'
		"Độc lập - Tự do - Hạnh phúc</div>"
		'<div style="font-style:italic;color:#555;font-size:11.5px">'
		"SOCIALIST REPUBLIC OF VIETNAM - Independence - Freedom - Happiness</div></div>"
	)
	ra.append(
		'<div style="text-align:center;margin:18px 0 4px">'
		'<div style="font-weight:bold;font-size:16px">HỢP ĐỒNG MUA BÁN HÀNG HÓA</div>'
		'<div style="font-style:italic;color:#555;font-size:12.5px">GOODS SALE AND PURCHASE CONTRACT</div>'
		'<div style="font-size:12px;margin-top:3px">Số / <i>No.</i>: %s</div></div>' % _esc(so)
	)
	ra.append(
		'<div style="margin-top:12px;font-size:12px;line-height:1.6">'
		"<b>Căn cứ:</b>"
		'<div style="font-style:italic;color:#555">Pursuant to:</div>'
		+ _gach(
			"Bộ luật Dân sự số 91/2015/QH13 ngày 24/11/2015 của Quốc hội nước "
			"Cộng hòa Xã hội Chủ nghĩa Việt Nam;",
			"The Civil Code No. 91/2015/QH13 dated 24 November 2015 of the "
			"National Assembly of the Socialist Republic of Vietnam;",
		)
		+ _gach(
			"Luật Thương mại số 36/2005/QH11 ngày 14/06/2005 của Quốc hội nước "
			"Cộng hòa Xã hội Chủ nghĩa Việt Nam;",
			"The Commercial Law No. 36/2005/QH11 dated 14 June 2005 of the "
			"National Assembly of the Socialist Republic of Vietnam;",
		)
		+ _gach(
			"Căn cứ nhu cầu và khả năng của hai Bên.",
			"The needs and capabilities of both Parties.",
		)
		+ "</div>"
	)
	ra.append(
		vi_en(
			"Hôm nay, %s, tại Thành phố Hồ Chí Minh, chúng tôi gồm:"
			% _ngay_vn(d.get("ngay_ky") or nowdate()),
			"Today, %s, in Ho Chi Minh City, we are:"
			% _ngay_en(d.get("ngay_ky") or nowdate()),
		)
	)
	ra.append(_o_ben("BÊN MUA (gọi tắt là Bên A)", "THE BUYER (hereinafter referred to as Party A)", a))
	ra.append(_o_ben("BÊN BÁN (gọi tắt là Bên B)", "THE SELLER (hereinafter referred to as Party B)", b))
	ra.append(
		vi_en(
			"Sau khi thỏa thuận, hai Bên thống nhất ký Hợp đồng mua bán hàng hóa "
			"với những nội dung dưới đây:",
			"After negotiation, both Parties agree to sign this Goods Sale and "
			"Purchase Contract with the following terms:",
		)
	)

	ra.append(dieu(1, "HÀNG HÓA", "GOODS"))
	ra.append(
		vi_en(
			"Bên B đồng ý bán và Bên A đồng ý mua số lượng hàng hóa như sau:",
			"Party B agrees to sell and Party A agrees to buy the following goods:",
		)
	)
	ra.append(_bang_hang(d))
	ra.append(
		'<div style="margin-top:4px"><i>(Bằng chữ: %s./.)</i>'
		'<div style="font-style:italic;color:#555">(In words: %s VND only.)</div></div>'
		% (_chu_so_tien(tong), _tien_vn(tong))
	)
	if d.get("bao_gia") or d.get("phu_luc_scan"):
		ra.append(
			vi_en(
				"Chi tiết quy cách, hình ảnh và điều kiện vận hành xem tại "
				"<b>Phụ lục 01</b> đính kèm, là bộ phận không tách rời của Hợp đồng này.",
				"Detailed specifications, images and operating conditions are set "
				"out in <b>Appendix 01</b> attached hereto, which forms an "
				"integral part of this Contract.",
			)
		)

	ra.append(dieu(2, "THANH TOÁN", "PAYMENT"))
	ra.append(
		_gach(
			"Hình thức thanh toán: Chuyển khoản theo số tài khoản do Bên B cung "
			"cấp trong Hợp đồng này.",
			"Payment method: Bank transfer to the account provided by Party B herein.",
		)
	)
	ra.append(_gach("Phương thức thanh toán:", "Payment schedule:"))
	ra.append(cau_dieu_2(tong, pt1, n1, n2))
	if b.get("ngan_hang"):
		ra.append(_gach("Thông tin chuyển khoản:", "Bank details:"))
		ra.append('<div style="margin-left:14px">%s</div>' % _br(b["ngan_hang"]))
	ra.append(
		_gach(
			"Chứng từ kèm theo: Hóa đơn giá trị gia tăng hợp lệ (cung cấp sau khi giao hàng).",
			"Accompanying documents: A valid VAT invoice (issued after delivery).",
		)
	)

	ra.append(dieu(3, "QUY CÁCH, CHẤT LƯỢNG HÀNG HÓA", "SPECIFICATIONS AND QUALITY"))
	ra.append(
		_gach(
			"Hàng hóa do Bên B cung cấp được sản xuất đúng quy cách, số lượng, "
			"tiêu chuẩn như mẫu đã được hai Bên duyệt.",
			"The goods supplied by Party B shall be produced in accordance with "
			"the specifications, quantity and standards of the samples approved "
			"by both Parties.",
		)
		+ _gach(
			"Trong trường hợp hàng hóa do Bên B bàn giao bị hư hỏng hoặc thiếu, "
			"Bên B có trách nhiệm khắc phục trong thời gian sớm nhất.",
			"If the goods delivered by Party B are damaged or short in quantity, "
			"Party B shall remedy the situation as soon as possible.",
		)
		+ _gach(
			"Bên B không đổi lại hàng trong trường hợp sản phẩm hư hỏng do các "
			"điều kiện khách quan gây ra (tác động ngoại lực, rơi vỡ do lỗi của "
			"người sử dụng).",
			"Party B shall not replace goods damaged by objective causes "
			"(external impact, dropping or breakage due to the user's fault).",
		)
	)

	ra.append(dieu(4, "ĐỊA ĐIỂM, THỜI GIAN BÀN GIAO HÀNG HÓA", "PLACE AND TIME OF DELIVERY"))
	tg = d.get("thoi_gian_giao") or d.get("bg_giao_hang") or ""
	ra.append(
		_gach(
			"Thời gian: %s"
			% (_br(tg) or "theo lịch giao hàng hai Bên thống nhất bằng văn bản."),
			"Time: %s"
			% (_br(tg) or "as per the delivery schedule agreed in writing by both Parties."),
		)
		+ _gach(
			"Địa điểm bàn giao hàng: %s" % (_br(d.get("dia_diem_giao")) or "..........."),
			"Place of delivery: %s" % (_br(d.get("dia_diem_giao")) or "..........."),
		)
	)

	ra.append(dieu(5, "TRÁCH NHIỆM CỦA HAI BÊN", "RESPONSIBILITIES OF THE PARTIES"))
	ra.append(vi_en("5.1. Trách nhiệm của Bên A:", "5.1. Responsibilities of Party A:", dam=True))
	ra.append(
		_gach(
			"Thanh toán cho Bên B theo quy định tại Điều 2 của Hợp đồng này.",
			"Pay Party B in accordance with Article 2 of this Contract.",
		)
		+ _gach(
			"Hỗ trợ, tạo điều kiện thuận lợi, chuẩn bị mặt bằng và các điều kiện "
			"làm việc sẵn sàng cho Bên B trong thời gian giao hàng.",
			"Support and facilitate Party B, prepare the venue and working "
			"conditions during the delivery period.",
		)
		+ _gach(
			"Trong trường hợp Bên A đơn phương hủy Hợp đồng mà không được sự chấp "
			"thuận của Bên B, Bên A sẽ không được hoàn lại khoản tiền đã thanh "
			"toán cho Bên B.",
			"If Party A unilaterally terminates this Contract without Party B's "
			"consent, Party A shall not be refunded any amount already paid to Party B.",
		)
		+ _gach(
			"Kiểm tra chi tiết quy cách, số lượng, tiêu chuẩn hàng hóa và ký nhận "
			"biên bản giao nhận tại thời điểm Bên B giao hàng.",
			"Inspect the specifications, quantity and standards of the goods and "
			"sign the handover record at the time of delivery.",
		)
	)
	ra.append(vi_en("5.2. Trách nhiệm của Bên B:", "5.2. Responsibilities of Party B:", dam=True))
	ra.append(
		_gach(
			"Giao hàng đúng quy cách, thời gian, số lượng, tiêu chuẩn như đã cam "
			"kết và quy định tại Điều 1.",
			"Deliver the goods in the correct specifications, time, quantity and "
			"standards as committed and stipulated in Article 1.",
		)
		+ _gach(
			"Cung cấp đầy đủ các chứng từ kèm theo tại Điều 2.",
			"Provide all accompanying documents stipulated in Article 2.",
		)
		+ _gach(
			"Nhanh chóng giải quyết khiếu nại của khách hàng liên quan đến hàng "
			"hóa do Bên B cung cấp.",
			"Promptly resolve customer complaints relating to the goods supplied "
			"by Party B.",
		)
		+ _gach(
			"Chịu trách nhiệm trước pháp luật về nguồn gốc, phẩm chất, tính pháp "
			"lý của hàng hóa do Bên B cung cấp.",
			"Be legally responsible for the origin, quality and legality of the "
			"goods supplied by Party B.",
		)
		+ _gach(
			"Trong trường hợp xảy ra sự cố ngộ độc thực phẩm, Bên B phải bồi "
			"thường nếu có thiệt hại xảy ra cho Bên A; trường hợp này phải có sự "
			"điều tra và chứng minh do lỗi của nhà sản xuất.",
			"In the event of food poisoning, Party B shall compensate any damage "
			"caused to Party A, subject to investigation proving the fault of the "
			"manufacturer.",
		)
		+ _gach(
			"Bên B không chịu trách nhiệm về chất lượng sản phẩm nếu Bên A không "
			"tuân thủ quy trình bảo quản theo hướng dẫn của Bên B.",
			"Party B shall not be liable for product quality if Party A fails to "
			"follow Party B's storage instructions.",
		)
		+ _gach(
			"Bên B cam kết bảo đảm vệ sinh an toàn thực phẩm đối với nguyên liệu "
			"và sản phẩm bánh do Bên B sản xuất, kinh doanh và chịu hoàn toàn "
			"trách nhiệm trước người tiêu dùng và cơ quan quản lý Nhà nước về "
			"những vi phạm vệ sinh an toàn thực phẩm theo quy định của pháp luật.",
			"Party B undertakes to ensure food safety and hygiene for the "
			"ingredients and pastry products it produces and trades, and bears "
			"full responsibility before consumers and State authorities for any "
			"food safety violations under the law.",
		)
		+ _gach(
			"Bảo đảm hàng hóa thuộc quyền sở hữu, kinh doanh hợp pháp của Bên B, "
			"không thuộc các trường hợp bị cấm lưu thông mua bán, không vi phạm "
			"pháp luật về quyền sở hữu tài sản và quyền sở hữu trí tuệ, không bị "
			"tranh chấp bởi bất kỳ bên thứ ba nào.",
			"Warrant that the goods are lawfully owned and traded by Party B, are "
			"not prohibited from circulation, do not infringe property or "
			"intellectual property rights, and are not subject to any third party "
			"dispute.",
		)
		+ _gach(
			"Bàn giao đầy đủ hàng hóa theo thời gian, địa điểm, số lượng, chất "
			"lượng đã cam kết.",
			"Deliver the goods in full according to the committed time, place, "
			"quantity and quality.",
		)
	)

	ra.append(dieu(6, "ĐIỀU KHOẢN CHUNG", "GENERAL PROVISIONS"))
	ra.append(
		_gach(
			"Hợp đồng này đã được hai Bên đọc kỹ, hiểu rõ và cam kết thực hiện "
			"nghiêm túc các điều khoản đã thỏa thuận.",
			"Both Parties have carefully read, fully understood and undertake to "
			"strictly perform the agreed terms of this Contract.",
		)
		+ _gach(
			"Các sửa đổi, bổ sung đối với Hợp đồng này phải được hai Bên thống "
			"nhất, lập thành văn bản và do đại diện có thẩm quyền của hai Bên ký kết.",
			"Any amendment or supplement to this Contract must be agreed by both "
			"Parties, made in writing and signed by their authorised representatives.",
		)
		+ _gach(
			"Hai Bên chủ động thông báo cho nhau tiến độ thực hiện Hợp đồng. Nếu "
			"có mâu thuẫn hoặc tranh chấp phát sinh, hai Bên phải thông báo kịp "
			"thời bằng văn bản và tích cực bàn bạc giải quyết trên tinh thần hợp "
			"tác. Trường hợp không tự giải quyết được trong thời hạn 30 (ba mươi) "
			"ngày kể từ thời điểm một Bên gửi thông báo bằng văn bản đầu tiên, hai "
			"Bên sẽ đưa vụ việc đến Tòa án có thẩm quyền tại Thành phố Hồ Chí Minh "
			"để giải quyết. Quyết định của Tòa án là quyết định cuối cùng và bắt "
			"buộc đối với hai Bên. Các chi phí liên quan do Bên thua kiện chịu.",
			"The Parties shall keep each other informed of the progress of this "
			"Contract. Any dispute shall be promptly notified in writing and "
			"settled through cooperative negotiation. If not resolved within 30 "
			"(thirty) days from the first written notice, the dispute shall be "
			"referred to the competent Court in Ho Chi Minh City. The Court's "
			"decision shall be final and binding on both Parties, and all related "
			"costs shall be borne by the losing Party.",
		)
		+ _gach(
			"Hợp đồng này có hiệu lực kể từ ngày ký, được lập thành 02 (hai) bản "
			"có giá trị pháp lý như nhau, mỗi Bên giữ 01 (một) bản. Hợp đồng tự "
			"động thanh lý khi hai Bên hoàn thành quyền và nghĩa vụ của mình.",
			"This Contract takes effect from the signing date and is made in 02 "
			"(two) counterparts of equal legal validity, each Party keeping 01 "
			"(one). The Contract is automatically liquidated when both Parties "
			"have fulfilled their rights and obligations.",
		)
	)

	ra.append(
		'<div style="text-align:right;margin-top:16px">'
		'<div style="font-style:italic">Thành phố Hồ Chí Minh, %s</div>'
		'<div style="font-style:italic;color:#555">Ho Chi Minh City, %s</div></div>'
		% (_ngay_vn(d.get("ngay_ky") or nowdate()), _ngay_en(d.get("ngay_ky") or nowdate()))
	)

	# Khoi o ky. Anh Viet 18/08/2026: "tuyet doi khong duoc ghi Ms./Mr. va
	# khong duoc lay mac dinh ten cua ban Sales" - nguoi ky thuong la Giam
	# doc. Ten lay tu o rieng do nguoi lap dien, va da duoc loc bo Ms./Mr.
	ky_a = _bo_xung_ho(d.get("nguoi_ky_a"))
	ky_b = _bo_xung_ho(d.get("nguoi_ky_b"))
	cv_a = (d.get("chuc_vu_ky_a") or "").strip()
	cv_b = (d.get("chuc_vu_ky_b") or "").strip()

	def o_ky(nhan_vi, nhan_en, ten, chuc):
		return (
			'<td style="width:50%%;text-align:center;vertical-align:top">'
			"<b>%s</b>"
			'<div style="font-style:italic;color:#555;font-size:11px">%s</div>'
			'<div style="font-size:11px"><i>(Ký, ghi rõ họ tên và đóng dấu)</i></div>'
			'<div style="font-style:italic;color:#555;font-size:10.5px">'
			"(Signature, full name and seal)</div>"
			'<div style="height:78px"></div>'
			'<div style="font-weight:bold">%s</div>'
			'<div style="font-size:11px">%s</div></td>'
			% (nhan_vi, nhan_en, _esc(ten) or "...........", _esc(chuc))
		)

	ra.append(
		'<table style="width:100%%;margin-top:6px;font-size:12px;page-break-inside:avoid">'
		"<tr>%s%s</tr></table>"
		% (
			o_ky("ĐẠI DIỆN BÊN A", "FOR AND ON BEHALF OF PARTY A", ky_a, cv_a),
			o_ky("ĐẠI DIỆN BÊN B", "FOR AND ON BEHALF OF PARTY B", ky_b, cv_b),
		)
	)
	return (
		'<div style="font-family:%s;font-size:12.5px;line-height:1.55;color:#000">'
		% FONT_TO
	) + "".join(ra) + "</div>"


def _so_chu(n):
	"""Doc mot so nho bang chu, dung cho "trong vong 03 (ba) ngay". THUAN."""
	bang = {
		1: "một", 2: "hai", 3: "ba", 4: "bốn", 5: "năm", 6: "sáu", 7: "bảy",
		8: "tám", 9: "chín", 10: "mười", 14: "mười bốn", 15: "mười lăm",
		20: "hai mươi", 30: "ba mươi",
	}
	n = cint(n)
	if n in bang:
		return bang[n]
	return _chu_so_tien(n).replace(" đồng", "").lower()


@frappe.whitelist()
def xem_truoc(name):
	"""HTML to hop dong, de xem tren app truoc khi xuat PDF."""
	_quyen()
	return _html(name)


@frappe.whitelist()
def _anh_data(url):
	"""Doc mot tep dinh kem thanh chuoi data: de nhung thang vao HTML.

	wkhtmltopdf khong tai duoc anh qua duong dan noi bo cua site (no chay o
	tien trinh khac, khong co phien dang nhap), nen phai nhung san.
	Tra ve rong neu doc khong duoc - luc do to van xuat, chi thieu anh.
	"""
	import mimetypes
	import os

	try:
		duong = (url or "").split("?")[0]
		if not duong:
			return "", ""
		if duong.startswith("/private/files/"):
			that = frappe.get_site_path("private", "files", os.path.basename(duong))
		elif duong.startswith("/files/"):
			that = frappe.get_site_path("public", "files", os.path.basename(duong))
		else:
			return "", ""
		kieu = mimetypes.guess_type(that)[0] or ""
		with open(that, "rb") as f:
			noi = f.read()
		return kieu, base64.b64encode(noi).decode()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hop_dong_pdf: doc tep phu luc")
		return "", ""


def _khoi_phu_luc(name, so_hd):
	"""Trang Phu luc 01. Uu tien BAN DA KY do Sales tai len.

	Anh Viet 18/08/2026: "Bao gia dinh kem lam phu luc phai la ban da duoc
	khach hang xac nhan."

	Nen thu tu uu tien la:
	  1. ban scan da co chu ky va moc hai ben, neu Sales da tai len
	  2. ban bao gia he tu dung, neu chua co ban scan

	Truong hop 2 khong bi bo di: no van dung khi hai ben moi chi thong nhat
	qua email va chua ky giay. Nhung to nao dung ban tu dung thi phai NOI RO
	tren trang phu luc, de nguoi doc biet day chua phai ban co chu ky.
	"""
	tep = frappe.db.get_value(DT, name, "phu_luc_scan")
	bg = frappe.db.get_value(DT, name, "bao_gia")
	dau = (
		'<div style="page-break-before:always"></div>'
		'<div style="font-family:%s;text-align:center;font-weight:bold;'
		'font-size:15px;margin:0 0 2px">PHỤ LỤC 01</div>'
		'<div style="font-family:%s;text-align:center;font-style:italic;'
		'color:#555;font-size:12px;margin:0 0 10px">APPENDIX 01</div>' % (FONT_TO, FONT_TO)
	)

	if tep:
		kieu, b64 = _anh_data(tep)
		ghi = (
			'<div style="font-family:%s;text-align:center;font-size:11.5px;margin:0 0 12px">'
			"Bản báo giá đã được hai Bên xác nhận, là bộ phận không tách rời của "
			"Hợp đồng số %s"
			'<div style="font-style:italic;color:#555">The quotation confirmed by '
			"both Parties, forming an integral part of Contract No. %s</div></div>"
			% (FONT_TO, _esc(so_hd), _esc(so_hd))
		)
		if b64 and kieu.startswith("image/"):
			return dau + ghi + (
				'<div style="text-align:center"><img src="data:%s;base64,%s" '
				'style="max-width:100%%;max-height:250mm"></div>' % (kieu, b64)
			)
		# Tep PDF hoac tep khong doc duoc: khong nhung vao duoc, nhung van
		# phai noi ro cho nguoi doc biet ban da ky nam o dau.
		return dau + ghi + (
			'<div style="font-family:%s;text-align:center;font-size:12px;'
			'border:1px dashed #888;padding:22px;margin-top:10px">'
			"Bản báo giá đã ký được lưu kèm hồ sơ hợp đồng %s trên hệ thống."
			'<div style="font-style:italic;color:#555">The signed quotation is '
			"stored with contract record %s in the system.</div></div>"
			% (FONT_TO, _esc(name), _esc(name))
		)

	if bg and frappe.db.exists(DT_BG, bg):
		from vagabond import bao_gia as mod_bg

		return dau + (
			'<div style="font-family:%s;text-align:center;font-size:11.5px;margin:0 0 4px">'
			"Báo giá số %s, là bộ phận không tách rời của Hợp đồng số %s"
			'<div style="font-style:italic;color:#555">Quotation No. %s, forming an '
			"integral part of Contract No. %s</div></div>"
			'<div style="font-family:%s;text-align:center;font-size:11px;color:#b3261e;'
			'margin:0 0 12px">Bản hệ thống dựng, CHƯA có chữ ký hai bên.</div>'
			% (FONT_TO, _esc(bg), _esc(so_hd), _esc(bg), _esc(so_hd), FONT_TO)
		) + mod_bg._html(bg)
	return ""


@frappe.whitelist()
def xuat_pdf(name, kem_phu_luc=1):
	"""To hop dong PDF, tu dinh kem bao gia lam Phu luc 01.

	Gop bang cach noi HAI khoi HTML trong cung mot lan dung PDF, ngan bang
	mot ngat trang cung. Khong gop hai tep PDF roi lai voi nhau: lam vay
	phai them thu vien, ma canh le va phong chu cua hai to se lech nhau.
	"""
	_quyen()
	from frappe.utils.pdf import get_pdf
	from vagabond.phong_chu import bao_dam_phong

	# Chep bo phong sang thu muc nguoi dung neu container nay chua co. Lan
	# thu hai tro di chi ton mot phep kiem thu muc.
	bao_dam_phong()

	so_hd = frappe.db.get_value(DT, name, "so_hop_dong") or name
	than = _html(name)
	if cint(kem_phu_luc):
		than += _khoi_phu_luc(name, so_hd)

	# Font Arial dat o CAP KHUNG, khong chi trong tung khoi (anh Viet
	# 18/08/2026: "toan bo hop dong va phu luc bat buoc su dung font Arial").
	# Chu "PHU LUC 01" truoc do bi vo font vi khoi do dung Times New Roman
	# ma ban PDF khong co bo chu do day du cho tieng Viet.
	khung = (
		"<html><head><meta charset='utf-8'>"
		"<style>@page{margin:14mm 12mm}%s"
		"body{margin:0}p{margin:5px 0}"
		"table{page-break-inside:auto}tr{page-break-inside:avoid}</style>"
		"</head><body>" % khung_style()
	) + than + "</body></html>"
	noi_dung = get_pdf(khung, options={"page-size": "A4", "orientation": "Portrait"})
	return {
		"ten_file": "Hop-dong-%s.pdf" % str(so_hd).replace("/", "-"),
		"b64": base64.b64encode(noi_dung).decode(),
		"kieu": "application/pdf",
	}


# ------------------------------------------------------------------- email

@frappe.whitelist()
def xem_nguoi_nhan(name, email=None):
	"""Ai se nhan thu nay. Cho bang xac nhan TRUOC khi bam gui.

	Dung DUNG phep loc cua gui_email, khong chep lai - neu khong thi bang
	xac nhan noi mot dang ma thu gui mot neo.
	"""
	_quyen()
	from vagabond.bao_gia import _cd, _tach_email

	cd = _cd()
	nhan, sai = _tach_email(email or frappe.db.get_value(DT, name, "email") or "")
	cc, _ = _tach_email(", ".join(cd["cc_noi_bo"]))
	da_co = {x.lower() for x in nhan}
	toi_la = (frappe.session.user or "").strip().lower()
	cc = [x for x in cc if x.lower() not in da_co and x.lower() != toi_la]
	tu = (cd.get("email_gui") or "").strip()
	co_that = bool(tu and frappe.db.exists("Email Account", {"email_id": tu, "enable_outgoing": 1}))
	return {
		"nhan": nhan, "sai": sai, "cc": cc,
		"tu": tu if co_that else "", "tu_khai": tu, "tu_co_that": 1 if co_that else 0,
	}


@frappe.whitelist()
def gui_email(name, email=None, loi_nhan=None):
	"""Gui to hop dong PDF (da gom phu luc bao gia) sang email khach."""
	_quyen(sua=True)
	from vagabond.bao_gia import _cd, _tach_email

	d = frappe.get_doc(DT, name)
	cd = _cd()
	b = _ben_b()

	# Kiem o MAY CHU chu khong tin app (QT-19). Gui nham mot to hop dong
	# sang dia chi khac la loai loi khong rut lai duoc.
	nhan, sai = _tach_email(email or d.get("email") or "")
	if sai:
		frappe.throw(
			"Địa chỉ này chưa đúng dạng email: %s. Anh chị sửa lại rồi gửi giúp em. "
			"Nhiều email thì ngăn nhau bằng dấu phẩy." % ", ".join(sai)
		)
	if not nhan:
		frappe.throw(
			"Chưa có email bên A để gửi hợp đồng. Anh chị mở hợp đồng, điền ô "
			"Email nhận hợp đồng rồi gửi lại nhé."
		)
	cc, _ = _tach_email(", ".join(cd["cc_noi_bo"]))
	da_co = {x.lower() for x in nhan}
	toi_la = (frappe.session.user or "").strip().lower()
	cc = [x for x in cc if x.lower() not in da_co and x.lower() != toi_la]

	tep = xuat_pdf(name)
	so = d.get("so_hop_dong") or name
	than = (
		'<div style="font-family:Arial,Liberation Sans,Helvetica,sans-serif;font-size:14px;'
		'line-height:1.6;color:#1c1a17">'
		"<p>Kính gửi Quý khách %s,</p>"
		"<p>The Vagabond Pâtisserie trân trọng gửi Quý khách <b>Hợp đồng mua bán hàng hóa "
		"số %s</b> theo nội dung hai bên đã thống nhất. Bản báo giá đã chốt được đính kèm "
		"trong cùng tệp PDF làm Phụ lục 01.</p>"
		"<p>Tổng giá trị Hợp đồng là <b>%s đ</b> (Bằng chữ: %s).</p>%s"
		"<p>Quý khách vui lòng kiểm tra lại thông tin doanh nghiệp, người đại diện và các "
		"điều khoản. Nếu cần điều chỉnh, xin phản hồi lại email này trước khi ký.</p>"
		"<p>Trân trọng,<br><b>%s</b><br>%s<br>The Vagabond Pâtisserie<br>%s</p></div>"
	) % (
		_esc(d.get("ten_khach") or ""),
		_esc(so),
		_tien_vn(d.get("gia_tri")),
		_chu_so_tien(d.get("gia_tri")),
		("<p>%s</p>" % _br(loi_nhan)) if (loi_nhan or "").strip() else "",
		_esc(b.get("dai_dien") or ""),
		_esc(b.get("chuc_vu") or ""),
		_esc(b.get("dien_thoai") or ""),
	)
	gui = {
		"recipients": nhan,
		"cc": cc or None,
		"subject": "Hợp đồng mua bán hàng hóa số %s - The Vagabond Pâtisserie" % so,
		"message": than,
		"attachments": [{"fname": tep["ten_file"], "fcontent": base64.b64decode(tep["b64"])}],
		"reference_doctype": DT,
		"reference_name": name,
		"now": True,
	}
	tu = (cd.get("email_gui") or "").strip()
	if tu and frappe.db.exists("Email Account", {"email_id": tu, "enable_outgoing": 1}):
		gui["sender"] = tu
	elif tu:
		frappe.log_error(
			"Chua co Email Account bat gui di cho %s, dung hop thu mac dinh." % tu,
			"hop_dong_pdf: gui email",
		)
	frappe.sendmail(**gui)
	if d.get("trang_thai") in (None, "", "Nháp", "Mới"):
		try:
			frappe.db.set_value(DT, name, "trang_thai", "Đã gửi khách")
		except Exception:
			pass
	frappe.db.commit()
	return {"ok": 1, "nhan": nhan, "cc": cc, "ten_file": tep["ten_file"]}
