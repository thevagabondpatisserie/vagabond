# -*- coding: utf-8 -*-
"""Khuôn thư điện tử theo bộ nhận diện Vagabond, dùng chung cho MỌI thư máy gửi.

Vì sao có tệp này (03/09/2026)
------------------------------
Rà lại toàn bộ thư máy gửi ra thì thấy 17 chỗ gọi gửi thư, dựng theo BỐN
kiểu khác nhau: có thư bọc khung robin egg (thư mời nhân viên, thư báo nhà
cung cấp), có thư tự vẽ một cái khung riêng màu khác (thư đã nhận tiền),
có thư chỉ là vài thẻ p trơn không logo không chân thư (báo giá, hợp đồng,
mã ưu đãi, xuất hoá đơn), và có thư nội bộ là một khối pre chữ đen. Cùng
một tiệm mà khách nhận ba lá thư trông như ba công ty.

Nặng hơn: thư báo thanh toán cho nhà cung cấp đang HỎNG từ bản v369 vì một
biến phông được tham chiếu ngoài phạm vi khai báo. Đây đúng là hậu quả của
việc mỗi tệp tự dựng thư: sửa xâu phông một chỗ thì chỗ khác vỡ.

Nay mọi thư gọi vào đây. Đổi màu, đổi logo, đổi chân thư thì đổi MỘT chỗ.

Bộ nhận diện (cùng nguồn với mẫu in, xem vagabond/mau_in/thuong_hieu.py)
-------------------------------------------------------------------------
  #4FDCF2  robin egg, màu chủ đạo: dải đầu thư, nút, gạch nhấn
  #1A1A1A  mực, chữ thân thư
  #FAF7F2  kem, nền ngoài và các ô nhấn
  #8C857B  xám ấm, chữ phụ
  #D9D2C7  kẻ mảnh
  #05323C  chữ đặt TRÊN nền robin egg (robin egg sáng, chữ trắng không đọc được)

Phông: Arial. Thư hiện trên máy NGƯỜI NHẬN; Vagabond Sans và Qualy không
nhúng được vào thư (Gmail bỏ @font-face), nhét tên phông lạ vào là mỗi hộp
thư tự chọn một kiểu. Tiêu đề viết HOA có giãn chữ để giữ tinh thần
Vagabond Sans bằng phông thường.

Ba luật kỹ thuật của thư điện tử, rút từ các bản trước
-------------------------------------------------------
1. Bố cục bằng bảng 600px, CSS viết inline hết. Hộp thư không đọc thẻ style.
2. Nút dựng bằng bảng chứ không phải thẻ a có padding: nhiều hộp thư bỏ
   padding của thẻ a.
3. Mảng màu thương hiệu LÓT ẢNH nền kèm bgcolor dự phòng: Gmail chế độ tối
   tự đảo màu những mảng sáng thuần CSS, ảnh thì không bị đảo.

Ba loại chân thư, chọn theo NGƯỜI NHẬN chứ không theo loại chứng từ
--------------------------------------------------------------------
  khach      khách mua bánh: địa chỉ các quầy, hotline, web đặt bánh
  ncc        nhà cung cấp, đối tác: tên pháp nhân, mã số thuế, địa chỉ trụ sở
  nhan_vien  người trong công ty: chỗ hỏi khi app có vấn đề
  noi_bo     thư máy tự bắn cho kế toán, quản lý: nói rõ là thư tự động

Phần THUẦN của tệp không chạm Frappe nên kiểm thử và xem trước được trên
máy CI tay không. Chỉ `goc_anh()` và `_cac_quay()` hỏi hệ, và đều có
phương án lùi.
"""

from html import escape as _h

# Bo mau. Cung nguon voi mau in (thuong_hieu.py). Khai lai o day de tep nay
# import duoc ma khong keo theo frappe.
XANH = "#4FDCF2"
MUC = "#1A1A1A"
KEM = "#FAF7F2"
XAM = "#8C857B"
KE = "#D9D2C7"
XANH_DAM = "#05323C"
LIEN_KET = "#0B7C93"
CANH_BAO_NEN = "#FFF6E5"
CANH_BAO_CHU = "#8A4B00"

PHONG = "Arial,Helvetica,sans-serif"

TEN_TIEM = "The Vagabond Pâtisserie"
HOTLINE = "0931 224 334"
WEB = "thevagabondpatisserie.com"
WEB_DAT_BANH = "order.thevagabondpatisserie.com/banh"
HO_TRO_APP = "Cần hỗ trợ về app hãy nhắn anh Việt, 0901 486 556 (Zalo)."

# Anh dung trong thu, nam trong repo de theo phien ban. Duoc phuc vu o
# /assets/vagabond/images/thu/... tren site.
ANH_DAU = "dau.png"          # dai robin egg, logo trang, 1200x400 (hien 600x200)
ANH_LOT_XANH = "lot-xanh.png"  # o mau dac 24x24 de lat nen
ANH_LOT_KEM = "lot-kem.png"

CHAN_HOP_LE = ("khach", "ncc", "nhan_vien", "noi_bo")


# ------------------------------------------------------------- phần THUẦN

def tien(v):
	"""1234567 -> 1.234.567. THUẦN."""
	try:
		return "{:,.0f}".format(float(v or 0)).replace(",", ".")
	except Exception:
		return "0"


def h(s):
	"""Thoát HTML. Không dùng frappe.utils.escape_html để tệp này thuần."""
	return _h(str(s if s is not None else ""), quote=True)


def _chu(co=14, mau=MUC, dam=False, giong=1.65, them=""):
	return (
		"font-family:%s;font-size:%spx;line-height:%s;color:%s;%s%s"
		% (PHONG, co, giong, mau, "font-weight:bold;" if dam else "", them)
	)


def nhan_hoa(chu, mau=XAM):
	"""Nhãn viết HOA giãn chữ, kiểu tiêu đề của bộ nhận diện. THUẦN."""
	return (
		'<div style="%s">%s</div>'
		% (_chu(11, mau, True, 1.4, "letter-spacing:2px;text-transform:uppercase;"), h(chu))
	)


def doan(noi_dung, cach=14, mau=MUC, co=14):
	"""Một đoạn văn. `noi_dung` là HTML đã thoát sẵn ở chỗ gọi."""
	return '<p style="margin:0 0 %dpx;%s">%s</p>' % (cach, _chu(co, mau), noi_dung)


def o_kem(noi_dung, goc_anh=""):
	"""Ô kem có vạch robin egg bên trái, dùng cho khối thông tin cần nhìn ra ngay."""
	return (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%" '
		'style="margin:6px 0 14px"><tr>'
		'<td width="4" background="%s" bgcolor="%s" style="width:4px;font-size:0;line-height:0">&nbsp;</td>'
		'<td background="%s" bgcolor="%s" style="padding:13px 16px;%s">%s</td>'
		"</tr></table>"
	) % (
		_anh(goc_anh, ANH_LOT_XANH), XANH, _anh(goc_anh, ANH_LOT_KEM), KEM,
		_chu(13.5, MUC, False, 1.7), noi_dung,
	)


def o_canh_bao(noi_dung):
	"""Ô vàng nhạt cho lời dặn quan trọng (tiền, hạn chót)."""
	return (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%" '
		'style="margin:6px 0 14px"><tr>'
		'<td bgcolor="%s" style="padding:12px 16px;border:1px solid #F3D9A4;%s">%s</td>'
		"</tr></table>"
	) % (CANH_BAO_NEN, _chu(13.5, CANH_BAO_CHU, False, 1.65), noi_dung)


def cap(cac_cap):
	"""Danh sách nhãn - giá trị xếp hai cột. cac_cap: [(nhan, gia_tri_html)]."""
	dong = "".join(
		'<tr><td valign="top" style="padding:5px 14px 5px 0;white-space:nowrap;%s">%s</td>'
		'<td valign="top" style="padding:5px 0;%s">%s</td></tr>'
		% (_chu(13, XAM, False, 1.6), h(n), _chu(13.5, MUC, False, 1.6), g)
		for n, g in cac_cap
	)
	return (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
		'style="border-collapse:collapse;margin:0 0 14px">%s</table>' % dong
	)


def bang(cot, dong, tong=None, goc_anh=""):
	"""Bảng số liệu. cot: [(nhan, 'left'|'right')]; dong: [[html,...]];
	tong: (nhan, gia_tri_html) in đậm ở cuối. Đầu bảng nền kem, kẻ mảnh."""
	dau = "".join(
		'<td bgcolor="%s" style="padding:8px 10px;text-align:%s;%s">%s</td>'
		% (KEM, can, _chu(11, XAM, True, 1.4, "letter-spacing:1.5px;text-transform:uppercase;"), h(n))
		for n, can in cot
	)
	than = ""
	for r in dong:
		than += "<tr>" + "".join(
			'<td style="padding:8px 10px;border-bottom:1px solid %s;text-align:%s;%s">%s</td>'
			% (KE, cot[i][1] if i < len(cot) else "left", _chu(13.5, MUC, False, 1.5), o)
			for i, o in enumerate(r)
		) + "</tr>"
	chan = ""
	if tong:
		chan = (
			'<tr><td colspan="%d" style="padding:11px 10px 4px;text-align:right;%s">%s</td>'
			'<td style="padding:11px 10px 4px;text-align:right;white-space:nowrap;%s">%s</td></tr>'
			% (max(1, len(cot) - 1), _chu(12, XAM, True, 1.4, "letter-spacing:1.5px;text-transform:uppercase;"),
			   h(tong[0]), _chu(16, MUC, True, 1.4), tong[1])
		)
	return (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%" '
		'style="border-collapse:collapse;margin:6px 0 14px"><tr>%s</tr>%s%s</table>'
		% (dau, than, chan)
	)


def nut(dia_chi, chu, phu=False, goc_anh=""):
	"""Nút. Chính: nền robin egg chữ mực đậm. Phụ: nền trắng viền mực."""
	if phu:
		o = 'bgcolor="#FFFFFF" style="border:2px solid %s;border-radius:6px"' % MUC
		mau = MUC
	else:
		o = 'background="%s" bgcolor="%s" style="border-radius:6px"' % (_anh(goc_anh, ANH_LOT_XANH), XANH)
		mau = XANH_DAM
	return (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto">'
		'<tr><td align="center" %s>'
		'<a href="%s" target="_blank" style="display:inline-block;padding:13px 34px;'
		'%s;text-decoration:none">%s</a>'
		"</td></tr></table>"
	) % (o, h(dia_chi), _chu(15, mau, True, 1.3, "letter-spacing:.3px;"), h(chu))


def chu_ky(ten, chuc_vu="", lien_he=""):
	"""Khối chữ ký người gửi thật (báo giá, hợp đồng). Không ký tên tiệm ở đây,
	tên tiệm nằm ở chân thư rồi."""
	dong = ['<b style="color:%s">%s</b>' % (MUC, h(ten))]
	if chuc_vu:
		dong.append(h(chuc_vu))
	if lien_he:
		dong.append(h(lien_he))
	return '<p style="margin:18px 0 0;%s">Trân trọng,<br>%s</p>' % (_chu(14, MUC), "<br>".join(dong))


def _anh(goc, ten):
	return (goc or "") + "/assets/vagabond/images/thu/" + ten


def _chan(loai, goc_anh, cac_quay):
	"""Chân thư theo người nhận. THUẦN: cac_quay truyền vào từ ngoài."""
	if loai not in CHAN_HOP_LE:
		loai = "khach"
	dong = []
	if loai == "khach":
		dong.append("<b>%s</b>" % TEN_TIEM)
		for q in cac_quay or []:
			dong.append(h(q))
		dong.append("Hotline %s &middot; %s" % (h(HOTLINE), h(WEB)))
		dong.append("Đặt bánh online: %s" % h(WEB_DAT_BANH))
	elif loai == "ncc":
		dong.append("<b>CÔNG TY TNHH PATISSERIE VAGABOND</b>")
		dong.append("Mã số thuế 0318561568 &middot; 9 Trần Cao Vân, Phường Sài Gòn, TP.HCM")
		dong.append(h(WEB))
	elif loai == "nhan_vien":
		dong.append("<b>%s</b> &middot; app quản lý nội bộ" % TEN_TIEM)
		dong.append(h(HO_TRO_APP))
	else:
		dong.append("<b>%s</b> &middot; thư tự động từ hệ thống vận hành" % TEN_TIEM)
		dong.append("Việc xử lý làm trong app. Không cần trả lời thư này.")
	return (
		'<tr><td background="%s" bgcolor="%s" style="padding:4px 30px;font-size:0;line-height:0;height:4px">&nbsp;</td></tr>'
		'<tr><td bgcolor="%s" style="padding:16px 30px 18px;text-align:center;%s">%s</td></tr>'
	) % (
		_anh(goc_anh, ANH_LOT_XANH), XANH, KEM,
		_chu(12, XAM, False, 1.75), "<br>".join(dong),
	)


def khung_thuan(tieu_de, than, nut_html="", chan="khach", nhan="", goc_anh="", cac_quay=None):
	"""Dựng cả lá thư. THUẦN, không chạm Frappe.

	tieu_de : tiêu đề lớn (chữ thường, máy tự in đậm)
	than    : HTML thân thư, đã thoát ở chỗ gọi
	nut_html: kết quả của nut(), để trống nếu không có nút
	chan    : một trong CHAN_HOP_LE
	nhan    : nhãn nhỏ viết HOA phía trên tiêu đề (vd "Báo giá", "Thư nội bộ")
	"""
	return (
		'<div style="margin:0;padding:0;background:%(kem)s">'
		'<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0" '
		'bgcolor="%(kem)s"><tr><td align="center" style="padding:20px 8px">'
		'<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" '
		'style="width:600px;max-width:600px;background:#FFFFFF;border:1px solid %(ke)s">'
		'<tr><td background="%(lot)s" bgcolor="%(xanh)s"><img src="%(dau)s" width="600" height="200" '
		'alt="%(tiem)s" style="display:block;width:100%%;height:auto;border:0"></td></tr>'
		'<tr><td style="padding:26px 30px 0">%(nhan)s'
		'<div style="%(tieu_de_css)s">%(tieu_de)s</div>'
		'<div style="width:36px;height:3px;background:%(xanh)s;margin:12px 0 18px;font-size:0;line-height:0">&nbsp;</div>'
		"</td></tr>"
		'<tr><td style="padding:0 30px 6px;%(than_css)s">%(than)s</td></tr>'
		"%(nut)s"
		"%(chan)s"
		"</table></td></tr></table></div>"
	) % {
		"kem": KEM, "ke": KE, "xanh": XANH, "tiem": TEN_TIEM,
		"lot": _anh(goc_anh, ANH_LOT_XANH), "dau": _anh(goc_anh, ANH_DAU),
		"nhan": nhan_hoa(nhan) if nhan else "",
		"tieu_de_css": _chu(21, MUC, True, 1.3, "margin-top:%dpx;" % (6 if nhan else 0)),
		"tieu_de": h(tieu_de),
		"than_css": _chu(14, MUC),
		"than": than,
		"nut": ('<tr><td style="padding:14px 30px 26px">%s</td></tr>' % nut_html) if nut_html
			else '<tr><td style="padding:0 30px 20px"></td></tr>',
		"chan": _chan(chan, goc_anh, cac_quay),
	}


# ------------------------------------------------------------- chạm hệ

def goc_anh():
	"""Địa chỉ gốc để lấy ảnh: tên miền app nếu đã khai, không thì tên miền site."""
	try:
		from vagabond.nhan_su import link_app

		return link_app()
	except Exception:
		try:
			import frappe
			from frappe.utils import get_url

			return get_url().rstrip("/")
		except Exception:
			return ""


def _cac_quay():
	"""Địa chỉ các quầy đang bật, đọc từ cấu hình điểm bán. Hỏng thì lùi về
	hai địa chỉ cố định để chân thư không bao giờ trống."""
	try:
		from vagabond import diem_ban

		ra = []
		for d in diem_ban.ds(chi_bat=True):
			if not d.get("quay"):
				continue
			dc = d.get("dia_chi") or d.get("phu") or ""
			if dc:
				ra.append("%s: %s" % (d.get("ten_ngan") or d.get("ten"), dc))
		if ra:
			return ra
	except Exception:
		pass
	return ["District 1: 9 Trần Cao Vân, Quận 1", "NVHTN: 21 Phạm Ngọc Thạch, Quận 3"]


def khung(tieu_de, than, nut_html="", chan="khach", nhan=""):
	"""Cửa dùng thật: tự điền địa chỉ ảnh và danh sách quầy."""
	return khung_thuan(
		tieu_de, than, nut_html=nut_html, chan=chan, nhan=nhan,
		goc_anh=goc_anh(), cac_quay=_cac_quay() if chan == "khach" else None,
	)
