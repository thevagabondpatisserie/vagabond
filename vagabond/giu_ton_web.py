"""Chỗ giữ web nằm trong snapshot đơn sẵn có, cùng transaction tạo đơn.

Khoá hàng cấu hình chung cho nhận đơn và đồng bộ Kiểm bánh. Các SELECT
FOR UPDATE đọc trạng thái vừa commit, không dùng snapshot đầu request.
Không commit ở đây; lỗi kiểm vẫn đi cách B tại cửa nhận đơn.
"""
import json
from datetime import datetime, timedelta
import frappe
from vagabond.ton_don_web import hom_nay

O = "giu_ton_web"
DT = "Vagabond Don Web"


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
    # Ngày nhận trên biên nhận web có thể cũ sau khi Sales dời trên Pancake.
    # Đọc thêm ID đang đồng bộ và ngày nguồn đã biết, không đổi biên nhận cũ.
    ids=tuple(str(x) for x in cac_id if x is not None) or ("",)
    return frappe.db.sql("""select name,ngay_nhan,pancake_id,snapshot from `tabVagabond Don Web`
        where trang_thai in ('Dang gui','Da nhan','Cho doi soat','Da ghi so')
        and snapshot like %s
        and ((ngay_nhan >= %s and ngay_nhan < %s)
          or (json_unquote(json_extract(snapshot,'$.giu_ton_web.ngay_nguon')) >= %s
            and json_unquote(json_extract(snapshot,'$.giu_ton_web.ngay_nguon')) < %s)
          or pancake_id in %s) for update""",
        ('%"giu_ton_web"%',str(hom_nay()),str(hom_nay()+timedelta(days=4)),
         str(hom_nay()),str(hom_nay()+timedelta(days=4)),ids), as_dict=True)


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
        dd = {}
        for i in (1,2,3):
            for d in _dong(nay + timedelta(days=i)):
                ma = str(d.ma_hang)
                dd[ma] = dd.get(ma,0) + int(d.da_dat or 0)
        for d in frappe.db.sql("""select ma_hang,ten_banh,so_decor from `tabBTP Banh O Dong`
            where parent='BTP Banh O' and parenttype='BTP Banh O' for update""", as_dict=True):
            if int(d.so_decor or 0) > 0:
                ton[str(d.ma_hang)] = (max(0,int(d.so_decor)-dd.get(str(d.ma_hang),0)),d.ten_banh or d.ma_hang)
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
            frappe.db.set_value(DT,d.name,'snapshot',json.dumps(snap,ensure_ascii=False),update_modified=False)


def bao_ve(doc):
    """Không để save bản đơn đọc trước nhịp KB ghi đè dấu đã tính tồn."""
    if doc.is_new():
        return
    cu = frappe.db.get_value(DT,doc.name,'snapshot',for_update=True)
    that = json.loads(cu or '{}')
    moi = json.loads(doc.snapshot or '{}')
    if moi.get(O) == that.get(O) and (O in moi) == (O in that):
        return
    if O in that:
        moi[O] = that[O]
    else:
        moi.pop(O,None)
    doc.snapshot = json.dumps(moi,ensure_ascii=False)
