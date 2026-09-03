# -*- coding: utf-8 -*-
"""Phiếu thanh toán hợp đồng: thu tiền theo đợt của một hợp đồng đã ký.

VÌ SAO CÓ TỆP NÀY, ngày 28/08/2026
--------------------------------------------------------------------
Anh Việt: *"Tạo phiếu thanh toán. Có thể chọn mức 50% hoặc nút 100% giá
trị hợp đồng. Generate ra file và QR Code và nội dung chuyển khoản
'Thanh toán 50PT (hoặc 100PT nếu là thanh toán 100%) gia tri hop dong
(chèn mã hợp đồng)'. Luồng này giống như luồng tạo phiếu thu công nợ."*

Nên tệp này đi đúng vết `cong_no.py`: sinh mã phiếu, sinh mã QR VietQR,
dựng một tờ A4 gửi khách, rồi để máy dò SePay xem tiền về chưa.

BA CHỖ KHÁC PHIẾU CÔNG NỢ, và lý do
--------------------------------------------------------------------
1. Tờ phiếu bày TIẾN ĐỘ HAI ĐỢT của hợp đồng chứ không bày danh sách hoá
   đơn. Khách hợp đồng cần biết mình đang trả đợt mấy và còn đợt nào;
   danh sách hoá đơn là thứ của khách sỉ mua lai rai cả tháng.

2. Mức thu có BA chip chứ không phải hai. Anh Việt nói 50% và 100%,
   nhưng hồ sơ hợp đồng có ô tỷ lệ đặt cọc riêng và có tờ ghi 30% hoặc
   40%. Chip đợt 1 đọc đúng tỷ lệ của chính tờ đang mở, cộng thêm đường
   gõ số khác. Đặt cứng 50 là thu nhầm những tờ không phải 50.

3. Tiền tố mã riêng `PTHD` thay vì `DNTT`. Nhìn mã là biết tiền này của
   hợp đồng chứ không phải của công nợ bán sỉ, mà chị Dung thì đối soát
   hai luồng này ở hai chỗ khác nhau.
"""

import re

# Tiền tố mã phiếu. Đếm lại từ 1 mỗi tháng, giống hệt cách `cong_no` đặt
# mã: mã dài mà mang sẵn tháng thì đọc sao kê cuối năm còn lần ra được.
TIEN_TO = "PTHD"

# Hạn của mã QR, tính bằng ngày kể từ lúc lập phiếu. Bằng đúng hạn của
# phiếu công nợ để hai luồng không dạy khách hai con số khác nhau.
QR_SO_NGAY = 7

# Mức thu mà máy nhận. `None` nghĩa là gõ số khác.
MUC_TRON = (50, 100)

TT_CHO = "Cho thu"
TT_DA_THU = "Da thu"
TT_HUY = "Huy"

# Hop thu gui phieu cho khach, va hop thu nhan ban sao. Cung cach da lam
# cho thu bao nha cung cap ngay 28/08/2026.
EMAIL_SALES = "sales@thevagabondpatisserie.com"
EMAIL_KE_TOAN = "account@thevagabondpatisserie.com"
TEN_TIEM = "The Vagabond Pâtisserie"
NHAN_TT = {TT_CHO: "Chờ thu", TT_DA_THU: "Đã thu", TT_HUY: "Đã huỷ"}


def bo_dau(s):
	"""Bỏ dấu tiếng Việt. THUẦN.

	Ngân hàng đẩy nội dung chuyển khoản CÓ DẤU về SePay là thành một dãy
	dấu hỏi, mất luôn đường dò tiền tự động. Đây là bài học đã ghi ở
	`ho_so_tt._noi_dung_ck`, chép lại đây để tệp này còn chạy được khi
	kiểm thử không nạp Frappe.
	"""
	import unicodedata

	s = unicodedata.normalize("NFD", str(s or ""))
	s = "".join(c for c in s if unicodedata.category(c) != "Mn")
	return s.replace("đ", "d").replace("Đ", "D")


def sach_ma_hd(so_hop_dong):
	"""Mã hợp đồng rút về dạng ngân hàng không nuốt. THUẦN.

	`HD-26-08-012` thành `HD26080012`. Bỏ gạch ngang và mọi ký tự lạ: một
	số ngân hàng cắt hoặc thay ký tự đặc biệt trong nội dung chuyển
	khoản, mà mã này chính là thứ phép dò SePay bám vào.
	"""
	return re.sub(r"[^A-Za-z0-9]", "", bo_dau(so_hop_dong)).upper()


def noi_dung_ck(muc_pt, so_hop_dong):
	"""Nội dung chuyển khoản in lên phiếu và nhét vào mã QR. THUẦN.

	Cú pháp anh Việt chốt 28/08/2026, giữ nguyên chữ:

	    THANH TOAN <mức>PT GIA TRI HOP DONG <mã hợp đồng>

	Mức làm tròn về số nguyên: `50.0` và `50` phải ra cùng một chuỗi, nếu
	không thì hai lần lập phiếu cho cùng một đợt lại ra hai nội dung, và
	phép dò sao kê thấy hai khoản khác nhau.
	"""
	try:
		muc = int(round(float(muc_pt or 0)))
	except Exception:
		muc = 0
	ma = sach_ma_hd(so_hop_dong)
	nd = "THANH TOAN %dPT GIA TRI HOP DONG %s" % (muc, ma)
	return re.sub(r"\s+", " ", nd).strip()


def tien_theo_muc(gia_tri, muc_pt):
	"""Số tiền phải thu ứng với một mức phần trăm. THUẦN.

	Làm tròn về ĐỒNG chứ không giữ số lẻ: số tiền này in lên phiếu, nhét
	vào mã QR và đọc thành chữ. Ba chỗ đó mà lệch nhau vài xu là khách
	chuyển một đằng sổ ghi một nẻo.
	"""
	try:
		gt = float(gia_tri or 0)
		mp = float(muc_pt or 0)
	except Exception:
		return 0
	if gt <= 0 or mp <= 0:
		return 0
	# Lam tron NUA LEN chu khong dung round() cua Python: round(500.5)
	# tra 500 chu khong phai 501, va mot con so tien nhin thay 500,5 ma
	# ra 500 la thu khong ai giai thich duoc cho khach.
	return int(gt * mp / 100.0 + 0.5)


def muc_hop_le(muc_pt):
	"""Mức phần trăm có nhận được không. THUẦN."""
	try:
		mp = float(muc_pt or 0)
	except Exception:
		return False
	return 0 < mp <= 100


def nhan_muc(muc_pt):
	"""Nhãn ngắn của mức thu, để màn hình và tờ phiếu gọi cùng một tên. THUẦN."""
	try:
		mp = int(round(float(muc_pt or 0)))
	except Exception:
		mp = 0
	if mp >= 100:
		return "Toàn bộ giá trị hợp đồng"
	return "Thanh toán %d%% giá trị hợp đồng" % mp


def loi_chua_chot(nhan_trang_thai):
	"""Câu chặn khi hợp đồng chưa tới bước thu tiền. THUẦN."""
	return (
		"Hợp đồng đang ở %s nên chưa thu tiền theo nó được. Con số trên hợp đồng "
		"chưa chốt, thu theo con số chưa chốt thì sau này phải hoàn lại cho khách. "
		"Chuyển hợp đồng sang Đang thực hiện rồi bấm lại." % (nhan_trang_thai or "")
	)


def loi_khong_co_gia_tri(ma):
	"""Câu chặn khi hợp đồng chưa có giá trị. THUẦN."""
	return (
		"Hợp đồng %s chưa có giá trị nên chưa tính được số tiền phải thu. "
		"Anh chị mở hợp đồng, bấm Điều chỉnh và điền giá trị rồi quay lại." % (ma or "")
	)


# ------------------------------------------------------- phần cần Frappe

import base64

import frappe
from frappe.utils import add_days, cint, flt, getdate, now_datetime, nowdate

DT = "Vagabond Thu Hop Dong"
DT_HD = "Hop Dong Ban Hang"

# Trang thai hop dong duoc phep thu tien. Nhap va Da gui khach thi con so
# chua chot; Dang thuong thao thi dang doi lai; Huy thi khoi noi.
TT_HD_THU_DUOC = ("Dang thuc hien", "Hoan tat", "Da thanh ly")


def _quyen():
	from vagabond.hop_dong import _quyen as q

	q()


def _sinh_ma():
	"""Mã phiếu PTHD-yy-mm-nnnnn, đếm lại từ 1 mỗi tháng."""
	h = getdate()
	dau = "%s-%02d-%02d-" % (TIEN_TO, h.year % 100, h.month)
	cu = frappe.db.sql(
		"select name from `tab%s` where name like %%s order by name desc limit 1" % DT,
		dau + "%",
	)
	so = 1
	if cu:
		try:
			so = int(str(cu[0][0]).split("-")[-1]) + 1
		except Exception:
			so = 1
	return "%s%05d" % (dau, so)


def _hop_dong(ten):
	if not ten or not frappe.db.exists(DT_HD, ten):
		frappe.throw("Không tìm thấy hợp đồng %s." % (ten or "(trống)"))
	return frappe.get_doc(DT_HD, ten)


def _nhan_tt_hd(tt):
	return {
		"Nhap": "Nháp", "Da gui khach": "Đã gửi khách",
		"Dang thuong thao": "Đang thương thảo", "Dang thuc hien": "Đang thực hiện",
		"Hoan tat": "Hoàn tất", "Da thanh ly": "Đã thanh lý", "Huy": "Huỷ",
	}.get(tt, tt or "")


@frappe.whitelist()
def muc_goi_y(hop_dong=None):
	"""Ba chip mức thu của đúng hợp đồng này.

	Chip đợt 1 đọc tỷ lệ đặt cọc ghi trên chính hợp đồng, không đặt cứng
	50: có tờ ghi 30%, có tờ ghi 40%. Hợp đồng không khai tỷ lệ nào thì
	rơi về 50 và màn hình nói rõ đó là con số mặc định.
	"""
	_quyen()
	hd = _hop_dong(hop_dong)
	gt = flt(hd.gia_tri)
	pt = flt(hd.get("dat_coc_pt"))
	tu_hd = pt > 0
	if not tu_hd:
		pt = 50
	da_thu = _da_thu(hop_dong)
	return {
		"hop_dong": hd.name,
		"so_hop_dong": hd.get("so_hop_dong") or hd.name,
		"ten": hd.ten or "",
		"gia_tri": gt,
		"trang_thai": hd.trang_thai,
		"nhan_trang_thai": _nhan_tt_hd(hd.trang_thai),
		"thu_duoc": 1 if hd.trang_thai in TT_HD_THU_DUOC else 0,
		"da_thu": da_thu,
		"con_lai": max(0.0, gt - da_thu),
		"muc": [
			{
				"pt": pt, "tien": tien_theo_muc(gt, pt),
				"nhan": "Đợt 1 · %g%%" % pt,
				"tu_hop_dong": 1 if tu_hd else 0,
			},
			{"pt": 100, "tien": tien_theo_muc(gt, 100), "nhan": "Toàn bộ · 100%", "tu_hop_dong": 0},
		],
		"email": hd.get("email") or hd.get("email_ky_a") or "",
		"ten_khach": hd.get("ten_khach") or hd.get("khach_hang") or "",
	}


def _da_thu(hop_dong):
	"""Tổng tiền đã thu qua các phiếu của hợp đồng này."""
	try:
		r = frappe.db.sql(
			"select coalesce(sum(da_thu),0) from `tab%s` "
			"where hop_dong = %%s and trang_thai != %%s" % DT,
			(hop_dong, TT_HUY),
		)
		return flt(r[0][0]) if r else 0.0
	except Exception:
		return 0.0


@frappe.whitelist()
def tao_phieu(hop_dong=None, muc_pt=None, so_tien=None, ghi_chu=""):
	"""Lập một phiếu thanh toán cho hợp đồng.

	`so_tien` chỉ dùng khi người bấm chọn "Số khác". Còn lại máy tự tính
	từ mức phần trăm, để hai chỗ không ra hai con số.
	"""
	_quyen()
	hd = _hop_dong(hop_dong)
	if hd.trang_thai not in TT_HD_THU_DUOC:
		frappe.throw(loi_chua_chot(_nhan_tt_hd(hd.trang_thai)), title="Chưa thu tiền được")
	gt = flt(hd.gia_tri)
	if gt <= 0:
		frappe.throw(loi_khong_co_gia_tri(hd.get("so_hop_dong") or hd.name))

	if so_tien is not None and flt(so_tien) > 0:
		tien = flt(so_tien)
		pt = round(tien * 100.0 / gt, 2) if gt else 0
	else:
		if not muc_hop_le(muc_pt):
			frappe.throw("Mức thu phải nằm trong khoảng lớn hơn 0 và không quá 100%.")
		pt = flt(muc_pt)
		tien = tien_theo_muc(gt, pt)
	if tien <= 0:
		frappe.throw("Số tiền phải thu đang bằng 0, chưa lập phiếu được.")

	doc = frappe.new_doc(DT)
	doc.name = _sinh_ma()
	doc.ma_phieu = doc.name
	doc.hop_dong = hd.name
	doc.so_hop_dong = hd.get("so_hop_dong") or hd.name
	doc.ten_hop_dong = hd.get("ten") or ""
	doc.khach_hang = hd.get("khach_hang") or ""
	doc.ten_khach = hd.get("ten_khach") or hd.get("khach_hang") or ""
	doc.ma_so_thue = hd.get("ma_so_thue") or ""
	doc.nguoi_lien_he = hd.get("dai_dien") or ""
	doc.email = hd.get("email") or hd.get("email_ky_a") or ""
	doc.gia_tri_hd = gt
	doc.muc_pt = pt
	doc.so_tien = tien
	doc.noi_dung_ck = noi_dung_ck(pt, doc.so_hop_dong)
	doc.ngay_tao = nowdate()
	doc.han_tt = add_days(nowdate(), QR_SO_NGAY)
	doc.trang_thai = TT_CHO
	doc.da_thu = 0
	doc.nguoi_tao = frappe.session.user
	doc.ghi_chu = (ghi_chu or "").strip()
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	try:
		hd.add_comment("Comment", "Lập phiếu thanh toán %s, số tiền %s đ." % (
			doc.name, "{:,.0f}".format(tien).replace(",", ".")))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thu_hop_dong: ghi vet lap phieu")
	return xem_phieu(doc.name)


@frappe.whitelist()
def ds_phieu(hop_dong=None):
	"""Các phiếu thanh toán của một hợp đồng, mới nhất trước."""
	_quyen()
	ds = frappe.get_all(
		DT,
		filters={"hop_dong": hop_dong} if hop_dong else {},
		fields=[
			"name", "ma_phieu", "hop_dong", "so_hop_dong", "ten_khach", "muc_pt",
			"so_tien", "da_thu", "trang_thai", "ngay_tao", "han_tt", "noi_dung_ck",
			"email_gui_toi", "email_gui_luc",
		],
		order_by="creation desc",
		limit_page_length=100,
	)
	for d in ds:
		d["nhan"] = NHAN_TT.get(d["trang_thai"], d["trang_thai"])
		d["con_thieu"] = max(0.0, flt(d["so_tien"]) - flt(d["da_thu"]))
	return {"rows": ds}


@frappe.whitelist()
def xem_phieu(name=None):
	"""Một phiếu, kèm thông tin tài khoản nhận tiền để màn hình vẽ."""
	_quyen()
	if not frappe.db.exists(DT, name):
		frappe.throw("Không tìm thấy phiếu %s." % (name or "(trống)"))
	d = frappe.get_doc(DT, name).as_dict()
	from vagabond import tai_khoan

	d["qr"] = tai_khoan.tk_phieu_no() or {}
	d["nhan"] = NHAN_TT.get(d.get("trang_thai"), d.get("trang_thai"))
	d["con_thieu"] = max(0.0, flt(d.get("so_tien")) - flt(d.get("da_thu")))
	d["dot"] = _bang_dot(d)
	return d


def _bang_dot(d):
	"""Hai dòng tiến độ in trên tờ phiếu: đợt đang thu và phần còn lại."""
	gt = flt(d.get("gia_tri_hd"))
	tien = flt(d.get("so_tien"))
	con = max(0.0, gt - tien)
	pt = flt(d.get("muc_pt"))
	ra = [{
		"stt": 1,
		"noi_dung": "Thanh toán đợt này theo Điều khoản thanh toán của hợp đồng",
		"ty_le": "%g%%" % pt,
		"so_tien": tien,
		"tinh_trang": "Đang thu",
	}]
	if con > 0:
		ra.append({
			"stt": 2,
			"noi_dung": "Thanh toán phần còn lại theo hợp đồng",
			"ty_le": "%g%%" % max(0.0, 100.0 - pt),
			"so_tien": con,
			"tinh_trang": "Chưa đến hạn",
		})
	return ra


@frappe.whitelist()
def huy_phieu(name=None, ly_do=""):
	"""Huỷ một phiếu lập nhầm. KHÔNG xoá, phiếu vẫn nằm lại để truy được."""
	_quyen()
	if not frappe.db.exists(DT, name):
		frappe.throw("Không tìm thấy phiếu %s." % (name or "(trống)"))
	doc = frappe.get_doc(DT, name)
	if doc.trang_thai == TT_DA_THU:
		frappe.throw(
			"Phiếu %s đã ghi nhận tiền về nên không huỷ được. Tiền đã vào tài khoản "
			"thật thì phải xử lý bên kế toán chứ không xoá phiếu." % name
		)
	doc.trang_thai = TT_HUY
	doc.ly_do_huy = (ly_do or "").strip()
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "trang_thai": doc.trang_thai}


@frappe.whitelist()
def kiem_sepay(name=None):
	"""Dò sao kê xem tiền của phiếu này về chưa. Chỉ đọc, không ghi sổ.

	Dò theo MÃ HỢP ĐỒNG trong nội dung giao dịch chứ không theo số tiền:
	hai khách cùng chuyển 8.789.400 đ trong một ngày là chuyện thường, dò
	theo số tiền là khớp nhầm.
	"""
	_quyen()
	d = xem_phieu(name)
	ma = sach_ma_hd(d.get("so_hop_dong") or "")
	if not ma:
		return {"so_gd": 0, "da_ve": 0, "vi_sao": "Hợp đồng chưa có số nên không dò được."}
	try:
		from vagabond import sepay

		gd = sepay.tim_theo_noi_dung(ma) if hasattr(sepay, "tim_theo_noi_dung") else []
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thu_hop_dong: do SePay loi")
		gd = []
	tong = sum(flt(x.get("amount_in") or x.get("so_tien")) for x in gd or [])
	return {"so_gd": len(gd or []), "da_ve": tong, "ma_do": ma}


@frappe.whitelist()
def ghi_da_thu(name=None, so_tien=None, ma_giao_dich="", ngay=None):
	"""Kế toán xác nhận tiền của phiếu đã về.

	Không tự sinh bút toán ở đây: tiền của hợp đồng vào sổ qua hoá đơn bán
	hàng và phiếu thu của kế toán. Ô này chỉ đánh dấu trên phiếu để sales
	nhìn màn hình biết đợt nào đã thu xong.
	"""
	_quyen()
	if not frappe.db.exists(DT, name):
		frappe.throw("Không tìm thấy phiếu %s." % (name or "(trống)"))
	doc = frappe.get_doc(DT, name)
	if doc.trang_thai == TT_HUY:
		frappe.throw("Phiếu %s đã huỷ, không ghi nhận tiền vào đó được." % name)
	tien = flt(so_tien) if so_tien is not None else flt(doc.so_tien)
	if tien <= 0:
		frappe.throw("Số tiền ghi nhận phải lớn hơn 0.")
	doc.da_thu = tien
	doc.ma_giao_dich = (ma_giao_dich or "").strip()
	doc.ngay_thu = getdate(ngay) if ngay else getdate()
	doc.trang_thai = TT_DA_THU if tien >= flt(doc.so_tien) - 1 else TT_CHO
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return xem_phieu(name)


# ------------------------------------------------ tờ phiếu gửi khách


def _phieu_html(name):
	"""Tờ A4 gửi khách, dùng đúng khuôn bản in của phiếu công nợ.

	Dùng lại khuôn có sẵn chứ không vẽ khuôn thứ hai: khách sỉ đã nhận
	phiếu công nợ theo mẫu đó rồi, tờ này nhìn lệch đi là họ tưởng của
	một bên khác. Ba hàm định dạng cũng gọi thẳng sang `cong_no`, để
	tiền, ngày và số tiền bằng chữ chỉ có MỘT cách viết trong cả hệ.
	"""
	from vagabond.cong_no import (
		TEN_NGAN_HANG_DAY_DU, _chu_so_tien, _ngay_vn, _qr_data_uri, _tien_vn,
	)

	d = xem_phieu(name)
	qr = d.get("qr") or {}
	esc = frappe.utils.escape_html

	# Xâu phông lấy từ một nơi duy nhất, xem vagabond/phong_chu.py.
	from vagabond.mau_chuan import PHONG
	VIEN = "1px solid #c9c4bd"
	o_th = (
		'style="border:%s;padding:6px 7px;background:#f3f0ec;font-size:10.5px;'
		'font-weight:bold;text-align:center"' % VIEN
	)

	def _td(noi, canh="left", dam=False, khong_ngat=False):
		return (
			'<td style="border:%s;padding:5px 7px;font-size:10.5px;text-align:%s;%s%s">%s</td>'
			% (VIEN, canh, "font-weight:bold;" if dam else "",
			   "white-space:nowrap;" if khong_ngat else "", noi)
		)

	hang = []
	for x in d.get("dot") or []:
		dang = x.get("tinh_trang") == "Đang thu"
		hang.append(
			"<tr>"
			+ _td(str(x.get("stt")), "center")
			+ _td(esc(x.get("noi_dung") or ""))
			+ _td(esc(x.get("ty_le") or ""), "center", khong_ngat=True)
			+ _td(_tien_vn(x.get("so_tien")), "right", dam=dang, khong_ngat=True)
			+ _td(esc(x.get("tinh_trang") or ""), "center", dam=dang, khong_ngat=True)
			+ "</tr>"
		)

	gt = flt(d.get("gia_tri_hd"))
	tien = flt(d.get("so_tien"))
	da_thu = flt(d.get("da_thu"))
	con_thieu = max(0.0, tien - da_thu)

	cuoi = (
		'<tr><td colspan="3" style="border:%s;padding:6px 7px;font-size:11px;'
		'text-align:right;font-weight:bold">GIÁ TRỊ HỢP ĐỒNG</td>'
		'<td style="border:%s;padding:6px 7px;font-size:11.5px;text-align:right;'
		'white-space:nowrap;font-weight:bold">%s</td>'
		'<td style="border:%s"></td></tr>' % (VIEN, VIEN, _tien_vn(gt), VIEN)
	)
	cuoi += (
		'<tr><td colspan="3" style="border:%s;padding:6px 7px;font-size:11.5px;'
		'text-align:right;font-weight:bold">SỐ TIỀN PHẢI THANH TOÁN LẦN NÀY</td>'
		'<td style="border:%s;padding:6px 7px;font-size:12.5px;text-align:right;'
		'white-space:nowrap;font-weight:bold">%s</td>'
		'<td style="border:%s"></td></tr>' % (VIEN, VIEN, _tien_vn(tien), VIEN)
	)
	if da_thu > 0:
		cuoi += (
			'<tr><td colspan="3" style="border:%s;padding:6px 7px;font-size:11px;'
			'text-align:right">Đã nhận</td>'
			'<td style="border:%s;padding:6px 7px;font-size:11px;text-align:right;'
			'white-space:nowrap">%s</td><td style="border:%s"></td></tr>'
			'<tr><td colspan="3" style="border:%s;padding:6px 7px;font-size:11.5px;'
			'text-align:right;font-weight:bold">CÒN PHẢI THANH TOÁN</td>'
			'<td style="border:%s;padding:6px 7px;font-size:12.5px;text-align:right;'
			'white-space:nowrap;font-weight:bold">%s</td><td style="border:%s"></td></tr>'
			% (VIEN, VIEN, _tien_vn(da_thu), VIEN, VIEN, VIEN, _tien_vn(con_thieu), VIEN)
		)

	def _o_tt(nhan, gt_, to=False, nho=False):
		return (
			'<tr><td style="border:none;padding:3px 0;font-size:11px;color:#555;'
			'width:38%%;vertical-align:top">%s</td>'
			'<td style="border:none;padding:3px 0;font-size:%s;font-weight:bold;'
			'vertical-align:top">%s</td></tr>'
			% (nhan, "14px" if to else ("10px" if nho else "11.5px"), gt_)
		)

	nd_ck = d.get("noi_dung_ck") or ""
	anh_qr = _qr_data_uri(qr, con_thieu, nd_ck)
	o_qr = (
		'<td style="border:none;width:170px;text-align:center;vertical-align:top;'
		'padding-left:12px">'
		'<img src="%s" width="150" height="150" '
		'style="width:150px !important;height:150px !important">'
		'<div style="font-size:9.5px;color:#555;margin-top:4px">Quét mã để chuyển khoản</div>'
		"</td>" % anh_qr
	) if anh_qr else ""

	khoi_ck = (
		'<div style="border:2px solid #1c1a17;padding:12px 14px;margin-top:14px">'
		'<div style="font-size:11px;font-weight:bold;letter-spacing:.5px;'
		'margin-bottom:7px">THÔNG TIN CHUYỂN KHOẢN</div>'
		'<table style="width:100%;border:none;border-collapse:collapse"><tr>'
		'<td style="border:none;vertical-align:top">'
		'<table style="width:100%;border:none;border-collapse:collapse">'
		+ _o_tt("Ngân hàng:", esc(
			TEN_NGAN_HANG_DAY_DU.get(qr.get("bank") or "", qr.get("bank") or "...............")
		))
		+ _o_tt("Số tài khoản:", esc(qr.get("stk") or "..............."), to=True)
		+ _o_tt("Tên tài khoản:", esc(qr.get("ten") or "..............."))
		+ _o_tt("Số tiền:", _tien_vn(con_thieu) + " đ", to=True)
		+ _o_tt("Nội dung chuyển khoản:", esc(nd_ck), nho=True)
		+ "</table></td>"
		+ o_qr
		+ "</tr></table>"
		'<div style="font-size:10px;color:#555;margin-top:8px;line-height:1.5">'
		"Quý khách vui lòng giữ nguyên nội dung chuyển khoản để hệ thống đối soát "
		"tự động. Sau khi nhận được tiền, chúng tôi sẽ xuất hoá đơn giá trị gia tăng "
		"và gửi qua email trong vòng 24 giờ làm việc.</div></div>"
	)

	ben_nhan = (
		'<table style="width:100%;border:none;border-collapse:collapse">'
		+ _o_tt("Kính gửi:", esc(d.get("ten_khach") or ""), to=True)
		+ (_o_tt("Mã số thuế:", esc(d.get("ma_so_thue") or "")) if d.get("ma_so_thue") else "")
		+ (_o_tt("Người liên hệ:", esc(d.get("nguoi_lien_he") or "")) if d.get("nguoi_lien_he") else "")
		+ _o_tt("Theo hợp đồng số:", esc(d.get("so_hop_dong") or ""))
		+ (_o_tt("Nội dung:", esc(d.get("ten_hop_dong") or "")) if d.get("ten_hop_dong") else "")
		+ _o_tt("Hạn thanh toán:", _ngay_vn(d.get("han_tt")) or "...............")
		+ "</table>"
	)

	ghi_chu = ""
	if (d.get("ghi_chu") or "").strip():
		ghi_chu = (
			'<div style="margin-top:12px;font-size:11px"><b>Ghi chú:</b> %s</div>'
			% esc(d["ghi_chu"])
		)

	return (
		'<div style="font-family:%s;color:#1c1a17;font-size:12px;line-height:1.45">'
		'<table style="width:100%%;border:none;border-collapse:collapse"><tr>'
		'<td style="border:none;width:45%%;vertical-align:middle">'
		'<img src="/files/vagabond_logo_print.png" width="150" height="62" '
		'style="width:150px !important;height:62px !important;object-fit:contain">'
		"</td>"
		'<td style="border:none;text-align:right;vertical-align:middle;font-size:9.5px;'
		'color:#444;line-height:1.5">'
		'<b style="font-size:10.5px;color:#1c1a17">CÔNG TY TNHH PATISSERIE VAGABOND</b><br>'
		"MST: 0318561568<br>"
		"9 Trần Cao Vân, Phường Sài Gòn, TP.HCM<br>"
		"www.thevagabondpatisserie.com"
		"</td></tr></table>"
		'<div style="text-align:center;margin:14px 0 2px">'
		'<div style="font-size:19px;font-weight:bold;letter-spacing:1px">'
		"PHIẾU THANH TOÁN HỢP ĐỒNG</div>"
		'<div style="font-size:11px;color:#555;margin-top:3px">'
		"Số: <b>%s</b> &nbsp;·&nbsp; Ngày %s</div></div>"
		"%s"
		'<table style="width:100%%;border-collapse:collapse;margin-top:12px">'
		"<tr><th %s>Đợt</th><th %s>Nội dung</th><th %s>Tỷ lệ</th>"
		"<th %s>Số tiền</th><th %s>Tình trạng</th></tr>%s%s</table>"
		'<div style="margin-top:8px;font-size:11px">Số tiền bằng chữ: '
		"<i>%s</i></div>"
		"%s%s"
		'<table style="width:100%%;border:none;border-collapse:collapse;margin-top:26px">'
		'<tr><td style="border:none;width:50%%;text-align:center;font-size:11px">'
		'<b>ĐẠI DIỆN BÊN MUA</b><div style="font-size:10px;color:#666;margin-top:2px">'
		"(Ký, ghi rõ họ tên)</div>"
		'<div style="height:58px"></div></td>'
		'<td style="border:none;width:50%%;text-align:center;font-size:11px">'
		"<b>THE VAGABOND PÂTISSERIE</b>"
		'<div style="font-size:10px;color:#666;margin-top:2px">(Ký, ghi rõ họ tên)</div>'
		'<div style="height:58px"></div>'
		'<div style="font-size:10.5px">%s</div></td></tr></table>'
		'<div style="margin-top:14px;font-size:9.5px;color:#777;text-align:center">'
		"Phiếu này được lập từ hệ thống The Vagabond Pâtisserie. "
		"Mọi thắc mắc xin liên hệ bộ phận kinh doanh.</div>"
		"</div>"
	) % (
		PHONG,
		esc(d.get("ma_phieu") or name), _ngay_vn(d.get("ngay_tao")),
		ben_nhan,
		o_th, o_th, o_th, o_th, o_th,
		"".join(hang), cuoi,
		_chu_so_tien(con_thieu),
		khoi_ck, ghi_chu,
		esc(frappe.db.get_value("User", d.get("nguoi_tao") or frappe.session.user, "full_name") or ""),
	)


@frappe.whitelist()
def xem_truoc(name=None):
	"""HTML tờ phiếu để xem trước trên app trước khi tải PDF."""
	_quyen()
	return {"html": _phieu_html(name)}


@frappe.whitelist()
def xuat_pdf(name=None):
	"""Tờ phiếu ra PDF A4 dọc để gửi khách."""
	_quyen()
	from frappe.utils.pdf import get_pdf

	# Đi qua khung chuẩn: nó chép bộ phông tiếng Việt vào máy chủ rồi ép
	# phông cho cả tờ. Xem vagabond/phong_chu.py.
	from vagabond import mau_chuan

	khung = mau_chuan.khung_trang(_phieu_html(name), name, le="12mm 10mm")
	noi_dung = get_pdf(khung, options={"page-size": "A4", "orientation": "Portrait"})
	return {
		"ten_file": "Phieu-thanh-toan-%s.pdf" % name,
		"b64": base64.b64encode(noi_dung).decode(),
		"kieu": "application/pdf",
	}


@frappe.whitelist()
def gui_email(name=None, email=None):
	"""Gửi tờ phiếu cho khách, kèm PDF.

	Gửi từ hộp SALES và gửi bản sao cho kế toán, cùng cách vừa làm cho thư
	báo nhà cung cấp: khách bấm Trả lời là về đúng người đang làm việc với
	họ, mà kế toán vẫn thấy đã hẹn gì với khách.
	"""
	_quyen()
	d = xem_phieu(name)
	toi = (email or d.get("email") or "").strip()
	if not toi or "@" not in toi:
		frappe.throw(
			"Chưa có email của khách. Anh chị điền email vào hợp đồng, hoặc gõ tay "
			"vào ô gửi tới."
		)
	if d.get("trang_thai") == TT_HUY:
		frappe.throw("Phiếu %s đã huỷ, không gửi cho khách được." % name)

	from vagabond import thu_khung as _tk

	_o_nhat = lambda x: _tk.o_kem(x, goc_anh=_tk.goc_anh())
	tep = xuat_pdf(name)
	h = frappe.utils.escape_html
	than = (
		"<p style='margin:0 0 14px'>Kính gửi <b>%s</b>,</p>"
		"<p style='margin:0 0 12px'>%s xin gửi quý khách phiếu thanh toán "
		"<b>%s</b> cho hợp đồng <b>%s</b>. Chi tiết và mã QR chuyển khoản nằm "
		"trong tệp PDF đính kèm.</p>%s"
		"<p style='margin:14px 0 0'>Quý khách vui lòng giữ nguyên nội dung chuyển "
		"khoản để hệ thống đối soát tự động. Sau khi nhận được tiền, chúng tôi sẽ "
		"xuất hoá đơn giá trị gia tăng và gửi qua email này.</p>"
		"<p style='margin:12px 0 0'>Trân trọng cảm ơn quý khách.</p>"
	) % (
		h(d.get("ten_khach") or ""),
		TEN_TIEM,
		h(d.get("ma_phieu") or name),
		h(d.get("so_hop_dong") or ""),
		_o_nhat("<br>".join([
			"Số tiền: <b>%s đ</b>" % "{:,.0f}".format(flt(d.get("con_thieu"))).replace(",", "."),
			"Nội dung chuyển khoản: <b>%s</b>" % h(d.get("noi_dung_ck") or ""),
			"Hạn thanh toán: <b>%s</b>" % (str(d.get("han_tt") or "")),
		])),
	)
	frappe.sendmail(
		recipients=[toi],
		cc=[EMAIL_KE_TOAN],
		sender=EMAIL_SALES,
		subject="%s - Phiếu thanh toán hợp đồng %s" % (TEN_TIEM, d.get("so_hop_dong") or ""),
		message=_tk.khung("Phiếu thanh toán hợp đồng", than, chan="khach", nhan="Hợp đồng"),
		attachments=[{"fname": tep["ten_file"], "fcontent": base64.b64decode(tep["b64"])}],
		reference_doctype=DT,
		reference_name=name,
		delayed=False,
		retry=2,
	)
	frappe.db.set_value(DT, name, {
		"email_gui_toi": toi, "email_gui_luc": now_datetime(),
	}, update_modified=False)
	frappe.db.commit()
	return {"ok": 1, "toi": toi}
