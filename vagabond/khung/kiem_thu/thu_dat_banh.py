"""Ca kiểm cho nền móng luồng khách đặt bánh ổ tại cửa hàng (issue #195).

Anh Việt chốt năm câu nghiệp vụ 05/09/2026: khách trả trước toàn bộ, thu
tiền mặt tại quầy được, đặt điểm này nhận điểm khác được, huỷ thì hoàn
tiền, hoá đơn VAT xuất ngày giao.

Bản này là phần NỀN, không có màn hình. Bốn thứ được canh:

1. Ba cái ngày không được lẫn: ngày đặt, ngày thu, ngày nhận.
2. Chốt ca không lệch ở CẢ HAI đầu. Tiền của một đơn vào két đúng MỘT lần,
   ở ngày thu.
3. Phần giữ chỗ tính theo ngày NHẬN, và không bao giờ đếm trùng với phần
   đã giao.
4. Đổi ngày chứng từ thì đo lại cả ngày cũ lẫn ngày mới. Đây là lỗi có sẵn
   từ trước, Codex bắt được khi soi issue.

Mọi ca chạy trên phép THUẦN và trên văn bản tệp: không cần Frappe, không
cần site, không cần mạng, không cần thư viện requests.
"""

import io
import os

from vagabond.dat_banh import (
	PT_TRA_TRUOC, con_giu_cho, gom_giu_cho, hai_ngay_phai_do, la_banh_o,
	tong_ung_truoc,
)
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.pt_thanh_toan import TIEN_NGAY_KHAC

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


DB = _doc("dat_banh.py")
CQ = _doc("ca_quay.py")
KB = _doc("kiem_banh.py")
PT = _doc("pt_thanh_toan.py")
TTT = _doc("truong_tu_them.py")
KBN = _doc(os.path.join("vagabond", "doctype", "kiem_banh_ngay", "kiem_banh_ngay.py"))


# ------------------------------------------------- Nhận diện bánh ổ


@ca("chi banh o moi vao bang, khong go lai tien to o hai noi")
def _banh_o():
	for x in ("BAWC-001", "baws-9", "BAWC"):
		dung("%r la banh o" % x, la_banh_o(x))
	for x in ("HOP-01", "PHIGIAO", "", None):
		dung("%r khong phai banh o" % x, not la_banh_o(x))
	# Go lai chuoi "BAWC" trong dat_banh.py la de ra hai noi noi khac nhau.
	dung("lay tien to tu kiem_banh", "from vagabond.kiem_banh import TIEN_TO_MA" in DB)
	dung("khong go lai tien to", '"BAWC"' not in DB and "'BAWC'" not in DB)


# ------------------------------------------------- Giữ chỗ, không đếm trùng


@ca("con giu cho = so dat tru phan da xong, khong bao gio am")
def _con_giu_cho():
	la("chua giao gi", con_giu_cho(3, 0, 0), 3)
	la("giao mot", con_giu_cho(3, 1, 0), 2)
	la("giao het", con_giu_cho(3, 3, 0), 0)
	la("giao qua so dat van ve khong", con_giu_cho(3, 5, 0), 0)
	la("so dat bang khong", con_giu_cho(0, 0, 0), 0)
	la("so dat am", con_giu_cho(-2, 0, 0), 0)


@ca("lay MAX cua da giao va da xuat hoa don, khong cong hai cot")
def _khong_cong_hai_cot():
	"""Hai duong hoan tat khac nhau cap nhat hai cot khac nhau. Cong lai la
	tru hai lan: khach dat 2 ma bang tuong da giao 4."""
	la("chi phieu giao chay", con_giu_cho(2, 2, 0), 0)
	la("chi hoa don chay", con_giu_cho(2, 0, 2), 0)
	# Ca hai cung chay cho CUNG mot lan giao: van la 2, khong phai 4.
	la("ca hai cung chay", con_giu_cho(2, 2, 2), 0)
	la("giao mot, xuat hoa don mot", con_giu_cho(2, 1, 1), 1)
	# Neu cong hai cot thi ca nay ra 0, tuc mat mot cai banh khoi bang.
	dung("khong bi cong thanh 0", con_giu_cho(2, 1, 1) != 0)


@ca("gom giu cho theo NGAY NHAN chu khong theo ngay dat")
def _gom_theo_ngay_nhan():
	dong = [
		{"item_code": "BAWC-01", "delivery_date": "2026-09-20", "qty": 2,
			"delivered_qty": 0, "billed_qty": 0},
		{"item_code": "BAWC-01", "delivery_date": "2026-09-22", "qty": 1,
			"delivered_qty": 0, "billed_qty": 0},
		{"item_code": "BAWS-07", "delivery_date": "2026-09-20", "qty": 5,
			"delivered_qty": 2, "billed_qty": 0},
	]
	g = gom_giu_cho(dong)
	la("hai ngay", sorted(g), ["2026-09-20", "2026-09-22"])
	la("ngay 20 banh 01", g["2026-09-20"]["BAWC-01"], 2)
	la("ngay 20 banh 07 tru phan da giao", g["2026-09-20"]["BAWS-07"], 3)
	la("ngay 22", g["2026-09-22"]["BAWC-01"], 1)


@ca("gom giu cho bo dong khong phai banh o, dong da xong, dong thieu ngay")
def _gom_bo_rac():
	dong = [
		{"item_code": "HOP-01", "delivery_date": "2026-09-20", "qty": 9,
			"delivered_qty": 0, "billed_qty": 0},
		{"item_code": "BAWC-01", "delivery_date": "", "qty": 2,
			"delivered_qty": 0, "billed_qty": 0},
		{"item_code": "BAWC-02", "delivery_date": "2026-09-20", "qty": 2,
			"delivered_qty": 2, "billed_qty": 0},
		None, "rac", {},
	]
	la("khong giu cho nao", gom_giu_cho(dong), {})
	la("danh sach rong", gom_giu_cho([]), {})


@ca("hai dong cung ma cung ngay thi cong don")
def _cong_don():
	dong = [
		{"item_code": "BAWC-01", "delivery_date": "2026-09-20", "qty": 2,
			"delivered_qty": 0, "billed_qty": 0},
		{"item_code": "bawc-01", "delivery_date": "2026-09-20", "qty": 3,
			"delivered_qty": 0, "billed_qty": 0},
	]
	la("cong don va chuan hoa ma", gom_giu_cho(dong)["2026-09-20"]["BAWC-01"], 5)


# ------------------------------------------------- Đổi ngày: đo lại hai ngày


@ca("doi ngay chung tu thi do lai CA ngay cu lan ngay moi")
def _hai_ngay():
	la("doi ngay", hai_ngay_phai_do("2026-09-20", "2026-09-22"),
		["2026-09-20", "2026-09-22"])
	la("khong doi thi mot ngay", hai_ngay_phai_do("2026-09-20", "2026-09-20"),
		["2026-09-20"])
	la("khong co ngay cu", hai_ngay_phai_do(None, "2026-09-22"), ["2026-09-22"])
	la("ca hai rong", hai_ngay_phai_do("", None), [])


@ca("hook hoa don goi do lai hai ngay, khong con goi mot ngay")
def _hook_hai_ngay():
	"""Loi co san tu truoc: ban cu chi goi cap_nhat_don_khac(doc.posting_date),
	tuc ngay MOI. Doi ngay tu 20 sang 22 thi ngay 20 van tru mot cai banh cua
	to hoa don da khong con o do."""
	i = KB.find("def khi_doi_hoa_don(")
	than = KB[i:KB.find("def dong_bo_tu_dong", i)]
	dung("dung ham do hai ngay", "hai_ngay_phai_do" in than)
	dung("doc lai ban truoc khi luu", "get_doc_before_save" in than)
	dung("khong con goi thang mot ngay", "cap_nhat_don_khac(doc.posting_date)" not in than)


# ------------------------------------------------- Chốt ca, hai đầu


@ca("nhom tien thu ngay khac la nhom RIENG, khong nhap vao bon nhom cu")
def _nhom_rieng():
	la("ma nhom", TIEN_NGAY_KHAC, "ngay_khac")
	for cu in ('"ngay"', '"sau"', '"cong_no"', '"khong_thu"'):
		dung("khong trung ma nhom %s" % cu, ('TIEN_NGAY_KHAC = %s' % cu) not in PT)
	dung("co ham doc nhom", "def thu_ngay_khac()" in PT)
	dung("hien tren man Cai dat", "Đã thu ngày khác" in PT)
	dung("co phuong thuc Tra truoc", '"ten": "Trả trước"' in PT)
	la("ten phuong thuc dung mot cho", PT_TRA_TRUOC, "Trả trước")


@ca("dau ngay giao: phuong thuc Tra truoc roi khoi bang doi soat ket")
def _dau_ngay_giao():
	i = CQ.find("def _ngoai_ket()")
	than = CQ[i:CQ.find("def _pt_cua_diem", i)]
	dung("ke nhom thu ngay khac", "thu_ngay_khac()" in than)
	# Ba nhom cu phai con nguyen, khong duoc thay the.
	for x in ("chua_ve_tien()", "ve_sau()", "khong_thu()"):
		dung("con giu nhom %s" % x, x in than)


@ca("dau ngay thu: chot ca cong them tien khach tra truoc")
def _dau_ngay_thu():
	i = CQ.find("def _doanh_thu_he_thong(")
	than = CQ[i:CQ.find("def tinh_trang(", i)]
	dung("goi ham thu ung truoc", "dat_banh.thu_ung_truoc(" in than)
	# Phai theo dung quy uoc moc thoi gian cua chinh ham do, khong thi mot
	# ca mo 8h se nuot ca tien cua hom qua.
	dung("theo dung moc thoi gian tung loai diem", "theo_ngay=not _co_quay(diem)" in than)
	# Nuot loi: doc chung tu thu hong khong duoc lam thu ngan khong chot
	# duoc ca.
	j = than.find("dat_banh.thu_ung_truoc(")
	dung("boc trong try", "try:" in than[max(0, j - 400):j])


@ca("tien ung truoc chi dem phan CHUA gan vao hoa don")
def _chua_gan():
	"""Khoan da gan het vao hoa don la tien tra cho mot to da ton tai, va to
	do da duoc dem o duong thuong. Cong them la dem hai lan."""
	i = DB.find("def thu_ung_truoc(")
	than = DB[i:]
	dung("loc theo phan chua gan", '"unallocated_amount": [">", 0]' in than)
	dung("chi lay chung tu da ghi so", '"docstatus": 1' in than)
	dung("chi lay chieu thu", '"payment_type": "Receive"' in than)
	dung("chi lay khach hang", '"party_type": "Customer"' in than)
	dung("loc theo quay", '"vgb_quay"' in than)


@ca("gom tien ung truoc theo phuong thuc, bo dong khong duong")
def _gom_ung_truoc():
	rows = [
		{"pt": "Tiền mặt", "so_tien": 500000},
		{"pt": "Tiền mặt", "so_tien": 300000},
		{"pt": "Chuyển khoản", "so_tien": 1200000},
		{"pt": "Tiền mặt", "so_tien": -100000},
		{"pt": "Tiền mặt", "so_tien": 0},
		None, "rac",
	]
	g = tong_ung_truoc(rows)
	la("tien mat cong don", g["Tiền mặt"], 800000.0)
	la("chuyen khoan", g["Chuyển khoản"], 1200000.0)
	la("khong sinh nhom la", sorted(g), ["Chuyển khoản", "Tiền mặt"])
	la("danh sach rong", tong_ung_truoc([]), {})


@ca("phuong thuc trong khong bi nuot, ve nhom Chua ro")
def _chua_ro():
	la("pt rong", tong_ung_truoc([{"pt": "", "so_tien": 5000}]), {"Chưa rõ": 5000.0})


# ------------------------------------------------- Bảng kiểm bánh


@ca("bang kiem banh co cot giu cho va TRU no vao so co the ban")
def _cot_giu_cho():
	import json

	j = json.load(io.open(os.path.join(
		GOI, "vagabond", "doctype", "kiem_banh_dong", "kiem_banh_dong.json"),
		encoding="utf-8"))
	ten = [f["fieldname"] for f in j["fields"]]
	dung("co cot giu cho", "giu_cho" in ten)
	dung("cot nam trong field_order", "giu_cho" in (j.get("field_order") or []))
	la("so o bang so dong field_order", len(j["fields"]), len(j["field_order"]))
	# Them cot ma quen tru la bang bay ra mot con so khong ai dung toi.
	dung("co the ban tru giu cho", "- (d.giu_cho or 0)" in KBN)
	for cu in ("d.da_dat", "d.phat_sinh", "d.cho_chot", "d.don_khac"):
		dung("van tru %s" % cu, ("- (%s or 0)" % cu) in KBN)


@ca("ngay da chot so thi khong dung vao cot giu cho nua")
def _ngay_da_chot():
	i = KB.find("def _ghi_giu_cho(")
	than = KB[i:KB.find("def _ghi_don_khac(", i)]
	dung("co chan ngay da chot", 'doc.tinh_trang == "Da chot"' in than)
	dung("do giu cho tu dat_banh", "dat_banh.dem_giu_cho" in than)


@ca("chi dem phieu dat con hieu luc")
def _con_hieu_luc():
	i = DB.find("def dong_phieu_dat(")
	than = DB[i:DB.find("def dem_giu_cho(", i)]
	dung("chi phieu da ghi so", '"docstatus": 1' in than)
	dung("bo phieu da dong va da huy", '["Closed", "Cancelled"]' in than)


# ------------------------------------------------- Ô trên chứng từ thu


@ca("o quay thu tien va o phieu dat da khai va da dang ky dung lai")
def _o_moi():
	dung("khai o quay", '"fieldname": "vgb_quay"' in DB)
	dung("khai o phieu dat", '"fieldname": "vgb_phieu_dat"' in DB)
	dung("hai o deu chi doc", DB.count('"read_only": 1') >= 2)
	# Khai ma quen dang ky thi sau moi lan deploy o bien mat.
	dung("da dang ky trong truong tu them", "dat_banh.TRUONG_MOI" in TTT)


@ca("ba cai ngay duoc noi ro trong tai lieu cua mo dun")
def _ba_ngay():
	"""Anh Viet hoi 05/09: nhap luon ngay thu tien va ngay lay banh duoc
	khong. Duoc, va phai tach han ba cai ngay ra."""
	for x in ("Ngày ĐẶT", "Ngày THU", "Ngày NHẬN"):
		dung("co noi ve %s" % x, x in DB)
	dung("noi ro bat bien mot lan", "đúng MỘT lần" in DB)
