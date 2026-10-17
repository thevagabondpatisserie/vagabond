"""Chọn ảnh bánh cho trang đặt bánh: MỘT hàm cho mọi nhánh (#367).

Vì sao có tệp này
-----------------
Marketing (Minh Vũ) muốn tự tải ảnh bánh ở hồ sơ món trên ERP, không phải
nhờ Sales sửa bên Pancake. Nhưng trước 25/09/2026 bốn nhánh trả ảnh cho web
mỗi nhánh tự chọn một kiểu, và cả bốn đều để ảnh Pancake đè lên ảnh ERP:

  - tab Có sẵn hôm nay   (`kiem_banh.co_the_ban_hom_nay`)
  - tab Đặt bánh trước   (`kiem_banh._dat_truoc_theo_decor`)
  - tab In store         (`kiem_kho.con_tren_quay_web`)
  - tab In season        (`mua_vu.hang_theo_mua`)

Cái sau cùng còn tệ hơn: nhánh hôm nay đọc `d.hinh or Item.image` rồi
`_bo_anh_mo_ta` đè lại bằng ảnh Pancake, nên có sửa ảnh ERP cũng vô ích.
Không có ảnh nào thì thẻ bánh hiện một ô đen.

Thứ tự đã chốt trong #367: ảnh hồ sơ món ERP, rồi ảnh Pancake, rồi ảnh lưu
trong dòng kiểm bánh (cũng là ảnh Pancake chụp lại lúc kéo đơn), rồi ảnh nền
thương hiệu. Không nhánh nào được tự viết lại thứ tự này; ca kiểm
`thu_don_web_367.py` quét chặn.

Ngày 12/10/2026, Hannari lại hiện bộ ảnh Pancake cũ vì tệp
`sp-<mã>*` do máy chép vào Item bị nhầm là ảnh ERP người chọn. Tệp
chép vẫn là dự phòng khi Pancake không trả ảnh, nhưng không được đè
bộ ảnh Pancake đang sống. Ảnh Item không theo mẫu này vẫn đứng đầu.

Ngày 17/10/2026 (v601), Hannari vẫn hiện ảnh sai: Item BAWC00024 (16cm)
mang tệp `sp-bawc00098...` chép từ mã 18cm. Nhóm đặt trước chỉ gồm các size
đang có số (12 và 16cm), nên cách nhận tệp chép theo đúng mã trong nhóm bỏ
sót tệp của mã 18cm và coi nó là ảnh người chọn, đưa lên đầu. Từ nay mọi tệp
`sp-<mã hàng>*` (đúng mẫu tên đối soát đặt, xem doi_soat.py) đều là bản chép,
bất kể mã nào.

Hàm THUẦN, không chạm Frappe.
"""

import os
import re
from urllib.parse import urlsplit

ANH_NEN = "/assets/vagabond/web_order/anh-bia.png"
SO_ANH_TOI_DA = 5


def anh_cong_khai(u):
	"""Chỉ đường dẫn khách mở được. Ảnh /private cần đăng nhập nên bỏ."""
	u = str(u or "").strip()
	if not u or u.startswith("/private") or "/private/files/" in u:
		return ""
	return u


# Tên tệp đối soát đặt: "sp-<mã hàng viết thường>.<đuôi>", Frappe trùng tên thì
# chèn thêm chuỗi băm hex (vd. sp-bawc00098565623.jpg, sp-bawc00023a1227d.jpg).
MAU_TEP_CHEP = re.compile(r"^sp-[a-z]{2,8}[0-9]{3,}(?:[^a-z0-9]|[a-f0-9]{6,})")


def la_anh_pancake_da_chep(u, ma_hang=None):
	"""Nhận tệp `sp-<mã hàng>*` do đối soát chép vào Item, của BẤT KỲ mã nào.

	Dữ liệu cũ có Item dùng chung tệp chép của một size khác, kể cả size không
	nằm trong nhóm đang xét (Hannari 16cm mang tệp của 18cm). `ma_hang` giữ
	lại cho các nơi gọi cũ, không còn dùng để lọc.
	"""
	ten = os.path.basename(urlsplit(str(u or "").strip()).path).lower()
	return bool(MAU_TEP_CHEP.match(ten))


def chon_anh(anh_erp=None, anhs_pancake=(), anh_dong=None, nen=ANH_NEN, ma_hang=None):
	"""Trả (ảnh chính, danh sách ảnh tối đa 5) theo đúng thứ tự đã chốt.

	`anh_erp` có thể là một chuỗi hoặc một danh sách (một nhóm bánh gom nhiều
	size, mỗi size một hồ sơ món). Ảnh trùng chỉ giữ một lần. Không có ảnh
	nào thì trả ảnh nền thương hiệu, không bao giờ trả rỗng.
	"""
	ds = []
	erp = anh_erp if isinstance(anh_erp, (list, tuple)) else [anh_erp]
	erp_tay = [u for u in erp if not la_anh_pancake_da_chep(u, ma_hang)]
	erp_chep = [u for u in erp if la_anh_pancake_da_chep(u, ma_hang)]
	# Có ảnh Pancake sống thì bản chép cũ lùi sau nó. Không có thì
	# bản chép vẫn đứng trước ảnh dòng và ảnh nền để không rơi ảnh.
	for u in erp_tay + list(anhs_pancake or ()) + erp_chep + [anh_dong]:
		u = anh_cong_khai(u)
		if u and u not in ds:
			ds.append(u)
	if not ds:
		ds = [nen]
	return ds[0], ds[:SO_ANH_TOI_DA]
