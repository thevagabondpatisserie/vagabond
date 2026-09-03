# -*- coding: utf-8 -*-
"""Gửi thư đi: vá ô người gửi, cứu hàng đợi kẹt, và báo động khi hỏng.

Sự cố 16/08/2026
----------------
Uyên báo email đơn mua hàng bấm gửi thì màn báo thành công, bốn mươi phút
sau đổi thành "Gửi lỗi", nhà cung cấp không nhận được gì.

Truy ra thì KHÔNG phải lỗi SMTP. Không có mã 535, không có 550, không có
timeout, vì email chưa bao giờ chạm tới máy chủ thư. Nó vỡ trong Python
trước đó một bước:

    File "/usr/lib/python3.14/smtplib.py", line 152, in quoteaddr
        if addrstring.strip().startswith('<'):
    AttributeError: 'NoneType' object has no attribute 'strip'

Ô `sender` trên hàng đợi rỗng, nên lúc dựng câu lệnh `MAIL FROM:` thì
`quoteaddr(None)` nổ. Bốn mươi phút chỉ là nhịp chạy lại của bộ lập lịch,
mỗi bản ghi thử ba lần rồi mới bị đánh dấu lỗi hẳn.

Phạm vi thật rộng hơn nhiều so với luồng đặt hàng. Đếm trên hàng đợi:

    truoc 17/08         711 ban ghi   693 da gui   704 co nguoi gui
    tu 16/08 18:00      118 ban ghi     1 da gui     1 co nguoi gui

Tức từ chiều 16/08 gần như MỌI email đi ra đều mất ô người gửi, ở mọi loại
chứng từ: 43 Material Request, 26 Purchase Order, 7 phiếu hoàn tiền, 6 báo
cáo tự động. Cả tiệm không gửi được một email nào.

Thủ phạm là code của chính mình
-------------------------------
Không phải Frappe. Là `vagabond/email_sach.py`, commit 102a22b lúc 16/08
17:26, tức trước lúc hỏng ba mươi tư phút.

Hôm đó khách gõ email thiếu ".com" làm rớt một đơn hàng, nên mình thêm hook
`email_sach.don` ở `before_validate` đặt trên `"*"`, quét mọi ô kiểu
Data/options=Email, ô nào không khớp regex thì bỏ trống để chứng từ vẫn lưu
được.

Ô `sender` của Email Queue đúng là kiểu Data/options=Email. Mà Frappe không
điền địa chỉ trần vào đó, nó điền dạng có tên:

    Purchasing The Vagabond <purchasing@thevagabondpatisserie.com>

Regex cấm khoảng trắng, nên chuỗi đó bị xếp là sai, và hook xoá trắng ô
`sender`. Rồi `quoteaddr(None)` nổ.

Và đó cũng là lý do bản vá Server Script hôm 17/08 vô dụng: nó chạy ở
`before_insert`, còn `email_sach.don` chạy ở `before_validate` tức là SAU,
nên vừa điền xong là bị xoá lại. Script đang bật, logic đúng, mà 109 trên
110 bản ghi sinh sau đó vẫn rỗng.

Gốc đã vá bên `email_sach.py`: `hop_le` nhận dạng có tên, và `don` chừa các
doctype hạ tầng ra.

Vì sao vẫn giữ mô đun này
-------------------------
Vá gốc là đủ để chuyện này không lặp lại. Mô đun này lo ba việc khác mà vá
gốc không lo được.

Một, lưới hứng. Ô người gửi rỗng làm chết cả đường thư đi, mà nó rỗng vì
nhiều lý do chứ không riêng lý do vừa rồi: hộp thư mặc định bị tắt, ai đó
gọi `frappe.sendmail` quên truyền `sender`, một hook khác sau này lại đụng
vào. Hàm `bu_nguoi_gui` ở dưới móc vào `after_insert` và ghi bằng
`frappe.db.set_value`, tức ghi thẳng xuống bảng không qua `validate`, nên
không hook nào ở tầng validate xoá lại được nữa.

Hai, gửi đúng hộp thư. Đơn mua hàng phải đi từ purchasing@ để nhà cung cấp
bấm trả lời là thư về đúng hộp của Uyên.

Ba, và đây là bài học đắt nhất: KHÔNG AI BIẾT. Cả tiệm không gửi được một
email nào suốt nhiều ngày, và mình chỉ biết vì Uyên đi hỏi. Không có cảnh
báo nào cả. Phần `canh_bao_email_loi` ở cuối tệp là để lần sau máy tự hú.

Và đặt trong repo chứ không phải Server Script. Đúng cái Server Script kia
là ví dụ: nó nằm trong cơ sở dữ liệu, không ai kiểm thử nó, không ai biết nó
không chạy, và nó nằm im nhiều ngày trong khi cả tiệm không gửi được email.
"""

import json
import re

import frappe
from frappe.utils import add_to_date, cint, now_datetime

HANG_DOI = "Email Queue"
HOP_THU = "Email Account"

# --------------------------------------------------- hộp thư theo chứng từ
#
# Đơn mua hàng phải đi từ purchasing@, không phải erp@. Nhà cung cấp bấm trả
# lời là thư về đúng hộp của Uyên, chứ không rơi vào hộp kỹ thuật rồi nằm đó.
#
# Không viết cứng địa chỉ ở đây mà viết TÊN bản ghi hộp thư: địa chỉ đổi thì
# sửa một chỗ trên Desk, mã nguồn không phải deploy lại.
HOP_THU_MUA = "Purchasing The Vagabond"
HOP_THU_BAN = "Sales The Vagabond"

HOP_THU_THEO_CHUNG_TU = {
	"Purchase Order": HOP_THU_MUA,
	"Material Request": HOP_THU_MUA,
	"Request for Quotation": HOP_THU_MUA,
	"Supplier Quotation": HOP_THU_MUA,
	"Vagabond Ho So TT": HOP_THU_MUA,
	"Sales Invoice": HOP_THU_BAN,
	"Sales Order": HOP_THU_BAN,
	"Quotation": HOP_THU_BAN,
	"Bao Gia Ban Hang": HOP_THU_BAN,
}

# ------------------------------------------------------------- mã lỗi
LOI_NGUOI_GUI = "nguoi_gui_rong"
LOI_DANG_NHAP = "dang_nhap"
LOI_DIA_CHI_NHAN = "dia_chi_nhan"
LOI_MANG = "mang"
LOI_HAN_MUC = "han_muc"
LOI_KHAC = "khac"

# Dịch mã lỗi kỹ thuật sang câu người vận hành đọc được, và quan trọng hơn
# là câu đó phải nói RÕ AI PHẢI LÀM GÌ. "Gửi lỗi" chung chung thì Uyên chỉ
# biết ngồi đợi.
CAU_CHO_NGUOI_DUNG = {
	LOI_NGUOI_GUI: (
		"Hệ thống chưa xác định được hộp thư gửi đi. Đây là lỗi cấu hình của hệ thống, không phải lỗi của đơn này, anh chị vui lòng báo anh Việt. Đơn không cần lập lại, gửi lại được ngay sau khi sửa."
	),
	LOI_DANG_NHAP: (
		"Hộp thư gửi đi bị máy chủ từ chối đăng nhập. Báo anh Việt kiểm lại "
		"mật khẩu hộp thư, đơn không cần lập lại."
	),
	LOI_DIA_CHI_NHAN: (
		"Địa chỉ email của nhà cung cấp không tồn tại hoặc bị từ chối. Anh "
		"chị mở hồ sơ nhà cung cấp kiểm lại địa chỉ rồi bấm gửi lại."
	),
	LOI_MANG: (
		"Máy chủ thư không phản hồi. Thường là tạm thời, anh chị thử gửi lại "
		"sau ít phút; vẫn hỏng thì báo anh Việt."
	),
	LOI_HAN_MUC: (
		"Hộp thư đã chạm hạn mức gửi trong ngày. Chờ sang ngày mai hoặc báo "
		"anh Việt nâng hạn mức."
	),
	LOI_KHAC: (
		"Gửi không thành công, chưa xếp được nguyên nhân. Anh chị vui lòng báo anh Việt kèm mã đơn."
	),
}

# Lỗi nào gửi lại là có ích, lỗi nào gửi lại bao nhiêu lần cũng hỏng. Địa chỉ
# người nhận sai thì phải sửa hồ sơ nhà cung cấp trước, gửi lại chỉ tạo thêm
# rác trong hàng đợi.
GUI_LAI_DUOC = {LOI_NGUOI_GUI, LOI_MANG, LOI_DANG_NHAP}

# Bao nhiêu email lỗi trong một lượt quét thì hú còi. Anh Việt chốt 5.
NGUONG_BAO_DONG = 5

# Quét lùi bao nhiêu phút mỗi lượt.
CUA_SO_QUET_PHUT = 60


# ============================================================ phép THUẦN
#
# Không chạm Frappe nên kiểm thử được không cần site.


def chon_hop_thu(hop_thu_dang_co, loai_chung_tu):
	"""Bản ghi này nên gửi từ hộp thư nào. THUẦN.

	Ưu tiên hộp thư mà chính bản ghi đã mang. Frappe điền ô đó lúc dựng hàng
	đợi, và nó biết ngữ cảnh rõ hơn bảng tra ở đây.

	Không có thì tra theo loại chứng từ. Vẫn không ra thì trả về None, để
	phần chạm hệ đi lấy hộp thư mặc định.
	"""
	dang_co = (hop_thu_dang_co or "").strip()
	if dang_co:
		return dang_co
	return HOP_THU_THEO_CHUNG_TU.get((loai_chung_tu or "").strip())


def xep_loai_loi(loi):
	"""Đọc traceback, trả về mã lỗi. THUẦN.

	Xếp theo thứ tự HẸP TRƯỚC RỘNG SAU: lỗi người gửi rỗng có dấu vân tay
	riêng là `quoteaddr`, phải bắt trước, vì chuỗi traceback của nó cũng có
	chữ "smtplib" và dễ bị nhánh mạng nuốt mất.
	"""
	t = str(loi or "")
	if not t.strip():
		return LOI_KHAC
	if "quoteaddr" in t or ("NoneType" in t and "strip" in t):
		return LOI_NGUOI_GUI
	if "535" in t or "Authentication" in t or "authentication failed" in t.lower():
		return LOI_DANG_NHAP
	if "550" in t or "551" in t or "553" in t or "Recipient address rejected" in t:
		return LOI_DIA_CHI_NHAN
	if "552" in t or "Quota" in t or "quota" in t or "over quota" in t.lower():
		return LOI_HAN_MUC
	if "timed out" in t or "timeout" in t.lower() or "Connection refused" in t:
		return LOI_MANG
	return LOI_KHAC


def cau_loi(loi):
	"""Câu tiếng Việt cho người vận hành, từ traceback. THUẦN."""
	return CAU_CHO_NGUOI_DUNG.get(xep_loai_loi(loi)) or CAU_CHO_NGUOI_DUNG[LOI_KHAC]


def nen_gui_lai(trang_thai, loi):
	"""Bản ghi này gửi lại có ích không. THUẦN.

	Chỉ gửi lại bản ghi ĐANG LỖI và lỗi thuộc nhóm chữa được ở phía mình.
	Bản ghi đã gửi rồi mà gửi lại là nhà cung cấp nhận hai lần một đơn.
	"""
	if (trang_thai or "").strip() != "Error":
		return False
	return xep_loai_loi(loi) in GUI_LAI_DUOC


def va_dong_from(noi_dung, dia_chi):
	"""Vá dòng From trong thân thư đã dựng sẵn. THUẦN.

	Ô `sender` chỉ là phong bì, tức câu lệnh `MAIL FROM:`. Còn dòng `From:`
	mà người nhận nhìn thấy thì nằm trong chính thân thư đã dựng từ trước.
	Vá phong bì mà quên thân thư thì máy chủ nhận có thể từ chối vì thư
	không có người gửi, hoặc nhà cung cấp thấy một thư trống người gửi.

	Chỉ đụng vào KHỐI TIÊU ĐỀ, tức phần trước dòng trống đầu tiên. Không bao
	giờ đụng vào phần thân, vì thân thư có thể chứa chữ "From:" trong nội
	dung mà sửa vào đó là hỏng thư.

	Đã có dòng From tử tế rồi thì trả nguyên vẹn, không đụng.
	"""
	noi_dung = noi_dung or ""
	dia_chi = (dia_chi or "").strip()
	if not noi_dung or not dia_chi:
		return noi_dung

	ngat = re.search(r"\r?\n\r?\n", noi_dung)
	if not ngat:
		return noi_dung
	tieu_de, than = noi_dung[: ngat.start()], noi_dung[ngat.start():]

	dong_from = re.search(r"^From:[ \t]*(.*)$", tieu_de, re.MULTILINE)
	if dong_from and "@" in (dong_from.group(1) or ""):
		return noi_dung

	xuong = "\r\n" if "\r\n" in noi_dung else "\n"
	if dong_from:
		tieu_de = (
			tieu_de[: dong_from.start()] + "From: " + dia_chi + tieu_de[dong_from.end():]
		)
	else:
		tieu_de = "From: " + dia_chi + xuong + tieu_de
	return tieu_de + than


def gom_theo_loai(ds_loi):
	"""Gom danh sách lỗi theo mã, để câu báo động nói được cái gì đang hỏng.

	`ds_loi` là danh sách chuỗi traceback. THUẦN.
	"""
	bang = {}
	for x in ds_loi or []:
		ma = xep_loai_loi(x)
		bang[ma] = bang.get(ma, 0) + 1
	return bang


def cau_bao_dong(so_loi, bang_loai, tu_gio, den_gio):
	"""Dựng câu báo động đỏ. THUẦN.

	Viết cho người đọc trên điện thoại lúc đang bận: câu đầu phải nói ngay
	chuyện gì, câu sau mới giải thích.
	"""
	dong = [
		"BAO DONG DO: he thong gui email dang hong.",
		"%d email loi trong khoang %s den %s." % (so_loi, tu_gio, den_gio),
	]
	for ma, dem in sorted(bang_loai.items(), key=lambda o: -o[1]):
		dong.append("- %d loi: %s" % (dem, CAU_CHO_NGUOI_DUNG.get(ma, ma)))
	dong.append(
		"Email khong gui duoc thi don mua hang khong toi nha cung cap, ma khong ai biet cho toi khi co nguoi hoi. Vui lòng kiem ngay."
	)
	return "\n".join(dong)


# ========================================================= chạm vào hệ


def _dia_chi_hop_thu(ten):
	"""Địa chỉ email của một bản ghi hộp thư."""
	if not ten:
		return None
	return (frappe.db.get_value(HOP_THU, ten, "email_id") or "").strip() or None


def _hop_thu_mac_dinh():
	"""Hộp thư mặc định để gửi đi, trả về (tên, địa chỉ)."""
	tk = frappe.db.get_value(
		HOP_THU, {"default_outgoing": 1, "enable_outgoing": 1},
		["name", "email_id"], as_dict=True,
	)
	if not tk:
		return None, None
	return tk.get("name"), (tk.get("email_id") or "").strip() or None


def _tim_nguoi_gui(hop_thu_dang_co, loai_chung_tu):
	"""Chọn hộp thư rồi lấy địa chỉ. Trả về (tên hộp thư, địa chỉ)."""
	ten = chon_hop_thu(hop_thu_dang_co, loai_chung_tu)
	dia_chi = _dia_chi_hop_thu(ten)
	if dia_chi:
		return ten, dia_chi
	return _hop_thu_mac_dinh()


def bu_nguoi_gui(doc, method=None):
	"""LỚP 1. Bù ô người gửi ngay sau khi hàng đợi được tạo.

	Gọi từ hook `after_insert` của Email Queue.

	Vì sao `after_insert` chứ không phải `before_insert`: mọi thứ chạy ở
	`before_insert` đều bị tầng `validate` chạy sau đó xoá lại được, và đó
	đúng là chuyện đã xảy ra hôm 17/08. Ghi ở đây bằng `frappe.db.set_value`
	thì đi thẳng xuống bảng, không qua `validate`, nên không hook nào ở tầng
	đó với tới được nữa.

	Tuyệt đối không ném lỗi ra ngoài: hàm này nằm trên đường đi của MỌI email
	trong hệ. Nó hỏng mà chặn luôn việc tạo hàng đợi thì mất cả thư lẫn dấu
	vết, tệ hơn hẳn cái nó đang chữa.
	"""
	try:
		if (doc.get("sender") or "").strip():
			return
		ten, dia_chi = _tim_nguoi_gui(doc.get("email_account"), doc.get("reference_doctype"))
		if not dia_chi:
			frappe.log_error(
				"Khong tim duoc hop thu gui di cho %s (chung tu %s)"
				% (doc.name, doc.get("reference_doctype")),
				"gui_thu: khong co nguoi gui",
			)
			return

		gia_tri = {"sender": dia_chi}
		if ten and not (doc.get("email_account") or "").strip():
			gia_tri["email_account"] = ten
		# Vá luôn dòng From trong thân thư nếu nó cũng trống.
		da_va = va_dong_from(doc.get("message"), dia_chi)
		if da_va and da_va != (doc.get("message") or ""):
			gia_tri["message"] = da_va

		frappe.db.set_value(HANG_DOI, doc.name, gia_tri, update_modified=False)
		# Cập nhật cả bản trong bộ nhớ, để phần chạy tiếp sau trong cùng một
		# lượt yêu cầu nhìn thấy giá trị mới chứ không thấy ô rỗng.
		for k, v in gia_tri.items():
			doc.set(k, v)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "gui_thu: bu nguoi gui loi")


# ============================================================== LỚP 3
#
# Cứu dữ liệu. Bù ô người gửi cho các bản ghi đã kẹt, rồi xếp lại hàng đợi.


def _mo_ta_ket(hang):
	"""Một dòng mô tả bản ghi kẹt, cho người đọc báo cáo."""
	return "%s | %s %s | %s" % (
		hang.get("name"),
		hang.get("reference_doctype") or "khong gan chung tu",
		hang.get("reference_name") or "",
		(hang.get("status") or "").strip(),
	)


@frappe.whitelist()
def va_hang_doi_ket(tu_ngay=None, den_ngay=None, chay_that=0, gioi_han=500,
		loai_chung_tu=None):
	"""LỚP 3. Điền bù người gửi cho hàng đợi đang kẹt rồi cho gửi lại.

	Mặc định CHẠY THỬ: chỉ đếm và liệt kê, không ghi gì. Phải truyền
	`chay_that=1` mới thật sự sửa. Hàm này đụng vào dữ liệu thật của hàng
	đợi thư nên không cho nó tự chạy khi ai đó bấm nhầm.

	Ba việc cho mỗi bản ghi:

	Một, điền `sender` bằng địa chỉ hộp thư đúng theo loại chứng từ. Hai, vá
	dòng `From:` trong thân thư nếu nó cũng trống. Ba, đặt lại trạng thái về
	`Not Sent` và `retry = 0` để bộ lập lịch nhặt lên gửi lại.

	Chỉ đặt lại trạng thái cho bản ghi mà `nen_gui_lai` nói là có ích. Bản
	đã gửi rồi thì tuyệt đối không đụng, gửi lại là nhà cung cấp nhận hai
	lần một đơn. Bản lỗi vì địa chỉ người nhận sai thì điền bù người gửi
	nhưng KHÔNG xếp lại hàng, vì gửi bao nhiêu lần cũng hỏng, phải sửa hồ sơ
	nhà cung cấp trước; những bản đó trả về trong mục `can_nguoi_sua`.

	`loai_chung_tu` để cứu từng nhóm một chứ không thả cả trăm thư ra cùng
	lúc. Nhóm nào cứu trước là quyết định của người, không phải của máy: một
	đơn mua hàng nằm kẹt mấy ngày mà giờ mới tới tay nhà cung cấp thì có thể
	đã đặt lại bằng đường khác rồi, gửi ra là nhà cung cấp làm hai lần.
	"""
	chay_that = cint(chay_that)
	gioi_han = cint(gioi_han) or 500
	dieu = {"status": ["in", ["Error", "Not Sent"]]}
	if tu_ngay and den_ngay:
		dieu["creation"] = ["between", [tu_ngay, den_ngay]]
	elif tu_ngay:
		dieu["creation"] = [">=", tu_ngay]
	elif den_ngay:
		dieu["creation"] = ["<=", den_ngay]
	if loai_chung_tu:
		dieu["reference_doctype"] = loai_chung_tu

	ds = frappe.get_all(
		HANG_DOI,
		filters=dieu,
		fields=["name", "status", "sender", "email_account", "reference_doctype",
			"reference_name", "error", "creation"],
		order_by="creation asc",
		limit=gioi_han,
	)

	da_va, da_xep_lai, can_nguoi_sua, khong_ro_hop_thu, bo_qua = [], [], [], [], []

	for hang in ds:
		co_nguoi_gui = bool((hang.get("sender") or "").strip())
		xep_lai = nen_gui_lai(hang.get("status"), hang.get("error"))

		if co_nguoi_gui and not xep_lai:
			bo_qua.append(_mo_ta_ket(hang))
			continue

		ten_hop_thu, dia_chi = (hang.get("email_account"), hang.get("sender"))
		if not co_nguoi_gui:
			ten_hop_thu, dia_chi = _tim_nguoi_gui(
				hang.get("email_account"), hang.get("reference_doctype")
			)
			if not dia_chi:
				khong_ro_hop_thu.append(_mo_ta_ket(hang))
				continue

		gia_tri = {}
		if not co_nguoi_gui:
			gia_tri["sender"] = dia_chi
			if ten_hop_thu and not (hang.get("email_account") or "").strip():
				gia_tri["email_account"] = ten_hop_thu
			than = frappe.db.get_value(HANG_DOI, hang["name"], "message")
			moi = va_dong_from(than, dia_chi)
			if moi and moi != (than or ""):
				gia_tri["message"] = moi
			da_va.append(_mo_ta_ket(hang))

		if xep_lai:
			# retry về 0 chứ không giữ nguyên: Frappe đếm ba lần rồi bỏ hẳn,
			# mà ba lần đó đều hỏng vì cùng một lý do đã được sửa xong.
			gia_tri.update({"status": "Not Sent", "error": "", "retry": 0})
			da_xep_lai.append(_mo_ta_ket(hang))
		elif (hang.get("status") or "").strip() == "Error":
			can_nguoi_sua.append(
				"%s -> %s" % (_mo_ta_ket(hang), cau_loi(hang.get("error")))
			)

		if gia_tri and chay_that:
			frappe.db.set_value(HANG_DOI, hang["name"], gia_tri, update_modified=False)

	if chay_that:
		frappe.db.commit()

	return {
		"chay_that": chay_that,
		"loai_chung_tu": loai_chung_tu or "tat ca",
		"da_quet": len(ds),
		"da_va_nguoi_gui": len(da_va),
		"da_xep_lai_hang": len(da_xep_lai),
		"can_nguoi_sua": can_nguoi_sua,
		"khong_ro_hop_thu": khong_ro_hop_thu,
		"bo_qua": len(bo_qua),
		"chi_tiet_da_va": da_va[:50],
		"chi_tiet_xep_lai": da_xep_lai[:50],
	}


# =========================================== CỨU MỘT LẦN, KHOẢNG SỰ CỐ

# Khoảng của sự cố, chốt cứng chứ không nhận tham số. Hàm này sinh ra để
# chạy đúng một lần cho đúng một sự cố; mở tham số ra là biến nó thành con
# dao cùn có thể chém vào bất cứ khoảng nào.
SU_CO_TU = "2026-08-16 00:00:00"
SU_CO_DEN = "2026-08-20 23:59:59"

# Hai nhóm anh Việt chốt cứu trước: đơn mua hàng và phiếu yêu cầu vật tư.
# Đây là luồng đang tắc, nhà cung cấp chưa nhận được đơn. Sáu Auto Email
# Report và 35 thư không gắn chứng từ thì để lại, gửi bù báo cáo cũ mấy ngày
# trước chỉ tạo nhiễu.
SU_CO_NHOM = ("Purchase Order", "Material Request")

TRUONG_DA_CUU = "email_da_cuu_su_co_1608"


@frappe.whitelist()
def cuu_su_co_1608(chay_that=0, bo_khoa=0):
	"""Chạy một lần: cứu email đơn mua hàng và yêu cầu vật tư kẹt từ 16/08.

	Mặc định CHẠY THỬ. Truyền `chay_that=1` mới sửa thật.

	Chạy thật đúng MỘT lần rồi tự khoá: sau lần đầu, hàm ghi mốc vào
	Vagabond Settings và những lần gọi sau trả về ngay. Lý do là hàm này
	đẩy thư ra ngoài tới nhà cung cấp; gọi nhầm lần thứ hai là nhà cung cấp
	nhận hai lần một đơn, và không có cách nào rút lại. Cần chạy lại thật
	thì truyền `bo_khoa=1`, tức là phải cố ý.

	Chỉ người có quyền ghi trên hàng đợi thư gọi được.
	"""
	if not frappe.has_permission("Email Queue", "write"):
		frappe.throw("Chỉ quản trị hệ thống chạy được lệnh cứu này.")
	chay_that = cint(chay_that)

	da_chay = frappe.db.get_single_value("Vagabond Settings", TRUONG_DA_CUU)
	if chay_that and da_chay and not cint(bo_khoa):
		return {
			"da_chay_roi": 1,
			"luc": str(da_chay),
			"nhac": (
				"Lệnh cứu này đã chạy thật lúc %s rồi. Chạy lại là nhà cung "
				"cấp nhận hai lần một đơn. Thật sự cần thì truyền bo_khoa=1."
			) % da_chay,
		}

	tung_nhom = {}
	for loai in SU_CO_NHOM:
		tung_nhom[loai] = va_hang_doi_ket(
			tu_ngay=SU_CO_TU, den_ngay=SU_CO_DEN, chay_that=chay_that,
			gioi_han=500, loai_chung_tu=loai,
		)

	if chay_that:
		frappe.db.set_single_value(
			"Vagabond Settings", TRUONG_DA_CUU, now_datetime()
		)
		frappe.db.commit()

	return {
		"chay_that": chay_that,
		"tu": SU_CO_TU,
		"den": SU_CO_DEN,
		"tung_nhom": tung_nhom,
		"tong_va_nguoi_gui": sum(
			x.get("da_va_nguoi_gui", 0) for x in tung_nhom.values()
		),
		"tong_xep_lai_hang": sum(
			x.get("da_xep_lai_hang", 0) for x in tung_nhom.values()
		),
		"nhac": (
			"Đây mới là chạy thử, chưa sửa gì. Đọc kỹ rồi truyền chay_that=1."
			if not chay_that
			else "Đã xếp lại hàng đợi. Bộ lập lịch nhặt lên trong vài phút."
		),
	}


# ========================================================= CẢNH BÁO
#
# Nhiều ngày không ai biết. Đây là phần để lần sau máy tự hú.


TRUONG_WEBHOOK = "webhook_bao_dong"
TRUONG_LAN_HU = "email_bao_dong_lan_cuoi"

# Hú xong thì im bao nhiêu phút. Không có mốc này thì nhịp quét mỗi mười lăm
# phút sẽ bắn lại đúng một sự cố suốt cả đêm, và tin thứ năm trở đi thì
# không ai đọc nữa.
IM_SAU_KHI_HU_PHUT = 180


def _webhook():
	return (
		frappe.db.get_single_value("Vagabond Settings", TRUONG_WEBHOOK) or ""
	).strip()


def ban_webhook(cau):
	"""Đẩy một tin nhắn báo động tới webhook nhóm quản trị.

	Viết theo dạng chung `{"text": ...}` chứ không viết riêng cho Zalo hay
	Lark. Zalo ZNS bên `vagabond/zalo.py` không dùng được ở đây vì nó gửi
	theo mẫu tới một số điện thoại, không bắn được vào nhóm. Lark, Slack,
	Google Chat, và Zalo qua cầu trung gian đều nhận dạng này.

	Không có URL thì thôi, không coi là lỗi: cảnh báo còn đường thư dự phòng.
	"""
	url = _webhook()
	if not url:
		return False
	try:
		import requests

		requests.post(
			url,
			data=json.dumps({"text": cau, "msg_type": "text",
				"content": {"text": cau}}, ensure_ascii=False).encode("utf-8"),
			headers={"Content-Type": "application/json"},
			timeout=10,
		)
		return True
	except Exception:
		frappe.log_error(frappe.get_traceback(), "gui_thu: ban webhook loi")
		return False


def _bao_bang_thu(cau, so_loi):
	"""Đường dự phòng: gửi thư cho địa chỉ khai ở Vagabond Settings.

	Có vẻ trớ trêu khi báo sự cố email bằng email. Nhưng lỗi hay gặp là hỏng
	MỘT hộp thư chứ không phải hỏng cả máy chủ, mà thư cảnh báo đi từ hộp
	mặc định, nên phần lớn trường hợp nó vẫn tới. Webhook mới là đường
	chính, đây chỉ là đường thứ hai.
	"""
	dia_chi = [
		e.strip()
		for e in re.split(
			r"[,;\s]+",
			frappe.db.get_single_value("Vagabond Settings", "email_canh_bao") or "",
		)
		if "@" in e
	]
	if not dia_chi:
		return False
	try:
		_ten, nguoi_gui = _hop_thu_mac_dinh()
		frappe.sendmail(
			recipients=dia_chi,
			sender=nguoi_gui,
			subject="[Vagabond] BAO DONG DO: %d email khong gui duoc" % so_loi,
			message=_khung_bao_dong(cau, so_loi),
		)
		return True
	except Exception:
		frappe.log_error(frappe.get_traceback(), "gui_thu: bao bang thu loi")
		return False


def _khung_bao_dong(cau, so_loi):
	"""Thu bao dong do qua khuon thu chung. Noi dung loi giu nguyen dang chu
	don cach de doc duoc ten hop thu va ma loi."""
	try:
		from vagabond import thu_khung as _tk

		than = (
			_tk.doan("Trong cửa sổ vừa qua có <b>%d</b> thư không gửi được. Chi tiết:" % so_loi)
			+ '<pre style="margin:0 0 14px;padding:12px 14px;background:%s;border:1px solid %s;'
			'font-size:12px;line-height:1.55;color:%s;white-space:pre-wrap;word-break:break-word">%s</pre>'
			% (_tk.KEM, _tk.KE, _tk.MUC, frappe.utils.escape_html(cau))
			+ _tk.doan("Mở Desk, vào Email Queue lọc trạng thái Error để xem từng thư.", cach=0)
		)
		return _tk.khung("Email của tiệm đang không gửi được", than, chan="noi_bo", nhan="Báo động đỏ")
	except Exception:
		return "<pre>%s</pre>" % frappe.utils.escape_html(cau)


def canh_bao_email_loi():
	"""Nhịp lập lịch: quét hàng đợi, đủ ngưỡng lỗi thì hú còi.

	Đếm bản ghi trạng thái Error sinh trong cửa sổ vừa qua. Từ ngưỡng trở
	lên thì bắn webhook và gửi thư.

	Đếm bản ghi LỖI chứ không đếm bản ghi chưa gửi: hàng đợi đang dài là
	chuyện bình thường lúc gửi hàng loạt, còn năm cái lỗi trong một giờ thì
	không bao giờ là bình thường ở quy mô tiệm này.

	Không bao giờ ném lỗi: nhịp lập lịch ném lỗi là cả hàng nhịp phía sau
	đứng theo.
	"""
	try:
		moc = add_to_date(now_datetime(), minutes=-CUA_SO_QUET_PHUT)
		ds = frappe.get_all(
			HANG_DOI,
			filters={"status": "Error", "modified": [">=", moc]},
			fields=["name", "error"],
			limit=200,
		)
		if len(ds) < NGUONG_BAO_DONG:
			return

		lan_hu = frappe.db.get_single_value("Vagabond Settings", TRUONG_LAN_HU)
		if lan_hu and lan_hu >= add_to_date(
			now_datetime(), minutes=-IM_SAU_KHI_HU_PHUT
		):
			return

		cau = cau_bao_dong(
			len(ds),
			gom_theo_loai([x.get("error") for x in ds]),
			moc.strftime("%H:%M %d/%m"),
			now_datetime().strftime("%H:%M %d/%m"),
		)
		ban_webhook(cau)
		_bao_bang_thu(cau, len(ds))
		frappe.db.set_single_value("Vagabond Settings", TRUONG_LAN_HU, now_datetime())
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "gui_thu: canh bao loi")


@frappe.whitelist()
def suc_khoe(so_gio=24):
	"""Màn hình hỏi: đường thư đi có đang khoẻ không.

	Trả về số đếm theo trạng thái trong khoảng vừa qua, cộng số bản ghi
	thiếu ô người gửi. Con số cuối cùng chính là con số lẽ ra phải có người
	nhìn thấy hôm 16/08.
	"""
	moc = add_to_date(now_datetime(), hours=-(cint(so_gio) or 24))
	ds = frappe.get_all(
		HANG_DOI,
		filters={"creation": [">=", moc]},
		fields=["status", "sender", "error"],
		limit=5000,
	)
	theo_trang_thai, loi = {}, []
	thieu_nguoi_gui = 0
	for x in ds:
		tt = (x.get("status") or "?").strip()
		theo_trang_thai[tt] = theo_trang_thai.get(tt, 0) + 1
		if not (x.get("sender") or "").strip():
			thieu_nguoi_gui += 1
		if tt == "Error":
			loi.append(x.get("error"))
	return {
		"so_gio": cint(so_gio) or 24,
		"tong": len(ds),
		"theo_trang_thai": theo_trang_thai,
		"thieu_nguoi_gui": thieu_nguoi_gui,
		"loi_theo_loai": {
			ma: {"so_luong": dem, "y_nghia": CAU_CHO_NGUOI_DUNG.get(ma, ma)}
			for ma, dem in gom_theo_loai(loi).items()
		},
	}


@frappe.whitelist()
def gui_bo_thu_mau(email=None, chi_mot=None):
	"""Gửi bộ thư mẫu tới một địa chỉ để soi trên hộp thư thật.

	Anh Việt 03/09/2026: *"Em gửi thử tất cả các email em đã fix đến email anh
	là thevagabondbakery@gmail.com nhé"*. Soi thư trên trình duyệt không thay
	được việc mở nó trong Gmail: Gmail cắt thẻ style, đảo màu ở chế độ tối, và
	bóp bảng lại trên điện thoại.

	Thân thư dựng bằng đúng khuôn đang chạy, nội dung là số liệu mẫu. Không
	đọc đơn nào, không đổi trạng thái gì, tiêu đề luôn mang chữ THƯ MẪU.
	"""
	from vagabond import thu_khung as tk

	return tk.gui_thu_mau(email=email, chi_mot=chi_mot)
