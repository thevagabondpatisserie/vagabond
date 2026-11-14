# -*- coding: utf-8 -*-
"""v657: giữ quy tắc chữ ERP (docs/quy-tac-chu-erp.md, anh Việt duyệt 14/11/2026).

Anh Việt 14/11, ảnh nút "📤 Gửi Khải" trên màn Đề xuất công thức: "Lại dùng
tên riêng, ở đây phải là gửi Kế toán chứ". Chữ "Lại" là vì app còn khoảng 150
câu gọi tên người ("báo anh Việt", "nhờ chị Dung", "Chờ Khải") và sổ tay còn
khoảng 90 dòng. Người nghỉ, người đổi việc thì chữ trên app sai ngay.

Ca kiểm quét chữ NGƯỜI DÙNG THẤY, không quét chú thích hay docstring:
- Python: chuỗi trong mã, trừ docstring.
- JS, HTML: chuỗi trong mã, trừ chú thích // và /* */.
- Doctype JSON: label, description, options.
- Sổ tay: mọi dòng trừ dòng "Từ khoá" (giữ cách gọi cũ để người hỏi tìm ra).

Mốc "BOM", "NCC" trong chuỗi màn app chỉ được giảm (quy tắc điểm 7).
"""

import glob
import io
import json
import os
import re
import tokenize

from vagabond import hddt_bu
from vagabond.khung.kiem_thu.nen import ca, dung, la

TEN_CAM = re.compile(
	r"\bKhải\b|\banh Việt\b|\b[Cc]hị Dung\b|\bUyên\b|\bHân\b|\bLinh\b(?! hoạt)"
	r"|\bLoan Anh\b|\b[Cc]hị Dễ\b")

# Công cụ chạy một lần đã xong: chuỗi nằm trong mã xác nhận hay nhật ký đã
# ghi, đổi chữ là làm lệch hash hoặc sai lịch sử. Giữ nguyên, có lý do.
MIEN_TEP = {
	"vagabond/doi_chieu_tang_cu.py": "công cụ #225, chuỗi nằm trong mã xác nhận sha256",
	"vagabond/public/js/sua_pkt_tang.js": "màn của công cụ #225 đã chạy xong",
	"vagabond/gram_bom_252.py": "công cụ #252 đã chạy, câu căn cứ đã ghi vào bình luận",
}
MIEN_THU_MUC = ("vagabond/patches/", "vagabond/khung/", "vagabond/du_lieu/")
# Một chuỗi được giữ: tên trạng thái cũ để bản vá đổi tên tìm phiếu cũ.
MIEN_CHUOI = {("vagabond/de_xuat_cong_thuc.py", '"Chờ Khải"')}

# Số chỗ "BOM", "NCC" trong chuỗi màn app /bep, đếm 14/11/2026. Chỉ được giảm.
MOC_VIET_TAT = {"BOM": 5, "NCC": 44}


def _goc():
	return os.path.dirname(os.path.dirname(os.path.abspath(hddt_bu.__file__)))


def _doc(rel):
	return io.open(os.path.join(_goc(), rel), encoding="utf-8").read()


def chuoi_py(s):
	"""THUẦN: [(dòng, chuỗi)] của mã Python, bỏ docstring và chú thích."""
	ra = []
	truoc = None
	for t in tokenize.generate_tokens(io.StringIO(s).readline):
		if t.type == tokenize.STRING:
			la_doc = (truoc is None or truoc.type in (
				tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE)) and t.string.lstrip("rbuRBUfF")[:3] in ('"""', "'''")
			if not la_doc:
				ra.append((t.start[0], t.string))
		elif t.type == getattr(tokenize, "FSTRING_MIDDLE", -1):
			ra.append((t.start[0], t.string))  # Python 3.12+ tách f-string
		if t.type not in (tokenize.COMMENT, tokenize.NL):
			truoc = t
	return ra


_JS = re.compile(
	r"/\*.*?\*/|//[^\n]*"
	r"|'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`", re.S)


def chuoi_js(s):
	"""THUẦN: [(dòng, chuỗi)] của mã JS hay HTML, bỏ chú thích."""
	ra = []
	for m in _JS.finditer(s):
		x = m.group(0)
		if x.startswith("/*") or x.startswith("//"):
			continue
		ra.append((s.count("\n", 0, m.start()) + 1, x))
	return ra


def chuoi_json(s):
	"""THUẦN: chữ hiển thị của một doctype JSON (label, description, options)."""
	ra = []
	try:
		d = json.loads(s)
	except ValueError:
		return ra
	def di(x):
		if isinstance(x, dict):
			for k, v in x.items():
				if k in ("label", "description", "options", "title") and isinstance(v, str):
					ra.append((0, v))
				else:
					di(v)
		elif isinstance(x, list):
			for v in x:
				di(v)
	di(d)
	return ra


def chuoi_so_tay(s):
	return [(i, l) for i, l in enumerate(s.split("\n"), 1) if not l.startswith("Từ khoá")]


def chuoi_hien_thi(rel, s):
	if rel.endswith(".py"):
		return chuoi_py(s)
	if rel.endswith((".js", ".html", ".vue")):
		return chuoi_js(s)
	if rel.endswith(".json") and "/doctype/" in rel:
		return chuoi_json(s)
	if rel.endswith(".md") and "/so_tay/" in rel:
		return chuoi_so_tay(s)
	return []


def tim_ten(rel, s):
	"""THUẦN: [(dòng, chuỗi)] có tên người trong chữ hiển thị của một tệp."""
	# Chú thích CSS nằm trong chuỗi CSS (/* ... */) không hiện ra màn.
	return [(d, c) for d, c in chuoi_hien_thi(rel, s)
		if TEN_CAM.search(re.sub(r"/\*.*?\*/", "", c, flags=re.S)) and (rel, c.strip()) not in MIEN_CHUOI]


def _cac_tep():
	goc = _goc()
	for p in glob.glob(os.path.join(goc, "vagabond", "**", "*"), recursive=True):
		rel = os.path.relpath(p, goc).replace(os.sep, "/")
		if not os.path.isfile(p) or rel.endswith("app_bep.js") or rel in MIEN_TEP:
			continue
		if rel.startswith(MIEN_THU_MUC) or "/node_modules/" in rel:
			continue
		if rel.endswith((".py", ".js", ".html", ".vue", ".json", ".md")):
			yield rel


@ca("v657 quy tắc chữ: bộ quét bắt tên người trong chuỗi, bỏ qua chú thích và docstring")
def _bo_quet():
	js = ("// báo anh Việt trong chú thích\nvar a = 'Gửi Khải';\n/* chị Dung */\n"
		"var b = \"Nhờ chị Dung\"; var c = `Chờ ${x} Uyên`; var d = 'Linh hoạt';\n")
	la("JS: bắt chuỗi, bỏ chú thích", [d for d, _ in tim_ten("vagabond/public/js/bep/x.js", js)], [2, 4, 4])
	py = ('def f():\n\t"""Khải chốt 28/08."""\n\t# anh Việt\n\tthrow("Báo anh Việt")\n'
		'\treturn f"Chờ {x} Hân"\n')
	la("Python: bắt chuỗi, bỏ docstring và chú thích", [d for d, _ in tim_ten("vagabond/x.py", py)], [4, 5])
	md = "## Gửi Kế toán\nTừ khoá: gửi Khải\n- Bấm [[Gửi Khải]].\n"
	la("Sổ tay: bỏ dòng Từ khoá", [d for d, _ in tim_ten("vagabond/so_tay/x.md", md)], [3])
	dj = json.dumps({"fields": [{"label": "Khải hỏi lại", "fieldname": "ghi_chu_khai"}]})
	la("Doctype: bắt label", len(tim_ten("vagabond/vagabond/doctype/x/x.json", dj)), 1)
	la("Doanh Việt không phải tên người", tim_ten("vagabond/x.py", 'a = "Liên Doanh Việt Nga"\n'), [])
	la("chú thích CSS trong chuỗi không hiện ra màn",
		tim_ten("vagabond/public/js/bep/x.js", "var e = `.a{color:red} /* anh Việt 03/11 */`;\n"), [])


@ca("v657 quy tắc chữ: không chữ hiển thị nào trên app và sổ tay gọi tên người")
def _khong_ten_nguoi():
	sai = []
	for rel in _cac_tep():
		for d, c in tim_ten(rel, _doc(rel)):
			sai.append("%s:%s %s" % (rel, d, c.strip()[:90]))
	la("chỗ còn gọi tên người", sai, [])


def dem_viet_tat():
	dem = dict((k, 0) for k in MOC_VIET_TAT)
	for p in sorted(glob.glob(os.path.join(_goc(), "vagabond", "public", "js", "bep", "*.js"))):
		for _, c in chuoi_js(io.open(p, encoding="utf-8").read()):
			for k in dem:
				dem[k] += len(re.findall(r"\b%s\b" % k, c))
	return dem


@ca("v657 quy tắc chữ: số chỗ BOM, NCC trên màn app chỉ được giảm")
def _viet_tat():
	dem = dem_viet_tat()
	for k, moc in MOC_VIET_TAT.items():
		dung("%s: %d chỗ, mốc %d (chỉ được giảm, giảm thì hạ mốc)" % (k, dem[k], moc), dem[k] <= moc)


@ca("v657 phiếu đề xuất công thức: Gửi Kế toán, Chờ Kế toán, bản vá đổi phiếu cũ")
def _de_xuat():
	py = _doc("vagabond/de_xuat_cong_thuc.py")
	la("trạng thái chờ", re.search(r'^TT_CHO = "([^"]*)"', py, re.M).group(1), "Chờ Kế toán")
	js = _doc("vagabond/public/js/bep/72-de-xuat-cong-thuc.js")
	dung("nút Gửi Kế toán", "📤 Gửi Kế toán</button>" in js)
	dt = json.loads(_doc("vagabond/vagabond/doctype/vagabond_de_xuat_cong_thuc/vagabond_de_xuat_cong_thuc.json"))
	tt = [f for f in dt["fields"] if f["fieldname"] == "trang_thai"][0]["options"].split("\n")
	dung("doctype có Chờ Kế toán, hết Chờ Khải", "Chờ Kế toán" in tt and "Chờ Khải" not in tt)
	dung("bản vá v657 có trong patches.txt",
		"vagabond.patches.v657_doi_ten_cho_ke_toan" in _doc("vagabond/patches.txt").split())
	vg = _doc("vagabond/patches/v657_doi_ten_cho_ke_toan.py")
	dung("bản vá chỉ đổi phiếu đang ở tên cũ", "where trang_thai=%s" in vg and "TT_CHO_CU" in vg)


@ca("v657 quy tắc chữ: tệp quy tắc có trong repo và AGENTS.md trỏ tới")
def _tai_lieu():
	q = _doc("docs/quy-tac-chu-erp.md")
	dung("có bảng thuật ngữ", "Từ điển thuật ngữ" in q and "Hệ thống tài khoản" in q)
	dung("AGENTS.md trỏ tới", "docs/quy-tac-chu-erp.md" in _doc("AGENTS.md"))
	dung("quy ước sổ tay cấm tên người", "Không gọi tên người" in _doc("vagabond/so_tay/_quy-uoc.md"))
