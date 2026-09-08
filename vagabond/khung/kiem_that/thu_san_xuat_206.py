"""#206: Work Order/Stock Entry thật, kho thật, SLE/GL thật.

Chỉ tạo mã thử ngẫu nhiên, chạy trong savepoint của nen.py, không commit.
Chưa thể chứng minh lô thay thế bằng ca không theo lô: nghiệm thu ISC/Bacardi
vẫn là gate riêng trong tai_lieu/issue-206-san-xuat.md.
"""
import uuid
import frappe
from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry, get_consumed_qty
from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry as nhap_kho
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, la, so_cai_cua
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu, _bom_thu
from vagabond.san_xuat_desktop import TRUONG_KHO


def _nen(theo_lo=0):
	cty = cong_ty()
	kho = frappe.get_all('Warehouse', filters={'company': cty, 'is_group': 0, 'disabled': 0}, pluck='name', limit_page_length=2)
	if len(kho) != 2:
		raise AssertionError('Cần hai kho lá đang hoạt động để kiểm khác kho.')
	tag = uuid.uuid4().hex[:10]
	nvl = _mon_thu('KT206-NVL-' + tag, theo_lo=theo_lo)
	tp = _mon_thu('KT206-TP-' + tag)
	it = frappe.get_doc('Item', tp)
	it.set(TRUONG_KHO, kho[0]); it.save()
	bom = _bom_thu(tp, nvl, cty)
	return cty, kho, nvl, tp, bom


def _lenh(cty, kho, tp, bom, nguon=None):
	wo = frappe.get_doc({'doctype': 'Work Order', 'company': cty, 'production_item': tp,
		'bom_no': bom.name, 'qty': 2, 'source_warehouse': nguon,
		'fg_warehouse': kho[1], 'wip_warehouse': kho[0], 'skip_transfer': 1,
		'use_multi_level_bom': 1})
	wo.insert()
	nen._DA_TAO.append(('Work Order', wo.name))
	wo.reload()
	return wo


@ca('206 thật: mặc định món, kho chọn tay, kho dòng, lệnh cũ không bị thay')
def _kho():
	cty, kho, nvl, tp, bom = _nen()
	wo = _lenh(cty, kho, tp, bom)
	la('kho từ món', wo.source_warehouse, kho[0])
	la('kho dòng đã lưu', wo.required_items[0].source_warehouse, kho[0])
	tay = _lenh(cty, kho, tp, bom, kho[1])
	la('kho chọn tay thắng', tay.source_warehouse, kho[1])
	tay.required_items[0].source_warehouse = kho[0]
	tay.save(); tay.reload()
	la('giữ kho dòng có chủ ý', tay.required_items[0].source_warehouse, kho[0])
	it = frappe.get_doc('Item', tp)
	it.set(TRUONG_KHO, kho[1]); it.save()
	wo.save(); wo.reload()
	la('không hồi tố mặc định', wo.source_warehouse, kho[0])


@ca('206 thật: hoàn tất từng phần trừ đúng kho SLE, consumed_qty và GL cân')
def _ghi_so():
	cty, kho, nvl, tp, bom = _nen()
	for k in kho:
		phieu = nhap_kho(item_code=nvl, qty=10, company=cty, to_warehouse=k, rate=1000, do_not_save=True)
		phieu.insert(); nen._DA_TAO.append(('Stock Entry', phieu.name)); phieu.submit()
	wo = _lenh(cty, kho, tp, bom, kho[1])
	wo.submit()
	for lan in range(2):
		doc = frappe.get_doc(make_stock_entry(wo.name, 'Manufacture', qty=1))
		doc.insert(); nen._DA_TAO.append(('Stock Entry', doc.name)); doc.submit()
		sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_type':'Stock Entry', 'voucher_no':doc.name, 'is_cancelled':0}, fields=['item_code','warehouse','actual_qty','stock_value_difference'])
		nl = [d for d in sle if d.item_code == nvl]
		la('một dòng nguyên liệu', len(nl), 1)
		la('trừ đúng kho chọn', nl[0].warehouse, kho[1])
		la('số trừ mỗi lần', float(nl[0].actual_qty), -1)
		la('consumed cộng dồn', get_consumed_qty(wo.name,nvl), lan+1)
		gl = so_cai_cua(doc)
		# Cùng tài khoản tồn và không thêm chi phí có thể không phát sinh GL.
		# Chỉ chấp nhận rỗng khi biến động giá trị kho ròng bằng 0.
		if not gl:
			la('không GL thì giá trị kho ròng không đổi', round(sum(float(d.stock_value_difference) for d in sle), 2), 0)
		la('GL nợ có cân', sum(float(d.debit) for d in gl), sum(float(d.credit) for d in gl))
	wo.reload()
	la('hoàn tất đủ hai phần', float(wo.produced_qty), 2)
	la('đóng lệnh', wo.status, 'Completed')


# #206: nhận khi còn hạn rồi chỉ lùi ngày của lô THỬ vừa tạo trong savepoint.
# Không sửa bất kỳ Batch/Work Order lịch sử nào của bếp.
def _nen_qua_han():
	from frappe.utils import nowdate, add_days
	from vagabond.khung.kiem_that.thu_nhan_nvl import _lo, _nhap, _bat_serial_batch_neu_chua
	_bat_serial_batch_neu_chua()
	frappe.db.set_single_value('Vagabond Settings', 'chan_lo_het_han', 0)
	cty, kho, nvl, tp, bom = _nen(theo_lo=1)
	lo = _lo(nvl, 'KT206-' + uuid.uuid4().hex[:10], add_days(nowdate(), 30))
	_nhap(nvl, kho[0], [(lo, 10)], cty)
	frappe.db.set_value('Batch', lo, 'expiry_date', add_days(nowdate(), -5))
	frappe.clear_document_cache('Batch', lo)
	wo = _lenh(cty, kho, tp, bom, kho[0]); wo.submit()
	return cty, kho, nvl, lo, wo


def _phieu_qua_han(wo, nvl, lo, cach, cty, kho):
	from vagabond.khung.kiem_that.thu_nhan_nvl import _goi_xuat
	doc = frappe.get_doc(make_stock_entry(wo.name, 'Manufacture', qty=1))
	doc.remarks = 'Ghi chú của bếp'
	for d in doc.items:
		if d.item_code != nvl: continue
		if cach == 'tay':
			d.batch_no = lo; d.use_serial_batch_fields = 1
		elif cach == 'goi':
			d.batch_no = None; d.use_serial_batch_fields = 0
			d.serial_and_batch_bundle = _goi_xuat(nvl, kho[0], {lo: 1}, cty).name
	return doc


def _dat_qua_han(cach):
	from vagabond import lo_het_han
	cty, kho, nvl, lo, wo = _nen_qua_han()
	doc = _phieu_qua_han(wo, nvl, lo, cach, cty, kho)
	doc.insert(); nen._DA_TAO.append(('Stock Entry', doc.name))
	doc.save(); doc.submit(); doc.reload()
	la('ghi sổ', doc.docstatus, 1)
	la('một câu dấu vết qua insert/save/submit', doc.remarks.count(lo_het_han.DAU_CAU), 1)
	dung('giữ ghi tay và lô, ngày hạn', all(x in doc.remarks for x in [
		'Ghi chú của bếp', 'Dòng ', nvl, lo, str(frappe.db.get_value('Batch', lo, 'expiry_date'))]))
	sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_no':doc.name, 'is_cancelled':0},
		fields=['item_code','warehouse','actual_qty','serial_and_batch_bundle','batch_no','stock_value_difference'])
	nl = [d for d in sle if d.item_code == nvl]
	la('trừ đúng một đơn vị', sum(float(d.actual_qty) for d in nl), -1)
	la('đúng kho', {d.warehouse for d in nl}, {kho[0]})
	for d in nl:
		if d.serial_and_batch_bundle:
			lo_ghi = frappe.get_all('Serial and Batch Entry', filters={'parent': d.serial_and_batch_bundle}, pluck='batch_no')
			la('gói ghi đúng lô', set(lo_ghi), {lo})
		else: la('sổ ghi đúng lô', d.batch_no, lo)
	la('consumed_qty', get_consumed_qty(wo.name, nvl), 1)
	gl = so_cai_cua(doc)
	la('GL cân', sum(float(d.debit) for d in gl), sum(float(d.credit) for d in gl))
	if not gl:
		la('không GL thì giá trị kho cân', round(sum(float(d.stock_value_difference) for d in sle), 2), 0)
	wo.reload(); la('lệnh ghi đúng sản lượng', float(wo.produced_qty), 1)


@ca('206 thật: Manufacture tự chọn lô hết hạn khi chốt tắt, SLE/GL/consumed đúng')
def _het_han_tu_chon():
	_dat_qua_han('tu_chon')


@ca('206 thật: Manufacture lô tay hết hạn, ghi vết không lặp qua save/submit')
def _het_han_chon_tay():
	_dat_qua_han('tay')


@ca('206 thật: Manufacture gói lô hết hạn, đúng lô trên SLE và có vết')
def _het_han_goi():
	_dat_qua_han('goi')


@ca('206 thật: bật chốt chặn cả lô tay/gói; lô tắt vẫn chặn; không chứng từ rác')
def _het_han_chan():
	cty, kho, nvl, lo, wo = _nen_qua_han()
	for cach, chan, tat in [('tay', 1, 0), ('goi', 1, 0), ('tay', 0, 1), ('goi', 0, 1)]:
		frappe.db.set_single_value('Vagabond Settings', 'chan_lo_het_han', chan)
		# Tạo gói lúc lô còn hoạt động, rồi tắt lô trước khi ghi phiếu.
		frappe.db.set_value('Batch', lo, 'disabled', 0)
		frappe.clear_document_cache('Batch', lo)
		doc = _phieu_qua_han(wo, nvl, lo, cach, cty, kho)
		frappe.db.set_value('Batch', lo, 'disabled', tat)
		frappe.clear_document_cache('Batch', lo)
		bang = ['Stock Entry', 'Stock Ledger Entry', 'GL Entry', 'Serial and Batch Bundle']
		truoc = {dt: frappe.db.count(dt) for dt in bang}
		frappe.db.savepoint('kt206_chan')
		try:
			doc.insert(); nen._DA_TAO.append(('Stock Entry', doc.name)); doc.submit()
			raise AssertionError('Không được ghi phiếu với chốt bật hoặc lô tắt')
		except frappe.ValidationError as e:
			dung('lỗi nêu đúng lô', lo in str(e))
		finally:
			frappe.db.rollback(save_point='kt206_chan')
		la('không phiếu/sổ/gói phát sinh sau rollback', {dt: frappe.db.count(dt) for dt in bang}, truoc)
		wo.reload(); la('không tăng sản lượng', float(wo.produced_qty), 0)
