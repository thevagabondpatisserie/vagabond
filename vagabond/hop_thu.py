"""Tu dung san ban ghi Hop thu (Email Account) cho bao gia.

Vi sao co tep nay
-----------------
Anh Viet 15/08/2026: *"Anh khong nho thao tac tao Email Account trong
Frappe Desk nam o dau. Do do, thay vi bat anh tao tay, em hay viet mot
patch script (chay qua after_migrate) de he thong tu dong sinh ra ban ghi
Email Account cho sales@thevagabondpatisserie.com. Hay dien san moi cau
hinh can thiet. Em chi viec de trong truong 'Mat khau'."*

Nen tep nay dung san ban ghi voi day du may chu, cong, ma hoa - dung thong
so Google Workspace - va DE TRONG o mat khau. Anh Viet vao dung ban ghi do,
dan Mat khau ung dung vao, bam Luu la chay.

BA DIEU TEP NAY KHONG LAM, va deu la co y
------------------------------------------
Mot. KHONG dat mat khau. Em khong nhap khoa hay mat khau ho ai, ke ca khi
anh dua tan tay; do la ranh gioi em giu co dinh. Va neu chon cung mat khau
vao ma nguon thi no nam trong GitHub vinh vien.

Hai. KHONG bat gui di ngay (enable_outgoing = 0). Hop thu chua co mat khau
ma bat gui thi Frappe se thu gui va nem loi xac thuc vao mat moi nguoi.
Ham nay tu bat len khi thay da co mat khau.

Ba. KHONG dung vao hop thu neu no da ton tai. Anh Viet co the da tu sua
cong hay may chu; ghi de len la pha cau hinh dang chay. Chi bo sung dung
nhung o con trong.
"""

import frappe

TEN = "Sales The Vagabond"
DIA_CHI = "sales@thevagabondpatisserie.com"

# Thong so Google Workspace. Cong 587 kem STARTTLS la duong Google khuyen
# dung; 465 kem SSL cung chay nhung mot so mang chan.
KHAI = {
	"doctype": "Email Account",
	"email_account_name": TEN,
	"email_id": DIA_CHI,
	"service": "GMail",
	"domain": "",
	# Gui di
	"enable_outgoing": 0,
	"smtp_server": "smtp.gmail.com",
	"smtp_port": 587,
	"use_tls": 1,
	"use_ssl_for_outgoing": 0,
	"default_outgoing": 0,
	"always_use_account_email_id_as_sender": 1,
	"always_use_account_name_as_sender_name": 1,
	"send_unsubscribe_message": 0,
	# Nhan ve. Bat san de thu khach tra loi bao gia chui ve dung ho so
	# chung tu, khong nam lac o hop thu ca nhan cua Loan Anh.
	"enable_incoming": 0,
	"email_server": "imap.gmail.com",
	"use_imap": 1,
	"incoming_port": 993,
	"use_ssl": 1,
	"append_to": "Bao Gia Ban Hang",
	"create_contact": 0,
	"enable_automatic_linking": 1,
}

# Nhung o duoc phep bo sung khi ban ghi DA co nhung o do con trong. Co y
# khong dua enable_outgoing va default_outgoing vao day: hai o do la quyet
# dinh cua nguoi dung, may khong tu bat.
BO_SUNG = (
	"smtp_server", "smtp_port", "use_tls", "email_server", "use_imap",
	"incoming_port", "use_ssl", "append_to",
	"always_use_account_email_id_as_sender",
	"always_use_account_name_as_sender_name",
)


def dung():
	"""Dung hoac va lai hop thu sales@. Goi tu after_migrate, lap lai duoc."""
	cu = frappe.db.get_value(
		"Email Account", {"email_id": DIA_CHI}, "name"
	)
	if cu:
		_bo_sung(cu)
		return cu

	doc = frappe.get_doc(dict(KHAI))
	# Frappe kiem cau hinh bang cach thu ket noi that khi luu. Hop thu chua
	# co mat khau nen phep thu do chac chan hong; hai co nay bao no bo qua.
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_validate = True
	doc.insert(ignore_permissions=True)
	doc.add_comment(
		"Comment",
		"Máy dựng sẵn hộp thư gửi báo giá. Còn thiếu Mật khẩu ứng dụng: "
		"dán vào ô Password rồi tích Enable Outgoing và bấm Lưu là chạy.",
	)
	return doc.name


def _bo_sung(ten):
	"""Chi dien vao nhung o CON TRONG. Khong dung vao o nguoi dung da dat."""
	doc = frappe.get_doc("Email Account", ten)
	doi = {}
	for f in BO_SUNG:
		if not doc.get(f) and KHAI.get(f):
			doi[f] = KHAI[f]
	if doi:
		frappe.db.set_value("Email Account", ten, doi, update_modified=False)


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
	if not co_mk:
		return {
			"co": 1, "ten": o["name"], "san_sang": 0,
			"viec": "Mở hộp thư %s trên Desk, dán Mật khẩu ứng dụng của "
					"Google vào ô Password, tích Enable Outgoing rồi bấm Lưu."
					% o["name"],
		}
	if not o.get("enable_outgoing"):
		return {
			"co": 1, "ten": o["name"], "san_sang": 0,
			"viec": "Đã có mật khẩu. Chỉ còn tích Enable Outgoing rồi bấm Lưu.",
		}
	return {"co": 1, "ten": o["name"], "san_sang": 1, "viec": ""}
