"""Tu dung san ban ghi Hop thu (Email Account) cho bao gia.

Vi sao co tep nay
-----------------
Anh Viet 15/08/2026: *"Anh khong nho thao tac tao Email Account trong
Frappe Desk nam o dau. Do do, thay vi bat anh tao tay, em hay viet mot
patch script (chay qua after_migrate) de he thong tu dong sinh ra ban ghi
Email Account cho sales@thevagabondpatisserie.com. Hay dien san moi cau
hinh can thiet. Em chi viec de trong truong 'Mat khau'."*

Ban dau tep nay chon cung thong so Google Workspace, vi anh Viet noi toi
"App Password cua Google". SAI. Doc hien trang tren chinh he ngay
16/08/2026 thi hai hop thu dang gui that deu di qua:

    smtp.mail  mail.thevagabondpatisserie.com  cong 465  SSL
    imap       mail.thevagabondpatisserie.com  cong 993  SSL

Tuc ten mien nay chay tren MAY CHU THU RIENG chu khong phai Google. Dan
mat khau vao mot ban ghi tro toi smtp.gmail.com thi Frappe thu ket noi va
hong, nen mat khau khong bao gio luu duoc.

Bai hoc va cung la cach lam moi cua tep nay: KHONG doan thong so may chu.
Doc mot hop thu CUNG TEN MIEN dang gui duoc tren chinh he nay roi chep
thong so cua no. He nao doi nha cung cap thu, patch tu di theo.

BA DIEU TEP NAY KHONG LAM, va deu la co y
------------------------------------------
Mot. KHONG dat mat khau. Em khong nhap khoa hay mat khau ho ai, ke ca khi
anh dua tan tay; do la ranh gioi em giu co dinh. Va neu chon cung mat khau
vao ma nguon thi no nam trong GitHub vinh vien.

Hai. KHONG tu bat gui di (enable_outgoing). Do la quyet dinh cua nguoi
dung, va hop thu chua co mat khau ma bat gui thi Frappe se thu gui roi nem
loi xac thuc vao mat moi nguoi.

Ba. KHONG ghi de len o nguoi dung da tu dat. Chi sua lai dung nhung o con
trong, hoac nhung o dang mang DUNG gia tri sai ma chinh patch nay tung ghi
vao - tuc di don rac cua chinh minh, khong dung vao lua chon cua ai.
"""

import frappe

TEN = "Sales The Vagabond"
DIA_CHI = "sales@thevagabondpatisserie.com"

# Thong so may chu mac dinh, CHI dung khi khong tim duoc hop thu nao cung
# ten mien dang chay tren he de hoc theo.
MAC_DINH = {
	"smtp_server": "smtp.gmail.com",
	"smtp_port": 587,
	"use_tls": 1,
	"use_ssl_for_outgoing": 0,
	"email_server": "imap.gmail.com",
	"use_imap": 1,
	"incoming_port": 993,
	"use_ssl": 1,
}

# Nhung gia tri chinh patch nay tung ghi nham hom 15/08/2026. Gap dung
# chung thi duoc phep sua lai; gap gia tri khac thi de yen vi do la nguoi
# dung tu dat.
RAC_CU = {
	"smtp_server": "smtp.gmail.com",
	"smtp_port": "587",
	"email_server": "imap.gmail.com",
}

O_MAY_CHU = (
	"smtp_server", "smtp_port", "use_tls", "use_ssl_for_outgoing",
	"email_server", "use_imap", "incoming_port", "use_ssl",
)


def _ten_mien(dia_chi):
	"""Phan sau dau a coi. THUAN."""
	return str(dia_chi or "").rsplit("@", 1)[-1].strip().lower()


def _thong_so():
	"""Hoc thong so may chu tu mot hop thu cung ten mien dang gui duoc.

	Khong co thi tra ve bo mac dinh. Doc hien trang chu khong doan.
	"""
	mien = _ten_mien(DIA_CHI)
	for o in frappe.get_all(
		"Email Account",
		filters={"enable_outgoing": 1},
		fields=["name", "email_id"] + list(O_MAY_CHU),
		order_by="modified desc",
		limit_page_length=0,
	):
		if _ten_mien(o.get("email_id")) != mien:
			continue
		if not o.get("smtp_server"):
			continue
		return {f: o.get(f) for f in O_MAY_CHU if o.get(f) not in (None, "")}
	return dict(MAC_DINH)


def _khai():
	ra = {
		"doctype": "Email Account",
		"email_account_name": TEN,
		"email_id": DIA_CHI,
		# De trong: dat "GMail" se bat Frappe ep bo thong so cua Google len,
		# ma ten mien nay khong chay tren Google.
		"service": "",
		"domain": "",
		"enable_outgoing": 0,
		"default_outgoing": 0,
		"always_use_account_email_id_as_sender": 1,
		"always_use_account_name_as_sender_name": 1,
		"send_unsubscribe_message": 0,
		# Nhan ve de tam tat. Bat len thi Frappe bat dau keo thu that; de
		# nguoi dung tu quyet khi nao san sang.
		"enable_incoming": 0,
		# Thu khach tra loi bao gia chui ve dung ho so chung tu, khong nam
		# lac o hop thu ca nhan cua Loan Anh.
		"append_to": "Bao Gia Ban Hang",
		"create_contact": 0,
		"enable_automatic_linking": 1,
	}
	ra.update(_thong_so())
	return ra


def dung():
	"""Dung hoac va lai hop thu sales@. Goi tu after_migrate, lap lai duoc."""
	cu = frappe.db.get_value("Email Account", {"email_id": DIA_CHI}, "name")
	if cu:
		_don_rac_cu(cu)
		return cu

	doc = frappe.get_doc(_khai())
	# Frappe kiem cau hinh bang cach thu ket noi that khi luu. Hop thu chua
	# co mat khau nen phep thu do chac chan hong; hai co nay bao no bo qua.
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_validate = True
	doc.insert(ignore_permissions=True)
	doc.add_comment(
		"Comment",
		"Máy dựng sẵn hộp thư gửi báo giá, thông số lấy theo hộp thư đang "
		"chạy của cùng tên miền. Còn thiếu Mật khẩu: dán vào ô Password "
		"rồi tích Enable Outgoing và bấm Lưu là chạy.",
	)
	return doc.name


def _don_rac_cu(ten):
	"""Dien o con trong, va sua lai dung nhung o mang gia tri sai cua patch cu.

	KHONG dung toi enable_outgoing hay default_outgoing: hai o do la quyet
	dinh cua nguoi dung.
	"""
	doc = frappe.get_doc("Email Account", ten)
	dung_ts = _thong_so()
	doi = {}
	for f in O_MAY_CHU:
		gt = doc.get(f)
		la_rac = f in RAC_CU and str(gt or "") == str(RAC_CU[f])
		if (gt in (None, "") or la_rac) and dung_ts.get(f) not in (None, ""):
			if str(gt or "") != str(dung_ts[f]):
				doi[f] = dung_ts[f]
	# "GMail" ep Frappe ap bo thong so cua Google de len; go ra.
	if (doc.get("service") or "") == "GMail":
		doi["service"] = ""
	if doi:
		frappe.db.set_value("Email Account", ten, doi, update_modified=False)
		doc.add_comment(
			"Comment",
			"Máy sửa lại thông số máy chủ cho khớp hộp thư đang chạy của "
			"cùng tên miền: %s" % ", ".join(sorted(doi)),
		)


@frappe.whitelist()
def tinh_trang():
	"""Hop thu bao gia da san sang chua. CHI DOC, khong bao gio tra mat khau."""
	if not (set(frappe.get_roles()) & {"System Manager"}):
		frappe.throw("Chỉ quản trị hệ thống xem được tình trạng hộp thư.")
	o = frappe.db.get_value(
		"Email Account",
		{"email_id": DIA_CHI},
		["name", "enable_outgoing", "smtp_server", "smtp_port"],
		as_dict=True,
	)
	if not o:
		return {"co": 0, "viec": "Chưa có hộp thư. Chạy migrate một lần là máy dựng."}
	# get_password nem loi khi o mat khau con trong - do chinh la cau tra loi
	# can biet, nen bat lay chu khong de no noi len.
	try:
		co_mk = bool(
			frappe.get_doc("Email Account", o["name"]).get_password(
				"password", raise_exception=False
			)
		)
	except Exception:
		co_mk = False
	ra = {
		"co": 1, "ten": o["name"], "may_chu": o.get("smtp_server"),
		"cong": o.get("smtp_port"), "co_mat_khau": 1 if co_mk else 0,
		"bat_gui": 1 if o.get("enable_outgoing") else 0,
	}
	if not co_mk:
		ra["san_sang"] = 0
		ra["viec"] = (
			"Mở hộp thư %s trên Desk, dán Mật khẩu vào ô Password rồi bấm "
			"Lưu. Máy chủ đang đặt là %s cổng %s."
			% (o["name"], o.get("smtp_server"), o.get("smtp_port"))
		)
	elif not o.get("enable_outgoing"):
		ra["san_sang"] = 0
		ra["viec"] = "Đã có mật khẩu. Chỉ còn tích Enable Outgoing rồi bấm Lưu."
	else:
		ra["san_sang"] = 1
		ra["viec"] = ""
	return ra
