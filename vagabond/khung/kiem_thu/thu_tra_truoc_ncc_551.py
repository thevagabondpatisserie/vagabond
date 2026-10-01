"""v551: chi từ TK công ty cho khoản hoá đơn đến sau = phiếu chi trả trước NCC.

Chị Dung 01/10/2026: hồ sơ Adecco APP.26.09.009 ghi Nợ chi phí / Có 1121 lúc
chi rồi bút toán tay Nợ 331 / Có chi phí khi hoá đơn về. Đúng là Nợ 331 / Có
1121 lúc chi, hoá đơn tự ghi Nợ chi phí + 1331 / Có 331. Các ca dưới chốt
phần THUẦN: khoản nào thành trả trước, chia phiếu cho tờ, đối chiếu phiếu.
"""
from vagabond.khung.kiem_thu.nen import ca, la, dung
from vagabond import tra_truoc_ncc as t

NH = "1121 - MB"


def k(cho=1, tien=100, tk_co="", tra_truoc=0):
	return {"cho_hoa_don": cho, "so_tien": tien, "tk_co": tk_co, "tra_truoc": tra_truoc}


@ca("v551 khoản chờ hoá đơn của hồ sơ có NCC thành trả trước, khoản khác giữ bút toán")
def _tach():
	# Ca Adecco: ba khoản chờ hoá đơn, một nhà cung cấp.
	la("ba khoản Adecco", t.tach_dong([k(tien=290659834), k(tien=202911506), k(tien=193238819)], "NCC-ADECCO", NH),
		(686810159.0, [0, 1, 2], []))
	la("khoản không chờ hoá đơn giữ bút toán", t.tach_dong([k(), k(cho=0, tien=50)], "N", NH), (100.0, [0], [1]))
	la("không có NCC thì không trả trước", t.tach_dong([k()], "", NH), (0.0, [], [0]))
	la("Có tài khoản khác (quỹ, bù trừ) giữ bút toán", t.tach_dong([k(tk_co="1411")], "N", NH), (0.0, [], [0]))
	la("Có đúng tài khoản ngân hàng vẫn là trả trước", t.tach_dong([k(tk_co=NH)], "N", NH), (100.0, [0], []))
	la("khoản 0 đồng bỏ qua", t.tach_dong([k(tien=0), k()], "N", NH), (100.0, [1], []))


@ca("v551 đã chi thì chỉ dấu tra_truoc quyết, cờ chờ hoá đơn đổi sau không làm lệch bộ chứng từ")
def _da_chi():
	# Hồ sơ chi trước v551 (chi phí ngay): không có dấu, đã chi -> không có trả trước.
	la("hồ sơ cũ đã chi không bị đòi phiếu trả trước", t.tach_dong([k(), k()], "N", NH, da_chi=True), (0.0, [], [0, 1]))
	# Hồ sơ v551: khoản 0 đã chi trả trước; sau đó máy nối tờ bật cờ cho khoản 1.
	la("cờ bật sau khi chi không thêm phần trả trước",
		t.tach_dong([k(tra_truoc=1), k(cho=1)], "N", NH, da_chi=True), (100.0, [0], [1]))
	la("cờ tắt sau khi chi không bớt phần trả trước",
		t.tach_dong([k(cho=0, tra_truoc=1)], "N", NH, da_chi=True), (100.0, [0], []))
	la("mở lại về Đã duyệt sau khi huỷ phiếu: vẫn theo dấu",
		t.tach_dong([k(tra_truoc=1), k(cho=1)], "N", NH, da_chi=False), (100.0, [0], [1]))


@ca("v551 chia phiếu trả trước cho tờ: đúng NCC, cũ trước, không vượt")
def _chia():
	p = [{"name": "PE1", "party": "A", "con": 60}, {"name": "PE2", "party": "B", "con": 500},
		{"name": "PE3", "party": "A", "con": 100}]
	la("lấy PE1 hết rồi PE3, bỏ PE2 khác NCC", t.chia_phan_bo(p, 120, "A"), (120.0, [("PE1", 60.0), ("PE3", 60.0)]))
	la("không đủ thì lấy hết phần còn", t.chia_phan_bo(p, 1000, "A"), (160.0, [("PE1", 60.0), ("PE3", 100.0)]))
	la("NCC khác không lấy được gì", t.chia_phan_bo(p, 10, "C"), (0.0, []))
	la("phiếu đã hết tiền bỏ qua", t.chia_phan_bo([{"name": "PE1", "party": "A", "con": 0}], 10, "A"), (0.0, []))


def pe(**doi):
	x = {"name": "PE1", "payment_type": "Pay", "party_type": "Supplier", "party": "A", "paid_from": NH,
		"paid_amount": 686810159, "unallocated_amount": 686810159, "paid_from_account_currency": "VND",
		"paid_to_account_currency": "VND", "source_exchange_rate": 1, "target_exchange_rate": 1, "tham_chieu": []}
	x.update(doi)
	return x


KE = {"tien": 686810159, "supplier": "A", "nguon_chi": NH}


@ca("v551 đối chiếu phiếu trả trước: trước và sau khi phân bổ vào tờ đều khớp, sai thì báo")
def _doi_chieu():
	la("phiếu mới chưa phân bổ", t.loi_bo_tra_truoc(KE, pe()), [])
	la("đã phân bổ hết vào tờ Adecco vẫn khớp", t.loi_bo_tra_truoc(KE, pe(unallocated_amount=0,
		tham_chieu=[{"reference_doctype": "Purchase Invoice", "reference_name": "HDM-26-09-00135",
			"allocated_amount": 686810159}])), [])
	dung("sai NCC", t.loi_bo_tra_truoc(KE, pe(party="B")))
	dung("sai tài khoản chi", t.loi_bo_tra_truoc(KE, pe(paid_from="1111")))
	dung("sai số tiền", t.loi_bo_tra_truoc(KE, pe(paid_amount=1, unallocated_amount=1)))
	dung("phiếu thu không phải phiếu chi", t.loi_bo_tra_truoc(KE, pe(payment_type="Receive")))
	dung("phân bổ cộng chưa phân bổ không bằng số chi", t.loi_bo_tra_truoc(KE, pe(unallocated_amount=5)))
	dung("trỏ sang chứng từ không phải hoá đơn mua", t.loi_bo_tra_truoc(KE, pe(unallocated_amount=0,
		tham_chieu=[{"reference_doctype": "Purchase Order", "reference_name": "PO1", "allocated_amount": 686810159}])))
	dung("ngoại tệ", t.loi_bo_tra_truoc(KE, pe(paid_from_account_currency="USD")))


def _ke(tt=100, no=None, co=None):
	k = {"loai": "JE", "tong": tt + sum((no or {}).values()), "company": "CTY", "company_currency": "VND",
		"no": no or {}, "co": co or {}, "doi_tac": {}, "tien_te_tk": {tk: "VND" for tk in set(no or {}) | set(co or {})},
		"hoa_don": {}, "nha_cung_cap": "A"}
	if tt:
		k["tra_truoc"] = {"tien": tt, "supplier": "A", "nguon_chi": NH}
	return k


def _pe(tien=100, **doi):
	x = pe(paid_amount=tien, unallocated_amount=tien, **doi)
	x["doctype"] = "Payment Entry"
	return x


def _je(tk_no, tien):
	dong = [{"account": tk_no, "debit_in_account_currency": tien, "credit_in_account_currency": 0, "debit": tien,
		"credit": 0, "account_currency": "VND", "exchange_rate": 1, "party_type": None, "party": None},
		{"account": NH, "debit_in_account_currency": 0, "credit_in_account_currency": tien, "debit": 0,
		"credit": tien, "account_currency": "VND", "exchange_rate": 1, "party_type": None, "party": None}]
	return {"doctype": "Journal Entry", "name": "PKT-1", "company": "CTY", "tong_no": tien, "dong": dong}


@ca("v551 bộ chứng từ hồ sơ Chi từ TK công ty: phiếu trả trước đủ là đủ, thiếu hay thừa phiếu thì báo")
def _bo_chung_tu():
	from vagabond import ho_so_tt as hs
	la("chỉ phiếu trả trước", hs._kiem_bo_chung_tu(_ke(), [_pe()], 2)["du"], 1)
	kq = hs._kiem_bo_chung_tu(_ke(), [], 2)
	la("không có phiếu là thiếu", (kq["du"], bool(kq["thieu"])), (0, True))
	kq = hs._kiem_bo_chung_tu(_ke(), [_pe(), dict(_pe(), name="PE2")], 2)
	la("hai phiếu là thừa", (kq["du"], bool(kq["thua"])), (0, True))
	la("phiếu sai NCC là lệch", hs._kiem_bo_chung_tu(_ke(), [_pe(party="B")], 2)["du"], 0)
	la("lẫn: phiếu 70 và bút toán chi phí 30", hs._kiem_bo_chung_tu(
		_ke(70, {"6427": 30}, {NH: 30}), [_pe(70), _je("6427", 30)], 2)["du"], 1)
	kq = hs._kiem_bo_chung_tu(_ke(70, {"6427": 30}, {NH: 30}), [_pe(70)], 2)
	la("lẫn mà thiếu bút toán chi phí", (kq["du"], bool(kq["thieu"])), (0, True))
	kq = hs._kiem_bo_chung_tu(_ke(), [_pe(), _je("6427", 30)], 2)
	la("chỉ trả trước mà có thêm bút toán là thừa", (kq["du"], bool(kq["thua"])), (0, True))
	# Hồ sơ cũ (không trả trước): giữ luật cũ, phiếu chi là thừa.
	kq = hs._kiem_bo_chung_tu(_ke(0, {"6427": 30}, {NH: 30}), [_je("6427", 30), _pe(30)], 2)
	la("hồ sơ cũ không nhận phiếu chi", (kq["du"], bool(kq["thua"])), (0, True))


@ca("v551 kế hoạch đối chiếu hồ sơ lẫn khoản: phần chờ hoá đơn thành trả trước, chỉ phần còn lại vào Nợ/Có")
def _ke_hoach():
	from unittest.mock import patch
	from vagabond import ho_so_tt as hs
	from vagabond import tra_tien_app

	class D(dict):
		def get(self, k, md=None):
			return dict.get(self, k, md)
	doc = D(loai=hs.LOAI_TKCT, tong_tien=100, nha_cung_cap="A", tk_chi="BA-MB", trang_thai="Da duyet",
		dong=[D(cho_hoa_don=1, so_tien=70, tk_no="", tk_co=""), D(cho_hoa_don=0, so_tien=30, tk_no="6427", tk_co="")])

	def gv(dt, ten=None, truong=None, *a, **k):
		if dt == "Bank Account":
			return NH
		if dt == "Company":
			return "VND"
		if dt == "Account":
			return "VND" if truong == "account_currency" else ""
		return None
	with patch.object(hs, "_cong_ty_chung_tu", return_value="CTY"), \
			patch.object(tra_tien_app, "tk_tien_chi", return_value=(NH, "BA-MB")), \
			patch.object(hs.frappe.db, "get_value", side_effect=gv, create=True):
		ke = hs._dung_ke_hoach_chi(doc)
	la("phần trả trước 70 cho NCC A từ ngân hàng", ke.get("tra_truoc"), {"tien": 70.0, "supplier": "A", "nguon_chi": NH})
	la("Nợ chỉ còn khoản không hoá đơn", ke.get("no"), {"6427": 30.0})
	la("Có ngân hàng chỉ phần bút toán", ke.get("co"), {NH: 30.0})


@ca("v551 nguồn chi của hồ sơ có phần trả trước: một tài khoản ngân hàng, không báo nhiều nguồn (bench #405)")
def _nguon():
	from unittest.mock import patch
	from vagabond import ho_so_tt as hs
	from vagabond import doi_chieu_app as dc
	ke_chi_tt = _ke(100)
	ke_lan = _ke(70, {"6427": 30}, {NH: 30})
	for nhan, ke in (("chỉ phần trả trước", ke_chi_tt), ("lẫn trả trước và bút toán", ke_lan)):
		with patch.object(hs, "_dung_ke_hoach_chi", return_value=ke), \
				patch.object(hs, "_so_phai_chuyen", return_value={"con": 100}), \
				patch.object(hs, "_do_chinh_xac", return_value=2):
			la(nhan, dc._nguon({"name": "APP.1"}), ("CTY", NH, 100))


@ca("v551 tờ nối phân bổ phiếu chi ghi vào ô phieu_chi (Link Payment Entry), không vào but_toan (Link Journal Entry); vẫn giữ hồ sơ ở Đã thanh toán (bench #405 vòng 2)")
def _o_phieu_chi():
	import json
	from pathlib import Path
	from vagabond.hoa_don_sau import loi_bo_thanh_toan, TRUONG_HD_SAU
	goc = Path(__file__).resolve().parents[2]
	dt = json.loads((goc / "vagabond/doctype/vagabond_ho_so_tt_hd_sau/vagabond_ho_so_tt_hd_sau.json").read_text(encoding="utf-8"))
	o = {f["fieldname"]: f for f in dt["fields"]}
	la("but_toan chỉ nhận bút toán", (o["but_toan"]["fieldtype"], o["but_toan"]["options"]), ("Link", "Journal Entry"))
	la("phieu_chi nhận phiếu chi", (o["phieu_chi"]["fieldtype"], o["phieu_chi"]["options"]), ("Link", "Payment Entry"))
	dung("phieu_chi có trong field_order", "phieu_chi" in dt["field_order"])
	dung("phieu_chi khoá sửa tay", "phieu_chi" in TRUONG_HD_SAU)
	dung("tờ đã phân bổ phiếu chi chặn bỏ Đã thanh toán",
		"HDM-1" in loi_bo_thanh_toan("Da thanh toan", "Da duyet", [dict(hoa_don="HDM-1", but_toan="", phieu_chi="ACC-PAY-1")]))
	# Hai chỗ ghi dòng nối phải ghi phiếu chi vào phieu_chi. Dò chuỗi chỉ chốt
	# điều này; hành vi thật do ca bench _noi_va_go và _to_nhap kiểm.
	nguon = (goc / "ho_so_bo_sung.py").read_text(encoding="utf-8") + (goc / "tra_truoc_ncc.py").read_text(encoding="utf-8")
	dung("không còn chỗ ghi phiếu chi vào but_toan",
		'dong["but_toan"] = chia' not in nguon and '"but_toan": da[0][0]' not in nguon)
