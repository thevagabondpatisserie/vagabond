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


# v628 (Dễ báo 02/11/2026, ca TH1 và TH3): một khoản mang mã bill mà KHÔNG
# bill nào đang sống giữ thì sau bao nhiêu phút được coi là tiền chưa thuộc ai.
# Mười lăm phút đủ cho thu ngân lưu xong bill đang hiện mã QR; quá mốc đó mà
# vẫn chưa có bill nào lưu mã này thì bill đã mất trước khi lưu (app tải lại).
PHUT_MO_COI = 15


def bill_huy_nha(rows, co_phieu_hoan):
	"""Bill nào đã huỷ mềm và NHẢ tiền ra. THUẦN.

	rows           [{name, docstatus, vgb_huy}]
	co_phieu_hoan  tên các bill đang có phiếu hoàn tiền còn hiệu lực

	Nháp đã huỷ mềm không giữ tiền (đúng luật `doi_soat_sepay.chu_cua_giao_dich`
	đã dùng từ trước). Riêng bill đã có phiếu hoàn thì tiền đang chờ trả lại
	khách, không được gắn sang bill khác: gắn là một khoản tiền tính hai chỗ.
	Bill đã ghi sổ (docstatus 1) luôn giữ tiền.
	"""
	co_phieu_hoan = set(co_phieu_hoan or ())
	ra = set()
	for r in rows or []:
		try:
			ds, huy = int(r.get("docstatus") or 0), int(r.get("vgb_huy") or 0)
		except (TypeError, ValueError):
			continue
		if ds == 0 and huy and r.get("name") and r["name"] not in co_phieu_hoan:
			ra.add(r["name"])
	return ra


def cau_bill_nha(ma, ten, huy_luc="", ly_do=""):
	"""Câu giải thích vì sao khoản của một bill đã huỷ được gắn lại. THUẦN."""
	luc = str(huy_luc or "")[:16]
	gio = ""
	if len(luc) >= 16:
		gio = " lúc %s ngày %s/%s" % (luc[11:16], luc[8:10], luc[5:7])
	ld = str(ly_do or "").strip()
	return "Bill %s (%s) đã huỷ%s%s, chưa hoàn tiền cho khách." % (
		ma or ten, ten, gio, (" (lý do: %s)" % ld) if ld else "")


def cau_mo_coi(ma):
	"""Câu giải thích cho khoản mang mã của bill chưa từng lưu. THUẦN."""
	return "Chưa có bill nào lưu mã %s (bill bị mất trước khi lưu)." % ma


def qua_han_mo_coi(ngay_gd, phut_gd, hom_nay, phut_bay_gio, phut=PHUT_MO_COI):
	"""Khoản về đã đủ lâu để coi mã mồ côi là tiền chưa thuộc ai. THUẦN.

	Ngày khác hôm nay là đủ lâu. Thiếu giờ thì KHÔNG coi là đủ lâu: không
	đoán giờ, vì đoán sai là nhả tiền của bill đang chờ lưu.
	"""
	if not ngay_gd or not hom_nay:
		return False
	if str(ngay_gd)[:10] < str(hom_nay)[:10]:
		return True
	if str(ngay_gd)[:10] > str(hom_nay)[:10]:
		return False
	try:
		return float(phut_bay_gio) - float(phut_gd) >= float(phut)
	except (TypeError, ValueError):
		return False


def chu_theo_noi_dung(gds, ma_cua_bill, re_ma_bill, chu_ma=None, tu_do=None, gd_qua_han=None, ghi_chu=None):
	"""Hai kiểu "đã có chủ" đọc được ngay trên dòng sao kê. THUẦN.

	  - dòng mang mã của MỘT BILL KHÁC trong nội dung: tiền đó là của bill kia
	  - dòng đã khớp chứng từ trong Đối chiếu ngân hàng của ERPNext
	    (`da_phan_bo` > 1 đồng)

	ma_cua_bill  mọi mã bill đang xem từng mang (mã tham chiếu và mã bill gốc).
	             Codex #497 v1: sau lần gắn đầu mã tham chiếu đổi thành số ngân
	             hàng, so một ô thì mã gốc trong nội dung bị tưởng của bill khác.
	chu_ma       {mã: tên hoá đơn đang mang mã đó}, đã trừ bill đang xem và
	             bill đã huỷ nhả tiền.
	tu_do        {mã: câu giải thích} mã chỉ còn bill đã huỷ nhả tiền giữ
	             (v628). Dòng mang mã này không còn chủ, kèm câu giải thích.
	gd_qua_han   tên các dòng về đã quá PHUT_MO_COI phút (v628). Mã không ai
	             mang trên dòng quá hạn là bill đã mất trước khi lưu: tiền chưa
	             thuộc ai. Dòng chưa quá hạn thì VẪN coi là có chủ, vì bill đang
	             hiện mã QR có thể sắp được lưu.
	ghi_chu      dict ra: {tên dòng: {"cau": câu, "bill": bill đã huỷ hoặc ""}}
	             cho các dòng được nhả theo hai luật trên.
	Trả {tên dòng: câu nói ai đang giữ}.
	"""
	ra = {}
	if isinstance(ma_cua_bill, str):
		ma_cua_bill = [ma_cua_bill]
	cua_minh = {str(m or "").strip().upper() for m in (ma_cua_bill or []) if str(m or "").strip()}
	chu_ma = chu_ma or {}
	nha_mode = gd_qua_han is not None
	tu_do = tu_do or {}
	gd_qua_han = set(gd_qua_han or ())
	for g in gds or []:
		ten = g.get("ten")
		ma_la = []
		if re_ma_bill:
			ma_la = [m for m in re_ma_bill.findall(str(g.get("mo_ta") or "").upper()) if m not in cua_minh]
		if ma_la:
			# Codex #527 vòng 3: XÉT MỌI MÃ, không chỉ mã đầu. Còn một mã thuộc bill
			# đang sống là dòng có chủ; chỉ nhả khi mọi mã đều nhả được.
			song = [m for m in ma_la if chu_ma.get(m)]
			if song:
				ra[ten] = "bill %s (mã %s)" % (chu_ma[song[0]], song[0])
				continue
			if not nha_mode:
				ra[ten] = "bill mang mã " + ma_la[0]
				continue
			cho = [m for m in ma_la if m not in tu_do and ten not in gd_qua_han]
			if cho:
				ra[ten] = "bill mang mã %s (đang chờ lưu, sau %s phút chưa ai lưu thì gắn được)" % (cho[0], PHUT_MO_COI)
				continue
			if ghi_chu is not None:
				m = ma_la[0]
				if m in tu_do:
					ghi_chu[ten] = dict(tu_do[m]) if isinstance(tu_do[m], dict) else {"cau": str(tu_do[m]), "bill": ""}
				else:
					ghi_chu[ten] = {"cau": cau_mo_coi(m), "bill": ""}
		try:
			pb = float(g.get("da_phan_bo") or 0)
		except (TypeError, ValueError):
			pb = 0.0
		if pb > 1:
			ra[ten] = "chứng từ trong Đối chiếu ngân hàng"
	return ra


def dung_bang_do_tien(gds, bang, khoa_diem, rieng, tien, co_chu, vai, nguon, cung_tien, ghi_chu=None):
	"""Dựng toàn bộ kết quả của nút Dò tiền từ dữ liệu đã đọc. THUẦN.

	gds        [{ten, tien, gio, mo_ta}] mọi khoản tiền về trong ngày
	bang       bảng dấu tài khoản ảo (`bang_dau`)
	co_chu     {tên dòng: ai đang giữ}, đã hỏi toàn hệ
	vai        vai của người đang bấm
	nguon      chip người đã chọn, rỗng là để máy chọn
	cung_tien  phép "hai số tiền coi là một" (khop_tien.cung_tien)
	ghi_chu    {tên dòng: {"cau": ...}} khoản của bill đã huỷ hoặc bill mất
	           trước khi lưu (v628): hiện câu giải thích ngay trên dòng
	"""
	ghi_chu = ghi_chu or {}
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
			"ghi_chu": "" if co_chu.get(ten) else str((ghi_chu.get(ten) or {}).get("cau") or ""),
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


# v646 (chị Dung báo 09/11/2026, anh Việt: "có bao nhiêu điểm bán phải hiển
# thị hết"): màn chỉ lấy bill có quầy nên điểm Sales Online (không quầy) biến
# mất khỏi màn, bill Sales khách chuyển không theo mã QR không có chỗ để khớp.
NHAN_CHUA_RO = "Chưa rõ điểm"


def diem_cua_dong(quay, nguon, ma, diem_ds):
	"""Mã điểm bán của một bill trên màn Đối soát. THUẦN.

	quay     ô quầy của bill (rỗng với điểm không quầy như Sales Online)
	nguon    nguồn đơn của bill (Pancake, Tại chỗ...)
	ma       mã bill gốc (TCVxxxxx, SOLxxxxx, hoặc số đơn Pancake)
	diem_ds  danh sách điểm bán (diem_ban.ds), có ma, quay, nguon

	Có quầy: điểm của quầy đó (quầy lạ vẫn trả chính mã quầy, không giấu).
	Không quầy: theo tiền tố mã bill (SOL là Sales), rồi theo nguồn đơn
	của điểm không quầy, rồi điểm không quầy duy nhất (quy ước cũ
	`diem_ban.ma_theo_quay`: quầy rỗng là Sales Online). Không đoán được thì
	trả rỗng, màn hiện ở chip Chưa rõ điểm.
	"""
	from vagabond import ma_bill

	diem_ds = [d for d in diem_ds or [] if d.get("ma")]
	q = str(quay or "").strip().upper()
	if q:
		for d in diem_ds:
			if str(d.get("quay") or "").strip().upper() == q:
				return d["ma"]
		return q
	khong_quay = [d for d in diem_ds if not str(d.get("quay") or "").strip()]
	m = str(ma or "").strip().upper()
	if m and re.fullmatch(ma_bill.mau_do(), m):
		for d in diem_ds:
			tt = ma_bill.TIEN_TO_DIEM.get(d["ma"])
			if tt and tt != ma_bill.TIEN_TO_CU and m.startswith(tt):
				return d["ma"]
	n = str(nguon or "").strip()
	if n:
		for d in khong_quay:
			if n in (d.get("nguon") or []):
				return d["ma"]
	if len(khong_quay) == 1:
		return khong_quay[0]["ma"]
	return ""


def nhan_diem(d):
	"""Chữ trên chip của một điểm. THUẦN. Điểm có quầy giữ mã quầy như màn
	đang hiện (TCV, NVHTN), điểm không quầy dùng tên ngắn (Sales Online)."""
	q = str(d.get("quay") or "").strip()
	return q or str(d.get("ten_ngan") or d.get("ten") or d.get("ma") or "")


def chip_diem(diem_ds, ma_co_bill):
	"""Danh sách chip điểm bán của màn. THUẦN.

	Mọi điểm ĐANG BẬT luôn có chip, kể cả ngày không có bill nào (đếm 0), theo
	thứ tự cài đặt. Điểm đã tắt hay quầy lạ mà vẫn có bill trong ngày thì
	thêm vào sau. Bill không rõ điểm thì có chip Chưa rõ điểm ở cuối.
	Trả [{"ma", "ten"}].
	"""
	ra, co = [], set()
	theo_ma = {d["ma"]: d for d in diem_ds or [] if d.get("ma")}
	for d in diem_ds or []:
		if d.get("ma") and d.get("bat", 1) and d["ma"] not in co:
			ra.append({"ma": d["ma"], "ten": nhan_diem(d)})
			co.add(d["ma"])
	for m in ma_co_bill or []:
		if m and m not in co:
			ra.append({"ma": m, "ten": nhan_diem(theo_ma[m]) if m in theo_ma else m})
			co.add(m)
	if "" in set(ma_co_bill or []):
		ra.append({"ma": "", "ten": NHAN_CHUA_RO})
	return ra


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


def _diem_ds_he():
	"""Mọi điểm bán (kể cả đã tắt, để bill cũ của điểm đã tắt vẫn có tên).
	Chạm hệ."""
	from vagabond import diem_ban

	try:
		return diem_ban.ds()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "doi_soat_ck: doc diem ban")
		return []


@frappe.whitelist()
def ds_bill_ck(ngay=None, diem=""):
	"""Bill trả bằng chuyển khoản trong một ngày của MỌI điểm bán, kèm tiền
	đã khớp. Chỉ đọc, không ghi.

	v646: gồm cả điểm không quầy (Sales Online: đơn Pancake và bill quầy
	Sales mã SOL), để khoản khách chuyển không theo mã QR có chỗ khớp tay.
	`diem_ds` là chip điểm bán: mọi điểm đang bật luôn có mặt.
	"""
	if not co_quyen_ngoai():
		frappe.throw("Màn Đối soát chuyển khoản chỉ mở cho Quản lý cửa hàng và Kế toán.")
	from vagabond import ban_hang as bh

	ngay = str(getdate(ngay or nowdate()))
	loc = {
		"posting_date": ngay,
		"docstatus": ["<", 2],
		"vgb_pt_thanh_toan": "Chuyển khoản",
		"vgb_huy": 0,
		"vgb_tam_tinh": 0,
	}
	# v646: bỏ điều kiện "có quầy". Bill Sales Online (đơn Pancake, bill quầy
	# Sales mã SOL) để trống ô quầy nên trước đây cả điểm Sales biến mất.
	d = str(diem or "").strip().upper()
	ds = frappe.get_all(
		"Sales Invoice", filters=loc,
		fields=["name", "creation", "docstatus", "grand_total", "vgb_quay",
			"vgb_ma_tham_chieu", "custom_pancake_display_id", "customer_name",
			"vgb_ghi_chu_doi_soat", "custom_nguon"],
		order_by="creation desc", limit_page_length=0)
	diem_ds = _diem_ds_he()
	theo_ma, _bo = bh._sepay_theo_ma_bill(
		[r.vgb_ma_tham_chieu for r in ds] + [r.custom_pancake_display_id for r in ds])
	# Đơn Pancake còn nháp: tiền khớp theo mạch S<shop>O<đơn>T như cửa ghi sổ
	# (`ban_hang._soat_sepay`). Đơn đã ghi sổ thì đã đủ tiền, khỏi hỏi.
	theo_don = {}
	so_don = [str(r.custom_pancake_display_id or "").strip() for r in ds
		if cint(r.docstatus) == 0 and str(r.custom_pancake_display_id or "").strip()
		and not bh.RE_MA_BILL.fullmatch(str(r.custom_pancake_display_id or "").strip().upper())]
	if so_don:
		try:
			theo_don = bh._sepay_theo_don(bh.cfg().pancake_shop_id, so_don) or {}
		except Exception:
			frappe.log_error(frappe.get_traceback(), "doi_soat_ck: doc tien don Pancake")
			theo_don = {}
	rows, dem = [], {TT_DU: 0, TT_THIEU: 0, TT_CHUA: 0}
	for r in ds:
		ma_tc = str(r.vgb_ma_tham_chieu or "").strip().upper()
		# Mã bill gốc nằm yên ở custom_pancake_display_id; ô tham chiếu đổi
		# thành số ngân hàng sau khi gắn tay (Codex #497 v1).
		ma = str(r.custom_pancake_display_id or "").strip().upper() or ma_tc
		dm = diem_cua_dong(r.vgb_quay, r.custom_nguon, ma, diem_ds)
		if d and dm != d:
			continue
		nhan = max(flt((theo_ma.get(ma) or {}).get("nhan")), flt((theo_ma.get(ma_tc) or {}).get("nhan")),
			flt((theo_don.get(str(r.custom_pancake_display_id or "").strip()) or {}).get("nhan")))
		# Bill đã ghi sổ là đủ tiền, khỏi hỏi sao kê theo số tham chiếu từng dòng
		# (v646: điểm Sales có vài chục đơn mỗi ngày).
		if cint(r.docstatus) == 0 and ma_tc and not bh.RE_MA_BILL.fullmatch(ma_tc):
			nhan = max(nhan, flt((bh._sepay_theo_tham_chieu(ma_tc) or {}).get("nhan")))
		tt = TT_DU if cint(r.docstatus) == 1 else trang_thai_tien(nhan, r.grand_total)
		dem[tt] = dem.get(tt, 0) + 1
		rows.append({
			"name": r.name, "ma": ma, "ma_tc": ma_tc, "quay": r.vgb_quay or "", "diem": dm,
			"gio": str(r.creation or "")[11:16], "tong": flt(r.grand_total),
			"nhan": nhan, "tt": tt, "ghi_so": cint(r.docstatus),
			"khach": r.customer_name or "",
			"vet": str(r.vgb_ghi_chu_doi_soat or "")[-160:],
		})
	# Chưa khớp lên đầu, rồi thiếu, rồi đủ; trong nhóm thì mới nhất trước.
	thu_tu = {TT_CHUA: 0, TT_THIEU: 1, TT_DU: 2}
	rows.sort(key=lambda x: thu_tu.get(x["tt"], 3))
	return {"ngay": ngay, "rows": rows, "dem": dem, "diem": d,
		"diem_ds": chip_diem(diem_ds, [x["diem"] for x in rows])}
