"""#262: số dư có nghĩa, không bù bằng cách làm tròn hoặc bỏ công nợ đầu kỳ."""
from vagabond import can_tru_san as ct
from vagabond.khung.kiem_thu.nen import ca,la,dung

@ca('#262 khop, du No chuyen ky, du Co va le vai nghin')
def _du():
    la('khớp',ct.ket_qua(0,10000000,8000000,2000000)['du'],0)
    la('giữ đầu kỳ',ct.ket_qua(100000,10000000,8000000,2000000)['du'],100000)
    la('dư Có',ct.ket_qua(0,10000000,8100000,2000000)['trang_thai'],'Cần kiểm tra dư Có')
    la('lệch nhỏ vẫn còn',ct.ket_qua(0,10000000,7998000,2000000)['du'],2000)

@ca('#262 phi gom VAT khong trung chung tu, khong so am hoac NaN')
def _phi():
    la('phí gồm VAT',ct.tong_dong([{'hoa_don':'PI1','so_tien':108000},{'hoa_don':'PI2','so_tien':22000}]),130000)
    for ds in ([],[{'hoa_don':'PI1','so_tien':1}]*2,*[[{'hoa_don':'PI1','so_tien':v}] for v in ('',0,-1,1.5,'NaN','Infinity')]):
        try: ct.tong_dong(ds)
        except ValueError: continue
        dung('phải từ chối số/chứng từ không hợp lệ',False)

@ca('#262 scheduler không tự chạy lại phiếu cần kế toán kiểm')
def _lich_cho():
    from unittest.mock import patch
    def doc(dt, filters, **kwargs):
        la('chỉ phiếu đã duyệt',filters['docstatus'],1)
        la('chỉ trạng thái tự chờ',filters['trang_thai'],['in',['Chờ duyệt đối soát','Chờ đối soát']])
        return []
    with patch.object(ct.frappe,'get_all',side_effect=doc):
        ct.xep_hang_cho()
