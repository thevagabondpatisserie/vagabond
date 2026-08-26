# -*- coding: utf-8 -*-
"""Kiem thu: hoa don hang bieu tang khach VIP (v312).

Anh Viet dat bai 26/08/2026. Bo ca kiem nay chot BON quyet dinh, ca bon
deu la loai doc lai se thay "ky ky" va co nguoi sua nguoc lai:

  1. KHONG giam 100%. De bai viet vay, nhung luat hang bieu tang bat hoa
     don phai ghi gia ban va thue suat that. Anh Viet chot 26/08/2026 di
     duong dung luat.
  2. KHONG dung o write_off cua Sales Invoice. Da do ma nguon ERPNext v16:
     `allow_write_off_only_on_pos` xoa trang o do neu khong phai hoa don
     quay, va `make_write_off_gl_entry` chi sinh but toan khi is_pos bat.
  3. Moi dong tren to phai nam trong danh sach qua da duyet. Khong tron
     hang ban tien vao cung to voi hang tang.
  4. Hoa don qua KHONG tich diem thanh vien.

Ca ghi so o day cham GL Entry (but toan gat cong no), nen bo kiem tang
khung nay KHONG DU. Phai chay bo kiem tich hop tren site that sau deploy.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.qua_tang_hoa_don import (
	GHI_CHU_QUA, TT_CHO_TANG, TT_DA_TANG, TT_DOT_CHAY,
	dong_but_toan, loi_mon, loi_phieu, them_ghi_chu,
)
from vagabond.tang_qua import (
	COT_DAN, O_KHONG_CHEP, doc_dong_dan, ma_dot_moi, ma_dot_tu_dip,
	tach_dan, ten_dot_goi_y, ten_dot_moi,
)

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def chi_phan_ma(nguon):
	"""Bo chu thich va docstring khoi mot tep Python. THUAN.

	Cung ham voi thu_tiec_b2b, va cung ly do: cac ca duoi day soi xem ma
	nguon co dung mot thu bi cam khong, ma chinh doan GIAI THICH VI SAO
	khong dung thu do lai chua dung chu bi cam. Soi ca chu thich thi nguoi
	viet bi ep phai xoa loi giai thich di.
	"""
	import tokenize

	ra = []
	dau_khoi = {tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
		tokenize.DEDENT, tokenize.ENCODING}
	truoc = tokenize.NEWLINE
	for tk in tokenize.generate_tokens(io.StringIO(nguon).readline):
		if tk.type == tokenize.COMMENT:
			continue
		if tk.type == tokenize.STRING and truoc in dau_khoi:
			truoc = tokenize.STRING
			continue
		if tk.type not in (tokenize.NL, tokenize.INDENT, tokenize.DEDENT):
			truoc = tk.type
		ra.append(tk.string)
	return "\n".join(ra)


MA = _doc("qua_tang_hoa_don.py")
MA_CODE = chi_phan_ma(MA)
# `chi_phan_ma` tra ve TUNG TOKEN moi dong mot. Nen tim mot cum nhieu token
# thi phai tim theo dung dang do, khong tim theo cach nguoi ta viet ra.
MA_TOKEN = "\n" + MA_CODE + "\n"


def co_cum(*token):
	"""Chuoi token nay co xuat hien lien tiep trong ma nguon khong."""
	return ("\n" + "\n".join(token) + "\n") in MA_TOKEN
MA_HOOK = _doc("hooks.py")
# Ban da bo chu thich: cac ca "khong con" ben duoi phai soi vao MA THAT,
# khong soi vao doan giai thich vi sao da go.
MA_HOOK_CODE = chi_phan_ma(MA_HOOK)
MA_KHACH = chi_phan_ma(_doc("khach_hang.py"))
MA_CUA = _doc("khung", "kiem_thu", "thu_cua_ngo.py")
MA_TRUONG = _doc("truong_tu_them.py")
MA_GIAO = _doc("giao_viec.py")
MA_JS = _doc("public", "js", "bep", "34-crm-tang-qua.js")


def _phieu(**k):
	"""Mot phieu qua hop le, cac ca sua tung o mot de soi tung luat."""
	p = {
		"name": "TQV-2026-00007",
		"dot": "TRUNGTHU-2026",
		"dot_trang_thai": TT_DOT_CHAY,
		"khach": "KH-0001",
		"tt_tang": TT_CHO_TANG[0],
		"huy": 0,
		"hoa_don": "",
	}
	p.update(k)
	return p


# ------------------------------------------------------- ghi chu hang tang


@ca("qua tang: ghi chu hang tang noi dung MOT lan, khong noi chong")
def _():
	# Ham nay chay o before_submit, ma mot to co the bi huy roi sua roi ghi
	# so lai. Noi mu thi dien giai dai dan ra va to in ra nhin nhu loi may.
	mot = them_ghi_chu("Bánh Trung thu hộp 4 bánh")
	la("nối lần đầu", mot, "Bánh Trung thu hộp 4 bánh " + GHI_CHU_QUA)
	la("nối lần hai không đổi gì", them_ghi_chu(mot), mot)
	la("nối lần ba vẫn không đổi", them_ghi_chu(them_ghi_chu(mot)), mot)


@ca("qua tang: dien giai rong thi ghi chu dung mot minh, khong co dau cach thua")
def _():
	for xau in ("", None, "   "):
		la("diễn giải %r" % (xau,), them_ghi_chu(xau), GHI_CHU_QUA)


@ca("qua tang: cau ghi chu dung NGUYEN VAN cua nghiep vu thue")
def _():
	# Chu nay in len to hoa don gui khach va gui co quan thue. Doi mot chu
	# la khac voi huong dan, nen chot cung o day.
	la("nguyên văn", GHI_CHU_QUA, "(Hàng tặng không thu tiền)")


# --------------------------------------------------- hang rao chong gian lan


@ca("chong gian lan: phieu dung, dot dang chay, dung khach thi KHONG loi")
def _():
	la("không lỗi nào", loi_phieu(_phieu(), "KH-0001", None), [])


@ca("chong gian lan: khong co phieu thi chan")
def _():
	dung("phiếu rỗng bị chặn", len(loi_phieu(None, "KH-0001", None)) == 1)
	dung("tự điển rỗng cũng bị chặn", len(loi_phieu({}, "KH-0001", None)) == 1)


@ca("chong gian lan: dot chua Dang chay thi chan")
def _():
	# Day la cho de bi bo qua nhat. Dot vua nhan ban cho mua sau dang o
	# trang thai Nhap, chua ai soat dong nao, ma neu cho xuat thi ca danh
	# sach 347 khach cua mua truoc lap tuc xuat duoc qua.
	for tt in ("Nhap", "Da dong", "", None):
		loi = loi_phieu(_phieu(dot_trang_thai=tt), "KH-0001", None)
		dung("đợt %r bị chặn" % (tt,), any("Đang chạy" in x for x in loi))


@ca("chong gian lan: phieu da huy thi chan")
def _():
	loi = loi_phieu(_phieu(huy=1), "KH-0001", None)
	dung("phiếu huỷ bị chặn", any("đã bị huỷ" in x for x in loi))


@ca("chong gian lan: khach tren to khac khach tren phieu thi chan")
def _():
	# Chinh la cau anh Viet dat ra: nhan vien tu y tang banh roi bao la
	# tang khach VIP. Phieu cua khach A khong dung cho hoa don khach B.
	loi = loi_phieu(_phieu(), "KH-9999", None)
	dung("lệch khách bị chặn", any("phải là một người" in x for x in loi))


@ca("chong gian lan: phieu chua gan khach trong he thi chan")
def _():
	# Phieu khong gan khach thi khong the doi chieu voi ai, tuc la hang rao
	# tu vo hieu. Chan thang thay vi de lot.
	loi = loi_phieu(_phieu(khach=""), "KH-0001", None)
	dung("phiếu không có khách bị chặn", any("chưa gắn khách" in x for x in loi))


@ca("chong nhan hai lan: phieu da co hoa don khac thi chan")
def _():
	loi = loi_phieu(_phieu(tt_tang=TT_DA_TANG, hoa_don="ACC-SINV-2026-00099"),
		"KH-0001", None)
	dung("đã tặng rồi bị chặn", any("một lần" in x.lower() for x in loi))


@ca("chong nhan hai lan: ghi so LAI dung to cu thi KHONG chan")
def _():
	# Huy roi ghi so lai chinh to do la chuyen that. Chan o day thi ke toan
	# khong bao gio sua lai duoc mot to hoa don qua.
	la("cùng tờ thì đi qua",
		loi_phieu(_phieu(tt_tang=TT_DA_TANG, hoa_don="ACC-SINV-2026-00099"),
			"KH-0001", "ACC-SINV-2026-00099"),
		[])


@ca("chong nhan hai lan: trang thai Da tang ma chua co hoa don van chan")
def _():
	loi = loi_phieu(_phieu(tt_tang=TT_DA_TANG), "KH-0001", None)
	dung("Đã tặng tay cũng bị chặn", any("Đã tặng" in x for x in loi))


@ca("chong gian lan: trang thai Dang xu ly van xuat duoc")
def _():
	la("đang xử lý đi qua", loi_phieu(_phieu(tt_tang="Dang xu ly"), "KH-0001", None), [])


# ------------------------------------------------ mon tren to phai duoc duyet


@ca("chong gian lan: mon ngoai danh sach duyet thi chan")
def _():
	loi = loi_mon(
		[{"ma": "TP0001", "so_luong": 1}, {"ma": "TP0999", "so_luong": 1}],
		{"TP0001": 1},
	)
	dung("món lạ bị chặn", any("TP0999" in x for x in loi))
	dung("chỉ một câu lỗi", len(loi) == 1)


@ca("chong gian lan: vuot so luong da duyet thi chan")
def _():
	loi = loi_mon([{"ma": "TP0001", "so_luong": 5}], {"TP0001": 2})
	dung("vượt số lượng bị chặn", any("xuất 5" in x and "duyệt 2" in x for x in loi))


@ca("chong gian lan: cung mot mon nam hai dong thi CONG DON roi moi so")
def _():
	# Neu so tung dong rieng thi moi dong deu lot ma tong lai vuot. Day la
	# duong lach de nhat cua ca hang rao.
	loi = loi_mon(
		[{"ma": "TP0001", "so_luong": 2}, {"ma": "TP0001", "so_luong": 3}],
		{"TP0001": 4},
	)
	dung("cộng dồn rồi mới chặn", any("xuất 5" in x for x in loi))
	la("đúng bằng mức duyệt thì qua",
		loi_mon([{"ma": "TP0001", "so_luong": 2}, {"ma": "TP0001", "so_luong": 2}],
			{"TP0001": 4}),
		[])


@ca("chong gian lan: xuat it hon so duyet thi cho qua")
def _():
	la("xuất ít hơn được", loi_mon([{"ma": "TP0001", "so_luong": 1}], {"TP0001": 3}), [])


@ca("chong gian lan: to khong co dong nao thi chan")
def _():
	dung("tờ rỗng bị chặn", len(loi_mon([], {"TP0001": 1})) == 1)


# ---------------------------------------------------- but toan gat cong no


@ca("but toan qua: hai dong, can bang, dung chieu No chi phi Co cong no")
def _():
	d = dong_but_toan("6418 - Chi phí bằng tiền khác - TV",
		"131 - Phải thu khách hàng - TV", "KH-0001", 1_320_000, "ACC-SINV-2026-00001")
	la("đúng hai dòng", len(d), 2)
	la("nợ chi phí", d[0]["debit_in_account_currency"], 1_320_000)
	la("có công nợ", d[1]["credit_in_account_currency"], 1_320_000)
	la("cân",
		d[0]["debit_in_account_currency"] - d[1]["credit_in_account_currency"], 0)


@ca("but toan qua: dong cong no phai TRO NGUOC ve dung so hoa don")
def _():
	# Khong tro nguoc thi ERPNext tru lung tung sang to khac cua cung khach,
	# va to hoa don qua thi treo cong no mai mai.
	d = dong_but_toan("6418", "131", "KH-0001", 500_000, "ACC-SINV-2026-00042")
	la("loại chứng từ", d[1]["reference_type"], "Sales Invoice")
	la("số chứng từ", d[1]["reference_name"], "ACC-SINV-2026-00042")
	la("bên là khách", d[1]["party_type"], "Customer")
	la("đúng khách", d[1]["party"], "KH-0001")


@ca("but toan qua: khong con no thi KHONG lap but toan rong")
def _():
	for tien in (0, None, -5):
		la("tiền %r" % (tien,), dong_but_toan("6418", "131", "KH-0001", tien, "X"), [])


# ------------------------------------------------- chot cac quyet dinh trong ma


@ca("qua tang: KHONG ap giam 100 phan tram, vi giam la thue ve 0 theo")
def _():
	# De bai viet "ap Discount 100%". Anh Viet chot 26/08/2026 khong lam vay:
	# giam 100% thi can cu tinh thue GTGT cung ve 0, ma luat bat gia tinh
	# thue phai la gia ban cua hang cung loai.
	dung("không đặt phần trăm giảm bằng 100",
		not co_cum("additional_discount_percentage", "=", "100"))
	dung("có xoá mọi khoản giảm để khỏi kéo căn cứ tính thuế xuống",
		co_cum("additional_discount_percentage", "=", "0"))


@ca("qua tang: KHONG dung o write_off cua Sales Invoice")
def _():
	# ERPNext v16: allow_write_off_only_on_pos() xoa trang write_off_account
	# neu khong phai hoa don quay, va make_write_off_gl_entry() chi sinh but
	# toan khi is_pos bat. Dien vao do la dien vao cho may se tu xoa, va
	# khong co mot dong so cai nao duoc sinh ra.
	dung("không đụng write_off_amount", "write_off_amount" not in MA_CODE)
	dung("không đụng write_off_account", "write_off_account" not in MA_CODE)


@ca("qua tang: bon hook deu duoc khai trong hooks.py")
def _():
	for ten in ("truoc_khi_luu", "truoc_khi_ghi_so", "sau_khi_ghi_so", "khi_huy"):
		dung("hook %s đã khai" % ten,
			"vagabond.qua_tang_hoa_don." + ten in MA_HOOK)


@ca("qua tang: hoa don qua KHONG tich diem thanh vien")
def _():
	# Khach duoc tang qua ma lai duoc cong diem nhu vua mua that la cong hai
	# lan mot mon qua, va diem do quy doi ra tien mat cua tiem.
	dung("có chốt bỏ qua trong hàm cộng điểm",
		"vgb_qua_tang" in MA_KHACH and "vgb_phieu_qua" in MA_KHACH)


@ca("qua tang: khach hang noi bo KHONG di duong qua tang")
def _():
	# Don noi bo giam 100% va chan hoa don dien tu, nguoc han voi hang bieu
	# tang. Hai luat nguoc nhau tren cung mot to thi to do sai kieu gi cung
	# sai, nen chan thang thay vi de hai mo dun giang nhau.
	dung("có gọi la_noi_bo để chặn", "la_noi_bo" in MA_CODE)


@ca("qua tang: huy hoa don thi HUY but toan chu khong xoa (QT-20)")
def _():
	dung("có gọi cancel", co_cum("cancel", "(", ")"))
	dung("không xoá chứng từ nào", "delete_doc" not in MA_CODE)


@ca("qua tang: chi HAI cua mo ra ngoai, bon hook khong duoc whitelist")
def _():
	dung("có khai trong bảng cửa ngõ", '"qua_tang_hoa_don.py"' in MA_CUA)
	for ten in ("truoc_khi_luu", "truoc_khi_ghi_so", "sau_khi_ghi_so", "khi_huy"):
		dung("hook %s không nằm trong bảng cửa ngõ" % ten,
			('"%s"' % ten) not in MA_CUA.split('"qua_tang_hoa_don.py"')[1][:200])


@ca("qua tang: truong tu them duoc dung lai moi lan Migrate")
def _():
	dung("có gọi dựng nhóm trường",
		"qua_tang_hoa_don.TRUONG_MOI" in MA_TRUONG)


@ca("qua tang: tai khoan chi phi KHONG duoc doan bua trong ma")
def _():
	# Chon ho cho hach toan la quyet dinh ke toan, ma but toan sinh ra o day
	# di thang vao so cai. Chua khai thi nem loi ro rang chu khong lay dai
	# mot tai khoan nao.
	for so in ("641", "642", "6418", "811"):
		dung("không nhét cứng tài khoản %s" % so, so not in MA_CODE)


# -------------------------------------------------------- nhan ban dot qua


@ca("nhan ban dot: doi dung cum nam o cuoi ma, khong dung phan chu")
def _():
	la("mã có đuôi năm", ma_dot_moi("TRUNGTHU-2025", 2026), "TRUNGTHU-2026")
	la("mã nhiều gạch", ma_dot_moi("TET-BINH-NGO-2026", 2027), "TET-BINH-NGO-2027")


@ca("nhan ban dot: ma khong co duoi nam thi NOI THEM, khong doan bua")
def _():
	la("nối thêm năm", ma_dot_moi("TRIAN", 2027), "TRIAN-2027")
	la("đuôi không phải bốn chữ số thì cũng nối thêm",
		ma_dot_moi("DOT-12", 2027), "DOT-12-2027")


@ca("nhan ban dot: thieu mot ve thi tra ve ve con lai, khong nem")
def _():
	la("thiếu mã", ma_dot_moi("", 2027), "2027")
	la("thiếu năm", ma_dot_moi("TET-2026", ""), "TET-2026")


@ca("nhan ban dot: ten dot thay so nam cu neu ten co chua nam")
def _():
	la("thay trong tên", ten_dot_moi("Trung thu 2025", 2025, 2026), "Trung thu 2026")
	la("tên không chứa năm thì kẹp thêm",
		ten_dot_moi("Quà tri ân", 2025, 2026), "Quà tri ân (2026)")


@ca("nhan ban dot: KHONG chep trang thai va khong chep hoa don sang mua sau")
def _():
	# Chep sang la mua moi mo ra da thay khach nao cung "Da tang", va khong
	# ai biet con so do la cua nam nao.
	for o in ("tt_tang", "ngay_tang", "tt_lien_he", "huy", "hoa_don",
			"zns_da_gui"):
		dung("ô %s nằm trong danh sách không chép" % o, o in O_KHONG_CHEP)


# ------------------------------------------------------------------ man app


@ca("man CRM: nut nhan ban duoc soi TRUOC the dot")
def _():
	# Nut nhan ban nam TRONG the dot. Soi the truoc thi bam nut cung chi mo
	# dot ra, va khong ai nhan ban duoc.
	dong_nb = "var nb = e.target.closest('[data-nb]');"
	dong_dot = "var t = e.target.closest('[data-dot]');"
	dung("có dòng soi nút nhân bản", dong_nb in MA_JS)
	dung("có dòng soi thẻ đợt", dong_dot in MA_JS)
	if dong_nb in MA_JS and dong_dot in MA_JS:
		dung("soi nút nhân bản trước thẻ đợt",
			MA_JS.index(dong_nb) < MA_JS.index(dong_dot))


@ca("man CRM: nut xuat hoa don chi hien khi phieu DA LUU va DA gan khach")
def _():
	dung("có chốt moi hoặc chưa gắn khách", "moi || !p.khach" in MA_JS)


# ------------------------------------------------- lap dot va dan danh sach


@ca("lap dot: ma dot sinh tu dip va nam, dung MOT khuon voi nut nhan ban")
def _():
	# Hai cho tu ghep chuoi thi som muon mot cho ghep khac, va nut nhan ban
	# se khong nhan ra duoi nam de thay.
	la("Trung thu", ma_dot_tu_dip("Trung thu", 2026), "TRUNGTHU-2026")
	la("Tết", ma_dot_tu_dip("Tet", 2027), "TET-2027")
	la("dịp lạ rơi về DOT", ma_dot_tu_dip("Khong co dip nay", 2026), "DOT-2026")
	# Va day la phep noi hai ham lai: ma sinh ra phai nhan ban duoc.
	la("mã sinh ra nhân bản được",
		ma_dot_moi(ma_dot_tu_dip("Trung thu", 2026), 2027), "TRUNGTHU-2027")


@ca("lap dot: ten goi y co ten dip bang tieng Viet co dau")
def _():
	la("Trung thu", ten_dot_goi_y("Trung thu", 2026), "Trung thu 2026")
	la("Giáng sinh", ten_dot_goi_y("Giang sinh", 2026), "Giáng sinh 2026")


@ca("dan danh sach: TAB va cham phay la dau ngan cot, dau PHAY thi KHONG")
def _():
	# Dia chi o day gan nhu dong nao cung co dau phay. Lay phay lam dau ngan
	# la vo het dia chi ma nguoi dan khong hieu vi sao.
	mot = tach_dan("Mr.Giang\t1\t12 Le Loi, Quan 1\t0902455422")
	la("một dòng bốn ô", len(mot[0]), 4)
	la("địa chỉ còn nguyên dấu phẩy", mot[0][2], "12 Le Loi, Quan 1")
	la("chấm phẩy cũng tách được",
		tach_dan("Mr.A;1;12 Le Loi, Q1")[0][2], "12 Le Loi, Q1")


@ca("dan danh sach: bo dong trong va bo dong tieu de")
def _():
	ra = tach_dan("Tên khách\tSố lượng\tĐịa chỉ\n\nMr.A\t2\tQ1\n\nMr.B\t1\tQ3\n")
	la("còn đúng hai dòng", len(ra), 2)
	la("dòng đầu là Mr.A", ra[0][0], "Mr.A")


@ca("dan danh sach: thieu cot cuoi thi de trong chu KHONG no")
def _():
	# Nguoi dan hay quet thieu cot cuoi. Bat ho dan lai ca bang vi thieu o
	# Ghi chu la vo ich.
	d = doc_dong_dan(["Mr.A", "2"])
	la("đủ sáu ô", len(d), len(COT_DAN))
	la("tên khách", d["ten_khach"], "Mr.A")
	la("số lượng", d["so_luong"], 2)
	la("ghi chú để trống", d["ghi_chu"], "")


@ca("dan danh sach: so luong go lung tung van doc ra so, rong thi ve 1")
def _():
	la("có chữ kèm", doc_dong_dan(["Mr.A", "2 hộp"])["so_luong"], 2)
	la("để trống thì 1", doc_dong_dan(["Mr.A", ""])["so_luong"], 1)
	la("chữ thuần thì 1", doc_dong_dan(["Mr.A", "hai"])["so_luong"], 1)


@ca("dan danh sach: so dan vao la so SHIPPER GOI, khong phai so gui Zalo")
def _():
	# O `sdt_khach` la o DUY NHAT duoc phep gui tin Zalo. Nhet so nguoi nhan
	# thay vao do la tin chuc bay vao may tro ly.
	ma = _doc("tang_qua.py")
	moc = ma.split("def nap_dan(")[1].split("def ")[0] if "def nap_dan(" in ma else ""
	dung("có nạp vào ô số người nhận", "sdt_nhan_tho" in moc)
	dung("KHÔNG nạp vào ô số riêng của khách", "sdt_khach_tho" not in moc)


@ca("man CRM: khong con bao nguoi dung mo Desk de tao dot")
def _():
	dung("bỏ hẳn câu bảo mở Desk", "Mở Desk tạo một đợt" not in MA_JS)
	dung("có nút cộng mở màn lập đợt", "go(scrTqLapDot)" in MA_JS)


# ------------------------------------------ KHONG giao viec tu dong nua
#
# Anh Viet chot 26/08/2026 sau khi chi Dung nhan duoc phan cong mot phieu
# tang qua khong lien quan gi toi chi. Bon ca duoi day la hang rao de khong
# ai mac lai nham.


class _PhieuGia(object):
	"""Mot phieu tang qua gia, du de goi `_ai_phai_lam`."""

	doctype = "Vagabond Tang Qua VIP"
	name = "TQV-2026-00006"

	def __init__(self, **k):
		self._o = {"huy": 0, "tt_lien_he": "Chua lien he",
			"nguoi_lam": "", "bo_phan_lam": "Sales",
			"ten_khach": "Ms.Lâm Quang Tiến"}
		self._o.update(k)

	def get(self, ten, md=None):
		return self._o.get(ten, md)


@ca("giao viec: phieu tang qua KHONG con giao tu dong cho ai nua")
def _():
	from vagabond.giao_viec import _ai_phai_lam

	# Bo phan Sales, khong ghi ten nguoi lam: truoc day day chinh la truong
	# hop giao cho MOI nguoi giu ba vai Sales, ke ca ke toan.
	nguoi, mo_ta = _ai_phai_lam(_PhieuGia())
	la("không giao cho ai", nguoi, [])
	la("không có mô tả việc", mo_ta, "")


@ca("giao viec: co ghi ten nguoi lam cung KHONG tu giao")
def _():
	# Anh Viet noi ro chi giu phan cong TAY. Co ten trong o Nguoi lam van la
	# mot o de biet ai lo, khong phai mot lenh giao viec.
	from vagabond.giao_viec import _ai_phai_lam

	nguoi, _mt = _ai_phai_lam(_PhieuGia(nguoi_lam="ai_do@vagabond"))
	la("vẫn không giao", nguoi, [])


@ca("giao viec: bo phan Marketing cung khong giao")
def _():
	from vagabond.giao_viec import _ai_phai_lam

	nguoi, _mt = _ai_phai_lam(_PhieuGia(bo_phan_lam="Marketing"))
	la("vẫn không giao", nguoi, [])


@ca("giao viec: hooks.py khong con mac phieu tang qua vao khi_sinh_phieu")
def _():
	# Soi theo CUM chu khong soi ca tep: ten doctype van con trong hooks o
	# muc ghi chu, va do la dieu nen giu.
	dung("không còn khối doc_events cho phiếu tặng quà",
		'"Vagabond Tang Qua VIP"' not in MA_HOOK_CODE)


@ca("giao viec: khong con nhip quet dem ban phan cong moi sang")
def _():
	dung("bỏ hẳn khỏi bộ lập lịch", "quet_dem_tu_dong" not in MA_HOOK_CODE)
	ma_tq = _doc("tang_qua.py")
	dung("hàm quét đêm đã gỡ khỏi mã", "def quet_dem(" not in ma_tq)
	dung("điểm gọi của bộ lập lịch cũng gỡ", "def quet_dem_tu_dong(" not in ma_tq)


@ca("giao viec: phan cong TAY tren Desk khong di qua ham nay nen van dung duoc")
def _():
	# `giao` va `go_giao` la duong cua ma nguon, con nut Phan cong cua Desk
	# goi thang frappe.desk.form.assign_to. Go nhanh tang qua o `_ai_phai_lam`
	# KHONG dong duong do lai.
	dung("hàm giao vẫn còn cho các loại phiếu khác", "def giao(" in MA_GIAO)
	dung("nhánh tặng quà trả rỗng",
		'if dt == "Vagabond Tang Qua VIP":' in MA_GIAO)
