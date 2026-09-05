# -*- coding: utf-8 -*-
"""Ô địa chỉ trên hoá đơn nuốt cả nhãn "Địa chỉ:" (Issue #193, 05/09/2026).

Chị Dung phát hiện trên một tờ hoá đơn đã phát hành: ô địa chỉ người mua bắt
đầu bằng chính cái nhãn thay vì bằng địa chỉ.

    Địa chỉ (Address): - Địa chỉ: Tầng Trệt Phoenix 1A, 547-549 đường Tạ
    Quang Bửu, Phường Chánh Hưng, Thành phố Hồ Chí Minh, Việt Nam

Rà trên site ngày 05/09/2026 thấy năm tờ dính, với ba dạng tiền tố khác nhau,
tức là copy nguyên một dòng gạch đầu dòng từ khối thông tin khách gửi qua
Pancake chứ không phải máy ghép sai.

Bộ ca này chốt hai thứ: phép làm sạch bóc đúng cái phải bóc và KHÔNG bóc cái
không được bóc, và mọi đường ghi vào ô đó đều đi qua phép làm sạch.
"""

import io
import os

from vagabond import hoa_don_vat as hdv
from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


def _js(ten):
	return io.open(
		os.path.join(GOI, "public", "js", "bep", ten), encoding="utf-8").read()


# Năm chuỗi THẬT lấy từ site ngày 05/09/2026. Giữ nguyên từng ký tự, kể cả
# chỗ thiếu khoảng trắng sau dấu hai chấm và chỗ thừa khoảng trắng trước nó.
THAT = (
	(
		"- Địa chỉ: Tầng Trệt Phoenix 1A, 547-549 đường Tạ Quang Bửu, "
		"Phường Chánh Hưng, Thành phố Hồ Chí Minh, Việt Nam",
		"Tầng Trệt Phoenix 1A, 547-549 đường Tạ Quang Bửu, "
		"Phường Chánh Hưng, Thành phố Hồ Chí Minh, Việt Nam",
	),
	(
		"+ Địa chỉ :Tầng 10, Sofic Tower, Số 10 Đường Mai Chí Thọ, "
		"Phường An Khánh, Thành phố Hồ Chí Minh, Việt Nam",
		"Tầng 10, Sofic Tower, Số 10 Đường Mai Chí Thọ, "
		"Phường An Khánh, Thành phố Hồ Chí Minh, Việt Nam",
	),
	(
		"- Địa chỉ : 138/22 Trương Công Định, Phường Tân Bình, "
		"Thành phố Hồ Chí Minh, Việt Nam",
		"138/22 Trương Công Định, Phường Tân Bình, "
		"Thành phố Hồ Chí Minh, Việt Nam",
	),
	(
		"- Địa chỉ: Tầng 7, Cao ốc Đại Minh Convention, Số 77 Hoàng Văn Thái, "
		"Phường Tân Mỹ, Thành phố Hồ Chí Minh, Việt Nam.",
		"Tầng 7, Cao ốc Đại Minh Convention, Số 77 Hoàng Văn Thái, "
		"Phường Tân Mỹ, Thành phố Hồ Chí Minh, Việt Nam.",
	),
)

# Những chuỗi TUYỆT ĐỐI không được đụng tới. Bóc nhầm ở đây là ăn mất một
# phần địa chỉ thật, mà địa chỉ sai trên hoá đơn thì cũng hỏng y như cũ.
GIU_NGUYEN = (
	"9 Trần Cao Vân, Phường Sài Gòn, Thành phố Hồ Chí Minh, Việt Nam",
	"138/22 Trương Công Định, Phường Tân Bình",
	"Tầng 10, Sofic Tower, Số 10 Đường Mai Chí Thọ",
	# Dấu hai chấm nằm GIỮA địa chỉ thật, không phải nhãn.
	"Lô A: 12 Nguyễn Văn Cừ, Quận 5",
	# Chữ "địa chỉ" nằm giữa câu, không phải ở đầu.
	"12 Trần Hưng Đạo, gần địa chỉ cũ",
	# Số nhà có dấu gạch nhưng không phải gạch đầu dòng.
	"547-549 đường Tạ Quang Bửu",
)


@ca("#193 bóc đúng cả năm dạng tiền tố thật trên site")
def _boc_that():
	for vao, mong in THAT:
		la("bóc %r" % vao[:28], hdv.sach_dia_chi_xhd(vao), mong)


@ca("#193 không đụng vào địa chỉ thật, kể cả khi có dấu hai chấm ở giữa")
def _giu_nguyen():
	for x in GIU_NGUYEN:
		la("giữ %r" % x[:28], hdv.sach_dia_chi_xhd(x), x)


@ca("#193 các dạng nhãn khác cũng bóc được, không cần gạch đầu dòng")
def _nhan_khac():
	la("nhãn trần", hdv.sach_dia_chi_xhd("Địa chỉ: 5 Lê Lợi"), "5 Lê Lợi")
	la("viết tắt", hdv.sach_dia_chi_xhd("ĐC: 5 Lê Lợi"), "5 Lê Lợi")
	la("tiếng Anh", hdv.sach_dia_chi_xhd("Address: 5 Le Loi"), "5 Le Loi")
	la("không dấu", hdv.sach_dia_chi_xhd("Dia chi: 5 Le Loi"), "5 Le Loi")
	la("chấm tròn", hdv.sach_dia_chi_xhd("• Địa chỉ: 5 Lê Lợi"), "5 Lê Lợi")


@ca("#193 chuỗi rỗng, None, và chuỗi toàn dấu gạch đều ra rỗng, không treo")
def _bien():
	la("None", hdv.sach_dia_chi_xhd(None), "")
	la("rỗng", hdv.sach_dia_chi_xhd(""), "")
	la("khoảng trắng", hdv.sach_dia_chi_xhd("   "), "")
	la("toàn gạch", hdv.sach_dia_chi_xhd("- - -"), "")
	la("chỉ có nhãn", hdv.sach_dia_chi_xhd("- Địa chỉ:"), "")


@ca("#193 chỉ chạy tối đa hai lượt bóc, nhãn xếp sâu hơn thì giữ nguyên")
def _hai_lop():
	# Một lượt bóc được cả cụm gạch đầu dòng LẪN một nhãn, nên hai thứ đó
	# nằm cạnh nhau là sạch ngay trong lượt đầu.
	la("gạch rồi nhãn", hdv.sach_dia_chi_xhd("- Địa chỉ: 5 Lê Lợi"), "5 Lê Lợi")
	la("gạch, nhãn, nhãn",
		hdv.sach_dia_chi_xhd("- Địa chỉ: Địa chỉ: 5 Lê Lợi"), "5 Lê Lợi")
	# Ba nhãn chồng nhau thì lượt thứ ba không chạy, còn lại một nhãn. Đó là
	# ý muốn chứ không phải thiếu sót: bóc vô hạn là mở đường cho việc ăn mất
	# phần đầu của một địa chỉ lạ mà mình chưa lường tới.
	dung("ba nhãn thì còn lại một",
		hdv.sach_dia_chi_xhd("Địa chỉ: Địa chỉ: Địa chỉ: 5 Lê Lợi")
		== "Địa chỉ: 5 Lê Lợi")


@ca("#193 nhãn phải nằm gần đầu chuỗi mới được coi là nhãn")
def _xa_thi_thoi():
	dung("có mốc khoảng cách", hdv.XA_NHAT_CUA_NHAN == 24)
	x = "Toa nha van phong so 12 duong Nguyen Trai: 5 Le Loi"
	la("dấu hai chấm ở xa thì giữ nguyên", hdv.sach_dia_chi_xhd(x), x)


@ca("#193 hoa_don_vat vẫn THUẦN, không kéo Frappe vào")
def _van_thuan():
	s = _py("hoa_don_vat.py")
	la("không import frappe", "import frappe" in s, False)
	# Tệp này không được chứa dấu gạch dài, quy ước trình bày của tiệm. Bộ ký
	# tự đầu dòng vì thế phải viết bằng mã escape.
	dung("bộ ký tự đầu dòng viết bằng mã escape", '\\u2022' in s)


@ca("#193 MỌI đường ghi vào ô địa chỉ đều đi qua phép làm sạch")
def _moi_duong_deu_sach():
	s = _py("ban_hang.py")
	# Sáu chỗ gán: hai nguồn tự động (Vagabond Hoa Don, VietQR) và bốn cửa
	# người gõ (luu_xhd, tao_don_tay, pos_sua_don, xhd_khach_luu).
	la("sáu chỗ gọi phép làm sạch", s.count("hoa_don_vat.sach_dia_chi_xhd("), 6)
	# Không còn chỗ nào chỉ strip rồi ghi thẳng.
	for xau in (
		'"vgb_xhd_dia_chi": (dia_chi or "").strip()',
		'si.vgb_xhd_dia_chi = (xhd_dia_chi or "").strip()',
		'"vgb_xhd_dia_chi": hd.dia_chi or ""',
		'"vgb_xhd_dia_chi": tt.get("dia_chi") or ""',
	):
		la("không còn %s" % xau[:34], xau in s, False)


# Câu mặc định của ô tên người mua. Chép nguyên văn từ `ban_hang.XHD_MAC_DINH`
# chứ không import, để bộ ca này chạy được mà không cần Frappe.
TEN_MAC_DINH = "Bán cho người tiêu dùng"


@ca("#193 luật địa chỉ không có chủ: kiểm HÀNH VI, không dò chuỗi")
def _luat_dia_chi_khong_chu():
	f = hdv.dia_chi_khong_chu
	# Năm ca Codex yêu cầu trong review PR #194.
	dung("địa chỉ + tên mặc định + không MST thì CHẶN",
		f(TEN_MAC_DINH, "", "5 Lê Lợi", TEN_MAC_DINH) is True)
	dung("địa chỉ + tên thật + không MST thì CHO QUA",
		f("Nguyễn Văn A", "", "5 Lê Lợi", TEN_MAC_DINH) is False)
	dung("địa chỉ + MST + tên hợp lệ thì CHO QUA",
		f("CÔNG TY TNHH IMAE", "0301464830", "5 Lê Lợi", TEN_MAC_DINH) is False)
	dung("không có địa chỉ thì CHO QUA",
		f(TEN_MAC_DINH, "", "", TEN_MAC_DINH) is False)
	dung("địa chỉ toàn khoảng trắng cũng coi như không có",
		f(TEN_MAC_DINH, "", "   ", TEN_MAC_DINH) is False)
	# Vài ca biên nữa.
	dung("tên rỗng cũng tính là chưa có chủ",
		f("", "", "5 Lê Lợi", TEN_MAC_DINH) is True)
	dung("tên mặc định có khoảng trắng thừa vẫn nhận ra",
		f("  " + TEN_MAC_DINH + " ", "", "5 Lê Lợi", TEN_MAC_DINH) is True)
	dung("có MST thì tên mặc định cũng cho qua, cửa tên đã chặn ở chỗ khác",
		f(TEN_MAC_DINH, "0301464830", "5 Lê Lợi", TEN_MAC_DINH) is False)
	dung("None ở mọi ô không làm nổ",
		f(None, None, None, TEN_MAC_DINH) is False)


@ca("#193 mọi cửa ghi đều thực thi luật, mỗi cửa một cách phù hợp")
def _moi_cua_thuc_thi():
	s = _py("ban_hang.py")
	# Hàm ném ra màn phải gọi phép THUẦN chứ không tự chép lại luật.
	i = s.index("def _chan_dia_chi_khong_chu(")
	than = s[i:s.index("\n@frappe.whitelist()", i)]
	dung("hàm chặn gọi phép thuần", "hoa_don_vat.dia_chi_khong_chu(" in than)
	dung("hàm chặn ném ra màn", "frappe.throw(" in than)
	# Hai cửa NGƯỜI GÕ thì ném lỗi: người đang ngồi đó, sửa được ngay.
	la("hai cửa người gõ gọi hàm chặn",
		s.count("\n\t_chan_dia_chi_khong_chu(ten"), 2)
	# Cửa POS thì KHÔNG ném, mà bỏ qua lần ghi địa chỉ. Ném ở đây là chặn
	# luôn việc sửa món, sửa tiền của những tờ cũ đã lỡ mang tổ hợp sai.
	dung("cửa POS cũng thực thi luật",
		"if not hoa_don_vat.dia_chi_khong_chu(" in s)
	dung("cửa POS không ném lỗi mà bỏ qua lần ghi",
		"si.vgb_xhd_dia_chi = _moi" in s)


@ca("#193 lời nhắn khớp với luật, không đòi cá nhân phải có mã số thuế")
def _loi_nhan_khop_luat():
	s = _py("ban_hang.py")
	i = s.index("def _chan_dia_chi_khong_chu(")
	than = s[i:s.index("\n@frappe.whitelist()", i)]
	# Luật CHO PHÉP khách cá nhân có tên thật mà không có mã số thuế, nên
	# lời nhắn không được nói rằng phải có cả hai.
	dung("lời nhắn nói rõ cá nhân vẫn điền được",
		"không có mã số thuế thì vẫn điền địa chỉ bình thường" in than)
	la("không còn câu đòi cả tên lẫn mã số thuế",
		"phải có tên người mua và mã số thuế" in than, False)


@ca("#193 màn Bill quay không gửi lên địa chỉ mồ côi")
def _man_pos_khong_gui_mo_coi():
	j = _js("10-bill-quay.js")
	# Trước 05/09/2026 màn này bỏ trống ô tên khi tên là câu mặc định nhưng
	# vẫn giữ nguyên ô địa chỉ, nên payload gửi lên đúng tổ hợp bị cấm.
	la("không còn giữ địa chỉ khi bỏ trống tên",
		"mst: d.vgb_xhd_mst || '', dc: d.vgb_xhd_dia_chi || '', email: d.vgb_xhd_email || ''\n      }" in j,
		False)
	dung("bỏ trống tên thì bỏ trống luôn địa chỉ và mã số thuế",
		"return { ten: '', mst: '', dc: '', email: d.vgb_xhd_email || '' };" in j)


@ca("#193 KHÔNG có đường nào tự sửa hoá đơn cũ")
def _khong_sua_qua_khu():
	# Năm tờ đã phát hành và đã gửi cơ quan thuế. Luật anh Việt chốt
	# 13/08/2026: liệt kê cho anh Việt, không tự sửa.
	s = _py("ban_hang.py")
	i = s.index("def _chan_dia_chi_khong_chu(")
	than = s[i:s.index("\n@frappe.whitelist()", i)]
	for xau in ("frappe.db.sql", "set_value", "save(", "for si in", "update"):
		la("hàm chặn không có %s" % xau, xau in than, False)
	s2 = _py("hoa_don_vat.py")
	for xau in ("frappe", "set_value", "sql"):
		la("phép làm sạch không có %s" % xau, xau in s2, False)
