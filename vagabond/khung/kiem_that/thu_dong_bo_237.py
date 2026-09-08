"""#237: vận đơn mới trong savepoint, HTTP giả lập, lưu/reload thật."""
from contextlib import ExitStack
from unittest.mock import patch
import frappe
from frappe.utils import add_days, nowdate
from vagabond import van_don as vd
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la


def tao():
    d=frappe.get_doc({'doctype':'Van Don','ngay_giao':add_days(nowdate(),3650),
        'pancake_id':'THU237-'+frappe.generate_hash(length=12),'ma_don':'THU237',
        'trang_thai':'Chờ giao','kenh':'Shipper nội bộ','khach':'Khách thử237',
        'dia_chi':'Địa chỉ phải giữ','tien_thu_ho':123})
    d.append('mon',{'ma_hang':'THU-A','ten':'Bánh thử A','so_luong':2})
    d.append('mon',{'ma_hang':'THU-B','ten':'Bánh thử B','so_luong':1})
    d.insert(ignore_permissions=True)
    nen._DA_TAO.append((d.doctype,d.name))
    return d


def dong_bo(d,o,ds=None,loi_luu=False):
    class R:
        status_code=200
        def json(self): return {'data':o}
    class Mang:
        def get(self,url,**kw):
            if url.rsplit('/',1)[-1] != d.pancake_id: raise AssertionError('Cấm đọc đơn thật')
            return R()
    with ExitStack() as st:
        st.enter_context(patch.object(vd,'cfg',lambda:frappe._dict(pancake_shop_id='THU')))
        st.enter_context(patch.object(vd,'key',lambda *a:'THU'))
        st.enter_context(patch.object(vd,'_keo_don',lambda *a:ds if ds is not None else []))
        st.enter_context(patch.object(vd,'_mang',lambda:Mang()))
        st.enter_context(patch.object(vd,'cache_get',lambda *a:None))
        st.enter_context(patch.object(vd,'cache_set',lambda *a:None))
        if loi_luu: st.enter_context(patch.object(vd,'_ghi_mon',side_effect=RuntimeError('Lỗi thử sau đổi ngày')))
        return vd._dong_bo_pancake_ruot(str(d.ngay_giao))


def don(d):
    return {'id':d.pancake_id,'display_id':'THU237','status':1,
        'estimate_delivery_date':str(add_days(d.ngay_giao,2))+'T08:00:00+07:00',
        'items':[{'variation_info':{'display_id':'THU-A','name':'Bánh thử A','retail_price':100},'quantity':1}]}


@ca('#237: dời ngày và bỏ món qua ID, reload ngày cũ hết đơn, chạy lại không nhân đôi')
def _doi_ngay_mon():
    d=tao();cu=d.ngay_giao;o=don(d)
    ra=dong_bo(d,o);la('không lỗi',ra['loi'],[]);d.reload()
    la('ngày mới',str(d.ngay_giao),str(add_days(cu,2)))
    la('món đã bỏ không còn',[(r.ma_hang,r.so_luong) for r in d.mon],[('THU-A',1)])
    la('không xoá địa chỉ vì nguồn thiếu',d.dia_chi,'Địa chỉ phải giữ')
    la('ngày cũ không còn',frappe.db.count('Van Don',{'name':d.name,'ngay_giao':cu}),0)
    dong_bo(d,o,[o]);d.reload()
    la('một vận đơn cùng ID',frappe.db.count('Van Don',{'pancake_id':d.pancake_id}),1)


@ca('#237: nguồn trả items rỗng xoá hết bảng con thật; huỷ pickup giữ vết')
def _rong_huy():
    d=tao();o=don(d);o['items']=[]
    ra=dong_bo(d,o);la('không lỗi',ra['loi'],[]);d.reload()
    la('bảng con thật rỗng',frappe.db.count('Van Don Mon',{'parent':d.name}),0)
    d.trang_thai='Chờ khách lấy';d.save(ignore_permissions=True)
    ra=dong_bo(d,{'id':d.pancake_id,'status':6});la('không lỗi huỷ',ra['loi'],[]);d.reload()
    la('pickup đã huỷ',d.trang_thai,'Huỷ')
    la('không xoá chứng từ',frappe.db.exists('Van Don',d.name),d.name)


@ca('#237: lỗi lưu món sau đổi ngày hoàn nguyên cả ngày và món')
def _rollback():
    d=tao();cu=str(d.ngay_giao)
    ra=dong_bo(d,don(d),loi_luu=True);d.reload()
    la('báo lỗi riêng đơn',len(ra['loi']),1)
    la('ngày được trả lại',str(d.ngay_giao),cu)
    la('món được trả lại',[(r.ma_hang,r.so_luong) for r in d.mon],[('THU-A',2),('THU-B',1)])


@ca('#237: phí book lưu/reload, không đổi COD và không sửa sau đối soát')
def _phi():
    d=tao();d.kenh='Grab';d.save(ignore_permissions=True)
    with patch.object(vd,'_la_sales',lambda:True):
        vd.luu_phi_book(d.name,45000);d.reload()
        la('phí thực lưu',d.phi_giao,45000);la('COD giữ nguyên',d.tien_thu_ho,123)
        d.da_doi_soat=1;d.save(ignore_permissions=True)
        try: vd.luu_phi_book(d.name,50000)
        except frappe.ValidationError: pass
        else: raise AssertionError('Đã sửa phí sau đối soát')
    d.reload();la('phí vẫn cũ',d.phi_giao,45000)
