# -*- coding: utf-8 -*-
"""Bóc số điện thoại ra khỏi một ô người ta gõ tự do.

Vì sao có tệp này
-----------------
Ngày 25/08/2026, khi dựng luồng Tặng quà khách VIP, em chạy thử `lib.sdt()`
trên 18 ô số điện thoại lấy NGUYÊN VĂN từ bảng tính của chị Loan Anh. Kết
quả khác hẳn điều ai cũng tưởng.

`lib.sdt()` không hỏng. Nó bóc được phần lớn ca rác thông thường, và khi
không chắc thì trả rỗng chứ không đoán bừa, đúng như chú thích trong
`lib.py` đã dặn. Nó hỏng ở ba chỗ khác:

  1. MẤT SỐ CỐ ĐỊNH. Bảng đầu số của `lib.py` chỉ có đầu số di động, nên
     "028 39322722 gặp chị Thư" trả rỗng. Trong bảng tính có ít nhất hai
     khách chỉ để lại số bàn. Với hai người đó hệ thống sẽ mãi mãi báo
     "chưa có số".

  2. MẤT SỐ NẰM TRONG CÂU. `lib._chin_so` ép CẢ Ô thành một dãy chữ số rồi
     mới xét. Ô nào có thêm chữ số khác, ví dụ số lượng hộp hay ngày tháng,
     là tổng vượt chín chữ số và hàm trả rỗng. Ví dụ thật: "25 hộp cho Sen
     Vàng gửi cùng 1 địa chỉ - Thông tin liên hệ: 0903015001 - Thi".

  3. TRẢ VỀ SỐ ĐÚNG CỦA NGƯỜI KHÁC. Đây mới là chỗ nguy hiểm. Ô
     "Gửi bảo vệ cho anh Bình hoặc alo chị Hương 0908280338" cho ra một số
     hợp lệ hoàn hảo, không cờ, không cảnh báo. Số đó là của chị Hương.
     Cùng kiểu đó là "0972741266 - Na (Trợ Lý)" và "093 2554338 (chị Linh
     quản gia)".

Chỗ thứ ba không phải lỗi kỹ thuật, đó là một sự cố thương hiệu chờ sẵn:
nối vào ZNS thì hệ thống sẽ gửi "Kính chúc anh Lâm Thành Kim..." vào máy
trợ lý của anh ấy, đúng vào nhóm khách mà cả đợt quà sinh ra để chăm.

Cách làm ở đây khác `lib._chin_so` ở một điểm căn bản: TÁCH MẨU TRƯỚC, XÉT
SAU. Dò từng mẩu số trên chuỗi gốc khi chữ vẫn còn nguyên, rồi mới gọi
`lib.sdt()` trên riêng từng mẩu. Nhờ vậy đọc được cả ô có hai số, ô có ngày
tháng, và đọc được luôn tên người nghe máy nằm cạnh số.

Ba luật xuyên suốt, viết ra để người sau không nới lỏng
-------------------------------------------------------
  1. KHÔNG BAO GIỜ ĐOÁN. Không chắc thì trả rỗng kèm câu bảo phải làm gì
     (QT-24). Đoán đúng chín lần và sai một lần vẫn là một khách VIP nhận
     tin nhắn chúc mừng mang tên người khác.
  2. KHÔNG BAO GIỜ SỬA Ô GỐC. Ô người ta gõ giữ nguyên vĩnh viễn, để sáu
     tháng sau còn tra lại được máy đã hiểu sai chỗ nào.
  3. BÓC LẠI ĐƯỢC KHÔNG GIỚI HẠN LẦN. Chạy lần thứ mười trên cùng một ô
     phải ra cùng một kết quả, để vá luật xong thì quét lại cả sổ được.

Tệp này là PHẦN THUẦN, không `import frappe`, để bộ kiểm thử tầng khung
chạy được ở CI mà không cần site. Ca kiểm ở
`vagabond/khung/kiem_thu/thu_sdt_boc.py`, nạp thẳng 18 ô nguyên văn làm dữ
liệu kiểm.
"""

import re

from vagabond.lib import sdt as _sdt_di_dong

# Đầu số điện thoại cố định Việt Nam, mã vùng sau nghị định đổi mã năm 2017.
#
# Phải liệt kê từng mã chứ không kiểm "bắt đầu bằng 02": cùng lý do đã ghi
# trong lib.py, một mã vùng không tồn tại nghĩa là ô đó chứa thứ khác chứ
# không phải số điện thoại. Trong tệp Fabi từng có mã số thuế bị gõ nhầm vào
# ô số điện thoại.
MA_VUNG = frozenset((
	"024 0203 0204 0205 0206 0207 0208 0209 0210 0211 0212 0213 0214 0215 "
	"0216 0218 0219 0220 0221 0222 0225 0226 0227 0228 0229 0232 0233 0234 "
	"0235 0236 0237 0238 0239 0251 0252 0254 0255 0256 0257 0258 0259 0260 "
	"0261 0262 0263 0269 0270 0271 0272 0273 0274 0275 0276 0277 0290 0291 "
	"0292 0293 0294 0296 0297 0299 028"
).split())

# Những chữ nói rằng số này KHÔNG phải của chính khách.
#
# Đây là danh sách quan trọng nhất trong tệp. Thiếu một từ ở đây là một tin
# nhắn chúc mừng bay nhầm máy. Viết cả bản có dấu lẫn không dấu vì trong
# bảng tính người ta gõ cả hai kiểu.
BAO_KHONG_CHINH_CHU = (
	"trợ lý", "tro ly", "trợ lí", "quản gia", "quan gia",
	"thư ký", "thu ky", "thư kí", "bảo vệ", "bao ve",
	"nhân viên", "nhan vien", "quản lý", "quan ly", "quản lí",
	"giúp việc", "giup viec", "người giúp", "nguoi giup",
	"tài xế", "tai xe", "lễ tân", "le tan", "số bàn", "so ban",
	"trực", "truc", "công ty", "cong ty",
)

# Từ dẫn đứng trước hoặc sau một số, cần gọt đi khi lấy tên người nghe máy.
TU_DAN = (
	"gặp", "gap", "gọi", "goi", "alo", "a lô", "liên hệ", "lien he",
	"số", "so", "sdt", "sđt", "đt", "dt", "hoặc", "hoac", "hay",
	"thông tin liên hệ", "thong tin lien he", "bấm chuông", "bam chuong",
)

# Khuôn dò một VỆT SỐ trên chuỗi GỐC: chữ số, xen khoảng trắng, dấu chấm
# và dấu gạch ở GIỮA, bắt buộc kết thúc bằng chữ số.
#
# Vệt số KHÔNG phải là số điện thoại, nó chỉ là vùng để xét. "0906220392 24"
# là một vệt nhưng chứa một số điện thoại cộng một con số ngày. Việc tách
# vệt thành số nằm ở `_tach_so`.
KHUON_VET = re.compile(r"\+?\d[\d\s.\-]*\d")

# Dấu gạch lạ hay bị dán vào từ Word, Google Sheets. Đổi hết về gạch thường
# trước khi dò, không thì khuôn ở trên không nhận ra.
GACH_LA = dict.fromkeys(map(ord, "‐‑‒–—―−"), "-")


# ------------------------------------------------------------- phép thuần


def _chuan_be_mat(tho):
	"""Đổi dấu gạch lạ về gạch thường, gộp khoảng trắng. GIỮ NGUYÊN CHỮ.

	Không bỏ chữ, vì chữ chính là chỗ đọc ra ai đang nghe máy.
	"""
	s = str(tho or "").translate(GACH_LA)
	s = s.replace(" ", " ")
	return re.sub(r"[ \t]+", " ", s).strip()


def _doc_mot_mau(mau):
	"""Một mẩu số ra được gì. Trả về (sdt, loai). Rỗng nghĩa là không đọc được.

	Gọi `lib.sdt()` trên RIÊNG mẩu này, tức là đã cô lập khỏi phần chữ và
	khỏi các con số khác trong ô. Đó là điều kiện để dùng lại hàm cũ mà
	không dính ba lỗi đã kể ở đầu tệp.
	"""
	di_dong = _sdt_di_dong(mau)
	if di_dong:
		return di_dong, "di_dong"

	# Không phải di động thì thử số cố định. Số cố định Việt Nam là mã vùng
	# 3 tới 4 chữ số cộng 7 tới 8 chữ số thuê bao, tổng 10 tới 11 chữ số kể
	# cả số 0 đầu.
	so = "".join(c for c in mau if c.isdigit())
	if so.startswith("0084"):
		so = "0" + so[4:]
	elif so.startswith("84") and len(so) > 10:
		so = "0" + so[2:]
	if len(so) in (10, 11) and so.startswith("0"):
		for n in (4, 3):
			if so[:n] in MA_VUNG:
				return so, "co_dinh"
	return "", ""


def _tach_so(vet):
	"""Một vệt số chứa mấy số điện thoại. Trả về danh sách (sdt, loai).

	Vì sao phải có bước này chứ không để một khuôn chính quy lo hết
	------------------------------------------------------------------
	Ô thật "0913112345 - 0908280338" và ô thật "0906220392 24" nhìn giống
	nhau với mọi khuôn chính quy: đều là chữ số xen dấu ngăn. Cái đầu là hai
	số điện thoại, cái sau là một số điện thoại cộng một con số ngày.

	Khuôn tham lam thì cả hai thành một mẩu dài, không đọc ra gì, và MẤT
	SẠCH. Khuôn dè dặt thì cắt nhầm một số thành hai mảnh. Cả hai đều sai.

	Nên tách vệt thành các nhóm chữ số rồi ghép lại từ trái sang, mỗi lần
	thử nhóm dài nhất trước. Ghép ra một số hợp lệ thì ăn, không thì lùi một
	nhóm. Đây KHÔNG phải đoán: chỉ nhận tổ hợp mà `lib.sdt()` hoặc bảng mã
	vùng công nhận, phần thừa thì bỏ chứ không nhét bừa vào đâu.
	"""
	nhom = re.findall(r"\+?\d+", vet)
	ra, i = [], 0
	while i < len(nhom):
		an = 0
		for j in range(len(nhom), i, -1):
			so, loai = _doc_mot_mau("".join(nhom[i:j]))
			if so:
				ra.append((so, loai))
				i, an = j, 1
				break
		if not an:
			i += 1
	return ra


def _got_ten(doan):
	"""Gọt một đoạn chữ thành tên người nghe máy. Rỗng nếu không còn gì.

	Bỏ dấu dẫn ở hai đầu, bỏ từ dẫn, bỏ chữ số còn sót.
	"""
	s = str(doan or "").strip(" -:,.;/|\t\n")
	# Cặp ngoặc bọc CẢ đoạn thì bỏ cả hai. Không dùng strip cho dấu ngoặc,
	# vì "Na (Trợ Lý)" bị strip là mất dấu đóng và tên đọc ra thành hỏng.
	while len(s) > 1 and s[0] in "([" and s[-1] in ")]":
		s = s[1:-1].strip(" -:,.;/|")
	if not s:
		return ""
	thap = s.lower()
	for tu in sorted(TU_DAN, key=len, reverse=True):
		if thap.startswith(tu + " ") or thap == tu:
			s = s[len(tu):].strip(" -:,.;")
			thap = s.lower()
	s = s.strip(" -:,.;/|")
	# Còn lại toàn chữ số hoặc rỗng thì coi như không có tên.
	if not s or not re.search(r"[^\W\d_]", s, re.UNICODE):
		return ""
	# Cắt bớt cho gọn: tên người nghe máy dài hơn 40 ký tự thì gần như chắc
	# chắn đã nuốt cả một câu ghi chú.
	return s[:40].strip(" -:,.;")


def _la_chinh_chu(ten_nghe, ca_o=""):
	"""Số này có phải của chính khách không. Soi CẢ Ô chứ không chỉ tên nghe máy.

	Vì sao phải soi cả ô: ô thật
	"Gửi bảo vệ cho anh Bình hoặc alo chị Hương 0908280338( đã tặng)" có chữ
	"bảo vệ" đứng ở ĐẦU ô, cách con số hơn ba mươi ký tự, còn phần chữ ngay
	cạnh số lại là "( đã tặng)". Soi mỗi phần cạnh số thì ô này lọt lưới với
	cờ chính chủ bằng 1, và số của chị Hương sẽ nhận tin nhắn mang tên anh
	Bình.

	Soi cả ô thì đôi khi khoá nhầm một ô vốn sạch. Đó là cái giá chấp nhận
	được: khoá nhầm chỉ tốn một cuộc gọi tay, gửi nhầm thì mất một khách VIP.
	"""
	thap = ("%s %s" % (ten_nghe or "", ca_o or "")).lower()
	if not thap.strip():
		return True
	return not any(tu in thap for tu in BAO_KHONG_CHINH_CHU)


def boc(tho):
	"""Bóc một ô số điện thoại rác. THUẦN, không đụng cơ sở dữ liệu.

	Trả về dict:
		tho         nguyên văn đầu vào, không bao giờ bị sửa
		sdt         '0xxxxxxxxx' hoặc rỗng
		loai        'di_dong' | 'co_dinh' | ''
		nguoi_nghe  'Na (Trợ Lý)' hoặc rỗng
		chinh_chu   1 hoặc 0
		canh_bao    câu nói rõ phải làm gì tiếp, rỗng nếu sạch (QT-24)
	"""
	goc = str(tho or "")
	ra = {"tho": goc, "sdt": "", "loai": "", "nguoi_nghe": "",
		"chinh_chu": 1, "canh_bao": ""}
	s = _chuan_be_mat(goc)
	if not s:
		return ra

	# Dò từng VỆT SỐ trên chuỗi gốc, giữ cả vị trí để còn cắt phần chữ hai
	# bên, rồi tách mỗi vệt ra thành các số thật.
	tim_duoc = []
	for m in KHUON_VET.finditer(s):
		for so, loai in _tach_so(m.group(0)):
			tim_duoc.append((so, loai, m.start(), m.end()))
	if not tim_duoc:
		ra["canh_bao"] = (
			"Chưa đọc ra số điện thoại nào trong ô này. Nhờ anh chị gõ lại "
			"số vào ô, hoặc để trống nếu khách không cho số."
		)
		return ra

	# Bỏ trùng nhưng GIỮ THỨ TỰ, vì mẩu đầu là mẩu sẽ được lấy làm gợi ý.
	rieng, da_thay = [], set()
	for x in tim_duoc:
		if x[0] not in da_thay:
			da_thay.add(x[0])
			rieng.append(x)

	so, loai, dau, cuoi = rieng[0]
	ra["sdt"], ra["loai"] = so, loai

	# Tên người nghe máy: phần chữ NGAY SAU số, không có thì phần NGAY TRƯỚC.
	#
	#   '0972741266 - Na (Trợ Lý)'        -> 'Na (Trợ Lý)'
	#   '093 2554338 (chị Linh quản gia)' -> 'chị Linh quản gia'
	#   'Hoàng Phương Nam +84 90 8415976' -> 'Hoàng Phương Nam'
	sau = _got_ten(s[cuoi:])
	ra["nguoi_nghe"] = sau or _got_ten(s[:dau])

	if len(rieng) > 1:
		# KHÔNG TỰ CHỌN. Lấy mẩu đầu làm gợi ý nhưng khoá lại.
		#
		# Vì sao không tự chọn mẩu đầu: ô thật "Gửi bảo vệ cho anh Bình hoặc
		# alo chị Hương 0908280338" chỉ có MỘT số, mà số đó là của chị Hương.
		# Máy không có cách nào biết. Ô có hai số thì xác suất chọn nhầm còn
		# cao hơn nữa, nên phải để người nhìn.
		ra["chinh_chu"] = 0
		ra["canh_bao"] = (
			"Ô này có %d số khác nhau (%s). Nhờ anh chị chọn giúp số của "
			"chính khách rồi gõ lại một số thôi."
			% (len(rieng), ", ".join(x[0] for x in rieng[:3]))
		)
		return ra

	if not _la_chinh_chu(ra["nguoi_nghe"], s):
		ra["chinh_chu"] = 0
		ra["canh_bao"] = (
			"Ô này cho thấy số không phải của chính khách%s. Tin nhắn tự động "
			"đã khoá, nhờ anh chị gọi tay."
			% ((" mà của %s" % ra["nguoi_nghe"]) if ra["nguoi_nghe"] else "")
		)
		return ra

	if loai == "co_dinh":
		ra["canh_bao"] = (
			"Đây là số bàn, không nhận được tin nhắn Zalo. Nhờ anh chị gọi "
			"tay, hoặc xin thêm số di động của khách."
		)
	return ra
