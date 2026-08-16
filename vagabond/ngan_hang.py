"""Danh muc ngan hang va tep chuyen tien lo cua MB Biz.

MOT NGUON SU THAT cho ca hai thu (anh Viet chot 17/08/2026)
-----------------------------------------------------------
Truoc tep nay, moi cho tu lo mot kieu:

  - Man hoan tien cho GO TAY ten ngan hang. Anh go "MB" thi may nem loi
    "Khong tim thay Ngan hang: MB", vi o do la mot o Link tro vao doctype
    Bank ma ten day du la "MB - Ngan hang TMCP Quan doi".
  - Ho so thanh toan APP dung mot o Data tu do, go gi cung duoc.
  - Cau truc cot tep lo MB nam trong ma frontend cua ho so thanh toan.

Ba cho, ba cach, va khong cho nao biet cho nao. Do dung la cai bay da lam
hong ba viec trong ngay 16/08/2026 (hai cho dinh tuyen, hai duong doi soat,
regex chep hai ban). Nen lan nay gom lai truoc khi no kip lech.

Danh muc lay tu dau
-------------------
Tep eMB_BulkPayment.xlsx cua MB Biz, tab "Danh sach ngan hang - Bank list",
581 ngan hang. Chinh MB khuyen nghi trong tab Huong dan: "Khuyen nghi copy
truong Ten ngan hang day du tai tab DS ngan hang". Nen ten trong doctype
Bank cua minh de DUNG Y NGUYEN chuoi do, khong rut gon, khong dich lai.

Vi sao khong dung MA ngan hang lam khoa: trong 581 dong co 468 dong trung
ma, vi mot ma co nhieu chi nhanh (KBNN, NHNN, SINOPAC...). Ten day du moi
la thu duy nhat khong trung.
"""

import json
import os
import re

import frappe
from frappe.utils import cint, flt

DUONG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "du_lieu", "napas.json")


def doc_danh_muc():
	"""Doc 581 ngan hang tu tep du lieu. Tra list [(ten, hinh_thuc)]."""
	try:
		with open(DUONG, encoding="utf-8") as f:
			return [(str(x[0]).strip(), str(x[1]).strip()) for x in json.load(f) if x and x[0]]
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ngan_hang: doc danh muc loi")
		return []


def nap_danh_muc():
	"""Nap 581 ngan hang vao doctype Bank. LAP LAI DUOC.

	Goi tu patch dong_bo_cau_truc nen moi lan Migrate deu duoc chay lai.

	KHONG dung vao ngan hang da co: chung dang duoc mot so Bank Account tro
	toi, doi ten la lam mo coi cac tai khoan do. Chi THEM cai con thieu.
	"""
	ds = doc_danh_muc()
	if not ds:
		return {"them": 0, "da_co": 0, "loi": "Khong doc duoc danh muc"}
	da_co = {d["name"] for d in frappe.get_all("Bank", fields=["name"], limit_page_length=0)}
	them = 0
	for ten, _ht in ds:
		if ten in da_co:
			continue
		try:
			doc = frappe.get_doc({"doctype": "Bank", "bank_name": ten})
			doc.flags.ignore_permissions = True
			doc.insert(ignore_permissions=True)
			them += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ngan_hang: nap %s loi" % ten[:60])
	if them:
		frappe.db.commit()
	return {"them": them, "da_co": len(da_co), "tong_danh_muc": len(ds)}


# Tra HET danh muc trong mot lan goi. 581 dong la khoang 60 KB, tai mot lan
# roi app giu lai; con tra tung khuc thi o tim nhanh cua ham sheet() chi loc
# duoc trong khuc da tai, va nhan vien go "Vietcombank" se khong thay gi neu
# no roi ngoai khuc dau.
#
# Bat duoc ngay sau khi deploy v195: mac dinh cu la 60, nen app chi nhan 60
# ngan hang dau bang chu cai va thieu 521 cai con lai - khong bao gi.
SO_DONG_MAC_DINH = 600


@frappe.whitelist()
def tim(tu_khoa="", so_dong=None):
	"""O chon ngan hang tren app goi ham nay.

	Tra ve danh sach de dung voi ham sheet() cua app: moi phan tu co k (gia
	tri that, la ten day du) va ten (chu hien tren man).

	Tim theo CA MA LAN TEN, khong phan biet hoa thuong va khong phan biet
	dau: go "MB", "quan doi" hay "Quân đội" deu ra Ngan hang TMCP Quan doi.
	Vi sao: nhan vien quay go nhanh tren dien thoai, bat go dung dau tieng
	Viet la bat go lai ba lan.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	tk = _khong_dau(tu_khoa)
	ds = doc_danh_muc()
	if not ds:
		# Roi ve doctype Bank neu tep du lieu hong - man van dung duoc.
		ds = [(d["name"], "") for d in frappe.get_all("Bank", fields=["name"], limit_page_length=0)]
	tran = max(1, min(SO_DONG_MAC_DINH, cint(so_dong) or SO_DONG_MAC_DINH))
	ra = []
	for ten, ht in ds:
		kd = _khong_dau(ten)
		if tk and tk not in kd:
			continue
		# Gui kem ban KHONG DAU de o tim nhanh cua ham sheet() ben app loc
		# duoc ma khong bat nhan vien go dau: sheet() so chuoi tho, nen neu
		# khong gui ban nay thi go "quan doi" se khong ra "Quân đội".
		ra.append({"k": ten, "ten": ten, "tim": kd, "hinh_thuc": ht})
		if len(ra) >= tran:
			break
	return {"ds": ra, "tong": len(ds), "co_tu_khoa": 1 if tk else 0}


def _khong_dau(s):
	"""Bo dau tieng Viet va viet thuong, de so chuoi khong phan biet dau."""
	import unicodedata

	s = unicodedata.normalize("NFD", str(s or ""))
	s = "".join(c for c in s if unicodedata.category(c) != "Mn")
	return s.replace("đ", "d").replace("Đ", "D").lower().strip()


# ==================================================================
# Tep chuyen tien lo MB Biz
# ==================================================================
#
# Cau truc SAU cot, doc tu chinh tep mau eMB_BulkPayment.xlsx cua MB:
#
#   (1) STT                          chi chu so
#   (2) So tai khoan                 toi da 24 ky tu, KHONG dau cach
#   (3) Ten don vi thu huong         toi da 69 ky tu
#   (4) Ngan hang thu huong          ten day du tu tab Bank list
#   (5) So tien                      VND, khong thap phan
#   (6) Chi tiet thanh toan          toi da 140 ky tu
#
# Moi nut "Xuat MB Biz" tren app deu goi ham o day. KHONG dung cau truc cot
# trong ma frontend nua - anh Viet chot 17/08/2026.

COT_MB = [
	"STT",
	"Số tài khoản",
	"Tên đơn vị thụ hưởng",
	"Ngân hàng thụ hưởng/Chi nhánh",
	"Số tiền",
	"Chi tiết thanh toán",
]

DAI_TOI_DA = {"so_tk": 24, "ten": 69, "noi_dung": 140}

# Quy tac thay ky tu dac biet, chep tu tab Huong dan cua chinh tep MB.
#
# Vi sao phai lam o day chu khong de MB tu thay: MB noi "ngay sau khi upload
# file, ky tu dac biet SE DUOC THAY THE". Nghia la noi dung ke toan nhin
# thay luc go KHAC voi noi dung ve tren sao ke. Ma doi soat cua minh do theo
# noi dung sao ke. Nen minh phai thay TRUOC, de cai minh luu va cai ngan
# hang tra ve la mot.
_THAY_TIEN = [("&", "VA")]
_THAY_ND = [("&", "VA"), ("%", "PT"), ("=", "BANG"), ("€", "EURO"), ("£", "BANG ANH"), ("$", "DO LA MY")]
_XOA = "()[]{}<>"
_THANH_CHAM = "!@#^*-_+\\|`~,/?;:”’'\""


def sach_ten(chu):
	"""Lam sach o Ten don vi thu huong va So tai khoan. THUAN."""
	s = _bo_dau(chu).upper()
	for a, b in _THAY_TIEN:
		s = s.replace(a, b)
	s = "".join(" " if c in _THANH_CHAM else ("" if c in _XOA else c) for c in s)
	s = re.sub(r"[^A-Z0-9 .]", "", s)
	return re.sub(r"\s+", " ", s).strip()


def sach_noi_dung(chu):
	"""Lam sach o Chi tiet thanh toan. THUAN.

	Giu lai dau GACH NGANG, vi ma hoa don cua minh la HDB-26-08-00323 va
	dau gach do la thu giup doi soat doc lai duoc ma. MB cho phep dau gach
	trong giao dich noi bo MB; voi giao dich ra ngoai thi no bi thay, va
	ham khop_giao_dich ben hoan_tien.py da co duong got de van bat duoc.
	"""
	s = _bo_dau(chu).upper()
	for a, b in _THAY_ND:
		s = s.replace(a, b)
	s = "".join("" if c in _XOA else c for c in s)
	s = re.sub(r"[^A-Z0-9 \-.]", " ", s)
	return re.sub(r"\s+", " ", s).strip()


def sach_so_tk(chu):
	"""So tai khoan: chi chu va so, KHONG dau cach. THUAN."""
	return re.sub(r"[^A-Za-z0-9]", "", str(chu or "")).upper()[: DAI_TOI_DA["so_tk"]]


def _bo_dau(s):
	import unicodedata

	s = unicodedata.normalize("NFD", str(s or ""))
	s = "".join(c for c in s if unicodedata.category(c) != "Mn")
	return s.replace("đ", "d").replace("Đ", "D")


def dong_mb(stt, so_tk, ten_nhan, ngan_hang, so_tien, noi_dung):
	"""Mot dong cua tep lo MB. THUAN. Tra (dong, list cau nhac).

	Cat theo do dai toi da CHU KHONG nem loi: mot ten dai 70 ky tu khong
	dang lam ke toan khong xuat duoc tep. Nhung phai NOI ra la da cat, chu
	khong lang le cat.
	"""
	nhac = []
	tk = sach_so_tk(so_tk)
	if not tk:
		nhac.append("Chưa có số tài khoản")
	ten = sach_ten(ten_nhan)
	if len(ten) > DAI_TOI_DA["ten"]:
		ten = ten[: DAI_TOI_DA["ten"]].strip()
		nhac.append("Tên người thụ hưởng dài quá %d ký tự nên đã cắt bớt" % DAI_TOI_DA["ten"])
	nd = sach_noi_dung(noi_dung)
	if len(nd) > DAI_TOI_DA["noi_dung"]:
		nd = nd[: DAI_TOI_DA["noi_dung"]].strip()
		nhac.append("Nội dung dài quá %d ký tự nên đã cắt bớt" % DAI_TOI_DA["noi_dung"])
	nh = str(ngan_hang or "").strip()
	if not nh:
		nhac.append("Chưa chọn ngân hàng")
	tien = int(round(flt(so_tien)))
	if tien <= 0:
		nhac.append("Số tiền phải lớn hơn 0")
	return [cint(stt), tk, ten, nh, tien, nd], nhac


@frappe.whitelist()
def tep_lo(dong=None):
	"""Dung tep lo MB Biz tu danh sach lenh chi. MOT CUA DUY NHAT.

	dong: list dict, moi cai co so_tk, ten_nhan, ngan_hang, so_tien, noi_dung.

	Tra ve:
	  cot       - tieu de sau cot, dung thu tu cua MB
	  bang      - list cac dong da lam sach
	  tsv       - ca bang ngan bang Tab, dan thang vao Excel duoc
	  nhac      - cac cau canh bao theo tung dong
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if isinstance(dong, str):
		try:
			dong = json.loads(dong)
		except Exception:
			frappe.throw("Danh sách lệnh chi không đọc được. Báo em để kiểm tra lại.")
	if not dong:
		frappe.throw("Chưa có lệnh chi nào để xuất. Chọn ít nhất một phiếu rồi bấm lại.")

	bang, nhac = [], []
	for i, d in enumerate(dong, 1):
		r, n = dong_mb(
			i,
			d.get("so_tk"),
			d.get("ten_nhan"),
			d.get("ngan_hang"),
			d.get("so_tien"),
			d.get("noi_dung"),
		)
		bang.append(r)
		for c in n:
			nhac.append("Dòng %d (%s): %s" % (i, d.get("ten_nhan") or "?", c))

	tsv = "\t".join(COT_MB) + "\n" + "\n".join("\t".join(str(x) for x in r) for r in bang)
	return {
		"cot": COT_MB,
		"bang": bang,
		"tsv": tsv,
		"nhac": nhac,
		"so_dong": len(bang),
		"tong_tien": sum(r[4] for r in bang),
		"nhac_lo": (
			"MB yêu cầu tệp lô có ít nhất 2 giao dịch. Một lệnh thì chuyển thẳng trên "
			"MB Biz, không cần tệp."
			if len(bang) < 2
			else ""
		),
	}
