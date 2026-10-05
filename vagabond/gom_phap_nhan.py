# -*- coding: utf-8 -*-
"""v575: gom hoá đơn của NHIỀU pháp nhân vào một phiếu đề nghị thanh toán.

VÌ SAO (Loan Anh báo 05/10/2026)
--------------------------------
"Công ty TNHH Oshima's đang có 3 bill, anh Vũ Oshima đang có 10 bill. Em cần
gom chung 2 pháp nhân này để tick chung 13 bill ra chung 1 đề nghị thanh toán."
Trước bản này màn Công nợ chỉ cho tick và gom trong một khách.

CÁCH LÀM
--------
Phiếu vẫn có MỘT khách đứng tên (ô Kính gửi, người nhận email), là một trong
các khách có hoá đơn trong phiếu. Mỗi dòng phiếu ghi thêm khách của chính hoá
đơn đó. Phiếu thu khi tiền về vẫn lập theo từng hoá đơn với đúng khách của hoá
đơn (thu_tien.ghi_thu_tien đọc customer của hoá đơn), nên sổ công nợ từng pháp
nhân vẫn đúng.

Tệp này THUẦN, không chạm Frappe, để kiểm được không cần site. Không import
cong_no ở đây: cong_no kéo ban_hang, ban_hang kéo requests (bài học 20/08).
"""


def chu_no(customer, khach_no):
	"""Khách thật đang nợ hoá đơn. THUẦN.

	Kế toán gán lại chủ nợ sau khi ghi sổ thì ô vgb_khach_no ưu tiên hơn
	customer, cùng phép với ds_khach_no và tao_phieu từ trước."""
	return (khach_no or "").strip() or (customer or "").strip()


def kiem_khach(khach, chu_cac_hd, nhieu_khach=False):
	"""Kiểm khách đứng tên và chủ của từng hoá đơn khi gom. THUẦN.

	khach        khách đứng tên phiếu.
	chu_cac_hd   danh sách (mã hoá đơn, khách nợ) theo đúng thứ tự tick.
	nhieu_khach  người dùng đã chọn gom chung nhiều khách.

	Trả về (lỗi, các khách theo thứ tự xuất hiện). Có lỗi thì không lập phiếu.
	"""
	khach = (khach or "").strip()
	if not khach:
		return "Chưa chọn khách đứng tên phiếu.", []
	cac = []
	for ten_hd, chu in chu_cac_hd or []:
		chu = (chu or "").strip()
		if not chu:
			return "Hoá đơn %s chưa có khách hàng." % ten_hd, []
		if chu != khach and not nhieu_khach:
			return "Hoá đơn %s không phải của khách này." % ten_hd, []
		if chu not in cac:
			cac.append(chu)
	if khach not in cac:
		# Gom chung thì khách đứng tên phải là một trong các khách có hoá
		# đơn trong phiếu: đứng tên một khách ngoài cuộc là đòi nhầm người.
		return "Khách đứng tên phiếu phải có ít nhất một hoá đơn trong phiếu.", []
	return "", cac


def khach_dong(khach_dong_luu, khach_phieu):
	"""Khách của một dòng phiếu. THUẦN.

	Phiếu lập trước v575 không ghi khách từng dòng: khi đó cả phiếu là một
	khách, chính là khách đứng tên. Không sửa dữ liệu cũ."""
	return (khach_dong_luu or "").strip() or (khach_phieu or "").strip()


def gom_theo_khach(dong, khach_phieu):
	"""Cộng số hoá đơn và số tiền theo khách, giữ thứ tự xuất hiện. THUẦN.

	dong: danh sách dict có khach, ten_khach, so_tien.
	"""
	ra, vi_tri = [], {}
	for d in dong or []:
		k = khach_dong(d.get("khach"), khach_phieu)
		if k not in vi_tri:
			vi_tri[k] = len(ra)
			ra.append({"khach": k, "ten": d.get("ten_khach") or k, "so_hd": 0, "tien": 0.0})
		o = ra[vi_tri[k]]
		o["so_hd"] += 1
		o["tien"] += float(d.get("so_tien") or 0)
	return ra
