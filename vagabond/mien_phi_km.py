"""v675 (giám đốc chốt 19/11/2026): miễn phí giao chỉ trong bán kính, mặc định
7 km tính đường thẳng từ điểm xuất hàng gần nhất (bếp hoặc cửa hàng).

Một nguồn cho cửa tạo đơn web (don_hang), cấu hình trang khách (don_web.cau_hinh)
và trang khách (kho/thuan.js trongKmMienPhi cùng luật). Phần quyết định là THUẦN.
"""

KM_MIEN_PHI_MAC_DINH = 7.0


def tu_o(v):
	"""Bán kính miễn phí giao (km) từ giá trị ô cài đặt. THUẦN.

	v675 (giám đốc chốt 19/11/2026): miễn phí giao trong bán kính 7 km tính từ
	điểm xuất hàng. Ô chưa từng điền (None, rỗng) là 7; điền 0 là KHÔNG giới
	hạn bán kính (giá trị người dùng chọn, không coi là chưa điền); số âm hay
	chữ lạ về 7."""
	if v is None or str(v).strip() == "":
		return KM_MIEN_PHI_MAC_DINH
	try:
		x = float(v)
	except (TypeError, ValueError):
		return KM_MIEN_PHI_MAC_DINH
	return x if x >= 0 else KM_MIEN_PHI_MAC_DINH


def doc():
	"""Bán kính đang cài (Vagabond Settings, ô Miễn phí giao trong bán kính). Đọc
	hỏng thì về mặc định 7 km, không làm hỏng cửa nhận đơn."""
	try:
		from vagabond.lib import cfg_o

		return tu_o(cfg_o("mien_phi_giao_km"))
	except Exception:
		return KM_MIEN_PHI_MAC_DINH


def trong(bao_phi, km_mien):
	"""Địa chỉ giao có nằm trong bán kính miễn phí không. THUẦN. km_mien 0 hay
	None là không giới hạn. Chưa biết khoảng cách (báo phí cũ còn trong bộ nhớ
	đệm, chưa định vị được) thì coi là trong, như trước v675."""
	try:
		gh = float(km_mien or 0)
	except (TypeError, ValueError):
		gh = 0
	if gh <= 0:
		return True
	km = (bao_phi or {}).get("km_thang")
	try:
		return km is None or float(km) <= gh
	except (TypeError, ValueError):
		return True


def gan_co(bao_phi, km_mien):
	"""Báo phí kèm cờ `ngoai_km_mien_phi` cho don_web.quyet_phi_giao. THUẦN.
	Không có báo phí (đơn tự lấy) thì trả nguyên."""
	if not isinstance(bao_phi, dict):
		return bao_phi
	return dict(bao_phi, ngoai_km_mien_phi=not trong(bao_phi, km_mien))
