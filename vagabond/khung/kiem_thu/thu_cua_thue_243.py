"""#243: canh cửa nạp mẫu máy chủ, không lấy mock làm chứng minh GL/core."""
import ast
from pathlib import Path
from types import SimpleNamespace, ModuleType
from unittest.mock import patch
from vagabond.khung.kiem_thu.nen import ca, la, dung


class To(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    def is_new(self): return True
    def set(self, k, v): self[k] = v
    def extend(self, k, v): self[k].extend(v)


def _goi(bang=None, mau='Mau', ds=None, gom=1, cong_ty='CT', tat=0, nguon='GrabFood', item_tk=None):
    p=Path(__file__).resolve().parents[2]/'hoa_don_thue_vnd.py'
    cay=ast.parse(p.read_text())
    ham=next(n for n in cay.body if isinstance(n,ast.FunctionDef) and n.name=='nap_mau_thue')
    vat=dict(charge_type='On Net Total',account_head='33311',rate=8,included_in_print_rate=gom)
    def nem(s): raise ValueError(s)
    def doc(dt,ten):
        return To(company=cong_ty,disabled=tat) if dt.startswith('Sales') else To(taxes=[To(tax_type=item_tk)])
    f=SimpleNamespace(throw=nem,get_all=lambda *a,**kw: ds if ds is not None else ['Mau'],get_cached_doc=doc)
    ns={'frappe':f}
    exec(compile(ast.Module(body=[ham],type_ignores=[]),str(p),'exec'),ns)
    d=To(docstatus=0,currency='VND',company='CT',taxes=list(bang or []),taxes_and_charges=mau,custom_nguon=nguon)
    object.__setattr__(d,'items',[To(idx=1,item_code='BANH',item_tax_template='IT' if item_tk else None)])
    mod=ModuleType('erpnext.controllers.accounts_controller')
    mod.get_taxes_and_charges=lambda *a:[vat]
    with patch.dict('sys.modules',{'erpnext.controllers.accounts_controller':mod}): ns['nap_mau_thue'](d)
    return d


@ca('#243: máy chủ nạp đủ bảng khi có tên mẫu nhưng taxes trống')
def _co_ten():
    d=_goi()
    la('một dòng',len(d.taxes),1)
    la('giá gồm VAT',d.taxes[0]['included_in_print_rate'],1)


@ca('#243: app trống tên và bảng nhận mẫu mặc định')
def _mac_dinh():
    d=_goi(mau=None)
    la('nạp tên mẫu',d.taxes_and_charges,'Mau')
    la('nạp thuế',d.taxes[0]['rate'],8)


@ca('#243: dòng tự sinh ngoài giá được thay bằng mẫu gồm giá')
def _tu_sinh():
    d=_goi([To(set_by_item_tax_template=1,rate=0,included_in_print_rate=0)],mau=None)
    la('gồm VAT',d.taxes[0]['included_in_print_rate'],1)
    from vagabond.thue_vnd import tinh_dong
    la('bill 220.000 không thành 239.000',sum(x['gross'] for x in tinh_dong([150000,70000],[8,10],True)),220000)


@ca('#243: thiếu hoặc trùng mẫu mặc định phải báo, không đoán 8%')
def _thieu():
    for ds in ([],['A','B']):
        try: _goi(mau=None,ds=ds)
        except ValueError as e: dung('chỉ bước sửa', 'mẫu thuế' in str(e))
        else: dung('phải chặn',False)


@ca('#243: mẫu khác công ty, tắt, chưa gồm giá hoặc sai tài khoản đều chặn')
def _sai():
    for kw in (dict(cong_ty='KHAC'),dict(tat=1),dict(gom=0),dict(item_tk='33312')):
        try: _goi(**kw)
        except ValueError: pass
        else: dung('phải chặn '+str(kw),False)


@ca('#243: bảng thuế nhập tay được giữ nguyên không bị nạp đè')
def _giu():
    bang=[To(charge_type='Actual',tax_amount=50)]
    la('giữ phí thật',_goi(bang).taxes,bang)


@ca('#243: SI máy chủ không có nguồn app vẫn chặn khi thiếu chính sách thuế')
def _khong_nguon():
    try: _goi(mau=None,ds=[],nguon=None)
    except ValueError as e: dung('hướng dẫn chọn mẫu','chọn mẫu' in str(e))
    else: dung('không coi thiếu cấu hình là VAT 0',False)
