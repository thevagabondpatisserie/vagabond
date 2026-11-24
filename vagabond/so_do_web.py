"""Sơ đồ trang /sitemap.xml cho Google (v643, còn tồn v605).

Trước v643 /sitemap.xml là bản mặc định của Frappe: ghi địa chỉ nội bộ
vagabond.s.frappe.cloud và liệt kê cả trang dành cho nhân viên (kho-v2,
in-tem, kiem-banh, sop-san-xuat, suc-khoe...). Google lấy đó làm trang của
tiệm. Từ v643 sơ đồ chỉ gồm các trang khách trên tên miền chính.

Phần dựng chuỗi XML là THUẦN để kiểm không cần site.
"""
from xml.sax.saxutils import escape

from vagabond.google_merchant import duong_mon

GOC = "https://thevagabondpatisserie.com"

# (đường dẫn, độ ưu tiên). Chỉ trang khách công khai. Thêm trang khách mới thì
# thêm ở đây; trang của nhân viên TUYỆT ĐỐI không đưa vào.
TRANG_CONG_KHAI = (
	# v692: trang đặt bánh ở "/" và các màn đường sạch (không còn /banh#/...).
	("/", "1.0"),
	("/dat-truoc", "0.9"),
	("/uu-dai", "0.6"),
	("/tuyen-dung", "0.5"),
	("/dat-ban", "0.8"),
	("/thanh-vien", "0.7"),
	("/banh-si", "0.7"),
	("/ung-tuyen", "0.5"),
	("/chinh-sach-bao-mat", "0.3"),
	("/dieu-khoan", "0.3"),
	("/giao-hang-doi-tra", "0.3"),
)


UU_TIEN_MON = "0.6"


def trang_mon(ds):
	"""THUẦN: trang /mon/<mã> của từng bánh đang đưa lên Google (v672).

	ds là kết quả google_merchant.mon_dua_google(), cùng nguồn với tệp
	/google-merchant.xml và trang /mon, nên sơ đồ không tự giữ danh sách bánh
	riêng. Mã trùng hoặc rỗng chỉ ghi một lần."""
	ra, da = [], set()
	for m in ds or ():
		ma = str((m or {}).get("ma") or "").strip()
		if ma and ma not in da:
			da.add(ma)
			ra.append((duong_mon(ma, goc=""), UU_TIEN_MON))
	return tuple(ra)


def xml_so_do(ngay, goc=GOC, trang=TRANG_CONG_KHAI):
	"""THUẦN: chuỗi XML sơ đồ trang. ngay dạng YYYY-MM-DD."""
	dong = ['<?xml version="1.0" encoding="UTF-8"?>',
		'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
	for duong, uu_tien in trang:
		dong.append("<url><loc>%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>"
			% (escape(goc.rstrip("/") + duong), escape(str(ngay)), uu_tien))
	dong.append("</urlset>")
	return "\n".join(dong) + "\n"
