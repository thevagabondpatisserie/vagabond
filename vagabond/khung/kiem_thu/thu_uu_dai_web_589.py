# -*- coding: utf-8 -*-
"""v589: ưu đãi trên website lấy từ ERP (anh Việt 09/10/2026).

ERP là nguồn duy nhất: chương trình khuyến mãi tích "Hiện trên website" thì
trang khách tự hiện, tắt hay hết hạn là web tự ẩn; đặt bánh trên web dùng
CHUNG bộ tính `khuyen_mai.tinh` của quầy. Các ca dưới:

  - gọi THẲNG phép thuần (ly_do_khong_web, the_web, thay_uu_dai_erp);
  - chạy `ap_web` THẬT với `tinh` THẬT, chỉ thay phần đọc cơ sở dữ liệu;
  - đối chiếu luật "dùng được trên web" giữa máy chủ và màn app (node) trên
    cùng một bảng ca, để hai bản không lệch nhau.
"""

import datetime
import json
import os
import subprocess
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import khuyen_mai as km  # noqa: E402
from vagabond import noi_dung_web as nw  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _ct(**k):
    c = {"name": "SN10", "ten": "Giảm 10% sinh nhật", "cach_thuc": "Giam tong hoa don", "kieu_giam": "Phan tram",
         "gia_tri": 10, "bat": 1, "hien_web": 1, "cach_ma": "Ma co dinh", "ma_co_dinh": "sn10", "can_otp": 0,
         "doi_tuong": "Moi khach", "kenh": "", "quay": "", "hd_toi_thieu": 500000, "sl_toi_thieu": 0,
         "tu_ngay": "2026-10-01", "den_ngay": "2026-10-31", "gio_tu": None, "gio_den": None, "uu_tien": 10,
         "cong_don": 0, "giam_toi_da": 0, "web_mo_ta": "Mừng sinh nhật", "web_anh": "/files/sn.jpg",
         "dong_mon": [], "dong_bac": []}
    for t in km.THU_TRONG_TUAN:
        c.setdefault(t, 0)
    c.update(k)
    return c


# Bảng ca chung cho luật "dùng được trên web" (máy chủ và màn app).
BANG_WEB = [
    ({}, ""),
    ({"cach_thuc": "Tang mon"}, "tặng món"),
    ({"cach_thuc": "Mua X tang Y"}, "tặng món"),
    ({"can_otp": 1}, "OTP"),
    ({"doi_tuong": "Theo hang khach"}, "hạng"),
    ({"doi_tuong": "Nhan vien"}, "hạng"),
    ({"kenh": "Pancake\nGrabFood"}, "Website"),
    ({"kenh": "Pancake\nWebsite"}, ""),
    ({"quay": "TCV"}, "quầy"),
    ({"quay": "TCV\nSALES"}, ""),
]


@ca("v589 luật dùng được trên web: tặng món, OTP, theo hạng/nhân viên, khác kênh Website, chỉ quầy thì không")
def _():
    for doi, mong in BANG_WEB:
        ly = km.ly_do_khong_web(_ct(**doi))
        dung("%s -> %r, được %r" % (doi, mong, ly), (mong in ly) if mong else ly == "")


@ca("v589 luật web của màn app (node) trùng máy chủ trên cùng bảng ca")
def _():
    src = open(os.path.join(GOC, "public", "js", "bep", "13-khuyen-mai.js"), encoding="utf-8").read()
    a = src.index("var KM_WEB_CACH"); b = src.index("function kmHtmlWeb")
    ca_js = [dict(_ct(**doi), hien_web=1) for doi, _m in BANG_WEB]
    kich = src[a:b] + "\nconsole.log(JSON.stringify(" + json.dumps(ca_js, ensure_ascii=False) + ".map(kmLyDoWeb)));"
    r = subprocess.run(["node", "-e", kich], capture_output=True, text=True, timeout=30)
    la("node chạy", r.returncode, 0)
    la("từng ca trùng nguyên câu", json.loads(r.stdout), [km.ly_do_khong_web(c) for c in ca_js])


@ca("v589 thẻ web từ một chương trình ERP: tên, mô tả, ảnh, mã viết hoa, đơn tối thiểu, hạn, điều kiện tự ghi")
def _():
    t = km.the_web(_ct(thu_7=1, thu_cn=1, gio_tu="07:00:00", gio_den="21:00:00", giam_toi_da=50000), "2026-10-09")
    la("khung", (t["id"], t["loai"], t["vi_tri"], t["hien"], t["nguon"]), ("erp-SN10", "uu_dai", "uu_dai", True, "erp"))
    la("chữ", (t["tieu_de"], t["noi_dung"], t["anh"], t["ma_uu_dai"], t["nhom"]),
       ("Giảm 10% sinh nhật", "Mừng sinh nhật", "/files/sn.jpg", "SN10", "Mã giảm giá"))
    la("hạn và giờ", (t["bat_dau"], t["ket_thuc"], t["gio_bat_dau"], t["gio_ket_thuc"], t["don_toi_thieu"]),
       ("2026-10-01", "2026-10-31", "07:00", "21:00", 500000))
    la("điều kiện", t["dieu_kien"].split("\n"),
       ["Giảm 10%, tối đa 50.000đ", "Áp dụng T7, CN.", "Đặt bánh trên web: nhập mã ở bước thanh toán."])
    la("dùng được trên web", t["dung_web"], 1)
    dung("mọi trường nằm trong bộ trường trang khách nhận", set(t) - {"nguon", "dung_web"} <= nw.TRUONG)


@ca("v589 thẻ web: tắt, chưa tích hiện web, hết hạn thì không hiện; tặng món vẫn hiện kèm câu chỉ dùng tại cửa hàng")
def _():
    la("tắt", km.the_web(_ct(bat=0), "2026-10-09"), None)
    la("chưa tích", km.the_web(_ct(hien_web=0), "2026-10-09"), None)
    la("hết hạn hôm qua", km.the_web(_ct(den_ngay="2026-10-08"), "2026-10-09"), None)
    dung("còn hạn tới hết hôm nay", km.the_web(_ct(den_ngay="2026-10-09"), "2026-10-09") is not None)
    t = km.the_web(_ct(cach_thuc="Tang mon", cach_ma="Khong can ma"), "2026-10-09")
    la("tặng món", (t["dung_web"], t["dieu_kien"].split("\n")[-1]), (0, "Chương trình tặng món chỉ dùng tại cửa hàng."))
    t = km.the_web(_ct(cach_ma="Ma dung mot lan", ma_co_dinh=""), "2026-10-09")
    la("mã dùng một lần không lộ mã", (t["ma_uu_dai"], "tiệm gửi riêng" in t["dieu_kien"]), ("", True))


@ca("v589 trang khách: bỏ hết ưu đãi gõ tay, chèn thẻ ERP vào đúng chỗ khối ưu đãi đầu tiên")
def _():
    khoi = [{"id": "a", "loai": "anh_bia"}, {"id": "u1", "loai": "uu_dai"}, {"id": "t", "loai": "tiec"},
            {"id": "u2", "loai": "uu_dai"}]
    ra = nw.thay_uu_dai_erp(khoi, [{"id": "erp-1", "loai": "uu_dai"}])
    la("thứ tự", [k["id"] for k in ra], ["a", "erp-1", "t"])
    la("không có khối ưu đãi cũ thì nối cuối", [k["id"] for k in nw.thay_uu_dai_erp([{"id": "a"}], [{"id": "erp-1"}])], ["a", "erp-1"])
    la("ERP trống thì trang không còn ưu đãi gõ tay", [k["id"] for k in nw.thay_uu_dai_erp(khoi, [])], ["a", "t"])


def _gia_db(ds):
    """Thay phần đọc cơ sở dữ liệu của khuyen_mai bằng danh sách chương trình."""
    theo_ten = {c["name"]: c for c in ds}
    return [
        patch.object(km, "_ds_web_tho", lambda chi_bat=True: [c for c in ds if c["hien_web"] and (c["bat"] or not chi_bat)]),
        patch.object(km, "_doc_ctkm", lambda ma: dict(theo_ten[ma])),
        patch.object(km, "_nhom_cua_mon", lambda ds_ma: {m: {"nhom": "Bánh kem", "ten": m} for m in ds_ma}),
        patch.object(km, "_dem_da_dung", lambda *a, **k: 0),
        patch.object(km.frappe.db, "exists", lambda dt, ten=None: (ten in theo_ten) if dt == "Vagabond CTKM" else False),
        patch.object(km.frappe.db, "get_value",
                     lambda dt, loc, cot=None, **k: ((theo_ten[next(n for n, c in theo_ten.items() if str(c.get("ma_co_dinh") or "").upper() == loc.get("ma_co_dinh"))]["name"],
                                                      "x") if dt == "Vagabond CTKM" and isinstance(loc, dict)
                                                     and any(str(c.get("ma_co_dinh") or "").upper() == loc.get("ma_co_dinh") and c["bat"] for c in ds) else None)),
    ]


def _chay(ds, ham):
    ps = _gia_db(ds)
    for p in ps:
        p.start()
    try:
        return ham()
    finally:
        for p in ps:
            p.stop()


GIO = [{"item_code": "BAWC00139", "qty": 2, "rate": 450000}]  # 900.000


@ca("v589 ap_web THẬT với tinh THẬT: mã cố định gõ chữ thường vẫn nhận, giảm đúng 10% của 900.000")
def _():
    with patch.object(km, "nowdate", lambda: "2026-10-09"), patch.object(km, "now_datetime", lambda: datetime.datetime(2026, 10, 9, 10, 0)):
        kq = _chay([_ct()], lambda: km.ap_web(GIO, ma="sn10", sdt="0931224334"))
    la("giảm", (kq["tong_giam"], kq["ly_do"], [a["ma"] for a in kq["ap"]]), (90000, "", ["SN10"]))


@ca("v589 ap_web: mã sai, chương trình chỉ dùng tại quầy, đơn chưa đủ tối thiểu đều trả lý do, không giảm")
def _():
    with patch.object(km, "nowdate", lambda: "2026-10-09"), patch.object(km, "now_datetime", lambda: datetime.datetime(2026, 10, 9, 10, 0)):
        sai = _chay([_ct()], lambda: km.ap_web(GIO, ma="KHONGCO"))
        otp = _chay([_ct(can_otp=1)], lambda: km.ap_web(GIO, ma="SN10"))
        thieu = _chay([_ct(hd_toi_thieu=1000000)], lambda: km.ap_web(GIO, ma="SN10"))
        het = _chay([_ct(den_ngay="2026-10-08")], lambda: km.ap_web(GIO, ma="SN10"))
    for ten, kq in (("mã sai", sai), ("cần OTP", otp), ("chưa đủ tối thiểu", thieu), ("hết hạn", het)):
        dung("%s có lý do" % ten, bool(kq["ly_do"]))
        la("%s không giảm" % ten, kq["tong_giam"], 0)
    dung("câu OTP", "OTP" in otp["ly_do"])
    dung("câu tối thiểu", "1.000.000" in thieu["ly_do"])


@ca("v589 ap_web không mã: tự áp chương trình 'Không cần mã' bật hiện web; không cộng dồn thì lấy cái lợi nhất")
def _():
    a = _ct(name="A", ma_co_dinh="", cach_ma="Khong can ma", kieu_giam="So tien", gia_tri=50000, hd_toi_thieu=0)
    b = _ct(name="B", ma_co_dinh="", cach_ma="Khong can ma", gia_tri=10, hd_toi_thieu=0)
    an = _ct(name="C", ma_co_dinh="", cach_ma="Khong can ma", gia_tri=50, hd_toi_thieu=0, hien_web=0)
    ma = _ct(name="D", cach_ma="Ma co dinh", ma_co_dinh="D20", gia_tri=20, hd_toi_thieu=0)
    with patch.object(km, "nowdate", lambda: "2026-10-09"), patch.object(km, "now_datetime", lambda: datetime.datetime(2026, 10, 9, 10, 0)):
        kq = _chay([a, b, an, ma], lambda: km.ap_web(GIO))
    la("chọn 10% (90.000) hơn 50.000, không áp chương trình ẩn web hay cần mã", (kq["tong_giam"], [x["ma"] for x in kq["ap"]]), (90000, ["B"]))


@ca("v589 ap_web: chương trình tặng món tự áp không bao giờ lên đơn web")
def _():
    t = _ct(name="T", cach_ma="Khong can ma", ma_co_dinh="", cach_thuc="Tang mon", hd_toi_thieu=0)
    with patch.object(km, "nowdate", lambda: "2026-10-09"), patch.object(km, "now_datetime", lambda: datetime.datetime(2026, 10, 9, 10, 0)):
        kq = _chay([t], lambda: km.ap_web(GIO))
    la("không giảm, không lỗi", (kq["tong_giam"], kq["ap"], kq["ly_do"]), (0, [], ""))


# ------------------------------------------------- trang đặt bánh (chạy thật)

GIO_WEB = r"""
CART.push({id:'BAWC00139',k:'Candle',cm:12,qty:2,adds:[],wish:'',price:450000});
EL('#f-name').value='Nguyen Van A';
EL('#f-phone').value='0912345678';
EL('#f-addr').value='9 Tran Cao Van, Quan 1, TP HCM';
setMode('pick');
var i13=SLOTS.findIndex(function(s){return s.from===13;});
pick(2); pickSlot(i13);
function goi(ham){ return GHI.goiMang.filter(function(x){return x.url.indexOf(ham)>=0;})
  .map(function(g){return JSON.parse(JSON.parse(g.opt.body).don);}); }
GHI.traLoi=function(url,opt){
  if(url.indexOf('xem_uu_dai')>=0){
    var d=JSON.parse(JSON.parse(opt.body).don);
    if(!d.ma_uu_dai) return {message:{ok:1,giam:0,ap:[]}};
    if(d.ma_uu_dai==='SN10') return {message:{ok:1,giam:90000,ap:[{ten:'Giảm sinh nhật',giam:90000}]}};
    return {message:{ok:0,ly_do:'ma_uu_dai',chi_tiet:'Mã '+d.ma_uu_dai+': chương trình đã hết hạn.'}};
  }
  if(url.indexOf('tao_don')>=0) return {message:{ok:0,ly_do:'ma_uu_dai',chi_tiet:'Mã SN10 vừa được dùng cho một đơn khác.'}};
  return null; };
openCoUI();
await CHO_XONG();
"""


def _trang(kich):
    from vagabond.khung.kiem_thu.thu_trang_dat_banh import _chay as chay_trang
    return chay_trang("2026-10-09T08:00:00", GIO_WEB + kich)


@ca("v589 trang đặt bánh: mở giỏ hỏi máy chủ ưu đãi tự áp; gõ mã chữ thường bấm Áp dụng thì gửi mã viết hoa kèm giỏ, hiện dòng giảm và tổng đã trừ")
def _():
    r = _trang(r"""
var dau=goi('xem_uu_dai');
EL('#f-ma').value=' sn10 '; apMaUuDai(); await CHO_XONG();
var sau=goi('xem_uu_dai');
RA({dau:dau.length, dau_ma:dau[0].ma_uu_dai, gui:sau[sau.length-1], hint:EL('#maHint').innerHTML, sum:EL('#sum').innerHTML, o:EL('#f-ma').value});
""")
    la("mở giỏ là hỏi một lần, chưa có mã", (r["dau"], r["dau_ma"]), (1, ""))
    la("gửi mã chuẩn hoá và giỏ", (r["gui"]["ma_uu_dai"], r["gui"]["items"]), ("SN10", [{"variation_id": "BAWC00139", "quantity": 2}]))
    la("ô mã viết hoa lại", r["o"], "SN10")
    dung("báo đã giảm", "Đã giảm 90.000" in r["hint"] and "Giảm sinh nhật" in r["hint"])
    dung("tóm tắt có dòng ưu đãi", "- 90.000" in r["sum"])
    dung("tổng đã trừ: 900.000 - 90.000", "810.000" in r["sum"])


@ca("v589 trang đặt bánh: mã sai hiện đúng câu máy chủ (không thành HTML), không trừ tiền; đổi giỏ thì hỏi lại")
def _():
    r = _trang(r"""
EL('#f-ma').value='<b>X</b>'; apMaUuDai(); await CHO_XONG();
var hint=EL('#maHint').innerHTML, sum=EL('#sum').innerHTML;
var truoc=goi('xem_uu_dai').length;
CART[0].qty=3; drawCo(); await CHO_XONG();
RA({hint:hint, sum:sum, hoi_lai:goi('xem_uu_dai').length-truoc});
""")
    dung("câu lỗi đã escape", "&lt;B&gt;X&lt;/B&gt;" in r["hint"] and "<B>" not in r["hint"])
    dung("không có dòng giảm", "Ưu đãi" not in r["sum"])
    la("đổi giỏ hỏi lại một lần", r["hoi_lai"], 1)


@ca("v589 trang đặt bánh: gửi đơn kèm mã; máy chủ báo mã vừa bị dùng thì khách đọc đúng câu đó")
def _():
    r = _trang(r"""
EL('#f-ma').value='SN10'; apMaUuDai(); await CHO_XONG();
tgl('dongy');
await submitOrder(); await CHO_XONG();
var don=goi('tao_don');
RA({so:don.length, ma:don[0]&&don[0].ma_uu_dai, hint:EL('#sendHint').innerHTML});
""")
    la("gửi một đơn kèm mã", (r["so"], r["ma"]), (1, "SN10"))
    dung("câu từ máy chủ", "vừa được dùng cho một đơn khác" in r["hint"])


@ca("v589 cong_khai: trang khách chỉ nhận ưu đãi từ ERP, ưu đãi gõ tay cũ không ra ngoài (đột biến bỏ lời gọi thay_uu_dai_erp phải đổ ca này)")
def _():
    import copy
    from vagabond.noi_dung_web import MAC_DINH
    ban = copy.deepcopy(MAC_DINH)
    ban["khoi"] = [{"id": "a", "loai": "banner"}, {"id": "cu", "loai": "uu_dai", "tieu_de": "Gõ tay cũ"}]
    with patch.object(nw, "_ban_cong_khai", lambda: copy.deepcopy(ban)), \
            patch.object(nw, "_the_uu_dai_erp", lambda: [{"id": "erp-SN", "loai": "uu_dai", "nguon": "erp"}]):
        ra = nw.cong_khai()
    la("thứ tự khối", [k["id"] for k in ra["khoi"]], ["a", "erp-SN"])


@ca("v589 trang đặt bánh: đổi giỏ thì tóm tắt bỏ ngay mức giảm cũ, chờ máy chủ tính lại mới hiện (đột biến bỏ kiểm khoá giỏ phải đổ ca này)")
def _():
    r = _trang(r"""
EL('#f-ma').value='SN10'; apMaUuDai(); await CHO_XONG();
var co=EL('#sum').innerHTML;
CART[0].qty=3; drawCo();
var ngay=EL('#sum').innerHTML;
await CHO_XONG();
RA({co:co, ngay:ngay, sau:EL('#sum').innerHTML});
""")
    dung("trước khi đổi có giảm", "- 90.000" in r["co"])
    dung("vừa đổi giỏ: chưa trừ mức giảm của giỏ cũ", "- 90.000" not in r["ngay"])
    dung("máy chủ trả lời xong thì hiện lại", "- 90.000" in r["sau"])


@ca("Codex #460 P1: khách đổi số điện thoại hoặc ngày nhận thì trang hỏi lại máy chủ, bỏ mức giảm cũ cho tới khi có câu trả lời mới")
def _():
    r = _trang(r"""
EL('#f-ma').value='SN10'; apMaUuDai(); await CHO_XONG();
var truoc=goi('xem_uu_dai').length;
EL('#f-phone').value='0987654321'; lookupPhone();
var ngay_doi_so=EL('#sum').innerHTML;
await CHO_XONG();
var sau_so=goi('xem_uu_dai');
pick(3); await CHO_XONG();
var sau_ngay=goi('xem_uu_dai');
RA({hoi_so:sau_so.length-truoc, so:sau_so[sau_so.length-1].dien_thoai, ngay_doi_so:ngay_doi_so,
    hoi_ngay:sau_ngay.length-sau_so.length, ngay:sau_ngay[sau_ngay.length-1].ngay_nhan, ngay_cu:sau_so[sau_so.length-1].ngay_nhan});
""")
    la("đổi số: hỏi lại một lần, gửi số mới", (r["hoi_so"], r["so"]), (1, "0987654321"))
    dung("vừa đổi số: chưa trừ mức giảm tính cho số cũ", "- 90.000" not in r["ngay_doi_so"])
    la("đổi ngày: hỏi lại một lần", r["hoi_ngay"], 1)
    dung("gửi ngày mới", r["ngay"] != r["ngay_cu"] and r["ngay"][:10] != r["ngay_cu"][:10])


@ca("Codex #460 P1: khách gõ mã rồi bấm gửi ngay, chưa kịp thấy mức giảm: trang hỏi máy chủ, dừng cho khách xem tổng mới, lần bấm sau mới gửi")
def _():
    r = _trang(r"""
tgl('dongy');
EL('#f-ma').value='SN10'; apMaUuDai();
await submitOrder(); await CHO_XONG();
var lan1=goi('tao_don').length, sum=EL('#sum').innerHTML;
await submitOrder(); await CHO_XONG();
RA({lan1:lan1, lan2:goi('tao_don').length, sum:sum});
""")
    la("lần đầu không gửi", r["lan1"], 0)
    dung("tóm tắt đã có mức giảm", "- 90.000" in r["sum"])
    la("lần sau gửi", r["lan2"], 1)


@ca("Codex #460 P1: khoa_ctkm khoá đúng các chương trình (FOR UPDATE, không trùng); tra_luot_web chỉ xoá lượt kênh Website chưa gắn hoá đơn của đúng đơn và trừ số đã dùng")
def _():
    goi = []

    def sql(q, v=None, as_dict=False):
        goi.append((" ".join(q.split()), v))
        if q.strip().startswith("select name, ctkm"):
            return [{"name": "SD-1", "ctkm": "SN10", "combo": None}, {"name": "SD-2", "ctkm": None, "combo": "CB1"}]
        return []
    with patch.object(km.frappe.db, "sql", sql, create=True):
        km.khoa_ctkm(["SN10", "B", "SN10", ""])
        km.khoa_ctkm([])
        n = km.tra_luot_web("Đơn web DW-1")
    la("một câu khoá, đủ hai chương trình, có FOR UPDATE", (goi[0][1], goi[0][0].endswith("for update")), (("B", "SN10"), True))
    sel = goi[1]
    dung("lọc đúng đơn, kênh Website, chưa có hoá đơn", sel[1] == ("Đơn web DW-1", "Website") and "ifnull(hoa_don, '')=''" in sel[0])
    la("trả hai lượt", n, 2)
    upd = [g for g in goi if g[0].startswith("update") and "da_dung" in g[0]]
    la("trừ số đã dùng đúng bảng", [g[1] for g in upd], [("SN10",), ("CB1",)])
    dung("CTKM rồi Combo", "tabVagabond CTKM`" in upd[0][0] and "tabVagabond Combo`" in upd[1][0])
    la("xoá đúng hai dòng", [g[1] for g in goi if g[0].startswith("delete")], [("SD-1",), ("SD-2",)])


@ca("Codex #460 vòng 2: giu_luot_web là phép giữ CHẶT: chèn dòng lỗi thì ném lỗi, không nuốt, không tự commit")
def _():
    chen, sql, commit = [], [], []

    class _D(dict):
        def insert(self, **k):
            if len(chen) == 1:
                raise RuntimeError("chèn hỏng")
            chen.append(dict(self))
    with patch.object(km.frappe, "get_doc", lambda d: _D(d)), \
            patch.object(km.frappe.db, "sql", lambda q, v=None, **k: sql.append((" ".join(q.split()), v)), create=True), \
            patch.object(km.frappe.db, "commit", lambda: commit.append(1), create=True), \
            patch.object(km, "now_datetime", lambda: datetime.datetime(2026, 10, 9, 10, 0)):
        km.giu_luot_web({"ap": [{"loai": "ctkm", "ma": "SN10", "ten": "SN", "giam": 90000}]},
                        khach="An", sdt="0931 224 334", ngay="2026-10-12", ghi_chu="Đơn web DW-1")
        la("một dòng, đúng ngày, kênh Website, ghi chú đơn", (chen[0]["ngay"], chen[0]["kenh"], chen[0]["ghi_chu"], chen[0]["sdt"]),
           ("2026-10-12", "Website", "Đơn web DW-1", "0931224334"))
        dung("tăng số đã dùng bằng một câu cộng tại chỗ", sql and "da_dung=ifnull(da_dung, 0)+1" in sql[0][0])
        try:
            km.giu_luot_web({"ap": [{"loai": "ctkm", "ma": "SN10", "giam": 1}]}, ghi_chu="Đơn web DW-2")
            dung("phải ném lỗi khi chèn hỏng", False)
        except RuntimeError:
            pass
    la("không tự commit", commit, [])


@ca("Codex #460 vòng 2: tra_luot_web trả cả mã dùng một lần đã giữ cho đúng đơn")
def _():
    goi = []

    def sql(q, v=None, as_dict=False):
        goi.append((" ".join(q.split()), v))
        return []
    with patch.object(km.frappe.db, "sql", sql, create=True):
        km.tra_luot_web("Đơn web DW-1")
    v = [g for g in goi if "tabVagabond Voucher" in g[0]]
    dung("trả mã theo ghi chú đơn, chỉ mã Đã dùng chưa có hoá đơn",
         len(v) == 1 and v[0][1] == ("Đơn web DW-1",) and "trang_thai='Da dung'" in v[0][0] and "hoa_don is null" in v[0][0])


@ca("Codex #460 vòng 3: không mã, hai chương trình cộng dồn được (50.000 + 50.000) và một không cộng dồn (60.000) thì lấy bộ cộng dồn 100.000, không lấy lẻ 60.000")
def _():
    a = _ct(name="A", ma_co_dinh="", cach_ma="Khong can ma", kieu_giam="So tien", gia_tri=50000, hd_toi_thieu=0, cong_don=1, uu_tien=1)
    b = _ct(name="B", ma_co_dinh="", cach_ma="Khong can ma", kieu_giam="So tien", gia_tri=50000, hd_toi_thieu=0, cong_don=1, uu_tien=2)
    c = _ct(name="C", ma_co_dinh="", cach_ma="Khong can ma", kieu_giam="So tien", gia_tri=60000, hd_toi_thieu=0, cong_don=0, uu_tien=3)
    with patch.object(km, "nowdate", lambda: "2026-10-09"), patch.object(km, "now_datetime", lambda: datetime.datetime(2026, 10, 9, 10, 0)):
        kq = _chay([a, b, c], lambda: km.ap_web(GIO))
    la("bộ có lợi nhất", (kq["tong_giam"], sorted(x["ma"] for x in kq["ap"])), (100000, ["A", "B"]))


@ca("Codex #460 vòng 3: có mã thì vẫn cộng thêm được các chương trình tự áp cộng dồn, kể cả khi có một chương trình tự áp không cộng dồn")
def _():
    ma = _ct(name="M", cach_ma="Ma co dinh", ma_co_dinh="M10", kieu_giam="So tien", gia_tri=40000, hd_toi_thieu=0, cong_don=1, uu_tien=1)
    a = _ct(name="A", ma_co_dinh="", cach_ma="Khong can ma", kieu_giam="So tien", gia_tri=50000, hd_toi_thieu=0, cong_don=1, uu_tien=2)
    c = _ct(name="C", ma_co_dinh="", cach_ma="Khong can ma", kieu_giam="So tien", gia_tri=60000, hd_toi_thieu=0, cong_don=0, uu_tien=3)
    with patch.object(km, "nowdate", lambda: "2026-10-09"), patch.object(km, "now_datetime", lambda: datetime.datetime(2026, 10, 9, 10, 0)):
        kq = _chay([ma, a, c], lambda: km.ap_web(GIO, ma="m10"))
    la("mã cộng chương trình cộng dồn", (kq["tong_giam"], sorted(x["ma"] for x in kq["ap"])), (90000, ["A", "M"]))


@ca("Codex #460 vòng 3: tra_luot_web khoá dòng lượt dùng (FOR UPDATE) trước khi trừ số đã dùng, để hai lần trả cùng lúc không trừ hai lần")
def _():
    goi = []

    def sql(q, v=None, as_dict=False):
        goi.append(" ".join(q.split()))
        return []
    with patch.object(km.frappe.db, "sql", sql, create=True):
        km.tra_luot_web("Đơn web DW-1")
    dung("câu chọn dòng có for update", goi[0].startswith("select name, ctkm") and goi[0].endswith("for update"))


@ca("Codex #460 vòng 3: tinh_co_khoa (quầy dùng chung giao thức với web): tính, commit, khoá đúng chương trình đã áp, tính lại và dùng kết quả lần sau")
def _():
    vet, lan = [], []

    def tinh(items, **k):
        lan.append(k)
        vet.append("tinh")
        return {"tong_giam": 10 * len(lan), "ap": [{"loai": "ctkm", "ma": "SN10"}, {"loai": "combo", "ma": "CB"}]}
    with patch.object(km, "tinh", tinh), \
            patch.object(km.frappe.db, "commit", lambda: vet.append("commit"), create=True), \
            patch.object(km, "khoa_ctkm", lambda ds: vet.append(("khoa", list(ds)))):
        kq = km.tinh_co_khoa([{"item_code": "X"}], ctkm=["SN10"], quay="TCV")
    la("thứ tự", vet, ["tinh", "commit", ("khoa", ["SN10"]), "tinh"])
    la("dùng kết quả tính sau khi khoá", kq["tong_giam"], 20)
    la("truyền nguyên tham số", lan[1], {"ctkm": ["SN10"], "quay": "TCV"})


@ca("Codex #460 vòng 3: màn tính tiền quầy dùng tinh_co_khoa và giữ lượt TRƯỚC commit hoá đơn (cùng giao dịch với khoá), không ghi lượt sau khi đã nhả khoá")
def _():
    src = open(os.path.join(GOC, "ban_hang.py"), encoding="utf-8").read()
    than = src[src.index("def tao_don_tay("):]
    than = than[:than.index("\ndef ", 10)]
    dung("không còn gọi tinh trần", "_km.tinh(" not in than and "_km.tinh_co_khoa(" in than)
    i_save = than.index("si.save()")
    i_ghi = than.index("_km.ghi_su_dung(")
    i_commit = than.index("frappe.db.commit()", i_save)
    dung("ghi lượt nằm giữa lưu hoá đơn và commit đầu tiên sau đó", i_save < i_ghi < i_commit)
    la("chỉ ghi lượt một lần", than.count("ghi_su_dung("), 1)
