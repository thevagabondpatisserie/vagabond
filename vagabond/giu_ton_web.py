"""Chỗ giữ web nằm trong snapshot đơn sẵn có, cùng transaction tạo đơn.

Khoá hàng cấu hình chung cho nhận đơn và đồng bộ Kiểm bánh. Các SELECT
FOR UPDATE đọc trạng thái vừa commit, không dùng snapshot đầu request.
Không commit ở đây; lỗi kiểm vẫn đi cách B tại cửa nhận đơn.
"""
import json
from datetime import datetime, timedelta
import frappe
from vagabond.ton_don_web import decor_huu_han, hom_nay

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
    return frappe.db.sql("""select ma_hang,ten_banh,co_the_ban,da_dat from `tabKiem Banh Dong`
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
    """Trả cảnh báo và metadata để ghi vào chính đơn sắp tạo, chưa commit."""
    if not ngay or not str(ngay).strip():
        return [], None
    ng = datetime.fromisoformat(str(ngay)).date()
    nay = hom_nay()
    if not nay <= ng <= nay + timedelta(days=3):
        return [], None
    khoa()
    ton = {}
    if ng == nay:
        for d in _dong(ng):
            ton[str(d.ma_hang)] = (max(0, int(d.co_the_ban or 0)), d.ten_banh or d.ma_hang)
    else:
        # v646: mã có ngày nhận nằm trong khoảng refill do ton_don_web kiểm theo
        # số refill, không giữ theo Đủ decor; đơn ngày refill không trừ decor.
        from vagabond import refill
        # Giữ đúng thứ tự khoá cũ: dòng kiểm bánh ba ngày trước, bảng BTP sau.
        kb = [(nay + timedelta(days=i), _dong(nay + timedelta(days=i))) for i in (1,2,3)]
        btp = frappe.db.sql("""select ma_hang,ten_banh,so_decor,decor_da_lam,so_refill,refill_tu,refill_den from `tabBTP Banh O Dong`
            where parent='BTP Banh O' and parenttype='BTP Banh O' for update""", as_dict=True)
        rf = refill.hieu_luc_tu_dong(btp, nay)
        dd = {}
        for ngay_kb, dong_kb in kb:
            for d in dong_kb:
                ma = str(d.ma_hang)
                if refill.ngay_cua_refill(rf, ma, ngay_kb):
                    continue
                dd[ma] = dd.get(ma,0) + int(d.da_dat or 0)
        for d in btp:
            # v649: decor cạn vì bếp làm hết vẫn chặn (ton_don_web.decor_huu_han).
            if decor_huu_han(d) and not refill.ngay_cua_refill(rf, str(d.ma_hang), ng):
                ton[str(d.ma_hang)] = (max(0,int(d.so_decor or 0)-dd.get(str(d.ma_hang),0)),d.ten_banh or d.ma_hang)
    giu = {}
    for d in _don():
        snap = json.loads(d.snapshot or '{}')
        b = snap.get(O) or {}
        if not b or b.get('da_dem'):
            continue
        ngay_don = datetime.fromisoformat(str(b.get('ngay_nguon') or d.ngay_nhan)).date()
        cung_nguon = ngay_don == nay if ng == nay else nay < ngay_don <= nay + timedelta(days=3)
        if cung_nguon:
            for ma, so in (b.get('dong') or {}).items():
                giu[ma] = giu.get(ma,0) + int(so)
    thieu, dong = tinh(hang,ton,giu)
    nhac = ['%s ngày %s chỉ còn %s cái, quý khách đang chọn %s cái.' %
        (ten,ng.strftime('%d/%m/%Y'),con,so) for ten,con,so in thieu]
    return nhac, {'dong':dong,'da_dem':False} if dong else None


def giu_refill_cho(rows, ids, rf):
    """{mã: số} suất refill đơn web đang giữ mà lần đếm Pancake chưa có. THUẦN.

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
    btp = frappe.db.sql("""select ma_hang,ten_banh,so_decor,so_refill,refill_tu,refill_den from `tabBTP Banh O Dong`
        where parent='BTP Banh O' and parenttype='BTP Banh O' for update""", as_dict=True)
    rf = refill.hieu_luc_tu_dong(btp, nay)
    can = {}
    for h in hang or []:
        ma = str(h["variation_id"])
        if ma in rf and refill.trong_khoang(ng, rf[ma]["tu"], rf[ma]["den"]):
            can[ma] = can.get(ma, 0) + int(h["quantity"])
    if not can:
        return [], None
    giu = {"dong": can, "ngay": ng.isoformat()}
    so = refill.tinh(nay, dong=btp)
    if so.get("loi"):
        return [], giu
    tu = min(rf[m]["tu"] for m in can)
    den = max(rf[m]["den"] for m in can)
    rows = frappe.db.sql("select name,pancake_id,snapshot from `tabVagabond Don Web` "
        "force index (vgb_ngay_nguon_ton) where trang_thai in ('Dang gui','Da nhan','Cho doi soat','Da ghi so')"
        " and vgb_ngay_nguon_ton >= %s and vgb_ngay_nguon_ton <= %s for update",
        (str(tu), str(den)), as_dict=True)
    dang_giu = giu_refill_cho(rows, so.get("ids"), rf)
    con = {m: (((so.get("refill") or {}).get(m) or {}).get("con") or 0) - dang_giu.get(m, 0) for m in can}
    nhac = refill.kiem_don([{"variation_id": m, "quantity": n} for m, n in can.items()], ng, rf, con)
    return nhac, giu


def da_dem(ngay, cac_id):
    """Đồng bộ KB đã giữ khoa(): đánh dấu trong cùng transaction với số tồn.

    Hôm nay co_the_ban trừ cả Cho chốt; ngày sau nguồn decor chỉ trừ Đã đặt.
    Bên gọi phải truyền đúng danh sách thực sự dùng để tính cột tương ứng.
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
