# -*- coding: utf-8 -*-
"""v528: khoản chi trước, hoá đơn về sau (anh Việt 25/09/2026).

Hai ca thật trên site:

- Phiếu trả trước APP-26-09-893 (Hộ kinh doanh Nhà Sen, 3.650.000 đ trả trước
  cho đơn mua DMH-2026-00472) đã ghi sổ thì màn phiếu chi chỉ còn dòng "Không
  có thao tác cho vai trò của bạn": không khớp sao kê, không đính uỷ nhiệm
  chi, không nối được hoá đơn khi nhà cung cấp xuất sau. Anh Việt chốt: nút
  nối hoá đơn là CẤN TRỪ luôn khoản trả trước vào hoá đơn.
- Hồ sơ APP.26.09.010 (Adecco, chi từ TK công ty 07/09) lập trước v526 nên
  khoản chưa có cờ "hoá đơn đến sau", nút nối không bao giờ hiện. Anh Việt
  chốt: cho FIN hoặc giám đốc đánh dấu bù.

Ca kiểm chạy hàm THẬT (máy chủ) và màn THẬT (nạp tệp app vào node, API giả).
Không gọi thêm hàm nào ngoài chuỗi thao tác của người dùng (điều 15).
"""

import json
import subprocess
import sys
import unittest.mock
from pathlib import Path
from types import SimpleNamespace as NS

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[2]


class _D(dict):
	__getattr__ = dict.get


# ------------------------------------------------------------------ thuần


@ca("v528 đánh dấu bù: đúng ca Adecco thì được, mọi ca khác nói rõ vì sao không")
def _danh_dau_thuan():
	from vagabond.ho_so_bo_sung import loi_danh_dau_bu as f
	adecco = {"hoa_don": None, "cho_hoa_don": 0, "hoa_don_bo_sung": None}
	la("hồ sơ TK công ty đã thanh toán, khoản chưa có hoá đơn: được", f("TK cong ty", "Da thanh toan", adecco), "")
	dung("hồ sơ NCC: không", "TK công ty" in f("NCC", "Da duyet", adecco))
	dung("hồ sơ huỷ: không", "huỷ" in f("TK cong ty", "Huy", adecco))
	dung("hồ sơ bị từ chối: không", "từ chối" in f("TK cong ty", "Tu choi", adecco))
	dung("khoản đã có hoá đơn gốc: không", "hoá đơn gốc" in f("TK cong ty", "Da duyet", dict(adecco, hoa_don="ACC-PINV-1")))
	dung("khoản đã nối: không", "đã nối" in f("TK cong ty", "Da duyet", dict(adecco, hoa_don_bo_sung="ACC-PINV-2")))
	dung("đã đánh dấu rồi: không", "rồi" in f("TK cong ty", "Da duyet", dict(adecco, cho_hoa_don=1)))


@ca("v528 gợi ý hoá đơn cấn trả trước: tờ cùng đơn mua lên đầu, tờ cũ trước, bỏ tờ hết nợ")
def _xep_hoa_don():
	from vagabond.coc_app import xep_hoa_don_can as f
	ds = [
		{"name": "PI-3", "bill_date": "2026-09-20", "outstanding_amount": 500, "don_mua": []},
		{"name": "PI-1", "bill_date": "2026-09-25", "outstanding_amount": 7300000, "don_mua": ["DMH-2026-00472"]},
		{"name": "PI-2", "bill_date": "2026-09-10", "outstanding_amount": 100, "don_mua": ["DMH-KHAC"]},
		{"name": "PI-0", "bill_date": "2026-09-01", "outstanding_amount": 0, "don_mua": ["DMH-2026-00472"]},
	]
	ra = f(ds, ["DMH-2026-00472"])
	la("thứ tự", [x["name"] for x in ra], ["PI-1", "PI-2", "PI-3"])
	la("cờ cùng đơn", [x["cung_don"] for x in ra], [1, 0, 0])


# ------------------------------------------------------- máy chủ, hàm thật


def _danh_dau_that(loai="TK cong ty", trang_thai="Da thanh toan", dong=1, vai=("AP Kiểm soát (FIN)",)):
	from vagabond import ho_so_bo_sung as hb
	ghi = {"save": 0, "nhat_ky": []}
	kd = _D(hoa_don=None, cho_hoa_don=0, hoa_don_bo_sung=None)
	kd.as_dict = lambda: dict(kd)
	doc = NS(loai=loai, trang_thai=trang_thai, dong=[kd],
		save=lambda **k: ghi.__setitem__("save", ghi["save"] + 1),
		add_comment=lambda loai_, noi: ghi["nhat_ky"].append(noi))
	import frappe as _fr

	def kiem(nhom, viec):
		if not nhom & set(vai):
			_fr.throw("Tài khoản của bạn không có quyền %s." % viec)
	hs = NS(_kiem=kiem, VAI_FIN={"AP Kiểm soát (FIN)"}, VAI_GD={"AP Giám đốc"}, LOAI_TKCT="TK cong ty")
	f = NS(db=NS(sql=lambda *a, **k: None), get_doc=lambda dt, ten: doc, throw=_fr.throw,
		session=NS(user="dung@vagabond"))
	with unittest.mock.patch.object(hb, "frappe", f), unittest.mock.patch.dict(sys.modules, {"vagabond.ho_so_tt": hs}):
		try:
			return hb.danh_dau_cho_hoa_don("APP.26.09.010", dong), kd, ghi
		except Exception as e:
			return {"loi": str(e)}, kd, ghi


@ca("v528 đánh dấu bù (hàm thật): FIN đánh dấu khoản Adecco, lưu một lần, có nhật ký người bấm")
def _danh_dau_that_ok():
	kq, kd, ghi = _danh_dau_that()
	la("trả ok", kq, {"ok": 1, "dong": 1})
	la("cờ bật và lưu một lần", (kd.cho_hoa_don, ghi["save"]), (1, 1))
	dung("nhật ký có người bấm", len(ghi["nhat_ky"]) == 1 and "dung@vagabond" in ghi["nhat_ky"][0])


@ca("v528 đánh dấu bù (hàm thật): sales không làm được, hồ sơ NCC không, khoản ngoài phạm vi không, không lưu gì")
def _danh_dau_that_chan():
	for mo_ta, kw, chu in (
			("sales", {"vai": ("Sales User",)}, "không có quyền"),
			("hồ sơ NCC", {"loai": "NCC"}, "TK công ty"),
			("khoản thứ 2 không có", {"dong": 2}, "Không tìm thấy khoản"),
			("hồ sơ huỷ", {"trang_thai": "Huy"}, "huỷ")):
		kq, kd, ghi = _danh_dau_that(**kw)
		dung(mo_ta + ": chặn có lời", chu in kq.get("loi", ""))
		la(mo_ta + ": không lưu, không bật cờ", (ghi["save"], kd.cho_hoa_don), (0, 0))


def _unc_that(docstatus=1, co_po=True, unc='["/private/files/unc-moi.jpg"]', cu='["/private/files/unc-cu.jpg"]',
		vai=("AP Kiểm soát (FIN)",)):
	from vagabond import duyet_chi as dc
	from vagabond import tep_dinh_kem as tdk
	ghi = {"set": [], "vet": []}
	doc = _D(name="APP-26-09-893", docstatus=docstatus, payment_type="Pay", party_type="Supplier",
		references=[_D(reference_doctype="Purchase Order" if co_po else "Purchase Invoice", reference_name="DMH-2026-00472")],
		vgb_chi_unc=cu)
	import frappe as _fr
	f = NS(get_doc=lambda dt, ten=None: doc if dt == "Payment Entry" else (ghi["vet"].append(dt) or NS(insert=lambda **k: None)),
		get_roles=lambda: list(vai), throw=_fr.throw, session=NS(user="dung@vagabond"),
		db=NS(set_value=lambda dt, ten, o, gt, **k: ghi["set"].append((ten, o, gt)), commit=lambda: None))
	gan = lambda dt, ten, o, ds: [u for u in tdk.doc_ds(ds)]
	with unittest.mock.patch.object(dc, "frappe", f), unittest.mock.patch.object(tdk, "gan_vao", gan):
		try:
			return dc.dinh_unc_sau("APP-26-09-893", unc), ghi
		except Exception as e:
			return {"loi": str(e)}, ghi


@ca("v528 đính UNC sau ghi sổ (hàm thật): gộp tờ cũ với tờ mới, không mất tờ cũ, chỉ kế toán, chỉ phiếu trả trước đã ghi sổ")
def _unc():
	kq, ghi = _unc_that()
	la("hai tờ", kq, {"ok": 1, "so_unc": 2})
	la("ghi đúng ô, giữ tờ cũ đứng trước", [(t, o, json.loads(g)) for t, o, g in ghi["set"]],
		[("APP-26-09-893", "vgb_chi_unc", ["/private/files/unc-cu.jpg", "/private/files/unc-moi.jpg"])])
	for mo_ta, kw, chu in (
			("phiếu chưa ghi sổ", {"docstatus": 0}, "Xác nhận đã chuyển tiền"),
			("không phải phiếu trả trước", {"co_po": False}, "không phải phiếu trả trước"),
			("không chọn tệp", {"unc": "[]"}, "Chưa có tệp"),
			("sales", {"vai": ("Sales User",)}, "kế toán")):
		kq, ghi = _unc_that(**kw)
		dung(mo_ta + ": chặn có lời, không ghi", chu in kq.get("loi", "") and ghi["set"] == [])


def _xem_that(pe_kw=None, links=(), con_coc=3650000.0):
	from vagabond import coc_app as ca_
	pe = _D(name="APP-26-09-893", docstatus=1, payment_type="Pay", party_type="Supplier", party="NHA-SEN",
		party_name="Hộ kinh doanh Nhà Sen", company="VGB", paid_to="331 - TV", paid_amount=3650000,
		references=[_D(reference_doctype="Purchase Order", reference_name="DMH-2026-00472", allocated_amount=3650000)],
		vgb_chi_unc='["/private/files/unc.jpg"]')
	pe.update(pe_kw or {})
	pe.check_permission = lambda *a: None
	hd = [_D(name="PI-9", bill_no="0000123", bill_date="2026-09-25", posting_date="2026-09-25",
		grand_total=7300000, outstanding_amount=7300000),
		_D(name="PI-7", bill_no="77", bill_date="2026-09-01", posting_date="2026-09-01",
		grand_total=100000, outstanding_amount=100000)]
	hoi = []

	def get_list(dt, filters=None, fields=None, **k):
		hoi.append((dt, filters))
		return hd if filters.get("docstatus") == 1 else [_D(name="PI-NHAP", bill_no="88", grand_total=5)]
	f = NS(get_doc=lambda dt, ten: pe, get_list=get_list,
		get_all=lambda dt, filters=None, **k: [_D(parent="PI-9", purchase_order="DMH-2026-00472")])
	with unittest.mock.patch.object(ca_, "frappe", f), \
			unittest.mock.patch.object(ca_.hs, "_kiem", lambda *a: None), \
			unittest.mock.patch.object(ca_, "_phieu", lambda ten, ncc, **k: (pe, [_D(name=x, allocated_amount=3650000) for x in links])), \
			unittest.mock.patch.object(ca_, "_doi_chieu", lambda p, *a: (None, [{"amount": con_coc}] if con_coc else [])):
		return ca_.tra_truoc_xem("APP-26-09-893"), hoi


@ca("v528 tình hình trả trước (hàm thật): APP-26-09-893 chưa khớp sao kê, có 1 UNC, còn 3.650.000 đ chưa cấn, tờ cùng đơn mua lên đầu")
def _xem():
	kq, hoi = _xem_that()
	la("là trả trước", kq["la_tra_truoc"], 1)
	la("sao kê chưa khớp", (kq["sao_ke"], kq["can_noi_sao_ke"]), ([], 1))
	la("một tờ UNC", kq["so_unc"], 1)
	la("còn trả trước", kq["con_coc"], 3650000.0)
	la("hoá đơn gợi ý: cùng đơn mua trước", [(x["name"], x["cung_don"]) for x in kq["hoa_don"]], [("PI-9", 1), ("PI-7", 0)])
	la("báo tờ nháp chưa ghi sổ", [x["bill_no"] for x in kq["nhap"]], ["88"])
	loc = [f for dt, f in hoi if f.get("docstatus") == 1][0]
	la("chỉ tờ đã ghi sổ, còn nợ, đúng NCC, đúng tài khoản công nợ",
		(loc["supplier"], loc["outstanding_amount"], loc["credit_to"]), ("NHA-SEN", [">", 0], "331 - TV"))
	kq, _ = _xem_that(links=("ACC-BTN-2026-06243",))
	la("đã khớp sao kê", (kq["sao_ke"], kq["can_noi_sao_ke"]), (["ACC-BTN-2026-06243"], 0))
	kq, _ = _xem_that(pe_kw={"references": [_D(reference_doctype="Purchase Invoice", reference_name="PI-1", allocated_amount=1)]})
	la("phiếu không neo đơn mua: không phải trả trước", kq, {"la_tra_truoc": 0})
	kq, _ = _xem_that(pe_kw={"docstatus": 0})
	la("phiếu chưa ghi sổ: không", kq, {"la_tra_truoc": 0})


# ------------------------------------------------------------- màn thật


def _node(kich, tep):
	goc = GOC / "public" / "js" / "bep"

	def cat(t, ten):
		import re
		s = (goc / t).read_text(encoding="utf-8")
		m = re.search(r"\nfunction %s\([^)]*\) ?\{.*?\n\}" % ten, s, re.S)
		return m.group(0)
	nen = cat("00-nen.js", "h") + cat("00-nen.js", "money") + cat("09-tinh-tien-quay.js", "posChipNut") + \
		cat("13-khuyen-mai.js", "kmHangChip")
	# Mã nguồn đọc thẳng từ đĩa trong node, kịch bản đi qua stdin: nhét cả
	# tệp vào dòng lệnh thì vượt giới hạn độ dài tham số của hệ điều hành.
	ma = " + ".join("require('fs').readFileSync(%s, 'utf8')" % json.dumps(str(goc / t)) for t in tep)
	kich = kich.replace("__NEN__", json.dumps(nen)).replace("__MA__", ma)
	r = subprocess.run(["node", "-"], input=kich, capture_output=True, text=True, timeout=60)
	if r.returncode != 0:
		raise AssertionError("node lỗi: " + (r.stderr or "").strip()[:600])
	return json.loads(r.stdout)


KHUNG_JS = r"""
const vm = require('vm');
const ghi = { html: [], api: [], chon: [], can: [], sk: [], go: [], bao: [] };
let khung = null; const phan = {};
function el(id) { const h = ghi.html[ghi.html.length - 1] || ''; if (h.indexOf('id="' + id + '"') < 0) return null;
  return phan[id] || (phan[id] = { id: id, innerHTML: '', onclick: null }); }
const ctx = { console: console, setTimeout: setTimeout, JSON: JSON,
  document: { getElementById: el, querySelector: function () { return null; }, querySelectorAll: function () { return []; } },
  root: { querySelector: function () { return null; } },
  sessionStorage: { getItem: function () { return null; }, setItem: function () {}, removeItem: function () {} },
  frame: function (t, b, o) { ghi.html.push(b + ((o && o.footer) || '')); khung = { onclick: null, addEventListener: function (e, f) { khung.nghe = f; }, querySelector: function () { return null; } }; return khung; },
  api: async function (m, a) { ghi.api.push([m, a || {}]); return TRA(m, a || {}); },
  getList: async function () { return []; }, dmy: function (x) { return x; }, payNhan: function (x) { return x; },
  hasRole: function (r) { return VAI.indexOf(r) >= 0; }, errMsg: function (e) { return e && e.message; },
  go: function (f) { ghi.go.push(1); }, busy: function () {}, toast: function () {}, baoTin: function (x) { ghi.bao.push(x); },
  hoiCo: async function () { return true; }, hoiChon: async function (t, m, ds) { ghi.chon.push(ds.map(function (x) { return x.k; })); return CHON; },
  tdkNap: function () {}, tdkKhoi: function () { return '<i>tdk</i>'; }, tdkNoi: function () {}, tdkDs: function () { return TDK; },
  S: { user: 'x' } };
vm.createContext(ctx);
vm.runInContext(__NEN__, ctx);
vm.runInContext(__MA__, ctx);
__THEM__
"""


def _xem_phieu(pe, tt, vai=("AP Kiểm soát (FIN)",), bam=None, chon=None, tdk=()):
	them = r"""
ctx.hsChonCanCoc = function (ncc, dong, xong, ds, pe) { ghi.can.push({ ncc: ncc, dong: dong, pe: pe, co_ds: !!(ds && ds.rows) }); };
ctx.hsNoiSaoKeCoc = function (ncc, pe, xong) { ghi.sk.push([ncc, pe]); };
(async function () {
  await ctx.scrPayView('APP-26-09-893');
  const b = BAM && phan[BAM];
  if (BAM && !b) throw new Error('khong thay nut ' + BAM);
  if (b) { await b.onclick(); }
  process.stdout.write(JSON.stringify({ html: ghi.html[ghi.html.length - 1], api: ghi.api, chon: ghi.chon, can: ghi.can, sk: ghi.sk, bao: ghi.bao, go: ghi.go.length }));
})().catch(function (e) { console.error(e && e.stack || e); process.exit(1); });
"""
	kich = KHUNG_JS.replace("__THEM__", them)
	for k, v in (("TRA(m, a || {})", "(m === 'frappe.client.get' ? PE : (m === 'vagabond.coc_app.tra_truoc_xem' ? TT : (m === 'vagabond.coc_app.danh_sach' ? { rows: [{ name: 'APP-26-09-893', con_coc: 3650000 }] } : { so_unc: 2 })))"),):
		kich = kich.replace(k, v)
	kich = kich.replace("const vm = require('vm');", "const vm = require('vm'); const PE = %s; const TT = %s; const VAI = %s; const BAM = %s; const CHON = %s; const TDK = %s;" % (
		json.dumps(pe), json.dumps(tt), json.dumps(list(vai)), json.dumps(bam), json.dumps(chon), json.dumps(list(tdk))))
	return _node(kich, ["04-tao-phieu.js", "19-ho-so-tt.js"])


PE_893 = {"name": "APP-26-09-893", "docstatus": 1, "payment_type": "Pay", "party_type": "Supplier", "party": "NHA-SEN",
	"paid_amount": 3650000, "workflow_state": "Đã duyệt - Đã ghi sổ",
	"references": [{"reference_doctype": "Purchase Order", "reference_name": "DMH-2026-00472", "allocated_amount": 3650000}]}
TT_893 = {"la_tra_truoc": 1, "payment_entry": "APP-26-09-893", "ncc": "NHA-SEN", "ten_ncc": "Nhà Sen", "tien": 3650000,
	"con_coc": 3650000, "don_mua": ["DMH-2026-00472"], "sao_ke": [], "can_noi_sao_ke": 1, "so_unc": 1, "da_can": [],
	"hoa_don": [{"name": "PI-9", "bill_no": "123", "ngay": "2026-09-25", "tong": 7300000, "con_no": 7300000, "cung_don": 1}],
	"nhap": []}


@ca("v528 màn phiếu trả trước (thật): phiếu đã ghi sổ có đủ ba nút, người không phải kế toán thì không")
def _man_phieu():
	ra = _xem_phieu(PE_893, TT_893)
	for id_ in ("pvKhopSk", "pvUncSau", "pvLuuUnc", "pvNoiHd"):
		dung("có " + id_, 'id="%s"' % id_ in ra["html"])
	dung("báo chưa khớp sao kê và còn trả trước", "chưa khớp" in ra["html"] and "3.650.000" in ra["html"])
	ra = _xem_phieu(PE_893, TT_893, vai=("Sales User",))
	dung("sales: không có khối, không gọi API tình hình", "pvNoiHd" not in ra["html"]
		and not any(m == "vagabond.coc_app.tra_truoc_xem" for m, a in ra["api"]))
	ra = _xem_phieu(dict(PE_893, docstatus=0, workflow_state="Chờ FIN kiểm tra"), TT_893)
	dung("phiếu chưa ghi sổ: không có khối", "pvNoiHd" not in ra["html"])
	ra = _xem_phieu(PE_893, dict(TT_893, can_noi_sao_ke=0, sao_ke=["ACC-BTN-1"], con_coc=0,
		da_can=[{"hoa_don": "PI-9", "tien": 3650000}]))
	dung("đã khớp và đã cấn hết: không còn nút khớp, không còn nút nối", "pvKhopSk" not in ra["html"]
		and "pvNoiHd" not in ra["html"] and "PI-9" in ra["html"])


@ca("v528 màn phiếu trả trước (thật): bấm nối hoá đơn thì chọn tờ rồi đi đúng cửa cấn trừ với đúng số tiền")
def _man_noi():
	ra = _xem_phieu(PE_893, TT_893, bam="pvNoiHd", chon="PI-9")
	la("danh sách chọn là tờ còn nợ", ra["chon"], [["PI-9"]])
	la("đi cửa cấn trừ với tờ đã chọn, tối đa số còn trả trước",
		ra["can"], [{"ncc": "NHA-SEN", "dong": [{"hoa_don": "PI-9", "so_tien": 3650000}], "pe": "APP-26-09-893", "co_ds": True}])
	ra = _xem_phieu(PE_893, TT_893, bam="pvNoiHd", chon=None)
	la("bấm Thôi: không cấn", ra["can"], [])
	ra = _xem_phieu(PE_893, dict(TT_893, hoa_don=[]), bam="pvNoiHd")
	dung("chưa có hoá đơn ghi sổ: báo rõ, không mở chọn", ra["chon"] == [] and "ghi sổ" in (ra["bao"] or [""])[0])


@ca("v528 màn phiếu trả trước (thật): khớp sao kê đi đúng cửa, lưu UNC gửi đúng tệp")
def _man_sk_unc():
	ra = _xem_phieu(PE_893, TT_893, bam="pvKhopSk")
	la("khớp sao kê", ra["sk"], [["NHA-SEN", "APP-26-09-893"]])
	ra = _xem_phieu(PE_893, TT_893, bam="pvLuuUnc", tdk=["/private/files/unc2.jpg"])
	la("lưu UNC", [(m, a) for m, a in ra["api"] if m == "vagabond.duyet_chi.dinh_unc_sau"],
		[("vagabond.duyet_chi.dinh_unc_sau", {"name": "APP-26-09-893", "unc": '["/private/files/unc2.jpg"]'})])
	ra = _xem_phieu(PE_893, TT_893, bam="pvLuuUnc", tdk=[])
	dung("chưa chọn tệp: không gọi máy chủ", not any(m == "vagabond.duyet_chi.dinh_unc_sau" for m, a in ra["api"]))


def _xem_ho_so(dong, q=None, loai="TK cong ty", trang_thai="Da thanh toan", bam=None, hd_sau=None):
	them = r"""
(async function () {
  await ctx.scrHoSoTTView('APP.26.09.010');
  const h = ghi.html[ghi.html.length - 1];
  if (BAM) {
    const nut = { getAttribute: function () { return BAM; } };
    await khung.nghe({ target: { closest: function (s) { return s === '[data-hsv]' ? nut : null; } } });
  }
  process.stdout.write(JSON.stringify({ html: h, api: ghi.api, go: ghi.go.length, bao: ghi.bao }));
})().catch(function (e) { console.error(e && e.stack || e); process.exit(1); });
"""
	d = {"ho_so": {"ma": "APP.26.09.010", "loai": loai, "trang_thai": trang_thai, "tong_tien": 2160000,
		"ten_ncc": "Adecco", "ngay": "2026-09-07", "loai_cp_thue": "Chi phi khong hop le"},
		"quyen": q if q is not None else {"fin": 1},
		"dong": [dict({"noi_dung": "PHI DV", "so_tien": 2160000, "hoa_don": None, "cho_hoa_don": 0,
			"hoa_don_bo_sung": None, "po": [], "pnk": [], "scan": [], "hddt": []}, **x) for x in dong]}
	# v530: máy chủ trả mức phủ và các tờ nối mức hồ sơ (ho_so_tt.chi_tiet).
	# Tính bằng CHÍNH phép thuần của máy chủ để ca không tự bịa số.
	from vagabond.hoa_don_sau import do_phu
	d["hd_sau"] = hd_sau or []
	d["phu_hd_sau"] = do_phu(d["dong"], d["hd_sau"])
	kich = KHUNG_JS.replace("__THEM__", them).replace("TRA(m, a || {})", "(m === 'vagabond.ho_so_tt.chi_tiet' ? D : { ok: 1 })")
	kich = kich.replace("const vm = require('vm');", "const vm = require('vm'); const D = %s; const BAM = %s; const VAI = []; const CHON = null; const TDK = [];" % (
		json.dumps(d), json.dumps(bam)))
	return _node(kich, ["19-ho-so-tt.js"])


# v530 (chị Dung, anh Việt 25/09/2026): hai bước "Đánh dấu hoá đơn đến sau"
# rồi "Nối hóa đơn đến sau" trên TỪNG khoản gộp thành MỘT nút cho cả hồ sơ.
# Chị Dung: "tuỳ cái có nút gợi ý còn có cái không có". Máy chủ tự đánh dấu
# khoản đủ điều kiện lúc nối (noi_nhieu, cùng luật loi_danh_dau_bu của v528).
# Ca v528 cũ chốt hai nút theo khoản nên được viết lại theo luật mới.
@ca("v530 hồ sơ Adecco (màn thật): một nút Nối cho cả hồ sơ, không còn nút theo từng khoản; bấm thì mở danh sách tờ của hồ sơ")
def _man_ho_so():
	ra = _xem_ho_so([{}])
	dung("FIN thấy một nút Nối cho hồ sơ", ra["html"].count('data-hsv="noihds"') == 1)
	dung("không còn nút đánh dấu hay nút nối theo khoản", "ddhd1" not in ra["html"] and "bohd1" not in ra["html"])
	dung("hiện số cần và còn thiếu", "2.160.000" in ra["html"] and "còn thiếu" in ra["html"])
	ra = _xem_ho_so([{"cho_hoa_don": 1}])
	dung("khoản đã đánh dấu: vẫn đúng một nút của hồ sơ", ra["html"].count('data-hsv="noihds"') == 1 and "bohd1" not in ra["html"])
	# Bấm nút rồi chọn tờ: chạy trong hanh_vi/hoa_don_sau_530.js (cần hộp
	# thoại thật và DOM giả, harness ở đây chỉ nạp riêng 19-ho-so-tt.js).
	for mo_ta, kw in (("sales", {"q": {}}), ("hồ sơ huỷ", {"trang_thai": "Huy"}), ("hồ sơ từ chối", {"trang_thai": "Tu choi"})):
		ra = _xem_ho_so([{}], **kw)
		dung(mo_ta + ": không có nút nối", "noihds" not in ra["html"])
	ra = _xem_ho_so([{"hoa_don": "ACC-PINV-1"}])
	dung("khoản đã có hoá đơn gốc: không cần nối, không có nút", "noihds" not in ra["html"])
	ra = _xem_ho_so([{}], hd_sau=[{"hoa_don": "HDM-1", "so_hd_ncc": "5802", "ncc_ten": "Adecco", "tien_khop": 2160000,
		"tong_hd": 2160000, "da_ghi_so": 1, "bu_tru": 2160000, "but_toan": "PKT-9", "nhan": "Đã ghi sổ, đã trả hết", "scan": []}])
	dung("nối đủ: không còn nút nối, báo đủ hoá đơn", "noihds" not in ra["html"] and "đủ hoá đơn" in ra["html"])
	dung("tờ đã nối có nút Gỡ và ghi bút toán bù trừ", 'data-hsv="gohds|HDM-1"' in ra["html"] and "PKT-9" in ra["html"])


# ------------------------------------------------ Codex #370 vòng 1 trên 6e2053d


@ca("v528 Codex #370 F1: phiếu trả trước cấn 12 tờ, còn 7 tờ nháp: ba nút vẫn đứng trước mọi danh sách, danh sách đủ mở theo yêu cầu")
def _f1_danh_sach_dai():
	da_can = [{"hoa_don": "PI-%02d" % i, "tien": 100000} for i in range(12)]
	nhap = [{"name": "PI-NHAP-%d" % i, "bill_no": "N%d" % i} for i in range(7)]
	ra = _xem_phieu(PE_893, dict(TT_893, con_coc=1000, da_can=da_can, nhap=nhap))
	html = ra["html"]
	nut = min(html.index('id="%s"' % x) for x in ("pvKhopSk", "pvLuuUnc", "pvNoiHd"))
	truoc = html[:nut]
	la("trước khối nút: không tờ đã cấn nào, không tờ nháp nào",
		[x for x in ["PI-%02d" % i for i in range(12)] + ["N%d" % i for i in range(7)] if x in truoc], [])
	dung("trước khối nút: có số tờ và tổng tiền đã cấn", "12 tờ" in truoc and "1.200.000" in truoc)
	sau = html[nut:]
	dung("sau khối nút: đủ 12 tờ đã cấn trong phần mở theo yêu cầu",
		"<details" in sau and all("PI-%02d" % i in sau for i in range(12)))
	dung("tờ nháp: rút gọn 3 tờ đầu và số còn lại", "N0, N1, N2" in sau and "và 4 tờ nữa" in sau and "N6" not in sau)
