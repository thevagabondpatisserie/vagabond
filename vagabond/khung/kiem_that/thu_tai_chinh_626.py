"""v626: phân hệ Tài chính đọc SỔ CÁI và GIAO DỊCH NGÂN HÀNG thật. Chạy thật.

Codex #524: tầng khung thay _so_cai_quy, _gl_ky, _phat_sinh_nh bằng số định
sẵn, nên không chứng minh được câu truy vấn đọc đúng GL Entry, đúng loại
chứng từ, đúng số hiệu tài khoản. AGENTS.md: đường đọc sổ cái phải có ca dựng
chứng từ thật, insert rồi submit, đọc lại.

Các ca dưới dựng tài khoản, bút toán, giao dịch ngân hàng THẬT trong điểm lưu
của nen.py, gọi đúng hàm màn Tài chính dùng, so phần TĂNG THÊM trước và sau
(site thật có sẵn số liệu cùng ngày nên không so tuyệt đối).
"""
import random
from unittest.mock import patch

import frappe
from frappe.utils import add_days, flt, getdate, today

from vagabond import tai_chinh as tc
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi


def _tk(cty, dau, goc, loai=None):
	"""Tài khoản chi tiết mới, số hiệu bắt đầu bằng `dau`, chỉ sống trong điểm lưu."""
	cha = frappe.db.get_value("Account", {"company": cty, "is_group": 1, "root_type": goc}, "name", order_by="lft desc")
	dung("công ty thử có nhóm tài khoản %s" % goc, bool(cha))
	for _i in range(5):
		so = dau + str(random.randint(10000, 99999))
		if not frappe.db.exists("Account", {"company": cty, "account_number": so}):
			break
	d = frappe.get_doc({"doctype": "Account", "company": cty, "parent_account": cha, "is_group": 0,
		"account_name": "Kiểm tài chính 626 " + frappe.generate_hash(length=8), "account_number": so,
		"root_type": goc, "account_type": loai, "account_currency": "VND"})
	d.insert(ignore_permissions=True)
	nen._DA_TAO.append((d.doctype, d.name))
	return d.name


def _but_toan(cty, no, co, tien, nhan):
	cc = frappe.db.get_value("Company", cty, "cost_center")
	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = cty
	je.posting_date = today()
	je.user_remark = "Kiểm tài chính 626: " + nhan
	je.append("accounts", {"account": no, "debit_in_account_currency": tien, "cost_center": cc})
	je.append("accounts", {"account": co, "credit_in_account_currency": tien, "cost_center": cc})

	def ghi():
		je.insert(ignore_permissions=True)
		nen._DA_TAO.append((je.doctype, je.name))
		je.submit()
		return je
	return khong_nem("bút toán " + nhan, ghi)


def _gd(ba, vao, ra, mo_ta, tham_chieu):
	g = frappe.get_doc({"doctype": "Bank Transaction", "date": today(), "bank_account": ba,
		"deposit": vao, "withdrawal": ra, "currency": "VND", "description": mo_ta,
		"reference_number": tham_chieu, "transaction_id": "KT626-" + frappe.generate_hash(length=12)})

	def ghi():
		g.insert(ignore_permissions=True)
		nen._DA_TAO.append((g.doctype, g.name))
		g.submit()
		return g
	return khong_nem("giao dịch ngân hàng " + mo_ta, ghi)


def _quy(kq):
	return next((d for d in kq["dong"] if d["nguon"] == tc.NGUON_QUY), None)


@ca("v626 sổ cái thật: thu chi tiền mặt bằng bút toán vào đúng quỹ công ty, chi quỹ theo ngày và lãi lỗ tháng")
def _so_cai():
	cty = cong_ty()
	hom = getdate(today())
	qua = add_days(hom, -1)
	tm = _tk(cty, "1111", "Asset", "Cash")
	dt = _tk(cty, "5111", "Income")
	gv = _tk(cty, "6321", "Expense")
	nv = _tk(cty, "6421", "Expense")
	tk_khac = _tk(cty, "711", "Income")
	# Mốc chốt quỹ hôm qua đi qua đúng cửa màn Cài đặt tài chính.
	moc = khong_nem("chốt số dư quỹ", lambda: tc.luu_moc(nguon=tc.NGUON_QUY, ngay_chot=str(qua),
		so_du="10.000.000", ghi_chu="kiểm 626"))
	if not moc:
		return
	nen._DA_TAO.append((tc.DT_MOC, moc["name"]))
	m = frappe.get_doc(tc.DT_MOC, moc["name"])
	la("mốc lưu đúng nguồn, loại, số", (m.nguon, m.loai, flt(m.so_du), str(m.ngay_chot)),
		(tc.NGUON_QUY, tc.LOAI_TM, 10000000.0, str(qua)))
	with patch.object(tc, "_sepay_so_bao", lambda: {}):
		t0 = tc._tinh_tien()
	q0, c0 = tc._so_cai_quy(qua), tc._chi_quy_theo_ngay(hom, hom).get(str(hom), 0.0)
	l0 = tc.lai_lo(tc._gl_ky(hom, hom))
	for no, co, tien, nhan in ((tm, dt, 1000000, "thu tiền mặt bán hàng"), (gv, tm, 400000, "chi giá vốn"),
			(nv, tm, 300000, "chi lương"), (tm, tk_khac, 50000, "thu khác")):
		if not _but_toan(cty, no, co, tien, nhan):
			return
	q1, c1 = tc._so_cai_quy(qua), tc._chi_quy_theo_ngay(hom, hom).get(str(hom), 0.0)
	la("quỹ: tiền vào sổ cái tăng", round(q1[0] - q0[0], 2), 1050000.0)
	la("quỹ: tiền ra sổ cái tăng", round(q1[1] - q0[1], 2), 700000.0)
	la("dòng tiền: chi quỹ hôm nay tăng", round(flt(c1) - flt(c0), 2), 700000.0)
	l1 = tc.lai_lo(tc._gl_ky(hom, hom))
	for k, mong in (("doanh_thu", 1000000.0), ("gia_von", 400000.0), ("cp_quan_ly", 300000.0),
			("nhan_vien", 300000.0), ("khac", 50000.0), ("lai_rong", 350000.0)):
		la("lãi lỗ: %s tăng" % k, round(flt(l1[k]) - flt(l0[k]), 2), mong)
	with patch.object(tc, "_sepay_so_bao", lambda: {}):
		t1 = tc._tinh_tien()
	a, b = _quy(t0), _quy(t1)
	dung("có dòng quỹ công ty", bool(a and b))
	if a and b:
		la("quỹ tính từ đúng mốc vừa chốt", (b.get("moc") or {}).get("ngay_chot"), str(qua))
		la("số dư quỹ tăng đúng thu trừ chi", round(flt(b["so_du"]) - flt(a["so_du"]), 2), 350000.0)


@ca("v626 giao dịch ngân hàng thật: phát sinh sau mốc; chỉ cặp chung lệnh là chuyển nội bộ, khách và NCC trùng tiền giữ nguyên")
def _ngan_hang():
	cty = cong_ty()
	hom = getdate(today())
	goc = _tk_ngan_hang(cty)
	a = _tai_khoan_cong_ty_moi(goc).name
	b = _tai_khoan_cong_ty_moi(goc).name
	ref = "FTKT626" + frappe.generate_hash(length=8).upper()
	for ba, vao, ra, mo_ta, tc_ in (
			(a, 0, 5000000, "VAGABOND KT626 NAP QUY TAM UNG THANG 10", ref),
			(b, 5000000, 0, "VAGABOND KT626 NAP QUY TAM UNG THANG 10", ref),
			(a, 665000, 0, "Qanehu5840 PANCAKE2278 KT626 khach chuyen", "FTKT626A" + frappe.generate_hash(length=6)),
			(b, 0, 665000, "VGB TT DH KT626 NCC", "FTKT626B" + frappe.generate_hash(length=6))):
		if not _gd(ba, vao, ra, mo_ta, tc_):
			return
	la("phát sinh tài khoản A sau hôm qua", tc._phat_sinh_nh(a, add_days(hom, -1)), (665000.0, 5000000.0, 2))
	la("không tính giao dịch của chính ngày chốt", tc._phat_sinh_nh(a, hom), (0.0, 0.0, 0))
	gd = tc._gd_ngan_hang(hom, hom, [{"bank_account": a, "ten": "A", "dong_bo": 1},
		{"bank_account": b, "ten": "B", "dong_bo": 1}])
	la("đọc đủ bốn giao dịch kèm mã tham chiếu", sorted((g["tk"] == a, g["vao"], g["ra"], bool(g.get("tham_chieu"))) for g in gd),
		sorted([(True, 0.0, 5000000.0, True), (False, 5000000.0, 0.0, True), (True, 665000.0, 0.0, True), (False, 0.0, 665000.0, True)]))
	ngoai, nb = tc.tach_noi_bo(gd)
	la("một cặp nội bộ đúng chiều", [(x["tu"], x["den"], x["so"]) for x in nb], [(a, b, 5000000.0)])
	la("khách vào A và NCC ra B cùng số tiền vẫn là tiền vào, tiền ra",
		sorted((g["vao"], g["ra"]) for g in ngoai), [(0.0, 665000.0), (665000.0, 0.0)])


@ca("v626 Codex #524: phiếu thu tiền mặt tại quầy đã vào két thì KHÔNG cộng lần nữa vào quỹ công ty")
def _thu_quay():
	from vagabond import tra_truoc_khach as tk
	from vagabond.khung.kiem_that.thu_tra_truoc_khach_607 import _nap
	from vagabond.khung.kiem_that.thu_tra_truoc_khach_607 import _nen as _nen_607
	cty, _tien, _mon, kh = _nen_607()
	hom = getdate(today())
	qua = add_days(hom, -1)
	# Tiền mặt tại quầy đi vào đúng một tài khoản 111x như site thật
	# (Mode of Payment "Tiền mặt" -> 1111 Tiền Việt Nam).
	tm = _tk(cty, "1111", "Asset", "Cash")
	mp = frappe.get_doc("Mode of Payment", "Tiền mặt")
	for r in mp.accounts:
		if r.company == cty:
			r.default_account = tm
	mp.save(ignore_permissions=True)
	frappe.clear_document_cache("Mode of Payment", "Tiền mặt")
	q0 = tc._so_cai_quy(qua)
	truoc = flt((tk.thu_nap_tai_quay("TCV", "%s 00:00:00" % hom, "%s 23:59:59" % hom) or {}).get("Tiền mặt"))
	pe = khong_nem("nạp tiền mặt tại quầy", lambda: _nap(kh, 500000, "tien_mat", "TCV"))
	if not pe:
		return
	gl = nen.so_cai_cua(pe)
	la("phiếu thu tại quầy ghi Nợ đúng tài khoản 1111", sum(flt(g.debit) for g in gl if g.account == tm), 500000.0)
	sau = flt((tk.thu_nap_tai_quay("TCV", "%s 00:00:00" % hom, "%s 23:59:59" % hom) or {}).get("Tiền mặt"))
	la("két quầy TCV đã cộng phiếu này", round(sau - truoc, 2), 500000.0)
	q1 = tc._so_cai_quy(qua)
	la("quỹ công ty không cộng lần hai", (round(q1[0] - q0[0], 2), round(q1[1] - q0[1], 2)), (0.0, 0.0))
	# Thu tiền mặt bằng bút toán của kế toán (không qua quầy) thì vẫn là quỹ.
	dt = _tk(cty, "711", "Income")
	if _but_toan(cty, tm, dt, 80000, "thu khác vào quỹ"):
		q2 = tc._so_cai_quy(qua)
		la("bút toán thu vào quỹ vẫn được cộng", round(q2[0] - q1[0], 2), 80000.0)


@ca("v626 Codex #524: lập phiếu đòi nợ không làm khoản Khách nợ mình biến khỏi Tài chính")
def _phai_thu_gom():
	from vagabond import cong_no as cn
	from vagabond import thu_tien as tt
	from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen as _nen_243
	from vagabond.khung.kiem_that.thu_gom_phap_nhan_576 import _hd, _khach, _phieu
	cty, tk_thue, _mau = _nen_243()
	kh = _khach("Tài chính 626")
	si = _hd(tk_thue, cty, 5000000, kh)
	tien = flt(si.outstanding_amount)
	dung("hoá đơn còn nợ trên sổ cái", tien > 0)
	# Bench #437: đơn GrabFood không nhận phương thức "Công nợ" ở cửa lưu.
	# Cho riêng tờ thử này đi đường "có dòng công nợ" của ds_khach_no; mọi
	# câu đọc sổ cái, phép chia nợ và phép loại tờ đã gom vẫn chạy thật.
	goc_dong, goc_la = tt.si_co_dong_cong_no, tt.la_cong_no
	with patch.object(tt, "si_co_dong_cong_no", lambda: list(goc_dong() or []) + [si.name]), \
		patch.object(tt, "la_cong_no", lambda pt: pt == si.vgb_pt_thanh_toan or goc_la(pt)):
		truoc = cn.ds_khach_no()
		pt_truoc = tc._phai_thu()
		la("Tài chính tính đủ nợ trước khi gom", round(pt_truoc - flt(truoc["tong"]), 2),
			round(flt(truoc["tong_ca_phieu"]) - flt(truoc["tong"]), 2))
		p = khong_nem("lập phiếu đòi nợ", lambda: _phieu([si], kh))
		if not p:
			return
		sau = cn.ds_khach_no()
		pt_sau = tc._phai_thu()
	la("màn Công nợ bỏ tờ đã gom khỏi số còn gom được", round(flt(truoc["tong"]) - flt(sau["tong"]), 2), tien)
	la("Tài chính vẫn giữ khoản nợ đó", round(pt_sau - pt_truoc, 2), 0.0)
	la("tổng kể cả phiếu không đổi khi gom", round(flt(sau["tong_ca_phieu"]) - flt(truoc["tong_ca_phieu"]), 2), 0.0)
