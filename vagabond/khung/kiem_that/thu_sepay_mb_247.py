"""#247: Bank Account cá nhân MB đi trọn đường SePay trên ERPNext thật.

Ca kiểm dựng tài khoản cá nhân trong điểm lưu, không dùng số tài khoản hay
khoá thật và không gọi ra SePay. Giao dịch giả phải vào đúng Bank Account,
chạy lại không sinh đôi, còn tài khoản phải hiện đúng ở luồng hoàn ứng.
"""

from unittest.mock import patch

import frappe
from frappe.utils import now_datetime, today

from vagabond import ho_so_tt, sepay
from vagabond.khung.kiem_that.nen import (
	_DA_TAO, _mot, ca, cong_ty, dung, la, mot_nha_cung_cap,
)


def _so_thu():
	"""Dãy số chỉ sống trong savepoint, đủ khác nhau giữa các lượt kiểm."""
	return "247" + now_datetime().strftime("%H%M%S%f")[-11:]


def _bank_mb():
	"""Lấy đúng danh mục MB; nếu bench thiếu thì dựng bằng nguồn Napas chuẩn."""
	from vagabond.ngan_hang import chuan_hoa_hoac_bao

	truoc = set(frappe.get_all("Bank", pluck="name", limit_page_length=0))
	ten = chuan_hoa_hoac_bao("MB")
	if ten not in truoc:
		_DA_TAO.append(("Bank", ten))
	return ten


def _tai_khoan_ca_nhan(so_tk, ncc):
	cty = cong_ty()
	tk_141 = _mot("Account", {
		"company": cty, "is_group": 0, "disabled": 0,
		"name": ["like", "141%"],
	})
	if not tk_141:
		frappe.throw(
			"Công ty thử chưa có tài khoản con nhóm 141 để kiểm luồng hoàn ứng MB."
		)
	b = frappe.get_doc({
		"doctype": "Bank Account",
		"account_name": "Kiểm MB cá nhân " + frappe.generate_hash(length=8),
		"bank": _bank_mb(),
		"bank_account_no": so_tk,
		"account": tk_141,
		"is_company_account": 0,
		"party_type": "Supplier",
		"party": ncc,
	})
	b.insert(ignore_permissions=True)
	_DA_TAO.append((b.doctype, b.name))
	return b


@ca("#247 MB cá nhân: map, nạp bù và retry đi trọn ERPNext không sinh đôi")
def _mb_ca_nhan():
	cu = frappe.session.user
	frappe.set_user("Administrator")
	try:
		ncc = mot_nha_cung_cap()
		if not ncc:
			frappe.throw("Site thử chưa có Supplier để gắn người hoàn ứng MB.")
		so_tk = _so_thu()
		b = _tai_khoan_ca_nhan(so_tk, ncc)

		trang = sepay.tinh_trang()
		dong = [x for x in trang["ds_tai_khoan"] if x["ma"] == b.name]
		la("tài khoản cá nhân hiện trong bản đồ", len(dong), 1)
		la("bản đồ giữ đúng người", dong[0]["chu"], ncc)
		la("không biến thành tài khoản công ty", dong[0]["la_cong_ty"], 0)

		frappe.db.set_single_value(
			"Vagabond Settings", "sepay_chua_map", "000000,%s" % so_tk
		)
		kq_map = sepay.them_tai_khoan(" ".join((so_tk[:6], so_tk[6:])), b.name)
		la("map đúng Bank Account cá nhân", kq_map["ban_do"].get(so_tk), b.name)
		la("số vừa map rời danh sách chờ", so_tk in (sepay.cfg().get("sepay_chua_map") or ""), False)
		dung("tài khoản hiện ở luồng hoàn ứng", any(
			x["ma"] == b.name and x["nguoi"] == ncc
			for x in ho_so_tt.ds_tk_hoan_ung(ncc)["tk"]
		))

		ma_gd = int(now_datetime().strftime("%d%H%M%S%f")[-14:])
		giao_dich = [{
			"id": ma_gd,
			"account_number": " ".join((so_tk[:5], so_tk[5:])),
			"transaction_date": str(today()) + " 10:10:10",
			"amount_in": 0,
			"amount_out": 247000,
			"transaction_content": "KIEM THU MB HOAN UNG ISSUE 247",
			"reference_number": "KIEM-247",
		}]
		with patch.object(sepay, "_goi_userapi", return_value=giao_dich):
			lan_dau = sepay.nap_bu(
				so_tk=so_tk, tu_ngay=today(), den_ngay=today(), so_trang=1, that=1
			)
			lan_hai = sepay.nap_bu(
				so_tk=so_tk, tu_ngay=today(), den_ngay=today(), so_trang=1, that=1
			)

		ma = sepay.TIEN_TO + str(ma_gd)
		bt = frappe.db.get_value("Bank Transaction", {"transaction_id": ma}, "name")
		dung("lần đầu tạo sao kê", bool(bt))
		if bt:
			_DA_TAO.append(("Bank Transaction", bt))
			doc = frappe.get_doc("Bank Transaction", bt)
			la("sao kê vào đúng MB cá nhân", doc.bank_account, b.name)
			la("giữ đúng chiều tiền ra", float(doc.withdrawal), 247000.0)
			la("không đổi thành tiền vào", float(doc.deposit), 0.0)
		la("lần đầu thêm một dòng", lan_dau["them"], 1)
		la("retry không thêm dòng", lan_hai["them"], 0)
		la("retry nhận đúng giao dịch đã có", lan_hai["da_co"], 1)
		la("chỉ một transaction_id", frappe.db.count(
			"Bank Transaction", {"transaction_id": ma}
		), 1)
	finally:
		frappe.set_user(cu)
