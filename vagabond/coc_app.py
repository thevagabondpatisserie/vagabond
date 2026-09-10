"""Cấn cọc đã ghi sổ qua Payment Reconciliation lõi, trước khi lập đợt chi.

Không tạo thêm bút toán ngân hàng cho khoản đã chi. APP chỉ đề nghị phần
còn nợ sau cấn; lịch sử nằm trên Payment Entry Reference/Payment Ledger.
"""
import json
import frappe
from frappe.utils import flt
from vagabond import ho_so_tt as hs
from vagabond.phan_bo_app import gom, kiem

TRUONG_MOI = {"Payment Entry": [{"fieldname": "vgb_lan_can_coc",
    "label": "Lịch sử yêu cầu cấn cọc APP", "fieldtype": "Long Text",
    "read_only": 1, "hidden": 1, "no_copy": 1, "allow_on_submit": 1, "print_hide": 1}]}


def _phieu(name, ncc, khoa=False, can_sao_ke=True):
    pe = frappe.get_doc("Payment Entry", name, for_update=khoa)
    pe.check_permission("read")
    if (pe.docstatus != 1 or pe.payment_type != "Pay" or pe.party_type != "Supplier"
            or pe.party != ncc
            or pe.paid_from_account_currency != "VND" or pe.paid_to_account_currency != "VND"
            or flt(pe.source_exchange_rate) != 1 or flt(pe.target_exchange_rate) != 1
            or pe.get("vgb_ho_so_tt")):
        frappe.throw("Chọn khoản cọc nhà cung cấp đã ghi sổ, còn tiền chưa cấn, bằng VND và chưa thuộc APP khác.")
    links = frappe.db.sql("""select b.name, d.allocated_amount from `tabBank Transaction Payments` d
        join `tabBank Transaction` b on b.name=d.parent
        where d.payment_document='Payment Entry' and d.payment_entry=%s
        and b.docstatus=1 and b.bank_account=%s""" + (" for update" if khoa else ""), (pe.name, pe.bank_account), as_dict=True)
    if can_sao_ke and sum(flt(r.allocated_amount) for r in links) < flt(pe.paid_amount):
        frappe.throw("Khoản cọc %s chưa đối chiếu đủ tiền trên sao kê. Kế toán đối chiếu trước khi cấn." % pe.name)
    return pe, links


@frappe.whitelist()
def danh_sach(ncc):
    hs._kiem(hs.VAI_FIN, "xem cọc nhà cung cấp")
    ra = []
    for r in frappe.get_list("Payment Entry", filters={"docstatus": 1,
            "payment_type": "Pay", "party_type": "Supplier", "party": ncc}, fields=["name", "posting_date"],
            order_by="posting_date, name", limit_page_length=0):
        try:
            pe, links = _phieu(r.name, ncc, can_sao_ke=False)
            rec, payments = _doi_chieu(pe)
            con = sum(flt(p.get("amount")) for p in payments)
            if con <= 0:
                continue
        except frappe.ValidationError:
            continue
        ra.append({"name": pe.name, "ngay": str(pe.posting_date),
            "con_coc": con, "sao_ke": [x.name for x in links],
            "can_noi_sao_ke": sum(flt(x.allocated_amount) for x in links) < flt(pe.paid_amount)})
    return {"rows": ra}


@frappe.whitelist(methods=["POST"])
def can_coc(ncc, payment_entry, hoa_don, ma_lan):
    hs._kiem(hs.VAI_FIN, "cấn cọc nhà cung cấp")
    dong = frappe.parse_json(hoa_don)
    if not isinstance(dong, list) or not dong:
        frappe.throw("Chọn hóa đơn và số tiền cấn vào từng hóa đơn.")
    try:
        ke = gom(dong)
    except ValueError as exc:
        frappe.throw(str(exc))
    from vagabond.lan_nhan import doc_ma_lan
    ma_lan = doc_ma_lan(ma_lan)
    payload = {"ncc": ncc, "hoa_don": {k: str(v) for k, v in sorted(ke.items())}}
    # Khóa hóa đơn trước, sau đó PE; đọc nhật ký trước khi so dư nợ để
    # lần đã hoàn tất vẫn được nhận diện khi dư nợ/cọc đã về 0.
    for ten in sorted(ke):
        frappe.db.get_value("Purchase Invoice", ten, "name", for_update=True)
    pe_cu = frappe.get_doc("Payment Entry", payment_entry, for_update=True)
    pe_cu.check_permission("read")
    lich_su = json.loads(pe_cu.get("vgb_lan_can_coc") or "{}")
    if ma_lan in lich_su:
        cu = lich_su[ma_lan]
        if cu["payload"] != payload or pe_cu.docstatus != 1:
            frappe.throw("Mã lần cấn đã dùng với nội dung khác hoặc chứng từ đã hủy. Kiểm lại chứng từ trước khi thao tác tiếp.")
        return dict(cu["ket_qua"], da_lam_roi=1)
    try:
        # Cùng thứ tự khóa với các APP: hóa đơn trước, tiền cọc sau.
        hien_tai = kiem(dong)
        pe, links = _phieu(payment_entry, ncc, khoa=True)
        tong = sum(ke.values())
        _kiem_snapshot_pe(pe)
        rec, payments = _doi_chieu(pe)
        con_coc = sum(flt(p.get("amount")) for p in payments)
        if not ke or float(tong) > con_coc:
            frappe.throw("Khoản cọc không còn đủ tiền. Tải lại trước khi cấn; không bấm lặp để thử.")
        invoices = []
        for ten, tien in sorted(ke.items()):
            hd = frappe.get_doc("Purchase Invoice", ten)
            hd.check_permission("read")
            if flt(hd.outstanding_amount) != flt(hien_tai[ten].outstanding_amount):
                frappe.throw("Công nợ vừa thay đổi. Tải lại hóa đơn trước khi cấn cọc.")
            if hd.supplier != ncc or hd.company != pe.company or hd.credit_to != pe.paid_to or hd.currency != "VND":
                frappe.throw("Hóa đơn %s không khớp nhà cung cấp, công ty, tài khoản công nợ hoặc tiền tệ của cọc." % ten)
            match = [i.as_dict() for i in rec.invoices if i.invoice_type == "Purchase Invoice" and i.invoice_number == ten]
            if len(match) != 1:
                frappe.throw("Không tìm được dư nợ lõi của hóa đơn %s." % ten)
            match[0]["outstanding_amount"] = float(tien)
            invoices.extend(match)
        rec.allocate_entries({"payments": payments, "invoices": invoices})
    except frappe.QueryDeadlockError:
        raise
    except frappe.ValidationError as exc:
        # Chỉ phần tiền kiểm đọc dữ liệu/allocate trong bộ nhớ ở trên.
        # Chưa gọi reconcile và chưa ghi chứng từ: lưu kết quả từ chối để
        # retry sau mất phản hồi nhận cùng kết quả, rồi sửa một lần mới.
        ket_qua = {"ok": 0, "loi": str(exc), "payment_entry": payment_entry}
        lich_su[ma_lan] = {"payload": payload, "ket_qua": ket_qua}
        frappe.db.set_value("Payment Entry", payment_entry, "vgb_lan_can_coc", json.dumps(lich_su), update_modified=False)
        return ket_qua
    rec.reconcile()
    pe.reload()
    pe.add_comment("Comment", "Cấn cọc từ APP bởi %s: %s. Sao kê: %s." %
        (frappe.session.user, ", ".join("%s: %s đ" % (k, v) for k, v in ke.items()),
         ", ".join(x.name for x in links)))
    ket_qua = {"ok": 1, "payment_entry": pe.name, "da_can": float(tong), "con_coc": con_coc - float(tong)}
    lich_su[ma_lan] = {"payload": payload, "ket_qua": ket_qua}
    frappe.db.set_value("Payment Entry", pe.name, "vgb_lan_can_coc", json.dumps(lich_su), update_modified=False)
    return ket_qua


def chan_sua_lich_su(doc, method=None):
    cu = doc.get_doc_before_save()
    if (doc.get("vgb_lan_can_coc") or "") != ((cu.get("vgb_lan_can_coc") or "") if cu else ""):
        frappe.throw("Lịch sử lần cấn cọc do máy chủ ghi. Không sửa hoặc xóa trực tiếp.")


def _doi_chieu(pe):
    # ERPNext de591661: khoản ứng có thể còn ở reference Purchase Order,
    # dù PE.unallocated_amount=0. Đọc khả dụng từ PLE qua bộ đối chiếu lõi.
    rec = frappe.new_doc("Payment Reconciliation")
    rec.company, rec.party_type, rec.party = pe.company, "Supplier", pe.party
    rec.receivable_payable_account = pe.paid_to
    rec.get_unreconciled_entries()
    payments = [p.as_dict() for p in rec.payments
                if p.reference_type == "Payment Entry" and p.reference_name == pe.name and flt(p.amount) > 0]
    return rec, payments


@frappe.whitelist()
def sao_ke_coc(ncc, payment_entry):
    hs._kiem(hs.VAI_FIN, "chọn sao kê cọc")
    pe, _ = _phieu(payment_entry, ncc, can_sao_ke=False)
    rows = frappe.get_list("Bank Transaction", filters={"docstatus": 1,
        "bank_account": pe.bank_account, "currency": "VND", "deposit": 0,
        "withdrawal": pe.paid_amount, "unallocated_amount": pe.paid_amount},
        fields=["name", "date", "description", "withdrawal"], order_by="date desc", limit_page_length=0)
    return {"rows": rows}


@frappe.whitelist(methods=["POST"])
def noi_sao_ke_coc(ncc, payment_entry, giao_dich):
    hs._kiem(hs.VAI_FIN, "nối sao kê cọc")
    pe, links = _phieu(payment_entry, ncc, khoa=True, can_sao_ke=False)
    g = frappe.get_doc("Bank Transaction", giao_dich, for_update=True)
    g.check_permission("read")
    if any(r.name != g.name and flt(r.allocated_amount) > 0 for r in links):
        frappe.throw("Phiếu cọc đã nối sao kê khác. Không nối cùng khoản chi hai lần.")
    if (g.docstatus != 1 or g.bank_account != pe.bank_account or g.currency != "VND"
            or flt(g.deposit) != 0 or flt(g.withdrawal) != flt(pe.paid_amount)):
        frappe.throw("Sao kê phải đúng tài khoản, tiền ra và tiền tệ của phiếu cọc.")
    from vagabond.doi_chieu_app import _chu_khac
    chu = _chu_khac(g, frappe._dict(name=pe.name))
    if chu and chu != pe.name:
        frappe.throw("Sao kê đã được %s sử dụng." % chu)
    if links:
        if len(links) == 1 and links[0].name == g.name and flt(links[0].allocated_amount) == flt(pe.paid_amount):
            return {"ok": 1, "giao_dich": g.name, "payment_entry": pe.name, "da_lam_roi": 1}
        frappe.throw("Liên kết sao kê cọc chưa khớp đủ tiền. Kế toán kiểm trong Đối chiếu ngân hàng.")
    for r in g.payment_entries:
        if r.payment_document != "Payment Entry" or r.payment_entry != pe.name:
            frappe.throw("Sao kê đã nối chứng từ khác, không dùng lại cho cọc.")
    if not g.payment_entries:
        if flt(g.unallocated_amount) != flt(pe.paid_amount):
            frappe.throw("Sao kê không còn đủ tiền chưa phân bổ.")
        g.add_payment_entries([{"payment_doctype": "Payment Entry", "payment_name": pe.name}])
        g.save(ignore_permissions=True)
    _phieu(pe.name, ncc)
    return {"ok": 1, "giao_dich": g.name, "payment_entry": pe.name}


def _kiem_snapshot_pe(pe):
    # Current read sau khóa không tự làm mới snapshot của các truy vấn lõi
    # trên MariaDB REPEATABLE READ. Nếu snapshot đã cũ thì dừng trước ghi.
    snap = frappe.get_doc("Payment Entry", pe.name)
    for k in ("docstatus", "party", "party_type", "company", "paid_from", "paid_to", "bank_account"):
        if snap.get(k) != pe.get(k):
            frappe.throw("Phiếu cọc vừa thay đổi. Tải lại trước khi cấn.")
    for k in ("paid_amount", "received_amount", "unallocated_amount"):
        if flt(snap.get(k)) != flt(pe.get(k)):
            frappe.throw("Số tiền cọc vừa thay đổi. Tải lại trước khi cấn.")
    rows = frappe.db.sql("""select name, reference_doctype, reference_name, allocated_amount
        from `tabPayment Entry Reference` where parent=%s for update""", (pe.name,), as_dict=True)
    def refs(ds):
        return sorted((r.name, r.reference_doctype or "", r.reference_name or "", flt(r.allocated_amount)) for r in ds)
    if refs(rows) != refs(snap.references):
        frappe.throw("Phân bổ cọc vừa thay đổi. Tải lại trước khi cấn.")
