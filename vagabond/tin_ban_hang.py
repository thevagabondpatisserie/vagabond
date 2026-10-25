# -*- coding: utf-8 -*-
"""v611: tin Zalo cho hoá đơn bán và tiền về tài khoản công ty.

Anh Việt 25/10/2026 (duyệt danh sách tin cùng ngày):
  - bh_thong_tin_hd_sai: đơn không ghi sổ được vì m-invoice từ chối thông tin
    người mua. Ca gốc: bill Pancake 95914 nằm nháp ba ngày vì email nhận hoá
    đơn có dấu gạch dưới ở đầu, máy chỉ ghi Error Log, không ai biết. Tin vào
    nhóm Bán hàng & Sales để Sales sửa ngay.
  - kt_tien_chua_gan: 08:00 mỗi sáng, khoản tiền vào tài khoản chính công ty
    quá 24 giờ mà chưa thuộc đơn hay phiếu nào (ca TCVEHQHG: khách chuyển
    thẳng vào MB 31561568, hai ngày không ai gắn).

Phần THUẦN tách riêng để kiểm thử không cần site. Phần chạm hệ nuốt lỗi và ghi
Error Log: tin báo không bao giờ làm hỏng việc ghi sổ.
"""

import re

import frappe
from frappe.utils import add_days, add_to_date, flt, now_datetime, nowdate

from vagabond import kenh_zalo

DAU_LOI_MINVOICE = "Chưa tạo được hoá đơn Chờ ký trên m-invoice"
# Chữ m-invoice dùng khi chê thông tin người mua (đọc trên Error Log site thật).
DAU_THONG_TIN_SAI = ("không hợp lệ", "khong hop le", "invalid", "email", "mã số thuế", "ma so thue", "mst",
	"tên người mua", "ten nguoi mua", "địa chỉ", "dia chi")
GIO_CHUA_GAN = 24
NGAY_XET_TIEN = 14
TOI_DA_DONG_TIEN = 10
RE_DON_PANCAKE = re.compile(r"S\d+O(\d+)T", re.IGNORECASE)


# ----------------------------------------------------------------- THUẦN


def tien(x):
	return "{:,.0f}".format(round(flt(x))).replace(",", ".") + " đ"


def chi_tiet_hd_sai(loi):
	"""Phần m-invoice chê thông tin người mua, rỗng nếu lỗi ghi sổ là chuyện khác.

	Lỗi có dạng: "... Chưa tạo được hoá đơn Chờ ký trên m-invoice ... Chi tiết:
	['HDB-26-10-04205: Mã chưa rõ 9999 [_quynhntm@ocb.com.vn] địa chỉ email
	không hợp lệ Nội dung: ...']". Lỗi mạng, hết số, mất kết nối không phải
	việc của Sales nên không báo ở đây."""
	s = str(loi or "")
	if DAU_LOI_MINVOICE not in s:
		return ""
	ct = s.split("Chi tiết:", 1)[1] if "Chi tiết:" in s else ""
	ct = re.sub(r"^[\s\[\]'\"]+|[\s\[\]'\"]+$", "", ct)
	ct = re.sub(r"^[A-Z]{2,5}-\d{2}-\d{2}-\d+:\s*", "", ct)
	ct = re.sub(r"Mã chưa rõ \d+\s*", "", ct)
	ct = re.split(r"\s*Nội dung:", ct)[0].strip()
	thuong = ct.lower()
	if not ct or not any(d in thuong for d in DAU_THONG_TIN_SAI):
		return ""
	return ct[:240]


def soan_hd_sai(d, chi_tiet):
	"""(tiêu đề, dòng) của tin thông tin hoá đơn sai. d: các ô của hoá đơn bán."""
	ma = d.get("custom_pancake_display_id") or d.get("name")
	dong = ["Đơn %s (%s), %s, chưa ghi sổ" % (ma, d.get("name"), tien(d.get("grand_total")))]
	nguoi = (d.get("vgb_xhd_ten") or "").strip()
	if nguoi:
		dong.append("Người mua: %s%s" % (nguoi, (" (MST %s)" % d.get("vgb_xhd_mst")) if d.get("vgb_xhd_mst") else ""))
	dong.append("m-invoice báo: %s" % chi_tiet)
	dong.append("Sales mở bill, sửa ở Thông tin xuất hoá đơn; máy tự ghi sổ lại ở lượt sau.")
	return "Thông tin xuất hoá đơn sai, đơn chưa ghi sổ", dong


def don_pancake_trong(mo_ta):
	"""Các số đơn Pancake mang mạch S<shop>O<đơn>T trong nội dung sao kê."""
	return set(RE_DON_PANCAKE.findall(str(mo_ta or "")))


def loc_tien_chua_gan(gds, co_chu, don_co_bill):
	"""THUẦN: khoản tiền vào tài khoản chính chưa thuộc chứng từ nào, lớn trước.

	gds: [{"ten","tien","ngay","mo_ta","tk_cty"}]; co_chu: {tên dòng: ai giữ};
	don_co_bill: các số đơn Pancake đã có hoá đơn bán (dòng mang đơn đó coi như
	có chủ, như đơn 95914 chuyển thẳng tài khoản công ty)."""
	ra = []
	for g in gds or []:
		if not g.get("tk_cty") or flt(g.get("tien")) <= 0 or co_chu.get(g.get("ten")):
			continue
		if don_pancake_trong(g.get("mo_ta")) & set(don_co_bill or ()):
			continue
		ra.append(g)
	ra.sort(key=lambda g: (-flt(g.get("tien")), str(g.get("ten"))))
	return ra


def dong_tien_chua_gan(ds, toi_da=TOI_DA_DONG_TIEN):
	"""THUẦN: mỗi khoản một dòng "dd/mm: 1.875.000 đ, nội dung rút gọn"."""
	ra = []
	for g in (ds or [])[:toi_da]:
		nd = re.sub(r"\s+", " ", str(g.get("mo_ta") or "")).strip()[:60]
		ngay = str(g.get("ngay") or "")[:10]
		ngay = "%s/%s" % (ngay[8:10], ngay[5:7]) if len(ngay) == 10 else ngay
		ra.append("%s: %s%s" % (ngay, tien(g.get("tien")), (", " + nd) if nd else ""))
	if len(ds or []) > toi_da:
		ra.append("+%d khoản khác" % (len(ds) - toi_da))
	return ra


# ------------------------------------------------------------- chạm Frappe


def _url(duong):
	try:
		return frappe.utils.get_url(duong)
	except Exception:
		return duong


def bao_thong_tin_hd_sai(si, loi):
	"""Gọi từ ban_hang._ghi_so_mot_don SAU khi đã rollback lượt ghi sổ hỏng.
	Một đơn một tin mỗi ngày; người gọi commit để tin còn lại."""
	try:
		ct = chi_tiet_hd_sai(loi)
		if not ct:
			return
		d = si.as_dict() if hasattr(si, "as_dict") else dict(si)
		tieu_de, dong = soan_hd_sai(d, ct)
		kenh_zalo.bao("canh_bao", "hoa_don", tieu_de, dong, link=_url("/app/sales-invoice/%s" % d.get("name")),
			khoa="hd-sai:%s:%s" % (d.get("name"), nowdate()), ma_tin="bh_thong_tin_hd_sai")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		frappe.log_error(frappe.get_traceback(), "tin_ban_hang: thong tin hd sai")


def nhac_tien_chua_gan():
	"""Lịch 08:00: khoản tiền vào tài khoản chính công ty quá GIO_CHUA_GAN giờ chưa thuộc chứng từ nào."""
	try:
		from vagabond import ban_hang, doi_soat_ck

		moc = add_to_date(now_datetime(), hours=-GIO_CHUA_GAN)
		rows = frappe.db.sql(
			"""select name, description, reference_number, deposit, date, unallocated_amount
			from `tabBank Transaction`
			where docstatus < 2 and deposit > 0 and date >= %s and creation <= %s
			and ifnull(unallocated_amount, deposit) > 1""",
			(add_days(nowdate(), -NGAY_XET_TIEN), moc), as_dict=True)
		if not rows:
			return
		bang = doi_soat_ck.bang_dau_he()
		gds = []
		for g in rows:
			mo_ta = "%s %s" % (g.description or "", g.reference_number or "")
			khoa, _nhan = doi_soat_ck.thuoc_tk(mo_ta, bang)
			gds.append({"ten": g.name, "tien": flt(g.deposit), "ngay": str(g.date), "mo_ta": g.description or "",
				"tham_chieu": (g.reference_number or "").strip(), "tk_cty": not khoa, "da_phan_bo": 0.0})
		cty = [g for g in gds if g["tk_cty"]]
		if not cty:
			return
		co_chu = ban_hang._gd_co_chu_toan_he([{"ten": g["ten"], "mo_ta": g["mo_ta"], "tham_chieu": g["tham_chieu"],
			"da_phan_bo": 0.0} for g in cty])
		don = sorted(set().union(*[don_pancake_trong(g["mo_ta"]) for g in cty]))
		don_co_bill = set()
		if don:
			for r in frappe.get_all("Sales Invoice", filters={"custom_pancake_display_id": ["in", don], "docstatus": ["<", 2]},
					fields=["custom_pancake_display_id"], limit_page_length=0):
				don_co_bill.add(str(r.custom_pancake_display_id))
		ds = loc_tien_chua_gan(cty, co_chu or {}, don_co_bill)
		if not ds:
			return
		dong = ["%d khoản, tổng %s, vào tài khoản chính quá %d giờ" % (len(ds), tien(sum(flt(g["tien"]) for g in ds)), GIO_CHUA_GAN)]
		dong += dong_tien_chua_gan(ds)
		dong.append("Kế toán mở Đối soát chuyển khoản hoặc Đối chiếu ngân hàng để gắn cho đúng đơn, phiếu.")
		kenh_zalo.bao("viec", "cong_no", "Tiền vào tài khoản công ty chưa gắn chứng từ", dong,
			link=_url("/doi-soat-chuyen-khoan"), khoa="tien-chua-gan:%s" % nowdate(), ma_tin="kt_tien_chua_gan")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tin_ban_hang: tien chua gan")
