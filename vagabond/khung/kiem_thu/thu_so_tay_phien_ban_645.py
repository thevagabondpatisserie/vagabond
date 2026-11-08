# -*- coding: utf-8 -*-
"""Anh Việt 08/11/2026: mỗi bản deploy phải kèm hướng dẫn trong sổ tay.

Trước đó sổ tay đứng ở v631 trong khi app đã lên v644: mười bốn bản liền
(OnePay, gọi món tại bàn, Biên tập menu, đối soát qua hộp thư...) nhân viên hỏi
trợ lý thì trợ lý không biết. Không phép kiểm nào nhắc, vì mọi cổng chỉ soi mã.

Ca này chốt bằng máy: APPVER trên nhánh phải có mục `## vNNN` trong
`vagabond/so_tay/_phien-ban.md`, mỗi dòng là tên một mục sổ tay CÓ THẬT (đúng
từng chữ dòng `## ` trong chương), hoặc đúng một dòng "Không đổi thao tác: <lý do>".
"""

import glob
import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
THU_MUC = os.path.join(GOI, "so_tay")
SO_DOI = os.path.join(THU_MUC, "_phien-ban.md")
KHONG_DOI = "Không đổi thao tác:"


def _doc(p):
	return io.open(p, encoding="utf-8").read()


def appver():
	m = re.search(r"var APPVER = '(\d+)'", _doc(os.path.join(GOI, "public", "js", "bep", "12-van-don.js")))
	return m.group(1) if m else ""


def ten_muc():
	ra = set()
	for p in glob.glob(os.path.join(THU_MUC, "*.md")):
		if os.path.basename(p).startswith("_"):
			continue
		for d in _doc(p).split("\n"):
			if d.startswith("## "):
				ra.add(d[3:].strip())
	return ra


def doc_so_doi(chuoi):
	"""'## vNNN' -> danh sách dòng '- ...'. THUẦN."""
	ra, cur = {}, None
	for d in chuoi.split("\n"):
		m = re.match(r"^## v(\d+)\s*$", d)
		if m:
			cur = m.group(1)
			ra.setdefault(cur, [])
			continue
		if cur and d.startswith("- "):
			ra[cur].append(d[2:].strip())
	return ra


def loi_ban(dong, co_muc):
	"""Lỗi của mục một bản: thiếu, tên mục không có thật, miễn không lý do. THUẦN."""
	if not dong:
		return ["chưa có dòng nào"]
	mien = [x for x in dong if x.startswith(KHONG_DOI)]
	if mien:
		if len(dong) != 1 or len(mien[0]) <= len(KHONG_DOI) + 5:
			return ["dòng miễn phải đứng một mình và ghi lý do"]
		return []
	return ["không có mục sổ tay: " + x for x in dong if x not in co_muc]


@ca("sổ tay theo bản: phép thuần đọc sổ đối chiếu, miễn có lý do, tên mục phải có thật")
def _thuan():
	sd = doc_so_doi("## v9\n- A\n- B\n\n## v8\n- Không đổi thao tác: sửa lỗi ngầm đọc file\n## v7\n")
	la("đọc", sd, {"9": ["A", "B"], "8": ["Không đổi thao tác: sửa lỗi ngầm đọc file"], "7": []})
	la("đủ", loi_ban(["A"], {"A"}), [])
	la("thiếu", loi_ban([], {"A"}), ["chưa có dòng nào"])
	la("tên sai", loi_ban(["A", "C"], {"A"}), ["không có mục sổ tay: C"])
	la("miễn hợp lệ", loi_ban(["Không đổi thao tác: sửa lỗi ngầm"], set()), [])
	dung("miễn không lý do", loi_ban(["Không đổi thao tác:"], set()))
	dung("miễn lẫn mục", loi_ban(["Không đổi thao tác: x y z w", "A"], {"A"}))


@ca("sổ tay theo bản: APPVER đang phát hành có mục trong _phien-ban.md, mọi tên mục có thật trong sổ tay")
def _ban_hien_tai():
	v = appver()
	dung("đọc được APPVER", v.isdigit())
	sd = doc_so_doi(_doc(SO_DOI))
	dung("bản v%s có mục trong vagabond/so_tay/_phien-ban.md (anh Việt: deploy phải kèm sổ tay)" % v, v in sd)
	la("bản v%s" % v, loi_ban(sd.get(v), ten_muc()), [])


@ca("sổ tay theo bản: mọi bản đã ghi đều trỏ đúng mục có thật (đổi tên mục thì sửa luôn sổ đối chiếu)")
def _moi_ban():
	co = ten_muc()
	sai = {}
	for v, dong in doc_so_doi(_doc(SO_DOI)).items():
		l = loi_ban(dong, co)
		if l:
			sai[v] = l
	la("bản ghi sai", sai, {})
	dung("sổ tay không nạp tệp đối chiếu", os.path.basename(SO_DOI).startswith("_"))
