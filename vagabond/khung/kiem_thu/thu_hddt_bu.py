# -*- coding: utf-8 -*-
"""Phát hành hoá đơn điện tử theo lô và lưới đỡ mỗi giờ (v392).

Anh Việt 03/09/2026, kèm ba ảnh màn Hoá đơn hôm nay TCV:

    *"Quá tệ hại. Những đơn hàng đã ghi sổ thì lại không xuất hoá đơn (ngày
    1/9, ngày 2/9), rồi lại có những hoá đơn không tự ghi sổ để xuất hoá
    đơn dù anh đã bật chức năng ghi sổ tự động và xuất hoá đơn với em cho
    bên điểm bán TCV."*

Chuyện thật: chuỗi cuối ngày làm mọi việc trong MỘT lượt chạy nền, hàng đợi
mặc định cắt ở 300 giây. Kéo Pancake 3 phút, ghi sổ 1 phút, còn hơn một
phút cho 140 tờ hoá đơn. 01/09 cắt sau 90 tờ, 02/09 cắt sau 99 tờ. Ba lớp
đáng lẽ phải kêu đều im: nhịp bù mỗi giờ bị công tắc khác tắt từ 11/08,
nhịp vét bỏ qua bước phát hành, nhật ký bị vét ghi đè thành "xuất hoá đơn
0". Và khi bù, m-invoice từ chối tờ ngày 01/09 vì số đã nhảy sang 02/09.

Ca kiểm ở đây chốt: phép chọn ngày còn mở cửa, luật dừng lô, cách gộp kết
quả, nhịp vét không ghi đè khi không làm gì, và soi chuỗi mã nguồn để bảo
đảm phát hành đã đi hàng đợi dài, nhịp bù đi cùng đường, chuông 23h55 đã
khai vào bộ lập lịch. Toàn phép thuần và soi chuỗi, không cần Frappe.
"""

import datetime
import io
import os

from vagabond import hddt_bu
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	return os.path.dirname(os.path.dirname(os.path.abspath(hddt_bu.__file__)))


def _py(ten):
	return io.open(os.path.join(_goc(), "vagabond", ten), encoding="utf-8").read()


def _js(ten):
	return io.open(
		os.path.join(_goc(), "vagabond", "public", "js", "bep", ten), encoding="utf-8"
	).read()


def _than(s, ten_ham):
	i = s.find("def %s(" % ten_ham)
	dung("có hàm " + ten_ham, i >= 0)
	j = s.find("\ndef ", i + 10)
	return s[i:j if j > 0 else len(s)]


D = datetime.date

# ------------------------------------------------------ ngày còn mở cửa


@ca("ngày được bù: hôm qua và hôm nay khi chuỗi đã chạy, số mới nhất còn ở hôm qua")
def _bu_ca_hai():
	ra = hddt_bu.ngay_duoc_bu(D(2026, 9, 3), D(2026, 9, 2), True)
	la("hai ngày, cũ trước", ra, [D(2026, 9, 2), D(2026, 9, 3)])


@ca("ngày được bù: đã có số mang hôm nay thì hôm qua đóng cửa")
def _bu_dong_hom_qua():
	ra = hddt_bu.ngay_duoc_bu(D(2026, 9, 3), D(2026, 9, 3), True)
	la("chỉ còn hôm nay", ra, [D(2026, 9, 3)])


@ca("ngày được bù: chuỗi hôm nay chưa chạy thì không đụng bill hôm nay")
def _bu_cho_chuoi():
	ra = hddt_bu.ngay_duoc_bu(D(2026, 9, 3), D(2026, 9, 2), False)
	la("chỉ hôm qua", ra, [D(2026, 9, 2)])
	ra = hddt_bu.ngay_duoc_bu(D(2026, 9, 3), D(2026, 9, 3), False)
	la("không ngày nào", ra, [])


@ca("ngày được bù: chưa có tờ nào thì cả hai ngày đều mở")
def _bu_chua_co_so():
	ra = hddt_bu.ngay_duoc_bu("2026-09-03", None, True)
	la("hai ngày", ra, [D(2026, 9, 2), D(2026, 9, 3)])
	ra = hddt_bu.ngay_duoc_bu("2026-09-03", "", True)
	la("chuỗi rỗng coi như chưa có", ra, [D(2026, 9, 2), D(2026, 9, 3)])


@ca("ngày được bù: ca thật 03/09, số 11876 mang ngày 02/09 nên 01/09 không được thử")
def _bu_ca_that():
	ra = hddt_bu.ngay_duoc_bu(D(2026, 9, 3), datetime.datetime(2026, 9, 2, 10, 50), False)
	la("chỉ 02/09", ra, [D(2026, 9, 2)])


# ------------------------------------------------------------- luật dừng lô


@ca("dừng lô: hết tờ thì dừng, còn tờ và có tạo thì tiếp")
def _lo_tiep():
	dung("còn tờ, có tạo: tiếp", hddt_bu.con_goi_lo_tiep({"tim_thay": 20, "tao_ok": 20}, 1, 40))
	dung("hết tờ: dừng", not hddt_bu.con_goi_lo_tiep({"tim_thay": 0, "tao_ok": 0}, 1, 40))


@ca("dừng lô: lô không tạo được tờ nào thì dừng, không lặp lại lỗi")
def _lo_loi():
	dung("toàn lỗi: dừng", not hddt_bu.con_goi_lo_tiep({"tim_thay": 15, "tao_ok": 0, "loi": ["x"]}, 1, 40))


@ca("dừng lô: đủ số lô tối đa thì dừng dù còn tờ")
def _lo_tran():
	dung("lô 40/40: dừng", not hddt_bu.con_goi_lo_tiep({"tim_thay": 5, "tao_ok": 5}, 40, 40))
	dung("kết quả lạ: dừng", not hddt_bu.con_goi_lo_tiep(None, 1, 40))


@ca("dừng lô ký: cùng luật với phát hành")
def _lo_ky():
	dung("còn tờ, có ký: tiếp", hddt_bu.con_ky_lo_tiep({"can_ky": 10, "da_ky": 10}, 1, 40))
	dung("không ký được: dừng", not hddt_bu.con_ky_lo_tiep({"can_ky": 10, "da_ky": 0}, 1, 40))
	dung("hết: dừng", not hddt_bu.con_ky_lo_tiep({"can_ky": 0, "da_ky": 0}, 1, 40))


# ------------------------------------------------------------ gộp kết quả


@ca("gộp lô: tìm thấy lấy lô đầu, tạo cộng dồn, lỗi bỏ trùng")
def _gop():
	kq = hddt_bu.gom_lo([
		{"tim_thay": 48, "tao_ok": 20, "loi": []},
		{"tim_thay": 28, "tao_ok": 20, "loi": ["A: 296"]},
		{"tim_thay": 8, "tao_ok": 7, "loi": ["A: 296", "B: mạng"]},
	])
	la("tìm thấy 48", kq["tim_thay"], 48)
	la("tạo 47", kq["tao_ok"], 47)
	la("lỗi hai dòng", kq["loi"], ["A: 296", "B: mạng"])


@ca("gộp lô: rỗng hay phần tử lạ không nổ")
def _gop_rong():
	la("rỗng", hddt_bu.gom_lo([]), {"tim_thay": 0, "tao_ok": 0, "loi": []})
	la("lạ", hddt_bu.gom_lo([None, "x"]), {"tim_thay": 0, "tao_ok": 0, "loi": []})
	la("ký rỗng", hddt_bu.gom_ky(None), {"can_ky": 0, "da_ky": 0, "loi": []})


@ca("nhật ký chuỗi: nêu đủ ghi sổ, phát hành, ký, và số đơn cần xem")
def _nhat_ky():
	s = hddt_bu.dong_nhat_ky(
		"2026-09-03", "23:09", 52,
		{"tim_thay": 148, "tao_ok": 148, "loi": []},
		{"can_ky": 148, "da_ky": 148, "loi": []}, 0,
	)
	la("câu đủ", s, "2026-09-03 lúc 23:09: ghi sổ 52 đơn. Phát hành 148/148 tờ. Ký 148/148 tờ.")
	s = hddt_bu.dong_nhat_ky("2026-09-03", "23:09", 52, "bỏ qua (tắt ở m-invoice)", None, 2)
	dung("bỏ qua ghi rõ", "Phát hành bỏ qua (tắt ở m-invoice)" in s)
	dung("ký không rõ", "Ký không rõ." in s)
	dung("đuôi cần xem", s.endswith(" Còn 2 đơn cần xem lại."))
	dung("không dấu gạch dài", "\u2013" not in s and "\u2014" not in s)


@ca("nhịp vét: không làm gì thì không ghi đè nhật ký")
def _vet_im():
	dung("0/0/0 im", not hddt_bu.vet_co_gi_de_ghi(0, 0, 0))
	dung("ghi sổ thêm thì ghi", hddt_bu.vet_co_gi_de_ghi(1, 0, 0))
	dung("có lỗi thì ghi", hddt_bu.vet_co_gi_de_ghi(0, 0, 1))


@ca("câu cảnh báo sót: có ngày, số tờ, tiền có dấu chấm nghìn")
def _cau_sot():
	s = hddt_bu.cau_canh_bao_sot("2026-09-02", 49, 14048891)
	la("câu", s, "CẢNH BÁO: ngày 2026-09-02 còn 49 hoá đơn đã ghi sổ mà chưa có hoá đơn điện tử, tổng 14.048.891 đ.")


# -------------------------------------------------------- soi mã nguồn thật


@ca("chuỗi cuối ngày: phát hành và ký đã đi hàng đợi dài, không còn gọi thẳng")
def _chuoi_hang_doi():
	s = _py("ban_hang.py")
	than = _than(s, "tu_ghi_so_cuoi_ngay")
	dung("đẩy sang hàng đợi long", 'queue="long"' in than and "phat_hanh_cuoi_ngay" in than)
	dung("một giờ, không phải 300 giây", "timeout=3600" in than)
	dung("chống đẩy trùng", "deduplicate=True" in than)
	dung("không còn gọi phát hành thẳng trong luồng 300 giây",
		'"MInvoice - Phat hanh HD Sales (API)"' not in than)
	dung("nhịp vét im khi không có gì", "vet_co_gi_de_ghi" in than)


@ca("lượt phát hành: theo lô, có khoá, một công tắc m-invoice")
def _luot_phat_hanh():
	s = _py("ban_hang.py")
	than = _than(s, "phat_hanh_cuoi_ngay")
	dung("lấy khoá", "_khoa_hddt(" in than)
	dung("một công tắc", "_cong_tac_minvoice()" in than)
	dung("nhả khoá trong finally", "finally:" in than and "_mo_khoa_dong_bo(khoa)" in than)
	lo = _than(s, "_phat_hanh_theo_lo")
	dung("gọi kịch bản m-invoice theo lô", '"so_luong": moi_lo' in lo)
	dung("luật dừng nằm bên phép thuần", "hddt_bu.con_goi_lo_tiep" in lo)
	dung("khoá riêng, không dùng chung khoá đơn Sales",
		'KHOA_HDDT = "vgb_phat_hanh_hddt"' in s)


@ca("nhịp bù mỗi giờ: đi cùng đường kịch bản m-invoice, chỉ ngày còn mở cửa")
def _nhip_bu():
	s = _py("ban_hang.py")
	than = _than(s, "xuat_hddt_con_thieu_tu_dong")
	dung("không còn đi đường Python cũ", "_xuat_hddt_con_thieu(" not in than)
	dung("không còn lệ thuộc công tắc tu_xuat_hddt", "tu_xuat_hddt" not in than)
	dung("chọn ngày bằng phép thuần", "hddt_bu.ngay_duoc_bu(" in than)
	dung("đọc ngày của số mới nhất", "_ngay_so_hddt_moi_nhat()" in than)
	dung("chờ chuỗi hôm nay", "tu_ghi_so_lan_cuoi" in than)
	dung("cùng khoá với lượt cuối ngày", "_khoa_hddt(" in than)
	dung("phát hành theo lô", "_phat_hanh_theo_lo(" in than)
	moi = _than(s, "_ngay_so_hddt_moi_nhat")
	dung("so số theo giá trị số, không theo chuỗi", "cast(custom_hddt_so as unsigned)" in moi)


@ca("chuông 23h55: đếm bằng chính bộ lọc kịch bản, đã khai vào bộ lập lịch")
def _chuong():
	s = _py("ban_hang.py")
	than = _than(s, "canh_bao_hddt_sot")
	dung("đếm tờ sót", "_dem_hddt_sot(" in than)
	dung("ghi cảnh báo vào nhật ký", "tu_ghi_so_nhat_ky" in than)
	dung("gửi thư kế toán", "frappe.sendmail(" in than)
	dem = _than(s, "_dem_hddt_sot")
	dung("đếm bằng chế độ thử của kịch bản", '"che_do": "thu"' in dem)
	h = _py("hooks.py")
	i = h.find('"55 23 * * *"')
	dung("có nhịp 23h55", i >= 0)
	khoi = h[i:h.find("]", i)]
	dung("chuông đơn treo còn nguyên", "vagabond.ban_hang.canh_bao_don_treo" in khoi)
	dung("chuông tờ sót đã khai", "vagabond.ban_hang.canh_bao_hddt_sot" in khoi)
	dung("nhịp bù mỗi giờ còn nguyên",
		'"15 * * * *": ["vagabond.ban_hang.xuat_hddt_con_thieu_tu_dong"]' in h)


@ca("màn Cài đặt: nhật ký có CẢNH BÁO thì tô đỏ")
def _man_cai_dat():
	j = _js("17-cai-dat.js")
	dung("bắt chữ CẢNH BÁO", "indexOf('CẢNH BÁO')" in j)
	dung("nền đỏ", "#fef2f2" in j and "#991b1b" in j)


@ca("mô đun thuần không kéo Frappe hay mạng")
def _thuan():
	s = _py("hddt_bu.py")
	dung("không import frappe", "import frappe" not in s)
	dung("không import requests", "import requests" not in s)
