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


def _phieu(name, ncc, khoa=False):
    pe = frappe.get_doc("Payment Entry", name, for_update=khoa)
    pe.check_permission("read")
    if (pe.docstatus != 1 or pe.payment_type != "Pay" or pe.party_type != "Supplier"
            or pe.party != ncc or pe.unallocated_amount <= 0
            or pe.paid_from_account_currency != "VND" or pe.paid_to_account_currency != "VND"
            or flt(pe.source_exchange_rate) != 1 or flt(pe.target_exchange_rate) != 1
            or pe.get("vgb_ho_so_tt")):
        frappe.throw("Chọn khoản cọc nhà cung cấp đã ghi sổ, còn tiền chưa cấn, bằng VND và chưa thuộc APP khác.")
    links = frappe.db.sql("""select b.name, d.allocated_amount from `tabBank Transaction Payments` d
        join `tabBank Transaction` b on b.name=d.parent
        where d.payment_document='Payment Entry' and d.payment_entry=%s
        and b.docstatus=1 and b.bank_account=%s""", (pe.name, pe.bank_account), as_dict=True)
    if sum(flt(r.allocated_amount) for r in links) < flt(pe.paid_amount):
        frappe.throw("Khoản cọc %s chưa đối chiếu đủ tiền trên sao kê. Kế toán đối chiếu trước khi cấn." % pe.name)
    return pe, links


@frappe.whitelist()
def danh_sach(ncc):
    hs._kiem(hs.VAI_FIN, "xem cọc nhà cung cấp")
    ra = []
    for r in frappe.get_list("Payment Entry", filters={"docstatus": 1,
            "payment_type": "Pay", "party_type": "Supplier", "party": ncc,
            "unallocated_amount": [">", 0]}, fields=["name", "posting_date", "unallocated_amount"],
            order_by="posting_date, name", limit_page_length=0):
        try:
            pe, links = _phieu(r.name, ncc)
        except frappe.ValidationError:
            continue
        ra.append({"name": pe.name, "ngay": str(pe.posting_date),
            "con_coc": pe.unallocated_amount, "sao_ke": [x.name for x in links]})
    return {"rows": ra}


@frappe.whitelist()
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
    # Cùng thứ tự khóa với các APP: hóa đơn trước, tiền cọc sau.
    kiem(dong)
    pe, links = _phieu(payment_entry, ncc, khoa=True)
    tong = sum(ke.values())
    if not ke or float(tong) > flt(pe.unallocated_amount):
        frappe.throw("Khoản cọc không còn đủ tiền. Tải lại trước khi cấn; không bấm lặp để thử.")
    rec = frappe.new_doc("Payment Reconciliation")
    rec.company, rec.party_type, rec.party = pe.company, "Supplier", ncc
    rec.receivable_payable_account = pe.paid_to
    rec.get_unreconciled_entries()
    payments = [p.as_dict() for p in rec.payments if p.reference_type == "Payment Entry" and p.reference_name == pe.name]
    if len(payments) != 1:
        frappe.throw("Lõi chưa xác định được một khoản cọc chưa phân bổ. Kế toán mở Đối chiếu thanh toán để kiểm.")
    invoices = []
    for ten, tien in sorted(ke.items()):
        hd = frappe.get_doc("Purchase Invoice", ten)
        hd.check_permission("read")
        if hd.supplier != ncc or hd.company != pe.company or hd.credit_to != pe.paid_to or hd.currency != "VND":
            frappe.throw("Hóa đơn %s không khớp nhà cung cấp, công ty, tài khoản công nợ hoặc tiền tệ của cọc." % ten)
        match = [i.as_dict() for i in rec.invoices if i.invoice_type == "Purchase Invoice" and i.invoice_number == ten]
        if len(match) != 1:
            frappe.throw("Không tìm được dư nợ lõi của hóa đơn %s." % ten)
        match[0]["outstanding_amount"] = float(tien)
        invoices.extend(match)
    payments[0]["amount"] = float(tong)
    rec.allocate_entries({"payments": payments, "invoices": invoices})
    rec.reconcile()
    pe.reload()
    pe.add_comment("Comment", "Cấn cọc từ APP bởi %s: %s. Sao kê: %s." %
        (frappe.session.user, ", ".join("%s: %s đ" % (k, v) for k, v in ke.items()),
         ", ".join(x.name for x in links)))
    ket_qua = {"ok": 1, "payment_entry": pe.name, "da_can": float(tong), "con_coc": pe.unallocated_amount}
    lich_su[ma_lan] = {"payload": payload, "ket_qua": ket_qua}
    frappe.db.set_value("Payment Entry", pe.name, "vgb_lan_can_coc", json.dumps(lich_su), update_modified=False)
    return ket_qua
