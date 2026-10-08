# -*- coding: utf-8 -*-
"""#420 v579: hiểu từng mẫu báo cáo vendor, trả dòng chuẩn để đối soát.

Đầu vào là kết quả của doi_soat_doc.doc_tep (trang lưới ô hoặc dòng chữ
PDF). Mỗi mẫu có hai việc: nhận ra tệp của mình (nhan) và đọc (doc). Không
mẫu nào được đoán: thiếu cột, sai phương trình, sai tổng là lỗi có lý do,
dòng lỗi vẫn giữ để kế toán xem.

Đặc tả từng nguồn (đã khảo sát trên mẫu thật trong Drive ngày 06/10/2026)
nằm ở docs/doi-soat-vendor/schema/. Những điều đặc tả chốt:
- Tiền Payoo trong bản CSV gốc là "1900000.000" (ba số lẻ); bản đã chuyển qua
  Google Sheets thành "1.900.000.000". Cả hai đều là 1.900.000 đồng.
- ShopeeFood ghi tiền theo NGHÌN đồng có ba số lẻ (82.488 = 82.488 đồng).
- OnePay, Shinhan, Xanh SM, Be, Grab ghi đồng nguyên.
- Phí OnePay: chỉ lấy Total fee, Fix fee nằm sẵn trong đó.
- Phí Shinhan MDF đã gồm VAT; không trừ VAT lần nữa.

Dòng chuẩn (mọi số tiền là int đồng):
  ma_su_kien  căn cước ổn định trong phạm vi vendor + tài khoản
  merchant    điểm chấp nhận / cửa hàng phía vendor
  diem_ban    mã điểm bán của tiệm (TCV, SALES, NVHTN) hoặc "" nếu chưa rõ
  ngay, gio   ngày ISO, giờ "HH:MM:SS" hoặc ""
  ngay_tien_ve  ngày vendor trả tiền (ISO) hoặc ""
  loai        ban | hoan | dieu_chinh | phi_ky   (nhóm tiền bán)
              chuyen | phi_quan_ly | dieu_chinh   (nhóm chuyến đi)
              phat_sinh | phi | lai | thanh_toan | hoan   (nhóm thẻ tín dụng)
  ma_don      mã đơn phía vendor (giữ số 0 đầu)
  ma_tham_chieu  mã để tìm hoá đơn bán (RRN, mã chuẩn chi, mã đơn sàn)
  ma_can_cu   căn cứ cho dòng điều chỉnh / phí kỳ
  tien_hang, giam_gia, phi, dieu_chinh, thuc_nhan, thue
  mo_ta       chữ ngắn, không chứa dữ liệu cá nhân
"""

# phần thuần
import re
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

PHIEN_BAN = "v579.1"


class LoiDong(ValueError):
	"""Lỗi của một dòng; dòng vẫn được giữ cùng lý do."""


class LoiMau(ValueError):
	"""Tệp nhận ra là của mẫu này nhưng không đọc tiếp được."""


# ------------------------------------------------------------ chuẩn hoá chữ

_DAU = str.maketrans({"đ": "d", "Đ": "d"})


def khong_dau(s):
	s = unicodedata.normalize("NFD", str(s if s is not None else "")).translate(_DAU)
	return "".join(c for c in s if unicodedata.category(c) != "Mn")


def chuan(s):
	"""Chữ để so: bỏ dấu, thường, gộp mọi khoảng trắng và xuống dòng."""
	s = khong_dau(s).lower()
	s = re.sub(r"[^a-z0-9%/()+=.\-]+", " ", s)
	return re.sub(r"\s+", " ", s).strip()


def chu(v):
	"""Ô thành chữ, giữ nguyên số 0 đầu; số nguyên trong Excel bỏ ".0"."""
	if v is None:
		return ""
	if isinstance(v, float) and v.is_integer():
		return str(int(v))
	if isinstance(v, datetime):
		return v.strftime("%d/%m/%Y %H:%M:%S")
	if isinstance(v, date):
		return v.strftime("%d/%m/%Y")
	return unicodedata.normalize("NFC", str(v)).strip()


def rong(v):
	return chu(v) == ""


# ------------------------------------------------------------ tiền

def _so(v):
	if isinstance(v, bool):
		raise LoiDong("Ô tiền là đúng/sai, không phải số.")
	if isinstance(v, int):
		return Decimal(v)
	if isinstance(v, float):
		# Excel lưu nhị phân; làm tròn 6 số lẻ để 1179999.9999999 thành đúng.
		return Decimal(repr(v)).quantize(Decimal("0.000001"))
	if isinstance(v, Decimal):
		return v
	return None


def _dong_nguyen(so, ten):
	q = so.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
	if q != so:
		raise LoiDong("%s có số lẻ đồng (%s); kiểm đơn vị trên tệp gốc." % (ten, so))
	if abs(q) > Decimal("100000000000"):
		raise LoiDong("%s quá lớn (%s); kiểm đơn vị trên tệp gốc." % (ten, so))
	return int(q)


def tien_vi(v, ten="Số tiền", cho_rong=False):
	"""Đồng, kiểu Việt: 1.180.000 hoặc 1.180.000,00; ô số giữ nguyên."""
	so = _so(v)
	if so is None:
		s = chu(v).replace("VND", "").replace("VNĐ", "").replace("đ", "").replace(" ", "")
		if s == "" or s == "-":
			if cho_rong:
				return 0
			raise LoiDong("Thiếu %s." % ten)
		if not re.fullmatch(r"-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,6})?", s):
			raise LoiDong("%s sai dạng (%s); không đoán." % (ten, s))
		so = Decimal(s.replace(".", "").replace(",", "."))
	return _dong_nguyen(so, ten)


def tien_en(v, ten="Số tiền", cho_rong=False):
	"""Đồng, kiểu Anh: 65,000 hoặc 65,000.00; ô số giữ nguyên."""
	so = _so(v)
	if so is None:
		s = chu(v).replace("VND", "").replace(" ", "")
		if s == "" or s == "-":
			if cho_rong:
				return 0
			raise LoiDong("Thiếu %s." % ten)
		if s.startswith("(") and s.endswith(")"):
			s = "-" + s[1:-1]
		if not re.fullmatch(r"-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,6})?", s):
			raise LoiDong("%s sai dạng (%s); không đoán." % (ten, s))
		so = Decimal(s.replace(",", ""))
	return _dong_nguyen(so, ten)


def tien_payoo(v, ten="Số tiền", cho_rong=False):
	"""Payoo: CSV gốc "1900000.000" hoặc bản Google Sheets "1.900.000.000".

	Bản Sheets là do máy Google đọc dấu chấm thập phân thành dấu nghìn, nên
	số hiện ra gấp 1.000 lần và luôn tận cùng ".000". Chỉ nhận đúng hai hình
	dạng đó; ô số (Excel) thì không biết đã qua Sheets hay chưa nên báo lỗi
	thay vì đoán.
	"""
	s = chu(v).replace(" ", "")
	if s in ("", "-"):
		if cho_rong:
			return 0
		raise LoiDong("Thiếu %s." % ten)
	if s in ("0", "0.000", "0.0"):
		return 0
	if not isinstance(v, str):
		raise LoiDong("%s là ô số Excel; tải tệp CSV gốc Payoo gửi qua email." % ten)
	if re.fullmatch(r"-?\d+\.\d{1,3}", s) or re.fullmatch(r"-?\d+", s):
		return _dong_nguyen(Decimal(s), ten)
	if re.fullmatch(r"-?\d{1,3}(?:\.\d{3}){2,}", s) and s.endswith(".000"):
		return _dong_nguyen(Decimal(s.replace(".", "")) / 1000, ten)
	raise LoiDong("%s sai dạng Payoo (%s); tải tệp CSV gốc từ email." % (ten, s))


def tien_nghin(v, ten="Số tiền", cho_rong=False):
	"""ShopeeFood: số theo nghìn đồng, tối đa ba số lẻ (82.488 = 82.488 đồng).

	Ô số Excel giữ nguyên giá trị; ô chữ chỉ nhận dấu chấm thập phân hoặc
	dấu phẩy thập phân (bản Sheets tiếng Việt), không nhận dấu nghìn.
	"""
	so = _so(v)
	if so is None:
		s = chu(v).replace(" ", "")
		if s in ("", "-"):
			if cho_rong:
				return 0
			raise LoiDong("Thiếu %s." % ten)
		if re.fullmatch(r"-?\d+(?:[.,]\d{1,3})?", s):
			so = Decimal(s.replace(",", "."))
		else:
			raise LoiDong("%s sai dạng nghìn đồng (%s); không đoán." % (ten, s))
	return _dong_nguyen((so * 1000).quantize(Decimal("0.001")), ten)


def ti_le(v):
	"""Tỷ lệ phí "2,40%" hoặc "1.440" (phần trăm) thành Decimal phần trăm."""
	s = chu(v).replace("%", "").replace(" ", "").replace(",", ".")
	try:
		return Decimal(s)
	except InvalidOperation:
		raise LoiDong("Tỷ lệ phí sai dạng (%s)." % s) from None


# ------------------------------------------------------------ ngày giờ

def ngay_gio(v, ten="Ngày"):
	"""Trả (ngày ISO, "HH:MM:SS"). Nhận datetime, dd/mm/yyyy[ hh:mm[:ss]],
	dd-mm-yyyy, HH:MM:SS dd-mm-yyyy, yyyymmdd, dd/mm/yy, yyyy-mm-dd."""
	if isinstance(v, datetime):
		return v.date().isoformat(), v.strftime("%H:%M:%S") if (v.hour or v.minute or v.second) else ""
	if isinstance(v, date):
		return v.isoformat(), ""
	if isinstance(v, (int, float)) and not isinstance(v, bool) and 20000 < v < 80000:
		# Số ngày kiểu Excel (Google Sheets xuất ô ngày giờ thành số).
		dt = datetime(1899, 12, 30) + timedelta(seconds=round(float(v) * 86400))
		return dt.date().isoformat(), dt.strftime("%H:%M:%S")
	s = chu(v)
	m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?\s+(\d{1,2})[-/](\d{1,2})[-/](\d{4})", s)
	if m:
		hh, mi, ss, d, mo, y = m.groups()
		return _iso(y, mo, d, ten), "%02d:%s:%s" % (int(hh), mi, ss or "00")
	m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})(?:,?\s+(\d{1,2}):(\d{2})(?::(\d{2}))?)?", s)
	if m:
		d, mo, y, hh, mi, ss = m.groups()
		if len(y) == 2:
			y = "20" + y
		return _iso(y, mo, d, ten), ("%02d:%s:%s" % (int(hh), mi, ss or "00")) if hh else ""
	m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?", s)
	if m:
		y, mo, d, hh, mi, ss = m.groups()
		return _iso(y, mo, d, ten), ("%s:%s:%s" % (hh, mi, ss or "00")) if hh else ""
	m = re.fullmatch(r"(\d{4})(\d{2})(\d{2})", s)
	if m:
		y, mo, d = m.groups()
		return _iso(y, mo, d, ten), ""
	raise LoiDong("%s sai dạng (%s)." % (ten, s or "trống"))


def _iso(y, mo, d, ten):
	try:
		return date(int(y), int(mo), int(d)).isoformat()
	except ValueError:
		raise LoiDong("%s không tồn tại (%s/%s/%s)." % (ten, d, mo, y)) from None


def ngay(v, ten="Ngày"):
	return ngay_gio(v, ten)[0]


# ------------------------------------------------------------ lưới ô

def tim_tieu_de(o, can, toi_da=60):
	"""Tìm dòng tiêu đề chứa đủ các tên cột cần (đã chuẩn hoá, so "chứa").

	Trả (chỉ số dòng, {khoá: chỉ số cột}). can là {khoá: [tên chuẩn, ...]}.
	Một ô có nhiều dòng (tiếng Việt\\ntiếng Anh) được so từng phần lẫn cả ô.
	"""
	for r, hang in enumerate(o[:toi_da]):
		o_chuan = [chuan(v) for v in hang]
		cot = {}
		for khoa, ten_ds in can.items():
			for c, s in enumerate(o_chuan):
				if not s or c in cot.values():
					continue
				phan = [chuan(p) for p in chu(hang[c]).split("\n")] + [s]
				if any(t == p or (len(t) > 6 and t in p) for t in ten_ds for p in phan if p):
					cot[khoa] = c
					break
		if len(cot) == len(can):
			return r, cot
	return None, None


def o_tai(hang, c):
	return hang[c] if c is not None and c < len(hang) else None


def dong_trong(hang):
	return all(rong(v) for v in hang)


def tim_nhan(o, nhan, tu=0, den=None):
	"""Ô đầu tiên có chữ chuẩn hoá bắt đầu bằng nhan; trả (r, c) hoặc (None, None)."""
	nhan = chuan(nhan)
	for r in range(tu, len(o) if den is None else min(den, len(o))):
		for c, v in enumerate(o[r]):
			if chuan(v).startswith(nhan):
				return r, c
	return None, None


def gia_tri_sau(o, r, c):
	"""Ô có giá trị đầu tiên bên phải (r, c) trên cùng dòng."""
	for v in o[r][c + 1:]:
		if not rong(v):
			return v
	return None


# ------------------------------------------------------------ khung kết quả

def ket_qua(mau, nhom, vendor, tai_khoan):
	return dict(mau=mau, nhom=nhom, vendor=vendor, tai_khoan=tai_khoan, phien_ban=PHIEN_BAN,
		tu_ngay="", den_ngay="", ngay_tien_ve="", dong=[], dong_loi=[], loi=[], canh_bao=[],
		tong=None, ghi_chu_don_vi="", them={})


def dong_moi(**k):
	ra = dict(ma_su_kien="", merchant="", diem_ban="", ngay="", gio="", ngay_tien_ve="",
		loai="ban", ma_don="", ma_tham_chieu="", ma_can_cu="", tien_hang=0, giam_gia=0,
		phi=0, dieu_chinh=0, thuc_nhan=0, thue=0, mo_ta="")
	ra.update(k)
	return ra


def them_loi(kq, vi_tri, ly_do, tho=None):
	kq["dong_loi"].append(dict(vi_tri=vi_tri, ly_do=str(ly_do), tho=[chu(v) for v in (tho or [])][:40]))


def khep_ky(kq):
	"""Kỳ của tệp = từ ngày nhỏ nhất tới lớn nhất của các dòng, nếu mẫu chưa đặt."""
	ngay_ds = sorted(d["ngay"] for d in kq["dong"] if d["ngay"])
	if not kq["tu_ngay"] and ngay_ds:
		kq["tu_ngay"] = ngay_ds[0]
	if not kq["den_ngay"] and ngay_ds:
		kq["den_ngay"] = ngay_ds[-1]
	tv = sorted({d["ngay_tien_ve"] for d in kq["dong"] if d["ngay_tien_ve"]})
	if not kq["ngay_tien_ve"] and len(tv) == 1:
		kq["ngay_tien_ve"] = tv[0]
	return kq


def kiem_tong(kq, tong_tep, truong=("tien_hang", "phi", "thuc_nhan"), dung_sai=0):
	"""So tổng các dòng đọc được (kể cả dòng lỗi thì không cộng) với dòng tổng
	in trên tệp. Lệch là lỗi cấp tệp: tệp chưa được coi là đủ."""
	kq["tong"] = dict(tong_tep)
	if kq["dong_loi"]:
		return kq
	for t in truong:
		if t not in tong_tep or tong_tep[t] is None:
			continue
		doc = sum(d[t] for d in kq["dong"])
		if abs(doc - tong_tep[t]) > dung_sai:
			kq["loi"].append("Tổng %s đọc được %s khác dòng tổng trên tệp %s; kiểm dòng thiếu hoặc đơn vị." % (
				_TEN_TRUONG.get(t, t), _so_vn(doc), _so_vn(tong_tep[t])))
	if "so_dong" in tong_tep and tong_tep["so_dong"] is not None and tong_tep["so_dong"] != len(kq["dong"]):
		kq["loi"].append("Tệp ghi %s giao dịch, đọc được %s." % (tong_tep["so_dong"], len(kq["dong"])))
	return kq


_TEN_TRUONG = dict(tien_hang="tiền hàng", phi="phí", thuc_nhan="thực nhận", giam_gia="giảm giá",
	dieu_chinh="điều chỉnh", thue="thuế")


def _so_vn(n):
	return "{:,}".format(int(n)).replace(",", ".")


# ============================================================ PAYOO

# Tài khoản con Payoo -> điểm bán của tiệm (đặc tả payoo.md mục 8). Terminal
# P6A91696 ở 9 Trần Cao Vân, P6A91697 ở xưởng 307/1 Nguyễn Văn Trỗi (SALES).
PAYOO_DIEM = {"VAGABOND_9TCV": "TCV", "VAGABOND_307NVT": "SALES"}

_PAYOO_THE = dict(
	tk_tong=["tai khoan payoo tong/quan ly"], tk_gd=["tai khoan payoo thuc hien giao dich"],
	ngay=["ngay giao dich"], rrn=["so tham chieu"], chuan_chi=["ma chuan chi"],
	gop=["so tien giao dich the"], phi=["phi xu ly the"], phi_gop=["phi chuyen doi tra gop"],
	nhan=["so tien payoo thanh toan"], ngay_tt=["ngay payoo thanh toan"],
	thiet_bi=["ma thiet bi"], loai=["loai tac nghiep"], loai_the=["chi tiet h.thuc t.toan"],
)
_PAYOO_QR = dict(
	tk_tong=["tai khoan payoo tong/quan ly"], tk_gd=["tai khoan payoo thuc hien giao dich"],
	ngay=["ngay giao dich"], ma_qr=["ma gd qr"], gop=["so tien giao dich"],
	phi=["phi xu ly giao dich qr"], nhan=["so tien payoo thanh toan"],
	ngay_tt=["ngay payoo thanh toan"], thiet_bi=["ma thiet bi"], loai=["loai tac nghiep"],
)


def _trang_luoi(tep):
	return [t for t in tep["trang"] if "o" in t]


def nhan_payoo(tep):
	for t in _trang_luoi(tep):
		if tim_tieu_de(t["o"], _PAYOO_THE, 5)[0] is not None:
			return "payoo_the"
		if tim_tieu_de(t["o"], _PAYOO_QR, 5)[0] is not None:
			return "payoo_qr"
	return None


def doc_payoo(tep, mau):
	the = mau == "payoo_the"
	can = _PAYOO_THE if the else _PAYOO_QR
	o = next(t["o"] for t in _trang_luoi(tep) if tim_tieu_de(t["o"], can, 5)[0] is not None)
	r0, cot = tim_tieu_de(o, can, 5)
	kq = ket_qua(mau, "ban", "Payoo", "")
	m = re.search(r"Doisoatky(?:tongket)?(\d{2})(\d{2})(\d{4})-(\d{2})(\d{2})(\d{4})", tep["ten"] or "")
	if m:
		kq["tu_ngay"] = _iso(m.group(3), m.group(2), m.group(1), "Kỳ")
		kq["den_ngay"] = _iso(m.group(6), m.group(5), m.group(4), "Kỳ")
	tk = set()
	for r in range(r0 + 1, len(o)):
		hang = o[r]
		if dong_trong(hang):
			continue
		# Dòng đánh số cột 1, 2, 3... ngay dưới tiêu đề.
		if all(chu(v) in ("", str(i + 1)) for i, v in enumerate(hang)) and chu(hang[0]) == "1":
			continue
		try:
			loai_tn = chuan(o_tai(hang, cot["loai"]))
			if loai_tn != "thanh toan":
				raise LoiDong("Loại tác nghiệp '%s' chưa có mẫu; giữ để kế toán xem, không tự đoán dấu." % chu(o_tai(hang, cot["loai"])))
			tk_tong = chu(o_tai(hang, cot["tk_tong"]))
			tk_gd = chu(o_tai(hang, cot["tk_gd"]))
			tk.add(tk_tong)
			ng, gio = ngay_gio(o_tai(hang, cot["ngay"]), "Ngày giao dịch")
			gop = tien_payoo(o_tai(hang, cot["gop"]), "Số tiền giao dịch")
			phi = tien_payoo(o_tai(hang, cot["phi"]), "Phí")
			phi_gop = tien_payoo(o_tai(hang, cot.get("phi_gop")), "Phí trả góp", cho_rong=True) if the else 0
			nhan = tien_payoo(o_tai(hang, cot["nhan"]), "Tiền Payoo thanh toán")
			if gop - phi - phi_gop != nhan:
				raise LoiDong("Tiền giao dịch trừ phí khác tiền Payoo thanh toán; kiểm dòng gốc.")
			thiet_bi = chu(o_tai(hang, cot["thiet_bi"]))
			if the:
				rrn = chu(o_tai(hang, cot["rrn"]))
				if not rrn:
					raise LoiDong("Thiếu Số tham chiếu; không có căn cước giao dịch.")
				ma = "the:%s:%s:%s:%s" % (tk_gd, thiet_bi, rrn, ng)
				tham_chieu = rrn
				ma_don = chu(o_tai(hang, cot["chuan_chi"]))
			else:
				ma_qr = chu(o_tai(hang, cot["ma_qr"]))
				if not ma_qr:
					raise LoiDong("Thiếu Mã GD QR; không có căn cước giao dịch.")
				ma = "qr:%s" % ma_qr
				tham_chieu = ma_qr
				ma_don = ma_qr
			kq["dong"].append(dong_moi(
				ma_su_kien=ma, merchant=tk_gd, diem_ban=PAYOO_DIEM.get(tk_gd, ""), ngay=ng, gio=gio,
				ngay_tien_ve=ngay(o_tai(hang, cot["ngay_tt"]), "Ngày Payoo thanh toán"),
				loai="ban", ma_don=ma_don, ma_tham_chieu=tham_chieu,
				tien_hang=gop, phi=phi + phi_gop, thuc_nhan=nhan,
				mo_ta=("Payoo %s" % chu(o_tai(hang, cot.get("loai_the"))).lower()) if the else "Payoo QR"))
		except LoiDong as e:
			them_loi(kq, r + 1, e, hang)
	if len(tk) > 1:
		kq["loi"].append("Tệp có nhiều tài khoản Payoo tổng (%s); tách tệp theo tài khoản." % ", ".join(sorted(tk)))
	kq["tai_khoan"] = next(iter(tk)) if len(tk) == 1 else ""
	kq["canh_bao"].append("Payoo không in dòng tổng; đủ hay thiếu được kiểm bằng tiền về ngân hàng.")
	return khep_ky(kq)


# ============================================================ ONEPAY

_ONEPAY_CHI_TIET = dict(stt=["no"], txn=["transaction id"], ref=["merchant trans. ref."],
	ngay=["transaction date"], loai=["transaction type"], kenh=["pay channel"])


def nhan_onepay(tep):
	for t in _trang_luoi(tep):
		o = t["o"]
		dau = " ".join(chuan(v) for h in o[:16] for v in h)
		if "onepay" not in dau and "vagabond" not in dau:
			continue
		if "thong bao tam ung" in dau or "advance payment notice" in dau:
			return "onepay_ngay"
		if "danh sach chi tiet giao dich" in dau:
			return "onepay_thang"
		if "monthly fee report" in dau or "bien ban xac nhan doi soat" in dau:
			return "onepay_bbds"
	return None


def _cot_onepay(o):
	"""Dòng tiêu đề tiếng Anh của OnePay (có 'Transaction ID') và bản đồ cột."""
	for r, hang in enumerate(o[:40]):
		s = [chuan(v) for v in hang]
		if "transaction id" in s and "no" in s:
			cot = {}
			for c, v in enumerate(s):
				if v and v not in cot:
					cot[v] = c
			return r, cot
	raise LoiMau("Không thấy dòng tiêu đề tiếng Anh (Transaction ID) của OnePay.")


def _c(cot, *ten):
	for t in ten:
		if t in cot:
			return cot[t]
	return None


def doc_onepay(tep, mau):
	"""Thông báo tạm ứng ngày (QT hoặc VietQR) và chi tiết tháng.

	Tiền OnePay là đồng nguyên; chuỗi theo kiểu Việt "1.180.000,00". Chỉ lấy
	Total fee làm phí (Fix fee đã nằm trong đó). Hoàn tiền mang số âm.
	"""
	luoi = _trang_luoi(tep)
	o = luoi[0]["o"]
	kq = ket_qua(mau, "ban", "OnePay", "VAGABOND")
	r0, cot = _cot_onepay(o)
	# QT: tiêu đề Việt, công thức, Anh; VietQR: Việt, Anh, công thức. Bỏ dòng
	# công thức "(1)" nếu nằm ngay dưới.
	bat_dau = r0 + 1
	if bat_dau < len(o) and any(chu(v).startswith("(") for v in o[bat_dau]):
		bat_dau += 1
	c_txn = _c(cot, "transaction id")
	c_ref = _c(cot, "merchant trans. ref.")
	c_don = _c(cot, "order reference")
	c_ngay = _c(cot, "transaction date")
	c_loai = _c(cot, "transaction type")
	c_kenh = _c(cot, "pay channel")
	c_gop = _c(cot, "successful amount (vnd)", "transaction amount")
	c_phi = _c(cot, "total fee")
	c_nhan = _c(cot, "advance amount", "total advance amount", "total amount after charge fee")
	c_tv = _c(cot, "payment date", "advance date")
	if mau == "onepay_thang" and c_tv is None:
		# Cột Payment Date của QT tháng không có tiêu đề tiếng Anh; nằm ngay sau cột cuối.
		c_tv = max(cot.values()) + 1
	thieu = [n for n, c in (("Transaction ID", c_txn), ("Transaction date", c_ngay), ("Amount", c_gop),
		("Total fee", c_phi), ("Advance amount", c_nhan)) if c is None]
	if thieu:
		raise LoiMau("Thiếu cột OnePay: %s." % ", ".join(thieu))
	kenh_tep = set()
	tong_tep = None
	for r in range(bat_dau, len(o)):
		hang = o[r]
		if dong_trong(hang):
			continue
		nhan_dong = " ".join(chuan(v) for v in hang if not rong(v))
		if nhan_dong.startswith("tong cong") or nhan_dong.startswith("tong cuoi"):
			try:
				tong_tep = dict(phi=tien_vi(o_tai(hang, c_phi), "Tổng phí"),
					thuc_nhan=tien_vi(o_tai(hang, c_nhan), "Tổng tạm ứng"))
				g = o_tai(hang, c_gop)
				if not rong(g):
					tong_tep["tien_hang"] = tien_vi(g, "Tổng giá trị")
			except LoiDong as e:
				kq["loi"].append("Dòng tổng OnePay đọc không được: %s" % e)
			break
		stt = chu(o_tai(hang, cot.get("no")))
		if not stt.isdigit():
			continue
		try:
			kenh = chuan(o_tai(hang, c_kenh)).upper() if c_kenh is not None else ""
			kenh = "VIETQR" if kenh == "VIETQR" else kenh
			kenh_tep.add(kenh)
			txn = chu(o_tai(hang, c_txn))
			if not txn:
				raise LoiDong("Thiếu Transaction ID.")
			ng, gio = ngay_gio(o_tai(hang, c_ngay), "Transaction date")
			gop = tien_vi(o_tai(hang, c_gop), "Số tiền giao dịch")
			phi = tien_vi(o_tai(hang, c_phi), "Total fee")
			nhan = tien_vi(o_tai(hang, c_nhan), "Advance amount")
			loai_gd = chu(o_tai(hang, c_loai)).upper()
			if loai_gd == "PURCHASE":
				loai = "ban"
				if gop < 0:
					raise LoiDong("Giao dịch PURCHASE mang số âm; kiểm tệp gốc.")
			elif "REFUND" in loai_gd:
				loai = "hoan"
				if gop > 0:
					raise LoiDong("Giao dịch hoàn mang số dương; OnePay ghi hoàn bằng số âm.")
			else:
				raise LoiDong("Loại giao dịch '%s' chưa có mẫu; giữ để kế toán xem." % loai_gd)
			if gop - phi != nhan:
				raise LoiDong("Số tiền trừ Total fee khác Advance amount; kiểm dòng gốc.")
			tv = ngay(o_tai(hang, c_tv), "Payment date") if c_tv is not None and not rong(o_tai(hang, c_tv)) else ""
			ref = chu(o_tai(hang, c_ref))
			kq["dong"].append(dong_moi(
				ma_su_kien="%s:%s" % (kenh or "?", txn), merchant="VAGABOND", diem_ban="SALES",
				ngay=ng, gio=gio, ngay_tien_ve=tv, loai=loai, ma_don=ref or chu(o_tai(hang, c_don)),
				ma_tham_chieu=ref, tien_hang=gop, phi=phi, thuc_nhan=nhan,
				thue=int((Decimal(abs(phi)) / 11).quantize(Decimal("1"), rounding=ROUND_HALF_UP)) * (1 if phi >= 0 else -1),
				mo_ta="OnePay %s" % ("VietQR" if kenh == "VIETQR" else "thẻ quốc tế")))
		except LoiDong as e:
			them_loi(kq, r + 1, e, hang)
	if len(kenh_tep) > 1:
		kq["loi"].append("Tệp trộn nhiều kênh OnePay (%s)." % ", ".join(sorted(kenh_tep)))
	if tong_tep is None:
		kq["loi"].append("Không thấy dòng Tổng cộng của OnePay; tệp có thể bị cắt.")
	else:
		kiem_tong(kq, tong_tep)
	if mau == "onepay_ngay":
		_onepay_tom_tat(tep, kq)
	return khep_ky(kq)


def _onepay_tom_tat(tep, kq):
	"""Đọc tab Summary (nếu có): bút toán, số cuối, nội dung chuyển tiền PVS."""
	m = re.match(r"(\d{8})_(\d{5,9})", tep["ten"] or "")
	if m:
		kq["ngay_tien_ve"] = ngay(m.group(1))
		kq["them"]["but_toan"] = m.group(2)
		for d in kq["dong"]:
			d["ngay_tien_ve"] = d["ngay_tien_ve"] or kq["ngay_tien_ve"]
	for t in _trang_luoi(tep)[1:]:
		o = t["o"]
		r, c = tim_nhan(o, "TW tổng cuối")
		if r is not None:
			try:
				kq["them"]["so_cuoi"] = tien_vi(gia_tri_sau(o, r, c), "Final total amount")
			except LoiDong:
				pass
		r, c = tim_nhan(o, "Nội dung chuyển tiền")
		if r is not None:
			nd = chu(gia_tri_sau(o, r, c))
			pvs = re.search(r"PVS\d{5,10}", nd)
			if pvs:
				kq["them"]["ma_chuyen"] = pvs.group(0)
	if "so_cuoi" in kq["them"] and kq["tong"] and kq["them"]["so_cuoi"] != kq["tong"].get("thuc_nhan"):
		kq["loi"].append("Số cuối ở tab Summary khác tổng tạm ứng ở chi tiết.")


def doc_onepay_bbds(tep, mau):
	"""Biên bản đối soát tháng: không có giao dịch, chỉ tổng theo từng đợt trả.

	Dùng làm tổng kiểm soát tháng: so với các thông báo tạm ứng đã nhận.
	"""
	o = _trang_luoi(tep)[0]["o"]
	kq = ket_qua(mau, "tong_hop", "OnePay", "VAGABOND")
	kenh = ""
	for h in o[:14]:
		s = " ".join(chu(v) for v in h)
		m = re.search(r"-\s*(QT|VIETQR)\s*-\s*VAGABOND", s, re.I)
		if m:
			kenh = m.group(1).upper()
	r0 = None
	for r, h in enumerate(o[:40]):
		if any("advance amount" in chuan(v) for v in h) and any("total fee" in chuan(v) for v in h):
			r0 = r
			break
	if r0 is None:
		raise LoiMau("Không thấy tiêu đề biên bản đối soát OnePay.")
	cot = {chuan(chu(v).split("\n")[-1]): c for c, v in enumerate(o[r0]) if not rong(v)}
	c_ky = _c(cot, "transaction date")
	c_gop = _c(cot, "transaction amount")
	c_nhan = _c(cot, "advance amount")
	c_phi = _c(cot, "total fee")
	c_sl = _c(cot, "count success")
	ky = []
	for r in range(r0 + 1, len(o)):
		h = o[r]
		if dong_trong(h):
			continue
		dau = chuan(h[0])
		try:
			if dau.startswith("tong cong"):
				kq["tong"] = dict(tien_hang=tien_vi(o_tai(h, c_gop)), phi=tien_vi(o_tai(h, c_phi)),
					thuc_nhan=tien_vi(o_tai(h, c_nhan)), so_dong=int(tien_vi(o_tai(h, c_sl))))
				break
			if not dau.isdigit():
				continue
			khoang = chu(o_tai(h, c_ky)).split("-")
			ky.append(dict(tu=ngay(khoang[0].strip()), den=ngay(khoang[-1].strip()),
				tien_hang=tien_vi(o_tai(h, c_gop)), phi=tien_vi(o_tai(h, c_phi)),
				thuc_nhan=tien_vi(o_tai(h, c_nhan)), so_dong=int(tien_vi(o_tai(h, c_sl)))))
		except (LoiDong, IndexError) as e:
			kq["loi"].append("Dòng %s của biên bản đọc không được: %s" % (r + 1, e))
	if kq["tong"] is None:
		kq["loi"].append("Không thấy dòng TỔNG CỘNG của biên bản.")
	elif ky:
		for t in ("tien_hang", "phi", "thuc_nhan", "so_dong"):
			if sum(k[t] for k in ky) != kq["tong"][t]:
				kq["loi"].append("Cộng các đợt khác dòng tổng của biên bản (%s)." % _TEN_TRUONG.get(t, t))
	m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})_(\d{2})\.(\d{2})\.(\d{4})", tep["ten"] or "")
	if m:
		kq["tu_ngay"] = _iso(m.group(3), m.group(2), m.group(1), "Kỳ")
		kq["den_ngay"] = _iso(m.group(6), m.group(5), m.group(4), "Kỳ")
	kq["them"].update(kenh=kenh, ky=ky)
	return kq


# ============================================================ SHINHAN POS

_SHINHAN_CT = dict(
	tt=["mid"], tid=["tid"], the=["card no."], ngay=["trxn date"], gop=["trxn amount (vnd)", "trxn amount"],
	mdr=["mdr (%)"], phi=["mdf (include vat)"], phi_xl=["processing fee"], nhan=["payment amount"],
	chuan_chi=["approval code"], hoan=["reversal/refund"], ngay_tt=["paymen date", "payment date"],
)
_SHINHAN_TH = dict(mid=["mid"], ngay_tt=["paymen date", "payment date"], sl=["count of trxn"],
	gop=["trxn amount"], phi=["mdf (include vat)"], nhan=["payment amount"])

# MID Shinhan -> điểm bán. Đặc tả shinhan_pos.md: tệp không ghi MID nào ở
# cửa hàng nào; anh Việt xác nhận rồi mới điền. Để trống thì dòng vẫn nhận,
# chỉ chưa gán điểm bán.
SHINHAN_DIEM = {}


def nhan_shinhan(tep):
	for t in _trang_luoi(tep):
		dau = " ".join(chuan(v) for h in t["o"][:6] for v in h)
		if "merchant statement report" in dau or "monthly detail report" in dau:
			return "shinhan_ngay" if "merchant statement report" in dau else "shinhan_thang"
	return None


def doc_shinhan(tep, mau):
	"""Sao kê Shinhan POS: tab chi tiết là nguồn dòng, tab tóm tắt là tổng kiểm.

	Căn cước: MID|TID|thời điểm|mã chuẩn chi|số thẻ đã che|số tiền (đặc tả
	mục 7). Báo cáo ngày và tháng cùng chứa một giao dịch nên căn cước giống
	hệt ở cả hai, nhận lần hai là dòng trùng.
	"""
	kq = ket_qua(mau, "ban", "Shinhan POS", "")
	ct = th = None
	for t in _trang_luoi(tep):
		if ct is None and tim_tieu_de(t["o"], _SHINHAN_CT, 40)[0] is not None:
			ct = t
		elif th is None and tim_tieu_de(t["o"], _SHINHAN_TH, 40)[0] is not None:
			th = t
	if ct is None:
		raise LoiMau("Không thấy tab chi tiết giao dịch (Detail) của Shinhan; tải tệp gốc đủ hai tab.")
	o = ct["o"]
	r0, cot = tim_tieu_de(o, _SHINHAN_CT, 40)
	tong_tep = None
	mids = set()
	for r in range(r0 + 1, len(o)):
		h = o[r]
		if dong_trong(h):
			continue
		if any(chuan(v).startswith("tong/total") for v in h):
			try:
				tong_tep = dict(tien_hang=tien_vi(o_tai(h, cot["gop"])), phi=tien_vi(o_tai(h, cot["phi"])),
					thuc_nhan=tien_vi(o_tai(h, cot["nhan"])))
			except LoiDong as e:
				kq["loi"].append("Dòng tổng Shinhan đọc không được: %s" % e)
			break
		if not chu(h[0]).isdigit():
			continue
		try:
			mid = chu(o_tai(h, cot["tt"]))
			tid = chu(o_tai(h, cot["tid"]))
			mids.add(mid)
			ng, gio = ngay_gio(o_tai(h, cot["ngay"]), "Thời gian giao dịch")
			gop = tien_vi(o_tai(h, cot["gop"]), "Số tiền giao dịch")
			phi = tien_vi(o_tai(h, cot["phi"]), "MDF")
			phi_xl = tien_vi(o_tai(h, cot["phi_xl"]), "Phí xử lý", cho_rong=True)
			nhan = tien_vi(o_tai(h, cot["nhan"]), "Số tiền báo có")
			if gop - phi - phi_xl != nhan:
				raise LoiDong("Tiền giao dịch trừ MDF và phí xử lý khác số báo có; kiểm dòng gốc.")
			chuan_chi = chu(o_tai(h, cot["chuan_chi"])).lstrip("'")
			if chuan(o_tai(h, cot["hoan"])) == "y":
				raise LoiDong("Giao dịch hoàn/huỷ (Y) chưa có mẫu thật; giữ để kế toán xem, không tự đoán dấu.")
			the = chu(o_tai(h, cot["the"]))
			kq["dong"].append(dong_moi(
				ma_su_kien="%s|%s|%s %s|%s|%s|%s" % (mid, tid, ng, gio, chuan_chi, the, gop),
				merchant=mid, diem_ban=SHINHAN_DIEM.get(mid, ""), ngay=ng, gio=gio,
				ngay_tien_ve=ngay(o_tai(h, cot["ngay_tt"]), "Ngày thanh toán"), loai="ban",
				ma_don=chuan_chi, ma_tham_chieu=chuan_chi, tien_hang=gop, phi=phi + phi_xl, thuc_nhan=nhan,
				thue=int((Decimal(phi) / 11).quantize(Decimal("1"), rounding=ROUND_HALF_UP)),
				mo_ta="Thẻ %s" % the[-4:] if the else "Thẻ"))
		except LoiDong as e:
			them_loi(kq, r + 1, e, h)
	kq["tai_khoan"] = "SHINHAN-POS"
	if tong_tep is None:
		kq["loi"].append("Không thấy dòng Tổng/Total ở tab chi tiết Shinhan; tệp có thể bị cắt.")
	else:
		kiem_tong(kq, tong_tep)
	if th is not None:
		_shinhan_doi_tom_tat(th["o"], kq)
	kq["them"]["mid"] = sorted(mids)
	return khep_ky(kq)


def _shinhan_doi_tom_tat(o, kq):
	r0, cot = tim_tieu_de(o, _SHINHAN_TH, 40)
	for r in range(r0 + 1, len(o)):
		h = o[r]
		if chuan(h[0]).startswith("tong/total"):
			try:
				th = dict(tien_hang=tien_vi(o_tai(h, cot["gop"])), phi=tien_vi(o_tai(h, cot["phi"])),
					thuc_nhan=tien_vi(o_tai(h, cot["nhan"])), so_dong=int(tien_vi(o_tai(h, cot["sl"]))))
			except LoiDong as e:
				kq["loi"].append("Tab tóm tắt Shinhan đọc không được: %s" % e)
				return
			if not kq["dong_loi"]:
				for t in ("tien_hang", "phi", "thuc_nhan"):
					if sum(d[t] for d in kq["dong"]) != th[t]:
						kq["loi"].append("Tab tóm tắt Shinhan khác tổng chi tiết (%s)." % _TEN_TRUONG[t])
				if th["so_dong"] != len(kq["dong"]):
					kq["loi"].append("Tab tóm tắt ghi %s giao dịch, chi tiết có %s." % (th["so_dong"], len(kq["dong"])))
			return


# ============================================================ SHOPEEFOOD

# Mã cửa hàng ShopeeFood -> điểm bán (đặc tả shopeefood.md mục 1).
SHOPEE_DIEM = {"10322362": "TCV", "10332477": "SALES"}

_SHOPEE = dict(ma=["ma don hang"], cua_hang=["id cua hang"], ngay=["thoi gian hoan thanh/ huy don",
	"thoi gian hoan thanh/huy don"], gop=["gia tri don hang"], km=["khuyen mai tu quan"],
	phi_dv=["phi dich vu"], ship=["phi van chuyen tra cho quan"], ck=["chiet khau"], nhan=["thuc thu"])


def nhan_shopee(tep):
	for t in _trang_luoi(tep):
		r, cot = tim_tieu_de(t["o"], _SHOPEE, 3)
		# Xanh SM Ngon cũng có các cột này; ShopeeFood thì KHÔNG có "Mã Rút Gọn".
		if r is not None and not any(chuan(v) == "ma rut gon" for v in t["o"][r]):
			return "shopeefood"
	return None


def doc_shopee(tep, mau):
	"""ShopeeFood: tiền theo NGHÌN đồng, ba số lẻ. Không có dòng tổng.

	Phí = tiền hàng sau khuyến mại trừ thực thu (gồm chiết khấu, thuế khấu
	trừ, phí dịch vụ, trừ phí ship trả quán). Lệch quá 1 đồng so với các cột
	phí in ra là lỗi; 1 đồng là Shopee làm tròn từ số chưa làm tròn.
	"""
	o = next(t["o"] for t in _trang_luoi(tep) if tim_tieu_de(t["o"], _SHOPEE, 3)[0] is not None)
	r0, cot = tim_tieu_de(o, _SHOPEE, 3)
	c_thue = next((c for c, v in enumerate(o[r0]) if chuan(v) == "thue khau tru"), None)
	kq = ket_qua(mau, "ban", "ShopeeFood", "SHOPEEFOOD")
	kq["ghi_chu_don_vi"] = "ShopeeFood ghi tiền theo nghìn đồng; đã nhân 1.000."
	for r in range(r0 + 1, len(o)):
		h = o[r]
		if dong_trong(h):
			continue
		try:
			ma = chu(o_tai(h, cot["ma"]))
			if not ma:
				raise LoiDong("Thiếu Mã đơn hàng.")
			ch = chu(o_tai(h, cot["cua_hang"]))
			ng, gio = ngay_gio(o_tai(h, cot["ngay"]), "Thời gian hoàn thành")
			gop = tien_nghin(o_tai(h, cot["gop"]), "Giá trị đơn hàng")
			km = tien_nghin(o_tai(h, cot["km"]), "Khuyến mại từ quán", cho_rong=True)
			phi_dv = tien_nghin(o_tai(h, cot["phi_dv"]), "Phí dịch vụ", cho_rong=True)
			ship = tien_nghin(o_tai(h, cot["ship"]), "Phí vận chuyển trả quán", cho_rong=True)
			ck = tien_nghin(o_tai(h, cot["ck"]), "Chiết khấu", cho_rong=True)
			thue = tien_nghin(o_tai(h, c_thue), "Thuế khấu trừ", cho_rong=True) if c_thue is not None else 0
			nhan = tien_nghin(o_tai(h, cot["nhan"]), "Thực thu")
			if min(gop, km, phi_dv, ship, ck, thue) < 0 or nhan > gop:
				raise LoiDong("Dòng có số âm hoặc thực thu lớn hơn giá trị đơn; chưa có mẫu hoàn/điều chỉnh, giữ để xem.")
			tien_hang = gop - km
			phi = tien_hang - nhan
			in_ra = ck + thue + phi_dv - ship
			if abs(phi - in_ra) > 1:
				raise LoiDong("Giá trị trừ khuyến mại và các khoản phí khác thực thu quá 1 đồng; kiểm dòng gốc.")
			kq["dong"].append(dong_moi(
				ma_su_kien=ma, merchant=ch, diem_ban=SHOPEE_DIEM.get(ch, ""), ngay=ng, gio=gio, loai="ban",
				ma_don=ma, ma_tham_chieu=ma, tien_hang=tien_hang, giam_gia=km, phi=phi, thuc_nhan=nhan,
				thue=thue, mo_ta="ShopeeFood"))
		except LoiDong as e:
			them_loi(kq, r + 1, e, h)
	kq["canh_bao"].append("ShopeeFood không in dòng tổng; đủ hay thiếu được kiểm bằng tiền về ngân hàng.")
	return khep_ky(kq)


# ============================================================ XANH SM NGON

GREENSM_DIEM = {"01K23YRC2F21BG1DP3P8T4KV7Q": "TCV", "01K23YRC3K35J07ZYBVADZZSYK": "SALES"}

_GREENSM = dict(ma=["ma don hang"], rut_gon=["ma rut gon"], cua_hang=["id cua hang"],
	ngay=["thoi gian hoan thanh/ huy don", "thoi gian hoan thanh/huy don"], trang_thai=["trang thai"],
	gop=["gia tri don hang"], giam_mon=["giam gia mon"], cofund_mon=["tong tien cofund km mon an"],
	rong_=["doanh thu rong"], ck=["chiet khau"], vat=["vat"], pit=["pit"], nhan=["thuc thu"])


def nhan_greensm(tep):
	for t in _trang_luoi(tep):
		if tim_tieu_de(t["o"], _GREENSM, 3)[0] is not None:
			return "greensm_ngon"
	return None


def doc_greensm(tep, mau):
	"""Xanh SM Ngon: mỗi tệp một cửa hàng một ngày. Tab Summary là tổng kiểm.

	Doanh thu ròng = giá trị - giảm giá món - cofund phần món ăn. Cofund phần
	giao hàng không trừ vào quán; cột tổng cofund là tổng của hai phần nên
	không cộng thêm lần nữa.
	"""
	luoi = _trang_luoi(tep)
	o = next(t["o"] for t in luoi if tim_tieu_de(t["o"], _GREENSM, 3)[0] is not None)
	r0, cot = tim_tieu_de(o, _GREENSM, 3)
	kq = ket_qua(mau, "ban", "Xanh SM Ngon", "GREENSM")
	cua_hang = set()
	for r in range(r0 + 1, len(o)):
		h = o[r]
		if dong_trong(h):
			continue
		try:
			ma = chu(o_tai(h, cot["ma"]))
			if not ma:
				raise LoiDong("Thiếu Mã Đơn Hàng.")
			ch = chu(o_tai(h, cot["cua_hang"]))
			cua_hang.add(ch)
			tt = chuan(o_tai(h, cot["trang_thai"]))
			if tt != "completed":
				raise LoiDong("Trạng thái '%s' chưa có mẫu; giữ để kế toán xem." % chu(o_tai(h, cot["trang_thai"])))
			ng, gio = ngay_gio(o_tai(h, cot["ngay"]), "Thời gian hoàn thành")
			gop = tien_vi(o_tai(h, cot["gop"]), "Giá trị đơn hàng")
			giam = tien_vi(o_tai(h, cot["giam_mon"]), "Giảm giá món", cho_rong=True)
			cof = tien_vi(o_tai(h, cot["cofund_mon"]), "Cofund món ăn", cho_rong=True)
			rong_ = tien_vi(o_tai(h, cot["rong_"]), "Doanh thu ròng")
			ck = tien_vi(o_tai(h, cot["ck"]), "Chiết khấu", cho_rong=True)
			vat = tien_vi(o_tai(h, cot["vat"]), "VAT", cho_rong=True)
			pit = tien_vi(o_tai(h, cot["pit"]), "PIT", cho_rong=True)
			nhan = tien_vi(o_tai(h, cot["nhan"]), "Thực thu")
			if gop - giam - cof != rong_:
				raise LoiDong("Giá trị trừ giảm giá món và cofund món khác doanh thu ròng; kiểm dòng gốc.")
			if rong_ - ck - vat - pit != nhan:
				raise LoiDong("Doanh thu ròng trừ chiết khấu, VAT, PIT khác thực thu; kiểm dòng gốc.")
			kq["dong"].append(dong_moi(
				ma_su_kien=ma, merchant=ch, diem_ban=GREENSM_DIEM.get(ch, ""), ngay=ng, gio=gio, loai="ban",
				ma_don=chu(o_tai(h, cot["rut_gon"])), ma_tham_chieu=chu(o_tai(h, cot["rut_gon"])),
				tien_hang=rong_, giam_gia=giam + cof, phi=ck + vat + pit, thuc_nhan=nhan, thue=vat + pit,
				mo_ta="Xanh SM Ngon"))
		except LoiDong as e:
			them_loi(kq, r + 1, e, h)
	# Codex #446 F3: mã đơn Xanh SM là ULID duy nhất toàn hệ, nên phạm vi khoá
	# để cố định "GREENSM" dù tệp có một hay nhiều cửa hàng. Đổi phạm vi theo
	# thành phần tệp là nhận trùng khi tải bản tách và bản gộp.
	tong = None
	for t in luoi:
		if t["o"] is o:
			continue
		nhan_ = {chuan(h[0]): h[1] if len(h) > 1 else None for h in t["o"] if h and not rong(h[0])}
		if "tong thuc thu" in nhan_:
			try:
				tong = dict(so_dong=int(tien_vi(nhan_.get("tong so don hang"))),
					thuc_nhan=tien_vi(nhan_.get("tong thuc thu")),
					tien_hang=tien_vi(nhan_.get("doanh thu rong")),
					phi=tien_vi(nhan_.get("tong chiet khau")))
			except LoiDong as e:
				kq["loi"].append("Tab Summary của Xanh SM đọc không được: %s" % e)
	if tong is None:
		kq["canh_bao"].append("Không có tab Summary; tải tệp Excel gốc đủ hai tab để có tổng kiểm.")
	else:
		# Phí ở dòng tổng chỉ có chiết khấu; VAT/PIT thường bằng 0.
		if all(d["thue"] == 0 for d in kq["dong"]):
			kiem_tong(kq, tong)
		else:
			kiem_tong(kq, tong, truong=("tien_hang", "thuc_nhan"))
	return khep_ky(kq)


# ============================================================ GRABFOOD (PDF)

GRAB_DIEM = {"5-C4E1NPWGG2WZFA": "TCV", "5-C4E1NPWGMGBGNX": "SALES", "5-C8BKA3MZMEW1CA": "NVHTN"}
GRAB_TEN = {"tran cao van": "5-C4E1NPWGG2WZFA", "the vagabond delivery kitchen": "5-C4E1NPWGMGBGNX",
	"nha van hoa thanh nien": "5-C8BKA3MZMEW1CA"}

_SO_GRAB = r"-?\d{1,3}(?:\.\d{3})*|-"
_RE_DON = re.compile(r"^\s*(\d{1,2}:\d{2}\s?[AP]M|Đã hủy)\s+(G[A-Z]-\s?[A-Z0-9]*)\s+(Trả thẻ / Ví|Tiền mặt|-)\s+(.*)$")
_RE_ADS = re.compile(r"^\s*(\d{1,2})\s+Th(\d{1,2}),\s*(\d{1,2}:\d{2}\s?[AP]M)\s+(ADS-\d+)\s+(.*?)\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)\s*$")
_RE_DC = re.compile(r"^\s*(\d{1,2})\s+Th(\d{1,2}),\s*(\d{1,2}:\d{2}\s?[AP]M)\s+(MPA-\d+)\s+(?:(G[A-Z]-\s?[A-Z0-9]+)\s+)?(.*?)\s+(-?[\d.]+)\s*$")


def _so_grab(s):
	s = s.strip()
	if s in ("-", ""):
		return 0
	if not re.fullmatch(r"-?\d{1,3}(?:\.\d{3})*", s):
		raise LoiDong("Số GrabFood sai dạng (%s)." % s)
	return int(s.replace(".", ""))


def _gio_24(s):
	m = re.fullmatch(r"(\d{1,2}):(\d{2})\s?([AP]M)", s.strip())
	if not m:
		return ""
	hh = int(m.group(1)) % 12 + (12 if m.group(3) == "PM" else 0)
	return "%02d:%s:00" % (hh, m.group(2))


def _dong_pdf(tep):
	return [d for t in tep["trang"] for d in t.get("dong", [])]


def nhan_grab(tep):
	dong = _dong_pdf(tep)[:15]
	if any("Báo cáo kinh doanh hàng ngày" in d for d in dong) and any("grb.to" in d for d in dong):
		return "grabfood"
	return None


def doc_grab(tep, mau):
	"""GrabFood: PDF báo cáo kinh doanh hàng ngày của một cửa hàng.

	Ba loại dòng: đơn (bán), quảng cáo (phí kỳ, có mã ADS làm căn cứ), điều
	chỉnh (có mã MPA và mã đơn làm căn cứ). Đơn huỷ không có tiền nhưng được
	đếm trong "Tổng số đơn hàng". Mã đơn Grab ngắn và lặp lại, nên căn cước
	ghép cửa hàng + ngày + mã + giờ + tiền (đặc tả grabfood.md mục 7).
	"""
	dong = _dong_pdf(tep)
	kq = ket_qua(mau, "ban", "GrabFood", "")
	m = re.search(r"(5-[A-Z0-9]{10,20})-(\d{8})", tep["ten"] or "")
	merchant = m.group(1) if m else ""
	ngay_bc = ""
	for d in dong[:6]:
		mm = re.search(r"(\d{1,2}) tháng (\d{1,2}) (\d{4})", d)
		if mm:
			ngay_bc = _iso(mm.group(3), mm.group(2), mm.group(1), "Ngày báo cáo")
			break
	if not ngay_bc:
		raise LoiMau("Không thấy ngày báo cáo trên PDF GrabFood.")
	ten_ch = chuan(" ".join(dong[:8]))
	theo_ten = next((v for k, v in GRAB_TEN.items() if k in ten_ch), "")
	if not merchant:
		merchant = theo_ten
	elif theo_ten and theo_ten != merchant:
		kq["loi"].append("Tên cửa hàng trong PDF không khớp mã cửa hàng ở tên tệp.")
	if not merchant:
		raise LoiMau("Không xác định được cửa hàng GrabFood; giữ đúng tên tệp gốc 5-<mã>-<ngày>.pdf.")
	kq.update(tu_ngay=ngay_bc, den_ngay=ngay_bc, tai_khoan="GRABFOOD:" + merchant)
	diem = GRAB_DIEM.get(merchant, "")
	tong = {}
	vung = ""
	huy = []
	bo_qua = set()
	for i, d in enumerate(dong):
		if i in bo_qua:
			continue
		s = d.strip()
		if s.startswith("Hướng dẫn đọc hiểu báo cáo"):
			break
		if s.startswith("VND") and "đơn hàng" in s:
			so = re.findall(r"VND\s?(-?[\d.]+)", s)
			sl = re.search(r"(\d+)\s+đơn hàng", s)
			if so:
				tong["thuc_nhan"] = _so_grab(so[0])
			if len(so) > 1:
				tong["con_thieu"] = _so_grab(so[1])
			if sl:
				tong["so_don"] = int(sl.group(1))
			continue
		mtv = re.search(r"chuyển cho bạn vào ngày.*?tháng (\d{1,2}) (\d{1,2})", s)
		if mtv:
			y = int(ngay_bc[:4]) + (1 if int(mtv.group(1)) < int(ngay_bc[5:7]) else 0)
			kq["ngay_tien_ve"] = _iso(y, mtv.group(1), mtv.group(2), "Ngày chuyển")
			continue
		if s in ("Đơn hàng Delivery",):
			vung = "don"
			continue
		if s == "Marketing":
			vung = "ads"
			continue
		if s == "Điều chỉnh":
			vung = "dc"
			continue
		if s in ("Đơn hàng ăn tại quán", "Phí giao hàng", "Khoản bồi hoàn", "Số tiền đã hoàn lại"):
			kq["loi"].append("PDF có mục '%s' chưa có mẫu; giữ tệp để đọc tay." % s)
			vung = "la"
			continue
		if s.startswith("Tổng cộng") and vung == "don":
			so = re.findall(r"-?\d{1,3}(?:\.\d{3})+|-?\d+", s.replace("VND", ""))
			if so:
				tong["don"] = _so_grab(so[-1])
			continue
		try:
			if vung == "don":
				md = _RE_DON.match(d)
				if not md:
					if re.fullmatch(r"[\d.\s-]*", s):
						continue
					raise LoiDong("Dòng trong mục đơn hàng không đọc được; đối chiếu PDF.")
				gio_, ma, pt, con = md.groups()
				ma = re.sub(r"\s+", "", ma)
				if ma.endswith("-"):
					# Mã dài bị PDF ngắt sang dòng sau (GD-\n TZOZM7AF).
					sau = dong[i + 1].strip() if i + 1 < len(dong) else ""
					if not re.fullmatch(r"[A-Z0-9]{3,20}", sau):
						raise LoiDong("Mã đơn %s bị cắt, không thấy phần sau; đối chiếu PDF." % ma)
					ma += sau
					bo_qua.add(i + 1)
				so = con.split()
				if len(so) != 7:
					raise LoiDong("Dòng đơn %s không đủ 7 cột tiền." % ma)
				if gio_ == "Đã hủy":
					if any(x != "-" for x in so):
						raise LoiDong("Đơn huỷ %s lại có tiền; kiểm PDF." % ma)
					huy.append(ma)
					continue
				gop, vat, dv, km, ck, ship, nhan = (_so_grab(x) for x in so)
				if gop + vat + dv + km + ck + ship != nhan:
					raise LoiDong("Đơn %s: trị giá cộng các khoản khác thu nhập; kiểm PDF." % ma)
				kq["dong"].append(dong_moi(
					ma_su_kien="%s|%s|%s|%s|%s" % (merchant, ngay_bc, ma, _gio_24(gio_), gop),
					merchant=merchant, diem_ban=diem, ngay=ngay_bc, gio=_gio_24(gio_), loai="ban",
					ma_don=ma, ma_tham_chieu=ma, tien_hang=gop + vat + dv + km + ship, giam_gia=-(km + ship),
					phi=-ck, thuc_nhan=nhan, thue=vat,
					mo_ta="GrabFood %s" % ("tiền mặt" if pt == "Tiền mặt" else "thẻ/ví")))
			elif vung == "ads":
				ma_ = _RE_ADS.match(d)
				if not ma_:
					continue
				dd, mo, gio_, ma, mo_ta, phi_, thue_, tong_ = ma_.groups()
				phi_, thue_, tong_ = _so_grab(phi_), _so_grab(thue_), _so_grab(tong_)
				if phi_ + thue_ != tong_:
					raise LoiDong("Quảng cáo %s: phí cộng thuế khác tổng." % ma)
				kq["dong"].append(dong_moi(
					ma_su_kien="%s|%s|%s" % (merchant, ngay_bc, ma), merchant=merchant, diem_ban=diem,
					ngay=ngay_bc, gio=_gio_24(gio_), loai="phi_ky", ma_can_cu=ma, ma_don=ma,
					tien_hang=0, phi=-tong_, thuc_nhan=tong_, thue=-thue_, mo_ta=("Quảng cáo: " + mo_ta)[:140]))
			elif vung == "dc":
				mdc = _RE_DC.match(d)
				if not mdc:
					continue
				dd, mo, gio_, ma, ma_don, mo_ta, tien = mdc.groups()
				tien = _so_grab(tien)
				ma_don = re.sub(r"\s+", "", ma_don or "")
				kq["dong"].append(dong_moi(
					ma_su_kien="%s|%s|%s" % (merchant, ngay_bc, ma), merchant=merchant, diem_ban=diem,
					ngay=ngay_bc, gio=_gio_24(gio_), loai="dieu_chinh", ma_can_cu=(ma + " " + ma_don).strip(),
					ma_don=ma_don, ma_tham_chieu=ma_don, dieu_chinh=tien, thuc_nhan=tien,
					mo_ta=("Điều chỉnh: " + mo_ta)[:140]))
		except LoiDong as e:
			them_loi(kq, i + 1, e, [d])
	kq["them"]["don_huy"] = huy
	if "thuc_nhan" not in tong:
		kq["loi"].append("Không thấy Tổng thu nhập trên PDF GrabFood.")
	else:
		ban = [d for d in kq["dong"] if d["loai"] == "ban"]
		if not kq["dong_loi"]:
			if "don" in tong and sum(d["thuc_nhan"] for d in ban) != tong["don"]:
				kq["loi"].append("Cộng thu nhập các đơn khác dòng Tổng cộng của mục đơn hàng.")
			if "so_don" in tong and tong["so_don"] != len(ban) + len(huy):
				kq["loi"].append("PDF ghi %s đơn, đọc được %s đơn và %s đơn huỷ." % (tong["so_don"], len(ban), len(huy)))
		kiem_tong(kq, dict(thuc_nhan=tong["thuc_nhan"]), truong=("thuc_nhan",))
		kq["tong"] = tong
	if tong.get("con_thieu"):
		kq["canh_bao"].append("Grab ghi còn thiếu %s đồng; tiền về sẽ bị trừ." % _so_vn(tong["con_thieu"]))
	if any(d["mo_ta"].endswith("tiền mặt") for d in kq["dong"]):
		kq["canh_bao"].append("Có đơn tiền mặt: thu nhập in trên PDF đã tính cả đơn tiền mặt; đối chiếu số Grab chuyển thật.")
	return kq


# ============================================================ CHUYẾN ĐI

def tien_le(v, kieu="vi", ten="Số tiền", cho_rong=True):
	"""Tiền có thể có số lẻ đồng (Xanh SM 17.153,70). Trả Decimal, chưa làm tròn.

	kieu "vi" = 1.234,56; "en" = 1,234.56; "so" = chuỗi số thuần 1234.56.
	"""
	so = _so(v)
	if so is not None:
		return so
	s = chu(v).replace(" ", "").replace("VND", "")
	if s in ("", "-", "NaN", "nan"):
		if cho_rong:
			return Decimal(0)
		raise LoiDong("Thiếu %s." % ten)
	mau = {"vi": r"-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,8})?",
		"en": r"-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,8})?", "so": r"-?\d+(?:\.\d{1,12})?"}[kieu]
	if not re.fullmatch(mau, s):
		raise LoiDong("%s sai dạng (%s); không đoán." % (ten, s))
	if kieu == "vi":
		s = s.replace(".", "").replace(",", ".")
	elif kieu == "en":
		s = s.replace(",", "")
	return Decimal(s)


def lam_tron(so):
	return int(Decimal(so).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


# ---------- Be for Business

_BE = dict(ma=["ma dat chuyen"], ngay=["ngay"], loai_xe=["loai phuong tien"], diem_don=["diem don"],
	diem_den=["diem den"], cuoc=["cuoc phi van tai"], km=["chiet khau/giam gia"], tong=["tong tien"],
	cktm=["chiet khau thuong mai"], tra=["tong tien thanh toan sau khi tru cktm"])


def nhan_be(tep):
	for t in _trang_luoi(tep):
		dau = " ".join(chuan(v) for h in t["o"][:10] for v in h)
		if "be group" in dau and tim_tieu_de(t["o"], _BE, 30)[0] is not None:
			return "be"
	return None


def doc_be(tep, mau):
	"""Be for Business: bảng kê cước kỳ 26 tháng trước tới 25 tháng này.

	Số phải trả từng chuyến = Tổng tiền trừ chiết khấu thương mại. Tổng kiểm
	là dòng "Tổng số tiền thanh toán trong kỳ". Ô số là chuỗi kiểu Anh "65,000".
	"""
	o = next(t["o"] for t in _trang_luoi(tep) if tim_tieu_de(t["o"], _BE, 30)[0] is not None)
	r0, cot = tim_tieu_de(o, _BE, 30)
	tieu_de = [chuan(v) for v in o[r0]]
	c_ten = next((c for c, v in enumerate(tieu_de) if v == "ten nguoi di"), None)
	c_phi = [c for c, v in enumerate(tieu_de) if v.startswith(("phi cau duong", "phu phi gio cao diem",
		"phi diem don", "phi bao hiem", "phi thong bao"))]
	kq = ket_qua(mau, "chuyen", "Be for Business", "BE")
	for h in o[:r0]:
		s = " ".join(chu(v) for v in h)
		m = re.search(r"từ ngày (\d{1,2}/\d{1,2}/\d{4}) đến ngày (\d{1,2}/\d{1,2}/\d{4})", s, re.I)
		if m:
			kq["tu_ngay"], kq["den_ngay"] = ngay(m.group(1)), ngay(m.group(2))
	tong_tra = None
	for r in range(r0 + 1, len(o)):
		h = o[r]
		if dong_trong(h):
			continue
		dau = chuan(h[0])
		if dau.startswith("tong so tien thanh toan trong ky"):
			v = next((x for x in h[1:] if not rong(x)), None)
			tong_tra = tien_en(v, "Tổng số tiền thanh toán trong kỳ")
			break
		if not chu(h[0]).isdigit():
			continue
		try:
			ma = chu(o_tai(h, cot["ma"]))
			if not ma:
				raise LoiDong("Thiếu Mã đặt chuyến.")
			cuoc = tien_en(o_tai(h, cot["cuoc"]), "Cước phí vận tải")
			phu = sum(tien_en(o_tai(h, c), "Phụ phí", cho_rong=True) for c in c_phi)
			km = tien_en(o_tai(h, cot["km"]), "Chiết khấu/Giảm giá", cho_rong=True)
			tong = tien_en(o_tai(h, cot["tong"]), "Tổng tiền")
			cktm = tien_en(o_tai(h, cot["cktm"]), "Chiết khấu thương mại", cho_rong=True)
			tra = tien_en(o_tai(h, cot["tra"]), "Tổng tiền thanh toán")
			if cuoc + phu - km != tong:
				raise LoiDong("Cước cộng phụ phí trừ giảm giá khác Tổng tiền; kiểm dòng gốc.")
			if tong - cktm != tra:
				raise LoiDong("Tổng tiền trừ chiết khấu thương mại khác số phải trả; kiểm dòng gốc.")
			loai_xe = chu(o_tai(h, cot["loai_xe"]))
			kq["dong"].append(dong_moi(
				ma_su_kien=ma, merchant="BE", ngay=ngay(o_tai(h, cot["ngay"]), "Ngày"), loai="chuyen",
				ma_don=ma, ma_tham_chieu=ma, tien_hang=cuoc + phu, giam_gia=km + cktm, thuc_nhan=tra,
				mo_ta=loai_xe[:60], nguoi=chu(o_tai(h, c_ten))[:60] if c_ten is not None else "",
				giao_hang=chuan(loai_xe).startswith("giao hang")))
		except LoiDong as e:
			them_loi(kq, r + 1, e, h)
	if tong_tra is None:
		kq["loi"].append("Không thấy dòng 'Tổng số tiền thanh toán trong kỳ' của Be.")
	else:
		kiem_tong(kq, dict(thuc_nhan=tong_tra), truong=("thuc_nhan",))
	kq["canh_bao"].append("Be xuất hoá đơn gộp cho cả kỳ sau khi bảng kê được chấp nhận; nối hoá đơn mua theo kỳ và tổng tiền.")
	return khep_ky(kq)


# ---------- Grab for Business (bố cục xuất thẳng từ portal, từ 12/2025)

# chuan() đổi "_" thành khoảng trắng nên tên cột viết theo dạng đã chuẩn.
_GRAB_B = dict(tg=["transaction time"], portal=["portal id"], booking=["booking id"], ten=["employee name"],
	email=["employee email address"], vertical=["vertical"], loai=["taxi type"], base=["base fare"],
	promo=["promo"], toll=["tolls and surcharge"], late=["late fees"], other=["other fees"],
	amount=["amount"], billing=["billing type"], so_hd=["invoice number"], ky_hieu=["vat invoice serial"],
	ngay_hd=["vat invoice date"], order=["order id"])


def nhan_grab_business(tep):
	for t in _trang_luoi(tep):
		if tim_tieu_de(t["o"], _GRAB_B, 3)[0] is not None:
			return "grab_business"
		ten = [chuan(t2["ten"]) for t2 in _trang_luoi(tep)]
		if "hoa don chi tiet" in ten and "tong quan" in ten:
			return "grab_business_cu"
	return None


def doc_grab_business(tep, mau):
	"""Grab for Business: mỗi chuyến một dòng, có số hoá đơn riêng; dòng Admin
	Fee là phí quản lý cả tháng (5% tổng chuyến), cũng có hoá đơn riêng."""
	if mau == "grab_business_cu":
		raise LoiMau("Bảng kê Grab for Business kiểu cũ (4 tab, trước 12/2025) chưa hỗ trợ; tải bản xuất từ portal (1 tab, cột TRANSACTION_TIME).")
	o = next(t["o"] for t in _trang_luoi(tep) if tim_tieu_de(t["o"], _GRAB_B, 3)[0] is not None)
	r0, cot = tim_tieu_de(o, _GRAB_B, 3)
	kq = ket_qua(mau, "chuyen", "Grab for Business", "")
	portal = set()
	for r in range(r0 + 1, len(o)):
		h = o[r]
		if dong_trong(h):
			continue
		try:
			p = chu(o_tai(h, cot["portal"]))
			portal.add(p)
			ng, gio = ngay_gio(chu(o_tai(h, cot["tg"]))[:19], "TRANSACTION_TIME")
			amount = tien_en(o_tai(h, cot["amount"]), "AMOUNT")
			so_hd = chu(o_tai(h, cot["so_hd"]))
			ky_hieu = chu(o_tai(h, cot["ky_hieu"]))
			hd = ("%s#%s" % (ky_hieu, so_hd)) if so_hd else ""
			billing = chuan(o_tai(h, cot["billing"]))
			if billing == "admin fee":
				kq["dong"].append(dong_moi(
					ma_su_kien="admin:%s:%s" % (p, ng[:7]), merchant=p, ngay=ng, gio=gio, loai="phi_quan_ly",
					ma_can_cu=hd or "admin %s" % ng[:7], ma_don=hd, ma_tham_chieu=hd,
					tien_hang=amount, thuc_nhan=amount, mo_ta="Phí quản lý tháng %s" % ng[5:7], hoa_don=hd))
				continue
			booking = chu(o_tai(h, cot["booking"]))
			if not booking:
				raise LoiDong("Thiếu BOOKING_ID ở dòng không phải Admin Fee.")
			base = tien_en(o_tai(h, cot["base"]), "BASE_FARE", cho_rong=True)
			promo = tien_en(o_tai(h, cot["promo"]), "PROMO", cho_rong=True)
			toll = tien_en(o_tai(h, cot["toll"]), "TOLLS", cho_rong=True)
			late = tien_en(o_tai(h, cot["late"]), "LATE_FEES", cho_rong=True)
			other = tien_en(o_tai(h, cot["other"]), "OTHER_FEES", cho_rong=True)
			if base + promo + toll + late + other != amount:
				raise LoiDong("BASE_FARE cộng các khoản khác AMOUNT; kiểm dòng gốc.")
			vertical = chu(o_tai(h, cot["vertical"])).lower()
			kq["dong"].append(dong_moi(
				ma_su_kien=booking, merchant=p, ngay=ng, gio=gio, loai="chuyen", ma_don=chu(o_tai(h, cot["order"])) or booking,
				ma_tham_chieu=booking, tien_hang=amount - promo, giam_gia=-promo, thuc_nhan=amount,
				mo_ta=chu(o_tai(h, cot["loai"]))[:60], nguoi=chu(o_tai(h, cot["ten"]))[:60], hoa_don=hd,
				giao_hang=vertical == "express"))
		except LoiDong as e:
			them_loi(kq, r + 1, e, h)
	if len(portal) == 1:
		kq["tai_khoan"] = "GRABBIZ:" + next(iter(portal))
	elif len(portal) > 1:
		kq["loi"].append("Tệp có nhiều tài khoản portal Grab (%s)." % ", ".join(sorted(portal)))
	m = re.match(r"(\d{2})(\d{2})\s*-", tep["ten"] or "")
	if m:
		y, mo = 2000 + int(m.group(1)), int(m.group(2))
		kq["tu_ngay"] = date(y, mo, 1).isoformat()
		kq["den_ngay"] = (date(y + (mo == 12), mo % 12 + 1, 1).toordinal() - 1) and date.fromordinal(
			date(y + (mo == 12), mo % 12 + 1, 1).toordinal() - 1).isoformat()
	kq["canh_bao"].append("Grab for Business không in dòng tổng; số phải trả là tổng AMOUNT các dòng.")
	return khep_ky(kq)


# ---------- Xanh SM doanh nghiệp (taxi / express)

def nhan_xanh_taxi(tep):
	for t in _trang_luoi(tep):
		dau = " ".join(chuan(v) for h in t["o"][:3] for v in h)
		if "bang ke chuyen di" in dau and tim_tieu_de(t["o"], dict(ma=["ma dat chuyen"], tt=["tong thanh toan"]), 10)[0] is not None:
			return "xanh_taxi"
	return None


def doc_xanh_taxi(tep, mau):
	"""Xanh SM bảng kê chuyến đi doanh nghiệp (ba bố cục T4, T5 trả trước, T7).

	Tiền có số lẻ đồng; phương trình kiểm trên số lẻ, số lưu làm tròn đồng.
	Tổng thanh toán = giá cước + phụ phí - khuyến mại - chiết khấu DN
	(+ phí quản lý trước VAT + VAT nếu có cột phí quản lý).
	"""
	o = next(t["o"] for t in _trang_luoi(tep) if nhan_xanh_taxi(dict(trang=[t])))
	can = dict(ma=["ma dat chuyen"], gc=["gia cuoc"], pp=["phu phi"], km=["tong khuyen mai"], tt=["tong thanh toan"],
		bd=["bat dau (utc+7)"])
	r0, cot = tim_tieu_de(o, can, 10)
	td = [chuan(v).lstrip("'") for v in o[r0]]

	def c_(ten):
		return next((c for c, v in enumerate(td) if v == ten), None)

	c_ck = c_("so tien chiet khau") if c_("so tien chiet khau") is not None else c_("chiet khau (doanh nghiep)")
	c_ql = c_("phi quan ly truoc vat")
	c_vql = c_("vat phi quan ly")
	c_pb = c_("phong ban")
	c_ten = c_("ten tren the")
	c_nguon = c_("nguon")
	c_dv = c_("dich vu (m)")
	c_hd = c_("so hoa don")
	c_ly_do = next((c for c, v in enumerate(td) if v.startswith("ly do loi") or v.startswith("ghi chu ly do")), None)
	kq = ket_qua(mau, "chuyen", "Xanh SM doanh nghiệp", "XANHSM")
	tieu = " ".join(chu(v) for h in o[:3] for v in h)
	m = re.search(r"Từ\s*(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})", tieu)
	if m:
		kq["tu_ngay"], kq["den_ngay"] = ngay(m.group(1)), ngay(m.group(2))
	if "tra truoc" in chuan(tieu):
		kq["them"]["tra_truoc"] = True
	tong_tt = None
	dem_le = Decimal(0)
	for r in range(r0 + 1, len(o)):
		h = o[r]
		if dong_trong(h):
			continue
		dau = chuan(h[0])
		if dau == "total" or dau.startswith("tong thanh toan"):
			v = o_tai(h, cot["tt"])
			if rong(v):
				v = next((x for x in reversed(h) if not rong(x)), None)
			tong_tt = tien_le(v, "so" if not isinstance(v, str) or "," not in v else "vi", "Tổng thanh toán", cho_rong=False)
			break
		if not chu(h[0]).isdigit():
			continue
		try:
			kieu = "vi" if any(isinstance(x, str) and "," in x for x in h) else "so"
			ma = chu(o_tai(h, cot["ma"]))
			if not ma:
				raise LoiDong("Thiếu Mã đặt chuyến.")
			gc = tien_le(o_tai(h, cot["gc"]), kieu, "Giá cước")
			pp = tien_le(o_tai(h, cot["pp"]), kieu, "Phụ phí")
			km = tien_le(o_tai(h, cot["km"]), kieu, "Tổng khuyến mại")
			ck = tien_le(o_tai(h, c_ck), kieu, "Chiết khấu") if c_ck is not None else Decimal(0)
			ql = (tien_le(o_tai(h, c_ql), kieu, "Phí quản lý") + tien_le(o_tai(h, c_vql), kieu, "VAT phí quản lý")) if c_ql is not None else Decimal(0)
			tt = tien_le(o_tai(h, cot["tt"]), kieu, "Tổng thanh toán", cho_rong=False)
			if abs(gc + pp - km - ck + ql - tt) > Decimal("0.05"):
				raise LoiDong("Giá cước cộng phụ phí trừ khuyến mại, chiết khấu (cộng phí quản lý) khác tổng thanh toán.")
			dem_le += tt
			bd = o_tai(h, cot["bd"])
			ng, gio = ngay_gio(chu(bd)[:19] if isinstance(bd, str) else bd, "Bắt đầu")
			loai = "chuyen"
			ly_do = chu(o_tai(h, c_ly_do)) if c_ly_do is not None else ""
			can_cu = ""
			if gc == 0 and tt < 0:
				loai = "dieu_chinh"
				can_cu = (ma + " " + ly_do).strip()
			nguon = chu(o_tai(h, c_nguon)).lower() if c_nguon is not None else ""
			kq["dong"].append(dong_moi(
				ma_su_kien="%s:%s" % (ma, kq["den_ngay"] or ng[:7]) if loai == "dieu_chinh" else ma,
				merchant=chu(o_tai(h, c_pb)) if c_pb is not None else "", ngay=ng, gio=gio, loai=loai,
				ma_don=ma, ma_tham_chieu=ma, ma_can_cu=can_cu, tien_hang=lam_tron(gc + pp + ql),
				giam_gia=lam_tron(km + ck), thuc_nhan=lam_tron(tt), dieu_chinh=lam_tron(tt) if loai == "dieu_chinh" else 0,
				mo_ta=(chu(o_tai(h, c_dv)) if c_dv is not None else "")[:60],
				nguoi=chu(o_tai(h, c_ten))[:60] if c_ten is not None else "",
				hoa_don=chu(o_tai(h, c_hd)) if c_hd is not None else "", giao_hang=nguon == "express"))
		except LoiDong as e:
			them_loi(kq, r + 1, e, h)
	if tong_tt is None:
		kq["loi"].append("Không thấy dòng Total của bảng kê Xanh SM.")
	elif not kq["dong_loi"] and abs(dem_le - tong_tt) > Decimal("0.5"):
		kq["loi"].append("Tổng thanh toán các dòng %s khác dòng Total %s." % (dem_le, tong_tt))
	kq["tong"] = dict(thuc_nhan=lam_tron(tong_tt)) if tong_tt is not None else None
	if kq["tong"] and not kq["dong_loi"]:
		lech = lam_tron(tong_tt) - sum(d["thuc_nhan"] for d in kq["dong"])
		if lech:
			kq["canh_bao"].append("Làm tròn từng chuyến lệch %s đồng so với dòng Total; số phải trả theo dòng Total." % lech)
	return khep_ky(kq)


# ============================================================ THẺ TÍN DỤNG SHINHAN

_RE_THE_GD = re.compile(r"^\s*(\d{2}-\d{2}-\d{4})\s+(\d{2}-\d{2}-\d{4})\s+(.+?)\s{2,}(?:([A-Z]{2}/\S.*?)\s+)?([A-Z]{3})\s+(-?[\d,]+\.\d{2})\s+(-?[\d,]+)(\s*CR)?\s*$")


def nhan_the_shinhan(tep):
	dong = _dong_pdf(tep)[:30]
	if any(d.strip() == "Sao Kê" for d in dong) and any("Chu kỳ sao kê" in d for d in dong):
		return "the_shinhan"
	return None


def _vnd_the(s):
	s = s.replace("VND", "").replace(" ", "").replace(",", "")
	try:
		return lam_tron(Decimal(s))
	except InvalidOperation:
		raise LoiDong("Số tiền sao kê thẻ sai dạng (%s)." % s) from None


def doc_the_shinhan(tep, mau):
	"""Sao kê thẻ tín dụng Shinhan (PDF một trang, có lớp chữ).

	Giao dịch thuộc kỳ theo ngày bút toán. Sao kê không in đầu kỳ và khoản
	đã trả; hai số đó dựng ở máy chủ từ sao kê kỳ trước (doi_soat_vendor).
	Kiểm trong tệp: tổng phát sinh = Your Spend, tổng phí = Fees, Spend + Fees
	= Billing Amount = Đến hạn thanh toán của tháng này.
	"""
	dong = _dong_pdf(tep)
	van = "\n".join(dong)
	kq = ket_qua(mau, "the", "Thẻ tín dụng Shinhan", "")
	m = re.search(r"Chu kỳ sao kê\s+(\d{2}/\d{2}/\d{4})\s*~\s*(\d{2}/\d{2}/\d{4})", van)
	if not m:
		raise LoiMau("Không thấy chu kỳ sao kê trên PDF thẻ Shinhan.")
	kq["tu_ngay"], kq["den_ngay"] = ngay(m.group(1)), ngay(m.group(2))
	ms = re.search(r"Ngày sao kê\s+(\d{2}/\d{2}/\d{4})", van)
	mh = re.search(r"Ngày đến hạn thanh toán\s+(\d{2}/\d{2}/\d{4})", van)
	tk = re.search(r"Tài khoản thanh toán\s*:\s*(\S+)", van)
	kq["tai_khoan"] = "SHB-THE:" + tk.group(1) if tk else ""
	if not tk:
		kq["loi"].append("Không thấy số tài khoản thanh toán trên sao kê thẻ; tải đúng PDF gốc ngân hàng gửi.")
	so = {}
	for nhan, khoa in (("Khoản tiền chưa thanh toán", "chua_tra_truoc"), ("Phí chậm trả", "phi_cham"),
			("Đến hạn thanh toán của", "den_han_thang"), ("Đến hạn thanh toán ", "den_han")):
		pass
	# Các ô số đứng lẫn dòng chữ nhãn; lấy theo thứ tự xuất hiện của "VND x.xx".
	vnd = [(i, x) for i, d in enumerate(dong) for x in re.findall(r"VND\s+(-?[\d,]+\.\d{2})", d)
		if "Chi tiết sao kê" not in d]
	dau_ct = next((i for i, d in enumerate(dong) if d.strip() == "Chi tiết sao kê"), len(dong))
	vnd = [x for i, x in vnd if i < dau_ct]
	if len(vnd) >= 4:
		so = dict(chua_tra_truoc=_vnd_the(vnd[0]), phi_cham=_vnd_the(vnd[1]), den_han_thang=_vnd_the(vnd[2]),
			den_han=_vnd_the(vnd[3]))
	else:
		kq["loi"].append("Không đọc đủ bốn ô số tiền đầu sao kê (chưa trả tháng trước, phí chậm trả, đến hạn).")
	the4 = ""
	sau_spend = False
	spend = fees = billing = None
	dem = {}
	for i, d in enumerate(dong[dau_ct:], dau_ct):
		s = d.strip()
		mc = re.search(r"Card\s+Number\s+(\S+)", s)
		if mc:
			the4 = mc.group(1)[-4:]
			continue
		if s.startswith("Your Spend For This Month"):
			spend = _vnd_the(s.split()[-1])
			sau_spend = True
			continue
		if s.startswith("Fees") and re.fullmatch(r"Fees\s+[\d,]+", s):
			fees = _vnd_the(s.split()[-1])
			continue
		if s.startswith("Billing Amount of the Current Month"):
			billing = _vnd_the(s.split()[-1])
			continue
		mg = _RE_THE_GD.match(d)
		if not mg:
			continue
		try:
			ngd, nbt, dv, qg, tien_te, goc, vnd_, cr = mg.groups()
			tien = _vnd_the(vnd_) * (-1 if cr else 1)
			dv = re.sub(r"\s+", " ", dv).strip()
			loai = "phi" if (sau_spend or not qg) else ("hoan" if tien < 0 else "phat_sinh")
			if "interest" in dv.lower() or "lãi" in dv.lower():
				loai = "lai"
			ngay_bt = ngay(nbt, "Ngày bút toán")
			goc_ = "%s:%s:%s:%s:%s" % (the4, ngay(ngd), ngay_bt, dv, tien)
			dem[goc_] = dem.get(goc_, 0) + 1
			kq["dong"].append(dong_moi(
				ma_su_kien="%s:%s" % (goc_, dem[goc_]), merchant=the4, ngay=ngay_bt, loai=loai,
				ma_don=dv[:60], ma_tham_chieu=dv[:60], ma_can_cu=dv[:60] if loai in ("phi", "lai") else "",
				tien_hang=tien, thuc_nhan=tien, mo_ta=("%s %s" % (dv, qg or "")).strip()[:120],
				them=dict(ngay_gd=ngay(ngd), tien_goc=goc, tien_te=tien_te)))
		except LoiDong as e:
			them_loi(kq, i + 1, e, [d])
	if spend is None or billing is None:
		kq["loi"].append("Không thấy dòng Your Spend For This Month hoặc Billing Amount; PDF có thể bị cắt.")
	elif not kq["dong_loi"]:
		ps = sum(d["thuc_nhan"] for d in kq["dong"] if d["loai"] in ("phat_sinh", "hoan"))
		ph = sum(d["thuc_nhan"] for d in kq["dong"] if d["loai"] in ("phi", "lai"))
		if ps != spend:
			kq["loi"].append("Cộng giao dịch %s khác Your Spend %s." % (_so_vn(ps), _so_vn(spend)))
		if ph != (fees or 0):
			kq["loi"].append("Cộng phí %s khác dòng Fees %s." % (_so_vn(ph), _so_vn(fees or 0)))
		if spend + (fees or 0) != billing:
			kq["loi"].append("Your Spend cộng Fees khác Billing Amount.")
		if so and so["den_han_thang"] != billing:
			kq["loi"].append("Đến hạn thanh toán của tháng này khác Billing Amount.")
		if so and so["chua_tra_truoc"] + so["phi_cham"] + so["den_han_thang"] != so["den_han"]:
			kq["loi"].append("Chưa trả tháng trước + phí chậm trả + đến hạn tháng này khác Đến hạn thanh toán.")
	kq["tong"] = dict(spend=spend, fees=fees or 0, billing=billing, thuc_nhan=billing, **so)
	kq["them"].update(ngay_sao_ke=ngay(ms.group(1)) if ms else "", ngay_den_han=ngay(mh.group(1)) if mh else "",
		the=sorted({d["merchant"] for d in kq["dong"]}))
	kq["ngay_tien_ve"] = kq["them"]["ngay_den_han"]
	return kq


_THE_BANG = dict(ngay_gd=["ngay giao dich"], ngay_bt=["ngay but toan"], dv=["don vi chap nhan the"],
	goc=["so tien goc"], vnd=["so tien(vnd)", "so tien (vnd)", "so tien vnd"])


def nhan_the_shinhan_bang(tep):
	"""Sao kê thẻ Shinhan gõ tay sang Excel (#457, chị Dung 08/10/2026): ngân
	hàng gửi sao kê dạng ảnh, kế toán gõ lại theo đúng sáu cột của bảng Chi
	tiết sao kê. Nhận bằng tiêu đề cột, không cần dòng Chu kỳ sao kê."""
	for t in _trang_luoi(tep):
		if tim_tieu_de(t["o"], _THE_BANG, 5)[0] is not None:
			return "the_shinhan_bang"
	return None


def _vnd_bang(v):
	"""Ô tiền VND gõ tay: "1,018,559 ", "38,384,995", 1018559, "-500,000", "500,000 CR"."""
	if isinstance(v, (int, float)) and not isinstance(v, bool):
		return lam_tron(Decimal(str(v)))
	s = chu(v).strip()
	am = s.upper().endswith("CR") or s.startswith("-")
	s = re.sub(r"[^0-9.]", "", s)
	if not s:
		raise LoiDong("Số tiền VND trống.")
	try:
		t = lam_tron(Decimal(s))
	except InvalidOperation:
		raise LoiDong("Số tiền VND sai dạng (%s)." % chu(v)) from None
	return -t if am else t


def doc_the_shinhan_bang(tep, mau):
	"""Đọc bảng gõ tay. Cùng khuôn kết quả với doc_the_shinhan (PDF) để phần
	đối soát thẻ dùng chung: dòng phát sinh, phí, tổng spend, fees, billing.

	Khác PDF: tệp không có chu kỳ sao kê, ngày đến hạn, tài khoản thanh toán,
	bốn ô số đầu sao kê. Kỳ lấy theo THÁNG của ngày bút toán lớn nhất, tài
	khoản ghi theo bốn số cuối thẻ; cả hai ghi vào cảnh báo để kế toán biết
	là máy suy ra chứ không đọc từ ngân hàng.
	"""
	luoi = _trang_luoi(tep)
	o = next(t["o"] for t in luoi if tim_tieu_de(t["o"], _THE_BANG, 5)[0] is not None)
	r0, cot = tim_tieu_de(o, _THE_BANG, 5)
	kq = ket_qua(mau, "the", "Thẻ tín dụng Shinhan", "")
	the4 = ""
	spend = fees = billing = None
	sau_spend = False
	dem = {}
	for r in range(r0 + 1, len(o)):
		h = o[r]
		if dong_trong(h):
			continue
		dv = re.sub(r"\s+", " ", chu(o_tai(h, cot["dv"]))).strip()
		ngd, nbt = chu(o_tai(h, cot["ngay_gd"])).strip(), chu(o_tai(h, cot["ngay_bt"])).strip()
		vnd_o = o_tai(h, cot["vnd"])
		if chuan(ngd) == "card" and chuan(nbt) == "number":
			the4 = re.sub(r"[^0-9X]", "", dv.upper())[-4:]
			continue
		dvc = chuan(dv)
		if dvc.startswith("your spend for this month"):
			spend = _vnd_bang(vnd_o)
			sau_spend = True
			continue
		if dvc == "fees":
			fees = _vnd_bang(vnd_o)
			continue
		if dvc.startswith("billing amount of the current month"):
			billing = _vnd_bang(vnd_o)
			continue
		if not ngd and not nbt:
			continue
		try:
			if not dv:
				raise LoiDong("Thiếu Đơn vị chấp nhận thẻ.")
			ngay_bt = ngay(nbt, "Ngày bút toán")
			tien = _vnd_bang(vnd_o)
			goc_chu = chu(o_tai(h, cot["goc"])).strip()
			mg = re.match(r"^([A-Z]{3})\s*(-?[\d,]+(?:\.\d+)?)$", goc_chu)
			tien_te, goc = (mg.group(1), mg.group(2)) if mg else ("VND", goc_chu)
			qg = chu(o_tai(h, cot.get("qg"))).strip() if "qg" in cot else ""
			loai = "phi" if sau_spend else ("hoan" if tien < 0 else "phat_sinh")
			if "interest" in dv.lower() or "lãi" in dv.lower():
				loai = "lai"
			goc_ = "%s:%s:%s:%s:%s" % (the4, ngay(ngd, "Ngày giao dịch") if ngd else ngay_bt, ngay_bt, dv, tien)
			dem[goc_] = dem.get(goc_, 0) + 1
			kq["dong"].append(dong_moi(
				ma_su_kien="%s:%s" % (goc_, dem[goc_]), merchant=the4, ngay=ngay_bt, loai=loai,
				ma_don=dv[:60], ma_tham_chieu=dv[:60], ma_can_cu=dv[:60] if loai in ("phi", "lai") else "",
				tien_hang=tien, thuc_nhan=tien, mo_ta=("%s %s" % (dv, qg)).strip()[:120],
				them=dict(ngay_gd=ngay(ngd) if ngd else "", tien_goc=goc, tien_te=tien_te, go_tay=1)))
		except LoiDong as e:
			them_loi(kq, r + 1, e, [chu(x) for x in h])
	if not the4:
		kq["loi"].append("Không thấy dòng Card Number (bốn số cuối thẻ) trong bảng; gõ thêm dòng đó dưới tiêu đề.")
	if spend is None or billing is None:
		kq["loi"].append("Không thấy dòng Your Spend For This Month hoặc Billing Amount of the Current Month; gõ đủ hai dòng tổng.")
	elif not kq["dong_loi"]:
		ps = sum(d["thuc_nhan"] for d in kq["dong"] if d["loai"] in ("phat_sinh", "hoan"))
		ph = sum(d["thuc_nhan"] for d in kq["dong"] if d["loai"] in ("phi", "lai"))
		if ps != spend:
			kq["loi"].append("Cộng giao dịch %s khác Your Spend %s; kiểm lại số gõ tay." % (_so_vn(ps), _so_vn(spend)))
		if ph != (fees or 0):
			kq["loi"].append("Cộng phí %s khác dòng Fees %s." % (_so_vn(ph), _so_vn(fees or 0)))
		if spend + (fees or 0) != billing:
			kq["loi"].append("Your Spend cộng Fees khác Billing Amount.")
	if kq["dong"]:
		cuoi = max(d["ngay"] for d in kq["dong"])
		y, mo = int(cuoi[:4]), int(cuoi[5:7])
		kq["tu_ngay"] = "%04d-%02d-01" % (y, mo)
		kq["den_ngay"] = ((date(y + (mo == 12), mo % 12 + 1, 1)) - timedelta(days=1)).isoformat()
		kq["canh_bao"].append("Bảng gõ tay không có chu kỳ sao kê; máy lấy kỳ là tháng %02d/%04d theo ngày bút toán. Ngày đến hạn và tài khoản thanh toán cũng không có, đối chiếu tay với sao kê ảnh." % (mo, y))
	kq["tai_khoan"] = "SHB-THE:%s" % the4 if the4 else ""
	kq["tong"] = dict(spend=spend, fees=fees or 0, billing=billing, thuc_nhan=billing)
	kq["them"].update(ngay_sao_ke="", ngay_den_han="", the=sorted({d["merchant"] for d in kq["dong"]}), go_tay=1)
	return kq


# ============================================================ BẢNG MẪU

MAU = [
	# (khoá, nhận, đọc, tên hiển thị, nhóm)
	("payoo", nhan_payoo, doc_payoo, "Payoo", "ban"),
	("onepay", nhan_onepay, None, "OnePay", "ban"),
	("shinhan", nhan_shinhan, doc_shinhan, "Shinhan POS", "ban"),
	("shopeefood", nhan_shopee, doc_shopee, "ShopeeFood", "ban"),
	("greensm_ngon", nhan_greensm, doc_greensm, "Xanh SM Ngon", "ban"),
	("grabfood", nhan_grab, doc_grab, "GrabFood", "ban"),
	("be", nhan_be, doc_be, "Be for Business", "chuyen"),
	("grab_business", nhan_grab_business, doc_grab_business, "Grab for Business", "chuyen"),
	("xanh_taxi", nhan_xanh_taxi, doc_xanh_taxi, "Xanh SM doanh nghiệp", "chuyen"),
	("the_shinhan", nhan_the_shinhan, doc_the_shinhan, "Thẻ tín dụng Shinhan", "the"),
	("the_shinhan_bang", nhan_the_shinhan_bang, doc_the_shinhan_bang, "Thẻ tín dụng Shinhan (bảng gõ tay)", "the"),
]

TEN_MAU = {
	"payoo_the": "Payoo thẻ", "payoo_qr": "Payoo QR", "onepay_ngay": "OnePay tạm ứng ngày",
	"onepay_thang": "OnePay chi tiết tháng", "onepay_bbds": "OnePay biên bản tháng",
	"shinhan_ngay": "Shinhan POS ngày", "shinhan_thang": "Shinhan POS tháng", "shopeefood": "ShopeeFood",
	"greensm_ngon": "Xanh SM Ngon", "grabfood": "GrabFood", "be": "Be for Business",
	"grab_business": "Grab for Business", "grab_business_cu": "Grab for Business (kiểu cũ)",
	"xanh_taxi": "Xanh SM doanh nghiệp", "the_shinhan": "Thẻ tín dụng Shinhan", "the_shinhan_bang": "Thẻ tín dụng Shinhan (bảng gõ tay)",
}


def dau_tep(tep, so_dong=3, rong_toi_da=160):
	"""THUẦN (#457 mục 3). Ba dòng đầu có chữ của tệp để người dùng và kỹ thuật
	biết máy đã đọc được gì khi chưa nhận ra mẫu. Mỗi dòng ghép ô bằng " | ",
	cắt ngắn, không lộ quá rong_toi_da ký tự."""
	ra = []
	for tr in tep.get("trang") or []:
		for h in tr.get("o") or []:
			if not h or all(rong(v) for v in h):
				continue
			chu = " | ".join(str(v).strip() for v in h if not rong(v))
			ra.append(chu[:rong_toi_da] + ("..." if len(chu) > rong_toi_da else ""))
			if len(ra) >= so_dong:
				return ra
	return ra


def nhan_dien(tep):
	"""Trả khoá mẫu chi tiết (ví dụ "payoo_the") hoặc None. Thử theo thứ tự
	bảng MAU; mỗi hàm nhận chỉ đọc vài dòng đầu nên rẻ."""
	for _k, nhan, _d, _t, _n in MAU:
		try:
			m = nhan(tep)
		except Exception:
			m = None
		if m:
			return m
	return None


def doc(tep, mau=None):
	"""Nhận diện rồi đọc. Lỗi cấp mẫu trả kết quả rỗng có lý do, không ném."""
	mau = mau or nhan_dien(tep)
	if not mau:
		kq = ket_qua("", "", "", "")
		kq["loi"].append("Chưa nhận ra mẫu báo cáo của tệp này. Bấm Lưu nguồn để máy giữ tệp trong mục "
			"Mẫu chưa nhận, rồi gửi tệp này cho kỹ thuật thêm mẫu. Không cần làm gì thêm.")
		kq["them"]["dau_tep"] = dau_tep(tep)
		kq["them"]["mau_chua_nhan"] = 1
		return kq
	if mau.startswith("onepay"):
		ham = doc_onepay_bbds if mau == "onepay_bbds" else doc_onepay
	else:
		# Khớp đúng khoá trước, rồi mới khớp tiền tố (#457: "the_shinhan_bang"
		# không được rơi vào "the_shinhan").
		ham = next((d for k, n, d, t, _n in MAU if k == mau), None) or next(d for k, n, d, t, _n in MAU if mau.startswith(k))
	try:
		return ham(tep, mau)
	except LoiMau as e:
		kq = ket_qua(mau, next((n for k, _x, _d, _t, n in MAU if k == mau), next((n for k, _x, _d, _t, n in MAU if mau.startswith(k)), "")), TEN_MAU.get(mau, mau), "")
		kq["loi"].append(str(e))
		return kq
