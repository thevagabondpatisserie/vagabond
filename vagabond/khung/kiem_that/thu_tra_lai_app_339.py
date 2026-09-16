"""#339: trả lại NCC, giữ sổ PI và sửa liên kết sau cancel/amend."""
import frappe
from vagabond import ho_so_tt as hs
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO, so_cai_cua
from vagabond.khung.kiem_that.thu_phan_bo_app import _app, _chan
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _hoa_don_mua


@ca("339 NCC: API từ chối/hủy hóa đơn có sẵn giữ nguyên GL và dư nợ")
def _():
    for buoc, tt in (("tu_choi", "Tu choi"), ("huy", "Huy")):
        hd = _hoa_don_mua(810000)
        h = _app(hd, 810000, "Cho ke toan")
        gl = so_cai_cua(hd)
        la("trả lại", hs.duyet(h.name, buoc, "Sửa hồ sơ")["trang_thai"], tt)
        h.reload(); hd.reload()
        la("trạng thái lưu thật", h.trang_thai, tt)
        la("PI vẫn submit", hd.docstatus, 1)
        la("dư nợ giữ", hd.outstanding_amount, 810000)
        la("GL giữ", so_cai_cua(hd), gl)


@ca("339 NCC: PI hủy sau lập, chặn duyệt nhưng trả lại và nối bản amend được")
def _():
    hd = _hoa_don_mua(810000)
    h = _app(hd, 810000, "Cho ke toan")
    hd.cancel()
    moi = frappe.copy_doc(hd)
    moi.amended_from = hd.name
    moi.docstatus = 0
    moi.insert(ignore_permissions=True)
    _DA_TAO.append((moi.doctype, moi.name))
    moi.submit()
    dung("duyệt PI hủy bị chặn", "đã hủy" in _chan(lambda: hs.duyet(h.name, "fin")))
    la("trả lại PI hủy", hs.duyet(h.name, "tu_choi", "Chọn bản sửa")["trang_thai"], "Tu choi")
    h.reload()
    h.dong[0].hoa_don = moi.name
    h.trang_thai = "Cho ke toan"
    h.save(ignore_permissions=True)
    h.reload()
    la("bản sửa", h.dong[0].hoa_don, moi.name)
    la("tổng giữ", h.tong_tien, 810000)
    la("duyệt lại được", hs.duyet(h.name, "fin")["trang_thai"], "Cho giam doc")


@ca("339 hoàn ứng: nguồn sinh chặn API và Document cả khi đổi sang NCC")
def _():
    hd = _hoa_don_mua(810000)
    h = _app(hd, 810000, "Cho ke toan")
    # Tái hiện dấu nguồn đúng do _sinh_hoa_don_hoan_ung ghi trên PI.
    # Chỉ fixture bench, không chỉnh chứng từ site thật.
    frappe.db.set_value("Purchase Invoice", hd.name, "remarks", "Hoàn ứng %s - NCC thử" % h.name)
    for buoc, tt in (("tu_choi", "Tu choi"), ("huy", "Huy")):
        dung("API chặn nguồn sinh", "ĐÃ GHI SỔ" in _chan(lambda: hs.duyet(h.name, buoc, "Thử trả lại")))
        h.reload()
        h.trang_thai = tt
        dung("Document cũng chặn", "ĐÃ GHI SỔ" in _chan(lambda: h.save(ignore_permissions=True)))
        h.reload()
        la("trạng thái không đổi", h.trang_thai, "Cho ke toan")
    hd.reload()
    la("không hủy PI hộ", hd.docstatus, 1)


@ca("339 Document: không được xóa/đổi link nguồn sinh cùng lúc từ chối")
def _():
    hd = _hoa_don_mua(810000)
    h = _app(hd, 810000, "Cho ke toan")
    frappe.db.set_value("Purchase Invoice", hd.name, "remarks", "Hoàn ứng %s - NCC thử" % h.name)
    for tt in ("Tu choi", "Huy"):
        h.reload()
        h.trang_thai = tt
        h.dong[0].hoa_don = ""
        dung("link bị xóa vẫn chặn nguồn cũ", "ĐÃ GHI SỔ" in _chan(lambda: h.save(ignore_permissions=True)))
        h.reload()
        la("link đã lưu giữ nguyên", h.dong[0].hoa_don, hd.name)
        la("không chuyển trạng thái", h.trang_thai, "Cho ke toan")
