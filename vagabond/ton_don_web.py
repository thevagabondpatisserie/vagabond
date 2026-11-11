"""F21, PR471: chỉ từ chối khi có dòng tồn thật cho ngày nhận.

Không dùng danh mục công khai vì danh mục bỏ dòng tồn 0. Không có dòng
nguồn là chưa biết, không phải hết hàng. Dư decor chỉ phục vụ ba ngày tới,
không được dùng số hôm nay để chặn bánh làm theo đơn nhiều ngày sau.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import frappe

from vagabond.giu_vo import don_con_giu_vo


def hom_nay():
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()


def _kiem_refill(hang, ng, nay):
    """v646 Refill: (mã đã xét, câu nhắc). Mã có refill còn nhận đơn: ngày nhận
    trong khoảng thì kiểm số còn (đếm MỚI, không dùng số giữ 5 phút); ngoài
    khoảng mà không còn decor 3 ngày tới thì nhắc chọn ngày trong khoảng."""
    from vagabond import refill

    if ng <= nay:
        return set(), []
    dong_btp = frappe.get_single("BTP Banh O").dong
    rf = refill.hieu_luc_tu_dong(dong_btp, nay)
    ma_hang = {h["variation_id"] for h in hang}
    if not (set(rf) & ma_hang):
        return set(), []
    so = refill.tinh(nay, moi=True, dong=dong_btp)
    if so.get("loi"):
        # Chưa đếm được: không chặn khách (web đã ẩn refill khi chưa đếm được),
        # nhưng báo Sales đối chiếu như mọi lỗi kiểm tồn.
        bao_loi(ng)
        return set(rf) & ma_hang, []
    con = {m: (r.get("con") or 0) for m, r in (so.get("refill") or {}).items()}
    decor = {}
    if ng <= nay + timedelta(days=3):
        for d in dong_btp or []:
            if int(d.so_decor or 0) > 0:
                decor[d.ma_hang] = int(d.so_decor or 0)
    xet = {m for m in set(rf) & ma_hang if refill.trong_khoang(ng, rf[m]["tu"], rf[m]["den"]) or m not in decor}
    return xet, refill.kiem_don([h for h in hang if h["variation_id"] in xet], ng, rf, con, decor)


def decor_huu_han(d):
    """Dòng bảng BTP có nguồn Đủ decor hữu hạn không (F21 review 13/10: decor gốc
    bằng 0 là dòng giữ chỗ, không chặn). v649, Codex #552 vòng 4: Đủ decor nay
    trừ ngay theo Bếp làm, nên decor về 0 hay âm vì bếp làm hết vẫn là nguồn
    hữu hạn đã cạn. Gốc = Đủ decor hiện còn + phần đã trừ theo Bếp làm kể từ lần
    bếp nhập decor gần nhất. Thuần."""
    lay = (lambda k: d.get(k)) if hasattr(d, "get") else (lambda k: getattr(d, k, 0))
    return int(lay("so_decor") or 0) + int(lay("decor_da_lam") or 0) > 0


def chan_dat_truoc_hom_nay(hang, co_kb, ten_btp):
    """v649: bánh đặt trước (có trong bảng BTP) mà không có dòng trong Kiểm bánh
    hôm nay thì không nhận giao hôm nay. Bánh có dòng thì đã kiểm theo cột Bán
    được như cũ. Thuần, không chạm Frappe."""
    nhac = []
    for h in hang or []:
        ma = h.get("variation_id")
        if ma in ten_btp and ma not in co_kb:
            nhac.append("%s là bánh đặt trước, nhận từ ngày mai. Bánh nhận hôm nay "
                        "quý khách chọn ở tab Có sẵn hôm nay." % ten_btp[ma])
    return nhac


def kiem(hang, ngay):
    if not ngay or not str(ngay).strip():
        return []
    ng = datetime.fromisoformat(str(ngay)).date()
    nay = hom_nay()
    xet_rf, nhac_rf = _kiem_refill(hang, ng, nay)
    hang = [h for h in hang if h["variation_id"] not in xet_rf]
    if ng != nay and not nay < ng <= nay + timedelta(days=3):
        return nhac_rf
    ma = {h["variation_id"] for h in hang}
    ton = {}
    nhac_truoc = []
    if ng == nay:
        ten = "KB-%s" % nay
        # F21-4: chưa có bảng Kiểm bánh hôm nay là chưa biết tồn, nhận như cũ.
        if not frappe.db.exists("Kiem Banh Ngay", ten):
            return []
        co_kb = set()
        for d in frappe.get_doc("Kiem Banh Ngay", ten).dong:
            co_kb.add(d.ma_hang)
            if d.ma_hang in ma:
                ton[d.ma_hang] = (max(0, int(d.co_the_ban or 0)), d.ten_banh or d.ma_hang)
        # v649 (anh Việt 11/11/2026): bánh đặt trước nhận từ ngày mai. Đơn nhận
        # hôm nay chỉ nhận bánh có trong Kiểm bánh hôm nay (tab Có sẵn hôm nay).
        ten_btp = {d.ma_hang: (d.ten_banh or d.ma_hang) for d in (frappe.get_single("BTP Banh O").dong or [])}
        nhac_truoc = chan_dat_truoc_hom_nay(hang, co_kb, ten_btp)
    else:
        kho = frappe.get_single("BTP Banh O")
        da_dat = {}
        from vagabond import refill
        rf = refill.hieu_luc_tu_dong(kho.dong, nay)
        for i in (1, 2, 3):
            ten = "KB-%s" % (nay + timedelta(days=i))
            if frappe.db.exists("Kiem Banh Ngay", ten):
                for d in frappe.get_doc("Kiem Banh Ngay", ten).dong:
                    # v646: đơn ngày nằm trong khoảng refill của mã trừ vào refill.
                    if refill.ngay_cua_refill(rf, d.ma_hang, nay + timedelta(days=i)):
                        continue
                    # v649 Codex #552 vòng 7: đơn đã có bánh bếp làm trước thì vỏ đã trừ.
                    da_dat[d.ma_hang] = da_dat.get(d.ma_hang, 0) + don_con_giu_vo(d, ("da_dat",))
        for d in kho.dong or []:
            # Dòng giữ chỗ decor0 chưa phải nguồn tồn hữu hạn.
            if d.ma_hang in ma and decor_huu_han(d):
                ton[d.ma_hang] = (max(0, int(d.so_decor or 0) - da_dat.get(d.ma_hang, 0)), d.ten_banh or d.ma_hang)
    nhac = list(nhac_rf) + nhac_truoc
    for h in hang:
        if h["variation_id"] not in ton:
            continue
        con, ten = ton[h["variation_id"]]
        if h["quantity"] > con:
            nhac.append("%s ngày %s chỉ còn %s cái, quý khách đang chọn %s cái."
                        % (ten, ng.strftime("%d/%m/%Y"), con, h["quantity"]))
    return nhac


def _ghi_loi(noi_dung, tieu_de):
    try:
        frappe.log_error(noi_dung, tieu_de)
    except Exception:
        # Mất cả DB ghi Error Log cũng không được làm hỏng cửa nhận đơn.
        frappe.logger("don_web").error(tieu_de)


def bao_loi(ngay):
    """Dùng đúng kênh Sales nhận đơn web; lỗi cảnh báo không chặn đơn."""
    try:
        _ghi_loi(frappe.get_traceback(), "F21: chưa kiểm được tồn đơn web")
        from vagabond import kenh_zalo
        # v597: Zalo thay Lark. Một tin mỗi ngày nhận, không nhắc lặp mỗi đơn.
        ten = kenh_zalo.bao("canh_bao", "don_web", "Sales kiểm lại tồn đơn web ngày nhận %s" % ngay,
                            ["Phép kiểm tồn bị lỗi; web vẫn tiếp nhận yêu cầu.",
                             "Sales kiểm lại tồn trước khi xác nhận với khách."],
                            khoa="f21-ton-loi:%s" % ngay, ma_tin="bh_ton_web_loi")
        if not ten:
            _ghi_loi("Chưa có nhóm Zalo nhận chủ đề Đơn web, hoặc chưa ghi được tin.",
                     "F21: chưa gửi được cảnh báo Sales")
    except Exception:
        try:
            _ghi_loi(frappe.get_traceback(), "F21: chưa gửi được cảnh báo Sales")
        except Exception:
            pass
