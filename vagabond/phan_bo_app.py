"""APP là một đợt chi. Giữ tiền theo hóa đơn, khóa trước khi đọc dư nợ."""
from decimal import Decimal, InvalidOperation

GIU = ("Cho ke toan", "Cho giam doc", "Da duyet")


def tien_hop_le(value):
    """Không để flt biến dữ liệu lỗi, NaN hay số 0 thành toàn bộ dư nợ."""
    if isinstance(value, bool):
        raise ValueError("Số tiền phải là số dương hữu hạn.")
    try:
        tien = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Số tiền phải là số dương hữu hạn.") from None
    if not tien.is_finite() or tien <= 0:
        raise ValueError("Số tiền phải là số dương hữu hạn.")
    return tien


def gom(dong):
    ra = {}
    for d in dong or []:
        hd = str(d.get("hoa_don") or "").strip()
        if hd:
            ra[hd] = ra.get(hd, Decimal(0)) + tien_hop_le(d.get("so_tien"))
    return ra


def dang_giu(tru_ho_so="", khoa=False):
    import frappe
    # Đọc từng dòng để không dựa vào aggregate snapshot sau lúc chờ khóa.
    rows = frappe.db.sql("""select d.hoa_don, d.so_tien, p.name
        from `tabVagabond Ho So TT Dong` d
        join `tabVagabond Ho So TT` p on p.name=d.parent
        where p.trang_thai in %s and p.name != %s and ifnull(d.hoa_don,'') != ''
        """ + (" for update" if khoa else ""), (GIU, tru_ho_so), as_dict=True)
    theo_app = {}
    for r in rows:
        key = (r.name, r.hoa_don)
        theo_app[key] = theo_app.get(key, Decimal(0)) + tien_hop_le(r.so_tien)
    if theo_app:
        da_chi = frappe.db.sql("""select pe.vgb_ho_so_tt, r.reference_name, r.allocated_amount
            from `tabPayment Entry Reference` r join `tabPayment Entry` pe on pe.name=r.parent
            where pe.docstatus=1 and pe.vgb_ho_so_tt in %s
            and r.reference_doctype='Purchase Invoice'""" + (" for update" if khoa else ""),
            (tuple(sorted({k[0] for k in theo_app})),), as_dict=True)
        for r in da_chi:
            key = (r.vgb_ho_so_tt, r.reference_name)
            if key in theo_app:
                theo_app[key] -= Decimal(str(r.allocated_amount or 0))
    ra = {}
    for (_, hd), tien in theo_app.items():
        ra[hd] = ra.get(hd, Decimal(0)) + max(Decimal(0), tien)
    return ra


def kiem(dong, tru_ho_so="", khoa=True):
    import frappe
    try:
        return _kiem(dong, tru_ho_so, khoa)
    except frappe.QueryDeadlockError:
        # Giữ loại lỗi giao dịch để caller không coi là từ chối tiền kiểm
        # rồi commit một kết quả trên transaction đã bị MariaDB hủy.
        frappe.throw("Có người đang xử lý cùng công nợ. Tải lại danh sách và kiểm số tiền còn được đề nghị trước khi gửi lại.", frappe.QueryDeadlockError)


def _kiem(dong, tru_ho_so="", khoa=True):
    import frappe
    try:
        ke = gom(dong)
    except ValueError as exc:
        frappe.throw(str(exc))
    if not ke:
        return
    # Thứ tự ổn định cho các APP chứa nhiều hóa đơn.
    hd = {}
    for ten in sorted(ke):
        hd[ten] = frappe.db.get_value("Purchase Invoice", ten,
            ["docstatus", "outstanding_amount", "supplier", "company", "currency"], as_dict=True, for_update=khoa)
    giu = dang_giu(tru_ho_so, khoa=khoa)
    for ten, tien in ke.items():
        r = hd[ten]
        if not r or r.docstatus != 1:
            frappe.throw("Hóa đơn %s chưa ghi sổ hoặc đã hủy. Kiểm lại trước khi đề nghị chi." % ten)
        no = Decimal(str(r.outstanding_amount or 0))
        dang = giu.get(ten, Decimal(0))
        if tien + dang > no:
            frappe.throw("Hóa đơn %s còn nợ %s đ, APP khác đang giữ %s đ; đợt này chỉ được đề nghị tối đa %s đ. Mở lại danh sách để cập nhật." %
                (ten, no, dang, max(Decimal(0), no-dang)))

    return hd


def kiem_luu(doc):
    import frappe
    chan_doi_sau_duyet(doc)
    # Khoản đã chi phải được kiểm bằng bộ chứng từ lõi, không so lại với dư
    # nợ đã giảm do chính Payment Entry của nó.
    if doc.trang_thai in ("Da thanh toan", "Huy", "Tu choi"):
        return
    if not doc.is_new() and frappe.db.exists("Payment Entry", {"vgb_ho_so_tt": doc.name, "docstatus": 1}):
        return
    invoices = kiem(doc.get("dong"), doc.name or "") or {}
    if (doc.get("loai") or "NCC") in ("NCC", "TK cong ty"):
        # APP gom nhiều NCC là luồng hiện có; mỗi PE vẫn lấy NCC từ hóa đơn.
        # Tên NCC đầu hồ sơ phải thuộc tập hóa đơn, không được đổi sang người khác.
        if invoices and doc.nha_cung_cap not in {hd.supplier for hd in invoices.values()}:
            frappe.throw("Hóa đơn không thuộc nhà cung cấp của hồ sơ.")
        if len({hd.company for hd in invoices.values()}) > 1:
            frappe.throw("Một APP chỉ dùng hóa đơn trong cùng công ty.")


def dau_van_tay(doc):
    return (
        tuple((k, str(doc.get(k) or "")) for k in
              ("loai", "nha_cung_cap", "nguoi_ung", "tk_chi", "stk_nhan", "ngan_hang_nhan", "da_tam_ung")),
        tuple(sorted((str(d.get("hoa_don") or ""), str(d.get("so_tien") or 0),
                      str(d.get("tk_no") or ""), str(d.get("tk_co") or ""))
                     for d in doc.get("dong") or [])),
    )


def chan_doi_sau_duyet(doc):
    import frappe
    cu = doc.get_doc_before_save()
    if cu and cu.trang_thai in GIU + ("Da thanh toan",) and dau_van_tay(cu) != dau_van_tay(doc):
        frappe.throw("Hồ sơ đã gửi duyệt. Từ chối hoặc hủy hồ sơ trước khi sửa tiền, phân bổ hay người nhận, rồi gửi duyệt lại.")
