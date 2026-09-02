"""Diem vao cua bo kiem thu.

    python3 vagabond/khung/kiem_thu/chay.py        chay het, in tung ca
    python3 vagabond/khung/kiem_thu/chay.py -im    chi in ca hong

Tra ve ma loi 0 neu dat het, khac 0 neu co ca hong - de sau nay ghep vao
buoc kiem truoc khi deploy.
"""

import os
import sys

# Cho phep chay tep nay tu bat ky thu muc nao.
GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))
if GOC not in sys.path:
	sys.path.insert(0, GOC)

from vagabond.khung.kiem_thu import nen  # noqa: E402

# Cai ban Frappe gia TRUOC khi nap bat ky mo dun nghiep vu nao. Neu doi thu
# tu nay thi mo dun nghiep vu se doi Frappe that va no ngay.
nen.gia_lap()

from vagabond.khung.kiem_thu import (  # noqa: E402,F401
	thu_bang_gia_nhap,
	thu_bao_cao_don_nhap,
	thu_bo_doctype, thu_bom_note_va_nut_huong_dan,
	thu_ca_moi_diem, thu_card_khong_la_flex, thu_chan_man, thu_chi_loi_qz,
	thu_chon_pt_moi_man,
	thu_cua_ngo, thu_cuon_va_o_tim,
	thu_de_nghi_chi, thu_dien_giai, thu_dinh_kem_go,
	thu_diem_ban_va_chiem,
	thu_dinh_tuyen_ngan_hang,
	thu_doi_soat_sepay, thu_don_du_lieu, thu_don_huy, thu_don_rac_tep,
	thu_don_vi_in_qz,
	thu_ds,
	thu_dung_lai_hddt,
	thu_duong_app,
	thu_duyet_ycmh,
	thu_dvt_mua,
	thu_dvt_trung_va_huong_dan,
	thu_gac_don_vi,
	thu_gac_thu_ncc,
	thu_ghep_hop_theo_ruot,
	thu_ghi_so_dieu_kien,
	thu_giam_doc_va_giao_dien,
	thu_giao_dien_xuat_huy_va_tro_ly,
	thu_goi_y_ycsx,
	thu_gui_thu,
	thu_hang_tang,
	thu_hoa_don_am, thu_hoa_don_vat, thu_hoan_tien_noi_dung, thu_hoan_ung_v279, thu_hop_dong,
	thu_hop_dong_thu_tien, thu_hop_qua,
	thu_huy_don_nhap, thu_ke_toan_mua,
	thu_ke_hoach_sx,
	thu_kho_rut_tuot,
	thu_kpi,
	thu_khach_tren_don, thu_kho_san_xuat, thu_xuat_kho_them, thu_khoa_va_tim_hang, thu_may_in_qz, thu_kiem_that, thu_lo_hang, thu_luat, thu_luat_thanh_toan, thu_ma_bill_va_khop_tien, thu_ma_vach, thu_mau_in, thu_mau_in_quay,
	thu_loai_chung_tu_dung_chung,
	thu_minvoice_chung_tu,
	thu_mua_dich_vu, thu_mua_vu_ngay,
	thu_ngay_don_mua,
	thu_ngay_pancake, thu_nhip_pancake_va_tat_web,
	thu_nguoi_ban_va_kiem_kho,
	thu_nhan_banh, thu_nha_cung_cap, thu_phantom, thu_phieu_chi_va_cuon,
	thu_nvl_thay_the,
	thu_phieu_hoan_huy,
	thu_phong_moi_to,
	thu_qua_tang_hoa_don,
	thu_quyen_ap, thu_tien_ca, thu_tim_ncc, thu_tinh,
	thu_sdt_boc,
	thu_siet_hoan_ung,
	thu_tang_qua,
	thu_ten_mon,
	thu_ten_nguoi_va_tu_khai,
	thu_tep_dinh_kem,
	thu_thanh_toan_nhieu,
	thu_tiec_b2b,
	thu_tk_kho_va_ghi_so,
	thu_tk_nhan_hoan_ung,
	thu_ton_chang,
	thu_tra_truoc,
	thu_trang_web,
	thu_tro_ly,
	thu_unc_va_tk_chi,
	thu_vai_cua_hang,
	thu_viec_can_lam,
	thu_xung_ho,
)


def main():
	im = "-im" in sys.argv
	print("Bộ kiểm thử tầng khung Vagabond")
	print("Ngày cố định trong mọi ca: %s" % nen.HOM_NAY)
	print("")
	return 1 if nen.chay_het(im=im) else 0


if __name__ == "__main__":
	sys.exit(main())
