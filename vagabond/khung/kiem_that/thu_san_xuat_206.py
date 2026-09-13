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


@ca('206 Desk thật: migrate lặp, tên cạnh mã, mặc định mới và giữ bỏ tick chủ động')
def _mac_dinh_desk():
	from vagabond.patches.mac_dinh_san_xuat_206 import execute
	try:
		execute(); execute()
		meta = frappe.get_meta('Work Order', cached=False)
		thu_tu = [d.fieldname for d in meta.fields]
		la('tên cạnh mã', thu_tu[thu_tu.index('production_item')+1], 'item_name')
		la('mặc định lệnh mới', frappe.new_doc('Work Order').skip_transfer, 1)
		cty, kho, nvl, tp, bom = _nen()
		wo = _lenh(cty, kho, tp, bom, kho[0])
		wo.skip_transfer = 0; wo.save(); wo.reload()
		la('giữ bỏ tick chủ động', wo.skip_transfer, 0)
		la('tên lấy đúng món', wo.item_name, frappe.db.get_value('Item', tp, 'item_name'))
	finally:
		# nen.py sẽ rollback Property Setter; không để metadata thử trong cache.
		for dt in ['Work Order', 'Stock Entry']: frappe.clear_cache(doctype=dt)


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
	from vagabond.khung.kiem_that.thu_nhan_nvl import _lo, _bat_serial_batch_neu_chua
	_bat_serial_batch_neu_chua()
	cty, kho, nvl, tp, bom = _nen(theo_lo=1)
	lo = _lo(nvl, 'KT206-' + uuid.uuid4().hex[:10], add_days(nowdate(), 30))
	# Ca sản xuất cần NVL có giá vốn thật. Helper nhận lô _nhap bật
	# allow_zero_valuation_rate, khiến core v16 ép basic_rate về 0 và
	# thành phẩm mới không thể tính giá vốn khi lưu Manufacture lần hai.
	nhap = nhap_kho(item_code=nvl, qty=10, company=cty,
		to_warehouse=kho[0], rate=1000, do_not_save=True)
	nhap.items[0].batch_no = lo
	nhap.items[0].use_serial_batch_fields = 1
	nhap.items[0].allow_zero_valuation_rate = 0
	nhap.insert(); nen._DA_TAO.append(('Stock Entry', nhap.name)); nhap.submit()
	gia_nhap = frappe.get_all('Stock Ledger Entry', filters={
		'voucher_type': 'Stock Entry', 'voucher_no': nhap.name, 'is_cancelled': 0},
		fields=['stock_value_difference'])
	la('nền nhập NVL có giá vốn thật', sum(float(d.stock_value_difference) for d in gia_nhap), 10000)
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


@ca('489 thật: lô tắt/quá hạn vẫn ghi sổ và cảnh báo, huỷ trả tồn')
def _het_han_chan():
	cty, kho, nvl, lo, wo = _nen_qua_han()
	for cach in ['tay', 'goi']:
		doc = _phieu_qua_han(wo, nvl, lo, cach, cty, kho)
		frappe.db.set_value('Batch', lo, 'disabled', 1)
		frappe.clear_document_cache('Batch', lo)
		doc.insert(); nen._DA_TAO.append(('Stock Entry', doc.name)); doc.submit(); doc.reload()
		la('ghi sổ lô tắt', doc.docstatus, 1)
		dung('cảnh báo đúng lô', 'Phiếu dùng lô đã tắt:' in doc.remarks and lo in doc.remarks)
		doc.cancel(); wo.reload()
		la('huỷ trả sản lượng', float(wo.produced_qty), 0)


@ca('#258 app hoàn tất bỏ giờ máy khách, reload SLE/GL đúng giờ và giá trị')
def _gio_hoan_tat_app():
	from frappe.utils import now_datetime, get_datetime, add_days, today
	from vagabond.kho_san_xuat import hoan_tat_phieu
	cty, kho, nvl, tp, bom = _nen()
	nhap = nhap_kho(item_code=nvl, qty=10, company=cty, to_warehouse=kho[0], rate=1000, do_not_save=True)
	nhap.insert(); nen._DA_TAO.append(('Stock Entry', nhap.name)); nhap.submit(); nhap.reload()
	lenh = _lenh(cty, kho, tp, bom, kho[0]); lenh.submit()
	phieu = make_stock_entry(lenh.name, 'Manufacture', qty=2)
	# Giờ sai từ máy khách phải bị bỏ; nếu gỡ dòng set_posting_time=0,
	# core sẽ xuất trước lần nhập thử hoặc lưu ngày cũ, ca này phải đỏ.
	phieu.update(set_posting_time=1, posting_date=add_days(today(), -1), posting_time='00:00:00')
	truoc = now_datetime().replace(microsecond=0)
	kq = hoan_tat_phieu(phieu, q=2, can=2)
	nen._DA_TAO.append(('Stock Entry', kq['name']))
	doc = frappe.get_doc('Stock Entry', kq['name'])
	luc = get_datetime(str(doc.posting_date)+' '+str(doc.posting_time))
	sau = now_datetime()
	dung('giờ site %s <= %s <= %s' % (truoc,luc,sau), truoc <= luc <= sau)
	la('phiếu ghi sổ', doc.docstatus, 1)
	sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_type':'Stock Entry','voucher_no':doc.name,'is_cancelled':0},
		fields=['item_code','warehouse','actual_qty','stock_value_difference','posting_date','posting_time'])
	la('đúng hai dòng SLE', sorted((d.item_code,d.warehouse,float(d.actual_qty)) for d in sle),
		sorted([(nvl,kho[0],-2.0),(tp,kho[1],2.0)]))
	for d in sle:
		la('giờ SLE khớp phiếu', get_datetime(str(d.posting_date)+' '+str(d.posting_time)), luc)
		la('giá trị từng dòng kho', round(float(d.stock_value_difference),2), -2000 if d.item_code==nvl else 2000)
	gl = frappe.get_all('GL Entry',filters={'voucher_type':'Stock Entry','voucher_no':doc.name,'is_cancelled':0},
		fields=['debit','credit','posting_date'])
	for d in gl:
		la('ngày GL khớp thời điểm server',str(d.posting_date),str(luc.date()))
	if not gl:
		la('GL rỗng chỉ hợp lệ khi giá trị kho ròng0',round(sum(float(d.stock_value_difference) for d in sle),2),0)
	la('GL cân', sum(float(d.debit) for d in gl), sum(float(d.credit) for d in gl))
	la('giá trị kho ròng không đổi', round(sum(float(d.stock_value_difference) for d in sle),2), 0)
	lenh.reload(); la('lệnh sản xuất đủ', float(lenh.produced_qty), 2)


# Khải #206: ảnh lô âm không chứng minh giá vốn sai. Hai phép kiểm dưới đây
# tách số lượng từng lô khỏi giá bình quân. Chỉ có dữ liệu thử trong savepoint.
def _hai_lo_khai(so_cu, so_moi, gia_cu, gia_moi, can):
	from frappe.utils import add_days, nowdate
	from vagabond.khung.kiem_that.thu_nhan_nvl import _lo, _bat_serial_batch_neu_chua
	_bat_serial_batch_neu_chua()
	cty, kho, nvl, tp, _ = _nen(theo_lo=1)
	# Nos thường bắt số nguyên. Tạo đơn vị lẻ riêng cho ca, không sửa UOM thật.
	dvt = 'KT206-gram-' + uuid.uuid4().hex[:8]
	frappe.get_doc({'doctype': 'UOM', 'uom_name': dvt, 'must_be_whole_number': 0}).insert()
	nen._DA_TAO.append(('UOM', dvt))
	it = frappe.get_doc('Item', nvl)
	it.stock_uom = dvt
	it.valuation_method = 'Moving Average'
	it.set('uoms', [{'uom': dvt, 'conversion_factor': 1}])
	it.save()
	frappe.clear_document_cache('Item', nvl)
	bom = frappe.get_doc({'doctype': 'BOM', 'item': tp, 'company': cty,
		'quantity': 1, 'is_active': 1, 'is_default': 1,
		'items': [{'item_code': nvl, 'qty': can, 'uom': dvt, 'rate': gia_cu}]})
	bom.insert(); nen._DA_TAO.append(('BOM', bom.name)); bom.submit()
	lo = []
	for i, (so, gia) in enumerate([(so_cu, gia_cu), (so_moi, gia_moi)]):
		b = _lo(nvl, 'KT206-KHAI-' + uuid.uuid4().hex[:10], add_days(nowdate(), 10 + 20*i))
		lo.append(b)
		nhap = nhap_kho(item_code=nvl, qty=so, company=cty, to_warehouse=kho[0], rate=gia, do_not_save=True)
		nhap.items[0].batch_no = b
		nhap.items[0].use_serial_batch_fields = 1
		nhap.items[0].allow_zero_valuation_rate = 0
		nhap.insert(); nen._DA_TAO.append(('Stock Entry', nhap.name)); nhap.submit()
	wo = _lenh(cty, kho, tp, bom, kho[0]); wo.submit()
	return kho, nvl, tp, lo, wo


def _xuat_khai(wo, nvl, kho):
	phieu = frappe.get_doc(make_stock_entry(wo.name, 'Manufacture', qty=1))
	phieu.insert(); nen._DA_TAO.append(('Stock Entry', phieu.name))
	phieu.submit(); phieu.reload()
	sle = frappe.get_all('Stock Ledger Entry', filters={
		'voucher_type': 'Stock Entry', 'voucher_no': phieu.name, 'is_cancelled': 0},
		fields=['item_code', 'warehouse', 'actual_qty', 'stock_value_difference', 'serial_and_batch_bundle'])
	nl = [d for d in sle if d.item_code == nvl]
	dung('sổ nguyên liệu phải có thật', bool(nl))
	la('đúng kho nguyên liệu', {d.warehouse for d in nl}, {kho})
	la('giá trị kho ròng cân', round(sum(float(d.stock_value_difference) for d in sle), 2), 0)
	gl = so_cai_cua(phieu)
	la('GL cân', round(sum(float(d.debit)-float(d.credit) for d in gl), 2), 0)
	return phieu, nl


@ca('206 Khải: 704+2000 gram, hai lần 403.431, chia lô thật và huỷ phục hồi')
def _khai_chia_lo():
	from vagabond.khung.kiem_that.thu_nhan_nvl import _ton_lo
	kho, nvl, tp, lo, wo = _hai_lo_khai(704, 2000, 340, 340, 403.431)
	mot, _ = _xuat_khai(wo, nvl, kho[0])
	la('lô cũ sau lượt đầu', round(_ton_lo(lo[0], kho[0]), 3), 300.569)
	la('chưa đụng lô mới', _ton_lo(lo[1], kho[0]), 2000)
	hai, nl = _xuat_khai(wo, nvl, kho[0])
	la('tổng xuất lượt hai', round(sum(float(d.actual_qty) for d in nl), 3), -403.431)
	la('lô cũ dùng hết', round(_ton_lo(lo[0], kho[0]), 3), 0)
	la('lô mới góp 102.862', round(_ton_lo(lo[1], kho[0]), 3), 1897.138)
	la('WO cộng đúng tiêu hao', round(get_consumed_qty(wo.name, nvl), 3), 806.862)
	hai.cancel(); wo.reload()
	la('huỷ lượt hai về đúng sản lượng', float(wo.produced_qty), 1)
	la('huỷ trả lô cũ', round(_ton_lo(lo[0], kho[0]), 3), 300.569)
	la('huỷ trả lô mới', _ton_lo(lo[1], kho[0]), 2000)
	mot.cancel(); wo.reload()
	la('huỷ cả hai trả đủ lô cũ', _ton_lo(lo[0], kho[0]), 704)
	la('huỷ cả hai trả đủ lô mới', _ton_lo(lo[1], kho[0]), 2000)
	la('WO hết tiêu hao', get_consumed_qty(wo.name, nvl), 0)
	la('WO hết sản lượng', float(wo.produced_qty), 0)


def _khai_gia(binh_quan):
	# ERPNext de591661, stock/serial_batch_bundle.py:prepare_batches:
	# Moving Average + do_not_use_batchwise_valuation -> non_batchwise.
	# Nhập lúc cờ TẮT để cả hai Batch thực sự có use_batchwise_valuation=1.
	# Bật sau nhập rồi xuất mới chứng minh nhánh xử lý cả lô đang tồn.
	from vagabond.khung.kiem_that.thu_nhan_nvl import _ton_lo
	frappe.db.set_single_value('Stock Settings', 'do_not_use_batchwise_valuation', 0)
	kho, nvl, tp, lo, wo = _hai_lo_khai(10, 10, 1000, 3000, 4)
	for b in lo:
		la('nền lô có định giá riêng', frappe.db.get_value('Batch', b, 'use_batchwise_valuation'), 1)
	frappe.db.set_single_value('Stock Settings', 'do_not_use_batchwise_valuation', binh_quan)
	phieu, nl = _xuat_khai(wo, nvl, kho[0])
	la('số lượng xuất thật', sum(float(d.actual_qty) for d in nl), -4)
	dung('mọi dòng xuất giữ gói lô', all(d.serial_and_batch_bundle for d in nl))
	for b in lo:
		la('không sửa cờ của lô cũ', frappe.db.get_value('Batch', b, 'use_batchwise_valuation'), 1)
	la('giữ theo dõi Batch', frappe.db.get_value('Item', nvl, 'has_batch_no'), 1)
	la('vẫn rút đúng lô cũ', _ton_lo(lo[0], kho[0]), 6)
	la('không rút lô mới', _ton_lo(lo[1], kho[0]), 10)
	la('giá vốn thực ghi sổ', round(-sum(float(d.stock_value_difference) for d in nl), 2),
		8000 if binh_quan else 4000)


@ca('206 Khải giá vốn: cờ tắt lấy giá lô 1000, đối chứng có chịu lực')
def _khai_gia_lo():
	_khai_gia(0)


@ca('206 Khải giá vốn: giữ Batch cũ, bật bình quân, xuất giá 2000 từ SLE thật')
def _khai_gia_binh_quan():
	_khai_gia(1)


@ca('206 phiếu nhập kho thật: lô quá hạn cảnh báo, ghi sổ và huỷ trả tồn')
def _nhap_lo_qua_han():
	from vagabond.khung.kiem_that.thu_nhan_nvl import _ton_lo
	cty, kho, nvl, lo, wo = _nen_qua_han()
	doc = nhap_kho(item_code=nvl, qty=2, company=cty, to_warehouse=kho[0], rate=1000, do_not_save=True)
	doc.items[0].batch_no = lo
	doc.items[0].use_serial_batch_fields = 1
	doc.insert(); nen._DA_TAO.append(('Stock Entry', doc.name)); doc.submit(); doc.reload()
	la('nhập đủ vào lô cũ', _ton_lo(lo, kho[0]), 12)
	dung('cảnh báo trên phiếu đã lưu', lo in (doc.remarks or ''))
	_kiem_phieu_kho_han(doc, nvl, kho[0], 2, 2000)
	doc.cancel()
	la('huỷ trả đúng tồn trước nhận', _ton_lo(lo, kho[0]), 10)


@ca('206 FEFO thật: nhập sau nhưng HSD gần hơn thì lấy trước')
def _khai_fefo():
	from frappe.utils import nowdate, add_days
	from vagabond.khung.kiem_that.thu_nhan_nvl import _ton_lo
	kho, nvl, tp, lo, wo = _hai_lo_khai(10, 10, 1000, 1000, 4)
	for b, ngay in [(lo[0], 180), (lo[1], 30)]:
		frappe.db.set_value('Batch', b, 'expiry_date', add_days(nowdate(), ngay))
		frappe.clear_document_cache('Batch', b)
	_xuat_khai(wo, nvl, kho[0])
	la('giữ lô nhập trước nhưng hạn xa', _ton_lo(lo[0], kho[0]), 10)
	la('lấy lô nhập sau nhưng hạn gần', _ton_lo(lo[1], kho[0]), 6)



def _kiem_phieu_kho_han(doc, ma, kho, so, gia):
	from vagabond.lo_het_han import DAU_CAU
	la('cảnh báo đúng một lần', (doc.remarks or '').count(DAU_CAU), 1)
	sle = frappe.get_all('Stock Ledger Entry', filters={'voucher_type': 'Stock Entry',
		'voucher_no': doc.name, 'is_cancelled': 0, 'item_code': ma, 'warehouse': kho},
		fields=['actual_qty', 'stock_value_difference', 'serial_and_batch_bundle'])
	dung('SLE không rỗng và giữ gói lô', bool(sle) and all(d.serial_and_batch_bundle for d in sle))
	la('số lượng SLE', sum(float(d.actual_qty) for d in sle), so)
	la('giá trị SLE', sum(float(d.stock_value_difference) for d in sle), gia)


def _xuat_chuyen_han(chuyen):
	from vagabond.khung.kiem_that.thu_nhan_nvl import _ton_lo
	cty, kho, ma, lo, wo = _nen_qua_han()
	# Công tắc BẬT mới chạm hồi quy F4, core vẫn cho xuất/chuyển lô quá hạn.
	doc = nhap_kho(item_code=ma, qty=2, company=cty, from_warehouse=kho[0],
		to_warehouse=kho[1] if chuyen else None, rate=1000, do_not_save=True)
	doc.items[0].batch_no = lo; doc.items[0].use_serial_batch_fields = 1
	doc.insert(); nen._DA_TAO.append(('Stock Entry', doc.name)); doc.submit(); doc.reload()
	_kiem_phieu_kho_han(doc, ma, kho[0], -2, -2000)
	la('trừ lô nguồn', _ton_lo(lo, kho[0]), 8)
	if chuyen:
		_kiem_phieu_kho_han(doc, ma, kho[1], 2, 2000)
		la('giữ lô đến', _ton_lo(lo, kho[1]), 2)
	doc.cancel()
	la('huỷ trả lô nguồn', _ton_lo(lo, kho[0]), 10)
	if chuyen: la('huỷ nhả lô đến', _ton_lo(lo, kho[1]), 0)


@ca('206 F4 thật: xuất lô quá hạn khi công tắc bật, SLE/huỷ đúng')
def _xuat_han_bat():
	_xuat_chuyen_han(False)


@ca('206 F4 thật: chuyển lô quá hạn khi công tắc bật, hai kho/huỷ đúng')
def _chuyen_han_bat():
	_xuat_chuyen_han(True)


def _bu_lo_that(goi):
	from frappe.utils import add_days, today
	from vagabond.khung.kiem_that.thu_nhan_nvl import _lo, _nhap, _goi_xuat, _ton_lo
	cty, kho, ma, tp, bom = _nen(theo_lo=1)
	tag = uuid.uuid4().hex[:10]
	a = _lo(ma, 'KT489-A-' + tag, add_days(today(), 30))
	b = _lo(ma, 'KT489-B-' + tag, add_days(today(), 60))
	_nhap(ma, kho[0], [(a, 100), (b, 50)], cty)
	d = nhap_kho(item_code=ma, qty=130, company=cty, from_warehouse=kho[0], do_not_save=True)
	if goi:
		d.items[0].serial_and_batch_bundle = _goi_xuat(ma, kho[0], {a: 130}, cty).name
		d.items[0].use_serial_batch_fields = 0
	else:
		d.items[0].batch_no = a; d.items[0].use_serial_batch_fields = 1
	d.insert(); nen._DA_TAO.append(('Stock Entry', d.name)); d.submit(); d.reload()
	la('lô chọn cạn', _ton_lo(a, kho[0]), 0)
	la('lô bổ sung còn 20', _ton_lo(b, kho[0]), 20)
	dung('ghi cảnh báo bù', 'Đã bù phần thiếu' in d.remarks)
	d.cancel()
	la('huỷ trả lô chọn', _ton_lo(a, kho[0]), 100)
	la('huỷ trả lô bổ sung', _ton_lo(b, kho[0]), 50)
	thieu = nhap_kho(item_code=ma, qty=200, company=cty, from_warehouse=kho[0], do_not_save=True)
	thieu.items[0].batch_no = a; thieu.items[0].use_serial_batch_fields = 1
	try:
		thieu.insert()
		raise AssertionError('Không được cho âm tồn thật')
	except frappe.ValidationError as e:
		dung('thiếu hàng thật', 'không đủ' in str(e))


@ca('489 thật: chọn tay lô100 cần130 tự bù30, thiếu200 chặn, huỷ đúng')
def _bu_lo_tay_that():
	_bu_lo_that(False)


@ca('489 thật: gói nháp lô100 cần130 tự bù30, thiếu200 chặn, huỷ đúng')
def _bu_goi_that():
	_bu_lo_that(True)


@ca('489 thật: API nhận mua thiếu HSD/cận hạn tạo đúng Batch, ghi cảnh báo, huỷ trả tồn')
def _nhan_mua_han_that():
	from frappe.utils import today, add_days
	from vagabond import nhan_hang
	from vagabond.khung.kiem_that.he_so_252 import _luu
	from vagabond.khung.kiem_that.gram_bom_252 import _kho_rieng
	cty = cong_ty(); kho, tk = _kho_rieng(cty, '489-NHAN')
	ma = _mon_thu('KT489-NHAN-' + uuid.uuid4().hex[:10], theo_lo=1)
	it = frappe.get_doc('Item', ma); it.has_expiry_date=1; it.shelf_life_in_days=90; it.save()
	for han in [None, add_days(today(), -1), add_days(today(), 3650)]:
		po = _luu(frappe.get_doc(dict(doctype='Purchase Order', company=cty,
			supplier=nen.mot_nha_cung_cap(), currency='VND', conversion_rate=1,
			transaction_date=today(), schedule_date=today(),
			items=[dict(item_code=ma, qty=1, rate=1000, warehouse=kho, schedule_date=today())])))
		po.submit(); po.reload()
		ra = nhan_hang.tao_phieu(po.name, dong=[{'dong':po.items[0].name, 'sl':1, 'hsd':han}])
		pr = frappe.get_doc('Purchase Receipt', ra['phieu']); nen._DA_TAO.append((pr.doctype,pr.name))
		la('API ghi sổ',pr.docstatus,1)
		d = pr.items[0]
		lo = d.batch_no or frappe.db.get_value('Serial and Batch Entry', {'parent':d.serial_and_batch_bundle},'batch_no')
		nen._DA_TAO.append(('Batch',lo))
		la('đúng hạn hoặc trống',str(frappe.db.get_value('Batch',lo,'expiry_date') or ''),str(han or ''))
		can_canh_bao = not han or str(han) < today()
		la('API trả cảnh báo',bool(ra['canh_bao_han']),can_canh_bao)
		if can_canh_bao:
			dung('cảnh báo lưu trên phiếu', ('Chưa có hạn sử dụng' if not han else 'Hạn dùng cần kiểm tra') in pr.remarks)
		else:
			dung('hạn tốt không ghi cảnh báo thừa', 'Chưa có hạn sử dụng' not in (pr.remarks or '') and 'Hạn dùng cần kiểm tra' not in (pr.remarks or ''))
		la('tồn đã nhận',float(frappe.db.get_value('Bin',{'item_code':ma,'warehouse':kho},'actual_qty')),1)
		pr.cancel()
		la('huỷ trả tồn',float(frappe.db.get_value('Bin',{'item_code':ma,'warehouse':kho},'actual_qty')),0)


@ca('489 PR nháp: HSD nhãn/trống tới Batch, retry không thêm sổ, huỷ trả tồn')
def _nhan_nhap_han_that():
	from frappe.utils import today, add_days
	from vagabond import nhan_hang
	from vagabond.khung.kiem_that.he_so_252 import _luu
	from vagabond.khung.kiem_that.gram_bom_252 import _kho_rieng
	from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt
	cty = cong_ty(); kho, tk = _kho_rieng(cty, '489-NHAP')
	ma = _mon_thu('KT489-NHAP-' + uuid.uuid4().hex[:10], theo_lo=1)
	it = frappe.get_doc('Item', ma); it.has_expiry_date=1; it.shelf_life_in_days=90; it.save()
	for han in ['', add_days(today(), -1), add_days(today(),3650)]:
		po = _luu(frappe.get_doc(dict(doctype='Purchase Order',company=cty,
			supplier=nen.mot_nha_cung_cap(),currency='VND',conversion_rate=1,
			transaction_date=today(),schedule_date=today(),
			items=[dict(item_code=ma,qty=1,rate=1000,warehouse=kho,schedule_date=today())])))
		po.submit()
		pr = _luu(make_purchase_receipt(po.name)); pr.reload()
		payload = pr.as_dict(); dong=[dict(dong=pr.items[0].name,sl=1,hsd=han)]
		if not han:
			from unittest.mock import patch
			so_lo = frappe.db.count('Batch',{'item':ma})
			with patch.object(type(pr),'submit',side_effect=RuntimeError('loi sau tao Batch')):
				try: nhan_hang.ghi_phieu_nhap(payload,dong)
				except RuntimeError as e: la('đúng lỗi thử',str(e),'loi sau tao Batch')
				else: raise AssertionError('Phải phát lại lỗi submit')
			la('lỗi không để lô rác',frappe.db.count('Batch',{'item':ma}),so_lo)
			la('lỗi giữ nháp',frappe.db.get_value('Purchase Receipt',pr.name,'docstatus'),0)
			nguoi=frappe.session.user
			try:
				frappe.set_user('Guest')
				try: nhan_hang.ghi_phieu_nhap(payload,dong)
				except frappe.ValidationError: pass
				else: raise AssertionError('Guest không được nhận hàng')
			finally: frappe.set_user(nguoi)
			ra = nhan_hang.ghi_phieu_nhap(payload,dong)
		else:
			ra = nhan_hang.ghi_phieu_nhap(payload,dong)
		pr.reload(); la('PR ghi sổ',pr.docstatus,1)
		r=pr.items[0]; lo=r.batch_no or frappe.db.get_value('Serial and Batch Entry',{'parent':r.serial_and_batch_bundle},'batch_no')
		nen._DA_TAO.append(('Batch',lo))
		la('HSD thực sự vào Batch',str(frappe.db.get_value('Batch',lo,'expiry_date') or ''),str(han))
		canh=not han or str(han)<today()
		la('cảnh báo trả app',bool(ra['canh_bao_han']),canh)
		if canh: dung('cảnh báo lưu phiếu', ('Chưa có hạn sử dụng' if not han else 'Hạn dùng cần kiểm tra') in (pr.remarks or ''))
		else: dung('hạn tốt không cảnh báo thừa','Chưa có hạn sử dụng' not in (pr.remarks or '') and 'Hạn dùng cần kiểm tra' not in (pr.remarks or ''))
		sle=frappe.db.count('Stock Ledger Entry',{'voucher_type':'Purchase Receipt','voucher_no':pr.name})
		lap=nhan_hang.ghi_phieu_nhap(payload,dong)
		la('retry đúng phiếu',lap['phieu'],pr.name)
		la('retry đúng cảnh báo kể cả lô quá hạn',lap['canh_bao_han'],ra['canh_bao_han'])
		la('retry không thêm SLE',frappe.db.count('Stock Ledger Entry',{'voucher_type':'Purchase Receipt','voucher_no':pr.name}),sle)
		la('tồn sau nhận',float(frappe.db.get_value('Bin',{'item_code':ma,'warehouse':kho},'actual_qty')),1)
		pr.cancel();la('huỷ trả tồn',float(frappe.db.get_value('Bin',{'item_code':ma,'warehouse':kho},'actual_qty')),0)


def _nhap_lo_chon_san(kieu):
	from frappe.utils import today, add_days, nowtime
	from vagabond import nhan_hang
	from vagabond.khung.kiem_that.he_so_252 import _luu
	from vagabond.khung.kiem_that.gram_bom_252 import _kho_rieng
	from vagabond.khung.kiem_that.thu_nhan_nvl import _lo, _nhap, _ton_lo
	cty=cong_ty(); kho,tk=_kho_rieng(cty,'489-CHON')
	ma=_mon_thu('KT489-CHON-'+uuid.uuid4().hex[:10],theo_lo=1)
	han_cu=add_days(today(),30); han_moi=add_days(today(),60)
	lo=_lo(ma,'KT489-CHONLO-'+uuid.uuid4().hex[:10],han_cu)
	truoc=10 if kieu=='co_so' else 0
	if truoc: _nhap(ma,kho,[(lo,truoc)],cty)
	so_dong=2 if kieu=='hai_dong' else 1
	pr=_luu(frappe.get_doc(dict(doctype='Purchase Receipt',company=cty,
		supplier=nen.mot_nha_cung_cap(),currency='VND',conversion_rate=1,posting_date=today(),
		items=[dict(item_code=ma,qty=10,rate=1000,warehouse=kho,batch_no=lo,use_serial_batch_fields=1) for _ in range(so_dong)])))
	if kieu=='goi':
		from erpnext.stock.serial_batch_bundle import SerialBatchCreation
		sb=SerialBatchCreation(dict(item_code=ma,warehouse=kho,company=cty,type_of_transaction='Inward',
			voucher_type='Purchase Receipt',voucher_no=pr.name,qty=1,batches={lo:1},do_not_submit=1,
			posting_date=today(),posting_time=nowtime())).make_serial_and_batch_bundle()
		nen._DA_TAO.append(('Serial and Batch Bundle',sb.name))
		pr.items[0].qty=pr.items[0].received_qty=1
		pr.items[0].batch_no=None;pr.items[0].use_serial_batch_fields=0;pr.items[0].serial_and_batch_bundle=sb.name
		pr.save()
	pr.reload(); payload=pr.as_dict()
	if kieu=='chua_so':
		payload['items'][0].update(rate=1,conversion_factor=10,uom='SAI',stock_uom='SAI')
		payload['posting_date']='2000-01-01'
	dong=[dict(dong=r.name,sl=1,hsd=han_moi) for r in pr.items]
	if kieu in ('giu','xoa'):
		dong[0].update(hsd='',giu=1 if kieu=='giu' else 0)
	if kieu=='hai_dong':
		dong[1]['hsd']=''
		try: nhan_hang.ghi_phieu_nhap(payload,dong)
		except frappe.ValidationError as e: dung('bắt đúng mâu thuẫn', 'HSD khác nhau' in str(e))
		else: raise AssertionError('Hai hạn cho một lô phải chặn trước khi ghi')
		la('không ghi đè lô',str(frappe.db.get_value('Batch',lo,'expiry_date')),han_cu)
		la('còn nháp',frappe.db.get_value('Purchase Receipt',pr.name,'docstatus'),0)
		dong[1]['hsd']=han_moi
	if kieu=='chua_so':
		dong[0]['sl']=11
		try: nhan_hang.ghi_phieu_nhap(payload,dong)
		except frappe.ValidationError as e: dung('chặn vượt số DB','không vượt phiếu nháp' in str(e))
		else: raise AssertionError('Phải chặn vượt nháp')
		dong[0]['sl']=1
	if kieu=='goi':
		dong[0]['sl']=0.5
		try: nhan_hang.ghi_phieu_nhap(payload,dong)
		except frappe.ValidationError as e: dung('gói lệch có hướng dẫn','Sửa gói trên Desk' in str(e))
		else: raise AssertionError('Lượng gói không khớp phải chặn')
		dong[0]['sl']=1
	ra=nhan_hang.ghi_phieu_nhap(payload,dong);pr.reload()
	la('ghi sổ được',pr.docstatus,1)
	if kieu=='chua_so':
		la('giá máy chủ',float(pr.items[0].rate),1000)
		la('hệ số máy chủ',float(pr.items[0].conversion_factor),1)
		la('ngày máy chủ',str(pr.posting_date),today())
		sle=frappe.get_all('Stock Ledger Entry',filters={'voucher_type':'Purchase Receipt','voucher_no':pr.name,'is_cancelled':0},fields=['actual_qty','stock_value_difference'])
		la('SLE giá DB',sum(float(x.stock_value_difference) for x in sle),1000)
		la('SLE lượng DB',sum(float(x.actual_qty) for x in sle),1)
	la('số đếm thắng qty10 của payload',[float(r.qty) for r in pr.items],[1.0]*so_dong)
	la('hạn đúng chính sách',str(frappe.db.get_value('Batch',lo,'expiry_date') or ''),han_cu if kieu in ('co_so','goi','giu') else ('' if kieu=='xoa' else han_moi))
	if kieu in ('giu','xoa'):
		dung('cảnh báo đúng giữ hoặc xóa', any(('Chưa đọc được HSD' if kieu=='giu' else 'Chưa có hạn sử dụng') in c for c in ra['canh_bao_han']))
	if kieu in ('co_so','goi'):
		dung('có cảnh báo giữ hạn',any(('đã có sổ kho' if kieu=='co_so' else 'đã chia gói lô') in c for c in ra['canh_bao_han']))
		la('retry giữ đúng cảnh báo',nhan_hang.ghi_phieu_nhap(payload,dong)['canh_bao_han'],ra['canh_bao_han'])
	la('tồn đúng số đếm',_ton_lo(lo,kho),truoc+so_dong)
	pr.cancel();la('hủy trả đúng tồn',_ton_lo(lo,kho),truoc)


@ca('489 PR nháp: lô chưa sổ đổi ngày, số đếm thắng qty payload, vượt nháp bị chặn')
def _nhap_chua_so(): _nhap_lo_chon_san('chua_so')

@ca('489 PR nháp: lô có sổ giữ hạn, cảnh báo nhưng vẫn nhận và hủy đúng')
def _nhap_co_so(): _nhap_lo_chon_san('co_so')

@ca('489 PR nháp: gói lô giữ hạn riêng, cảnh báo nhưng vẫn nhận và hủy đúng')
def _nhap_co_goi(): _nhap_lo_chon_san('goi')

@ca('489 PR nháp: hai dòng một lô không ghi đè hai hạn, cùng hạn ghi đủ hai dòng')
def _nhap_hai_han(): _nhap_lo_chon_san('hai_dong')


@ca('489 PR nháp: đọc HSD lỗi giữ hạn lô chưa sổ, xóa chủ động vẫn xóa được')
def _nhap_giu_han_loi():
	_nhap_lo_chon_san('giu')

@ca('489 PR nháp: xóa HSD chủ động trên lô chưa sổ vẫn xóa được')
def _nhap_xoa_han_chu_dong():
	_nhap_lo_chon_san('xoa')


@ca('489 PR nháp: giá tạm do máy chủ lấy từ chứng từ cùng công ty, payload không đổi giá vốn')
def _nhap_gia_may_chu():
	from frappe.utils import today
	from vagabond import nhan_hang
	from vagabond.khung.kiem_that.he_so_252 import _luu
	from vagabond.khung.kiem_that.gram_bom_252 import _kho_rieng
	cty=cong_ty();kho,tk=_kho_rieng(cty,'489-GIA')
	ma=_mon_thu('KT489-GIA-'+uuid.uuid4().hex[:10])
	def tao(gia):
		return _luu(frappe.get_doc(dict(doctype='Purchase Receipt',company=cty,
			supplier=nen.mot_nha_cung_cap(),currency='VND',conversion_rate=1,posting_date=today(),
			items=[dict(item_code=ma,qty=1,rate=gia,warehouse=kho,allow_zero_valuation_rate=1)])))
	cu=tao(1234);cu.submit()
	pr=tao(0);pr.reload();payload=pr.as_dict();payload['items'][0].rate=99999
	ra=nhan_hang.ghi_phieu_nhap(payload,[dict(dong=pr.items[0].name,sl=1,hsd='')]);pr.reload()
	la('giá mua gần nhất từ DB',float(pr.items[0].rate),1234)
	la('không thiếu giá',ra['thieu_gia'],[])
	sle=frappe.get_all('Stock Ledger Entry',filters={'voucher_type':'Purchase Receipt','voucher_no':pr.name,'is_cancelled':0},fields=['actual_qty','stock_value_difference'])
	la('giá vốn thật',sum(float(x.stock_value_difference) for x in sle),1234)
	pr.cancel();cu.cancel()


def _mua_ban_lo_cu(dt):
	from frappe.utils import today, add_days
	from vagabond.khung.kiem_that.thu_nhan_nvl import _lo, _nhap, _ton_lo
	from vagabond.khung.kiem_that.he_so_252 import _luu
	from vagabond.khung.kiem_that.gram_bom_252 import _kho_rieng
	cty=cong_ty(); kho,tk=_kho_rieng(cty,'489-MB')
	ma=_mon_thu('KT489-MB-'+uuid.uuid4().hex[:10],theo_lo=1)
	lo=_lo(ma,'KT489-LO-'+uuid.uuid4().hex[:10],add_days(today(),30))
	_nhap(ma,kho,[(lo,10)],cty)
	frappe.db.set_value('Batch',lo,{'expiry_date':add_days(today(),-1),'disabled':1})
	frappe.clear_document_cache('Batch',lo)
	mua=dt.startswith('Purchase')
	gia=1000 if mua else (108 if dt=='Sales Invoice' else 1)
	du_lieu=dict(doctype=dt,company=cty,currency='VND',conversion_rate=1,
		posting_date=today(),due_date=today(),update_stock=1,ignore_pricing_rule=1,
		bill_no='KT489-'+uuid.uuid4().hex[:10],bill_date=today(),
		items=[dict(item_code=ma,qty=1,rate=gia,warehouse=kho,batch_no=lo,use_serial_batch_fields=1)])
	du_lieu['supplier' if mua else 'customer']=nen.mot_nha_cung_cap() if mua else nen._mot('Customer',{'disabled':0})
	if dt=='Sales Invoice':
		from vagabond.hang_tang_so_cai import tai_khoan
		du_lieu['taxes']=[dict(charge_type='On Net Total',account_head=tai_khoan(cty,'33311','Liability'),
			rate=8,description='VAT fixture489 đã gồm giá',included_in_print_rate=1)]
	d=_luu(frappe.get_doc(du_lieu)); d.submit(); d.reload()
	la('ghi sổ thật',d.docstatus,1)
	truong='vgb_dien_giai' if dt=='Delivery Note' else 'remarks'
	vet=frappe.db.get_value(dt,d.name,truong) or ''
	dung('cảnh báo lưu DB cả hạn và tắt', 'Phiếu dùng lô quá hạn:' in vet and 'Phiếu dùng lô đã tắt:' in vet)
	sle=frappe.get_all('Stock Ledger Entry',filters={'voucher_type':dt,'voucher_no':d.name,'is_cancelled':0},fields=['actual_qty','warehouse'])
	la('SLE đúng kho',{x.warehouse for x in sle},{kho})
	la('SLE đúng lượng',sum(float(x.actual_qty) for x in sle),1 if mua else -1)
	la('tồn lô',_ton_lo(lo,kho),11 if mua else 9)
	d.cancel(); la('huỷ trả tồn',_ton_lo(lo,kho),10)


@ca('489 thật: Purchase Receipt lô tắt/quá hạn cảnh báo, SLE và huỷ')
def _pr_cu(): _mua_ban_lo_cu('Purchase Receipt')


@ca('489 thật: Purchase Invoice có kho lô tắt/quá hạn cảnh báo, SLE và huỷ')
def _pi_cu(): _mua_ban_lo_cu('Purchase Invoice')


@ca('489 thật: Delivery Note lô tắt/quá hạn cảnh báo, SLE và huỷ')
def _dn_cu(): _mua_ban_lo_cu('Delivery Note')


@ca('489 thật: Sales Invoice có kho lô tắt/quá hạn cảnh báo, SLE và huỷ')
def _si_cu(): _mua_ban_lo_cu('Sales Invoice')


@ca('489 thật: Batch mới giữ shelf life ngoài API, thiếu shelf life chỉ cảnh báo, không điền lại lô cũ')
def _shelf_life_that():
	from frappe.utils import today, add_days
	from vagabond.khung.kiem_that.thu_nhan_nvl import _lo
	ma=_mon_thu('KT489-SHELF-'+uuid.uuid4().hex[:10],theo_lo=1)
	it=frappe.get_doc('Item',ma); it.has_expiry_date=1; it.shelf_life_in_days=90; it.save()
	b=frappe.get_doc(dict(doctype='Batch',item=ma,batch_id='KT489-S-'+uuid.uuid4().hex[:10],manufacturing_date=today()))
	b.insert(); nen._DA_TAO.append(('Batch',b.name)); b.reload()
	la('giữ tự tính lô mới khác API',str(b.expiry_date),str(add_days(today(),90)))
	it.shelf_life_in_days=0; it.save()
	ten=_lo(ma,'KT489-NO-'+uuid.uuid4().hex[:10],None)
	b=frappe.get_doc('Batch',ten); la('thiếu shelf life vẫn tạo',b.expiry_date,None)
	it.shelf_life_in_days=90; it.save(); b.save(); b.reload()
	la('không suy lại hạn lô đã lưu',b.expiry_date,None)
