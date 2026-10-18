"""v604: điền sẵn ô Tin nhận cho hai nhóm Zalo đang có trên site.

Anh Việt 18/10/2026 bỏ hẳn thư cảnh báo nội bộ, mọi tin cho nhân viên đi qua
nhóm Zalo, mỗi nhóm tích đúng những tin cần nhận (kenh_zalo.TIN). Site đang có
hai nhóm: "ERP Văn Phòng - Kế Toán - Thu Mua" và "Sales Vagabond - Nhóm Bán
hàng". Bản vá này tích sẵn cho hai nhóm đó để từ đêm đầu tiên tin đã vào đúng
nhóm, anh không phải mở từng nhóm tích lại.

Chỉ ghi cấu hình (bảng Nhóm nhận tin trong Vagabond Settings), không chạm chứng
từ hay sổ sách nào. Chỉ điền nhóm có ô Tin nhận đang TRỐNG: nhóm anh đã tích tay
thì giữ nguyên, chạy lại bản vá không đổi gì (lũy đẳng). Nhóm có tên khác thì
không đụng tới.
"""

import unicodedata

# Tin cho nhóm văn phòng, kế toán: toàn bộ mục Hoá đơn, kế toán, cộng báo động thư
# hỏng và bản tin phát hành (anh Việt chốt danh sách 18/10/2026).
TIN_KE_TOAN = (
	"hd_ket_ghi_so", "hd_don_chua_ghi_so", "hd_hddt_sot", "hd_giu_ngay_cu", "hd_trung", "hd_dau_vao",
	"kt_tra_truoc_erp", "kt_hoan_tien", "kt_de_nghi_chi", "kt_tra_truoc_kiem", "kt_diem_het_han",
	"kt_hop_dong_dc", "ht_email_loi", "ht_phat_hanh",
)
# Tin cho nhóm Sales: mục Bán hàng, cửa hàng cộng bản tin phát hành. Hai tin
# bh_pancake_lech_tong, bh_ahamove_phi trước đây đã tới nhóm Sales theo chủ đề Đơn
# web, nên giữ cho nhóm này để không mất tin sau khi nhóm chuyển sang lọc theo tin.
TIN_SALES = (
	"bh_don_web_treo", "bh_ton_web_loi", "bh_ahamove_huy", "bh_dat_ban", "bh_tiec",
	"bh_pancake_lech_tong", "bh_ahamove_phi", "ht_phat_hanh",
)


def _khong_dau(s):
	s = unicodedata.normalize("NFD", str(s or "")).replace("đ", "d").replace("Đ", "D")
	return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def tin_cho_nhom(ten_nhom):
	"""THUẦN: các mã tin điền sẵn cho một nhóm theo tên, rỗng nếu không đoán được.

	Khớp không phân biệt hoa thường và dấu: tên chứa "ke toan" là nhóm kế toán,
	tên chứa "sales" hoặc "ban hang" là nhóm bán hàng. Tên chứa cả hai thì ưu tiên
	kế toán (nhóm văn phòng nhận tin hoá đơn, không được để rơi)."""
	t = _khong_dau(ten_nhom)
	if "ke toan" in t:
		return list(TIN_KE_TOAN)
	if "sales" in t or "ban hang" in t:
		return list(TIN_SALES)
	return []


def dien_san(ds):
	"""THUẦN: [(chỉ số dòng, chuỗi mã)] cần ghi cho các dòng có Tin nhận đang trống."""
	ra = []
	for i, r in enumerate(ds or []):
		if str((r or {}).get("tin_nhan") or "").strip():
			continue
		ma = tin_cho_nhom((r or {}).get("ten_nhom"))
		if ma:
			ra.append((i, ", ".join(ma)))
	return ra


def execute():
	import frappe
	from vagabond import kenh_zalo

	# Chốt cùng danh mục: mã ở đây mà không còn trong TIN thì kiem_bo_loc chặn
	# lưu Cài đặt về sau, nên dừng migrate ngay cho người làm sửa.
	la = sorted(set(TIN_KE_TOAN + TIN_SALES) - set(kenh_zalo.TIN))
	if la:
		raise Exception("v604_tin_nhan_zalo: mã tin không có trong kenh_zalo.TIN: %s" % ", ".join(la))
	if not frappe.db.has_column("Vagabond Kenh Zalo", "tin_nhan"):
		return
	rows = frappe.get_all("Vagabond Kenh Zalo",
		filters={"parenttype": "Vagabond Settings", "parentfield": "zalo_nhom"},
		fields=["name", "ten_nhom", "tin_nhan"], order_by="idx asc", limit_page_length=0)
	for i, chuoi in dien_san(rows):
		# Ghi thẳng ô con: không qua save() của Cài đặt để không kích các phép kiểm
		# khác (mã chat, token) có thể chặn migrate vì cấu hình chưa đủ.
		frappe.db.set_value("Vagabond Kenh Zalo", rows[i]["name"], "tin_nhan", chuoi, update_modified=False)
	frappe.db.commit()
	frappe.clear_cache(doctype="Vagabond Settings")
