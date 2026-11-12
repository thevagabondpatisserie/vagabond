"""v650 (anh Việt cho phép 12/11/2026): bỏ dòng thuế đầu ra 33311 máy tự thêm trên
đơn mua, phiếu nhập kho và báo giá nhà cung cấp CŨ.

Từ 22/07/2026 mẫu thuế từng món khai cả 1331 lẫn 33311, Cài đặt kế toán tự thêm
thuế theo mẫu của món, nên chứng từ mua có thêm dòng 33311 và tổng tiền cộng VAT
hai lần (đọc site 12/11: 125 đơn mua, 137 phiếu nhập đã ghi sổ, 1 đơn mua và 34
phiếu nhập nháp, 1 báo giá). Hook v650 chặn từ nay; bản này dọn chứng từ cũ.

Vì sao làm được an toàn:
- Dòng 33311 trên các chứng từ này loại "Total": không sinh bút toán (đọc site:
  0 dòng sổ cái 33311 từ đơn mua, phiếu nhập, hoá đơn mua). Bỏ dòng chỉ sửa số
  hiển thị và tổng tiền trên chứng từ, không đụng sổ cái, sổ kho.
- KHÔNG đụng Hoá đơn mua (gắn hoá đơn điện tử, dòng 33311 ở đó đều 0 đồng) và
  chứng từ đã huỷ.
- Chỉ TRỪ đúng dòng 33311 (thue_don_mua.tinh_bo_thue), không tính lại theo mẫu
  thuế hiện tại: chạy thử trên site 12/11, tính lại làm đổi thuế 1331 của 7 chứng
  từ cũ vì mẫu thuế món đã đổi từ đó.
- Kiểm trước khi ghi: tổng cũ phải bằng tiền hàng cộng thuế (lệch tối đa 1 đồng),
  và sau khi trừ thì tiền hàng, thuế 1331 giữ nguyên, ứng trước không vượt tổng
  mới (thue_don_mua.kiem_sau_bo). Không đạt thì bỏ qua, liệt kê vào Error Log.
- Codex #553: trừ theo số thuế SAU giảm giá trên tổng (tax_amount_after_discount_amount),
  và chia lại lịch thanh toán của đơn mua theo tổng mới, giữ phần đã trả.
- Mỗi chứng từ đã sửa có một dòng ghi chú ghi số trước và sau.
"""

import frappe
from frappe.utils import flt

LOAI = ("Purchase Order", "Purchase Receipt", "Supplier Quotation")
TIEU_DE_LOG = "v650 bỏ thuế 33311 tự thêm: chứng từ bỏ qua"
TRUONG_CHA = ("net_total", "grand_total", "base_grand_total", "total_taxes_and_charges",
	"base_total_taxes_and_charges", "taxes_and_charges_added", "base_taxes_and_charges_added",
	"rounded_total", "base_rounded_total", "disable_rounded_total", "advance_paid", "currency")


def cac_chung_tu(dt):
	"""Chứng từ chưa huỷ của loại dt có dòng 33311 dạng máy tự thêm."""
	return [r[0] for r in frappe.db.sql(
		"""select distinct p.name from `tab{dt}` p
		join `tabPurchase Taxes and Charges` t on t.parent = p.name and t.parenttype = %(dt)s
		where p.docstatus < 2 and t.account_head like %(ra)s
		and t.charge_type = 'On Net Total' and t.rate = 0
		order by p.name""".format(dt=dt),
		{"dt": dt, "ra": "33311%"},
	)]


def _tien(x):
	return "{:,.0f}".format(flt(x)).replace(",", ".")


def _bang_chu(dt, cha, moi):
	from frappe.utils import money_in_words

	meta = frappe.get_meta(dt)
	ra = {}
	cty = frappe.get_cached_value("Company", cha.get("company"), "default_currency") if cha.get("company") else None
	for p, tien in (("", cha.get("currency")), ("base_", cty or cha.get("currency"))):
		if not meta.get_field(p + "in_words"):
			continue
		so = moi.get(p + "rounded_total") if (meta.get_field(p + "rounded_total") and not int(cha.get("disable_rounded_total") or 0)
			and flt(moi.get(p + "rounded_total", cha.get(p + "rounded_total")))) else moi.get(p + "grand_total")
		ra[p + "in_words"] = money_in_words(abs(flt(so)), tien)
	return ra


def sua_mot(dt, ten):
	"""Bỏ dòng 33311 tự thêm của một chứng từ. Trả None nếu không có gì để bỏ,
	{"ten", "loi"} nếu không đạt kiểm (không ghi gì), hoặc {"ten", "truoc", "sau"}."""
	from frappe.utils import round_based_on_smallest_currency_fraction

	from vagabond import thue_don_mua as tdm

	meta = frappe.get_meta(dt)
	cot = [k for k in TRUONG_CHA + ("company",) if meta.has_field(k)]
	cha = frappe.db.get_value(dt, ten, cot, as_dict=True) or {}
	dong = frappe.get_all("Purchase Taxes and Charges", filters={"parenttype": dt, "parent": ten, "parentfield": "taxes"},
		fields=["name", "idx", "account_head", "charge_type", "rate", "tax_amount", "base_tax_amount",
			"tax_amount_after_discount_amount", "base_tax_amount_after_discount_amount", "total",
			"base_total", "add_deduct_tax"], order_by="idx asc", limit_page_length=0)
	bo = tdm.dong_thue_ra_tu_them(dong)
	if not bo:
		return None
	ten_bo = [dong[i]["name"] for i in bo]

	def thue(r):
		# Số SAU giảm giá trên tổng (Codex #553), chứng từ không giảm thì bằng tax_amount.
		v = r.get("tax_amount_after_discount_amount")
		return flt(v if v is not None else r.get("tax_amount"))

	thue_bo = sum(thue(dong[i]) for i in bo)
	thue_giu = sum(thue(r) for i, r in enumerate(dong) if i not in bo)
	if abs(flt(cha.get("grand_total")) - flt(cha.get("net_total")) - flt(cha.get("total_taxes_and_charges"))) > 1:
		return {"ten": ten, "loi": ["tổng cũ không bằng tiền hàng cộng thuế"]}

	tien_te = cha.get("currency")
	moi, dong_moi = tdm.tinh_bo_thue(cha, dong, bo,
		lam_tron=lambda x: round_based_on_smallest_currency_fraction(x, tien_te, 0))
	truoc = {"net_total": flt(cha.get("net_total")), "grand_total": flt(cha.get("grand_total")), "thue_giu": thue_giu,
		"advance_paid": flt(cha.get("advance_paid"))}
	sau = dict(truoc, grand_total=moi["grand_total"])
	loi = tdm.kiem_sau_bo(truoc, sau, thue_bo)
	if loi:
		return {"ten": ten, "loi": loi}

	# Codex #553: lịch thanh toán của đơn mua theo tổng mới, tính xong mới ghi.
	lich_moi = []
	if meta.get_field("payment_schedule"):
		lich = frappe.get_all("Payment Schedule", filters={"parenttype": dt, "parent": ten},
			fields=["name", "invoice_portion", "payment_amount", "paid_amount", "base_paid_amount", "discounted_amount"],
			order_by="idx asc", limit_page_length=0)
		lam_tron_bat = not int(cha.get("disable_rounded_total") or 0) and flt(moi.get("rounded_total"))
		lich_moi, loi_lich = tdm.chia_lich_tra(lich,
			flt(moi["rounded_total"] if lam_tron_bat else moi["grand_total"]),
			flt(moi.get("base_rounded_total") if lam_tron_bat else moi.get("base_grand_total")))
		if loi_lich:
			return {"ten": ten, "loi": loi_lich}

	moi.update(_bang_chu(dt, cha, moi))
	frappe.db.set_value(dt, ten, {k: v for k, v in moi.items() if meta.has_field(k)}, update_modified=False)
	for r in dong_moi:
		frappe.db.set_value("Purchase Taxes and Charges", r["name"],
			{"idx": r["idx"], "total": r["total"], "base_total": r["base_total"]}, update_modified=False)
	for r in lich_moi:
		frappe.db.set_value("Payment Schedule", r.pop("name"), r, update_modified=False)
	frappe.db.delete("Purchase Taxes and Charges", {"name": ["in", ten_bo]})
	frappe.db.delete("Item Wise Tax Detail", {"parenttype": dt, "parent": ten, "tax_row": ["in", ten_bo]})
	frappe.get_doc({"doctype": "Comment", "comment_type": "Comment", "reference_doctype": dt, "reference_name": ten,
		"content": ("Máy bỏ dòng thuế đầu ra 33311 tự thêm (v650, anh Việt cho phép 12/11/2026). "
			"Thuế: %s → %s đ. Tổng: %s → %s đ. Không đổi sổ cái, sổ kho."
			% (_tien(thue_giu + thue_bo), _tien(thue_giu), _tien(truoc["grand_total"]), _tien(moi["grand_total"])))
	}).insert(ignore_permissions=True)
	return {"ten": ten, "truoc": truoc, "sau": sau}


def execute():
	da_sua, bo_qua = {}, []
	for dt in LOAI:
		for ten in cac_chung_tu(dt):
			kq = sua_mot(dt, ten)
			if not kq:
				continue
			if kq.get("loi"):
				bo_qua.append("%s %s: %s" % (dt, ten, ", ".join(kq["loi"])))
			else:
				da_sua[dt] = da_sua.get(dt, 0) + 1
	if bo_qua:
		frappe.log_error("\n".join(bo_qua), TIEU_DE_LOG)
	print("v650 bỏ thuế 33311 tự thêm: đã sửa %s; bỏ qua %d" % (da_sua, len(bo_qua)))
	return {"da_sua": da_sua, "bo_qua": bo_qua}
