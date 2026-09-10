# -*- coding: utf-8 -*-
"""#266 (09/09/2026): 59 đơn Sales và 116 tờ TCV không có hoá đơn điện tử.

Hai lỗi thật đọc từ Error Log của site:

1. "Payload không cùng số dòng SI." - kịch bản phát hành bỏ dòng thành tiền
   0 (đúng quy tắc của nó), bản v460 của chuan_tien lại đòi đủ số dòng SI.
   Đơn có món 0 đồng bị chặn NGAY LÚC GHI SỔ, cả 59 đơn Sales nằm nháp.
2. "Mã chưa rõ 9999 Mã thuế suất= [8.0] ... không hợp lệ" - chuan_tien ghi
   ma_thue là số thực 8.0, m-invoice chỉ nhận số nguyên. 116 tờ TCV bị từ
   chối rồi giữ cờ đối chiếu, nhịp nào sau cũng bỏ qua chúng.

Ca kiểm ở đây dựng lại đúng payload kịch bản gửi (đọc từ snapshot 07/09) và
đúng dữ liệu đơn HDB-26-09-01648 (3 dòng, dòng 2 là 0 đồng), rồi chốt phần
kéo ngày lập HĐĐT sang hôm nay: lọc tờ, ngày lập gửi đi, gỡ cờ chỉ khi
m-invoice không có dấu vết tờ, và chip cùng câu chữ với app.
"""

import datetime
import io
import unittest.mock
import json
import os

from vagabond import hddt_cho_xuat, minvoice_an_toan
from vagabond.thue_vnd import chuan_tien, tinh_dong
from vagabond.khung.kiem_thu.nen import ca, dung, la

D = datetime.date


def _goc():
	return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(*duong):
	return io.open(os.path.join(_goc(), *duong), encoding="utf-8").read()


def _phieu_01648():
	"""HDB-26-09-01648 ngày 09/09: 650.000 + 0 + 70.000 (phí dịch vụ, mã gộp)."""
	gia = [650000, 0, 70000]
	ds = tinh_dong(gia, [8, 8, 8], True)
	si = {"name": "HDB-26-09-01648", "posting_date": "2026-09-09", "vgb_thue_vnd": 1, "items": [],
		"taxes": [{"name": "T", "idx": 1, "tax_amount_after_discount_amount": sum(d["vat"] for d in ds)}],
		"net_total": sum(d["net"] for d in ds), "total_taxes_and_charges": sum(d["vat"] for d in ds),
		"grand_total": 720000, "item_wise_tax_details": []}
	for i, (d, ma) in enumerate(zip(ds, ["BAWC00139", "BATP00031", "DVBH00001"]), 1):
		si["items"].append({"idx": i, "name": str(i), "item_code": ma, "qty": 1, "net_amount": d["net"]})
		si["item_wise_tax_details"].append({"item_row": str(i), "tax_row": "T", "rate": d["rate"], "amount": d["vat"]})
	return si


def _goi_kich_ban(si):
	"""Payload y như kịch bản trên site: bỏ dòng thành tiền 0, ma_thue cint."""
	dong = []
	for it, x in zip(si["items"], tinh_dong([650000, 0, 70000], [8, 8, 8], True)):
		if x["gross"] > 0:
			dong.append({"tchat": 1, "inv_itemCode": it["item_code"], "inv_quantity": it["qty"], "ma_thue": 8,
				"inv_TotalAmountWithoutVat": 0, "inv_vatAmount": 0, "inv_TotalAmount": 0})
	return {"inv_invoiceIssuedDate": str(si["posting_date"]), "details": [{"data": dong}]}


# ------------------------------------------------------------ hai lỗi thật


@ca("#266: đơn có dòng 0 đồng đi qua được cửa kiểm payload (lỗi 1 đêm 09/09)")
def _dong_0():
	si = _phieu_01648()
	goi = _goi_kich_ban(si)
	chuan_tien(si, goi)
	d = goi["details"][0]["data"]
	la("hai dòng có tiền lên hoá đơn", [x["inv_itemCode"] for x in d], ["BAWC00139", "DVBH00001"])
	la("tổng tờ", (goi["inv_TotalAmountWithoutVat"], goi["inv_vatAmount"], goi["inv_TotalAmount"]),
		(sum(x["inv_TotalAmountWithoutVat"] for x in d), sum(x["inv_vatAmount"] for x in d), 720000))


@ca("#266: ma_thue gửi m-invoice là số nguyên, JSON không còn 8.0 (lỗi 2 đêm 09/09)")
def _ma_thue():
	si = _phieu_01648()
	goi = _goi_kich_ban(si)
	chuan_tien(si, goi)
	van_ban = json.dumps(goi)
	dung("không có 8.0 trong JSON", '"ma_thue": 8.0' not in van_ban and '"ma_thue": 8' in van_ban)
	dung("kiểu int", all(type(x["ma_thue"]) is int for x in goi["details"][0]["data"]))


@ca("#266: mã hàng gộp ĐÃ KHAI gửi số lượng 1 được nhận, số lượng khác thì dừng")
def _gop():
	si = _phieu_01648()
	si["items"][2]["qty"] = 3
	goi = _goi_kich_ban(si)
	goi["details"][0]["data"][1]["inv_quantity"] = 1
	chuan_tien(si, goi, ["DVBH00001"])
	la("đơn giá tính trên số lượng gửi", goi["details"][0]["data"][1]["inv_unitPrice"], float(goi["details"][0]["data"][1]["inv_TotalAmountWithoutVat"]))
	goi["details"][0]["data"][1]["inv_quantity"] = 2
	try:
		chuan_tien(si, goi, ["DVBH00001"])
	except ValueError:
		pass
	else:
		dung("số lượng 2 khác 3 phải từ chối", False)


@ca("#266 vòng 2 (F5): món KHÔNG khai gộp mà gửi số lượng 1 thì phải chặn")
def _gop_chua_khai():
	# Tái hiện đúng finding của Codex: trước sửa, payload hỏng của một món
	# thường ba cái vẫn qua cửa cuối và ra tờ ghi một cái, đơn giá 277.778
	# thay vì 92.593.
	ds = tinh_dong([300000], [8], True)
	si = {"name": "X", "posting_date": "2026-09-09", "vgb_thue_vnd": 1,
		"items": [{"idx": 1, "name": "1", "item_code": "BANH-THUONG", "qty": 3, "net_amount": ds[0]["net"]}],
		"taxes": [{"name": "T", "idx": 1, "tax_amount_after_discount_amount": ds[0]["vat"]}],
		"net_total": ds[0]["net"], "total_taxes_and_charges": ds[0]["vat"], "grand_total": 300000,
		"item_wise_tax_details": [{"item_row": "1", "tax_row": "T", "rate": 8, "amount": ds[0]["vat"]}]}
	for ma_gop in (None, [], ["DVBH00001"], [""]):
		goi = {"details": [{"data": [{"inv_itemCode": "BANH-THUONG", "inv_quantity": 1, "ma_thue": 8}]}]}
		try:
			chuan_tien(si, goi, ma_gop)
		except ValueError:
			pass
		else:
			dung("ma_gop=%r phải chặn" % (ma_gop,), False)
	# Khai đúng mã đó thì mới được, và khai chữ thường vẫn nhận.
	goi = {"details": [{"data": [{"inv_itemCode": "BANH-THUONG", "inv_quantity": 1, "ma_thue": 8}]}]}
	chuan_tien(si, goi, ["banh-thuong"])
	la("khai rồi thì qua", goi["details"][0]["data"][0]["inv_quantity"], 1)


@ca("#266: payload thiếu hay thừa dòng có tiền, hay sai mã, vẫn bị chặn")
def _van_chat():
	for loai in ("thieu", "thua", "ma"):
		si = _phieu_01648()
		goi = _goi_kich_ban(si)
		d = goi["details"][0]["data"]
		if loai == "thieu":
			d.pop()
		elif loai == "thua":
			d.append(dict(d[0]))
		else:
			d[0]["inv_itemCode"] = "KHAC"
		try:
			chuan_tien(si, goi)
		except ValueError:
			pass
		else:
			dung("phải từ chối " + loai, False)


# ------------------------------------------------------------ ngày lập


@ca("#266: ngày lập HĐĐT là ngày chờ xuất nếu có, không thì ngày sổ")
def _ngay_lap():
	la("chưa kéo", hddt_cho_xuat.ngay_lap({"posting_date": "2026-09-09"}), D(2026, 9, 9))
	la("đã kéo", hddt_cho_xuat.ngay_lap({"posting_date": "2026-09-09", "vgb_hddt_ngay_xuat": "2026-09-10"}), D(2026, 9, 10))
	try:
		hddt_cho_xuat.ngay_lap({"posting_date": "2026-09-09", "vgb_hddt_ngay_xuat": "2026-09-08", "name": "X"})
	except ValueError:
		pass
	else:
		dung("ngày chờ xuất nhỏ hơn ngày sổ phải dừng", False)


@ca("#266: cửa chung chuan_goi ghi inv_invoiceIssuedDate theo ngày chờ xuất")
def _cua_chung():
	si = _phieu_01648()
	si.update(vgb_hddt_ngay_xuat="2026-09-10")
	goi = {"data": [_goi_kich_ban(si)]}
	ra = minvoice_an_toan.chuan_goi(si, goi)["data"][0]
	la("ngày lập là ngày kéo", ra["inv_invoiceIssuedDate"], "2026-09-10")
	la("mã phiếu làm keyApi", ra["key_api"], "HDB-26-09-01648")
	si.pop("vgb_hddt_ngay_xuat")
	ra = minvoice_an_toan.chuan_goi(si, {"data": [_goi_kich_ban(si)]})["data"][0]
	la("chưa kéo thì giữ ngày sổ", ra["inv_invoiceIssuedDate"], "2026-09-09")


# ------------------------------------------------------------ lọc tờ kéo

NGUON = ["Pancake", "GrabFood", "Tại chỗ", "Mang về"]


def _to(**k):
	r = {"name": "HDB-1", "posting_date": "2026-09-09", "docstatus": 1, "grand_total": 100000, "vgb_huy": 0,
		"vgb_tam_tinh": 0, "custom_nguon": "Tại chỗ", "vgb_quay": "TCV", "custom_minvoice_id": None,
		"custom_hddt_id": None, "custom_hddt_so": None, "vgb_hddt_cho_doi_chieu": 0}
	r.update(k)
	return r


@ca("#266: chỉ kéo tờ đã ghi sổ, có tiền, đúng ngày, chưa có HĐĐT, thuộc điểm đang xuất")
def _loc():
	rows = [
		_to(name="A"),
		_to(name="B", vgb_hddt_cho_doi_chieu=1),
		_to(name="C", docstatus=0),
		_to(name="D", custom_hddt_so="12950"),
		_to(name="E", custom_minvoice_id="abc"),
		_to(name="F", grand_total=0),
		_to(name="G", vgb_huy=1),
		_to(name="H", posting_date="2026-09-08"),
		_to(name="I", custom_nguon="Khác"),
		_to(name="J", vgb_quay="NVHTN"),
		_to(name="K", vgb_quay="", custom_nguon="Pancake"),
	]
	ra = hddt_cho_xuat.loc_to_keo(rows, "2026-09-09", "2026-09-10", NGUON, ["@", "TCV"])
	la("đúng tập tờ", [r["name"] for r in ra], ["A", "B", "K"])
	ra = hddt_cho_xuat.loc_to_keo(rows, "2026-09-09", "2026-09-10", NGUON, [])
	la("chưa khai quầy thì không lọc quầy", [r["name"] for r in ra], ["A", "B", "J", "K"])
	try:
		hddt_cho_xuat.loc_to_keo(rows, "2026-09-11", "2026-09-10", NGUON, [])
	except ValueError:
		pass
	else:
		dung("không kéo ngày tương lai", False)


@ca("#266: hôm nay chỉ liệt kê tờ đang giữ cờ đối chiếu, không kéo ngày")
def _hom_nay():
	rows = [_to(name="A", posting_date="2026-09-10"), _to(name="B", posting_date="2026-09-10", vgb_hddt_cho_doi_chieu=1)]
	ra = hddt_cho_xuat.loc_to_keo(rows, "2026-09-10", "2026-09-10", NGUON, [])
	la("chỉ tờ giữ cờ", [r["name"] for r in ra], ["B"])
	s = _doc("vagabond", "hddt_cho_xuat.py")
	dung("ngày lập ghi theo chế độ, một nguồn", "ngay_dat = ngay_lap_theo_che_do(che_do, ngay_cu, hom_nay)" in s)


@ca("#266: gỡ cờ đối chiếu chỉ khi m-invoice trả lời không có dấu vết tờ")
def _go_co():
	# CHUNG là mẫu đối chứng lượt này dựng ra: mã "không có tờ" đo được là "01".
	kc = dict(chung={"ma": "01", "duong": "SI-X", "khoa_am": "VGB-KHONG-TON-TAI-AB12"})
	dung("không có tờ", hddt_cho_xuat.minvoice_khong_co_to({"code": "01", "message": "not found", "data": None}, **kc))
	dung("có số hoá đơn thì giữ", not hddt_cho_xuat.minvoice_khong_co_to({"code": "00", "data": {"inv_invoiceNumber": "12950"}}, **kc))
	dung("có ID thì giữ", not hddt_cho_xuat.minvoice_khong_co_to({"code": "00", "data": {"inv_invoiceAuth_id": "x"}}, **kc))
	dung("lỗi mạng thì giữ", not hddt_cho_xuat.minvoice_khong_co_to(None, **kc))
	dung("chuỗi lạ thì giữ", not hddt_cho_xuat.minvoice_khong_co_to("<html>", **kc))


@ca("#266 vòng 2 (F1): phản hồi LỖI dạng dict không được coi là không có tờ")
def _go_co_loi():
	# Tái hiện finding: trước sửa, cả bốn phản hồi dưới đây đều cho gỡ cờ,
	# nên tờ đã có hoá đơn bị gửi lại và sinh hoá đơn đúp.
	kc = dict(chung={"ma": "01", "duong": "SI-X", "khoa_am": "VGB-KHONG-TON-TAI-AB12"})
	for ph in ({"code": "500", "message": "internal error"},
			{"code": "401", "message": "Unauthorized"},
			{"code": "503", "message": ""},
			{"message": "System error, please try again"},
			{"code": "00", "message": "Token expired"}):
		dung("phải giữ cờ với %s" % ph, not hddt_cho_xuat.minvoice_khong_co_to(ph, **kc))
	# Phản hồi không có hình dạng của API cũng không kết luận được.
	for ph in ({}, {"linh": "tinh"}):
		dung("phản hồi lạ phải giữ cờ %s" % ph, not hddt_cho_xuat.minvoice_khong_co_to(ph, **kc))


@ca("#266 vòng 3 (F1): mã LẠ chưa từng thấy cũng phải giữ cờ")
def _go_co_ma_la():
	"""Vòng 2 lọc theo danh sách CẤM nên mã 9999 và 296 vẫn gỡ được cờ:
	9999 là đúng mã m-invoice đã từ chối 116 tờ TCV đêm 09/09, 296 là mã từ
	chối vì ngày lập đã lùi. Cả hai đều KHÔNG phải câu "không có tờ".
	Vòng 3 chỉ nhận đúng mã đo được từ mẫu âm tính."""
	kc = dict(chung={"ma": "01", "duong": "SI-X", "khoa_am": "VGB-KHONG-TON-TAI-AB12"})
	for ph in ({"code": "9999", "message": "Mã chưa rõ"},
			{"code": "296", "message": "date is not valid"},
			{"code": "", "message": ""},
			{"code": None, "data": None},
			{"message": "not found", "data": None},
			{"code": "02", "message": "not found", "data": None}):
		dung("mã lạ %s phải giữ cờ" % ph, not hddt_cho_xuat.minvoice_khong_co_to(ph, **kc))
	# Còn đúng mã của mẫu âm tính thì gỡ, dù mẫu ấy là mã nào đi nữa.
	for ma in ("01", "02", "", None):
		c = {"ma": hddt_cho_xuat._ma_phan_hoi({"code": ma}), "duong": "SI-X", "khoa_am": "K"}
		dung("trùng mẫu âm tính %r thì gỡ" % ma,
			hddt_cho_xuat.minvoice_khong_co_to({"code": ma, "data": None}, chung=c))


@ca("#266 vòng 3 (F1): mẫu đối chứng ÂM TÍNH phải tự dựng được và tự hỏng được")
def _mau_am_tinh():
	"""kiem_chung_api chạm Frappe nên bộ khung không với tới; ở đây giả lập
	hai lời gọi ra ngoài để chốt: hỏi đúng một mã phiếu bịa ra, và mọi cách
	hỏng của mẫu ấy đều làm cả lượt KHÔNG kết luận gì (trả None)."""
	db = unittest.mock.MagicMock()
	db.get_value.return_value = "SI-DA-CO-HDDT"

	def chay(dap):
		hoi = []

		def gia(base, hdr, khoa):
			hoi.append(khoa)
			ra = dap(khoa)
			if isinstance(ra, Exception):
				raise ra
			return ra

		with unittest.mock.patch.object(hddt_cho_xuat, "frappe", unittest.mock.MagicMock(db=db)), \
				unittest.mock.patch.object(hddt_cho_xuat, "_hoi_minvoice", gia):
			return hddt_cho_xuat.kiem_chung_api("http://x", {}), hoi

	co_dau = {"code": "00", "data": {"inv_invoiceNumber": "12943"}}
	sach = {"code": "01", "message": "not found", "data": None}

	# Đủ hai mẫu: dựng được, và mã "không có tờ" đúng bằng mã của mẫu âm tính.
	(chung, cau), hoi = chay(lambda k: co_dau if k == "SI-DA-CO-HDDT" else sach)
	dung("dựng được mẫu đối chứng", bool(chung))
	la("mã không có tờ đo được", chung.get("ma"), "01")
	dung("có hỏi một mã phiếu bịa ra", any(
		str(k).startswith(hddt_cho_xuat.KHOA_AM_TINH) for k in hoi))
	dung("mã bịa ra không trùng mã phiếu thật", "SI-DA-CO-HDDT" != chung.get("khoa_am"))
	dung("hai lần hỏi khác mã nhau", len(set(hoi)) == 2)

	# Mẫu âm tính LẠI có dấu vết: m-invoice nhận vơ cả mã không tồn tại.
	(chung, cau), _ = chay(lambda k: co_dau)
	dung("mẫu âm tính có dấu vết thì không kết luận", chung is None)
	dung("và nói rõ vì sao", "chưa từng tồn tại" in cau)

	# Mẫu âm tính là lỗi hệ thống, hay không ra hình dạng API, hay ném lỗi.
	for dap, mo_ta in (
			(lambda k: co_dau if k == "SI-DA-CO-HDDT" else {"code": "500", "message": "internal error"}, "lỗi hệ thống"),
			(lambda k: co_dau if k == "SI-DA-CO-HDDT" else "<html>", "không ra hình dạng API"),
			(lambda k: co_dau if k == "SI-DA-CO-HDDT" else RuntimeError("404"), "ném lỗi")):
		(chung, cau), _ = chay(dap)
		dung("mẫu âm tính %s thì không kết luận" % mo_ta, chung is None)

	# Mẫu DƯƠNG TÍNH hỏng thì dừng trước, không cần hỏi mẫu âm tính.
	(chung, cau), hoi = chay(lambda k: sach)
	dung("mẫu dương tính không có dấu vết thì dừng", chung is None)
	la("dừng ngay, chỉ hỏi một lần", len(hoi), 1)

	# Chưa có tờ nào đã xuất thì cũng không kết luận.
	db.get_value.return_value = None
	(chung, cau), hoi = chay(lambda k: sach)
	dung("không có tờ mẫu thì không kết luận", chung is None)
	la("và không hỏi m-invoice lần nào", len(hoi), 0)
	db.get_value.return_value = "SI-DA-CO-HDDT"


@ca("#266 vòng 3 (F1): mỗi lớp chặn đứng một mình cũng phải chặn được")
def _go_co_tung_lop():
	"""Đột biến vòng 3 cho thấy hai lớp cũ (chặn lỗi hệ thống, đòi hình dạng
	API) không làm đổ ca nào, vì lớp đối chiếu mã che mất chúng. Hai ca dưới
	đây dựng đúng tình huống lớp kia KHÔNG đỡ được, để mỗi lớp tự đứng.
	ĐỪNG sửa hai ca này thành mã khác mẫu âm tính, làm vậy là che lỗi lại."""
	# Cổng m-invoice trả code "00" cho cả "không có tờ" lẫn lỗi token hết hạn:
	# mã trùng mẫu âm tính, chỉ còn _la_loi_he_thong đỡ.
	c00 = {"ma": "00", "duong": "SI-X", "khoa_am": "K"}
	dung("mã trùng mẫu nhưng message báo lỗi thì vẫn giữ cờ",
		not hddt_cho_xuat.minvoice_khong_co_to({"code": "00", "message": "Token expired"}, chung=c00))
	dung("còn câu sạch cùng mã ấy thì gỡ",
		hddt_cho_xuat.minvoice_khong_co_to({"code": "00", "data": None}, chung=c00))
	# Cổng trả về không có khoá code: mẫu âm tính cũng None, chỉ còn lớp
	# "phải có hình dạng phản hồi của API" đỡ.
	cnone = {"ma": None, "duong": "SI-X", "khoa_am": "K"}
	for ph in ({}, {"linh": "tinh"}, {"1": 2}):
		dung("phản hồi không ra hình dạng API thì giữ cờ %s" % ph,
			not hddt_cho_xuat.minvoice_khong_co_to(ph, chung=cnone))
	dung("có khoá của API và cùng mẫu thì gỡ",
		hddt_cho_xuat.minvoice_khong_co_to({"data": None, "message": ""}, chung=cnone))


@ca("#266 vòng 2 (F1): chưa đối chứng được API thì không gỡ cờ tờ nào")
def _go_co_chua_kiem_chung():
	sach = {"code": "01", "message": "not found", "data": None}
	dung("chưa kiểm chứng thì giữ", not hddt_cho_xuat.minvoice_khong_co_to(sach))
	dung("chung rỗng cũng giữ", not hddt_cho_xuat.minvoice_khong_co_to(sach, chung={}))
	dung("kiểm chứng rồi mới gỡ", hddt_cho_xuat.minvoice_khong_co_to(
		sach, chung={"ma": "01", "duong": "SI-X", "khoa_am": "K"}))
	h = _doc("vagabond", "hddt_cho_xuat.py")
	i = h.find("def chay_nen(")
	than = h[i:h.find("\ndef ", i + 10)]
	dung("chay_nen đối chứng API trước khi hỏi từng tờ", "kiem_chung_api(base, hdr)" in than)
	dung("và truyền kết quả đối chứng vào từng lượt hỏi",
		"_tra_minvoice(base, hdr, r.name, chung)" in than)
	kc = h[h.find("def kiem_chung_api("):]
	dung("mẫu đối chứng là tờ CHẮC CHẮN đã có hoá đơn",
		'"custom_hddt_so": ["!=", ""]' in kc and '"custom_minvoice_id": ["!=", ""]' in kc)
	dung("và có mẫu ÂM TÍNH bằng mã phiếu bịa ra", "KHOA_AM_TINH" in kc and "uuid4()" in kc)


@ca("#266: chip cùng câu chữ giữa máy chủ và app")
def _chip():
	cau = hddt_cho_xuat.nhan_chip("2026-09-10")
	la("câu máy chủ", cau, "Hoá đơn chờ xuất cho ngày 10/09/2026")
	js = _doc("vagabond", "public", "js", "bep", "09-tinh-tien-quay.js")
	dung("app dùng cùng câu", "'Hoá đơn chờ xuất cho ngày ' +" in js)
	for tep in ("08-doanh-so-sales.js", "10-bill-quay.js"):
		dung("chip trên " + tep, "hddtChoXuatChu(r.vgb_hddt_ngay_xuat)" in _doc("vagabond", "public", "js", "bep", tep))
	cd = _doc("vagabond", "public", "js", "bep", "17-cai-dat.js")
	dung("nút xử ngày cũ trong Cài đặt", "vagabond.hddt_cho_xuat.xu_ly_ngay_cu" in cd and "chay_thu: 1" in cd and "chay_thu: 0" in cd)
	dung("app nói rõ cửa m-invoice còn mở hay đã đóng", "che_do_de_xuat === 'giu_ngay'" in cd and "ngay_so_moi_nhat" in cd)


@ca("#266: gộp kết quả phát hành từng tờ")
def _gom():
	ra = hddt_cho_xuat.gom_ket_qua([{"tim_thay": 1, "tao_ok": 1, "loi": []}, {"tim_thay": 1, "tao_ok": 0, "loi": ["x"]}, None])
	la("gộp", ra, {"tim_thay": 2, "tao_ok": 1, "loi": ["x"]})


@ca("#266: chuỗi cuối ngày và nhịp bù đều gọi phát hành và ký tờ chờ xuất")
def _noi_vao_chuoi():
	s = _doc("vagabond", "ban_hang.py")
	i = s.find("def phat_hanh_cuoi_ngay(")
	than = s[i:s.find("\ndef ", i + 10)]
	dung("chuỗi cuối ngày phát hành tờ chờ xuất", "hddt_cho_xuat.phat_hanh(ngay, _goi_server_script)" in than)
	dung("chuỗi cuối ngày ký tờ chờ xuất", "hddt_cho_xuat.ky(ngay, _goi_server_script)" in than)
	i = s.find("def xuat_hddt_con_thieu_tu_dong(")
	than = s[i:s.find("\ndef ", i + 10)]
	dung("nhịp bù phát hành tờ chờ xuất hôm nay", "hddt_cho_xuat.phat_hanh(str(d), _goi_server_script)" in than and "if d == hom_nay" in than)
	for ham in ("bang_doanh_so", "pos_ds_bill"):
		i = s.find("def %s(" % ham)
		than = s[i:s.find("\ndef ", i + 10)]
		dung(ham + " trả ô ngày chờ xuất và cờ đối chiếu", "vgb_hddt_ngay_xuat" in than and "vgb_hddt_cho_doi_chieu" in than)
	tt = _doc("vagabond", "truong_tu_them.py")
	dung("trường được dựng khi migrate", "hddt_cho_xuat.TRUONG_MOI" in tt)


# ------------------------------------------- cửa m-invoice và thứ tự xuất


@ca("#266: cửa m-invoice của một ngày còn mở khi ngày đó không nhỏ hơn ngày tờ số lớn nhất")
def _cua():
	dung("chưa có tờ nào thì mở", hddt_cho_xuat.cua_con_mo("2026-09-09", None))
	dung("tờ mới nhất 08/09 thì 09/09 còn mở", hddt_cho_xuat.cua_con_mo("2026-09-09", "2026-09-08"))
	dung("cùng ngày vẫn mở", hddt_cho_xuat.cua_con_mo("2026-09-09", "2026-09-09"))
	dung("tờ mới nhất 10/09 thì 09/09 đã đóng", not hddt_cho_xuat.cua_con_mo("2026-09-09", "2026-09-10"))


@ca("#266: cửa còn mở thì giữ đúng ngày bán, đóng rồi mới kéo (anh Việt chốt 10/09)")
def _che_do():
	la("đêm 09/09, tờ mới nhất 08/09", hddt_cho_xuat.che_do_de_xuat(D(2026, 9, 9), D(2026, 9, 10), D(2026, 9, 8)), "giu_ngay")
	la("cửa đã đóng", hddt_cho_xuat.che_do_de_xuat(D(2026, 9, 9), D(2026, 9, 10), D(2026, 9, 10)), "keo")
	la("giữ ngày thì ngày lập là ngày bán",
		hddt_cho_xuat.ngay_lap_theo_che_do("giu_ngay", D(2026, 9, 9), D(2026, 9, 10)), D(2026, 9, 9))
	la("kéo thì ngày lập là hôm nay",
		hddt_cho_xuat.ngay_lap_theo_che_do("keo", D(2026, 9, 9), D(2026, 9, 10)), D(2026, 9, 10))
	try:
		hddt_cho_xuat.ngay_lap_theo_che_do("", D(2026, 9, 9), D(2026, 9, 10))
	except ValueError:
		pass
	else:
		dung("chưa chọn chế độ phải dừng", False)
	# Tờ giữ đúng ngày bán vẫn qua được cửa ngày lập, không bị coi là lùi ngày.
	la("ngày lập của tờ giữ ngày",
		hddt_cho_xuat.ngay_lap({"posting_date": "2026-09-09", "vgb_hddt_ngay_xuat": "2026-09-09"}), D(2026, 9, 9))


@ca("#266: ngày cũ còn mở được xếp cũ trước mới sau, ngày đã đóng bị loại")
def _ngay_cu_con_mo():
	ds = ["2026-09-09", "2026-09-08", "2026-09-10", "2026-09-09"]
	la("chỉ ngày cũ còn mở, không trùng",
		hddt_cho_xuat.ngay_cu_con_mo(ds, D(2026, 9, 10), D(2026, 9, 9)), [D(2026, 9, 9)])
	la("chưa có tờ nào thì cả hai ngày cũ",
		hddt_cho_xuat.ngay_cu_con_mo(ds, D(2026, 9, 10), None), [D(2026, 9, 8), D(2026, 9, 9)])
	la("hôm nay không nằm trong danh sách ngày cũ",
		hddt_cho_xuat.ngay_cu_con_mo(["2026-09-10"], D(2026, 9, 10), None), [])


@ca("#266: hàng rào thứ tự chạy TRƯỚC mọi lượt ghi sổ của hôm nay")
def _hang_rao():
	s = _doc("vagabond", "ban_hang.py")
	for ham, sau_do in (("tu_ghi_so_cuoi_ngay", "_dong_bo_doanh_so(ngay)"),
			("xuat_rai_trong_ngay", "hddt_bu.duoc_rai(")):
		i = s.find("def %s(" % ham)
		than = s[i:s.find("\ndef ", i + 10)]
		vi_tri_rao = than.find("hddt_cho_xuat.xuat_ngay_cu_truoc()")
		dung(ham + " có gọi hàng rào", vi_tri_rao >= 0)
		# Gọi sau khi đã chạm vào tờ của hôm nay là vô nghĩa: tờ đầu tiên của
		# hôm nay đã đóng cửa rồi. Phải đứng trước.
		dung(ham + " gọi hàng rào trước khi chạm tờ hôm nay",
			vi_tri_rao >= 0 and vi_tri_rao < than.find(sau_do))
	h = _doc("vagabond", "hddt_cho_xuat.py")
	i = h.find("def xuat_ngay_cu_truoc(")
	than = h[i:]
	dung("hàng rào chỉ làm ngày còn mở", "ngay_cu_con_mo(ds, getdate(nowdate()), _ngay_so_hddt_moi_nhat())" in than)
	dung("hàng rào tôn trọng công tắc m-invoice", "_cong_tac_minvoice()" in than)
	dung("hàng rào lấy khoá phát hành", "_khoa_hddt(" in than)
	# Lượt xử của chính HÔM NAY cũng phải nhường ngày cũ đi trước, không thì
	# chính nó là tờ đóng sập cửa của ngày cũ đang chờ.
	i = h.find("def chay_nen(")
	than_nen = h[i:h.find("\ndef ", i + 10)]
	vi_rao = than_nen.find("xuat_ngay_cu_truoc()")
	dung("lượt hôm nay nhường ngày cũ trước",
		vi_rao >= 0 and "if ngay_cu >= hom_nay and not xuat_ngay_cu_truoc():" in than_nen)
	dung("nhường trước khi phát hành", vi_rao < than_nen.find("_phat_hanh_theo_lo("))


@ca("#266 vòng 2 (F2): hàng rào nằm ở CỬA CHUNG, mọi đường phát hành đều qua")
def _cua_chung_hang_rao():
	# Codex bắt đúng: chốt đơn tay và chốt cả loạt cũng phát hành ngay sau
	# khi ghi sổ, không đi qua hai nhịp lịch. Cửa chung là kiem_goi.
	m = _doc("vagabond", "minvoice_an_toan.py")
	i = m.find("def kiem_goi(")
	than = m[i:]
	vi_rao = than.find("hddt_cho_xuat.chan_neu_con_ngay_cu(si)")
	dung("kiem_goi gọi hàng rào", vi_rao >= 0)
	dung("gọi TRƯỚC khi dựng payload", vi_rao < than.find("chuan_goi(si,"))
	# Hai cửa tay đi tới kiem_goi qua _tu_xuat_hddt -> xuat_hoa_don_dien_tu.
	b = _doc("vagabond", "ban_hang.py")
	for ham in ("chot_mot_don", "chot_doanh_so"):
		i = b.find("def %s(" % ham)
		dung(ham + " phát hành qua _tu_xuat_hddt", "_tu_xuat_hddt(" in b[i:b.find("\ndef ", i + 10)])
	i = b.find("def _tu_xuat_hddt(")
	dung("_tu_xuat_hddt đi qua xuat_hoa_don_dien_tu",
		"xuat_hoa_don_dien_tu(" in b[i:b.find("\ndef ", i + 10)])
	i = b.find("def xuat_hoa_don_dien_tu(")
	dung("xuat_hoa_don_dien_tu đi qua kiem_goi",
		"minvoice_an_toan.kiem_goi(" in b[i:b.find("\ndef ", i + 10)])
	# Server Script phát hành cũng gọi đúng cửa đó.
	k = _doc("vagabond", "minvoice_kich_ban.py")
	dung("Server Script gọi kiem_goi", "vagabond.minvoice_an_toan.kiem_goi" in k)


@ca("#266 vòng 2 (F2): phép nhường, kèm van an toàn khi ngày cũ không xuất được")
def _phep_nhuong():
	ds = ["2026-09-09"]
	hn = D(2026, 9, 10)
	# Tờ của hôm nay: phải nhường.
	phai, ngay, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(hn, hn, ds, D(2026, 9, 8))
	dung("tờ hôm nay phải nhường", phai and ngay == [D(2026, 9, 9)])
	# Chính tờ ngày cũ thì được đi, không thì bế tắc.
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(D(2026, 9, 9), hn, ds, D(2026, 9, 8))
	dung("tờ ngày cũ được đi", not phai)
	# Cửa ngày cũ đã đóng thì không nhường nữa, nhường cũng vô ích.
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(hn, hn, ds, D(2026, 9, 10))
	dung("cửa đã đóng thì thôi", not phai)
	# Không còn ngày cũ nào chờ.
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(hn, hn, [], None)
	dung("không nợ thì đi", not phai)
	# Van an toàn: vừa thử mà không xuất được tờ nào thì tạm mở.
	bay_gio = datetime.datetime(2026, 9, 10, 23, 10)
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(hn, hn, ds, D(2026, 9, 8),
		moc_loi=datetime.datetime(2026, 9, 10, 23, 5), bay_gio=bay_gio)
	dung("van mở trong 15 phút sau lần thử hỏng", not phai)
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(hn, hn, ds, D(2026, 9, 8),
		moc_loi=datetime.datetime(2026, 9, 10, 22, 50), bay_gio=bay_gio)
	dung("quá 15 phút thì chặn lại", phai)


@ca("#266 vòng 2 (F3): không lấy được khoá là CÒN NỢ, không cho tờ hôm nay đi")
def _fail_closed():
	h = _doc("vagabond", "hddt_cho_xuat.py")
	i = h.find("def xuat_ngay_cu_truoc(")
	than = h[i:h.find("\ndef ", i + 10)]
	j = than.find("khoa = _khoa_hddt(")
	dung("có lấy khoá", j >= 0)
	sau = than[j:j + 400]
	dung("không lấy được khoá thì trả False", "if khoa is None:" in sau and "return False" in sau)
	dung("hỏng giữa chừng cũng trả False", than.rstrip().endswith("return False"))
	dung("đọc lại danh sách sau khi chạy, không tin con số vừa gộp",
		"return not ngay_cu_con_mo(ngay_cu_dang_cho()" in than)
	b = _doc("vagabond", "ban_hang.py")
	for ham in ("tu_ghi_so_cuoi_ngay", "xuat_rai_trong_ngay"):
		i = b.find("def %s(" % ham)
		than_b = b[i:b.find("\ndef ", i + 10)]
		dung(ham + " đọc trạng thái hàng rào chứ không gọi rồi đi tiếp",
			"if not hddt_cho_xuat.xuat_ngay_cu_truoc():" in than_b)


@ca("#266 vòng 2 (F4): cửa mở hay đóng đọc theo NGÀY LẬP, không phải ngày sổ")
def _ngay_lap_hieu_luc():
	b = _doc("vagabond", "ban_hang.py")
	i = b.find("def _ngay_so_hddt_moi_nhat(")
	than = b[i:b.find("\ndef ", i + 10)]
	dung("SQL lấy ngày lập hiệu lực",
		"coalesce(vgb_hddt_ngay_xuat, posting_date)" in than)
	dung("vẫn có đường lui khi cột chưa dựng", than.count("select posting_date from") == 1)
	# Ca thật của Codex: tờ mang số lớn nhất có ngày sổ 09/09 nhưng ngày lập
	# 10/09. Đọc đúng ngày lập thì cửa 09/09 phải là ĐÃ ĐÓNG.
	dung("đọc ngày lập 10/09 thì cửa 09/09 đóng",
		not hddt_cho_xuat.cua_con_mo(D(2026, 9, 9), D(2026, 9, 10)))
	la("và chế độ đề xuất chuyển sang kéo",
		hddt_cho_xuat.che_do_de_xuat(D(2026, 9, 9), D(2026, 9, 10), D(2026, 9, 10)), "keo")


@ca("#266 vòng 2: bench qua Server Script với HTTP giả đã đăng ký vào runner CI")
def _bench_dang_ky():
	b = _doc("vagabond", "khung", "bench_thu", "kiem_hddt_266.py")
	for moc in ("execute_method", "make_get_request", "make_post_request",
			"_khoa_hddt", "ngay_cu_dang_cho", "vagabond_bench_thu"):
		dung("bench có " + moc, moc in b)
	ci = _doc("vagabond", "khung", "bench_thu", "chay_ci.py")
	dung("runner gọi bench #266", "kiem_hddt_266 import chay as chay_hddt266" in ci)
	dung("và kết quả bench #266 quyết định job", 'bool(kq266.get("dat"))' in ci)


@ca("#266: cửa chỉ mở ra ngoài đúng một hàm, phần chạy nền là nội bộ")
def _cua_ngo():
	from vagabond.khung.kiem_thu.thu_cua_ngo import CUA_NGO
	la("đúng danh sách", CUA_NGO["hddt_cho_xuat.py"], ["xu_ly_ngay_cu"])
