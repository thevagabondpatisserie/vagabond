# -*- coding: utf-8 -*-
"""Dọn nhật ký theo lô và giữ lịch sử chứng từ nghiệp vụ (#284).

Ngày 12/09/2026 bảng điều khiển Frappe Cloud báo thẳng *"Database or Disk
usage limits exceeded. Upgrade plan or reduce usage to avoid suspension"*:
database 1,25 GB trên trần 1 GB. Ngày 19/08/2026 con số này mới là 0,88 GB,
tức chưa đầy một tháng đã phình thêm gần 400 MB. Site bị khoá ghi nghĩa là
cả tiệm không lập được chứng từ và không xuất được hoá đơn.

VÌ SAO CÓ NHỊP DỌN RIÊNG

Frappe16.27.1 dùng LogType là runtime_checkable Protocol. Notification Log
và Deleted Document có clear_old_logs nên dùng được Log Settings dù không
kế thừa LogType trực tiếp; Version không có method này. Không có cấu hình
mặc định không đồng nghĩa không được hỗ trợ.

Nhịp riêng ở đây chia lô, giới hạn mỗi lượt và giữ lịch sử/payload chứng từ
nghiệp vụ trong KHONG_DUOC_DON; hàm clear_old_logs của hai bảng trên dọn
phẳng theo tuổi nên không cung cấp các giới hạn đó. Trước bật lịch cần xác
nhận mốc lưu và không đăng ký thêm nhịp dọn phẳng cho hai bảng được bảo vệ.

BA THỨ PHẢI NHỚ KHI ĐỌC CON SỐ SAU KHI DỌN

1. DELETE không trả chỗ trống cho hệ điều hành ngay. InnoDB giữ vùng vừa
   giải phóng trong chính tệp bảng để dùng lại, nên con số trên Frappe Cloud
   có thể CHƯA tụt sau lần dọn đầu, nhưng bảng sẽ thôi phình thêm. Bước gọn
   tệp (OPTIMIZE TABLE) mới làm tệp co lại, và bước đó có thể bị từ chối vì
   quyền.
2. Dọn hết ba bảng này cũng chưa chắc lọt xuống dưới trần. Ước tính 241 MB từ bàn giao ban đầu chưa loại trừ lịch sử
   chứng từ bảo vệ, không được coi là dung lượng sẽ thu hồi. Cần đo lại
   đúng bộ lọc và có phê duyệt trước khi dọn hoặc đổi gói.
3. Xoá một phát vài trăm nghìn dòng là khoá bảng lâu. Giờ hành chính mà khoá
   bảng thì quầy không tính tiền được. Nên xoá theo lô, commit giữa các lô,
   và có trần cho mỗi lần chạy. Dọn không hết một đêm thì đêm sau dọn tiếp.
"""


# --------------------------------------------------------------- phần thuần
# Phần trên mốc "phần cần Frappe" KHÔNG chạm Frappe, để kiểm thử được mà
# không cần site.

# Ba bảng dọn được, và số ngày giữ lại.
#
# Mốc 180/30/180 đã được anh Việt duyệt trực tiếp ngày 12/09/2026;
# biên nhận trên PR286 comment 5644924025, không lấy ca kiểm làm bằng chứng.
# Version/Deleted Document của KHONG_DUOC_DON được giữ, không áp mốc này.
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


# LỊCH SỬ SỬA CỦA MÀN KHÔNG PHẢI CHỨNG TỪ, GIỮ NGẮN (anh Việt chọn 28/10/2026).
#
# Ngày 28/10/2026 cơ sở dữ liệu ở 1,62 GB trên trần 2 GB của gói Frappe
# Cloud. Lịch sử sửa trang web (mỗi lần lưu chụp lại cả trang HTML) và mùa
# vụ chiếm gần 190 MB dù không phải chứng từ. Giữ 30 ngày là đủ để truy ai
# vừa đổi gì; quá đó thì xoá theo lô như ba bảng ở trên.
VERSION_NGAN = {
	"Web Page": 30,
	"Vagabond Mua Vu": 30,
	"Vagabond Noi Dung Web": 30,
}

# GỌN LỊCH SỬ DO MÁY GHI TRÊN CHỨNG TỪ (anh Việt chọn 28/10/2026).
#
# Lịch sử sửa hoá đơn bán chiếm hơn 1 GB dữ liệu thô, 97% do máy ghi: nhịp
# đồng bộ Pancake 30 phút một lần dựng lại bảng món của hoá đơn nháp, và
# ERPNext tự dựng lại bảng thuế theo dòng mỗi lần lưu. Mỗi lần như vậy lịch sử
# chụp lại TOÀN BỘ dòng cũ (removed) và dòng mới (added), dù nội dung y hệt.
#
# Quá số ngày dưới đây, lịch sử do máy ghi chỉ bỏ hai ảnh chụp đó và ghi lại
# số dòng đã bỏ; ai đổi, lúc nào, trường nào đổi từ đâu sang đâu (changed,
# row_changed) giữ nguyên. Lịch sử do NGƯỜI sửa không đụng tới. Không xoá dòng
# lịch sử nào, nên chứng từ vẫn nằm trong KHONG_DUOC_DON.
GON_MAY_GHI = {
	"Sales Invoice": 30,
}
# Tài khoản mà các nhịp tự động chạy dưới tên. Người thật có email riêng.
NGUOI_MAY = ("Administrator",)
# Chỉ hai khoá này được bỏ. Đây là hàng rào chạy thật trong gon_du_lieu.
KHOA_BO = ("added", "removed")
# Dấu ghi vào dữ liệu đã gọn, để lần sau không chọn lại.
DAU_GON = "vgb_da_gon"
# Lịch sử ngắn hơn ngưỡng này không đáng mở ra đọc.
NGUONG_BYTE = 4000
LO_GON = 500
TRAN_GON = 30000
# Gọn bớt được chừng này byte trở lên thì thu tệp bảng lại.
NGUONG_GON_BYTE = 20 * 1024 * 1024


def gon_du_lieu(data, ngay=None):
	"""Bỏ ảnh chụp dòng con (added/removed) khỏi dữ liệu một lịch sử sửa.

	Trả về (chuỗi mới, số byte bớt được), hoặc (None, 0) khi không có gì để
	gọn hoặc dữ liệu không đọc được. Không bao giờ đụng khoá nào ngoài
	KHOA_BO; dữ liệu đã gọn thì để nguyên.
	"""
	import json

	if not data or not isinstance(data, str):
		return None, 0
	try:
		d = json.loads(data)
	except (TypeError, ValueError):
		return None, 0
	if not isinstance(d, dict) or DAU_GON in d:
		return None, 0
	dem = {}
	for k in KHOA_BO:
		v = d.get(k)
		if isinstance(v, list) and v:
			dem[k] = len(v)
	if not dem:
		return None, 0
	moi = dict(d)
	for k in dem:
		moi[k] = []
	moi[DAU_GON] = dict(dem, ngay=str(ngay or ""))
	chuoi = json.dumps(moi, ensure_ascii=False, separators=(",", ":"), default=str)
	bot = len(data.encode("utf-8")) - len(chuoi.encode("utf-8"))
	if bot <= 0:
		return None, 0
	return chuoi, bot


def kiem_an_toan(bang=None):
	"""Chặn cứng: không doctype nghiệp vụ nào được lọt vào diện dọn.

	Ném ValueError chứ không trả về False, để người gọi không thể lỡ bỏ qua
	kết quả. Gọi ở đầu MỖI lần dọn, không chỉ trong bộ kiểm.
	"""
	bang = BANG_DON if bang is None else bang
	pham = sorted(set(bang) & KHONG_DUOC_DON)
	if pham:
		raise ValueError("doctype nghiep vu khong duoc don: " + ", ".join(pham))
	# Lịch sử của chứng từ không bao giờ bị XOÁ theo mốc ngắn; chứng từ chỉ
	# được gọn lịch sử máy ghi qua GON_MAY_GHI.
	pham = sorted(set(VERSION_NGAN) & KHONG_DUOC_DON)
	if pham:
		raise ValueError("lich su chung tu khong duoc xoa: " + ", ".join(pham))
	if tuple(KHOA_BO) != ("added", "removed"):
		raise ValueError("chi duoc bo anh chup dong con")
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

import frappe


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
	n = int(frappe.db.sql("select row_count()")[0][0])
	if n < 0:
		raise ValueError('Không xác định được số dòng vừa xóa. Dừng lô để đối chiếu.')
	return n


def don_mot_bang(dt, so_ngay=None, lo=None, tran=None):
	"""Xoá dần dòng cũ của MỘT bảng. Trả về số dòng đã xoá."""
	bang = ten_bang(dt)
	moc = _moc(BANG_DON[dt] if so_ngay is None else so_ngay)
	lo = int(lo or LO)
	tran = int(tran or TRAN_MOI_BANG)
	dieu_kien = "creation < %s"
	tham = [moc]
	cot = {'Version': 'ref_doctype', 'Deleted Document': 'deleted_doctype'}.get(dt)
	if cot:
		# Giữ cả lịch sử sửa và bản khôi phục của chứng từ thuộc vùng bảo vệ.
		# Không xác định được loại chứng từ thì cũng giữ lại để đối chiếu.
		dieu_kien += " and `%s` != '' and `%s` not in %%s" % (cot, cot)
		tham.append(tuple(sorted(KHONG_DUOC_DON)))
	da_xoa = 0
	while da_xoa < tran:
		con = min(lo, tran - da_xoa)
		try:
			frappe.db.sql(
				"delete from `%s` where %s limit %%s" % (bang, dieu_kien),
				tuple(tham + [con]),
			)
			xoa = _so_dong_vua_xoa()
			frappe.db.commit()
		except Exception:
			# Chỉ lô hiện tại còn lùi được; không nhận lỗi đọc số là xóa 0.
			frappe.db.rollback()
			raise
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
		ket = frappe.db.sql("optimize table `%s`" % bang)
		# MariaDB có thể trả error/status rows mà không ném SQL exception.
		if (not ket or any(len(r) < 4 or str(r[2]).lower() in ('error', 'warning') for r in ket)
			or not any(str(r[2]).lower() == 'status' and str(r[3]).upper() == 'OK' for r in ket)):
			raise RuntimeError('OPTIMIZE không xác nhận status OK; chưa chứng minh tệp đã co.')
		frappe.db.commit()
		return True
	except Exception:
		frappe.log_error(frappe.get_traceback(), "don_dep_db: gon tep %s" % bang)
		return False


def don_version_ngan(dt, so_ngay=None, lo=None, tran=None):
	"""Xoá dần lịch sử sửa quá hạn của MỘT màn không phải chứng từ."""
	kiem_an_toan()
	if dt not in VERSION_NGAN:
		raise ValueError("doctype chua khai trong VERSION_NGAN: %r" % (dt,))
	moc = _moc(VERSION_NGAN[dt] if so_ngay is None else so_ngay)
	lo = int(lo or LO)
	tran = int(tran or TRAN_MOI_BANG)
	da_xoa = 0
	while da_xoa < tran:
		con = min(lo, tran - da_xoa)
		try:
			frappe.db.sql(
				"delete from `tabVersion` where ref_doctype = %s and creation < %s limit %s",
				(dt, moc, con),
			)
			xoa = _so_dong_vua_xoa()
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			raise
		da_xoa += xoa
		if xoa < con:
			break
	return da_xoa


def gon_lich_su_may(dt, so_ngay=None, lo=None, tran=None):
	"""Gọn lịch sử do máy ghi của MỘT loại chứng từ. Không xoá dòng nào.

	Trả về {"so_dong": số lịch sử đã gọn, "byte": số byte bớt được}.
	"""
	from frappe.utils import nowdate

	kiem_an_toan()
	if dt not in GON_MAY_GHI:
		raise ValueError("doctype chua khai trong GON_MAY_GHI: %r" % (dt,))
	moc = _moc(GON_MAY_GHI[dt] if so_ngay is None else so_ngay)
	lo = int(lo or LO_GON)
	tran = int(tran or TRAN_GON)
	hom_nay = nowdate()
	so_dong = byte = 0
	sau = ""  # Đi theo tên tăng dần: mỗi lượt chỉ đọc mỗi dòng một lần.
	da_doc = 0
	while da_doc < tran:
		ds = frappe.db.sql(
			"select name, data from `tabVersion` where ref_doctype = %s and owner in %s"
			" and creation < %s and length(data) > %s and name > %s order by name limit %s",
			(dt, tuple(NGUOI_MAY), moc, NGUONG_BYTE, sau, min(lo, tran - da_doc)),
			as_dict=True,
		)
		if not ds:
			break
		try:
			for r in ds:
				moi, bot = gon_du_lieu(r.data, hom_nay)
				if moi is None:
					continue
				frappe.db.sql(
					"update `tabVersion` set data = %s where name = %s and ref_doctype = %s and owner in %s",
					(moi, r.name, dt, tuple(NGUOI_MAY)),
				)
				so_dong += 1
				byte += bot
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			raise
		da_doc += len(ds)
		sau = ds[-1].name
	return {"so_dong": so_dong, "byte": byte}


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
			ket[dt] = None  # Không biết kết quả đầy đủ, khác với thành công xóa 0.
			frappe.log_error(frappe.get_traceback(), "don_dep_db: don %s" % dt)
	xoa_ngan = byte = 0
	for dt in VERSION_NGAN:
		khoa = "Lịch sử %s" % dt
		try:
			ket[khoa] = don_version_ngan(dt)
			xoa_ngan += ket[khoa]
		except Exception:
			ket[khoa] = None
			frappe.log_error(frappe.get_traceback(), "don_dep_db: lich su %s" % dt)
	for dt in GON_MAY_GHI:
		khoa = "Gọn lịch sử máy ghi %s" % dt
		try:
			r = gon_lich_su_may(dt)
			ket[khoa] = r["so_dong"]
			byte += r["byte"]
		except Exception:
			ket[khoa] = None
			frappe.log_error(frappe.get_traceback(), "don_dep_db: gon %s" % dt)
	# Xoá và gọn chỉ trả chỗ trống lại cho chính tệp bảng; phải dựng lại
	# bảng thì con số trên Frappe Cloud mới tụt.
	if can_gon(xoa_ngan) or byte >= NGUONG_GON_BYTE:
		gon_tep("tabVersion")
	return ket


def _chan_neu_khong_phai_quan_tri():
	if "System Manager" not in (frappe.get_roles() or []):
		frappe.throw("Chỉ System Manager mới chạy và xem được phần dọn cơ sở dữ liệu.")


@frappe.whitelist(methods=['POST'])
def don_dep_ngay_bay_gio():
	"""Nút bấm tay, dùng khi Frappe Cloud đang cảnh báo mà chưa tới 03:20."""
	_chan_neu_khong_phai_quan_tri()
	ket = don_dep_hang_ngay()
	loi = [dt for dt, so in ket.items() if so is None]
	if loi:
		frappe.msgprint('Chưa dọn xong: %s. Một số lô có thể đã xóa; mở Error Log mục don_dep_db để đối chiếu.' % ', '.join(loi))
	return ket


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
