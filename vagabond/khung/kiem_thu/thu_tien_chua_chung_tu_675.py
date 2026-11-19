"""v675 (anh Việt 19/11/2026): hai tin 08:00 tiền vào / tiền ra chưa có chứng từ
gom theo nhóm việc, chỉ khoản từ 01/11/2026, tiền vào chỉ tài khoản chính; phiếu
chi đã xác nhận được nối đối chiếu lõi để không hiện lại mỗi sáng.

Mô tả sao kê trong ca lấy từ dòng thật trên site sáng 19/11/2026.
"""
import unittest.mock as um

from vagabond import duyet_chi as DC
from vagabond import tien_chua_chung_tu as T
from vagabond.khung.kiem_thu.nen import ca, dung, la

VAO = [
	{"tien": 200000000, "ngay": "2026-11-10", "mo_ta": "VAGABOND CHUYEN TIEN NOI BO TU SHINHAN QUA MB aJJ3ZI8R/81838"},
	{"tien": 165000000, "ngay": "2026-11-15", "mo_ta": "MBVCB.17050490942.197979.mts ck.CT tu 1033507466 MA THANH SON toi 31561568"},
	{"tien": 28514550, "ngay": "2026-11-16", "mo_ta": "PVS1505135 OnePay tam ung VAGABOND VIETQR 0h 13 11 26 den 23"},
	{"tien": 9494545, "ngay": "2026-11-05", "mo_ta": "Grab TT 122249866 2023073788274689 The Vagabond Patisserie Cafe"},
	{"tien": 1186702, "ngay": "2026-11-05", "mo_ta": "SHOPEEPAY CHUYEN TIEN 2118134985461964800 ShopeeFood thanh toan tu don"},
	{"tien": 133980, "ngay": "2026-11-05", "mo_ta": "dbl0imnn1mmc+GSM TT tien rut vi MC 051126"},
	{"tien": 442000, "ngay": "2026-11-09", "mo_ta": "4884373 beFood thanh toan ky 05112026 06112026"},
	{"tien": 429375, "ngay": "2026-11-16", "mo_ta": "Payoo TT TD ngay 13 11 15 11 2026 VAGABOND TONG"},
	{"tien": 787000, "ngay": "2026-11-05", "mo_ta": "PANCAKE2278 4 S67355O96995T0501194932 96995"},
	{"tien": 8096000, "ngay": "2026-11-10", "mo_ta": "HO KINH DOANH RAVIE chuyen tien banh T10 cho Vagabond"},
]
RA = [
	{"tien": 9180000, "ngay": "2026-11-06", "mo_ta": "MBCT VAGABOND TT HD NCC CONG TY TNHH THUONG MAI NGUYEN LIEU ZUNAVI APP 26 11 181"},
	{"tien": 6864094, "ngay": "2026-11-16", "mo_ta": "RetailVISADN-833087-6864094-VND-631912528186-FACEBK 8XYTDE2PJ4-The 657832920"},
	{"tien": 75505, "ngay": "2026-11-16", "mo_ta": "RetailVISADN-833087-6864094-VND-631912528186-FACEBK 8XYTDE2PJ4-The 657832920"},
	{"tien": 8053433, "ngay": "2026-10-28", "mo_ta": "MTC:00102026042973662800 MST:0318561568 CQT:1140957-Phuong Sai Gon - Thue co so"},
	{"tien": 3240000, "ngay": "2026-11-16", "mo_ta": "VGB TT QC SHOPEE"},
	{"tien": 2626800, "ngay": "2026-11-03", "mo_ta": "S6607892 - Ma giao dich/ Trace 286252"},
]


@ca("v675: nhận diện nhóm trên dòng sao kê thật (nội bộ, đối tác, Pancake, thẻ, thuế, NCC, chưa rõ)")
def _nhom():
	la("nhóm tiền vào", [T.nhom_cua(g["mo_ta"], T.NHOM_VAO) for g in VAO],
		["noi_bo", "khac", "doi_tac", "doi_tac", "doi_tac", "doi_tac", "doi_tac", "doi_tac", "pancake", "khac"])
	la("nhóm tiền ra", [T.nhom_cua(g["mo_ta"], T.NHOM_RA) for g in RA], ["ncc", "the", "the", "thue", "khac", "khac"])


@ca("v675: tin tiền vào gom theo nhóm, nhóm lớn trước, chưa rõ nguồn đứng cuối và liệt kê từng khoản")
def _soan_vao():
	td, dong = T.soan_vao(VAO)
	la("tiêu đề giữ nguyên", td, "Tiền vào tài khoản công ty chưa gắn chứng từ")
	dung("dòng tổng: 10 khoản, từ 01/11/2026: %s" % dong[0], dong[0].startswith("10 khoản, tổng 414.084.152 đ") and "01/11/2026" in dong[0])
	dung("nhóm nội bộ đứng đầu (200 tr): %s" % dong[1], dong[1].startswith("Chuyển nội bộ giữa tài khoản công ty: 1 khoản, 200.000.000 đ"))
	dung("nhóm đối tác một dòng 6 khoản: %s" % dong[2], dong[2].startswith("Tiền đối tác về") and ": 6 khoản, 40.201.152 đ" in dong[2])
	dung("nhóm chưa rõ nguồn cuối, kèm từng khoản lớn trước", dong[-3].startswith("Chưa rõ nguồn: 2 khoản, 173.096.000 đ")
		and "165.000.000 đ" in dong[-2] and "8.096.000 đ" in dong[-1])
	la("không khoản thì không tin", T.soan_vao([]), None)


@ca("v675: tin tiền ra gom theo nhóm; khoản chưa rõ nội dung liệt kê, cắt ở tối đa")
def _soan_ra():
	td, dong = T.soan_ra(RA)
	la("tiêu đề", td, "Tiền ra khỏi tài khoản công ty chưa có chứng từ")
	dung("trả NCC đứng trước thẻ (9,18 tr > 6,94 tr): %s" % dong[1], dong[1].startswith("Trả nhà cung cấp chưa nối phiếu chi: 1 khoản, 9.180.000 đ"))
	dung("thẻ gộp phí ngoại tệ: %s" % dong[3], any(d.startswith("Trừ thẻ Visa (Meta, phần mềm, phí ngoại tệ): 2 khoản, 6.939.599 đ") for d in dong))
	dung("chưa rõ nội dung cuối", dong[-3].startswith("Chưa rõ nội dung: 2 khoản"))
	nhieu = [{"tien": 1000 + i, "ngay": "2026-11-0%d" % (i % 9 + 1), "mo_ta": "KHOAN LA %d" % i} for i in range(8)]
	la("cắt khoản lẻ ở 5", T.soan_ra(nhieu)[1][-1], "  +3 khoản khác")


@ca("v675: chỉ nhắc khoản từ 01/11/2026 (anh Việt chốt), ngày rỗng không nhắc")
def _moc():
	la("mốc", T.MOC_NHAC, "2026-11-01")
	la("31/10 bỏ, 01/11 nhắc, rỗng bỏ", [T.tu_moc("2026-10-31"), T.tu_moc("2026-11-01"), T.tu_moc(None)], [False, True, False])


class _Db(object):
	"""Bản giả db.sql: áp đúng điều kiện ngày, tài khoản của câu thật (tham số
	theo thứ tự trong câu), để ca thấy được khoản cũ và quỹ tạm ứng có bị lọt."""

	def __init__(self, dong):
		self.dong = dong
		self.q = []

	def sql(self, q, a=None, as_dict=False, **k):
		self.q.append(q)
		if "tabBank Transaction" not in q:
			return []
		a = list(a)
		tu = a.pop(0) if "date >= %s" in q else "0000"
		a.pop(0)
		tk = a.pop(0) if "bank_account in %s" in q else None
		from frappe import _dict
		return [_dict(x) for x in self.dong if str(x["date"]) >= tu and (tk is None or x["bank_account"] in tk)
			and (x.get("deposit", 0) > 0 if "deposit > 0" in q else x.get("withdrawal", 0) > 0)]


@ca("v675: tin tiền vào chỉ tài khoản chính, chỉ từ 01/11; khoản quỹ tạm ứng và tháng 10 không lọt (chạy đúng hàm lịch 08:00)")
def _vao_that():
	import sys
	import types

	import frappe
	import vagabond
	from vagabond import kenh_zalo
	from vagabond import tin_ban_hang as tbh
	ban_hang = types.ModuleType("vagabond.ban_hang")
	ban_hang._gd_co_chu_toan_he = lambda *a, **k: {}
	doi_soat_ck = types.ModuleType("vagabond.doi_soat_ck")
	doi_soat_ck.bang_dau_he = lambda: []
	doi_soat_ck.thuoc_tk = lambda mo_ta, bang: ("", "Tài khoản chính")
	dong = [
		{"name": "BT-1", "bank_account": "MB-CTY", "deposit": 200000000, "date": "2026-11-10", "description": VAO[0]["mo_ta"], "reference_number": "", "unallocated_amount": 200000000},
		{"name": "BT-2", "bank_account": "MB-QUY-TAMUNG", "deposit": 19000000, "date": "2026-11-16", "description": "Qaardl4994 APPMB1 1 Nop tien mat", "reference_number": "", "unallocated_amount": 19000000},
		{"name": "BT-3", "bank_account": "MB-CTY", "deposit": 5000000, "date": "2026-10-20", "description": "KHOAN THANG 10", "reference_number": "", "unallocated_amount": 5000000},
	]
	db = _Db(dong)
	gui = []
	with um.patch.object(frappe, "db", db, create=True), \
			um.patch("vagabond.tin_tai_chinh._tk_cong_ty", lambda: {"MB-CTY"}), \
			um.patch.dict(sys.modules, {"vagabond.ban_hang": ban_hang, "vagabond.doi_soat_ck": doi_soat_ck}), \
			um.patch.object(vagabond, "ban_hang", ban_hang, create=True), \
			um.patch.object(vagabond, "doi_soat_ck", doi_soat_ck, create=True), \
			um.patch.object(tbh, "_url", lambda d: d), \
			um.patch.object(kenh_zalo, "bao", lambda *a, **k: gui.append((a, k))):
		tbh.nhac_tien_chua_gan()
	dung("có gửi tin", len(gui) == 1)
	if gui:
		(loai, nhom, td, dong_tin), k = gui[0][0][:4], gui[0][1]
		la("nhóm nhận giữ nguyên", (loai, nhom), ("viec", "cong_no"))
		la("tiêu đề tin", td, "Tiền vào tài khoản công ty chưa gắn chứng từ")
		dung("chỉ 1 khoản 200 tr của tài khoản chính: %s" % dong_tin[0], dong_tin[0].startswith("1 khoản, tổng 200.000.000 đ"))
		la("mã tin giữ nguyên", k.get("ma_tin"), "kt_tien_chua_gan")


@ca("v675: nối phiếu chi vào dòng sao kê: các lý do không nối (đã nối, chưa ghi sổ, khác tài khoản, thiếu tiền)")
def _ly_do_noi():
	pe = {"docstatus": 1, "paid_amount": 6850000, "paid_from": "11211 - MB"}
	g = {"docstatus": 1, "withdrawal": 6850000, "deposit": 0, "unallocated_amount": 6850000}
	la("nối được", DC.ly_do_khong_noi(pe, g, "11211 - MB", False), "")
	la("đã nối", DC.ly_do_khong_noi(pe, g, "11211 - MB", True), "da_noi")
	la("phiếu nháp", DC.ly_do_khong_noi(dict(pe, docstatus=0), g, "11211 - MB", False), "phiếu chi chưa ghi sổ")
	la("không có dòng", DC.ly_do_khong_noi(pe, None, None, False), "không xác định được một dòng sao kê")
	la("tiền vào", DC.ly_do_khong_noi(pe, dict(g, withdrawal=0, deposit=6850000), "11211 - MB", False), "dòng sao kê không phải tiền ra đã xác nhận")
	la("khác tài khoản", DC.ly_do_khong_noi(pe, g, "1121 - Shinhan", False), "dòng sao kê thuộc tài khoản khác tài khoản chi của phiếu")
	la("thiếu tiền", DC.ly_do_khong_noi(pe, dict(g, unallocated_amount=6000000), "11211 - MB", False),
		"dòng sao kê không còn đủ tiền chưa đối chiếu")
	la("lệch dưới 1 đ vẫn nối", DC.ly_do_khong_noi(pe, dict(g, unallocated_amount=6849999.5), "11211 - MB", False), "")
