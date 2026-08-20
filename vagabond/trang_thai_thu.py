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

import re

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

# Mẫu mã chứng từ nằm trong thân thư: DMH-2026-00146, MAT-MR-2026-00007, và
# bản sửa đổi có đuôi số như DMH-2026-00133-1.
MAU_MA = re.compile(r"\b[A-Z]{2,6}(?:-[A-Z]{2,6}){0,2}-\d{4}-\d{4,6}(?:-\d{1,2})?\b")

# Quét lùi bao nhiêu ngày khi màn hình hỏi một chứng từ đã gửi thư tới đâu.
# Có mốc thì câu lệnh dò thân thư không phải quét cả bảng Communication.
CUA_SO_HOI_NGAY = 120


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


def tim_ma_trong_thu(chuoi):
	"""Nhặt mọi mã chứng từ có mặt trong tiêu đề cộng thân thư. THUẦN.

	Vì sao phải dò thân thư
	-----------------------
	Một bản ghi hàng đợi chỉ có MỘT ô `reference_name`. Uyên gộp ba đơn vào
	một lá thư thì hàng đợi vẫn chỉ đóng dấu được đơn đầu, hai đơn còn lại
	nằm nguyên ở "Chưa gửi". Uyên thấy vậy thì bấm gửi lại, và nhà cung cấp
	nhận thư hai lần. Chiều 20/08/2026 chuyện này xảy ra thật với
	DMH-2026-00139 và DMH-2026-00146.

	Đây là bài học cũ, đã học một lần hồi 03/08/2026 rồi lại quên: bản đầu
	hôm đó dựa vào bảng `Communication Link` để biết thư gồm những đơn nào,
	chạy thật thì bảng đó rỗng. Nguồn đầy đủ và không phụ thuộc bảng phụ nào
	chính là THÂN THƯ, vì mẫu thư gộp in đủ mã từng đơn ra bảng tóm tắt.

	Trả về danh sách mã ứng viên, XẾP DÀI TRƯỚC. Xếp dài trước là bắt buộc:
	đơn sửa đổi `DMH-2026-00133-1` mà đứng sau thì sẽ bị nuốt thành
	`DMH-2026-00133`. Hàm này chỉ nhặt, không hỏi hệ xem mã có thật không.
	"""
	ra, da = [], set()
	for m in MAU_MA.findall(chuoi or ""):
		if m in da:
			continue
		da.add(m)
		ra.append(m)
	ra.sort(key=len, reverse=True)
	return ra


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


def _than_thu(ma_thu, bo_nho=None):
	"""Lấy tiêu đề cộng thân của một lá thư trong hàng đợi.

	Ưu tiên bản ghi `Communication` vì ở đó thân thư là HTML thường, đọc
	thẳng được. Ô `message` của hàng đợi là bản MIME đã mã hoá base64, dò
	chữ trong đó thì không ra gì; chỉ mở ra khi thư không gắn Communication.
	"""
	if bo_nho is not None and ma_thu in bo_nho:
		return bo_nho[ma_thu]
	cau = ""
	try:
		c = frappe.db.get_value(
			"Communication", ma_thu, ["subject", "content"], as_dict=True
		)
		if c:
			cau = "%s\n%s" % (c.get("subject") or "", c.get("content") or "")
	except Exception:
		cau = ""
	if bo_nho is not None:
		bo_nho[ma_thu] = cau
	return cau


def _boc_mime(chuoi):
	"""Mở bản MIME của hàng đợi ra lấy phần chữ. Chỉ dùng khi không có Communication."""
	try:
		import email as thu_mime

		msg = thu_mime.message_from_string(chuoi or "")
		phan = [msg.get("Subject") or ""]
		for p in msg.walk():
			if p.get_content_maintype() != "text":
				continue
			try:
				than = p.get_payload(decode=True)
			except Exception:
				continue
			if not than:
				continue
			phan.append(than.decode(p.get_content_charset() or "utf-8", "ignore"))
		return "\n".join(phan)
	except Exception:
		return ""


def _cac_chung_tu_cua_thu(hang, bo_nho=None):
	"""Một lá thư trong hàng đợi ứng với những chứng từ nào.

	Luôn có chứng từ gắn ở ô tham chiếu. Ngoài ra dò thêm mã trong thân thư,
	vì thư gộp mang nhiều đơn mà ô tham chiếu chỉ chứa được một.

	Mã dò ra phải TỒN TẠI THẬT mới nhận. Không có phép kiểm này thì một
	chuỗi ngẫu nhiên trông giống mã đơn cũng thành chứng từ, và máy sẽ đóng
	dấu "Đã gửi" lên thứ không hề được gửi.
	"""
	ra, da = [], set()

	def them(loai, ma):
		if not loai or not ma or loai not in CHUNG_TU_CO_GUI:
			return
		if (loai, ma) in da:
			return
		if not _co_o(loai) or not frappe.db.exists(loai, ma):
			return
		da.add((loai, ma))
		ra.append((loai, ma))

	them((hang.get("reference_doctype") or "").strip(),
		(hang.get("reference_name") or "").strip())

	try:
		ma_thu = (hang.get("communication") or "").strip()
		cau = _than_thu(ma_thu, bo_nho) if ma_thu else _boc_mime(hang.get("message"))
		for ma in tim_ma_trong_thu(cau):
			for loai in CHUNG_TU_CO_GUI:
				them(loai, ma)
				# Đuôi "-1" trong thân thư có thể là số thứ tự chứ không phải
				# bản sửa đổi. Không tìm ra bản đủ đuôi thì thử bản gốc.
				if (loai, ma) not in da:
					goc = re.sub(r"-\d{1,2}$", "", ma)
					if goc != ma:
						them(loai, goc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "trang_thai_thu: do than thu")

	return ra


def danh_dau_cho_gui(doc, method=None):
	"""Hook after_insert của Email Queue: đặt ngay "Đang chờ gửi".

	Đây là nhịp một trong ba. Người vừa bấm Gửi phải thấy đúng thứ vừa xảy
	ra, và thứ vừa xảy ra là thư mới vào hàng đợi.

	Không bao giờ ném lỗi: hàm này nằm trên đường đi của mọi email trong hệ,
	nó hỏng mà chặn luôn việc tạo hàng đợi thì mất cả thư.
	"""
	try:
		loai = (doc.get("reference_doctype") or "").strip()
		if not loai or loai not in CHUNG_TU_CO_GUI:
			return
		# Thư gộp mang nhiều đơn: đóng dấu "Đang chờ gửi" cho TẤT CẢ, không
		# chỉ đơn nằm ở ô tham chiếu. Xem `tim_ma_trong_thu`.
		for loai_ct, ma in _cac_chung_tu_cua_thu(doc, {}):
			_ghi(loai_ct, ma, DANG_CHO, "")
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
				"communication", "modified"],
			order_by="modified asc",
			limit=1000,
		)
		if not ds:
			return

		# Gom theo CHỨNG TỪ chứ không theo ô tham chiếu: một lá thư gộp ba
		# đơn thì cả ba đơn phải nhận trạng thái của lá thư đó.
		bo_nho = {}
		nhom = {}
		for x in ds:
			for khoa in _cac_chung_tu_cua_thu(x, bo_nho):
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


@frappe.whitelist()
def soat_lai(so_ngay=7):
	"""Soát lại một quãng dài, để vá các đơn bị sót trước khi có bản này.

	Nhịp lập lịch chỉ nhìn lùi 45 phút, nên các thư gộp gửi từ hôm trước sẽ
	không bao giờ được soát lại. Hàm này chạy đúng phép đó trên cửa sổ rộng,
	gọi tay một lần sau khi deploy là đủ.

	Chỉ đọc hàng đợi rồi ghi lại trạng thái đúng của hàng đợi, nên chạy mấy
	lần cũng ra một kết quả.
	"""
	if not frappe.has_permission("Purchase Order", "write"):
		frappe.throw(
			"Chỉ người có quyền sửa đơn mua hàng mới soát lại được. "
			"Anh chị nhờ anh Việt chạy giúp."
		)
	ngay = max(1, min(int(so_ngay or 7), 90))
	moc = add_to_date(now_datetime(), days=-ngay)
	ds = frappe.get_all(
		HANG_DOI,
		filters={
			"modified": [">=", moc],
			"reference_doctype": ["in", list(CHUNG_TU_CO_GUI)],
		},
		fields=["name", "status", "error", "reference_doctype", "reference_name",
			"communication", "modified"],
		order_by="modified asc",
		limit=5000,
	)
	bo_nho = {}
	nhom = {}
	for x in ds:
		for khoa in _cac_chung_tu_cua_thu(x, bo_nho):
			nhom.setdefault(khoa, []).append(x)

	da_doi = []
	for (loai, ma), hang in nhom.items():
		trang_thai = gop_nhieu_thu([x.status for x in hang])
		if not trang_thai:
			continue
		ly_do = ""
		if trang_thai == GUI_LOI:
			loi = [x for x in hang if theo_hang_doi(x.status) == GUI_LOI]
			loi.sort(key=lambda x: x.modified or "")
			ly_do = cau_loi(loi[-1].error if loi else "")
		cu = frappe.db.get_value(loai, ma, O_TRANG_THAI)
		if _ghi(loai, ma, trang_thai, ly_do):
			da_doi.append({"ma": ma, "loai": loai, "cu": cu or "", "moi": trang_thai})
	if da_doi:
		frappe.db.commit()
	return {
		"so_thu": len(ds),
		"so_chung_tu": len(nhom),
		"da_doi": da_doi,
		"ghi_chu": "Soát %d ngày, %d lá thư, sửa %d chứng từ."
			% (ngay, len(ds), len(da_doi)),
	}


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


def _thu_gop_co_nhac(ma):
	"""Các lá thư gộp có nhắc tới mã chứng từ này trong thân thư.

	Dò bằng `like` trên bảng Communication, có chặn mốc thời gian để không
	quét cả bảng. Thư cũ hơn mốc thì thôi, vì cột trạng thái trên chứng từ
	đã chốt từ lâu rồi, màn hình chi tiết không cần liệt kê lại.
	"""
	ma = (ma or "").strip()
	if not ma:
		return []
	try:
		moc = add_to_date(now_datetime(), days=-CUA_SO_HOI_NGAY)
		cac_thu = frappe.get_all(
			"Communication",
			filters={"creation": [">=", moc], "content": ["like", "%" + ma + "%"]},
			pluck="name",
			limit=20,
		)
		if not cac_thu:
			return []
		return frappe.get_all(
			HANG_DOI,
			filters={"communication": ["in", cac_thu]},
			fields=["name", "status", "error", "sender", "creation", "modified"],
			order_by="creation desc",
			limit=20,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "trang_thai_thu: tim thu gop")
		return []


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
	# Cộng thêm các lá thư GỘP có nhắc tới mã này mà ô tham chiếu lại trỏ
	# sang đơn khác. Không cộng thì màn hình báo "Chưa gửi" trong khi thư đã
	# đi rồi, và người dùng sẽ bấm gửi lại.
	da_co = set(x.name for x in ds)
	for x in _thu_gop_co_nhac(ma):
		if x.name not in da_co:
			da_co.add(x.name)
			ds.append(x)
	ds.sort(key=lambda x: x.creation or "", reverse=True)
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
