"""Kiem thu: mot danh muc loai chung tu duy nhat cho ca ba man (v307).

Vi sao co tep nay
-----------------
Ngay 25/08/2026 ke toan khong luu duoc ho so thanh toan. O chon tren man hinh
xo ra "Hoa don VAT" lay tu danh muc dung chung, con o luu tru phia sau lai la
mot o Select cam cung 11 ten phap ly khac han. Frappe chan ngay luc luu:

    Loai chung tu dinh kem khong the la "Hoa don VAT". Phai la mot trong
    "", "Bang bao gia", "Hop dong mua ban hang hoa giua hai ben", ...

Hai bang CON deu da la o noi toi danh muc dung chung tu dau. Chi rieng o o
muc ho so con giu danh sach cam cung tu thang 8, khong ai go bo. Ma o do chi
la NHAN cho de nhin tren danh sach: loai that nam o tung dong chi.

Cach chua: o muc ho so thanh o chu thuong, chi doc, may tu dien theo dong dau
tien co khai loai. Bo danh sach cam cung di.

Ca kiem duoi day doc thang tep .json va tep .py tren dia. Khong can Frappe,
khong can site, khong keo thu vien mang nao.
"""

import io
import json
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
THU_MUC_DT = os.path.join(GOI, "vagabond", "doctype")

DANH_MUC = "Vagabond Loai Chung Tu"


def _truong(ten_doctype, ten_truong):
	"""Doc mot truong trong tep .json cua doctype. Tra None neu khong co."""
	d = os.path.join(THU_MUC_DT, ten_doctype, "%s.json" % ten_doctype)
	if not os.path.exists(d):
		return None
	kho = json.load(io.open(d, encoding="utf-8"))
	for f in kho.get("fields") or []:
		if f.get("fieldname") == ten_truong:
			return f
	return None


def _doc(ten_tep):
	return io.open(os.path.join(GOI, ten_tep), encoding="utf-8").read()


@ca("ô loại chứng từ ở mức hồ sơ không còn cấm cứng danh sách riêng")
def _():
	f = _truong("vagabond_ho_so_tt", "loai_chung_tu")
	dung("có trường loại chứng từ ở mức hồ sơ", f is not None)
	# Bay da sap that: Select cam cung 11 ten phap ly, trong khi man hinh xo ra
	# ten lay tu danh muc dung chung. Luu la Frappe chan.
	la("không phải ô Select cấm cứng", f.get("fieldtype"), "Data")
	la("không còn danh sách riêng", (f.get("options") or ""), "")
	dung("ô nhãn này chỉ đọc, máy tự điền", f.get("read_only") == 1)


@ca("hai bảng con vẫn nối thẳng vào danh mục dùng chung")
def _():
	for dt in ("vagabond_ho_so_tt_dong", "vagabond_de_nghi_chi_dong"):
		f = _truong(dt, "loai_chung_tu")
		dung("%s có trường loại chứng từ" % dt, f is not None)
		la("%s nối bằng ô chọn danh mục" % dt, f.get("fieldtype"), "Link")
		la("%s trỏ đúng danh mục dùng chung" % dt, f.get("options"), DANH_MUC)


@ca("ô chọn trên màn hình đọc đúng danh mục dùng chung, không dựng danh sách riêng")
def _():
	hs = _doc("ho_so_tt.py")
	dn = _doc("de_nghi_chi.py")
	dung("phiếu thanh toán nội bộ khai tên danh mục dùng chung",
		'DM_CT = "%s"' % DANH_MUC in dn)
	dung("màn hồ sơ trỏ đúng tên danh mục đó",
		'DM_CHUNG_TU = "%s"' % DANH_MUC in hs)
	dung("màn hồ sơ gọi lại phép dựng danh mục của phiếu nội bộ",
		"from vagabond.de_nghi_chi import dung_danh_muc_chung_tu" in hs)
	# Neu mai sau ai do dan lai mot danh sach cung vao day thi bay sap.
	dung("màn hồ sơ không dựng danh sách loại chứng từ riêng",
		"Hóa đơn giá trị gia tăng đầu vào" not in hs)


@ca("mọi tên trong danh mục mặc định đều lưu được, không tên nào bị chặn")
def _():
	dn = _doc("de_nghi_chi.py")
	dung("có bộ danh mục mặc định", "DM_CT_MAC_DINH" in dn)
	f = _truong("vagabond_ho_so_tt", "loai_chung_tu")
	# O da la Data nen khong con danh sach de doi chieu. Ca kiem nay chot lai
	# dieu do: khong co danh sach nao o mo ho so co the loai bo mot ten cua
	# danh muc chung nua.
	la("ô lưu không kèm danh sách chặn", (f.get("options") or ""), "")
