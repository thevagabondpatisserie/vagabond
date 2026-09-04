# -*- coding: utf-8 -*-
"""Cửa SỬA và HUỶ dành riêng cho cấp giám đốc, dùng chung cho mọi loại phiếu.

Vì sao có tệp này
-----------------
Anh Việt 04/09/2026: *"luôn có nút sửa/huỷ (chứ không xoá) dành cho cấp
giám đốc cho mọi loại phiếu, em ghi vào backend"*.

Chuyện nổ ra từ một phiếu nộp quỹ NQ-2026-01629 lập thử rồi bỏ đó ở trạng
thái Nháp. Phiếu nháp đó vẫn tính là đã nộp cho ngày 30/08 của điểm Quận 1,
nên tới lúc làm biên nhận THẬT cho đúng ngày đó thì máy chặn, mà trên màn
không có một nút nào để gỡ phiếu nháp kia ra. Người dùng đứng trước một cái
ngõ cụt do chính phần mềm dựng lên.

Bịt riêng cho màn nộp quỹ thì lần sau một màn khác lại đúng cảnh đó. Nên
gom luật vào một chỗ, mỗi loại phiếu chỉ việc cắm vào.

Ba điều bất di bất dịch
-----------------------
1. HUỶ CHỨ KHÔNG XOÁ. Phiếu huỷ vẫn nằm nguyên trong cơ sở dữ liệu, vẫn mở
   ra đọc được, chỉ đổi trạng thái và mang dấu ai huỷ, lúc nào, vì sao. Xoá
   thật là mất luôn vết một lần bàn giao tiền, mà tiền thì có thật.
2. PHẢI CÓ LÝ DO, và lý do phải ra hồn. Gõ "abc" hay một dấu chấm thì chặn.
   Sau này mở phiếu ra đọc, câu lý do là thứ duy nhất còn lại để hiểu vì sao
   một phiếu tiền bị bỏ.
3. CHẶN Ở MÁY CHỦ. Ẩn nút trên màn chỉ là lịch sự; gọi thẳng API vẫn lọt.
   Vai được kiểm ở đây, trong cùng hàm ghi.

Cách cắm một loại phiếu mới vào
-------------------------------
a. Doctype thêm một trạng thái huỷ vào ô `trang_thai`, và thêm bốn ô vết
   trong `TRUONG_VET` bên dưới.
b. Mô đun nghiệp vụ thêm hai cửa `huy(ma, ly_do)` và `sua(ma, ..., ly_do)`,
   mở đầu bằng `giam_doc_sua_huy.chan()` rồi `doc_ly_do(...)`.
c. Trước khi đổi trạng thái, TRẢ LẠI mọi thứ phiếu đang giữ: ca đã đóng
   dấu, phiếu con đã nối, chứng từ đã khoá. Huỷ mà quên nhả là khoá vĩnh
   viễn thứ khác.
d. Chặn huỷ khi phiếu đã đẻ ra chứng từ kế toán đã ghi sổ. Việc gỡ sổ là
   việc của kế toán, không phải của một nút trên app.
e. Thêm tên hai cửa vào `vagabond/khung/kiem_thu/thu_cua_ngo.py`.
"""

import frappe
from frappe.utils import now_datetime

# Cấp giám đốc. Giữ đúng bộ vai mà `ho_so_tt.py` và `de_nghi_chi.py` đang
# dùng cho bước duyệt cuối, để không sinh ra khái niệm "giám đốc" thứ hai
# trong cùng một hệ.
VAI_GD = {"AP Giám đốc", "System Manager"}

# Lý do ngắn hơn mức này thì coi như chưa gõ. Tám ký tự đủ cho "gõ nhầm"
# hay "trùng ngày", mà chặn được "x", "." và "aaa".
DAI_LY_DO_TOI_THIEU = 8

# Bốn ô vết mà doctype nào muốn huỷ được cũng phải có. Ghi ra đây để lần
# sau cắm thêm một loại phiếu thì khỏi phải đi đọc ngược.
TRUONG_VET = ("huy_boi", "ten_nguoi_huy", "huy_luc", "ly_do_huy")


# ============================================================ phép THUẦN


def duoc_sua_huy(cac_vai):
	"""Người mang các vai này có được sửa hay huỷ phiếu không. THUẦN."""
	return bool(VAI_GD & set(cac_vai or []))


def sach_ly_do(ly_do):
	"""Gọt lý do về dạng sạch, chặn lý do rỗng hay gõ cho có. THUẦN.

	Ném ValueError khi không đạt, để tầng gọi tự quyết ném ra màn hay trả
	về dạng khác.
	"""
	t = " ".join(str(ly_do or "").split())
	if len(t) < DAI_LY_DO_TOI_THIEU:
		raise ValueError(
			"Phải ghi lý do, ít nhất %d ký tự. Đây là dấu vết duy nhất còn "
			"lại để sau này hiểu vì sao một phiếu tiền bị sửa hay bị bỏ."
			% DAI_LY_DO_TOI_THIEU
		)
	return t


def cau_vet(viec, nguoi, ly_do):
	"""Một dòng vết gọn cho nhật ký phiếu. THUẦN."""
	return "%s bởi %s - %s" % (viec, nguoi, ly_do)


# ====================================================== phần chạm hệ


def chan(viec="sửa hoặc huỷ phiếu"):
	"""Chặn ngay nếu người gọi không phải cấp giám đốc."""
	if not duoc_sua_huy(frappe.get_roles()):
		frappe.throw(
			"Chỉ cấp giám đốc mới được %s. Nếu phiếu sai thì báo giám đốc, "
			"đừng lập phiếu mới đè lên." % viec,
			title="Không đủ quyền",
		)


def doc_ly_do(ly_do):
	"""Gọt lý do, ném thẳng ra màn khi không đạt."""
	try:
		return sach_ly_do(ly_do)
	except ValueError as e:
		frappe.throw(str(e), title="Thiếu lý do")


def ghi_vet(doctype, name, viec):
	"""Lưu một dòng nhật ký lên chính phiếu. Hỏng thì bỏ qua, không chặn."""
	try:
		frappe.get_doc({
			"doctype": "Comment", "comment_type": "Info",
			"reference_doctype": doctype, "reference_name": name,
			"content": viec,
		}).insert(ignore_permissions=True)
	except Exception:
		pass


def ten_toi():
	toi = frappe.session.user
	return frappe.db.get_value("User", toi, "full_name") or toi


def dong_dau_huy(doc, ly_do):
	"""Đóng bốn ô vết huỷ lên phiếu. KHÔNG tự lưu, KHÔNG tự đổi trạng thái.

	Để tầng nghiệp vụ tự đặt trạng thái huỷ của nó, vì mỗi loại phiếu gọi
	tên trạng thái đó một kiểu.
	"""
	doc.huy_boi = frappe.session.user
	doc.ten_nguoi_huy = ten_toi()
	doc.huy_luc = now_datetime()
	doc.ly_do_huy = ly_do
	return doc


def da_huy(doc, tt_huy):
	"""Phiếu này đã huỷ rồi thì chặn, kèm ai huỷ lúc nào."""
	if doc.get("trang_thai") == tt_huy:
		frappe.throw(
			"Phiếu %s đã huỷ rồi (%s lúc %s%s). Không huỷ hai lần." % (
				doc.name,
				doc.get("ten_nguoi_huy") or doc.get("huy_boi") or "?",
				doc.get("huy_luc") or "?",
				(", lý do: " + doc.get("ly_do_huy")) if doc.get("ly_do_huy") else "",
			)
		)
