# -*- coding: utf-8 -*-
"""Phân hệ Tài chính (v626).

ANH VIỆT 31/10/2026
-------------------
"Em tham khảo các phần mềm hàng đầu để làm nút phân hệ Tài chính trên app:
tổng tiền mặt hiện có, tổng tiền ngân hàng hiện có (qua SePay, anh đưa em số
dư ban đầu tại thời điểm chốt, em tự tính), tỉ lệ hao hụt, còn nút gì nữa em
khảo sát để làm." Sau khi xem ảnh mẫu, anh chốt:
  * làm đủ chín nút: Tổng quan, Tiền hiện có, Dòng tiền, Dự báo 30 ngày, Lãi
    lỗ tháng, Tỉ lệ giá vốn và hao hụt, Khách nợ mình, Mình nợ nhà cung cấp,
    Chờ chi, Tiền khách gửi trước (bốn ô sau mở màn đã có);
  * chỉ Giám đốc và kế toán trưởng thấy; kế toán viên không thấy;
  * tiền mặt tách từng két cửa hàng và quỹ công ty;
  * tài khoản tạm ứng OCB, ACB, MB (đứng tên cá nhân) tính vào tổng nhưng
    tách dòng ghi rõ tạm ứng.

SỰ THẬT ĐỌC TRÊN SITE 31/10 (vì sao không đọc số dư từ sổ cái)
----------------------------------------------------------------
  * Sổ cái 11211 MB công ty đang ÂM 5,8 tỷ, 1111 tiền mặt âm 249 triệu: số
    dư đầu kỳ chưa từng nhập, tiền bán tại quầy không đi qua 1111. Lấy số dư
    từ sổ cái là ra số sai. Nên số dư = MỐC CHỐT anh đưa + phát sinh từ sau
    ngày chốt, đúng như anh dặn.
  * SePay userapi/bankaccounts trả ô `accumulated` (số dư). Với MB, OCB, ACB
    ô đó luôn 0 (SePay nhận biến động, không đọc số dư). Riêng Shinhan
    700037279585 SePay báo số dư thật. Nên: tài khoản nào SePay báo số dư
    thì đối chiếu với số app tự tính; tài khoản SePay không đồng bộ giao dịch
    (Shinhan, không nằm trong account_map) thì lấy luôn số SePay báo.
  * Tiền vào két: dùng ĐÚNG phép của màn Chốt ca (ca_quay._doanh_thu_he_thong:
    tách bill trả nhiều phương thức, cộng tiền đặt bánh trả trước và tiền
    nạp số dư tại quầy). Không tự cộng hoá đơn lần nữa ở đây.
  * Két ra quỹ: phiếu Nộp quỹ (Vagabond Nop Quy). Phiếu này không ghi sổ cái.

GIỚI HẠN ĐÃ BIẾT (ghi thẳng lên màn để người đọc không tin nhầm)
-----------------------------------------------------------------
  * Chi tiền mặt từ két không qua app (mua lặt vặt) thì app không thấy: két
    tính ra cao hơn thật. Cách sửa: bấm Chốt lại số dư sau khi đếm.
  * Quỹ công ty trừ chi tiền mặt bằng bút toán sổ cái 111 (trừ hoá đơn bán).
    Nộp tiền mặt vào ngân hàng mà không ghi bút toán thì quỹ không giảm.

Các hàm trên vạch "phần chạm hệ" THUẦN, ca kiểm chạy thẳng không cần Frappe.
"""

import json
import re
from datetime import date, datetime, timedelta
from difflib import SequenceMatcher

import frappe
from frappe.utils import cint, flt, getdate, now_datetime, nowdate

# ---------------------------------------------------------------- hằng số

DT_MOC = "Vagabond Moc So Du"
DT_CAI = "Vagabond Tai Chinh Cai Dat"

# Hai vai luôn xem được. Người khác (kế toán trưởng) do Giám đốc chọn đích
# danh ở màn Cài đặt Tài chính: gói Kế toán đang có cả Accounts Manager lẫn
# AP Kiểm soát (FIN), dùng vai thì mọi kế toán viên đều thấy (anh Việt không
# muốn). AP Giám đốc cũng không dùng: quản lý cửa hàng đang có vai đó để duyệt
# chi. Bản JS TC_VAI_LUON_XEM trong 61-tai-chinh.js phải trùng, có ca kiểm.
VAI_LUON_XEM = ("System Manager", "Giám đốc")

LOAI_NH = "Ngân hàng"
LOAI_TM = "Tiền mặt"
NGUON_QUY = "tm:QUY"
TEN_QUY = "Quỹ tiền mặt công ty"
TIEN_MAT = "Tiền mặt"

# Lệch dưới mức này coi như khớp (làm tròn, phí lẻ).
NGUONG_KHOP = 1000
# Hai nội dung chuyển khoản phải chung một đoạn liền ít nhất chừng này ký tự
# (sau khi bỏ dấu cách) mới là bằng chứng hai vế cùng một lệnh chuyển nội bộ.
NGAN_NHAT_MO_TA = 20

# Tài khoản chi phí nhân viên, cộng vào giá vốn thành prime cost.
TK_NHAN_VIEN = ("622", "6411", "6421")

KY_DONG_TIEN = (7, 30)

# Hao hụt kiểm kê một kho vượt mức này (phần trăm nguyên liệu đã dùng) thì
# màn gắn chip Bất thường: thường là lần đếm đầu sau khi dựng kho, không phải
# hao hụt thật (Baker tháng 10/2026: thiếu 301 triệu trên 186 triệu dùng).
NGUONG_BAT_THUONG = 20
NGAY_SOM_NHAT = date(2025, 1, 1)


# ================================================================ THUẦN

def chuoi(x):
	return str(x if x is not None else "").strip()


def doc_nguoi_xem(chu):
	"""Danh sách tài khoản được xem, từ ô chữ cấu hình. THUẦN.

	Ô do người gõ: chịu mọi cách ngăn (xuống dòng, dấu phẩy, chấm phẩy, khoảng
	trắng), chữ hoa, trùng. Chỉ nhận chuỗi có @ hoặc đúng Administrator.
	"""
	ra = []
	for t in re.split(r"[\s,;]+", chuoi(chu)):
		t = t.strip().strip("<>\"'")
		if not t:
			continue
		if t.lower() == "administrator":
			t = "Administrator"
		elif "@" in t:
			t = t.lower()
		else:
			continue
		if t not in ra:
			ra.append(t)
	return ra


def duoc_xem(nguoi, vai, nguoi_xem):
	"""Người này có được mở phân hệ Tài chính không. THUẦN."""
	if set(vai or ()) & set(VAI_LUON_XEM):
		return True
	n = chuoi(nguoi)
	if not n or n == "Guest":
		return False
	ds = [x.lower() for x in (nguoi_xem or [])]
	return n.lower() in ds


def doc_so_tien(x):
	"""Số tiền người gõ: "1.628.400.000", "1,628,400,000", "1628400000 đ",
	"-5.000". THUẦN. Trả float, hoặc None khi không đọc được.

	Tiền Việt không có phần lẻ, nên mọi dấu chấm, phẩy, khoảng trắng đều là
	dấu ngăn nghìn.
	"""
	if isinstance(x, (int, float)):
		return float(x)
	t = chuoi(x)
	if not t:
		return None
	am = t.lstrip().startswith("-")
	so = re.sub(r"[^0-9]", "", t)
	if not so:
		return None
	v = float(int(so))
	return -v if am else v


def doc_ngay(x):
	"""Ngày người chọn, dạng YYYY-MM-DD hoặc DD/MM/YYYY. THUẦN. None khi hỏng."""
	t = chuoi(x)
	if not t:
		return None
	try:
		if "/" in t:
			d, m, y = [int(p) for p in t.split("/")[:3]]
			return date(y, m, d)
		return date(*[int(p) for p in t[:10].split("-")])
	except Exception:
		return None


def kiem_moc(nguon, ngay, so, cac_nguon, hom_nay):
	"""Kiểm một mốc chốt trước khi lưu. THUẦN. Trả câu lỗi, rỗng là đạt."""
	if chuoi(nguon) not in set(cac_nguon or ()):
		return "Chọn lại tài khoản hoặc két cần chốt số dư."
	if ngay is None:
		return "Chọn ngày chốt số dư."
	if ngay > hom_nay:
		return "Ngày chốt không được sau hôm nay."
	if ngay < NGAY_SOM_NHAT:
		return "Ngày chốt quá xa, chọn từ năm 2025 trở đi."
	if so is None:
		return "Gõ số dư bằng số, ví dụ 1.628.400.000."
	if abs(so) >= 1e13:
		return "Số dư quá lớn, kiểm lại số chữ số."
	return ""


def moc_moi_nhat(cac_moc):
	"""{nguồn: mốc mới nhất}. Mốc sau ghi đè mốc trước theo (ngày chốt, lúc
	lưu). THUẦN. Chốt lại số dư là THÊM một mốc mới, không sửa mốc cũ."""
	ra = {}
	for m in cac_moc or ():
		k = chuoi(m.get("nguon"))
		if not k:
			continue
		khoa = (str(m.get("ngay_chot") or ""), str(m.get("luc") or ""), str(m.get("name") or ""))
		cu = ra.get(k)
		if cu is None or khoa > cu[0]:
			ra[k] = (khoa, m)
	return {k: v[1] for k, v in ra.items()}


def so_du_tu_moc(moc, vao, ra):
	"""Số dư = mốc chốt + vào - ra. Chưa có mốc thì None. THUẦN."""
	if not moc:
		return None
	return round(flt(moc.get("so_du")) + flt(vao) - flt(ra), 2)


def doi_chieu(so_tinh, so_bao, nguong=NGUONG_KHOP):
	"""So số app tính với số ngân hàng báo. THUẦN.

	so_bao <= 0 hoặc None: ngân hàng không báo số dư (MB, OCB, ACB qua SePay
	luôn báo 0), không kết luận khớp hay lệch."""
	if so_bao is None or flt(so_bao) <= 0:
		return {"tt": "khong_bao", "lech": 0.0}
	if so_tinh is None:
		return {"tt": "chua_chot", "lech": 0.0}
	lech = round(flt(so_tinh) - flt(so_bao), 2)
	return {"tt": "khop" if abs(lech) < nguong else "lech", "lech": lech}


def ten_ngan_hang(ten):
	"""'OCB - Ngân hàng TMCP Phương Đông' -> 'OCB'; 'MB Bank' -> 'MB Bank'."""
	t = chuoi(ten)
	return t.split(" - ")[0].strip() if " - " in t else t


def nguon_ngan_hang(ban_do, tk_cong_ty, so_bao):
	"""Danh sách tài khoản ngân hàng của phân hệ. THUẦN.

	ban_do      {số TK: tên Bank Account} của SePay Settings.account_map (đồng
	            bộ giao dịch về app).
	tk_cong_ty  [{name, account, bank, bank_account_no, is_company_account}] các
	            Bank Account có mặt trong ban_do HOẶC là tài khoản công ty.
	so_bao      {số TK: số dư SePay báo}.

	Tạm ứng = tài khoản sổ cái 141x (đứng tên cá nhân). Chỉ hiện bốn số cuối.
	Tài khoản công ty không đồng bộ giao dịch mà SePay cũng không báo số dư
	thì vẫn liệt kê, để Giám đốc chốt tay.
	"""
	ban_do = ban_do or {}
	theo_ten = {chuoi(r.get("name")): r for r in tk_cong_ty or ()}
	stk_cua = {}
	for stk, ten in ban_do.items():
		stk_cua[chuoi(ten)] = chuoi(stk)
	ra, da = [], set()
	ds = list(ban_do.items()) + [
		(chuoi(r.get("bank_account_no")), chuoi(r.get("name"))) for r in tk_cong_ty or ()
		if cint(r.get("is_company_account")) and chuoi(r.get("name")) not in stk_cua
	]
	for stk, ten in ds:
		stk, ten = chuoi(stk), chuoi(ten)
		if not stk or stk in da:
			continue
		da.add(stk)
		r = theo_ten.get(ten) or {}
		tk = chuoi(r.get("account"))
		tam_ung = tk.startswith("141")
		bao = flt((so_bao or {}).get(stk))
		ra.append({
			"nguon": "nh:" + stk,
			"loai": LOAI_NH,
			"ten": "%s ···%s%s" % (ten_ngan_hang(r.get("bank") or ten), stk[-4:], " (tạm ứng)" if tam_ung else ""),
			"tam_ung": 1 if tam_ung else 0,
			"bank_account": ten,
			"dong_bo": 1 if stk in {chuoi(k) for k in ban_do} else 0,
			"so_bao": bao,
		})
	ra.sort(key=lambda x: (x["tam_ung"], -x["dong_bo"], x["ten"]))
	return ra


def nguon_tien_mat(cac_diem):
	"""Két của từng điểm bán đang bật, rồi quỹ công ty. THUẦN."""
	ra = []
	for d in cac_diem or ():
		ma = chuoi(d.get("ma")).upper()
		if not ma:
			continue
		ten = chuoi(d.get("ten_ngan") or d.get("ten") or ma)
		ra.append({"nguon": "tm:" + ma, "loai": LOAI_TM, "ten": "Két " + ten, "diem": ma,
			"co_quay": 1 if chuoi(d.get("quay")) else 0})
	ra.append({"nguon": NGUON_QUY, "loai": LOAI_TM, "ten": TEN_QUY, "diem": ""})
	return ra


def tong_tien(cac_dong):
	"""Cộng số dư các nguồn đã có số. THUẦN. Nguồn chưa chốt không cộng,
	nhưng được đếm để màn báo "còn N nguồn chưa chốt"."""
	nh = tm = tu = 0.0
	chua = 0
	for d in cac_dong or ():
		v = d.get("so_du")
		if v is None:
			chua += 1
			continue
		if d.get("loai") == LOAI_NH:
			nh += flt(v)
			if d.get("tam_ung"):
				tu += flt(v)
		else:
			tm += flt(v)
	return {"tong": round(nh + tm, 2), "ngan_hang": round(nh, 2), "tien_mat": round(tm, 2),
		"tam_ung": round(tu, 2), "chua_chot": chua}


def _gon(x):
	return re.sub(r"[^0-9A-Z]", "", chuoi(x).upper())


def cung_lenh(r, v):
	"""Hai vế có dấu vết của CÙNG một lệnh chuyển không. THUẦN.

	Codex #524: cùng ngày cùng số tiền chưa đủ. Site 31/10/2026 có 99 cặp
	như vậy từ 01/08, phần lớn là khách chuyển vào MB công ty và quỹ tạm ứng
	trả NCC đúng số đó. Bằng chứng nhận:
	- cùng mã tham chiếu ngân hàng (chuyển trong cùng MB, hai vế chung mã FT);
	- hai nội dung chung một đoạn liền dài ít nhất NGAN_NHAT_MO_TA ký tự sau
	  khi bỏ dấu cách và ký tự lạ (khác ngân hàng: bên nhận thêm tiền tố MBCT,
	  cắt bớt đuôi, thêm mã giao dịch, có khi gộp một dấu cách).
	Đo trên 99 cặp site: chuyển thật chung từ 25 ký tự trở lên, cặp khách và
	NCC trùng tiền chung nhiều nhất 13 (một cái tên người).
	"""
	a, b = _gon(r.get("tham_chieu")), _gon(v.get("tham_chieu"))
	if a and a == b:
		return True
	x, y = _gon(r.get("mo_ta")), _gon(v.get("mo_ta"))
	if len(x) < NGAN_NHAT_MO_TA or len(y) < NGAN_NHAT_MO_TA:
		return False
	m = SequenceMatcher(None, x, y, autojunk=False).find_longest_match(0, len(x), 0, len(y))
	return m.size >= NGAN_NHAT_MO_TA


def tach_noi_bo(cac_gd):
	"""Tách chuyển tiền nội bộ giữa các tài khoản của mình. THUẦN.

	Một khoản RA ở tài khoản A và một khoản VÀO ở tài khoản B khác A, cùng
	ngày, cùng số tiền VÀ có bằng chứng cùng lệnh (cung_lenh): đó là chuyển
	nội bộ (ví dụ MB công ty nạp quỹ tạm ứng OCB), không phải tiền vào hay ra
	của công ty. Cặp không có bằng chứng giữ nguyên là tiền vào, tiền ra.
	Ghép từng cặp một lần, khoản lớn ghép trước. Trả (ngoài, nội bộ).
	"""
	vao = [g for g in cac_gd if flt(g.get("vao")) > 0]
	ra = [g for g in cac_gd if flt(g.get("ra")) > 0]
	da = set()
	cap = []
	ra_sx = sorted(ra, key=lambda g: (-flt(g.get("ra")), str(g.get("ten"))))
	for r in ra_sx:
		for v in vao:
			if id(v) in da or id(r) in da:
				continue
			if chuoi(v.get("tk")) == chuoi(r.get("tk")):
				continue
			if str(v.get("ngay"))[:10] != str(r.get("ngay"))[:10]:
				continue
			if abs(flt(v.get("vao")) - flt(r.get("ra"))) >= 1:
				continue
			if not cung_lenh(r, v):
				continue
			da.add(id(v))
			da.add(id(r))
			cap.append((r, v))
			break
	ngoai = [g for g in cac_gd if id(g) not in da]
	noi_bo = [{"ngay": str(r.get("ngay"))[:10], "so": flt(r.get("ra")), "tu": r.get("tk"), "den": v.get("tk")}
		for r, v in cap]
	return ngoai, noi_bo


def chuoi_ngay(tu, den):
	"""Mọi ngày từ tu tới den (date), kể cả hai đầu. THUẦN."""
	d, ra = tu, []
	while d <= den:
		ra.append(d.isoformat())
		d += timedelta(days=1)
	return ra


def gom_ngay(cac_gd, tien_mat_vao, tien_mat_ra, tu, den):
	"""Tiền vào, tiền ra từng ngày. THUẦN.

	cac_gd        giao dịch ngân hàng ĐÃ bỏ chuyển nội bộ: {ngay, vao, ra}
	tien_mat_vao  {ngày: tiền mặt vào két} (bán, đặt bánh, nạp số dư)
	tien_mat_ra   {ngày: tiền mặt chi từ quỹ ghi sổ}
	"""
	ngay = chuoi_ngay(tu, den)
	o = {n: {"ngay": n, "vao_nh": 0.0, "ra_nh": 0.0, "vao_tm": 0.0, "ra_tm": 0.0} for n in ngay}
	for g in cac_gd or ():
		n = str(g.get("ngay"))[:10]
		if n in o:
			o[n]["vao_nh"] += flt(g.get("vao"))
			o[n]["ra_nh"] += flt(g.get("ra"))
	for n, v in (tien_mat_vao or {}).items():
		if str(n)[:10] in o:
			o[str(n)[:10]]["vao_tm"] += flt(v)
	for n, v in (tien_mat_ra or {}).items():
		if str(n)[:10] in o:
			o[str(n)[:10]]["ra_tm"] += flt(v)
	ds = []
	for n in ngay:
		x = o[n]
		x["vao"] = round(x["vao_nh"] + x["vao_tm"], 2)
		x["ra"] = round(x["ra_nh"] + x["ra_tm"], 2)
		x["rong"] = round(x["vao"] - x["ra"], 2)
		ds.append(x)
	return {
		"ngay": ds,
		"vao": round(sum(x["vao"] for x in ds), 2),
		"ra": round(sum(x["ra"] for x in ds), 2),
		"rong": round(sum(x["rong"] for x in ds), 2),
	}


def lon_nhat(cac_gd, so=8):
	"""Các khoản lớn nhất, vào và ra riêng. THUẦN."""
	vao = sorted([g for g in cac_gd if flt(g.get("vao")) > 0], key=lambda g: -flt(g.get("vao")))[:so]
	ra = sorted([g for g in cac_gd if flt(g.get("ra")) > 0], key=lambda g: -flt(g.get("ra")))[:so]
	gon = lambda g, k: {"ngay": str(g.get("ngay"))[:10], "so": flt(g.get(k)),
		"tk": g.get("ten_tk") or g.get("tk"), "mo_ta": chuoi(g.get("mo_ta"))[:90]}
	return {"vao": [gon(g, "vao") for g in vao], "ra": [gon(g, "ra") for g in ra]}


def nhom_tk(so_hieu):
	"""Số hiệu tài khoản -> nhóm của bảng lãi lỗ. THUẦN."""
	s = chuoi(so_hieu)
	for tien_to, nhom in (
		("511", "doanh_thu"), ("521", "giam_tru"), ("515", "dt_tai_chinh"), ("711", "thu_khac"),
		("632", "gia_von"), ("621", "cp_san_xuat"), ("622", "cp_san_xuat"), ("627", "cp_san_xuat"),
		("635", "cp_tai_chinh"), ("641", "cp_ban_hang"), ("642", "cp_quan_ly"),
		("811", "chi_khac"), ("821", "thue_tndn"),
	):
		if s.startswith(tien_to):
			return nhom
	return "khac"


def la_tk_nhan_vien(so_hieu):
	s = chuoi(so_hieu)
	return any(s.startswith(t) for t in TK_NHAN_VIEN)


def lai_lo(so_theo_tk):
	"""Bảng lãi lỗ một kỳ. THUẦN.

	so_theo_tk  [{so_hieu, loai ("Income"/"Expense"), co_tru_no}] với co_tru_no
	            = tổng Có trừ tổng Nợ của tài khoản trong kỳ.
	Doanh thu dương khi Có lớn hơn Nợ; chi phí dương khi Nợ lớn hơn Có.
	"""
	g = {}
	nv = 0.0
	khac_thu = khac_chi = 0.0
	for r in so_theo_tk or ():
		v = flt(r.get("co_tru_no"))
		n = nhom_tk(r.get("so_hieu"))
		if r.get("loai") == "Expense":
			v = -v
			if la_tk_nhan_vien(r.get("so_hieu")):
				nv += v
		if n == "khac":
			if r.get("loai") == "Income":
				khac_thu += v
			else:
				khac_chi += v
			continue
		g[n] = g.get(n, 0.0) + v
	dt = g.get("doanh_thu", 0.0) - g.get("giam_tru", 0.0)
	gv = g.get("gia_von", 0.0)
	lai_gop = dt - gv
	cp = g.get("cp_ban_hang", 0.0) + g.get("cp_quan_ly", 0.0) + g.get("cp_san_xuat", 0.0)
	tc = g.get("dt_tai_chinh", 0.0) - g.get("cp_tai_chinh", 0.0)
	khac = g.get("thu_khac", 0.0) + khac_thu - g.get("chi_khac", 0.0) - khac_chi
	truoc_thue = lai_gop - cp + tc + khac
	sau_thue = truoc_thue - g.get("thue_tndn", 0.0)
	tl = lambda a: ti_le(a, dt)
	return {
		"doanh_thu": round(g.get("doanh_thu", 0.0), 2), "giam_tru": round(g.get("giam_tru", 0.0), 2),
		"doanh_thu_thuan": round(dt, 2), "gia_von": round(gv, 2), "lai_gop": round(lai_gop, 2),
		"cp_ban_hang": round(g.get("cp_ban_hang", 0.0), 2), "cp_quan_ly": round(g.get("cp_quan_ly", 0.0), 2),
		"cp_san_xuat": round(g.get("cp_san_xuat", 0.0), 2), "tai_chinh": round(tc, 2), "khac": round(khac, 2),
		"truoc_thue": round(truoc_thue, 2), "thue_tndn": round(g.get("thue_tndn", 0.0), 2),
		"lai_rong": round(sau_thue, 2), "nhan_vien": round(nv, 2),
		"ti_le_lai_gop": tl(lai_gop), "ti_le_lai_rong": tl(sau_thue),
		"food_cost": tl(gv), "prime_cost": tl(gv + nv),
	}


def ti_le(tu, mau):
	"""Phần trăm, một chữ số lẻ. Mẫu <= 0 thì None (màn ghi "chưa có")."""
	if not mau or flt(mau) <= 0:
		return None
	return round(flt(tu) / flt(mau) * 100, 1)


def thang_truoc(thang):
	y, m = [int(x) for x in thang.split("-")]
	return "%04d-%02d" % ((y, m - 1) if m > 1 else (y - 1, 12))


def doc_thang(x, hom_nay):
	"""'2026-10' hoặc rỗng (tháng này). THUẦN. Tháng sau hôm nay thì về tháng này."""
	t = chuoi(x)
	m = re.match(r"^(\d{4})-(\d{1,2})$", t)
	ht = "%04d-%02d" % (hom_nay.year, hom_nay.month)
	if not m:
		return ht
	v = "%04d-%02d" % (int(m.group(1)), int(m.group(2)))
	if not 1 <= int(m.group(2)) <= 12 or v > ht:
		return ht
	return v


def khoang_thang(thang):
	y, m = [int(x) for x in thang.split("-")]
	dau = date(y, m, 1)
	cuoi = (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1))
	return dau, cuoi


def hao_hut(kiem_ke, da_dung, huy, doanh_thu_thuan):
	"""Tỉ lệ hao hụt trong tháng. THUẦN.

	kiem_ke  {kho: chênh lệch kiểm kê (âm là thiếu)} của phiếu kiểm kê định kỳ
	da_dung  {kho: giá trị nguyên liệu xuất dùng (sản xuất, xuất dùng)}
	huy      {kho: giá trị xuất huỷ}
	"""
	kho = sorted(set(kiem_ke or {}) | set(da_dung or {}) | set(huy or {}))
	dong = []
	thieu_tong = dung_tong = huy_tong = 0.0
	for k in kho:
		lech = flt((kiem_ke or {}).get(k))
		thieu = -lech if lech < 0 else 0.0
		dung = flt((da_dung or {}).get(k))
		h = flt((huy or {}).get(k))
		thieu_tong += thieu
		dung_tong += dung
		huy_tong += h
		tl = ti_le(thieu, dung)
		dong.append({"kho": k, "thieu": round(thieu, 2), "thua": round(lech if lech > 0 else 0.0, 2),
			"da_dung": round(dung, 2), "huy": round(h, 2), "ti_le_kiem_ke": tl,
			"bat_thuong": 1 if (tl is not None and tl > NGUONG_BAT_THUONG) or (thieu > 0 and dung <= 0) else 0})
	dong.sort(key=lambda d: -(d["thieu"] + d["huy"]))
	return {
		"dong": dong,
		"thieu": round(thieu_tong, 2), "da_dung": round(dung_tong, 2), "huy": round(huy_tong, 2),
		"ti_le_kiem_ke": ti_le(thieu_tong, dung_tong),
		"ti_le_huy": ti_le(huy_tong, doanh_thu_thuan),
	}


def tuan_den_han(han, hom_nay):
	"""Khoản đến hạn rơi vào cột nào của dự báo. THUẦN."""
	if not han:
		return "khong_han"
	d = han if isinstance(han, date) else doc_ngay(han)
	if d is None:
		return "khong_han"
	so = (d - hom_nay).days
	if so < 0:
		return "qua_han"
	if so > 29:
		return "sau_30"
	return "tuan_%d" % (so // 7 + 1)


COT_DU_BAO = ("qua_han", "tuan_1", "tuan_2", "tuan_3", "tuan_4", "tuan_5")
# Nguồn của dự báo có thể đọc hỏng, theo thứ tự hiện trên màn.
NGUON_DU_BAO = {"phai_thu": "Khách nợ mình", "ncc": "Nợ nhà cung cấp",
	"giu": "Hồ sơ thanh toán đang giữ hoá đơn"}


def du_bao(so_du, phai_thu, ncc, giu_boi_app, cho_chi, cho_duyet, hom_nay, thieu=()):
	"""Số dư dự kiến sau 30 ngày. THUẦN.

	ncc          [{name, han, con_no}] hoá đơn mua còn nợ
	giu_boi_app  {hoá đơn: số tiền hồ sơ thanh toán đang giữ}: phần này đã
	             nằm trong chờ chi hoặc chờ duyệt, trừ ra để không trừ hai lần
	thieu        khoá trong NGUON_DU_BAO đọc hỏng. Codex #524: nguồn hỏng
	             không được coi là 0; còn thiếu thì không kết luận cuối kỳ,
	             và ô của nguồn đó trả None để màn ghi "Chưa đọc được".
	"""
	cot = {k: 0.0 for k in COT_DU_BAO}
	sau = 0.0
	for r in ncc or ():
		con = flt(r.get("con_no")) - flt((giu_boi_app or {}).get(r.get("name")))
		if con <= 0:
			continue
		c = tuan_den_han(r.get("han"), hom_nay)
		if c == "tuan_5":
			c = "tuan_4"
		if c in cot:
			cot[c] += con
		elif c == "khong_han":
			cot["qua_han"] += con
		else:
			sau += con
	tra_ncc = sum(cot.values())
	thieu = [k for k in NGUON_DU_BAO if k in (thieu or ())]
	co_so = so_du is not None and not thieu
	cuoi = (flt(so_du) + flt(phai_thu) - tra_ncc - flt(cho_chi) - flt(cho_duyet)) if co_so else None
	hong_ncc = "ncc" in thieu or "giu" in thieu
	return {
		"so_du": so_du, "phai_thu": None if "phai_thu" in thieu else round(flt(phai_thu), 2),
		"tra_ncc": None if hong_ncc else round(tra_ncc, 2),
		"theo_tuan": None if hong_ncc else {k: round(v, 2) for k, v in cot.items() if k != "tuan_5"},
		"sau_30": None if hong_ncc else round(sau, 2), "cho_chi": round(flt(cho_chi), 2),
		"cho_duyet": round(flt(cho_duyet), 2),
		"cuoi_ky": round(cuoi, 2) if co_so else None,
		"cuoi_ky_khong_thu": round(cuoi - flt(phai_thu), 2) if co_so else None,
		"thieu": [NGUON_DU_BAO[k] for k in thieu],
	}


# ======================================================= phần chạm hệ

def _vai():
	return set(frappe.get_roles())


def _nguoi_xem():
	try:
		return doc_nguoi_xem(frappe.db.get_single_value(DT_CAI, "nguoi_xem"))
	except Exception:
		return []


def co_quyen(nguoi=None, vai=None):
	"""Cho cờ trên trang chủ (nhan_su.khoi_dong): không ném lỗi."""
	return duoc_xem(nguoi or frappe.session.user, vai if vai is not None else _vai(), _nguoi_xem())


def _kiem():
	if not co_quyen():
		frappe.throw("Phân hệ Tài chính chỉ mở cho Giám đốc và người Giám đốc chọn cho xem.",
			frappe.PermissionError)


def _la_giam_doc():
	return bool(_vai() & set(VAI_LUON_XEM))


def _sepay_so_bao():
	"""{số TK: số dư SePay báo}. Hỏng mạng thì rỗng, màn ghi "chưa đọc được"."""
	c = frappe.cache()
	k = "vgb_tc_sepay_so_du"
	try:
		v = c.get_value(k)
		if v:
			return json.loads(v)
	except Exception:
		pass
	ra = {}
	try:
		stg = frappe.get_doc("SePay Settings")
		tk = stg.get_password("api_token", raise_exception=False) or ""
		if not tk:
			return {}
		r = frappe.make_get_request("https://my.sepay.vn/userapi/bankaccounts/list",
			headers={"Authorization": "Bearer " + tk, "Content-Type": "application/json"})
		for a in (r or {}).get("bankaccounts") or []:
			ra[chuoi(a.get("account_number"))] = flt(a.get("accumulated"))
		c.set_value(k, json.dumps(ra), expires_in_sec=300)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tai_chinh: doc so du SePay")
		return {}
	return ra


def _ban_do_sepay():
	try:
		v = frappe.db.get_single_value("SePay Settings", "account_map") or "{}"
		d = json.loads(v) if isinstance(v, str) else (v or {})
		return {chuoi(k): chuoi(x) for k, x in (d or {}).items()}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tai_chinh: doc account_map SePay")
		return {}


def _cac_nguon(so_bao=None):
	from vagabond import diem_ban
	ban_do = _ban_do_sepay()
	tk = frappe.get_all("Bank Account",
		filters=[["name", "in", list(ban_do.values()) or [""]]],
		or_filters=None, fields=["name", "account", "bank", "bank_account_no", "is_company_account"],
		limit_page_length=0)
	tk += frappe.get_all("Bank Account", filters={"is_company_account": 1},
		fields=["name", "account", "bank", "bank_account_no", "is_company_account"], limit_page_length=0)
	nh = nguon_ngan_hang(ban_do, tk, so_bao if so_bao is not None else {})
	tm = nguon_tien_mat(diem_ban.ds(chi_bat=True))
	return nh + tm


def _cac_moc():
	return frappe.get_all(DT_MOC, fields=["name", "nguon", "ten_nguon", "loai", "ngay_chot", "so_du",
		"ghi_chu", "nguoi", "luc"], order_by="ngay_chot desc, luc desc", limit_page_length=0)


def _phat_sinh_nh(bank_account, sau_ngay):
	r = frappe.db.sql("""select coalesce(sum(deposit),0), coalesce(sum(withdrawal),0), count(*)
		from `tabBank Transaction` where docstatus=1 and bank_account=%s and date>%s""",
		(bank_account, str(sau_ngay)))
	return flt(r[0][0]), flt(r[0][1]), cint(r[0][2])


def _tien_mat_vao_ket(diem, tu_ngay, den_luc=None):
	"""Tiền mặt vào két từ đầu ngày tu_ngay tới den_luc. Đúng phép màn Chốt ca."""
	from vagabond import ca_quay
	pt, _ = ca_quay._doanh_thu_he_thong(diem, "%s 00:00:00" % tu_ngay, den_luc or str(now_datetime()))
	return flt((pt or {}).get(TIEN_MAT))


def _nop_quy(diem=None, trang_thai=("Đã nộp quỹ",), sau_ngay=None, theo="giao"):
	"""Tổng tiền phiếu nộp quỹ. theo="giao" lấy lúc két giao tiền, "nhan" lúc
	quỹ ký nhận."""
	cot = "coalesce(giao_luc, nhan_luc, ngay)" if theo == "giao" else "coalesce(nhan_luc, giao_luc, ngay)"
	dk = ["trang_thai in %(tt)s"]
	ts = {"tt": tuple(trang_thai)}
	if diem is not None:
		dk.append("diem_ban=%(d)s")
		ts["d"] = diem
	if sau_ngay is not None:
		dk.append("date(%s) > %%(n)s" % cot)
		ts["n"] = str(sau_ngay)
	r = frappe.db.sql("select coalesce(sum(coalesce(nullif(tong_thuc_nhan,0), tien_ky_vong, 0)),0), count(*) "
		"from `tabVagabond Nop Quy` where " + " and ".join(dk), ts)
	return flt(r[0][0]), cint(r[0][1])


def _so_cai_quy(sau_ngay):
	"""Phát sinh sổ cái tiền mặt 111x ngoài hoá đơn bán (chi, thu bằng bút toán)."""
	r = frappe.db.sql("""select coalesce(sum(g.debit),0), coalesce(sum(g.credit),0) from `tabGL Entry` g
		join `tabAccount` a on a.name=g.account
		where g.is_cancelled=0 and a.account_number like '111%%' and g.posting_date>%s
		and g.voucher_type not in ('Sales Invoice','POS Invoice')""", (str(sau_ngay),))
	return flt(r[0][0]), flt(r[0][1])


def _ca_gan_nhat(diem):
	r = frappe.get_all("Vagabond Ca Quay", filters={"quay": diem, "trang_thai": ["!=", "Đang mở"]},
		fields=["name", "chot_luc", "tien_mat_dem"], order_by="chot_luc desc", limit_page_length=1)
	return r[0] if r else None


def _tinh_tien():
	so_bao = _sepay_so_bao()
	nguon = _cac_nguon(so_bao)
	moc = moc_moi_nhat(_cac_moc())
	hom = getdate(nowdate())
	dong = []
	for n in nguon:
		m = moc.get(n["nguon"])
		d = dict(n, moc=None, vao=0.0, ra=0.0, so_du=None, ghi=[], doi_chieu=None)
		if m:
			d["moc"] = {"ngay_chot": str(m.get("ngay_chot")), "so_du": flt(m.get("so_du")),
				"nguoi": m.get("nguoi"), "luc": str(m.get("luc") or "")}
		try:
			if n["loai"] == LOAI_NH:
				if not n["dong_bo"] and n["so_bao"] > 0:
					# Không đồng bộ giao dịch về app, SePay báo số dư: lấy luôn.
					d["so_du"] = n["so_bao"]
					d["ghi"].append("Số dư SePay báo")
				elif m:
					vao, ra, so_gd = _phat_sinh_nh(n["bank_account"], m["ngay_chot"])
					d.update(vao=vao, ra=ra, so_gd=so_gd)
					d["so_du"] = so_du_tu_moc(m, vao, ra)
					d["doi_chieu"] = doi_chieu(d["so_du"], n["so_bao"])
				if n["dong_bo"] and not m:
					d["ghi"].append("Chưa chốt số dư đầu")
				if not n["dong_bo"] and n["so_bao"] <= 0 and not m:
					d["ghi"].append("Chưa nối SePay, cần chốt tay")
			elif n["nguon"] == NGUON_QUY:
				if m:
					vao_nq, so_nq = _nop_quy(sau_ngay=m["ngay_chot"], theo="nhan")
					no, co = _so_cai_quy(m["ngay_chot"])
					d.update(vao=vao_nq + no, ra=co, so_phieu=so_nq)
					d["so_du"] = so_du_tu_moc(m, vao_nq + no, co)
				else:
					d["ghi"].append("Chưa chốt số dư đầu")
			else:
				ca = None
				try:
					ca = _ca_gan_nhat(n["diem"])
				except Exception:
					pass
				if ca:
					d["ca"] = {"luc": str(ca.get("chot_luc") or ""), "dem": flt(ca.get("tien_mat_dem"))}
				if m:
					tu = getdate(m["ngay_chot"]) + timedelta(days=1)
					vao = _tien_mat_vao_ket(n["diem"], tu.isoformat()) if tu <= hom else 0.0
					ra_nq, _ = _nop_quy(diem=n["diem"], trang_thai=("Đã nộp quỹ", "Chờ ký nhận"),
						sau_ngay=m["ngay_chot"], theo="giao")
					d.update(vao=vao, ra=ra_nq)
					d["so_du"] = so_du_tu_moc(m, vao, ra_nq)
				else:
					d["ghi"].append("Chưa chốt số dư đầu")
		except Exception:
			frappe.log_error(frappe.get_traceback(), "tai_chinh: tinh nguon %s" % n["nguon"])
			d["ghi"].append("Chưa tính được, báo kỹ thuật")
			d["so_du"] = None
		dong.append(d)
	# Tiền két đã giao, quỹ chưa ký nhận: đã trừ khỏi két, chưa cộng vào quỹ.
	try:
		dang, so_dang = _nop_quy(trang_thai=("Chờ ký nhận",))
	except Exception:
		dang, so_dang = 0.0, 0
	if dang:
		dong.append({"nguon": "tm:DANG", "loai": LOAI_TM, "ten": "Đang nộp về quỹ (chờ ký nhận)",
			"so_du": dang, "so_phieu": so_dang, "ghi": ["%d phiếu nộp quỹ chờ ký nhận" % so_dang], "dang_chuyen": 1})
	return {"dong": dong, "tong": tong_tien(dong), "luc": str(now_datetime())[:16],
		"sepay_doc_duoc": 1 if so_bao else 0}


@frappe.whitelist()
def tien_hien_co():
	"""Màn Tiền hiện có: từng tài khoản, từng két, quỹ công ty."""
	_kiem()
	return _tinh_tien()


def _gd_ngan_hang(tu, den, cac_nh):
	ten = {n["bank_account"]: n["ten"] for n in cac_nh if n.get("dong_bo")}
	if not ten:
		return []
	r = frappe.db.sql("""select name, date, bank_account, deposit, withdrawal, description, reference_number
		from `tabBank Transaction` where docstatus=1 and date between %s and %s and bank_account in %s""",
		(str(tu), str(den), tuple(ten)), as_dict=1)
	return [{"ten": x.name, "ngay": str(x.date), "tk": x.bank_account, "ten_tk": ten.get(x.bank_account),
		"vao": flt(x.deposit), "ra": flt(x.withdrawal), "mo_ta": x.description,
		"tham_chieu": x.reference_number} for x in r]


def _tien_mat_theo_ngay(tu, den, cac_tm):
	"""{ngày: tiền mặt vào các két}. Mỗi ngày mỗi điểm một lượt phép Chốt ca."""
	c = frappe.cache()
	ra = {}
	for n in chuoi_ngay(tu, den):
		k = "vgb_tc_tm_%s" % n
		v = None
		hom = n == nowdate()
		if not hom:
			try:
				v = c.get_value(k)
			except Exception:
				v = None
		if v is None:
			s = 0.0
			for d in cac_tm:
				if not d.get("diem"):
					continue
				try:
					s += _tien_mat_vao_ket(d["diem"], n, "%s 23:59:59" % n)
				except Exception:
					frappe.log_error(frappe.get_traceback(), "tai_chinh: tien mat %s %s" % (d["diem"], n))
			v = s
			if not hom:
				try:
					c.set_value(k, v, expires_in_sec=1800)
				except Exception:
					pass
		ra[n] = flt(v)
	return ra


def _chi_quy_theo_ngay(tu, den):
	r = frappe.db.sql("""select g.posting_date, sum(g.credit) from `tabGL Entry` g
		join `tabAccount` a on a.name=g.account
		where g.is_cancelled=0 and a.account_number like '111%%' and g.posting_date between %s and %s
		and g.voucher_type not in ('Sales Invoice','POS Invoice') group by g.posting_date""", (str(tu), str(den)))
	return {str(x[0]): flt(x[1]) for x in r}


@frappe.whitelist()
def dong_tien(so_ngay=30):
	"""Màn Dòng tiền: tiền vào, tiền ra từng ngày, bỏ chuyển nội bộ."""
	_kiem()
	n = cint(so_ngay) if cint(so_ngay) in KY_DONG_TIEN else 30
	den = getdate(nowdate())
	tu = den - timedelta(days=n - 1)
	nguon = _cac_nguon({})
	nh = [x for x in nguon if x["loai"] == LOAI_NH]
	tm = [x for x in nguon if x["loai"] == LOAI_TM]
	gd = _gd_ngan_hang(tu, den, nh)
	ngoai, noi_bo = tach_noi_bo(gd)
	kq = gom_ngay(ngoai, _tien_mat_theo_ngay(tu, den, tm), _chi_quy_theo_ngay(tu, den), tu, den)
	kq.update(so_ngay=n, tu=str(tu), den=str(den), lon_nhat=lon_nhat(ngoai),
		noi_bo={"so": len(noi_bo), "tien": round(sum(x["so"] for x in noi_bo), 2)})
	return kq


def _gl_ky(tu, den):
	r = frappe.db.sql("""select a.account_number, a.root_type, sum(g.credit)-sum(g.debit)
		from `tabGL Entry` g join `tabAccount` a on a.name=g.account
		where g.is_cancelled=0 and a.root_type in ('Income','Expense') and g.posting_date between %s and %s
		group by a.account_number, a.root_type""", (str(tu), str(den)))
	return [{"so_hieu": x[0], "loai": x[1], "co_tru_no": flt(x[2])} for x in r]


@frappe.whitelist()
def lai_lo_thang(thang=""):
	"""Màn Lãi lỗ tháng, kèm tháng trước để so."""
	_kiem()
	hom = getdate(nowdate())
	t = doc_thang(thang, hom)
	tt = thang_truoc(t)
	tu, den = khoang_thang(t)
	tu2, den2 = khoang_thang(tt)
	return {"thang": t, "thang_truoc": tt, "dang_chay": 1 if den >= hom else 0,
		"ky": lai_lo(_gl_ky(tu, min(den, hom))), "ky_truoc": lai_lo(_gl_ky(tu2, den2))}


def _hao_hut_so(tu, den):
	kk = frappe.db.sql("""select i.warehouse, sum(i.amount_difference) from `tabStock Reconciliation Item` i
		join `tabStock Reconciliation` s on s.name=i.parent
		where s.docstatus=1 and s.purpose='Stock Reconciliation' and s.posting_date between %s and %s
		group by i.warehouse""", (str(tu), str(den)))
	dung = frappe.db.sql("""select d.s_warehouse, sum(d.basic_amount) from `tabStock Entry Detail` d
		join `tabStock Entry` e on e.name=d.parent
		where e.docstatus=1 and e.posting_date between %s and %s and d.s_warehouse is not null and d.s_warehouse!=''
		and (e.purpose='Manufacture' or (e.purpose='Material Issue' and coalesce(e.vgb_ly_do_huy,'')=''))
		group by d.s_warehouse""", (str(tu), str(den)))
	huy = frappe.db.sql("""select d.s_warehouse, sum(d.basic_amount) from `tabStock Entry Detail` d
		join `tabStock Entry` e on e.name=d.parent
		where e.docstatus=1 and e.posting_date between %s and %s and e.purpose='Material Issue'
		and coalesce(e.vgb_ly_do_huy,'')!='' group by d.s_warehouse""", (str(tu), str(den)))
	return {x[0]: flt(x[1]) for x in kk}, {x[0]: flt(x[1]) for x in dung}, {x[0]: flt(x[1]) for x in huy}


@frappe.whitelist()
def ti_le_thang(thang=""):
	"""Màn Tỉ lệ giá vốn và hao hụt."""
	_kiem()
	hom = getdate(nowdate())
	t = doc_thang(thang, hom)
	tu, den = khoang_thang(t)
	den = min(den, hom)
	ll = lai_lo(_gl_ky(tu, den))
	kk, dung, huy = _hao_hut_so(tu, den)
	hh = hao_hut(kk, dung, huy, ll["doanh_thu_thuan"])
	return {"thang": t, "dang_chay": 1 if khoang_thang(t)[1] >= hom else 0,
		"doanh_thu_thuan": ll["doanh_thu_thuan"], "gia_von": ll["gia_von"], "nhan_vien": ll["nhan_vien"],
		"food_cost": ll["food_cost"], "prime_cost": ll["prime_cost"], "hao_hut": hh}


def _phai_thu():
	from vagabond import cong_no
	return flt((cong_no.ds_khach_no() or {}).get("tong"))


def _ncc():
	from vagabond import cong_no_ncc
	kq = cong_no_ncc._ket_qua(trang_thai="con_no")
	return kq.get("dong") or [], flt((kq.get("tong_theo_tien") or {}).get("VND")), \
		flt((kq.get("qua_han_theo_tien") or {}).get("VND"))


def _cho_chi():
	r = frappe.db.sql("""select trang_thai, count(*), coalesce(sum(greatest(coalesce(con_lai,0)-coalesce(da_tra,0),0)),0)
		from `tabVagabond Ho So TT` where trang_thai in ('Da duyet','Cho ke toan','Cho giam doc')
		group by trang_thai""")
	o = {x[0]: (cint(x[1]), flt(x[2])) for x in r}
	cd = o.get("Da duyet", (0, 0.0))
	cy = (o.get("Cho ke toan", (0, 0.0))[0] + o.get("Cho giam doc", (0, 0.0))[0],
		o.get("Cho ke toan", (0, 0.0))[1] + o.get("Cho giam doc", (0, 0.0))[1])
	return {"so": cd[0], "tien": round(cd[1], 2), "so_cho_duyet": cy[0], "tien_cho_duyet": round(cy[1], 2)}


def _tra_truoc():
	from vagabond import tra_truoc_khach
	ds = (tra_truoc_khach.ds() or {}).get("khach") or []
	return round(sum(flt(x.get("con_chua_can")) for x in ds), 2), len([x for x in ds if flt(x.get("con_chua_can")) > 0])


def _giu_boi_app():
	"""{hoá đơn mua: số tiền hồ sơ thanh toán đang giữ}."""
	from vagabond import ho_so_tt
	return {k: flt(v.get("so_tien")) for k, v in (ho_so_tt._hd_ho_so_giu() or {}).items()}


@frappe.whitelist()
def du_bao_30():
	"""Màn Dự báo 30 ngày."""
	_kiem()
	hom = getdate(nowdate())
	tien = _tinh_tien()
	so_du = tien["tong"]["tong"] if any(d.get("so_du") is not None for d in tien["dong"]) else None
	thieu = []
	pt, dong, giu = 0.0, [], {}
	try:
		pt = _phai_thu()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tai_chinh: phai thu")
		thieu.append("phai_thu")
	try:
		dong, _, _ = _ncc()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tai_chinh: phai tra")
		thieu.append("ncc")
	try:
		giu = _giu_boi_app()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tai_chinh: hoa don ho so giu")
		thieu.append("giu")
	cc = _cho_chi()
	ncc = [{"name": r.get("name"), "han": r.get("han"), "con_no": r.get("con_no")} for r in dong
		if r.get("account_currency") in (None, "", "VND")]
	kq = du_bao(so_du, pt, ncc, giu, cc["tien"], cc["tien_cho_duyet"], hom, thieu=thieu)
	kq.update(chua_chot=tien["tong"]["chua_chot"], hom_nay=str(hom))
	return kq


def _phan(ham, *a):
	try:
		return {"ok": 1, "v": ham(*a)}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "tai_chinh: tong quan %s" % getattr(ham, "__name__", ""))
		return {"ok": 0, "loi": chuoi(e)[:160] or "Chưa đọc được"}


@frappe.whitelist()
def tong_quan():
	"""Một lượt cho màn Tổng quan: số trên từng thẻ. Phần nào hỏng chỉ thẻ
	đó báo, các thẻ khác vẫn lên."""
	_kiem()
	hom = getdate(nowdate())
	t = doc_thang("", hom)

	def tien():
		k = _tinh_tien()
		return k["tong"]

	def dong7():
		k = dong_tien(7)
		return {"vao": k["vao"], "ra": k["ra"], "rong": k["rong"]}

	def ll():
		tu, den = khoang_thang(t)
		x = lai_lo(_gl_ky(tu, min(den, hom)))
		return {"lai_rong": x["lai_rong"], "ti_le_lai_rong": x["ti_le_lai_rong"], "food_cost": x["food_cost"],
			"doanh_thu_thuan": x["doanh_thu_thuan"]}

	def ptra():
		_, tong, qh = _ncc()
		return {"tong": tong, "qua_han": qh}

	def tt():
		tien_tt, so = _tra_truoc()
		return {"tong": tien_tt, "so_khach": so}

	return {"thang": t, "tien": _phan(tien), "dong7": _phan(dong7), "lai_lo": _phan(ll),
		"phai_thu": _phan(_phai_thu), "phai_tra": _phan(ptra), "cho_chi": _phan(_cho_chi),
		"tra_truoc": _phan(tt), "la_giam_doc": 1 if _la_giam_doc() else 0}


@frappe.whitelist()
def cai_dat():
	"""Màn Cài đặt Tài chính: mốc chốt từng nguồn, lịch sử, người được xem."""
	_kiem()
	nguon = _cac_nguon(_sepay_so_bao())
	moc = _cac_moc()
	theo = {}
	for m in moc:
		theo.setdefault(m["nguon"], [])
		if len(theo[m["nguon"]]) < 5:
			theo[m["nguon"]].append({"ngay_chot": str(m["ngay_chot"]), "so_du": flt(m["so_du"]),
				"ghi_chu": m.get("ghi_chu") or "", "nguoi": m.get("nguoi") or "", "luc": str(m.get("luc") or "")[:16]})
	ds = [dict(n, lich_su=theo.get(n["nguon"], [])) for n in nguon]
	ra = {"nguon": ds, "la_giam_doc": 1 if _la_giam_doc() else 0, "hom_nay": nowdate()}
	if ra["la_giam_doc"]:
		xem = _nguoi_xem()
		nd = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User", "name": ["not in", ["Guest"]]},
			fields=["name", "full_name"], order_by="full_name asc", limit_page_length=300)
		ra["nguoi_dung"] = [{"email": u.name, "ten": u.full_name or u.name, "chon": 1 if u.name.lower() in
			[x.lower() for x in xem] else 0} for u in nd]
	return ra


@frappe.whitelist(methods=["POST"])
def luu_moc(nguon=None, ngay_chot=None, so_du=None, ghi_chu=""):
	"""Thêm một mốc chốt số dư. Không sửa mốc cũ: chốt lại là thêm mốc mới."""
	_kiem()
	nguon_ds = {n["nguon"]: n for n in _cac_nguon({})}
	ngay = doc_ngay(ngay_chot)
	so = doc_so_tien(so_du)
	loi = kiem_moc(nguon, ngay, so, nguon_ds, getdate(nowdate()))
	if loi:
		frappe.throw(loi)
	n = nguon_ds[chuoi(nguon)]
	doc = frappe.get_doc({"doctype": DT_MOC, "nguon": n["nguon"], "ten_nguon": n["ten"], "loai": n["loai"],
		"ngay_chot": str(ngay), "so_du": so, "ghi_chu": chuoi(ghi_chu)[:500],
		"nguoi": frappe.session.user, "luc": now_datetime()})
	doc.insert(ignore_permissions=True)
	return {"ok": 1, "name": doc.name}


@frappe.whitelist(methods=["POST"])
def luu_nguoi_xem(ds=None):
	"""Giám đốc chọn ai được xem phân hệ Tài chính."""
	_kiem()
	if not _la_giam_doc():
		frappe.throw("Chỉ Giám đốc chọn được người xem Tài chính.", frappe.PermissionError)
	if isinstance(ds, str):
		try:
			ds = json.loads(ds)
		except Exception:
			ds = doc_nguoi_xem(ds)
	ds = doc_nguoi_xem("\n".join(chuoi(x) for x in (ds or [])))
	co = set(frappe.get_all("User", filters={"name": ["in", ds or [""]], "enabled": 1}, pluck="name"))
	sach = [x for x in ds if x in co or x.lower() in {c.lower() for c in co}]
	frappe.db.set_single_value(DT_CAI, "nguoi_xem", "\n".join(sach))
	return {"ok": 1, "nguoi_xem": sach}
