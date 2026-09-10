"""#225: tiền dòng VND và payload đọc lại đúng số đã lưu, không đọc Settings thuế."""
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_FLOOR


def so(x):
    d=Decimal(str(x or 0))
    if not d.is_finite(): raise ValueError('Số tiền không hữu hạn.')
    return d


def dong(x):
    return int(so(x).quantize(Decimal('1'), rounding=ROUND_HALF_EVEN))


def phan_bo(trong_so, tong):
    """Phần dư chia theo phần lẻ lớn nhất; hoà thì giữ thứ tự dòng."""
    ws=[so(x) for x in trong_so]; t=int(tong)
    if any(w<0 for w in ws) or t<0: raise ValueError('Không phân bổ số tiền âm.')
    if not sum(ws):
        if t: raise ValueError('Không có giá trị dòng để phân bổ.')
        return [0]*len(ws)
    q=[w*t/sum(ws) for w in ws]
    a=[int(x.to_integral_value(rounding=ROUND_FLOOR)) for x in q]
    for i in sorted(range(len(q)),key=lambda i:(-(q[i]-a[i]),i))[:t-sum(a)]: a[i]+=1
    return a


def tinh_dong(gia, thue_suat, gom_thue, giam=0, giam_tren='Grand Total'):
    """Giá dòng đã qua chiết khấu riêng; chiết khấu đầu phiếu chỉ tính một lần."""
    rates=[so(r) for r in thue_suat]
    if len(gia)!=len(rates) or any(r not in (0,5,8,10) for r in rates):
        raise ValueError('Luồng VND này cần thuế suất từng dòng 0, 5, 8 hoặc 10%.')
    a=[dong(x) for x in gia]
    if any(x<0 for x in a): raise ValueError('Luồng VND này không dùng dòng âm.')
    net=[dong(so(g)/(1+r/100)) for g,r in zip(a,rates)] if gom_thue else a
    vat=[g-n for g,n in zip(a,net)] if gom_thue else [dong(so(n)*r/100) for n,r in zip(net,rates)]
    gross=[n+v for n,v in zip(net,vat)]
    discount=dong(giam)
    if discount:
        if discount<0: raise ValueError('Chiết khấu không được âm.')
        if giam_tren=='Net Total':
            net=phan_bo(net,sum(net)-discount)
            vat=[dong(so(n)*r/100) for n,r in zip(net,rates)]
            gross=[n+v for n,v in zip(net,vat)]
        elif giam_tren=='Grand Total':
            gross=phan_bo(gross,sum(gross)-discount)
            net=[dong(so(g)/(1+r/100)) for g,r in zip(gross,rates)]
            vat=[g-n for g,n in zip(gross,net)]
        else: raise ValueError('Chưa xác định cơ sở chiết khấu.')
    return [{'net':n,'vat':v,'gross':g,'rate':float(r)} for n,v,g,r in zip(net,vat,gross,rates)]


def doc_dong(si):
    """Đọc thuế theo item_row/tax_row, không gộp các dòng trùng mã món."""
    items=si.get('items') or []; taxes=si.get('taxes') or []
    if len(taxes)!=1: raise ValueError('Phiếu VND cần đúng một dòng tài khoản VAT.')
    tax=taxes[0]; ds=si.get('_item_wise_tax_details') or si.get('item_wise_tax_details') or []
    rows={}
    for d in ds:
        item=d.get('item')
        key=item.get('idx') if item else next((x.get('idx') for x in items if x.get('name')==d.get('item_row')),None)
        tax_obj=d.get('tax')
        if (tax_obj and tax_obj.get('idx')!=tax.get('idx')) or (not tax_obj and d.get('tax_row')!=tax.get('name')):
            raise ValueError('Chi tiết VAT không trỏ đúng dòng thuế.')
        if key is None or key in rows: raise ValueError('Chi tiết VAT thiếu hoặc trùng dòng hàng.')
        rows[key]=d
    if len(rows) != len(items): raise ValueError('Chi tiết VAT không cùng số dòng hàng.')
    ra=[]
    for it in items:
        d=rows.get(it.get('idx'))
        if d is None: raise ValueError('Chưa có chi tiết VAT đã lưu của từng dòng.')
        n,v,r=so(it.get('net_amount')),so(d.get('amount')),so(d.get('rate'))
        if n!=dong(n) or v!=dong(v) or r not in (0,5,8,10): raise ValueError('Số tiền/thuế suất dòng chưa theo chuẩn VND.')
        ra.append({'net':int(n),'vat':int(v),'gross':int(n+v),'rate':float(r)})
    if (sum(x['net'] for x in ra)!=so(si.get('net_total'))
        or sum(x['vat'] for x in ra)!=so(si.get('total_taxes_and_charges'))
        or sum(x['vat'] for x in ra)!=so(tax.get('tax_amount_after_discount_amount'))
        or sum(x['gross'] for x in ra)!=so(si.get('grand_total'))
        or so(si.get('rounding_adjustment'))
        or so(si.get('base_rounding_adjustment'))):
        raise ValueError('SI, chi tiết VAT và tổng chưa khớp; chưa gửi M-Invoice.')
    return ra


def dong_len_hoa_don(items, ra):
    """Cặp (dòng SI, tiền đã lưu) của những dòng ĐƯỢC đưa lên tờ hoá đơn.

    #266 (09/09/2026): kịch bản phát hành trên site bỏ dòng có thành tiền 0
    (quy tắc ghi ngay đầu kịch bản: "dòng hàng có thành tiền = 0 thì KHÔNG
    đưa lên hoá đơn"), còn bản v460 của hàm này lại đòi payload có ĐỦ số
    dòng SI. Đơn nào kèm một món 0 đồng (túi, nến, hàng tặng kèm) là bị
    chặn "Payload không cùng số dòng SI" ngay lúc ghi sổ: 59 đơn Sales
    ngày 09/09 nằm nháp cả đêm. Nay đối chiếu đúng tập dòng kịch bản gửi.
    """
    return [(it, x) for it, x in zip(items, ra) if x['gross'] > 0]


def chuan_tien(si, dd):
    if not si.get('vgb_thue_vnd'): return
    ra=doc_dong(si); items=si.get('items') or []
    sent=[d for nhom in dd.get('details') or [] for d in nhom.get('data') or []]
    cap=dong_len_hoa_don(items, ra)
    if len(sent)!=len(cap): raise ValueError('Payload không cùng số dòng có tiền của SI.')
    for d,(it,x) in zip(sent,cap):
        if d.get('inv_itemCode')!=it.get('item_code'):
            raise ValueError('Payload không đúng thứ tự dòng SI.')
        # Mã hàng gộp (ma_hang_gop bên cài đặt m-invoice, ví dụ phí dịch vụ)
        # kịch bản gửi số lượng 1 dù dòng SI ghi nhiều hơn; ngoài ca đó số
        # lượng phải khớp từng dòng.
        sl=so(d.get('inv_quantity'))
        if sl!=so(it.get('qty')) and sl!=1:
            raise ValueError('Payload không đúng số lượng dòng SI.')
        # ma_thue phải là SỐ NGUYÊN: m-invoice từ chối "Mã thuế suất= [8.0]"
        # (mã 9999, 116 tờ TCV đêm 09/09/2026 giữ đối chiếu vì đúng lỗi này).
        d.update(inv_TotalAmountWithoutVat=x['net'],inv_vatAmount=x['vat'],inv_TotalAmount=x['gross'],ma_thue=int(x['rate']),
            inv_unitPrice=float(so(x['net'])/sl) if sl else 0,
            inv_discountPercentage=0,inv_discountAmount=0)
    dd.update(inv_TotalAmountWithoutVat=sum(x['net'] for x in ra),inv_vatAmount=sum(x['vat'] for x in ra),
        inv_TotalAmount=sum(x['gross'] for x in ra),inv_discountAmount=0)


TRUONG={'Sales Invoice':[{'fieldname':'vgb_thue_vnd','label':'Tính VAT từng dòng VND',
    'fieldtype':'Check','read_only':1,'hidden':1,'no_copy':1,'insert_after':'taxes_and_charges'}]}
