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
	dung("chu thich khong gui mo hinh", "kiểm:" not in m[0]["chi_tiet"])
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
			if not m["mo_ta"]:
				sai.append("%s: %s thieu Tu khoa" % (f, m["ten"]))
			if len(than) > 1600:
				sai.append("%s: %s dai %d" % (f, m["ten"], len(than)))
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
