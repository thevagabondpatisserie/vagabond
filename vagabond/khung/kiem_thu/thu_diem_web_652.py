"""v652 điểm thành viên trên web, nhân điểm theo chương trình, thể lệ (anh Việt 12/11/2026).

Luật anh chốt: khách online dùng điểm ở bước thanh toán sau khi xác thực số qua
mã Zalo; cùng luật quầy (1 điểm = 1 đồng, tối đa 50%, bill còn lại không dưới
10.000, hạng AMBASSADOR, FAMILY, OWNER không dùng); điểm chỉ trừ tiền bánh,
không trừ phí giao, cộng chung với mã và ưu đãi đơn đầu, trừ sau cùng; đơn không
thành thì tự hoàn điểm và báo Zalo. Nhân điểm là một CTKM Marketing cài (ví dụ
thứ Năm trên web x2), không mặc định. Hạn điểm cuốn chiếu 12 tháng.

Ca dưới gọi THẬT tao_don, xem_uu_dai của don_hang (bộ khung nap như v367, v645)
với phần điểm dùng phép thật diem_web.xet_web.
"""
import json
import types
from datetime import datetime
from unittest.mock import patch

from vagabond import diem_web as dw
from vagabond import don_dau_web as dd
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu import thu_don_dau_web_645 as t645
from vagabond.khung.kiem_thu.thu_don_web_367 import _Tra, _don, _km_gia, _moi_truong_tao_don


class DiemGia:
	"""Phần chạm hệ của diem_web thay bằng số giả; phép xét là phép THẬT."""

	def __init__(self, so_du=300000, hang="VAGABONDER", co_phien=True, giu=None):
		self.so_du, self.hang, self.co_phien, self.giu = so_du, hang, co_phien, giu
		self.vet = types.SimpleNamespace(xet=[], giu=[], hoan=[])

	def thong_tin(self, sdt, tien_banh, dung):
		self.vet.xet.append((sdt, tien_banh, dung))
		ra = dw.xet_web(self.co_phien, "KH-1", self.hang, self.so_du, tien_banh, dung, 1.0, 50.0, 10000.0)
		ra["khach"] = "KH-1" if self.co_phien else ""
		return ra

	def giu_diem(self, ten, khach, diem, tien_banh):
		self.vet.giu.append((ten, khach, diem, tien_banh))
		return diem if self.giu is None else self.giu

	def hoan_don_web(self, ten, ly_do=""):
		self.vet.hoan.append((ten, ly_do))


def _tao(diem, pancake=None, **don):
	vet, tao_don = _moi_truong_tao_don(pancake or (lambda v: _Tra(200, {"data": {"id": "1"}})), km=_km_gia(giam=0))
	tao_don.__globals__["diem_web"] = diem
	return vet, tao_don(_don(**don))


@ca("v652 xet_web thuần: chưa xác thực KHÔNG lộ số dư; số không có thành viên; hạng cấm; bill nhỏ; trần 50% và số dư; chỉ trừ khi khách chọn")
def _():
	la("chưa xác thực", dw.xet_web(False, "KH", "", 500000, 900000, True, 1, 50, 10000),
		{"trang_thai": "can_xac_thuc", "so_du": 0, "toi_da": 0, "tien_toi_da": 0, "dung": 0, "tien": 0})
	la("không phải thành viên", dw.xet_web(True, None, "", 0, 900000, True, 1, 50, 10000)["trang_thai"], "khong_co")
	for h in ("AMBASSADOR", "family", " Owner "):
		r = dw.xet_web(True, "KH", h, 500000, 900000, True, 1, 50, 10000)
		la("hạng %s không dùng" % h, (r["trang_thai"], r["dung"], r["so_du"]), ("cam", 0, 500000))
	la("bill quá nhỏ", dw.xet_web(True, "KH", "", 500000, 9000, True, 1, 50, 10000)["trang_thai"], "chua_du")
	la("hết điểm", dw.xet_web(True, "KH", "", 0, 900000, True, 1, 50, 10000)["trang_thai"], "chua_du")
	r = dw.xet_web(True, "KH", "VAGABONDER", 600000, 900000, False, 1, 50, 10000)
	la("trần 50%, chưa chọn thì chưa trừ", (r["trang_thai"], r["toi_da"], r["tien_toi_da"], r["dung"], r["tien"]),
		("dung_duoc", 450000, 450000, 0, 0))
	r = dw.xet_web(True, "KH", "VAGABONDER", 120000, 900000, True, 1, 50, 10000)
	la("trần số dư, đã chọn", (r["dung"], r["tien"]), (120000, 120000))


@ca("v652 hệ số nhân điểm: ô điền tay '2', 'x2', '2,5', trống, chữ lạ, âm đều ra số hợp lý; nhiều chương trình lấy lớn nhất, không nhân chồng")
def _():
	la("các cách điền", [dw.he_so(x) for x in ("2", "x2", "X3", "2,5", "", None, "abc", "-3", "0.5", "50")],
		[2.0, 2.0, 3.0, 2.5, 1.0, 1.0, 1.0, 1.0, 1.0, 10.0])
	la("lấy lớn nhất", dw.chon_he_so([{"gia_tri": "2", "ten": "A"}, {"gia_tri": "3", "ten": "B"}, {"gia_tri": "x1", "ten": "C"}]), (3.0, "B"))
	la("không chương trình", dw.chon_he_so([]), (1.0, ""))
	la("nhân và làm tròn", (dw.diem_nhan(1235, 2), dw.diem_nhan(1001, "2,5"), dw.diem_nhan(0, 3)), (2470, 2502, 0))
	la("câu thể lệ", dw.cau_nhan_diem({"thu_5": 1, "kenh": "Website", "gia_tri": "2"}), "Thứ Năm hằng tuần, đặt bánh trên web được x2 điểm.")
	la("câu mọi ngày", dw.cau_nhan_diem({"gia_tri": "1,5"}), "Mua bánh được x1,5 điểm.")


@ca("v652 nhân điểm: CTKM Nhân điểm thứ Năm kênh Website x2 chỉ áp đơn web thứ Năm; quầy hay thứ Sáu giữ x1; hoá đơn web lấy lúc khách đặt")
def _():
	km = {"name": "KM-1", "ten": "Thứ Năm x2 web", "gia_tri": "2", "tu_ngay": None, "den_ngay": None, "gio_tu": None, "gio_den": None,
		"kenh": "Website", "quay": "", "doi_tuong": "Moi khach", "hang_khach": "", "nhom_khach": "", "hien_web": 1,
		"thu_2": 0, "thu_3": 0, "thu_4": 0, "thu_5": 1, "thu_6": 0, "thu_7": 0, "thu_cn": 0}
	from vagabond import khuyen_mai as km_
	# Khung giả lập cố định "bây giờ"; ca này cần đúng lúc mua truyền vào.
	that = lambda v: v if isinstance(v, datetime) else datetime.fromisoformat(str(v))
	with patch.object(dw, "ctkm_nhan_dang_bat", return_value=[km]), patch.object(km_, "get_datetime", that):
		la("thứ Năm web", dw.he_so_luc(datetime(2026, 11, 12, 10, 0), "Website", "", "KH-1"), (2.0, "Thứ Năm x2 web"))
		la("thứ Năm tại quầy", dw.he_so_luc(datetime(2026, 11, 12, 10, 0), "Tai quay", "TCV", "KH-1"), (1.0, ""))
		la("thứ Sáu web", dw.he_so_luc(datetime(2026, 11, 13, 10, 0), "Website", "", "KH-1"), (1.0, ""))
		si = {"grand_total": 450000, "customer": "KH-1", "custom_pancake_display_id": "9150", "posting_date": "2026-11-13", "posting_time": "09:00:00"}
		# khach_hang kéo ban_hang (cần requests, CI không có): thay bằng mô đun giả chỉ có hàm cần.
		kh = types.SimpleNamespace(diem_cho_don=lambda tong, ty_le: int(tong * ty_le / 100))
		with patch.object(dw, "boi_canh_hoa_don", return_value=(datetime(2026, 11, 12, 21, 0), "Website", "")), \
				patch.dict("sys.modules", {"vagabond.khach_hang": kh}):
			la("hoá đơn ghi sổ thứ Sáu của đơn đặt thứ Năm: x2", dw.diem_hoa_don(si, 5), (45000, 2.0, "Thứ Năm x2 web"))


@ca("v652 tao_don dùng điểm: đủ điều kiện thì ghi đơn, trừ điểm cùng giao dịch, Pancake nhận giảm gồm điểm, snapshot ghi số điểm; phí giao miễn theo tiền trước điểm")
def _():
	diem = DiemGia(so_du=500000)
	vet, kq = _tao(diem, dien_thoai="0931224334", dung_diem=True, giam_da_xem=500000,
		items=[{"variation_id": "BAWC00139", "quantity": 3}])
	la("đơn thành", kq.get("ok"), 1)
	la("trừ điểm đúng đơn, khách, số, tiền bánh", diem.vet.giu, [("DW-2609-00001", "KH-1", 500000, 1350000)])
	dung("trừ SAU khi ghi bản ghi, TRƯỚC khi gửi Pancake", vet.su.index("ghi") < vet.su.index("post"))
	la("Pancake nhận giảm gồm điểm", sum(x["discount_each_product"] * x["quantity"] for x in vet.body["items"]), 500000)
	sn = json.loads(vet.truong["snapshot"])
	la("snapshot", (sn["uu_dai"]["giam"], sn["uu_dai"]["diem"]), (500000, {"so_diem": 500000, "tien": 500000}))
	la("miễn phí giao: 1.350.000 trước điểm vẫn trên ngưỡng 1.000.000", vet.body.get("shipping_fee"), 0)


@ca("v652 tao_don dùng điểm: trang chưa tính điểm thì trả bảng mới kèm dòng Điểm thành viên; phiên hết hạn hay giữ điểm hụt thì diem_doi, không gửi Pancake")
def _():
	diem = DiemGia(so_du=300000)
	vet, kq = _tao(diem, dien_thoai="0931224334", dung_diem=True, giam_da_xem=0)
	la("bảng mới", (kq.get("ly_do"), kq["uu"]), ("uu_dai_doi", {"giam": 300000, "ap": [{"ten": "Điểm thành viên", "giam": 300000}]}))
	dung("không ghi, không gửi", "ghi" not in vet.su and "post" not in vet.su)
	vet, kq = _tao(DiemGia(co_phien=False), dien_thoai="0931224334", dung_diem=True, giam_da_xem=300000)
	la("phiên hết", (kq.get("ly_do"), kq["diem"]["trang_thai"], "so_du" in kq["diem"] and kq["diem"]["so_du"]), ("diem_doi", "can_xac_thuc", 0))
	dung("không ghi, không gửi", "ghi" not in vet.su and "post" not in vet.su)
	diem = DiemGia(so_du=300000, giu=0)
	vet, kq = _tao(diem, dien_thoai="0931224334", dung_diem=True, giam_da_xem=300000)
	la("giữ hụt (đơn khác vừa tiêu)", kq.get("ly_do"), "diem_doi")
	dung("lùi bản ghi, không gửi Pancake", "rollback" in vet.su and "post" not in vet.su)
	dung("không lộ mã khách ra trình duyệt", "khach" not in (kq.get("diem") or {}))


@ca("v652 tao_don dùng điểm: Pancake từ chối thì hoàn điểm ngay theo đúng đơn; Pancake nhận thì không hoàn; không chọn dùng điểm thì không đụng điểm")
def _():
	diem = DiemGia(so_du=300000)
	_tao(diem, pancake=lambda v: _Tra(422, {"message": "sai"}), dien_thoai="0931224334", dung_diem=True, giam_da_xem=300000)
	la("hoàn theo đơn", [x[0] for x in diem.vet.hoan], ["DW-2609-00001"])
	diem = DiemGia(so_du=300000)
	_tao(diem, dien_thoai="0931224334", dung_diem=True, giam_da_xem=300000)
	la("nhận thì không hoàn", diem.vet.hoan, [])
	diem = DiemGia(so_du=300000)
	vet, kq = _tao(diem, dien_thoai="0931224334", giam_da_xem=0)
	la("không chọn: không xét, không trừ", (kq.get("ok"), diem.vet.xet, diem.vet.giu), (1, [], []))


@ca("v652 xem_uu_dai: giỏ có số đã xác thực, chọn dùng điểm thì giảm gồm điểm trừ sau ưu đãi khác, có dòng Điểm thành viên và phần điểm cho thẻ; chưa xác thực thì thẻ mời xác thực, không số dư")
def _():
	xem, _d, _k, _l = t645._xem(ap_giam=30000, dau=t645._dau_gia(trang_thai=dd.KHONG))
	diem = DiemGia(so_du=1000000)
	xem.__globals__["diem_web"] = diem
	r = xem({"items": [{"variation_id": "A", "quantity": 1}], "dien_thoai": t645.SO, "dung_diem": 1})
	la("trừ sau mã: tiền bánh 450.000 - 30.000", diem.vet.xet[0][1], 420000)
	la("giảm gồm 50% còn lại", (r["giam"], r["ap"][-1]), (30000 + 210000, {"ten": "Điểm thành viên", "giam": 210000}))
	la("phần thẻ", (r["diem"]["trang_thai"], r["diem"]["dung"], r["diem"]["so_du"]), ("dung_duoc", 210000, 1000000))
	xem.__globals__["diem_web"] = DiemGia(co_phien=False)
	r = xem({"items": [{"variation_id": "A", "quantity": 1}], "dien_thoai": t645.SO, "dung_diem": 1})
	la("chưa xác thực", (r["giam"], r["diem"]["trang_thai"], r["diem"]["so_du"]), (30000, "can_xac_thuc", 0))


@ca("v652 điểm sắp hết hạn (cuốn chiếu 12 tháng): đúng số và ngày mất đầu tiên, đã tiêu thì trừ, ngoài 30 ngày thì không nhắc")
def _():
	but = [("2025-11-20", 300), ("2025-12-25", 200), ("2026-03-01", -100), ("2026-05-01", 500)]
	la("trong 30 ngày tới", dw.sap_het_han(but, "2026-11-12", 12), {"diem": 200, "ngay": "21/11/2026"})
	la("còn quá xa", dw.sap_het_han([("2026-05-01", 500)], "2026-11-12", 12), None)
	la("tắt hạn", dw.sap_het_han(but, "2026-11-12", 0), None)


@ca("v652 thể lệ: hạng theo chi tiêu đang bật theo thứ tự; quyền lợi lấy từ CTKM theo hạng đang hiện web; CTKM nhân điểm không lẫn vào quyền lợi")
def _():
	hang = [{"ten_hang": "AMBASSADOR", "thu_tu": 3, "loai": "Theo chi tieu", "bat": 1, "chi_tieu_tu": 20000000, "tich_diem": 7, "giam_gia": 10},
		{"ten_hang": "VAGABONDER", "thu_tu": 1, "loai": "Theo chi tieu", "bat": 1, "chi_tieu_tu": 0, "tich_diem": 3, "giam_gia": 0},
		{"ten_hang": "FAMILY", "thu_tu": 9, "loai": "Gan tay", "bat": 1},
		{"ten_hang": "CU", "thu_tu": 2, "loai": "Theo chi tieu", "bat": 0}]
	ctkm = [{"ten": "Quà sinh nhật Ambassador", "doi_tuong": "Theo hang khach", "hang_khach": "AMBASSADOR", "hien_web": 1},
		{"ten": "Giấu web", "doi_tuong": "Theo hang khach", "hang_khach": "AMBASSADOR", "hien_web": 0},
		{"ten": "x2 thứ Năm", "doi_tuong": "Theo hang khach", "hang_khach": "AMBASSADOR", "hien_web": 1, "cach_thuc": "Nhan diem"}]
	b = dw.bang_the_le(hang, ctkm)
	la("hạng hiện", [x["ten_hang"] for x in b], ["VAGABONDER", "AMBASSADOR"])
	la("chỉ Ambassador giảm 10%", [(x["ten_hang"], x["giam_gia"]) for x in b], [("VAGABONDER", 0.0), ("AMBASSADOR", 10.0)])
	la("quyền lợi", [x["dac_quyen"] for x in b], [[], ["Quà sinh nhật Ambassador"]])


@ca("v652 hoàn điểm đơn web: hoàn đúng số đã trừ, MỘT lần dù gọi lại; báo Zalo; đơn không trừ điểm thì không làm gì")
def _():
	import sys
	fr = sys.modules["frappe"]
	so, zalo = [], []
	da_hoan = {"x": False}

	def sql(c, ts=None, **k):
		if "sum(diem)" in c:
			return [("KH-1", -300000)] if ts[1] == "Đơn web DW-1" else []
		if "count(*)" in c:  # Codex #557 vòng 2: đã hoàn chưa đọc bằng SQL có khoá
			return [(1 if da_hoan["x"] else 0,)]
		return []
	with patch.object(fr.db, "sql", side_effect=sql), \
			patch.dict("sys.modules", {"vagabond.khach_hang": types.SimpleNamespace(
				_ghi_so_diem=lambda kh, d, loai, si, gc: (so.append((kh, d, loai, gc)), da_hoan.update(x=True)))}), \
			patch("vagabond.zalo_kich_ban.cho_hoan_diem", lambda kh, don, d: zalo.append((kh, don, d))):
		la("hoàn", dw.hoan_don_web("DW-1", "Pancake từ chối"), 300000)
		la("gọi lại không hoàn nữa", dw.hoan_don_web("DW-1", "Đơn web đã huỷ"), 0)
		da_hoan["x"] = False
		la("đơn không trừ điểm", dw.hoan_don_web("DW-2"), 0)
	la("bút hoàn", so, [("KH-1", 300000, "Hoan lai diem da dung", "Đơn web DW-1")])
	la("tin Zalo", zalo, [("KH-1", "DW-1", 300000)])


@ca("v652 trang thành viên chạy thật trong node (hanh_vi/thanh_vien_652.js): Thể lệ, điểm sắp hết hạn, khách chưa đăng nhập xem thể lệ, Mua lại")
def _():
	import os
	import subprocess
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
	r = subprocess.run(["node", os.path.join(goc, "vagabond", "khung", "kiem_thu", "hanh_vi", "thanh_vien_652.js")],
		capture_output=True, text=True, timeout=120)
	la("chạy xanh", (r.returncode, (r.stderr or "")[-400:], (r.stdout or "")[-800:] if r.returncode else ""), (0, "", ""))
	dung("đủ 4 ca", "4 ca đạt, 0 ca hỏng" in r.stdout)


@ca("v652 cửa ngõ: hàm thể lệ cho khách chưa đăng nhập có trong danh sách cửa ngõ")
def _():
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
	s = open(os.path.join(goc, "vagabond", "khung", "kiem_thu", "thu_cua_ngo.py"), encoding="utf-8").read()
	dung("the_le", '"the_le"' in s.split('"thanh_vien.py"')[1].split("]")[0])


class _SoMVCC:
	"""Sổ điểm giả theo luật MariaDB REPEATABLE READ: đọc thường thấy ảnh chụp đầu
	giao dịch, đọc có khoá (FOR UPDATE, LOCK IN SHARE MODE) thấy bản đã commit."""

	def __init__(self, so_du):
		self.but, self.anh, self.cau = [so_du], so_du, []

	def sql(self, q, args=None, **k):
		ql = " ".join(q.lower().split())
		self.cau.append(ql)
		if "tabcustomer" in ql:
			return []
		if "sum(diem)" in ql:
			khoa = "for update" in ql or "lock in share mode" in ql
			return [[sum(self.but) if khoa else self.anh]]
		return []


@ca("Codex #557 P1: hai đơn web cùng khách chạy song song không tiêu hai lần một số dư (đọc số dư có khoá sau khi khoá khách)")
def _():
	import sys
	from vagabond import diem_otp

	so = _SoMVCC(50000)
	f = types.SimpleNamespace(db=so)
	kh = types.SimpleNamespace(_ghi_so_diem=lambda khach, diem, loai, ref, gc: so.but.append(diem))
	cd = {"quy_doi": 1.0, "tran_pt": 50.0, "bill_toi_thieu": 10000.0}
	with patch.dict(sys.modules, {"frappe": f, "vagabond.khach_hang": kh}), patch.object(diem_otp, "frappe", f), \
			patch.object(dw, "_cd", lambda: cd):
		# Hai giao dịch cùng chụp số dư 50.000 từ lúc tạo đơn (thong_tin), đơn A ghi trước.
		a = dw.giu_diem("WEB-A", "KH-1", 50000, 200000)
		b = dw.giu_diem("WEB-B", "KH-1", 50000, 200000)
	la("đơn A giữ đủ, đơn B không giữ được", (a, b), (50000, 0))
	la("sổ không âm", sum(so.but), 0)


@ca("Codex #557 P2: điểm sắp hết hạn trả đúng số mất vào ngày đầu tiên, không cộng đợt mất ngày khác")
def _():
	la("100 điểm mất 16/11, 200 điểm mất 26/11", dw.sap_het_han([("2025-11-15", 100), ("2025-11-25", 200)], "2026-11-12", 12),
		{"diem": 100, "ngay": "16/11/2026"})
	la("cùng ngày thì cộng", dw.sap_het_han([("2025-11-15", 100), ("2025-11-15", 50)], "2026-11-12", 12),
		{"diem": 150, "ngay": "16/11/2026"})


class _SoHoanMVCC:
	"""Sổ điểm giả cho hoàn điểm: đọc thường (kể cả frappe.db.exists) thấy ảnh chụp
	đầu giao dịch, đọc có khoá thấy bản đã commit."""

	def __init__(self, dong):
		self.dong, self.anh = list(dong), list(dong)

	def _bang(self, q):
		return self.dong if ("for update" in q or "lock in share mode" in q) else self.anh

	def sql(self, q, args=None, **k):
		ql = " ".join(q.lower().split())
		if "tabvagabond don web" in ql:
			return []
		if "tabvagabond so diem" in ql:
			loai, gc = args[0], args[1]
			ds = [r for r in self._bang(ql) if r["loai"] == loai and r["ghi_chu"] == gc]
			if "sum(diem)" in ql:
				tong = {}
				for r in ds:
					tong[r["khach"]] = tong.get(r["khach"], 0) + r["diem"]
				return [(k2, v) for k2, v in tong.items()]
			return [(len(ds),)] if "count(" in ql else [(r["name"],) for r in ds]
		return []

	def exists(self, dt, f):
		return any(all(r.get(k2) == v for k2, v in f.items()) for r in self.anh)


@ca("Codex #557 vòng 2 P1: lượt quét định kỳ và hoàn ngay khi Pancake từ chối chồng nhau thì vẫn hoàn ĐÚNG MỘT lần")
def _():
	import sys
	from vagabond import diem_otp

	gc = dw._ghi_chu("DW-9")
	so = _SoHoanMVCC([dict(name="B1", khach="KH-1", diem=-50000, loai=diem_otp.LOAI_TRU, ghi_chu=gc)])
	f = types.SimpleNamespace(db=so, log_error=lambda **k: None, get_traceback=lambda: "")
	# Lượt quét đã chụp sổ (chưa có bút hoàn) thì lượt hoàn ngay commit bút hoàn 50.000.
	so.dong.append(dict(name="B2", khach="KH-1", diem=50000, loai=diem_otp.LOAI_HOAN, ghi_chu=gc))
	ghi = []
	kh = types.SimpleNamespace(_ghi_so_diem=lambda khach, diem, loai, ref, g: ghi.append((khach, diem, loai)))
	zkb = types.SimpleNamespace(cho_hoan_diem=lambda *a: None)
	with patch.dict(sys.modules, {"frappe": f, "vagabond.khach_hang": kh, "vagabond.zalo_kich_ban": zkb}):
		n = dw.hoan_don_web("DW-9", "quét định kỳ")
	la("lượt quét không hoàn lần hai", (n, ghi), (0, []))


@ca("Codex #557 vòng 3 P2: bút tích cuối tháng báo đúng ngày mất theo mốc cuốn chiếu của việc định kỳ")
def _():
	from vagabond import diem_han
	r = dw.sap_het_han([("2026-02-28", 100)], "2026-03-12", 1)
	la("28/02 hạn 1 tháng mất ngày 01/04", r, {"diem": 100, "ngay": "01/04/2026"})
	# Ngày báo phải đúng ngày đầu tiên việc định kỳ (mốc = hôm đó lùi han_thang) thấy bút đã quá hạn.
	for but, hn, han in ((
			[("2026-01-31", 80)], "2026-02-20", 1), ([("2025-11-30", 50), ("2025-12-31", 60)], "2026-11-20", 12),
			([("2024-02-29", 70)], "2025-02-10", 12)):
		r = dw.sap_het_han(but, hn, han)
		d, m, y = (int(x) for x in r["ngay"].split("/"))
		ngay = dw.date(y, m, d)
		truoc = str(dw.cong_thang(ngay - dw.timedelta(days=1), -han))
		la("%s: hôm trước chưa mất, hôm đó mất" % but, (
			diem_han.qua_han_cuon_chieu(but, truoc) - diem_han.qua_han_cuon_chieu(but, str(dw.cong_thang(dw._ngay(hn), -han))),
			diem_han.qua_han_cuon_chieu(but, str(dw.cong_thang(ngay, -han))) > 0), (0, True))
