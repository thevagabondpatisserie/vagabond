# -*- coding: utf-8 -*-
"""v609: tin Zalo cho phân hệ kho, thu mua, sản xuất và đơn web mới.

Anh Việt 22/10/2026: "phần kho có thêm mấy tin báo cho bộ phận: đã nhập hàng,
đã xuất hàng, điều chuyển... làm cho triệt để; tin liên quan hàng hoá thì phải
có tên hàng hoá". Mẫu tin đã duyệt cùng ngày.

Luật soạn tin (đã duyệt):
  - Tin về hàng hoá kê TÊN HÀNG, số lượng, đơn vị; tối đa TOI_DA_MON dòng rồi
    "+N món khác". Tên kho bỏ đuôi công ty.
  - Số tiền CHỈ xuất hiện ở tin của Thu mua và Kế toán (mã tm_ và kt_); tin cho
    Kho, Bếp, Bán hàng không có tiền.
  - Tin sự kiện (vừa nhập, vừa xuất, vừa chuyển) gửi ngay lúc ghi sổ. Tin gom
    (lô sắp hết hạn, tồn dưới mức, đơn mua trễ hẹn, hàng về chưa hoá đơn) gửi
    theo lịch sáng, mỗi ngày một lần nhờ khoá chống trùng theo ngày.
  - Mỗi hàm phát đúng MỘT mã tin (ca thu_tin_zalo_604 chốt NOI_PHAT); hai tin
    từ cùng một chứng từ thì tách hai hàm, hàm hook chỉ điều phối.

Phần THUẦN (soạn chữ) tách khỏi phần chạm Frappe để kiểm thử không cần site.
Mọi hàm chạm hệ đều nuốt lỗi và ghi Error Log: tin báo không bao giờ được làm
hỏng chứng từ đang ghi sổ.
"""

import re

import frappe
from frappe.utils import add_days, add_to_date, cint, flt, getdate, now_datetime, nowdate

from vagabond import kenh_zalo

TOI_DA_MON = 5
NGAY_SAP_HET_HAN = 3
NGAY_CHO_HOA_DON = 3
GIO_CHUA_NHAN_TU = 2
GIO_CHUA_NHAN_DEN = 48
MUC_DICH_PHUC_VU_BAN = "phuc_vu_ban"

# ----------------------------------------------------------------- THUẦN


def ten_kho(kho):
	"""Bỏ đuôi công ty: "Kho D1 - TV" thành "Kho D1"."""
	t = str(kho or "").strip()
	return re.sub(r"\s*-\s*[A-Z]{1,4}$", "", t) or t


def so(x):
	"""Số lượng gọn: 12, 1.250, 0,5."""
	x = flt(x)
	if abs(x - round(x)) < 0.0005:
		return "{:,.0f}".format(round(x)).replace(",", ".")
	return ("{:,.3f}".format(x).replace(",", "~").replace(".", ",").replace("~", ".")).rstrip("0").rstrip(",")


def tien(x):
	"""Tiền kiểu Việt: 1.234.567 đ."""
	return "{:,.0f}".format(round(flt(x))).replace(",", ".") + " đ"


def ngay_vn(d):
	"""dd/mm từ ngày (date, datetime hay chuỗi ISO); rỗng thì rỗng."""
	if not d:
		return ""
	try:
		d = getdate(d)
	except Exception:
		return str(d)
	return "%02d/%02d" % (d.day, d.month)


def gio_vn(t):
	"""HH:MM dd/mm từ datetime; rỗng thì rỗng."""
	if not t:
		return ""
	try:
		return "%02d:%02d %02d/%02d" % (t.hour, t.minute, t.day, t.month)
	except Exception:
		return str(t)


def dong_hang(ds, toi_da=TOI_DA_MON, them=None):
	"""Mỗi món một dòng "Tên: số đơn vị", tối đa toi_da rồi "+N món khác".

	ds: [{"ten", "sl", "dvt", "ghi"?}]; "ghi" là phần đuôi thêm (lệch, hạn lô).
	them: hàm(d) trả chuỗi đuôi, dùng khi dòng cần thêm lời (ví dụ còn thiếu)."""
	ra = []
	ds = [d for d in (ds or []) if (d.get("ten") or "").strip()]
	for d in ds[:toi_da]:
		dong = "%s: %s" % ((d.get("ten") or "").strip(), " ".join([x for x in (so(d.get("sl")), (d.get("dvt") or "").strip()) if x]))
		duoi = (them(d) if them else d.get("ghi")) or ""
		if duoi:
			dong += " (%s)" % duoi
		ra.append(dong)
	if len(ds) > toi_da:
		ra.append("+%d món khác" % (len(ds) - toi_da))
	return ra


def hang_tu_items(items):
	"""Rút [{"ten","sl","dvt"}] từ dòng chứng từ (dict hay đối tượng Frappe)."""
	ra = []
	for r in items or []:
		g = r.get if hasattr(r, "get") else (lambda k, _r=r: getattr(_r, k, None))
		ra.append({"ten": g("item_name") or g("item_code") or "", "sl": g("qty"), "dvt": g("uom") or g("stock_uom") or "",
			"ma": g("item_code") or "", "lo": g("batch_no") or "", "goc": g("purchase_order_item") or "",
			"kho_xuat": g("s_warehouse") or "", "kho_nhap": g("t_warehouse") or "", "thanh_pham": cint(g("is_finished_item"))})
	return ra


def cau_lech_don(d, con_thieu):
	"""Đuôi dòng nhập hàng: còn thiếu theo đơn mua, hay đã đủ."""
	if con_thieu is None:
		return ""
	if con_thieu > 0.0005:
		return "còn thiếu %s theo đơn" % so(con_thieu)
	if con_thieu < -0.0005:
		return "dư %s so với đơn" % so(-con_thieu)
	return "đủ theo đơn"


def tom_tat_lech_nhan(cac_dong):
	"""Dòng lệch khi nhận điều chuyển: "Tên: giao 10, nhận 8"."""
	ra = []
	for d in cac_dong or []:
		if abs(flt(d.get("giao")) - flt(d.get("nhan"))) > 0.0005:
			ra.append({"ten": d.get("ten") or d.get("ma") or "", "sl": d.get("nhan"), "dvt": "",
				"ghi": "giao %s, nhận %s" % (so(d.get("giao")), so(d.get("nhan")))})
	return ra


def ten_muc_dich(ma):
	"""Tên có dấu của mục đích xuất nội bộ, hoặc chính mã nếu chưa khai."""
	from vagabond.xuat_noi_bo import MUC_DICH
	for m in MUC_DICH:
		if m.get("ma") == ma:
			return m.get("ten") or ma
	return ma or ""


def phan_loai_phieu_kho(purpose, muc_dich, huy, ly_do_huy=None):
	"""THUẦN: một phiếu kho ghi sổ thuộc tin nào.

	Trả "chuyen", "huy", "noi_bo", "san_xuat" hoặc "" (không báo: phục vụ bán,
	phiếu huỷ mềm, loại khác).

	Codex #495 vòng 4: Material Issue KHÔNG mặc nhiên là xuất huỷ. Trừ kho bù
	(tru_kho_bu), xuất nguyên liệu tiệc (tiec), dọn dữ liệu (don_du_lieu) đều là
	Material Issue để trống mục đích. Xuất huỷ chỉ nhận khi có dấu hiệu DƯƠNG:
	ô Lý do huỷ có giá trị (màn Xuất huỷ bắt buộc chọn lý do)."""
	if huy:
		return ""
	if purpose == "Material Transfer":
		return "chuyen"
	if purpose == "Manufacture":
		return "san_xuat"
	if purpose == "Material Issue":
		md = (muc_dich or "").strip()
		if not md:
			return "huy" if (ly_do_huy or "").strip() else ""
		if md == MUC_DICH_PHUC_VU_BAN:
			return ""
		return "noi_bo"
	return ""


def _loai_phieu(doc):
	return phan_loai_phieu_kho(doc.get("purpose"), doc.get("vgb_muc_dich_xuat"), cint(doc.get("vgb_huy")), doc.get("vgb_ly_do_huy"))


def dong_don_web(mon, toi_da=TOI_DA_MON):
	"""Dòng món của đơn web: "Tên x2"."""
	ds = [{"ten": m.get("ten") or m.get("ma") or "", "sl": m.get("sl"), "dvt": ""} for m in (mon or [])]
	ra = []
	for d in ds[:toi_da]:
		ra.append("%s x%s" % (d["ten"].strip(), so(d["sl"])))
	if len(ds) > toi_da:
		ra.append("+%d món khác" % (len(ds) - toi_da))
	return ra


def dong_tien_don_web(sau_giam, phi):
	"""THUẦN: dòng tiền của tin đơn web theo bốn trạng thái phí của don_web.quyet_phi_giao.

	Codex #495 P2: phí "chua_ro" (Ahamove không báo được) KHÔNG được cộng thành 0
	rồi gọi là Tổng; Sales phải báo phí khi gọi khách, nên tin nói rõ điều đó."""
	phi = phi or {}
	sau_giam = int(flt(sau_giam))
	pk = phi.get("phi_khach")
	if (phi.get("trang_thai") or "") == "tu_lay":
		return "Tổng %s, tự lấy" % tien(sau_giam)
	if phi.get("mien_phi"):
		return "Tổng %s, miễn phí giao" % tien(sau_giam)
	if pk is None:
		return "Tiền bánh %s, phí giao CHƯA RÕ (Ahamove không báo được), Sales báo phí khi gọi khách" % tien(sau_giam)
	return "Tổng %s (gồm phí giao %s)" % (tien(sau_giam + int(flt(pk))), tien(pk))


def soan_don_web_moi(ten, ngay_nhan, tu_lay, diem_lay, dia_chi, mon, sau_giam, phi, ma_pancake):
	"""THUẦN: dòng tin "Đơn web mới" cho Sales. Không in đủ họ tên, số điện thoại.

	sau_giam: tiền bánh sau giảm; phi: dict của don_web.quyet_phi_giao (bốn trạng thái)."""
	from vagabond.don_web import khung_gio, viet_tat_ten
	ngay, gio = khung_gio(ngay_nhan)
	nhan = ("Tự lấy tại %s" % diem_lay) if tu_lay else ("Giao: %s" % (dia_chi or "")[:80])
	khi = (" ".join([x for x in (ngay, gio) if x])).strip()
	dong = ["Khách %s, %s" % (viet_tat_ten(ten), ("nhận " + khi) if khi else "chưa rõ giờ nhận"), nhan]
	dong += dong_don_web(mon)
	dong.append(dong_tien_don_web(sau_giam, phi))
	if ma_pancake:
		dong.append("Đã vào Pancake, mã %s" % ma_pancake)
	return dong


# --------------------------------------------------------- chạm Frappe: chung


def _url(duong):
	try:
		return frappe.utils.get_url(duong)
	except Exception:
		return duong


def _ghi_loi(ten):
	try:
		frappe.log_error(title="Vagabond: tin kho %s" % ten, message=frappe.get_traceback())
	except Exception:
		pass


def _ten_nguoi(user):
	try:
		return frappe.get_cached_value("User", user, "full_name") or user
	except Exception:
		return user


def _con_thieu_theo_don(goc):
	"""Còn thiếu so với đơn mua của dòng đơn (sau khi phiếu nhập đã ghi sổ)."""
	if not goc:
		return None
	r = frappe.db.get_value("Purchase Order Item", goc, ["qty", "received_qty"], as_dict=True)
	if not r:
		return None
	return flt(r.qty) - flt(r.received_qty)


def _han_lo(lo):
	if not lo:
		return ""
	h = frappe.db.get_value("Batch", lo, "expiry_date")
	return ("hạn %s" % ngay_vn(h)) if h else ""


# ------------------------------------------------------- Thu mua (tm_)


def khi_co_yeu_cau_mua(doc, method=None):
	"""Hook Material Request after_insert và on_submit: tin cho Thu mua, một lần mỗi phiếu."""
	try:
		if (doc.get("material_request_type") or "Purchase") != "Purchase" or cint(doc.get("docstatus")) == 2:
			return
		bp = doc.get("bo_phan_yeu_cau") or doc.get("nguoi_yeu_cau") or doc.get("owner") or ""
		dong = ["Phiếu %s, bộ phận %s%s" % (doc.name, bp, (", cần ngày %s" % ngay_vn(doc.get("schedule_date"))) if doc.get("schedule_date") else "")]
		dong += dong_hang(hang_tu_items(doc.get("items")))
		kenh_zalo.bao("viec", "kho", "Yêu cầu mua hàng mới", dong,
			link=_url("/app/material-request/%s" % doc.name), khoa="ycm:%s" % doc.name, ma_tin="tm_yeu_cau_mua")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("yêu cầu mua")


def khi_ghi_so_don_mua(doc, method=None):
	"""Hook Purchase Order on_submit: Thu mua biết đơn vừa đặt, có tiền."""
	try:
		if cint(doc.get("vgb_huy")):
			return
		dong = ["Đơn %s, nhà cung cấp %s" % (doc.name, doc.get("supplier_name") or doc.get("supplier") or "")]
		if doc.get("schedule_date"):
			dong.append("Hẹn về %s" % ngay_vn(doc.get("schedule_date")))
		dong += dong_hang(hang_tu_items(doc.get("items")))
		dong.append("Tổng %s" % tien(doc.get("grand_total")))
		kenh_zalo.bao("thong_bao", "kho", "Đơn mua hàng vừa đặt", dong,
			link=_url("/app/purchase-order/%s" % doc.name), khoa="dmh:%s" % doc.name, ma_tin="tm_don_mua_moi")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("đơn mua mới")


def nhac_don_mua_tre_hen():
	"""Lịch 08:00: đơn mua đã quá ngày hẹn mà chưa về đủ."""
	try:
		hom_nay = nowdate()
		ds = frappe.get_all("Purchase Order", filters={"docstatus": 1, "status": ["not in", ("Closed", "Completed")],
			"per_received": ["<", 99.99], "schedule_date": ["<", hom_nay], "vgb_huy": ["!=", 1]},
			fields=["name", "supplier_name", "schedule_date", "grand_total", "per_received"],
			order_by="schedule_date asc", limit_page_length=0)
		if not ds:
			return
		dong = ["%s: %s, hẹn %s, về %s%%, %s" % (d.name, d.supplier_name or "", ngay_vn(d.schedule_date),
			so(d.per_received), tien(d.grand_total)) for d in ds]
		dong = kenh_zalo.cat_dong(dong, 8, "đơn")
		kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "%d đơn mua trễ hẹn chưa về đủ" % len(ds), dong,
			link=_url("/app/purchase-order?status=To%20Receive%20and%20Bill"), khoa="dmh-tre:%s" % hom_nay,
			ma_tin="tm_don_mua_tre_hen", nguon="Purchase Order")
	except Exception:
		_ghi_loi("đơn mua trễ hẹn")


def nhac_hang_ve_chua_hoa_don():
	"""Lịch 08:25: phiếu nhập đã ghi sổ quá NGAY_CHO_HOA_DON ngày mà chưa có hoá đơn mua."""
	try:
		hom_nay = nowdate()
		moc = add_days(hom_nay, -NGAY_CHO_HOA_DON)
		ds = frappe.get_all("Purchase Receipt", filters={"docstatus": 1, "is_return": 0, "per_billed": ["<", 99.99], "posting_date": ["<=", moc],
			"status": ["!=", "Closed"]}, fields=["name", "supplier_name", "posting_date", "grand_total"],
			order_by="posting_date asc", limit_page_length=0)
		if not ds:
			return
		dong = ["%s: %s, nhập %s, %s" % (d.name, d.supplier_name or "", ngay_vn(d.posting_date), tien(d.grand_total)) for d in ds]
		dong = kenh_zalo.cat_dong(dong, 8, "phiếu")
		kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "%d phiếu nhập quá %d ngày chưa có hoá đơn" % (len(ds), NGAY_CHO_HOA_DON), dong,
			link=_url("/app/purchase-receipt?status=To%20Bill"), khoa="pnk-chua-hd:%s" % hom_nay,
			ma_tin="tm_hang_ve_chua_hoa_don", nguon="Purchase Receipt")
	except Exception:
		_ghi_loi("hàng về chưa hoá đơn")


# ------------------------------------------------------------ Kho (kho_)


def khi_lap_phieu_nhap(doc, method=None):
	"""Hook Purchase Receipt after_insert: phiếu nháp chờ kho đếm.

	Màn Nhận hàng của app ghi sổ ngay lúc tạo (cờ vgb_nhap_ngay): không báo chờ
	kiểm, tin "đã nhập" sẽ đi ở on_submit."""
	try:
		# Codex #495 vòng 4: phiếu trả hàng nhà cung cấp (is_return) là hàng ĐI, không báo nhập.
		if cint(doc.get("docstatus")) != 0 or getattr(doc.flags, "vgb_nhap_ngay", False) or cint(doc.get("is_return")):
			return
		dong = ["Phiếu %s, nhà cung cấp %s, kho %s" % (doc.name, doc.get("supplier_name") or doc.get("supplier") or "",
			ten_kho(doc.get("set_warehouse")))]
		dong += dong_hang(hang_tu_items(doc.get("items")))
		kenh_zalo.bao("viec", "kho", "Phiếu nhập chờ kho đếm và ghi sổ", dong,
			link=_url("/app/purchase-receipt/%s" % doc.name), khoa="pnk-cho:%s" % doc.name, ma_tin="kho_nhap_cho_kiem")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("phiếu nhập chờ kiểm")


def khi_ghi_so_phieu_nhap(doc, method=None):
	"""Hook Purchase Receipt on_submit: hàng đã vào kho, kèm lệch so với đơn và hạn lô gần nhất."""
	try:
		if cint(doc.get("is_return")):
			return
		hang = hang_tu_items(doc.get("items"))

		def duoi(d):
			phan = [cau_lech_don(d, _con_thieu_theo_don(d.get("goc"))), _han_lo(d.get("lo"))]
			return ", ".join([p for p in phan if p])
		dong = ["Phiếu %s, nhà cung cấp %s, vào kho %s" % (doc.name, doc.get("supplier_name") or doc.get("supplier") or "",
			ten_kho(doc.get("set_warehouse")))]
		dong += dong_hang(hang, them=duoi)
		kenh_zalo.bao("thong_bao", "kho", "Đã nhập hàng vào kho", dong,
			link=_url("/app/purchase-receipt/%s" % doc.name), khoa="pnk-xong:%s" % doc.name, ma_tin="kho_da_nhap")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("đã nhập hàng")


def khi_lap_phieu_kho(doc, method=None):
	"""Hook Stock Entry after_insert: phiếu xuất huỷ còn nháp, chờ ghi sổ."""
	try:
		if cint(doc.get("docstatus")) != 0:
			return
		if _loai_phieu(doc) != "huy":
			return
		dong = ["Phiếu %s, kho %s%s" % (doc.name, ten_kho(doc.get("from_warehouse")),
			(", lý do: %s" % doc.get("vgb_ly_do_huy")) if doc.get("vgb_ly_do_huy") else "")]
		dong += dong_hang(hang_tu_items(doc.get("items")))
		kenh_zalo.bao("viec", "kho", "Phiếu xuất huỷ chờ ghi sổ", dong,
			link=_url("/app/stock-entry/%s" % doc.name), khoa="xh-cho:%s" % doc.name, ma_tin="kho_huy_cho_ghi_so")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("xuất huỷ chờ ghi sổ")


def khi_ghi_so_phieu_kho(doc, method=None):
	"""Hook Stock Entry on_submit: điều phối theo loại phiếu, mỗi tin một hàm."""
	loai = _loai_phieu(doc)
	if loai == "chuyen":
		_bao_da_chuyen(doc)
	elif loai == "huy":
		_bao_da_huy(doc)
		_bao_ke_toan_gia_von_huy(doc)
	elif loai == "noi_bo":
		_bao_xuat_noi_bo(doc)
	elif loai == "san_xuat":
		_bao_bep_xuat_nvl(doc)


def _bao_da_chuyen(doc):
	try:
		dong = ["Phiếu %s: %s sang %s" % (doc.name, ten_kho(doc.get("from_warehouse")), ten_kho(doc.get("to_warehouse")))]
		dong += dong_hang(hang_tu_items(doc.get("items")))
		dong.append("Kho nhận vào Hàng chuyển về kho tôi để xác nhận số thực nhận.")
		kenh_zalo.bao("thong_bao", "kho", "Đã chuyển hàng giữa kho", dong,
			link=_url("/app/stock-entry/%s" % doc.name), khoa="dc-xong:%s" % doc.name, ma_tin="kho_da_chuyen")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("đã chuyển hàng")


def _bao_da_huy(doc):
	try:
		dong = ["Phiếu %s, kho %s%s" % (doc.name, ten_kho(doc.get("from_warehouse")),
			(", lý do: %s" % doc.get("vgb_ly_do_huy")) if doc.get("vgb_ly_do_huy") else "")]
		dong += dong_hang(hang_tu_items(doc.get("items")))
		kenh_zalo.bao("thong_bao", "kho", "Đã xuất huỷ", dong,
			link=_url("/app/stock-entry/%s" % doc.name), khoa="xh-xong:%s" % doc.name, ma_tin="kho_da_huy")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("đã xuất huỷ")


def _bao_ke_toan_gia_von_huy(doc):
	try:
		dong = ["Phiếu %s, kho %s, giá vốn xuất huỷ %s" % (doc.name, ten_kho(doc.get("from_warehouse")), tien(doc.get("total_outgoing_value")))]
		if doc.get("vgb_ly_do_huy"):
			dong.append("Lý do: %s" % doc.get("vgb_ly_do_huy"))
		dong += dong_hang(hang_tu_items(doc.get("items")))
		kenh_zalo.bao("thong_bao", "kho", "Xuất huỷ đã ghi sổ, giá vốn", dong,
			link=_url("/app/stock-entry/%s" % doc.name), khoa="xh-gv:%s" % doc.name, ma_tin="kt_xuat_huy_gia_von")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("giá vốn xuất huỷ")


def _bao_xuat_noi_bo(doc):
	try:
		dong = ["Phiếu %s, kho %s, mục đích: %s" % (doc.name, ten_kho(doc.get("from_warehouse")), ten_muc_dich(doc.get("vgb_muc_dich_xuat")))]
		dong += dong_hang(hang_tu_items(doc.get("items")))
		kenh_zalo.bao("thong_bao", "kho", "Đã xuất dùng nội bộ", dong,
			link=_url("/app/stock-entry/%s" % doc.name), khoa="xnb-xong:%s" % doc.name, ma_tin="kho_xuat_noi_bo")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("xuất nội bộ")


def _bao_bep_xuat_nvl(doc):
	try:
		hang = hang_tu_items(doc.get("items"))
		tp = [h for h in hang if h.get("thanh_pham")]
		nvl = [h for h in hang if not h.get("thanh_pham")]
		dong = ["Phiếu %s%s" % (doc.name, (", lệnh %s" % doc.get("work_order")) if doc.get("work_order") else "")]
		if tp:
			dong.append("Thành phẩm: " + "; ".join("%s %s %s" % (h["ten"], so(h["sl"]), h["dvt"]) for h in tp[:3]))
		dong += dong_hang(nvl)
		kenh_zalo.bao("thong_bao", "san_xuat", "Lệnh sản xuất đã xuất nguyên liệu", dong,
			link=_url("/app/stock-entry/%s" % doc.name), khoa="lsx-nvl:%s" % doc.name, ma_tin="bep_lenh_sx_xuat_nvl")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("lệnh sản xuất xuất nguyên liệu")


def bao_da_nhan_chuyen(doc, tt, cac_dong):
	"""Gọi từ nhan_dieu_chuyen.xac_nhan sau khi ghi số thực nhận. Thiếu thì là Cảnh báo."""
	try:
		from vagabond.nhan_dieu_chuyen import THIEU
		thieu = tt == THIEU
		dong = ["Phiếu %s: %s sang %s, %s xác nhận" % (doc.name, ten_kho(doc.get("from_warehouse")),
			ten_kho(doc.get("to_warehouse")), _ten_nguoi(frappe.session.user))]
		if thieu:
			dong += dong_hang(tom_tat_lech_nhan(cac_dong))
		else:
			dong += dong_hang([{"ten": d.get("ten") or d.get("ma"), "sl": d.get("nhan"), "dvt": ""} for d in cac_dong or []])
		kenh_zalo.bao("canh_bao" if thieu else "thong_bao", "kho",
			"Nhận điều chuyển THIẾU hàng" if thieu else "Đã nhận đủ hàng điều chuyển", dong,
			link=_url("/app/stock-entry/%s" % doc.name), khoa="dc-nhan:%s" % doc.name, ma_tin="kho_da_nhan_chuyen")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("nhận điều chuyển")


MOC_GHI_SO = "modified"


def cua_so_chua_nhan(bay_gio):
	"""THUẦN: (từ, đến) của cửa sổ nhắc: ghi sổ từ GIO_CHUA_NHAN_TU tới GIO_CHUA_NHAN_DEN giờ trước."""
	return add_to_date(bay_gio, hours=-GIO_CHUA_NHAN_DEN), add_to_date(bay_gio, hours=-GIO_CHUA_NHAN_TU)


def nhac_chuyen_chua_nhan():
	"""Lịch mỗi giờ: phiếu điều chuyển đã ghi sổ từ 2 tới 48 giờ mà kho nhận chưa xác nhận.

	Codex #495 P2: mốc là lúc GHI SỔ, không phải lúc tạo nháp. Phiếu nháp lập trên
	Desk rồi ghi sổ hai ngày sau mà đo theo creation thì không bao giờ được nhắc.
	Stock Entry không có ô giờ ghi sổ; dùng modified: ghi sổ đổi docstatus nên
	modified bằng giờ ghi sổ, và các lượt ghi ô sau đó của app (xác nhận nhận, vết)
	đều update_modified=False. Một lượt sửa tay sau ghi sổ chỉ làm nhắc trễ, không
	làm mất nhắc; khoá chống trùng giữ mỗi phiếu một tin.

	Codex #495 P2 (vòng 2): KHÔNG giới hạn số dòng. Giới hạn 30 với thứ tự cố định
	thì 30 phiếu cũ nhất (đã có tin, khoá chặn trùng) chiếm chỗ mỗi giờ, phiếu thứ
	31 không bao giờ tới lượt và trôi khỏi cửa sổ 48 giờ mà không ai nhắc. Cửa sổ
	chỉ 46 giờ phiếu điều chuyển chưa xác nhận nên đọc hết là an toàn."""
	try:
		tu, den = cua_so_chua_nhan(now_datetime())
		ds = frappe.get_all("Stock Entry", filters={"docstatus": 1, "purpose": "Material Transfer", "vgb_huy": ["!=", 1],
			# Codex #495 vòng 6: ô chưa từng ghi là NULL; ["in", ("", None)] ra SQL IN ('', NULL)
			# không khớp NULL (bẫy đã ghi ở ban_hang.py). "is not set" dịch ra ifnull(ô, '') = ''.
			MOC_GHI_SO: ["between", (tu, den)], "vgb_nhan_tt": ["is", "not set"]},
			fields=["name", "from_warehouse", "to_warehouse", MOC_GHI_SO], order_by=MOC_GHI_SO + " asc", limit_page_length=0)
		for d in ds:
			kenh_zalo.bao("viec", "kho", "Hàng chuyển tới chưa được xác nhận nhận", [
				"Phiếu %s: %s sang %s, ghi sổ lúc %s" % (d.name, ten_kho(d.from_warehouse), ten_kho(d.to_warehouse), gio_vn(d.get(MOC_GHI_SO))),
				"Kho %s mở Hàng chuyển về kho tôi, đếm rồi bấm Xác nhận." % ten_kho(d.to_warehouse),
			], link=_url("/app/stock-entry/%s" % d.name), khoa="chua-nhan:%s" % d.name, ma_tin="kho_chuyen_chua_nhan")
	except Exception:
		_ghi_loi("chuyển chưa nhận")


def khi_ghi_so_giao_si(doc, method=None):
	"""Hook Delivery Note on_submit: hàng xuất giao khách sỉ."""
	try:
		# Codex #495 vòng 5: phiếu khách trả hàng (is_return) là hàng VỀ, không báo xuất giao
		# (cùng điều kiện xuat_ban.ds_phieu đang lọc).
		if cint(doc.get("is_return")):
			return
		dong = ["Phiếu %s, khách %s, từ kho %s%s" % (doc.name, doc.get("customer_name") or doc.get("customer") or "",
			ten_kho(doc.get("set_warehouse")), (", người nhận %s" % doc.get("vgb_nguoi_nhan")) if doc.get("vgb_nguoi_nhan") else "")]
		dong += dong_hang(hang_tu_items(doc.get("items")))
		kenh_zalo.bao("thong_bao", "kho", "Đã xuất giao khách sỉ", dong,
			link=_url("/app/delivery-note/%s" % doc.name), khoa="dn-xong:%s" % doc.name, ma_tin="kho_giao_si")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("giao sỉ")


def khi_doi_phieu_kiem_ke(doc, method=None):
	"""Hook Phieu Kiem Ke on_update: sang Chờ duyệt thì nhắc người duyệt, một lần mỗi phiếu."""
	try:
		if (doc.get("trang_thai") or "") != "Chờ duyệt":
			return
		ds = _dong_lech_kiem_ke(doc)
		dong = ["Phiếu %s, kho %s, %s kiểm ngày %s, %d dòng lệch" % (doc.name, ten_kho(doc.get("kho")), doc.get("nguoi_kiem") or "",
			ngay_vn(doc.get("ngay_kiem")), len(ds))]
		dong += dong_hang(ds)
		kenh_zalo.bao("viec", "kho", "Phiếu kiểm kê chờ duyệt", dong,
			link=_url("/app/phieu-kiem-ke/%s" % doc.name), khoa="kk-cho-duyet:%s" % doc.name, ma_tin="kho_kiem_ke_cho_duyet")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("kiểm kê chờ duyệt")


def _dong_lech_kiem_ke(doc):
	return [{"ten": r.get("item_name") or r.get("item_code") or "", "sl": r.get("so_luong"), "dvt": r.get("dvt") or "",
		"ghi": "lệch %s" % so(r.get("lech"))} for r in (doc.get("items") or []) if abs(flt(r.get("lech"))) > 0.0005]


def bao_kiem_ke_da_ghi_so(doc, ma_sr):
	"""Gọi từ kiem_ke.ghi_so sau khi điều chỉnh tồn đã ghi sổ."""
	try:
		ds = _dong_lech_kiem_ke(doc)
		dong = ["Phiếu %s, kho %s, %s" % (doc.name, ten_kho(doc.get("kho")),
			("đã điều chỉnh %d dòng lệch" % len(ds)) if ma_sr else "tồn khớp, không phải điều chỉnh")]
		dong += dong_hang(ds)
		kenh_zalo.bao("thong_bao", "kho", "Kiểm kê đã ghi sổ", dong,
			link=_url("/app/phieu-kiem-ke/%s" % doc.name), khoa="kk-ghi-so:%s" % doc.name, ma_tin="kho_kiem_ke_da_ghi_so")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("kiểm kê đã ghi sổ")


def bao_ke_toan_kiem_ke_lech(doc, ma_sr):
	"""Gọi từ kiem_ke.ghi_so: kế toán biết giá trị chênh lệch đã vào sổ."""
	try:
		if not ma_sr:
			return
		gt = frappe.db.get_value("Stock Reconciliation", ma_sr, "difference_amount")
		ds = _dong_lech_kiem_ke(doc)
		dong = ["Phiếu %s, kho %s, %d dòng lệch, chênh lệch giá trị %s" % (doc.name, ten_kho(doc.get("kho")), len(ds), tien(gt))]
		dong += dong_hang(ds)
		kenh_zalo.bao("thong_bao", "kho", "Kiểm kê đã ghi sổ, giá trị chênh lệch", dong,
			link=_url("/app/stock-reconciliation/%s" % ma_sr), khoa="kk-gt:%s" % doc.name, ma_tin="kt_kiem_ke_lech")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("giá trị kiểm kê")


def gom_ton_theo_kho(dong):
	"""THUẦN: {kho: tồn dương} từ các dòng {"warehouse", "qty"} (bỏ dòng không kho, tồn âm hay 0)."""
	ra = {}
	for d in dong or []:
		kho = (d or {}).get("warehouse") if hasattr(d, "get") else None
		if kho:
			ra[kho] = flt(ra.get(kho, 0)) + flt(d.get("qty"))
	return {k: v for k, v in ra.items() if v > 0.0005}


def _ton_lo_theo_kho(lo, ma):
	"""{kho: tồn} của một lô, KỂ CẢ lô đã quá hạn.

	Codex #495 P1: get_batch_qty không có cờ for_stock_levels thì lọc bỏ lô có
	expiry_date trước hôm nay (lo_hang._ton_tung_lo_tai đã ghi đúng bẫy này), nên
	lô hết hạn hôm qua mà còn hàng, thứ cần nhắc nhất, không có dòng nào. Phải
	truyền for_stock_levels=True. ERPNext trả về rỗng hay không có cột kho thì
	cộng thẳng sổ: gói lô (Serial and Batch Entry của gói đã ghi sổ) và sổ kho
	có cột batch_no, cùng cách lo_hang đã đo ngày 03/09/2026."""
	try:
		from erpnext.stock.doctype.batch.batch import get_batch_qty
		ds = get_batch_qty(batch_no=lo, item_code=ma, for_stock_levels=True) or []
		ra = gom_ton_theo_kho(ds if isinstance(ds, (list, tuple)) else [])
		if ra or any(hasattr(d, "get") and d.get("warehouse") for d in (ds if isinstance(ds, (list, tuple)) else [])):
			return ra
	except Exception:
		pass
	try:
		# Codex #495 vòng 3: gói lô chỉ tính khi có DÒNG SỔ KHO còn hiệu lực trỏ tới
		# (Pick List cũng ghi sổ gói mà không vào sổ kho); dòng sổ kho kiểu cũ (cột
		# batch_no) chỉ tính khi không trỏ gói, để không đếm hai lần cùng một lô.
		dong = frappe.db.sql("""select s.warehouse as warehouse, sum(e.qty) as qty
			from `tabSerial and Batch Entry` e join `tabStock Ledger Entry` s on s.serial_and_batch_bundle = e.parent
			where e.batch_no = %s and s.is_cancelled = 0 group by s.warehouse""", (lo,), as_dict=True)
		dong += frappe.db.sql("""select warehouse, sum(actual_qty) as qty from `tabStock Ledger Entry`
			where batch_no = %s and is_cancelled = 0 and ifnull(serial_and_batch_bundle, '') = '' group by warehouse""", (lo,), as_dict=True)
		return gom_ton_theo_kho(dong)
	except Exception:
		_ghi_loi("tồn lô theo kho")
		return {}


def gom_lo_sap_het_han(cac_lo, hom_nay, so_ngay=NGAY_SAP_HET_HAN):
	"""THUẦN: {kho: [{"ten","sl","dvt","ghi"}]} từ [{"lo","ten","dvt","han","ton":{kho: sl}}]."""
	ra = {}
	hom_nay = getdate(hom_nay)
	for b in cac_lo or []:
		han = b.get("han")
		if not han:
			continue
		han = getdate(han)
		con = (han - hom_nay).days
		if con > so_ngay:
			continue
		ghi = ("hết hạn %s" % ngay_vn(han)) if con >= 0 else ("đã quá hạn %s" % ngay_vn(han))
		for kho, sl in (b.get("ton") or {}).items():
			if flt(sl) > 0.0005:
				ra.setdefault(kho, []).append({"ten": b.get("ten") or "", "sl": sl, "dvt": b.get("dvt") or "", "ghi": ghi, "han": han})
	for kho in ra:
		ra[kho].sort(key=lambda d: d["han"])
	return ra


def nhac_lo_sap_het_han():
	"""Lịch 07:00: lô còn tồn mà hết hạn trong NGAY_SAP_HET_HAN ngày, một tin mỗi kho."""
	try:
		hom_nay = nowdate()
		moc = add_days(hom_nay, NGAY_SAP_HET_HAN)
		lo = frappe.get_all("Batch", filters={"expiry_date": ["between", (add_days(hom_nay, -30), moc)], "disabled": 0},
			fields=["name", "item", "item_name", "stock_uom", "expiry_date"], order_by="expiry_date asc", limit_page_length=0)
		cac_lo = [{"lo": b.name, "ten": b.item_name or b.item, "dvt": b.stock_uom or "", "han": b.expiry_date,
			"ton": _ton_lo_theo_kho(b.name, b.item)} for b in lo]
		theo_kho = gom_lo_sap_het_han(cac_lo, hom_nay)
		for kho, ds in sorted(theo_kho.items()):
			dong = ["Kho %s, %d lô" % (ten_kho(kho), len(ds))] + dong_hang(ds, toi_da=8)
			dong.append("Dùng trước, chuyển bớt hay lập phiếu xuất huỷ.")
			kenh_zalo.bao("viec", "kho", "Lô sắp hết hạn trong %d ngày" % NGAY_SAP_HET_HAN, dong,
				link=_url("/app/batch"),
				khoa="lo-het-han:%s:%s" % (kho, hom_nay), ma_tin="kho_lo_sap_het_han")
	except Exception:
		_ghi_loi("lô sắp hết hạn")


def gom_ton_duoi_muc(muc, ton):
	"""THUẦN: {kho: [{"ten","sl","dvt","ghi"}]} từ mức đặt lại và tồn thực.

	muc: [{"ma","ten","dvt","kho","muc"}]; ton: {(ma, kho): tồn}."""
	ra = {}
	for m in muc or []:
		k = (m.get("ma"), m.get("kho"))
		co = flt(ton.get(k, 0))
		if co < flt(m.get("muc")) - 0.0005:
			ra.setdefault(m.get("kho"), []).append({"ten": m.get("ten") or m.get("ma") or "", "sl": co, "dvt": m.get("dvt") or "",
				"ghi": "mức tối thiểu %s" % so(m.get("muc"))})
	return ra


def nhac_ton_duoi_muc():
	"""Lịch 07:00: tồn thực dưới mức đặt lại khai ở Mặt hàng (Item Reorder), một tin mỗi kho."""
	try:
		hom_nay = nowdate()
		muc = frappe.get_all("Item Reorder", filters={"warehouse_reorder_level": [">", 0]},
			fields=["parent", "warehouse", "warehouse_reorder_level"], limit_page_length=0)
		if not muc:
			return
		ma = sorted({m.parent for m in muc})
		ten = {i.name: (i.item_name, i.stock_uom) for i in frappe.get_all("Item", filters={"name": ["in", ma]},
			fields=["name", "item_name", "stock_uom"])}
		ton = {(b.item_code, b.warehouse): flt(b.actual_qty) for b in frappe.get_all("Bin",
			filters={"item_code": ["in", ma]}, fields=["item_code", "warehouse", "actual_qty"])}
		ds_muc = [{"ma": m.parent, "ten": ten.get(m.parent, ("", ""))[0] or m.parent, "dvt": ten.get(m.parent, ("", ""))[1] or "",
			"kho": m.warehouse, "muc": m.warehouse_reorder_level} for m in muc]
		for kho, ds in sorted(gom_ton_duoi_muc(ds_muc, ton).items()):
			dong = ["Kho %s, %d món" % (ten_kho(kho), len(ds))] + dong_hang(ds, toi_da=8)
			dong.append("Lập yêu cầu mua hoặc chuyển hàng từ kho khác.")
			kenh_zalo.bao("viec", "kho", "Tồn kho dưới mức tối thiểu", dong,
				link=_url("/app/material-request/new"), khoa="ton-thap:%s:%s" % (kho, hom_nay), ma_tin="kho_ton_duoi_muc")
	except Exception:
		_ghi_loi("tồn dưới mức")


# -------------------------------------------------------- Bán hàng (bh_)


def bao_don_web_moi(ten_don, ten, ngay_nhan, tu_lay, diem_lay, dia_chi, mon, sau_giam, phi, ma_pancake):
	"""Gọi từ don_hang.tao_don sau khi Pancake đã nhận đơn. Không bao giờ làm hỏng đơn."""
	try:
		dong = soan_don_web_moi(ten, ngay_nhan, tu_lay, diem_lay, dia_chi, mon, sau_giam, phi, ma_pancake)
		kenh_zalo.bao("thong_bao", "don_web", "Đơn web mới", dong,
			link=_url("/app/vagabond-don-web/%s" % ten_don), khoa="don-web-moi:%s" % ten_don, ma_tin="bh_don_web_moi")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("đơn web mới")


# ================================================================ v611
# Anh Việt 25/10/2026: tắt thư nội bộ (yêu cầu sản xuất, điều chuyển, đặt mua đang
# gửi qua Notification của Frappe), thay bằng tin Zalo; thêm tin sản xuất, tin yêu
# cầu điều chuyển treo, tin nhận hàng không được vì kho xuất chưa đủ hàng.

NGAY_YCDC_TREO = 2
TT_MR_XONG = ("Stopped", "Cancelled", "Transferred", "Received", "Issued", "Manufactured", "Draft")


def soan_ycsx(d, items, hom_nay):
	"""THUẦN: (tiêu đề, dòng) của tin yêu cầu sản xuất mới.

	d: các ô của phiếu (name, custom_bep_nhan, bo_phan_yeu_cau, nguoi_yeu_cau,
	schedule_date, set_warehouse). Cần trong hôm nay hoặc đã qua ngày thì GẤP."""
	bep = (d.get("custom_bep_nhan") or "").strip() or "bếp"
	can = d.get("schedule_date")
	gap = bool(can) and getdate(can) <= getdate(hom_nay)
	tieu_de = ("GẤP: " if gap else "") + "Yêu cầu sản xuất mới cho %s" % bep
	ai = ", ".join([x for x in ((d.get("bo_phan_yeu_cau") or "").strip(), (d.get("nguoi_yeu_cau") or "").strip()) if x])
	dau = "Phiếu %s%s" % (d.get("name"), (", " + ai) if ai else "")
	if can:
		dau += ", cần ngày %s" % ngay_vn(can)
	if d.get("set_warehouse"):
		dau += ", giao %s" % ten_kho(d.get("set_warehouse"))
	return tieu_de, [dau] + dong_hang(items)


def gom_ycsx_theo_bep(dong):
	"""THUẦN: {bếp: [{"ten","sl","dvt","ghi"}]} cộng số lượng cùng món, kèm số phiếu.

	dong: [{"bep","ma","ten","sl","dvt","phieu"}]; bếp trống gom vào "Chưa chọn bếp"."""
	ra = {}
	for r in dong or []:
		bep = (r.get("bep") or "").strip() or "Chưa chọn bếp"
		khoa = (r.get("ma") or r.get("ten"), r.get("dvt") or "")
		o = ra.setdefault(bep, {}).setdefault(khoa, {"ten": r.get("ten") or r.get("ma") or "", "sl": 0.0,
			"dvt": r.get("dvt") or "", "phieu": set()})
		o["sl"] += flt(r.get("sl"))
		if r.get("phieu"):
			o["phieu"].add(r.get("phieu"))
	kq = {}
	for bep, mon in ra.items():
		ds = sorted(mon.values(), key=lambda x: (-x["sl"], x["ten"]))
		kq[bep] = [{"ten": x["ten"], "sl": x["sl"], "dvt": x["dvt"], "so_phieu": len(x["phieu"])} for x in ds]
	return kq


def gom_ycdc_treo(rows, hom_nay, so_ngay=NGAY_YCDC_TREO):
	"""THUẦN: các yêu cầu điều chuyển đã gửi từ so_ngay ngày trở lên mà chưa xong, cũ nhất trước.

	rows: [{"name","status","transaction_date","set_from_warehouse","set_warehouse","so_mon"}]."""
	hom_nay = getdate(hom_nay)
	ra = []
	for r in rows or []:
		if (r.get("status") or "") in TT_MR_XONG or not r.get("transaction_date"):
			continue
		tre = (hom_nay - getdate(r.get("transaction_date"))).days
		if tre >= so_ngay:
			ra.append(dict(r, tre=tre))
	ra.sort(key=lambda r: (-r["tre"], r.get("name") or ""))
	return ra


def dong_ycdc_treo(ds, toi_da=8):
	"""THUẦN: mỗi phiếu một dòng "YCDC-...: Kho A sang Kho B, gửi dd/mm (N ngày), K món"."""
	ra = ["%s: %s sang %s, gửi %s (%d ngày), %d món" % (r.get("name"), ten_kho(r.get("set_from_warehouse")) or "?",
		ten_kho(r.get("set_warehouse")) or "?", ngay_vn(r.get("transaction_date")), r.get("tre", 0), int(r.get("so_mon") or 0))
		for r in (ds or [])[:toi_da]]
	if len(ds or []) > toi_da:
		ra.append("+%d phiếu khác" % (len(ds) - toi_da))
	return ra


def gom_thieu_ton(items, ton, gia=None):
	"""THUẦN: dòng hàng mà kho xuất không đủ tồn (hoặc có tồn nhưng chưa có giá vốn).

	items: [{"ma","ten","can","dvt","kho"}] theo đơn vị kho; ton: {(ma, kho): tồn};
	gia: {(ma, kho): giá vốn}. Trả [{"ten","sl","dvt","ghi"}] cho dong_hang."""
	gia = gia or {}
	can = {}
	for r in items or []:
		k = (r.get("ma"), r.get("kho"))
		o = can.setdefault(k, {"ten": r.get("ten") or r.get("ma") or "", "can": 0.0, "dvt": r.get("dvt") or ""})
		o["can"] += flt(r.get("can"))
	ra = []
	for k, o in can.items():
		co = flt(ton.get(k, 0))
		if co < o["can"] - 0.0005:
			ra.append({"ten": o["ten"], "sl": o["can"], "dvt": o["dvt"], "ghi": "kho đang có %s" % so(max(co, 0))})
		elif flt(gia.get(k, 0)) <= 0:
			ra.append({"ten": o["ten"], "sl": o["can"], "dvt": o["dvt"], "ghi": "có hàng nhưng máy chưa có giá nhập, báo kế toán"})
	return ra


# Lỗi của lõi ERPNext khi kho xuất chưa đủ hàng hoặc chưa có giá (bản tiếng Anh
# và bản dịch máy tiếng Việt trên site). Câu báo đã dễ hiểu của chính app (ví
# dụ lo_hang "Kho ... không đủ ... còn thiếu ...") KHÔNG thuộc nhóm này, giữ nguyên.
LOP_LOI_TON = ("NegativeStockError",)
CHU_LOI_TON = ("valuation rate", "tỷ giá định giá", "is required to do accounting entries",
	"to complete this transaction")


def la_loi_ton_loi(e):
	"""THUẦN: lỗi này là câu lõi ERPNext về thiếu tồn hoặc thiếu giá xuất kho không."""
	if type(e).__name__ in LOP_LOI_TON:
		return True
	chu = str(e or "").lower()
	return any(c in chu for c in CHU_LOI_TON)


def cau_thieu_ton(kho_xuat, thieu):
	"""THUẦN: câu báo trên màn hình cho người bấm nhận, thay câu lỗi thô của ERPNext."""
	return ("%s chưa đủ hàng để chuyển: %s. Bếp hoặc kho cần ghi nhận sản xuất hoặc nhập kho "
		"các món này vào %s trước, rồi bấm nhận lại." % (ten_kho(kho_xuat), "; ".join(dong_hang(thieu, toi_da=8)),
		ten_kho(kho_xuat)))


def khi_co_yeu_cau_sx(doc, method=None):
	"""Hook Material Request on_submit: yêu cầu sản xuất mới gửi bếp (thay thư Notification)."""
	try:
		if (doc.get("material_request_type") or "") != "Manufacture":
			return
		tieu_de, dong = soan_ycsx(doc.as_dict() if hasattr(doc, "as_dict") else doc, hang_tu_items(doc.get("items")), nowdate())
		kenh_zalo.bao("viec", "san_xuat", tieu_de, dong,
			link=_url("/app/material-request/%s" % doc.name), khoa="ycsx:%s" % doc.name, ma_tin="bep_ycsx_moi")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("yêu cầu sản xuất mới")


def khi_huy_yeu_cau_sx(doc, method=None):
	"""Hook Material Request on_cancel: yêu cầu sản xuất bị huỷ, bếp bỏ khỏi kế hoạch."""
	try:
		if (doc.get("material_request_type") or "") != "Manufacture":
			return
		dong = ["Phiếu %s cho %s, cần ngày %s, %s huỷ" % (doc.name, doc.get("custom_bep_nhan") or "bếp",
			ngay_vn(doc.get("schedule_date")) or "?", _ten_nguoi(frappe.session.user))]
		dong += dong_hang(hang_tu_items(doc.get("items")))
		kenh_zalo.bao("thong_bao", "san_xuat", "Yêu cầu sản xuất đã huỷ", dong,
			link=_url("/app/material-request/%s" % doc.name), khoa="ycsx-huy:%s" % doc.name, ma_tin="bep_ycsx_huy")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("huỷ yêu cầu sản xuất")


def nhac_ycsx_ngay_mai():
	"""Lịch 20:30: cộng các yêu cầu sản xuất cần ngày mai, một tin mỗi bếp."""
	try:
		mai = add_days(nowdate(), 1)
		phieu = frappe.get_all("Material Request", filters={"material_request_type": "Manufacture", "docstatus": 1,
			"schedule_date": mai, "status": ["not in", list(TT_MR_XONG)]},
			fields=["name", "custom_bep_nhan"], limit_page_length=0)
		if not phieu:
			return
		bep = {p.name: p.custom_bep_nhan for p in phieu}
		dong = [{"bep": bep.get(i.parent), "ma": i.item_code, "ten": i.item_name, "sl": i.qty, "dvt": i.uom, "phieu": i.parent}
			for i in frappe.get_all("Material Request Item", filters={"parent": ["in", list(bep)]},
				fields=["parent", "item_code", "item_name", "qty", "uom"], limit_page_length=0)]
		for ten_bep, ds in sorted(gom_ycsx_theo_bep(dong).items()):
			so_phieu = len({p for p, b in bep.items() if ((b or "").strip() or "Chưa chọn bếp") == ten_bep})
			noi = ["%s, ngày %s: %d phiếu, %d món" % (ten_bep, ngay_vn(mai), so_phieu, len(ds))] + dong_hang(ds, toi_da=12)
			kenh_zalo.bao("viec", "san_xuat", "Yêu cầu sản xuất cho ngày mai", noi,
				link=_url("/app/material-request?material_request_type=Manufacture"),
				khoa="ycsx-mai:%s:%s" % (ten_bep, mai), ma_tin="bep_ycsx_ngay_mai")
	except Exception:
		_ghi_loi("yêu cầu sản xuất ngày mai")


def khi_co_yeu_cau_chuyen(doc, method=None):
	"""Hook Material Request on_submit: yêu cầu điều chuyển mới (thay thư Notification)."""
	try:
		if (doc.get("material_request_type") or "") != "Material Transfer":
			return
		ai = ", ".join([x for x in ((doc.get("bo_phan_yeu_cau") or "").strip(), (doc.get("nguoi_yeu_cau") or "").strip()) if x])
		dau = "Phiếu %s: %s sang %s%s%s" % (doc.name, ten_kho(doc.get("set_from_warehouse")) or "?",
			ten_kho(doc.get("set_warehouse")) or "?", (", " + ai) if ai else "",
			(", cần ngày %s" % ngay_vn(doc.get("schedule_date"))) if doc.get("schedule_date") else "")
		kenh_zalo.bao("viec", "kho", "Yêu cầu điều chuyển mới", [dau] + dong_hang(hang_tu_items(doc.get("items"))),
			link=_url("/app/material-request/%s" % doc.name), khoa="ycdc:%s" % doc.name, ma_tin="kho_ycdc_moi")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("yêu cầu điều chuyển mới")


def nhac_ycdc_treo():
	"""Lịch 08:00: yêu cầu điều chuyển gửi từ NGAY_YCDC_TREO ngày trở lên mà chưa chuyển xong."""
	try:
		hom_nay = nowdate()
		rows = frappe.get_all("Material Request", filters={"material_request_type": "Material Transfer", "docstatus": 1,
			"transaction_date": ["<=", add_days(hom_nay, -NGAY_YCDC_TREO)], "status": ["not in", list(TT_MR_XONG)]},
			fields=["name", "status", "transaction_date", "set_from_warehouse", "set_warehouse"], limit_page_length=0)
		if not rows:
			return
		dem = {}
		for i in frappe.get_all("Material Request Item", filters={"parent": ["in", [r.name for r in rows]]},
				fields=["parent"], limit_page_length=0):
			dem[i.parent] = dem.get(i.parent, 0) + 1
		ds = gom_ycdc_treo([dict(r, so_mon=dem.get(r.name, 0)) for r in rows], hom_nay)
		if not ds:
			return
		dong = ["%d phiếu chờ quá %d ngày" % (len(ds), NGAY_YCDC_TREO)] + dong_ycdc_treo(ds)
		dong.append("Kho xuất soạn hàng, kho nhận bấm nhận; không cần nữa thì dừng phiếu.")
		kenh_zalo.bao("viec", "kho", "Yêu cầu điều chuyển treo", dong,
			link=_url("/app/material-request?material_request_type=Material%20Transfer"),
			khoa="ycdc-treo:%s" % hom_nay, ma_tin="kho_ycdc_treo")
	except Exception:
		_ghi_loi("yêu cầu điều chuyển treo")


def kiem_thieu_ton(doc):
	"""Dòng hàng mà kho xuất của phiếu chuyển không đủ tồn hoặc chưa có giá vốn. Chỉ đọc."""
	items = [{"ma": r.item_code, "ten": r.item_name or r.item_code, "can": flt(r.transfer_qty) or flt(r.qty),
		"dvt": r.stock_uom or r.uom or "", "kho": r.s_warehouse} for r in doc.get("items") or [] if r.get("s_warehouse")]
	if not items:
		return []
	bins = frappe.get_all("Bin", filters={"item_code": ["in", sorted({i["ma"] for i in items})],
		"warehouse": ["in", sorted({i["kho"] for i in items})]}, fields=["item_code", "warehouse", "actual_qty", "valuation_rate"])
	ton = {(b.item_code, b.warehouse): flt(b.actual_qty) for b in bins}
	gia = {(b.item_code, b.warehouse): flt(b.valuation_rate) for b in bins}
	return gom_thieu_ton(items, ton, gia)


def bao_nhan_thieu_ton(phieu, kho_xuat, kho_nhan, thieu):
	"""Tin cho Kho khi người bấm nhận không ghi sổ được vì kho xuất chưa đủ hàng.
	Gọi SAU khi đã rollback phiếu hỏng; người gọi commit để tin còn lại."""
	try:
		dong = ["Phiếu %s: %s sang %s, %s bấm nhận" % (phieu or "(nhận tay)", ten_kho(kho_xuat), ten_kho(kho_nhan),
			_ten_nguoi(frappe.session.user))]
		dong += dong_hang(thieu, toi_da=8)
		dong.append("Bếp hoặc kho ghi nhận sản xuất, nhập kho vào %s trước, rồi nhận lại." % ten_kho(kho_xuat))
		kenh_zalo.bao("canh_bao", "kho", "Nhận hàng không được: kho xuất chưa đủ hàng", dong,
			link=_url("/app/material-request/%s" % phieu) if phieu else None,
			khoa="thieu-ton:%s:%s:%s" % (phieu or kho_nhan, kho_xuat, nowdate()), ma_tin="kho_nhan_thieu_ton")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		_ghi_loi("nhận hàng thiếu tồn")
