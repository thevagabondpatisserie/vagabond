"""v559 (#410): bắn tin Zalo trên ERPNext thật: bảng cài đặt, sổ gửi, chống trùng.

Không gọi Zalo thật: thay `_gui_zalo` bằng hàm ghi lại. `commit`/`rollback`
của worker được thay bằng hàm rỗng để giữ savepoint của nen.py (không ghi
gì ra site). Không đổi Vagabond Settings thật: danh sách nhóm đưa thẳng vào.
"""
import uuid
from unittest.mock import patch

import frappe

from vagabond import kenh_zalo as kz
from vagabond.khung.kiem_that.nen import ca, dung, la


@ca("v559 Zalo: Cài đặt có đủ ô, bảng nhóm và sổ gửi đúng kiểu")
def _cau_truc():
	m = frappe.get_meta("Vagabond Settings")
	la("kiểu các ô", [m.get_field(f).fieldtype for f in ("zalo_bot_bat", "zalo_bot_token", "zalo_bi_mat", "zalo_chat_moi", "zalo_nhom")],
		["Check", "Password", "Password", "Code", "Table"])
	la("bảng nhóm trỏ đúng", m.get_field("zalo_nhom").options, "Vagabond Kenh Zalo")
	t = frappe.get_meta("Vagabond Tin Kenh")
	la("sổ gửi đặt tên theo khoá", t.autoname, "field:khoa")


@ca("v559 Zalo: gửi thật vào sổ, lần hai cùng sự kiện vấp khoá chính và không gửi lại")
def _so_gui():
	goi = []
	nhom = [{"ten_nhom": "Kế toán " + uuid.uuid4().hex[:6], "chat_id": "c1", "loai_tin": "", "chu_de": "",
		"im_tu": "", "im_den": "", "bat": 1}]
	tin = {"loai": "viec", "chu_de": "cong_no", "tieu_de": "Thử 559", "dong": ["a"], "link": None,
		"khoa": "thu559:" + uuid.uuid4().hex}
	with patch.object(kz, "_bat", lambda: 1), patch.object(kz, "_cac_nhom", lambda: nhom), \
			patch.object(kz, "_gui_zalo", lambda c, t: (goi.append(c), ("Đã gửi", ""))[1]), \
			patch.object(frappe.db, "commit", lambda: None), patch.object(frappe.db, "rollback", lambda: None):
		kz.gui_hang_doi(tin)
		ten = kz.khoa_tin(tin["khoa"], nhom[0]["ten_nhom"])
		la("đã gửi một lần", goi, ["c1"])
		la("sổ ghi đã gửi", frappe.db.get_value("Vagabond Tin Kenh", ten, "trang_thai"), "Đã gửi")
		try:
			frappe.get_doc({"doctype": "Vagabond Tin Kenh", "name": ten, "khoa": ten}).insert(ignore_permissions=True)
			dung("trùng khoá phải bị chặn", False)
		except frappe.DuplicateEntryError:
			pass


@ca("v559 #413 P2: câu UPDATE claim lô giờ im trên MariaDB thật: lượt sau không lấy lại dòng lượt trước đã nhận")
def _claim_that():
	nhom = "Thử claim " + uuid.uuid4().hex[:6]
	for i in range(3):
		k = "ZL-thu559-" + uuid.uuid4().hex[:12]
		frappe.get_doc({"doctype": "Vagabond Tin Kenh", "name": k, "khoa": k, "nhom": nhom, "loai": "viec",
			"noi_dung": "Việc %s" % i, "trang_thai": "Hoãn giờ im"}).insert(ignore_permissions=True)
	with patch.object(frappe.db, "commit", lambda: None):
		a = kz._nhan_lo(nhom, "lo-a-" + uuid.uuid4().hex[:8])
		b = kz._nhan_lo(nhom, "lo-b-" + uuid.uuid4().hex[:8])
	la("lượt đầu nhận đủ 3", len(a), 3)
	la("lượt sau không nhận lại", len(b), 0)
	la("trạng thái sau claim", sorted({frappe.db.get_value("Vagabond Tin Kenh", r.name, "trang_thai") for r in a}), ["Đang gửi gộp"])


@ca("v559 #413: sổ gửi có mã lượt, mã kiểm, nguồn và đủ trạng thái mới; Cài đặt có ô kết quả xác minh")
def _truong_moi():
	t = frappe.get_meta("Vagabond Tin Kenh")
	la("có trường", [bool(t.get_field(f)) for f in ("ma_lo", "kiem", "nguon")], [True, True, True])
	tt = (t.get_field("trang_thai").options or "").split("\n")
	dung("đủ trạng thái", all(x in tt for x in ("Đang gửi gộp", "Bỏ qua (đã xử lý)")))
	dung("ô xác minh", bool(frappe.get_meta("Vagabond Settings").get_field("zalo_noi_trang_thai")))
