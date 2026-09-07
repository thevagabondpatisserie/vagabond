"""#227: giữ đúng VAT từng dòng và chặn cấu hình đổi sau ghi sổ."""

from vagabond.hang_tang_so_cai import chia_thue, kiem_thue_gui
from vagabond.khung.kiem_thu.nen import ca, la, dung
from types import SimpleNamespace
from unittest.mock import patch
from vagabond import hang_tang_so_cai as sc


class To(dict):
	__getattr__ = dict.get
	__setattr__ = dict.__setitem__
	def set_status(self):
		self["status"] = "Paid" if not self.outstanding_amount else "Unpaid"

	def set(self, ten, so):
		self[ten] = so


def _to(**them):
	t = To(company="CTY", currency="VND", conversion_rate=1, grand_total=1900000,
		vgb_pt_thanh_toan="Hàng tặng", vgb_tang_so_cai=999, vgb_tang_tien_thue=999,
		outstanding_amount=1900000, update_stock=0)
	# dict.items là method; Frappe document dùng thuộc tính items.
	t.items = [To(amount=1900000)]
	object.__setattr__(t, "items", t["items"])
	t.update(them)
	return t


def _frappe():
	def nem(loi):
		raise ValueError(loi)
	def doc(dt, ten, o):
		return {"default_currency": "VND", "cost_center": "CC-CTY"}[o]
	def cau_hinh(dt):
		la("nguồn cấu hình đúng script trên site", dt, "MInvoice Phat Hanh Settings")
		return To(thue_suat=8)
	return SimpleNamespace(throw=nem, get_cached_value=doc, get_single=cau_hinh,
		get_all=lambda dt, **kw: [To(name=kw["filters"]["account_number"], account_currency="VND",
			root_type="Expense" if kw["filters"]["account_number"] == "64182" else "Liability", account_type="")])


@ca("#227: submit tự tính lại VAT, gỡ nợ, bù cost center, không sửa update_stock")
def _ghi_so():
	with patch.object(sc, "frappe", _frappe()):
		t = _to()
		sc.truoc_khi_ghi_so(t)
		la("không tin VAT client", t.vgb_tang_tien_thue, 140741)
		la("không tin marker client", t.vgb_tang_so_cai, 1)
		la("không phải thu", t.outstanding_amount, 0)
		la("tính lại trạng thái", t.status, "Paid")
		la("bù trung tâm chi phí", t.cost_center, "CC-CTY")
		la("chờ giá vốn, không xuất kho", (t.vgb_tang_cho_gia_von, t.update_stock), (1, 0))
		t = _to(vgb_pt_thanh_toan="Tiền mặt")
		sc.truoc_khi_ghi_so(t)
		la("đơn thường không nhận dấu giả", t.vgb_tang_so_cai, 0)
		la("đơn thường giữ nợ", t.outstanding_amount, 1900000)


@ca("#227: chưa có kho và các luồng không thuần hàng tặng đều dừng trước ghi sổ")
def _chan_luong():
	with patch.object(sc, "frappe", _frappe()):
		for them in ({"update_stock": 1}, {"is_return": 1}, {"is_pos": 1}, {"paid_amount": 1},
			{"is_opening": "Yes"}, {"advances": [1]}, {"currency": "USD"}):
			try:
				sc.truoc_khi_ghi_so(_to(**them))
			except ValueError:
				continue
			dung("phải chặn " + str(them), False)


@ca("#227: 1.900.000 gross ra 140.741 VAT, không gọi giá bán là giá vốn")
def _vat():
	la("đúng số issue", chia_thue(1900000, [{"amount": 1900000}], 8), [(1759259, 140741, 1900000)])
	for tong, gia in ((100, [30, 30, 40]), (99, [1, 1, 1]), (1900000, [1000000, 1000000])):
		ra = chia_thue(tong, [{"amount": g} for g in gia], 8)
		la("chia hết gross kể cả chiết khấu", sum(d[2] for d in ra), tong)
		dung("từng dòng cân", all(d[0] + d[1] == d[2] for d in ra))
	la("VAT 0 hợp lệ", chia_thue(100, [{"amount": 100}], 0), [(100, 0, 100)])


@ca("#227: không đoán VAT với tiền âm, NaN, thuế suất lạ")
def _loi():
	for tong, gia, ts in ((-1, 1, 8), (100, -1, 8), (100, 0, 8), (100, 100, 12), (float('nan'), 1, 8)):
		try:
			chia_thue(tong, [{"amount": gia}], ts)
		except ValueError:
			continue
		dung("phải báo dữ liệu không đủ", False)


@ca("#227: thuế suất hoặc VAT thay đổi thì không phát hành lệch sổ")
def _doi_thue():
	si = {"vgb_tang_so_cai": 1, "grand_total": 1900000, "items": [{"amount": 1900000}],
		"vgb_tang_thue_suat": 8, "vgb_tang_tien_thue": 140741}
	dong = {"inv_TotalAmountWithoutVat": 1759259, "inv_vatAmount": 140741, "inv_TotalAmount": 1900000, "ma_thue": 8}
	goi = dict(dong, details=[{"data": [dict(dong)]}])
	kiem_thue_gui(si, goi)
	for o, so in (("inv_vatAmount", 140740), ("ma_thue", 10), ("inv_TotalAmountWithoutVat", 1759260)):
		goi["details"][0]["data"][0] = dict(dong, **{o: so})
		try:
			kiem_thue_gui(si, goi)
		except ValueError:
			continue
		dung("phải chặn lệch sổ", False)
	# Phiếu lịch sử chưa theo cách ghi mới không bị tự đổi kế toán.
	kiem_thue_gui({}, goi)
