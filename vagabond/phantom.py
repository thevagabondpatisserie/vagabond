# -*- coding: utf-8 -*-
"""Chuyển bán thành phẩm cấp 1 thành Phantom, chạy thử trước rồi mới ghi.

Bài anh Việt giao 21/08/2026, sau khi thấy 139 mã BTP vẫn ghi sổ kho dù
chưa ai làm lệnh sản xuất nào cho chúng.

Bốn cấp của xưởng, đọc từ dưới lên
----------------------------------
    NVL                       nguyên vật liệu mua vào
    BTP thành phần   (139)    trộn ra rồi dùng ngay trong ngày
    Ruột bánh (C1)   (16)     giữ tồn, có ngày dùng, có kiểm
    Bánh khuôn (C2)  (23)     giữ tồn, có ngày dùng, có kiểm
    Thành phẩm       (77)     bán ra

Chỉ CẤP BTP thành phần là thứ không đáng ghi sổ: nó sinh ra và biến mất
trong cùng một ca bếp, ghi vào kho thì được một con số không ai dùng và
một đống bút toán phải đối chiếu. Đó chính là nghĩa của "Phantom": có
công thức, không có kho.

Hai cấp C1 và C2 thì NGƯỢC LẠI, phải giữ tồn. Bánh khuôn nướng hôm nay
để mai ráp mới là chuyện thường ngày ở đây, không theo tồn hai cấp đó là
mất dấu hàng thật đang nằm trong tủ.

Ba việc phải làm cùng nhau, thiếu một là hỏng
---------------------------------------------
1. Mã BTP: `is_stock_item = 0`.

   ERPNext CHẶN đổi ô này khi mã hàng còn BOM đã ghi sổ trỏ tới, dù chưa
   hề có bút toán kho nào. Nó đếm BOM là "giao dịch". Nên ở đây ghi
   thẳng xuống bảng, KHÔNG đi qua `doc.save()`.

   Ghi thẳng xuống bảng là việc nguy hiểm, và nó chỉ an toàn vì hàm này
   tự dựng lấy hàng rào mà ERPNext đáng ra dựng hộ: còn tồn kho thì
   dừng, còn lệnh sản xuất treo thì dừng. Xem `_hang_rao`.

2. Dòng BTP trong BOM cha: `do_not_explode = 0` và phải có `bom_no`.

   Đây là chỗ dễ tưởng đã xong mà chưa xong. Chiều 21/08 đọc số thật:
   371 dòng BTP nằm trong các BOM đang chạy, thì 300 dòng có
   `do_not_explode = 1` VÀ `bom_no` để trống. Bỏ cờ mà không điền
   `bom_no` thì chẳng có gì để nổ xuống, lệnh sản xuất sẽ đòi đúng cái
   mã vừa bị bỏ tồn kho, và bếp đứng.

3. Dòng C1 và C2 trong BOM cha: `do_not_explode = 1`.

   Bật nổ nhiều cấp mà không chặn ở đây thì ERPNext nổ xuyên qua cả C1
   lẫn C2 xuống tận NVL, và hai cấp đang theo tồn biến mất khỏi lệnh sản
   xuất. Hôm nay cả 39 dòng đều đã đúng, hàm vẫn kiểm lại từng dòng chứ
   không tin.

Rồi phải DỰNG LẠI bảng nổ (`BOM Explosion Item`) của từng BOM cha, vì
ERPNext đọc bảng đó chứ không tính lại lúc chạy.

Chạy thử là mặc định
--------------------
`chuyen()` không truyền gì thì CHỈ ĐỌC và trả về kế hoạch. Phải gọi rõ
`chay_that=1` mới ghi. Bếp đang sản xuất, và một lần đổi hàng loạt sai ở
đây thì không có nút hoàn tác.
"""

# ------------------------------------------------------------ phần thuần

CHANG_BTP = "BTP thành phần"
CHANG_C1 = "Ruột bánh (C1)"
CHANG_C2 = "Bánh khuôn (C2)"
CHANG_TP = "Thành phẩm"

# Hai chặng phải DỪNG nổ: hàng lấy từ kho chứ không xuất thẳng nguyên liệu.
CHANG_DUNG_NO = (CHANG_C1, CHANG_C2)

# Lệnh sản xuất ở các trạng thái này coi như đã xong, không chặn chuyển đổi.
WO_DA_XONG = ("Completed", "Stopped", "Closed", "Cancelled")

# Việc phải làm với một dòng con trong BOM cha.
BAT_NO = "bat_no"
CHAN_NO = "chan_no"
KHONG_DUNG = ""


def viec_cua_dong(chang_con, do_not_explode, co_bom_no):
	"""Dòng con thuộc chặng này, đang mang cờ này, thì phải sửa gì. THUẦN.

	Trả về (việc, vì_sao). Việc rỗng nghĩa là dòng đã đúng, đừng đụng vào.

	Không đụng tới dòng nguyên vật liệu hay chặng lạ: nguyên vật liệu
	không có BOM nên cờ nổ vô nghĩa, còn chặng lạ là thứ hàm này chưa
	biết, mà đoán bừa trên 371 dòng thì hỏng cả xưởng.
	"""
	if chang_con == CHANG_BTP:
		if not co_bom_no:
			return BAT_NO, "chưa trỏ công thức con nên không có gì để nổ xuống"
		if do_not_explode:
			return BAT_NO, "đang chặn nổ nên lệnh sẽ đòi chính mã Phantom"
		return KHONG_DUNG, ""
	if chang_con in CHANG_DUNG_NO:
		if not do_not_explode:
			return CHAN_NO, "đang để nổ nên lệnh sẽ xuyên qua cấp giữ tồn"
		return KHONG_DUNG, ""
	return KHONG_DUNG, ""


def wo_con_treo(trang_thai, docstatus):
	"""Lệnh sản xuất này còn treo không. THUẦN."""
	if int(docstatus or 0) >= 2:
		return False
	return (trang_thai or "").strip() not in WO_DA_XONG


def cau_chan(so_ton, so_lenh):
	"""Câu từ chối, phải nói rõ làm gì tiếp chứ không chỉ nói không. QT-24."""
	phan = []
	if so_lenh:
		phan.append(
			"còn %d lệnh sản xuất treo trên các mã này" % so_lenh
		)
	if so_ton:
		phan.append("còn %d mã đang có tồn kho khác 0" % so_ton)
	if not phan:
		return ""
	return (
		"Chưa chuyển Phantom được vì " + " và ".join(phan) + ". "
		"Anh chị vào màn Dọn chứng từ thử đóng nốt các lệnh đó, và xuất "
		"hết hoặc kiểm kê về 0 phần tồn còn lại, rồi chạy lại. Bỏ qua bước "
		"này thì số tồn sẽ nằm lại trong kho mà không màn nào đọc ra nữa."
	)


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, flt


def _chan():
	if not {"System Manager", "Giám đốc", "AP Giám đốc"} & set(frappe.get_roles()):
		frappe.throw(
			"Chỉ quản lý hệ thống hoặc giám đốc mới chạy được việc này. "
			"Đây là thao tác đổi cấu hình kho của cả trăm mã hàng."
		)


def _bom_dang_chay():
	"""Các BOM đã ghi sổ và đang hoạt động, kèm chặng của chúng."""
	return frappe.get_all(
		"BOM",
		filters={"docstatus": 1, "is_active": 1},
		fields=["name", "item", "item_name", "custom_chang", "is_default"],
		limit_page_length=0,
	)


def _ma_theo_chang(ds_bom=None):
	"""Chặng nào gồm những mã hàng nào."""
	ra = {}
	for b in ds_bom if ds_bom is not None else _bom_dang_chay():
		ra.setdefault(b.custom_chang or "", set()).add(b.item)
	return ra


def _bom_cua_ma(ds_bom):
	"""Mã hàng nào dùng BOM nào. Ưu tiên bản mặc định."""
	ra = {}
	for b in ds_bom:
		if b.item not in ra or cint(b.is_default):
			ra[b.item] = b.name
	return ra


# ------------------------------------------- hàng rào trước khi ghi thật


def _lenh_treo(cac_ma):
	"""Lệnh sản xuất còn treo của các mã này."""
	if not cac_ma:
		return []
	ds = frappe.get_all(
		"Work Order",
		filters={"production_item": ["in", list(cac_ma)], "docstatus": ["<", 2]},
		fields=["name", "production_item", "item_name", "status", "docstatus",
			"qty", "produced_qty", "planned_start_date"],
		order_by="creation asc",
		limit_page_length=0,
	)
	return [x for x in ds if wo_con_treo(x.status, x.docstatus)]


def _ton_con_lai(cac_ma):
	"""Các mã còn tồn kho khác 0, kèm kho và số lượng."""
	if not cac_ma:
		return []
	return frappe.get_all(
		"Bin",
		filters={"item_code": ["in", list(cac_ma)], "actual_qty": ["!=", 0]},
		fields=["item_code", "warehouse", "actual_qty", "stock_uom"],
		limit_page_length=0,
	)


def _phieu_nhap(cac_ma):
	"""Phiếu kho còn nháp có dính các mã này. Chỉ cảnh báo, không chặn.

	Đọc thẳng bảng con, KHÔNG truyền `parent=`. Ô `parent` là tham số của
	đường REST bên ngoài, `frappe.get_all` ở trong máy chủ không nhận nó và
	sẽ ném TypeError. Đây đúng là lỗi đã làm màn này trả về mã 500 ngay lần
	mở đầu tiên tối 20/08/2026.
	"""
	if not cac_ma:
		return []
	dong = frappe.get_all(
		"Stock Entry Detail",
		filters={"item_code": ["in", list(cac_ma)], "docstatus": 0},
		fields=["parent", "item_code", "qty"],
		limit_page_length=0,
	)
	cha = {}
	for d in dong:
		cha.setdefault(d.parent, []).append(d.item_code)
	if not cha:
		return []
	ds = frappe.get_all(
		"Stock Entry",
		filters={"name": ["in", list(cha.keys())], "docstatus": 0},
		fields=["name", "stock_entry_type", "purpose", "posting_date"],
		limit_page_length=0,
	)
	for x in ds:
		x["cac_ma"] = sorted(set(cha.get(x.name) or []))
	return ds


def _hang_rao(cac_ma):
	"""Đọc hết ba hàng rào một lượt, trả về đúng thứ màn hình cần hiện."""
	lenh = _lenh_treo(cac_ma)
	ton = _ton_con_lai(cac_ma)
	nhap = _phieu_nhap(cac_ma)
	return {
		"lenh_treo": lenh,
		"ton_con_lai": ton,
		"phieu_nhap": nhap,
		"chan": bool(lenh or ton),
		"vi_sao": cau_chan(len(ton), len(lenh)),
	}


# ------------------------------------------------------------- kế hoạch


def _ke_hoach():
	"""Đọc hệ và dựng ra đúng danh sách sẽ đổi. KHÔNG ghi gì."""
	ds_bom = _bom_dang_chay()
	theo_chang = _ma_theo_chang(ds_bom)
	bom_cua = _bom_cua_ma(ds_bom)
	chang_cua_bom = {b.name: (b.custom_chang or "") for b in ds_bom}
	chang_cua_ma = {}
	for chang, cac in theo_chang.items():
		for ma in cac:
			chang_cua_ma[ma] = chang

	btp = sorted(theo_chang.get(CHANG_BTP) or [])

	# --- việc 1: mã nào đổi sang Phantom
	doi_ma = []
	if btp:
		for it in frappe.get_all(
			"Item",
			filters={"name": ["in", btp]},
			fields=["name", "item_name", "is_stock_item", "custom_lam_tuoi",
				"has_batch_no", "has_serial_no", "disabled"],
			order_by="name asc",
			limit_page_length=0,
		):
			if not cint(it.is_stock_item):
				continue
			vuong = []
			if cint(it.has_batch_no):
				vuong.append("đang theo lô")
			if cint(it.has_serial_no):
				vuong.append("đang theo số máy")
			doi_ma.append({
				"ma": it.name, "ten": it.item_name,
				"bom": bom_cua.get(it.name) or "",
				"vuong": ", ".join(vuong),
			})

	# --- việc 2 và 3: dòng nào trong BOM cha phải sửa cờ nổ
	con = set(btp) | set(theo_chang.get(CHANG_C1) or []) | set(theo_chang.get(CHANG_C2) or [])
	doi_dong, bom_dung_lai = [], set()
	if con:
		for d in frappe.get_all(
			"BOM Item",
			filters={"item_code": ["in", sorted(con)], "docstatus": 1,
				"parenttype": "BOM"},
			fields=["name", "parent", "item_code", "do_not_explode", "bom_no"],
			limit_page_length=0,
		):
			if d.parent not in chang_cua_bom:
				# BOM cha đã ngừng hoạt động thì để yên, không dựng lại.
				continue
			viec, vi_sao = viec_cua_dong(
				chang_cua_ma.get(d.item_code, ""), cint(d.do_not_explode),
				bool((d.bom_no or "").strip()),
			)
			if not viec:
				continue
			bom_moi = ""
			if viec == BAT_NO and not (d.bom_no or "").strip():
				bom_moi = bom_cua.get(d.item_code) or ""
				if not bom_moi:
					# Không có công thức con thì KHÔNG được bỏ cờ chặn,
					# bỏ là lệnh sản xuất đòi đúng mã vừa bỏ tồn kho.
					doi_dong.append({
						"dong": d.name, "bom_cha": d.parent, "ma": d.item_code,
						"viec": "bo_qua", "vi_sao": "mã này không có công thức "
							"đang chạy nên chưa nổ xuống được, phải lập BOM trước",
						"bom_con": "",
					})
					continue
			doi_dong.append({
				"dong": d.name, "bom_cha": d.parent, "ma": d.item_code,
				"chang": chang_cua_ma.get(d.item_code, ""),
				"viec": viec, "vi_sao": vi_sao, "bom_con": bom_moi,
			})
			bom_dung_lai.add(d.parent)

	return {
		"so_btp": len(btp),
		"doi_ma": doi_ma,
		"doi_dong": [x for x in doi_dong if x["viec"] != "bo_qua"],
		"vuong_dong": [x for x in doi_dong if x["viec"] == "bo_qua"],
		"bom_dung_lai": sorted(bom_dung_lai),
		"hang_rao": _hang_rao(btp),
	}


# ------------------------------------ hàng rào cờ "Làm tươi" đúng chặng


def chang_duoc_lam_tuoi(chang):
	"""Chặng này có được mang cờ Làm tươi không. THUẦN.

	Chỉ BTP thành phần. C1 và C2 phải giữ tồn - bánh khuôn nướng hôm nay
	để mai ráp là chuyện thường ngày ở đây, bỏ tồn hai cấp đó là mất dấu
	hàng thật đang nằm trong tủ.
	"""
	return (chang or "").strip() == CHANG_BTP


def _chang_cua_ma(ma):
	"""Chặng đọc từ BOM đang hoạt động của mã. Rỗng khi mã chưa có BOM."""
	return frappe.db.get_value(
		"BOM", {"item": ma, "docstatus": 1, "is_active": 1}, "custom_chang") or ""


def chan_lam_tuoi_sai_chang(doc, method=None):
	"""Hook validate Item: không cho bật cờ Làm tươi ngoài chặng BTP thành phần.

	Ngày 28/08/2026 đo được 23 trên 23 mã Bánh khuôn (C2) đang mang cờ này,
	tức không phải ai đó lỡ tay một lần mà là cả lô bị bật. Gỡ xong mà
	không dựng hàng rào thì lần nhân bản mã tiếp theo lại bật lại y như cũ,
	vì người ta hay tạo mã mới bằng nút Nhân bản từ một mã BTP.

	Chặn ở đây thay vì chỉ sửa dữ liệu, vì cùng một lý do đã ghi trong
	`kho_san_xuat`: mã sinh ra từ nhiều đường, vá một đường là ba đường kia
	vẫn lọt.

	Món chưa có công thức thì KHÔNG chặn: lúc đó chưa biết nó thuộc chặng
	nào, chặn là cản người ta khai món mới.
	"""
	try:
		if not cint(doc.get("custom_lam_tuoi")):
			return
		if doc.get("__islocal") and not doc.get("name"):
			return
		chang = _chang_cua_ma(doc.name)
		if not chang or chang_duoc_lam_tuoi(chang):
			return
	except Exception:
		frappe.log_error(frappe.get_traceback(), "phantom: hang rao lam tuoi")
		return
	frappe.throw(
		"<p>Món <b>%s</b> thuộc chặng <b>%s</b>, không đánh dấu "
		"<b>Làm tươi, không giữ tồn kho</b> được.</p>"
		"<p>Cờ này chỉ dành cho chặng <b>%s</b> - loại trộn xong dùng ngay "
		"trong ca, không nhập kho. Còn %s là hàng có giữ tồn: nướng hôm nay "
		"để mai ráp là chuyện thường ngày, bỏ tồn đi là mất dấu hàng thật "
		"đang nằm trong tủ.</p>"
		"<p><b>Cách sửa:</b> bỏ tích ô Làm tươi rồi lưu lại.</p>"
		% (doc.name, chang, CHANG_BTP, chang),
		title="Cờ Làm tươi đặt sai chặng",
	)


@frappe.whitelist()
def soat_lam_tuoi(chay_that=0):
	"""Liệt kê, và nếu được lệnh thì gỡ, các cờ Làm tươi đặt sai chặng.

	Chạy thử là mặc định. Gỡ cờ KHÔNG động tới sổ kho: cả 23 mã C2 vẫn
	đang `is_stock_item = 1`, cờ này mới chỉ là nhãn cho app đọc.
	"""
	_chan()
	chay_that = cint(chay_that)
	sai, da_go = [], []
	for it in frappe.get_all(
		"Item", filters={"custom_lam_tuoi": 1},
		fields=["name", "item_name", "is_stock_item"], limit_page_length=0,
	):
		chang = _chang_cua_ma(it.name)
		if not chang or chang_duoc_lam_tuoi(chang):
			continue
		sai.append({"ma": it.name, "ten": it.item_name, "chang": chang,
			"con_theo_ton": cint(it.is_stock_item)})
		if chay_that:
			frappe.db.set_value("Item", it.name, "custom_lam_tuoi", 0,
				update_modified=False)
			da_go.append(it.name)
	if chay_that:
		frappe.db.commit()
	return {"chay_that": chay_that, "so_sai": len(sai),
		"da_go": da_go, "ds": sorted(sai, key=lambda x: x["ma"])}


@frappe.whitelist()
def xem_truoc():
	"""Chỉ đọc: kế hoạch chuyển Phantom sẽ đổi những gì."""
	_chan()
	ke = _ke_hoach()
	ke["chay_that"] = 0
	ke["ghi_chu"] = (
		"Chạy thử. Sẽ đổi %d mã sang Phantom, sửa %d dòng công thức, dựng "
		"lại bảng nổ của %d công thức cha. Chưa ghi gì xuống hệ."
		% (len(ke["doi_ma"]), len(ke["doi_dong"]), len(ke["bom_dung_lai"]))
	)
	return ke


@frappe.whitelist()
def chuyen(chay_that=0):
	"""Chuyển thật. Mặc định `chay_that=0` nên gọi trống là chỉ chạy thử.

	Ghi thẳng xuống bảng chứ không qua `doc.save()`, vì ERPNext chặn đổi
	`is_stock_item` khi còn BOM đã ghi sổ trỏ tới. Hàng rào thay thế nằm ở
	`_hang_rao`: còn tồn hoặc còn lệnh treo là dừng.
	"""
	_chan()
	that = cint(chay_that)
	ke = _ke_hoach()
	ke["chay_that"] = that
	if not that:
		ke["ghi_chu"] = (
			"Chạy thử. Sẽ đổi %d mã sang Phantom, sửa %d dòng công thức, "
			"dựng lại bảng nổ của %d công thức cha. Chưa ghi gì xuống hệ. "
			"Muốn ghi thật thì chạy lại với chay_that bằng 1."
			% (len(ke["doi_ma"]), len(ke["doi_dong"]), len(ke["bom_dung_lai"]))
		)
		return ke

	if ke["hang_rao"]["chan"]:
		frappe.throw(ke["hang_rao"]["vi_sao"])

	# --- dòng công thức trước, mã hàng sau. Thứ tự này là cố ý: nếu nửa
	# chừng hỏng thì hệ vẫn còn ở trạng thái cũ đọc được, các mã BTP vẫn
	# là hàng theo tồn và bếp vẫn chạy được.
	da_dong = 0
	for d in ke["doi_dong"]:
		gia_tri = {"do_not_explode": 1 if d["viec"] == CHAN_NO else 0}
		if d.get("bom_con"):
			gia_tri["bom_no"] = d["bom_con"]
		frappe.db.set_value("BOM Item", d["dong"], gia_tri, update_modified=False)
		da_dong += 1

	da_ma, hong_ma = [], []
	for m in ke["doi_ma"]:
		try:
			frappe.db.set_value("Item", m["ma"], "is_stock_item", 0,
				update_modified=False)
			frappe.clear_document_cache("Item", m["ma"])
			da_ma.append(m["ma"])
		except Exception as e:
			hong_ma.append({"ma": m["ma"], "vi_sao": str(e)[:180]})

	da_bom, hong_bom = [], []
	for ten in ke["bom_dung_lai"]:
		try:
			doc = frappe.get_doc("BOM", ten)
			doc.update_exploded_items(save=True)
			da_bom.append(ten)
		except Exception as e:
			hong_bom.append({"bom": ten, "vi_sao": str(e)[:180]})
			frappe.log_error(frappe.get_traceback(), "phantom: dung lai no %s" % ten)

	frappe.db.commit()
	frappe.clear_cache()
	ke["da_doi_dong"] = da_dong
	ke["da_doi_ma"] = da_ma
	ke["hong_ma"] = hong_ma
	ke["da_dung_lai_bom"] = da_bom
	ke["hong_bom"] = hong_bom
	ke["ghi_chu"] = (
		"Đã chuyển %d mã sang Phantom, sửa %d dòng công thức, dựng lại bảng "
		"nổ của %d công thức cha.%s"
		% (len(da_ma), da_dong, len(da_bom),
			" Có %d chỗ hỏng, xem phần hỏng." % (len(hong_ma) + len(hong_bom))
			if (hong_ma or hong_bom) else "")
	)
	return ke


# ------------------------------------------------- dọn chứng từ thử


@frappe.whitelist()
def chung_tu_thu():
	"""Danh sách chứng từ còn treo trên 139 mã BTP, để anh Việt rà rồi dọn."""
	_chan()
	btp = sorted(_ma_theo_chang().get(CHANG_BTP) or [])
	rao = _hang_rao(btp)
	rao["so_btp"] = len(btp)
	rao["ghi_chu"] = rao["vi_sao"] or (
		"Không còn chứng từ nào treo trên các mã bán thành phẩm. "
		"Chạy chuyển Phantom được rồi."
	)
	return rao


@frappe.whitelist()
def dong_lenh(ma, ly_do=""):
	"""Đóng một lệnh sản xuất treo. ĐÓNG chứ không xoá, giữ nguyên vết (QT-20).

	Dùng đúng đường "Close" của ERPNext: lệnh vẫn nằm đó, vẫn tra lại được,
	chỉ thôi đòi nguyên liệu và thôi chặn việc đổi cấu hình mã hàng.
	"""
	_chan()
	ma = (ma or "").strip()
	if not ma:
		frappe.throw("Chưa chọn lệnh sản xuất nào để đóng.")
	wo = frappe.db.get_value("Work Order", ma, ["status", "docstatus"], as_dict=True)
	if not wo:
		frappe.throw("Không tìm thấy lệnh sản xuất %s." % ma)
	if not wo_con_treo(wo.status, wo.docstatus):
		return {"ok": 1, "ma": ma, "trang_thai": wo.status,
			"ghi_chu": "Lệnh %s đã ở trạng thái %s rồi, không cần đóng nữa."
				% (ma, wo.status)}
	from erpnext.manufacturing.doctype.work_order.work_order import stop_unstop

	stop_unstop(ma, "Closed")
	if (ly_do or "").strip():
		try:
			frappe.get_doc("Work Order", ma).add_comment(
				"Comment", "Đóng khi dọn chứng từ thử: %s" % ly_do.strip()
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "phantom: ghi chu dong lenh")
	frappe.db.commit()
	return {"ok": 1, "ma": ma, "trang_thai": "Closed",
		"ghi_chu": "Đã đóng lệnh %s. Lệnh vẫn tra lại được trên Desk." % ma}


@frappe.whitelist()
def trang_thai():
	"""Cấp BTP đã thành Phantom chưa. Màn sản xuất hỏi câu này trước khi lập lệnh.

	Vì sao màn sản xuất phải hỏi
	----------------------------
	Lệnh sản xuất lập với `use_multi_level_bom = 0` thì đòi đúng các dòng
	con trực tiếp của công thức, tức đòi luôn mã BTP. Mã BTP đã thành
	Phantom thì không còn kho để lấy, lệnh sẽ treo.

	Ngược lại, bật nổ nhiều cấp TRƯỚC khi chuyển đổi thì 71 dòng BTP đang
	có sẵn `bom_no` sẽ nổ ngay hôm nay, đổi cách bếp lấy hàng mà không ai
	yêu cầu. Nên cờ này phải đọc từ hệ tại thời điểm lập lệnh, chứ không
	ghi cứng trong màn hình.

	Đọc quyền nhẹ tay: đây chỉ là một con số cấu hình, ai lập được lệnh
	sản xuất thì đọc được.
	"""
	btp = sorted(_ma_theo_chang().get(CHANG_BTP) or [])
	if not btp:
		return {"da_phantom": 0, "so_btp": 0, "con_theo_ton": 0}
	con = frappe.get_all(
		"Item",
		filters={"name": ["in", btp], "is_stock_item": 1},
		pluck="name",
		limit_page_length=0,
	)
	return {
		"da_phantom": 0 if con else 1,
		"so_btp": len(btp),
		"con_theo_ton": len(con),
	}
