# -*- coding: utf-8 -*-
"""v552: mã thay thế cho nguyên liệu KHÔNG theo lô khi hoàn tất lệnh sản xuất.

Ca thật 02/10/2026 (Khải báo): lệnh ở kho Baker - Nguyên liệu cần 1.248,113
ml whipping Lescure (NVLT00002), tồn 0; whipping Pauls (NVLT00329) còn
87.915,824 ml cùng kho, cặp thay thế đã khai hai chiều. Bấm Hoàn tất vẫn
bị chặn "Cần 1248.113 đơn vị". Đường lấy mã thay thế chỉ có trong
`lo_hang.gan_lo`, mà `gan_lo` chỉ xét dòng THEO LÔ; cả 15 cặp đang khai
trên site đều không theo lô.

Các ca dưới chạy THẬT `lo_hang.thay_ma_khong_lo` (hàm hook gọi), chỉ thay
các cửa đọc tồn và danh mục. Insert, submit và sổ kho thật nằm ở ca bench
`kiem_that/thu_thay_the_khong_lo_552.py`.
"""

from types import SimpleNamespace
from unittest.mock import patch

from vagabond import lo_hang as lh
from vagabond.khung.kiem_thu.nen import ca, dung, la


class Dong(object):
	def __init__(self, **kw):
		object.__setattr__(self, "_d", dict(kw))

	def __getattr__(self, k):
		d = object.__getattribute__(self, "_d")
		if k in d:
			return d[k]
		raise AttributeError(k)

	def get(self, k, mac_dinh=None):
		return object.__getattribute__(self, "_d").get(k, mac_dinh)

	def as_dict(self):
		return dict(object.__getattribute__(self, "_d"))


class Phieu(object):
	def __init__(self, purpose, dong, docstatus=0):
		self.purpose = purpose
		self.docstatus = docstatus
		self.items = list(dong)

	def set(self, ten, gt):
		if ten == "items":
			self.items = list(gt)

	def append(self, ten, x):
		if ten == "items":
			self.items.append(Dong(**x))


class Chan(Exception):
	pass


def _nem(cau, title=None):
	raise Chan(cau)


def dong(ma, kho, qty, he_so=1, uom="ML", ten=None, **them):
	d = {"item_code": ma, "s_warehouse": kho, "qty": qty, "conversion_factor": he_so,
		"uom": uom, "stock_uom": "ML", "name": ten or "dong-%s" % ma,
		"item_name": "Tên %s" % ma, "description": "Mô tả %s" % ma}
	d.update(them)
	return Dong(**d)


def chay(phieu, ton, thay=None, theo_lo=(), am=0):
	"""Chạy thật thay_ma_khong_lo. `ton`: {(mã, kho): số}. `thay`: {mã: [mã thay]}."""
	thay = thay or {}
	gia = SimpleNamespace(
		get_cached_value=lambda dt, ten, o=None, **k: "ML",
		db=SimpleNamespace(get_single_value=lambda dt, o: am),
		throw=_nem,
	)
	with patch.object(lh, "frappe", gia), \
			patch.object(lh, "_theo_lo", lambda ma: 1 if ma in theo_lo else 0), \
			patch.object(lh, "_ton_khong_lo", lambda ma, kho, luc=None: float(ton.get((ma, kho), 0))), \
			patch.object(lh, "_cac_ma_thay_the", lambda ma: list(thay.get(ma, []))), \
			patch.object(lh, "_kho_khac_con", lambda ma, kho: []), \
			patch.object(lh, "luc_cua_phieu", lambda doc: None), \
			patch.object(lh, "_ten_hang", lambda d, ma: "Tên %s" % ma):
		lh.thay_ma_khong_lo(phieu)
	return [d.as_dict() for d in phieu.items]


def gon(ra):
	return [(d.get("item_code"), d.get("original_item"), round(float(d.get("qty")), 6)) for d in ra]


BAKER = "Baker - Nguyên liệu - TV"


# ------------------------------------------------------------- phần thuần


@ca("v552 chia_khong_lo: mã gốc trước, thiếu mới lấy mã thay theo thứ tự, còn thiếu thì báo đúng số")
def _chia():
	la("gốc đủ", lh.chia_khong_lo(100, 300, [("B", 999)]), (100.0, [], 0.0))
	la("gốc hết, thay đủ (ca Lescure/Pauls)", lh.chia_khong_lo(1248.113, 0, [("NVLT00329", 87915.824)]),
		(0.0, [("NVLT00329", 1248.113)], 0.0))
	la("gốc một phần", lh.chia_khong_lo(100, 30, [("B", 999)]), (30.0, [("B", 70.0)], 0.0))
	la("hai mã thay, đúng thứ tự", lh.chia_khong_lo(100, 0, [("B", 40), ("C", 999)]),
		(0.0, [("B", 40.0), ("C", 60.0)], 0.0))
	la("thay cũng thiếu", lh.chia_khong_lo(100, 10, [("B", 50)]), (10.0, [("B", 50.0)], 40.0))
	la("tồn âm hay rỗng coi như 0", lh.chia_khong_lo(10, -5, [("B", None)]), (0.0, [], 10.0))


# --------------------------------------------------------- chạy thật hook


@ca("v552 ca thật: Lescure tồn 0, Pauls còn hàng cùng kho -> dòng đổi sang Pauls, giữ mã gốc, giữ tên dòng")
def _ca_that():
	ra = chay(Phieu("Manufacture", [dong("NVLT00002", BAKER, 1248.113, ten="row-1")]),
		ton={("NVLT00002", BAKER): 0, ("NVLT00329", BAKER): 87915.824},
		thay={"NVLT00002": ["NVLT00329"]})
	la("một dòng Pauls, mang mã gốc Lescure", gon(ra), [("NVLT00329", "NVLT00002", 1248.113)])
	la("giữ tên dòng gốc để Frappe sửa chứ không thêm", ra[0].get("name"), "row-1")
	la("cùng kho", ra[0].get("s_warehouse"), BAKER)
	dung("bỏ tên món cũ để ERPNext điền lại", "item_name" not in ra[0])
	dung("diễn giải nói rõ dùng thay", "NVLT00002" in (ra[0].get("description") or ""))


@ca("v552 gốc còn một phần: lấy hết gốc trước, phần thiếu sang mã thay")
def _mot_phan():
	ra = chay(Phieu("Manufacture", [dong("A", BAKER, 1000)]),
		ton={("A", BAKER): 400, ("B", BAKER): 5000}, thay={"A": ["B"]})
	la("hai dòng", gon(ra), [("A", None, 400.0), ("B", "A", 600.0)])


@ca("v552 hai dòng cùng mã cùng kho chung MỘT túi tồn, không ăn trùng phần tồn")
def _chung_tui():
	ra = chay(Phieu("Manufacture", [dong("A", BAKER, 600, ten="r1"), dong("A", BAKER, 600, ten="r2")]),
		ton={("A", BAKER): 1000, ("B", BAKER): 5000}, thay={"A": ["B"]})
	la("dòng hai chỉ còn 400 gốc", gon(ra), [("A", None, 600.0), ("A", None, 400.0), ("B", "A", 200.0)])


@ca("v552 dòng khai bằng đơn vị phụ: chia theo số gốc, dòng thay đi bằng đơn vị gốc")
def _he_so():
	ra = chay(Phieu("Manufacture", [dong("A", BAKER, 1.5, he_so=1000, uom="Lít")]),
		ton={("A", BAKER): 500, ("B", BAKER): 5000}, thay={"A": ["B"]})
	la("gốc 0,5 lít, thay 1000 ml", [(d["item_code"], round(float(d["qty"]), 6), d["conversion_factor"]) for d in ra],
		[("A", 0.5, 1000), ("B", 1000.0, 1)])


@ca("v552 chỉ luồng sản xuất: phiếu nhận nguyên liệu thiếu thì không tự đổi mã")
def _chi_san_xuat():
	p = Phieu("Material Transfer", [dong("A", BAKER, 100)])
	ra = chay(p, ton={("A", BAKER): 0, ("B", BAKER): 999}, thay={"A": ["B"]})
	la("giữ nguyên", gon(ra), [("A", None, 100.0)])


@ca("v552 không khai mã thay thì không đụng dòng, không tự ném (ERPNext chặn như cũ)")
def _khong_khai():
	ra = chay(Phieu("Manufacture", [dong("A", BAKER, 100)]), ton={("A", BAKER): 0})
	la("giữ nguyên", gon(ra), [("A", None, 100.0)])


@ca("v552 mã thay cũng không đủ: câu lỗi đọc được, nêu cả mã thay; kho cho âm thì không chặn")
def _thay_thieu():
	try:
		chay(Phieu("Manufacture", [dong("A", BAKER, 100)]),
			ton={("A", BAKER): 10, ("B", BAKER): 50}, thay={"A": ["B"]})
		dung("phải chặn", False)
	except Chan as e:
		dung("nói thiếu đúng 40", "40" in str(e))
	ra = chay(Phieu("Manufacture", [dong("A", BAKER, 100)]),
		ton={("A", BAKER): 10, ("B", BAKER): 50}, thay={"A": ["B"]}, am=1)
	la("cho âm: phần còn thiếu nằm lại dòng gốc", gon(ra), [("A", None, 50.0), ("B", "A", 50.0)])


@ca("v552 bỏ qua dòng theo lô (để gan_lo), dòng thành phẩm, dòng đã là dòng thay, và phiếu đã ghi sổ")
def _bo_qua():
	ton = {("A", BAKER): 0, ("B", BAKER): 999, ("L", BAKER): 0}
	thay = {"A": ["B"], "L": ["B"]}
	ra = chay(Phieu("Manufacture", [dong("L", BAKER, 5)]), ton, thay, theo_lo=("L",))
	la("dòng theo lô giữ nguyên", gon(ra), [("L", None, 5.0)])
	ra = chay(Phieu("Manufacture", [dong("A", BAKER, 5, is_finished_item=1)]), ton, thay)
	la("thành phẩm giữ nguyên", gon(ra), [("A", None, 5.0)])
	ra = chay(Phieu("Manufacture", [dong("A", BAKER, 5, original_item="X")]), ton, thay)
	la("dòng đã thay giữ nguyên", gon(ra), [("A", "X", 5.0)])
	ra = chay(Phieu("Manufacture", [dong("A", BAKER, 5)], docstatus=1), ton, thay)
	la("phiếu đã ghi sổ không sửa", gon(ra), [("A", None, 5.0)])
	ra = chay(Phieu("Manufacture", [dong("A", BAKER, 5)]), ton, {"A": ["L"]}, theo_lo=("L",))
	la("mã thay theo lô không dùng ở đường này", gon(ra), [("A", None, 5.0)])


@ca("v552 _cac_ma_thay_the: món gốc tắt 'cho phép thay' thì không có mã thay (khớp màn Mặt hàng thay thế)")
def _cho_phep():
	def gia(cho):
		def gcv(dt, ten, o=None, **k):
			if k.get("as_dict"):
				return {"stock_uom": "ML", "disabled": 0, "is_stock_item": 1}
			if isinstance(o, (list, tuple)):
				return ("ML", cho)
			if o == "stock_uom":
				return "ML"
			return {"stock_uom": "ML", "disabled": 0, "is_stock_item": 1}

		def get_all(dt, filters=None, pluck=None, **k):
			if filters.get("item_code") == "A":
				return ["B"]
			return []
		return SimpleNamespace(get_cached_value=gcv, get_all=get_all)
	with patch.object(lh, "frappe", gia(0)):
		la("tắt", lh._cac_ma_thay_the("A"), [])
	with patch.object(lh, "frappe", gia(1)):
		la("bật", lh._cac_ma_thay_the("A"), ["B"])


@ca("v552 hook đăng ký NGAY TRƯỚC gan_lo trong before_validate của Stock Entry")
def _thu_tu_hook():
	from pathlib import Path
	import re
	nguon = (Path(lh.__file__).resolve().parent / "hooks.py").read_text(encoding="utf-8")
	ds = re.findall(r'"(vagabond\.[a-z_]+\.[a-z_]+)"', nguon.split('"Stock Entry": {', 1)[1].split("},", 1)[0])
	dung("có hook", "vagabond.lo_hang.thay_ma_khong_lo" in ds)
	la("đứng ngay trước gan_lo", ds.index("vagabond.lo_hang.gan_lo") - ds.index("vagabond.lo_hang.thay_ma_khong_lo"), 1)
