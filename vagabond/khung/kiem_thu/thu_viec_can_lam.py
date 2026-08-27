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


# ------------------------------------------- o "Viec can lam" phai deo con so
#
# Anh Viet 27/08/2026: ke toan gui ba ho so thanh toan len cho giam doc duyet,
# tren app cua anh "chang co gi de duyet ca".
#
# Da do lai tren site that: ba ho so nam dung buoc "Cho giam doc", tai khoan
# cua anh co vai AP Giam doc, va `viec_can_lam.danh_sach` tra ve du ca ba. Ba
# lop deu dung. Cai sai nam o TRANG CHU: o "Viec can lam" la o DUY NHAT khong
# deo con so, moi o khac deu co. Nhin vao mot o trong tron thi khong ai bam.
#
# Roi anh sang man "Duyet phieu chi" - man do doc Payment Entry, mot loai
# chung tu khac han ho so thanh toan APP, nen no rong that. Hai hang doi tien
# ma chi mot cai mang cai ten nghe nhu la tat ca.

TEP_JS_CHI = os.path.join(GOC, "vagabond", "public", "js", "bep", "04-tao-phieu.js")


@ca("viec can lam: co duong DEM rieng de trang chu hoi con so")
def _co_duong_dem():
	src = _doc(TEP_PY)
	dung("có hàm dem", re.search(r"^def dem\(\)", src, re.M) is not None)
	# Phai co whitelist, khong thi man hinh goi khong toi.
	m = re.search(r"@frappe\.whitelist\(\)\s*\ndef dem\(\)", src)
	dung("dem có mở cửa ra ngoài", m is not None)
	# Va phai khai trong so cua ngo, khong thi lan sau ai chen ham moi vao
	# giua se lam no mat quyen goi ma khong ai hay.
	ngo = _doc(os.path.join(GOC, "vagabond", "khung", "kiem_thu", "thu_cua_ngo.py"))
	m2 = re.search(r'"viec_can_lam\.py": \[([^\]]*)\]', ngo)
	dung("thấy dòng khai cửa ngõ", m2 is not None)
	dung("dem có trong sổ cửa ngõ", '"dem"' in (m2.group(1) if m2 else ""))


@ca("trang chu: o Viec can lam PHAI deo con so nhu moi o khac")
def _o_vcl_deo_so():
	js = _doc(TEP_JS)
	m = re.search(r"data-nhom=\"VCL\".*?</div>';", js, re.S)
	dung("tìm thấy ô Việc cần làm", m is not None)
	o = m.group(0) if m else ""
	# `gb` la lop cua con so tren moi o khac. O nay tung thieu dung mot cai do.
	dung("ô có chỗ đeo con số", "gb" in o)
	dung("con số có mã riêng để điền sau", "vgbSoVCL" in o)
	dung("có gọi máy chủ đếm", "vgbDemVCL()" in js)
	dung("đường đếm đúng tên hàm bên máy chủ",
		"vagabond.viec_can_lam.dem" in js)


@ca("trang chu: dem hong thi IM LANG, khong pha man")
def _dem_hong_thi_im():
	js = _doc(TEP_JS)
	m = re.search(r"async function vgbDemVCL\(\) \{.*?\n\}", js, re.S)
	dung("tìm thấy vgbDemVCL", m is not None)
	than = m.group(0) if m else ""
	dung("có bọc try", "try {" in than)
	# Khong duoc goi toast hay frame trong nhanh hong: mot con so phu ma lam
	# ca trang chu do len thi te hon la khong co con so.
	dung("không toast khi hỏng", "toast" not in than)
	dung("không vẽ đè màn khi hỏng", "frame(" not in than)


@ca("duyet phieu chi: o rong phai chi duong sang Ho so thanh toan")
def _man_chi_chi_duong():
	js = _doc(TEP_JS_CHI)
	m = re.search(r"function payRong\(\) \{.*?\n\}", js, re.S)
	dung("tìm thấy payRong", m is not None)
	than = m.group(0) if m else ""
	dung("nói rõ còn hồ sơ chờ duyệt", "hồ sơ thanh toán" in than)
	dung("có nút mở màn kia", "data-hstt" in than)
	# Nut phai dan toi dung ma man APPTT, di qua vgbGo chu khong go() thang.
	dung("bấm nút thì đi qua cửa đặt địa chỉ", "vgbGo('APPTT')" in js)
	# Va chi noi cau do khi THAT SU con ho so, khong doa suong.
	dung("chỉ nói khi thật sự còn hồ sơ", "if (paySoHoSo)" in than)
	dung("hết sạch thì vẫn là câu cũ", "Không có phiếu nào cần xử lý" in than)


@ca("duyet phieu chi: chi dem ho so o buoc CHO DUYET, khong dem ca so")
def _chi_dem_cho_duyet():
	js = _doc(TEP_JS_CHI)
	m = re.search(r"async function payDoHoSo\(ve\) \{.*?\n\}", js, re.S)
	dung("tìm thấy payDoHoSo", m is not None)
	than = m.group(0) if m else ""
	dung("lọc đúng loại hồ sơ thanh toán", "ho_so_tt" in than)
	# `cho_duyet` la buoc dang cho CHINH nguoi nay. Neu dem ca ban nhap va
	# buoc cho chuyen tien thi con so se doa mot viec khong phai cua ho.
	dung("chỉ đếm bước chờ duyệt", "'cho_duyet'" in than)
	dung("hỏng thì im lặng", "catch (e) { return; }" in than)
