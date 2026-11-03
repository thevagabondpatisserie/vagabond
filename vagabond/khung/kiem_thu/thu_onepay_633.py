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
