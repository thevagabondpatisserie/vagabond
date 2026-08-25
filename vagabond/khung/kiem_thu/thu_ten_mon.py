"""Ca kiểm cho phép cắt quy cách đóng gói ra khỏi tên món.

Toàn phép thuần, chạy được không cần Frappe, không cần site.

Số liệu trong các ca dưới đây lấy nguyên từ danh mục thật ngày 25/08/2026,
để nếu sau này ai sửa luật cắt thì tên thật sẽ tố cáo ngay.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _thuan(tep, ten_hien):
	ma = io.open(os.path.join(GOI, tep), encoding="utf-8").read()
	moc = "# ------------------------------------------------------- phan can Frappe"
	assert moc in ma, "%s doi cau truc, khong tim thay moc phan thuan" % ten_hien
	ns = {}
	exec(compile(ma.split(moc)[0], ten_hien, "exec"), ns)
	return ns


T = _thuan("ten_mon.py", "ten_mon_thuan")


@ca("ten mon: cat dung doan quy cach, giu nguyen phan con lai")
def _cat_dung():
	moi, cat = T["cat_quy_cach"]("Bột mì Baker Choice số 8, Bao 25 kg, Interflour")
	la("ten moi", moi, "Bột mì Baker Choice số 8, Interflour")
	la("doan cat", cat, ["Bao 25 kg"])
	moi2, cat2 = T["cat_quy_cach"]("Bơ lạt Avonmore,Unsalted Butter, Khối 2,5kg, Ireland")
	la("bo lat", moi2, "Bơ lạt Avonmore, Unsalted Butter, Ireland")
	la("bo lat doan cat", cat2, ["Khối 2,5kg"])


@ca("ten mon: dau phay thap phan khong lam vo doan quy cach")
def _dau_phay_thap_phan():
	# Bay that: "Can 3,5 kg" tach theo dau phay ra "Can 3" va "5 kg". Neu
	# khong gom lai thi ten moi con sot chu "5 kg" nam tro tro.
	moi, cat = T["cat_quy_cach"]("Nước Rửa Chén Bát Thiên Nhiên Lô Hội, Can 3,5 kg, Sunlight")
	la("ten moi", moi, "Nước Rửa Chén Bát Thiên Nhiên Lô Hội, Sunlight")
	la("doan cat nguyen ven", cat, ["Can 3,5 kg"])
	la("gom lai dung", T["gom_dau_phay_thap_phan"](["Can 3", "5 kg", "Sunlight"]),
		["Can 3,5 kg", "Sunlight"])


@ca("ten mon: doan DAU TIEN khong bao gio bi cat")
def _doan_dau_giu():
	# Ten goc cua mon nam o doan dau. Cat no la mat luon mon.
	moi, cat = T["cat_quy_cach"]("Túi 100 cái, The Minhs")
	la("giu nguyen doan dau", moi, "Túi 100 cái, The Minhs")
	la("khong cat gi", cat, [])


@ca("ten mon: khong co doan quy cach thi tra ten nguyen ven")
def _khong_co_gi_cat():
	moi, cat = T["cat_quy_cach"]("Whipping cream, Lescure UHT")
	la("nguyen ven", moi, "Whipping cream, Lescure UHT")
	la("rong", cat, [])
	la("ten mot doan", T["cat_quy_cach"]("Muối hạt")[0], "Muối hạt")
	la("ten rong", T["cat_quy_cach"]("")[0], "")
	la("ten None", T["cat_quy_cach"](None)[0], "")


@ca("ten mon: nhom hang ban ra KHONG duoc dung toi")
def _nhom_ban_ra():
	# Ben ban ra thi con so chinh la san pham. Anh Viet chot 05/08/2026.
	dung("banh khong cat", not T["duoc_cat_nhom"]("Bánh Ổ"))
	dung("nuoc khong cat", not T["duoc_cat_nhom"]("Bán thành phẩm Nước"))
	dung("tra khong cat", not T["duoc_cat_nhom"]("Trà"))
	dung("ca phe khong cat", not T["duoc_cat_nhom"]("Cà phê"))
	dung("qua tang khong cat", not T["duoc_cat_nhom"]("Hộp quà"))
	dung("nguyen vat lieu cat duoc", T["duoc_cat_nhom"]("Nguyên vật liệu Thô"))
	dung("cong cu dung cu cat duoc", T["duoc_cat_nhom"]("Công cụ Dụng cụ"))


@ca("ten mon: doc so va danh tu bao bi trong doan quy cach")
def _doc_so_danh_tu():
	la("so nguyen", T["doc_so"]("Bao 25 kg"), 25.0)
	la("so thap phan dau phay", T["doc_so"]("Khối 2,5kg"), 2.5)
	la("so thap phan dau cham", T["doc_so"]("Túi 4.1kg"), 4.1)
	la("danh tu", T["doc_danh_tu"]("Thùng 2000 cái"), "Thùng")
	la("danh tu hai chu", T["doc_danh_tu"]("Túi 500 gr"), "Túi")


@ca("ten mon: quy doan quy cach ra don vi kho")
def _quy_ra_goc():
	la("kg ra gram", T["quy_ra_don_vi_goc"]("Bao 25 kg"), 25000.0)
	la("lit ra ml", T["quy_ra_don_vi_goc"]("Chai 1 lít"), 1000.0)
	la("gram giu nguyen", T["quy_ra_don_vi_goc"]("Túi 500 gr"), 500.0)
	la("ml giu nguyen", T["quy_ra_don_vi_goc"]("Chai 880ml"), 880.0)
	# "Tui 100 cai" thi 100 cai bang bao nhieu gram khong ai biet.
	la("dem cai thi ra chinh no", T["quy_ra_don_vi_goc"]("Túi 100 cái"), 100.0)
	la("khong co so", T["quy_ra_don_vi_goc"]("Túi"), None)


@ca("ten mon: xep dung ba muc an toan")
def _ba_muc():
	# A: don vi co trong bang quy doi va he so khop.
	la("muc A", T["muc_an_toan"]("Bao 25 kg", {"Gram": 1, "Bao": 25000}), "A")
	# B: don vi co nhung he so lech. Ca that NVLT00350 Bot Lion Custard:
	# ten ghi "Lon 3,5 kg" tuc 3.500 gram, bang quy doi ghi 35.000, sai
	# gap muoi lan.
	la("muc B he so lech", T["muc_an_toan"]("Lon 3,5 kg",
		{"Gram": 1, "Lon": 35000}), "B")
	# C: chua co don vi do trong bang quy doi.
	la("muc C", T["muc_an_toan"]("Túi 100 cái", {"Cái": 1}), "C")
	la("muc C bang rong", T["muc_an_toan"]("Bao 25 kg", {}), "C")
	# Doc ten don vi khong phan biet hoa thuong.
	la("khong phan biet hoa thuong", T["muc_an_toan"]("túi 50gr",
		{"Túi": 50}), "A")


@ca("ten mon: cat roi thi lan sau khong con gi de cat")
def _lap_lai_duoc():
	# Chot tinh lap lai duoc: chay lenh hai lan khong lam hong ten.
	goc = "Đường cát trắng, Bao 12 kg, Cô Ba Biên Hòa"
	lan1, cat1 = T["cat_quy_cach"](goc)
	la("lan mot cat duoc", len(cat1), 1)
	lan2, cat2 = T["cat_quy_cach"](lan1)
	la("lan hai khong cat gi", cat2, [])
	la("ten khong doi them", lan2, lan1)


@ca("ten mon: doan khong phai quy cach thi khong dung toi")
def _khong_nham_doan_khac():
	# Ten nha cung cap, ten tieng Anh, quy cach san pham deu khong bi cat.
	dung("ten ncc", not T["la_doan_quy_cach"](" Interflour"))
	dung("ten tieng anh", not T["la_doan_quy_cach"](" Unsalted Butter"))
	dung("co so nhung khong co danh tu bao bi",
		not T["la_doan_quy_cach"](" số 8"))
	dung("dung la quy cach", T["la_doan_quy_cach"](" Bao 25 kg"))
	dung("quy cach khong don vi", T["la_doan_quy_cach"](" Hộp 4 cái"))
