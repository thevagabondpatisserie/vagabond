"""Ưu đãi khách tự chọn trên trang gọi món tại bàn (v643).

Anh Việt 06/11/2026 xin "đồng bộ ưu đãi lên trang O2O cho khách tự áp, có OTP
Zalo"; 07/11/2026 duyệt mẫu và chốt: khách chọn là MÁY TỰ TRỪ NGAY vào hoá đơn
tạm tính của bàn, quầy không phải bấm. Combo không đi đường này (đã có chip
Combo trên trang bàn). Chương trình cần OTP quản lý không hiện cho khách.

Xác minh khách: dùng lại đúng phiên đăng nhập Thành viên (mã Zalo, cookie
vgb_thanh_vien, sống 30 ngày). Khách chưa đăng nhập thì trang bàn mở bước gửi
mã và xác thực của thanh_vien, không có cửa OTP thứ hai.

Tiền: phần giảm của ưu đãi nằm RIÊNG ở vgb_giam_ud, giống vgb_giam_diem của
điểm thành viên. discount_amount luôn dựng lại bằng phần của người khác CỘNG
phần riêng (ban_hang._giam_rieng), nên nhịp đồng bộ, sửa hoá đơn, chốt bill
không xoá mất phần ưu đãi, và quyen_quay không coi nó là giảm tay cần OTP.

Lượt dùng: chỉ ghi (tiêu mã voucher, đếm lượt chương trình) LÚC CHỐT bill
(ban_hang.pos_chot gọi truoc_chot rồi sau_chot), tính lại trên giỏ cuối cùng
có khoá chương trình như quầy. Khách đổi hay bỏ ưu đãi trước đó thì không
phải trả lượt nào.
"""

import json
import re

import frappe
from frappe.rate_limiter import rate_limit
from frappe.utils import cint, flt, getdate, now_datetime, nowdate

SI = "Sales Invoice"
DT_CTKM = "Vagabond CTKM"
CACH_DUYET = "Khách xác minh Zalo tại bàn"
LOAI = ("ma", "ctkm")
CAU_CAN_OTP = "ưu đãi này cần quản lý duyệt, quý khách nhờ thu ngân áp tại quầy"

TRUONG_MOI = {
	"Sales Invoice": [
		{
			"fieldname": "vgb_giam_ud",
			"label": "Giảm giá ưu đãi khách chọn tại bàn (đ)",
			"fieldtype": "Currency",
			"insert_after": "vgb_noi_bo",
			"read_only": 1,
			"description": (
				"Phần giảm giá của ưu đãi khách tự chọn trên trang gọi món tại bàn. "
				"Tách riêng khỏi discount_amount như giảm từ điểm, để dựng lại "
				"discount_amount không xoá mất phần này."
			),
		},
		{
			"fieldname": "vgb_ud_ban",
			"label": "Ưu đãi khách chọn tại bàn",
			"fieldtype": "Small Text",
			"insert_after": "vgb_giam_ud",
			"read_only": 1,
			"hidden": 1,
		},
	]
}


# ------------------------------------------------------------------ THUẦN

def doc_ud(s):
	"""THUẦN: ưu đãi đã chọn lưu trên hoá đơn (JSON), {} khi chưa có hay hỏng."""
	if isinstance(s, dict):
		return s
	try:
		x = json.loads(s or "{}")
	except (TypeError, ValueError):
		return {}
	return x if isinstance(x, dict) and x.get("ma") and x.get("loai") in LOAI else {}


def chuan_chon(loai, ma):
	"""THUẦN: (loại, mã) khách gửi lên đã chuẩn, hoặc (None, None)."""
	loai = str(loai or "").strip()
	ma = str(ma or "").strip()
	if loai == "ma":
		ma = ma.upper()
		return (loai, ma) if re.fullmatch(r"[A-Z0-9-]{3,40}", ma) else (None, None)
	if loai == "ctkm":
		return (loai, ma) if re.fullmatch(r"[A-Za-z0-9 _.\-]{2,140}", ma) else (None, None)
	return None, None


def che_sdt(so):
	"""THUẦN: 0909123412 -> "0909 *** 412"."""
	s = re.sub(r"\D", "", str(so or ""))
	if s.startswith("84") and len(s) >= 11:
		s = "0" + s[2:]
	return (s[:4] + " *** " + s[-3:]) if len(s) >= 9 else ""


def giam_tu_kq(kq):
	"""THUẦN: (số giảm, lý do không áp) từ kết quả khuyen_mai.tinh của MỘT ưu đãi.
	Ưu đãi chính không áp được (nằm ở bo, không ở ap) thì giảm 0 kèm lý do,
	kể cả khi ưu đãi hạng thành viên vẫn áp (không tính hạng thành ưu đãi
	khách chọn)."""
	kq = kq or {}
	ap = [a for a in kq.get("ap") or [] if a.get("loai") != "hang"]
	if not ap:
		bo = [b for b in kq.get("bo") or [] if not str(b.get("ten") or "").startswith("Ưu đãi hạng")]
		return 0, (bo[0].get("ly_do") if bo else "không đủ điều kiện")
	# Codex PR #546 vòng 1: khuyen_mai.tinh chỉ BÁO cờ can_otp, không chặn. Mã
	# trong Ví quà của chương trình cần OTP quản lý đi qua đây được, nên mọi
	# đường (danh sách, chọn, gọi thêm, chốt) đều về 0 ở đúng một chỗ này.
	if any(cint(a.get("can_otp")) for a in ap):
		return 0, CAU_CAN_OTP
	giam = sum(flt(a.get("giam")) for a in ap)
	if kq.get("tong_hd") is not None:
		giam = min(giam, flt(kq.get("tong_hd")))
	return max(0.0, giam), ""


def kep_giam(giam, truoc_giam, goc):
	"""THUẦN: phần ưu đãi không được kéo hoá đơn xuống dưới 0 (cộng phần giảm khác)."""
	return max(0.0, min(flt(giam), flt(truoc_giam) - flt(goc)))


def tong_dong(items):
	"""THUẦN: tổng tiền các dòng món trước giảm cấp hoá đơn."""
	return sum(flt(d.get("vgb_combo_tien")) if flt(d.get("vgb_combo_luong")) else flt(d.get("qty")) * flt(d.get("rate"))
		for d in items or [])


def the_ud(ud):
	"""THUẦN: phần trang khách được thấy của ưu đãi trên hoá đơn bàn."""
	ud = doc_ud(ud)
	if not ud:
		return None
	return {"ten": ud.get("ten") or "", "giam": int(round(flt(ud.get("giam")))),
		"ly_do": ud.get("ly_do") or "", "sdt": che_sdt(ud.get("sdt"))}


# --------------------------------------------------------------- CHẠM HỆ

def giam_ud(si):
	"""Phần giảm của ưu đãi khách chọn trên một hoá đơn. Mặc định 0 (đọc được
	cả trước khi migrate dựng cột, bài học v177)."""
	try:
		return flt((si or {}).get("vgb_giam_ud") or 0)
	except Exception:
		return 0.0


def _items(si):
	return [{"item_code": d.get("item_code"), "qty": flt(d.get("qty")), "rate": flt(d.get("rate"))}
		for d in (si.get("items") or []) if d.get("item_code")]


def _tinh(si, ud, co_khoa=False):
	from vagabond import khuyen_mai

	f = khuyen_mai.tinh_co_khoa if co_khoa else khuyen_mai.tinh
	return f(_items(si), ctkm=[ud["ma"]] if ud["loai"] == "ctkm" else [],
		ma=ud["ma"] if ud["loai"] == "ma" else None,
		quay=si.get("vgb_quay"), nguon=si.get("custom_nguon"),
		khach=ud.get("khach") or None, sdt=ud.get("sdt") or None, ngay=str(getdate(nowdate())))


def giam_hieu_luc(si, giam):
	"""Số ưu đãi THẬT sẽ trừ trên hoá đơn này sau khi kẹp (không đổi hoá đơn).
	Trả (số thật, phần giảm khác). Một cửa cho dat_giam và truoc_chot (Codex PR
	#546 vòng 1: truoc_chot so số chưa kẹp với số đã kẹp nên chốt dừng mãi)."""
	goc = max(0.0, flt(si.get("discount_amount")) - giam_ud(si))
	# Tổng trước giảm tính lại từ dòng món (grand_total còn là số cũ khi vừa
	# thêm hay sửa món mà chưa lưu).
	return kep_giam(giam, tong_dong(si.get("items")), goc), goc


def kq_theo_so_that(kq, so_that):
	"""THUẦN: kết quả tinh với tiền giảm các dòng ưu đãi chính chỉnh về số thật
	đã trừ (bị kẹp thì chia theo tỉ lệ), để lượt dùng ghi đúng số khách nhận."""
	ap = [dict(a) for a in (kq or {}).get("ap") or [] if a.get("loai") != "hang"]
	tong = sum(flt(a.get("giam")) for a in ap)
	if tong > 0 and so_that < tong - 0.5:
		con = int(round(so_that))
		for i, a in enumerate(ap):
			g = con if i == len(ap) - 1 else int(round(flt(a.get("giam")) * so_that / tong))
			a["giam"] = g
			con -= g
	return dict(kq or {}, ap=ap, tong_giam=sum(flt(a.get("giam")) for a in ap))


def dat_giam(si, giam):
	"""Đặt lại phần ưu đãi trên hoá đơn đang mở (KHÔNG lưu, bên gọi lưu).
	Phần giảm khác (giảm tay, điểm, Pancake) giữ nguyên, không cộng dồn khi
	gọi nhiều lần."""
	moi, goc = giam_hieu_luc(si, giam)
	si.vgb_giam_ud = moi
	si.apply_discount_on = "Grand Total"
	si.discount_amount = goc + moi
	return moi


def tinh_lai(si):
	"""Giỏ của bàn đổi (gọi thêm, quầy sửa món): tính lại phần ưu đãi trên
	giỏ mới, không lưu. Ưu đãi chưa đủ điều kiện (ví dụ đơn tối thiểu) thì
	giữ lựa chọn, giảm 0 kèm lý do, đủ thì tự áp lại."""
	ud = doc_ud(si.get("vgb_ud_ban"))
	if not ud or ud.get("da_ghi"):
		return
	try:
		giam, ly_do = giam_tu_kq(_tinh(si, ud))
	except Exception as e:
		giam, ly_do = 0, str(e)[:140]
	ud.update(giam=int(round(dat_giam(si, giam))), ly_do=ly_do)
	si.vgb_ud_ban = json.dumps(ud, ensure_ascii=False)


def _phien():
	"""(sdt nội địa, khách) của phiên Thành viên đang đăng nhập, hoặc (None, None)."""
	from vagabond import thanh_vien

	so = thanh_vien._so_phien()
	if not so:
		return None, None
	nd = thanh_vien._dn()._sdt_noi_dia(so)
	kh, ly = thanh_vien._khach_cua_so(nd)
	return nd, (kh or {}).get("name") if not ly else None


def _hoa_don_ban(d, ban, khoa=False):
	from vagabond import goi_mon_ban

	ten = goi_mon_ban._phieu_tam_cua_ban(d["ma"], ban, getdate())
	if not ten:
		return None
	si = frappe.get_doc(SI, ten, for_update=khoa) if khoa else frappe.get_doc(SI, ten)
	if si.docstatus != 0 or not cint(si.get("vgb_tam_tinh")) or cint(si.get("vgb_huy")):
		return None
	return si


def loc_ctkm(ds, nguon, quay, hop_kenh, cach_giam):
	"""THUẦN: chương trình khách tự chọn được tại bàn. Bỏ chương trình cần mã
	(mã đi qua Ví quà), cần OTP quản lý, tặng món (khách không tự thêm món
	được), và chương trình không mở cho nguồn hay quầy của bàn. Chương trình
	lệch khung giờ, hết lượt vẫn giữ để trang hiện mờ kèm lý do."""
	ra = []
	for x in ds or []:
		if (x.get("cach_ma") or "Khong can ma") != "Khong can ma" or cint(x.get("can_otp")):
			continue
		if x.get("cach_thuc") not in cach_giam:
			continue
		if not hop_kenh(x, nguon, quay)[0]:
			continue
		ra.append(x)
	return ra


def _ds_ctkm(d, si):
	from vagabond import goi_mon_ban, khuyen_mai

	ds = frappe.get_all(DT_CTKM, filters={"bat": 1, "can_otp": 0},
		fields=["name", "ten", "cach_ma", "cach_thuc", "can_otp", "kenh", "quay", "web_mo_ta"],
		order_by="uu_tien asc, ten asc", limit_page_length=100)
	nguon = (si.get("custom_nguon") if si else None) or goi_mon_ban.NGUON_QR
	quay = (si.get("vgb_quay") if si else None) or d.get("quay") or d.get("ma")
	return loc_ctkm(ds, nguon, quay, khuyen_mai._hop_kenh, khuyen_mai.CACH_THUC_WEB)


def _vi(khach):
	from vagabond import thanh_vien

	if not khach:
		return []
	return [v for v in thanh_vien._vi(khach, thanh_vien._hom_nay()) if v.get("trang_thai") == "dung_duoc"]


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=600)
def ds(diem=None, ban=None, k=None):
	"""Danh sách ưu đãi khách dùng được cho hoá đơn của bàn, kèm số giảm dự kiến."""
	from vagabond import goi_mon_ban

	try:
		frappe.local.response_headers["Cache-Control"] = "private, no-store"
	except Exception:
		pass  # ngoài một lượt gọi web (bench, lịch) không có response_headers
	d, n = goi_mon_ban._kiem_link(diem, ban, k)
	if not d:
		return {"ok": 0, "cau": "Link bàn không đúng, quý khách quét lại mã QR trên bàn."}
	nd, khach = _phien()
	if not nd:
		return {"ok": 1, "dang_nhap": 0}
	si = _hoa_don_ban(d, n)
	chon = the_ud(si.get("vgb_ud_ban")) if si else None
	ra = []
	for v in _vi(khach):
		ra.append({"loai": "ma", "ma": v["ma"], "nhom": "vi", "ten": v.get("uu_dai") or v.get("ten") or "",
			"phu": " · ".join(x for x in ("Mã " + v["ma"], ("hạn " + v["han"]) if v.get("han") else "",
				v.get("dieu_kien") or "") if x)})
	for c in _ds_ctkm(d, si):
		ra.append({"loai": "ctkm", "ma": c["name"], "nhom": "ctkm", "ten": c.get("ten") or c["name"],
			"phu": (c.get("web_mo_ta") or "")[:140]})
	for x in ra:
		x["giam"], x["ly_do"] = None, ""
		if si:
			try:
				giam, ly = giam_tu_kq(_tinh(si, {"loai": x["loai"], "ma": x["ma"], "sdt": nd, "khach": khach}))
			except Exception as e:
				giam, ly = 0, str(getattr(e, "message", "") or e)[:140]
			x["giam"], x["ly_do"] = int(round(giam)), ly
		x["dung_duoc"] = 1 if (x["giam"] or 0) > 0 else 0
	ra.sort(key=lambda x: (0 if x["nhom"] == "vi" else 1, -x["dung_duoc"], -(x["giam"] or 0)))
	return {"ok": 1, "dang_nhap": 1, "sdt": che_sdt(nd), "co_hoa_don": 1 if si else 0, "chon": chon, "ds": ra}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=600)
def chon(diem=None, ban=None, k=None, loai=None, ma=None):
	"""Khách chọn một ưu đãi: máy tự trừ ngay vào hoá đơn tạm tính của bàn."""
	from vagabond import goi_mon_ban

	d, n = goi_mon_ban._kiem_link(diem, ban, k)
	if not d:
		return {"ok": 0, "cau": "Link bàn không đúng, quý khách quét lại mã QR trên bàn."}
	nd, khach = _phien()
	if not nd:
		return {"ok": 0, "cau": "Quý khách đăng nhập bằng mã Zalo trước khi chọn ưu đãi.", "dang_nhap": 0}
	loai, ma = chuan_chon(loai, ma)
	if not loai:
		return {"ok": 0, "cau": "Ưu đãi không đúng, quý khách chọn lại."}
	si = _hoa_don_ban(d, n, khoa=True)
	if not si:
		return {"ok": 0, "cau": "Bàn chưa có hoá đơn. Quý khách gọi món và chờ quầy nhận rồi chọn ưu đãi."}
	cu = doc_ud(si.get("vgb_ud_ban"))
	if cu and re.sub(r"\D", "", str(cu.get("sdt"))) != re.sub(r"\D", "", nd):
		return {"ok": 0, "cau": "Bàn đã dùng ưu đãi của số %s. Mỗi hoá đơn một ưu đãi." % che_sdt(cu.get("sdt"))}
	if loai == "ctkm" and not any(c["name"] == ma for c in _ds_ctkm(d, si)):
		return {"ok": 0, "cau": "Chương trình này không dùng được tại bàn."}
	if loai == "ma" and not any(v["ma"] == ma for v in _vi(khach)):
		return {"ok": 0, "cau": "Mã này không có trong Ví quà của quý khách."}
	ud = {"loai": loai, "ma": ma, "sdt": nd, "khach": khach or "", "luc": str(now_datetime())}
	try:
		kq = _tinh(si, ud)
	except Exception as e:
		return {"ok": 0, "cau": str(getattr(e, "message", "") or e)[:200] or "Chưa áp được ưu đãi này."}
	giam, ly = giam_tu_kq(kq)
	if giam <= 0:
		return {"ok": 0, "cau": "Ưu đãi chưa dùng được cho hoá đơn này: %s." % ly}
	ten = next((a.get("ten") for a in kq.get("ap") or [] if a.get("loai") != "hang"), "") or ma
	ud.update(ten=ten, ly_do="")
	ud["giam"] = int(round(dat_giam(si, giam)))
	si.vgb_ud_ban = json.dumps(ud, ensure_ascii=False)
	si.flags.ignore_permissions = True
	si.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "chon": the_ud(ud), "tong": int(round(flt(si.grand_total)))}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=600)
def bo(diem=None, ban=None, k=None):
	"""Khách bỏ ưu đãi đã chọn (chỉ chính số đã chọn)."""
	from vagabond import goi_mon_ban

	d, n = goi_mon_ban._kiem_link(diem, ban, k)
	if not d:
		return {"ok": 0, "cau": "Link bàn không đúng, quý khách quét lại mã QR trên bàn."}
	nd, _kh = _phien()
	si = _hoa_don_ban(d, n, khoa=True) if nd else None
	cu = doc_ud(si.get("vgb_ud_ban")) if si else {}
	if not cu:
		return {"ok": 1}
	if re.sub(r"\D", "", str(cu.get("sdt"))) != re.sub(r"\D", "", nd or ""):
		return {"ok": 0, "cau": "Chỉ số đã chọn ưu đãi mới bỏ được."}
	_go(si)
	si.flags.ignore_permissions = True
	si.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "tong": int(round(flt(si.grand_total)))}


def _go(si):
	dat_giam(si, 0)
	si.vgb_ud_ban = ""


@frappe.whitelist()
def bo_quay(name=None, ly_do=""):
	"""Thu ngân bỏ ưu đãi khách chọn trên bill tạm tính (khách đổi ý, nhầm bàn)."""
	from vagabond import ban_hang

	ban_hang._kiem_quyen_ban()
	si = frappe.get_doc(SI, name, for_update=True)
	if si.docstatus != 0:
		frappe.throw("Hoá đơn đã ghi sổ rồi, không bỏ ưu đãi ở đây được.")
	cu = doc_ud(si.get("vgb_ud_ban"))
	if not cu:
		return {"ok": 1}
	if cu.get("da_ghi"):
		frappe.throw("Ưu đãi đã ghi lượt dùng lúc chốt bill, không bỏ ở đây được.")
	_go(si)
	si.add_comment("Comment", "Bỏ ưu đãi khách chọn tại bàn (%s). Lý do: %s" % (cu.get("ten") or cu.get("ma"), (ly_do or "").strip() or "không ghi"))
	si.flags.ignore_permissions = True
	si.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "grand_total": flt(si.grand_total)}


class UuDaiDoi(frappe.ValidationError):
	pass


def truoc_chot(si):
	"""ban_hang.pos_chot gọi trước khi lưu: tính lại ưu đãi trên giỏ cuối cùng
	có khoá chương trình. Số khác số khách đang thấy thì đặt số mới, lưu, rồi
	DỪNG chốt để thu ngân báo khách số mới. Trả kết quả tinh để sau_chot ghi lượt."""
	ud = doc_ud(si.get("vgb_ud_ban"))
	if not ud or ud.get("da_ghi"):
		return None
	kq = _tinh(si, ud, co_khoa=True)
	giam, ly = giam_tu_kq(kq)
	cu = giam_ud(si)
	that, _goc = giam_hieu_luc(si, giam)
	if abs(that - cu) > 0.5:
		moi = dat_giam(si, giam)
		ud.update(giam=int(round(moi)), ly_do=ly)
		si.vgb_ud_ban = json.dumps(ud, ensure_ascii=False)
		si.flags.ignore_permissions = True
		si.save(ignore_permissions=True)
		frappe.db.commit()
		frappe.throw(
			"Ưu đãi khách chọn (%s) đổi từ %s đ thành %s đ%s. Tổng mới %s đ: báo khách rồi bấm Chốt lại."
			% (ud.get("ten") or ud.get("ma"), "{:,.0f}".format(cu).replace(",", "."), "{:,.0f}".format(moi).replace(",", "."),
				(" (" + ly + ")") if ly else "", "{:,.0f}".format(flt(si.grand_total)).replace(",", ".")),
			exc=UuDaiDoi, title="Ưu đãi của bàn đã đổi")
	return kq_theo_so_that(kq, that) if that > 0 else None


def sau_chot(si, kq):
	"""Sau khi bill chốt lưu xong: ghi lượt dùng, tiêu mã voucher, đánh dấu đã ghi."""
	ud = doc_ud(si.get("vgb_ud_ban"))
	if not ud or ud.get("da_ghi") or not kq:
		return
	from vagabond import khuyen_mai

	kq = dict(kq, ap=[a for a in kq.get("ap") or [] if a.get("loai") != "hang"])
	khuyen_mai.ghi_su_dung(kq, si.name, quay=si.get("vgb_quay"), nguon=si.get("custom_nguon"),
		khach=ud.get("khach"), sdt=ud.get("sdt"), cach_duyet=CACH_DUYET, ghi_chu="Bàn %s" % (si.get("vgb_so_ban") or ""))
	ud["da_ghi"] = 1
	frappe.db.set_value(SI, si.name, "vgb_ud_ban", json.dumps(ud, ensure_ascii=False), update_modified=False)
