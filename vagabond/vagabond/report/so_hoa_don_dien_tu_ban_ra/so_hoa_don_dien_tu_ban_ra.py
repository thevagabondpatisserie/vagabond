"""Sổ hoá đơn điện tử bán ra (v536).

Mỗi tờ trên m-invoice một dòng, đúng số, ký hiệu, ngày lập, tên người mua,
mã số thuế, trạng thái, tờ gốc, đơn ERP và MÃ KHÁCH KẾ TOÁN theo luật của
chị Dung: không MST là KL0001, có MST là mã Fast của công ty. Nguồn là bảng
MInvoice Invoice (bản chụp 1:1 của m-invoice), không phải đơn hàng, nên tờ
thay thế, tờ lập tay, tờ tách đều có mặt. Chỉ đọc.
"""
import frappe
from frappe.utils import add_days, cint, getdate

from vagabond import ma_ke_toan
from vagabond.doi_soat_hddt_ra import kh, so, tach_ghi_thay_the, tach_goc

TOI_DA = 5000


def cot():
	return [
		dict(fieldname="ngay_lap", label="Ngày lập", fieldtype="Date", width=95),
		dict(fieldname="ky_hieu", label="Ký hiệu", fieldtype="Data", width=80),
		dict(fieldname="so_hd", label="Số", fieldtype="Data", width=70),
		dict(fieldname="ma_khach", label="Mã khách KT", fieldtype="Data", width=95),
		dict(fieldname="nguoi_mua_ban", label="Người mua", fieldtype="Data", width=260),
		dict(fieldname="mst_doi_tac", label="MST", fieldtype="Data", width=115),
		dict(fieldname="tien_truoc_thue", label="Trước thuế", fieldtype="Currency", width=110),
		dict(fieldname="tien_thue", label="Thuế", fieldtype="Currency", width=95),
		dict(fieldname="tong_tien", label="Tổng tiền", fieldtype="Currency", width=115),
		dict(fieldname="trang_thai", label="Trạng thái", fieldtype="Data", width=95),
		dict(fieldname="to_goc", label="Thay/điều chỉnh tờ", fieldtype="Data", width=110),
		dict(fieldname="don_erp", label="Đơn ERP", fieldtype="Link", options="Sales Invoice", width=150),
		dict(fieldname="cach_noi", label="Nối", fieldtype="Data", width=80),
		dict(fieldname="ma_cqt", label="Mã CQT", fieldtype="Data", width=130),
		dict(fieldname="ngay_ky", label="Ngày ký", fieldtype="Date", width=95),
		dict(fieldname="to", label="Tờ m-invoice", fieldtype="Link", options="MInvoice Invoice", width=120),
	]


def dong_so(t, ma_theo_mst, don_cua_to):
	"""Một dòng sổ từ một tờ. THUẦN: ma_theo_mst là {mst_chuan: mã},
	don_cua_to(t) trả (đơn, cách nối)."""
	goc = tach_goc(t.get("hd_goc"))
	don, cach = don_cua_to(t)
	return {
		"to": t.get("name"), "ngay_lap": t.get("ngay_lap"), "ky_hieu": kh(t.get("ky_hieu")),
		"so_hd": so(t.get("so_hd")),
		"ma_khach": ma_ke_toan.ma_ke_toan_cua_hoa_don(t.get("mst_doi_tac"),
			lambda m: ma_theo_mst.get(m, "")) or "(chưa có mã)",
		"nguoi_mua_ban": t.get("nguoi_mua_ban") or "", "mst_doi_tac": ma_ke_toan.chuan_mst(t.get("mst_doi_tac")) or "",
		"tien_truoc_thue": t.get("tien_truoc_thue"), "tien_thue": t.get("tien_thue"), "tong_tien": t.get("tong_tien"),
		"trang_thai": t.get("trang_thai") or "", "to_goc": goc[1] if goc else "",
		"don_erp": don, "cach_noi": cach, "ma_cqt": t.get("ma_cqt") or "", "ngay_ky": t.get("ngay_ky"),
	}


def _don_cua_to_tren_site(to_ds):
	"""Đơn ERP của từng tờ: ô Đơn ERP đã nối (máy hoặc tay), không có thì tra
	theo mã m-invoice hoặc ký hiệu và số, rồi theo ô Hoá đơn thay thế."""
	ten = [t["name"] for t in to_ds]
	theo_id, theo_so, theo_thay = {}, {}, {}
	if ten:
		for o in ("custom_minvoice_id", "custom_hddt_id"):
			for r in frappe.get_all("Sales Invoice", filters={o: ["in", ten], "docstatus": 1},
					fields=["name", o], limit_page_length=0):
				theo_id.setdefault(r[o], r["name"])
	so_ds = sorted({so(t.get("so_hd")) for t in to_ds if so(t.get("so_hd"))})
	if so_ds:
		for r in frappe.get_all("Sales Invoice", filters={"custom_hddt_so": ["in", so_ds], "docstatus": 1},
				fields=["name", "custom_hddt_so", "custom_hddt_ky_hieu"], limit_page_length=0):
			theo_so.setdefault((kh(r.get("custom_hddt_ky_hieu")), so(r.get("custom_hddt_so"))), r["name"])
		for r in frappe.get_all("Sales Invoice", filters={"custom_hddt_thay_the": ["is", "set"], "docstatus": 1,
				"posting_date": [">=", add_days(min(getdate(t["ngay_lap"]) for t in to_ds if t.get("ngay_lap")) if any(t.get("ngay_lap") for t in to_ds) else getdate(), -120)]},
				fields=["name", "custom_hddt_thay_the"], limit_page_length=0):
			cap = tach_ghi_thay_the(r.get("custom_hddt_thay_the"))
			if cap:
				theo_thay.setdefault(cap, r["name"])

	def tra(t):
		if str(t.get("vgb_don_erp") or "").strip():
			return t["vgb_don_erp"], "đã nối"
		k, n = kh(t.get("ky_hieu")), so(t.get("so_hd"))
		if t["name"] in theo_id:
			return theo_id[t["name"]], "ERP xuất"
		d = theo_so.get((k, n)) or theo_so.get(("", n))
		if d:
			return d, "ERP xuất"
		d = theo_thay.get((k, n))
		if d:
			return d, "thay thế"
		return "", ""
	return tra


def execute(filters=None):
	f = filters or {}
	a, b = getdate(f.get("tu_ngay")), getdate(f.get("den_ngay"))
	if a > b:
		frappe.throw("Từ ngày không được sau Đến ngày.")
	loc = {"loai": "Đầu ra", "ngay_lap": ["between", [a, b]]}
	if f.get("so_hd"):
		loc["so_hd"] = cint(so(f["so_hd"]))
	if f.get("ky_hieu"):
		loc["ky_hieu"] = ["like", "%" + str(f["ky_hieu"]).strip()[-6:] + "%"]
	if f.get("trang_thai"):
		loc["trang_thai"] = f["trang_thai"]
	if f.get("chi_chua_noi"):
		loc["vgb_don_erp"] = ["is", "not set"]
	to_ds = frappe.get_list("MInvoice Invoice", filters=loc, fields=["name", "so_hd", "ky_hieu", "ngay_lap",
		"nguoi_mua_ban", "mst_doi_tac", "tien_truoc_thue", "tien_thue", "tong_tien", "trang_thai", "hd_goc",
		"vgb_don_erp", "ma_cqt", "ngay_ky"], order_by="ngay_lap asc, so_hd asc", limit_page_length=TOI_DA + 1)
	tim = str(f.get("nguoi_mua") or "").strip().lower()
	if tim:
		so_tim = ma_ke_toan.chuan_mst(tim)
		to_ds = [t for t in to_ds if tim in str(t.get("nguoi_mua_ban") or "").lower()
			or (so_tim and ma_ke_toan.chuan_mst(t.get("mst_doi_tac")) == so_tim)]
	ma_theo_mst = ma_ke_toan.bang_ma_theo_mst([t.get("mst_doi_tac") for t in to_ds])
	tra = _don_cua_to_tren_site(to_ds) if to_ds else (lambda t: ("", ""))
	rows = [dong_so(t, ma_theo_mst, tra) for t in to_ds]
	if f.get("ma_khach"):
		mk = str(f["ma_khach"]).strip().upper()
		rows = [r for r in rows if r["ma_khach"] == mk]
	if f.get("chi_chua_noi"):
		rows = [r for r in rows if not r["don_erp"]]
	msg = "%d tờ." % len(rows)
	if len(to_ds) > TOI_DA:
		msg += " Quá %d tờ, thu hẹp khoảng ngày để xem hết." % TOI_DA
	thieu = sum(1 for r in rows if r["ma_khach"] == "(chưa có mã)")
	if thieu:
		msg += " %d tờ có MST nhưng khách chưa có mã kế toán: nạp danh mục Fast hoặc lưu lại hồ sơ khách." % thieu
	return cot(), rows, msg
