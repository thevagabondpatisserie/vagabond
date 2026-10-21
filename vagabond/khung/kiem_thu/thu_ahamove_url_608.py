# -*- coding: utf-8 -*-
"""v608 (anh Việt 21/10/2026): web mất phí giao vì ô địa chỉ API Ahamove có
đuôi /v3, và sales thu phí giao của đơn web đã được miễn.

Hai lỗ:
  1. Ô Vagabond Settings điền "https://partner-api.ahamove.com/v3", mã nối
     thêm "/v3/accounts/token" thành ".../v3/v3/...", Ahamove 404, web báo
     "ahamove_loi" suốt hai tuần. Sửa bằng MỘT hàm lib.aha_url chịu mọi kiểu
     điền, và chốt bằng AST: không còn chỗ nào tự ghép từ ahamove_base.
  2. Đơn web đủ ngưỡng miễn phí giao sang Pancake chỉ có phí giao 0, không
     có chữ nào nói là miễn phí, sales tưởng chưa tính nên thu thêm. Nay gửi
     cờ is_free_shipping và dòng ghi chú in đậm.

Không import don_hang (kéo requests, CI tay không không có): nạp riêng
cau_mien_phi bằng AST.
"""

import ast
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.lib import aha_url

GOC = Path(__file__).resolve().parents[2]


@ca("v608 aha_url: mọi kiểu điền ô địa chỉ đều ra đúng một địa chỉ")
def _():
	muc = "https://partner-api.ahamove.com/v3/accounts/token"
	for base in ("https://partner-api.ahamove.com", "https://partner-api.ahamove.com/",
			"https://partner-api.ahamove.com/v3", "https://partner-api.ahamove.com/v3/",
			"  https://partner-api.ahamove.com/V3/  ", "https://partner-api.ahamove.com/v3/v3"):
		la("base %r" % base, aha_url(base, "/accounts/token"), muc)
	la("đường dẫn đã có /v3 thì không nối thêm", aha_url("https://x/v3", "/v3/services?city_id=SGN"),
		"https://x/v3/services?city_id=SGN")
	la("đường dẫn thiếu dấu / đầu", aha_url("https://x", "orders"), "https://x/v3/orders")
	la("staging giữ nguyên tên miền", aha_url("https://partner-apistg.ahamove.com/", "/orders/estimates"),
		"https://partner-apistg.ahamove.com/v3/orders/estimates")
	la("ô trống thì chỉ còn đường dẫn, để lớp trên báo chưa điền", aha_url(None, "/orders"), "/v3/orders")


@ca("v608 aha_url: không còn chỗ nào tự ghép địa chỉ từ ahamove_base ngoài aha_url")
def _():
	con = []
	for tep in sorted(GOC.glob("*.py")):
		src = tep.read_text(encoding="utf-8")
		if "ahamove_base" not in src:
			continue
		cay = ast.parse(src)
		for n in ast.walk(cay):
			# Phép cộng chuỗi mà một vế đọc ahamove_base là tự ghép.
			if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
				chu = ast.unparse(n)
				if "ahamove_base" in chu:
					con.append("%s: %s" % (tep.name, chu))
	la("danh sách chỗ tự ghép", con, [])
	# Bốn chỗ gọi Ahamove đều đi qua aha_url.
	goi = 0
	for tep in ("giao_hang.py", "van_don.py"):
		src = (GOC / tep).read_text(encoding="utf-8")
		goi += src.count("aha_url(c.ahamove_base,")
	la("bốn chỗ gọi qua aha_url", goi, 4)


def _nap_cau_mien_phi():
	cay = ast.parse((GOC / "don_hang.py").read_text(encoding="utf-8"))
	ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "cau_mien_phi")
	from vagabond import don_web
	g = {"don_web": don_web}
	exec(compile(ast.Module(body=[ham], type_ignores=[]), "don_hang.py", "exec"), g)
	return g["cau_mien_phi"]


@ca("v608 miễn phí giao: dòng ghi chú cho sales nói rõ ngưỡng, không có số thì vẫn nói miễn phí")
def _():
	f = _nap_cau_mien_phi()
	la("có ngưỡng", f(1000000), "MIỄN PHÍ GIAO: đơn web từ 1.000.000 đ, không thu phí giao của khách.")
	la("ngưỡng chuỗi", f("1500000"), "MIỄN PHÍ GIAO: đơn web từ 1.500.000 đ, không thu phí giao của khách.")
	la("không ngưỡng", f(0), "MIỄN PHÍ GIAO: không thu phí giao của khách.")
	la("ngưỡng rác", f("abc"), "MIỄN PHÍ GIAO: không thu phí giao của khách.")


@ca("v608 miễn phí giao: tao_don gửi Pancake cờ is_free_shipping và ghi chú khi phi.mien_phi")
def _():
	src = (GOC / "don_hang.py").read_text(encoding="utf-8")
	cay = ast.parse(src)
	f = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == "tao_don")
	khoi = [n for n in ast.walk(f) if isinstance(n, ast.If) and ast.unparse(n.test) == "phi.get('mien_phi')"]
	la("đúng một khối theo phi.mien_phi", len(khoi), 1)
	than = "\n".join(ast.unparse(x) for x in khoi[0].body)
	dung("đặt cờ miễn phí", "body['is_free_shipping'] = True" in than)
	dung("ghi chú nội bộ", "body['note'] = _them_dong(body.get('note'), chu_mp)" in than)
	dung("ghi chú in", "body['note_print'] = _them_dong(body.get('note_print'), chu_mp)" in than)
	dung("câu lấy từ cau_mien_phi theo ngưỡng thật", "cau_mien_phi(don_web.nguong_mien_phi())" in than)
	# Khối nằm SAU khi body dựng xong và TRƯỚC khi gửi Pancake.
	vi_tri = src.index("if phi.get(\"mien_phi\"):")
	dung("sau khi dựng body", src.index('"shipping_fee": int(phi.get("phi_khach") or 0)') < vi_tri)
	dung("trước khi gửi Pancake", vi_tri < src.index("ma_http, du_lieu, loi_mang = _gui_pancake("))
