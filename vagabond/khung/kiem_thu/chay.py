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
	thu_chi_loi_qz,
	thu_cua_ngo, thu_de_nghi_chi, thu_dien_giai, thu_don_du_lieu, thu_don_huy,
	thu_ds,
	thu_gui_thu,
	thu_hoa_don_am, thu_hoan_ung_v279, thu_hop_dong, thu_hop_qua, thu_huy_don_nhap, thu_ke_toan_mua,
	thu_kho_san_xuat, thu_may_in_qz, thu_kiem_that, thu_lo_hang, thu_luat, thu_ma_vach, thu_mau_in,
	thu_mua_dich_vu, thu_mua_vu_ngay,
	thu_nha_cung_cap, thu_phantom, thu_phieu_chi_va_cuon, thu_quyen_ap, thu_tien_ca, thu_tim_ncc, thu_tinh,
	thu_siet_hoan_ung,
	thu_tra_truoc,
)


def main():
	im = "-im" in sys.argv
	print("Bộ kiểm thử tầng khung Vagabond")
	print("Ngày cố định trong mọi ca: %s" % nen.HOM_NAY)
	print("")
	return 1 if nen.chay_het(im=im) else 0


if __name__ == "__main__":
	sys.exit(main())
