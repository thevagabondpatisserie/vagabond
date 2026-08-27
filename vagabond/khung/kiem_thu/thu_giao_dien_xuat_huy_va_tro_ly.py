# -*- coding: utf-8 -*-
"""Hai việc giao diện anh Việt giao ngày 27/08/2026.

MỘT: *"Màn xuất huỷ thì anh thấy visual đang bị xấu. Em phải làm thành khung
chọn đẹp như các màn khác, nhìn nó bị thô sơ (các ô chọn kho, lý do, ảnh
chứng minh (ô này bắt buộc nha),...)"*

HAI: *"Ô trợ lý phải làm dạng floating để kéo đi được, nó đang bị cố định 1
chỗ nên các nút ở góc trái màn hình bị nó che, không nhìn thấy được nút."*

Nút trợ lý neo cứng ở góc dưới bên trái, và màn Lập phiếu xuất huỷ có nút
nằm đúng chỗ đó. Một nút trợ giúp mà che mất nút làm việc thật thì nó đang
cản trở chứ không còn trợ giúp.
"""

import io
import os

from vagabond import xuat_kho
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _js(ten):
	goc = os.path.dirname(os.path.abspath(xuat_kho.__file__))
	return io.open(
		os.path.join(goc, "public", "js", "bep", ten), encoding="utf-8").read()


# ------------------------------------------------- màn Lập phiếu xuất huỷ


@ca("xuất huỷ: ba ô đều nằm trong thẻ có tiêu đề và biểu tượng")
def _():
	src = _js("03-kho-chung-tu.js")
	i = src.find("var body = frame('Lập phiếu xuất huỷ',")
	dung("tìm thấy màn lập phiếu", i > 0)
	than = src[i:i + 4000]
	for nhan in ("Kho xuất", "Lý do huỷ", "Ảnh chứng minh", "Danh sách hàng huỷ", "Ghi chú"):
		dung("có thẻ %s" % nhan, ("<b>" + nhan + "</b>") in than)
	# Khong con o nhap tran kieu cu tren man nay.
	la("không còn nhãn xám kiểu cũ", than.count('class="vxl"'), 0)
	la("không còn ô chọn kiểu cũ", than.count('class="vxs"'), 0)
	dung("dùng ô chọn kiểu mới", 'class="vfs"' in than)


@ca("xuất huỷ: ảnh chứng minh nay là BẮT BUỘC, không còn chữ không bắt buộc")
def _():
	src = _js("03-kho-chung-tu.js")
	i = src.find("var body = frame('Lập phiếu xuất huỷ',")
	than = src[i:i + 4000]
	la("không còn chữ không bắt buộc", than.count("không bắt buộc"), 0)
	# Ba o bat buoc deu phai deo nhan, khong chi rieng anh.
	la("ba ô đeo nhãn Bắt buộc", than.count('class="bat">Bắt buộc'), 4)
	dung("chặn lưu khi thiếu ảnh",
		"to(body.querySelector('#vxAnhO'), !XK.anh);" in src)
	dung("nói rõ vì sao chặn",
		"Phiếu xuất huỷ bắt buộc có ảnh chứng minh." in src)


@ca("xuất huỷ: thiếu ô nào thì tô đỏ ô đó và kéo vào giữa màn, không chỉ bung toast")
def _():
	# Bieu mau nay dai hon mot man hinh. Mot cau toast tat sau vai giay thi
	# nguoi dung doc xong van khong biet phai go vao dau.
	src = _js("03-kho-chung-tu.js")
	dung("có hàm tô ô thiếu", "var to = function (el, co) {" in src)
	dung("kéo ô thiếu đầu tiên vào giữa màn",
		"thieu.scrollIntoView({ block: 'center', behavior: 'smooth' })" in src)
	dung("sửa xong thì bỏ tô đỏ ở ô lý do",
		"XK.lyDo = this.value; this.classList.remove('thieu');" in src)
	dung("và ở ô kho xuất", "this.classList.remove('thieu');" in src)


@ca("xuất huỷ: chọn ảnh xong thì thấy ĐÚNG tấm ảnh vừa chọn")
def _():
	# Ban cu chi hien mot dong chu "Da tai anh len". Chon nham anh trong thu
	# vien thi khong ai biet cho den luc quan ly mo phieu ra xem.
	src = _js("03-kho-chung-tu.js")
	dung("bày ảnh thật ra màn", "ok.innerHTML = '<img class=\"vfanh\"" in src)
	dung("đổi trạng thái ô sang đã xong", "o.classList.add('xong');" in src)
	dung("tải hỏng thì nói ra tại chỗ", "t.textContent = 'Không tải được ảnh';" in src)


@ca("xuất huỷ: các lớp giao diện mới đặt tên chung, không đặt theo một màn")
def _():
	# Dat ten `vf` chu khong `vxh`: man nao co bieu mau cung dung lai duoc.
	css = _js("02-trang-chu.js")
	for lop in (".vf{", ".vf .vfh{", ".vfs{", ".vfi{", ".vfa{", ".vfanh{"):
		dung("có lớp %s" % lop, lop in css)
	dung("ô đang thiếu có màu riêng", ".vfs.thieu,.vfi.thieu{" in css)
	dung("ô chọn tự vẽ mũi tên cho ba hệ giống nhau",
		"-webkit-appearance:none" in css and "data:image/svg+xml" in css)


# ------------------------------------------------------ nút trợ lý kéo được


@ca("trợ lý: nút kéo đi được, và kéo xong không bung hộp thoại")
def _():
	src = _js("35-tro-ly.js")
	dung("có hàm cho kéo", "function tlChoKeo(nut)" in src)
	dung("bắt đầu kéo", "nut.addEventListener('pointerdown'" in src)
	dung("theo tay khi kéo", "nut.addEventListener('pointermove'" in src)
	# Cham va keo tren dien thoai deu la mot chuoi pointerdown roi pointerup.
	# Khong phan biet thi moi lan keo xong hop thoai bat len.
	dung("phân biệt chạm với kéo bằng quãng đường", "if (daDi < 6) return;" in src)
	dung("chặn cú bấm đó lại sau khi kéo", "if (daDi >= 6) { e.stopPropagation();" in src)
	# touch-action:none la BAT BUOC, thieu no thi trinh duyet dien thoai hieu
	# cu keo la cuon trang va nut khong nhuc nhich.
	dung("khai touch-action none", "touch-action:none" in src)


@ca("trợ lý: nút không bao giờ ra khỏi màn hình")
def _():
	src = _js("35-tro-ly.js")
	dung("có hàm kẹp trong mép", "function tlKep(nut, x, y)" in src)
	dung("kẹp theo chiều ngang", "Math.min(x, window.innerWidth - w - m)" in src)
	dung("kẹp theo chiều dọc", "Math.min(y, window.innerHeight - h - m)" in src)
	# Xoay man hay ban phim bung len lam man hep lai: phai keo nut ve trong.
	dung("màn hẹp lại thì kéo nút về trong",
		"window.addEventListener('resize'" in src)


@ca("trợ lý: nhớ chỗ đã kéo, không bắt kéo lại mỗi lần đổi màn")
def _():
	src = _js("35-tro-ly.js")
	dung("có khoá lưu chỗ", "var TL_CHO = 'vgbTroLyCho';" in src)
	dung("đọc chỗ cũ lúc gắn nút", "var cu = tlDocCho();" in src)
	dung("ghi lại sau khi kéo xong", "localStorage.setItem(TL_CHO," in src)
	# Nho theo left/top chu khong theo bottom: doi man xoay ngang hay ban phim
	# bung len thi bottom nhay lung tung.
	dung("neo theo left và top", "nut.style.bottom = 'auto';" in src)
	# Doc hong (che do rieng tu, xoa du lieu trang) thi phai chay tiep chu
	# khong duoc lam chet nut.
	dung("đọc hỏng thì vẫn chạy", "} catch (e) { }\n  return null;" in src)
