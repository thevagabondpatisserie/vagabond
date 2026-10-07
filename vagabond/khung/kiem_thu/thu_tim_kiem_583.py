# -*- coding: utf-8 -*-
"""v583: MOT phep tim cho moi o tim trong app (anh Viet 07/10/2026).

Anh Viet: "phai sua o backend cho moi o tim kiem trong app, go co dau, khong
dau, dau phay, cham, ma,... go kieu nao cung phai ra cai mon ay".

Ca that 06/10/2026: De go "chocolatine mini" trong Phieu yeu cau san xuat thi
khong ra "Bánh Chocolatine, Mini size" (BANU00050). Do tren site that cung
ngay: `like '%chocolatine mini%'` ra 0 dong; `like '%duong%'` khong ra
"Đường đen" (co so du lieu coi d va đ la hai chu khac nhau).

Cac ca duoi chay THAT vagabond/tim_kiem.py:
  - bang mau dung chung voi JS (mau_tim/mau_tim_583.json) cho `khop`;
  - `ten_khop` tren mot bang gia lap co phep `like` BAT CHUOC dung collation
    utf8mb4 _ci da do tren site (khong phan biet hoa thuong va dau thanh,
    nhung d khac đ);
  - chot khong con o tim nao tu viet `like '%cum chu%'` nua.
"""

import io
import json
import os
import re
import unicodedata

from vagabond.khung.kiem_thu.nen import ca, dung, la, gia_lap

gia_lap()

from vagabond import tim_kiem as tk  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAU = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
	"mau_tim", "mau_tim_583.json"), encoding="utf-8"))["ca"]


# ------------------------------------------------------------ phep thuan

@ca("v583: chuan hoa bo dau, đ thanh d, bo dau cau, gop dau cach")
def _chuan():
	la("ten mon", tk.chuan("Bánh Chocolatine, Mini size"), "banh chocolatine mini size")
	la("đ hoa thuong", tk.chuan("ĐƯỜNG đen"), "duong den")
	la("dau cau", tk.chuan(" BANU-00050. "), "banu 00050")
	la("rong", tk.chuan(None), "")
	la("tach tu, bo trung", tk.cac_tu("mini  Mini, chocolatine"), ["mini", "chocolatine"])
	la("toi da 8 tu", len(tk.cac_tu("a b c d e f g h i j")), 8)


@ca("v583: bang mau chung voi JS, tung dong ra dung ket qua")
def _bang_mau():
	sai = []
	for chu, go, mong, vi_sao in MAU:
		if tk.khop(chu, go) != mong:
			sai.append("%r / %r (%s)" % (chu, go, vi_sao))
	la("so dong sai", sai, [])
	dung("bang mau du lon", len(MAU) >= 20)


@ca("v583: khop nhan ca danh sach cot, bo qua None")
def _khop_ds():
	dung("ten + ma", tk.khop(["Bánh Chocolatine, Mini size", None, "BANU00050"], "mini banu00050"))
	dung("thieu tu", not tk.khop(["Bánh Chocolatine", "BANU00008"], "mini"))


@ca("v583: mau like co ca bien the đ, tu ngan chi khop dau tieng")
def _mau():
	la("duong", tk.cac_mau("duong"), ["%duong%", "%đuong%"])
	la("khong co d", tk.cac_mau("mini"), ["%mini%"])
	m = tk.cac_mau("o")
	dung("tu ngan bat dau chuoi", "o%" in m)
	dung("tu ngan sau dau cach", "% o%" in m)
	dung("tu ngan khong khop giua tu", "%o%" not in m)
	dung("tran so mau", len(tk.cac_mau("ddddddd")) <= tk.SO_MAU_TOI_DA)


@ca("v583: dieu kien SQL: AND giua tu, OR giua cot, tham so co ten")
def _sql():
	d, t = tk.sql("chocolatine mini", ["i.item_name", "i.name"])
	dung("hai nhom AND", d.count(" and ") == 1)
	dung("cot item_name", "i.item_name like %(tk0_0)s" in d)
	dung("cot name", "i.name like %(tk0_0)s" in d)
	la("tham so", sorted(t.values()), ["%chocolatine%", "%mini%"])
	la("go rong", tk.sql("  ,. ", ["x"]), ("", {}))
	dung("khong noi chuoi go vao cau lenh", "chocolatine" not in d)


@ca("v583: cot tu man hinh chi nhan ten cot that, khong lot SQL")
def _cot():
	la("loc", tk.cot_hop_le(["name", "item_name", "x; drop table", "khong_co", "name"],
		{"name", "item_name"}), ["name", "item_name"])


# ------------------------------------------------- ten_khop tren bang gia lap

def _db(s):
	"""Bat chuoc collation utf8mb4 _ci da do tren site: bo dau thanh, hoa
	thuong, NHUNG giu đ khac d."""
	s = str(s or "").replace("Đ", "đ").lower()
	s = unicodedata.normalize("NFD", s)
	return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "\x01")


def _like(gt, mau):
	rx = "^" + ".*".join(re.escape(_db(p)) for p in mau.split("%")) + "$"
	return re.match(rx, _db(gt), re.S) is not None


class _Bang(object):
	def __init__(self, dong, ma_vach=None):
		self.dong = dong
		self.ma_vach = ma_vach or []
		self.hoi = []

	def get_all(self, dt, filters=None, or_filters=None, fields=None, pluck=None, limit_page_length=0, **k):
		self.hoi.append((dt, filters, or_filters))
		if dt == "Item Barcode":
			mau = filters["barcode"][1]
			return [p for p, b in self.ma_vach if _like(b, mau)]
		ra = []
		for r in self.dong:
			if filters and "name" in filters and r["name"] not in filters["name"][1]:
				continue
			if or_filters and not any(_like(r.get(c), m) for c, _, m in or_filters):
				continue
			ra.append(r)
		if pluck:
			return [r[pluck] for r in ra]
		return [{f: r.get(f) for f in (fields or ["name"])} for r in ra]


MON = [
	{"name": "BANU00050", "item_name": "Bánh Chocolatine, Mini size"},
	{"name": "BANU00008", "item_name": "Bánh Chocolatine, Full size"},
	{"name": "BANU00064", "item_name": "Bông lan Chuối Đường đen"},
	{"name": "NVLT00062", "item_name": "Bột màu xanh dương gốc dầu, NE"},
	{"name": "BAWC00001", "item_name": "Bánh Ổ Roman De La Rose"},
	{"name": "BAWC00002", "item_name": "Bánh Croissant Avocado"},
	{"name": "BAWC00003", "item_name": "Bánh Ống Quế"},
]


def _tim(q, cot=("name", "item_name"), ma_vach=None):
	import unittest.mock as um

	b = _Bang(MON, ma_vach)
	with um.patch.object(tk.frappe, "get_all", b.get_all, create=True):
		return tk.ten_khop("Item", q, list(cot)), b


@ca("v583: ten_khop chay that tren bang gia lap co collation nhu site")
def _ten_khop():
	# Truoc v583, cung bang nay: like '%chocolatine mini%' ra rong.
	cu = [r["name"] for r in MON if _like(r["item_name"], "%chocolatine mini%")]
	la("kieu cu ra rong (tai hien ca De)", cu, [])
	la("chocolatine mini", _tim("chocolatine mini")[0], ["BANU00050"])
	la("mini chocolatine", _tim("mini, chocolatine")[0], ["BANU00050"])
	la("ma co gach", _tim("BANU-00050")[0], ["BANU00050"])
	# Truoc v583: like '%duong%' khong ra Đường đen.
	la("kieu cu duong", [r["name"] for r in MON if _like(r["item_name"], "%duong den%")], [])
	la("duong den", _tim("duong den")[0], ["BANU00064"])
	# "Bánh Ống" qua duoc buoc hoi rong tay ('% o%'), buoc so lai phai loai.
	la("banh o khong ra croissant, khong ra ong", _tim("banh o")[0], ["BAWC00001"])
	la("go rong", _tim("  ")[0], None)


@ca("v583: ten_khop hoi tu dai truoc, luot sau chi hoi trong tap da khop")
def _ten_khop_hoi():
	ra, b = _tim("chocolatine mini")
	b.hoi = [h for h in b.hoi if h[0] == "Item"]
	la("hai luot", len(b.hoi), 2)
	la("luot dau khong gioi han", b.hoi[0][1], None)
	dung("luot hai trong tap da khop", b.hoi[1][1] == {"name": ["in", ["BANU00008", "BANU00050"]]})
	dung("luot dau la tu dai nhat", any("chocolatine" in str(m) for _, _, m in b.hoi[0][2]))


@ca("v583: go ma vach cung ra mon")
def _ma_vach():
	ra, _ = _tim("2000000000507", ma_vach=[("BANU00050", "2000000000507")])
	la("ra mon theo ma vach", ra, ["BANU00050"])


@ca("v583: them_loc ghep vao dict va list, go rong khong them gi")
def _them_loc():
	import unittest.mock as um

	with um.patch.object(tk, "ten_khop", lambda dt, q, cot, gioi_han=2000: ["A"] if tk.cac_tu(q) else None):
		la("dict", tk.them_loc({"disabled": 0}, "Item", "x", ["name"]),
			[["disabled", "=", 0], ["name", "in", ["A"]]])
		la("list", tk.them_loc([["a", "=", 1]], "Item", "x", ["name"]),
			[["a", "=", 1], ["name", "in", ["A"]]])
		la("rong", tk.them_loc({"a": 1}, "Item", "", ["name"]), {"a": 1})
		la("dict co dieu kien", tk.them_loc({"x": ["in", [1]]}, "Item", "x", ["name"]),
			[["x", "in", [1]], ["name", "in", ["A"]]])
	with um.patch.object(tk, "ten_khop", lambda *a, **k: []):
		la("khong khop gi thi loc ra rong", tk.loc_ten("Item", "x", ["name"]), ["name", "in", ["\x00khong-co"]])


class _Df(object):
	def __init__(self, fieldname, fieldtype="Data", permlevel=0):
		self.fieldname, self.fieldtype, self.permlevel = fieldname, fieldtype, permlevel


@ca("v583: cua tim tu man hinh: chi o chu quyen cap 0, van qua get_list soat quyen")
def _cua_tim():
	import unittest.mock as um

	meta = type("M", (), {"fields": [_Df("item_name"), _Df("mat_khau", "Password"),
		_Df("gia_von", "Data", 1), _Df("ghi_chu", "Text")], "title_field": "item_name", "search_fields": ""})()
	hoi = {}

	def _ten_khop(dt, q, cot, gioi_han=2000):
		hoi["cot"] = cot
		return ["BANU00050"]

	def _get_list(dt, **k):
		hoi["get_list"] = (dt, k)
		return [{"name": "BANU00050"}]

	with um.patch.object(tk.frappe, "get_meta", lambda dt: meta, create=True), \
			um.patch.object(tk.frappe, "get_list", _get_list, create=True), \
			um.patch.object(tk, "ten_khop", _ten_khop):
		ra = tk.tim("Item", "chocolatine mini", '["item_name", "mat_khau", "gia_von", "x;drop"]',
			'["name"]', '{"disabled": 0}', 50, "item_name")
	la("ket qua", ra, [{"name": "BANU00050"}])
	la("chi giu o chu quyen cap 0", hoi["cot"], ["item_name"])
	dt, k = hoi["get_list"]
	la("doc qua get_list co soat quyen", dt, "Item")
	la("giu bo loc va them ten khop", k["filters"], [["disabled", "=", 0], ["name", "in", ["BANU00050"]]])
	la("so dong", k["limit_page_length"], 50)


# ------------------------------------------------------ chot: mot nguon

_O_TIM_PY = re.compile(r'\["like",\s*"%"\s*\+\s*(q|tim|tu|tu_khoa|tk)\b|"%%%s%%"\s*%\s*(q|tim|tu|tu_khoa)\b')


@ca("v583: khong con o tim may chu nao tu viet like '%cum chu%'")
def _chot_py():
	# Nhung cho con lai dung `like` voi chuoi go la so khop NOI BO (ma so thue,
	# so dien thoai danh ba, mo ta giao dich), khong phai o tim nguoi dung go.
	bo_qua = {
		"doi_soat_hddt_ra.py",  # loc_tim_don: giu kieu cu, da them luot tim_kiem
		"doi_soat_vendor.py",  # tep cua phien dang lam #420/#450, bao lai ho
	}
	hong = []
	for goc_, _, tep in os.walk(GOC):
		if "kiem_thu" in goc_ or "kiem_that" in goc_ or "bench_thu" in goc_:
			continue
		for t in tep:
			if not t.endswith(".py") or t in bo_qua or t == "tim_kiem.py":
				continue
			s = io.open(os.path.join(goc_, t), encoding="utf-8").read()
			for i, dong in enumerate(s.splitlines(), 1):
				if _O_TIM_PY.search(dong):
					hong.append("%s:%d" % (t, i))
	la("o tim tu viet like", hong, [])


@ca("v583: khong con o tim may khach nao tu viet or_filters like hay indexOf cum chu")
def _chot_js():
	bep = os.path.join(GOC, "public", "js", "bep")
	hong = []
	for t in sorted(os.listdir(bep)):
		if not t.endswith(".js"):
			continue
		s = io.open(os.path.join(bep, t), encoding="utf-8").read()
		for i, dong in enumerate(s.splitlines(), 1):
			if re.search(r"or_filters\s*[:=]\s*\{[^}]*'like'", dong):
				hong.append("%s:%d or_filters" % (t, i))
			# 05-san-xuat mfgWhOpts loc KHO theo bep (baker/pastry/lab), khong
			# phai o tim nguoi dung go.
			if "String(o.value).toLowerCase().indexOf(tu)" in dong:
				continue
			if re.search(r"\.toLowerCase\(\)\.indexOf\((q|q0|k|tim|tu)\)", dong):
				hong.append("%s:%d indexOf" % (t, i))
	la("o tim tu viet", hong, [])


@ca("v583: Phieu yeu cau san xuat tim qua may chu bang timList")
def _ycsx():
	s = io.open(os.path.join(GOC, "public", "js", "bep", "04-tao-phieu.js"), encoding="utf-8").read()
	i = s.index("async function drawPick(")
	than = s[i:s.index("\n}\n", i)]
	dung("goi timList", "timList('Item', qs, ['name', 'item_name'], ar)" in than)
	dung("loc tai cho bang vgbKhop", "vgbKhop([it.item_name, it.name], q)" in than)
