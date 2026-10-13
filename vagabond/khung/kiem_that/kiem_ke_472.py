"""#472: đếm mù về 0 phải ghi sổ thật, không lọc bằng ảnh chụp bị che."""
import frappe
from frappe.utils import nowdate, nowtime
from vagabond import kiem_ke
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, la, dung
from vagabond.khung.kiem_that.gia_von_kiem_ke_547 import _kho
from vagabond.khung.kiem_that.thu_kho_dich_512 import _mon
from vagabond.khung.kiem_that.tat_lo_545 import _phieu, _ton, _sle


def _dung(duoi, so_dem):
	cty = cong_ty()
	kho = _kho(cty)
	ma = _mon('NVLT-KT472' + duoi)
	_phieu(cty, kho, ma, 11, 'Material Receipt', 400)
	doc = frappe.get_doc({'doctype': 'Phieu Kiem Ke', 'kho': kho,
		'ngay_kiem': nowdate(), 'pham_vi': 'Tất cả', 'trang_thai': 'Đang kiểm',
		'items': [{'item_code': ma, 'item_name': ma, 'dvt': 'Gram',
			'so_luong': so_dem, 'da_dem': 1, 'ton_he_thong': 0,
			'vgb_ly_do_lech': 'lech_don_vi'}]})
	doc.insert()
	nen._DA_TAO.append(('Phieu Kiem Ke', doc.name))
	la('máy chủ chụp tồn Bin, không tin 0 từ màn', doc.items[0].ton_he_thong, 11)
	# Payload round-trip của đếm mù ở phiên bản cũ biến None thành 0.
	doc.items[0].ton_he_thong = 0
	doc.save()
	doc.reload()
	la('lưu số đếm không xoá tồn sổ', doc.items[0].ton_he_thong, 11)
	doc.trang_thai = 'Chờ duyệt'
	doc.save()
	vao = {'purpose': 'Stock Reconciliation', 'posting_time': nowtime(),
		'expense_account': frappe.db.get_value('Company', cty, 'stock_adjustment_account'),
		'cost_center': frappe.db.get_value('Company', cty, 'cost_center'),
		'items': [{'item_code': ma, 'qty': 999, 'valuation_rate': 400}]}
	return doc, ma, kho, vao


@ca('#472: đếm 0, duyệt, ghi sổ, đọc lại SLE/GL và retry không trùng')
def _ve_khong():
	doc, ma, kho, vao = _dung('A', 0)
	# Giống phiếu cũ đã hỏng ảnh chụp: DB cũng bằng 0, tồn thật vẫn 11.
	frappe.db.set_value('Chi Tiet Kiem Ke', doc.items[0].name, 'ton_he_thong', 0)
	kq = kiem_ke.ghi_so(doc.name, vao)
	nen._DA_TAO.append(('Stock Reconciliation', kq['name']))
	doc.reload()
	la('đã đóng phiếu', doc.trang_thai, 'Đã ghi sổ')
	la('tồn về 0', _ton(ma, kho), 0)
	sr = frappe.get_doc('Stock Reconciliation', kq['name'])
	la('không tin qty giả từ trình duyệt', sr.items[0].qty, 0)
	la('core đọc tồn thật', sr.items[0].current_qty, 11)
	# Core de591661 get_sle_for_items: actual_qty=0, qty_after_transaction=row.qty.
	# Kiểm kê đặt số tồn, không phải phiếu xuất có actual_qty=-11.
	sle = _sle(sr.name, ma)
	dung('có sổ kho đặt tồn và giá trị về 0', bool(sle) and all(
		r.qty_after_transaction == 0 and r.stock_value == 0 for r in sle))
	gl = frappe.get_all('GL Entry', filters={'voucher_no': sr.name, 'is_cancelled': 0}, fields=['debit', 'credit'])
	dung('có sổ cái điều chỉnh', bool(gl))
	la('sổ cái cân', round(sum(r.debit-r.credit for r in gl), 4), 0)
	la('sổ cái ghi đủ giá trị 11 x 400', round(sum(r.debit for r in gl), 4), 4400)
	la('retry trả đúng phiếu cũ', kiem_ke.ghi_so(doc.name, vao)['name'], sr.name)
	sr.cancel()
	la('huỷ core khôi phục tồn', _ton(ma, kho), 11)


@ca('#472: mọi dòng không đổi đóng phiếu rõ ràng, không sinh PKK nháp')
def _khong_doi():
	doc, ma, kho, vao = _dung('B', 11)
	kq = kiem_ke.ghi_so(doc.name, vao)
	dung('trả kết quả không đổi', kq['khong_doi'])
	doc.reload()
	la('đã kiểm xong', doc.trang_thai, 'Đã ghi sổ')
	la('giữ nguyên tồn', _ton(ma, kho), 11)
	dung('không sót dòng điều chỉnh nháp', not frappe.db.exists('Stock Reconciliation Item', {'item_code': ma}))
	dung('retry no-op không sinh phiếu', kiem_ke.ghi_so(doc.name, vao)['khong_doi'])


@ca('#472: lỗi đóng phiếu sau submit phải lùi cả SR/SLE/GL, retry được')
def _loi_dong_phieu():
	doc, ma, kho, vao = _dung('C', 0)
	cu = kiem_ke.soat_truoc_khi_chot
	def hong(d, method=None):
		if d.trang_thai == 'Đã ghi sổ':
			raise RuntimeError('472 giả lỗi đóng phiếu')
		return cu(d, method)
	kiem_ke.soat_truoc_khi_chot = hong
	try:
		try:
			kiem_ke.ghi_so(doc.name, vao)
		except RuntimeError as e:
			dung('lỗi đúng điểm đã chèn', '472 giả lỗi' in str(e))
		else:
			dung('phải ném lỗi', False)
	finally:
		kiem_ke.soat_truoc_khi_chot = cu
	doc.reload()
	la('vẫn chờ duyệt', doc.trang_thai, 'Chờ duyệt')
	la('không giảm tồn dở', _ton(ma, kho), 11)
	dung('không sót SR', not frappe.db.exists('Stock Reconciliation Item', {'item_code': ma}))
	kq = kiem_ke.ghi_so(doc.name, vao)
	nen._DA_TAO.append(('Stock Reconciliation', kq['name']))
	la('retry ghi sổ đúng', _ton(ma, kho), 0)
