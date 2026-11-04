# -*- coding: utf-8 -*-
"""v634: tra cứu giao dịch OnePay (QueryDR) theo địa chỉ OnePay cấp cho
VAGABONDWEB, và điểm nhận IPN không xác nhận khi chưa dán khoá.

Bản v633 đoán địa chỉ tra cứu .../Vpcdps.op theo tài liệu nội địa cũ; trên
site thật lệnh quét chạy mà không báo lỗi, không phân biệt được "OnePay nói
không có giao dịch" với "gọi nhầm chỗ". Nay địa chỉ đúng, và phản hồi không
đọc được thì ném kèm phản hồi đã che để Error Log cho thấy ngay.
"""

import json
import types
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import onepay as op  # noqa: E402

KHOA = "0123456789ABCDEF0123456789ABCDEF"
C = {"bat": 1, "cong": "https://onepay.vn/paygate/vpcpay.op\t", "merchant": "VAGABONDWEB", "access_code": "ABCD1234",
	"hash_code": KHOA, "query_user": "op01", "query_password": "mk-bi-mat"}


class _Dap:
	def __init__(self, ma, chu):
		self.status_code = ma
		self.text = chu


class _Req:
	"""requests giả: ghi lại mọi lượt gọi, trả phản hồi theo cách gọi."""

	def __init__(self, post=None, get=None):
		self.goi = []
		self._post, self._get = post, get

	def post(self, url, data=None, timeout=None):
		self.goi.append(("post", url, dict(data or {})))
		if isinstance(self._post, Exception):
			raise self._post
		return self._post

	def get(self, url, params=None, timeout=None):
		self.goi.append(("get", url, dict(params or {})))
		if isinstance(self._get, Exception):
			raise self._get
		return self._get


@ca("v634 OnePay: địa chỉ tra cứu đúng địa chỉ OnePay cấp, cả cổng thật lẫn cổng thử, chịu ô dán thừa ký tự")
def _dia_chi():
	la("cổng thật (ô dán thừa dấu tab)", op.cong_tra_cuu(C["cong"]), "https://onepay.vn/msp/api/v1/vpc/invoices/queries")
	la("cổng thử", op.cong_tra_cuu("mtf.onepay.vn/paygate/vpcpay.op?x=1"), "https://mtf.onepay.vn/msp/api/v1/vpc/invoices/queries")
	la("trống", op.cong_tra_cuu(""), "")


@ca("v634 OnePay: tra cứu gửi POST đủ tham số đã ký tới đúng địa chỉ; POST không đọc được thì thử GET; cả hai hỏng thì ném, không lộ mật khẩu")
def _tra_cuu():
	dap = "vpc_DRExists=Y&vpc_TxnResponseCode=0&vpc_MerchTxnRef=DNTT260900014-2&vpc_Amount=16650000"
	rq = _Req(post=_Dap(200, dap))
	with patch.object(op, "requests", rq), patch.object(op, "cau_hinh", return_value=C):
		kq = op.tra_cuu("DNTT260900014-2")
	la("đọc được kết quả", (kq["vpc_DRExists"], kq["vpc_TxnResponseCode"]), ("Y", "0"))
	la("một lượt POST tới đúng địa chỉ", [(g[0], g[1]) for g in rq.goi], [("post", "https://onepay.vn/msp/api/v1/vpc/invoices/queries")])
	ts = rq.goi[0][2]
	la("đủ tham số", sorted(ts), ["vpc_AccessCode", "vpc_Command", "vpc_MerchTxnRef", "vpc_Merchant", "vpc_Password",
		"vpc_SecureHash", "vpc_User", "vpc_Version"])
	la("lệnh queryDR, đúng mã", (ts["vpc_Command"], ts["vpc_MerchTxnRef"]), ("queryDR", "DNTT260900014-2"))
	dung("đã ký đúng", op.dung_chu_ky(ts, KHOA))

	rq = _Req(post=_Dap(405, "<html>Method Not Allowed</html>"), get=_Dap(200, dap))
	with patch.object(op, "requests", rq), patch.object(op, "cau_hinh", return_value=C):
		kq = op.tra_cuu("DNTT260900014-2")
	la("POST hỏng thì GET", ([g[0] for g in rq.goi], kq["vpc_DRExists"]), (["post", "get"], "Y"))

	rq = _Req(post=_Dap(200, "<html>Paygate</html>"), get=_Dap(200, "vpc_User=op01&vpc_Password=mk-bi-mat&loi=sai-tham-so"))
	loi = ""
	with patch.object(op, "requests", rq), patch.object(op, "cau_hinh", return_value=C):
		try:
			op.tra_cuu("DNTT260900014-2")
		except ValueError as e:
			loi = str(e)
	dung("trang HTML 200 không bị coi là 'không có giao dịch': ném", "không đọc được" in loi)
	dung("lỗi nêu địa chỉ đã gọi", "msp/api/v1/vpc/invoices/queries" in loi)
	dung("không lộ mật khẩu trong Error Log", "mk-bi-mat" not in loi and "op01" not in loi)

	la("JSON phẳng cũng đọc được", op.doc_tra_cuu('{"vpc_DRExists": "N", "vpc_TxnResponseCode": null}'),
		{"vpc_DRExists": "N", "vpc_TxnResponseCode": ""})
	la("JSON bọc một lớp", op.doc_tra_cuu('{"data": {"vpc_DRExists": "Y"}}'), {"vpc_DRExists": "Y"})
	la("HTML là rỗng", op.doc_tra_cuu("<!doctype html><p>x=1</p>"), {})


@ca("v634 OnePay: phản hồi tra cứu không chữ ký được tin (máy tiệm tự gọi OnePay qua HTTPS); có chữ ký thì phải đúng; trang về và IPN vẫn bắt buộc chữ ký")
def _tin_cay():
	ts = {"vpc_MerchTxnRef": "DNTT260900014-2", "vpc_Amount": "16650000", "vpc_TxnResponseCode": "0"}
	la("tra cứu không chữ ký: hợp lệ, thành công", [op.doc_ket_qua(ts, KHOA, tin_cay=True)[k] for k in ("hop_le", "thanh_cong")], [True, True])
	la("trang về, IPN không chữ ký: không hợp lệ", op.doc_ket_qua(ts, KHOA)["hop_le"], False)
	gia = dict(ts, vpc_SecureHash="AB" * 32)
	la("tra cứu có chữ ký sai: không hợp lệ", op.doc_ket_qua(gia, KHOA, tin_cay=True)["hop_le"], False)
	that = dict(ts, vpc_SecureHash=op.ky(ts, KHOA))
	la("tra cứu có chữ ký đúng: hợp lệ", op.doc_ket_qua(that, KHOA, tin_cay=True)["hop_le"], True)


@ca("v634 OnePay: lượt quét ghi kết quả tra cứu với tin_cay, bỏ kết quả của giao dịch khác, ghi Error Log khi phản hồi lạ")
def _quet():
	kho = {"CN-1": json.dumps([{"ma": "DNTT260900014-2", "so_tien": 166500, "tao_luc": "2026-11-03 18:48:00", "trang_thai": "cho"}])}
	from datetime import datetime

	nhat = []
	loi = []

	def get_all(dt, filters=None, limit_page_length=0, **kw):
		# v637: quét đi cả phiếu đặt (đơn đặt trước); ca này chỉ có phiếu công nợ.
		if dt != op.CN:
			return []
		sau = (filters or {}).get("name")
		return [t for t in sorted(kho) if not sau or t > sau[1]]

	gia = types.SimpleNamespace(get_all=get_all, log_error=lambda *a, **k: loi.append(a), get_traceback=lambda: "tb",
		db=types.SimpleNamespace(get_value=lambda dt, ten, o, **k: kho[ten], set_value=lambda *a, **k: None,
			commit=lambda: None, rollback=lambda: None),
		utils=types.SimpleNamespace(now_datetime=lambda: datetime(2026, 11, 3, 19, 16)))

	def chay(phan_hoi):
		del nhat[:], loi[:]
		with patch.object(op, "frappe", gia), patch.object(op, "cau_hinh", return_value=C), \
				patch.object(op, "tra_cuu", side_effect=phan_hoi), \
				patch.object(op, "ghi_nhan", side_effect=lambda ts, nguon, tin_cay=False: nhat.append((ts["vpc_MerchTxnRef"], nguon, tin_cay))):
			op.quet()

	chay(lambda ma: {"vpc_DRExists": "Y", "vpc_TxnResponseCode": "0", "vpc_MerchTxnRef": ma})
	la("có giao dịch: ghi với tin_cay", nhat, [("DNTT260900014-2", "tra_cuu", True)])
	chay(lambda ma: {"vpc_DRExists": "Y", "vpc_TxnResponseCode": "0", "vpc_MerchTxnRef": "DNTT260900099-1"})
	la("kết quả của giao dịch khác: không ghi", nhat, [])
	dung("và ghi Error Log", len(loi) == 1)
	chay(lambda ma: {"vpc_DRExists": "N"})
	la("không có giao dịch: không ghi, không lỗi", (nhat, loi), ([], []))

	def hong(ma):
		raise ValueError("Phản hồi tra cứu OnePay không đọc được")
	chay(hong)
	dung("phản hồi lạ: Error Log", len(loi) == 1 and "tra cứu" in str(loi[0]))


@ca("v634 OnePay: chưa dán khoá thì IPN KHÔNG trả 'đã nhận' (OnePay gọi lại sau khi dán khoá)")
def _ipn_chua_khoa():
	import sys

	wz = types.ModuleType("werkzeug.wrappers")

	class Response:
		def __init__(self, chu, mimetype=None):
			self.chu = chu
	wz.Response = Response
	with patch.dict(sys.modules, {"werkzeug.wrappers": wz}), \
			patch.object(op, "cau_hinh", return_value=dict(C, hash_code="")):
		la("chưa khoá", op.ipn(vpc_MerchTxnRef="X-1", vpc_SecureHash="AA").chu, op.DAP_IPN_CHUA_KHOA)
	dung("không phải câu xác nhận", op.DAP_IPN_CHUA_KHOA.startswith("responsecode=0"))
	with patch.dict(sys.modules, {"werkzeug.wrappers": wz}), patch.object(op, "cau_hinh", return_value=C):
		la("có khoá, chữ ký giả", op.ipn(vpc_MerchTxnRef="X-1", vpc_SecureHash="AA").chu, op.DAP_IPN_SAI)


@ca("Codex #535: phản hồi lạ ghi Error Log không lộ trọn giá trị bí mật: JSON có dấu phẩy, khoảng trắng, HTML input, k=v có cách; giá trị bí mật đã biết bị xoá ở mọi chỗ")
def _che_bi_mat():
	bm = ("alpha,beta", "op01", "ABCD1234", KHOA)
	ca_thu = [
		('{"vpc_Password": "alpha,beta", "vpc_DRExists": ""}', "alpha"),
		('{"vpc_Password":"a b c","vpc_User":"op01"}', "a b c"),
		('<input name="vpc_Password" value="alpha-beta">', "alpha-beta"),
		("<input type=hidden name='vpc_AccessCode' value='ABCD1234'>", "ABCD1234"),
		("vpc_Password = alpha beta&x=1", "beta"),
		("vpc_User=op01&vpc_Password=mk&vpc_SecureHash=AB12&ok=1", "AB12"),
		("<p>Lỗi xác thực op01 / alpha,beta</p>", "alpha,beta"),
	]
	for chuoi, khong_duoc_con in ca_thu:
		ra = op.tom_tat_phan_hoi(chuoi, bi_mat=bm)
		dung("che hết '%s' trong %s" % (khong_duoc_con, chuoi[:40]), khong_duoc_con not in ra and "op01" not in ra)
	la("phần không bí mật giữ nguyên để đọc lỗi", op.tom_tat_phan_hoi("vpc_DRExists=&loi=sai-tham-so"), "vpc_DRExists=&loi=sai-tham-so")

	# Đi đúng đường thật: tra_cuu ném lỗi chứa phản hồi đã che.
	rq = _Req(post=_Dap(200, '<form><input name="vpc_Password" value="mk-bi-mat"></form>'),
		get=_Dap(200, '<p>Sai mật khẩu mk-bi-mat cho tài khoản op01</p>'))
	loi = ""
	with patch.object(op, "requests", rq), patch.object(op, "cau_hinh", return_value=C):
		try:
			op.tra_cuu("DNTT260900014-2")
		except ValueError as e:
			loi = str(e)
	# Ca GET là chữ tự do: chỉ lớp xoá giá trị đã biết che được (lớp mẫu ô không bắt).
	dung("lỗi thật không chứa mật khẩu, tài khoản", bool(loi) and "mk-bi-mat" not in loi and "op01" not in loi)
