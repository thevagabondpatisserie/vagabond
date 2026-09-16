"""Cấp quỹ và quyết toán APP bằng Journal Entry lõi, NQ chỉ là tham chiếu.

ERPNext v16.28.0 journal_entry.validate_reference_doc kiểm từng PI/party/
account và make_gl_entries cập nhật công nợ. Không tự sửa GL hoặc số dư PI.
Các nguồn và lượt cấn khóa chung Bank Account; không coi mọi tiền vào của
cá nhân là tiền công ty. Chỉ nguồn kế toán chủ động ghi nhận mới được cấn.
"""
import json
from decimal import Decimal, InvalidOperation

import frappe
from frappe.utils import flt, today

APP = "Vagabond Ho So TT"
JE = "Journal Entry"
TRUONG_MOI = {
    APP: [{"fieldname": "vgb_can_ung", "label": "Bút toán quyết toán tạm ứng",
           "fieldtype": "Link", "options": JE, "read_only": 1, "no_copy": 1}],
    JE: [
        {"fieldname": "vgb_quy_ung", "label": "Quỹ tạm ứng", "fieldtype": "Link", "options": "Bank Account", "read_only": 1, "no_copy": 1},
        {"fieldname": "vgb_cap_ung_bt", "label": "Sao kê cấp quỹ", "fieldtype": "Link", "options": "Bank Transaction", "read_only": 1, "no_copy": 1},
        {"fieldname": "vgb_nq_tham_chieu", "label": "Phiếu nộp quỹ tham chiếu", "fieldtype": "Link", "options": "Vagabond Nop Quy", "read_only": 1},
        {"fieldname": "vgb_nguon_ung", "label": "Phân bổ nguồn tạm ứng", "fieldtype": "Long Text", "read_only": 1, "no_copy": 1},
    ],
}


def _quyen():
    from vagabond.ho_so_tt import _kiem, VAI_FIN
    _kiem(VAI_FIN, "ghi nhận và quyết toán quỹ tạm ứng")


def _quy(name, khoa=True):
    b = frappe.get_doc("Bank Account", name, for_update=khoa)
    a = frappe.get_doc("Account", b.account)
    if b.disabled or b.is_company_account or b.party_type != "Supplier" or not b.party:
        frappe.throw("Chọn tài khoản cá nhân đã khai đúng người giữ quỹ tạm ứng.")
    if not str(a.account_number or a.name).startswith("141") or a.is_group or a.disabled:
        frappe.throw("Tài khoản nhận chưa gắn với sổ quỹ tạm ứng 141. Kế toán kiểm lại danh mục.")
    if a.account_type != "Bank":
        frappe.throw("Sổ quỹ 141 chưa khai loại Bank nên lõi chưa đối chiếu được sao kê. Kế toán kiểm cấu hình tài khoản, không cần lập lại APP.")
    if a.account_currency != "VND" or frappe.db.get_value("Company", a.company, "default_currency") != "VND":
        frappe.throw("Luồng quỹ tạm ứng này chỉ dùng VND.")
    return b, a


def _nguon(bank):
    """Current read dưới khóa quỹ; tiền còn lại từ JE đã submit, không từ cache."""
    rows = frappe.db.sql("""select name, total_debit, vgb_cap_ung_bt, vgb_nguon_ung,
        posting_date from `tabJournal Entry` where docstatus=1 and vgb_quy_ung=%s
        order by posting_date, creation, name for update""", (bank,), as_dict=True)
    con = {r.name: flt(r.total_debit) for r in rows if r.vgb_cap_ung_bt}
    for r in rows:
        for ten, tien in json.loads(r.vgb_nguon_ung or "{}").items():
            if ten not in con:
                frappe.throw("Bút toán %s đang cấn một nguồn không còn hiệu lực. Kế toán kiểm lại." % r.name)
            con[ten] -= flt(tien)
    return rows, con


def chia_nguon(nguon, so_tien):
    """Phân bổ chính xác theo thứ tự nguồn; không làm tròn tiền để che thiếu."""
    try:
        can = Decimal(str(so_tien))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Số tiền cấn phải là số dương hữu hạn.") from None
    if not can.is_finite() or can <= 0:
        raise ValueError("Số tiền cấn phải là số dương hữu hạn.")
    ra = {}
    for ten, so in nguon.items():
        so = Decimal(str(so))
        if not so.is_finite() or so < 0:
            raise ValueError("Nguồn tạm ứng đang lệch số dư, cần kiểm lại chứng từ.")
        lay = min(can, so)
        if lay:
            ra[ten] = float(lay)
            can -= lay
        if not can:
            return ra
    raise ValueError("Số tiền cấn lớn hơn khoản cấp quỹ còn lại.")


@frappe.whitelist()
def danh_sach(tai_khoan):
    _quyen()
    b, a = _quy(tai_khoan)
    rows, con = _nguon(b.name)
    return {"nguoi": b.party, "company": a.company,
            "nguon": [{"name": r.name, "ngay": r.posting_date, "so_tien": flt(r.total_debit),
                       "con_lai": con[r.name]} for r in rows if r.name in con],
            "con_lai": sum(con.values())}


@frappe.whitelist(methods=["POST"])
def ghi_nhan_cap(giao_dich, tai_khoan_nguon, nop_quy=""):
    """Tiền ĐÃ nộp: ghi Nợ141/Có111, không tạo yêu cầu chuyển tiền mới."""
    _quyen()
    bank = frappe.db.get_value("Bank Transaction", giao_dich, "bank_account")
    b, a = _quy(bank)
    g = frappe.get_doc("Bank Transaction", giao_dich, for_update=True)
    if g.docstatus != 1 or g.bank_account != b.name or g.currency != "VND" or flt(g.deposit) <= 0 or flt(g.withdrawal):
        frappe.throw("Chọn dòng tiền vào đã xác nhận của đúng quỹ tạm ứng.")
    cu = frappe.db.get_value(JE, {"vgb_cap_ung_bt": g.name, "docstatus": 1}, "name")
    if cu:
        j = frappe.get_doc(JE, cu)
        if (j.get("vgb_nq_tham_chieu") or "") != (nop_quy or "") or not any(
                d.account == tai_khoan_nguon and flt(d.credit_in_account_currency) == flt(g.deposit) for d in j.accounts):
            frappe.throw("Giao dịch đã được ghi nhận với nguồn khác. Mở bút toán %s để kiểm, không ghi lần hai." % cu)
        return {"name": cu, "da_lam_roi": 1}
    if g.payment_entries or flt(g.allocated_amount):
        frappe.throw("Dòng sao kê đã nối chứng từ khác. Mở Đối chiếu ngân hàng để kiểm trước khi ghi nhận cấp quỹ.")
    src = frappe.get_doc("Account", tai_khoan_nguon)
    if src.company != a.company or src.is_group or src.disabled or src.account_currency != "VND" or not str(src.account_number or src.name).startswith("111"):
        frappe.throw("Nộp tiền mặt phải chọn tài khoản quỹ tiền mặt 111 cùng công ty. Khoản chuyển từ ngân hàng dùng chứng từ chuyển tiền của kế toán.")
    if nop_quy and not frappe.db.exists("Vagabond Nop Quy", nop_quy):
        frappe.throw("Không tìm thấy phiếu NQ tham chiếu. Chọn lại hoặc để trống.")
    j = frappe.new_doc(JE)
    j.company, j.posting_date, j.voucher_type = a.company, g.date, "Journal Entry"
    j.vgb_quy_ung, j.vgb_cap_ung_bt, j.vgb_nq_tham_chieu = b.name, g.name, nop_quy or ""
    j.user_remark = "Ghi nhận tiền mặt đã cấp vào quỹ tạm ứng. NQ chỉ tham chiếu, không khẳng định đã nộp hết quỹ."
    j.append("accounts", {"account": a.name, "debit_in_account_currency": g.deposit})
    j.append("accounts", {"account": src.name, "credit_in_account_currency": g.deposit})
    j.flags.vgb_tam_ung = True
    j.insert(ignore_permissions=True)
    j.submit()
    g.add_payment_entries([{"payment_doctype": JE, "payment_name": j.name}])
    g.save(ignore_permissions=True)
    g.reload()
    if flt(g.unallocated_amount) != 0 or len(g.payment_entries) != 1 or g.payment_entries[0].payment_entry != j.name:
        frappe.throw("Đối chiếu khoản cấp quỹ chưa khớp. Toàn bộ lượt ghi nhận được lùi lại.")
    return {"name": j.name, "so_tien": flt(g.deposit)}


def kiem_je(doc, method=None):
    """Metadata nghiệp vụ không được giả bằng Desk/import, kể cả sửa sau submit."""
    keys = ("vgb_quy_ung", "vgb_cap_ung_bt", "vgb_nq_tham_chieu", "vgb_nguon_ung")
    cu = doc.get_doc_before_save()
    if not any(doc.get(k) or (cu and cu.get(k)) for k in keys):
        return
    if not doc.flags.get("vgb_tam_ung"):
        if not cu or any(doc.get(k) != cu.get(k) for k in keys) or doc.docstatus != cu.docstatus:
            frappe.throw("Dùng nút ghi nhận/cấn quỹ trên APP để giữ đúng nguồn và tránh dùng trùng tiền.")
        if doc.docstatus == 0:
            frappe.throw("Bút toán quỹ tạm ứng phải được lập và ghi sổ cùng một lượt từ APP.")


def truoc_huy(doc, method=None):
    if not doc.get("vgb_quy_ung"):
        return
    _quy(doc.vgb_quy_ung)
    rows, con = _nguon(doc.vgb_quy_ung)
    if doc.get("vgb_cap_ung_bt") and flt(con.get(doc.name)) != flt(doc.total_debit):
        frappe.throw("Khoản cấp quỹ đã được cấn vào APP. Huỷ bút toán cấn trước rồi mới huỷ khoản cấp.")
    if doc.get("vgb_nguon_ung") and not doc.flags.get("vgb_bo_can"):
        frappe.throw("Bút toán đang cấn vào APP. Dùng nút Bỏ cấn tạm ứng trên hồ sơ để hoàn lại nguồn và trạng thái cùng lượt.")


def thong_tin(doc):
    """Đọc bút toán cấn thật; link hỏng không trở thành số 0 yên lặng."""
    if not doc.get("vgb_can_ung"):
        return None
    j = frappe.get_doc(JE, doc.vgb_can_ung)
    if j.docstatus != 1 or j.get("vgb_ho_so_tt") != doc.name or not j.get("vgb_nguon_ung") or j.get("vgb_quy_ung") != doc.tk_nhan:
        frappe.throw("Bút toán cấn tạm ứng không còn khớp hồ sơ. Kế toán kiểm trước khi tiếp tục.")
    return j


def phan_con_lai(doc):
    from vagabond.ho_so_tt import _ke_hoach_phan_bo
    ra = _ke_hoach_phan_bo(doc)
    j = thong_tin(doc)
    if j:
        for d in j.accounts:
            if d.reference_type == "Purchase Invoice":
                ten = d.reference_name
                ra[ten] = flt(ra.get(ten)) - flt(d.debit_in_account_currency)
                if ra[ten] < 0:
                    frappe.throw("Bút toán cấn vượt tiền hoá đơn trong hồ sơ.")
    return {ten: tien for ten, tien in ra.items() if tien > 0}


def dong_con_lai(doc):
    return [{"hoa_don": ten, "so_tien": tien} for ten, tien in phan_con_lai(doc).items()]


def kiem_app(doc):
    cu = doc.get_doc_before_save()
    if (doc.get("vgb_can_ung") or (cu and cu.get("vgb_can_ung"))) and not doc.flags.get("vgb_tam_ung"):
        if not cu or doc.get("vgb_can_ung") != cu.get("vgb_can_ung"):
            frappe.throw("Dùng nút Cấn/Bỏ cấn tạm ứng trên hồ sơ, không sửa liên kết bút toán trực tiếp.")
    if doc.get("vgb_can_ung"):
        j = thong_tin(doc)
        if flt(doc.da_tam_ung) != flt(j.total_debit):
            frappe.throw("Số trừ tạm ứng phải khớp bút toán cấn của hồ sơ.")
        if doc.trang_thai in ("Nhap", "Cho ke toan", "Cho giam doc", "Tu choi", "Huy"):
            frappe.throw("Hồ sơ đang có bút toán cấn. Bỏ cấn trước khi sửa hoặc huỷ hồ sơ.")


@frappe.whitelist(methods=["POST"])
def can(name, so_tien):
    _quyen()
    from vagabond import ho_so_tt as hs
    from vagabond.phan_bo_app import kiem
    doc = frappe.get_doc(APP, name, for_update=True)
    if doc.loai not in (hs.LOAI_HU, hs.LOAI_HU_HD) or doc.trang_thai != hs.TT_DA_DUYET:
        frappe.throw("Cấn tạm ứng trên hồ sơ hoàn ứng đã duyệt. Hồ sơ chưa duyệt vẫn lưu và gửi như bình thường.")
    if doc.get("vgb_can_ung"):
        j = thong_tin(doc)
        if flt(so_tien) != flt(j.total_debit):
            frappe.throw("Hồ sơ đã cấn số khác. Bỏ cấn trước khi chọn lại.")
        return {"name": j.name, "da_lam_roi": 1}
    if hs._but_toan_cua_ho_so(doc.name) or doc.get("ma_giao_dich"):
        frappe.throw("Hồ sơ đã có bút toán hoặc đã chọn giao dịch hoàn tiền. Kiểm và bỏ đối chiếu cũ trước khi thay đổi khoản phải chuyển.")
    b, a = _quy(doc.tk_nhan)
    if b.party != (doc.nguoi_ung or doc.nha_cung_cap):
        frappe.throw("Quỹ phải thuộc đúng người được hoàn ứng trên hồ sơ.")
    _, con = _nguon(b.name)
    try:
        nguon = chia_nguon(con, so_tien)
        pb = chia_nguon(hs._ke_hoach_phan_bo(doc), so_tien)
    except ValueError as exc:
        frappe.throw(str(exc))
    kiem(doc.dong, doc.name)
    j = frappe.new_doc(JE)
    j.company, j.posting_date, j.voucher_type = a.company, today(), "Journal Entry"
    j.vgb_quy_ung, j.vgb_ho_so_tt = b.name, doc.name
    j.vgb_nguon_ung = json.dumps(nguon, sort_keys=True)
    j.user_remark = "Quyết toán khoản đã chi bằng tiền được cấp trước theo hồ sơ " + doc.name
    for ten, tien in pb.items():
        hd = frappe.get_doc("Purchase Invoice", ten, for_update=True)
        if hd.docstatus != 1 or hd.company != a.company or hd.currency != "VND" or flt(hd.conversion_rate) != 1 or hd.is_return:
            frappe.throw("Hoá đơn %s không cùng công ty/VND hoặc không còn là hoá đơn mua đã ghi sổ." % ten)
        j.append("accounts", {"account": hd.credit_to, "party_type": "Supplier", "party": hd.supplier,
            "reference_type": "Purchase Invoice", "reference_name": hd.name, "debit_in_account_currency": tien})
    j.append("accounts", {"account": a.name, "credit_in_account_currency": sum(nguon.values())})
    j.flags.vgb_tam_ung = True
    j.insert(ignore_permissions=True)
    j.submit()
    doc.vgb_can_ung, doc.da_tam_ung = j.name, j.total_debit
    doc.flags.vgb_tam_ung = True
    doc.save(ignore_permissions=True)
    return {"name": j.name, "da_tam_ung": flt(doc.da_tam_ung), "con_lai": flt(doc.con_lai)}


@frappe.whitelist(methods=["POST"])
def bo_can(name):
    _quyen()
    from vagabond import ho_so_tt as hs
    doc = frappe.get_doc(APP, name, for_update=True)
    j = thong_tin(doc)
    if not j:
        return {"ok": 1, "da_lam_roi": 1}
    _quy(j.vgb_quy_ung)
    if any(b["name"] != j.name for b in hs._but_toan_cua_ho_so(doc.name)) or doc.get("ma_giao_dich"):
        frappe.throw("Còn bút toán chi hoặc đối chiếu hoàn tiền. Kế toán xử lý bút toán chi trước khi bỏ cấn.")
    j.ignore_linked_doctypes = [APP]
    j.flags.vgb_bo_can = True
    j.flags.ignore_permissions = True
    j.cancel()
    doc.vgb_can_ung, doc.da_tam_ung = "", 0
    doc.trang_thai, doc.da_tra = hs.TT_DA_DUYET, 0
    doc.ngay_thanh_toan = None
    doc.flags.vgb_tam_ung = True
    doc.save(ignore_permissions=True)
    return {"ok": 1, "con_lai": flt(doc.con_lai)}


def ke_hoach(doc, ke):
    """Lưu kỳ vọng JE từ hồ sơ và PI hiện tại, không tự tin tổng JE."""
    j = thong_tin(doc)
    if not j:
        return ke
    b, a = _quy(doc.tk_nhan, khoa=False)
    pb = {}
    for d in j.accounts:
        if d.reference_type == "Purchase Invoice":
            pb[d.reference_name] = pb.get(d.reference_name, 0) + flt(d.debit_in_account_currency)
    tong = sum(pb.values())
    if tong != flt(doc.da_tam_ung) or tong != flt(j.total_debit):
        frappe.throw("Bút toán cấn không khớp tổng tiền đã trừ.")
    can = {"name": j.name, "company": a.company, "tai_khoan": a.name, "tong": tong, "hoa_don": {}}
    for ten, tien in pb.items():
        k = ke["hoa_don"].get(ten)
        if not k or tien <= 0 or tien > k["tien"]:
            frappe.throw("Bút toán cấn không khớp từng hoá đơn của hồ sơ.")
        can["hoa_don"][ten] = {"tien": tien, "supplier": k["supplier"],
            "account": frappe.db.get_value("Purchase Invoice", ten, "credit_to")}
        k["tien"] -= tien
    ke["hoa_don"] = {ten: k for ten, k in ke["hoa_don"].items() if k["tien"] > 0}
    ke["can_ung"], ke["tong"] = can, flt(ke["tong"]) - tong
    return ke


def kiem_bo(ke, bo, do):
    """Đối chiếu cả JE cấn và PE trả thêm, kể cả retry sau mất phản hồi."""
    from vagabond.ho_so_tt import _kiem_bo_chung_tu
    can = ke["can_ung"]
    ten = [b["name"] for b in bo]
    js = [b for b in bo if b["doctype"] == JE and b["name"] == can["name"]]
    loi = []
    if len(js) != 1:
        loi.append("thiếu bút toán cấn tạm ứng")
    else:
        j = js[0]
        if j["company"] != can["company"] or flt(j["tong_no"], do) != flt(can["tong"], do):
            loi.append("bút toán cấn sai công ty hoặc tổng")
        pb, co = {}, 0
        for d in j["dong"]:
            no, credit = flt(d["debit_in_account_currency"]), flt(d["credit_in_account_currency"])
            if d.get("account_currency") != "VND" or flt(d.get("exchange_rate")) != 1 or flt(d.get("debit")) != no or flt(d.get("credit")) != credit:
                loi.append("bút toán cấn sai tiền tệ")
            if credit:
                if no or d["account"] != can["tai_khoan"] or d.get("party") or d.get("reference_type"):
                    loi.append("bút toán cấn sai nguồn quỹ")
                co += credit
            elif no:
                hd = d.get("reference_name")
                k = can["hoa_don"].get(hd)
                if d.get("reference_type") != "Purchase Invoice" or not k or d["account"] != k["account"] or d.get("party_type") != "Supplier" or d.get("party") != k["supplier"]:
                    loi.append("bút toán cấn sai hoá đơn/đối tượng")
                pb[hd] = pb.get(hd, 0) + no
        if flt(co, do) != flt(can["tong"], do) or pb != {hd: k["tien"] for hd, k in can["hoa_don"].items()}:
            loi.append("bút toán cấn lệch phân bổ")
    rest = [b for b in bo if b not in js]
    if ke["hoa_don"]:
        k = dict(ke)
        del k["can_ung"]
        ra = _kiem_bo_chung_tu(k, rest, do)
    else:
        ra = {"du": int(not rest), "thieu": [], "thua": [b["name"] for b in rest], "lech": [], "ten": []}
    ra["lech"].extend(loi)
    ra["du"] = int(bool(ra["du"]) and not loi)
    ra["ten"] = ten
    return ra


@frappe.whitelist()
def ung_vien_cap(tai_khoan):
    _quyen()
    b, a = _quy(tai_khoan)
    rows = frappe.get_all("Bank Transaction", filters={"bank_account": b.name, "docstatus": 1,
        "deposit": [">", 0], "withdrawal": 0, "allocated_amount": 0},
        fields=["name", "date", "deposit", "description", "reference_number"],
        order_by="date desc, creation desc, name desc", limit_page_length=0)
    nguon = frappe.get_all("Account", filters={"company": a.company, "is_group": 0, "disabled": 0,
        "account_currency": "VND", "name": ["like", "111%"]}, fields=["name"], order_by="name", limit_page_length=0)
    nq = frappe.get_all("Vagabond Nop Quy", fields=["name"], order_by="creation desc", limit_page_length=0)
    return {"giao_dich": rows, "tai_khoan_nguon": nguon, "nop_quy": nq}
