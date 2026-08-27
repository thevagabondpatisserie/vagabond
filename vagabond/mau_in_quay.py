# -*- coding: utf-8 -*-
"""Mau in: nhan vien tu chinh duoc noi dung ban in, khong phai deploy.

Anh Viet 26/08/2026: *"Anh thay em can lam them phan he Cau hinh mau in an
trong nut cai dat tren app, trong do co cau hinh mau in hoa don, cau hinh
mau in tem,... de nhan vien chinh duoc giong nhu ben ipos."*

RANH GIOI VOI MAN "MAY IN" DA CO
--------------------------------
Hai man tra loi hai cau khac nhau, khong duoc lan sang nhau:

  may_in.py       in o DAU va ra TO TO BAO NHIEU. So may in, manh ten may
                  in tren Windows, kho giay, can tem lech may mi li met.
  mau_in_quay.py  tren to giay do IN NHUNG GI. Co logo khong, chu to hay
                  nho, co in khoi diem thanh vien khong, dong cam on viet gi.

TEN TEP KHONG PHAI LA `mau_in.py`, va do la co y: goi `vagabond/mau_in/` da
co san tu truoc, no giu cac ban in cua ban DESKTOP (phieu nhap kho, chung
tu thanh toan). Dat trung ten thi Python nap mot cai va giau mat cai kia,
khong bao mot dong loi nao. Tep nay lo ban in cua QUAY, nen ten co chu quay.

Nen doi mot cai may in thi sua man May in; con doi cach trinh bay to bill
thi sua man nay. Khong o nao bi khai hai lan.

VI SAO CHIA THEO DIEM BAN
-------------------------
Y het ly do cua kho giay (may_in.kho_theo_vai_tro): quay Tran Cao Van va
quay Nguyen Van Huong Tra Noi khong bat buoc in giong nhau. Diem nao chua
khai rieng thi dung ban CHUNG, nen khai mot lan o ban chung la ca ba diem
cung theo.

VI SAO MAC DINH PHAI BANG DUNG HANH VI CU
-----------------------------------------
Man nay ra doi giua luc quay dang ban. Neu mot o nao co gia tri mac dinh
khac hanh vi hom qua thi sang mai to bill doi kieu ma khong ai bam gi ca,
va khong ai hieu vi sao. Nen tung con so trong MAC_DINH duoi day deu duoc
chep tu chinh ma nguon ban in dang chay, khong phai tu chon cho dep.
"""

import json

import frappe

from vagabond.lib import cfg

TRUONG = "vgb_mau_in_quay"

from vagabond.vai_cua_hang import VAI_QLCH

QUYEN_SUA = {"System Manager", "Accounts Manager", "Sales Manager", VAI_QLCH}

# Ba loai ban in dang cho chinh. Phieu chot ca CHUA co trong day: no do man
# dong ca dung, khong dung chung khuon voi ba ban nay, nen de nguyen cho
# den khi co nguoi thuc su can chinh.
VAI_TRO = [
	{
		"k": "hoa_don",
		"ten": "Hoá đơn cho khách",
		"mo": "Tờ giấy đưa khách sau khi thu tiền.",
		"ic": "🧾",
	},
	{
		"k": "phieu_mon",
		"ten": "Phiếu làm món",
		"mo": "Phiếu quầy pha chế đọc để làm nước.",
		"ic": "🥤",
	},
	{
		"k": "tem",
		"ten": "Tem dán ly và dán bánh",
		"mo": "Tem nhỏ dán lên ly mang đi và hộp bánh.",
		"ic": "🏷",
	},
]

# Mo ta tung o cho man hinh tu dung ra, de them mot o moi chi phai sua MOT
# cho. `loai` la 'bat' (co / khong), 'so' hoac 'chu'.
O = {
	"hoa_don": [
		{"k": "logo", "loai": "bat", "ten": "In logo đầu hoá đơn",
		 "mo": "Tắt thì in tên tiệm bằng chữ, tốn ít giấy hơn."},
		{"k": "dia_chi", "loai": "bat", "ten": "In tên quầy và địa chỉ"},
		{"k": "co_chu", "loai": "so", "ten": "Cỡ chữ", "min": 9, "max": 16, "buoc": 0.5,
		 "mo": "Chữ to thì dễ đọc nhưng tờ giấy dài ra."},
		{"k": "gop_mon", "loai": "bat", "ten": "Gộp các dòng cùng một món",
		 "mo": "Bấm ba lần một món thì in một dòng số lượng 3, thay vì ba dòng."},
		{"k": "an_mon_0d", "loai": "bat", "ten": "Ẩn món giá 0 đồng",
		 "mo": "Món tặng kèm và món khuyến mãi sẽ không hiện trên hoá đơn."},
		{"k": "hien_tuy_chon", "loai": "bat", "ten": "In tuỳ chọn pha chế",
		 "mo": "Dòng ít đá, ít đường in ngay dưới tên món."},
		{"k": "qr_xhd", "loai": "bat", "ten": "In mã QR xuất hoá đơn điện tử"},
		{"k": "khoi_diem", "loai": "bat", "ten": "In khối thẻ thành viên",
		 "mo": "Hạng thẻ, điểm tích đơn này và số dư điểm."},
		{"k": "chan_trang", "loai": "chu", "ten": "Dòng cảm ơn cuối hoá đơn", "dai": 80},
		{"k": "web", "loai": "chu", "ten": "Dòng địa chỉ web cuối cùng", "dai": 60},
	],
	"phieu_mon": [
		{"k": "co_chu", "loai": "so", "ten": "Cỡ chữ tên món", "min": 10, "max": 22, "buoc": 0.5},
		{"k": "hien_ban", "loai": "bat", "ten": "In số bàn thật to"},
		{"k": "hien_tuy_chon", "loai": "bat", "ten": "In tuỳ chọn pha chế"},
		{"k": "hien_gio", "loai": "bat", "ten": "In giờ ra phiếu"},
	],
	"tem": [
		{"k": "co_chu", "loai": "so", "ten": "Cỡ chữ tên món", "min": 7, "max": 16, "buoc": 0.5,
		 "mo": "Tên món dài mà chữ to thì bị cắt bớt, in thử một tem rồi chỉnh."},
		{"k": "hien_dau", "loai": "bat", "ten": "In dòng đầu tem",
		 "mo": "Tên tiệm, hoặc tên sàn và mã đơn nếu là đơn giao hàng."},
		{"k": "hien_tuy_chon", "loai": "bat", "ten": "In tuỳ chọn pha chế"},
		{"k": "hien_ghi_chu", "loai": "bat", "ten": "In ghi chú của khách"},
		{"k": "hien_chan", "loai": "bat", "ten": "In mã hoá đơn và số thứ tự tem"},
	],
}

# Chep tu chinh ma nguon ban in dang chay, xem ghi chu o dau tep.
MAC_DINH = {
	"hoa_don": {
		"logo": 1,
		"dia_chi": 1,
		"co_chu": 11.5,
		"gop_mon": 0,
		"an_mon_0d": 0,
		"hien_tuy_chon": 1,
		"qr_xhd": 1,
		"khoi_diem": 1,
		"chan_trang": "Cảm ơn quý khách!",
		"web": "thevagabondpatisserie.com",
	},
	"phieu_mon": {
		"co_chu": 14,
		"hien_ban": 1,
		"hien_tuy_chon": 1,
		"hien_gio": 1,
	},
	"tem": {
		"co_chu": 11,
		"hien_dau": 1,
		"hien_tuy_chon": 1,
		"hien_ghi_chu": 1,
		"hien_chan": 1,
	},
}


# --------------------------------------------------------------- phan thuan
# Ba ham duoi day KHONG cham Frappe: vao la vat the, ra la vat the. Nho vay
# bo kiem thu tang khung chay duoc khong can site, khong can mang.


def chuan_mot(vai, tho):
	"""Mot ban mau da duoc go ve dung kieu va dung khoang cho phep.

	O nao thieu, sai kieu, hay ngoai khoang thi ve mac dinh CUA CHINH O DO,
	khong bo ca ban. Ban luu tren may chu la thu du lieu song lau nam: mot
	ngay nao do co o duoc them, ban cu se thieu dung o do thoi.
	"""
	md = MAC_DINH.get(vai) or {}
	tho = tho if isinstance(tho, dict) else {}
	ra = {}
	for o in O.get(vai) or []:
		k = o["k"]
		v = tho.get(k, None)
		if o["loai"] == "bat":
			ra[k] = 1 if (md[k] if v is None else v) else 0
		elif o["loai"] == "so":
			try:
				x = float(v)
			except (TypeError, ValueError):
				x = float(md[k])
			if x < o["min"] or x > o["max"]:
				x = float(md[k])
			ra[k] = x
		else:
			x = md[k] if v is None else str(v)
			ra[k] = x.strip()[: int(o.get("dai") or 80)]
	return ra


def chuan_ban(tho):
	"""Ca mot ban mau cho ba loai phieu."""
	tho = tho if isinstance(tho, dict) else {}
	return {v["k"]: chuan_mot(v["k"], tho.get(v["k"])) for v in VAI_TRO}


def chuan_het(tho):
	"""Ban chung cong cac ban rieng cua tung diem ban."""
	tho = tho if isinstance(tho, dict) else {}
	rieng = tho.get("diem")
	rieng = rieng if isinstance(rieng, dict) else {}
	ra = {"chung": chuan_ban(tho.get("chung")), "diem": {}}
	for ma, ban in rieng.items():
		ma = str(ma or "").strip().upper()
		if ma:
			ra["diem"][ma] = chuan_ban(ban)
	return ra


def mau_cho(het, diem=""):
	"""Ban mau ap dung cho mot diem ban. Chua khai rieng thi lay ban chung."""
	het = het if isinstance(het, dict) else {}
	ma = str(diem or "").strip().upper()
	rieng = (het.get("diem") or {}).get(ma)
	return rieng if isinstance(rieng, dict) and rieng else (het.get("chung") or {})


# ------------------------------------------------------------- cham he thong


def het():
	"""Toan bo cau hinh mau in dang luu. Hong dinh dang thi ve mac dinh."""
	try:
		tho = json.loads((cfg().get(TRUONG) or "").strip() or "{}")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "mau_in: cau hinh hong dinh dang")
		tho = {}
	return chuan_het(tho)


def theo_diem(diem=""):
	"""Ban mau cua mot diem ban, dang gui thang cho app."""
	return mau_cho(het(), diem)


# ------------------------------------------------------------------ man app


@frappe.whitelist()
def danh_sach():
	from vagabond import diem_ban
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	return {
		"mau": het(),
		"vai_tro": VAI_TRO,
		"o": O,
		"mac_dinh": MAC_DINH,
		"diem": [{"ma": d["ma"], "ten": d["ten_ngan"] or d["ten"]} for d in diem_ban.ds()],
		"sua_duoc": 1 if QUYEN_SUA & set(frappe.get_roles()) else 0,
	}


@frappe.whitelist()
def luu(diem="", mau=None):
	"""Ghi ban mau cua MOT diem ban, hoac ban chung khi `diem` rong.

	Chi ghi de dung phan cua diem do. Hai nguoi cung mo man nay, moi nguoi
	sua mot diem roi bam Luu thi khong ai xoa viec cua ai - cung mot bai hoc
	da viet trong may_in._tron.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not QUYEN_SUA & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới sửa được mẫu in.")
	if isinstance(mau, str):
		mau = frappe.parse_json(mau or "{}")
	ma = str(diem or "").strip().upper()
	dang_co = het()
	if ma:
		dang_co["diem"][ma] = chuan_ban(mau)
	else:
		dang_co["chung"] = chuan_ban(mau)
	frappe.db.set_single_value(
		"Vagabond Settings", TRUONG, json.dumps(dang_co, ensure_ascii=False, indent=1)
	)
	frappe.db.commit()
	frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
	_ghi_vet("Sửa mẫu in %s" % (("điểm " + ma) if ma else "dùng chung"))
	return danh_sach()


@frappe.whitelist()
def tra_mac_dinh(diem=""):
	"""Bo ban rieng cua mot diem ban, cho no theo lai ban chung."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not QUYEN_SUA & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới sửa được mẫu in.")
	ma = str(diem or "").strip().upper()
	dang_co = het()
	if ma:
		dang_co["diem"].pop(ma, None)
	else:
		dang_co["chung"] = chuan_ban(None)
	frappe.db.set_single_value(
		"Vagabond Settings", TRUONG, json.dumps(dang_co, ensure_ascii=False, indent=1)
	)
	frappe.db.commit()
	frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
	_ghi_vet("Trả mẫu in về mặc định: %s" % (("điểm " + ma) if ma else "dùng chung"))
	return danh_sach()


def _ghi_vet(viec):
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Vagabond Settings",
				"reference_name": "Vagabond Settings",
				"content": "%s - %s" % (viec, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass
