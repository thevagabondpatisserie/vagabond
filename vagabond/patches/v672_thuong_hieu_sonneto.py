"""v672 (anh Việt 18/11/2026): kênh Sonneto trên màn Bài đăng mạng xã hội.

"Sonneto Social em cho vào luôn ở đây đi nhé, làm luôn thêm việc kết nối với các kênh của
Sonneto để đăng nhé, quản lý từ 1 nơi thôi."

Chủ đề có tên chứa "Sonneto" (sổ Sonneto Social gieo ở v670) mang thương hiệu Sonneto, nên
bài trong chủ đề đó đi kênh Sonneto. v670 gieo cho mọi chủ đề bốn câu chân bài của The
Vagabond (đặt bánh, địa chỉ quầy); chủ đề Sonneto còn đúng bốn câu đó thì bỏ đi, vì đó
không phải chân bài của Sonneto. Chủ đề Marketing đã sửa chân bài thì giữ nguyên.

Bài còn sửa được (Nháp, Chờ duyệt) trong chủ đề Sonneto ghi thương hiệu Sonneto và bỏ
kênh Zalo OA (Sonneto chưa có Zalo OA). Bài đã duyệt, đã đăng không đổi.
Chạy lại không đổi gì.
"""


def la_chu_de_sonneto(ten):
	"""THUẦN: chủ đề này của Sonneto (tên có chữ Sonneto, không phân biệt hoa thường)."""
	return "sonneto" in str(ten or "").lower()


def cta_moi(cta, cta_gieo):
	"""THUẦN: chân bài mới của chủ đề Sonneto: còn đúng chân bài gieo sẵn của The
	Vagabond thì bỏ (chuỗi rỗng); đã sửa thì None (giữ nguyên)."""
	dong = [x.strip() for x in str(cta or "").split("\n") if x.strip()]
	return "" if dong and dong == [x.strip() for x in cta_gieo] else None


def kenh_bo_zalo(kenh_chon):
	"""THUẦN: chuỗi kênh bỏ Zalo OA; None nếu không có Zalo OA."""
	ma = [x for x in str(kenh_chon or "").replace(";", ",").replace(" ", ",").split(",") if x]
	if "zl" not in ma:
		return None
	return ",".join(x for x in ma if x != "zl")


def execute():
	import frappe
	from vagabond import bai_dang

	if not frappe.db.table_exists(bai_dang.DT_CHU_DE):
		return
	so = []
	for c in frappe.get_all(bai_dang.DT_CHU_DE, fields=["name", "ten", "cta", "thuong_hieu"], limit_page_length=0):
		if not la_chu_de_sonneto(c.ten):
			if not c.thuong_hieu:
				frappe.db.set_value(bai_dang.DT_CHU_DE, c.name, "thuong_hieu", "Vagabond", update_modified=False)
			continue
		so.append(c.name)
		if c.thuong_hieu != "Sonneto":
			frappe.db.set_value(bai_dang.DT_CHU_DE, c.name, "thuong_hieu", "Sonneto", update_modified=False)
			moi = cta_moi(c.cta, bai_dang.CTA_GIEO)
			if moi is not None:
				frappe.db.set_value(bai_dang.DT_CHU_DE, c.name, "cta", moi, update_modified=False)
	if so:
		for b in frappe.get_all(bai_dang.DT, filters={"chu_de": ["in", so], "trang_thai": ["in", bai_dang.TT_SUA_DUOC]},
				fields=["name", "kenh_chon", "thuong_hieu"], limit_page_length=0):
			gia_tri = {}
			if b.thuong_hieu != "Sonneto":
				gia_tri["thuong_hieu"] = "Sonneto"
			k = kenh_bo_zalo(b.kenh_chon)
			if k is not None:
				gia_tri["kenh_chon"] = k
			if gia_tri:
				frappe.db.set_value(bai_dang.DT, b.name, gia_tri, update_modified=False)
	frappe.db.commit()
