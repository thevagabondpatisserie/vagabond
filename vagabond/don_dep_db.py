# -*- coding: utf-8 -*-
"""Dọn ba bảng nhật ký mà Frappe không bao giờ tự dọn (#284).

Ngày 12/09/2026 bảng điều khiển Frappe Cloud báo thẳng *"Database or Disk
usage limits exceeded. Upgrade plan or reduce usage to avoid suspension"*:
database 1,25 GB trên trần 1 GB. Ngày 19/08/2026 con số này mới là 0,88 GB,
tức chưa đầy một tháng đã phình thêm gần 400 MB. Site bị khoá ghi nghĩa là
cả tiệm không lập được chứng từ và không xuất được hoá đơn.

VÌ SAO PHẢI VIẾT CODE, CHỨ KHÔNG CHỈNH ĐƯỢC TRÊN MÀN LOG SETTINGS

Frappe có sẵn Log Settings và mỗi đêm tự dọn, nhưng nó chỉ dọn được các
doctype kế thừa lớp LogType. Đọc mã nguồn frappe nhánh version-16:

  - LogSettings.remove_unsupported_doctypes() GỠ BỎ mọi dòng có doctype
    không thoả, qua _supports_log_clearing(), tức phép
    issubclass(controller, LogType). Nghĩa là thêm tay trên màn hình cũng bị
    gỡ im lặng, không một lời báo.
  - frappe/core/doctype/version/version.py KHÔNG có method clear_old_logs.
    Các method của nó: update_version_info, set_impersonator, set_diff,
    for_insert, get_data, onload.
  - default_log_clearing_doctypes trong hooks của frappe có 15 dòng, không
    dòng nào là Version, Notification Log hay Deleted Document.

Đối chiếu trên site: Log Settings đang có đúng 14 dòng, trùng khít danh sách
mặc định của khung, chưa ai tuỳ chỉnh gì. Nên tabVersion CHƯA TỪNG được dọn
kể từ ngày dựng site, và đó đúng là lý do nó phình tới 113,80 MB trong khi
Error Log có retention 14 ngày chỉ nằm ở 35,15 MB.

BA THỨ PHẢI NHỚ KHI ĐỌC CON SỐ SAU KHI DỌN

1. DELETE không trả chỗ trống cho hệ điều hành ngay. InnoDB giữ vùng vừa
   giải phóng trong chính tệp bảng để dùng lại, nên con số trên Frappe Cloud
   có thể CHƯA tụt sau lần dọn đầu, nhưng bảng sẽ thôi phình thêm. Bước gọn
   tệp (OPTIMIZE TABLE) mới làm tệp co lại, và bước đó có thể bị từ chối vì
   quyền.
2. Dọn hết ba bảng này cũng chưa chắc lọt xuống dưới trần. Tổng phần dọn
   được tối đa khoảng 241 MB, từ 1,25 GB trừ đi còn khoảng 1,04 GB, vẫn trên
   trần 1 GB. Vì vậy anh Việt chốt nâng gói trước, dọn sau. Tệp này là để
   chuyện đó không tái diễn.
3. Xoá một phát vài trăm nghìn dòng là khoá bảng lâu. Giờ hành chính mà khoá
   bảng thì quầy không tính tiền được. Nên xoá theo lô, commit giữa các lô,
   và có trần cho mỗi lần chạy. Dọn không hết một đêm thì đêm sau dọn tiếp.
"""

import frappe

# --------------------------------------------------------------- phần thuần
# Phần trên mốc "phần cần Frappe" KHÔNG chạm Frappe, để kiểm thử được mà
# không cần site.

# Ba bảng dọn được, và số ngày giữ lại.
#
# Version 180 ngày: anh Việt chốt 12/09/2026. Đủ tra "ai sửa chứng từ này"
#   cho nửa năm gần nhất, là khoảng thời gian thực tế người ta còn hỏi lại.
# Notification Log 30 ngày: chuông trong app, quá 30 ngày không ai mở lại.
# Deleted Document 180 ngày: giữ cùng mốc với Version, vì hai bảng này hay
#   phải đọc chung khi truy một chứng từ đã biến mất.
BANG_DON = {
	"Version": 180,
	"Notification Log": 30,
	"Deleted Document": 180,
}

# Mỗi lô xoá bao nhiêu dòng. 2.000 giữ cho mỗi câu DELETE đủ ngắn để không
# khoá bảng lâu tới mức quầy thấy.
LO = 2000

# Trần mỗi bảng mỗi lần chạy. Thà chậm vài đêm còn hơn một đêm nặng làm site
# treo đúng lúc đang có người bán hàng.
TRAN_MOI_BANG = 50000

# Xoá được ít hơn ngưỡng này thì KHÔNG gọn tệp. OPTIMIZE TABLE dựng lại cả
# bảng và khoá nó suốt thời gian đó, nên chỉ đáng làm khi vừa xoá đủ nhiều
# để có chỗ mà thu lại.
NGUONG_GON = 5000

# Danh sách chặn cứng. Đây là HÀNG RÀO CHẠY THẬT, không phải tài liệu: nó
# được gọi ở đầu MỖI lần dọn chứ không chỉ trong bộ kiểm, vì cấu hình có thể
# bị người sau sửa mà không ai chạy lại bộ kiểm.
#
# Riêng MInvoice Invoice là hoá đơn điện tử đã gửi cơ quan thuế. Anh Việt
# chốt 13/08/2026: không đụng tới dữ liệu quá khứ đã xuất chứng từ.
KHONG_DUOC_DON = {
	"Sales Invoice",
	"Sales Invoice Item",
	"Purchase Invoice",
	"Purchase Invoice Item",
	"Payment Entry",
	"Payment Entry Reference",
	"GL Entry",
	"Journal Entry",
	"Journal Entry Account",
	"Stock Ledger Entry",
	"Stock Entry",
	"Stock Entry Detail",
	"Delivery Note",
	"Delivery Note Item",
	"Purchase Receipt",
	"Purchase Receipt Item",
	"Purchase Order",
	"Purchase Order Item",
	"Sales Order",
	"Sales Order Item",
	"Quotation",
	"Customer",
	"Supplier",
	"Address",
	"Contact",
	"Item",
	"BOM",
	"BOM Item",
	"Work Order",
	"MInvoice Invoice",
	"Vagabond Ho So TT",
}


def kiem_an_toan(bang=None):
	"""Chặn cứng: không doctype nghiệp vụ nào được lọt vào diện dọn.

	Ném ValueError chứ không trả về False, để người gọi không thể lỡ bỏ qua
	kết quả. Gọi ở đầu MỖI lần dọn, không chỉ trong bộ kiểm.
	"""
	bang = BANG_DON if bang is None else bang
	pham = sorted(set(bang) & KHONG_DUOC_DON)
	if pham:
		raise ValueError("doctype nghiep vu khong duoc don: " + ", ".join(pham))
	return True


def ten_bang(dt):
	"""Tên bảng SQL của một doctype ĐÃ KHAI trong BANG_DON.

	Tên bảng không tham số hoá được nên phải nối chuỗi vào câu lệnh, và đây
	là hàng rào cho đúng chỗ đó: chỉ doctype đã khai mới đi qua được.
	"""
	if dt not in BANG_DON:
		raise ValueError("doctype chua khai trong BANG_DON: %r" % (dt,))
	kiem_an_toan()
	return "tab" + dt


def can_gon(da_xoa):
	"""Xoá được bấy nhiêu dòng thì có đáng gọn tệp không."""
	try:
		n = int(da_xoa or 0)
	except (TypeError, ValueError):
		return False
	return n >= NGUONG_GON


# ------------------------------------------------------- phần cần Frappe


def _moc(so_ngay):
	from frappe.utils import add_days, nowdate

	return add_days(nowdate(), -int(so_ngay))


def _so_dong_vua_xoa():
	"""Đọc ROW_COUNT() của câu lệnh vừa chạy.

	PHẢI gọi NGAY SAU câu DELETE và TRƯỚC khi commit. COMMIT là một câu lệnh,
	nên sau nó ROW_COUNT() trả về giá trị của chính COMMIT chứ không phải của
	DELETE. Đọc sau commit là luôn thấy 0, vòng lặp dừng ngay ở lô đầu và
	nhịp dọn im lặng không làm gì cả.
	"""
	try:
		n = int(frappe.db.sql("select row_count()")[0][0])
	except Exception:
		return 0
	return n if n > 0 else 0


def don_mot_bang(dt, so_ngay=None, lo=None, tran=None):
	"""Xoá dần dòng cũ của MỘT bảng. Trả về số dòng đã xoá."""
	bang = ten_bang(dt)
	moc = _moc(BANG_DON[dt] if so_ngay is None else so_ngay)
	lo = int(lo or LO)
	tran = int(tran or TRAN_MOI_BANG)
	da_xoa = 0
	while da_xoa < tran:
		con = min(lo, tran - da_xoa)
		frappe.db.sql(
			"delete from `%s` where creation < %%s limit %%s" % bang,
			(moc, con),
		)
		xoa = _so_dong_vua_xoa()
		frappe.db.commit()
		da_xoa += xoa
		# Lô cuối trả về ít hơn số xin nghĩa là hết dòng cũ, dừng luôn chứ
		# đừng chạy thêm một câu DELETE rỗng.
		if xoa < con:
			break
	if can_gon(da_xoa):
		gon_tep(bang)
	return da_xoa


def gon_tep(bang):
	"""Thu tệp bảng lại sau khi xoá.

	Bọc bắt lỗi vì tài khoản database của site có thể không có quyền
	OPTIMIZE, và thiếu quyền thì chỉ là không co được tệp, không được phép
	làm hỏng cả nhịp dọn đã chạy xong phần việc chính.
	"""
	try:
		frappe.db.sql("optimize table `%s`" % bang)
		frappe.db.commit()
		return True
	except Exception:
		frappe.log_error(frappe.get_traceback(), "don_dep_db: gon tep %s" % bang)
		return False


def don_dep_hang_ngay():
	"""Nhịp đêm 03:20. KHÔNG whitelist: chỉ scheduler gọi.

	Một bảng hỏng không được kéo theo hai bảng còn lại, nên mỗi bảng bọc lỗi
	riêng và vẫn ghi lại để sáng ra đọc được.
	"""
	kiem_an_toan()
	ket = {}
	for dt in BANG_DON:
		try:
			ket[dt] = don_mot_bang(dt)
		except Exception:
			ket[dt] = 0
			frappe.log_error(frappe.get_traceback(), "don_dep_db: don %s" % dt)
	return ket


def _chan_neu_khong_phai_quan_tri():
	if "System Manager" not in (frappe.get_roles() or []):
		frappe.throw("Chỉ System Manager mới chạy và xem được phần dọn cơ sở dữ liệu.")


@frappe.whitelist()
def don_dep_ngay_bay_gio():
	"""Nút bấm tay, dùng khi Frappe Cloud đang cảnh báo mà chưa tới 03:20."""
	_chan_neu_khong_phai_quan_tri()
	return don_dep_hang_ngay()


@frappe.whitelist()
def do_dung_luong(so_bang=15):
	"""Các bảng to nhất, để khỏi phải đi mò lại báo cáo của khung mỗi lần."""
	_chan_neu_khong_phai_quan_tri()
	try:
		n = int(so_bang or 15)
	except (TypeError, ValueError):
		n = 15
	n = max(1, min(n, 100))
	return frappe.db.sql(
		"""
		select table_name as bang,
			round((data_length + index_length) / 1024 / 1024, 2) as mb
		from information_schema.tables
		where table_schema = database()
		order by (data_length + index_length) desc
		limit %s
		""",
		(n,),
		as_dict=True,
	)
