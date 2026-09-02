"""Canh cua vao cua may chu: ham nao dang duoc goi tu ngoai.

Vi sao co tep nay
-----------------
Ngay 19/08/2026, khi them ham `dong_bo_so_hddt` vao `hoan_tien.py`, em chen
no vao ngay TRUOC dong `def ds(...)`. Ma phia tren `def ds` la dong
`@frappe.whitelist()`. Ket qua: cai decorator do bam vao ham moi, con `ds`
thi mat quyen goi.

Python khong bao gi ca. Kiem thu cung khong bao, vi khong ca nao goi `ds`.
Cong tam cong doan van tra ve 0. Chi den luc mo man Hoan tien tren app moi
ra loi "Ham vagabond.hoan_tien.ds chua duoc whitelist" - tuc la sales va ke
toan chiu tran.

Day la kieu loi khong the bat bang cach doc lai code cho ky hon, vi no vo
hinh: hai dong dung canh nhau, doi cho la hong, ma nhin thi van rat hop ly.
Nen phai chot bang mot danh sach viet ro ra.

Cach dung khi them ham moi
--------------------------
Them ham CO whitelist thi them ten vao danh sach duoi day. Ca kiem se do.
Neu ca kiem bao thua hoac thieu mot ten ma minh khong co y dinh doi, thi
gan nhu chac chan la mot decorator vua bam nham ham.
"""

import ast
import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

# Ba lan dirname tu tep nay ra dung thu muc goi `vagabond/`, tuc cho dat
# hoan_tien.py, mua_dich_vu.py va cac mo dun nghiep vu khac.
GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Danh sach cua ngo tung mo dun. Chot ngay 19/08/2026.
CUA_NGO = {
	# Them 23/08/2026 cung lan dua Web Page va Mau in ra git. `soi_lech` chi
	# DOC va so sanh, khong ghi gi, nen mo ra ngoai duoc. `dong_bo` thi KHONG:
	# no ghi de mau in tren site, chi duoc chay trong after_migrate.
	"mau_in/__init__.py": ["soi_lech"],
	# Them 26/08/2026 cung lan dua phan he Cau hinh mau in an ra man Cai dat.
	# Ba ham deu la cua man hinh. `het`, `theo_diem` va nhom ham thuan
	# `chuan_*` la ham noi bo, khong duoc mo ra ngoai.
	"mau_in_quay.py": ["danh_sach", "luu", "tra_mac_dinh"],
	# Them 27/08/2026: cong tac tam ngung ban mot ma tren web dat banh. Chi
	# `dat` duoc mo ra ngoai; `bang` va `dang_tat` la ham noi bo, hai man kiem
	# banh goi qua cua rieng cua chung.
	"tat_ban_web.py": ["dat"],
	"nvl_thay_the.py": ["tinh_lai"],
	# Them 01/09/2026 cung lan mo phan he Nhan su, man Duyet KPI va hoa hong.
	# Muoi hai cua ngo deu la cua man hinh: dung phieu, cham diem, duyet, tra
	# lai, gop y, day sang de nghi chi, xem danh sach, xem chi tiet, xem phieu
	# cua chinh minh, doc va luu bang chi tieu, tra danh sach nguoi dung.
	#
	# `tinh_lai` va `so_lieu_tu_dong` CO Y khong nam trong danh sach. Hai ham
	# do tinh ra tien hoa hong; mo ra ngoai la cho trinh duyet tu quyet so
	# tien. Man hinh chi duoc XEM so may chu da tinh, khong duoc tu tinh.
	"kpi.py": [
		"cai_dat", "cham", "chi_tiet", "cua_toi", "danh_sach", "day_chi",
		"dung_phieu", "duyet", "luu_cai_dat", "nguoi_dung", "tra_lai",
		# Them 02/09/2026: nhan vien tu lap phieu duyet KPI va hoa hong cho
		# nhung ky may chua co so lieu.
		"tu_khai",
		"y_kien",
	],
	# Them 01/09/2026: cong tai tep dung chung cho moi man. Ba cua ngo:
	# `nap_tam` nhan mot tep luc chung tu chua co ma, `go_ra` go tep con treo,
	# `cai_dat` chi doc luat de man hinh va may chu khong noi khac nhau.
	#
	# `gan_vao` va `don_rac` CO Y khong nam trong danh sach. `gan_vao` buoc tep
	# vao chung tu - mo ra ngoai la cho bat ky ai buoc tep bat ky vao chung tu
	# bat ky. `don_rac` xoa tep that - mo ra ngoai la cho goi mot nhip xoa tu
	# trinh duyet.
	"tep_dinh_kem.py": ["cai_dat", "go_ra", "nap_tam"],
	# Them 28/08/2026 cung lan dat hang rao tai khoan kho. Chi `soat_kho` la
	# cua man hinh; `chan_nhap_vao_thanh_pham` la HOOK, chay tren duong ghi
	# so cua Frappe chu khong ai goi tu ngoai, nen KHONG mo ra ngoai. Ba ham
	# thuan `so_hieu`, `la_tk_thanh_pham`, `soi_dong` cung vay.
	"gac_tk_kho.py": ["soat_kho"],
	# Them 28/08/2026: uy nhiem chi cho ho so thanh toan tren app. Bon cua
	# ngo, ba cai dau la nut tren man ho so, cai cuoi chi doc de xem may
	# dang dinh chi tien ra tu tai khoan nao. Cac ham con lai (`chep_unc`,
	# `tk_tien_chi`, `dem_unc`, `ds_unc_tho`) la ham noi bo, ho_so_tt goi
	# thang chu khong di qua mang.
	"tra_tien_app.py": ["dinh_unc", "ds_unc", "go_unc", "soat_tk_chi"],
	# Them 28/08/2026: thu tien va xuat hoa don cho hop dong da ky, va
	# bang doi ruot hop mua vu. Ba nhom cua ngo:
	#   thu_hop_dong  - lap phieu, xem, xuat PDF, gui khach
	#   hop_dong_hoa_don - doc dong hang tu bao gia, roi ghi so
	# `mua_vu.py` khong nam trong bang nay (tep lon, nhieu phien lam song
	# song), nen hai cua ngo doi ruot cua no khong ghi o day.
	"thu_hop_dong.py": [
		"muc_goi_y", "tao_phieu", "ds_phieu", "xem_phieu", "huy_phieu",
		"kiem_sepay", "ghi_da_thu", "xem_truoc", "xuat_pdf", "gui_email",
	],
	"hop_dong_hoa_don.py": ["dong_tu_hop_dong", "ghi_so"],
	# Them 26/08/2026 cung lan vá phép so đơn vị giữa hoá đơn mua và phiếu
	# nhập. `_noi`, `_goi_y`, `_vuot_lech_gia_duoc` deu la ham noi bo, chi
	# bon ham man hinh goi truc tiep moi duoc mo ra ngoai.
	# Them 26/08/2026: dung lai hoa don mua theo ban hoa don dien tu goc.
	# `dong_bo_luc_luu` va `tk_theo_mon` la HOOK, chay tren duong luu cua moi
	# hoa don mua, tuyet doi khong duoc mo ra ngoai. Hai ham hang loat va sua
	# to da ghi so chi cho ke toan truong, kiem quyen ben trong.
	"dung_lai_hddt.py": [
		"dung_lai", "dung_lai_tat_ca",
		# dung_lai_lech_don_vi va soat_do_tam them 27/08/2026: nhom to lech
		# DON VI ma tien van dung khong nam trong danh sach cua `soat`, nen
		# `dung_lai_tat_ca` khong bao gio cham toi. Phai co duong rieng.
		"dung_lai_lech_don_vi", "soat", "soat_do_tam", "soat_don_vi",
		"sua_to_da_ghi_so",
	],
	# Bang ra thu gui nha cung cap, them 28/08/2026 cung lan dat hang rao.
	"gac_thu_ncc.py": ["soat_thu_ncc"],
	# khai_don_vi them 31/08/2026. Anh Viet: "cai vu don vi tinh cu suot ngay
	# bi lech anh chang hieu anh phai lam gi de no khong lech". Truoc do
	# `sua_don_vi` tu choi khi mon chua khai don vi va bao "nho thu mua khai
	# truoc", nhung khong co man nao de khai - phai mo Desk. Day la cai cho do.
	# gan_ma_hang va goi_y_mon them 31/08/2026. Ngay do he co 9.985 tren
	# 11.351 dong hoa don khong co ma hang, tren 2.612 to - va man hinh bao
	# nham thanh "hang chua duoc nhap kho". `_mst_cua_to` va `_phieu_ung_vien`
	# la ham noi bo, KHONG mo ra ngoai.
	"doi_chieu_mua.py": [
		"danh_sach", "don_vi_cua_mon", "gan_ma_hang", "ghi_so_thang", "goi_y_mon",
		"khai_don_vi", "noi_phieu", "so_sanh", "sua_don_vi", "xem",
	],
	# Bang gia nhap duoi theo gia tren hoa don, them 31/08/2026. `can_khai_don_vi`
	# chi DOC, dua ra danh sach don vi cua nha cung cap ma Mon chua khai.
	# `cap_nhat_tu_hoa_don` va `_chay` la moc doc_events, KHONG mo ra ngoai.
	"bang_gia_nhap.py": ["can_khai_don_vi"],
	"de_nghi_chi.py": [
		"danh_muc", "danh_sach",
		# doi_soat va ds_man them 20/08/2026: man Danh sach TTNB co chip
		# trang thai va chip thoi gian, va doi soat dong tien ra tu OCB.
		"doi_soat", "ds_man",
		"duyet", "goi_y_tai_khoan", "gui_duyet",
		# chi_tiet va tam_ung_cua_toi them ngay 20/08/2026 cung lan doi sang
		# bang ke nhieu dong: mot phieu gio co nhieu khoan nen phai co cua
		# doc ca phieu, va o "Thuoc ma Tam ung" phai co cai de do vao.
		"chi_tiet",
		# tao them ngay 19/08/2026: cong lap phieu tu APP cho moi nhan vien,
		# truoc do phieu chi lap duoc tren Desk.
		"tam_ung_cua_toi", "tao", "tra_lai",
		# tim_gd_ra va khop_tay them 24/08/2026: man nay la duong DUY NHAT
		# webhook SePay goi thang, phieu tu nhay sang "Da chi" khong ai bam
		# nut nao, ma truoc do KHONG co duong lui khi noi dung go sai.
		"tim_gd_ra", "khop_tay",
	],
	# Duong thu di, them 21/08/2026 sau su co ca tiem khong gui duoc email.
	# `bu_nguoi_gui` va `canh_bao_email_loi` KHONG duoc co mat o day: mot cai
	# la hook nam tren duong di cua MOI email trong he, mot cai la nhip lap
	# lich. Ho ra thi la decorator vua bam nham.
	"gui_thu.py": ["cuu_su_co_1608", "suc_khoe", "va_hang_doi_ket"],
	# Luong dong tien, them 21/08/2026: ca lam viec tai quay va phieu nop
	# quy. Cac ham _doanh_thu_he_thong, _ca_dang_mo la noi bo, khong mo.
	"ca_quay.py": ["chi_tiet", "chot_ca", "danh_sach", "mo_ca", "tinh_trang"],
	"nop_quy.py": ["ca_cho_nop", "chi_tiet", "danh_sach", "doanh_thu_diem",
		"ky_giao", "ky_nhan", "tao", "tao_theo_ngay", "tim_nguoi_nhan",
		"xuat_excel", "xuat_pdf"],
	# Trang thai gui thu tren chung tu. `danh_dau_cho_gui` la hook va
	# `soat_tu_dong` la nhip lap lich, ca hai chay tu ben trong.
	"trang_thai_thu.py": ["soat_lai", "tinh_trang"],
	# Chuyen BTP cap 1 sang Phantom, them 21/08/2026. `chuyen` mac dinh chi
	# chay thu; phai truyen chay_that=1 moi ghi.
	"phantom.py": ["chung_tu_thu", "chuyen", "dong_lenh", "trang_thai",
		"xem_truoc", "soat_lam_tuoi"],
	# Bo don du lieu san xuat mot lan, them 21/08/2026. Moi cua deu
	# chay_that=0 mac dinh, goi trong chi tra ke hoach.
	"don_du_lieu.py": ["dat_tran_vuot_lenh", "doi_ten", "don_kho_do_dang",
		"ma_thay_the", "nap_bom_thu_vien", "nuoc_het_ton"],
	# Danh muc cong thuc BOM cho bep truong, them 21/08/2026.
	"cong_thuc.py": ["bo_nhap", "chi_tiet", "danh_sach", "dieu_chinh",
		"ghi_so", "sua_nhap", "tao_moi"],
	# Loi ke toan mua hang, them 21/08/2026. `giu_tk_theo_phieu_nhap` la hook
	# nen KHONG whitelist, chi hai cua nay mo cho ke toan truong.
	"ke_toan_mua.py": ["dat_tk_hang_chua_hoa_don", "kiem_tra", "so_chi_tiet_ncc"],
	# Bo kiem thu tich hop, them 21/08/2026 sau su co Kien khong nhap kho
	# duoc. Chay tren site that nen phai co cua, `nen.py` va cac tep `thu_`
	# la noi bo, KHONG duoc mo ra ngoai.
	"khung/kiem_that/cua.py": ["chay"],
	# Danh muc ngan hang Napas, them 23/08/2026 cung dot QT-31.
	# `khop_ten` va `chuan_hoa_hoac_bao` la phep noi bo: `khop_ten` thuan nen
	# vo hai, con `chuan_hoa_hoac_bao` co quyen TAO ban ghi Bank moi nen tuyet
	# doi khong mo ra ngoai.
	"ngan_hang.py": ["chuan_hoa", "tep_lo", "tim"],
	# Don Pancake da huy cho hoan tien, them 21/08/2026. `don_ban_dem`,
	# `_keo_don_huy`, `_doc_don` la ham noi bo, KHONG mo ra ngoai.
	# `_phieu` da go 23/08/2026: luong nay khong con dung chung tu ke toan
	# trong yeu cau cua Sales nua, hai phieu sinh o buoc doi soat ben
	# hoan_tien. Xem `hoan_tien._lap_cap_phieu_huy_don`.
	# `ds_phieu` va `xuat_excel_phieu`: man Phieu hoan don huy cho Sales,
	# them 31/08/2026. Chi DOC ho so ben ke toan, khong sua gi.
	# `dem_phieu_cho` cham do tren o Ban hang, `tim_don_de_hoan` man chon
	# don de lap phieu hoan, them 31/08/2026. `tim_don_de_hoan` CHI TIM,
	# viec lap van di qua ba cua cu cua hoan_tien.
	# `tai_tep` them 01/09/2026: ruot mot tep cua phieu hoan tien, di duong
	# co kiem quyen thay cho /private/files (Sales khong doc duoc Payment
	# Entry nen tep uy nhiem chi tra 403).
	# Mot don tra bang nhieu phuong thuc, them 01/09/2026. Cac phep thuan
	# (gom_dong, chinh_cua, tach_theo_pt...) va hai hook (dat_pt_chinh,
	# kiem_truoc_ghi_so) TUYET DOI khong mo ra ngoai.
	"thanh_toan_nhieu.py": ["luu", "xem"],
	"don_huy.py": ["bo_qua", "dem_cho_hoan", "dem_phieu_cho", "dong_bo", "ds",
		"ds_phieu", "tai_tep", "tao_hoan", "tim_don_de_hoan", "xem_hoan",
		"xuat_excel", "xuat_excel_phieu"],
	# Cay kho bon chang, them 21/08/2026. `gan_kho_nguon` la hook validate
	# cua Work Order nen KHONG whitelist.
	"kho_san_xuat.py": ["dung_cay_kho", "gan_chang_theo_ten",
		"gan_nguoi_phu_trach", "soat_chang", "tat_kho_trung_gian"],
	# Gom nam nhan chang ve hai ten, va man Ton kho theo chang, 28/08/2026.
	# `chang_cua_nhan`, `gop_dong`, `loc_theo_chang`, `cau_tom_tat` va
	# `kho_cua_bep` la phep thuan hoac ham noi bo, KHONG mo ra ngoai.
	"ton_chang.py": ["gom_chang", "ton_theo_chang"],
	# Ke hoach san xuat trong ngay, 28/08/2026. `tu_lap_nua_dem`,
	# `nhac_bep_sang` va `dung_mau_in` la nhip lap lich va after_migrate,
	# KHONG mo ra ngoai. Cac phep thuan cung khong.
	"ke_hoach_sx.py": ["chot", "dat_ton", "ds_lenh", "ds_phieu", "huy_lenh",
		"huy_phieu", "lap", "sua_so_lenh", "tao_lenh", "tim_lenh", "tinh_hinh_giu_cho",
		"ton_dong", "xem", "xin_chuyen_nvl"],
	# Ma phieu san xuat, them 30/08/2026. `soat_ma_cu` chi DEM phieu con
	# mang ma kieu cu, khong doi ten phieu nao.
	"ma_phieu_sx.py": ["soat_ma_cu"],
	# Tuy bien ruot hop qua, them 21/08/2026.
	"hop_qua.py": ["mon_thay_the", "ruot_goc", "xem_tuy_bien"],
	# Ham don o email: `don` va `ghi_vet` la hook, chi `kiem` mo ra ngoai.
	"email_sach.py": ["kiem"],
	# Phan he CRM, luong Tang qua khach VIP, them 25/08/2026.
	# `truoc_khi_luu` va `_kiem_mau` la hook validate, `quet_dem` va
	# `quet_dem_tu_dong` la nhip lap lich - ca bon deu chay tu ben trong nen
	# TUYET DOI khong mo ra ngoai. Rieng `quet_dem` mac dinh chay thu.
	#
	# Ba cua them 26/08/2026 cho Chien dich qua tang: `nhan_ban_dot` chep mot
	# dot sang mua sau, `khach_co_hang` doc danh sach khach da xep hang de
	# tick, `them_hang_loat` them nhieu khach vao dot mot lan bam.
	#
	# Bon cua nua them 26/08/2026, cung lan dua viec lap dot len app:
	# `danh_muc_dot` va `luu_dot` cho man lap dot, `xem_truoc_dan` va
	# `nap_dan` cho man dan danh sach tu bang tinh.
	"tang_qua.py": ["chi_tiet", "danh_muc", "danh_muc_dot", "danh_sach",
		"doi_trang_thai", "ds_dot", "khach_co_hang", "luu", "luu_dot",
		"nap_dan", "nhan_ban_dot", "them_hang_loat", "thu_boc_sdt",
		"xem_truoc_dan", "xem_truoc_loi_chuc"],
	# Hoa don hang bieu tang, them 26/08/2026. Chi HAI cua mo ra ngoai:
	# `kiem_phieu` chi doc, `xuat_hoa_don` lap to nhap. Bon ham hook
	# (truoc_khi_luu, truoc_khi_ghi_so, sau_khi_ghi_so, khi_huy) chay tu ben
	# trong Frappe nen TUYET DOI khong duoc whitelist: mo ra la ai cung goi
	# duoc ham dong dau "Da tang" len phieu ma khong can hoa don nao.
	"qua_tang_hoa_don.py": ["kiem_phieu", "xuat_hoa_don"],
	# Them 31/08/2026: phuong thuc "Hang tang" va luong giam doc duyet. Cac
	# ham hook (truoc_khi_luu, truoc_khi_ghi_so, sau_khi_ghi_so, khi_huy) do
	# hooks.py goi, KHONG duoc mo ra ngoai; `bo_sung_mac_dinh` ben
	# pt_thanh_toan cung vay, no chi chay trong after_migrate.
	"hang_tang.py": ["cai_dat", "luu_thong_tin", "dem_cho_duyet", "ds_don",
		"chi_tiet", "duyet", "tu_choi", "bao_cao"],
	# Hoa don dien tu thanh chung tu, them 26/08/2026 sau khi phat hien 125
	# to bi nuot. `con_sot` chi DOC, `mo_lai` chi doi co, `chay_bu` dung
	# chung tu that. `chay_tu_dong` la nhip lap lich, `_chay`, `_mot_to`,
	# `dung_hoa_don_mua` chay tu ben trong nen KHONG duoc whitelist.
	# `dong_bo_ngay` them 31/08/2026: ruot cua nut "Dong bo M-Invoice" tren
	# man danh sach Desk. Keo roi dung trong mot nhip bam.
	"minvoice_chung_tu.py": [
		"chay_bu", "con_sot", "dong_bo_ngay", "lanh_vo_ruot", "mo_lai",
	],
	# Man Viec can lam, them 20/08/2026: gom viec va LOC THEO VAI o may chu.
	# Truoc do man nay gom viec ngay tren may khach va phan lon khong loc vai.
	"viec_can_lam.py": ["danh_sach", "dem"],
	# Gan Assignee that, them 21/08/2026. Chi mot duong DOC, va no chi doc
	# viec cua CHINH nguoi dang dang nhap - khong co tham so nguoi nhan.
	"giao_viec.py": ["cua_toi"],
	# Nhap tep sao ke ngan hang, them 21/08/2026. Bu nhung khoan SePay khong
	# day ve. Ba duong deu chan bang _chan(): chi Ke toan, Thu mua, Giam doc.
	"nhap_sao_ke.py": ["danh_sach_tai_khoan", "tai_len", "xem_truoc", "nap"],
	# Thuong thao va dieu chinh hop dong, them 21/08/2026 (bai cua Loan Anh).
	#
	# `ban_chot_cua` CO Y khong nam trong danh sach: no la cong noi bo cho
	# hop_dong_pdf.py hoi truoc khi dung to, khong phai duong app goi. Neu
	# no loi ra day nghia la mot decorator vua bam nham ham.
	"hop_dong_dieu_chinh.py": [
		"chot_dieu_chinh", "cap_nhat_so_lieu", "go_ban_chot", "huy_thuong_thao",
		"lich_su", "mo_thuong_thao", "tai_ban_chot", "tai_ve_ban_chot",
	],
	# Thong bao day, them 20/08/2026.
	# Phieu thanh toan TRUOC cho nha cung cap, them 21/08/2026. Bon cua:
	# ba cua DOC de app bay man hinh, mot cua GHI dung phieu o trang thai
	# nhap. Khong cua nao ghi so, khong cua nao chuyen tien.
	"tra_truoc.py": ["chi_tiet_don", "ds_don_mua", "ds_nguon_tien", "tao_phieu"],
	"thong_bao.py": ["dang_ky", "khoa_cong_khai", "tinh_hinh", "thu_gui"],
	# Tang doi soat SePay dung chung, them 24/08/2026. Ba cua ngo nay phuc vu
	# MOI man co doi soat, nen thieu mot ten la mot man mat nut.
	"doi_soat_sepay.py": ["tu_dong", "ung_vien", "khop_tay"],

	"hoan_tien.py": [
		"chi_tiet", "dem_cho_chi",
		# dinh_unc va hoan_thanh them ngay 19/08/2026: luong KET THUC phieu
		# hoan tien. Truoc do phieu di den "Da doi soat" roi dung mai o do,
		# vi buoc ghi so nam tren Desk chu khong tren man /bep.
		"dinh_unc", "doi_soat", "ds", "ds_ngan_hang",
		# gan_gd_vao them ngay 19/08/2026: gan tay mot khoan tien VAO cho
		# phieu hoan, dung cho ca khach tu go noi dung chuyen khoan nen may
		# khong tu khop duoc (ca Ms.Giang, HT-2026-00912).
		"gan_gd_vao", "hoan_thanh",
		# go_unc them 24/08/2026: nut X tren tung hinh UNC. Chi go duoc khi
		# phieu CHUA ket thuc - ghi so roi thi to do la chung tu cua but
		# toan da nam trong so.
		"go_unc",
		# go_anh_bang_chung them 24/08/2026: nut X tren anh Sales chup. Chi
		# go duoc khi phieu con o "Cho chi" - da chi roi thi tam anh la can
		# cu cua mot lan chi tien that.
		"go_anh_bang_chung",
		# tim_gd_ra va khop_tay them 24/08/2026: khop SePay THU CONG cho
		# dong tien RA. Khac han gan_gd_vao ngay tren, cai do la tien VAO.
		# Ke toan go noi dung tay tren MB Biz nen chi can lech mot chu la
		# phep tu dong khong khop, va phieu nam mai o "Cho chi".
		"tim_gd_ra", "khop_tay",
		# tai_unc them 20/08/2026: Sales xem va tai UNC lam bang chung gui
		# khach. Tep dinh vao Payment Entry ma Sales khong doc duoc doctype
		# do, nen phai co cua rieng kiem quyen theo phieu hoan tien.
		"tai_unc",
		# Noi ma hoa don THAY THE, them 21/08/2026. Ba duong nay chi GHI LAI
		# mot con so nguoi that da doc ben M-Invoice; khong duong nao phat
		# hanh, huy hay thay the mot to hoa don nao.
		"ghi_hddt_thay_the", "go_hddt_thay_the", "can_ghi_thay_the",
		"sepay_tien_ra", "tao",
		# tao_huy_nhap va xem_huy_nhap them 21/08/2026: khach chot banh,
		# chuyen tien, roi huy khi hoa don con nhap. Hai cua nay la loai
		# phieu thu ba, khong khu doanh thu vi don chua tung ghi so.
		"tao_huy_nhap", "tao_tien_du", "thong_tin_chuyen_khoan",
		"tinh_trang", "tu_choi",
		# xuat_excel them ngay 19/08/2026: chi Dung can danh sach hoan tien
		# ra tep de theo doi.
		"xem_huy_nhap", "xem_tien_du", "xuat_excel",
	],
	# M-Invoice trong ma nguon, them 20/08/2026 sau vu sot hoa don dau vao
	# tu 14/08. `dong_bo_tu_dong` va `tu_lanh_hang_dem` la nhip lap lich,
	# khong duoc mo ra ngoai.
	"minvoice_dong_bo.py": ["keo"],
	# `keo_pdf_thieu`, `don_dep_pdf` la nhip lap lich; `dinh_vao_ho_so` la
	# ham noi bo goi tu ho_so_tt. Chi `lay_pdf` mo ra ngoai.
	"minvoice_tep.py": ["lay_pdf"],
	# Tai cau truc BOM bep, them 20/08/2026. Sau cua, cua nao cung co
	# _chan() chi cho quan ly he thong va giam doc.
	"don_bep.py": [
		"lam_tuoi_xem_truoc", "lam_tuoi_thuc_hien",
		"so_che_xem_truoc", "so_che_thuc_hien",
		"trung_xem_truoc", "trung_thuc_hien",
	],
	# SePay, chot danh sach 20/08/2026 khi them duong ACB. `webhook` la
	# diem nhan cua SePay (allow_guest, tu xac thuc bang khoa); cac duong
	# con lai deu qua _kiem_quyen.
	"sepay.py": [
		"dat_hmac", "dat_khoa", "nap_bu", "soi_khoa", "them_tai_khoan",
		"tim_gd_vao", "tinh_trang", "webhook",
	],
	# Ho so nha cung cap, them 21/08/2026 sau khi Uyen khong tao duoc NCC
	# tren app. `tao` ghi mot lan xuong bon bang; cac ham `_gan_*` la ham noi
	# bo, ho ra day nghia la mot decorator vua bam nham.
	"nha_cung_cap.py": ["chi_tiet", "danh_muc", "tao"],
	# Khung danh sach dung chung. Duong `tao_moi` them 21/08/2026 khi anh
	# Viet mo nut Tao moi cho ca 16 danh muc: mot duong ghi duy nhat cho ca
	# khung, va no chi ghi duoc dung nhung truong da khai trong tao()["o"].
	"khung/ds.py": ["chay", "danh_ba", "tao_moi", "tim_lien_ket"],
	# Kiem banh theo mua, khai 21/08/2026 khi them tab San luong theo ngay.
	# Ba duong them_san_luong, sua_san_luong, xoa_san_luong nam ngay canh
	# nhau va ngay tren mot ham cu, tuc dung cho de mot decorator bam nham.
	# v274 them "bang_ngay" va "dat_san_luong" cho tab Co the ban theo ngay.
	# "dat_san_luong" nam ngay canh "danh_dau_dot_ve" trong tep nen day dung
	# la cho de mot decorator bam nham.
	"mua_vu.py": [
		"bang", "bang_ngay", "canh_bao", "danh_dau_dot_ve", "danh_sach",
		"dat_san_luong", "dat_ton_dau", "doi_tinh_trang", "dong_bo",
		"hang_theo_mua", "kiem_truoc_khi_ban", "luu_o", "sua_san_luong", "tao_mua",
		"them_dinh_muc", "them_dong", "them_dot", "them_san_luong", "tim_san_pham",
		"xin_dong_bo", "xoa_dinh_muc", "xoa_dong", "xoa_dot", "xoa_san_luong",
		# Them 28/08/2026: bang doi ruot hop, sua cho may dem sai
		# nhung hop khach xin doi banh ben trong.
		"them_doi_ruot", "xoa_doi_ruot",
	],
	# Goi y so cho phieu YCSX, them 23/08/2026. Mo dun nay CHI DOC, mot cua
	# duy nhat. Them cua thu hai vao day thi phai hoi lai: mot man goi y ma
	# ghi duoc vao he la sai thiet ke.
	"goi_y_ycsx.py": ["goi_y"],
	# So nhan banh dau ngay cua cua hang, them 23/08/2026. Mo dun nay ghi vao
	# SO RIENG, khong dung ton kho ERPNext va khong sinh but toan nao. Them
	# cua moi vao day thi phai tu hoi: cua do co lo dong vao Stock Entry
	# khong. Neu co thi dung lai va hoi anh Viet, vi but toan doi ung cua
	# nhap kho khong nguon di thang vao 632 Gia von hang ban.
	"nhan_banh.py": [
		"bang", "chot_ngay", "dat_ton_dau", "diem_nhan", "ghi_nhan",
		"mon_hay_nhan", "sua_so", "tim_mon", "xoa_mon"
	],
	# Ba mo dun duoi day CHUA duoc chot cho toi 24/08/2026, va do la mot
	# lo hong that: v294 mo bon cua go anh tren chinh chung (go_anh,
	# go_anh_nhan, go_anh_xuat_huy) ma khong co hang rao nao canh. Chen
	# mot ham moi vao giua dong @frappe.whitelist() va dong def cua mot
	# trong cac ham nay se lam ham cu mat quyen goi, Python khong bao,
	# kiem thu khong bao, cong tra ve 0, chi lo khi co nguoi bam nut.
	#
	# van_don.py la mo dun to nhat trong ba: 31 cua, gom ca duong shipper
	# bam va duong webhook cua Aha goi vao.
	"van_don.py": [
		"aha_bao_gia", "aha_dich_vu", "aha_webhook",
		"bo_loc", "book_xe", "canh_bao_thanh_toan",
		"chi_phi_danh_sach", "chi_phi_xuat_excel",
		"chuyen_cua_toi", "chuyen_dang_chay",
		"danh_sach", "doi_soat_cod", "dong_bo_pancake", "ds_shipper",
		"duyet_chi_phi", "gan_anh", "gan_shipper", "giao_loi", "giao_xong",
		# go_anh them 24/08/2026 (v294): nut X tren anh giao va chu ky.
		# Chu ky chan chat hon anh giao, xem TT_GO_DUOC_ANH trong van_don.
		"go_anh",
		"gop_chuyen", "huy_van_don", "khach_khong_ky", "luu_chu_ky",
		"mon_van_don", "nap_mon_thieu", "nhan_don", "phieu_in",
		"tao_chi_phi", "tao_van_don", "xac_nhan_cod",
	],
	# Nhan hang tu nha cung cap. `go_anh_nhan` them 24/08/2026 (v294): anh
	# Viet chot chi chan khi phieu da huy, vi anh chup hang thuong phai
	# chup lai sau khi phat hien chup thieu.
	"nhan_hang.py": [
		"chi_tiet", "danh_sach", "dong_con_lai", "go_anh_nhan",
		"mo_lai", "tao_phieu",
	],
	# Xuat kho: dieu chuyen va xuat huy. `go_anh_xuat_huy` them 24/08/2026
	# (v294), chan khi da ghi so hoac da huy - luc do anh la chung tu.
	"xuat_kho.py": [
		"chi_tiet", "dong_cua_yeu_cau", "ds_phieu", "ghi_so_xuat_huy",
		"go_anh_xuat_huy", "hang_chuyen_ve", "khoi_dong",
		"luu_dieu_chuyen", "luu_xuat_huy", "tim_hang", "xoa_ban_nhap",
		"yeu_cau_cho_chuyen",
	],
	# Doi don vi tinh TRUNG trong BOM sang Qua (them 25/08/2026, v301).
	# `doi_het` GHI VAO BOM that nen chot ky: chi ba cua, khong hon.
	"doi_dvt_bom.py": ["doi_het", "soi_ghi_nham", "sua_ghi_nham", "xem_truoc"],
	"ten_mon.py": ["doi_ten", "xem_truoc"],
	# Tro ly huong dan dung app (26/08/2026). Chi hai cua, va ca hai deu
	# KHONG cham du lieu nghiep vu: `hoi` doc so tay sinh ra tu ma nguon,
	# `bao_loi` chi cam co vao dong nhat ky cua chinh cau tra loi do.
	# `tro_ly_so_tay.py` co y KHONG mo cua nao: no la thu vien noi bo.
	"tro_ly.py": ["bao_loi", "cai_dat", "hoi", "luu_cai_dat"],
	# Huong dan che bien di kem moi BOM (them 25/08/2026, v301).
	"huong_dan_che_bien.py": [
		"chi_tiet", "danh_sach", "luu", "soat_cong_thuc_da_doi",
	],
	# Mang B2B va Tiec, lam theo don khong dinh muc (them 25/08/2026).
	# `xuat_nvl` va `huy_xuat_nvl` GHI THANG vao so kho va so cai, nen
	# danh sach nay chot ky: khong cua nao khac duoc lo ra ngoai.
	"tiec.py": [
		"chi_tiet_tiec", "don_tiec", "huy_xuat_nvl", "lai_lo", "xuat_nvl",
	],
}


def _ten_whitelist(duong_dan):
	"""Doc thang tu MA NGUON, khong nap mo dun. THUAN theo nghia khong chay code.

	Doc bang ast chu khong import: import thi keo theo ca Frappe that, va
	quan trong hon, ham nao bi bam nham decorator thi khi import van chay
	binh thuong nen khong lo ra.
	"""
	cay = ast.parse(io.open(duong_dan, encoding="utf-8").read())
	ten = []
	for nut in cay.body:
		if not isinstance(nut, ast.FunctionDef):
			continue
		for d in nut.decorator_list:
			la_wl = (
				isinstance(d, ast.Call) and getattr(d.func, "attr", "") == "whitelist"
			) or getattr(d, "attr", "") == "whitelist"
			if la_wl:
				ten.append(nut.name)
				break
	return sorted(ten)


@ca("cửa ngõ: từng mô đun mở đúng danh sách hàm đã chốt, không thừa không thiếu")
def _():
	# Ham `dong_bo_so_hddt` PHAI KHONG co trong danh sach: no ghi vao co so
	# du lieu va chi duoc goi tu ben trong. Neu no loi ra day nghia la
	# decorator lai bam nham lan nua.
	for tep, mong in CUA_NGO.items():
		duoc = _ten_whitelist(os.path.join(GOI, tep))
		la("số hàm mở ra ngoài của %s" % tep, len(duoc), len(mong))
		la("đúng danh sách của %s" % tep, duoc, sorted(mong))


@ca("cửa ngõ: hook và nhịp lập lịch của đường thư không được mở ra ngoài")
def _():
	duoc = _ten_whitelist(os.path.join(GOI, "gui_thu.py"))
	# `va_hang_doi_ket` sua du lieu that cua hang doi thu, `bu_nguoi_gui`
	# nam tren duong di cua MOI email trong he. Mo cai thu hai ra ngoai la
	# cho phep goi tu trinh duyet vao dung cho nhay cam nhat.
	dung("bu_nguoi_gui phải nằm ngoài danh sách", "bu_nguoi_gui" not in duoc)
	dung("canh_bao_email_loi phải nằm ngoài danh sách",
		"canh_bao_email_loi" not in duoc)
	dung("ban_webhook phải nằm ngoài danh sách", "ban_webhook" not in duoc)
	dung("va_hang_doi_ket phải nằm trong danh sách", "va_hang_doi_ket" in duoc)
	tt = _ten_whitelist(os.path.join(GOI, "trang_thai_thu.py"))
	dung("danh_dau_cho_gui phải nằm ngoài danh sách", "danh_dau_cho_gui" not in tt)
	dung("soat_tu_dong phải nằm ngoài danh sách", "soat_tu_dong" not in tt)


@ca("cửa ngõ: hàm nội bộ đồng bộ số hoá đơn không được mở ra ngoài")
def _():
	duoc = _ten_whitelist(os.path.join(GOI, "hoan_tien.py"))
	dung("dong_bo_so_hddt phải nằm ngoài danh sách",
		"dong_bo_so_hddt" not in duoc)
	dung("ds phải nằm trong danh sách", "ds" in duoc)
