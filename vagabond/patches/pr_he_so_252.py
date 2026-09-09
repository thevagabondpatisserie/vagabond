"""Lưu trữ đúng guard PR cũ; hook chung đã xử lý nguồn và trả hàng."""
import hashlib
from pathlib import Path
import frappe

TEN = 'PR - Chan he so quy doi sai'
SHA256 = '0025e2a10ee31f568033c0c2d40356e72bda91f748b38cd9045ce8516eba8025'


def ban_cu():
    return Path(__file__).with_name('pr_he_so_252_cu.txt').read_text(encoding='utf-8')


def nhan_dang(doc):
    return (doc.script_type == 'DocType Event'
        and doc.reference_doctype == 'Purchase Receipt'
        and doc.doctype_event == 'Before Validate'
        and hashlib.sha256((doc.script or '').replace('\r\n', '\n').strip().encode()).hexdigest() == SHA256)


def execute():
    if not frappe.db.exists('Server Script', TEN):
        return
    doc = frappe.get_doc('Server Script', TEN)
    if not nhan_dang(doc):
        frappe.throw('Kịch bản PR cũ đã khác bản được rà soát; giữ nguyên và cần kiểm tra trước khi migrate: ' + TEN)
    for event in ('validate', 'before_submit'):
        hooks = frappe.get_hooks('doc_events').get('Purchase Receipt', {}).get(event, [])
        if isinstance(hooks, str):
            hooks = [hooks]
        if 'vagabond.he_so_chung_tu.kiem' not in hooks:
            frappe.throw('Chưa có hàng rào quy cách Purchase Receipt thay thế: ' + event)
    if not doc.disabled:
        doc.disabled = 1
        doc.save(ignore_permissions=True)
