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


def viet_tat_khach(ten):
	"""Cum viet tat cua ten cong ty, dung trong so hop dong. THUAN.

	"CONG TY TNHH M.O.I COSMETICS" -> "MOI"
	"CONG TY TNHH PATISSERIE VAGABOND" -> "PV"

	Cach lam: bo cac tu chi loai hinh doanh nghiep (cong ty nao cung co nen
	khong phan biet duoc ai voi ai), roi nhin phan ten rieng con lai. Neu tu
	dau tien cua no da ngan san - tuc no von la mot cum viet tat nhu MOI,
	PYR, KFC - thi lay nguyen tu do; con neu la mot tu dai thi lay chu cai
	dau cua cac tu.

	So sanh phai BO DAU truoc: "CO PHAN" va "CỔ PHẦN" la mot, va neu khong
	bo dau thi "CONG TY CỔ PHẦN PYRAMID" ra "CP" - lay dung hai chu cua cai
	phan dang le phai bo di.

	Day chi la GOI Y. Nguoi lap sua tay duoc truoc khi ky, nen tha doan hoi
	tho con hon bat ho go tay tu dau.
	"""
	bo = {
		"CONG", "TY", "TNHH", "CO", "PHAN", "CP", "MTV", "MOT", "THANH",
		"VIEN", "DOANH", "NGHIEP", "TU", "NHAN", "HO", "KINH", "SO",
		"CHI", "NHANH", "VN", "VIETNAM", "VIET", "NAM", "AND", "VA",
	}
	tho = str(ten or "").replace(".", "").replace(",", " ").replace("-", " ")
	tu = [t for t in tho.split() if t]
	giu = [t for t in tu if _khong_dau(t).upper() not in bo]
	if not giu:
		giu = tu
	if not giu:
		return ""
	dau = "".join(c for c in _khong_dau(giu[0]).upper() if c.isalnum())
	if len(giu) == 1 or (dau and len(dau) <= 5):
		ra = dau
	else:
		ra = "".join(_khong_dau(t)[0] for t in giu if _khong_dau(t))
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


def _esc(s):
	return (
		str(s or "")
		.replace("&", "&amp;")
		.replace("<", "&lt;")
		.replace(">", "&gt;")
	)


def _br(s):
	return _esc(s).replace("\n", "<br>")


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
	return {
		"ten": c.get("ten_ban") or "CÔNG TY TNHH PATISSERIE VAGABOND",
		"mst": c.get("mst_ban") or "",
		"dia_chi": c.get("dia_chi_ban") or "",
		"dai_dien": c.get("dai_dien_ban") or "",
		"chuc_vu": c.get("chuc_vu_ban") or "Giám đốc",
		"dien_thoai": c.get("dt_ban") or "",
		"email": c.get("email_ban") or "",
		"ngan_hang": c.get("ngan_hang_vi") or "",
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
			}
			for r in (bg.dong or [])
		]
		d["bg_thue_pt"] = flt(bg.thue_pt)
		d["bg_gia_da_gom_vat"] = cint(bg.gia_da_gom_vat)
		d["bg_giao_hang"] = bg.giao_hang or ""
	return d


# ------------------------------------------------------------------ to PDF

def _bang_hang(d):
	"""Bang Dieu 1. Lay tung dong tu bao gia nguon neu con, khong thi mot dong gop."""
	dong = d.get("dong_bao_gia") or []
	vat = ""
	if d.get("bg_gia_da_gom_vat") or flt(d.get("bg_thue_pt")):
		vat = "<br>(đã gồm VAT %s%%)" % (_tien_vn(d.get("bg_thue_pt")) if flt(d.get("bg_thue_pt")) else "8")
	th = (
		'<tr style="background:#f2f2f2">'
		'<th style="border:1px solid #000;padding:5px 6px;width:34px">STT</th>'
		'<th style="border:1px solid #000;padding:5px 6px;text-align:left">Tên hàng</th>'
		'<th style="border:1px solid #000;padding:5px 6px;width:52px">ĐVT</th>'
		'<th style="border:1px solid #000;padding:5px 6px;width:62px">Số lượng</th>'
		'<th style="border:1px solid #000;padding:5px 6px;width:100px">Đơn giá%s</th>'
		'<th style="border:1px solid #000;padding:5px 6px;width:110px">Thành tiền%s</th></tr>' % (vat, vat)
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
		'font-weight:bold">TỔNG TIỀN%s</td>'
		'<td style="border:1px solid #000;padding:5px 6px;text-align:right;font-weight:bold">%s</td></tr>'
		% (vat.replace("<br>", " "), _tien_vn(d.get("gia_tri")))
	)
	return (
		'<table style="width:100%;border-collapse:collapse;font-size:11.5px;margin:8px 0">'
		+ th + "".join(hang) + tong + "</table>"
	)


def _o_ben(nhan, b):
	"""Khoi thong tin mot ben, dung khuon bang hai cot cua mau anh Viet gui."""
	dong = [
		("Tên công ty", b.get("ten")),
		("Địa chỉ", b.get("dia_chi")),
		("Mã số thuế", b.get("mst")),
		("Đại diện", b.get("dai_dien")),
		("Chức vụ", b.get("chuc_vu")),
	]
	if b.get("dien_thoai"):
		dong.append(("Điện thoại", b.get("dien_thoai")))
	if b.get("email"):
		dong.append(("Email", b.get("email")))
	if b.get("ngan_hang"):
		dong.append(("Tài khoản", b.get("ngan_hang")))
	than = "".join(
		'<tr><td style="padding:2px 0;width:110px;vertical-align:top">%s</td>'
		'<td style="padding:2px 0;vertical-align:top">: %s</td></tr>' % (_esc(k), _br(v or "..........."))
		for k, v in dong
	)
	return (
		'<div style="font-weight:bold;margin:11px 0 3px">%s</div>'
		'<table style="width:100%%;font-size:12px;border-collapse:collapse">%s</table>' % (_esc(nhan), than)
	)


def cau_dieu_2(tong, pt1, n1=3, n2=3):
	"""Cau chu cua Dieu 2, chia hai dot hoac tra mot lan. THUAN.

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
	if pt1 <= 0 or pt1 >= 100:
		return (
			"<p style='margin:4px 0 4px 14px'>Bên A thanh toán 100%% giá trị Hợp đồng, "
			"tương đương số tiền <b>%s VNĐ</b> (Bằng chữ: %s), chậm nhất trước %02d "
			"(%s) ngày bàn giao hàng hóa theo lịch giao hàng đã được hai Bên thống nhất.</p>"
			% (_tien_vn(tong), _chu_so_tien(tong), n2, _so_chu(n2))
		)
	return (
		"<p style='margin:4px 0 4px 14px'>Đợt 01: Bên A thanh toán %s%% giá trị Hợp đồng, "
		"tương đương số tiền <b>%s VNĐ</b> (Bằng chữ: %s), trong vòng %02d (%s) ngày kể "
		"từ ngày Hợp đồng được hai Bên ký kết.</p>"
		"<p style='margin:4px 0 4px 14px'>Đợt 02: Bên A thanh toán %s%% giá trị Hợp đồng "
		"còn lại, tương đương số tiền <b>%s VNĐ</b> (Bằng chữ: %s), chậm nhất trước %02d "
		"(%s) ngày bàn giao hàng hóa theo lịch giao hàng đã được hai Bên thống nhất.</p>"
		% (
			_tien_vn(pt1), _tien_vn(dot1), _chu_so_tien(dot1), n1, _so_chu(n1),
			_tien_vn(100.0 - pt1), _tien_vn(dot2), _chu_so_tien(dot2), n2, _so_chu(n2),
		)
	)


def _html(name):
	"""To hop dong mua ban hang hoa, cau truc hanh chinh Viet Nam."""
	d = chi_tiet(name)
	b = d["ben_b"]
	a = {
		"ten": d.get("ten_khach"),
		"mst": d.get("ma_so_thue"),
		"dia_chi": d.get("dia_chi"),
		"dai_dien": d.get("dai_dien"),
		"chuc_vu": d.get("chuc_vu"),
		"dien_thoai": d.get("dien_thoai"),
		"email": d.get("email"),
	}
	so = d.get("so_hop_dong") or d["so_goi_y"]
	pt1 = flt(d.get("dat_coc_pt"))
	n1 = cint(d.get("ngay_dot1")) or 3
	n2 = cint(d.get("ngay_dot2")) or 3

	dieu2_dot = cau_dieu_2(d.get("gia_tri"), pt1, n1, n2)

	def dieu(so_dieu, tua):
		return (
			'<div style="font-weight:bold;margin:13px 0 4px;text-transform:uppercase">'
			"ĐIỀU %d: %s</div>" % (so_dieu, _esc(tua))
		)

	ra = []
	ra.append(
		'<div style="text-align:center;line-height:1.5">'
		'<div style="font-weight:bold;font-size:13px">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</div>'
		'<div style="font-weight:bold;font-size:12.5px;text-decoration:underline">'
		"Độc lập – Tự do – Hạnh phúc</div></div>"
	)
	ra.append(
		'<div style="text-align:center;margin:18px 0 4px">'
		'<div style="font-weight:bold;font-size:16px">HỢP ĐỒNG MUA BÁN HÀNG HÓA</div>'
		'<div style="font-size:12px;margin-top:3px">Số: %s</div></div>' % _esc(so)
	)
	ra.append(
		'<div style="margin-top:12px;font-size:12px;line-height:1.65">'
		"<b>Căn cứ:</b><br>"
		"–&nbsp;&nbsp;Bộ luật Dân sự số 91/2015/QH13 ngày 24/11/2015 của Quốc hội nước "
		"Cộng hòa Xã hội Chủ nghĩa Việt Nam;<br>"
		"–&nbsp;&nbsp;Luật Thương mại số 36/2005/QH11 ngày 14/06/2005 của Quốc hội nước "
		"Cộng hòa Xã hội Chủ nghĩa Việt Nam;<br>"
		"–&nbsp;&nbsp;Căn cứ nhu cầu và khả năng của hai Bên.</div>"
	)
	ra.append(
		'<p style="margin:12px 0 0">Hôm nay, %s, tại Thành phố Hồ Chí Minh, chúng tôi gồm:</p>'
		% _ngay_vn(d.get("ngay_ky") or nowdate())
	)
	ra.append(_o_ben("BÊN MUA (gọi tắt là Bên A)", a))
	ra.append(_o_ben("BÊN BÁN (gọi tắt là Bên B)", b))
	ra.append(
		"<p>Sau khi thỏa thuận, hai Bên thống nhất ký Hợp đồng mua bán hàng hóa với "
		"những nội dung dưới đây:</p>"
	)

	ra.append(dieu(1, "HÀNG HÓA"))
	ra.append("<p>Bên B đồng ý bán và Bên A đồng ý mua số lượng hàng hóa như sau:</p>")
	ra.append(_bang_hang(d))
	ra.append("<p><i>(Bằng chữ: %s./.)</i></p>" % _chu_so_tien(d.get("gia_tri")))
	if d.get("bao_gia"):
		ra.append(
			'<p style="font-size:11.5px;color:#333">Chi tiết quy cách, hình ảnh và điều kiện '
			"vận hành xem tại <b>Phụ lục 01 - Báo giá số %s</b> đính kèm, là bộ phận không "
			"tách rời của Hợp đồng này.</p>" % _esc(d["bao_gia"])
		)

	ra.append(dieu(2, "THANH TOÁN"))
	ra.append(
		"<p>–&nbsp;&nbsp;Hình thức thanh toán: Chuyển khoản theo số tài khoản do Bên B "
		"cung cấp trong Hợp đồng này.</p><p>–&nbsp;&nbsp;Phương thức thanh toán:</p>"
	)
	ra.append(dieu2_dot)
	if b.get("ngan_hang"):
		ra.append(
			"<p>–&nbsp;&nbsp;Thông tin chuyển khoản:</p>"
			'<div style="margin-left:14px">%s</div>' % _br(b["ngan_hang"])
		)
	ra.append(
		"<p>–&nbsp;&nbsp;Chứng từ kèm theo: Hóa đơn giá trị gia tăng hợp lệ "
		"(cung cấp sau khi giao hàng).</p>"
	)

	ra.append(dieu(3, "QUY CÁCH, CHẤT LƯỢNG HÀNG HÓA"))
	ra.append(
		"<p>–&nbsp;&nbsp;Hàng hóa do Bên B cung cấp được sản xuất đúng quy cách, số lượng, "
		"tiêu chuẩn như mẫu đã được hai Bên duyệt.</p>"
		"<p>–&nbsp;&nbsp;Trong trường hợp hàng hóa do Bên B bàn giao bị hư hỏng hoặc thiếu, "
		"Bên B có trách nhiệm khắc phục trong thời gian sớm nhất.</p>"
		"<p>–&nbsp;&nbsp;Bên B không đổi lại hàng trong trường hợp sản phẩm hư hỏng do các "
		"điều kiện khách quan gây ra (tác động ngoại lực, rơi vỡ do lỗi của người sử dụng).</p>"
	)

	ra.append(dieu(4, "ĐỊA ĐIỂM, THỜI GIAN BÀN GIAO HÀNG HÓA"))
	tg = d.get("thoi_gian_giao") or d.get("bg_giao_hang") or ""
	ra.append(
		"<p>–&nbsp;&nbsp;Thời gian: %s</p>"
		"<p>–&nbsp;&nbsp;Địa điểm bàn giao hàng: %s</p>"
		% (_br(tg) or "theo lịch giao hàng hai Bên thống nhất bằng văn bản.",
		   _br(d.get("dia_diem_giao")) or "...........")
	)

	ra.append(dieu(5, "TRÁCH NHIỆM CỦA HAI BÊN"))
	ra.append(
		"<p><b>5.1. Trách nhiệm của Bên A:</b></p>"
		"<p>–&nbsp;&nbsp;Thanh toán cho Bên B theo quy định tại Điều 2 của Hợp đồng này.</p>"
		"<p>–&nbsp;&nbsp;Hỗ trợ, tạo điều kiện thuận lợi, chuẩn bị mặt bằng và các điều kiện "
		"làm việc sẵn sàng cho Bên B trong thời gian giao hàng.</p>"
		"<p>–&nbsp;&nbsp;Trong trường hợp Bên A đơn phương hủy Hợp đồng mà không được sự "
		"chấp thuận của Bên B, Bên A sẽ không được hoàn lại khoản tiền đã thanh toán cho Bên B.</p>"
		"<p>–&nbsp;&nbsp;Kiểm tra chi tiết quy cách, số lượng, tiêu chuẩn hàng hóa và ký nhận "
		"biên bản giao nhận tại thời điểm Bên B giao hàng.</p>"
		"<p><b>5.2. Trách nhiệm của Bên B:</b></p>"
		"<p>–&nbsp;&nbsp;Giao hàng đúng quy cách, thời gian, số lượng, tiêu chuẩn như đã cam "
		"kết và quy định tại Điều 1.</p>"
		"<p>–&nbsp;&nbsp;Cung cấp đầy đủ các chứng từ kèm theo tại Điều 2.</p>"
		"<p>–&nbsp;&nbsp;Nhanh chóng giải quyết khiếu nại của khách hàng liên quan đến hàng hóa "
		"do Bên B cung cấp.</p>"
		"<p>–&nbsp;&nbsp;Chịu trách nhiệm trước pháp luật về nguồn gốc, phẩm chất, tính pháp lý "
		"của hàng hóa do Bên B cung cấp.</p>"
		"<p>–&nbsp;&nbsp;Trong trường hợp xảy ra sự cố ngộ độc thực phẩm, Bên B phải bồi thường "
		"nếu có thiệt hại xảy ra cho Bên A; trường hợp này phải có sự điều tra và chứng minh do "
		"lỗi của nhà sản xuất.</p>"
		"<p>–&nbsp;&nbsp;Bên B không chịu trách nhiệm về chất lượng sản phẩm nếu Bên A không "
		"tuân thủ quy trình bảo quản theo hướng dẫn của Bên B.</p>"
		"<p>–&nbsp;&nbsp;Bên B cam kết bảo đảm vệ sinh an toàn thực phẩm đối với nguyên liệu và "
		"sản phẩm bánh do Bên B sản xuất, kinh doanh và chịu hoàn toàn trách nhiệm trước người "
		"tiêu dùng và cơ quan quản lý Nhà nước về những vi phạm vệ sinh an toàn thực phẩm theo "
		"quy định của pháp luật.</p>"
		"<p>–&nbsp;&nbsp;Bảo đảm hàng hóa thuộc quyền sở hữu, kinh doanh hợp pháp của Bên B, "
		"không thuộc các trường hợp bị cấm lưu thông mua bán, không vi phạm pháp luật về quyền "
		"sở hữu tài sản và quyền sở hữu trí tuệ, không bị tranh chấp bởi bất kỳ bên thứ ba nào.</p>"
		"<p>–&nbsp;&nbsp;Bàn giao đầy đủ hàng hóa theo thời gian, địa điểm, số lượng, chất lượng "
		"đã cam kết.</p>"
	)

	ra.append(dieu(6, "ĐIỀU KHOẢN CHUNG"))
	ra.append(
		"<p>–&nbsp;&nbsp;Hợp đồng này đã được hai Bên đọc kỹ, hiểu rõ và cam kết thực hiện "
		"nghiêm túc các điều khoản đã thỏa thuận.</p>"
		"<p>–&nbsp;&nbsp;Các sửa đổi, bổ sung đối với Hợp đồng này phải được hai Bên thống nhất, "
		"lập thành văn bản và do đại diện có thẩm quyền của hai Bên ký kết.</p>"
		"<p>–&nbsp;&nbsp;Hai Bên chủ động thông báo cho nhau tiến độ thực hiện Hợp đồng. Nếu có "
		"mâu thuẫn hoặc tranh chấp phát sinh, hai Bên phải thông báo kịp thời bằng văn bản và "
		"tích cực bàn bạc giải quyết trên tinh thần hợp tác. Trường hợp không tự giải quyết được "
		"trong thời hạn 30 (ba mươi) ngày kể từ thời điểm một Bên gửi thông báo bằng văn bản đầu "
		"tiên, hai Bên sẽ đưa vụ việc đến Tòa án có thẩm quyền tại Thành phố Hồ Chí Minh để giải "
		"quyết. Quyết định của Tòa án là quyết định cuối cùng và bắt buộc đối với hai Bên. Các "
		"chi phí liên quan do Bên thua kiện chịu.</p>"
		"<p>–&nbsp;&nbsp;Hợp đồng này có hiệu lực kể từ ngày ký, được lập thành 02 (hai) bản có "
		"giá trị pháp lý như nhau, mỗi Bên giữ 01 (một) bản. Hợp đồng tự động thanh lý khi hai "
		"Bên hoàn thành quyền và nghĩa vụ của mình.</p>"
	)

	ra.append(
		'<p style="text-align:right;font-style:italic;margin-top:16px">'
		"Thành phố Hồ Chí Minh, %s</p>" % _ngay_vn(d.get("ngay_ky") or nowdate())
	)
	ra.append(
		'<table style="width:100%;margin-top:6px;font-size:12px;page-break-inside:avoid">'
		'<tr><td style="width:50%;text-align:center;vertical-align:top">'
		"<b>ĐẠI DIỆN BÊN A</b><br><i>(Ký, ghi rõ họ tên và đóng dấu)</i>"
		'<div style="height:78px"></div>%s</td>'
		'<td style="width:50%%;text-align:center;vertical-align:top">'
		"<b>ĐẠI DIỆN BÊN B</b><br><i>(Ký, ghi rõ họ tên và đóng dấu)</i>"
		'<div style="height:78px"></div>%s</td></tr></table>'
		% (_esc(d.get("dai_dien") or ""), _esc(b.get("dai_dien") or ""))
	)
	return (
		'<div style="font-family:\'Times New Roman\',Times,serif;font-size:12.5px;'
		'line-height:1.6;color:#000">' + "".join(ra) + "</div>"
	)


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
def xuat_pdf(name, kem_phu_luc=1):
	"""To hop dong PDF, tu dinh kem bao gia da chot lam Phu luc 01.

	Anh Viet 18/08/2026: "File PDF xuat ra phai bao gom phan Hop dong chinh
	(phap ly) va tu dong dinh kem Bao gia da chot o trang cuoi lam Phu luc."

	Gop bang cach noi HAI khoi HTML trong cung mot lan dung PDF, ngan bang
	mot ngat trang cung. Khong gop hai tep PDF roi lai voi nhau: lam vay
	phai them thu vien, ma canh le va phong chu cua hai to se lech nhau.
	"""
	_quyen()
	from frappe.utils.pdf import get_pdf

	than = _html(name)
	if cint(kem_phu_luc):
		bg = frappe.db.get_value(DT, name, "bao_gia")
		if bg and frappe.db.exists(DT_BG, bg):
			from vagabond import bao_gia as mod_bg

			than += (
				'<div style="page-break-before:always"></div>'
				'<div style="font-family:\'Times New Roman\',Times,serif;text-align:center;'
				'font-weight:bold;font-size:14px;margin:0 0 10px">PHỤ LỤC 01</div>'
				'<div style="font-family:\'Times New Roman\',Times,serif;text-align:center;'
				'font-size:11.5px;margin:0 0 14px">Báo giá số %s, là bộ phận không tách rời '
				"của Hợp đồng số %s</div>" % (_esc(bg), _esc(frappe.db.get_value(DT, name, "so_hop_dong") or name))
			) + mod_bg._html(bg)

	khung = (
		"<html><head><meta charset='utf-8'>"
		"<style>@page{margin:14mm 12mm}body{margin:0}"
		"p{margin:5px 0}table{page-break-inside:auto}tr{page-break-inside:avoid}</style>"
		"</head><body>" + than + "</body></html>"
	)
	noi_dung = get_pdf(khung, options={"page-size": "A4", "orientation": "Portrait"})
	so = (frappe.db.get_value(DT, name, "so_hop_dong") or name).replace("/", "-")
	return {
		"ten_file": "Hop-dong-%s.pdf" % so,
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
		'<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;'
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
