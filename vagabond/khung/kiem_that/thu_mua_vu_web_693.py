"""v693 bench: tab In season cho Panettone và Bûche trên ERPNext thật.

Tầng khung đã kiểm các phép thuần. Ở đây chứng minh trên site dựng thật: doctype
Mùa vụ nhận các ô mới sau migrate (bảng con Sốt, ba ô của dòng, bốn ô lịch); lưu
Mùa vụ có ô lịch ghi sai bị chặn; lưu hợp lệ thì tạo đúng một thẻ nội dung cho
mỗi nhóm và không tạo trùng; hang_theo_mua trả nhóm đã gộp size kèm sốt, luật và
nội dung; phép kiểm lúc tạo đơn từ chối ngày sai.

Dữ liệu trong ca là GIẢ (mã, tên, giá). Ca KHÔNG đọc bản ghi thật của site
(Codex #626 P1): hàm chọn mùa cho web được thay bằng bản ghi của ca; mọi truy vấn
thẻ Bánh trên web đi qua mua_vu_web.the_cua, chỉ lấy đúng khoá và mã của ca, và
một bộ ghi chép bắt mọi lần đọc bảng thẻ Bánh để chứng minh không dòng nào ngoài
phạm vi ca; bản ghi thật được chứng minh giữ nguyên bằng số đếm và mốc sửa cuối
(chỉ phép tổng hợp, không đọc nội dung).
"""
import contextlib
import datetime
from unittest.mock import patch

import frappe

from vagabond import banh_web as bw
from vagabond import mua_vu as mv
from vagabond import mua_vu_web as mw
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, la

TEN_MUA = "Mua Kiem Thu Web 693"
TIEN_TO = "BASS-KIEM-693-"
KHOA_CA = ("Panettone Thử 693", "Bûche Thử 693")


def _khoa_ca():
	return [bw.khoa_banh(t) for t in KHOA_CA]


def _dau_vet_that():
	"""Số đếm và mốc sửa cuối của bản ghi THẬT (ngoài phạm vi ca) ở hai bảng ca
	chạm tới. Chỉ phép tổng hợp, không đọc nội dung bản ghi nào."""
	a = frappe.db.sql("select count(*), max(modified) from `tab%s` where khoa not in %%(k)s" % bw.DT, {"k": tuple(_khoa_ca())})[0]
	b = frappe.db.sql("select count(*), max(modified) from `tab%s` where ifnull(ten_mua, '') != %%(t)s" % mv.DT, {"t": TEN_MUA})[0]
	return (int(a[0]), str(a[1] or ""), int(b[0]), str(b[1] or ""))


@contextlib.contextmanager
def _ghi_lan_doc_the():
	"""Ghi lại mọi dòng thẻ Bánh trên web được đọc trong khối; so_ghi (đọc cả bảng)
	bị cấm hẳn. Trả danh sách các dòng đã đọc."""
	goc, doc = frappe.get_all, []

	def get_all(dt, *a, **k):
		ra = goc(dt, *a, **k)
		if dt == bw.DT:
			doc.extend(ra)
		return ra

	def cam():
		raise AssertionError("ca bench không được đọc cả bảng thẻ Bánh (so_ghi)")

	with patch.object(frappe, "get_all", get_all), patch.object(bw, "so_ghi", cam):
		yield doc


def _chi_trong_ca(doc):
	"""Mọi dòng đã đọc thuộc ca: khoá của ca hoặc có gắn mã thử."""
	khoa = set(_khoa_ca())
	return [x for x in doc if x.get("khoa") not in khoa and TIEN_TO not in str(x.get("ma_hang") or "")]


def _mon(ma, ten, gia):
	from vagabond.khung.kiem_that import nen

	d = frappe.get_doc({"doctype": "Item", "item_code": ma, "item_name": ten,
		"item_group": nen._mot("Item Group", {"is_group": 0}), "stock_uom": nen._mot("UOM", {}),
		"is_stock_item": 0, "is_sales_item": 1, "standard_rate": gia})
	d.insert(ignore_permissions=True)
	_DA_TAO.append((d.doctype, d.name))
	return d.name


def _ma_thu():
	return (_mon("BASS-KIEM-693-P1", "Panettone Thử 693, 680gr", 780000), _mon("BASS-KIEM-693-P2", "Panettone Thử 693 Mini, 250gr", 320000),
		_mon("BASS-KIEM-693-B1", "Bûche Thử 693", 990000), _mon("BASS-KIEM-693-S1", "Sốt Thử 693", 45000))


def _mua(ma=None, **them):
	hn = frappe.utils.getdate(frappe.utils.nowdate())
	p1, p2, b1, s1 = ma or _ma_thu()
	doc = frappe.get_doc(dict({"doctype": mv.DT, "ten_mua": TEN_MUA, "tinh_trang": "Dang ban",
		"tu_ngay": hn, "den_ngay": frappe.utils.add_days(hn, 30),
		"dong": [
			{"ma_hang": p1, "ten_banh": "Panettone Thử 693", "sx_dau_mua": 9, "nhom_web": "Panettone Thử 693", "nhan_size": "Bánh lớn 680gr", "loai_web": "Panettone"},
			{"ma_hang": p2, "ten_banh": "Panettone Thử 693 Mini", "sx_dau_mua": 4, "nhom_web": "Panettone Thử 693", "nhan_size": "Bánh Mini 250gr"},
			# Codex #625: size Mini chưa điền loại (theo loại của nhóm); tên trên dòng Bûche khác tên hồ sơ món.
			{"ma_hang": b1, "ten_banh": "Bûche Tên Pancake 693", "sx_dau_mua": 3, "loai_web": "Bûche"}],
		"sot_web": [{"ma_hang": s1}]}, **them))
	return doc, (p1, p2, b1, s1)


@ca("v693 bench: Mùa vụ có đủ ô mới sau migrate; ô lịch ghi sai bị chặn lúc lưu; lưu hợp lệ tạo một thẻ nội dung mỗi nhóm, lưu lại không tạo trùng")
def _():
	m, md = frappe.get_meta(mv.DT), frappe.get_meta("Vagabond Mua Vu Dong")
	dung("ô của Mùa vụ", all(m.has_field(f) for f in ("sot_web", "panettone_thu", "panettone_truoc", "buche_thu", "buche_truoc")))
	dung("ô của dòng", all(md.has_field(f) for f in ("nhom_web", "nhan_size", "loai_web")))
	dung("thẻ Bánh có cờ mùa vụ", frappe.get_meta(bw.DT).has_field("mua_vu"))
	vet = _dau_vet_that()
	dem_ca = lambda: frappe.db.count(bw.DT, {"khoa": ["in", _khoa_ca()]})  # noqa: E731
	truoc = dem_ca()
	ma = _ma_thu()
	sai, _ma = _mua(ma, panettone_thu="thứ hai")
	loi = ""
	try:
		sai.insert(ignore_permissions=True)
	except frappe.ValidationError as e:
		loi = str(e)
	dung("ô thứ ghi sai bị chặn, câu nói cách ghi đúng: " + loi[:80], "2,4,6" in loi)
	doc, (p1, p2, _b1, _s1) = _mua(ma, panettone_truoc="0", buche_thu="7,CN")
	with _ghi_lan_doc_the() as da_doc:
		doc.insert(ignore_permissions=True)
	_DA_TAO.append((doc.doctype, doc.name))
	khoa_p, khoa_b = _khoa_ca()
	for k in (khoa_p, khoa_b):
		_DA_TAO.append((bw.DT, k))
	la("tạo thẻ nội dung không đọc dòng nào ngoài ca", _chi_trong_ca(da_doc), [])
	la("hai nhóm, hai thẻ nội dung mới", dem_ca() - truoc, 2)
	bg = frappe.get_doc(bw.DT, khoa_p)
	la("thẻ mùa vụ: cờ, không chờ ảnh, đủ hai mã size", (int(bg.mua_vu), bg.trang_thai, bw.tach_dong(bg.ma_hang)), (1, bw.DA_AN, [p1, p2]))
	doc.reload()
	with _ghi_lan_doc_the() as da_doc:
		doc.save(ignore_permissions=True)
	dung("lưu lại có đọc thẻ của ca", len(da_doc) >= 1)
	la("lưu lại không đọc dòng nào ngoài ca", _chi_trong_ca(da_doc), [])
	la("lưu lại không tạo trùng", dem_ca() - truoc, 2)
	la("số 0 và ô đã điền được giữ đúng, ô trống là None hoặc rỗng", (doc.panettone_truoc, doc.buche_thu, doc.panettone_thu or "", doc.buche_truoc or ""), ("0", "7,CN", "", ""))
	la("bản ghi thật của hai bảng giữ nguyên (số đếm, mốc sửa cuối)", _dau_vet_that(), vet)


@ca("v693 bench: hang_theo_mua gộp size, kèm sốt theo giá hồ sơ món, luật theo ô cài đặt, nội dung thẻ Bánh; lúc tạo đơn ngày sai và quá 2 hũ sốt bị từ chối")
def _():
	vet = _dau_vet_that()
	doc, (p1, p2, b1, s1) = _mua(panettone_truoc="1", buche_thu="7,CN")
	doc.insert(ignore_permissions=True)
	_DA_TAO.append((doc.doctype, doc.name))
	khoa_p = bw.khoa_banh("Panettone Thử 693")
	for k in (khoa_p, bw.khoa_banh("Bûche Thử 693")):
		_DA_TAO.append((bw.DT, k))
	frappe.db.set_value(bw.DT, khoa_p, {"mo_ta": "Mô tả thử 693.", "tang": "Men tự nhiên\nBơ", "di_ung": "Gluten", "bao_quan": ""})
	doc.reload()
	with patch.object(mv, "mua_cho_web", lambda: doc), patch.object(bw, "dang_dung", lambda: True), _ghi_lan_doc_the() as da_doc:
		kq = mv.hang_theo_mua()
		dung("tab In season có đọc thẻ của ca", any(x.get("khoa") == khoa_p for x in da_doc))
		la("tab In season không đọc dòng thẻ Bánh nào ngoài ca", _chi_trong_ca(da_doc), [])
		la("có mùa của ca", (kq["co"], kq["ten_mua"]), (1, TEN_MUA))
		g = next(x for x in kq["nhom"] if x["ten"] == "Panettone Thử 693")
		la("một thẻ hai size, size lớn trước", [(s["ma"], s["nhan"], s["gia"]) for s in g["sizes"]], [(p1, "Bánh lớn 680gr", 780000), (p2, "Bánh Mini 250gr", 320000)])
		la("loại và nội dung của thẻ", (g["loai"], g["mo_ta"], g["tang"], g["di_ung"], g["bao_quan"]), ("panettone", "Mô tả thử 693.", ["Men tự nhiên", "Bơ"], "Gluten", ""))
		dung("Bûche đứng một thẻ, mang loại", any(x["loai"] == "buche" and len(x["sizes"]) == 1 and x["sizes"][0]["ma"] == b1 for x in kq["nhom"]))
		la("danh sách phẳng cũ còn nguyên ba mã cho trang đang mở", sorted(x["ma"] for x in kq["mon"]), sorted([p1, p2, b1]))
		la("sốt theo giá hồ sơ món", [(x["ma"], x["gia"]) for x in kq["sot"]], [(s1, 45000)])
		la("luật theo ô cài đặt", kq["luat"], {"panettone": {"truoc": 1, "thu": [2, 4, 6]}, "buche": {"truoc": 2, "thu": [7, 8]}})
		mua = mw.doc_mua_web()
		hn = frappe.utils.getdate(frappe.utils.nowdate())
		tot = next(hn + datetime.timedelta(days=i) for i in range(1, 9) if mw.thu_cua_ngay(hn + datetime.timedelta(days=i)) in (2, 4, 6))
		xau = next(hn + datetime.timedelta(days=i) for i in range(1, 9) if mw.thu_cua_ngay(hn + datetime.timedelta(days=i)) in (3, 5))
		h = lambda **k: [{"variation_id": ma, "quantity": sl} for ma, sl in k.items()]  # noqa: E731
		la("Panettone ngày đúng thứ: nhận", mw.kiem_don(h(**{p1: 1}), str(tot) + "T13:00:00", mua), None)
		la("Panettone ngày sai thứ: từ chối", (mw.kiem_don(h(**{p1: 1}), str(xau) + "T13:00:00", mua) or {}).get("ly_do"), "ngay_mua_vu")
		la("Panettone nhận hôm nay khi cài trước 1 ngày: từ chối", (mw.kiem_don(h(**{p2: 1}), str(hn), mua) or {}).get("ly_do"), "ngay_mua_vu")
		la("1 bánh 3 hũ sốt: từ chối", (mw.kiem_don(h(**{p1: 1, s1: 3}), str(tot), mua) or {}).get("ly_do"), "sot_qua_so")
		la("mã Panettone không tính dĩa nĩa", mw.ma_khong_dung_cu(), {p1, p2})
	la("bản ghi thật của hai bảng giữ nguyên (số đếm, mốc sửa cuối)", _dau_vet_that(), vet)


@ca("v697 bench: trần mỗi ngày và nút Ngưng nhận ngày này trên ERPNext thật; xét theo bảng Đơn theo ngày của ca; không đọc đơn web thật")
def _():
	vet = _dau_vet_that()
	dung("ô ngày ngưng sau migrate", frappe.get_meta(mv.DT).has_field("ngay_ngung_web"))
	doc, (p1, p2, _b1, _s1) = _mua()
	doc.dong[0].tran_ngay = 2
	hn = frappe.utils.getdate(frappe.utils.nowdate())
	ngay = str(hn + datetime.timedelta(days=10))
	doc.append("lich", {"ngay": ngay, "ma_hang": p1, "so_luong": 1, "cho_chot": 0, "don_khac": 0})
	doc.dong_bo_luc = frappe.utils.now_datetime()
	doc.insert(ignore_permissions=True)
	_DA_TAO.append((doc.doctype, doc.name))
	for k in _khoa_ca():
		_DA_TAO.append((bw.DT, k))
	doc.reload()
	goc, dw = frappe.get_all, []

	def get_all(dt, *a, **k):
		ra = goc(dt, *a, **k)
		if dt == "Vagabond Don Web":
			dw.extend(ra)
		return ra

	h = lambda **k: [{"variation_id": ma, "quantity": sl} for ma, sl in k.items()]  # noqa: E731
	# Đọc lại bản ghi mỗi lần như mua_cho_web thật (nút Ngưng nhận lưu bằng get_doc riêng).
	with patch.object(mv, "mua_cho_web", lambda: frappe.get_doc(doc.doctype, doc.name)), patch.object(frappe, "get_all", get_all):
		mua = mw.doc_mua_web()
		la("1 đã nhận + 1 đúng trần 2: nhận", mw.xet_ngay_that(h(**{p1: 1}), ngay, mua), None)
		la("1 đã nhận + 2 vượt trần: từ chối", (mw.xet_ngay_that(h(**{p1: 2}), ngay, mua) or {}).get("ly_do"), "ngay_mua_vu")
		kq = mv.ngung_ngay(mua=doc.name, ngay=ngay, ngung=1)
		la("bảng Lịch tháng trả ngày ngưng và số đã nhận", (kq["lich"]["ngung"], kq["lich"]["da_nhan"].get(ngay)), ([ngay], {p1: 1}))
		la("ngày ngưng: size không đặt trần cũng bị từ chối", (mw.xet_ngay_that(h(**{p2: 1}), ngay, mua) or {}).get("ly_do"), "ngay_mua_vu")
		la("trang khách nhận ngày ngưng", mv.hang_theo_mua()["han_ngay"]["ngung"], [ngay])
		mv.ngung_ngay(mua=doc.name, ngay=ngay, ngung=0)
		la("mở lại thì nhận", mw.xet_ngay_that(h(**{p2: 1}), ngay, mua), None)
		loi = ""
		try:
			mv.ngung_ngay(mua=doc.name, ngay=str(hn + datetime.timedelta(days=60)), ngung=1)
		except frappe.ValidationError as e:
			loi = str(e)
		dung("ngày ngoài khoảng mùa bị chặn: " + loi[:60], "ngoài khoảng" in loi)
	la("không đọc đơn web thật nào (chỉ đơn nhắc mã của ca)", [x for x in dw if not any(m in str(x.get("snapshot") or "") for m in (p1, p2))], [])
	la("bản ghi thật của hai bảng giữ nguyên (số đếm, mốc sửa cuối)", _dau_vet_that(), vet)
