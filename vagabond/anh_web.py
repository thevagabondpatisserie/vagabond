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

Hàm THUẦN, không chạm Frappe.
"""

ANH_NEN = "/assets/vagabond/web_order/anh-bia.png"
SO_ANH_TOI_DA = 5


def anh_cong_khai(u):
	"""Chỉ đường dẫn khách mở được. Ảnh /private cần đăng nhập nên bỏ."""
	u = str(u or "").strip()
	if not u or u.startswith("/private") or "/private/files/" in u:
		return ""
	return u


def chon_anh(anh_erp=None, anhs_pancake=(), anh_dong=None, nen=ANH_NEN):
	"""Trả (ảnh chính, danh sách ảnh tối đa 5) theo đúng thứ tự đã chốt.

	`anh_erp` có thể là một chuỗi hoặc một danh sách (một nhóm bánh gom nhiều
	size, mỗi size một hồ sơ món). Ảnh trùng chỉ giữ một lần. Không có ảnh
	nào thì trả ảnh nền thương hiệu, không bao giờ trả rỗng.
	"""
	ds = []
	erp = anh_erp if isinstance(anh_erp, (list, tuple)) else [anh_erp]
	for u in list(erp) + list(anhs_pancake or ()) + [anh_dong]:
		u = anh_cong_khai(u)
		if u and u not in ds:
			ds.append(u)
	if not ds:
		ds = [nen]
	return ds[0], ds[:SO_ANH_TOI_DA]
