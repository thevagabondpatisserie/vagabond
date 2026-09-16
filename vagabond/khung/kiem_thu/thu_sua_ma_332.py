"""#332: đổi mã giữ tiền nguồn, lỗi lưu không để ánh xạ viết dở."""
from contextlib import ExitStack
from types import SimpleNamespace as NS
from unittest.mock import patch
from vagabond import sua_ma_hoa_don as sm, minvoice_chung_tu as mc, quy_cach_ncc as qc
from vagabond.khung.kiem_thu.nen import ca, la, nem
from vagabond.khung.kiem_thu.thu_mua_hddt_227 import To


class Dong(To):
    def update(self, d):
        self.__dict__.update(d)


def _nen(loi=False):
    d = Dong(name='R', idx=1, item_code='CU', item_name='Tên cũ', ten_hang_ncc='Hàng nguồn',
             qty=3, rate=395000, uom='Chai', conversion_factor=750)
    doc = Dong(items=[d], name='PI', modified='M', grand_total=995454)
    ghi = []
    doc.save = lambda: (_ for _ in ()).throw(ValueError('save fail')) if loi else ghi.append('save')
    doc.reload = lambda: ghi.append('reload')
    doc.add_comment = lambda *a: ghi.append('comment')
    mapping = Dong(save=lambda **k: ghi.append('map'))
    def value(dt, name, field):
        return {'stock_uom':'ML', 'item_name':'Món mới', 'conversion_factor':700}.get(field)
    def throw(s):
        raise ValueError(s)
    bo = ExitStack()
    bo.enter_context(patch.object(sm, 'frappe', NS(db=NS(get_value=value), new_doc=lambda *a:mapping, throw=throw)))
    bo.enter_context(patch.object(qc, '_kiem_uom', lambda *a: None))
    bo.enter_context(patch.object(qc, '_anh_xa', lambda *a: []))
    g = dict(mst_doi_tac='123', chi_tiet=[dict(ten='Hàng nguồn', sluong=3, dgia=331818, dvtinh='Chai')])
    return bo, doc, g, ghi


@ca('#332: chọn lại mã/UOM giữ tên và giá nguồn, save rồi reload trước báo thành công')
def _doi():
    bo, doc, g, ghi = _nen()
    with bo:
        r = sm._sua(doc, g, 'R', '0', 'MOI', 'Chai 700 ml')
    la('giá nguồn', r['rate'], 331818)
    la('lượng nguồn', r['qty'], 3)
    la('quy cách mới', doc.items[0].conversion_factor, 700)
    la('tên nguồn còn', doc.items[0].ten_hang_ncc, 'Hàng nguồn')
    la('thứ tự', ghi, ['map','save','reload','comment'])


@ca('#332: không đoán khi nguồn trùng, đã tách hoặc đã nối kho')
def _mo_ho():
    for cach in ('trung','tach','noi','dong_sai'):
        bo, doc, g, ghi = _nen()
        with bo:
            if cach == 'trung': g['chi_tiet'] *= 2
            if cach == 'tach': doc.items.append(Dong(name='R2', ten_hang_ncc='Hàng nguồn'))
            if cach == 'noi': doc.items[0].pr_detail='PR-ROW'
            nem(cach, lambda:sm._sua(doc,g,'khong-co' if cach=='dong_sai' else 'R',0,'MOI','Chai 700 ml'), ValueError)
        la('chưa ghi gì', ghi, [])


@ca('#332: ánh xạ Item disabled cho dòng chưa gán mã, giữ nguyên nguồn để xử lý')
def _disabled():
    with patch.object(qc,'tim_mon',lambda *a:'CU'), \
         patch.object(mc,'frappe',NS(db=NS(get_value=lambda *a:1, exists=lambda *a:True))), \
         patch.object(mc,'don_vi_theo_ma',side_effect=AssertionError('không được lấy quy cách món ngừng dùng')):
        la('không gán món ngừng dùng',mc._tra_ma_hang(dict(ten='Hàng nguồn',ma='',dvt='Chai'),'123','NCC'),(None,'Chai',1))


@ca('#332: API lỗi lưu rollback ánh xạ, không commit; phiên cũ không bắt đầu ghi')
def _rollback():
    from vagabond import doi_chieu_mua as dc
    bo, doc, g, ghi = _nen()
    with bo, patch.object(sm,'_phieu',lambda *a:(doc,g)), \
         patch.object(dc,'_kiem_quyen',lambda:None), patch.object(dc,'_lam_duoc',lambda:True), \
         patch.object(sm,'_sua',side_effect=ValueError('loi save')):
        sm.frappe.generate_hash=lambda **k:'ABC'
        sm.frappe.db.savepoint=lambda moc:ghi.append('savepoint')
        sm.frappe.db.rollback=lambda **k:ghi.append('rollback')
        nem('lỗi save',lambda:sm.sua('PI','R',0,'MOI','Chai','M'),ValueError)
        la('lùi cùng giao dịch',ghi,['savepoint','rollback'])
        ghi.clear()
        nem('stale',lambda:sm.sua('PI','R',0,'MOI','Chai','CU'),ValueError)
        la('stale chưa ghi',ghi,[])


@ca('#332: hồ sơ mất nguồn chỉ cảnh báo trong đúng NCC/công ty, không tự gắn')
def _mat_nguon():
    goi=[]
    doc=To(name='PI', company='CTY', supplier='NCC', bill_no='123', custom_minvoice_id=None)
    with patch.object(sm,'frappe',NS(get_list=lambda *a,**k:goi.append(k) or [To(name='GOC')])):
        la('gợi ý',sm._lien_quan(doc)[0].name,'GOC')
        la('đúng NCC',goi[0]['filters']['supplier'],'NCC')
        la('đúng công ty',goi[0]['filters']['company'],'CTY')
        la('loại chính tờ',goi[0]['filters']['name'],['!=','PI'])
        la('không tự gắn nguồn',doc.custom_minvoice_id,None)
        doc.custom_minvoice_id='M'
        la('có nguồn không cảnh báo bản sao',sm._lien_quan(doc),[])
        la('không đọc thêm',len(goi),1)
