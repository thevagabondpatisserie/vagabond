# -*- coding: utf-8 -*-
"""v684 (BẢN 2 mục 3): dữ liệu thẻ ĐƠN HÀNG và NHẬN BÁNH của biên nhận mới.

Chốt: mọi chữ, giá, lựa chọn lấy từ ảnh chụp đơn lúc đặt; thiệp ép kim nằm trong
từng chiếc (không thành dòng riêng) khi đơn có ghi từng chiếc; dĩa nĩa một dòng
tặng kèm; nhận bánh chỉ có phường và tên viết tắt, không số điện thoại, địa chỉ.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la

SNAP = {
	"mon": [
		{"ma": "BAWC00139", "ten": "Bánh Ổ OBON, size 12cm", "sl": 2, "gia": 450000},
		{"ma": "BAPK00002", "ten": "Thiệp ép kim", "sl": 1, "gia": 15000},
		{"ma": "BAPK00010", "ten": "Nến số 3", "sl": 1, "gia": 10000},
		{"ma": "BAPK00020", "ten": "Dĩa giấy bã mía", "sl": 5, "gia": 0},
		{"ma": "BAPK00018", "ten": "Nĩa gỗ", "sl": 5, "gia": 0},
	],
	"chiec": [
		{"ma": "BAWC00139", "ten": "Epi · Ø 12cm", "co": True, "loi_chuc": "Happy 30", "thiep": "ep_kim", "loi_thiep": "Thương em"},
		{"ma": "BAWC00139", "ten": "Epi · Ø 12cm", "co": False, "loi_chuc": "", "thiep": "khong", "loi_thiep": ""},
	],
	"tu_lay": False, "phuong": {"ma": "84_VN12903", "ten": "Phường Bến Thành"},
	"dia_chi": "10 Lê Lợi, Phường Bến Thành", "nguoi_dat": {"ho_ten": "Nguyễn Văn An", "dien_thoai": "0901234567"},
	"nguoi_nhan": {"ho_ten": "Trần Bình", "dien_thoai": "0912345678"},
}


@ca("v684 thẻ ĐƠN HÀNG: tên web lúc đặt (không tên nội bộ), cờ và thiệp từng chiếc, thiệp ép kim có giá là dòng có giá, mua thêm có giá, dĩa nĩa miễn phí gộp một dòng tặng kèm")
def _():
	from vagabond import bien_nhan_web as b
	d = b.dong_don(SNAP)
	la("loại dòng", [x["loai"] for x in d], ["banh", "them", "them", "tang"])
	la("bánh", (d[0]["ten"], d[0]["sl"], d[0]["gia"]), ("Epi · Ø 12cm", 2, "900.000 đ"))
	la("từng chiếc (lựa chọn đã lưu, chữ do trang lấy từ bảng chữ)", d[0]["chiec"], [
		{"co": True, "loi_chuc": "Happy 30", "thiep": "ep_kim", "loi_thiep": "Thương em"},
		{"co": False, "loi_chuc": "", "thiep": "", "loi_thiep": ""}])
	la("thiệp ép kim có giá vẫn là dòng có giá", (d[1]["ten"], d[1]["gia"]), ("Thiệp ép kim", "15.000 đ"))
	la("mua thêm", (d[2]["ten"], d[2]["gia"]), ("Nến số 3", "10.000 đ"))
	la("tặng kèm", d[3], {"loai": "tang", "muc": [{"ma": "dia", "sl": 5}, {"ma": "nia", "sl": 5}]})
	chi_nia = b.dong_don({"mon": [{"ma": "BAPK00018", "sl": 2, "gia": 0}, {"ma": "X", "sl": 1, "gia": 1}]})
	la("chỉ có nĩa", chi_nia[-1]["muc"], [{"ma": "nia", "sl": 2}])
	cu = b.dong_don({"mon": SNAP["mon"][:2]})
	la("đơn cũ không ghi từng chiếc: giữ dòng thiệp ép kim", [x["ten"] for x in cu], ["Bánh Ổ OBON, size 12cm", "Thiệp ép kim"])
	la("chọn cờ mà để trống lời chúc", b._chiec({"co": True, "loi_chuc": " ", "thiep": "nho"}), {"co": True, "loi_chuc": "", "thiep": "nho", "loi_thiep": ""})


@ca("v684 thẻ NHẬN BÁNH: giao thì chỉ phường, người nhận viết tắt; tự lấy thì tên điểm; không có số điện thoại hay địa chỉ trong dữ liệu biên nhận")
def _():
	from vagabond import bien_nhan_web as b, don_web
	nb = b.nhan_banh(SNAP, don_web.viet_tat_ten)
	la("giao", nb, {"tu_lay": False, "noi": "Phường Bến Thành", "nguoi_nhan": "T. Bình", "la_nguoi_dat": False})
	tl = b.nhan_banh({"tu_lay": True, "diem_lay_ten": "Cửa hàng Sài Gòn", "nguoi_dat": {"ho_ten": "Nguyễn Văn An"}}, don_web.viet_tat_ten)
	la("tự lấy, người đặt nhận", tl, {"tu_lay": True, "noi": "Cửa hàng Sài Gòn", "nguoi_nhan": "N. V. An", "la_nguoi_dat": True})
	tt = don_web.tom_tat_bien_nhan({"name": "DW-1", "trang_thai": "Da nhan", "tien_banh": 900000, "trang_thai_phi": "mien_phi", "thanh_toan": "bank"}, SNAP)
	s = repr(tt)
	dung("không số điện thoại, không địa chỉ", "0901234567" not in s and "0912345678" not in s and "10 Lê Lợi" not in s)
	dung("có thẻ mới", tt["dong"] and tt["nhan_banh"]["noi"] == "Phường Bến Thành")


@ca("v684 ảnh món trên biên nhận: chỉ ảnh /files/ PNG, JPG, WebP")
def _():
	from vagabond import don_web
	for u, ok in (("/files/epi.webp", True), ("/files/Bánh.png", False), ("https://x.com/a.png", False), ("/files/../a.png", False), ("/files/a.svg", False)):
		la(u, bool(don_web.RE_ANH_MON.match(u)), ok)


@ca("v684 Codex #606: các dòng thẻ ĐƠN HÀNG cộng lại ĐÚNG tiền bánh: thiệp ép kim, dĩa, nĩa có giá không biến mất; miễn phí thì không thành dòng tiền")
def _():
	from vagabond import bien_nhan_web as b

	def cong(d):
		return sum(int(x["gia"].replace(".", "").replace(" đ", "")) for x in d if x.get("gia"))

	def tien(snap):
		return sum(int(m["gia"]) * int(m["sl"]) for m in snap["mon"])

	co_gia = {"mon": [{"ma": "B1", "sl": 1, "gia": 450000}, {"ma": "BAPK00002", "sl": 1, "gia": 15000},
		{"ma": "BAPK00020", "sl": 3, "gia": 2000}, {"ma": "BAPK00018", "sl": 3, "gia": 0}],
		"chiec": [{"ma": "B1", "ten": "Epi", "co": True, "loi_chuc": "Hi", "thiep": "ep_kim", "loi_thiep": ""}]}
	d = b.dong_don(co_gia)
	la("đủ 465.000 đ cộng 6.000 đ dĩa", cong(d), tien(co_gia))
	la("dĩa có giá là dòng có giá, nĩa miễn phí là tặng kèm", [(x["loai"], x.get("ma")) for x in d],
		[("banh", "B1"), ("them", "BAPK00002"), ("them", "BAPK00020"), ("tang", None)])
	mien = {"mon": [{"ma": "B1", "sl": 2, "gia": 450000}, {"ma": "BAPK00002", "sl": 1, "gia": 0}],
		"chiec": [{"ma": "B1", "ten": "Epi", "co": True, "thiep": "ep_kim"}, {"ma": "B1", "ten": "Epi", "co": False}]}
	d2 = b.dong_don(mien)
	la("thiệp miễn phí: không dòng riêng, vẫn khớp", ([x["loai"] for x in d2], cong(d2)), (["banh"], tien(mien)))
