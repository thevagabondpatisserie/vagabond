"""Đổi mã trên hóa đơn nguồn bằng lựa chọn rõ ràng, không xóa/thêm dòng.

#332: thay dòng làm mất tên NCC, lấy giá bảng và quy cách của mã mới;
ánh xạ cũ lại trỏ món ngừng dùng nên hook không khôi phục được. Người dùng
chọn dòng nguồn + mã + UOM, máy kiểm đủ trước khi lưu chung với ánh xạ.
Không chạy tự động trên chứng từ cũ, không thêm chốt chặn save/submit.
"""
from html import escape
import frappe
from frappe.utils import flt
from vagabond import dung_lai_hddt as dl, minvoice_chung_tu as mc, quy_cach_ncc as qc


def _phieu(name, can_nguon=True):
    doc = frappe.get_doc('Purchase Invoice', name, for_update=True)
    doc.check_permission('write')
    if doc.docstatus != 0 or (can_nguon and doc.get('is_return')):
        frappe.throw('Chỉ sửa mã theo nguồn trên hóa đơn mua nháp. Tờ đã ghi sổ dùng quy trình sửa/hủy của ERP.')
    g = dl._goc(doc.get('custom_minvoice_id'))
    if not g and can_nguon:
        frappe.throw('Tờ này chưa có liên kết hóa đơn nguồn. Mở hồ sơ đồng bộ gốc để đối chiếu, không tạo thêm bản sao.')
    return doc, g


def _dong_goc(g):
    return [mc.dong_tu_hoa_don(d, mc.dau_cua_to(g.get('tong_tien')))
            for d in mc.dong_hang_hoa(dl.doc_chi_tiet(g.get('chi_tiet')))]


@frappe.whitelist()
def lua_chon(name):
    doc, g = _phieu(name, can_nguon=False)
    if not g or doc.get('is_return'):
        return dict(co_nguon=False)
    return dict(co_nguon=True, modified=str(doc.modified),
        dong=[dict(name=d.name, idx=d.idx, nhan='%s. %s' % (d.idx, d.item_name or d.item_code or ''),
                   item_code=d.item_code) for d in doc.items],
        nguon=[dict(vi_tri=i, ten=x['ten'], sl=x['sl'], gia=x['gia'], dvt=x['dvt'])
               for i, x in enumerate(_dong_goc(g))])


def _sua(doc, g, dong, vi_tri, item_code, uom):
    """Trong savepoint của caller; không commit và không sửa chứng từ khác."""
    ds = _dong_goc(g)
    if str(vi_tri) not in {str(i) for i in range(len(ds))}:
        frappe.throw('Chọn một dòng có thật trên hóa đơn nguồn.')
    x = ds[int(vi_tri)]
    ten = str(x.get('ten') or '').strip()[:140]
    if not ten or sum(str(r.get('ten') or '').strip()[:140] == ten for r in ds) != 1:
        frappe.throw('Tên nguồn đang trùng hoặc trống. Dùng đối chiếu chi tiết để sửa tay, không đoán dòng theo vị trí.')
    d = next((r for r in doc.items if r.name == dong), None)
    if not d:
        frappe.throw('Dòng đã thay đổi. Tải lại hóa đơn rồi chọn lại dòng cần sửa.')
    if d.get('pr_detail') or d.get('purchase_receipt') or d.get('po_detail'):
        frappe.throw('Dòng đang nối chứng từ kho/mua. Bỏ nối dòng này trước khi đổi mã hoặc quy cách; tiền trên phiếu nhập không tự đổi.')
    if any(r.name != d.name and dl.khoa_ten(dl.ten_ncc_cua_dong(r)) == dl.khoa_ten(ten)
           for r in doc.items):
        frappe.throw('Dòng nguồn này đã nằm ở dòng khác hoặc đã tách qua nhiều phiếu. Đối chiếu các dòng đó trước, không cộng thêm lượng nguồn.')
    qc._kiem_uom(item_code, uom)
    stock_uom = frappe.db.get_value('Item', item_code, 'stock_uom')
    hs = 1 if uom == stock_uom else flt(frappe.db.get_value('UOM Conversion Detail',
        {'parent': item_code, 'parenttype': 'Item', 'uom': uom}, 'conversion_factor'))
    mst = (g.get('mst_doi_tac') or '').strip().split('-')[0]
    if not mst:
        frappe.throw('Nguồn thiếu MST nhà cung cấp. Kiểm lại bản nguồn trước khi ghi nhớ mã và quy cách.')
    # tim_mon ưu tiên mã NCC rồi mới tên. Sửa cả hai khóa, kể cả khi
    # tên lưu ở khóa mã là tên cũ; không để lần đồng bộ sau quay về mã cũ.
    ma = str(x.get('ma') or '').strip()
    theo_ma = qc._anh_xa(mst, 'ma_ncc', ma) if ma else []
    theo_ten = qc._anh_xa(mst, 'ten_ncc', ten)
    if len(theo_ma) > 1 or len(theo_ten) > 1:
        frappe.throw('Có nhiều ánh xạ cùng mã hoặc tên nguồn. Mở ánh xạ NCC và giữ một lựa chọn rõ ràng trước khi sửa.')
    ds_map = {}
    for r in theo_ma + theo_ten:
        if r.name not in ds_map:
            ds_map[r.name] = frappe.get_doc(qc.LOAI, r.name, for_update=True)
    for r in theo_ten:
        ma_cu = str(ds_map[r.name].get('ma_ncc') or '').strip()
        if ma_cu and ma_cu != ma:
            frappe.throw('Tên nguồn đang thuộc một mã NCC khác. Đối chiếu ánh xạ trước khi đổi, không ghi đè mã khác.')
    if not theo_ten:
        m = frappe.new_doc(qc.LOAI)
        m.update(dict(supplier_mst=mst, ten_ncc=ten, ma_ncc=ma if not theo_ma else ''))
        ds_map['__moi__'] = m
    # Giữ tên lịch sử trên mapping theo mã; mapping đúng tên cấp quy cách.
    # Ghi trước save để hook đọc lựa chọn mới, lỗi sau đó rollback tất cả.
    for m in ds_map.values():
        m.update(dict(item_code=item_code, vgb_uom=uom))
        m.save(ignore_permissions=True)
    cu = dict(item_code=d.item_code, uom=d.uom, qty=d.qty, rate=d.rate)
    d.update(dict(item_code=item_code, item_name=frappe.db.get_value('Item', item_code, 'item_name'),
        ten_hang_ncc=ten, qty=x['sl'], rate=x['gia'], price_list_rate=x['gia'],
        discount_percentage=0, discount_amount=0, margin_rate_or_amount=0,
        uom=uom, stock_uom=stock_uom, conversion_factor=hs))
    doc.ignore_pricing_rule = 1
    doc.save()
    doc.reload()
    sau = [r for r in doc.items if r.name == dong]
    if len(sau) != 1 or any(sau[0].get(k) != v for k, v in dict(
        item_code=item_code, ten_hang_ncc=ten, uom=uom).items()) or any(
        abs(flt(sau[0].get(k)) - flt(v)) > 0.000001 for k, v in dict(
            qty=x['sl'], rate=x['gia'], conversion_factor=hs).items()):
        frappe.throw('Lượt lưu chưa giữ đúng dòng đã chọn. Hệ thống đã lùi cả sửa mã và ánh xạ; tải lại và báo kỹ thuật.')
    doc.add_comment('Comment', escape('Sửa mã theo dòng nguồn %s: %s -> %s; đơn vị %s -> %s. '
        'Giữ số lượng/giá theo nguồn: %s / %s; trước sửa: %s / %s.' %
        (int(vi_tri)+1, cu['item_code'], item_code, cu['uom'], uom,
         x['sl'], x['gia'], cu['qty'], cu['rate'])))
    return dict(name=doc.name, item_code=item_code, uom=uom, qty=sau[0].qty,
                rate=sau[0].rate, grand_total=doc.grand_total)


@frappe.whitelist()
def sua(name, dong, vi_tri, item_code, uom, modified):
    from vagabond.doi_chieu_mua import _kiem_quyen, _lam_duoc
    _kiem_quyen()
    if not _lam_duoc():
        frappe.throw('Chỉ kế toán hoặc thu mua được sửa mã hóa đơn.')
    doc, g = _phieu(name)
    if str(doc.modified) != str(modified):
        frappe.throw('Hóa đơn vừa được sửa ở nơi khác. Tải lại và kiểm dòng nguồn trước khi thử lại.')
    moc = 'sua_ma_' + frappe.generate_hash(length=10)
    frappe.db.savepoint(moc)
    try:
        return _sua(doc, g, dong, vi_tri, str(item_code or '').strip(), str(uom or '').strip())
    except Exception:
        frappe.db.rollback(save_point=moc)
        raise


def _lien_quan(doc):
    """Chỉ gợi ý cùng số/NCC/công ty, không tự coi đó là bản sao hay gắn nguồn."""
    if doc.get('custom_minvoice_id') or not all(doc.get(k) for k in ('bill_no','supplier','company')):
        return []
    return frappe.get_list('Purchase Invoice', filters=dict(
        company=doc.company, supplier=doc.supplier, bill_no=doc.bill_no,
        name=['!=', doc.name or ''], docstatus=['<',2], custom_minvoice_id=['is','set']),
        fields=['name'], limit_page_length=5, order_by='creation desc')


@frappe.whitelist()
def lien_quan(name):
    doc = frappe.get_doc('Purchase Invoice', name)
    doc.check_permission('read')
    return _lien_quan(doc)


def nhac_nguon(doc, method=None):
    """Tờ gõ/sao chép mất mã nguồn vẫn được ghi sổ, có đường kiểm hồ sơ gốc."""
    try:
        ds = _lien_quan(doc)
        if ds:
            frappe.msgprint('Tờ này chưa liên kết hóa đơn điện tử, nhưng có hồ sơ cùng số hóa đơn, '
                'nhà cung cấp và công ty: ' + ', '.join(escape(d.name) for d in ds) +
                '. Mở hồ sơ đó kiểm tiền và trạng thái để tránh ghi sổ hai lần. '
                'Đây là cảnh báo, không chặn ghi sổ và không tự gắn nguồn.',
                title='Kiểm tra hồ sơ hóa đơn liên quan', indicator='orange')
    except Exception:
        # Không biến lỗi tra cảnh báo thành chặn kế toán.
        try:
            frappe.log_error(title='Đối chiếu liên kết hóa đơn nguồn', message=frappe.get_traceback())
        except Exception:
            pass
