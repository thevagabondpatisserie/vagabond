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


@ca("SePay: mã mới không gạch vẫn khớp mã cũ, không nhầm số liền kề")
def _ma_khong_gach():
	from vagabond.de_nghi_chi import noi_dung_ck
	ma = "TTNB-26-08-00001"
	nd = noi_dung_ck(ma)
	la("chuỗi mới", nd, "THE VAGABOND TTNB260800001")
	dung("khớp mã gốc", dss.co_ma(nd, ma))
	dung("không ăn mã dài hơn", not dss.co_ma(nd + "2", ma))


@ca("SePay: chip theo mapping, nhãn chỉ bốn số cuối, không trả tài khoản chưa nối")
def _chip_mapping():
	from unittest.mock import patch
	from vagabond import sepay
	with patch.object(sepay, "_ban_do", lambda: {"12345678": "A"}), patch.object(dss.frappe, "get_all", lambda *a, **k: [
		{"name":"A", "bank":"MB", "bank_account_no":"12345678", "disabled":0},
		{"name":"B", "bank":"Ngân hàng B", "bank_account_no":"87654321", "disabled":0}]):
		nhan, chip, chua = dss.nhan_tai_khoan()
		la("chỉ mapped có chip", [x['ma'] for x in chip], ['A'])
		la("đuôi bốn số", nhan['A'], 'MB · 5678')
		la("không còn chẩn đoán chưa nối", chua, [])


@ca("SePay: lọc tài khoản trước trần 500 giữ dòng tài khoản ít giao dịch")
def _loc_truoc_tran_323():
	from unittest.mock import patch
	du_lieu = [dict(name='DONG-%s' % i, bank_account='DONG', withdrawal=1) for i in range(501)] + [dict(name='IT-1', bank_account='IT', withdrawal=2)]
	def lay(dt, **kw):
		ds = du_lieu
		for cot, phep, gia in kw['filters']:
			if cot == 'bank_account':
				ds = [r for r in ds if r[cot] == gia]
		return [dict(r) for r in ds[:kw['limit_page_length']]]
	with patch.object(dss.frappe, 'get_all', lay), patch.object(dss, 'nhan_tai_khoan', return_value=({}, [], [])):
		la('dòng ít vẫn tới cửa đối soát', [r['name'] for r in dss.dong_sao_ke(dss.RA, tu_ngay='2026-09-15', tai_khoan='IT')], ['IT-1'])


@ca("SePay: cửa đọc không giấu dòng, nhãn đọc một lần và truyền xuống query")
def _quyen_chan_doan_323():
	from unittest.mock import patch
	import sys
	from types import SimpleNamespace
	ban = dict(doctype='TEST', ma_do=lambda d: 'TEST', so_tien=lambda d: 1, chieu=dss.RA, ten_man='TEST', truong_gd='gd')
	# Bỏ vòng lặp hai vai: từ #327 danh sách "chưa nối" không còn được trả về
	# nữa nên hai vai cho cùng một kết quả, lặp chỉ làm ca kiểm trông như có
	# kiểm quyền trong khi nó không kiểm gì. Quyền của màn này do _kiem_quyen lo.
	for roles in [['Sales User'], ['Accounts User']]:
		with patch.dict(sys.modules, {'vagabond.ban_hang': SimpleNamespace(_kiem_quyen=lambda: None)}), patch.object(dss, 'nap_so'), patch.object(dss, '_ban', return_value=ban), patch.object(dss.frappe, 'get_doc', return_value={}), patch.object(dss.frappe, 'get_roles', return_value=roles), patch.object(dss, 'da_chiem', return_value={}), patch.object(dss, 'nhan_tai_khoan', return_value=({'TK': 'Nhãn'}, [{'ma':'TK','nhan':'Nhãn'}], ['Chưa nối'])) as nhan, patch.object(dss, 'dong_sao_ke', return_value=[]) as dong:
			kq = dss.ung_vien('ttnb', 'TEST', tai_khoan='TK')
			la('không còn phát danh sách chưa nối', kq['chua_noi_sepay'], [])
			la('không giấu tài khoản chưa nối ở cửa đọc', dong.call_args.kwargs.get('tai_khoan_cho_phep'), None)
			la('lọc truyền xuống query', dong.call_args.kwargs['tai_khoan'], 'TK')
			la('nhãn dùng lại', dong.call_args.kwargs['nhan'], {'TK': 'Nhãn'})
			la('chỉ đọc nhãn một lần', nhan.call_count, 1)


@ca("#325: chỉ mapping enabled có chip; nhãn lịch sử vẫn đủ")
def _tai_khoan_325():
	from unittest.mock import patch
	from vagabond import sepay
	ds = [dict(name='CT', bank='MB - Ngân hàng TMCP Quân đội', bank_account_no='12340615'),
		dict(name='CN', bank='ACB', bank_account_no='99996066', party='Nguoi', party_type='Supplier'),
		dict(name='NCC', bank='NCC', bank_account_no='1111', party='NCC'),
		dict(name='KH', bank='KH', bank_account_no='2222', party='KH'),
		dict(name='TAT', bank='MB', bank_account_no='3333', disabled=1)]
	with patch.object(sepay, '_ban_do', return_value={'1':'CT','2':'CN','3':'TAT'}), patch.object(dss.frappe, 'get_all', return_value=ds):
		nhan, chip, chua = dss.nhan_tai_khoan()
		la('hai tài khoản mapped enabled', [x['ma'] for x in chip], ['CT','CN'])
		la('nhãn gọn', chip[0]['nhan'], 'MB · 0615')
		la('tên đầy đủ', chip[0]['ten_day_du'], ds[0]['bank'])
		la('giữ nhãn lịch sử', nhan['CT'], 'MB - Ngân hàng TMCP Quân đội · 0615')
		la('không phát danh sách ngoài mapping', chua, [])
	la('cắt tên dài giữ đuôi', dss.nhan_gon_ngan_hang('ABCDEFGHIJKLMNOPQ', '12345678'), 'ABCDEFGHIJKLM… · 5678')


@ca("#327: cửa đọc KHÔNG được lọc theo phạm vi tài khoản, chỉ lọc theo chip người chọn")
def _sao_ke_mapping_325():
	"""Ca này chặn đường lỗi ngày 14/09/2026, phiếu TTNB-26-09-02113.

	Hôm đó dòng sao kê có thật bị một bộ lọc phạm vi giấu khỏi bảng, và màn
	báo là không có giao dịch nào. Luật sau #327: tầng chung chỉ được lọc theo
	chip mà NGƯỜI chọn, tuyệt đối không tự thêm bộ lọc phạm vi nào khác. Ai
	thêm lại một bộ lọc như vậy thì ca này phải đổ.
	"""
	import inspect
	from unittest.mock import patch
	tham_so = list(inspect.signature(dss.dong_sao_ke).parameters)
	la('không còn tham số phạm vi', [x for x in tham_so if 'cho_phep' in x], [])
	with patch.object(dss.frappe, 'get_all', return_value=[]) as lay:
		dss.dong_sao_ke(dss.RA, nhan={})
		loc = lay.call_args.kwargs['filters']
		la('không tự lọc tài khoản', [x for x in loc if x[0] == 'bank_account'], [])
		la('giữ limit', lay.call_args.kwargs['limit_page_length'], 500)
		lay.reset_mock()
		dss.dong_sao_ke(dss.RA, nhan={}, tai_khoan='CT')
		loc = lay.call_args.kwargs['filters']
		dung('chip người chọn vẫn lọc được', ['bank_account', '=', 'CT'] in loc)


@ca('#327: cửa ghi đọc lại mapping, chặn API ngoài phạm vi trước mọi ghi')
def _ghi_mapping_327():
	from unittest.mock import patch, Mock
	from types import SimpleNamespace
	import sys
	ban = dict(doctype='TEST', chieu=dss.RA, so_tien=lambda d: 100, truong_gd='gd', truong_nguoi='nguoi', khi_khop=None)
	g = dict(name='GD', docstatus=1, withdrawal=100, deposit=0, bank_account='CT')
	class Chan(Exception):
		pass
	for chip, duoc in [([], False), ([{'ma':'KHAC'}], False), ([{'ma':'CT'}], True)]:
		db = SimpleNamespace(get_value=Mock(return_value=g), set_value=Mock(), commit=Mock())
		with patch.dict(sys.modules, {'vagabond.ban_hang': SimpleNamespace(_kiem_quyen=lambda:None)}), patch.object(dss,'nap_so'), patch.object(dss,'_ban',return_value=ban), patch.object(dss.frappe,'get_doc',return_value={}), patch.object(dss.frappe,'db',db), patch.object(dss.frappe,'session',SimpleNamespace(user='ke-toan')), patch.object(dss.frappe,'throw',side_effect=Chan), patch.object(dss,'_loi_giao_dich',return_value=None), patch.object(dss,'da_chiem',return_value={}), patch.object(dss,'nhan_tai_khoan',return_value=({},chip,[])) as nap:
			bi_chan=False
			try:
				dss.khop_tay('ttnb','PHIEU','GD')
			except Chan:
				bi_chan=True
			la('kết quả theo mapping hiện tại', bi_chan, not duoc)
			la('đọc lại mapping tại đường ghi', nap.call_count, 1)
			la('không ghi ngoài mapping', db.set_value.call_count, int(duoc))
			la('không commit ngoài mapping', db.commit.call_count, int(duoc))


@ca('#327: tự động dùng cùng phạm vi mapping trước khi ghi')
def _tu_dong_mapping_327():
	from unittest.mock import patch, Mock
	from types import SimpleNamespace
	import sys
	ban = dict(doctype='TEST', dang_cho={}, ma_do=lambda d:'TEST', so_tien=lambda d:100, chieu=dss.RA, truong_gd='gd', khi_khop=None)
	for chip, duoc in [([],False), ([{'ma':'CT'}],True)]:
		db=SimpleNamespace(set_value=Mock(),commit=Mock())
		with patch.dict(sys.modules, {'vagabond.ban_hang':SimpleNamespace(_kiem_quyen=lambda:None)}), patch.object(dss,'nap_so'), patch.object(dss,'_ban',return_value=ban), patch.object(dss.frappe,'get_all',return_value=[{'name':'P'}]), patch.object(dss.frappe,'get_doc',return_value=SimpleNamespace(name='P')), patch.object(dss.frappe,'db',db), patch.object(dss,'dong_sao_ke',return_value=[dict(name='GD',mo_ta='TEST',tien=100,bank_account='CT')]), patch.object(dss,'da_chiem',return_value={}), patch.object(dss,'xet',return_value=(dss.KHOP,'')), patch.object(dss,'nhan_tai_khoan',return_value=({},chip,[])):
			kq=dss.tu_dong('ttnb')
			la('chỉ ghi khi mapped',db.set_value.call_count,int(duoc))
			la('đếm khớp đúng',kq['da_khop'],int(duoc))
			la('ngoài mapping phải có lý do',bool(kq['xem_lai']),not duoc)


@ca('#327 dòng dùng được luôn trước dòng chưa nối dù lệch tiền')
def _xep_mapping_327():
	ra=ksk.xep_ung_vien([dict(name='chan',tien=100,mo_ta='TEST',dung_duoc=0),dict(name='duoc',tien=90,mo_ta='',dung_duoc=1)],'TEST',100)
	la('ưu tiên dùng được', [r['name'] for r in ra], ['duoc','chan'])


@ca('#327: BA duong ghi tu dong cu cung phai qua phep kiem pham vi tai khoan')
def _ba_duong_ghi_tu_dong_327():
	"""Finding cua Codex ngay 16/09/2026, tai hien duoc va da sua.

	Phep kiem pham vi ban dau chi cam o khop_tay va tu_dong. Ba duong ghi tu
	dong cu van gan tien thang bang set_value: quet theo gio cua lenh chi noi
	bo, duong webhook goi ngay khi co giao dich, va quet theo gio cua phieu
	hoan tien. Mot dong thuoc tai khoan ngoai pham vi vi the van danh dau
	duoc mot phieu la da chi, trong khi cung dong do bi tu choi o duong khop
	tay. Cung mot giao dich cho hai ket qua trai nguoc tuy nguoi bam nut nao.

	Ca nay dung dung chuoi thao tac cua tung duong va khang dinh KHONG co
	set_value nao chay khi tai khoan ngoai pham vi, va van ghi dung mot lan
	khi tai khoan hop le. Dung doi thanh phep do chuoi: dieu 16.
	"""
	import sys
	from contextlib import ExitStack
	from types import SimpleNamespace
	from unittest.mock import Mock, patch

	from vagabond import de_nghi_chi as dnc
	from vagabond import hoan_tien as ht

	gd = dict(name='GD', description='THE VAGABOND TTNB', reference_number='',
		withdrawal=100.0, date='2026-09-14', bank_account='CT')
	phieu = dict(name='TTNB-1', tong_tien=100.0, so_tien=100.0)

	def _db():
		return SimpleNamespace(sql=Mock(return_value=[dict(gd)]), set_value=Mock(),
			commit=Mock(), get_value=Mock(return_value=dict(gd)))

	for chip, ghi_duoc in [([], False), ([{'ma': 'CT'}], True)]:
		nhan_gia = ({'CT': 'MB - 0615'}, chip, [])

		# 1. Quet theo gio cua lenh chi noi bo.
		db = _db()
		with ExitStack() as g:
			g.enter_context(patch.dict(sys.modules, {'vagabond.ban_hang': SimpleNamespace(_kiem_quyen=lambda: None)}))
			g.enter_context(patch.object(dnc, '_phieu_cho_chi', return_value=[dict(phieu)]))
			g.enter_context(patch.object(dnc.frappe, 'db', db))
			g.enter_context(patch.object(dnc, '_gd_da_chiem_ttnb', return_value={}))
			g.enter_context(patch.object(dnc, '_loi_nguon_chi_ttnb', return_value=""))
			g.enter_context(patch.object(dnc, 'khop_noi_dung', return_value=True))
			g.enter_context(patch.object(dnc, '_het_viec', Mock()))
			g.enter_context(patch.object(dss, 'nhan_tai_khoan', return_value=nhan_gia))
			kq = dnc.doi_soat(30)
		la('quet theo gio lenh chi: so lan ghi', db.set_value.call_count, int(ghi_duoc))
		la('quet theo gio lenh chi: so phieu khop', kq['da_khop'], int(ghi_duoc))
		if not ghi_duoc:
			dung('dong bi chan van bay len cho nguoi xem kem ly do',
				bool(kq['xem_xet']) and bool(kq['xem_xet'][0].get('vi_sao')))

		# 2. Duong webhook, goi ngay khi ngan hang bao co giao dich.
		db = _db()
		with ExitStack() as g:
			g.enter_context(patch.object(dnc.frappe, 'db', db))
			g.enter_context(patch.object(dnc, '_loi_nguon_chi_ttnb', return_value=""))
			g.enter_context(patch.object(dnc, '_gd_da_chiem_ttnb', return_value={}))
			g.enter_context(patch.object(dnc, '_phieu_cho_chi', return_value=[dict(phieu)]))
			g.enter_context(patch.object(dnc, 'khop_noi_dung', return_value=True))
			g.enter_context(patch.object(dnc, '_het_viec', Mock()))
			g.enter_context(patch.object(dss, 'nhan_tai_khoan', return_value=nhan_gia))
			dnc.khi_co_giao_dich('GD')
		la('duong webhook: so lan ghi', db.set_value.call_count, int(ghi_duoc))

		# 3. Quet theo gio cua phieu hoan tien.
		db = _db()
		with ExitStack() as g:
			g.enter_context(patch.dict(sys.modules, {'vagabond.ban_hang': SimpleNamespace(_kiem_quyen=lambda: None)}))
			g.enter_context(patch.object(ht.frappe, 'db', db))
			g.enter_context(patch.object(ht.frappe, 'get_all', return_value=[dict(name='HT-1', hoa_don='HD-1', so_tien=100.0)]))
			g.enter_context(patch.object(ht, 'ma_do_soat', return_value='HD-1'))
			g.enter_context(patch.object(ht, '_gd_da_chiem', return_value={}))
			g.enter_context(patch.object(ht, 'khop_giao_dich', return_value=True))
			g.enter_context(patch.object(ht.frappe, 'get_doc', Mock()))
			g.enter_context(patch.object(ht, '_sinh_chung_tu', return_value={'bo_qua': 1}))
			g.enter_context(patch.object(dss, 'nhan_tai_khoan', return_value=nhan_gia))
			kq = ht.doi_soat()
		la('quet theo gio hoan tien: so lan ghi', db.set_value.call_count, int(ghi_duoc))
		la('quet theo gio hoan tien: so ho so khop', kq['da_khop'], int(ghi_duoc))
		if not ghi_duoc:
			dung('hoan tien: dong bi chan co ly do',
				bool(kq['xem_xet']) and bool(kq['xem_xet'][0].get('vi_sao')))


@ca('#327 hoàn tiền trực tiếp: sao kê thật, mapping active, không tin payload')
def _hoan_truc_tiep_327():
	import sys
	from contextlib import ExitStack
	from types import SimpleNamespace
	from unittest.mock import Mock, patch
	from vagabond import hoan_tien as ht
	gd = dict(name='GD', bank_account='CT', description='HOAN TIEN HD-1',
		reference_number='', withdrawal=100, docstatus=1)
	for ten, dong, chip, ma, khop in [
		('thiếu mã', gd, [{'ma':'CT'}], '', False),
		('không có sao kê', None, [{'ma':'CT'}], 'GD', False),
		('đã hủy', dict(gd, docstatus=2), [{'ma':'CT'}], 'GD', False),
		('tiền vào', dict(gd, withdrawal=0), [{'ma':'CT'}], 'GD', False),
		('mapping tắt', gd, [], 'GD', False),
		('đã nối', gd, [{'ma':'CT'}], 'GD', True),
		('payload giả không sửa được tiền', dict(gd, withdrawal=200), [{'ma':'CT'}], 'GD', False),
	]:
		db=SimpleNamespace(get_value=Mock(return_value=dong), set_value=Mock(), commit=Mock())
		# v523 (Codex #363 vòng 5): sepay_tien_ra sinh chứng từ qua MỘT cửa có
		# khoá và chặn thiếu phiếu chi (_sinh_va_ghi_loi), không gọi thẳng
		# _sinh_chung_tu nữa. Ca này vẫn chốt đúng ý #327: chỉ khớp thật mới sinh.
		sinh=Mock(return_value={'phieu_chi':'APP-1'})
		with ExitStack() as g:
			g.enter_context(patch.dict(sys.modules, {'vagabond.ban_hang':SimpleNamespace(_kiem_quyen=lambda:None)}))
			g.enter_context(patch.object(ht.frappe,'db',db))
			g.enter_context(patch.object(ht.frappe,'get_all',return_value=[dict(name='HT-1',so_tien=100)]))
			g.enter_context(patch.object(ht.frappe,'get_doc',Mock()))
			g.enter_context(patch.object(ht,'ma_do_soat',return_value='HD-1'))
			chon=g.enter_context(patch.object(ht,'chon_ma_khop',return_value='HD-1'))
			g.enter_context(patch.object(ht,'_gd_da_chiem',return_value={}))
			g.enter_context(patch.object(ht,'_sinh_va_ghi_loi',sinh))
			g.enter_context(patch.object(dss,'nhan_tai_khoan',return_value=({'CT':'MB'},chip,[])))
			kq=ht.sepay_tien_ra(mo_ta='PAYLOAD GIA',so_tien=100,ma_gd=ma)
		la(ten+' khớp',kq['khop'],int(khop))
		la(ten+' ghi DB',db.set_value.call_count,int(khop))
		la(ten+' sinh chứng từ',sinh.call_count,int(khop))
		la(ten+' commit',db.commit.call_count,int(khop))
		if not khop: dung(ten+' lý do',bool(kq.get('vi_sao')))
		if chon.called: la(ten+' dùng nội dung DB',chon.call_args[0][0],gd['description']+' ')


@ca("#328: ngày giảm dần, gợi ý mã/tiền và tham chiếu đứng riêng")
def _thu_tu_328():
	dong = [dict(name='cu',date='2026-09-01',tien=102),
		dict(name='moi',date='2026-09-16',tien=200),
		dict(name='ma',date='2026-08-10',tien=100,reference_number='TTNB-1')]
	la('gợi ý rồi mới nhất, không độ lệch', [r['name'] for r in ksk.xep_ung_vien(dong,'TTNB-1',100)], ['ma','moi','cu'])
	la('chế độ mới nhất', [r['name'] for r in ksk.xep_ung_vien(dong,'TTNB-1',100,'moi_nhat')], ['moi','cu','ma'])


@ca("#328: whitelist giữ nguồn cá nhân/đã có chủ, đủ 601 dòng và trang tiếp")
def _ung_vien_328():
	from unittest.mock import patch
	from contextlib import ExitStack
	from types import SimpleNamespace
	import sys
	ban = dict(doctype='TEST', ma_do=lambda d:'TEST', so_tien=lambda d:100,
		chieu=dss.RA, ten_man='TEST', truong_gd='gd', loi_giao_dich=lambda g:'Nguồn cá nhân' if g['bank_account']=='CN' else '')
	ds = [dict(name='GD%04d'%i,date='2026-09-16',withdrawal=200,description='Nội dung',bank_account='CT') for i in range(600)]
	ds += [dict(name='DICH',date='2026-08-10',withdrawal=100,description='',reference_number='TEST',bank_account='CN')]
	def lay(dt, **kw):
		ra = ds
		for cot, phep, gia in kw['filters']:
			if cot=='bank_account': ra=[r for r in ra if r[cot]==gia]
		n=kw['limit_page_length']
		return [dict(r) for r in (ra[:n] if n else ra)]
	with ExitStack() as st:
		st.enter_context(patch.dict(sys.modules, {'vagabond.ban_hang':SimpleNamespace(_kiem_quyen=lambda:None)}))
		for ten, value in [('nap_so',None),('_ban',ban),('da_chiem',{'GD0001':'PHIEU-KHAC'}),('nhan_tai_khoan',({'CN':'MB · 0615'},[{'ma':'CT'},{'ma':'CN'}],[]))]:
			st.enter_context(patch.object(dss,ten,return_value=value))
		st.enter_context(patch.object(dss.frappe,'get_doc',return_value={}))
		st.enter_context(patch.object(dss.frappe,'get_all',side_effect=lay))
		kq=dss.ung_vien('ttnb','P',tai_khoan='CN')
		la('MB có dòng, không rỗng giả',len(kq['rows']),1)
		la('giữ chặn nguồn',kq['rows'][0]['dung_duoc'],0)
		la('lý do',kq['rows'][0]['vi_sao_khong'],'Nguồn cá nhân')
		kq=dss.ung_vien('ttnb','P',tu_khoa='TEST')
		la('tìm qua trần 500',[r['name'] for r in kq['rows']],['DICH'])
		kq=dss.ung_vien('ttnb','P',bat_dau=540)
		la('không mất dòng',kq['tong'],601)
		la('còn trang cuối',kq['con_nua'],1)
		kq=dss.ung_vien('ttnb','P',tu_khoa='GD0001')
		dung('chủ cũ được giải thích','PHIEU-KHAC' in kq['rows'][0]['vi_sao_khong'])


@ca("#328: tự động gặp nguồn cá nhân báo xem lại, không ghi")
def _tu_dong_328():
	from unittest.mock import patch, Mock
	from contextlib import ExitStack
	from types import SimpleNamespace
	import sys
	ban=dict(doctype='TEST',chieu=dss.RA,ma_do=lambda d:'TEST',so_tien=lambda d:100,
		dang_cho={},truong_gd='gd',khi_khop=None,loi_giao_dich=lambda g:'Nguồn cá nhân')
	db=Mock()
	with ExitStack() as st:
		st.enter_context(patch.dict(sys.modules,{'vagabond.ban_hang':SimpleNamespace(_kiem_quyen=lambda:None)}))
		for ten,val in [('nap_so',None),('_ban',ban),('da_chiem',{}),('dong_sao_ke',[dict(name='GD',mo_ta='TEST',tien=100)])]:st.enter_context(patch.object(dss,ten,return_value=val))
		st.enter_context(patch.object(dss.frappe,'db',db))
		st.enter_context(patch.object(dss.frappe,'get_all',return_value=[{'name':'P'}]))
		st.enter_context(patch.object(dss.frappe,'get_doc',return_value=SimpleNamespace(name='P')))
		kq=dss.tu_dong('ttnb','P')
		la('không khớp',kq['da_khop'],0)
		la('không set giá trị',db.set_value.call_count,0)
		la('giải thích',kq['xem_lai'][0]['vi_sao'],'Nguồn cá nhân')
