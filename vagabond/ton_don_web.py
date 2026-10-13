"""F21, PR471: chỉ từ chối khi có dòng tồn thật cho ngày nhận.

Không dùng danh mục công khai vì danh mục bỏ dòng tồn 0. Không có dòng
nguồn là chưa biết, không phải hết hàng. Dư decor chỉ phục vụ ba ngày tới,
không được dùng số hôm nay để chặn bánh làm theo đơn nhiều ngày sau.
"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import frappe


def hom_nay():
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date()


def kiem(hang, ngay):
    ng = datetime.fromisoformat(str(ngay)).date()
    nay = hom_nay()
    if ng != nay and not nay < ng <= nay + timedelta(days=3):
        return []
    ma = {h["variation_id"] for h in hang}
    ton = {}
    if ng == nay:
        ten = "KB-%s" % nay
        if not frappe.db.exists("Kiem Banh Ngay", ten):
            return []
        for d in frappe.get_doc("Kiem Banh Ngay", ten).dong:
            if d.ma_hang in ma:
                ton[d.ma_hang] = (max(0, int(d.co_the_ban or 0)), d.ten_banh or d.ma_hang)
    else:
        kho = frappe.get_single("BTP Banh O")
        da_dat = {}
        for i in (1, 2, 3):
            ten = "KB-%s" % (nay + timedelta(days=i))
            if frappe.db.exists("Kiem Banh Ngay", ten):
                for d in frappe.get_doc("Kiem Banh Ngay", ten).dong:
                    da_dat[d.ma_hang] = da_dat.get(d.ma_hang, 0) + int(d.da_dat or 0)
        for d in kho.dong or []:
            if d.ma_hang in ma:
                ton[d.ma_hang] = (max(0, int(d.so_decor or 0) - da_dat.get(d.ma_hang, 0)), d.ten_banh or d.ma_hang)
    nhac = []
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
        from vagabond.lib import cfg_o
        from vagabond.gui_thu import ban_webhook
        url = str(cfg_o("webhook_don_web") or "").strip()
        cau = ("Sales kiểm lại tồn đơn web — ngày nhận %s. Phép kiểm tồn bị lỗi; "
               "web vẫn tiếp nhận yêu cầu. Sales kiểm lại tồn trước khi xác nhận với khách." % ngay)
        if not url or not ban_webhook(cau, url=url):
            _ghi_loi("Kiểm tra webhook_don_web và kênh nhận đơn của Sales.",
                     "F21: chưa gửi được cảnh báo Sales")
    except Exception:
        try:
            _ghi_loi(frappe.get_traceback(), "F21: chưa gửi được cảnh báo Sales")
        except Exception:
            pass
