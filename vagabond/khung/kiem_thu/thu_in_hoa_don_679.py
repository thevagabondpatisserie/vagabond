# -*- coding: utf-8 -*-
"""v679: mẫu in hoá đơn quầy (anh Việt 21/11/2026, tờ HDB-26-11-03963).

1. Bỏ phần "(tiệm chịu 40.000)" của tên voucher Grab trên tờ khách.
2. In mã Grab Dine-Out (GD-...) thu ngân nhập, ngay dưới dòng voucher Grab.
3. Thân hoá đơn có lề ngang (trước sát mép trái), mã QR nhỏ lại 26mm.
4. In lại từ chi tiết bill cũng có dòng khuyến mãi và mã GD-.

Các ca CHẠY THẬT hàm posInBill trong node với hàm in giả bắt lấy tờ HTML,
không dò chuỗi trong mã nguồn.
"""

import io
import json
import os
import re
import subprocess

from vagabond import mau_in_quay
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	return os.path.dirname(
		os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	)


def _js(ten):
	return io.open(
		os.path.join(_goc(), "vagabond", "public", "js", "bep", ten), encoding="utf-8"
	).read()


def _ham(src, ten, async_=False):
	m = re.search(r"\n%sfunction %s\([^)]*\) \{.*?\n\}" % ("async " if async_ else "", re.escape(ten)), src, re.S)
	if not m:
		raise AssertionError("không thấy hàm %s" % ten)
	return m.group(0)


def _nen():
	"""Mã thật của các hàm in hoá đơn, cộng bản giả của phần chạm mạng."""
	b = _js("10-bill-quay.js")
	n = _js("00-nen.js")
	md = re.search(r"\nvar IN_MAU_MD = \{.*?\n\};", b, re.S).group(0)
	ham = "".join(_ham(b, t) for t in (
		"posTenKmIn", "posLaKmGrab", "inSoMm", "posKmTuBill", "posUdBan", "inKho", "inMau"))
	ham += _ham(b, "posInBill", True)
	ham += _ham(n, "h") + _ham(n, "money")
	gia = r"""
var location = {origin: 'https://app.x'};
function posGopDongMon(m) { return m; }
function posPmGhiNho() {}
async function posInPhieuMon() {}
var TO = null, CFGBH = {}, S = {me: {full_name: 'Thu ngân'}, user: 'tn@x'}, posQuay = {ma: 'TCV', ten: 'Quầy', phu: '9 Trần Cao Vân'};
var posDon = {bill: ''};
function inMoCuaSoNeuCan() { return null; }
function posCanInKemPhieuMon() { return false; }
async function api(m) { if (m === 'vagabond.ban_hang.pos_link_xhd') return {url: 'https://x/xhd?d=1'}; return {diem: null, thu_ngan: 'Bảo'}; }
async function inQrAnh() { return 'data:image/png;base64,AA'; }
async function posQrAnhIn() { return 'data:image/png;base64,AA'; }
function posQrLoi() { return ''; }
function posNoiDungCk() { return 'TCV1'; }
function posTaiKhoan() { return {}; }
function toast() {}
async function inTo(v, t, html) { TO = html; return 'qz'; }
"""
	return gia + md + ham


def _in(bill, cau_hinh=None):
	ma = _nen() + """
CFGBH = %s;
(async function () { await posInBill(%s); console.log(JSON.stringify(TO)); })()
  .catch(function (e) { console.error(e && e.stack || e); process.exit(1); });
""" % (json.dumps(cau_hinh or {}), json.dumps(bill))
	r = subprocess.run(["node", "-e", ma], capture_output=True, text=True, timeout=30)
	if r.returncode != 0:
		raise AssertionError("node lỗi: " + (r.stderr or "")[:600])
	return json.loads(r.stdout.strip())


def _bill(**them):
	d = {
		"name": "HDB-26-11-03963", "bill": "TCV569MN", "tam_tinh": 0, "huy": 0,
		"mon": [{"ten": "Hũ Flan Kasutera Verrine", "qty": 3, "rate": 65000, "tc": []}],
		"tong": 195000, "giam": 40000, "thu": 155000, "pt": "Grab Dine-Out",
		"kmAp": [{"ten": "VOUCHER 200.000 GRAB DINE OUT (tiệm chịu 40.000)", "giam": 40000}],
		"mtc": "GD-KKJDUSEH", "quay": "TCV", "nguon": "", "diem": None, "xhd_url": "https://x/xhd?d=1",
	}
	d.update(them)
	return d


def _dong(html):
	"""Các dòng chữ của tờ in, bỏ thẻ."""
	return [re.sub(r"<[^>]+>", " ", x).strip() for x in html.split('<div class="d">')[1:]]


@ca("in hoá đơn v679: tên voucher Grab không còn phần (tiệm chịu ...)")
def _():
	to = _in(_bill())
	dung("không còn chữ tiệm chịu", "tiệm chịu" not in to)
	dung("vẫn còn tên voucher", "VOUCHER 200.000 GRAB DINE OUT" in to)
	dung("vẫn còn số giảm", "-40.000" in to)


@ca("in hoá đơn v679: mã GD- in ngay dưới dòng voucher Grab, đúng một lần")
def _():
	d = _dong(_in(_bill()))
	i = [k for k, x in enumerate(d) if "GRAB DINE OUT" in x]
	dung("có dòng voucher", len(i) == 1)
	dung("dòng ngay sau là mã GD-", "Mã voucher: GD-KKJDUSEH" in d[i[0] + 1])
	la("mã GD- chỉ in một lần", sum("GD-KKJDUSEH" in x for x in d), 1)


@ca("in hoá đơn v679: không có dòng voucher Grab thì mã GD- in dưới dòng Thanh toán")
def _():
	d = _dong(_in(_bill(kmAp=[])))
	i = [k for k, x in enumerate(d) if x.startswith("Thanh toán")]
	dung("có dòng Thanh toán", len(i) == 1)
	dung("dòng sau là mã GD-", "Mã voucher: GD-KKJDUSEH" in d[i[0] + 1])


@ca("in hoá đơn v679: phiếu tạm tính và bill không có mã GD- thì không in dòng mã")
def _():
	dung("tạm tính không in mã", "Mã voucher" not in _in(_bill(tam_tinh=1)))
	dung("mã tham chiếu khác (thẻ) không in", "Mã voucher" not in _in(_bill(mtc="046327", pt="Thẻ", kmAp=[])))
	dung("không có mã thì không in", "Mã voucher" not in _in(_bill(mtc="")))


@ca("in hoá đơn v679: thân hoá đơn có lề ngang và QR 26mm theo mặc định")
def _():
	to = _in(_bill())
	dung("lề trái và phải 3mm", "padding:4mm 3mm 6mm 3mm" in to)
	dung("QR 26mm", ".qr img{width:26mm;height:26mm" in to)
	dung("không còn QR 34mm", "width:34mm" not in to)


@ca("in hoá đơn v679: lề và cỡ QR đọc từ mẫu in của điểm bán; 0 là giá trị hợp lệ")
def _():
	cau = {"mau_in_diem": {"TCV": {"hoa_don": {"le_trai": 4.5, "le_phai": 0, "co_qr": 22}}}}
	to = _in(_bill(), cau)
	dung("lề trái 4.5 phải 0", "padding:4mm 0mm 6mm 4.5mm" in to)
	dung("QR 22mm", ".qr img{width:22mm;height:22mm" in to)
	# Ngoài khoảng thì về mặc định, không in tờ lỗi.
	cau = {"mau_in_diem": {"TCV": {"hoa_don": {"le_trai": 50, "co_qr": "to"}}}}
	to = _in(_bill(), cau)
	dung("lề 50 về 3", "6mm 3mm}" in to)
	dung("QR chữ về 26", ".qr img{width:26mm" in to)


@ca("in hoá đơn v679: in lại từ chi tiết bill lấy dòng khuyến mãi từ bill đã lưu")
def _():
	b = _js("10-bill-quay.js")
	ma = _ham(b, "posKmTuBill") + _ham(b, "posUdBan") + """
var a = posKmTuBill({vgb_km: JSON.stringify([{ten: 'VOUCHER 200.000 GRAB DINE OUT (tiệm chịu 40.000)', giam: 40000}, {ten: 'Nhân điểm', giam: 0}])});
var u = posKmTuBill({vgb_ud_ban: JSON.stringify({ma: 'K7M2QP', ten: 'Ưu đãi Zalo', giam: 20000})});
var u0 = posKmTuBill({vgb_ud_ban: JSON.stringify({ma: 'K7M2QP', ten: 'Ưu đãi Zalo', giam: 0})});
var hong = posKmTuBill({vgb_km: '{hỏng'});
console.log(JSON.stringify([a, u, u0, hong]));
"""
	r = subprocess.run(["node", "-e", ma], capture_output=True, text=True, timeout=20)
	dung("node chạy", r.returncode == 0)
	a, u, u0, hong = json.loads(r.stdout)
	la("chỉ lấy chương trình có trừ tiền", a, [{"ten": "VOUCHER 200.000 GRAB DINE OUT (tiệm chịu 40.000)", "giam": 40000}])
	la("ưu đãi áp tại bàn có trừ tiền", u, [{"ten": "Ưu đãi Zalo", "giam": 20000}])
	la("ưu đãi chưa trừ thì không in", u0, [])
	la("dữ liệu hỏng không làm hỏng tờ in", hong, [])
	# Và pbBillObj (in lại) thật sự mang hai khoá này vào posInBill.
	than = b.split("function pbBillObj() {")[1].split("\n  }")[0]
	dung("in lại mang dòng khuyến mãi", "kmAp: posKmTuBill(d)" in than)
	dung("in lại mang mã tham chiếu", "mtc: d.vgb_ma_tham_chieu" in than)


@ca("in hoá đơn v679: máy chủ cho chỉnh lề và cỡ QR trong khoảng, giữ 0")
def _():
	ra = mau_in_quay.chuan_mot("hoa_don", {"le_trai": 0, "le_phai": 8, "co_qr": 20})
	la("lề trái 0 giữ nguyên", ra["le_trai"], 0.0)
	la("lề phải 8 giữ nguyên", ra["le_phai"], 8.0)
	la("QR 20 giữ nguyên", ra["co_qr"], 20.0)
	ra = mau_in_quay.chuan_mot("hoa_don", {"le_trai": -1, "co_qr": 40})
	la("lề âm về mặc định", ra["le_trai"], 3.0)
	la("QR 40 về mặc định", ra["co_qr"], 26.0)
	ra = mau_in_quay.chuan_mot("hoa_don", {"co_chu": 12})
	la("bản đã lưu trước v679 nhận mặc định mới", (ra["le_trai"], ra["le_phai"], ra["co_qr"]), (3.0, 3.0, 26.0))
