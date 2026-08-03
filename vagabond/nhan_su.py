"""Thu moi nhan vien vao app dien thoai.

Anh Viet 03/08/2026: thu moi mac dinh cua Frappe dan nguoi ta vao ban quan tri
tren may tinh, shipper bam vao lac duong. Tu nay thu moi CHI noi ve app dien
thoai: dat mat khau, mo app, gan ra man hinh chinh. Khong nhac gi toi desk.

Cach hoat dong: doctype User duoc thay bang lop NguoiDung ben duoi (khai o
hooks.override_doctype_class), chi ghi de dung ham gui thu chao mung.
"""

import json

import frappe
from frappe.core.doctype.user.user import User
from frappe.utils import get_url

from vagabond.lib import cfg

# Bo mau nhan dien dung chung voi mau thu PO gui nha cung cap (xem
# claude/erpnext-email-va-mau-thu-po.md). Cac mang mau thuong hieu deu lot
# anh nen, vi Gmail che do toi tu dao mau nhung mang sang thuan CSS.
SITE_ANH = "https://vagabond.s.frappe.cloud"
ANH_DAU_THU = SITE_ANH + "/files/vgb_email_header.png"
ANH_NEN_XANH = SITE_ANH + "/files/vgb_bg_robinegg.png"
XANH = "#50DBF2"          # robin egg dac
XANH_NHAT = "#E4F9FD"     # robin egg nhat
XANH_DAM = "#05323C"      # chu tren nen xanh
CHU = "#22333B"
VIEN = "#CDEBF2"
LIEN_KET = "#0B7C93"


def link_app():
	"""Dia chi app cho nhan vien. Uu tien o cai dat (de doi sang ten mien
	rieng khi DNS xong) roi moi den dia chi cua site."""
	try:
		c = cfg()
		if (c.get("link_app") or "").strip():
			return c.get("link_app").strip().rstrip("/")
	except Exception:
		pass
	return get_url().rstrip("/")


def _nut_xanh(dia_chi, chu):
	"""Nut chinh mau robin egg, lot anh nen de khong bi Gmail dao mau."""
	return (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto">'
		'<tr><td align="center" background="%s" bgcolor="%s" style="border-radius:10px">'
		'<a href="%s" target="_blank" style="display:inline-block;padding:15px 40px;'
		'font-family:Arial,Helvetica,sans-serif;font-size:17px;font-weight:bold;letter-spacing:.3px;'
		'color:%s;text-decoration:none">%s</a>'
		"</td></tr></table>"
	) % (ANH_NEN_XANH, XANH, dia_chi, XANH_DAM, chu)


def _nut_vien(dia_chi, chu):
	"""Nut phu: nen trang, vien xanh dam."""
	return (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto">'
		'<tr><td align="center" bgcolor="#FFFFFF" style="border:2px solid %s;border-radius:10px">'
		'<a href="%s" target="_blank" style="display:inline-block;padding:13px 38px;'
		'font-family:Arial,Helvetica,sans-serif;font-size:16px;font-weight:bold;'
		'color:%s;text-decoration:none">%s</a>'
		"</td></tr></table>"
	) % (XANH_DAM, dia_chi, XANH_DAM, chu)


def _buoc(so, tieu_de, noi_dung):
	return (
		'<tr><td style="padding:0 0 16px">'
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%">'
		'<tr><td width="34" valign="top">'
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
		'<td width="26" height="26" align="center" background="%s" bgcolor="%s" '
		'style="border-radius:13px;font-family:Arial,Helvetica,sans-serif;font-size:13px;'
		'font-weight:bold;color:%s">%s</td></tr></table></td>'
		'<td style="font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.65;color:%s">'
		'<b style="color:%s">%s</b><br>%s</td></tr></table></td></tr>'
	) % (ANH_NEN_XANH, XANH, XANH_DAM, so, CHU, XANH_DAM, tieu_de, noi_dung)


def thu_moi_html(ten, link_dat_mat_khau, dia_chi_app):
	"""Dung noi dung thu moi. Tach rieng de xem truoc duoc ma khong phai gui."""
	return (
		'<div style="margin:0;padding:0;background:#F2FAFC">\n'
		'<table role="presentation" width="100%%" cellpadding="0" cellspacing="0" border="0"><tr>'
		'<td align="center" style="padding:18px 8px">\n'
		'<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" '
		'style="width:600px;max-width:600px;background:#FFFFFF;border:1px solid %(vien)s">\n'
		'<tr><td><img src="%(anh_dau)s" width="600" alt="The Vagabond Patisserie" '
		'style="display:block;width:100%%;height:auto;border:0"></td></tr>\n'
		'<tr><td style="padding:26px 30px 6px;font-family:Arial,Helvetica,sans-serif;'
		'font-size:14px;line-height:1.65;color:%(chu)s">\n'
		'<p style="margin:0 0 14px">Chào <b style="color:%(dam)s">%(ten)s</b>,</p>\n'
		'<p style="margin:0 0 4px">Anh chị đã có tài khoản trên <b>app quản lý nội bộ của công ty</b>. '
		'App chạy thẳng trên <b>điện thoại</b>, không cần cài đặt gì, chỉ cần làm ba bước dưới đây.</p>\n'
		'</td></tr>\n'
		'<tr><td style="padding:18px 30px 0">\n'
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%">\n'
		'%(b1)s<tr><td style="padding:0 0 20px">%(nut1)s</td></tr>\n'
		'%(b2)s<tr><td style="padding:0 0 20px">%(nut2)s</td></tr>\n'
		'%(b3)s'
		'</table>\n</td></tr>\n'
		'<tr><td style="padding:2px 30px 24px">\n'
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%">'
		'<tr><td bgcolor="%(nhat)s" style="padding:13px 16px;font-family:Arial,Helvetica,sans-serif;'
		'font-size:13.5px;line-height:1.6;color:%(dam)s">'
		'Đăng nhập bằng chính <b>địa chỉ email này</b> và mật khẩu anh chị vừa đặt. '
		'App dùng trên điện thoại là đủ, không cần mở trên máy tính.</td></tr></table>\n'
		'</td></tr>\n'
		'<tr><td background="%(nen_xanh)s" bgcolor="%(xanh)s" '
		'style="padding:12px 30px;font-family:Arial,Helvetica,sans-serif;font-size:12px;'
		'line-height:1.7;color:%(dam)s;text-align:center">'
		'The Vagabond P&acirc;tisserie - 307/1 Nguyễn Văn Trỗi &amp; 9 Trần Cao Vân, TP. Hồ Chí Minh<br>'
		'Cần hỗ trợ về app hãy nhắn số anh Việt (0901486556, Zalo)</td></tr>\n'
		"</table>\n</td></tr></table></div>"
	) % {
		"vien": VIEN,
		"anh_dau": ANH_DAU_THU,
		"chu": CHU,
		"dam": XANH_DAM,
		"nhat": XANH_NHAT,
		"xanh": XANH,
		"nen_xanh": ANH_NEN_XANH,
		"ten": frappe.utils.escape_html(ten or ""),
		"b1": _buoc(
			1, "Đặt mật khẩu",
			"Bấm nút bên dưới, gõ mật khẩu mới hai lần rồi lưu lại. Nhớ mật khẩu này để đăng nhập app.",
		),
		"nut1": _nut_vien(link_dat_mat_khau, "Đặt mật khẩu"),
		"b2": _buoc(
			2, "Mở app trên điện thoại",
			"Bấm nút xanh bên dưới, đăng nhập bằng email và mật khẩu vừa đặt.",
		),
		"nut2": _nut_xanh(dia_chi_app, "Mở app"),
		"b3": _buoc(
			3, "Gắn app ra màn hình chính",
			"iPhone: bấm nút Chia sẻ ở thanh dưới rồi chọn Thêm vào MH chính. "
			"Android: bấm dấu ba chấm góc trên rồi chọn Thêm vào màn hình chính. "
			"Từ lần sau chỉ cần bấm biểu tượng như một app bình thường.",
		),
	}


class NguoiDung(User):
	"""Chi thay doi thu chao mung, con lai giu nguyen cua Frappe."""

	def send_welcome_mail_to_user(self):
		try:
			lien_ket = self.reset_password()
			frappe.sendmail(
				recipients=self.email,
				subject="Tài khoản app The Vagabond Pâtisserie",
				message=thu_moi_html(self.full_name or self.first_name or "", lien_ket, link_app()),
				delayed=False,
				retry=3,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "vagabond: gui thu moi loi")
			super().send_welcome_mail_to_user()


@frappe.whitelist()
def xem_truoc_thu_moi():
	"""Tra ve HTML thu moi voi du lieu gia de duyet mau, khong gui cho ai."""
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản trị xem trước được.")
	return thu_moi_html("Trương Minh Lâm", link_app() + "/update-password?key=xem-truoc", link_app())


@frappe.whitelist()
def moi_nhan_su(users, that_su=0):
	"""Gui lai thu moi cho cac tai khoan da tao.

	that_su = 0: chi thu thu, khong gui - tra ve danh sach se gui cho ai.
	that_su = 1: gui that.
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản trị gửi lời mời được.")
	if isinstance(users, str):
		users = json.loads(users)
	ra = []
	for u in users or []:
		d = frappe.db.get_value("User", u, ["name", "full_name", "enabled"], as_dict=True)
		if not d:
			ra.append({"user": u, "ket_qua": "không thấy tài khoản"})
			continue
		if not d.enabled:
			ra.append({"user": u, "ket_qua": "tài khoản đang tắt, bỏ qua"})
			continue
		if not frappe.utils.cint(that_su):
			ra.append({"user": u, "ten": d.full_name, "ket_qua": "sẽ gửi"})
			continue
		try:
			doc = frappe.get_doc("User", u)
			lien_ket = doc.reset_password()
			frappe.sendmail(
				recipients=doc.email,
				subject="Tài khoản app The Vagabond Pâtisserie",
				message=thu_moi_html(doc.full_name or "", lien_ket, link_app()),
				delayed=False,
				retry=3,
			)
			ra.append({"user": u, "ten": d.full_name, "ket_qua": "đã gửi"})
		except Exception:
			frappe.log_error(frappe.get_traceback(), "vagabond: gui lai thu moi loi")
			ra.append({"user": u, "ten": d.full_name, "ket_qua": "lỗi, xem Error Log"})
	return ra


@frappe.whitelist()
def ds_nhan_su_theo_vai(vai="Shipper"):
	"""Danh sach tai khoan dang bat theo vai tro, kem ten day du."""
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản trị xem được.")
	rows = frappe.get_all("Has Role", filters={"role": vai, "parenttype": "User"}, fields=["parent"])
	ra = []
	for r in rows:
		if r.parent in ("Administrator", "Guest"):
			continue
		d = frappe.db.get_value("User", r.parent, ["full_name", "enabled"], as_dict=True)
		if d and d.enabled:
			ra.append({"user": r.parent, "ten": d.full_name})
	return sorted(ra, key=lambda x: x["ten"] or "")
