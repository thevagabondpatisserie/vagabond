"""F21, PR471: chỉ từ chối khi có dòng tồn thật cho ngày nhận.

Không dùng danh mục công khai vì danh mục bỏ dòng tồn 0. Không có dòng
nguồn là chưa biết, không phải hết hàng.

v671 (Loan Anh góp ý 18/11/2026, anh Việt chốt): bánh đặt trước nhận NGÀY MAI,
số theo cột Có thể bán của phiếu Kiểm bánh ngày mai, cùng cách với hôm nay.
Trước v671 ba ngày tới theo ô Đủ decor. Bánh làm theo mẻ (refill) vẫn theo
khoảng của mẻ.

v675 (Sales nhắn 19/11/2026, giám đốc chốt nhận tới 3 ngày tới): hôm nay và
ngày mai theo cột Có thể bán (Còn bán) của phiếu Kiểm bánh đúng ngày; ngày kia và
ngày thứ ba theo Đủ decor trừ các đơn chưa làm (con_decor); xa hơn không nhận
bánh đặt trước thường. Đợt refill đã nhận đủ đơn không giữ ngày của nó nữa
(refill.bo_dot_du_don): ngày đó bán theo đúng luật trên.

v677 (Loan Anh báo 20/11/2026, anh Việt chọn hướng A): ngày kia và ngày thứ ba
theo BTP sẵn (không còn theo Đủ decor) trừ các đơn chưa làm của ba ngày tới, vì
còn một, hai ngày thì bếp kịp decor từ vỏ. Ngày mai vẫn theo phiếu. Đủ decor chỉ
còn là số theo dõi của bếp, không chặn web. Một phép con_btp cho thẻ web, cửa
nhận đơn, cửa giữ hàng và bảng Kiểm bánh (so_web_ba_ngay).
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import frappe

from vagabond.giu_vo import don_con_giu_vo

# v675: bánh đặt trước thường nhận tới ngày thứ ba kể từ hôm nay (giám đốc chốt
# 19/11/2026); v677: ngày kia và ngày thứ ba theo BTP sẵn.
SO_NGAY_DAT_TRUOC = 3

def hom_nay():
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()


def _kiem_refill(hang, ng, nay):
    """v646 Refill: (mã đã xét, câu nhắc). Mã có refill còn nhận đơn: ngày nhận
    trong khoảng thì kiểm số còn (đếm MỚI, không dùng số giữ 5 phút); ngoài
    khoảng mà không còn số ba ngày tới thì nhắc chọn ngày trong khoảng."""
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
    # v675: đợt đã nhận đủ đơn không giữ ngày của nó nữa, bánh bán theo phiếu.
    rf = refill.bo_dot_du_don(rf, so)
    if not (set(rf) & ma_hang):
        return set(), []
    # v660: một bánh nhiều đợt, số còn là của đợt CHỨA ngày nhận.
    con = {m: (c or 0) for m, c in refill.con_theo_ngay(so, ng).items()}
    # v671: ngoài khoảng mẻ, bánh chỉ nhận được NGÀY MAI theo phiếu Kiểm bánh
    # ngày mai (trước v671: theo Đủ decor ba ngày tới).
    # v675, v677: ngày kia và ngày thứ ba theo BTP sẵn còn nhận.
    mai = {}
    if ng == nay + timedelta(days=1):
        # Codex #588: chưa có phiếu ngày mai thì coi như phiếu rỗng, vẫn nhắc chọn
        # ngày trong khoảng đợt (trước bản sửa: nổ lỗi, đơn ngoài khoảng lọt qua).
        mai = {m: n for m, (n, _ten) in (_ton_phieu(ng) or {}).items() if n > 0}
    elif ng <= nay + timedelta(days=SO_NGAY_DAT_TRUOC):
        mai = {m: n for m, (n, _ten) in _con_btp_web(dong_btp, nay, so).items() if n > 0}
    xet = {m for m in set(rf) & ma_hang if refill.ngay_cua_refill(rf, m, ng) or m not in mai}
    return xet, refill.kiem_don([h for h in hang if h["variation_id"] in xet], ng, rf, con, mai)


def da_lam_dot_vuot(so, nay, doc_dong=None):
    """{(mã, ngày đầu đợt): số đơn của đợt đã có bánh Bếp làm}, cho các đợt refill
    nhận vượt số còn chạm ba ngày tới (Codex #594).

    Bếp nhập Bếp làm là máy đã trừ BTP sẵn và Đủ decor (btp.tru_vo_theo_sx), nên
    phần vượt đã làm không được trừ lần nữa trong con_btp. Đọc phiếu Kiểm bánh của MỌI
    ngày thuộc đợt (kể cả hôm nay và các ngày đã qua); ngày chưa có phiếu thì
    chưa ai nhập Bếp làm. `doc_dong(ngày)` trả dòng phiếu hoặc None (tiêm cho ca
    kiểm). Một nguồn cho thẻ web, cửa nhận đơn và cửa tạo đơn."""
    from vagabond import refill
    from vagabond.giu_vo import DON_GIU, _o_so

    if not so or so.get("loi"):
        return {}
    if doc_dong is None:
        def doc_dong(ng):
            ten = "KB-%s" % ng
            return frappe.get_doc("Kiem Banh Ngay", ten).dong if frappe.db.exists("Kiem Banh Ngay", ten) else None
    cuoi = nay + timedelta(days=SO_NGAY_DAT_TRUOC)
    nho, ra = {}, {}
    for ma, ds in (so.get("refill") or {}).items():
        for r in ds or []:
            c = r.get("con")
            tu, den = refill.ngay(r.get("tu")), refill.ngay(r.get("den"))
            if c is None or int(c) >= 0 or not tu or not den or tu > cuoi or den <= nay:
                continue
            lam, ng = 0, tu
            while ng <= den and (ng - tu).days < 62:
                if ng not in nho:
                    nho[ng] = doc_dong(ng) or []
                for d in nho[ng]:
                    ma_d = d.get("ma_hang") if hasattr(d, "get") else getattr(d, "ma_hang", None)
                    if str(ma_d or "") == str(ma):
                        don = sum(_o_so(d, o) for o in DON_GIU)
                        if don > 0:
                            lam += don - don_con_giu_vo(d)
                ng += timedelta(days=1)
            ra[(str(ma), tu.isoformat())] = lam
    return ra


def con_btp(dong_btp, kb_ngay, nay, rf=None, so=None, da_lam=None):
    """{mã: (BTP sẵn còn nhận, tên)} cho ngày kia và ngày thứ ba (v677). THUẦN.

    MỘT phép cho thẻ web, cửa nhận đơn, cửa giữ hàng và bảng Kiểm bánh. BTP sẵn
    trừ các đơn chưa làm của ba ngày tới (`kb_ngay` = [(ngày, dòng phiếu Kiểm
    bánh)], cùng cột với Có thể bán qua don_con_giu_vo: bánh Bếp làm đã trừ thẳng
    vào BTP sẵn nên không trừ lần hai). Ngày thuộc đợt refill (`rf` hiệu lực) thì
    đơn trừ vào mẻ, không trừ BTP; riêng đợt đã nhận đủ đơn (`so` của
    refill.tinh, con âm) thì phần vượt số của đợt lấy từ BTP nên trừ vào đây,
    chỉ phần vượt CHƯA được Bếp làm (`da_lam` của da_lam_dot_vuot); không truyền
    `da_lam` thì trừ cả phần vượt (thận trọng).

    v675 tới v676 phép này đọc Đủ decor (tên cũ con_decor). v677: đọc BTP sẵn,
    mọi dòng của bảng BTP (BTP 0 là hết vỏ, không phải chưa biết)."""
    from vagabond import refill

    def lay(d, k):
        return d.get(k) if hasattr(d, "get") else getattr(d, k, None)
    dd = {}
    for ngay_kb, dong in kb_ngay or []:
        for d in dong or []:
            ma = str(lay(d, "ma_hang") or "")
            if not ma or refill.ngay_cua_refill(rf, ma, ngay_kb):
                continue
            dd[ma] = dd.get(ma, 0) + don_con_giu_vo(d)
    if so and not so.get("loi"):
        cuoi = nay + timedelta(days=SO_NGAY_DAT_TRUOC)
        for ma, ds in (so.get("refill") or {}).items():
            for r in ds or []:
                c = r.get("con")
                tu, den = refill.ngay(r.get("tu")), refill.ngay(r.get("den"))
                if c is not None and int(c) < 0 and tu and den and tu <= cuoi and den > nay:
                    vuot = -int(c)
                    if da_lam is not None and r.get("da_dat") is not None:
                        chua_lam = max(0, int(r["da_dat"]) - int(da_lam.get((str(ma), tu.isoformat()), 0)))
                        vuot = min(vuot, chua_lam)
                    dd[str(ma)] = dd.get(str(ma), 0) + vuot
    ra = {}
    for d in dong_btp or []:
        ma = str(lay(d, "ma_hang") or "")
        if ma:
            ra[ma] = (int(lay(d, "so_btp") or 0) - dd.get(ma, 0), lay(d, "ten_banh") or ma)
    return ra


def kb_ba_ngay(nay):
    """[(ngày, dòng phiếu Kiểm bánh)] của ngày mai tới ngày thứ ba có phiếu."""
    kb = []
    for i in range(1, SO_NGAY_DAT_TRUOC + 1):
        ng = nay + timedelta(days=i)
        ten = "KB-%s" % ng
        if frappe.db.exists("Kiem Banh Ngay", ten):
            kb.append((ng, frappe.get_doc("Kiem Banh Ngay", ten).dong))
    return kb


def _con_btp_web(dong_btp, nay, so=None):
    """BTP sẵn còn nhận theo dữ liệu trên site (đọc phiếu ba ngày tới)."""
    from vagabond import refill

    return con_btp(dong_btp, kb_ba_ngay(nay), nay, refill.hieu_luc_tu_dong(dong_btp, nay), so, da_lam_dot_vuot(so, nay))


def so_web_ba_ngay(ma, nay, phieu_mai, pool, rf_mo=None, so=None):
    """[(ngày, số, nguồn)] web nhận cho mã `ma` từ ngày mai tới ngày thứ ba (v677). THUẦN.

    Cùng luật với thẻ web (kho-banh.js soThuong, gioiHanNhan) và cửa nhận đơn:
    ngày thuộc một đợt refill đang mở (`rf_mo` sau bo_dot_du_don) theo số còn
    của đợt đó; ngày mai theo Có thể bán của phiếu ngày mai (`phieu_mai` {mã: số},
    None khi chưa có phiếu: số None là chưa biết); ngày kia và ngày thứ ba theo
    `pool` của con_btp. Số âm giữ nguyên để bảng Kiểm bánh báo đã nhận quá; web
    hiện 0. Nguồn: "refill", "phieu" hay "btp", để bảng ghi số lấy từ đâu. Dùng
    cho bảng Kiểm bánh để Sales thấy đúng số khách thấy."""
    from vagabond import refill

    ra = []
    con_dot = {}
    for i in range(1, SO_NGAY_DAT_TRUOC + 1):
        ng = nay + timedelta(days=i)
        if rf_mo and refill.ngay_cua_refill(rf_mo, ma, ng):
            if ng not in con_dot:
                con_dot[ng] = refill.con_theo_ngay(so or {}, ng) if so and not so.get("loi") else {}
            c = con_dot[ng].get(ma)
            ra.append((ng, int(c) if c is not None else None, "refill"))
        elif i == 1:
            ra.append((ng, None if phieu_mai is None else int(phieu_mai.get(ma, 0)), "phieu"))
        else:
            ra.append((ng, int(pool.get(ma, 0)), "btp"))
    return ra


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
    """v671, v675: bánh đặt trước (có trên phiếu Kiểm bánh ngày mai hoặc bảng BTP)
    nhận tới ngày thứ ba. Đơn chọn ngày xa hơn thì nhắc. Bánh làm theo mẻ trong khoảng
    của mẻ và món của đợt Đặc biệt đã được bỏ ra trước khi gọi. Thuần."""
    nhac = []
    for h in hang or []:
        ma = h.get("variation_id")
        if ma in ten_dat_truoc:
            nhac.append("%s là bánh đặt trước, nhận trong 3 ngày tới. Cần nhận ngày %s "
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
    if mai < ng <= nay + timedelta(days=SO_NGAY_DAT_TRUOC):
        # v675, v677: ngày kia và ngày thứ ba theo BTP sẵn trừ đơn chưa làm. Đếm
        # refill hỏng thì không trừ phần vượt đợt (như mọi lỗi đếm: không chặn).
        if not hang:
            return nhac_rf
        from vagabond import refill
        dong_btp = frappe.get_single("BTP Banh O").dong
        so = None
        if refill.hieu_luc_tu_dong(dong_btp, nay):
            so = refill.tinh(nay, dong=dong_btp)
        ton = _con_btp_web(dong_btp, nay, so)
        # Bánh đặt trước (phiếu ngày mai) không có dòng BTP thì hết
        # chỗ cho ngày này, không phải chưa biết.
        ten_dt = {d.ma_hang: (d.ten_banh or d.ma_hang) for d in (dong_btp or [])}
        for m, (_n, t) in (_ton_phieu(mai) or {}).items():
            ten_dt.setdefault(m, t)
        for h in hang:
            if h["variation_id"] in ten_dt and h["variation_id"] not in ton:
                ton[h["variation_id"]] = (0, ten_dt[h["variation_id"]])
    elif ng > mai:
        # v671, v675: bánh đặt trước thường nhận tới ngày thứ ba. Xa hơn chỉ còn
        # bánh làm theo mẻ (đã xét ở trên) và món của đợt (bên gọi đã bỏ ra).
        if not hang:
            return nhac_rf
        ten = {d.ma_hang: (d.ten_banh or d.ma_hang) for d in (frappe.get_single("BTP Banh O").dong or [])}
        for m, (_n, t) in (_ton_phieu(mai) or {}).items():
            ten.setdefault(m, t)
        return list(nhac_rf) + chan_dat_truoc_ngay_xa(hang, ten, ng)
    else:
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
