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
	PT_TRA_TRUOC, con_giu_cho, gom_giu_cho, gop_ngay, hai_ngay_phai_do,
	la_banh_o, la_phieu_ung_truoc, ngay_nhan_cua_phieu, tien_thuc_thu,
	tong_ung_truoc,
)
from vagabond.khung.kiem_thu.nen import Doi, ca, dung, la
from vagabond.kiem_banh import TIEN_TO_MA
from vagabond.pt_thanh_toan import TIEN_NGAY_KHAC

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


DB = _doc("dat_banh.py")
HK = _doc("hooks.py")
CQ = _doc("ca_quay.py")
KB = _doc("kiem_banh.py")
PT = _doc("pt_thanh_toan.py")
TTT = _doc("truong_tu_them.py")
KBN = _doc(os.path.join("vagabond", "doctype", "kiem_banh_ngay", "kiem_banh_ngay.py"))


# ------------------------------------------------- Nhận diện bánh ổ


@ca("chi banh o moi vao bang, khong go lai tien to o hai noi")
def _banh_o():
	for x in ("BAWC-001", "baws-9", "BAWC"):
		dung("%r la banh o" % x, la_banh_o(x, TIEN_TO_MA))
	for x in ("HOP-01", "PHIGIAO", "", None):
		dung("%r khong phai banh o" % x, not la_banh_o(x, TIEN_TO_MA))
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
	g = gom_giu_cho(dong, TIEN_TO_MA)
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
	la("khong giu cho nao", gom_giu_cho(dong, TIEN_TO_MA), {})
	la("danh sach rong", gom_giu_cho([], TIEN_TO_MA), {})


@ca("hai dong cung ma cung ngay thi cong don")
def _cong_don():
	dong = [
		{"item_code": "BAWC-01", "delivery_date": "2026-09-20", "qty": 2,
			"delivered_qty": 0, "billed_qty": 0},
		{"item_code": "bawc-01", "delivery_date": "2026-09-20", "qty": 3,
			"delivered_qty": 0, "billed_qty": 0},
	]
	la("cong don va chuan hoa ma", gom_giu_cho(dong, TIEN_TO_MA)["2026-09-20"]["BAWC-01"], 5)


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


@ca("tien ung truoc lay so THUC THU, khong lay so du chua gan")
def _khong_dung_so_du():
	"""Codex bat o PR #197. Chung tu thu tao dung cach tu phieu dat co dong
	tham chieu tro ve phieu do; gan du xong thi unallocated_amount ve 0, tuc
	la moi khoan tra truoc CHUAN deu bi loai khoi ca. Con so ay lai con DOI
	ve sau luc khoan ung duoc can vao hoa don ngay giao, ma ca cua ngay thu
	la so lich su, khong duoc phep doi theo viec xay ra o ngay khac."""
	i = DB.find("def thu_ung_truoc(")
	than = DB[i:]
	dung("khong con loc theo so du chua gan", "unallocated_amount" not in than)
	dung("chi lay chung tu da ghi so", '"docstatus": 1' in than)
	dung("chi lay chieu thu", '"payment_type": "Receive"' in than)
	dung("chi lay khach hang", '"party_type": "Customer"' in than)
	dung("loc theo quay", '"vgb_quay"' in than)
	# So thuc thu: uu tien so vao tai khoan nhan, thieu thi lay so tra.
	la("lay so vao tai khoan nhan", tien_thuc_thu(
		{"received_amount": 500000, "paid_amount": 9}), 500000.0)
	la("thieu thi lay so tra", tien_thuc_thu(
		{"received_amount": 0, "paid_amount": 700000}), 700000.0)
	la("rong ve khong", tien_thuc_thu({}), 0.0)


@ca("chi cong chung tu thu CUA luong dat banh, khong cong tien nop thua")
def _dung_dau_hieu():
	"""Codex bat o PR #197: ban dau khong doi dau hieu nao, nen moi khoan
	khach nop thua o quay deu bi cong vao ca nhu tien dat banh."""
	dung("co o phieu dat thi nhan", la_phieu_ung_truoc(
		{"vgb_phieu_dat": "SO-2026-00007"}, False))
	dung("co dong tham chieu thi nhan", la_phieu_ung_truoc(
		{"vgb_phieu_dat": ""}, True))
	dung("khong dau hieu nao thi loai", not la_phieu_ung_truoc(
		{"vgb_phieu_dat": ""}, False))
	dung("o toan khoang trang khong tinh", not la_phieu_ung_truoc(
		{"vgb_phieu_dat": "   "}, False))
	i = DB.find("def thu_ung_truoc(")
	than = DB[i:]
	dung("co doi dau hieu", "la_phieu_ung_truoc(" in than)
	dung("co hoi bang dong tham chieu", "_tro_toi_phieu_dat(" in than)


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


# ------------------------------------------------- Codex PR #197: hành vi thật
#
# Bốn ca dưới đây chạy trên bản Frappe giả có LỌC, chứ không chỉ tìm chuỗi
# trong mã nguồn. Codex nói đúng: cổng xanh mà toàn ca tìm chuỗi thì không
# chứng minh được đường chạm cơ sở dữ liệu có đúng hay không.


class _Dong(dict):
	"""Một dòng con trên bảng kiểm bánh, truy cập được bằng dấu chấm."""

	def __getattr__(self, k):
		return self.get(k)

	def __setattr__(self, k, v):
		self[k] = v


class _Bang:
	"""Bản ghi kiểm bánh giả, đủ cho _ghi_giu_cho làm việc."""

	def __init__(self, ma_hang, tinh_trang="Dang mo"):
		self.tinh_trang = tinh_trang
		self.dong = [_Dong({"ma_hang": m, "giu_cho": 0}) for m in ma_hang]

	def append(self, _bang, gia_tri):
		d = _Dong(dict(gia_tri, giu_cho=0))
		self.dong.append(d)
		return d


def _gia_lap_get_all(bang):
	"""Trả về hàm thay cho frappe.get_all, CÓ tôn trọng bộ lọc.

	`bang` là {doctype: list dict}. Bản giả trong nen.py bỏ qua bộ lọc, nên
	không dùng để kiểm phần lọc được.
	"""
	def _chay(dt, filters=None, fields=None, pluck=None, **k):
		ds = list(bang.get(dt) or [])
		for o, dk in (filters or {}).items():
			if isinstance(dk, list) and len(dk) == 2 and dk[0] == "in":
				ds = [r for r in ds if r.get(o) in dk[1]]
			elif isinstance(dk, list) and len(dk) == 2 and dk[0] == "not in":
				ds = [r for r in ds if r.get(o) not in dk[1]]
			elif isinstance(dk, list) and len(dk) == 2 and dk[0] == "between":
				ds = [r for r in ds if dk[1][0] <= str(r.get(o) or "") <= dk[1][1]]
			elif isinstance(dk, list) and len(dk) == 2 and dk[0] in (">", ">=", "<", "<="):
				# Phai hieu ca phep so sanh, khong thi mot bo loc sai lot qua
				# ma ca kiem van xanh. Dung dieu do da xay ra: cay lai loi
				# "unallocated_amount > 0" ma ca kiem hanh vi khong keu.
				import operator

				ph = {">": operator.gt, ">=": operator.ge,
					"<": operator.lt, "<=": operator.le}[dk[0]]
				ds = [r for r in ds if ph(float(r.get(o) or 0), float(dk[1]))]
			elif isinstance(dk, list) and len(dk) == 2 and dk[0] == "is":
				ds = [r for r in ds if (
					bool(str(r.get(o) or "").strip())
					if dk[1] == "set" else not str(r.get(o) or "").strip()
				)]
			elif not isinstance(dk, list):
				ds = [r for r in ds if r.get(o) == dk]
		if pluck:
			return [r.get(pluck) for r in ds]
		# Frappe that tra ve _dict (truy cap duoc bang dau cham), khong phai
		# dict tran. Tra dict tran thi ca kiem xanh gia o day ma no o site.
		return [Doi(r) for r in ds]
	return _chay


@ca("phieu thu da gan HET vao phieu dat van duoc tinh dung mot lan vao ca")
def _gan_het_van_tinh():
	"""Đây chính là lỗi Codex bắt: bộ lọc cũ đòi số dư chưa gán phải dương,
	nên chứng từ thu chuẩn (đã gán đủ, số dư 0) bị loại sạch khỏi chốt ca.
	Ngày khách trả tiền, két thừa nguyên giá trị đơn mà không ai giải thích
	được."""
	import frappe

	from vagabond import dat_banh

	cu = frappe.get_all
	frappe.get_all = _gia_lap_get_all({
		"Payment Entry": [
			# Chuẩn: gán đủ vào phiếu đặt, số dư chưa gán bằng 0.
			{"name": "PE-1", "creation": "2026-09-05 10:00:00", "mode_of_payment": "Tiền mặt", "vgb_quay": "SALES",
				"docstatus": 1, "payment_type": "Receive", "party_type": "Customer",
				"vgb_phieu_dat": "SO-2026-00007", "unallocated_amount": 0,
				"received_amount": 850000, "paid_amount": 850000},
			# Khách nộp thừa ở quầy, không dính gì tới đặt bánh.
			{"name": "PE-2", "creation": "2026-09-05 10:00:00", "mode_of_payment": "Tiền mặt", "vgb_quay": "SALES",
				"docstatus": 1, "payment_type": "Receive", "party_type": "Customer",
				"vgb_phieu_dat": "", "unallocated_amount": 300000,
				"received_amount": 300000, "paid_amount": 300000},
			# Đúng luồng nhưng đi đường Desk: không có ô, có dòng tham chiếu.
			{"name": "PE-3", "creation": "2026-09-05 10:00:00", "mode_of_payment": "Chuyển khoản", "vgb_quay": "SALES",
				"docstatus": 1, "payment_type": "Receive", "party_type": "Customer",
				"vgb_phieu_dat": "", "unallocated_amount": 0,
				"received_amount": 1200000, "paid_amount": 1200000},
			# Quầy khác, không được lẫn sang ca này.
			{"name": "PE-4", "creation": "2026-09-05 10:00:00", "mode_of_payment": "Tiền mặt", "vgb_quay": "TCV",
				"docstatus": 1, "payment_type": "Receive", "party_type": "Customer",
				"vgb_phieu_dat": "SO-2026-00009", "unallocated_amount": 0,
				"received_amount": 999000, "paid_amount": 999000},
		],
		"Payment Entry Reference": [
			{"parent": "PE-3", "reference_doctype": "Sales Order"},
			{"parent": "PE-2", "reference_doctype": "Sales Invoice"},
		],
	})
	try:
		g = dat_banh.thu_ung_truoc("SALES", "2026-09-05 00:00:00", "2026-09-05 23:59:59")
	finally:
		frappe.get_all = cu
	la("tien mat dung mot lan", g.get("Tiền mặt"), 850000.0)
	la("chuyen khoan qua duong tham chieu", g.get("Chuyển khoản"), 1200000.0)
	dung("khong cong tien nop thua", g.get("Tiền mặt") != 1150000.0)
	dung("khong lay tien cua quay khac", 999000.0 not in g.values())


@ca("ma banh chi co tren phieu dat van duoc them dong vao bang")
def _them_dong_thieu():
	"""Codex bắt: vòng đồng bộ thường chỉ thêm mã từ đơn Pancake và từ hoá
	đơn bán. Một loại bánh chỉ mới có khách đặt trước thì không có dòng nào,
	nên số giữ chỗ của nó không trừ vào khả năng bán, và cùng một cái bánh
	bán được hai lần."""
	import frappe

	from vagabond import kiem_banh

	bang = _Bang(["BAWC00001"])
	cu_ga, cu_dem = frappe.get_all, None
	from vagabond import dat_banh
	cu_dem = dat_banh.dem_giu_cho
	frappe.get_all = _gia_lap_get_all({
		"Item": [{"name": "BAWS00007", "item_name": "Bánh mới", "image": ""}],
	})
	dat_banh.dem_giu_cho = lambda ngay: {"BAWC00001": 2, "BAWS00007": 3}
	try:
		kiem_banh._ghi_giu_cho(bang, "2026-09-20")
	finally:
		frappe.get_all, dat_banh.dem_giu_cho = cu_ga, cu_dem
	co = {d.ma_hang: d for d in bang.dong}
	la("da them dong con thieu", sorted(co), ["BAWC00001", "BAWS00007"])
	la("dong cu duoc do", co["BAWC00001"].giu_cho, 2)
	la("dong moi duoc do", co["BAWS00007"].giu_cho, 3)
	la("lay ten tu danh muc hang hoa", co["BAWS00007"].ten_banh, "Bánh mới")


@ca("doc so giu cho hong thi GIU NGUYEN so cu, khong ghi 0")
def _khong_fail_open():
	"""Codex bắt: bản đầu nuốt lỗi rồi trả về rỗng, bên gọi hiểu rỗng là
	không còn ai đặt và ghi 0 vào mọi dòng. Một trục trặc cơ sở dữ liệu vài
	giây sẽ nhả toàn bộ bánh đã giữ của khách ra bán tiếp, im lặng."""
	from vagabond import dat_banh, kiem_banh

	bang = _Bang(["BAWC00001"])
	bang.dong[0].giu_cho = 5
	cu = dat_banh.dem_giu_cho

	def _no(ngay):
		raise Exception("gia lap loi co so du lieu")

	dat_banh.dem_giu_cho = _no
	try:
		ra = kiem_banh._ghi_giu_cho(bang, "2026-09-20")
	finally:
		dat_banh.dem_giu_cho = cu
	la("bao cho ben goi biet la doc hong", ra, None)
	la("so cu con nguyen", bang.dong[0].giu_cho, 5)
	# Va chinh dem_giu_cho khong duoc nuot loi nua.
	i = DB.find("def dem_giu_cho(")
	than = DB[i:DB.find("def ngay_nhan_cua(", i)]
	dung("dem_giu_cho khong nuot loi", "except Exception" not in than)


@ca("ngay da chot khong bi sua du co phieu dat moi")
def _da_chot_van_yen():
	from vagabond import kiem_banh

	bang = _Bang(["BAWC00001"], tinh_trang="Da chot")
	bang.dong[0].giu_cho = 4
	la("tra ve rong", kiem_banh._ghi_giu_cho(bang, "2026-09-20"), {})
	la("khong dung vao so cu", bang.dong[0].giu_cho, 4)


# ------------------------------------------------- Codex PR #197: đường nối


@ca("phieu dat co hook rieng, khong doi hoa don chay qua moi do giu cho")
def _co_hook_phieu_dat():
	"""Codex bắt: không có mục này thì lập một phiếu đặt hợp lệ xong, cột
	giữ chỗ vẫn bằng 0 cho tới khi tình cờ có một hoá đơn khác chạy qua."""
	i = HK.find('"Sales Order": {')
	dung("co khai Sales Order trong doc_events", i > 0)
	than = HK[i:HK.find("}", i)]
	for cua in ("on_submit", "on_update_after_submit", "on_cancel", "on_trash",
			"on_update"):
		dung("bat cua %s" % cua, cua in than)
	dung("goi dung ham", "vagabond.kiem_banh.khi_doi_phieu_dat" in than)
	# Ham do phai do ca ngay cu lan ngay moi, va khong duoc nem loi ra ngoai
	# vi no chay giua luot luu phieu cua sales.
	j = KB.find("def khi_doi_phieu_dat(")
	th = KB[j:KB.find("def khi_doi_hoa_don(", j)]
	dung("doc ban truoc khi luu", "get_doc_before_save" in th)
	dung("gop ca hai ben ngay", "gop_ngay(" in th)
	dung("nuot loi", "except Exception" in th)


@ca("nhip dong bo tu chua cot giu cho neu hook tung hong")
def _dong_bo_tu_chua():
	i = KB.find("def dong_bo(")
	than = KB[i:KB.find("def _lay_hoac_tao(", i)]
	if not than:
		than = KB[i:i + 12000]
	dung("nhip dong bo co do lai giu cho", "_ghi_giu_cho(doc, ngay)" in than)
	dung("van do kenh khac", "_ghi_don_khac(doc, ngay)" in than)


@ca("phuong thuc Tra truoc khong hien o man chon thanh toan")
def _tra_truoc_khong_hien():
	"""Codex bắt: để hiện ra thì thu ngân chọn nhầm được cho một hoá đơn bán
	thường, mà nhóm tiền này bị loại khỏi bảng đối soát, nên một khoản tiền
	THẬT vừa thu sẽ biến mất khỏi số két phải có."""
	from vagabond import pt_thanh_toan

	tt = [x for x in pt_thanh_toan.MAC_DINH if x.get("ten") == PT_TRA_TRUOC]
	la("co dung mot khai bao", len(tt), 1)
	la("khong hien o man quay", tt[0].get("quay"), 0)
	la("khong hien cho don online", tt[0].get("online"), 0)
	la("bat khai so phieu dat", tt[0].get("bat"), 1)
	la("dung nhom tien ngay khac", tt[0].get("tien_ve"), TIEN_NGAY_KHAC)


@ca("gop ngay cua phieu dat: nhieu dong nhieu ngay, bo trung va bo rong")
def _gop_ngay_phieu():
	dong = [
		{"item_code": "BAWC00001", "delivery_date": "2026-09-20"},
		{"item_code": "BAWS00007", "delivery_date": "2026-09-22"},
		{"item_code": "BAWC00002", "delivery_date": "2026-09-20"},
		{"item_code": "HOP-01", "delivery_date": "2026-09-25"},
		{"item_code": "BAWC00003", "delivery_date": ""},
	]
	la("chi ngay cua banh o, bo trung", ngay_nhan_cua_phieu(dong, TIEN_TO_MA),
		["2026-09-20", "2026-09-22"])
	la("gop hai ben", gop_ngay(["2026-09-20"], ["2026-09-22", "2026-09-20"]),
		["2026-09-20", "2026-09-22"])
	la("gop ban rong", gop_ngay([], None), [])
	# Dong da giao xong VAN phai co trong danh sach: chinh no la dong phai do
	# lai de nha so giu cho ra.
	la("dong da giao van duoc ke", ngay_nhan_cua_phieu(
		[{"item_code": "BAWC00001", "delivery_date": "2026-09-20"}], TIEN_TO_MA),
		["2026-09-20"])


@ca("phan thuan cua dat_banh khong dung frappe")
def _phan_thuan_sach():
	"""AGENTS.md: phan thuan phai chay duoc khong can khung. Vi vay phan
	tren khong import frappe, va nhan tien to ma banh qua tham so chu khong
	tu di lay (di lay la keo theo kiem_banh, tuc keo theo frappe)."""
	tren = DB[:DB.find("# ------------------------------------------------------------- chạm Frappe")]
	dung("phan thuan khong import frappe", "import frappe" not in tren)
	dung("phan thuan khong dung frappe.utils", "from frappe.utils" not in tren)
	dung("phan thuan khong nap kiem_banh", "from vagabond.kiem_banh" not in tren)
	dung("nhan tien to qua tham so", "def la_banh_o(ma, tien_to)" in tren)
