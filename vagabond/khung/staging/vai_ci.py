"""Tai khoan tong hop cho kiem quyen HTTP; khong sao chep nguoi dung site."""
import json
import os
from pathlib import Path


def tao():
    import frappe
    from frappe.utils.password import update_password
    from vagabond.khung.staging.van_don_ci import khoa

    khoa()
    frappe.set_user('Administrator')
    profiles = {
        'sales': ['Sales User'],
        'kho': ['Stock User'],
        'bep': ['Manufacturing User'],
        'ke_toan': ['Accounts User'],
    }
    out = {}
    for name, roles in profiles.items():
        email = 'thu257-' + name + '@example.invalid'
        if frappe.db.exists('User', email):
            raise RuntimeError('Tai khoan fixture da ton tai: ' + email)
        for role in roles:
            if not frappe.db.exists('Role', role):
                raise RuntimeError('Thieu vai core: ' + role)
        user = frappe.get_doc({
            'doctype': 'User', 'email': email, 'first_name': 'THU257 ' + name,
            'enabled': 1, 'user_type': 'System User', 'send_welcome_email': 0,
            'language': 'en', 'roles': [{'role': role} for role in roles],
        }).insert()
        update_password(user.name, 'bench-only-roles-257')
        actual = set(frappe.get_roles(user.name))
        if not set(roles) <= actual or actual - set(roles) - {'All', 'Desk User', 'Guest'}:
            raise RuntimeError('Vai fixture khong dung pham vi: ' + name)
        out[name] = {'user': user.name, 'roles': sorted(actual)}
    frappe.db.commit()
    (Path(os.environ['VGB_ARTIFACTS']) / 'vai-fixture.json').write_text(json.dumps(out))
