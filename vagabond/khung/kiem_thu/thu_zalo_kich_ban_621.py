# -*- coding: utf-8 -*-
"""v621: tin Zalo tự động cho khách (sau mua hàng, sinh nhật, lâu chưa quay lại).

Anh Việt 29/10/2026 chốt: tự động hoàn toàn có trần và giờ gửi; tin khuyến mãi
chỉ gửi khách đã đồng ý nhận tin Zalo. Luật Zalo kiểm cùng ngày: mọi tin qua máy
phải theo mẫu đã duyệt; tin khuyến mãi cần hạn mức tháng (OA hiện 0) và khách
phải từng nhận tin chăm sóc.

Mỗi ca chốt một đường lỗi có thật:
  - gửi trùng (hai lượt quét, hai lượt gửi);
  - phát voucher khi Zalo không cho gửi (mã nằm im, khách không biết);
  - gửi cho khách đã rút đồng ý giữa lúc quét và lúc gửi;
  - sai kiểu tham số làm Zalo từ chối cả tin;
  - gửi ngoài giờ (Zalo cấm 22h tới 6h), vượt trần;
  - hoá đơn huỷ sau khi tích điểm vẫn nhận tin cảm ơn.
Phần chạm hệ chạy trên lớp Frappe giả, vá đúng lời gọi hàm thật dùng.
"""

import datetime as dt
import json
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import zalo_kich_ban as zk  # noqa: E402

D8 = dt.date


class D(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v


# ------------------------------------------------------------ phần thuần

@ca("v621 giờ gửi: kẹp vào 6h tới 22h, đảo chỗ khi gõ ngược, trong giờ tính nửa mở")
def _gio():
	la("gõ ngược", zk.gio_hop_le(20, 8), (8, 20))
	la("0 tới 24 bị kẹp", zk.gio_hop_le(0, 24), (6, 22))
	la("chữ và rỗng về mặc định", zk.gio_hop_le("abc", ""), (8, 20))
	la("bằng nhau về mặc định", zk.gio_hop_le(9, 9), (8, 20))
	luc = dt.datetime(2026, 10, 29, 19, 59)
	dung("19:59 trong 8-20", zk.trong_gio(luc, 8, 20))
	dung("20:00 ngoài 8-20", not zk.trong_gio(luc.replace(hour=20, minute=0), 8, 20))
	dung("23h không bao giờ trong giờ dù gõ 0-24", not zk.trong_gio(luc.replace(hour=23), 0, 24))
	dung("5h không bao giờ trong giờ dù gõ 0-24", not zk.trong_gio(luc.replace(hour=5), 0, 24))


@ca("v621 sinh nhật: đúng N ngày nữa, qua năm, người sinh 29/02 được chúc 28/02 năm thường")
def _sinh_nhat():
	dung("trước 3 ngày", zk.den_sinh_nhat("1990-11-01", D8(2026, 10, 29), 3))
	dung("không phải hôm khác", not zk.den_sinh_nhat("1990-11-02", D8(2026, 10, 29), 3))
	dung("qua năm: sinh 01/01, gửi 29/12", zk.den_sinh_nhat("1985-01-01", D8(2026, 12, 29), 3))
	dung("đúng ngày khi đặt 0", zk.den_sinh_nhat("1990-10-29", D8(2026, 10, 29), 0))
	dung("29/02 năm thường là 28/02", zk.den_sinh_nhat("1992-02-29", D8(2027, 2, 25), 3))
	dung("29/02 năm nhuận vẫn là 29/02", not zk.den_sinh_nhat("1992-02-29", D8(2028, 2, 25), 3))
	dung("ngày sinh hỏng", not zk.den_sinh_nhat("abc", D8(2026, 10, 29), 3))
	la("quét 28/02 năm thường gồm cả người sinh 29/02", zk.ngay_sinh_can_quet(D8(2027, 2, 28)), [(2, 28), (2, 29)])
	la("năm nhuận thì không", zk.ngay_sinh_can_quet(D8(2028, 2, 28)), [(2, 28)])


@ca("v621 lâu chưa quay lại: vắng đủ N ngày trong cửa sổ 3 ngày; khoá theo ngày mua cuối")
def _quay_lai():
	dung("đúng 60", zk.vang_mat_du("2026-08-30", D8(2026, 10, 29), 60))
	dung("62 vẫn trong cửa sổ", zk.vang_mat_du("2026-08-28", D8(2026, 10, 29), 60))
	dung("63 ra khỏi cửa sổ (đã có lượt trước)", not zk.vang_mat_du("2026-08-27", D8(2026, 10, 29), 60))
	dung("59 chưa đủ", not zk.vang_mat_du("2026-08-31", D8(2026, 10, 29), 60))
	dung("N = 0 là tắt", not zk.vang_mat_du("2026-08-30", D8(2026, 10, 29), 0))
	la("khoá sau mua theo hoá đơn", zk.khoa_tin("sau_mua", "K1", "HDB-1"), "sau_mua:HDB-1")
	la("khoá sinh nhật theo năm", zk.khoa_tin("sinh_nhat", "K1", moc=2026), "sinh_nhat:K1:2026")
	la("khoá quay lại theo ngày mua cuối", zk.khoa_tin("quay_lai", "K1", moc=D8(2026, 8, 30)), "quay_lai:K1:2026-08-30")


@ca("v621 tên trên tin: số điện thoại hay rỗng thành Quý khách; chữ hoa toàn bộ thành chữ thường có hoa đầu")
def _ten():
	la("số điện thoại", zk.ten_goi("0901 486 556"), "Quý khách")
	la("rỗng", zk.ten_goi("  "), "Quý khách")
	la("hoa toàn bộ", zk.ten_goi("NGUYỄN  VĂN AN"), "Nguyễn Văn An")
	la("giữ nguyên tên thường", zk.ten_goi("Lan Anh"), "Lan Anh")


@ca("v621 tham số mẫu: đúng kiểu Zalo đòi (số, ngày, chữ có trần); thiếu tham số bắt buộc thì không gửi")
def _tham_so():
	ts = [{"name": "ten_khach", "type": "STRING", "maxLength": 30}, {"name": "tong_tien", "type": "NUMBER", "maxLength": 20},
		{"name": "ngay_mua", "type": "DATE", "maxLength": 20}, {"name": "hang", "type": "STRING", "maxLength": 5},
		{"name": "ghi_chu", "type": "STRING", "maxLength": 30, "require": False}]
	data, thieu = zk.du_lieu_mau({"ten_khach": "Lan", "tong_tien": "1.450.000đ", "ngay_mua": "29/10/2026 15:30", "hang": "EXPLORER"}, ts)
	la("dữ liệu", data, {"ten_khach": "Lan", "tong_tien": "1450000", "ngay_mua": "29/10/2026", "hang": "EXPLO"})
	la("không thiếu (ô không bắt buộc bỏ qua)", thieu, [])
	_, thieu = zk.du_lieu_mau({"ten_khach": "Lan"}, ts)
	la("thiếu ba tham số bắt buộc", thieu, ["tong_tien", "ngay_mua", "hang"])
	la("số thật", zk.chuan_tham_so(9000.0, "NUMBER", 20), "9000")
	la("ngày ISO", zk.chuan_tham_so("2026-11-30", "DATE", 20), "30/11/2026")
	la("số 0", zk.so_chuoi("0đ"), "0")


@ca("v621 ô voucher: tự viết từ chương trình (phần trăm, số tiền, hoá đơn tối thiểu); ô người điền thắng và bị cắt đúng trần")
def _uu_dai():
	la("phần trăm", zk.mo_ta_uu_dai({"kieu_giam": "Phan tram", "gia_tri": 10}), ("Giảm 10%", "Dùng 1 lần cho 1 hoá đơn"))
	la("số tiền và tối thiểu", zk.mo_ta_uu_dai({"kieu_giam": "So tien", "gia_tri": 50000, "hd_toi_thieu": 300000}),
		("Giảm 50.000đ", "Hoá đơn từ 300.000đ"))
	la("không giá trị: dùng tên chương trình", zk.mo_ta_uu_dai({"ten": "Quà sinh nhật thành viên"})[0], "Quà sinh nhật thành viên")
	t, d = zk.mo_ta_uu_dai({}, "Một ly cà phê và bánh nhỏ cho bạn nhân dịp sinh nhật", "x" * 60)
	la("cắt trong 30 chữ, không để khoảng trắng thừa", t, "Một ly cà phê và bánh nhỏ cho")
	la("cắt 40", len(d), 40)


@ca("v621 lỗi Zalo: câu tiếng Việt cho mã hay gặp; lỗi cả lượt gồm hết tiền, hết hạn mức, ngoài giờ")
def _loi():
	m, c = zk.y_nghia_loi({"error": -140, "message": "User not eligible"})
	la("-140", m, -140)
	dung("-140 nói rõ lý do", "chưa nhận tin chăm sóc" in c and c.endswith("(mã -140)"))
	la("thành công", zk.y_nghia_loi({"error": 0}), (0, ""))
	dung("mã lạ dùng câu Zalo", zk.y_nghia_loi({"error": -999, "message": "abc"})[1].startswith("abc"))
	la("trả lời lạ", zk.y_nghia_loi(None)[0], -1)
	for ma in (-115, -137, -144, -1441, -133, -131):
		dung("%s dừng lượt" % ma, ma in zk.LOI_DUNG_LUOT)
	for ma in (-140, -118, -1471):
		dung("%s chỉ là lỗi của một khách" % ma, ma not in zk.LOI_DUNG_LUOT)


@ca("v621 sẵn sàng: tắt, chưa có mẫu, mẫu chưa duyệt, tin khuyến mãi chưa chọn chương trình đều không gửi và nói đúng lý do")
def _san_sang():
	c = {"ma": "sinh_nhat", "bat": 1, "ma_mau": "659377", "mau_trang_thai": "ENABLE", "ctkm": "KM-1"}
	la("đủ", zk.mau_san_sang(c), (True, ""))
	la("tắt", zk.mau_san_sang(dict(c, bat=0))[1], "Kịch bản đang tắt.")
	la("chưa mã mẫu", zk.mau_san_sang(dict(c, ma_mau=" "))[1], "Chưa gắn mã mẫu Zalo.")
	la("đang chờ duyệt", zk.mau_san_sang(dict(c, mau_trang_thai="PENDING_REVIEW"))[1], "Mẫu tin đang chờ zalo duyệt.")
	la("chưa chọn chương trình", zk.mau_san_sang(dict(c, ctkm=""))[1], "Chưa chọn chương trình khuyến mãi để phát voucher.")
	la("sau mua không cần chương trình", zk.mau_san_sang(dict(c, ma="sau_mua", ctkm=""))[0], True)
	la("trần", (zk.con_duoc_gui(300, 120), zk.con_duoc_gui(5, 9), zk.con_duoc_gui("", 0)), (180, 0, 0))


# ------------------------------------------------------------ phần chạm hệ

BAY_GIO = dt.datetime(2026, 10, 29, 10, 0, 0)


def _gd(v):
	if isinstance(v, dt.datetime):
		return v
	return dt.datetime.fromisoformat(str(v)[:19])


TS_SAU_MUA = [{"name": n, "type": t, "maxLength": m, "require": True} for n, t, m in (
	("ten_khach", "STRING", 30), ("ma_hoa_don", "STRING", 30), ("ngay_mua", "STRING", 20), ("tong_tien", "NUMBER", 12),
	("diem_tich", "NUMBER", 20), ("tong_diem", "NUMBER", 20), ("hang", "STRING", 30))]
TS_VC = [{"name": n, "type": t, "maxLength": m, "require": True} for n, t, m in (
	("ten_khach", "STRING", 30), ("ten_uu_dai", "STRING", 30), ("dieu_kien", "STRING", 30), ("han_dung", "DATE", 20),
	("ma_voucher", "STRING", 30))]


class Moi:
	"""Lớp giả cơ sở dữ liệu tối thiểu cho việc gửi: dòng sổ, voucher, hoá đơn."""

	def __init__(self, cau_hinh, rows, ho_so, zalo_tra, si=None, ctkm=None, han_muc=999, da_gui=0):
		self.c, self.rows, self.hs, self.tra = cau_hinh, rows, ho_so, list(zalo_tra)
		self.si = si or {}
		self.ctkm = ctkm or D(name="KM-SN", ten="Quà sinh nhật", cach_ma="Ma dung mot lan", bat=1, kieu_giam="Phan tram", gia_tri=10, hd_toi_thieu=0)
		self.han_muc, self.da_gui = han_muc, da_gui
		self.goi, self.sv, self.chen, self.lay = [], [], [], []
		self.ma_sinh = iter(["VC1", "VC2", "VC3", "VC4"])
		# Đồng hồ: mặc định đứng yên; ca giờ gửi cho nó chạy theo số tin đã gửi.
		self.dong_ho = lambda: BAY_GIO

	def get_value(self, dt_, n, cot=None, as_dict=False, **k):
		if dt_ == "Sales Invoice":
			return self.si.get(n)
		if dt_ == "Vagabond CTKM":
			return self.ctkm
		return None

	def get_all(self, dt_, filters=None, fields=None, order_by=None, limit_page_length=None, **k):
		self.lay.append((dt_, filters, limit_page_length))
		ra = [r for r in self.rows if r.trang_thai == zk.TT_CHO]
		return ra[:limit_page_length] if limit_page_length else ra

	def set_value(self, dt_, n, v, *a, **k):
		self.sv.append((dt_, n, v if isinstance(v, dict) else {a[0] if a else "?": v}))
		if dt_ == zk.DT_TIN:
			for r in self.rows:
				if r.name == n and isinstance(v, dict) and "trang_thai" in v:
					r.trang_thai = v["trang_thai"]

	def get_doc(self, d, *a, **k):
		moi = self

		class Doc(D):
			def insert(self, **kk):
				moi.chen.append(dict(self))
				return self
		return Doc(d if isinstance(d, dict) else {"doctype": d})

	def gui_mau(self, c, sdt, mau, data, dau_vet):
		self.goi.append((sdt, mau, data, dau_vet))
		return self.tra.pop(0) if self.tra else {"error": 0, "data": {"msg_id": "m"}}

	def chay(self, ham):
		fr = zk.frappe
		with um.patch.object(zk, "_cau_hinh", lambda ma: dict(self.c, ma=ma) if ma == self.c["ma"] else {"ma": ma, "bat": 0}), \
				um.patch.object(zk, "kiem_mau", lambda ma: dict(self.c, ma=ma)), \
				um.patch.object(zk, "_ho_so", lambda kh: self.hs[kh]), \
				um.patch.object(zk, "_da_gui_hom_nay", lambda ma: self.da_gui), \
				um.patch.object(zk, "_han_muc_km", lambda: self.han_muc), \
				um.patch.object(zk, "_bay_gio", lambda: self.dong_ho()), \
				um.patch.object(zk, "get_datetime", _gd), \
				um.patch.object(zk, "_cfg", lambda: {}), \
				um.patch.object(zk, "_gui_mau", self.gui_mau), \
				um.patch.object(zk, "_sinh_ma", lambda: next(self.ma_sinh)), \
				um.patch.object(fr.db, "get_value", self.get_value), \
				um.patch.object(fr.db, "get_all", self.get_all), \
				um.patch.object(fr.db, "set_value", self.set_value), \
				um.patch.object(fr.db, "sql", lambda *a, **k: []), \
				um.patch.object(fr, "get_doc", self.get_doc):
			return ham()

	def tt(self):
		return {r.name: r.trang_thai for r in self.rows}

	def voucher_huy(self):
		return [n for d, n, v in self.sv if d == "Vagabond Voucher" and v.get("trang_thai") == "Da huy"]

	def voucher_moi(self):
		return [x["ma"] for x in self.chen if x.get("doctype") == "Vagabond Voucher"]


def _cau(ma, **k):
	c = {"ma": ma, "bat": 1, "ma_mau": "659376" if ma == "sau_mua" else "659377", "mau_trang_thai": "ENABLE",
		"mau_tham_so": json.dumps(TS_SAU_MUA if ma == "sau_mua" else TS_VC), "mau_gia": "400", "ctkm": "" if ma == "sau_mua" else "KM-SN",
		"tran_ngay": 300, "gio_tu": 8, "gio_den": 20, "han_ngay": 14, "mau_kiem_luc": BAY_GIO}
	c.update(k)
	return c


def _hs(dong_y=True, sdt="84901486556", ten="Lan Anh"):
	return {"ten": ten, "sdt84": sdt, "dong_y": dong_y, "diem": 25400, "hang": "EXPLORER"}


@ca("v621 cảm ơn sau mua: điền đúng bảy tham số đúng kiểu, ghi Đã gửi kèm phí và nhật ký liên hệ; hoá đơn đã huỷ thì bỏ, không gọi Zalo")
def _gui_sau_mua():
	si = {"HDB-1": D(docstatus=1, posting_date=D8(2026, 10, 29), posting_time="15:30:12", grand_total=450000),
		"HDB-2": D(docstatus=2, posting_date=D8(2026, 10, 29), posting_time="16:00:00", grand_total=90000)}
	rows = [D(name="T1", khach="K1", hoa_don="HDB-1", diem=9000, khoa="sau_mua:HDB-1", trang_thai="Chờ gửi"),
		D(name="T2", khach="K2", hoa_don="HDB-2", diem=1800, khoa="sau_mua:HDB-2", trang_thai="Chờ gửi")]
	m = Moi(_cau("sau_mua"), rows, {"K1": _hs(), "K2": _hs(ten="Bình")}, [], si=si)
	m.chay(zk.gui_hang_doi)
	la("chỉ gọi Zalo cho hoá đơn còn hiệu lực", [g[3] for g in m.goi], ["sau_mua:HDB-1"])
	la("tham số", m.goi[0][2], {"ten_khach": "Lan Anh", "ma_hoa_don": "HDB-1", "ngay_mua": "29/10/2026 15:30", "tong_tien": "450000",
		"diem_tich": "9000", "tong_diem": "25400", "hang": "EXPLORER"})
	la("đúng mẫu và số", m.goi[0][:2], ("84901486556", "659376"))
	la("trạng thái", m.tt(), {"T1": "Đã gửi", "T2": "Bỏ qua"})
	v1 = [v for d, n, v in m.sv if n == "T1" and v.get("trang_thai") == "Đã gửi"][0]
	la("ghi phí và mã mẫu", (v1["gia"], v1["ma_mau"]), (400.0, "659376"))
	la("không phát voucher cho tin chăm sóc", m.voucher_moi(), [])
	la("nhật ký liên hệ", [(x["khach"], x["kenh"]) for x in m.chen if x.get("doctype") == "Vagabond Lien He Khach"], [("K1", "Zalo OA")])


@ca("v621 tin khuyến mãi: Zalo chưa cấp hạn mức thì KHÔNG phát voucher, KHÔNG gọi Zalo, dòng để chờ")
def _han_muc_0():
	rows = [D(name="T1", khach="K1", khoa="sinh_nhat:K1:2026", trang_thai="Chờ gửi")]
	m = Moi(_cau("sinh_nhat"), rows, {"K1": _hs()}, [], han_muc=0)
	tom = m.chay(zk.gui_hang_doi)
	la("không gọi Zalo", m.goi, [])
	la("không phát voucher", m.voucher_moi(), [])
	la("dòng vẫn chờ", m.tt(), {"T1": "Chờ gửi"})
	dung("tóm tắt nói rõ", "hạn mức tin khuyến mãi" in tom["sinh_nhat"])


@ca("v621 tin khuyến mãi: khách rút đồng ý sau lúc quét thì bỏ, không phát mã; khách đủ điều kiện nhận đúng mã vừa phát")
def _dong_y():
	rows = [D(name="T1", khach="K1", khoa="sinh_nhat:K1:2026", trang_thai="Chờ gửi"),
		D(name="T2", khach="K2", khoa="sinh_nhat:K2:2026", trang_thai="Chờ gửi")]
	m = Moi(_cau("sinh_nhat"), rows, {"K1": _hs(dong_y=False), "K2": _hs(ten="Bình")}, [])
	m.chay(zk.gui_hang_doi)
	la("trạng thái", m.tt(), {"T1": "Bỏ qua", "T2": "Đã gửi"})
	la("chỉ một mã được phát", m.voucher_moi(), ["VC1"])
	la("tin mang đúng mã và hạn 14 ngày", (m.goi[0][2]["ma_voucher"], m.goi[0][2]["han_dung"]), ("VC1", "12/11/2026"))
	la("ô voucher tự viết", (m.goi[0][2]["ten_uu_dai"], m.goi[0][2]["dieu_kien"]), ("Giảm 10%", "Dùng 1 lần cho 1 hoá đơn"))
	vc = [x for x in m.chen if x.get("doctype") == "Vagabond Voucher"][0]
	la("mã ghi cho đúng khách", (vc["danh_cho"], vc["ctkm"], vc["trang_thai"]), ("K2", "KM-SN", "Chua dung"))
	la("ghi voucher lên dòng sổ", [v.get("voucher") for d, n, v in m.sv if n == "T2" and v.get("trang_thai") == "Đã gửi"], ["VC1"])


@ca("v621 Zalo từ chối một khách (-140): dòng Lỗi kèm câu, voucher vừa phát bị huỷ, lượt đi tiếp; hết hạn mức tháng (-1441): dừng lượt, dòng để chờ")
def _zalo_tu_choi():
	rows = [D(name="T%d" % i, khach="K%d" % i, khoa="sinh_nhat:K%d:2026" % i, trang_thai="Chờ gửi") for i in (1, 2, 3, 4)]
	hs = {"K%d" % i: _hs(ten="Khách %d" % i) for i in (1, 2, 3, 4)}
	m = Moi(_cau("sinh_nhat"), rows, hs, [{"error": -140, "message": "x"}, {"error": 0, "data": {}}, {"error": -1441, "message": "y"}])
	tom = m.chay(zk.gui_hang_doi)
	la("gọi đúng ba lần rồi dừng", len(m.goi), 3)
	la("trạng thái", m.tt(), {"T1": "Lỗi", "T2": "Đã gửi", "T3": "Chờ gửi", "T4": "Chờ gửi"})
	la("huỷ mã của hai tin không đi", m.voucher_huy(), ["VC1", "VC3"])
	loi1 = [v["loi"] for d, n, v in m.sv if n == "T1" and v.get("trang_thai") == "Lỗi"][0]
	dung("câu lỗi -140", "(mã -140)" in loi1)
	dung("dòng chờ ghi lý do dừng", any(n == "T3" and "(mã -1441)" in (v.get("loi") or "") for d, n, v in m.sv))
	dung("tóm tắt có dừng lượt", "Dừng lượt" in tom["sinh_nhat"])


@ca("v621 trần mỗi ngày: đã gửi 299 trên trần 300 thì chỉ lấy 1 dòng; đủ trần thì không lấy dòng nào")
def _tran():
	rows = [D(name="T%d" % i, khach="K1", hoa_don="HDB-1", diem=1, khoa="sau_mua:%d" % i, trang_thai="Chờ gửi") for i in (1, 2, 3)]
	si = {"HDB-1": D(docstatus=1, posting_date=D8(2026, 10, 29), posting_time="", grand_total=1)}
	m = Moi(_cau("sau_mua"), rows, {"K1": _hs()}, [], si=si, da_gui=299)
	m.chay(zk.gui_hang_doi)
	la("chỉ một tin", len(m.goi), 1)
	la("giới hạn câu đọc", [x[2] for x in m.lay if x[0] == zk.DT_TIN], [1])
	m = Moi(_cau("sau_mua"), rows, {"K1": _hs()}, [], si=si, da_gui=300)
	tom = m.chay(zk.gui_hang_doi)
	la("đủ trần thì không gửi", m.goi, [])
	la("tóm tắt", tom["sau_mua"], "Đã đủ trần tin hôm nay.")


@ca("v621 không gửi ngoài giờ, khi mẫu chưa duyệt hay khi kịch bản tắt")
def _chan():
	rows = [D(name="T1", khach="K1", hoa_don="HDB-1", diem=1, khoa="sau_mua:HDB-1", trang_thai="Chờ gửi")]
	si = {"HDB-1": D(docstatus=1, posting_date=D8(2026, 10, 29), posting_time="", grand_total=1)}
	for cau, ly_do in ((_cau("sau_mua", gio_tu=11, gio_den=20), "Ngoài giờ gửi."),
			(_cau("sau_mua", mau_trang_thai="PENDING_REVIEW"), "Mẫu tin đang chờ zalo duyệt."),
			(_cau("sau_mua", bat=0), None)):
		m = Moi(cau, [D(r) for r in rows], {"K1": _hs()}, [], si=si)
		tom = m.chay(zk.gui_hang_doi)
		la("không gọi Zalo: %s" % ly_do, m.goi, [])
		la("lý do: %s" % ly_do, tom.get("sau_mua"), ly_do)


@ca("v621 mẫu đòi tham số máy không có: không gửi, dòng Lỗi nói rõ tên tham số, voucher vừa phát bị huỷ")
def _thieu():
	ts = TS_VC + [{"name": "so_ban", "type": "STRING", "maxLength": 10, "require": True}]
	rows = [D(name="T1", khach="K1", khoa="sinh_nhat:K1:2026", trang_thai="Chờ gửi")]
	m = Moi(_cau("sinh_nhat", mau_tham_so=json.dumps(ts)), rows, {"K1": _hs()}, [])
	m.chay(zk.gui_hang_doi)
	la("không gọi Zalo", m.goi, [])
	la("Lỗi", m.tt(), {"T1": "Lỗi"})
	la("huỷ mã", m.voucher_huy(), ["VC1"])
	dung("câu nêu tên tham số", any("so_ban" in (v.get("loi") or "") for d, n, v in m.sv))


@ca("v621 chương trình không phát mã dùng một lần hay đang tắt: không phát mã, dòng để chờ, tóm tắt chỉ đúng việc cần sửa")
def _ctkm_sai():
	# Từ vòng sửa PR #517: chương trình chưa hợp lệ thì giữ cả kịch bản chờ
	# (sửa chương trình xong lượt sau gửi tiếp), không đánh Lỗi từng khách.
	rows = [D(name="T1", khach="K1", khoa="sinh_nhat:K1:2026", trang_thai="Chờ gửi")]
	m = Moi(_cau("sinh_nhat"), rows, {"K1": _hs()}, [], ctkm=D(name="KM-X", ten="Tết", cach_ma="Ma co dinh", bat=1))
	tom = m.chay(zk.gui_hang_doi)
	la("không gọi Zalo, không phát mã", (m.goi, m.voucher_moi()), ([], []))
	la("dòng để chờ", m.tt(), {"T1": "Chờ gửi"})
	dung("câu nói cần Mã dùng một lần", "Mã dùng một lần" in (tom.get("sinh_nhat") or ""))


@ca("PR517 Codex: chương trình đã hết hạn hay chưa bắt đầu thì không phát mã, không gửi, dòng để chờ; hạn voucher kẹp theo ngày kết thúc")
def _ctkm_het_han():
	# Tái hiện finding Codex trên 5ed80e8: CTKM vẫn bật nhưng qua den_ngay thì
	# máy vẫn phát mã và gửi tin, trong khi quầy (khuyen_mai._hop_thoi_gian)
	# từ chối chương trình hết hạn: khách nhận quà không dùng được.
	km = dict(name="KM-SN", ten="Quà sinh nhật", cach_ma="Ma dung mot lan", bat=1, kieu_giam="Phan tram", gia_tri=10, hd_toi_thieu=0)
	for them, chu in ((dict(den_ngay=D8(2026, 10, 28)), "hết hạn"), (dict(tu_ngay=D8(2026, 11, 1)), "chưa tới ngày bắt đầu")):
		rows = [D(name="T1", khach="K1", khoa="sinh_nhat:K1:2026", trang_thai="Chờ gửi")]
		m = Moi(_cau("sinh_nhat"), rows, {"K1": _hs()}, [], ctkm=D(km, **them))
		tom = m.chay(zk.gui_hang_doi)
		la("%s: không gọi Zalo, không phát mã" % chu, (m.goi, m.voucher_moi()), ([], []))
		la("%s: dòng vẫn chờ" % chu, m.tt(), {"T1": "Chờ gửi"})
		dung("%s: tóm tắt nói rõ" % chu, chu in (tom.get("sinh_nhat") or ""))
	# Chương trình còn 5 ngày, voucher đặt 14 ngày: hạn trên mã và trên tin là ngày kết thúc chương trình.
	rows = [D(name="T1", khach="K1", khoa="sinh_nhat:K1:2026", trang_thai="Chờ gửi")]
	m = Moi(_cau("sinh_nhat"), rows, {"K1": _hs()}, [], ctkm=D(km, den_ngay=D8(2026, 11, 3)))
	m.chay(zk.gui_hang_doi)
	vc = [x for x in m.chen if x.get("doctype") == "Vagabond Voucher"][0]
	la("hạn mã kẹp theo chương trình", str(vc["han_dung"]), "2026-11-03")
	la("hạn trên tin", m.goi[0][2]["han_dung"], "03/11/2026")
	# Hạn mã mặc định của chương trình (han_ma) ngắn hơn cũng kẹp.
	rows = [D(name="T1", khach="K1", khoa="sinh_nhat:K1:2026", trang_thai="Chờ gửi")]
	m = Moi(_cau("sinh_nhat"), rows, {"K1": _hs()}, [], ctkm=D(km, han_ma=D8(2026, 11, 1)))
	m.chay(zk.gui_hang_doi)
	la("kẹp theo hạn mã", m.goi[0][2]["han_dung"], "01/11/2026")


@ca("PR517 Codex: lượt bắt đầu sát giờ đóng thì dừng đúng giờ, các dòng còn lại để chờ")
def _het_gio_giua_luot():
	# Tái hiện finding Codex trên 5ed80e8: trong_gio chỉ kiểm một lần trước
	# vòng gửi; lượt bắt đầu 19:59 với nhiều dòng chờ vẫn gửi qua 20:00.
	si = {"HDB-%d" % i: D(docstatus=1, posting_date=D8(2026, 10, 29), posting_time="", grand_total=1) for i in range(1, 6)}
	rows = [D(name="T%d" % i, khach="K1", hoa_don="HDB-%d" % i, diem=1, khoa="sau_mua:HDB-%d" % i, trang_thai="Chờ gửi") for i in range(1, 6)]
	m = Moi(_cau("sau_mua"), rows, {"K1": _hs()}, [], si=si)
	dau = dt.datetime(2026, 10, 29, 19, 59, 0)
	m.dong_ho = lambda: dau + dt.timedelta(seconds=40 * len(m.goi))
	tom = m.chay(zk.gui_hang_doi)
	la("chỉ gửi trước 20:00", len(m.goi), 2)
	la("còn lại để chờ", m.tt(), {"T1": "Đã gửi", "T2": "Đã gửi", "T3": "Chờ gửi", "T4": "Chờ gửi", "T5": "Chờ gửi"})
	dung("tóm tắt nói hết giờ", "Hết giờ gửi" in (tom.get("sau_mua") or ""))


@ca("PR517 Codex: đổi mã mẫu thì xoá trạng thái duyệt và tham số cũ ngay khi lưu; Zalo chưa trả lời thì không gửi")
def _doi_mau():
	# Tái hiện finding Codex trên 5ed80e8: đổi 659377 sang mã khác mà lần hỏi
	# Zalo lỗi mạng thì dòng giữ ENABLE và tham số mẫu cũ, máy gửi bằng mẫu mới
	# với tham số cũ trong sáu giờ.
	from vagabond import crm

	fr = zk.frappe
	db = _cau("sinh_nhat")

	def sv(dt_, n, v, *a, **k):
		if isinstance(v, dict):
			db.update(v)
		else:
			db[v] = a[0] if a else None
	with um.patch.object(crm, "_kiem", lambda vai, viec: None), \
			um.patch.object(zk, "_dam_bao", lambda: None), um.patch.object(zk, "_cau_hinh", lambda ma: dict(db)), \
			um.patch.object(zk, "ds_kich_ban", lambda: "ds"), um.patch.object(zk, "_bay_gio", lambda: BAY_GIO), \
			um.patch.object(zk, "_doc_mau", lambda mau: {"ok": 0, "loi": "Không kết nối được Zalo."}), \
			um.patch.object(fr.db, "set_value", sv):
		zk.luu_kich_ban("sinh_nhat", json.dumps({"ma_mau": "700001"}))
	la("mã mới đã lưu", db["ma_mau"], "700001")
	la("không còn trạng thái duyệt và tham số của mẫu cũ", (db.get("mau_trang_thai"), zk.doc_tham_so(db.get("mau_tham_so"))), ("", []))
	la("không gửi được tới khi Zalo trả lời", zk.mau_san_sang(db)[0], False)
	dung("lý do nói rõ", "Không kết nối được Zalo" in (db.get("mau_ly_do") or ""))
	# Sửa thẳng trên Desk (form doctype) cũng phải xoá như vậy.
	class Doc(D):
		def get_doc_before_save(self):
			return D(ma_mau="659377")
	doc = Doc(_cau("sinh_nhat", ma_mau="700002"))
	zk.doi_mau_tren_form(doc)
	la("Desk: xoá trạng thái cũ", (doc.get("mau_trang_thai"), doc.get("mau_tham_so")), ("", "[]"))
	doc = Doc(_cau("sinh_nhat", ma_mau="659377"))
	zk.doi_mau_tren_form(doc)
	la("Desk: không đổi mã thì giữ", doc.get("mau_trang_thai"), "ENABLE")


@ca("PR517 Codex: danh sách chọn chương trình bỏ cái đã hết hạn, ghi ngày kết thúc; thẻ kịch bản nói rõ khi chương trình đã chọn hết hạn")
def _ds_ctkm():
	fr = zk.frappe
	ds_km = [D(name="KM-HET", ten="Hè 2026", cach_ma="Ma dung mot lan", bat=1, den_ngay=D8(2026, 9, 30)),
		D(name="KM-CON", ten="Thu 2026", cach_ma="Ma dung mot lan", bat=1, den_ngay=D8(2026, 11, 30)),
		D(name="KM-MAI", ten="Noel", cach_ma="Ma dung mot lan", bat=1, tu_ngay=D8(2026, 12, 1)),
		D(name="KM-MO", ten="Thành viên", cach_ma="Ma dung mot lan", bat=1)]
	cau = {"sau_mua": _cau("sau_mua"), "sinh_nhat": _cau("sinh_nhat", ctkm="KM-HET"), "quay_lai": _cau("quay_lai", ctkm="KM-CON")}
	with um.patch.object(zk, "_quyen", lambda xem=True: None), um.patch.object(zk, "_dam_bao", lambda: None), \
			um.patch.object(zk, "_cau_hinh", lambda ma: dict(cau[ma])), um.patch.object(zk, "_bay_gio", lambda: BAY_GIO), \
			um.patch.object(zk, "_han_muc", lambda: {}), um.patch.object(zk, "_co_lap", lambda: True), \
			um.patch.object(zk, "_doc_ctkm", lambda ten: {d.name: d for d in ds_km}.get(ten)), \
			um.patch.object(fr.db, "sql", lambda *a, **k: []), \
			um.patch.object(fr, "get_all", lambda *a, **k: [D(x) for x in ds_km]):
		kq = zk.ds_kich_ban()
	la("bỏ chương trình hết hạn", [x["name"] for x in kq["ctkm"]], ["KM-CON", "KM-MAI", "KM-MO"])
	la("dòng phụ", [x["phu"] for x in kq["ctkm"]], ["Đến hết 30/11/2026", "Bắt đầu 01/12/2026, không giới hạn ngày", "Không giới hạn ngày"])
	the = {t["ma"]: t for t in kq["ds"]}
	la("thẻ sinh nhật không sẵn sàng", the["sinh_nhat"]["san_sang"], 0)
	dung("lý do nói hết hạn", "đã hết hạn" in the["sinh_nhat"]["ly_do"])
	la("thẻ quay lại sẵn sàng", the["quay_lai"]["san_sang"], 1)


@ca("PR517 Codex vòng 2: mất kết nối Zalo (-1) thì dừng lượt, dòng để chờ, lượt sau gửi lại; không loại vĩnh viễn")
def _mat_mang():
	# Tái hiện finding Codex trên 87c103b: hai phản hồi -1 làm cả hai dòng
	# thành Lỗi, lượt sau không gửi lại; khoá chống trùng chặn quét lại.
	si = {"HDB-%d" % i: D(docstatus=1, posting_date=D8(2026, 10, 29), posting_time="", grand_total=1) for i in (1, 2)}
	rows = [D(name="T%d" % i, khach="K1", hoa_don="HDB-%d" % i, diem=1, khoa="sau_mua:HDB-%d" % i, trang_thai="Chờ gửi") for i in (1, 2)]
	m = Moi(_cau("sau_mua"), rows, {"K1": _hs()}, [{"error": -1, "message": "Không gọi được Zalo"}, {"error": -1, "message": "Không gọi được Zalo"}], si=si)
	tom = m.chay(zk.gui_hang_doi)
	la("gọi một lần rồi dừng", len(m.goi), 1)
	la("cả hai dòng vẫn chờ", m.tt(), {"T1": "Chờ gửi", "T2": "Chờ gửi"})
	dung("tóm tắt có dừng lượt", "Dừng lượt" in tom["sau_mua"])
	m.tra = []
	m.chay(zk.gui_hang_doi)
	la("lượt sau có mạng thì gửi cả hai", m.tt(), {"T1": "Đã gửi", "T2": "Đã gửi"})
	# Phản hồi không đọc được (không có mã) cũng là lỗi cả lượt.
	rows = [D(name="T1", khach="K1", hoa_don="HDB-1", diem=1, khoa="sau_mua:HDB-1", trang_thai="Chờ gửi")]
	m = Moi(_cau("sau_mua"), rows, {"K1": _hs()}, ["<html>502</html>"], si=si)
	m.chay(zk.gui_hang_doi)
	la("phản hồi lạ: dòng vẫn chờ", m.tt(), {"T1": "Chờ gửi"})
	# Tin khuyến mãi: mã vừa phát bị huỷ, lượt sau phát mã mới.
	rows = [D(name="T1", khach="K1", khoa="sinh_nhat:K1:2026", trang_thai="Chờ gửi")]
	m = Moi(_cau("sinh_nhat"), rows, {"K1": _hs()}, [{"error": -1}])
	m.chay(zk.gui_hang_doi)
	la("huỷ mã của tin không đi", m.voucher_huy(), ["VC1"])
	la("dòng khuyến mãi vẫn chờ", m.tt(), {"T1": "Chờ gửi"})


@ca("PR517 Codex vòng 2: sổ tin tìm ở máy chủ theo tên khách, số điện thoại, hoá đơn, voucher (tìm được cả dòng chưa tải)")
def _tim_tin():
	la("rỗng thì không lọc", zk.dk_tim_tin("  "), [])
	dk = zk.dk_tim_tin("HDB-26-0012")
	dung("tìm hoá đơn", ["hoa_don", "like", "%HDB-26-0012%"] in dk)
	dung("tìm voucher", ["voucher", "like", "%HDB-26-0012%"] in dk)
	dk = zk.dk_tim_tin("0901 486 556")
	dung("số điện thoại gõ kiểu 09 tìm theo 84", ["sdt", "like", "%84901486556%"] in dk)
	dk = zk.dk_tim_tin("6556")
	dung("bốn số cuối", ["sdt", "like", "%6556%"] in dk)
	dung("tên có dấu", ["ten_khach", "like", "%Lan Anh%"] in zk.dk_tim_tin("Lan Anh"))
	la("bỏ dấu % người gõ", zk.dk_tim_tin("50%")[0], ["ten_khach", "like", "%50%"])
	fr = zk.frappe
	goi = []

	def ga(dt_, **k):
		goi.append(k)
		return []
	with um.patch.object(zk, "_quyen", lambda xem=True: None), um.patch.object(fr, "get_all", ga):
		zk.ds_tin("sau_mua", "", 0, "HDB-1")
		zk.ds_tin("sau_mua", "", 0, "")
	la("có tìm thì gửi or_filters", bool(goi[0].get("or_filters")), True)
	la("lọc kịch bản vẫn giữ", goi[0]["filters"], {"kich_ban": "sau_mua"})
	la("không tìm thì không or_filters", goi[1].get("or_filters"), None)


@ca("v621 quét sau mua: chỉ lượt tích điểm từ lúc bật (không gửi bù hoá đơn cũ), mỗi hoá đơn một dòng, quét lại không thêm")
def _quet_sau_mua():
	fr = zk.frappe
	ts_sql, chen, co = [], [], set()

	def sql(q, ts=None, *a, **k):
		ts_sql.append(ts)
		return [D(khach="K1", diem=9000, hoa_don="HDB-1"), D(khach="K2", diem=100, hoa_don="HDB-2")]

	class Doc(D):
		def insert(self, **k):
			chen.append(dict(self))
			co.add(self["khoa"])
			return self
	bat_luc = BAY_GIO - dt.timedelta(hours=2)
	with um.patch.object(zk, "_cau_hinh", lambda ma: {"ma": ma, "bat": 1, "bat_luc": bat_luc}), \
			um.patch.object(zk, "_bay_gio", lambda: BAY_GIO), um.patch.object(zk, "get_datetime", _gd), \
			um.patch.object(fr.db, "sql", sql), \
			um.patch.object(fr.db, "exists", lambda dt_, f=None, *a, **k: (f or {}).get("khoa") in co), \
			um.patch.object(fr, "get_doc", lambda d, *a, **k: Doc(d)):
		n1 = zk.quet_sau_mua()
		n2 = zk.quet_sau_mua()
	la("mốc quét là lúc bật, không phải 48 giờ trước", ts_sql[0], (bat_luc,))
	la("lượt đầu hai dòng, lượt sau không thêm", (n1, n2), (2, 0))
	la("dòng chờ", [(x["khoa"], x["trang_thai"], x["diem"]) for x in chen], [("sau_mua:HDB-1", "Chờ gửi", 9000), ("sau_mua:HDB-2", "Chờ gửi", 100)])
	with um.patch.object(zk, "_cau_hinh", lambda ma: {"ma": ma, "bat": 0}), um.patch.object(fr.db, "sql", sql):
		la("tắt thì không quét", zk.quet_sau_mua(), 0)


@ca("v621 quét sinh nhật: đúng ngày đích, có người sinh 29/02 khi đích là 28/02 năm thường, chỉ khách đã đồng ý; khoá theo năm của ngày đích")
def _quet_sn():
	fr = zk.frappe
	cau, chen = [], []

	def sql(q, ts=None, *a, **k):
		cau.append((q, ts))
		return [D(khach="K9")]

	class Doc(D):
		def insert(self, **k):
			chen.append(dict(self))
			return self
	with um.patch.object(zk, "_cau_hinh", lambda ma: {"ma": ma, "bat": 1, "so_ngay": 3}), \
			um.patch.object(fr.db, "sql", sql), um.patch.object(fr.db, "exists", lambda *a, **k: False), \
			um.patch.object(fr, "get_doc", lambda d, *a, **k: Doc(d)):
		zk.quet_sinh_nhat(D8(2027, 2, 25))
		zk.quet_sinh_nhat(D8(2026, 12, 29))
	la("tham số ngày 28/02/2027", cau[0][1], [2, 28, 2, 29])
	dung("chỉ khách đã đồng ý, không trong Danh sách không quảng cáo", "h.dy_zalo, '') = 'Đồng ý'" in cau[0][0] and "khong_quang_cao, 0) = 0" in cau[0][0])
	la("khoá theo năm của ngày đích", [x["khoa"] for x in chen], ["sinh_nhat:K9:2027", "sinh_nhat:K9:2027"])


@ca("v621 lưu cài đặt: bật lần đầu ghi lúc bật; giờ kẹp; chữ trên ô voucher cắt đúng trần; chương trình lạ bị chặn; vai chỉ xem không lưu được")
def _luu():
	from vagabond import crm

	fr = zk.frappe
	sv = []
	cu = {"ma": "sinh_nhat", "bat": 0, "ma_mau": "659377", "gio_tu": 8, "gio_den": 20, "tran_ngay": 300}
	with um.patch.object(crm, "_kiem", lambda vai, viec: None), \
			um.patch.object(zk, "_dam_bao", lambda: None), um.patch.object(zk, "_cau_hinh", lambda ma: dict(cu)), \
			um.patch.object(zk, "ds_kich_ban", lambda: "ds"), um.patch.object(zk, "_bay_gio", lambda: BAY_GIO), \
			um.patch.object(fr.db, "exists", lambda dt_, n=None, *a, **k: n == "KM-1"), \
			um.patch.object(fr.db, "set_value", lambda dt_, n, v, *a, **k: sv.append(v)):
		zk.luu_kich_ban("sinh_nhat", json.dumps({"bat": 1, "gio_tu": 23, "gio_den": 2, "ten_uu_dai": "x" * 50, "ctkm": "KM-1", "tran_ngay": "abc"}))
		nem("chương trình lạ", lambda: zk.luu_kich_ban("sinh_nhat", {"ctkm": "KM-LA"}))
		nem("kịch bản lạ", lambda: zk.luu_kich_ban("thang_hang", {"bat": 1}))
	v = sv[0]
	la("bật và lúc bật", (v["bat"], v["bat_luc"]), (1, BAY_GIO))
	la("giờ kẹp và đảo", (v["gio_tu"], v["gio_den"]), (6, 22))
	la("cắt 30", len(v["ten_uu_dai"]), 30)
	la("ô số hỏng giữ số cũ", v["tran_ngay"], 300)

	def cam(vai, viec):
		if vai == crm.CRM_LAP:
			raise fr.ValidationError("không có quyền")
	with um.patch.object(crm, "_kiem", cam):
		nem("vai chỉ xem không lưu", lambda: zk.luu_kich_ban("sau_mua", {"bat": 1}))
		nem("vai chỉ xem không gửi thử", lambda: zk.gui_thu("sau_mua", "0901486556"))


@ca("v621 nhịp 5 phút có khai trong hooks; dòng cấu hình mới luôn TẮT")
def _nhip():
	import ast
	import io
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	cay = ast.parse(io.open(os.path.join(goc, "hooks.py"), encoding="utf-8").read())
	se = None
	for nut in cay.body:
		if isinstance(nut, ast.Assign) and any(getattr(t, "id", "") == "scheduler_events" for t in nut.targets):
			se = ast.literal_eval(nut.value)
	dung("có trong nhịp 5 phút", "vagabond.zalo_kich_ban.chay_tu_dong" in se["cron"]["*/5 * * * *"])
	fr = zk.frappe
	chen = []

	class Doc(D):
		def insert(self, **k):
			chen.append(dict(self))
			return self
	with um.patch.object(fr.db, "exists", lambda *a, **k: False), um.patch.object(fr, "get_doc", lambda d, *a, **k: Doc(d)):
		zk._dam_bao()
	la("ba dòng, đều tắt", [(x["ma"], x["bat"]) for x in chen], [("sau_mua", 0), ("sinh_nhat", 0), ("quay_lai", 0)])
	la("gắn sẵn mẫu đã nộp", [x["ma_mau"] for x in chen], ["659376", "659377", "659378"])


@ca("v621 cửa gửi theo mẫu (zalo.gui_mau) và gui_tin đều đọc cờ kiểm thật: chạy bộ kiểm tích hợp không bắn tin ra máy khách")
def _co_kiem_that():
	# Đọc thân hàm bằng AST như thu_kiem_that: chặn kiểu "có chuỗi đâu đó
	# trong tệp" thì một dòng chú thích nhắc tên cờ cũng làm ca xanh giả.
	# Không nạp zalo.py vì tệp đó kéo thư viện mạng ở đầu tệp.
	import ast
	import io
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	cay = ast.parse(io.open(os.path.join(goc, "zalo.py"), encoding="utf-8").read())
	than = {n.name: ast.dump(n) for n in ast.walk(cay) if isinstance(n, ast.FunctionDef)}
	for ham in ("gui_mau", "gui_tin"):
		dung("zalo.%s đọc cờ kiểm thật" % ham, "vagabond_kiem_that" in than.get(ham, ""))
	# Mọi lối gửi của kịch bản đi qua đúng một cửa _gui_mau -> zalo.gui_mau.
	nguon = io.open(os.path.join(goc, "zalo_kich_ban.py"), encoding="utf-8").read()
	cay2 = ast.parse(nguon)
	goi = [ast.dump(n.func) for n in ast.walk(cay2) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
		and n.func.attr in ("gui_mau", "gui_tin", "post")]
	la("chỉ một lời gọi zalo.gui_mau, không gọi requests trực tiếp", len(goi), 1)
