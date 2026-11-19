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


O_CAI_DAT = "mien_phi_giao_km"


def _doc_o():
	"""Giá trị thô của ô trong bảng Singles; chưa từng lưu thì None. Codex #594:
	KHÔNG đọc qua lib.cfg_o, vì cfg_o đổi số 0 (không giới hạn bán kính) thành
	chuỗi rỗng rồi bị hiểu là chưa điền (7 km)."""
	import frappe

	ds = frappe.db.sql("select value from `tabSingles` where doctype=%s and field=%s",
		("Vagabond Settings", O_CAI_DAT))
	return ds[0][0] if ds else None


def doc():
	"""Bán kính đang cài (Vagabond Settings, ô Miễn phí giao trong bán kính). Số 0
	người dùng điền được giữ nguyên là 0 (không giới hạn). Đọc hỏng thì về mặc
	định 7 km, không làm hỏng cửa nhận đơn."""
	try:
		return tu_o(_doc_o())
	except Exception:
		return KM_MIEN_PHI_MAC_DINH


def gieo_mac_dinh():
	"""Bước nâng chạy một lần (bản vá v675): site đã có Cài đặt từ trước thì ô mới
	chưa có dòng nào trong bảng Singles. Ghi sẵn 7 để lần lưu Cài đặt trên Desk
	không biến ô trống thành 0 (không giới hạn). Ô đã có giá trị (kể cả 0) thì
	giữ nguyên. Trả True khi vừa ghi."""
	import frappe

	if _doc_o() is not None:
		return False
	frappe.db.sql("insert into `tabSingles` (doctype, field, value) values (%s, %s, %s)",
		("Vagabond Settings", O_CAI_DAT, str(KM_MIEN_PHI_MAC_DINH)))
	return True


def trong(bao_phi, km_mien):
	"""Địa chỉ giao có nằm trong bán kính miễn phí không. THUẦN. km_mien 0 hay
	None là không giới hạn. Codex #594: có giới hạn mà CHƯA biết khoảng cách
	(không định vị được địa chỉ) thì KHÔNG coi là trong: không hứa miễn phí khi
	thiếu dữ liệu, phí giao do Sales báo khi xác nhận như đơn chưa báo được phí."""
	try:
		gh = float(km_mien or 0)
	except (TypeError, ValueError):
		gh = 0
	if gh <= 0:
		return True
	km = (bao_phi or {}).get("km_thang")
	try:
		return km is not None and float(km) <= gh
	except (TypeError, ValueError):
		return False


def gan_co(bao_phi, km_mien):
	"""Báo phí kèm cờ `ngoai_km_mien_phi` cho don_web.quyet_phi_giao. THUẦN.
	Không có báo phí (đơn tự lấy) thì trả nguyên."""
	if not isinstance(bao_phi, dict):
		return bao_phi
	return dict(bao_phi, ngoai_km_mien_phi=not trong(bao_phi, km_mien))
