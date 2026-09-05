# -*- coding: utf-8 -*-
"""Phép quyết định cho đường đẩy mã hàng từ ERP sang Pancake. THUẦN.

VÌ SAO CÓ TỆP NÀY (issue 204, Codex rà soát 05/09/2026)
--------------------------------------------------------
Đường đẩy cũ trả về đúng hai kiểu: `ok = 1` là xong, `ok = 0` là "đã có".
Hai giá trị đó không đủ để một cái máy khác đọc và quyết định làm gì tiếp.

Codex chỉ ra bốn tình huống bị gộp nhầm vào nhau:

  1. Mã đã có bên Pancake, hợp lệ. Không phải lỗi, không cần làm gì.
  2. Có NHIỀU mẫu mã cùng mang một mã hiển thị. Pancake cho phép chuyện đó,
     nên đây là xung đột cần người ngó tới, không phải "đã có".
  3. Đẩy hỏng thật, cần thử lại.
  4. Đã gửi lệnh tạo nhưng KHÔNG biết kết quả, ví dụ mạng đứt sau khi
     Pancake đã nhận. Đây là tình huống nguy nhất: thử lại mù là đẻ ra mã
     thứ hai.

Bốn cái đó phải là bốn trạng thái khác nhau, vì cách xử lý khác hẳn nhau.

TỆP NÀY KHÔNG import frappe, không gọi mạng, để chạy được ở máy kiểm thử
tay không. Phần gọi Pancake nằm ở pancake_sp.py.
"""

# Trạng thái của một lần đẩy. Đọc phần đầu tệp để biết vì sao phải tách.
KQ_CHUA_CO = "chua_co"        # tìm không thấy, được phép tạo
KQ_DA_CO = "da_co"            # đã có đúng một bản, không tạo lại
KQ_XUNG_DOT = "xung_dot"      # nhiều bản cùng mã, cần người xem
KQ_DA_TAO = "da_tao"          # vừa tạo xong, Pancake xác nhận
KQ_CHUA_RO = "chua_ro"        # đã gửi lệnh nhưng không biết kết quả
KQ_LOI = "loi"                # hỏng thật, thử lại được
KQ_THIEU_GIA = "thieu_gia"    # chưa có giá bán, không đẩy giá 0 lên

# Trạng thái nào cho phép người gọi thử lại lệnh tạo. `chua_ro` KHÔNG nằm
# ở đây, và đó là điểm quan trọng nhất của cả tệp: chưa rõ thì đi kiểm
# trạng thái, không tạo lại.
DUOC_THU_LAI = (KQ_LOI,)


def chuan_ma(ma):
	"""Chuẩn hoá một mã để so sánh. THUẦN."""
	return str(ma or "").strip().upper()


def khop_chinh_xac(ds, ma):
	"""Lọc ra những bản có mã hiển thị TRÙNG KHÍT với `ma`. THUẦN.

	Pancake tìm theo kiểu chứa chuỗi, nên hỏi "SLOP00015" có thể trả về cả
	"SLOP00015C" và "SLOP00015S". Ba mã đó là ba thứ khác nhau, gộp lại là
	gán nhầm hàng.
	"""
	m = chuan_ma(ma)
	if not m:
		return []
	ra = []
	for v in ds or []:
		if chuan_ma((v or {}).get("display_id")) == m:
			ra.append(v)
	return ra


def xep_ket_qua_tim(so_ban):
	"""Tìm xong thì rơi vào trạng thái nào. THUẦN.

	Không bản nào thì được tạo. Đúng một bản thì thôi. Từ hai bản trở lên
	là xung đột: Pancake cho hai mẫu mã cùng mã hiển thị, và lúc đó không
	ai biết đơn hàng đang trỏ vào bản nào.
	"""
	n = int(so_ban or 0)
	if n <= 0:
		return KQ_CHUA_CO
	if n == 1:
		return KQ_DA_CO
	return KQ_XUNG_DOT


def duoc_tao(trang_thai):
	"""Có được phép gửi lệnh tạo không. THUẦN."""
	return trang_thai == KQ_CHUA_CO


def duoc_thu_lai(trang_thai):
	"""Có được phép gọi lại lệnh tạo sau khi hỏng không. THUẦN.

	Chỉ lỗi thật mới được thử lại. `chua_ro` thì phải đi tìm lại trước, vì
	rất có thể Pancake đã tạo rồi mà mình không nghe được câu trả lời.
	"""
	return trang_thai in DUOC_THU_LAI


def gia_dung_de_day(gia, cho_phep_khong):
	"""Con số giá này có được phép đẩy đi không. THUẦN.

	Trả về (được hay không, trạng thái nếu không được).

	Đẩy giá 0 lên Pancake là dựng một mã bán được với giá không đồng. Trước
	đây hàm cũ vẫn đẩy và chỉ nhắn một câu trong lời chúc mừng, nên không ai
	đọc. Nay chặn hẳn, trừ khi người bấm nói rõ là cố ý.
	"""
	try:
		g = float(gia or 0)
	except (TypeError, ValueError):
		g = 0.0
	if g > 0:
		return True, ""
	if cho_phep_khong:
		return True, ""
	return False, KQ_THIEU_GIA


def duoc_xuat_ban(vo_hieu, hang_ban):
	"""Mã này có được phép đưa lên Pancake không. THUẦN.

	Mã đã ngừng dùng, hoặc mã không phải hàng bán, thì không được xuất bản
	chỉ vì nó lọt vào một danh sách nào đó. Codex nêu 05/09/2026.
	"""
	if int(vo_hieu or 0):
		return False
	return bool(int(hang_ban or 0))


def thong_bao(trang_thai, ma, so_ban=0):
	"""Câu tiếng Việt hiện cho người bấm. THUẦN.

	KHÔNG có câu mặc định kiểu "Xong.". Trạng thái lạ thì nói là chưa xác
	minh, vì báo thành công khi chưa biết kết quả đúng là cái đã làm Uyên
	mất niềm tin vào nút này.
	"""
	m = str(ma or "").strip()
	if trang_thai == KQ_DA_TAO:
		return "Đã tạo %s trên Pancake." % m
	if trang_thai == KQ_DA_CO:
		return "Mã %s đã có sẵn trên Pancake, không tạo lại." % m
	if trang_thai == KQ_XUNG_DOT:
		return ("Trên Pancake đang có %d mẫu mã cùng mang mã %s. "
			"Cần mở Pancake dọn lại trước, máy không tự chọn." % (int(so_ban or 0), m))
	if trang_thai == KQ_CHUA_RO:
		return ("Đã gửi lệnh tạo %s nhưng chưa nghe được trả lời. "
			"CHƯA XÁC MINH: bấm Kiểm lại, đừng bấm tạo lần nữa." % m)
	if trang_thai == KQ_THIEU_GIA:
		return ("Mã %s chưa có giá bán. Điền giá rồi hãy đẩy, "
			"hoặc tích ô cho phép đẩy giá 0 nếu cố ý." % m)
	if trang_thai == KQ_CHUA_CO:
		return "Mã %s chưa có trên Pancake." % m
	if trang_thai == KQ_LOI:
		return "Đẩy %s không được, thử lại sau." % m
	return "Chưa xác minh được kết quả của %s." % m
