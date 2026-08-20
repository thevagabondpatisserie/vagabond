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


def cau_thieu_lo(ten_hang, ma, kho, thieu, don_vi, kho_khac):
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
	else:
		cau += " Cả hệ không còn tồn mã này, phải nhập hàng hoặc kiểm kê lại trước."
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


def _ton_tung_lo(ma, kho):
	"""Tồn từng lô của một mã tại một kho. Trả về {tên lô: tồn}."""
	ra = {}
	try:
		from erpnext.stock.doctype.batch.batch import get_batch_qty

		ds = get_batch_qty(item_code=ma, warehouse=kho) or []
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
	try:
		dong = frappe.get_all(
			"Stock Ledger Entry",
			filters={"item_code": ma, "warehouse": kho, "is_cancelled": 0},
			fields=["batch_no", "sum(actual_qty) as ton"],
			group_by="batch_no",
			limit_page_length=0,
		)
		for d in dong:
			if not d.get("batch_no"):
				continue
			if flt(d.get("ton")) > LI_TI:
				ra[d["batch_no"]] = flt(d["ton"])
	except Exception:
		pass
	return ra


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


def gan_lo(doc, method=None):
	"""Hook before_validate của Stock Entry: điền lô cho các dòng bị trừ.

	Chỉ đụng vào dòng CHƯA có lô. Ai đã chọn lô bằng tay, hoặc dòng đã có
	gói lô của ERPNext, thì để nguyên - máy không được cãi người.
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
			ton = _ton_tung_lo(ma, kho)
			phan, thieu = chia_theo_lo(flt(d.qty), _xep_het_han_truoc(ton))
			if thieu > LI_TI:
				frappe.throw(
					cau_thieu_lo(
						d.get("item_name") or ma, ma, kho, thieu,
						d.get("uom") or d.get("stock_uom") or "",
						_kho_khac_con(ma, kho),
					),
					title="Thiếu hàng trong kho",
				)
			for i, (ten_lo, so) in enumerate(phan):
				x = _boc(d, giu_ten=(i == 0))
				x["qty"] = so
				x["batch_no"] = ten_lo
				x["use_serial_batch_fields"] = 1
				moi.append(x)

		doc.set("items", [])
		for x in moi:
			doc.append("items", x)
	except frappe.ValidationError:
		raise
	except Exception:
		# Hỏng ở đây không được kéo đổ cả phiếu: để ERPNext xử như trước.
		frappe.log_error(frappe.get_traceback(), "lo_hang: gan lo tu dong")


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
