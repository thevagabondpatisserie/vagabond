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


@ca("#193 chặn tờ có địa chỉ mà không có tên và mã số thuế")
def _chan_thieu_chu():
	s = _py("ban_hang.py")
	dung("có hàm chặn", "def _chan_dia_chi_khong_chu(" in s)
	i = s.index("def _chan_dia_chi_khong_chu(")
	than = s[i:s.index("\n@frappe.whitelist()", i)]
	dung("có địa chỉ mới xét", 'if not (dia_chi or "").strip():' in than)
	dung("có mã số thuế thì cho qua", 'if (so_mst or "").strip():' in than)
	dung("tên thật thì cho qua", "!= XHD_MAC_DINH" in than)
	dung("ném ra màn", "frappe.throw(" in than)
	# Hai cửa NGƯỜI GÕ phải gọi hàm chặn: `luu_xhd` của màn Doanh số sales và
	# `xhd_khach_luu` của trang /xhd khách tự điền. Hai nguồn tự động thì
	# không cần, vì chúng luôn đi kèm mã số thuế.
	#
	# Đếm theo dòng có THỤT ĐẦU, để không đếm nhầm chính dòng `def`.
	la("hai cửa gọi hàm chặn",
		s.count("\n\t_chan_dia_chi_khong_chu(ten"), 2)


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
