# -*- coding: utf-8 -*-
"""Tiền ứng trước theo phiếu đặt (Sales Order): phần DÙNG CHUNG của Thiết kế
riêng và Bánh sỉ (v630).

Vì sao có tệp này. Thiết kế riêng (thiet_ke_rieng.py) dựng trước một bộ máy
nhận tiền chuyển khoản cho phiếu đặt: tìm dòng sao kê SePay mang mã đơn,
CHIẾM dòng đó trong sổ đối soát chung, lập phiếu thu ứng trước trỏ ĐÚNG phiếu
đặt, và ngày giao chỉ cấn đúng các phiếu thu đó vào hoá đơn. Bánh sỉ trả trước
cần y hệt bộ máy ấy (khác mã đơn và mức tối thiểu phải chuyển). Chép thêm một
bản là hai bản sẽ lệch nhau, đúng cái lỗi đã sinh ra doi_soat_sepay.py
("bảy phép khớp viết lại độc lập, mỗi phép sai một kiểu"). Nên gom về đây,
hai mô đun chỉ khai mã đơn, mức tối thiểu và câu báo tin.

Luật tiền giữ nguyên như thiet_ke_rieng ghi ở đầu tệp đó:
  - Một dòng sao kê chỉ được chiếm MỘT lần cho toàn hệ (ô `vgb_gd_tkr` trên
    phiếu thu, khai vào sổ đối soát chung ở thiet_ke_rieng._khai_doi_soat).
  - Phiếu thu chuyển khoản do máy lập ở dạng NHÁP: kế toán đính giấy báo Có
    rồi mới ghi sổ (luật chị Dung 16/08).
  - Còn phải thu tính ở MÁY CHỦ từ tổng phiếu đặt trừ mọi phiếu thu chưa huỷ.
  - Hoá đơn ngày giao chỉ cấn phiếu thu ĐÃ GHI SỔ của đúng phiếu đặt, tắt tự
    cấn của lõi (lõi sẽ vơ mọi khoản ứng trước chưa phân bổ của khách).
"""

# ------------------------------------------------------------ phần thuần

import json

SO = "Sales Order"
PE = "Payment Entry"
BT = "Bank Transaction"
PT_CK = "Chuyển khoản"
LECH = 1.0


def so_tien(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def tron(x):
	"""Tiền Việt không có số lẻ."""
	return float(round(so_tien(x)))


def vnd(x):
	return "{:,.0f}".format(tron(x)).replace(",", ".") + " đ"


def con_phai_thu(tong, ds_phieu):
	"""Còn phải thu bao nhiêu. THUẦN.

	`ds_phieu` là phiếu thu của phiếu đặt ({so_tien, docstatus}). Phiếu đã huỷ
	không tính; phiếu NHÁP vẫn tính vì nháp ở luồng này chỉ được lập khi đã
	chiếm một dòng sao kê thật (tiền đã về, chờ kế toán đính giấy báo Có).
	Không cho âm: thu dư là chuyện kế toán xử lý, không đòi khách số âm.
	"""
	da = sum(so_tien(p.get("so_tien")) for p in ds_phieu or [] if int(p.get("docstatus") or 0) < 2)
	return max(0.0, tron(so_tien(tong) - da))


def xet_giao_dich(tien_gd, toi_thieu, tong, da_nhan, ten_toi_thieu="tiền cọc"):
	"""Một dòng sao kê mang đúng mã có được lập phiếu thu không. THUẦN.

	Trả (được không, số tiền lập phiếu, lý do khi không).
	  - Chưa có đồng nào: phải từ `toi_thieu` trở lên (cọc 50% với thiết kế
	    riêng, cả đơn với bánh sỉ trả trước). Chuyển thiếu thì Sales gọi lại.
	  - Không bao giờ lập phiếu vượt phần còn phải thu: tiền dư để người nhìn.
	"""
	t = tron(tien_gd)
	con = max(0.0, tron(so_tien(tong) - so_tien(da_nhan)))
	if t <= 0:
		return (False, 0.0, "Dòng sao kê không phải tiền vào.")
	if con <= 0:
		return (False, 0.0, "Đơn đã nhận đủ tiền, dòng này chuyển dư.")
	if so_tien(da_nhan) <= 0 and t + LECH < so_tien(toi_thieu):
		return (False, 0.0, "Khách chuyển %s, ít hơn %s %s." % (vnd(t), ten_toi_thieu, vnd(toi_thieu)))
	if t > con + LECH:
		return (False, 0.0, "Khách chuyển %s, nhiều hơn số còn phải thu %s." % (vnd(t), vnd(con)))
	return (True, min(t, con), "")


def chon_giao_dich(ds_gd, ma, re_ma, chu, toi_thieu, tong, da_nhan, ten_toi_thieu="tiền cọc"):
	"""Từ các dòng sao kê, chọn dòng được lập phiếu thu cho đơn mang mã `ma`. THUẦN.

	`ds_gd`: {name, mo_ta, tien, date}; `re_ma`: mẫu mã của luồng (TKR..., BSI...);
	`chu`: {tên dòng: chứng từ đang giữ}. Bỏ dòng đã có chủ, dòng mang hai mã
	khác nhau CÙNG luồng (không biết chia cho ai), dòng không mang đúng mã.
	Trả (danh sách {gd, so_tien}, cần xem lại).
	"""
	from vagabond.khop_sao_ke import co_ma, got

	nhan, xem = [], []
	da = so_tien(da_nhan)
	for g in sorted(ds_gd or [], key=lambda x: (str(x.get("date") or ""), str(x.get("name") or ""))):
		mo = str(g.get("mo_ta") or "")
		if not co_ma(mo, ma):
			continue
		cac_ma = set(re_ma.findall(got(mo)))
		if len(cac_ma) > 1:
			xem.append({"gd": g.get("name"), "ly_do": "Dòng sao kê mang nhiều mã đơn, khớp tay."})
			continue
		if (chu or {}).get(g.get("name")):
			continue
		ok, so, ly_do = xet_giao_dich(g.get("tien"), toi_thieu, tong, da, ten_toi_thieu)
		if not ok:
			xem.append({"gd": g.get("name"), "ly_do": ly_do})
			continue
		nhan.append({"gd": g, "so_tien": so})
		da += so
	return nhan, xem


def quay_chuyen_khoan(ds_diem):
	"""Mã điểm bán không có két (Sales Online) cho mọi khoản chuyển khoản. THUẦN."""
	for d in ds_diem or []:
		if d.get("bat", 1) and not d.get("quay") and d.get("ma"):
			return d["ma"]
	return "SALES"


def phieu_thu(don_dat, khach, tong, so, quay, pt, ngay, gd=None, ghi_chu="", tien_to="TKR"):
	"""Các ô của MỘT phiếu thu ứng trước cho phiếu đặt. THUẦN.

	Dựng ở đây để ca kiểm chạy đúng `dat_banh.loi_phieu_dat_banh` trên chính
	các ô sẽ được ghi, không dựng một bản riêng cho ca kiểm.
	"""
	ref = (gd or {}).get("ma_tham_chieu") or (gd or {}).get("name") or ""
	return {
		"doctype": PE, "payment_type": "Receive", "party_type": "Customer", "party": khach,
		"posting_date": str(ngay)[:10], "paid_amount": tron(so), "received_amount": tron(so),
		"mode_of_payment": pt, "vgb_quay": str(quay or "").strip().upper(), "vgb_phieu_dat": don_dat,
		"vgb_gd_tkr": (gd or {}).get("name") or "",
		"reference_no": (ref or ("%s:%s:%s" % (tien_to, don_dat, pt)))[:140], "reference_date": str(ngay)[:10],
		"remarks": ghi_chu[:1000],
		"references": [{"reference_doctype": SO, "reference_name": don_dat,
			"total_amount": tron(tong), "allocated_amount": tron(so)}],
	}


def loi_phieu(p):
	"""Bốn hàng rào của dat_banh cho một phiếu dựng bởi `phieu_thu`. THUẦN."""
	from vagabond.dat_banh import loi_phieu_dat_banh

	return loi_phieu_dat_banh({"vgb_phieu_dat": p.get("vgb_phieu_dat"), "vgb_quay": p.get("vgb_quay")},
		p.get("references") or [])


def chon_ung_truoc(ds_ung, phieu_hop_le, tong):
	"""Dòng advances của hoá đơn ngày giao. THUẦN.

	`ds_ung` là kết quả `get_advance_entries` của lõi; chỉ giữ dòng là phiếu
	thu ĐÃ GHI SỔ của đúng phiếu đặt (`phieu_hop_le`). Tổng cấn phải bằng
	tổng hoá đơn, không thì trả lỗi: không xuất hoá đơn trả trước còn treo nợ.
	"""
	ra, con = [], tron(tong)
	for r in ds_ung or []:
		if r.get("reference_type") != PE or r.get("reference_name") not in (phieu_hop_le or ()):
			continue
		so = min(tron(r.get("amount")), con)
		if so <= 0:
			continue
		ra.append(dict(r, allocated_amount=so))
		con -= so
	if con > LECH:
		return ra, "Các phiếu thu đã ghi sổ của đơn mới cấn được %s trên tổng %s." % (vnd(tron(tong) - con), vnd(tong))
	return ra, ""


def dong_advances(ds_ung, ngay):
	"""Từ kết quả `chon_ung_truoc` ra các dòng Sales Invoice Advance. THUẦN."""
	ra = []
	for r in ds_ung or []:
		dong = {"doctype": "Sales Invoice Advance", "reference_type": r.get("reference_type"),
			"reference_name": r.get("reference_name"), "reference_row": r.get("reference_row"),
			"remarks": r.get("remarks"), "advance_amount": so_tien(r.get("amount")),
			"allocated_amount": r["allocated_amount"], "ref_exchange_rate": so_tien(r.get("exchange_rate")) or 1,
			"difference_posting_date": str(ngay)[:10]}
		if r.get("paid_from"):
			dong["account"] = r.get("paid_from")
		if r.get("paid_to"):
			dong["account"] = r.get("paid_to")
		ra.append(dong)
	return ra


# ------------------------------------------------------------- chạm Frappe

import frappe  # noqa: E402
from frappe.utils import flt  # noqa: E402


def phieu_cua(so_name):
	return frappe.get_all(PE, filters={"vgb_phieu_dat": so_name, "docstatus": ["<", 2], "payment_type": "Receive"},
		fields=["name", "docstatus", "paid_amount", "received_amount", "mode_of_payment", "vgb_quay",
			"vgb_gd_tkr", "posting_date", "creation"], order_by="creation asc", limit_page_length=0)


def ds_phieu(so_name):
	from vagabond.dat_banh import tien_thuc_thu

	return [dict(p, so_tien=tien_thuc_thu(p)) for p in phieu_cua(so_name)]


def gd_mang_ma(ma):
	ds = frappe.db.sql(
		"""select name, date, deposit, withdrawal, description, reference_number, bank_account, transaction_id
		from `tabBank Transaction` where docstatus = 1 and deposit > 0
		and (upper(description) like %(m)s or upper(reference_number) like %(m)s)""",
		{"m": "%" + ma + "%"}, as_dict=True)
	for g in ds:
		g["mo_ta"] = "%s %s" % (g.get("description") or "", g.get("reference_number") or "")
		g["tien"] = flt(g.get("deposit"))
		g["ma_tham_chieu"] = g.get("reference_number") or g.get("transaction_id") or g.get("name")
	return ds


def khop(so_name, truong_ma, re_ma, toi_thieu_cua, quay, cong_ty, ghi_chu_cua, khi_lap_dau=None,
		ten_toi_thieu="tiền cọc", tien_to="TKR", tieu_de_loi="ung_truoc_don"):
	"""Tìm tiền về cho MỘT phiếu đặt, chiếm dòng sao kê và lập phiếu thu nháp.

	Chạy trong khoá hàng của phiếu đặt: nhịp 5 phút và lượt khách hỏi trạng
	thái cùng lúc thì lượt sau đọc lại phiếu thu của lượt trước, không lập đôi.
	  truong_ma      ô mã đơn trên phiếu đặt (vgb_tkr_ma, vgb_si_ma)
	  toi_thieu_cua  hàm(hàng phiếu đặt, tổng) -> số tiền tối thiểu lần đầu
	  quay, cong_ty  hàm không đối số, gọi lúc chạy (ca kiểm thay được)
	  ghi_chu_cua    hàm(mã đơn, dòng sao kê) -> ghi chú phiếu thu
	  khi_lap_dau    hàm(tên phiếu đặt, mã đơn) gọi một lần khi đồng đầu tiên về
	Trả số phiếu đã lập.
	"""
	from vagabond import doi_soat_sepay as dss
	from vagabond.thu_tien import nang_quyen_lap_phieu

	hang = frappe.db.sql("select name, docstatus, status, `%s`, vgb_tkr_coc, customer, grand_total, "
		"rounded_total, per_billed from `tabSales Order` where name=%%s for update" % truong_ma, (so_name,), as_dict=True)
	if not hang:
		return 0
	so = hang[0]
	if int(so.docstatus) != 1 or so.status in ("Closed", "Cancelled", "Completed") or flt(so.per_billed) > 0:
		return 0
	ma = so.get(truong_ma)
	if not ma:
		return 0
	tong = flt(so.rounded_total) or flt(so.grand_total)
	cac_phieu = ds_phieu(so_name)
	da = sum(p["so_tien"] for p in cac_phieu)
	if con_phai_thu(tong, cac_phieu) <= 0:
		return 0
	gds = gd_mang_ma(ma)
	if not gds:
		return 0
	chu = dss.chu_cua_giao_dich([g["name"] for g in gds])
	nhan, xem = chon_giao_dich(gds, ma, re_ma, chu, toi_thieu_cua(so, tong), tong, da, ten_toi_thieu)
	if xem:
		frappe.log_error(json.dumps(xem, ensure_ascii=False), "%s: sao kê cần xem lại %s" % (tieu_de_loi, ma))
	cho_phep = dss.tai_khoan_duoc_khop()
	lap = 0
	for x in nhan:
		g = x["gd"]
		if dss.ly_do_tai_khoan_sepay(g.get("bank_account"), cho_phep):
			continue
		tk = frappe.db.get_value("Bank Account", g.get("bank_account"), "account")
		if not tk:
			continue
		p = phieu_thu(so_name, so.customer, tong, x["so_tien"], quay(), PT_CK, g.get("date"), g,
			ghi_chu_cua(ma, g), tien_to)
		loi = loi_phieu(p)
		if loi:
			frappe.throw(loi)
		with nang_quyen_lap_phieu():
			pe = frappe.get_doc(dict(p, company=cong_ty(), paid_to=tk, bank_account=g.get("bank_account")))
			if not frappe.db.exists("Mode of Payment", PT_CK):
				pe.mode_of_payment = None
			pe.setup_party_account_field()
			pe.set_missing_values()
			pe.flags.ignore_permissions = True
			pe.insert(ignore_permissions=True)
		lap += 1
		if da <= 0 and khi_lap_dau:
			khi_lap_dau(so_name, ma)
		da += x["so_tien"]
	return lap


def ghi_so_nhap(so_name, phieu, anh=None):
	"""Kế toán đính giấy báo Có hoặc UNC khách gửi rồi ghi sổ phiếu thu chuyển
	khoản NHÁP do máy lập khi chiếm sao kê. Cổng quyền (vai màn, kế toán) do
	mô đun gọi kiểm TRƯỚC khi vào đây."""
	pe = frappe.get_doc(PE, phieu)
	if pe.get("vgb_phieu_dat") != so_name or int(pe.docstatus) != 0 or not pe.get("vgb_gd_tkr"):
		frappe.throw("Phiếu %s không phải phiếu thu nháp của đơn này." % phieu)
	g = frappe.db.get_value(BT, pe.vgb_gd_tkr, ["docstatus", "deposit"], as_dict=True)
	if not g or int(g.docstatus) != 1 or tron(g.deposit) + LECH < tron(pe.paid_amount):
		frappe.throw("Dòng sao kê %s của phiếu không còn hợp lệ. Kế toán đối chiếu tay." % pe.vgb_gd_tkr)
	if isinstance(anh, str):
		anh = frappe.parse_json(anh or "[]") or []
	from vagabond.tra_truoc_khach import _dinh_tep

	_dinh_tep(PE, pe.name, anh)
	pe.flags.ignore_permissions = True
	pe.submit()
	return pe


def cap_ung_truoc(si, phieu_da_ghi):
	"""Gắn bảng advances của hoá đơn ngày giao: CHỈ phiếu thu đã ghi sổ của đúng
	phiếu đặt, tắt tự cấn (lõi vơ mọi khoản ứng trước chưa phân bổ của khách:
	erpnext/controllers/accounts_controller.py, nhánh
	`if cint(self.allocate_advances_automatically)` gọi set_advances với
	include_unallocated). Thiếu thì ném lỗi, không xuất hoá đơn còn treo nợ."""
	si.allocate_advances_automatically = 0
	si.run_method("calculate_taxes_and_totals")
	ds_ung, loi = chon_ung_truoc(si.get_advance_entries(include_unallocated=False), phieu_da_ghi,
		flt(si.rounded_total) or flt(si.grand_total))
	if loi:
		frappe.throw(loi)
	si.set("advances", [])
	for d in dong_advances(ds_ung, si.posting_date):
		si.append("advances", d)
	return si
