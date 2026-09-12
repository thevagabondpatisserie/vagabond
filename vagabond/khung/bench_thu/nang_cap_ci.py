"""Nền nâng cấp CI từ snapshot Server Script đã biết, không vá tắt mã mới.

Fresh install Frappe đánh dấu patches hiện tại đã xong. Chỉ bench dùng
một lần được bỏ đúng các dấu dưới đây để kiểm lại đường migrate thật.
"""
import os
import frappe
from vagabond import minvoice_kich_ban

PATCHES = (
    'vagabond.patches.minvoice_v482',
    'vagabond.patches.pr_he_so_252',
    'vagabond.patches.minvoice_v454',
    'vagabond.patches.thue_don_mua_v450',
    'vagabond.patches.san_xuat_206',
    'vagabond.patches.mac_dinh_san_xuat_206',
    'vagabond.patches.thue_vnd_v458',
    'vagabond.patches.hang_tang_kho_v458',
    'vagabond.patches.dong_bo_cau_truc #v460',
)


def _khoa():
    if (os.environ.get('GITHUB_ACTIONS') != 'true'
            or frappe.local.site != 'bench-ci.localhost'
            or not frappe.conf.get('vagabond_bench_thu')):
        raise RuntimeError('Chỉ dựng nền nâng cấp trong bench GitHub dùng một lần.')


def chuan_bi():
    _khoa()
    from frappe.utils.password import get_encryption_key
    get_encryption_key()  # Ghi khoá vào site_config, không in hoặc đưa vào artifact.
    from vagabond import minvoice_sau_ghi_so as sau
    frappe.get_doc(dict(doctype='Server Script', name=sau.TEN, script_type='DocType Event',
        reference_doctype='Sales Invoice', doctype_event='After Submit',
        disabled=0, script=sau.ban_goc())).insert(ignore_permissions=True)
    for ten, loai, _cu, _moi in minvoice_kich_ban.BO:
        if frappe.db.exists('Server Script', ten):
            raise RuntimeError('Bench mới không được có sẵn kịch bản: ' + ten)
        frappe.get_doc(dict(doctype='Server Script', name=ten, script_type='API',
            api_method='kiem_ci_' + loai, allow_guest=0, disabled=0,
            script=minvoice_kich_ban.ban_goc(loai))).insert(ignore_permissions=True)
    from vagabond.patches.pr_he_so_252 import TEN, ban_cu
    if frappe.db.exists('Server Script', TEN):
        raise RuntimeError('Bench mới đã có kịch bản PR: ' + TEN)
    frappe.get_doc(dict(doctype='Server Script', name=TEN, script_type='DocType Event',
        reference_doctype='Purchase Receipt', doctype_event='Before Validate',
        disabled=0, script=ban_cu())).insert(ignore_permissions=True)
    for patch in PATCHES:
        frappe.db.delete('Patch Log', {'patch': patch})
    frappe.db.commit()
    return {'kich_ban': 'snapshot 20260907', 'patches_can_chay': list(PATCHES)}


def doi_chieu():
    _khoa()
    from vagabond.thue_vnd import TRUONG as THUE
    from vagabond.hang_tang_kho import TRUONG as KHO
    ds = []
    for bo in (THUE, KHO):
        for dt, fields in bo.items():
            meta = frappe.get_meta(dt, cached=False)
            for field in fields:
                ten = field['fieldname']
                if not frappe.db.has_column(dt, ten) or not meta.has_field(ten):
                    raise AssertionError('Migrate thiếu cột/metadata %s.%s' % (dt, ten))
                ds.append(dt + '.' + ten)
    for patch in PATCHES:
        if not frappe.db.exists('Patch Log', {'patch': patch}):
            raise AssertionError('Thiếu Patch Log: ' + patch)
    bam = {}
    from vagabond import minvoice_sau_ghi_so as sau
    if frappe.db.get_value('Server Script', sau.TEN, 'script') != sau.ban_moi():
        raise AssertionError('Hook After Submit chưa đúng bản vá v482')
    for ten, loai, _cu, _moi in minvoice_kich_ban.BO:
        ma = frappe.db.get_value('Server Script', ten, 'script')
        if ma != minvoice_kich_ban.ban_moi(loai):
            raise AssertionError('Server Script chưa đúng mã nguồn: ' + ten)
        bam[loai] = minvoice_kich_ban.bam(ma)
    from vagabond.patches.pr_he_so_252 import TEN, nhan_dang
    pr_guard = frappe.get_doc('Server Script', TEN)
    if not pr_guard.disabled or not nhan_dang(pr_guard):
        raise AssertionError('Migrate phải lưu trữ đúng kịch bản PR cũ đã nhận dạng')
    from frappe.utils.safe_exec import is_safe_exec_enabled
    if not is_safe_exec_enabled():
        raise AssertionError('Chưa bật Server Script trong common_site_config của bench')
    return {'truong': ds, 'patches': list(PATCHES), 'server_script_sha256': bam}
