"""Kiem thu bo tu chon lo cho nguyen lieu bi tru.

Toi 20/08/2026 Khai bam lam mot cai Plain Croissant thi may nem ra
"Serial No / Batch No are mandatory for Item NVLT00166" - men tuoi Saf.
App chi gan lo cho THANH PHAM lam ra, con NGUYEN LIEU bi tru thi de trong.

Ca dat nhat trong tep nay la ca "lay can tung lo": chia deu thi mot me banh
dung vao bon lo men va so lo tro nen vo nghia.
"""

from vagabond import lo_hang as lh
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("chọn lô: một lô đủ thì lấy đúng lô đó, không đụng lô sau")
def _():
	ra, thieu = lh.chia_theo_lo(78, [("A", 10000), ("B", 3000)])
	la("một dòng", ra, [("A", 78.0)])
	la("không thiếu", thieu, 0.0)


@ca("chọn lô: lấy CẠN từng lô rồi mới sang lô sau, không chia đều")
def _():
	ra, thieu = lh.chia_theo_lo(100, [("A", 60), ("B", 90)])
	la("hai dòng đúng số", ra, [("A", 60.0), ("B", 40.0)])
	la("không thiếu", thieu, 0.0)


@ca("chọn lô: thiếu bao nhiêu phải nói đúng bấy nhiêu, không nuốt")
def _():
	ra, thieu = lh.chia_theo_lo(100, [("A", 30)])
	la("lấy hết lô A", ra, [("A", 30.0)])
	la("còn thiếu 70", thieu, 70.0)
	ra2, thieu2 = lh.chia_theo_lo(50, [])
	la("không lô nào", ra2, [])
	la("thiếu cả 50", thieu2, 50.0)


@ca("chọn lô: lô rỗng hoặc âm thì bỏ qua chứ không sinh dòng 0")
def _():
	ra, thieu = lh.chia_theo_lo(10, [("A", 0), ("B", -5), ("C", 10)])
	la("chỉ lô C", ra, [("C", 10.0)])
	la("không thiếu", thieu, 0.0)


@ca("chọn lô: sai số 6 chữ số thập phân không được biến thành thiếu hàng")
def _():
	ra, thieu = lh.chia_theo_lo(1, [("A", 0.9999999)])
	la("không báo thiếu", thieu, 0.0)
	dung("vẫn lấy được", len(ra) == 1)


@ca("câu thiếu hàng: phải nói kho nào còn bao nhiêu, và việc làm tiếp")
def _():
	cau = lh.cau_thieu_lo("Men tươi Saf", "NVLT00166", "Pastry - Nguyên liệu - TV",
		78, "Gram", [("Baker - Nguyên liệu - TV", 13000), ("Kho tổng 307 - TV", 0)])
	dung("nêu tên hàng", "Men tươi Saf" in cau)
	dung("nêu kho đang thiếu", "Pastry - Nguyên liệu" in cau)
	dung("nêu kho còn hàng", "Baker - Nguyên liệu" in cau)
	dung("nêu số còn", "13.000" in cau)
	dung("bỏ kho tồn 0", "Kho tổng 307" not in cau)
	dung("chỉ việc làm tiếp", "chuyển kho" in cau)


@ca("câu thiếu hàng: cả hệ hết sạch thì nói thẳng là phải nhập hàng")
def _():
	cau = lh.cau_thieu_lo("Men tươi Saf", "NVLT00166", "Pastry - Nguyên liệu - TV",
		78, "Gram", [])
	dung("không bịa ra kho nào", "đang còn ở" not in cau)
	dung("nói phải nhập hàng", "nhập hàng" in cau)


@ca("tên kho: bỏ đuôi công ty cho gọn màn hình điện thoại")
def _():
	la("bỏ đuôi TV", lh._ten_kho("Baker - Nguyên liệu - TV"), "Baker - Nguyên liệu")
	la("không có đuôi thì giữ nguyên", lh._ten_kho("Kho tổng"), "Kho tổng")
	la("rỗng", lh._ten_kho(""), "")


@ca("gắn lô: chỉ đụng dòng BỊ TRỪ, theo lô, mà chưa ai chọn lô")
def _():
	import inspect

	nguon = inspect.getsource(lh._dong_can_lo)
	dung("phải có kho xuất", 's_warehouse' in nguon)
	dung("ai chọn lô tay rồi thì thôi", 'batch_no' in nguon)
	dung("có gói lô rồi thì thôi", 'serial_and_batch_bundle' in nguon)


@ca("gắn lô: bản sao của một dòng phải bỏ tên bản gốc, nếu không mất một lô")
def _():
	import inspect

	dung("có bỏ khoá name", "name" in lh.KHOA_BO)
	dung("bỏ luôn số đã tính để máy chủ tính lại", "transfer_qty" in lh.KHOA_BO)
	nguon = inspect.getsource(lh._boc)
	dung("chỉ dòng đầu giữ tên", "giu_ten" in nguon)


@ca("gắn lô: hỏng ở đây không được kéo đổ cả phiếu")
def _():
	import inspect

	nguon = inspect.getsource(lh.gan_lo)
	dung("ném tiếp lỗi kiểm tra", "raise" in nguon)
	dung("nuốt lỗi khác và ghi nhật ký", "frappe.log_error" in nguon)
