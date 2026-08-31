"""Kiểm thử bộ sinh mã vạch Code 39 (vagabond/ma_vach.py).

Mã vạch sai là chuyện nguy: thủ kho quét một mã ra một mã KHÁC thì hàng vào
nhầm phiếu mà không ai nghi ngờ gì, vì máy quét kêu "bíp" y như bình thường.
Nên bộ kiểm ở đây không chỉ soi hình dạng, nó GIẢI MÃ ngược lại chuỗi vạch
rồi so với chuỗi gốc - đúng việc mà cái máy quét sẽ làm ngoài kho.

Bảng mã trong ma_vach.py đã được đối chiếu từng phần tử với thư viện
python-barcode, và ảnh dựng ra đã được thư viện zxing-cpp quét đọc đúng
(23/08/2026). Hai thư viện đó KHÔNG được nhập ở đây: máy chạy CI tay không,
xem quy tắc 5. Ca kiểm dưới đây tự đứng một mình.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la


def _mv():
	from vagabond import ma_vach

	return ma_vach


def _giai_ma(pt, mv):
	"""Chuỗi phần tử -> chữ, bằng cách tra ngược bảng mã.

	CẢNH BÁO, đọc trước khi tin ca kiểm này: hàm tra ngược CHÍNH bảng mã đang
	kiểm, nên nó chỉ chứng minh bộ sinh TỰ NHẤT QUÁN, không chứng minh bảng mã
	đúng chuẩn Code 39. Sửa hỏng một ô trong bảng thì hàm này vẫn giải ra đúng
	chuỗi gốc - em đã thử cố ý làm hỏng ô "7" ngày 23/08/2026 và ca kiểm vẫn
	xanh, nên mới viết dòng cảnh báo này.

	Thứ giữ cửa cho tính ĐÚNG là hai ca kiểm vân tay bên dưới, chốt lại đúng
	bảng đã đối chiếu từng phần tử với thư viện python-barcode và đã được
	zxing-cpp quét đọc lại thành công.
	"""
	nguoc = {}
	for c, p in mv.BANG.items():
		nguoc[p] = c
	# Cat chuoi phan tu thanh tung ky tu 9 phan tu, bo khoang ngan cach.
	ra, i = [], 0
	while i < len(pt):
		khuc = pt[i:i + 9]
		if len(khuc) < 9:
			return None
		mau = "".join("w" if w == mv.RONG else "n" for w, _ in khuc)
		if mau not in nguoc:
			return None
		ra.append(nguoc[mau])
		i += 9
		if i < len(pt):
			# Phai la mot khoang HEP ngan cach
			if pt[i][0] != 1 or pt[i][1]:
				return None
			i += 1
	return "".join(ra)


@ca("Bảng mã Code 39 đủ 44 ký tự, mỗi ký tự 9 phần tử và đúng 3 phần tử rộng")
def _():
	mv = _mv()
	la("số ký tự", len(mv.BANG), 44)
	sai_dai = [c for c, p in mv.BANG.items() if len(p) != 9]
	la("ký tự không đủ 9 phần tử", sai_dai, [])
	sai_rong = [c for c, p in mv.BANG.items() if p.count("w") != 3]
	la("ký tự không đúng 3 phần tử rộng", sai_rong, [])
	la("không mẫu nào trùng nhau", len(set(mv.BANG.values())), 44)
	dung("có ký tự mốc *", "*" in mv.BANG)


@ca("Quét ngược lại chuỗi vạch phải ra đúng mã ban đầu")
def _():
	mv = _mv()
	for goc in ("PNK-2026-00054", "NVLT00021", "BAWC00019", "DMH-2026-00047",
				"ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789", "BASS00038"):
		pt = mv.day_phan_tu(goc)
		doc = _giai_ma(pt, mv)
		# Chuoi ra phai la *GOC*
		la("giải mã %s" % goc, doc, "*" + goc + "*")


@ca("Mốc mở và mốc đóng luôn có, và phần tử đầu tiên luôn là VẠCH")
def _():
	mv = _mv()
	pt = mv.day_phan_tu("PNK-2026-00054")
	dung("phần tử đầu là vạch", pt[0][1])
	dung("phần tử cuối là vạch", pt[-1][1])
	# 16 ky tu (14 chu + 2 moc) x 9 phan tu + 15 khoang ngan cach
	la("đủ số phần tử", len(pt), 16 * 9 + 15)


@ca("Ký tự không mã hoá được thì bị loại chứ không đổi bậy thành mã khác")
def _():
	mv = _mv()
	la("chữ thường thành chữ hoa", mv.loc_duoc("pnk-2026"), "PNK-2026")
	la("bỏ ký tự lạ", mv.loc_duoc("BAWC#00019"), "BAWC00019")
	la("bỏ dấu tiếng Việt", mv.loc_duoc("BÁNH01"), "BNH01")
	la("bỏ luôn dấu sao vì nó là mốc", mv.loc_duoc("*ABC*"), "ABC")
	la("rỗng thì trả rỗng", mv.loc_duoc(""), "")
	la("None không làm sập", mv.loc_duoc(None), "")


@ca("Chuỗi rỗng không sinh ra mã vạch rỗng nghĩa")
def _():
	mv = _mv()
	la("không có ký tự nào thì không vẽ", mv.day_phan_tu("###"), [])
	la("SVG rỗng", mv.code39_svg("###"), "")
	la("thẻ img rỗng", mv.code39_img("###"), "")


@ca("SVG dựng ra đúng khổ và có đủ vạch đen")
def _():
	mv = _mv()
	svg = mv.code39_svg("BAWC00019", cao_mm=12, don_vi_mm=0.28)
	dung("là thẻ svg", svg.startswith("<svg"))
	dung("khai đơn vị mm", "mm" in svg)
	dung("có nền trắng", 'fill="#fff"' in svg)
	dung("có nhóm vạch đen", 'fill="#000"' in svg)
	dung("có in dòng chữ người đọc được", "BAWC00019" in svg)
	# Moi ky tu co 5 vach, 11 ky tu (9 chu + 2 moc) -> 55 hinh chu nhat vach
	la("số vạch", svg.count("<rect x"), 11 * 5)
	khong_chu = mv.code39_svg("BAWC00019", hien_chu=False)
	dung("tắt được dòng chữ", "<text" not in khong_chu)


@ca("Thẻ img mang data URI, không trỏ đường dẫn nào ra ngoài")
def _():
	mv = _mv()
	t = mv.code39_img("PNK-2026-00054")
	dung("là thẻ img", t.startswith("<img"))
	dung("nhúng thẳng dạng data URI", "src=\"data:image/svg+xml;base64," in t)
	dung("KHÔNG trỏ /files/ - đó là lỗi cũ", "/files/" not in t)
	dung("có alt để máy đọc màn hình còn biết", 'alt="PNK-2026-00054"' in t)


@ca("Mẫu in Phiếu nhập kho không còn dùng font mã vạch")
def _():
	"""Anh Việt 23/08/2026: bản in ra chỉ thấy chữ *PNK-2026-00054*.

	Nguyên nhân là @font-face trỏ /files/LibreBarcode39.ttf, wkhtmltopdf
	không nạp được. Ca kiểm này giữ cửa để không ai vô tình đưa font trở lại.
	"""
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	tep = os.path.join(goc, "mau_in", "phieu_nhap_kho.html")
	dung("mẫu in nằm trong repo chứ không chỉ trong cơ sở dữ liệu", os.path.exists(tep))
	if not os.path.exists(tep):
		return
	import io as _io
	import re as _re

	# Bo khoi ghi chu Jinja {# ... #} truoc khi soi. Chinh mau in CO nhac lai
	# tên cái font cũ trong phần giải thích vì sao nó bị bỏ, và soi cả ghi chú
	# thì ca kiểm báo hỏng trong khi mã thật đã đúng - đúng cái bẫy đã mất
	# công hai lần rồi (chip_cu hôm 21/08, mvNgaySau hôm 22/08).
	noi = _re.sub(r"\{#.*?#\}", "", _io.open(tep, encoding="utf-8").read(), flags=_re.S)
	dung("không còn @font-face", "@font-face" not in noi)
	dung("không còn trỏ LibreBarcode39.ttf", "LibreBarcode39" not in noi)
	dung("gọi hàm sinh mã vạch", "code39_img(" in noi)
	dung("có khai lề trang", "@page" in noi)


# ---------------------------------------------------------------- vân tay
#
# Hai ca dưới đây mới là thứ chặn được bảng mã bị sửa hỏng. Con số trong này
# lấy từ đúng bản đã kiểm chéo ngày 23/08/2026:
#
#   - so từng phần tử với thư viện python-barcode: 7/7 chuỗi thử KHỚP tuyệt đối
#   - dựng ảnh rồi cho zxing-cpp quét lại: 6/6 mã đọc đúng, nhận dạng Code39
#
# Đổi bảng mã mà không đổi hai con số này thì ca kiểm đỏ, và người đổi buộc
# phải đi kiểm chéo lại bằng thư viện thật trước khi chốt.


@ca("Vân tay bảng mã Code 39 phải khớp bản đã kiểm chéo bằng thư viện thật")
def _():
	import hashlib
	import json

	mv = _mv()
	van_tay = hashlib.sha256(
		json.dumps(mv.BANG, sort_keys=True).encode()
	).hexdigest()
	la(
		"SHA256 của bảng mã",
		van_tay,
		"14335fcb52ffa2b4fd656f234e5bc5c8cce04854372227c97a630a2c6f2a651c",
	)


@ca("Bề rộng từng phần tử của hai mã thật phải đúng từng con số")
def _():
	"""Hai chuỗi vàng, chép từ bản đã cho máy quét thật đọc đúng.

	Mỗi chữ số là bề rộng một phần tử: 1 hẹp, 3 rộng. Đây là thứ mà đầu đọc
	của máy quét thực sự nhìn thấy.
	"""
	mv = _mv()

	def _be_rong(t):
		return "".join(str(w) for w, _ in mv.day_phan_tu(t))

	la(
		"PNK-2026-00054",
		_be_rong("PNK-2026-00054"),
		"131131311111313113111111311331311111133113111131311133111131111331"
		"311111331111311133311111131111313111133131111113313111111331311131"
		"133111111113311131131131311",
	)
	la(
		"BAWC00019",
		_be_rong("BAWC00019"),
		"131131311111311311313111131131333111111131311311111113313111111331"
		"3111111331311131131111311133113111131131311",
	)


# =========================================================================
# Khối 1: ô tìm món ở màn kiểm bánh
# =========================================================================


def _doc_nguon(ten):
	import io as _io
	import os
	import re as _re

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	noi = _io.open(os.path.join(goc, ten), encoding="utf-8").read()
	# Bo dong ghi chu truoc khi soi - bay da mat cong ba lan roi.
	return "\n".join(d for d in noi.split("\n") if not d.strip().startswith("#"))


@ca("Bếp tìm được bánh lẻ, bánh mặn và BTP chứ không chỉ bánh ổ")
def _():
	"""Anh Việt 23/08/2026: ô tìm kiếm chỉ lọc ra bánh ổ.

	Patechaud mang mã BANU00065, bánh lạnh BAEN, bánh khô BACF, bán thành
	phẩm BTPB/BTPN - bản cũ lọc cứng "BAW%" nên không mã nào trong số đó ra.
	"""
	from vagabond import kiem_banh as kb

	for t in ("BAWC", "BAWS", "BANU", "BAEN", "BACF", "BASS", "BTPB", "BTPN"):
		dung("cho thêm tay tiền tố %s" % t, t in kb.TIEN_TO_THEM_TAY)
	# Nhung thu KHONG duoc lot vao: bang kiem banh khong dem phu kien hay nuoc.
	for t in ("BAPK", "BATP", "NUCF", "NUTR", "NVLT", "CCDC", "VVPP", "DVBH"):
		dung("KHÔNG nhận tiền tố %s" % t, t not in kb.TIEN_TO_THEM_TAY)
	# May TU nhat ve thi van chi banh o va banh si, khong duoc noi ra - noi ra
	# la bang ngap nhung dong khong ai muon dem.
	la("máy tự nhặt vẫn chỉ hai tiền tố", kb.TIEN_TO_MA, ("BAWC", "BAWS"))


@ca("Mã Patechaud và mã BTP đi qua được cửa _dang_ma_dung")
def _():
	from vagabond import kiem_banh as kb

	for ma in ("BANU00065", "BAEN00012", "BACF00003", "BTPB00030", "BTPN00014",
			   "BAWC00019", "BASS00038"):
		dung("nhận %s" % ma, kb._dang_ma_dung(ma))
	for ma in ("BAWC", "BANU", "NUCF00027", "CCDC00006", "", "linh tinh"):
		dung("chặn %s" % (ma or "(rỗng)"), not kb._dang_ma_dung(ma))
	dung("vẫn nhận hậu tố size cũ", kb._dang_ma_dung("BAWC00114MINI12CM"))


@ca("Đồng bộ KHÔNG được xoá dòng bếp thêm tay")
def _():
	"""Bẫy sâu hơn cái anh Việt nhìn thấy.

	Cho bếp thêm được mã mà bảng không giữ thì tính năng đó không tồn tại:
	đồng bộ chạy ngầm 5 phút một lần, dòng Patechaud vừa thêm sẽ biến mất
	không dấu vết và bếp tưởng mình bấm hụt.
	"""
	nguon = _doc_nguon("kiem_banh.py")
	dung(
		"lọc dòng theo tiền tố THÊM TAY",
		"if str(d.ma_hang or \"\").upper().startswith(TIEN_TO_THEM_TAY)" in nguon,
	)
	dung(
		"không còn lọc cứng theo TIEN_TO_MA",
		'doc.dong = [d for d in doc.dong if str(d.ma_hang or "").upper().startswith(TIEN_TO_MA)]'
		not in nguon,
	)


@ca("Đơn của mã bếp thêm tay vẫn được đếm vào cột Đã đặt")
def _():
	nguon = _doc_nguon("kiem_banh.py")
	dung("phép đếm nhận danh sách mã đang theo dõi", "def _dem_banh(dons, dang_theo_doi=None)" in nguon)
	dung("đếm cả mã ngoài tiền tố nếu bảng đang theo dõi",
		 "not ma.upper().startswith(TIEN_TO_MA) and ma.upper() not in theo_doi" in nguon)
	dung("kênh khác cũng vậy", "def _dem_don_khac(ngay, dang_theo_doi=None)" in nguon)


# =========================================================================
# Khối 3: rasterize PDF và lề in
# =========================================================================


@ca("Thiếu thư viện rasterize thì trả rỗng chứ không làm sập bản in")
def _():
	from vagabond import ho_so_tt as hs

	# Khong co thu vien -> danh sach rong, ben goi tu quay ve duong noi PDF cu.
	dung("hàm dò thư viện không ném lỗi", isinstance(hs._thu_vien_raster(), str))
	la("dữ liệu rác không làm sập", hs._pdf_ra_anh(b"khong phai PDF"), [])
	la("rỗng cũng không làm sập", hs._pdf_ra_anh(b""), [])


@ca("PDF đính kèm được đổi thành ảnh chứ không bị bỏ lại")
def _():
	"""Anh Việt 23/08/2026: *"không in được Bản thể hiện hoá đơn vì nó là PDF"*."""
	nguon = _doc_nguon("ho_so_tt.py")
	dung("có nhánh xử lý riêng cho pdf", 'if duoi == "pdf":' in nguon)
	dung("gọi hàm rasterize", "_pdf_ra_anh(_noi_tep(ma))" in nguon)
	dung("đổi không được thì vẫn ghi vào bỏ qua để nối ở cuối", "bo_qua.append" in nguon)


@ca("Lề in lấy từ một chỗ duy nhất, không nơi nào tự khai lại")
def _():
	from vagabond.mau_in import le_in

	la("lề 15mm", le_in.LE_MM, 15)
	la("vùng in ngang còn lại", le_in.RONG_TRONG_MM, 180)
	la("vùng in dọc còn lại", le_in.CAO_TRONG_MM, 267)
	css = le_in.css_trang()
	dung("khai khổ A4 dọc", "size:A4 portrait" in css)
	dung("khai lề 15mm", "margin:15mm" in css)
	dung("có hàng rào thứ hai bằng padding", ".vgb-in{padding" in css)

	nguon = _doc_nguon("ho_so_tt.py")
	# Tu 31/08/2026 co truyen them xau phong vao, xem thu_phong_moi_to.py.
	dung("bản in hồ sơ dùng CSS chung", "css_trang(" in nguon)
	dung("không còn tự khai 12mm", "margin:12mm" not in nguon)


@ca("Mô đun nào bộ kiểm tầng khung có import thì đầu tệp KHÔNG được kéo thư viện mạng")
def _():
	# Ca chan chung cho ca lop loi nay, khong phai cho rieng mot tep.
	#
	# Ngay 20/08/2026 CI do 3 ca: nop_quy keo cong_no, cong_no keo ban_hang,
	# ban_hang co "import requests" o dau tep.
	# Ngay 23/08/2026 CI lai do 2 ca: hai ca Khoi 1 duoi day import
	# vagabond.kiem_banh, tep do cung co "import requests" o dau.
	# Hai lan cung mot nguyen nhan, nen lan nay dat mot cai chan tu dong.
	#
	# May chay CI cua GitHub tay khong, Python 3.11, khong co requests, khong
	# co Frappe, khong co site. May lam viec thi co san requests nen cong tai
	# may VAN XANH trong khi CI do - dung cai bay quy tac 5 da ghi.
	#
	# Cach go khi ca nay do: chuyen "import requests" xuong TRONG than ham
	# dung no, giong _mang() trong kiem_banh.py va "import erpnext" o duong
	# tra truoc. Dung stub requests trong nen.py, lam vay la giau loi di.
	import io
	import os
	import re

	thu_muc = os.path.dirname(os.path.abspath(__file__))
	goc = os.path.dirname(os.path.dirname(thu_muc))  # .../vagabond

	MANG = ("requests", "urllib3", "httpx")

	# Lot qua moi tep ca kiem, nhat ra ten mo dun nghiep vu ma no import.
	can = set()
	for ten in sorted(os.listdir(thu_muc)):
		if not ten.startswith("thu_") or not ten.endswith(".py"):
			continue
		src = io.open(os.path.join(thu_muc, ten), encoding="utf-8").read()
		for m in re.finditer(r"from vagabond import ([a-z_0-9, ]+)", src):
			for x in m.group(1).split(","):
				can.add(x.strip().split(" ")[0])
		for m in re.finditer(r"import vagabond\.([a-z_0-9]+)", src):
			can.add(m.group(1))
	can.discard("")
	dung("có nhặt ra được mô đun để soi", len(can) > 0)

	hong = []
	for ten in sorted(can):
		p = os.path.join(goc, ten + ".py")
		if not os.path.exists(p):
			continue
		src = io.open(p, encoding="utf-8").read()
		# Chi soi phan TRUOC dinh nghia dau tien, do la vung chay luc import.
		cat = re.split(r"\n(?:def |class )", src, maxsplit=1)[0]
		for lib in MANG:
			if re.search(r"^import %s\b" % lib, cat, re.M) or re.search(
				r"^from %s\b" % lib, cat, re.M
			):
				hong.append("%s.py keo %s o dau tep" % (ten, lib))

	dung("không mô đun nào kéo thư viện mạng ở đầu tệp: " + (", ".join(hong) or "sạch"),
		not hong)
