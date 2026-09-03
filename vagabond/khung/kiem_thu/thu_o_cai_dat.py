# -*- coding: utf-8 -*-
"""Ca kiểm: ô Cài đặt nào mã nguồn dùng thì ô đó phải được dựng bằng mã nguồn.

Anh Việt 03/09/2026, kèm ảnh chuyển khoản thử cho Trần Cao Vân vẫn ra tài
khoản chung: *"nó vẫn không ra tài khoản của chi nhánh này"*.

Ô chứa cấu hình tài khoản nhận tiền chưa bao giờ tồn tại trên hệ thống. Phép
ghi vẫn chạy trót lọt vì nó ghi thẳng xuống bảng Singles, không soi danh sách
trường; phép đọc thì đi qua danh sách trường nên luôn trả về rỗng. Khai xong
bấm lưu thấy báo thành công, quay lại thấy trắng, và cả ba điểm bán lặng lẽ
nhận tiền về một tài khoản. Đúng hai lần: 16/08 và 01/09.

Hai việc soi được bằng chuỗi thì soi ở đây:

1. Mọi ô Cài đặt mã nguồn đọc hoặc ghi đều phải có trong `vagabond_settings.json`
   hoặc trong một khai `TRUONG_MOI` của repo. Ô cũ dựng tay trên Desk từ trước
   thì nằm trong bảng mốc dưới đây, và bảng đó CHỈ ĐƯỢC NGẮN ĐI.
2. Màn tài khoản phải đọc thẳng bảng Singles và phải đọc lại sau khi ghi.

Toàn phép soi chuỗi, không cần Frappe.
"""

import io
import json
import os
import re

from vagabond import hddt_bu
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	return os.path.dirname(os.path.dirname(os.path.abspath(hddt_bu.__file__)))


def _doc(duong):
	return io.open(os.path.join(_goc(), duong), encoding="utf-8").read()


# O CU dung tay tren Desk ma ma nguon chua khai lai. Ngay 03/09/2026 bay o
# cuoi cung da duoc dua vao o_cai_dat.py nen bang nay rong. Bang CHI DUOC
# GIU RONG: them mot dong vao day nghia la vua dung mot o ma khong ai dung
# no bang ma nguon, va do la dung cai da lam mat cau hinh tai khoan hai lan.
MOC_O_CU = set()

# Ten goi cua chinh doi tuong Document, khong phai o cai dat.
KHONG_PHAI_O = {
	"get", "set", "name", "save", "db_set", "as_dict", "reload", "append",
	"get_password", "run_method", "flags", "meta", "doctype", "get_value",
	"insert", "delete", "load_from_db", "get_doc_before_save",
}

_LOI = [
	re.compile(r"""cfg_o\(\s*["']([a-z0-9_]+)["']"""),
	re.compile(r"""cfg\(\)\.get\(\s*["']([a-z0-9_]+)["']"""),
	re.compile(r"""cfg\(\)\.([a-z][a-z0-9_]*)"""),
	re.compile(
		r"""set_single_value\(\s*\n?\s*["']Vagabond Settings["']\s*,\s*\n?\s*["']([a-z0-9_]+)["']"""
	),
	re.compile(
		r"""get_single_value\(\s*\n?\s*["']Vagabond Settings["']\s*,\s*\n?\s*["']([a-z0-9_]+)["']"""
	),
]

# Tep nao goi o Cai dat bang HANG "TRUONG" thi lay gia tri cua hang do.
_QUA_HANG = re.compile(
	r"""(?:get|set)_single_value\(\s*\n?\s*["']Vagabond Settings["']\s*,\s*\n?\s*(TRUONG[A-Z_]*)\b"""
	r"""|cfg_o\(\s*(TRUONG[A-Z_]*)\b"""
)


def _gia_tri_hang(s, ten):
	m = re.search(r"""^%s\s*=\s*["']([a-z0-9_]+)["']""" % ten, s, re.M)
	return m.group(1) if m else ""

# Khai truong tu them: bat fieldname nam trong khoi "Vagabond Settings": [ ... ]
_KHOI_SETTINGS = re.compile(
	r"""["']Vagabond Settings["']\s*:\s*\[(.*?)\n\t\]""", re.S
)
_FIELDNAME = re.compile(r"""["']fieldname["']\s*:\s*(?:TRUONG|["']([a-z0-9_]+)["'])""")


def _tep_py():
	ra = []
	for goc, _, ts in os.walk(os.path.join(_goc(), "vagabond")):
		if "__pycache__" in goc or "kiem_thu" in goc:
			continue
		for t in ts:
			if t.endswith(".py"):
				ra.append(os.path.join(goc, t))
	return sorted(ra)


def o_ma_nguon_dung():
	"""Moi o Cai dat ma nguon doc hoac ghi, kem tep noi no xuat hien."""
	ra = {}
	for p in _tep_py():
		s = io.open(p, encoding="utf-8").read()
		for r in _LOI:
			for m in r.finditer(s):
				ten = m.group(1)
				if not ten or ten in KHONG_PHAI_O:
					continue
				ra.setdefault(ten, set()).add(os.path.basename(p))
		for m in _QUA_HANG.finditer(s):
			ten_hang = m.group(1) or m.group(2)
			gt = _gia_tri_hang(s, ten_hang)
			if gt:
				ra.setdefault(gt, set()).add(os.path.basename(p))
	return ra


def o_da_khai():
	"""Moi o da duoc dung bang ma nguon: doctype json va cac khai TRUONG_MOI."""
	d = json.loads(
		_doc("vagabond/vagabond/doctype/vagabond_settings/vagabond_settings.json")
	)
	ra = set(f.get("fieldname") for f in d.get("fields") or [])
	for p in _tep_py():
		s = io.open(p, encoding="utf-8").read()
		if '"Vagabond Settings"' not in s or "TRUONG_MOI" not in s:
			continue
		for khoi in _KHOI_SETTINGS.findall(s):
			for m in _FIELDNAME.finditer(khoi):
				if m.group(1):
					ra.add(m.group(1))
				else:
					# "fieldname": TRUONG -> lay hang TRUONG cua chinh tep do
					h = re.search(r"""^TRUONG\s*=\s*["']([a-z0-9_]+)["']""", s, re.M)
					if h:
						ra.add(h.group(1))
	return ra


@ca("ô cài đặt: đọc được cả hai nguồn khai, không rỗng")
def _doc_duoc():
	khai = o_da_khai()
	dung("doctype có nhiều ô", len(khai) > 50)
	dung("bắt được ô khai bằng hằng TRUONG", "vgb_tai_khoan_nhan" in khai)
	dung(
		"bắt được ô khai bằng chuỗi thẳng",
		"vgb_nhan_tt" in khai or len(khai) > 100,
	)
	dungx = o_ma_nguon_dung()
	dung("mã nguồn có dùng ô cài đặt", len(dungx) > 5)
	dung("bắt được ô tài khoản", "vgb_tai_khoan_nhan" in dungx)


@ca("ô cài đặt: mọi ô mã nguồn dùng đều được dựng bằng mã nguồn")
def _du_khai():
	khai = o_da_khai()
	for ten, teps in sorted(o_ma_nguon_dung().items()):
		if ten in MOC_O_CU:
			continue
		dung(
			"%s (dùng ở %s) phải được khai trong repo"
			% (ten, ", ".join(sorted(teps))),
			ten in khai,
		)


@ca("ô cài đặt: bảng mốc ô cũ chỉ được ngắn đi")
def _moc_ngan():
	la("không còn ô nào nợ mã nguồn", len(MOC_O_CU), 0)
	khai = o_da_khai()
	for ten in sorted(MOC_O_CU):
		dung(
			"%s đã khai trong repo rồi thì bỏ khỏi bảng mốc" % ten,
			ten not in khai,
		)


@ca("ô cài đặt: màn tài khoản đọc thẳng bảng Singles và đọc lại sau khi ghi")
def _tai_khoan_chac():
	s = _doc("vagabond/tai_khoan.py")
	dung("có đường đọc thẳng", "def _doc_o(" in s)
	dung("đọc thẳng qua đường dùng chung", "return cfg_o(TRUONG)" in s)
	dung("phép đọc cấu hình đi qua đường đó", "_doc_o() or" in s)
	than = s[s.index("def cai():"):s.index("def tk_cho(")]
	dung("phép đọc cấu hình không đi qua danh sách trường", "cfg()" not in than)
	dung("ghi xong đọc lại", "if (_doc_o() or \"\").strip() != chuoi.strip():" in s)
	dung("ô chứa được khai bằng mã nguồn", "TRUONG_MOI = {" in s)
	t = _doc("vagabond/truong_tu_them.py")
	dung("khai được đăng ký để dựng lại mỗi lần deploy", "tai_khoan.TRUONG_MOI" in t)
