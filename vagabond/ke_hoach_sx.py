# -*- coding: utf-8 -*-
"""Kế hoạch sản xuất trong ngày, dựng trên Production Plan của ERPNext.

Anh Việt giao 28/08/2026: nút "Lập kế hoạch sản xuất" trong phân hệ Sản
xuất, ghi chú "tính toán nguyên vật liệu, bán thành phẩm, thành phẩm sản
xuất trong ngày". Nửa đêm máy tự lập phiếu cho ngày hôm sau từ toàn bộ
phiếu yêu cầu sản xuất các bên đã gửi; 5h sáng bếp vào ca mở ra đọc rồi
chuẩn bị.

KHÔNG ĐẺ DOCTYPE MỚI, đây là điều kiện anh Việt đặt
---------------------------------------------------
Production Plan của ERPNext đã có sẵn đúng bốn thứ đề bài cần:

    material_requests    các YCSX được gom vào kế hoạch
    po_items             thành phẩm phải làm, kèm số đã có lệnh
    sub_assembly_items   BTP nổ ra theo từng cấp BOM, kèm tồn hiện tại
    mr_items             nguyên vật liệu tổng, kèm tồn và số đã yêu cầu

nên tệp này KHÔNG tính lại một con số nào của ERPNext. Nó chỉ làm ba việc:
gom đúng danh sách YCSX vào phiếu, gọi đúng hàm của ERPNext, rồi dọn kết
quả ra thành hình cho app đọc. Mọi phép nổ BOM vẫn là phép của ERPNext, nên
màn app và màn Desk luôn nói cùng một con số - đó là yêu cầu "luôn đồng bộ
giữa 2 bản".

MỘT PHIẾU MỖI NGÀY CHO CẢ TIỆM
------------------------------
Anh Việt chốt 28/08/2026. Tách theo bếp thì nguyên liệu dùng chung hai bếp
bị tính hai lần ở hai phiếu, và người đi lấy hàng ở kho tổng phải tự cộng.
Một phiếu thì máy cộng hộ, còn muốn xem riêng từng bếp thì lọc bằng chip.

VÌ SAO KHÔNG BẬT `skip_available_sub_assembly_item`
---------------------------------------------------
ERPNext có sẵn công tắc đó: bật lên thì món nào còn đủ tồn sẽ KHÔNG hiện
trong bảng BTP nữa. Nghe tiện mà nguy: bếp mở phiếu ra thấy thiếu vài dòng
so với hôm qua, không biết là do đủ hàng hay do máy sót. Và công tắc đó bắt
buộc phải chọn MỘT kho BTP cho cả phiếu, trong khi tiệm có hai bếp.

Nên ở đây giữ đủ mọi dòng, và đặt bốn cột cạnh nhau đúng như đề bài:

    cần theo BOM   ERPNext nổ ra, chưa trừ gì cả
    tồn đầu ngày   số ở kho lúc 0h, đọc từ sổ kho
    tồn hiện tại   số ngay lúc mở màn
    còn phải làm   cần trừ tồn hiện tại, không âm

Dòng nào đủ tồn thì mang chip "Đủ tồn" và số còn phải làm bằng 0. Bếp vẫn
nhìn thấy nó, vẫn biết vì sao không cần làm.

NGÀY CỦA PHIẾU ĐỌC THEO `schedule_date` CỦA YCSX
-------------------------------------------------
`get_pending_material_requests` của ERPNext lọc theo `transaction_date`,
tức NGÀY LẬP phiếu. Bếp cần ngược lại: ngày HẸN GIAO. Một phiếu lập hôm
nay hẹn ngày kia mà lọc theo ngày lập thì rơi vào kế hoạch sai ngày. Nên
danh sách YCSX ở đây tự chọn theo `schedule_date` rồi đổ thẳng vào bảng
`material_requests`, sau đó vẫn gọi `get_items()` của ERPNext để nổ.

Đơn quá hạn được kéo theo, có gắn dấu. Anh Việt chốt: một ngày bếp nghỉ mà
đơn rơi mất thì không ai biết.
"""

# ------------------------------------------------------------ phần thuần

TRANG_THAI_BO = ("Stopped", "Cancelled")

# Don qua han duoc keo sang ke hoach hom sau, nhung chi trong CUA SO nay.
#
# Anh Viet chot 28/08/2026 la gom don qua han, va do van la luat. Nhung do
# tren site that cung ngay: 233 phieu YCSX deu dang o trang thai Pending,
# phieu cu nhat tu 28/07, tuc mot thang khong phieu nao duoc dong. Ly do la
# bep lam banh xong nhung khong ra lenh san xuat noi nguoc ve phieu, nen
# ERPNext khong bao gio biet phieu da xong.
#
# Gom het mot thang do vao ke hoach ngay mai thi ke hoach dau tien da sai:
# bep se thay 230 phieu trong khi thuc te chi con vai phieu chua lam. Nen
# cua so mac dinh la HAI ngay - hom qua va hom kia, du de vot mot ngay bep
# nghi ma khong keo theo no cu ca thang.
#
# Phan cu hon cua so KHONG bi giau di: `ton_dong()` liet ke ra cho anh Viet
# doc. Sua du lieu cu la viec cua anh Viet, khong phai cua man hinh nay.
SO_NGAY_QUA_HAN = 2

# Chip trạng thái của một dòng cần làm.
MUC_DU = "du"
MUC_THIEU = "thieu"
MUC_MOT_PHAN = "mot_phan"
MUC_DA_CO_LENH = "da_co_lenh"
MUC_CHUA_BOM = "chua_bom"

TEN_MUC = {
	MUC_DU: "Đủ tồn",
	MUC_THIEU: "Phải làm",
	MUC_MOT_PHAN: "Thiếu một phần",
	MUC_DA_CO_LENH: "Đã có lệnh",
	MUC_CHUA_BOM: "Chưa có công thức",
}

MAU_MUC = {
	MUC_DU: "g",
	MUC_THIEU: "w",
	MUC_MOT_PHAN: "w",
	MUC_DA_CO_LENH: "n",
	MUC_CHUA_BOM: "r",
}


def _so(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def con_phai_lam(can, ton):
	"""Cần bao nhiêu, còn tồn bao nhiêu, thì phải làm thêm bao nhiêu. THUẦN.

	Không bao giờ trả số âm: dư hàng không có nghĩa là làm âm mẻ.
	"""
	thieu = _so(can) - _so(ton)
	return thieu if thieu > 0 else 0.0


def muc_cua(can, ton, da_co_lenh=0, co_bom=True):
	"""Chip trạng thái của một dòng. THUẦN.

	Thứ tự xét là có chủ ý. "Chưa có công thức" đứng TRƯỚC mọi thứ vì dòng
	đó máy không tính được gì cả, gắn chip "đủ tồn" lên nó là nói dối. "Đã
	có lệnh" đứng trên "phải làm" vì việc đã giao đi rồi, bếp bấm tạo lệnh
	lần nữa là ra hai lệnh cho một mẻ.
	"""
	if not co_bom:
		return MUC_CHUA_BOM
	thieu = con_phai_lam(can, ton)
	if _so(da_co_lenh) > 0:
		if _so(da_co_lenh) + _so(ton) >= _so(can):
			return MUC_DA_CO_LENH
		return MUC_MOT_PHAN
	if thieu <= 0:
		return MUC_DU
	return MUC_THIEU


def gom_theo_ma(dong):
	"""Gom nhiều dòng cùng một mã thành một. THUẦN.

	Giữ lại danh sách nguồn để bếp còn biết số đó của điểm bán nào. Gom mà
	đánh mất nguồn thì lúc con số trông lạ không ai truy lại được.
	"""
	ra = {}
	for d in dong or []:
		ma = (d.get("ma") or "").strip()
		if not ma:
			continue
		o = ra.get(ma)
		if not o:
			o = ra[ma] = {"ma": ma, "ten": d.get("ten") or ma,
				"dvt": d.get("dvt") or "", "sl": 0.0, "nguon": []}
		o["sl"] += _so(d.get("sl"))
		nguon = (d.get("nguon") or "").strip()
		if nguon:
			cu = [x for x in o["nguon"] if x["ten"] == nguon]
			if cu:
				cu[0]["sl"] += _so(d.get("sl"))
			else:
				o["nguon"].append({"ten": nguon, "sl": _so(d.get("sl"))})
	return sorted(ra.values(), key=lambda x: x["ma"])


def cau_tom_tat(so_tp, so_btp, so_nvl, so_ycsx, so_thieu):
	"""Một câu nói gọn cả phiếu, đặt trên đầu màn hình. THUẦN."""
	if not so_ycsx:
		return ("Chưa có phiếu yêu cầu sản xuất nào cho ngày này. "
			"Kế hoạch trống là đúng, không phải máy sót.")
	cau = ("Gom %d phiếu yêu cầu: %d thành phẩm, %d bán thành phẩm, %d nguyên liệu."
		% (so_ycsx, so_tp, so_btp, so_nvl))
	if so_thieu:
		cau += " Còn %d mã thiếu nguyên liệu ở kho bếp." % so_thieu
	return cau


# ------------------------------------------------------- phần cần Frappe

import json

import frappe
from frappe.utils import add_days, cint, flt, getdate, nowdate

from vagabond import kho_san_xuat as ksx
from vagabond import ton_chang as tc

QUYEN_XEM = ("System Manager", "Manufacturing Manager", "Manufacturing User",
	"Bếp phó", "Giám đốc", "AP Giám đốc")
QUYEN_SUA = ("System Manager", "Manufacturing Manager", "Giám đốc", "AP Giám đốc")

# Vai được nhận thông báo 5h sáng.
VAI_NHAC = ("Manufacturing Manager", "Bếp phó")

TRUONG_MOI = {"Production Plan": [
	{
		"fieldname": "vgb_ngay_bep", "label": "Ngày bếp làm",
		"fieldtype": "Date", "insert_after": "posting_date",
		"read_only": 1, "no_copy": 1,
		"description": "Ngày mà bếp thực sự làm mẻ này. Đọc từ ngày hẹn giao "
			"của các phiếu yêu cầu sản xuất, không phải ngày lập phiếu.",
	},
	{
		"fieldname": "vgb_tu_dong", "label": "Máy tự lập",
		"fieldtype": "Check", "insert_after": "vgb_ngay_bep",
		"read_only": 1, "no_copy": 1,
		"description": "Phiếu do nhịp nửa đêm tự lập, không phải người bấm.",
	},
	{
		"fieldname": "vgb_qua_han", "label": "Số phiếu quá hạn gom vào",
		"fieldtype": "Int", "insert_after": "vgb_tu_dong",
		"read_only": 1, "no_copy": 1,
		"description": "Bao nhiêu phiếu yêu cầu hẹn ngày cũ mà bếp chưa làm "
			"xong, được kéo sang kế hoạch này.",
	},
]}


def _chan(quyen=QUYEN_XEM):
	if not set(frappe.get_roles()) & set(quyen):
		frappe.throw("Bạn chưa được cấp quyền xem kế hoạch sản xuất.")


def _cong_ty():
	return frappe.defaults.get_user_default("Company") or frappe.db.get_value(
		"Company", {"name": ["!=", ""]}, "name")


def ngay_mai(hom_nay=None):
	"""Ngày kế hoạch mặc định: hôm sau ngày đang đứng."""
	return getdate(add_days(getdate(hom_nay or nowdate()), 1))


# ---------------------------------------------------- chọn YCSX cho phiếu


def ycsx_can_lam(ngay, gom_qua_han=1, cong_ty=None, so_ngay=None):
	"""Các phiếu YCSX phải nằm trong kế hoạch của ngày này.

	Lọc theo `schedule_date` chứ không phải `transaction_date`, xem lý do ở
	đầu tệp. Chỉ lấy dòng còn dư (`qty > ordered_qty`): phần đã ra lệnh sản
	xuất rồi thì không gom lại, không thì bếp làm gấp đôi.
	"""
	ngay = getdate(ngay)
	cong_ty = cong_ty or _cong_ty()
	so_ngay = cint(so_ngay) if so_ngay is not None else SO_NGAY_QUA_HAN
	som_nhat = add_days(ngay, -so_ngay) if cint(gom_qua_han) else ngay
	dieu = ["mr.material_request_type = 'Manufacture'", "mr.docstatus = 1",
		"mr.status not in ('Stopped', 'Cancelled')", "mr.company = %(cong_ty)s",
		"mri.qty > ifnull(mri.ordered_qty, 0)",
		"mri.schedule_date <= %(ngay)s", "mri.schedule_date >= %(som_nhat)s"]
	ds = frappe.db.sql("""
		select mr.name, mr.transaction_date, mri.schedule_date, mri.item_code,
			mri.item_name, mri.qty - ifnull(mri.ordered_qty, 0) as con_lai,
			mri.uom, mri.warehouse
		from `tabMaterial Request Item` mri
		join `tabMaterial Request` mr on mr.name = mri.parent
		where %s
		order by mri.schedule_date asc, mr.name asc
	""" % " and ".join(dieu),
		{"ngay": ngay, "som_nhat": som_nhat, "cong_ty": cong_ty}, as_dict=True)
	for d in ds:
		d["qua_han"] = 1 if getdate(d.schedule_date) < ngay else 0
	return ds


def _phieu_cua_ngay(ngay):
	"""Phiếu kế hoạch còn hiệu lực của một ngày, nếu đã có."""
	return frappe.db.get_value("Production Plan", {
		"vgb_ngay_bep": getdate(ngay), "docstatus": ["<", 2]}, "name")


# ------------------------------------------------------------ lập phiếu


def _dung_phieu(ngay, ds_ycsx, cong_ty):
	"""Dựng đối tượng Production Plan và để ERPNext nổ. KHÔNG lưu.

	VÌ SAO `combine_items` PHẢI TẮT KHI NGUỒN LÀ PHIẾU YÊU CẦU SẢN XUẤT
	------------------------------------------------------------------
	Ô "Gộp món" của ERPNext chỉ chạy đúng khi nguồn là Đơn bán. Bật nó với
	nguồn là Phiếu yêu cầu sản xuất thì hỏng hai chỗ, đọc trong
	`production_plan.add_items`:

	1. Nó nhét TÊN PHIẾU YÊU CẦU vào ô `sales_order` của bảng tham chiếu,
	   mà ô đó là ô Link trỏ sang doctype Đơn bán. Lưu phiếu là Frappe từ
	   chối ngay: "Không tìm thấy Dòng #1: Tham chiếu đơn bán:
	   YCSX-2026-00150". Anh Việt gặp đúng câu này khi bấm Lập kế hoạch
	   ngày 28/08/2026.

	2. Nguy hơn cái trên và không ai thấy: đoạn cuối `add_items` gán số
	   lượng ĐÃ GỘP cho TỪNG dòng, chứ không xoá bớt dòng:

	       for po_item in self.po_items:
	           po_item.planned_qty = refs[po_item.bom_no]["qty"]

	   Ba điểm bán cùng đặt 10 cái bánh X thì ra ba dòng, mỗi dòng 30, tổng
	   90. Bếp làm gấp ba. Với nguồn Đơn bán thì màn Desk gọi tiếp
	   `combine_so_items()` để dồn ba dòng thành một, còn nguồn Phiếu yêu
	   cầu KHÔNG có bước đó.

	Nên ở đây tắt hẳn. Mỗi dòng phiếu yêu cầu thành một dòng riêng, số lượng
	đúng của điểm bán đó, và mỗi dòng giữ được tên phiếu yêu cầu gốc - bếp
	nhìn ra ngay món này của bên nào đặt.

	Phần GỘP thật sự cần thì vẫn còn: `combine_sub_items` gộp bán thành phẩm
	và nguyên liệu của cả phiếu lại, mà đó mới là con số bếp đi lấy hàng.
	"""
	doc = frappe.new_doc("Production Plan")
	doc.company = cong_ty
	doc.posting_date = nowdate()
	doc.vgb_ngay_bep = getdate(ngay)
	doc.get_items_from = "Material Request"
	# combine_items PHAI TAT khi nguon la Material Request. Xem ghi chu dai
	# ngay duoi day.
	doc.combine_items = 0
	doc.combine_sub_items = 1
	# KHÔNG bật skip_available_sub_assembly_item, xem lý do ở đầu tệp.
	doc.skip_available_sub_assembly_item = 0
	ten_mr, qua_han = [], 0
	for d in ds_ycsx:
		if d.name in ten_mr:
			continue
		ten_mr.append(d.name)
		if cint(d.get("qua_han")):
			qua_han += 1
	doc.vgb_qua_han = qua_han
	for ten in ten_mr:
		doc.append("material_requests", {
			"material_request": ten,
			"material_request_date": frappe.db.get_value(
				"Material Request", ten, "transaction_date"),
		})
	doc.get_items()
	# Ngày bắt đầu dự kiến của từng dòng là ngày bếp làm, không phải hôm nay.
	for d in doc.po_items:
		d.planned_start_date = getdate(ngay)
	if doc.po_items:
		doc.get_sub_assembly_items()
	# Hang rao thu hai cho loi 1 o tren. `combine_items` dang tat nen bang
	# nay le ra phai rong; don lai phong khi ban ERPNext sau doi cach lam.
	# Mot dong thua o day la ca phieu khong luu duoc.
	doc.set("prod_plan_references", [])
	return doc


def _nap_nvl(doc):
	"""Gọi phép tính nguyên vật liệu của ERPNext, đổ vào bảng mr_items.

	Bọc riêng vì phép này chạm nhiều kho và có thể ném lỗi trên một mã cấu
	hình lạ. Hỏng bảng nguyên liệu thì phiếu vẫn còn thành phẩm và bán thành
	phẩm để bếp làm việc, mất cả phiếu mới là hỏng.
	"""
	from erpnext.manufacturing.doctype.production_plan.production_plan import (
		get_items_for_material_requests,
	)

	try:
		# get_warehouse_list cua ERPNext goi row.get("warehouse") tren tung
		# phan tu, nen phai truyen LIST CAC DICT chu khong phai list chuoi.
		# Truyen chuoi thi no nem AttributeError va bang nguyen lieu rong
		# tron - dung loi da gap khi chay thu tren site that 28/08/2026.
		kho = [{"warehouse": k["kho"]} for k in tc.kho_cua_bep(None)
			if k["chang"] == ksx.NGUYEN_LIEU]
		du_lieu = doc.as_dict()
		ra = get_items_for_material_requests(du_lieu, warehouses=kho) or []
		doc.set("mr_items", [])
		for d in ra:
			d = dict(d)
			d["material_request_type"] = "Material Transfer"
			d["from_warehouse"] = ksx.KHO_GOC
			doc.append("mr_items", d)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ke_hoach_sx: nap nguyen lieu")


@frappe.whitelist()
def lap(ngay=None, chay_that=0, gom_qua_han=1):
	"""Lập phiếu kế hoạch cho một ngày. Chạy thử là mặc định.

	Gọi trống là chỉ ĐỌC và trả về kế hoạch sẽ ra sao. Phải truyền
	`chay_that=1` mới ghi xuống hệ.

	Đã có phiếu còn hiệu lực cho ngày đó thì KHÔNG lập nữa, trả lại phiếu cũ.
	Nhịp nửa đêm và người bấm tay dùng chung hàm này, nên chỗ chặn trùng phải
	nằm ở đây chứ không nằm ở nhịp.
	"""
	_chan(QUYEN_SUA)
	chay_that = cint(chay_that)
	ngay = getdate(ngay) if ngay else ngay_mai()
	cong_ty = _cong_ty()

	da_co = _phieu_cua_ngay(ngay)
	if da_co:
		return {"ok": 1, "da_co": 1, "ten": da_co, "ngay": str(ngay),
			"ghi_chu": "Ngày %s đã có phiếu kế hoạch %s rồi, không lập thêm."
				% (ngay.strftime("%d/%m/%Y"), da_co)}

	ds = ycsx_can_lam(ngay, gom_qua_han, cong_ty)
	if not ds:
		return {"ok": 0, "ten": "", "ngay": str(ngay), "so_ycsx": 0,
			"ghi_chu": "Không có phiếu yêu cầu sản xuất nào hẹn ngày %s, "
				"nên chưa lập kế hoạch." % ngay.strftime("%d/%m/%Y")}

	doc = _dung_phieu(ngay, ds, cong_ty)
	_nap_nvl(doc)
	ke = {
		"ngay": str(ngay), "so_ycsx": len({d.name for d in ds}),
		"so_tp": len(doc.po_items or []),
		"so_btp": len(doc.sub_assembly_items or []),
		"so_nvl": len(doc.mr_items or []),
		"qua_han": cint(doc.vgb_qua_han),
		"chay_that": chay_that,
	}
	if not chay_that:
		ke["ok"] = 0
		ke["ghi_chu"] = ("Chạy thử, chưa ghi gì. Sẽ lập phiếu cho ngày %s: "
			"%d thành phẩm, %d bán thành phẩm, %d nguyên liệu."
			% (ngay.strftime("%d/%m/%Y"), ke["so_tp"], ke["so_btp"], ke["so_nvl"]))
		return ke

	if not doc.po_items:
		ke["ok"] = 0
		ke["ghi_chu"] = ("Các phiếu yêu cầu ngày %s không có mã nào đang có "
			"công thức chạy, nên chưa lập được kế hoạch. Kiểm lại công thức "
			"của các mã đó." % ngay.strftime("%d/%m/%Y"))
		return ke

	doc.vgb_tu_dong = cint(frappe.flags.get("vgb_ke_hoach_tu_dong") or 0)
	doc.flags.ignore_permissions = True
	doc.insert()
	frappe.db.commit()
	ke["ok"] = 1
	ke["ten"] = doc.name
	ke["ghi_chu"] = ("Đã lập phiếu %s cho ngày %s ở dạng NHÁP. Bếp đọc xong "
		"bấm Chốt kế hoạch thì mới tạo được lệnh sản xuất."
		% (doc.name, ngay.strftime("%d/%m/%Y")))
	return ke


def tu_lap_nua_dem():
	"""Nhịp 0h: lập sẵn kế hoạch cho ngày hôm nay (ngày vừa sang).

	Chạy lúc 00:00 nên "ngày mai" theo cách nói của anh Việt chính là NGÀY
	HÔM NAY theo đồng hồ máy. Đặt thẳng `nowdate()` chứ không cộng thêm một
	ngày, không thì bếp 5h sáng mở ra thấy kế hoạch của ngày kia.
	"""
	try:
		frappe.flags.vgb_ke_hoach_tu_dong = 1
		frappe.set_user("Administrator")
		ra = lap(nowdate(), chay_that=1)
		frappe.logger().info("ke_hoach_sx: %s" % ra.get("ghi_chu"))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ke_hoach_sx: nhip nua dem")
	finally:
		frappe.flags.vgb_ke_hoach_tu_dong = 0


def nhac_bep_sang():
	"""Nhịp 5h: rung điện thoại bếp trưởng khi kế hoạch đã sẵn."""
	try:
		from vagabond import thong_bao

		ten = _phieu_cua_ngay(nowdate())
		if not ten:
			return
		d = frappe.db.get_value("Production Plan", ten,
			["total_planned_qty", "docstatus"], as_dict=True) or {}
		so_tp = frappe.db.count("Production Plan Item", {"parent": ten})
		so_btp = frappe.db.count("Production Plan Sub Assembly Item", {"parent": ten})
		than = ("%d món thành phẩm, %d bán thành phẩm cần làm hôm nay. "
			"Mở ra đọc rồi bấm Chốt kế hoạch." % (so_tp, so_btp))
		thong_bao.bao_cho_vai(list(VAI_NHAC), "Kế hoạch sản xuất hôm nay",
			than, duong_dan="/bep#lap-ke-hoach-san-xuat", tag="ke-hoach-sx")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ke_hoach_sx: nhac bep sang")


# ------------------------------------------------------------ đọc phiếu


def _kho_bep():
	"""Các kho lá của hai bếp, để đọc tồn. Kho đã tắt tự rơi ra."""
	return [k["kho"] for k in tc.kho_cua_bep(None)]


def _ton_hien_tai(cac_ma, cac_kho):
	"""Tồn ngay lúc này của từng mã, cộng qua các kho được hỏi."""
	if not cac_ma or not cac_kho:
		return {}
	ra = {}
	for i in range(0, len(cac_ma), 400):
		for b in frappe.get_all("Bin", filters={
			"item_code": ["in", cac_ma[i:i + 400]], "warehouse": ["in", cac_kho],
		}, fields=["item_code", "actual_qty"], limit_page_length=0):
			ra[b.item_code] = ra.get(b.item_code, 0.0) + flt(b.actual_qty)
	return ra


def _ton_dau_ngay(cac_ma, cac_kho, ngay):
	"""Tồn lúc 0h của ngày kế hoạch, đọc từ sổ kho.

	Lấy dòng sổ CUỐI CÙNG trước mốc 0h của từng cặp (mã, kho) rồi cộng lại.
	Không dùng `get_stock_balance` từng mã: 200 mã nhân 8 kho là 1.600 lần
	chạy vòng xuống cơ sở dữ liệu, màn hình sẽ treo.

	Ngày kế hoạch là hôm nay hoặc tương lai thì mốc 0h đã qua nên số này là
	số thật. Ngày tương lai xa thì nó bằng tồn hiện tại, và như vậy là đúng:
	chưa có bút toán nào giữa hai mốc.
	"""
	if not cac_ma or not cac_kho:
		return {}
	moc = "%s 00:00:00" % getdate(ngay)
	ra = {}
	for i in range(0, len(cac_ma), 300):
		lo = cac_ma[i:i + 300]
		try:
			ds = frappe.db.sql("""
				select x.item_code, x.qty_after_transaction
				from (
					select sle.item_code, sle.warehouse, sle.qty_after_transaction,
						row_number() over (
							partition by sle.item_code, sle.warehouse
							order by timestamp(sle.posting_date, sle.posting_time) desc,
								sle.creation desc
						) as thu_tu
					from `tabStock Ledger Entry` sle
					where sle.is_cancelled = 0
						and sle.item_code in %(ma)s
						and sle.warehouse in %(kho)s
						and timestamp(sle.posting_date, sle.posting_time) < %(moc)s
				) x
				where x.thu_tu = 1
			""", {"ma": lo, "kho": cac_kho, "moc": moc}, as_dict=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ke_hoach_sx: ton dau ngay")
			return {}
		for d in ds:
			ra[d.item_code] = ra.get(d.item_code, 0.0) + flt(d.qty_after_transaction)
	return ra


def _ton_kho_goc(cac_ma):
	"""Tồn ở Kho tổng 307, nơi hàng mua về nằm trước khi chuyển sang bếp."""
	return _ton_hien_tai(cac_ma, [ksx.KHO_GOC])


def _chang_cua(cac_ma):
	"""Chặng đã gom của từng mã, đọc từ công thức đang chạy."""
	if not cac_ma:
		return {}
	ra = {}
	for i in range(0, len(cac_ma), 400):
		for b in frappe.get_all("BOM", filters={
			"item": ["in", cac_ma[i:i + 400]], "docstatus": 1, "is_active": 1,
		}, fields=["item", "custom_chang", "is_default"], limit_page_length=0):
			c = tc.chang_cua_nhan(b.get("custom_chang"))
			if not c:
				continue
			if b.item not in ra or cint(b.get("is_default")):
				ra[b.item] = c
	return ra


def _bep_cua(ma, kho):
	"""Bếp của một dòng: ưu tiên hồ sơ món, không có thì đoán theo kho."""
	return ksx._bep_cua_mon(ma) or ksx.bep_cua_kho(kho or "") or ""


@frappe.whitelist()
def xem(ngay=None, ten=None):
	"""Toàn bộ phiếu kế hoạch, đã dọn thành hình cho màn app. CHỈ ĐỌC."""
	_chan()
	if ten:
		ngay = frappe.db.get_value("Production Plan", ten, "vgb_ngay_bep")
	ngay = getdate(ngay) if ngay else getdate(nowdate())
	ten = ten or _phieu_cua_ngay(ngay)
	nen = {"ngay": str(ngay), "ten": ten or "",
		"thu_tu_chang": list(tc.THU_TU), "ten_chang": dict(tc.TEN)}
	if not ten:
		nen.update({"co_phieu": 0, "thanh_pham": [], "btp": [], "nvl": [],
			"tom_tat": ("Ngày %s chưa có phiếu kế hoạch. Bấm Lập kế hoạch để "
				"máy gom các phiếu yêu cầu sản xuất lại."
				% ngay.strftime("%d/%m/%Y"))})
		return nen

	doc = frappe.get_doc("Production Plan", ten)
	kho_bep = _kho_bep()

	tp = [dict(d.as_dict()) for d in (doc.po_items or [])]
	btp = [dict(d.as_dict()) for d in (doc.sub_assembly_items or [])]
	nvl = [dict(d.as_dict()) for d in (doc.mr_items or [])]

	cac_ma = sorted({x.get("item_code") for x in tp if x.get("item_code")}
		| {x.get("production_item") for x in btp if x.get("production_item")}
		| {x.get("item_code") for x in nvl if x.get("item_code")})
	ton_nay = _ton_hien_tai(cac_ma, kho_bep)
	ton_dau = _ton_dau_ngay(cac_ma, kho_bep, ngay)
	ton_goc = _ton_kho_goc(cac_ma)
	chang = _chang_cua(cac_ma)

	def _dong(ma, ten_mon, dvt, can, da_lenh, kho, khoa, them=None):
		t_nay = flt(ton_nay.get(ma, 0))
		t_dau = flt(ton_dau.get(ma, 0))
		c = chang.get(ma, "")
		m = muc_cua(can, t_nay, da_lenh, co_bom=True)
		d = {
			"khoa": khoa, "ma": ma, "ten": ten_mon or ma, "dvt": dvt or "",
			"can": flt(can), "ton_dau": t_dau, "ton_nay": t_nay,
			"ton_goc": flt(ton_goc.get(ma, 0)),
			"con_lam": con_phai_lam(can, t_nay), "da_lenh": flt(da_lenh),
			"chang": c, "ten_chang": tc.ten_chang(c) if c else "",
			"chip_chang": tc.CHIP.get(c, ""), "muc": m, "ten_muc": TEN_MUC[m],
			"mau": MAU_MUC[m], "bep": _bep_cua(ma, kho), "kho": kho or "",
		}
		if them:
			d.update(them)
		return d

	# GOM THANH PHAM THEO MA.
	#
	# ERPNext de moi dong phieu yeu cau thanh mot dong rieng, nen mot ma
	# banh sau diem ban dat la sau dong. Do tren site 28/08/2026: 110 dong
	# cho 38 ma. Bep mo ra thay BANU00021 sau lan thi khong biet phai lam
	# bao nhieu.
	#
	# Gom lai mot dong mot ma, va GIU DANH SACH NGUON ben trong de bep con
	# truy duoc so do cua diem ban nao. Gom ma danh mat nguon thi luc con so
	# trong la khong ai truy lai duoc.
	gom_tp = {}
	for x in tp:
		ma = x.get("item_code")
		o = gom_tp.get(ma)
		if not o:
			o = gom_tp[ma] = {
				"ma": ma, "ten_mon": x.get("item_name") or x.get("description"),
				"dvt": x.get("stock_uom"), "can": 0.0, "da_lenh": 0.0,
				"da_lam": 0.0, "kho": x.get("warehouse"),
				"bom": x.get("bom_no") or "", "khoa": [], "nguon": [],
			}
		o["can"] += flt(x.get("planned_qty"))
		o["da_lenh"] += flt(x.get("ordered_qty"))
		o["da_lam"] += flt(x.get("produced_qty"))
		o["khoa"].append(x.get("name"))
		o["nguon"].append({
			"ycsx": x.get("material_request") or "",
			"kho": x.get("warehouse") or "",
			"sl": flt(x.get("planned_qty")),
		})

	ra_tp = []
	for o in sorted(gom_tp.values(), key=lambda z: z["ma"]):
		# Khoa la danh sach ten dong, noi bang dau phay. Nut tao lenh se ra
		# lenh cho TUNG dong, de moi lenh noi ve dung phieu yeu cau cua no -
		# do la cach phieu yeu cau duoc dong lai.
		d = _dong(o["ma"], o["ten_mon"], o["dvt"], o["can"], o["da_lenh"],
			o["kho"], ",".join(o["khoa"]),
			{"bom": o["bom"], "da_lam": o["da_lam"], "nguon": o["nguon"],
				"so_nguon": len(o["nguon"])})
		ra_tp.append(d)

	# Nguyên liệu xổ ra dưới từng bán thành phẩm.
	#
	# ERPNext có ô `sub_assembly_item_reference` để neo, NHƯNG nó chỉ điền ô
	# đó trong `on_submit`. Phiếu của bếp nằm ở dạng NHÁP cho tới khi bấm
	# Chốt, nên đọc ô đó trên phiếu nháp thì luôn rỗng và bếp không xổ ra
	# được gì. Đo trên site 28/08/2026: 47 dòng nguyên liệu, 0 dòng có neo.
	#
	# Nên ở đây TỰ ĐỐI CHIẾU, đúng luật ERPNext dùng trong
	# `add_reference_to_raw_materials`: một dòng nguyên liệu thuộc về dòng
	# bán thành phẩm nào có cùng món và cùng công thức. Chỉ đọc, không ghi
	# gì xuống phiếu, nên chạy được cả trên phiếu nháp lẫn phiếu đã chốt.
	nvl_theo_btp = {}
	neo_cua = {}
	for x in btp:
		neo_cua[(x.get("production_item"), x.get("bom_no"))] = x.get("name")
	for x in nvl:
		neo = (x.get("sub_assembly_item_reference") or "").strip()
		if not neo:
			neo = neo_cua.get((x.get("main_item_code"), x.get("from_bom"))) or ""
		if neo:
			nvl_theo_btp.setdefault(neo, []).append(x)

	def _dong_nvl(x):
		ma = x.get("item_code")
		return _dong(ma, x.get("item_name"), x.get("uom"), x.get("quantity"),
			x.get("ordered_qty"), x.get("warehouse"), x.get("name"),
			{"da_xin": flt(x.get("requested_qty")),
				"toi_thieu": flt(x.get("min_order_qty")),
				"du_kien": flt(x.get("projected_qty")),
				"cua_mon": x.get("main_item_code") or ""})

	ra_btp = []
	for x in btp:
		d = _dong(x.get("production_item"), x.get("item_name"),
			x.get("stock_uom") or x.get("uom"), x.get("qty"),
			x.get("ordered_qty"), x.get("fg_warehouse"), x.get("name"),
			{"bom": x.get("bom_no") or "", "cap": cint(x.get("bom_level")),
				"cua_mon": x.get("parent_item_code") or "",
				"da_lam": flt(x.get("wo_produced_qty"))})
		d["nvl"] = [_dong_nvl(n) for n in nvl_theo_btp.get(x.get("name"), [])]
		ra_btp.append(d)
	ra_btp.sort(key=lambda d: (-d["cap"], d["ma"]))

	ra_nvl = [_dong_nvl(x) for x in nvl]
	ra_nvl.sort(key=lambda d: (0 if d["muc"] == MUC_THIEU else 1, d["ma"]))

	so_thieu = len([d for d in ra_nvl if d["muc"] == MUC_THIEU])
	nen.update({
		"co_phieu": 1, "trang_thai": doc.status, "docstatus": doc.docstatus,
		"da_chot": 1 if doc.docstatus == 1 else 0,
		"tu_dong": cint(doc.get("vgb_tu_dong")), "qua_han": cint(doc.get("vgb_qua_han")),
		"so_ycsx": len(doc.material_requests or []),
		"ycsx": [d.material_request for d in (doc.material_requests or [])],
		"thanh_pham": ra_tp, "btp": ra_btp, "nvl": ra_nvl,
		"so_thieu": so_thieu,
		"tom_tat": cau_tom_tat(len(ra_tp), len(ra_btp), len(ra_nvl),
			len(doc.material_requests or []), so_thieu),
	})
	return nen


# ------------------------------------------------------------ hành động


@frappe.whitelist()
def chot(ten):
	"""Ghi sổ phiếu kế hoạch. ERPNext bắt buộc bước này mới tạo lệnh được."""
	_chan(QUYEN_SUA)
	doc = frappe.get_doc("Production Plan", ten)
	if doc.docstatus == 1:
		return {"ok": 1, "ten": ten, "ghi_chu": "Phiếu %s đã chốt từ trước rồi." % ten}
	if doc.docstatus == 2:
		frappe.throw("Phiếu %s đã huỷ, không chốt lại được. Lập phiếu mới." % ten)
	doc.submit()
	frappe.db.commit()
	return {"ok": 1, "ten": ten,
		"ghi_chu": "Đã chốt kế hoạch %s. Giờ tạo lệnh sản xuất được rồi." % ten}


@frappe.whitelist()
def tao_lenh(ten, khoa, loai="btp"):
	"""Tạo lệnh sản xuất cho một dòng, hoặc một nhóm dòng cùng mã.

	`khoa` nhận nhiều tên dòng nối bằng dấu phẩy. Màn hình gom thành phẩm
	theo mã nên một thẻ trên màn ứng với nhiều dòng phiếu, mỗi dòng của một
	phiếu yêu cầu khác nhau. Ra lệnh cho TỪNG dòng chứ không gộp thành một
	lệnh to: có vậy mỗi lệnh mới neo về đúng phiếu yêu cầu của nó, và phiếu
	yêu cầu mới tự đóng lại khi làm xong. Gộp thành một lệnh thì năm phiếu
	yêu cầu treo mãi ở trạng thái Pending, đúng cái đống 233 phiếu tồn đọng
	đang có trên hệ.
	"""
	ra, hong = [], []
	for k in [x.strip() for x in str(khoa or "").split(",") if x.strip()]:
		r = _tao_mot_lenh(ten, k, loai)
		if r.get("ok"):
			ra.append(r.get("lenh"))
		else:
			hong.append(r.get("ghi_chu"))
	if not ra:
		return {"ok": 0, "ghi_chu": hong[0] if hong else
			"Không có dòng nào để tạo lệnh."}
	return {"ok": 1, "lenh": ra,
		"ghi_chu": "Đã tạo %d lệnh sản xuất: %s.%s"
			% (len(ra), ", ".join(ra),
				" Có %d dòng bỏ qua." % len(hong) if hong else "")}


def _tao_mot_lenh(ten, khoa, loai="btp"):
	"""Tạo lệnh sản xuất cho ĐÚNG MỘT dòng của phiếu.

	ERPNext có sẵn nút tạo lệnh cho cả phiếu một lượt. Bếp cần ngược lại:
	làm tới đâu ra lệnh tới đó, vì mẻ bột trộn xong mới biết có đủ để ráp
	bánh hay không.

	Dùng `create_work_order` của chính Production Plan chứ không tự dựng
	Work Order: số lượng, kho, công thức và cách trừ phần đã có lệnh đều
	phải giống hệt nút của Desk, không thì hai bản lệch nhau.
	"""
	_chan(QUYEN_SUA)
	doc = frappe.get_doc("Production Plan", ten)
	if doc.docstatus != 1:
		frappe.throw("Phiếu %s chưa chốt. Bấm Chốt kế hoạch trước đã, ERPNext "
			"không cho tạo lệnh từ phiếu nháp." % ten)

	from erpnext.manufacturing.doctype.work_order.work_order import get_default_warehouse

	kho_mac_dinh = get_default_warehouse(doc.company)
	loai = (loai or "btp").strip().lower()

	if loai == "tp":
		dong = [d for d in (doc.po_items or []) if d.name == khoa]
		if not dong:
			frappe.throw("Không thấy dòng thành phẩm này trong phiếu %s." % ten)
		d = dong[0]
		con = flt(d.planned_qty) - flt(d.ordered_qty)
		if con <= 0:
			return {"ok": 0, "ghi_chu": "Món %s đã ra lệnh đủ số rồi." % d.item_code}
		mon = frappe._dict({
			"production_item": d.item_code, "use_multi_level_bom": d.include_exploded_items,
			"material_request": d.material_request,
			"material_request_item": d.material_request_item,
			"bom_no": d.bom_no, "description": d.description, "stock_uom": d.stock_uom,
			"company": doc.company, "fg_warehouse": d.warehouse,
			"production_plan": doc.name, "production_plan_item": d.name,
			"planned_start_date": d.planned_start_date, "qty": con,
		})
	else:
		dong = [d for d in (doc.sub_assembly_items or []) if d.name == khoa]
		if not dong:
			frappe.throw("Không thấy dòng bán thành phẩm này trong phiếu %s." % ten)
		d = dong[0]
		if flt(d.qty) - flt(d.ordered_qty) <= 0:
			return {"ok": 0, "ghi_chu": "Món %s đã ra lệnh đủ số rồi." % d.production_item}
		mon = frappe._dict({"company": doc.company})
		doc.prepare_data_for_sub_assembly_items(d, mon)

	from erpnext.manufacturing.doctype.production_plan.production_plan import (
		set_default_warehouses,
	)

	set_default_warehouses(mon, kho_mac_dinh)
	ten_lenh = doc.create_work_order(mon)
	if not ten_lenh:
		return {"ok": 0, "ghi_chu": "ERPNext không tạo lệnh cho dòng này, "
			"thường là do số cần làm đã về 0 hoặc đã có lệnh trùng."}
	doc.reload()
	doc.update_ordered_status()
	doc.update_requested_status()
	doc.set_status()
	doc.db_update_all()
	frappe.db.commit()
	return {"ok": 1, "lenh": ten_lenh,
		"ghi_chu": "Đã tạo lệnh sản xuất %s." % ten_lenh}


@frappe.whitelist()
def xin_chuyen_nvl(ten):
	"""Sinh phiếu xin chuyển nguyên liệu từ Kho tổng 307 sang kho bếp.

	Đây là mảnh còn thiếu giữa "kế hoạch nói cần bao nhiêu" và "bếp thật sự
	có hàng trong tay". Dùng `make_material_request` của Production Plan để
	số lượng khớp đúng bảng nguyên liệu, và để phần đã xin rồi không xin lại.

	Phiếu sinh ra là NHÁP: anh Kiên còn phải xem kho tổng có đủ không đã.
	"""
	_chan(QUYEN_SUA)
	doc = frappe.get_doc("Production Plan", ten)
	if doc.docstatus != 1:
		frappe.throw("Phiếu %s chưa chốt nên chưa xin chuyển nguyên liệu được." % ten)
	if not doc.mr_items:
		return {"ok": 0, "ghi_chu": "Phiếu này không có dòng nguyên liệu nào thiếu."}
	for d in doc.mr_items:
		d.material_request_type = "Material Transfer"
		if not d.from_warehouse:
			d.from_warehouse = ksx.KHO_GOC
	doc.db_update_all()
	truoc = set(frappe.get_all("Material Request", filters={
		"material_request_type": "Material Transfer", "docstatus": 0}, pluck="name"))
	doc.make_material_request()
	frappe.db.commit()
	sau = set(frappe.get_all("Material Request", filters={
		"material_request_type": "Material Transfer", "docstatus": 0}, pluck="name"))
	moi = sorted(sau - truoc)
	if not moi:
		return {"ok": 0, "ghi_chu": "Không có gì để xin thêm, các mã đã xin "
			"chuyển đủ từ trước."}
	return {"ok": 1, "phieu": moi,
		"ghi_chu": "Đã tạo %d phiếu xin chuyển kho ở dạng nháp: %s. Anh Kiên "
			"soạn hàng rồi ghi sổ." % (len(moi), ", ".join(moi))}


@frappe.whitelist()
def tinh_hinh_giu_cho():
	"""Công tắc giữ chỗ nguyên liệu đang bật hay tắt, và bật thì ảnh hưởng gì.

	KHÔNG tự bật. `enable_stock_reservation` là công tắc của cả hệ Kho, bật
	lên là mọi đơn bán cũng bắt đầu giữ chỗ theo, không riêng gì sản xuất.
	Đổi một công tắc cỡ đó phải là quyết định của anh Việt chứ không phải
	của một màn hình bếp.
	"""
	_chan()
	bat = cint(frappe.db.get_single_value("Stock Settings", "enable_stock_reservation"))
	return {
		"bat": bat,
		"ghi_chu": ("Giữ chỗ nguyên liệu đang BẬT. Phiếu kế hoạch chốt xong sẽ "
			"khoá phần nguyên liệu đã tính, bếp kia và đơn lẻ không rút mất."
			if bat else
			"Giữ chỗ nguyên liệu đang TẮT. Muốn bật thì vào Cài đặt kho của "
			"ERPNext bật ô Enable Stock Reservation. Lưu ý đây là công tắc "
			"chung: bật lên thì đơn bán cũng bắt đầu giữ chỗ theo, không "
			"riêng phần sản xuất."),
	}


@frappe.whitelist()
def ton_dong(truoc_ngay=None, gioi_han=200):
	"""Các YCSX quá hạn NGOÀI cửa sổ, tức nằm ngoài kế hoạch hằng ngày.

	Đo trên site 28/08/2026: 233 phiếu YCSX đều đang ở trạng thái Pending,
	phiếu cũ nhất từ 28/07. Không phải bếp nợ một tháng hàng: bếp làm xong
	rồi nhưng không ra lệnh sản xuất nối ngược về phiếu, nên ERPNext không
	bao giờ biết phiếu đã xong.

	Hàm này CHỈ ĐỌC và liệt kê ra. KHÔNG tự đóng phiếu nào: đó là dữ liệu
	quá khứ, và quy tắc của tiệm là liệt kê cho anh Việt chứ không tự sửa.
	"""
	_chan()
	truoc = getdate(truoc_ngay) if truoc_ngay else add_days(
		getdate(nowdate()), -SO_NGAY_QUA_HAN)
	gioi_han = cint(gioi_han) or 200
	ds = frappe.db.sql("""
		select mr.name, mri.schedule_date, mri.item_code, mri.item_name,
			mri.qty - ifnull(mri.ordered_qty, 0) as con_lai, mri.uom,
			mri.warehouse, mr.owner
		from `tabMaterial Request Item` mri
		join `tabMaterial Request` mr on mr.name = mri.parent
		where mr.material_request_type = 'Manufacture' and mr.docstatus = 1
			and mr.status not in ('Stopped', 'Cancelled')
			and mri.qty > ifnull(mri.ordered_qty, 0)
			and mri.schedule_date < %(truoc)s
		order by mri.schedule_date asc
		limit %(gioi_han)s
	""", {"truoc": truoc, "gioi_han": gioi_han}, as_dict=True)
	phieu = sorted({d.name for d in ds})
	som = str(ds[0].schedule_date) if ds else ""
	return {
		"truoc_ngay": str(truoc), "so_phieu": len(phieu), "so_dong": len(ds),
		"som_nhat": som, "ds": [dict(d) for d in ds],
		"ghi_chu": ("Có %d phiếu yêu cầu sản xuất hẹn trước ngày %s mà hệ vẫn "
			"coi là chưa làm, phiếu cũ nhất hẹn %s. Phần lớn là do bếp làm "
			"xong nhưng không ra lệnh sản xuất nối về phiếu, chứ không phải "
			"nợ hàng thật. Anh Việt xem rồi quyết đóng hay để, màn này không "
			"tự đóng phiếu nào."
			% (len(phieu), truoc.strftime("%d/%m/%Y"),
				getdate(som).strftime("%d/%m/%Y") if som else "-"))
			if ds else "Không có phiếu yêu cầu nào tồn đọng ngoài cửa sổ.",
	}


@frappe.whitelist()
def ds_phieu(so_ngay=14):
	"""Vài phiếu gần đây, để bếp lật lại ngày hôm trước."""
	_chan()
	so_ngay = cint(so_ngay) or 14
	tu = add_days(nowdate(), -so_ngay)
	ds = frappe.get_all("Production Plan", filters={
		"vgb_ngay_bep": [">=", tu], "docstatus": ["<", 2],
	}, fields=["name", "vgb_ngay_bep", "docstatus", "status", "total_planned_qty",
		"vgb_tu_dong"], order_by="vgb_ngay_bep desc", limit_page_length=40)
	return [{"ten": d.name, "ngay": str(d.vgb_ngay_bep),
		"da_chot": 1 if d.docstatus == 1 else 0, "trang_thai": d.status,
		"tong": flt(d.total_planned_qty), "tu_dong": cint(d.vgb_tu_dong)}
		for d in ds]


MAU_IN = "Vagabond - Kế hoạch sản xuất"


def dung_mau_in():
	"""Tạo bản ghi Print Format lần đầu, nếu chưa có. Gọi từ after_migrate.

	`mau_in.dong_bo()` CỐ Ý không tự tạo bản ghi mới, xem tài liệu của nó:
	một bản ghi sinh ra lặng lẽ trong lúc migrate thì không ai biết nó từ
	đâu ra. Nên việc tạo lần đầu nằm ở đây, có tên hàm rõ ràng. Tạo xong thì
	nội dung HTML để nhịp đồng bộ chung giữ, y như mọi mẫu in khác.
	"""
	try:
		if frappe.db.exists("Print Format", MAU_IN):
			return 0
		from vagabond.mau_in import doc_mau
		from vagabond.mau_in.le_in import LE_MM

		doc = frappe.get_doc({
			"doctype": "Print Format", "name": MAU_IN,
			"doc_type": "Production Plan", "module": "Vagabond",
			"standard": "No", "print_format_type": "Jinja",
			"custom_format": 1, "raw_printing": 0, "disabled": 0,
			"margin_top": LE_MM, "margin_bottom": LE_MM,
			"margin_left": LE_MM, "margin_right": LE_MM,
			"html": doc_mau("ke_hoach_san_xuat.html"),
		})
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
		return 1
	except Exception:
		# Khong bao gio duoc lam hong after_migrate.
		frappe.log_error(frappe.get_traceback(), "ke_hoach_sx: dung mau in")
		return 0
