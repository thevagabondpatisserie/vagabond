# -*- coding: utf-8 -*-
"""v650 (Uyên báo 12/11/2026, DMH-2026-00970): đơn mua tính thuế GTGT hai lần.

Mẫu thuế từng món của site khai cả 1331 (đầu vào) lẫn 33311 (đầu ra), mỗi tài
khoản 8%; Cài đặt kế toán tự thêm dòng thuế theo mẫu của món nên đơn mua có hai
dòng: 620.000 đ ra thuế 99.200 đ. Ca ERPNext thật ở kiem_that/thu_thue_mua_hai_lan_650.
"""
from types import SimpleNamespace as NS

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
from vagabond import thue_don_mua as tdm  # noqa: E402

VAO = "1331 - Thuế GTGT được khấu trừ của hàng hóa, dịch vụ - TV"
RA = "33311 - Thuế GTGT đầu ra - TV"


def _d(tk, rate=0.0, loai="On Net Total"):
	return {"account_head": tk, "rate": rate, "charge_type": loai}


@ca("v650 thuần: chỉ bỏ dòng 33311 máy tự thêm (On Net Total, thuế suất 0) khi đã có dòng 1331")
def _():
	g = tdm.dong_thue_ra_tu_them
	la("đúng hai dòng của DMH-2026-00970: bỏ dòng 33311", g([_d(VAO), _d(RA)]), [1])
	la("thứ tự ngược vẫn đúng", g([_d(RA), _d(VAO)]), [0])
	la("không có 1331 thì không đoán", g([_d(RA)]), [])
	la("33311 tự khai thuế suất thì giữ", g([_d(VAO), _d(RA, 2)]), [])
	la("33311 loại khác thì giữ", g([_d(VAO), _d(RA, 0, "Actual")]), [])
	la("không có thuế", g([]), [])
	la("đọc được dòng Frappe kiểu thuộc tính", g([NS(account_head=VAO, rate=0, charge_type="On Net Total"), NS(account_head=RA, rate=0, charge_type="On Net Total")]), [1])
	la("tài khoản 13311 không nhầm là 1331", g([_d("13311 - Khác - TV"), _d(RA)]), [])


class _Don(dict):
	__getattr__ = dict.get

	def set(self, k, v):
		self[k] = v

	def calculate_taxes_and_totals(self):
		self["tinh_lai"] = self.get("tinh_lai", 0) + 1
		self["total_taxes_and_charges"] = sum(620000 * 0.08 for r in self["taxes"])


class _Dong(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v


@ca("v650 hook: chứng từ mua hai dòng thì bỏ 33311 và tính lại tổng (620.000 đ ra thuế 49.600 đ); lúc submit (docstatus 1) cũng chạy; huỷ thì không đụng")
def _():
	for ds in (0, 1):
		d = _Don(docstatus=ds, taxes=[_Dong(_d(VAO), idx=1), _Dong(_d(RA), idx=2)])
		tdm.bo_thue_ra_chung_tu_mua(d)
		la("docstatus %d: còn 1331" % ds, [r["account_head"] for r in d["taxes"]], [VAO])
		la("docstatus %d: thuế 49.600, tính lại một lần" % ds, (d["total_taxes_and_charges"], d["tinh_lai"]), (49600, 1))
	d = _Don(docstatus=0, taxes=[_Dong(_d(RA), idx=1), _Dong(_d(VAO), idx=2)])
	tdm.bo_thue_ra_chung_tu_mua(d)
	la("đánh lại số thứ tự", [r["idx"] for r in d["taxes"]], [1])
	d = _Don(docstatus=2, taxes=[_Dong(_d(VAO)), _Dong(_d(RA))])
	tdm.bo_thue_ra_chung_tu_mua(d)
	la("huỷ: không đụng", (len(d["taxes"]), d.get("tinh_lai")), (2, None))
	d = _Don(docstatus=0, taxes=[_Dong(_d(VAO))])
	tdm.bo_thue_ra_chung_tu_mua(d)
	la("một dòng: không tính lại", d.get("tinh_lai"), None)


@ca("v650 hook gắn CUỐI validate đúng bốn chứng từ mua, không đặt trên chứng từ bán hay \"*\"")
def _():
	import ast
	import os

	p = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "hooks.py")
	ma = open(p, encoding="utf-8").read()
	ns = {"__file__": p}
	try:
		exec(compile(ma, p, "exec"), ns)
	except Exception as e:  # noqa: BLE001
		dung("đọc được hooks.py: %s" % e, False)
		return
	ev = ns["doc_events"]
	ham = "vagabond.thue_don_mua.bo_thue_ra_chung_tu_mua"
	co = sorted(dt for dt, s in ev.items() if ham in (s.get("validate") if isinstance(s.get("validate"), list) else [s.get("validate")]))
	la("bốn chứng từ mua", co, ["Purchase Invoice", "Purchase Order", "Purchase Receipt", "Supplier Quotation"])
	dung("đứng cuối validate", all(ev[dt]["validate"][-1] == ham for dt in co))
	dung("dòng bỏ thuế ở hook gốc #227 vẫn còn", "vagabond.thue_don_mua.theo_mau_dau_phieu" in ev["Purchase Order"]["before_validate"])
	dung("khai báo ast hợp lệ", bool(ast.parse(ma)))


@ca("v650 Gom yêu cầu mua: thuế suất từng món lấy đúng dòng 1331 của mẫu thuế món; nhóm có tiền thuế tạm tính")
def _():
	from vagabond import gom_mua as gm

	ct = {"GTGT 8% - TV": [(VAO, 8.0), (RA, 8.0)], "GTGT 0% - TV": [(VAO, 0.0), (RA, 0.0)], "Chỉ bán - TV": [(RA, 10.0)]}
	la("8%, 0%, mẫu không có 1331 thì bỏ, món chưa khai thì bỏ",
		gm.thue_cua_mon({"A": "GTGT 8% - TV", "B": "GTGT 0% - TV", "C": "Chỉ bán - TV"}, ct), {"A": 8.0, "B": 0.0})
	dong = [{"ten": "r1", "phieu": "YCMH-1", "ma": "A", "ten_mon": "Hũ sốt", "xin": 2000, "dvt": "Cái", "ngay": "2026-11-12"}]
	g = gm.gom(dong, {"A": "NCC"}, {}, {"A": 310}, {}, {"NCC": "The Minhs"}, {"A": 8.0})
	la("món mang thuế suất", g[0]["mon"][0]["thue"], 8.0)
	la("nhóm: tiền 620.000, thuế 49.600 (một lần)", (g[0]["tien"], g[0]["tien_thue"]), (620000, 49600))
	g = gm.gom(dong, {"A": "NCC"}, {}, {"A": 310})
	la("không truyền thuế: như cũ, món chưa khai", (g[0]["mon"][0]["thue"], g[0]["tien_thue"]), (None, 0))


@ca("Codex #553 vòng 4: màn Gom yêu cầu mua đếm tồn đúng Kho tổng 307, không cộng tồn bếp vào chip Kho tổng")
def _():
	from unittest.mock import patch

	from vagabond import duyet_ycmh as dy
	from vagabond import gom_mua as gm
	from vagabond.kho_san_xuat import KHO_GOC

	bin_ = {("A", KHO_GOC): 0.0, ("A", "Pastry - Nguyên liệu - TV"): 5000.0}

	def boi_canh(ma, bo_qua_phieu=None, kho=None):
		# Đúng hợp đồng của duyet_ycmh.boi_canh_hang: có kho thì `ton` chỉ đếm kho đó.
		return {m: {"ton": sum(v for (mm, k), v in bin_.items() if mm == m and (not kho or k == kho)),
			"ton_tat_ca": sum(v for (mm, k), v in bin_.items() if mm == m), "cho_ve": 0.0} for m in ma}

	dong = [{"ten": "r1", "phieu": "YCMH-1", "ma": "A", "ten_mon": "Bơ", "xin": 2000, "dvt": "Gram", "ngay": "2026-11-12"}]
	with patch.object(gm, "_kiem_quyen", lambda: None), patch.object(gm, "dong_cho_gom", lambda: dong), \
			patch.object(gm, "_ncc_cua", lambda m: ({"A": "NCC"}, {"NCC": "An Phú"})), \
			patch.object(gm, "_gia_anh", lambda m: ({"A": 0.25}, {})), patch.object(gm, "_thue", lambda m: {}), \
			patch.object(dy, "boi_canh_hang", boi_canh):
		ra = gm.ds()
	la("Kho tổng 0 dù bếp còn 5000", ra["nhom"][0]["mon"][0]["ton"], 0.0)


@ca("v650 app: màn Gom yêu cầu mua chạy bộ kiểm hành vi node (chip, VAT, nút không tràn ngang)")
def _():
	import os
	import subprocess

	goc = os.path.dirname(os.path.abspath(__file__))
	for tep, mong in (("gom_chip_650.js", "5 dat, 0 hong"),):
		r = subprocess.run(["node", os.path.join(goc, "hanh_vi", tep)], capture_output=True, text=True)
		la(tep, (r.returncode, r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:]), (0, mong))
