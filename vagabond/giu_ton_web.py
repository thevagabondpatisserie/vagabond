"""Chỗ giữ web nằm trong snapshot đơn sẵn có, cùng transaction tạo đơn.

Khoá hàng cấu hình chung cho nhận đơn và đồng bộ Kiểm bánh. Các SELECT
FOR UPDATE đọc trạng thái vừa commit, không dùng snapshot đầu request.
Không commit ở đây; lỗi kiểm vẫn đi cách B tại cửa nhận đơn.
"""
import json
from datetime import datetime, timedelta
import frappe
from vagabond.ton_don_web import SO_NGAY_DAT_TRUOC, con_btp, da_lam_dot_vuot, hom_nay

O = "giu_ton_web"
# v646 Codex 549 (1eefda8): suất refill đơn web đã giữ, ghi trong snapshot đơn.
O_RF = "giu_refill"
DT = "Vagabond Don Web"
O_NGAY = "vgb_ngay_nguon_ton"


def khoa():
    r = frappe.db.sql("""select field from tabSingles where doctype='Vagabond Settings'
        and field='pancake_shop_id' for update""")
    if not r:
        raise RuntimeError("Chưa có hàng cấu hình để giữ tồn web")


def _dong(ngay):
    # v649: đủ cột cho phép giữ vỏ (giu_vo.don_con_giu_vo).
    return frappe.db.sql("""select ma_hang,ten_banh,co_the_ban,da_dat,phat_sinh,cho_chot,sx,huy,don_khac,giu_cho
        from `tabKiem Banh Dong`
        where parent=%s and parenttype='Kiem Banh Ngay' for update""",
        ("KB-%s" % ngay,), as_dict=True)


def _don(cac_id=()):
    # Hai truy vấn có chỉ mục riêng, không OR/JSON/LIKE khiến MariaDB
    # quét và khóa cả bảng. Hàng cấu hình đã tuần tự hóa mọi lượt giữ tồn.
    cot = "name,ngay_nhan,pancake_id,snapshot"
    trang_thai = "trang_thai in ('Dang gui','Da nhan','Cho doi soat','Da ghi so')"
    rows = frappe.db.sql("select " + cot + " from `tabVagabond Don Web` "
        "force index (vgb_ngay_nguon_ton) where " + trang_thai +
        " and vgb_ngay_nguon_ton >= %s and vgb_ngay_nguon_ton < %s for update",
        (str(hom_nay()), str(hom_nay()+timedelta(days=4))), as_dict=True)
    ids = tuple(sorted({str(x) for x in cac_id if x is not None}))
    if ids:
        rows += frappe.db.sql("select " + cot + " from `tabVagabond Don Web` "
            "force index (pancake_id) where " + trang_thai +
            " and pancake_id in %s for update", (ids,), as_dict=True)
    return list({r.name:r for r in rows}.values())


def tinh(hang, ton, giu):
    """Gộp cùng mã trước kiểm: hai dòng mỗi dòng 1 cũng cần 2 bánh."""
    can = {}
    for h in hang:
        ma = str(h['variation_id'])
        can[ma] = can.get(ma, 0) + int(h['quantity'])
    thieu = []
    for ma, so in can.items():
        if ma not in ton:
            continue
        con = max(0, int(ton[ma][0]) - int(giu.get(ma, 0)))
        if so > con:
            thieu.append((ton[ma][1], con, so))
    return thieu, {ma:so for ma,so in can.items() if ma in ton}


def kiem_va_giu(hang, ngay):
    """Trả cảnh báo và metadata để ghi vào chính đơn sắp tạo, chưa commit.

    v671: hôm nay và ngày mai cùng một luật, số theo cột Có thể bán của phiếu
    Kiểm bánh ĐÚNG ngày nhận, trừ suất các đơn web cùng ngày nhận mà nhịp đếm
    chưa có. Bánh làm theo mẻ giữ ở kiem_va_giu_refill.

    v675: ngày kia và ngày thứ ba giữ theo số còn nhận chung của ba ngày tới, trừ
    suất các đơn web ba ngày tới mà nhịp đếm chưa có, vì các đơn đó cùng ăn vào
    một nguồn. v677: nguồn là BTP sẵn (ton_don_web.con_btp, cùng phép với thẻ
    web), trước đó là Đủ decor. Xa hơn không giữ (ton_don_web chặn)."""
    if not ngay or not str(ngay).strip():
        return [], None
    ng = datetime.fromisoformat(str(ngay)).date()
    nay = hom_nay()
    if not nay <= ng <= nay + timedelta(days=SO_NGAY_DAT_TRUOC):
        return [], None
    khoa()
    ton = {}
    xa = ng > nay + timedelta(days=1)
    if xa:
        from vagabond import refill
        # Giữ đúng thứ tự khoá cũ: dòng kiểm bánh ba ngày trước, bảng BTP sau.
        kb = [(nay + timedelta(days=i), _dong(nay + timedelta(days=i))) for i in range(1, SO_NGAY_DAT_TRUOC + 1)]
        btp = frappe.db.sql("""select ma_hang,ten_banh,so_btp,so_decor,decor_da_lam,so_refill,refill_tu,refill_den,refill_dot from `tabBTP Banh O Dong`
            where parent='BTP Banh O' and parenttype='BTP Banh O' for update""", as_dict=True)
        rf = refill.hieu_luc_tu_dong(btp, nay)
        so = refill.tinh(nay, dong=btp) if rf else None
        mo = refill.bo_dot_du_don(rf, so)
        ten_dt = {str(d.ma_hang): d.ten_banh or d.ma_hang for d in btp}
        for d in kb[0][1]:
            ten_dt.setdefault(str(d.ma_hang), d.ten_banh or d.ma_hang)
        ton = {m: (max(0, c), t) for m, (c, t) in con_btp(btp, kb, nay, rf, so, da_lam_dot_vuot(so, nay)).items()}
        # Bánh đặt trước không có dòng BTP thì hết chỗ ngày này (như ton_don_web).
        for h in hang or []:
            m = str(h["variation_id"])
            if m in ten_dt and m not in ton:
                ton[m] = (0, ten_dt[m])
        ton = {m: v for m, v in ton.items() if not refill.ngay_cua_refill(mo, m, ng)}
    for d in ([] if xa else _dong(ng)):
        ton[str(d.ma_hang)] = (max(0, int(d.co_the_ban or 0)), d.ten_banh or d.ma_hang)
    if nay < ng and not xa:
        # Ngày mai thuộc khoảng mẻ refill của mã: đơn trừ vào mẻ (kiem_va_giu_refill).
        from vagabond import refill
        btp = frappe.db.sql("""select ma_hang,ten_banh,so_decor,so_refill,refill_tu,refill_den,refill_dot from `tabBTP Banh O Dong`
            where parent='BTP Banh O' and parenttype='BTP Banh O' for update""", as_dict=True)
        rf = refill.hieu_luc_tu_dong(btp, nay)
        ma_don = {str(h["variation_id"]) for h in hang or []}
        if any(refill.ngay_cua_refill(rf, m, ng) for m in ma_don):
            # v675: đợt đã nhận đủ đơn không giữ ngày của nó, bánh bán theo phiếu
            # ngày mai (cùng phép với thẻ web và cửa nhận đơn).
            rf = refill.bo_dot_du_don(rf, refill.tinh(nay, dong=btp))
        ton = {m: v for m, v in ton.items() if not refill.ngay_cua_refill(rf, m, ng)}
    giu = {}
    for d in _don():
        snap = json.loads(d.snapshot or '{}')
        b = snap.get(O) or {}
        if not b or b.get('da_dem'):
            continue
        ngay_don = datetime.fromisoformat(str(b.get('ngay_nguon') or d.ngay_nhan)).date()
        cung_nguon = nay < ngay_don <= nay + timedelta(days=SO_NGAY_DAT_TRUOC) if xa else ngay_don == ng
        if cung_nguon:
            for ma, so in (b.get('dong') or {}).items():
                giu[ma] = giu.get(ma,0) + int(so)
    thieu, dong = tinh(hang,ton,giu)
    nhac = ['%s ngày %s chỉ còn %s cái, quý khách đang chọn %s cái.' %
        (ten,ng.strftime('%d/%m/%Y'),con,so) for ten,con,so in thieu]
    return nhac, {'dong':dong,'da_dem':False} if dong else None


def giu_refill_cho(rows, ids, rf, ngay=None):
    """{mã: số} suất refill đơn web đang giữ mà lần đếm Pancake chưa có. THUẦN.

    v660: một bánh nhiều đợt. Chỉ tính suất của đơn có ngày nhận nằm trong
    CÙNG đợt với ngày đang xét `ngay` (rf dạng {mã: [đợt]}), để đơn của đợt
    khác không ăn vào số còn của đợt này. rf dạng cũ {mã: đợt} vẫn nhận.

    Đơn đã lên Pancake (pancake_id nằm trong `ids` của CÙNG lần đếm) thì số
    refill đã trừ nó rồi, không trừ lần hai. Đơn chưa lên, hoặc lên sau lần
    đếm, thì trừ ở đây cho tới khi lần đếm sau có nó."""
    from vagabond import refill
    ids = {str(x) for x in ids or []}
    ra = {}
    for d in rows or []:
        if d.get("pancake_id") and str(d.get("pancake_id")) in ids:
            continue
        b = json.loads(d.get("snapshot") or "{}").get(O_RF) or {}
        for ma, so in (b.get("dong") or {}).items():
            r = (rf or {}).get(ma)
            if isinstance(r, list):
                r = refill.dot_cua(rf, ma, ngay)
            if r and refill.trong_khoang(b.get("ngay"), r["tu"], r["den"]):
                ra[ma] = ra.get(ma, 0) + int(so or 0)
    return ra


def kiem_va_giu_refill(hang, ngay):
    """Kiểm và giữ suất refill trong CÙNG transaction tạo đơn (Codex 549, 1eefda8).

    Trước: chỉ ton_don_web đếm từ xa trước transaction, nên hai khách đặt
    cùng lúc suất cuối đều qua. Nay sau khoa() (tuần tự hoá mọi lượt giữ),
    khoá bảng BTP, lấy số còn từ lần đếm Pancake (cửa ngoài vừa đếm mới), trừ
    suất các đơn web đang giữ mà Pancake chưa có, rồi ghi suất của đơn này.
    Chưa đếm được Pancake thì không chặn (như ton_don_web) nhưng vẫn ghi suất.
    Trả (câu nhắc, dữ liệu giữ cho snapshot[O_RF]). Không commit ở đây."""
    from vagabond import refill
    if not ngay or not str(ngay).strip():
        return [], None
    ng = datetime.fromisoformat(str(ngay)).date()
    nay = hom_nay()
    if ng <= nay:
        return [], None
    khoa()
    btp = frappe.db.sql("""select ma_hang,ten_banh,so_decor,so_refill,refill_tu,refill_den,refill_dot from `tabBTP Banh O Dong`
        where parent='BTP Banh O' and parenttype='BTP Banh O' for update""", as_dict=True)
    rf = refill.hieu_luc_tu_dong(btp, nay)
    can = {}
    for h in hang or []:
        ma = str(h["variation_id"])
        if refill.ngay_cua_refill(rf, ma, ng):
            can[ma] = can.get(ma, 0) + int(h["quantity"])
    if not can:
        return [], None
    giu = {"dong": can, "ngay": ng.isoformat()}
    so = refill.tinh(nay, dong=btp)
    if so.get("loi"):
        return [], giu
    if ng <= nay + timedelta(days=SO_NGAY_DAT_TRUOC):
        # v675: ngày thuộc đợt đã nhận đủ đơn thì bánh bán như bánh đặt trước
        # thường (ngày mai theo phiếu, ngày kia và ngày thứ ba theo Đủ decor;
        # kiem_va_giu giữ), không giữ suất mẻ. Ngày xa hơn vẫn chặn theo đợt.
        mo = refill.bo_dot_du_don(rf, so)
        can = {m: n for m, n in can.items() if refill.ngay_cua_refill(mo, m, ng)}
        if not can:
            return [], None
        giu = {"dong": can, "ngay": ng.isoformat()}
    # v660: chỉ xét đợt CHỨA ngày nhận của đơn này (một bánh nhiều đợt).
    rf_ng = refill.theo_ngay(rf, ng)
    tu = min(rf_ng[m]["tu"] for m in can)
    den = max(rf_ng[m]["den"] for m in can)
    rows = frappe.db.sql("select name,pancake_id,snapshot from `tabVagabond Don Web` "
        "force index (vgb_ngay_nguon_ton) where trang_thai in ('Dang gui','Da nhan','Cho doi soat','Da ghi so')"
        " and vgb_ngay_nguon_ton >= %s and vgb_ngay_nguon_ton <= %s for update",
        (str(tu), str(den)), as_dict=True)
    dang_giu = giu_refill_cho(rows, so.get("ids"), rf_ng)
    con_dot = refill.con_theo_ngay(so, ng)
    con = {m: (con_dot.get(m) or 0) - dang_giu.get(m, 0) for m in can}
    nhac = refill.kiem_don([{"variation_id": m, "quantity": n} for m, n in can.items()], ng, rf, con)
    return nhac, giu


def da_dem(ngay, cac_id):
    """Đồng bộ KB đã giữ khoa(): đánh dấu trong cùng transaction với số tồn.

    Có thể bán trừ cả Đã đặt, Phát sinh và Chờ chốt, nên bên gọi truyền mọi
    đơn giao ngày đó (v671: ngày mai cũng theo Có thể bán, trước đây theo Đủ
    decor chỉ trừ Đã đặt). Bên gọi phải truyền đúng danh sách thực sự dùng để
    tính cột tương ứng.
    """
    ids = {str(x) for x in cac_id if x is not None}
    ngay=str(ngay)[:10]
    for d in _don(ids):
        snap = json.loads(d.snapshot or '{}')
        b = snap.get(O)
        if not b:
            continue
        moi = bool(d.pancake_id) and str(d.pancake_id) in ids
        nguon=str(b.get('ngay_nguon') or d.ngay_nhan or '')[:10]
        # ID thật ở ngày mới thắng ngày cũ trên đơn web. Đồng bộ ngày cũ
        # sau đó không được xóa dấu của ngày mới và trừ decor lần hai.
        if not moi and nguon != ngay:
            continue
        doi=bool(b.get('da_dem')) != moi or (moi and nguon != ngay)
        if doi:
            b['da_dem'] = moi
            if moi:b['ngay_nguon'] = ngay
            frappe.db.set_value(DT,d.name,{'snapshot':json.dumps(snap,ensure_ascii=False),
                O_NGAY:ngay_nguon(snap,d.ngay_nhan)},update_modified=False)


def ngay_nguon(snap, ngay):
    b = snap.get(O) or {}
    if b.get('dong') and (b.get('ngay_nguon') or ngay):
        return str(b.get('ngay_nguon') or ngay)[:10]
    # v646: đơn chỉ giữ suất refill cũng cần ngày trên cột có chỉ mục để
    # kiem_va_giu_refill tìm được mà không quét cả bảng.
    r = snap.get(O_RF) or {}
    return str(r.get('ngay') or ngay)[:10] if r.get('dong') and (r.get('ngay') or ngay) else None


def bao_ve(doc):
    """Không để save bản đơn đọc trước nhịp KB ghi đè dấu đã tính tồn."""
    if doc.is_new():
        setattr(doc,O_NGAY,ngay_nguon(json.loads(doc.snapshot or '{}'),doc.ngay_nhan))
        return
    cu = frappe.db.get_value(DT,doc.name,'snapshot',for_update=True)
    that = json.loads(cu or '{}')
    setattr(doc,O_NGAY,ngay_nguon(that,doc.ngay_nhan))
    moi = json.loads(doc.snapshot or '{}')
    doi = False
    for k in (O, O_RF):
        if moi.get(k) == that.get(k) and (k in moi) == (k in that):
            continue
        doi = True
        if k in that:
            moi[k] = that[k]
        else:
            moi.pop(k,None)
    if doi:
        doc.snapshot = json.dumps(moi,ensure_ascii=False)
