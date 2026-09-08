"""Khung KIỂM THỬ TÍCH HỢP: chạy trên site thật, có Frappe và ERPNext thật.

Vì sao phải có tệp này
----------------------
Ngày 21/08/2026, Kiên không nhập kho được. Nguyên nhân: bản v256 đính mã
nhà cung cấp vào dòng sổ cái của tài khoản 3311, mà ERPNext chỉ cho đính
đối tác lên tài khoản loại Receivable, Payable hoặc Equity. Mỗi lần bấm
Xác nhận nhập kho là ERPNext ném lỗi và cả tiệm đứng.

Lỗi đó lọt qua cổng tám công đoạn vì bộ kiểm thử tầng khung chỉ chạy PHÉP
THUẦN của mình. Hàm `gan_doi_tac` chạy đúng răm rắp: nó nhận danh sách
dòng, nó điền đối tác, ca kiểm xanh. Cái nó không hỏi là câu quan trọng
nhất: **hệ lõi có CHẤP THUẬN cái mình vừa điền không.**

Bộ kiểm tầng khung không bao giờ trả lời được câu đó, vì nó chạy tay
không, không có Frappe, không có site. Nên phải có tầng thứ hai: dựng
chứng từ thật, gọi `submit()` thật, để ERPNext chạy hết chuỗi validation
của nó. Hệ ném lỗi là ca kiểm ĐỎ.

Chạy ở đâu
----------
TRÊN SITE THẬT, qua cửa `vagabond.khung.kiem_that.cua.chay`. Không bao giờ
chạy ở máy chạy CI của GitHub: ở đó không có Frappe, các mô đun này không
nạp nổi. Cổng `kiem_truoc_deploy.sh` chỉ nhắc, không chạy.

Ba lớp bảo vệ dữ liệu thật
--------------------------
1. **Điểm lưu (savepoint).** Mở điểm lưu trước mỗi ca, `rollback` về đúng
   điểm đó sau mỗi ca. Chứng từ ảo có thật trong cơ sở dữ liệu suốt lúc
   chạy, đủ để ERPNext chạy đầy đủ validation, rồi biến mất hoàn toàn.

2. **Khoá tay lái giao dịch.** `frappe.db._disable_transaction_control` là
   bộ đếm của chính Frappe (xem `frappe/database/database.py`, và cách
   Frappe dùng nó ở `frappe/model/document.py` quanh doc_events). Khi nó
   lớn hơn 0 thì mọi lời gọi `frappe.db.commit()` lạc trong hook hay trong
   ERPNext đều bị bỏ qua. Không có nó thì một `commit()` duy nhất ở giữa
   đường sẽ ghi thẳng chứng từ ảo vào sổ thật, và điểm lưu thành vô nghĩa.

3. **Cấm gửi ra ngoài.** Cờ `frappe.flags.vagabond_kiem_that` bật suốt lúc
   chạy. `thong_bao.gui` và đường gửi thư đọc cờ đó rồi im lặng. Điểm lưu
   chỉ hoàn nguyên được cơ sở dữ liệu, KHÔNG hoàn nguyên được một cái
   chuông đã bắn vào điện thoại Uyên hay một lá thư đã bay tới nhà cung
   cấp.

Sau khi chạy hết, `chay_het` tự dựng một hàng rào: mọi chứng từ đã tạo
phải KHÔNG còn tồn tại, và số lượng chứng từ mỗi loại phải bằng đúng lúc
trước khi chạy. Lệch một cái là báo đỏ ngay trong kết quả trả về, để người
gọi biết mà đi dọn chứ không phải phát hiện sau ba tuần.

Điều tuyệt đối không được làm ở tầng này
----------------------------------------
Không ca kiểm nào được chạm tới hoá đơn điện tử đã gửi cơ quan thuế, không
ca nào được sửa dữ liệu quá khứ, không ca nào được gọi `frappe.db.commit`.
Anh Việt chốt 13/08/2026: dữ liệu quá khứ là vùng cấm.
"""

import traceback
import re
from contextlib import contextmanager
from unittest.mock import patch

import frappe

# Tên điểm lưu. Một tên cố định là đủ, vì các ca chạy nối tiếp chứ không
# lồng nhau.
DIEM_LUU = "vagabond_kiem_that"

CA = []          # danh sách (tên, hàm)
_LOI = []        # các câu báo hỏng của ca đang chạy
_DA_TAO = []     # (doctype, tên) mọi chứng từ ca kiểm đã tạo ra


def ca(ten):
	"""Ghi danh một ca kiểm thử tích hợp."""
	def boc(ham):
		CA.append((ten, ham))
		return ham
	return boc


# ---------------------------------------------------------------- so sánh


def la(nhan, duoc, mong):
	if isinstance(duoc, float) or isinstance(mong, float):
		ok = abs(float(duoc) - float(mong)) < 0.000001
	else:
		ok = duoc == mong
	if not ok:
		_LOI.append("%s: được %r ¦ mong %r" % (nhan, duoc, mong))


def dung(nhan, dieu):
	la(nhan, bool(dieu), True)


def cau_loi(e):
	"""Câu lỗi của Frappe, bỏ thẻ HTML để đọc được trong kết quả trả về."""
	try:
		from frappe.utils import strip_html_tags

		return strip_html_tags(str(e)).strip()
	except Exception:
		return str(e)


def khong_nem(nhan, ham):
	"""Gọi hàm này KHÔNG được ném lỗi. Ném là ca kiểm ĐỎ.

	Đây là phép quan trọng nhất của cả tầng kiểm thử này. Vụ 3311 sẽ bị bắt
	đúng ở đây: `submit()` ném "Loại đối tác và Đối tác chỉ có thể được đặt
	cho tài khoản Phải thu / Phải trả", và câu đó vào thẳng kết quả.
	"""
	try:
		return ham()
	except Exception as e:
		_LOI.append("%s: hệ ném lỗi: %s" % (nhan, cau_loi(e)))
		return None


# ------------------------------------------------------------ dựng dữ liệu


def cong_ty():
	return (frappe.defaults.get_user_default("Company")
		or frappe.db.get_value("Company", {"name": ["!=", ""]}, "name"))


def _mot(doctype, dieu_kien, sap_xep="creation desc"):
	return frappe.db.get_value(doctype, dieu_kien, "name", order_by=sap_xep)


def mot_nha_cung_cap():
	return _mot("Supplier", {"disabled": 0})


def mot_mon_theo_ton(cty):
	"""Một mã hàng theo tồn kho, MUA ĐƯỢC, không lô, không serial, không tài sản.

	`is_purchase_item` là bắt buộc, không phải cho gọn: lần chạy đầu tiên
	ngày 21/08/2026 khung này chọn nhầm BAWC00146 là hàng chỉ để bán, và
	ERPNext chặn ngay với câu "Sản phẩm BAWC00146 chưa được đánh dấu là
	purchase". Đó là bằng chứng khung chạy đúng, nhưng ca kiểm đỏ vì đề
	bài sai chứ không phải vì hệ hỏng, và một ca kiểm đỏ nhầm thì lần sau
	không ai đọc nó nữa.

	Loại lô và serial ra để chứng từ ảo không phải khai số lô, chứ không
	phải vì đường đó không đáng kiểm. Muốn kiểm đường lô thì viết ca riêng
	có khai lô đàng hoàng.
	"""
	return _mot("Item", {
		"is_stock_item": 1, "disabled": 0, "has_batch_no": 0,
		"has_serial_no": 0, "is_fixed_asset": 0, "is_purchase_item": 1,
	})


def mot_kho(cty):
	return _mot("Warehouse", {"company": cty, "is_group": 0, "disabled": 0},
		"creation asc")


def phieu_nhap_ao(so_luong=1, don_gia=1000):
	"""Dựng và GHI SỔ một phiếu nhập kho ảo. Ném lỗi thì để nó ném ra.

	Người gọi bọc bằng `khong_nem` để câu lỗi của ERPNext thành lời báo của
	ca kiểm. Phiếu này sẽ biến mất khi ca kiểm kết thúc.
	"""
	cty = cong_ty()
	ncc, mon, kho = mot_nha_cung_cap(), mot_mon_theo_ton(cty), mot_kho(cty)
	# Nói rõ thiếu cái gì. Thiếu dữ liệu nền mà để nó nổ trong lòng ERPNext
	# thì câu lỗi trả về không ai đoán ra là do đâu.
	for nhan, gia_tri in (("nhà cung cấp", ncc), ("mã hàng mua được", mon),
			("kho lá", kho)):
		if not gia_tri:
			frappe.throw("Site này chưa có %s nào hợp lệ để dựng chứng từ thử."
				% nhan)
	doc = frappe.new_doc("Purchase Receipt")
	doc.company = cty
	doc.supplier = ncc
	doc.posting_date = frappe.utils.today()
	doc.append("items", {
		"item_code": mon,
		"qty": so_luong,
		"rate": don_gia,
		"warehouse": kho,
	})
	doc.insert()
	_DA_TAO.append((doc.doctype, doc.name))
	doc.submit()
	return doc


def so_cai_cua(doc):
	"""Các dòng sổ cái của một chứng từ vừa ghi sổ."""
	return frappe.get_all("GL Entry", filters={
		"voucher_type": doc.doctype, "voucher_no": doc.name, "is_cancelled": 0,
	}, fields=["account", "party_type", "party", "debit", "credit"])


# ------------------------------------------------------------------- chạy


def _dem(cac_doctype):
	return {dt: frappe.db.count(dt) for dt in cac_doctype}


# Frappe f33ac3f Database.rollback(save_point) chỉ dọn value_cache, không
# chạy/reset CallbackManager; ERPNext de59166 stock.get_warehouse_account_map
# giữ bản đồ ở flags suốt request. Ca sau phải thấy kho mới của chính nó.
@contextmanager
def _cach_ly():
	co_cu = frappe.flags.get("vagabond_kiem_that")
	co_co = "vagabond_kiem_that" in frappe.flags
	khoa_cu = frappe.db._disable_transaction_control
	ban_do_co = "warehouse_account_map" in frappe.flags
	ban_do_cu = frappe.flags.get("warehouse_account_map")
	chuong_co = hasattr(frappe.local, "_realtime_log")
	chuong_cu = list(getattr(frappe.local, "_realtime_log", []))
	doi_cu = [(getattr(frappe.db, k), getattr(frappe.db, k)._functions.copy())
		for k in ("before_commit", "after_commit", "before_rollback", "after_rollback")]
	cham = set()
	dau_tao = len(_DA_TAO)
	xoa_goc = frappe.clear_document_cache
	sql_goc = frappe.db.sql

	def xoa(dt, name=None):
		cham.add((dt, name))
		return xoa_goc(dt, name)

	def chan_ddl(*a, **kw):
		# sql_ddl của Frappe tự bỏ khoá rồi commit trước DDL. Báo đỏ TRƯỚC
		# khi nó được chạy, không cố dựng lại savepoint sau một commit thật.
		raise RuntimeError("Ca kiểm gọi DDL làm mất điểm lưu; dựng schema trong nen_bench trước khi chạy ca.")

	def sql(query, *a, **kw):
		cau = query.decode() if isinstance(query, bytes) else str(query)
		cau = re.sub(r"/\*.*?\*/|--[^\n]*", " ", cau, flags=re.S).strip().lower()
		if (re.match(r"^(commit|begin|start\s+transaction|truncate|alter|drop|create|rename)\b", cau)
				or (re.match(r"^rollback\b", cau) and not re.match(r"^rollback\s+to\s+(savepoint\s+)?\w+\s*;?$", cau))):
			raise RuntimeError("Ca kiểm gọi SQL phá điểm lưu: " + cau[:120])
		return sql_goc(query, *a, **kw)

	frappe.flags.pop("warehouse_account_map", None)
	frappe.local.request_cache.clear()
	frappe.db.value_cache.clear()
	frappe.db._disable_transaction_control = khoa_cu + 1
	frappe.flags.vagabond_kiem_that = True
	try:
		with patch.object(frappe, "clear_document_cache", xoa), patch.object(frappe.db, "sql_ddl", chan_ddl), patch.object(frappe.db, "sql", sql):
			yield
	finally:
		try:
			# Dọn cache của cả dữ liệu nền đã sửa lẫn tài liệu thử vừa tạo.
			# Không xoá chứng từ. Dữ liệu chỉ được lùi bằng savepoint.
			for dt, name in cham | set(_DA_TAO[dau_tao:]):
				xoa_goc(dt, name)
		finally:
			for bo, cu in doi_cu:
				bo._functions = cu
			frappe.flags.pop("warehouse_account_map", None)
			if ban_do_co:
				frappe.flags.warehouse_account_map = ban_do_cu
			if chuong_co:
				frappe.local._realtime_log = chuong_cu
			elif hasattr(frappe.local, "_realtime_log"):
				del frappe.local._realtime_log
			frappe.local.request_cache.clear()
			frappe.db.value_cache.clear()
			frappe.db._disable_transaction_control = khoa_cu
			frappe.flags.vagabond_kiem_that = False
			if co_co:
				frappe.flags.vagabond_kiem_that = co_cu
			else:
				frappe.flags.pop("vagabond_kiem_that", None)


DEM_CANH = ("Purchase Receipt", "Purchase Invoice", "Stock Ledger Entry",
	"GL Entry", "Sales Invoice", "Stock Entry", "Work Order", "BOM",
	"Warehouse", "Account", "Batch", "Serial and Batch Bundle")


def chay_het(im=1):
	"""Chạy mọi ca trong điểm lưu riêng; mất điểm lưu thì dừng cả lượt."""
	global _LOI, _DA_TAO
	_DA_TAO = []
	truoc = _dem(DEM_CANH)
	ket = []
	dat = hong = da_chay = 0
	mat_diem_luu = False

	for ten, ham in CA:
		_LOI = []
		da_chay += 1
		try:
			with _cach_ly():
				frappe.db.savepoint(DIEM_LUU)
				try:
					ham()
				except Exception:
					_LOI.append("nổ giữa chừng:\n" + traceback.format_exc())
				finally:
					try:
						frappe.db.rollback(save_point=DIEM_LUU)
					except Exception:
						mat_diem_luu = True
						_LOI.append("KHÔNG lùi được về điểm lưu, DỪNG lượt kiểm: " + traceback.format_exc())
		except Exception:
			mat_diem_luu = True
			_LOI.append("Lỗi bảo vệ khung kiểm, DỪNG lượt kiểm: " + traceback.format_exc())
		if _LOI:
			hong += 1
			ket.append({"ca": ten, "dat": 0, "loi": list(_LOI)})
		else:
			dat += 1
			if not im:
				ket.append({"ca": ten, "dat": 1, "loi": []})
		if mat_diem_luu:
			break

	sau = _dem(DEM_CANH)
	rac = [{"doctype": dt, "ten": ten} for dt, ten in _DA_TAO
		if frappe.db.exists(dt, ten)]
	lech = {dt: [truoc[dt], sau[dt]] for dt in DEM_CANH if truoc[dt] != sau[dt]}
	return {
		"so_ca": len(CA), "da_chay": da_chay, "chua_chay": len(CA) - da_chay,
		"dat": dat, "hong": hong, "ket_qua": ket,
		"mat_diem_luu": mat_diem_luu,
		"chung_tu_con_sot": rac, "so_luong_lech": lech,
		"sach": 1 if (not mat_diem_luu and not rac and not lech) else 0,
	}
