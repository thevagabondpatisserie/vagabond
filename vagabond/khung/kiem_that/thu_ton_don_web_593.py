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


@ca("F21 Document: Dư decor trừ đơn ba ngày và chỉ chặn đúng cửa sổ")
def _():
    b, ma = _bang_moi()
    b.append("dong", {"ma_hang":ma, "da_dat":1})
    b.insert(ignore_permissions=True)
    _DA_TAO.append((b.doctype,b.name))
    ngay=getdate(b.ngay)-timedelta(days=1)
    kho=frappe.get_single("BTP Banh O")
    # Nguồn singleton được khung rollback; chỉ thay bằng fixture trong ca.
    kho.set("dong",[])
    kho.append("dong",{"ma_hang":ma,"ten_banh":"Bánh F21","so_decor":2})
    kho.save(ignore_permissions=True)
    with patch.object(ton_don_web,"hom_nay",lambda:ngay):
        for i in (1,2,3):
            r=ton_don_web.kiem([{"variation_id":ma,"quantity":2}],ngay+timedelta(days=i))
            dung("còn1 ngày+%s"%i,"còn 1 cái" in r[0])
        la("ngày+4 không chặn",ton_don_web.kiem([{"variation_id":ma,"quantity":2}],ngay+timedelta(days=4)),[])
