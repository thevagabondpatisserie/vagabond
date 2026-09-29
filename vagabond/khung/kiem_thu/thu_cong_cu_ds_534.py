"""v534 (issue #380): bộ công cụ danh sách dùng chung, sổ hàng tặng, tiền đã về.

Sales Manager báo 28/09/2026: khách đã trả tiền vẫn nằm trong Công nợ phải
thu, và đơn hàng tặng xong rồi thì không có chỗ xem lại bill. Anh Việt chốt
cùng ngày: chip lọc, xuất Excel, chip trạng thái theo chặng là tối cần thiết,
áp dụng cho mọi màn.

Các ca ở đây chạy trên phép THUẦN: không cần Frappe, không cần site, không
cần requests (cong_no.py kéo ban_hang nên KHÔNG được nạp ở đây). Hành vi màn
hình chạy thật ở hanh_vi/cong_cu_ds_534.js; ghi sổ phiếu thu chạy trên sổ cái
thật ở kiem_that/thu_phieu_thu_unc_534.py (bench).
"""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")


def _doc(*p):
	return io.open(os.path.join(GOI, *p), encoding="utf-8").read()


# ------------------------------------------------------------ chip ngày

@ca("v534 chip ngày ra đúng khoảng, hai đầu đều tính")
def _khoang_ky():
	from vagabond.khung.cong_cu_ds import khoang_ky
	hn = "2026-09-28"
	la("mọi ngày không lọc", khoang_ky("", hn), (None, None))
	la("khoá lạ không lọc, không nổ", khoang_ky("nam_ngoai", hn), (None, None))
	la("hôm nay", khoang_ky("hom_nay", hn), ("2026-09-28", "2026-09-28"))
	la("7 ngày gồm cả hôm nay", khoang_ky("7_ngay", hn), ("2026-09-22", "2026-09-28"))
	la("tháng này", khoang_ky("thang_nay", hn), ("2026-09-01", "2026-09-28"))
	la("tháng trước", khoang_ky("thang_truoc", hn), ("2026-08-01", "2026-08-31"))
	la("tháng trước qua năm", khoang_ky("thang_truoc", "2026-01-15"), ("2025-12-01", "2025-12-31"))
	la("tháng trước tháng hai năm nhuận", khoang_ky("thang_truoc", "2028-03-02"), ("2028-02-01", "2028-02-29"))
	la("tuỳ chọn gõ ngược thì đảo", khoang_ky("tuy_chon", hn, "2026-09-20", "2026-09-01"), ("2026-09-01", "2026-09-20"))
	la("tuỳ chọn thiếu một đầu", khoang_ky("tuy_chon", hn, "2026-09-20", ""), ("2026-09-20", None))
	la("tuỳ chọn gõ bậy", khoang_ky("tuy_chon", hn, "abc", "xyz"), (None, None))


@ca("v534 trong_khoang tính cả hai đầu, ngày hỏng thì loại")
def _trong_khoang():
	from vagabond.khung.cong_cu_ds import trong_khoang
	dung("không lọc thì nhận hết", trong_khoang("", None, None))
	dung("đầu trái", trong_khoang("2026-09-01", "2026-09-01", "2026-09-30"))
	dung("đầu phải", trong_khoang("2026-09-30", "2026-09-01", "2026-09-30"))
	dung("ngoài phải", not trong_khoang("2026-10-01", "2026-09-01", "2026-09-30"))
	dung("ngày trống khi đang lọc thì loại", not trong_khoang("", "2026-09-01", None))


# ------------------------------------------------------------ bảng Excel

@ca("v534 dung_bang: tiêu đề đúng thứ tự cột, tiền là số, ngày dd/mm/yyyy, thiếu ô thì trống")
def _dung_bang():
	from vagabond.khung.cong_cu_ds import dung_bang
	cot = [{"k": "ngay", "nhan": "Ngày", "kieu": "ngay"}, {"k": "khach", "nhan": "Khách"},
		{"k": "tien", "nhan": "Số tiền", "kieu": "tien"}, {"k": "x", "nhan": "Lạ", "kieu": "bat_ky"}]
	b = dung_bang(cot, [{"ngay": "2026-09-23", "khach": "Khách A", "tien": 5785500.0},
		{"khach": None, "tien": "12.5"}])
	la("hàng tiêu đề", b[0], ["Ngày", "Khách", "Số tiền", "Lạ"])
	la("dòng một", b[1], ["23/09/2026", "Khách A", 5785500, ""])
	la("dòng thiếu ô", b[2], ["", "", 12.5, ""])
	la("tiền là kiểu số để kế toán cộng được", type(b[1][2]).__name__, "int")
	la("không cột nào thì chỉ còn hàng tiêu đề rỗng", dung_bang([], [{"a": 1}]), [[], []])


@ca("v534 tên tệp Excel an toàn cho điện thoại")
def _ten_tep():
	from vagabond.khung.cong_cu_ds import ten_tep
	la("bỏ ký tự lạ", ten_tep("Sổ đơn / tặng", "2026-09-28"), "Sổ-đơn-tặng-2026-09-28.xlsx")
	la("trống thì có tên mặc định", ten_tep("", "2026-09-28"), "danh-sach-2026-09-28.xlsx")


@ca("v534 sổ khai xuất: mỗi màn trỏ tới adapter có thật, adapter KHÔNG mở ra ngoài")
def _so_khai():
	from vagabond.khung.cong_cu_ds import MAN_XUAT
	from vagabond.khung.kiem_thu.thu_cua_ngo import _ten_whitelist
	la("ba màn đợt 1", sorted(MAN_XUAT), ["cong_no", "hang_tang", "tien_da_ve"])
	for man, duong in MAN_XUAT.items():
		mo_dun, ham = duong.rsplit(".", 1)
		tep = mo_dun.split(".", 1)[1].replace(".", "/") + ".py"
		ma = _doc(tep)
		dung("%s: có def %s" % (man, ham), ("\ndef %s(" % ham) in ma)
		dung("%s: adapter nhận khoá lạ mà không nổ" % man,
			re.search(r"\ndef %s\([^)]*\*\*khac\)" % ham, ma) is not None)
		# Adapter chỉ đi qua cửa xuat_excel; mở thẳng ra ngoài là thêm một
		# cửa đọc dữ liệu không qua sổ khai.
		dung("%s: adapter không whitelist" % man, ham not in _ten_whitelist(os.path.join(GOI, tep)))


@ca("v534 cửa xuất Excel từ chối tên màn lạ, không nạp mô đun theo chuỗi người gửi")
def _cua_la():
	from vagabond.khung import cong_cu_ds
	import frappe
	nem("màn lạ bị chặn", lambda: cong_cu_ds.xuat_excel("os.system", "{}"), frappe.ValidationError)
	nem("màn trống bị chặn", lambda: cong_cu_ds.xuat_excel("", "{}"), frappe.ValidationError)


# ------------------------------------------------------------ sổ hàng tặng

@ca("v534 hàng tặng: chặng tách Đã duyệt thành Chờ ghi sổ và Hoàn tất")
def _chang():
	from vagabond.hang_tang import chang_cua, KHOA_CHANG
	la("bốn chặng", KHOA_CHANG, ("cho_duyet", "cho_ghi_so", "hoan_tat", "tu_choi"))
	la("chờ duyệt", chang_cua("Chờ duyệt", 0), "cho_duyet")
	la("ô trống là chờ duyệt", chang_cua("", 0), "cho_duyet")
	la("đã duyệt chưa ghi sổ", chang_cua("Đã duyệt", 0), "cho_ghi_so")
	la("đã duyệt đã ghi sổ", chang_cua("Đã duyệt", 1), "hoan_tat")
	la("đơn cũ ghi sổ trước khi có luồng duyệt", chang_cua("", 1), "hoan_tat")
	la("từ chối", chang_cua("Từ chối", 0), "tu_choi")
	la("docstatus dạng chuỗi", chang_cua("Đã duyệt", "1"), "hoan_tat")
	# Số thật 28/09/2026: 41 đơn tặng, 40 đã duyệt và đã ghi sổ, 1 chờ duyệt.
	dem = {}
	for tt, ds, n in (("Đã duyệt", 1, 40), ("Chờ duyệt", 0, 1)):
		for _ in range(n):
			k = chang_cua(tt, ds)
			dem[k] = dem.get(k, 0) + 1
	la("site thật 28/09 ra 40 hoàn tất, 1 chờ duyệt", dem, {"hoan_tat": 40, "cho_duyet": 1})


@ca("v534 hàng tặng: màn cắt 200/500 dòng, Excel lấy ĐỦ (Codex #381 F5, ca 501 dòng)")
def _cat_dong():
	from vagabond.hang_tang import cat_dong
	ra = [{"name": "HDB-%04d" % i} for i in range(501)]
	la("màn mặc định 200", len(cat_dong(ra, None)), 200)
	la("màn trần 500", len(cat_dong(ra, 9999)), 500)
	la("Excel đủ 501", len(cat_dong(ra, 200, day_du=1)), 501)
	la("Excel giữ đúng dòng cuối", cat_dong(ra, 200, day_du=1)[-1]["name"], "HDB-0500")
	la("số lạ về 200", len(cat_dong(ra, "abc")), 200)


@ca("v534 hàng tặng: màn và Excel dùng CHUNG một tập lọc, bill mở lại được")
def _tang_chung():
	s = _doc("hang_tang.py")
	i = s.find("def ds_don(")
	j = s.find("\n# Cột Excel", i)
	dung("ds_don đọc từ _tap", "_tap(diem, chang, loai, tim, ky, tu, den, trang_thai)" in s[i:j])
	i = s.find("def xuat_ds(")
	dung("xuat_ds đọc từ _tap", "_tap(diem, chang, loai, tim, ky, tu, den)" in s[i:i + 900])
	dung("xuat_ds kiểm quyền như màn", "_quyen()" in s[i:i + 900])
	js = io.open(os.path.join(BEP, "41-duyet-don-tang.js"), encoding="utf-8").read()
	dung("nút xem lại bill", "data-dtgbill" in js and "scrPosBill(maB)" in js)
	tc = io.open(os.path.join(BEP, "02-trang-chu.js"), encoding="utf-8").read()
	dung("lối vào Sổ hàng tặng ở nhóm Bán hàng", "'CN', 'SOTANG'" in tc)
	dung("lối vào mở sẵn chặng Hoàn tất", "if (k === 'SOTANG') { dtgChang = 'hoan_tat';" in tc)


# ------------------------------------------------------ tiền đã về, phiếu thu

def _pe(**k):
	d = {"payment_type": "Receive", "docstatus": 0, "reference_no": "FT26266374066864",
		"paid_amount": 5785500, "paid_to": "11211 - Tiền gửi MB Bank - TV", "company": "TV"}
	d.update(k)
	return d


def _gd(**k):
	d = {"name": "ACC-BTN-2026-06238", "docstatus": 1, "deposit": 5785500, "withdrawal": 0,
		"currency": "VND", "unallocated_amount": 5785500, "allocated_amount": 0, "so_noi": 0}
	d.update(k)
	return d


TK = "11211 - Tiền gửi MB Bank - TV"


@ca("v534 xác minh tiền về: ca thật 23/09 (5.785.500 đ, FT...6864) khớp")
def _xac_minh_dung():
	from vagabond.thu_tien import xac_minh_tien_ve
	la("khớp", xac_minh_tien_ve(_pe(), _gd(), TK, "TV"), (True, ""))


@ca("v534 xác minh tiền về: mọi đường sai đều KHÔNG tách khỏi nợ (Codex #381 F2, F4)")
def _xac_minh_sai():
	from vagabond.thu_tien import xac_minh_tien_ve
	ca_sai = {
		"phiếu chi": (_pe(payment_type="Pay"), _gd()),
		"phiếu đã ghi sổ": (_pe(docstatus=1), _gd()),
		"phiếu không số tham chiếu": (_pe(reference_no=""), _gd()),
		"không có giao dịch": (_pe(), None),
		"giao dịch trùng số": (_pe(), _gd(trung=2)),
		"giao dịch nháp": (_pe(), _gd(docstatus=0)),
		"tiền ra": (_pe(), _gd(deposit=0, withdrawal=5785500)),
		"ngoại tệ": (_pe(), _gd(currency="USD")),
		"giao dịch đã nối chứng từ khác": (_pe(), _gd(so_noi=1)),
		"giao dịch đã phân bổ một phần": (_pe(), _gd(allocated_amount=1000000, unallocated_amount=4785500)),
		"giao dịch ít tiền hơn phiếu": (_pe(), _gd(deposit=5000000, unallocated_amount=5000000)),
		"phiếu không có tiền": (_pe(paid_amount=0), _gd()),
	}
	for nhan, (pe, gd) in ca_sai.items():
		ok, ly_do = xac_minh_tien_ve(pe, gd, TK, "TV")
		dung(nhan + ": không khớp", not ok)
		dung(nhan + ": có câu lý do", bool(ly_do))
	ok, _ = xac_minh_tien_ve(_pe(), _gd(), "11212 - Tiền gửi khác - TV", "TV")
	dung("tài khoản khác: không khớp", not ok)
	ok, _ = xac_minh_tien_ve(_pe(), _gd(), TK, "CTY KHAC")
	dung("công ty khác: không khớp", not ok)
	ok, _ = xac_minh_tien_ve(_pe(paid_amount=5785500.4), _gd(), TK, "TV")
	dung("lệch dưới nửa đồng vẫn khớp", ok)


@ca("v534 xác minh tiền về: so theo tiền TÀI KHOẢN NHẬN, phiếu ngoại tệ hoặc tỉ giá khác 1 thì không nhận (Codex #382 vòng 5)")
def _tien_te():
	from vagabond.thu_tien import xac_minh_tien_ve, tien_phia_ngan_hang
	# Ca Codex nêu: 100 USD ghi có 2.500.000 đ, giao dịch chỉ 1.000.000 đ.
	# Trên 87dda5ee phép so dùng paid_amount (100) nên ra (True, "").
	usd = _pe(paid_amount=100.0, received_amount=2500000.0, paid_from_account_currency="USD",
		paid_to_account_currency="VND", source_exchange_rate=25000.0, target_exchange_rate=1.0)
	ok, ly_do = xac_minh_tien_ve(usd, _gd(deposit=1000000, unallocated_amount=1000000), TK, "TV")
	dung("100 USD với giao dịch 1.000.000 đ: không khớp", not ok)
	dung("có câu lý do ngoại tệ", "ngoại tệ" in ly_do)
	ti_gia = _pe(received_amount=5785500, paid_from_account_currency="VND",
		paid_to_account_currency="VND", source_exchange_rate=1.0, target_exchange_rate=2.0)
	dung("tỉ giá đích khác 1: không khớp", not xac_minh_tien_ve(ti_gia, _gd(), TK, "TV")[0])
	dung("tỉ giá nguồn khác 1: không khớp", not xac_minh_tien_ve(
		_pe(source_exchange_rate=0.5), _gd(), TK, "TV")[0])
	dung("tài khoản nhận ngoại tệ: không khớp", not xac_minh_tien_ve(
		_pe(paid_to_account_currency="USD"), _gd(), TK, "TV")[0])
	# Tiền hai phía lệch nhau: giao dịch đủ cho paid_amount nhưng thiếu cho
	# received_amount thì phải dựa vào received_amount.
	lech = _pe(paid_amount=1000000, received_amount=2500000)
	ok, ly_do = xac_minh_tien_ve(lech, _gd(deposit=1000000, unallocated_amount=1000000), TK, "TV")
	dung("tiền hai phía lệch: không khớp", not ok and bool(ly_do))
	# Chiều ngược lại: tiền vào tài khoản đủ giao dịch mà phiếu gạch nợ khách
	# nhiều hơn. Chỉ phép soát hai phía bằng nhau chặn được, phép so tiền
	# chưa phân bổ không đỡ (đột biến M31 vòng 5 lọt khi chưa có dòng này).
	nguoc = _pe(paid_amount=2500000, received_amount=1000000)
	ok, ly_do = xac_minh_tien_ve(nguoc, _gd(deposit=1000000, unallocated_amount=1000000), TK, "TV")
	dung("phiếu gạch nợ nhiều hơn tiền vào: không khớp", not ok)
	dung("câu lý do nói hai phía lệch", "lệch" in ly_do)
	vnd = _pe(received_amount=5785500, paid_from_account_currency="VND",
		paid_to_account_currency="VND", source_exchange_rate=1.0, target_exchange_rate=1.0)
	la("phiếu tiền đồng thuần đủ trường vẫn khớp", xac_minh_tien_ve(vnd, _gd(), TK, "TV"), (True, ""))
	la("số dùng để so là tiền tài khoản nhận", tien_phia_ngan_hang(vnd), (5785500.0, ""))
	la("phiếu cũ thiếu trường tiền tệ: dùng paid_amount", tien_phia_ngan_hang(_pe()), (5785500.0, ""))
	la("tỉ giá để trống coi là 1", tien_phia_ngan_hang(_pe(target_exchange_rate=None))[1], "")
	s = _doc("thu_tien.py")
	i = s.find("def ghi_so_phieu_thu(")
	than = s[i:s.find("\n@frappe.whitelist", i + 10)]
	dung("ghi sổ không còn so với paid_amount", "flt(doc.paid_amount)" not in than)
	la("ghi sổ đọc tiền tài khoản nhận trước submit và sau submit",
		than.count("tien_nh, sai_tien = tien_phia_ngan_hang(doc.as_dict())"), 2)
	dung("soát đủ tiền chưa phân bổ theo tiền nhận", "flt(gdoc.unallocated_amount) + LECH < tien_nh" in than)
	dung("soát số lõi cấp theo tiền nhận", "flt(dong[0].allocated_amount) + LECH < tien_nh" in than)
	i = s.find("def phieu_thu_nhap(")
	than = s[i:s.find("\ndef ", i + 10)]
	la("màn Tiền đã về đọc kèm trường tiền tệ ở cả hai nhánh", than.count("+ TRUONG_TIEN_TE"), 2)


@ca("v534 tách tiền đã về: chỉ khi đã xác minh VÀ phủ đủ số còn nợ")
def _tach():
	from vagabond.thu_tien import tach_tien_da_ve
	dung("đủ và đã xác minh", tach_tien_da_ve(5785500, 5785500, 1))
	dung("chưa xác minh thì vẫn là nợ", not tach_tien_da_ve(5785500, 5785500, 0))
	dung("phủ một phần thì vẫn là nợ", not tach_tien_da_ve(5785500, 3000000, 1))
	dung("không còn nợ thì không có gì để tách", not tach_tien_da_ve(0, 5785500, 1))
	dung("lệch một đồng làm tròn vẫn tách", tach_tien_da_ve(5785500, 5785499, 1))


@ca("v534 công nợ: tiền đã về một phần trừ khỏi số còn phải đòi, hoá đơn vẫn ở Đang nợ (Codex #382 vòng 8)")
def _chia_con_no():
	from vagabond.thu_tien import chia_con_no
	la("600.000 đã về trên nợ 1.000.000", chia_con_no(1000000, 600000, 1), (400000.0, 600000.0))
	la("chưa xác minh thì không trừ", chia_con_no(1000000, 600000, 0), (1000000.0, 0.0))
	la("phủ đủ thì tách hẳn", chia_con_no(1000000, 1000000, 1), (0.0, 1000000.0))
	la("lệch một đồng làm tròn vẫn là phủ đủ", chia_con_no(1000000, 999999, 1), (0.0, 1000000.0))
	la("về nhiều hơn nợ chỉ tính tới số nợ", chia_con_no(1000000, 1500000, 1), (0.0, 1000000.0))
	la("không còn nợ", chia_con_no(0, 600000, 1), (0.0, 0.0))
	la("không có phiếu", chia_con_no(1000000, None, None), (1000000.0, 0.0))
	# Phép thuần mà ds_khach_no dùng, chạy trên bốn hoá đơn mẫu. Không nạp
	# cong_no ở đây: cong_no kéo ban_hang, ban_hang kéo requests, máy CI
	# không có (bài học 20/08).
	from vagabond.thu_tien import chia_no_hoa_don

	def hd(ten, khach, no):
		return {"name": ten, "customer": khach, "vgb_khach_no": "", "con_no": no}
	rows = [hd("HD1", "K1", 1000000), hd("HD2", "K1", 500000), hd("HD3", "K2", 700000), hd("HD4", "K2", 300000)]
	ve = {"HD1": {"phan_bo": 600000.0, "cac_pe": ["P1"], "da_xac_minh": 1},
		"HD2": {"phan_bo": 500000.0, "cac_pe": ["P2"], "da_xac_minh": 1},
		"HD3": {"phan_bo": 700000.0, "cac_pe": ["P3"], "da_xac_minh": 0}}
	con, the, khach = chia_no_hoa_don(rows, ve)
	dong = {r["name"]: r for r in con}
	la("HD1 còn phải đòi 400.000", dong["HD1"]["con_doi"], 400000.0)
	la("HD1 ghi rõ 600.000 đã về", dong["HD1"]["da_ve"], 600000.0)
	la("HD1 nợ sổ cái giữ nguyên", dong["HD1"]["con_no"], 1000000)
	dung("HD2 phủ đủ nên rời Đang nợ", "HD2" not in dong)
	la("HD3 chưa xác minh vẫn đòi đủ", (dong["HD3"]["con_doi"], dong["HD3"]["da_ve"]), (700000.0, 0.0))
	la("HD4 không có phiếu", dong["HD4"]["con_doi"], 300000.0)
	tong = sum(r["con_doi"] for r in con)
	la("tổng Còn phải đòi", tong, 400000.0 + 700000.0 + 300000.0)
	la("thẻ Tiền đã về: tiền cộng cả phần về một phần", the["tien"], 600000.0 + 500000.0)
	la("thẻ Tiền đã về: số hoá đơn có tiền về", the["so_hd"], 2)
	la("khách có tiền về", khach, {"K1"})
	la("sổ cái vẫn đủ: đòi + đã về = nợ trên sổ", tong + the["tien"], 1000000.0 + 500000.0 + 700000.0 + 300000.0)
	s = _doc("cong_no.py")
	i = s.find("def ds_khach_no(")
	than = s[i:s.find("\ndef ", i + 10)]
	dung("ds_khach_no đi qua phép thuần", "rows, the_ve, khach_cho = tt.chia_no_hoa_don(rows, ve)" in than)
	dung("cộng khách theo số còn đòi", 'o["tien"] += flt(r["con_doi"])' in than)
	dung("dòng hoá đơn: tiền là số còn đòi", '"tien": flt(r["con_doi"])' in than)
	dung("dòng hoá đơn: có số đã về", '"da_ve": flt(r["da_ve"])' in than)
	dung("dòng hoá đơn: đã thu theo sổ cái", '"da_thu": flt(r.grand_total) - flt(r["con_no"])' in than)
	dung("Excel Đang nợ có cột tiền đã về", '{"k": "da_ve", "nhan": "Tiền đã về, chờ ghi sổ (đ)", "kieu": "tien"}' in s)


@ca("v534 công nợ: đang tìm thì phần hiện ra có tổng riêng, thẻ trên đầu giữ tổng thật (Codex #382 vòng 9)")
def _loc_khach_no():
	from vagabond.thu_tien import loc_khach_no
	ds = [{"khach": "K1", "ten": "Công ty A", "tien": 1000000.0, "hd": [{"name": "HDB-1"}]},
		{"khach": "K2", "ten": "Công ty B", "tien": 5000000.0, "hd": [{"name": "HDB-2"}, {"name": "HDB-9"}]}]
	la("không tìm: đủ và tổng đủ", loc_khach_no(ds, ""), (ds, 6000000.0))
	la("tìm theo tên", loc_khach_no(ds, " công ty a "), ([ds[0]], 1000000.0))
	la("tìm theo số hoá đơn", loc_khach_no(ds, "hdb-9"), ([ds[1]], 5000000.0))
	la("tìm theo mã khách", loc_khach_no(ds, "k2"), ([ds[1]], 5000000.0))
	la("không khớp ai", loc_khach_no(ds, "zzz"), ([], 0))
	la("rỗng", loc_khach_no(None, "a"), ([], 0))
	s = _doc("cong_no.py")
	i = s.find("def ds_khach_no(")
	than = s[i:s.find("\ndef ", i + 10)]
	dung("ds_khach_no lọc qua phép thuần", "ra, tong_loc = tt.loc_khach_no(ra, tim)" in than)
	dung("trả tổng phần lọc", '"tong_loc": tong_loc' in than)
	# Dò chuỗi vì ds_khach_no kéo requests, không chạy được trên CI tay không.
	# Đột biến trả tong_loc vào ô "tong" (M57 vòng 9) lọt khi thiếu dòng này.
	dung("thẻ trên đầu trả tổng thật, không phải tổng lọc", '"khach": ra, "tong": tong, "so_khach_tat_ca"' in than)
	dung("thẻ trên đầu vẫn là tổng trước khi lọc", 0 < than.find("tong = sum(") < than.find("tt.loc_khach_no(ra, tim)"))


@ca("v534 ghi sổ phiếu thu: phải có UNC khách gửi, chỉ kế toán bấm (anh Việt 28/09)")
def _soat_ghi_so():
	from vagabond.thu_tien import soat_ghi_so_thu
	la("đủ ba điều kiện", soat_ghi_so_thu(True, "", 1, True), (True, ""))
	ok, ly = soat_ghi_so_thu(True, "", 0, True)
	dung("thiếu UNC bị chặn", not ok and "uỷ nhiệm chi" in ly)
	ok, ly = soat_ghi_so_thu(True, "", 2, False)
	dung("Sales có UNC vẫn chờ kế toán", not ok and "kế toán" in ly)
	ok, ly = soat_ghi_so_thu(False, "Giao dịch X đã nối với chứng từ khác.", 1, True)
	la("chưa khớp giao dịch thì trả đúng lý do xác minh", (ok, ly), (False, "Giao dịch X đã nối với chứng từ khác."))


@ca("v534 ghi sổ phiếu thu: một lượt nguyên khối, khoá, lùi điểm lưu khi hỏng, không đặt tay bước duyệt")
def _nguyen_khoi():
	s = _doc("thu_tien.py")
	i = s.find("def ghi_so_phieu_thu(")
	j = s.find("\n@frappe.whitelist", i + 10)
	than = s[i:j]
	dung("POST", '@frappe.whitelist(methods=["POST"])\ndef ghi_so_phieu_thu(' in s)
	dung("khoá phiếu", "frappe.get_doc(PE, name, for_update=True)" in than)
	dung("khoá giao dịch", "frappe.get_doc(BT, g[\"name\"], for_update=True)" in than)
	dung("soát lại trên bản đã khoá", "if gdoc.payment_entries or flt(gdoc.allocated_amount) > LECH:" in than)
	dung("có điểm lưu", 'frappe.db.savepoint("vgb_ghi_so_thu")' in than)
	dung("lùi điểm lưu khi hỏng", 'frappe.db.rollback(save_point="vgb_ghi_so_thu")' in than)
	dung("nối giao dịch rồi tải lại xác minh", "add_payment_entries" in than and "gdoc.reload()" in than)
	dung("giao dịch cấp thiếu tiền cho phiếu thì lùi", "flt(dong[0].allocated_amount) + LECH < tien_nh" in than)
	# Codex #382: ghi rõ điều kiện lõi đã đọc, để nâng ERPNext còn đối chiếu.
	for moc in ("frappe/model/document.py", "set_workflow_state_on_action",
			"erpnext/accounts/doctype/bank_transaction/bank_transaction.py",
			"add_payment_entries", "allocate_payment_entries", "get_clearance_details"):
		dung("chú thích lõi có " + moc, moc in than)
	# Frappe tự đặt bước duyệt đúng docstatus khi submit (set_workflow_state_on_action).
	# Đặt tay "Đã duyệt - Đã ghi sổ" từ "Nháp" là một bước chuyển workflow không khai.
	# Chú thích lõi có nhắc tên hàm set_workflow_state_on_action nên soát
	# đúng các kiểu ĐẶT giá trị, không soát chữ trần.
	dung("không đặt tay workflow_state", not re.search(r"\.workflow_state\s*=|[\"']workflow_state[\"']", than))
	dung("không tự commit", "frappe.db.commit" not in than)
	i = s.find("def chan_doan_ghi_so(")
	than = s[i:s.find("\ndef _ghi_vet_thu", i)]
	dung("chẩn đoán chỉ chạy bước kiểm, không submit", "run_before_save_methods()" in than and ".submit(" not in than)
	dung("chẩn đoán luôn lùi điểm lưu", 'finally:\n\t\tfrappe.db.rollback(save_point="vgb_chan_doan_thu")' in than)


@ca("v534 anh Việt 29/09: Desk và app cùng một luật UNC khách gửi (Codex #382 vòng 3)")
def _unc_desk():
	from unittest.mock import patch
	from vagabond import thu_tien as tt
	vao = dict(payment_type="Receive", party_type="Customer", paid_to="11211 - MB - TV")
	dung("phiếu thu tiền khách chuyển khoản gắn hoá đơn, khớp giao dịch", tt.can_unc_khach(vao, True, True))
	for nhan, doi, hd, gd in (
			("phiếu chi", dict(payment_type="Pay"), True, True),
			("thu nhà cung cấp", dict(party_type="Supplier"), True, True),
			("thu tiền mặt", dict(paid_to="1111 - Tiền mặt - TV"), True, True),
			("thu đặt bánh", dict(vgb_phieu_dat="PD-1"), True, True),
			("hồ sơ hoàn tiền", dict(vgb_hoan_tien="HT-1"), True, True),
			("không gắn hoá đơn", {}, False, True),
			("không khớp giao dịch", {}, True, False)):
		dung(nhan + ": không bắt ô UNC khách gửi", not tt.can_unc_khach(dict(vao, **doi), hd, gd))
	la("gộp tệp Desk vào danh sách", tt.gop_tep(["/a"], "/b"), ["/a", "/b"])
	la("gộp tệp trùng thì giữ nguyên", tt.gop_tep(["/a"], " /a "), ["/a"])
	la("không có tệp Desk", tt.gop_tep([], ""), [])

	class Doc(dict):
		doctype = "Payment Entry"
		def get(self, k, d=None):
			return dict.get(self, k, d)
		def __getattr__(self, k):
			return dict.get(self, k)
		def __setattr__(self, k, v):
			self[k] = v
		def as_dict(self):
			return dict(self)
	import frappe
	d = Doc(name="PE1", reference_no="FT1", vgb_thu_unc=None,
		references=[{"reference_doctype": "Sales Invoice"}], **vao)
	with patch.object(frappe.db, "exists", lambda *a, **k: True, create=True), \
			patch.object(tt, "_so_tep_unc", lambda *a: 0):
		nem("Desk: ô UNC trống thì chặn ghi sổ", lambda: tt.chan_thieu_unc_khach(d), frappe.ValidationError)
	with patch.object(frappe.db, "exists", lambda *a, **k: True, create=True), \
			patch.object(tt, "_so_tep_unc", lambda *a: 1):
		la("Desk: có tệp trong ô thì cho qua", tt.chan_thieu_unc_khach(d), None)
	with patch.object(frappe.db, "exists", lambda *a, **k: False, create=True), \
			patch.object(tt, "_so_tep_unc", lambda *a: 0):
		la("không khớp giao dịch thì hook này không chặn", tt.chan_thieu_unc_khach(d), None)
	# Codex #382 vòng 4: hỏng giữa chừng thì CHẶN, không cho qua.
	def hong(*a, **k):
		raise RuntimeError("hỏng đọc giao dịch")
	with patch.object(frappe.db, "exists", hong, create=True), patch.object(frappe, "log_error", lambda *a, **k: None):
		nem("lỗi lạ trong hook thì chặn ghi sổ", lambda: tt.chan_thieu_unc_khach(d), RuntimeError)
	s2 = _doc("thu_tien.py")
	i = s2.find("def ghi_so_phieu_thu(")
	than2 = s2[i:s2.find("\n@frappe.whitelist", i + 10)]
	dung("nút đính UNC soát loại phiếu trước khi gắn tệp",
		0 < than2.find("if not _thuoc_tap_unc(doc):") < than2.find("tep_dinh_kem.gan_vao("))
	dd = Doc(name="PE1", vgb_thu_unc='["/private/files/a.png"]', vgb_thu_unc_tep="/private/files/b.pdf")
	tt.gop_unc_desk(dd)
	la("lưu trên Desk: tệp ô Desk gộp vào ô danh sách", dd["vgb_thu_unc"],
		'["/private/files/a.png", "/private/files/b.pdf"]')
	# Codex #382 vòng 10: xoá hay thay tệp ở ô Desk thì bỏ đường dẫn cũ khỏi
	# ô danh sách. Chạy thật hook với bản trước khi lưu, như Frappe gọi.
	class DocTruoc(Doc):
		def get_doc_before_save(self):
			return self.get("_truoc")
	xoa = DocTruoc(name="PE1", vgb_thu_unc='["/private/files/a.png", "/private/files/b.pdf"]',
		vgb_thu_unc_tep=None, _truoc={"vgb_thu_unc_tep": "/private/files/b.pdf"})
	tt.gop_unc_desk(xoa)
	la("xoá ô Desk: bỏ tệp Desk, giữ tệp app", xoa["vgb_thu_unc"], '["/private/files/a.png"]')
	thay = DocTruoc(name="PE1", vgb_thu_unc='["/private/files/a.png", "/private/files/b.pdf"]',
		vgb_thu_unc_tep="/private/files/c.pdf", _truoc={"vgb_thu_unc_tep": "/private/files/b.pdf"})
	tt.gop_unc_desk(thay)
	la("thay ô Desk: tệp cũ ra, tệp mới vào", thay["vgb_thu_unc"], '["/private/files/a.png", "/private/files/c.pdf"]')
	chi_desk = DocTruoc(name="PE1", vgb_thu_unc='["/private/files/b.pdf"]',
		vgb_thu_unc_tep="", _truoc={"vgb_thu_unc_tep": "/private/files/b.pdf"})
	tt.gop_unc_desk(chi_desk)
	la("xoá tệp Desk duy nhất: ô danh sách trống", chi_desk["vgb_thu_unc"], None)
	la("thuần: không đổi thì giữ nguyên", tt.doi_unc_desk(["/a", "/b"], "/b", "/b"), ["/a", "/b"])
	la("thuần: lần lưu đầu chỉ gộp", tt.doi_unc_desk(["/a"], "", "/b"), ["/a", "/b"])
	import runpy
	pe_ev = runpy.run_path(os.path.join(GOI, "hooks.py"))["doc_events"]["Payment Entry"]
	bs = pe_ev["before_submit"]
	dung("hook ghi sổ đã gắn, sau hook tệp chung",
		bs.index("vagabond.thu_tien.chan_thieu_unc_khach") > bs.index("vagabond.chung_tu_tien.chan_thieu_dinh_kem"))
	dung("hook gộp tệp Desk đã gắn", "vagabond.thu_tien.gop_unc_desk" in pe_ev["before_validate"])
	o = tt.TRUONG_MOI["Payment Entry"][1]
	la("ô Desk", (o["fieldname"], o["fieldtype"], o["insert_after"]), ("vgb_thu_unc_tep", "Attach", "vgb_thu_unc"))


@ca("v534 ô UNC khách gửi dựng lúc migrate, sau ô UNC phiếu chi")
def _truong():
	from vagabond.thu_tien import TRUONG_MOI
	o = TRUONG_MOI["Payment Entry"][0]
	la("tên ô", o["fieldname"], "vgb_thu_unc")
	la("đứng sau ô UNC chi", o["insert_after"], "vgb_chi_unc")
	t = _doc("truong_tu_them.py")
	dung("dựng nhóm thu_tien", '_dung_nhom(thu_tien.TRUONG_MOI, "thu_tien")' in t)
	dung("dựng SAU nhóm duyet_chi", t.find('_dung_nhom(duyet_chi.TRUONG_MOI') < t.find('_dung_nhom(thu_tien.TRUONG_MOI'))


@ca("v534 công nợ: tách tiền đã về dựa trên phép xác minh, không đọc cờ nháp")
def _cong_no_tach():
	s = _doc("cong_no.py")
	i = s.find("def ds_khach_no(")
	than = s[i:s.find("\ndef ", i + 10)]
	dung("gọi phép chia thuần", "tt.chia_no_hoa_don(rows, ve)" in than)
	dung("tổng nợ tính trước ô tìm", 0 < than.find("tong = sum(") < than.find("tt.loc_khach_no(ra, tim)"))
	i = s.find("def _tien_da_ve_theo_hd(")
	than = s[i:s.find("\ndef ", i + 10) if s.find("\ndef ", i + 10) > 0 else len(s)]
	dung("cộng qua phép thuần gom_tien_da_ve", "return tt.gom_tien_da_ve(ds)" in than)


@ca("v534 tiền đã về: hai lần chuyển cộng lại phủ đủ thì tách, trùng một giao dịch không cộng hai lần (Codex #382)")
def _gom_tien_da_ve():
	from vagabond.thu_tien import gom_tien_da_ve, tach_tien_da_ve
	hai_lan = [
		{"pe": "PE1", "gd": "BT1", "da_xac_minh": 1, "hd": [("SI1", 600000.0)]},
		{"pe": "PE2", "gd": "BT2", "da_xac_minh": 1, "hd": [("SI1", 400000.0)]},
	]
	g = gom_tien_da_ve(hai_lan)
	la("600.000 + 400.000", g["SI1"]["phan_bo"], 1000000.0)
	la("giữ cả hai phiếu", g["SI1"]["cac_pe"], ["PE1", "PE2"])
	dung("hoá đơn 1.000.000 đã trả đủ thì tách", tach_tien_da_ve(1000000, g["SI1"]["phan_bo"], 1))
	trung = [
		{"pe": "PE1", "gd": "BT1", "da_xac_minh": 1, "hd": [("SI1", 600000.0)]},
		{"pe": "PE3", "gd": "BT1", "da_xac_minh": 1, "hd": [("SI1", 600000.0)]},
	]
	la("hai phiếu nháp cùng một FT chỉ tính một lần", gom_tien_da_ve(trung)["SI1"]["phan_bo"], 600000.0)
	chua = [
		{"pe": "PE1", "gd": "BT1", "da_xac_minh": 1, "hd": [("SI1", 600000.0)]},
		{"pe": "PE4", "gd": "BT4", "da_xac_minh": 0, "hd": [("SI1", 400000.0)]},
	]
	g = gom_tien_da_ve(chua)
	la("phiếu chưa xác minh không cộng", g["SI1"]["phan_bo"], 600000.0)
	dung("nên hoá đơn vẫn ở Đang nợ", not tach_tien_da_ve(1000000, g["SI1"]["phan_bo"], 1))
	la("một phiếu chia hai hoá đơn", gom_tien_da_ve([{"pe": "P", "gd": "B", "da_xac_minh": 1,
		"hd": [("SI1", 1.0), ("SI2", 2.0)]}]), {"SI1": {"phan_bo": 1.0, "cac_pe": ["P"], "da_xac_minh": 1},
		"SI2": {"phan_bo": 2.0, "cac_pe": ["P"], "da_xac_minh": 1}})
	la("rỗng", gom_tien_da_ve(None), {})


@ca("v534 tiền đã về: một giao dịch chia cho hai hoá đơn khác nhau chỉ tính MỘT phiếu (Codex #382 vòng 2)")
def _mot_phieu_moi_gd():
	from vagabond.thu_tien import gom_tien_da_ve, tach_tien_da_ve, mot_phieu_moi_giao_dich
	hai_hd = [
		{"pe": "PE1", "gd": "BT1", "ma_gd": "FT1", "tien": 1000000.0, "da_xac_minh": 1, "hd": [("SI1", 1000000.0)]},
		{"pe": "PE2", "gd": "BT1", "ma_gd": "FT1", "tien": 1000000.0, "da_xac_minh": 1, "hd": [("SI2", 1000000.0)]},
	]
	g = gom_tien_da_ve(hai_hd)
	tach = sorted(si for si in g if tach_tien_da_ve(1000000, g[si]["phan_bo"], 1))
	la("một lần tiền về 1.000.000 chỉ tách một hoá đơn", tach, ["SI1"])
	ra = mot_phieu_moi_giao_dich(hai_hd)
	la("phiếu thua hạ về chưa xác minh", [p["da_xac_minh"] for p in ra], [1, 0])
	dung("phiếu thua có câu lý do nêu phiếu thắng", "PE1" in ra[1]["ly_do"])
	la("không sửa danh sách gốc", hai_hd[1]["da_xac_minh"], 1)
	# Phiếu thắng chọn theo MỌI phiếu cùng mã trên hệ thống, không theo tập màn đang xem:
	# màn chỉ đọc PE2 nhưng hệ thống còn PE0 lớn hơn thì PE2 vẫn thua.
	ra = mot_phieu_moi_giao_dich([hai_hd[1]], {"FT1": [("PE0", 1200000.0), ("PE2", 1000000.0)]})
	la("thua phiếu ngoài tập đang xem", ra[0]["da_xac_minh"], 0)
	# Phiếu thắng tự nó không xác minh được thì không phiếu nào được tính.
	ra = mot_phieu_moi_giao_dich([dict(hai_hd[0], da_xac_minh=0), hai_hd[1]])
	la("thắng mà hỏng thì không ai tách", [p["da_xac_minh"] for p in ra], [0, 0])
	la("một phiếu chia hai hoá đơn vẫn đủ cả hai", sorted(gom_tien_da_ve([{"pe": "P", "gd": "B", "ma_gd": "F",
		"tien": 3.0, "da_xac_minh": 1, "hd": [("SI1", 1.0), ("SI2", 2.0)]}])), ["SI1", "SI2"])
	s = _doc("thu_tien.py")
	i = s.find("def phieu_thu_nhap(")
	than = s[i:s.find("\ndef ", i + 10)]
	dung("màn và công nợ cùng đi qua một chỗ chọn", "return mot_phieu_moi_giao_dich(ra, ung_vien)" in than)
	# Codex #382 vòng 3: phiếu không gắn hoá đơn bán không thuộc màn công nợ,
	# và không được làm ứng viên thắng.
	dung("bỏ phiếu không gắn hoá đơn", "cac_pe = [p for p in cac_pe if ref.get(p.name)]" in than)
	dung("ứng viên cũng phải gắn hoá đơn", "if t in co_hd]" in than)
	dung("lọc hoá đơn trước khi đọc tệp và giao dịch",
		than.find("cac_pe = [p for p in cac_pe if ref.get(p.name)]") < than.find("_gd_theo_so("))


@ca("v534 ghi sổ phiếu thu: chỉ tệp nằm TRONG ô UNC khách gửi mới tính (Codex #382)")
def _dem_tep_unc():
	from vagabond.thu_tien import dem_tep_unc
	la("ô trống, có một ảnh bất kỳ gắn vào phiếu", dem_tep_unc([], {"/private/files/anh-bat-ky.png"}), 0)
	la("ô có tệp và tệp còn gắn vào phiếu", dem_tep_unc(["/private/files/unc.png"], {"/private/files/unc.png"}), 1)
	la("ô có tệp nhưng tệp đã gỡ khỏi phiếu", dem_tep_unc(["/private/files/unc.png"], set()), 0)
	la("ô ghi trùng một tệp hai lần", dem_tep_unc(["/a", "/a"], {"/a"}), 1)
	la("hai tệp UNC, thêm một tệp mục khác", dem_tep_unc(["/a", "/b"], {"/a", "/b", "/khac"}), 2)
	s = _doc("thu_tien.py")
	i = s.find("def ghi_so_phieu_thu(")
	than = s[i:s.find("\n@frappe.whitelist", i + 10)]
	dung("ghi sổ đếm qua ô UNC", 'so_tep = _so_tep_unc(doc.name, doc.get("vgb_thu_unc"))' in than)
	dung("không còn đếm mọi File của phiếu", 'frappe.db.count("File"' not in than)
	i = s.find("def phieu_thu_nhap(")
	than = s[i:s.find("\ndef ", i + 10)]
	dung("màn Tiền đã về đọc đúng ô UNC", 'o_unc = {p.name: tep_dinh_kem.doc_ds(p.get("vgb_thu_unc"))' in than)
	dung("màn Tiền đã về đếm cùng phép", "dem_tep_unc(o_unc[p.name]" in than)


@ca("v534 UNC khách gửi: chỉ tệp gắn vào phiếu QUA ô UNC mới tính, ảnh ở mục khác không đổi nhãn được (Codex #382 vòng 7)")
def _o_unc_muc_khac():
	from vagabond.thu_tien import url_trong_o_unc, tep_muc_khac, O_UNC
	la("hai ô được nhận", O_UNC, ("vgb_thu_unc", "vgb_thu_unc_tep"))
	kep = {"file_url": "/private/files/anh-bat-ky.png", "attached_to_field": None}
	app = {"file_url": "/private/files/unc-app.png", "attached_to_field": "vgb_thu_unc"}
	desk = {"file_url": "/private/files/unc-desk.png", "attached_to_field": "vgb_thu_unc_tep"}
	o_khac = {"file_url": "/private/files/hd.pdf", "attached_to_field": "vgb_tep_hoa_don"}
	la("chỉ tệp gắn qua hai ô UNC", url_trong_o_unc([kep, app, desk, o_khac]),
		{"/private/files/unc-app.png", "/private/files/unc-desk.png"})
	la("rỗng", url_trong_o_unc(None), set())
	# Ca Codex nêu: ô UNC trống, gửi đường dẫn ảnh kẹp giấy của chính phiếu.
	la("ảnh kẹp giấy bị trả ra để từ chối", tep_muc_khac([kep["file_url"]], [kep]), [kep["file_url"]])
	la("tệp ô chứng từ khác cũng vậy", tep_muc_khac([o_khac["file_url"]], [o_khac]), [o_khac["file_url"]])
	la("tệp mới tải lên (chưa gắn đâu) thì nhận", tep_muc_khac(["/private/files/moi.png"], [kep]), [])
	la("tệp đã gắn qua ô UNC thì nhận", tep_muc_khac([app["file_url"], desk["file_url"]], [app, desk]), [])
	# Cùng một đường dẫn có hai bản ghi File (kẹp giấy và ô UNC): đã có
	# bản gắn qua ô UNC thì là tệp UNC thật.
	hai = [kep, {"file_url": kep["file_url"], "attached_to_field": "vgb_thu_unc"}]
	la("cùng đường dẫn có bản qua ô UNC thì nhận", tep_muc_khac([kep["file_url"]], hai), [])
	from vagabond.thu_tien import dem_tep_unc
	la("đếm: ô ghi tên ảnh kẹp giấy thì 0", dem_tep_unc([kep["file_url"]], url_trong_o_unc([kep])), 0)
	la("đếm: tệp qua ô Desk thì 1", dem_tep_unc([desk["file_url"]], url_trong_o_unc([kep, desk])), 1)
	s = _doc("thu_tien.py")
	i = s.find("def _so_tep_unc(")
	than = s[i:s.find("\n@frappe.whitelist", i)]
	dung("cổng ghi sổ đếm qua url_unc_that", "return dem_tep_unc(ds, url_unc_that(ten_pe, rows))" in than)
	dung("đọc MỌI dòng File mang đường dẫn, không lọc theo phiếu", 'filters={"file_url": ["in", ds]}' in than)
	i = s.find("def phieu_thu_nhap(")
	than = s[i:s.find("\ndef ", i + 10)]
	dung("màn Tiền đã về đếm cùng phép", "tep = {p.name: dem_tep_unc(o_unc[p.name], url_unc_that(" in than)
	dung("màn Tiền đã về đọc mọi dòng File theo đường dẫn", 'filters={"file_url": ["in", lo]}' in than)
	i = s.find("def ghi_so_phieu_thu(")
	than = s[i:s.find("\n@frappe.whitelist", i + 10)]
	a1, a2 = than.find("khac = tep_muc_khac(moi, cua_phieu)"), than.find('gan_vao(PE, doc.name, "vgb_thu_unc", unc)')
	dung("nút đính soát mục khác TRƯỚC khi gắn tệp", 0 < a1 < a2)
	# Dò chuỗi, vì ghi_so_phieu_thu chỉ chạy thật trên bench (ca _doi_nhan).
	# Đột biến bỏ lời từ chối (M41 vòng 7) lọt tầng thuần khi thiếu dòng này:
	# lớp đếm vẫn chặn ghi sổ, nhưng tệp kẹp giấy bị ghi tên vào ô UNC.
	dung("có mục khác thì từ chối", 'if khac:\n\t\t\tfrappe.throw("Tệp đã chọn đang đính ở mục khác' in than)


@ca("v534 UNC khách gửi: bản chép do ô Attach sinh ra không được tính (bench #382 vòng 8)")
def _unc_ban_chep():
	from vagabond.thu_tien import url_unc_that, dem_tep_unc

	def f(url, dt="Payment Entry", ten="PE1", o=None):
		return {"file_url": url, "attached_to_doctype": dt, "attached_to_name": ten, "attached_to_field": o}
	# Frappe attach_files_to_document: trỏ ô Attach vào đường dẫn có sẵn thì
	# CHÉP ra một dòng mới gắn qua ô đó. Bench vòng 7 đổ đúng chỗ này.
	kep = "/private/files/anh-bat-ky.png"
	la("ảnh kẹp giấy được chép sang ô Desk: không tính",
		url_unc_that("PE1", [f(kep), f(kep, o="vgb_thu_unc_tep")]), set())
	unc_b = "/private/files/unc-phieu-khac.png"
	la("UNC của phiếu khác chép sang ô Desk: không tính",
		url_unc_that("PE1", [f(unc_b, ten="PE2", o="vgb_thu_unc"), f(unc_b, o="vgb_thu_unc_tep")]), set())
	la("tệp của chứng từ khác loại chép sang: không tính",
		url_unc_that("PE1", [f("/files/x.png", dt="Sales Invoice", ten="SI1", o=None), f("/files/x.png", o="vgb_thu_unc_tep")]), set())
	la("tệp tải lên thật qua ô Desk: tính", url_unc_that("PE1", [f("/private/files/d.png", o="vgb_thu_unc_tep")]),
		{"/private/files/d.png"})
	la("tệp tải lên thật qua app: tính", url_unc_that("PE1", [f("/private/files/a.png", o="vgb_thu_unc")]),
		{"/private/files/a.png"})
	la("UNC của phiếu khác không tính cho phiếu này",
		url_unc_that("PE1", [f("/private/files/a.png", ten="PE2", o="vgb_thu_unc")]), set())
	la("một dòng treo chưa gắn cùng đường dẫn: không tính",
		url_unc_that("PE1", [f("/private/files/a.png", o="vgb_thu_unc"), f("/private/files/a.png", dt=None, ten=None)]), set())
	la("đếm: hai tệp thật, một bản chép", dem_tep_unc(["/private/files/a.png", "/private/files/d.png", kep],
		url_unc_that("PE1", [f("/private/files/a.png", o="vgb_thu_unc"), f("/private/files/d.png", o="vgb_thu_unc_tep"),
			f(kep), f(kep, o="vgb_thu_unc_tep")])), 2)


@ca("v534 Excel: chữ mở đầu bằng ký tự công thức không thành công thức (Codex #382 vòng 7)")
def _chu_an_toan():
	from vagabond.khung.cong_cu_ds import chu_an_toan, dung_bang
	for goc in ('=HYPERLINK("http://x.invalid","Bấm")', "=1+1", "{=SUM(1,2)}", "@SUM(1)", "+cmd|x",
			"-2+3", "\t=1", "\r=1"):
		la("thêm nháy: " + repr(goc), chu_an_toan(goc), "'" + goc)
	for goc in ("Khách thường", "+84 90 123 4567", "-150000", "0901234567", "HDB-26-09-04242", "", "a=b"):
		la("giữ nguyên: " + repr(goc), chu_an_toan(goc), goc)
	la("None ra rỗng", chu_an_toan(None), "")
	b = dung_bang([{"k": "ten", "nhan": "Tên", "kieu": "chu"}, {"k": "tien", "nhan": "Tiền", "kieu": "tien"}],
		[{"ten": "=1+1", "tien": 5}])
	la("dựng bảng đi qua phép an toàn, số vẫn là số", b[1], ["'=1+1", 5])
	# Có xlsxwriter (máy làm việc, site thật) thì ghi thật và đọc lại XML:
	# không ô nào là công thức. Máy CI tay không thì phép thuần ở trên chốt.
	try:
		import xlsxwriter
	except ImportError:
		return
	import io, zipfile
	bo = io.BytesIO()
	wb = xlsxwriter.Workbook(bo, {"constant_memory": True})
	ws = wb.add_worksheet("x")
	for goc in ('=HYPERLINK("http://x.invalid","Bấm")', "{=SUM(1,2)}"):
		ws.write(0, 0, dung_bang([{"k": "t", "nhan": "T"}], [{"t": goc}])[1][0])
		ws.write(1, 0, goc)
	wb.close()
	xml = zipfile.ZipFile(io.BytesIO(bo.getvalue())).read("xl/worksheets/sheet1.xml").decode()
	dung("dòng chưa qua phép an toàn là công thức (chứng minh phép đo đúng)", "<f" in xml.split('r="2"', 1)[1])
	dung("dòng đã qua phép an toàn là chữ", "<f" not in xml.split('r="1"', 1)[1].split('r="2"', 1)[0])


@ca("v534 hàng tặng: bản app cũ gửi trang_thai vẫn lọc ĐÚNG như trước v534 (Codex #382)")
def _tt_cu():
	from unittest.mock import patch
	from vagabond.khung.kiem_thu import nen
	from vagabond import hang_tang as ht
	dung("Đã duyệt cũ: nhận đơn chờ ghi sổ", ht.hop_trang_thai_cu("Đã duyệt", "Đã duyệt"))
	dung("Đã duyệt cũ: không nhận chờ duyệt", not ht.hop_trang_thai_cu("Đã duyệt", "Chờ duyệt"))
	dung("Chờ duyệt cũ nhận ô trống", ht.hop_trang_thai_cu("Chờ duyệt", ""))
	dung("trạng thái lạ thì không lọc", ht.hop_trang_thai_cu("abc", "Từ chối"))
	cu = nen.BANG_GIA.get("Sales Invoice")
	nen.BANG_GIA["Sales Invoice"] = [
		dict(name="A", creation="2026-09-01 10:00", owner="x", docstatus=0, posting_date="2026-09-01", vgb_tang_duyet="Đã duyệt", vgb_quay=""),
		dict(name="B", creation="2026-09-02 10:00", owner="x", docstatus=1, posting_date="2026-09-02", vgb_tang_duyet="Đã duyệt", vgb_quay=""),
		dict(name="C", creation="2026-09-03 10:00", owner="x", docstatus=0, posting_date="2026-09-03", vgb_tang_duyet="", vgb_quay=""),
		dict(name="D", creation="2026-09-04 10:00", owner="x", docstatus=0, posting_date="2026-09-04", vgb_tang_duyet="Từ chối", vgb_quay=""),
		dict(name="E", creation="2026-09-05 10:00", owner="x", docstatus=1, posting_date="2026-09-05", vgb_tang_duyet="", vgb_quay=""),
	]
	try:
		with patch.object(ht, "_diem_cua_don", lambda q: "Q1"), patch.object(ht.ten_nguoi, "gan", lambda *a, **k: None):
			ten = lambda **k: sorted(r["name"] for r in ht._tap(**k)["ra"])
			la("app cũ bấm Đã duyệt: cả chờ ghi sổ lẫn đã ghi sổ", ten(trang_thai="Đã duyệt"), ["A", "B"])
			la("app cũ bấm Chờ duyệt: gồm ô trống như cũ", ten(trang_thai="Chờ duyệt"), ["C", "E"])
			la("app cũ bấm Từ chối", ten(trang_thai="Từ chối"), ["D"])
			la("app mới bấm chặng thì chặng thắng", ten(chang="hoan_tat", trang_thai="Đã duyệt"), ["B", "E"])
			la("không lọc", ten(), ["A", "B", "C", "D", "E"])
	finally:
		if cu is None:
			nen.BANG_GIA.pop("Sales Invoice", None)
		else:
			nen.BANG_GIA["Sales Invoice"] = cu


# -------------------------------------------- mọi màn danh sách đều có công cụ

# Màn danh sách CHƯA dùng thanh công cụ chung, kèm lý do. Làm tới màn nào thì
# xoá dòng của màn đó; ca kiểm dưới bắt lỗi nếu màn đã dùng mà vẫn nằm ở đây.
DOT1B = "đợt 1b (Sales), anh Việt chốt làm sau v534"
DOT2 = "đợt 2 (Kế toán)"
DOT3 = "đợt 3 (Kho, bếp, giao hàng)"
KHONG_PHAI = "màn chọn trong lúc lập phiếu hoặc danh mục cài đặt ngắn, không phải sổ để tra"
MIEN = {
	"scrDsView": DOT1B, "scrKhachHang": DOT1B, "scrHopDong": DOT1B, "scrHopDongHub": DOT1B,
	"scrBaoGia": DOT1B, "scrKhuyenMai": DOT1B, "scrHoanTien": DOT1B, "scrDonHuy": DOT1B,
	"scrPhieuHoanHuy": DOT1B, "scrTqDot": DOT1B, "scrTqDs": DOT1B, "scrBntDs": DOT1B,
	"scrMuaVuDs": DOT1B, "scrMuaVu": DOT1B, "scrKhachChiTiet": DOT1B,
	"scrHdBan": DOT2, "scrHdMua": DOT2, "scrDoiChieuMua": DOT2, "scrHoSoTT": DOT2,
	"scrDeNghiChi": DOT2, "scrTTNB": DOT2, "scrNopQuy": DOT2, "scrButToan": DOT2,
	"scrTaiSan": DOT2, "scrBangGia": DOT2, "scrNcc": DOT2, "scrDonMua": DOT2,
	"scrDuyetYc": DOT2, "scrBaoCao": DOT2, "scrKPI": DOT2,
	"scrXkHuyList": DOT3, "scrXkCkList": DOT3, "scrMfgList": DOT3, "scrRecvList": DOT3,
	"scrVanDon": DOT3, "scrVdView": DOT3, "scrVdTuyen": DOT3, "scrKhsxDsPhieu": DOT3,
	"scrXkNbList": DOT3, "scrXkTraList": DOT3, "scrXkSiList": DOT3, "scrXkPvList": DOT3,
	"scrVclList": DOT3, "scrHuongDan": DOT3,
	"scrHoSoTTTao": KHONG_PHAI, "scrHoanUngTao": KHONG_PHAI, "scrChiCongTyTao": KHONG_PHAI,
	"scrNccGan": KHONG_PHAI, "scrTraTruocTao": KHONG_PHAI, "scrPhLap": KHONG_PHAI,
	"scrDiemBan": KHONG_PHAI, "scrPtThanhToan": KHONG_PHAI, "scrTaiKhoan": KHONG_PHAI,
	"scrCaiDatKho": KHONG_PHAI, "scrMayIn": KHONG_PHAI, "scrNguoiDung": KHONG_PHAI,
	"scrMauBg": KHONG_PHAI, "scrMauIn": KHONG_PHAI,
}
DOT1 = ("scrCongNo", "scrDuyetTang")


def _man_danh_sach():
	"""Màn nào là màn danh sách: hàm scr* gọi một hàm máy chủ kiểu danh sách.

	Đây là phép dò chuỗi, chỉ dùng để CHỐT PHẠM VI (quy tắc 16): màn mới
	thêm vào mà không dùng công cụ chung và không khai miễn thì đỏ.
	"""
	ra = {}
	for f in sorted(os.listdir(BEP)):
		if not re.match(r"^\d\d-.+\.js$", f):
			continue
		s = io.open(os.path.join(BEP, f), encoding="utf-8").read()
		for m in re.finditer(r"^(?:async )?function (scr\w+)\(", s, re.M):
			i = m.start()
			j = min(x for x in (s.find("\nfunction ", i + 10), s.find("\nasync function ", i + 10), len(s)) if x > 0)
			than = s[i:j]
			goi = re.findall(r"api\('vagabond\.([\w.]+)'", than)
			if any(re.search(r"\.(ds|danh_sach|ds_\w+|\w+_ds|bang)$", g) for g in goi):
				ra[m.group(1)] = (f, "dsCongCu(" in than)
	return ra


@ca("v534 mọi màn danh sách dùng thanh công cụ chung, hoặc nằm trong danh sách miễn có lý do")
def _moi_man():
	ds = _man_danh_sach()
	dung("dò ra được màn danh sách", len(ds) >= 50)
	sot = sorted(t for t, (_, co) in ds.items() if not co and t not in MIEN)
	la("màn danh sách chưa có công cụ mà không khai miễn", sot, [])
	thua = sorted(t for t in MIEN if t not in ds)
	la("miễn cho màn không còn tồn tại hoặc không còn là danh sách", thua, [])
	da_lam = sorted(t for t in MIEN if t in ds and ds[t][1])
	la("màn đã dùng công cụ mà vẫn nằm trong danh sách miễn", da_lam, [])
	for t in DOT1:
		dung("%s (đợt 1) dùng thanh công cụ chung" % t, t in ds and ds[t][1])
	for t, ly in MIEN.items():
		dung("miễn %s có lý do" % t, bool((ly or "").strip()))


@ca("v534 thanh công cụ: đúng thứ tự khối, nút Excel gọi cửa dùng chung, chạm đủ 44 điểm")
def _thanh():
	s = io.open(os.path.join(BEP, "15-khuon-danh-sach.js"), encoding="utf-8").read()
	i = s.find("function dsCongCu(c)")
	than = s[i:s.find("\nasync function dsXuatExcel", i)]
	thu_tu = [than.find("if (c.chang)"), than.find("(c.ho || [])"), than.find("if (c.ky)"), than.find("var coTim")]
	dung("đủ bốn khối", all(x > 0 for x in thu_tu))
	la("thứ tự chặng, lọc riêng, ngày, tìm và Excel", thu_tu, sorted(thu_tu))
	dung("Excel gọi cửa dùng chung", "api('vagabond.khung.cong_cu_ds.xuat_excel'" in s)
	dung("ô tìm và nút Excel cao 44", "height:44px" in than and "min-height:44px" in than)
	dung("không có ô select", "<select" not in than)


@ca("v534 ca hành vi chạy trong cổng trước deploy")
def _cong():
	sh = io.open(os.path.join(os.path.dirname(GOI), "kiem_truoc_deploy.sh"), encoding="utf-8").read()
	dung("cổng chạy cong_cu_ds_534.js", "node vagabond/khung/kiem_thu/hanh_vi/cong_cu_ds_534.js" in sh)


@ca("v534 ca tích hợp sổ cái đăng ký vào bộ kiểm thật (bench)")
def _dang_ky_that():
	c = _doc("khung", "kiem_that", "cua.py")
	dung("cua.py nạp thu_phieu_thu_unc_534", "import thu_phieu_thu_unc_534" in c)


@ca("v541 Khách đã chuyển tiền: đọc mã đơn, số điện thoại; xếp gợi ý nhưng không bỏ giao dịch nào")
def _goi_y_tien_ve():
	from vagabond import thu_tien as tt
	dh = tt.dau_hieu_don("Pancake #93367 - Ms.Thanh - 0933346399", "HDB-26-09-01294")
	la("mã đơn", dh["ma_don"], ["93367"])
	la("số điện thoại 9 số cuối", dh["dien_thoai"], ["933346399"])
	ds = [
		{"name": "BT-a", "date": "2026-09-10", "unallocated_amount": 745000, "description": "Lam Ngoc chuyen"},
		{"name": "BT-b", "date": "2026-09-12", "unallocated_amount": 1490000, "description": "CK DON 93367 VA 93368"},
		{"name": "BT-c", "date": "2026-09-09", "unallocated_amount": 745000, "description": "0933346399 chuyen tien banh"},
		{"name": "BT-d", "date": "2026-09-11", "unallocated_amount": 300000, "description": "khac"},
	]
	xep = tt.xep_ung_vien(ds, dh, 745000)
	la("đủ bốn, không bỏ cái nào", len(xep), 4)
	la("mã đơn lên đầu, rồi số điện thoại, rồi đúng tiền", [x["name"] for x in xep], ["BT-b", "BT-c", "BT-a", "BT-d"])
	la("lý do của dòng có mã đơn", xep[0]["khop"], ["nội dung có mã đơn 93367"])
	la("dòng điện thoại và đúng tiền", xep[1]["khop"], ["có số điện thoại khách", "đúng số tiền"])
	la("dòng lệch tiền không có lý do", xep[3]["khop"], [])
	la("không có dấu hiệu gì thì rỗng", tt.dau_hieu_don("", ""), {"ma_don": [], "dien_thoai": [], "ten_si": ""})
	# Codex #389 P2: nhiều khoản cùng điểm (cùng số tiền, không mã) thì khoản
	# MỚI trước, để khoản khách vừa chuyển nằm đầu danh sách.
	cung = [{"name": "BT-%02d" % i, "date": "2026-09-%02d" % i, "unallocated_amount": 745000, "description": "ck"}
		for i in range(1, 16)]
	xep = tt.xep_ung_vien(cung, dh, 745000)
	la("cùng điểm: mới nhất đứng đầu", [x["name"] for x in xep[:3]], ["BT-15", "BT-14", "BT-13"])
	la("không cắt: đủ 15 khoản", len(xep), 15)
	dung("không còn trần gợi ý nào (Codex #389 vòng 2)", not hasattr(tt, "GOI_Y_TOI_DA"))
	cung.append({"name": "BT-ma", "date": "2026-09-01", "unallocated_amount": 745000, "description": "DON 93367"})
	la("điểm cao vẫn trước ngày", tt.xep_ung_vien(cung, dh, 745000)[0]["name"], "BT-ma")


class _A(dict):
	__getattr__ = dict.get


@ca("Codex #389 P2 vòng 2: máy chủ trả ĐỦ mọi giao dịch ứng viên, không cắt, khoản mới nhất đứng đầu")
def _ung_vien_du():
	# Chạy ung_vien_tien_ve THẬT; chỉ giả frappe (bảng giao dịch 40 khoản cùng số
	# tiền, tôn trọng limit_page_length như site) và hàm kiểm quyền của ban_hang
	# (ban_hang kéo requests, CI tay không không có).
	import sys
	import types
	import unittest.mock
	from vagabond import thu_tien as tt
	gd = [_A(name="BT-%02d" % i, date="2026-09-%02d" % (i % 28 + 1), deposit=745000, unallocated_amount=745000,
		description="ck %d" % i, reference_number="FT%02d" % i, bank_account="MB") for i in range(1, 41)]
	gd.sort(key=lambda x: x["date"], reverse=True)

	def get_all(dt, filters=None, fields=None, pluck=None, limit_page_length=0, order_by=None, **k):
		if dt == "Bank Account":
			return ["MB"]
		if dt == tt.PE:
			return []
		if dt == tt.BT:
			ra = [g for g in gd if "description" not in (filters or {})]
			return ra[:limit_page_length] if limit_page_length else ra
		return []
	hd = _A(name="HDB-1", docstatus=1, outstanding_amount=745000, posting_date="2026-09-01", company="V",
		remarks="Pancake #93367", customer_name="Ms.Thanh")
	f = types.SimpleNamespace(get_all=get_all, db=types.SimpleNamespace(get_value=lambda *a, **k: hd),
		throw=lambda m: (_ for _ in ()).throw(ValueError(m)))
	gia_bh = types.ModuleType("vagabond.ban_hang")
	gia_bh._kiem_quyen_doc_luu_don = lambda: None
	with unittest.mock.patch.object(tt, "frappe", f), unittest.mock.patch.dict(sys.modules, {"vagabond.ban_hang": gia_bh}), \
			unittest.mock.patch("frappe.utils.add_days", lambda d, n: d, create=True):
		r = tt.ung_vien_tien_ve("HDB-1")
	la("đủ 40 khoản, không cắt", len(r["gd"]), 40)
	la("khoản mới nhất đứng đầu", r["gd"][0]["ngay"], max(g["date"] for g in gd))
