# -*- coding: utf-8 -*-
"""Tự chọn lô cho nguyên liệu bị trừ khi ghi phiếu kho.

Vì sao có tệp này
-----------------
Tối 20/08/2026 Khải bấm làm một cái Plain Croissant thì máy ném ra:

    Serial No / Batch No are mandatory for Item NVLT00166

NVLT00166 là men tươi Saf. Hệ đang theo lô cho 829 mã, trong đó 349 nguyên
vật liệu thô, nên theo lô là chủ trương chứ không phải ai đó bật nhầm.

Chỗ hụt nằm ở app: khi ghi phiếu sản xuất, app chỉ gắn lô cho THÀNH PHẨM
làm ra, còn các NGUYÊN LIỆU bị trừ thì để trống. ERPNext không đoán hộ khi
`Stock Settings.use_serial_batch_fields` đang bật, nên nó chặn.

Bắt bếp gõ số lô trên điện thoại là không tưởng. Việc chọn lô nào là việc
của máy, và máy có đủ dữ liệu để chọn đúng: lấy lô hết hạn gần nhất trước
(FEFO), vì đó cũng chính là cách kho thật đang làm.

Đặt ở đâu
---------
Ở hook `before_validate` của Stock Entry, KHÔNG ở màn hình. Ba luồng khác
nhau của app cùng sinh ra phiếu sản xuất (hoàn tất lệnh, làm luôn bán thành
phẩm, khai nguyên liệu tay), chưa kể Desk. Vá ở màn hình là vá ba lần và
lần thứ tư sẽ quên. Vá ở đây là vá một lần cho tất cả (QT-19: máy chủ chốt
số, màn hình chỉ hiển thị).

Ba việc thêm ngày 06/09/2026 (#206, Codex duyệt hướng trên #215)
----------------------------------------------------------------
1. MÃ THAY THẾ chỉ dùng cho luồng SẢN XUẤT. Trước đây hàm này áp cho mọi
   phiếu kho, mà từ 06/09 màn "Nhận hàng" điều chuyển nội bộ cũng đi qua
   đây. Nhận nguyên liệu theo phiếu yêu cầu thì kho giao mã nào phải ghi
   sổ mã đó: tự đổi sang mã B là người nhận cầm một thứ, sổ ghi một thứ
   khác, và không ai biết cho tới lúc kiểm kê. Xem `duoc_thay_ma`.

2. MỘT TÚI LÔ CHO CẢ PHIẾU, không phải mỗi dòng một túi. Một phiếu có thể
   có hai dòng cùng mã cùng kho (hai dòng của hai phiếu yêu cầu khác
   nhau). Tính tồn riêng cho từng dòng thì cả hai cùng nhìn thấy một phần
   tồn, cùng lấy, và phiếu ghi ra nhiều hơn số kho thật có. Xem `_tui_lo`
   và `rut_tu_kho`.

3. ĐƯỜNG DỰ PHÒNG phải loại lô đang TẮT và lô quá hạn. Đường đó cộng
   thẳng sổ kho, không qua bộ lọc của ERPNext, nên nó thấy cả hai loại.
   Lấy phải lô TẮT thì `validate_batch` chặn cứng ngay sau đó và bếp đứng
   im với một câu lỗi nói về cái lô không ai chọn; lấy phải lô quá hạn thì
   nó chen lên trước cả lô còn hạn, phá vỡ đúng thứ tự FEFO mà tệp này
   dựng ra. Xem `_bo_lo_khong_dung`.

Khi thiếu hàng thì nói kho nào còn bao nhiêu
--------------------------------------------
Đúng hôm đó còn một chuyện nữa: men tươi có 13.000 gram ở kho Baker, nhưng
lệnh croissant lấy nguyên liệu ở kho Pastry, nơi men bằng 0. Câu lỗi gốc
của ERPNext không nói điều đó. Câu của mình phải nói, vì việc phải làm tiếp
là chuyển kho chứ không phải bấm lại (QT-24).
"""

import re

# ------------------------------------------------------------ phần thuần

# Sai số cho phép khi so số lượng. Số lượng kho ERPNext giữ 6 chữ số thập
# phân, so bằng dấu bằng thì 77.99999999 sẽ thành thiếu hàng.
LI_TI = 0.000001


def chia_theo_lo(can, cac_lo):
	"""Cần `can` đơn vị, các lô xếp sẵn theo thứ tự ưu tiên. THUẦN.

	`cac_lo`: [(tên lô, tồn của lô)] đã xếp hết hạn gần nhất lên trước.
	Trả về ([(tên lô, số lấy)], phần còn thiếu).

	Lấy cạn từng lô rồi mới sang lô sau, chứ không chia đều: chia đều thì
	một mẻ bánh đụng vào bốn lô men, và sổ lô trở nên vô nghĩa.
	"""
	con = float(can or 0)
	ra = []
	for ten, ton in cac_lo or []:
		if con <= LI_TI:
			break
		ton = float(ton or 0)
		if ton <= LI_TI:
			continue
		lay = round(min(con, ton), 6)
		if lay <= LI_TI:
			continue
		ra.append((ten, lay))
		con = round(con - lay, 6)
	return ra, (0.0 if con <= LI_TI else round(con, 6))


# Luong nao duoc phep tu doi sang MA THAY THE khi thieu hang.
#
# CHI luong san xuat. Nhan nguyen lieu theo phieu yeu cau thi KHONG: kho
# giao ma A, may khong duoc tu ghi so thanh ma B roi coi la xong. Nguoi
# nhan cam tren tay mot thu, so sach ghi mot thu khac, va khong ai bao
# gio biet cho toi luc kiem ke. Codex chot 06/09/2026 tren #215.
#
# Chinh sach nam o MOT cho, khong sao chep them mot bo chon lo thu hai.
LUONG_DUOC_THAY_MA = (
	"Manufacture",
	"Repack",
	"Material Transfer for Manufacture",
	"Send to Subcontractor",
)


def duoc_thay_ma(purpose):
	"""Phiếu loại này có được tự lấy mã thay thế khi thiếu không. THUẦN."""
	return (purpose or "").strip() in LUONG_DUOC_THAY_MA


def rut_tu_kho(muc, can):
	"""Rút `can` đơn vị ra khỏi một túi lô, TRỪ LUÔN phần đã rút. THUẦN.

	`muc` là {"con": [(tên lô, còn lại)] đã xếp theo thứ tự ưu tiên}.

	Vì sao phải trừ: một phiếu có thể có HAI dòng cùng một mã cùng một kho
	(hai dòng của hai phiếu yêu cầu khác nhau). Tính tồn riêng cho từng
	dòng thì cả hai dòng cùng nhìn thấy một phần tồn, cùng lấy, và phiếu
	ghi ra nhiều hơn số kho thật có. Nên cả phiếu chung MỘT túi.
	"""
	phan, thieu = chia_theo_lo(can, muc.get("con") or [])
	if phan:
		da_lay = {}
		for ten, so in phan:
			da_lay[ten] = da_lay.get(ten, 0) + float(so or 0)
		con = []
		for ten, so in muc.get("con") or []:
			lai = round(float(so or 0) - da_lay.get(ten, 0), 6)
			if lai > LI_TI:
				con.append((ten, lai))
		muc["con"] = con
	return phan, thieu


def cau_thieu_lo(ten_hang, ma, kho, thieu, don_vi, kho_khac, thay_khac=None):
	"""Câu báo thiếu hàng theo lô. Phải nói việc làm tiếp, không chỉ nói không.

	`kho_khac`: [(tên kho, tồn)] các kho khác đang còn mã này.
	"""
	cau = 'Kho "%s" không đủ %s để trừ: còn thiếu %s %s.' % (
		_ten_kho(kho), ten_hang or ma, _so(thieu), don_vi or "",
	)
	con = [(k, t) for k, t in (kho_khac or []) if float(t or 0) > LI_TI]
	if con:
		cau += " Mã này đang còn ở %s." % ", ".join(
			"%s %s tại %s" % (_so(t), don_vi or "", _ten_kho(k)) for k, t in con[:4]
		)
		cau += " Anh chị chuyển kho phần thiếu rồi bấm lại."
	elif not thay_khac:
		cau += " Chưa tìm thấy tồn mã này ở kho khác; kiểm tra tồn, nhập hàng hoặc kiểm kê lại."
	if thay_khac:
		cau += " Mã thay thế đã khai đang còn: " + ", ".join(
			"%s: %s %s tại %s" % (m, _so(t), don_vi or "", _ten_kho(k))
			for m, k, t in thay_khac[:4]) + "."
		cau += " Kiểm tra kho nguồn đã chọn hoặc chuyển nguyên liệu về đúng kho rồi bấm lại. Tồn này chưa xác nhận lô dùng được."
	return cau


def _ten_kho(kho):
	"""Bỏ đuôi công ty cho gọn: "Baker - Nguyên liệu - TV" thành "Baker - Nguyên liệu"."""
	t = (kho or "").strip()
	return re.sub(r"\s*-\s*[A-Z]{1,4}$", "", t) or t


def _so(x):
	x = float(x or 0)
	if abs(x - round(x)) < 0.0005:
		return "{:,.0f}".format(round(x)).replace(",", ".")
	return "{:,.3f}".format(x).replace(",", "~").replace(".", ",").replace("~", ".")


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, flt

from vagabond import lo_het_han

# Các khoá của khung, phải bỏ đi khi nhân một dòng ra làm hai, nếu không
# bản sao mang tên của bản gốc và Frappe ghi đè lên nhau.
KHOA_BO = (
	"name", "idx", "parent", "parentfield", "parenttype", "doctype",
	"creation", "modified", "owner", "modified_by", "docstatus",
	# Để ERPNext tính lại, không bê số cũ sang dòng mới (QT-19).
	"transfer_qty", "basic_rate", "basic_amount", "amount", "valuation_rate",
	"serial_and_batch_bundle", "serial_no",
)


def _theo_lo(ma):
	try:
		return cint(frappe.get_cached_value("Item", ma, "has_batch_no"))
	except Exception:
		return 0


def _ton_tung_lo(ma, kho, ke_ca_qua_han=False):
	"""Tồn từng lô của một mã tại một kho. Trả về {tên lô: tồn}.

	`ke_ca_qua_han` bật thì gọi ERPNext kèm cờ `for_stock_levels`, là cách
	duy nhất để nó chịu trả về lô đã quá hạn (get_auto_batch_nos lọc
	`expiry_date >= today` nếu không có cờ). Cờ đó cũng bỏ luôn phần trừ
	hàng đang giữ cho hoá đơn POS nháp, nên CHỈ dùng cho vòng vét cuối,
	sau khi vòng thường đã tính đủ phần hàng còn hạn.
	"""
	ra = {}
	try:
		from erpnext.stock.doctype.batch.batch import get_batch_qty

		ds = get_batch_qty(
			item_code=ma, warehouse=kho, for_stock_levels=bool(ke_ca_qua_han)
		) or []
		if isinstance(ds, (list, tuple)):
			for d in ds:
				ten = (d or {}).get("batch_no") if hasattr(d, "get") else None
				if not ten:
					continue
				ra[ten] = flt(ra.get(ten, 0)) + flt((d or {}).get("qty"))
	except Exception:
		ra = {}
	if ra:
		return {k: v for k, v in ra.items() if flt(v) > LI_TI}
	# Đường dự phòng khi ERPNext đổi cách gọi: cộng thẳng sổ kho.
	#
	# 03/09/2026: đường này TỪNG VÔ DỤNG. Nó cộng theo cột `batch_no` của
	# sổ kho, mà ERPNext v16 để trống cột đó và cất số lô trong gói Serial
	# and Batch Bundle. Đo thật: NVLT00037 còn 3.000 gram ở Kho tổng 307,
	# sổ kho đúng một dòng, batch_no của nó NULL. Nay cộng cả hai đường.
	# Số trong gói đã mang dấu sẵn (nhập dương, xuất âm) nên cộng thẳng.
	try:
		dong = frappe.get_all(
			"Stock Ledger Entry",
			filters={"item_code": ma, "warehouse": kho, "is_cancelled": 0},
			fields=["batch_no", "actual_qty", "serial_and_batch_bundle"],
			limit_page_length=0,
		)
		goi = []
		for d in dong:
			if d.get("batch_no"):
				ten = d["batch_no"]
				ra[ten] = flt(ra.get(ten, 0)) + flt(d.get("actual_qty"))
			elif d.get("serial_and_batch_bundle"):
				goi.append(d["serial_and_batch_bundle"])
		if goi:
			for e in frappe.get_all(
				"Serial and Batch Entry",
				filters={"parenttype": "Serial and Batch Bundle",
					"parent": ["in", goi]},
				fields=["batch_no", "qty"],
				limit_page_length=0,
			):
				if e.get("batch_no"):
					ra[e["batch_no"]] = flt(ra.get(e["batch_no"], 0)) + flt(e.get("qty"))
	except Exception:
		pass
	# Duong du phong cong THANG so kho, khong qua bo loc cua ERPNext, nen
	# no thay ca lo da TAT lan lo qua han. Lay bua o day la hai chuyen:
	# lo TAT thi `validate_batch` chan cung ngay sau do (bep dung im, cau
	# loi lai noi ve mot lo khong ai chon), con lo qua han thi len truoc ca
	# lo con han, pha vo dung thu tu FEFO. Loc lai o day.
	ra = _bo_lo_khong_dung(ra, ke_ca_qua_han)
	return {k: v for k, v in ra.items() if flt(v) > LI_TI}


def _bo_lo_khong_dung(cac_lo, ke_ca_qua_han):
	"""Bỏ lô đang TẮT, và bỏ luôn lô quá hạn ở vòng thường.

	Lô không tra được hồ sơ thì cũng bỏ: thà báo thiếu còn hơn ghi sổ một
	lô mà máy không biết nó còn hạn hay đã bị ai khoá.
	"""
	if not cac_lo:
		return {}
	ho = {}
	try:
		for b in frappe.get_all(
			"Batch",
			filters={"name": ["in", list(cac_lo)]},
			fields=["name", "disabled", "expiry_date"],
			limit_page_length=0,
		):
			ho[b["name"]] = b
	except Exception:
		return {}
	hn = lo_het_han.hom_nay()
	ra = {}
	for ten, so in cac_lo.items():
		b = ho.get(ten)
		if not b or cint(b.get("disabled")):
			continue
		if not ke_ca_qua_han and lo_het_han.qua_han(b.get("expiry_date"), hn):
			continue
		ra[ten] = so
	return ra


def _ton_lo_qua_han(ma, kho, da_tinh=None):
	"""Tồn của riêng các lô ĐÃ QUÁ HẠN, trừ các lô vòng thường đã tính."""
	tat = _ton_tung_lo(ma, kho, ke_ca_qua_han=True)
	if not tat:
		return {}
	return lo_het_han.chi_lo_qua_han(
		tat, lo_het_han.han_cua(list(tat)), lo_het_han.hom_nay(),
		bo_qua=set(da_tinh or {}),
	)


def _xep_het_han_truoc(cac_lo):
	"""Xếp lô hết hạn gần nhất lên trước. Lô không ghi hạn xếp sau cùng."""
	if not cac_lo:
		return []
	ten = list(cac_lo.keys())
	han = {}
	try:
		for b in frappe.get_all(
			"Batch",
			filters={"name": ["in", ten]},
			fields=["name", "expiry_date", "creation"],
			limit_page_length=0,
		):
			han[b["name"]] = (b.get("expiry_date"), b.get("creation"))
	except Exception:
		han = {}

	def khoa(t):
		h, tao = han.get(t, (None, None))
		# Có hạn thì xếp nhóm 0 theo ngày hết hạn; không hạn thì nhóm 1
		# theo ngày tạo, cũ trước.
		return (0, str(h), str(tao or "")) if h else (1, "", str(tao or ""))

	return [(t, cac_lo[t]) for t in sorted(ten, key=khoa)]


def _kho_khac_con(ma, kho):
	"""Các kho khác đang còn mã này, để câu báo lỗi chỉ được đường đi tiếp."""
	try:
		ds = frappe.get_all(
			"Bin",
			filters={"item_code": ma, "actual_qty": [">", 0]},
			fields=["warehouse", "actual_qty"],
			limit_page_length=0,
		)
		return [(d["warehouse"], d["actual_qty"]) for d in ds if d["warehouse"] != kho]
	except Exception:
		return []


def _cac_ma_thay_the(ma):
	"""Các mã thay thế đã duyệt cho một mã, cùng đơn vị gốc.

	Đọc bảng Item Alternative theo CẢ HAI chiều (bản ghi khai a-b với cờ
	hai chiều thì b cũng thay được cho a). Chỉ nhận mã cùng stock_uom:
	gram thay gram, không để cái thay gram rồi số lượng thành vô nghĩa.
	"""
	try:
		dvt = frappe.get_cached_value("Item", ma, "stock_uom")
		ra = []
		for x in frappe.get_all("Item Alternative",
				filters={"item_code": ma}, pluck="alternative_item_code",
				limit_page_length=0):
			ra.append(x)
		for x in frappe.get_all("Item Alternative",
				filters={"alternative_item_code": ma, "two_way": 1},
				pluck="item_code", limit_page_length=0):
			ra.append(x)
		loc = []
		for m in ra:
			if m == ma or m in loc:
				continue
			it = frappe.get_cached_value(
				"Item", m, ["stock_uom", "disabled", "is_stock_item"],
				as_dict=True) or {}
			if it.get("disabled") or not it.get("is_stock_item"):
				continue
			if it.get("stock_uom") != dvt:
				continue
			loc.append(m)
		return loc
	except Exception:
		return []


def phan_da_chon_tay(cac_dong, lo_trong_goi=None):
	"""Số các dòng NGƯỜI đã chọn lô tay, gom theo (mã, kho) -> {lô: số gốc}. THUẦN.

	Dòng chọn tay không đi qua túi (máy không cãi người), nhưng nó VẪN ăn
	tồn của lô đó. Không trừ ra thì dòng máy chọn sau lại thấy đủ lô ấy và
	phiếu ghi ra nhiều hơn kho thật có. Codex nêu trên #219.

	Người chọn lô tay có HAI cách ghi, phải đọc cả hai:
	  - ô `batch_no` trên dòng (cách cũ, và cách của app);
	  - gói Serial and Batch Bundle (cách ERPNext v15+ dùng trên Desk khi
	    người ta chọn nhiều lô cho một dòng). Gói nằm ở bảng con của một
	    doctype khác nên phần thuần không tự đọc được; người gọi đưa vào
	    `lo_trong_goi(tên gói) -> {lô: số gốc}`. Codex tái hiện trên #222
	    (06/09/2026): bản trước bỏ qua gói, nên lô A tồn 60, một dòng gói
	    lấy 40, dòng máy chọn xin 30 vẫn được cấp trọn 30 từ lô A, tức phiếu
	    ghi 70 trên một lô chỉ có 60.
	Dòng có cả hai thì tin `batch_no`, không đếm hai lần.

	Số trong gói đã là SỐ GỐC (đơn vị kho) nên không nhân hệ số quy đổi; số
	trên dòng thì phải nhân, vì dòng có thể khai bằng Túi, Hộp.
	"""
	ra = {}
	for d in cac_dong or []:
		kho = (d.get("s_warehouse") or "").strip()
		if not kho:
			continue
		k = (d.get("item_code"), kho)
		lo = (d.get("batch_no") or "").strip()
		goi = (d.get("serial_and_batch_bundle") or "").strip()
		if lo:
			he_so = float(d.get("conversion_factor") or 0) or 1
			ra.setdefault(k, {})
			ra[k][lo] = round(ra[k].get(lo, 0) + float(d.get("qty") or 0) * he_so, 6)
		elif goi and lo_trong_goi:
			for ten_lo, so in (lo_trong_goi(goi) or {}).items():
				ten_lo = (ten_lo or "").strip()
				so = abs(float(so or 0))
				if not ten_lo or so <= LI_TI:
					continue
				ra.setdefault(k, {})
				ra[k][ten_lo] = round(ra[k].get(ten_lo, 0) + so, 6)
	return ra


def tru_da_dung(cac_lo, da_dung):
	"""Trừ phần người đã chọn tay ra khỏi tồn từng lô. THUẦN.

	`cac_lo` là {lô: tồn}, `da_dung` là {lô: số đã lấy tay}. Lô bị trừ về
	không thì bỏ hẳn, không để lại một dòng 0.
	"""
	if not cac_lo:
		return {}
	if not da_dung:
		return dict(cac_lo)
	ra = {}
	for ten, so in cac_lo.items():
		lai = round(float(so or 0) - float(da_dung.get(ten, 0) or 0), 6)
		if lai > LI_TI:
			ra[ten] = lai
	return ra


def _lo_trong_goi(ten_goi):
	"""Các lô trong một gói Serial and Batch Bundle -> {lô: số gốc}.

	Đọc bảng con `Serial and Batch Entry` (erpnext v16,
	erpnext/stock/doctype/serial_and_batch_entry/serial_and_batch_entry.json:
	có `batch_no`, `qty`, `warehouse`). Gói xuất kho ghi `qty` ÂM, nên lấy
	trị tuyệt đối. Đọc hỏng thì trả rỗng và ghi nhật ký: thà máy chọn thừa
	rồi ERPNext chặn ở validate_batch, còn hơn cả phiếu đổ vì một gói lạ.
	"""
	ra = {}
	if not ten_goi:
		return ra
	try:
		for r in frappe.get_all("Serial and Batch Entry",
				filters={"parent": ten_goi, "parenttype": "Serial and Batch Bundle"},
				fields=["batch_no", "qty"], limit_page_length=0):
			lo = (r.get("batch_no") or "").strip()
			if not lo:
				continue
			ra[lo] = round(ra.get(lo, 0) + abs(flt(r.get("qty"))), 6)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "lo_hang: doc goi lo %s" % ten_goi)
	return ra


def _tui_lo(bo, ma, kho, ke_ca_qua_han=False, da_dung=None):
	"""Túi lô dùng chung cho CẢ PHIẾU của một cặp (mã, kho).

	Tính tồn đúng MỘT LẦN cho mỗi cặp rồi trừ dần, xem `rut_tu_kho`. Hai
	dòng cùng mã cùng kho trong một phiếu vì thế không cùng ăn một phần
	tồn nữa. Phần người đã chọn lô tay được trừ ngay lúc dựng túi, xem
	`phan_da_chon_tay`.
	"""
	k = (ma, kho)
	if k not in bo:
		ton = _ton_tung_lo(ma, kho, ke_ca_qua_han=ke_ca_qua_han)
		tay = (da_dung or {}).get(k) or {}
		ton = tru_da_dung(ton, tay)
		bo[k] = {"con": _xep_het_han_truoc(ton), "goc": dict(ton), "vet": 0,
			"tay": dict(tay)}
	return bo[k]


def _vet_qua_han(muc, ma, kho):
	"""Đổ thêm lô QUÁ HẠN vào túi, đúng một lần cho mỗi cặp (mã, kho).

	Lô quá hạn mà người đã chọn tay cũng bị trừ phần đó, cùng luật với lô
	còn hạn.
	"""
	if muc.get("vet"):
		return
	muc["vet"] = 1
	hh = _ton_lo_qua_han(ma, kho, da_tinh=muc.get("goc") or {})
	hh = tru_da_dung(hh, muc.get("tay") or {})
	if hh:
		muc["con"] = list(muc.get("con") or []) + _xep_het_han_truoc(hh)


def gan_lo(doc, method=None):
	"""Hook before_validate của Stock Entry: điền lô cho các dòng bị trừ.

	Chỉ đụng vào dòng CHƯA có lô. Ai đã chọn lô bằng tay, hoặc dòng đã có
	gói lô của ERPNext, thì để nguyên - máy không được cãi người.

	Mã thay thế CHỈ áp cho luồng sản xuất, xem `duoc_thay_ma`.
	"""
	try:
		if cint(getattr(doc, "docstatus", 0)) != 0:
			return
		if not getattr(doc, "items", None):
			return

		can_lam = False
		for d in doc.items:
			if _dong_can_lo(d):
				can_lam = True
				break
		if not can_lam:
			return

		thay_ma = duoc_thay_ma(getattr(doc, "purpose", None))
		bo = {}
		da_dung = phan_da_chon_tay(doc.items, lo_trong_goi=_lo_trong_goi)
		moi = []
		for d in doc.items:
			if not _dong_can_lo(d):
				# Dòng không đụng tới thì bê nguyên, kể cả đơn giá ai đó
				# đã sửa tay. Chỉ bỏ số thứ tự để Frappe đánh lại.
				x = d.as_dict()
				x.pop("idx", None)
				moi.append(x)
				continue
			ma, kho = d.item_code, d.s_warehouse
			# Chia lô theo SỐ LƯỢNG GỐC (stock qty). Dòng khai bằng đơn vị
			# phụ (Túi, Hộp) mang hệ số quy đổi, mà tồn từng lô thì luôn
			# tính theo đơn vị gốc - chia theo d.qty trần là chia sai.
			he_so = flt(d.get("conversion_factor")) or 1
			can_goc = flt(d.qty) * he_so
			muc = _tui_lo(bo, ma, kho, da_dung=da_dung)
			phan, thieu = rut_tu_kho(muc, can_goc)

			# Thiếu thì thử MÃ THAY THẾ đã duyệt trước khi chặn: hết bơ
			# Avonmore mà bơ Anchor còn đầy kệ thì bếp không việc gì phải
			# đứng chờ. Máy lấy phần thiếu từ mã thay thế, ghi rõ trên
			# từng dòng để kế toán giá thành lần lại được.
			#
			# CHỈ luồng sản xuất. Phiếu nhận nguyên liệu thì kho giao mã
			# nào ghi sổ mã đó, xem `duoc_thay_ma`.
			phan_thay = []
			if thieu > LI_TI and thay_ma:
				for ma_thay in _cac_ma_thay_the(ma):
					muc_thay = _tui_lo(bo, ma_thay, kho, da_dung=da_dung)
					p2, thieu = rut_tu_kho(muc_thay, thieu)
					for ten_lo, so in p2:
						phan_thay.append((ma_thay, ten_lo, so))
					if thieu <= LI_TI:
						break
			# Vòng vét cuối: lô QUÁ HẠN của chính mã đó. Đặt sau cùng để
			# máy không tự dồn hàng quá hạn vào bánh khi kho còn hàng tốt
			# và còn mã thay thế. Chốt của anh Việt 03/09/2026: thà bếp
			# xuất được rồi ghi vết, còn hơn đứng im vì một dòng ngày hết
			# hạn gõ sai lúc kiểm kho. Ô chặn nằm ở Vagabond Settings.
			if thieu > LI_TI and not lo_het_han.dang_chan():
				_vet_qua_han(muc, ma, kho)
				p3, thieu = rut_tu_kho(muc, thieu)
				phan = list(phan) + list(p3)
			if thieu > LI_TI:
				frappe.throw(
					cau_thieu_lo(
						_ten_hang(d, ma), ma, kho, thieu,
						d.get("stock_uom") or d.get("uom") or "",
						_kho_khac_con(ma, kho),
						[(m, k, t) for m in _cac_ma_thay_the(ma) for k, t in _kho_khac_con(m, kho)] if thay_ma else [],
					),
					title="Thiếu hàng trong kho",
				)
			for i, (ten_lo, so) in enumerate(phan):
				x = _boc(d, giu_ten=(i == 0))
				x["qty"] = round(so / he_so, 6)
				x["batch_no"] = ten_lo
				x["use_serial_batch_fields"] = 1
				moi.append(x)
			for j, (ma_thay, ten_lo, so) in enumerate(phan_thay):
				# Giữ tên dòng gốc đúng MỘT lần: nếu mã chính không góp được
				# lô nào thì dòng thay thế đầu tiên thừa kế tên dòng gốc.
				x = _boc(d, giu_ten=(not phan and j == 0))
				x["item_code"] = ma_thay
				# WorkOrder.get_consumed_qty (ERPNext 16.28.0) cộng theo
				# item_code HOẶC original_item. Diễn giải không thay liên kết.
				x["original_item"] = d.get("original_item") or ma
				# Dòng thay thế đi bằng đơn vị GỐC cho khỏi kéo hệ số quy
				# đổi của mã cũ sang mã mới.
				x["qty"] = so
				x["uom"] = frappe.get_cached_value("Item", ma_thay, "stock_uom")
				x["conversion_factor"] = 1
				x["batch_no"] = ten_lo
				x["use_serial_batch_fields"] = 1
				x.pop("item_name", None)
				x.pop("description", None)
				x["description"] = "Dùng thay %s đang hết tại kho (mã thay thế đã duyệt)." % ma
				moi.append(x)

		doc.set("items", [])
		for x in moi:
			doc.append("items", x)
	except frappe.ValidationError:
		raise
	except Exception:
		# Hỏng ở đây không được kéo đổ cả phiếu: để ERPNext xử như trước.
		frappe.log_error(frappe.get_traceback(), "lo_hang: gan lo tu dong")


def _ten_hang(d, ma):
	"""Tên món để đưa vào câu báo lỗi.

	Ở `before_validate` thì ERPNext chưa kịp điền `item_name`, nên câu lỗi
	sẽ chỉ có mã trần kiểu NVLT00166. Bếp không thuộc mã, và một câu lỗi
	không đọc được thì cũng như không có (QT-24). Nên tra thẳng bảng Item.
	"""
	ten = (d.get("item_name") or "").strip()
	if ten:
		return ten
	try:
		return frappe.get_cached_value("Item", ma, "item_name") or ma
	except Exception:
		return ma


def _dong_can_lo(d):
	"""Dòng này có phải dòng bị trừ, theo lô, mà chưa ai chọn lô không."""
	if not (d.get("s_warehouse") or "").strip():
		return False
	if (d.get("batch_no") or "").strip():
		return False
	if (d.get("serial_and_batch_bundle") or "").strip():
		return False
	if flt(d.get("qty")) <= LI_TI:
		return False
	return bool(_theo_lo(d.get("item_code")))


def _boc(d, giu_ten):
	"""Đổi một dòng thành dict để đắp lại.

	Bản sao PHẢI bỏ tên của bản gốc, nếu không hai dòng cùng một tên và
	Frappe ghi đè dòng nọ lên dòng kia, mất hẳn một lô.
	"""
	x = d.as_dict()
	for k in KHOA_BO:
		x.pop(k, None)
	if giu_ten:
		x["name"] = d.name
	return x
