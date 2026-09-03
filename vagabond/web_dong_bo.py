# -*- coding: utf-8 -*-
"""Cài đặt trang đặt bánh web: một nút đồng bộ ảnh và mô tả từ Pancake.

Anh Việt 03/09/2026: *"Minh Vũ đã import hình ảnh mới lên trên pancake
nhưng bên web không tự map hình đó về. Em có thể cho anh 1 nút cài đặt web
bên trong phân hệ cài đặt và có nút nhấn đồng bộ để bạn ấy tự nhấn sau khi
cài các thứ bên pancake để đồng bộ về được không?"*

Vì sao web không tự đổi
-----------------------
Trang đặt bánh lấy ảnh và mô tả từ danh mục Pancake, nhưng qua ba đường
khác nhau, và mỗi đường có một chỗ nhớ riêng:

  1. Tab "Có sẵn hôm nay" và "Đặt bánh trước": hỏi Pancake từng mã, nhớ
     kết quả NỬA TIẾNG trong bộ nhớ đệm để khách vãng lai không làm tiệm
     bị Pancake chặn (26/08 Pancake trả 403 suốt hai ngày). Sửa ảnh bên
     Pancake thì web đổi theo sau tối đa nửa tiếng, không tức thì.
  2. Tab "In season": ảnh lưu trong dòng bảng mùa vụ, và dòng đó chỉ được
     ghi lúc kéo ĐƠN về. Không có đơn mới cho mã đó thì ảnh cũ nằm mãi.
     Đây đúng là chỗ Minh Vũ vướng.
  3. Ảnh trong danh mục Hàng hoá bên Next: dùng cho các màn nội bộ (kiểm
     bánh, tính tiền) và là lớp lùi cuối của web. Chỉ được gán một lần.

Nút này làm ba việc trong một lần bấm: kéo cả danh mục Pancake về MỘT
LƯỢT (vài trang, không hỏi từng mã), xoá bộ nhớ đệm của mọi mã đang lên
web, và ghi lại ảnh vào dòng mùa vụ cùng dòng kiểm bánh hôm nay. Món bên
Next chưa có ảnh thì gán thêm; món đã có ảnh thì KHÔNG ghi đè, vì đó là
danh mục chuẩn của tiệm, đổi phải đổi có chủ đích ở màn Danh mục.

Nó cũng chỉ ra những mã đang lên web mà Pancake KHÔNG có ảnh, để Minh Vũ
biết còn thiếu mã nào bên Pancake thay vì đoán.
"""

import json

import frappe
from frappe.utils import cint, getdate, now_datetime

from vagabond.lib import cfg, key

KHOA_LAN_CUOI = "vgb_web_dong_bo_lan_cuoi"

# Ai bấm được: những người đang cầm danh mục bên Pancake và bên Next.
# Trung voi bo vai cua doi_soat.py, vi nut nay keo danh muc qua chinh cua do.
QUYEN = {"System Manager", "Sales Manager", "Sales User", "Bộ phận đặt hàng"}

# Ma banh si khong bao gio len web ban le (anh Viet 10/08/2026).
TIEN_TO_KHONG_LEN_WEB = ("BAWS",)


# ----------------------------------------------------------- phần THUẦN

def gom_ma(*cac_nhom):
	"""Gom mã của nhiều tab lại: bỏ trống, bỏ trùng, bỏ bánh sỉ, GIỮ thứ tự
	gặp lần đầu. THUẦN."""
	ra, da = [], set()
	for nhom in cac_nhom:
		for m in nhom or []:
			m = str(m or "").strip()
			if not m or m in da:
				continue
			if m.upper().startswith(TIEN_TO_KHONG_LEN_WEB):
				continue
			da.add(m)
			ra.append(m)
	return ra


def anh_dung_duoc(u):
	"""Một đường dẫn ảnh có dùng lên web được không. THUẦN.

	Ảnh riêng tư của Next (/private/...) không mở được khi chưa đăng nhập,
	đưa lên web là ô ảnh vỡ.
	"""
	u = str(u or "").strip()
	if not u:
		return False
	return not u.startswith("/private")


def can_doi_anh(anh_pancake, anh_dang_giu):
	"""Có phải ghi lại ảnh cho dòng này không. THUẦN.

	Pancake không có ảnh thì KHÔNG xoá ảnh đang giữ: mất ảnh bên Pancake
	(sales lỡ xoá, Pancake lỗi) không được kéo theo mất ảnh trên web.
	"""
	moi = str(anh_pancake or "").strip()
	if not moi:
		return False
	return moi != str(anh_dang_giu or "").strip()


def ma_thieu_anh(cac_ma, anh_theo_ma):
	"""Những mã đang lên web mà Pancake không có ảnh. THUẦN, có thứ tự."""
	return sorted(m for m in (cac_ma or []) if not str((anh_theo_ma or {}).get(m) or "").strip())


def ban_do_anh(danh_muc_pancake, bo_hau_to=None):
	"""{ma: url ảnh} từ danh mục Pancake. THUẦN.

	Mã bên Pancake có thể mang hậu tố size tự sinh (BAWC00104S16CM); mã gốc
	cũng được nhận ảnh đó nếu chưa có ảnh riêng. Giữ ảnh gặp TRƯỚC cho mỗi
	mã, vì danh mục Pancake trả theo thứ tự tiệm sắp.
	"""
	ra = {}
	for v in danh_muc_pancake or []:
		ma = str((v or {}).get("ma") or "").strip()
		u = str((v or {}).get("anh") or "").strip()
		if not ma or not u:
			continue
		ra.setdefault(ma, u)
		if bo_hau_to:
			goc = bo_hau_to(ma)
			if goc and goc != ma:
				ra.setdefault(goc, u)
	return ra


# ----------------------------------------------------------- chạm hệ

def _kiem_quyen():
	if not QUYEN & set(frappe.get_roles()):
		frappe.throw("Tài khoản của bạn chưa được cấp quyền cài đặt trang web.")


def _ma_dang_len_web():
	"""Mã từng tab của trang đặt bánh đang lấy ra. Chỉ ĐỌC."""
	from vagabond import kiem_kho, mua_vu

	ngay = getdate()
	ra = {"mua_vu": [], "hom_nay": [], "quay": [], "dat_truoc": []}

	# In season: mua dang chay.
	try:
		for ten in mua_vu.mua_dang_chay(ngay) or []:
			ra["mua_vu"] += [
				r["ma_hang"] for r in frappe.get_all(
					"Vagabond Mua Vu Dong", filters={"parent": ten},
					fields=["ma_hang"], limit_page_length=0, ignore_permissions=True,
				)
			]
	except Exception:
		pass

	# Co san hom nay: bang kiem banh ngay.
	try:
		ra["hom_nay"] = [
			r["ma_hang"] for r in frappe.get_all(
				"Kiem Banh Dong", filters={"parent": "KB-%s" % ngay},
				fields=["ma_hang"], limit_page_length=0, ignore_permissions=True,
			)
		]
	except Exception:
		pass

	# In store: bang kiem kho tung quay.
	try:
		for d in kiem_kho._diem_co_quay():
			ra["quay"] += [
				r["ma_hang"] for r in frappe.get_all(
					kiem_kho.DT_DONG,
					filters={"parent": kiem_kho.ten_phieu(d["ma"], ngay)},
					fields=["ma_hang"], limit_page_length=0, ignore_permissions=True,
				)
			]
	except Exception:
		pass

	# Dat banh truoc: kho BTP Banh O.
	try:
		kho = frappe.get_single("BTP Banh O")
		ra["dat_truoc"] = [b.ma_hang for b in (kho.dong or []) if (b.so_decor or 0) > 0]
	except Exception:
		pass
	return ra


def _xoa_dem(cac_ma):
	"""Xoá bộ nhớ đệm nửa tiếng của từng mã, để lần khách mở web kế tiếp
	hỏi Pancake lấy bản mới."""
	n = 0
	for m in cac_ma:
		try:
			frappe.cache().delete_value("vgb:sp:" + m)
			n += 1
		except Exception:
			pass
	return n


def _ghi_lai_hinh(doctype_dong, bo_loc, anh_theo_ma):
	"""Ghi lại ô ảnh của các dòng con khớp bộ lọc. Trả số dòng đã đổi.

	Ghi thẳng bằng set_value, KHÔNG động vào dấu thời gian của phiếu mẹ:
	đổi ảnh không phải là một lần sửa phiếu.
	"""
	doi = 0
	try:
		dong = frappe.get_all(
			doctype_dong, filters=bo_loc, fields=["name", "ma_hang", "hinh"],
			limit_page_length=0, ignore_permissions=True,
		)
	except Exception:
		return 0
	for r in dong:
		moi = anh_theo_ma.get(r["ma_hang"])
		if not can_doi_anh(moi, r.get("hinh")):
			continue
		try:
			frappe.db.set_value(doctype_dong, r["name"], "hinh", moi, update_modified=False)
			doi += 1
		except Exception:
			pass
	return doi


def _gan_anh_mon_trong(cac_ma, anh_theo_ma):
	"""Món bên Next chưa có ảnh thì tải ảnh Pancake về gán. Không ghi đè."""
	from vagabond import doi_soat

	gan, loi = [], []
	if not cac_ma:
		return gan, loi
	trong = frappe.get_all(
		"Item", filters={"name": ["in", cac_ma], "image": ["in", ["", None]]},
		fields=["name"], limit_page_length=0, ignore_permissions=True,
	)
	for it in trong:
		u = anh_theo_ma.get(it["name"])
		if not u:
			continue
		try:
			doi_soat._gan_anh_url(it["name"], u)
			gan.append(it["name"])
		except Exception:
			frappe.log_error(frappe.get_traceback(), "web_dong_bo: gan anh %s" % it["name"])
			loi.append(it["name"])
	return gan, loi


def _doc_lan_cuoi():
	try:
		tho = frappe.db.get_default(KHOA_LAN_CUOI)
		return json.loads(tho) if tho else None
	except Exception:
		return None


@frappe.whitelist()
def tinh_hinh():
	"""Màn Cài đặt web đọc: đang có bao nhiêu mã ở mỗi tab, lần đồng bộ gần
	nhất ra sao. CHỈ ĐỌC, không hỏi Pancake."""
	_kiem_quyen()
	c = cfg()
	nhom = _ma_dang_len_web()
	return {
		"co_khoa": 1 if (key(c, "pancake_api_key") and c.pancake_shop_id) else 0,
		"so_ma": {k: len(gom_ma(v)) for k, v in nhom.items()},
		"tong": len(gom_ma(*nhom.values())),
		"lan_cuoi": _doc_lan_cuoi(),
	}


@frappe.whitelist()
def dong_bo():
	"""Nút "Đồng bộ từ Pancake". Kéo danh mục một lượt, xoá đệm, ghi lại ảnh.

	Trả về bản tóm tắt bằng lời để màn hình hiện thẳng, và lưu lại làm
	"lần cuối" cho lần mở màn sau.
	"""
	_kiem_quyen()
	c = cfg()
	if not (key(c, "pancake_api_key") and c.pancake_shop_id):
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings.")

	from vagabond import doi_soat

	try:
		danh_muc = doi_soat.keo_san_pham_pancake()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "web_dong_bo: keo danh muc Pancake")
		frappe.throw(
			"Pancake không trả danh mục lúc này. Chờ vài phút rồi bấm lại; "
			"vẫn lỗi thì kiểm khoá Pancake trong Cài đặt."
		)
	anh_theo_ma = ban_do_anh(
		danh_muc, bo_hau_to=lambda m: doi_soat.HAU_TO_SIZE.sub("", m).strip()
	)

	nhom = _ma_dang_len_web()
	tat_ca = gom_ma(*nhom.values())
	ngay = getdate()

	da_xoa_dem = _xoa_dem(tat_ca)
	doi_mua = 0
	try:
		from vagabond import mua_vu
		for ten in mua_vu.mua_dang_chay(ngay) or []:
			doi_mua += _ghi_lai_hinh("Vagabond Mua Vu Dong", {"parent": ten}, anh_theo_ma)
	except Exception:
		pass
	doi_ngay = _ghi_lai_hinh("Kiem Banh Dong", {"parent": "KB-%s" % ngay}, anh_theo_ma)
	gan, loi = _gan_anh_mon_trong(tat_ca, anh_theo_ma)
	thieu = ma_thieu_anh(tat_ca, anh_theo_ma)

	kq = {
		"luc": str(now_datetime())[:16],
		"boi": frappe.session.user,
		"so_ma_pancake": len(danh_muc),
		"tong_len_web": len(tat_ca),
		"da_xoa_dem": da_xoa_dem,
		"doi_anh_mua_vu": doi_mua,
		"doi_anh_hom_nay": doi_ngay,
		"gan_anh_mon": gan[:50],
		"loi_gan_anh": loi[:50],
		"thieu_anh_tren_pancake": thieu[:100],
	}
	try:
		frappe.db.set_default(KHOA_LAN_CUOI, json.dumps(kq, ensure_ascii=False))
	except Exception:
		pass
	frappe.db.commit()
	return kq
