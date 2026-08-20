# -*- coding: utf-8 -*-
"""Trạng thái gửi email trên chứng từ, nói đúng sự thật của hàng đợi.

Vì sao có tệp này
-----------------
Uyên bấm Gửi, màn báo thành công, bốn mươi phút sau đổi thành "Gửi lỗi",
nhà cung cấp không nhận được gì. Cái màn báo thành công đó là lời nói dối,
và nó là loại nói dối tệ nhất: nó làm người ta tin việc đã xong rồi bỏ đi
làm việc khác.

Sự thật là lúc bấm Gửi thì email mới chỉ chui vào Email Queue. Chưa ai gửi
gì cả. Bộ lập lịch nhặt lên sau đó, có thể vài giây, có thể vài phút, và
đó mới là lúc biết được thành hay bại.

Nên trạng thái phải kể đúng ba nhịp đó:

    Đang chờ gửi   thư đã vào hàng đợi, máy chưa gửi
    Đã gửi         hàng đợi báo Sent, tức máy chủ thư đã nhận
    Gửi lỗi        hàng đợi báo Error, kèm lý do bằng tiếng người

Và "Đã gửi" CHỈ được hiện khi hàng đợi thật sự báo Sent. Không suy đoán,
không lạc quan, không đặt trước rồi sửa sau.

Vì sao dùng nhịp lập lịch chứ không dùng hook
---------------------------------------------
Frappe đổi trạng thái hàng đợi bằng `frappe.db.set_value` ở trong lòng
đoạn mã gửi thư, tức KHÔNG chạy qua vòng đời tài liệu. Móc `on_update` vào
Email Queue thì phần lớn lần đổi trạng thái sẽ không nổ hook.

Nên chia hai đường. Lúc thư vào hàng đợi thì có `after_insert` thật, dùng
nó để đặt "Đang chờ gửi" ngay lập tức, người bấm nút thấy đúng thứ vừa xảy
ra. Còn hai nhịp sau thì một nhịp lập lịch đi soát và cập nhật.

Vì sao không tính ra lúc đọc màn hình
-------------------------------------
Tính ra thì luôn đúng và không cần cột. Nhưng Uyên nhìn danh sách trên
Desk, mà danh sách thì lọc và sắp xếp theo CỘT. Một trạng thái không nằm
trong cột là một trạng thái không lọc được, tức không dùng để làm việc
được.
"""

import frappe
from frappe.utils import add_to_date, now_datetime

from vagabond.gui_thu import HANG_DOI, cau_loi, xep_loai_loi

O_TRANG_THAI = "trang_thai_gui_email"
O_LY_DO = "ly_do_loi_email"

CHUA_GUI = "Chưa gửi"
DANG_CHO = "Đang chờ gửi"
DA_GUI = "Đã gửi"
GUI_LOI = "Gửi lỗi"

# Chứng từ nào có nút gửi thư cho bên ngoài thì mang cột trạng thái này.
CHUNG_TU_CO_GUI = ("Purchase Order", "Material Request")

# Hàng đợi nói gì thì màn hình nói lại thế. `Sending` vẫn là đang chờ:
# máy đang cầm thư trong tay chứ chưa buông được.
THEO_HANG_DOI = {
	"Not Sent": DANG_CHO,
	"Sending": DANG_CHO,
	"Sent": DA_GUI,
	"Error": GUI_LOI,
	"Expired": GUI_LOI,
}

# Quét lùi bao nhiêu phút mỗi nhịp. Rộng hơn nhịp chạy (5 phút) nhiều lần,
# để một nhịp lỡ không làm mất luôn bản ghi.
CUA_SO_SOAT_PHUT = 45


# ============================================================ phép THUẦN


def theo_hang_doi(trang_thai_hang_doi):
	"""Hàng đợi ở trạng thái này thì màn hình hiện gì. THUẦN.

	Trạng thái lạ thì trả về None chứ không đoán bừa. Frappe thêm trạng thái
	mới lúc nào là việc của Frappe; đoán bừa ở đây là lại nói dối một lần
	nữa, đúng cái vừa đi sửa.
	"""
	return THEO_HANG_DOI.get((trang_thai_hang_doi or "").strip())


def gop_nhieu_thu(ds_trang_thai):
	"""Một chứng từ gửi nhiều thư thì cột hiện gì. THUẦN.

	Thứ tự ưu tiên là thứ tự của cái cần người xử lý: lỗi trước, rồi đang
	chờ, rồi mới tới đã gửi. Một đơn gửi hai thư mà một thư hỏng thì cột
	phải hiện "Gửi lỗi", vì có việc phải làm. Hiện "Đã gửi" là giấu mất
	cái hỏng đi.
	"""
	co = [theo_hang_doi(x) for x in (ds_trang_thai or [])]
	co = [x for x in co if x]
	if not co:
		return None
	for uu_tien in (GUI_LOI, DANG_CHO, DA_GUI):
		if uu_tien in co:
			return uu_tien
	return None


def cau_nhac(trang_thai, loi=None):
	"""Câu giải thích đặt cạnh trạng thái. THUẦN.

	Mỗi câu phải trả lời được "giờ tôi làm gì", chứ không chỉ mô tả tình
	hình. "Gửi lỗi" một mình là bắt Uyên ngồi đoán.
	"""
	if trang_thai == DANG_CHO:
		return (
			"Thư đã nằm trong hàng đợi, máy chưa gửi đi. Thường xong trong "
			"vài phút. Anh chị không cần bấm lại, bấm lại là nhà cung cấp "
			"nhận hai lần."
		)
	if trang_thai == DA_GUI:
		return "Máy chủ thư đã nhận và chuyển đi."
	if trang_thai == GUI_LOI:
		return cau_loi(loi)
	if trang_thai == CHUA_GUI:
		return "Đơn này chưa gửi thư cho nhà cung cấp lần nào."
	return ""


# ========================================================= chạm vào hệ


def _co_o(loai_chung_tu):
	"""Doctype này có cột trạng thái gửi email không."""
	try:
		return frappe.get_meta(loai_chung_tu).has_field(O_TRANG_THAI)
	except Exception:
		return False


def _co_ly_do(loai_chung_tu):
	try:
		return frappe.get_meta(loai_chung_tu).has_field(O_LY_DO)
	except Exception:
		return False


def _ghi(loai_chung_tu, ma, trang_thai, ly_do=""):
	"""Ghi trạng thái xuống chứng từ nếu nó khác cái đang có.

	Dùng `frappe.db.set_value` với `update_modified=False`: cột này là vết
	kỹ thuật của đường thư, không phải người sửa chứng từ. Đụng vào
	`modified` là làm rối danh sách "sửa gần đây" của cả phòng, và tệ hơn
	là đá vào phép kiểm trùng phiên bản của Frappe khi ai đó đang mở đơn.
	"""
	dang_co = frappe.db.get_value(loai_chung_tu, ma, O_TRANG_THAI)
	gia_tri = {}
	if (dang_co or "") != trang_thai:
		gia_tri[O_TRANG_THAI] = trang_thai
	if _co_ly_do(loai_chung_tu):
		ly_do_cu = frappe.db.get_value(loai_chung_tu, ma, O_LY_DO)
		if (ly_do_cu or "") != (ly_do or ""):
			gia_tri[O_LY_DO] = ly_do or ""
	if not gia_tri:
		return False
	frappe.db.set_value(loai_chung_tu, ma, gia_tri, update_modified=False)
	return True


def danh_dau_cho_gui(doc, method=None):
	"""Hook after_insert của Email Queue: đặt ngay "Đang chờ gửi".

	Đây là nhịp một trong ba. Người vừa bấm Gửi phải thấy đúng thứ vừa xảy
	ra, và thứ vừa xảy ra là thư mới vào hàng đợi.

	Không bao giờ ném lỗi: hàm này nằm trên đường đi của mọi email trong hệ,
	nó hỏng mà chặn luôn việc tạo hàng đợi thì mất cả thư.
	"""
	try:
		loai = (doc.get("reference_doctype") or "").strip()
		ma = (doc.get("reference_name") or "").strip()
		if not loai or not ma or loai not in CHUNG_TU_CO_GUI:
			return
		if not _co_o(loai) or not frappe.db.exists(loai, ma):
			return
		_ghi(loai, ma, DANG_CHO, "")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "trang_thai_thu: danh dau cho gui")


def soat_tu_dong():
	"""Nhịp lập lịch: đọc hàng đợi rồi cập nhật trạng thái trên chứng từ.

	Đây là nhịp hai và ba. Chỉ soát các bản ghi vừa động trong cửa sổ gần
	đây, không quét cả bảng: hàng đợi có hàng nghìn dòng và phần lớn đã yên
	vị từ lâu.

	Một chứng từ có thể có nhiều thư (gửi lại, gửi cho nhiều người), nên gom
	theo chứng từ rồi mới quyết, xem `gop_nhieu_thu`.
	"""
	try:
		moc = add_to_date(now_datetime(), minutes=-CUA_SO_SOAT_PHUT)
		ds = frappe.get_all(
			HANG_DOI,
			filters={
				"modified": [">=", moc],
				"reference_doctype": ["in", list(CHUNG_TU_CO_GUI)],
			},
			fields=["name", "status", "error", "reference_doctype", "reference_name",
				"modified"],
			order_by="modified asc",
			limit=1000,
		)
		if not ds:
			return

		nhom = {}
		for x in ds:
			khoa = (x.reference_doctype, x.reference_name)
			nhom.setdefault(khoa, []).append(x)

		da_doi = 0
		for (loai, ma), hang in nhom.items():
			if not _co_o(loai) or not frappe.db.exists(loai, ma):
				continue
			trang_thai = gop_nhieu_thu([x.status for x in hang])
			if not trang_thai:
				continue
			ly_do = ""
			if trang_thai == GUI_LOI:
				# Lấy lỗi của bản ghi ĐỘNG GẦN NHẤT trong nhóm lỗi, chứ không
				# lấy bừa cái đầu: đơn gửi lại nhiều lần thì lần cuối mới là
				# lần đang cần giải thích.
				loi = [x for x in hang if theo_hang_doi(x.status) == GUI_LOI]
				loi.sort(key=lambda x: x.modified or "")
				ly_do = cau_loi(loi[-1].error if loi else "")
			if _ghi(loai, ma, trang_thai, ly_do):
				da_doi += 1

		if da_doi:
			frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "trang_thai_thu: soat tu dong")


# ===================================================== cột và ô trên Desk


def dung():
	"""Dựng cột trạng thái và ô lý do. Gọi từ after_migrate.

	Ô `trang_thai_gui_email` là truong CU, bấm tay trên Desk từ trước, và bộ
	quy tắc của repo nói rõ là không kéo trường cũ vào `truong_tu_them.py`
	vì khai lại là rủi ro ghi đè.

	Nên ở đây KHÔNG khai lại cả trường. Chỉ đọc danh sách lựa chọn đang có
	rồi CHÈN THÊM "Đang chờ gửi" vào nếu thiếu, giữ nguyên thứ tự và mọi
	lựa chọn cũ. Thao tác này lặp lại được và không xoá được gì.
	"""
	for loai in CHUNG_TU_CO_GUI:
		try:
			_them_lua_chon_dang_cho(loai)
		except Exception:
			frappe.log_error(frappe.get_traceback(),
				"trang_thai_thu: them lua chon %s" % loai)
	try:
		_dung_o_ly_do()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "trang_thai_thu: dung o ly do")


def _them_lua_chon_dang_cho(loai_chung_tu):
	"""Chèn "Đang chờ gửi" vào danh sách lựa chọn, không đụng cái cũ."""
	ten = frappe.db.get_value(
		"Custom Field", {"dt": loai_chung_tu, "fieldname": O_TRANG_THAI}, "name"
	)
	if not ten:
		return
	cu = frappe.db.get_value("Custom Field", ten, "options") or ""
	dong = [d for d in cu.split("\n")]
	if DANG_CHO in [d.strip() for d in dong]:
		return
	# Chèn ngay sau "Chưa gửi" để danh sách đọc theo đúng thứ tự thời gian
	# của một lá thư. Không có "Chưa gửi" thì thêm vào cuối.
	moi = []
	da_chen = False
	for d in dong:
		moi.append(d)
		if not da_chen and d.strip() == CHUA_GUI:
			moi.append(DANG_CHO)
			da_chen = True
	if not da_chen:
		moi.append(DANG_CHO)
	frappe.db.set_value("Custom Field", ten, "options", "\n".join(moi))
	frappe.clear_cache(doctype=loai_chung_tu)


def _dung_o_ly_do():
	"""Ô lý do lỗi: chỉ hiện khi trạng thái là Gửi lỗi."""
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	khai = {}
	for loai in CHUNG_TU_CO_GUI:
		if not frappe.db.exists("Custom Field",
				{"dt": loai, "fieldname": O_TRANG_THAI}):
			continue
		khai[loai] = [
			{
				"fieldname": O_LY_DO,
				"label": "Vì sao gửi lỗi",
				"fieldtype": "Small Text",
				"insert_after": O_TRANG_THAI,
				"read_only": 1,
				"depends_on": "eval:doc.%s=='%s'" % (O_TRANG_THAI, GUI_LOI),
				"description": (
					"Máy tự điền. Câu này nói rõ ai phải làm gì tiếp. Nếu nó "
					"bảo là lỗi cấu hình của hệ thống thì anh chị báo anh Việt, "
					"đơn không cần lập lại."
				),
			}
		]
	if khai:
		create_custom_fields(khai, update=True)


@frappe.whitelist()
def tinh_trang(loai_chung_tu, ma):
	"""Màn hình hỏi: chứng từ này gửi thư tới đâu rồi.

	Trả về cả câu nhắc, để màn hình không phải tự dịch mã lỗi lần nữa.
	"""
	loai = (loai_chung_tu or "").strip()
	ma = (ma or "").strip()
	if not loai or not ma:
		return {"trang_thai": CHUA_GUI, "nhac": cau_nhac(CHUA_GUI), "thu": []}
	frappe.has_permission(loai, "read", doc=ma, throw=True)
	ds = frappe.get_all(
		HANG_DOI,
		filters={"reference_doctype": loai, "reference_name": ma},
		fields=["name", "status", "error", "sender", "creation", "modified"],
		order_by="creation desc",
		limit=20,
	)
	trang_thai = gop_nhieu_thu([x.status for x in ds]) or CHUA_GUI
	loi = [x for x in ds if theo_hang_doi(x.status) == GUI_LOI]
	return {
		"trang_thai": trang_thai,
		"nhac": cau_nhac(trang_thai, loi[0].error if loi else None),
		"ma_loi": xep_loai_loi(loi[0].error) if loi else "",
		"so_thu": len(ds),
		"thu": [
			{
				"ma": x.name,
				"hang_doi": x.status,
				"hien": theo_hang_doi(x.status) or x.status,
				"nguoi_gui": x.sender,
				"luc": str(x.creation),
			}
			for x in ds
		],
	}
