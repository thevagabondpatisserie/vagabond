"""Soạn BOM thật bằng vai bếp phó/bar, không cấp quyền ghi sổ."""
import json
import os
import traceback
from pathlib import Path
import frappe
from vagabond.khung.bench_thu.kho_tang_243 import _mo, _dong, _dung


def chay():
    _mo()
    kq = {'dat': False}
    da_tao = []
    try:
        from vagabond import cong_thuc as ct
        nhom = frappe.db.get_value('Item Group', {'is_group': 0}, 'name')
        dvt = frappe.db.get_value('UOM', {}, 'name')
        for ma in ('CI334-TP', 'CI334-NVL'):
            frappe.get_doc({'doctype': 'Item', 'item_code': ma, 'item_name': ma,
                'item_group': nhom, 'stock_uom': dvt, 'is_stock_item': 1}).insert(ignore_permissions=True)
        for so, vai in enumerate(('Bếp phó', 'Quầy Bar')):
            if not frappe.db.exists('Role', vai):
                frappe.get_doc({'doctype': 'Role', 'role_name': vai}).insert(ignore_permissions=True)
            u = frappe.get_doc({'doctype': 'User', 'email': 'ci334-%s@example.test' % so,
                'first_name': 'CI334', 'enabled': 1, 'send_welcome_email': 0,
                'roles': [{'role': vai}]}).insert(ignore_permissions=True)
            frappe.set_user(u.name)
            r = ct.tao_moi('CI334-TP', 1, dvt, [{'ma': 'CI334-NVL', 'sl': 2, 'dvt': dvt}])
            ten = r['bom_nhap']; da_tao.append(ten)
            ct.sua_nhap(ten, 3, [{'ma': 'CI334-NVL', 'sl': 4, 'dvt': dvt}])
            doc = frappe.get_doc('BOM', ten)
            _dung(doc.docstatus == 0 and doc.quantity == 3 and doc.items[0].qty == 4,
                  vai + ': lưu nháp thật')
            try:
                ct.ghi_so(ten)
            except frappe.ValidationError:
                pass
            else:
                raise AssertionError(vai + ': lọt cửa ghi sổ')
            _dung(frappe.db.get_value('BOM', ten, 'docstatus') == 0, 'Vẫn Nháp sau từ chối')
            ct.bo_nhap(ten)
            _dung(not frappe.db.exists('BOM', ten), 'Bỏ đúng bản Nháp')
            kq[vai] = True
            frappe.set_user('Administrator')
        kq['dat'] = True
    except Exception:
        kq['loi'] = traceback.format_exc()
    finally:
        frappe.db.rollback()
        kq['sach'] = not any(frappe.db.exists('BOM', ten) for ten in da_tao)
        kq['dat'] = bool(kq['dat'] and kq['sach'])
        (Path(os.environ['VGB_ARTIFACTS'])/'cong-thuc-334.json').write_text(
            json.dumps(kq, ensure_ascii=False, indent=2))
        _dong()
    print(json.dumps(kq, ensure_ascii=False), flush=True)
    return kq['dat']


if __name__ == '__main__':
    raise SystemExit(0 if chay() else 1)
