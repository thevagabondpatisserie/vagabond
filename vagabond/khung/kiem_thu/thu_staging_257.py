"""#257: báo cáo UOM phải phát hiện lệch thật mà không tự đoán quy đổi."""
from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.staging.ra_uom import ra


@ca('#257 UOM: quả và pcs chỉ báo lệch khi có quy ước theo món đã duyệt')
def _():
    mon = [dict(item_code='TRUNG-THU', stock_uom='pcs', uoms=[dict(uom='pcs', conversion_factor=1)])]
    la('khong doan tu ten', ra(mon, {})['so_phat_hien'], 0)
    kq = ra(mon, {'TRUNG-THU': 'Quả'})
    la('bao dung lech', kq['phat_hien'][0]['loai'], 'lech_quy_uoc')
    la('khong sua nguon', mon[0]['stock_uom'], 'pcs')


@ca('#257 UOM: bắt hệ số không hữu hạn, bằng 0 và đơn vị gốc khác 1')
def _():
    for he in ['NaN', 'Infinity', 0, -1, None, 'khong phai so']:
        kq = ra([dict(item_code='THU', stock_uom='Gram', uoms=[dict(uom='Gram', conversion_factor=he)])], {})
        dung('he so sai bi bao', any(r['loai'] == 'he_so_khong_hop_le' for r in kq['phat_hien']))
    kq = ra([dict(item_code='THU', stock_uom='Gram', uoms=[dict(uom='Gram', conversion_factor=1000)])], {})
    la('goc bang mot', kq['phat_hien'][0]['loai'], 'he_so_goc_khac_mot')


@ca('#257 UOM: không bỏ sót quy đổi mua bán và bản xuất thiếu món')
def _():
    kq = ra([dict(item_code='THU', stock_uom='Quả', purchase_uom='Thùng', sales_uom='Gói', uoms=[])], {'THIEU': 'Gram'})
    la('du ba phat hien', kq['so_phat_hien'], 3)
    kq = ra([dict(item_code='THU', stock_uom='Quả', purchase_uom='Thùng', uoms=[dict(uom='Thùng', conversion_factor=30)])], {})
    la('he so ro rang dat', kq['so_phat_hien'], 0)


@ca('#257 nguồn thử: danh sách ngày cũ rỗng nhưng GET theo ID vẫn trả ngày mới')
def _():
    from datetime import datetime
    from vagabond.khung.staging.nguon_pancake import tra
    don = {'id': 'THU257-93405', 'estimate_delivery_date': '2036-09-10T08:00:00+07:00'}
    goc = 'https://pos.pages.fm/api/v1/shops/THU257/orders'
    def moc(s): return int(datetime.fromisoformat(s + 'T00:00:00+07:00').timestamp())
    p = dict(api_key='THU257', updateStatus='estimate_delivery_date', page_number=1,
             startDateTime=moc('2036-09-08'), endDateTime=moc('2036-09-09') - 1)
    la('ngay cu rong', tra(goc, p, don)['data'], [])
    la('ID con o nguon', tra(goc + '/' + don['id'], {'api_key': 'THU257'}, don)['data'], don)
    p.update(startDateTime=moc('2036-09-10'), endDateTime=moc('2036-09-11') - 1)
    la('ngay moi co don', tra(goc, p, don)['data'], [don])
    for url in [goc.replace('THU257', 'SHOP-THAT'), goc + '/ID-KHAC', goc.replace('pos.pages.fm', 'example.com')]:
        try: tra(url, p, don)
        except ValueError: pass
        else: raise AssertionError('Nguồn thử nhận URL không thuộc fixture')


@ca('#257 xuất UOM: đi hết trang và ghép đúng quy đổi, không tự duyệt đơn vị')
def _():
    from vagabond.khung.staging.xuat_uom import doc
    da_doc = []
    def lay(dt, **kw):
        da_doc.append((dt, kw))
        if dt == 'UOM Conversion Detail':
            return [{'parent': 'A', 'uom': 'Thùng', 'conversion_factor': 30}] if 'A' in kw['filters']['parent'][1] else []
        if 'modified' in kw['filters']: return []
        moc = kw['filters']['name'][1]
        return {'': [{'name': 'A', 'item_code': 'A', 'stock_uom': 'Quả'}],
                'A': [{'name': 'B', 'item_code': 'B', 'stock_uom': 'Gram'}], 'B': []}[moc]
    kq = doc(lay, '2036-09-10 00:00:00')
    la('du hai trang', [d['item_code'] for d in kq['items']], ['A', 'B'])
    la('quy doi dung mon', kq['items'][0]['uoms'], [{'uom': 'Thùng', 'conversion_factor': 30}])
    la('khong ghep nham', kq['items'][1]['uoms'], [])
    la('khong tu duyet', kq['quy_uoc_da_duyet'], {})


@ca('#257 xuất UOM: từ chối snapshot đổi giữa chừng hoặc trang không tiến')
def _():
    from vagabond.khung.staging.xuat_uom import doc
    def doi(dt, **kw):
        return [{'name': 'A'}] if 'modified' in kw['filters'] else []
    def lap(dt, **kw):
        return [] if dt == 'UOM Conversion Detail' else [{'name': 'A', 'item_code': 'A'}]
    for lay in (doi, lap):
        try: doc(lay, '2036-09-10 00:00:00')
        except RuntimeError: pass
        else: raise AssertionError('Snapshot không ổn định vẫn được nhận')


@ca('#257 xuất UOM: hơn 500 quy đổi trong một trang không bị cắt')
def _():
    from vagabond.khung.staging.xuat_uom import doc
    def lay(dt, **kw):
        if dt == 'UOM Conversion Detail':
            ds = [{'parent': 'A', 'uom': 'Quy cách %s' % i, 'conversion_factor': i + 1} for i in range(501)]
            han = kw.get('limit_page_length', 20)
            return ds[:han] if han else ds
        if 'modified' in kw['filters'] or kw['filters']['name'][1]: return []
        return [{'name': 'A', 'item_code': 'A', 'stock_uom': 'Quả'}]
    la('giữ đủ quy đổi', len(doc(lay, '2036-09-10')['items'][0]['uoms']), 501)
