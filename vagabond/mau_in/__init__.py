"""Các mẫu in của tiệm, do MÃ NGUỒN giữ chứ không để trôi nổi trong cơ sở dữ liệu.

  thuong_hieu.py  font va logo theo bo nhan dien, nhung dang data URI
  khuon/          cac khuon Jinja cua phan he bao gia: The Executive,
                  The Lookbook, The Legal Addendum, The Heritage
  *.html          cac mau in khai trong MAU_IN ben duoi, may tu day xuong
                  co so du lieu moi lan Migrate

VÌ SAO MẪU IN PHẢI NẰM Ở ĐÂY
----------------------------
Print Format sửa thẳng trên Desk nằm trong bảng `tabPrint Format` của cơ sở
dữ liệu. Git không quản, không có lịch sử, không ai kiểm chéo được, và nếu
lỡ tay xoá thì không khôi phục được - đúng cái rủi ro đã ghi trong AGENTS.md
với Server Script.

Ngày 21/08/2026 anh Việt in thử Chứng từ thanh toán và thấy ô Mã NCC ra tên
công ty, bảng Nội dung để trống. Lúc đi tìm thì mẫu in không có trong repo,
phải mở Desk mới đọc được. Từ nay mẫu in nằm ở đây, mỗi lần Migrate thì máy
tự đồng bộ xuống cơ sở dữ liệu.

CÁCH DÙNG
---------
Thêm một mẫu: bỏ tệp .html vào thư mục này rồi khai vào MAU_IN bên dưới.
Sửa một mẫu: sửa tệp .html, deploy, patch tự cập nhật.

Máy chỉ ghi đè khi nội dung THỰC SỰ khác, để khỏi đụng vào `modified` của
bản ghi mỗi lần migrate.
"""

import os

import frappe

# ten ban ghi Print Format  ->  (tep .html, doctype)
MAU_IN = {
	"Vagabond - Chứng từ thanh toán": ("chung_tu_thanh_toan.html", "Payment Entry"),
	# Keo ve repo 23/08/2026 khi sua ma vach. Truoc do mau nay chi song trong
	# co so du lieu, khong ai doc duoc neu khong mo Desk.
	"Vagabond - Phiếu nhập kho": ("phieu_nhap_kho.html", "Purchase Receipt"),
}

# Le giay cua tung ban ghi Print Format. Bon o margin nam trong co so du lieu
# chu khong trong HTML, nen phai dat rieng - xem le_in.py de biet vi sao 15mm.
LE_BAN_GHI = ("margin_top", "margin_bottom", "margin_left", "margin_right")

GOC = os.path.dirname(os.path.abspath(__file__))


def doc_mau(ten_tep):
	"""Đọc một tệp mẫu in trong repo. Dùng chung cho patch và cho ca kiểm."""
	with open(os.path.join(GOC, ten_tep), encoding="utf-8") as f:
		return f.read()


def dong_bo():
	"""Đẩy mẫu in từ repo xuống cơ sở dữ liệu. Lặp lại được không giới hạn."""
	ra = {"da_sua": [], "giu_nguyen": [], "chua_co": []}
	for ten, (tep, doctype) in MAU_IN.items():
		try:
			moi = doc_mau(tep)
		except OSError:
			ra["chua_co"].append(ten)
			continue
		if not frappe.db.exists("Print Format", ten):
			# KHÔNG tự tạo mẫu mới ở đây. Tạo mẫu in là việc có chủ đích, và
			# một bản ghi sinh ra lặng lẽ trong lúc migrate thì không ai biết
			# nó từ đâu ra. Ghi nhận rồi thôi.
			ra["chua_co"].append(ten)
			continue
		cu = frappe.db.get_value("Print Format", ten, "html") or ""
		if cu.strip() == moi.strip():
			ra["giu_nguyen"].append(ten)
			continue
		frappe.db.set_value("Print Format", ten, "html", moi, update_modified=False)
		ra["da_sua"].append(ten)

	# Le giay: dat cho MOI mau in cua tiem, ke ca mau chua keo ve repo. Bon o
	# nay nam trong ban ghi chu khong trong HTML nen ha CSS xuong khong toi.
	from vagabond.mau_in.le_in import LE_MM, duoc_ap_le_chung

	for r in frappe.get_all(
		"Print Format",
		filters={"standard": "No", "name": ["like", "Vagabond%"]},
		fields=["name", "doc_type", "html"] + list(LE_BAN_GHI),
	):
		# Khong ap le chung cho ban in khac kho A4/A5, dien hinh la tem
		# 62x45mm. Xem duoc_ap_le_chung() trong le_in.py de biet vi sao.
		if not duoc_ap_le_chung(r.get("name"), r.get("doc_type"), r.get("html")):
			ra.setdefault("bo_qua_le", []).append(r.get("name"))
			continue
		if all(int(r.get(o) or 0) == LE_MM for o in LE_BAN_GHI):
			continue
		for o in LE_BAN_GHI:
			frappe.db.set_value("Print Format", r["name"], o, LE_MM, update_modified=False)
		ra.setdefault("da_dat_le", []).append(r["name"])
	return ra
