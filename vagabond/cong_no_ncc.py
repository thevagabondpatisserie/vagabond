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
    # v549: phần đã trả trước ERP đang chờ kế toán duyệt, để dòng không nói
    # "chưa làm gì" khi Uyên đã gửi. Chỉ đọc 30 dòng đang xem.
    ten = [r["name"] for r in kq["dong"]]
    cho = {}
    if ten:
        for hd, je, tien in frappe.db.sql("""select a.reference_name, je.name, sum(a.debit_in_account_currency)
                from `tabJournal Entry` je join `tabJournal Entry Account` a on a.parent = je.name
                where je.docstatus = 0 and a.reference_type = 'Purchase Invoice' and a.reference_name in %s
                  and je.user_remark like %s group by a.reference_name, je.name""",
                (tuple(ten), DAU_TRUOC_ERP + "%")):
            cho.setdefault(hd, []).append({"je": je, "so_tien": float(tien or 0)})
    for r in kq["dong"]:
        r["cho_duyet"] = cho.get(r["name"], [])
    kq["ke_toan"] = _la_ke_toan()
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


# ---------------------------------------------------------------------------
# v549: hóa đơn đã trả TRƯỚC KHI LÊN ERP.
#
# Ca thật 01/10/2026: hóa đơn Printeco 04/04/2026 (212.090.400 đ) trả từ tháng
# 4, trước khi ERP chạy, nên trên ERP không có phiếu chi nào để cấn. Nút Cấn
# trừ công nợ của v548 chỉ cấn được vào phiếu chi đã có, nên với hóa đơn này
# chỉ hiện hướng dẫn. Anh Việt chốt cách ghi:
#   Nợ 331 (đúng NCC, đúng hóa đơn) / Có tài khoản tạm "chờ xử lý đầu kỳ"
#   (Account loại Temporary của công ty).
# Không Có 1121: tiền đã ra khỏi ngân hàng trước khi lên ERP, số dư ngân hàng
# mang sang ERP đã trừ khoản này rồi, Có 1121 nữa là trừ hai lần. Kế toán kết
# chuyển tài khoản tạm khi chốt số dư đầu kỳ.
# Thu mua (Uyên) lập bút toán NHÁP kèm UNC; kế toán duyệt mới ghi sổ. Kế toán
# tự lập thì ghi sổ luôn.
# ---------------------------------------------------------------------------

DAU_TRUOC_ERP = "[Trả trước khi lên ERP]"


def kiem_so_tien_truoc_erp(so_tien, con_no, dang_cho=0):
    """THUẦN: lỗi (chuỗi) hoặc None. Không vượt dư trừ phần đang chờ duyệt."""
    try:
        tien = _so(so_tien)
    except Exception:
        return "Nhập số tiền đã trả bằng số."
    if tien <= 0:
        return "Nhập số tiền đã trả lớn hơn 0."
    con = _so(con_no) - _so(dang_cho)
    if con <= 0:
        return "Hóa đơn này đã có khoản chờ kế toán duyệt bằng toàn bộ dư nợ. Chờ duyệt xong rồi xem lại."
    if tien > con:
        return "Số tiền vượt phần còn nợ có thể cấn (%s đ)." % "{:,.0f}".format(con).replace(",", ".")
    return None


def kiem_ngay_tra(ngay_tra, ngay_hd, hom_nay):
    """THUẦN: ngày đã trả phải có, không sau hôm nay. Trả lỗi hoặc None."""
    n = str(ngay_tra or "")[:10]
    if len(n) != 10:
        return "Chọn ngày đã trả cho nhà cung cấp."
    if n > str(hom_nay)[:10]:
        return "Ngày đã trả không được sau hôm nay."
    return None


def dong_but_toan_truoc_erp(hd, tk_tam, so_tien, ttcp=None):
    """THUẦN: hai dòng Journal Entry. hd là dict có name, supplier, credit_to."""
    tien = float(_so(so_tien))
    no = {"account": hd["credit_to"], "party_type": "Supplier", "party": hd["supplier"],
        "debit_in_account_currency": tien, "reference_type": "Purchase Invoice",
        "reference_name": hd["name"]}
    co = {"account": tk_tam, "credit_in_account_currency": tien}
    if ttcp:
        no["cost_center"] = ttcp
        co["cost_center"] = ttcp
    return [no, co]


def _vai_lap_truoc_erp():
    from vagabond import ho_so_tt as hs
    return hs.VAI_LAP | hs.VAI_FIN


def _la_ke_toan():
    from vagabond import ho_so_tt as hs
    return bool(hs.VAI_FIN & hs._vai())


def _tk_tam(cong_ty):
    ds = frappe.get_all("Account", filters={"company": cong_ty, "account_type": "Temporary",
        "is_group": 0, "disabled": 0}, pluck="name", order_by="name")
    if len(ds) != 1:
        frappe.throw("Công ty %s cần đúng một tài khoản tạm (loại Temporary) để ghi khoản đã trả "
            "trước khi lên ERP; đang có %s. Báo kế toán kiểm danh mục tài khoản." % (cong_ty, len(ds)))
    return ds[0]


def _cho_duyet(hoa_don):
    """Bút toán nháp của luồng này đang treo trên hóa đơn: [(tên, tiền)]."""
    rows = frappe.db.sql("""select je.name, sum(a.debit_in_account_currency)
        from `tabJournal Entry` je join `tabJournal Entry Account` a on a.parent = je.name
        where je.docstatus = 0 and a.reference_type = 'Purchase Invoice' and a.reference_name = %s
          and je.user_remark like %s
        group by je.name order by je.creation""", (hoa_don, DAU_TRUOC_ERP + "%"))
    return [(r[0], float(r[1] or 0)) for r in rows]


def _hd_truoc_erp(hoa_don):
    from vagabond import ho_so_tt as hs
    hs._kiem(_vai_lap_truoc_erp(), "ghi khoản đã trả trước khi lên ERP")
    hd = frappe.get_doc("Purchase Invoice", hoa_don)
    hd.check_permission("read")
    if hd.docstatus != 1 or hd.is_return:
        frappe.throw("Chọn hóa đơn mua thường đã ghi sổ.")
    if hd.currency != "VND" or (frappe.db.get_value("Account", hd.credit_to, "account_currency") or "VND") != "VND":
        frappe.throw("Hóa đơn ngoại tệ: kế toán xử lý ở Đối chiếu thanh toán lõi.")
    return hd


@frappe.whitelist()
def xem_truoc_erp(hoa_don):
    """Màn khai khoản đã trả trước ERP: dư, phần đang chờ duyệt, ai được duyệt."""
    hd = _hd_truoc_erp(hoa_don)
    cho = _cho_duyet(hd.name)
    return {"hoa_don": hd.name, "ncc": hd.supplier, "ten_ncc": hd.supplier_name,
        "con_no": float(hd.outstanding_amount), "cho_duyet": [{"je": j, "so_tien": t} for j, t in cho],
        "dang_cho": sum(t for _, t in cho), "ke_toan": _la_ke_toan(), "tk_tam": _tk_tam(hd.company)}


@frappe.whitelist(methods=["POST"])
def lap_truoc_erp(hoa_don, so_tien, ngay_tra, unc=None, ghi_chu="", ma_lan=""):
    """Thu mua lập nháp chờ kế toán duyệt; kế toán lập thì ghi sổ luôn.

    ma_lan chống bấm hai lần khi mất phản hồi: cùng mã thì trả lại bút toán cũ."""
    from frappe.utils import nowdate
    from vagabond import tep_dinh_kem
    hd = _hd_truoc_erp(hoa_don)
    ma_lan = str(ma_lan or "").strip()[:60]
    if ma_lan:
        cu = frappe.db.get_value("Journal Entry", {"cheque_no": ma_lan, "docstatus": ["<", 2]},
            ["name", "docstatus"], as_dict=True)
        if cu:
            return {"je": cu.name, "da_ghi_so": cu.docstatus == 1, "da_lam_roi": 1}
    frappe.db.sql("select name from `tabPurchase Invoice` where name=%s for update", hd.name)
    hd.reload()
    loi = kiem_ngay_tra(ngay_tra, hd.bill_date or hd.posting_date, nowdate()) or \
        kiem_so_tien_truoc_erp(so_tien, hd.outstanding_amount, sum(t for _, t in _cho_duyet(hd.name)))
    if loi:
        frappe.throw(loi)
    urls = tep_dinh_kem.doc_ds(unc)
    ke_toan = _la_ke_toan()
    if not urls and not ke_toan:
        frappe.throw("Đính UNC hoặc phiếu chi của khoản đã trả để kế toán duyệt.")
    ttcp = frappe.db.get_value("Company", hd.company, "cost_center")
    je = frappe.new_doc("Journal Entry")
    je.voucher_type = "Journal Entry"
    je.company = hd.company
    je.posting_date = nowdate()
    je.cheque_no = ma_lan or None
    je.cheque_date = str(ngay_tra)[:10] if ma_lan else None
    je.user_remark = "%s Cấn hóa đơn %s (HĐ %s) của %s, đã trả ngày %s. %s" % (
        DAU_TRUOC_ERP, hd.name, hd.bill_no or "", hd.supplier_name, str(ngay_tra)[:10], (ghi_chu or "").strip()[:300])
    for r in dong_but_toan_truoc_erp({"name": hd.name, "supplier": hd.supplier, "credit_to": hd.credit_to},
            _tk_tam(hd.company), so_tien, ttcp):
        je.append("accounts", r)
    je.flags.ignore_permissions = True
    je.insert(ignore_permissions=True)
    if urls:
        da = tep_dinh_kem.gan_vao("Journal Entry", je.name, "unc_truoc_erp", urls)
        if len(da) != len(urls):
            frappe.throw("Có tệp UNC không còn tồn tại. Chọn lại tệp rồi gửi.")
    if ke_toan:
        je.submit()
    je.add_comment("Comment", "Lập từ màn Công nợ phải trả: khoản đã trả trước khi lên ERP%s." % (
        ", kế toán ghi sổ luôn" if ke_toan else ", chờ kế toán duyệt"))
    return {"je": je.name, "da_ghi_so": je.docstatus == 1}


@frappe.whitelist(methods=["POST"])
def duyet_truoc_erp(je):
    """Kế toán duyệt bút toán nháp của luồng này. Kiểm lại dư tại lúc duyệt."""
    from vagabond import ho_so_tt as hs
    hs._kiem(hs.VAI_FIN, "duyệt khoản đã trả trước khi lên ERP")
    doc = frappe.get_doc("Journal Entry", je)
    if not (doc.user_remark or "").startswith(DAU_TRUOC_ERP):
        frappe.throw("Bút toán này không thuộc luồng khoản đã trả trước khi lên ERP.")
    if doc.docstatus == 1:
        return {"je": doc.name, "da_ghi_so": True, "da_lam_roi": 1}
    if doc.docstatus != 0:
        frappe.throw("Bút toán đã hủy.")
    doc.check_permission("submit")
    doc.submit()
    return {"je": doc.name, "da_ghi_so": True}


@frappe.whitelist(methods=["POST"])
def bo_truoc_erp(je):
    """Kế toán từ chối hoặc người lập rút lại một bút toán NHÁP của luồng này."""
    from vagabond import ho_so_tt as hs
    doc = frappe.get_doc("Journal Entry", je)
    if not (doc.user_remark or "").startswith(DAU_TRUOC_ERP) or doc.docstatus != 0:
        frappe.throw("Chỉ bỏ được bút toán nháp của luồng khoản đã trả trước khi lên ERP.")
    if doc.owner != frappe.session.user:
        hs._kiem(hs.VAI_FIN, "từ chối khoản đã trả trước khi lên ERP")
    frappe.delete_doc("Journal Entry", doc.name, ignore_permissions=True)
    return {"ok": 1}
