"""Ô "Chặng bán thành phẩm" quyết tài khoản tồn kho của món (#307, con của #206).

VÌ SAO CÓ TỆP NÀY, 13/09/2026
--------------------------------------------------------------------
Khải (kế toán giá thành) muốn bán thành phẩm (BTP) có theo dõi tồn hạch
toán vào 1552, không nằm chung tài khoản thành phẩm 1551 của kho bếp. Anh
Việt không mở lại kho BTP riêng (đã tắt 28/08/2026, xem kho_san_xuat.py).
Giải pháp anh duyệt: giữ MỘT kho, bật tính năng "tài khoản tồn kho theo
món" của ERPNext, và để ô Chặng trên hồ sơ món tự điền tài khoản vào Item
Default. Kế toán chọn chặng là xong, không nhét cấp vào số mã, không đổi
mã cũ.

CƠ CHẾ LÕI ĐANG DÙNG (đối chiếu, không tự chế)
--------------------------------------------------------------------
ERPNext de591661, erpnext/controllers/stock_controller.py, đã ghi tại
vagabond/hang_tang_kho.py:27-31:

    get_inventory_account_map: if self.use_item_inventory_account:
        return self.get_item_wise_inventory_account_map()
    return get_warehouse_account_map(self.company)

Cờ bật đọc trên site ngày 08/09/2026 (tai_lieu/issue-206-tai-khoan-chi-phi.md
dòng 10-11): Company Vagabond `enable_item_wise_inventory_account=0`. Tệp
này KHÔNG bật cờ đó; bật là thao tác tay của kế toán đúng ngày cắt.

Tên ô trên Item Default mà lõi đọc khi cờ bật đặt ở một hằng duy nhất
`TRUONG_ITEM_DEFAULT`. Phiên viết tệp này (14/09/2026, GitHub Actions)
không ra được mạng để clone lõi nên CHƯA dán được nguyên văn hàm
get_item_wise_inventory_account_map. Phần chạm Frappe vì thế kiểm meta
trước khi ghi: ô không tồn tại thì hook chỉ báo và không ghi, còn patch
thì dừng migrate rõ ràng. Người có bench phải đối chiếu hằng này với lõi
trước khi bật cờ thật (xem docs/van-hanh-agent/cong-viec/issue-307.md).

LUẬT ÁP DỤNG (đặc tả #307 mục 3)
--------------------------------------------------------------------
- Chỉ món theo tồn (is_stock_item=1), mã có tiền tố BTP (TIEN_TO_BTP), ô
  Chặng là "BTP sơ cấp" hoặc "BTP sẵn sàng". "BTP thành phần" (phantom)
  KHÔNG áp, dù ma_chang_khai_tay xếp nó về sơ cấp cho việc chọn kho.
- Chặng cấp 1 lấy ô "Tài khoản tồn kho BTP cấp 1" của Vagabond Settings,
  cấp 2 lấy ô cấp 2. Khải chốt 1552 chung hay tách 15521/15522 thì chỉ
  đổi hai ô đó, không đổi code.
- Chặng không đổi mà kế toán đã khai tay tài khoản khác: GIỮ. Chặng đổi:
  máy ghi đè và ghi chú vào comment của món. Xoá chặng: xoá tài khoản khai
  riêng để món quay về theo kho.
- Hai ô cấu hình trống: không ghi, chỉ nhắc màu vàng, không chặn lưu.

Phần thuần nằm trên vạch `import frappe`, để bộ kiểm tầng khung chạy được
trên máy CI tay không.
"""

from vagabond.kho_san_xuat import (
	BTP_SO_CAP, BTP_SAN_SANG, TEN_CHANG, TIEN_TO_BTP, NHAN_BTP_THANH_PHAN,
	ma_chang_khai_tay,
)

# phần thuần

# Ô trên Vagabond Settings cho từng chặng.
O_CAU_HINH = {
	BTP_SO_CAP: "tk_ton_btp_cap1",
	BTP_SAN_SANG: "tk_ton_btp_cap2",
}

# Ô trên Item Default mà lõi đọc khi Company.enable_item_wise_inventory_account
# bật. CHƯA đối chiếu nguyên văn với lõi (xem đầu tệp). Đổi ở đây là đổi
# một chỗ duy nhất.
TRUONG_ITEM_DEFAULT = "default_inventory_account"

# Số hiệu tài khoản BTP theo TT200, dùng để patch chọn mặc định khi site có
# đúng một tài khoản con còn dùng.
SO_HIEU_BTP = "1552"

# Ô điền tay trên hồ sơ món (anh Việt chốt 14/09/2026 chiều). Nó là GƯƠNG
# của ô TRUONG_ITEM_DEFAULT trên dòng Item Default của công ty, đặt ngay
# dưới ô Chặng để kế toán thấy và sửa được mà không phải mở bảng con. Nguồn
# sự thật vẫn là dòng Item Default (lõi đọc ở đó); ô gương chỉ là lối vào.
# Người đổi ô gương thì máy chép xuống dòng; không đổi thì ô gương chép lại
# giá trị dòng khi lưu.
O_TAY = "custom_tk_ton_kho_tay"
NHAN_O_TAY = "Tài khoản tồn kho (điền tay)"

TRUONG_MOI = {"Item": [
	{
		"fieldname": O_TAY, "label": NHAN_O_TAY,
		"fieldtype": "Link", "options": "Account",
		"insert_after": "custom_chang_btp",
		"description": "Tài khoản tồn kho riêng của món này khi Company bật "
			"tài khoản tồn kho theo món. Chính là ô Tài khoản tồn kho trên dòng "
			"Item Default của công ty, đưa lên đây cho dễ sửa. Món có Chặng bán "
			"thành phẩm thì máy tự điền theo chặng; đổi chặng là máy ghi đè. "
			"Để trống thì lõi tìm ở nhóm món rồi nhãn hiệu.",
	},
]}

# Năm kết luận của phép quyết định, để hook và patch cùng đọc một luật.
GIU = "giu"          # kế toán đã khai tay khác, chặng không đổi: tôn trọng
GHI = "ghi"          # ghi (hoặc ghi đè) tài khoản theo chặng
XOA = "xoa"          # chặng bị bỏ: xoá tài khoản khai riêng, về theo kho
NHAC = "nhac"        # chặng hợp lệ nhưng ô cấu hình trống: chỉ nhắc
BO_QUA = "bo_qua"    # không thuộc phạm vi, hoặc đã đúng rồi


def _chu(v):
	return " ".join((v or "").split()).strip().lower()


def la_ma_btp(ma):
	"""Mã có tiền tố BTP không. THUẦN."""
	m = (ma or "").strip().upper()
	return any(m.startswith(t) for t in TIEN_TO_BTP)


def chang_ap_dung(ma, is_stock_item, khai_tay):
	"""Chặng mà luật tài khoản ÁP cho món này, hoặc None. THUẦN.

	Khác `chang_cua_mon` ở hai chỗ có chủ ý: không suy từ tên hay công
	thức (chỉ nghe ô khai tay), và "BTP thành phần" trả None chứ không xếp
	về sơ cấp. Phantom thường không theo tồn, và nếu có theo tồn thì Khải
	phải tự chọn cấp cho nó, máy không đoán.
	"""
	if not is_stock_item or not la_ma_btp(ma):
		return None
	if _chu(khai_tay) == NHAN_BTP_THANH_PHAN.lower():
		return None
	chang = ma_chang_khai_tay(khai_tay)
	return chang if chang in (BTP_SO_CAP, BTP_SAN_SANG) else None


def tai_khoan_theo_chang(chang, cau_hinh):
	"""Tài khoản cấu hình cho chặng, hoặc None khi ô trống. THUẦN."""
	if chang not in O_CAU_HINH:
		return None
	return ((cau_hinh or {}).get(O_CAU_HINH[chang]) or "").strip() or None


def quyet_dinh(ma, is_stock_item, khai_tay, khai_tay_cu, tk_hien_co, cau_hinh):
	"""Phải làm gì với tài khoản tồn kho của món. THUẦN.

	Trả về dict(hanh_dong, tai_khoan, chang, ghi_chu). `khai_tay_cu` là ô
	Chặng đang nằm trong cơ sở dữ liệu trước lần lưu này (None khi món mới);
	`tk_hien_co` là tài khoản đang ghi trên Item Default của công ty.
	"""
	moi = chang_ap_dung(ma, is_stock_item, khai_tay)
	cu = chang_ap_dung(ma, is_stock_item, khai_tay_cu)
	tk_hien_co = (tk_hien_co or "").strip() or None
	kq = dict(hanh_dong=BO_QUA, tai_khoan=None, chang=moi, ghi_chu="")
	if moi is None:
		# Ra khỏi phạm vi (xoá chặng, đổi sang thành phần, tắt theo tồn).
		# Chỉ xoá giá trị MÁY đã điền: giá trị đang có phải đúng bằng cái
		# máy điền cho chặng cũ. Khác đi là người điền tay (anh Việt chốt
		# 14/09/2026 chiều), giữ nguyên và nói rõ.
		if cu is not None and tk_hien_co:
			tk_may_cu = tai_khoan_theo_chang(cu, cau_hinh)
			if tk_hien_co == tk_may_cu:
				kq.update(hanh_dong=XOA, ghi_chu="Bỏ chặng %s, xoá tài khoản máy điền %s, "
					"món quay về lưới đỡ theo nhóm món hoặc theo kho." % (TEN_CHANG[cu], tk_hien_co))
			else:
				kq.update(hanh_dong=GIU, ghi_chu="Bỏ chặng %s nhưng giữ tài khoản điền tay %s "
					"(khác giá trị máy điền)." % (TEN_CHANG[cu], tk_hien_co))
		return kq
	tk = tai_khoan_theo_chang(moi, cau_hinh)
	if not tk:
		kq.update(hanh_dong=NHAC, ghi_chu="Chưa khai ô %s trên Vagabond Settings."
			% O_CAU_HINH[moi])
		return kq
	kq["tai_khoan"] = tk
	if tk_hien_co == tk:
		return kq
	if moi == cu and tk_hien_co:
		kq.update(hanh_dong=GIU, ghi_chu="Giữ tài khoản khai tay %s vì chặng không đổi."
			% tk_hien_co)
		return kq
	ghi_chu = "Chặng %s: tài khoản tồn kho %s." % (TEN_CHANG[moi], tk)
	if tk_hien_co:
		ghi_chu = "Đổi chặng sang %s: máy ghi đè tài khoản tồn kho %s bằng %s." % (
			TEN_CHANG[moi], tk_hien_co, tk)
	kq.update(hanh_dong=GHI, ghi_chu=ghi_chu)
	return kq


def loi_tai_khoan(tk, cong_ty):
	"""Câu báo lỗi nếu tài khoản không dùng được cho ô cấu hình, else "". THUẦN.

	`tk` là dict các cột của Account. Lọc theo đặc tả: đúng công ty, loại
	Stock, không nhóm, không tắt, VND.
	"""
	if not tk:
		return "Tài khoản không tồn tại."
	if cong_ty and tk.get("company") != cong_ty:
		return "Tài khoản thuộc công ty %s, không phải %s." % (tk.get("company"), cong_ty)
	if tk.get("is_group"):
		return "Tài khoản là nhóm, chọn tài khoản chi tiết."
	if tk.get("disabled"):
		return "Tài khoản đã tắt."
	if tk.get("account_type") != "Stock":
		return "Tài khoản phải có loại Stock (tồn kho)."
	if (tk.get("account_currency") or "VND") != "VND":
		return "Tài khoản phải là VND."
	return ""


def doc_o_tay(o_tay, o_tay_cu, tk_dong):
	"""Giá trị tài khoản đang có hiệu lực trước khi xét chặng. THUẦN.

	Trả về (tk_hien_co, tay_doi). Người đổi ô gương so với bản trong cơ sở
	dữ liệu thì ý người thắng dòng Item Default (kể cả xoá trắng để bỏ tài
	khoản riêng). Không đổi thì dòng Item Default là sự thật.
	"""
	o_tay = (o_tay or "").strip() or None
	o_tay_cu = (o_tay_cu or "").strip() or None
	tk_dong = (tk_dong or "").strip() or None
	if o_tay != o_tay_cu:
		return o_tay, True
	return tk_dong, False


def gia_tri_cuoi(hanh_dong, tai_khoan, tk_hien_co):
	"""Giá trị sẽ nằm trên dòng Item Default sau lần lưu này. THUẦN.

	Máy ghi (GHI) hay xoá (XOA) thì theo máy. Còn lại theo `tk_hien_co`, tức
	là ô điền tay nếu người vừa đổi, hoặc chính dòng cũ.
	"""
	if hanh_dong == GHI:
		return tai_khoan
	if hanh_dong == XOA:
		return None
	return (tk_hien_co or "").strip() or None


def chon_mac_dinh(cac_tk):
	"""Tài khoản 1552 mặc định nếu site có ĐÚNG MỘT tài khoản con còn dùng. THUẦN.

	`cac_tk` là danh sách dict Account (name, account_number, is_group,
	disabled). Nhiều hơn một (Khải đã tách 15521/15522) hoặc không có thì
	trả None để kế toán tự khai.
	"""
	hop = [t for t in (cac_tk or [])
		if str(t.get("account_number") or "").strip().startswith(SO_HIEU_BTP)
		and not t.get("is_group") and not t.get("disabled")]
	return hop[0].get("name") if len(hop) == 1 else None


# phần chạm Frappe
import frappe


def doc_cau_hinh():
	return {o: frappe.db.get_single_value("Vagabond Settings", o) for o in O_CAU_HINH.values()}


def co_o_item_default():
	return bool(frappe.get_meta("Item Default").has_field(TRUONG_ITEM_DEFAULT))


def cong_ty_ap_dung(cau_hinh):
	"""Cấu hình toàn site phải theo công ty mặc định, không theo Account nhập vào.

	Nếu suy công ty từ tài khoản, chọn nhầm Account của công ty Demo sẽ
	đổi luôn công ty đích và vượt qua mọi phép kiểm phía sau.
	"""
	ct = frappe.db.get_single_value("Global Defaults", "default_company")
	if not ct:
		frappe.throw("Chưa có công ty mặc định. Khai công ty trong Global Defaults trước khi cấu hình tài khoản tồn kho.")
	return ct


def kiem_o_cau_hinh(doc, method=None):
	"""Validate Vagabond Settings: hai ô tài khoản BTP phải là tài khoản kho hợp lệ."""
	if not any(doc.get(o) for o in O_CAU_HINH.values()):
		return
	ct = cong_ty_ap_dung(doc)
	for o in O_CAU_HINH.values():
		tk = doc.get(o)
		if not tk:
			continue
		r = frappe.db.get_value("Account", tk, ["company", "is_group", "disabled",
			"account_type", "account_currency"], as_dict=True)
		loi = loi_tai_khoan(r, ct)
		if loi:
			frappe.throw("Ô %s: %s" % (o, loi))


def ap_dung(doc, cau_hinh=None, ghi_db=False):
	"""Áp luật lên một Item đã nạp. Trả về dict quyết định.

	`ghi_db=False` (hook validate): chỉ sửa trên doc, Frappe ghi khi lưu.
	`ghi_db=True` (patch): ghi thẳng dòng Item Default, không save() Item để
	không kích các validate khác trên dữ liệu cũ.
	"""
	cau_hinh = cau_hinh if cau_hinh is not None else doc_cau_hinh()
	if not ghi_db and not frappe.db.get_single_value("Global Defaults", "default_company"):
		cau = "Chưa có công ty mặc định. Đã giữ tài khoản của món; kế toán khai Global Defaults rồi lưu lại."
		frappe.msgprint(cau, indicator="orange", alert=True)
		return {"hanh_dong": BO_QUA, "tai_khoan": None, "ghi_chu": cau}
	khai_cu, o_tay_cu = None, None
	# Chỉ hỏi cột ô gương khi nó đã được dựng, để lần migrate đầu (hook
	# chạy trước truong_tu_them) không ném lỗi thiếu cột.
	cot = ["custom_chang_btp"] + ([O_TAY] if doc.meta.has_field(O_TAY) else [])
	if not doc.is_new():
		r = frappe.db.get_value("Item", doc.name, cot, as_dict=True) or {}
		khai_cu, o_tay_cu = r.get("custom_chang_btp"), r.get(O_TAY)
	cty = cong_ty_ap_dung(cau_hinh)
	dong = None
	for d in doc.get("item_defaults") or []:
		if d.company == cty:
			dong = d
			break
	tk_dong = (dong.get(TRUONG_ITEM_DEFAULT) if dong else None) or None
	# Ô điền tay: người vừa đổi thì ý người thắng dòng Item Default.
	tk_hien_co, tay_doi = doc_o_tay(doc.get(O_TAY), o_tay_cu, tk_dong)
	kq = quyet_dinh(doc.item_code or doc.name, doc.is_stock_item,
		doc.get("custom_chang_btp"), khai_cu, tk_hien_co, cau_hinh)
	hd = kq["hanh_dong"]
	kq["tay_doi"] = tay_doi
	if hd == NHAC:
		frappe.msgprint("Món %s ở chặng %s nhưng %s Kế toán khai tài khoản tồn kho BTP "
			"trong Vagabond Settings rồi lưu lại món." % (doc.name, TEN_CHANG[kq["chang"]],
			kq["ghi_chu"]), indicator="orange", alert=True)
	gia_tri = gia_tri_cuoi(hd, kq["tai_khoan"], tk_hien_co)
	kq["gia_tri"] = gia_tri
	if gia_tri == tk_dong:
		# Không có gì phải ghi xuống dòng; chỉ giữ ô gương khớp với dòng.
		_dat_o_tay(doc, gia_tri, ghi_db)
		return kq
	if not co_o_item_default():
		frappe.log_error("Item Default không có ô %s, không ghi tài khoản tồn kho cho %s"
			% (TRUONG_ITEM_DEFAULT, doc.name), "tai_khoan_btp")
		frappe.msgprint("Chưa đối chiếu được ô tài khoản tồn kho theo món với lõi "
			"ERPNext. Chưa ghi tài khoản; báo người kỹ thuật.", indicator="orange", alert=True)
		return kq
	if dong is None:
		if gia_tri is None:
			_dat_o_tay(doc, None, ghi_db)
			return kq
		dong = doc.append("item_defaults", {"company": cty})
	dong.set(TRUONG_ITEM_DEFAULT, gia_tri)
	if ghi_db:
		if dong.name:
			frappe.db.set_value("Item Default", dong.name, TRUONG_ITEM_DEFAULT, gia_tri,
				update_modified=False)
		else:
			dong.parent, dong.parenttype, dong.parentfield = doc.name, "Item", "item_defaults"
			dong.idx = len(doc.get("item_defaults") or [])
			dong.db_insert()
	_dat_o_tay(doc, gia_tri, ghi_db)
	if hd == GHI and tk_dong and not doc.is_new():
		doc.add_comment("Comment", kq["ghi_chu"])
	return kq


def _dat_o_tay(doc, gia_tri, ghi_db):
	"""Ô gương luôn khớp dòng Item Default sau khi lưu."""
	if not doc.meta.has_field(O_TAY):
		return
	doc.set(O_TAY, gia_tri)
	if ghi_db and not doc.is_new():
		frappe.db.set_value("Item", doc.name, O_TAY, gia_tri, update_modified=False)


def dung():
	"""Dựng ô gương trên Item và cho cột tài khoản hiện trong lưới Item Default.

	Gọi từ truong_tu_them.dung() sau mỗi lần migrate. Lặp lại được:
	create_custom_fields(update=True) và make_property_setter ghi đè đúng
	một bản ghi. Item Default là bảng con dùng chung cho Item, Item Group và
	Brand, nên nhãn tiếng Việt hiện ở cả ba nơi; đó là điều mong muốn vì
	lưới đỡ theo nhóm món (luoi_do_nhom.py) cũng khai ở ô này.
	"""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter

	create_custom_fields(TRUONG_MOI, update=True)
	if not co_o_item_default():
		frappe.log_error("Item Default không có ô %s" % TRUONG_ITEM_DEFAULT, "tai_khoan_btp.dung")
		return
	make_property_setter("Item Default", TRUONG_ITEM_DEFAULT, "in_list_view", 1, "Check",
		validate_fields_for_doctype=False)
	make_property_setter("Item Default", TRUONG_ITEM_DEFAULT, "label", NHAN_O_TAY, "Data",
		validate_fields_for_doctype=False)


def khi_luu_mon(doc, method=None):
	"""Hook validate Item. Không bao giờ chặn lưu món vì lỗi của lớp này.

	Chạy cho MỌI món, không chỉ mã BTP: ô điền tay áp cho cả nguyên liệu và
	thành phẩm; luật theo chặng tự trả BO_QUA khi mã không phải BTP.
	"""
	try:
		ap_dung(doc)
	except frappe.ValidationError:
		raise
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tai_khoan_btp.khi_luu_mon %s" % doc.name)


def khi_luu_cau_hinh(doc, method=None):
	"""Kế toán khai tài khoản rồi lưu Settings: nạp chặng đã chọn, giữ khai tay."""
	if not any(doc.has_value_changed(o) for o in O_CAU_HINH.values()):
		return
	cau_hinh = {o: doc.get(o) for o in O_CAU_HINH.values()}
	# Lần cài app đầu, Single mới báo các ô đều đổi dù cùng đang trống.
	# Chưa có tài khoản để nạp thì không đòi công ty hoặc ghi nhóm/món.
	if not any(cau_hinh.values()):
		return
	cty = cong_ty_ap_dung(cau_hinh)
	from vagabond import luoi_do_nhom
	kq = luoi_do_nhom.ap_dung(cty, chi_btp=True, cau_hinh=cau_hinh)
	if kq["dem"]["loi"]:
		frappe.throw("Chưa nạp được tài khoản cho nhóm BTP. Chưa lưu cấu hình; kiểm nhật ký lỗi rồi thử lại.")
	for ten in frappe.get_all("Item", filters={"is_stock_item": 1,
		"custom_chang_btp": ["!=", ""]}, pluck="name", limit_page_length=0):
		ap_dung(frappe.get_doc("Item", ten), cau_hinh, ghi_db=True)
	frappe.clear_cache(doctype="Item")
