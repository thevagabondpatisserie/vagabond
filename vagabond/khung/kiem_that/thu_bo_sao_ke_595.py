"""A1: chứng minh khả năng phân bổ của lõi, chưa thay nghiệm thu cửa app.

Chỉ fixture trong savepoint của bench, không gọi API ngân hàng hay sửa APP cũ.
"""
import frappe
from frappe.utils import today
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua, _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi, _giao_dich
from vagabond.khung.kiem_that.thu_phieu_thu_unc_534 import _Tep


def _pe(tien, ba):
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    hd = _hoa_don_mua(tien)
    pe = get_payment_entry("Purchase Invoice", hd.name, party_amount=tien, bank_account=ba.account)
    pe.bank_account = ba.name
    pe.reference_no = "KT595-" + frappe.generate_hash(length=8)
    pe.reference_date = today()
    pe.insert(ignore_permissions=True)
    _DA_TAO.append((pe.doctype, pe.name))
    with _Tep(pe.name):
        pe.submit()
    pe.reload()
    gl = frappe.get_all("GL Entry", filters={"voucher_type": pe.doctype,
        "voucher_no": pe.name, "is_cancelled": 0}, fields=["debit", "credit"])
    dung("PE có GL thật", bool(gl))
    la("GL cân", sum(float(d.debit)-float(d.credit) for d in gl), 0)
    hd.reload()
    la("hoá đơn hết nợ", float(hd.outstanding_amount), 0)
    return pe


def _noi(g, pe):
    g.add_payment_entries([{"payment_doctype": "Payment Entry", "payment_name": pe.name}])
    g.save(ignore_permissions=True)
    g.reload()


@ca("#595 lõi một Payment Entry phân bổ đủ hai Bank Transaction, huỷ trả cả hai")
def _():
    from vagabond.khung.kiem_that.nen import cong_ty
    ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cong_ty()))
    pe = _pe(714138056, ba)
    a = _giao_dich(ba.name, 450000000, "KT595 tách lệnh A")
    b = _giao_dich(ba.name, 264138056, "KT595 tách lệnh B")
    for g, tien in ((a,450000000), (b,264138056)):
        _noi(g, pe)
        la("một liên kết", len(g.payment_entries), 1)
        la("đúng PE", g.payment_entries[0].payment_entry, pe.name)
        la("phân bổ đúng phần", float(g.payment_entries[0].allocated_amount), tien)
        la("BT hết phần", float(g.unallocated_amount), 0)
    pe.reload()
    la("clearance khi đủ bộ", str(pe.clearance_date), str(b.date))
    pe.cancel()
    for g in (a,b):
        g.reload()
        la("huỷ gỡ đủ bộ", len(g.payment_entries), 0)
        la("hoàn tiền khả dụng", float(g.unallocated_amount), float(g.withdrawal))


@ca("#595 lõi một Bank Transaction phân bổ hai Payment Entry không nhân đôi tiền")
def _():
    from vagabond.khung.kiem_that.nen import cong_ty
    ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cong_ty()))
    a, b = _pe(60000, ba), _pe(40000, ba)
    g = _giao_dich(ba.name,100000,"KT595 trả hai phiếu")
    _noi(g,a)
    la("còn phần cho phiếu hai",float(g.unallocated_amount),40000)
    _noi(g,b)
    la("hai liên kết",len(g.payment_entries),2)
    la("tổng không vượt giao dịch",sum(float(d.allocated_amount) for d in g.payment_entries),100000)
    la("không còn phần cho phiếu ba",float(g.unallocated_amount),0)


@ca("#476 APP tự dò hai dòng cùng mã, một PE và hai phân bổ lõi qua cửa thanh toán")
def _():
    from vagabond import ho_so_tt as hs, doi_chieu_app as dc
    from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _ho_so_ncc, _unc_gia, _giao_dich_ngan_hang
    hd=_hoa_don_mua(714138056)
    h=_ho_so_ncc([hd]); _unc_gia(h)
    a=_giao_dich_ngan_hang(h.name,450000000,hd.company)
    b=_giao_dich_ngan_hang(h.name,264138056,hd.company)
    hs.danh_dau_da_tra(h.name,gui_thu=0)
    bo=hs._but_toan_cua_ho_so(h.name)
    _DA_TAO.extend((p["doctype"],p["name"]) for p in bo)
    la("một PE",len(bo),1)
    for g,tien in ((a,450000000),(b,264138056)):
        g.reload()
        la("BT hết phần",float(g.unallocated_amount),0)
        la("phân bổ đúng dòng",float(g.payment_entries[0].allocated_amount),tien)
        la("cùng PE",g.payment_entries[0].payment_entry,bo[0]["name"])
    la("retry không thêm phiếu",hs.danh_dau_da_tra(h.name,gui_thu=0)["da_lam_roi"],1)


@ca("#476 APP chọn bộ bằng payload màn hình, bỏ nối nhả đủ các dòng đang giữ")
def _():
    import json
    from vagabond import doi_chieu_app as dc, bo_sao_ke_db as bs
    from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _ho_so_ncc, _giao_dich_ngan_hang
    hd=_hoa_don_mua(100000);h=_ho_so_ncc([hd])
    a=_giao_dich_ngan_hang("KT476-KHONGMA",60000,hd.company)
    b=_giao_dich_ngan_hang("KT476-KHONGMA",40000,hd.company)
    ds=[dict(name=a.name,phan_bo=60000),dict(name=b.name,phan_bo=40000)]
    dc.gan(h.name,json.dumps(ds));h.reload()
    la("giữ hai dòng",len(bs.doc_hien_tai(h)["dong"]),2)
    dc.bo(h.name);h.reload()
    la("bỏ đủ bộ",bs.doc_hien_tai(h)["dong"],[])
    for g in (a,b):
        g.reload()
        la("không ghi tiền ngân hàng",float(g.allocated_amount),0)


@ca("#476 APP một BT trả hai phiếu, phần giữ và phần lõi không bị trừ hai lần")
def _():
    import json
    from vagabond import doi_chieu_app as dc, bo_sao_ke_db as bs, ho_so_tt as hs
    from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _ho_so_ncc, _giao_dich_ngan_hang, _unc_gia
    a=_hoa_don_mua(60000);b=_hoa_don_mua(40000)
    h1=_ho_so_ncc([a]);h2=_ho_so_ncc([b]);_unc_gia(h1);_unc_gia(h2)
    g=_giao_dich_ngan_hang("KT476-CHIA",100000,a.company)
    for h,t in ((h1,60000),(h2,40000)):
        dc.gan(h.name,json.dumps([dict(name=g.name,phan_bo=t)]))
    for h in (h1,h2):
        hs.danh_dau_da_tra(h.name,gui_thu=0)
        _DA_TAO.extend((p["doctype"],p["name"]) for p in hs._but_toan_cua_ho_so(h.name))
    g.reload()
    la("hai PE thật",len(g.payment_entries),2)
    la("BT hết tiền",float(g.unallocated_amount),0)
    la("đúng hai phần",sorted(float(p.allocated_amount) for p in g.payment_entries),[40000,60000])


@ca("#476 đổi bộ APP chưa trả giữ bộ mới; chọn lỗi không làm mất bộ cũ")
def _():
    import json
    from vagabond import doi_chieu_app as dc, bo_sao_ke_db as bs
    from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _ho_so_ncc, _giao_dich_ngan_hang
    hd=_hoa_don_mua(100000);h=_ho_so_ncc([hd])
    a=_giao_dich_ngan_hang("KT476-CU",100000,hd.company)
    b=_giao_dich_ngan_hang("KT476-MOI",60000,hd.company)
    c=_giao_dich_ngan_hang("KT476-MOI",40000,hd.company)
    dc.gan(h.name,json.dumps([dict(name=a.name,phan_bo=100000)]))
    ds=[dict(name=b.name,phan_bo=60000),dict(name=c.name,phan_bo=40000)]
    dc.gan(h.name,json.dumps(ds));h.reload()
    la("đổi giữ bộ mới",bs.doc_hien_tai(h)["dong"],ds)
    la("mã tương thích",h.ma_giao_dich,b.name)
    la("dòng cũ rảnh",bs.con_lai(a,h),100000)
    frappe.db.savepoint("thu_bo_hong_476")
    try:
        dc.gan(h.name,json.dumps([dict(name=a.name,phan_bo=50000)]))
    except frappe.ValidationError:
        pass
    else:
        dung("bộ thiếu phải bị từ chối",False)
    frappe.db.rollback(save_point="thu_bo_hong_476")
    h.reload();la("rollback còn nguyên bộ mới",bs.doc_hien_tai(h)["dong"],ds)


@ca("#476 TTNB nhận hai lệnh từ MB cá nhân, retry không ghi hai lần")
def _():
    import json
    from vagabond import sepay, de_nghi_chi as dc, bo_sao_ke_db as bs
    from vagabond.khung.kiem_that.nen import mot_nha_cung_cap
    from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_ca_nhan, _so_thu, _phieu_cho_chi
    ba=_tai_khoan_ca_nhan(_so_thu(),mot_nha_cung_cap())
    sepay.them_tai_khoan(ba.bank_account_no,ba.name)
    h=_phieu_cho_chi(100000)
    a=_giao_dich(ba.name,60000,h.name);b=_giao_dich(ba.name,40000,h.name)
    ds=json.dumps([dict(name=a.name,phan_bo=60000),dict(name=b.name,phan_bo=40000)])
    k=dc.khop_tay(h.name,ds);h.reload()
    la("đã chi",h.trang_thai,dc.TT_DA_CHI)
    la("hai phần giữ",len(bs.doc_hien_tai(h)["dong"]),2)
    la("không lỗi bước sau",k["loi"],"")
    la("retry",dc.khop_tay(h.name,ds)["da_lam_roi"],1)


@ca("#476 TTNB tự dò bộ thay vì đòi từng dòng bằng tổng phiếu")
def _():
    from vagabond import sepay, de_nghi_chi as dc, bo_sao_ke_db as bs
    from vagabond.khung.kiem_that.nen import mot_nha_cung_cap
    from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_ca_nhan, _so_thu, _phieu_cho_chi
    ba=_tai_khoan_ca_nhan(_so_thu(),mot_nha_cung_cap())
    sepay.them_tai_khoan(ba.bank_account_no,ba.name)
    h=_phieu_cho_chi(100000)
    _giao_dich(ba.name,60000,h.name);g=_giao_dich(ba.name,40000,h.name)
    nguoi=frappe.session.user
    try:
        frappe.set_user("Guest")
        dc.khi_co_giao_dich(g.name)
    finally:
        frappe.set_user(nguoi)
    h.reload()
    la("webhook ghép hai dòng",h.trang_thai,dc.TT_DA_CHI)
    la("giữ cả bộ",len(bs.doc_hien_tai(h)["dong"]),2)


@ca("#476 hoàn tiền: chọn bộ sinh nháp đúng ngân hàng, submit mới phân bổ hai BT")
def _():
    import json
    from vagabond import sepay, hoan_tien as ht, don_huy
    from vagabond.khung.kiem_that.nen import cong_ty
    from vagabond.khung.kiem_that.thu_don_huy import _ho_so_thu
    ba=_tai_khoan_cong_ty_moi(_tk_ngan_hang(cong_ty()))
    sepay.them_tai_khoan(ba.bank_account_no,ba.name)
    h=_ho_so_thu(don_huy._khach_le_online());_DA_TAO.append((h.doctype,h.name))
    h.loai_hoan=ht.LOAI_HUY_PANCAKE;h.save(ignore_permissions=True)
    a=_giao_dich(ba.name,450000,h.noi_dung_ck);b=_giao_dich(ba.name,255000,h.noi_dung_ck)
    k=ht.khop_tay(h.name,json.dumps([dict(name=a.name,phan_bo=450000),dict(name=b.name,phan_bo=255000)]))
    h.reload()
    for ten in (h.phieu_chi,h.get("phieu_thu")):
        if ten:_DA_TAO.append(("Payment Entry",ten))
    la("không lỗi lập",k["loi"],"")
    dung("đã sinh phiếu chi",bool(h.phieu_chi))
    if not h.phieu_chi:return
    pe=frappe.get_doc("Payment Entry",h.phieu_chi)
    la("vẫn là nháp",pe.docstatus,0)
    la("đúng ngân hàng đã chọn",pe.bank_account,ba.name)
    la("đúng nguồn sổ cái",pe.paid_from,ba.account)
    with _Tep(pe.name):pe.submit()
    for g in (a,b):
        g.reload();la("đã phân bổ khi ghi sổ",float(g.unallocated_amount),0)
        la("liên kết đúng PE",g.payment_entries[0].payment_entry,pe.name)


@ca("#476 ngoại lệ: FIN không được bỏ SePay; Manager ghi kèm lý do rồi đối chiếu đủ mới hết chờ")
def _():
    from unittest.mock import patch
    from vagabond import ho_so_tt as hs, doi_chieu_app as dc
    from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _ho_so_ncc, _unc_gia, _giao_dich_ngan_hang
    hd=_hoa_don_mua(100000);h=_ho_so_ncc([hd]);_unc_gia(h)
    for vai in ("Accounts User","AP Kiểm soát (FIN)"):
        frappe.db.savepoint("ngoai_le476")
        try:
            with patch.object(frappe,"get_roles",return_value=[vai]):
                hs.danh_dau_da_tra(h.name,gui_thu=0,ly_do_som="Sao kê về chậm")
        except frappe.ValidationError:
            pass
        else:
            dung("vai không có ngoại lệ phải bị từ chối",False)
        frappe.db.rollback(save_point="ngoai_le476")
        h.reload();la("chưa trả",h.trang_thai,hs.TT_DA_DUYET)
    with patch.object(frappe,"get_roles",return_value=["Accounts Manager"]):
        hs.danh_dau_da_tra(h.name,gui_thu=0,ly_do_som="Sao kê về chậm, có UNC")
    _DA_TAO.extend((p["doctype"],p["name"]) for p in hs._but_toan_cua_ho_so(h.name))
    h.reload();la("đã ghi có vết",h.vgb_tt_ly_do_som,"Sao kê về chậm, có UNC")
    la("đang chờ đối chiếu sau",hs._cho_doi_chieu_sau(h),True)
    g=_giao_dich_ngan_hang(h.name,100000,hd.company)
    dc.gan(h.name,g.name);h.reload()
    la("đủ phân bổ mới hết chờ",hs._cho_doi_chieu_sau(h),False)
    la("lịch sử lý do còn nguyên",h.vgb_tt_ly_do_som,"Sao kê về chậm, có UNC")


@ca("#476 một PE dùng hai phần lẻ của hai BT đang có phiếu khác giữ, không chiếm phần giữ")
def _():
    import json
    from vagabond import doi_chieu_app as dc, ho_so_tt as hs, bo_sao_ke_db as bs
    from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _ho_so_ncc, _unc_gia, _giao_dich_ngan_hang
    hd1=_hoa_don_mua(60000);hd2=_hoa_don_mua(60000);hd3=_hoa_don_mua(80000)
    h1=_ho_so_ncc([hd1]);h2=_ho_so_ncc([hd2]);h3=_ho_so_ncc([hd3])
    for h in (h1,h2,h3):_unc_gia(h)
    a=_giao_dich_ngan_hang("KT476-CHIA-A",100000,hd1.company)
    b=_giao_dich_ngan_hang("KT476-CHIA-B",100000,hd1.company)
    dc.gan(h1.name,json.dumps([dict(name=a.name,phan_bo=60000)]))
    dc.gan(h2.name,json.dumps([dict(name=b.name,phan_bo=60000)]))
    dc.gan(h3.name,json.dumps([dict(name=a.name,phan_bo=40000),dict(name=b.name,phan_bo=40000)]))
    hs.danh_dau_da_tra(h3.name,gui_thu=0)
    bo=hs._but_toan_cua_ho_so(h3.name)
    _DA_TAO.extend((p["doctype"],p["name"]) for p in bo)
    la("một PE cho hai phần lẻ",len(bo),1)
    for g in (a,b):
        g.reload();la("lõi chỉ dùng phần của hồ sơ ba",float(g.allocated_amount),40000)
        la("lõi còn đủ 60.000",float(g.unallocated_amount),60000)
    for h in (h1,h2):
        hs.danh_dau_da_tra(h.name,gui_thu=0)
        _DA_TAO.extend((p["doctype"],p["name"]) for p in hs._but_toan_cua_ho_so(h.name))
    for g in (a,b):
        g.reload();la("hai phiếu dùng đúng 100.000",float(g.allocated_amount),100000)
        la("hai liên kết",len(g.payment_entries),2)
