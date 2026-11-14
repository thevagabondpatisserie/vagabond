"""Loan Anh 14/11/2026, đơn 97492 (HDB-26-11-02701): khách chuyển khoản 684.000
(SePay khớp đúng mã đơn) và trả 20.000 qua OnePay. Sales lưu hai dòng ở "Sửa
cách chia tiền" mà màn Đơn bán vẫn báo "Chờ tiền về", cửa ghi sổ vẫn chặn, vì
mọi chỗ so số ngân hàng nhận với CẢ tờ 704.000.

Nay một nguồn: thanh_toan_nhieu.so_can_ck (phép thuần) và ban_hang._can_ck
(cửa ghi sổ, danh sách Đơn bán, màn tính tiền, Đơn còn treo, chuông ghi sổ, khớp
theo số tiền, chốt ca) cùng doi_soat_ck. Ca ở đây chạy hàm THẬT nạp từ tệp
nguồn, dựng đúng đơn 97492, và chốt không còn chỗ nào tự so với grand_total.
"""
import re
from pathlib import Path
from types import SimpleNamespace as NS

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_su_co_290 import D, nap

GOC = Path(__file__).resolve().parents[2]


def _nem(cau, *a, **k):
	raise ValueError(cau)


@ca("đơn 97492: tờ chia Chuyển khoản 684.000 + OnePay 20.000 thì ngân hàng chỉ phải nhận 684.000; không chia thì cả tờ; chia lệch thì theo tỷ lệ")
def _thuan():
	from vagabond import thanh_toan_nhieu as ttn

	dong = [{"pt": "Chuyển khoản", "so_tien": 684000}, {"pt": "OnePay", "so_tien": 20000}]
	la("đúng đơn 97492", ttn.so_can_ck(dong, 704000), 684000.0)
	la("không chia", ttn.so_can_ck([], 704000), 704000.0)
	la("dòng rỗng, số âm bị bỏ", ttn.so_can_ck([{"pt": "", "so_tien": 5}, {"pt": "OnePay", "so_tien": -1}], 704000), 704000.0)
	la("không có dòng chuyển khoản", ttn.so_can_ck([{"pt": "Tiền mặt", "so_tien": 704000}], 704000), 0.0)
	la("chia lệch: theo tỷ lệ cho đủ tờ", ttn.so_can_ck([{"pt": "Chuyển khoản", "so_tien": 500000}, {"pt": "OnePay", "so_tien": 500000}], 704000), 352000.0)


def _g_soat(nhan):
	return dict(frappe=NS(throw=_nem), flt=lambda x: float(x or 0), cfg=lambda: NS(pancake_shop_id="67355"),
		_sepay_theo_don=lambda shop, ma: {"97492": {"nhan": nhan, "ma": "FT26315874337462"}}, _ck_don_web=lambda si: {})


@ca("đơn 97492: cửa ghi sổ cho qua khi ngân hàng nhận đủ phần chuyển khoản (684.000) và tự điền mã giao dịch; nhận thiếu phần đó vẫn chặn, câu báo nói đúng số phải chuyển khoản")
def _cua_ghi_so():
	def si():
		return D(name="HDB-26-11-02701", custom_pancake_display_id="97492", vgb_pt_thanh_toan="Chuyển khoản",
			grand_total=704000, vgb_ma_tham_chieu="",
			vgb_thanh_toan_nhieu=[D(pt="Chuyển khoản", so_tien=684000), D(pt="OnePay", so_tien=20000)])
	g = _g_soat(684000)
	nap("ban_hang.py", "_tien", g)
	d = si()
	nap("ban_hang.py", "_soat_sepay", g)(d)
	la("qua cửa, điền mã giao dịch", d.vgb_ma_tham_chieu, "FT26315874337462")
	g = _g_soat(600000)
	nap("ban_hang.py", "_tien", g)
	try:
		nap("ban_hang.py", "_soat_sepay", g)(si())
		dung("nhận thiếu phải chặn", False)
	except ValueError as e:
		dung("câu báo nói 684.000 phải chuyển khoản", "684.000" in str(e) and "704.000" not in str(e))
	# Tờ không chia vẫn đòi cả tờ như cũ.
	g = _g_soat(684000)
	nap("ban_hang.py", "_tien", g)
	d = si()
	d.vgb_thanh_toan_nhieu = []
	try:
		nap("ban_hang.py", "_soat_sepay", g)(d)
		dung("tờ không chia mà nhận thiếu phải chặn", False)
	except ValueError:
		pass


@ca("đơn 97492 trên danh sách: màn Đơn bán, Đơn còn treo đọc bảng chia một lượt cho cả danh sách, đơn đủ phần chuyển khoản không còn chip Chờ tiền về")
def _danh_sach():
	doc = []

	def get_all(dt, filters=None, fields=None, **k):
		doc.append(dt)
		if dt == "Vagabond Dong Thanh Toan":
			return [{"parent": "HDB-26-11-02701", "pt": "Chuyển khoản", "so_tien": 684000, "ma_tham_chieu": "", "do_may": 0},
				{"parent": "HDB-26-11-02701", "pt": "OnePay", "so_tien": 20000, "ma_tham_chieu": "", "do_may": 0}]
		return []
	from unittest.mock import patch

	from vagabond import thanh_toan_nhieu as ttn
	from vagabond import ghi_so_dieu_kien as gsdk

	g = dict(flt=lambda x: float(x or 0), ghi_so_dieu_kien=gsdk, _pt_cho_nguon=lambda n: ["Chuyển khoản", "OnePay"])
	nap("ban_hang.py", "_ly_do_treo", g)
	ds = [D(name="HDB-26-11-02701", grand_total=704000, vgb_pt_thanh_toan="Chuyển khoản", vgb_ma_tham_chieu="",
		custom_pancake_display_id="97492", custom_nguon="Pancake"),
		D(name="HDB-KHAC", grand_total=500000, vgb_pt_thanh_toan="Chuyển khoản", vgb_ma_tham_chieu="",
		custom_pancake_display_id="97500", custom_nguon="Pancake")]
	with patch.object(ttn.frappe, "get_all", get_all, create=True):
		g["_gan_can_ck"](ds)
	la("đọc bảng chia MỘT lượt", doc.count("Vagabond Dong Thanh Toan"), 1)
	sepay = {"97492": {"nhan": 684000}, "97500": {"nhan": 300000}}
	la("97492 đủ phần chuyển khoản", g["_ly_do_treo"](ds[0], sepay), "san_sang")
	la("đơn không chia nhận thiếu vẫn chờ tiền", g["_ly_do_treo"](ds[1], sepay), "chua_ve_tien")


@ca("một nguồn: ban_hang.py và doi_soat_ck.py không còn chỗ nào tự so số ngân hàng nhận với grand_total; mọi chỗ đi qua _can_ck")
def _mot_nguon():
	for tep in ("ban_hang.py", "doi_soat_ck.py"):
		s = (GOC / tep).read_text(encoding="utf-8")
		sai = re.findall(r"(?:nhan|tien|sepay_nhan)[^\n]{0,40}(?:>=|<)\s*flt\([^\n]*grand_total[^\n]*\)\s*-\s*1", s)
		sai += re.findall(r"trang_thai_tien\(nhan,\s*r\.grand_total\)", s)
		la(tep + ": chỗ tự so với grand_total", sai, [])
	s = (GOC / "ban_hang.py").read_text(encoding="utf-8")
	dung("cửa ghi sổ gọi _can_ck", "can = _can_ck(si)" in s.split("def _soat_sepay")[1].split("\ndef ")[0])


@ca("Codex #567: màn tính tiền (pos_ds_bill) với 100 bill tiền mặt chỉ đọc bảng chia tiền MỘT lượt, không hỏi từng bill; bill chuyển khoản chia đôi vẫn chỉ đòi phần chuyển khoản")
def _pos_khong_hoi_tung_bill():
	import sys
	import types
	from unittest.mock import patch

	from vagabond import thanh_toan_nhieu as ttn

	hoi = []

	def get_all(dt, filters=None, fields=None, **k):
		if dt == "Sales Invoice":
			ds = [D(name="TM-%03d" % i, grand_total=50000, vgb_pt_thanh_toan="Tiền mặt", vgb_ma_tham_chieu="",
				custom_pancake_display_id="") for i in range(100)]
			ds.append(D(name="HDB-26-11-02701", grand_total=704000, vgb_pt_thanh_toan="Chuyển khoản",
				vgb_ma_tham_chieu="", custom_pancake_display_id="97492"))
			return ds
		if dt == ttn.DT_DONG:
			hoi.append(filters.get("parent"))
			cha = filters.get("parent")
			ten = cha[1] if isinstance(cha, list) else [cha]
			if "HDB-26-11-02701" in ten:
				return [{"parent": "HDB-26-11-02701", "pt": "Chuyển khoản", "so_tien": 684000, "ma_tham_chieu": "", "do_may": 0},
					{"parent": "HDB-26-11-02701", "pt": "OnePay", "so_tien": 20000, "ma_tham_chieu": "", "do_may": 0}]
		return []

	fr = NS(get_all=get_all, throw=_nem, log_error=lambda *a, **k: None, get_traceback=lambda: "")
	g = dict(frappe=fr, flt=lambda x: float(x or 0), _kiem_quyen_ban=lambda: None, _loc_diem_ban=lambda q: {},
		getdate=lambda x: x, nowdate=lambda: "2026-11-14", cfg=lambda: NS(pancake_shop_id="67355"),
		_sepay_theo_ma_bill=lambda ma: ({}, []), _sepay_theo_don=lambda shop, ma: {"97492": {"nhan": 684000}},
		_ma_trung_trong_ngay=lambda ngay, ma: set(), gan_khach_vao_dong=lambda ds: None, _gan_ly_do_treo=lambda ds: None,
		pancake_nhip=NS(tinh_trang=lambda: {}), ghi_so_dieu_kien=NS(LY_DO={}))
	ham = nap("ban_hang.py", "pos_ds_bill", g)
	kho = types.ModuleType("vagabond.tru_kho_bu")
	kho.gan_trang_thai = lambda ds: None
	with patch.object(ttn.frappe, "get_all", get_all, create=True), patch.dict(sys.modules, {"vagabond.tru_kho_bu": kho}):
		kq = ham("TCV", "2026-11-14")
	la("đọc bảng chia một lượt cho cả ngày", len(hoi), 1)
	ck = [b for b in kq["bill"] if b.name == "HDB-26-11-02701"][0]
	la("bill chia đôi: đủ phần chuyển khoản", ck["sepay_du"], 1)


@ca("Codex #567 quét theo loại: mọi chỗ gắn số phải chuyển khoản đều gắn cho CẢ danh sách mà vòng lặp sau đó đi qua (không lọc riêng tờ Chuyển khoản), và chuông ghi sổ cũng gắn trước khi xét lý do treo")
def _gan_ca_danh_sach():
	s = (GOC / "ban_hang.py").read_text(encoding="utf-8")
	la("không còn chỗ gắn cho danh sách đã lọc", re.findall(r"_gan_can_ck\(\[", s), [])
	than = s.split("\ndef bao_dong_ghi_so(")[1].split("\ndef ")[0]
	dung("chuông ghi sổ gắn trước vòng lặp", "_gan_can_ck(rows)" in than
		and than.index("_gan_can_ck(rows)") < than.index("_ly_do_treo(r, sepay)"))
