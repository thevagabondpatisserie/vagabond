"""Trang khách trả phiếu đề nghị thanh toán bằng thẻ qua OnePay (v633).

Mã QR "Thẻ" in trên phiếu trỏ về đây: /tra-the/<mã phiếu bỏ gạch>?k=<khoá>.
Khoá sai thì trang như không có phiếu. OnePay trả khách về đúng trang này kèm
tham số vpc_ (ve=1): kiểm chữ ký rồi ghi tiền (cùng một cửa với IPN, lặp lại
không ghi hai lần), rồi hiện kết quả và số còn phải trả mới."""
import re

import frappe

no_cache = 1


def get_context(context):
	from vagabond import onepay as op

	context.no_cache = 1
	context.csrf_token = frappe.sessions.get_csrf_token()
	fd = frappe.form_dict or {}
	ma = str(fd.get("ma") or "").strip()
	if not ma:
		# Đường /tra-the/<ma>: Frappe đặt phần sau vào form_dict theo luật định tuyến.
		duong = str(getattr(frappe.local, "request", None) and frappe.local.request.path or "")
		m = re.search(r"/tra-the/([A-Za-z0-9]+)", duong)
		ma = m.group(1) if m else ""
	k = str(fd.get("k") or "").strip()
	context.ket_qua = None
	if str(fd.get("ve") or "") == "1" and fd.get("vpc_SecureHash"):
		ts = {x: v for x, v in fd.items() if x.startswith("vpc_") or x.startswith("user_")}
		try:
			r = op.ghi_nhan(ts, "trang_ve")
			kq = r.get("kq") or {}
			context.ket_qua = {"thanh_cong": bool(kq.get("thanh_cong")), "cau": kq.get("cau") or "",
				"so_tien": kq.get("so_tien") or 0}
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "onepay: trang về")
			context.ket_qua = {"thanh_cong": False, "cau": "Chưa ghi nhận được kết quả. Nếu thẻ đã bị trừ tiền, "
				"The Vagabond sẽ tự đối chiếu với OnePay; quý khách không cần trả lại.", "so_tien": 0}
	context.phieu = op.thong_tin_trang(ma, k)
	context.ma = ma
	context.k = k
	if context.phieu:
		try:
			from vagabond import cong_no, qr_chuyen_khoan, tai_khoan

			tk = tai_khoan.tk_phieu_no()
			context.ck = {"ngan_hang": cong_no.TEN_NGAN_HANG_DAY_DU.get(tk.get("bank") or "", tk.get("bank") or ""),
				"stk": tk.get("stk") or "", "ten": tk.get("ten") or "",
				"anh": qr_chuyen_khoan.anh_qr(tk, context.phieu["con"], context.phieu["ma_phieu"])}
		except Exception:
			frappe.log_error(frappe.get_traceback(), "onepay: trang trả thẻ, khối chuyển khoản")
			context.ck = None
	return context
