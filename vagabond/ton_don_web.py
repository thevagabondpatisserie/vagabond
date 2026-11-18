"""F21, PR471: chỉ từ chối khi có dòng tồn thật cho ngày nhận.

Không dùng danh mục công khai vì danh mục bỏ dòng tồn 0. Không có dòng
nguồn là chưa biết, không phải hết hàng.

v671 (Loan Anh góp ý 18/11/2026, anh Việt chốt): bánh đặt trước nhận NGÀY MAI,
số theo cột Có thể bán của phiếu Kiểm bánh ngày mai, cùng cách với hôm nay.
Trước v671 ba ngày tới theo ô Đủ decor. Bánh làm theo mẻ (refill) vẫn theo
khoảng của mẻ.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import frappe



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
    # v660: một bánh nhiều đợt, số còn là của đợt CHỨA ngày nhận.
    con = {m: (c or 0) for m, c in refill.con_theo_ngay(so, ng).items()}
    # v671: ngoài khoảng mẻ, bánh chỉ nhận được NGÀY MAI theo phiếu Kiểm bánh
    # ngày mai (trước v671: theo Đủ decor ba ngày tới).
    mai = {}
    if ng == nay + timedelta(days=1):
        mai = {m: n for m, (n, _ten) in _ton_phieu(ng).items() if n > 0}
    xet = {m for m in set(rf) & ma_hang if refill.ngay_cua_refill(rf, m, ng) or m not in mai}
    return xet, refill.kiem_don([h for h in hang if h["variation_id"] in xet], ng, rf, con, mai)


def _ton_phieu(ng):
    """{mã: (Có thể bán, tên)} của phiếu Kiểm bánh ngày `ng`; chưa có phiếu thì
    None (chưa biết tồn, không phải hết hàng)."""
    ten = "KB-%s" % ng
    if not frappe.db.exists("Kiem Banh Ngay", ten):
        return None
    ra = {}
    for d in frappe.get_doc("Kiem Banh Ngay", ten).dong:
        ra[d.ma_hang] = (int(d.co_the_ban or 0), d.ten_banh or d.ma_hang)
    return ra


def chan_dat_truoc_ngay_xa(hang, ten_dat_truoc, ng):
    """v671: bánh đặt trước (có trên phiếu Kiểm bánh ngày mai hoặc bảng BTP) chỉ
    nhận NGÀY MAI. Đơn chọn ngày xa hơn thì nhắc. Bánh làm theo mẻ trong khoảng
    của mẻ và món của đợt Đặc biệt đã được bỏ ra trước khi gọi. Thuần."""
    nhac = []
    for h in hang or []:
        ma = h.get("variation_id")
        if ma in ten_dat_truoc:
            nhac.append("%s là bánh đặt trước, chỉ nhận vào ngày mai. Cần nhận ngày %s "
                        "quý khách nhắn tiệm qua số 0931 224 334." % (ten_dat_truoc[ma], ng.strftime("%d/%m/%Y")))
    return nhac


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
    mai = nay + timedelta(days=1)
    xet_rf, nhac_rf = _kiem_refill(hang, ng, nay)
    hang = [h for h in hang if h["variation_id"] not in xet_rf]
    if ng < nay:
        return nhac_rf
    nhac_truoc = []
    if ng > mai:
        # v671: bánh đặt trước chỉ nhận ngày mai. Ngày xa hơn chỉ còn bánh làm
        # theo mẻ (đã xét ở trên) và món của đợt (bên gọi đã bỏ ra).
        if not hang:
            return nhac_rf
        ten = {d.ma_hang: (d.ten_banh or d.ma_hang) for d in (frappe.get_single("BTP Banh O").dong or [])}
        for m, (_n, t) in (_ton_phieu(mai) or {}).items():
            ten.setdefault(m, t)
        return list(nhac_rf) + chan_dat_truoc_ngay_xa(hang, ten, ng)
    ton = _ton_phieu(ng)
    # F21-4: chưa có phiếu Kiểm bánh của ngày nhận là chưa biết tồn, nhận như cũ.
    if ton is None:
        return nhac_rf
    if ng == nay:
        # v649 (anh Việt 11/11/2026): bánh đặt trước nhận từ ngày mai. Đơn nhận
        # hôm nay chỉ nhận bánh có trong Kiểm bánh hôm nay (tab Có sẵn hôm nay).
        ten_btp = {d.ma_hang: (d.ten_banh or d.ma_hang) for d in (frappe.get_single("BTP Banh O").dong or [])}
        nhac_truoc = chan_dat_truoc_hom_nay(hang, set(ton), ten_btp)
    nhac = list(nhac_rf) + nhac_truoc
    for h in hang:
        if h["variation_id"] not in ton:
            continue
        con, ten = ton[h["variation_id"]]
        con = max(0, con)
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
