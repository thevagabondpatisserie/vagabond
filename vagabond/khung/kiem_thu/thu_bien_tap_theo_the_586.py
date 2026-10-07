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
    # lưu trong trình duyệt nhớ điểm nhận theo số thứ tự).
    with io.open(os.path.join(GOC, "trang", "banh.html"), encoding="utf-8") as f:
        html = f.read()
    bep = re.search(r'const BEP = \{n:"([^"]+)", a:"([^"]+)"\}', html)
    ch = re.search(r'const PICKUPS_GOC = \[ BEP, \{n:"([^"]+)", a:"([^"]+)"\} \];', html)
    trong_trang = [(bep.group(1), bep.group(2)), (ch.group(1), ch.group(2))]
    nhan = [(c["ten"], c["dia_chi"]) for c in nw.thong_tin_day_du({})["cua_hang"] if c["nhan_banh"]]
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

    def vao(self):
        fr = sys.modules["frappe"]
        site = self

        def _sql(q, *a, **k):
            site.sql.append(q)
            if "tabVagabond Noi Dung Web" in q and "for update" in q:
                return [("order",)]
            if "tabVagabond Dang Ky Tiec" in q:
                return []
            return []

        db = types.SimpleNamespace(
            sql=_sql, exists=lambda *a, **k: True,
            get_value=lambda dt, ten, *a, **k: site.hang.get(ten),
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
           um.patch.object(tw, "dem_ve", lambda ids: (site.sql.append("DEM"), {})[1]),
           um.patch.object(nw, "_ban_cong_khai", lambda: json.loads(site.doc.ban_cong_khai))]
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
    i_khoa = next(i for i, q in enumerate(site.sql) if "for update" in q)
    dung("khoá hàng trước khi đếm vé", i_khoa < site.sql.index("DEM"))
    la("trạng thái đầu", them[0]["trang_thai"], "Chờ xác nhận")


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

def _trang(kich):
    import subprocess
    r = subprocess.run(["node", os.path.join(GOC, "khung", "kiem_thu", "gia_lap_trang.js"), os.path.join(GOC, "trang", "banh.html"),
                        "2026-10-07T08:00:00+07:00", kich], capture_output=True, text=True, timeout=30)
    if r.returncode:
        raise AssertionError(r.stderr[:1500])
    return json.loads(r.stdout)


@ca("v586: điểm nhận bánh lấy từ thẻ Cửa hàng, hiện ở bước Tự lấy, xoá hết thì về hai điểm cũ")
def _diem_nhan_trang():
    d = _trang(r'''
const goc=PICKUPS.map(x=>x.n);
capNhatDiemNhan([{n:'Bếp A',a:'1 Đường A'},{n:'Quầy B',a:'2 Đường B'},{n:'Quầy C',a:'3 Đường C'}]);
CO.mode='pick';setPickup(2);
const html=EL('#pickList').innerHTML, chon=CO.pickup;
capNhatDiemNhan([]);
RA({goc,html,chon,ve:PICKUPS.map(x=>x.n),sau:CO.pickup});
''')
    la("trước khi tải nội dung: hai điểm cũ", d["goc"], ["Bếp Tân Sơn Hoà", "Cửa hàng Sài Gòn"])
    dung("bước Tự lấy có điểm mới", "Quầy C" in d["html"] and "3 Đường C" in d["html"])
    la("chọn được điểm thứ ba", d["chon"], 2)
    la("danh sách trống thì về hai điểm cũ", d["ve"], ["Bếp Tân Sơn Hoà", "Cửa hàng Sài Gòn"])
    la("điểm đang chọn không còn thì về điểm đầu", d["sau"], 0)


@ca("v586: đổi số ở thẻ Liên hệ thì mọi câu có số cũ đổi theo, kể cả câu marketing đã sửa")
def _so_goi():
    d = _trang(r'''
window.vgbDienThoai='0909 000 111';
window.vgbNhan={dat_banh_04267831d:'Còn {gia_tri_a} bánh, cần thêm gọi 0931 224 334 nhé'};
RA({mac_dinh:chuWeb('x_khong_co','Gọi 0931 224 334 để được hỗ trợ'), da_sua:chuWeb('dat_banh_04267831d','', {gia_tri_a:2})});
''')
    la("câu mặc định", d["mac_dinh"], "Gọi 0909 000 111 để được hỗ trợ")
    la("câu đã sửa", d["da_sua"], "Còn 2 bánh, cần thêm gọi 0909 000 111 nhé")
