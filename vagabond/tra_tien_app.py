# -*- coding: utf-8 -*-
"""Uỷ nhiệm chi và tài khoản chi cho hồ sơ thanh toán trên app.

VÌ SAO CÓ TỆP NÀY, ngày 28/08/2026
--------------------------------------------------------------------
Chị Dung bấm "Ghi nhận đã thanh toán" trên hồ sơ APP.26.08.018 và máy
trả về đúng một dòng khó hiểu:

    Tỷ giá nguồn là bắt buộc

Đó là câu ERPNext nói khi bút toán chi tiền chưa biết TIỀN ĐI RA TỪ
TÀI KHOẢN NÀO. Không có tài khoản nguồn thì không có loại tiền của
tài khoản nguồn, không có loại tiền thì không suy ra được tỷ giá, và
ô tỷ giá là ô bắt buộc. Câu báo lỗi rơi vào mắt xích cuối cùng chứ
không phải chỗ hỏng.

Chỗ hỏng thật: luồng trả nợ nhà cung cấp dựng Payment Entry mà chỉ
điền tài khoản nguồn cho ĐÚNG MỘT loại hồ sơ là "Chi từ TK công ty",
vì loại đó có ô chọn tài khoản trên màn hình. Hồ sơ công nợ nhà cung
cấp không có ô đó nên tài khoản nguồn để trống. Đếm trên site hôm ấy:
CHƯA MỘT hồ sơ công nợ nào từng ghi nhận thanh toán trót lọt, nên lỗi
này có từ ngày dựng luồng chứ không phải mới sinh.

VIỆC THỨ HAI: UỶ NHIỆM CHI
--------------------------------------------------------------------
Anh Việt 28/08/2026: *"Em thêm 1 nút đính kèm UNC dùm anh để chị Dung
đính kèm UNC lên các APP rồi mới ghi nhận được thanh toán của TẤT CẢ
CÁC APP."*

Hàng rào này vốn đã có ở tầng dưới: hook `chan_thieu_dinh_kem` chặn
ghi sổ mọi chứng từ tiền đi qua ngân hàng mà chưa có tệp đính kèm.
Nhưng nó chặn ở Payment Entry, tức là chặn SAU khi hồ sơ đã đổi trạng
thái, và người bấm nút trên app thì không có chỗ nào để đính tệp vào.
Nên phải đưa hàng rào lên đúng chỗ người bấm: đính uỷ nhiệm chi vào
HỒ SƠ trước, lúc ghi nhận thanh toán thì máy chép tệp đó sang bút
toán vừa dựng, hook tầng dưới thấy có tệp và cho ghi sổ.

Chép chứ không dời: hồ sơ giữ bộ giấy tờ của nó, bút toán giữ bộ giấy
tờ của nó, hai bên độc lập. Chép bằng cách trỏ cùng một đường dẫn tệp
nên không tốn thêm dung lượng.
"""

# Tài khoản tiền gửi ngân hàng theo TT200. Tiền của một lần chuyển
# khoản phải ra từ đây chứ không ra từ quỹ tiền mặt.
DAU_NGAN_HANG = "112"

# Giới hạn tệp uỷ nhiệm chi. Cùng con số với luồng hoàn tiền khách để
# hai bên không giải thích hai kiểu cho cùng một người dùng.
MAX_MB = 12


def tach_ma(chuoi):
	"""Tách ô lưu danh sách mã tệp thành danh sách. THUẦN.

	Nhận cả ba dạng người ta có thể ghi vào ô: xuống dòng, dấu phẩy,
	dấu chấm phẩy. Nhận rộng ở cửa vào, ra khỏi hàm chỉ còn một dạng.
	"""
	ra = []
	for phan in str(chuoi or "").replace(";", "\n").replace(",", "\n").split("\n"):
		ma = phan.strip()
		if ma and ma not in ra:
			ra.append(ma)
	return ra


def gop_ma(ds):
	"""Ngược của `tach_ma`. THUẦN."""
	sach = []
	for x in (ds or []):
		ma = str(x or "").strip()
		if ma and ma not in sach:
			sach.append(ma)
	return "\n".join(sach)


def du_unc(so_tep):
	"""Có đủ uỷ nhiệm chi để ghi nhận thanh toán chưa. THUẦN."""
	try:
		return int(so_tep or 0) >= 1
	except Exception:
		return False


def loi_thieu_unc(ma_ho_so):
	"""Câu báo khi hồ sơ chưa có uỷ nhiệm chi. THUẦN.

	Nói ra việc phải làm và chỗ bấm, không nói tên trường hay tên hàm.
	"""
	return (
		"Hồ sơ %s chưa có Uỷ nhiệm chi. Anh chị tải UNC từ e-banking về máy, "
		"bấm nút Đính kèm UNC ở màn hồ sơ, rồi mới ghi nhận thanh toán được.\n\n"
		"Đây là chứng từ gốc để giải trình với cơ quan thuế. Dòng sao kê SePay "
		"chỉ để xem tiền đã đi chưa, không thay được tờ UNC."
		% (ma_ho_so or "")
	)


def loi_khong_ro_tk(ten_cong_ty):
	"""Câu báo khi không suy ra được tài khoản tiền chi. THUẦN."""
	return (
		"Chưa biết tiền đi ra từ tài khoản ngân hàng nào của %s nên máy chưa dựng "
		"được bút toán chi. Nhờ kế toán khai một tài khoản ngân hàng của công ty, "
		"hoặc khai tài khoản mặc định cho hình thức Chuyển khoản, rồi bấm lại."
		% (ten_cong_ty or "công ty")
	)


def chon_tk_ngan_hang(ds):
	"""Chọn một tài khoản chi trong danh sách ứng viên. THUẦN.

	`ds` là danh sách chuỗi số hiệu tài khoản. Ưu tiên tài khoản tiền
	gửi ngân hàng 112x; không có thì lấy cái đầu tiên còn dùng được.

	Vì sao ưu tiên 112 chứ không lấy bừa: 1411 là tạm ứng cá nhân, chi
	từ đó là ghi tiền ra khỏi một chỗ không ai theo dõi. Đây đúng là
	chỗ chị Dung đã bẻ lại ở luồng hoàn tiền ngày 16/08/2026.
	"""
	sach = [str(x or "").strip() for x in (ds or []) if str(x or "").strip()]
	for tk in sach:
		if tk.split("-")[0].strip().startswith(DAU_NGAN_HANG):
			return tk
	return sach[0] if sach else ""


def ty_gia_chi(tien_te_tk, tien_te_cong_ty):
	"""Tỷ giá của chân tiền ra. THUẦN.

	Cùng loại tiền thì tỷ giá là 1. Khác loại tiền thì trả 0 để bên
	gọi biết là phải hỏi bảng tỷ giá chứ không được đoán bừa - đoán
	bừa ở đây là ghi sai số tiền lên sổ cái.
	"""
	a = str(tien_te_tk or "").strip().upper()
	b = str(tien_te_cong_ty or "").strip().upper()
	if not a or not b:
		return 0.0
	return 1.0 if a == b else 0.0


def kiem_tep(ten, so_byte):
	"""Tệp uỷ nhiệm chi có nhận được không. THUẦN. Trả câu lỗi hoặc rỗng."""
	if not str(ten or "").strip():
		return "Tệp uỷ nhiệm chi chưa có tên. Vui lòng chọn lại tệp."
	try:
		n = int(so_byte or 0)
	except Exception:
		n = 0
	if n <= 0:
		return "Tệp uỷ nhiệm chi rỗng. Vui lòng kiểm lại tệp tải từ e-banking."
	if n > MAX_MB * 1024 * 1024:
		return (
			"Tệp uỷ nhiệm chi nặng %s MB, quá %d MB nên máy không nhận. Vui lòng "
			"xuất lại bản PDF hoặc chụp nhỏ hơn."
			% ("{:.1f}".format(n / 1024.0 / 1024.0), MAX_MB)
		)
	return ""


# ------------------------------------------------------- phần cần Frappe

import frappe
from frappe.utils import cint, now_datetime

DT = "Vagabond Ho So TT"
PE = "Payment Entry"

# Trước bước nào thì còn gỡ uỷ nhiệm chi ra được. Đã thanh toán rồi thì
# tờ UNC là chứng từ gốc của một lần tiền ra thật, gỡ ra là làm thủng bộ
# hồ sơ (QT-20, và luật không đụng vào dữ liệu quá khứ anh Việt chốt
# 13/08/2026).
TT_GO_DUOC_UNC = ("Nhap", "Tu choi", "Cho ke toan", "Cho giam doc", "Da duyet")


def _vai():
	from vagabond.ho_so_tt import VAI_FIN, VAI_GD, VAI_LAP

	return VAI_LAP, VAI_FIN, VAI_GD


def _kiem_ho_so(name):
	if not name or not frappe.db.exists(DT, name):
		frappe.throw("Không tìm thấy hồ sơ %s. Vui lòng tải lại danh sách." % (name or "(trống)"))


def ds_unc_tho(name):
	"""Danh sách tệp UNC đang đính trên hồ sơ, đã lọc tệp không còn."""
	chuoi = frappe.db.get_value(DT, name, "unc_tep")
	ra = []
	for ma in tach_ma(chuoi):
		f = frappe.db.get_value(
			"File", ma, ["name", "file_name", "file_url", "file_size", "is_private"], as_dict=True
		)
		if f:
			ra.append(f)
	return ra


def dem_unc(name):
	"""Hồ sơ đang có mấy tờ uỷ nhiệm chi. Đếm THẬT trên máy chủ."""
	try:
		return len(ds_unc_tho(name))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tra_tien_app: dem UNC loi")
		return 0


@frappe.whitelist()
def ds_unc(name=None):
	"""Màn hình hỏi: hồ sơ này đang có những tờ uỷ nhiệm chi nào."""
	vai_lap, vai_fin, vai_gd = _vai()
	from vagabond.ho_so_tt import _kiem

	_kiem(vai_lap | vai_fin | vai_gd, "xem uỷ nhiệm chi")
	_kiem_ho_so(name)
	tt = frappe.db.get_value(DT, name, "trang_thai")
	return {
		"tep": [
			{
				"file": f.name,
				"ten": f.file_name or f.name,
				"url": f.file_url or "",
				"co": cint(f.file_size),
			}
			for f in ds_unc_tho(name)
		],
		"go_duoc": 1 if tt in TT_GO_DUOC_UNC else 0,
		"nguoi": frappe.db.get_value(DT, name, "unc_nguoi") or "",
		"luc": str(frappe.db.get_value(DT, name, "unc_luc") or ""),
	}


@frappe.whitelist()
def dinh_unc(name=None, tep=None):
	"""Đính uỷ nhiệm chi vào hồ sơ thanh toán.

	Nhận mã tệp đã tải lên bằng đường `upload_file` chứ không nhận nội
	dung tệp: màn hình đã có sẵn đường đó cho bản thể hiện hoá đơn, dùng
	lại thì hai chỗ hỏng cùng lúc chứ không hỏng lệch nhau.
	"""
	from vagabond.ho_so_tt import _ghi_vet, _kiem, _tep_hop_le

	vai_lap, vai_fin, vai_gd = _vai()
	_kiem(vai_fin | vai_gd, "đính uỷ nhiệm chi")
	_kiem_ho_so(name)

	ma_moi = _tep_hop_le(tep)
	if not ma_moi:
		frappe.throw("Tệp gửi lên không còn trên máy chủ. Vui lòng chọn tệp rồi đính lại.")

	for ma in ma_moi:
		f = frappe.db.get_value("File", ma, ["file_name", "file_size"], as_dict=True) or {}
		loi = kiem_tep(f.get("file_name") or ma, f.get("file_size"))
		if loi:
			frappe.throw(loi)

	cu = [f.name for f in ds_unc_tho(name)]
	frappe.db.set_value(
		DT,
		name,
		{
			"unc_tep": gop_ma(cu + ma_moi),
			"unc_nguoi": frappe.session.user,
			"unc_luc": now_datetime(),
		},
		update_modified=False,
	)
	for ma in ma_moi:
		try:
			frappe.db.set_value(
				"File",
				ma,
				{"attached_to_doctype": DT, "attached_to_name": name, "is_private": 1},
				update_modified=False,
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "tra_tien_app: gan tep UNC ve ho so")
	frappe.db.commit()
	_ghi_vet(name, "Đính %d tờ uỷ nhiệm chi." % len(ma_moi))
	return ds_unc(name)


@frappe.whitelist()
def go_unc(name=None, tep=None):
	"""Gỡ một tờ uỷ nhiệm chi đính nhầm. KHÔNG xoá tệp khỏi máy chủ."""
	from vagabond.ho_so_tt import NHAN, _ghi_vet, _kiem

	vai_lap, vai_fin, vai_gd = _vai()
	_kiem(vai_fin | vai_gd, "gỡ uỷ nhiệm chi")
	_kiem_ho_so(name)

	tt = frappe.db.get_value(DT, name, "trang_thai")
	if tt not in TT_GO_DUOC_UNC:
		frappe.throw(
			"Hồ sơ %s đang ở %s nên không gỡ uỷ nhiệm chi ra được nữa. Tờ này là "
			"chứng từ gốc của một lần chuyển tiền thật. Đính nhầm thì đính thêm tờ "
			"đúng vào, và báo bộ phận kỹ thuật."
			% (name, NHAN.get(tt, tt))
		)

	ma = str(tep or "").strip()
	con = [f.name for f in ds_unc_tho(name) if f.name != ma]
	if len(con) == len(ds_unc_tho(name)):
		frappe.throw("Tệp này không nằm trên hồ sơ %s. Vui lòng tải lại trang rồi bấm lại." % name)
	frappe.db.set_value(DT, name, {"unc_tep": gop_ma(con)}, update_modified=False)
	try:
		frappe.db.set_value(
			"File",
			ma,
			{"attached_to_doctype": None, "attached_to_name": None},
			update_modified=False,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tra_tien_app: go tep UNC")
	frappe.db.commit()
	_ghi_vet(name, "Gỡ một tờ uỷ nhiệm chi khỏi hồ sơ.")
	return ds_unc(name)


def chep_unc(name, sang_doctype, sang_name):
	"""Chép uỷ nhiệm chi của hồ sơ sang một chứng từ khác.

	Trỏ CÙNG một đường dẫn tệp chứ không tải lại nội dung: một tờ UNC
	nằm một chỗ trên đĩa, hai chứng từ cùng trỏ tới. Đây đúng là cách
	Frappe đính một tệp có sẵn vào chứng từ thứ hai.

	Không ném lỗi ra ngoài: hàm này chạy giữa lúc dựng bút toán, hỏng
	thì hook tầng dưới sẽ chặn ghi sổ và nói rõ hơn.
	"""
	da_chep = 0
	for f in ds_unc_tho(name):
		if not (f.file_url or "").strip():
			continue
		try:
			if frappe.db.exists(
				"File",
				{
					"file_url": f.file_url,
					"attached_to_doctype": sang_doctype,
					"attached_to_name": sang_name,
				},
			):
				da_chep += 1
				continue
			moi = frappe.get_doc(
				{
					"doctype": "File",
					"file_url": f.file_url,
					"file_name": f.file_name,
					"attached_to_doctype": sang_doctype,
					"attached_to_name": sang_name,
					"is_private": cint(f.is_private),
				}
			)
			moi.flags.ignore_permissions = True
			moi.insert(ignore_permissions=True)
			da_chep += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "tra_tien_app: chep UNC sang chung tu")
	return da_chep


def tk_tien_chi(cong_ty, phuong_thuc=None, bank_account=None):
	"""Tiền của một lần chi đi ra từ tài khoản kế toán nào.

	Năm đường, xét theo thứ tự từ cụ thể tới chung. Dừng ở đường đầu
	tiên cho ra kết quả:

	  1. Tài khoản ngân hàng đã chọn ngay trên hồ sơ
	  2. Tài khoản mặc định của hình thức thanh toán (Chuyển khoản)
	  3. Tài khoản ngân hàng mặc định khai trong hồ sơ công ty
	  4. Một tài khoản ngân hàng của công ty, ưu tiên 112x
	  5. Tài khoản tiền mặt mặc định của công ty

	Trả về cặp (tài khoản kế toán, Bank Account). Không suy ra được thì
	trả cặp rỗng, bên gọi tự quyết nói gì với người bấm.
	"""
	cong_ty = (cong_ty or "").strip()

	ten_ba = (bank_account or "").strip()
	if ten_ba and frappe.db.exists("Bank Account", ten_ba):
		tk = frappe.db.get_value("Bank Account", ten_ba, "account")
		if tk:
			return tk, ten_ba

	pt = (phuong_thuc or "").strip()
	if pt and cong_ty and frappe.db.exists("Mode of Payment", pt):
		tk = frappe.db.get_value(
			"Mode of Payment Account", {"parent": pt, "company": cong_ty}, "default_account"
		)
		if tk:
			return tk, _bank_account_cua(tk, cong_ty)

	if cong_ty:
		tk = frappe.db.get_value("Company", cong_ty, "default_bank_account")
		if tk:
			return tk, _bank_account_cua(tk, cong_ty)

	ds = frappe.get_all(
		"Bank Account",
		filters={"company": cong_ty, "is_company_account": 1, "disabled": 0},
		fields=["name", "account"],
		limit_page_length=0,
	) if cong_ty else []
	tk = chon_tk_ngan_hang([d["account"] for d in ds if d.get("account")])
	if tk:
		for d in ds:
			if d.get("account") == tk:
				return tk, d["name"]
		return tk, ""

	if cong_ty:
		tk = frappe.db.get_value("Company", cong_ty, "default_cash_account")
		if tk:
			return tk, ""

	return "", ""


def _bank_account_cua(tai_khoan, cong_ty):
	"""Bank Account nào đang trỏ vào tài khoản kế toán này."""
	try:
		return (
			frappe.db.get_value(
				"Bank Account",
				{"account": tai_khoan, "company": cong_ty, "disabled": 0},
				"name",
			)
			or ""
		)
	except Exception:
		return ""


@frappe.whitelist()
def soat_tk_chi():
	"""Chỉ đọc: máy đang định chi tiền ra từ tài khoản nào.

	Để anh Việt và chị Dung xem trước mà không phải bấm thử một lần
	chuyển tiền thật.
	"""
	from vagabond.ho_so_tt import VAI_FIN, VAI_GD, _kiem

	_kiem(VAI_FIN | VAI_GD, "xem tài khoản chi")
	cong_ty = frappe.db.get_single_value("Global Defaults", "default_company")
	tk, ba = tk_tien_chi(cong_ty, "Chuyển khoản")
	return {
		"cong_ty": cong_ty or "",
		"tai_khoan": tk or "",
		"bank_account": ba or "",
		"tien_te": frappe.db.get_value("Account", tk, "account_currency") if tk else "",
		"tien_te_cong_ty": frappe.db.get_value("Company", cong_ty, "default_currency") if cong_ty else "",
	}
