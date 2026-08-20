# -*- coding: utf-8 -*-
"""Thương thảo và điều chỉnh hợp đồng (Contract Amendment).

Loan Anh bên Sales đặt bài, anh Việt chuyển sang 21/08/2026: *"Khách hàng
yêu cầu chỉnh sửa điều khoản hợp đồng sau khi nhận được bản hệ thống sinh
ra. Chúng ta cần bổ sung luồng Thương thảo và Điều chỉnh Hợp đồng."*

===================================================================
NGUYÊN TẮC SỐ MỘT, VIẾT ĐẦU TỆP VÌ NÓ CHI PHỐI CẢ TỆP
===================================================================

Anh Việt: *"Tuyệt đối KHÔNG dùng AI hay tool tự động đọc file của khách để
ghi đè số liệu vào Database. Mọi thay đổi tài chính (số lượng, giá) bắt buộc
Sales phải thao tác tay để bảo vệ tính toàn vẹn của dữ liệu Kế toán và Kho."*

Nên tệp này chia làm hai đường TÁCH HẲN nhau, và chúng không bao giờ gặp
nhau:

  Đường SỐ LIỆU     Sales gõ tay từng ô trên màn. Máy chỉ nhận số, kiểm số,
                    ghi số. Không có một dòng nào đọc tệp ở đường này.

  Đường TỆP         Nhận đúng một tệp PDF, cất đi, ghi lại ai tải lên lúc
                    nào. Máy KHÔNG mở tệp, KHÔNG đọc chữ trong tệp, KHÔNG
                    rút một con số nào ra khỏi tệp.

Vì sao chặt đến vậy: một con số rút sai từ PDF sẽ đi thẳng vào hoá đơn, vào
sổ kế toán, vào lệnh xuất kho. Nó không dừng ở tờ hợp đồng. Và nó sai theo
kiểu êm ru, vì con số vẫn trông rất hợp lý. Bộ kiểm thử nhóm 45 có ba ca
chốt cứng điều này: đường tệp không được chứa lời gọi đọc PDF nào.

===================================================================
VÒNG ĐỜI
===================================================================

    Nháp ──────────┐
    Đã gửi khách ──┼─► Đang thương thảo ──► (chốt) ──► về đúng trạng thái cũ
    Đang thực hiện ┘                    └─► (đóng thương thảo) ──► về cũ

Anh Việt chỉ nói mở từ Nháp. Em mở thêm hai trạng thái nữa, và đây là lý do:

"Đã gửi khách" chính là tình huống Loan Anh mô tả nguyên văn - khách đòi sửa
SAU KHI đã nhận bản hệ thống sinh ra. Gửi thư xong là hợp đồng rơi vào đúng
trạng thái đó. Không mở từ đây thì luồng này không dùng được cho chính cái
việc nó sinh ra để giải quyết.

"Đang thực hiện" là ca thật hay gặp thứ hai: khách đòi sửa sau khi đã ký và
đã bắt đầu chạy. Lúc đó hợp đồng đã có hoá đơn, nên máy cảnh báo rõ số hoá
đơn và số tiền đang treo, để Sales biết mình đang đứng ở đâu.

Điều máy KHÔNG làm, cố ý: không tự sửa, không tự huỷ, không tự lập lại một
hoá đơn nào. Sửa tờ hợp đồng và sửa chứng từ kế toán là hai việc khác nhau,
và trộn chúng lại là cách làm sai sổ mà không ai nhìn ra.

===================================================================
PHIÊN BẢN
===================================================================

Bản gốc là v1, chụp lại ngay lần MỞ thương thảo đầu tiên - lúc đó tờ hợp
đồng vẫn còn nguyên như máy sinh ra. Mỗi lần chốt một lần điều chỉnh thì
sinh v2, v3... kèm bảng khác biệt do máy tự dựng.

Chụp lúc MỞ chứ không chụp lúc tạo hợp đồng: hợp đồng nào không ai đụng tới
thì không cần một hàng phiên bản nào cả, và bày ra một danh sách phiên bản
chỉ có đúng một dòng là làm màn hình bẩn mà không nói thêm điều gì.
"""

import json

DT = "Hop Dong Ban Hang"
DT_PB = "Hop Dong Phien Ban"

TT_NHAP = "Nháp"
TT_DA_GUI = "Đã gửi khách"
TT_THUONG_THAO = "Đang thương thảo"
TT_DANG_LAM = "Đang thực hiện"
TT_HOAN_TAT = "Hoàn tất"
TT_THANH_LY = "Đã thanh lý"
TT_HUY = "Huỷ"

# Trạng thái mở được thương thảo. Hoàn tất, Đã thanh lý và Huỷ thì KHÔNG:
# tờ đã đóng rồi mà mở ra sửa là sửa lịch sử, không phải thương thảo.
#
# LỖI CŨ BẮT ĐƯỢC NHÂN TIỆN, 21/08/2026
# --------------------------------------
# "Đã gửi khách" vốn ĐÃ có trong dữ liệu thật mà KHÔNG có trong ô chọn của
# doctype: `hop_dong_pdf.gui_email` ghi nó vào bằng `frappe.db.set_value`,
# mà `set_value` không kiểm danh sách Select nên không ai báo gì suốt từ
# đó tới nay. Hậu quả: mọi hợp đồng đã gửi thư đều mang một trạng thái
# không nằm trong danh sách, mở trên Desk ra thì ô trạng thái trông như
# trống, và bộ lọc theo trạng thái không bao giờ tìm thấy chúng.
#
# Cách vá: khai nó vào doctype cho khớp với dữ liệu THẬT, chứ không đi sửa
# dữ liệu cũ. Sửa dữ liệu là xoá mất dấu vết những tờ đã gửi khách thật.
MO_DUOC = (TT_NHAP, TT_DA_GUI, TT_DANG_LAM)

# Trường được theo dõi qua từng phiên bản, kèm nhãn tiếng Việt và kiểu.
#
# Khai một chỗ này thôi, và cả ba việc dùng chung: chụp ảnh, so sánh, và
# danh sách ô Sales được sửa lúc thương thảo. Ba danh sách riêng là ba cơ
# hội lệch nhau, và lệch ở đây nghĩa là một ô đổi mà không ai thấy trong
# nhật ký.
TRUONG_THEO_DOI = (
	("ten", "Tên hợp đồng", "chu"),
	("so_hop_dong", "Số hợp đồng", "chu"),
	("loai", "Loại hợp đồng", "chu"),
	("khach_hang", "Khách hàng", "chu"),
	("ngay_ky", "Ngày ký", "ngay"),
	("ngay_su_kien", "Ngày sự kiện / giao", "ngay"),
	("gia_tri", "Giá trị hợp đồng", "tien"),
	("mo_ta", "Mô tả nội dung", "chu"),
	("bao_gia", "Báo giá nguồn", "chu"),
	("ten_khach", "Tên công ty bên A", "chu"),
	("ma_so_thue", "Mã số thuế bên A", "chu"),
	("dia_chi", "Địa chỉ bên A", "chu"),
	("dai_dien", "Người đại diện bên A", "chu"),
	("chuc_vu", "Chức vụ đại diện", "chu"),
	("dien_thoai", "Điện thoại bên A", "chu"),
	("email", "Email nhận hợp đồng", "chu"),
	("dat_coc_pt", "Đợt 1 (%)", "so"),
	("dat_coc_tien", "Tiền đợt 1", "tien"),
	("ngay_dot1", "Số ngày trả đợt 1 sau khi ký", "so"),
	("ngay_dot2", "Số ngày trả đợt 2 trước khi giao", "so"),
	("dia_diem_giao", "Địa điểm bàn giao", "chu"),
	("thoi_gian_giao", "Thời gian bàn giao", "chu"),
	("nguoi_ky_a", "Người ký bên A", "chu"),
	("chuc_vu_ky_a", "Chức vụ người ký bên A", "chu"),
	("nguoi_ky_b", "Người ký bên B", "chu"),
	("chuc_vu_ky_b", "Chức vụ người ký bên B", "chu"),
)

NHAN = {k: n for k, n, _ in TRUONG_THEO_DOI}
KIEU = {k: t for k, _, t in TRUONG_THEO_DOI}

# Ô Sales được sửa trong lúc thương thảo. HẸP HƠN danh sách theo dõi: mã hợp
# đồng, khách hàng và báo giá nguồn KHÔNG cho đổi ở đây.
#
# Vì sao: đổi khách hàng giữa chừng thì tờ hợp đồng không còn là tờ ban đầu
# nữa, đó là một hợp đồng khác và phải lập tờ mới. Đổi báo giá nguồn thì
# Phụ lục 01 đổi theo mà bảng khác biệt lại không nói được là đổi những
# dòng hàng nào - im lặng đúng chỗ nguy hiểm nhất.
SUA_DUOC = (
	"ten", "so_hop_dong", "loai", "ngay_ky", "ngay_su_kien", "gia_tri",
	"mo_ta", "ten_khach", "ma_so_thue", "dia_chi", "dai_dien", "chuc_vu",
	"dien_thoai", "email", "dat_coc_pt", "dat_coc_tien", "ngay_dot1",
	"ngay_dot2", "dia_diem_giao", "thoi_gian_giao",
)


# ===================================================================
# PHẦN THUẦN. Không import frappe ở trong, chạy được bằng python3 trần.
# ===================================================================

def chuan(gt, kieu):
	"""Đưa một giá trị về dạng so sánh được. THUẦN.

	Vì sao cần: cùng một con số, Frappe lúc trả về `50000`, lúc trả về
	`50000.0`, lúc trả về `Decimal('50000.00')`. So thô thì lần nào cũng
	thấy "đã đổi", và một bảng khác biệt lúc nào cũng đầy dòng là một bảng
	không ai đọc nữa.
	"""
	if gt is None:
		return "" if kieu in ("chu", "ngay") else 0
	if kieu in ("tien", "so"):
		try:
			n = float(gt)
		except (TypeError, ValueError):
			return 0
		return round(n, 2)
	return str(gt).strip()


def so_sanh(cu, moi):
	"""Bảng khác biệt giữa hai ảnh chụp. THUẦN.

	Trả về danh sách [{truong, nhan, kieu, tu, den}], đúng thứ tự khai báo
	trong TRUONG_THEO_DOI chứ không phải thứ tự ngẫu nhiên của dict - Giám
	đốc đọc mười dòng thì thứ tự phải cố định, không thì lần nào đọc cũng
	như một tờ mới.
	"""
	ra = []
	cu = cu or {}
	moi = moi or {}
	for k, nhan, kieu in TRUONG_THEO_DOI:
		a = chuan(cu.get(k), kieu)
		b = chuan(moi.get(k), kieu)
		if a == b:
			continue
		ra.append({"truong": k, "nhan": nhan, "kieu": kieu, "tu": a, "den": b})
	return ra


def loc_o_sua_duoc(goi):
	"""Chỉ giữ lại những ô Sales được phép sửa. THUẦN.

	Đây là hàng rào thật, không phải trang trí: màn hình gửi lên ô nào khác
	thì ô đó bị bỏ LẶNG LẼ. Không ném lỗi, vì ném lỗi là nói cho người gửi
	biết ô đó có tồn tại.
	"""
	ra = {}
	for k in SUA_DUOC:
		if k in (goi or {}):
			ra[k] = goi[k]
	return ra


def nhan_phien_ban(n):
	"""Nhãn hiện trên màn và trong thư. THUẦN."""
	return "Hợp đồng v%d" % int(n or 1)


# ===================================================================
# PHẦN CHẠM CƠ SỞ DỮ LIỆU
# ===================================================================
#
# `import frappe` CỐ Ý đặt ở đây chứ không ở đầu tệp, đúng nếp của
# `nhap_sao_ke.py`. Nhờ vậy bộ kiểm thử cắt lấy phần trên rồi chạy thẳng
# bằng python3 trần, không cần dựng cả một site. Phép so sánh phiên bản là
# thứ Giám đốc đọc để biết Sales đã đổi gì, nên nó phải được kiểm bằng dữ
# liệu thật chứ không phải bằng cách đọc lại mã nguồn.

import frappe
from frappe.utils import flt, now_datetime


def _quyen():
	from vagabond.hop_dong import _quyen as q

	q()


def _doc(name):
	if not frappe.db.exists(DT, name):
		frappe.throw("Không tìm thấy hợp đồng %s. Tải lại danh sách giúp em." % name)
	return frappe.get_doc(DT, name)


def anh_chup(doc):
	"""Chụp lại toàn bộ trường được theo dõi của một hợp đồng."""
	return {k: doc.get(k) for k, _, _ in TRUONG_THEO_DOI}


def _so_phien_ban(name):
	return frappe.db.count(DT_PB, {"hop_dong": name})


def _ban_moi_nhat(name):
	ds = frappe.get_all(
		DT_PB, filters={"hop_dong": name},
		fields=["name", "phien_ban", "anh_chup"],
		order_by="phien_ban desc", limit_page_length=1,
	)
	return ds[0] if ds else None


def _tien_hoa_don(name):
	"""Hoá đơn đã chốt của hợp đồng này, để cảnh báo khi sửa giữa chừng."""
	r = frappe.db.sql(
		"""select count(name), coalesce(sum(grand_total), 0)
		from `tabSales Invoice` where custom_hop_dong = %s and docstatus = 1""",
		name,
	)[0]
	return {"so_hoa_don": int(r[0] or 0), "tien_hoa_don": flt(r[1])}


def _ghi_phien_ban(doc, ly_do, khac_biet=None, tep=None):
	"""Ghi một phiên bản. Trả về bản ghi vừa tạo."""
	n = _so_phien_ban(doc.name) + 1
	pb = frappe.get_doc({
		"doctype": DT_PB,
		"hop_dong": doc.name,
		"phien_ban": n,
		"nhan": nhan_phien_ban(n),
		"trang_thai_luc_chot": doc.trang_thai,
		"gia_tri": flt(doc.gia_tri),
		"nguoi": frappe.session.user,
		"luc": now_datetime(),
		"ly_do": (ly_do or "").strip(),
		"khac_biet": json.dumps(khac_biet or [], ensure_ascii=False),
		"anh_chup": json.dumps(anh_chup(doc), ensure_ascii=False, default=str),
		"tep_chot": tep or "",
	})
	pb.flags.ignore_permissions = True
	pb.insert(ignore_permissions=True)
	return pb


@frappe.whitelist()
def mo_thuong_thao(name, ly_do):
	"""Bấm nút Điều chỉnh: chuyển hợp đồng sang Đang thương thảo.

	Bắt buộc ghi lý do. Đây là câu Giám đốc đọc đầu tiên khi mở nhật ký ra,
	và một dòng "khách yêu cầu sửa" trống rỗng thì không giải thích được gì
	sau ba tháng.
	"""
	_quyen()
	ly_do = (str(ly_do or "")).strip()
	if len(ly_do) < 5:
		frappe.throw(
			"Phải ghi rõ khách yêu cầu sửa cái gì, ít nhất 5 ký tự. Câu này "
			"nằm lại trong nhật ký và là thứ giải thích vì sao tờ hợp đồng đổi."
		)
	doc = _doc(name)
	if doc.trang_thai == TT_THUONG_THAO:
		frappe.throw("Hợp đồng này đang thương thảo rồi. Sửa số liệu rồi bấm Chốt điều chỉnh.")
	if doc.trang_thai not in MO_DUOC:
		frappe.throw(
			"Hợp đồng đang ở trạng thái %s nên không mở thương thảo được. Chỉ mở "
			"được khi còn Nháp, Đã gửi khách hoặc Đang thực hiện. Tờ đã Hoàn tất "
			"hay Đã thanh lý mà sửa là sửa lịch sử, cần đổi thì lập phụ lục hoặc "
			"lập tờ mới." % doc.trang_thai
		)

	# Bản gốc: chụp NGAY TRƯỚC khi ai đó đụng vào ô nào.
	if not _so_phien_ban(doc.name):
		_ghi_phien_ban(doc, "Bản gốc do hệ thống sinh, chụp lại lúc mở thương thảo lần đầu.")

	tt_cu = doc.trang_thai
	frappe.db.set_value(DT, doc.name, {
		"trang_thai": TT_THUONG_THAO,
		"tt_truoc_thuong_thao": tt_cu,
		"ly_do_thuong_thao": ly_do,
		"nguoi_mo_thuong_thao": frappe.session.user,
		"ngay_mo_thuong_thao": now_datetime(),
	})
	try:
		doc.add_comment("Comment", "Mở thương thảo. Lý do: %s" % ly_do)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hop_dong_dieu_chinh: ghi vet mo thuong thao")
	frappe.db.commit()

	tien = _tien_hoa_don(doc.name)
	nhac = ""
	if tien["so_hoa_don"]:
		nhac = (
			"Hợp đồng này đã có %d hoá đơn chốt, tổng %s đ. Sửa số liệu ở đây "
			"KHÔNG đụng tới hoá đơn nào. Nếu tiền đổi thì phải làm việc với kế "
			"toán về chứng từ, máy cố ý không tự sửa hộ."
			% (tien["so_hoa_don"], "{:,.0f}".format(tien["tien_hoa_don"]).replace(",", "."))
		)
	return {"ok": 1, "trang_thai": TT_THUONG_THAO, "nhac": nhac, "phien_ban": _so_phien_ban(doc.name)}


@frappe.whitelist()
def cap_nhat_so_lieu(name, gt=None):
	"""Sales gõ tay số liệu mới trong lúc thương thảo.

	ĐÂY LÀ ĐƯỜNG DUY NHẤT số liệu hợp đồng đổi được sau khi đã sinh tờ, và
	nó nhận số từ BÀN PHÍM của Sales chứ không từ bất cứ tệp nào. Xem nguyên
	tắc số một ở đầu tệp.
	"""
	_quyen()
	doc = _doc(name)
	if doc.trang_thai != TT_THUONG_THAO:
		frappe.throw(
			"Chỉ sửa được số liệu khi hợp đồng đang thương thảo. Bấm nút Điều "
			"chỉnh trước, ghi lý do, rồi mới sửa."
		)
	goi = frappe.parse_json(gt) if isinstance(gt, str) else (gt or {})
	if not isinstance(goi, dict):
		frappe.throw("Dữ liệu gửi lên không đúng định dạng.")
	sach = loc_o_sua_duoc(goi)
	if not sach:
		frappe.throw("Không có ô nào để cập nhật.")

	dat = {}
	for k, v in sach.items():
		kieu = KIEU.get(k)
		if kieu in ("tien", "so"):
			dat[k] = flt(v)
		elif kieu == "ngay":
			dat[k] = v or None
		else:
			dat[k] = (str(v or "")).strip()
	if "gia_tri" in dat and dat["gia_tri"] < 0:
		frappe.throw("Giá trị hợp đồng không âm được. Kiểm lại con số vừa gõ giúp em.")
	if "dat_coc_pt" in dat and not (0 <= dat["dat_coc_pt"] <= 100):
		frappe.throw("Phần trăm đợt 1 phải nằm trong khoảng 0 đến 100.")
	# Chup lai TEN O TRUOC khi goi set_value: Frappe nhet them `modified` va
	# `modified_by` vao chinh cai dict minh dua vao, nen doc sau khi goi thi
	# man hinh bao "da luu 6 o" trong khi nguoi ta chi sua 4. Bat duoc luc
	# chay thu tren site that ngay 21/08/2026.
	da_sua = sorted(dat.keys())
	frappe.db.set_value(DT, doc.name, dat)
	frappe.db.commit()
	return {"ok": 1, "da_sua": da_sua}


@frappe.whitelist()
def chot_dieu_chinh(name, ghi_chu=None):
	"""Chốt bản đang thương thảo: sinh phiên bản mới và trả về trạng thái cũ."""
	_quyen()
	doc = _doc(name)
	if doc.trang_thai != TT_THUONG_THAO:
		frappe.throw("Hợp đồng không đang thương thảo nên không có gì để chốt.")

	truoc = _ban_moi_nhat(doc.name)
	cu = {}
	if truoc:
		try:
			cu = json.loads(truoc.get("anh_chup") or "{}")
		except ValueError:
			cu = {}
	khac = so_sanh(cu, anh_chup(doc))

	ve = doc.get("tt_truoc_thuong_thao") or TT_NHAP
	if ve not in MO_DUOC:
		ve = TT_NHAP
	ly_do = (doc.get("ly_do_thuong_thao") or "").strip()
	if ghi_chu and str(ghi_chu).strip():
		ly_do = (ly_do + " | " + str(ghi_chu).strip()).strip(" |")

	frappe.db.set_value(DT, doc.name, {
		"trang_thai": ve,
		"tt_truoc_thuong_thao": "",
	})
	doc.reload()
	pb = _ghi_phien_ban(doc, ly_do, khac)
	try:
		doc.add_comment(
			"Comment",
			"Chốt %s, %d ô đổi so với bản trước." % (pb.nhan, len(khac)),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hop_dong_dieu_chinh: ghi vet chot")
	frappe.db.commit()
	_bao_giam_doc(doc, pb, khac)
	return {
		"ok": 1,
		"trang_thai": ve,
		"phien_ban": pb.phien_ban,
		"nhan": pb.nhan,
		"so_o_doi": len(khac),
		"khac_biet": khac,
		"loi_nhan": (
			"Đã chốt %s. %s"
			% (pb.nhan,
			   ("%d ô đổi so với bản trước." % len(khac)) if khac
			   else "Không ô nào đổi so với bản trước, phiên bản này chỉ ghi lại mốc thời gian.")
		),
	}


@frappe.whitelist()
def huy_thuong_thao(name):
	"""Thôi không thương thảo nữa, trả hợp đồng về trạng thái cũ.

	KHÔNG sinh phiên bản: không có gì được chốt cả. Nhưng vẫn ghi một dòng
	nhật ký, vì việc đã mở ra rồi đóng lại cũng là một việc đã xảy ra.
	"""
	_quyen()
	doc = _doc(name)
	if doc.trang_thai != TT_THUONG_THAO:
		frappe.throw("Hợp đồng không đang thương thảo.")
	ve = doc.get("tt_truoc_thuong_thao") or TT_NHAP
	if ve not in MO_DUOC:
		ve = TT_NHAP
	frappe.db.set_value(DT, doc.name, {"trang_thai": ve, "tt_truoc_thuong_thao": ""})
	try:
		doc.add_comment("Comment", "Đóng thương thảo, không chốt điều chỉnh nào.")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hop_dong_dieu_chinh: ghi vet huy")
	frappe.db.commit()
	return {"ok": 1, "trang_thai": ve}


def _bao_giam_doc(doc, pb, khac):
	"""Báo Giám đốc rằng Sales vừa chốt một lần điều chỉnh. Nuốt lỗi.

	Anh Việt: *"để Giám đốc biết Sales đã thay đổi gì so với bản gốc ban
	đầu."* Nhật ký nằm sẵn trên màn, nhưng nhật ký chỉ trả lời khi có người
	mở ra xem. Một cái chuông thì nói ngay lúc việc vừa xảy ra.
	"""
	try:
		from vagabond import thong_bao
		from vagabond.viec_can_lam import VAI_GIAM_DOC

		tom = ", ".join(k["nhan"] for k in khac[:3]) or "không ô nào"
		if len(khac) > 3:
			tom += " và %d ô nữa" % (len(khac) - 3)
		thong_bao.bao_cho_vai(
			sorted(VAI_GIAM_DOC),
			"Hợp đồng vừa được điều chỉnh",
			"%s · %s · đổi: %s" % (doc.name, pb.nhan, tom),
			"/bep",
			"hd-%s" % doc.name,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hop_dong_dieu_chinh: bao giam doc loi")


@frappe.whitelist()
def lich_su(name):
	"""Nhật ký phiên bản của một hợp đồng, mới nhất lên đầu."""
	_quyen()
	ra = []
	for r in frappe.get_all(
		DT_PB, filters={"hop_dong": name},
		fields=["name", "phien_ban", "nhan", "trang_thai_luc_chot", "gia_tri",
		        "nguoi", "luc", "ly_do", "khac_biet", "tep_chot"],
		order_by="phien_ban desc", limit_page_length=60,
	):
		try:
			r["khac_biet"] = json.loads(r.get("khac_biet") or "[]")
		except ValueError:
			r["khac_biet"] = []
		r["luc"] = str(r.get("luc") or "")
		ra.append(r)
	return {"ds": ra, "tong": len(ra)}


# ===================================================================
# ĐƯỜNG TỆP: nhận bản hợp đồng hai bên đã chốt bên ngoài
# ===================================================================
#
# Anh Việt: *"Khi Sales upload một file PDF (do hai bên tự redline và chốt
# bên ngoài), hệ thống sẽ vô hiệu hóa nút Xuất PDF tự động của Form mẫu, và
# sử dụng chính cái file Sales vừa upload làm file Hợp đồng chuẩn để gửi
# Email cho khách hoặc chuyển sang bước Ký kết."*
#
# ĐỌC KỸ ĐOẠN NÀY TRƯỚC KHI SỬA BẤT CỨ DÒNG NÀO BÊN DƯỚI.
#
# Ba hàm dưới đây làm đúng ba việc: cất tệp, gỡ tệp, trả tệp về cho người
# tải xuống. Chúng KHÔNG mở tệp, KHÔNG đọc chữ trong tệp, KHÔNG rút một con
# số nào ra khỏi tệp, và KHÔNG ghi một trường tài chính nào của hợp đồng.
#
# Nếu ngày nào đó có ai muốn "cho máy tự đọc PDF rồi điền giá hộ Sales cho
# nhanh" thì đó chính là việc anh Việt đã cấm, và nó bị cấm vì một con số
# rút sai từ PDF không dừng ở tờ hợp đồng: nó chảy thẳng vào hoá đơn, vào
# sổ kế toán và vào lệnh xuất kho, mà vẫn trông rất hợp lý.

# 20 MB: một tờ hợp đồng có scan chữ ký hai bên nặng nhất cũng chỉ vài MB.
TRAN_TEP = 20 * 1024 * 1024
DUOI_NHAN = (".pdf",)


def _kiem_duoi(ten):
	"""Chỉ nhận PDF. THUẦN theo nghĩa chỉ soi cái tên, không mở tệp."""
	t = str(ten or "").strip().lower()
	return t.endswith(DUOI_NHAN)


@frappe.whitelist()
def tai_ban_chot(name, ten=None, noi_dung=None, ghi_chu=None):
	"""Nhận bản PDF hai bên đã chốt và đặt nó làm bản hợp đồng chuẩn.

	Cất tệp, ghi lại ai tải lên lúc nào, hết. Không đọc nội dung tệp.
	"""
	_quyen()
	doc = _doc(name)
	ten = (str(ten or "")).strip() or "hop-dong-da-chot.pdf"
	if not _kiem_duoi(ten):
		frappe.throw(
			"Chỉ nhận tệp PDF. Bản Word thì bấm Lưu thành PDF rồi tải lên lại, "
			"vì bản gửi khách phải là bản không sửa được nữa."
		)
	noi = (str(noi_dung or "")).strip()
	if not noi:
		frappe.throw("Chưa chọn tệp. Bấm Chọn tệp rồi thử lại giúp em.")
	if "," in noi and noi[:5].lower() == "data:":
		noi = noi.split(",", 1)[1]
	import base64

	try:
		so_byte = len(base64.b64decode(noi))
	except Exception:
		frappe.throw("Tệp gửi lên hỏng giữa đường nên máy không nhận được. Chọn lại tệp giúp em.")
	if so_byte <= 0:
		frappe.throw("Tệp rỗng. Kiểm lại tệp trên máy giúp em.")
	if so_byte > TRAN_TEP:
		frappe.throw(
			"Tệp nặng %s MB, quá 20 MB. Xuất lại bản PDF nhẹ hơn giúp em."
			% ("{:.1f}".format(so_byte / 1024.0 / 1024.0))
		)

	# Frappe tu kiem va nen lai tep PDF luc luu. Tep hong thi no nem
	# PdfStreamError - mot cau tieng Anh khong noi len dieu gi voi Sales
	# dang dung dien thoai. Boc lai theo QT-24: noi ro phai lam gi tiep.
	#
	# Luu y cho nguoi doc sau: phep kiem do la CUA KHUNG Frappe, khong phai
	# cua tep nay. No chi xac nhan tep con doc duoc, va KHONG rut mot con
	# so nao ra khoi tep. Nguyen tac so mot o dau tep van nguyen ven.
	try:
		f = frappe.get_doc({
			"doctype": "File", "file_name": ten,
			"attached_to_doctype": DT, "attached_to_name": doc.name,
			"content": noi, "decode": True, "is_private": 1,
		})
		f.flags.ignore_permissions = True
		f.insert(ignore_permissions=True)
	except Exception as e:
		if "Pdf" in type(e).__name__ or "pdf" in str(e).lower():
			frappe.log_error(frappe.get_traceback(), "hop_dong_dieu_chinh: tep PDF hong")
			frappe.throw(
				"Tệp PDF này máy đọc không ra, nhiều khả năng nó hỏng hoặc bị "
				"khoá mật khẩu. Mở lại bằng máy tính, bấm In rồi chọn Lưu thành "
				"PDF để xuất một bản mới, xong tải lên lại giúp em."
			)
		raise

	frappe.db.set_value(DT, doc.name, {
		"tep_hop_dong_chot": f.file_url,
		"tep_chot_ten": ten,
		"tep_chot_nguoi": frappe.session.user,
		"tep_chot_luc": now_datetime(),
		"tep_chot_ghi_chu": (str(ghi_chu or "")).strip(),
	})
	try:
		doc.add_comment(
			"Comment",
			"Tải lên bản hợp đồng đã chốt %s. Từ nay tờ gửi khách là bản này, "
			"không phải bản máy tự sinh." % ten,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hop_dong_dieu_chinh: ghi vet tai ban chot")
	frappe.db.commit()
	return {
		"ok": 1,
		"tep": f.file_url,
		"ten": ten,
		"loi_nhan": (
			"Đã đặt %s làm bản hợp đồng chuẩn. Nút Xuất PDF tự sinh đã tắt, "
			"thư gửi khách sẽ đính đúng tệp này." % ten
		),
	}


@frappe.whitelist()
def go_ban_chot(name, ly_do):
	"""Gỡ bản đã tải lên, quay lại dùng tờ máy tự sinh. Bắt buộc ghi lý do.

	QT-20: chỉ bỏ trỏ trên hợp đồng, tệp vẫn nằm trong kho tệp của hệ thống.
	"""
	_quyen()
	ly_do = (str(ly_do or "")).strip()
	if not ly_do:
		frappe.throw("Phải ghi lý do gỡ thì người sau mới hiểu vì sao tờ gửi khách đổi lại.")
	doc = _doc(name)
	cu = (doc.get("tep_chot_ten") or doc.get("tep_hop_dong_chot") or "").strip()
	if not cu:
		frappe.throw("Hợp đồng này chưa có bản tải lên nào, không có gì để gỡ.")
	frappe.db.set_value(DT, doc.name, {
		"tep_hop_dong_chot": "", "tep_chot_ten": "",
		"tep_chot_ghi_chu": "", "tep_chot_luc": None,
	})
	try:
		doc.add_comment(
			"Comment",
			"Gỡ bản hợp đồng đã chốt %s. Lý do: %s. Tờ gửi khách quay lại bản "
			"máy tự sinh." % (cu, ly_do),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hop_dong_dieu_chinh: ghi vet go ban chot")
	frappe.db.commit()
	return {"ok": 1, "loi_nhan": "Đã gỡ %s. Tờ gửi khách quay lại bản máy tự sinh." % cu}


def ban_chot_cua(name):
	"""Đường dẫn bản đã chốt của hợp đồng, rỗng nếu chưa có.

	Hàm này là CÁI CÔNG mà hop_dong_pdf.py hỏi trước khi dựng tờ. Để một
	chỗ chứ không để mỗi nơi tự đọc trường: mỗi nơi tự đọc là hôm nào thêm
	một đường gửi thư mới lại quên hỏi, và khách nhận nhầm bản máy tự sinh
	sau khi hai bên đã chốt bản khác.
	"""
	try:
		return (frappe.db.get_value(DT, name, "tep_hop_dong_chot") or "").strip()
	except Exception:
		return ""


@frappe.whitelist()
def tai_ve_ban_chot(name):
	"""Trả bản đã chốt về cho màn hình tải xuống, dạng base64."""
	_quyen()
	duong = ban_chot_cua(name)
	if not duong:
		frappe.throw("Hợp đồng này chưa có bản đã chốt nào được tải lên.")
	import base64

	f = frappe.get_doc("File", {"file_url": duong})
	noi = f.get_content()
	if isinstance(noi, str):
		noi = noi.encode()
	return {
		"ten_file": f.file_name or "hop-dong-da-chot.pdf",
		"kieu": "application/pdf",
		"b64": base64.b64encode(noi).decode(),
	}
