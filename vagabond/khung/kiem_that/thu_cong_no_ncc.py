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
