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
# Xâu phông cho thư điện tử, khai một nơi. Thư hiện trên máy NGƯỜI NHẬN nên
# phông của nó khác phông bản in. Xem vagabond/mau_chuan.py.
from vagabond.mau_chuan import PHONG_THU

# Bo mau va khuon thu nay lay tu MOT cho: vagabond/thu_khung.py (03/09/2026).
# Cac ten duoi day giu lai de cac tep khac dang import khong vo; viet moi thi
# goi thang thu_khung.
from vagabond import thu_khung as _tk

XANH = _tk.XANH
XANH_NHAT = _tk.KEM
XANH_DAM = _tk.XANH_DAM
CHU = _tk.MUC
VIEN = _tk.KE
LIEN_KET = _tk.LIEN_KET


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


def _doi_ve_app(lien_ket):
	"""Frappe dung ten mien goc cua site cho lien ket dat mat khau. Doi sang
	ten mien app de nhan vien luon o lai trong app dien thoai."""
	try:
		from urllib.parse import urlsplit

		p = urlsplit(lien_ket or "")
		if not p.path:
			return lien_ket
		return link_app() + p.path + (("?" + p.query) if p.query else "")
	except Exception:
		return lien_ket


def _lien_ket_dat_mat_khau(doc):
	"""Sinh lien ket dat mat khau roi doi ve ten mien app.

	Frappe v16 doi ten ham nay thanh `_reset_password`; ban cu ten
	`reset_password`. Do ca hai de khong vo khi nang cap.
	"""
	ham = getattr(doc, "_reset_password", None) or getattr(doc, "reset_password", None)
	if not ham:
		frappe.throw("Không sinh được liên kết đặt mật khẩu.")
	return _doi_ve_app(ham())


def _nut_xanh(dia_chi, chu):
	"""Nut chinh. Giu ten cu cho cac cho dang goi."""
	return _tk.nut(dia_chi, chu, goc_anh=_tk.goc_anh())


def _nut_vien(dia_chi, chu):
	"""Nut phu."""
	return _tk.nut(dia_chi, chu, phu=True, goc_anh=_tk.goc_anh())


def _buoc(so, tieu_de, noi_dung):
	"""Mot buoc danh so trong vong tron robin egg."""
	goc = _tk.goc_anh()
	return (
		'<tr><td style="padding:0 0 16px">'
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%%">'
		'<tr><td width="36" valign="top">'
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
		'<td width="26" height="26" align="center" background="%s" bgcolor="%s" '
		'style="border-radius:13px;font-family:' + PHONG_THU + ';font-size:13px;'
		'font-weight:bold;color:%s">%s</td></tr></table></td>'
		'<td style="font-family:' + PHONG_THU + ';font-size:14px;line-height:1.65;color:%s">'
		'<b>%s</b><br>%s</td></tr></table></td></tr>'
	) % (_tk._anh(goc, _tk.ANH_LOT_XANH), XANH, XANH_DAM, so, CHU, tieu_de, noi_dung)


def thu_moi_html(ten, link_dat_mat_khau, dia_chi_app):
	"""Dung noi dung thu moi. Tach rieng de xem truoc duoc ma khong phai gui."""
	than = (
		_tk.doan("Chào <b>%s</b>," % _tk.h(ten or ""))
		+ _tk.doan(
			"Anh chị đã có tài khoản trên <b>app quản lý nội bộ của công ty</b>. "
			"App chạy thẳng trên <b>điện thoại</b>, không cần cài đặt gì, chỉ cần làm ba bước dưới đây.",
			cach=18,
		)
		+ '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">'
		+ _buoc(1, "Đặt mật khẩu",
			"Bấm nút bên dưới, gõ mật khẩu mới hai lần rồi lưu lại. Nhớ mật khẩu này để đăng nhập app.")
		+ '<tr><td style="padding:0 0 22px">%s</td></tr>' % _nut_vien(link_dat_mat_khau, "Đặt mật khẩu")
		+ _buoc(2, "Mở app trên điện thoại",
			"Bấm nút xanh bên dưới, đăng nhập bằng email và mật khẩu vừa đặt.")
		+ '<tr><td style="padding:0 0 22px">%s</td></tr>' % _nut_xanh(dia_chi_app, "Mở app")
		+ _buoc(3, "Gắn app ra màn hình chính",
			"iPhone: bấm nút Chia sẻ ở thanh dưới rồi chọn Thêm vào MH chính. "
			"Android: bấm dấu ba chấm góc trên rồi chọn Thêm vào màn hình chính. "
			"Từ lần sau chỉ cần bấm biểu tượng như một app bình thường.")
		+ "</table>"
		+ _tk.o_kem(
			"Đăng nhập bằng chính <b>địa chỉ email này</b> và mật khẩu anh chị vừa đặt. "
			"App dùng trên điện thoại là đủ, không cần mở trên máy tính.",
			goc_anh=_tk.goc_anh(),
		)
	)
	return _tk.khung("Tài khoản app của anh chị đã sẵn sàng", than, chan="nhan_vien", nhan="Chào mừng")


class NguoiDung(User):
	"""Chi thay doi thu chao mung, con lai giu nguyen cua Frappe."""

	def send_welcome_mail_to_user(self):
		try:
			lien_ket = _lien_ket_dat_mat_khau(self)
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
			lien_ket = _lien_ket_dat_mat_khau(doc)
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


def _khung_thu(tieu_de, than, nut="", chan="nhan_vien", nhan=""):
	"""Khung thu dung chung. Giu ten cu; than thu la vagabond/thu_khung.py.

	Mac dinh chan thu NHAN VIEN vi cac cho goi cu deu la thu cho nguoi trong
	cong ty. Thu cho khach hay nha cung cap phai truyen chan= cho dung.
	"""
	return _tk.khung(tieu_de, than, nut_html=nut, chan=chan, nhan=nhan)


def _o_nhat(noi_dung):
	return _tk.o_kem(noi_dung, goc_anh=_tk.goc_anh())


def _tien(v):
	try:
		return "{:,.0f}".format(float(v or 0)).replace(",", ".")
	except Exception:
		return "0"


def thu_phan_cong_html(ten, doc):
	"""Bao shipper vua duoc giao mot don. Ngan gon, mo app la thay."""
	h = frappe.utils.escape_html
	dong = [
		"<b>%s</b> - %s" % (h(doc.ma_don or doc.name), h(doc.khach or "")),
		h(doc.dia_chi or ""),
	]
	if doc.nguoi_nhan or doc.sdt_nhan:
		dong.append("Người nhận: %s %s" % (h(doc.nguoi_nhan or ""), h(doc.sdt_nhan or "")))
	if doc.tag_gio:
		dong.append("Khung giờ: <b>%s</b>" % h(doc.tag_gio))
	if doc.tien_thu_ho:
		dong.append("Thu hộ (COD): <b>%s đ</b>" % _tien(doc.tien_thu_ho))
	if doc.ghi_chu_in:
		dong.append("Ghi chú: %s" % h(doc.ghi_chu_in))
	than = (
		"<p style='margin:0 0 14px'>Chào <b>%s</b>, anh chị vừa được giao một đơn mới.</p>%s"
	) % (h(ten or ""), _o_nhat("<br>".join(dong)))
	return _khung_thu("Có đơn mới cho anh chị", than, _nut_xanh(link_app(), "Mở app xem đơn"), nhan="Giao hàng")


def thu_tai_xe_huy_html(doc):
	"""Bao sales rang tai xe app ngoai da huy, don dang cho phan cong lai."""
	h = frappe.utils.escape_html
	dong = [
		"<b>%s</b> - %s" % (h(doc.ma_don or doc.name), h(doc.khach or "")),
		h(doc.dia_chi or ""),
	]
	if doc.tag_gio:
		dong.append("Khung giờ: <b>%s</b>" % h(doc.tag_gio))
	if doc.tien_thu_ho:
		dong.append("Thu hộ (COD): <b>%s đ</b>" % _tien(doc.tien_thu_ho))
	than = (
		"<p style='margin:0 0 14px'>Tài xế bên app ngoài đã huỷ đơn này. "
		"Hệ thống đã gỡ mã đặt xe và trả vận đơn về <b>Chờ giao</b>, "
		"nhờ anh chị phân công lại giúp.</p>%s"
	) % _o_nhat("<br>".join(dong))
	return _khung_thu("Tài xế huỷ đơn, cần phân công lại", than,
		_nut_xanh(link_app(), "Mở màn Vận đơn"), chan="noi_bo", nhan="Giao hàng")


CONG_TY = "CÔNG TY TNHH PATISSERIE VAGABOND"


@frappe.whitelist()
def khoi_dong():
	"""Du lieu nen app nhan vien can luc mo: vai tro, kho, nhom hang.

	Truoc day app tu doc ba bang nay bang quyen cua chinh nguoi dung. Vai
	Shipper khong co quyen doc Warehouse, Item Group va User nen ca ba loi
	quyen mot luc, man hinh chinh treo mai o dong ho cat. Gom lai mot loi
	goi chay bang quyen he thong, chi tra ve ten - khong co so lieu nhay cam.
	"""
	if frappe.session.user in ("Guest", "", None):
		frappe.throw("Chưa đăng nhập.")
	kho = frappe.get_all(
		"Warehouse",
		filters={"is_group": 0, "disabled": 0, "company": CONG_TY},
		pluck="name",
		order_by="name",
		limit_page_length=200,
	)
	nhom = frappe.get_all(
		"Item Group",
		fields=["name", "parent_item_group", "is_group", "custom_bep_phu_trach"],
		order_by="name",
		limit_page_length=0,
	)
	return {"vai": frappe.get_roles(), "kho": kho, "nhom": nhom}
