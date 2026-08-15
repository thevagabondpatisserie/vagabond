"""Kiem thu cac chan khai bao trong khung/hop_dong.py.

Muc dich cua nhung ca nay: mot cai typo trong khai bao man PHAI vo ngay
luc nap mo dun, tuc luc deploy, chu khong doi toi 11 gio dem ngoai quay
moi lo ra.
"""

from vagabond.khung import hop_dong as khai
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem


@ca("kiểu cột lạ bị chặn ngay lúc khai báo")
def _():
	nem("gõ nhầm 'tienn'", lambda: khai.cot(("a", "A", "tienn")), khai.LoiKhaiBao)
	nem("để trống kiểu", lambda: khai.cot(("a", "A", "")), khai.LoiKhaiBao)


@ca("cột trùng khoá bị chặn, vì cột sau sẽ lặng lẽ đè cột trước")
def _():
	nem("hai cột cùng khoá",
		lambda: khai.cot(("a", "A", "tien"), ("a", "B", "so")), khai.LoiKhaiBao)


@ca("màn không có cột nào thì không phải là màn danh sách")
def _():
	nem("không cột", lambda: khai.cot(), khai.LoiKhaiBao)


@ca("cột khai đúng thì giữ nguyên thứ tự và cờ không cộng")
def _():
	c = khai.cot(("a", "A", "chu"), ("b", "B", "tien"), ("c", "C", "tien", True))
	la("giữ thứ tự", [x["k"] for x in c], ["a", "b", "c"])
	dung("cột thứ ba mang cờ không cộng", c[2].get("kc"))
	dung("cột thứ hai không mang cờ", not c[1].get("kc"))


@ca("kiểu bộ lọc lạ bị chặn")
def _():
	nem("kiểu bịa",
		lambda: khai.loc({"k": "x", "nhan": "X", "kieu": "bia_ra"}), khai.LoiKhaiBao)


@ca("bộ lọc tìm chữ mà quên khai trường tìm thì bị chặn")
def _():
	nem("thiếu trường tìm",
		lambda: khai.loc({"k": "q", "nhan": "Tìm", "kieu": "tim_chu"}),
		khai.LoiKhaiBao)


@ca("bộ lọc chọn một mà quên khai trường thì bị chặn")
def _():
	nem("thiếu trường",
		lambda: khai.loc({"k": "ncc", "nhan": "NCC", "kieu": "chon_mot"}),
		khai.LoiKhaiBao)
	# Danh dau tay=1 nghia la mo dun tu xu ly, luc do khong can truong.
	c = khai.loc({"k": "ncc", "nhan": "NCC", "kieu": "chon_mot", "tay": 1})
	la("đánh dấu tự xử lý thì cho qua", len(c), 1)


@ca("chip đầu tiên bắt buộc là Tất cả")
def _():
	nem("chip đầu không phải Tất cả",
		lambda: khai.chip({"k": "cho", "ten": "Chờ"}), khai.LoiKhaiBao)
	nem("chip thiếu tên",
		lambda: khai.chip({"k": "", "ten": "Tất cả"}, {"k": "cho"}), khai.LoiKhaiBao)


@ca("màn không khai quyền thì bị chặn, không có màn nào mở cho tất cả")
def _():
	nem("quyền rỗng", lambda: khai.bang(
		ma="X", ten="X", doctype="Purchase Order", quyen=set(), loi_quyen="",
		cot=khai.cot(("a", "A", "chu")), truong=["a"]), khai.LoiKhaiBao)


@ca("khai chip mà quên hàm xếp, hoặc ngược lại, đều bị chặn")
def _():
	nen = dict(ma="X", ten="X", doctype="Purchase Order", quyen={"System Manager"},
		loi_quyen="không được", cot=khai.cot(("a", "A", "chu")), truong=["a"])
	nem("có chip không có hàm xếp", lambda: khai.bang(
		chip=khai.chip({"k": "", "ten": "Tất cả"}), **nen), khai.LoiKhaiBao)
	nem("có hàm xếp không có chip", lambda: khai.bang(
		xep=lambda r, bc: "", **nen), khai.LoiKhaiBao)


@ca("khai báo đủ và đúng thì dựng được bảng, giữ nguyên mặc định an toàn")
def _():
	b = khai.bang(
		ma="X", ten="Màn thử", doctype="Purchase Order",
		quyen={"System Manager"}, loi_quyen="không được",
		cot=khai.cot(("a", "A", "chu")), truong=["a"])
	la("trần mặc định đúng bằng hằng số của khung", b["tran"], khai.GIOI_HAN_DONG)
	la("mặc định thẻ KHÔNG chạy theo chip", b["tom_tat_theo_chip"], 0)
	la("không khai lọc thì rỗng chứ không phải None", b["loc"], [])
	la("mã giữ nguyên", b["ma"], "X")
