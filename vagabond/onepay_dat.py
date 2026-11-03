# -*- coding: utf-8 -*-
"""Khách trả thẻ OnePay cho đơn đặt trước tại quầy (v637).

Anh Việt 03/11/2026: "chỗ đơn đặt trước mà thu ngân ở quầy lên đơn cho khách
thì em cho thêm phương thức OnePay vô đó, để thu ngân không cần phải sử dụng
máy cà thẻ tại quầy, để tách biệt riêng tiền cà thẻ vào cho tiền của bên
Sales". Anh chọn (cùng ngày):
  - Khách quét QR trên màn quầy bằng điện thoại, nhập thẻ trên trang OnePay.
    Trả xong màn quầy tự báo, thu ngân không chạm thẻ.
  - Đơn đặt trước bỏ "thẻ chụp bill máy POS", chỉ còn OnePay.
  - Chỉ đơn đặt trước; bill bán lẻ giữ nguyên.

Dòng tiền: OnePay báo thành công thì GHI SỔ NGAY một phiếu thu ứng trước của
đúng phiếu đặt, phương thức "OnePay" (tài khoản phương thức đó, 11211 MB),
quầy = điểm bán KHÔNG có két (Sales Online). Vì không mang quầy cửa hàng nên
Chốt ca không đếm khoản này: tiền thẻ là tiền của Sales, không phải của két
(cùng quy ước với tiền chuyển khoản của đơn, xem thiet_ke_rieng.py "QUẦY CỦA
PHIẾU THU"). Biên nhận OnePay đính vào phiếu thu trước khi ghi sổ (hook
chan_thieu_dinh_kem đòi chứng từ cho phiếu qua ngân hàng).

Phần chung với phiếu công nợ (chữ ký, cổng, trang /tra-the, IPN, tra cứu 15
phút) nằm ở onepay.py; onepay.py chuyển sang đây khi mã là mã đơn đặt trước.
Nhật ký giao dịch cất trên phiếu đặt (ô ẩn vgb_onepay_gd), cùng dạng với ô
onepay_gd của phiếu công nợ.
"""

import json
import re

# Mã đơn đặt trước nhận trả thẻ -> ô mang mã trên phiếu đặt. Thêm loại đơn mới
# (đơn quầy D1, bánh sỉ) là thêm một dòng ở đây, cùng mẫu ở RE_MA_DON.
LOAI = {"TKR": "vgb_tkr_ma"}
RE_MA_DON = re.compile(r"^(TKR[0-9]{8})$")
TRUONG_NK = "vgb_onepay_gd"


def la_ma_don(ma):
	"""Mã (đã bỏ gạch) có phải mã đơn đặt trước nhận trả thẻ không. THUẦN."""
	return bool(RE_MA_DON.match(str(ma or "").strip().upper()))


def truong_ma(ma):
	"""Ô mang mã trên phiếu đặt cho một mã đơn. THUẦN."""
	return LOAI.get(str(ma or "").strip().upper()[:3]) if la_ma_don(ma) else None


def ghi_chu_phieu(ma_don, kq):
	"""Diễn giải phiếu thu thẻ. THUẦN."""
	return ("Khách trả thẻ qua OnePay cho đơn %s, mã giao dịch %s, mã OnePay %s. Tiền của Sales, không vào két quầy."
		% (ma_don, kq.get("ma") or "", kq.get("ma_onepay") or ""))[:1000]


def tien_vn(x):
	try:
		return "{:,.0f}".format(round(float(x or 0))).replace(",", ".")
	except (TypeError, ValueError):
		return "0"


def khoa_phieu_thu(ma_gd):
	"""reference_no của phiếu thu một giao dịch: khoá chống ghi hai lần. THUẦN."""
	return ("onepay:%s" % ma_gd)[:140]


def chon_quay(ds_diem):
	"""Quầy ghi trên phiếu thu thẻ: điểm bán KHÔNG có két, như tiền chuyển khoản.
	Không bao giờ là quầy cửa hàng, nên Chốt ca không đếm. THUẦN."""
	from vagabond.ung_truoc_don import quay_chuyen_khoan

	return quay_chuyen_khoan(ds_diem)


# ------------------------------------------------------------- chạm Frappe

import frappe  # noqa: E402
from frappe.utils import flt  # noqa: E402

SO = "Sales Order"
PE = "Payment Entry"


def _ten_don(ma):
	o = truong_ma(ma)
	if not o:
		return None
	return frappe.db.get_value(SO, {o: str(ma).strip().upper(), "docstatus": ["<", 2]}, "name")


def tim_don(ma, k):
	"""Mã trên đường dẫn + khoá -> tên phiếu đặt. Sai khoá thì như không có."""
	import hmac

	from vagabond import onepay as op

	ma = re.sub(r"[^A-Z0-9]", "", str(ma or "").upper())
	if not la_ma_don(ma) or not isinstance(k, str) or not re.fullmatch(r"[0-9a-f]{16}", k):
		return None
	ten = _ten_don(ma)
	if not ten or not hmac.compare_digest(op.khoa_phieu(ma), k):
		return None
	return ten


def link_don(ma):
	"""Địa chỉ tuyệt đối trang trả thẻ của một đơn, vẽ thành QR trên màn quầy."""
	from vagabond import onepay as op
	from vagabond.ten_mien import link_khach

	return link_khach(op.duong_trang(ma, op.khoa_phieu(ma)))


def _tom_tat(ten, khoa=False):
	from vagabond.thiet_ke_rieng import tom_tat

	return tom_tat(ten, khoa=khoa)


def _khoa(ten):
	from vagabond.thiet_ke_rieng import _khoa_don

	_khoa_don(ten)


def thong_tin_trang(ma, k):
	"""Dữ liệu trang /tra-the cho một đơn đặt trước (cùng khuôn với phiếu công nợ)."""
	from vagabond import onepay as op

	ten = tim_don(ma, k)
	if not ten:
		return None
	t = _tom_tat(ten)
	return {"ten": ten, "ma_phieu": t["ma"], "khach": t["khach"], "tong": flt(t["tong"]),
		"con": flt(t["con_lai"]) if t["trang_thai"] not in ("da_huy", "da_giao") else 0.0,
		"huy": t["trang_thai"] == "da_huy", "dung_duoc": op.dung_duoc()}


def tao_gd(ma, k):
	"""Khách bấm trả thẻ trên trang: một giao dịch mới cho SỐ CÒN PHẢI THU đọc ở
	máy chủ trong khoá phiếu đặt."""
	from vagabond import onepay as op

	ten = tim_don(ma, k)
	if not ten:
		frappe.throw("Không tìm thấy đơn đặt bánh.")
	c = op.cau_hinh()
	if not op.dung_duoc(c):
		frappe.throw("Thanh toán thẻ đang tạm ngưng. Quý khách vui lòng thanh toán tại quầy.")
	_khoa(ten)
	t = _tom_tat(ten, khoa=True)
	if t["trang_thai"] == "da_huy":
		frappe.throw("Đơn này đã huỷ. Quý khách liên hệ The Vagabond.")
	con = flt(t["con_lai"]) if t["trang_thai"] != "da_giao" else 0.0
	if con < 1:
		frappe.throw("Đơn này đã được thanh toán đủ. Cảm ơn quý khách.")
	if con < op.TIEN_TOI_THIEU:
		frappe.throw("Số còn lại dưới 10.000 đ nên không trả bằng thẻ được. Quý khách vui lòng thanh toán tại quầy.")
	nk = op.doc_nhat_ky(frappe.db.get_value(SO, ten, TRUONG_NK, for_update=True))
	lan = op.lan_tiep(nk)
	if lan > op.SO_LAN_TOI_DA:
		frappe.throw("Đơn này đã thử thanh toán thẻ quá nhiều lần. Quý khách thanh toán tại quầy giúp tiệm.")
	ma_moi = op.ma_gd(t["ma"], lan)
	duong = link_don(t["ma"])
	ts = op.tham_so_tra(c, ma_moi, con, t["ma"], duong + "&ve=1", getattr(frappe.local, "request_ip", None), duong)
	nk.append({"ma": ma_moi, "so_tien": con, "tao_luc": str(frappe.utils.now_datetime())[:19], "trang_thai": "cho"})
	frappe.db.set_value(SO, ten, TRUONG_NK, json.dumps(nk, ensure_ascii=False), update_modified=False)
	frappe.db.commit()
	return {"url": op.url_tra(c, ts)}


def _phieu_cua_gd(ten, ma_gd):
	"""Phiếu thu ĐÃ GHI SỔ của một giao dịch, đọc lại sổ theo khoá chống trùng."""
	ds = frappe.get_all(PE, filters={"reference_no": khoa_phieu_thu(ma_gd), "vgb_phieu_dat": ten, "docstatus": 1},
		fields=["name", "paid_amount"], order_by="name asc", limit_page_length=0)
	return [r["name"] for r in ds], sum(flt(r["paid_amount"]) for r in ds)


def _lap_phieu(ten, t, kq, so):
	"""Lập và ghi sổ phiếu thu thẻ, đính biên nhận OnePay trước khi ghi sổ."""
	from vagabond import onepay as op
	from vagabond.cong_no import bien_nhan_the_html
	from vagabond.thiet_ke_rieng import _cong_ty, _ds_diem, _hom_nay, loi_phieu, phieu_thu
	from vagabond.thu_tien import _giu_chu, loi_chua_khai_tk, nang_quyen_lap_phieu, tk_tien_thu

	cty = _cong_ty()
	tk, _ba = tk_tien_thu(cty, op.PT)
	if not tk:
		raise frappe.ValidationError(loi_chua_khai_tk(op.PT))
	khach = frappe.db.get_value(SO, ten, "customer")
	p = phieu_thu(ten, khach, t["tong"], so, chon_quay(_ds_diem()), op.PT, _hom_nay(), None, ghi_chu_phieu(t["ma"], kq))
	p["reference_no"] = khoa_phieu_thu(kq["ma"])
	loi = loi_phieu(p)
	if loi:
		raise frappe.ValidationError(loi)
	luc = str(frappe.utils.now_datetime())[:19]
	with nang_quyen_lap_phieu() as goc:
		pe = frappe.get_doc(dict(p, company=cty, paid_to=tk))
		pe.setup_party_account_field()
		pe.set_missing_values()
		pe.flags.ignore_permissions = True
		pe.insert(ignore_permissions=True)
		frappe.get_doc({
			"doctype": "File", "file_name": "onepay-%s.html" % kq["ma"], "is_private": 1,
			"attached_to_doctype": PE, "attached_to_name": pe.name,
			"content": bien_nhan_the_html("Đơn đặt bánh %s" % t["ma"], kq, so, luc),
		}).insert(ignore_permissions=True)
		pe.submit()
		_giu_chu(pe, goc)
	return pe.name


def ghi_nhan_the(ma_don, kq, nguon):
	"""Ghi một kết quả OnePay (đã đọc, đã kiểm chữ ký) cho đơn đặt trước. Lặp
	lại bao nhiêu lần cũng chỉ ghi một phiếu thu. Lập phiếu hỏng thì NÉM để
	người gọi lùi lại (IPN không xác nhận, OnePay gọi lại sau)."""
	from vagabond import onepay as op

	ten = _ten_don(ma_don)
	if not ten:
		return {"ok": 1, "ly_do": "gd_la", "kq": kq}
	_khoa(ten)
	nk = op.doc_nhat_ky(frappe.db.get_value(SO, ten, TRUONG_NK, for_update=True))
	gd = op.tim_gd(nk, kq["ma"])

	def _luu():
		frappe.db.set_value(SO, ten, TRUONG_NK, json.dumps(nk, ensure_ascii=False), update_modified=False)

	if gd and not kq["thanh_cong"]:
		if gd.get("trang_thai") == "cho":
			gd.update(trang_thai="that_bai", ma_kq=kq.get("ma_kq"))
			_luu()
			frappe.db.commit()
		return {"ok": 1, "ly_do": "khong_thanh_cong", "kq": kq}
	t = _tom_tat(ten, khoa=True)
	con = flt(t["con_lai"]) if t["trang_thai"] not in ("da_huy", "da_giao") else 0.0
	ghi, so, ly_do = op.xet_ghi_nhan(gd, kq, con)
	if not ghi:
		return {"ok": 1, "ly_do": ly_do, "kq": kq}
	# Phiếu thu của giao dịch này đã có (lượt trước lập xong rồi lỗi trước khi
	# ghi nhật ký) thì không lập lần hai: đọc lại sổ.
	pe, da_ghi = _phieu_cua_gd(ten, kq["ma"])
	if not pe and so > 0.5:
		pe = [_lap_phieu(ten, t, kq, so)]
		pe, da_ghi = _phieu_cua_gd(ten, kq["ma"])
	dc = op.doi_chieu_ghi(kq.get("so_tien"), so, da_ghi)
	gd.update(trang_thai="da_ghi", ma_onepay=kq.get("ma_onepay"), the=kq.get("the"), so_ghi=dc["so_ghi"],
		du=dc["du"], ghi_luc=str(frappe.utils.now_datetime())[:19], nguon=nguon, phieu_thu=pe)
	_luu()
	cau_du = (" Khách trả dư %s đ (đơn đã được trả ở chỗ khác), Sales hoàn lại cho khách."
		% tien_vn(dc["du"])) if dc["du"] > 0.5 else ""
	frappe.get_doc(SO, ten).add_comment("Comment", "Khách trả thẻ OnePay %s đ (mã giao dịch %s, mã OnePay %s). "
		"Phiếu thu đã ghi sổ: %s.%s" % (tien_vn(kq.get("so_tien")), kq["ma"], kq.get("ma_onepay") or "",
			", ".join(pe) or "không có", cau_du))
	frappe.db.commit()
	return {"ok": 1, "ly_do": ly_do, "kq": kq, "phieu_thu": pe}


@frappe.whitelist()
def ma_the(name):
	"""Màn quầy (Thu phần còn lại, cách Thẻ OnePay): link và mã QR trang trả thẻ
	của đơn, cùng số còn phải thu để màn biết tiền đã về chưa."""
	from vagabond import onepay as op
	from vagabond.qr_chuyen_khoan import anh_lien_ket
	from vagabond.thiet_ke_rieng import _kiem_quyen

	_kiem_quyen()
	t = _tom_tat(name)
	if not op.dung_duoc():
		frappe.throw("Thanh toán thẻ OnePay đang tắt. Bật ở Cài đặt lõi và API, mục Thanh toán thẻ OnePay.")
	link = link_don(t["ma"])
	return {"ma": t["ma"], "link": link, "anh": anh_lien_ket(link), "con_lai": t["con_lai"],
		"trang_thai": t["trang_thai"]}


@frappe.whitelist()
def con_lai(name):
	"""Màn quầy hỏi lại mỗi vài giây khi đang chờ khách trả thẻ."""
	from vagabond.thiet_ke_rieng import _kiem_quyen

	_kiem_quyen()
	t = _tom_tat(name)
	return {"con_lai": t["con_lai"], "trang_thai": t["trang_thai"]}
