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
    except frappe.ValidationError:
        return
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
    from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
    hd = _hoa_don_mua(10000000)
    ba = _tk_ngan_hang(hd.company)
    tk = frappe.db.get_value("Bank Account", ba, "account")
    pe = get_payment_entry("Purchase Invoice", hd.name, party_amount=3000000, bank_account=tk)
    pe.set("references", [])
    pe.bank_account = ba
    pe.reference_no, pe.reference_date = "COC-APP-THU", today()
    pe.insert(ignore_permissions=True)
    _DA_TAO.append((pe.doctype, pe.name))
    pe.submit()
    g = _giao_dich_ngan_hang("COC-APP-THU", 3000000, hd.company)
    g.add_payment_entries([{"payment_doctype": "Payment Entry", "payment_name": pe.name}])
    g.save(ignore_permissions=True)
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
