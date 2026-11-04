"""v636: font chữ trong nút của app /bep, và nút Khách sỉ trên đầu trang web.

1. Anh Việt 03/11/2026 gửi ảnh màn Đơn đặt trước trên máy Mac: chữ trong chip
   lọc (Tất cả, Mọi điểm nhận, Mọi ngày) và ô đếm (Chờ cọc...) vẽ bằng một font
   khác hẳn chữ thường, đậm vỡ nét; chữ thường cùng độ đậm 800 vẫn đẹp. Đọc trên
   site thật (app.thevagabondpatisserie.com, trình duyệt của Claude): mọi thuộc
   tính chữ của nút trùng chữ thường TRỪ font-variation-settings (nút "normal",
   chữ thường "opsz" 24 do Frappe đặt trên html, body). Bootstrap của Frappe
   chỉ trả font-family cho nút, không trả các thuộc tính chữ còn lại.
   Cách sửa: quy tắc gốc cho button, input, select, textarea nhận TRỌN bộ chữ
   của trang. Bằng chứng trình duyệt thật: cong_cu/kiem_font_nut_636.py dựng
   trang với quy tắc thật của Frappe và toàn bộ CSS app, so thuộc tính chữ của
   chip (vẽ bằng đúng posChipNut) với chữ thường: trước 1 khác biệt, sau 0.
   Máy CI không có trình duyệt nên ca dưới giữ quy tắc gốc và chặn style riêng
   của nút đè lại bộ chữ.

2. Anh Việt 03/11/2026: "làm nút Khách sỉ trên đầu trang, kế bên nút Đặt bàn".
   Ca hành vi dựng THẬT khuôn đầu trang bằng Vue (hanh_vi/dau_trang_636.mjs).
"""

import io
import os
import re
import subprocess

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOC = os.path.dirname(GOI)
BEP = os.path.join(GOI, "public", "js", "bep")
THUOC_TINH = ("font-family", "font-style", "font-stretch", "font-variation-settings",
	"font-optical-sizing", "font-feature-settings")


def _doc(*p):
	return io.open(os.path.join(*p), encoding="utf-8").read()


def _quy_tac(css):
	"""THUẦN. [(danh sách bộ chọn, {thuộc tính: giá trị})] của các quy tắc cấp
	ngoài cùng (bỏ @media và chú thích)."""
	css = re.sub(r"/\*[\s\S]*?\*/", "", css)
	ra = []
	for m in re.finditer(r"([^{}@]+)\{([^{}]*)\}", css):
		chon = [x.strip() for x in m.group(1).split(",")]
		kv = {}
		for d in m.group(2).split(";"):
			if ":" in d:
				k, v = d.split(":", 1)
				kv[k.strip().lower()] = v.strip()
		ra.append((chon, kv))
	return ra


def _css_app():
	app = _doc(GOI, "public", "js", "app_bep.js")
	m = re.search(r"var CSS = `([\s\S]*?)`;", app)
	dung("app_bep.js có khối CSS", m is not None)
	return m.group(1)


@ca("v636 nút và ô nhập nhận trọn bộ chữ của trang (quy tắc gốc trong CSS đã ghép)")
def _nut_nhan_bo_chu():
	qt = [kv for chon, kv in _quy_tac(_css_app()) if "button" in chon]
	la("đúng một quy tắc gốc cho button", len(qt), 1)
	for k in THUOC_TINH:
		la("button " + k, qt[0].get(k), "inherit")
	for the in ("input", "select", "textarea"):
		dung(the + " cũng nhận", any(the in chon and kv.get("font-variation-settings") == "inherit"
			for chon, kv in _quy_tac(_css_app())))
	dung("không đặt cỡ, độ đậm ở quy tắc gốc (giữ cỡ chữ riêng của từng nút)",
		not ({"font", "font-size", "font-weight"} & set(qt[0])))


@ca("v636 không quy tắc CSS nào khác đè lại bộ chữ của nút")
def _khong_de_lai():
	xau = []
	for chon, kv in _quy_tac(_css_app()):
		if "button" in chon:
			continue
		if any(re.search(r"(^|[\s>+~])button\b|\bbutton\[|^\.btn\b", c) for c in chon):
			for k in THUOC_TINH + ("font",):
				if k in kv and kv[k] != "inherit":
					xau.append("%s { %s: %s }" % (",".join(chon), k, kv[k]))
	la("không quy tắc nào đè", xau, [])


@ca("v636 chip lọc dùng chung (posChipNut) vẽ ra không tự đặt bộ chữ riêng")
def _chip_khong_tu_dat():
	# Vẽ THẬT bằng node đúng hàm dựng chip của mọi hàng lọc (Đơn đặt trước, Đơn
	# sỉ web...), cả chip đang chọn lẫn chưa chọn, rồi đọc style của nút vẽ ra.
	ma = r"""
const s=require('fs').readFileSync(process.argv[1],'utf8');
eval(s.match(/function posChipNut\([\s\S]*?\n\}/)[0]);
process.stdout.write(JSON.stringify([posChipNut('data-x="1"','Mọi điểm nhận',true,false,'#4338ca'),
  posChipNut('data-x="2"','Tất cả',false,false)]));"""
	r = subprocess.run(["node", "-e", ma, os.path.join(BEP, "09-tinh-tien-quay.js")], capture_output=True, text=True, timeout=30)
	la(r.stderr[-500:], r.returncode, 0)
	import json
	for html in json.loads(r.stdout):
		dung("vẽ ra nút", html.startswith("<button "))
		style = re.search(r'style="([^"]*)"', html).group(1)
		for k, v in re.findall(r"(font-family|font-variation-settings|font-stretch|font-style)\s*:\s*([^;]+)", style):
			la("chip " + k, v.strip(), "inherit")


@ca("v636 đầu trang web: nút Khách sỉ cạnh Đặt bàn, dựng thật bằng Vue (hanh_vi/dau_trang_636.mjs)")
def _dau_trang():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/dau_trang_636.mjs"], cwd=GOC,
		capture_output=True, text=True, timeout=60)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)
	m = re.search(r"(\d+) ca dat, 0 ca hong", r.stdout)
	dung("đủ số ca", m and int(m.group(1)) >= 2)
