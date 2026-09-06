# -*- coding: utf-8 -*-
"""Cấp mã lệnh sản xuất và mã lô, đuôi sáu số tăng LIÊN TỤC (#206, 06/09/2026).

Anh Việt chốt: đuôi số của mã lệnh và mã lô không được đánh lại khi sang
ngày, sang tháng, sang năm. Thiết kế vòng 3 dùng chuỗi đặt tên
`LSX-.DD.MM.YY.-.######` chính là cái đánh lại theo ngày, nên đã bỏ; tên
thật nay do hai hook autoname đặt, lấy số từ `tabSeries`.

Các ca dưới đây canh đúng những chỗ đã hoặc sẽ hỏng:
- đuôi số quay vòng ở 999999 (yêu cầu nói rõ: tuyệt đối không quay vòng),
- máy đặt lại số của lô do NGƯỜI gõ (661 trên 750 lô đang có là loại này),
- hook đặt tên ném lỗi ra ngoài và chặn bếp giữa giờ làm,
- đường lùi mang cùng hình dạng với dãy mới nên có ngày đẻ ra mã trùng.

CHƯA kiểm được ở đây: cấp số THẬT, hai lượt tạo đồng thời, và giữ bộ đếm
sau khi khởi động lại. Ba thứ đó cần Frappe và cơ sở dữ liệu thật, không có
cách nào mô phỏng cho ra bằng chứng đúng nghĩa. Xem `getseries` của frappe
16.27.1: nó khoá dòng bằng `for_update` rồi mới cộng.
"""

import io
import os

from vagabond import ma_phieu_sx as mps
from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


# ------------------------------------------------------------ đuôi số


@ca("đuôi số tối thiểu sáu chữ số, số nhỏ thì đệm 0")
def _duoi_ngan():
	la("số 1", mps.duoi_so(1), "000001")
	la("số 57", mps.duoi_so(57), "000057")
	la("số 751", mps.duoi_so(751), "000751")
	la("số 0", mps.duoi_so(0), "000000")
	la("nhận cả chuỗi", mps.duoi_so("000057"), "000057")


@ca("qua 999999 thì đuôi số DÀI RA, tuyệt đối không quay về 000001")
def _khong_quay_vong():
	la("sát ngưỡng", mps.duoi_so(999999), "999999")
	la("vượt ngưỡng ra bảy chữ số", mps.duoi_so(1000000), "1000000")
	la("vượt xa", mps.duoi_so(12345678), "12345678")
	# Khong duoc cat bot: cat la hai chung tu khac nhau mang cung mot ma.
	la("không cắt còn sáu", len(mps.duoi_so(1000000)), 7)
	# Va trong ca tep khong duoc co phep chia du, vi do la cach duy nhat de
	# mot con so quay vong ma van "trong nhu dung".
	m = _py("ma_phieu_sx.py")
	dung("không có phép chia dư trong mã", " % 1000000" not in m and "% 10 ** " not in m)


@ca("đuôi số nhận rác thì trả 000000 chứ không nổ giữa lúc bếp đang lưu")
def _duoi_rac():
	la("None", mps.duoi_so(None), "000000")
	la("chữ", mps.duoi_so("bay nhieu"), "000000")
	la("số âm", mps.duoi_so(-5), "000000")


# ------------------------------------------------------------ khuôn mã


@ca("mã lệnh LSX-ddmmyy-nnnnnn, mã lô LO-yymmdd-nnnnnn")
def _khuon():
	la("lệnh", mps.ma_lenh("2026-09-06", 57), "LSX-060926-000057")
	la("lô", mps.ma_lo("2026-09-06", 751), "LO-260906-000751")
	# Hai khuon dao thu tu ngay khac nhau. Do la co y: tem lo dang in kieu
	# yymmdd tu truoc, doi lai la doi hinh dang tem cua nhung lo da in.
	la("ngày của lệnh", mps.ddmmyy("2026-09-06"), "060926")
	la("ngày của lô", mps.yymmdd("2026-09-06"), "260906")


@ca("sang ngày, sang tháng, sang năm mà đuôi số vẫn NỐI TIẾP")
def _noi_tiep():
	# Day chinh la yeu cau 06/09/2026. Bo dem la mot day so, phan ngay chi
	# di theo; hai viec doc lap.
	la("06/09 số 10", mps.ma_lenh("2026-09-06", 10), "LSX-060926-000010")
	la("07/09 số 11", mps.ma_lenh("2026-09-07", 11), "LSX-070926-000011")
	la("sang tháng số 12", mps.ma_lenh("2026-10-01", 12), "LSX-011026-000012")
	la("sang năm số 13", mps.ma_lenh("2027-01-01", 13), "LSX-010127-000013")
	la("lô sang ngày", mps.ma_lo("2026-09-07", 752), "LO-260907-000752")
	la("lô sang năm", mps.ma_lo("2027-01-01", 900), "LO-270101-000900")


@ca("mã mới KHÔNG THỂ trùng mã cũ, vì khác độ dài đuôi số")
def _khong_trung():
	# Lo cu co duoi BON chu so (LO-260906-0002), ma moi luon tu SAU chu so
	# tro len. Khac do dai thi khong co cach nao ra cung mot chuoi.
	moi = mps.ma_lo("2026-09-06", 2)
	la("lô mới của số 2", moi, "LO-260906-000002")
	dung("không trùng lô cũ", moi != "LO-260906-0002")
	# Lenh cu theo thang va theo nam deu khac hinh dang.
	l = mps.ma_lenh("2026-09-06", 10)
	dung("khác mã tháng", l != "LSX-26-09-0010")
	dung("khác mã năm", l != "LSX-2026-00010")
	dung("khác mã ERPNext gốc", l != "MFG-WO-2026-00048")


# ------------------------------------------------------------ lô người gõ


@ca("nhận ra lô do MÁY đặt số theo khuôn, không nhận lô người gõ")
def _lo_may_dat():
	la("lô máy đặt kiểu cũ", mps.la_ma_lo_may_dat("LO-260906-0002"), True)
	la("lô máy đặt kiểu mới", mps.la_ma_lo_may_dat("LO-260906-000751"), True)
	la("mã lô nhà cung cấp", mps.la_ma_lo_may_dat("KKK2600007-NVLT00026"), False)
	la("số trần", mps.la_ma_lo_may_dat("12"), False)
	la("rỗng", mps.la_ma_lo_may_dat(""), False)


class _Ho(object):
	"""Hồ sơ giả, đủ những gì hai hook đụng tới."""

	def __init__(self, doctype, ten=None, batch_id=None):
		self.doctype = doctype
		self.name = ten
		self.batch_id = batch_id
		self.flags = _Co()

	def get(self, o):
		return getattr(self, o, None)


class _Co(dict):
	"""Bắt chước frappe._dict: đọc bằng dấu chấm lẫn .get()."""

	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v


_THAT = (mps._so_moi, mps._chua_ai_mang, mps._hom_nay)


def _tra_lai():
	mps._so_moi, mps._chua_ai_mang, mps._hom_nay = _THAT


def _thay(so="000057", trung=(), ngay="2026-09-06"):
	"""Thay ba cửa chạm hệ. `trung` là các mã coi như đã có người mang."""
	mps._so_moi = lambda khoa: so
	mps._chua_ai_mang = lambda dt, ten: ten not in trung
	mps._hom_nay = lambda: ngay


@ca("hook đặt tên lệnh: chưa có tên thì đặt LSX theo ngày tạo và số của bộ đếm")
def _hook_lenh():
	_thay(so="000057")
	d = _Ho("Work Order")
	mps.dat_ten_lenh(d)
	_tra_lai()
	la("tên đặt xong", d.name, "LSX-060926-000057")


@ca("hook đặt tên lệnh KHÔNG cãi tên ai đã đặt, kể cả bản sửa của Frappe")
def _hook_lenh_da_co_ten():
	# Frappe dat ten rieng cho ban SUA (amended) truoc khi toi autoname.
	# Ghi de o day la ban sua mat moi noi ve ban goc.
	_thay(so="000057")
	d = _Ho("Work Order", ten="LSX-26-09-0010-1")
	mps.dat_ten_lenh(d)
	_tra_lai()
	la("giữ nguyên", d.name, "LSX-26-09-0010-1")


@ca("hook đặt tên lệnh bỏ qua doctype khác, hook rộng là cách phá cả hệ")
def _hook_lenh_doctype_khac():
	# Ngay 16/08/2026 mot hook dat tren "*" xoa trang o sender cua Email
	# Queue, ca tiem khong gui duoc email suot bon ngay.
	_thay(so="000057")
	d = _Ho("Stock Entry")
	mps.dat_ten_lenh(d)
	_tra_lai()
	la("không đụng", d.name, None)


@ca("mã vừa cấp đã có người mang thì lấy số khác, không ghi đè chứng từ ai")
def _hook_lenh_trung():
	so = ["000057", "000058"]
	mps._so_moi = lambda khoa: so.pop(0)
	mps._chua_ai_mang = lambda dt, ten: ten != "LSX-060926-000057"
	mps._hom_nay = lambda: "2026-09-06"
	d = _Ho("Work Order")
	mps.dat_ten_lenh(d)
	_tra_lai()
	la("nhảy sang số kế tiếp", d.name, "LSX-060926-000058")


@ca("cấp số hỏng thì hook IM LẶNG nhường Frappe, không ném lỗi lên mặt bếp")
def _hook_lenh_hong():
	def no(khoa):
		raise RuntimeError("gia lap tabSeries hong")

	mps._so_moi = no
	mps._chua_ai_mang = lambda dt, ten: True
	mps._hom_nay = lambda: "2026-09-06"
	d = _Ho("Work Order")
	try:
		mps.dat_ten_lenh(d)
	except Exception:
		_tra_lai()
		dung("không được ném lỗi ra ngoài", False)
		return
	_tra_lai()
	la("để trống cho Frappe đặt theo naming_series", d.name, None)


@ca("hook đặt tên lô: người GÕ số lô thì máy không đặt lại")
def _hook_lo_nguoi_go():
	# 661 tren 750 lo dang co la ma lo nha cung cap go tay. Doi so cua ho la
	# mat dau vet truy xuat ve lo goc.
	_thay(so="000751")
	d = _Ho("Batch", batch_id="KKK2600007-NVLT00026")
	mps.nho_nguoi_go_lo(d)
	d.name = "KKK2600007-NVLT00026"
	mps.dat_ten_lo(d)
	_tra_lai()
	la("giữ số người gõ", d.name, "KKK2600007-NVLT00026")
	la("batch_id cũng giữ", d.batch_id, "KKK2600007-NVLT00026")


@ca("hook đặt tên lô: máy đặt số thì đặt CẢ batch_id lẫn name")
def _hook_lo_may_dat():
	# Lech hai o la tem in mot dang so sach mot neo.
	_thay(so="000751")
	d = _Ho("Batch")
	mps.nho_nguoi_go_lo(d)
	d.batch_id = "LO-260906-0003"
	d.name = "LO-260906-0003"
	mps.dat_ten_lo(d)
	_tra_lai()
	la("name mới", d.name, "LO-260906-000751")
	la("batch_id mới", d.batch_id, "LO-260906-000751")


@ca("không có dấu vết before_naming thì chỉ đặt lại mã ĐÚNG KHUÔN máy")
def _hook_lo_khong_co_co():
	# Duong lui khi mot luong nao do khong chay before_naming. Doan bua o
	# day la doi so lo cua nha cung cap.
	_thay(so="000751")
	d = _Ho("Batch")
	d.name = "KKK2600007-NVLT00026"
	mps.dat_ten_lo(d)
	_tra_lai()
	la("không đụng lô người gõ", d.name, "KKK2600007-NVLT00026")

	_thay(so="000751")
	d2 = _Ho("Batch")
	d2.name = "LO-260906-0003"
	mps.dat_ten_lo(d2)
	_tra_lai()
	la("lô đúng khuôn thì đặt lại", d2.name, "LO-260906-000751")


@ca("đặt tên lô hỏng cũng im lặng, hoàn tất lệnh không được đứng vì số lô")
def _hook_lo_hong():
	def no(khoa):
		raise RuntimeError("gia lap tabSeries hong")

	mps._so_moi = no
	mps._chua_ai_mang = lambda dt, ten: True
	mps._hom_nay = lambda: "2026-09-06"
	d = _Ho("Batch")
	mps.nho_nguoi_go_lo(d)
	d.batch_id = "LO-260906-0003"
	d.name = "LO-260906-0003"
	try:
		mps.dat_ten_lo(d)
	except Exception:
		_tra_lai()
		dung("không được ném lỗi ra ngoài", False)
		return
	_tra_lai()
	la("giữ tên ERPNext vừa đặt", d.name, "LO-260906-0003")


# ------------------------------------------------------------ dòng đếm


@ca("dòng đếm chỉ DỰNG khi chưa có, không bao giờ hạ số của dòng đã có")
def _moc_bo_dem():
	# Ha so la cap lai nhung so da phat, tuc hai chung tu mang mot ma.
	m = _py("ma_phieu_sx.py")
	doan = m.split("def dat_moc_bo_dem(")[1].split("\ndef ")[0]
	dung("có đọc dòng đang có trước", "select `current` from `tabSeries`" in doan)
	dung("thấy rồi thì đi ra", "giu nguyen" in doan)
	dung("chỉ insert, không update", "insert into `tabSeries`" in doan)
	dung("không có câu update nào", "update `tabSeries`" not in doan.lower())
	dung("không xoá dòng nào", "delete" not in doan.lower())


@ca("cấp số đi qua getseries của Frappe, không MAX+1 và không đếm bản ghi")
def _cap_so_nguyen_tu():
	# MAX+1 khong khoa dong: hai luot cung luc doc ra cung mot so. Dem ban
	# ghi con te hon, chung tu huy cung bi tinh vao.
	m = _py("ma_phieu_sx.py")
	doan = m.split("def _so_moi(")[1].split("\ndef ")[0]
	dung("dùng getseries", "getseries(khoa, SO_CHU_SO)" in doan)
	dung("không MAX+1", "max(" not in doan.lower())
	dung("đi vòng qua duoi_so", "duoi_so(so)" in doan)
	dung("có cảnh báo trước ngưỡng", "NGUONG_CANH_BAO" in doan)


@ca("hai dãy RIÊNG cho lệnh và cho lô, không gộp làm một")
def _hai_day():
	la("khoá của lệnh", mps.KHOA_LENH, "LSX")
	la("khoá của lô", mps.KHOA_LO, "LO")
	dung("hai khoá khác nhau", mps.KHOA_LENH != mps.KHOA_LO)
	la("lệnh đếm theo Work Order", mps.MOC_THEO_KHOA[mps.KHOA_LENH], "Work Order")
	la("lô đếm theo Batch", mps.MOC_THEO_KHOA[mps.KHOA_LO], "Batch")


@ca("ba hook đặt tên phải được khai trong hooks.py, khai thiếu là hook không chạy")
def _khai_hook():
	# Viet ham ma quen khai la ma van ra kieu cu, khong ai bao gi ca.
	h = _py("hooks.py")
	dung("hook tên lệnh", '"autoname": "vagabond.ma_phieu_sx.dat_ten_lenh"' in h)
	dung("hook nhớ người gõ lô", '"before_naming": "vagabond.ma_phieu_sx.nho_nguoi_go_lo"' in h)
	dung("hook tên lô", '"autoname": "vagabond.ma_phieu_sx.dat_ten_lo"' in h)
	dung("khai dưới đúng doctype Batch", '"Batch": {' in h)


@ca("soát bộ đếm CHỈ ĐỌC, xem số không được tiêu mất một số")
def _soat_chi_doc():
	m = _py("ma_phieu_sx.py")
	doan = m.split("def soat_bo_dem(")[1].split("\ndef ")[0]
	dung("không cấp số", "getseries" not in doan)
	dung("không ghi gì", "insert" not in doan.lower() and "update" not in doan.lower())
	dung("có kiểm quyền", "_kiem_quyen()" in doan)
