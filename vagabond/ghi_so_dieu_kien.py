# -*- coding: utf-8 -*-
"""Vì sao một hoá đơn chưa ghi sổ được. Toàn phép THUẦN.

Tệp này KHÔNG import gì cả, kể cả Frappe, để chạy được trên máy CI tay
không (xem AGENTS.md mục 6).

Anh Việt chốt 27/08/2026:

    *"Em thêm 1 chip lọc 'Không ghi sổ được' để lọc các đơn không đủ điều
    kiện ghi sổ (thiếu phương thức thanh toán,...) để các bạn điền, bổ sung
    ngay trước 23h mỗi ngày. Chip này cần có ở mọi màn tính tiền của các
    điểm bán."*

VÌ SAO PHẢI CÓ TỆP RIÊNG
========================

Trước đây phép "đơn này ghi sổ được chưa" nằm rải ba nơi và không nơi nào
biết nơi kia:

* `_chuan_bi_ghi_so` trong ban_hang.py - chặn thật lúc ghi sổ, nhưng chỉ
  nói ra khi đã bấm, và nói bằng cách ném lỗi.
* `_ly_do_treo` - chỉ soi đơn Pancake của màn "Đơn còn treo", không soi
  bill quầy, và không biết tới quầy nào được bật tự ghi sổ.
* Bộ lọc `loc_sales` / `loc_quay` của chuỗi cuối ngày - quyết định đơn nào
  được máy nhặt lúc 23h, nhưng không màn nào hiển thị luật đó.

Hậu quả: một đơn có thể trông bình thường trên màn tính tiền mà 23h máy
không nhặt, và không ai biết cho tới khi kế toán rà cuối tháng.

Nay ba nơi đó nói cùng một câu, vì cùng gọi `ly_do()` ở đây.

CẨN THẬN KHI SỬA
================

Thứ tự các phép kiểm ở đây phải bám theo `_chuan_bi_ghi_so`, vì đó mới là
cửa chặn thật. Đảo thứ tự thì màn hình báo một lý do mà máy chặn vì lý do
khác, nhân viên sửa xong vẫn không ghi sổ được.
"""

# Mã lý do -> câu cho nhân viên đọc. Câu phải nói RÕ PHẢI LÀM GÌ, vì người
# đọc là bạn Sales lúc 22h chứ không phải người viết mã.
LY_DO = {
	"tam_tinh": "Còn là phiếu tạm tính, khách chưa trả tiền nên chưa chốt",
	"chua_pt": "Chưa chọn phương thức thanh toán",
	"pt_sai_nguon": "Phương thức thanh toán không dùng được cho nguồn đơn này",
	"thieu_ma": "Phương thức này bắt buộc có mã tham chiếu mà đang để trống",
	"chua_ve_tien": "Chuyển khoản nhưng ngân hàng chưa nhận đủ tiền, cũng chưa có mã tham chiếu",
	"thieu_khach_no": "Bán công nợ nhưng chưa chọn khách công nợ",
	"tang_cho_duyet": "Đơn hàng tặng đang chờ Giám đốc duyệt",
	"tang_tu_choi": "Đơn hàng tặng đã bị Giám đốc từ chối, sửa lại hoặc đổi phương thức",
	"ngoai_chuoi": "Đơn đủ điều kiện nhưng nằm ngoài chuỗi tự ghi sổ cuối ngày, phải ghi sổ tay",
}

# Thứ tự này quyết định lý do nào được nói ra khi một đơn thiếu nhiều thứ.
# Nói cái người ta sửa được trước, cái thuộc về cấu hình sau cùng.
THU_TU = [
	"tam_tinh",
	"chua_pt",
	"pt_sai_nguon",
	"chua_ve_tien",
	"thieu_ma",
	"thieu_khach_no",
	"tang_tu_choi",
	"tang_cho_duyet",
	"ngoai_chuoi",
]

CHUYEN_KHOAN = "Chuyển khoản"
CONG_NO = "Công nợ"

# Ba chuoi duoi day CHEP TU `vagabond/hang_tang.py`, co y va bat dac di:
# tep nay khong duoc import gi ca, ke ca mo dun cua chinh minh, vi no phai
# chay tren may CI tay khong. Ban sao duoc canh boi ca kiem
# `thu_hang_tang.py`, ca do doc ca hai tep va bat den do neu hai ben lech
# nhau. Doi ten o mot ben ma quen ben kia thi ca kiem bao ngay.
HANG_TANG = "Hàng tặng"
TANG_DA_DUYET = "Đã duyệt"
TANG_TU_CHOI = "Từ chối"


def _chu(x):
	return str(x if x is not None else "").strip()


def _so(x):
	"""Đọc một ô cờ ra 0 hoặc 1. Nhận cả 1, "1", True, None."""
	if x is None or x is False or x == "":
		return 0
	try:
		return 1 if int(x) else 0
	except (TypeError, ValueError):
		return 1 if _chu(x) else 0


def ly_do(b, pt_hop_le=None, pt_can_ma=None, trong_chuoi=True, khach_le=""):
	"""Mã lý do một hoá đơn chưa ghi sổ được. Rỗng nghĩa là ghi sổ được.

	b           một dòng hoá đơn dạng dict, như `pos_ds_bill` trả về. Các ô
	            được đọc: docstatus, vgb_huy, vgb_tam_tinh, vgb_pt_thanh_toan,
	            vgb_ma_tham_chieu, sepay_du, customer.
	pt_hop_le   danh sách phương thức dùng được cho nguồn của đơn này.
	            None nghĩa là không kiểm - dùng khi người gọi chưa đọc được
	            danh sách, thà im còn hơn báo sai.
	pt_can_ma   tập tên phương thức bắt buộc có mã tham chiếu.
	trong_chuoi đơn này có được chuỗi tự ghi sổ cuối ngày nhặt không.
	khach_le    mã khách lẻ; bán công nợ cho khách lẻ tức là chưa chọn khách.

	Hoá đơn đã ghi sổ hoặc đã huỷ thì trả rỗng: hai loại đó không nằm trong
	việc "chưa ghi sổ được", đưa vào chip chỉ làm nhiễu.
	"""
	b = b or {}
	if _so(b.get("docstatus")) != 0:
		return ""
	if _so(b.get("vgb_huy")):
		return ""
	if _so(b.get("vgb_tam_tinh")):
		return "tam_tinh"

	pt = _chu(b.get("vgb_pt_thanh_toan"))
	if not pt:
		return "chua_pt"
	if pt_hop_le is not None and pt not in set(pt_hop_le or []):
		return "pt_sai_nguon"

	ma = _chu(b.get("vgb_ma_tham_chieu"))
	du_tien = _so(b.get("sepay_du"))
	if pt == CHUYEN_KHOAN:
		# SePay nhận đủ tiền thì máy tự điền mã giao dịch lúc ghi sổ, nên
		# đủ tiền cũng là đủ điều kiện dù ô mã đang trống.
		if not ma and not du_tien:
			return "chua_ve_tien"
	elif pt in set(pt_can_ma or []) and not ma:
		return "thieu_ma"

	if pt == CONG_NO:
		kh = _chu(b.get("customer"))
		if not kh or kh == _chu(khach_le):
			return "thieu_khach_no"

	# Hang tang: khong co dong nao ve nen khong co gi de doi soat, cai thay
	# cho doi soat la giam doc duyet. Dat SAU cac phep tren de thu tu bao loi
	# van bam theo `_chuan_bi_ghi_so`: to thieu phuong thuc thi noi thieu
	# phuong thuc truoc da.
	if pt == HANG_TANG:
		tt = _chu(b.get("vgb_tang_duyet"))
		if tt == TANG_TU_CHOI:
			return "tang_tu_choi"
		if tt != TANG_DA_DUYET:
			return "tang_cho_duyet"

	if not trong_chuoi:
		return "ngoai_chuoi"
	return ""


def chu(ma):
	"""Câu tiếng Việt của một mã lý do."""
	return LY_DO.get(_chu(ma), "")


def dem(ds_ly_do):
	"""Đếm số đơn theo từng lý do. Bỏ qua các đơn ghi sổ được."""
	ra = {}
	for m in ds_ly_do or []:
		m = _chu(m)
		if not m:
			continue
		ra[m] = ra.get(m, 0) + 1
	return ra


def xep(ds_ly_do):
	"""Các lý do có mặt, xếp theo THU_TU. Dùng để vẽ chip phụ cho gọn."""
	co = set(m for m in (ds_ly_do or []) if _chu(m))
	ra = [m for m in THU_TU if m in co]
	ra += sorted(m for m in co if m not in THU_TU)
	return ra
