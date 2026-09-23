"""Ca kiểm TÍCH HỢP cho nút Sinh lại chứng từ (v523, Codex #363 vòng 2).

Tầng khung đã chốt phần chọn hồ sơ, khoá và ghi lỗi bằng dữ liệu giả. Câu
chỉ tầng này trả lời được: đi đúng lối mới (hồ sơ đã khớp tiền ra, chứng từ
từng hỏng), ERPNext có THẬT SỰ nhận tờ trả hàng và phiếu chi không, sổ cái
có cân không, và tờ trả hàng có ra đúng số tiền hoàn trên một đơn có chiết
khấu tổng như ca thật HT-2026-02900 không.

Dựng lại đúng ca thật bằng chứng từ ảo: đơn tổng hàng 570.000, chiết khấu
tổng 135.000, khách trả 435.000, hoàn 90.000. Mọi thứ lùi về điểm lưu, xem
nen.py. Không chạm hoá đơn điện tử nào.

Giới hạn nói thẳng: một tiến trình bench không dựng được hai giao dịch
MariaDB chạy song song, nên phần SELECT ... FOR UPDATE chỉ được chốt ở tầng
khung bằng thứ tự xen kẽ giả lập, không phải ở đây.
"""

import frappe

from vagabond import hoan_tien
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, dung, khong_nem, la, so_cai_cua
from vagabond.khung.kiem_that.thu_cua_thue_243 import _mon, _nen


def _don_co_chiet_khau():
	ct, tk, _ = _nen()
	a, b = _mon(tk), _mon(tk)
	hd = frappe.get_doc(dict(
		doctype="Sales Invoice", company=ct, currency="VND", conversion_rate=1,
		customer=frappe.db.get_value("Customer", {"disabled": 0, "is_internal_customer": 0}, "name"),
		apply_discount_on="Grand Total", discount_amount=135000,
		items=[dict(item_code=a, qty=1, rate=300000), dict(item_code=b, qty=1, rate=270000)],
	))
	hd.insert(ignore_permissions=True)
	nen._DA_TAO.append((hd.doctype, hd.name))
	hd.flags.ignore_permissions = True
	hd.submit()
	hd.reload()
	return hd


def _ho_so_ket(hd):
	"""Hồ sơ đã khớp tiền ra mà chứng từ hỏng, đúng trạng thái HT-2026-02900."""
	hs = frappe.new_doc(hoan_tien.DT)
	hs.khach = hd.customer
	hs.hoa_don = hd.name
	hs.so_tien = 90000.0
	hs.ly_do = "Khac"
	hs.dien_giai = "Ca kiem tich hop v523, khong phai ho so that."
	hs.trang_thai = "Cho chi"
	hs.noi_dung_ck = hoan_tien.noi_dung_ck(hd.name)
	hs.flags.ignore_permissions = True
	hs.insert(ignore_permissions=True)
	nen._DA_TAO.append((hs.doctype, hs.name))
	# Trạng thái sau lượt khớp cũ: đã đối soát, có mã giao dịch, không chứng
	# từ, còn câu lỗi. Ghi thẳng như vòng khớp thật đã ghi.
	frappe.db.set_value(hoan_tien.DT, hs.name, {
		"da_doi_soat": 1, "ma_gd": "ACC-BTN-KIEM-523", "trang_thai": "Da doi soat",
		"loi_sinh_ct": "Tiền đã ra ... (ca kiểm v523)",
	})
	return hs.name


@ca("#523 sinh lại chứng từ: ERPNext nhận tờ trả hàng đúng 90.000 trên đơn có chiết khấu tổng, sổ cân")
def _sinh_lai_that():
	hd = khong_nem("lập đơn bán có chiết khấu tổng", _don_co_chiet_khau)
	if not hd:
		return
	la("đơn nguồn khách trả 435.000", round(float(hd.grand_total)), 435000)
	if not hoan_tien.kho_huy(hd.company):
		# Bench CI dựng mới có thể chưa có kho này; dựng trong điểm lưu, lùi
		# cùng mọi thứ khác. Site thật đã có sẵn.
		khong_nem("dựng Kho Hàng Hủy", lambda: hoan_tien.dung_kho_huy(hd.company))
	if not hoan_tien.kho_huy(hd.company):
		dung("site có Kho Hàng Hủy để chạy ca này", False)
		return
	ten = khong_nem("lập hồ sơ kẹt", lambda: _ho_so_ket(hd))
	if not ten:
		return

	kq = khong_nem("bấm Sinh lại chứng từ", lambda: hoan_tien.sinh_lai(ten))
	if not kq:
		return
	la("nút báo thành công", kq.get("ok"), 1)
	ho = frappe.get_doc(hoan_tien.DT, ten)
	la("câu lỗi được dọn", ho.loi_sinh_ct or "", "")
	dung("hồ sơ có tờ trả hàng", bool(ho.hoa_don_tra))
	if not ho.hoa_don_tra:
		return
	tra = frappe.get_doc("Sales Invoice", ho.hoa_don_tra)
	nen._DA_TAO.append((tra.doctype, tra.name))
	la("tờ trả hàng đã ghi sổ", int(tra.docstatus), 1)
	la("đúng là tờ trả hàng của đơn nguồn", (int(tra.is_return), tra.return_against), (1, hd.name))
	la("tờ trả hàng đúng 90.000", round(abs(float(tra.grand_total))), 90000)
	la("không chép chiết khấu tổng sang", float(tra.discount_amount or 0), 0.0)
	so = so_cai_cua(tra)
	dung("tờ trả hàng có bút toán sổ cái", len(so) > 0)
	la("sổ cái cân nợ có", round(sum(float(r.debit) for r in so)), round(sum(float(r.credit) for r in so)))
	if ho.phieu_chi:
		nen._DA_TAO.append(("Payment Entry", ho.phieu_chi))
		pe = frappe.get_doc("Payment Entry", ho.phieu_chi)
		la("phiếu chi để NHÁP chờ UNC", int(pe.docstatus), 0)
		la("phiếu chi đúng 90.000", round(float(pe.paid_amount)), 90000)
	else:
		dung("lập được phiếu chi (thiếu thì kiểm tài khoản ngân hàng chi hoàn)", False)

	# Bấm lần hai trên hồ sơ đã đủ chứng từ: phải bị từ chối, không lập thêm.
	try:
		hoan_tien.sinh_lai(ten)
		lot = True
	except Exception:
		lot = False
	dung("bấm lần hai bị từ chối", not lot)
	la("vẫn đúng một tờ trả hàng cho đơn", frappe.db.count("Sales Invoice",
		{"return_against": hd.name, "docstatus": 1}), 1)
