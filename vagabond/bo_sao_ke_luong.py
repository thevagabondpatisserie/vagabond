"""Adapter bộ sao kê cho các cửa đối soát hiện có. Không thêm DocType."""
import json
import frappe
from frappe.utils import flt, now_datetime
from vagabond import bo_sao_ke_db as bs

LUONG = {"ttnb", "hoan_tien"}


def kiem(loai, b, doc, g):
    from vagabond import doi_soat_sepay as dss, doi_chieu_app as dc
    ly_do = dss._loi_giao_dich(b,g) or dss.ly_do_tai_khoan_sepay(g.bank_account)
    if ly_do:
        return ly_do
    if loai == "hoan_tien":
        ba=frappe.db.get_value("Bank Account",g.bank_account,
            ["is_company_account","disabled","account"],as_dict=True) or {}
        if not ba.get("is_company_account") or ba.get("disabled") or not ba.get("account"):
            return "Chọn tài khoản công ty đang hoạt động để hoàn tiền khách."
    chu=dc._chu_khac(g,doc,bo=True)
    return "Giao dịch đã được %s sử dụng." % chu if chu else ""


def ung_vien(loai, doc, kq):
    from vagabond import doi_soat_sepay as dss
    b=dss._ban(loai)
    for r in kq["rows"]:
        g=frappe.get_doc("Bank Transaction",r["name"])
        loi=kiem(loai,b,doc,g)
        r["con_lai"]=bs.con_lai(g,doc)
        if loi or r["con_lai"]<=0:
            r.update(dung_duoc=0,vi_sao_khong=loi or "Giao dịch đã phân bổ hết.")
    kq["chon_bo"]=1
    return kq


def khop(loai, ma, dong):
    from vagabond import doi_soat_sepay as dss
    return _khop(loai, ma, dong, dss.kiem_quyen_luong(loai,ghi=True))


def _khop(loai, ma, dong, b):
    # Cửa nội bộ, không whitelist. Webhook đã xác thực vẫn là Guest;
    # không yêu cầu Guest có vai kế toán, không đổi người dùng toàn phiên.
    # Cửa khớp tay ở trên luôn kiểm quyền trước khi gọi.
    from vagabond import doi_soat_sepay as dss
    if loai not in LUONG:
        frappe.throw("Luồng này chưa mở đối soát bộ.")
    # Cửa tự dò bắt ValidationError rồi tiếp tục phiếu khác. Hoàn lại cả
    # phần giữ nếu bất kỳ bước trước commit hỏng, không để claim mồ côi.
    savepoint="bo_sao_ke_"+frappe.generate_hash(length=10)
    frappe.db.savepoint(savepoint)
    try:
        moi=json.loads(dong) if isinstance(dong,str) else dong
        bs.khoa_phieu(b["doctype"], ma, bs.doc_bo({"dong": moi, "chung_tu": []})["dong"])
        doc=frappe.get_doc(b["doctype"],ma,for_update=True)
        cu=bs.doc_hien_tai(doc)
        # Retry không đánh dấu/sinh chứng từ thêm lần nữa. Việc sinh lỗi của
        # hoàn tiền có cửa Sinh lại chứng từ riêng và giữ nguyên bằng chứng.
        if cu["dong"] and cu["dong"] == moi and (
                (loai=="ttnb" and doc.trang_thai=="Da chi") or
                (loai=="hoan_tien" and doc.get("da_doi_soat"))):
            return dict(ok=1,da_lam_roi=1,gd=doc.get(b["truong_gd"]),lech=0,
                so_tien_dong=flt(b["so_tien"](doc)),so_tien_phieu=flt(b["so_tien"](doc)),
                nhac="Bộ sao kê này đã được ghi nhận, không ghi thêm.",loi=doc.get("loi_sinh_ct") or "")
        if b.get("loi_phieu"):
            loi=b["loi_phieu"](doc)
            if loi:frappe.throw(loi)
        if loai=="hoan_tien" and (doc.trang_thai=="Da huy" or doc.get("da_doi_soat")):
            frappe.throw("Phiếu hoàn tiền đã huỷ hoặc đã đối soát. Tải lại để xem kết quả.")
        g=bs.chon(doc,moi,flt(b["so_tien"](doc)),b["chieu"],lambda g:kiem(loai,b,doc,g),ghi=True)
        ghi={b["truong_gd"]:g.name}
        if b.get("truong_nguoi"):ghi[b["truong_nguoi"]]=frappe.session.user
        if b.get("truong_luc"):ghi[b["truong_luc"]]=now_datetime()
        frappe.db.set_value(doc.doctype,doc.name,ghi)
        doc.add_comment("Comment","Khớp bộ sao kê: %s. Tổng %s đ. Người làm: %s." % (
            "; ".join("%s: %s đ" % (d["name"],d["phan_bo"]) for d in moi),g.withdrawal,frappe.session.user))
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        raise
    # Giữ đúng ranh giới cũ: bằng chứng tiền đã đi tồn tại độc lập với
    # bước sinh chứng từ. Phần giữ cũng commit cùng bằng chứng đó.
    frappe.db.commit()
    loi=""
    try:
        if b.get("khi_khop"):
            b["khi_khop"](frappe.get_doc(doc.doctype,doc.name),g.name)
        frappe.db.commit()
    except Exception as e:
        vet=frappe.get_traceback()
        frappe.db.rollback()
        frappe.log_error(vet,"Đối soát bộ: %s %s" % (loai,ma))
        loi=dss.cau_loi_sau_khop(e,vet)
    return dict(ok=1,gd=g.name,lech=0,so_tien_dong=g.withdrawal,
        so_tien_phieu=flt(b["so_tien"](doc)),loi=loi,
        nhac="Đã khớp %d dòng sao kê với phiếu." % len(moi))


def noi_hoan_tien(pe, method=None):
    """Khi PE hoàn tiền được ghi sổ, nối bộ bằng phép phân bổ lõi."""
    ma=pe.get("vgb_hoan_tien")
    if not ma or pe.docstatus!=1 or pe.payment_type!="Pay":
        return
    from vagabond import doi_soat_sepay as dss
    dss.nap_so()
    doc=frappe.get_doc("Vagabond Hoan Tien",ma,for_update=True)
    cu=bs.doc_hien_tai(doc)
    if not cu["dong"]:
        return
    b=dss._ban("hoan_tien")
    g=bs.chon(doc,cu["dong"],flt(doc.so_tien),"ra",lambda g:kiem("hoan_tien",b,doc,g),ghi=True)
    bs.noi(doc,g,[dict(doctype=pe.doctype,name=pe.name)])


def tu_dong_mot(loai, ma, cac_gd):
    """Chỉ nhận trọn các dòng cùng mã. Không tìm tổ hợp cho vừa tổng.

    None: không phải bộ, cửa cũ tiếp tục. Có kết quả: cửa cũ phải bỏ qua
    phiếu này dù bộ đang thiếu/thừa, không chọn một dòng riêng rồi báo đủ.
    """
    from vagabond import doi_soat_sepay as dss
    from vagabond.khop_sao_ke import co_ma
    if len(cac_gd)<2:
        return None
    b=dss._ban(loai)
    doc=frappe.get_doc(b["doctype"],ma)
    code=b["ma_do"](doc)
    ds=[r for r in cac_gd if co_ma(r.get("description") or r.get("mo_ta"),code) or co_ma(r.get("reference_number"),code)]
    # Cùng mã nhưng nguồn không hợp lệ không thuộc bộ tự nhận. Cửa cũ
    # vẫn trình lý do của dòng đó; không để nó che dòng công ty hợp lệ.
    ds=[r for r in ds if not dss._loi_giao_dich(b,r) and not dss.ly_do_tai_khoan_sepay(r.get("bank_account"))]
    if len(ds)<2:
        return None
    dong=[dict(name=r["name"],phan_bo=flt(r.get("withdrawal") if b["chieu"]=="ra" else r.get("deposit")) or flt(r.get("tien"))) for r in ds]
    try:
        return _khop(loai,ma,dong,b)
    except frappe.ValidationError as e:
        return dict(ok=0,phieu=ma,vi_sao=str(e),giao_dich=", ".join(r["name"] for r in ds))


def nguon_hoan_tien(pe, method=None):
    """Phiếu chi mới của bộ dùng đúng ngân hàng đã chọn, không ngân hàng mặc định."""
    if not pe.is_new() or pe.get("payment_type")!="Pay" or not pe.get("vgb_hoan_tien"):
        return
    doc=frappe.get_doc("Vagabond Hoan Tien",pe.vgb_hoan_tien)
    cu=bs.doc_hien_tai(doc)
    if not cu["dong"]:
        return
    from vagabond import doi_soat_sepay as dss
    dss.nap_so()
    b=dss._ban("hoan_tien")
    g=bs.chon(doc,cu["dong"],flt(doc.so_tien),"ra",lambda g:kiem("hoan_tien",b,doc,g),ghi=False)
    ba=frappe.db.get_value("Bank Account",g.flags.bo_sao_ke[0].bank_account,["company","account"],as_dict=True)
    if ba.company!=pe.company:
        frappe.throw("Tài khoản chi và hồ sơ hoàn tiền khác công ty.")
    pe.bank_account=g.flags.bo_sao_ke[0].bank_account
    pe.paid_from=ba.account


def duoc_bo(loai, doc):
    if not doc.get(bs.O_BO):
        return False
    if loai=='ttnb':
        from vagabond.de_nghi_chi import VAI_KE_TOAN, VAI_GIAM_DOC
        return bool(set(frappe.get_roles()) & (VAI_KE_TOAN | VAI_GIAM_DOC))
    if loai=='hoan_tien':
        from vagabond.hoan_tien import _duoc_tu_choi
        return _duoc_tu_choi()
    return False


@frappe.whitelist(methods=["POST"])
def bo(loai, ma):
    """Bỏ toàn bộ chỗ giữ của phiếu, không huỷ hoặc tháo bút toán thay kế toán."""
    from vagabond import doi_soat_sepay as dss
    b=dss.kiem_quyen_luong(loai,ghi=True)
    if loai not in LUONG:
        frappe.throw("Luồng này chưa có cửa bỏ bộ sao kê.")
    doc=frappe.get_doc(b['doctype'],ma,for_update=True)
    cu=bs.doc_hien_tai(doc)
    if not cu['dong']:
        return dict(ok=1,da_lam_roi=1)
    if not duoc_bo(loai,doc):
        frappe.throw("Chỉ kế toán hoặc giám đốc được bỏ bộ đối chiếu.")
    hop_le=('Hoan tat','Da chi') if loai=='ttnb' else ('Cho chi','Da doi soat','Da chi','Hoan thanh')
    if doc.trang_thai not in hop_le:
        frappe.throw("Phiếu đã đổi trạng thái. Tải lại trước khi bỏ đối chiếu.")
    if loai=='ttnb' and doc.get('ho_so_tt'):
        frappe.throw("Phiếu đã nối hồ sơ %s. Gỡ liên kết ở hồ sơ trước khi bỏ bộ sao kê." % doc.ho_so_tt)
    ct={(c['doctype'],c['name']) for c in cu['chung_tu']}
    if loai=='hoan_tien':
        # Kể cả phiếu chi nháp chưa vào metadata cũng không bỏ quên nó.
        for r in frappe.db.sql("""select name,docstatus from `tabPayment Entry`
            where vgb_hoan_tien=%s and payment_type='Pay' and docstatus<2 for update""",(ma,),as_dict=True):
            frappe.throw("Phiếu chi %s còn %s. Kế toán xử lý phiếu chi trong ERPNext trước khi bỏ bộ sao kê." %
                (r.name,'bản nháp' if r.docstatus==0 else 'đã ghi sổ'))
        if doc.get('phieu_chi') and frappe.db.get_value('Payment Entry',doc.phieu_chi,'docstatus',for_update=True) in (0,1):
            frappe.throw("Phiếu chi còn hiệu lực. Kế toán xử lý trước khi bỏ bộ sao kê.")
    for dt,ten in sorted(ct):
        if frappe.db.get_value(dt,ten,'docstatus',for_update=True) in (0,1):
            frappe.throw("Chứng từ %s còn hiệu lực. Kế toán xử lý trước khi bỏ bộ sao kê." % ten)
    for d in sorted(cu['dong'],key=lambda d:d['name']):
        frappe.db.get_value('Bank Transaction',d['name'],'name',for_update=True)
        if any((r.doctype,r.name) in ct for r in bs._loi(d['name'])):
            frappe.throw("Bộ sao kê còn liên kết bút toán; chưa bỏ được.")
    bs.luu(doc,[])
    ghi={b['truong_gd']:None}
    for o in ('truong_nguoi','truong_luc'):
        if b.get(o):ghi[b[o]]=None
    if loai=='ttnb':
        ghi.update(trang_thai='Hoan tat',ngay_da_chi=None)
    else:
        ghi.update(trang_thai='Cho chi',da_doi_soat=0,ngay_doi_soat=None,phieu_chi=None,loi_sinh_ct='',
            nguoi_hoan_thanh=None,ngay_hoan_thanh=None)
    frappe.db.set_value(doc.doctype,doc.name,ghi)
    doc.add_comment('Comment','Bỏ toàn bộ bộ sao kê: %s. Người làm: %s. Không chuyển tiền thêm chỉ vì đã bỏ đối chiếu.' %
        (', '.join(d['name'] for d in cu['dong']),frappe.session.user))
    return dict(ok=1,loi_nhan='Đã bỏ cả bộ, phiếu về Chờ chi để chọn lại đúng sao kê. Không chuyển tiền thêm.')
