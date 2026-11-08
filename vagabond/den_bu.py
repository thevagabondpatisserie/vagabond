# -*- coding: utf-8 -*-
"""Mã đền bù cho khách gặp sự cố (v645, anh Việt duyệt 08/11/2026).

VÌ SAO CÓ TỆP NÀY
-----------------
Giao trễ, sai trang trí, bánh hỏng: trước đây quản lý tự hứa giảm lần sau bằng
lời, không ai ghi lại, khách quay lại thì thu ngân không biết. Nghiên cứu về
đền bù (Tahir 2021) cho thấy phiếu mua hàng cho lần sau giữ niềm tin khách mua
online tốt hơn hoàn tiền một phần, và còn là một lý do để khách quay lại.

Ba mức, mỗi mức là MỘT kịch bản trong màn Tin Zalo tự động (den_bu_nhe,
den_bu_vua, den_bu_nang) để anh chọn chương trình khuyến mãi cho từng mức và
mẫu tin Zalo dùng chung. Quản lý chỉ làm một việc: ở màn Khuyến mãi bấm
"Cấp mã đền bù", gõ mã đơn, chọn mức và lý do. Máy:
  - phát mã dùng một lần, chỉ chính khách đó dùng, hạn theo kịch bản (60 ngày);
  - mã vào Ví quà của khách ngay;
  - khách đã đồng ý nhận tin Zalo và mẫu đã duyệt thì xếp gửi Zalo, không thì
    màn hiện mã để quản lý đọc cho khách;
  - mỗi đơn gốc chỉ một mã đền bù, mọi mức (khoá den_bu:<hoá đơn>);
  - ghi người cấp, lý do, đơn gốc vào mã.
Lỗi nặng (bánh hỏng) vẫn phải làm lại hoặc hoàn tiền trước: mã chỉ là phần thêm.

Phần THUẦN ở đầu tệp để bộ kiểm tầng khung gọi thẳng.
"""

import frappe

MUC = (
	("nhe", "Nhẹ", "Giao trễ hơn 30 phút, thiếu nến hoặc thiệp."),
	("vua", "Vừa", "Sai trang trí, sai lời chúc, thiếu món. Giao bù món thiếu trước."),
	("nang", "Nặng", "Bánh hỏng không dùng được. Làm lại hoặc hoàn tiền trước, mã này là phần thêm."),
)
MA_MUC = tuple(m[0] for m in MUC)
LY_DO = ("Giao trễ", "Thiếu nến, thiệp", "Sai trang trí", "Sai lời chúc", "Thiếu món", "Bánh hỏng", "Khác")


# ================================================================ phần thuần

def ten_muc(muc):
	"""Tên hiển thị của một mức. THUẦN. Mức lạ trả rỗng."""
	for m in MUC:
		if m[0] == muc:
			return m[1]
	return ""


def kich_ban_cua(muc):
	"""Mã kịch bản Zalo của mức. THUẦN."""
	return "den_bu_%s" % muc if muc in MA_MUC else ""


def chuan_ly_do(ly_do, ghi_chu=""):
	"""Lý do ghi vào mã. THUẦN. Lý do ngoài danh sách thì về Khác; Khác mà
	không có ghi chú thì báo lỗi (người đọc lại không biết chuyện gì)."""
	ld = str(ly_do or "").strip()
	if ld not in LY_DO:
		ld = "Khác"
	gc = " ".join(str(ghi_chu or "").split())[:200]
	if ld == "Khác" and not gc:
		return None, "Chọn lý do, hoặc ghi rõ chuyện gì ở ô ghi chú."
	return (ld + (": " + gc if gc else "")), ""


def che_sdt(s):
	"""0901234567 -> 090***4567. THUẦN."""
	so = "".join(ch for ch in str(s or "") if ch.isdigit())
	if len(so) < 7:
		return so
	return so[:3] + "***" + so[-4:]


# ================================================================ chạm hệ

def _hoa_don(q):
	"""Tìm hoá đơn theo mã hoá đơn, mã đơn Pancake (hiển thị) hay Pancake id."""
	q = str(q or "").strip()
	if not q:
		return None
	cot = ["name", "customer", "customer_name", "posting_date", "grand_total", "docstatus", "is_return",
		"custom_pancake_display_id", "custom_pancake_id", "vgb_huy"]
	for loc in ({"name": q}, {"custom_pancake_display_id": q}, {"custom_pancake_id": q}):
		r = frappe.db.get_value("Sales Invoice", dict(loc, is_return=0), cot, as_dict=True)
		if r and int(r.docstatus or 0) != 2:
			return r
	return None


def _ma_da_cap(hoa_don):
	from vagabond.zalo_kich_ban import DT_TIN

	return frappe.db.get_value(DT_TIN, {"khoa": "den_bu:%s" % hoa_don}, ["voucher", "kich_ban"], as_dict=True)


@frappe.whitelist()
def xem_don(q=None):
	"""Tra đơn trước khi cấp mã: khách, tiền, đã đền bù chưa, ba mức đang cài."""
	from vagabond import khuyen_mai, zalo_kich_ban as zk

	khuyen_mai._kiem_quyen_sua()
	zk._dam_bao()
	hd = _hoa_don(q)
	muc = []
	for m in MUC:
		c = zk._cau_hinh(kich_ban_cua(m[0])) or {}
		km = zk._doc_ctkm(c.get("ctkm")) or {}
		ten_ud = zk.mo_ta_uu_dai(km, c.get("ten_uu_dai"), c.get("dieu_kien"))[0] if km else ""
		muc.append({"ma": m[0], "ten": m[1], "giai_thich": m[2], "uu_dai": ten_ud,
			"chua_cai": 0 if km else 1})
	if not hd:
		return {"ok": 0, "muc": muc, "ds_ly_do": list(LY_DO),
			"ly_do": "Không tìm thấy đơn này. Gõ mã hoá đơn hoặc mã đơn Pancake." if q else ""}
	cap = _ma_da_cap(hd.name)
	kh = zk._ho_so(hd.customer) if hd.customer else {}
	return {
		"ok": 1, "muc": muc, "ds_ly_do": list(LY_DO), "hoa_don": hd.name, "ma_don": hd.custom_pancake_display_id or hd.name,
		"ngay": zk.ngay_vn(hd.posting_date), "tien": zk.tien_vn(hd.grand_total),
		"khach": "" if zk._la_khach_gop(hd.customer) else (hd.customer_name or hd.customer),
		"sdt": che_sdt((kh or {}).get("sdt84")), "dong_y": 1 if (kh or {}).get("dong_y") else 0,
		"khach_le": 1 if zk._la_khach_gop(hd.customer) else 0,
		"da_cap": (cap or {}).get("voucher") or "", "da_cap_muc": ten_muc(str((cap or {}).get("kich_ban") or "").replace("den_bu_", "")),
	}


@frappe.whitelist(methods=["POST"])
def cap_ma(q=None, muc=None, ly_do=None, ghi_chu=None):
	"""Cấp MỘT mã đền bù cho đơn `q`. Trả mã, hạn, có xếp gửi Zalo không."""
	from vagabond import khuyen_mai, zalo_kich_ban as zk

	khuyen_mai._kiem_quyen_sua()
	if muc not in MA_MUC:
		frappe.throw("Chọn mức đền bù: Nhẹ, Vừa hoặc Nặng.")
	ld, loi = chuan_ly_do(ly_do, ghi_chu)
	if loi:
		frappe.throw(loi)
	zk._dam_bao()
	hd = _hoa_don(q)
	if not hd:
		frappe.throw("Không tìm thấy đơn này. Gõ mã hoá đơn hoặc mã đơn Pancake.")
	if zk._la_khach_gop(hd.customer):
		frappe.throw("Đơn này là khách lẻ chưa có số điện thoại, không gắn được mã riêng. Gắn khách cho hoá đơn trước.")
	# Khoá dòng hoá đơn để hai quản lý bấm cùng lúc không ra hai mã.
	frappe.db.sql("select name from `tabSales Invoice` where name = %s for update", (hd.name,))
	cu = _ma_da_cap(hd.name)
	if cu:
		frappe.throw("Đơn này đã được cấp mã đền bù %s (mức %s). Mỗi đơn một mã."
			% (cu.get("voucher") or "", ten_muc(str(cu.get("kich_ban") or "").replace("den_bu_", ""))))
	ma_kb = kich_ban_cua(muc)
	c = zk._cau_hinh(ma_kb) or {}
	km = zk._doc_ctkm(c.get("ctkm"))
	if not km:
		frappe.throw("Mức %s chưa chọn chương trình khuyến mãi. Vào Chăm sóc khách, Tin Zalo tự động, thẻ Đền bù mức %s để chọn."
			% (ten_muc(muc), ten_muc(muc).lower()))
	hom_nay = zk._bay_gio().date()
	han, loi = zk.ctkm_phat_duoc(km, hom_nay, c.get("han_ngay"))
	if not han:
		frappe.throw(loi)
	kh = zk._ho_so(hd.customer)
	# Codex PR 548 c02f2be: chương trình của mức có thể chỉ dành cho một hạng,
	# nhóm hay danh sách khách. Kiểm bằng đúng phép của quầy trước khi phát mã,
	# không thì khách cầm mã đền bù mà quầy không giảm, và khoá một mã mỗi đơn
	# chặn luôn việc cấp lại.
	ok_dt, ly_dt = zk._hop_doi_tuong(km, hd.customer, kh["sdt84"])
	if not ok_dt:
		frappe.throw("Chương trình của mức %s không áp cho khách này (%s). Vào Chăm sóc khách, Tin Zalo tự động, thẻ Đền bù mức %s để chọn chương trình dành cho mọi khách."
			% (ten_muc(muc), ly_dt, ten_muc(muc).lower()))
	ma = zk._sinh_ma()
	frappe.get_doc({"doctype": "Vagabond Voucher", "ma": ma, "ctkm": km.get("name"), "ten_ctkm": zk.cat(km.get("ten"), 140),
		"trang_thai": "Chua dung", "han_dung": han, "khach": zk.cat(kh["ten"], 140), "sdt": kh["sdt84"],
		"danh_cho": hd.customer, "chi_nguoi_nhan": 1, "gui_cho": zk.cat("Đền bù mức " + ten_muc(muc), 140),
		"ghi_chu": zk.cat("Đền bù mức %s, %s. Đơn gốc %s. Người cấp %s." % (ten_muc(muc), ld,
			hd.custom_pancake_display_id or hd.name, frappe.session.user), 500)}).insert(ignore_permissions=True)
	duoc, ly = zk.mau_san_sang(c)
	if not kh["sdt84"]:
		duoc, ly = False, "Khách chưa có số điện thoại."
	elif not kh["dong_y"]:
		duoc, ly = False, "Khách chưa đồng ý nhận tin Zalo."
	zk._ghi_cho(ma_kb, zk.khoa_tin(ma_kb, hoa_don=hd.name), hd.customer, hd.name, voucher=ma,
		trang_thai=zk.TT_CHO if duoc else zk.TT_BO, loi="" if duoc else "Không gửi Zalo: " + ly + " Quản lý đọc mã cho khách.")
	frappe.db.commit()
	ten_ud = zk.mo_ta_uu_dai(km, c.get("ten_uu_dai"), c.get("dieu_kien"))[0]
	return {"ok": 1, "ma": ma, "han": zk.ngay_vn(han), "uu_dai": ten_ud, "zalo": 1 if duoc else 0,
		"ly_do": "" if duoc else ly}
