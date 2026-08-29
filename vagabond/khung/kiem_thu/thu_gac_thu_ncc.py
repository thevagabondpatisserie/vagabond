# -*- coding: utf-8 -*-
"""Ca kiểm cho hàng rào thư gửi nhà cung cấp.

Toàn phép thuần, chạy được trên máy CI tay không.

Số liệu lấy từ site thật ngày 28/08/2026: 120 lá thư trên 97 đơn mua, trong
đó 1 lá gửi cho đơn đã huỷ và 5 lá gửi tới địa chỉ ngoài hồ sơ.
"""

from vagabond import gac_thu_ncc as G
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("thu ncc: don da duyet thi thu di binh thuong")
def _da_duyet():
    la("docstatus 1 cho di", G.xet_thu_don_mua(1), G.THU_OK)


@ca("thu ncc: don nhap va don huy thi CHAN")
def _chan():
    la("don nhap", G.xet_thu_don_mua(0), G.THU_CHAN_NHAP)
    # Ca that: PUR-ORD-2026-00056 gui Thanh An Eggpack sau khi don da huy.
    la("don huy", G.xet_thu_don_mua(2), G.THU_CHAN_HUY)


@ca("thu ncc: trang thai la thi CHO DI chu khong chan")
def _la_thi_cho_di():
    # Nguyen tac 3: tha lot mot la thu con hon chan ca hop thu cua tiem vi
    # mot loi cua minh. Ngay 16/08/2026 da co bon ngay ca tiem khong gui
    # duoc thu nao vi mot hook dat sai.
    la("None cho di", G.xet_thu_don_mua(None), G.THU_OK)
    la("chuoi rac cho di", G.xet_thu_don_mua("abc"), G.THU_OK)
    la("chuoi rong cho di", G.xet_thu_don_mua(""), G.THU_OK)
    la("so la cho di", G.xet_thu_don_mua(9), G.THU_OK)


@ca("thu ncc: cau bao loi noi ro phai lam gi")
def _cau_bao():
    c = G.loi_thu_bi_chan(G.THU_CHAN_HUY, "DMH-2026-00056", "Thanh An Eggpack")
    dung("noi ten don", "DMH-2026-00056" in c)
    dung("noi ten nha cung cap", "Thanh An Eggpack" in c)
    dung("noi ro hau qua", "không còn hiệu lực" in c)
    dung("chi duong ra", "lập đơn mới" in c)
    c2 = G.loi_thu_bi_chan(G.THU_CHAN_NHAP, "DMH-2026-00099", "")
    dung("chua co ten thi goi chung", "nhà cung cấp" in c2)
    dung("noi phai duyet truoc", "Duyệt đơn" in c2)
    for cam in ("docstatus", "Communication", "reference_doctype"):
        dung("khong lo tu ky thuat %s" % cam, cam not in c and cam not in c2)


@ca("thu ncc: tach dia chi nguoi nhan")
def _tach():
    la("mot dia chi", G.tach_dia_chi("a@b.com"), ["a@b.com"])
    la("nhieu dia chi", G.tach_dia_chi("a@b.com, c@d.com"), ["a@b.com", "c@d.com"])
    la("dau cham phay cung tach", G.tach_dia_chi("a@b.com; c@d.com"), ["a@b.com", "c@d.com"])
    la("rong", G.tach_dia_chi(""), [])
    la("None", G.tach_dia_chi(None), [])


@ca("thu ncc: dia chi ngoai ho so")
def _dia_chi():
    ho_so = ["po-vietnam@simba.com.vn"]
    # Ca that: PUR-ORD-2026-00042 gui toi gmail ca nhan.
    la("gui ra ngoai", G.dia_chi_la(["tranhuynhnhauyen99@gmail.com"], ho_so),
       ["tranhuynhnhauyen99@gmail.com"])
    la("gui dung thi rong", G.dia_chi_la(["po-vietnam@simba.com.vn"], ho_so), [])
    la("khac hoa thuong van la mot", G.dia_chi_la(["PO-Vietnam@Simba.com.vn"], ho_so), [])
    # Ho so chua khai dia chi nao thi KHONG keu, vi do la thieu du lieu chu
    # khong phai gui sai. Keu ca 100 phan tram thi khong ai doc nua.
    la("ho so trong thi khong keu", G.dia_chi_la(["ai@do.com"], []), [])
    la("ho so None thi khong keu", G.dia_chi_la(["ai@do.com"], None), [])


@ca("thu ncc: hang rao chi dong vao dung loai thu")
def _pham_vi():
    import inspect

    ma = inspect.getsource(G.chan_thu_don_hong)
    dung("chi don mua hang", 'reference_doctype") or "") != DON_MUA' in ma)
    dung("chi thu gui DI", '!= "Sent"' in ma)
    dung("dia chi la thi khong chan, chi ghi nhat ky", "frappe.log_error" in ma)
    dung("chi throw mot lan", ma.count("frappe.throw") == 1)
    # Nguyen tac 3: doc du lieu hong thi cho thu di.
    dung("boc try khi doc don", "except Exception:" in ma)
    # Tuyet doi khong duoc sua noi dung thu.
    for cam in (".save(", "db_set", "doc.recipients =", "doc.sender ="):
        dung("khong %s" % cam, cam not in ma)


@ca("thu ncc: bang ra chi doc, khong sua gi")
def _bang_ra_chi_doc():
    import inspect

    ma = inspect.getsource(G.soat_thu_ncc)
    for cam in (".save(", ".delete(", "db_set", "frappe.delete_doc", "set_value"):
        dung("khong %s" % cam, cam not in ma)
    dung("da khai o cua ngo", True)


@ca("thu ncc: phan thuan khong cham Frappe")
def _thuan_that():
    import inspect

    for f in (G.xet_thu_don_mua, G.loi_thu_bi_chan, G.dia_chi_la, G.tach_dia_chi):
        dung("%s khong goi frappe" % f.__name__, "frappe." not in inspect.getsource(f))


@ca("thu ncc: da gan hook va da khai cua ngo")
def _da_gan():
    import inspect
    import os

    from vagabond import hooks

    ma = inspect.getsource(hooks)
    doan = ma.split('"Communication"', 1)
    dung("co hook Communication", len(doan) > 1)
    dung("goi dung ham", "gac_thu_ncc.chan_thu_don_hong" in doan[1][:400])

    goc = os.path.dirname(os.path.abspath(__file__))
    cn = open(os.path.join(goc, "thu_cua_ngo.py"), encoding="utf-8").read()
    dung("khai soat_thu_ncc o cua ngo", '"soat_thu_ncc"' in cn)
