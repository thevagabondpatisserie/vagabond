"""Các đợt chi và cấn cọc trên lõi ERPNext thật."""
import frappe
from frappe.utils import today
from vagabond import ho_so_tt as hs, coc_app
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua, _tk_ngan_hang, _unc_gia, _giao_dich_ngan_hang
from vagabond.khung.kiem_that.thu_doi_chieu_app_247 import _ghi


def _app(hd, tien, tt="Da duyet"):
    h = frappe.new_doc("Vagabond Ho So TT")
    h.ma, h.loai, h.ngay = hs._sinh_ma(), "NCC", today()
    h.tk_chi = _tk_ngan_hang(hd.company)
    h.nha_cung_cap, h.ten_ncc = hd.supplier, hd.supplier_name
    h.trang_thai, h.da_tam_ung = tt, 0
    h.append("dong", {"hoa_don": hd.name, "so_tien": tien,
        "tong_hd": hd.grand_total, "con_no": hd.outstanding_amount})
    h.insert(ignore_permissions=True)
    _DA_TAO.append((h.doctype, h.name))
    return h


def _chan(lam):
    try:
        lam()
    except frappe.ValidationError as exc:
        return str(exc)
    dung("phải chặn", False)


@ca("APP từng đợt: 10 triệu trả 3 rồi 7, lõi GL/BT và retry")
def _():
    hd = _hoa_don_mua(10000000)
    a = _app(hd, 3000000)
    b = _app(hd, 7000000)
    _chan(lambda: _app(hd, 1))
    for h, tien, no in ((a, 3000000, 7000000), (b, 7000000, 0)):
        _unc_gia(h)
        g = _giao_dich_ngan_hang(h.name, tien, hd.company)
        _ghi(h, g)
        hd.reload()
        la("dư nợ", float(hd.outstanding_amount), float(no))
        la("retry", hs.danh_dau_da_tra(h.name, gui_thu=0)["da_lam_roi"], 1)


@ca("APP từng đợt: nháp không giữ tiền, gửi duyệt phải kiểm lại")
def _():
    hd = _hoa_don_mua(10000000)
    a, b = _app(hd, 7000000, "Nhap"), _app(hd, 7000000, "Nhap")
    a.trang_thai = "Cho ke toan"
    a.save(ignore_permissions=True)
    b.trang_thai = "Cho ke toan"
    _chan(lambda: b.save(ignore_permissions=True))
    a.dong[0].so_tien = 9000000
    _chan(lambda: a.save(ignore_permissions=True))


@ca("APP cọc: cấn lõi giảm nợ, không thêm GL ngân hàng, retry không cấn đôi")
def _():
    hd, pe, g = _coc()
    truoc = frappe.db.count("GL Entry", {"voucher_type": "Payment Entry", "voucher_no": pe.name})
    args = dict(ncc=hd.supplier, payment_entry=pe.name,
        hoa_don=[{"hoa_don": hd.name, "so_tien": 2000000}], ma_lan="thu-coc-app-247-0001")
    coc_app.can_coc(**args)
    hd.reload()
    la("nợ sau cấn", float(hd.outstanding_amount), 8000000.0)
    la("retry", coc_app.can_coc(**args)["da_lam_roi"], 1)
    hd.reload()
    la("không cấn hai lần", float(hd.outstanding_amount), 8000000.0)
    la("không thêm GL", frappe.db.count("GL Entry", {"voucher_type": "Payment Entry", "voucher_no": pe.name}), truoc)
    args["hoa_don"][0]["so_tien"] = 1000000
    _chan(lambda: coc_app.can_coc(**args))


def _coc(theo_po=False):
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    hd = _hoa_don_mua(10000000)
    ba = _tk_ngan_hang(hd.company)
    tk = frappe.db.get_value("Bank Account", ba, "account")
    dt, ten = "Purchase Invoice", hd.name
    if theo_po:
        po = frappe.get_doc({"doctype": "Purchase Order", "supplier": hd.supplier,
            "company": hd.company, "transaction_date": today(), "schedule_date": today(),
            "currency": "VND", "conversion_rate": 1, "items": [{"item_code": hd.items[0].item_code,
            "qty": 1, "rate": 10000000, "schedule_date": today(), "uom": hd.items[0].uom}]})
        po.insert(ignore_permissions=True)
        _DA_TAO.append((po.doctype, po.name))
        po.submit()
        dt, ten = "Purchase Order", po.name
    pe = get_payment_entry(dt, ten, party_amount=3000000, bank_account=tk)
    if not theo_po:
        pe.set("references", [])
    pe.bank_account = ba
    pe.reference_no, pe.reference_date = "COC-APP-THU", today()
    pe.insert(ignore_permissions=True)
    _DA_TAO.append((pe.doctype, pe.name))
    f = frappe.get_doc({"doctype": "File", "file_name": "UNC-coc-thu.txt",
        "content": "UNC thu tren bench", "is_private": 1,
        "attached_to_doctype": "Payment Entry", "attached_to_name": pe.name})
    f.insert(ignore_permissions=True)
    _DA_TAO.append((f.doctype, f.name))
    g = _giao_dich_ngan_hang(pe.name, 3000000, hd.company)
    if theo_po:
        from vagabond import duyet_chi
        pe.workflow_state = duyet_chi.TT_DA_DUYET_CHI
        pe.vgb_chi_unc = frappe.as_json([f.file_url])
        pe.save(ignore_permissions=True)
        duyet_chi.xac_nhan_da_chuyen(pe.name, ma_giao_dich=g.name)
        pe.reload()
    else:
        pe.submit()
    coc_app.noi_sao_ke_coc(hd.supplier, pe.name, g.name)
    coc_app.noi_sao_ke_coc(hd.supplier, pe.name, g.name)
    g.reload()
    la("sao kê chỉ một liên kết", len(g.payment_entries), 1)
    return hd, pe, g


@ca("APP cọc neo PO: số chưa phân bổ 0 vẫn cấn được và trả phần còn lại")
def _():
    hd, pe, g = _coc(theo_po=True)
    la("PE chưa phân bổ bằng 0", float(pe.unallocated_amount), 0.0)
    ds = coc_app.danh_sach(hd.supplier)
    dung("cọc PO có trong danh sách", any(x["name"] == pe.name for x in ds["rows"]))
    kq = coc_app.can_coc(hd.supplier, pe.name,
        [{"hoa_don": hd.name, "so_tien": 3000000}], "coc-po-247-0001")
    la("cấn được", kq["ok"], 1)
    hd.reload()
    la("còn nợ 7 triệu", float(hd.outstanding_amount), 7000000.0)
    h = _app(hd, 7000000)
    _unc_gia(h)
    g2 = _giao_dich_ngan_hang(h.name, 7000000, hd.company)
    _ghi(h, g2)
    hd.reload()
    la("hết nợ", float(hd.outstanding_amount), 0.0)


@ca("APP cọc: từ chối số đã bị APP khác giữ, retry cùng kết quả")
def _():
    hd, pe, g = _coc()
    _app(hd, 9000000)
    args = dict(ncc=hd.supplier, payment_entry=pe.name,
        hoa_don=[{"hoa_don": hd.name, "so_tien": 2000000}], ma_lan="coc-bi-giu-247-0001")
    kq = coc_app.can_coc(**args)
    la("từ chối", kq["ok"], 0)
    la("retry từ chối", coc_app.can_coc(**args)["ok"], 0)
    pe.reload(); hd.reload()
    la("cọc nguyên", float(pe.unallocated_amount), 3000000.0)
    la("nợ nguyên", float(hd.outstanding_amount), 10000000.0)


@ca("APP cửa tạo trên app: số 0/âm không thành toàn bộ hóa đơn, 3 triệu giữ đúng")
def _():
    hd = _hoa_don_mua(10000000)
    for tien in (0, -1, "NaN", "Infinity", "abc"):
        _chan(lambda: hs.tao(ncc=hd.supplier, hoa_don=[{"hoa_don": hd.name, "so_tien": tien}]))
    kq = hs.tao(ncc=hd.supplier, hoa_don=[{"hoa_don": hd.name, "so_tien": 3000000}])
    h = frappe.get_doc("Vagabond Ho So TT", kq["ma"])
    _DA_TAO.append((h.doctype, h.name))
    la("3 triệu trên dòng", float(h.dong[0].so_tien), 3000000.0)
    la("3 triệu trên tổng", float(h.tong_tien), 3000000.0)
    la("nháp", h.trang_thai, "Nhap")


@ca("APP Document: đổi NCC sau lập mới và đổi phân bổ sau duyệt bị chặn")
def _():
    hd = _hoa_don_mua(10000000)
    h = _app(hd, 3000000)
    h.dong[0].so_tien = 4000000
    _chan(lambda: h.save(ignore_permissions=True))
    h.reload()
    la("số đã duyệt còn nguyên", float(h.dong[0].so_tien), 3000000.0)
    other = frappe.copy_doc(frappe.get_doc("Supplier", hd.supplier))
    other.supplier_name = "Thử APP NCC khác " + frappe.generate_hash(length=8)
    other.insert(ignore_permissions=True)
    _DA_TAO.append((other.doctype, other.name))
    moi = frappe.copy_doc(h)
    moi.ma, moi.trang_thai, moi.nha_cung_cap = hs._sinh_ma(), "Nhap", other.name
    cau = _chan(lambda: moi.insert(ignore_permissions=True))
    dung("chặn đúng sai NCC", "không thuộc nhà cung cấp" in cau)


@ca("APP bản in: có số gốc, đã giảm nợ, đợt chi và lịch sử lõi")
def _():
    hd, pe, g = _coc()
    kq = coc_app.can_coc(hd.supplier, pe.name,
        [{"hoa_don": hd.name, "so_tien": 3000000}], "coc-in-247-0001")
    la("cấn trước", kq["ok"], 1)
    hd.reload()
    h = _app(hd, 4000000)
    html = hs._to_app_html(h.name)
    dung("gốc10 triệu", "Gốc: " + hs._tien(10000000) in html)
    dung("đã giảm nợ3 triệu", "đã giảm nợ trước khi lập: " + hs._tien(3000000) in html)
    dung("đợt này4 triệu", "chi đợt này: " + hs._tien(4000000) in html)
    dung("còn nợ lúc in7 triệu", "còn nợ lúc in: " + hs._tien(7000000) in html)
    dung("dẫn đúng PE cọc", pe.name in html)
