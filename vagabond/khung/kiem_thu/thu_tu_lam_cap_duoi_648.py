# -*- coding: utf-8 -*-
"""v648 (anh Việt chốt 11/11/2026, phương án C): bếp chỉ bấm Hoàn tất món chính.

Pastry 14 ngày tới 10/11 chỉ có khoảng 10 lệnh (Baker 88): bấm cấp 1, rồi cấp 2,
rồi thành phẩm là "bấm không nổi". Thay vì bỏ cấp 1 khỏi công thức (mất dấu ruột
bánh làm sẵn trong tủ), máy tự làm phần CẤP 1, CẤP 2 còn thiếu tồn ngay lúc hoàn
tất món cha, như bán thành phẩm làm tươi. Ca ở đây chốt luật máy chủ
(kho_san_xuat.mon_tu_lam); hành vi app chạy thật ở hanh_vi/tu_lam_cap_duoi_648.js.
"""
import subprocess
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond import kho_san_xuat as ksx
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("v648 luật tự làm: chỉ món giữ tồn có công thức; làm tươi như cũ, thêm cấp 1, cấp 2; thành phẩm và nguyên liệu không")
def _():
	la("cấp 1", ksx.duoc_tu_lam(1, 0, ksx.BTP_SO_CAP, True), True)
	la("cấp 2", ksx.duoc_tu_lam(1, 0, ksx.BTP_SAN_SANG, True), True)
	la("làm tươi giữ tồn", ksx.duoc_tu_lam(1, 1, None, True), True)
	la("thành phẩm", ksx.duoc_tu_lam(1, 0, ksx.THANH_PHAM, True), False)
	la("nguyên liệu", ksx.duoc_tu_lam(1, 0, ksx.NGUYEN_LIEU, True), False)
	la("mặt hàng ảo (không giữ tồn) dù là cấp 1", ksx.duoc_tu_lam(0, 0, ksx.BTP_SO_CAP, True), False)
	la("chưa có công thức", ksx.duoc_tu_lam(1, 0, ksx.BTP_SO_CAP, False), False)


class _Kho:
	ITEM = [
		NS(name="NBTP00016", item_name="BTP Cấp 1 Bánh Ổ DIANTHUS size 16cm", is_stock_item=1, custom_lam_tuoi=0, custom_chang_btp=""),
		NS(name="NBTP00030", item_name="BTP Cấp 2 Bánh Ổ DIANTHUS size 16cm", is_stock_item=1, custom_lam_tuoi=0, custom_chang_btp=""),
		NS(name="NBTP00099", item_name="BTP Cấp 1 Bánh Ổ Epi size 12cm", is_stock_item=0, custom_lam_tuoi=0, custom_chang_btp=""),
		NS(name="BTPB00001", item_name="Kem tươi đánh bông", is_stock_item=1, custom_lam_tuoi=1, custom_chang_btp="BTP thành phần"),
		NS(name="NVLT00041", item_name="Trứng gà tươi", is_stock_item=1, custom_lam_tuoi=0, custom_chang_btp=""),
		NS(name="BAWC00068", item_name="Bánh Ổ Roman De La Rose, size 18cm", is_stock_item=1, custom_lam_tuoi=0, custom_chang_btp=""),
		NS(name="NBTP00077", item_name="BTP Cấp 2 Bánh Ổ Hannari size 12cm", is_stock_item=1, custom_lam_tuoi=0, custom_chang_btp=""),
	]
	BOM = ["NBTP00016", "NBTP00030", "NBTP00099", "BTPB00001", "BAWC00068"]

	def get_all(self, dt, filters=None, fields=None, pluck=None, **k):
		ds = filters["item" if dt == "BOM" else "name"][1]
		if dt == "BOM":
			return [m for m in self.BOM if m in ds]
		return [NS(**dict(vars(x), get=(lambda key, mac=None, x=x: getattr(x, key, mac)))) for x in self.ITEM if x.name in ds]


@ca("v648 mon_tu_lam trên kho giả: trả cấp 1, cấp 2, làm tươi có công thức và giữ tồn; bỏ ảo, NVL, thành phẩm, món chưa có công thức")
def _():
	k = _Kho()
	with patch.object(ksx.frappe, "get_all", k.get_all, create=True), \
			patch.object(ksx.frappe, "get_meta", lambda dt: NS(has_field=lambda f: True), create=True), \
			patch.object(ksx, "_co_btp_con", lambda ma: False):
		ra = ksx.mon_tu_lam('["NBTP00016","NBTP00030","NBTP00099","BTPB00001","NVLT00041","BAWC00068","NBTP00077"]')
	la("đúng các mã", sorted(ra), ["BTPB00001", "NBTP00016", "NBTP00030"])
	la("danh sách rỗng", ksx.mon_tu_lam("[]"), [])
	la("nhận BTP thành phần mọi cách gõ", [ksx.la_btp_thanh_phan(x) for x in ("BTP thành phần", " btp  THÀNH phần ", "BTP sơ cấp", None)],
		[True, True, False, False])


class _KhoThieuO(_Kho):
	"""Site chưa có ô Làm tươi (bench CI): hỏi cột không có thì MariaDB báo
	Unknown column; kho chỉ trả đúng các cột được hỏi."""
	CO = {"name", "item_name", "is_stock_item", "custom_chang_btp"}

	def get_all(self, dt, filters=None, fields=None, pluck=None, **k):
		if dt == "BOM":
			return super().get_all(dt, filters, fields, pluck, **k)
		la_cot = set(fields or ()) - self.CO
		if la_cot:
			raise Exception("(1054, \"Unknown column '%s' in 'SELECT'\")" % sorted(la_cot)[0])
		ds = filters["name"][1]
		ra = []
		for x in self.ITEM:
			if x.name in ds:
				d = {f: getattr(x, f) for f in fields}
				ra.append(NS(**dict(d, get=(lambda key, mac=None, d=d: d.get(key, mac)))))
		return ra


@ca("Codex #551 bench: site chưa có ô Làm tươi thì mon_tu_lam không hỏi cột đó, cấp 1, cấp 2 vẫn tự làm")
def _():
	k = _KhoThieuO()
	with patch.object(ksx.frappe, "get_all", k.get_all, create=True), \
			patch.object(ksx.frappe, "get_meta", lambda dt: NS(has_field=lambda f: f in _KhoThieuO.CO), create=True), \
			patch.object(ksx, "_co_btp_con", lambda ma: False):
		ra = ksx.mon_tu_lam('["NBTP00016","NBTP00030","NBTP00099","BTPB00001","NVLT00041","BAWC00068","NBTP00077"]')
	# BTPB00001 khai "BTP thành phần" (máy xếp về kho sơ cấp) chỉ tự làm nhờ cờ Làm
	# tươi; site không có ô Làm tươi thì không tự làm, không bị coi là ruột bánh cấp 1.
	la("cấp 1, cấp 2 vẫn tự làm", sorted(ra), ["NBTP00016", "NBTP00030"])


@ca("v648 app chạy thật trong node: bếp bấm Hoàn tất món chính, máy làm cấp 1 trước cấp 2, chỉ phần thiếu")
def _():
	goc = Path(__file__).parents[3]
	r = subprocess.run(["node", str(goc / "vagabond/khung/kiem_thu/hanh_vi/tu_lam_cap_duoi_648.js")],
		capture_output=True, text=True, timeout=120)
	dung("chạy được: " + (r.stdout[-1500:] + r.stderr[-600:]), r.returncode == 0)
	dung("đủ 23 ca", "23 dat, 0 hong" in r.stdout)
