# -*- coding: utf-8 -*-
"""Phí giao thu của khách: MỘT dòng, số lượng 1, đơn giá bằng số tiền.

Loan Anh 18/09/2026: *"cái phí vận chuyển chỉ được tăng số lượng chứ không
được tăng đơn giá, nếu đúng là phải chỉnh đơn giá chứ k phải tăng số lượng
để khi xuất hoá đơn mới đúng"*. Bên Pancake bấm 1.000 đ x 4, sang app thì
món "Phí Dịch Vụ Vận Chuyển" nằm trong danh mục với giá 1.000 đ, thu ngân
chỉ có nút cộng số lượng nên bill ra "4 x 1.000". Hoá đơn điện tử chép y
nguyên dòng đó là sai bản chất: phí giao là một khoản, không phải bốn cái.

Tệp này KHÔNG import Frappe. Mọi đường ghi hoá đơn (lập đơn tay, sửa bill)
đều gọi `gom` trước khi ghi, nên dù màn nào gửi phí giao theo kiểu gì, vào
sổ vẫn là một dòng qty 1.
"""

MA_PHI_GIAO = "DVBH00001"


def _so(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def la_phi_giao(ma):
	return (ma or "").strip().upper() == MA_PHI_GIAO


def gom(rows, phi_ship=0):
	"""Gom mọi dòng phí giao trong `rows` cộng với `phi_ship` thành đúng một dòng.

	- Dòng phí giao gửi dạng qty 4 x 1.000 thành qty 1 x 4.000.
	- Nhiều dòng phí giao thì cộng dồn.
	- Ô phí giao riêng (`phi_ship`) cộng chung vào.
	- Tổng bằng 0 thì không có dòng phí giao nào.
	- Các dòng khác giữ nguyên thứ tự; dòng phí giao đặt cuối.
	Giữ description/tên dòng của dòng phí giao đầu tiên (nếu có) để màn sửa
	bill không mất neo.
	"""
	khac, tong, mau = [], _so(phi_ship), None
	for r in rows or []:
		if la_phi_giao(r.get("item_code")):
			tong += _so(r.get("qty")) * _so(r.get("rate"))
			if mau is None:
				mau = r
		else:
			khac.append(r)
	if tong <= 0:
		return khac
	d = dict(mau) if mau else {}
	for k in ("amount", "base_amount", "base_rate", "net_amount", "net_rate", "base_net_amount", "base_net_rate", "stock_qty"):
		d.pop(k, None)
	d.update({"item_code": MA_PHI_GIAO, "qty": 1, "rate": tong})
	khac.append(d)
	return khac
