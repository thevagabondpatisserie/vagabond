"""Sinh mã vạch Code 39 thành ảnh SVG, THUẦN Python, không thư viện ngoài.

VÌ SAO KHÔNG DÙNG FONT MÃ VẠCH
------------------------------
Mẫu in Phiếu nhập kho trước đây khai một @font-face trỏ tới
`/files/LibreBarcode39.ttf` rồi in `*{{ doc.name }}*` bằng font đó. Tệp font
CÓ trên máy chủ và tải qua trình duyệt vẫn tốt, nhưng wkhtmltopdf chạy một
tiến trình riêng và KHÔNG nạp được @font-face trỏ đường dẫn tương đối, nên
bản in ra chỉ còn dòng chữ "*PNK-2026-00054*" thường - anh Việt bắt được
23/08/2026.

Đây đúng bài học đã ghi hai lần trong repo này (`thuong_hieu.py`,
`_qr_data_uri` của cong_no.py): NHÚNG THẲNG vào tờ, đừng trỏ đường dẫn.

Sinh hẳn hình vạch thì không phụ thuộc font nào, máy quét đọc bề rộng vạch
chứ không đọc chữ, và cùng một tờ in ra ở đâu cũng như nhau.

VÌ SAO CODE 39
--------------
Mã của tiệm (PNK-2026-00054, NVLT00021, BAWC00019) chỉ gồm chữ HOA, chữ số
và dấu gạch ngang - nằm gọn trong bộ ký tự Code 39. Code 39 không cần tính
số kiểm tra, mọi máy quét bán lẻ đều đọc được, và bảng mã đủ nhỏ để kiểm
thử từng ký tự một.

CÁCH ĐỌC BẢNG MÃ
----------------
Mỗi ký tự Code 39 gồm ĐÚNG 9 phần tử xen kẽ vạch-khoảng, bắt đầu bằng vạch:

    vạch khoảng vạch khoảng vạch khoảng vạch khoảng vạch
     0     1     2     3     4     5     6     7     8

Trong 9 phần tử đó có ĐÚNG 3 phần tử rộng ('w'), còn lại hẹp ('n'). Giữa
hai ký tự là một khoảng hẹp. Ký tự '*' làm mốc mở và mốc đóng.
"""

# Bang ma chuan Code 39. 'n' hep, 'w' rong. Chin phan tu, xen ke vach-khoang,
# phan tu dau tien LA VACH. Moi dong dung ba chu 'w' - bo kiem thu giu luat do.
BANG = {
	"0": "nnnwwnwnn", "1": "wnnwnnnnw", "2": "nnwwnnnnw", "3": "wnwwnnnnn",
	"4": "nnnwwnnnw", "5": "wnnwwnnnn", "6": "nnwwwnnnn", "7": "nnnwnnwnw",
	"8": "wnnwnnwnn", "9": "nnwwnnwnn",
	"A": "wnnnnwnnw", "B": "nnwnnwnnw", "C": "wnwnnwnnn", "D": "nnnnwwnnw",
	"E": "wnnnwwnnn", "F": "nnwnwwnnn", "G": "nnnnnwwnw", "H": "wnnnnwwnn",
	"I": "nnwnnwwnn", "J": "nnnnwwwnn", "K": "wnnnnnnww", "L": "nnwnnnnww",
	"M": "wnwnnnnwn", "N": "nnnnwnnww", "O": "wnnnwnnwn", "P": "nnwnwnnwn",
	"Q": "nnnnnnwww", "R": "wnnnnnwwn", "S": "nnwnnnwwn", "T": "nnnnwnwwn",
	"U": "wwnnnnnnw", "V": "nwwnnnnnw", "W": "wwwnnnnnn", "X": "nwnnwnnnw",
	"Y": "wwnnwnnnn", "Z": "nwwnwnnnn",
	"-": "nwnnnnwnw", ".": "wwnnnnwnn", " ": "nwwnnnwnn", "$": "nwnwnwnnn",
	"/": "nwnwnnnwn", "+": "nwnnnwnwn", "%": "nnnwnwnwn", "*": "nwnnwnwnn",
}

MOC = "*"          # ky tu mo va dong cua Code 39
RONG = 3           # ty le rong tren hep. 3:1 de doc hon 2:1, chuan cho phep


def loc_duoc(chuoi):
	"""Bỏ mọi ký tự Code 39 không mã hoá được, viết HOA phần còn lại. THUẦN.

	Thà in một mã ngắn hơn mà máy quét đọc được, còn hơn ném lỗi giữa lúc
	thủ kho đang cần tờ phiếu. Ký tự lạ bị bỏ chứ không đổi thành dấu hỏi:
	đổi bậy là sinh ra một mã KHÁC mã thật, nguy hơn nhiều.
	"""
	ra = []
	for c in str(chuoi or "").upper():
		if c in BANG and c != MOC:
			ra.append(c)
	return "".join(ra)


def day_phan_tu(chuoi):
	"""Chuỗi chữ -> danh sách bề rộng từng phần tử, kèm mốc mở và mốc đóng. THUẦN.

	Trả về [(rong, la_vach), ...]. Dùng chung cho phép vẽ và cho bộ kiểm thử,
	để ca kiểm soi đúng thứ mà máy in vẽ ra chứ không soi một bản sao.
	"""
	sach = loc_duoc(chuoi)
	if not sach:
		return []
	ra = []
	for i, c in enumerate(MOC + sach + MOC):
		if i:
			# Khoang hep ngan cach hai ky tu. Thieu no la hai ky tu dinh nhau
			# va may quet doc ra mot ky tu khac han.
			ra.append((1, False))
		for k, p in enumerate(BANG[c]):
			ra.append((RONG if p == "w" else 1, k % 2 == 0))
	return ra


def code39_svg(chuoi, cao_mm=12.0, don_vi_mm=0.28, hien_chu=True):
	"""Vẽ mã vạch Code 39 thành SVG nội tuyến. THUẦN, không chạm Frappe.

	cao_mm    chiều cao vạch
	don_vi_mm bề rộng một phần tử hẹp. 0,28mm là cỡ an toàn cho máy in nhiệt
	          và máy in văn phòng; nhỏ hơn nữa thì mực nhoè làm máy quét trượt.
	hien_chu  in dòng chữ người đọc được ngay dưới vạch, để ai không có máy
	          quét vẫn gõ tay được.

	Trả về chuỗi SVG. Rỗng nếu không mã hoá được ký tự nào.
	"""
	pt = day_phan_tu(chuoi)
	if not pt:
		return ""
	tong = sum(w for w, _ in pt)
	rong_mm = tong * don_vi_mm
	cao_chu = 3.2 if hien_chu else 0.0
	cao_tong = cao_mm + cao_chu

	vach, x = [], 0.0
	for w, la_vach in pt:
		if la_vach:
			vach.append(
				'<rect x="%.3f" y="0" width="%.3f" height="%.3f"/>'
				% (x, w * don_vi_mm, cao_mm)
			)
		x += w * don_vi_mm

	chu = ""
	if hien_chu:
		chu = (
			'<text x="%.3f" y="%.3f" text-anchor="middle" '
			'font-family="Arial,Helvetica,sans-serif" font-size="2.6" '
			'letter-spacing="0.35">%s</text>'
			% (rong_mm / 2.0, cao_mm + 2.6, loc_duoc(chuoi))
		)

	return (
		'<svg xmlns="http://www.w3.org/2000/svg" width="%.3fmm" height="%.3fmm" '
		'viewBox="0 0 %.3f %.3f" shape-rendering="crispEdges">'
		'<rect width="%.3f" height="%.3f" fill="#fff"/>'
		'<g fill="#000">%s</g>%s</svg>'
		% (rong_mm, cao_tong, rong_mm, cao_tong, rong_mm, cao_tong,
		   "".join(vach), chu)
	)


def code39_img(chuoi, cao_mm=12.0, don_vi_mm=0.28, hien_chu=True):
	"""Thẻ <img> mang mã vạch dạng data URI, dán thẳng vào mẫu in Jinja.

	Dùng data URI chứ không phải SVG nội tuyến vì wkhtmltopdf dựng <img> ổn
	định hơn nhiều so với <svg> nằm giữa dòng.
	"""
	import base64

	svg = code39_svg(chuoi, cao_mm=cao_mm, don_vi_mm=don_vi_mm, hien_chu=hien_chu)
	if not svg:
		return ""
	b64 = base64.b64encode(svg.encode("utf-8")).decode()
	return (
		'<img alt="%s" src="data:image/svg+xml;base64,%s" '
		'style="height:%.2fmm;display:block;margin:0 auto">'
		% (loc_duoc(chuoi), b64, cao_mm + (3.2 if hien_chu else 0.0))
	)
