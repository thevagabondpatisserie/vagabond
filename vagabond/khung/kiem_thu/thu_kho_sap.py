# -*- coding: utf-8 -*-
"""Ca kiểm năm nút kho học từ SAP (anh Việt duyệt 03/09/2026).

Toàn phép thuần trong `kho_sap.py`, không cần Frappe. Ca kiểm ở đây giữ đúng
những chỗ dễ trượt nhất: dung sai tính trên số ĐẶT chứ không phải số còn lại,
đếm mù chỉ mù với người đếm, và lý do chênh lệch phải đúng chiều.
"""

import datetime
import io
import os

from vagabond import kho_sap
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _ngay(s):
	return datetime.date(*[int(x) for x in s.split("-")])


def _doc(duong):
	goc = os.path.dirname(os.path.dirname(os.path.abspath(kho_sap.__file__)))
	return io.open(os.path.join(goc, duong), encoding="utf-8").read()


@ca("kho SAP: dung sai đọc số người dùng gõ về khoảng cho phép")
def _chuan():
	la("để trống thì lấy mặc định", kho_sap.chuan_dung_sai(None), 5.0)
	la("chữ không phải số thì lấy mặc định", kho_sap.chuan_dung_sai("nhiều"), 5.0)
	la("số âm về 0", kho_sap.chuan_dung_sai(-3), 0.0)
	la("vượt trần thì về trần", kho_sap.chuan_dung_sai(90), 20.0)
	la("số thường giữ nguyên", kho_sap.chuan_dung_sai("7.5"), 7.5)


@ca("kho SAP: nhận dư trong dung sai thì cho, quá thì chặn")
def _thua():
	# Dat 100, da nhan 90, con 10. Dung sai 5% cua 100 = 5.
	trong = kho_sap.soat_nhan_thua(100, 90, 13)
	la("dư 3 là trong dung sai", (trong["qua"], trong["trong_dung_sai"]), (1, 1))
	la("nói đúng số dư", trong["du"], 3.0)
	qua = kho_sap.soat_nhan_thua(100, 90, 20)
	la("dư 10 là quá", (qua["qua"], qua["trong_dung_sai"]), (1, 0))
	vua = kho_sap.soat_nhan_thua(100, 90, 10)
	la("nhận đúng phần còn lại thì không có gì để nói", vua["qua"], 0)
	sat = kho_sap.soat_nhan_thua(100, 90, 15)
	la("dư đúng bằng trần vẫn cho", (sat["qua"], sat["trong_dung_sai"]), (1, 1))


@ca("kho SAP: dung sai tính trên số ĐẶT, không phải trên phần còn lại")
def _tinh_tren_dat():
	# Cho nay de viet sai nhat. Dat 100 nhan lam 10 dot, con lai 1: neu tinh
	# 5% cua phan con lai thi tran chi con 0,05 - nhan du 1 hop cung chan.
	kq = kho_sap.soat_nhan_thua(100, 99, 3)
	la("trần vẫn là 5 của số đặt", kq["tran"], 5.0)
	la("dư 2 vẫn trong dung sai", kq["trong_dung_sai"], 1)


@ca("kho SAP: giao thiếu ít thì đóng đơn được")
def _thieu():
	la("thiếu 3 trên 100 thì đóng được", kho_sap.thieu_dong_duoc(100, 97), 1)
	la("thiếu 30 trên 100 thì không", kho_sap.thieu_dong_duoc(100, 70), 0)
	la("nhận đủ rồi thì không hỏi nữa", kho_sap.thieu_dong_duoc(100, 100), 0)
	la("nhận dư rồi cũng không hỏi", kho_sap.thieu_dong_duoc(100, 103), 0)


@ca("kho SAP: câu nói khi nhận dư nói đủ số và mức trần")
def _cau_thua():
	c1 = kho_sap.cau_nhan_thua("Bơ lạt", kho_sap.soat_nhan_thua(100, 90, 13), "kg")
	dung("nói là còn trong dung sai", "trong dung sai" in c1)
	dung("có tên món", "Bơ lạt" in c1)
	c2 = kho_sap.cau_nhan_thua("Bơ lạt", kho_sap.soat_nhan_thua(100, 90, 20), "kg")
	dung("nói vượt mức cho phép", "vượt mức cho phép" in c2)
	dung("nói rõ trần", "5 kg" in c2)
	la("không dư thì không nói gì", kho_sap.cau_nhan_thua("X", kho_sap.soat_nhan_thua(10, 0, 5)), "")


@ca("kho SAP: hạn dùng tối thiểu theo món")
def _hsd():
	hn = _ngay("2026-09-03")
	dat = kho_sap.soat_han_dung(_ngay("2026-10-20"), hn, 30)
	la("còn 47 ngày là đạt", (dat["dat"], dat["con"]), (1, 47))
	thieu = kho_sap.soat_han_dung(_ngay("2026-09-20"), hn, 30)
	la("còn 17 ngày là không đạt", thieu["dat"], 0)
	qua = kho_sap.soat_han_dung(_ngay("2026-09-01"), hn, 30)
	la("quá hạn thì không đạt", (qua["dat"], qua["con"]), (0, -2))
	khong = kho_sap.soat_han_dung(None, hn, 30)
	la("không khai hạn thì không kết luận", (khong["co_han"], khong["dat"]), (0, 1))
	khong_soi = kho_sap.soat_han_dung(_ngay("2026-09-04"), hn, 0)
	la("món không đặt mức tối thiểu thì cho qua", khong_soi["dat"], 1)


@ca("kho SAP: món theo lô thì bắt buộc khai hạn dùng")
def _bat_hsd():
	la("theo lô là bắt buộc", kho_sap.bat_buoc_han_dung(1), 1)
	la("không theo lô nhưng có mức tối thiểu cũng bắt buộc", kho_sap.bat_buoc_han_dung(0, 30), 1)
	la("không lô không mức thì thôi", kho_sap.bat_buoc_han_dung(0, 0), 0)
	c = kho_sap.cau_han_dung("Bơ lạt", kho_sap.soat_han_dung(_ngay("2026-09-20"), _ngay("2026-09-03"), 30))
	dung("câu nói đủ hai con số", "17 ngày" in c and "30 ngày" in c)


@ca("kho SAP: khoá mã đang kiểm kê")
def _khoa():
	phieu = [
		{"kho": "Kho D1", "trang_thai": "Đang kiểm", "ma": ["BOLAT", "SUA"]},
		{"kho": "Kho Lab", "trang_thai": "Đã ghi sổ", "ma": ["BOLAT"]},
		{"kho": "Kho D1", "trang_thai": "Đã chốt", "ma": ["DUONG"]},
	]
	khoa = kho_sap.khoa_dang_kiem(phieu)
	dung("mã đang kiểm bị khoá", ("Kho D1", "BOLAT") in khoa)
	dung("phiếu đã ghi sổ không khoá nữa", ("Kho Lab", "BOLAT") not in khoa)
	dung("đã chốt vẫn khoá vì còn chờ ghi sổ chênh lệch", ("Kho D1", "DUONG") in khoa)
	la("đúng ba mã bị khoá", len(khoa), 3)

	vuong = kho_sap.dong_bi_khoa(
		[
			{"ma": "BOLAT", "kho": ["Kho D1"]},
			{"ma": "BOLAT", "kho": ["Kho Lab"]},
			{"ma": "MUOI", "kho": ["Kho D1"]},
			{"ma": "DUONG", "kho": ["Kho Lab", "Kho D1"]},
		],
		khoa,
	)
	la("hai dòng vướng", len(vuong), 2)
	dung("dòng điều chuyển soi cả hai kho", any(v["ma"] == "DUONG" for v in vuong))
	c = kho_sap.cau_bi_khoa(vuong, {"BOLAT": "Bơ lạt"})
	dung("câu chặn gọi tên món", "Bơ lạt" in c)
	dung("câu chặn nói phải làm gì", "ghi sổ chênh lệch" in c)


@ca("kho SAP: phiếu kiểm bỏ quên thì hết quyền khoá")
def _het_han_khoa():
	hn = _ngay("2026-09-03")
	la("phiếu hôm nay còn khoá", kho_sap.con_hieu_luc_khoa(_ngay("2026-09-03"), hn), 1)
	la("phiếu hôm kia vẫn còn", kho_sap.con_hieu_luc_khoa(_ngay("2026-09-01"), hn), 1)
	la("phiếu bốn ngày trước thì thôi", kho_sap.con_hieu_luc_khoa(_ngay("2026-08-30"), hn), 0)
	khoa = kho_sap.khoa_dang_kiem([
		{"kho": "K", "trang_thai": "Đang kiểm", "ma": ["A"], "con_hieu_luc": 0},
		{"kho": "K", "trang_thai": "Đang kiểm", "ma": ["B"], "con_hieu_luc": 1},
	])
	dung("phiếu hết hiệu lực không khoá nữa", ("K", "A") not in khoa)
	dung("phiếu còn hiệu lực vẫn khoá", ("K", "B") in khoa)


@ca("kho SAP: đếm mù chỉ mù với người đếm")
def _dem_mu():
	la("người đếm khi đang kiểm thì không thấy", kho_sap.duoc_thay_ton_so("Đang kiểm", False), 0)
	la("quản lý thì thấy", kho_sap.duoc_thay_ton_so("Đang kiểm", True), 1)
	la("chốt xong ai cũng thấy", kho_sap.duoc_thay_ton_so("Chờ duyệt", False), 1)
	dong = [{"ma": "BOLAT", "ton_he_thong": 12, "lech": 2, "so_luong": 14}]
	che = kho_sap.che_ton_so(dong, 0)
	la("che thì bỏ tồn sổ", che[0]["ton_he_thong"], None)
	la("che thì bỏ luôn cột lệch", che[0]["lech"], None)
	la("số đếm được thì giữ nguyên", che[0]["so_luong"], 14)
	la("có cờ để màn hình biết mà nói", che[0]["dem_mu"], 1)
	la("không che thì giữ nguyên bảng", kho_sap.che_ton_so(dong, 1)[0]["ton_he_thong"], 12)


@ca("kho SAP: lý do chênh lệch phải đúng chiều")
def _ly_do():
	dung("thiếu thì có hao hụt", any(x["ma"] == "hao_hut" for x in kho_sap.ly_do_hop(-1)))
	dung("thiếu thì KHÔNG có nhập quên phiếu", all(x["ma"] != "quen_phieu_nhap" for x in kho_sap.ly_do_hop(-1)))
	dung("thừa thì có nhập quên phiếu", any(x["ma"] == "quen_phieu_nhap" for x in kho_sap.ly_do_hop(1)))
	dung("thừa thì KHÔNG có hao hụt", all(x["ma"] != "hao_hut" for x in kho_sap.ly_do_hop(1)))
	dung("lệch đơn vị dùng được cả hai chiều", any(x["ma"] == "lech_don_vi" for x in kho_sap.ly_do_hop(1)))
	dung("mỗi lý do có tài khoản", all(x.get("tk") for x in kho_sap.LY_DO_LECH))


@ca("kho SAP: soát lý do trước khi ghi sổ chênh lệch")
def _soat():
	kq = kho_sap.soat_ly_do([
		{"ma": "A", "ten": "Bơ", "lech": -2, "ly_do": ""},
		{"ma": "B", "ten": "Sữa", "lech": 0, "ly_do": ""},
		{"ma": "C", "ten": "Đường", "lech": 3, "ly_do": "hao_hut"},
		{"ma": "D", "ten": "Muối", "lech": -1, "ly_do": "hao_hut"},
	])
	la("một dòng thiếu lý do", kq["thieu"], ["Bơ"])
	la("dòng khớp không bị hỏi", "Sữa" not in kq["thieu"], True)
	la("một dòng ngược chiều", len(kq["nguoc"]), 1)
	dung("nói rõ dòng nào ngược", "Đường" in kq["nguoc"][0])
	la("lý do lạ tính là chưa khai", kho_sap.soat_ly_do([{"ten": "X", "lech": 1, "ly_do": "abc"}])["thieu"], ["X"])


@ca("kho SAP: mất hàng thì giám đốc duyệt, và gom được theo lý do")
def _duyet_va_gom():
	la("có dòng mất là cần duyệt", kho_sap.can_giam_doc_duyet([{"lech": -2, "ly_do": "mat"}]), 1)
	la("mất mà lệch bằng 0 thì thôi", kho_sap.can_giam_doc_duyet([{"lech": 0, "ly_do": "mat"}]), 0)
	la("hao hụt thì không cần", kho_sap.can_giam_doc_duyet([{"lech": -2, "ly_do": "hao_hut"}]), 0)
	gom = kho_sap.gom_theo_ly_do([
		{"lech": -2, "ly_do": "hao_hut", "gia": 100},
		{"lech": -1, "ly_do": "hao_hut", "gia": 50},
		{"lech": 3, "ly_do": "quen_phieu_nhap", "gia": 10},
		{"lech": 0, "ly_do": "mat", "gia": 999},
	])
	la("hai lý do có mặt", sorted(gom.keys()), ["hao_hut", "quen_phieu_nhap"])
	la("gom đúng số dòng", gom["hao_hut"]["so_dong"], 2)
	la("gom đúng tiền", gom["hao_hut"]["tien"], -250.0)


@ca("kho SAP: năm nút được nối vào đúng chỗ trong hệ")
def _noi_vao_he():
	h = _doc("vagabond/hooks.py")
	dung(
		"phiếu xuất nhập nội bộ chịu khoá khi đang kiểm",
		'"Stock Entry": {' in h and "vagabond.kiem_ke.chan_khi_dang_kiem" in h,
	)
	la(
		"khoá đặt ở hai đường chứng từ kho",
		h.count("vagabond.kiem_ke.chan_khi_dang_kiem"),
		2,
	)
	dung("chốt phiếu thì soát lý do", "vagabond.kiem_ke.soat_truoc_khi_chot" in h)
	dung("phiếu sinh ra là chụp tồn sổ", "vagabond.kiem_ke.chup_ton_so" in h)
	# Duong ban hang KHONG bi chan: chan giua gio la ca quay dung ban.
	dung(
		"không khoá đường bán hàng",
		'"Sales Invoice": {"before_submit": "vagabond.kiem_ke.chan_khi_dang_kiem"' not in h,
	)


@ca("kho SAP: nhận hàng gọi xuống phép thuần chứ không tự tính lại")
def _nhan_hang_goi():
	n = _doc("vagabond/nhan_hang.py")
	dung("dung sai đi qua phép thuần", "kho_sap.soat_nhan_thua(" in n)
	dung("hạn dùng đi qua phép thuần", "kho_sap.soat_han_dung(" in n)
	dung("bắt buộc hạn dùng đi qua phép thuần", "kho_sap.bat_buoc_han_dung(" in n)
	dung("ngưỡng đọc từ Cài đặt", "kho_cai_dat.doc()" in n)
	dung("mức tối thiểu đọc theo món", "kho_cai_dat.hsd_toi_thieu_cua(" in n)
	# Cau chan cu chan thang moi khoan du, khong con dung nua.
	dung("không còn câu chặn cứng cũ", "Nhập quá số còn phải nhận" not in n)
	dung("nhận dư trong dung sai để lại vết", "Nhận dư trong dung sai" in n)


@ca("kho SAP: màn kiểm kê đọc qua cửa che tồn sổ")
def _kiem_ke_goi():
	k = _doc("vagabond/kiem_ke.py")
	dung("có cửa mở phiếu riêng", "def mo_phieu(" in k)
	dung("che tồn sổ đi qua phép thuần", "kho_sap.che_ton_so(" in k)
	dung("quyền xem đi qua phép thuần", "kho_sap.duoc_thay_ton_so(" in k)
	dung("khoá mã đi qua phép thuần", "kho_sap.khoa_dang_kiem(" in k)
	dung("soát lý do đi qua phép thuần", "kho_sap.soat_ly_do(" in k)
	dung("hàng rào khoá không được kéo đổ cả hệ", "frappe.log_error" in k)
	# Nguoi dem dang mu thi khong duoc bat ho khai ly do.
	than = k[k.index("def soat_truoc_khi_chot("):k.index("def chup_ton_so(")]
	dung("không chặn người đếm ở bước chốt", '"Chờ duyệt"' not in than)
	dung("chặn ở bước ghi sổ của quản lý", '"Đã ghi sổ"' in than)
	t = _doc("vagabond/truong_tu_them.py")
	for nhom in ("kiem_ke.TRUONG_MOI", "kho_cai_dat.TRUONG_MOI"):
		dung("%s được dựng lại mỗi lần deploy" % nhom, nhom in t)
