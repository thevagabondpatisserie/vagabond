# -*- coding: utf-8 -*-
"""Ba viec anh Viet bao ngay 22/08/2026.

MOT. Man "Duyet phieu chi" hien ca phieu THU tien khach
-------------------------------------------------------
*"Sao tu nhien lai co ca HDM cua khach le online the nhi. Day la luong thanh
toan di HDB ma."*

Vi sao lot vao: luong duyet "Duyet phieu chi APP" dat tren CA doctype Payment
Entry, nen Frappe gan trang thai "Nhap" cho MOI phieu tien moi, ke ca phieu
THU tien khach do may tu tao khi doi soat sao ke. Man danh sach truoc day chi
loc theo `workflow_state` nen vo hai tay.

O `custom_loai_chi` KHONG phan biet duoc, vi no co gia tri mac dinh: phieu thu
tien khach cung mang chu "Thanh toan cong no NCC". Loc theo `payment_type` moi
la cach chac.

HAI. Bam nut nao cung nhay ve dau trang
---------------------------------------
*"Trang tao APP thanh toan truoc cho NCC thi cu bam nut nao trong phieu la
lai bi cuon ve dau trang."*

Goc re: hau het man goi `frame()` HAI LAN cho mot lan bam, lan dau la khung
cho ngan tun. Ban va cu doc vi tri cuon o dau `frame()`, nen lan hai doc phai
so 0 cua khung cho va xoa mat vi tri that.

BA. Mau in Chung tu thanh toan
------------------------------
*"Bo het may cai gach cheo ngan giua phan tieng Viet va phan tieng Anh. Cho
phan tieng Anh luon xuong hang ben duoi phan tieng Viet va luon duoc in
nghieng."*
"""

import io
import os

from vagabond import may_in
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _js(ten):
	goi = os.path.dirname(os.path.abspath(may_in.__file__))
	return io.open(
		os.path.join(goi, "public", "js", "bep", ten), encoding="utf-8").read()


def _mau_in():
	goi = os.path.dirname(os.path.abspath(may_in.__file__))
	return io.open(
		os.path.join(goi, "mau_in", "chung_tu_thanh_toan.html"), encoding="utf-8").read()


# ------------------------------------------------- MOT: chi hien phieu chi


@ca("duyệt phiếu chi: danh sách CHỈ lấy phiếu chi, không lấy phiếu thu")
def _():
	js = _js("04-tao-phieu.js")
	khuc = js.split("async function scrPayList(")[1].split("async function scrPayView(")[0]
	# Đếm theo SỐ LẦN GỌI chứ không chốt cứng con số hai: 03/09/2026 màn này
	# thêm tab "Tôi lập" nên có ba lần gọi. Điều phải giữ là mọi lần gọi đều
	# có bộ lọc, chứ không phải là có đúng bao nhiêu lần gọi.
	so_goi = khuc.count("getList('Payment Entry'")
	dung("có ít nhất hai lần gọi", so_goi >= 2)
	la("mọi lần gọi đều lọc payment_type Pay", khuc.count("payment_type: 'Pay'"), so_goi)
	dung("có tách phiếu trả tiền cho khách ra", "!== 'Customer'" in khuc)


@ca("duyệt phiếu chi: màn chi tiết cũng chặn phiếu thu")
def _():
	js = _js("04-tao-phieu.js")
	khuc = js.split("async function scrPayView(")[1]
	dung("có phép kiểm", "d.payment_type !== 'Pay'" in khuc)
	dung("nói rõ đây là phiếu thu", "phiếu THU tiền khách" in khuc)
	dung("dừng lại, không bày nút duyệt", "phiếu chi. Phiếu thu tiền khách do máy " not in khuc and khuc.split("d.payment_type !== 'Pay'")[1].split("}")[0].count("return") == 1)


@ca("duyệt phiếu chi: KHÔNG lọc bằng custom_loai_chi vì ô đó có giá trị mặc định")
def _():
	# Phieu thu tien khach cung mang "Thanh toan cong no NCC" o o nay, nen
	# ai do doi sang loc bang no la loi quay lai ma khong ai hay.
	js = _js("04-tao-phieu.js")
	khuc = js.split("async function scrPayList(")[1].split("async function scrPayView(")[0]
	dung("không dùng custom_loai_chi làm bộ lọc",
	     "custom_loai_chi:" not in khuc.replace("'custom_loai_chi'", ""))


# ----------------------------------------------------- HAI: giu vi tri cuon


@ca("giữ vị trí cuộn: ghi lúc người dùng cuộn, không đọc lúc vẽ lại màn")
def _():
	js = _js("01-khung-app.js")
	dung("có hàm theo dõi cuộn", "function vgbTheoDoiCuon(" in js)
	dung("nghe sự kiện scroll", "addEventListener('scroll'" in js)
	dung("nghe một lần cho mỗi khung", "ob.vgbDaNghe" in js)


@ca("giữ vị trí cuộn: bỏ qua sự kiện do CHÍNH MÌNH gây ra khi trả vị trí")
def _():
	# Day la cai bay: dat scrollTop cung sinh su kien scroll, ma luc khung
	# cho con ngan thi trinh duyet ket qua ve 0. Ghi lai so 0 do la mat vi tri
	# lan nua, dung cai loi vua di chua.
	js = _js("01-khung-app.js")
	dung("có cờ đang trả", "VGB_DANG_TRA" in js)
	khuc = js.split("function vgbTheoDoiCuon(")[1].split("\n}")[0]
	dung("người nghe bỏ qua khi cờ bật", "if (VGB_DANG_TRA) return;" in khuc)
	tra = js.split("function vgbTraCuon(")[1].split("\n}")[0]
	dung("bật cờ trước khi đặt", "VGB_DANG_TRA = 1;" in tra)
	dung("có đường tắt cờ", "VGB_DANG_TRA = 0;" in tra)


@ca("giữ vị trí cuộn: frame KHÔNG còn đọc scrollTop lúc vẽ lại")
def _():
	js = _js("01-khung-app.js")
	khung = js.split("function frame(title, bodyHtml, opt)")[1].split("\n}")[0]
	dung("không đọc scrollTop trong frame", "scrollTop" not in khung)
	dung("đổi màn thì xoá vị trí cũ", "if (doiMan) VGB_CUON = 0;" in khung)
	dung("cùng màn thì trả lại", "if (giuCuon) vgbTraCuon(" in khung)


@ca("giữ vị trí cuộn: dùng chung, nằm ở tầng khung chứ không rải từng màn")
def _():
	# Nam trong 01-khung-app.js nen MOI man goi frame() deu duoc huong, khong
	# phai di sua tung man mot.
	js = _js("01-khung-app.js")
	dung("hàm giữ cuộn nằm cùng tệp với frame", "function frame(" in js and "function vgbTraCuon(" in js)


# ------------------------------------------------------ BA: mau in song ngu


@ca("mẫu in: không còn dấu gạch chéo ngăn tiếng Việt với tiếng Anh")
def _():
	t = _mau_in()
	than = t.split("</style>")[1]
	for xau in ("/ Payment", "/ Voucher", "/ Vendor", "/ Customer", "/ Tax ID",
	            "/ Account", "/ Bank name", "/ Description", "/ Amount",
	            "/ Total", "/ Less advance", "/ Remaining", "/ Remarks",
	            "/ PAYMENT VOUCHER"):
		dung("bỏ hết %s" % xau, xau not in than)


@ca("mẫu in: có nhãn song ngữ dùng chung, tiếng Anh xuống dòng và in nghiêng")
def _():
	t = _mau_in()
	dung("có macro dùng chung", '{%- macro sn(vi, en) -%}' in t)
	dung("tiếng Anh nằm trong thẻ riêng", '<span class="en">{{ en }}</span>' in t)
	css = t.split("</style>")[0]
	dung("thẻ đó xuống dòng", ".apv .en" in css and "display:block" in css)
	dung("và in nghiêng", "font-style:italic" in css)


@ca("mẫu in: mọi nhãn song ngữ đều đi qua macro, không ai gõ tay nữa")
def _():
	t = _mau_in()
	than = t.split("</style>")[1]
	la("số nhãn đi qua macro", than.count("sn(") >= 28, True)
	dung("không còn <br> ghép hai thứ tiếng ở tiêu đề bảng",
	     "<br>Invoice date" not in than and "<br>Full name" not in than
	     and "<br>Remark" not in than)


@ca("mẫu in: nhãn tiếng Việt giữ dấu hai chấm, tiếng Anh thì không")
def _():
	# Dat dau hai cham o dong tieng Viet thoi, de dong tieng Anh doc ra la mot
	# cum danh tu chu khong phai mot nhan thu hai.
	t = _mau_in()
	dung("nhãn Việt có hai chấm", 'sn("Số chứng từ:", "Voucher no.")' in t)
	dung("nhãn Anh không có hai chấm", '"Voucher no.:"' not in t)
