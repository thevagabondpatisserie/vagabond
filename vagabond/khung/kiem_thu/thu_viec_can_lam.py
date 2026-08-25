# -*- coding: utf-8 -*-
"""Ca kiểm cho màn Việc cần làm. Soi mã nguồn, không cần site.

VÌ SAO CÓ TỆP NÀY
-----------------
Ngày 25/08/2026 soi lại thì hai loại phiếu `ycmh` và `ho_so_tt` đã khai đủ
trong `LOAI_PHIEU` và `MA_TRAN` từ 20/08, tức là có nhãn, có icon, có khai
vai, nhưng KHÔNG có hàm nguồn nào trong danh sách `nguon`. Hệ quả: hai chip
đó vĩnh viễn đếm 0 và không bao giờ hiện ra, nên Uyên vẫn phải nhớ tự mở màn
Duyệt yêu cầu mua, chị Dung vẫn phải nhớ tự mở màn Hồ sơ thanh toán.

Không lớp nào bắt được kiểu hỏng này. Mã chạy đúng, không ném lỗi, không ghi
log, cổng trước deploy trả về 0. Nó chỉ lộ ra khi có người ngồi đếm xem chip
nào không bao giờ sáng.

Cùng kiểu đó, `tang_qua` thêm ở v305 có hàm nguồn bên máy chủ nhưng bên màn
hình thì thiếu icon và thiếu nhánh mở, nên bấm vào một việc tặng quà lại ra
câu "cần xử lý trên máy tính" trong khi màn CRM đã có sẵn.

Ba ca dưới đây chốt cứng: khai một loại phiếu là phải khai ĐỦ BỐN CHỖ.
"""

import ast
import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))
TEP_PY = os.path.join(GOC, "vagabond", "viec_can_lam.py")
TEP_JS = os.path.join(GOC, "vagabond", "public", "js", "bep", "02-trang-chu.js")


def _doc(duong):
	return io.open(duong, encoding="utf-8").read()


def _khoa_loai_phieu(src):
	"""Các khoá khai trong LOAI_PHIEU. Đọc thẳng từ mã nguồn."""
	m = re.search(r"^LOAI_PHIEU = \(.*?^\)", src, re.S | re.M)
	return [x for x in re.findall(r'\(\s*"([a-z_]+)"', m.group(0))] if m else []


def _khoa_trong_nguon(src):
	"""Các khoá thực sự có hàm gom việc, đọc từ danh sách `nguon`."""
	m = re.search(r"^\tnguon = \[.*?^\t\]", src, re.S | re.M)
	return re.findall(r'\(\s*"([a-z_]+)"\s*,\s*lambda', m.group(0)) if m else []


@ca("viec can lam: moi loai khai trong LOAI_PHIEU phai co ham gom viec that")
def _():
	src = _doc(TEP_PY)
	khai = _khoa_loai_phieu(src)
	co = _khoa_trong_nguon(src)
	dung("đọc được LOAI_PHIEU", len(khai) > 0)
	dung("đọc được danh sách nguon", len(co) > 0)
	# Khai mà không có hàm nguồn thì chip đếm 0 vĩnh viễn, im lặng.
	thieu = sorted(set(khai) - set(co))
	la("loại khai rồi mà không có hàm gom việc", thieu, [])
	# Ngược lại cũng sai: có hàm gom mà quên khai thì việc gom ra rồi bị
	# cổng `thay_duoc` chặn lại, cũng im lặng y như vậy.
	thua = sorted(set(co) - set(khai))
	la("loại có hàm gom mà quên khai trong LOAI_PHIEU", thua, [])


@ca("viec can lam: moi loai deu phai co ham nguon dinh nghia that trong tep")
def _():
	src = _doc(TEP_PY)
	cay = ast.parse(src)
	co_ham = {n.name for n in cay.body if isinstance(n, ast.FunctionDef)}
	for k in _khoa_trong_nguon(src):
		dung("có hàm _viec_%s" % k, ("_viec_%s" % k) in co_ham)


@ca("viec can lam: moi loai deu phai co icon va co duong mo ben man hinh")
def _():
	src = _doc(TEP_PY)
	js = _doc(TEP_JS)
	khai = _khoa_loai_phieu(src)

	# vclIcon: thiếu icon thì dòng việc hiện ra trơ trọi không có gì nhận ra.
	m = re.search(r"function vclIcon\(l\) \{.*?\n\}", js, re.S)
	dung("tìm thấy vclIcon", bool(m))
	icon = m.group(0) if m else ""
	thieu_icon = sorted(k for k in khai if ("%s:" % k) not in icon)
	la("loại thiếu icon trong vclIcon", thieu_icon, [])

	# vclMo: thiếu nhánh thì bấm vào ra câu "cần xử lý trên máy tính", kể cả
	# khi màn hình của nó đã có sẵn trên app.
	m = re.search(r"function vclMo\(x\) \{.*?\n\}", js, re.S)
	dung("tìm thấy vclMo", bool(m))
	mo = m.group(0) if m else ""
	thieu_mo = sorted(k for k in khai if ("'%s'" % k) not in mo)
	# `don_mua` cố ý KHÔNG có nhánh: đơn mua quá hẹn phải xử lý trên Desk,
	# app chưa có màn nào cho nó. Đây là ngoại lệ DUY NHẤT, khai rõ ra đây
	# để người sau biết là cố ý chứ không phải bỏ sót.
	la("loại thiếu nhánh mở trong vclMo", thieu_mo, ["don_mua"])
