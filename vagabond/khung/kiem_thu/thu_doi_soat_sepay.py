"""Ca kiểm cho tầng đối soát SePay dùng chung.

Mọi ca ở đây chạy trên phép THUẦN, không cần Frappe, không cần site, không
cần mạng.

VÌ SAO TỆP NÀY RA ĐỜI (anh Việt 24/08/2026)
============================================
*"Tất cả các phần đối chiếu SePay này phải làm ở cấp độ backend cho mọi màn
cần đối soát SePay, gồm đối soát tự động và nút đối soát thủ công ở kế bên."*

Trước v294 có BẢY phép "một dòng sao kê có khớp phiếu này không" viết lại độc
lập, mỗi phép sai một kiểu, và bốn hàm gọt chuỗi làm y hệt một việc với bốn
cái tên khác nhau. Bộ ca kiểm này canh phép DUY NHẤT thay cho cả bảy.
"""

from vagabond import doi_soat_sepay as dss
from vagabond import khop_sao_ke as ksk
from vagabond.khung.kiem_thu.nen import ca, dung, la

# BA DONG SAO KE THAT, chep nguyen van tu bang Bank Transaction ngay
# 24/08/2026. Day la du lieu quyet dinh ca thiet ke, khong duoc sua cho gon.
THAT = [
	("MBCT THE VAGABOND HOAN TIEN DH 92156 D2HLVNHF/428417", "92156", 750000),
	("THE VAGABOND HOAN TIEN DH 92252", "92252", 705000),
	("MBCT VAGABOND HOAN TIEN DON HANG 92245 D237BVMB/870581", "92245", 920000),
]


@ca("đối soát SePay: gọt bỏ mọi ký tự ngăn cách rồi viết hoa")
def _():
	la("bỏ dấu gạch", dss.got("HDB-2026-01593"), "HDB202601593")
	la("bỏ dấu cách", dss.got("THE VAGABOND HOAN TIEN"), "THEVAGABONDHOANTIEN")
	la("bỏ dấu gạch chéo", dss.got("D2HLVNHF/428417"), "D2HLVNHF428417")
	la("rỗng vào rỗng ra", dss.got(""), "")
	la("None vào rỗng ra", dss.got(None), "")


@ca("đối soát SePay: BA DÒNG SAO KÊ THẬT đều phải khớp theo mã đơn")
def _():
	"""Đây là ca quan trọng nhất của cả tệp.

	Dòng thứ ba là dòng đã làm phép cũ trượt và bắt chị Dung bấm tay lúc
	14:31 ngày 24/08/2026: app bảo gõ "THE VAGABOND HOAN TIEN 92245", chị
	gõ "VAGABOND HOAN TIEN DON HANG 92245", ngân hàng chèn "MBCT" ở đầu.
	Dò cả câu thì trượt, dò mã trần thì trúng.
	"""
	for mo_ta, ma, _tien in THAT:
		dung("dòng %s khớp mã %s" % (ma, ma), dss.co_ma(mo_ta, ma))


@ca("đối soát SePay: HÀNG RÀO có cắn không, dựng lại đúng phép cũ")
def _():
	"""Hàng rào không cắn còn tệ hơn không có hàng rào.

	Phép cũ dò CẢ CÂU nội dung chuyển khoản. Ca này chạy lại đúng phép đó
	trên đúng ba dòng thật, rồi đòi bản mới phải khác.
	"""
	cau = "THE VAGABOND HOAN TIEN 92245"
	mo_ta = "MBCT VAGABOND HOAN TIEN DON HANG 92245 D237BVMB/870581"
	dung("phép CŨ dò cả câu thì TRƯỢT", not dss.co_ma(mo_ta, cau))
	dung("phép MỚI dò mã trần thì TRÚNG", dss.co_ma(mo_ta, "92245"))


@ca("đối soát SePay: chặn chữ số CẢ HAI ĐẦU, không chỉ phía sau")
def _():
	"""Đây là điểm khác duy nhất mà cũng là điểm quyết định so với bản cũ.

	Bản cũ `hoan_tien.khop_giao_dich` chỉ chặn phía sau. Chính vì thiếu chặn
	phía trước mà phiếu Pancake buộc phải dò cả câu, và dò cả câu là thứ đã
	làm dòng 92245 trượt. Chặn hai đầu gỡ được cả hai chuyện trong một nước.
	"""
	dung("mã đứng sau một chữ số thì KHÔNG khớp",
		not dss.co_ma("CHUYEN KHOAN 192252 ABC", "92252"))
	dung("mã đứng trước một chữ số thì KHÔNG khớp",
		not dss.co_ma("CHUYEN KHOAN 922521 ABC", "92252"))
	dung("mã nằm giữa hai chữ số thì KHÔNG khớp",
		not dss.co_ma("CHUYEN KHOAN 1922521 ABC", "92252"))
	# Chu cai dung sat thi VAN khop: sau khi got, moi ky tu ngan cach da bien
	# mat nen chu cai sat ma la chuyen binh thuong va vo hai.
	dung("chữ cái đứng sát mã thì VẪN khớp", dss.co_ma("HOAN TIEN DH 92252", "92252"))
	dung("mã ở cuối chuỗi vẫn khớp", dss.co_ma("HOAN TIEN 92252", "92252"))
	dung("mã ở đầu chuỗi vẫn khớp", dss.co_ma("92252 HOAN TIEN", "92252"))


@ca("đối soát SePay: mã xuất hiện HAI lần, một lần dính số một lần sạch")
def _():
	"""Chỉ xét vị trí đầu tiên là bỏ sót.

	Bản cũ dùng `find` một lần rồi kết luận. Dòng nào tình cờ có mã dính vào
	một con số ở đầu chuỗi thì cả dòng bị loại, dù phía sau có một lần xuất
	hiện sạch.
	"""
	dung("vẫn khớp nhờ lần xuất hiện thứ hai",
		dss.co_ma("REF 192252 THE VAGABOND HOAN TIEN 92252", "92252"))


@ca("đối soát SePay: mã hoá đơn vẫn khớp, kể cả khi ngân hàng làm mất dấu gạch")
def _():
	"""Sửa cái sai không được làm mất cái đúng."""
	ma = "HDB-2026-01593"
	dung("dấu gạch còn nguyên", dss.co_ma("THE VAGABOND HOAN TIEN HDB-2026-01593", ma))
	dung("ngân hàng thay gạch bằng dấu cách",
		dss.co_ma("THE VAGABOND HOAN TIEN HDB 2026 01593", ma))
	dung("ngân hàng bỏ hẳn dấu gạch",
		dss.co_ma("THEVAGABONDHOANTIENHDB202601593", ma))
	dung("mã hoá đơn KHÁC thì không khớp",
		not dss.co_ma("THE VAGABOND HOAN TIEN HDB-2026-01594", ma))
	# Ma ngan khong duoc an nham ma dai: day la bay cua ma WOO da gap.
	dung("mã ngắn không ăn nhầm mã dài",
		not dss.co_ma("THE VAGABOND HOAN TIEN HDB-2026-016041", "HDB-2026-01604"))


@ca("đối soát SePay: mã phiếu TTNB không còn ăn nhầm phiếu số dài hơn")
def _():
	"""Phép cũ ở de_nghi_chi là phép LỎNG NHẤT repo, và nguy nhất.

	Nó chỉ hỏi "chuỗi đã gọt có chứa mã đã gọt không", không chặn đầu nào.
	Mà đây là đường DUY NHẤT webhook SePay gọi thẳng, phiếu tự nhảy sang
	"Đã chi" không ai bấm nút.
	"""
	dung("phiếu 00001 KHÔNG ăn dòng của phiếu 00012",
		not dss.co_ma("THE VAGABOND TTNB-26-08-00012", "TTNB-26-08-00001"))
	# Ca CAN nhat, va la ca duy nhat phan biet duoc phep long voi phep chat:
	# ma ngan la TIEN TO cua ma dai. Hom nay Frappe danh so co dinh nam chu so
	# nen chua dung, nhung qua 99999 phieu la dung ngay, va hang rao thi
	# khong ton gi.
	dung("mã 00012 KHÔNG ăn dòng của phiếu 000123",
		not dss.co_ma("THE VAGABOND TTNB-26-08-000123", "TTNB-26-08-00012"))
	# Chung minh cai bay la THAT: dung lai dung phep long cu ngay tai day.
	long = lambda mo, ma: bool(dss.got(ma)) and dss.got(ma) in dss.got(mo)
	dung("phép LỎNG cũ thì ăn nhầm - đây là lý do phải chặn hai đầu",
		long("THE VAGABOND TTNB-26-08-000123", "TTNB-26-08-00012"))
	dung("phiếu 00012 khớp đúng dòng của nó",
		dss.co_ma("THE VAGABOND TTNB-26-08-00012", "TTNB-26-08-00012"))
	dung("ngân hàng thay gạch bằng dấu cách vẫn khớp",
		dss.co_ma("THE VAGABOND TTNB 26 08 00012", "TTNB-26-08-00012"))


@ca("đối soát SePay: mã rỗng thì KHÔNG BAO GIỜ khớp")
def _():
	"""Thà không khớp còn hơn khớp nhầm một lần tiền ra.

	Bản v292 để `ma_do_soat` trả về cả câu nội dung, nên phiếu bị lỗi cũ xoá
	mã còn trơ lại "THE VAGABOND HOAN TIEN" - một chuỗi là con của MỌI dòng
	hoàn tiền, khớp bừa vào bất kỳ dòng nào.
	"""
	dung("mã rỗng", not dss.co_ma("THE VAGABOND HOAN TIEN 92252", ""))
	dung("mã None", not dss.co_ma("THE VAGABOND HOAN TIEN 92252", None))
	dung("mã toàn ký tự lạ", not dss.co_ma("THE VAGABOND HOAN TIEN 92252", "!!!"))
	dung("mô tả rỗng", not dss.co_ma("", "92252"))


@ca("đối soát SePay: chọn mã dài trước khi hai mã cùng nằm trong một dòng")
def _():
	la("chọn mã dài", dss.tim_ma("APP26080271 xong", ["APP2608027", "APP26080271"]),
		"APP26080271")
	la("không mã nào khớp", dss.tim_ma("KHONG CO GI", ["92252", "92156"]), "")
	la("danh sách rỗng", dss.tim_ma("THE VAGABOND 92252", []), "")
	la("chọn đúng mã trong danh sách",
		dss.tim_ma("HOAN TIEN DON HANG 92245", ["92156", "92245", "92252"]), "92245")


@ca("đối soát SePay: xét một cặp phiếu và dòng sao kê ra ba kết quả")
def _():
	la("mã khớp tiền khớp",
		dss.xet("HOAN TIEN DH 92252", 705000, "92252", 705000)[0], dss.KHOP)
	la("mã khớp tiền lệch thì đẩy cho NGƯỜI xem",
		dss.xet("HOAN TIEN DH 92252", 700000, "92252", 705000)[0], dss.XEM_LAI)
	la("mã không khớp",
		dss.xet("HOAN TIEN DH 92156", 705000, "92252", 705000)[0], dss.KHONG)
	la("phiếu không có mã thì KHÔNG, tuyệt đối không đoán theo tiền",
		dss.xet("MOT DONG NAO DO", 705000, "", 705000)[0], dss.KHONG)
	la("dòng đã có chủ thì đẩy cho NGƯỜI xem",
		dss.xet("HOAN TIEN DH 92252", 705000, "92252", 705000,
			chu_cu="HT-2026-01181")[0], dss.XEM_LAI)
	# Lech mot dong van coi la khop: ngan hang khong lam tron tien Viet, nhung
	# mot dong lech la sai so lam tron cua chinh he.
	la("lệch đúng một đồng vẫn khớp",
		dss.xet("HOAN TIEN DH 92252", 705001, "92252", 705000)[0], dss.KHOP)
	la("lệch hai đồng thì phải xem lại",
		dss.xet("HOAN TIEN DH 92252", 705002, "92252", 705000)[0], dss.XEM_LAI)


@ca("đối soát SePay: câu giải thích phải nói ra CON SỐ, không nói chung chung")
def _():
	"""Người đọc phải biết lệch bao nhiêu mà không phải đi tra."""
	_kq, vi_sao = dss.xet("HOAN TIEN DH 92252", 700000, "92252", 705000)
	dung("nói số tiền trên sao kê", "700.000" in vi_sao)
	dung("nói số tiền trên phiếu", "705.000" in vi_sao)
	_kq2, vi_sao2 = dss.xet("HOAN TIEN DH 92252", 705000, "92252", 705000,
		chu_cu="HT-2026-01181")
	dung("nói rõ phiếu nào đang giữ dòng đó", "HT-2026-01181" in vi_sao2)


@ca("đối soát SePay: xếp ứng viên khớp mã lên trước, KHÔNG loại theo tiền")
def _():
	"""Loại theo tiền chính là cái bẫy của `sepay.tim_gd_vao` bản cũ.

	Nó bỏ qua mọi dòng lệch quá 2 phần trăm, nên ngân hàng trừ phí hay kế
	toán chuyển làm hai lần là đúng dòng cần tìm bị cắt mất khỏi danh sách,
	và người dùng kết luận "không có dòng nào".
	"""
	dong = [
		{"name": "A", "mo_ta": "KHACH CHUYEN TIEN", "tien": 705000},
		{"name": "B", "mo_ta": "HOAN TIEN DH 92252", "tien": 690000},
		{"name": "C", "mo_ta": "MOT DONG KHAC", "tien": 705000},
	]
	ra = dss.xep_ung_vien(dong, "92252", 705000)
	la("giữ đủ mọi dòng, không loại dòng nào", len(ra), 3)
	la("dòng khớp mã lên đầu dù lệch tiền", ra[0]["name"], "B")
	dung("dòng khớp mã được đánh dấu", ra[0]["khop_ma"] == 1)
	dung("dòng đúng tiền được đánh dấu", ra[1]["dung_tien"] == 1)
	la("lệch tính đúng", ra[0]["lech"], 15000)
	# Khong co ma de do thi khong dong nao duoc danh dau khop ma.
	ra2 = dss.xep_ung_vien(dong, "", 705000)
	dung("không mã thì không dòng nào khớp mã",
		all(r["khop_ma"] == 0 for r in ra2))


@ca("đối soát SePay: sổ đăng ký phải nhận đủ hai luồng của đợt 1")
def _():
	"""Khai thiếu thì cửa ngõ chung ném lỗi ngay chứ không im lặng bỏ qua."""
	from vagabond import de_nghi_chi  # noqa: F401
	from vagabond import hoan_tien  # noqa: F401

	dung("có luồng hoàn tiền", "hoan_tien" in dss._SO)
	dung("có luồng thanh toán nội bộ", "ttnb" in dss._SO)
	for loai in ("hoan_tien", "ttnb"):
		b = dss._SO[loai]
		dung("%s khai đủ chiều tiền" % loai, b["chieu"] in (dss.RA, dss.VAO))
		dung("%s khai hàm lấy mã dò" % loai, callable(b["ma_do"]))
		dung("%s khai hàm lấy số tiền" % loai, callable(b["so_tien"]))
		dung("%s khai bộ lọc phiếu đang chờ" % loai, bool(b["dang_cho"]))
		dung("%s khai việc làm sau khi khớp" % loai, callable(b["khi_khop"]))


@ca("đối soát SePay: mọi phép khớp cũ nay trỏ về MỘT chỗ")
def _():
	"""Đọc thẳng mã nguồn: hàm cũ nào cũng phải gọi tầng chung.

	Bốn hàm gọt chuỗi làm y hệt một việc với bốn cái tên khác nhau là bốn cơ
	hội lệch nhau, và ngày 16/08/2026 chúng đã lệch thật.
	"""
	import inspect

	from vagabond import de_nghi_chi, hoan_tien

	for ham, ten in (
		(hoan_tien.khop_giao_dich, "hoan_tien.khop_giao_dich"),
		(hoan_tien.chon_ma_khop, "hoan_tien.chon_ma_khop"),
		(hoan_tien._got, "hoan_tien._got"),
		(de_nghi_chi.khop_noi_dung, "de_nghi_chi.khop_noi_dung"),
	):
		# Doi DONG NHAP THAT chu khong chi doi chuoi "doi_soat_sepay" xuat
		# hien dau do: chu thich cua chinh cac ham nay deu nhac ten tang
		# chung, nen phep tim chuoi tron se xanh gia ngay ca khi than ham da
		# bi cheo lai phep cu. Da thu lai bang tay va no da xanh gia that.
		ma = inspect.getsource(ham)
		dung("%s thật sự nhập tầng chung" % ten,
			"from vagabond.khop_sao_ke import" in ma)


@ca("đối soát SePay: hai hàm cũ vẫn cho ĐÚNG kết quả như tầng chung")
def _():
	"""Uỷ quyền mà lệch kết quả thì tệ hơn không uỷ quyền."""
	from vagabond import de_nghi_chi, hoan_tien

	for mo_ta, ma, _tien in THAT:
		la("hoan_tien.khop_giao_dich khớp dòng %s" % ma,
			hoan_tien.khop_giao_dich(mo_ta, ma), dss.co_ma(mo_ta, ma))
	la("de_nghi_chi.khop_noi_dung chặn được phiếu số dài hơn",
		de_nghi_chi.khop_noi_dung("THE VAGABOND TTNB-26-08-00012", "TTNB-26-08-00001"),
		False)
	la("hoan_tien._got giống got chung",
		hoan_tien._got("HDB-2026-01593"), dss.got("HDB-2026-01593"))


@ca("đối soát SePay: mã dò của phiếu hoàn tiền là MÃ ĐƠN, không phải cả câu")
def _():
	"""Đổi từ v292 sang v294, và lý do nằm ở ba dòng sao kê thật."""
	from vagabond import hoan_tien

	pancake = {
		"hoa_don": "", "loai_hoan": hoan_tien.LOAI_HUY_PANCAKE,
		"ma_don_pancake": "92245",
		"noi_dung_ck": "THE VAGABOND HOAN TIEN 92245",
	}
	la("trả về mã đơn trần", hoan_tien.ma_do_soat(pancake), "92245")
	dung("mã đó khớp được dòng sao kê thật",
		dss.co_ma("MBCT VAGABOND HOAN TIEN DON HANG 92245 D237BVMB/870581",
			hoan_tien.ma_do_soat(pancake)))

	# Phieu bi loi cu xoa ma: THA KHONG KHOP CON HON KHOP NHAM.
	mat_ma = {
		"hoa_don": "", "loai_hoan": hoan_tien.LOAI_HUY_PANCAKE,
		"ma_don_pancake": "", "noi_dung_ck": "THE VAGABOND HOAN TIEN ",
	}
	la("mất mã đơn thì trả về rỗng", hoan_tien.ma_do_soat(mat_ma), "")

	tra_hang = {"hoa_don": "HDB-2026-01593", "loai_hoan": "Tra hang"}
	la("phiếu trả hàng vẫn dò theo mã hoá đơn",
		hoan_tien.ma_do_soat(tra_hang), "HDB-2026-01593")
