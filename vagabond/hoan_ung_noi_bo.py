"""TTNB là lần người ứng trả nhân viên; APP là lần công ty hoàn người ứng.

Không tạo bút toán ở bước nối TTNB. Giữ một khoản có hai chứng từ minh chứng,
nhưng chỉ một APP được hoàn tiền. Nguồn 141 phải gắn đúng người nhận hoàn.
"""
import frappe
from frappe.utils import cint, flt


def nguon_chi(ten):
    b = frappe.db.get_value('Bank Account', ten or '',
        ['name', 'account', 'is_company_account', 'party_type', 'party', 'disabled'], as_dict=True) or {}
    if not b or cint(b.get('disabled')):
        return {}
    tk = b.get('account')
    a = frappe.db.get_value('Account', tk or '', ['account_number', 'disabled', 'is_group'], as_dict=True) or {}
    if not a or cint(a.get('disabled')) or cint(a.get('is_group')):
        return {}
    so = str(a.get('account_number') or str(tk).split(' - ')[0]).strip()
    b['tam_ung'] = bool(so.startswith('141') and b.get('party_type') == 'Supplier' and b.get('party'))
    b['cong_ty'] = bool(cint(b.get('is_company_account')) and not so.startswith('141'))
    return b


def giao_dich(ma):
    """Mã BT hoặc tham chiếu FT cũ; không đoán khi nhiều dòng cùng tham chiếu."""
    ma = str(ma or '').strip()
    if not ma:
        return None
    cot = ['name', 'reference_number', 'bank_account', 'withdrawal', 'docstatus', 'description', 'date']
    if frappe.db.exists('Bank Transaction', ma):
        return frappe.db.get_value('Bank Transaction', ma, cot, as_dict=True)
    ds = frappe.get_all('Bank Transaction', filters={'reference_number': ma, 'docstatus': ['<', 2]},
        fields=cot, limit_page_length=2)
    return ds[0] if len(ds) == 1 else None


def xep_goi_y(ds, so_tien=0, noi_dung='', ma_gd=''):
    """Gợi ý có lý do, chưa bao giờ là quyết định khớp tự động."""
    from vagabond.khop_sao_ke import co_ma
    ra = [dict(d) for d in ds]
    ra.sort(key=lambda d: (str(d.get('creation') or d.get('ngay') or ''), d.get('name') or d.get('ma') or ''), reverse=True)
    for d in ra:
        ma = d.get('name') or d.get('ma') or ''
        tien = flt(d.get('tong_tien')) or flt(d.get('so_tien'))
        if ma_gd and d.get('ma_gd') == ma_gd:
            d['hang_goi_y'], d['goi_y'] = 0, 'Cùng giao dịch'
        elif noi_dung and co_ma(noi_dung, ma):
            d['hang_goi_y'], d['goi_y'] = 1, 'Đúng mã phiếu'
        elif flt(so_tien) > 0 and abs(tien - flt(so_tien)) <= 1:
            d['hang_goi_y'], d['goi_y'] = 2, 'Đúng số tiền'
        else:
            d['hang_goi_y'], d['goi_y'] = 3, ''
    return sorted(ra, key=lambda d: d['hang_goi_y'])


def kiem_ho_so(doc):
    """Cửa Document: APP/Desk/API cùng kiểm và giữ TTNB trong một giao dịch.

    Chỉ kiểm phần liên kết mới/đổi; không ép sửa lịch sử khi lưu hồ sơ cũ.
    Không commit ở validate. Frappe Document.insert/save chạy trong transaction
    của caller; lỗi ở bước sau phải rollback cả dấu giữ phiếu.
    """
    if doc.get('loai') not in ('Hoan ung', 'Hoan ung HD'):
        return
    cu = doc.get_doc_before_save()
    cu_dong = {d.name: d for d in (cu.get('dong') or [])} if cu else {}
    da_thay = set()
    for d in doc.get('dong') or []:
        ma = str(d.get('de_nghi_chi') or '').strip()
        if not ma:
            continue
        if ma in da_thay:
            frappe.throw('Phiếu %s đang nối hai khoản. Gỡ một khoản để không hoàn ứng hai lần.' % ma)
        da_thay.add(ma)
        truoc = cu_dong.get(d.name)
        if cu and truoc and cu.get('tk_nhan') == doc.get('tk_nhan') and all(
                truoc.get(k) == d.get(k) for k in ('de_nghi_chi', 'ma_giao_dich', 'so_tien')):
            continue
        rows = frappe.db.sql('''select name, trang_thai, ma_gd, ho_so_tt, tong_tien, so_tien
            from `tabVagabond De Nghi Chi` where name=%s for update''', (ma,), as_dict=True)
        if not rows:
            frappe.throw('Không thấy phiếu %s. Chọn lại phiếu nội bộ.' % ma)
        p = rows[0]
        from vagabond.ho_so_tt import TT_PHIEU_NOI_BO
        if p.trang_thai not in TT_PHIEU_NOI_BO:
            frappe.throw('Phiếu %s chưa được duyệt. Nhờ kế toán duyệt trước khi nối.' % ma)
        if p.ho_so_tt and p.ho_so_tt != doc.name:
            frappe.throw('Phiếu %s đã nối hồ sơ %s. Mở hồ sơ đó, không lập hoàn ứng lần hai.' % (ma, p.ho_so_tt))
        if abs(flt(d.so_tien) - (flt(p.tong_tien) or flt(p.so_tien))) > 1:
            frappe.throw('Số tiền khoản nối %s phải bằng số tiền phiếu. Kiểm lại khoản đã chọn.' % ma)
        if p.ma_gd:
            g = giao_dich(p.ma_gd)
            if not g or cint(g.docstatus) >= 2 or flt(g.withdrawal) <= 0:
                frappe.throw('Sao kê của %s không còn hợp lệ. Kiểm lại giao dịch đã khớp.' % ma)
            b = nguon_chi(g.bank_account)
            if not b.get('tam_ung'):
                frappe.throw('Phiếu %s đã chi từ tài khoản công ty hoặc chưa rõ nguồn ứng. Kiểm lại nguồn, không hoàn ứng thêm cho khoản công ty đã chi.' % ma)
            nhan = nguon_chi(doc.get('tk_nhan'))
            if not nhan.get('tam_ung') or nhan.get('party') != b.get('party') or doc.get('nha_cung_cap') != b.get('party'):
                frappe.throw('Phiếu %s do người khác ứng tiền. Chọn tài khoản nhận hoàn của đúng người đã chi.' % ma)
            gd_dong = str(d.get('ma_giao_dich') or '').strip()
            if gd_dong and gd_dong not in (g.name, g.reference_number):
                frappe.throw('Khoản đang chọn và phiếu %s thuộc hai giao dịch khác nhau. Chọn lại phiếu hoặc gỡ giao dịch ở khoản này.' % ma)
            if abs(flt(d.so_tien) - flt(g.withdrawal)) > 1:
                frappe.throw('Tiền sao kê và phiếu %s chưa khớp. Kiểm lại khoản chuyển trước khi đề nghị hoàn.' % ma)
            # Canonical name giúp mã FT và mã BT không tạo hai lần hoàn khác nhau.
            d.ma_giao_dich = g.name
        frappe.db.set_value('Vagabond De Nghi Chi', ma, 'ho_so_tt', doc.name, update_modified=False)


def khoa_ma_giao_dich(ma):
    """Khóa dòng tiền trước khi đọc APP giữ nó, gộp tên BT và tham chiếu cũ."""
    g = giao_dich(ma)
    if not g:
        return {ma}
    frappe.db.sql('select name from `tabBank Transaction` where name=%s for update', (g.name,))
    return {m for m in (g.name, g.reference_number, ma) if m}
