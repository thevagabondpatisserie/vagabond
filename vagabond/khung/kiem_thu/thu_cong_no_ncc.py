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


@ca("v549 trả trước ERP: số tiền không vượt dư trừ phần đang chờ duyệt")
def _so_tien_truoc_erp():
    la("đủ dư", cn.kiem_so_tien_truoc_erp(212090400, 212090400), None)
    dung("0 đồng", cn.kiem_so_tien_truoc_erp(0, 100))
    dung("âm", cn.kiem_so_tien_truoc_erp(-5, 100))
    dung("chữ", cn.kiem_so_tien_truoc_erp("abc", 100))
    dung("vượt dư", cn.kiem_so_tien_truoc_erp(101, 100))
    dung("vượt phần còn sau khi trừ nháp chờ duyệt", cn.kiem_so_tien_truoc_erp(60, 100, 50))
    la("vừa đủ phần còn lại", cn.kiem_so_tien_truoc_erp(50, 100, 50), None)
    dung("đã chờ duyệt hết dư", "chờ kế toán duyệt" in cn.kiem_so_tien_truoc_erp(1, 100, 100))


@ca("v549 trả trước ERP: ngày đã trả bắt buộc, không sau hôm nay")
def _ngay_truoc_erp():
    la("ngày hợp lệ", cn.kiem_ngay_tra("2026-04-10", "2026-04-04", "2026-10-01"), None)
    dung("thiếu ngày", cn.kiem_ngay_tra("", "2026-04-04", "2026-10-01"))
    dung("ngày tương lai", cn.kiem_ngay_tra("2026-10-02", "2026-04-04", "2026-10-01"))


@ca("v549 trả trước ERP: Nợ 331 đúng NCC và hóa đơn / Có tài khoản tạm, không đụng ngân hàng")
def _dong_truoc_erp():
    d = cn.dong_but_toan_truoc_erp({"name": "PI-1", "supplier": "NCC", "credit_to": "331 - TV"},
        "Temporary Opening - TV", 212090400, "Main - TV")
    la("hai dòng", len(d), 2)
    la("vế Nợ", (d[0]["account"], d[0]["party_type"], d[0]["party"], d[0]["debit_in_account_currency"],
        d[0]["reference_type"], d[0]["reference_name"]),
        ("331 - TV", "Supplier", "NCC", 212090400.0, "Purchase Invoice", "PI-1"))
    la("vế Có tài khoản tạm", (d[1]["account"], d[1]["credit_in_account_currency"]), ("Temporary Opening - TV", 212090400.0))
    dung("vế Có không gắn NCC/hóa đơn", "party" not in d[1] and "reference_name" not in d[1])
    la("cân", d[0]["debit_in_account_currency"], d[1]["credit_in_account_currency"])


@ca("v549 Codex #403: lap_truoc_erp khóa hóa đơn TRƯỚC khi tra mã lần (chạy chồng không lập hai bút toán)")
def _khoa_truoc_tra_ma():
    # Không dựng được hai giao dịch chồng nhau khi không có site; chốt thứ tự
    # trong mã nguồn để không ai đảo lại. Ca bench _tra_truoc_erp kiểm retry thật.
    import inspect
    nguon = inspect.getsource(cn.lap_truoc_erp)
    khoa = nguon.find("for update")
    tra = nguon.find('"cheque_no": ma_lan')
    dung("có khóa và có tra mã lần", khoa > 0 and tra > 0)
    dung("khóa đứng trước tra mã lần", khoa < tra)
    dung("tra mã lần bỏ qua nháp đã bỏ", "DAU_TRUOC_ERP" in nguon[tra:tra + 200])
    duyet = inspect.getsource(cn.duyet_truoc_erp)
    dung("duyệt có khóa hóa đơn", "for update" in duyet)
    dung("duyệt kiểm lại số tiền với dư sống", "kiem_so_tien_truoc_erp" in duyet)
    bo = inspect.getsource(cn.bo_truoc_erp)
    dung("từ chối không xóa bút toán", "delete_doc" not in bo)
