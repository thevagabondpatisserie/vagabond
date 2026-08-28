# -*- coding: utf-8 -*-
"""Gom năm nhãn chặng về hai tên, và màn tồn kho theo chặng (28/08/2026).

Khải gom năm nhãn đang dùng còn hai tên cho phần bán thành phẩm:

    BTP thành phần + Ruột bánh (C1)  ->  BTP sơ cấp
    Bánh khuôn (C2)                  ->  BTP sẵn sàng

Nguyên liệu và Thành phẩm giữ nguyên vì không phải bán thành phẩm.

Ca kiểm ở đây canh ba thứ dễ hỏng nhất:

1. Bảng dịch nhãn phải nhận CẢ BA dạng đang có trong hệ - nhãn cũ trên
   công thức, mã chặng trong ô khai tay, và tên mới - vì ba dạng đó đang
   nằm lẫn nhau trong dữ liệu thật.
2. Nhãn lạ phải trả về rỗng chứ không đoán bừa. Đoán bừa là xếp món vào
   chặng sai, mà chặng sai thì lệnh sản xuất lấy sai kho.
3. Bảng đếm phải luôn đủ bốn chặng kể cả chặng không có mã nào. Chip biến
   mất thì người xem tưởng mình lọc nhầm chứ không nghĩ là hết hàng thật.
"""

import io
import os

from vagabond import kho_san_xuat as k
from vagabond import ton_chang as tc
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _py(ten):
	goc = os.path.dirname(os.path.abspath(k.__file__))
	return io.open(os.path.join(goc, ten), encoding="utf-8").read()


# ------------------------------------------------------- bảng dịch nhãn


@ca("BTP thành phần và Ruột bánh C1 cùng về BTP sơ cấp")
def _():
	la("BTP thành phần", tc.chang_cua_nhan("BTP thành phần"), k.BTP_SO_CAP)
	la("Ruột bánh (C1)", tc.chang_cua_nhan("Ruột bánh (C1)"), k.BTP_SO_CAP)
	la("không dấu ngoặc", tc.chang_cua_nhan("Ruột bánh C1"), k.BTP_SO_CAP)


@ca("Bánh khuôn C2 về BTP sẵn sàng, một mình")
def _():
	la("Bánh khuôn (C2)", tc.chang_cua_nhan("Bánh khuôn (C2)"), k.BTP_SAN_SANG)
	la("không dấu ngoặc", tc.chang_cua_nhan("Bánh khuôn C2"), k.BTP_SAN_SANG)


@ca("Nguyên liệu và Thành phẩm KHÔNG bị gom vào hai tên BTP")
def _():
	# Gom nốt hai cái này thì không còn cách nào phân biệt hàng bán được
	# với hàng đang làm dở.
	la("nguyên liệu", tc.chang_cua_nhan("Nguyên liệu"), k.NGUYEN_LIEU)
	la("thành phẩm", tc.chang_cua_nhan("Thành phẩm"), k.THANH_PHAM)


@ca("nhận cả mã chặng và tên mới, không chỉ nhãn cũ")
def _():
	la("mã chặng", tc.chang_cua_nhan("btp_san_sang"), k.BTP_SAN_SANG)
	la("tên mới", tc.chang_cua_nhan("BTP sơ cấp"), k.BTP_SO_CAP)
	la("tên mới khác hoa thường", tc.chang_cua_nhan("btp sẵn sàng"), k.BTP_SAN_SANG)


@ca("thừa khoảng trắng hay xuống dòng vẫn tra ra đúng chặng")
def _():
	la("thừa hai đầu", tc.chang_cua_nhan("  Bánh khuôn (C2)  "), k.BTP_SAN_SANG)
	la("thừa ở giữa", tc.chang_cua_nhan("BTP  thành   phần"), k.BTP_SO_CAP)


@ca("nhãn lạ trả về rỗng, KHÔNG đoán bừa")
def _():
	la("chuỗi lạ", tc.chang_cua_nhan("Bánh mì"), "")
	la("rỗng", tc.chang_cua_nhan(""), "")
	la("None", tc.chang_cua_nhan(None), "")


@ca("chặng Sơ chế đã ngừng dùng vẫn đọc ra được, bản công thức cũ còn giữ")
def _():
	la("sơ chế", tc.chang_cua_nhan("Sơ chế"), k.BTP_SO_CAP)


@ca("tên hiện lên màn hình lấy từ kho_san_xuat, không chép lại")
def _():
	for ma in tc.THU_TU:
		la("tên %s" % ma, tc.ten_chang(ma), k.TEN_CHANG[ma])
	la("mã lạ nói thẳng là chưa rõ", tc.ten_chang("linh tinh"), "Chưa phân chặng")


@ca("thứ tự chip đúng chiều đi lên của dây chuyền")
def _():
	la("thứ tự", list(tc.THU_TU),
		[k.NGUYEN_LIEU, k.BTP_SO_CAP, k.BTP_SAN_SANG, k.THANH_PHAM])


@ca("mỗi chặng đều có chữ chip và màu, không chặng nào rơi ra ngoài")
def _():
	for ma in tc.THU_TU:
		dung("chip %s" % ma, bool(tc.CHIP.get(ma)))
		dung("màu %s" % ma, tc.MAU.get(ma) in ("n", "w", "g"))


# ---------------------------------------------------------- bảng gom đếm


DS = [
	{"ma": "BTPB00001", "chang": "btp_so_cap", "sl": 10},
	{"ma": "BTPB00002", "chang": "btp_so_cap", "sl": 5},
	{"ma": "NBTP00003", "chang": "btp_san_sang", "sl": 2},
	{"ma": "NVLT00004", "chang": "nguyen_lieu", "sl": 100},
	{"ma": "LA00005", "chang": "", "sl": 7},
]


@ca("bảng đếm luôn đủ bốn chặng kể cả chặng không có mã nào")
def _():
	b = tc.gop_dong(DS)
	for ma in tc.THU_TU:
		dung("phải có chặng %s" % ma, ma in b)
	la("thành phẩm rỗng vẫn có mặt", b[k.THANH_PHAM]["so_ma"], 0)


@ca("đếm đúng số mã và cộng đúng tổng từng chặng")
def _():
	b = tc.gop_dong(DS)
	la("sơ cấp số mã", b[k.BTP_SO_CAP]["so_ma"], 2)
	la("sơ cấp tổng", b[k.BTP_SO_CAP]["tong"], 15.0)
	la("sẵn sàng số mã", b[k.BTP_SAN_SANG]["so_ma"], 1)
	la("nguyên liệu tổng", b[k.NGUYEN_LIEU]["tong"], 100.0)


@ca("mã chưa phân chặng gom riêng, không nhét vào chặng nào")
def _():
	b = tc.gop_dong(DS)
	la("chưa phân chặng", b[""]["so_ma"], 1)


@ca("bảng rỗng vẫn trả về đủ bốn chặng với số 0")
def _():
	b = tc.gop_dong([])
	la("số chặng", len([x for x in tc.THU_TU if x in b]), 4)
	la("sơ cấp", b[k.BTP_SO_CAP]["so_ma"], 0)


# --------------------------------------------------------------- bộ lọc


@ca("lọc theo chặng lấy đúng nhóm đó")
def _():
	la("sơ cấp", len(tc.loc_theo_chang(DS, k.BTP_SO_CAP)), 2)
	la("sẵn sàng", len(tc.loc_theo_chang(DS, k.BTP_SAN_SANG)), 1)
	la("thành phẩm", len(tc.loc_theo_chang(DS, k.THANH_PHAM)), 0)


@ca("chặng rỗng nghĩa là lấy hết, không phải lấy nhóm chưa phân chặng")
def _():
	la("rỗng", len(tc.loc_theo_chang(DS, "")), len(DS))
	la("None", len(tc.loc_theo_chang(DS, None)), len(DS))


@ca("chip Chưa phân chặng có khoá riêng, không dùng chung chuỗi rỗng")
def _():
	# Dùng chung thì bấm vào chip lại ra cả danh sách.
	dung("khoá riêng", tc.CHUA_PHAN not in ("",) + tuple(tc.THU_TU))
	r = tc.loc_theo_chang(DS, tc.CHUA_PHAN)
	la("chỉ lấy mã chưa phân chặng", len(r), 1)
	la("đúng mã đó", r[0]["ma"], "LA00005")


@ca("lọc không sửa danh sách gốc")
def _():
	tc.loc_theo_chang(DS, k.BTP_SO_CAP)
	la("gốc còn nguyên", len(DS), 5)


# ------------------------------------------------------------- câu tóm tắt


@ca("câu tóm tắt nói đủ từng chặng có hàng, và cả phần chưa phân chặng")
def _():
	c = tc.cau_tom_tat(tc.gop_dong(DS))
	dung("có sơ cấp", "BTP sơ cấp 2 mã" in c)
	dung("có sẵn sàng", "BTP sẵn sàng 1 mã" in c)
	dung("có phần chưa phân", "chưa phân chặng 1 mã" in c)
	dung("không nhắc chặng rỗng hàng", "Thành phẩm" not in c)


@ca("không có gì thì nói thẳng, không trả câu rỗng")
def _():
	c = tc.cau_tom_tat(tc.gop_dong([]))
	dung("phải nói rõ", "Không có mã nào" in c)


# ------------------------------------------------ hàng rào của phần ghi


@ca("hàm gom nhãn xuống dữ liệu chạy thử là mặc định")
def _():
	m = _py("ton_chang.py")
	dung("mặc định chạy thử", "def gom_chang(chay_that=0)" in m)
	doan = m.split("def gom_chang")[1]
	dung("chỉ ghi khi được lệnh", "if chay_that:" in doan)
	dung("phải chặn quyền", "frappe.throw" in doan)


@ca("hàm gom nhãn phải cảnh báo trước là ghi xong sẽ mất dấu C1")
def _():
	# phantom.py đang đọc đúng chỗ này để biết mã nào được bỏ tồn kho.
	m = _py("ton_chang.py")
	doan = m.split("def gom_chang")[1]
	dung("phải đếm số mã mất dấu", "mat_dau" in doan)
	dung("phải nói ra trong câu ghi chú", "mất " in doan)


@ca("màn tồn kho theo chặng chỉ ĐỌC, không ghi gì")
def _():
	m = _py("ton_chang.py")
	doan = m.split("def ton_theo_chang")[1].split("\n@frappe")[0]
	la("không được ghi", "set_value" in doan, False)
	la("không được commit", "db.commit" in doan, False)


@ca("màn bỏ qua kho đã tắt, không cộng tồn của kho nằm im")
def _():
	m = _py("ton_chang.py")
	doan = m.split("def kho_cua_bep")[1].split("\ndef ")[0]
	dung("phải kiểm cờ disabled", '"disabled"' in doan)


# ------------------------------------------------------- phía màn hình


def _js(ten):
	goc = os.path.dirname(os.path.abspath(k.__file__))
	return io.open(os.path.join(goc, "public", "js", "bep", ten),
		encoding="utf-8").read()


@ca("chip chặng trên màn Công thức chỉ còn bốn tên, không chia kiểu cũ")
def _():
	m = _js("26-cong-thuc.js")
	bang = m.split("var CT_CHANG = [")[1].split("];")[0]
	for t in ("Nguyên liệu", "BTP sơ cấp", "BTP sẵn sàng", "Thành phẩm"):
		dung("phải có chip %s" % t, t in bang)
	for t in ("BTP thành phần", "Ruột bánh", "Bánh khuôn", "C1", "C2"):
		la("không được còn nhãn cũ %s" % t, t in bang, False)


@ca("chip chặng lọc tại máy chủ, không lọc tại máy khách")
def _():
	# Lọc tại máy khách thì con số trên chip đếm theo 1200 dòng đã tải chứ
	# không theo cả tiệm, và bếp trưởng đọc ra số sai.
	m = _js("26-cong-thuc.js")
	dung("phải gửi mã chặng đi", "chang: ctD.cg || null" in m)


@ca("màn Tồn kho theo chặng không tự dịch nhãn, để máy chủ dịch")
def _():
	# Hai bảng dịch ở hai nơi thì sáng mai lệch nhau, mà lúc lệch không ai
	# biết bên nào đúng.
	m = _js("37-ton-chang.js")
	for t in ("BTP thành phần", "Ruột bánh", "Bánh khuôn"):
		la("không được chép nhãn cũ %s" % t, t in m, False)
	dung("tên chặng đọc từ máy chủ", "d.ten_chang" in m)
	dung("thứ tự chip đọc từ máy chủ", "d.thu_tu" in m)


@ca("chip chặng rỗng hàng vẫn hiện với số 0, không bị giấu đi")
def _():
	# Chip biến mất thì người xem tưởng mình lọc nhầm.
	m = _js("37-ton-chang.js")
	doan = m.split("var chips =")[1].split(";")[0]
	la("không được lọc bỏ chặng rỗng", "so_ma ?" in doan, False)
	dung("vẽ đủ theo thứ tự máy chủ trả về", "d.thu_tu || []" in doan)


@ca("màn Tồn kho theo chặng đã nối vào bảng đường dẫn và trang chủ")
def _():
	m = _js("02-trang-chu.js")
	dung("có ô trên trang chủ", "'TONCHANG'" in m)
	dung("có nhánh mở màn", "if (k === 'TONCHANG') return go(scrTonChang);" in m)
	dung("có địa chỉ riêng", "'ton-kho-theo-chang': 'TONCHANG'" in m)
