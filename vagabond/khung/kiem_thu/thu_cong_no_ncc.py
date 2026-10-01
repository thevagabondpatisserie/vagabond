"""#391: số đọc và Excel không được cắt, trộn tiền tệ hay bỏ phạm vi quyền."""
from unittest.mock import patch
from vagabond.khung.kiem_thu.nen import ca, la, dung
from vagabond import cong_no_ncc as cn


def dong(i=1, **doi):
    d = dict(name="HD-%s" % i, supplier="NCC-1", supplier_name="Nhà cung cấp", ma_ncc="M001",
        company="CTY", supplier_group="Hàng", posting_date="2026-09-01", bill_date="2026-09-02",
        bill_no="0001", due_date="2026-09-30", outstanding_amount=100, grand_total=100,
        base_grand_total=100, currency="VND", account_currency="VND")
    d.update(doi)
    return d


@ca("#391 không cộng lẫn ngoại tệ, phân biệt thiếu hạn với quá hạn")
def _tien_te():
    k = cn.tong_hop([dong(), dong(2, account_currency="USD", currency="USD", due_date=None)], "2026-10-01")
    la("hai số dư riêng", k["tong_theo_tien"], {"VND": 100, "USD": 100})
    la("chỉ tờ có hạn thật", k["qua_han_theo_tien"], {"VND": 100})


@ca("#391 giảm một phần không được gọi là đã thanh toán, hết dư không còn quá hạn")
def _trang_thai():
    ds = [dong(), dong(2, outstanding_amount=25), dong(3, outstanding_amount=0)]
    k = cn.tong_hop(ds,"2026-10-01", "tat_ca")
    la("đếm", k["dem"], dict(tat_ca=3, con_no=2, qua_han=2, mot_phan=1, het_no=1))
    la("tờ hết dư", cn.tong_hop(ds,"2026-10-01","het_no")["dong"][0]["tre_ngay"], 0)
    la("nhãn không suy tiền đã ra", cn.tong_hop(ds,"2026-10-01","mot_phan")["dong"][0]["trang_thai"], "Giảm một phần")


@ca("#391 chip ngày dùng ngày hóa đơn, tìm số HĐ giữ zero đầu, lọc nhóm")
def _loc():
    ds=[dong(),dong(2, bill_date="2026-10-01"),dong(3,supplier_group="Khác")]
    k=cn.tong_hop(ds,"2026-10-01",ky="thang_truoc",nhom="Hàng",tu_khoa="0001")
    la("cùng mọi bộ lọc", [r["name"] for r in k["dong"]], ["HD-1"])


@ca("#391 phân trang 30 chỉ cắt phần hiển thị, Excel xuất đủ và cùng lọc")
def _excel():
    ds=[dong(i, outstanding_amount=i) for i in range(1,66)]
    co=cn.frappe._dict(name="CTY",default_currency="VND")
    with patch.object(cn,"_doc",return_value=([co],co,ds)), patch.object(cn,"nowdate",return_value="2026-10-01"):
        k=cn.danh_sach(trang=2)
        la("trang cuối",len(k["dong"]),5)
        la("tổng không bị cắt",k["tong_theo_tien"]["VND"],2145)
        la("không còn",k["con_nua"],False)
        _,cot,ra=cn.xuat_ds(trang=2)
        la("Excel không lấy trang cuối",len(ra),65)
        la("Excel cùng tổng",sum(r["con_no"] for r in ra),2145)
        from vagabond.khung.cong_cu_ds import dung_bang
        ra[0]["supplier_name"]="=1+2"
        bang=dung_bang(cot,ra)
        la("Excel chặn công thức",bang[1][3],"'=1+2")


@ca("#391 đọc PI theo quyền và công ty, chỉ chứng từ ghi sổ, không ghi lại mã NCC")
def _doc_quyen():
    import sys, types
    goi=[]
    def ds(dt, **kw):
        goi.append((dt,kw))
        if dt=="Company": return [cn.frappe._dict(name="CTY",default_currency="VND")]
        if dt=="Purchase Invoice": return [cn.frappe._dict(dong(credit_to="331"))]
        if dt=="Supplier": return [cn.frappe._dict(name="NCC-1",custom_ma_ncc="M001",supplier_group="Hàng")]
        raise AssertionError(dt)
    mh=types.ModuleType("vagabond.mua_hang");mh._kiem_quyen=lambda:goi.append(("quyen",{}))
    with patch.dict(sys.modules,{"vagabond.mua_hang":mh}), patch.object(cn.frappe,"get_list",ds), patch.object(cn.frappe,"get_all",return_value=[("331","VND")]):
        _,_,ra=cn._doc("CTY")
        la("quyền trước dữ liệu",goi[0][0],"quyen")
        loc=next(k[1]["filters"] for k in goi if k[0]=="Purchase Invoice")
        la("đúng công ty",loc["company"],"CTY")
        la("đã ghi sổ",loc["docstatus"],1)
        la("không return",loc["is_return"],0)
        la("mã đã có",ra[0]["ma_ncc"],"M001")
        goi.clear(); _,co,ra=cn._doc("CTY NGOAI QUYEN")
        la("không đọc nhầm công ty",co,None)
        la("không truy PI",[t for t,k in goi], ["quyen","Company"])


@ca("#391 hóa đơn làm tròn chưa phân bổ không bị gắn giảm một phần")
def _lam_tron():
    k=cn.tong_hop([dong(grand_total=100.4,rounded_total=100)],"2026-10-01")
    la("không giảm",k["dem"]["mot_phan"],0)
