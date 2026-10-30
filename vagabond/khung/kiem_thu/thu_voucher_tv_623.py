# -*- coding: utf-8 -*-
"""v623: voucher dành cho thành viên (anh Việt 30/10/2026).

Anh chốt: cài ngay trong phiếu Chương trình khuyến mãi. Ô Đối tượng có sẵn
(hạng, nhóm khách, khách chỉ định) quyết định ai nhận; bật "Phát vào Ví quà
thành viên", chọn Dịp phát (Mọi lúc / Tháng sinh nhật) và Số lần nhận (Một lần
/ Mỗi năm một lần). Khách đủ điều kiện mở trang thành viên là mã TỰ HIỆN trong
Ví quà, không phải bấm, thu ngân áp như mã quà chào mừng.

Mỗi ca chốt một đường lỗi có thật:
  - hai thẻ mở cùng lúc hay mở lại trang ra hai mã trong một kỳ;
  - khách ngoài hạng, ngoài tháng sinh nhật, hay số nhân viên vẫn nhận mã;
  - mã hạn quá ngày cuối tháng sinh nhật, quá ngày kết thúc chương trình;
  - tin Zalo cùng chương trình phát thêm mã thứ hai, hay gửi lỗi rồi HUỶ mất
    mã khách đang giữ trong ví;
  - thu ngân áp mã ví của người này cho hoá đơn người khác;
  - ô cấu hình "áp cho" mà máy không áp (doctype, form app, lưu).
Phần chạm hệ chạy trên lớp Frappe giả, vá đúng lời gọi hàm thật dùng.
"""

import datetime as dt
import json
import re
import sys
import types
import unittest.mock as um
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_rl = types.ModuleType("frappe.rate_limiter")
_rl.rate_limit = lambda *a, **k: (lambda f: f)
sys.modules.setdefault("frappe.rate_limiter", _rl)

from vagabond import thanh_vien as tv  # noqa: E402
from vagabond import khuyen_mai as km  # noqa: E402
from vagabond import zalo_kich_ban as zk  # noqa: E402

GOC = Path(__file__).resolve().parents[2]
D8 = dt.date
HN = D8(2026, 11, 12)


class D(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v


def _ct(name, **v):
	c = D(name=name, ten=v.pop("ten", "Voucher " + name), cach_ma="Ma dung mot lan", bat=1, kieu_giam="So tien",
		gia_tri=50000, hd_toi_thieu=0, doi_tuong="Moi khach", vi_phat=1, vi_dip="Moi luc", vi_so_lan="Mot lan",
		vi_han_ngay=30)
	c.update(v)
	return c


# ------------------------------------------------------------------ thuần

@ca("v623 dịp phát: Tháng sinh nhật chỉ trong đúng tháng sinh của khách, mã tới hết tháng; chưa khai ngày sinh thì chưa nhận")
def _ky_vi():
	sn = _ct("SN", vi_dip="Thang sinh nhat")
	la("đúng tháng", tv.ky_vi(sn, D8(1990, 11, 30), HN), (True, "", D8(2026, 11, 30)))
	la("ngày sinh dạng chuỗi", tv.ky_vi(sn, "1990-11-03", HN)[0], True)
	la("khác tháng", tv.ky_vi(sn, D8(1990, 12, 1), HN), (False, "chua_toi_thang_sinh_nhat", None))
	la("chưa khai", tv.ky_vi(sn, None, HN), (False, "chua_co_sinh_nhat", None))
	la("tháng 2 năm nhuận", tv.ky_vi(sn, D8(1992, 2, 29), D8(2028, 2, 10))[2], D8(2028, 2, 29))
	la("tháng 12", tv.ky_vi(sn, D8(1992, 12, 5), D8(2026, 12, 31))[2], D8(2026, 12, 31))
	la("Mọi lúc: không cần ngày sinh", tv.ky_vi(_ct("ML"), None, HN), (True, "", None))
	la("ô trống là Mọi lúc", tv.ky_vi(_ct("ML", vi_dip=""), None, HN), (True, "", None))


@ca("v623 số lần nhận: Một lần tính mọi mã đã nhận; Mỗi năm một lần chỉ tính mã từ 01/01 năm nay")
def _so_lan():
	la("Một lần: không mốc", tv.moc_so_lan(_ct("A"), HN), None)
	la("Mỗi năm: 01/01", tv.moc_so_lan(_ct("A", vi_so_lan="Moi nam mot lan"), HN), D8(2026, 1, 1))
	nam_ngoai = [D(creation=dt.datetime(2025, 11, 3, 9, 0))]
	nam_nay = [D(creation=dt.datetime(2026, 1, 1, 0, 1))]
	la("Một lần: mã năm ngoái vẫn tính", tv.da_nhan_trong_ky(nam_ngoai, None), True)
	la("Mỗi năm: mã năm ngoái không tính", tv.da_nhan_trong_ky(nam_ngoai, D8(2026, 1, 1)), False)
	la("Mỗi năm: mã năm nay tính", tv.da_nhan_trong_ky(nam_nay, D8(2026, 1, 1)), True)
	la("không đọc được ngày tạo: coi như đã nhận (không phát thừa)", tv.da_nhan_trong_ky([D(creation=None)], D8(2026, 1, 1)), True)
	la("chưa có mã", tv.da_nhan_trong_ky([], None), False)


@ca("v623 hạn mã ví: theo số ngày đã đặt, không quá ngày kết thúc chương trình hay ngày cuối tháng sinh nhật")
def _han():
	la("Mọi lúc 30 ngày", tv.han_ma_vi(_ct("A"), HN, None), D8(2026, 12, 12))
	la("ô số ngày gõ bậy dùng 30", tv.han_ma_vi(_ct("A", vi_han_ngay="ba muoi"), HN, None), D8(2026, 12, 12))
	la("ô số ngày 7", tv.han_ma_vi(_ct("A", vi_han_ngay="7"), HN, None), D8(2026, 11, 19))
	la("kẹp ngày kết thúc", tv.han_ma_vi(_ct("A", den_ngay="2026-11-20"), HN, None), D8(2026, 11, 20))
	la("tháng sinh nhật: hết tháng", tv.han_ma_vi(_ct("A", vi_dip="Thang sinh nhat"), HN, D8(2026, 11, 30)), D8(2026, 11, 30))
	la("ngày cuối tháng: dùng trong ngày", tv.han_ma_vi(_ct("A"), D8(2026, 11, 30), D8(2026, 11, 30)), D8(2026, 11, 30))
	la("chưa tới ngày bắt đầu", tv.han_ma_vi(_ct("A", tu_ngay="2026-12-01"), HN, None), None)
	la("đã hết chương trình", tv.han_ma_vi(_ct("A", den_ngay="2026-11-01"), HN, None), None)
	la("đang tắt", tv.han_ma_vi(_ct("A", bat=0), HN, None), None)


@ca("v623 mã ví chỉ dùng cho chính người nhận, như quà chào mừng; mã lô thường không gắn người nhận thì không ràng buộc")
def _rang_buoc():
	la("quà chào mừng", km.ma_rang_buoc({"name": km.CTKM_QUA}), 1)
	la("chương trình Ví quà", km.ma_rang_buoc({"name": "KMSN01", "vi_phat": 1}), 1)
	la("chương trình Ví quà, ô kiểu chuỗi", km.ma_rang_buoc({"name": "KMSN01", "vi_phat": "1"}), 1)
	la("chương trình thường", km.ma_rang_buoc({"name": "KMLO01", "vi_phat": 0}), 0)
	tt = {"danh_cho": "KL0412", "sdt": "0909123412", "rang_buoc": km.ma_rang_buoc({"name": "KMSN01", "vi_phat": 1})}
	la("hoá đơn khách khác: từ chối", bool(km.kiem_nguoi_nhan(tt, "KL0001", "")[1]), True)
	la("hoá đơn chưa chọn khách, số khác: từ chối", bool(km.kiem_nguoi_nhan(tt, "", "0911222333")[1]), True)
	la("hoá đơn chưa chọn khách: gắn đúng người nhận", km.kiem_nguoi_nhan(tt, "", ""), ("KL0412", ""))


# ------------------------------------------------------------------ chạm hệ

class Moi:
	"""Lớp giả cho cap_vi_tv / vi_du_dieu_kien: chương trình, voucher, khách, khoá."""

	def __init__(self, ds_ct=None, vc=None, hang="VOYAGER", sinh_nhat=D8(1990, 11, 14), nhan_vien=False, chi_dinh=()):
		self.ct = ds_ct if ds_ct is not None else [_ct("KMML01")]
		self.vc = vc if vc is not None else {}
		self.kh = D(name="KL0412", customer_name="Nguyễn Lan Anh", vgb_hang=hang, vgb_sinh_nhat=sinh_nhat,
			customer_group="Khách lẻ")
		self.hs = {"KL0412": D(ten_goi="Lan Anh", dy_zalo="Đồng ý")}
		self.nv, self.chi_dinh = nhan_vien, set(chi_dinh)
		self.vet, self.ma = [], iter("VT%04d" % i for i in range(1, 99))

	def get_value(self, dt_, ten=None, cot=None, as_dict=False, **k):
		if dt_ == "Customer":
			return self.kh.get(cot)
		if dt_ == tv.DT_HO_SO:
			h = self.hs.get(ten) or {}
			return D({c: h.get(c) for c in cot}) if isinstance(cot, list) else h.get(cot)
		return None

	def exists(self, dt_, f=None, *a, **k):
		if dt_ == "Vagabond CTKM Khach":
			return 1 if f["parent"] in self.chi_dinh else None
		return None

	def get_all(self, dt_, filters=None, fields=None, order_by=None, limit_page_length=None, **k):
		f = filters or {}
		if dt_ == "Vagabond CTKM":
			return [c for c in self.ct if all(str(c.get(a)) == str(b) for a, b in f.items())]
		if dt_ == "Vagabond Voucher":
			ra = [D(v, ma=m) for m, v in self.vc.items() if all(v.get(a) == b for a, b in f.items())]
			ra.sort(key=lambda v: v.get("creation") or dt.datetime.min, reverse=True)
			return ra[:limit_page_length] if limit_page_length else ra
		return []

	def sql(self, q, *a, **k):
		self.vet.append(("sql", q.strip()[:40]))
		return []

	def get_doc(self, d, *a, **k):
		moi = self

		class Doc(D):
			def insert(self, **kk):
				moi.vet.append(("insert", self.get("doctype")))
				moi.vc[self["ma"]] = D(self, creation=dt.datetime(HN.year, HN.month, HN.day, 9, 30))
				return self
		return Doc(d)

	def vas(self):
		fr = tv.frappe
		from vagabond import crm

		def ho_so(khach, tao=False):
			if tao:
				self.hs.setdefault(khach, D(dy_zalo="Chưa hỏi"))
			return self.hs.get(khach)
		return [um.patch.object(tv, "_so_phien", lambda: "84909123412"), um.patch.object(tv, "_hom_nay", lambda: HN),
			um.patch.object(tv, "_dn", lambda: types.SimpleNamespace(_sdt_noi_dia=lambda s: "0" + s[-9:])),
			um.patch.object(tv, "_khach_cua_so", lambda so: (self.kh, "")),
			um.patch.object(tv, "_khong_cache", lambda: None),
			um.patch.object(km, "_la_sdt_nhan_vien", lambda s: self.nv),
			um.patch.object(km, "_sinh_ma_moi", lambda n: [next(self.ma)]),
			um.patch.object(crm, "_ho_so", ho_so),
			um.patch.object(fr.db, "get_value", self.get_value), um.patch.object(fr.db, "sql", self.sql),
			um.patch.object(fr.db, "exists", self.exists), um.patch.object(fr.db, "commit", lambda: None),
			um.patch.object(fr, "get_all", self.get_all), um.patch.object(fr, "get_doc", self.get_doc)]

	def chay(self, ham, *a, **k):
		vas = self.vas()
		for v in vas:
			v.start()
		try:
			return ham(*a, **k)
		finally:
			for v in reversed(vas):
				v.stop()


@ca("v623 mở trang thành viên: cấp MỘT mã gắn đúng người nhận vào Ví quà; mở lại không ra mã thứ hai; khoá hồ sơ trước khi cấp")
def _cap_vi():
	m = Moi()
	la("hồ sơ báo còn một quà chờ", m.chay(tv.vi_du_dieu_kien, m.kh, "0909123412", HN)[0][1], D8(2026, 12, 12))
	kq = m.chay(tv.cap_vi_tv)
	la("cấp mã", (kq["ok"], [x["ma"] for x in kq["moi"]], kq["moi"][0]["han"], kq["moi"][0]["uu_dai"]),
		(1, ["VT0001"], "12/12/2026", "Giảm 50.000đ"))
	v = m.vc["VT0001"]
	la("mã gắn người nhận", (v["danh_cho"], v["ctkm"], v["trang_thai"], v["han_dung"], v["sdt"], v["gui_cho"]),
		("KL0412", "KMML01", "Chua dung", D8(2026, 12, 12), "0909123412", "Ví quà thành viên"))
	dung("khoá dòng hồ sơ trước khi cấp", m.vet.index(("sql", "select name from `tabVagabond Ho So CRM`"))
		< m.vet.index(("insert", "Vagabond Voucher")))
	la("mở lại: không mã mới", (m.chay(tv.cap_vi_tv)["moi"], len(m.vc)), ([], 1))
	la("hồ sơ hết quà chờ", m.chay(tv.vi_du_dieu_kien, m.kh, "0909123412", HN), [])


@ca("v623 một kỳ một mã: Một lần tính cả mã đã dùng, đã huỷ, mã gửi qua Zalo; Mỗi năm một lần thì sang năm nhận lại")
def _mot_ky():
	for tt in ("Da dung", "Da huy", "Chua dung"):
		m = Moi(vc={"ZL0001": D(ctkm="KMML01", danh_cho="KL0412", trang_thai=tt, han_dung=D8(2026, 11, 1),
			creation=dt.datetime(2025, 3, 1), gui_cho="Zalo")})
		la("Một lần, mã cũ %s: không cấp" % tt, (m.chay(tv.cap_vi_tv)["moi"], len(m.vc)), ([], 1))
	nam = [_ct("KMSN01", vi_dip="Thang sinh nhat", vi_so_lan="Moi nam mot lan")]
	m = Moi(ds_ct=nam, vc={"SN2025": D(ctkm="KMSN01", danh_cho="KL0412", trang_thai="Da dung",
		creation=dt.datetime(2025, 11, 2))})
	kq = m.chay(tv.cap_vi_tv)
	la("Mỗi năm: năm ngoái đã dùng, năm nay nhận mã mới tới hết tháng sinh nhật",
		([x["han"] for x in kq["moi"]], len(m.vc)), (["30/11/2026"], 2))
	la("Mỗi năm: nhận rồi thì thôi", m.chay(tv.cap_vi_tv)["moi"], [])
	m = Moi(vc={"KHAC01": D(ctkm="KMML01", danh_cho="KL9999", trang_thai="Chua dung", creation=dt.datetime(2026, 11, 1))})
	la("mã của khách khác không tính", [x["ma"] for x in m.chay(tv.cap_vi_tv)["moi"]], ["VT0001"])


@ca("v623 ai nhận: đúng ô Đối tượng của chương trình (hạng, nhóm, khách chỉ định); số nhân viên không nhận; ngoài tháng sinh nhật không nhận")
def _ai_nhan():
	hang = [_ct("KMH01", doi_tuong="Theo hang khach", hang_khach="VOYAGER\nVAGABONDER")]
	la("đúng hạng", len(Moi(ds_ct=hang).chay(tv.cap_vi_tv)["moi"]), 1)
	la("hạng chữ thường vẫn khớp", len(Moi(ds_ct=hang, hang="voyager").chay(tv.cap_vi_tv)["moi"]), 1)
	m = Moi(ds_ct=hang, hang="MEMBER")
	la("ngoài hạng", (m.chay(tv.cap_vi_tv)["moi"], len(m.vc)), ([], 0))
	nhom = [_ct("KMN01", doi_tuong="Theo nhom khach", nhom_khach="Khách sỉ")]
	la("ngoài nhóm", Moi(ds_ct=nhom).chay(tv.cap_vi_tv)["moi"], [])
	cd = [_ct("KMCD1", doi_tuong="Khach chi dinh")]
	la("khách chỉ định: có tên", len(Moi(ds_ct=cd, chi_dinh=["KMCD1"]).chay(tv.cap_vi_tv)["moi"]), 1)
	la("khách chỉ định: không tên", Moi(ds_ct=cd).chay(tv.cap_vi_tv)["moi"], [])
	la("số nhân viên, chương trình khách", Moi(nhan_vien=True).chay(tv.cap_vi_tv)["moi"], [])
	nv = [_ct("KMNV1", doi_tuong="Nhan vien")]
	la("số nhân viên, chương trình Nhân viên", len(Moi(ds_ct=nv, nhan_vien=True).chay(tv.cap_vi_tv)["moi"]), 1)
	la("khách thường, chương trình Nhân viên", Moi(ds_ct=nv).chay(tv.cap_vi_tv)["moi"], [])
	sn = [_ct("KMSN01", vi_dip="Thang sinh nhat")]
	la("tháng sinh nhật: đúng tháng", len(Moi(ds_ct=sn).chay(tv.cap_vi_tv)["moi"]), 1)
	la("tháng sinh nhật: khác tháng", Moi(ds_ct=sn, sinh_nhat=D8(1990, 4, 2)).chay(tv.cap_vi_tv)["moi"], [])
	la("tháng sinh nhật: chưa khai", Moi(ds_ct=sn, sinh_nhat=None).chay(tv.cap_vi_tv)["moi"], [])
	la("chương trình chưa bắt đầu", Moi(ds_ct=[_ct("KMT1", tu_ngay="2026-12-01")]).chay(tv.cap_vi_tv)["moi"], [])
	la("quà chào mừng không đi đường này", Moi(ds_ct=[_ct(km.CTKM_QUA)]).chay(tv.cap_vi_tv)["moi"], [])
	la("chương trình không bật Ví quà", Moi(ds_ct=[_ct("KMLO1", vi_phat=0)]).chay(tv.cap_vi_tv)["moi"], [])
	hai = [_ct("KMA"), _ct("KMB", doi_tuong="Theo hang khach", hang_khach="VOYAGER")]
	la("hai chương trình: hai mã", [x["ma"] for x in Moi(ds_ct=hai).chay(tv.cap_vi_tv)["moi"]], ["VT0001", "VT0002"])


@ca("v623 cửa cap_vi_tv: chưa đăng nhập thì không cấp; số có nhiều hồ sơ thì không đoán; site chưa migrate thì trang vẫn lên")
def _cua():
	m = Moi()
	vas = m.vas()
	for v in vas:
		v.start()
	try:
		with um.patch.object(tv, "_so_phien", lambda: None):
			la("chưa đăng nhập", tv.cap_vi_tv(), {"ok": 0, "ly_do": "chua_dang_nhap"})
		with um.patch.object(tv, "_khach_cua_so", lambda so: (None, "can_doi_chieu")):
			la("nhiều hồ sơ cùng số", tv.cap_vi_tv(), {"ok": 1, "moi": []})

		def loi(*a, **k):
			raise Exception("Unknown column 'vi_phat'")
		with um.patch.object(tv.frappe, "get_all", loi):
			la("site chưa có ô vi_phat", tv._ds_ctkm_vi(), [])
	finally:
		for v in reversed(vas):
			v.stop()
	la("không cấp mã nào", len(m.vc), 0)


# ------------------------------------------------------------------ tin Zalo cùng chương trình

def _gui(km_ct, trong_ky, loi_zalo=0, sinh_nhat=None, nhan_vien=False):
	"""Chạy _gui_mot với chương trình km_ct; trả (vết, kết quả). Vết `buoc`
	ghi thứ tự khoá hồ sơ, đọc mã trong kỳ, phát mã, ghi sổ, gửi Zalo."""
	vet = D(phat=[], huy=[], xong=[], gui=[], buoc=[])
	c = D(ma="chao_mung", ctkm=km_ct["name"], ma_mau="659378", han_ngay=30, mau_tham_so="")
	row = D(name="TIN-1", khach="KL0412", khoa="chao_mung:KL0412")

	def phat(c_, kh, khach, ma_kb, han=None):
		vet.phat.append((khach, han))
		vet.buoc.append("phat")
		return "ZMOI01", han or D8(2026, 12, 12), ""

	def trong(k, kh, hn):
		vet.buoc.append("doc_ky")
		return trong_ky

	def gui(cfg, sdt, mau, data, khoa):
		vet.buoc.append("gui")
		vet.gui.append(data)
		return {"error": loi_zalo}
	vas = [um.patch.object(zk, "kich_ban", lambda m: {"km": 1, "ten": "Chào mừng"}),
		um.patch.object(zk, "_ho_so", lambda k: {"sdt84": "84909123412", "dong_y": 1, "ten": "Lan Anh", "sinh_nhat": sinh_nhat}),
		um.patch.object(zk, "_doc_ctkm", lambda t: km_ct),
		um.patch.object(zk, "_hop_doi_tuong", lambda *a: (True, "")),
		um.patch.object(km, "_hop_doi_tuong", lambda *a: (True, "")),
		um.patch.object(km, "_la_sdt_nhan_vien", lambda s: nhan_vien),
		# create=True: bản trước Codex PR #520 chưa có khoa_ho_so; ca vẫn chạy để tái hiện.
		um.patch.object(tv, "khoa_ho_so", lambda k: vet.buoc.append("khoa:" + k), create=True),
		um.patch.object(tv, "ma_vi_trong_ky", trong),
		um.patch.object(zk, "_bay_gio", lambda: dt.datetime(2026, 11, 12, 10, 0)),
		um.patch.object(zk, "_phat_voucher", phat),
		um.patch.object(zk, "du_lieu_mau", lambda gt, ts: (dict(gt), [])),
		um.patch.object(zk, "_cfg", lambda: {}),
		um.patch.object(zk, "_gui_mau", gui),
		um.patch.object(zk, "y_nghia_loi", lambda j: (j["error"], "" if not j["error"] else "Zalo từ chối")),
		um.patch.object(zk, "_huy_voucher", lambda ma, ly: vet.huy.append(ma)),
		um.patch.object(zk, "_xong", lambda r, tt, loi="", **v: vet.xong.append((tt, loi, v.get("voucher")))),
		um.patch.object(zk.frappe, "get_doc", lambda d: D(d, insert=lambda **k: None)),
		um.patch.object(zk.frappe.db, "commit", lambda: vet.buoc.append("ghi"))]
	for v in vas:
		v.start()
	try:
		kq = zk._gui_mot(c, row)
	finally:
		for v in reversed(vas):
			v.stop()
	return vet, kq


@ca("v623 tin Zalo cùng chương trình Ví quà: gửi lại đúng mã trong ví, không phát mã thứ hai; Zalo lỗi thì KHÔNG huỷ mã khách đang giữ")
def _zalo():
	ct = _ct("KMML01")
	con = [D(ma="VT0001", trang_thai="Chua dung", han_dung=D8(2026, 12, 1), creation=dt.datetime(2026, 11, 10))]
	vet, kq = _gui(ct, con)
	la("gửi mã trong ví", (kq, vet.phat, vet.gui[0]["ma_voucher"], vet.gui[0]["han_dung"], vet.xong[-1][2]),
		(0, [], "VT0001", "01/12/2026", "VT0001"))
	vet, kq = _gui(ct, con, loi_zalo=-201)
	la("Zalo lỗi: không huỷ mã ví", (vet.phat, vet.huy), ([], [None]))
	het = [D(ma="VT0001", trang_thai="Da dung", han_dung=D8(2026, 12, 1), creation=dt.datetime(2026, 11, 10))]
	vet, kq = _gui(ct, het)
	la("mã kỳ này đã dùng: bỏ qua, không phát, không gửi", (vet.phat, vet.gui, vet.xong[-1][0]), ([], [], zk.TT_BO))
	vet, kq = _gui(ct, [])
	la("chưa có mã: phát mã mới theo hạn Ví quà", (kq, vet.phat, vet.gui[0]["ma_voucher"]), (0, [("KL0412", D8(2026, 12, 12))], "ZMOI01"))
	thuong = _ct("KMLO01", vi_phat=0)
	vet, kq = _gui(thuong, con, loi_zalo=-201)
	la("chương trình thường: như cũ, phát mới và huỷ khi lỗi", (vet.phat, vet.huy), ([("KL0412", None)], ["ZMOI01"]))
	dung("chương trình thường: không khoá hồ sơ", not [b for b in vet.buoc if b.startswith("khoa")])


@ca("v623 tin Zalo phát mã Ví quà mới theo đúng luật Ví quà: dịp phát, số nhân viên, hạn tới cuối tháng sinh nhật (Codex PR #520 finding 1)")
def _zalo_luat_vi():
	sn = _ct("KMSN01", vi_dip="Thang sinh nhat", vi_so_lan="Moi nam mot lan")
	vet, kq = _gui(sn, [], sinh_nhat=None)
	la("chưa khai ngày sinh: không phát, không gửi", (vet.phat, vet.gui, vet.xong[-1][0]), ([], [], zk.TT_BO))
	dung("lý do nói rõ", "chưa khai ngày sinh" in vet.xong[-1][1])
	vet, kq = _gui(sn, [], sinh_nhat=D8(1990, 4, 2))
	la("ngoài tháng sinh nhật: không phát", (vet.phat, vet.xong[-1][0]), ([], zk.TT_BO))
	vet, kq = _gui(sn, [], sinh_nhat=D8(1990, 11, 14))
	la("đúng tháng: hạn tới cuối tháng, không theo 30 ngày của kịch bản", (kq, vet.phat, vet.gui[0]["han_dung"]),
		(0, [("KL0412", D8(2026, 11, 30))], "30/11/2026"))
	vet, kq = _gui(_ct("KMML01"), [], nhan_vien=True)
	la("số nhân viên: không phát", (vet.phat, vet.xong[-1][0]), ([], zk.TT_BO))
	vet, kq = _gui(_ct("KMML01", vi_han_ngay=7), [])
	la("Mọi lúc: hạn theo số ngày của chương trình", vet.phat, [("KL0412", D8(2026, 11, 19))])


@ca("v623 tin Zalo và trang thành viên khoá cùng dòng hồ sơ trước khi xét đã nhận; mã Ví quà mới ghi sổ trước khi gọi Zalo và không bị huỷ khi gửi lỗi (Codex PR #520 finding 2)")
def _zalo_khoa():
	ct = _ct("KMML01")
	vet, kq = _gui(ct, [])
	la("thứ tự: khoá, xét, phát, ghi sổ (nhả khoá) rồi mới gọi Zalo", vet.buoc[:5], ["khoa:KL0412", "doc_ky", "phat", "ghi", "gui"])
	vet, kq = _gui(ct, [], loi_zalo=-201)
	la("gửi lỗi: mã Ví quà mới vẫn giữ trong ví", (vet.phat, vet.huy), ([("KL0412", D8(2026, 12, 12))], [None]))
	src = (GOC / "thanh_vien.py").read_text()
	dung("cap_vi_tv khoá qua khoa_ho_so", "\tkhoa_ho_so(khach)\n\ttv = _ho_so_tv(khach)" in src)
	m = Moi()
	vas = m.vas()
	for v in vas:
		v.start()
	try:
		tv.khoa_ho_so("KL0412")
	finally:
		for v in reversed(vas):
			v.stop()
	la("khoá đúng dòng hồ sơ CRM", m.vet, [("sql", "select name from `tabVagabond Ho So CRM`")])


# ------------------------------------------------------------------ cấu hình

def _json_ctkm():
	return json.loads((GOC / "vagabond/doctype/vagabond_ctkm/vagabond_ctkm.json").read_text())


@ca("v623 phiếu Chương trình khuyến mãi: có mục Ví quà sau Cách phát mã, giá trị lựa chọn trùng tuyệt đối với chip trên app và máy chủ")
def _doctype():
	j = _json_ctkm()
	tr = {f["fieldname"]: f for f in j["fields"]}
	for t in ("sb_vi", "vi_phat", "vi_dip", "vi_so_lan", "vi_han_ngay"):
		dung("có ô %s trong field_order" % t, t in j["field_order"] and t in tr)
	i = j["field_order"].index
	dung("mục Ví quà đứng sau Cách phát mã", i("han_ma") < i("sb_vi") < i("vi_phat"))
	la("Dịp phát", tr["vi_dip"]["options"].split("\n"), list(tv.VI_DIP))
	la("Số lần nhận", tr["vi_so_lan"]["options"].split("\n"), list(tv.VI_SO_LAN))
	dung("mốc modified đã đẩy", j["modified"] >= "2026-10-31")
	js = (GOC / "public/js/bep/13-khuyen-mai.js").read_text()
	for ten, giu in (("KM_VI_DIP", tv.VI_DIP), ("KM_VI_SO_LAN", tv.VI_SO_LAN)):
		khoi = re.search(r"var %s = \[(.*?)\];" % ten, js, re.S).group(1)
		la("chip %s trùng giá trị lưu" % ten, re.findall(r"k: '([^']+)'", khoi), list(giu))
		dung("mỗi lựa chọn %s có tên có dấu và dòng giải thích" % ten,
			all(re.search(r"nhan: '[^']*[^\x00-\x7f][^']*', mo: '[^']{20,}'", d) for d in khoi.split("},")))
	for t in ("vi_phat", "vi_dip", "vi_so_lan", "vi_han_ngay"):
		dung("lưu từ app nhận ô %s" % t, t in km.TRUONG_CTKM)
		dung("tin Zalo đọc ô %s" % t, t in zk.COT_CTKM)
		dung("trang thành viên đọc ô %s" % t, t in tv.COT_CTKM_VI)


@ca("v623 phiếu Chương trình: bật Ví quà mà không phải mã dùng một lần thì chặn; bật đúng thì tự điền dịp, số lần, 30 ngày")
def _validate():
	from vagabond.vagabond.doctype.vagabond_ctkm.vagabond_ctkm import VagabondCTKM

	def doc(**v):
		d = D(nguoi_tao="a@x", cach_thuc="Giam tong hoa don", kieu_giam="So tien", gia_tri=50000, pham_vi="Ca hoa don",
			doi_tuong="Moi khach", cach_ma="Ma dung mot lan", bat=1, giam_toi_da=50000, dong_mon=[], vi_phat=1)
		d.update(v)
		return d
	for cm in ("Ma co dinh", "Khong can ma"):
		nem("bật Ví quà với %s" % cm, lambda: VagabondCTKM.validate(doc(cach_ma=cm, ma_co_dinh="VGB10")))
	d = doc()
	VagabondCTKM.validate(d)
	la("tự điền mặc định", (d.vi_dip, d.vi_so_lan, d.vi_han_ngay), ("Moi luc", "Mot lan", 30))
	d = doc(vi_dip="Thang sinh nhat", vi_so_lan="Moi nam mot lan", vi_han_ngay=0)
	VagabondCTKM.validate(d)
	la("giữ lựa chọn đã chọn", (d.vi_dip, d.vi_so_lan), ("Thang sinh nhat", "Moi nam mot lan"))
	d = doc(vi_phat=0, cach_ma="Ma co dinh", ma_co_dinh="vgb10")
	VagabondCTKM.validate(d)
	la("không bật Ví quà: mã cố định vẫn lưu được", d.ma_co_dinh, "VGB10")


@ca("v623 tắt Phát vào Ví quà sau khi đã phát: mã cũ trong ví vẫn chỉ dùng cho chính người nhận (Codex PR #520 vòng 4)")
def _tat_vi_giu_rang_buoc():
	# Chuỗi thật: trang thành viên cấp mã vào ví, rồi quản lý tắt Ví quà (vi_phat 0),
	# rồi thu ngân tra mã cho hoá đơn khách khác.
	m = Moi()
	m.chay(tv.cap_vi_tv)
	v = m.vc["VT0001"]
	la("mã ví mang dấu chỉ người nhận ngay lúc phát", v.get("chi_nguoi_nhan"), 1)
	tat = dict(_ct("KMML01"), vi_phat=0, bat=1, name="KMML01")
	fr = km.frappe
	dong = dict(v, han_dung=None)
	vas = [um.patch.object(fr.db, "exists", lambda d, n=None, *a, **k: d == "Vagabond Voucher"),
		um.patch.object(fr.db, "get_value", lambda d, ten, cot=None, as_dict=False, **k:
			(D({c: dong.get(c) for c in cot}) if d == "Vagabond Voucher" else None)),
		um.patch.object(km, "_doc_ctkm", lambda t: tat),
		um.patch.object(km, "_hop_thoi_gian", lambda k: (True, "")),
		um.patch.object(km, "_hop_kenh", lambda k, n, q: (True, ""))]
	for x in vas:
		x.start()
	try:
		tt = km._tra_ma("VT0001")
	finally:
		for x in reversed(vas):
			x.stop()
	la("tắt Ví quà rồi tra mã cũ: vẫn ràng buộc", tt["rang_buoc"], 1)
	dung("hoá đơn khách khác KL9999: vẫn từ chối", bool(km.kiem_nguoi_nhan(tt, "KL9999", "")[1]))
	la("phép thuần: chương trình đã tắt Ví quà, mã không mang dấu thì không ràng buộc",
		km.ma_rang_buoc({"name": "KMLO01", "vi_phat": 0}, {"chi_nguoi_nhan": 0}), 0)


@ca("v623 tin Zalo phát mã: chương trình Ví quà thì mã mang dấu chỉ người nhận; chương trình thường thì không")
def _zalo_dau_rang_buoc():
	ghi = []
	for ct, mong in ((_ct("KMML01"), 1), (_ct("KMLO01", vi_phat=0), 0)):
		del ghi[:]
		vas = [um.patch.object(zk, "_doc_ctkm", lambda t, ct=ct: D(ct, name=ct["name"], ten="Chương trình")),
			um.patch.object(zk, "_sinh_ma", lambda: "ZM0001"),
			um.patch.object(zk, "kich_ban", lambda m: {"ten": "Chào mừng"}),
			um.patch.object(zk.frappe, "get_doc", lambda d: (ghi.append(d), D(d, insert=lambda **k: None))[1])]
		for x in vas:
			x.start()
		try:
			zk._phat_voucher(D(ctkm=ct["name"]), {"ten": "Lan Anh", "sdt84": "84909123412"}, "KL0412", "chao_mung", han=D8(2026, 12, 12))
		finally:
			for x in reversed(vas):
				x.stop()
		la("%s: dấu chỉ người nhận" % ct["name"], ghi[0].get("chi_nguoi_nhan"), mong)


@ca("v623 phiếu mã: có ô Chỉ dùng cho người nhận (chỉ đọc), máy đọc ô này khi tra mã")
def _json_voucher():
	d = json.loads((GOC / "vagabond/doctype/vagabond_voucher/vagabond_voucher.json").read_text())
	f = [x for x in d["fields"] if x["fieldname"] == "chi_nguoi_nhan"]
	la("ô có, kiểu Check, chỉ đọc", [(x["fieldtype"], x.get("read_only")) for x in f], [("Check", 1)])
	dung("thứ tự ô đủ", d["field_order"] == [x["fieldname"] for x in d["fields"]])
	dung("mốc modified đã đẩy", d["modified"] >= "2026-10-31")
