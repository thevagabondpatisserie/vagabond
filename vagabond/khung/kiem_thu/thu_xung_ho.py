"""Kiem thu XUNG HO trong thong bao gui nguoi dung (v293).

Vi sao co tep nay
-----------------
Anh Viet 24/08/2026: app Vagabond la he thong quan tri doanh nghiep, thong
bao loi khong duoc xung "em". Da ra soat va doi 267 cau (182 ben Python, 85
ben JS) sang "he thong", "vui long" hoac "bo phan ky thuat".

Doi mot lan thi de, giu cho no khong quay lai moi kho: moi man hinh moi deu
co nguoi go them mot cau toast, va "go giup em" la loi noi tu nhien cua
nguoi Viet. Ca kiem duoi day la hang rao: them cau moi co "em" thi cong
kiem truoc deploy do ngay, khong cho di tiep.

Ba vung duoc chua, va ly do:
  - vagabond/mau_chuan.py: chua don vi CSS "0.86em", khong phai xung ho.
  - LOI_NHAN_MAU / LOI_NHAN_HD_MAU trong bao_gia.py va nam cau tuong ung
    trong 11-khach-ca-hop-dong.js: day la cau SALES GUI KHACH, nguoi ban tu
    xung "ben em" voi khach la dung phep. Doi thanh "ben he thong da dinh
    kem bao gia" la cau vo nghia.
  - public/js/vendor/: thu vien ben ngoai.

Chu thich trong ma nguon cung duoc chua: chung chep NGUYEN VAN loi anh Viet
noi, sua vao do la lam sai loi trich dan, va khong ai nhin thay chung tren
man hinh.

Ca kiem chay bang doc tep tren dia, khong can Frappe, khong can site, khong
can thu vien mang - de con chay duoc tren may CI tay khong.
"""

import ast
import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JS = os.path.join(GOI, "public", "js")

# Chan "em" dung mot minh. Khong tinh "0.86em" (don vi CSS), "them", "kem",
# "emp" (ten lop CSS): do la chu khac chu khong phai dai tu.
DAI_TU = re.compile(r"(?<![A-Za-zÀ-ỹ0-9.])[Ee]m(?![A-Za-zÀ-ỹ])")

CHUA_TEP_PY = {"mau_chuan.py"}
CHUA_HANG = ("LOI_NHAN_MAU", "LOI_NHAN_HD_MAU")

CAU_SALES_GUI_KHACH = {
	"Anh chị xem giúp em phần Điều 2 rồi phản hồi trước thứ Sáu ạ.",
	"Anh chị ký đóng dấu rồi gửi lại bên em một bản scan giúp em ạ.",
	"Bên em đã đính kèm báo giá đã chốt làm Phụ lục 01 của Hợp đồng ạ.",
	"Sau khi nhận cọc đợt 1 bên em sẽ lên lịch sản xuất ngay ạ.",
	"Anh chị cần điều chỉnh chỗ nào thì báo em, bên em gửi lại bản mới ạ.",
}


def _vung_chua(cay):
	"""Khoang dong cua hai hang so cau mau gui khach."""
	ra = []
	for nut in cay.body:
		if isinstance(nut, ast.Assign):
			for d in nut.targets:
				if isinstance(d, ast.Name) and d.id in CHUA_HANG:
					ra.append((nut.lineno, getattr(nut, "end_lineno", nut.lineno)))
	return ra


def _soi_python():
	ra = []
	for goc, thu_muc, tep in os.walk(GOI):
		thu_muc[:] = [t for t in thu_muc if t not in ("kiem_thu", "__pycache__", "node_modules")]
		for t in sorted(tep):
			if not t.endswith(".py") or t in CHUA_TEP_PY:
				continue
			p = os.path.join(goc, t)
			try:
				cay = ast.parse(io.open(p, encoding="utf-8").read())
			except Exception:
				continue
			chua = _vung_chua(cay)
			# Chuoi dung mot minh lam mot cau lenh la loi ghi chu (docstring
			# hoac chu thich dai giua ham), khong ai nhin thay tren man hinh.
			ghi_chu = {
				id(n.value)
				for n in ast.walk(cay)
				if isinstance(n, ast.Expr)
				and isinstance(n.value, ast.Constant)
				and isinstance(n.value.value, str)
			}
			for nut in ast.walk(cay):
				if not (isinstance(nut, ast.Constant) and isinstance(nut.value, str)):
					continue
				if id(nut) in ghi_chu:
					continue
				if any(a <= nut.lineno <= b for a, b in chua):
					continue
				if DAI_TU.search(nut.value):
					ra.append("%s:%d %s" % (os.path.relpath(p, GOI), nut.lineno,
											nut.value.replace("\n", " ")[:70]))
	return ra


MO_REGEX = set("(,=:[!&|?{};+-*%~^<>") | {"\n"}


def _chuoi_js(src):
	"""Cac chuoi trong tep JS. Bo chu thich va bieu thuc chinh quy.

	Khong dung regex de tim chuoi: chu thich trong repo nay chep nguyen van
	loi anh Viet noi, ma trong do co rat nhieu dau nhay va chu "em".
	"""
	ra = []
	i, n, truoc = 0, len(src), ""
	while i < n:
		c = src[i]
		if c == "/" and i + 1 < n and src[i + 1] == "/":
			j = src.find("\n", i)
			i = n if j < 0 else j
			continue
		if c == "/" and i + 1 < n and src[i + 1] == "*":
			j = src.find("*/", i + 2)
			i = n if j < 0 else j + 2
			continue
		if c == "/" and (truoc == "" or truoc in MO_REGEX):
			j, trong_lop = i + 1, False
			while j < n:
				d = src[j]
				if d == "\\":
					j += 2
					continue
				if d == "[":
					trong_lop = True
				elif d == "]":
					trong_lop = False
				elif d == "\n" or (d == "/" and not trong_lop):
					break
				j += 1
			i, truoc = j + 1, "/"
			continue
		if c in "\"'`":
			j = i + 1
			while j < n:
				d = src[j]
				if d == "\\":
					j += 2
					continue
				if d == c or (d == "\n" and c != "`"):
					break
				j += 1
			if j < n and src[j] == c:
				ra.append((src[:i].count("\n") + 1, src[i + 1:j]))
				i, truoc = j + 1, c
				continue
			i += 1
			continue
		if not c.isspace():
			truoc = c
		i += 1
	return ra


def _soi_js():
	ra = []
	for goc, thu_muc, tep in os.walk(JS):
		thu_muc[:] = [t for t in thu_muc if t != "vendor"]
		for t in sorted(tep):
			if not t.endswith(".js") or t == "app_bep.js":
				continue
			p = os.path.join(goc, t)
			for dong, than in _chuoi_js(io.open(p, encoding="utf-8").read()):
				if than in CAU_SALES_GUI_KHACH:
					continue
				if DAI_TU.search(than):
					ra.append("%s:%d %s" % (os.path.relpath(p, GOI), dong, than[:70]))
	return ra


@ca("không thông báo Python nào còn xưng em")
def _():
	la("mọi chuỗi Python đã dùng giọng hệ thống", _soi_python(), [])


@ca("không thông báo JS nào còn xưng em")
def _():
	la("mọi chuỗi JS đã dùng giọng hệ thống", _soi_js(), [])


@ca("bộ soi thật sự đọc được mã nguồn chứ không quét trúng thư mục rỗng")
def _():
	# Mot ca kiem luon xanh vi khong tim thay tep nao thi te hon la khong co.
	so_py = sum(1 for g, _tm, ts in os.walk(GOI)
				if "kiem_thu" not in g and "__pycache__" not in g
				for t in ts if t.endswith(".py"))
	so_js = sum(1 for g, _tm, ts in os.walk(JS) if "vendor" not in g
				for t in ts if t.endswith(".js") and t != "app_bep.js")
	la("thấy đủ tệp nguồn hai bên", [so_py > 40, so_js > 20], [True, True])
