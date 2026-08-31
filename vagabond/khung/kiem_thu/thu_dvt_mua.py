# -*- coding: utf-8 -*-
"""Ca kiểm cho phép so đơn vị giữa hoá đơn mua và phiếu nhập kho.

Toàn phép thuần. `dvt_mua.py` để phần chạm Frappe xuống dưới vạch phân
cách nên bộ kiểm này chạy được trên máy CI tay không, không cần requests,
không cần site.

Số liệu lấy nguyên từ sự cố thật ngày 26/08/2026: hoá đơn HDM-26-08-00104
và phiếu nhập PNK-2026-00162 của Thực phẩm Ngon Cổ Điển, món hạt dẻ đông
lạnh NVLT00227.
"""

from vagabond import dvt_mua as D
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("bo dau: ten don vi tieng Viet so duoc voi nhau")
def _bo_dau():
	la("Tui", D.bo_dau("Túi"), "tui")
	la("Lit", D.bo_dau("Lít"), "lit")
	la("Hu", D.bo_dau("Hũ"), "hu")
	la("chuan bo khoang trang", D.chuan("  Tú i "), "tui")


@ca("cung don vi: ten viet khac nhau van la mot")
def _cung_don_vi():
	dung("Tui vs tui", D.cung_don_vi("Túi", "tui"))
	dung("Tui vs TUI", D.cung_don_vi("Túi", "TÚI"))
	dung("Tui khac Gram", not D.cung_don_vi("Túi", "Gram"))
	dung("rong khong bao gio bang", not D.cung_don_vi("", ""))


@ca("goi y don vi: BAG cua nha cung cap la Tui cua minh")
def _goi_y():
	# Hoa don dien tu so 55445 ghi dvtinh la "BAG". Bang quy doi cua mon chi
	# co Tui va Kg nen may khong tra ra duoc, phai lui ve don vi kho.
	la("BAG", D.goi_y_don_vi("BAG"), "Túi")
	la("bag thuong", D.goi_y_don_vi("bag"), "Túi")
	la("PCS", D.goi_y_don_vi("PCS"), "Cái")
	la("CTN", D.goi_y_don_vi("CTN"), "Thùng")
	la("khong biet thi chiu, khong doan", D.goi_y_don_vi("ZZZ"), "")
	la("rong", D.goi_y_don_vi(""), "")


@ca("he so: thieu hoac phi ly deu ve 1")
def _he_so():
	la("binh thuong", D.he_so(1000), 1000.0)
	la("None", D.he_so(None), 1.0)
	la("khong", D.he_so(0), 1.0)
	la("am", D.he_so(-5), 1.0)
	la("chu", D.he_so("abc"), 1.0)


@ca("quy ve don vi kho: 4 Tui la 4.000 Gram chu khong phai 4")
def _quy_ve_kho():
	la("4 Tui", D.ton(4, 1000), 4000.0)
	la("4 Gram", D.ton(4, 1), 4.0)
	la("rong", D.ton(None, 1000), 0.0)


@ca("don gia quy ve don vi kho moi tru nhau duoc")
def _gia_theo_kho():
	# 280.000 mot Gram va 161.000 mot Tui la hai con so khong cung ho. Quy
	# ca hai ve mot gram thi thay ro: 280.000 doi dien 161.
	la("hoa don 280.000/Gram", D.gia_moi_don_vi_kho(280000, 1), 280000.0)
	la("phieu nhap 161.000/Tui", D.gia_moi_don_vi_kho(161000, 1000), 161.0)
	la("chia cho he so 0 khong no", D.gia_moi_don_vi_kho(1000, 0), 1000.0)


@ca("lech don vi: Gram doi dien Tui la lech, Kg doi dien Ky thi khong")
def _lech_dvt():
	dung("Gram vs Tui", D.lech_don_vi("Gram", 1, "Túi", 1000))
	dung("Tui vs Tui", not D.lech_don_vi("Túi", 1000, "Túi", 1000))
	# Hai ten khac nhau ma cung he so thi so luong ghi ra nhu nhau, khong
	# viec gi phai chan nguoi ta lai.
	dung("Kg vs Ky cung 1000", not D.lech_don_vi("Kg", 1000, "Ký", 1000))


@ca("so luong: phai quy ve don vi kho truoc khi so, day la loi cua v314")
def _so_ton():
	# Truoc v315 cho nay so "4" voi "4" roi ket luan khop so luong. Ca that
	# lech gap mot nghin lan ma man hinh chi bao lech gia.
	dung("4 Gram KHONG khop 4 Tui", not D.so_ton_khop(4, 1, 4, 1000))
	dung("4.000 Gram khop 4 Tui", D.so_ton_khop(4000, 1, 4, 1000))
	dung("4 Tui khop 4 Tui", D.so_ton_khop(4, 1000, 4, 1000))


@ca("cau bao lech don vi: noi du so va noi viec can lam")
def _cau_bao():
	c = D.loi_lech_don_vi(1, "Hạt dẻ", 4, "Gram", 1, 4, "Túi", 1000, "Gram", "BAG")
	dung("co so dong", "Dòng 1" in c)
	dung("co ten mon", "Hạt dẻ" in c)
	dung("co so quy doi cua phieu nhap", "4000" in c)
	dung("co don vi goc cua nha cung cap", "BAG" in c)
	dung("co goi y", "Túi" in c)
	dung("co viec can lam", "bảng quy đổi" in c)
	# Khong doc duoc don vi goc thi van phai ra cau tu te, khong duoc bia.
	c2 = D.loi_lech_don_vi(2, "Bơ", 1, "Gram", 1, 1, "Thùng", 5000, "Gram", "")
	dung("khong bia don vi ncc", "BAG" not in c2 and "hoá đơn điện tử" not in c2)
	dung("van co so dong", "Dòng 2" in c2)


@ca("quy uoc trinh bay: khong dau gach dai trong cau bao nguoi dung doc")
def _khong_gach_dai():
	c = D.loi_lech_don_vi(1, "Hạt dẻ", 4, "Gram", 1, 4, "Túi", 1000, "Gram", "BAG")
	dung("khong em dash", "—" not in c)
	dung("khong en dash", "–" not in c)


# --------- v327: MOT phep xet don vi dung chung cho ca hai cho

@ca("xet don vi: cung ten thi khop")
def _xet_khop():
	la("Tui vs tui", D.xet_don_vi("Túi", 1000, "tui", 1000), D.DVT_KHOP)


@ca("xet don vi: he so khac nhau la LECH THAT")
def _xet_lech():
	# 4 Gram doi dien 4 Tui: lech mot nghin lan, khong duoc noi.
	la("Gram vs Tui", D.xet_don_vi("Gram", 1, "Túi", 1000), D.DVT_LECH)


@ca("xet don vi: cung he so ma khac ten thi chi la KHAC TEN")
def _xet_khac_ten():
	# Ca that 27/08/2026, HDM-26-08-00115: hoa don ghi Gói he so 1.000,
	# phieu nhap ghi Kg he so 1.000. Cung 4.500 gram, chi khac cai ten.
	# Truoc do man hinh coi la khop con phep noi lai tu choi.
	la("Goi vs Kg cung 1000", D.xet_don_vi("Gói", 1000, "Kg", 1000), D.DVT_KHAC_TEN)
	la("Kg vs Ky cung 1000", D.xet_don_vi("Kg", 1000, "Ký", 1000), D.DVT_KHAC_TEN)


@ca("xet don vi: ba nhan khac nhau, khong cai nao trung cai nao")
def _xet_ba_nhan():
	dung("ba hang khac nhau", len({D.DVT_KHOP, D.DVT_KHAC_TEN, D.DVT_LECH}) == 3)


# --------- v327: man Doi chieu va phep noi phai noi cung mot cau

@ca("doi chieu: man hinh va phep noi dung CHUNG mot phep xet")
def _hai_cho_cung_phep():
	import inspect

	from vagabond import doi_chieu_mua as C

	so_sanh = inspect.getsource(C.so_sanh)
	noi = inspect.getsource(C._noi)
	dung("man hinh goi xet_don_vi", "xet_don_vi(" in so_sanh)
	dung("phep noi goi xet_don_vi", "xet_don_vi(" in noi)
	dung("man hinh khong con tu goi lech_don_vi", "lech_don_vi(" not in so_sanh)
	dung("phep noi khong con tu ghep hai dieu kien",
		"or not dvt_mua.cung_don_vi(" not in noi)


@ca("doi chieu: cung so luong khac ten thi TU doi ten roi di tiep")
def _tu_doi_ten():
	import inspect

	from vagabond import doi_chieu_mua as C

	dung("co ham doi ten don vi", hasattr(C, "_doi_ten_don_vi"))
	ma = inspect.getsource(C._doi_ten_don_vi)
	dung("co kiem Mon da khai don vi do chua", "UOM Conversion Detail" in ma)
	dung("co kiem he so bang nhau moi doi", "he_so" in ma)
	dung("doi ca o don vi lan he so", "dong.uom = dvt" in ma and "dong.conversion_factor" in ma)

	noi = inspect.getsource(C._noi)
	dung("phep noi co goi ham do", "_doi_ten_don_vi(d, chon)" in noi)
	dung("khac ten ma khong doi duoc thi bao ro", "chưa khai" in noi)


@ca("quyen chot gia khac: ghi trong ma nguon chu khong phu thuoc o thiet lap")
def _quyen_chot_gia():
	from vagabond import doi_chieu_mua as C

	dung("co danh sach vai", hasattr(C, "VAI_CHOT_GIA_KHAC"))
	# Anh Viet chot 27/08/2026: mo cho Uyen, Uyen giu Purchase Manager.
	dung("thu mua chot duoc", "Purchase Manager" in C.VAI_CHOT_GIA_KHAC)
	dung("ke toan van chot duoc", "Accounts Manager" in C.VAI_CHOT_GIA_KHAC)
	# Bep khong duoc chot gia.
	dung("bep khong nam trong day", "Bộ phận đặt hàng" not in C.VAI_CHOT_GIA_KHAC)


@ca("dong dich vu: dong khong co ma hang khong tinh la lech don vi")
def _dong_dich_vu():
    dung("khong ma hang la dong dich vu", D.dong_dich_vu(None))
    dung("chuoi rong cung vay", D.dong_dich_vu(""))
    dung("chuoi toan khoang trang cung vay", D.dong_dich_vu("   "))
    dung("co ma hang thi KHONG phai", not D.dong_dich_vu("NVLT00242"))


@ca("do tam: mon nhan qua nhieu ten NCC la dau hieu bi dung lam cho do")
def _do_tam():
    # So lieu that 27/08/2026.
    dung("NVLT00231 nhan 18 ten, bi keu", D.dang_do_tam("NVLT00231", 18))
    dung("mon dong thu ba chi 7 ten, khong keu", not D.dang_do_tam("NVLT00204", 7))
    dung("dung nguong 8 thi 8 ten la keu", D.mon_bi_do_tam(8))
    dung("7 ten thi chua keu", not D.mon_bi_do_tam(7))
    # Chi phi tiep khach VON DI la mon gom, keu no la keu oan.
    dung("mon gom co chu y khong bi keu", not D.dang_do_tam("DVTI00017", 11))
    dung("nhung phep thuan tran thi van dem", D.mon_bi_do_tam(11))
    dung("khai san trong danh sach mon gom", "DVTI00017" in D.MON_GOM_CO_Y)


@ca("con so canh bao lech don vi phai TRU dong dich vu ra")
def _con_so_sach():
    import inspect

    from vagabond import dung_lai_hddt as H

    ma = inspect.getsource(H.soat_don_vi)
    dung("co loc dong dich vu", "dong_dich_vu" in ma)
    dung("so_to dem tu danh sach da loc", '"so_to": len({x["name"] for x in that})' in ma)
    dung("van dem rieng phan dich vu", '"so_to_dich_vu"' in ma)
    # Ngay 27/08/2026 con so dua ra man hinh la 1.185 to trong khi lech that
    # chi 505 to. Dem ca hai vao mot con so la thoi phong gap doi.
    dung("KHONG cong hai loai lam mot", "that + dich_vu" not in ma)


@ca("dung lai to lech don vi: co duong rieng, khong di nho duong lech tien")
def _duong_rieng():
    import inspect

    from vagabond import dung_lai_hddt as H

    dung("co ham rieng", hasattr(H, "dung_lai_lech_don_vi"))
    ma = inspect.getsource(H.dung_lai_lech_don_vi)
    # Nhom nay TIEN DUNG nen `soat` khong bao gio nhac toi. Lay danh sach tu
    # `soat` la chay khong, khong to nao duoc dung lai.
    dung("lay danh sach tu phep soi don vi", "soat_don_vi(" in ma)
    dung("KHONG lay tu phep soi tien", "soat(gioi_han" not in ma)
    dung("bo qua to da ghi so", 'da_ghi_so' in ma)
    dung("van dung thu truoc khi ghi de", "dung_lai_co_loi_khong" in ma)
    dung("luu xong lech thi tra ve nguyen trang", "rollback" in ma)
    dung("khong sua tay so luong", ".qty =" not in ma)


@ca("soat do tam: chi liet ke, khong tu go anh xa")
def _soat_do_tam_chi_doc():
    import inspect

    from vagabond import dung_lai_hddt as H

    dung("co ham", hasattr(H, "soat_do_tam"))
    ma = inspect.getsource(H.soat_do_tam)
    dung("dem theo TEN nha cung cap khac nhau", "ten_ncc" in ma)
    dung("dung phep thuan chung", "dang_do_tam" in ma)
    for cam in (".delete(", "frappe.delete_doc", "db_set", ".save(", "set_value"):
        dung("khong %s" % cam, cam not in ma)


@ca("doi chieu: mon khong co phieu nhap nao thi phai chi duong di tiep")
def _khong_co_phieu_nhap():
    """Cau bao nay tung lam Uyen ket (anh Viet bao 31/08/2026).

    Ban cu chi noi "khong co trong phieu nhap nao dang chon" roi dung.
    Nguoi doc hieu la minh chon nham phieu nen di chon lai, chon mai khong
    ra, roi ket luan la he thong chan quyen sua gia - trong khi su that la
    mon do CHUA TUNG duoc nhap kho, khong co phieu nao de chon ca.

    Ca that: giay in A4 cua Muc In Bao Tin, hoa don 3513. Nha cung cap do
    khong co mot phieu nhap nao trong he.

    Mot cau chan doan ma khong co duong ra thi nguoi ta tu nghi ra duong sai.
    """
    import inspect

    from vagabond import doi_chieu_mua as C

    noi = inspect.getsource(C._noi)
    doan = noi.split("if not ds:")[1].split("elif")[0]
    dung("noi ro la hang chua duoc nhap kho", "chưa được nhập kho" in doan)
    dung("chi duong lap phieu nhap", "lập phiếu" in doan)
    dung("chi duong ghi so thang khi hang khong qua kho",
         "ghi sổ thẳng" in doan)
    dung("co ke ra loai hang khong qua kho", "văn phòng" in doan)
    # Cau cu chi chan doan ma khong co duong ra.
    dung("khong con cau cut ngan cu",
         "không có trong phiếu nhập nào đang chọn." not in noi)
