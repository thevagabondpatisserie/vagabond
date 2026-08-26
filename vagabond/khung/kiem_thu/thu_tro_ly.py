# -*- coding: utf-8 -*-
"""Ca kiểm cho sổ tay tri thức của trợ lý.

Toàn phép thuần, chạy được không cần Frappe, không cần requests, không cần
site. `tro_ly.py` có gọi mạng nên KHÔNG được nạp vào đây: một ca kiểm kéo
theo thư viện mạng là ca kiểm đặt sai chỗ, và máy chạy CI thì tay không.

Vài ca đọc thẳng tệp thật trên đĩa để nếu ai sửa cấu trúc thẻ trang chủ hay
đoạn mô tả đầu tệp thì cổng đỏ ngay, chứ không đợi tới lúc trợ lý trả lời
rỗng trên máy nhân viên.
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


T = _thuan("tro_ly_so_tay.py", "tro_ly_so_tay_thuan")


@ca("so tay: rut duoc the chuc nang tren trang chu")
def _doc_the():
	js = ("card('\U0001f9fe', 'Đơn mua hàng', 'Đơn đã gửi nhà cung cấp, hàng về "
		"tới đâu', 0, 'PO') + card('\U0001f4b8', 'Công nợ phải trả', 'Còn nợ nhà "
		"cung cấp nào, khoản nào quá hạn', 0, 'CNPT')")
	the = T["doc_the_trang_chu"](js)
	la("so the", len(the), 2)
	la("mo ta PO", the["PO"], "Đơn đã gửi nhà cung cấp, hàng về tới đâu")
	la("mo ta CNPT", the["CNPT"], "Còn nợ nhà cung cấp nào, khoản nào quá hạn")


@ca("so tay: the lay ten tu bien thi BO QUA chu khong doan bua")
def _the_dung_bien():
	# Vai the khai `TYPES.Purchase.title` thay vi mot chuoi. Doan gia tri cua
	# mot bien JavaScript bang bieu thuc chinh quy la cach chac chan sinh ra
	# mo ta sai, nen phep rut co y de rot.
	js = "card(TYPES.Purchase.icon, TYPES.Purchase.title, TYPES.Purchase.sub, n[0], 'Purchase')"
	la("khong bat the dung bien", len(T["doc_the_trang_chu"](js)), 0)


@ca("so tay: the that tren trang chu van doc duoc")
def _the_that():
	nguon = io.open(os.path.join(GOI, "public", "js", "bep", "02-trang-chu.js"),
		encoding="utf-8").read()
	the = T["doc_the_trang_chu"](nguon)
	# Ngay 26/08/2026 doc duoc 59 khoa. Chot san mot con so toi thieu: tut
	# xuong duoi nghia la ai do doi cach viet the, va so tay se rong dan ma
	# khong ai hay.
	dung("doc duoc it nhat 50 the that", len(the) >= 50)
	dung("co man doanh so", "DS" in the or "POS" in the)
	for khoa, mo_ta in the.items():
		dung("mo ta %s khong rong" % khoa, len(mo_ta) > 5)


@ca("so tay: rut duoc doan mo ta dau tep Python")
def _doan_dau():
	nguon = '# -*- coding: utf-8 -*-\n"""Dòng đầu.\n\nĐoạn sau.\n"""\n\nimport os\n'
	d = T["doan_dau_tep"](nguon)
	la("dong dau", d.split("\n")[0], "Dòng đầu.")
	dung("giu ca doan sau", "Đoạn sau." in d)
	la("tep khong co doan mo ta", T["doan_dau_tep"]("import os\n"), "")
	la("tep rong", T["doan_dau_tep"](""), "")


@ca("so tay: doan mo ta bi cat theo tran do dai")
def _doan_bi_cat():
	nguon = '"""' + ("x" * 5000) + '"""'
	la("cat dung tran", len(T["doan_dau_tep"](nguon, dai=100)), 100)


@ca("so tay: tu khoa bo dau va bo tu qua pho bien")
def _tu_khoa():
	tu = T["tu_khoa"]("Làm sao để xem Công nợ phải trả?")
	dung("giu tu co nghia", "cong" in tu and "no" in tu and "tra" in tu)
	dung("bo tu qua pho bien", "lam" not in tu and "sao" not in tu and "de" not in tu)
	la("cau rong", T["tu_khoa"](""), set())


@ca("so tay: ten man nang hon mo ta, mo ta nang hon phan chi tiet")
def _diem_khop():
	tu = T["tu_khoa"]("doanh số")
	o_ten = {"ten": "Doanh số", "mo_ta": "", "chi_tiet": ""}
	o_mo_ta = {"ten": "", "mo_ta": "Doanh số", "chi_tiet": ""}
	o_chi_tiet = {"ten": "", "mo_ta": "", "chi_tiet": "Doanh số"}
	d1 = T["diem_khop"](tu, o_ten)
	d2 = T["diem_khop"](tu, o_mo_ta)
	d3 = T["diem_khop"](tu, o_chi_tiet)
	dung("ten thang mo ta", d1 > d2)
	dung("mo ta thang chi tiet", d2 > d3)
	la("cau hoi rong thi khong diem", T["diem_khop"](set(), o_ten), 0)


@ca("so tay: khong muc nao khop thi tra RONG, khong lay bua")
def _khong_khop_thi_rong():
	# Day la cho chan bia quan trong nhat. Tra ve rong thi tro_ly.py tra loi
	# thang la chua co tai lieu va KHONG goi mo hinh. Neu doi thanh "lay dai
	# ba muc dau bang" thi mo hinh se duoc moi bia tren tu lieu khong lien
	# quan, ma bia ve phan mem noi bo thi nghe rat that.
	so_tay = [
		{"ten": "Doanh số", "mo_ta": "Đơn bán trong ngày", "chi_tiet": ""},
		{"ten": "Công nợ", "mo_ta": "Khách còn nợ bao nhiêu", "chi_tiet": ""},
	]
	la("hoi chuyen khong lien quan",
		T["chon_muc"]("cách nướng bánh mì sourdough", so_tay), [])
	la("cau hoi rong", T["chon_muc"]("", so_tay), [])
	la("cau hoi toan tu pho bien", T["chon_muc"]("làm sao để", so_tay), [])


@ca("so tay: chon dung muc sat nhat va gioi han so muc")
def _chon_muc():
	so_tay = [
		{"ten": "Doanh số", "mo_ta": "Đơn bán trong ngày", "chi_tiet": ""},
		{"ten": "Công nợ", "mo_ta": "Khách còn nợ bao nhiêu", "chi_tiet": ""},
		{"ten": "Công nợ phải trả", "mo_ta": "Còn nợ nhà cung cấp nào", "chi_tiet": ""},
	]
	ra = T["chon_muc"]("công nợ", so_tay)
	dung("co ket qua", len(ra) >= 2)
	dung("khong lot man khong lien quan",
		all(x["ten"] != "Doanh số" for x in ra))
	la("gioi han so muc", len(T["chon_muc"]("công nợ", so_tay, so_muc=1)), 1)


@ca("so tay: tu lieu gui kem co tran do dai")
def _gon_tu_lieu():
	muc = [{"ten": "M%d" % i, "duong": "/m%d" % i, "mo_ta": "x" * 500,
		"chi_tiet": "y" * 500} for i in range(20)]
	t = T["gon_tu_lieu"](muc, tran=2000)
	dung("khong vuot tran", len(t) <= 2200)
	dung("co dia chi mo man", "/m0" in t)
	la("khong muc nao", T["gon_tu_lieu"]([]), "")


@ca("so tay: nguong do phu chan cau hoi ngoai le, van cho cau ve app qua")
def _nguong_do_phu():
	# Ban dau phep chon chi doi "co chu nao trung la duoc". Do tren so tay
	# THAT ngay 26/08/2026 (177 muc) thi luat do gan nhu khong bao gio tu
	# choi: hoi "hom nay troi dep khong" van ra sau muc, vi trong hon mot
	# tram doan mo ta cua mot tiem banh thi chu nao cung tung xuat hien o
	# dau do. Nhu vay cai chan quan trong nhat xem nhu khong ton tai.
	so_tay = [
		{"ten": "Doanh số", "mo_ta": "Đơn bán trong ngày, xem vào đâu",
			"chi_tiet": ""},
		{"ten": "Nhận bánh", "mo_ta": "Sổ nhận bánh của cửa hàng",
			"chi_tiet": "Bếp giao bánh cho cửa hàng, đếm tại nhà kho"},
	]
	dung("cau ve app van qua", bool(T["chon_muc"]("xem doanh số vào đâu", so_tay)))
	la("cau ngoai le bi chan",
		T["chon_muc"]("cách nướng bánh mì sourdough tại nhà", so_tay), [])


@ca("so tay: do phu dem tren ca ten, mo ta va phan chi tiet")
def _do_phu():
	tu = T["tu_khoa"]("công nợ nhà cung cấp")
	m = {"ten": "Công nợ", "mo_ta": "phải trả", "chi_tiet": "nhà cung cấp nào còn nợ"}
	la("phu du nam chu", T["phu_tu_khoa"](tu, m), 5)
	dung("du lien quan", T["du_lien_quan"](tu, m))
	xa = {"ten": "Tồn kho", "mo_ta": "", "chi_tiet": "đếm hàng trong kho"}
	dung("khong du lien quan", not T["du_lien_quan"](tu, xa))
	la("cau hoi rong thi khong phu", T["phu_tu_khoa"](set(), m), 0)
	dung("cau hoi rong khong bao gio du", not T["du_lien_quan"](set(), m))


@ca("so tay: xep theo DO PHU truoc roi moi toi diem")
def _xep_theo_do_phu():
	# Cai bay that gap luc dung: neu xep theo diem truoc thi mot muc dai
	# lem nhem co the day muc phu tron ven cau hoi xuong duoi, va phep xet
	# nguong o tren soi nham nguoi roi tra ve rong.
	so_tay = [
		# Phu ca hai chu nhung chi nam o phan chi tiet nen diem thap.
		{"ten": "", "mo_ta": "", "chi_tiet": "màn doanh số nằm ở trang chủ"},
		# Diem cao vi trung ten, nhung chi phu mot chu.
		{"ten": "Doanh thu", "mo_ta": "", "chi_tiet": ""},
	]
	ra = T["chon_muc"]("doanh số", so_tay)
	dung("co ket qua", bool(ra))
	dung("muc phu tron ven dung dau", "doanh số" in (ra[0].get("chi_tiet") or ""))
