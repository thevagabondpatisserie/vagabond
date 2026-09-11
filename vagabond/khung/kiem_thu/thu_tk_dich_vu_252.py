"""Tài khoản được chọn phải đi xuống dòng, dù tổng tiền không cần dựng lại."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from vagabond.khung.kiem_thu.nen import ca, la


class Phieu(dict):
    __getattr__ = dict.get
    def __setattr__(self, ten, gia_tri):
        self[ten] = gia_tri
    def set_against_expense_account(self):
        self['da_cap_nhat_header'] = True


@ca('#252 tài khoản dịch vụ: áp dụng dòng không kho, giữ dòng PNK và không đổi tiền')
def _tai_khoan():
    p = Path(__file__).resolve().parents[2] / 'mua_dich_vu.py'
    cay = ast.parse(p.read_text())
    ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == 'gan_tai_khoan_chi_phi')
    da_kiem = []
    core = SimpleNamespace(validate_account_head=lambda *a: da_kiem.append(a))
    env = dict(cint=lambda n: int(n or 0), LOAI_DICH_VU='Mua dịch vụ',
               frappe=SimpleNamespace(db=SimpleNamespace(get_value=lambda dt, ma, f: ma == 'HANG_KHO')))
    exec(compile(ast.Module(body=[ham], type_ignores=[]), str(p), 'exec'), env)
    dong = [Phieu(idx=i+1, item_code=ma, expense_account='632', amount=100,
                  purchase_receipt='PNK-1' if i == 3 else None)
            for i, ma in enumerate((None, 'DICH_VU', 'HANG_KHO', 'DICH_VU'))]
    doc = Phieu(docstatus=0, company='TV', vgb_loai_chung_tu='Mua dịch vụ', vgb_tk_chi_phi='64183', items=dong)
    with patch.dict(sys.modules, {'erpnext.controllers.accounts_controller': core}):
        env[ham.name](doc, 'validate')
        la('đúng phạm vi kế toán', [d.expense_account for d in dong], ['64183', '64183', '632', '632'])
        la('tiền giữ nguyên', [d.amount for d in dong], [100]*4)
        la('dùng kiểm lõi đúng công ty', da_kiem, [(1, '64183', 'TV', 'Expense'), (2, '64183', 'TV', 'Expense')])
        doc.vgb_tk_chi_phi = '6277'; env[ham.name](doc, 'before_submit')
        la('đổi lựa chọn cũng áp xuống', [d.expense_account for d in dong][:2], ['6277', '6277'])
        doc.vgb_loai_chung_tu = 'Mua hàng'; doc.vgb_tk_chi_phi = '6418'; env[ham.name](doc)
        la('không áp khi là mua hàng', dong[0].expense_account, '6277')
        doc.vgb_loai_chung_tu = 'Mua dịch vụ'; doc.docstatus = 2; env[ham.name](doc)
        la('không sửa phiếu đã hủy', dong[0].expense_account, '6277')
