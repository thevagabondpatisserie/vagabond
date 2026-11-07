"""v643 (còn tồn v605): /sitemap.xml chỉ gồm trang khách trên tên miền chính.

Trước v643 (đọc trên site 07/11/2026): sơ đồ mặc định của Frappe có 14 địa chỉ,
TẤT CẢ ghi vagabond.s.frappe.cloud, gồm cả trang nhân viên kho-v2, kho-moi,
in-tem, btp, kiem-banh, cuon-ma, sop-san-xuat, suc-khoe."""
import ast
import re
from pathlib import Path
from xml.etree import ElementTree as ET

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import so_do_web, ten_mien

GOC = Path(__file__).resolve().parents[3]
NOI_BO = ("/kho-v2", "/kho-moi", "/in-tem", "/btp", "/kiem-banh", "/cuon-ma", "/sop-san-xuat", "/suc-khoe",
	"/bep", "/app", "/xhd", "/tt", "/ong-trang", "/about", "/contact")


@ca("v643 /sitemap.xml: chỉ trang khách, đúng tên miền chính, XML hợp lệ, không trang nhân viên")
def _so_do():
	x = so_do_web.xml_so_do("2026-11-07")
	goc = ET.fromstring(x.encode())
	ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
	loc = [e.text for e in goc.findall("s:url/s:loc", ns)]
	dung("có trang đặt bánh", "https://thevagabondpatisserie.com/banh" in loc)
	dung("mọi địa chỉ trên tên miền chính", loc and all(u.startswith("https://thevagabondpatisserie.com/") for u in loc))
	dung("không địa chỉ nội bộ frappe.cloud", "frappe.cloud" not in x)
	duong = [u[len("https://thevagabondpatisserie.com"):] for u in loc]
	la("không trang nhân viên", [d for d in duong if d in NOI_BO or any(d == a or d.startswith(a + "/") for a in ten_mien.DAU_APP)], [])
	la("ngày cập nhật", {e.text for e in goc.findall("s:url/s:lastmod", ns)}, {"2026-11-07"})
	dung("mọi trang trong sơ đồ là trang khách của tên miền chính", all(any(d == a for a in ten_mien.DAU_KHACH) for d in duong))


@ca("v643 /sitemap.xml: luật định tuyến trỏ về trang của tiệm, có mẫu và bộ điều khiển đi cùng")
def _luat():
	src = (GOC / "vagabond/hooks.py").read_text()
	dung("hooks có luật /sitemap.xml", re.search(r'\{"from_route":\s*"/sitemap\.xml",\s*"to_route":\s*"vgb-sitemap\.xml"\}', src))
	mau = (GOC / "vagabond/www/vgb-sitemap.xml").read_text()
	dung("mẫu chỉ in chuỗi sơ đồ", mau.strip() == "{{ so_do }}")
	py = ast.parse((GOC / "vagabond/www/vgb_sitemap.py").read_text())
	dung("bộ điều khiển có get_context", any(isinstance(n, ast.FunctionDef) and n.name == "get_context" for n in py.body))
	dung("ten_mien cho /sitemap.xml đi qua mọi tên miền", "/sitemap.xml" in ten_mien.CHUA_RA)
