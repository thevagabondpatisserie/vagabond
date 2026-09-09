"""Hệ số tại Document thật; không gửi HĐĐT, không sửa dữ liệu đã có."""
import frappe
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la, dung
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu
from vagabond.he_so_chung_tu import kiem


def _luu(doc):
    doc.flags.ignore_permissions = True
    doc.insert(ignore_permissions=True)
    nen._DA_TAO.append((doc.doctype, doc.name))
    return doc


def _nen():
    ma = _mon_thu('KT-HS252-' + frappe.generate_hash(length=9))
    mon = frappe.get_doc('Item', ma)
    lon = 'Lon252-' + frappe.generate_hash(length=8)
    _luu(frappe.get_doc(dict(doctype='UOM', uom_name=lon, must_be_whole_number=1)))
    mon.append('uoms', dict(uom=lon, conversion_factor=550))
    mon.save(ignore_permissions=True)
    return mon, lon


def _pi(mon, lon, hs=550):
    return frappe.get_doc(dict(doctype='Purchase Invoice', company=nen.cong_ty(),
        supplier=nen.mot_nha_cung_cap(), currency='VND', conversion_rate=1,
        bill_no='KT-HS252-' + frappe.generate_hash(length=9), bill_date=frappe.utils.today(),
        posting_date=frappe.utils.today(), update_stock=0,
        items=[dict(item_code=mon.name, qty=1, uom=lon, conversion_factor=hs, rate=55000)]))


def _bi_chan(ham, nhan):
    try:
        ham()
    except frappe.ValidationError as e:
        dung(nhan + ' lỗi đúng hệ số', 'hệ số' in str(e) or 'quy cách' in str(e) or 'đơn vị' in str(e))
    else:
        dung(nhan + ' phải chặn', False)


@ca('#252 hệ số thật: PI Lon1 bị chặn, Lon550 lưu và reload giữ nguyên tiền')
def _pi_tay():
    mon, lon = _nen()
    truoc = frappe.db.count('Purchase Invoice')
    _bi_chan(lambda: _luu(_pi(mon, lon, 1)), 'insert API sai hệ số')
    la('không tạo PI sai', frappe.db.count('Purchase Invoice'), truoc)
    hd = _luu(_pi(mon, lon)); hd.reload()
    la('giữ hệ số đúng', hd.items[0].conversion_factor, 550)
    la('giữ lượng mua', hd.items[0].qty, 1)
    la('giữ tổng tiền', hd.grand_total, 55000)
    hd.items[0].conversion_factor = 1
    _bi_chan(lambda: hd.save(ignore_permissions=True), 'save Desk sai hệ số')
    hd.reload(); la('DB vẫn giữ quy cách đúng', hd.items[0].conversion_factor, 550)


@ca('#252 hệ số thật: giả stock_uom, hệ số âm/NaN/Inf và đơn vị kho khác1 không qua guard')
def _du_lieu_gia():
    mon, lon = _nen()
    hd = _pi(mon, lon)
    hd.items[0].stock_uom = lon
    _bi_chan(lambda: kiem(hd), 'không tin stock_uom của client')
    hd.items[0].stock_uom = mon.stock_uom
    for hs in (0, -1, float('nan'), float('inf')):
        hd.items[0].conversion_factor = hs
        _bi_chan(lambda: kiem(hd), 'số không hợp lệ')
    hd.items[0].uom = mon.stock_uom
    hd.items[0].conversion_factor = 550
    _bi_chan(lambda: kiem(hd), 'đơn vị kho phải là1')


@ca('#252 hệ số thật: danh mục đổi sau lưu nháp thì submit kiểm lại, không ghi GL dở')
def _doi_master():
    mon, lon = _nen()
    hd = _luu(_pi(mon, lon))
    row = next(d for d in mon.uoms if d.uom == lon)
    frappe.db.set_value('UOM Conversion Detail', row.name, 'conversion_factor', 1000)
    frappe.clear_document_cache('Item', mon.name)
    _bi_chan(lambda: hd.submit(), 'submit dùng danh mục mới')
    la('vẫn nháp', frappe.db.get_value(hd.doctype, hd.name, 'docstatus'), 0)
    la('không GL', frappe.db.count('GL Entry', {'voucher_type': hd.doctype, 'voucher_no': hd.name}), 0)


@ca('#252 hệ số thật: trả PI gốc giữ550 dù danh mục đã đổi1000')
def _tra_lich_su():
    mon, lon = _nen()
    hd = _luu(_pi(mon, lon)); hd.submit(); hd.reload()
    row = next(d for d in mon.uoms if d.uom == lon)
    frappe.db.set_value('UOM Conversion Detail', row.name, 'conversion_factor', 1000)
    frappe.clear_document_cache('Item', mon.name)
    tra = _pi(mon, lon)
    tra.is_return = 1; tra.return_against = hd.name
    tra.items[0].qty = -1
    _luu(tra); tra.submit(); tra.reload()
    la('phiếu trả ghi sổ', tra.docstatus, 1)
    la('trả đúng quy cách cũ', tra.items[0].conversion_factor, 550)
    la('trả đủ lượng cũ', tra.items[0].stock_qty, -550)
    la('PI gốc không bị sửa', frappe.db.get_value('Purchase Invoice Item', hd.items[0].name, 'conversion_factor'), 550)


@ca('#252 hệ số thật: nguồn PO khác master không tự hợp thức hoá PI, nguồn sai dòng bị chặn')
def _nguon():
    mon, lon = _nen()
    po = _luu(frappe.get_doc(dict(doctype='Purchase Order', company=nen.cong_ty(),
        supplier=nen.mot_nha_cung_cap(), schedule_date=frappe.utils.today(),
        items=[dict(item_code=mon.name, qty=1, uom=lon, conversion_factor=550,
            rate=55000, schedule_date=frappe.utils.today())])))
    po.submit(); po.reload()
    hd = _pi(mon, lon)
    hd.items[0].purchase_order = po.name
    hd.items[0].po_detail = po.items[0].name
    kiem(hd)
    # Đổi từ Lon sang đơn vị kho là nghiệp vụ core hợp lệ. Guard không
    # được so trực tiếp hệ số của hai đơn vị khác nhau rồi chặn nhầm.
    hd.items[0].uom = mon.stock_uom
    hd.items[0].stock_uom = mon.stock_uom
    hd.items[0].conversion_factor = 1
    hd.items[0].qty = 550
    kiem(hd)
    hd.items[0].uom = lon
    hd.items[0].conversion_factor = 550
    hd.items[0].qty = 1
    hd.items[0].po_detail = 'khong-thuoc-phieu'
    _bi_chan(lambda: kiem(hd), 'phải đúng dòng nguồn')
    hd.items[0].po_detail = po.items[0].name
    row = next(d for d in mon.uoms if d.uom == lon)
    frappe.db.set_value('UOM Conversion Detail', row.name, 'conversion_factor', 1000)
    frappe.clear_document_cache('Item', mon.name)
    _bi_chan(lambda: _luu(hd), 'không lấy nguồn cũ làm lý do bỏ qua chênh lệch')


@ca('#252 hệ số thật: SO/DN/SI/SE/PO/PR đều không nhận quy cách1 thay550')
def _cac_chung_tu():
    mon, lon = _nen()
    for loai in ('Sales Order', 'Delivery Note', 'Sales Invoice', 'Stock Entry', 'Purchase Order', 'Purchase Receipt'):
        doc = frappe.get_doc(dict(doctype=loai, company=nen.cong_ty(), items=[
            dict(item_code=mon.name, uom=lon, stock_uom=mon.stock_uom, conversion_factor=1, qty=1)]))
        _bi_chan(lambda: kiem(doc), loai)


@ca('#252 hệ số thật: alias NCC theo bảng Món, tên đơn vị lạ không rơi về1')
def _alias_ncc():
    from vagabond.minvoice_chung_tu import don_vi_theo_ma
    mon, _ = _nen()
    if not frappe.db.exists('UOM', 'Lon'):
        _luu(frappe.get_doc(dict(doctype='UOM', uom_name='Lon', must_be_whole_number=1)))
    mon.append('uoms', dict(uom='Lon', conversion_factor=550))
    mon.save(ignore_permissions=True)
    la('CAN dùng quy cách Lon của Món', don_vi_theo_ma(mon.name, 'CAN'), ('Lon', 550))
    la('tên đúng không bị hạ hệ số', don_vi_theo_ma(mon.name, 'Lon'), ('Lon', 550))
    _bi_chan(lambda: don_vi_theo_ma(mon.name, 'KIENTHU252-KHONG-BIET'), 'NCC ghi đơn vị chưa khai')


@ca('#252 hệ số thật: MInvoice cùng UOM1 được nắn550 qua hook mà không đổi tiền')
def _minvoice_cung_uom():
    from vagabond.khung.kiem_that.thu_mua_hddt_227 import _nguon
    from vagabond import minvoice_chung_tu as mc
    from vagabond.dung_lai_hddt import nan_quy_cach_tu_goc
    mon, lon = _nen()
    ten = 'Cherry thử ' + frappe.generate_hash(length=8)
    raw = [{'ten': ten, 'dvtinh': lon, 'sluong': 1, 'dgia': 55000, 'thtien': 55000, 'tchat': '1'}]
    la('đọc đúng hình dạng nguồn thật', mc.dong_tu_hoa_don(mc.dong_hang_hoa(raw)[0])['dvt'], lon)
    goc = _nguon(raw, 0, 55000)
    hd = _pi(mon, lon, hs=1)
    hd.items[0].item_name = ten
    hd.items[0].ten_hang_ncc = ten
    hd.items[0].description = ten + ' (' + lon + ')'
    truoc = (hd.items[0].qty, hd.items[0].rate)
    nan_quy_cach_tu_goc(hd, goc.as_dict())
    la('hàm nắn cùng UOM sửa hệ số', hd.items[0].conversion_factor, 550)
    la('hàm nắn không đổi lượng/giá', (hd.items[0].qty, hd.items[0].rate), truoc)
    # Trả về lỗi đầu vào rồi để before_validate thật sửa lại trước guard.
    hd.items[0].conversion_factor = 1
    hd.custom_minvoice_id = goc.name
    _luu(hd); hd.reload()
    la('hook insert thực sự nắn550', hd.items[0].conversion_factor, 550)
    la('lượng kho đúng', hd.items[0].stock_qty, 550)
    la('không sửa lượng/giá qua insert', (hd.items[0].qty, hd.items[0].rate), truoc)
    la('tiền vẫn55000', hd.grand_total, 55000)
    hd.items[0].conversion_factor = 1
    hd.save(ignore_permissions=True); hd.reload()
    la('hook save vẫn sửa lại550', hd.items[0].conversion_factor, 550)
    la('save vẫn giữ tiền', hd.grand_total, 55000)


@ca('#252 quy cách NCC thật: đúng MST/tên dùng UOM đã chọn, sai món/UOM bị chặn')
def _quy_cach_ncc():
    from vagabond import quy_cach_ncc as qc
    mon, lon = _nen()
    mst = 'KT252' + frappe.generate_hash(length=8)
    ten = 'Chai riêng NCC ' + frappe.generate_hash(length=8)
    ban = _luu(frappe.get_doc(dict(doctype=qc.LOAI, supplier_mst=mst,
        ten_ncc=ten, item_code=mon.name, vgb_uom=lon)))
    la('đúng NCC và tên lấy quy cách', qc.lay(mon.name, mst, ten), lon)
    la('khác NCC không mượn quy cách', qc.lay(mon.name, mst+'x', ten), None)
    la('khác tên không mượn quy cách', qc.lay(mon.name, mst, ten+'x'), None)
    khac, _ = _nen()
    _bi_chan(lambda: qc.lay(khac.name, mst, ten), 'ánh xạ chọn món khác')
    ban.vgb_uom = khac.uoms[-1].uom
    _bi_chan(lambda: ban.save(ignore_permissions=True), 'UOM chưa khai của món')
    ban.reload(); la('ánh xạ đúng vẫn nguyên', ban.vgb_uom, lon)
    from vagabond.khung.kiem_that.thu_mua_hddt_227 import _nguon
    goc = _nguon([{'ten': ten, 'dvtinh': lon, 'sluong': 1, 'dgia': 55000, 'thtien': 55000}], 0, 55000)
    frappe.db.set_value(goc.doctype, goc.name, 'mst_doi_tac', mst)
    hd = _pi(mon, mon.stock_uom, 1)
    hd.custom_minvoice_id = goc.name
    hd.items[0].ten_hang_ncc = ten
    _bi_chan(lambda: kiem(hd), 'không đổi sang UOM khác dù hợp lệ trong master')
    hd.items[0].uom = lon; hd.items[0].conversion_factor = 550
    kiem(hd)
