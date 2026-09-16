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

@ca('Quỹ tạm ứng: phân bổ nhiều nguồn, giữ số lẻ và không lấy quá dư')
def _chia():
    from vagabond.tam_ung_app import chia_nguon
    la('hai nguồn', chia_nguon({'A':100, 'B':50},120), {'A':100.0,'B':20.0})
    la('số lẻ', chia_nguon({'A':'0.1','B':'0.2'},'0.3'), {'A':0.1,'B':0.2})
    for x in (0,-1,151,'NaN','Infinity'):
        try:
            chia_nguon({'A':100,'B':50},x)
        except ValueError:
            pass
        else:
            la('phải từ chối số sai',x,'ValueError')

@ca('APP quyết toán: kiểm đúng từng PI, quỹ141, thiếu JE và không trả thêm lần hai')
def _kiem_can():
    from copy import deepcopy
    k={'loai':'PE','hoa_don':{},'tong':0,'can_ung':{'name':'JE-1','company':'CT','tai_khoan':'141','tong':100,
       'hoa_don':{'PI-1':{'tien':100,'supplier':'NCC','account':'331'}}}}
    def dong(tk,no,co,**kw):
        return dict(account=tk,debit_in_account_currency=no,credit_in_account_currency=co,
          debit=no,credit=co,account_currency='VND',exchange_rate=1,**kw)
    b=[dict(name='JE-1',doctype='Journal Entry',company='CT',tong_no=100,dong=[
      dong('331',100,0,party_type='Supplier',party='NCC',reference_type='Purchase Invoice',reference_name='PI-1'),
      dong('141',0,100)])]
    la('đủ',hs._kiem_bo_chung_tu(k,b)['du'],1)
    la('thiếu',hs._kiem_bo_chung_tu(k,[])['du'],0)
    for field,value in [('account','112'),('credit_in_account_currency',101),('exchange_rate',2)]:
        sai=deepcopy(b);sai[0]['dong'][1][field]=value
        la('bắt sai '+field,hs._kiem_bo_chung_tu(k,sai)['du'],0)
    sai=deepcopy(b);sai[0]['dong'][0]['reference_name']='PI-KHAC'
    la('bắt sai hóa đơn',hs._kiem_bo_chung_tu(k,sai)['du'],0)
    la('bắt trả thêm',hs._kiem_bo_chung_tu(k,b+[dict(name='PE-DUP',doctype='Payment Entry')])['du'],0)

@ca('APP cấn đủ: cửa xuất chuyển khoản không đổi 0 thành tổng tiền hồ sơ')
def _khong_xuat_tien_lan_hai():
    d=Doc(name='APP-THU',tong_tien=100,con_lai=0,ten_nhan='Người thử',stk_nhan='SO-THU',nha_cung_cap='NCC')
    with patch.object(hs,'_kiem'), patch.object(frappe,'get_doc',return_value=d), patch.object(hs,'_noi_dung_ck',return_value='THU'):
        try:
            hs.noi_dung_chuyen_khoan('APP-THU')
        except frappe.ValidationError as e:
            la('nói không chuyển thêm', 'không còn tiền phải chuyển' in str(e), True)
        else:
            la('phải dừng xuất lệnh',True,False)
