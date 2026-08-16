"""Ten goi chung tu tien theo tai khoan, va luat bat buoc dinh kem.

Chi Dung chot 16/08/2026, sau khi doc lai luong hoan tien
---------------------------------------------------------
"Phieu thu / phieu chi" la chung tu cua QUY TIEN MAT, gan voi tai khoan
111. Mot giao dich qua ngan hang thi chung tu goc la Uy nhiem chi minh gui
ngan hang, cong Giay bao No ngan hang gui lai.

Truoc do he nay dich Payment Entry thanh "phieu thu chi" cho MOI truong
hop - mot cai ten cho ca tien mat lan ngan hang. But toan khong sai (van
ghi Co 11211 chu khong phai 111), nhung ke toan mo mot giao dich chuyen
khoan ra lai thay chu "phieu chi".

Va mot chuyen dang ghi lai: em de xuat cong nhan dong sao ke SePay la
Giay bao No dien tu, de ke toan khoi phai tai tep tay. CHI DUNG TU CHOI.
Ly do chi dua ra: SePay la dich vu trung gian xem bien dong nhanh, khong
phai chung tu cua ngan hang. Lam viec voi Cuc Thue thi bat buoc phai co
tep Uy nhiem chi tai truc tiep tu e-banking.

Nen doi soat SePay van giu nguyen, nhung no la CONG CU QUAN TRI de biet
tien da di chua, KHONG phai chung tu phap ly. Ho so phap ly la tep dinh
kem, va tu nay khong co tep thi khong ghi so duoc.
"""

import frappe
from frappe.utils import cint, flt

PE = "Payment Entry"

# Ngay chot luat moi. Chung tu lap TRUOC ngay nay khong bi ap.
#
# Vi sao phai co moc: doi luat cho chung tu qua khu la dung vao dung cai
# anh Viet cam ngay 13/08/2026. Chung tu da ghi so giu nguyen ten nguyen
# so; luat moi chi soi vao cai lap tu hom nay tro di.
NGAY_CHOT = "2026-08-16"


TRUONG_MOI = {
	PE: [
		{
			"fieldname": "vgb_loai_ct",
			"label": "Loại chứng từ",
			"fieldtype": "Data",
			"insert_after": "payment_type",
			"read_only": 1,
			"in_list_view": 1,
			"description": (
				"Tên gọi đúng theo tài khoản tiền: 111 là Phiếu thu / Phiếu chi, "
				"112 là Giấy báo Có / Uỷ nhiệm chi. Máy tự điền, không sửa tay."
			),
		}
	]
}


# ------------------------------------------------------------ phep THUAN


def la_ngan_hang(so_tai_khoan):
	"""Tai khoan nay co phai tien gui ngan hang khong. THUAN.

	Doc theo SO HIEU chu khong theo account_type cua ERPNext: tren he nay
	tai khoan 1411 (Tam ung ca nhan) tung duoc khai account_type "Bank" vi
	no gan voi mot tai khoan OCB. Xet theo account_type thi 1411 thanh
	ngan hang, ma ban chat no la tam ung.
	"""
	return str(so_tai_khoan or "").strip().startswith("112")


def la_tien_mat(so_tai_khoan):
	"""Tai khoan nay co phai quy tien mat khong. THUAN."""
	return str(so_tai_khoan or "").strip().startswith("111")


def ten_chung_tu(loai_thanh_toan, tai_khoan, da_ghi_so=0):
	"""Ten goi dung cua mot chung tu tien. THUAN.

	Chi Dung chot 16/08/2026:
	  111 chi  -> Phieu chi          111 thu  -> Phieu thu
	  112 chi  -> Uy nhiem chi       112 thu  -> Giay bao Co
	  112 chi da ghi so -> Uy nhiem chi / Giay bao No

	Vi sao ban nhap va ban da ghi so khac ten nhau o chieu chi ngan hang:
	luc con nhap thi minh moi RA LENH, tien chua roi tai khoan, chung tu la
	Uy nhiem chi do minh phat hanh. Ghi so nghia la da co tep ngan hang
	dinh kem, tuc da co Giay bao No.
	"""
	chi = str(loai_thanh_toan or "").strip().lower() == "pay"
	if la_tien_mat(tai_khoan):
		return "Phiếu chi" if chi else "Phiếu thu"
	if la_ngan_hang(tai_khoan):
		if not chi:
			return "Giấy báo Có"
		return "Uỷ nhiệm chi / Giấy báo Nợ" if cint(da_ghi_so) else "Uỷ nhiệm chi"
	# Tai khoan khac (tam ung, chuyen noi bo...): goi trung tinh, KHONG goi
	# la phieu chi - do la ten danh rieng cho quy tien mat.
	return "Chứng từ thanh toán"


# --------------------------------------------------------------- hook


def _tk_tien(doc):
	"""Tai khoan tien cua chung tu: chi thi la paid_from, thu thi paid_to."""
	chi = str(doc.get("payment_type") or "").strip().lower() == "pay"
	return (doc.get("paid_from") if chi else doc.get("paid_to")) or ""


def dat_ten(doc, method=None):
	"""Hook validate cua Payment Entry: dien ten goi dung vao o hien thi."""
	try:
		if not doc.meta.has_field("vgb_loai_ct"):
			return
		doc.vgb_loai_ct = ten_chung_tu(
			doc.get("payment_type"), _tk_tien(doc), cint(doc.get("docstatus")) == 1
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "chung_tu_tien: dat ten loi")


def chan_thieu_dinh_kem(doc, method=None):
	"""Hook before_submit: chung tu qua NGAN HANG phai co tep dinh kem.

	Chi Dung chot 16/08/2026: ke toan tai Uy nhiem chi tu e-banking ve,
	dinh kem vao chung tu, ROI MOI duoc ghi so. Khong cong nhan dong sao
	ke SePay thay cho tep nay.

	Chan o BACKEND chu khong chi nhac tren man: nhac tren man thi bo qua
	duoc, ma day la ho so de giai trinh voi Cuc Thue.

	Chi soi chung tu lap TU NGAY CHOT tro di. Chung tu cu da ghi so giu
	nguyen, va chung tu cu con nhap thi ke toan van ghi so duoc nhu truoc -
	doi luat nguoc ve qua khu la lam ke toan ket cung voi mot chong phieu
	khong ai con nho da tra tien bang gi.
	"""
	try:
		if doc.doctype != PE:
			return
		tk = _tk_tien(doc)
		if not la_ngan_hang(tk):
			return
		tao_luc = str(doc.get("creation") or "")[:10]
		if tao_luc and tao_luc < NGAY_CHOT:
			return
		if frappe.db.count(
			"File", {"attached_to_doctype": PE, "attached_to_name": doc.name}
		):
			return
		frappe.throw(
			"%s %s đi qua tài khoản ngân hàng %s nên bắt buộc phải có Uỷ nhiệm chi "
			"đính kèm mới ghi sổ được. Tải UNC từ e-banking về, bấm nút kẹp giấy ở "
			"góc phải để đính kèm, rồi ghi sổ lại.\n\n"
			"Dòng sao kê SePay chỉ để xem tiền đã đi chưa, không thay được UNC khi "
			"làm việc với cơ quan thuế."
			% (ten_chung_tu(doc.get("payment_type"), tk), doc.name, tk)
		)
	except frappe.ValidationError:
		raise
	except Exception:
		frappe.log_error(frappe.get_traceback(), "chung_tu_tien: kiem dinh kem loi")


@frappe.whitelist()
def tinh_trang(name=None):
	"""Man hinh hoi: chung tu nay ten gi, da du ho so chua."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	d = frappe.db.get_value(
		PE, name, ["name", "payment_type", "paid_from", "paid_to", "docstatus", "creation"], as_dict=True
	)
	if not d:
		return {"co": 0}
	tk = _tk_tien(d)
	so_tep = frappe.db.count("File", {"attached_to_doctype": PE, "attached_to_name": d["name"]})
	ngan_hang = la_ngan_hang(tk)
	return {
		"co": 1,
		"ten": ten_chung_tu(d["payment_type"], tk, cint(d["docstatus"]) == 1),
		"tai_khoan": tk,
		"ngan_hang": 1 if ngan_hang else 0,
		"so_tep": so_tep,
		"du_ho_so": 1 if (not ngan_hang or so_tep) else 0,
		"nhac": (
			""
			if (not ngan_hang or so_tep)
			else "Chưa có Uỷ nhiệm chi đính kèm nên chưa ghi sổ được. Tải UNC từ e-banking rồi đính kèm."
		),
	}
