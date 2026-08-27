# -*- coding: utf-8 -*-
"""Hai việc ngày 27/08/2026.

MỘT: hệ phải NÓI RA khi đơn Pancake không về.

Đo trên dữ liệu thật ngày 27/08: hoá đơn sinh từ đơn Pancake tụt từ 45 đơn
ngày 25, xuống 12 đơn ngày 26, còn 1 đơn ngày 27. Số bản ghi bị xoá: 0. Số
hoá đơn bị huỷ: 0. Đơn chỉ đơn giản là không về, vì Pancake trả 403.

Suốt hai ngày không màn hình nào nói một câu nào, vì chuỗi cuối ngày bắt lỗi
Pancake rồi chạy tiếp và chỉ ghi nhật ký. Anh Việt tưởng dữ liệu bị mất. Cái
hỏng nặng nhất không phải mã 403 mà là hệ IM LẶNG.

HAI: công tắc tay tạm ngừng bán một mã trên web đặt bánh, vì *"có vài trường
hợp bất khả kháng, còn tồn nhưng phải tắt, không bán được hôm đó"*.
"""

import io
import os

from vagabond import pancake_nhip, tat_ban_web
from vagabond.khung.kiem_thu.nen import ca, dung, la

GIO = 3600


def _py(ten):
	goc = os.path.dirname(os.path.abspath(pancake_nhip.__file__))
	return io.open(os.path.join(goc, ten), encoding="utf-8").read()


def _js(duong):
	goc = os.path.dirname(os.path.dirname(os.path.abspath(pancake_nhip.__file__)))
	return io.open(os.path.join(goc, "vagabond", duong), encoding="utf-8").read()


# ------------------------------------------------- nhịp Pancake nói ra sự thật


@ca("nhịp Pancake: đang hỏng thì câu báo nói rõ số đang xem là số cũ")
def _():
	t = {"luc_ok": 1000.0, "ok_luc_nao": "09:17 26/08", "luc_hong": 2000.0,
		"loi": "Pancake đang từ chối lượt gọi (mã 403)."}
	c = pancake_nhip.cau_bao(t, 2100.0)
	dung("có nói đơn chưa về", "chưa về" in c)
	dung("có nhắc lại lý do", "403" in c)
	dung("có nói số là số cũ", "lần kéo được gần nhất" in c)
	dung("có nói lúc mấy giờ", "09:17 26/08" in c)


@ca("nhịp Pancake: kéo được rồi thì im, không dán cảnh báo vô cớ")
def _():
	t = {"luc_ok": 2000.0, "ok_luc_nao": "14:15 27/08", "luc_hong": 1000.0}
	la("vừa kéo được thì không báo gì", pancake_nhip.cau_bao(t, 2100.0), "")
	# Sua xong thi phai HET bao, khong duoc bam vao lan hong cu.
	la("hỏng cũ hơn lần kéo được thì thôi", pancake_nhip.cau_bao(
		{"luc_ok": 5000.0, "luc_hong": 4000.0, "ok_luc_nao": "x"}, 5100.0), "")


@ca("nhịp Pancake: im quá lâu cũng phải kêu, dù không ai kịp ghi lại lần hỏng")
def _():
	# Truong hop that: tien trinh chet giua chung, khong ai kip ghi "hong".
	# Neu chi soi o `luc_hong` thi man hinh im lang y nhu cu.
	t = {"luc_ok": 1000.0, "ok_luc_nao": "09:17 26/08", "luc_hong": 0}
	c = pancake_nhip.cau_bao(t, 1000.0 + 5 * GIO)
	dung("năm tiếng không có đơn thì kêu", "5 tiếng" in c)
	dung("nói rõ danh sách có thể thiếu", "có thể thiếu" in c)
	la("hai tiếng thì chưa kêu", pancake_nhip.cau_bao(t, 1000.0 + 1.5 * GIO), "")


@ca("nhịp Pancake: chưa lần nào kéo được thì chỉ thẳng vào khoá API")
def _():
	c = pancake_nhip.cau_bao({}, 9999.0)
	dung("nói chưa lần nào kéo được", "Chưa lần nào" in c)
	dung("chỉ chỗ phải sửa", "khoá API" in c)


@ca("nhịp Pancake: không còn chỗ nào nuốt lỗi rồi chạy tiếp")
def _():
	src = _py("ban_hang.py")
	# Hai cho da tung nuot loi. Ca hai nay phai ghi lai truoc khi di tiep.
	dung("nhịp cron ghi lại khi hỏng",
		"pancake_nhip.ghi_hong(_loi_pancake_nguoi_doc(e))" in src)
	dung("chuỗi cuối ngày ghi lại khi hỏng",
		"pancake_nhip.ghi_hong(_loi_pancake_nguoi_doc(e_kd))" in src)
	dung("kéo được thì cũng ghi lại", src.count("pancake_nhip.ghi_ok()") >= 2)
	dung("có hàm đổi lỗi mạng sang tiếng Việt",
		"def _loi_pancake_nguoi_doc(e):" in src)
	dung("và hàm đó giấu khoá API", "chuoi = giau_khoa(e)" in src)
	dung("nhật ký cũng giấu khoá",
		'frappe.log_error(giau_khoa(frappe.get_traceback()), "ban_hang cron")' in src)
	dung("màn hoá đơn nhận được tình trạng",
		'"pancake": pancake_nhip.tinh_trang()' in src)


@ca("nhịp Pancake: cả hệ nghỉ chung, không mỗi mô đun tự đếm giờ riêng")
def _():
	kb = _py("kiem_banh.py")
	dung("kiểm bánh gọi nghỉ chung", "pancake_nhip.bat_dau_nghi()" in kb)
	dung("kiểm bánh hỏi nghỉ chung", "return pancake_nhip.con_nghi()" in kb)
	# Bang moc rieng cua man kiem banh phai bien mat, khong thi hai cho dem
	# gio khac nhau va cai nay khong biet cai kia.
	la("không còn bảng mốc riêng của kiểm bánh", kb.count("_NGHI_DEN"), 0)
	bh = _py("ban_hang.py")
	dung("nhịp cron cũng chịu ký nghỉ chung",
		"if pancake_nhip.con_nghi():" in bh)


@ca("nhịp Pancake: màn Hoá đơn Sales dán cảnh báo lên đầu bảng")
def _():
	man = _js("public/js/bep/10-bill-quay.js")
	dung("đọc tình trạng máy chủ gửi về", "var pk = (kq && kq.pancake) || {};" in man)
	dung("có câu báo thì dán lên", "if (pk.cau_bao) {" in man)
	dung("dán TRƯỚC lịch chọn ngày, tức trên đầu bảng",
		man.find("if (pk.cau_bao) {") < man.find("Lich chon ngay"))


@ca("nhịp Pancake: nhịp mùa vụ đã nới ra và biết nghỉ khi bị từ chối")
def _():
	# Con so that ngay 27/08/2026: mua Trung thu chay 01/08 den 27/09, nhip
	# `mua_vu.dong_bo_tu_dong` chay MOI PHUT va moi lan keo CA MUA, tran 30
	# trang. Do la hang chuc nghin luot goi Pancake moi ngay chi rieng nhip
	# nay - va Pancake chan suot hai ngay.
	src = _py("mua_vu.py")
	dung("có nhịp thật riêng, không chạy mỗi phút nữa", "NHIP_TU_DONG = 300" in src)
	dung("bỏ qua khi cả hệ đang nghỉ", "if pancake_nhip.con_nghi():" in src)
	dung("kéo được thì ghi lại", "pancake_nhip.ghi_ok()" in src)
	dung("hỏng thì ghi lại chứ không nuốt", "pancake_nhip.ghi_hong(_loi_pancake(e))" in src)
	dung("nhật ký giấu khoá", "message=giau_khoa(frappe.get_traceback())" in src)
	# Phai ghi ro trong ma nguon rang day la doi mot phan quyet dinh cu cua
	# anh Viet, va vi sao. Khong thi sau nay co nguoi doc lai va tuong ai do
	# lo tay noi nhip.
	dung("chép lại lý do đổi quyết định 18/08",
		"di nguoc mot phan dieu anh Viet chot 18/08" in src)


# ------------------------------------------- công tắc tắt bán trên web


@ca("tắt bán web: ô trống, ô hỏng hay ngày đã qua đều là ĐANG BÁN")
def _():
	# Nghieng ve phia BAN chu khong ve phia TAT: mot cai o hong khong duoc
	# phep lang le go banh khoi web.
	la("ô trống thì đang bán", tat_ban_web.dang_tat("", "2026-08-27"), 0)
	la("ô None thì đang bán", tat_ban_web.dang_tat(None, "2026-08-27"), 0)
	la("ngày hỏng định dạng thì đang bán",
		tat_ban_web.dang_tat("khong-phai-ngay", "2026-08-27"), 0)
	la("ngày đã qua thì đang bán lại",
		tat_ban_web.dang_tat("2026-08-26", "2026-08-27"), 0)


@ca("tắt bán web: tắt đến hết ngày nào thì hết ngày đó, sáng hôm sau tự bán lại")
def _():
	la("đúng ngày đó vẫn đang tắt",
		tat_ban_web.dang_tat("2026-08-27", "2026-08-27"), 1)
	la("ngày sau thì bán lại", tat_ban_web.dang_tat("2026-08-27", "2026-08-28"), 0)
	la("tắt trước nhiều ngày thì vẫn tắt",
		tat_ban_web.dang_tat("2026-09-05", "2026-08-27"), 1)


@ca("tắt bán web: lưu một CÁI NGÀY chứ không phải một ô có / không")
def _():
	src = _py("tat_ban_web.py")
	dung("ô là kiểu Ngày", '"fieldtype": "Date"' in src)
	dung("tên ô nói rõ đến hết ngày", 'custom_tat_ban_web_den' in src)
	# Mot o co / khong thi tat xong tat mai, hom sau bep lam duoc ma web van
	# khong hien, va khong ai nho ra la hom kia co nguoi bam tat.
	dung("có ghi vết ai tắt mã nào đến bao giờ", "def _ghi_vet(ma, den):" in src)
	dung("không cho đặt ngày đã qua", "Ngày tắt bán đã qua rồi" in src)


@ca("tắt bán web: web không hiện mã đang tắt, nhưng BẢNG vẫn hiện đủ số thật")
def _():
	kb = _py("kiem_banh.py")
	i_dem = kb.find('dong = [\n\t\td for d in doc.dong\n\t\tif (d.co_the_ban or 0) > 0')
	i_loc = kb.find("dong = [d for d in dong if not (tat.get(d.ma_hang) or {}).get(\"tat\")]")
	dung("web có lọc mã đang tắt", i_loc > 0)
	dung("lọc SAU phép đếm, không sửa số của bảng", i_dem > 0 and i_loc > i_dem)
	dung("bảng vẫn gửi trạng thái tắt lên màn", '"tat_web": (tat.get(d.ma_hang)' in kb)


@ca("tắt bán web: một công tắc dùng chung cho cả hai màn kiểm bánh")
def _():
	kb = _py("kiem_banh.py")
	mv = _py("mua_vu.py")
	dung("kiểm bánh hằng ngày dùng", "from vagabond import pancake_nhip, tat_ban_web" in kb)
	dung("kiểm mùa vụ dùng", "from vagabond import pancake_nhip, tat_ban_web" in mv)
	dung("mùa vụ chỉ bày trạng thái, không đụng phép đếm",
		'x["tat_web"] = g.get("tat", 0)' in mv)
	# Phep that chi nam o MOT cho, hai man goi vao do.
	dung("kiểm bánh chỉ là cửa vào", "return tat_ban_web.dat(" in kb)


@ca("tắt bán web: hai màn đều nói rõ ngày bán lại, không chỉ nói đang tắt")
def _():
	kbjs = _js("trang/kiem-banh.js")
	dung("kiểm bánh có nút", "function nutWeb(d)" in kbjs)
	dung("kiểm bánh nói ngày bán lại", "đến hết " in kbjs)
	dung("kiểm bánh hỏi trước khi tắt", "Tạm ngừng bán " in kbjs)
	mvjs = _js("public/js/bep/11-khach-ca-hop-dong.js")
	dung("mùa vụ có nút", "function mvNutWeb(x)" in mvjs)
	dung("mùa vụ hỏi trước khi tắt", "Tạm ngừng bán trên web" in mvjs)
	dung("mùa vụ nói sang hôm sau tự bán lại", "Sang ngày hôm sau tự bán lại" in mvjs)
