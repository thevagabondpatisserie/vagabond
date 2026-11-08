# -*- coding: utf-8 -*-
"""Thanh toán ngay trên web cho đơn đặt bánh (v638), phần chạm hệ.

Anh Việt 04/11/2026: khách đặt bánh trên web thanh toán NGAY trên web, không
phải nhắn Zalo chờ Sales gửi hướng dẫn. Phần thuần (nhãn, phép tính số tiền,
nội dung chuyển khoản, phép khớp sao kê, thân PUT Pancake, tin Zalo) nằm ở
thanh_toan_web_thuan.py.

Dòng tiền
---------
- Chuyển khoản: biên nhận hiện VietQR đúng số tiền vào tài khoản nhận như các
  luồng QR khác, nội dung là chuỗi mà `ban_hang._sepay_theo_don` đã nhận ra
  (S<shop>O<mã Pancake>T) cộng mã Don Web. Khách hỏi trạng thái (trang biên
  nhận mỗi 5 giây) hay nhịp 5 phút thì máy khớp sao kê SePay của ĐÚNG đơn đó.
- Thẻ (quốc tế, ATM nội địa): giao dịch OnePay loại thứ ba, mã giao dịch là mã
  Don Web bỏ gạch nối số lần (DW261100123-1), nhật ký trên ô ẩn vgb_onepay_gd
  của Vagabond Don Web. Trang /tra-the, IPN và lượt quét 15 phút dùng chung cửa
  onepay.py (định tuyến sang đây theo mã).
- Tiền mặt: không đổi gì.

Khi đã thu đủ: ghi trạng thái, số tiền, cách, mã giao dịch lên Don Web (ô mới,
không đụng KHONG_DOI), ghi số đã trả lên đơn Pancake (transfer_money hoặc
prepaid, đọc lại để chắc Pancake nhận) để COD giảm đúng, rồi báo nhóm Sales
(bh_don_web_da_tra). KHÔNG lập Payment Entry: tiền đơn Pancake vào sổ qua
phương thức trên hoá đơn đồng bộ (Chuyển khoản qua chốt `_soat_sepay`, OnePay
không có chốt chặn), giống mọi đơn Pancake khác. Lập thêm phiếu thu ở đây là
ghi tiền hai lần khi hoá đơn ghi sổ.
"""

import json
import re

import frappe
from frappe.utils import add_to_date, cint, flt, now_datetime

from vagabond import thanh_toan_web_thuan as ttt

try:
	import requests  # noqa: F401
except ImportError:  # CI tay không
	requests = None

try:
	from frappe.rate_limiter import rate_limit
except ImportError:  # Frappe giả của bộ kiểm tầng khung
	def rate_limit(**_kw):
		return lambda f: f

DT = "Vagabond Don Web"
O_NK = "vgb_onepay_gd"
O_TAT_PANCAKE = "web_tt_khong_ghi_pancake"

TRUONG_MOI = {
	DT: [
		{"fieldname": "vgb_sec_tt", "label": "Thanh toán online", "fieldtype": "Section Break",
			"insert_after": "da_bao_sales_luc", "collapsible": 0},
		{"fieldname": "vgb_tt_trang_thai", "label": "Thu online", "fieldtype": "Select",
			"options": "\nThu thieu\nDa thu", "insert_after": "vgb_sec_tt", "read_only": 1, "no_copy": 1,
			"in_standard_filter": 1,
			"description": "Máy ghi khi khách chuyển khoản (SePay khớp) hoặc trả thẻ OnePay thành công."},
		{"fieldname": "vgb_tt_da_thu", "label": "Số đã thu online", "fieldtype": "Currency",
			"insert_after": "vgb_tt_trang_thai", "read_only": 1, "no_copy": 1},
		{"fieldname": "vgb_tt_cach", "label": "Cách thu online", "fieldtype": "Data",
			"insert_after": "vgb_tt_da_thu", "read_only": 1, "no_copy": 1,
			"description": "Chuyển khoản hoặc OnePay, đúng tên phương thức thanh toán trên hoá đơn."},
		{"fieldname": "vgb_tt_luc", "label": "Lúc thu đủ", "fieldtype": "Datetime",
			"insert_after": "vgb_tt_cach", "read_only": 1, "no_copy": 1},
		{"fieldname": "vgb_cb_tt", "fieldtype": "Column Break", "insert_after": "vgb_tt_luc"},
		{"fieldname": "vgb_tt_ma_gd", "label": "Giao dịch đã ghi nhận", "fieldtype": "Small Text",
			"insert_after": "vgb_cb_tt", "read_only": 1, "no_copy": 1,
			"description": "Dòng sao kê SePay hoặc mã giao dịch OnePay đã tính cho đơn này."},
		{"fieldname": "vgb_tt_pancake", "label": "Ghi lên Pancake", "fieldtype": "Data",
			"insert_after": "vgb_tt_ma_gd", "read_only": 1, "no_copy": 1,
			"description": "da_ghi: COD trên Pancake đã giảm; tien_mat: COD đã giảm nhưng Pancake xếp vào Tiền mặt, Sales đổi sang OnePay; loi hoặc tat: Sales ghi tay số đã trả."},
		{"fieldname": "vgb_tt_bao_luc", "label": "Đã báo Sales lúc", "fieldtype": "Datetime",
			"insert_after": "vgb_tt_pancake", "read_only": 1, "no_copy": 1},
		{"fieldname": O_NK, "label": "Nhật ký thẻ OnePay", "fieldtype": "Long Text",
			"insert_after": "vgb_tt_bao_luc", "read_only": 1, "hidden": 1, "no_copy": 1},
	],
	"Vagabond Settings": [
		{"fieldname": O_TAT_PANCAKE, "label": "Tạm không ghi tiền đơn web đã trả lên Pancake", "fieldtype": "Check",
			"insert_after": "onepay_query_password", "default": "0",
			"description": "Mặc định máy ghi số khách đã trả online (chuyển khoản, thẻ) lên đơn Pancake để COD giảm. "
				"Bật ô này khi Pancake từ chối; Sales nhận tin và ghi tay."},
	],
}

F_DOC = ["name", "trang_thai", "thanh_toan", "tien_banh", "trang_thai_phi", "snapshot", "creation",
	"pancake_id", "pancake_display_id", "vgb_tt_trang_thai", "vgb_tt_da_thu", "vgb_tt_cach",
	"vgb_tt_ma_gd", "vgb_tt_pancake", "vgb_tt_bao_luc", O_NK]


def _snap(d):
	try:
		return json.loads((d or {}).get("snapshot") or "{}")
	except (TypeError, ValueError):
		return {}


def _doc(ten, khoa=False):
	return frappe.db.get_value(DT, ten, F_DOC, as_dict=True, for_update=khoa)


def _shop():
	from vagabond.lib import cfg

	try:
		return str(cfg().pancake_shop_id or "").strip()
	except Exception:
		return ""


def _tk():
	"""Tài khoản nhận tiền đơn web: cùng bảng tài khoản như các luồng QR khác
	(nguồn Pancake, rỗng thì tài khoản mặc định)."""
	from vagabond import tai_khoan

	return tai_khoan.tk_cho("Pancake")


def _onepay_dung():
	from vagabond import onepay as op

	return op.dung_duoc()


def khoi_thanh_toan(d, snap=None):
	"""Khối thanh toán đầy đủ cho biên nhận (cả hai bản trang): phần thuần cộng
	tài khoản, mã QR, khoá trang thẻ. Lỗi đọc cấu hình không làm hỏng biên nhận."""
	snap = snap if snap is not None else _snap(d)
	pt = ttt.chuan_pt((d or {}).get("thanh_toan") or snap.get("thanh_toan"))
	k = ttt.khoi_bien_nhan(pt, ttt.tien_ban_ghi(d, snap), d.get("vgb_tt_trang_thai"), d.get("vgb_tt_da_thu"),
		d.get("vgb_tt_cach"), d.get("trang_thai") == "Da huy")
	if k["trang_thai"] not in ("cho", "thieu"):
		return k
	try:
		if pt in ttt.CARD_LIST:
			if _onepay_dung():
				from vagabond import onepay as op

				ma = ttt.ma_dw(d.get("name"))
				k["the"] = {"ma": ma, "k": op.khoa_phieu(ma), "duong": op.duong_trang(ma, op.khoa_phieu(ma))}
				return k
			# Cổng thẻ vừa tắt sau khi khách đặt: cho chuyển khoản thay, không bỏ khách đứng đó.
			k["the_tat"] = 1
		from vagabond import cong_no, qr_chuyen_khoan

		tk = _tk()
		nd = ttt.noi_dung_ck(_shop(), d.get("name"), d.get("pancake_display_id"))
		k["ck"] = {"ngan_hang": cong_no.TEN_NGAN_HANG_DAY_DU.get(tk.get("bank") or "", tk.get("bank") or ""),
			"stk": tk.get("stk") or "", "ten": tk.get("ten") or "", "noi_dung": nd,
			"anh": qr_chuyen_khoan.anh_qr(tk, k["con"], nd)}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thanh_toan_web: khối thanh toán biên nhận")
	return k


# ------------------------------------------------------------ chuyển khoản

def _gd_sao_ke(d):
	"""Dòng tiền vào trong sao kê có thể là của đơn này (sơ lọc bằng SQL, lọc
	thật bằng ttt.mo_ta_khop). Chỉ đọc từ một ngày trước lúc đặt đơn."""
	mau = ttt.mau_khop(_shop(), d["name"], d.get("pancake_display_id"))
	if not mau:
		return []
	tu = add_to_date(d["creation"], days=-1)
	return frappe.db.sql(
		"""select name, description, deposit, withdrawal, reference_number
		from `tabBank Transaction`
		where docstatus < 2 and deposit > 0 and date >= %s and description regexp %s
		order by name""", (str(tu)[:10], mau), as_dict=True)


def _gd_don_khac_da_dung(ten_gd, tru):
	"""Trong các dòng sao kê đã cho, dòng nào đã được Don Web KHÁC ghi nhận."""
	ra = set()
	for g in ten_gd or []:
		if frappe.db.sql("select name from `tab%s` where name != %%s and vgb_tt_ma_gd like %%s limit 1" % DT,
				(tru, '%%"%s"%%' % g)):
			ra.add(g)
	return ra


def _bao_ck_nhieu_don(d, mo_ho):
	"""Báo Sales đối soát tay giao dịch mang mã nhiều đơn; mỗi giao dịch một lần."""
	from vagabond.kenh_zalo import bao

	for x in mo_ho:
		tieu_de, dong = ttt.tin_ck_nhieu_don(d.name, d.pancake_display_id, x["ma_khac"])
		bao("canh_bao", "don_web", tieu_de, dong, khoa="don-web-ck-nhieu-don:%s:%s" % (d.name, x["gd"]),
			link=frappe.utils.get_url_to_form(DT, d.name), ma_tin="bh_don_web_da_tra")


def khop_ck(ten):
	"""Khớp sao kê cho một đơn chọn chuyển khoản, trong khoá hàng Don Web (nhịp
	5 phút và lượt khách hỏi trạng thái có thể chạy cùng lúc). Trả trạng thái
	thu mới hoặc rỗng khi không đổi. Bên gọi commit (hàm tự commit khi đổi)."""
	d = _doc(ten, khoa=True)
	if not d or d.trang_thai == "Da huy" or d.vgb_tt_trang_thai == ttt.TT_DA_THU:
		return ""
	if ttt.chuan_pt(d.thanh_toan) not in QUET_CACH:
		return ""
	snap = _snap(d)
	so_can = ttt.so_tien_online(d, snap)
	gds = _gd_sao_ke(d)
	ten_gd = sorted({str(g.get("name")) for g in gds if g.get("name")})
	# Codex PR #541: giữ khoá các dòng sao kê (thứ tự tên cố định, sau khoá Don
	# Web) rồi mới đọc đơn nào đã dùng chúng, để hai đơn không cùng ăn một khoản.
	for g in ten_gd:
		frappe.db.sql("select name from `tabBank Transaction` where name = %s for update", (g,))
	kq = ttt.tong_khop(gds, _shop(), d.name, d.pancake_display_id, _gd_don_khac_da_dung(ten_gd, d.name))
	if kq["mo_ho"]:
		_bao_ck_nhieu_don(d, kq["mo_ho"])
	# Đơn chọn thẻ mà đã trả một phần bằng thẻ thì cộng phần thẻ với phần chuyển khoản.
	the = [g for g in ttt.doc_ds_gd(d.vgb_tt_ma_gd) if g.get("loai") == "the"]
	nhan = kq["nhan"] + sum(flt(g.get("so")) for g in the)
	tt = ttt.xet_thu(so_can, nhan)
	if not tt or (tt == (d.vgb_tt_trang_thai or "") and abs(nhan - flt(d.vgb_tt_da_thu)) < 0.5):
		return ""
	ds = the + [dict(g, loai="ck") for g in kq["gd"]]
	gia_tri = {"vgb_tt_trang_thai": tt, "vgb_tt_da_thu": nhan, "vgb_tt_ma_gd": json.dumps(ds, ensure_ascii=False)}
	gia_tri["vgb_tt_cach"] = ttt.cach_tu_ds(ds, ttt.PT_SO["bank"])
	if tt == ttt.TT_DA_THU:
		gia_tri["vgb_tt_luc"] = now_datetime()
	frappe.db.set_value(DT, ten, gia_tri, update_modified=False)
	frappe.db.commit()
	if tt == ttt.TT_DA_THU:
		sau_thu(ten)
	return tt


# ------------------------------------------------------------ sau khi thu đủ

def _pancake_khoa():
	from vagabond.lib import cfg, key

	c = cfg()
	return c, key(c, "pancake_api_key")


def _doc_don_pancake(c, k, pid):
	from vagabond.lib import PANCAKE, TIMEOUT

	r = requests.get("%s/shops/%s/orders/%s" % (PANCAKE, c.pancake_shop_id, pid), params={"api_key": k}, timeout=TIMEOUT)
	if r.status_code != 200:
		raise ValueError("Pancake trả HTTP %s khi đọc đơn %s." % (r.status_code, pid))
	return (r.json() or {}).get("data") or {}


def _put_don_pancake(c, k, pid, than):
	from vagabond.lib import PANCAKE, TIMEOUT

	r = requests.put("%s/shops/%s/orders/%s" % (PANCAKE, c.pancake_shop_id, pid), params={"api_key": k},
		json=than, timeout=TIMEOUT)
	if r.status_code not in (200, 201):
		raise ValueError("Pancake trả HTTP %s khi ghi đơn %s: %s" % (r.status_code, pid, (r.text or "")[:300]))


def ghi_pancake(d):
	"""Ghi số khách đã trả lên đơn Pancake. Trả mã kết quả (ttt.CAU_PANCAKE).
	Lỗi KHÔNG làm hỏng ghi nhận tiền: chỉ ghi Error Log, tin Sales nói ghi tay."""
	from vagabond.lib import cfg_o

	if cint(cfg_o(O_TAT_PANCAKE)):
		return "tat"
	pid = str(d.get("pancake_id") or "").strip()
	if not pid:
		return "cho_ma_don"
	try:
		if requests is None:
			raise RuntimeError("Thiếu thư viện requests.")
		c, k = _pancake_khoa()
		if not (k and c.pancake_shop_id):
			raise ValueError("Chưa điền khoá Pancake.")
		don = _doc_don_pancake(c, k, pid)
		than = ttt.than_pancake_ds(ttt.doc_ds_gd(d.get("vgb_tt_ma_gd")), d.get("vgb_tt_cach"), d.get("vgb_tt_da_thu"), don)
		if not than:
			return "da_co"
		_put_don_pancake(c, k, pid, than)
		sau = _doc_don_pancake(c, k, pid)
		if not ttt.da_ghi_pancake(sau, than):
			raise ValueError("Pancake nhận lệnh nhưng đơn %s chưa mang %s." % (pid, than))
		if ttt.the_vao_tien_mat(don, sau, than):
			# v645: COD đã đúng; chỉ hình thức sai, tin Sales nói đổi tay.
			return "tien_mat"
		return "da_ghi"
	except Exception:
		from vagabond.lib import giau_khoa

		try:
			tb = giau_khoa(frappe.get_traceback())
		except Exception:
			tb = "(không đọc được vết lỗi)"
		frappe.log_error(tb, "thanh_toan_web: ghi tiền lên Pancake %s" % d.get("name"))
		return "loi"


def sau_thu(ten):
	"""Việc sau khi đơn đã thu đủ: ghi Pancake, báo nhóm Sales. Chạy một lần
	(đóng dấu vgb_tt_bao_luc); hỏng giữa chừng thì nhịp 5 phút làm lại. Lỗi chỉ
	ghi Error Log: tiền đã ghi nhận rồi, không được làm hỏng lượt gọi (IPN)."""
	try:
		d = _doc(ten)
		if not d or d.vgb_tt_trang_thai != ttt.TT_DA_THU or d.vgb_tt_bao_luc:
			return
		kq = ghi_pancake(d)
		tien = ttt.tien_ban_ghi(d, _snap(d))
		frappe.db.set_value(DT, ten, {"vgb_tt_pancake": kq, "vgb_tt_bao_luc": now_datetime()}, update_modified=False)
		from vagabond.kenh_zalo import bao

		tieu_de, dong = ttt.tin_da_tra(ten, d.pancake_display_id, d.vgb_tt_cach, tien["phi_sau"], kq)
		bao("thong_bao", "don_web", tieu_de, dong, khoa="don-web-da-tra:%s" % ten,
			link=frappe.utils.get_url_to_form(DT, ten), ma_tin="bh_don_web_da_tra")
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "thanh_toan_web: báo đã thu %s" % ten)


def _ghi_pancake_sau(ten):
	"""Đơn đã báo Sales lúc chưa có mã Pancake: có mã rồi thì ghi tiền lên đơn.
	Hỏng thì báo Sales một lần (tin cùng mã, khoá riêng)."""
	d = _doc(ten)
	if not d or d.vgb_tt_pancake != "cho_ma_don" or not d.pancake_id:
		return
	kq = ghi_pancake(d)
	frappe.db.set_value(DT, ten, "vgb_tt_pancake", kq, update_modified=False)
	if kq == "loi":
		from vagabond.kenh_zalo import bao

		bao("canh_bao", "don_web", "Đơn web %s đã trả online, chưa ghi được lên Pancake" % (d.pancake_display_id or ten),
			["Khách đã trả online qua %s." % ttt.NHAN_CACH_THU.get(d.vgb_tt_cach, d.vgb_tt_cach), ttt.CAU_PANCAKE["loi"]], khoa="don-web-pancake-loi:%s" % ten,
			link=frappe.utils.get_url_to_form(DT, ten), ma_tin="bh_don_web_da_tra")
	frappe.db.commit()


QUET_CACH = ("bank", "card", "atm")


def quet():
	"""Nhịp 5 phút: khớp sao kê cho đơn chọn chuyển khoản chưa thu đủ (3 ngày
	gần nhất), làm nốt việc sau thu cho đơn đã thu mà chưa báo, ghi Pancake cho
	đơn vừa có mã. Mỗi đơn tự chịu lỗi của mình."""
	if getattr(frappe.flags, "vagabond_kiem_that", False):
		return
	tu = add_to_date(now_datetime(), days=-3)
	try:
		# Codex PR #541 vòng 3: đơn chọn thẻ mà cổng OnePay tắt thì biên nhận hiện
		# VietQR cho khách chuyển khoản thay; nhịp quét phải xét cả đơn thẻ.
		ds = frappe.get_all(DT, filters={"thanh_toan": ["in", list(QUET_CACH)], "trang_thai": ["!=", "Da huy"],
			"vgb_tt_trang_thai": ["!=", ttt.TT_DA_THU], "creation": [">=", tu]},
			pluck="name", order_by="creation asc", limit_page_length=0, ignore_permissions=True)
		bao = frappe.get_all(DT, filters={"vgb_tt_trang_thai": ttt.TT_DA_THU, "vgb_tt_bao_luc": ["is", "not set"],
			"creation": [">=", tu]}, pluck="name", limit_page_length=0, ignore_permissions=True)
		cho = frappe.get_all(DT, filters={"vgb_tt_pancake": "cho_ma_don", "pancake_id": ["is", "set"],
			"creation": [">=", tu]}, pluck="name", limit_page_length=0, ignore_permissions=True)
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "thanh_toan_web: quét đơn chờ tiền")
		return
	for ham, cac in ((khop_ck, ds), (sau_thu, bao), (_ghi_pancake_sau, cho)):
		for ten in cac:
			try:
				ham(ten)
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
				frappe.log_error(frappe.get_traceback(), "thanh_toan_web: %s %s" % (ham.__name__, ten))


# ------------------------------------------------------------ cửa khách hỏi

@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=150, seconds=600)
def trang_thai(token):
	"""Biên nhận hỏi lại mỗi 5 giây: đơn đã nhận tiền chưa. Cần token biên nhận
	(chỉ người cầm đường dẫn mới hỏi được). Hỏi xong máy thử khớp sao kê của
	đúng đơn đó. Chỉ trả khối thanh toán, không tên, không số điện thoại."""
	from vagabond import don_web

	if not don_web.token_hop_le(token):
		frappe.throw("Không tìm thấy đơn.")
	ten = frappe.db.get_value(DT, {"token_hash": don_web.bam(token)}, "name")
	if not ten:
		frappe.throw("Không tìm thấy đơn.")
	try:
		khop_ck(ten)
	except Exception as e:
		from vagabond.loi_csdl import chet_giao_dich

		frappe.db.rollback()
		if chet_giao_dich(e):
			raise
		frappe.log_error(frappe.get_traceback(), "thanh_toan_web: khớp khi khách hỏi")
	return khoi_thanh_toan(_doc(ten))


def tien_cho_hoa_don(pid, did):
	"""Đơn web ứng với một hoá đơn Pancake (theo mã Pancake), kèm số đã thu
	online. Rỗng khi không phải đơn web hay chưa thu gì."""
	ma = [str(x).strip() for x in (did, pid) if str(x or "").strip()]
	if not ma:
		return {}
	ten = (frappe.db.get_value(DT, {"pancake_display_id": ["in", ma]}, "name")
		or frappe.db.get_value(DT, {"pancake_id": ["in", ma]}, "name"))
	if not ten:
		return {}
	d = _doc(ten)
	if not d or not d.vgb_tt_trang_thai:
		return {}
	r = dict(d)
	r["phi_sau"] = ttt.tien_ban_ghi(d, _snap(d))["phi_sau"]
	return r


def pt_hoa_don(pid, did):
	"""(phương thức, mã tham chiếu) cho hoá đơn đồng bộ của đơn web đã trả đủ
	online. Đọc hỏng thì rỗng: không được làm hỏng nhịp đồng bộ."""
	try:
		return ttt.pt_cho_hoa_don(tien_cho_hoa_don(pid, did))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thanh_toan_web: phương thức hoá đơn đơn web")
		return "", ""


def ck_hoa_don(pid, did):
	"""Tiền chuyển khoản đã khớp cho đơn web (kể cả nội dung theo mã Don Web mà
	`_sepay_theo_don` không thấy), cho chốt `_soat_sepay`. {"nhan", "ma"}."""
	try:
		r = tien_cho_hoa_don(pid, did)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thanh_toan_web: tiền chuyển khoản cho hoá đơn")
		return {}
	ck = [g for g in ttt.doc_ds_gd((r or {}).get("vgb_tt_ma_gd")) if g.get("loai") == "ck"]
	if not ck:
		return {}
	return {"nhan": sum(flt(g.get("so")) for g in ck), "ma": next((g.get("ma") for g in ck if g.get("ma")), ""),
		"gd": [g.get("gd") for g in ck]}


# ------------------------------------------------------------ thẻ OnePay

def la_ma_don(ma):
	return ttt.la_ma_dw(ma)


def tim_don(ma, k):
	"""Mã trên đường dẫn + khoá -> tên Don Web. Sai khoá thì như không có."""
	import hmac

	from vagabond import onepay as op

	ma = re.sub(r"[^A-Z0-9]", "", str(ma or "").upper())
	if not la_ma_don(ma) or not isinstance(k, str) or not re.fullmatch(r"[0-9a-f]{16}", k):
		return None
	ten = ttt.ten_dw(ma)
	if not ten or not frappe.db.exists(DT, ten) or not hmac.compare_digest(op.khoa_phieu(ma), k):
		return None
	return ten


def _con(d):
	"""Số còn phải trả online (0 khi huỷ hoặc đã thu đủ)."""
	if d.trang_thai == "Da huy" or d.vgb_tt_trang_thai == ttt.TT_DA_THU:
		return 0.0
	return max(0.0, float(ttt.so_tien_online(d, _snap(d))) - flt(d.vgb_tt_da_thu))


def thong_tin_trang(ma, k):
	"""Dữ liệu trang /tra-the cho một đơn web (cùng khuôn phiếu công nợ). Tên
	khách viết tắt như biên nhận."""
	from vagabond import don_web
	from vagabond import onepay as op

	ten = tim_don(ma, k)
	if not ten:
		return None
	d = _doc(ten)
	snap = _snap(d)
	return {"ten": ten, "ma_phieu": ten, "loai": "don_web", "tieu_de": "Đơn đặt bánh", "xem_lai": 1,
		"khach": don_web.viet_tat_ten((snap.get("nguoi_dat") or {}).get("ho_ten")),
		"tong": float(ttt.so_tien_online(d, snap)), "con": _con(d), "huy": d.trang_thai == "Da huy",
		"dung_duoc": op.dung_duoc()}


def tao_gd(ma, k):
	"""Khách bấm "Thanh toán bằng thẻ": một giao dịch mới cho SỐ CÒN PHẢI TRẢ
	đọc ở máy chủ trong khoá hàng Don Web; loại thẻ theo cách khách đã chọn."""
	from vagabond import onepay as op

	ten = tim_don(ma, k)
	if not ten:
		frappe.throw("Không tìm thấy đơn đặt bánh.")
	c = op.cau_hinh()
	if not op.dung_duoc(c):
		frappe.throw("Thanh toán thẻ đang tạm ngưng. Quý khách vui lòng chuyển khoản theo mã trên biên nhận.")
	d = _doc(ten, khoa=True)
	if d.trang_thai == "Da huy":
		frappe.throw("Đơn này đã huỷ. Quý khách liên hệ The Vagabond để được hỗ trợ.")
	con = _con(d)
	if con < 1:
		frappe.throw("Đơn này đã được thanh toán. Cảm ơn quý khách.")
	if con < op.TIEN_TOI_THIEU:
		frappe.throw("Số còn lại dưới 10.000 đ nên không trả bằng thẻ được. Quý khách vui lòng chuyển khoản.")
	nk = op.doc_nhat_ky(d.get(O_NK))
	lan = op.lan_tiep(nk)
	if lan > op.SO_LAN_TOI_DA:
		frappe.throw("Đơn này đã thử thanh toán thẻ quá nhiều lần. Quý khách vui lòng chuyển khoản hoặc liên hệ The Vagabond.")
	ma_ngan = ttt.ma_dw(ten)
	ma_moi = op.ma_gd(ma_ngan, lan)
	from vagabond.ten_mien import link_khach

	duong = link_khach(op.duong_trang(ma_ngan, op.khoa_phieu(ma_ngan)))
	ts = op.tham_so_tra(c, ma_moi, con, ma_ngan, duong + "&ve=1", getattr(frappe.local, "request_ip", None), duong,
		card_list=ttt.CARD_LIST.get(ttt.chuan_pt(d.thanh_toan)))
	nk.append({"ma": ma_moi, "so_tien": con, "tao_luc": str(now_datetime())[:19], "trang_thai": "cho"})
	frappe.db.set_value(DT, ten, O_NK, json.dumps(nk, ensure_ascii=False), update_modified=False)
	frappe.db.commit()
	return {"url": op.url_tra(c, ts)}


def ghi_nhan_the(ma, kq, nguon):
	"""Ghi một kết quả OnePay (đã đọc, đã kiểm chữ ký) cho đơn web. Lặp lại bao
	nhiêu lần cũng chỉ cộng tiền một lần (nhật ký trong khoá hàng Don Web).
	Trả dư (đơn đã thu đủ chỗ khác, hoặc đã huỷ) thì báo kế toán hoàn."""
	from vagabond import onepay as op

	ten = ttt.ten_dw(ma)
	if not ten or not frappe.db.exists(DT, ten):
		return {"ok": 1, "ly_do": "gd_la", "kq": kq}
	d = _doc(ten, khoa=True)
	nk = op.doc_nhat_ky(d.get(O_NK))
	gd = op.tim_gd(nk, kq["ma"])

	def _luu(gia_tri=None):
		v = {O_NK: json.dumps(nk, ensure_ascii=False)}
		v.update(gia_tri or {})
		frappe.db.set_value(DT, ten, v, update_modified=False)

	if gd and not kq["thanh_cong"]:
		if gd.get("trang_thai") == "cho":
			gd.update(trang_thai="that_bai", ma_kq=kq.get("ma_kq"))
			_luu()
			frappe.db.commit()
		return {"ok": 1, "ly_do": "khong_thanh_cong", "kq": kq}
	ghi, so, ly_do = op.xet_ghi_nhan(gd, kq, _con(d))
	if not ghi:
		return {"ok": 1, "ly_do": ly_do, "kq": kq}
	du = max(0.0, float(kq.get("so_tien") or 0) - so)
	gd.update(trang_thai="da_ghi", ma_onepay=kq.get("ma_onepay"), the=kq.get("the"), so_ghi=so, du=du,
		ghi_luc=str(now_datetime())[:19], nguon=nguon)
	gia_tri = {}
	tt = ""
	if so > 0.5:
		ds = ttt.doc_ds_gd(d.vgb_tt_ma_gd) + [{"gd": kq["ma"], "ma": kq.get("ma_onepay") or "", "so": so, "loai": "the"}]
		da_thu = flt(d.vgb_tt_da_thu) + so
		tt = ttt.xet_thu(ttt.so_tien_online(d, _snap(d)), da_thu)
		gia_tri = {"vgb_tt_trang_thai": tt, "vgb_tt_da_thu": da_thu, "vgb_tt_cach": ttt.cach_tu_ds(ds, ttt.PT_SO["card"]),
			"vgb_tt_ma_gd": json.dumps(ds, ensure_ascii=False)}
		if tt == ttt.TT_DA_THU:
			gia_tri["vgb_tt_luc"] = now_datetime()
	_luu(gia_tri)
	if du > 0.5:
		# Ghi tin TRƯỚC commit (bài học Codex #534 vòng 3: trang về là GET).
		try:
			from vagabond.kenh_zalo import bao
			from vagabond.onepay_dat import tien_vn

			cau = ("Đơn %s đã huỷ trước khi tiền thẻ về: kế toán hoàn %s đ cho khách." % (ten, tien_vn(du))
				if d.trang_thai == "Da huy" else
				"Khách trả dư %s đ (đơn đã được trả ở chỗ khác): kế toán hoàn lại cho khách." % tien_vn(du))
			bao("thong_bao", "cong_no", "Khách trả thẻ OnePay cho đơn web %s, cần hoàn %s đ" % (ten, tien_vn(du)), [
				"Số tiền khách trả: %s đ, mã OnePay %s" % (tien_vn(kq.get("so_tien")), kq.get("ma_onepay") or ""),
				"Đã tính cho đơn: %s đ" % tien_vn(so), cau,
			], khoa="onepay:%s" % kq["ma"], ma_tin="kt_the_onepay")
		except Exception as e:
			from vagabond.loi_csdl import chet_giao_dich

			if chet_giao_dich(e):
				raise
			frappe.log_error(frappe.get_traceback(), "thanh_toan_web: báo hoàn tiền thẻ")
	frappe.db.commit()
	if tt == ttt.TT_DA_THU:
		sau_thu(ten)
	return {"ok": 1, "ly_do": ly_do, "kq": kq}
