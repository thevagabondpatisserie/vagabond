"""Công nợ NCC: xem dư hóa đơn và xử lý chứng từ cũ mà không nhập kho lại.

#391: file đã chi ngoài ERP là bằng chứng để kế toán kiểm, không phải lệnh
xóa nợ. Màn và Excel dùng cùng một bộ lọc; số hiện tại không giả làm số
chốt quá khứ hay dư thuần sau bù tiền trả trước/Journal Entry.
"""
from datetime import date
from decimal import Decimal


def _so(v):
    return Decimal(str(v or 0))


def tong_hop(ds, hom_nay, trang_thai="con_no", tu_khoa="", ky="", nhom=""):
    """THUẦN: chỉ nhận hóa đơn cùng công ty, không cộng lẫn các đồng tiền."""
    from vagabond.khung.cong_cu_ds import khoang_ky
    tu, den = khoang_ky(ky, hom_nay)
    tim = str(tu_khoa or "").strip().casefold()
    dong, dem = [], {"tat_ca": 0, "con_no": 0, "qua_han": 0, "mot_phan": 0, "het_no": 0}
    for r in ds:
        ngay = str(r.get("bill_date") or r.get("posting_date") or "")[:10]
        if tu and not (tu <= ngay <= den):
            continue
        if nhom and r.get("supplier_group") != nhom:
            continue
        if tim and tim not in " ".join(str(r.get(k) or "") for k in
                ("name", "supplier", "supplier_name", "ma_ncc", "bill_no")).casefold():
            continue
        # ERPNext de591661 accounts/utils.py:update_voucher_outstanding
        # ghi outstanding_in_account_currency vào PI, không phải currency HĐ.
        no = _so(r.get("outstanding_amount"))
        tong = _so((r.get("rounded_total") or r.get("grand_total")) if r.get("account_currency") == r.get("currency") else (r.get("base_rounded_total") or r.get("base_grand_total")))
        han = str(r.get("due_date") or "")[:10]
        tre = max(0, (date.fromisoformat(str(hom_nay)[:10]) - date.fromisoformat(han)).days) if han else 0
        het = no == 0
        phan = 0 < no < tong
        dem["tat_ca"] += 1
        dem["het_no"] += int(het)
        dem["con_no"] += int(no > 0)
        dem["qua_han"] += int(no > 0 and tre > 0)
        dem["mot_phan"] += int(phan)
        if trang_thai == "con_no" and no <= 0 or trang_thai == "qua_han" and not (no > 0 and tre > 0):
            continue
        if trang_thai == "mot_phan" and not phan or trang_thai == "het_no" and not het:
            continue
        dong.append(dict(r, ngay=ngay, han=han, tre_ngay=tre if no > 0 else 0,
            con_no=float(no),
            trang_thai="Hết dư nợ" if het else ("Giảm một phần" if phan else "Còn nợ")))
    dong.sort(key=lambda r: (-bool(r["tre_ngay"]), r["account_currency"], -r["con_no"], r["han"], r["name"]))
    tong_tien, qua_han = {}, {}
    for r in dong:
        tien_te = r["account_currency"]
        tong_tien[tien_te] = tong_tien.get(tien_te, Decimal(0)) + _so(r["con_no"])
        if r["tre_ngay"]:
            qua_han[tien_te] = qua_han.get(tien_te, Decimal(0)) + _so(r["con_no"])
    return {"dong": dong, "dem": dem, "so_hd": len(dong),
        "so_ncc": len({r["supplier"] for r in dong}),
        "tong_theo_tien": {k: float(v) for k, v in tong_tien.items()},
        "qua_han_theo_tien": {k: float(v) for k, v in qua_han.items()}}



import frappe
from frappe.utils import nowdate, cint


def _doc(cong_ty=None):
    from vagabond.mua_hang import _kiem_quyen
    _kiem_quyen()
    # get_list giữ User Permission; không lấy dữ liệu công ty ngoài quyền.
    cty = frappe.get_list("Company", fields=["name", "default_currency"], order_by="name", limit_page_length=0)
    ten = cong_ty or frappe.defaults.get_user_default("Company")
    if not ten and len(cty) == 1:
        ten = cty[0].name
    co = next((r for r in cty if r.name == ten), None)
    if not co:
        return cty, None, []
    ds = frappe.get_list("Purchase Invoice", filters={"docstatus": 1, "company": ten,
        "is_return": 0, "outstanding_amount": [">=", 0]}, fields=["name", "supplier", "supplier_name",
        "posting_date", "bill_date", "bill_no", "due_date", "grand_total", "base_grand_total",
        "rounded_total", "base_rounded_total", "outstanding_amount", "currency", "conversion_rate", "credit_to", "company"],
        order_by="posting_date desc, name desc", limit_page_length=0)
    # Không truy vấn mỗi hóa đơn; tên/mã NCC chỉ nối vào chứng từ đã được phép đọc.
    ncc = {r.name: r for r in frappe.get_list("Supplier", filters={"name": ["in", list({r.supplier for r in ds}) or [""]]},
        fields=["name", "supplier_group", "custom_ma_ncc"], limit_page_length=0)}
    tk = dict(frappe.get_all("Account", filters={"company": ten, "name": ["in", list({r.credit_to for r in ds}) or [""]]},
        fields=["name", "account_currency"], as_list=True, limit_page_length=0))
    for r in ds:
        if not tk.get(r.credit_to):
            frappe.throw("Chưa xác định tiền tệ tài khoản công nợ. Kế toán kiểm tài khoản trước khi cộng số.")
        r.update(ma_ncc=ncc.get(r.supplier, {}).get("custom_ma_ncc") or r.supplier,
            supplier_group=ncc.get(r.supplier, {}).get("supplier_group") or "Chưa phân nhóm",
            account_currency=tk.get(r.credit_to) or co.default_currency,
            company_currency=co.default_currency)
    return cty, co, ds


def _ket_qua(cong_ty=None, trang_thai="con_no", tu_khoa="", ky="", nhom="", **bo_qua):
    if trang_thai not in ("tat_ca", "con_no", "qua_han", "mot_phan", "het_no"):
        frappe.throw("Chọn lại trạng thái công nợ rồi tải lại.")
    cty, co, ds = _doc(cong_ty)
    kq = tong_hop(ds, nowdate(), trang_thai, tu_khoa, ky, nhom)
    kq.update(cong_ty=co.name if co else "", tien_te=co.default_currency if co else "",
        cac_cong_ty=[r.name for r in cty], cac_nhom=sorted({r["supplier_group"] for r in ds}),
        ngay_doc=nowdate(), nguon="Dư hóa đơn đã ghi sổ hiện tại; chưa bù tiền trả trước và bút toán khác.")
    return kq


@frappe.whitelist()
def danh_sach(cong_ty=None, trang_thai="con_no", tu_khoa="", ky="", nhom="", trang=0):
    kq = _ket_qua(cong_ty, trang_thai, tu_khoa, ky, nhom)
    dau = max(0, cint(trang)) * 30
    kq["dong"] = kq["dong"][dau:dau + 30]
    kq["con_nua"] = dau + 30 < kq["so_hd"]
    return kq


def xuat_ds(**khac):
    kq = _ket_qua(**khac)
    cot = [("company", "Công ty", "chu"), ("ma_ncc", "Mã NCC", "chu"),
        ("supplier", "Mã ERP NCC", "chu"), ("supplier_name", "Nhà cung cấp", "chu"),
        ("name", "Mã hóa đơn ERP", "chu"), ("bill_no", "Số hóa đơn NCC", "chu"),
        ("ngay", "Ngày hóa đơn", "ngay"), ("posting_date", "Ngày hạch toán", "ngay"),
        ("han", "Hạn trả", "ngay"), ("trang_thai", "Trạng thái dư", "chu"),
        ("grand_total", "Tổng hóa đơn", "tien"), ("currency", "Tiền tệ hóa đơn", "chu"),
        ("con_no", "Dư theo TK công nợ", "tien"), ("account_currency", "Tiền tệ TK công nợ", "chu"),
        ("nguon", "Phạm vi số liệu", "chu"), ("ngay_doc", "Ngày đọc dư hiện tại", "ngay")]
    return "Du-hoa-don-NCC", [dict(k=k, nhan=n, kieu=t) for k, n, t in cot], [
        dict(r, nguon=kq["nguon"], ngay_doc=kq["ngay_doc"]) for r in kq["dong"]]


def _cap_chung_tu(hoa_don, payment_entry=None, khoa=False):
    """Đúng công ty/NCC/tài khoản trước khi cho xem hoặc gắn bằng chứng."""
    from vagabond import ho_so_tt as hs, coc_app
    hs._kiem(hs.VAI_FIN, "cấn trừ công nợ nhà cung cấp")
    hd = frappe.get_doc("Purchase Invoice", hoa_don)
    hd.check_permission("read")
    if hd.docstatus != 1 or hd.is_return:
        frappe.throw("Chọn hóa đơn mua thường đã ghi sổ để cấn trừ.")
    if not payment_entry:
        return hd, None
    pe, _ = coc_app._phieu(payment_entry, hd.supplier, khoa=khoa, can_sao_ke=False)
    if pe.company != hd.company or pe.paid_to != hd.credit_to or hd.currency != "VND":
        frappe.throw("Chọn khoản đã trả cùng công ty, nhà cung cấp, tài khoản công nợ và tiền VND của hóa đơn.")
    return hd, pe


@frappe.whitelist()
def khoan_da_tra(hoa_don):
    from vagabond import coc_app, tep_dinh_kem
    hd, _ = _cap_chung_tu(hoa_don)
    # Chỉ trả lựa chọn cùng công ty/tài khoản; không đợi bấm cấn mới báo sai.
    hop_le = set(frappe.get_list("Payment Entry", filters={"docstatus": 1,
        "company": hd.company, "party_type": "Supplier", "party": hd.supplier,
        "paid_to": hd.credit_to}, pluck="name", limit_page_length=0))
    ds = [r for r in coc_app.danh_sach(hd.supplier)["rows"] if r["name"] in hop_le]
    for r in ds:
        pe = frappe.get_doc("Payment Entry", r["name"])
        pe.check_permission("read")
        r["unc"] = tep_dinh_kem.doc_ds(pe.get("vgb_chi_unc"))
        r["unc"] = [u for u in r["unc"] if u.startswith(("/private/files/", "/files/"))]
    return {"rows": ds, "hoa_don": hd.name, "ncc": hd.supplier, "con_no": hd.outstanding_amount}


@frappe.whitelist(methods=["POST"])
def luu_unc(hoa_don, payment_entry, unc):
    """Chỉ gắn tệp vào phiếu đã chi, tuyệt đối không ghi giảm công nợ."""
    from vagabond import tep_dinh_kem
    _, pe = _cap_chung_tu(hoa_don, payment_entry, khoa=True)
    pe.check_permission("write")
    cu = tep_dinh_kem.doc_ds(pe.get("vgb_chi_unc"))
    urls = tep_dinh_kem.doc_ds(unc)
    if not urls:
        frappe.throw("Chọn tệp UNC trước khi lưu.")
    if len(set(cu + urls)) > tep_dinh_kem.CAP_SO_TEP:
        frappe.throw("Phiếu đã đủ số tệp cho phép. Mở phiếu để xem các tệp đã đính.")
    them = tep_dinh_kem.gan_vao("Payment Entry", pe.name, "vgb_chi_unc", urls)
    if len(them) != len(urls):
        frappe.throw("Có tệp không còn tồn tại. Chọn lại tệp UNC rồi lưu.")
    moi = tep_dinh_kem.doc_ds(tep_dinh_kem.ghi_ds(cu + them))
    frappe.db.set_value("Payment Entry", pe.name, "vgb_chi_unc", tep_dinh_kem.ghi_ds(moi))
    if moi != cu:
        pe.add_comment("Comment", "Đính bổ sung UNC từ màn công nợ NCC; không thay số dư hay bút toán.")
    return {"so_unc": len(moi)}
