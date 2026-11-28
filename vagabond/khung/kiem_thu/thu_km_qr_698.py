# -*- coding: utf-8 -*-
"""v698 (Dễ báo 27/11/2026): bill gọi món qua QR tại bàn, quầy bấm Chương trình
thì mọi dòng đều "Không áp được".

Hai nguyên nhân, anh Việt chốt cách sửa cùng ngày:
- Voucher Grab Dine Out chỉ mở cho kênh Tại chỗ, bill QR mang nguồn "QR tại bàn".
  Quầy áp thì xét kênh như bill Tại chỗ; khách tự chọn trên trang bàn vẫn xét
  theo nguồn gốc (khách không tự lấy được voucher Grab).
- Chương trình Tặng món đủ điều kiện nhưng món tặng chưa có trong bill thì giảm 0
  và báo "chưa đủ điều kiện". Anh chọn "Tự thêm món tặng": quầy bấm là máy thêm
  dòng món tặng (giá quầy) rồi trừ đúng số đó, như nút "+ Thêm món tặng vào đơn"
  của màn Tính tiền.

Ca chạm hệ chạy THẬT uu_dai_ban.ds_quay, ap_quay, truoc_chot và THẬT
khuyen_mai.ds_ctkm, khuyen_mai.tinh (luật kênh, thời gian, Tặng món), chỉ thay
phần đọc bảng (Vagabond CTKM, Item Price, Item) bằng dữ liệu GIẢ.
"""
import contextlib
import json
import os
import subprocess
import sys
import types
from unittest.mock import patch

import vagabond
from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
_fr = sys.modules["frappe"]

# Bộ ca 643 dựng sẵn frappe.rate_limiter giả và hoá đơn giả trước khi nạp uu_dai_ban.
from vagabond.khung.kiem_thu.thu_uu_dai_ban_643 import _hd  # noqa: E402,I100
from vagabond import goi_mon_ban, khuyen_mai  # noqa: E402
from vagabond import uu_dai_ban as u  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BANH = "GIA-BANH01"


def _km(name, ten, **k):
	d = dict(name=name, ten=ten, bat=1, cach_thuc="Giam tong hoa don", kieu_giam="So tien", gia_tri=0, gia_dong=0,
		uu_tien=0, cach_ma="Khong can ma", ma_co_dinh="", can_otp=0, cong_don=0, hd_toi_thieu=0, sl_toi_thieu=0,
		giam_toi_da=0, pham_vi="Ca hoa don", tu_ngay="2026-08-12", den_ngay="2030-12-12", gio_tu=None, gio_den=None,
		kenh="", quay="", doi_tuong="Moi khach", hang_khach="", nhom_khach="", nhom_mon="", da_dung=0,
		lan_moi_ngay=0, lan_moi_ca=0, lan_moi_khach=0, so_lan_toi_da=0, hien_web=0, web_anh="", web_mo_ta="",
		vi_phat=0, vi_dip="", dong_mon=[], dong_bac=[])
	d.update(k)
	return _fr._dict(d)


CTKM = [
	_km("KM-GRAB", "Voucher Grab Dine Out giả (tiệm chịu 40.000)", gia_tri=40000, kenh="Tại chỗ", quay="TCV"),
	_km("KM-TANG", "Tặng Bánh Giả", cach_thuc="Tang mon", kieu_giam="Phan tram", cach_ma="Ma co dinh", quay="TCV",
		dong_mon=[{"item_code": BANH, "vai_tro": "Uu dai", "so_luong": 1, "kieu_giam": None, "gia_tri": 0}]),
	_km("KM-WEB", "Chỉ Website giả", gia_tri=10000, kenh="Website"),
	_km("KM-TANG2", "Tặng 2 Bánh Giả", cach_thuc="Tang mon", kieu_giam="Phan tram", cach_ma="Ma co dinh", quay="TCV",
		dong_mon=[{"item_code": BANH, "vai_tro": "Uu dai", "so_luong": 2, "kieu_giam": None, "gia_tri": 0}]),
]
KM = {c.name: c for c in CTKM}


@contextlib.contextmanager
def _moi_truong(si, gia_diem=None, ghi=None):
	"""Quầy TCV trên bill QR si: bảng CTKM, giá, tên món GIẢ; phép khuyến mãi thật."""
	bh = types.SimpleNamespace(_kiem_quyen_ban=lambda: None, _otp_la_sep=lambda: False,
		_otp_kiem=lambda otp, viec="": "OTP",
		_dung_dong_mon=lambda r: {"item_code": r["item_code"], "qty": r["qty"], "rate": r["rate"]})
	tdb = types.SimpleNamespace(_la_gop=lambda kh: not kh or kh.startswith("Khách lẻ"))
	db = types.SimpleNamespace(exists=lambda dt, ten=None: dt == "Vagabond CTKM" and ten in KM,
		get_value=lambda *a, **k: "", commit=lambda: None, sql=lambda *a, **k: [])
	diem = types.SimpleNamespace(gia_rieng_cua_quay=lambda q: dict(gia_diem or {}), loc_bo_bang_rieng=lambda: [])
	with patch.dict(sys.modules, {"vagabond.ban_hang": bh, "vagabond.tich_diem_ban": tdb, "vagabond.diem_ban": diem}), \
			patch.object(vagabond, "ban_hang", bh, create=True), patch.object(vagabond, "tich_diem_ban", tdb, create=True), \
			patch.object(vagabond, "diem_ban", diem, create=True), \
			patch.object(_fr, "get_doc", return_value=si), patch.object(_fr, "db", db), \
			patch.object(_fr, "get_all", side_effect=lambda dt, **k: [_fr._dict(c) for c in CTKM] if dt == "Vagabond CTKM" else []), \
			patch.object(khuyen_mai, "_kiem_quyen", lambda: None), \
			patch.object(khuyen_mai, "_doc_ctkm", side_effect=lambda ma: dict(KM[ma])), \
			patch.object(khuyen_mai, "_hop_han_muc", lambda km, sdt=None, ngay=None: (True, "")), \
			patch.object(khuyen_mai, "_uu_dai_hang", lambda kh, ng: None), \
			patch.object(khuyen_mai, "_gia_ban", lambda ma: 50000), \
			patch.object(khuyen_mai, "_ten_mon", lambda ma: "Bánh Giả" if ma == BANH else ma), \
			patch.object(khuyen_mai, "ghi_su_dung", side_effect=lambda kq, ten, **k: (ghi if ghi is not None else []).append(k)), \
			patch.object(vagabond.quyen_quay, "muc", return_value="tu_do"), \
			patch.object(_fr, "session", _fr._dict(user="thungan@vgb"), create=True):
		yield


@ca("v698 phép thuần: bill QR khi QUẦY áp xét kênh như Tại chỗ, khách tự chọn vẫn theo nguồn gốc; dòng món tặng theo giá quầy; lý do rõ khi món tặng chưa có")
def _thuan():
	la("quầy áp bill QR", u.nguon_km(goi_mon_ban.NGUON_QR, True), "Tại chỗ")
	la("khách tự chọn bill QR", u.nguon_km(goi_mon_ban.NGUON_QR, False), goi_mon_ban.NGUON_QR)
	la("nguồn khác không đổi", (u.nguon_km("GrabFood", True), u.nguon_km("", True)), ("GrabFood", ""))
	them = [{"item_code": BANH, "qty": 1, "rate": 50000}, {"item_code": "GIA-B2", "qty": 2, "rate": 30000}, {"item_code": "GIA-B3", "qty": 0, "rate": 1}]
	la("giá điểm nếu có, không thì giá gợi ý; số lượng 0 bỏ", u.dong_tang_thuan(them, {BANH: 45000}),
		[{"item_code": BANH, "qty": 1.0, "rate": 45000.0}, {"item_code": "GIA-B2", "qty": 2.0, "rate": 30000.0}])
	la("giá điểm 0 là giá đã chọn, không thay bằng giá gợi ý", u.dong_tang_thuan(them[:1], {BANH: 0})[0]["rate"], 0.0)
	la("mô tả", u.mo_ta_tang(u.dong_tang_thuan(them, {}), {BANH: "Bánh Giả"}), "1 Bánh Giả, 2 GIA-B2")
	kq = {"tong_hd": 90000, "ap": [{"loai": "ctkm", "giam": 0}], "them_mon": [{"item_code": BANH, "qty": 1}]}
	la("Tặng món, món tặng chưa có: lý do rõ", u.giam_tu_kq(kq), (0, "món tặng chưa có trong hoá đơn"))


@ca("v698 màn bill QR, nút Chương trình (uu_dai_ban.ds_quay thật, khuyen_mai thật): voucher Grab kênh Tại chỗ áp được; Tặng món báo tặng bánh và số trừ theo giá quầy; chương trình chỉ Website vẫn không áp")
def _ds_quay():
	si = _hd()
	with _moi_truong(si, gia_diem={BANH: 45000}):
		r = u.ds_quay(si.name)
	ds = {x["ma"]: x for x in r["ds"]}
	la("Grab", (ds["KM-GRAB"]["dung_duoc"], ds["KM-GRAB"]["giam"]), (1, 40000))
	la("Tặng món", (ds["KM-TANG"]["dung_duoc"], ds["KM-TANG"]["giam"], ds["KM-TANG"]["tang"]), (1, 45000, "1 Bánh Giả"))
	la("chỉ Website", (ds["KM-WEB"]["dung_duoc"], "Website" in ds["KM-WEB"]["ly_do"] or "nguồn" in ds["KM-WEB"]["ly_do"]), (0, True))
	la("bill chưa đổi khi chỉ xem danh sách", (len(si["items"]), si.luu), (2, 0))


@ca("v698 quầy bấm Tặng món trên bill QR (uu_dai_ban.ap_quay thật): thêm đúng một dòng món tặng giá quầy, trừ đúng số đó, tổng bill không đổi; lịch sử ghi món tặng; chốt bill giữ nguyên số")
def _ap_tang():
	si = _hd()
	truoc = si.grand_total
	with _moi_truong(si, gia_diem={BANH: 45000}):
		r = u.ap_quay(si.name, "ctkm", "KM-TANG")
	la("áp được", (r["ok"], r["giam"], r["tang"]), (1, 45000, "1 Bánh Giả"))
	la("thêm một dòng món tặng giá quầy", [(x.item_code, float(x.qty), float(x.rate)) for x in si["items"]][-1], (BANH, 1.0, 45000.0))
	la("số dòng", len(si["items"]), 3)
	la("trừ đúng giá món tặng, tổng không đổi", (si.vgb_giam_ud, si.grand_total), (45000.0, truoc))
	dung("lịch sử ghi món tặng: " + str(si.ghi_chu), any("thêm món tặng 1 Bánh Giả" in c for c in si.ghi_chu))
	ghi = []
	with _moi_truong(si, gia_diem={BANH: 45000}, ghi=ghi):
		kq = u.truoc_chot(si)
	dung("chốt: tính lại vẫn trừ đúng giá món tặng, không báo ưu đãi đổi", kq and abs(sum(a["giam"] for a in kq["ap"]) - 45000) < 1)
	with _moi_truong(si, gia_diem={BANH: 45000}):
		r2 = u.ap_quay(si.name, "ctkm", "KM-TANG")
	la("bấm lần hai: chặn, không thêm dòng", (r2["ok"], len(si["items"])), (0, 3))


@ca("v698 quầy bấm voucher Grab trên bill QR (ap_quay thật): trừ 40.000, không thêm dòng; bill QR mà khách tự chọn thì danh sách khách vẫn không có voucher Grab")
def _ap_grab():
	si = _hd()
	with _moi_truong(si):
		r = u.ap_quay(si.name, "ctkm", "KM-GRAB")
	la("áp Grab", (r["ok"], r["giam"], r["tang"], len(si["items"])), (1, 40000, "", 2))
	la("ghi nguồn khuyến mãi như Tại chỗ khi quầy áp", u.doc_ud(si.vgb_ud_ban)["cach"], u.CACH_QUAY)
	# Khách tự chọn trên trang bàn: nguồn gốc QR, voucher Grab không có trong danh sách.
	ds = u.loc_ctkm([_fr._dict(c) for c in CTKM if c.name != "KM-TANG"], goi_mon_ban.NGUON_QR, "TCV", khuyen_mai._hop_kenh, khuyen_mai.CACH_THUC_WEB)
	la("trang khách không có voucher Grab", [x["name"] for x in ds if x["name"] == "KM-GRAB"], [])


@ca("v698 khách tự chọn (bill có ud không có cách quầy): tính theo nguồn gốc QR, voucher kênh Tại chỗ bị chặn như trước")
def _khach_giu_nguon():
	si = _hd()
	with _moi_truong(si):
		kq = u._tinh(si, {"loai": "ctkm", "ma": "KM-GRAB", "khach": "", "sdt": ""})
	la("khách: không áp", ([a["ma"] for a in kq["ap"]], "QR tại bàn" in json.dumps(kq["bo"], ensure_ascii=False)), ([], True))


@ca("v698 màn bill: dòng chương trình Tặng món ghi rõ tặng bánh và máy thêm vào bill (nạp nguyên app_bep.js bằng node)")
def _giao_dien():
	r = subprocess.run(["node", os.path.join(GOC, "vagabond/khung/kiem_thu/hanh_vi/bill_km_tang_698.js")],
		capture_output=True, text=True, timeout=180)
	la("bill_km_tang_698.js", (r.returncode, (r.stdout + r.stderr)[-800:] if r.returncode else ""), (0, ""))


@ca("Codex #630 (loại 3): bill đã có 1 bánh tặng giá cũ 30.000 đ, giá quầy nay 45.000 đ, chương trình tặng 2: dòng tự thêm theo giá dòng đã có trên bill, trừ đúng tiền hai bánh, khách chỉ trả món thường; chốt tính lại không lệch")
def _codex630_gia_dong():
	si = _hd(items=[{"item_code": "GIA-THUONG", "qty": 1, "rate": 100000}, {"item_code": BANH, "qty": 1, "rate": 30000}])
	with _moi_truong(si, gia_diem={BANH: 45000}):
		ds = {x["ma"]: x for x in u.ds_quay(si.name)["ds"]}
		r = u.ap_quay(si.name, "ctkm", "KM-TANG2")
	la("danh sách báo đúng số trừ", (ds["KM-TANG2"]["giam"], ds["KM-TANG2"]["tang"]), (60000, "1 Bánh Giả"))
	la("dòng thêm theo giá dòng đã có", [(x.item_code, float(x.rate)) for x in si["items"]][-1], (BANH, 30000.0))
	la("trừ hai bánh, khách trả đúng món thường", (r["giam"], si.grand_total), (60000, 100000.0))
	with _moi_truong(si, gia_diem={BANH: 45000}):
		kq = u.truoc_chot(si)
	la("chốt tính lại không lệch", (sum(a["giam"] for a in kq["ap"]), si.grand_total), (60000, 100000.0))
	la("hai dòng cùng món khác giá: lấy dòng đầu như khuyen_mai._tinh_mot", u.gia_dong_dau(
		[{"item_code": BANH, "rate": 30000}, {"item_code": "GIA-THUONG", "rate": 100000}, {"item_code": BANH, "rate": 45000}]), {BANH: 30000.0, "GIA-THUONG": 100000.0})
	la("phép thuần: giá dòng trên bill trước giá điểm", u.dong_tang_thuan([{"item_code": BANH, "qty": 1, "rate": 50000}], {BANH: 45000}, {BANH: 30000})[0]["rate"], 30000.0)
