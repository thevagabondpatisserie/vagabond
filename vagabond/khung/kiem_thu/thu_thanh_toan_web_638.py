# -*- coding: utf-8 -*-
"""v638: khách đặt bánh trên web thanh toán NGAY trên web (anh Việt 04/11/2026).

Bốn cách: tiền mặt khi nhận, thẻ quốc tế và thẻ ATM nội địa qua OnePay, chuyển
khoản VietQR máy tự xác nhận khi SePay báo tiền về. Ca chạm hệ chạy HÀM THẬT
(thanh_toan_web.khop_ck, ghi_nhan_the, tao_gd, ghi_pancake; onepay.ghi_nhan;
ban_hang._soat_sepay; don_hang.tao_don; trang_khach.bien_nhan_html), chỉ thay
tầng Frappe bằng bản giả ghi lại lời gọi. Phần chạy trên trình duyệt (bước đặt
bánh, biên nhận Vue) nạp thật trong node ở hanh_vi/thanh_toan_web_638.mjs.
"""

import contextlib
import json
import re
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if not hasattr(_fr.utils, "get_url"):
	_fr.utils.get_url = lambda *a, **k: "https://vagabond.test"
if not hasattr(_fr.utils, "get_url_to_form"):
	_fr.utils.get_url_to_form = lambda dt, ten: "https://vagabond.test/app/%s/%s" % (dt, ten)
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import kenh_zalo as kz  # noqa: E402
from vagabond import onepay as op  # noqa: E402
from vagabond import thanh_toan_web as tw  # noqa: E402
from vagabond import thanh_toan_web_thuan as ttt  # noqa: E402
from vagabond import don_web, trang_khach  # noqa: E402
from vagabond.khung.kiem_thu.thu_su_co_290 import D, nap  # noqa: E402

GOC = Path(__file__).resolve().parents[3]
KHOA = "0123456789ABCDEF0123456789ABCDEF"
C = {"bat": 1, "cong": "https://mtf.onepay.vn/paygate/vpcpay.op", "merchant": "VAGABONDWEB", "access_code": "ABCD1234",
	"hash_code": KHOA, "query_user": "op01", "query_password": "mk"}
TEN = "DW-2611-00123"
MA = "DW261100123"


def _phi(tt, phi_khach=None):
	return {"trang_thai": tt, "phi_khach": phi_khach}


# ------------------------------------------------------------------ phần thuần

@ca("v638 số tiền thu online: phí đã rõ là đủ tổng (kể cả tự lấy, miễn phí); phí chưa rõ chỉ tiền bánh sau ưu đãi, phí giao trả khi nhận")
def _so_tien():
	la("đủ: tiền bánh + phí", ttt.tien_don(900000, 0, _phi("chinh_xac", 36000))["online"], 936000)
	la("ưu đãi trừ trước", ttt.tien_don(900000, 100000, _phi("chinh_xac", 36000))["online"], 836000)
	la("miễn phí giao", ttt.tien_don(1200000, 0, _phi("mien_phi"))["online"], 1200000)
	la("tự lấy", ttt.tien_don(650000, 0, _phi("tu_lay"))["online"], 650000)
	ro = ttt.tien_don(900000, 100000, _phi("chua_ro"))
	la("phí chưa rõ: chỉ tiền bánh sau ưu đãi", (ro["online"], ro["tong"], ro["phi_sau"]), (800000, None, True))
	la("chính xác mà phí 0 coi như chưa rõ", ttt.tien_don(500000, 0, _phi("chinh_xac", 0))["phi_sau"], True)
	la("ưu đãi lớn hơn tiền bánh không âm", ttt.tien_don(100000, 500000, _phi("tu_lay"))["online"], 0)
	b = {"tien_banh": 900000, "trang_thai_phi": "chua_ro"}
	snap = {"phi": {"trang_thai": "chua_ro", "phi_khach": None}, "uu_dai": {"giam": 50000}}
	la("đọc từ bản ghi + ảnh chụp", ttt.so_tien_online(b, snap), 850000)
	# Biên nhận đọc CÙNG phép tính: tổng biên nhận và số thu online không lệch nhau.
	tt = don_web.tom_tat_bien_nhan(dict(b, name=TEN, trang_thai="Da nhan", thanh_toan="bank"), snap)
	la("biên nhận: tổng chờ phí, khối thanh toán đòi tiền bánh", (tt["tong"], tt["tt"]["so"], tt["tt"]["phi_sau"]),
		("Chờ Sales báo phí giao", 850000, True))
	snap2 = {"phi": {"trang_thai": "chinh_xac", "phi_khach": 36000}}
	tt2 = don_web.tom_tat_bien_nhan(dict(b, name=TEN, trang_thai="Da nhan", trang_thai_phi="chinh_xac", thanh_toan="bank"), snap2)
	la("biên nhận: tổng và số thu online cùng một số", (tt2["tong"], tt2["tt"]["so_chu"]), ("936.000 đ", "936.000 đ"))


@ca("v638 không chỗ nào tự tính số tiền đơn web: biên nhận, thu online, cổng thẻ, đối soát đều qua thanh_toan_web_thuan.tien_don")
def _mot_nguon():
	for tep in ("vagabond/don_web.py", "vagabond/thanh_toan_web.py", "vagabond/trang_khach.py", "vagabond/public/web_vue/trang/app.js"):
		s = (GOC / tep).read_text()
		dung(tep + " không tự cộng phí giao vào tiền sau giảm", not re.search(r"sau_giam\s*\+", s))
		dung(tep + " không tự trừ ưu đãi khỏi tiền bánh", not re.search(r"tien_banh\s*-\s*giam", s))
	tw_s = (GOC / "vagabond/thanh_toan_web.py").read_text()
	dung("cổng thẻ, khớp sao kê đọc so_tien_online", tw_s.count("ttt.so_tien_online(") >= 4)
	dung("biên nhận đọc tien_ban_ghi", "ttt.tien_ban_ghi(ban_ghi, snap)" in (GOC / "vagabond/don_web.py").read_text())
	thuan = (GOC / "vagabond/thanh_toan_web_thuan.py").read_text()
	la("chỉ một chỗ cộng phí giao", len(re.findall(r"sau_giam\s*\+\s*phi_khach", thuan)), 1)


@ca("v638 cách thanh toán: bốn giá trị máy chủ nhận; giá trị lạ, rỗng, viết hoa lạ về chuyển khoản; cổng thẻ tắt thì hai cách thẻ về chuyển khoản")
def _pt():
	la("bốn giá trị", [ttt.chuan_pt(x) for x in ("bank", "card", "atm", "cash")], ["bank", "card", "atm", "cash"])
	la("giá trị lạ", [ttt.chuan_pt(x) for x in ("", None, "momo", "<b>", 5, "CASH ")], ["bank"] * 5 + ["cash"])
	la("cổng tắt", [ttt.chuan_pt(x, the_dung=False) for x in ("card", "atm", "cash", "bank")], ["bank", "bank", "cash", "bank"])
	la("vpc_CardList", (ttt.CARD_LIST["card"], ttt.CARD_LIST["atm"]), ("INTERNATIONAL", "DOMESTIC"))
	la("nhãn biên nhận một nguồn với trang cũ", [trang_khach.GIA_TRI_BIEN_NHAN[ttt.nhan_pt(x)][0] for x in ttt.PT_HOP_LE],
		["bien_nhan_chuyen_khoan", "bien_nhan_the_qt", "bien_nhan_the_atm", "bien_nhan_tien_mat"])
	la("TEN_THANH_TOAN của đơn web là bảng này", don_web.TEN_THANH_TOAN, {k: v[0] for k, v in ttt.NHAN_PT.items()})
	nhan = json.loads((GOC / "vagabond/public/web_order/chu-mac-dinh.json").read_text())
	for chu, khoa in ttt.NHAN_PT.values():
		la("sổ nhãn có " + khoa, nhan[khoa]["mac_dinh"], chu)


@ca("v638 mã giới thiệu: chỉ giữ chữ số, 8 đến 12 số; sai thì bỏ")
def _gioi_thieu():
	la("chuẩn", [ttt.chuan_gioi_thieu(x) for x in ("0909 123 456", "+84-909-123-456", "1234567", "1234567890123", "", None, "abc12345678")],
		["0909123456", "84909123456", "", "", "", "", "12345678"])


@ca("v638 nội dung chuyển khoản là chuỗi ban_hang._sepay_theo_don đã nhận: S<shop>O<mã>T cho mã số, mã chữ đứng riêng; luôn kèm mã Don Web")
def _noi_dung():
	la("mã số", ttt.noi_dung_ck("67355", TEN, "91853"), "S67355O91853T " + MA)
	la("mã chữ", ttt.noi_dung_ck("67355", TEN, "woo2749"), "WOO2749 " + MA)
	la("chưa có mã Pancake", ttt.noi_dung_ck("67355", TEN, ""), MA)
	la("biểu thức sơ lọc", ttt.mau_khop("67355", TEN, "91853"), "S67355O91853T|" + MA)
	# Đúng mạch mà bộ khớp sẵn có tìm: cùng biểu thức như ban_hang._sepay_theo_don.
	re_don = re.compile(r"S%sO(\d+)T" % re.escape("67355"), re.I)
	la("bộ khớp cũ đọc ra đúng mã đơn", re_don.search(ttt.noi_dung_ck("67355", TEN, "91853")).group(1), "91853")
	dung("nội dung ngắn, chỉ chữ số in hoa và khoảng trắng (VietQR)", re.fullmatch(r"[A-Z0-9 ]{1,60}", ttt.noi_dung_ck("67355", TEN, "91853")))


@ca("v638 khớp sao kê: đúng đơn; không ăn nhầm đơn khác (91853 vs 9185, DW...123 vs DW...1234); tiền ra không tính; mỗi dòng một lần")
def _khop():
	gds = [
		{"name": "BT-1", "description": "NGUYEN VAN A S67355O91853T DW261100123", "deposit": 500000, "reference_number": "FT1"},
		{"name": "BT-1", "description": "NGUYEN VAN A S67355O91853T DW261100123", "deposit": 500000},
		{"name": "BT-2", "description": "chuyen DW261100123", "deposit": 300000, "reference_number": "FT2"},
		{"name": "BT-3", "description": "S67355O9185T", "deposit": 999000},
		{"name": "BT-4", "description": "DW2611001234", "deposit": 999000},
		{"name": "BT-5", "description": "DW261100124", "deposit": 999000},
		{"name": "BT-6", "description": "S67355O91853T hoan", "deposit": 0, "withdrawal": 200000},
		{"name": "BT-7", "description": "s67355o91853t ck lan 2", "deposit": 100000},
	]
	kq = ttt.tong_khop(gds, "67355", TEN, "91853")
	la("dòng đúng đơn", [g["gd"] for g in kq["gd"]], ["BT-1", "BT-2", "BT-7"])
	la("tổng", kq["nhan"], 900000.0)
	la("mã tham chiếu giữ để điền hoá đơn", kq["gd"][0]["ma"], "FT1")
	la("thiếu tiền không báo đủ", ttt.xet_thu(936000, 900000), ttt.TT_THIEU)
	la("đủ (lệch dưới 1 đồng)", ttt.xet_thu(900000, 899999.5), ttt.TT_DA_THU)
	la("chưa có gì", ttt.xet_thu(900000, 0), "")
	la("số cần 0 không bao giờ đủ", ttt.xet_thu(0, 0), "")


# --------------------------------------------------------- frappe giả, Don Web

class _Db:
	"""frappe.db giả: một bảng Vagabond Don Web và một bảng sao kê."""

	def __init__(self, ban_ghi=None, sao_ke=None):
		self.dw = {}
		for b in ban_ghi or []:
			self.dw[b["name"]] = dict(b)
		self.sao_ke = list(sao_ke or [])
		self.sql_goi = []
		self.commit_n = 0
		self.khoa = []

	def _tim(self, loc):
		for ten, r in self.dw.items():
			ok = True
			for k, v in loc.items():
				if isinstance(v, list) and v and v[0] == "in":
					ok = ok and r.get(k) in v[1]
				else:
					ok = ok and r.get(k) == v
			if ok:
				return ten
		return None

	def get_value(self, dt, ten, o=None, as_dict=False, for_update=False, **kw):
		if dt != tw.DT:
			return None
		if isinstance(ten, dict):
			ten = self._tim(ten)
			if o == "name":
				return ten
		if ten not in self.dw:
			return None
		if for_update:
			self.khoa.append(ten)
		r = self.dw[ten]
		if isinstance(o, (list, tuple)):
			return D({k: r.get(k) for k in o}) if as_dict else [r.get(k) for k in o]
		return r.get(o)

	def exists(self, dt, ten=None, **kw):
		return dt == tw.DT and ten in self.dw

	def set_value(self, dt, ten, o, v=None, **kw):
		self.dw[ten].update(o if isinstance(o, dict) else {o: v})

	def sql(self, cau, tham=None, as_dict=False, **kw):
		self.sql_goi.append((cau, tham))
		if "for update" in cau:
			self.khoa.append(tham[0])
			return []
		if "vgb_tt_ma_gd like" in cau:
			can = tham[1].strip("%")
			return [[ten] for ten, r in self.dw.items() if ten != tham[0] and can in (r.get("vgb_tt_ma_gd") or "")][:1]
		if "Bank Transaction" in cau:
			mau = re.compile(tham[1], re.I)
			return [D(g) for g in self.sao_ke if g.get("deposit", 0) > 0 and mau.search(g.get("description") or "")]
		return []

	def commit(self):
		self.commit_n += 1

	def rollback(self, **kw):
		pass


def _dw(**them):
	r = {"name": TEN, "trang_thai": "Da nhan", "thanh_toan": "bank", "tien_banh": 900000, "trang_thai_phi": "chinh_xac",
		"snapshot": json.dumps({"phi": {"trang_thai": "chinh_xac", "phi_khach": 36000},
			"nguoi_dat": {"ho_ten": "Nguyễn Văn An", "dien_thoai": "0931224334"}}),
		"creation": __import__("datetime").datetime(2026, 11, 4, 9, 0), "pancake_id": "91853", "pancake_display_id": "91853",
		"vgb_tt_trang_thai": None, "vgb_tt_da_thu": 0, "vgb_tt_luc": None, "vgb_tt_cach": None, "vgb_tt_ma_gd": None,
		"vgb_tt_pancake": None, "vgb_tt_bao_luc": None, tw.O_NK: None, "token_hash": don_web.bam("T" * 43)}
	r.update(them)
	return r


def _vat(dbg, bao=None, pancake=None, onepay_dung=True):
	"""Thay tầng Frappe cho thanh_toan_web. `bao` ghi tin Zalo; `pancake` thay ghi_pancake."""
	bao = bao if bao is not None else []
	ds = [patch.object(_fr, "db", dbg), patch.object(tw, "_shop", lambda: "67355"),
		patch.object(op, "cau_hinh", return_value=dict(C, bat=1 if onepay_dung else 0)),
		patch.object(op, "_bi_mat", lambda: "bi-mat-site"),
		patch.object(kz, "bao", lambda *a, **k: bao.append((a, k)) or ["ZL-1"]),
		patch.object(tw, "ghi_pancake", pancake or (lambda d: "da_ghi"))]
	return ds


def _bh():
	"""Các hàm THẬT của ban_hang.py nạp riêng (ban_hang kéo requests ở đầu tệp nên
	bộ kiểm tầng khung không import cả mô đun)."""
	from vagabond import pt_thanh_toan

	g = dict(frappe=_fr, re=re, flt=_fr.utils.flt, pt_thanh_toan=pt_thanh_toan,
		cfg=lambda: D(pancake_shop_id="67355"), _sepay_theo_don=lambda shop, ma: {})
	for ten in ("_tien", "_ck_don_web", "_pt_don_web", "_soat_sepay", "_chuan_ma_tham_chieu"):
		nap("ban_hang.py", ten, g)
	return types.SimpleNamespace(**{k: g[k] for k in ("_ck_don_web", "_pt_don_web", "_soat_sepay", "_chuan_ma_tham_chieu")})


def _chay(vat, ham):
	with contextlib.ExitStack() as st:
		for v in vat:
			st.enter_context(v)
		return ham()


@ca("v638 chuyển khoản: khớp đúng đơn thì ghi đã thu, số, cách, mã giao dịch lên Don Web; báo Sales MỘT lần; khớp lặp không ghi hai lần")
def _khop_ck():
	sk = [{"name": "BT-9", "description": "S67355O91853T DW261100123", "deposit": 936000, "reference_number": "FT9"},
		{"name": "BT-8", "description": "S67355O91854T", "deposit": 936000}]
	dbg = _Db([_dw()], sk)
	bao, pc = [], []
	vat = _vat(dbg, bao, pancake=lambda d: pc.append(d["name"]) or "da_ghi")
	r1 = _chay(vat, lambda: tw.khop_ck(TEN))
	r2 = _chay(vat, lambda: tw.khop_ck(TEN))
	d = dbg.dw[TEN]
	la("trạng thái", (r1, r2), (ttt.TT_DA_THU, ""))
	la("ô Don Web", (d["vgb_tt_trang_thai"], d["vgb_tt_da_thu"], d["vgb_tt_cach"]), ("Da thu", 936000.0, "Chuyển khoản"))
	la("giao dịch ghi nhận", [g["gd"] for g in json.loads(d["vgb_tt_ma_gd"])], ["BT-9"])
	la("ghi Pancake một lần", pc, [TEN])
	la("báo Sales một lần, đúng mã tin", [x[1].get("ma_tin") for x in bao], ["bh_don_web_da_tra"])
	dung("đọc Don Web trong khoá hàng", TEN in dbg.khoa)
	dung("KHÔNG đụng ô máy ghi lúc gửi đơn (KHONG_DOI)", not set(dbg.dw[TEN]) - set(_dw()) and
		all(dbg.dw[TEN][o] == _dw()[o] for o in don_web.KHONG_DOI if o in _dw()))


@ca("Codex PR #541: một giao dịch mang mã hai đơn web thì KHÔNG đơn nào tự thành đã thu, báo Sales đối soát tay một lần; giao dịch đơn khác đã ghi nhận thì không cộng lần hai")
def _ck_nhieu_don():
	ten2 = "DW-2611-00124"
	# Đúng chuỗi Codex: một lần chuyển 936.000 đ nội dung "DW261100123 DW261100124", hai đơn cùng 936.000 đ.
	sk = [{"name": "BT-50", "description": "DW261100123 DW261100124", "deposit": 936000}]
	dbg = _Db([_dw(), _dw(name=ten2, pancake_id="91854", pancake_display_id="91854")], sk)
	bao, pc = [], []
	vat = _vat(dbg, bao, pancake=lambda d: pc.append(d["name"]) or "da_ghi")
	r = (_chay(vat, lambda: tw.khop_ck(TEN)), _chay(vat, lambda: tw.khop_ck(ten2)))
	la("không đơn nào ghi đã thu", (r, dbg.dw[TEN]["vgb_tt_trang_thai"], dbg.dw[ten2]["vgb_tt_trang_thai"]), (("", ""), None, None))
	la("không giảm COD Pancake", pc, [])
	_chay(vat, lambda: tw.khop_ck(TEN))
	tin = [(a[0], a[2], k.get("ma_tin"), k.get("khoa")) for a, k in bao]
	# Lượt quét lặp gửi lại cùng khoá; kenh_zalo.bao chống trùng theo khoá nên Sales nhận một lần.
	la("báo Sales đối soát tay, mỗi đơn một khoá", sorted(set(x[3] for x in tin)),
		sorted({"don-web-ck-nhieu-don:%s:BT-50" % TEN, "don-web-ck-nhieu-don:%s:BT-50" % ten2}))
	dung("tin cảnh báo đúng mã tin, nêu mã đơn kia", all(x[0] == "canh_bao" and x[2] == "bh_don_web_da_tra" for x in tin)
		and any("DW261100124" in " ".join(a[3]) for a, k in bao))
	dung("tin không có số tiền", not any(kz.MAU_TIEN.search(x) for a, k in bao for x in [a[2]] + list(a[3])))
	# Nội dung đúng của chính đơn (VietQR in cả S..O..T lẫn mã Don Web của nó) vẫn khớp như cũ.
	la("nội dung VietQR của đơn không bị coi là nhiều đơn", ttt.ma_don_khac(ttt.noi_dung_ck("67355", TEN, "91853"), "67355", TEN, "91853"), [])
	la("mạch S..O..T của đơn khác", ttt.ma_don_khac("S67355O91853T S67355O91854T", "67355", TEN, "91853"), ["S67355O91854T"])
	# Giao dịch đã nằm trong Don Web khác: không cộng lần hai, có giữ khoá dòng sao kê.
	dbg2 = _Db([_dw(vgb_tt_ma_gd=None), _dw(name=ten2, vgb_tt_trang_thai="Da thu",
		vgb_tt_ma_gd=json.dumps([{"gd": "BT-60", "ma": "", "so": 936000, "loai": "ck"}]))],
		[{"name": "BT-60", "description": "S67355O91853T", "deposit": 936000}])
	la("giao dịch đơn khác đã giữ: không ghi đã thu", (_chay(_vat(dbg2), lambda: tw.khop_ck(TEN)), dbg2.dw[TEN]["vgb_tt_trang_thai"]), ("", None))
	dung("khoá dòng sao kê trước khi đọc", "BT-60" in dbg2.khoa)


@ca("v638 chuyển khoản thiếu tiền: ghi 'thu thiếu', KHÔNG báo đủ, không báo Sales; đơn khác không bị khớp; đơn tiền mặt không quét")
def _ck_thieu():
	dbg = _Db([_dw()], [{"name": "BT-1", "description": "DW261100123", "deposit": 500000}])
	bao = []
	r = _chay(_vat(dbg, bao), lambda: tw.khop_ck(TEN))
	la("thiếu", (r, dbg.dw[TEN]["vgb_tt_trang_thai"], dbg.dw[TEN]["vgb_tt_da_thu"]), (ttt.TT_THIEU, "Thu thieu", 500000.0))
	la("không báo", bao, [])
	dbg2 = _Db([_dw(name="DW-2611-00124")], [{"name": "BT-1", "description": "DW261100123", "deposit": 936000}])
	_chay(_vat(dbg2, bao), lambda: tw.khop_ck("DW-2611-00124"))
	la("đơn khác không nhận tiền của đơn này", dbg2.dw["DW-2611-00124"]["vgb_tt_trang_thai"], None)
	dbg3 = _Db([_dw(thanh_toan="cash")], [{"name": "BT-1", "description": "DW261100123", "deposit": 936000}])
	la("tiền mặt: không khớp", _chay(_vat(dbg3), lambda: tw.khop_ck(TEN)), "")
	la("tiền mặt: không đọc sao kê", dbg3.sql_goi, [])
	dbg4 = _Db([_dw(trang_thai="Da huy")], [{"name": "BT-1", "description": "DW261100123", "deposit": 936000}])
	la("đơn huỷ: không ghi đã thu", _chay(_vat(dbg4), lambda: tw.khop_ck(TEN)), "")


@ca("v638 phí giao chưa rõ: thu online là tiền bánh; đủ tiền bánh là 'đã thu', hoá đơn KHÔNG tự đặt Chuyển khoản cả đơn (phí giao thu khi nhận)")
def _phi_sau():
	snap = json.dumps({"phi": {"trang_thai": "chua_ro", "phi_khach": None}})
	dbg = _Db([_dw(snapshot=snap, trang_thai_phi="chua_ro")], [{"name": "BT-1", "description": "S67355O91853T", "deposit": 900000}])
	_chay(_vat(dbg), lambda: tw.khop_ck(TEN))
	la("đã thu tiền bánh", dbg.dw[TEN]["vgb_tt_trang_thai"], ttt.TT_DA_THU)
	pt = _chay(_vat(dbg), lambda: tw.pt_hoa_don("91853", "91853"))
	la("hoá đơn để Sales chọn (nhiều cách trả)", pt, ("", ""))
	tieu, dong = ttt.tin_da_tra(TEN, "91853", "Chuyển khoản", True, "da_ghi")
	dung("tin nói phí giao trả khi nhận", any("phí giao khách trả khi nhận" in x for x in dong))


@ca("v638 biên nhận: khối thanh toán theo cách; chuyển khoản có VietQR đúng số còn lại, nội dung khớp đơn; thẻ có khoá trang; cổng tắt thì cho chuyển khoản")
def _khoi():
	import vagabond
	from vagabond import qr_chuyen_khoan, tai_khoan

	# cong_no kéo ban_hang (requests ở đầu tệp): CI tay không không nạp được, chỉ cần bảng tên ngân hàng.
	cong_no = types.SimpleNamespace(TEN_NGAN_HANG_DAY_DU={"MB": "Ngân hàng TMCP Quân đội (MB Bank)"})
	tk = {"bank": "MB", "bin": "970422", "stk": "0931224334", "ten": "CONG TY TNHH PATISSERIE VAGABOND"}
	ve = []
	with patch.object(tai_khoan, "tk_cho", lambda *a, **k: dict(tk)), \
			patch.dict(sys.modules, {"vagabond.cong_no": cong_no}), patch.object(vagabond, "cong_no", cong_no, create=True), \
			patch.object(qr_chuyen_khoan, "anh_qr", lambda t, so, nd: ve.append((so, nd)) or "data:image/svg+xml;base64,QUJD"):
		k = _chay(_vat(_Db([_dw()])), lambda: tw.khoi_thanh_toan(_dw()))
		la("chuyển khoản", (k["trang_thai"], k["con"], k["ck"]["noi_dung"], k["ck"]["stk"]), ("cho", 936000, "S67355O91853T " + MA, tk["stk"]))
		la("vẽ QR đúng số, đúng nội dung", ve[-1], (936000, "S67355O91853T " + MA))
		la("tên ngân hàng đầy đủ", k["ck"]["ngan_hang"], "Ngân hàng TMCP Quân đội (MB Bank)")
		dung("không lộ tên, số điện thoại khách", "0931224334" not in json.dumps({x: y for x, y in k.items() if x != "ck"}))
		thieu = _chay(_vat(_Db()), lambda: tw.khoi_thanh_toan(_dw(vgb_tt_trang_thai="Thu thieu", vgb_tt_da_thu=500000)))
		la("thu thiếu: QR số còn lại", (thieu["trang_thai"], thieu["con"], ve[-1][0]), ("thieu", 436000, 436000))
		the = _chay(_vat(_Db()), lambda: tw.khoi_thanh_toan(_dw(thanh_toan="atm")))
		la("thẻ: mã và khoá trang, không QR", (the["the"]["ma"], len(the["the"]["k"]), "ck" in the), (MA, 16, False))
		la("thẻ: đường trang thẻ", the["the"]["duong"], "/tra-the/%s?k=%s" % (MA, the["the"]["k"]))
		tat = _chay(_vat(_Db(), onepay_dung=False), lambda: tw.khoi_thanh_toan(_dw(thanh_toan="card")))
		la("cổng tắt: không nút thẻ, có chuyển khoản", ("the" in tat, tat.get("the_tat"), bool(tat.get("ck"))), (False, 1, True))
	tm = _chay(_vat(_Db()), lambda: tw.khoi_thanh_toan(_dw(thanh_toan="cash")))
	la("tiền mặt", (tm["trang_thai"], "ck" in tm, "the" in tm, tm["phi_sau"]), ("tien_mat", False, False, False))
	da = _chay(_vat(_Db()), lambda: tw.khoi_thanh_toan(_dw(vgb_tt_trang_thai="Da thu", vgb_tt_da_thu=936000, vgb_tt_cach="OnePay")))
	la("đã thu", (da["trang_thai"], da["da_thu_chu"], da["cach_thu"], "ck" in da), ("da_thu", "936.000 đ", "Thẻ qua OnePay", False))
	huy = _chay(_vat(_Db()), lambda: tw.khoi_thanh_toan(_dw(trang_thai="Da huy")))
	la("đơn huỷ không đòi tiền", huy["trang_thai"], "huy")


@ca("v638 biên nhận trang cũ: thay câu 'chưa thu tiền' bằng khối thanh toán; QR chỉ nhận ảnh data SVG; nút thẻ sang trang thẻ của tiệm; nút Zalo giữ làm phụ")
def _trang_cu():
	ck = {"ngan_hang": "MB Bank", "stk": "0931224334", "ten": "VAGABOND", "noi_dung": "S67355O91853T " + MA,
		"anh": "data:image/svg+xml;base64,QUJD"}
	tt = {"ma": TEN, "cach_nhan": "Giao tận nơi", "thanh_toan": "Chuyển khoản (mã VietQR)", "tong": "936.000 đ",
		"tt": {"cach": "bank", "trang_thai": "cho", "so": 936000, "so_chu": "936.000 đ", "con": 936000, "con_chu": "936.000 đ", "ck": ck}}
	lh = {"zalo": "https://zalo.me/thevagabondsaigon"}
	html = trang_khach.bien_nhan_html(tt, lh)
	dung("không còn câu chưa thu tiền", "chưa thu tiền" not in html and "bien_nhan_0ea4a5a10" not in html)
	dung("có QR", '<img class="bn-tt-qr" src="data:image/svg+xml;base64,QUJD"' in html)
	dung("có nội dung chuyển khoản", "S67355O91853T " + MA in html)
	dung("nút Zalo vẫn có, đứng sau câu hỗ trợ", html.index("bien_nhan_tt_ho_tro") < html.index("zalo.me"))
	ban = trang_khach.bien_nhan_html(dict(tt, tt=dict(tt["tt"], ck=dict(ck, anh='x" onerror="alert(1)'))), lh)
	dung("ảnh lạ không vào thẻ img", "onerror" not in ban and "bn-tt-qr" not in ban)
	the = trang_khach.bien_nhan_html(dict(tt, tt={"cach": "card", "trang_thai": "cho", "con_chu": "936.000 đ",
		"the": {"ma": MA, "k": "a" * 16, "duong": "/tra-the/%s?k=%s" % (MA, "a" * 16)}}), lh)
	dung("thẻ: nút sang trang thẻ", 'href="/tra-the/%s?k=%s"' % (MA, "a" * 16) in the and "bn-tt-qr" not in the)
	tm = trang_khach.bien_nhan_html(dict(tt, tt={"cach": "cash", "trang_thai": "tien_mat"}), lh)
	dung("tiền mặt: một câu, không QR", "thanh toán tiền mặt khi nhận bánh" in tm and "bn-tt-qr" not in tm)
	da = trang_khach.bien_nhan_html(dict(tt, tt={"cach": "bank", "trang_thai": "da_thu", "da_thu_chu": "936.000 đ", "cach_thu": "Chuyển khoản"}), lh)
	dung("đã thu", "Đã nhận tiền" in da and "936.000 đ · Chuyển khoản" in da and "bn-tt-qr" not in da)
	cu = trang_khach.bien_nhan_html({"ma": TEN}, lh)
	dung("biên nhận chưa có khối (đơn cũ) vẫn dựng được", "bn-tt" not in cu and "zalo.me" in cu)


# ----------------------------------------------------------------- OnePay

@ca("v638 OnePay: vpc_CardList theo cách khách chọn, nằm TRONG chữ ký; không truyền thì không có ô; giá trị lạ không gửi")
def _card_list():
	for loai in ("INTERNATIONAL", "DOMESTIC"):
		ts = op.tham_so_tra(C, MA + "-1", 936000, MA, "https://x/ve", "1.2.3.4", "https://x", card_list=loai)
		la("ô " + loai, ts["vpc_CardList"], loai)
		dung("chuỗi ký có " + loai, "vpc_CardList=" + loai in op.chuoi_ky(ts))
		dung("chữ ký đúng", op.dung_chu_ky(ts, KHOA))
		sua = dict(ts, vpc_CardList="DOMESTIC" if loai == "INTERNATIONAL" else "INTERNATIONAL")
		dung("đổi loại thẻ là chữ ký sai", not op.dung_chu_ky(sua, KHOA))
	for kl in (None, "VISA", ""):
		dung("không ô khi %r" % kl, "vpc_CardList" not in op.tham_so_tra(C, MA + "-1", 1, MA, "u", "", "l", card_list=kl))


@ca("v638 OnePay định tuyến mã DW: mã giao dịch DW...-lần qua RE_MA_GD; ghi_nhan, thong_tin_trang, tao_gd sang thanh_toan_web; mã khác giữ đường cũ")
def _dinh_tuyen():
	la("mã giao dịch", op.ma_gd(MA, 2), MA + "-2")
	la("tách mã", (op.ma_phieu_cua_gd(MA + "-2"), op.ma_phieu_cua_gd("DW26110012-1"), op.ma_phieu_cua_gd("DW2611001234-1")), (MA, "", ""))
	la("lần tiếp", op.lan_tiep([{"ma": MA + "-1"}, {"ma": MA + "-3"}]), 4)
	vet = []
	with patch.object(tw, "ghi_nhan_the", lambda m, kq, n: vet.append(("ghi", m, n)) or {"ok": 1, "ly_do": ""}), \
			patch.object(tw, "thong_tin_trang", lambda m, k: vet.append(("trang", m)) or {"x": 1}), \
			patch.object(tw, "tao_gd", lambda m, k: vet.append(("tao", m)) or {"url": "u"}), \
			patch.object(op, "cau_hinh", return_value=dict(C)):
		ts = {"vpc_MerchTxnRef": MA + "-1", "vpc_Amount": op.so_tien_vpc(936000), "vpc_TxnResponseCode": "0"}
		ts["vpc_SecureHash"] = op.ky(ts, KHOA)
		op.ghi_nhan(ts, "ipn")
		op.thong_tin_trang(MA, "0" * 16)
		op.tao_gd("dw-2611-00123", "0" * 16)
	la("đi đúng đường", vet, [("ghi", MA, "ipn"), ("trang", MA), ("tao", "dw-2611-00123")])


def _kq(ma=MA + "-1", tien=936000, ma_kq="0", khoa=KHOA):
	ts = {"vpc_MerchTxnRef": ma, "vpc_Amount": op.so_tien_vpc(tien), "vpc_TxnResponseCode": ma_kq,
		"vpc_TransactionNo": "998877", "vpc_Card": "VC", "vpc_Merchant": "VAGABONDWEB"}
	ts["vpc_SecureHash"] = op.ky(ts, khoa)
	return ts


@ca("v638 tao_gd đơn web: khoá đúng mới tạo; số tiền là số còn phải trả đọc ở máy chủ; vpc_CardList theo cách khách chọn; nhật ký trên ô ẩn Don Web")
def _tao_gd():
	dbg = _Db([_dw(thanh_toan="atm")])
	with patch.object(op, "khoa_phieu", lambda ma: "abcdef0123456789"), \
			patch("vagabond.ten_mien.link_khach", lambda d: "https://order.test" + d):
		nem("khoá sai thì như không có đơn", lambda: _chay(_vat(dbg), lambda: tw.tao_gd(MA, "0" * 16)), _fr.ValidationError)
		r = _chay(_vat(dbg), lambda: tw.tao_gd(MA, "abcdef0123456789"))
	q = dict(re.findall(r"([^?&=]+)=([^&]*)", r["url"].split("?", 1)[1]))
	la("số tiền, loại thẻ, mã", (q["vpc_Amount"], q["vpc_CardList"], q["vpc_MerchTxnRef"]), ("93600000", "DOMESTIC", MA + "-1"))
	nk = json.loads(dbg.dw[TEN][tw.O_NK])
	la("nhật ký", [(g["ma"], g["so_tien"], g["trang_thai"]) for g in nk], [(MA + "-1", 936000.0, "cho")])
	dbg2 = _Db([_dw(thanh_toan="card", vgb_tt_trang_thai="Da thu", vgb_tt_da_thu=936000)])
	with patch.object(op, "khoa_phieu", lambda ma: "abcdef0123456789"):
		nem("đã thu đủ thì không tạo", lambda: _chay(_vat(dbg2), lambda: tw.tao_gd(MA, "abcdef0123456789")), _fr.ValidationError)
		nem("cổng tắt thì không tạo", lambda: _chay(_vat(dbg, onepay_dung=False), lambda: tw.tao_gd(MA, "abcdef0123456789")), _fr.ValidationError)


@ca("v638 OnePay đơn web: IPN chữ ký sai không ghi; thành công ghi ĐÚNG MỘT lần (IPN lặp, trang về); báo Sales một lần; Don Web ghi cách OnePay và mã")
def _ghi_the():
	nk = [{"ma": MA + "-1", "so_tien": 936000, "trang_thai": "cho"}]
	dbg = _Db([_dw(thanh_toan="card", **{tw.O_NK: json.dumps(nk)})])
	bao = []
	vat = _vat(dbg, bao)
	sai = _chay(vat, lambda: op.ghi_nhan(_kq(khoa="FFFF" + KHOA[4:]), "ipn"))
	la("chữ ký sai", (sai["ly_do"], dbg.dw[TEN]["vgb_tt_trang_thai"], json.loads(dbg.dw[TEN][tw.O_NK])[0]["trang_thai"]),
		("chu_ky_sai", None, "cho"))
	r = [_chay(vat, lambda: op.ghi_nhan(_kq(), n)) for n in ("ipn", "ipn", "trang_ve")]
	la("lần đầu ghi, sau đó đã ghi", [x["ly_do"] for x in r], ["", "da_ghi_roi", "da_ghi_roi"])
	d = dbg.dw[TEN]
	la("Don Web", (d["vgb_tt_trang_thai"], d["vgb_tt_da_thu"], d["vgb_tt_cach"]), ("Da thu", 936000.0, "OnePay"))
	la("giao dịch", [(g["gd"], g["ma"], g["loai"]) for g in json.loads(d["vgb_tt_ma_gd"])], [(MA + "-1", "998877", "the")])
	la("báo Sales một lần", [x[1].get("ma_tin") for x in bao], ["bh_don_web_da_tra"])
	la("hoá đơn đồng bộ: OnePay, mã giao dịch của tiệm", _chay(vat, lambda: tw.pt_hoa_don("91853", "91853")), ("OnePay", MA + "-1"))


@ca("Codex PR #541 vòng 2: đơn chọn thẻ đã khớp 300.000 đ chuyển khoản, trả nốt 636.000 đ qua OnePay: cách thu 'Nhiều cách', Pancake ghi riêng từng ô, hoá đơn để Sales chọn (không gán OnePay cho cả tổng)")
def _ck_va_the():
	nk = [{"ma": MA + "-1", "so_tien": 636000, "trang_thai": "cho"}]
	dbg = _Db([_dw(thanh_toan="card", **{tw.O_NK: json.dumps(nk)})],
		[{"name": "BT-1", "description": "S67355O91853T", "deposit": 300000, "reference_number": "FT1"}])
	bao = []
	vat = _vat(dbg, bao)
	# Đúng chuỗi Codex: khớp chuyển khoản trước, rồi kết quả OnePay về.
	la("chuyển khoản trước: thu thiếu", _chay(vat, lambda: tw.khop_ck(TEN)), ttt.TT_THIEU)
	la("cách lúc đó là chuyển khoản", dbg.dw[TEN]["vgb_tt_cach"], "Chuyển khoản")
	r = _chay(vat, lambda: op.ghi_nhan(_kq(tien=636000), "ipn"))
	la("ghi thẻ", r["ly_do"], "")
	d = dbg.dw[TEN]
	la("Don Web: đủ, nhiều cách", (d["vgb_tt_trang_thai"], d["vgb_tt_da_thu"], d["vgb_tt_cach"]), ("Da thu", 936000.0, ttt.CACH_NHIEU))
	ds = json.loads(d["vgb_tt_ma_gd"])
	la("nhật ký giữ riêng từng loại", [(g["gd"], g["loai"], g["so"]) for g in ds], [("BT-1", "ck", 300000.0), (MA + "-1", "the", 636000.0)])
	la("Pancake ghi riêng từng ô", ttt.than_pancake_ds(ds, d["vgb_tt_cach"], d["vgb_tt_da_thu"], {}),
		{"transfer_money": 300000, "prepaid": 636000})
	la("Pancake đã có ô chuyển khoản thì chỉ ghi ô thẻ", ttt.than_pancake_ds(ds, d["vgb_tt_cach"], d["vgb_tt_da_thu"], {"transfer_money": 300000}),
		{"prepaid": 636000})
	la("hoá đơn đồng bộ: để Sales chọn, không gán OnePay cho cả tổng", _chay(vat, lambda: tw.pt_hoa_don("91853", "91853")), ("", ""))
	la("chốt chuyển khoản vẫn thấy đúng phần chuyển khoản", _chay(vat, lambda: tw.ck_hoa_don("91853", "91853"))["nhan"], 300000.0)
	tieu, dong = ttt.tin_da_tra(TEN, "91853", d["vgb_tt_cach"], False, "da_ghi")
	dung("tin Sales nói hai cách", any("chuyển khoản và thẻ qua OnePay" in x for x in dong))
	# Bản ghi cũ OnePay mà nhật ký có cả chuyển khoản: cũng không gán OnePay.
	la("cách ghi OnePay mà nhật ký hai loại", ttt.pt_cho_hoa_don({"vgb_tt_trang_thai": "Da thu", "vgb_tt_cach": "OnePay",
		"vgb_tt_ma_gd": d["vgb_tt_ma_gd"]}), ("", ""))
	la("mã OnePay lấy đúng dòng thẻ, không lấy dòng sao kê", ttt.pt_cho_hoa_don({"vgb_tt_trang_thai": "Da thu", "vgb_tt_cach": "OnePay",
		"vgb_tt_ma_gd": json.dumps([{"gd": "BT-0", "loai": "ck", "so": 0}, {"gd": MA + "-2", "loai": "the", "so": 936000}])}), ("OnePay", MA + "-2"))


@ca("Codex PR #541 vòng 3: đơn chọn thẻ (cổng tắt, biên nhận hiện VietQR) mà khách chuyển khoản rồi đóng trang: nhịp quét 5 phút vẫn khớp và ghi đã thu")
def _quet_don_the():
	for cach in ("card", "atm"):
		dbg = _Db([_dw(thanh_toan=cach)], [{"name": "BT-1", "description": "S67355O91853T DW261100123", "deposit": 936000}])
		loc = []

		def get_all(dt, filters=None, **k):
			loc.append(dict(filters or {}))
			f = (filters or {}).get("thanh_toan")
			if dt == tw.DT and len(loc) == 1 and isinstance(f, list) and f[0] == "in" and cach in f[1]:
				return [TEN]
			return []
		with patch.object(_fr, "get_all", side_effect=get_all), patch.object(_fr, "log_error", lambda *a, **k: None):
			_chay(_vat(dbg), tw.quet)
		la("đơn %s: quét được và ghi đã thu" % cach, dbg.dw[TEN]["vgb_tt_trang_thai"], ttt.TT_DA_THU)
	la("lọc đủ ba cách online", loc[0]["thanh_toan"], ["in", ["bank", "card", "atm"]])
	la("khop_ck và nhịp quét cùng một danh sách cách", tw.QUET_CACH, ("bank", "card", "atm"))


@ca("v638 OnePay đơn web thất bại thì ghi thất bại, không đổi tiền; trả khi đơn đã huỷ thì báo kế toán hoàn toàn bộ")
def _the_hong():
	nk = [{"ma": MA + "-1", "so_tien": 936000, "trang_thai": "cho"}]
	dbg = _Db([_dw(thanh_toan="card", **{tw.O_NK: json.dumps(nk)})])
	_chay(_vat(dbg), lambda: op.ghi_nhan(_kq(ma_kq="99"), "trang_ve"))
	la("thất bại", (json.loads(dbg.dw[TEN][tw.O_NK])[0]["trang_thai"], dbg.dw[TEN]["vgb_tt_da_thu"]), ("that_bai", 0))
	dbg2 = _Db([_dw(thanh_toan="card", trang_thai="Da huy", **{tw.O_NK: json.dumps(nk)})])
	bao = []
	_chay(_vat(dbg2, bao), lambda: op.ghi_nhan(_kq(), "ipn"))
	g = json.loads(dbg2.dw[TEN][tw.O_NK])[0]
	la("nhật ký: phải hoàn toàn bộ", (g["trang_thai"], g["so_ghi"], g["du"]), ("da_ghi", 0.0, 936000.0))
	la("báo kế toán hoàn, không báo Sales đã trả", [x[1].get("ma_tin") for x in bao], ["kt_the_onepay"])
	la("Don Web không ghi đã thu", dbg2.dw[TEN]["vgb_tt_trang_thai"], None)


@ca("v638 lượt quét 15 phút có loại thứ ba: Don Web, ô nhật ký thẻ, cả đơn đã huỷ")
def _quet():
	loc = []
	gia = types.SimpleNamespace(get_all=lambda dt, filters=None, **k: loc.append((dt, dict(filters or {}))) or [],
		db=types.SimpleNamespace(commit=lambda: None, rollback=lambda: None), log_error=lambda *a, **k: None,
		get_traceback=lambda: "", utils=types.SimpleNamespace(now_datetime=lambda: __import__("datetime").datetime(2026, 11, 4, 12)))
	with patch.object(op, "frappe", gia), patch.object(op, "cau_hinh", return_value=dict(C)):
		op.quet()
	dw = [f for dt, f in loc if dt == tw.DT]
	la("có quét Don Web", len(dw), 1)
	la("lọc theo ô nhật ký, không lọc trạng thái", sorted(dw[0]), sorted([tw.O_NK, "name"]))


# ----------------------------------------------------------- Pancake, hoá đơn

class _Tra:
	def __init__(self, ma, d):
		self.status_code, self._d, self.text = ma, d, "x"

	def json(self):
		return self._d


@ca("v638 ghi Pancake: chuyển khoản ô transfer_money, thẻ ô prepaid; đọc lại phải mang số; không hạ số đang có; cờ tắt; chưa có mã đơn; lỗi không ném")
def _pancake():
	la("thân chuyển khoản", ttt.than_pancake("Chuyển khoản", 936000, {}), {"transfer_money": 936000})
	la("thân thẻ", ttt.than_pancake("OnePay", 936000, {"prepaid": 0}), {"prepaid": 936000})
	la("đã có đủ thì thôi", ttt.than_pancake("OnePay", 936000, {"prepaid": 936000}), None)
	la("cách lạ thì thôi", ttt.than_pancake("Tiền mặt", 936000, {}), None)
	from vagabond import lib

	def chay(don_doc, cfg_tat=0, pid="91853", put_ma=200):
		vet = []
		lan = iter(don_doc)
		req = types.SimpleNamespace(get=lambda *a, **k: vet.append("get") or _Tra(200, {"data": next(lan)}),
			put=lambda *a, **k: vet.append(("put", k.get("json"))) or _Tra(put_ma, {}))
		with patch.object(tw, "requests", req), patch.object(lib, "cfg_o", lambda o: cfg_tat if o == tw.O_TAT_PANCAKE else ""), \
				patch.object(tw, "_pancake_khoa", lambda: (D(pancake_shop_id="67355"), "k")):
			r = tw.ghi_pancake(D(name=TEN, pancake_id=pid, vgb_tt_cach="Chuyển khoản", vgb_tt_da_thu=936000))
		return r, vet
	r, vet = chay([{"transfer_money": 0}, {"transfer_money": 936000}])
	la("ghi xong, đọc lại thấy số", (r, vet), ("da_ghi", ["get", ("put", {"transfer_money": 936000}), "get"]))
	la("Pancake nhận 200 mà bỏ qua ô: lỗi", chay([{}, {}])[0], "loi")
	la("Pancake từ chối: lỗi", chay([{}], put_ma=400)[0], "loi")
	la("đã có sẵn", chay([{"transfer_money": 936000}])[0], "da_co")
	la("cờ tắt", chay([], cfg_tat=1), ("tat", []))
	la("chưa có mã đơn", chay([], pid=""), ("cho_ma_don", []))
	tieu, dong = ttt.tin_da_tra(TEN, "91853", "OnePay", False, "loi")
	sach, bo = kz.bo_dong_tien("\n".join([tieu] + dong))
	la("tin Sales không mang số tiền (luật v613)", bo, 0)
	dung("tin nói Sales ghi tay khi lỗi", any("Sales ghi tay" in x for x in dong))


@ca("v638 hoá đơn đơn web trả chuyển khoản theo nội dung mã Don Web (đơn chưa có mã Pancake lúc đặt): _soat_sepay cho ghi sổ; không có tiền thì vẫn chặn")
def _soat():
	bh = _bh()
	si = D(name="HDB-1", vgb_pt_thanh_toan="Chuyển khoản", custom_pancake_id="91853", custom_pancake_display_id="91853",
		grand_total=936000, vgb_ma_tham_chieu="")
	ds = [{"gd": "BT-9", "ma": "FT9", "so": 936000, "loai": "ck"}]
	dbg = _Db([_dw(vgb_tt_trang_thai="Da thu", vgb_tt_da_thu=936000, vgb_tt_cach="Chuyển khoản", vgb_tt_ma_gd=json.dumps(ds))])
	_chay(_vat(dbg), lambda: bh._soat_sepay(si, sepay={}))
	la("qua chốt, điền mã tham chiếu", si.vgb_ma_tham_chieu, "FT9")
	si2 = D(si, vgb_ma_tham_chieu="")
	nem("không có tiền: vẫn chặn", lambda: _chay(_vat(_Db([_dw()])), lambda: bh._soat_sepay(si2, sepay={})), _fr.ValidationError)
	the = [{"gd": MA + "-1", "ma": "998877", "so": 936000, "loai": "the"}]
	dbg3 = _Db([_dw(vgb_tt_trang_thai="Da thu", vgb_tt_da_thu=936000, vgb_tt_cach="OnePay", vgb_tt_ma_gd=json.dumps(the))])
	nem("tiền thẻ không được tính là chuyển khoản", lambda: _chay(_vat(dbg3), lambda: bh._soat_sepay(D(si2), sepay={})), _fr.ValidationError)


@ca("v638 hoá đơn đơn web trả thẻ qua OnePay của tiệm KHÔNG bị chặn ghi sổ: phương thức OnePay không bắt mã, không qua chốt SePay")
def _onepay_khong_chan():
	from vagabond import pt_thanh_toan

	bh = _bh()

	q = pt_thanh_toan.theo_ten("OnePay") or {}
	dung("OnePay không bắt buộc mã tham chiếu", not q.get("bat"))
	la("chuẩn hoá mã giao dịch của tiệm qua được", bh._chuan_ma_tham_chieu("OnePay", MA + "-1"), MA + "-1")
	si = D(name="HDB-2", vgb_pt_thanh_toan="OnePay", custom_pancake_display_id="91853", grand_total=936000, vgb_ma_tham_chieu="")
	la("chốt SePay bỏ qua OnePay", bh._soat_sepay(si, sepay={}), None)
	la("đơn web chưa trả: không đặt phương thức", _chay(_vat(_Db([_dw()])), lambda: bh._pt_don_web("91853", "91853")), ("", ""))
	la("đọc hỏng không làm hỏng đồng bộ", bh._pt_don_web(object(), object()), ("", ""))


# --------------------------------------------------------------- tao_don, cửa

@ca("v638 tao_don: nhận bốn cách, giá trị lạ về chuyển khoản, cổng tắt thì thẻ về chuyển khoản; mã giới thiệu chuẩn hoá vào ảnh chụp gioi_thieu_sdt")
def _tao_don():
	from vagabond.khung.kiem_thu.thu_don_web_367 import _Tra as _T, _don, _moi_truong_tao_don

	def gui(dung_duoc, **them):
		vet, tao_don = _moi_truong_tao_don(lambda v: _T(200, {"data": {"id": "91500"}}))
		import vagabond

		tk = types.SimpleNamespace(bao_don_web_moi=lambda *a, **k: None)
		with patch.object(op, "dung_duoc", lambda c=None: dung_duoc), \
				patch.dict(sys.modules, {"vagabond.tin_kho": tk}), patch.object(vagabond, "tin_kho", tk, create=True):
			tao_don(_don(**them))
		return vet.truong["thanh_toan"], json.loads(vet.truong["snapshot"])
	for pt in ("bank", "card", "atm", "cash"):
		la("nhận " + pt, gui(True, thanh_toan=pt)[0], pt)
	la("lạ", gui(True, thanh_toan="momo")[0], "bank")
	la("cổng tắt", [gui(False, thanh_toan=x)[0] for x in ("card", "atm", "cash")], ["bank", "bank", "cash"])
	_t, snap = gui(True, thanh_toan="cash", ma_gioi_thieu="0909 123 456")
	la("ảnh chụp", (snap["thanh_toan"], snap["gioi_thieu_sdt"]), ("cash", "0909123456"))
	la("mã sai bỏ", gui(True, ma_gioi_thieu="12ab")[1]["gioi_thieu_sdt"], "")


@ca("v638 cửa khách hỏi trạng thái: token sai hay không có đơn thì báo không thấy; đúng token thì khớp sao kê rồi trả khối thanh toán, không lộ tên, số điện thoại")
def _cua():
	dbg = _Db([_dw()], [{"name": "BT-9", "description": "S67355O91853T", "deposit": 936000}])
	nem("token sai dạng", lambda: _chay(_vat(dbg), lambda: tw.trang_thai("ngan")), _fr.ValidationError)
	nem("token không có đơn", lambda: _chay(_vat(dbg), lambda: tw.trang_thai("X" * 43)), _fr.ValidationError)
	r = _chay(_vat(dbg), lambda: tw.trang_thai("T" * 43))
	la("đã nhận tiền", (r["trang_thai"], r["cach_thu"]), ("da_thu", "Chuyển khoản"))
	s = json.dumps(r, ensure_ascii=False)
	dung("không lộ tên, số điện thoại", "Nguyễn" not in s and "0931224334" not in s)
	nguon = (GOC / "vagabond/thanh_toan_web.py").read_text()
	m = re.search(r"@frappe\.whitelist\(allow_guest=True, methods=\[\"POST\"\]\)\n@rate_limit\(limit=(\d+), seconds=(\d+)\)\ndef trang_thai\(", nguon)
	dung("cửa khách có rate_limit, chỉ POST", bool(m))
	dung("giới hạn đủ cho hỏi mỗi 5 giây trong 10 phút (120 lần)", m and int(m.group(1)) >= 120 and int(m.group(2)) == 600)


@ca("v638 nối: ô mới có neo, ô nhật ký ẩn; dựng ở truong_tu_them; nhịp 5 phút; tin Zalo mới có ở danh mục; cấu hình web báo cổng thẻ")
def _noi():
	for dt, ds in tw.TRUONG_MOI.items():
		for o in ds:
			dung("%s.%s có insert_after" % (dt, o["fieldname"]), o.get("insert_after"))
	o_nk = [o for o in tw.TRUONG_MOI[tw.DT] if o["fieldname"] == tw.O_NK][0]
	la("ô nhật ký ẩn, chỉ đọc, không chép", (o_nk.get("hidden"), o_nk.get("read_only"), o_nk.get("no_copy")), (1, 1, 1))
	dung("không ô mới nào trùng ô máy ghi lúc gửi đơn", not {o["fieldname"] for o in tw.TRUONG_MOI[tw.DT]} & set(don_web.KHONG_DOI))
	dung("dựng nhóm trường", "_dung_nhom(thanh_toan_web.TRUONG_MOI" in (GOC / "vagabond/truong_tu_them.py").read_text())
	dung("nhịp 5 phút", '"vagabond.thanh_toan_web.quet"' in (GOC / "vagabond/hooks.py").read_text())
	dung("tin mới", "bh_don_web_da_tra" in kz.TIN and kz.TIN["bh_don_web_da_tra"][0] == "Bán hàng, cửa hàng")
	s = (GOC / "vagabond/don_web.py").read_text()
	dung("cấu hình web có cờ onepay", '"onepay": 1 if dung_duoc() else 0' in s)


@ca("v638 hành vi trình duyệt: bước đặt bánh 4 cách, gửi đúng thanh_toan và ma_gioi_thieu; biên nhận Vue vẽ đúng khối, hỏi lại rồi đổi sang đã nhận (node thật)")
def _node():
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/thanh_toan_web_638.mjs"], cwd=GOC, capture_output=True, text=True, timeout=60)
	la(r.stdout[-2500:] + r.stderr[-1500:], r.returncode, 0)
	m = re.search(r"(\d+) ca dat, 0 ca hong", r.stdout)
	dung("đủ số ca", m and int(m.group(1)) >= 8)
