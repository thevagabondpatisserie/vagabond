"""Gọi cửa tạo thật: FIN lập và gửi ngay phải lưu dấu FIN trước insert."""
from contextlib import ExitStack
from unittest.mock import patch
import frappe
from vagabond import ho_so_tt as hs
from vagabond.khung.kiem_thu.nen import ca, la

class Doc(frappe._dict):
    def __getattr__(self,k): return self.get(k)
    def __setattr__(self,k,v): self[k]=v
    def set(self,k,v): self[k]=v
    def append(self,k,v): self.setdefault(k,[]).append(v)
    def insert(self,**kw):
        self.name='APP-TEST'
        self.tong_tien=sum(d['so_tien'] for d in self.dong)
        self.con_lai=self.tong_tien
        self.saved=dict(self)

@ca('APP gửi ngay: FIN được ghi tại insert, người thường và nháp không được ghi')
def _tao():
    for vai,gui,state,fin in [({'AP Kiểm soát (FIN)'},1,hs.TT_CHO_GD,True),
            ({'AP Officer'},1,hs.TT_CHO_FIN,False),
            ({'AP Kiểm soát (FIN)'},0,hs.TT_NHAP,False)]:
        doc=Doc(flags=frappe._dict(),dong=[])
        with ExitStack() as st:
            for ten in ['_kiem','_chan_hoa_don_trung','_soi_phieu_noi_bo','_chan_thieu_chung_tu','_gan_tep_ve_ho_so','_khoa_phieu_noi_bo']:
                st.enter_context(patch.object(hs,ten))
            for ten,val in [('_vai',vai),('_tep_hop_le',[]),('_sinh_ma','APP-TEST'),('_email_ncc',''),('_tk_nhan',{}),('_dat_tk_nhan','BANK-TEST')]:
                st.enter_context(patch.object(hs,ten,return_value=val))
            st.enter_context(patch.object(frappe,'new_doc',return_value=doc,create=True))
            st.enter_context(patch.object(frappe.db,'exists',return_value=True))
            st.enter_context(patch.object(frappe.db,'get_value',return_value='Người thử'))
            st.enter_context(patch.object(frappe.db,'commit'))
            hs.tao_hoan_ung(nguoi_ung='TEST',dong=[dict(noi_dung='Chi thử',so_tien=100)],gui_luon=gui,tk_hoan='BANK-TEST')
        la('trạng thái lưu',doc.saved['trang_thai'],state)
        la('dấu FIN lưu',bool(doc.saved.get('fin_boi')),fin)
        la('thời gian FIN lưu',bool(doc.saved.get('fin_luc')),fin)
