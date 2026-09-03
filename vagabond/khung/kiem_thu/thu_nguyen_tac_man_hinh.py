# -*- coding: utf-8 -*-
"""Ca kiểm giữ bộ nguyên tắc thiết kế màn hình (AGENTS.md mục 2b, v396).

Anh Việt 03/09/2026, kèm ảnh hai màn xuất kho:

    *"Giao diện phần xuất kho đang không đồng bộ với giao diện đẹp của app
    thì cả, lại bị rất thô sơ... các nút chọn thì luôn phải có nút tìm kiếm
    đi kèm chứ không phải chỉ xổ danh sách ra mà kéo... Chỗ nào hiển thị
    tên món thì phải có luôn hình món... vì anh đã rất nhiều lần yêu cầu
    rồi."*

"Đã rất nhiều lần yêu cầu rồi" nghĩa là nguyên tắc chỉ nằm trong lời dặn thì
ba tuần sau lại bị bỏ. Nên nguyên tắc phải có ca kiểm. Ba việc soi được bằng
chuỗi thì soi ở đây:

1. Ô `<select>` xổ danh sách trong từng tệp màn CHỈ ĐƯỢC GIẢM so với mốc.
   Tệp mới, hay tệp đã dọn xong, không được có ô nào. Ai muốn dùng lại
   `<select>` là phải sửa mốc ở đây, và sửa mốc là một dòng diff ai cũng
   thấy khi duyệt.
2. Tệp màn đã dọn theo chuẩn phải gọi `anhMon(` khi vẽ dòng hàng, có hàng
   chip và ô tìm ở màn danh sách.
3. AGENTS.md phải còn mục 2b để mọi phiên đọc.

Toàn phép soi chuỗi, không cần Frappe.
"""

import glob
import io
import os
import re

from vagabond import hddt_bu
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	return os.path.dirname(os.path.dirname(os.path.abspath(hddt_bu.__file__)))


def _bep():
	return os.path.join(_goc(), "vagabond", "public", "js", "bep")


def _js(ten):
	return io.open(os.path.join(_bep(), ten), encoding="utf-8").read()


def dem_select(s):
	"""Số ô <select> THẬT trong một tệp màn: chỉ đếm thẻ nằm trong chuỗi
	HTML (có dấu nháy ngay trước), không đếm chữ <select> trong chú thích."""
	return len(re.findall(r"""['"]<select""", s or ""))


# MOC: so o <select> con lai trong tung tep tinh den 03/09/2026 (v396). Chi
# duoc giam. Tep khong co trong bang nay phai bang 0.
MOC_SELECT = {
	"03-kho-chung-tu.js": 3,
	"04-tao-phieu.js": 1,
	"05-san-xuat.js": 2,
	"08-doanh-so-sales.js": 1,
	"10-bill-quay.js": 2,
	"15-khuon-danh-sach.js": 1,
	"16-mua-hang.js": 2,
	"17-cai-dat.js": 5,
	"33-don-tiec.js": 1,
	"39-bien-nhan-tien.js": 3,
	"42-thanh-toan-nhieu.js": 1,
}

# Tep da don theo chuan: phai co anh mon o dong hang, hang chip va o tim.
TEP_DA_CHUAN = ["45-xuat-kho-them.js"]


@ca("nguyên tắc màn hình: đếm ô xổ danh sách bỏ qua chữ trong chú thích")
def _dem():
	la("hai thẻ thật", dem_select("a '<select class=\"x\">' b \"<select id='y'>\""), 2)
	la("chú thích không tính", dem_select("/* dung <select> nua */ `<select>`"), 0)
	la("rỗng", dem_select(""), 0)


@ca("nguyên tắc màn hình: số ô xổ danh sách trong từng tệp chỉ được giảm")
def _moc():
	for f in sorted(glob.glob(os.path.join(_bep(), "*.js"))):
		ten = os.path.basename(f)
		n = dem_select(io.open(f, encoding="utf-8").read())
		moc = MOC_SELECT.get(ten, 0)
		dung("%s: %d ô, mốc %d" % (ten, n, moc), n <= moc)


@ca("nguyên tắc màn hình: tệp đã dọn có ảnh món, hàng chip, ô tìm, không xổ danh sách")
def _da_chuan():
	for ten in TEP_DA_CHUAN:
		j = _js(ten)
		dung(ten + " không còn ô xổ danh sách", dem_select(j) == 0)
		dung(ten + " dòng hàng có ảnh món", "anhMon(" in j)
		dung(ten + " có hàng chip", "xktChipNhom(" in j or "posChipNut(" in j)
		dung(ten + " có ô tìm ở màn danh sách", "srchBox(" in j)
		dung(ten + " chọn là tìm: mở sheet có ô tìm", "sheet(" in j)
		dung(ten + " không vẽ ô chữ cái thay ảnh", "charAt(0).toUpperCase()" not in j)


@ca("nguyên tắc màn hình: AGENTS.md còn mục 2b với đủ ba ý cốt lõi")
def _agents():
	s = io.open(os.path.join(_goc(), "AGENTS.md"), encoding="utf-8").read()
	dung("có mục 2b", "## 2b. Nguyên tắc thiết kế màn hình app" in s)
	dung("chọn là tìm", "Chọn là tìm" in s)
	dung("ảnh món", "có tên món thì có ảnh món" in s)
	dung("ba hàng chip", "Ba hàng chip" in s)
	dung("nhắc tới ca kiểm này", "thu_nguyen_tac_man_hinh.py" in s)
