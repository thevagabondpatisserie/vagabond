"""Kiem thu bo chuyen doi Phantom cho cap BTP thanh phan.

Anh Viet giao 21/08/2026. Ca dat nhat trong tep nay la ca "chua tro cong
thuc con thi van phai bat no": chieu 21/08 doc so that thi 300 tren 371
dong BTP nam trong cac BOM dang chay deu co do_not_explode bang 1 VA
bom_no de trong. Bo co ma khong dien bom_no thi khong co gi de no xuong,
lenh san xuat se doi dung cai ma vua bi bo ton kho, va bep dung.
"""

from vagabond import phantom as ph
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("phantom: dòng BTP đã trỏ công thức con và đang mở nổ thì để yên")
def _():
	viec, _vs = ph.viec_cua_dong(ph.CHANG_BTP, 0, True)
	la("không đụng", viec, ph.KHONG_DUNG)


@ca("phantom: dòng BTP đang chặn nổ thì phải mở, nếu không lệnh đòi mã Phantom")
def _():
	viec, vs = ph.viec_cua_dong(ph.CHANG_BTP, 1, True)
	la("bật nổ", viec, ph.BAT_NO)
	dung("nói rõ vì sao", "Phantom" in vs)


@ca("phantom: dòng BTP chưa trỏ công thức con thì vẫn phải xử, đây là 300 dòng thật")
def _():
	viec, vs = ph.viec_cua_dong(ph.CHANG_BTP, 1, False)
	la("bật nổ", viec, ph.BAT_NO)
	dung("nêu đúng cái thiếu", "công thức con" in vs)
	viec2, _vs2 = ph.viec_cua_dong(ph.CHANG_BTP, 0, False)
	la("mở cờ rồi mà thiếu bom_no vẫn phải xử", viec2, ph.BAT_NO)


@ca("phantom: hai cấp C1 và C2 phải CHẶN nổ, không được nổ xuyên xuống NVL")
def _():
	for chang in (ph.CHANG_C1, ph.CHANG_C2):
		viec, vs = ph.viec_cua_dong(chang, 0, True)
		la("chặn nổ " + chang, viec, ph.CHAN_NO)
		dung("nói rõ hậu quả " + chang, "giữ tồn" in vs)
		la("đã chặn rồi thì thôi " + chang,
			ph.viec_cua_dong(chang, 1, True)[0], ph.KHONG_DUNG)


@ca("phantom: nguyên vật liệu và chặng lạ thì không đụng vào, không đoán bừa")
def _():
	la("nguyên vật liệu", ph.viec_cua_dong("", 0, False)[0], ph.KHONG_DUNG)
	la("chặng lạ", ph.viec_cua_dong("Chặng Lạ", 1, True)[0], ph.KHONG_DUNG)
	la("thành phẩm", ph.viec_cua_dong(ph.CHANG_TP, 0, True)[0], ph.KHONG_DUNG)


@ca("phantom: lệnh sản xuất đã xong hoặc đã huỷ thì không chặn chuyển đổi")
def _():
	dung("đang chạy thì treo", ph.wo_con_treo("In Process", 1))
	dung("chưa bắt đầu thì treo", ph.wo_con_treo("Not Started", 1))
	dung("nháp cũng treo", ph.wo_con_treo("Draft", 0))
	dung("xong rồi thì thôi", not ph.wo_con_treo("Completed", 1))
	dung("đã đóng thì thôi", not ph.wo_con_treo("Closed", 1))
	dung("đã dừng thì thôi", not ph.wo_con_treo("Stopped", 1))
	dung("đã huỷ thì thôi", not ph.wo_con_treo("In Process", 2))


@ca("phantom: câu từ chối phải nói việc phải làm tiếp, không chỉ nói không")
def _():
	cau = ph.cau_chan(1, 4)
	dung("nêu số lệnh", "4 lệnh" in cau)
	dung("nêu số mã còn tồn", "1 mã" in cau)
	dung("chỉ đường đi tiếp", "Dọn chứng từ thử" in cau)
	dung("nói hậu quả nếu bỏ qua", "nằm lại trong kho" in cau)
	la("không vướng gì thì không có câu chặn", ph.cau_chan(0, 0), "")


@ca("phantom: chạy thật phải gọi rõ, gọi trống là chỉ chạy thử")
def _():
	import inspect

	tham = inspect.signature(ph.chuyen).parameters
	la("mặc định là chạy thử", tham["chay_that"].default, 0)
	nguon = inspect.getsource(ph.chuyen)
	dung("chưa chạy thật thì trả về sớm", "if not that:" in nguon)
	dung("chạy thật mới đụng hàng rào", "hang_rao" in nguon)


@ca("phantom: sửa dòng công thức TRƯỚC, đổi mã hàng SAU, để nửa chừng vẫn chạy được")
def _():
	import inspect

	nguon = inspect.getsource(ph.chuyen)
	vt_dong = nguon.find('"BOM Item"')
	vt_ma = nguon.find('"is_stock_item"')
	dung("có cả hai bước", vt_dong > 0 and vt_ma > 0)
	dung("dòng công thức đứng trước", vt_dong < vt_ma)


@ca("phantom: ghi thẳng xuống bảng thì phải tự dựng hàng rào thay ERPNext")
def _():
	import inspect

	nguon = inspect.getsource(ph._hang_rao)
	dung("soi lệnh treo", "_lenh_treo" in nguon)
	dung("soi tồn còn lại", "_ton_con_lai" in nguon)
	dung("tồn hoặc lệnh là chặn", "bool(lenh or ton)" in nguon)


@ca("phantom: đóng lệnh chứ không xoá, giữ nguyên vết theo QT-20")
def _():
	import inspect

	nguon = inspect.getsource(ph.dong_lenh)
	dung("dùng đường Close của ERPNext", "stop_unstop" in nguon)
	dung("không xoá", "delete" not in nguon)
