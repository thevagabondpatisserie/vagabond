# -*- coding: utf-8 -*-
"""Bánh thiết kế riêng đặt trên web, cọc 50% (v630).

Anh Việt chốt 02/11/2026 (bản 2 của đề xuất, sau góp ý Codex vòng 1):

  - Tác phẩm (Croquembouche...) do Marketing khai ở trình biên tập web, khối
    `thiet_ke_rieng` trong noi_dung_web: size, giá ĐÃ GỒM VAT, trang trí, số
    ngày đặt trước (không dưới 7).
  - Khách đặt trên trang Vue, cọc 50% (làm tròn LÊN tới nghìn) qua VietQR.
  - Đơn đi LUỒNG ĐẶT BÁNH CỦA APP (dat_banh.py): Sales Order một dòng
    BAEV00001 "Bánh thiết kế riêng", giá do MÁY CHỦ tính từ khối đã xuất
    bản, không nhận giá từ trình duyệt. KHÔNG qua Pancake (Codex: Pancake đòi
    đủ tiền và `ban_hang._soat_sepay` so cả hoá đơn, đơn trả hai lần bị chặn
    ghi sổ; tiền cọc cũng không được biến thành dòng giảm giá).
  - Phần còn lại thu khi khách nhận bánh. Hoá đơn VAT xuất NGÀY GIAO, cấn
    các khoản ứng trước của đúng phiếu đặt.

DÒNG TIỀN, TỪNG BƯỚC (đọc kỹ trước khi sửa)
===========================================
1. Khách gửi đơn: Sales Order đã ghi sổ (cam kết, giữ lịch bếp), CHƯA có
   bút toán nào. Mã chuyển khoản riêng `TKRyymmNNNN` nằm trên phiếu.
2. Tiền cọc về (SePay ghi Bank Transaction): `khop_mot` tìm dòng sao kê mang
   đúng mã, kiểm số tiền, CHIẾM dòng đó (ô `vgb_gd_tkr` trên phiếu thu, khai
   vào sổ đối soát chung `doi_soat_sepay` nên không luồng nào khác gạch lại
   được), rồi lập Payment Entry ứng trước TRỎ ĐÚNG phiếu đặt, ở dạng NHÁP.
   Nháp vì luật chị Dung 16/08: chứng từ qua ngân hàng phải có giấy báo Có
   đính kèm mới ghi sổ (`chung_tu_tien.chan_thieu_dinh_kem`), dòng SePay
   không thay được. Kế toán đính chứng từ rồi ghi sổ (màn Đơn đặt trước có
   nút cho kế toán, hoặc trên Desk).
3. Khách nhận bánh, trả phần còn lại:
     - tiền mặt: phiếu thu ứng trước thứ hai, quầy = quầy đang thu, ghi sổ
       ngay (tiền vào két, Chốt ca của quầy đó đếm đúng một lần qua
       `dat_banh.thu_ung_truoc`);
     - chuyển khoản qua QR (cùng mã đơn): đi đúng đường bước 2.
4. Giao bánh: Sales Invoice lập TỪ phiếu đặt (make_sales_invoice), phương
   thức "Trả trước" (nhóm tiền về ngày khác, `ca_quay._ngoai_ket` loại khỏi
   đối soát két), bảng advances CHỈ gồm các phiếu thu đã ghi sổ của đúng
   phiếu đặt này, tắt tự cấn (`allocate_advances_automatically = 0`) để lõi
   không vơ thêm khoản ứng trước khác của khách (tiền nạp số dư...). Tổng
   cấn phải bằng tổng hoá đơn, không thì chặn: không xuất hoá đơn còn nợ.

QUẦY CỦA PHIẾU THU (Codex finding 4)
=====================================
Hàng rào 1 của `dat_banh.loi_phieu_dat_banh` bắt có ô quầy. Quyết định:
  - Mọi khoản CHUYỂN KHOẢN của đơn này (cọc web, phần còn lại qua QR) mang
    quầy = điểm bán không có két (Sales Online, mã lấy từ cấu hình điểm bán,
    mặc định "SALES"), phương thức "Chuyển khoản". Tiền vào tài khoản, không
    vào két: trên bảng Chốt ca dòng không phải tiền mặt đặt đếm = máy nên
    không bao giờ lệch (`ca_quay.ghep_chi_tien_mat`), và quầy cửa hàng nhận
    bánh không bị cộng khoản nó không cầm.
  - Tiền mặt thu lúc nhận bánh mang quầy = quầy đang thu. Đó là tiền thật
    trong két quầy đó, đếm đúng một lần.
  - Hoá đơn ngày giao mang "Trả trước": không cộng vào két lần thứ hai.
Ca kiểm `thu_thiet_ke_rieng_630` chạy đúng `thu_ung_truoc`, `loc_trong_ket`
và `ghep_chi_tien_mat` để chứng minh.

KHÔNG ĐẾM HAI LẦN
=================
  - Một dòng sao kê chỉ được chiếm một lần cho toàn hệ: hỏi
    `doi_soat_sepay.chu_cua_giao_dich` (mọi luồng, hoá đơn bán, bộ sao kê)
    trước khi lập phiếu, trong khoá hàng của phiếu đặt.
  - Một phiếu đặt chỉ một hoá đơn: `custom_pancake_id = TKR-<mã>` vướng
    `ban_hang.chan_trung_ma_pancake` và khoá duy nhất dưới cơ sở dữ liệu.
  - Còn phải thu tính ở MÁY CHỦ từ tổng phiếu đặt trừ mọi phiếu thu chưa
    huỷ (kể cả nháp đã chiếm sao kê), không nhận số từ màn hình.
"""

# ------------------------------------------------------------ phần thuần
#
# Không chạm Frappe để bộ kiểm tầng khung chạy được ở CI tay không.

import hashlib
import json
import math
import re
from datetime import date, timedelta

MA_MON = "BAEV00001"
SO_NGAY_TOI_THIEU = 7
PT_CK = "Chuyển khoản"
PT_TM = "Tiền mặt"
PT_TRA_TRUOC = "Trả trước"
SO = "Sales Order"
PE = "Payment Entry"
SI = "Sales Invoice"
BT = "Bank Transaction"
LOAI = "thiet_ke_rieng"
TIEN_TO_MA = "TKR"
RE_MA = re.compile(r"TKR[0-9]{8}")
GHI_CHU_TOI_DA = 500
LECH = 1.0

# Ai mở màn Đơn đặt trước trên app. Bản JS (QUYEN_TKR trong 63-don-dat-truoc.js)
# phải trùng tuyệt đối, ca kiểm chốt.
QUYEN_TKR = ("Sales User", "Sales Manager", "System Manager", "VGB - Quản lý cửa hàng",
	"Accounts User", "Accounts Manager", "Giám đốc")

# Trạng thái màn Đơn đặt trước. (mã, nhãn). Thứ tự là thứ tự chip.
TRANG_THAI = (
	("cho_coc", "Chờ cọc"),
	("da_coc", "Đã cọc"),
	("du_tien", "Đã thu đủ"),
	("da_giao", "Đã giao"),
	("da_huy", "Đã huỷ"),
)


def so_tien(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def tron(x):
	"""Tiền Việt không có số lẻ."""
	return float(round(so_tien(x)))


def tien_coc(tong):
	"""Tiền cọc 50%, làm tròn LÊN tới nghìn đồng. THUẦN.

	Làm tròn lên chứ không làm tròn thường: anh Việt chốt cọc "ít nhất một
	nửa"; làm tròn xuống là nhận cọc dưới một nửa giá trị đơn.
	"""
	t = int(round(so_tien(tong)))
	if t <= 0:
		return 0
	return int(math.ceil(t / 2.0 / 1000.0)) * 1000


def vnd(x):
	return "{:,.0f}".format(tron(x)).replace(",", ".") + " đ"


def ngay_iso(x):
	"""Chuỗi YYYY-MM-DD hợp lệ thành date, sai thì None. THUẦN."""
	try:
		return date.fromisoformat(str(x or "")[:10]) if len(str(x or "")) >= 10 else None
	except ValueError:
		return None


def so_ngay_cua(tac_pham):
	"""Số ngày đặt trước của một tác phẩm, không bao giờ dưới 7. THUẦN."""
	try:
		n = int(str((tac_pham or {}).get("so_ngay") or SO_NGAY_TOI_THIEU))
	except ValueError:
		n = SO_NGAY_TOI_THIEU
	return max(SO_NGAY_TOI_THIEU, n)


def ngay_som_nhat(hom_nay, tac_pham):
	"""Ngày nhận sớm nhất còn nhận đặt (giờ Việt Nam). THUẦN."""
	hn = ngay_iso(hom_nay) if not isinstance(hom_nay, date) else hom_nay
	return hn + timedelta(days=so_ngay_cua(tac_pham))


def chuan_sdt(s):
	"""Số di động Việt Nam về dạng 0xxxxxxxxx, sai thì rỗng.

	MỘT nguồn với `lib.sdt` (bench #531): bản cũ nhận mọi số 0[35789]xxxxxxxx,
	nên số đầu 095, 080... qua được form mà lúc lập phiếu `khach_cho_don`
	(đọc theo lib.sdt) không tạo được khách, đơn báo lỗi khi khách đã gửi."""
	from vagabond.lib import sdt

	return sdt(s)


def tac_pham_hien(nd, id_tac_pham):
	"""Khối tác phẩm đang hiện trên web theo mã. THUẦN."""
	for k in (nd or {}).get("khoi") or []:
		if k.get("loai") == LOAI and k.get("id") == id_tac_pham and k.get("hien"):
			return k
	return None


def tinh_gia(tac_pham, ten_kich_co, ds_trang_tri):
	"""Giá máy chủ của một lựa chọn. THUẦN. Lỗi thì ValueError câu tiếng Việt.

	Giá size và giá cộng thêm của trang trí ĐÃ GỒM VAT (anh Việt chốt
	02/11/2026), đọc từ khối đã xuất bản, không bao giờ từ trình duyệt.
	Trang trí cùng nhóm (ví dụ nhóm Hoa) chỉ chọn một.
	"""
	kc = next((x for x in (tac_pham or {}).get("kich_co") or [] if x.get("ten") == ten_kich_co), None)
	if not kc:
		raise ValueError("Chọn một size của tác phẩm.")
	co = {x.get("ten"): x for x in (tac_pham or {}).get("trang_tri") or []}
	chon = []
	for t in ds_trang_tri or []:
		t = str(t or "")
		if t not in co:
			raise ValueError("Trang trí \"%s\" không còn trong danh sách. Tải lại trang." % t[:60])
		if t not in chon:
			chon.append(t)
	nhom = {}
	for t in chon:
		n = str(co[t].get("nhom") or "")
		if n:
			if n in nhom:
				raise ValueError("Nhóm %s chỉ chọn một: %s hoặc %s." % (n, nhom[n], t))
			nhom[n] = t
	gia_kc = int(kc.get("gia") or 0)
	gia_tt = sum(int(co[t].get("gia_them") or 0) for t in chon)
	tong = gia_kc + gia_tt
	if gia_kc <= 0 or tong <= 0:
		raise ValueError("Tác phẩm này chưa có giá. Nhờ Sales tư vấn trước.")
	coc = tien_coc(tong)
	return {"kich_co": kc.get("ten"), "mo_ta_kich_co": kc.get("mo_ta") or "", "gia_kich_co": gia_kc,
		"trang_tri": chon, "gia_trang_tri": gia_tt, "tong": tong, "coc": coc, "con_lai": tong - coc}


RE_GIO = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]")


def chuan_don(du_lieu, tac_pham, hom_nay, diem_nhan):
	"""Kiểm một đơn khách gửi. THUẦN. Trả bản sạch, lỗi thì ValueError.

	`diem_nhan` là danh sách điểm nhận đang bật trên web ({id, n, a}).
	"""
	if not isinstance(du_lieu, dict):
		raise ValueError("Kiểm tra lại thông tin đặt bánh.")
	if not tac_pham:
		raise ValueError("Tác phẩm này không còn nhận đặt trên web. Tải lại trang để xem tác phẩm đang mở.")
	gia = tinh_gia(tac_pham, str(du_lieu.get("kich_co") or ""), du_lieu.get("trang_tri") or [])
	ngay = ngay_iso(du_lieu.get("ngay"))
	som = ngay_som_nhat(hom_nay, tac_pham)
	if not ngay:
		raise ValueError("Chọn ngày cần bánh.")
	if ngay < som:
		raise ValueError("Tác phẩm này cần đặt trước ít nhất %d ngày. Ngày sớm nhất còn nhận là %s."
			% (so_ngay_cua(tac_pham), som.strftime("%d/%m/%Y")))
	if ngay > som + timedelta(days=365):
		raise ValueError("Chỉ nhận đặt trong vòng một năm tới.")
	gio = str(du_lieu.get("gio") or "").strip()
	if gio and not RE_GIO.fullmatch(gio):
		raise ValueError("Giờ cần bánh gõ dạng 17:00.")
	ten = re.sub(r"\s+", " ", str(du_lieu.get("ten") or "")).strip()
	sdt = chuan_sdt(du_lieu.get("sdt"))
	if not ten or len(ten) > 120 or not sdt:
		raise ValueError("Điền họ tên và số điện thoại di động Việt Nam hợp lệ.")
	ghi_chu = str(du_lieu.get("ghi_chu") or "").strip()
	if len(ghi_chu) > GHI_CHU_TOI_DA:
		raise ValueError("Ghi chú cho bếp tối đa %d ký tự." % GHI_CHU_TOI_DA)
	diem = next((d for d in diem_nhan or [] if d.get("id") and d.get("id") == du_lieu.get("diem_nhan")), None)
	if not diem:
		raise ValueError("Chọn nơi nhận bánh.")
	return dict(gia, tac_pham_id=tac_pham.get("id"), tac_pham=tac_pham.get("tieu_de") or "",
		ngay=ngay.isoformat(), gio=gio, ten=ten, sdt=sdt, ghi_chu=ghi_chu,
		diem_nhan=diem.get("id"), ten_diem_nhan=diem.get("n") or "", dia_chi_nhan=diem.get("a") or "")


def bang_ke(don):
	"""Bảng kê đi theo phiếu đặt và hoá đơn: tác phẩm, size, trang trí, ngày tiệc. THUẦN."""
	d = don or {}
	ngay = ngay_iso(d.get("ngay"))
	dong = [
		"Bánh thiết kế riêng: %s" % d.get("tac_pham", ""),
		"Size: %s%s" % (d.get("kich_co", ""), (" (%s)" % d["mo_ta_kich_co"]) if d.get("mo_ta_kich_co") else ""),
		"Trang trí: %s" % (", ".join(d.get("trang_tri") or []) or "Không chọn thêm"),
		"Ngày tiệc: %s%s" % (ngay.strftime("%d/%m/%Y") if ngay else "", (" lúc " + d["gio"]) if d.get("gio") else ""),
		"Nhận tại: %s" % (d.get("ten_diem_nhan") or ""),
	]
	if d.get("ghi_chu"):
		dong.append("Ghi chú cho bếp: %s" % d["ghi_chu"])
	return dong


def bam(du_lieu):
	"""Dấu nội dung một lần gửi để nhận ra gửi lại cùng nội dung. THUẦN."""
	return hashlib.sha256(json.dumps(du_lieu, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def ma_tiep_theo(ma_cuoi, hom_nay):
	"""Mã đơn kế tiếp theo tháng: TKR + yymm + 4 số. THUẦN."""
	hn = ngay_iso(hom_nay) if not isinstance(hom_nay, date) else hom_nay
	dau = "%s%02d%02d" % (TIEN_TO_MA, hn.year % 100, hn.month)
	so = 0
	if ma_cuoi and str(ma_cuoi).startswith(dau) and str(ma_cuoi)[len(dau):].isdigit():
		so = int(str(ma_cuoi)[len(dau):])
	return "%s%04d" % (dau, so + 1)


def con_phai_thu(tong, ds_phieu):
	"""Còn phải thu bao nhiêu (phần dùng chung ung_truoc_don.con_phai_thu). THUẦN."""
	from vagabond.ung_truoc_don import con_phai_thu as _cpt

	return _cpt(tong, ds_phieu)


def trang_thai(tong, ds_phieu, co_hoa_don, da_huy):
	"""Trạng thái đơn trên màn app. THUẦN. Trả (mã, nhãn)."""
	nhan = dict(TRANG_THAI)
	if da_huy:
		return ("da_huy", nhan["da_huy"])
	if co_hoa_don:
		return ("da_giao", nhan["da_giao"])
	da = [p for p in ds_phieu or [] if int(p.get("docstatus") or 0) < 2 and so_tien(p.get("so_tien")) > 0]
	if not da:
		return ("cho_coc", nhan["cho_coc"])
	if con_phai_thu(tong, ds_phieu) <= 0:
		return ("du_tien", nhan["du_tien"])
	return ("da_coc", nhan["da_coc"])


# v630 Bánh sỉ: bộ máy nhận tiền chuyển khoản cho phiếu đặt (chọn dòng sao kê,
# phiếu thu ứng trước, cấn ngày giao) chuyển sang ung_truoc_don.py để bánh sỉ
# trả trước dùng CHUNG một bản. Các tên dưới đây giữ nguyên chữ ký cũ.


def xet_giao_dich(tien_gd, coc, tong, da_nhan):
	"""Một dòng sao kê mang đúng mã có được lập phiếu thu không. THUẦN."""
	from vagabond.ung_truoc_don import xet_giao_dich as _x

	return _x(tien_gd, coc, tong, da_nhan, "tiền cọc")


def chon_giao_dich(ds_gd, ma, chu, coc, tong, da_nhan):
	"""Chọn dòng sao kê được lập phiếu thu cho đơn TKR mang mã `ma`. THUẦN."""
	from vagabond.ung_truoc_don import chon_giao_dich as _c

	return _c(ds_gd, ma, RE_MA, chu, coc, tong, da_nhan, "tiền cọc")


def quay_chuyen_khoan(ds_diem):
	"""Mã điểm bán không có két (Sales Online) cho mọi khoản chuyển khoản. THUẦN."""
	from vagabond.ung_truoc_don import quay_chuyen_khoan as _q

	return _q(ds_diem)


def nguon_cua_diem(diem):
	"""Nguồn đơn ghi trên hoá đơn ngày giao ở một quầy: ưu tiên "Mang về". THUẦN."""
	d = diem or {}
	return d.get("mang_ve") or next((n for n in d.get("nguon") or [] if n), "") or "Mang về"


def phieu_thu(don_dat, khach, tong, so, quay, pt, ngay, gd=None, ghi_chu=""):
	"""Các ô của MỘT phiếu thu ứng trước cho phiếu đặt TKR. THUẦN."""
	from vagabond.ung_truoc_don import phieu_thu as _p

	return _p(don_dat, khach, tong, so, quay, pt, ngay, gd, ghi_chu, TIEN_TO_MA)


def loi_phieu(p):
	"""Bốn hàng rào của dat_banh cho một phiếu dựng bởi `phieu_thu`. THUẦN."""
	from vagabond.ung_truoc_don import loi_phieu as _l

	return _l(p)


def chon_ung_truoc(ds_ung, phieu_hop_le, tong):
	"""Dòng advances của hoá đơn ngày giao, chỉ phiếu đã ghi sổ của đơn. THUẦN."""
	from vagabond.ung_truoc_don import chon_ung_truoc as _u

	return _u(ds_ung, phieu_hop_le, tong)


def tin_don(don, ma, loai):
	"""Tin Zalo cho Sales và bếp. KHÔNG ghi số tiền (nhóm Bán hàng, Bếp không nhận tiền). THUẦN."""
	ngay = ngay_iso(don.get("ngay"))
	dau = {"moi": "ĐƠN THIẾT KẾ RIÊNG MỚI, CHỜ CỌC", "coc": "ĐƠN THIẾT KẾ RIÊNG ĐÃ NHẬN CỌC",
		"tu_van": "KHÁCH NHỜ TƯ VẤN THIẾT KẾ RIÊNG"}[loai]
	dong = [dau]
	if ma:
		dong.append("Mã đơn: %s" % ma)
	dong.append("Tác phẩm: %s%s" % (don.get("tac_pham", ""), (", size " + don["kich_co"]) if don.get("kich_co") else ""))
	if don.get("trang_tri"):
		dong.append("Trang trí: %s" % ", ".join(don["trang_tri"]))
	if ngay:
		dong.append("Ngày cần bánh: %s%s" % (ngay.strftime("%d/%m/%Y"), (" lúc " + don["gio"]) if don.get("gio") else ""))
	if don.get("ten_diem_nhan"):
		dong.append("Nhận tại: %s" % don["ten_diem_nhan"])
	dong.append("Khách: %s, SĐT: %s" % (don.get("ten", ""), don.get("sdt", "")))
	if don.get("ghi_chu"):
		dong.append("Ghi chú: %s" % re.sub(r"\s+", " ", don["ghi_chu"]))
	return "\n".join(dong)


# ------------------------------------------------------------- chạm Frappe

import frappe  # noqa: E402
from frappe.rate_limiter import rate_limit  # noqa: E402
from frappe.utils import flt, nowdate  # noqa: E402

TRUONG_MOI = {
	SO: [
		{"fieldname": "vgb_tkr_ma", "label": "Mã đơn thiết kế riêng", "fieldtype": "Data", "insert_after": "delivery_date",
			"read_only": 1, "no_copy": 1, "in_standard_filter": 1,
			"description": "Mã khách ghi khi chuyển khoản cọc. Máy điền khi khách đặt trên web."},
		{"fieldname": "vgb_tkr_coc", "label": "Tiền cọc", "fieldtype": "Currency", "insert_after": "vgb_tkr_ma",
			"read_only": 1, "no_copy": 1, "description": "50% tổng đơn, làm tròn lên tới nghìn đồng."},
		{"fieldname": "vgb_tkr_bang_ke", "label": "Bảng kê thiết kế riêng", "fieldtype": "Small Text",
			"insert_after": "vgb_tkr_coc", "read_only": 1, "no_copy": 1},
		{"fieldname": "vgb_tkr_du_lieu", "label": "Dữ liệu đơn thiết kế riêng", "fieldtype": "Long Text",
			"insert_after": "vgb_tkr_bang_ke", "read_only": 1, "hidden": 1, "no_copy": 1},
		{"fieldname": "vgb_tkr_khoa", "label": "Khoá xem trạng thái", "fieldtype": "Data",
			"insert_after": "vgb_tkr_du_lieu", "read_only": 1, "hidden": 1, "no_copy": 1},
		# Ràng buộc DUY NHẤT (Codex #531 f2): hai lần gửi cùng mã lần gửi mà lọt
		# qua khoá thì cơ sở dữ liệu chỉ nhận một phiếu đặt. Frappe đổi chuỗi rỗng
		# của ô unique thành NULL, nên các phiếu đặt khác không đụng nhau.
		{"fieldname": "vgb_tkr_lan", "label": "Mã lần gửi", "fieldtype": "Data",
			"insert_after": "vgb_tkr_khoa", "read_only": 1, "hidden": 1, "no_copy": 1, "unique": 1},
	],
	PE: [
		{"fieldname": "vgb_gd_tkr", "label": "Dòng sao kê đã gạch (đơn đặt trước)", "fieldtype": "Data",
			"insert_after": "vgb_phieu_dat", "read_only": 1, "no_copy": 1, "search_index": 1,
			"description": "Dòng sao kê SePay mà máy đã chiếm cho phiếu thu này. Một dòng chỉ gạch một lần."},
	],
}


def _khai_doi_soat():
	"""Khai luồng vào sổ đối soát SePay chung để `chu_cua_giao_dich` thấy dòng
	sao kê phiếu thu thiết kế riêng đã chiếm. Ba cửa chung (tu_dong, ung_vien,
	khop_tay) KHÔNG dùng cho luồng này: khớp chạy ở `khop_mot` trong khoá hàng
	phiếu đặt, nên quyền của ba cửa đó luôn chặn."""
	from vagabond import doi_soat_sepay as dss

	def _chan():
		frappe.throw("Tiền của đơn thiết kế riêng và đơn bánh sỉ trả trước khớp ở màn Đơn đặt trước, "
			"Đơn sỉ web, không khớp ở đây.")

	# v630 Bánh sỉ: phiếu thu đơn sỉ trả trước dùng CHUNG ô `vgb_gd_tkr` và luồng
	# khai này (ung_truoc_don.khop), nên một dòng sao kê đã gạch cho đơn sỉ cũng
	# hiện là "có chủ" với mọi luồng khác, không cần khai luồng thứ hai.
	dss.khai(
		loai=LOAI, doctype=PE, chieu=dss.VAO,
		ma_do=lambda doc: "", so_tien=lambda doc: flt(doc.get("paid_amount")),
		dang_cho={"name": "__khong_co__"}, ten_man="phiếu thu đơn đặt trước (thiết kế riêng, bánh sỉ)",
		truong_gd="vgb_gd_tkr", loc_chiem={"docstatus": ["<", 2]},
		quyen_doc=_chan, quyen_ghi=_chan,
	)


_khai_doi_soat()


def _cong_ty():
	return frappe.db.get_single_value("Global Defaults", "default_company")


def _hom_nay():
	return str(nowdate())


def _kiem_quyen():
	if not set(QUYEN_TKR) & set(frappe.get_roles()):
		frappe.throw("Màn Đơn đặt trước mở cho Sales, quản lý cửa hàng, kế toán và giám đốc.")


def _ban():
	from vagabond.noi_dung_web import _ban_cong_khai

	return _ban_cong_khai()


def _diem_nhan(ban):
	from vagabond.noi_dung_web import diem_nhan

	return diem_nhan(ban)


def _ds_diem():
	from vagabond import diem_ban

	return diem_ban.ds(chi_bat=True)


def _nuot_loi_tin(e, ten):
	"""Lỗi báo Zalo không làm mất đơn hay phiếu thu, trừ lỗi làm chết giao dịch."""
	from vagabond.loi_csdl import chet_giao_dich

	if chet_giao_dich(e):
		raise e
	frappe.log_error(frappe.get_traceback(), "thiet_ke_rieng: tin Zalo %s" % ten)


def _bao_moi(don, so):
	"""Đơn mới chờ cọc: nhóm Bán hàng gọi xác nhận với khách."""
	if getattr(frappe.flags, "vagabond_kiem_that", False):
		return
	try:
		from vagabond import kenh_zalo

		tieu_de, dong = kenh_zalo.tach_tin(tin_don(don, so.vgb_tkr_ma, "moi"))
		kenh_zalo.bao_hoac_ghi_loi("viec", "don_web", tieu_de, dong, khoa="tkr_moi:%s" % so.name, nguon=so.name,
			ma_tin="bh_tkr_moi")
	except Exception as e:
		_nuot_loi_tin(e, "bh_tkr_moi")


def _bao_sales_coc(don, ma, so_name):
	if getattr(frappe.flags, "vagabond_kiem_that", False):
		return
	try:
		from vagabond import kenh_zalo

		tieu_de, dong = kenh_zalo.tach_tin(tin_don(don, ma, "coc"))
		kenh_zalo.bao_hoac_ghi_loi("viec", "don_web", tieu_de, dong, khoa="tkr_coc:%s" % so_name, nguon=so_name,
			ma_tin="bh_tkr_da_coc")
	except Exception as e:
		_nuot_loi_tin(e, "bh_tkr_da_coc")


def _bao_bep_coc(don, ma, so_name):
	if getattr(frappe.flags, "vagabond_kiem_that", False):
		return
	try:
		from vagabond import kenh_zalo

		tieu_de, dong = kenh_zalo.tach_tin(tin_don(don, ma, "coc"))
		kenh_zalo.bao_hoac_ghi_loi("thong_bao", "san_xuat", tieu_de, dong, khoa="tkr_bep:%s" % so_name, nguon=so_name,
			ma_tin="bep_tkr_da_coc")
	except Exception as e:
		_nuot_loi_tin(e, "bep_tkr_da_coc")


def _bao_tu_van(don, sdt):
	if getattr(frappe.flags, "vagabond_kiem_that", False):
		return
	try:
		from vagabond import kenh_zalo

		tieu_de, dong = kenh_zalo.tach_tin(tin_don(don, "", "tu_van"))
		kenh_zalo.bao_hoac_ghi_loi("viec", "don_web", tieu_de, dong, khoa="tkr_tv:%s:%s" % (sdt, _hom_nay()), nguon=sdt,
			ma_tin="bh_tkr_tu_van")
	except Exception as e:
		_nuot_loi_tin(e, "bh_tkr_tu_van")


# ------------------------------------------------------------------ khách web


def _anh_tam(ma_anh):
	"""Mã tạm ảnh tham khảo -> tên File riêng tư chưa gắn đơn nào."""
	if not ma_anh:
		return None
	if not re.fullmatch(r"[a-z0-9]{24}", str(ma_anh)):
		frappe.throw("Ảnh tham khảo không hợp lệ. Chọn lại ảnh rồi gửi.")
	ten = frappe.cache().get_value(KHOA_ANH + ma_anh)
	if not ten or not frappe.db.exists("File", ten):
		frappe.throw("Ảnh tham khảo đã hết hạn chờ. Chọn lại ảnh rồi gửi.")
	return ten


KHOA_ANH = "vgb_tkr_anh:"
ANH_TOI_DA = 8 * 1024 * 1024


@frappe.whitelist(methods=["POST"], allow_guest=True)
@rate_limit(limit=10, seconds=600)
def tai_anh_mau():
	"""Khách gửi ảnh tham khảo (không bắt buộc). Lưu RIÊNG TƯ, chỉ nhận ảnh thật
	JPG, PNG, WebP dưới 8 MB, tên do máy chủ đặt. Trả mã tạm để gắn vào đơn."""
	from io import BytesIO
	from PIL import Image
	from frappe.utils.file_manager import save_file

	tep = frappe.request.files.get("tep") if getattr(frappe, "request", None) else None
	if not tep:
		frappe.throw("Chọn một ảnh JPG, PNG hoặc WebP.")
	du_lieu = tep.stream.read(ANH_TOI_DA + 1)
	if len(du_lieu) > ANH_TOI_DA:
		frappe.throw("Ảnh lớn hơn 8 MB. Chọn ảnh nhỏ hơn.")
	try:
		with Image.open(BytesIO(du_lieu)) as a:
			duoi = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}.get(a.format)
			if not duoi or a.width * a.height > 40000000:
				raise ValueError("ảnh không hợp lệ")
			a.verify()
	except Exception:
		frappe.throw("Không đọc được ảnh. Chọn ảnh JPG, PNG hoặc WebP.")
	f = save_file("tkr-" + frappe.generate_hash(length=16) + "." + duoi, du_lieu, None, None, is_private=1)
	ma = frappe.generate_hash(length=24)
	frappe.cache().set_value(KHOA_ANH + ma, f.name, expires_in_sec=6 * 3600)
	return {"ok": 1, "ma_anh": ma}


def _ma_moi():
	dau = ma_tiep_theo("", _hom_nay())[:-4]
	cuoi = frappe.db.sql(
		"select vgb_tkr_ma from `tabSales Order` where vgb_tkr_ma like %s order by vgb_tkr_ma desc limit 1 for update",
		(dau + "%",))
	ma = ma_tiep_theo(cuoi[0][0] if cuoi else "", _hom_nay())
	for _ in range(50):
		if not frappe.db.exists(SO, {"vgb_tkr_ma": ma}):
			return ma
		ma = ma_tiep_theo(ma, _hom_nay())
	frappe.throw("Chưa sinh được mã đơn. Bấm gửi lại.")


def _da_gui(lan, dau, khoa=False):
	"""Đơn cùng mã lần gửi đã có thì trả đơn đó. khoa=True là đọc HIỆN TẠI
	(for update), dùng sau khi chờ khoá: đọc thường lúc đó trả ảnh chụp
	REPEATABLE READ từ lần tra đầu, không thấy đơn lần gửi trước vừa lập
	(Codex #531 f2, cùng nếp tiec_web._da_nhan)."""
	r = frappe.db.get_value(SO, {"vgb_tkr_lan": lan}, ["name", "vgb_tkr_ma", "vgb_tkr_khoa", "vgb_tkr_du_lieu"],
		as_dict=True, for_update=khoa)
	if not r:
		return None
	du = json.loads(r.vgb_tkr_du_lieu or "{}")
	if du.get("bam") != dau:
		frappe.throw("Đơn này đã được gửi. Tải lại trang để đặt đơn mới.")
	return _ket_qua(r.name, khoa=khoa)


def _qr(ma, so):
	from vagabond import qr_chuyen_khoan, tai_khoan

	tk = tai_khoan.tk_cho("Thiết kế riêng", quay_chuyen_khoan(_ds_diem()))
	return {"ngan_hang": tk.get("bank") or "", "stk": tk.get("stk") or "", "ten_tk": tk.get("ten") or "",
		"so_tien": tron(so), "noi_dung": ma, "anh": qr_chuyen_khoan.anh_qr(tk, so, ma)}


def _ket_qua(so_name, khoa=False):
	"""Phản hồi của lần đặt. khoa=True khi phiếu đặt vừa được tìm thấy bằng phép
	đọc hiện tại (lần gửi lại chờ khoá): đọc lại bằng phép thường thì ảnh chụp
	REPEATABLE READ không thấy phiếu lần trước vừa commit, trả None và nổ thay
	vì trả mã đơn và QR (Codex #531 vòng 3)."""
	so = frappe.db.get_value(SO, so_name, ["name", "vgb_tkr_ma", "vgb_tkr_khoa", "vgb_tkr_coc", "grand_total",
		"rounded_total", "delivery_date"], as_dict=True, for_update=khoa)
	tong = flt(so.rounded_total) or flt(so.grand_total)
	return {"ok": 1, "ma": so.vgb_tkr_ma, "khoa": so.vgb_tkr_khoa, "tong": tron(tong), "coc": tron(so.vgb_tkr_coc),
		"con_lai": tron(tong) - tron(so.vgb_tkr_coc), "ngay": str(so.delivery_date), "qr": _qr(so.vgb_tkr_ma, so.vgb_tkr_coc)}


@frappe.whitelist(methods=["POST"], allow_guest=True)
@rate_limit(limit=5, seconds=600)
def dat(du_lieu, ma_lan_gui):
	"""Khách gửi đơn thiết kế riêng. Gửi lại cùng mã lần gửi thì trả đơn cũ."""
	if not isinstance(ma_lan_gui, str) or not re.fullmatch(r"[a-f0-9-]{36}", ma_lan_gui):
		frappe.throw("Tải lại trang để bắt đầu đặt bánh.")
	try:
		raw = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
		if not isinstance(raw, dict) or len(json.dumps(raw, ensure_ascii=False)) > 4000:
			raise ValueError("Thông tin đặt bánh quá dài hoặc không hợp lệ.")
	except (TypeError, ValueError) as e:
		frappe.throw(str(e))
	dau = bam(raw)
	lan = hashlib.sha256(("tkr:" + ma_lan_gui).encode()).hexdigest()[:40]
	cu = _da_gui(lan, dau)
	if cu:
		return cu
	# Đọc khối đã xuất bản CÓ KHOÁ: giá là bản Marketing vừa lưu, không phải
	# ảnh chụp lúc khách mở trang (Codex #454, cùng nếp tiec_web.dang_ky).
	from vagabond.noi_dung_web import _ban_cong_khai

	ban = _ban_cong_khai(khoa=True)
	cu = _da_gui(lan, dau, khoa=True)
	if cu:
		return cu
	try:
		don = chuan_don(raw, tac_pham_hien(ban, str(raw.get("tac_pham") or "")), _hom_nay(), _diem_nhan(ban))
	except (TypeError, ValueError) as e:
		frappe.throw(str(e))
	ten_anh = _anh_tam(raw.get("ma_anh"))
	don["bam"] = dau
	# Phòng hờ khi khoá không xếp hàng được (chưa có hàng nội dung web): ô mã
	# lần gửi là DUY NHẤT, lần sau đâm ràng buộc thì lùi điểm lưu và trả đơn
	# lần trước, như tiec_web.dang_ky.
	moc = "tkr_dat_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(moc)
	so_tin = len(getattr(frappe.local, "message_log", None) or [])
	try:
		so = _lap_phieu_dat(don, lan)
	except frappe.UniqueValidationError:
		frappe.db.rollback(save_point=moc)
		cu = _da_gui(lan, dau, khoa=True)
		if not cu:
			raise
		# db_insert đã thêm thông báo "phải là duy nhất" trước khi ném lỗi.
		if getattr(frappe.local, "message_log", None):
			del frappe.local.message_log[so_tin:]
		return cu
	if ten_anh:
		frappe.db.set_value("File", ten_anh, {"attached_to_doctype": SO, "attached_to_name": so.name},
			update_modified=False)
	_bao_moi(don, so)
	return _ket_qua(so.name)


def _kho_cua_mon(cty):
	if not frappe.db.get_value("Item", MA_MON, "is_stock_item"):
		return None
	return (frappe.db.get_value("Item Default", {"parent": MA_MON, "company": cty}, "default_warehouse")
		or frappe.db.get_single_value("Stock Settings", "default_warehouse"))


def _lap_phieu_dat(don, lan):
	"""Sales Order đã ghi sổ, một dòng BAEV00001, giá máy chủ (gồm VAT)."""
	from vagabond.nhap_khach import khach_cho_don
	from vagabond.thu_tien import nang_quyen_lap_phieu

	if not frappe.db.exists("Item", MA_MON):
		frappe.log_error("Thiếu mã món %s" % MA_MON, "thiet_ke_rieng: thiếu mã món")
		frappe.throw("Chưa nhận đặt được lúc này. Quý khách gọi cho chúng tôi để đặt.")
	cty = _cong_ty()
	with nang_quyen_lap_phieu():
		khach = khach_cho_don(don["sdt"], don["ten"], "Web thiết kế riêng")
		if not khach:
			frappe.throw("Chưa ghi nhận được thông tin khách. Kiểm tra số điện thoại rồi gửi lại.")
		so = frappe.new_doc(SO)
		so.company = cty
		so.customer = khach
		so.order_type = "Sales"
		so.transaction_date = _hom_nay()
		so.delivery_date = don["ngay"]
		so.currency = "VND"
		so.conversion_rate = 1
		so.ignore_pricing_rule = 1
		so.vgb_tkr_ma = _ma_moi()
		so.vgb_tkr_coc = don["coc"]
		so.vgb_tkr_bang_ke = "\n".join(bang_ke(don))
		so.vgb_tkr_du_lieu = json.dumps(don, ensure_ascii=False)
		so.vgb_tkr_khoa = frappe.generate_hash(length=24)
		so.vgb_tkr_lan = lan
		dong = {"item_code": MA_MON, "qty": 1, "rate": don["tong"], "price_list_rate": don["tong"],
			"delivery_date": don["ngay"], "description": "<br>".join(frappe.utils.escape_html(x) for x in bang_ke(don))}
		kho = _kho_cua_mon(cty)
		if kho:
			dong["warehouse"] = kho
		so.append("items", dong)
		# Giá web ĐÃ GỒM VAT: nạp cùng mẫu thuế "đã gồm trong giá" mà hoá đơn
		# bán của app dùng (hoa_don_thue_vnd.nap_mau_thue), để tổng phiếu đặt
		# đúng bằng giá và hoá đơn lập từ phiếu đặt mang đúng mẫu đó.
		from vagabond.hoa_don_thue_vnd import nap_mau_thue

		nap_mau_thue(so)
		so.flags.ignore_permissions = True
		so.insert(ignore_permissions=True)
		tong = flt(so.rounded_total) or flt(so.grand_total)
		if abs(tong - don["tong"]) > LECH:
			frappe.log_error("Phiếu đặt %s tổng %s khác giá %s" % (so.name, tong, don["tong"]),
				"thiet_ke_rieng: tổng phiếu đặt lệch giá")
			frappe.throw("Chưa nhận đặt được lúc này. Quý khách gọi cho chúng tôi để đặt.")
		so.submit()
	return so


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=60, seconds=600)
def trang_thai_don(ma, khoa):
	"""Trang khách hỏi đơn đã nhận cọc chưa. Cần khoá riêng của đơn (trả lúc đặt),
	đoán mã đơn không đọc được gì. Hỏi xong máy thử khớp sao kê của đúng đơn đó."""
	if not (isinstance(ma, str) and RE_MA.fullmatch(ma) and isinstance(khoa, str) and re.fullmatch(r"[a-z0-9]{24}", khoa)):
		frappe.throw("Không tìm thấy đơn.")
	ten = frappe.db.get_value(SO, {"vgb_tkr_ma": ma, "vgb_tkr_khoa": khoa, "docstatus": 1}, "name")
	if not ten:
		frappe.throw("Không tìm thấy đơn.")
	try:
		khop_mot(ten)
	except Exception as e:
		from vagabond.loi_csdl import chet_giao_dich

		if chet_giao_dich(e):
			raise
		frappe.log_error(frappe.get_traceback(), "thiet_ke_rieng: khớp khi khách hỏi")
	tt = tom_tat(ten)
	return {"trang_thai": tt["trang_thai"], "nhan": tt["nhan"]}


@frappe.whitelist(methods=["POST"], allow_guest=True)
@rate_limit(limit=5, seconds=600)
def nho_tu_van(du_lieu):
	"""Nút "Nhờ Sales tư vấn trước": báo nhóm Zalo Sales, không tạo đơn."""
	try:
		raw = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
	except ValueError:
		raw = None
	if not isinstance(raw, dict):
		frappe.throw("Kiểm tra lại thông tin.")
	ten = re.sub(r"\s+", " ", str(raw.get("ten") or "")).strip()[:120]
	sdt = chuan_sdt(raw.get("sdt"))
	if not ten or not sdt:
		frappe.throw("Điền họ tên và số điện thoại di động Việt Nam hợp lệ.")
	tp = tac_pham_hien(_ban(), str(raw.get("tac_pham") or ""))
	don = {"tac_pham": (tp or {}).get("tieu_de") or "Chưa chọn", "ten": ten, "sdt": sdt,
		"ghi_chu": str(raw.get("ghi_chu") or "").strip()[:GHI_CHU_TOI_DA]}
	_bao_tu_van(don, sdt)
	return {"ok": 1}


# ------------------------------------------------------------ khớp tiền về


def _phieu_cua(so_name):
	from vagabond.ung_truoc_don import phieu_cua

	return phieu_cua(so_name)


def _ds_phieu(so_name):
	from vagabond.ung_truoc_don import ds_phieu

	return ds_phieu(so_name)


def _gd_mang_ma(ma):
	from vagabond.ung_truoc_don import gd_mang_ma

	return gd_mang_ma(ma)


def khop_mot(so_name):
	"""Tìm tiền về cho MỘT phiếu đặt thiết kế riêng, chiếm dòng sao kê và lập
	phiếu thu nháp. Bộ máy chung ở ung_truoc_don.khop (dùng cả cho bánh sỉ);
	ở đây chỉ khai mã TKR, mức cọc và tin báo. Trả số phiếu đã lập."""
	from vagabond import ung_truoc_don as utd

	def _bao_dau(ten, ma):
		don = json.loads(frappe.db.get_value(SO, ten, "vgb_tkr_du_lieu") or "{}")
		_bao_sales_coc(don, ma, ten)
		_bao_bep_coc(don, ma, ten)

	return utd.khop(so_name, "vgb_tkr_ma", RE_MA, lambda so, tong: so.vgb_tkr_coc,
		lambda: quay_chuyen_khoan(_ds_diem()), _cong_ty,
		lambda ma, g: "Tiền chuyển khoản đơn thiết kế riêng %s, dòng sao kê %s." % (ma, g.get("name")),
		_bao_dau, "tiền cọc", TIEN_TO_MA, "thiet_ke_rieng")


def quet():
	"""Nhịp 5 phút: khớp tiền về cho mọi phiếu đặt thiết kế riêng còn phải thu."""
	ds = frappe.get_all(SO, filters={"vgb_tkr_ma": ["is", "set"], "docstatus": 1,
		"status": ["not in", ["Closed", "Cancelled", "Completed"]], "per_billed": ["<", 100]},
		pluck="name", limit_page_length=500)
	for ten in ds:
		try:
			khop_mot(ten)
			frappe.db.commit()
		except Exception as e:
			frappe.db.rollback()
			from vagabond.loi_csdl import chet_giao_dich

			if chet_giao_dich(e):
				continue
			frappe.log_error(frappe.get_traceback(), "thiet_ke_rieng: quét %s" % ten)


# ------------------------------------------------------------ màn app


def _hoa_don_cua(so):
	return frappe.db.get_value(SI, {"custom_pancake_id": "TKR-" + str(so.get("vgb_tkr_ma") or ""),
		"docstatus": ["<", 2]}, ["name", "docstatus"], as_dict=True)


def tom_tat(so_name):
	so = frappe.db.get_value(SO, so_name, ["name", "docstatus", "status", "customer", "customer_name",
		"delivery_date", "transaction_date", "grand_total", "rounded_total", "vgb_tkr_ma", "vgb_tkr_coc",
		"vgb_tkr_bang_ke", "vgb_tkr_du_lieu", "per_billed", "creation"], as_dict=True)
	tong = flt(so.rounded_total) or flt(so.grand_total)
	ds_phieu = _ds_phieu(so_name)
	hd = _hoa_don_cua(so)
	ma, nhan = trang_thai(tong, ds_phieu, bool(hd and int(hd.docstatus) == 1), int(so.docstatus) == 2)
	don = json.loads(so.vgb_tkr_du_lieu or "{}")
	return {
		"name": so.name, "ma": so.vgb_tkr_ma, "trang_thai": ma, "nhan": nhan, "khach": so.customer_name or so.customer,
		"sdt": don.get("sdt", ""), "tac_pham": don.get("tac_pham", ""), "kich_co": don.get("kich_co", ""),
		"ngay": str(so.delivery_date or ""), "gio": don.get("gio", ""), "diem_nhan": don.get("ten_diem_nhan", ""),
		"tong": tron(tong), "coc": tron(so.vgb_tkr_coc), "con_lai": con_phai_thu(tong, ds_phieu),
		"bang_ke": (so.vgb_tkr_bang_ke or "").split("\n"), "ghi_chu": don.get("ghi_chu", ""),
		"hoa_don": hd.name if hd else "", "dat_luc": str(so.creation or "")[:16],
		"phieu": [{"name": p["name"], "so_tien": tron(p["so_tien"]), "docstatus": int(p["docstatus"]),
			"pt": p.get("mode_of_payment") or "", "quay": p.get("vgb_quay") or "", "ngay": str(p.get("posting_date") or ""),
			"gd": p.get("vgb_gd_tkr") or ""} for p in ds_phieu],
	}


@frappe.whitelist()
def ds_don(trang_thai_loc="", tim=""):
	"""Danh sách đơn đặt trước thiết kế riêng, xếp theo ngày nhận."""
	_kiem_quyen()
	tu = str(frappe.utils.add_days(_hom_nay(), -60))
	ten = frappe.get_all(SO, filters={"vgb_tkr_ma": ["is", "set"], "docstatus": ["in", [1, 2]],
		"delivery_date": [">=", tu]}, pluck="name", order_by="delivery_date asc, creation asc", limit_page_length=400)
	rows = [tom_tat(t) for t in ten]
	dem = {k: 0 for k, _ in TRANG_THAI}
	for r in rows:
		dem[r["trang_thai"]] = dem.get(r["trang_thai"], 0) + 1
	return {"rows": rows, "dem": dem, "hom_nay": _hom_nay(), "trang_thai": [{"k": k, "ten": t} for k, t in TRANG_THAI],
		"quay": [{"ma": d["ma"], "ten": d.get("ten_ngan") or d["ten"]} for d in _ds_diem() if d.get("quay")],
		"la_ke_toan": 1 if _la_ke_toan() else 0}


def _la_ke_toan():
	from vagabond.thu_tien import la_ke_toan

	return la_ke_toan()


@frappe.whitelist()
def xem(name):
	_kiem_quyen()
	t = tom_tat(name)
	t["qr"] = _qr(t["ma"], t["con_lai"]) if t["con_lai"] > 0 and t["trang_thai"] not in ("da_huy", "da_giao") else None
	t["quay"] = [{"ma": d["ma"], "ten": d.get("ten_ngan") or d["ten"]} for d in _ds_diem() if d.get("quay")]
	t["la_ke_toan"] = 1 if _la_ke_toan() else 0
	return t


def _khoa_don(name):
	r = frappe.db.sql("select name from `tabSales Order` where name=%s and ifnull(vgb_tkr_ma,'')!='' for update", (name,))
	if not r:
		frappe.throw("Không có đơn thiết kế riêng %s." % name)


def _quay_hop_le(quay):
	q = str(quay or "").strip().upper()
	if not any(d.get("quay") == q for d in _ds_diem()):
		frappe.throw("Chọn quầy đang thu tiền.")
	return q


@frappe.whitelist(methods=["POST"])
def thu_tien_mat(name, quay):
	"""Thu phần còn lại bằng tiền mặt tại quầy: phiếu thu ứng trước thứ hai,
	quầy = quầy đang thu, ghi sổ ngay (tiền vào két, Chốt ca đếm một lần)."""
	_kiem_quyen()
	from vagabond.thu_tien import nang_quyen_lap_phieu, tk_tien_thu, loi_chua_khai_tk

	q = _quay_hop_le(quay)
	_khoa_don(name)
	t = tom_tat(name)
	if t["trang_thai"] in ("da_huy", "da_giao"):
		frappe.throw("Đơn %s đã %s." % (t["ma"], t["nhan"].lower()))
	if t["con_lai"] <= 0:
		frappe.throw("Đơn %s đã thu đủ, không thu thêm." % t["ma"])
	cty = _cong_ty()
	tk, _ba = tk_tien_thu(cty, PT_TM)
	if not tk:
		frappe.throw(loi_chua_khai_tk(PT_TM))
	khach = frappe.db.get_value(SO, name, "customer")
	p = phieu_thu(name, khach, t["tong"], t["con_lai"], q, PT_TM, _hom_nay(), None,
		"Thu tiền mặt phần còn lại đơn thiết kế riêng %s tại quầy %s." % (t["ma"], q))
	p["reference_no"] = "TKR:%s:TM:%s" % (t["ma"], frappe.generate_hash(length=6))
	loi = loi_phieu(p)
	if loi:
		frappe.throw(loi)
	moc = "tkr_tm_" + frappe.generate_hash(length=8)
	frappe.db.savepoint(moc)
	try:
		with nang_quyen_lap_phieu() as goc:
			pe = frappe.get_doc(dict(p, company=cty, paid_to=tk))
			pe.setup_party_account_field()
			pe.set_missing_values()
			pe.flags.ignore_permissions = True
			pe.insert(ignore_permissions=True)
			pe.submit()
			from vagabond.thu_tien import _giu_chu

			_giu_chu(pe, goc)
	except Exception as e:
		frappe.db.rollback(save_point=moc)
		frappe.throw("Chưa thu được: %s. Chưa có phiếu nào được lập." % frappe.utils.strip_html(str(e))[:300])
	frappe.db.commit()
	return {"ok": 1, "phieu": pe.name, "don": tom_tat(name)}


@frappe.whitelist(methods=["POST"])
def kiem_tien_ve(name):
	"""Sau khi khách quét QR phần còn lại: tìm tiền về và lập phiếu thu nháp."""
	_kiem_quyen()
	lap = khop_mot(name)
	frappe.db.commit()
	return {"ok": 1, "lap": lap, "don": tom_tat(name)}


@frappe.whitelist(methods=["POST"])
def ghi_so_phieu(name, phieu, anh=None):
	"""Kế toán đính giấy báo Có hoặc UNC khách gửi rồi ghi sổ phiếu thu chuyển
	khoản của đơn (nháp do máy lập khi chiếm sao kê)."""
	_kiem_quyen()
	if not _la_ke_toan():
		frappe.throw("Chỉ kế toán ghi sổ phiếu thu chuyển khoản, sau khi đính giấy báo Có.")
	from vagabond.ung_truoc_don import ghi_so_nhap

	ghi_so_nhap(name, phieu, anh)
	frappe.db.commit()
	return {"ok": 1, "don": tom_tat(name)}


@frappe.whitelist(methods=["POST"])
def giao_banh(name, quay):
	"""Giao bánh và xuất hoá đơn: Sales Invoice lập từ phiếu đặt, ngày giao,
	phương thức "Trả trước", cấn ĐÚNG các phiếu thu đã ghi sổ của phiếu đặt."""
	_kiem_quyen()
	from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice
	from vagabond.thu_tien import nang_quyen_lap_phieu

	q = _quay_hop_le(quay)
	_khoa_don(name)
	t = tom_tat(name)
	if t["trang_thai"] == "da_giao":
		frappe.throw("Đơn %s đã giao, hoá đơn %s." % (t["ma"], t["hoa_don"]))
	if t["trang_thai"] == "da_huy":
		frappe.throw("Đơn %s đã huỷ." % t["ma"])
	if t["con_lai"] > 0:
		frappe.throw("Đơn %s còn phải thu %s. Thu phần còn lại trước khi giao bánh." % (t["ma"], vnd(t["con_lai"])))
	nhap = [p for p in t["phieu"] if p["docstatus"] == 0]
	if nhap:
		frappe.throw("Phiếu thu %s (chuyển khoản) chờ kế toán đính giấy báo Có và ghi sổ. Nhờ kế toán ghi sổ rồi bấm lại."
			% ", ".join(p["name"] for p in nhap))
	da_ghi = [p["name"] for p in t["phieu"] if p["docstatus"] == 1]
	so = frappe.get_doc(SO, name)
	diem = next((d for d in _ds_diem() if d.get("quay") == q), {})
	moc = "tkr_si_" + frappe.generate_hash(length=8)
	frappe.db.savepoint(moc)
	try:
		with nang_quyen_lap_phieu():
			si = make_sales_invoice(name, ignore_permissions=True)
			hn = _hom_nay()
			si.posting_date = hn
			si.set_posting_time = 1
			si.due_date = hn
			si.update_stock = 0
			# Tắt tự cấn: lõi sẽ vơ mọi khoản ứng trước chưa phân bổ của khách
			# (tiền nạp số dư, tiền chuyển dư), không chỉ của phiếu đặt này.
			si.allocate_advances_automatically = 0
			si.vgb_quay = q
			si.custom_nguon = nguon_cua_diem(diem)
			si.vgb_pt_thanh_toan = PT_TRA_TRUOC
			si.vgb_ma_tham_chieu = so.vgb_tkr_ma
			si.custom_pancake_id = "TKR-" + so.vgb_tkr_ma
			si.custom_pancake_display_id = so.vgb_tkr_ma
			from vagabond.ban_hang import XHD_MAC_DINH

			si.vgb_xhd_ten = XHD_MAC_DINH
			si.remarks = "\n".join((so.vgb_tkr_bang_ke or "").split("\n") + ["Đơn thiết kế riêng %s, phiếu đặt %s." % (so.vgb_tkr_ma, so.name)])[:1000]
			from vagabond.ung_truoc_don import cap_ung_truoc

			cap_ung_truoc(si, da_ghi)
			si.flags.ignore_permissions = True
			si.insert(ignore_permissions=True)
			si.submit()
	except Exception as e:
		frappe.db.rollback(save_point=moc)
		frappe.log_error(frappe.get_traceback(), "thiet_ke_rieng: xuất hoá đơn %s" % name)
		frappe.throw("Chưa xuất được hoá đơn cho đơn %s: %s. Chưa có hoá đơn nào được lập, bấm lại sau khi xử lý."
			% (t["ma"], frappe.utils.strip_html(str(e))[:300]))
	frappe.db.commit()
	return {"ok": 1, "hoa_don": si.name, "don": tom_tat(name)}


@frappe.whitelist(methods=["POST"])
def huy(name, ly_do=""):
	"""Huỷ đơn khi CHƯA nhận đồng nào. Đã có tiền (kể cả phiếu nháp đã chiếm sao
	kê) thì chặn: tiền khách phải đi đường hoàn tiền, màn này chưa làm."""
	_kiem_quyen()
	from vagabond.thu_tien import nang_quyen_lap_phieu

	ly_do = re.sub(r"\s+", " ", str(ly_do or "")).strip()
	if len(ly_do) < 5:
		frappe.throw("Ghi lý do huỷ.")
	_khoa_don(name)
	t = tom_tat(name)
	if t["trang_thai"] != "cho_coc":
		frappe.throw("Đơn %s đã nhận tiền (%s). Huỷ đơn có tiền phải lập phiếu hoàn tiền cho khách ở màn Hoàn tiền; "
			"màn này chỉ huỷ đơn chưa cọc." % (t["ma"], t["nhan"]))
	so = frappe.get_doc(SO, name)
	with nang_quyen_lap_phieu():
		so.add_comment("Comment", "Huỷ đơn thiết kế riêng: %s" % ly_do)
		so.flags.ignore_permissions = True
		so.cancel()
	frappe.db.commit()
	return {"ok": 1, "don": tom_tat(name)}
