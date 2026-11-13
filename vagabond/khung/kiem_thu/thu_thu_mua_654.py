# -*- coding: utf-8 -*-
"""v654 gọi đúng tên bộ phận "Thu mua" thay cho tên người (anh Việt 13/11/2026).

Ảnh màn Dự chi công nợ 13/11 ghi "Uyên đang thương lượng". Tên người làm vai
nghiệp vụ trên màn, nhãn trạng thái, tin nhắn, sổ tay thì đổi người là sai.
Ca chốt: không còn "Uyên" trong chữ người dùng thấy (chuỗi trong mã Python trừ
docstring, chuỗi trong mã màn app trừ chú thích, sổ tay, nhãn và mô tả doctype).
Lịch sử trong chú thích mã và người thật trong nhật ký, chứng từ giữ nguyên.
"""

import glob
import io
import json
import os
import re
import tokenize

from vagabond.khung.kiem_thu.nen import ca, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEN = "Uyên"


def _chuoi_py(p):
	ra = []
	toks = list(tokenize.generate_tokens(io.StringIO(open(p, encoding="utf-8").read()).readline))
	for i, t in enumerate(toks):
		if t.type != tokenize.STRING or TEN not in t.string:
			continue
		truoc = toks[i - 1] if i else None
		if t.string.startswith(('"""', "'''")) and (truoc is None or truoc.type in (
				tokenize.INDENT, tokenize.NEWLINE, tokenize.NL, tokenize.DEDENT, tokenize.ENCODING, tokenize.COMMENT)):
			continue  # docstring: lịch sử, không hiện cho người dùng
		ra.append("%s:%d" % (os.path.relpath(p, GOC), t.start[0]))
	return ra


def _bo_chu_thich_js(s):
	s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
	return "\n".join(re.sub(r"(^|[^:'\"\\])//.*$", r"\1", d) for d in s.split("\n"))


@ca("v654 không còn tên người \"Uyên\" ở chữ người dùng thấy: mã Python, màn app, sổ tay, doctype")
def _khong_ten_nguoi():
	py = []
	for p in glob.glob(os.path.join(GOC, "**", "*.py"), recursive=True):
		if os.sep + "khung" + os.sep in p:
			continue
		py += _chuoi_py(p)
	la("chuỗi Python", py, [])
	js = []
	for p in sorted(glob.glob(os.path.join(GOC, "public", "js", "bep", "*.js"))):
		for i, d in enumerate(_bo_chu_thich_js(open(p, encoding="utf-8").read()).split("\n"), 1):
			if TEN in d:
				js.append("%s:%d" % (os.path.basename(p), i))
	la("màn app", js, [])
	st = [os.path.basename(p) for p in glob.glob(os.path.join(GOC, "so_tay", "*.md")) if TEN in open(p, encoding="utf-8").read()]
	la("sổ tay", st, [])
	dt = []
	for p in glob.glob(os.path.join(GOC, "vagabond", "doctype", "*", "*.json")):
		d = json.load(open(p, encoding="utf-8"))
		for f in d.get("fields") or []:
			if TEN in (f.get("label") or "") + (f.get("description") or "") + str(f.get("options") or ""):
				dt.append("%s.%s" % (d.get("name"), f.get("fieldname")))
	la("nhãn, mô tả doctype", dt, [])


@ca("v654 nhãn bước đợt dự chi: Thu mua đang thương lượng (đợt cũ đọc nhãn theo mã nên đổi theo)")
def _nhan():
	from vagabond.khung.kiem_thu.nen import gia_lap

	gia_lap()
	from vagabond import du_chi as dc

	la("nhãn nháp", dc.NHAN[dc.TT_NHAP], "Thu mua đang thương lượng")
	la("trạng thái lưu là mã, không phải tên người", dc.TT_NHAP, "Nhap")
