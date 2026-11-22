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


@ca("v684 thẻ ĐƠN HÀNG: tên web lúc đặt (không tên nội bộ), cờ và thiệp từng chiếc, thiệp ép kim không thành dòng riêng, mua thêm có giá, dĩa nĩa gộp một dòng tặng kèm")
def _():
	from vagabond import bien_nhan_web as b
	d = b.dong_don(SNAP)
	la("loại dòng", [x["loai"] for x in d], ["banh", "them", "tang"])
	la("bánh", (d[0]["ten"], d[0]["sl"], d[0]["gia"]), ("Epi · Ø 12cm", 2, "900.000 đ"))
	la("từng chiếc", d[0]["chiec"], [
		{"co": "Cờ: “Happy 30”", "thiep": "Thiệp ép kim", "loi_thiep": "Thương em"},
		{"co": "Không cờ", "thiep": "Không thiệp", "loi_thiep": ""}])
	la("mua thêm", (d[1]["ten"], d[1]["gia"]), ("Nến số 3", "10.000 đ"))
	la("tặng kèm", (d[2]["ten"], d[2]["gia"]), ("Dĩa giấy bã mía x5, nĩa gỗ x5", "tặng kèm"))
	chi_nia = b.dong_don({"mon": [{"ma": "BAPK00018", "sl": 2, "gia": 0}, {"ma": "X", "sl": 1, "gia": 1}]})
	la("chỉ có nĩa", chi_nia[-1]["ten"], "Nĩa gỗ x2")
	cu = b.dong_don({"mon": SNAP["mon"][:2]})
	la("đơn cũ không ghi từng chiếc: giữ dòng thiệp ép kim", [x["ten"] for x in cu], ["Bánh Ổ OBON, size 12cm", "Thiệp ép kim"])
	la("chọn cờ mà để trống lời chúc", b._chiec({"co": True, "loi_chuc": " ", "thiep": "nho"})["co"], "Cờ chưa ghi lời chúc")


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
