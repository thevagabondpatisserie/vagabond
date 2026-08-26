# -*- coding: utf-8 -*-
"""Dựng lại hoá đơn mua theo đúng bản hoá đơn điện tử gốc.

Ca thật ngày 26/08/2026, hoá đơn HDM-26-08-00012 của Thanh An Eggpack
------------------------------------------------------------------------
Bản đồng bộ về ĐÚNG: trứng gà 1.500 quả, đơn giá 2.190,48, tiền hàng
3.285.720, tổng 3.450.000. Khớp từng đồng với tờ giấy.

Ngày 17/08 có người bấm nút "Nối phiếu nhập kho" của ERPNext trên Desk.
Nút đó KHÔNG nối, nó CHÉP dòng hàng từ phiếu nhập đè lên dòng hàng của hoá
đơn. Phiếu nhập ghi giá đặt hàng 2.100, nên tiền hàng tụt xuống 3.150.000
và tổng còn 3.314.280. Mất 135.720 đồng, không ai được báo gì.

Đây là chỗ khác nhau giữa hai nút trông giống nhau:

  * Nút "Nối phiếu nhập kho" của ERPNext trên Desk: chép dòng hàng của
    phiếu nhập sang, GHI ĐÈ số lượng và đơn giá của hoá đơn.
  * Màn "Đối chiếu hoá đơn mua" trong app: chỉ gắn dòng hoá đơn vào dòng
    phiếu nhập, KHÔNG đụng tới số lượng hay đơn giá.

Cửa chặn ghi sổ đã có sẵn (`mua_dich_vu.chan_lech_tong`) nên tờ sai không
vào được sổ cái. Nhưng chặn ở phút chót thì người ta đã gõ xong xuôi mới
biết, mà lại không có đường nào để dựng lại số cũ ngoài gõ tay.

Tệp này bù hai chỗ đó:

  1. Cảnh báo NGAY LÚC LƯU, không đợi tới lúc ghi sổ.
  2. Một nút dựng lại dòng hàng theo hoá đơn điện tử gốc.

Đếm ngày 26/08/2026: 3.077 hoá đơn mua sinh từ hoá đơn điện tử, 323 tờ còn
nháp đang lệch tổng, và 3 tờ ĐÃ GHI SỔ mà lệch. Ba tờ đó chỉ liệt kê cho
anh Việt, không tự sửa (điều 11).
"""

import json

import frappe
from frappe.utils import cint, flt

from vagabond import mua_dich_vu

DT_HD = "MInvoice Invoice"
PI = "Purchase Invoice"

QUYEN = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"Purchase Manager",
	"Purchase User",
}

# Cùng ngưỡng với cửa chặn ghi sổ, để người dùng chỉ phải nhớ MỘT con số.
NGUONG = mua_dich_vu.NGUONG_LECH


# ----------------------------------------------------------------- thuần


def huong_lech(tong_erp, tong_hddt):
	"""Phiếu đang thiếu hay thừa so với hoá đơn điện tử. THUẦN.

	Trả ("khop", 0) | ("thieu", x) | ("thua", x), x luôn dương.
	"""
	a, b = flt(tong_erp), flt(tong_hddt)
	if not mua_dich_vu.lech_qua_nguong(a, b, NGUONG):
		return "khop", 0.0
	return ("thieu", b - a) if a < b else ("thua", a - b)


def cau_canh_bao(ten, tong_erp, tong_hddt):
	"""Câu báo cho người đang lưu phiếu. THUẦN, không chạm Frappe."""
	viec, so = huong_lech(tong_erp, tong_hddt)
	if viec == "khop":
		return ""
	return (
		"Hoá đơn %s đang %s %s đồng so với bản hoá đơn điện tử của nhà cung cấp "
		"(phiếu %s đồng, hoá đơn điện tử %s đồng). Số trên hoá đơn điện tử là số "
		"đã gửi cơ quan thuế nên không ghi sổ được khi còn lệch. "
		'Bấm "Dựng lại theo hoá đơn điện tử" ở màn Đối chiếu để lấy lại số gốc. '
		'Lưu ý nút "Nối phiếu nhập kho" bên màn quản trị sẽ chép đè giá của '
		"phiếu nhập lên hoá đơn, đó thường là nguyên nhân."
		% (ten, "thiếu" if viec == "thieu" else "thừa", _so(so), _so(tong_erp), _so(tong_hddt))
	)


def _so(x):
	"""Số tiền có dấu chấm ngăn nghìn, không phần thập phân. THUẦN."""
	try:
		n = int(round(float(x or 0)))
	except (TypeError, ValueError):
		return "0"
	dau = "-" if n < 0 else ""
	s = str(abs(n))
	cum = []
	while s:
		cum.insert(0, s[-3:])
		s = s[:-3]
	return dau + ".".join(cum)


def doc_chi_tiet(chi_tiet):
	"""Danh sách dòng hàng thô của một hoá đơn điện tử. THUẦN.

	Chuỗi hỏng thì trả danh sách rỗng chứ không nổ: một tờ hỏng không được
	làm chết cả nhịp.
	"""
	if isinstance(chi_tiet, (list, tuple)):
		return list(chi_tiet)
	try:
		ds = json.loads(chi_tiet or "[]")
	except (ValueError, TypeError):
		return []
	return ds if isinstance(ds, list) else []


# ------------------------------------------------------- phan can Frappe


def _kiem_quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Việc này dành cho kế toán và thu mua.")


def _goc(ma_minvoice):
	"""Bản hoá đơn điện tử gốc của một phiếu. None nếu phiếu không từ đó ra."""
	ma = (ma_minvoice or "").strip()
	if not ma:
		return None
	return frappe.db.get_value(
		DT_HD, ma,
		["name", "so_hd", "ky_hieu", "ngay_lap", "tong_tien", "tien_truoc_thue",
			"tien_thue", "mst_doi_tac", "nguoi_mua_ban", "chi_tiet"],
		as_dict=True,
	)


def canh_bao_lech(doc, method=None):
	"""Hook `validate` trên Hoá đơn mua: nói ngay lúc lưu, không đợi ghi sổ.

	CHỈ nhắc chứ không chặn. Chặn ở đây là nhốt luôn 323 tờ nháp đang lệch
	sẵn, người ta không mở ra sửa được nữa. Cửa chặn thật nằm ở
	`mua_dich_vu.chan_lech_tong`, đúng lúc ghi sổ.
	"""
	try:
		if cint(doc.get("docstatus")) != 0:
			return
		g = _goc(doc.get("custom_minvoice_id"))
		if not g or not flt(g.get("tong_tien")):
			return
		cau = cau_canh_bao(doc.get("name") or "này", doc.get("base_grand_total"), g.get("tong_tien"))
		if cau:
			frappe.msgprint(cau, title="Lệch so với hoá đơn điện tử", indicator="orange")
	except Exception:
		# Cảnh báo hỏng thì thôi, tuyệt đối không làm rớt việc lưu phiếu.
		frappe.log_error(frappe.get_traceback(), "dung_lai_hddt: canh bao lech")


@frappe.whitelist()
def soat(gioi_han=300):
	"""CHỈ ĐỌC: những hoá đơn mua sinh từ hoá đơn điện tử đang lệch tổng.

	Tách riêng phần ĐÃ GHI SỔ: mấy tờ đó không tự sửa được nữa, chỉ liệt kê
	cho anh Việt xem (điều 11, không đề xuất sửa dữ liệu quá khứ).
	"""
	_kiem_quyen()
	ds = frappe.get_all(
		PI,
		filters={"custom_minvoice_id": ["is", "set"], "docstatus": ["<", 2]},
		fields=["name", "supplier_name", "posting_date", "bill_no", "docstatus",
			"base_grand_total", "custom_minvoice_id"],
		order_by="posting_date desc",
		limit_page_length=0,
	)
	if not ds:
		return {"nhap": [], "da_ghi_so": [], "so_nhap": 0, "so_da_ghi_so": 0}
	goc = {
		r["name"]: r
		for r in frappe.get_all(
			DT_HD,
			filters={"name": ["in", [x["custom_minvoice_id"] for x in ds]]},
			fields=["name", "tong_tien", "so_hd", "ky_hieu"],
			limit_page_length=0,
		)
	}
	nhap, xong = [], []
	for r in ds:
		g = goc.get(r["custom_minvoice_id"])
		if not g or not flt(g["tong_tien"]):
			continue
		viec, so = huong_lech(r["base_grand_total"], g["tong_tien"])
		if viec == "khop":
			continue
		mot = {
			"name": r["name"],
			"ncc": r["supplier_name"],
			"ngay": str(r["posting_date"] or ""),
			"so_hddt": "%s/%s" % (g.get("ky_hieu") or "", g.get("so_hd") or ""),
			"tong_erp": flt(r["base_grand_total"]),
			"tong_hddt": flt(g["tong_tien"]),
			"viec": viec,
			"lech": so,
		}
		(xong if cint(r["docstatus"]) == 1 else nhap).append(mot)
	nhap.sort(key=lambda x: -x["lech"])
	xong.sort(key=lambda x: -x["lech"])
	return {
		"nhap": nhap[: max(1, cint(gioi_han) or 300)],
		"da_ghi_so": xong,
		"so_nhap": len(nhap),
		"so_da_ghi_so": len(xong),
		"nguong": NGUONG,
	}


@frappe.whitelist()
def dung_lai(name):
	"""Dựng lại dòng hàng của một hoá đơn NHÁP theo hoá đơn điện tử gốc.

	Chỉ đụng bảng dòng hàng. Nhà cung cấp, ngày, số hoá đơn, dòng thuế đều
	giữ nguyên - chúng vốn đã lấy từ hoá đơn điện tử.

	Phiếu đã ghi sổ thì TỪ CHỐI. Sửa chứng từ đã vào sổ là việc của kế toán
	với chị Dung, không phải việc của một cái nút.

    Tệp này gọi hai hàm nội bộ của `minvoice_chung_tu` để tra mã hàng và
    dựng dòng, cốt để hai đường dựng chứng từ không bao giờ ra hai kết quả
    khác nhau. Đổi chữ ký hai hàm đó thì ca kiểm `thu_dung_lai_hddt` đỏ
    ngay, đừng bỏ qua.
	"""
	_kiem_quyen()
	doc = frappe.get_doc(PI, name)
	if cint(doc.docstatus) != 0:
		frappe.throw(
			"Hoá đơn %s đã ghi sổ rồi, không dựng lại được. Trường hợp này báo "
			"anh Việt và chị Dung xem xét, đừng tự sửa." % name
		)
	g = _goc(doc.get("custom_minvoice_id"))
	if not g:
		frappe.throw(
			"Hoá đơn %s không phải sinh từ hoá đơn điện tử nên không có bản gốc "
			"để dựng lại." % name
		)
	dong_goc = doc_chi_tiet(g.get("chi_tiet"))
	if not dong_goc:
		frappe.throw(
			"Bản hoá đơn điện tử %s không còn dòng hàng nào để dựng lại."
			% (g.get("so_hd") or "")
		)

	from vagabond import minvoice_chung_tu as mc

	goc_mst = (g.get("mst_doi_tac") or "").split("-")[0]
	tk = None
	for d in doc.items:
		if d.get("expense_account"):
			tk = d.expense_account
			break

	moi = []
	for it in dong_goc:
		x = mc.dong_tu_hoa_don(it)
		ma, uom, he_so = mc._tra_ma_hang(x, goc_mst, doc.supplier)
		moi.append(mc._dong_pi(x, tk, ma, uom, he_so))

	tong_dong = sum(flt(d.get("qty")) * flt(d.get("rate")) for d in moi)
	viec, so_tien = mc.can_theo_truoc_thue(tong_dong, g.get("tien_truoc_thue"))
	if viec == "phi":
		moi.append(mc._dong_pi({
			"ma": "", "ten": "Phí khác theo hoá đơn", "dvt": None,
			"sl": 1, "gia": so_tien, "tien": so_tien,
		}, tk))

	truoc = flt(doc.base_grand_total)
	doc.set("items", [])
	tt = doc.get("cost_center")
	for d in moi:
		if tt:
			d["cost_center"] = tt
		doc.append("items", d)
	doc.apply_discount_on = "Net Total"
	doc.discount_amount = so_tien if viec == "giam" else 0
	mc.bo_mau_thue_mat_hang(doc)
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()

	sau = flt(doc.base_grand_total)
	con_lech, _ = huong_lech(sau, g.get("tong_tien"))
	return {
		"name": doc.name,
		"truoc": truoc,
		"sau": sau,
		"goc": flt(g.get("tong_tien")),
		"so_dong": len(doc.items),
		"khop": 1 if con_lech == "khop" else 0,
		"loi_nhan": (
			"Đã dựng lại %d dòng theo hoá đơn điện tử. Tổng %s đồng, khớp bản gốc."
			% (len(doc.items), _so(sau))
			if con_lech == "khop"
			else "Đã dựng lại %d dòng nhưng tổng %s đồng vẫn chưa khớp bản gốc %s đồng. "
			"Nhờ kế toán xem lại, đừng ghi sổ." % (len(doc.items), _so(sau), _so(g.get("tong_tien")))
		),
	}
