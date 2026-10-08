# -*- coding: utf-8 -*-
"""Ca kiểm v586: trình biên tập website theo việc và đăng ký tiệc.

Minh Vũ đề xuất, anh Việt duyệt 07/10/2026: bỏ trình dựng trang theo khối
làm màn chính, chia theo việc (Ưu đãi, Tiệc, Tuyển dụng, Cửa hàng, Trang và
chữ, Liên hệ), lưu là khách thấy ngay. Các ca dưới đây:

  - gọi THẲNG phép thuần (ap_muc, xoa_muc, ap_nhan, chuan_hoa...);
  - gọi hàm máy chủ thật (luu_muc, xoa_muc_web, luu_lien_he, tiec_web.dang_ky)
    trên một site giả giữ bản nháp và bản công khai riêng, để chốt tính chất
    quan trọng nhất: lưu một mục KHÔNG cuốn theo phần nháp chưa xuất bản của
    trình cũ;
  - chạy cùng một bảng mẫu trạng thái với bộ kiểm JS.
"""

import copy
import io
import json
import os
import re
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

# Frappe giả của nen.py không có frappe.rate_limiter; dựng tạm ở đây (như
# thu_quan_ly_nguoi_dung dựng frappe.core), decorator để nguyên hàm.
if "frappe.rate_limiter" not in sys.modules:
    sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
    sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import noi_dung_web as nw  # noqa: E402
from vagabond import tiec_web as tw  # noqa: E402

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAU_TT = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "mau_web", "trang_thai_586.json"), encoding="utf-8"))


def bi_chan(nd, chu=None):
    try:
        nw.chuan_hoa(nd)
    except (ValueError, TypeError) as e:
        return chu is None or chu in str(e)
    return False


def _uu(**k):
    m = {"id": "uu-1", "loai": "uu_dai", "vi_tri": "uu_dai", "hien": True, "tieu_de": "Giảm 10%"}
    m.update(k)
    return m


def _nd(*khoi):
    nd = copy.deepcopy(nw.MAC_DINH)
    nd["khoi"].extend(copy.deepcopy(list(khoi)))
    return nd


# ------------------------------------------------------------ chuan_hoa

@ca("v586: nhận đủ trường mới của ưu đãi, tuyển dụng, tiệc")
def _truong_moi():
    nd = _nd(
        _uu(don_toi_thieu="500000", gio_bat_dau="07:00", gio_ket_thuc="21:00", dieu_kien="Không cộng dồn\nMỗi khách một lần"),
        {"id": "td-1", "loai": "tuyen_dung", "vi_tri": "tuyen_dung", "hien": True, "tieu_de": "Thợ bánh",
         "email": "hr@vgb.vn", "yeu_cau": "Một năm kinh nghiệm", "hinh_thuc": "Toàn thời gian / Bán thời gian"},
        {"id": "tiec-1", "loai": "tiec", "vi_tri": "tiec", "hien": True, "tieu_de": "Trà chiều", "bat_dau": "2026-10-20",
         "gio_bat_dau": "15:00", "gio_ket_thuc": "17:30", "gia_ve": "350000", "so_ve": "40", "han_ban": "2026-10-18",
         "dia_diem": "Cửa hàng Sài Gòn", "yeu_cau": "5 món bánh"},
    )
    la("giữ nguyên", nw.chuan_hoa(nd), nd)


@ca("v586: chặn số có dấu chấm, giờ một ô, giờ ngược, hạn đăng ký sau ngày tiệc, số vé 0")
def _chan_sai():
    for m, chu in [
        (_uu(don_toi_thieu="500.000"), "chỉ gõ chữ số"),
        (_uu(gio_bat_dau="07:00"), "cả hai ô giờ"),
        (_uu(gio_bat_dau="21:00", gio_ket_thuc="07:00"), "sau giờ bắt đầu"),
        (_uu(gio_bat_dau="7h", gio_ket_thuc="21:00"), "07:00"),
        ({"id": "t", "loai": "tiec", "vi_tri": "tiec", "hien": True, "tieu_de": "T", "bat_dau": "2026-10-20", "han_ban": "2026-10-21"}, "Hạn đăng ký"),
        ({"id": "t", "loai": "tiec", "vi_tri": "tiec", "hien": True, "tieu_de": "T", "bat_dau": "2026-10-20", "so_ve": "0"}, "Số vé"),
        ({"id": "t", "loai": "tiec", "vi_tri": "tiec", "hien": True, "tieu_de": "T"}, "ngày diễn ra"),
        ({"id": "t", "loai": "tiec", "vi_tri": "tiec", "hien": True, "tieu_de": ""}, "cần có tên"),
    ]:
        dung("chặn: " + chu, bi_chan(_nd(m), chu))
    nd = _nd()
    nd["khoi"][-1]["vi_tri"] = "tiec"
    dung("khối thường không đặt vào khe Tiệc", bi_chan(nd))
    # Tiệc ẩn thì chưa cần ngày, để soạn dần.
    la("tiệc ẩn chưa có ngày vẫn lưu", bi_chan(_nd({"id": "t", "loai": "tiec", "vi_tri": "tiec", "hien": False, "tieu_de": "Nháp"})), False)


@ca("v586: trần khối nâng lên 80, vẫn chặn quá trần")
def _tran_khoi():
    nd = _nd(*[_uu(id="u%d" % i) for i in range(80 - len(nw.MAC_DINH["khoi"]))])
    la("đúng 80 khối", bi_chan(nd), False)
    nd["khoi"].append(_uu(id="u-thua"))
    dung("81 khối bị chặn", bi_chan(nd, "tối đa 80"))


@ca("v586: cửa hàng mặc định trùng hai điểm nhận bánh đang gõ cứng trong trang")
def _diem_nhan_goc():
    # Deploy xong khách phải thấy y nguyên điểm nhận, đúng thứ tự (giỏ hàng
    # lưu trong trình duyệt nhớ điểm nhận theo mã cửa hàng từ v586b).
    with io.open(os.path.join(GOC, "trang", "banh.html"), encoding="utf-8") as f:
        html = f.read()
    bep = re.search(r'const BEP = \{id:"([^"]+)", n:"([^"]+)", a:"([^"]+)"\}', html)
    ch = re.search(r'const PICKUPS_GOC = \[ BEP, \{id:"([^"]+)", n:"([^"]+)", a:"([^"]+)"\} \];', html)
    trong_trang = [bep.groups(), ch.groups()]
    nhan = [(c["id"], c["ten"], c["dia_chi"]) for c in nw.thong_tin_day_du({})["cua_hang"] if c["nhan_banh"]]
    la("hai điểm nhận, đúng thứ tự", nhan, trong_trang)
    la("bản mặc định qua được chuan_hoa", bi_chan(dict(_nd(), thong_tin=nw.thong_tin_day_du({}))), False)


@ca("v586: cửa hàng bật hiện hay nhận bánh phải có địa chỉ, link chỉ đường phải https")
def _cua_hang_sai():
    def thu(c, chu):
        nd = _nd(); nd["thong_tin"] = {"cua_hang": [dict({"id": "a", "ten": "A", "dia_chi": "1 Lê Lợi", "loai": "cua_hang", "hien": True, "nhan_banh": False}, **c)]}
        return bi_chan(nd, chu)
    dung("thiếu địa chỉ", thu({"dia_chi": ""}, "cần địa chỉ"))
    dung("link http", thu({"chi_duong": "http://maps.app.goo.gl/x"}, "https://"))
    dung("hotline chữ", thu({"hotline": "gọi tôi"}, "Hotline"))
    dung("trường lạ", thu({"gia": "1"}, "không được hỗ trợ"))
    la("hợp lệ", thu({"chi_duong": "https://maps.app.goo.gl/x", "hotline": "0909 123 456", "gio_mo_cua": "7:00 - 21:00"}, None), False)


@ca("v586: thẻ Liên hệ kiểm số điện thoại, email và link mạng xã hội")
def _lien_he():
    tot = {k: "" for k in nw.TRUONG_LIEN_HE}
    tot.update(dien_thoai=" 0931 224 334 ", email="hello@thevagabondpatisserie.com", instagram="https://instagram.com/x")
    la("gọt khoảng trắng", nw.kiem_lien_he(tot)["dien_thoai"], "0931 224 334")
    for k, v, chu in [("dien_thoai", "abc", "8 đến 12"), ("email", "khong-email", "Email"), ("tiktok", "javascript:alert(1)", "https://"),
                      ("zalo", "http://zalo.me/x", "https://")]:
        x = dict(tot, **{k: v})
        try:
            nw.kiem_lien_he(x)
            dung("phải chặn " + k, False)
        except ValueError as e:
            dung("câu báo " + k, chu in str(e))
    try:
        nw.kiem_lien_he(dict(tot, web_secret="x"))
        dung("phải chặn ô lạ", False)
    except ValueError:
        pass


# ------------------------------------------------------------ phép gộp

@ca("v586: thêm mục mới lên đầu nhóm cùng loại, sửa mục cũ tại chỗ")
def _ap_muc():
    nd = _nd(_uu(id="u1"), _uu(id="u2"))
    moi = nw.ap_muc(nd, _uu(id="u3", tieu_de="Mới"), "")
    ids = [k["id"] for k in moi["khoi"] if k["loai"] == "uu_dai"]
    la("mục mới đứng đầu ưu đãi", ids, ["u3", "u1", "u2"])
    sua = nw.ap_muc(moi, _uu(id="u2", tieu_de="Đã sửa", vi_tri="cuoi_trang"), nw.dau_van_tay(_uu(id="u2")))
    k2 = [k for k in sua["khoi"] if k["id"] == "u2"][0]
    la("sửa tại chỗ", k2["tieu_de"], "Đã sửa")
    la("vị trí luôn là loại của mục", k2["vi_tri"], "uu_dai")
    la("không đụng bản gốc", [k["id"] for k in nd["khoi"] if k["loai"] == "uu_dai"], ["u1", "u2"])


@ca("v586: người khác vừa sửa hay xoá đúng mục đó thì báo, không ghi đè")
def _xung_dot():
    nd = _nd(_uu(id="u1", tieu_de="Bản người kia vừa lưu"))
    dau_luc_mo = nw.dau_van_tay(_uu(id="u1"))
    for ham in (lambda: nw.ap_muc(nd, _uu(id="u1", tieu_de="Của tôi"), dau_luc_mo),
                lambda: nw.xoa_muc(nd, "u1", dau_luc_mo),
                lambda: nw.ap_muc(nd, _uu(id="u1"), "")):
        try:
            ham()
            dung("phải báo xung đột", False)
        except nw.XungDot:
            pass
    try:
        nw.ap_muc(_nd(), _uu(id="mat"), dau_luc_mo)
        dung("mục đã bị xoá phải báo", False)
    except nw.XungDot:
        pass
    la("không soát (bản nháp) thì ghi", nw.ap_muc(nd, _uu(id="u1", tieu_de="Của tôi"), None)["khoi"][-1]["tieu_de"], "Của tôi")


@ca("v586: không sửa xoá được khối thường hay đổi loại qua thẻ mới")
def _loai():
    nd = _nd(_uu(id="u1"))
    for ham, chu in [(lambda: nw.ap_muc(nd, {"id": "cau-chuyen", "loai": "cau_chuyen"}, ""), "Chỉ lưu"),
                     (lambda: nw.ap_muc(nd, {"id": "u1", "loai": "tiec", "tieu_de": "x"}, None), "loại khác"),
                     (lambda: nw.xoa_muc(nd, "cau-chuyen", None), "Nâng cao")]:
        try:
            ham()
            dung("phải chặn: " + chu, False)
        except ValueError as e:
            dung("câu báo: " + chu, chu in str(e))


@ca("v586: nhãn chữ đổi từng khoá, để trống là về mặc định, soát người khác vừa sửa")
def _ap_nhan():
    nd = _nd(); nd["nhan"] = {"tab_today": "Bánh vừa ra lò"}
    moi = nw.ap_nhan(nd, {"tab_order": ["", "Đặt trước"], "tab_today": ["Bánh vừa ra lò", ""]})
    la("thêm và bỏ", moi["nhan"], {"tab_order": "Đặt trước"})
    try:
        nw.ap_nhan(nd, {"tab_today": ["", "Của tôi"]})
        dung("phải báo xung đột", False)
    except nw.XungDot:
        pass
    try:
        nw.ap_nhan(nd, {"khoa_la": ["", "x"]})
        dung("phải chặn khoá lạ", False)
    except ValueError:
        pass


@ca("v586: trạng thái mục theo bảng mẫu dùng chung với JS")
def _trang_thai():
    sai = []
    for muc, ma, chu in MAU_TT["ca"]:
        if list(nw.trang_thai_muc(muc, MAU_TT["hom_nay"])) != [ma, chu]:
            sai.append(muc)
    la("không dòng nào lệch", sai, [])


# ------------------------------------------------------- hàm thật, site giả

class _Doc(object):
    def __init__(self, nhap, cong):
        self.ban_nhap = json.dumps(nhap, ensure_ascii=False)
        self.ban_cong_khai = json.dumps(cong, ensure_ascii=False)
        self.lich_su = "[]"
        self.phien_ban = 3
        self.flags = types.SimpleNamespace()
        self.luu = 0

    def save(self, **k):
        # Đúng như controller thật: chuẩn hoá cả hai bản, tăng phiên bản.
        self.ban_nhap = json.dumps(nw.chuan_hoa(self.ban_nhap), ensure_ascii=False)
        self.ban_cong_khai = json.dumps(nw.chuan_hoa(self.ban_cong_khai), ensure_ascii=False)
        self.phien_ban += 1
        self.luu += 1


class _Site(object):
    def __init__(self, nhap, cong, settings=None):
        self.doc = _Doc(nhap, cong)
        self.settings = dict(settings or {})
        self.sql = []
        self.ghi_settings = []
        self.hang = {}
        self.doc_gv = []
        # Giả REPEATABLE READ: đọc thường thấy ảnh chụp (self.doc), đọc có
        # for update thấy bản hiện tại (hien_tai, mặc định trùng ảnh chụp).
        self.hien_tai = None
        self.da_giu = {}

    def vao(self):
        fr = sys.modules["frappe"]
        site = self

        def _sql(q, *a, **k):
            site.sql.append(q)
            if "tabVagabond Noi Dung Web" in q and "for update" in q:
                if "ban_cong_khai" in q:
                    return [(site.hien_tai if site.hien_tai is not None else site.doc.ban_cong_khai,)]
                return [("order",)]
            if "sum(so_ve)" in q:
                return list(site.da_giu.items())
            return []

        def _gv(dt, ten, *a, **k):
            site.doc_gv.append((ten, bool(k.get("for_update")), len(site.sql)))
            if dt == "Vagabond Noi Dung Web" and a and a[0] == "ban_cong_khai":
                return site.doc.ban_cong_khai
            return site.hang.get(ten)

        db = types.SimpleNamespace(
            sql=_sql, exists=lambda *a, **k: True, get_value=_gv,
            savepoint=lambda *a: None, rollback=lambda *a, **k: None,
            set_single_value=lambda dt, k, v: (site.ghi_settings.append((k, v)), site.settings.__setitem__(k, v)),
        )
        return [
            um.patch.object(fr, "db", db),
            um.patch.object(fr, "get_doc", lambda *a, **k: site.doc),
            um.patch.object(fr, "get_roles", lambda *a: ["Marketing"], create=True),
            um.patch.object(fr, "clear_document_cache", lambda *a, **k: None, create=True),
            um.patch.object(fr.session, "user", "minhvu@vgb"),
            um.patch.object(fr.utils, "now", lambda: "2026-10-07 10:00:00", create=True),
            um.patch.object(fr.utils, "nowdate", lambda: "2026-10-07", create=True),
            um.patch("vagabond.lib.cfg_o", lambda k: site.settings.get(k)),
        ]


def _chay(site, ham):
    ps = site.vao()
    for p in ps:
        p.start()
    try:
        return ham()
    finally:
        for p in reversed(ps):
            p.stop()


@ca("v586: lưu một mục ghi cả bản khách thấy lẫn bản nháp, KHÔNG cuốn nháp chưa xuất bản")
def _khong_cuon_nhap():
    cong = _nd(_uu(id="u1", tieu_de="Cũ"))
    nhap = copy.deepcopy(cong)
    # Ai đó đang sửa dở câu chuyện ở Nâng cao, chưa xuất bản.
    nhap["khoi"][4]["tieu_de"] = "Nháp chưa xuất bản"
    site = _Site(nhap, cong)
    kq = _chay(site, lambda: nw.luu_muc(_uu(id="u1", tieu_de="Mới"), nw.dau_van_tay(cong["khoi"][-1])))
    c, n = json.loads(site.doc.ban_cong_khai), json.loads(site.doc.ban_nhap)
    la("khách thấy mục mới", [k["tieu_de"] for k in c["khoi"] if k["id"] == "u1"], ["Mới"])
    la("nháp cũng có mục mới", [k["tieu_de"] for k in n["khoi"] if k["id"] == "u1"], ["Mới"])
    la("câu chuyện công khai giữ nguyên", c["khoi"][4]["tieu_de"], cong["khoi"][4]["tieu_de"])
    la("câu chuyện nháp giữ phần đang sửa", n["khoi"][4]["tieu_de"], "Nháp chưa xuất bản")
    la("bản khách thấy trước đó vào lịch sử", json.loads(site.doc.lich_su)[0]["noi_dung"], cong)
    la("màn nhận lại bản mới", [k["tieu_de"] for k in kq["khoi"]], ["Mới"])
    la("báo nháp còn khác", kq["nhap_chua_xuat_ban"], 1)


@ca("v586: lưu đè lên bản người khác vừa lưu thì báo, không ghi gì")
def _khong_ghi_de():
    cong = _nd(_uu(id="u1", tieu_de="Người kia vừa sửa"))
    site = _Site(copy.deepcopy(cong), cong)
    try:
        _chay(site, lambda: nw.luu_muc(_uu(id="u1", tieu_de="Của tôi"), nw.dau_van_tay(_uu(id="u1", tieu_de="Cũ"))))
        dung("phải báo", False)
    except Exception as e:
        dung("câu báo", "vừa sửa" in str(e))
    la("không lưu", site.doc.luu, 0)


@ca("v586: xoá một mục khỏi cả hai bản, mục khác giữ nguyên")
def _xoa():
    cong = _nd(_uu(id="u1"), _uu(id="u2"))
    site = _Site(copy.deepcopy(cong), cong)
    _chay(site, lambda: nw.xoa_muc_web("u1", nw.dau_van_tay(_uu(id="u1"))))
    for ban in (site.doc.ban_cong_khai, site.doc.ban_nhap):
        la("còn u2", [k["id"] for k in json.loads(ban)["khoi"] if k["loai"] == "uu_dai"], ["u2"])


@ca("v586: thẻ Liên hệ ghi đúng bảy ô web_* của Settings, soát người khác vừa sửa")
def _luu_lien_he():
    cu = {"web_dien_thoai": "0931 224 334", "web_email": "", "web_zalo": "", "web_messenger": "https://m.me/a",
          "web_facebook": "", "web_instagram": "", "web_tiktok": ""}
    site = _Site(_nd(), _nd(), cu)
    dau = nw.dau_van_tay({k: cu[nw.O_LIEN_HE[k]] for k in nw.TRUONG_LIEN_HE})
    moi = {k: cu[nw.O_LIEN_HE[k]] for k in nw.TRUONG_LIEN_HE}
    moi.update(dien_thoai="0909 000 111", email="hello@thevagabondpatisserie.com")
    kq = _chay(site, lambda: nw.luu_lien_he(moi, dau))
    la("chỉ ghi bảy ô web_*", sorted(k for k, _ in site.ghi_settings), sorted(nw.O_LIEN_HE.values()))
    la("số mới", site.settings["web_dien_thoai"], "0909 000 111")
    la("màn đọc lại số mới", kq["lien_he"]["dien_thoai"], "0909 000 111")
    site.ghi_settings = []
    try:
        _chay(site, lambda: nw.luu_lien_he(moi, dau))
        dung("dấu cũ phải bị chặn", False)
    except Exception as e:
        dung("câu báo", "vừa sửa" in str(e))
    la("không ghi gì", site.ghi_settings, [])


# ------------------------------------------------------------ đăng ký tiệc

TIEC = {"id": "tiec-1", "loai": "tiec", "hien": True, "tieu_de": "Trà chiều", "bat_dau": "2026-10-20",
        "han_ban": "2026-10-18", "gia_ve": "350000", "so_ve": "40"}


@ca("v586: đăng ký tiệc kiểm tên, số, số vé còn, hạn đăng ký")
def _dk_thuan():
    ok = tw.chuan_hoa({"tiec_id": "tiec-1", "ten": " Lan ", "sdt": "+84 909 123 456", "so_ve": "2"}, TIEC, 30, "2026-10-07")
    la("bản sạch", (ok["ten"], ok["sdt"], ok["so_ve"], ok["tong_tien"], ok["ten_tiec"]), ("Lan", "0909123456", 2, 700000, "Trà chiều"))
    for du, tiec, da, ngay, chu in [
        ({"ten": "Lan", "sdt": "0909123456", "so_ve": "3"}, TIEC, 38, "2026-10-07", "chỉ còn 2 vé"),
        ({"ten": "Lan", "sdt": "0909123456", "so_ve": "1"}, TIEC, 40, "2026-10-07", "hết vé"),
        ({"ten": "Lan", "sdt": "0909123456", "so_ve": "1"}, TIEC, 0, "2026-10-19", "hết hạn đăng ký"),
        ({"ten": "Lan", "sdt": "0909123456", "so_ve": "1"}, TIEC, 0, "2026-10-21", "đã diễn ra"),
        ({"ten": "Lan", "sdt": "0909123456", "so_ve": "1"}, dict(TIEC, hien=False), 0, "2026-10-07", "không còn trên website"),
        ({"ten": "Lan", "sdt": "123", "so_ve": "1"}, TIEC, 0, "2026-10-07", "số điện thoại"),
        ({"ten": "Lan", "sdt": "0909123456", "so_ve": "11"}, TIEC, 0, "2026-10-07", "từ 1 đến 10"),
        ({"ten": "Lan", "sdt": "0909123456", "so_ve": "1.5"}, TIEC, 0, "2026-10-07", "từ 1 đến 10"),
    ]:
        try:
            tw.chuan_hoa(du, tiec, da, ngay)
            dung("phải chặn: " + chu, False)
        except ValueError as e:
            dung("câu báo: " + chu, chu in str(e))
    la("không giới hạn vé", tw.con_ve(dict(TIEC, so_ve=""), 999), None)
    tin = tw.soan_tin(dict(ok, url="https://x"))
    dung("tin có tạm tính", "Tạm tính: 700.000 đ" in tin and "ĐĂNG KÝ TIỆC MỚI" in tin)


@ca("v586: cửa đăng ký khoá hàng TRƯỚC khi đếm vé, gửi lại cùng mã không tạo đăng ký mới")
def _dk_ham_that():
    site = _Site(_nd(TIEC), _nd(TIEC))
    them = []
    hang = site.hang

    class _Phieu(dict):
        def __init__(self, d):
            super().__init__(d)
            self.flags = types.SimpleNamespace()
            self.name = d["name"]

        def insert(self, **k):
            them.append(dict(self))
            hang[self.name] = types.SimpleNamespace(name=self.name, bam_noi_dung=self["bam_noi_dung"])

    ps = site.vao()
    fr = sys.modules["frappe"]
    ps += [um.patch.object(fr, "get_doc", lambda d, *a, **k: _Phieu(d) if isinstance(d, dict) else site.doc),
           um.patch.object(fr, "generate_hash", lambda length=10: "h" * length, create=True),
           um.patch.object(fr.local, "message_log", [], create=True),
           ]  # GHI CHÚ (Codex #454): không thay _ban_cong_khai bằng hàm giả nữa, nó che
    # mất việc cấu hình tiệc được đọc bằng phép thường sau khoá.
    for p in ps:
        p.start()
    try:
        ma = "0f0e0d0c-0b0a-4908-8706-050403020100"
        du = {"tiec_id": "tiec-1", "ten": "Lan", "sdt": "0909123456", "so_ve": "2"}
        kq = tw.dang_ky.__wrapped__(json.dumps(du), ma) if hasattr(tw.dang_ky, "__wrapped__") else tw.dang_ky(json.dumps(du), ma)
        kq2 = tw.dang_ky.__wrapped__(json.dumps(du), ma) if hasattr(tw.dang_ky, "__wrapped__") else tw.dang_ky(json.dumps(du), ma)
    finally:
        for p in reversed(ps):
            p.stop()
    la("một đăng ký", len(them), 1)
    la("gửi lại trả cùng mã", kq["ma"], kq2["ma"])
    # GHI CHÚ (Codex #453 vòng 1): bản trước của ca này thay hẳn dem_ve bằng
    # hàm giả, nên không bao giờ thấy câu đếm vé là đọc thường. Giữ dem_ve
    # thật, soi đúng câu SQL nó chạy.
    i_khoa = next(i for i, q in enumerate(site.sql) if "tabVagabond Noi Dung Web" in q and "for update" in q)
    dem = [(i, q) for i, q in enumerate(site.sql) if "sum(so_ve)" in q]
    la("đếm vé một lần", len(dem), 1)
    dung("khoá hàng trước khi đếm vé", i_khoa < dem[0][0])
    dung("đếm vé sau khoá là đọc hiện tại (for update)", "for update" in dem[0][1])
    sau_khoa = [g for g in site.doc_gv if i_khoa < g[2] <= dem[0][0]]
    dung("đọc lại mã lần gửi sau khoá là đọc hiện tại", bool(sau_khoa) and all(g[1] for g in sau_khoa))
    la("trạng thái đầu", them[0]["trang_thai"], "Chờ xác nhận")


@ca("v586 (Codex #453): hai lần gửi CÙNG mã chen nhau, lần sau đâm khoá chính thì trả lại đăng ký trước")
def _dk_trung_dong_thoi():
    site = _Site(_nd(TIEC), _nd(TIEC))
    du = {"tiec_id": "tiec-1", "ten": "Lan", "sdt": "0909123456", "so_ve": "2"}
    dau = __import__("hashlib").sha256(json.dumps(du, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    ma = "0f0e0d0c-0b0a-4908-8706-050403020100"
    ten = __import__("hashlib").sha256(("tiec:" + ma).encode()).hexdigest()
    vet = []

    class _Trung(Exception):
        pass

    class _Phieu(dict):
        def __init__(self, d):
            super().__init__(d); self.flags = types.SimpleNamespace(); self.name = d["name"]

        def insert(self, **k):
            # Lần gửi kia đã ghi xong đúng lúc này: mọi lần đọc trước đều trống.
            fr.local.message_log.append("Duplicate Name")
            site.hang[ten] = types.SimpleNamespace(name=ten, bam_noi_dung=dau)
            raise _Trung()

    ps = site.vao()
    fr = sys.modules["frappe"]
    ps += [um.patch.object(fr, "get_doc", lambda d, *a, **k: _Phieu(d) if isinstance(d, dict) else site.doc),
           um.patch.object(fr, "DuplicateEntryError", _Trung, create=True),
           um.patch.object(fr, "generate_hash", lambda length=10: "h" * length, create=True),
           um.patch.object(fr.local, "message_log", ["truoc"], create=True),
           ]
    for p in ps:
        p.start()
    fr.db.savepoint = lambda m: vet.append(("moc", m))
    fr.db.rollback = lambda save_point=None: vet.append(("lui", save_point))
    try:
        kq = tw.dang_ky(json.dumps(du), ma)
        log = list(fr.local.message_log)
    finally:
        for p in reversed(ps):
            p.stop()
    la("trả lại đăng ký trước, không báo lỗi", kq, {"ok": 1, "ma": ten[:8].upper()})
    la("lùi đúng điểm lưu vừa đặt", [v[0] for v in vet], ["moc", "lui"])
    la("bỏ thông báo Duplicate Name của lần chèn hỏng", log, ["truoc"])
    dung("đọc lại sau lùi là đọc hiện tại", site.doc_gv[-1][1])


@ca("v586b (Codex #454): Marketing đổi tiệc trong lúc khách chờ khoá, cửa đăng ký đọc cấu hình HIỆN TẠI")
def _dk_cau_hinh_sau_khoa():
    du = {"tiec_id": "tiec-1", "ten": "Lan", "sdt": "0909123456", "so_ve": "3"}
    ma = "0f0e0d0c-0b0a-4908-8706-050403020100"
    fr = sys.modules["frappe"]
    for ten_ca, moi in (("giảm vé 40 xuống 20", dict(TIEC, so_ve="20")), ("vừa ẩn tiệc", dict(TIEC, hien=False))):
        # Ảnh chụp lúc khách bắt đầu: 40 vé. Marketing lưu xong lúc khách đang chờ khoá.
        site = _Site(_nd(TIEC), _nd(TIEC))
        site.hien_tai = json.dumps(_nd(moi), ensure_ascii=False)
        site.da_giu = {"tiec-1": 18}
        them = []

        class _Phieu(dict):
            def __init__(self, d):
                super().__init__(d); self.flags = types.SimpleNamespace(); self.name = d["name"]

            def insert(self, **k):
                them.append(dict(self))

        ps = site.vao()
        ps += [um.patch.object(fr, "get_doc", lambda d, *a, **k: _Phieu(d) if isinstance(d, dict) else site.doc),
               um.patch.object(fr, "generate_hash", lambda length=10: "h" * length, create=True),
               um.patch.object(fr.local, "message_log", [], create=True)]
        for p in ps:
            p.start()
        loi = ""
        try:
            tw.dang_ky(json.dumps(du), ma)
        except Exception as e:
            loi = str(e)
        finally:
            for p in reversed(ps):
                p.stop()
        la(ten_ca + ": không ghi đăng ký", len(them), 0)
        dung(ten_ca + ": có câu báo cho khách", bool(loi))


@ca("v586b (Codex #454): bảng Nâng cao nhận trần số khối từ máy chủ, không còn số chép tay trong bien-tap.js")
def _tran_khoi_mot_nguon():
    site = _Site(_nd(), _nd())
    site.doc.ban_nhap = site.doc.ban_cong_khai
    site.doc.modified_by, site.doc.modified = "x", "y"
    la("có bản ghi: mang trần", _chay(site, nw.doc_bang)["so_khoi_toi_da"], nw.SO_KHOI_TOI_DA)
    fr = sys.modules["frappe"]
    ps = site.vao() + [um.patch.object(fr.db, "exists", lambda *a, **k: False, create=True)]
    for p in ps:
        p.start()
    try:
        moi = nw.doc_bang()
    finally:
        for p in reversed(ps):
            p.stop()
    la("chưa có bản ghi: mang trần", moi["so_khoi_toi_da"], nw.SO_KHOI_TOI_DA)
    with io.open(os.path.join(GOC, "public", "web_order", "bien-tap.js"), encoding="utf-8") as f:
        js = f.read()
    # Dò chuỗi chỉ để chốt "không còn chỗ tự đặt trần"; hành vi đã có ca node.
    la("không còn so độ dài khối với số cứng", re.findall(r"khoi\.length\s*>=?\s*\d+", js), [])


@ca("v586: sales chỉ đổi trạng thái theo chiều tới, không sửa chữ khách gửi")
def _dk_phieu():
    class _P(dict):
        def __init__(self, d, cu=None, moi=False):
            super().__init__(d); self._cu = cu; self._moi = moi; self.flags = types.SimpleNamespace(dang_ky_web=moi)
            self.trang_thai = d.get("trang_thai")

        def is_new(self):
            return self._moi

        def get_doc_before_save(self):
            return self._cu
    cu = {"ten": "Lan", "sdt": "0909123456", "so_ve": 2, "trang_thai": "Chờ xác nhận"}
    cu_p = types.SimpleNamespace(get=cu.get, trang_thai="Chờ xác nhận")
    tw.kiem_phieu(_P(dict(cu, trang_thai="Đã xác nhận"), cu_p))
    for d, chu in [(dict(cu, so_ve=5), "Giữ nguyên"), (dict(cu, trang_thai="Lạ"), "trạng thái")]:
        try:
            tw.kiem_phieu(_P(d, cu_p))
            dung("phải chặn: " + chu, False)
        except Exception as e:
            dung("câu báo: " + chu, chu in str(e))
    cu_huy = types.SimpleNamespace(get=dict(cu, trang_thai="Đã hủy").get, trang_thai="Đã hủy")
    try:
        tw.kiem_phieu(_P(dict(cu, trang_thai="Đã xác nhận"), cu_huy))
        dung("không mở lại phiếu đã huỷ", False)
    except Exception as e:
        dung("câu báo ngược", "ngược" in str(e))
    try:
        tw.kiem_phieu(_P(dict(cu), None, moi=False) if False else types.SimpleNamespace(is_new=lambda: True, flags=types.SimpleNamespace(dang_ky_web=False)))
        dung("không tạo tay từ Desk", False)
    except Exception as e:
        dung("câu báo tạo tay", "trang đặt bánh" in str(e))


# ------------------------------------------------------ trang đặt bánh thật

def _trang(kich, kho=None):
    import subprocess
    r = subprocess.run(["node", os.path.join(GOC, "khung", "kiem_thu", "gia_lap_trang.js"), os.path.join(GOC, "trang", "banh.html"),
                        "2026-10-07T08:00:00+07:00", kich] + ([json.dumps(kho, ensure_ascii=False)] if kho else []),
                       capture_output=True, text=True, timeout=30)
    if r.returncode:
        raise AssertionError(r.stderr[:1500])
    return json.loads(r.stdout)


@ca("v586: điểm nhận bánh lấy từ thẻ Cửa hàng; tắt hết thì ẩn Tự đến lấy, KHÔNG về điểm cũ (Codex #453)")
def _diem_nhan_trang():
    d = _trang(r'''
const goc=PICKUPS.map(x=>x.n);
capNhatDiemNhan(undefined);
const chuaTai=PICKUPS.map(x=>x.n);
capNhatDiemNhan([{id:'a',n:'Bếp A',a:'1 Đường A'},{id:'b',n:'Quầy B',a:'2 Đường B'},{id:'c',n:'Quầy C',a:'3 Đường C'}]);
setMode('pick');setPickup(2);
const html=EL('#pickList').innerHTML, chon=CO.pickup, anTruoc=EL('#m-pick').hidden;
capNhatDiemNhan([]);
RA({goc,chuaTai,html,chon,anTruoc,ve:PICKUPS.map(x=>x.n),an:EL('#m-pick').hidden,mode:CO.mode});
''')
    la("trước khi tải nội dung: hai điểm cũ", d["goc"], ["Bếp Tân Sơn Hoà", "Cửa hàng Sài Gòn"])
    la("chưa có dữ liệu thì giữ nguyên", d["chuaTai"], ["Bếp Tân Sơn Hoà", "Cửa hàng Sài Gòn"])
    dung("bước Tự lấy có điểm mới", "Quầy C" in d["html"] and "3 Đường C" in d["html"])
    la("chọn được điểm thứ ba", d["chon"], 2)
    la("còn điểm thì nút Tự đến lấy hiện", d["anTruoc"], False)
    la("đã tải mà rỗng: không còn điểm nào", d["ve"], [])
    la("nút Tự đến lấy ẩn", d["an"], True)
    la("đang chọn tự lấy thì chuyển về giao tận nơi", d["mode"], "ship")


@ca("v586: luật điểm nhận một nguồn ở máy chủ, mặc định trùng hai điểm cũ của trang")
def _diem_nhan_thuan():
    la("mặc định", [x["n"] for x in nw.diem_nhan({})], ["Bếp Tân Sơn Hoà", "Cửa hàng Sài Gòn"])
    tat = copy.deepcopy(nw.THONG_TIN_MAC_DINH)
    for c in tat["cua_hang"]:
        c["nhan_banh"] = False
    la("tắt hết là rỗng", nw.diem_nhan({"thong_tin": tat}), [])
    la("xoá hết là rỗng", nw.diem_nhan({"thong_tin": {"cua_hang": []}}), [])
    thieu = {"thong_tin": {"cua_hang": [{"id": "a", "ten": "A", "dia_chi": " ", "nhan_banh": True}, {"id": "b", "ten": "B", "dia_chi": "2 Đường B", "nhan_banh": True}]}}
    la("thiếu địa chỉ thì không nhận", nw.diem_nhan(thieu), [{"id": "b", "n": "B", "a": "2 Đường B"}])
    la("mỗi điểm mang mã cửa hàng", [x["id"] for x in nw.diem_nhan({})], ["bep-tan-son-hoa", "cua-hang-sai-gon"])


@ca("v586b (Codex #453 vòng 2): điểm đã chọn giữ theo MÃ; điểm bị xoá thì bắt chọn lại, không tự chuyển")
def _diem_nhan_theo_ma():
    d = _trang(r'''
const BA=[{id:'a',n:'Quầy A',a:'1 A'},{id:'b',n:'Quầy B',a:'2 B'}];
capNhatDiemNhan(BA); setMode('pick'); setPickup(0);
const truoc=CO.pickupId;
capNhatDiemNhan([{id:'b',n:'Quầy B',a:'2 B'}]); setMode('pick');
const sauXoa={pickup:CO.pickup, id:CO.pickupId, mode:CO.mode, html:EL('#pickList').innerHTML};
capNhatDiemNhan([{id:'x',n:'Trùng tên',a:'1 Đường X'},{id:'y',n:'Trùng tên',a:'2 Đường Y'}]); setPickup(1);
const trung={id:CO.pickupId, dia:PICKUPS[CO.pickup].a};
capNhatDiemNhan([{id:'y',n:'Trùng tên',a:'2 Đường Y'},{id:'x',n:'Trùng tên',a:'1 Đường X'}]);
const doiCho={id:CO.pickupId, dia:PICKUPS[CO.pickup].a};
capNhatDiemNhan([{id:'z',n:'<img src=x onerror=alert(1)>',a:'<b>3</b>'}]); setMode('pick');
RA({truoc, sauXoa, trung, doiCho, html:EL('#pickList').innerHTML});
''')
    la("chọn điểm A", d["truoc"], "a")
    la("A bị xoá: không tự chọn điểm còn lại", (d["sauXoa"]["pickup"], d["sauXoa"]["id"]), (-1, ""))
    dung("không điểm nào đang bật", 'class="pick on"' not in d["sauXoa"]["html"])
    la("trùng tên: giữ đúng điểm đã chọn theo mã", d["trung"], {"id": "y", "dia": "2 Đường Y"})
    la("đổi thứ tự danh sách vẫn đúng điểm", d["doiCho"], {"id": "y", "dia": "2 Đường Y"})
    dung("tên marketing nhập được thoát HTML", "<img" not in d["html"] and "&lt;img" in d["html"])


@ca("v586b (Codex #453 vòng 2): tải lại trang, giỏ nhớ điểm nhận theo MÃ; giỏ cũ chỉ có số thứ tự thì bắt chọn lại")
def _diem_nhan_tai_lai():
    luc = 1791334740000  # 07/10/2026 07:59 giờ VN, một phút trước đồng hồ giả
    gio = {"luc": luc, "gio": [{"id": "BAWC00139", "qty": 1, "cm": 0}], "co": {"mode": "pick", "pickupId": "cua-hang-sai-gon"}}
    kich = r'''
const sauTai={id:CO.pickupId, chon:(PICKUPS[CO.pickup]||{}).id, mode:CO.mode};
capNhatDiemNhan([{id:'cua-hang-sai-gon',n:'Cửa hàng Sài Gòn',a:'9 Trần Cao Vân'}]);
RA({sauTai, sauDoi:{id:CO.pickupId, chon:(PICKUPS[CO.pickup]||{}).id}});
'''
    d = _trang(kich, {"vgb-gio-v1": json.dumps(gio)})
    la("tải lại: đúng điểm đã chọn theo mã", d["sauTai"], {"id": "cua-hang-sai-gon", "chon": "cua-hang-sai-gon", "mode": "pick"})
    la("danh sách đổi thứ tự: vẫn đúng điểm", d["sauDoi"], {"id": "cua-hang-sai-gon", "chon": "cua-hang-sai-gon"})
    cu = dict(gio, co={"mode": "pick", "pickup": 1})
    d = _trang("RA({id:CO.pickupId, pickup:CO.pickup});", {"vgb-gio-v1": json.dumps(cu)})
    la("giỏ cũ chỉ có số thứ tự: không đoán, bắt chọn lại", d, {"id": "", "pickup": -1})


@ca("v586 (Codex #453): trang khách nhận điểm nhận do máy chủ tính, không tự lọc lại danh sách cửa hàng")
def _cua_hang_dung_diem_may_chu():
    import subprocess
    js = r'''
const fs=require('fs'),vm=require('vm');const nhan=[];
const g={console,setTimeout,CustomEvent:function(){},location:{search:'',hash:'',origin:'x'}};
g.window=g;g.parent=g;g.self=g;
g.document={querySelectorAll:()=>[],getElementById:()=>null,dispatchEvent(){},createElement:()=>({})};
g.capNhatDiemNhan=ds=>nhan.push(ds);g.VgbKhoi={ve(){}};
const ND=JSON.parse(process.argv[2]);
g.fetch=async()=>({ok:true,json:async()=>({message:ND})});
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),g);
setTimeout(()=>console.log(JSON.stringify(nhan)),50);
'''
    tep = os.path.join(GOC, "public", "web_order", "cua-hang.js")
    def chay(nd):
        r = subprocess.run(["node", "-e", js, tep, json.dumps(nd, ensure_ascii=False)], capture_output=True, text=True, timeout=30)
        if r.returncode:
            raise AssertionError(r.stderr[:800])
        return json.loads(r.stdout)
    ch = [{"ten": "Quầy cũ", "dia_chi": "1 A", "nhan_banh": True}]
    la("đúng danh sách máy chủ gửi", chay({"khoi": [], "thong_tin": {"cua_hang": ch}, "diem_nhan": [{"n": "Quầy mới", "a": "2 B"}], "lien_he": {}}),
       [[{"n": "Quầy mới", "a": "2 B"}]])
    la("máy chủ nói rỗng thì rỗng, dù cửa hàng còn bật", chay({"khoi": [], "thong_tin": {"cua_hang": ch}, "diem_nhan": [], "lien_he": {}}), [[]])
    la("máy chủ cũ chưa gửi điểm nhận thì không đụng tới", chay({"khoi": [], "thong_tin": {"cua_hang": ch}, "lien_he": {}}), [])


@ca("v586 (Codex #453): đổi Messenger ở thẻ Liên hệ thì MỌI chỗ trên trang theo, kể cả câu báo đơn lỗi")
def _messenger_mot_nguon():
    d = _trang(r'''
const truoc=linkMessenger();
vgbApLienHe({messenger:'https://m.me/tai-khoan-moi'});
const sau=linkMessenger();
vgbApLienHe({messenger:''});
RA({truoc,sau,trong:linkMessenger()});
''')
    dung("chưa tải: link mặc định", "https://m.me/thevagabond.saigon" in d["truoc"])
    dung("câu báo đơn lỗi trỏ link mới", "https://m.me/tai-khoan-moi" in d["sau"] and "thevagabond.saigon" not in d["sau"])
    dung("để trống thì chỉ còn chữ, không link cũ", "href" not in d["trong"] and "Messenger" in d["trong"])
    # DOM giả của node không dựng thẻ a đầy đủ, nên phần "mọi thẻ a theo" kiểm
    # bằng trình duyệt thật (ảnh và số đo trên PR #453). Ở đây chỉ chốt điều
    # không chạy được: không còn thẻ a mạng xã hội nào thiếu dấu một nguồn, và
    # CONFIG.messenger chỉ còn được đọc trong linkMessenger.
    trang = io.open(os.path.join(GOC, "trang", "banh.html"), encoding="utf-8").read()
    the_a = re.findall(r"<a\b[^>]*href=\"https://(?:m\.me|instagram\.com|www\.tiktok\.com)/[^>]*>", trang)
    la("thẻ a mạng xã hội thiếu data-vgb-mxh", [a for a in the_a if "data-vgb-mxh" not in a], [])
    la("chỗ đọc CONFIG.messenger", len(re.findall(r"CONFIG\.messenger", trang)), 2)


@ca("v586: đổi số ở thẻ Liên hệ thì mọi câu có số cũ đổi theo, kể cả câu marketing đã sửa")
def _so_goi():
    d = _trang(r'''
window.vgbDienThoai='0909 000 111';
window.vgbNhan={dat_banh_04267831d:'Còn {gia_tri_a} bánh, cần thêm gọi 0931 224 334 nhé'};
RA({mac_dinh:chuWeb('x_khong_co','Gọi 0931 224 334 để được hỗ trợ'), da_sua:chuWeb('dat_banh_04267831d','', {gia_tri_a:2})});
''')
    la("câu mặc định", d["mac_dinh"], "Gọi 0909 000 111 để được hỗ trợ")
    la("câu đã sửa", d["da_sua"], "Còn 2 bánh, cần thêm gọi 0909 000 111 nhé")
