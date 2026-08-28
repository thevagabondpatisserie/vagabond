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

CÂY BỐN CHẶNG TRÊN LÀ LỊCH SỬ, KHÔNG CÒN CHẠY
---------------------------------------------
Anh Việt chốt 28/08/2026: bỏ hẳn phương án chuyển hàng qua kho trung gian.
Hai kho BTP sơ cấp và BTP sẵn sàng của cả hai bếp đã tắt, mọi lệnh rút
nguyên liệu từ kho Nguyên liệu của bếp và cũng nhập trả về đó, trừ thành
phẩm thì nhập kho Thành phẩm. Xem ghi chú dài ở `LUAT_NGUON` phía dưới.

Giữ sơ đồ cũ ở đây để đọc lại được ý ban đầu, chứ đừng dựng lại theo nó.

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
from frappe.utils import cint, flt

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
#
# ĐỔI LUẬT 28/08/2026: RÚT TUỘT TỪ KHO NGUYÊN LIỆU
# ------------------------------------------------
# Khải đề nghị tắt hẳn hai kho logic BTP sơ cấp và BTP sẵn sàng ở cả hai
# bếp, anh Việt chốt. Từ nay mọi lệnh lấy nguyên liệu từ MỘT kho duy nhất
# là kho Nguyên liệu của bếp, và cũng nhập trả về đó, trừ thành phẩm thì
# nhập kho Thành phẩm.
#
# Vì sao đổi, đo trên site ngày 28/08:
#
# * Bốn kho trung gian (hai bếp nhân hai chặng) có 23 bản ghi tồn kho mà
#   tồn đều bằng 0, và KHÔNG MỘT BÚT TOÁN KHO NÀO từng đi qua chúng. Dựng
#   ra từ 21/08 tới giờ chưa hàng nào ghé.
# * Sáu lệnh sản xuất từng trỏ vào chúng thì cả sáu đã bị huỷ. Đó chính là
#   những lệnh Khải thử rồi gặp "thiếu nguyên liệu" - luật cũ bảo lấy hàng
#   từ kho sơ cấp, mà kho đó rỗng nên ERPNext báo thiếu, hoàn toàn đúng.
# * Hàng thật nằm ở kho Nguyên liệu: Pastry 132 mã có tồn, Baker 84 mã.
#
# Nói cách khác bếp KHÔNG chuyển hàng qua kho trung gian trên thực tế. Giữ
# một luật đòi hàng ở nơi không có hàng thì luật đó chỉ làm bếp đứng.
#
# PHƯƠNG ÁN CHUYỂN KHO TRUNG GIAN: BỎ HẲN, KHÔNG DÙNG NỮA
# --------------------------------------------------------
# Anh Việt chốt 28/08/2026, sau khi Khải đề nghị: "phương án chuyển kho
# trung gian là bỏ luôn, không dùng nữa". Đây KHÔNG phải một công tắc tắt
# tạm chờ ngày bật lại. Bếp không đi qua kho trung gian trên thực tế, và
# một luật đòi hàng ở nơi không có hàng thì chỉ làm bếp đứng.
#
# Bản luật cũ chép lại đây để đọc lịch sử, ĐỪNG chép ngược lên trên:
#     BTP_SO_CAP:   [NGUYEN_LIEU]
#     BTP_SAN_SANG: [BTP_SO_CAP, NGUYEN_LIEU]
#     THANH_PHAM:   [BTP_SAN_SANG, BTP_SO_CAP, NGUYEN_LIEU]
# Ai muốn quay về bản đó thì phải hỏi anh Việt trước, vì quay về là bếp
# lại gặp đúng câu "thiếu nguyên liệu" mà Khải đã gặp sáu lần.
LUAT_NGUON = {
	BTP_SO_CAP: [NGUYEN_LIEU],
	BTP_SAN_SANG: [NGUYEN_LIEU],
	THANH_PHAM: [NGUYEN_LIEU],
}

# Chặng nào nhập hàng về kho nào. Chỉ thành phẩm mới rời kho Nguyên liệu.
LUAT_KHO_DICH = {
	BTP_SO_CAP: NGUYEN_LIEU,
	BTP_SAN_SANG: NGUYEN_LIEU,
	THANH_PHAM: THANH_PHAM,
}

# Hai chặng kho đã tắt hẳn. Giữ tên ở đây để hàm tắt kho và ca kiểm cùng
# đọc một chỗ, và để người sau biết bốn kho nào đang nằm im.
CHANG_TAT = (BTP_SO_CAP, BTP_SAN_SANG)

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


def kho_cua_lenh(chang_mon, bep, hau_to=" - TV"):
	"""Ba kho của một lệnh sản xuất. THUẦN.

	Trả (kho nguyên liệu, kho dở dang, kho đích). Thiếu dữ kiện thì trả ba
	giá trị None để người gọi giữ nguyên thứ người tạo lệnh đã chọn.

	Khải chốt 28/08/2026: kho dở dang đi CHUNG với kho nguyên liệu. Bếp
	không có khu vực dở dang riêng, bột trộn xong nằm ngay tại bàn cạnh
	kho nguyên liệu chứ không chuyển đi đâu. Tách ra một kho dở dang riêng
	chỉ đẻ thêm hai bút toán chuyển kho cho mỗi mẻ, không ai đọc.
	"""
	if not chang_mon or chang_mon not in LUAT_KHO_DICH:
		return (None, None, None)
	nguon = ten_kho_cua(bep, NGUYEN_LIEU, hau_to)
	dich = ten_kho_cua(bep, LUAT_KHO_DICH[chang_mon], hau_to)
	if not nguon or not dich:
		return (None, None, None)
	return (nguon, nguon, dich)


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


@frappe.whitelist()
def tat_kho_trung_gian(chay_that=0):
	"""Tắt bốn kho trung gian của hai bếp. Chạy thử là mặc định.

	Khải đề nghị 28/08/2026, anh Việt chốt. An toàn vì đo trên site cùng
	ngày: bốn kho này có 23 bản ghi tồn nhưng tồn đều 0, KHÔNG bút toán kho
	nào từng đi qua, không lệnh sản xuất còn hiệu lực nào trỏ vào, không hồ
	sơ món nào lấy chúng làm kho mặc định.

	Hàm TỰ KIỂM lại ba điều đó trước khi ghi chứ không tin vào lần đo hôm
	nay. Còn tồn hay còn bút toán là DỪNG: tắt một kho đang giữ hàng thật
	là làm hàng đó biến khỏi mọi màn hình mà sổ vẫn còn.

	Tắt chứ KHÔNG xoá. Xoá là mất đường tra lại, và sổ kho cũ trỏ vào một
	kho không còn tồn tại thì mọi màn đọc sổ đều vỡ. Tắt rồi thì kho biến
	khỏi mọi ô chọn nhưng vẫn tra lại được.
	"""
	_chan()
	chay_that = cint(chay_that)
	ke, can_dung = [], []
	for k in khai_cay_kho():
		if k["chang"] not in CHANG_TAT:
			continue
		ten = k["ten"]
		if not frappe.db.exists("Warehouse", ten):
			continue
		ton = sum(flt(b.actual_qty) for b in frappe.get_all(
			"Bin", filters={"warehouse": ten}, fields=["actual_qty"]))
		so_but_toan = frappe.db.count(
			"Stock Ledger Entry", {"warehouse": ten, "is_cancelled": 0})
		so_lenh = frappe.db.count(
			"Work Order", {"wip_warehouse": ten, "docstatus": ["<", 2]}) + frappe.db.count(
			"Work Order", {"fg_warehouse": ten, "docstatus": ["<", 2]}) + frappe.db.count(
			"Work Order", {"source_warehouse": ten, "docstatus": ["<", 2]})
		so_ho_so = frappe.db.count("Item Default", {"default_warehouse": ten})
		da_tat = cint(frappe.db.get_value("Warehouse", ten, "disabled"))
		vuong = []
		if abs(ton) > 0.0001:
			vuong.append("còn tồn %s" % ton)
		if so_but_toan:
			vuong.append("có %d bút toán kho" % so_but_toan)
		if so_lenh:
			vuong.append("có %d lệnh sản xuất đang trỏ vào" % so_lenh)
		if so_ho_so:
			vuong.append("có %d hồ sơ món lấy làm kho mặc định" % so_ho_so)
		dong = {"kho": ten, "da_tat": da_tat, "ton": ton,
			"but_toan": so_but_toan, "lenh": so_lenh, "ho_so": so_ho_so,
			"vuong": vuong}
		ke.append(dong)
		if vuong:
			can_dung.append(dong)
	if can_dung:
		return {"chay_that": chay_that, "da_tat": [], "ds": ke,
			"dung_vi": "Có kho còn vướng, không tắt kho nào cả.",
			"can_xem": can_dung}
	da = []
	if chay_that:
		for d in ke:
			if d["da_tat"]:
				continue
			frappe.db.set_value("Warehouse", d["kho"], "disabled", 1)
			da.append(d["kho"])
		frappe.db.commit()
	return {"chay_that": chay_that, "so_kho": len(ke),
		"da_tat": da, "se_tat": [d["kho"] for d in ke if not d["da_tat"]],
		"ds": ke}


def gan_kho_lenh(doc, method=None):
	"""Hook before_validate Work Order: điền sẵn ba ô kho theo món.

	Khải hỏi 28/08/2026: ba ô kho cứ phải chọn lại mỗi lần lập lệnh, gán
	chết theo mã món được không.

	Gán ở đây chứ không gán vào hồ sơ món, vì kho đúng phụ thuộc hai thứ:
	món thuộc chặng nào, và món của bếp nào. Ghi cứng một kho vào hồ sơ
	món thì mã nào dùng chung hai bếp là sai ngay, mà đổi luật kho sau này
	phải sửa lại từng mã một.

	CHỈ ĐIỀN Ô ĐANG TRỐNG. Người tạo lệnh đã chọn tay thì máy không đè -
	cùng một luật với hook giá và hook mã tham chiếu: máy không đè lên chữ
	người thật.
	"""
	try:
		if not doc.get("production_item"):
			return
		bep = _bep_cua_mon(doc.production_item) or bep_cua_kho(
			doc.get("fg_warehouse") or "")
		if not bep:
			return
		kt, ten = _ho_so_mon(doc.production_item)
		chang = chang_cua_mon(doc.production_item,
			_co_btp_con(doc.production_item), kt, ten)
		nguon, dd, dich = kho_cua_lenh(chang, bep)
		for o, gia_tri in (("source_warehouse", nguon),
				("wip_warehouse", dd), ("fg_warehouse", dich)):
			if gia_tri and not (doc.get(o) or "").strip():
				if frappe.db.exists("Warehouse", gia_tri):
					doc.set(o, gia_tri)
	except Exception:
		frappe.log_error(frappe.get_traceback(),
			"vagabond: gan ba kho cho lenh san xuat")


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
