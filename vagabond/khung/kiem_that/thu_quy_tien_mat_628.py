"""v628 Quỹ tiền mặt công ty: bút toán THẬT trên sổ cái. Chạy thật.

Codex #527 vòng 2 (SHA 204b484d2): các ca tầng khung thay `_lap_but_toan` bằng
hàm giả, nên chưa chứng minh ERPNext chấp nhận chứng từ, sổ cái ghi đúng tài
khoản, và huỷ phiếu thì sổ cái hoàn lại. AGENTS.md: thay đổi chạm GL Entry phải
có ca dựng chứng từ thật, insert rồi submit, đọc lại sổ cái.

Ca dưới chạy ĐÚNG các cửa màn Quỹ gọi (kiem_quy, duyet_kiem_quy, nop_ngan_hang,
huy_phieu). Chỉ thay: quyền người bấm, số quỹ máy đang tính (đã có ca riêng ở
thu_tai_chinh_626), tài khoản quỹ lấy từ tài khoản thử, Zalo và tệp đính kèm.
"""
from unittest.mock import patch

import frappe
from frappe.utils import add_days, flt, getdate, today

from vagabond import but_toan, kenh_zalo, tep_dinh_kem
from vagabond import quy_tien_mat as q
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi
from vagabond.khung.kiem_that.thu_tai_chinh_626 import _tk


def _gl(je):
	"""{tài khoản: (nợ, có)} của một bút toán, chỉ dòng chưa huỷ."""
	ra = {}
	for g in frappe.get_all("GL Entry", filters={"voucher_type": "Journal Entry", "voucher_no": je, "is_cancelled": 0},
			fields=["account", "debit", "credit"]):
		n, c = ra.get(g.account, (0.0, 0.0))
		ra[g.account] = (round(n + flt(g.debit), 2), round(c + flt(g.credit), 2))
	return ra


def _ghi_nho(kq):
	if kq and kq.get("name"):
		nen._DA_TAO.append((q.DT, kq["name"]))
		je = frappe.db.get_value(q.DT, kq["name"], "but_toan")
		if je:
			nen._DA_TAO.append(("Journal Entry", je))
	return kq


@ca("v628 Quỹ tiền mặt thật: kiểm quỹ lệch nhỏ, lệch lớn chờ duyệt (lần kiểm sau thay lần trước), nộp ngân hàng và huỷ phiếu đều ghi đúng sổ cái")
def _quy_that():
	cty = cong_ty()
	qua = add_days(getdate(today()), -1)
	tm = _tk(cty, "1111", "Asset", "Cash")
	thieu = _tk(cty, "1381", "Asset")
	thua = _tk(cty, "3381", "Liability")
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty))
	tk = {"tk_quy": tm, "tk_thieu": thieu, "tk_thua": thua}
	vo = [
		patch.object(but_toan, "_cty", lambda: cty),
		patch.object(q, "_kiem_lam", lambda: None),
		patch.object(q, "_tk_dung", lambda k: tk[k]),
		patch.object(q, "_so_quy", lambda: (10000000.0, {"ngay_chot": str(qua), "so_du": 10000000.0})),
		patch.object(q, "_tai_khoan_nh", lambda: [{"ma": ba.name, "ten": "MB kiểm 628", "tk": ba.account}]),
		patch.object(kenh_zalo, "bao_hoac_ghi_loi", lambda *a, **k: None),
		patch.object(tep_dinh_kem, "gan_vao", lambda *a, **k: []),
		patch.object(tep_dinh_kem, "doc_ds", lambda x: [{"ten": "giay-nop.jpg"}]),
		patch.object(tep_dinh_kem, "ghi_ds", lambda ds: ""),
	]
	for v in vo:
		v.start()
	try:
		# 1. Lệch nhỏ (thiếu 150.000): ghi bút toán ngay.
		a = _ghi_nho(khong_nem("kiểm quỹ thiếu 150.000", lambda: q.kiem_quy(
			bang='{"500000": "19", "200000": "1", "100000": "1", "50000": "1"}', ly_do="chi_chua_nhap", ghi_chu="kiểm 628")))
		if not a:
			return
		la("lệch nhỏ ghi ngay", (a["trang_thai"], a["lech"]), ("Đã ghi", -150000.0))
		je_a = frappe.db.get_value(q.DT, a["name"], "but_toan")
		la("sổ cái: Nợ 1381, Có quỹ 150.000", _gl(je_a), {thieu: (150000.0, 0.0), tm: (0.0, 150000.0)})
		# 2. Lệch lớn hai lần trên cùng số máy: lần một bị thay, chỉ duyệt lần hai.
		b1 = _ghi_nho(khong_nem("kiểm quỹ thiếu 3 triệu lần một", lambda: q.kiem_quy(
			bang='{"500000": "14"}', ly_do="chua_ro", ghi_chu="đếm lần một")))
		b2 = _ghi_nho(khong_nem("kiểm quỹ thiếu 3 triệu lần hai", lambda: q.kiem_quy(
			bang='{"500000": "14"}', ly_do="chua_ro", ghi_chu="đếm lần hai")))
		if not (b1 and b2):
			return
		la("lần hai chờ duyệt, chưa bút toán", (b2["trang_thai"], frappe.db.get_value(q.DT, b2["name"], "but_toan") or ""),
			("Chờ duyệt", ""))
		la("lần một bị thay", frappe.db.get_value(q.DT, b1["name"], "trang_thai"), q.THAY)
		for p in (b1, b2):
			frappe.db.set_value(q.DT, p["name"], "nguoi", "nguoi-kiem-khac@vagabond.test")
		with patch.object(q, "_la_giam_doc", lambda: True):
			try:
				q.duyet_kiem_quy(b1["name"], 1)
				dung("duyệt phiếu đã bị thay phải bị chặn", False)
			except frappe.ValidationError:
				pass
			d = khong_nem("Giám đốc duyệt lần hai", lambda: q.duyet_kiem_quy(b2["name"], 1))
		if not d:
			return
		nen._DA_TAO.append(("Journal Entry", d["but_toan"]))
		la("duyệt xong ghi sổ", d["trang_thai"], "Đã ghi")
		la("sổ cái: Nợ 1381, Có quỹ 3.000.000", _gl(d["but_toan"]), {thieu: (3000000.0, 0.0), tm: (0.0, 3000000.0)})
		la("phiếu bị thay không có bút toán", frappe.db.get_value(q.DT, b1["name"], "but_toan") or "", "")
		# 3. Nộp ngân hàng 2.000.000 rồi huỷ: sổ cái hoàn lại.
		n = _ghi_nho(khong_nem("nộp ngân hàng 2 triệu", lambda: q.nop_ngan_hang(
			so_tien="2.000.000", bank_account=ba.name, ngay=str(getdate(today())), anh="[]", nguoi_nop="kiểm 628")))
		if not n:
			return
		je_n = frappe.db.get_value(q.DT, n["name"], "but_toan")
		la("sổ cái: Nợ ngân hàng, Có quỹ 2.000.000", _gl(je_n), {ba.account: (2000000.0, 0.0), tm: (0.0, 2000000.0)})
		la("chờ tiền về", n["trang_thai"], "Chờ tiền về")
		if khong_nem("huỷ phiếu nộp", lambda: q.huy_phieu(n["name"], "ghi nhầm số")):
			la("bút toán đã huỷ", frappe.db.get_value("Journal Entry", je_n, "docstatus"), 2)
			la("sổ cái không còn dòng sống", _gl(je_n), {})
			la("phiếu đã huỷ", frappe.db.get_value(q.DT, n["name"], "trang_thai"), "Đã huỷ")
	finally:
		for v in vo:
			v.stop()
