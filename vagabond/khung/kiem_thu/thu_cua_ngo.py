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
	],
	# Duong thu di, them 21/08/2026 sau su co ca tiem khong gui duoc email.
	# `bu_nguoi_gui` va `canh_bao_email_loi` KHONG duoc co mat o day: mot cai
	# la hook nam tren duong di cua MOI email trong he, mot cai la nhip lap
	# lich. Ho ra thi la decorator vua bam nham.
	"gui_thu.py": ["cuu_su_co_1608", "suc_khoe", "va_hang_doi_ket"],
	# Luong dong tien, them 21/08/2026: ca lam viec tai quay va phieu nop
	# quy. Cac ham _doanh_thu_he_thong, _ca_dang_mo la noi bo, khong mo.
	"ca_quay.py": ["chi_tiet", "chot_ca", "danh_sach", "mo_ca", "tinh_trang"],
	"nop_quy.py": ["ca_cho_nop", "chi_tiet", "danh_sach", "ky_giao", "ky_nhan",
		"tao", "xuat_excel", "xuat_pdf"],
	# Trang thai gui thu tren chung tu. `danh_dau_cho_gui` la hook va
	# `soat_tu_dong` la nhip lap lich, ca hai chay tu ben trong.
	"trang_thai_thu.py": ["soat_lai", "tinh_trang"],
	# Chuyen BTP cap 1 sang Phantom, them 21/08/2026. `chuyen` mac dinh chi
	# chay thu; phai truyen chay_that=1 moi ghi.
	"phantom.py": ["chung_tu_thu", "chuyen", "dong_lenh", "trang_thai",
		"xem_truoc"],
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
	"don_huy.py": ["bo_qua", "dem_cho_hoan", "dong_bo", "ds", "tao_hoan",
		"xem_hoan", "xuat_excel"],
	# Cay kho bon chang, them 21/08/2026. `gan_kho_nguon` la hook validate
	# cua Work Order nen KHONG whitelist.
	"kho_san_xuat.py": ["dung_cay_kho", "gan_nguoi_phu_trach", "soat_chang"],
	# Tuy bien ruot hop qua, them 21/08/2026.
	"hop_qua.py": ["mon_thay_the", "ruot_goc", "xem_tuy_bien"],
	# Ham don o email: `don` va `ghi_vet` la hook, chi `kiem` mo ra ngoai.
	"email_sach.py": ["kiem"],
	# Man Viec can lam, them 20/08/2026: gom viec va LOC THEO VAI o may chu.
	# Truoc do man nay gom viec ngay tren may khach va phan lon khong loc vai.
	"viec_can_lam.py": ["danh_sach"],
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
		"dat_san_luong", "doi_tinh_trang", "dong_bo",
		"hang_theo_mua", "kiem_truoc_khi_ban", "luu_o", "sua_san_luong", "tao_mua",
		"them_dinh_muc", "them_dong", "them_dot", "them_san_luong", "tim_san_pham",
		"xin_dong_bo", "xoa_dinh_muc", "xoa_dong", "xoa_dot", "xoa_san_luong"
	],
	# Goi y so cho phieu YCSX, them 23/08/2026. Mo dun nay CHI DOC, mot cua
	# duy nhat. Them cua thu hai vao day thi phai hoi lai: mot man goi y ma
	# ghi duoc vao he la sai thiet ke.
	"goi_y_ycsx.py": ["goi_y"],
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
