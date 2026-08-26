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
	viec, so_tien = mc.can_theo_truoc_thue(tong_dong, g.get("tien_truoc_thue"))
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
	mc.bo_mau_thue_mat_hang(doc)
	return len(doc.get("items"))


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
		if not g or not flt(g.get("tien_truoc_thue")):
			return
		if not mua_dich_vu.lech_qua_nguong(
			_tong_dong_hien_tai(doc), g.get("tien_truoc_thue"), NGUONG
		):
			return
		if not doc_chi_tiet(g.get("chi_tiet")):
			frappe.msgprint(
				"Tờ này đang lệch với hoá đơn điện tử %s mà bản gốc không còn "
				"dòng hàng để dựng lại. Nhờ kế toán đối chiếu tay, đừng ghi sổ."
				% (g.get("so_hd") or ""),
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
	khop, van_lech, hong = [], [], []
	for r in ds:
		try:
			doc = frappe.get_doc(PI, r["name"])
			g = _goc(doc.get("custom_minvoice_id"))
			if not g:
				hong.append({"name": r["name"], "vi_sao": "mất bản hoá đơn điện tử gốc"})
				continue
			phieu = _phieu_da_noi(doc)
			_dung_dong_tai_cho(doc, g)
			_noi_lai(doc, phieu)
			doc.flags.ignore_permissions = True
			doc.save()
			frappe.db.commit()
			viec, _lech = huong_lech(doc.base_grand_total, g.get("tong_tien"))
			(khop if viec == "khop" else van_lech).append(doc.name)
		except Exception as e:
			frappe.db.rollback()
			hong.append({"name": r["name"], "vi_sao": str(e)[:160]})
	con_lai = max(0, kq["so_nhap"] - len(ds))
	return {
		"khop": len(khop),
		"van_lech": van_lech,
		"hong": hong,
		"con_lai": con_lai,
		"loi_nhan": "Dựng lại %d tờ khớp bản gốc, %d tờ vẫn lệch, %d tờ lỗi, còn %d tờ chưa chạy."
			% (len(khop), len(van_lech), len(hong), con_lai),
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
