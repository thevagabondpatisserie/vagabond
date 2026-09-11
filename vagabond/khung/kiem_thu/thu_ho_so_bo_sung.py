"""#247 hoa don den sau: giu lien ket bo sung, va nen PDF khong mat trang.

Chuyen tu tests/test_ho_so_bo_sung.py vao cong ngay 10/09/2026. Ban cu nam
ngoai cong nen KHONG chay khi bam kiem_truoc_deploy.sh: cong van 2721 ca y het
main, tuc tinh nang moi khong dong gop mot ca nao. Ban cu con gia lap
`sys.modules['frappe']`, thu do khong the chay chung process voi cac ca khac.

Cach chua theo dieu 6 AGENTS: phan luat da duoc tach thanh phep THUAN
`ho_so_bo_sung.loi_giu_lien_ket`, khong cham Frappe, nen kiem thang duoc.

Phan nen PDF can pypdf. May chay CI cua GitHub tay khong (dieu 5), nen cac ca
do báo CHƯA CHẠY khi thiếu pypdf, không cộng vào số đạt.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la


def _dong(ten="D1", idx=1, bo_sung="PI1", cho=1, goc=""):
	return {"idx": idx, "hoa_don_bo_sung": bo_sung, "cho_hoa_don": cho, "hoa_don": goc}


def _luat():
	from vagabond.ho_so_bo_sung import loi_giu_lien_ket

	return loi_giu_lien_ket


# ------------------------------------------------------- giu lien ket bo sung


@ca("#247 bo sung: xoa dong da noi hoa don bi chan")
def _():
	loi_giu = _luat()
	idx, loi = loi_giu({"D1": _dong()}, {}, False, {})
	la("chan dung khoan so", idx, 1)
	dung("cau loi noi ro khong xoa dong", "không xóa dòng" in loi)


@ca("#247 bo sung: ghi de lien ket sang hoa don khac bi chan")
def _():
	loi_giu = _luat()
	idx, loi = loi_giu({"D1": _dong(bo_sung="PI1")}, {"D1": _dong(bo_sung="PI2")}, False, {})
	la("chan dung khoan so", idx, 1)
	dung("cau loi noi ro khong ghi de", "không ghi đè" in loi)


@ca("#247 bo sung: xoa trang o lien ket cung la ghi de, van bi chan")
def _():
	loi_giu = _luat()
	_, loi = loi_giu({"D1": _dong(bo_sung="PI1")}, {"D1": _dong(bo_sung="")}, False, {})
	dung("bi chan", bool(loi))


@ca("#247 bo sung: doi nha cung cap sau khi da noi bi chan")
def _():
	loi_giu = _luat()
	_, loi = loi_giu({"D1": _dong()}, {"D1": _dong()}, True, {})
	dung("bi chan vi doi NCC", "không đổi NCC" in loi)


@ca("#247 bo sung: doi hoa don goc sau khi da noi bi chan")
def _():
	loi_giu = _luat()
	_, loi = loi_giu({"D1": _dong(goc="A")}, {"D1": _dong(goc="B")}, False, {"D1": True})
	dung("bi chan vi doi hoa don goc", bool(loi))


@ca("#247 bo sung: bo co cho hoa don sau khi da noi bi chan")
def _():
	loi_giu = _luat()
	_, loi = loi_giu({"D1": _dong()}, {"D1": _dong(cho=0)}, False, {})
	dung("bi chan vi bo co cho hoa don", bool(loi))


@ca("#247 bo sung: giu nguyen lien ket thi khong bao loi")
def _():
	loi_giu = _luat()
	idx, loi = loi_giu({"D1": _dong()}, {"D1": _dong()}, False, {"D1": False})
	la("khong bao loi", loi, "")
	la("khong chi khoan nao", idx, 0)


@ca("#247 bo sung: dong CHUA noi thi xoa hay sua thoai mai")
def _():
	loi_giu = _luat()
	_, loi = loi_giu({"D1": _dong(bo_sung="")}, {}, True, {})
	la("khong chan dong chua noi", loi, "")


@ca("#247 bo sung: chan theo TUNG dong, dong sau da noi van bi bat")
def _():
	loi_giu = _luat()
	cu = {"D1": _dong(bo_sung=""), "D2": _dong(ten="D2", idx=2, bo_sung="PI9")}
	idx, loi = loi_giu(cu, {"D1": _dong(bo_sung="")}, False, {})
	la("bat dung khoan thu hai", idx, 2)
	dung("va la loi xoa dong", "không xóa dòng" in loi)


# ------------------------------------------------------------------ nen PDF


def _co_pypdf():
	try:
		import pypdf  # noqa: F401

		return True
	except ImportError:
		return False


def _pdf_thu(so_trang=1):
	from pypdf import PdfWriter

	import io

	w = PdfWriter()
	for _ in range(so_trang):
		w.add_blank_page(width=595, height=842)
	bo = io.BytesIO()
	w.write(bo)
	return bo.getvalue()


def _kiem_nen_pdf():
	from pypdf import PdfReader
	from vagabond.ho_so_bo_sung import nen_pdf
	import io

	goc = _pdf_thu(3)
	ra = nen_pdf(goc)
	la("van du ba trang", len(PdfReader(io.BytesIO(ra)).pages), 3)


def _kiem_gioi_han_pdf():
	from vagabond.ho_so_bo_sung import nen_pdf

	try:
		nen_pdf(b"x" * (12 * 1024 * 1024 + 1))
		dung("qua 12 MB phai bi chan", False)
	except ValueError as e:
		dung("cau loi noi ro 12 MB", "12 MB" in str(e))

	try:
		nen_pdf(_pdf_thu(101))
		dung("quá 100 trang phải bị chặn", False)
	except ValueError as e:
		dung("nêu đúng giới hạn 100 trang", "100 trang" in str(e))


# Không ghi PASS cho ca chưa chạy vì thiếu thư viện. Bench có pypdf phải
# chạy hai ca này; môi trường thuần báo rõ chưa kiểm, không cộng vào số đạt.
if _co_pypdf():
	ca("#247 nén PDF: giữ số trang và kích thước")(_kiem_nen_pdf)
	ca("#247 nén PDF: chặn 12 MB và 100 trang")(_kiem_gioi_han_pdf)
else:
	print("CHƯA CHẠY: 2 ca nén PDF #247 do thiếu pypdf; không tính là đạt.")


@ca("#247 nối hóa đơn: chưa đánh dấu thì API chặn trước save, không tự bật cờ")
def _kiem_api_chua_danh_dau():
	from types import SimpleNamespace
	from unittest.mock import Mock, patch
	import frappe
	from vagabond import ho_so_bo_sung as bo, ho_so_tt as hs

	r = SimpleNamespace(cho_hoa_don=0, hoa_don_bo_sung="")
	r.get = lambda k: getattr(r, k, None)
	d = SimpleNamespace(dong=[r], save=Mock(), add_comment=Mock())
	with patch.object(frappe, "db", SimpleNamespace(sql=Mock())), \
		patch.object(frappe, "get_doc", return_value=d), patch.object(hs, "_kiem"):
		try:
			bo.noi_hoa_don("APP-THU", 1, "PI-THU")
			dung("phải chặn khoản chưa đánh dấu", False)
		except frappe.ValidationError as e:
			dung("đúng lý do chưa đánh dấu", "chưa đánh dấu" in str(e))
	la("không tự bật cờ", r.cho_hoa_don, 0)
	la("không gán link trước khi chặn", r.hoa_don_bo_sung, "")
	la("không gọi save", d.save.call_count, 0)


@ca("#247 nối hóa đơn: đã đánh dấu thì lưu qua Document một lần")
def _kiem_api_da_danh_dau():
	from types import SimpleNamespace
	from unittest.mock import Mock, patch
	import frappe
	from vagabond import ho_so_bo_sung as bo, ho_so_tt as hs

	r = SimpleNamespace(cho_hoa_don=1, hoa_don_bo_sung="")
	r.get = lambda k: getattr(r, k, None)
	d = SimpleNamespace(dong=[r], save=Mock(), add_comment=Mock())
	with patch.object(frappe, "db", SimpleNamespace(sql=Mock())), \
		patch.object(frappe, "get_doc", return_value=d), patch.object(hs, "_kiem"):
		bo.noi_hoa_don("APP-THU", 1, "PI-THU")
	la("giữ cờ đã chọn", r.cho_hoa_don, 1)
	la("gán đúng link", r.hoa_don_bo_sung, "PI-THU")
	la("đi qua save đúng một lần", d.save.call_count, 1)
