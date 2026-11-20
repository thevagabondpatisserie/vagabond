"""Tích điểm cho hoá đơn gọi món tại bàn (v677, anh Việt duyệt 20/11/2026).

Dễ (quầy Quận 1) báo 20/11/2026: bill gọi qua QR đứng tên khách chung "Khách
lẻ Online" (tên hiện "Khách bàn B8"), màn Sửa hoá đơn chỉ có ô xuất hoá đơn,
trang gọi món của khách cũng không có chỗ nhập thành viên, nên chốt bill không
cộng điểm cho ai. Anh Việt chọn phương án A cho cả hai phía:

- Khách: đăng nhập Thành viên bằng mã Zalo (cùng phiên 30 ngày của trang
  Thành viên, không có cửa OTP thứ hai) rồi hoá đơn tạm tính của bàn tự gắn
  khách của số đó. Gõ số không cần mã (phương án B) bị loại vì ai cũng gõ được
  số người khác để lấy điểm.
- Quầy: bill Tạm tính có khối Khách thành viên, tìm khách có sẵn hoặc tạo
  khách mới bằng số điện thoại, gỡ được khi bill còn Tạm tính.

Điểm KHÔNG cộng ở đây: chỉ đổi customer của hoá đơn nháp. Lúc chốt bill, hook
khach_hang.cong_diem_hoa_don cộng điểm cho khách thật của hoá đơn (bỏ qua khách
gộp), đúng như bill bán tại quầy. Bill đã chốt thì không đổi khách (đã ghi sổ).

Một bàn một khách tích điểm: người gắn trước giữ, số khác đăng nhập sau chỉ
thấy câu báo, muốn đổi thì quầy đổi. Hoá đơn đã dùng ưu đãi của một số thì chỉ
số đó gắn được, để điểm và ưu đãi không thuộc hai người.
"""

import re

import frappe
from frappe.rate_limiter import rate_limit
from frappe.utils import cint

SI = "Sales Invoice"
CAU_LINK = "Link bàn không đúng, quý khách quét lại mã QR trên bàn."
CAU_DANG_NHAP = "Quý khách đăng nhập bằng mã Zalo trước khi tích điểm."
CAU_CHO_HD = "Quầy nhận món xong thì hoá đơn của bàn mới tích điểm được."
CAU_KHAC = "Hoá đơn bàn đã tích điểm cho một số khác. Cần đổi thì quý khách báo nhân viên."
CAU_DOI_CHIEU = "Số này cần quầy đối chiếu hồ sơ trước khi tích điểm. Quý khách báo nhân viên giúp."


def trang_thai(khach_bill, khach_toi, la_gop):
	"""THUẦN. 'gan': hoá đơn đã của khách tôi; 'trong': hoá đơn còn đứng tên
	khách gộp, gắn được; 'khac': hoá đơn đã của một khách thật khác."""
	if la_gop or not (khach_bill or "").strip():
		return "trong"
	return "gan" if khach_toi and khach_bill == khach_toi else "khac"


def _so(x):
	return re.sub(r"\D", "", str(x or ""))[-9:]


def ud_cua_so_khac(ud, sdt):
	"""THUẦN. Hoá đơn đã dùng ưu đãi của một số KHÁC số đang đăng nhập."""
	cu = _so((ud or {}).get("sdt"))
	return bool(cu) and cu != _so(sdt)


def lech_chu_ud(ud, khach_moi):
	"""THUẦN (Codex #596 vòng 2). Hoá đơn đã dùng ưu đãi của một khách, gắn khách
	tích điểm KHÁC thì điểm và ưu đãi thuộc hai người. Ưu đãi chưa có khách
	(khach rỗng) cũng coi là lệch với mọi khách thật, để không đoán."""
	if not ud or not khach_moi:
		return False
	return (ud.get("khach") or "") != khach_moi


CAU_UD_KHAC = ("Bill đang dùng ưu đãi của số %s. Bấm Bỏ ưu đãi này trên bill trước, "
	"rồi mới gắn khách khác để tích điểm.")


def kiem_cung_chu(si, khach_moi):
	"""Cửa ghi khách nào cũng gọi (gan_quay, ban_hang.luu_khach_no): khách mới
	phải là chủ của ưu đãi đang dùng trên hoá đơn, nếu có."""
	from vagabond import uu_dai_ban

	ud = uu_dai_ban.doc_ud(si.get("vgb_ud_ban"))
	if lech_chu_ud(ud, khach_moi):
		frappe.throw(CAU_UD_KHAC % uu_dai_ban.che_sdt(ud.get("sdt")))


def the_tv(tt, sdt):
	"""THUẦN. Phần tích điểm trả cho trang khách: không lộ mã khách."""
	from vagabond.uu_dai_ban import che_sdt

	return {"trang_thai": tt, "sdt": che_sdt(sdt)}


def _la_gop(kh):
	"""Khách chung của quầy (khach_hang.la_khach_gop). Rỗng thì khỏi nạp
	ban_hang: CI tay không có requests mà ban_hang nạp requests ở đầu tệp."""
	if not (kh or "").strip():
		return True
	from vagabond import khach_hang

	return khach_hang.la_khach_gop(kh)


def tv_cho_ds(si, sdt, khach):
	"""Trạng thái tích điểm của hoá đơn bàn cho danh sách ưu đãi (uu_dai_ban.ds)."""
	if not si:
		return the_tv("cho", sdt)
	kh = (si.get("customer") or "").strip()
	return the_tv(trang_thai(kh, khach, _la_gop(kh)), sdt)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=600)
def gan(diem=None, ban=None, k=None):
	"""Khách đã đăng nhập Zalo gắn số của mình vào hoá đơn tạm tính của bàn."""
	from vagabond import goi_mon_ban, thanh_vien, uu_dai_ban

	d, n = goi_mon_ban._kiem_link(diem, ban, k)
	if not d:
		return {"ok": 0, "cau": CAU_LINK}
	so = thanh_vien._so_phien()
	if not so:
		return {"ok": 0, "dang_nhap": 0, "cau": CAU_DANG_NHAP}
	# Khoá hoá đơn TRƯỚC khi đọc khách đang đứng tên (loại 1): hai máy cùng bàn
	# bấm cùng lúc thì máy sau chờ, vào thấy khách của máy trước.
	si = uu_dai_ban._hoa_don_ban(d, n, khoa=True)
	if not si:
		return {"ok": 0, "cho": 1, "cau": CAU_CHO_HD}
	nd = thanh_vien._dn()._sdt_noi_dia(so)
	if ud_cua_so_khac(uu_dai_ban.doc_ud(si.get("vgb_ud_ban")), nd):
		return {"ok": 0, "tv": the_tv("khac", nd), "cau": CAU_KHAC}
	with uu_dai_ban._luu_bang_quyen_he_thong():
		khach, ly = thanh_vien._khach_hoac_tao(so)
	if not khach:
		return {"ok": 0, "cau": CAU_DOI_CHIEU if ly == "can_doi_chieu" else "Chưa tích điểm được. Quý khách báo nhân viên giúp."}
	cu = (si.get("customer") or "").strip()
	tt = trang_thai(cu, khach, _la_gop(cu))
	if tt == "khac":
		return {"ok": 0, "tv": the_tv("khac", nd), "cau": CAU_KHAC}
	if tt == "trong":
		si.customer = khach
		uu_dai_ban._luu_cho_khach(si)
		_vet(si, "Khách tự gắn số %s qua Zalo tại bàn %s để tích điểm." % (uu_dai_ban.che_sdt(nd), n))
		frappe.db.commit()
	return {"ok": 1, "tv": the_tv("gan", nd)}


def _vet(si, chu):
	try:
		si.add_comment("Comment", chu)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tich_diem_ban: ghi vết lỗi")


@frappe.whitelist(methods=["POST"])
def gan_quay(name=None, khach=None, sdt=None, ten=None):
	"""Thu ngân gắn (hay gỡ) khách thành viên cho bill Tạm tính.

	khach: mã khách chọn trong danh sách. Không có mã mà có sdt thì tìm khách
	theo số, chưa có thì tạo khách lẻ mới (cùng nhap_khach.khach_cho_don của đơn
	online). Cả hai rỗng là gỡ, bill về khách chung."""
	from vagabond import ban_hang, nhap_khach

	ban_hang._kiem_quyen_ban()
	si = frappe.get_doc(SI, name, for_update=True)
	if si.docstatus != 0 or cint(si.get("vgb_huy")) or not cint(si.get("vgb_tam_tinh")):
		frappe.throw("Chỉ gắn khách cho bill Tạm tính chưa chốt. Bill đã chốt thì giữ nguyên khách.")
	ma = (khach or "").strip()
	if not ma and (sdt or "").strip():
		if not nhap_khach.sdt_chuan(sdt):
			frappe.throw("Số điện thoại chưa đúng. Kiểm tra lại 10 số rồi bấm Gắn.")
		ma = nhap_khach.khach_cho_don(sdt, ten, "Quầy gắn bill tạm tính")
		if not ma:
			frappe.throw("Chưa tạo được khách cho số này. Thử lại, vẫn lỗi thì báo quản trị hệ thống.")
	if ma and not frappe.db.exists("Customer", ma):
		frappe.throw("Không có khách hàng %s trong danh mục." % ma)
	if ma and _la_gop(ma):
		frappe.throw("\"%s\" là khách chung của quầy, không tích điểm được. Chọn đúng khách thành viên." % ma)
	if ma:
		kiem_cung_chu(si, ma)
	cu = (si.get("customer") or "").strip()
	moi = ma or ban_hang._khach_le()
	if moi != cu:
		si.customer = moi
		si.flags.ignore_permissions = True
		si.save(ignore_permissions=True)
		_vet(si, ("Quầy gắn khách %s để tích điểm." % ma) if ma else "Quầy gỡ khách tích điểm, bill về khách chung.")
		frappe.db.commit()
	ten_kh = frappe.db.get_value("Customer", ma, "customer_name") if ma else ""
	return {"ok": 1, "khach": ma, "ten": ten_kh or ma}
