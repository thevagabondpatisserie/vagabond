# -*- coding: utf-8 -*-
"""Đối soát tay tiền chuyển khoản của bill quầy (v610).

ANH VIỆT 24/10/2026, theo báo của Dễ
------------------------------------
Bill TCVEHQHG (HDB-26-10-04707) ngày 23/10, 1.875.000 đ. Khách không quét
QR mà xin số tài khoản công ty rồi chuyển thẳng vào MB 31561568. Dễ báo
"SePay không ghi nhận nên không ghi sổ tự động được".

SỰ THẬT ĐỌC TRÊN SITE
---------------------
SePay CÓ ghi: dòng ACC-BTN-2026-08831, 1.875.000 đ, lúc 13:27, tài khoản
MB-CTY-31561568, nội dung "Nam transfers money quickly via Zalo ...". Cái
hỏng là nút "Dò tiền chuyển khoản" chỉ liệt kê tiền vào TÀI KHOẢN ẢO của
điểm (lọc theo dấu tài khoản ảo trong nội dung). Tiền vào thẳng tài khoản
chính không mang dấu tài khoản ảo nào, nên không bao giờ hiện ra để chọn.

Anh Việt chốt:
  * làm cả hai: chip lọc tài khoản trong nút Dò tiền, và màn riêng
    "Đối soát chuyển khoản" liệt kê bill chuyển khoản chưa khớp tiền;
  * khoản vào tài khoản chính (nơi cũng nhận tiền khách sỉ trả nợ, nhà cung
    cấp hoàn tiền) chỉ Quản lý cửa hàng và Kế toán được gắn cho bill quầy.

Các hàm trên vạch "phần chạm hệ" THUẦN. Phần dưới chạm hệ, và chỉ nhập
`ban_hang` bên trong hàm (ban_hang kéo theo `requests`, máy CI tay không).
"""

import re

import frappe
from frappe.utils import cint, flt, getdate, nowdate

# Ba nguồn của chip lọc trong nút Dò tiền.
NGUON_DIEM = "diem"      # tiền vào tài khoản ảo của chính điểm bán này
NGUON_CTY = "cty"        # tiền vào thẳng tài khoản chính, không qua tài khoản ảo nào
NGUON_TAT_CA = "tat_ca"  # mọi khoản tiền về trong ngày
NGUON = (NGUON_DIEM, NGUON_CTY, NGUON_TAT_CA)

# Ai được gắn một khoản KHÔNG nằm trong tài khoản ảo của điểm (anh Việt
# 24/10/2026), và cũng là ai được mở màn Đối soát chuyển khoản. Bản JS
# QUYEN_DSCK trong 56-doi-soat-ck.js phải trùng từng chữ, có ca kiểm chốt.
QUYEN_GAN_NGOAI = (
	"VGB - Quản lý cửa hàng",
	"Accounts Manager",
	"Accounts User",
	"System Manager",
	"Giám đốc",
	"AP Giám đốc",
)

NHAN_CTY = "Vào thẳng tài khoản chính công ty"

# Trạng thái tiền của một bill chuyển khoản.
TT_DU = "du"        # ngân hàng đã nhận đủ
TT_THIEU = "thieu"  # đã nhận một phần
TT_CHUA = "chua"    # chưa khớp được khoản nào


def dau_tk(stk):
	"""Dấu nhận diện một tài khoản ảo trong nội dung sao kê. THUẦN.

	Ngân hàng ghi "Q00033k5p6" cho tài khoản "VQRQ00033k5p6": nó cắt ba chữ
	VQR ở đầu. Chỉ tài khoản ẢO mới để lại dấu trong nội dung; tài khoản
	thường (số 31561568) thì không, nên tài khoản thường trả rỗng.
	"""
	t = re.sub(r"\s+", "", str(stk or "")).upper()
	return t[3:] if t.startswith("VQR") and len(t) > 3 else ""


def bang_dau(cau_hinh, ten_diem=None):
	"""Bảng các tài khoản ảo đang khai: [{"dau", "khoa", "nhan"}]. THUẦN.

	cau_hinh  kết quả `tai_khoan.cai()`: {"mac_dinh": {...}, "theo_nguon": [...]}
	ten_diem  {mã điểm: tên ngắn} để nhãn đọc ra "Điểm Trần Cao Vân"

	Tài khoản theo nguồn đặt TRƯỚC tài khoản mặc định: hai dấu trùng nhau
	thì nhãn cụ thể thắng nhãn chung.
	"""
	ten_diem = ten_diem or {}
	ra, da = [], set()
	for t in (cau_hinh or {}).get("theo_nguon") or []:
		d = dau_tk((t or {}).get("stk"))
		if not d or d in da:
			continue
		khoa = str(t.get("nguon") or "").strip()
		if khoa.startswith("@diem:"):
			ma = khoa[len("@diem:"):].strip().upper()
			nhan = "Điểm " + str(ten_diem.get(ma) or ma)
		elif khoa == "@phieu_cong_no":
			nhan = "Phiếu đòi nợ khách sỉ"
		else:
			nhan = khoa or "Tài khoản ảo"
		ra.append({"dau": d, "khoa": khoa, "nhan": nhan})
		da.add(d)
	md = dau_tk(((cau_hinh or {}).get("mac_dinh") or {}).get("stk"))
	if md and md not in da:
		ra.append({"dau": md, "khoa": "@mac_dinh", "nhan": "Tài khoản ảo mặc định"})
	return ra


def thuoc_tk(mo_ta, bang):
	"""Một dòng sao kê vào tài khoản ảo nào. THUẦN.

	Trả (khoa, nhan). Không mang dấu tài khoản ảo nào thì trả ("", NHAN_CTY):
	tiền vào thẳng tài khoản chính.
	"""
	chu = str(mo_ta or "").upper()
	for b in bang or []:
		if b.get("dau") and b["dau"] in chu:
			return b.get("khoa") or "", b.get("nhan") or ""
	return "", NHAN_CTY


def loc_theo_nguon(gds, nguon, khoa_diem, rieng):
	"""Lọc các dòng đã gắn `khoa_tk` theo chip đang chọn. THUẦN.

	khoa_diem  khoá tài khoản của điểm, dạng "@diem:TCV"
	rieng      điểm có tài khoản ảo riêng không. Không có thì chip "diem"
	           giữ đúng nếp cũ: hiện cả sao kê chung.
	"""
	n = nguon if nguon in NGUON else NGUON_DIEM
	if n == NGUON_TAT_CA:
		return list(gds or [])
	if n == NGUON_CTY:
		return [g for g in gds or [] if not g.get("khoa_tk")]
	if not rieng:
		return list(gds or [])
	return [g for g in gds or [] if g.get("khoa_tk") == khoa_diem]


def duoc_gan(khoa_gd, khoa_diem, rieng, vai):
	"""Người này có được gắn dòng sao kê này cho bill của điểm không. THUẦN.

	Khoản vào đúng tài khoản ảo của điểm: ai đứng quầy cũng gắn được, như
	trước. Điểm chưa khai tài khoản riêng: giữ nếp cũ, ai cũng gắn được.
	Còn lại (tài khoản chính, tài khoản ảo của điểm khác, của khách sỉ):
	chỉ quản lý cửa hàng và kế toán.
	"""
	if not rieng or (khoa_gd and khoa_gd == khoa_diem):
		return True
	return bool(set(vai or []) & set(QUYEN_GAN_NGOAI))


def nguon_mac_dinh(nguon, so_khop_diem, so_khop_cty):
	"""Chip nào sáng khi mở bảng dò tiền. THUẦN.

	Người đã bấm chip thì giữ đúng chip đó. Mở lần đầu: tài khoản điểm có
	khoản đúng số tiền thì mở ở đó như cũ; không có mà tài khoản chính lại có
	thì mở thẳng chip tài khoản chính, khỏi bắt người bấm thêm một lần.
	"""
	if nguon in NGUON:
		return nguon
	if not so_khop_diem and so_khop_cty:
		return NGUON_CTY
	return NGUON_DIEM


def trang_thai_tien(nhan, tong, sai_so=1.0):
	"""Trạng thái tiền của một bill chuyển khoản. THUẦN."""
	try:
		n, t = float(nhan or 0), float(tong or 0)
	except (TypeError, ValueError):
		return TT_CHUA
	if n >= t - float(sai_so):
		return TT_DU
	if n > 0:
		return TT_THIEU
	return TT_CHUA


def chu_theo_noi_dung(gds, ma_cua_bill, re_ma_bill, chu_ma=None):
	"""Hai kiểu "đã có chủ" đọc được ngay trên dòng sao kê. THUẦN.

	  - dòng mang mã của MỘT BILL KHÁC trong nội dung: tiền đó là của bill kia
	  - dòng đã khớp chứng từ trong Đối chiếu ngân hàng của ERPNext
	    (`da_phan_bo` > 1 đồng)

	ma_cua_bill  mọi mã bill đang xem từng mang (mã tham chiếu và mã bill gốc).
	             Codex #497 v1: sau lần gắn đầu mã tham chiếu đổi thành số ngân
	             hàng, so một ô thì mã gốc trong nội dung bị tưởng của bill khác.
	chu_ma       {mã: tên hoá đơn đang mang mã đó}, đã trừ bill đang xem. Mã
	             không ai mang mà cũng không phải của bill này thì VẪN coi là
	             có chủ: không đoán.
	Trả {tên dòng: câu nói ai đang giữ}.
	"""
	ra = {}
	if isinstance(ma_cua_bill, str):
		ma_cua_bill = [ma_cua_bill]
	cua_minh = {str(m or "").strip().upper() for m in (ma_cua_bill or []) if str(m or "").strip()}
	chu_ma = chu_ma or {}
	for g in gds or []:
		ten = g.get("ten")
		ma_la = []
		if re_ma_bill:
			ma_la = [m for m in re_ma_bill.findall(str(g.get("mo_ta") or "").upper()) if m not in cua_minh]
		if ma_la:
			m = ma_la[0]
			ra[ten] = ("bill %s (mã %s)" % (chu_ma[m], m)) if chu_ma.get(m) else ("bill mang mã " + m)
			continue
		try:
			pb = float(g.get("da_phan_bo") or 0)
		except (TypeError, ValueError):
			pb = 0.0
		if pb > 1:
			ra[ten] = "chứng từ trong Đối chiếu ngân hàng"
	return ra


def dung_bang_do_tien(gds, bang, khoa_diem, rieng, tien, co_chu, vai, nguon, cung_tien):
	"""Dựng toàn bộ kết quả của nút Dò tiền từ dữ liệu đã đọc. THUẦN.

	gds        [{ten, tien, gio, mo_ta}] mọi khoản tiền về trong ngày
	bang       bảng dấu tài khoản ảo (`bang_dau`)
	co_chu     {tên dòng: ai đang giữ}, đã hỏi toàn hệ
	vai        vai của người đang bấm
	nguon      chip người đã chọn, rỗng là để máy chọn
	cung_tien  phép "hai số tiền coi là một" (khop_tien.cung_tien)
	"""
	gds = [dict(g) for g in gds or []]
	for g in gds:
		g["khoa_tk"], g["nhan_tk"] = thuoc_tk(g.get("mo_ta"), bang)
	co_chu = co_chu or {}

	def khop(g):
		return bool(tien) and cung_tien(g.get("tien"), tien) and g.get("ten") not in co_chu

	cac = {n: loc_theo_nguon(gds, n, khoa_diem, rieng) for n in NGUON}
	so_khop = {n: len([g for g in cac[n] if khop(g)]) for n in NGUON}
	so_dong = {n: len(cac[n]) for n in NGUON}
	chon = nguon_mac_dinh(str(nguon or "").strip(), so_khop[NGUON_DIEM], so_khop[NGUON_CTY])
	ra = []
	for g in cac[chon]:
		ten = g.get("ten")
		ra.append({
			"ten": ten,
			"tien": float(g.get("tien") or 0),
			"gio": g.get("gio") or "",
			"mo_ta": str(g.get("mo_ta") or "").strip()[:140],
			"khop": 1 if khop(g) else 0,
			"cua_bill": co_chu.get(ten) or "",
			"tk_nhan": g.get("nhan_tk") or "",
			"duoc_gan": 1 if duoc_gan(g.get("khoa_tk"), khoa_diem, rieng, vai) else 0,
		})
	# Khoản khớp và chưa có chủ lên đầu, rồi khoản chưa có chủ, cuối cùng là
	# khoản đã thuộc chứng từ khác. Trong từng nhóm thì theo giờ.
	ra.sort(key=lambda g: (0 if g["khop"] else (1 if not g["cua_bill"] else 2), g["gio"]))
	return {
		"nguon": chon,
		"so_khop_nguon": so_khop,
		"so_dong_nguon": so_dong,
		"so_khop": len([g for g in ra if g["khop"]]),
		"gan_ngoai": 1 if set(vai or []) & set(QUYEN_GAN_NGOAI) else 0,
		"gd": ra,
	}


# ------------------------------------------------------------- phần chạm hệ

def _vai():
	return frappe.get_roles()


def co_quyen_ngoai():
	return bool(set(_vai()) & set(QUYEN_GAN_NGOAI))


def bang_dau_he():
	"""Đọc bảng dấu tài khoản ảo trên site. Chạm hệ."""
	from vagabond import diem_ban, tai_khoan

	ten = {}
	try:
		for d in diem_ban.ds():
			ten[d["ma"]] = d.get("ten_ngan") or d.get("ten") or d["ma"]
	except Exception:
		frappe.log_error(frappe.get_traceback(), "doi_soat_ck: doc ten diem ban")
	return bang_dau(tai_khoan.cai(), ten)


@frappe.whitelist()
def ds_bill_ck(ngay=None, diem=""):
	"""Bill quầy trả bằng chuyển khoản trong một ngày, kèm tiền đã khớp.

	Chỉ đọc, không ghi. Bill Pancake (không có quầy) đối soát theo số đơn ở
	màn Đơn còn treo, không nằm ở đây.
	"""
	if not co_quyen_ngoai():
		frappe.throw("Màn Đối soát chuyển khoản chỉ mở cho Quản lý cửa hàng và Kế toán.")
	from vagabond import ban_hang as bh

	ngay = str(getdate(ngay or nowdate()))
	loc = {
		"posting_date": ngay,
		"docstatus": ["<", 2],
		"vgb_pt_thanh_toan": "Chuyển khoản",
		"vgb_quay": ["is", "set"],
		"vgb_huy": 0,
		"vgb_tam_tinh": 0,
	}
	d = str(diem or "").strip().upper()
	if d:
		loc["vgb_quay"] = d
	ds = frappe.get_all(
		"Sales Invoice", filters=loc,
		fields=["name", "creation", "docstatus", "grand_total", "vgb_quay",
			"vgb_ma_tham_chieu", "custom_pancake_display_id", "customer_name",
			"vgb_ghi_chu_doi_soat"],
		order_by="creation desc", limit_page_length=0)
	theo_ma, _bo = bh._sepay_theo_ma_bill(
		[r.vgb_ma_tham_chieu for r in ds] + [r.custom_pancake_display_id for r in ds])
	rows, dem = [], {TT_DU: 0, TT_THIEU: 0, TT_CHUA: 0}
	for r in ds:
		ma_tc = str(r.vgb_ma_tham_chieu or "").strip().upper()
		# Mã bill gốc nằm yên ở custom_pancake_display_id; ô tham chiếu đổi
		# thành số ngân hàng sau khi gắn tay (Codex #497 v1).
		ma = str(r.custom_pancake_display_id or "").strip().upper() or ma_tc
		nhan = max(flt((theo_ma.get(ma) or {}).get("nhan")), flt((theo_ma.get(ma_tc) or {}).get("nhan")))
		if ma_tc and not bh.RE_MA_BILL.fullmatch(ma_tc):
			nhan = max(nhan, flt((bh._sepay_theo_tham_chieu(ma_tc) or {}).get("nhan")))
		tt = TT_DU if cint(r.docstatus) == 1 else trang_thai_tien(nhan, r.grand_total)
		dem[tt] = dem.get(tt, 0) + 1
		rows.append({
			"name": r.name, "ma": ma, "ma_tc": ma_tc, "quay": r.vgb_quay or "",
			"gio": str(r.creation or "")[11:16], "tong": flt(r.grand_total),
			"nhan": nhan, "tt": tt, "ghi_so": cint(r.docstatus),
			"khach": r.customer_name or "",
			"vet": str(r.vgb_ghi_chu_doi_soat or "")[-160:],
		})
	# Chưa khớp lên đầu, rồi thiếu, rồi đủ; trong nhóm thì mới nhất trước.
	thu_tu = {TT_CHUA: 0, TT_THIEU: 1, TT_DU: 2}
	rows.sort(key=lambda x: thu_tu.get(x["tt"], 3))
	return {"ngay": ngay, "rows": rows, "dem": dem, "diem": d}
