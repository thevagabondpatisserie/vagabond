"""Cây kho bốn chặng của bếp và luật chọn kho nguồn khi nổ lệnh sản xuất.

Khải chốt 21/08/2026: mỗi bếp đi bốn chặng, mỗi chặng một kho, và kho nào
lấy hàng từ kho nào phải cố định thành luật chứ không để người tạo lệnh tự
chọn. Nguyên liệu về kho tổng 307 do anh Kiên giữ, chuyển sang kho nguyên
liệu của bếp, rồi đi lên dần:

    Kho tổng 307 (Kiên)
        v  chuyển kho nội bộ
    <Bếp> - Nguyên liệu          chặng nguyen_lieu
        v
    <Bếp> - BTP sơ cấp           lấy từ Nguyên liệu
        v
    <Bếp> - BTP sẵn sàng         lấy từ BTP sơ cấp, cộng Nguyên liệu
        v
    <Bếp> - Thành phẩm           lấy từ BTP sẵn sàng, cộng Nguyên liệu

VÌ SAO 307 KHÔNG LÀM KHO CHA
----------------------------
Đề bài ban đầu đặt `Kho tổng 307 - TV` làm kho cha của cả cây. Không làm
được: nó đang là kho lá và đã có 775 dòng sổ kho, 282 bản ghi tồn. ERPNext
từ chối đổi một kho đã phát sinh giao dịch thành kho nhóm, đúng câu
"Warehouses with existing transaction can not be converted to group" trong
`erpnext/stock/doctype/warehouse/warehouse.py`. Cùng một cái bẫy với TK 331
hôm 21/08, chỉ khác bảng.

Nên 307 đứng NGANG HÀNG, giữ vai kho nguyên liệu gốc; hai kho nhóm
`Bếp Baker - TV` và `Bếp Pastry - TV` vốn đã là kho nhóm sẵn thì làm cha cho
bốn kho lá của từng bếp. Luật backflush không đổi một dòng nào.

LUẬT NÀY CÀI Ở ĐÂU
------------------
Ở hook `validate` của Work Order chứ không ở chỗ tạo lệnh trên app. Lệnh sản
xuất sinh ra từ ít nhất bốn đường: màn Tạo lệnh, màn Bán thành phẩm cần làm,
mô đun phantom, và tay người trên Desk. Sửa một đường là ba đường kia vẫn
lấy sai kho, mà sai kho thì trừ nhầm tồn của bếp khác - không ai thấy cho
tới lúc kiểm kê.
"""

import frappe
from frappe.utils import cint

# Bốn chặng, theo đúng thứ tự đi lên.
NGUYEN_LIEU = "nguyen_lieu"
BTP_SO_CAP = "btp_so_cap"
BTP_SAN_SANG = "btp_san_sang"
THANH_PHAM = "thanh_pham"
CAC_CHANG = (NGUYEN_LIEU, BTP_SO_CAP, BTP_SAN_SANG, THANH_PHAM)

TEN_CHANG = {
	NGUYEN_LIEU: "Nguyên liệu",
	BTP_SO_CAP: "BTP sơ cấp",
	BTP_SAN_SANG: "BTP sẵn sàng",
	THANH_PHAM: "Thành phẩm",
}

# Kho của chặng nào lấy hàng từ chặng nào. Khoá là chặng của MÓN ĐANG LÀM,
# giá trị là danh sách chặng được phép lấy nguyên liệu, xếp theo thứ tự ưu
# tiên. Đọc ngược lại bảng của Khải: dòng "Thành phẩm" ghi "blf từ BTP sẵn
# sàng + Nguyên liệu" thành ra [BTP_SAN_SANG, NGUYEN_LIEU].
LUAT_NGUON = {
	BTP_SO_CAP: [NGUYEN_LIEU],
	BTP_SAN_SANG: [BTP_SO_CAP, NGUYEN_LIEU],
	THANH_PHAM: [BTP_SAN_SANG, BTP_SO_CAP, NGUYEN_LIEU],
}

# Hai bếp, kèm tiền tố tên kho và người giữ kho.
BEP = {
	"baker": {"ten": "Baker", "kho_nhom": "Bếp Baker - TV"},
	"pastry": {"ten": "Pastry", "kho_nhom": "Bếp Pastry - TV"},
}

# Kho lá của từng bếp theo chặng. Tên kho ĐÃ CÓ giữ nguyên, hai kho mới đặt
# theo đúng nếp cũ "<Bếp> - <Chức năng>" để máy ghép hậu tố " - TV".
#
# Đề bài viết "Baker - BTP TV - sẵn sàng". Đặt đúng chữ đó thì ERPNext tự
# nối thêm hậu tố công ty thành "Baker - BTP TV - sẵn sàng - TV", hai chữ TV
# trong một tên. Nên rút còn "BTP sẵn sàng", tên đầy đủ ra
# "Baker - BTP sẵn sàng - TV". Đổi lại được nếu Khải muốn khác.
TEN_KHO = {
	NGUYEN_LIEU: "%s - Nguyên liệu",
	BTP_SO_CAP: "%s - BTP sơ cấp",
	BTP_SAN_SANG: "%s - BTP sẵn sàng",
	THANH_PHAM: "%s - Thành phẩm",
}

# Kho nguyên liệu gốc, nơi hàng mua về nằm trước khi chuyển sang bếp.
KHO_GOC = "Kho tổng 307 - TV"

# Tiền tố mã hàng nào thuộc chặng nào. Bảng tiền tố đã được anh Việt đóng
# băng trong phiếu duyệt quy ước dữ liệu chủ ngày 05/08/2026.
TIEN_TO_NGUYEN_LIEU = ("NVLT", "BPKG", "CCDC", "VVPP")
TIEN_TO_BTP = ("BTPB", "BTPN", "NBTP")
TIEN_TO_THANH_PHAM = ("BAWC", "BANU", "BAEN", "BACF", "BAWS", "BASS")

QUYEN = ("System Manager", "Manufacturing Manager", "Giám đốc", "AP Giám đốc")

# Chu trong ten mon de khai thang chang. Anh Viet chot 25/08/2026:
# "Cap 1 = kho so cap, Cap 2 = kho san sang".
CHU_CAP = ((BTP_SO_CAP, "cấp 1"), (BTP_SAN_SANG, "cấp 2"))

TRUONG_MOI = {"Item": [
	{
		"fieldname": "custom_chang_btp", "label": "Chặng bán thành phẩm",
		"fieldtype": "Select",
		"options": "\nbtp_so_cap\nbtp_san_sang",
		"insert_after": "item_group",
		"description": "Món này nhập vào kho BTP sơ cấp hay kho BTP sẵn sàng. "
			"Khai ở đây thì máy nghe theo, không suy từ công thức nữa. "
			"Để trống thì máy vẫn suy như cũ.",
	},
], "Warehouse": [
	{
		"fieldname": "custom_nguoi_phu_trach", "label": "Người phụ trách kho",
		"fieldtype": "Link", "options": "User", "insert_after": "warehouse_name",
		"description": "Người giữ kho này. Dùng để biết hỏi ai khi tồn lệch.",
	},
	{
		"fieldname": "custom_chang", "label": "Chặng sản xuất",
		"fieldtype": "Select",
		"options": "\nnguyen_lieu\nbtp_so_cap\nbtp_san_sang\nthanh_pham",
		"insert_after": "custom_nguoi_phu_trach",
		"description": "Kho này đứng ở chặng nào trong bốn chặng của bếp. "
			"Để trống nghĩa là kho ngoài dây chuyền sản xuất.",
	},
	{
		"fieldname": "custom_kho_nguon", "label": "Kho nguồn chính",
		"fieldtype": "Link", "options": "Warehouse",
		"insert_after": "custom_chang",
		"description": "Khi làm món ở kho này, máy lấy nguyên liệu từ kho này trước.",
	},
	{
		"fieldname": "custom_kho_nguon_phu", "label": "Kho nguồn phụ",
		"fieldtype": "Link", "options": "Warehouse",
		"insert_after": "custom_kho_nguon",
		"description": "Thiếu ở kho nguồn chính thì tìm tiếp ở đây.",
	},
]}


# ---------------------------------------------------------------- phép thuần


def chang_theo_tien_to(ma):
	"""Chặng đoán từ tiền tố mã hàng. Bán thành phẩm trả về None vì còn phải
	nhìn công thức mới biết sơ cấp hay sẵn sàng."""
	ma = (ma or "").strip().upper()
	if not ma:
		return None
	for t in TIEN_TO_NGUYEN_LIEU:
		if ma.startswith(t):
			return NGUYEN_LIEU
	for t in TIEN_TO_THANH_PHAM:
		if ma.startswith(t):
			return THANH_PHAM
	for t in TIEN_TO_BTP:
		if ma.startswith(t):
			return None
	return None


def chang_theo_ten(ten):
	"""Chặng đọc thẳng từ tên món, khi tên có ghi rõ cấp.

	64 mã bánh ổ mang sẵn chữ "Cấp 1" hoặc "Cấp 2" trong tên. Anh Việt chốt
	25/08/2026: cấp 1 vào kho sơ cấp, cấp 2 vào kho sẵn sàng. Tên nói rõ thì
	không việc gì phải suy từ công thức.
	"""
	t = (ten or "").strip().lower()
	if not t:
		return None
	for chang, chu in CHU_CAP:
		if chu in t:
			return chang
	return None


def chang_cua_mon(ma, co_btp_con, khai_tay=None, ten=None):
	"""Chặng của một món. Bốn nấc, nấc trên thắng nấc dưới.

	1. `khai_tay` - ô "Chặng bán thành phẩm" người khai trên hồ sơ món.
	   Người biết món đó đi kho nào rõ hơn máy, nên khai rồi thì máy im.
	2. Tiền tố mã - nguyên vật liệu và thành phẩm thì tiền tố đã nói hết.
	3. Chữ cấp trong `ten` - 64 mã bánh ổ mang sẵn "Cấp 1" hoặc "Cấp 2".
	   Anh Việt chốt 25/08/2026: cấp 1 vào kho sơ cấp, cấp 2 vào kho sẵn
	   sàng. Tên đã nói rõ thì không việc gì phải suy.
	4. Cấu trúc công thức - `co_btp_con` là True khi công thức có ít nhất
	   một dòng là bán thành phẩm. Món chỉ ghép từ nguyên liệu thô là sơ
	   cấp, món ăn thêm bán thành phẩm khác là đã ở chặng sẵn sàng.

	Đặt nấc 3 TRÊN nấc 4 là có chủ ý. Suy từ công thức đọc được cấu trúc
	nhưng không đọc được ý người đặt tên, mà tên là thứ bếp nhìn vào.
	"""
	kt = (khai_tay or "").strip()
	if kt in (BTP_SO_CAP, BTP_SAN_SANG):
		return kt
	c = chang_theo_tien_to(ma)
	if c:
		return c
	ma = (ma or "").strip().upper()
	for t in TIEN_TO_BTP:
		if ma.startswith(t):
			return chang_theo_ten(ten) or (
				BTP_SAN_SANG if co_btp_con else BTP_SO_CAP)
	return None


def ten_kho_cua(bep, chang, hau_to=" - TV"):
	"""Tên kho lá của một bếp ở một chặng."""
	b = BEP.get((bep or "").lower())
	if not b or chang not in TEN_KHO:
		return None
	return (TEN_KHO[chang] % b["ten"]) + hau_to


def bep_cua_kho(ten_kho):
	"""Đọc ngược tên kho ra tên bếp."""
	t = (ten_kho or "").strip().lower()
	for ma_bep, b in BEP.items():
		if t.startswith(b["ten"].lower() + " -"):
			return ma_bep
	return None


def chon_kho_nguon(chang_mon_lam, chang_nguyen_lieu, bep, ton_theo_kho=None):
	"""Kho nào cấp nguyên liệu này cho lệnh đang làm.

	`chang_mon_lam` là chặng của món đầu ra, `chang_nguyen_lieu` là chặng của
	dòng nguyên liệu. Trả về tên kho, hoặc None nếu luật không phủ tới (để
	nguyên kho mà người tạo lệnh đã chọn, không tự ý đổi).

	`ton_theo_kho` nếu có là bảng {tên kho: số tồn}: cùng một chặng mà kho
	đầu hết hàng thì thử kho tiếp theo trong luật. Không truyền thì lấy kho
	đầu tiên đúng luật.
	"""
	uu_tien = LUAT_NGUON.get(chang_mon_lam)
	if not uu_tien or not chang_nguyen_lieu:
		return None
	if chang_nguyen_lieu not in uu_tien:
		return None
	kho = ten_kho_cua(bep, chang_nguyen_lieu)
	if not kho:
		return None
	if ton_theo_kho is not None and not ton_theo_kho.get(kho):
		for c in uu_tien:
			k2 = ten_kho_cua(bep, c)
			if k2 and ton_theo_kho.get(k2):
				return k2
	return kho


def khai_cay_kho():
	"""Bản khai đầy đủ tám kho lá, dùng chung cho việc dựng và việc kiểm."""
	ra = []
	for ma_bep, b in BEP.items():
		for chang in CAC_CHANG:
			nguon = LUAT_NGUON.get(chang) or []
			ra.append({
				"bep": ma_bep,
				"chang": chang,
				"ten": ten_kho_cua(ma_bep, chang),
				"cha": b["kho_nhom"],
				"kho_nguon": (ten_kho_cua(ma_bep, nguon[0]) if nguon else KHO_GOC),
				"kho_nguon_phu": (ten_kho_cua(ma_bep, nguon[1]) if len(nguon) > 1 else None),
			})
	return ra


# ------------------------------------------------------- phần chạm hệ thống


def _chan():
	if not set(frappe.get_roles()) & set(QUYEN):
		frappe.throw("Chỉ quản lý sản xuất hoặc giám đốc mới sắp lại cây kho được.")


def _cong_ty():
	return frappe.defaults.get_user_default("Company") or frappe.db.get_value(
		"Company", {"name": ["!=", ""]}, "name")


def _co_btp_con(ma):
	"""Công thức đang chạy của món này có dòng nào là bán thành phẩm không."""
	bom = frappe.db.get_value("BOM", {
		"item": ma, "is_active": 1, "is_default": 1, "docstatus": 1}, "name")
	if not bom:
		bom = frappe.db.get_value("BOM", {"item": ma, "docstatus": 1}, "name")
	if not bom:
		return False
	for con in frappe.get_all("BOM Item", filters={"parent": bom}, pluck="item_code"):
		if chang_theo_tien_to(con) is None and (con or "").strip().upper().startswith(
				TIEN_TO_BTP):
			return True
	return False


def _ho_so_mon(ma):
	"""Ô khai tay và tên món, đọc một lần. Món lạ thì trả hai chuỗi rỗng."""
	try:
		r = frappe.db.get_value("Item", ma,
			["custom_chang_btp", "item_name"], as_dict=True) or {}
		return (r.get("custom_chang_btp") or ""), (r.get("item_name") or "")
	except Exception:
		return "", ""


def _bep_cua_mon(ma):
	"""Bếp phụ trách món, đọc ô custom_bep_phu_trach; chưa khai thì đoán theo
	công thức đang có, cuối cùng mới chịu thua trả None."""
	b = frappe.db.get_value("Item", ma, "custom_bep_phu_trach")
	if b:
		b = str(b).strip().lower()
		if b in BEP:
			return b
		for ma_bep, x in BEP.items():
			if x["ten"].lower() in b:
				return ma_bep
	return None


@frappe.whitelist()
def dung_cay_kho(chay_that=0, cong_ty=None):
	"""Dựng tám kho lá của hai bếp, khai người phụ trách và luật kho nguồn.

	Gọi trống là chạy thử, chỉ trả kế hoạch. Chạy lại lần hai không đổi gì
	thêm. KHÔNG đụng vào kho đã có ngoài việc điền các ô mới.
	"""
	_chan()
	chay_that = cint(chay_that)
	cong_ty = cong_ty or _cong_ty()
	ke = {"chay_that": chay_that, "cong_ty": cong_ty, "se_mo": [], "se_khai": [],
		"da_dung": [], "canh_bao": []}

	w307 = frappe.db.get_value("Warehouse", KHO_GOC, ["name", "is_group"], as_dict=True)
	if not w307:
		ke["canh_bao"].append("Không thấy %s. Dừng, không đoán bừa." % KHO_GOC)
		return ke

	for k in khai_cay_kho():
		if not frappe.db.exists("Warehouse", k["cha"]):
			ke["canh_bao"].append("Chưa có kho nhóm %s, bỏ qua nhánh này." % k["cha"])
			continue
		co = frappe.db.exists("Warehouse", k["ten"])
		if not co:
			ke["se_mo"].append(k["ten"])
		else:
			ke["da_dung"].append(k["ten"])
		ke["se_khai"].append({
			"kho": k["ten"], "chang": TEN_CHANG[k["chang"]],
			"nguon": k["kho_nguon"], "nguon_phu": k["kho_nguon_phu"],
		})

	if not chay_that:
		ke["ghi_chu"] = (
			"Chạy thử. Sẽ mở %d kho mới, khai lại chặng và kho nguồn cho %d kho. "
			"%s giữ nguyên là kho lá nguyên liệu gốc, không đổi thành kho nhóm "
			"vì đã có giao dịch. Muốn ghi thật thì truyền chay_that=1."
			% (len(ke["se_mo"]), len(ke["se_khai"]), KHO_GOC))
		return ke

	for k in khai_cay_kho():
		if not frappe.db.exists("Warehouse", k["cha"]):
			continue
		if not frappe.db.exists("Warehouse", k["ten"]):
			doc = frappe.new_doc("Warehouse")
			doc.warehouse_name = k["ten"].rsplit(" - ", 1)[0]
			doc.company = cong_ty
			doc.parent_warehouse = k["cha"]
			doc.is_group = 0
			doc.insert(ignore_permissions=True)
	# Khai các ô mới SAU khi đã mở đủ kho: ô kho nguồn là Link, trỏ vào một
	# kho chưa tồn tại thì Frappe chặn ngay lúc lưu.
	for k in khai_cay_kho():
		if not frappe.db.exists("Warehouse", k["ten"]):
			continue
		gia = {"custom_chang": k["chang"]}
		if frappe.db.exists("Warehouse", k["kho_nguon"] or ""):
			gia["custom_kho_nguon"] = k["kho_nguon"]
		if k["kho_nguon_phu"] and frappe.db.exists("Warehouse", k["kho_nguon_phu"]):
			gia["custom_kho_nguon_phu"] = k["kho_nguon_phu"]
		frappe.db.set_value("Warehouse", k["ten"], gia, update_modified=False)
		frappe.clear_document_cache("Warehouse", k["ten"])
	frappe.db.commit()
	ke["ghi_chu"] = (
		"Xong. Đã mở %d kho mới và khai luật kho nguồn cho %d kho. Người phụ "
		"trách khai riêng bằng cửa gan_nguoi_phu_trach."
		% (len(ke["se_mo"]), len(ke["se_khai"])))
	return ke


@frappe.whitelist()
def gan_nguoi_phu_trach(bang=None, chay_that=0):
	"""Gắn người giữ kho. `bang` là danh sách {kho, email}.

	Tách khỏi dung_cay_kho vì người thì đổi, còn cây kho thì không.
	"""
	_chan()
	chay_that = cint(chay_that)
	if isinstance(bang, str):
		import json as _json
		bang = _json.loads(bang)
	bang = bang or []
	ke = {"chay_that": chay_that, "se_gan": [], "khong_thay": []}
	for d in bang:
		kho, email = (d.get("kho") or "").strip(), (d.get("email") or "").strip()
		if not frappe.db.exists("Warehouse", kho):
			ke["khong_thay"].append("kho " + kho)
			continue
		if email and not frappe.db.exists("User", email):
			ke["khong_thay"].append("người " + email)
			continue
		ke["se_gan"].append({"kho": kho, "email": email})
		if chay_that:
			frappe.db.set_value("Warehouse", kho, "custom_nguoi_phu_trach",
				email or None, update_modified=False)
			frappe.clear_document_cache("Warehouse", kho)
	if chay_that:
		frappe.db.commit()
	return ke


@frappe.whitelist()
def gan_chang_theo_ten(chay_that=0, gioi_han=1000):
	"""Cửa cho người gọi. Xem `_gan_chang_theo_ten`."""
	_chan()
	return _gan_chang_theo_ten(chay_that, gioi_han)


def _gan_chang_theo_ten(chay_that=0, gioi_han=1000):
	"""Khai chặng cho các món có ghi rõ cấp ngay trong tên.

	Anh Việt chốt 25/08/2026: cấp 1 vào kho sơ cấp, cấp 2 vào kho sẵn sàng.
	64 mã bánh ổ đã mang sẵn chữ đó trong tên nên khai được ngay, không phải
	chờ Khải duyệt. Các món không có chữ cấp trong tên thì tệp này KHÔNG
	đụng tới: chờ bảng duyệt của Khải.

	Gọi trống là chạy thử, chỉ trả kế hoạch. Lặp lại được. Món đã khai tay
	rồi thì giữ nguyên, không ghi đè lên quyết định của người.
	"""
	chay_that = cint(chay_that)
	gioi_han = cint(gioi_han) or 1000
	ds = frappe.get_all("Item", filters={"disabled": 0}, or_filters=[
		["item_code", "like", t + "%"] for t in TIEN_TO_BTP
	], fields=["name", "item_name", "custom_chang_btp"], limit=gioi_han,
		order_by="name asc")
	ra = {"chay_that": chay_that, "se_khai": [], "da_khai": [],
		"khong_co_chu_cap": 0}
	for it in ds:
		c = chang_theo_ten(it.item_name)
		if not c:
			ra["khong_co_chu_cap"] += 1
			continue
		cu = (it.get("custom_chang_btp") or "").strip()
		if cu:
			ra["da_khai"].append({"ma": it.name, "chang": cu})
			continue
		ra["se_khai"].append({"ma": it.name, "ten": it.item_name,
			"chang": TEN_CHANG[c]})
		if chay_that:
			frappe.db.set_value("Item", it.name, "custom_chang_btp", c,
				update_modified=False)
			frappe.clear_document_cache("Item", it.name)
	if chay_that:
		frappe.db.commit()
	ra["ghi_chu"] = (
		"%s. Khai %d món theo chữ cấp trong tên, %d món đã khai từ trước, "
		"%d món không có chữ cấp nên để nguyên chờ bảng duyệt của Khải."
		% ("Đã ghi" if chay_that else "Chạy thử, chưa ghi gì",
			len(ra["se_khai"]), len(ra["da_khai"]), ra["khong_co_chu_cap"]))
	return ra


@frappe.whitelist()
def soat_chang(gioi_han=400):
	"""Xếp mọi bán thành phẩm vào chặng sơ cấp hay sẵn sàng, KHÔNG ghi gì.

	Bảng này để bếp trưởng đọc và chốt. Máy suy từ cấu trúc công thức chứ
	không đoán: món chỉ ghép từ nguyên liệu thô là sơ cấp, món có ăn thêm bán
	thành phẩm khác là sẵn sàng. Món chưa có công thức thì máy nói thẳng là
	chưa biết, không xếp bừa.
	"""
	_chan()
	gioi_han = cint(gioi_han) or 400
	# Loc theo CA BA tien to ban thanh pham. Bo loc cu la "BTP%" nen bo sot
	# sach nhom NBTP - dung 64 ma banh o co chu Cap 1 va Cap 2 trong ten.
	ds = frappe.get_all("Item", filters={"disabled": 0}, or_filters=[
		["item_code", "like", t + "%"] for t in TIEN_TO_BTP
	], fields=["name", "item_name", "custom_bep_phu_trach",
		"custom_chang_btp"], limit=gioi_han, order_by="name asc")
	ra = {"so_cap": [], "san_sang": [], "chua_co_cong_thuc": []}
	for it in ds:
		bom = frappe.db.get_value("BOM", {"item": it.name, "docstatus": 1}, "name")
		if not bom:
			ra["chua_co_cong_thuc"].append({"ma": it.name, "ten": it.item_name})
			continue
		c = chang_cua_mon(it.name, _co_btp_con(it.name),
			it.get("custom_chang_btp"), it.item_name)
		muc = "san_sang" if c == BTP_SAN_SANG else "so_cap"
		ra[muc].append({"ma": it.name, "ten": it.item_name,
			"bep": it.custom_bep_phu_trach or ""})
	ra["ghi_chu"] = (
		"Suy từ cấu trúc công thức, chưa ghi vào đâu cả. Bếp trưởng đọc rồi "
		"chốt, sai chỗ nào báo lại chỗ đó.")
	return ra


def gan_kho_nguon(doc, method=None):
	"""Hook validate Work Order: mỗi dòng nguyên liệu lấy đúng kho của chặng.

	Bọc try/except: lấy đúng kho là tốt, nhưng hỏng chuyện này thì tuyệt đối
	không được chặn bếp tạo lệnh. Hỏng thì giữ nguyên kho mà người tạo lệnh
	đã chọn, y như trước khi có luật này.
	"""
	try:
		if not doc.get("required_items"):
			return
		bep = _bep_cua_mon(doc.production_item)
		if not bep:
			# Chưa khai bếp phụ trách thì đoán theo kho thành phẩm đang chọn.
			bep = bep_cua_kho(doc.get("fg_warehouse") or "")
		if not bep:
			return
		kt_ra, ten_ra = _ho_so_mon(doc.production_item)
		chang_ra = chang_cua_mon(doc.production_item,
			_co_btp_con(doc.production_item), kt_ra, ten_ra)
		if not chang_ra:
			return
		for d in doc.required_items:
			kt_nl, ten_nl = _ho_so_mon(d.item_code)
			chang_nl = chang_cua_mon(d.item_code, _co_btp_con(d.item_code),
				kt_nl, ten_nl)
			kho = chon_kho_nguon(chang_ra, chang_nl, bep)
			if kho and frappe.db.exists("Warehouse", kho):
				d.source_warehouse = kho
	except Exception:
		frappe.log_error(frappe.get_traceback(),
			"vagabond: gan kho nguon theo chang")
