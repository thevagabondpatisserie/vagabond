"""F21: đọc tồn từ Document thật, trong savepoint của khung bench."""
from datetime import timedelta
from unittest.mock import patch
import frappe
from frappe.utils import getdate
from vagabond import ton_don_web
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, la
from vagabond.khung.kiem_that.thu_kiem_banh_document import _bang_moi


@ca("F21 Document: tồn thay đổi sau khi tải, nguồn hôm nay không chặn đặt xa")
def _():
    b, ma = _bang_moi()
    b.append("dong", {"ma_hang":ma, "ten_banh":"Bánh F21", "ton_d1":2})
    b.insert(ignore_permissions=True)
    _DA_TAO.append((b.doctype,b.name))
    ngay=getdate(b.ngay)
    hang=[{"variation_id":ma,"quantity":2}]
    with patch.object(ton_don_web,"hom_nay",lambda:ngay):
        la("đủ số từ DB",ton_don_web.kiem(hang,ngay),[])
        b.dong[0].ton_d1=1
        b.save(ignore_permissions=True)
        dung("DB mới còn1", "còn 1 cái" in ton_don_web.kiem(hang,ngay)[0])
        b.dong[0].ton_d1=0
        b.save(ignore_permissions=True)
        dung("DB mới hết", "còn 0 cái" in ton_don_web.kiem(hang,ngay)[0])
        la("ngày xa không chặn",ton_don_web.kiem(hang,ngay+timedelta(days=4)),[])


@ca("v671, v675 Document: ngày mai theo Có thể bán của phiếu ngày mai (máy tính khi lưu), không theo Đủ decor; ngày kia và ngày thứ ba theo Đủ decor; ngày thứ tư không nhận")
def _():
    b, ma = _bang_moi()
    b.append("dong", {"ma_hang":ma, "ten_banh":"Bánh F21", "sx":3, "da_dat":1})
    b.insert(ignore_permissions=True)
    _DA_TAO.append((b.doctype,b.name))
    ngay=getdate(b.ngay)-timedelta(days=1)
    la("Có thể bán do máy tính khi lưu", frappe.db.get_value("Kiem Banh Dong", {"parent": b.name, "ma_hang": ma}, "co_the_ban"), 2)
    kho=frappe.get_single("BTP Banh O")
    # Nguồn singleton được khung rollback; chỉ thay bằng fixture trong ca.
    kho.set("dong",[])
    kho.append("dong",{"ma_hang":ma,"ten_banh":"Bánh F21","so_decor":9})
    kho.save(ignore_permissions=True)
    with patch.object(ton_don_web,"hom_nay",lambda:ngay):
        mai=ngay+timedelta(days=1)
        la("đặt 2 ngày mai: nhận",ton_don_web.kiem([{"variation_id":ma,"quantity":2}],mai),[])
        dung("đặt 3 ngày mai: còn 2 (Đủ decor 9 không tính)","còn 2 cái" in ton_don_web.kiem([{"variation_id":ma,"quantity":3}],mai)[0])
        # v675 (Sales 19/11/2026): ngày kia và ngày thứ ba theo Đủ decor (9; đơn ngày mai đã có
        # bánh Bếp làm nên không giữ vỏ), ngày thứ tư trở đi nhắc nhận trong 3 ngày tới.
        for i in (2,3):
            la("ngày+%s đặt 1: nhận theo Đủ decor"%i,ton_don_web.kiem([{"variation_id":ma,"quantity":1}],ngay+timedelta(days=i)),[])
            r=ton_don_web.kiem([{"variation_id":ma,"quantity":10}],ngay+timedelta(days=i))
            dung("ngày+%s đặt 10: còn 9"%i,len(r)==1 and "còn 9 cái" in r[0])
        r=ton_don_web.kiem([{"variation_id":ma,"quantity":1}],ngay+timedelta(days=4))
        dung("ngày+4: nhắc nhận trong 3 ngày tới",len(r)==1 and "nhận trong 3 ngày tới" in r[0])
