# -*- coding: utf-8 -*-
"""Sổ tay tri thức cho trợ lý trong app: MÁY SINH, không gõ tay.

Anh Việt giao 26/08/2026: dựng một trợ lý trong app để nhân viên hỏi cách
dùng bất kỳ màn hình nào.


VÌ SAO SỔ TAY PHẢI DO MÁY SINH
==============================

Một tệp hướng dẫn gõ tay thì đúng đúng một tuần. App này mỗi ngày lên một
bản, màn hình đổi, luật đổi, câu chặn đổi. Sổ tay gõ tay sẽ lệch với phần
mềm, và trợ lý dạy nhân viên làm theo cái không còn tồn tại - tệ hơn hẳn
việc không có trợ lý.

Nên sổ tay ở đây dựng lại từ CHÍNH MÃ NGUỒN mỗi lần gọi, lấy từ ba nguồn đã
có sẵn và đã được cổng kiểm canh:

1. Bảng `MAN` trong `duong_app.py`. Một nguồn duy nhất cho 90 màn hình, có
   cổng kiểm đối chiếu từng byte với bảng bên JavaScript. Cho ra TÊN màn và
   ĐỊA CHỈ mở màn đó.

2. Các thẻ trên trang chủ trong `02-trang-chu.js`. Mỗi thẻ đã sẵn một dòng
   mô tả viết cho người dùng đọc, ví dụ "Còn nợ nhà cung cấp nào, khoản nào
   quá hạn". Đây là câu chữ đã được duyệt qua mắt người thật.

3. Đoạn mô tả đầu mỗi tệp Python nghiệp vụ. Đây là nguồn quý nhất: mỗi tệp
   đều có một đoạn dài kể việc gì, vì sao làm vậy, ca hỏng thật nào sinh ra
   nó. Chính những đoạn đó trả lời được câu khó nhất mà nhân viên hay hỏi:
   "vì sao máy chặn tôi".

Sổ tay tự đúng theo mã nguồn. Không có bước "nhớ cập nhật tài liệu".


CHỖ CẦN CẨN THẬN
================

Đoạn mô tả đầu tệp chép NGUYÊN VĂN lời anh Việt, trong đó có xưng hô đời
thường. Trợ lý phải nói giọng "Hệ thống", nên phần gọi mô hình ngôn ngữ chỉ
dùng sổ tay làm TƯ LIỆU chứ không chép lại giọng văn. Luật đó nằm ở
`tro_ly.py`, không nằm ở đây.
"""

import re

# Bao nhiêu ký tự đầu của đoạn mô tả một tệp thì đủ. Cắt để một câu hỏi
# không kéo theo mười nghìn chữ.
DAI_DOAN = 1800

# Từ quá phổ biến, có mặt ở mọi câu nên không giúp phân biệt mục nào.
TU_BO = frozenset("""
la va cua o cho khi thi ma nhu de duoc co khong con nao day kia
mot hai ba bon nam sau bay tam chin muoi
lam sao the nay do gi ai dau bao nhieu vi cai
toi minh anh chi ban ho ta
tren duoi trong ngoai truoc sau
""".split())


def bo_dau(t):
	"""Bỏ dấu tiếng Việt và hạ thường. THUẦN."""
	import unicodedata

	t = unicodedata.normalize("NFD", str(t or ""))
	t = "".join(c for c in t if unicodedata.category(c) != "Mn")
	return t.replace("\u0111", "d").replace("\u0110", "d").lower()


def tu_khoa(t):
	"""Bộ từ khoá của một câu, đã bỏ dấu và bỏ từ quá phổ biến. THUẦN."""
	tu = re.findall(r"[a-z0-9]+", bo_dau(t))
	return {x for x in tu if len(x) > 1 and x not in TU_BO}


def doc_the_trang_chu(nguon_js):
	"""Rút các thẻ chức năng trên trang chủ. THUẦN.

	Mỗi thẻ khai `card(biểu tượng, tên, mô tả, số đếm, khoá màn)`. Trả về
	{khoá màn: mô tả}.

	Chỉ bắt các thẻ khai chuỗi thẳng. Vài thẻ lấy tên từ biến (`TYPES.X.title`)
	thì bỏ qua: đoán mò giá trị của biến trong một tệp JavaScript bằng biểu
	thức chính quy là cách chắc chắn sinh ra mô tả sai.
	"""
	mau = re.compile(
		r"card\(\s*'([^'\\]*)'\s*,\s*'([^'\\]*)'\s*,\s*'([^'\\]*)'\s*,"
		r"\s*[^,]+?,\s*'([^'\\]*)'",
		re.S,
	)
	ra = {}
	for _bt, _ten, mo_ta, khoa in mau.findall(str(nguon_js or "")):
		khoa = khoa.strip()
		mo_ta = re.sub(r"\s+", " ", mo_ta).strip()
		if khoa and mo_ta and khoa not in ra:
			ra[khoa] = mo_ta
	return ra


def doan_dau_tep(nguon_py, dai=DAI_DOAN):
	"""Đoạn mô tả đầu một tệp Python, đã gọn lại. THUẦN.

	Trả về chuỗi rỗng nếu tệp không mở đầu bằng đoạn mô tả.
	"""
	s = str(nguon_py or "").lstrip()
	if s.startswith("# -*-"):
		s = s.split("\n", 1)[-1].lstrip()
	for dau in ('"""', "'''"):
		if s.startswith(dau):
			het = s.find(dau, len(dau))
			if het < 0:
				return ""
			than = s[len(dau):het]
			than = re.sub(r"\n{3,}", "\n\n", than).strip()
			return than[:dai]
	return ""


def diem_khop(tu_hoi, muc):
	"""Mục này khớp câu hỏi tới đâu. THUẦN.

	Tên màn nặng hơn mô tả, mô tả nặng hơn phần chi tiết dài. Lý do: người
	ta hỏi "màn doanh số ở đâu" thì cái đáng trả về là màn tên Doanh số, chứ
	không phải một tệp nào đó có chữ "doanh số" nằm giữa nghìn chữ.
	"""
	if not tu_hoi:
		return 0
	d = 0
	d += 6 * len(tu_hoi & tu_khoa(muc.get("ten")))
	d += 3 * len(tu_hoi & tu_khoa(muc.get("mo_ta")))
	d += 1 * len(tu_hoi & tu_khoa(muc.get("chi_tiet")))
	return d


def chon_muc(cau_hoi, so_tay, so_muc=6):
	"""Vài mục sổ tay sát câu hỏi nhất. THUẦN.

	Trả về danh sách đã xếp theo điểm giảm dần. Không mục nào khớp thì trả
	về danh sách RỖNG, và nơi gọi phải hiểu đó là "chưa biết" chứ không
	được lấy bừa mấy mục đầu bảng.
	"""
	tu = tu_khoa(cau_hoi)
	if not tu:
		return []
	cham = []
	for m in so_tay or []:
		d = diem_khop(tu, m)
		if d > 0:
			cham.append((d, m))
	cham.sort(key=lambda x: (-x[0], str(x[1].get("ten") or "")))
	return [m for _d, m in cham[: max(1, int(so_muc or 6))]]


def gon_tu_lieu(cac_muc, tran=9000):
	"""Ghép các mục đã chọn thành tư liệu gửi kèm câu hỏi. THUẦN.

	Có trần ký tự: một câu hỏi kéo theo cả mã nguồn là vừa chậm vừa tốn
	tiền, mà mô hình cũng đọc kém đi khi tư liệu quá dài.
	"""
	phan, dai = [], 0
	for m in cac_muc or []:
		khoi = "## %s\n" % (m.get("ten") or "")
		if m.get("duong"):
			khoi += "Địa chỉ mở màn: %s\n" % m["duong"]
		if m.get("mo_ta"):
			khoi += "%s\n" % m["mo_ta"]
		if m.get("chi_tiet"):
			khoi += "%s\n" % m["chi_tiet"]
		if dai + len(khoi) > tran:
			break
		phan.append(khoi)
		dai += len(khoi)
	return "\n".join(phan).strip()


# ------------------------------------------------------- phan can Frappe

import os

import frappe

# Tệp nghiệp vụ KHÔNG đưa vào sổ tay: hạ tầng, tiện ích, hoặc chính trợ lý.
BO_TEP = frozenset("""
__init__.py hooks.py lib.py dich.py mau_chuan.py
tro_ly.py tro_ly_so_tay.py
""".split())

KHOA_NHO = "vgb_tro_ly_so_tay"


def _goc():
	return frappe.get_app_path("vagabond")


def _doc(duong):
	try:
		with open(duong, encoding="utf-8") as f:
			return f.read()
	except Exception:
		return ""


def dung_so_tay():
	"""Dựng lại sổ tay từ mã nguồn. Trả về danh sách mục."""
	from vagabond import duong_app

	goc = _goc()
	the = doc_the_trang_chu(
		_doc(os.path.join(goc, "public", "js", "bep", "02-trang-chu.js")))

	# Bang_duong() la {slug: khoa}, can chieu nguoc lai de biet mo mot man
	# thi go dia chi nao. Mot khoa chi co dung mot slug nen lat khong mat gi.
	dia_chi = {}
	for slug, khoa in duong_app.bang_duong().items():
		dia_chi.setdefault(khoa, "/" + slug)

	ra = []
	for hang in getattr(duong_app, "MAN", ()):
		ma, ten = hang[0], hang[1]
		ra.append({
			"loai": "man",
			"ten": ten,
			"duong": dia_chi.get(ma, ""),
			"mo_ta": the.get(ma, ""),
			"chi_tiet": "",
		})

	for ten_tep in sorted(os.listdir(goc)):
		if not ten_tep.endswith(".py") or ten_tep in BO_TEP:
			continue
		doan = doan_dau_tep(_doc(os.path.join(goc, ten_tep)))
		if not doan:
			continue
		dong_dau = doan.split("\n", 1)[0].strip().rstrip(".")
		ra.append({
			"loai": "nghiep_vu",
			"ten": dong_dau or ten_tep,
			"duong": "",
			"mo_ta": "",
			"chi_tiet": doan,
		})
	return ra


def so_tay(dung_lai=0):
	"""Sổ tay, có nhớ lại. Dựng lại mỗi lần deploy vì bộ nhớ đệm trống."""
	if not frappe.utils.cint(dung_lai):
		co = frappe.cache().get_value(KHOA_NHO)
		if co:
			return co
	ra = dung_so_tay()
	frappe.cache().set_value(KHOA_NHO, ra, expires_in_sec=3600)
	return ra
