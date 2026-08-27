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

Tệp này bù hai chỗ đó, và từ v319 đi xa hơn theo lệnh của anh Việt cùng
ngày: "phải đồng bộ giữa cả app và cả desktop về tất cả các nút tính năng".
Bản v318 mới chỉ CẢNH BÁO lúc lưu rồi dặn người ta đừng bấm nút bên màn
quản trị - vá bằng lời dặn, không phải vá hệ thống. Nay luật nằm ở hook
`dong_bo_luc_luu`, chạy trên MỌI lần lưu bất kể bấm từ đâu: dòng hàng lệch
khỏi bản gốc là máy dựng lại và giữ liên kết phiếu nhập. Hai nơi bấm, một
bản chất.

Đếm ngày 26/08/2026: 3.077 hoá đơn mua sinh từ hoá đơn điện tử, 338 tờ còn
nháp đang lệch tổng, và 3 tờ ĐÃ GHI SỔ mà lệch. Anh Việt cấp toàn quyền xử
cả hai nhóm trong cùng ngày - `dung_lai_tat_ca` cho tờ nháp,
`sua_to_da_ghi_so` cho tờ đã vào sổ.
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


def muc_tieu_truoc_thue(g):
	"""Tiền hàng trước thuế mà tờ chứng từ PHẢI ra bằng. THUẦN.

	VÌ SAO KHÔNG DÙNG THẲNG Ô `tien_truoc_thue` - sự cố 27/08/2026
	--------------------------------------------------------------------
	Bản v319 neo vào ô đó và làm hỏng 5 tờ thật ngay trong lượt chạy đầu:

	  * HDM-26-08-00096 Nhà Sen: bản gốc ghi tổng 3.650.000 nhưng ô
	    `tien_truoc_thue` để 0 (nhà cung cấp không khai tách). Máy hiểu là
	    dòng hàng THỪA 3.650.000 nên đặt giảm giá đúng bằng cả tờ, tổng về
	    0 đồng. Bốn tờ bị về 0 đều đúng kiểu này.
	  * HDM-26-08-00124 Avanti: ô đó ghi 26.953.500 nhưng dòng hàng dựng ra
	    tổng 31.453.500, lệch 4.500.000, thành ra tờ phình lên.

	Con số ĐÁNG TIN duy nhất là `tong_tien`: đó là số nhà cung cấp đã gửi cơ
	quan thuế, và cũng chính là số mà cửa chặn ghi sổ soi. Nên lấy tổng trừ
	thuế ra tiền hàng, chỉ khi tổng không có mới đành quay về ô cũ.
	"""
	tong = flt(g.get("tong_tien"))
	if tong:
		return tong - flt(g.get("tien_thue"))
	return flt(g.get("tien_truoc_thue"))


def _quyen_manh():
	if not {"System Manager", "Accounts Manager"} & set(frappe.get_roles()):
		frappe.throw("Việc này chỉ dành cho kế toán trưởng và quản lý hệ thống.")


def _dung_dong_tai_cho(doc, g):
	"""Dựng lại bảng dòng hàng NGAY TRÊN doc theo hoá đơn điện tử. Không lưu.

	Đây là MỘT đường dựng duy nhất, dùng chung cho nút trên app, cho hook
	chạy lúc lưu từ màn quản trị, cho lượt sửa hàng loạt và cho việc sửa tờ
	đã ghi sổ. Anh Việt chốt 26/08/2026: một cái nút mà hai nơi bấm ra hai
	bản chất là cấm, nên bản chất phải nằm ở đây, tầng dưới cùng, không nằm
	trong từng nút.

	Dựng đủ danh sách dòng mới TRƯỚC rồi mới thay vào doc, để lỡ giữa chừng
	có lỗi thì doc còn nguyên, không bao giờ lưu một tờ cụt dòng.

	NEO VÀO ĐÂU: xem `muc_tieu_truoc_thue`. Bản v319 neo vào ô
	`tien_truoc_thue` và việc đó đã làm hỏng 5 tờ thật, đọc mục đó trước khi
	định đổi lại.
	"""
	dong_goc = doc_chi_tiet(g.get("chi_tiet"))
	if not dong_goc:
		frappe.throw(
			"Bản hoá đơn điện tử %s không còn dòng hàng nào để dựng lại."
			% (g.get("so_hd") or "")
		)
	from vagabond import minvoice_chung_tu as mc

	goc_mst = (g.get("mst_doi_tac") or "").split("-")[0]
	tk = None
	for d in doc.get("items") or []:
		if d.get("expense_account"):
			tk = d.expense_account
			break
	moi = []
	for it in dong_goc:
		x = mc.dong_tu_hoa_don(it)
		ma, uom, he_so = mc._tra_ma_hang(x, goc_mst, doc.supplier)
		moi.append(mc._dong_pi(x, tk, ma, uom, he_so))
	tong_dong = sum(flt(d.get("qty")) * flt(d.get("rate")) for d in moi)
	viec, so_tien = mc.can_theo_truoc_thue(tong_dong, muc_tieu_truoc_thue(g))
	if viec == "phi":
		moi.append(mc._dong_pi({
			"ma": "", "ten": "Phí khác theo hoá đơn", "dvt": None,
			"sl": 1, "gia": so_tien, "tien": so_tien,
		}, tk))
	doc.set("items", [])
	tt = doc.get("cost_center")
	for d in moi:
		if tt:
			d["cost_center"] = tt
		doc.append("items", d)
	doc.apply_discount_on = "Net Total"
	doc.discount_amount = so_tien if viec == "giam" else 0
	_dung_thue_tai_cho(doc, g)
	mc.bo_mau_thue_mat_hang(doc)
	return len(doc.get("items"))


def _tong_thue_tren_phieu(doc):
	return sum(flt(t.get("tax_amount")) for t in doc.get("taxes") or [])


def _tk_thue_vao(doc):
	"""Tài khoản thuế GTGT được khấu trừ của công ty. None nếu không có."""
	for t in doc.get("taxes") or []:
		tk = (t.get("account_head") or "").strip()
		if tk.startswith("1331"):
			return tk
	try:
		return frappe.db.get_value(
			"Account", {"company": doc.get("company"), "name": ["like", "1331 -%"]}, "name"
		)
	except Exception:
		return None


def _dung_thue_tai_cho(doc, g):
	"""Dựng lại bảng thuế theo đúng bản hoá đơn điện tử. Không lưu.

	VÌ SAO PHẢI DỰNG CẢ THUẾ - ca thật 27/08/2026
	--------------------------------------------------------------------
	Nhóm hoá đơn LARAFARM đều lệch đúng 51.200 đồng. Bản gốc ghi thuế 0,
	dòng hàng dựng ra đúng 790.000, nhưng trên chứng từ còn sót hai dòng
	thuế "On Net Total" 1331 và 33311, mỗi dòng 25.600, do mẫu thuế của
	danh mục Món áp vào lúc tờ được sinh ra trước bản v315. Dựng lại mỗi
	dòng hàng thì tổng vẫn lệch, vì phần lệch nằm ở bảng thuế.

	Số thuế trên hoá đơn điện tử là số nhà cung cấp đã gửi cơ quan thuế.
	Dựng lại theo hoá đơn điện tử thì phải dựng cả phần đó, nếu không thì
	chỉ dựng được một nửa tờ.
	"""
	tien_thue = flt(g.get("tien_thue"))
	tk = _tk_thue_vao(doc)
	tt = doc.get("cost_center")
	doc.set("taxes", [])
	if tk and tien_thue:
		doc.append("taxes", {
			"charge_type": "Actual", "account_head": tk,
			"description": "Thuế GTGT được khấu trừ",
			"tax_amount": tien_thue,
			"category": "Total", "add_deduct_tax": "Add",
			"cost_center": tt,
		})
	doc.taxes_and_charges = None
	return tien_thue


def du_kien_tong(doc, g):
	"""Tổng tiền tờ này SẼ thành bao nhiêu nếu dựng lại. Không đụng doc.

	Tính trước rồi mới quyết có dựng hay không. Nhờ vậy không bao giờ có
	chuyện dựng dở rồi lưu ra một tờ tệ hơn lúc chưa dựng.
	"""
	dong_goc = doc_chi_tiet(g.get("chi_tiet"))
	if not dong_goc:
		return None
	try:
		from vagabond import minvoice_chung_tu as mc

		goc_mst = (g.get("mst_doi_tac") or "").split("-")[0]
		tong_dong = 0.0
		for it in dong_goc:
			x = mc.dong_tu_hoa_don(it)
			tong_dong += flt(x.get("sl")) * flt(x.get("gia"))
		viec, so_tien = mc.can_theo_truoc_thue(tong_dong, muc_tieu_truoc_thue(g))
		net = tong_dong + (so_tien if viec == "phi" else 0) - (so_tien if viec == "giam" else 0)
		# Thuế lấy theo BẢN GỐC, không lấy theo bảng thuế đang có trên phiếu:
		# `_dung_thue_tai_cho` sẽ dựng lại bảng đó theo đúng bản gốc.
		return net + flt(g.get("tien_thue"))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dung_lai_hddt: du kien tong")
		return None


def dung_lai_co_loi_khong(doc, g):
	"""Dựng lại tờ này có làm nó ĐÚNG HƠN không. Trả (nen_dung, ly_do).

	Đây là chốt chặn quan trọng nhất của tệp, thêm sau sự cố 27/08/2026 do
	chính bản v319 gây ra: đừng bao giờ ghi đè một tờ bằng thứ mình chưa
	kiểm là đúng.
	"""
	goc = flt(g.get("tong_tien"))
	if not goc:
		return False, "bản hoá đơn điện tử không ghi tổng tiền"
	du_kien = du_kien_tong(doc, g)
	if du_kien is None:
		return False, "không dựng thử được dòng hàng từ bản gốc"
	if mua_dich_vu.lech_qua_nguong(du_kien, goc, NGUONG):
		return False, (
			"dựng lại sẽ ra %s đồng, vẫn chưa khớp bản gốc %s đồng"
			% (_so(du_kien), _so(goc))
		)
	return True, ""


def _phieu_da_noi(doc):
	return sorted({
		(d.get("purchase_receipt") or "").strip()
		for d in doc.get("items") or []
	} - {""})


def _noi_lai(doc, phieu):
	"""Gắn lại các phiếu nhập đã nối trước đó, tốt nhất có thể.

	Gắn không được thì thôi chứ không chặn: số tiền đúng quan trọng hơn
	liên kết, và liên kết luôn nối lại tay được ở màn Đối chiếu.
	"""
	if not phieu:
		return []
	try:
		from vagabond import doi_chieu_mua

		return doi_chieu_mua._noi(doc, list(phieu))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dung_lai_hddt: noi lai phieu nhap")
		return ["Chưa gắn lại được phiếu nhập, vào màn Đối chiếu nối tay."]


def _tong_dong_hien_tai(doc):
	"""Tiền hàng trước thuế theo dòng đang có trên doc, trừ giảm giá."""
	tong = 0.0
	for d in doc.get("items") or []:
		tong += flt(d.get("qty")) * flt(d.get("rate"))
	return tong - flt(doc.get("discount_amount"))


def dong_bo_luc_luu(doc, method=None):
	"""Hook chạy MỌI lần lưu hoá đơn mua, bất kể lưu từ nút nào, màn nào.

	Anh Việt 26/08/2026: hai nút cùng tên mà hai bản chất là quá nguy hiểm,
	không được xử lý bằng lời dặn "chỉ bấm bên app". Nên luật đặt ở đây,
	tầng dưới cùng của việc lưu chứng từ: tờ sinh từ hoá đơn điện tử mà
	dòng hàng bị đè lệch đi - dù do nút "Nối phiếu nhập kho" bên màn quản
	trị, nút "Lấy mặt hàng từ", hay tay ai gõ - thì máy dựng lại đúng bản
	gốc ngay trong lần lưu đó và GIỮ LẠI liên kết phiếu nhập vừa chọn.
	Từ giờ bấm ở đâu cũng ra một kết quả.

	Đặt ở before_validate chứ không validate: ERPNext tính lại tổng tiền
	SAU before_validate, đổi dòng ở validate là tổng không được tính lại -
	cùng lý do với hook gom dòng của hoá đơn dịch vụ ngay phía trên.

	Mọi lỗi ở đây chỉ được ghi nhật ký, không bao giờ làm rớt việc lưu.
	"""
	try:
		if cint(doc.get("docstatus")) != 0:
			return
		g = _goc(doc.get("custom_minvoice_id"))
		if not g:
			return
		muc_tieu = muc_tieu_truoc_thue(g)
		if not muc_tieu:
			return
		if not mua_dich_vu.lech_qua_nguong(_tong_dong_hien_tai(doc), muc_tieu, NGUONG):
			return
		nen, vi_sao = dung_lai_co_loi_khong(doc, g)
		if not nen:
			# KHÔNG ĐỤNG VÀO TỜ. Bài học 27/08/2026: bản v319 cứ dựng bừa rồi
			# lưu, làm bốn tờ về 0 đồng và một tờ phình thêm 4,5 triệu. Chưa
			# chắc đúng thì để yên và nói cho người ta biết.
			frappe.msgprint(
				"Tờ này đang lệch với hoá đơn điện tử %s/%s và hệ thống chưa dựng "
				"lại được: %s. Hệ thống giữ nguyên tờ như đang có, nhờ kế toán đối "
				"chiếu tay và đừng ghi sổ khi còn lệch."
				% (g.get("ky_hieu") or "", g.get("so_hd") or "", vi_sao),
				title="Lệch so với hoá đơn điện tử", indicator="red",
			)
			return
		phieu = _phieu_da_noi(doc)
		_dung_dong_tai_cho(doc, g)
		loi = _noi_lai(doc, phieu)
		cau = (
			"Dòng hàng của tờ này vừa bị sửa lệch khỏi hoá đơn điện tử %s/%s, "
			"là số nhà cung cấp đã gửi cơ quan thuế, nên hệ thống dựng lại "
			"đúng bản gốc trong lần lưu này."
			% (g.get("ky_hieu") or "", g.get("so_hd") or "")
		)
		if phieu and not loi:
			cau += " Phiếu nhập %s vẫn được nối như vừa chọn." % ", ".join(phieu)
		elif loi:
			cau += " Riêng phần nối phiếu nhập chưa xong: " + " ".join(loi)
		frappe.msgprint(cau, title="Giữ đúng số hoá đơn điện tử", indicator="orange")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dung_lai_hddt: dong bo luc luu")


def tk_theo_mon(doc, method=None):
	"""Hook validate: tờ máy dựng thì tài khoản chi phí đi theo khai báo Món.

	Ca thật 26/08/2026: 12 dòng hoá đơn tiếp khách Avanti rơi cả vào 632
	giá vốn hàng bán, trong khi chị Dung chốt tiếp khách ăn uống đi 64183.
	Khai tài khoản một lần trên danh mục Món, mọi tờ sau tự vào đúng chỗ.

	Chỉ đụng dòng DỊCH VỤ (món không quản kho) và chưa nối phiếu nhập, để
	không dẫm lên luật tài khoản chờ 3311 của hàng nhập kho - vụ 21/08 chết
	nhập kho vẫn còn đó, đọc đầu tệp ke_toan_mua.py trước khi nới rộng.
	"""
	try:
		if cint(doc.get("docstatus")) != 0:
			return
		if not (doc.get("custom_minvoice_id") or "").strip():
			return
		for d in doc.get("items") or []:
			ma = (d.get("item_code") or "").strip()
			if not ma or (d.get("purchase_receipt") or "").strip():
				continue
			if cint(frappe.db.get_value("Item", ma, "is_stock_item")):
				continue
			tk = frappe.db.get_value(
				"Item Default", {"parent": ma, "company": doc.company}, "expense_account"
			)
			if tk and d.get("expense_account") != tk:
				d.expense_account = tk
	except Exception:
		frappe.log_error(frappe.get_traceback(), "dung_lai_hddt: tk theo mon")


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

	Phiếu đã ghi sổ thì TỪ CHỐI - tờ đã vào sổ đi đường `sua_to_da_ghi_so`,
	có kiểm phiếu chi và đi qua đủ cửa khoá sổ.

    Tệp này gọi các hàm nội bộ của `minvoice_chung_tu` để tra mã hàng và
    dựng dòng, cốt để hai đường dựng chứng từ không bao giờ ra hai kết quả
    khác nhau. Đổi chữ ký các hàm đó thì ca kiểm `thu_dung_lai_hddt` đỏ
    ngay, đừng bỏ qua.
	"""
	_kiem_quyen()
	doc = frappe.get_doc(PI, name)
	if cint(doc.docstatus) != 0:
		frappe.throw(
			"Hoá đơn %s đã ghi sổ rồi, không dựng lại kiểu này được. Tờ đã "
			"ghi sổ mà lệch thì báo anh Việt và chị Dung." % name
		)
	g = _goc(doc.get("custom_minvoice_id"))
	if not g:
		frappe.throw(
			"Hoá đơn %s không phải sinh từ hoá đơn điện tử nên không có bản gốc "
			"để dựng lại." % name
		)
	nen, vi_sao = dung_lai_co_loi_khong(doc, g)
	if not nen:
		frappe.throw(
			"Chưa dựng lại được tờ %s: %s. Hệ thống không ghi đè khi chưa chắc "
			"ra đúng số. Nhờ kế toán đối chiếu tay với bản hoá đơn điện tử."
			% (name, vi_sao)
		)
	phieu = _phieu_da_noi(doc)
	truoc = flt(doc.base_grand_total)
	_dung_dong_tai_cho(doc, g)
	loi_noi = _noi_lai(doc, phieu)
	doc.flags.ignore_permissions = True
	doc.save()
	frappe.db.commit()

	sau = flt(doc.base_grand_total)
	con_lech, _ = huong_lech(sau, g.get("tong_tien"))
	loi_nhan = (
		"Đã dựng lại %d dòng theo hoá đơn điện tử. Tổng %s đồng, khớp bản gốc."
		% (len(doc.items), _so(sau))
		if con_lech == "khop"
		else "Đã dựng lại %d dòng nhưng tổng %s đồng vẫn chưa khớp bản gốc %s đồng. "
		"Nhờ kế toán xem lại, đừng ghi sổ." % (len(doc.items), _so(sau), _so(g.get("tong_tien")))
	)
	if loi_noi:
		loi_nhan += " Phần nối phiếu nhập chưa xong: " + " ".join(loi_noi)
	return {
		"name": doc.name,
		"truoc": truoc,
		"sau": sau,
		"goc": flt(g.get("tong_tien")),
		"so_dong": len(doc.items),
		"khop": 1 if con_lech == "khop" else 0,
		"loi_nhan": loi_nhan,
	}


@frappe.whitelist()
def dung_lai_tat_ca(gioi_han=40):
	"""Dựng lại HÀNG LOẠT các tờ nháp đang lệch với hoá đơn điện tử gốc.

	Anh Việt cấp quyền 26/08/2026: 338 tờ nháp lệch là hậu quả của lỗi hệ
	thống, không được bắt Uyên ngồi bấm 338 lần. Chạy theo lô nhỏ, mỗi tờ
	tự chịu lỗi của mình - một tờ hỏng không được chặn các tờ còn lại.
	"""
	_quyen_manh()
	kq = soat(gioi_han=100000)
	ds = kq["nhap"][: max(1, cint(gioi_han) or 40)]
	khop, bo_qua, hong = [], [], []
	for r in ds:
		try:
			doc = frappe.get_doc(PI, r["name"])
			g = _goc(doc.get("custom_minvoice_id"))
			if not g:
				hong.append({"name": r["name"], "vi_sao": "mất bản hoá đơn điện tử gốc"})
				continue
			# Dựng thử TRƯỚC. Không chắc ra đúng thì bỏ qua, tuyệt đối không
			# ghi đè - đây là chốt thêm sau sự cố 27/08/2026 do bản v319 gây.
			nen, vi_sao = dung_lai_co_loi_khong(doc, g)
			if not nen:
				bo_qua.append({"name": r["name"], "vi_sao": vi_sao})
				continue
			phieu = _phieu_da_noi(doc)
			_dung_dong_tai_cho(doc, g)
			_noi_lai(doc, phieu)
			doc.flags.ignore_permissions = True
			doc.save()
			viec, _lech = huong_lech(doc.base_grand_total, g.get("tong_tien"))
			if viec != "khop":
				# Lưu xong mà vẫn lệch thì trả tờ về nguyên trạng.
				frappe.db.rollback()
				bo_qua.append({"name": r["name"], "vi_sao": "lưu xong vẫn lệch, đã trả về nguyên trạng"})
				continue
			frappe.db.commit()
			khop.append(doc.name)
		except Exception as e:
			frappe.db.rollback()
			hong.append({"name": r["name"], "vi_sao": str(e)[:160]})
	con_lai = max(0, kq["so_nhap"] - len(ds))
	return {
		"khop": len(khop),
		"bo_qua": bo_qua,
		"hong": hong,
		"con_lai": con_lai,
		"loi_nhan": "Dựng lại %d tờ khớp bản gốc, %d tờ để nguyên vì chưa chắc đúng, "
			"%d tờ lỗi, còn %d tờ chưa chạy."
			% (len(khop), len(bo_qua), len(hong), con_lai),
	}


@frappe.whitelist()
def sua_to_da_ghi_so(name):
	"""Sửa một tờ ĐÃ GHI SỔ đang lệch: huỷ, lập bản sửa đổi đúng theo hoá
	đơn điện tử, ghi sổ lại.

	Anh Việt cấp toàn quyền 26/08/2026 cho các tờ đã ghi sổ mà lệch. Vẫn
	giữ hai chốt, cố ý:

	  * Tờ đã có phiếu chi trỏ vào thì TỪ CHỐI, kể tên phiếu chi ra. Tự gỡ
	    phiếu chi là đụng vào tiền đã trả, việc đó của kế toán.
	  * Mọi cửa khoá sổ vẫn chạy như thường. Kỳ đã khoá thì lệnh này tự
	    thất bại chứ không lách.
	"""
	_quyen_manh()
	doc = frappe.get_doc(PI, name)
	if cint(doc.docstatus) != 1:
		frappe.throw("Tờ %s không ở trạng thái đã ghi sổ." % name)
	g = _goc(doc.get("custom_minvoice_id"))
	if not g:
		frappe.throw("Tờ %s không sinh từ hoá đơn điện tử nên không có bản gốc." % name)
	tien = frappe.get_all(
		"Payment Entry Reference",
		filters={"reference_doctype": PI, "reference_name": name, "docstatus": 1},
		fields=["parent"],
		limit_page_length=20,
	)
	if tien:
		frappe.throw(
			"Tờ %s đã có phiếu chi %s trỏ vào. Phải gỡ phiếu chi trước rồi mới "
			"sửa được, việc đó để kế toán quyết."
			% (name, ", ".join(sorted({t["parent"] for t in tien})))
		)
	nen, vi_sao = dung_lai_co_loi_khong(doc, g)
	if not nen:
		frappe.throw(
			"Chưa sửa được tờ %s: %s. Không huỷ một tờ đã ghi sổ khi chưa chắc "
			"dựng lại ra đúng số." % (name, vi_sao)
		)
	truoc = flt(doc.base_grand_total)
	doc.flags.ignore_permissions = True
	doc.cancel()

	moi = frappe.copy_doc(doc)
	moi.amended_from = name
	moi.docstatus = 0
	_dung_dong_tai_cho(moi, g)
	moi.flags.ignore_permissions = True
	moi.insert(ignore_permissions=True)
	moi.submit()
	frappe.db.commit()
	return {
		"cu": name,
		"moi": moi.name,
		"truoc": truoc,
		"sau": flt(moi.base_grand_total),
		"goc": flt(g.get("tong_tien")),
		"loi_nhan": "Đã huỷ %s, ghi sổ bản sửa %s, tổng %s đồng khớp hoá đơn điện tử."
			% (name, moi.name, _so(moi.base_grand_total)),
	}
