"""v562 (#410): bắn tin Zalo trên ERPNext thật: bảng cài đặt, sổ gửi, chống trùng.

Không gọi Zalo thật: thay `_gui_zalo` bằng hàm ghi lại. `commit`/`rollback`
của worker được thay bằng hàm rỗng để giữ savepoint của nen.py (không ghi
gì ra site). Không đổi Vagabond Settings thật: danh sách nhóm đưa thẳng vào.
"""
import uuid
from unittest.mock import patch

import frappe

from vagabond import kenh_zalo as kz
from vagabond.khung.kiem_that.nen import ca, dung, la


@ca("v562 Zalo: Cài đặt có đủ ô, bảng nhóm và sổ gửi đúng kiểu")
def _cau_truc():
	m = frappe.get_meta("Vagabond Settings")
	la("kiểu các ô", [m.get_field(f).fieldtype for f in ("zalo_bot_bat", "zalo_bot_token", "zalo_bi_mat", "zalo_chat_moi", "zalo_nhom")],
		["Check", "Password", "Password", "Code", "Table"])
	la("bảng nhóm trỏ đúng", m.get_field("zalo_nhom").options, "Vagabond Kenh Zalo")
	t = frappe.get_meta("Vagabond Tin Kenh")
	la("sổ gửi đặt tên theo khoá", t.autoname, "field:khoa")


@ca("v562 Zalo: gửi thật vào sổ, lần hai cùng sự kiện vấp khoá chính và không gửi lại")
def _so_gui():
	goi = []
	nhom = [{"ten_nhom": "Kế toán " + uuid.uuid4().hex[:6], "chat_id": "c1", "loai_tin": "", "chu_de": "",
		"im_tu": "", "im_den": "", "bat": 1}]
	tin = {"loai": "viec", "chu_de": "cong_no", "tieu_de": "Thử 562", "dong": ["a"], "link": None,
		"khoa": "thu562:" + uuid.uuid4().hex}
	with patch.object(kz, "_bat", lambda: 1), patch.object(kz, "_cac_nhom", lambda: nhom), \
			patch.object(kz, "_gui_zalo", lambda c, t: (goi.append(c), ("Đã gửi", ""))[1]), \
			patch.object(frappe.db, "commit", lambda: None), patch.object(frappe.db, "rollback", lambda: None):
		# Codex #425: hộp thư ghi trong giao dịch trước, rồi mới gửi theo tên dòng.
		ds = kz._ghi_hop_thu(tin)
		ten = kz.khoa_tin(tin["khoa"], nhom[0]["chat_id"])
		la("hộp thư ghi Chờ gửi", (ds, frappe.db.get_value("Vagabond Tin Kenh", ten, "trang_thai")), ([ten], kz.CHO_GUI))
		kz.gui_hang_doi(ds)
		la("đã gửi một lần", goi, ["c1"])
		la("sổ ghi đã gửi", frappe.db.get_value("Vagabond Tin Kenh", ten, "trang_thai"), "Đã gửi")
		try:
			frappe.get_doc({"doctype": "Vagabond Tin Kenh", "name": ten, "khoa": ten}).insert(ignore_permissions=True)
			dung("trùng khoá phải bị chặn", False)
		except frappe.DuplicateEntryError:
			pass


@ca("v562 #413 P2: câu UPDATE claim lô giờ im trên MariaDB thật: lượt sau không lấy lại dòng lượt trước đã nhận")
def _claim_that():
	chat = "chat-thu-" + uuid.uuid4().hex[:8]
	for i in range(3):
		k = "ZL-thu562-" + uuid.uuid4().hex[:12]
		frappe.get_doc({"doctype": "Vagabond Tin Kenh", "name": k, "khoa": k, "nhom": "Thử claim", "chat_id": chat, "loai": "viec",
			"noi_dung": "Việc %s" % i, "trang_thai": "Hoãn giờ im"}).insert(ignore_permissions=True)
	with patch.object(frappe.db, "commit", lambda: None):
		a = kz._nhan_lo(chat, "lo-a-" + uuid.uuid4().hex[:8])
		b = kz._nhan_lo(chat, "lo-b-" + uuid.uuid4().hex[:8])
	la("lượt đầu nhận đủ 3", len(a), 3)
	la("lượt sau không nhận lại", len(b), 0)
	la("trạng thái sau claim", sorted({frappe.db.get_value("Vagabond Tin Kenh", r.name, "trang_thai") for r in a}), ["Đang gửi gộp"])


@ca("v562 #413: sổ gửi có mã lượt, mã kiểm, nguồn và đủ trạng thái mới; Cài đặt có ô kết quả xác minh")
def _truong_moi():
	t = frappe.get_meta("Vagabond Tin Kenh")
	la("có trường", [bool(t.get_field(f)) for f in ("ma_lo", "kiem", "nguon")], [True, True, True])
	tt = (t.get_field("trang_thai").options or "").split("\n")
	dung("đủ trạng thái", all(x in tt for x in ("Đang gửi gộp", "Bỏ qua (đã xử lý)")))
	dung("ô xác minh", bool(frappe.get_meta("Vagabond Settings").get_field("zalo_noi_trang_thai")))


@ca("v562 #425 vòng 9: trên MariaDB thật, dòng kẹt Đang gửi quá 10 phút được gửi bù một lần; dòng Chưa rõ và tin hoãn của nhóm tắt xử lý đúng")
def _ket_that():
	from frappe.utils import add_to_date, now_datetime
	chat = "chat-thu-" + uuid.uuid4().hex[:8]
	ten = {}
	for tt in ("Đang gửi", "Chưa rõ", "Hoãn giờ im"):
		k = "ZL-thu562-" + uuid.uuid4().hex[:12]
		frappe.get_doc({"doctype": "Vagabond Tin Kenh", "name": k, "khoa": k, "nhom": "Thử kẹt", "chat_id": chat,
			"loai": "viec", "noi_dung": "Việc kẹt", "trang_thai": tt, "ma_lo": "lo-cu"}).insert(ignore_permissions=True)
		ten[tt] = k
	cu = add_to_date(now_datetime(), minutes=-30)
	frappe.db.sql("update `tabVagabond Tin Kenh` set creation=%s, modified=%s where chat_id=%s", (cu, cu, chat))
	goi = []
	nhom = [{"ten_nhom": "Thử kẹt", "chat_id": chat, "loai_tin": "", "chu_de": "", "im_tu": "", "im_den": "", "bat": 1}]
	with patch.object(kz, "_bat", lambda: 1), patch.object(kz, "_cac_nhom", lambda: nhom), \
			patch.object(kz, "_gui_zalo", lambda c, t: (goi.append(c), ("Đã gửi", ""))[1]), \
			patch.object(frappe.db, "commit", lambda: None):
		kz.quet_cho_gui()
		kz.quet_cho_gui()
		la("dòng Đang gửi kẹt: gửi bù một lần", (goi.count(chat), frappe.db.get_value("Vagabond Tin Kenh", ten["Đang gửi"], "trang_thai")),
			(1, "Đã gửi"))
		la("dòng Chưa rõ: để nguyên", frappe.db.get_value("Vagabond Tin Kenh", ten["Chưa rõ"], "trang_thai"), "Chưa rõ")
		kz._bo_hoan_nhom_tat(["chat-khac"])
		la("tin hoãn của nhóm không còn bật: Bỏ qua", frappe.db.get_value("Vagabond Tin Kenh", ten["Hoãn giờ im"], "trang_thai"), kz.BO_QUA)
