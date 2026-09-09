"""#225: bắt số lẻ, thuế hỗn hợp, trùng mã và sai liên kết dòng payload."""
from copy import deepcopy
from vagabond.thue_vnd import tinh_dong, chuan_tien, doc_dong
from vagabond.khung.kiem_thu.nen import ca, la, dung


def _phieu():
    ds=tinh_dong([108000,110000], [8,10], True)
    si={'vgb_thue_vnd':1, 'items':[], 'taxes':[{'name':'T','idx':1,'tax_amount_after_discount_amount':18000}],
        'net_total':200000,'total_taxes_and_charges':18000,'grand_total':218000,'item_wise_tax_details':[]}
    for i,d in enumerate(ds,1):
        si['items'].append({'idx':i,'name':str(i),'item_code':'BANH','qty':1,'net_amount':d['net']})
        si['item_wise_tax_details'].append({'item_row':str(i),'tax_row':'T','rate':d['rate'],'amount':d['vat']})
    goi={'details':[{'data':[{'inv_itemCode':'BANH','inv_quantity':1} for _ in ds]}]}
    return si,goi


@ca('#225: 10.420.000 đồng không còn khoản bù 0,15 đồng')
def _le():
    la('net và VAT', tinh_dong([10420000],[8],True),
       [{'net':9648148,'vat':771852,'gross':10420000,'rate':8.0}])


@ca('#225: năm dòng VAT 0,48 không cộng dồn thành VAT 2 đồng')
def _nho():
    ds=tinh_dong([6]*5,[8]*5,False)
    la('VAT từng dòng nguyên đồng',sum(d['vat'] for d in ds),0)
    la('giữ tổng dòng',sum(d['gross'] for d in ds),30)


@ca('#225: giảm đầu phiếu giữ tổng chính xác qua cả hai cơ sở')
def _giam():
    for nen in ('Net Total','Grand Total'):
        for giam in (1,3,777,10000):
            ds=tinh_dong([108000,110000],[8,10],True,giam,nen)
            khoa='net' if nen=='Net Total' else 'gross'
            la('giảm đúng một lần',sum(d[khoa] for d in ds),(200000 if khoa=='net' else 218000)-giam)
            dung('từng dòng cân',all(d['net']+d['vat']==d['gross'] for d in ds))


@ca('#225: hai dòng trùng mã vẫn gửi đúng 8 và 10 phần trăm')
def _hon_hop():
    si,goi=_phieu(); chuan_tien(si,goi)
    la('thuế từng dòng',[d['ma_thue'] for d in goi['details'][0]['data']],[8,10])
    la('VAT tổng',goi['inv_vatAmount'],18000)
    cu=deepcopy(goi); chuan_tien(si,goi);la('gọi lại không đổi',goi,cu)


@ca('#225: 0 phần trăm không bị thay bằng mặc định 8')
def _khong():
    ds=tinh_dong([100,108],[0,8],True)
    la('VAT',[d['vat'] for d in ds],[0,8])


@ca('#225: chi tiết thuế sai dòng hoặc payload sai số lượng phải dừng')
def _sai():
    for loai in ('link','vat','qty'):
        si,goi=_phieu()
        if loai=='link':si['item_wise_tax_details'][0]['item_row']='sai'
        elif loai=='vat':si['item_wise_tax_details'][0]['amount']=8000.15
        else:goi['details'][0]['data'][0]['inv_quantity']=2
        try:chuan_tien(si,goi)
        except ValueError:pass
        else:dung('phải từ chối '+loai,False)


@ca('#225: payload chứng từ cũ không bị tính lại')
def _cu():
    si,goi=_phieu();si['vgb_thue_vnd']=0
    cu=deepcopy(goi);chuan_tien(si,goi);la('giữ nguyên',goi,cu)


@ca('#225: cửa chung xuất tay và xuất rải giữ VAT của đơn tặng hỗn hợp')
def _cua_chung():
    from vagabond.minvoice_an_toan import chuan_goi
    si,goi=_phieu()
    si.update(name='KIEM',vgb_pt_thanh_toan='Hàng tặng',vgb_tang_duyet='Đã duyệt',
              vgb_tang_so_cai=1,vgb_tang_tien_thue=18000,vgb_tang_thue_suat=0)
    ra=chuan_goi(si,{'data':[goi]})['data'][0]
    la('thuế không đọc snapshot một suất',[d['ma_thue'] for d in ra['details'][0]['data']],[8,10])
    la('VAT kế toán',ra['inv_vatAmount'],18000)
    la('không thu tiền',ra['inv_paymentMethodName'],'Hàng tặng không thu tiền')


@ca('#225: trả cache không được tạo thuộc tính None làm core precision nổ')
def _tra_cache():
    import ast
    from pathlib import Path
    from types import SimpleNamespace
    ma=ast.parse((Path(__file__).resolve().parents[2]/'hoa_don_thue_vnd.py').read_text())
    ham=next(d for d in ma.body if isinstance(d,ast.FunctionDef) and d.name=='tinh')
    pham_vi={'deepcopy':deepcopy,'frappe':SimpleNamespace(flags={}),
        'do_chinh_xac':lambda d:setattr(d,'_precision',{'main':{'amount':0}}),
        'ThueVnd':lambda d:None,'doc_dong':lambda d:None}
    exec(compile(ast.Module(body=[ham],type_ignores=[]),'tinh-thuc','exec'),pham_vi)
    for co_cache in (False,True):
        doc=SimpleNamespace(items=[],taxes=[],calculate_commission=lambda:None,calculate_contribution=lambda:None)
        if co_cache:doc._precision={'main':{'amount':2}}
        pham_vi['tinh'](doc)
        if co_cache:la('trả số lẻ cũ',doc._precision,{'main':{'amount':2}})
        else:dung('cache chưa có phải tiếp tục chưa có',not hasattr(doc,'_precision'))
