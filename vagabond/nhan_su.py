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

# Xanh robin egg - mau nut chinh trong thu moi
XANH = "#00c2cb"
XANH_DAM = "#00a3ab"
NAU = "#1f1c19"
NEN = "#f2efe9"


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


def _nut(dia_chi, chu, nen, mau_chu="#ffffff", vien=None):
	"""Nut bam trong email. Dung bang thay vi thẻ a co padding vi Outlook va
	mot so ung dung mail Viet Nam bo qua padding cua the a."""
	vien = vien or nen
	return (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 auto">'
		'<tr><td align="center" bgcolor="%s" style="border-radius:12px;border:1px solid %s">'
		'<a href="%s" target="_blank" style="display:inline-block;padding:15px 34px;'
		'font-family:Helvetica,Arial,sans-serif;font-size:17px;font-weight:700;letter-spacing:.3px;'
		'color:%s;text-decoration:none;border-radius:12px">%s</a>'
		"</td></tr></table>"
	) % (nen, vien, dia_chi, mau_chu, chu)


def _buoc(so, tieu_de, noi_dung):
	return (
		'<tr><td style="padding:0 0 18px">'
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%">'
		'<tr><td width="30" valign="top" style="padding-top:2px">'
		'<div style="width:24px;height:24px;border-radius:12px;background:%s;color:#fff;'
		'font:700 13px/24px Helvetica,Arial,sans-serif;text-align:center">%s</div></td>'
		'<td style="font:400 15px/1.6 Helvetica,Arial,sans-serif;color:#3d372f">'
		'<b style="color:%s">%s</b><br>%s</td></tr></table></td></tr>'
	) % (NAU, so, NAU, tieu_de, noi_dung)


def thu_moi_html(ten, link_dat_mat_khau, dia_chi_app):
	"""Dung noi dung thu moi. Tach rieng de xem truoc duoc ma khong phai gui."""
	return """<!DOCTYPE html>
<html lang="vi"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:24px 12px;background:#e9e5de">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%" style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid %(nau)s">
  <tr><td align="center" bgcolor="%(nen)s" style="padding:22px 20px;border-bottom:1.5px solid %(nau)s">
    <div style="font:700 20px/1.2 Georgia,'Times New Roman',serif;letter-spacing:2.5px;text-transform:uppercase;color:%(nau)s">The Vagabond P&acirc;tisserie</div>
    <div style="margin-top:6px;font:600 11px/1.4 Helvetica,Arial,sans-serif;letter-spacing:2px;text-transform:uppercase;color:#6b645b">App n&#7897;i b&#7897; c&#7911;a ti&#7879;m</div>
  </td></tr>

  <tr><td style="padding:26px 26px 6px;font:400 16px/1.65 Helvetica,Arial,sans-serif;color:#1f1c19">
    Ch&agrave;o <b>%(ten)s</b>,<br><br>
    Anh ch&#7883; &#273;&atilde; c&oacute; t&agrave;i kho&#7843;n tr&ecirc;n app c&#7911;a ti&#7879;m.
    App ch&#7841;y th&#7859;ng tr&ecirc;n <b>&#273;i&#7879;n tho&#7841;i</b>, kh&ocirc;ng c&#7847;n c&agrave;i &#273;&#7863;t g&igrave;, ch&#7881; c&#7847;n l&agrave;m ba b&#432;&#7899;c d&#432;&#7899;i &#273;&acirc;y.
  </td></tr>

  <tr><td style="padding:22px 26px 0">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%">
      %(b1)s
      <tr><td style="padding:0 0 22px">%(nut1)s</td></tr>
      %(b2)s
      <tr><td style="padding:0 0 22px">%(nut2)s</td></tr>
      %(b3)s
    </table>
  </td></tr>

  <tr><td style="padding:4px 26px 24px">
    <div style="background:%(nen)s;border-left:3px solid %(nau)s;padding:12px 14px;font:400 14px/1.6 Helvetica,Arial,sans-serif;color:#3d372f">
      &#272;&#259;ng nh&#7853;p b&#7857;ng ch&iacute;nh <b>&#273;&#7883;a ch&#7881; email n&agrave;y</b> v&agrave; m&#7853;t kh&#7849;u anh ch&#7883; v&#7915;a &#273;&#7863;t.
      App d&ugrave;ng tr&ecirc;n &#273;i&#7879;n tho&#7841;i l&agrave; &#273;&#7911;, kh&ocirc;ng c&#7847;n m&#7903; tr&ecirc;n m&aacute;y t&iacute;nh.
    </div>
  </td></tr>

  <tr><td align="center" bgcolor="%(nen)s" style="padding:14px 20px;border-top:1.5px solid %(nau)s;font:400 12px/1.7 Helvetica,Arial,sans-serif;color:#3d372f">
    <b style="color:%(nau)s">THE VAGABOND P&Acirc;TISSERIE</b><br>
    307/1 Nguy&#7877;n V&#259;n Tr&#7895;i &amp; 9 Tr&#7847;n Cao V&acirc;n<br>
    C&#7847;n gi&uacute;p g&igrave; th&igrave; nh&#7855;n qu&#7843;n l&yacute; tr&#7921;c ti&#7871;p gi&uacute;p ti&#7879;m nh&eacute;.
  </td></tr>
</table>
</body></html>""" % {
		"nau": NAU,
		"nen": NEN,
		"ten": frappe.utils.escape_html(ten or ""),
		"b1": _buoc(
			1, "Đặt mật khẩu",
			"Bấm nút bên dưới, gõ mật khẩu mới hai lần rồi lưu lại. Nhớ mật khẩu này để đăng nhập app.",
		),
		"nut1": _nut(link_dat_mat_khau, "Đặt mật khẩu", "#ffffff", NAU, NAU),
		"b2": _buoc(
			2, "Mở app trên điện thoại",
			"Bấm nút xanh bên dưới, đăng nhập bằng email và mật khẩu vừa đặt.",
		),
		"nut2": _nut(dia_chi_app, "Mở app", XANH, "#ffffff", XANH_DAM),
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
