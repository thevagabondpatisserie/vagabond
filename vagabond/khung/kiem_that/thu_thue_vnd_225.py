"""#225: lưu, ghi sổ, đọc lại SI và GL thật trước khi so payload từng dòng.

Chỉ chứng từ mới trong điểm lưu của nen.py; không gửi M-Invoice, không
chạm hoá đơn cũ. Thiếu danh mục hoặc core từ chối thì đỏ, không vá tay.
"""
import frappe
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, la, dung, cong_ty
from vagabond.khung.kiem_that.thu_hang_tang_227 import _hoa_don, _gl
from vagabond.hang_tang_so_cai import tai_khoan
from vagabond.thue_vnd import doc_dong, chuan_tien


def _mau(tk, ts):
    mau=frappe.new_doc('Item Tax Template')
    mau.title='KIEM VAT '+frappe.generate_hash(length=8)
    mau.company=cong_ty()
    mau.append('taxes', {'tax_type':tk,'tax_rate':ts})
    mau.insert(ignore_permissions=True)
    nen._DA_TAO.append((mau.doctype,mau.name))
    return mau.name


def _dung(gia, ts, gom=True, giam=0, nen_giam='Grand Total', tang=False):
    hd=_hoa_don(tang)
    tk=tai_khoan(hd.company,'33311','Liability')
    hd.set('taxes', [])
    hd.append('taxes', {'charge_type':'On Net Total','account_head':tk,
        'rate':8,'description':'VAT kiểm #225','included_in_print_rate':int(gom)})
    mon=hd.items[0].as_dict()
    hd.set('items',[])
    for g,t in zip(gia,ts):
        d={k:v for k,v in mon.items() if k not in ('name','parent','parenttype','parentfield','idx')}
        d.update(rate=g,qty=1,price_list_rate=g,item_tax_template=_mau(tk,t))
        hd.append('items',d)
    hd.apply_discount_on=nen_giam
    hd.discount_amount=giam
    hd.save(ignore_permissions=True)
    hd.reload()
    la('máy chủ áp chính sách',hd.vgb_thue_vnd,1)
    return hd,tk


def _doi_chieu(hd,tk):
    hd.flags.ignore_permissions=True
    hd.submit()
    hd.reload()
    ds=doc_dong(hd)
    goi={'details':[{'data':[{'inv_itemCode':d.item_code,'inv_quantity':d.qty} for d in hd.items]}]}
    from vagabond.minvoice_an_toan import chuan_goi
    goi=chuan_goi(hd,{'data':[goi]})['data'][0]
    la('payload bằng SI',goi['inv_TotalAmount'],hd.grand_total)
    la('VAT bằng GL',sum(d.credit-d.debit for d in _gl(hd) if d.account==tk),sum(d['vat'] for d in ds))
    la('không bù lẻ',hd.rounding_adjustment,0)
    la('sổ cân',round(sum(d.debit-d.credit for d in _gl(hd)),6),0)
    return ds


@ca('#225 VND: 10.420.000 qua lưu và ghi sổ không sinh 15 xu')
def _le():
    hd,tk=_dung([10420000],[8])
    ds=_doi_chieu(hd,tk)
    la('net chính xác',ds[0]['net'],9648148)
    la('VAT chính xác',ds[0]['vat'],771852)


@ca('#225 VND: trùng mã 8/10 qua sửa giá, thêm dòng 0 và ghi sổ')
def _hon_hop():
    hd,tk=_dung([108000,110000],[8,10])
    hd.items[0].rate=216000
    d=hd.items[0].as_dict()
    for k in ('name','parent','parenttype','parentfield','idx'):d.pop(k,None)
    d.update(rate=50000,qty=1,item_tax_template=_mau(tk,0))
    hd.append('items',d)
    hd.save(ignore_permissions=True)
    hd.reload()
    ds=_doi_chieu(hd,tk)
    la('giữ thuế từng dòng',[d['rate'] for d in ds],[8,10,0])
    la('đúng VAT',[d['vat'] for d in ds],[16000,10000,0])


@ca('#225 VND: năm dòng rất nhỏ không lỗi tổng chi tiết thuế')
def _nho():
    hd,tk=_dung([6]*5,[8]*5,False)
    ds=_doi_chieu(hd,tk)
    la('VAT không cộng dồn lẻ',sum(d['vat'] for d in ds),0)


@ca('#225 VND: chiết khấu trên net và gross qua ghi sổ')
def _giam():
    for nen_giam in ('Net Total','Grand Total'):
        hd,tk=_dung([108000,110000],[8,10],True,777,nen_giam)
        ds=_doi_chieu(hd,tk)
        khoa='net' if nen_giam=='Net Total' else 'gross'
        la('giảm đúng',sum(d[khoa] for d in ds),(200000 if khoa=='net' else 218000)-777)


@ca('#225 VND: chiết khấu mỗi đơn vị 0,25 không bị làm tròn mất')
def _don_gia():
    hd,tk=_dung([100],[8],False)
    hd.items[0].qty=3
    hd.items[0].price_list_rate=100
    hd.items[0].rate=99.75
    hd.items[0].discount_amount=0.25
    hd.items[0].discount_percentage=0
    hd.save(ignore_permissions=True)
    hd.reload()
    la('giữ giá đã thoả thuận',hd.items[0].rate,99.75)
    la('giữ giảm mỗi đơn vị',hd.items[0].discount_amount,0.25)
    _doi_chieu(hd,tk)


@ca('#225 VND: hàng tặng thuế hỗn hợp ghi đúng VAT đã lưu')
def _tang():
    from vagabond import hang_tang
    hd,tk=_dung([108000,110000],[8,10],tang=True)
    # Sửa món làm mất duyệt; duyệt lại đúng nội dung vừa lưu trước submit.
    hang_tang.duyet(hd.name,'Ca kiểm thuế hỗn hợp trong điểm lưu')
    hd.reload()
    ds=_doi_chieu(hd,tk)
    la('VAT tặng',hd.vgb_tang_tien_thue,sum(d['vat'] for d in ds))
    la('không còn nợ',hd.outstanding_amount,0)
    la('chỉ hai dòng GL VAT',len(_gl(hd)),2)


@ca('#225 VND: cache số lẻ không lọt sang lần tính khác trên cùng object')
def _cache():
    hd,tk=_dung([108000],[8])
    truoc=hd.items[0].precision('net_amount')
    hd.calculate_taxes_and_totals()
    la('trả cache chuẩn sau tính',hd.items[0].precision('net_amount'),truoc)
    hd.set('taxes',[])
    hd.items[0].rate=99.75
    hd.calculate_taxes_and_totals()
    la('trả về core khi không có VAT',hd.vgb_thue_vnd,0)
    la('core giữ số lẻ',hd.items[0].net_amount,99.75)
