# -*- coding: utf-8 -*-
"""Tem HACCP không cần lô (v560).

Từ 30/09/2026 anh Việt tắt quản lý lô cho toàn bộ mã hàng. Tem HACCP cũ là
mẫu in trên Batch, nên tắt lô là nút In tem chỉ còn báo "chưa bật theo dõi
lô". Anh Việt chốt 03/10/2026 (bảng duyệt sổ tay, việc số 1): đổi dòng lô
thành "Ngày: ..." để nhân viên điền tay.

Tem mới dựng từ hồ sơ Món (và mã lệnh nếu có), trang /tem-lenh trả HTML in
được bằng cả đường trình duyệt lẫn đường in ngầm QZ, như /printview cũ.
Mọi phép ở đây là THUẦN để kiểm không cần site; trang www chỉ đọc dữ liệu
rồi gọi sang.
"""

import datetime
from html import escape

import frappe

TRAN_TEM = 200

C39 = {
	"0": "nnnwwnwnn", "1": "wnnwnnnnw", "2": "nnwwnnnnw", "3": "wnwwnnnnn", "4": "nnnwwnnnw",
	"5": "wnnwwnnnn", "6": "nnwwwnnnn", "7": "nnnwnnwnw", "8": "wnnwnnwnn", "9": "nnwwnnwnn",
	"A": "wnnnnwnnw", "B": "nnwnnwnnw", "C": "wnwnnwnnn", "D": "nnnnwwnnw", "E": "wnnnwwnnn",
	"F": "nnwnwwnnn", "G": "nnnnnwwnw", "H": "wnnnnwwnn", "I": "nnwnnwwnn", "J": "nnnnwwwnn",
	"K": "wnnnnnnww", "L": "nnwnnnnww", "M": "wnwnnnnwn", "N": "nnnnwnnww", "O": "wnnnwnnwn",
	"P": "nnwnwnnwn", "Q": "nnnnnnwww", "R": "wnnnnnwwn", "S": "nnwnnnwwn", "T": "nnnnwnwwn",
	"U": "wwnnnnnnw", "V": "nwwnnnnnw", "W": "wwwnnnnnn", "X": "nwnnwnnnw", "Y": "wwnnwnnnn",
	"Z": "nwwnwnnnn", "-": "nwnnnnwnw", ".": "wwnnnnwnn", "*": "nwnnwnwnn",
}


def so_tem(n):
	"""Số tem in: ít nhất 1, nhiều nhất TRAN_TEM, chữ rác thành 1."""
	try:
		n = int(float(n))
	except (TypeError, ValueError):
		return 1
	return max(1, min(TRAN_TEM, n))


def chu_bao_quan(bq):
	return {
		"Freeze": "BẢO QUẢN ĐÔNG -18°C",
		"Chill": "BẢO QUẢN MÁT 0 - 5°C",
		"Room Temp": "NƠI KHÔ RÁO, THOÁNG MÁT",
	}.get(bq or "", "")


def han_dung(nsx, han_gio=0, han_ngay=0):
	"""Hạn dùng tính từ lúc in, CÙNG LUẬT với màn xem trước trong app.

	Có số giờ hạn dùng thì cộng giờ (ghi cả giờ). Không có thì cộng ngày,
	giữ giờ của NSX. Không khai gì thì trả None (tem in dấu gạch).
	"""
	try:
		han_gio = float(han_gio or 0)
	except (TypeError, ValueError):
		han_gio = 0
	try:
		han_ngay = int(han_ngay or 0)
	except (TypeError, ValueError):
		han_ngay = 0
	if han_gio > 0:
		return nsx + datetime.timedelta(hours=han_gio)
	if han_ngay > 0:
		return nsx + datetime.timedelta(days=han_ngay)
	return None


def ma_vach_svg(chuoi):
	"""Mã vạch Code 39 dạng SVG, cùng cách vẽ với tem cũ (không cần font)."""
	gia_tri = "*" + "".join(c for c in (chuoi or "").upper() if c in C39 and c != "*") + "*"
	x, vach = 20, []
	for ch in gia_tri:
		mau = C39[ch]
		for i in range(9):
			rong = 5 if mau[i] == "w" else 2
			if i % 2 == 0:
				vach.append('<rect x="%d" y="0" width="%d" height="100"/>' % (x, rong))
			x += rong
		x += 2
	tong = x + 18
	return ('<svg class="b39s" width="%smm" height="8mm" viewBox="0 0 %d 100" '
		'preserveAspectRatio="none">%s</svg>') % (round(tong * 0.15, 2), tong, "".join(vach))


def du_lieu_tem(mon, bay_gio, lenh="", n=1):
	"""Gom mọi chữ in trên tem. `mon` là dict hồ sơ Món."""
	hsd = han_dung(bay_gio, mon.get("custom_han_dung_gio"), mon.get("shelf_life_in_days"))
	co_gio = bool(float(mon.get("custom_han_dung_gio") or 0) > 0)
	return {
		"ten": mon.get("item_name") or mon.get("name") or "",
		"ma": mon.get("name") or "",
		"klt": mon.get("custom_khoi_luong_tinh") or "",
		"di_ung": mon.get("custom_chat_gay_di_ung") or "",
		"bao_quan": chu_bao_quan(mon.get("custom_dieu_kien_bao_quan")),
		"nsx_gio": bay_gio.strftime("%H:%M"),
		"nsx_ngay": bay_gio.strftime("%d/%m/%Y"),
		"hsd_gio": hsd.strftime("%H:%M") if (hsd and co_gio) else "",
		"hsd_ngay": hsd.strftime("%d/%m/%Y") if hsd else "",
		"lenh": lenh or "",
		"n": so_tem(n),
	}


CSS = """
@page { size: 62mm 45mm; margin: 0; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { margin: 0; padding: 0; background: #fff; }
.tem { width: 62mm; height: 45mm; padding: 1.6mm 2mm; display: flex; flex-direction: column;
  background: #fff; color: #000; font-family: 'DejaVu Sans', Arial, Helvetica, sans-serif;
  overflow: hidden; page-break-after: always; break-after: page; }
.tem:last-child { page-break-after: auto; break-after: auto; }
.tem > * { flex: none; }
.tn { font-size: 9.5pt; font-weight: 700; line-height: 1.1; max-height: 7.4mm; overflow: hidden; }
.sub { display: flex; align-items: center; gap: 1.4mm; margin-top: .6mm; overflow: hidden; }
.kl { font-size: 6.4pt; white-space: nowrap; }
.bq { font-size: 6.4pt; font-weight: 700; border: .3mm solid #000; border-radius: .8mm; padding: .2mm 1.2mm; white-space: nowrap; }
.alg { font-size: 5.2pt; line-height: 1.1; margin-top: .4mm; max-height: 2.4mm; overflow: hidden; }
.bxs { display: flex; flex-direction: column; gap: .6mm; margin-top: .6mm; }
.bx { border: .45mm solid #000; border-radius: 1.4mm; display: flex; align-items: stretch; overflow: hidden; }
.bx .k { display: flex; align-items: center; font-size: 7pt; font-weight: 800; padding: 0 1.6mm; background: #000; color: #fff; }
.bx .v { flex: 1; display: flex; align-items: center; justify-content: center; padding: .2mm 1.2mm; font-size: 8pt; font-weight: 700; }
.warn { font-size: 5pt; line-height: 1.1; margin-top: .4mm; text-align: center; white-space: nowrap; overflow: hidden; }
.bc { margin-top: auto; text-align: center; }
.b39s { display: block; margin: .2mm auto 0; max-width: 58mm; height: 5mm; }
.ngay { font-size: 7pt; font-weight: 700; margin-top: .3mm; }
.ft { display: flex; justify-content: space-between; font-size: 5.6pt; opacity: .85; margin-top: .3mm; }
"""


def html_tem(d):
	"""HTML đầy đủ của N tem. Mọi chữ lấy từ dữ liệu đều được thoát."""
	e = lambda s: escape(str(s or ""))
	nsx = (e(d["nsx_gio"]) + " " + e(d["nsx_ngay"])).strip()
	hsd = ((e(d["hsd_gio"]) + " ") if d["hsd_gio"] else "") + (e(d["hsd_ngay"]) or "-")
	sub = ""
	if d["klt"]:
		sub += '<span class="kl">KL tịnh %s</span>' % e(d["klt"])
	if d["bao_quan"]:
		sub += '<span class="bq">%s</span>' % e(d["bao_quan"])
	alg = '<div class="alg"><b>Dị ứng:</b> %s</div>' % e(d["di_ung"]) if d["di_ung"] else ""
	vach = ma_vach_svg(d["ma"])
	mot = []
	for i in range(1, d["n"] + 1):
		mot.append(
			'<div class="tem"><div class="tn">%s</div><div class="sub">%s</div>%s'
			'<div class="bxs"><div class="bx"><div class="k">NSX</div><div class="v">%s</div></div>'
			'<div class="bx"><div class="k">HSD</div><div class="v">%s</div></div></div>'
			'<div class="warn">Không dùng khi bao bì hư hỏng hoặc đã quá HSD</div>'
			'<div class="bc">%s</div>'
			'<div class="ngay">Ngày: ............................</div>'
			'<div class="ft"><span>The Vagabond Pâtisserie · %s</span><span>%s%s/%s</span></div></div>'
			% (e(d["ten"]), sub, alg, nsx, hsd, vach, e(d["ma"]),
				(e(d["lenh"]) + " · ") if d["lenh"] else "", i, d["n"])
		)
	return ('<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8">'
		'<title>Tem HACCP</title><style>%s</style></head><body>%s'
		# Cua so trinh duyet thi tu bung hop in; duong in ngam QZ cat bo
		# trigger_print truoc khi chup nen khong bung gi.
		'<script>if(/[?&]trigger_print=1/.test(location.search))'
		'window.addEventListener("load",function(){window.print();});</script>'
		'</body></html>'
		% (CSS, "".join(mot)))


# ------------------------------------------------------------ cham he
#
# Tra HTML tho qua /api/method: Frappe tra thang doi tuong Response cua
# werkzeug ra ngoai, khong boc vao JSON. Nho vay mot duong dan dung duoc cho
# ca hai loi in: cua so trinh duyet va chup anh in ngam qua QZ Tray.

TRUONG_MON = ["name", "item_name", "shelf_life_in_days", "custom_han_dung_gio",
	"custom_dieu_kien_bao_quan", "custom_khoi_luong_tinh", "custom_chat_gay_di_ung"]
# O chuan cua ERPNext luon co; o tu them (custom_) chi doc khi site co that.
# Codex #421: tren site chua tao custom_khoi_luong_tinh hay
# custom_chat_gay_di_ung thi get_value bao loi cot la, MOI lan in tem hong.
TRUONG_CHUAN = {"name", "item_name", "shelf_life_in_days"}


def truong_doc_duoc(co_truong):
	"""THUAN. Loc TRUONG_MON con nhung o site that su co."""
	return [f for f in TRUONG_MON if f in TRUONG_CHUAN or co_truong(f)]


@frappe.whitelist()
def trang(ma=None, lenh=None, n=1):
	from frappe.utils import now_datetime
	from werkzeug.wrappers import Response

	if frappe.session.user == "Guest":
		frappe.throw("Đăng nhập rồi mới in tem.", frappe.PermissionError)
	if lenh:
		if not frappe.has_permission("Work Order", "read", lenh):
			frappe.throw("Không có quyền xem lệnh %s." % lenh, frappe.PermissionError)
		ma = ma or frappe.db.get_value("Work Order", lenh, "production_item")
	if not ma or not frappe.db.exists("Item", ma):
		frappe.throw("Không tìm thấy món để in tem.")
	meta = frappe.get_meta("Item")
	mon = frappe.db.get_value("Item", ma, truong_doc_duoc(meta.has_field), as_dict=True) or {}
	d = du_lieu_tem(mon, now_datetime(), lenh or "", n)
	return Response(html_tem(d), mimetype="text/html")
