# -*- coding: utf-8 -*-
"""Một tờ hoá đơn đã được trả tới đâu. Dùng chung cho mua vào và bán ra.

VÌ SAO CÓ TỆP NÀY (anh Việt nói 05/09/2026)
-------------------------------------------
Anh xin thêm chip "trạng thái thanh toán" cho cả màn hoá đơn mua lẫn màn
hoá đơn bán: đã thanh toán, còn một phần, và những trạng thái nào em thấy
hợp.

Trước bản này, hai màn đó nói hai giọng khác nhau. Màn hoá đơn mua chỉ
chia được hai mức là đã trả hết hay còn nợ. Màn hoá đơn bán thì không có
gì cả, đúng nhãn mặc định của ERPNext. Cùng một câu hỏi "tờ này trả tới
đâu rồi" mà hai màn trả lời hai kiểu.

VÌ SAO PHẢI TÁCH RIÊNG "TRẢ MỘT PHẦN"
-------------------------------------
Gộp trả một phần vào chung với chưa trả là mất đúng thông tin đáng giá
nhất. Tờ chưa trả đồng nào và tờ đã trả tám phần mười là hai tình huống
khác hẳn nhau khi đi đòi nợ hay khi xếp lịch chi. Nhập chung lại thì kế
toán phải mở từng tờ ra xem, tức là cái chip không tiết kiệm được gì.

VÌ SAO KHÔNG DÙNG THẲNG Ô `status` CỦA ERPNext
----------------------------------------------
ERPNext có sẵn ô đó với các giá trị Paid, Unpaid, Overdue, Partly Paid.
Không dùng vì hai lẽ. Thứ nhất, chữ "Overdue" của ERPNext đọc thẳng hạn
trả, mà 525 nhà cung cấp của tiệm không ai được khai điều khoản thanh
toán nên hạn trả bằng luôn ngày lập, khiến tờ vừa ghi sổ xong đã thành
quá hạn. Bài học này đã ghi ở bản v420 và tệp buoc_hoa_don_mua.py. Thứ
hai, ô đó còn mang lẫn cả trạng thái trả hàng và hoá đơn nội bộ, không
thuần là chuyện tiền.

Nên ở đây tính lại từ SỐ DƯ, và chỉ gọi là quá hạn khi có hạn trả THẬT,
tức hạn đặt sau ngày hạch toán.

TỆP NÀY THUẦN HOÀN TOÀN, không import frappe, để chạy được ở máy kiểm thử
tay không. Phần hiển thị nằm bên màn danh sách.
"""

T_CHUA_GHI = "Chưa ghi sổ"
T_DA_TRA = "Đã thanh toán"
T_MOT_PHAN = "Trả một phần"
T_CHUA_TRA = "Chưa thanh toán"
T_QUA_HAN = "Quá hạn thanh toán"
T_TRA_THUA = "Trả thừa"

DS_TRANG_THAI = [T_CHUA_GHI, T_DA_TRA, T_MOT_PHAN, T_CHUA_TRA, T_QUA_HAN, T_TRA_THUA]

# Dưới một đồng thì coi như bằng không. Tiền Việt không có hào, mọi số lẻ
# nhỏ hơn một đồng đều là rác làm tròn của máy.
LE = 1.0


def _so(x):
	"""Đọc một con số, hỏng thì trả 0. THUẦN."""
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def trang_thai_tra(tong, con_lai, ghi_so=1, ngay_hach_toan="", han_tra="", hom_nay=""):
	"""Tờ này đã trả tới đâu. THUẦN.

	`tong` là tổng tiền của tờ, `con_lai` là số dư chưa thanh toán.
	`ghi_so` là tờ đã ghi sổ chưa (docstatus 1).

	Thứ tự xét có lý do:

	  1. Tờ chưa ghi sổ thì chưa phát sinh công nợ, nên mọi câu chuyện trả
	     tiền đều chưa bắt đầu. Nói nó "chưa thanh toán" là nói thừa và
	     gây hiểu nhầm rằng có ai đó đang nợ.
	  2. Trả hết xét trước, vì đó là đích của mọi tờ.
	  3. Quá hạn xét trước trả một phần và chưa trả, vì quá hạn là việc
	     gấp hơn, cần nổi lên trên.
	  4. Cuối cùng mới phân biệt đã trả được một phần hay chưa đồng nào.
	"""
	if not ghi_so:
		return T_CHUA_GHI

	t = _so(tong)
	c = _so(con_lai)

	if c < -LE:
		return T_TRA_THUA
	if abs(c) < LE:
		return T_DA_TRA

	if qua_han(ngay_hach_toan, han_tra, hom_nay):
		return T_QUA_HAN

	# Còn nợ đúng bằng tổng tờ nghĩa là chưa ai trả đồng nào.
	if t > 0 and abs(c - t) < LE:
		return T_CHUA_TRA
	if t <= 0:
		return T_CHUA_TRA
	return T_MOT_PHAN


def qua_han(ngay_hach_toan, han_tra, hom_nay):
	"""Tờ này có thật sự quá hạn không. THUẦN.

	Hai điều kiện, phải đủ cả hai:

	  1. Có hạn trả THẬT, tức hạn đặt SAU ngày hạch toán. Hạn bằng đúng
	     ngày lập nghĩa là chưa ai khai điều khoản thanh toán cho đối tác
	     đó, gọi là quá hạn là vu oan cho họ.
	  2. Hạn đó đã trôi qua so với hôm nay.

	Thiếu bất kỳ ngày nào trong ba ngày thì không kết luận. Không biết thì
	không được phép nói là quá hạn.
	"""
	a = str(ngay_hach_toan or "").strip()
	b = str(han_tra or "").strip()
	n = str(hom_nay or "").strip()
	if not a or not b or not n:
		return False
	if not b > a:
		return False
	return b < n


def mau_cua_trang_thai(tt):
	"""Màu của một trạng thái trên màn danh sách. THUẦN.

	Chỉ quá hạn mới được màu đỏ. Chưa thanh toán là chuyện bình thường của
	mọi tờ vừa ghi sổ, tô đỏ hết thì đỏ mất nghĩa, đúng bài học của chữ
	"Quá hạn" cũ ở bản v420.
	"""
	return {
		T_CHUA_GHI: "gray",
		T_DA_TRA: "green",
		T_MOT_PHAN: "blue",
		T_CHUA_TRA: "orange",
		T_QUA_HAN: "red",
		T_TRA_THUA: "purple",
	}.get(str(tt or "").strip(), "gray")


def phan_tram_da_tra(tong, con_lai):
	"""Đã trả được bao nhiêu phần trăm. THUẦN, trả số nguyên 0 tới 100.

	Dùng cho câu chú thích khi rê chuột lên chip, để nhìn một cái là biết
	tờ trả một phần đó đang ở gần đầu hay gần cuối.
	"""
	t = _so(tong)
	if t <= 0:
		return 0
	da = t - _so(con_lai)
	if da <= 0:
		return 0
	if da >= t:
		return 100
	return int(round(da * 100.0 / t))
