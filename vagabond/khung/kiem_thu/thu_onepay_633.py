# -*- coding: utf-8 -*-
"""v633: thanh toán thẻ OnePay cho phiếu đề nghị thanh toán (anh Việt 03/11/2026).

Phép thuần của onepay.py chạy thật: chữ ký HMAC theo tài liệu tích hợp OnePay,
ô cài đặt người dán tay, mã giao dịch, khoá trang khách, luật được ghi tiền.
Đường ghi tiền thật (phiếu thu, biên nhận đính kèm, chống ghi hai lần) chạy
trên ERPNext thật ở kiem_that/thu_onepay_633.py.
"""

import hashlib
import hmac
import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import onepay as op  # noqa: E402

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Hash code dạng hex như OnePay cấp (giá trị bịa cho ca kiểm, không phải khoá thật).
KHOA = "0123456789ABCDEF0123456789ABCDEF"
C = {"cong": "https://mtf.onepay.vn/paygate/vpcpay.op", "merchant": "THUNGHIEM", "access_code": "ABCD1234",
	"hash_code": KHOA, "query_user": "op01", "query_password": "mk"}


def _doc(*p):
	return io.open(os.path.join(GOI, *p), encoding="utf-8").read()


@ca("v633 OnePay: chuỗi ký chỉ gồm vpc_ và user_, xếp theo tên, bỏ ô rỗng và ô chữ ký")
def _chuoi_ky():
	ts = {"vpc_Merchant": "M", "vpc_Amount": "100", "Title": "X", "AgainLink": "y", "vpc_Locale": "",
		"user_A": "1", "vpc_SecureHash": "ZZ", "vpc_SecureHashType": "SHA256"}
	la("đúng thứ tự, đúng ô", op.chuoi_ky(ts), "user_A=1&vpc_Amount=100&vpc_Merchant=M")


@ca("v633 OnePay: chữ ký là HMAC-SHA256 với khoá hex đã giải ra byte, hex IN HOA; sửa một ô là chữ ký sai")
def _ky():
	ts = {"vpc_Amount": "100000", "vpc_MerchTxnRef": "DNTT261100002-1", "vpc_Merchant": "THUNGHIEM"}
	tu_tinh = hmac.new(bytes.fromhex(KHOA), b"vpc_Amount=100000&vpc_MerchTxnRef=DNTT261100002-1&vpc_Merchant=THUNGHIEM",
		hashlib.sha256).hexdigest().upper()
	la("khớp phép tính độc lập", op.ky(ts, KHOA), tu_tinh)
	dung("64 ký tự hex in hoa", re.fullmatch(r"[0-9A-F]{64}", op.ky(ts, KHOA)) is not None)
	ky = dict(ts, vpc_SecureHash=op.ky(ts, KHOA))
	dung("chữ ký đúng", op.dung_chu_ky(ky, KHOA))
	dung("chữ ký thường cũng nhận", op.dung_chu_ky(dict(ky, vpc_SecureHash=ky["vpc_SecureHash"].lower()), KHOA))
	dung("sửa số tiền là sai", not op.dung_chu_ky(dict(ky, vpc_Amount="1000"), KHOA))
	dung("khoá khác là sai", not op.dung_chu_ky(ky, "FFFF" + KHOA[4:]))
	dung("thiếu chữ ký là sai", not op.dung_chu_ky(ts, KHOA))


@ca("v633 OnePay: ô địa chỉ cổng người dán tay: thiếu https, khoảng trắng, dấu ngoặc, tham số thừa đều chịu; địa chỉ tra cứu cùng thư mục")
def _cong():
	la("chuẩn", op.chuan_cong("https://onepay.vn/paygate/vpcpay.op"), "https://onepay.vn/paygate/vpcpay.op")
	la("thiếu https, thừa cách", op.chuan_cong("  onepay.vn/paygate/vpcpay.op "), "https://onepay.vn/paygate/vpcpay.op")
	la("dán kèm dấu ? và tham số", op.chuan_cong("https://ONEPAY.vn/paygate/vpcpay.op?x=1"), "https://onepay.vn/paygate/vpcpay.op")
	la("dán trong ngoặc kép", op.chuan_cong('"https://mtf.onepay.vn/paygate/vpcpay.op"'), "https://mtf.onepay.vn/paygate/vpcpay.op")
	la("trống", op.chuan_cong("  "), "")
	la("tra cứu", op.cong_tra_cuu("https://mtf.onepay.vn/onecomm-pay/vpc.op"), "https://mtf.onepay.vn/onecomm-pay/Vpcdps.op")


@ca("v633 OnePay: tham số một lần trả đủ ô OnePay đòi, số tiền nhân 100, đã ký đúng; thiếu khoá thì báo")
def _tra():
	ts = op.tham_so_tra(C, "DNTT261100002-1", 1224000, "DNTT-26-11-00002", "https://x/tra-the/A?k=b&ve=1", "1.2.3.4", "https://x/l")
	for o in ("vpc_Version", "vpc_Currency", "vpc_Command", "vpc_AccessCode", "vpc_Merchant", "vpc_Locale", "vpc_ReturnURL",
			"vpc_MerchTxnRef", "vpc_OrderInfo", "vpc_Amount", "vpc_TicketNo", "AgainLink", "Title", "vpc_SecureHash"):
		dung("có " + o, bool(ts.get(o)))
	la("số tiền nhân 100", ts["vpc_Amount"], "122400000")
	la("lệnh pay, tiền VND", (ts["vpc_Command"], ts["vpc_Currency"]), ("pay", "VND"))
	dung("chữ ký đúng", op.dung_chu_ky(ts, KHOA))
	dung("địa chỉ trả đi vào cổng", op.url_tra(C, ts).startswith("https://mtf.onepay.vn/paygate/vpcpay.op?"))
	loi = ""
	try:
		op.tham_so_tra(dict(C, hash_code=""), "A-1", 1, "", "", "", "")
	except ValueError as e:
		loi = str(e)
	dung("thiếu khoá báo rõ", "Hash code" in loi)
	la("tiền đọc ngược", op.tien_tu_vpc("122400000"), 1224000.0)


@ca("v633 OnePay: mã giao dịch theo phiếu và lần; lần tiếp theo; tách mã phiếu")
def _ma():
	la("mã", op.ma_gd("DNTT-26-11-00002", 3), "DNTT261100002-3")
	la("tách", op.ma_phieu_cua_gd("DNTT261100002-3"), "DNTT261100002")
	la("mã lạ", op.ma_phieu_cua_gd("PL_VAGABOND_1"), "")
	la("lần đầu", op.lan_tiep([]), 1)
	la("lần tiếp", op.lan_tiep([{"ma": "DNTT261100002-1"}, {"ma": "DNTT261100002-4"}, {"ma": "rác"}]), 5)
	la("nhật ký hỏng là rỗng", op.doc_nhat_ky("{không phải json"), [])


@ca("v633 OnePay: khoá trang khách cố định theo phiếu, phiếu khác khoá khác, bí mật khác khoá khác")
def _khoa():
	k1 = op.khoa_trang("bi-mat", "DNTT-26-11-00002")
	la("cố định", op.khoa_trang("bi-mat", "DNTT-26-11-00002"), k1)
	dung("16 ký tự hex", re.fullmatch(r"[0-9a-f]{16}", k1) is not None)
	dung("phiếu khác", op.khoa_trang("bi-mat", "DNTT-26-11-00003") != k1)
	dung("bí mật khác", op.khoa_trang("khac", "DNTT-26-11-00002") != k1)
	la("đường", op.duong_trang("DNTT-26-11-00002", k1), "/tra-the/DNTT261100002?k=" + k1)


def _kq(ma="DNTT261100002-1", tien=1224000, ma_kq="0", khoa=KHOA):
	ts = {"vpc_MerchTxnRef": ma, "vpc_Amount": op.so_tien_vpc(tien), "vpc_TxnResponseCode": ma_kq,
		"vpc_TransactionNo": "998877", "vpc_Card": "VC", "vpc_Merchant": "THUNGHIEM"}
	ts["vpc_SecureHash"] = op.ky(ts, khoa)
	return op.doc_ket_qua(ts, KHOA)


@ca("v633 OnePay: chỉ ghi tiền khi chữ ký đúng, thành công, đúng giao dịch của phiếu, chưa ghi, đúng số tiền; trả dư thì ghi phần còn nợ")
def _xet():
	gd = {"ma": "DNTT261100002-1", "so_tien": 1224000, "trang_thai": "cho"}
	la("được ghi", op.xet_ghi_nhan(gd, _kq(), 1224000), (True, 1224000.0, ""))
	la("chữ ký giả", op.xet_ghi_nhan(gd, _kq(khoa="FFFF" + KHOA[4:]), 1224000)[2], "chu_ky_sai")
	la("thẻ bị từ chối", op.xet_ghi_nhan(gd, _kq(ma_kq="5"), 1224000)[2], "khong_thanh_cong")
	la("giao dịch lạ", op.xet_ghi_nhan(None, _kq(), 1224000)[2], "gd_la")
	la("đã ghi rồi", op.xet_ghi_nhan(dict(gd, trang_thai="da_ghi"), _kq(), 1224000)[:2], (False, 0.0))
	la("lệch số tiền", op.xet_ghi_nhan(gd, _kq(tien=1000000), 1224000)[2], "lech_so_tien")
	la("trả dư (phiếu đã có tiền khác về)", op.xet_ghi_nhan(gd, _kq(), 224000), (True, 224000.0, "du"))
	la("câu mã 99", op.cau_ma("99"), "Quý khách đã huỷ giao dịch.")


@ca("v633 OnePay: phiếu, trang khách và điểm nhận IPN nối đúng chỗ (hook, miền khách, cửa ngõ, tin Zalo, chip cài đặt)")
def _noi():
	hk = _doc("hooks.py")
	dung("luật đường /tra-the/<ma>", '{"from_route": "/tra-the/<ma>", "to_route": "tra-the"}' in hk)
	dung("quét tra cứu 15 phút", '"*/15 * * * *", []).append("vagabond.onepay.quet")' in hk)
	from vagabond import ten_mien

	dung("trang /tra-the thuộc miền khách", "/tra-the" in ten_mien.DAU_KHACH)
	dung("có tệp trang", os.path.exists(os.path.join(GOI, "www", "tra-the.html")) and os.path.exists(os.path.join(GOI, "www", "tra_the.py")))
	# kenh_zalo nạp get_url (không có ở Frappe giả): đọc bảng TIN từ nguồn; khớp
	# bản JS đã có ca thu_tin_zalo_604 chốt.
	dung("tin kế toán khi khách trả thẻ", '"kt_the_onepay": ("Hoá đơn, kế toán",' in _doc("kenh_zalo.py"))
	import json

	d = json.loads(_doc("vagabond", "doctype", "vagabond_settings", "vagabond_settings.json"))
	f = {x["fieldname"]: x for x in d["fields"]}
	for o, kieu in (("onepay_bat", "Check"), ("onepay_cong", "Data"), ("onepay_merchant", "Data"), ("onepay_access_code", "Password"),
			("onepay_hash_code", "Password"), ("onepay_query_user", "Data"), ("onepay_query_password", "Password")):
		la("ô %s" % o, (f.get(o) or {}).get("fieldtype"), kieu)
	dung("mục nằm trong tab Bán hàng và thanh toán", d["field_order"].index("tab_ban_hang") < d["field_order"].index("sec_onepay")
		< d["field_order"].index("tab_ke_toan"))
	dung("mô tả mục ghi địa chỉ IPN", "/api/method/vagabond.onepay.ipn" in f["sec_onepay"]["description"])
	cn = json.loads(_doc("vagabond", "doctype", "vagabond_cong_no", "vagabond_cong_no.json"))
	dung("phiếu có nhật ký giao dịch thẻ", any(x["fieldname"] == "onepay_gd" for x in cn["fields"]))


def _dung_phieu():
	"""Dựng _phieu_html và _khoi_hai_cach thật của cong_no.py trên Frappe giả
	(cùng cách ca QR474 làm), trả hàm in phiếu."""
	import ast
	import html
	import types

	cay = ast.parse(_doc("cong_no.py"))
	ham = [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name in ("_phieu_html", "_khoi_hai_cach")]
	la("đủ hai hàm in phiếu", sorted(n.name for n in ham), ["_khoi_hai_cach", "_phieu_html"])
	d = dict(qr=dict(bank="MB", stk="123", ten="Vagabond"), tong_tien=1224000, ma_phieu="DNTT-26-11-00002")
	env = dict(xem_phieu=lambda name: d, frappe=types.SimpleNamespace(utils=types.SimpleNamespace(escape_html=html.escape),
		db=types.SimpleNamespace(get_value=lambda *a: ""), session=types.SimpleNamespace(user="test"),
		log_error=lambda *a, **k: None, get_traceback=lambda: ""),
		flt=lambda v: float(v or 0), _ngay_vn=lambda v: "", _tien_vn=lambda v: "{:,.0f}".format(float(v)).replace(",", "."),
		_chu_so_tien=lambda v: "Một triệu", TEN_NGAN_HANG_DAY_DU={})
	exec(compile(ast.Module(body=ham, type_ignores=[]), "cong_no.py", "exec"), env)
	env["_qr_data_uri"] = lambda *a: "data:image/svg+xml;base64,CK"
	return env["_phieu_html"]


@ca("v633 OnePay: phiếu đề nghị thanh toán in hai cách trả khi bật, QR thẻ trỏ đúng link có khoá; tắt hoặc đọc cài đặt hỏng thì phiếu như cũ")
def _phieu_pdf():
	from unittest.mock import patch

	from vagabond import qr_chuyen_khoan as q

	in_phieu = _dung_phieu()
	link = "https://thevagabondpatisserie.com/tra-the/DNTT261100002?k=0123456789abcdef"
	ve = []
	with patch.object(op, "cau_hinh", return_value=dict(C, bat=1)), patch.object(op, "link_phieu", return_value=link), \
			patch.object(q, "anh_lien_ket", side_effect=lambda u: ve.append(u) or "data:image/svg+xml;base64,THE"):
		bat = in_phieu("x")
	la("QR thẻ vẽ đúng link có khoá", ve, [link])
	dung("có ô thẻ", "2. THẺ TÍN DỤNG, THẺ GHI NỢ" in bat and "base64,THE" in bat)
	dung("có ô chuyển khoản", "1. CHUYỂN KHOẢN NGÂN HÀNG" in bat and "base64,CK" in bat)
	dung("in link đủ khoá để gõ tay", "thevagabondpatisserie.com/tra-the/DNTT261100002?k=0123456789abcdef" in bat)
	dung("không còn câu về phí thẻ (anh Việt bỏ 03/11)", "chịu phí" not in bat)
	dung("số tiền đúng", "1.224.000 đ" in bat)
	with patch.object(op, "cau_hinh", return_value=dict(C, bat=0)):
		tat = in_phieu("x")
	dung("tắt OnePay: phiếu như cũ, không ô thẻ", "OnePay" not in tat and "base64,CK" in tat)
	with patch.object(op, "cau_hinh", side_effect=RuntimeError("chưa migrate")):
		hong = in_phieu("x")
	dung("đọc cài đặt hỏng: phiếu vẫn in, không ô thẻ", "OnePay" not in hong and "base64,CK" in hong)
	for o in ("cong", "merchant", "access_code", "hash_code"):
		dung("thiếu ô %s là không in ô thẻ" % o, not op.dung_duoc(dict(C, bat=1, **{o: ""})))


# ------------------------------------------------ Codex #534 vòng 1 (3 finding)

def _trang(phieu, ck=True):
	"""Dựng trang /tra-the thật bằng Jinja (cùng tệp mẫu lên site)."""
	import jinja2

	env = jinja2.Environment(autoescape=False)
	ctx = {"csrf_token": "x", "ket_qua": None, "phieu": phieu, "ma": "DNTT261100002", "k": "0" * 16,
		"ck": {"ngan_hang": "MB", "stk": "123", "ten": "VAGABOND", "anh": ""} if ck else None}
	if phieu:
		ctx.update(op.cach_tra(phieu))
	return env.from_string(_doc("www", "tra-the.html")).render(**ctx)


@ca("Codex #534: còn nợ dưới 10.000 đ không được báo 'đã thanh toán đủ', vẫn hiện chuyển khoản; chỉ ẩn nút thẻ")
def _con_nho():
	p = {"ma_phieu": "DNTT-26-11-00002", "khach": "ABC", "huy": False, "dung_duoc": True}
	nho = _trang(dict(p, con=5000.0))
	dung("không báo đã trả đủ khi còn 5.000 đ", "đã được thanh toán đủ" not in nho)
	dung("còn khối chuyển khoản", "Hoặc chuyển khoản ngân hàng" in nho or "Chuyển khoản ngân hàng" in nho)
	dung("không có nút thẻ", 'id="nut-the"' not in nho)
	dung("nói rõ vì sao không trả thẻ", "10.000" in nho)
	du = _trang(dict(p, con=0.0))
	dung("trả đủ thì báo đã trả đủ", "đã được thanh toán đủ" in du and "chuyển khoản" not in du.lower().split("cần hỗ trợ")[0].split("số tiền còn phải thanh toán")[-1])
	lon = _trang(dict(p, con=500000.0))
	dung("số lớn: có nút thẻ và chuyển khoản", 'id="nut-the"' in lon and "chuyển khoản ngân hàng" in lon.lower())
	tat = _trang(dict(p, con=500000.0, dung_duoc=False))
	dung("tắt OnePay: không nút thẻ, còn chuyển khoản", 'id="nut-the"' not in tat and "chuyển khoản ngân hàng" in tat.lower())
	la("phép chọn", (op.cach_tra(dict(p, con=0.4))["da_du"], op.cach_tra(dict(p, con=1.0))["da_du"],
		op.cach_tra(dict(p, con=9999.0))["tra_the"], op.cach_tra(dict(p, con=10000.0))["tra_the"]), (True, False, False, True))


class _DbGia:
	def __init__(self, kho):
		self.kho = kho

	def get_value(self, dt, ten, o, **kw):
		return self.kho[ten]

	def set_value(self, dt, ten, o, v, **kw):
		self.kho[ten] = v

	def commit(self):
		pass

	def rollback(self):
		pass


@ca("Codex #534: quét tra cứu đi hết mọi phiếu có giao dịch chờ (không dừng ở 200), giao dịch chờ quá 2 ngày được cho hết hạn")
def _quet_het():
	import json
	import types
	from datetime import datetime
	from unittest.mock import patch

	bay_gio = datetime(2026, 11, 10, 12, 0, 0)
	cu = "2026-11-01 08:00:00"
	moi = "2026-11-10 11:00:00"
	kho = {}
	for i in range(250):
		kho["CN-%04d" % i] = json.dumps([{"ma": "DNTT26110%04d-1" % i, "so_tien": 100000, "tao_luc": cu, "trang_thai": "cho"}])
	for i in range(250, 260):
		kho["CN-%04d" % i] = json.dumps([{"ma": "DNTT26110%04d-1" % i, "so_tien": 100000, "tao_luc": moi, "trang_thai": "cho"}])

	def get_all(dt, filters=None, pluck=None, limit_page_length=0, order_by=None, **kw):
		ten = sorted(t for t, v in kho.items() if '"cho"' in v)
		sau = (filters or {}).get("name")
		if sau:
			ten = [t for t in ten if t > sau[1]]
		return ten[:limit_page_length] if limit_page_length else ten

	gia = types.SimpleNamespace(get_all=get_all, db=_DbGia(kho), log_error=lambda *a, **k: None,
		get_traceback=lambda: "", utils=types.SimpleNamespace(now_datetime=lambda: bay_gio))
	hoi = []
	with patch.object(op, "frappe", gia), patch.object(op, "cau_hinh", return_value=dict(C, bat=1)), \
			patch.object(op, "tra_cuu", side_effect=lambda ma: hoi.append(ma) or {"vpc_DRExists": "N"}):
		op.quet()
	la("hỏi đủ 10 giao dịch mới nằm sau 250 phiếu cũ", sorted(hoi), ["DNTT26110%04d-1" % i for i in range(250, 260)])
	la("giao dịch quá 2 ngày đã hết hạn, không còn chiếm lượt quét",
		sum(1 for v in kho.values() if '"cho"' in v), 10)
	la("phép phân loại", op.phan_loai_cho([{"ma": "A-1", "tao_luc": cu, "trang_thai": "cho"},
		{"ma": "A-2", "tao_luc": moi, "trang_thai": "cho"}, {"ma": "A-3", "tao_luc": "2026-11-10 11:55:00", "trang_thai": "cho"},
		{"ma": "A-4", "tao_luc": cu, "trang_thai": "da_ghi"}], "2026-11-08 12:00:00", "2026-11-10 11:45:00"), (["A-2"], ["A-1"]))


@ca("Codex #534: số ghi nhận là số phiếu thu ĐÃ GHI SỔ thật; hoá đơn bị trả chỗ khác thì phần dư báo kế toán")
def _doi_chieu():
	la("ghi đủ", op.doi_chieu_ghi(1000000, 1000000, 1000000), {"so_ghi": 1000000.0, "du": 0.0, "lech": False})
	la("hoá đơn đã trả bớt chỗ khác", op.doi_chieu_ghi(1000000, 1000000, 400000), {"so_ghi": 400000.0, "du": 600000.0, "lech": True})
	la("khách trả trùng, phiếu đã đủ", op.doi_chieu_ghi(500000, 0, 0), {"so_ghi": 0.0, "du": 500000.0, "lech": False})
	la("trả dư một phần", op.doi_chieu_ghi(500000, 200000, 200000), {"so_ghi": 200000.0, "du": 300000.0, "lech": False})
	# Nguồn: cong_no.ghi_nhan_the phải lấy số từ phiếu thu đã ghi sổ, không lấy số dự kiến.
	cn = _doc("cong_no.py")
	i = cn.index("def ghi_nhan_the(")
	than = cn[i:cn.index("\ndef ", i + 10)]
	dung("đọc lại phiếu thu đã ghi sổ của giao dịch", "_da_ghi_cho_gd(" in than and "doi_chieu_ghi(" in than)
	dung("không cộng số dự kiến vào đã thu", "flt(doc.da_thu) + so)" not in than)


@ca("Codex #534: chạy thật ghi_nhan_the trên Frappe giả: OnePay báo 1.000.000, phiếu thu thật 400.000 thì phiếu ghi 400.000, báo dư 600.000")
def _ghi_nhan_that():
	import json
	import types
	from unittest.mock import patch

	from vagabond import cong_no as cn

	class _Phieu(dict):
		__getattr__ = dict.get

		def __setattr__(self, k, v):
			self[k] = v

		def save(self, **kw):
			pass

		def add_comment(self, loai, noi_dung):
			self["ghi_chu"] = noi_dung

	doc = _Phieu(name="CN1", ma_phieu="DNTT-26-11-00002", tong_tien=1000000, da_thu=0, trang_thai="Cho thu", ma_gd="",
		ten_khach="ABC", khach="ABC", dong=[types.SimpleNamespace(hoa_don="HD1")], flags=types.SimpleNamespace(),
		onepay_gd=json.dumps([{"ma": "DNTT261100002-1", "so_tien": 1000000, "tao_luc": "x", "trang_thai": "cho"}]))
	kq = {"hop_le": True, "thanh_cong": True, "ma": "DNTT261100002-1", "so_tien": 1000000.0, "ma_onepay": "9"}
	lap = []
	so_lan_doc = []

	def get_all(dt, **kw):
		if dt == "Payment Entry":
			so_lan_doc.append(kw.get("filters"))
			return [{"name": "PE-1", "paid_amount": 400000}]
		return []

	with patch.object(cn.frappe, "get_doc", lambda *a, **k: doc, create=True), \
			patch.object(cn.frappe, "get_all", get_all, create=True), \
			patch.object(cn.frappe.db, "commit", lambda: None, create=True), \
			patch.object(cn, "_da_nhan_phieu", return_value=0.0), patch.object(cn, "_sepay_cn", return_value={}), \
			patch.object(cn, "ghi_thu_cho_phieu", side_effect=lambda *a, **k: lap.append(k.get("so_tien")) or ["PE-1"]), \
			patch.object(cn, "_ham_dinh_bien_nhan", return_value=None):
		cn.ghi_nhan_the("CN1", kq, "ipn")
	la("lập phiếu thu cho số dự kiến", lap, [1000000.0])
	dung("đọc lại phiếu thu đã ghi sổ theo khoá giao dịch", bool(so_lan_doc) and so_lan_doc[0]["docstatus"] == 1)
	g = json.loads(doc.onepay_gd)[0]
	la("phiếu và nhật ký ghi số thật", (doc.da_thu, doc.trang_thai, g["so_ghi"], g["du"]), (400000.0, "Thu thieu", 400000.0, 600000.0))
	dung("ghi chú báo phần dư cho kế toán", "phần dư 600.000 đ" in (doc.get("ghi_chu") or ""))


@ca("Codex #534 vòng 2: mọi hoá đơn đã được trả ở chỗ khác: IPN vẫn đi tiếp, ghi 0 đ, toàn bộ tiền thẻ là tiền dư báo kế toán; lỗi lập chứng từ thật vẫn ném")
def _het_no_cho_khac():
	import json
	import types
	from unittest.mock import patch

	from vagabond import cong_no as cn
	from vagabond import thu_tien as tt

	class _Phieu(dict):
		__getattr__ = dict.get

		def __setattr__(self, k, v):
			self[k] = v

		def save(self, **kw):
			pass

		def add_comment(self, loai, noi_dung):
			self["ghi_chu"] = noi_dung

	def _dung(con_no):
		doc = _Phieu(name="CN1", ma_phieu="DNTT-26-11-00002", tong_tien=1000000, da_thu=0, trang_thai="Cho thu", ma_gd="",
			ten_khach="ABC", khach="ABC", dong=[types.SimpleNamespace(hoa_don="HD1")], flags=types.SimpleNamespace(loi_thu=None),
			onepay_gd=json.dumps([{"ma": "DNTT261100002-1", "so_tien": 1000000, "tao_luc": "x", "trang_thai": "cho"}]))

		def get_all(dt, **kw):
			if dt == "Vagabond Cong No Dong":
				return [{"hoa_don": "HD1"}]
			if dt == "Sales Invoice":
				return [{"name": "HD1", "outstanding_amount": con_no, "posting_date": "2026-11-01"}] if con_no else []
			return []
		return doc, get_all

	kq = {"hop_le": True, "thanh_cong": True, "ma": "DNTT261100002-1", "so_tien": 1000000.0, "ma_onepay": "9"}
	doc, get_all = _dung(0)
	# ghi_thu_cho_phieu THẬT: không còn hoá đơn nào nợ.
	with patch.object(cn.frappe, "get_doc", lambda *a, **k: doc, create=True), \
			patch.object(cn.frappe, "get_all", get_all, create=True), \
			patch.object(cn.frappe.db, "commit", lambda: None, create=True), \
			patch.object(cn, "_da_nhan_phieu", return_value=0.0), patch.object(cn, "_sepay_cn", return_value={}), \
			patch.object(cn, "_ham_dinh_bien_nhan", return_value=None), \
			patch.object(tt, "phan_bo_nhap_theo_hd", return_value={}, create=True):
		ra = cn.ghi_nhan_the("CN1", kq, "ipn")
	g = json.loads(doc.onepay_gd)[0]
	la("đi tiếp, ghi 0 đ, dư toàn bộ", (ra.get("ok"), g["trang_thai"], g["so_ghi"], g["du"]), (1, "da_ghi", 0.0, 1000000.0))
	la("phiếu không đổi số đã thu", (doc.da_thu, doc.trang_thai), (0, "Cho thu"))
	dung("ghi chú báo phần dư 1.000.000 đ", "phần dư 1.000.000 đ" in (doc.get("ghi_chu") or ""))

	# Lập chứng từ hỏng thật thì vẫn ném, nhật ký giữ "chờ" để OnePay gọi lại.
	doc, get_all = _dung(400000)
	loi = ""
	with patch.object(cn.frappe, "get_doc", lambda *a, **k: doc, create=True), \
			patch.object(cn.frappe, "get_all", get_all, create=True), \
			patch.object(cn.frappe.db, "commit", lambda: None, create=True), \
			patch.object(cn, "_da_nhan_phieu", return_value=0.0), patch.object(cn, "_sepay_cn", return_value={}), \
			patch.object(cn, "_ham_dinh_bien_nhan", return_value=None), \
			patch.object(tt, "phan_bo_nhap_theo_hd", return_value={}, create=True), \
			patch.object(tt, "ghi_thu_tien", side_effect=RuntimeError("sổ khoá"), create=True):
		try:
			cn.ghi_nhan_the("CN1", kq, "ipn")
		except Exception as e:
			loi = str(e)
	dung("lỗi lập phiếu thu vẫn ném", "Chưa lập được phiếu thu" in loi)
	la("nhật ký vẫn chờ", json.loads(doc.onepay_gd)[0]["trang_thai"], "cho")
