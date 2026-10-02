# -*- coding: utf-8 -*-
"""v554: sổ tay viết tay cho trợ lý (vagabond/so_tay/*.md).

Anh Việt giao 02/10/2026: nhân viên hỏi trợ lý thay vì nhắn anh. Ba câu
hỏi thật đầu tiên trong nhật ký trợ lý trên site đều nhận câu "chưa có tài
liệu". Các ca dưới chạy ĐÚNG ba câu đó qua bộ chọn mục, trên sổ tay THẬT
đọc từ đĩa, cộng đoạn mô tả đầu tệp như máy dựng trên site. Ai sửa sổ tay
làm mất mục trả lời được ba câu đó thì cổng đỏ.

Toàn phép thuần, không Frappe, không requests.
"""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_tro_ly import GOI, T

THU_MUC = os.path.join(GOI, "so_tay")


def _doc(duong):
	return io.open(duong, encoding="utf-8").read()


def _chuong():
	return sorted(f for f in os.listdir(THU_MUC) if f.endswith(".md") and not f.startswith("_"))


def _so_tay_that():
	"""Dựng sổ tay như trên site: sổ tay viết tay trước, đoạn đầu tệp sau."""
	ra = []
	for f in _chuong():
		ra.extend(T["doc_chuong"](_doc(os.path.join(THU_MUC, f))))
	bo = {"__init__.py", "hooks.py", "lib.py", "dich.py", "mau_chuan.py",
		"tro_ly.py", "tro_ly_so_tay.py"}
	for f in sorted(os.listdir(GOI)):
		if f.endswith(".py") and f not in bo:
			d = T["doan_dau_tep"](_doc(os.path.join(GOI, f)))
			if d:
				ra.append({"loai": "nghiep_vu", "ten": d.split("\n", 1)[0],
					"duong": "", "mo_ta": "", "chi_tiet": d})
	return ra


@ca("so tay v554: tach chuong thanh muc, tu khoa vao mo ta, chu thich bi bo")
def _tach():
	md = ("# Kho\n\n## Tạo phiếu nhập kho\nTừ khoá: nhận hàng, PNK\n"
		"Ai dùng: Kho\n<!-- kiểm: chưa chắc -->\nCác bước:\n1. Bấm Nhập kho\n\n"
		"## Kiểm kê\nTừ khoá: đếm hàng\nThân\n")
	m = T["doc_chuong"](md)
	la("hai muc", [x["ten"] for x in m], ["Tạo phiếu nhập kho", "Kiểm kê"])
	la("loai", m[0]["loai"], "so_tay")
	la("tu khoa", m[0]["mo_ta"], "Từ khoá: nhận hàng, PNK")
	dung("chu thich khong con dang HTML", "<!--" not in m[0]["chi_tiet"])
	dung("dong tu khoa khong lap trong than", "Từ khoá" not in m[0]["chi_tiet"])
	dung("ghi chuong", m[0]["chi_tiet"].startswith("Chương: Kho"))
	dung("giu cac buoc", "1. Bấm Nhập kho" in m[0]["chi_tiet"])


@ca("so tay v554: moi muc co tu khoa, duoi 1600 ky tu, khong gach dai")
def _quy_uoc():
	sai = []
	n = 0
	for f in _chuong():
		for m in T["doc_chuong"](_doc(os.path.join(THU_MUC, f))):
			n += 1
			than = m["ten"] + m["mo_ta"] + m["chi_tiet"]
			# Do dai tinh tren chu NGUOI SOAN viet: dau CHUA XAC MINH va dong
			# dan do bo nap them vao, khong tinh (review #412 F1).
			viet = re.sub(r"\[CHƯA XÁC MINH:[^\]]*\]", "",
				than.replace(T["DONG_DAN_CHUA_XAC_MINH"], ""))
			if not m["mo_ta"]:
				sai.append("%s: %s thieu Tu khoa" % (f, m["ten"]))
			if len(viet) > 1600:
				sai.append("%s: %s dai %d" % (f, m["ten"], len(viet)))
			if "\u2014" in than or "\u2013" in than:
				sai.append("%s: %s co gach dai" % (f, m["ten"]))
	dung("co it nhat 100 muc (dem duoc %d)" % n, n >= 100)
	la("muc sai quy uoc", sai, [])


# Ba cau hoi THAT trong nhat ky tro ly tren site, ca ba tung nhan "chua co
# tai lieu", va muc phai dung DAU danh sach.
CAU_THAT = (
	("Cách hạch toán cho bút toán cấn trừ công nợ?", "cấn trừ công nợ"),
	("Cách tạo phiếu nhập kho?", "Tạo phiếu nhập kho"),
	("Đặt lại mật khẩu và xoá lịch sử đăng nhập các thiết bị", "thiết bị"),
)


@ca("so tay v554: ba cau hoi that trong nhat ky ra dung muc so tay o dau")
def _cau_that():
	st = _so_tay_that()
	for cau, chu in CAU_THAT:
		ra = T["chon_muc"](cau, st)
		dung("co tu lieu: " + cau, bool(ra))
		if ra:
			dung("muc dau la so tay: " + cau, ra[0].get("loai") == "so_tay")
			dung("muc dau dung viec (%s): %s" % (ra[0]["ten"], cau), chu in ra[0]["ten"])


@ca("so tay v554: cau ngoai le van bi chan khi so tay da day hon")
def _ngoai_le():
	st = _so_tay_that()
	for cau in ("cách nướng bánh mì sourdough tại nhà", "giá vàng hôm nay bao nhiêu",
			"thủ đô nước Pháp là gì", "hôm nay trời đẹp không"):
		la("chan: " + cau, T["chon_muc"](cau, st), [])


@ca("so tay v554: cung do phu thi muc so tay dung truoc doan mo ta dau tep")
def _uu_tien():
	st = [
		{"loai": "nghiep_vu", "ten": "Nhập kho", "mo_ta": "", "chi_tiet": "nhập kho"},
		{"loai": "so_tay", "ten": "", "mo_ta": "", "chi_tiet": "nhập kho"},
	]
	ra = T["chon_muc"]("nhập kho", st)
	la("so tay dung dau", ra[0]["loai"], "so_tay")


# --------------------------------------------- review #412 F1 va bo sung
#
# F1 (P1): ban dau doc_chuong XOA moi chu thich, ke ca <!-- kiem: --> la
# diem nguoi soan CHUA XAC MINH. Mo hinh nhan cau khang dinh ma khong biet,
# trong khi luat tro_ly bao no tin tu lieu. Cac ca duoi chay tren tu lieu
# CUOI CUNG gui mo hinh (chon_muc roi gon_tu_lieu), khong chi tren muc dau.


@ca("so tay #412 F1: diem chua xac minh thanh dau ro rang, muc gan co")
def _chua_xac_minh_tach():
	md = ("# Kho\n\n## Viec A\nTừ khoá: a\nBước 1.\n<!-- kiểm: nút này tên gì -->\n"
		"<!-- ghi chú thường -->\n\n## Viec B\nTừ khoá: b\nBước 1.\n")
	a, b = T["doc_chuong"](md)
	dung("dau chua xac minh co mat", "[CHƯA XÁC MINH: nút này tên gì]" in a["chi_tiet"])
	dung("co dong dan mo hinh", T["DONG_DAN_CHUA_XAC_MINH"] in a["chi_tiet"])
	la("co muc A", a["chua_xac_minh"], 1)
	dung("chu thich thuong van bo", "ghi chú thường" not in a["chi_tiet"])
	la("co muc B", b["chua_xac_minh"], 0)
	dung("muc B khong co dong dan", T["DONG_DAN_CHUA_XAC_MINH"] not in b["chi_tiet"])


@ca("so tay #412 F1: tu lieu that cua cau dat lai mat khau mang dau CHUA XAC MINH")
def _chua_xac_minh_tu_lieu():
	# Dung chuoi reviewer tai hien: chon_muc roi gon_tu_lieu tren so tay that.
	st = _so_tay_that()
	tl = T["gon_tu_lieu"](T["chon_muc"](CAU_THAT[2][0], st))
	dung("tu lieu co dau chua xac minh", "[CHƯA XÁC MINH:" in tl)
	dung("tu lieu khong con chu thich tho", "<!--" not in tl)
	# Muc khong con diem nao chua chac thi khong bi gan co oan.
	sach = [m for m in st if m.get("loai") == "so_tay" and not m.get("chua_xac_minh")]
	dung("van co muc da xac minh (%d)" % len(sach), len(sach) > 0)
	dung("muc sach khong mang dau", all("[CHƯA XÁC MINH:" not in m["chi_tiet"] for m in sach))


@ca("so tay #412 F1: luat tro ly co cau xu ly dau CHUA XAC MINH")
def _luat_chua_xac_minh():
	# Day la phep do chuoi, chi chot rang luat CO dong do (dieu 16): tro_ly.py
	# goi mang nen khong nap duoc vao bo kiem tang khung.
	ma = io.open(os.path.join(GOI, "tro_ly.py"), encoding="utf-8").read()
	i, j = ma.find('LUAT = """'), ma.find('"""', ma.find('LUAT = """') + 10)
	luat = ma[i:j]
	dung("luat nhac dau", "[CHƯA XÁC MINH" in luat)
	dung("luat bao noi ro chua xac minh", "chưa được xác minh" in luat)


@ca("so tay #412 bo sung 2: muc lac de khong lot vao tu lieu cau mat khau")
def _loc_muc_phu():
	st = _so_tay_that()
	ten = [m["ten"] for m in T["chon_muc"](CAU_THAT[2][0], st)]
	dung("khong co Lam bao gia: %s" % ten, not any("báo giá" in x for x in ten))
	dung("khong co Moi tai khoan moi", not any("Mời tài khoản" in x for x in ten))
	dung("van giu Quen mat khau", any("Quên mật khẩu" in x for x in ten))
	# Cau can tru: muc phu dung viec van giu du.
	ten2 = [m["ten"] for m in T["chon_muc"](CAU_THAT[0][0], st)]
	dung("can tru giu it nhat 4 muc (%d)" % len(ten2), len(ten2) >= 4)


@ca("so tay #412 bo sung 1: muc co dia chi man lay tu dong Man hinh")
def _duong():
	m = T["doc_chuong"]("# K\n\n## Nhap\nTừ khoá: x\nMàn hình: Nhập kho (/nhap-kho), tab Chờ nhận\n")[0]
	la("dia chi", m["duong"], "/nhap-kho")
	st = _so_tay_that()
	co = sum(1 for x in st if x.get("loai") == "so_tay" and x.get("duong"))
	dung("phan lon muc so tay co dia chi (%d)" % co, co >= 60)
