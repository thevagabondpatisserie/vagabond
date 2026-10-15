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
    from vagabond import bo_sao_ke_luong as luong
    from unittest.mock import patch
    with patch.object(frappe,'get_roles',return_value=['Sales User']):
        try:luong.bo('ttnb',h.name)
        except frappe.ValidationError:pass
        else:dung('Sales không được bỏ bộ',False)
    h.reload();la('chặn giữ nguyên bộ',len(bs.doc_hien_tai(h)['dong']),2)
    luong.bo('ttnb',h.name);h.reload()
    la('về chờ chi',h.trang_thai,dc.TT_HOAN_TAT)
    la('bỏ cả hai phần',bs.doc_hien_tai(h)['dong'],[])
    la('bỏ lần nữa không lỗi',luong.bo('ttnb',h.name)['da_lam_roi'],1)
    for g in (a,b):
        g.reload();la('lõi không bị giả ghi sổ',len(g.payment_entries),0)
        la('không còn giữ',bs.con_lai(g,h),float(g.withdrawal))



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
    from vagabond import bo_sao_ke_luong as luong, bo_sao_ke_db as bs
    try:luong.bo('hoan_tien',h.name)
    except frappe.ValidationError:pass
    else:dung('nháp còn sống phải chặn bỏ',False)
    with _Tep(pe.name):pe.submit()
    for g in (a,b):
        g.reload();la("đã phân bổ khi ghi sổ",float(g.unallocated_amount),0)
        la("liên kết đúng PE",g.payment_entries[0].payment_entry,pe.name)
    try:luong.bo('hoan_tien',h.name)
    except frappe.ValidationError:pass
    else:dung('đã ghi sổ phải chặn bỏ',False)
    pe.reload()  # Lõi cập nhật clearance_date sau submit, lấy bản mới trước hủy.
    pe.cancel()
    h.reload()
    la("PE hủy không tự đổi trạng thái hồ sơ",h.trang_thai,"Da chi")
    luong.bo('hoan_tien',h.name);h.reload()
    la('bỏ cả bộ sau huỷ lõi',bs.doc_hien_tai(h)['dong'],[])
    la('về chờ chi',h.trang_thai,'Cho chi')
    la('không giả đã khớp',int(h.da_doi_soat),0)



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


@ca('#476 hoàn ứng: TTNB hai lệnh giữ cùng chủ; một BT hai TTNB hoàn qua hai APP không nhân tiền')
def _():
    import json
    from vagabond import sepay, de_nghi_chi as dc, ho_so_tt as hs, bo_sao_ke_luong as bl
    from vagabond.khung.kiem_that.nen import mot_nha_cung_cap
    from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_ca_nhan, _so_thu, _phieu_cho_chi
    ba=_tai_khoan_ca_nhan(_so_thu(),mot_nha_cung_cap())
    sepay.them_tai_khoan(ba.bank_account_no,ba.name)
    def app(p,tien,gd):
        r=hs.tao_hoan_ung(tk_hoan=ba.name,dong=[dict(ngay_hd=today(),noi_dung='Kiểm bộ hoàn ứng',
            so_tien=tien,ma_giao_dich=gd,de_nghi_chi=p.name)],gui_luon=0)
        h=frappe.get_doc('Vagabond Ho So TT',r['ma']);_DA_TAO.append((h.doctype,h.name));return h
    p=_phieu_cho_chi(100000)
    a=_giao_dich(ba.name,60000,p.name);b=_giao_dich(ba.name,40000,p.name)
    dc.khop_tay(p.name,json.dumps([dict(name=a.name,phan_bo=60000),dict(name=b.name,phan_bo=40000)]))
    h=app(p,100000,a.name)
    la('tổng khoản theo bộ',float(h.dong[0].so_tien),100000)
    la('không giả công ty đã chi',h.ma_giao_dich or '', '')
    try:bl.bo('ttnb',p.name)
    except frappe.ValidationError as e:dung('chỉ APP phải gỡ trước',h.name in str(e))
    else:dung('không bỏ chứng cứ đang dùng',False)
    g=_giao_dich(ba.name,100000,'KT476-CHIA-HOAN')
    hs_moi=[]
    for tien in (60000,40000):
        p=_phieu_cho_chi(tien)
        dc.khop_tay(p.name,json.dumps([dict(name=g.name,phan_bo=tien)]))
        hs_moi.append(app(p,tien,g.name))
    la('hai hồ sơ đúng 100.000',sum(float(h.dong[0].so_tien) for h in hs_moi),100000)
    g.reload();la('chưa sinh bút toán công ty từ chứng cứ nhân viên',len(g.payment_entries),0)
    frappe.db.savepoint('cam_hoan_trung476')
    try:
        hs.tao_hoan_ung(tk_hoan=ba.name,dong=[dict(ngay_hd=today(),noi_dung='Không được hoàn lại',so_tien=100000,ma_giao_dich=g.name)],gui_luon=0)
    except frappe.ValidationError:pass
    else:dung('không đi vòng bỏ TTNB để hoàn lần nữa',False)
    finally:frappe.db.rollback(save_point='cam_hoan_trung476')
    hs.duyet(hs_moi[0].name,'tu_choi',ly_do='Ca kiểm hủy đề nghị hoàn, vẫn giữ chứng cứ TTNB đã chi')
    hs_moi[0].reload();la('APP hoàn ứng từ chối được',hs_moi[0].trang_thai,'Tu choi')


@ca('#476 APP từ chối và hủy nhả toàn bộ qua cửa duyệt thật, phiếu sau dùng được')
def _():
    import json
    from vagabond import doi_chieu_app as dc, bo_sao_ke_db as bs, ho_so_tt as hs
    from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _ho_so_ncc, _giao_dich_ngan_hang
    for buoc in ('tu_choi','huy'):
        hd=_hoa_don_mua(100000);h=_ho_so_ncc([hd])
        a=_giao_dich_ngan_hang('KT476-NHA',60000,hd.company)
        b=_giao_dich_ngan_hang('KT476-NHA',40000,hd.company)
        ds=[dict(name=a.name,phan_bo=60000),dict(name=b.name,phan_bo=40000)]
        dc.gan(h.name,json.dumps(ds))
        hs.duyet(h.name,buoc,ly_do='Ca kiểm nhả bộ sau từ chối/hủy')
        h.reload();la('nhả cả bộ',bs.doc_hien_tai(h)['dong'],[])
        la('bỏ mã cùng transaction',h.ma_giao_dich or '','')
        h2=_ho_so_ncc([_hoa_don_mua(100000)])
        dc.gan(h2.name,json.dumps(ds));h2.reload()
        la('phiếu sau giữ được cả hai dòng',len(bs.doc_hien_tai(h2)['dong']),2)


@ca('#476 lõi ghi từng PE công nợ qua hai BT: PE nháp giữ phần, retry và hủy')
def _():
    from vagabond.khung.kiem_that.thu_gom_phap_nhan_576 import _nen,_hd,_khach,_phieu
    from vagabond.khung.kiem_that.thu_khop_tay_gop_571 import _gd
    from vagabond import bo_sao_ke_db as bs, thu_tien as tt
    from frappe.utils import flt
    cty,tk,_mau=_nen()
    a,b=_hd(tk,cty,60000,_khach('476A')),_hd(tk,cty,40000,_khach('476B'))
    p=_phieu([a,b],a.customer)
    ba=_tai_khoan_cong_ty_moi(_tk_ngan_hang(cty))
    from vagabond import sepay
    sepay.them_tai_khoan(ba.bank_account_no,ba.name)
    tong=flt(a.grand_total)+flt(b.grand_total)
    so_a=1  # PE đầu chắc chắn cần phần ở BT thứ hai, không phụ thuộc thứ tự khách.
    ga,gb=_gd(ba.name,so_a),_gd(ba.name,tong-so_a)
    ds=[dict(name=ga.name,phan_bo=so_a),dict(name=gb.name,phan_bo=tong-so_a)]
    from vagabond import cong_no as cn
    import json
    lap=cn.khop_tay(p.name,999999999,dong=json.dumps(ds),ma_lan='KT476-thu-bo')
    cac=[frappe.get_doc('Payment Entry',ma) for ma in lap['pe'].split(', ')]
    la('retry cùng lần không lập PE mới',cn.khop_tay(p.name,999999999,dong=json.dumps(ds),ma_lan='KT476-thu-bo')['da_lam_roi'],1)
    _DA_TAO.extend((pe.doctype,pe.name) for pe in cac)
    la('không lấy số caller',lap['tien'],tong)
    la('hai PE đúng hai khách',len(cac),2)
    la('tab nháp xác minh cả bộ',sum(r['da_xac_minh'] for r in tt.phieu_thu_nhap([a.name,b.name])),2)
    for i,pe in enumerate(cac):
        with _Tep() as tep:
            r=tt.ghi_so_phieu_thu(pe.name,unc=[tep.file_url])
            la('app ghi sổ qua hook bộ',r.get('ok'),1)
        pe.reload()
        k=bs.noi_tung_phieu_thu(p,pe.name)
        la('đủ tiền PE',k['tien'],flt(pe.received_amount))
        la('retry cùng tiền',bs.noi_tung_phieu_thu(p,pe.name)['tien'],flt(pe.received_amount))
        if i==0:
            cac[1].reload()
            la('PE sau vẫn nháp',cac[1].docstatus,0)
            for gd in (ga,gb):
                gd.reload()
                dung('không nối PE nháp',all(x.payment_entry!=cac[1].name for x in gd.payment_entries))
    for gd in (ga,gb):
        gd.reload();la('đủ cả bộ',flt(gd.unallocated_amount),0)
    cac[0].reload();cac[0].cancel()
    for gd in (ga,gb):
        gd.reload()
        dung('hủy PE đầu gỡ khỏi cả bộ',all(x.payment_entry!=cac[0].name for x in gd.payment_entries))
    la('PE thứ hai vẫn đủ',bs.noi_tung_phieu_thu(p,cac[1].name)['tien'],flt(cac[1].received_amount))
    huy_hd={r.reference_name for r in cac[0].references}
    for hd in (a,b):
        hd.reload()
        la('hủy trả nợ đúng khách',flt(hd.outstanding_amount),flt(hd.grand_total) if hd.name in huy_hd else 0)


@ca('#476 nhóm6: công nợ trả hai kỳ từ cùng BT, phần dư cho phiếu khác, bỏ bộ giữ phiếu kia')
def _():
    from vagabond.khung.kiem_that.thu_gom_phap_nhan_576 import _nen,_hd,_khach,_phieu
    from vagabond.khung.kiem_that.thu_khop_tay_gop_571 import _gd
    from vagabond import cong_no as cn,bo_sao_ke_luong as bl,bo_sao_ke_db as bs,sepay
    from frappe.utils import flt
    import json
    cty,tk,_mau=_nen()
    a,b=_hd(tk,cty,100000,_khach('476KY1')),_hd(tk,cty,100000,_khach('476KY2'))
    p,q=_phieu([a],a.customer),_phieu([b],b.customer)
    ba=_tai_khoan_cong_ty_moi(_tk_ngan_hang(cty));sepay.them_tai_khoan(ba.bank_account_no,ba.name)
    g=_gd(ba.name,flt(a.grand_total)+flt(b.grand_total))
    cac=[]
    for so,ky in [(40000,'lan1'),(flt(a.grand_total)-40000,'lan2')]:
        r=cn.khop_tay(p.name,so,dong=json.dumps([dict(name=g.name,phan_bo=so)]),ma_lan='KT476-'+ky)
        cac+=r['pe'].split(', ')
        _DA_TAO.extend(('Payment Entry',ma) for ma in r['pe'].split(', '))
    p.reload();la('hai kỳ phủ đúng một phiếu',flt(p.da_thu),flt(a.grand_total))
    r=cn.khop_tay(q.name,flt(b.grand_total),dong=json.dumps([dict(name=g.name,phan_bo=flt(b.grand_total))]),ma_lan='KT476-khac')
    _DA_TAO.extend(('Payment Entry',ma) for ma in r['pe'].split(', '))
    dung('khách khác PE riêng',r['pe'] not in cac)
    try:bl.bo('cong_no',p.name)
    except frappe.ValidationError:pass
    else:dung('nháp còn sống không bỏ giữ',False)
    # Không xóa nháp: dự án giữ mọi chứng từ. Kiểm đường đã ghi sổ rồi
    # hủy qua lõi, từng PE trả phân bổ nhưng bộ giữ tới lúc kế toán bỏ.
    from vagabond import thu_tien as tt
    for ma in cac:
        with _Tep() as tep:
            la('ghi sổ kỳ thu',tt.ghi_so_phieu_thu(ma,unc=[tep.file_url]).get('ok'),1)
        pe=frappe.get_doc('Payment Entry',ma);pe.cancel()
        la('giữ chứng từ đã hủy',frappe.db.get_value('Payment Entry',ma,'docstatus'),2)
    bl.bo('cong_no',p.name);p.reload();q.reload();g.reload()
    la('phiếu1 về chờ thu',flt(p.da_thu),0)
    la('phiếu2 vẫn giữ đủ',sum(flt(d['phan_bo']) for d in bs.doc_hien_tai(q)['dong']),flt(b.grand_total))
    la('retry bỏ cả bộ',bl.bo('cong_no',p.name)['da_lam_roi'],1)
    la('không tự sinh bút toán',flt(g.allocated_amount),0)


@ca('#476 nút Đối chiếu SePay công nợ tự nhận hai lệnh, bấm lại không nhân phiếu thu')
def _():
    from vagabond.khung.kiem_that.thu_gom_phap_nhan_576 import _nen,_hd,_khach,_phieu
    from vagabond.khung.kiem_that.thu_khop_tay_gop_571 import _gd
    from vagabond import cong_no as cn,bo_sao_ke_db as bs,sepay
    from frappe.utils import flt
    cty,tk,_mau=_nen();hd=_hd(tk,cty,100000,_khach('476AUTO'))
    p=_phieu([hd],hd.customer);p.ma_phieu=cn._sinh_ma_cn();p.save(ignore_permissions=True)
    ba=_tai_khoan_cong_ty_moi(_tk_ngan_hang(cty));sepay.them_tai_khoan(ba.bank_account_no,ba.name)
    a,b=_gd(ba.name,40000,p.ma_phieu),_gd(ba.name,flt(hd.grand_total)-40000,p.ma_phieu)
    r=cn.kiem_sepay(p.name);p.reload()
    la('không lỗi lập phiếu',r.get('loi_lap'),[])
    ct=bs.doc_hien_tai(p)['chung_tu'];_DA_TAO.extend((x['doctype'],x['name']) for x in ct)
    la('một Customer một PE',len(ct),1)
    la('đủ cả hai lệnh',len(bs.doc_hien_tai(p)['dong']),2)
    la('đúng tiền',flt(p.da_thu),flt(hd.grand_total))
    cn.kiem_sepay(p.name);p.reload()
    la('bấm lại vẫn cùng PE',bs.doc_hien_tai(p)['chung_tu'],ct)
    hd.reload();la('nháp chưa giảm nợ sổ cái',flt(hd.outstanding_amount),flt(hd.grand_total))


@ca('#476 hủy mềm PE nháp rồi bỏ bộ: giữ lịch sử, khớp lại được, không phục hồi chủ cũ')
def _():
    from vagabond.khung.kiem_that.thu_gom_phap_nhan_576 import _nen,_hd,_khach,_phieu
    from vagabond.khung.kiem_that.thu_khop_tay_gop_571 import _gd
    from vagabond import cong_no as cn,bo_sao_ke_luong as bl,thu_tien as tt,sepay,chung_tu
    from frappe.utils import flt
    import json
    cty,tk,_mau=_nen();hd=_hd(tk,cty,100000,_khach('476HUYNHAP'))
    p=_phieu([hd],hd.customer)
    ba=_tai_khoan_cong_ty_moi(_tk_ngan_hang(cty));sepay.them_tai_khoan(ba.bank_account_no,ba.name)
    g=_gd(ba.name,flt(hd.grand_total));dong=json.dumps([dict(name=g.name,phan_bo=flt(hd.grand_total))])
    cu=cn.khop_tay(p.name,hd.grand_total,dong=dong,ma_lan='KT476-huy-nhap')['pe']
    _DA_TAO.append(('Payment Entry',cu))
    chung_tu.huy_phieu_nhap('Payment Entry',cu,'Kiểm hủy mềm trong bench')
    bl.bo('cong_no',p.name)
    la('nháp gốc còn nguyên',frappe.db.get_value('Payment Entry',cu,'vgb_huy'),1)
    la('nháp hủy không phủ nợ',tt.phan_bo_nhap_theo_hd([hd.name]).get(hd.name,0),0)
    moi=cn.khop_tay(p.name,hd.grand_total,dong=dong,ma_lan='KT476-sau-huy-nhap')['pe']
    _DA_TAO.append(('Payment Entry',moi));dung('phiếu mới khác lịch sử',moi!=cu)
    la('tab chỉ phiếu sống',[r['pe'] for r in tt.phieu_thu_nhap([hd.name])],[moi])
    try:chung_tu.bo_danh_dau_huy('Payment Entry',cu)
    except frappe.ValidationError:pass
    else:dung('không phục hồi phiếu đã nhả bộ',False)
    la('không gỡ dấu hủy',frappe.db.get_value('Payment Entry',cu,'vgb_huy'),1)
    hd.reload();g.reload()
    la('không giảm nợ khi còn nháp',flt(hd.outstanding_amount),flt(hd.grand_total))
    la('không ghi phân bổ lõi khi còn nháp',flt(g.allocated_amount),0)
