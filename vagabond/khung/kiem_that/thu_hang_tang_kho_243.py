"""#243: BOM -> sản xuất có lô -> SI tặng -> SLE/GL -> huỷ, trong savepoint.

Không xuất HĐĐT. Lỗi core phải làm ca đỏ. Rollback cục bộ của controller
được kiểm TRƯỚC rollback cuối ca, nên không che lỗi bằng khung thử.
"""
import json
import frappe
from unittest.mock import patch
from frappe.utils import flt
from vagabond import hang_tang, diem_ban
from vagabond.khung.kiem_that import nen
from vagabond.khung.kiem_that.nen import ca, cong_ty, la, dung
from vagabond.khung.kiem_that.thu_ma_cap_so import _mon_thu, _bom_thu, _lo_thu
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen as _nen_thue
from vagabond.khung.kiem_that.thu_hang_tang_227 import _gl


def _luu(d):
    d.insert(ignore_permissions=True); nen._DA_TAO.append((d.doctype,d.name))
    return d


def _nen():
    ct,tk,mau=_nen_thue()
    for truong, gia_tri in (('enable_serial_and_batch_no_for_item',1), ('use_serial_batch_fields',1), ('allow_negative_stock',0)):
        frappe.db.set_single_value('Stock Settings',truong,gia_tri)
    frappe.clear_document_cache('Stock Settings')
    tai=frappe.db.get_value('Account',{'company':ct,'account_number':'1551','account_type':'Stock','is_group':0,'disabled':0},'name')
    if not tai:
        tai=_luu(frappe.get_doc(dict(doctype='Account',account_name='Thành phẩm kiểm #243',account_number='1551',
            company=ct,parent_account=frappe.db.get_value('Account',{'company':ct,'root_type':'Asset','is_group':1},'name'),
            account_type='Stock',account_currency='VND',is_group=0))).name
    kho=_luu(frappe.get_doc(dict(doctype='Warehouse',warehouse_name='KT243-'+frappe.generate_hash(length=9),company=ct,account=tai))).name
    cfg=diem_ban.ds()
    for d in cfg:
        if not d['quay']: d['kho_tang']=kho
    frappe.db.set_single_value('Vagabond Settings',diem_ban.TRUONG,json.dumps(cfg,ensure_ascii=False))
    nvl=_mon_thu('KT243-NVL-'+frappe.generate_hash(length=8))
    tp=_mon_thu('KT243-TP-'+frappe.generate_hash(length=8),theo_lo=1)
    from erpnext.stock.doctype.stock_entry.stock_entry_utils import make_stock_entry
    ph=make_stock_entry(item_code=nvl,qty=10,company=ct,to_warehouse=kho,rate=12000,do_not_save=True)
    _luu(ph);ph.submit()
    bom=_bom_thu(tp,nvl,ct)
    wo=_luu(frappe.get_doc(dict(doctype='Work Order',company=ct,production_item=tp,bom_no=bom.name,
        qty=5,skip_transfer=1,source_warehouse=kho,wip_warehouse=kho,fg_warehouse=kho,use_multi_level_bom=1)))
    wo.submit()
    from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry as lam
    sx=frappe.get_doc(lam(wo.name,'Manufacture',qty=5))
    lo=_lo_thu(tp)
    for d in sx.items:
        if d.item_code==tp: d.batch_no=lo.name;d.use_serial_batch_fields=1
    _luu(sx);sx.submit()
    hd=frappe.get_doc(dict(doctype='Sales Invoice',company=ct,currency='VND',conversion_rate=1,
        customer=frappe.db.get_value('Customer',{'disabled':0,'is_internal_customer':0},'name'),
        taxes_and_charges=mau.name,vgb_pt_thanh_toan='Hàng tặng',vgb_tang_loai='marketing',
        vgb_tang_ly_do='Ca kiểm giá vốn từ mẻ sản xuất #243',items=[dict(item_code=tp,qty=2,rate=108000)]))
    _luu(hd);hang_tang.duyet(hd.name,'Ca kiểm trong điểm lưu, không giao bánh thật')
    hd.reload();hd.flags.ignore_permissions=True
    return hd,kho,lo.name


def _sle(hd):
    return frappe.get_all('Stock Ledger Entry',filters={'voucher_type':hd.doctype,'voucher_no':hd.name,'is_cancelled':0},
        fields=['warehouse','actual_qty','stock_value_difference','serial_and_batch_bundle'])


@ca('#243 kho thật: sản xuất có lô rồi tặng, giá vốn khớp SLE và huỷ đảo đủ')
def _xuyen_luong():
    hd,kho,lo=_nen();hd.submit();hd.reload()
    la('tự bật xuất',hd.update_stock,1);la('không chờ giá vốn',hd.vgb_tang_cho_gia_von,0)
    sle=_sle(hd);la('xuất đúng lượng',sum(d.actual_qty for d in sle),-2)
    dung('đúng kho',all(d.warehouse==kho for d in sle))
    tk=frappe.db.get_value('Account',{'company':hd.company,'account_number':'64181'},'name')
    gia=-sum(d.stock_value_difference for d in sle)
    dung('giá vốn thực dương',gia>0)
    la('64181 từ sổ kho',round(sum(d.debit-d.credit for d in _gl(hd) if d.account==tk),2),round(gia,2))
    dung('không sinh Customer GL',all(not d.party_type for d in _gl(hd)))
    la('GL cân',round(sum(d.debit-d.credit for d in _gl(hd)),2),0)
    la('không nợ',hd.outstanding_amount,0)
    # Gọi lại chính object đã submit không được xuất thêm.
    try: hd.submit()
    except frappe.ValidationError: pass
    la('gọi lại không xuất hai lần',sum(d.actual_qty for d in _sle(hd)),-2)
    hd.reload();hd.flags.ignore_permissions=True;hd.cancel()
    la('huỷ đảo đủ giá vốn',round(sum(d.debit-d.credit for d in _gl(hd) if d.account==tk),2),0)


@ca('#243 kho thật: lỗi sau GL hoàn nguyên ngay cả khi caller bắt lỗi')
def _loi_giua_chung():
    hd,kho,lo=_nen()
    lop=type(hd);goc=lop.make_gl_entries
    doi_truoc=list(frappe.db.after_commit._functions)
    def hong(self,*a,**kw):
        goc(self,*a,**kw)
        frappe.db.after_commit.add(lambda: None)
        raise RuntimeError('KT243 lỗi sau ghi GL')
    with patch.object(lop,'make_gl_entries',hong):
        try: hd.submit()
        except RuntimeError as e: dung('lỗi đúng điểm', 'sau ghi GL' in str(e))
        else: dung('phải ném lỗi',False)
    # Chưa lùi savepoint nen.py: nếu controller không nguyên khối ca này đỏ.
    la('DB còn nháp',frappe.db.get_value('Sales Invoice',hd.name,'docstatus'),0)
    la('không giữ job sau lỗi',list(frappe.db.after_commit._functions),doi_truoc)
    la('không SLE dở',len(_sle(hd)),0);la('không GL dở',len(_gl(hd)),0)
    hd.reload();hd.flags.ignore_permissions=True;hd.submit()
    la('thử lại chỉ xuất một lần',sum(d.actual_qty for d in _sle(hd)),-2)


@ca('#243 kho thật: thiếu tồn dù cho phép âm vẫn chặn sạch')
def _thieu_ton():
    hd,kho,lo=_nen()
    frappe.db.set_single_value('Stock Settings','allow_negative_stock',1)
    frappe.clear_document_cache('Stock Settings')
    hd.items[0].qty=6;hd.save(ignore_permissions=True)
    hang_tang.duyet(hd.name,'Kiểm thiếu tồn, không giao thật');hd.reload();hd.flags.ignore_permissions=True
    try: hd.submit()
    except frappe.ValidationError as e: dung('chỉ đúng thiếu hàng',kho in str(e))
    else: dung('phải chặn',False)
    la('không xuất',len(_sle(hd)),0);la('không hạch toán',len(_gl(hd)),0)
    la('vẫn nháp',frappe.db.get_value('Sales Invoice',hd.name,'docstatus'),0)


@ca('#243 kho thật: sai lô không âm thầm đổi sang lô khác')
def _sai_lo():
    hd,kho,lo=_nen()
    sai=_lo_thu(_mon_thu('KT243-KHAC-'+frappe.generate_hash(length=8),theo_lo=1))
    for pt in ('Hàng tặng', 'Tiền mặt'):
        for thao_tac in ('save', 'submit'):
            hd.reload();hd.flags.ignore_permissions=True
            hd.vgb_pt_thanh_toan=pt
            hd.items[0].batch_no=sai.name;hd.items[0].use_serial_batch_fields=1
            try: getattr(hd,thao_tac)()
            except frappe.ValidationError as e:
                dung('báo đúng lô và món cần sửa',sai.name in str(e) and 'Chọn lại đúng lô' in str(e))
            else: dung('phải chặn lô sai món '+pt+' '+thao_tac,False)
            la('không SLE',len(_sle(hd)),0);la('không GL',len(_gl(hd)),0)
            la('vẫn nháp',frappe.db.get_value('Sales Invoice',hd.name,'docstatus'),0)


@ca('#243 kho thật: đổi tặng sang bán thường không giữ cờ xuất/64181')
def _doi_loai():
    hd,kho,lo=_nen()
    hd.vgb_pt_thanh_toan='Tiền mặt';hd.save(ignore_permissions=True);hd.reload()
    la('trở lại luồng bán thường',hd.update_stock,0)
    la('gỡ kho tặng',hd.vgb_tang_kho,None)
    dung('gỡ 64181',all(not d.expense_account or frappe.get_cached_value('Account',d.expense_account,'account_number')!='64181' for d in hd.items))


@ca('#243 kho thật: phiếu xuất tay tham chiếu SI mới bị chặn tại Document')
def _chan_trung():
    hd,kho,lo=_nen();hd.submit();hd.reload()
    d=frappe.get_doc(dict(doctype='Stock Entry',company=hd.company,stock_entry_type='Material Issue',purpose='Material Issue',
        vgb_hoa_don_tang=hd.name,items=[dict(item_code=hd.items[0].item_code,qty=1,s_warehouse=kho,
        expense_account=hd.items[0].expense_account,batch_no=lo,use_serial_batch_fields=1)]))
    try: d.insert(ignore_permissions=True)
    except frappe.ValidationError as e: dung('chặn đúng xuất lần hai','tự xuất kho' in str(e))
    else:
        nen._DA_TAO.append((d.doctype,d.name));dung('phải chặn insert',False)


@ca('#243 core: insert thẳng docstatus 1 bị chặn trước khi tạo chứng từ')
def _insert_ghi_so():
    hd,kho,lo=_nen()
    moi=frappe.copy_doc(hd);moi.docstatus=1
    truoc=frappe.db.count('Sales Invoice')
    try: moi.insert(ignore_permissions=True)
    except frappe.ValidationError as e: dung('chỉ đúng lưu nháp trước','nháp trước' in str(e))
    else:
        nen._DA_TAO.append((moi.doctype,moi.name));dung('phải chặn',False)
    la('không thêm SI',frappe.db.count('Sales Invoice'),truoc)
