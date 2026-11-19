"""v675 (anh Việt 19/11/2026): hai tin 08:00 tiền vào / tiền ra chưa có chứng từ
gom theo nhóm việc, chỉ khoản từ 01/11/2026, tiền vào chỉ tài khoản chính; phiếu
chi đã xác nhận được nối đối chiếu lõi để không hiện lại mỗi sáng.

Mô tả sao kê trong ca là dữ liệu GIẢ dựng đúng dạng dòng sao kê thật (Codex #592:
không đưa tên, số tài khoản, mã giao dịch thật vào repo công khai).
"""
import unittest.mock as um

from vagabond import duyet_chi as DC
from vagabond import tien_chua_chung_tu as T
from vagabond.khung.kiem_thu.nen import ca, dung, la

VAO = [
	{"tien": 150000000, "ngay": "2026-11-10", "mo_ta": "VAGABOND CHUYEN TIEN NOI BO TU SHINHAN QUA MB KT00001/00001"},
	{"tien": 120000000, "ngay": "2026-11-15", "mo_ta": "MBVCB.10000000001.100001.ck.CT tu 0000000001 NGUYEN VAN A toi 00000001"},
	{"tien": 20000000, "ngay": "2026-11-16", "mo_ta": "PVS0000001 OnePay tam ung VAGABOND VIETQR 0h 13 11 26 den 23"},
	{"tien": 9000000, "ngay": "2026-11-05", "mo_ta": "Grab TT 100000001 2000000000000001 The Vagabond Patisserie Cafe"},
	{"tien": 1000000, "ngay": "2026-11-05", "mo_ta": "SHOPEEPAY CHUYEN TIEN 1000000000000000001 ShopeeFood thanh toan tu don"},
	{"tien": 100000, "ngay": "2026-11-05", "mo_ta": "kt00000001+GSM TT tien rut vi MC 051126"},
	{"tien": 400000, "ngay": "2026-11-09", "mo_ta": "1000001 beFood thanh toan ky 05112026 06112026"},
	{"tien": 300000, "ngay": "2026-11-16", "mo_ta": "Payoo TT TD ngay 13 11 15 11 2026 VAGABOND TONG"},
	{"tien": 700000, "ngay": "2026-11-05", "mo_ta": "PANCAKE0001 4 S10001O10001T0000001 10001"},
	{"tien": 5000000, "ngay": "2026-11-10", "mo_ta": "HO KINH DOANH KIEM THU chuyen tien banh T10 cho Vagabond"},
]
RA = [
	{"tien": 9000000, "ngay": "2026-11-06", "mo_ta": "MBCT VAGABOND TT HD NCC CONG TY KIEM THU APP 26 11 181"},
	{"tien": 6000000, "ngay": "2026-11-16", "mo_ta": "RetailVISADN-800001-6000000-VND-600000000001-FACEBK KT0000001-The 000000001"},
	{"tien": 66000, "ngay": "2026-11-16", "mo_ta": "RetailVISADN-800001-6000000-VND-600000000001-FACEBK KT0000001-The 000000001"},
	{"tien": 8000000, "ngay": "2026-10-28", "mo_ta": "MTC:00000000000000000001 MST:0000000000 CQT:0000001-Phuong Kiem Thu - Thue co so"},
	{"tien": 3000000, "ngay": "2026-11-16", "mo_ta": "VGB TT QC SHOPEE"},
	{"tien": 2500000, "ngay": "2026-11-03", "mo_ta": "S0000001 - Ma giao dich/ Trace 000001"},
]


@ca("v675: nhận diện nhóm trên dòng sao kê thật (nội bộ, đối tác, Pancake, thẻ, thuế, NCC, chưa rõ)")
def _nhom():
	la("nhóm tiền vào", [T.nhom_cua(g["mo_ta"], T.NHOM_VAO) for g in VAO],
		["noi_bo", "khac", "doi_tac", "doi_tac", "doi_tac", "doi_tac", "doi_tac", "doi_tac", "pancake", "khac"])
	la("nhóm tiền ra", [T.nhom_cua(g["mo_ta"], T.NHOM_RA) for g in RA], ["ncc", "meta_the", "meta_the", "thue", "khac", "khac"])


@ca("v675: tin tiền vào gom theo nhóm, nhóm lớn trước, chưa rõ nguồn đứng cuối và liệt kê từng khoản")
def _soan_vao():
	td, dong = T.soan_vao(VAO)
	la("tiêu đề giữ nguyên", td, "Tiền vào tài khoản công ty chưa gắn chứng từ")
	dung("dòng tổng: 10 khoản, từ 01/11/2026: %s" % dong[0], dong[0].startswith("10 khoản, tổng 306.500.000 đ") and "01/11/2026" in dong[0])
	dung("nhóm nội bộ đứng đầu (150 tr): %s" % dong[1], dong[1].startswith("Chuyển nội bộ giữa tài khoản công ty: 1 khoản, 150.000.000 đ"))
	dung("nhóm đối tác một dòng 6 khoản: %s" % dong[2], dong[2].startswith("Tiền đối tác về") and ": 6 khoản, 30.800.000 đ" in dong[2])
	dung("nhóm chưa rõ nguồn cuối, kèm từng khoản lớn trước", dong[-3].startswith("Chưa rõ nguồn: 2 khoản, 125.000.000 đ")
		and "120.000.000 đ" in dong[-2] and "5.000.000 đ" in dong[-1])
	la("không khoản thì không tin", T.soan_vao([]), None)


@ca("v675: tin tiền ra gom theo nhóm; khoản chưa rõ nội dung liệt kê, cắt ở tối đa")
def _soan_ra():
	td, dong = T.soan_ra(RA)
	la("tiêu đề", td, "Tiền ra khỏi tài khoản công ty chưa có chứng từ")
	dung("trả NCC đứng trước thẻ (9 tr > 6,07 tr): %s" % dong[1], dong[1].startswith("Trả nhà cung cấp chưa nối phiếu chi: 1 khoản, 9.000.000 đ"))
	dung("Meta trừ thẻ MB gộp cả phí, ghi việc máy làm", any(d.startswith("Quảng cáo Meta trừ thẻ Visa MB: 2 khoản, 6.066.000 đ. Máy gom vào bút toán Meta") for d in dong))
	la("thẻ Visa khác (phần mềm) vẫn nhóm thẻ chung", T.nhom_cua("RetailVISADN-800003-1000000-VND-600000000003-OPENAI  KIEM THU SUB-The 000000001", T.NHOM_RA), "the")
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
		{"name": "BT-1", "bank_account": "MB-CTY", "deposit": 150000000, "date": "2026-11-10", "description": VAO[0]["mo_ta"], "reference_number": "", "unallocated_amount": 150000000},
		{"name": "BT-2", "bank_account": "MB-QUY-TAMUNG", "deposit": 19000000, "date": "2026-11-16", "description": "KT00001 APPMB1 1 Nop tien mat", "reference_number": "", "unallocated_amount": 19000000},
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
		dung("chỉ 1 khoản 150 tr của tài khoản chính: %s" % dong_tin[0], dong_tin[0].startswith("1 khoản, tổng 150.000.000 đ"))
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


# ------------------------------------------------ Meta trừ thẻ Visa MB (anh Việt chốt 19/11/2026)
from vagabond import chi_phi_meta as M  # noqa: E402

MB = [
	{"name": "BT-1", "ngay": "2026-11-16", "tien": 6000000, "mo_ta": "RetailVISADN-800001-6000000-VND-600000000001-FACEBK  KT0000001-The 000000001", "tk_gl": "11211", "da_doi_chieu": 0},
	{"name": "BT-2", "ngay": "2026-11-16", "tien": 66000, "mo_ta": "RetailVISADN-800001-6000000-VND-600000000001-FACEBK  KT0000001-The 000000001", "tk_gl": "11211", "da_doi_chieu": 0},
	{"name": "BT-3", "ngay": "2026-11-14", "tien": 22000, "mo_ta": "RetailVISADN-800002-2000000-VND-600000000002-FACEBK  KT0000002-The 000000001", "tk_gl": "11211", "da_doi_chieu": 0},
	{"name": "BT-4", "ngay": "2026-11-14", "tien": 2000000, "mo_ta": "RetailVISADN-800002-2000000-VND-600000000002-FACEBK  KT0000002-The 000000001", "tk_gl": "11211", "da_doi_chieu": 2000000},
	{"name": "BT-5", "ngay": "2026-11-08", "tien": 1000000, "mo_ta": "RetailVISADN-800003-1000000-VND-600000000003-OPENAI  KIEM THU SUB-The 000000001", "tk_gl": "11211", "da_doi_chieu": 0},
]


@ca("v675 Meta thẻ MB: đọc dòng sao kê thật, dòng lớn là tiền quảng cáo, dòng nhỏ cùng mã là phí; OpenAI không thuộc Meta; dòng đã ghi tay là chứng từ khác")
def _mb_doc():
	p = M.tach_mb(MB[0]["mo_ta"])
	la("tách", (p["tien_te"], p["ma"], p["the4"], p["dv"]), ("VND", "600000000001", "0001", "FACEBK KT0000001"))
	la("không phải thẻ", M.tach_mb("Grab TT 100000001"), None)
	g = {x["bank_transaction"]: x for x in M.giao_dich_mb(MB)}
	la("chỉ dòng FACEBK", sorted(g), ["BT-1", "BT-2", "BT-3", "BT-4"])
	la("phân loại theo số lớn trong cùng mã (kể cả dòng phí đứng trước)", [g[k]["phan_loai"] for k in ("BT-1", "BT-2", "BT-3", "BT-4")],
		["meta", "phi_meta", "phi_meta", "meta"])
	vao = M.chon_giao_dich(list(g.values()), {}, set())
	la("dòng đã đối chiếu tay không vào bút toán", sorted(x["bank_transaction"] for x in vao), ["BT-1", "BT-2", "BT-3"])
	la("trạng thái dòng ghi tay", g["BT-4"]["trang_thai"], M.GD_CT_KHAC)


@ca("v675 Meta thẻ MB: bút toán Nợ 6417, Nợ 6427 phí, Có đúng tài khoản ngân hàng bị trừ; phần thẻ Shinhan vẫn Có 3411")
def _mb_but_toan():
	vao = [x for x in M.giao_dich_mb(MB) if not x["da_co_ct"]]
	shin = {"khoa": "S", "phan_loai": "meta", "tien": 1000000, "bang_chung": ["pdf"]}
	dong, qc, phi = M.dong_but_toan(vao + [shin], "6417", "6427", "3411", "MKT", "2026-11")
	ban = {(d["account"], d["debit"], d["credit"]) for d in dong}
	la("số", (qc, phi), (6000000 + 1000000, 66000 + 22000))
	la("các dòng", ban, {("6417", 7000000, 0), ("6427", 88000, 0), ("3411", 0, 1000000), ("11211", 0, 6088000)})
	dong2, _q, _p = M.dong_but_toan(vao, "6417", "6427", "3411", "MKT", "2026-11")
	la("chỉ thẻ MB thì không có dòng 3411", sorted(d["account"] for d in dong2), ["11211", "6417", "6427"])


@ca("v675 Meta thẻ MB: thẻ MB không chờ sao kê thẻ Shinhan nhưng chờ hết tháng; thẻ Shinhan vẫn chờ đủ sao kê")
def _mb_chon_lap():
	mb = {"khoa": "mb:1", "nguon": "mb"}
	shin = {"khoa": "S"}
	la("đủ sao kê, hết tháng: cả hai", M.chon_lap([mb, shin], [], True), [shin, mb])
	la("thiếu sao kê thẻ, hết tháng: chỉ MB", M.chon_lap([mb, shin], [("a", "b")], True), [mb])
	la("chưa hết tháng: chỉ Shinhan nếu đủ", M.chon_lap([mb, shin], [], False), [shin])
	t = {"thieu": [], "het_thang": False, "vao": [mb], "vao_lap": [], "con_quyet": [], "ct_chua_xem": []}
	dung("chưa hết tháng có câu rõ", "chưa hết" in M.dieu_kien_lap(t, "2026-11"))
	t = dict(t, thieu=[("2026-11-01", "2026-12-10")])
	dung("chưa hết tháng nói chưa hết, không nói thiếu sao kê thẻ", "chưa hết" in M.dieu_kien_lap(t, "2026-11"))
	t = {"thieu": [("2026-11-01", "2026-12-10")], "het_thang": True, "vao": [mb], "vao_lap": [mb], "con_quyet": [], "ct_chua_xem": []}
	la("thiếu sao kê thẻ không chặn phần MB", M.dieu_kien_lap(t, "2026-11"), "")
