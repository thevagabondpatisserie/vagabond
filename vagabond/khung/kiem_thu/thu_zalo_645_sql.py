# -*- coding: utf-8 -*-
"""v645 Codex PR 548 vòng b4b18d58b5: chạy câu SQL THẬT của zalo_kich_ban trên sqlite.

Ba finding Codex đều nằm trong câu SQL (mốc quét, điều kiện khách mới, cửa sổ
đo hiệu quả). Bản giả frappe.db.sql cũ chỉ trả dữ liệu dựng sẵn nên không thấy
câu sai. Ở đây câu SQL do mã thật soạn được dịch tối thiểu sang sqlite
(tham số %(x)s, bộ giá trị cho "in", concat, date_add) rồi chạy trên bảng
dựng đúng các cột câu đó đọc.

Ca chốt:
  - bill quầy lưu nháp trước lúc bật (hoặc quá 48 giờ) rồi mới ghi sổ vẫn được
    cảm ơn, mốc là lúc ghi sổ (dòng tích điểm), không phải lúc tạo hoá đơn;
  - khách mua lại gõ số người giới thiệu thì không sinh quà giới thiệu;
  - báo cáo "Hiệu quả 30 ngày" chỉ tính dòng đã đủ 30 ngày quan sát.
"""

import datetime as dt
import re
import sqlite3
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import zalo_kich_ban as zk  # noqa: E402
from vagabond.khung.kiem_thu.thu_zalo_kich_ban_621 import D, _gd, _gop  # noqa: E402

fr = zk.frappe
LUC = dt.datetime(2026, 11, 9, 10, 0)


def _iso(v):
	if isinstance(v, dt.datetime):
		return v.strftime("%Y-%m-%d %H:%M:%S")
	if isinstance(v, dt.date):
		return v.strftime("%Y-%m-%d")
	return v


class Kho:
	"""sqlite trong bộ nhớ với đúng các bảng, cột câu SQL của zk đọc."""

	BANG = {
		"tabSales Invoice": ["name", "customer", "docstatus", "custom_pancake_id", "custom_pancake_display_id",
			"grand_total", "creation", "is_return", "vgb_huy", "custom_nguon"],
		"tabVagabond Tin Zalo Khach": ["name", "khoa", "kich_ban", "khach", "trang_thai", "loi", "creation", "luc_gui"],
		"tabVagabond So Diem": ["name", "hoa_don", "khach", "loai", "diem", "creation"],
		"tabVagabond Voucher": ["name", "gui_cho", "creation", "trang_thai", "ngay_dung", "tien_giam", "hoa_don"],
	}

	def __init__(self):
		self.db = sqlite3.connect(":memory:")
		self.db.create_function("concat", -1, lambda *a: "".join(str(x) for x in a))
		for bang, cot in self.BANG.items():
			self.db.execute("create table `%s` (%s)" % (bang, ", ".join("`%s`" % c for c in cot)))
		self.cau = []

	def them(self, bang, **v):
		cot = self.BANG[bang]
		self.db.execute("insert into `%s` (%s) values (%s)" % (bang, ", ".join("`%s`" % c for c in cot), ", ".join("?" * len(cot))),
			[_iso(v.get(c)) for c in cot])

	def sql(self, q, ts=None, as_dict=False, **k):
		self.cau.append(q)
		q = re.sub(r"date_add\(([^,]+), interval (\d+) day\)", r"datetime(\1, '+\2 days')", q)
		gia = []

		def thay(m, nguon):
			v = nguon(m)
			if isinstance(v, (tuple, list)):
				gia.extend(_iso(x) for x in v)
				return "(" + ", ".join("?" * len(v)) + ")"
			gia.append(_iso(v))
			return "?"
		if isinstance(ts, dict):
			q = re.sub(r"%\((\w+)\)s", lambda m: thay(m, lambda mm: ts[mm.group(1)]), q)
		elif ts is not None:
			it = iter(ts)
			q = re.sub(r"%s", lambda m: thay(m, lambda mm: next(it)), q)
		q = q.replace("%%", "%")
		cur = self.db.execute(q, gia)
		rows = cur.fetchall()
		if as_dict:
			ten = [c[0] for c in cur.description]
			return [D(zip(ten, r)) for r in rows]
		return [list(r) for r in rows]


def _sau_mua(kho, bat_luc):
	chen = []

	class Doc(D):
		def insert(self, **k):
			chen.append(dict(self))
			kho.them("tabVagabond Tin Zalo Khach", name=self["khoa"], khoa=self["khoa"], kich_ban=self["kich_ban"],
				khach=self["khach"], trang_thai=self.get("trang_thai"), creation=LUC)
			return self
	with um.patch.object(zk, "_cau_hinh", lambda ma: {"ma": ma, "bat": 1, "bat_luc": bat_luc}), \
			um.patch.object(zk, "_bay_gio", lambda: LUC), um.patch.object(zk, "get_datetime", _gd), \
			um.patch.object(zk, "_la_khach_gop", _gop), um.patch.object(zk, "_la_qua_tang", lambda n: False), \
			um.patch.object(zk, "_diem_cua_don", lambda hd: (10, True)), \
			um.patch.object(fr.db, "sql", kho.sql), \
			um.patch.object(fr.db, "exists", lambda dt_, f=None, *a, **k: bool(kho.sql(
				"select 1 from `tabVagabond Tin Zalo Khach` where khoa = %s", ((f or {}).get("khoa"),)))), \
			um.patch.object(fr, "get_doc", lambda d, *a, **k: Doc(d)):
		n = zk.quet_sau_mua()
	return n, chen


@ca("v645 Codex 548 b4b18d5: bill quầy lưu nháp trước lúc bật hay quá 48 giờ rồi mới ghi sổ vẫn được cảm ơn (mốc là lúc ghi sổ); đơn cũ đã ghi sổ từ trước thì không")
def _sau_mua_ghi_so_muon():
	# Chuỗi thật: ban_hang.pos_chot() lưu bill nháp; ghi sổ sau đó, hook cộng
	# điểm ghi dòng sổ điểm đúng lúc ghi sổ. Kịch bản bật lúc 08:00.
	bat = LUC.replace(hour=8)
	kho = Kho()
	# Nháp tạo trước lúc bật, ghi sổ lúc 09:00 (sau lúc bật).
	kho.them("tabSales Invoice", name="HDB-A", customer="K1", docstatus=1, creation=bat - dt.timedelta(hours=3), grand_total=200000)
	kho.them("tabVagabond So Diem", name="D1", hoa_don="HDB-A", khach="K1", loai="Tich tu hoa don", diem=10, creation=LUC.replace(hour=9))
	# Nháp tạo 3 ngày trước (quá 48 giờ), ghi sổ sáng nay.
	kho.them("tabSales Invoice", name="HDB-B", customer="K2", docstatus=1, creation=LUC - dt.timedelta(days=3), grand_total=300000)
	kho.them("tabVagabond So Diem", name="D2", hoa_don="HDB-B", khach="K2", loai="Tich tu hoa don", diem=15, creation=LUC.replace(hour=9, minute=30))
	# Đơn ghi sổ từ hôm qua, trước lúc bật: không gửi bù.
	kho.them("tabSales Invoice", name="HDB-C", customer="K3", docstatus=1, creation=LUC - dt.timedelta(days=1), grand_total=100000)
	kho.them("tabVagabond So Diem", name="D3", hoa_don="HDB-C", khach="K3", loai="Tich tu hoa don", diem=5, creation=LUC - dt.timedelta(days=1))
	# Bill quầy tạo và ghi sổ sau lúc bật (đường thường).
	kho.them("tabSales Invoice", name="HDB-D", customer="K4", docstatus=1, creation=LUC.replace(hour=9, minute=45), grand_total=90000)
	# Đơn giao Pancake nháp (đã nhận) sau lúc bật.
	kho.them("tabSales Invoice", name="HDB-E", customer="K5", docstatus=0, custom_pancake_id="P5", creation=LUC.replace(hour=9, minute=50))
	# Đơn giao Pancake khách nhận TRƯỚC lúc bật (nháp dựng 07:00), cuối ngày mới
	# ghi sổ: không gửi bù, dù dòng tích điểm sinh sau lúc bật.
	kho.them("tabSales Invoice", name="HDB-G", customer="K7", docstatus=1, custom_pancake_id="P7", creation=bat - dt.timedelta(hours=1))
	kho.them("tabVagabond So Diem", name="D7", hoa_don="HDB-G", khach="K7", loai="Tich tu hoa don", diem=8, creation=LUC.replace(hour=9, minute=40))
	# Nháp quầy chưa ghi sổ: chưa phải đã nhận.
	kho.them("tabSales Invoice", name="HDB-F", customer="K6", docstatus=0, creation=LUC.replace(hour=9, minute=55))
	n, chen = _sau_mua(kho, bat)
	la("đúng các đơn", sorted(x["hoa_don"] for x in chen), ["HDB-A", "HDB-B", "HDB-D", "HDB-E"])
	la("số dòng", n, 4)
	n2, chen2 = _sau_mua(kho, bat)
	la("quét lại không thêm", (n2, chen2), (0, []))


def _gioi_thieu(kho, so_don):
	from vagabond import nhap_khach

	chen = []

	class Doc(D):
		def insert(self, **k):
			chen.append(dict(self))
			kho.them("tabVagabond Tin Zalo Khach", name=self["khoa"], khoa=self["khoa"], kich_ban=self["kich_ban"],
				khach=self["khach"], trang_thai=self.get("trang_thai"), creation=LUC)
			return self
	sdt = {hd: "0901000009" for hd in so_don}
	with um.patch.object(zk, "_cau_hinh", lambda ma: {"ma": ma, "bat": 1, "bat_luc": LUC - dt.timedelta(days=5)}), \
			um.patch.object(zk, "_bay_gio", lambda: LUC), um.patch.object(zk, "get_datetime", _gd), \
			um.patch.object(zk, "_la_khach_gop", _gop), \
			um.patch.object(zk, "_so_dien_thoai_gioi_thieu", lambda hd: sdt.get(hd, "")), \
			um.patch.object(nhap_khach, "tim_theo_sdt", lambda s: "K9" if s == "0901000009" else ""), \
			um.patch.object(fr.db, "sql", kho.sql), \
			um.patch.object(fr.db, "count", lambda dt_, f=None, *a, **k: 0, create=True), \
			um.patch.object(fr.db, "exists", lambda dt_, f=None, *a, **k: bool(kho.sql(
				"select 1 from `tabVagabond Tin Zalo Khach` where khoa = %s", ((f or {}).get("khoa"),)))), \
			um.patch.object(fr, "get_doc", lambda d, *a, **k: Doc(d)):
		n = zk.quet_gioi_thieu()
	return n, chen


@ca("v645 Codex 548 b4b18d5: quà giới thiệu chỉ khi người mua là khách MỚI (đơn đã nhận đầu tiên); khách mua lại gõ số người giới thiệu thì không sinh quà")
def _gioi_thieu_khach_moi():
	kho = Kho()
	# K1 khách mới: đơn web đầu tiên, gõ số của K9.
	kho.them("tabSales Invoice", name="HD-MOI", customer="K1", docstatus=0, custom_pancake_id="P1", creation=LUC - dt.timedelta(hours=2))
	# K2 đã mua hai lần trước, đơn web thứ ba vẫn gõ số K9.
	kho.them("tabSales Invoice", name="HD-CU1", customer="K2", docstatus=1, creation=LUC - dt.timedelta(days=60))
	kho.them("tabSales Invoice", name="HD-CU2", customer="K2", docstatus=1, creation=LUC - dt.timedelta(days=20))
	kho.them("tabSales Invoice", name="HD-LAI", customer="K2", docstatus=0, custom_pancake_id="P2", creation=LUC - dt.timedelta(hours=1))
	# Đơn trước của K3 đã huỷ: K3 vẫn là khách mới.
	kho.them("tabSales Invoice", name="HD-HUY", customer="K3", docstatus=1, vgb_huy=1, creation=LUC - dt.timedelta(days=9))
	kho.them("tabSales Invoice", name="HD-K3", customer="K3", docstatus=0, custom_pancake_id="P3", creation=LUC - dt.timedelta(minutes=30))
	# K4 mới có MỘT đơn trước (đơn thứ hai): đã là khách mua lại.
	kho.them("tabSales Invoice", name="HD-K4A", customer="K4", docstatus=1, creation=LUC - dt.timedelta(days=40))
	kho.them("tabSales Invoice", name="HD-K4B", customer="K4", docstatus=0, custom_pancake_id="P4", creation=LUC - dt.timedelta(minutes=20))
	n, chen = _gioi_thieu(kho, ["HD-MOI", "HD-LAI", "HD-K3", "HD-K4B"])
	la("chỉ đơn của khách mới sinh quà", sorted(x["hoa_don"] for x in chen), ["HD-K3", "HD-MOI"])
	dung("người nhận là người giới thiệu", all(x["khach"] == "K9" for x in chen))
	la("số dòng", n, 2)


@ca("v645 Codex 548 b4b18d5: báo cáo Hiệu quả 30 ngày chỉ tính dòng tin đã đủ 30 ngày quan sát; khách nhận tin 8 ngày trước chưa vào mẫu số")
def _bao_cao_du_30_ngay():
	kho = Kho()
	gui = lambda ma, kh, truoc: kho.them("tabVagabond Tin Zalo Khach", name=ma, khoa=ma, kich_ban="quay_lai", khach=kh,
		trang_thai=zk.TT_GUI, creation=LUC - dt.timedelta(days=truoc), luc_gui=LUC - dt.timedelta(days=truoc))
	# A nhận tin 33 ngày trước, mua lại ngày thứ 10 sau tin: đủ 30 ngày, có mua.
	gui("T-A", "KA", 33)
	kho.them("tabSales Invoice", name="HA", customer="KA", docstatus=1, creation=LUC - dt.timedelta(days=23))
	# B nhận tin 35 ngày trước, không mua: đủ 30 ngày, không mua.
	gui("T-B", "KB", 35)
	# C nhận tin 8 ngày trước, chưa mua: CHƯA đủ 30 ngày, không được tính.
	gui("T-C", "KC", 8)
	# Đối chứng D, 31 ngày trước, có mua ngày thứ 5.
	kho.them("tabVagabond Tin Zalo Khach", name="T-D", khoa="T-D", kich_ban="quay_lai", khach="KD", trang_thai=zk.TT_BO,
		loi=zk.LY_DO_DOI_CHUNG + ": không gửi để so sánh.", creation=LUC - dt.timedelta(days=31))
	kho.them("tabSales Invoice", name="HD", customer="KD", docstatus=1, creation=LUC - dt.timedelta(days=26))
	with um.patch.object(fr.db, "sql", kho.sql), um.patch.object(zk, "KB_DO_HIEU_QUA", ("quay_lai", "don_thu_hai")):
		so = zk._so_bao_cao_tuan(LUC)
	la("nhận tin: 1 mua trên 2 đã đủ 30 ngày", so["hq"]["nhan"], [1, 2])
	la("đối chứng", so["hq"]["dc"], [1, 1])
	tin = zk.soan_bao_cao_tuan(so, LUC.date())
	dung("câu báo cáo nói rõ nhóm đã đủ 30 ngày", "đã đủ 30 ngày" in tin)
