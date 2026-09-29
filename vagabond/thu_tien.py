# -*- coding: utf-8 -*-
"""Thu tiền hoá đơn bán: ghi chứng từ thật, và tính đúng số còn nợ.

VÌ SAO CÓ TỆP NÀY - đo trên số liệu thật ngày 04/09/2026
--------------------------------------------------------------------
Anh Việt chuyển phản ánh của bên Loan Anh: hoá đơn 92523 trị giá
43.978.500 đã chuyển khoản một nửa (21.989.250) mà màn công nợ vẫn ghi
khách nợ nguyên tờ; hoá đơn của Ms.Amber 21.000.000 đã thu đủ mà vẫn nằm
trong danh sách khách đang nợ.

Đo ra ba chỗ hỏng khác nhau, không phải một:

  1. `cong_no.ds_khach_no` cộng `grand_total` của mọi hoá đơn mang CỜ
     `vgb_pt_thanh_toan = "Công nợ"`. Cộng tổng tờ thì thu bao nhiêu cũng
     không trừ ra, và đọc cờ thì tờ nào cờ còn ghi Công nợ là còn nợ.
  2. Phiếu đòi nợ chuyển sang "Da thu du" mà KHÔNG sinh chứng từ thu tiền
     nào. Hoá đơn rơi khỏi phép loại "đang nằm trong phiếu chờ thu" (phép
     đó chỉ tính phiếu "Cho thu" và "Thu thieu") nên quay lại danh sách
     nợ. Đúng ca Ms.Amber: phiếu DNTT-26-09-00001 ghi đã thu 21.000.000,
     mà hoá đơn HDB-26-08-02800 vẫn `outstanding_amount` 21.000.000.
  3. Không có đường nào ghi "một phần đã thu, phần còn lại công nợ". Ô
     phương thức chỉ chứa một tên, chọn Công nợ là cả tờ thành nợ.

CON SỐ PHẢI BIẾT TRƯỚC KHI ĐỌC TIẾP
--------------------------------------------------------------------
Ngày 04/09/2026 hệ có 2.210 hoá đơn đã ghi sổ mang dư nợ, tổng
1.311.944.863 đồng. Chỉ 27 tờ (115.159.000) là công nợ thật. 2.183 tờ còn
lại là tiền ĐÃ THU (chuyển khoản 948 tờ, thẻ Shinhan 222 tờ, tiền mặt 111
tờ, Grab 344 tờ...) nhưng chưa bao giờ có chứng từ thu tiền, nên sổ cái
vẫn ghi khách nợ.

Nghĩa là KHÔNG ĐƯỢC đọc thẳng `outstanding_amount` làm số nợ: làm vậy màn
công nợ nhảy từ 115 triệu lên 1,31 tỷ trong một đêm và cả tiệm hoảng.

Anh Việt chốt 04/09/2026: chỉ làm cho tờ TỪ NAY, 2.183 tờ cũ liệt kê ra
cho chị Dung tự quyết, máy không đụng (điều 11).

LUẬT TÍNH SỐ NỢ - đọc kỹ trước khi sửa
--------------------------------------------------------------------
"Công nợ" KHÔNG phải một phương thức thanh toán thành công. Nó là tên gọi
của phần CHƯA THU. Nên:

    đã thu thật   = tổng các dòng thanh toán có phương thức KHÁC Công nợ
    còn nợ theo dòng = tổng đơn trừ đã thu thật
    còn nợ        = min(dư nợ sổ cái, còn nợ theo dòng)

Phép `min` là chỗ gánh cả ba ca cùng lúc:

  * Tờ MỚI có chứng từ thu tiền: hai vế bằng nhau, lấy cái nào cũng đúng.
  * Tờ 92523: sổ cái ghi 43.978.500, dòng ghi đã thu 21.989.250, ra
    21.989.250 - đúng số Loan Anh cần thấy.
  * 2.183 tờ CŨ đã thu bằng chuyển khoản mà chưa có chứng từ: không dòng
    nào, cờ không phải Công nợ, nên còn nợ theo dòng bằng 0, ra 0. Chúng
    không nhảy vào màn công nợ.

Sổ cái luôn được tôn trọng: đã ghi nhận thu rồi thì `min` kéo xuống ngay,
không bao giờ đòi khách số tiền họ đã trả.
"""

import frappe
from frappe.utils import flt, nowdate

SI = "Sales Invoice"

# "Công nợ" và "Chưa thu" là NHÃN CỦA PHẦN CHƯA TRẢ, không phải tiền vào.
# Cộng chúng vào phần đã thu là tự xoá sổ nợ của mình.
PT_KHONG_PHAI_THU = ("Công nợ", "Chưa thu", "Ghi nợ")

# Hàng tặng không phải một đường tiền vào, cũng không phải một khoản nợ.
# Tờ đã tất toán rồi, nhưng tất toán bằng CHI PHÍ biếu tặng chứ không bằng
# tiền: xem vagabond/hang_tang.py, nó có đường ghi sổ riêng vào 64181 và
# 64182. Sinh chứng từ thu cho nó là dựng ra một khoản tiền không ai trả.
#
# Nên nó nằm riêng khỏi PT_KHONG_PHAI_THU: vào danh sách đó thì nó lại bị
# tính thành nợ, và màn công nợ sẽ đi đòi khách một hộp bánh mình tặng.
PT_KHONG_SINH_PHIEU = ("Hàng tặng",)


def khong_sinh_phieu(pt):
	"""Phương thức đã tất toán tờ nhưng KHÔNG bằng tiền. THUẦN."""
	return (pt or "").strip() in PT_KHONG_SINH_PHIEU


# ------------------------------------------------------------ phần thuần


def _so(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def la_cong_no(pt):
	"""Tên phương thức này có phải là nhãn của phần chưa thu không. THUẦN."""
	return (pt or "").strip() in PT_KHONG_PHAI_THU


def da_thu_that(dong):
	"""Tiền THẬT SỰ đã vào, cộng từ các dòng thanh toán. THUẦN.

	Bỏ mọi dòng mang nhãn công nợ. Bỏ dòng số tiền âm hoặc bằng không:
	dòng âm là dấu hiệu gõ nhầm, cộng vào là tự giảm số phải đòi.
	"""
	t = 0.0
	for d in dong or []:
		if not isinstance(d, dict):
			continue
		if la_cong_no(d.get("pt")):
			continue
		so = _so(d.get("so_tien"))
		if so > 0:
			t += so
	return t


def da_thu_theo_pt(dong):
	"""Đã thu bao nhiêu theo TỪNG phương thức. THUẦN.

	Trả list cặp (phương thức, số tiền), giữ thứ tự gặp lần đầu. Màn hoá
	đơn phải bày được từng dòng chứ không chỉ một con số tổng, đó là yêu
	cầu anh Việt 04/09: *"Hiển thị minh bạch trên hóa đơn: tổng hóa đơn,
	đã thu theo từng phương thức, còn nợ, trạng thái thanh toán."*
	"""
	gom, thu_tu = {}, []
	for d in dong or []:
		if not isinstance(d, dict) or la_cong_no(d.get("pt")):
			continue
		so = _so(d.get("so_tien"))
		if so <= 0:
			continue
		pt = (d.get("pt") or "").strip() or "(chưa rõ)"
		if pt not in gom:
			gom[pt] = 0.0
			thu_tu.append(pt)
		gom[pt] += so
	return [(pt, gom[pt]) for pt in thu_tu]


def con_no_cua(tong_don, du_no_so_cai, dong, pt_chinh):
	"""Số tiền hoá đơn này THẬT SỰ còn phải đòi khách. THUẦN.

	`du_no_so_cai` là `outstanding_amount` của hoá đơn. Xem phần đầu tệp
	để biết vì sao không đọc thẳng ô đó.

	Không có dòng thanh toán nào thì quay về cách cũ: cờ ghi Công nợ mới
	tính là nợ. Đó là cửa giữ cho 2.183 tờ cũ nằm yên chỗ của chúng.
	"""
	tong = _so(tong_don)
	if tong <= 0:
		return 0.0
	co_dong = bool([d for d in (dong or []) if isinstance(d, dict) and _so(d.get("so_tien")) > 0])
	if co_dong:
		theo_dong = tong - da_thu_that(dong)
	else:
		theo_dong = tong if la_cong_no(pt_chinh) else 0.0
	if theo_dong <= 0:
		return 0.0
	so_cai = _so(du_no_so_cai)
	# Sổ cái đã ghi nhận thu tới đâu thì tôn trọng tới đó. Không bao giờ
	# đòi khách số tiền chứng từ đã ghi là họ trả rồi.
	return max(0.0, min(so_cai, theo_dong))


def trang_thai_thu(tong_don, con_no):
	"""Một chữ cho màn hình. THUẦN."""
	tong = _so(tong_don)
	no = _so(con_no)
	if no <= 0:
		return "Đã thanh toán"
	if no >= tong - 1:
		return "Chưa thu"
	return "Thu một phần"


def khoa_chong_trung(si_name, nguon):
	"""Khoá nhận diện một lần thu tiền, để không ghi hai lần cùng một khoản.

	Anh Việt 04/09/2026: *"Chống tạo Payment Entry trùng khi nhân viên bấm
	lại, reload trang hoặc webhook trả lại."* Khoá đi vào ô `reference_no`
	của chứng từ, nên phép chặn nằm ở DỮ LIỆU chứ không nằm ở nút bấm -
	bấm lại, tải lại trang hay webhook gọi lại đều đụng cùng một khoá.
	"""
	return ("THU:%s:%s" % ((si_name or "").strip(), (nguon or "").strip()))[:140]


# ------------------------------- phiếu thu nháp: tiền đã về, chờ ghi sổ
#
# Issue #380, 28/09/2026. Tiền khách chuyển đã về tài khoản và máy đã tự lập
# phiếu thu, nhưng phiếu kẹt ở nháp vì chốt 16/08 bắt chứng từ qua ngân hàng
# phải có tệp đính kèm (chung_tu_tien.chan_thieu_dinh_kem). Đo ngày 28/09:
# 1.428 phiếu, 1,33 tỷ; sổ cái vẫn ghi khách còn nợ nên màn Công nợ vẫn đòi
# những khách đã trả.
#
# Anh Việt chốt 28/09: KHÔNG coi riêng giao dịch ngân hàng là đủ chứng từ.
# Phải có uỷ nhiệm chi khách gửi đính vào phiếu thì mới ghi sổ.
#
# Codex #381: chỉ được tách một khoản ra khỏi "còn phải đòi" khi giao dịch
# ngân hàng đã được XÁC MINH độc lập, không phải cứ có phiếu nháp là tách.
# Phiếu nhập tay, phiếu lỗi, phiếu treo lâu mà chưa có tiền về thì vẫn là nợ.

TRUONG_MOI = {
	"Payment Entry": [
		{
			"fieldname": "vgb_thu_unc",
			"label": "Uỷ nhiệm chi khách gửi",
			"fieldtype": "Small Text",
			"read_only": 1,
			"insert_after": "vgb_chi_unc",
			"description": (
				"Ảnh hoặc tệp chuyển khoản khách gửi cho phiếu thu này. Anh Việt "
				"chốt 28/09/2026: có tệp này mới ghi sổ phiếu thu tiền về ngân hàng."
			),
		},
		# Anh Việt 29/09/2026: trên Desk cũng phải có ô đính UNC khách gửi cho
		# đồng bộ với app. Tệp đính ở ô này được gộp vào ô danh sách phía
		# trên lúc lưu (gop_unc_desk), nên mọi phép đếm chỉ đọc MỘT ô.
		{
			"fieldname": "vgb_thu_unc_tep",
			"label": "Đính uỷ nhiệm chi khách gửi",
			"fieldtype": "Attach",
			"insert_after": "vgb_thu_unc",
			"depends_on": "eval:doc.payment_type=='Receive' && doc.party_type=='Customer'",
			"description": (
				"Phiếu thu tiền khách chuyển khoản có gắn hoá đơn: đính ảnh hoặc PDF "
				"chuyển khoản khách gửi vào đây rồi lưu, sau đó mới ghi sổ được."
			),
		},
	],
}

LECH = 0.5


def _ti_gia_mot(v):
	"""Tỉ giá trống coi là 1 (phiếu cũ, dữ liệu kiểm), có số thì phải đúng 1."""
	if v in (None, ""):
		return True
	return abs(_so(v) - 1) < 1e-9


# Trường tiền tệ phải đọc kèm mỗi khi đưa phiếu thu vào xac_minh_tien_ve.
TRUONG_TIEN_TE = ["received_amount", "paid_from_account_currency", "paid_to_account_currency",
	"source_exchange_rate", "target_exchange_rate"]


def tien_phia_ngan_hang(pe):
	"""Số tiền phiếu thu tính theo tiền của TÀI KHOẢN NGÂN HÀNG nhận. THUẦN.

	Codex #382 vòng 5: `paid_amount` là tiền phía khách, còn giao dịch ngân
	hàng và phần lõi cấp cho phiếu tính theo tiền tài khoản nhận
	(`received_amount`). Phiếu 100 USD ghi có 2.500.000 đ mà so `paid_amount`
	thì giao dịch 1.000.000 đ vẫn lọt. Màn này chỉ nhận phiếu tiền đồng thuần:
	hai tài khoản đều VND, hai tỉ giá đều 1, tiền hai phía bằng nhau; khác đi
	thì trả lý do để kế toán xử lý tay trên Desk.
	Trả (số tiền, câu lý do); lý do rỗng là dùng được.
	"""
	pe = pe or {}
	for truong in ("paid_from_account_currency", "paid_to_account_currency"):
		if (pe.get(truong) or "VND") != "VND":
			return (0.0, "Phiếu thu dùng ngoại tệ, kế toán ghi sổ tay trên Desk.")
	for truong in ("source_exchange_rate", "target_exchange_rate"):
		if not _ti_gia_mot(pe.get(truong)):
			return (0.0, "Phiếu thu có tỉ giá khác 1, kế toán ghi sổ tay trên Desk.")
	tra = _so(pe.get("paid_amount"))
	nhan = pe.get("received_amount")
	if nhan in (None, ""):
		return (tra, "")
	nhan = _so(nhan)
	if abs(nhan - tra) > LECH:
		return (0.0, "Tiền khách trả và tiền vào tài khoản trên phiếu thu lệch nhau, kế toán soát tay trên Desk.")
	return (nhan, "")


def xac_minh_tien_ve(pe, gd, tk_gd="", cty_gd=""):
	"""Phiếu thu nháp này có khớp một khoản tiền ĐÃ VỀ thật không. THUẦN.

	`pe` là phiếu thu (dict), `gd` là Bank Transaction mang cùng số tham
	chiếu (dict hoặc None), `tk_gd` và `cty_gd` là tài khoản sổ cái và công
	ty của tài khoản ngân hàng nhận giao dịch.

	Soát đủ các điểm Codex nêu ở #381 F2: chiều tiền, tài khoản, công ty,
	tiền tệ, đã nối chứng từ khác chưa, số chưa phân bổ còn đủ không.
	Trả (đúng hay sai, câu lý do bằng tiếng người).
	"""
	pe = pe or {}
	if (pe.get("payment_type") or "") != "Receive":
		return (False, "Không phải phiếu thu tiền khách.")
	if int(pe.get("docstatus") or 0) != 0:
		return (False, "Phiếu thu đã ghi sổ hoặc đã huỷ.")
	ref = (pe.get("reference_no") or "").strip()
	if not ref:
		return (False, "Phiếu thu không mang số giao dịch ngân hàng.")
	if not gd:
		return (False, "Không tìm thấy giao dịch ngân hàng mang số %s." % ref)
	if gd.get("trung"):
		return (False, "Có %s giao dịch ngân hàng cùng số %s, cần kế toán chọn tay." % (gd.get("trung"), ref))
	if int(gd.get("docstatus") or 0) != 1:
		return (False, "Giao dịch ngân hàng %s chưa được xác nhận." % ref)
	if _so(gd.get("withdrawal")) > 0 or _so(gd.get("deposit")) <= 0:
		return (False, "Giao dịch %s không phải tiền vào." % ref)
	if (gd.get("currency") or "VND") != "VND":
		return (False, "Giao dịch %s không phải tiền đồng." % ref)
	if tk_gd and (pe.get("paid_to") or "") != tk_gd:
		return (False, "Giao dịch %s về tài khoản khác với tài khoản trên phiếu thu." % ref)
	if cty_gd and (pe.get("company") or "") != cty_gd:
		return (False, "Giao dịch %s thuộc công ty khác." % ref)
	if _so(gd.get("allocated_amount")) > LECH or int(gd.get("so_noi") or 0) > 0:
		return (False, "Giao dịch %s đã nối với chứng từ khác." % ref)
	tien, sai_tien = tien_phia_ngan_hang(pe)
	if sai_tien:
		return (False, sai_tien)
	con = _so(gd.get("unallocated_amount"))
	if tien <= 0:
		return (False, "Phiếu thu không có số tiền.")
	if con + LECH < tien:
		return (False, "Giao dịch %s còn %s đ chưa phân bổ, ít hơn số trên phiếu %s đ."
			% (ref, "{:,.0f}".format(con).replace(",", "."), "{:,.0f}".format(tien).replace(",", ".")))
	return (True, "")


def chia_con_no(con_no, phan_bo, da_xac_minh):
	"""Chia số còn nợ trên sổ cái thành (còn phải đòi, tiền đã về chờ ghi sổ). THUẦN.

	Codex #382 vòng 8: hoá đơn nợ 1.000.000 đ đã có 600.000 đ về tài khoản
	(giao dịch xác minh độc lập, phiếu thu còn nháp) thì Sales chỉ còn phải
	đòi 400.000 đ. Hoá đơn vẫn nằm ở nhóm đang nợ, số đòi trừ phần đã về.
	Phủ đủ (lệch tới 1 đ làm tròn) thì còn phải đòi 0, hoá đơn tách hẳn
	sang "Tiền đã về, chờ ghi sổ" như tach_tien_da_ve. Chưa xác minh thì
	không trừ gì: tiền chưa chứng minh là đã về.
	"""
	no = _so(con_no)
	if no <= 0:
		return (0.0, 0.0)
	ve = _so(phan_bo) if da_xac_minh else 0.0
	if ve <= 0:
		return (no, 0.0)
	if ve + 1 >= no:
		return (0.0, no)
	return (no - ve, ve)


def chia_no_hoa_don(rows, ve):
	"""Chia danh sách hoá đơn còn nợ theo tiền đã về. THUẦN.

	`rows` là hoá đơn còn nợ (mỗi dòng có name, con_no, customer,
	vgb_khach_no), `ve` là kết quả gom_tien_da_ve theo hoá đơn. Gán cho mỗi
	dòng `con_doi` (còn phải đòi) và `da_ve` (đã về, chờ ghi sổ) theo
	chia_con_no. Trả (các dòng còn phải đòi, thẻ tiền đã về {so_hd, tien},
	tập khách có tiền về). Tách khỏi cong_no để kiểm được không cần Frappe
	(cong_no kéo ban_hang, ban_hang kéo requests).
	"""
	con, the, khach = [], {"so_hd": 0, "tien": 0.0}, set()
	for r in rows or []:
		p = (ve or {}).get(r["name"]) or {}
		r["con_doi"], r["da_ve"] = chia_con_no(r["con_no"], p.get("phan_bo"), p.get("da_xac_minh"))
		if r["da_ve"] > 0:
			the["so_hd"] += 1
			the["tien"] += r["da_ve"]
			khach.add(r.get("vgb_khach_no") or r.get("customer") or "")
		if r["con_doi"] > 0:
			con.append(r)
	return con, the, khach


def loc_khach_no(ds_khach, tim):
	"""Lọc danh sách khách đang nợ theo ô tìm, kèm tổng của phần lọc ra. THUẦN.

	Khớp tên khách, mã khách hoặc số hoá đơn. Trả (danh sách khớp, tổng còn
	phải đòi của danh sách khớp). Codex #382 vòng 9: thẻ trên đầu màn giữ
	tổng nợ thật của mọi khách (không teo theo chữ đang gõ), còn phần đang
	hiện phải có tổng riêng do máy chủ cộng, để Sales không đọc nhầm số.
	"""
	tim = (tim or "").strip().lower()
	ds = list(ds_khach or [])
	if tim:
		ds = [v for v in ds if tim in (v.get("ten") or "").lower() or tim in (v.get("khach") or "").lower()
			or any(tim in (d.get("name") or "").lower() for d in v.get("hd") or [])]
	return ds, sum(_so(v.get("tien")) for v in ds)


def tach_tien_da_ve(con_no, phan_bo, da_xac_minh):
	"""Hoá đơn này có chuyển sang nhóm "Tiền đã về, chờ ghi sổ" không. THUẦN.

	Chỉ khi phiếu thu đã xác minh VÀ phần phân bổ phủ đủ số còn nợ. Phủ một
	phần thì hoá đơn vẫn ở nhóm đang nợ: khách còn thiếu thật.
	"""
	no = _so(con_no)
	return bool(da_xac_minh) and no > 0 and _so(phan_bo) + 1 >= no


def gom_tien_da_ve(ds):
	"""Cộng tiền đã về theo từng hoá đơn, từ các phiếu thu nháp ĐÃ XÁC MINH. THUẦN.

	`ds` là kết quả `phieu_thu_nhap`: mỗi phiếu có `da_xac_minh`, `gd` (giao
	dịch ngân hàng) và `hd` = [(hoá đơn, số phân bổ)]. Trả {hoá đơn:
	{"phan_bo": tổng, "cac_pe": [...], "da_xac_minh": 1}}.

	Codex #382: khách trả một hoá đơn bằng HAI lần chuyển (600.000 đ rồi
	400.000 đ) thì hai phiếu cộng lại mới phủ đủ; lấy phiếu lớn nhất là để
	hoá đơn đã trả đủ nằm lại "Đang nợ". Nhưng một giao dịch ngân hàng chỉ
	được tính MỘT lần cho một hoá đơn: hai phiếu nháp trùng cùng một số FT
	không phải hai lần tiền về.

	Codex #382 vòng 2: khoá chống trùng không được chứa hoá đơn. Hai phiếu
	nháp cùng một giao dịch 1.000.000 đ mà chia cho HAI hoá đơn khác nhau
	thì trước đây cả hai hoá đơn cùng sang "Tiền đã về" (2.000.000 đ từ một
	lần tiền về). Giờ mỗi giao dịch chỉ một phiếu được tính, chọn ở MỘT chỗ
	là `mot_phieu_moi_giao_dich`.
	"""
	ra = {}
	for p in mot_phieu_moi_giao_dich(ds):
		if not p.get("da_xac_minh"):
			continue
		for si, pb in p.get("hd") or []:
			o = ra.setdefault(si, {"phan_bo": 0.0, "cac_pe": [], "da_xac_minh": 1})
			o["phan_bo"] += _so(pb)
			if p.get("pe") not in o["cac_pe"]:
				o["cac_pe"].append(p.get("pe"))
	return ra


def _khoa_gd(p):
	return (p.get("ma_gd") or p.get("gd") or "").strip()


def mot_phieu_moi_giao_dich(ds, ung_vien=None):
	"""Mỗi giao dịch ngân hàng chỉ MỘT phiếu thu nháp được coi là đã xác minh. THUẦN.

	`ds`: các phiếu (dict có `pe`, `tien`, `ma_gd` hoặc `gd`, `da_xac_minh`).
	`ung_vien`: {mã giao dịch: [(phiếu, số tiền), ...]} gồm MỌI phiếu thu nháp
	mang mã đó trên hệ thống, kể cả phiếu nằm ngoài `ds` (màn chỉ đọc phiếu
	của vài hoá đơn). Không truyền thì lấy từ chính `ds`.

	Phiếu được giữ là phiếu tiền lớn nhất, bằng tiền thì mã nhỏ hơn, nên kết
	quả không đổi theo cách lọc màn. Phiếu còn lại hạ về chưa xác minh, kèm
	câu lý do, để hoá đơn của nó vẫn nằm trong "Đang nợ" cho kế toán xem tay.
	Phiếu thắng mà không tự xác minh được thì không phiếu nào được tính.
	"""
	ds = [dict(p) for p in (ds or [])]
	if ung_vien is None:
		ung_vien = {}
		for p in ds:
			k = _khoa_gd(p)
			if k:
				ung_vien.setdefault(k, []).append((p.get("pe"), _so(p.get("tien"))))
	thang = {}
	for k, cac in ung_vien.items():
		cac = [(ten, _so(t)) for ten, t in cac if ten]
		if cac:
			thang[k] = sorted(cac, key=lambda x: (-x[1], str(x[0])))[0][0]
	for p in ds:
		k = _khoa_gd(p)
		if not p.get("da_xac_minh") or not k or k not in thang:
			continue
		if thang[k] != p.get("pe"):
			p["da_xac_minh"] = 0
			p["ly_do"] = ("Giao dịch %s đã có phiếu thu nháp %s; phiếu này cần kế toán xem tay."
				% (k, thang[k]))
	return ds


def dem_tep_unc(ds_url_o, url_da_gan):
	"""Số tệp uỷ nhiệm chi khách gửi thật sự nằm trên phiếu. THUẦN.

	`ds_url_o` là danh sách đường dẫn ghi trong ô `vgb_thu_unc`, `url_da_gan`
	là các đường dẫn File đang gắn vào đúng phiếu này. Chỉ đếm tệp có mặt ở
	CẢ HAI: có trong ô (người dùng đính đúng chỗ) và còn gắn vào phiếu (tệp
	thật, chưa bị gỡ hay chuyển sang chứng từ khác).

	Codex #382: đếm mọi File gắn vào phiếu là để một ảnh chụp màn hình bất
	kỳ, hay tệp đính ở mục khác, mở khoá ghi sổ mà không có uỷ nhiệm chi.
	"""
	gan = set(url_da_gan or [])
	ra = []
	for u in ds_url_o or []:
		u = str(u or "").strip()
		if u and u in gan and u not in ra:
			ra.append(u)
	return len(ra)


# Hai ô là nơi đính uỷ nhiệm chi khách gửi: ô danh sách của app và ô đính
# trên Desk (gộp vào ô danh sách ở gop_unc_desk).
O_UNC = ("vgb_thu_unc", "vgb_thu_unc_tep")


def url_trong_o_unc(ds_file):
	"""Tập đường dẫn File gắn vào phiếu QUA Ô UNC khách gửi. THUẦN.

	`ds_file` là các dòng File đang gắn vào đúng phiếu, mỗi dòng có
	`file_url` và `attached_to_field`. Codex #382 vòng 7: tệp đã gắn vào
	phiếu ở mục khác (nút kẹp giấy, ô chứng từ khác) mà ghi tên vào ô UNC thì
	không được tính: đó là đổi nhãn một ảnh có sẵn để qua cổng ghi sổ.
	"""
	return {str(r.get("file_url")) for r in ds_file or []
		if r.get("file_url") and (r.get("attached_to_field") or "") in O_UNC}


def url_unc_that(ten_pe, ds_file):
	"""Tập đường dẫn là UNC khách gửi THẬT của phiếu `ten_pe`. THUẦN.

	`ds_file` là MỌI dòng File mang các đường dẫn đang xét, ở bất cứ chứng
	từ nào (file_url, attached_to_doctype, attached_to_name,
	attached_to_field). Một đường dẫn chỉ được tính khi có ít nhất một dòng
	gắn vào đúng phiếu qua ô UNC VÀ không có dòng nào nằm chỗ khác.

	Vì sao phải xét cả dòng ở chỗ khác (bench #382 vòng 8): Frappe v16.27.1
	`frappe/core/doctype/file/utils.py` `attach_files_to_document` chạy khi
	lưu mọi chứng từ; ô Attach trỏ vào một đường dẫn đã có thì nó CHÉP ra một
	dòng File mới gắn qua đúng ô đó. Trỏ ô Desk vào ảnh kẹp giấy, hay vào UNC
	của phiếu khác, là có ngay một dòng "gắn qua ô UNC". Tệp tải lên thật qua
	ô UNC (app hoặc Desk) chỉ có một dòng, nằm đúng chỗ.
	"""
	dung_cho, sai_cho = set(), set()
	for r in ds_file or []:
		u = str(r.get("file_url") or "")
		if not u:
			continue
		if (r.get("attached_to_doctype") == PE and r.get("attached_to_name") == ten_pe
				and (r.get("attached_to_field") or "") in O_UNC):
			dung_cho.add(u)
		else:
			sai_cho.add(u)
	return dung_cho - sai_cho


def tep_muc_khac(ds_url, ds_file):
	"""Đường dẫn người dùng gửi làm UNC mà đang gắn vào phiếu ở MỤC KHÁC. THUẦN.

	Tệp mới tải lên (chưa gắn đâu) và tệp đã gắn qua ô UNC thì được; tệp đã
	gắn vào phiếu mà không qua ô UNC thì trả ra để từ chối.
	"""
	gan = {str(r.get("file_url")) for r in ds_file or [] if r.get("file_url")}
	trong = url_trong_o_unc(ds_file)
	ra = []
	for u in ds_url or []:
		u = str(u or "").strip()
		if u and u in gan and u not in trong and u not in ra:
			ra.append(u)
	return ra


def can_unc_khach(pe, co_hoa_don, khop_giao_dich):
	"""Phiếu này có bắt buộc ô UNC khách gửi lúc ghi sổ không. THUẦN.

	Đúng tập phiếu mà màn Công nợ tab Tiền đã về xử lý: phiếu thu tiền khách
	(Receive, Customer) vào tài khoản ngân hàng, có phân bổ vào hoá đơn bán,
	mang mã giao dịch khớp một dòng sao kê ngân hàng. Trừ phiếu thu đặt bánh
	(có ô phiếu đặt) và phiếu của hồ sơ hoàn tiền: hai luồng đó có luật chứng
	từ riêng (giấy báo Có), anh Việt không đổi.

	Anh Việt 29/09/2026: Desk và app phải cùng một luật (Codex #382 vòng 3).
	"""
	from vagabond.chung_tu_tien import la_ngan_hang

	pe = pe or {}
	if (pe.get("payment_type") or "") != "Receive" or (pe.get("party_type") or "") != "Customer":
		return False
	if not la_ngan_hang(pe.get("paid_to")):
		return False
	if pe.get("vgb_phieu_dat") or pe.get("vgb_hoan_tien"):
		return False
	return bool(co_hoa_don) and bool(khop_giao_dich)


def gop_tep(ds_url, them):
	"""Thêm một đường dẫn tệp vào danh sách, không trùng, giữ thứ tự. THUẦN."""
	ra = [str(u).strip() for u in (ds_url or []) if str(u or "").strip()]
	them = str(them or "").strip()
	if them and them not in ra:
		ra.append(them)
	return ra


def doi_unc_desk(ds_url, cu, moi):
	"""Đối chiếu ô danh sách UNC với ô Desk khi lưu. THUẦN.

	cu: giá trị ô Desk trước khi lưu, moi: giá trị bây giờ. Ô Desk bị xoá
	hoặc thay thì bỏ đường dẫn cũ; có giá trị mới thì gộp vào (không trùng).
	Tệp đính qua app không đụng tới."""
	cu = str(cu or "").strip()
	moi = str(moi or "").strip()
	ra = [str(u).strip() for u in (ds_url or []) if str(u or "").strip()]
	if cu and cu != moi:
		ra = [u for u in ra if u != cu]
	return gop_tep(ra, moi)


def soat_ghi_so_thu(da_xac_minh, ly_do, so_tep, la_ke_toan):
	"""Được bấm ghi sổ phiếu thu chưa. THUẦN. Trả (được hay không, câu lý do)."""
	if not da_xac_minh:
		return (False, ly_do or "Phiếu thu chưa khớp giao dịch ngân hàng.")
	if int(so_tep or 0) <= 0:
		return (False, "Chưa có uỷ nhiệm chi khách gửi. Đính ảnh chuyển khoản khách gửi rồi ghi sổ.")
	if not la_ke_toan:
		return (False, "Đã có uỷ nhiệm chi. Chỉ kế toán bấm ghi sổ phiếu thu.")
	return (True, "")


def duoi_ma(ma, so=4):
	"""Bốn số cuối của mã giao dịch cho nhãn gọn trên màn. THUẦN."""
	ma = (ma or "").strip()
	return ma[-so:] if len(ma) > so else ma


# ------------------------------------------------------- phần cần Frappe


def dong_cua(si_name):
	"""Các dòng thanh toán của một hoá đơn."""
	from vagabond import thanh_toan_nhieu as ttn

	return ttn.dong_cua(si_name)


def bang_dong_cua(cac_si):
	"""Dòng thanh toán của nhiều hoá đơn, đọc một lượt."""
	from vagabond import thanh_toan_nhieu as ttn

	return ttn.bang_dong_cua(cac_si)


def si_co_dong_cong_no():
	"""Hoá đơn có ÍT NHẤT một dòng mang nhãn công nợ.

	Trước 04/09/2026 màn công nợ chỉ quét theo ô phương thức chính. Tờ trả
	hỗn hợp thì ô chính mang dòng LỚN NHẤT, nên tờ nào phần đã thu lớn hơn
	phần nợ là ô chính ghi "Chuyển khoản" và cả khoản nợ biến mất khỏi màn.
	Đây là đường thứ hai để tìm ra chúng.
	"""
	try:
		ds = frappe.get_all(
			"Vagabond Dong Thanh Toan",
			filters={"parenttype": SI, "pt": ["in", list(PT_KHONG_PHAI_THU)]},
			fields=["parent"], limit_page_length=0,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thu_tien: doc dong cong no")
		return set()
	return {r["parent"] for r in ds if r.get("parent")}


def tom_tat_thu(si_name):
	"""Tổng đơn, đã thu theo từng phương thức, còn nợ, trạng thái. CHỈ ĐỌC.

	Một chỗ tính duy nhất cho mọi màn cần bày con số này, để màn hoá đơn và
	màn công nợ không bao giờ nói hai số khác nhau về cùng một tờ.
	"""
	hd = frappe.db.get_value(
		SI, si_name,
		["name", "customer", "customer_name", "grand_total", "outstanding_amount",
			"vgb_pt_thanh_toan", "docstatus", "posting_date"],
		as_dict=True,
	)
	if not hd:
		return None
	dong = dong_cua(si_name)
	no = con_no_cua(hd.grand_total, hd.outstanding_amount, dong, hd.vgb_pt_thanh_toan)
	return {
		"name": hd.name,
		"khach": hd.customer or "",
		"ten_khach": hd.customer_name or "",
		"ngay": str(hd.posting_date or ""),
		"tong_don": flt(hd.grand_total),
		"da_thu": flt(hd.grand_total) - no,
		"theo_pt": [{"pt": p, "so_tien": flt(t)} for p, t in da_thu_theo_pt(dong)],
		"con_no": no,
		"trang_thai": trang_thai_thu(hd.grand_total, no),
		"du_no_so_cai": flt(hd.outstanding_amount),
		"co_dong": bool(dong),
	}


def tk_tien_thu(cong_ty, pt):
	"""Tiền thu bằng phương thức này VÀO tài khoản kế toán nào.

	CHỈ đọc tài khoản khai riêng cho chính phương thức đó. Không đoán, không
	lùi về tài khoản mặc định của công ty.

	VÌ SAO CHẶT ĐẾN THẾ - đo ngày 04/09/2026
	--------------------------------------------------------------------
	Cả 18 hình thức thanh toán trong hệ ĐỀU chưa khai tài khoản mặc định.
	Phép tra của luồng CHI (`tra_tien_app.tk_tien_chi`) có bốn đường lùi,
	đường cuối là tài khoản ngân hàng mặc định của công ty. Dùng nó cho
	luồng thu thì tiền mặt trong két cũng chạy vào tài khoản MB Bank, và
	sổ quỹ tiền mặt vĩnh viễn không khớp với két thật.

	Thà KHÔNG sinh chứng từ còn hơn sinh một chứng từ ghi sai chỗ tiền
	nằm: chưa ghi thì còn nhìn thấy mà đi ghi, ghi sai thì phải đi tìm.

	Trả cặp (tài khoản, Bank Account). Chưa khai thì trả cặp rỗng.
	"""
	cong_ty = (cong_ty or "").strip()
	pt = (pt or "").strip()
	if not (cong_ty and pt):
		return None, None
	if not frappe.db.exists("Mode of Payment", pt):
		return None, None
	tk = frappe.db.get_value(
		"Mode of Payment Account", {"parent": pt, "company": cong_ty}, "default_account"
	)
	if not tk:
		return None, None
	ba = frappe.db.get_value(
		"Bank Account", {"account": tk, "company": cong_ty, "is_company_account": 1}, "name"
	)
	return tk, ba


def loi_chua_khai_tk(pt):
	"""Câu báo khi chưa khai tài khoản cho một hình thức thanh toán.

	Anh Việt 04/09/2026: *"Mọi lỗi chặn thao tác phải nói rõ nguyên nhân và
	cách xử lý tiếp theo."* Nên câu này nói đúng ba điều: hỏng ở đâu, phải
	khai gì, và trong lúc chưa khai thì tờ hoá đơn ra sao.
	"""
	return (
		"Hình thức thanh toán \"%s\" chưa khai tài khoản tiền, nên chưa ghi "
		"nhận thanh toán vào sổ được. Nhờ kế toán mở Hình thức thanh toán "
		"\"%s\", thêm dòng công ty và chọn tài khoản tiền tương ứng (tiền mặt "
		"vào tài khoản quỹ, chuyển khoản vào tài khoản ngân hàng). Trong lúc "
		"chờ, hoá đơn vẫn đúng số tiền, chỉ là sổ cái còn ghi khách nợ." % (pt, pt)
	)


@frappe.whitelist()
def soat_hinh_thuc_chua_khai():
	"""CHỈ ĐỌC: hình thức thanh toán nào chưa khai tài khoản tiền.

	Đo ngày 04/09/2026: cả 18 hình thức đều chưa khai. Chưa khai xong thì
	luồng thu tiền mới không ghi được đồng nào vào sổ, nên đây là việc phải
	làm TRƯỚC khi nghiệm thu.
	"""
	if not ({"Accounts Manager", "System Manager"} & set(frappe.get_roles())):
		frappe.throw("Bảng này dành cho kế toán trưởng và quản lý hệ thống.")
	cty = frappe.db.get_single_value("Global Defaults", "default_company")
	ra = []
	for m in frappe.get_all("Mode of Payment", fields=["name", "enabled"], limit_page_length=0):
		if la_cong_no(m["name"]):
			continue
		tk, _ba = tk_tien_thu(cty, m["name"])
		if not tk:
			ra.append({"pt": m["name"], "dang_dung": bool(m.get("enabled"))})
	return {"cong_ty": cty, "chua_khai": ra, "so": len(ra)}


def _da_ghi_roi(khoa):
	"""Khoản thu mang khoá này đã có chứng từ chưa. Chặn ghi hai lần."""
	return bool(frappe.db.exists("Payment Entry", {"reference_no": khoa, "docstatus": ["<", 2]}))


def ghi_thu_tien(si_name, dong, nguon, ngay=None, ghi_chu=""):
	"""Sinh chứng từ thu tiền cho phần ĐÃ THU THẬT của một hoá đơn.

	`dong` là list dict {pt, so_tien}. Dòng mang nhãn công nợ bị bỏ qua -
	đó là phần chưa thu, ghi vào là tự xoá nợ của mình.

	Mỗi phương thức một chứng từ riêng, vì tiền vào những tài khoản khác
	nhau: tiền mặt vào két, chuyển khoản vào ngân hàng, quẹt thẻ vào tài
	khoản trung gian. Gộp một chứng từ là mất dấu ngay chỗ cần nhất.

	Trả về list tên chứng từ đã sinh. Đã sinh rồi thì trả list rỗng, không
	ném lỗi: người bấm hai lần không đáng bị một câu báo đỏ.
	"""
	hd = frappe.db.get_value(
		SI, si_name,
		["name", "company", "customer", "grand_total", "outstanding_amount",
			"due_date", "docstatus"],
		as_dict=True,
	)
	if not hd:
		frappe.throw("Không có hoá đơn %s." % si_name)
	if int(hd.docstatus or 0) != 1:
		frappe.throw("Hoá đơn %s chưa ghi sổ nên chưa ghi thu tiền được." % si_name)

	ngay = ngay or nowdate()
	ra = []
	con = flt(hd.outstanding_amount)
	for pt, so_tien in da_thu_theo_pt(dong):
		if con <= 0:
			break
		if khong_sinh_phieu(pt):
			# Hàng tặng: tờ đã tất toán bằng chi phí biếu tặng, không có
			# đồng nào vào két để mà lập phiếu thu.
			continue
		khoa = khoa_chong_trung(si_name, "%s|%s" % (nguon or "", pt))
		if _da_ghi_roi(khoa):
			continue
		phan_bo = min(flt(so_tien), con)
		if phan_bo <= 0:
			continue
		tk, ba = tk_tien_thu(hd.company, pt)
		if not tk:
			frappe.throw(loi_chua_khai_tk(pt))
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Receive"
		pe.company = hd.company
		pe.posting_date = ngay
		pe.party_type = "Customer"
		pe.party = hd.customer
		pe.paid_amount = phan_bo
		pe.received_amount = phan_bo
		pe.reference_no = khoa
		pe.reference_date = ngay
		if frappe.db.exists("Mode of Payment", pt):
			pe.mode_of_payment = pt
		pe.paid_to = tk
		if ba:
			pe.bank_account = ba
		pe.append("references", {
			"reference_doctype": SI,
			"reference_name": si_name,
			"total_amount": flt(hd.grand_total),
			"outstanding_amount": con,
			"allocated_amount": phan_bo,
			"due_date": hd.due_date,
		})
		pe.remarks = ("Thu tiền hoá đơn %s bằng %s, số tiền %s đ.%s" % (
			si_name, pt, "{:,.0f}".format(phan_bo),
			(" " + ghi_chu) if ghi_chu else ""))[:1000]
		pe.setup_party_account_field()
		pe.set_missing_values()
		pe.flags.ignore_permissions = True
		pe.insert(ignore_permissions=True)
		pe.submit()
		ra.append(pe.name)
		con -= phan_bo
	return ra


@frappe.whitelist()
def tom_tat(si=None):
	"""Cho màn hình: tờ này tổng bao nhiêu, đã thu gì, còn nợ bao nhiêu.

	Anh Việt 04/09/2026: *"Không bắt nhân viên tự suy ra trạng thái kế toán
	từ màn hình."* Một lần gọi ra đủ bốn con số, không ai phải cộng tay.
	"""
	si = (si or "").strip()
	if not si:
		return None
	if not frappe.has_permission(SI, "read", doc=si):
		frappe.throw("Không có quyền xem hoá đơn này.")
	return tom_tat_thu(si)


@frappe.whitelist()
def soat_thieu_chung_tu(gioi_han=500):
	"""CHỈ ĐỌC: những tờ đã thu tiền mà sổ cái vẫn ghi khách nợ.

	Đây là bảng anh Việt bảo liệt kê ra ngày 04/09/2026 thay vì để máy tự
	sửa. Đo hôm đó: 2.183 tờ, gần 1,2 tỷ, phần lớn là chuyển khoản và quẹt
	thẻ đã vào tài khoản từ lâu.

	KHÔNG sinh chứng từ, KHÔNG đụng một tờ nào - điều 11. Chị Dung đọc bảng
	này rồi quyết làm gì với chúng.
	"""
	if not ({"Accounts Manager", "System Manager"} & set(frappe.get_roles())):
		frappe.throw("Bảng này dành cho kế toán trưởng và quản lý hệ thống.")
	rows = frappe.get_all(
		SI,
		filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "posting_date", "customer_name", "grand_total",
			"outstanding_amount", "vgb_pt_thanh_toan"],
		order_by="posting_date asc", limit_page_length=0,
	)
	theo_pt, tong = {}, 0.0
	ra = []
	for r in rows:
		pt = (r.get("vgb_pt_thanh_toan") or "").strip()
		# To mang co Cong no la no THAT, khong nam trong bang nay.
		if la_cong_no(pt):
			continue
		o = theo_pt.setdefault(pt or "(chưa ghi phương thức)", {"so": 0, "tien": 0.0})
		o["so"] += 1
		o["tien"] += flt(r.outstanding_amount)
		tong += flt(r.outstanding_amount)
		if len(ra) < int(gioi_han or 500):
			ra.append(r)
	return {
		"so_to": sum(v["so"] for v in theo_pt.values()),
		"tong": tong,
		"theo_pt": [{"pt": k, "so": v["so"], "tien": v["tien"]}
			for k, v in sorted(theo_pt.items(), key=lambda x: -x[1]["tien"])],
		"hoa_don": ra,
	}


# ------------------------------------ phiếu thu nháp: phần cần Frappe (v534)

PE = "Payment Entry"
BT = "Bank Transaction"
VAI_KE_TOAN = {"AP Kiểm soát (FIN)", "Accounts Manager", "Accounts User", "System Manager"}


def la_ke_toan():
	return bool(VAI_KE_TOAN & set(frappe.get_roles()))


def _chia(ds, co=150):
	ds = list(ds)
	for i in range(0, len(ds), co):
		yield ds[i:i + co]


def _gd_theo_so(cac_so):
	"""Bank Transaction theo số tham chiếu, kèm tài khoản sổ cái và công ty."""
	ra, dem = {}, {}
	for lo in _chia({x for x in cac_so if x}):
		for g in frappe.get_all(
			BT, filters={"reference_number": ["in", lo], "docstatus": ["<", 2]},
			fields=["name", "reference_number", "docstatus", "date", "deposit", "withdrawal",
				"currency", "unallocated_amount", "allocated_amount", "bank_account"],
			limit_page_length=0,
		):
			k = g.reference_number
			dem[k] = dem.get(k, 0) + 1
			ra[k] = dict(g)
	# Giao dịch đã nối chứng từ nào chưa: đếm dòng con, không tin mỗi ô tiền.
	ten = [g["name"] for g in ra.values()]
	so_noi = {}
	for lo in _chia(ten):
		for r in frappe.get_all(
			"Bank Transaction Payments", filters={"parent": ["in", lo], "parenttype": BT},
			fields=["parent"], limit_page_length=0,
		):
			so_noi[r.parent] = so_noi.get(r.parent, 0) + 1
	tk = {}
	for ba in {g.get("bank_account") for g in ra.values() if g.get("bank_account")}:
		tk[ba] = frappe.db.get_value("Bank Account", ba, ["account", "company"], as_dict=True) or {}
	for k, g in ra.items():
		if dem.get(k, 0) > 1:
			g["trung"] = dem[k]
		g["so_noi"] = so_noi.get(g["name"], 0)
		b = tk.get(g.get("bank_account")) or {}
		g["tk"] = b.get("account") or ""
		g["cty"] = b.get("company") or ""
	return ra


def phieu_thu_nhap(cac_si=None, chi_ma_gd=True):
	"""Phiếu thu nháp và kết quả xác minh. CHỈ ĐỌC.

	`cac_si` để trống là mọi phiếu thu nháp mang số tham chiếu; có danh sách
	thì chỉ phiếu phân bổ vào những hoá đơn đó. Trả list dict, mỗi phiếu
	một dict có `hd` là danh sách (hoá đơn, số phân bổ).
	"""
	ten_pe = None
	ref = {}
	if cac_si is not None:
		ten_pe = set()
		for lo in _chia(set(cac_si)):
			for r in frappe.get_all(
				"Payment Entry Reference",
				filters={"reference_doctype": SI, "reference_name": ["in", lo],
					"docstatus": 0, "parenttype": PE},
				fields=["parent", "reference_name", "allocated_amount"], limit_page_length=0,
			):
				ten_pe.add(r.parent)
		if not ten_pe:
			return []
	loc = {"docstatus": 0, "payment_type": "Receive", "party_type": "Customer"}
	if chi_ma_gd:
		loc["reference_no"] = ["is", "set"]
	cac_pe = []
	if ten_pe is None:
		cac_pe = frappe.get_all(PE, filters=loc, fields=[
			"name", "payment_type", "docstatus", "paid_amount", "paid_to", "company",
			"reference_no", "party", "party_name", "posting_date", "vgb_thu_unc"] + TRUONG_TIEN_TE, limit_page_length=0)
	else:
		for lo in _chia(ten_pe):
			l2 = dict(loc)
			l2["name"] = ["in", lo]
			cac_pe += frappe.get_all(PE, filters=l2, fields=[
				"name", "payment_type", "docstatus", "paid_amount", "paid_to", "company",
				"reference_no", "party", "party_name", "posting_date", "vgb_thu_unc"] + TRUONG_TIEN_TE, limit_page_length=0)
	if not cac_pe:
		return []
	ten = [p.name for p in cac_pe]
	for lo in _chia(ten):
		for r in frappe.get_all(
			"Payment Entry Reference",
			filters={"parent": ["in", lo], "parenttype": PE, "reference_doctype": SI},
			fields=["parent", "reference_name", "allocated_amount"], limit_page_length=0,
		):
			ref.setdefault(r.parent, []).append((r.reference_name, flt(r.allocated_amount)))
	# Codex #382 vòng 3: chỉ phiếu thu CÓ phân bổ vào hoá đơn bán mới thuộc
	# màn công nợ. Phiếu thu tạm ứng, thu hộ, thu tay không gắn hoá đơn mà
	# lọt vào đây thì tab Tiền đã về và Excel hiện khoản không phải công nợ,
	# lại cho người chỉ có quyền Bán hàng xem.
	cac_pe = [p for p in cac_pe if ref.get(p.name)]
	if not cac_pe:
		return []
	ten = [p.name for p in cac_pe]
	from vagabond import tep_dinh_kem

	o_unc = {p.name: tep_dinh_kem.doc_ds(p.get("vgb_thu_unc")) for p in cac_pe}
	file_theo_url = {}
	for lo in _chia({u for ds in o_unc.values() for u in ds}):
		for r in frappe.get_all(
			"File", filters={"file_url": ["in", lo]},
			fields=["file_url", "attached_to_doctype", "attached_to_name", "attached_to_field"],
			limit_page_length=0,
		):
			file_theo_url.setdefault(r.file_url, []).append(r)
	# Chỉ đếm tệp nằm trong ô UNC khách gửi (Codex #382), gắn vào phiếu qua
	# chính ô đó (vòng 7) và không có bản ở chỗ khác (vòng 8): url_unc_that,
	# cùng một phép với cổng ghi sổ _so_tep_unc.
	tep = {p.name: dem_tep_unc(o_unc[p.name], url_unc_that(
		p.name, [r for u in o_unc[p.name] for r in file_theo_url.get(u, [])])) for p in cac_pe}
	gd = _gd_theo_so([p.reference_no for p in cac_pe])
	ra = []
	for p in cac_pe:
		g = gd.get((p.reference_no or "").strip())
		ok, ly_do = xac_minh_tien_ve(dict(p), g, (g or {}).get("tk", ""), (g or {}).get("cty", ""))
		ra.append({
			"pe": p.name, "tien": flt(p.paid_amount), "khach": p.party, "ten_khach": p.party_name or p.party,
			"ma_gd": p.reference_no or "", "duoi_gd": duoi_ma(p.reference_no),
			"ngay_ve": str((g or {}).get("date") or p.posting_date or "")[:10],
			"gd": (g or {}).get("name") or "", "hd": ref.get(p.name, []),
			"so_tep": tep.get(p.name, 0), "da_xac_minh": 1 if ok else 0, "ly_do": ly_do,
		})
	# Codex #382 vòng 2: một giao dịch chỉ một phiếu được tính. Đọc MỌI phiếu
	# thu nháp cùng mã giao dịch, kể cả phiếu của hoá đơn ngoài tập đang xem,
	# để phiếu được chọn không đổi theo cách lọc màn.
	ung_vien = {}
	for lo in _chia({p.reference_no.strip() for p in cac_pe if (p.reference_no or "").strip()}):
		for r in frappe.get_all(PE, filters={"docstatus": 0, "payment_type": "Receive",
				"reference_no": ["in", lo]}, fields=["name", "reference_no", "paid_amount"],
				limit_page_length=0):
			ung_vien.setdefault((r.reference_no or "").strip(), []).append((r.name, flt(r.paid_amount)))
	# Ứng viên cũng phải là phiếu có gắn hoá đơn: phiếu không thuộc màn này
	# không được "thắng" rồi hạ phiếu công nợ thật về chưa xác minh.
	ten_uv = {t for cac in ung_vien.values() for t, _ in cac}
	co_hd = set()
	for lo in _chia(ten_uv):
		for r in frappe.get_all("Payment Entry Reference", filters={"parent": ["in", lo],
				"parenttype": PE, "reference_doctype": SI}, fields=["parent"], limit_page_length=0):
			co_hd.add(r.parent)
	ung_vien = {k: [(t, v) for t, v in cac if t in co_hd] for k, cac in ung_vien.items()}
	return mot_phieu_moi_giao_dich(ra, ung_vien)


def _so_tep_unc(ten_pe, o_unc):
	"""Số tệp UNC khách gửi thật sự trên phiếu: có trong ô VÀ còn gắn vào phiếu."""
	from vagabond import tep_dinh_kem

	ds = tep_dinh_kem.doc_ds(o_unc)
	if not ds:
		return 0
	# Đọc MỌI dòng File mang các đường dẫn này, không chỉ dòng của phiếu:
	# bản chép do ô Attach sinh ra phải bị lộ (url_unc_that).
	rows = frappe.get_all("File", filters={"file_url": ["in", ds]}, fields=[
		"file_url", "attached_to_doctype", "attached_to_name", "attached_to_field"], limit_page_length=0)
	return dem_tep_unc(ds, url_unc_that(ten_pe, rows))


@frappe.whitelist(methods=["POST"])
def ghi_so_phieu_thu(name=None, unc=None):
	"""Đính uỷ nhiệm chi khách gửi vào phiếu thu nháp, và kế toán thì ghi sổ luôn.

	Anh Việt chốt 28/09/2026: có uỷ nhiệm chi khách gửi mới ghi sổ. Ai có
	quyền màn Công nợ đính được tệp; chỉ kế toán bấm ghi sổ.

	Ghi sổ là MỘT lượt nguyên khối (Codex #381 F2): khoá phiếu và giao dịch
	ngân hàng, soát lại, ghi sổ phiếu thu, nối giao dịch vào phiếu, tải lại
	xác minh. Hỏng ở bất cứ bước nào thì lùi cả lượt về điểm lưu, phiếu thu
	quay về nháp như chưa bấm.

	ĐIỀU KIỆN CỦA LÕI mà hàm này dựa vào (Codex #382, AGENTS mục đọc lõi).
	Đọc ngày 28/09/2026; site chạy Frappe v16.27.1 (f33ac3f), ERPNext nhánh
	version-16 (đọc tại 12cd563f, v16.35.0). Nâng lõi thì đối chiếu lại:

	1. frappe/model/document.py `Document.submit` -> `_submit`: đặt
	   docstatus = 1 rồi `save()`. `_save` chạy `run_before_save_methods`
	   (before_validate, validate, before_submit, trong đó có hook
	   `chung_tu_tien.chan_thieu_dinh_kem`), rồi `_validate` ->
	   `validate_workflow` -> frappe/model/workflow.py
	   `set_workflow_state_on_action` tự đặt bước duyệt đúng docstatus 1.
	   Vì vậy KHÔNG đặt tay bước duyệt ở đây.
	2. erpnext/accounts/doctype/bank_transaction/bank_transaction.py
	   `BankTransaction.add_payment_entries`: ném lỗi khi
	   `unallocated_amount <= 0`, còn lại chỉ thêm dòng `allocated_amount = 0`.
	3. Cùng tệp, `save()` trên giao dịch đã submit chạy
	   `before_update_after_submit` -> `allocate_payment_entries`: dòng có
	   allocated 0 được cấp `min(allocable, remaining)`, trong đó allocable
	   lấy từ GL của phiếu vào ĐÚNG tài khoản của Bank Account
	   (`get_related_bank_gl_entries`, `get_clearance_details`: phiếu không
	   chạm tài khoản đó thì ném lỗi, allocable = 0 thì XOÁ dòng). Hệ quả:
	   phải submit phiếu TRƯỚC khi nối (có GL mới có allocable), và phải tải
	   lại giao dịch để kiểm dòng còn đó và được cấp đủ số tiền phiếu.
	"""
	from vagabond.ban_hang import _kiem_quyen_doc_luu_don

	_kiem_quyen_doc_luu_don()
	name = (name or "").strip()
	if not name or not frappe.db.exists(PE, name):
		frappe.throw("Không tìm thấy phiếu thu.")
	doc = frappe.get_doc(PE, name, for_update=True)
	if int(doc.docstatus) == 1:
		return {"ok": 1, "da_lam_roi": 1, "name": doc.name}
	if int(doc.docstatus) != 0 or doc.payment_type != "Receive":
		frappe.throw("Phiếu này không phải phiếu thu nháp.")
	# Codex #382 vòng 4: soát loại phiếu TRƯỚC khi gắn tệp. Nút này chỉ dành
	# cho phiếu thu tiền khách chuyển khoản có gắn hoá đơn, đúng tập hook ghi
	# sổ bắt UNC; phiếu khác (hoàn tiền nhà cung cấp, thu lẻ không gắn hoá
	# đơn...) không được nhận tệp qua cửa này.
	if not _thuoc_tap_unc(doc):
		frappe.throw("Phiếu %s không phải phiếu thu tiền khách chuyển khoản có gắn hoá đơn, "
			"không đính uỷ nhiệm chi khách gửi qua màn Công nợ được." % doc.name)

	if unc:
		from vagabond import tep_dinh_kem

		da = tep_dinh_kem.doc_ds(doc.get("vgb_thu_unc"))
		# Codex #382 vòng 7: gan_vao coi tệp đã gắn vào phiếu này là xong,
		# không xét ô. Chỉ nhận tệp mới tải lên hoặc tệp đã gắn qua ô UNC.
		moi = tep_dinh_kem.doc_ds(unc)
		cua_phieu = frappe.get_all("File", filters={"attached_to_doctype": PE, "attached_to_name": doc.name,
			"file_url": ["in", moi]}, fields=["file_url", "attached_to_field"], limit_page_length=0) if moi else []
		khac = tep_muc_khac(moi, cua_phieu)
		if khac:
			frappe.throw("Tệp đã chọn đang đính ở mục khác của phiếu thu %s, không dùng làm uỷ nhiệm chi "
				"khách gửi được. Tải ảnh hoặc PDF chuyển khoản khách gửi lên lại." % doc.name)
		them = tep_dinh_kem.gan_vao(PE, doc.name, "vgb_thu_unc", unc)
		if them:
			frappe.db.set_value(PE, doc.name, "vgb_thu_unc", tep_dinh_kem.ghi_ds(da + them),
				update_modified=False)
			doc.reload()
	so_tep = _so_tep_unc(doc.name, doc.get("vgb_thu_unc"))

	g = _gd_theo_so([doc.reference_no]).get((doc.reference_no or "").strip())
	ok, ly_do = xac_minh_tien_ve(doc.as_dict(), g, (g or {}).get("tk", ""), (g or {}).get("cty", ""))
	duoc, vi_sao = soat_ghi_so_thu(ok, ly_do, so_tep, la_ke_toan())
	if not duoc:
		# Đính tệp xong mà chưa đủ điều kiện ghi sổ thì vẫn là một việc đã
		# làm được, không phải lỗi: trả lại câu cho màn hình hiện.
		if unc and so_tep:
			return {"ok": 0, "da_dinh": 1, "so_tep": so_tep, "vi_sao": vi_sao, "name": doc.name}
		frappe.throw(vi_sao, title="Chưa ghi sổ phiếu thu được")

	frappe.db.savepoint("vgb_ghi_so_thu")
	try:
		gdoc = frappe.get_doc(BT, g["name"], for_update=True)
		# Soát lại trên bản đã khoá: giữa lúc đọc và lúc khoá có thể có
		# người khác vừa nối giao dịch này vào chứng từ khác.
		if gdoc.payment_entries or flt(gdoc.allocated_amount) > LECH:
			frappe.throw("Giao dịch %s vừa được nối với chứng từ khác. Tải lại màn để kiểm." % doc.reference_no)
		# Codex #382 vòng 5: so theo tiền tài khoản nhận, không theo tiền
		# phía khách. Xem tien_phia_ngan_hang.
		tien_nh, sai_tien = tien_phia_ngan_hang(doc.as_dict())
		if sai_tien:
			frappe.throw(sai_tien)
		if flt(gdoc.unallocated_amount) + LECH < tien_nh:
			frappe.throw("Giao dịch %s không còn đủ tiền chưa phân bổ." % doc.reference_no)
		doc.flags.ignore_permissions = True
		doc.submit()
		doc.reload()
		if int(doc.docstatus) != 1:
			frappe.throw("Phiếu thu chưa vào sổ. Đã lùi cả lượt.")
		# Submit có thể tính lại tiền hai phía: đọc lại trên bản đã vào sổ.
		tien_nh, sai_tien = tien_phia_ngan_hang(doc.as_dict())
		if sai_tien:
			frappe.throw(sai_tien + " Đã lùi cả lượt.")
		gdoc.add_payment_entries([{"payment_doctype": PE, "payment_name": doc.name}])
		gdoc.save(ignore_permissions=True)
		gdoc.reload()
		dong = [r for r in (gdoc.payment_entries or []) if r.payment_entry == doc.name]
		if not dong:
			frappe.throw("Giao dịch ngân hàng chưa nối được vào phiếu thu. Đã lùi cả lượt.")
		# allocate_payment_entries cấp min(allocable, remaining): cấp thiếu
		# là giao dịch và phiếu lệch nhau, không nhận (điều 3 ở đầu hàm).
		if flt(dong[0].allocated_amount) + LECH < tien_nh:
			frappe.throw("Giao dịch ngân hàng chỉ nhận %s đ cho phiếu thu %s đ. Đã lùi cả lượt."
				% ("{:,.0f}".format(flt(dong[0].allocated_amount)).replace(",", "."),
					"{:,.0f}".format(tien_nh).replace(",", ".")))
	except Exception as e:
		frappe.db.rollback(save_point="vgb_ghi_so_thu")
		frappe.clear_messages()
		# Tệp vừa đính nằm TRƯỚC điểm lưu nên vẫn còn. Trả câu lỗi cho màn
		# thay vì ném, để request không lùi luôn tệp người dùng vừa tải.
		if unc and so_tep:
			return {"ok": 0, "da_dinh": 1, "so_tep": so_tep, "name": doc.name,
				"vi_sao": str(e) or "Chưa ghi sổ được, tệp đã lưu."}
		raise
	_ghi_vet_thu(doc.name, "Ghi sổ phiếu thu kèm %d tệp uỷ nhiệm chi khách gửi, nối giao dịch %s"
		% (so_tep, doc.reference_no))
	return {"ok": 1, "name": doc.name, "gd": gdoc.name}


@frappe.whitelist()
def chan_doan_ghi_so(name=None):
	"""CHỈ ĐỌC: chạy thử bước kiểm trước ghi sổ của một phiếu thu nháp, rồi lùi.

	Codex #381 F1: lý do 1.428 phiếu thu kẹt nháp mới là giả thuyết, vì
	script tự lập phiếu nuốt lỗi. Hàm này chạy đúng các bước kiểm mà Frappe
	chạy trước khi ghi sổ, theo thứ tự của frappe/model/document.py `_save`
	(v16.27.1): `_validate_links`, `run_before_save_methods` (before_validate,
	validate, before_submit), `_validate` (bắt buộc nhập, workflow). KHÔNG
	chạy on_submit nên không sinh bút toán, rồi lùi về điểm lưu. Trả nguyên
	văn câu lỗi đầu tiên.
	"""
	if not la_ke_toan():
		frappe.throw("Chỉ kế toán xem được chẩn đoán này.")
	name = (name or "").strip()
	if not frappe.db.exists(PE, name):
		frappe.throw("Không tìm thấy phiếu.")
	frappe.db.savepoint("vgb_chan_doan_thu")
	loi = ""
	try:
		doc = frappe.get_doc(PE, name)
		if int(doc.docstatus) != 0:
			return {"name": name, "loi": "", "ghi_chu": "Phiếu không còn là nháp."}
		doc.docstatus = 1
		doc._action = "submit"
		doc.flags.ignore_permissions = True
		doc.load_doc_before_save()
		doc._validate_links()
		doc.run_before_save_methods()
		doc._validate()
	except Exception as e:
		loi = str(e) or e.__class__.__name__
	finally:
		frappe.db.rollback(save_point="vgb_chan_doan_thu")
		frappe.clear_messages()
	return {"name": name, "loi": loi, "qua": 0 if loi else 1}


def gop_unc_desk(doc, method=None):
	"""Hook before_validate: tệp đính ở ô Desk gộp vào ô danh sách UNC khách gửi.

	Giữ MỘT nguồn: app và Desk cùng ghi vào `vgb_thu_unc`, mọi phép đếm chỉ
	đọc ô đó (dem_tep_unc).
	"""
	if doc.doctype != PE:
		return
	# Codex #382 vòng 10: xoá hay thay tệp ở ô Desk thì đường dẫn cũ phải ra
	# khỏi ô danh sách. Frappe giữ nguyên dòng File khi ô Attach bị xoá (xem
	# de_nghi_chi.py), nên nếu chỉ gộp thêm thì tệp đã gỡ vẫn được đếm và
	# phiếu ghi sổ được mà không có UNC đang chọn.
	lay_truoc = getattr(doc, "get_doc_before_save", None)
	truoc = lay_truoc() if callable(lay_truoc) else None
	cu = (truoc.get("vgb_thu_unc_tep") if truoc else "") or ""
	moi = doc.get("vgb_thu_unc_tep") or ""
	if not cu and not moi:
		return
	from vagabond import tep_dinh_kem

	ds = doi_unc_desk(tep_dinh_kem.doc_ds(doc.get("vgb_thu_unc")), cu, moi)
	doc.vgb_thu_unc = tep_dinh_kem.ghi_ds(ds)


def _thuoc_tap_unc(doc):
	"""Phiếu này thuộc tập bắt buộc UNC khách gửi không. MỘT chỗ cho cả hook
	ghi sổ và nút đính UNC trên app (Codex #382 vòng 4)."""
	co_hd = any((r.get("reference_doctype") == SI) for r in (doc.get("references") or []))
	ref = (doc.get("reference_no") or "").strip()
	khop = bool(ref) and bool(frappe.db.exists(BT, {"reference_number": ref, "docstatus": 1}))
	return can_unc_khach(doc.as_dict(), co_hd, khop)


def chan_thieu_unc_khach(doc, method=None):
	"""Hook before_submit: phiếu thu tiền khách chuyển khoản phải có UNC khách gửi.

	Anh Việt 29/09/2026 (Codex #382 vòng 3): ghi sổ trên Desk hay bất cứ
	đường nào gọi submit() cũng phải qua cùng luật với nút ghi sổ trên app.
	Hook `chung_tu_tien.chan_thieu_dinh_kem` (tệp bất kỳ) vẫn chạy như cũ cho
	mọi chứng từ ngân hàng; hook này chặt hơn và chỉ cho tập can_unc_khach.
	"""
	try:
		if doc.doctype != PE:
			return
		if not _thuoc_tap_unc(doc):
			return
		ref = (doc.get("reference_no") or "").strip()
		if _so_tep_unc(doc.name, doc.get("vgb_thu_unc")) > 0:
			return
		frappe.throw(
			"Phiếu thu %s là tiền khách chuyển khoản (giao dịch %s) nên phải có uỷ nhiệm chi "
			"khách gửi mới ghi sổ được. Trên Desk: đính ảnh hoặc PDF chuyển khoản khách gửi vào ô "
			"\"Đính uỷ nhiệm chi khách gửi\", lưu, rồi ghi sổ lại. Trên app: màn Công nợ, tab "
			"Tiền đã về, nút Đính UNC khách gửi." % (doc.name, ref),
			title="Thiếu uỷ nhiệm chi khách gửi",
		)
	except frappe.ValidationError:
		raise
	except Exception:
		# Codex #382 vòng 4: cổng chứng từ bắt buộc thì hỏng là CHẶN, không
		# cho qua. Ghi lỗi để biết vì sao, rồi ném lại: kế toán thấy lỗi và
		# báo, còn hơn phiếu vào sổ mà không ai soát UNC.
		frappe.log_error(frappe.get_traceback(), "thu_tien: kiem UNC khach gui loi")
		raise


def _ghi_vet_thu(name, viec):
	try:
		frappe.get_doc({
			"doctype": "Comment", "comment_type": "Info",
			"reference_doctype": PE, "reference_name": name,
			"content": "%s - %s" % (viec, frappe.session.user),
		}).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thu_tien: ghi vet phieu thu")


# ==================================================================
# v541: tab Đang nợ, nút "Khách đã chuyển" (anh Việt 29/09/2026)
# ==================================================================
#
# Ca thật: hoá đơn Pancake 745.000 đ trả Công nợ, tiền đã về tài khoản
# công ty nhưng nội dung chuyển khoản không mang mã đơn, nên script khớp
# SePay không lập phiếu thu nháp và hoá đơn nằm mãi ở tab Đang nợ. Tab Tiền
# đã về chỉ nhận hoá đơn ĐÃ có phiếu thu khớp giao dịch, nên không có cửa
# nào để người biết tiền đã về chọn đúng giao dịch. Cửa này: người chọn
# giao dịch ngân hàng (máy chỉ gợi ý, KHÔNG tự gán theo số tiền, cùng luật
# với hồ sơ thanh toán v528), máy lập phiếu thu NHÁP nối đúng giao dịch,
# hoá đơn sang tab Tiền đã về, rồi đính UNC khách gửi và ghi sổ như cũ.

SO_NGAY_TRUOC_HD = 7     # giao dịch về sớm hơn ngày hoá đơn tối đa bấy nhiêu ngày
GOI_Y_TOI_DA = 12


def dau_hieu_don(remarks, ten_si=""):
	"""Mã đơn và số điện thoại đọc được trên hoá đơn để đối với nội dung
	chuyển khoản. THUẦN. remarks kiểu "Pancake #93367 - Ms.Thanh - 0933346399"."""
	import re
	s = str(remarks or "")
	ma = re.findall(r"#\s*(\d{4,})", s)
	dt = [d[-9:] for d in re.findall(r"\d{9,11}", s)]
	return {"ma_don": ma, "dien_thoai": [d for d in dt if d not in ma], "ten_si": str(ten_si or "")}


def xep_ung_vien(ds_gd, dau_hieu, con_no):
	"""Xếp giao dịch ứng viên, gắn lý do khớp. THUẦN.

	Chỉ GỢI Ý: đúng số tiền, nội dung có mã đơn, có số điện thoại khách.
	Không bỏ giao dịch nào vì không khớp nội dung: người mới là người chọn."""
	dh = dau_hieu or {}
	ra = []
	for g in ds_gd or []:
		mo = str(g.get("description") or "")
		chu = "".join(mo.split()).upper()
		ly = []
		diem = 0
		for m in dh.get("ma_don") or []:
			if m and m in chu:
				ly.append("nội dung có mã đơn %s" % m)
				diem += 4
				break
		for d in dh.get("dien_thoai") or []:
			if d and d in chu:
				ly.append("có số điện thoại khách")
				diem += 2
				break
		ten = str(dh.get("ten_si") or "").upper()
		if ten and ten.replace("-", "") in chu.replace("-", ""):
			ly.append("có số hoá đơn")
			diem += 3
		con = _so(g.get("unallocated_amount"))
		if abs(con - _so(con_no)) <= LECH:
			ly.append("đúng số tiền")
			diem += 1
		ra.append(dict(g, khop=ly, diem=diem))
	ra.sort(key=lambda x: (-x["diem"], str(x.get("date") or "")))
	return ra


def _ma_gd_dang_dung():
	"""Số giao dịch đã có phiếu thu (nháp hoặc đã ghi sổ) mang theo."""
	return set(frappe.get_all(PE, filters={"docstatus": ["<", 2], "reference_no": ["is", "set"],
		"payment_type": "Receive"}, pluck="reference_no", limit_page_length=0))


@frappe.whitelist()
def ung_vien_tien_ve(si=None):
	"""Giao dịch ngân hàng có thể là tiền khách trả cho hoá đơn này."""
	from vagabond.ban_hang import _kiem_quyen_doc_luu_don
	from frappe.utils import add_days

	_kiem_quyen_doc_luu_don()
	d = frappe.db.get_value(SI, si, ["name", "docstatus", "outstanding_amount", "posting_date",
		"company", "remarks", "customer_name"], as_dict=True) if si else None
	if not d or int(d.docstatus) != 1:
		frappe.throw("Không tìm thấy hoá đơn đã ghi sổ.")
	con_no = flt(d.outstanding_amount)
	if con_no <= LECH:
		frappe.throw("Hoá đơn %s không còn nợ." % d.name)
	tk_cty = frappe.get_all("Bank Account", filters={"is_company_account": 1, "company": d.company},
		pluck="name", limit_page_length=0)
	dh = dau_hieu_don(d.remarks, d.name)
	loc = {"docstatus": 1, "deposit": [">", 0], "unallocated_amount": [">", LECH],
		"bank_account": ["in", tk_cty or [""]], "date": [">=", add_days(d.posting_date, -SO_NGAY_TRUOC_HD)]}
	truong = ["name", "date", "deposit", "unallocated_amount", "description", "reference_number", "bank_account"]
	gd = frappe.get_all(BT, filters=dict(loc, unallocated_amount=["between", [con_no - LECH, con_no + LECH]]),
		fields=truong, order_by="date asc", limit_page_length=200)
	# Khách chuyển gộp nhiều đơn: số tiền lớn hơn nhưng nội dung có mã đơn.
	for m in dh["ma_don"]:
		gd += frappe.get_all(BT, filters=dict(loc, description=["like", "%" + m + "%"]),
			fields=truong, limit_page_length=20)
	dung = _ma_gd_dang_dung()
	thay, sach = set(), []
	for g in gd:
		if g.name in thay or (g.reference_number or "") in dung:
			continue
		thay.add(g.name)
		sach.append(g)
	xep = xep_ung_vien(sach, dh, con_no)[:GOI_Y_TOI_DA]
	return {"si": d.name, "khach": d.customer_name, "con_no": con_no, "ngay_hd": str(d.posting_date),
		"gd": [{"name": g["name"], "ngay": str(g["date"]), "tien": flt(g["deposit"]),
			"con": flt(g["unallocated_amount"]), "mo_ta": str(g.get("description") or "")[:160],
			"ma_gd": g.get("reference_number") or "", "khop": g["khop"]} for g in xep]}


@frappe.whitelist(methods=["POST"])
def nhan_tien_ve(si=None, gd=None):
	"""Người chọn giao dịch ngân hàng cho hoá đơn: lập phiếu thu NHÁP nối đúng
	giao dịch đó. Không ghi sổ (ghi sổ vẫn cần UNC khách gửi, v534)."""
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
	from vagabond.ban_hang import _kiem_quyen_doc_luu_don

	_kiem_quyen_doc_luu_don()
	if not si or not gd or not frappe.db.exists(SI, si) or not frappe.db.exists(BT, gd):
		frappe.throw("Thiếu hoá đơn hoặc giao dịch ngân hàng.")
	g = frappe.get_doc(BT, gd, for_update=True)
	doc = frappe.get_doc(SI, si, for_update=True)
	if int(doc.docstatus) != 1 or flt(doc.outstanding_amount) <= LECH:
		frappe.throw("Hoá đơn %s không còn nợ." % si)
	if int(g.docstatus) != 1 or flt(g.deposit) <= 0 or (g.currency or "VND") != "VND":
		frappe.throw("Giao dịch %s không phải tiền vào đã xác nhận." % gd)
	ref = (g.reference_number or "").strip()
	if not ref:
		frappe.throw("Giao dịch %s không có số tham chiếu ngân hàng." % gd)
	if g.payment_entries or flt(g.unallocated_amount) <= LECH:
		frappe.throw("Giao dịch %s đã nối với chứng từ khác." % ref)
	cu = frappe.get_all(PE, filters={"docstatus": ["<", 2], "reference_no": ref, "payment_type": "Receive"},
		pluck="name", limit_page_length=1)
	if cu:
		frappe.throw("Giao dịch %s đã có phiếu thu %s. Mở tab Tiền đã về." % (ref, cu[0]))
	nhap = frappe.get_all("Payment Entry Reference", filters={"reference_doctype": SI, "reference_name": si,
		"docstatus": 0, "parenttype": PE}, pluck="parent", limit_page_length=1)
	if nhap:
		frappe.throw("Hoá đơn %s đã có phiếu thu nháp %s. Mở tab Tiền đã về." % (si, nhap[0]))
	b = frappe.db.get_value("Bank Account", g.bank_account, ["account", "company", "is_company_account"], as_dict=True) or {}
	if not b.get("account") or not b.get("is_company_account") or b.get("company") != doc.company:
		frappe.throw("Giao dịch %s không về tài khoản ngân hàng của công ty." % ref)
	tien = min(flt(doc.outstanding_amount), flt(g.unallocated_amount))
	pe = get_payment_entry(SI, si, party_amount=tien, bank_account=b["account"])
	pe.reference_no = ref
	pe.reference_date = g.date
	pe.remarks = "Khách chuyển khoản, giao dịch %s, người chọn trên màn Công nợ." % ref
	pe.flags.ignore_permissions = True
	pe.insert(ignore_permissions=True)
	_ghi_vet_thu(pe.name, "Lập phiếu thu nháp cho hoá đơn %s theo giao dịch %s do người chọn" % (si, ref))
	return {"pe": pe.name, "tien": flt(pe.paid_amount), "ma_gd": ref, "ngay_ve": str(g.date),
		"ten_khach": doc.customer_name, "con_no_sau": flt(doc.outstanding_amount) - tien}
