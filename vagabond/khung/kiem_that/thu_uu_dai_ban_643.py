"""v643: khách tự chọn ưu đãi trên trang gọi món tại bàn, chạy trên ERPNext thật.

Đi ĐÚNG các cửa: khách (phiên Guest) gọi `goi_mon_ban.goi` với link ký thật,
thu ngân nhận (phiếu tạm tính thật qua ban_hang.tao_don_tay); khách (Guest)
gọi `uu_dai_ban.ds` rồi `uu_dai_ban.chon` một chương trình THẬT (Vagabond CTKM
giảm 10% hoá đơn từ 150.000 đ, lập trong ca). Phiên Thành viên (cookie mã
Zalo) thay bằng `_phien` trả số kiểm, phần còn lại là thật: khuyen_mai.tinh,
Sales Invoice validate tính grand_total, hai trường mới đã dựng trên site.
Gọi thêm vào cùng phiếu thì phần ưu đãi tính lại; thu ngân chốt bill qua
ban_hang.pos_chot thật thì có đúng một lượt Vagabond CTKM Su Dung với cách
duyệt Zalo tại bàn. Không ghi sổ, không gửi gì ra ngoài.
"""
import json
from unittest.mock import patch

import frappe
from frappe.utils import flt

from vagabond import ban_hang, diem_ban
from vagabond import goi_mon_ban as g
from vagabond import uu_dai_ban as u
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, khong_nem, la
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen
from vagabond.khung.kiem_that.thu_goi_mon_ban_638 import _tra

SDT = "0909643643"


def _ctkm():
	km = frappe.get_doc({
		"doctype": "Vagabond CTKM", "ten": "Kiểm 643 giảm 10% tại bàn", "cach_thuc": "Giam tong hoa don",
		"kieu_giam": "Phan tram", "gia_tri": 10, "pham_vi": "Ca hoa don", "doi_tuong": "Moi khach",
		"cach_ma": "Khong can ma", "hd_toi_thieu": 150000, "bat": 1, "can_otp": 0, "uu_tien": 1,
	}).insert(ignore_permissions=True)
	_DA_TAO.append((km.doctype, km.name))
	return km.name


def _khach(fn):
	truoc = frappe.session.user
	try:
		frappe.set_user("Guest")
		return fn()
	finally:
		frappe.set_user(truoc)


@ca("v643 ưu đãi tại bàn: khách (Guest) chọn chương trình thật, máy trừ ngay vào phiếu tạm tính; gọi thêm thì tính lại; chốt bill ghi đúng một lượt dùng")
def _vong_doi():
	cty, _tk, _mau = _nen()
	quay = next((d for d in diem_ban.ds(chi_bat=True) if d["quay"] and d["ma"] in diem_ban.diem_cua_nguon(g.NGUON_TAO)), None)
	dung("có điểm bán có quầy nhận Tại chỗ", quay)
	if not quay:
		return
	dung("site đã dựng trường vgb_giam_ud, vgb_ud_ban", frappe.get_meta("Sales Invoice").has_field("vgb_giam_ud")
		and frappe.get_meta("Sales Invoice").has_field("vgb_ud_ban"))
	km = _ctkm()
	ma = _tra(45000)
	gia = g.gia_mon(ma, diem_ban.gia_rieng(quay["ma"]), 45000)
	ban = 86
	k = g.khoa_ban(g._bi_mat(), quay["ma"], ban)
	kh = frappe.db.get_value("Customer", {"disabled": 0, "is_internal_customer": 0}, "name")
	with patch.object(g, "_gio_mo_cua", return_value={"dang_mo": True, "gio": "7:00 - 22:00"}), \
			patch.object(ban_hang, "_cong_ty", return_value=cty), patch.object(ban_hang, "_khach_le", return_value=kh), \
			patch.object(u, "_phien", return_value=(SDT, None)):
		r1 = _khach(lambda: g.goi(diem=quay["ma"], ban=ban, k=k, nonce="KT643" + frappe.generate_hash(length=24),
			mon=json.dumps([{"ma": ma, "sl": 4}])))
		la("khách gọi được (%s)" % (r1 or {}).get("cau"), (r1 or {}).get("ok"), 1)
		if not (r1 or {}).get("ok"):
			return
		_DA_TAO.append((g.DT, r1["ma"]))
		n1 = khong_nem("thu ngân nhận đơn", lambda: g.nhan(r1["ma"]))
		if not n1:
			return
		_DA_TAO.append(("Sales Invoice", n1["hoa_don"]))
		tong = 4 * gia
		ds = _khach(lambda: u.ds(diem=quay["ma"], ban=ban, k=k))
		x = next((y for y in ds.get("ds") or [] if y["ma"] == km), None)
		dung("chương trình kiểm có trong danh sách của bàn", x)
		if not x:
			return
		la("số giảm dự kiến 10%", (x["giam"], x["dung_duoc"]), (round(tong * 0.1), 1))
		c = _khach(lambda: u.chon(diem=quay["ma"], ban=ban, k=k, loai="ctkm", ma=km))
		la("chọn được (%s)" % c.get("cau"), c.get("ok"), 1)
		si = frappe.get_doc("Sales Invoice", n1["hoa_don"])
		la("máy trừ ngay", (flt(si.vgb_giam_ud), flt(si.discount_amount), flt(si.grand_total)),
			(float(round(tong * 0.1)), float(round(tong * 0.1)), float(tong - round(tong * 0.1))))
		bill = g._tong_bill(si.name)
		la("trang khách thấy tổng sau ưu đãi và dòng ưu đãi", (bill["tong"], bill["ud"]["giam"]), (int(tong - round(tong * 0.1)), int(round(tong * 0.1))))

		r2 = _khach(lambda: g.goi(diem=quay["ma"], ban=ban, k=k, nonce="KT643" + frappe.generate_hash(length=24),
			mon=json.dumps([{"ma": ma, "sl": 2}])))
		_DA_TAO.append((g.DT, r2["ma"]))
		khong_nem("nhận lượt gọi thêm", lambda: g.nhan(r2["ma"]))
		si.reload()
		tong2 = 6 * gia
		la("gọi thêm: ưu đãi tính lại trên giỏ mới", (flt(si.vgb_giam_ud), flt(si.grand_total)),
			(float(round(tong2 * 0.1)), float(tong2 - round(tong2 * 0.1))))

		truoc = frappe.db.count("Vagabond CTKM Su Dung", {"hoa_don": si.name})
		# Bench #546: thu ngân chốt là chọn phương thức thanh toán, đúng như màn quầy.
		kq = khong_nem("thu ngân chốt bill", lambda: ban_hang.pos_chot(si.name, pt="Tiền mặt"))
		if not kq:
			return
		si.reload()
		la("chốt xong đúng tổng, hết tạm tính", (flt(si.grand_total), si.vgb_tam_tinh), (float(tong2 - round(tong2 * 0.1)), 0))
		dl = frappe.get_all("Vagabond CTKM Su Dung", filters={"hoa_don": si.name}, fields=["name", "ctkm", "cach_duyet"])
		for d in dl:
			_DA_TAO.append(("Vagabond CTKM Su Dung", d.name))
		la("đúng một lượt dùng, cách duyệt Zalo tại bàn", [(d.ctkm, d.cach_duyet) for d in dl][truoc:], [(km, u.CACH_DUYET)])
		la("đánh dấu đã ghi", json.loads(si.vgb_ud_ban).get("da_ghi"), 1)
