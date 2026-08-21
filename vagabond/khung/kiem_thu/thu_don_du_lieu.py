"""Kiem thu bo don du lieu san xuat va danh muc cong thuc (21/08/2026).

Hai mo dun sinh doi: don_du_lieu.py don mot lan, cong_thuc.py song lau dai.
Ca dat nhat o day la ca phien ban BOM: duong "dieu chinh" KHONG cancel ban
cu (ERPNext chan cancel khi co lenh san xuat tro vao), ma ghi so ban moi
roi ha ban cu xuong is_active=0. Neu ai do "sua gon" thanh cancel la vo
tran ngay khi dung vao cong thuc da tung chay lenh.
"""

from vagabond import cong_thuc as ct
from vagabond import don_du_lieu as dd
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("mã thay thế: nhóm 5 mã ra đúng 10 cặp, không cặp nào lặp")
def _():
	cap = dd.cap_thay_the(dd.NHOM_BO_LAT)
	la("số cặp", len(cap), 10)
	la("không lặp", len(set(cap)), 10)
	dung("không có cặp tự thay mình", all(a != b for a, b in cap))


@ca("mã thay thế: bơ tấm cán lớp KHÔNG được nằm trong nhóm bơ khối")
def _():
	dung("nhóm chỉ có mã bơ lạt khối",
		all(m.startswith("NVLT") for m in dd.NHOM_BO_LAT))
	# NVLT00243 la bo tam Echire (Butter Sheet) - thay bo khoi bang bo tam
	# la hong ca me croissant.
	dung("không lẫn bơ tấm", "NVLT00243" not in dd.NHOM_BO_LAT)


@ca("đổi tên: dòng thiếu mã, tên trống, tên trùng đều bị gạt với lý do rõ")
def _():
	la("thiếu mã", dd.doi_ten_hop_le("", "Tên", "Cũ")[0], False)
	la("tên trống", dd.doi_ten_hop_le("NVLT00001", "  ", "Cũ")[0], False)
	la("tên trùng", dd.doi_ten_hop_le("NVLT00001", "Cũ", "Cũ")[0], False)
	la("tên quá dài", dd.doi_ten_hop_le("NVLT00001", "x" * 141, "Cũ")[0], False)
	la("dòng chuẩn", dd.doi_ten_hop_le("NVLT00001", "Mới", "Cũ")[0], True)


@ca("nạp BOM thư viện: khối thiếu mã, thiếu mẻ, thiếu ghép đều bị gạt")
def _():
	goc = {"ma_btp": "BTPB00060", "me_gram": 5100, "dong": [{"ma": "NVLT00242"}],
		"thieu_ma": [], "sl_hong": []}
	la("khối chuẩn", dd.khoi_nap_duoc(dict(goc))[0], True)
	la("chưa có mã BTP", dd.khoi_nap_duoc(dict(goc, ma_btp=""))[0], False)
	la("không có mẻ", dd.khoi_nap_duoc(dict(goc, me_gram=None))[0], False)
	la("còn nguyên liệu chưa ghép",
		dd.khoi_nap_duoc(dict(goc, thieu_ma=["Butter"]))[0], False)
	la("số lượng hỏng", dd.khoi_nap_duoc(dict(goc, sl_hong=["x"]))[0], False)


@ca("dọn dữ liệu: mọi cửa đều chạy thử mặc định, không cửa nào ghi khi gọi trống")
def _():
	import inspect

	for ten in ("nuoc_het_ton", "don_kho_do_dang", "doi_ten", "ma_thay_the",
			"nap_bom_thu_vien"):
		tham = inspect.signature(getattr(dd, ten)).parameters
		la("%s mặc định chạy thử" % ten, tham["chay_that"].default, 0)


@ca("dọn dữ liệu: xả tồn đi bằng PHIẾU ghi sổ, không sửa thẳng bảng tồn")
def _():
	import inspect

	nguon = inspect.getsource(dd._xa_ton)
	dung("lập Stock Entry", "Stock Entry" in nguon)
	dung("có ghi sổ", "submit()" in nguon)
	dung("không đụng bảng Bin", "set_value(\"Bin" not in nguon)


@ca("dọn kho dở dang: còn lệnh treo trỏ vào kho là dừng và chỉ đường")
def _():
	import inspect

	nguon = inspect.getsource(dd.don_kho_do_dang)
	dung("soi lệnh treo", "_lenh_treo_dung" in nguon)
	dung("chỉ sang màn Dọn chứng từ thử", "Dọn chứng từ thử" in nguon)
	dung("tồn âm thì dừng", "ÂM" in nguon)


@ca("trạng thái BOM: bốn trạng thái đọc đúng từ ba cờ")
def _():
	la("nháp", ct.trang_thai_bom(0, 0, 0), "nhap")
	la("đang dùng", ct.trang_thai_bom(1, 1, 1), "dang_dung")
	la("bản cũ vì mất mặc định", ct.trang_thai_bom(1, 1, 0), "ban_cu")
	la("bản cũ vì tắt hoạt động", ct.trang_thai_bom(1, 0, 1), "ban_cu")
	la("đã huỷ", ct.trang_thai_bom(2, 1, 1), "da_huy")


@ca("phân tab: nhánh Nước thắng hết, rồi tới Bếp phụ trách, rồi mới đoán tên")
def _():
	la("nhóm nước là bar dù tên nghe như baker",
		ct.phan_tab(True, "Bếp Baker", "Croissant đá xay"), "bar")
	la("bếp phụ trách đã khai thì nghe theo",
		ct.phan_tab(False, "Bếp Pastry", "Bánh Croissant"), "pastry")
	la("croissant tart là baker, vỏ cuộn xét trước",
		ct.phan_tab(False, "", "Bánh Howick Croissant Tart"), "baker")
	la("cheesecake là pastry", ct.phan_tab(False, "", "Slice BOHOL Cheesecake"), "pastry")
	la("không đoán được thì khac", ct.phan_tab(False, "", "BÁNH MEAD"), "khac")


@ca("tìm kiếm: khớp cả mã lẫn tên, không phân biệt hoa thường, trống là qua hết")
def _():
	la("trống", ct.khop_tim("", "BANU00015", "Bánh Plain Croissant"), True)
	la("theo mã thường", ct.khop_tim("banu000", "BANU00015", "x"), True)
	la("theo tên", ct.khop_tim("croissant", "x", "Bánh Plain Croissant"), True)
	la("không khớp", ct.khop_tim("mead", "BANU00015", "Bánh Plain Croissant"), False)


@ca("phiên bản BOM: điều chỉnh tạo NHÁP trỏ về bản cũ, KHÔNG cancel bản cũ")
def _():
	import inspect

	nguon = inspect.getsource(ct.dieu_chinh)
	dung("sao chép ra nháp", "copy_doc" in nguon)
	dung("trỏ về bản cũ", "custom_ban_truoc" in nguon)
	dung("không cancel", ".cancel(" not in nguon)
	nguon2 = inspect.getsource(ct.ghi_so)
	dung("bản cũ lui về bản lưu",
		'"is_default": 0, "is_active": 0' in nguon2)
	dung("bản mới thành mặc định",
		'"is_default": 1, "is_active": 1' in nguon2)
	dung("ghi sổ cũng không cancel", ".cancel(" not in nguon2)


@ca("phiên bản BOM: chỉ nháp mới bỏ được, bản đã ghi sổ thì không")
def _():
	import inspect

	nguon = inspect.getsource(ct.bo_nhap)
	dung("kiểm docstatus trước khi bỏ", "docstatus" in nguon)
	dung("bản ghi sổ thì từ chối với lời chỉ đường", "Điều" in nguon)
