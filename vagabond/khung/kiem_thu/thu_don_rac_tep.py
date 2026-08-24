"""Kiem thu: nhip don rac khong duoc dung toi tep cua nguoi khac.

Vi sao co tep nay
-----------------
Ngay 24/08/2026 phat hien `van_don.don_dep_anh_giao` loc File theo "thuoc
phieu nao" ma quen loc theo "nam o o nao", nen no om ca CHU KY KHACH vao
dien don dep sau 30 ngay. Chu ky la chung tu giao nhan. May man chu ky moi
co tu 08/08 nen chua to nao du 30 ngay, va som hon 14 ngay.

Bai hoc khong nam o mot dong ma o CACH NGHI: khi quet tep de xoa, phai hoi
du ba cau, thieu cau nao cung du de xoa nham.

  1. Tep nay thuoc CHUNG TU nao      -> attached_to_doctype
  2. Tep nay nam o O nao cua chung tu -> attached_to_field
  3. Con AI KHAC dang dung tep nay khong -> cac dong File chung file_url

Ham cu cua `minvoice_tep.don_dep_pdf` tra loi duoc cau 1, khong hoi cau 2,
va tra loi SAI cau 3: no xoa moi dong tro cung `file_url` bat ke dong do
thuoc ai. Cai bay that: ke toan dinh chinh to PDF hoa don ay vao Payment
Entry lam chung tu goc, ma `chung_tu_tien.chan_thieu_dinh_kem` DEM tep tren
Payment Entry. Phieu da ghi so se lang le mat can cu sau 60 ngay.

Bo ca kiem duoi day chot ca hai nhip, va co ca dao chieu: bo hang rao di
thi ca kiem phai do.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	p = os.path.join(GOI, ten)
	if not os.path.exists(p):
		return ""
	return io.open(p, encoding="utf-8").read()


def _nap_thuan():
	"""Nap rieng phan THUAN cua minvoice_tep, khong keo theo frappe.

	Mo dun that `import frappe` o giua tep. May chay CI khong co frappe va
	khong co site, nen cat lay phan tren roi exec. Cach nay da dung o cac
	bo kiem khac trong repo.
	"""
	ma = _doc("minvoice_tep.py")
	moc = "# ------------------------------------------------------- phan can Frappe"
	assert moc in ma, "minvoice_tep.py doi cau truc, khong tim thay moc phan thuan"
	khong_gian = {}
	exec(compile(ma.split(moc)[0], "minvoice_tep_thuan", "exec"), khong_gian)
	return khong_gian


TH = _nap_thuan()
don_duoc = TH["don_duoc_nhom_tep"]
NOI_DINH = TH["NOI_DINH"]

HD = "MInvoice Invoice"
HS = "Vagabond Ho So TT"


def _t(ten, dt, o=""):
	return {"name": ten, "attached_to_doctype": dt, "attached_to_field": o}


# ------------------------------------------------------------- cho phep

@ca("chỉ có bản gốc trên hoá đơn thì dọn được")
def _():
	duoc, ly_do, ds = don_duoc(_t("F1", HD), [])
	dung("cho dọn", duoc)
	la("dọn đúng một tệp", ds, ["F1"])
	la("không có lý do từ chối", ly_do, "")


@ca("bản gốc trên hoá đơn cộng bản sao trên hồ sơ thì dọn cả cụm")
def _():
	duoc, _l, ds = don_duoc(_t("F1", HD), [_t("F2", HS), _t("F3", HS)])
	dung("cho dọn", duoc)
	# Ban sao xoa truoc, dong goc xoa sau: noi dung tren dia di theo dong
	# cuoi cung, xoa nguoc lai la ban sao tro vao hu khong mot nhip.
	la("bản sao xoá trước, gốc xoá sau", ds, ["F2", "F3", "F1"])


# -------------------------------------------------------------- từ chối

@ca("có bản đính vào Payment Entry thì KHÔNG được đụng tới cả cụm")
def _():
	# Day la ca that: ke toan dinh to PDF vao phieu chi lam chung tu goc.
	duoc, ly_do, ds = don_duoc(_t("F1", HD), [_t("F9", "Payment Entry")])
	dung("từ chối dọn", not duoc)
	la("không xoá gì cả", ds, [])
	dung("lý do nói rõ tệp thuộc ai", "Payment Entry" in ly_do)


@ca("một tệp lạ trong cụm là giữ nguyên CẢ cụm, không xoá phần của mình")
def _():
	duoc, _l, ds = don_duoc(
		_t("F1", HD), [_t("F2", HS), _t("F9", "Sales Invoice")]
	)
	dung("từ chối dọn", not duoc)
	# Xoa bot van con an toan ve mat du lieu, nhung giu ca cum thi khong
	# phai suy nghi lan nao nua. Chon duong khong phai suy nghi.
	la("kể cả bản sao của mình cũng không xoá", ds, [])


@ca("tệp mang tên ô thì không được xoá, dù nằm đúng chỗ của mình")
def _():
	# Mang `attached_to_field` nghia la tep nay LA gia tri cua mot o tren
	# chung tu. Xoa no la de lai mot o tro vao hu khong. Dung cai da xay
	# ra voi chu ky khach ben van don.
	duoc, ly_do, ds = don_duoc(_t("F1", HD, o="vgb_pdf"), [])
	dung("từ chối dọn", not duoc)
	la("không xoá gì cả", ds, [])
	dung("lý do nhắc tên ô", "vgb_pdf" in ly_do)


@ca("tệp không khai thuộc chứng từ nào thì cũng không đụng")
def _():
	duoc, _l, ds = don_duoc(_t("F1", ""), [])
	dung("từ chối dọn", not duoc)
	la("không xoá gì cả", ds, [])


# ------------------------------------------- nhịp cron gọi đúng hàng rào

@ca("nhịp dọn PDF thật sự đi qua hàng rào, không tự quét lấy")
def _():
	ma = _doc("minvoice_tep.py")
	than = ma.split("def don_dep_pdf(")[1]
	dung("có gọi hàng rào", "don_duoc_nhom_tep(" in than)
	# Dao chieu: neu ai do bo hang rao di roi xoa thang, cau nay do.
	dung(
		"không còn xoá thẳng mọi dòng chung file_url",
		"pluck=\"name\"" not in than,
	)
	dung("có đọc attached_to_field ra để xét", "attached_to_field" in than)
	dung("bỏ qua thì ghi lại cho người đọc", "log_error" in than)


@ca("nhịp dọn ảnh vận đơn vẫn còn hai hàng rào của v294")
def _():
	# Chot lai o day luon, de hai nhip don rac nam chung mot bo kiem. Mat
	# mot trong hai la ca kiem do.
	ma = _doc("van_don.py")
	than = ma.split("def don_dep_anh_giao(")[1].split("\n@")[0]
	dung("lọc đúng ô ảnh giao", '"attached_to_field": "anh_giao"' in than)
	dung("còn hàng rào thứ hai cho chữ ký", "ky == f.file_url" in than)


@ca("hai nơi đính tệp của m-invoice khớp với danh sách NƠI ĐÍNH")
def _():
	# NOI_DINH phai theo kip ma nguon. Them cho dinh thu ba ma quen khai
	# o day thi nhip don se tu choi don, im lang, va tep chat dong mai.
	ma = _doc("minvoice_tep.py")
	la("khai đúng hai nơi", sorted(NOI_DINH), sorted([HD, HS]))
	dung("mã nguồn còn dùng hằng số DT_HD", 'DT_HD = "%s"' % HD in ma)
	dung("mã nguồn còn dùng hằng số DT_HS", 'DT_HS = "%s"' % HS in ma)
