# -*- coding: utf-8 -*-
"""Hàng rào cho thư gửi nhà cung cấp từ đơn mua hàng.

VÌ SAO CÓ TỆP NÀY
--------------------------------------------------------------------
Rà 43 mẩu lệnh chỉ sống trên Desk (27/08/2026) tìm ra bốn mẩu gửi thư và
gộp đơn cho nhà cung cấp, tổng hơn 1.100 dòng. Chúng nằm trong cơ sở dữ
liệu, git không quản, không ca kiểm nào soi, và chúng gửi thư ra người
thật bên ngoài tiệm.

Đếm trên site thật ngày 28/08/2026: 120 lá thư đã gửi trên 97 đơn mua.
Nhìn chung là lành, nhưng có hai vết:

  - 1 lá gửi cho đơn ĐÃ HUỶ (PUR-ORD-2026-00056, gửi Thanh An Eggpack).
    Nhà cung cấp nhận thư rồi giao hàng theo một đơn mình đã huỷ.
  - 5 lá gửi tới địa chỉ không nằm trong hồ sơ nhà cung cấp.

VÌ SAO CHẶN Ở ĐÂY CHỨ KHÔNG SỬA MẨU LỆNH
--------------------------------------------------------------------
Cùng lý do với v328 và v332: mẩu lệnh nằm ngoài mã nguồn nên sửa nó không
có lịch sử, không có ca kiểm. Đặt hàng rào ở tầng dưới thì mọi đường gửi
thư đều chịu chung một luật, kể cả đường mình chưa biết.

RẤT THẬN TRỌNG, VÌ ĐÃ CÓ TIỀN LỆ
--------------------------------------------------------------------
Ngày 16/08/2026 một hook đặt trên "*" xoá trắng ô người gửi của hàng đợi
thư, làm CẢ TIỆM không gửi được lá nào suốt bốn ngày, 117 trên 118 thư
chết. Nên tệp này giữ ba nguyên tắc cứng:

  1. Chỉ động vào thư có chứng từ gốc đúng là Đơn mua hàng. Mọi thư khác
     đi qua không sứt mẻ gì.
  2. Chỉ CHẶN khi kết luận là chắc chắn: đơn đang nháp, hoặc đơn đã huỷ.
     Hai trạng thái này không thể là gửi đúng được.
  3. Tính toán mà lỗi thì CHO THƯ ĐI, chỉ ghi nhật ký. Thà lọt một lá thư
     còn hơn chặn cả hộp thư của tiệm vì một lỗi của mình.

Địa chỉ lạ thì chỉ GHI NHẬT KÝ chứ không chặn: người liên hệ mới bên nhà
cung cấp là chuyện thường ngày, chặn là cản việc thật.
"""

# Ba ket luan. Chuoi rong nghia la khong co gi de noi.
THU_OK = ""
THU_CHAN_NHAP = "nhap"
THU_CHAN_HUY = "huy"


def xet_thu_don_mua(docstatus):
	"""Thư cho đơn mua ở trạng thái này có được đi không. THUẦN.

	`docstatus` của Frappe: 0 nháp, 1 đã duyệt, 2 đã huỷ.

	Chỉ hai trạng thái bị chặn, và cả hai đều không thể là gửi đúng:
	đơn nháp là đơn chưa ai duyệt, đơn huỷ là đơn không còn hiệu lực.
	Trạng thái lạ (None, chuỗi rác) thì CHO ĐI: xem nguyên tắc 3 ở đầu tệp.
	"""
	try:
		d = int(docstatus)
	except (TypeError, ValueError):
		return THU_OK
	if d == 0:
		return THU_CHAN_NHAP
	if d == 2:
		return THU_CHAN_HUY
	return THU_OK


def loi_thu_bi_chan(ket, ten_don, ten_ncc):
	"""Câu tiếng Việt giải thích vì sao thư không đi. THUẦN."""
	if ket == THU_CHAN_NHAP:
		return (
			"Đơn mua %s chưa được duyệt nên chưa gửi cho %s được. Duyệt đơn "
			"xong rồi gửi, vì thư này là lời đặt hàng chính thức."
			% (ten_don, ten_ncc or "nhà cung cấp")
		)
	return (
		"Đơn mua %s đã huỷ nên không gửi cho %s được. Nhà cung cấp nhận thư "
		"này sẽ giao hàng theo một đơn không còn hiệu lực. Cần đặt lại thì "
		"lập đơn mới rồi gửi đơn đó."
		% (ten_don, ten_ncc or "nhà cung cấp")
	)


def dia_chi_la(gui_toi, dia_chi_ho_so):
	"""Những địa chỉ nhận không nằm trong hồ sơ nhà cung cấp. THUẦN.

	So chữ thường và bỏ khoảng trắng hai đầu. Hồ sơ chưa khai địa chỉ nào
	thì trả về rỗng chứ không kêu tất cả: chưa khai là thiếu dữ liệu, không
	phải gửi sai, và kêu cả 100 phần trăm thì không ai đọc nữa.
	"""
	ho_so = set(str(x or "").strip().lower() for x in (dia_chi_ho_so or []) if str(x or "").strip())
	if not ho_so:
		return []
	ra = []
	for x in (gui_toi or []):
		e = str(x or "").strip().lower()
		if e and e not in ho_so:
			ra.append(e)
	return ra


def tach_dia_chi(chuoi):
	"""Cắt ô người nhận thành danh sách địa chỉ. THUẦN."""
	s = str(chuoi or "").replace(";", ",")
	return [x.strip() for x in s.split(",") if x.strip()]


# ------------------------------------------------------- phần cần Frappe

import frappe


DON_MUA = "Purchase Order"


def _dia_chi_cua_ncc(ncc):
	"""Mọi địa chỉ thư đã khai trong hồ sơ liên hệ của nhà cung cấp."""
	if not ncc:
		return []
	lien_he = [
		r[0]
		for r in frappe.db.get_all(
			"Dynamic Link",
			filters={"link_doctype": "Supplier", "link_name": ncc, "parenttype": "Contact"},
			fields=["parent"],
			as_list=True,
			limit_page_length=0,
		)
	]
	ra = []
	if lien_he:
		ra += [
			r[0]
			for r in frappe.db.get_all(
				"Contact Email",
				filters={"parent": ["in", lien_he]},
				fields=["email_id"],
				as_list=True,
				limit_page_length=0,
			)
		]
	chinh = frappe.db.get_value("Supplier", ncc, "email_id")
	if chinh:
		ra.append(chinh)
	return ra


def chan_thu_don_hong(doc, method=None):
	"""Không cho thư đi khi đơn mua đang nháp hoặc đã huỷ.

	Gắn ở `before_insert` của Communication. Đọc kỹ ba nguyên tắc ở đầu tệp
	trước khi sửa hàm này.
	"""
	# Nguyen tac 1: chi dong vao thu cua don mua hang, gui DI.
	if str(doc.get("reference_doctype") or "") != DON_MUA:
		return
	if str(doc.get("sent_or_received") or "") != "Sent":
		return
	ten_don = str(doc.get("reference_name") or "")
	if not ten_don:
		return

	# Nguyen tac 3: tinh toan hong thi cho thu di, chi ghi nhat ky.
	try:
		don = frappe.db.get_value(
			DON_MUA, ten_don, ["docstatus", "supplier", "supplier_name"], as_dict=True
		)
	except Exception:
		return
	if not don:
		return

	# Nguyen tac 2: chi chan khi ket luan chac chan.
	ket = xet_thu_don_mua(don.get("docstatus"))
	if ket:
		frappe.throw(
			loi_thu_bi_chan(ket, ten_don, don.get("supplier_name")),
			title="Chưa gửi thư này được",
		)

	# Dia chi la thi CHI GHI NHAT KY, khong chan: nguoi lien he moi ben nha
	# cung cap la chuyen thuong ngay.
	try:
		la = dia_chi_la(
			tach_dia_chi(doc.get("recipients")), _dia_chi_cua_ncc(don.get("supplier"))
		)
		if la:
			frappe.log_error(
				"Đơn mua %s gửi tới %s, địa chỉ này chưa có trong hồ sơ liên hệ của "
				"%s. Thư vẫn đi. Nếu đúng là người liên hệ mới thì khai vào hồ sơ "
				"nhà cung cấp để lần sau khỏi bị nêu."
				% (ten_don, ", ".join(la), don.get("supplier_name") or don.get("supplier")),
				"gac_thu_ncc: dia chi ngoai ho so",
			)
	except Exception:
		pass


@frappe.whitelist()
def soat_thu_ncc(so_ngay=180):
	"""CHỈ ĐỌC: liệt kê thư gửi nhà cung cấp có dấu hiệu sai.

	Hai dấu hiệu: gửi cho đơn nháp hoặc đơn đã huỷ, và gửi tới địa chỉ ngoài
	hồ sơ. Chỉ liệt kê, không sửa gì.
	"""
	if not frappe.has_permission(DON_MUA, "read"):
		frappe.throw("Cần quyền đọc Đơn mua hàng mới xem được bảng rà này.")
	from frappe.utils import add_days, nowdate

	tu = add_days(nowdate(), -int(so_ngay or 180))
	thu = frappe.db.get_all(
		"Communication",
		filters={"reference_doctype": DON_MUA, "creation": [">=", tu]},
		fields=["name", "reference_name", "recipients", "creation", "sent_or_received"],
		order_by="creation desc",
		limit_page_length=0,
	)
	if not thu:
		return {"trang_thai": [], "dia_chi": [], "so_thu": 0}

	ten_don = sorted({t["reference_name"] for t in thu if t.get("reference_name")})
	don = {
		r["name"]: r
		for r in frappe.db.get_all(
			DON_MUA,
			filters={"name": ["in", ten_don]},
			fields=["name", "docstatus", "supplier", "supplier_name"],
			limit_page_length=0,
		)
	}
	kho_dia_chi = {}
	xau_tt, xau_dc = [], []
	for t in thu:
		d = don.get(t.get("reference_name"))
		if not d:
			continue
		ket = xet_thu_don_mua(d.get("docstatus"))
		if ket:
			xau_tt.append({
				"thu": t["name"],
				"don": t["reference_name"],
				"ncc": d.get("supplier_name") or d.get("supplier"),
				"gui_toi": t.get("recipients") or "",
				"ngay": str(t.get("creation") or "")[:16],
				"vi_sao": "đơn còn nháp" if ket == THU_CHAN_NHAP else "đơn đã huỷ",
			})
		ncc = d.get("supplier")
		if ncc not in kho_dia_chi:
			kho_dia_chi[ncc] = _dia_chi_cua_ncc(ncc)
		la = dia_chi_la(tach_dia_chi(t.get("recipients")), kho_dia_chi[ncc])
		if la:
			xau_dc.append({
				"thu": t["name"],
				"don": t["reference_name"],
				"ncc": d.get("supplier_name") or d.get("supplier"),
				"gui_toi": ", ".join(la),
				"ngay": str(t.get("creation") or "")[:16],
			})
	return {
		"trang_thai": xau_tt,
		"dia_chi": xau_dc,
		"so_thu": len(thu),
		"so_don": len(ten_don),
	}
