"""Lưới đỡ tài khoản tồn kho theo NHÓM MÓN (#307, anh Việt chốt 14/09/2026 chiều).

VÌ SAO CÓ TỆP NÀY
--------------------------------------------------------------------
Anh Việt đọc trực tiếp lõi ERPNext de591661 (comment trên PR #316) và
chốt ba điều:

1. `erpnext/controllers/stock_controller.py:258-270`, khi Company bật
   `enable_item_wise_inventory_account`, lõi lấy `inventory_account_map`
   theo món; KHÔNG có thì `frappe.throw("Please set default inventory
   account for item {0}, or their item group or brand.")`. KHÔNG quay về
   tài khoản của kho.
2. `stock_controller.py:2528-2571` tìm ba nấc: Item Default của món, rồi
   Item Group Default của nhóm món, rồi Brand.
3. `erpnext/setup/doctype/item_group/item_group.py:87-97`
   `get_item_group_defaults` chỉ đọc `item_group_defaults` của ĐÚNG nhóm
   ghi trên hồ sơ món, KHÔNG leo lên nhóm cha.

Hệ quả: ngày bật cờ, món nào không có tài khoản ở cả ba nấc là chứng từ bị
chặn. Lưới đỡ này gán tài khoản cho TỪNG NHÓM LÁ đang có món theo tồn,
theo nhóm gốc của cây: "Mua vào" trỏ 152, "Bán ra" trỏ 1551, "Sản xuất"
chia hai nhánh: bán thành phẩm trỏ tài khoản BTP cấp 1 trong Vagabond
Settings, còn lại (thành phẩm) trỏ 1551.

KHÔNG ĐOÁN TÊN TỪ TRÍ NHỚ
--------------------------------------------------------------------
Phiên viết tệp này chạy trên GitHub Actions, không đọc được site. Vì vậy
tệp KHÔNG ghim tên nhóm lá hay tên tài khoản thật. Nó chỉ ghim ba chữ nhóm
gốc và ba số hiệu tài khoản anh Việt nêu, rồi đọc cây nhóm và bảng tài
khoản từ site lúc chạy. `xem_bang()` in ra bảng dự kiến để dán lên PR cho
anh Việt và Khải duyệt; `ap_dung()` chỉ ghi đúng những dòng bảng đó nói
"sẽ gán". Không tìm được tài khoản duy nhất cho một số hiệu thì dòng đó
ghi "bỏ qua" kèm lý do, không đoán.

Phần thuần nằm trên vạch `import frappe`.
"""

# phần thuần

# Ba nhóm gốc anh Việt nêu, so không phân biệt hoa thường và khoảng trắng.
GOC_MUA_VAO = "mua vào"
GOC_BAN_RA = "bán ra"
GOC_SAN_XUAT = "sản xuất"

# Số hiệu tài khoản cho từng gốc. Sản xuất chia hai nhánh ở `tai_khoan_du_kien`.
SO_HIEU_MUA_VAO = "152"
SO_HIEU_THANH_PHAM = "1551"

# Nhánh con của "Sản xuất" mang bán thành phẩm: tên bắt đầu bằng chữ này.
CHU_NHANH_BTP = "bán thành phẩm"

# Ô cấu hình tài khoản BTP cấp 1 trên Vagabond Settings (cùng tai_khoan_btp).
O_BTP_CAP1 = "tk_ton_btp_cap1"

GAN = "gan"          # sẽ ghi tài khoản vào Item Group Default
GIU = "giu"          # nhóm đã có tài khoản khai tay: không đè
BO_QUA = "bo_qua"    # không xác định được tài khoản hoặc nhóm ngoài ba gốc


def _chu(v):
	return " ".join((v or "").split()).strip().lower()


def duong_len_goc(nhom, cha):
	"""Danh sách [nhóm, cha, ông, ..., gốc]. THUẦN.

	`cha` là dict tên nhóm -> tên nhóm cha ("" hoặc None ở gốc). Cắt vòng
	lặp ở 12 cấp để dữ liệu hỏng không treo patch.
	"""
	duong = [nhom]
	x = nhom
	for _ in range(12):
		x = (cha or {}).get(x) or ""
		if not x or x in duong:
			break
		duong.append(x)
	return duong


def nhom_goc_va_nhanh(nhom, cha):
	"""(gốc nghiệp vụ, nhánh ngay dưới gốc) của một nhóm, hoặc (None, None). THUẦN.

	Gốc nghiệp vụ là nhóm đầu tiên trên đường đi lên có tên là một trong ba
	chữ GOC_*; nhóm "All Item Groups" của Frappe nằm trên nữa nên không
	tính. Nhánh là nhóm ngay dưới gốc trên đường đi (chính nó nếu nhóm là
	con trực tiếp của gốc).
	"""
	duong = duong_len_goc(nhom, cha)
	for i, ten in enumerate(duong):
		g = _chu(ten)
		if g in (GOC_MUA_VAO, GOC_BAN_RA, GOC_SAN_XUAT):
			nhanh = duong[i - 1] if i > 0 else None
			return g, nhanh
	return None, None


def tai_khoan_du_kien(nhom, cha, tk_theo_so, tk_btp_cap1):
	"""Tài khoản dự kiến cho một nhóm và lý do. THUẦN.

	`tk_theo_so` là dict số hiệu -> tên tài khoản DUY NHẤT (None khi site
	không có hoặc có nhiều hơn một tài khoản chi tiết còn dùng mang số đó).
	Trả về (tai_khoan hoặc None, ly_do).
	"""
	goc, nhanh = nhom_goc_va_nhanh(nhom, cha)
	if goc is None:
		return None, "không thuộc ba gốc Mua vào, Bán ra, Sản xuất"
	if goc == GOC_MUA_VAO:
		so = SO_HIEU_MUA_VAO
	elif goc == GOC_BAN_RA:
		so = SO_HIEU_THANH_PHAM
	elif nhanh is not None and _chu(nhanh).startswith(CHU_NHANH_BTP):
		tk = (tk_btp_cap1 or "").strip() or None
		if not tk:
			return None, "gốc Sản xuất nhánh BTP nhưng ô %s trên Vagabond Settings trống" % O_BTP_CAP1
		return tk, "gốc Sản xuất, nhánh %s: tài khoản BTP cấp 1" % nhanh
	elif nhanh is None:
		return None, "chính là nhóm gốc Sản xuất, không gán cho gốc"
	else:
		so = SO_HIEU_THANH_PHAM
	tk = (tk_theo_so or {}).get(so)
	if not tk:
		return None, "gốc %s cần tài khoản %s nhưng site không có đúng một tài khoản chi tiết còn dùng mang số đó" % (goc, so)
	return tk, "gốc %s: tài khoản %s" % (goc, so)


def tai_khoan_duy_nhat(cac_tk):
	"""Số hiệu -> tên tài khoản khi số đó có ĐÚNG MỘT tài khoản chi tiết còn dùng. THUẦN."""
	dem = {}
	for t in cac_tk or []:
		if t.get("is_group") or t.get("disabled"):
			continue
		so = str(t.get("account_number") or "").strip()
		if so:
			dem.setdefault(so, []).append(t.get("name"))
	return {so: ten[0] for so, ten in dem.items() if len(ten) == 1}


def quyet_nhom(tk_hien_co, tk_du_kien, ly_do):
	"""Làm gì với một nhóm lá. THUẦN. Trả về dict(hanh_dong, tai_khoan, ly_do)."""
	tk_hien_co = (tk_hien_co or "").strip() or None
	if tk_hien_co:
		if tk_hien_co == tk_du_kien:
			return dict(hanh_dong=BO_QUA, tai_khoan=tk_hien_co, ly_do="đã đúng, không đổi")
		return dict(hanh_dong=GIU, tai_khoan=tk_hien_co,
			ly_do="nhóm đã có tài khoản khai tay, giữ (dự kiến %s)" % (tk_du_kien or "không có"))
	if not tk_du_kien:
		return dict(hanh_dong=BO_QUA, tai_khoan=None, ly_do=ly_do)
	return dict(hanh_dong=GAN, tai_khoan=tk_du_kien, ly_do=ly_do)


def bang_du_kien(nhom_co_ton, cha, tk_nhom_hien_co, tk_theo_so, tk_btp_cap1):
	"""Bảng dự kiến cho mọi nhóm đang có món theo tồn. THUẦN.

	`nhom_co_ton` là dict tên nhóm -> số món theo tồn; `tk_nhom_hien_co` là
	dict tên nhóm -> tài khoản đang khai trên Item Group Default của công ty.
	Trả về danh sách dict đã sắp theo tên nhóm.
	"""
	ra = []
	for nhom in sorted(nhom_co_ton or {}):
		if not nhom_co_ton[nhom]:
			continue
		tk, ly_do = tai_khoan_du_kien(nhom, cha, tk_theo_so, tk_btp_cap1)
		q = quyet_nhom((tk_nhom_hien_co or {}).get(nhom), tk, ly_do)
		goc, nhanh = nhom_goc_va_nhanh(nhom, cha)
		ra.append(dict(nhom=nhom, so_mon=nhom_co_ton[nhom], goc=goc, nhanh=nhanh,
			tk_hien_co=(tk_nhom_hien_co or {}).get(nhom), **q))
	return ra


def bang_markdown(bang):
	"""Bảng Markdown để dán lên PR. THUẦN."""
	dong = ["| Nhóm lá | Món theo tồn | Gốc | Nhánh | Đang có | Hành động | Tài khoản | Lý do |",
		"|---|---|---|---|---|---|---|---|"]
	for r in bang:
		dong.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
			r["nhom"], r["so_mon"], r.get("goc") or "", r.get("nhanh") or "",
			r.get("tk_hien_co") or "", r["hanh_dong"], r.get("tai_khoan") or "", r["ly_do"]))
	return "\n".join(dong)


# phần chạm Frappe
import frappe

from vagabond.tai_khoan_btp import TRUONG_ITEM_DEFAULT, co_o_item_default, cong_ty_ap_dung, doc_cau_hinh


def doc_du_lieu(cong_ty=None):
	"""Đọc cây nhóm, số món theo tồn, tài khoản đã khai và bảng tài khoản từ site."""
	cau_hinh = doc_cau_hinh()
	cong_ty = cong_ty or cong_ty_ap_dung(cau_hinh)
	cha = {g.name: g.parent_item_group for g in frappe.get_all("Item Group",
		fields=["name", "parent_item_group"], limit_page_length=0)}
	nhom_co_ton = {}
	for r in frappe.get_all("Item", filters={"is_stock_item": 1, "disabled": 0},
			fields=["item_group", "count(name) as so"], group_by="item_group"):
		if r.item_group:
			nhom_co_ton[r.item_group] = int(r.so or 0)
	tk_nhom = {}
	for r in frappe.get_all("Item Default", filters={"parenttype": "Item Group", "company": cong_ty},
			fields=["parent", TRUONG_ITEM_DEFAULT]):
		if r.get(TRUONG_ITEM_DEFAULT):
			tk_nhom[r.parent] = r.get(TRUONG_ITEM_DEFAULT)
	cac_tk = frappe.get_all("Account", filters={"company": cong_ty, "account_type": "Stock"},
		fields=["name", "account_number", "is_group", "disabled"], limit_page_length=0)
	return dict(cong_ty=cong_ty, cha=cha, nhom_co_ton=nhom_co_ton, tk_nhom=tk_nhom,
		tk_theo_so=tai_khoan_duy_nhat(cac_tk), tk_btp_cap1=cau_hinh.get(O_BTP_CAP1))


def xem_bang(cong_ty=None):
	"""CHỈ ĐỌC. Chạy `bench --site <site> execute vagabond.luoi_do_nhom.xem_bang`
	rồi dán bảng lên PR cho anh Việt và Khải duyệt trước khi phát hành patch."""
	d = doc_du_lieu(cong_ty)
	bang = bang_du_kien(d["nhom_co_ton"], d["cha"], d["tk_nhom"], d["tk_theo_so"], d["tk_btp_cap1"])
	md = bang_markdown(bang)
	print("Công ty: %s; tài khoản duy nhất theo số: %s; BTP cấp 1: %s" % (
		d["cong_ty"], d["tk_theo_so"], d["tk_btp_cap1"]))
	print(md)
	return bang


def ap_dung(cong_ty=None):
	"""Ghi Item Group Default cho các dòng GAN. Idempotent, không đè khai tay.

	Ghi thẳng dòng Item Default (parenttype Item Group), không save() Item
	Group để không kích validate cây nhóm trên dữ liệu cũ. Trả về bảng và
	bộ đếm để patch in ra.
	"""
	if not co_o_item_default():
		frappe.throw("Item Default không có ô %s. Đối chiếu lại lõi ERPNext trước khi "
			"phát hành lưới đỡ #307." % TRUONG_ITEM_DEFAULT)
	d = doc_du_lieu(cong_ty)
	bang = bang_du_kien(d["nhom_co_ton"], d["cha"], d["tk_nhom"], d["tk_theo_so"], d["tk_btp_cap1"])
	dem = {GAN: 0, GIU: 0, BO_QUA: 0, "loi": 0}
	for r in bang:
		if r["hanh_dong"] != GAN:
			dem[r["hanh_dong"]] += 1
			continue
		try:
			ten_dong = frappe.db.get_value("Item Default", {"parenttype": "Item Group",
				"parent": r["nhom"], "company": d["cong_ty"]}, "name")
			if ten_dong:
				frappe.db.set_value("Item Default", ten_dong, TRUONG_ITEM_DEFAULT, r["tai_khoan"],
					update_modified=False)
			else:
				dong = frappe.get_doc({"doctype": "Item Default", "parent": r["nhom"],
					"parenttype": "Item Group", "parentfield": "item_group_defaults",
					"company": d["cong_ty"], TRUONG_ITEM_DEFAULT: r["tai_khoan"],
					"idx": 1 + frappe.db.count("Item Default", {"parenttype": "Item Group",
						"parent": r["nhom"]})})
				dong.db_insert()
			dem[GAN] += 1
		except Exception:
			dem["loi"] += 1
			frappe.log_error(frappe.get_traceback(), "luoi_do_nhom %s" % r["nhom"])
	frappe.clear_cache(doctype="Item Group")
	return dict(bang=bang, dem=dem)
