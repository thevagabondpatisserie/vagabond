"""Các Web Page của tiệm, do MÃ NGUỒN giữ chứ không để trôi nổi trong CSDL.

  <route>.html   truong `main_section_html`
  <route>.js     truong `javascript`
  <route>.css    truong `css`
  <route>.json   cac truong con lai (tieu de, xuat ban, full_width, ...)

Mỗi lần Migrate, `dong_bo()` đẩy các tệp này xuống cơ sở dữ liệu.

VÌ SAO PHẢI LÀM
---------------
Web Page sửa thẳng trên Desk nằm trong bảng `tabWeb Page`. Git không quản,
không có lịch sử, không ai kiểm chéo được, lỡ tay xoá thì không khôi phục
được. Đúng cái rủi ro đã ghi trong AGENTS.md với Server Script.

Anh Việt chốt 23/08/2026: *"Không để code Web Page nằm kẹt trong Database"*,
và deploy phải *"khoá chặt rủi ro mất code do có người vô tình sửa tay trực
tiếp trên giao diện Desk"*.

ĐÂY LÀ MỘT THAY ĐỔI CÁCH LÀM VIỆC, KHÔNG CHỈ LÀ CODE
-----------------------------------------------------
Từ v288, mười ba trang dưới đây sửa TRONG GIT, không sửa trên Desk. Sửa trên
Desk thì lần deploy kế tiếp ghi đè mất. Trang `banh` là trang khách đặt bánh
và trước nay có người ngoài kỹ thuật sửa, nên phải báo cho họ biết.

`soi_lech` trong `vagabond/mau_in/__init__.py` cho biết BẤT KỲ LÚC NÀO trang
trên site có lệch bản trong repo hay không. Chạy nó TRƯỚC mỗi lần deploy: có
lệch nghĩa là có người vừa sửa tay, và phải kéo bản đó về git trước khi
deploy, nếu không là mất việc của họ.

VÌ SAO KHÔNG DÙNG `fixtures` CỦA FRAPPE
----------------------------------------
Anh Việt đề nghị `fixtures`. Đã đọc mã nguồn Frappe v16 và KHÔNG dùng, vì bốn
lý do cụ thể chứ không phải vì thích tự viết:

1. `import_file_by_path` XOÁ bản ghi cũ rồi INSERT lại. Web Page nào cũng bị
   xoá đi dựng lại mỗi lần migrate, kể cả khi nội dung không đổi. Cách ở đây
   chỉ ghi khi nội dung THỰC SỰ khác, nên `modified` không nhảy vô cớ.
2. `fixtures` chỉ xuất được bằng `bench export-fixtures`, mà Cowork không
   chạy được `bench`. Tệp fixture sẽ phải gõ tay, và gõ sai thì hỏng migrate.
3. `fixtures` nuốt lỗi rồi bỏ qua cả tệp. Một trang hỏng là im lặng bỏ qua
   cả mười ba trang, không ai biết.
4. Không kiểm thử được nếu không có site. Cả bộ quy tắc của repo này dựng
   trên nguyên tắc "tách phép THUẦN ra để kiểm được không cần site", và
   `fixtures` thì không tách được.

Cách ở đây làm đúng việc anh Việt cần - deploy đè git xuống CSDL - bằng chính
cơ chế mà `vagabond/mau_in/__init__.py` đã chạy thật cho mẫu in từ v281.

BỐN CHỐT AN TOÀN, ĐỌC TRƯỚC KHI SỬA TỆP NÀY
--------------------------------------------
1. CHỈ đẩy các trang khai trong `TRANG`. Trang lạ trên site không bị đụng tới.
   Đây là liệt kê từng cái, đúng tinh thần quy tắc 6.
2. KHÔNG BAO GIỜ TỰ TẠO trang mới. Chưa có bản ghi thì ghi nhận rồi thôi.
   Một trang sinh ra lặng lẽ trong lúc migrate thì không ai biết nó ở đâu ra.
3. KHÔNG HẠ SỐ APPVER. Trang `bep` và `kho-moi` mang APPVER trong phần
   javascript. Bản trong repo cũ hơn bản trên site thì BỎ QUA trang đó và ghi
   nhật ký, chứ không đẩy lùi. Luật này chép đúng ý Server Script "Chan ghi
   de APPVER - Web Page" đang chạy trên site, để hai cơ chế không đánh nhau.
4. LỌC RÁC TIỆN ÍCH TRÌNH DUYỆT. Ngày 06/08/2026 `main_section_html` của
   trang `banh` chứa hai thẻ script trỏ tới `local.adguard.org` do tiện ích
   chặn quảng cáo trên máy người sửa chèn vào rồi lưu thẳng vào CSDL. Khách
   vào trang phải tải hai đường dẫn chết đó.
"""

import json
import os
import re

import frappe

GOC = os.path.dirname(os.path.abspath(__file__))

# route Web Page -> mo ta ngan, chi de nguoi doc biet trang do lam gi.
TRANG = {
	"banh": "Trang khách đặt bánh (order.thevagabondpatisserie.com)",
	"bep": "Vỏ chứa app nghiệp vụ, chỉ có đoạn nạp app_bep.js",
	"btp": "Bán thành phẩm, bánh ổ",
	"cuon-ma": "Cuốn mã vạch nguyên vật liệu",
	"in-tem": "In tem",
	"kho-moi": "Kho bản thử nghiệm",
	"kho-v2": "Nhập kho v2",
	"kiem-banh": "Kiểm bánh ngày",
	"ong-trang": "Ông trăng xuống chơi",
	"sop-san-xuat": "SOP bếp một ngày sản xuất",
	"suc-khoe": "Sức khoẻ đồng bộ",
	"tt": "Thanh toán đơn hàng",
	"xhd": "Xuất hoá đơn",
}

# truong trong CSDL  ->  duoi tep trong thu muc nay
O_NOI_DUNG = (
	("main_section_html", "html"),
	("javascript", "js"),
	("css", "css"),
)

# Nhung truong KHONG duoc dua tu json xuong CSDL, du co nam trong tep.
# `name` va `route` la danh tinh cua ban ghi, doi la thanh mot trang khac.
O_CHI_DOC = ("name", "route", "doctype", "creation", "modified", "owner",
	"modified_by", "idx", "docstatus")

# Rac do tien ich chan quang cao chen vao. Xem chot an toan 4 o dau tep.
RAC = (
	re.compile(r"<script[^>]*local\.adguard\.org[^>]*>\s*</script>", re.I),
)


def loc_rac(noi_dung):
	"""Bỏ những thẻ do tiện ích trình duyệt chèn vào. THUẦN."""
	t = noi_dung or ""
	for m in RAC:
		t = m.sub("", t)
	return t


def so_appver(js):
	"""Số APPVER đọc từ một đoạn javascript. -1 là không có. THUẦN.

	Chép đúng cách đọc của Server Script "Chan ghi de APPVER - Web Page":
	tìm chữ APPVER rồi gom các chữ số liền sau nó.
	"""
	t = str(js or "")
	i = t.find("APPVER")
	if i < 0:
		return -1
	so = ""
	for ch in t[i:i + 60]:
		if ch.isdigit():
			so += ch
		elif so:
			break
	return int(so) if so else -1


def duoc_day(js_repo, js_csdl):
	"""Đoạn javascript trong repo có được phép đè lên bản trên site không.

	THUẦN, để kiểm thử được không cần site. Trả về (được_hay_không, lý_do).

	Chặn đúng một chuyện: HẠ số APPVER. Bản trên site không mang APPVER thì
	không có gì để chặn, và bằng nhau cũng cho qua vì đó là trường hợp bình
	thường nhất - deploy lại mà nội dung không đổi.
	"""
	cu, moi = so_appver(js_csdl), so_appver(js_repo)
	if cu >= 0 and 0 <= moi < cu:
		return False, ("bản trong repo mang APPVER %d, thấp hơn bản trên site "
			"APPVER %d. Có phiên khác đã cập nhật trang này." % (moi, cu))
	if cu >= 0 and moi < 0:
		return False, ("bản trên site mang APPVER %d còn bản trong repo không "
			"mang số nào. Đẩy xuống là xoá mất đoạn nạp app." % cu)
	return True, ""


def duong_tep(route, duoi):
	return os.path.join(GOC, "%s.%s" % (route, duoi))


def doc_mot(route):
	"""Đọc một trang từ repo thành dict {truong: noi_dung}. Thiếu tệp thì bỏ qua."""
	ra = {}
	for truong, duoi in O_NOI_DUNG:
		d = duong_tep(route, duoi)
		if os.path.exists(d):
			with open(d, encoding="utf-8") as f:
				ra[truong] = loc_rac(f.read())
	d = duong_tep(route, "json")
	if os.path.exists(d):
		with open(d, encoding="utf-8") as f:
			for k, v in (json.load(f) or {}).items():
				if k not in O_CHI_DOC:
					ra[k] = v
	return ra


def dong_bo():
	"""Đẩy các trang từ repo xuống cơ sở dữ liệu. Lặp lại được không giới hạn.

	Chỉ ghi khi nội dung THỰC SỰ khác, để khỏi đụng vào `modified` mỗi lần
	migrate. Không tự tạo trang mới. Không hạ APPVER.
	"""
	ra = {"da_sua": [], "giu_nguyen": [], "chua_co": [], "bo_qua": []}
	for route in sorted(TRANG):
		moi = doc_mot(route)
		if not moi:
			ra["chua_co"].append("%s (thiếu tệp trong repo)" % route)
			continue
		ten = frappe.db.get_value("Web Page", {"route": route}, "name")
		if not ten:
			# Chot an toan 2: khong tu tao trang moi.
			ra["chua_co"].append("%s (chưa có bản ghi trên site)" % route)
			continue

		cu = frappe.db.get_value(
			"Web Page", ten,
			["javascript"] + [k for k in moi if k != "javascript"],
			as_dict=True,
		) or {}

		# Chot an toan 3: khong ha APPVER.
		if "javascript" in moi:
			duoc, vi_sao = duoc_day(moi["javascript"], cu.get("javascript"))
			if not duoc:
				ra["bo_qua"].append("%s: %s" % (route, vi_sao))
				continue

		doi = {}
		for k, v in moi.items():
			gia_tri_cu = cu.get(k)
			if isinstance(v, str) or isinstance(gia_tri_cu, str):
				if (gia_tri_cu or "").strip() != (v or "").strip():
					doi[k] = v
			elif gia_tri_cu != v:
				doi[k] = v
		if not doi:
			ra["giu_nguyen"].append(route)
			continue
		for k, v in doi.items():
			frappe.db.set_value("Web Page", ten, k, v, update_modified=False)
		ra["da_sua"].append("%s (%s)" % (route, ", ".join(sorted(doi))))
	return ra
