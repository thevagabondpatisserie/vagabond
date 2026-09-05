"""Các bẫy tiền tìm thấy khi rà soát toàn luồng bán hàng ngày 06/09/2026.

Chạy chính thân hàm đang dùng, chỉ thay cổng cơ sở dữ liệu bằng giả lập.
Không chép lại thuật toán cần kiểm và không gọi mạng hay ghi chứng từ thật.
Các ca này không thay cho kiểm thử Payment Entry và sổ cái trên site.
"""

import ast
from pathlib import Path
import re
from types import SimpleNamespace
from unittest.mock import Mock

from vagabond import chiem_sao_ke, luat_thanh_toan
from vagabond.khung.kiem_thu.nen import ca, la, dung

GOI = Path(__file__).resolve().parents[2]


def _nap(tep, ten, **nen):
	"""Tách thân hàm thật để ca kiểm không phải nạp Frappe hoặc requests."""
	cay = ast.parse((GOI / tep).read_text(encoding="utf-8"))
	ds = [n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name in ten]
	assert {n.name for n in ds} == set(ten)
	for n in ds:
		n.decorator_list = []
	exec(compile(ast.Module(body=ds, type_ignores=[]), str(GOI / tep), "exec"), nen)
	return SimpleNamespace(**nen)


class _Phieu(dict):
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__


def _so(v):
	return float(v or 0)


def _nem(cau, *args, **kwargs):
	raise ValueError(cau)


def _phai_chan(goi, cau):
	try:
		goi()
	except ValueError as e:
		dung("lỗi chỉ đường xử lý", cau in str(e))
	else:
		raise AssertionError("Cửa phải chặn nhưng đã cho qua")


def _cong_no(dong):
	return _nap("cong_no.py", ["_chuan_ma", "_sepay_theo_ma_cn", "_sepay_cn"],
		re=re, flt=_so, chiem_sao_ke=chiem_sao_ke,
		RE_MA_CN=re.compile(r"CN[A-Z0-9]{6}"), RE_MA_DNTT=re.compile(r"DNTT[0-9]{9}"),
		frappe=SimpleNamespace(db=SimpleNamespace(sql=Mock(return_value=dong))))


@ca("đối soát một bill vẫn phải thấy mã thứ hai ngoài bộ lọc")
def _():
	dong = [{"ten": "BT-1", "mo_ta": "VGBAAAAA VGBBBBBB", "tien": 400000}]
	for ds in (["VGBAAAAA"], ["VGBBBBBB"], ["VGBAAAAA", "VGBBBBBB"], []):
		theo, bo = chiem_sao_ke.cong_tien(dong, ds, r"VGB[A-Z0-9]{5}")
		la("không gạch trọn tiền cho một bill", theo, {})
		la("chỉ rõ cả hai mã", bo[0]["ma"], ["VGBAAAAA", "VGBBBBBB"])


@ca("sao kê không liên quan không chen cảnh báo vào bill đang xem")
def _():
	dong = [{"ten": "BT-1", "mo_ta": "VGBAAAAA VGBBBBBB", "tien": 400000}]
	la("bỏ cả dòng lẫn cảnh báo", chiem_sao_ke.cong_tien(dong, ["VGBCCCCC"], r"VGB[A-Z0-9]{5}"), ({}, []))


@ca("một mã lặp trong nội dung và tham chiếu chỉ cộng một lần")
def _():
	theo, bo = chiem_sao_ke.cong_tien([
		{"ten": "BT-1", "mo_ta": "vgbAAAAA VGBAAAAA", "tien": 100000},
		{"ten": "BT-2", "mo_ta": "VGBAAAAA", "tien": 50000},
	], ["vgbaaaaa"], r"VGB[A-Z0-9]{5}")
	la("hai giao dịch, không nhân đôi một giao dịch", theo["VGBAAAAA"],
		{"nhan": 150000, "so_gd": 2, "gd": ["BT-1", "BT-2"]})
	la("không nhập nhằng", bo, [])


@ca("phiếu công nợ đơn lẻ không được nuốt mã DNTT hoặc CN còn lại")
def _():
	for ma_kia in ("DNTT-26-09-00002", "CNAAAAAA"):
		cn = _cong_no([{"name": "BT-1", "description": "DNTT-26-09-00001",
			"reference_number": ma_kia, "deposit": 400000, "withdrawal": 0}])
		theo, bo = cn._sepay_theo_ma_cn(["DNTT-26-09-00001"])
		la("không tự chia tiền", theo, {})
		la("báo một dòng nhập nhằng", len(bo), 1)
		la("tra đơn lẻ cũng không nhận tiền", cn._sepay_cn("DNTT-26-09-00001"), {})


@ca("công nợ không có mã hợp lệ trả đúng cặp kết quả và không hỏi sao kê")
def _():
	cn = _cong_no([])
	for ds in ([], [None], [""], ["khong-hop-le"]):
		la("đúng kiểu trả về", cn._sepay_theo_ma_cn(ds), ({}, []))
	la("xem mã trống không vỡ màn", cn._sepay_cn(None), {})
	cn.frappe.db.sql.assert_not_called()


@ca("mã DNTT có gạch vẫn khớp và giữ tên gốc")
def _():
	cn = _cong_no([{"name": "BT-2", "description": "DNTT260900001 DNTT-26-09-00001", "deposit": 150000}])
	la("tiền một lần", cn._sepay_cn("DNTT-26-09-00001")["nhan"], 150000)


@ca("lọc sơ bộ sao kê không được loại mã DNTT còn dấu gạch")
def _():
	cn = _cong_no([])
	cn._sepay_cn("DNTT-26-09-00001")
	_, tham_so = cn.frappe.db.sql.call_args.args
	for noi_dung in ("DNTT-26-09-00001", "DNTT260900001", "DNTT 26 09 00001"):
		dung("SQL phải nhận trước khi Python chuẩn hóa", re.search(tham_so[0], noi_dung))


def _cua_luu(trang_thai=0, huy=0):
	si = _Phieu(name="SI-1", custom_nguon="Quầy", docstatus=trang_thai,
		vgb_huy=huy, vgb_pt_thanh_toan="Chuyển khoản", vgb_ma_tham_chieu="VGBAAAAA")
	db = SimpleNamespace(get_value=Mock(return_value=si), set_value=Mock(), commit=Mock())
	return _nap("ban_hang.py", ["luu_thanh_toan"],
		frappe=SimpleNamespace(db=db, throw=_nem), cint=lambda v: int(v or 0),
		_kiem_quyen=Mock(), _kiem_pt=lambda pt, nguon: pt,
		_chuan_ma_tham_chieu=lambda pt, ma, **kw: str(ma or "").strip().upper(),
		luat_thanh_toan=luat_thanh_toan)


@ca("hóa đơn ghi sổ không được đổi phương thức hoặc mã sao kê ở cửa lưu nháp")
def _():
	for pt, ma in (("Tiền mặt", None), ("Chuyển khoản", "VGBBBBBB")):
		bh = _cua_luu(1)
		_phai_chan(lambda: bh.luu_thanh_toan("SI-1", pt, ma), "ghi sổ")
		bh.frappe.db.set_value.assert_not_called()
		bh.frappe.db.commit.assert_not_called()


@ca("lưu cùng giá trị trên hóa đơn ghi sổ là no-op để lưu thông tin xuất HĐ vẫn chạy")
def _():
	bh = _cua_luu(1)
	la("không làm hỏng chuỗi lưu thông tin", bh.luu_thanh_toan("SI-1", "Chuyển khoản")["ok"], 1)
	bh.frappe.db.set_value.assert_not_called()
	bh.frappe.db.commit.assert_not_called()


@ca("hóa đơn hủy cứng hoặc hủy mềm không được lưu lại thanh toán")
def _():
	for tt, huy in ((2, 0), (0, 1), (1, 1)):
		bh = _cua_luu(tt, huy)
		_phai_chan(lambda: bh.luu_thanh_toan("SI-1", "Chuyển khoản"), "huỷ")
		bh.frappe.db.set_value.assert_not_called()


@ca("hóa đơn nháp vẫn lưu thanh toán và khóa dòng trước khi kiểm trạng thái")
def _():
	bh = _cua_luu()
	bh.luu_thanh_toan("SI-1", "Chuyển khoản", "VGBBBBBB")
	bh.frappe.db.set_value.assert_called_once()
	bh.frappe.db.commit.assert_called_once()
	dung("đọc có khóa để tránh chốt bill xen giữa", bh.frappe.db.get_value.call_args.kwargs.get("for_update"))


def _quyen(muc="gioi_han"):
	return _nap("quyen_quay.py", ["_theo_ma", "can_otp", "them_giam_gia"],
		muc=lambda: muc, flt=_so, cint=lambda v: int(v or 0),
		frappe=SimpleNamespace(db=SimpleNamespace(get_value=Mock(return_value="Bánh"))))


@ca("in tạm tính rồi giảm đơn giá cũng phải xin duyệt như giảm giá")
def _():
	q = _quyen()
	si = _Phieu(vgb_tam_tinh=1, items=[{"item_code": "BANH", "qty": 1, "rate": 100000}])
	for sl in (1, 2):
		can, _ = q.can_otp(si, [{"item_code": "BANH", "qty": sl, "rate": 60000}])
		dung("không lấy tăng số lượng để che việc giảm đơn giá", can)


@ca("tách dòng cùng giá để thêm ghi chú không phải giảm giá")
def _():
	q = _quyen()
	si = _Phieu(vgb_tam_tinh=1, items=[{"item_code": "BANH", "qty": 2, "rate": 100000}])
	moi = [{"item_code": "BANH", "qty": 1, "rate": 100000}] * 2
	la("không đòi OTP nhầm", q.can_otp(si, moi), (False, ""))


@ca("bịt giảm đơn giá không thay lựa chọn quyền tự do hay bill chưa in")
def _():
	for muc, in_roi in (("tu_do", 1), ("gioi_han", 0)):
		q = _quyen(muc)
		si = _Phieu(vgb_tam_tinh=in_roi, items=[{"item_code": "BANH", "qty": 1, "rate": 100000}])
		la("giữ chính sách của chủ", q.can_otp(si, [{"item_code": "BANH", "qty": 1, "rate": 1}]), (False, ""))


@ca("kiểm SePay không được hồi sinh phiếu công nợ đã hủy")
def _():
	doc = _Phieu(trang_thai="Huy", ma_phieu="DNTT-26-09-00001", tong_tien=100000)
	doc.save = Mock()
	cn = _nap("cong_no.py", ["kiem_sepay"], _kiem_quyen=Mock(), flt=_so,
		frappe=SimpleNamespace(throw=_nem, get_doc=Mock(return_value=doc), db=SimpleNamespace(commit=Mock())),
		_sepay_cn=Mock(return_value={"nhan": 100000}), _giu_gd=Mock(return_value="BT-1"),
		ghi_thu_cho_phieu=Mock(), _gui_thu_da_nhan=Mock(), xem_phieu=Mock())
	_phai_chan(lambda: cn.kiem_sepay("CN-1"), "huỷ")
	cn._sepay_cn.assert_not_called()
	doc.save.assert_not_called()
	cn.ghi_thu_cho_phieu.assert_not_called()
