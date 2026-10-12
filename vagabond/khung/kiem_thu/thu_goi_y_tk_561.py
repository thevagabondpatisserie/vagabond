# -*- coding: utf-8 -*-
"""v561: tài khoản chênh lệch kiểm kê do kế toán chọn, máy gợi ý và nhớ.

Anh Việt chốt 03/10/2026 (bảng duyệt sổ tay, việc số 3): để hết cho kế
toán chọn, máy chỉ gợi ý; kế toán chọn rồi thì máy nhớ, lần sau gợi ý luôn.
Phép THUẦN goi_y_tk / ghi_nho_tk; chuỗi bấm trên app chạy thật ở
hanh_vi/goi_y_tk_561.js.
"""

from vagabond.khung.kiem_thu.nen import ca, gia_lap, la

gia_lap()
from vagabond import kiem_ke as K  # noqa: E402

MD, TAM = "632 - Giá vốn hàng bán - TVD", "Tạm đầu kỳ - TVD"


@ca("v561: chưa chọn lần nào thì gợi ý mặc định của công ty")
def _mac_dinh():
	la("dinh ky", K.goi_y_tk({}, "Kho Bếp - TVD", 0, MD, TAM), (MD, "mac_dinh"))
	la("dau ky", K.goi_y_tk({}, "Kho Bếp - TVD", 1, MD, TAM), (TAM, "mac_dinh"))
	la("khong co gi", K.goi_y_tk(None, None, 0, "", ""), ("", "mac_dinh"))


@ca("v561: nhớ theo kho trước, rồi lần gần nhất ở kho bất kỳ, tồn đầu kỳ nhớ riêng")
def _nho():
	n = K.ghi_nho_tk({}, "Kho Bếp - TVD", 0, "811 - Chi phí khác - TVD")
	la("dung kho", K.goi_y_tk(n, "Kho Bếp - TVD", 0, MD, TAM), ("811 - Chi phí khác - TVD", "lan_truoc_kho"))
	la("kho khac lay lan gan nhat", K.goi_y_tk(n, "Kho Quầy - TVD", 0, MD, TAM), ("811 - Chi phí khác - TVD", "lan_truoc"))
	la("dau ky khong lay so dinh ky", K.goi_y_tk(n, "Kho Bếp - TVD", 1, MD, TAM), (TAM, "mac_dinh"))
	n = K.ghi_nho_tk(n, "Kho Quầy - TVD", 0, "6328 - TVD")
	la("kho bep van giu cua no", K.goi_y_tk(n, "Kho Bếp - TVD", 0, MD, TAM)[0], "811 - Chi phí khác - TVD")
	la("kho quay doi theo lan moi", K.goi_y_tk(n, "Kho Quầy - TVD", 0, MD, TAM)[0], "6328 - TVD")
	n = K.ghi_nho_tk(n, "Kho Bếp - TVD", 1, "Tạm khác - TVD")
	la("dau ky nho rieng", K.goi_y_tk(n, "Kho Bếp - TVD", 1, MD, TAM), ("Tạm khác - TVD", "lan_truoc"))
	la("tk rong khong xoa nho", K.ghi_nho_tk(n, "Kho Bếp - TVD", 0, ""), n)
