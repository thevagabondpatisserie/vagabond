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
from vagabond.thue_vnd import chuan_tien, dong_duoc_gui, dong_len_hoa_don, tinh_dong
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
		# amount la THANH TIEN DONG (rate x qty), la phep loc that cua kich ban.
		si["items"].append({"idx": i, "name": str(i), "item_code": ma, "qty": 1,
			"amount": gia[i - 1], "net_amount": d["net"]})
		si["item_wise_tax_details"].append({"item_row": str(i), "tax_row": "T", "rate": d["rate"], "amount": d["vat"]})
	return si


def _goi_kich_ban(si):
	"""Payload y như kịch bản trên site: bỏ dòng thành tiền 0, ma_thue cint."""
	dong = []
	for it, x in zip(si["items"], tinh_dong([650000, 0, 70000], [8, 8, 8], True)):
		# Loc theo it.amount, y het kich ban (minvoice_phat_hanh_20260907.txt
		# dong 101-104). Doi phep loc nay la ca kiem het mo phong ban that.
		if float(it["amount"]) > 0:
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
		"items": [{"idx": 1, "name": "1", "item_code": "BANH-THUONG", "qty": 3,
			"amount": 300000, "net_amount": ds[0]["net"]}],
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


@ca("#266 vòng 5: phép lọc của kịch bản trên site và của thue_vnd phải cùng một trường")
def _contract_loc_dong():
	"""Codex vòng 5 đòi chốt contract amount > 0 giữa HAI BÊN, không chỉ một
	bên. Kịch bản phát hành nằm trong cơ sở dữ liệu site, git không quản; bản
	ảnh chụp trong du_lieu/ là nguồn đối chiếu duy nhất có trong repo.

	Đây là phép DÒ CHUỖI, và theo điều 16 nó KHÔNG phải kiểm thử: nó chỉ chốt
	hai bên còn nêu cùng một trường. Phần chứng minh hai bên cùng chọn đúng
	một tập dòng nằm ở bench kiem_hddt_266 (mục contract), chạy qua kịch bản
	thật trên site."""
	import re
	kb = _doc("vagabond", "khung", "kiem_thu", "du_lieu", "minvoice_phat_hanh_20260907.txt")
	dieu_kien = re.findall(r"if frappe\.utils\.flt\(it\.(\w+)\) > 0:", kb)
	la("kịch bản lọc theo đúng một trường", sorted(set(dieu_kien)), ["amount"])
	tv = _doc("vagabond", "thue_vnd.py")
	than = tv[tv.find("def dong_len_hoa_don("):]
	than = than[:than.find("\ndef ", 10)]
	dong_loc = [d for d in than.splitlines() if d.strip().startswith("return [")]
	la("thue_vnd lọc trong đúng một dòng", len(dong_loc), 1)
	dung("và gọi đúng một nguồn phép lọc", "dong_duoc_gui(it)" in dong_loc[0])
	dung("không lọc theo gross", "gross" not in dong_loc[0])
	# Nguon duy nhat ay phai la phep lọc theo amount, y het kich ban.
	nguon = tv[tv.find("def dong_duoc_gui("):]
	nguon = nguon[:nguon.find("\ndef ", 10)]
	dung("nguồn duy nhất lọc theo amount", "'amount'" in nguon and "> 0" in nguon)
	dung("và không lọc theo gross", "gross" not in nguon.split('"""')[-1])
	dung("chú thích cảnh báo đổi một bên phải đổi cả hai",
		"đừng đổi một bên" in than)


@ca("#266 vòng 5b (Codex): nợ chỉ tính tờ thuộc điểm ĐANG BẬT xuất hoá đơn")
def _no_theo_diem_dang_bat():
	"""Codex bắt đúng, và đây là lỗi CHẾT MÁY: hai tập nợ đếm cả tờ của
	nguồn/quầy KHÔNG bật xuất, kể cả phiếu Desk có custom_nguon rỗng. Kịch
	bản phát hành không bao giờ xuất được những tờ ấy, nên xuat_ngay_cu_truoc
	không rút cạn nổi, còn chan_neu_con_ngay_cu chặn MỌI tờ mới vĩnh viễn.
	Một phiếu Desk cũ không liên quan là cả tiệm ngừng xuất hoá đơn."""
	rows = [
		{"posting_date": D(2026, 9, 9), "custom_nguon": "Pancake", "vgb_quay": ""},
		{"posting_date": D(2026, 9, 8), "custom_nguon": "", "vgb_quay": ""},
		{"posting_date": D(2026, 9, 7), "custom_nguon": "Khac", "vgb_quay": ""},
		{"posting_date": D(2026, 9, 6), "custom_nguon": "Pancake", "vgb_quay": "TCV"},
		{"posting_date": D(2026, 9, 5), "custom_nguon": "Pancake", "vgb_quay": "KHONG-BAT"},
	]
	with unittest.mock.patch.object(hddt_cho_xuat, "_cai_dat_minvoice",
			lambda: ({}, ["Pancake"], ["@", "TCV"])):
		ra = hddt_cho_xuat._loc_diem_dang_xuat(rows)
	la("chỉ giữ ngày của điểm đang bật", sorted(str(d) for d in ra),
		["2026-09-06", "2026-09-09"])
	# Phiếu Desk nguồn rỗng là ca Codex nêu đích danh: KHÔNG được tính là nợ.
	with unittest.mock.patch.object(hddt_cho_xuat, "_cai_dat_minvoice",
			lambda: ({}, ["Pancake"], [])):
		ra = hddt_cho_xuat._loc_diem_dang_xuat(
			[{"posting_date": D(2026, 9, 8), "custom_nguon": "", "vgb_quay": ""}])
	la("phiếu Desk nguồn rỗng không phải nợ", ra, [])
	# Đọc cài đặt hỏng thì NÉM, tuyệt đối không âm thầm bỏ phép lọc.
	def no_ra():
		raise RuntimeError("mất kết nối")
	with unittest.mock.patch.object(hddt_cho_xuat, "_cai_dat_minvoice", no_ra), \
			unittest.mock.patch.object(hddt_cho_xuat, "frappe", unittest.mock.MagicMock()):
		try:
			hddt_cho_xuat._loc_diem_dang_xuat(rows)
			dung("đọc cài đặt hỏng phải ném", False)
		except hddt_cho_xuat.KhongDocDuocNo:
			dung("ném đúng loại", True)
	# Và cả hai tập nợ đều đi qua phép lọc này, không tập nào bỏ sót.
	h = _doc("vagabond", "hddt_cho_xuat.py")
	for ham in ("ngay_cu_dang_cho", "ngay_cu_can_bao_ve"):
		t = h[h.find("def %s(" % ham):]
		t = t[:t.find("\ndef ", 10)]
		dung(ham + " lọc theo điểm đang bật", "_loc_diem_dang_xuat(rows)" in t)
	dung("phép lọc dùng lại thuoc_diem_dang_xuat, không viết bản thứ hai",
		h.count("def thuoc_diem_dang_xuat(") == 1
		and "thuoc_diem_dang_xuat(r, ds_nguon, ds_quay)" in h[h.find("def _loc_diem_dang_xuat("):])


@ca("#266 vòng 5b (claude): đọc ngày số mới nhất KHÔNG được rollback")
def _khong_rollback_trong_khoa():
	"""claude bắt đúng: _ngay_so_hddt_moi_nhat được gọi từ kiem_goi, mà
	kiem_goi đang GIỮ khoá dòng (for_update=True) tới khi lưu xong dấu chờ.
	Gọi frappe.db.rollback() ở đó là nhả mất khoá ấy VÀ vứt phần việc chưa
	commit của chính lần ghi sổ. Nặng hơn: từ lúc deploy tới lúc migrate
	xong, cột vgb_hddt_ngay_xuat chưa có nên câu đầu HỎNG MỖI LẦN GỌI."""
	b = _doc("vagabond", "ban_hang.py")
	i = b.find("def _ngay_so_hddt_moi_nhat(")
	than = b[i:b.find("\ndef ", i + 10)]
	# Kiem THAN MA, bo docstring va chu thich: ca hai deu co nhac ten rollback
	# de giai thich vi sao khong duoc dung no.
	ma = than.split('"""')[-1]
	ma = "\n".join(d for d in ma.splitlines() if not d.strip().startswith("#"))
	dung("không còn lời gọi rollback trong thân hàm", "rollback(" not in ma)
	dung("hỏi cột bằng has_column thay vì bắt lỗi",
		"has_column(\"Sales Invoice\", \"vgb_hddt_ngay_xuat\")" in than)
	# Và cửa chung đúng là có gọi hàm này trong lúc giữ khoá.
	m = _doc("vagabond", "minvoice_an_toan.py")
	j = m.find("def kiem_goi(")
	than_m = m[j:m.find("\ndef ", j + 10)]
	dung("kiem_goi giữ khoá dòng", "for_update=True" in than_m)
	dung("và gọi hàng rào trong lúc giữ khoá", "chan_neu_con_ngay_cu(si)" in than_m)
	h = _doc("vagabond", "hddt_cho_xuat.py")
	k = h.find("def chan_neu_con_ngay_cu(")
	dung("hàng rào có đọc ngày số mới nhất",
		"_ngay_so_hddt_moi_nhat()" in h[k:h.find("\ndef ", k + 10)])


@ca("#266 vòng 5b (claude): chay_nen nâng quyền thì phải TRẢ LẠI người gọi")
def _tra_lai_quyen():
	"""xu_ly_ngay_cu mở cho cả kế toán, và khi đẩy hàng đợi hỏng thì nó gọi
	THẲNG chay_nen trong request của người dùng. chay_nen set_user
	Administrator, bản trước không trả lại, nên một lần Redis trục trặc là
	kế toán chạy nốt request với quyền Administrator."""
	ai = {"user": "ketoan@vagabond.vn"}
	gia = unittest.mock.MagicMock()
	gia.session.user = ai["user"]

	def dat(u):
		ai["user"] = u
		gia.session.user = u

	gia.set_user = dat

	def no_ra(*a, **k):
		raise RuntimeError("hỏng giữa chừng")

	with unittest.mock.patch.object(hddt_cho_xuat, "frappe", gia), \
			unittest.mock.patch.object(hddt_cho_xuat, "_chay_nen_da_nang_quyen", no_ra):
		try:
			hddt_cho_xuat.chay_nen("2026-09-09", "giu_ngay", "x")
		except RuntimeError:
			pass
	la("hỏng giữa chừng vẫn trả lại đúng người gọi", ai["user"], "ketoan@vagabond.vn")

	ghi = []
	with unittest.mock.patch.object(hddt_cho_xuat, "frappe", gia), \
			unittest.mock.patch.object(hddt_cho_xuat, "_chay_nen_da_nang_quyen",
				lambda *a, **k: ghi.append(ai["user"]) or {"ok": 1}):
		hddt_cho_xuat.chay_nen("2026-09-09", "giu_ngay", "x")
	la("thân hàm vẫn chạy với quyền Administrator", ghi, ["Administrator"])
	la("xong thì trả lại người gọi", ai["user"], "ketoan@vagabond.vn")


@ca("#266 vòng 5b (Codex): đường xuất TAY lọc dòng y hệt đường kịch bản")
def _xuat_tay_cung_phep_loc():
	"""Vòng 4 mới sửa phép lọc cho kịch bản Server Script. Codex bắt đúng
	lần thứ hai: ban_hang.xuat_hoa_don_dien_tu vẫn dựng một dòng payload cho
	MỌI dòng SI, nên đơn có một món 0 đồng đi đường xuất tay bị chặn ngay ở
	cửa cuối, đúng câu lỗi đã làm chết đêm 09/09."""
	for gia, mong in ((150000, True), (0, False), (-1, False), (None, False)):
		la("amount=%r" % gia, dong_duoc_gui({"amount": gia}), mong)
	b = _doc("vagabond", "ban_hang.py")
	i = b.find("def xuat_hoa_don_dien_tu(")
	than = b[i:b.find("\ndef ", i + 10)]
	dung("đường xuất tay dùng chung phép lọc", "dong_duoc_gui(r)" in than)
	dung("và không đánh số dòng bằng enumerate nữa",
		"for i, r in enumerate(si.items, 1):" not in than)
	t = _doc("vagabond", "thue_vnd.py")
	dung("dong_len_hoa_don cũng gọi chung ham đó", "if dong_duoc_gui(it)" in t)
	dung("chỉ có MỘT chỗ định nghĩa phép lọc", t.count("def dong_duoc_gui(") == 1)


@ca("#266 vòng 4 (Codex): phép lọc dòng phải Y HỆT kịch bản, lọc theo amount")
def _loc_giong_kich_ban():
	"""Kịch bản lọc `flt(it.amount) > 0`, tức thành tiền dòng TRƯỚC khi chia
	chiết khấu đầu phiếu. Bản trước lọc theo gross, là tiền SAU khi chia.

	Tái hiện: hai dòng 1.000.000 và 1.000, chiết khấu 1.000.999 trên Grand
	Total. Sau phân bổ, gross là 1 và 0. Kịch bản vẫn gửi ĐỦ HAI dòng vì cả
	hai đều amount > 0; hàm cũ chỉ nhận một dòng, nên cửa cuối chặn đúng bằng
	câu lỗi đã làm chết đêm 09/09.

	ĐỪNG đổi ca này về lọc gross. Muốn đổi phép lọc thì phải đổi CẢ kịch bản
	trên site cùng lúc, xem chú thích trong dong_len_hoa_don."""
	gia = [1000000, 1000]
	ds = tinh_dong(gia, [0, 0], True, 1000999, "Grand Total")
	la("chiết khấu đẩy dòng nhỏ về 0", [d["gross"] for d in ds], [1, 0])
	items = [{"idx": i, "name": str(i), "item_code": ma, "qty": 1, "amount": g, "net_amount": d["net"]}
		for i, (ma, g, d) in enumerate(zip(["MON-LON", "MON-BE"], gia, ds), 1)]
	la("lọc đúng như kịch bản, giữ cả dòng gross 0",
		[it["item_code"] for it, _ in dong_len_hoa_don(items, ds)], ["MON-LON", "MON-BE"])
	# Và cửa cuối cho payload hai dòng của kịch bản đi qua.
	si = {"name": "Y", "posting_date": "2026-09-09", "vgb_thue_vnd": 1, "items": items,
		"taxes": [{"name": "T", "idx": 1, "tax_amount_after_discount_amount": 0}],
		"net_total": 1, "total_taxes_and_charges": 0, "grand_total": 1,
		"item_wise_tax_details": [{"item_row": str(i), "tax_row": "T", "rate": 0, "amount": 0}
			for i in (1, 2)]}
	goi = {"details": [{"data": [{"inv_itemCode": ma, "inv_quantity": 1} for ma in ("MON-LON", "MON-BE")]}]}
	chuan_tien(si, goi)
	la("hai dòng lên tờ", [d["inv_itemCode"] for d in goi["details"][0]["data"]], ["MON-LON", "MON-BE"])


@ca("#266 vòng 4 (Codex): chip CẦN ĐỐI CHIẾU phải đứng TRƯỚC chip chờ xuất")
def _thu_tu_chip():
	"""Gửi tờ đi mà phản hồi không rõ thì giữ cờ đối chiếu VÀ giữ nguyên
	vgb_hddt_ngay_xuat. Xét ngày xuất trước là chỉ hiện chip vàng, giấu mất
	việc kế toán phải vào m-invoice dò tay. Chốt thứ tự ở CẢ HAI màn."""
	for tep, ham in (("08-doanh-so-sales.js", "function dsChips("),
			("10-bill-quay.js", "posChipBill")):
		ma = _doc("vagabond", "public", "js", "bep", tep)
		i = ma.find(ham)
		dung("tìm thấy %s trong %s" % (ham, tep), i > 0)
		than = ma[i:i + 3000]
		vi_doi = than.find("vgb_hddt_cho_doi_chieu")
		vi_ngay = than.find("vgb_hddt_ngay_xuat")
		dung("%s: cả hai nhánh còn đó" % tep, vi_doi > 0 and vi_ngay > 0)
		dung("%s: đối chiếu đứng trước chờ xuất" % tep, vi_doi < vi_ngay)


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


# Mẫu not-found GIẢ ĐỊNH, chỉ dùng trong kiểm thử để chạy thử đường khớp mẫu.
# KHÔNG khai vào MAU_KHONG_CO_TO của mô đun thật cho tới khi đo được phản hồi
# thật của m-invoice cho một mã phiếu không tồn tại.
MAU_THU = ({"code": "01", "message": "not found", "data": None},)
CHUNG_THU = {"duong": "SI-X", "so_hd": "12943", "khoa_am": "VGB-KHONG-TON-TAI-AB12"}


@ca("#266 vòng 5 (F1): chưa khai mẫu đã xác minh thì KHÔNG gỡ cờ tờ nào")
def _chua_khai_mau():
	"""Tái hiện được ba phản ví dụ của Codex. Cách cũ suy mẫu not-found bằng
	cách hỏi một mã bịa ra rồi lấy mã trả về làm chuẩn: chỉ chứng minh "cổng
	trả mã ấy cho mã đó", không chứng minh mọi phản hồi mang mã ấy nghĩa là
	không có tờ. Đo trước sửa: cả ba ca dưới đây đều cho GỠ CỜ."""
	la("mô đun thật để mẫu RỖNG là cố ý", hddt_cho_xuat.MAU_KHONG_CO_TO, ())
	# A. mẫu âm không có khoá code, tờ thật bị từ chối quyền: cùng mã None.
	a = {"message": "Không đủ quyền"}
	# B. mẫu âm 9999, tờ thật cũng 9999 - đúng mã đã từ chối 116 tờ TCV đêm 09/09.
	b = {"code": "9999", "message": "Mã chưa rõ"}
	# C. cùng mã 01 nhưng nội dung là từ chối quyền.
	c = {"code": "01", "data": {"reason": "Không đủ quyền"}}
	for ten, ph in (("A", a), ("B", b), ("C", c)):
		dung("phản ví dụ %s phải GIỮ cờ" % ten,
			not hddt_cho_xuat.minvoice_khong_co_to(ph, chung=CHUNG_THU))
	# Chưa khai mẫu thì cả câu sạch cũng không gỡ.
	dung("chưa khai mẫu thì câu sạch cũng giữ", not hddt_cho_xuat.minvoice_khong_co_to(
		{"code": "01", "message": "not found", "data": None}, chung=CHUNG_THU))
	# Và cửa hỏi từng tờ dừng ngay từ đầu, nói rõ lý do cho kế toán.
	co, cau = hddt_cho_xuat._tra_minvoice("http://x", {}, "SI-1", CHUNG_THU)
	dung("không kết luận", not co)
	dung("và nói rõ vì chưa khai mẫu", "chưa khai mẫu" in cau)


@ca("#266 vòng 5 (F1): khai mẫu rồi thì khớp ĐÚNG mẫu mới gỡ")
def _khai_mau_roi():
	"""Đường khớp mẫu vẫn phải chạy đúng cho ngày khai được mẫu thật, và ba
	phản ví dụ A/B/C vẫn phải giữ cờ kể cả khi đã khai mẫu."""
	m = dict(chung=CHUNG_THU, mau=MAU_THU)
	dung("khớp đủ mẫu thì gỡ", hddt_cho_xuat.minvoice_khong_co_to(
		{"code": "01", "message": "not found", "data": None}, **m))
	for ten, ph in (("A", {"message": "Không đủ quyền"}),
			("B", {"code": "9999", "message": "Mã chưa rõ"}),
			("C", {"code": "01", "data": {"reason": "Không đủ quyền"}})):
		dung("phản ví dụ %s vẫn giữ cờ dù đã khai mẫu" % ten,
			not hddt_cho_xuat.minvoice_khong_co_to(ph, **m))
	# Thiếu một khoá của mẫu là không khớp: mẫu là điều kiện ĐỦ, không phải gần đúng.
	for ph in ({"code": "01", "data": None},
			{"code": "01", "message": "not found"},
			{"code": "01", "message": "Not Found", "data": None}):
		dung("thiếu hoặc lệch khoá thì giữ %s" % ph,
			not hddt_cho_xuat.minvoice_khong_co_to(ph, **m))
	# Khớp mẫu nhưng lại có dấu vết chứng từ thì vẫn giữ: hai lớp, không phải một.
	ph = {"code": "01", "message": "not found", "data": None, "inv_invoiceNumber": "12950"}
	dung("khớp mẫu mà có dấu vết thì vẫn giữ",
		not hddt_cho_xuat.minvoice_khong_co_to(ph, **m))
	# Chưa đối chứng được API thì không gỡ, dù khớp mẫu.
	dung("chưa đối chứng thì giữ", not hddt_cho_xuat.minvoice_khong_co_to(
		{"code": "01", "message": "not found", "data": None}, chung=None, mau=MAU_THU))
	dung("chung rỗng cũng giữ", not hddt_cho_xuat.minvoice_khong_co_to(
		{"code": "01", "message": "not found", "data": None}, chung={}, mau=MAU_THU))
	# Phản hồi không phải dict thì không kết luận.
	for ph in (None, "<html>", 0, []):
		dung("phản hồi không phải dict thì giữ %r" % (ph,),
			not hddt_cho_xuat.minvoice_khong_co_to(ph, **m))


@ca("#266 vòng 5 (F1): đối chứng DƯƠNG TÍNH phải đúng TỜ ĐÓ, không phải tờ bất kỳ")
def _doi_chung_dung_to():
	"""kiem_chung_api không còn suy mẫu not-found nữa; nó chỉ còn là phép thử
	độ tin cậy của cổng trong lượt. Hai phép, thiếu một là không gỡ cờ tờ nào."""
	db = unittest.mock.MagicMock()
	db.get_value.return_value = {"name": "SI-DA-CO-HDDT", "custom_hddt_so": "12943"}

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

	dung_to = {"code": "00", "data": {"inv_invoiceNumber": "12943"}}
	to_khac = {"code": "00", "data": {"inv_invoiceNumber": "99999"}}
	sach = {"code": "01", "message": "not found", "data": None}

	(chung, cau), hoi = chay(lambda k: dung_to if k == "SI-DA-CO-HDDT" else sach)
	dung("đối chứng được", bool(chung))
	la("và nhớ số hoá đơn của tờ đối chứng", chung.get("so_hd"), "12943")
	dung("có hỏi một mã phiếu bịa ra", any(
		str(k).startswith(hddt_cho_xuat.KHOA_AM_TINH) for k in hoi))
	la("hai lần hỏi khác mã nhau", len(set(hoi)), 2)
	dung("KHÔNG còn suy mã not-found từ mẫu âm", "ma" not in chung)

	# Cổng trả dấu vết của TỜ KHÁC: tra nhầm tờ, còn nguy hơn không trả gì.
	(chung, cau), _ = chay(lambda k: to_khac if k == "SI-DA-CO-HDDT" else sach)
	dung("trả nhầm tờ thì không kết luận", chung is None)
	dung("và nói rõ là tra nhầm", "tra nhầm" in cau)

	# Mẫu âm tính lại có dấu vết: cổng nhận vơ.
	(chung, cau), _ = chay(lambda k: dung_to)
	dung("mẫu âm có dấu vết thì không kết luận", chung is None)
	dung("và nói rõ là nhận vơ", "nhận vơ" in cau)

	# Mẫu dương tính không có dấu vết thì dừng trước, không hỏi mẫu âm.
	(chung, cau), hoi = chay(lambda k: sach)
	dung("mẫu dương không dấu vết thì dừng", chung is None)
	la("dừng ngay, chỉ hỏi một lần", len(hoi), 1)

	# Ném lỗi ở bất kỳ phép nào cũng là không kết luận.
	for dap, mo_ta in (
			(lambda k: RuntimeError("timeout"), "mẫu dương ném lỗi"),
			(lambda k: dung_to if k == "SI-DA-CO-HDDT" else RuntimeError("404"), "mẫu âm ném lỗi")):
		(chung, _), _ = chay(dap)
		dung(mo_ta + " thì không kết luận", chung is None)

	# Chưa có tờ nào đã xuất thì không đối chứng được.
	db.get_value.return_value = None
	(chung, cau), hoi = chay(lambda k: sach)
	dung("không có tờ mẫu thì không kết luận", chung is None)
	la("và không hỏi m-invoice lần nào", len(hoi), 0)
	db.get_value.return_value = {"name": "SI-DA-CO-HDDT", "custom_hddt_so": "12943"}


@ca("#266 vòng 5 (F1): đường đi trong chay_nen vẫn gọi đủ hai bước")
def _go_co_chua_kiem_chung():
	h = _doc("vagabond", "hddt_cho_xuat.py")
	# #266 vong 5b: than that cua chay_nen tach sang _chay_nen_da_nang_quyen
	# de tra lai quyen cho nguoi goi (xem ca "tra lai quyen").
	i = h.find("def _chay_nen_da_nang_quyen(")
	than = h[i:h.find("\ndef ", i + 10)]
	dung("chay_nen đối chứng API trước khi hỏi từng tờ", "kiem_chung_api(base, hdr)" in than)
	dung("và truyền kết quả đối chứng vào từng lượt hỏi",
		"_tra_minvoice(base, hdr, r.name, chung)" in than)
	kc = h[h.find("def kiem_chung_api("):]
	kc = kc[:kc.find("\ndef ", 10)]
	dung("mẫu đối chứng là tờ CHẮC CHẮN đã có hoá đơn",
		'"custom_hddt_so": ["!=", ""]' in kc and '"custom_minvoice_id": ["!=", ""]' in kc)
	dung("và có mẫu ÂM TÍNH bằng mã phiếu bịa ra", "KHOA_AM_TINH" in kc and "uuid4()" in kc)
	dung("dấu vết phải mang số hoá đơn của chính tờ đối chứng", "so_hd not in json.dumps" in kc)
	dung("không còn suy mã not-found từ mẫu âm", '"ma":' not in kc)


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
	# #266 vong 5b: than that cua chay_nen tach sang _chay_nen_da_nang_quyen
	# de tra lai quyen cho nguoi goi (xem ca "tra lai quyen").
	i = h.find("def _chay_nen_da_nang_quyen(")
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


@ca("#266 vòng 5 (F2): không còn van thời gian, còn nợ là chặn")
def _phep_nhuong():
	"""Tái hiện được finding vòng 5 của Codex: van 15 phút đo lại thì dấu so
	sánh ngược, mốc lỗi 0s/60s/899s đều CHO ĐI, chỉ 900s mới chặn. Van mở
	NGAY sau lỗi. Mà sửa dấu vẫn không đủ, vì một tờ ngày mới đi lọt là đóng
	cửa ngày cũ VĨNH VIỄN. Nay gỡ hẳn van.
	ĐỪNG thêm lại tham số thời gian nào vào hàm này."""
	import inspect
	ds = ["2026-09-09"]
	hn = D(2026, 9, 10)
	phai, ngay, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(hn, hn, ds, D(2026, 9, 8))
	dung("tờ hôm nay phải nhường", phai and ngay == [D(2026, 9, 9)])
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(D(2026, 9, 9), hn, ds, D(2026, 9, 8))
	dung("tờ ngày cũ được đi", not phai)
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(hn, hn, ds, D(2026, 9, 10))
	dung("cửa đã đóng thì thôi", not phai)
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(hn, hn, [], None)
	dung("không nợ thì đi", not phai)
	# Van đã gỡ: hàm không còn nhận mốc lỗi hay đồng hồ nữa.
	ts = list(inspect.signature(hddt_cho_xuat.phai_nhuong_ngay_cu).parameters)
	la("chữ ký không còn tham số thời gian", ts,
		["ngay_lap_to", "hom_nay", "ds_ngay_cho", "ngay_so_moi_nhat"])
	h = _doc("vagabond", "hddt_cho_xuat.py")
	than = h[h.find("def phai_nhuong_ngay_cu("):]
	than = than[:than.find("\ndef ", 10)]
	for tu in ("moc_loi", "CHO_SAU_LOI_PHUT", "_doc_moc_loi"):
		dung("thân hàm không còn %s" % tu, tu not in than)
	dung("và hằng số van đã bỏ khỏi mô đun", "CHO_SAU_LOI_PHUT" not in h)


@ca("#266 vòng 5 (F3): chỉ ngày nợ SỚM NHẤT được đi, không phải mọi ngày cũ")
def _chi_ngay_som_nhat():
	"""Tái hiện được: bản trước miễn cho MỌI tờ mang ngày trước hôm nay, nên
	sang 11/09 thì tờ 10/09 vượt được nợ 09/09 và đóng cửa 09/09 vĩnh viễn.
	Đo trước sửa: ngay_lap=10/09, nợ=[09/09] cho phai_nhuong=False."""
	hn = D(2026, 9, 11)
	no = ["2026-09-09", "2026-09-10"]
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(D(2026, 9, 10), hn, no, D(2026, 9, 8))
	dung("tờ 10/09 phải nhường nợ 09/09", phai)
	phai, _, ly = hddt_cho_xuat.phai_nhuong_ngay_cu(D(2026, 9, 9), hn, no, D(2026, 9, 8))
	dung("chính tờ 09/09 được đi", not phai)
	dung("và nói rõ vì là ngày nợ sớm nhất", "sớm nhất" in ly)
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(D(2026, 9, 11), hn, no, D(2026, 9, 8))
	dung("tờ hôm nay vẫn phải nhường", phai)
	# Xong ngày 09 thì tới lượt 10 được đi.
	phai, _, _ = hddt_cho_xuat.phai_nhuong_ngay_cu(D(2026, 9, 10), hn, ["2026-09-10"], D(2026, 9, 8))
	dung("hết nợ 09 thì tờ 10/09 được đi", not phai)


@ca("#266 vòng 5 (F4): đọc nợ hỏng thì NÉM, và hàng rào phải chặn")
def _doc_no_hong():
	"""Tái hiện được: trước sửa ngay_cu_dang_cho() nuốt lỗi DB và trả [],
	caller hiểu là HẾT NỢ nên chan_neu_con_ngay_cu() cho tờ ngày mới đi
	thẳng. Đo trước sửa: DB lỗi -> ds = [], chan_neu_con_ngay_cu KHÔNG chặn."""
	db = unittest.mock.MagicMock()
	db.sql.side_effect = RuntimeError("mất kết nối DB")
	gia = unittest.mock.MagicMock(db=db)
	with unittest.mock.patch.object(hddt_cho_xuat, "frappe", gia), \
			unittest.mock.patch.object(hddt_cho_xuat, "nowdate", lambda: "2026-09-10"):
		for ham in ("ngay_cu_dang_cho", "ngay_cu_can_bao_ve"):
			try:
				getattr(hddt_cho_xuat, ham)()
				dung(ham + " phải ném khi đọc hỏng", False)
			except hddt_cho_xuat.KhongDocDuocNo:
				dung(ham + " ném đúng loại", True)
	h = _doc("vagabond", "hddt_cho_xuat.py")
	i = h.find("def chan_neu_con_ngay_cu(")
	than = h[i:h.find("\ndef ", i + 10)]
	dung("hàng rào bắt KhongDocDuocNo và chặn",
		"KhongDocDuocNo" in than and "frappe.throw" in than)
	dung("hàng rào dùng tập RỘNG", "ngay_cu_can_bao_ve()" in than)
	# Tập rộng phải rộng thật: nháp, giữ cờ, chưa đánh dấu đều nằm trong.
	def _sql(ten):
		t = h[h.find("def %s(" % ten):]
		t = t[:t.find("\ndef ", 10)]
		return t[t.find("frappe.db.sql("):]
	r = _sql("ngay_cu_can_bao_ve")
	dung("nhận cả đơn nháp", "docstatus in (0, 1)" in r)
	dung("không loại tờ đang giữ cờ đối chiếu", "vgb_hddt_cho_doi_chieu" not in r)
	dung("không đòi phải có dấu ngày xuất", hddt_cho_xuat.TRUONG_NGAY_XUAT not in r)
	n = _sql("ngay_cu_dang_cho")
	dung("tập hẹp vẫn hẹp, chỉ tờ tự gửi được", "vgb_hddt_cho_doi_chieu" in n)
	dung("và tập hẹp chỉ nhận tờ đã ghi sổ", "docstatus = 1" in n)


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
		"return not ngay_cu_con_mo(ngay_cu_can_bao_ve()" in than)
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
