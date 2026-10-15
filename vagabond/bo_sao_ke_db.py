"""Giữ phần tiền trên phiếu hiện có; Bank Transaction Payments là phần đã ghi sổ.

Không commit. Cửa nghiệp vụ kiểm quyền, nguồn và trạng thái rồi mới gọi.
Khóa các BT theo tên trước phiếu; tranh chấp/deadlock phải rollback cả request.
"""
import json
import frappe
from frappe.utils import flt
from vagabond.bo_sao_ke import doc_bo, phan_con
from vagabond.khop_sao_ke import xet_bo

O_BO = "vgb_bo_sao_ke"
O_CHU = "vgb_chu_bo_sao_ke"
PHIEU = ("Vagabond Ho So TT", "Vagabond De Nghi Chi", "Vagabond Hoan Tien", "Vagabond Cong No", "Journal Entry")
TRUONG_MOI = {dt: [{"fieldname": O_BO, "label": "Phân bổ bộ sao kê", "fieldtype": "Long Text",
    "read_only": 1, "hidden": 1, "no_copy": 1, "allow_on_submit": 1}] for dt in PHIEU}
TRUONG_MOI["Bank Transaction"] = [{"fieldname": O_CHU, "label": "Chủ phần sao kê",
    "fieldtype": "Long Text", "read_only": 1, "hidden": 1, "no_copy": 1, "allow_on_submit": 1}]


def khoa_phieu(dt, ten, dong=()):
    """Đọc dự kiến, khóa BT theo tên, rồi current read phiếu và so phiên bản.

    Không xin thêm BT sau khóa phiếu nếu người khác vừa đổi bộ. Caller phải
    rollback và thử lại, thay vì đảo thứ tự hoặc dùng snapshot cũ.
    """
    if dt not in PHIEU or not ten:
        return
    if (frappe.flags.get("in_migrate") or frappe.flags.get("in_install")) and not frappe.db.has_column(dt, O_BO):
        return
    cu = frappe.db.get_value(dt, ten, O_BO)
    ds = {d["name"] for d in doc_bo(cu)["dong"]} | {d["name"] for d in dong}
    for ma in sorted(ds):
        if not frappe.db.get_value("Bank Transaction", ma, "name", for_update=True):
            frappe.throw("Không còn giao dịch %s. Tải lại sao kê." % ma)
    that = frappe.db.get_value(dt, ten, O_BO, for_update=True)
    if doc_bo(cu) != doc_bo(that):
        frappe.throw("Bộ sao kê vừa đổi. Tải lại phiếu rồi chọn lại để giữ đúng phần tiền.")


def _doc_chu(raw):
    if not raw:
        return {}
    ds = json.loads(raw)
    if not isinstance(ds, dict):
        raise ValueError("Danh sách chủ sao kê không hợp lệ")
    for chu, b in ds.items():
        if not isinstance(chu, str) or chu.split("/", 1)[0] not in PHIEU:
            raise ValueError("Chủ sao kê không hợp lệ")
        doc_bo(b)
    return ds



def cua(doc):
    if doc.doctype not in PHIEU or not doc.name:
        frappe.throw("Loại phiếu chưa được khai phân bổ sao kê.")
    return doc.doctype + "/" + doc.name


def doc_hien_tai(doc):
    return doc_bo(doc.get(O_BO))


def _loi(ma):
    return frappe.db.sql("""select payment_document as doctype, payment_entry as name,
        allocated_amount as tien from `tabBank Transaction Payments`
        where parent=%s and parenttype='Bank Transaction' for update""", (ma,), as_dict=True)


def _cac_bo(ma, khoa=False):
    # Khóa chính name trên BT là chỉ mục chung cho mọi đường ghi. Lưu cả
    # kế hoạch ở đây để đọc phần giữ không phải khóa thêm phiếu của người khác.
    if (frappe.flags.get("in_migrate") or frappe.flags.get("in_install")) and not frappe.db.has_column("Bank Transaction", O_CHU):
        return []
    raw = frappe.db.get_value("Bank Transaction", ma, O_CHU, for_update=khoa)
    return [dict(b, chu=chu) for chu, b in _doc_chu(raw).items()]


def con_lai(g, doc, khoa=False):
    loi = _loi(g.name) if khoa else [dict(doctype=r.payment_document, name=r.payment_entry,
        tien=r.allocated_amount) for r in g.payment_entries or []]
    return phan_con(flt(g.withdrawal) or flt(g.deposit), loi, _cac_bo(g.name,khoa), g.name, cua(doc))


def luu(doc, dong, chung_tu=None):
    b = doc_bo({"dong": dong, "chung_tu": chung_tu or []})
    khoa_phieu(doc.doctype, doc.name, b["dong"])
    cu = doc_bo(frappe.db.get_value(doc.doctype, doc.name, O_BO, for_update=True))
    ma_moi = {d["name"] for d in b["dong"]}
    for ma in sorted(ma_moi | {d["name"] for d in cu["dong"]}):
        cac = _doc_chu(frappe.db.get_value("Bank Transaction", ma, O_CHU, for_update=True))
        cac.pop(cua(doc), None)
        if ma in ma_moi:
            cac[cua(doc)] = b
        frappe.db.set_value("Bank Transaction", ma, O_CHU,
            json.dumps(cac, ensure_ascii=False, separators=(",", ":")) if cac else None, update_modified=False)
    chuoi = json.dumps(b, ensure_ascii=False, separators=(",", ":")) if b["dong"] else None
    frappe.db.set_value(doc.doctype, doc.name, O_BO, chuoi, update_modified=False)
    doc.set(O_BO, chuoi)
    return b


def bao_ve_chu_bt(doc, method=None):
    """Ô chủ giữ do luu quản lý, không nhận từ payload của BT nháp hay đã ghi sổ."""
    if (frappe.flags.get("in_migrate") or frappe.flags.get("in_install")) and not frappe.db.has_column("Bank Transaction", O_CHU):
        return
    doc.set(O_CHU, None if doc.is_new() else frappe.db.get_value(
        "Bank Transaction", doc.name, O_CHU, for_update=True))


def bao_ve(doc, method=None):
    """Không tin ô read_only: payload Desk/API không được tự ghi chỗ giữ."""
    if doc.doctype in PHIEU:
        if (frappe.flags.get("in_migrate") or frappe.flags.get("in_install")) and not frappe.db.has_column(doc.doctype,O_BO):
            return
        doc.set(O_BO, frappe.db.get_value(doc.doctype,doc.name,O_BO) if not doc.is_new() else None)


def chon(doc, dong, can, chieu, kiem, ghi=False, them_dot=False):
    """kiểm nguồn/legacy qua callback; không dùng tiền client làm tổng phiếu."""
    cua(doc)
    if isinstance(dong,str):
        dong=json.loads(dong)
    b=doc_bo({"dong":dong,"chung_tu":[]})
    if not b["dong"]:
        frappe.throw("Chọn ít nhất một dòng sao kê.")
    if ghi:
        khoa_phieu(doc.doctype, doc.name, b["dong"])
    gs=[]; rows=[]
    for d in b["dong"]:
        g=frappe.get_doc("Bank Transaction",d["name"],for_update=ghi)
        if g.docstatus != 1 or g.currency != "VND":
            frappe.throw("Sao kê %s chưa ghi sổ hoặc không phải tiền đồng." % g.name)
        loi=kiem(g)
        if loi:
            frappe.throw("Giao dịch %s: %s" % (g.name,loi))
        ra,vao=flt(g.withdrawal),flt(g.deposit)
        rows.append(dict(name=g.name,tien=ra or vao,bank_account=g.bank_account,
            chieu="ra" if ra>0 and vao==0 else "vao" if vao>0 and ra==0 else "loi",
            con_lai=con_lai(g,doc,khoa=ghi),phan_bo=d["phan_bo"]))
        gs.append(g)
    k=xet_bo(rows,can,gs[0].bank_account,chieu,dung_sai=0)
    if k["ket_qua"]!="du":
        chu=sorted({b["chu"] for g in gs for b in _cac_bo(g.name,khoa=ghi) if b["chu"]!=cua(doc)})
        thong_bao=("Phần tiền đã được " + ", ".join(chu) + " giữ. " if chu else "")
        thong_bao += ("; ".join(d["ly_do"] for d in k["loi"]) or
            "Bộ sao kê đang có {:,.0f} / {:,.0f} đ; còn thiếu {:,.0f}, thừa {:,.0f} đ.".format(k["tong"],k["can"],k["thieu"],k["thua"]))
        frappe.throw("Bộ sao kê không khớp khoản phải chuyển/thu. "+thong_bao)
    if ghi:
        cu=doc_hien_tai(doc)
        if cu["chung_tu"] and cu["dong"] != dong:
            moi={d['name']:flt(d['phan_bo']) for d in dong}
            chi_them=them_dot and all(moi.get(d['name'],0)>=flt(d['phan_bo']) for d in cu['dong'])
            if not chi_them:
                frappe.throw("Bộ cũ đã nối bút toán. Bỏ đối chiếu trước khi đổi bộ.")
        luu(doc,dong,cu["chung_tu"])
    return frappe._dict(name=gs[0].name, date=max(str(g.date) for g in gs),
        description=getattr(gs[0],"description","") if len(gs)==1 else "", bank_account=gs[0].bank_account, currency="VND",
        reference_number="; ".join(g.reference_number or g.name for g in gs),
        withdrawal=k["tong"] if chieu=="ra" else 0, deposit=k["tong"] if chieu=="vao" else 0,
        flags=frappe._dict(bo_sao_ke=gs,dong=dong,theo_mau=False))


def noi(doc, bo, chung_tu):
    """Lõi tự tính allocated_amount; chênh kế hoạch thì rollback cả request."""
    chung_tu=[dict(doctype=c["doctype"],name=c["name"]) for c in chung_tu]
    ct={(c["doctype"],c["name"]) for c in chung_tu}
    if not ct:
        frappe.throw("Chưa có chứng từ đã ghi sổ để đối chiếu.")
    for dt,ma in sorted(ct):
        if dt not in ("Payment Entry","Journal Entry") or frappe.db.get_value(dt,ma,"docstatus",for_update=True)!=1:
            frappe.throw("Chứng từ %s chưa ghi sổ." % ma)
    # Ghi chủ chứng từ trước bước lõi trong cùng transaction, để cửa bảo vệ
    # BT không tính phần giữ và phân bổ thật của chính bộ này hai lần.
    luu(doc,bo.flags.dong,chung_tu)
    du_kien={d["name"]:flt(d["phan_bo"]) for d in bo.flags.dong}
    # Dòng sử dụng hết phần lõi trước; phần cuối có thể nhỏ hơn BT.
    gs=sorted(bo.flags.bo_sao_ke,key=lambda g:(du_kien[g.name]<flt(g.unallocated_amount),g.name))
    for g in gs:
        da={(p.doctype,p.name) for p in _loi(g.name)}
        moi=[{"payment_doctype":dt,"payment_name":ma} for dt,ma in sorted(ct-da)]
        if moi and flt(g.unallocated_amount)>0:
            g.flags.ignore_permissions=True
            g.add_payment_entries(moi)
            # Hạn mức của lượt này là phần đã kiểm/giữ, không phải toàn
            # số dư BT: phần khác có thể đang được phiếu chưa ghi sổ giữ.
            # Gọi phép lõi với hạn mức trong bộ nhớ. Chính lõi tính các
            # allocated_amount và clearance từ GL; cuối hàm lõi tự tính
            # lại unallocated_amount thật. Không ghi tay child allocation.
            da_cua_bo=sum(flt(p.tien) for p in _loi(g.name) if (p.doctype,p.name) in ct)
            g.unallocated_amount=min(flt(g.unallocated_amount),du_kien[g.name]-da_cua_bo)
            g.allocate_payment_entries()
            g.save(ignore_permissions=True)
        phan=sum(flt(p.tien) for p in _loi(g.name) if (p.doctype,p.name) in ct)
        if abs(phan-du_kien[g.name])>0.001:
            frappe.throw("Lõi chưa phân bổ đúng phần đã chọn trên %s. Đã dừng cả lượt; chọn lại phần tiền hoặc đối chiếu trong ERPNext." % g.name)
    luu(doc,bo.flags.dong,chung_tu)


def bao_ve_bt(doc, method=None):
    """Đối chiếu trực tiếp trong Desk cũng không được lấy phần đang giữ.

    Chạy sau phép phân bổ của lõi, trước ghi child table. Không sửa số tiền
    của lõi; dữ liệu vượt phần tiền thì rollback cả lượt.
    """
    if doc.is_new():
        doc.set(O_CHU, None)
        return
    frappe.db.get_value("Bank Transaction",doc.name,"name",for_update=True)
    raw = frappe.db.get_value("Bank Transaction", doc.name, O_CHU, for_update=True)
    doc.set(O_CHU, raw)
    if not raw:
        return
    cac_bo=[dict(b, chu=chu) for chu, b in _doc_chu(raw).items()]
    if not cac_bo:
        return
    truoc=doc.get_doc_before_save()
    cu=[dict(doctype=r.payment_document,name=r.payment_entry,tien=flt(r.allocated_amount))
        for r in (truoc.payment_entries if truoc else []) or []]
    that=[dict(doctype=r.doctype,name=r.name,tien=flt(r.tien)) for r in _loi(doc.name)]
    khoa=lambda p:(p["doctype"],p["name"])
    if sorted(cu,key=khoa)!=sorted(that,key=khoa):
        frappe.throw("Sao kê vừa được người khác đối chiếu. Tải lại trước khi chọn phần tiền còn lại.")
    moi=[dict(doctype=r.payment_document,name=r.payment_entry,tien=r.allocated_amount)
        for r in doc.payment_entries or []]
    try:
        phan_con(flt(doc.withdrawal) or flt(doc.deposit),moi,cac_bo,doc.name)
    except ValueError as e:
        frappe.throw("Sao kê đang có phần tiền của bộ đã chọn: %s" % str(e))


def kiem_cua_cu(dt, ten, ma):
    """Cửa một dòng cũ không được lấy BT thứ hai của một bộ đang giữ.

    Caller gọi trước ghi và giữ khóa đến commit. Không ghi lại dữ liệu cũ.
    """
    if not ma:
        return
    frappe.db.get_value("Bank Transaction",ma,"name",for_update=True)
    cac_bo=_cac_bo(ma,khoa=True)
    if any(b["chu"] != dt+"/"+ten for b in cac_bo):
        frappe.throw("Giao dịch %s có phần tiền đang được phiếu khác giữ. Mở Khớp SePay để chọn phần còn lại." % ma)


def noi_tung_phieu_thu(doc, ten_pe):
    """Nối một PE đã ghi sổ, giữ nguyên phần của các PE nháp trong cùng bộ.

    Cửa nội bộ: danh sách chứng từ và hạn mức chỉ đọc từ chủ trong DB.
    Caller phải kiểm quyền/UNC và khóa bộ trước khi ghi sổ PE. Không nhận
    chứng từ hay hạn mức từ payload để vượt phần đã giữ.
    """
    if doc.doctype != 'Vagabond Cong No':
        frappe.throw('Cửa ghi từng phiếu thu chỉ dùng cho công nợ tiền vào.')
    khoa_phieu(doc.doctype, doc.name)
    b = doc_bo(frappe.db.get_value(doc.doctype, doc.name, O_BO, for_update=True))
    ct = {(c['doctype'], c['name']) for c in b['chung_tu']}
    if ('Payment Entry', ten_pe) not in ct or any(dt != 'Payment Entry' for dt, _ in ct):
        frappe.throw('Phiếu thu không thuộc bộ sao kê của phiếu công nợ này.')
    if not b['dong']:
        frappe.throw('Phiếu công nợ chưa giữ bộ sao kê.')
    cac_pe = {ma: frappe.get_doc(dt, ma, for_update=True) for dt, ma in sorted(ct)}
    pe = cac_pe[ten_pe]
    if pe.docstatus != 1:
        frappe.throw('Phiếu thu chưa ghi sổ, chưa phân bổ vào sao kê.')
    gs = [frappe.get_doc('Bank Transaction', d['name'], for_update=True)
          for d in sorted(b['dong'], key=lambda d: d['name'])]
    banks = {g.bank_account for g in gs}
    if len(banks) != 1:
        frappe.throw('Bộ tiền vào phải thuộc cùng một tài khoản ngân hàng.')
    ba = frappe.db.get_value('Bank Account', gs[0].bank_account,
        ['account', 'company', 'is_company_account', 'disabled'], as_dict=True) or {}
    if not ba.get('is_company_account') or ba.get('disabled') or not ba.get('account'):
        frappe.throw('Bộ tiền vào phải thuộc tài khoản công ty đang hoạt động.')
    tong_pe = 0
    for p in cac_pe.values():
        if p.docstatus == 2:
            continue
        if (p.payment_type != 'Receive' or p.party_type != 'Customer' or
                p.company != ba.get('company') or p.paid_to != ba.get('account') or
                p.paid_to_account_currency != 'VND' or flt(p.received_amount) <= 0):
            frappe.throw('Phiếu thu %s không khớp nguồn tiền của bộ.' % p.name)
        tong_pe += flt(p.received_amount)
    han_muc = {d['name']: flt(d['phan_bo']) for d in b['dong']}
    if tong_pe > sum(han_muc.values()) + 0.001:
        frappe.throw('Các phiếu thu vượt tổng tiền đã giữ trong bộ.')
    for g in gs:
        if g.docstatus != 1 or g.currency != 'VND' or flt(g.deposit) <= 0 or flt(g.withdrawal):
            frappe.throw('Bộ có sao kê không phải tiền vào đã xác nhận.')
        loi = _loi(g.name)
        da = sum(flt(p.tien) for p in loi if (p.doctype, p.name) in ct)
        if da > han_muc[g.name] + 0.001:
            frappe.throw('Phân bổ lõi đã vượt hạn mức của bộ; tải lại để kiểm.')
        da_noi = any(p.doctype == 'Payment Entry' and p.name == ten_pe for p in loi)
        if not da_noi and han_muc[g.name] - da > 0.001:
            g.flags.ignore_permissions = True
            g.add_payment_entries([{'payment_doctype': 'Payment Entry', 'payment_name': ten_pe}])
            g.unallocated_amount = min(flt(g.unallocated_amount), han_muc[g.name] - da)
            g.allocate_payment_entries()
            g.save(ignore_permissions=True)
    that = sum(flt(p.tien) for g in gs for p in _loi(g.name)
               if p.doctype == 'Payment Entry' and p.name == ten_pe)
    if abs(that - flt(pe.received_amount)) > 0.001:
        frappe.throw('Lõi chưa phân bổ đủ phiếu thu %s; đã dừng cả lượt ghi sổ.' % ten_pe)
    return {'pe': ten_pe, 'tien': that, 'giao_dich': [g.name for g in gs]}
