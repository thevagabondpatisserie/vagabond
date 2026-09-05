# -*- coding: utf-8 -*-
"""Kiem thu phieu THANH TOAN TRUOC cho nha cung cap (anh Viet giao 21/08/2026).

Ca that: don in an phai tra truoc mot phan, moi co bao gia va hop dong, nha
in lam xong moi xuat hoa don.

Hai nhom ca dat nhat trong tep nay:

  1. TRAN LA PHAN CON LAI, khong phai tong don. Ung hai lan ma lan nao cung
     lay tong don lam tran la ung vuot gia tri don; luc hoa don ve ERPNext
     khong can tru het duoc va de lai mot khoan du No 331 khong ai giai
     thich noi.

  2. KHONG TU DUNG BANG references. `_dung_phieu` phai goi `get_payment_entry`
     cua ERPNext chu khong tu append dong tham chieu. Tu tay dung dong do la
     viet lai logic phan bo cua ERPNext, va ban sao se lech khi len phien
     ban - dung cai lam gay tinh nang can tru tu dong.
"""

import io
import os

from vagabond import tra_truoc as tt
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _ma_nguon(ten="tra_truoc.py"):
	goi = os.path.dirname(os.path.abspath(tt.__file__))
	return io.open(os.path.join(goi, ten), encoding="utf-8").read()


def _ma_js():
	goi = os.path.dirname(os.path.abspath(tt.__file__))
	return io.open(
		os.path.join(goi, "public", "js", "bep", "30-tra-truoc.js"),
		encoding="utf-8").read()


# ------------------------------------------------------------------ tran


@ca("trả trước: trần là PHẦN CÒN LẠI của đơn, không phải tổng đơn")
def _():
	# Don 10 trieu, da ung 3 trieu. Chi con ung duoc 7 trieu nua.
	duoc, tran, _v = tt.tran_tra_truoc(10000000, 3000000)
	dung("còn lập được phiếu", duoc)
	la("trần đúng phần còn lại", tran, 7000000)
	# Chua ung dong nao thi tran bang ca don.
	duoc2, tran2, _v2 = tt.tran_tra_truoc(10000000, 0)
	dung("chưa ứng thì vẫn lập được", duoc2)
	la("trần bằng tổng đơn", tran2, 10000000)


@ca("trả trước: ứng đủ rồi thì chặn, không cho ứng thêm")
def _():
	duoc, tran, vi_sao = tt.tran_tra_truoc(5000000, 5000000)
	dung("máy chặn", not duoc)
	la("trần bằng 0", tran, 0.0)
	dung("nói rõ đã ứng đủ", "đã trả trước đủ" in vi_sao)


@ca("trả trước: đơn chưa có giá thì chặn ngay từ đầu")
def _():
	# Don gia 0 la loi da gap that o phan he Nhap kho. Ung tien cho mot don
	# gia 0 la ung mot con so khong ai kiem duoc.
	duoc, _t, vi_sao = tt.tran_tra_truoc(0, 0)
	dung("máy chặn", not duoc)
	dung("nhắc điền đơn giá", "đơn giá" in vi_sao)


@ca("trả trước: đơn đã lập hoá đơn đủ thì đi đường công nợ, không ứng nữa")
def _():
	duoc, _t, vi_sao = tt.tran_tra_truoc(8000000, 0, 100)
	dung("máy chặn", not duoc)
	dung("chỉ sang luồng công nợ", "Công nợ nhà cung cấp" in vi_sao)
	# 99 phan tram thi van con phan chua lap hoa don, cho ung tiep.
	duoc2, _t2, _v2 = tt.tran_tra_truoc(8000000, 0, 99)
	dung("99 phần trăm vẫn ứng được", duoc2)


# --------------------------------------------------------------- so tien


@ca("trả trước: số tiền vượt trần bị chặn, đúng bằng trần thì qua")
def _():
	duoc, ly_do = tt.kiem_so_tien(7000001, 7000000)
	dung("vượt trần thì chặn", not duoc)
	dung("câu báo nói rõ mức tối đa", "7.000.000" in ly_do)
	dung("đúng bằng trần thì qua", tt.kiem_so_tien(7000000, 7000000)[0])


@ca("trả trước: số tiền 0 hoặc âm bị chặn")
def _():
	dung("số 0 bị chặn", not tt.kiem_so_tien(0, 1000000)[0])
	dung("số âm bị chặn", not tt.kiem_so_tien(-500000, 1000000)[0])


# ---------------------------------------------------- nguon tien, goi ten


@ca("trả trước: 141x đọc theo SỐ HIỆU chứ không theo account_type")
def _():
	# Ca 1411 lan 1412 tren he deu duoc khai account_type "Bank" vi moi cai
	# gan mot tai khoan ngan hang that. Xet theo account_type thi chung
	# thanh tien gui cua cong ty, ma ban chat la tam ung ca nhan.
	dung("1411 là quỹ tạm ứng", tt.la_quy_tam_ung("1411"))
	dung("1412 là quỹ tạm ứng", tt.la_quy_tam_ung("1412"))
	dung("11211 KHÔNG phải quỹ tạm ứng", not tt.la_quy_tam_ung("11211"))
	dung("1121 KHÔNG phải quỹ tạm ứng", not tt.la_quy_tam_ung("1121"))
	dung("rỗng thì không phải", not tt.la_quy_tam_ung(""))


@ca("trả trước: KHÔNG được gọi 141x là quỹ của bộ phận mua hàng")
def _():
	# Tren he nay khong ton tai quy nao cua Purchasing: 1411 va 1412 deu
	# dung ten anh Viet. Goi sai ten thi nguoi dung tuong day la tien cong
	# ty da giao cho bo phan, va quen mat rang phai hoan ung lai.
	nhan = tt.nhan_nguon("1411", "OCB")
	dung("gọi đúng là quỹ tạm ứng cá nhân", "tạm ứng cá nhân" in nhan)
	dung("không gọi là Purchasing", "Purchasing" not in nhan)
	dung("không gọi là quỹ bộ phận", "bộ phận" not in nhan)
	dung("tài khoản công ty gọi đúng", "công ty" in tt.nhan_nguon("11211", "MB"))


# ------------------------------------------- bang references khong duoc gay


@ca("trả trước: dựng phiếu bằng get_payment_entry của ERPNext, không tự append references")
def _():
	src = _ma_nguon()
	dung("có gọi get_payment_entry", "get_payment_entry(" in src)
	dung("truyền party_amount để ứng một phần", "party_amount=tien" in src)
	# Day la ca chan quan trong nhat cua tep nay: neu ai do sau nay thay
	# get_payment_entry bang mot vong append tay thi ca kiem phai do.
	dung("KHÔNG tự append vào bảng references",
		'append("references"' not in src and "append('references'" not in src)


@ca("trả trước: import erpnext nằm TRONG hàm, không ở đầu tệp")
def _():
	# May chay CI khong co erpnext, khong co Frappe, khong co site. De import
	# o dau tep la ca bo kiem thu tang khung chet theo. Ngay 20/08 da do CI
	# ba ca vi dung loi nay.
	src = _ma_nguon()
	dau = src.split("def _dung_phieu")[0]
	dung("đầu tệp không import erpnext", "from erpnext" not in dau and "import erpnext" not in dau)
	than = src.split("def _dung_phieu")[1]
	dung("import nằm trong thân hàm", "from erpnext.accounts" in than)


@ca("trả trước: có chốt kiểm neo đơn trước khi lưu phiếu")
def _():
	src = _ma_nguon().split("def _dung_phieu")[1]
	dung("chốt loại phiếu là Pay", '!= "Pay"' in src)
	dung("chốt đối tác khớp nhà cung cấp của đơn", "d.supplier" in src)
	dung("chốt có dòng neo vào đơn mua", "reference_doctype == PO" in src)
	dung("chốt số tiền phân bổ khác 0", "allocated_amount" in src)


@ca("trả trước: phiếu dựng ra ở bước kế toán kiểm, không tự ghi sổ")
def _():
	"""Đổi 03/09/2026: bước đầu là "Chờ FIN kiểm tra" chứ không phải "Nháp".

	Lý do dài nằm ở phần khai báo TT_CHO_FIN trong tra_truoc.py. Tóm tắt:
	tab "Nháp" của màn Duyệt phiếu chi chỉ người mang vai AP Officer mới
	thấy, mà người lập phiếu trả trước là thu mua. Phiếu vừa lập xong là
	biến khỏi mắt cả người lập lẫn kế toán, và câu app báo lại nói là đã
	gửi cho kế toán. Phiếu APP-26-08-713 nằm im như vậy sáu ngày.
	"""
	src = _ma_nguon()
	la("tên bước nháp vẫn đúng workflow đang chạy", tt.TT_NHAP, "Nháp")
	la("tên bước kế toán đúng workflow đang chạy", tt.TT_CHO_FIN, "Chờ FIN kiểm tra")
	dung("có đặt workflow_state", "workflow_state = TT_CHO_FIN" in src)
	# Khong duoc co bat ky loi goi submit nao trong tep nay.
	dung("KHÔNG có lời gọi submit", ".submit()" not in src)


# ------------------------------------------------------- chung tu bat buoc


@ca("trả trước: bắt buộc loại chứng từ và tệp đính kèm")
def _():
	src = _ma_nguon()
	dung("chặn khi loại chứng từ không thuộc danh mục", "not in CHUNG_TU" in src)
	dung("chặn khi không có tệp", "if not tep:" in src)
	dung("danh mục có Báo giá", any("báo giá" in x.lower() for x in tt.CHUNG_TU))
	dung("danh mục có Hợp đồng", any("hợp đồng" in x.lower() for x in tt.CHUNG_TU))


# ------------------------------------------------------------------ màn app


@ca("màn trả trước: đơn mua là mỏ neo, không hỏi mã số thuế để suy ra NCC")
def _():
	# Don da chot nha cung cap roi. Hoi lai ma so thue de tu do suy ra nha
	# cung cap la mo duong cho phieu tro vao mot NCC khac voi don.
	js = _ma_js()
	dung("có gọi chi_tiet_don theo đơn", "tra_truoc.chi_tiet_don" in js)
	dung("nhà cung cấp hiện ra là chỉ đọc, lấy từ đơn", "máy lấy từ đơn" in js)
	# Tra MST chi de DOI CHIEU, khong duoc dung de chon NCC.
	dung("nút MST chỉ để đối chiếu", "Đối chiếu tên với cơ quan thuế" in js)


@ca("màn trả trước: có cảnh báo quỹ tạm ứng là tiền cá nhân")
def _():
	js = _ma_js()
	dung("tách nhóm tài khoản công ty", "TÀI KHOẢN CÔNG TY" in js)
	dung("tách nhóm quỹ tạm ứng", "QUỸ TẠM ỨNG CÁ NHÂN" in js)
	dung("nói rõ phải đi tiếp đường hoàn ứng", "hoàn ứng" in js)


@ca("màn trả trước: nói rõ phiếu ở trạng thái nháp, tiền chưa đi")
def _():
	js = _ma_js()
	dung("có câu tiền chưa đi đâu", "tiền chưa đi đâu" in js)
	dung("nói rõ hai cấp duyệt", "giám đốc duyệt chi" in js)


@ca("màn trả trước: ô số tiền tự chặn trần ngay trên máy khách")
def _():
	js = _ma_js()
	# Chan o may chu la bat buoc va da co. Chan them o may khach de nguoi
	# nhap thay ngay, khong phai bam gui roi moi bi tu choi.
	dung("có đọc trần từ chi tiết đơn", "ttChiTiet && ttChiTiet.tran" in js or "ttChiTiet.tran" in js)
	dung("có cắt xuống trần", "if (v > tr) v = tr;" in js)


@ca("màn trả trước: luồng thứ năm nằm ngay dưới Công nợ nhà cung cấp")
def _():
	"""Ý ĐỊNH GỐC GIỮ NGUYÊN, chỗ đọc và câu đếm luồng thì đổi.

	Ca kiểm này dựng lúc thêm luồng trả trước, chốt ba việc: luồng đó CÓ
	trong bảng chọn, nằm ngay sau Công nợ nhà cung cấp, và lời trên màn đã
	được sửa cho khớp số luồng. Cả ba ý còn nguyên.

	v432 đổi màn từ năm nút thành hai câu hỏi (issue #196 phần A) nên:

	- Bảng chọn tách làm hai, khai ngay trên hàm chứ không nằm trong thân,
	  nên cắt theo "if (!c) return;" không còn đúng. Đọc thẳng cả tệp và so
	  vị trí năm mã luồng: thứ tự khai vẫn phải là ncc, tt, tkct rồi mới
	  tới hu_hd, hu_khd, nên phép so cũ vẫn nói đúng cái nó muốn nói.
	- Không còn câu nào đếm số luồng, vì hai câu hỏi không bày cả năm cùng
	  lúc nữa. Thay bằng phép chốt chắc hơn: đủ NĂM mã luồng, mỗi mã đúng
	  một lần. Thiếu một mã là có luồng không còn đường vào.
	"""
	goi = os.path.dirname(os.path.abspath(tt.__file__))
	js19 = io.open(
		os.path.join(goi, "public", "js", "bep", "19-ho-so-tt.js"),
		encoding="utf-8").read()
	i_ncc = js19.find("k: 'ncc'")
	i_tt = js19.find("k: 'tt'")
	i_hu = js19.find("k: 'hu_hd'")
	dung("có luồng trả trước trong bảng chọn", i_tt > 0)
	dung("nằm sau Công nợ nhà cung cấp", 0 <= i_ncc < i_tt)
	dung("nằm trước Hoàn ứng có hoá đơn", i_tt < i_hu)
	for ma in ("ncc", "tt", "tkct", "hu_hd", "hu_khd"):
		dung("luồng %s vẫn có đúng một đường vào" % ma,
			js19.count("k: '%s'" % ma) == 1)
