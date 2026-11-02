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


def ly_do_loai_dong(g, ly_do_tai_khoan, tk_so_cai):
	"""Lý do một dòng sao kê KHÔNG được đưa vào phép chọn. Rỗng là dùng được. THUẦN.

	`ly_do_tai_khoan`: hàm(tài khoản ngân hàng) -> lý do chưa được khớp (rỗng là được);
	`tk_so_cai`: {tài khoản ngân hàng: tài khoản sổ cái}.
	"""
	tien = so_tien(g.get("deposit"))
	if tien <= 0 or so_tien(g.get("withdrawal")) > 0:
		return "Dòng sao kê không phải tiền vào."
	if so_tien(g.get("docstatus")) != 1:
		return "Dòng sao kê chưa ghi sổ hoặc đã huỷ."
	if str(g.get("currency") or "VND").strip().upper() != "VND":
		return "Dòng sao kê không phải tiền đồng."
	tk = g.get("bank_account")
	ly_do = ly_do_tai_khoan(tk)
	if ly_do:
		return ly_do
	if not (tk_so_cai or {}).get(tk):
		return "Tài khoản ngân hàng %s chưa gắn tài khoản sổ cái." % (tk or "")
	con = g.get("unallocated_amount")
	if con is not None and so_tien(con) + LECH < tien:
		return "Dòng sao kê đã đối chiếu một phần hoặc toàn bộ ở nơi khác."
	return ""


def loc_dong_sao_ke(ds_gd, ly_do_tai_khoan, tk_so_cai):
	"""Phép lọc DUY NHẤT của bộ khớp, chạy TRƯỚC phép chọn và phép cộng dồn. THUẦN.

	Codex #531 vòng 9: lọc tài khoản sau phép chọn thì dòng ở tài khoản không
	được khớp đã kịp cộng vào số đã nhận, chiếm hết phần còn thu; dòng đúng
	đến sau bị loại vì "thừa", rồi dòng sai bị bỏ ở vòng lập phiếu: 0 phiếu.
	Mọi điều kiện loại một dòng phải nằm ở đây. Trả (dùng được, bị loại).
	"""
	dung, loai = [], []
	for g in ds_gd or []:
		ly_do = ly_do_loai_dong(g, ly_do_tai_khoan, tk_so_cai)
		if ly_do:
			loai.append({"gd": g.get("name"), "ly_do": ly_do})
		else:
			dung.append(g)
	return dung, loai


def chon_giao_dich(ds_gd, ma, re_ma, chu, toi_thieu, tong, da_nhan, ten_toi_thieu="tiền cọc"):
	"""Từ các dòng sao kê, chọn dòng được lập phiếu thu cho đơn mang mã `ma`. THUẦN.

	`ds_gd` phải đã qua `loc_dong_sao_ke`: hàm này cộng dồn số đã nhận theo
	từng dòng nhận, dòng nào lẽ ra bị loại mà lọt vào đây sẽ chiếm phần còn thu.
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


def loc_giay_bao_co(tep):
	"""Các tệp giấy báo Có kế toán gửi lên, kiểm ở cửa nhập. THUẦN.

	Codex #531 f3: trước đây đi qua `tra_truoc_khach._dinh_tep`, hàm đó chỉ
	nhận ẢNH, nên PDF giấy báo Có (đúng thứ ngân hàng cấp) bị bỏ lặng lẽ, rồi
	hook `chung_tu_tien.chan_thieu_dinh_kem` chặn ghi sổ và bánh không giao
	được. Luật đuôi và trần dung lượng lấy từ cổng tệp chung `tep_dinh_kem`
	(ảnh và PDF), không chép một bộ luật thứ hai.

	`tep`: [{ten, noi_dung (base64, có thể kèm tiền tố data:)}].
	Trả (danh sách (tên, base64), câu lỗi). Một tệp hỏng là dừng cả lô, vì
	ghi sổ thiếu chứng từ thì không lùi lại được.
	"""
	from vagabond.tep_dinh_kem import loi_tu_choi

	ra = []
	for a in tep or []:
		a = a if isinstance(a, dict) else {}
		ten = str(a.get("ten") or "").strip()[:140]
		noi = str(a.get("noi_dung") or "").strip()
		if noi[:5].lower() == "data:" and "," in noi[:200]:
			noi = noi.split(",", 1)[1]
		loi = loi_tu_choi(ten, len(noi) * 3 // 4)
		if loi:
			return [], loi
		if not noi:
			return [], "Tệp %s rỗng. Chọn lại ảnh hoặc PDF giấy báo Có." % ten
		ra.append((ten, noi))
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


def dk_don_mo(o_ma, tien_to):
	"""Điều kiện SQL "phiếu đặt đang mở" (bí danh bảng `so`), khớp ĐÚNG phép
	phân loại trạng thái của hai luồng (thiet_ke_rieng.trang_thai, banh_si.
	xet_trang_thai): đã huỷ khi docstatus 2; đã giao khi có hoá đơn ĐÃ GHI SỔ
	mang custom_pancake_id "<tiền tố>-<mã đơn>" (ô có khoá duy nhất nên phép
	`not exists` đi bằng chỉ mục). Mọi đơn khác là đang mở.

	Codex #531 vòng 8: câu đọc dùng làm nguồn danh sách việc đang chờ (đơn chờ
	tiền, chờ giao) không được có LIMIT hay cửa sổ ngày; chỉ phần lịch sử (đã
	giao, đã huỷ) mới cắt. Một nguồn cho mọi câu đọc đơn đang mở."""
	return ("so.docstatus = 1 and not exists (select 1 from `tabSales Invoice` si where si.custom_pancake_id = "
		"concat('%s-', so.`%s`) and si.docstatus = 1)" % (tien_to, o_ma))


def gop_ten_don(*cac_lo):
	"""Gộp các lô {name, ...} đọc từ nhiều câu, bỏ trùng theo tên, giữ thứ tự lô
	đầu rồi lô sau. THUẦN."""
	da, ra = set(), []
	for lo in cac_lo:
		for r in lo or []:
			if r["name"] not in da:
				da.add(r["name"])
				ra.append(r)
	return ra


def ten_don_man(o_ma, tien_to, tu, tran=400):
	"""Tên phiếu đặt cho màn danh sách app (Đơn sỉ web, Đơn đặt trước): MỌI đơn
	đang mở, kể cả đơn quá hạn giao từ trước cửa sổ ngày, cộng các đơn có ngày
	giao từ `tu` (lịch sử, tối đa `tran`). Xếp theo ngày giao. Codex #531 v8:
	đơn chờ giao quá 30 ngày không được biến mất khỏi màn vì nằm ngoài cửa sổ."""
	mo = frappe.db.sql("""select so.name, so.delivery_date, so.creation from `tabSales Order` so
		where ifnull(so.`%s`, '') != '' and %s""" % (o_ma, dk_don_mo(o_ma, tien_to)), as_dict=True)
	gan = frappe.db.sql("""select so.name, so.delivery_date, so.creation from `tabSales Order` so
		where ifnull(so.`%s`, '') != '' and so.docstatus in (1, 2) and so.delivery_date >= %%s
		order by so.delivery_date asc, so.creation asc limit %d""" % (o_ma, int(tran)), (tu,), as_dict=True)
	ds = gop_ten_don(mo, gan)
	ds.sort(key=lambda r: (str(r.get("delivery_date") or ""), str(r.get("creation") or "")))
	return [r["name"] for r in ds]


def phieu_cua(so_name, khoa=False):
	"""Phiếu thu chưa huỷ của phiếu đặt.

	khoa=True là phép đọc HIỆN TẠI có khoá, dùng NGAY SAU khi đã khoá hàng phiếu
	đặt (Codex #531 f1). MariaDB REPEATABLE READ: phép đọc thường sau khi chờ
	khoá vẫn trả ẢNH CHỤP từ lần đọc thường đầu tiên của yêu cầu (lượt khách
	hỏi trạng thái đọc phiếu đặt trước rồi mới khoá), nên lượt thứ hai không
	thấy phiếu thu lượt thứ nhất vừa lập và lập thêm một phiếu cho CÙNG dòng
	sao kê: cọc 50% thành "đã thu đủ".

	Đọc qua bảng tham chiếu (reference_name có chỉ mục trong ERPNext) để `for
	update` chỉ khoá đúng các dòng của phiếu đặt này; lọc `vgb_phieu_dat` thẳng
	trên Payment Entry là quét và khoá cả bảng. Phiếu thu ứng trước của luồng
	này luôn có đúng một dòng tham chiếu phiếu đặt (`loi_phieu` chặn).
	"""
	if khoa:
		ds = frappe.db.sql("""select p.name, p.docstatus, p.paid_amount, p.received_amount, p.mode_of_payment,
				p.vgb_quay, p.vgb_gd_tkr, p.posting_date, p.creation
			from `tabPayment Entry Reference` r join `tabPayment Entry` p on p.name = r.parent
			where r.parenttype = 'Payment Entry' and r.reference_doctype = 'Sales Order'
				and r.reference_name = %(so)s and p.vgb_phieu_dat = %(so)s and p.docstatus < 2
				and p.payment_type = 'Receive'
			order by p.creation asc for update""", {"so": so_name}, as_dict=True)
		da, ra = set(), []
		for p in ds:
			if p["name"] not in da:
				da.add(p["name"])
				ra.append(p)
		return ra
	return frappe.get_all(PE, filters={"vgb_phieu_dat": so_name, "docstatus": ["<", 2], "payment_type": "Receive"},
		fields=["name", "docstatus", "paid_amount", "received_amount", "mode_of_payment", "vgb_quay",
			"vgb_gd_tkr", "posting_date", "creation"], order_by="creation asc", limit_page_length=0)


def ds_phieu(so_name, khoa=False):
	from vagabond.dat_banh import tien_thuc_thu

	return [dict(p, so_tien=tien_thuc_thu(p)) for p in phieu_cua(so_name, khoa)]


def khoa_dong_sao_ke(ds_gd):
	"""Khoá các dòng sao kê sắp xét, theo thứ tự tên (Codex #531 f1).

	Khoá phiếu đặt chỉ xếp hàng các lượt CÙNG đơn. Một dòng sao kê mang mã của
	hai đơn (thiết kế riêng và sỉ) thì hai lượt khớp hai đơn khác nhau chạy
	song song, cùng đọc "chưa có chủ" rồi cùng lập phiếu thu. Khoá dòng sao kê
	TRƯỚC khi đọc chủ: lượt sau chờ tới khi lượt trước commit rồi mới đọc
	(hiện tại) và thấy chủ. Khoá trước rồi mới đọc chủ, không đọc chủ rồi mới
	khoá, để hai lượt cùng một dòng sao kê không cùng giữ khoá khoảng trống chỉ
	mục rồi chờ nhau.
	Thứ tự: hàng phiếu đặt, rồi dòng sao kê theo tên, rồi phiếu thu.

	Trả {tên: các ô đọc HIỆN TẠI trong khoá} để phép lọc quyết trên số mới
	nhất (đã huỷ, đã đối chiếu ở nơi khác giữa lúc tìm và lúc khoá)."""
	ds = sorted({str(x or "").strip() for x in ds_gd or [] if str(x or "").strip()})
	if not ds:
		return {}
	hang = frappe.db.sql("""select name, docstatus, deposit, withdrawal, currency, unallocated_amount, bank_account
		from `tabBank Transaction` where name in %(ds)s order by name for update""", {"ds": tuple(ds)}, as_dict=True)
	return {h["name"]: h for h in hang or [] if isinstance(h, dict)}


def phieu_chiem(ds_gd):
	"""Phiếu thu chưa huỷ đang chiếm các dòng sao kê, đọc HIỆN TẠI có khoá.

	Ô `vgb_gd_tkr` có chỉ mục (search_index) nên `for update` chỉ khoá đúng các
	dòng mang mã đó. `doi_soat_sepay.chu_cua_giao_dich` đọc bằng get_all (ảnh
	chụp), dùng cho các luồng khác; luồng này đọc lại chủ của chính nó ở đây.
	Không dùng ràng buộc DUY NHẤT trên ô này: phiếu thu tiền mặt để trống ô, và
	phiếu đã huỷ (docstatus 2) phải nhả dòng sao kê cho phiếu mới.

	Đọc có khoá mà không ra dòng nào thì MariaDB giữ khoá khoảng trống chỉ mục;
	hai lượt khớp HAI đơn khác nhau cùng lúc có thể đâm deadlock khi cùng ghi.
	MariaDB huỷ một lượt; lỗi chết giao dịch không bị nuốt (`quet` lùi rồi làm
	đơn sau, trang khách hỏi lại sau 8 giây), không sinh phiếu đôi."""
	ds = sorted({str(x or "").strip() for x in ds_gd or [] if str(x or "").strip()})
	if not ds:
		return []
	return frappe.db.sql("""select name, vgb_gd_tkr from `tabPayment Entry`
		where vgb_gd_tkr in %(ds)s and docstatus < 2 order by name for update""", {"ds": tuple(ds)}, as_dict=True)


def chu_hien_tai(ds_gd):
	return {p["vgb_gd_tkr"]: "phiếu thu đơn đặt trước " + p["name"] for p in phieu_chiem(ds_gd)}


def dien_dong(g):
	g["mo_ta"] = "%s %s" % (g.get("description") or "", g.get("reference_number") or "")
	g["tien"] = flt(g.get("deposit"))
	g["ma_tham_chieu"] = g.get("reference_number") or g.get("transaction_id") or g.get("name")
	return g


def gd_mang_ma(ma):
	"""Các dòng sao kê có thể mang mã, đọc ảnh chụp để TÌM. Quyết ở `loc_dong_sao_ke`
	trên bản đọc hiện tại trong khoá; điều kiện SQL ở đây chỉ để bớt dòng đọc."""
	ds = frappe.db.sql(
		"""select name, date, deposit, withdrawal, description, reference_number, bank_account, transaction_id,
		docstatus, currency, unallocated_amount
		from `tabBank Transaction` where docstatus = 1 and deposit > 0
		and (upper(description) like %(m)s or upper(reference_number) like %(m)s)""",
		{"m": "%" + ma + "%"}, as_dict=True)
	return [dien_dong(g) for g in ds]


def khop(so_name, truong_ma, re_ma, toi_thieu_cua, quay, cong_ty, ghi_chu_cua, khi_lap_dau=None,
		ten_toi_thieu="tiền cọc", tien_to="TKR", tieu_de_loi="ung_truoc_don"):
	"""Tìm tiền về cho MỘT phiếu đặt, chiếm dòng sao kê và lập phiếu thu nháp.

	Chạy trong khoá hàng của phiếu đặt: nhịp 5 phút và lượt khách hỏi trạng
	thái cùng lúc thì lượt sau đọc lại phiếu thu của lượt trước, không lập đôi.
	"Đọc lại" phải là đọc HIỆN TẠI (for update): phiếu thu của đơn và chủ của
	dòng sao kê, sau khi đã khoá các dòng sao kê (Codex #531 f1).
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
	# Sau khoá: MỌI phép đọc dùng để QUYẾT là đọc hiện tại (Codex #531 f1).
	cac_phieu = ds_phieu(so_name, khoa=True)
	da = sum(p["so_tien"] for p in cac_phieu)
	if con_phai_thu(tong, cac_phieu) <= 0:
		return 0
	gds = gd_mang_ma(ma)
	if not gds:
		return 0
	hien = khoa_dong_sao_ke([g["name"] for g in gds])
	gds = [dien_dong(dict(g, **hien[g["name"]])) for g in gds if g["name"] in hien]
	# Codex #531 vòng 9: LỌC TRƯỚC, rồi mới chọn và cộng dồn. Một phép lọc duy nhất.
	cho_phep = dss.tai_khoan_duoc_khop()
	tk_so_cai = {tk: frappe.db.get_value("Bank Account", tk, "account")
		for tk in sorted({g.get("bank_account") for g in gds if g.get("bank_account") in cho_phep})}
	gds = loc_dong_sao_ke(gds, lambda tk: dss.ly_do_tai_khoan_sepay(tk, cho_phep), tk_so_cai)[0]
	if not gds:
		return 0
	ten_gd = [g["name"] for g in gds]
	chu = dss.chu_cua_giao_dich(ten_gd)
	chu.update(chu_hien_tai(ten_gd))
	nhan, xem = chon_giao_dich(gds, ma, re_ma, chu, toi_thieu_cua(so, tong), tong, da, ten_toi_thieu)
	if xem:
		frappe.log_error(json.dumps(xem, ensure_ascii=False), "%s: sao kê cần xem lại %s" % (tieu_de_loi, ma))
	lap = 0
	for x in nhan:
		g = x["gd"]
		tk = tk_so_cai[g["bank_account"]]
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
	mô đun gọi kiểm TRƯỚC khi vào đây.

	`anh`: [{ten, noi_dung}], ẢNH HOẶC PDF (Codex #531 f3). Không đính được
	tệp nào và phiếu cũng chưa có tệp thì báo ngay, không gọi ghi sổ để hook
	`chan_thieu_dinh_kem` trả câu Uỷ nhiệm chi khó hiểu cho kế toán."""
	# Cùng thứ tự khoá với `khop`: phiếu đặt, dòng sao kê, phiếu thu.
	frappe.db.sql("select name from `tabSales Order` where name=%s for update", (so_name,))
	pe = frappe.get_doc(PE, phieu)
	if pe.get("vgb_phieu_dat") != so_name or int(pe.docstatus) != 0 or not pe.get("vgb_gd_tkr"):
		frappe.throw("Phiếu %s không phải phiếu thu nháp của đơn này." % phieu)
	g = frappe.db.get_value(BT, pe.vgb_gd_tkr, ["docstatus", "deposit"], as_dict=True)
	if not g or int(g.docstatus) != 1 or tron(g.deposit) + LECH < tron(pe.paid_amount):
		frappe.throw("Dòng sao kê %s của phiếu không còn hợp lệ. Kế toán đối chiếu tay." % pe.vgb_gd_tkr)
	# Hàng rào cuối: một dòng sao kê chỉ MỘT phiếu thu được ghi sổ. Nháp đôi
	# lập trước bản sửa #531 (hoặc lọt bằng đường nào khác) dừng ở đây.
	khoa_dong_sao_ke([pe.vgb_gd_tkr])
	khac = [p["name"] for p in phieu_chiem([pe.vgb_gd_tkr]) if p["name"] != pe.name]
	if khac:
		frappe.throw("Dòng sao kê %s đã có phiếu thu %s chiếm. Không ghi sổ thêm phiếu %s; kế toán đối chiếu "
			"rồi huỷ phiếu thừa." % (pe.vgb_gd_tkr, ", ".join(khac), pe.name))
	if isinstance(anh, str):
		anh = frappe.parse_json(anh or "[]") or []
	ds, loi = loc_giay_bao_co(anh)
	if loi:
		frappe.throw(loi)
	n = dinh_giay_bao_co(pe.name, ds)
	if n <= 0 and not frappe.db.count("File", {"attached_to_doctype": PE, "attached_to_name": pe.name}):
		frappe.throw("Phiếu %s chưa có giấy báo Có đính kèm. Chọn ảnh hoặc tệp PDF giấy báo Có rồi bấm "
			"Đính và ghi sổ lại." % pe.name)
	pe.flags.ignore_permissions = True
	pe.submit()
	return pe


def dinh_giay_bao_co(pe_name, ds):
	"""Đính các tệp đã qua `loc_giay_bao_co` vào phiếu thu. Trả số tệp đã đính.

	Không nuốt lỗi từng tệp như `tra_truoc_khach._dinh_tep`: tệp không lưu được
	thì nói ngay tên tệp, chưa ghi sổ gì."""
	from vagabond.loi_csdl import chet_giao_dich

	n = 0
	for ten, noi in ds or []:
		try:
			f = frappe.get_doc({"doctype": "File", "file_name": ten, "attached_to_doctype": PE,
				"attached_to_name": pe_name, "content": noi, "decode": True, "is_private": 1})
			f.flags.ignore_permissions = True
			f.insert(ignore_permissions=True)
		except Exception as e:
			if chet_giao_dich(e):
				raise
			frappe.log_error(frappe.get_traceback(), "ung_truoc_don: đính giấy báo Có")
			frappe.throw("Chưa lưu được tệp %s vào phiếu %s. Chọn lại tệp rồi bấm Đính và ghi sổ lại." % (ten, pe_name))
		n += 1
	return n


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
