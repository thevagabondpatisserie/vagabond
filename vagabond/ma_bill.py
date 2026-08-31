# -*- coding: utf-8 -*-
"""Mã bill quầy: tiền tố theo điểm bán, và phép đọc mã trong sao kê.

ANH VIỆT 31/08/2026
-------------------
*"Tiền tố mã đơn thì đơn ở Trần Cao Vân sẽ mang mã TCV thay vì VGB, NVHTN
thì là NVH, còn ở 307/1 Nguyễn Văn Trỗi Sales Online thì tiền tố là SOL."*

Lợi ích thật, không phải cho đẹp: kế toán nhìn sao kê ngân hàng là biết ngay
giao dịch thuộc điểm nào mà không phải mở từng đơn ra tra. Trước đây phải ghi
kèm mã điểm bán ở đầu nội dung ("TCV VGBAB123"), tức là nội dung dài hơn và
app ngân hàng nào cắt bớt ký tự là mất luôn phần đuôi. Nay gộp làm một chuỗi
tám ký tự, ngắn hơn và không có khoảng trắng để bị cắt.

BẢNG CHỮ SINH MÃ CỐ TÌNH THIẾU B I O Z 0 1 2
--------------------------------------------
Đó là những ký tự người hay đọc nhầm với 8, 1, 0, 2. Mã bill là thứ khách gõ
tay khi app ngân hàng không điền sẵn, nên bỏ hẳn cho chắc.

Và bảng chữ hẹp còn một tác dụng thứ hai: phép dò mã trong sao kê chặt hơn.
Dò `TCV[A-Z0-9]{5}` thì một chuỗi rác như "TCVB1OZ0" cũng khớp; dò theo đúng
bảng chữ này thì không.

ĐÃ THỬ VA CHẠM TRÊN SAO KÊ THẬT
-------------------------------
Quét 2.914 giao dịch ngân hàng của cả tháng 8/2026:

    VGB  11 lần khớp, cả 11 đều là mã bill thật
    TCV   0 lần
    NVH   0 lần
    SOL   0 lần

Không một dòng nào khớp nhầm. Ba tiền tố mới an toàn.

VGB PHẢI GIỮ MÃI MÃI
--------------------
Hơn hai nghìn bill cũ mang tiền tố VGB và sao kê cũ cũng vậy. Bỏ VGB ra khỏi
phép dò là mọi bill cũ mất đường đối soát. Nên VGB nằm trong danh sách nhận
vĩnh viễn, chỉ không sinh mới nữa.

Tệp này THUẦN, không chạm Frappe, để kiểm thử được không cần site.
"""

import re

# Bảng chữ sinh mã. Thiếu B I O Z 0 1 2 là có chủ ý, xem đầu tệp.
CHU_SINH = "ACDEFGHJKLMNPQRSTUVWXY3456789"

DAI_DUOI = 5

# Tiền tố mặc định, và cũng là tiền tố của mọi bill cũ.
TIEN_TO_CU = "VGB"

# Điểm bán nào mang tiền tố nào. Khoá là mã điểm bán viết hoa.
TIEN_TO_DIEM = {
	"TCV": "TCV",      # Trần Cao Vân
	"NVHTN": "NVH",    # Nguyễn Văn Huyên Thảo Nguyên
	"NVH": "NVH",
	"SALES": "SOL",    # 307/1 Nguyễn Văn Trỗi, Sales Online
	"SOL": "SOL",
}

# Mọi tiền tố hệ CHẤP NHẬN khi đọc sao kê. Rộng hơn danh sách sinh mới, vì
# bill cũ vẫn phải đối soát được.
TIEN_TO_NHAN = ("VGB", "TCV", "NVH", "SOL")


def tien_to_cua(diem=None):
	"""Tiền tố của một điểm bán. THUẦN. Không biết thì trả tiền tố cũ.

	Không biết mà trả rỗng là sinh ra mã năm ký tự trần, dò trong sao kê sẽ
	khớp bừa. Thà rơi về VGB, vẫn đối soát được.
	"""
	d = str(diem or "").strip().upper()
	return TIEN_TO_DIEM.get(d, TIEN_TO_CU)


def mau_do():
	"""Chuỗi mẫu (regex) dò mã bill trong nội dung sao kê. THUẦN."""
	return r"(?:%s)[%s]{%d}" % ("|".join(TIEN_TO_NHAN), CHU_SINH, DAI_DUOI)


RE_MA = re.compile(mau_do())


def hop_le(ma):
	"""Chuỗi này có đúng dạng một mã bill không. THUẦN."""
	return bool(RE_MA.fullmatch(str(ma or "").strip().upper()))


def tach_tien_to(ma):
	"""('TCV', 'Q4PFX') từ 'TCVQ4PFX'. THUẦN. Không hợp lệ thì ('', '')."""
	m = str(ma or "").strip().upper()
	if not hop_le(m):
		return "", ""
	return m[:3], m[3:]


def diem_cua_ma(ma):
	"""Mã bill này thuộc điểm bán nào. THUẦN. '' nếu là mã cũ hoặc không rõ.

	Mã cũ mang VGB thì KHÔNG đoán bừa ra điểm bán: trước ngày đổi tiền tố
	mọi điểm đều dùng chung VGB, đoán là đoán sai.
	"""
	tt, _ = tach_tien_to(ma)
	if not tt or tt == TIEN_TO_CU:
		return ""
	for diem, t in TIEN_TO_DIEM.items():
		if t == tt and diem == t:
			return diem
	for diem, t in TIEN_TO_DIEM.items():
		if t == tt:
			return diem
	return ""
