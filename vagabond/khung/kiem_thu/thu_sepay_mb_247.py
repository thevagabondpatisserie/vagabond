"""Ca kiểm cho tài khoản hoàn ứng MB Nguyễn Hoàng Việt trên SePay.

Ngày 10/09/2026 Uyên đã tạo người ở mục "Chi cho ai" nhưng không thấy số
tài khoản hoặc sao kê MB. Gốc lỗi có hai lớp độc lập:

1. Màn bản đồ chỉ tải tài khoản công ty, nên Bank Account cá nhân không thể
   được chọn dù đã khai đúng trong ERPNext.
2. Điểm nhận chỉ thử hai Secret Key của OCB và ACB. Nếu MB có webhook riêng,
   dán khoá MB sẽ phải ghi đè một tài khoản đang chạy.

Bộ ca này chạy thuần, không gọi SePay và không ghi cơ sở dữ liệu.
"""

import io
import os

from vagabond import sepay
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


def _than(s, dau, cuoi):
	i = s.find(dau)
	if i < 0:
		return ""
	j = s.find(cuoi, i + len(dau))
	return s[i:j if j > i else len(s)]


@ca("SePay MB: điểm nhận thử đủ ba Secret Key mà không ghi đè ACB")
def _ba_khoa():
	cu_cfg, cu_key = sepay.cfg, sepay.key
	try:
		sepay.cfg = lambda: {
			"sepay_hmac": "ocb", "sepay_hmac_2": "acb", "sepay_hmac_3": "mb",
		}
		sepay.key = lambda c, ten: c.get(ten) or ""
		la("giữ đúng thứ tự ba khoá", sepay._cac_khoa("sepay_hmac"), ["ocb", "acb", "mb"])
	finally:
		sepay.cfg, sepay.key = cu_cfg, cu_key


@ca("SePay MB: schema và màn cài đặt có khe HMAC riêng cho MB")
def _khe_mb():
	s = _doc("sepay.py")
	dung("trường Password riêng", '"fieldname": "sepay_hmac_3"' in s and '"fieldtype": "Password"' in s)
	dung("nhãn chỉ đúng tài khoản", "MB Nguyễn Hoàng Việt" in s)
	j = _doc("public/js/bep/17-cai-dat.js")
	dung("có ô khoá MB", 'id="seHm3"' in j)
	dung("lưu đúng khe 3", "seLuuHmac(3)" in j)
	dung("bày dấu vân tay khoá MB", "sepay_hmac_3" in j)


@ca("SePay MB: danh sách map có cả Bank Account cá nhân đang dùng")
def _tai_khoan_ca_nhan_hien_ra():
	ds = sepay._ds_tai_khoan_map([
		Doi(name="MB công ty", account_name="Vagabond", bank="MB", bank_account_no="111111",
			account="1121 - MB - TV", party_type="", party="", is_company_account=1, disabled=0),
		Doi(name="MB Nguyễn Hoàng Việt", account_name="Nguyễn Hoàng Việt", bank="MB", bank_account_no="222222",
			account="1411 - Tạm ứng - TV", party_type="Supplier", party="NCC-VIET", is_company_account=0, disabled=0),
		Doi(name="ACB cũ", account_name="Nguyễn Hoàng Việt", bank="ACB", bank_account_no="333333",
			account="1411 - Tạm ứng - TV", party_type="Supplier", party="NCC-VIET", is_company_account=0, disabled=1),
	])
	la("chỉ bỏ tài khoản ngưng dùng", sorted(x["ma"] for x in ds), ["MB Nguyễn Hoàng Việt", "MB công ty"])
	mb = [x for x in ds if x["ma"] == "MB Nguyễn Hoàng Việt"][0]
	dung("giữ cờ cá nhân", not mb["la_cong_ty"])
	la("giữ đúng chủ tài khoản", mb["chu"], "NCC-VIET")


@ca("SePay MB: backend chặn map nhầm số hoặc tài khoản cá nhân chưa gắn người")
def _chan_map_nham():
	dung_hop_le = Doi(bank_account_no="222 222", disabled=0, is_company_account=0,
		party_type="Supplier", party="NCC-VIET", account="1411 - Tạm ứng - TV")
	la("cá nhân đủ dữ liệu", sepay._loi_map_tai_khoan("222222", dung_hop_le), "")
	dung("chặn sai số", "không trùng" in sepay._loi_map_tai_khoan("999999", dung_hop_le))
	thieu_chu = Doi(bank_account_no="222222", disabled=0, is_company_account=0,
		party_type="", party="", account="1411 - Tạm ứng - TV")
	dung("chặn thiếu chủ", "gắn đúng người" in sepay._loi_map_tai_khoan("222222", thieu_chu))
	ngung = Doi(bank_account_no="222222", disabled=1, is_company_account=0,
		party_type="Supplier", party="NCC-VIET", account="1411 - Tạm ứng - TV")
	dung("chặn ngưng dùng", "ngưng dùng" in sepay._loi_map_tai_khoan("222222", ngung))
	sai_so_cai = Doi(bank_account_no="222222", disabled=0, is_company_account=0,
		party_type="Supplier", party="NCC-VIET", account="1121 - MB - TV")
	dung("chặn ngoài quỹ tạm ứng", "nhóm 141" in sepay._loi_map_tai_khoan("222222", sai_so_cai))
	cong_ty = Doi(bank_account_no="111111", disabled=0, is_company_account=1,
		party_type="", party="", account="1121 - MB - TV")
	la("tài khoản công ty vẫn hợp lệ", sepay._loi_map_tai_khoan("111111", cong_ty), "")
	la("chuẩn hoá khoảng trắng", sepay._so_tk_chuan("222 222"), "222222")


@ca("SePay MB: mọi cửa tra bản đồ đều chuẩn hoá số và không ghi đè âm thầm")
def _ban_do_mot_khoa():
	s = _doc("sepay.py")
	ban_do, xung_dot = sepay._chuan_hoa_ban_do({
		"0123 4567": "BANK-A",
		"01234567": "BANK-B",
		"9999-0000": "BANK-C",
		"99990000": "BANK-C",
	})
	dung("số trỏ hai túi bị bỏ khỏi định tuyến", "01234567" not in ban_do)
	la("giữ đủ hai nguồn xung đột", len(xung_dot["01234567"]), 2)
	la("cùng một túi thì gộp an toàn", ban_do["99990000"], "BANK-C")
	w = _than(s, "def _webhook():", "\ndef _ghi_chua_map(")
	dung("webhook chuẩn hoá số", "_so_tk_chuan(goi.get(" in w)
	n = _than(s, "def nap_bu(", "\n# --------------------------------------------------------------- tinh trang")
	dung("nạp bù chuẩn hoá số giao dịch", "so_gd = _so_tk_chuan(" in n)


@ca("SePay MB: DocType cấu hình nằm trong git và có lịch sử thay đổi")
def _doctype_trong_git():
	p = os.path.join(GOI, "vagabond", "doctype", "sepay_settings", "sepay_settings.json")
	dung("có schema SePay Settings", os.path.isfile(p))
	s = _doc("vagabond/doctype/sepay_settings/sepay_settings.json")
	dung("schema là singleton", '"issingle": 1' in s)
	dung("có lưu vết thay đổi", '"track_changes": 1' in s)
	dung("có bảng định tuyến", '"fieldname": "account_map"' in s)


@ca("SePay MB: màn map dùng ô chọn có tìm, không dùng select bị cắt danh sách")
def _o_chon_co_tim():
	j = _doc("public/js/bep/17-cai-dat.js")
	t = _than(j, "function seVe()", "async function seLuuHmac(")
	dung("có thẻ chọn tài khoản", "data-semaptk" in t)
	dung("không còn select trong khối SePay", "<select" not in t)
	dung("dùng sheet tìm kiếm", "seChonTaiKhoan" in j and "sheet('Chọn Bank Account để nhận sao kê'" in j)


@ca("SePay MB: truy vấn không lọc mất cá nhân và không cắt ở 50 dòng")
def _truy_van_du():
	s = _doc("sepay.py")
	t = _than(s, "def tinh_trang():", "\ndef dau_khoa(")
	dung("chỉ lấy tài khoản đang dùng", 'filters={"disabled": 0}' in t)
	dung("không lọc is_company_account", 'filters={"is_company_account": 1}' not in t)
	dung("không cắt 50", "limit_page_length=0" in t)
	dung("trả đủ dữ liệu để phân biệt túi tiền", '"party_type", "party", "is_company_account"' in t)


@ca('SePay: Sales bị chặn trước khi đọc cấu hình hoặc danh sách ngân hàng')
def _sales_khong_doc_cau_hinh():
	from unittest.mock import patch, Mock
	with patch.dict('sys.modules', {'vagabond.ban_hang': Mock()}), patch.object(sepay.frappe, 'get_roles', return_value=['Sales User']), patch.object(sepay, 'cfg') as doc:
		try:
			sepay.tinh_trang()
		except Exception:
			pass
		else:
			dung('Sales phải bị từ chối', False)
		la('chặn trước đọc cấu hình', doc.call_count, 0)
	with patch.object(sepay.frappe,'get_roles',return_value=['Sales User']), patch.object(sepay,'cfg') as doc:
		for ham in (sepay.soi_khoa,sepay.dat_khoa,sepay.dat_hmac,sepay.them_tai_khoan,sepay.nap_bu):
			try:
				ham()
			except sepay.frappe.ValidationError as e:
				dung('đúng câu quyền '+ham.__name__,'Chỉ quản lý hoặc kế toán' in str(e))
			else:
				dung('Sales không được sửa '+ham.__name__,False)
		la('không đọc cấu hình ở các cửa bị chặn',doc.call_count,0)


@ca('SePay: Document kiểm từng map cả khi không có xung đột số')
def _desk_kiem_tung_map():
	from unittest.mock import patch
	from vagabond.vagabond.doctype.sepay_settings.sepay_settings import SePaySettings
	d = Doi(account_map='{"123456":"BANK-A","654321":"BANK-B"}',get_doc_before_save=lambda:None)
	with patch.object(sepay, 'kiem_map_tai_khoan') as kiem:
		SePaySettings.validate(d)
		la('kiểm cả hai tài khoản', kiem.call_args_list, [(("123456", "BANK-A"),), (("654321", "BANK-B"),)])
	cu = Doi(account_map='{"123456":"BANK-A"}')
	d.get_doc_before_save = lambda:cu
	with patch.object(sepay,'kiem_map_tai_khoan') as kiem:
		SePaySettings.validate(d)
		la('chỉ kiểm tuyến mới',kiem.call_args_list,[(("654321","BANK-B"),)])
	d.account_map = cu.account_map
	with patch.object(sepay,'kiem_map_tai_khoan') as kiem:
		SePaySettings.validate(d)
		la('map không đổi không chặn lưu cấu hình khác',kiem.call_count,0)
