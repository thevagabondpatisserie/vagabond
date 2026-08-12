# -*- coding: utf-8 -*-
"""So may in va kho giay tung loai phieu (anh Viet 12/08/2026).

Hai viec khac nhau nam chung mot man, vi ca hai deu tra loi cau "phieu nay
in o dau, ra to to bao nhieu":

  1. SO THIET BI. Ba may in iPOS dang o 9 Tran Cao Van, moi may mot so
     seri. Khai o day de con biet may nao hong thi goi bao hanh cai nao,
     va mo chi nhanh moi thi them may chu khong phai lat so tay giay.

  2. KHO GIAY THEO LOAI PHIEU. Truoc day bon loai phieu deu go cung kho
     trong ma nguon: hoa don 80mm, phieu lam mon 80mm, tem 40x30mm, phieu
     chot ca 80mm. Doi mot may in khac kho la phai sua ma roi deploy.

MOT DIEU PHAI NOI THANG, khong duoc de man hinh hua hao:

  App in bang hop thoai in cua trinh duyet. Trinh duyet KHONG cho phep ma
  nguon chi dinh may in nao - do la rao can bao mat cua trinh duyet, khong
  phai thieu sot cua minh. Nghia la cai "may nay in hoa don" o day la ban
  ghi de nguoi doc biet, con muon phieu chay dung may thi phai dat may in
  mac dinh tren tung may tinh o quay, hoac dung trinh dieu khien in cua
  iPOS. Kho giay thi app dung THAT.
"""

import json
import re

import frappe
from frappe.utils import cint

from vagabond.lib import cfg

TRUONG = "vgb_may_in"

QUYEN_SUA = {"System Manager", "Accounts Manager", "Sales Manager"}

# Bon loai phieu app dang in. Them loai moi thi them mot dong o day, man
# Cai dat tu co them mot dong de chon kho.
VAI_TRO = [
	{"k": "hoa_don", "ten": "Hoá đơn cho khách", "mo": "Phiếu tính tiền đưa khách, in ở quầy thu ngân.", "ic": "🧾"},
	{"k": "phieu_mon", "ten": "Phiếu làm món", "mo": "Phiếu món nước cho quầy pha chế.", "ic": "🥤"},
	{"k": "tem", "ten": "Tem dán ly và dán bánh", "mo": "Tem nhỏ dán lên ly mang đi và hộp bánh.", "ic": "🏷"},
	{"k": "chot_ca", "ten": "Phiếu chốt ca", "mo": "Phiếu tổng kết cuối ca của thu ngân.", "ic": "📄"},
]

# Kho giay. "rong" la be ngang phan than in duoc, tru le hai bien - so nay
# di thang vao CSS ben app nen doi o day la doi ca ban in.
KHO_GIAY = [
	{"k": "80mm", "ten": "Giấy cuộn 80mm", "css": "80mm auto", "rong": 72, "cuon": 1},
	{"k": "58mm", "ten": "Giấy cuộn 58mm", "css": "58mm auto", "rong": 50, "cuon": 1},
	{"k": "tem_40x30", "ten": "Tem 40 x 30mm", "css": "40mm 30mm", "rong": 40, "cao": 30, "cuon": 0},
	{"k": "tem_50x30", "ten": "Tem 50 x 30mm", "css": "50mm 30mm", "rong": 50, "cao": 30, "cuon": 0},
	{"k": "tem_35x22", "ten": "Tem 35 x 22mm", "css": "35mm 22mm", "rong": 35, "cao": 22, "cuon": 0},
]

KHO_MAC_DINH = {"hoa_don": "80mm", "phieu_mon": "80mm", "tem": "tem_40x30", "chot_ca": "80mm"}

# Ba may in iPOS dang chay o 9 Tran Cao Van, thong so anh Viet gui
# 12/08/2026. Vua la gia tri khoi tao, vua la luoi do khi cau hinh tren
# Settings trong hoac hong dinh dang.
MAC_DINH = [
	{
		"ma": "MI1",
		"ten": "Máy in hoá đơn quầy",
		"hang": "iPOS.VN",
		"model": "iTP86",
		"loai": "Thermal Receipt Printer",
		"so_seri": "3.01.05.0094624112700613",
		"giao_tiep": "Serial, USB, Ethernet",
		"nguon_dien": "24V 2.5A",
		"xuat_xu": "Trung Quốc",
		"diem": "TCV",
		"vai_tro": ["hoa_don", "chot_ca"],
		"kho": "80mm",
		"ghi_chu": "",
		"bat": 1,
	},
	{
		"ma": "MI2",
		"ten": "Máy in tem",
		"hang": "iPOS.VN",
		"model": "ITP3300",
		"loai": "Thermal Barcode Printer",
		"so_seri": "2023040041",
		"giao_tiep": "USB, RS232, Ethernet",
		"nguon_dien": "24V 2.5A",
		"xuat_xu": "Trung Quốc",
		"diem": "TCV",
		"vai_tro": ["tem"],
		"kho": "tem_40x30",
		"ghi_chu": "Khổ giấy nhận được 20 đến 82mm. Tốc độ 125 đến 150mm/s. Lệnh EPSON ESC/POS. Sản xuất 2023.",
		"bat": 1,
	},
	{
		"ma": "MI3",
		"ten": "Máy in phiếu quầy bar",
		"hang": "iPOS.VN",
		"model": "iTP80",
		"loai": "Thermal Receipt Printer",
		"so_seri": "ITP8003242209",
		"giao_tiep": "USB, Serial, Ethernet",
		"nguon_dien": "24V 2.5A",
		"xuat_xu": "Trung Quốc",
		"diem": "TCV",
		"vai_tro": ["phieu_mon"],
		"kho": "80mm",
		"ghi_chu": "Khổ giấy 80mm. Tốc độ tối đa 230mm/s.",
		"bat": 1,
	},
]

MAU_MA = re.compile(r"^[A-Z0-9_]{2,10}$")


def _kho_hop_le(k):
	return k if any(x["k"] == k for x in KHO_GIAY) else ""


def _chuan(d, i=0):
	ma = str((d or {}).get("ma") or "").strip().upper()
	vt = (d or {}).get("vai_tro")
	if isinstance(vt, str):
		vt = [x.strip() for x in vt.replace(",", "\n").splitlines() if x.strip()]
	hop = {x["k"] for x in VAI_TRO}
	vt = [x for x in (vt or []) if x in hop]
	return {
		"ma": ma or ("MI%d" % (i + 1)),
		"ten": str((d or {}).get("ten") or "").strip() or "Máy in %d" % (i + 1),
		"hang": str((d or {}).get("hang") or "").strip(),
		"model": str((d or {}).get("model") or "").strip(),
		"loai": str((d or {}).get("loai") or "").strip(),
		"so_seri": str((d or {}).get("so_seri") or "").strip(),
		"giao_tiep": str((d or {}).get("giao_tiep") or "").strip(),
		"nguon_dien": str((d or {}).get("nguon_dien") or "").strip(),
		"xuat_xu": str((d or {}).get("xuat_xu") or "").strip(),
		"diem": str((d or {}).get("diem") or "").strip().upper(),
		"vai_tro": vt,
		"kho": _kho_hop_le(str((d or {}).get("kho") or "").strip()) or "80mm",
		"ghi_chu": str((d or {}).get("ghi_chu") or "").strip(),
		"bat": 1 if cint((d or {}).get("bat") if (d or {}).get("bat") is not None else 1) else 0,
	}


def ds(chi_bat=False):
	"""Toan bo may in da khai."""
	try:
		tho = json.loads((cfg().get(TRUONG) or "").strip() or "[]")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "may_in: cau hinh hong dinh dang")
		tho = []
	if not isinstance(tho, list) or not tho:
		tho = MAC_DINH
	ra = [_chuan(d, i) for i, d in enumerate(tho)]
	return [d for d in ra if d["bat"]] if chi_bat else ra


def kho_theo_vai_tro():
	"""Bang tra loai phieu -> kho giay, gui cho app cung cau hinh ban hang.

	May nao dang bat va nhan loai phieu do thi lay kho cua may do. Nhieu may
	cung nhan mot loai thi lay may dau tien - do la truong hop hai chi nhanh
	moi noi mot may, kho giay giong nhau nen khong sinh chuyen.
	"""
	bang = {}
	for m in ds(chi_bat=True):
		for v in m["vai_tro"]:
			if v not in bang:
				bang[v] = m["kho"]
	ra = {}
	for v in VAI_TRO:
		k = bang.get(v["k"]) or KHO_MAC_DINH.get(v["k"]) or "80mm"
		kho = [x for x in KHO_GIAY if x["k"] == k]
		ra[v["k"]] = dict(kho[0]) if kho else dict(KHO_GIAY[0])
	return ra


def _kiem(ra):
	"""Chan cac cau hinh se in ra giay sai kho, TRUOC khi luu."""
	ma_da_co = {}
	for d in ra:
		if not MAU_MA.match(d["ma"]):
			frappe.throw(
				"Mã máy in %s không hợp lệ. Chỉ dùng chữ in hoa không dấu, số "
				"và gạch dưới, từ 2 đến 10 ký tự." % d["ma"]
			)
		if d["ma"] in ma_da_co:
			frappe.throw("Mã máy in %s bị trùng." % d["ma"])
		ma_da_co[d["ma"]] = 1
		if d["bat"] and not d["vai_tro"]:
			frappe.throw(
				"Máy in %s đang bật mà chưa chọn in loại phiếu nào. Chọn ít "
				"nhất một loại, hoặc tắt máy đó đi." % d["ten"]
			)
		# Tem in tren giay cuon 80mm thi ra mot to dai loong toong, con phieu
		# in tren tem 40x30 thi cut mat noi dung. Chan o day cho nguoi khai
		# thay ngay chu khong de den luc dung may in that moi biet.
		la_tem = "tem" in d["vai_tro"]
		kho = [x for x in KHO_GIAY if x["k"] == d["kho"]]
		cuon = cint(kho[0].get("cuon")) if kho else 1
		if la_tem and cuon:
			frappe.throw(
				"Máy in %s nhận in tem mà đang để khổ giấy cuộn. Chọn một khổ "
				"tem cho máy đó." % d["ten"]
			)
		if not la_tem and d["vai_tro"] and not cuon:
			frappe.throw(
				"Máy in %s in phiếu mà đang để khổ tem. Phiếu in trên tem sẽ "
				"cụt mất nội dung." % d["ten"]
			)
	# Moi loai phieu phai co it nhat mot may nhan in, khong thi den luc can
	# in khong ai biet phieu do di dau.
	nhan = set()
	for d in ra:
		if d["bat"]:
			nhan |= set(d["vai_tro"])
	thieu = [v["ten"] for v in VAI_TRO if v["k"] not in nhan]
	if thieu:
		frappe.msgprint(
			"Chưa có máy in nào nhận: %s. Các phiếu này vẫn in được ra khổ mặc "
			"định, nhưng nên khai cho đủ." % ", ".join(thieu),
			indicator="orange",
		)


# ------------------------------------------------------------------ man app


@frappe.whitelist()
def danh_sach():
	from vagabond import diem_ban
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	return {
		"may": ds(),
		"vai_tro": VAI_TRO,
		"kho_giay": KHO_GIAY,
		"diem": [{"ma": d["ma"], "ten": d["ten_ngan"] or d["ten"]} for d in diem_ban.ds()],
		"sua_duoc": 1 if QUYEN_SUA & set(frappe.get_roles()) else 0,
	}


@frappe.whitelist()
def luu(may=None):
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not QUYEN_SUA & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới sửa được danh sách máy in.")
	if isinstance(may, str):
		may = frappe.parse_json(may or "[]")
	ra = [_chuan(d, i) for i, d in enumerate(may or [])]
	_kiem(ra)
	frappe.db.set_single_value(
		"Vagabond Settings", TRUONG, json.dumps(ra, ensure_ascii=False, indent=1)
	)
	frappe.db.commit()
	_ghi_vet(
		"Sửa danh sách máy in: %s"
		% ", ".join("%s %s%s" % (d["ma"], d["model"] or d["ten"], "" if d["bat"] else " (tắt)") for d in ra)
	)
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
