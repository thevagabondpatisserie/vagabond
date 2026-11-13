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

from vagabond.khung.kiem_thu import thu_cach_ly_243
from vagabond.khung.kiem_thu import nen  # noqa: E402

# Cai ban Frappe gia TRUOC khi nap bat ky mo dun nghiep vu nao. Neu doi thu
# tu nay thi mo dun nghiep vu se doi Frappe that va no ngay.
nen.gia_lap()
from vagabond.khung.kiem_thu import thu_tra_lai_app_339, thu_app_gui_fin

from vagabond.khung.kiem_thu import (  # noqa: E402,F401
	thu_tuyen_dung_622, thu_tuyen_dung_625, thu_anh_tuyen_dung_630, thu_hoan_ung_noi_bo_502, thu_nan_gia_dong_618, thu_the_flex_618, thu_dat_ban_301, thu_dat_ban_630, thu_thanh_vien_300, thu_noi_dung_web, thu_dat_ban_web, thu_ra_phantom_303,
	thu_combo_261, thu_can_tru_262, thu_ghi_so_266, thu_su_co_290, thu_luu_duyet_296,
	thu_doi_chieu_app_247, thu_doi_chieu_252, thu_dong_bo_227, thu_dong_bo_thong_bao, thu_minvoice_352, thu_go_tay_358, thu_ht_unc_518, thu_gram_bom_252, thu_tk_dich_vu_252, thu_do_chinh_xac_mua_259,
	thu_bang_gia_nhap, thu_minvoice_227, thu_link_thue_227, thu_bao_ve_hddt_225, thu_cong_cu_tang_cloud,
	thu_hang_tang_so_cai, thu_mua_hddt_227, thu_quyen_cong_thuc_498, thu_thue_vnd, thu_tra_truoc_500, thu_cua_thue_243, thu_kho_tang_243,
	thu_bao_cao_don_nhap,
	thu_bo_doctype, thu_bom_note_va_nut_huong_dan, thu_bom_excel_lich_su_593, thu_bo_sao_ke_469, thu_phan_con_595,
	thu_ca_moi_diem, thu_cai_dat_web_va_in_store, thu_card_khong_la_flex, thu_chan_man, thu_chi_loi_qz, thu_chot_ca_tien_mat_296,
	thu_chon_pt_moi_man,
	thu_chon_ncc,
	thu_chon_luong,
	thu_man_danh_sach_hoso,
	thu_cua_ngo, thu_cuon_va_o_tim,
	thu_de_nghi_chi, thu_ttnb_317, thu_dien_giai, thu_dinh_kem_go,
	thu_diem_ban_va_chiem,
	thu_dinh_tuyen_ngan_hang, thu_sepay_mb_247,
	thu_phi_book_app,
	thu_doi_soat_sepay, thu_don_du_lieu, thu_don_huy, thu_don_rac_tep,
	thu_don_dep_db_284,
	thu_don_vi_in_qz,
	thu_ds,
	thu_trang_dat_banh,
	thu_don_web_367,
	thu_giao_viec_609, thu_tin_kho_609,
	thu_ton_don_web_593, thu_giu_ton_web_476,
	thu_nhan_web_532, thu_chu_web_367, thu_web_vue, thu_web_597, thu_zalo_khong_nhom_597, thu_the_pancake_598, thu_nut_web_598, thu_bien_nhan_vue_484, thu_trao_vue_601, thu_trao_vue_603,
	thu_trang_www_532b,
	thu_buoc_hoa_don_mua,
	thu_nghiep_vu_tien,
	thu_chip_man_vagabond,
	thu_cot_huy_kiem_banh,
	thu_dung_lai_hddt,
	thu_duong_app,
	thu_duyet_ycmh,
	thu_dvt_mua,
	thu_dvt_trung_va_huong_dan,
	thu_gac_don_vi,
	thu_gac_thu_ncc,
	thu_duyet_chi,
	thu_ghep_hop_theo_ruot,
	thu_ghi_so_dieu_kien,
	thu_giam_doc_va_giao_dien,
	thu_giao_dien_xuat_huy_va_tro_ly,
	thu_goi_y_ycsx,
	thu_gui_thu,
	thu_hang_tang, thu_tang_tra_truoc_607, thu_uu_dai_hang_607, thu_kho_phu_trach_607, thu_hddt_bu, thu_hddt_cho_xuat, thu_hddt_dung_ngay_527, thu_doi_soat_hddt_ra_527, thu_ma_ke_toan_536, thu_lo_theo_ngay_phieu_540, thu_gsm_lam_tron_543, thu_hach_toan_kho_542, thu_tat_lo_545, thu_go_dat_hang_545, thu_tru_kho_bu_550, thu_gia_von_kiem_ke_547, thu_kiem_ke_472, thu_ngay_ban_573,
	thu_nguyen_tac_man_hinh,
	thu_kho_sap,
	thu_o_cai_dat,
	thu_hoa_don_am, thu_hoa_don_vat, thu_hoan_tien_noi_dung, thu_hoan_ung_v279, thu_hop_dong,
	thu_hop_dong_thu_tien, thu_hop_qua,
	thu_huy_don_nhap, thu_ke_toan_mua,
	thu_in_ngam_va_khong_quan_ton,
	thu_dia_chi_xhd,
	thu_ke_hoach_sx,
	thu_giam_doc_sua_huy,
	thu_kho_rut_tuot,
	thu_kpi,
	thu_khuon_thu_dien_tu,
	thu_khach_tren_don, thu_kho_san_xuat, thu_xuat_kho_them, thu_qr_chuyen_khoan_474, thu_qr_xhd_cfd_push, thu_khoa_va_tim_hang, thu_may_in_qz, thu_kiem_that, thu_lan_nhan, thu_lo_hang, thu_lo_het_han_v406, thu_luat, thu_luat_thanh_toan, thu_ma_bill_va_khop_tien, thu_ma_cap_so, thu_ma_vach, thu_mau_in, thu_mau_in_quay, thu_ton_ngay_mai,
	thu_loai_chung_tu_dung_chung,
	thu_lech_mot_dong_502,
	thu_minvoice_chung_tu,
	thu_mo_lai_ngay_va_gan_nguoi_ban,
	thu_mua_dich_vu, thu_mua_vu_ngay,
	thu_ngay_don_mua,
	thu_ngay_pancake, thu_nhip_pancake_va_tat_web,
	thu_nguoi_ban_va_kiem_kho,
	thu_nhan_banh, thu_nhan_nvl_chon_lo, thu_nha_cung_cap, thu_phantom, thu_phieu_chi_va_cuon,
	thu_nvl_thay_the,
	thu_phieu_hoan_huy,
	thu_phong_moi_to,
	thu_qua_tang_hoa_don,
	thu_quyen_ap, thu_tien_ca, thu_tim_ncc, thu_tinh,
	thu_san_xuat_v402, thu_san_xuat_206,
	thu_tai_khoan_chi_phi,
	thu_san_xuat_v409, thu_viec_can_lam_v410, thu_ho_so_tt_v413, thu_ho_so_tt_v416, thu_ho_so_tt_v445,
	thu_san_xuat_v403,
	thu_sdt_boc,
	thu_ho_so_bo_sung,
	thu_chip_ho_so_tt, thu_phan_bo_app,
	thu_siet_hoan_ung,
	thu_tang_qua,
	thu_ten_mon,
	thu_ten_nguoi_va_tu_khai,
	thu_tep_dinh_kem,
	thu_thanh_toan_nhieu,
	thu_tiec_b2b,
	thu_tk_kho_va_ghi_so,
	thu_tk_nhan_hoan_ung,
	thu_hoan_ung_sao_ke_642,
	thu_ton_chang,
	thu_tra_truoc,
	thu_tra_truoc_hien_tren_app,
	thu_trang_web,
	thu_tro_ly,
	thu_so_tay_554,
	thu_tro_ly_cho_556,
	thu_tem_lenh_560,
	thu_goi_y_tk_561,
	thu_gom_nhom_565,
	thu_cai_dat_568,
	thu_cai_dat_loi_570,
	thu_bo_ao_564,
	thu_mo_khoa_558,
	thu_unc_va_tk_chi, thu_thu_ncc,
	thu_xuat_phuc_vu_ban, thu_stk_ncc_509, thu_phi_giao_510, thu_sua_ma_332, thu_kho_dich_512, thu_tra_ton_513, thu_stk_tai_cho_515, thu_bang_sang_351,
	thu_ux_chi_dot_can_coc,
	thu_vai_cua_hang,
	thu_dat_banh,
	thu_quan_ly_nguoi_dung,
	thu_pickup,
	thu_noi_hoa_don_van_don,
	thu_dong_bo_237,
	thu_keo_chi_co_ma_519,
	thu_dem_that_520,
	thu_v523,
	thu_v524,
	thu_v526,
	thu_tra_truoc_528,
	thu_noi_hd_sau_530,
	thu_so_hd_that_531,
	thu_ban_soan_do_533,
	thu_cong_cu_ds_534, thu_cong_no_ncc, thu_tra_truoc_ncc_551, thu_but_toan_552, thu_thay_the_khong_lo_552, thu_kenh_zalo_562, thu_zalo_nhom_591,
	thu_tien_ich_528,
	thu_staging_257,
	thu_day_ma_pancake, thu_day_pancake_hanh_vi,
	thu_thu_tien,
	thu_cong_no_571,
	thu_gom_phap_nhan_575,
	thu_khop_tay_577,
	thu_goi_nhieu_582,
	thu_tim_kiem_583,
	thu_bien_tap_theo_the_586,
	thu_xhd_khong_mst_456, thu_xhd_dong_bo_khong_de_595,
	thu_uu_dai_web_589,
	thu_bo_phan_583,
	thu_van_don_dieu_chuyen,
	thu_van_don_man_ds,
	thu_viec_can_lam,
	thu_xung_ho,
	thu_tai_khoan_btp_307,
	thu_luoi_do_nhom_307,
	thu_doi_soat_nguon,
	thu_doi_soat_tep,
	thu_doi_soat_mau_579,
	thu_doi_soat_khop_579,
	thu_doi_soat_thu_641,
	thu_zalo_phat_hanh_585,
	thu_kho_quyen_585,
	thu_gia_von_tam,
	thu_chuoi_tung_don_602,
	thu_tin_zalo_604,
	thu_ahamove_url_608,
	thu_doi_soat_ck_610,
	thu_ten_mien_605,
	thu_zalo_bot_hai_606,
	thu_len_web_606,
	thu_bao_cao_chu_606,
	thu_dat_ban_zalo_611, thu_tin_zalo_613,
	thu_crm_614, thu_crm_dot2_617,
	thu_greensm_612,
	thu_gon_version_619,
	thu_dong_mon_giu_ten_619,
	thu_lien_ket_app_619,
	thu_tin_hao_hut_619,
	thu_chuong_619,
	thu_fbc_620,
	thu_zalo_kich_ban_621,
	thu_thanh_vien_621,
	thu_voucher_tv_623,
	thu_tai_chinh_626,
	thu_tai_chinh_627,
	thu_tin_tai_chinh_628,
	thu_quy_tien_mat_628,
	thu_quy_chot_dau_635,
	thu_ba_ca_bill_quay_628,
	thu_tuyen_dung_631,
	thu_diem_ban_631,
	thu_onepay_633,
	thu_onepay_634,
	thu_onepay_dat_637,
	thu_thiet_ke_rieng_630,
	thu_banh_si_630,
	thu_codex_531,
	thu_dau_trang_636,
	thu_zalo_oa_638,
	thu_thanh_toan_web_638,
	thu_gioi_thieu_638,
	thu_goi_mon_ban_638,
	thu_bien_tap_menu_640,
	thu_so_do_web_643,
	thu_kiem_banh_dung_643,
	thu_zalo_phat_hanh_643,
	thu_uu_dai_ban_643,
	thu_doi_soat_643,
	thu_doi_soat_644,
	thu_banh_web_644,
	thu_thanh_toan_the_645,
	thu_don_dau_web_645,
	thu_uu_dai_vue_645,
	thu_anh_menu_645,
	thu_don_dau_cai_dat_645,
	# v645 đợt 4: ưu đãi tự động qua Zalo, đền bù, mã của khách tại quầy.
	thu_zalo_uu_dai_645,
	# Codex PR 548 b4b18d5: câu SQL thật của zalo_kich_ban chạy trên sqlite.
	thu_zalo_645_sql,
	# Anh Việt 08/11/2026: mỗi bản deploy phải kèm mục sổ tay.
	thu_so_tay_phien_ban_645,
	# v646 bếp Pastry: Đếm hôm nay chia lặp 10 món khi phiếu chờ duyệt.
	thu_kiem_ke_xoay_646,
	# v646 Cài đặt tự động hoá: việc máy soạn sẵn, nhịp 15 phút, quá hạn báo một lần.
	thu_viec_tu_dong_646,
	# v653 Dự chi công nợ: đợt trả nhà cung cấp 10 và 20, duyệt cả đợt, máy lập APP.
	thu_du_chi_653,
	# v653 Nhật ký BTP sẵn, Đủ decor (sự cố Tira 18cm), lưu một dòng có khoá.
	thu_nhat_ky_btp_653,
	# v653 WhatsApp đường phụ cho mã xác thực và ưu đãi (Zalo trước).
	thu_whatsapp_653,
	# v653 tin Zalo Bánh có sẵn hôm nay kèm ảnh bánh và số lượng.
	thu_banh_co_san_653,
	# v654 tin Bánh có sẵn chỉ gửi khi số bán được đổi (dấu nằm trong sổ tin).
	thu_banh_co_san_654,
	# v653 tự đính hoá đơn nhà cung cấp từ hộp thư hoadon@ (chỉ đọc).
	thu_hoa_don_thu_653,
	# v654 hoá đơn mua vào tự nhận XML, PDF: thư mới nhất trước, thư gửi lại, quét lại.
	thu_hoa_don_thu_654,
	# v654 gọi đúng tên bộ phận Thu mua thay cho tên người trên màn và tin.
	thu_thu_mua_654,
	# v654 Lịch dự chi: dự chi tay, tự xếp theo hạn, tiền khả dụng theo ngày, lịch hằng tháng.
	thu_lich_du_chi_654,
	thu_de_xuat_cong_thuc_656,
	thu_banner_647,
	# v647 đối soát ShopeeFood báo lệch sai: tiền đúng kỳ, dò lại mỗi giờ.
	thu_tien_ve_dung_ky_647,
	# v647 (anh Việt 10/11/2026): từng bill thẻ/sàn dò ngược trong báo cáo đối tác.
	thu_bill_doi_tac_647,
	# v648 (anh Việt chốt 11/11/2026, phương án C): Hoàn tất món chính, máy tự làm cấp 1, cấp 2 còn thiếu.
	thu_tu_lam_cap_duoi_648,
	thu_xin_kho_tong_655,
	thu_thieu_nvl_650,
	thu_thue_mua_650,
	# v650 (anh Việt cho phép 12/11/2026): dọn dòng 33311 tự thêm trên chứng từ mua cũ.
	thu_bo_thue_cu_650,
	# v648: bill sàn ghi khuyến mại hoặc thực nhận không còn bị báo Lệch tiền sai.
	thu_tien_bill_san_648,
	# v647 tên bàn theo khu (A1, B1, VIP1), in QR bàn đúng branding.
	thu_qr_ban_khu_647,
	# v646 (Minh Vũ 09/11/2026): tham số mẫu Zalo thật, ô Tiền tệ -1124.
	thu_zalo_mau_646,
	# v646 Refill (bếp báo sau vụ Roman 18 đặt xa ngày, anh Việt duyệt 09/11).
	thu_refill_646,
	# v649 đối soát GrabFood: phí quảng cáo không mã, đơn mã dài ngắt dòng (site thật 10/11).
	thu_doi_soat_grab_649,
	thu_doi_soat_grab_651,
	thu_doi_soat_lich_651,
	thu_doi_soat_arc_651,
	# v652 ảnh, mô tả bánh trên tủ ở Biên tập menu (Minh Vũ, anh Việt 12/11).
	thu_banh_menu_652,
	# v652 điểm thành viên trên web, nhân điểm, thể lệ, hoàn điểm (anh Việt 12/11).
	thu_diem_web_652,
	# v649 màn Lệnh sản xuất: thẻ gọn, câu chặn kiểm kê ghi số phiếu (ảnh anh Việt 11/11).
	# v655 kho phương án B (bếp xin kho tổng, kho giao thực tế) và đối soát OnePay theo số đơn.
	thu_doi_soat_onepay_655,
	thu_lenh_sx_649,
	thu_tru_vo_btp_649,
	thu_dat_truoc_tu_mai_649,
	thu_giu_vo_da_lam_649,
)


def main():
	im = "-im" in sys.argv
	print("Bộ kiểm thử tầng khung Vagabond")
	print("Ngày cố định trong mọi ca: %s" % nen.HOM_NAY)
	print("")
	return 1 if nen.chay_het(im=im) else 0


if __name__ == "__main__":
	sys.exit(main())
