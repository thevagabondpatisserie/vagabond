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
