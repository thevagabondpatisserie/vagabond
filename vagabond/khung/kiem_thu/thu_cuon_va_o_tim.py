# -*- coding: utf-8 -*-
"""Hai việc anh Việt giao 28/08/2026.

MOT. Bam nut Back cua trinh duyet thi danh sach phai tra ve dung cho dang
doc, khong duoc nem len dau trang.

HAI. Moi cho chon trong app phai co o go tim.
"""

import io
import os

from vagabond import ho_so_tt as hs
from vagabond.khung.kiem_thu.nen import ca, dung


def _js(ten):
	goi = os.path.dirname(os.path.abspath(hs.__file__))
	return io.open(
		os.path.join(goi, "public", "js", "bep", ten), encoding="utf-8").read()


# ------------------------------------------------------- nho vi tri cuon


@ca("cuộn: mỗi nấc màn hình giữ riêng một vị trí, không dùng chung một biến")
def _():
	js = _js("01-khung-app.js")
	# Ban cu chi co MOT bien VGB_CUON cho ca app, va frame() xoa no ve 0 moi
	# khi tieu de doi. Mo chi tiet ra xem la tieu de doi, vi tri mat ngay
	# tai do. Mot bien thi khong the nho duoc hai man cung luc.
	dung("có mảng vị trí cuộn theo nấc", "S.cuon = [0];" in js)
	dung("đẩy xuống nấc mới thì cất vị trí nấc cũ", "S.cuon[S.stack.length - 1] = VGB_CUON;" in js)
	dung("nấc mới bắt đầu từ đầu trang", "S.cuon.push(0);" in js)
	dung("lùi thì cắt luôn mảng", "S.cuon.pop();" in js)
	dung("có hàm hẹn trả lại vị trí", "function vgbHenTraCuon(" in js)


@ca("cuộn: lùi về thì trả lại vị trí DÙ tiêu đề có khác")
def _():
	js = _js("01-khung-app.js")
	# Day la mau chot. Lui ve thi tieu de LUON khac, nen neu cu de
	# `if (doiMan) VGB_CUON = 0` chay truoc thi vi tri vua lay ra bi xoa
	# ngay lap tuc va cong suc phia tren thanh vo nghia.
	than = js.split("function frame(")[1][:1200]
	dung("có biến hẹn riêng", "VGB_CHO_TRA" in than)
	dung("hẹn được ưu tiên hơn việc đổi màn", "if (VGB_CHO_TRA > 0)" in than)
	dung("đọc xong thì xoá hẹn", "VGB_CHO_TRA = 0;" in than)
	dung("chỉ xoá vị trí khi KHÔNG có hẹn", "else if (doiMan) VGB_CUON = 0;" in than)


@ca("cuộn: nút Back của TRÌNH DUYỆT cũng phải trả lại vị trí")
def _():
	# Day chinh la duong anh Viet di khi bao loi. Nut ‹ trong app va nut
	# Back cua trinh duyet la HAI duong khac nhau, sua mot duong thi duong
	# kia van hong.
	js = _js("12-van-don.js")
	than = js.split("window.addEventListener('popstate'")[1]
	dung("cắt mảng vị trí theo nấc", "S.cuon.length = d + 1;" in than)
	dung("hẹn trả lại vị trí nấc còn lại", "vgbHenTraCuon();" in than)
	# Nut Back co the nhay lui NHIEU nac mot lan, nen phai doc nac tren cung
	# sau khi cat chu khong tru di mot.
	dung("cắt theo chỉ số nấc chứ không trừ dần", "S.stack.length = d + 1;" in than)


@ca("cuộn: về trang chủ thì bắt đầu từ đầu, không mang vị trí cũ theo")
def _():
	js = _js("01-khung-app.js")
	than = js.split("function reset(")[1][:500]
	dung("dựng lại mảng một nấc", "S.cuon = [0];" in than)
	dung("xoá hẹn còn sót", "VGB_CHO_TRA = 0;" in than)


# ----------------------------------------------------------- o go tim


@ca("ô tìm: có đồ dùng chung, không mỗi màn tự chế một kiểu")
def _():
	js = _js("07-hop-thoai.js")
	dung("có hàm dựng ô tìm", "function vgbOTim(" in js)
	dung("có hàm nối lọc", "function vgbNoiOTim(" in js)
	dung("có ngưỡng để khỏi bày ô cho ba cái chip", "function vgbCanOTim(" in js)


@ca("ô tìm: lọc trên DOM, KHÔNG vẽ lại màn")
def _():
	# Ve lai man thi mat vi tri cuon, mat cai dang go, va tren dien thoai la
	# ban phim tut xuong sau MOI chu. Dung cai lam nguoi ta bo cuoc.
	js = _js("07-hop-thoai.js")
	than = js.split("function vgbNoiOTim(")[1].split("\n}\n")[0]
	dung("nghe sự kiện gõ", "addEventListener('input'" in than)
	dung("giấu đi chứ không vẽ lại", "style.display" in than)
	for cam in ("go(", "render()", "innerHTML"):
		dung("KHÔNG %s" % cam, cam not in than)


@ca("ô tìm: gõ không dấu vẫn ra, và dùng lại đồ đã có")
def _():
	js = _js("07-hop-thoai.js")
	than = js.split("function vgbNoiOTim(")[1].split("\n}\n")[0]
	# Go "dien luc" phai thay "ĐIỆN LỰC". Dung lai mvKhongDau da co san chu
	# khong viet them mot ban bo dau thu hai trong app.
	dung("bỏ dấu cả hai bên", than.count("mvKhongDau(") >= 2)
	js2 = _js("11-khach-ca-hop-dong.js")
	dung("hàm bỏ dấu vẫn còn đó", "function mvKhongDau(" in js2)


@ca("ô tìm: hộp chọn dùng chung đã có ô tìm")
def _():
	# Mot cho nay lo cho nhieu man: chon tai khoan, chon nha cung cap, chon
	# nhom tai san, chon goi chuc vu deu di qua hoiChon.
	js = _js("07-hop-thoai.js")
	than = js.split("function hoiChon(")[1].split("\n}\n")[0]
	dung("có vẽ ô tìm", "vgbOTim('hcTim'" in than)
	dung("có nối lọc", "vgbNoiOTim(k.box, 'hcTim'" in than)


@ca("ô tìm: danh sách ngắn thì KHÔNG bày ô, bày là làm phiền")
def _():
	js = _js("07-hop-thoai.js")
	than = js.split("function vgbOTim(")[1].split("\n}\n")[0]
	dung("ngắn thì trả về rỗng", "if (!vgbCanOTim(soMuc)) return '';" in than)
	# Nguong 7: cac hang chip trang thai trong app deu 6 cai tro xuong, nen
	# nguong nay khong dung vao chung.
	dung("ngưỡng khai một chỗ", "VGB_NGUONG_TIM = 7" in js)


@ca("ô tìm: chọn nhà cung cấp trên màn hồ sơ thanh toán không phải dò bằng mắt")
def _():
	# Uyen bao 28/08/2026: 17 nha cung cap bay thanh mot bang chip, muon
	# chon mot nha la phai do bang mat. Luc do vá bang cach them o tim
	# `hsNccTim` ngay tren bang chip.
	#
	# 05/09/2026, Issue #196: anh Viet keu bang chip do van dai muot man
	# hinh dien thoai, doi han sang o chon thu gon, cham moi mo tam truot
	# len. O tim di theo vao trong tam truot. Y DINH cua ca kiem nay khong
	# doi: chon mot nha cung cap KHONG duoc bat nguoi ta do bang mat. Chi
	# doi cho kiem, tu bang chip sang tam truot.
	js = _js("19-ho-so-tt.js")
	dung("không còn bày cả bảng chip nhà cung cấp",
		"posChipNut('data-hsn=\"' + h(x.ncc)" not in js)
	dung("có tấm trượt chọn nhà cung cấp", "sheet('Chọn nhà cung cấp'" in js)
	# Tham so thu nam cua `sheet()` la `searchable`. Thieu no thi tam truot
	# hien ra khong co o tim, va nguoi dung lai phai do bang mat.
	i = js.index("sheet('Chọn nhà cung cấp'")
	dung("tấm trượt có bật ô tìm", js[i:i + 200].split("\n")[0].rstrip().endswith("true);"))
	# Duong quay ve xem tat ca nha cung cap van con, nam thanh mot muc
	# trong tam truot thay vi mot chip rieng.
	dung("vẫn còn đường xem tất cả nhà cung cấp",
		"label: 'Tất cả nhà cung cấp'" in js)


@ca("ô tìm: danh mục nhà cung cấp lọc được ngay không chờ máy chủ")
def _():
	js = _js("20-danh-muc-quyen.js")
	dung("có nối lọc trên DOM", "vgbNoiOTim(b, 'nccQ'" in js)
	# Van giu duong hoi may chu, vi danh sach cat con 200 dong.
	dung("vẫn còn đường hỏi máy chủ", "nccTim = q.value.trim(); go(scrNcc, true);" in js)
