# -*- coding: utf-8 -*-
"""Gom năm nhãn chặng cũ về hai tên, và màn theo dõi tồn kho theo chặng.

Khải chốt 28/08/2026, anh Việt duyệt: năm nhãn đang dùng

    Nguyên liệu · BTP thành phần · Ruột bánh (C1) · Bánh khuôn (C2) · Thành phẩm

gom lại còn HAI tên cho phần bán thành phẩm:

    BTP thành phần  +  Ruột bánh (C1)   ->  BTP sơ cấp
    Bánh khuôn (C2)                     ->  BTP sẵn sàng

Nguyên liệu và Thành phẩm giữ nguyên vì chúng không phải bán thành phẩm:
một cái là hàng mua vào, một cái là hàng bán ra. Gom nốt hai cái đó thì
không còn cách nào phân biệt hàng bán được với hàng đang làm dở.

VÌ SAO GOM Ở TẦNG HIỂN THỊ, KHÔNG SỬA 179 DÒNG DỮ LIỆU
------------------------------------------------------
Nhãn chặng đang nằm trong ô `custom_chang` của từng công thức: 140 công
thức ghi "BTP thành phần", 16 ghi "Ruột bánh (C1)", 23 ghi "Bánh khuôn
(C2)", 77 ghi "Thành phẩm". Sửa thẳng 179 dòng đó là việc một chiều: ghi
đè xong thì không còn biết mã nào vốn là C1 mã nào vốn là BTP thành phần,
mà đó đúng là thứ mô đun `phantom` đang dựa vào để biết mã nào được bỏ
tồn kho.

Nên tệp này chỉ DỊCH lúc đọc. Dữ liệu gốc giữ nguyên, màn hình và chip
lọc nhìn thấy hai tên mới. Ngày nào anh Việt muốn ghi thật xuống dữ liệu
thì có sẵn `gom_chang(chay_that=1)`, và nó chạy thử trước.

BẢNG NÀY LÀ NƠI DUY NHẤT BIẾT NHÃN CŨ ỨNG VỚI CHẶNG NÀO
-------------------------------------------------------
Trước đây mỗi tệp tự đoán lấy: `kho_san_xuat` suy từ tiền tố mã và chữ
"Cấp 1" trong tên, `phantom` đọc thẳng `custom_chang`, `don_bep` so chuỗi
với hằng riêng của nó. Ba đường suy khác nhau trên cùng một câu hỏi thì
sớm muộn cũng lệch nhau. Từ nay chỗ nào cần biết chặng của một nhãn thì
gọi `chang_cua_nhan`.
"""

# ------------------------------------------------------------ phần thuần

from vagabond.kho_san_xuat import (
	BTP_SAN_SANG, BTP_SO_CAP, NGUYEN_LIEU, TEN_CHANG, THANH_PHAM,
)

# Thứ tự đi lên của dây chuyền. Màn hình xếp chip theo đúng thứ tự này.
THU_TU = (NGUYEN_LIEU, BTP_SO_CAP, BTP_SAN_SANG, THANH_PHAM)

# Nhãn cũ nào thuộc chặng nào. Khoá viết thường, bỏ dấu cách thừa, để một
# nhãn gõ hoa gõ thường hay thừa khoảng trắng vẫn tra ra đúng chặng.
#
# "Sơ chế" là chặng đã ngừng dùng từ 20/08/2026 (hai công thức lòng đỏ và
# lòng trắng đã gộp vào trứng tươi). Vẫn để trong bảng vì công thức bản cũ
# còn giữ nhãn đó, và đọc một bản cũ ra chặng rỗng thì màn hình hiện "chưa
# phân chặng" cho một thứ vốn đã có chặng.
NHAN_CU = {
	"nguyên liệu": NGUYEN_LIEU,
	"btp thành phần": BTP_SO_CAP,
	"ruột bánh (c1)": BTP_SO_CAP,
	"ruột bánh c1": BTP_SO_CAP,
	"sơ chế": BTP_SO_CAP,
	"bánh khuôn (c2)": BTP_SAN_SANG,
	"bánh khuôn c2": BTP_SAN_SANG,
	"thành phẩm": THANH_PHAM,
}

# Tên mới hiện lên màn hình. Đọc từ `kho_san_xuat` chứ không chép lại, để
# đổi tên một chỗ là đổi khắp nơi.
TEN = dict(TEN_CHANG)

# Chữ ngắn in trên chip trạng thái của từng dòng.
CHIP = {
	NGUYEN_LIEU: "NVL",
	BTP_SO_CAP: "Sơ cấp",
	BTP_SAN_SANG: "Sẵn sàng",
	THANH_PHAM: "TP",
}

# Màu chip, dùng đúng bốn lớp màu app đã có: n xám, w vàng, g xanh lá.
MAU = {
	NGUYEN_LIEU: "n",
	BTP_SO_CAP: "w",
	BTP_SAN_SANG: "w",
	THANH_PHAM: "g",
}


def chang_cua_nhan(nhan):
	"""Nhãn chặng cũ hay mới đều trả về đúng một mã chặng. THUẦN.

	Nhận cả ba dạng đang có trong hệ:
	  * nhãn cũ trên công thức, ví dụ "Bánh khuôn (C2)"
	  * mã chặng, ví dụ "btp_san_sang", là thứ ô khai tay trên hồ sơ món ghi
	  * tên mới, ví dụ "BTP sẵn sàng"

	Nhãn lạ trả về chuỗi rỗng chứ không đoán bừa. Đoán bừa ở đây nghĩa là
	xếp một món vào chặng sai, và chặng sai thì lệnh sản xuất lấy sai kho.
	"""
	t = (nhan or "").strip()
	if not t:
		return ""
	if t in THU_TU:
		return t
	th = " ".join(t.lower().split())
	if th in NHAN_CU:
		return NHAN_CU[th]
	for ma, ten in TEN.items():
		if th == ten.lower():
			return ma
	return ""


def ten_chang(ma):
	"""Tên hiện lên màn hình của một mã chặng. Mã lạ thì nói thẳng là chưa rõ."""
	return TEN.get(ma) or "Chưa phân chặng"


def gop_dong(ds):
	"""Gom danh sách dòng tồn thành từng chặng. THUẦN.

	`ds` là các dict có khoá `chang` và `sl`. Trả về bảng
	{mã chặng: {"so_ma": n, "tong": x}} và luôn có đủ bốn chặng kể cả chặng
	rỗng: màn hình phải hiện "0 mã" chứ không được giấu chip đi. Chip biến
	mất thì người xem tưởng mình lọc nhầm, chứ không nghĩ là chặng đó hết
	hàng thật.
	"""
	ra = {c: {"so_ma": 0, "tong": 0.0} for c in THU_TU}
	ra[""] = {"so_ma": 0, "tong": 0.0}
	for d in ds or []:
		c = d.get("chang") or ""
		if c not in ra:
			ra[c] = {"so_ma": 0, "tong": 0.0}
		ra[c]["so_ma"] += 1
		ra[c]["tong"] += float(d.get("sl") or 0)
	return ra


# Khoá chip "chưa phân chặng". Phải là một chữ RIÊNG chứ không dùng chuỗi
# rỗng: chuỗi rỗng đã mang nghĩa "không lọc gì cả, lấy hết", và hai nghĩa
# đó nằm chung một giá trị thì bấm vào chip lại ra cả danh sách.
CHUA_PHAN = "chua"


def loc_theo_chang(ds, chang):
	"""Lọc danh sách dòng theo chặng. THUẦN.

	Chặng rỗng nghĩa là lấy hết. Chặng `chua` nghĩa là chỉ lấy các mã chưa
	phân chặng.
	"""
	c = (chang or "").strip()
	if not c:
		return list(ds or [])
	if c == CHUA_PHAN:
		return [d for d in (ds or []) if not (d.get("chang") or "")]
	return [d for d in (ds or []) if (d.get("chang") or "") == c]


def cau_tom_tat(bang):
	"""Một câu nói gọn bảng gom, để đặt trên đầu màn hình. THUẦN."""
	phan = []
	for c in THU_TU:
		o = bang.get(c) or {}
		if o.get("so_ma"):
			phan.append("%s %d mã" % (TEN.get(c, c), o["so_ma"]))
	chua = (bang.get("") or {}).get("so_ma") or 0
	if chua:
		phan.append("chưa phân chặng %d mã" % chua)
	if not phan:
		return "Không có mã nào còn tồn ở bộ lọc này."
	return " · ".join(phan)


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, flt

from vagabond import kho_san_xuat as ksx

QUYEN_GHI = ("System Manager", "Manufacturing Manager", "Giám đốc", "AP Giám đốc")

# Kho nào của chặng nào, để màn hình lọc nhanh theo bếp. Đọc từ chính bảng
# tên kho của `kho_san_xuat` chứ không gõ lại tên kho ở đây.
def kho_cua_bep(bep):
	"""Các kho lá còn bật của một bếp, kèm chặng của kho."""
	ra = []
	for k in ksx.khai_cay_kho():
		if bep and k["bep"] != bep:
			continue
		if not frappe.db.exists("Warehouse", k["ten"]):
			continue
		if cint(frappe.db.get_value("Warehouse", k["ten"], "disabled")):
			continue
		ra.append({"kho": k["ten"], "chang": k["chang"], "bep": k["bep"]})
	return ra


def _chang_theo_bom():
	"""Mã món nào thuộc chặng nào, đọc từ công thức đang chạy.

	Công thức là nguồn đáng tin nhất: chính bếp trưởng khai nhãn chặng ở đó
	khi lập công thức. Món không có công thức thì hàm gọi tự suy tiếp bằng
	`kho_san_xuat.chang_cua_mon`.
	"""
	ra = {}
	for b in frappe.get_all(
		"BOM", filters={"docstatus": 1, "is_active": 1},
		fields=["item", "custom_chang", "is_default"], limit_page_length=0,
	):
		c = chang_cua_nhan(b.get("custom_chang"))
		if not c:
			continue
		if b.item not in ra or cint(b.get("is_default")):
			ra[b.item] = c
	return ra


def _chang_cua_ma(ma, ten, khai_tay, tu_bom):
	"""Chặng của một mã, ba nấc. Nấc trên thắng nấc dưới.

	1. Ô khai tay trên hồ sơ món - người khai rõ hơn máy suy.
	2. Nhãn chặng trên công thức đang chạy.
	3. Suy từ tiền tố mã và tên món, đúng luật `kho_san_xuat` đang dùng cho
	   lệnh sản xuất. Để hai chỗ không nói hai câu khác nhau về cùng một mã.
	"""
	c = chang_cua_nhan(khai_tay)
	if c:
		return c
	c = tu_bom.get(ma) or ""
	if c:
		return c
	return ksx.chang_theo_tien_to(ma) or chang_cua_nhan(
		ksx.chang_theo_ten(ten)) or ""


@frappe.whitelist()
def ton_theo_chang(bep=None, chang=None, tim=None, gioi_han=300):
	"""Tồn kho hiện tại xếp theo chặng, cho màn Tồn kho theo chặng.

	Chỉ ĐỌC. Trả về ba thứ màn hình cần: bảng đếm từng chặng để vẽ chip,
	danh sách dòng đã lọc, và một câu tóm tắt.

	Đọc thẳng `Bin` chứ không đi qua báo cáo tồn kho của ERPNext: báo cáo đó
	dựng lại sổ từ đầu kỳ nên chậm hàng chục giây trên site này, mà câu hỏi
	ở đây chỉ là "ngay lúc này còn bao nhiêu".
	"""
	bep = (bep or "").strip().lower() or None
	chang = (chang or "").strip()
	tim = (tim or "").strip().lower()
	gioi_han = cint(gioi_han) or 300

	kho = kho_cua_bep(bep)
	ten_kho = [k["kho"] for k in kho]
	if not ten_kho:
		return {"bep": bep or "", "chang": chang, "kho": [], "bang": gop_dong([]),
			"thu_tu": list(THU_TU), "ten_chang": dict(TEN),
			"ds": [], "tong_dong": 0,
			"tom_tat": "Chưa có kho nào đang bật cho bộ lọc này."}

	dong_bin = frappe.get_all(
		"Bin", filters={"warehouse": ["in", ten_kho], "actual_qty": ["!=", 0]},
		fields=["item_code", "warehouse", "actual_qty", "stock_uom"],
		limit_page_length=0,
	)
	ma = sorted({d.item_code for d in dong_bin})
	ho_so = {}
	for i in range(0, len(ma), 400):
		for it in frappe.get_all(
			"Item", filters={"name": ["in", ma[i:i + 400]]},
			fields=["name", "item_name", "custom_chang_btp", "custom_lam_tuoi",
				"is_stock_item"],
			limit_page_length=0,
		):
			ho_so[it.name] = it

	tu_bom = _chang_theo_bom()
	gop = {}
	for d in dong_bin:
		it = ho_so.get(d.item_code) or {}
		ten = it.get("item_name") or d.item_code
		c = _chang_cua_ma(d.item_code, ten, it.get("custom_chang_btp"), tu_bom)
		o = gop.get(d.item_code)
		if not o:
			o = gop[d.item_code] = {
				"ma": d.item_code, "ten": ten, "chang": c,
				"chip": CHIP.get(c, "?"), "mau": MAU.get(c, "n"),
				"ten_chang": ten_chang(c), "dvt": d.stock_uom or "",
				"sl": 0.0, "kho": [], "lam_tuoi": cint(it.get("custom_lam_tuoi")),
			}
		o["sl"] += flt(d.actual_qty)
		o["kho"].append({"kho": d.warehouse, "sl": flt(d.actual_qty)})

	tat_ca = sorted(gop.values(), key=lambda x: (-x["sl"], x["ma"]))
	bang = gop_dong(tat_ca)
	ds = loc_theo_chang(tat_ca, chang)
	if tim:
		ds = [d for d in ds if tim in (d["ten"] + " " + d["ma"]).lower()]
	return {
		"bep": bep or "", "chang": chang,
		"thu_tu": list(THU_TU), "ten_chang": dict(TEN),
		"kho": kho, "bang": bang, "tong_dong": len(ds),
		"ds": ds[:gioi_han],
		"tom_tat": cau_tom_tat(bang),
	}


@frappe.whitelist()
def gom_chang(chay_that=0):
	"""Ghi hai tên mới xuống ô `custom_chang` của công thức. Chạy thử là mặc định.

	KHÔNG tự chạy. Màn hình không gọi hàm này, `after_migrate` cũng không.
	Nó nằm đây để ngày nào anh Việt muốn dữ liệu gốc cũng mang hai tên mới
	thì có sẵn đường, chứ hôm nay việc gom đang làm ở tầng hiển thị.

	Ghi xong là MẤT dấu mã nào vốn là "Ruột bánh (C1)" mã nào vốn là "BTP
	thành phần", mà `phantom` đang dựa đúng vào chỗ đó để biết mã nào được
	bỏ tồn kho. Nên hàm trả về sẵn số mã sẽ mất dấu để đọc trước khi quyết.
	"""
	if not set(frappe.get_roles()) & set(QUYEN_GHI):
		frappe.throw("Chỉ quản lý sản xuất hoặc giám đốc mới gom nhãn chặng được.")
	chay_that = cint(chay_that)
	se_doi, mat_dau = [], 0
	for b in frappe.get_all(
		"BOM", filters={"docstatus": 1, "is_active": 1},
		fields=["name", "item", "item_name", "custom_chang"], limit_page_length=0,
	):
		cu = (b.get("custom_chang") or "").strip()
		c = chang_cua_nhan(cu)
		if not c:
			continue
		moi = TEN.get(c) or ""
		if not moi or moi == cu:
			continue
		if c == BTP_SO_CAP:
			mat_dau += 1
		se_doi.append({"bom": b.name, "ma": b.item, "cu": cu, "moi": moi})
		if chay_that:
			frappe.db.set_value("BOM", b.name, "custom_chang", moi,
				update_modified=False)
	if chay_that:
		frappe.db.commit()
	return {
		"chay_that": chay_that, "so_doi": len(se_doi), "ds": se_doi,
		"ghi_chu": (
			"%s %d công thức. Trong đó %d công thức đang mang nhãn 'BTP thành "
			"phần' hoặc 'Ruột bánh (C1)' sẽ cùng thành 'BTP sơ cấp', tức mất "
			"dấu phân biệt hai loại đó - mô đun Phantom đang đọc chỗ này để "
			"biết mã nào được bỏ tồn kho."
			% ("Đã đổi" if chay_that else "Chạy thử, chưa ghi gì, sẽ đổi",
				len(se_doi), mat_dau)),
	}
