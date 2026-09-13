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
	frappe.db.set_single_value('Vagabond Settings', 'chan_lo_het_han', 0)
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
	frappe.db.set_single_value('Vagabond Settings', 'chan_lo_het_han', 1)
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
