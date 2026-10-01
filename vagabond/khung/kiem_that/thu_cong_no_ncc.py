"""#402: dư/UNC/phân bổ trên chứng từ thật; hoàn nguyên bởi khung bench."""
import frappe
from frappe.utils import today
from vagabond import cong_no_ncc as cn, coc_app
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO
from vagabond.khung.kiem_that.thu_phan_bo_app import _coc
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua


@ca("#402 UNC không giảm nợ; cấn một phần, retry và hủy trả lại dư")
def _unc_can():
    hd, pe, _ = _coc()
    ds = cn.khoan_da_tra(hd.name)
    dung("đọc đúng khoản cọc", pe.name in [r["name"] for r in ds["rows"]])
    f = frappe.get_doc({"doctype":"File","file_name":"UNC-402-%s.txt" % frappe.generate_hash(length=6),
        "content":"Bang chung thu tren bench 402", "is_private":1}).insert(ignore_permissions=True)
    _DA_TAO.append((f.doctype,f.name))
    gl = frappe.db.count("GL Entry", {"voucher_no":pe.name})
    cn.luu_unc(hd.name, pe.name, frappe.as_json([f.file_url]))
    cn.luu_unc(hd.name, pe.name, frappe.as_json([f.file_url]))
    pe.reload();hd.reload();f.reload()
    la("UNC không làm giảm nợ",float(hd.outstanding_amount),10000000.)
    la("UNC không sinh GL",frappe.db.count("GL Entry",{"voucher_no":pe.name}),gl)
    la("tệp gắn vào khoản đã trả",f.attached_to_name,pe.name)
    from vagabond.tep_dinh_kem import doc_ds
    la("retry không nhân UNC",doc_ds(pe.vgb_chi_unc).count(f.file_url),1)
    args=dict(ncc=hd.supplier,payment_entry=pe.name,hoa_don=[dict(hoa_don=hd.name,so_tien=1000000)],ma_lan="CC-402-"+frappe.generate_hash(length=12))
    r=coc_app.can_coc(**args);dung("cấn được",r.get("ok"))
    r=coc_app.can_coc(**args);dung("nhận lại lần cũ",r.get("da_lam_roi"))
    hd.reload();la("chỉ giảm một lần",float(hd.outstanding_amount),9000000.)
    la("không sinh GL chi thứ hai",frappe.db.count("GL Entry",{"voucher_no":pe.name}),gl)
    k=cn.danh_sach(cong_ty=hd.company,tu_khoa=hd.name)
    la("màn đọc lại dư",float(k["dong"][0]["con_no"]),9000000.)
    pe.reload();pe.cancel();hd.reload()
    la("hủy trả lại công nợ",float(hd.outstanding_amount),10000000.)


@ca("#402 PI USD tài khoản VND: dư lấy tiền tài khoản, không nhầm 100 USD thành 100 VND")
def _ngoai_te():
    goc=_hoa_don_mua(100)
    hd=frappe.copy_doc(goc)
    hd.currency="USD"
    hd.conversion_rate=25000
    hd.buying_price_list=None
    hd.price_list_currency="USD"
    hd.plc_conversion_rate=25000
    hd.bill_no="KIEM-402-USD-"+frappe.generate_hash(length=6)
    hd.flags.ignore_permissions=True
    hd.insert(ignore_permissions=True);_DA_TAO.append((hd.doctype,hd.name));hd.submit();hd.reload()
    la("tiền tài khoản",hd.party_account_currency,"VND")
    la("100 USD",float(hd.grand_total),100.)
    la("dư do lõi ghi bằng VND",float(hd.outstanding_amount),2500000.)
    k=cn.danh_sach(cong_ty=hd.company,tu_khoa=hd.name)
    la("nhãn VND đúng số",k["tong_theo_tien"],{"VND":2500000.})
    la("chưa phân bổ không giảm một phần",k["dem"]["mot_phan"],0)


@ca("#402 Accounts User đọc màn/Excel cùng quyền, Guest không có cửa đính UNC")
def _quyen():
    hd=_hoa_don_mua(120000)
    truoc=frappe.session.user
    u=frappe.get_doc({"doctype":"User","email":"kiem402-%s@example.invalid" % frappe.generate_hash(length=8),
        "first_name":"Kiểm công nợ","enabled":1,"send_welcome_email":0,
        "roles":[{"role":"Accounts User"}]}).insert(ignore_permissions=True)
    _DA_TAO.append((u.doctype,u.name))
    try:
        frappe.set_user(u.name)
        k=cn.danh_sach(cong_ty=hd.company,tu_khoa=hd.name)
        la("kế toán đọc đủ",len(k["dong"]),1)
        _,_,ds=cn.xuat_ds(cong_ty=hd.company,tu_khoa=hd.name)
        la("Excel cùng hóa đơn",ds[0]["name"],hd.name)
        frappe.set_user("Guest")
        try:
            cn.luu_unc(hd.name,"KHONG-CO",'[]')
            dung("Guest phải bị từ chối",False)
        except (frappe.PermissionError,frappe.ValidationError):
            pass
    finally:
        frappe.set_user(truoc)


def _tk_tam(cty):
    """Tài khoản tạm (Temporary) của công ty bench; site thật có sẵn, bench có
    thể chưa có thì dựng một cái dưới nhóm Nợ phải trả."""
    ds = frappe.get_all("Account", filters={"company": cty, "account_type": "Temporary", "is_group": 0, "disabled": 0}, pluck="name")
    if ds:
        return ds[0]
    cha = frappe.get_all("Account", filters={"company": cty, "is_group": 1, "root_type": "Liability"}, pluck="name", order_by="lft desc", limit=1)
    tk = frappe.get_doc({"doctype": "Account", "account_name": "Tam cho xu ly dau ky 549", "company": cty,
        "parent_account": cha[0], "account_type": "Temporary", "is_group": 0}).insert(ignore_permissions=True)
    _DA_TAO.append((tk.doctype, tk.name))
    return tk.name


@ca("v549 hóa đơn trả trước khi lên ERP: thu mua gửi nháp không giảm nợ, kế toán duyệt mới giảm; Có tài khoản tạm, không đụng ngân hàng")
def _tra_truoc_erp():
    hd = _hoa_don_mua(1000000)
    tam = _tk_tam(hd.company)
    truoc = frappe.session.user
    u = frappe.get_doc({"doctype": "User", "email": "kiem549-%s@example.invalid" % frappe.generate_hash(length=8),
        "first_name": "Thu mua 549", "enabled": 1, "send_welcome_email": 0,
        "roles": [{"role": "Purchase User"}]}).insert(ignore_permissions=True)
    _DA_TAO.append((u.doctype, u.name))
    try:
        frappe.set_user(u.name)
        f = frappe.get_doc({"doctype": "File", "file_name": "UNC-549-%s.txt" % frappe.generate_hash(length=6),
            "content": "UNC tra truoc ERP", "is_private": 1}).insert(ignore_permissions=True)
        _DA_TAO.append((f.doctype, f.name))
        try:
            cn.lap_truoc_erp(hd.name, 400000, "2026-04-10", "[]", "", "TE-549-a-" + frappe.generate_hash(length=6))
            dung("thu mua thiếu UNC phải bị chặn", False)
        except frappe.ValidationError:
            pass
        ma = "TE-549-" + frappe.generate_hash(length=10)
        k = cn.lap_truoc_erp(hd.name, 400000, "2026-04-10", frappe.as_json([f.file_url]), "Printeco tháng 4", ma)
        _DA_TAO.append(("Journal Entry", k["je"]))
        la("thu mua chỉ lập nháp", k["da_ghi_so"], False)
        k2 = cn.lap_truoc_erp(hd.name, 400000, "2026-04-10", frappe.as_json([f.file_url]), "", ma)
        la("bấm lại cùng mã trả bút toán cũ", (k2["je"], k2.get("da_lam_roi")), (k["je"], 1))
        hd.reload()
        la("nháp chưa giảm nợ", float(hd.outstanding_amount), 1000000.)
        try:
            cn.lap_truoc_erp(hd.name, 700000, "2026-04-10", frappe.as_json([f.file_url]), "", "TE-549-b-" + frappe.generate_hash(length=6))
            dung("vượt dư trừ phần chờ duyệt phải bị chặn", False)
        except frappe.ValidationError:
            pass
        dong = cn.danh_sach(cong_ty=hd.company, tu_khoa=hd.name)["dong"][0]
        c = dong["cho_duyet"]
        la("màn thấy phần chờ duyệt", [(x["je"], x["so_tien"]) for x in c], [(k["je"], 400000.)])
        # Codex #403 vòng 3: kế toán thấy bằng chứng ngay trên dòng.
        la("UNC hiện trên dòng chờ", c[0]["unc"], [f.file_url])
        la("ngày đã trả", c[0]["ngay_tra"], "2026-04-10")
        dung("có người gửi và lúc gửi", bool(c[0]["nguoi_gui"]) and bool(c[0]["luc_gui"]))
        dung("có ghi chú", "Printeco tháng 4" in c[0]["dien_giai"])
        try:
            cn.duyet_truoc_erp(k["je"])
            dung("thu mua không tự duyệt được", False)
        except frappe.ValidationError:
            pass
    finally:
        frappe.set_user(truoc)
    r = cn.duyet_truoc_erp(k["je"])
    dung("kế toán duyệt ghi sổ", r["da_ghi_so"])
    hd.reload()
    la("duyệt xong mới giảm nợ", float(hd.outstanding_amount), 600000.)
    gl = frappe.get_all("GL Entry", filters={"voucher_no": k["je"], "is_cancelled": 0}, fields=["account", "debit", "credit"])
    la("chỉ hai tài khoản: công nợ và tạm", sorted(g.account for g in gl), sorted([hd.credit_to, tam]))
    la("Có tài khoản tạm đúng tiền", sum(g.credit for g in gl if g.account == tam), 400000.)
    la("UNC gắn vào bút toán", frappe.db.get_value("File", f.name, "attached_to_name"), k["je"])
    # Kế toán tự lập thì ghi sổ luôn, không cần UNC; nháp thứ hai thì bỏ được.
    k3 = cn.lap_truoc_erp(hd.name, 100000, "2026-04-11", "[]", "", "TE-549-c-" + frappe.generate_hash(length=6))
    _DA_TAO.append(("Journal Entry", k3["je"]))
    dung("kế toán lập là ghi sổ", k3["da_ghi_so"])
    hd.reload()
    la("dư còn lại", float(hd.outstanding_amount), 500000.)
    je = frappe.get_doc("Journal Entry", k3["je"])
    je.cancel()
    hd.reload()
    la("hủy bút toán trả lại công nợ", float(hd.outstanding_amount), 600000.)


@ca("v549 Codex #403: duyệt kiểm dư sống lúc duyệt; từ chối giữ bản ghi, không xóa")
def _duyet_du_song_va_tu_choi():
    hd = _hoa_don_mua(1000000)
    tam = _tk_tam(hd.company)
    truoc = frappe.session.user
    u = frappe.get_doc({"doctype": "User", "email": "kiem549b-%s@example.invalid" % frappe.generate_hash(length=8),
        "first_name": "Thu mua 549b", "enabled": 1, "send_welcome_email": 0,
        "roles": [{"role": "Purchase User"}]}).insert(ignore_permissions=True)
    _DA_TAO.append((u.doctype, u.name))
    try:
        frappe.set_user(u.name)
        f = frappe.get_doc({"doctype": "File", "file_name": "UNC-549b-%s.txt" % frappe.generate_hash(length=6),
            "content": "UNC", "is_private": 1}).insert(ignore_permissions=True)
        _DA_TAO.append((f.doctype, f.name))
        k = cn.lap_truoc_erp(hd.name, 400000, "2026-04-10", frappe.as_json([f.file_url]), "", "TE-549-d-" + frappe.generate_hash(length=6))
        _DA_TAO.append(("Journal Entry", k["je"]))
    finally:
        frappe.set_user(truoc)
    # Một chứng từ khác (ngoài luồng này) giảm dư 800.000 sau khi Uyên gửi.
    je = frappe.new_doc("Journal Entry")
    je.company = hd.company
    je.posting_date = today()
    je.user_remark = "Ca kiểm 549: chứng từ khác giảm dư"
    for r in cn.dong_but_toan_truoc_erp({"name": hd.name, "supplier": hd.supplier, "credit_to": hd.credit_to}, tam, 800000,
            frappe.db.get_value("Company", hd.company, "cost_center")):
        je.append("accounts", r)
    je.insert(ignore_permissions=True)
    _DA_TAO.append((je.doctype, je.name))
    je.submit()
    hd.reload()
    la("dư sau chứng từ khác", float(hd.outstanding_amount), 200000.)
    try:
        cn.duyet_truoc_erp(k["je"])
        dung("duyệt vượt dư sống phải bị chặn", False)
    except frappe.ValidationError as e:
        dung("lỗi nói rõ không duyệt được", "Không duyệt được" in str(e))
    la("nháp vẫn là nháp", frappe.db.get_value("Journal Entry", k["je"], "docstatus"), 0)
    cn.bo_truoc_erp(k["je"])
    dung("từ chối không xóa bút toán", bool(frappe.db.exists("Journal Entry", k["je"])))
    dung("đánh dấu đã bỏ", frappe.db.get_value("Journal Entry", k["je"], "user_remark").startswith(cn.DAU_DA_BO))
    la("UNC vẫn gắn bút toán", frappe.db.get_value("File", f.name, "attached_to_name"), k["je"])
    la("ra khỏi phần chờ duyệt", cn.danh_sach(cong_ty=hd.company, tu_khoa=hd.name)["dong"][0]["cho_duyet"], [])
    try:
        cn.duyet_truoc_erp(k["je"])
        dung("không duyệt được nháp đã bỏ", False)
    except frappe.ValidationError:
        pass
    je.cancel()
