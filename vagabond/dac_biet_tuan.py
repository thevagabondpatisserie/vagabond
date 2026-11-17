"""v667: tab "Đặc biệt tuần này" trên trang /banh (anh Việt duyệt 17/11/2026).

Một "Đợt cuối tuần" là một mục loại `dac_biet_tuan` trong nội dung web, Marketing
tự nhập ở trình biên tập (thẻ Cuối tuần): chữ đầu tab, các mốc lịch, ô đếm ngược,
giờ mở và chốt đơn, các ngày giao, và 1 đến vài món (khoá bánh của thẻ Bánh).
Giá, size, tồn vẫn lấy từ danh mục đặt bánh như mọi bánh khác; đợt chỉ thêm
LUẬT ĐẶT:

  - chưa tới giờ mở đơn hay đã qua giờ chốt đơn: không nhận món của đợt;
  - đơn có món của đợt chỉ nhận vào các ngày giao của đợt;
  - món có số lượng tối đa: cộng mọi đơn web còn hiệu lực có món đó, tạo từ
    lúc mở đơn, không vượt quá (kiểm lại dưới khoá ngay trước lúc ghi đơn).

Mọi giờ là giờ Việt Nam, chuỗi "YYYY-MM-DDTHH:MM" so sánh theo thứ tự chữ.
Phép THUẦN ở trên, phần chạm Frappe ở dưới. Chỉ áp cho đơn mới.
"""

import json
import re
import unicodedata
from datetime import date, datetime
from urllib.parse import urlsplit

LOAI = "dac_biet_tuan"
# Trường danh sách của đợt (mọi trường khác của khối là chuỗi).
TRUONG_DS = {"moc", "ngay_giao", "mon_dt"}
TRUONG_CHU = {"mo_don", "chot_don", "dem_nguoc", "dem_chu_1", "dem_chu_2"}
MOC_TOI_THIEU, MOC_TOI_DA = 2, 5
MON_TOI_DA = 6
NGAY_GIAO_TOI_DA = 7
TOI_DA_SL = 9999
RE_LUC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}")

# Lý do từ chối đơn (trùng du-lieu.js LY_DO ở trang khách).
CHUA_MO = "dac_biet_chua_mo"
DA_CHOT = "dac_biet_da_chot"
SAI_NGAY = "dac_biet_sai_ngay"
HET_SUAT = "dac_biet_het_suat"


# ------------------------------------------------------------------ THUẦN

def chuan_luc(v, ten):
    """Chuỗi ngày giờ "YYYY-MM-DDTHH:MM" hợp lệ (bỏ giây nếu có). THUẦN."""
    s = str(v or "").strip().replace(" ", "T")[:16]
    if not RE_LUC.fullmatch(s):
        raise ValueError("Chọn %s (ngày và giờ)." % ten)
    try:
        datetime.strptime(s, "%Y-%m-%dT%H:%M")
    except ValueError:
        raise ValueError("%s không phải ngày giờ có thật." % ten.capitalize())
    return s


def _anh_hop_le(v):
    if not v:
        return True
    if any(ord(c) < 33 for c in v) or "\\" in v:
        return False
    u = urlsplit(v)
    noi_bo = v.startswith("/") and not v.startswith("//")
    if not (noi_bo or (u.scheme == "https" and u.hostname and not u.username and not u.password)):
        return False
    return not (v.startswith("/private/") or v.lower().split("?")[0].endswith(".svg"))


def _so_toi_da(v):
    s = str(v if v is not None else "").strip().replace(".", "")
    if s == "":
        return ""
    if not re.fullmatch(r"[0-9]{1,4}", s) or not 1 <= int(s) <= TOI_DA_SL:
        raise ValueError("Số lượng tối đa của món chỉ gõ chữ số, từ 1 tới %d. Để trống là không giới hạn." % TOI_DA_SL)
    return str(int(s))


def chuan_dot(k):
    """Kiểm và chuẩn hoá một đợt cuối tuần. THUẦN. Trả bản sạch, lỗi là ValueError
    với câu nói việc cần sửa (trình biên tập hiện nguyên câu)."""
    k = dict(k)
    k["mo_don"] = chuan_luc(k.get("mo_don"), "giờ mở đơn")
    k["chot_don"] = chuan_luc(k.get("chot_don"), "giờ chốt đơn")
    if k["mo_don"] >= k["chot_don"]:
        raise ValueError("Giờ chốt đơn phải sau giờ mở đơn.")
    moc = k.get("moc")
    if not isinstance(moc, list) or not MOC_TOI_THIEU <= len(moc) <= MOC_TOI_DA:
        raise ValueError("Bảng mốc lịch cần từ %d đến %d mốc." % (MOC_TOI_THIEU, MOC_TOI_DA))
    sach = []
    for i, x in enumerate(moc):
        if not isinstance(x, dict) or set(x) - {"nhan", "chu_ngay", "luc"}:
            raise ValueError("Mốc lịch không hợp lệ. Tải lại trang biên tập.")
        nhan = str(x.get("nhan") or "").strip()
        chu = str(x.get("chu_ngay") or "").strip()
        if not nhan or len(nhan) > 30 or len(chu) > 30:
            raise ValueError("Mốc %d cần nhãn (tối đa 30 ký tự), chữ ngày tối đa 30 ký tự." % (i + 1))
        luc = chuan_luc(x.get("luc"), "ngày giờ bắt đầu của mốc %d" % (i + 1))
        if sach and luc < sach[-1]["luc"]:
            raise ValueError("Các mốc lịch phải xếp theo thời gian, mốc sau không trước mốc trước.")
        sach.append({"nhan": nhan, "chu_ngay": chu, "luc": luc})
    k["moc"] = sach
    ng = k.get("ngay_giao")
    if not isinstance(ng, list) or not 1 <= len(ng) <= NGAY_GIAO_TOI_DA:
        raise ValueError("Chọn từ 1 đến %d ngày giao, nhận." % NGAY_GIAO_TOI_DA)
    ds = []
    for v in ng:
        s = str(v or "").strip()[:10]
        try:
            date.fromisoformat(s)
        except ValueError:
            raise ValueError("Ngày giao không hợp lệ.")
        if s < k["mo_don"][:10]:
            raise ValueError("Ngày giao %s đang trước ngày mở đơn." % s)
        if s not in ds:
            ds.append(s)
    k["ngay_giao"] = sorted(ds)
    mon = k.get("mon_dt")
    if not isinstance(mon, list) or not 1 <= len(mon) <= MON_TOI_DA:
        raise ValueError("Đợt cần từ 1 đến %d món." % MON_TOI_DA)
    sach, khoa_da = [], set()
    for x in mon:
        if not isinstance(x, dict) or set(x) - {"khoa", "mo_ta", "anh", "nhan_goc", "toi_da"}:
            raise ValueError("Món của đợt không hợp lệ. Tải lại trang biên tập.")
        # Cùng khoá bánh của thẻ Bánh (banh_web.khoa_banh; không import vì tệp đó chạm Frappe).
        khoa = " ".join(unicodedata.normalize("NFC", str(x.get("khoa") or "")).lower().split())[:140]
        if not khoa:
            raise ValueError("Chọn bánh cho từng món của đợt.")
        if khoa in khoa_da:
            raise ValueError("Một bánh đang được chọn hai lần trong đợt.")
        khoa_da.add(khoa)
        mo_ta = str(x.get("mo_ta") or "").strip()
        nhan_goc = str(x.get("nhan_goc") or "").strip()
        anh = str(x.get("anh") or "").strip()
        if len(mo_ta) > 200 or len(nhan_goc) > 30:
            raise ValueError("Mô tả món tối đa 200 ký tự, nhãn góc tối đa 30 ký tự.")
        if not _anh_hop_le(anh):
            raise ValueError("Chọn ảnh công khai PNG, JPG hoặc WebP cho món.")
        sach.append({"khoa": khoa, "mo_ta": mo_ta, "anh": anh, "nhan_goc": nhan_goc, "toi_da": _so_toi_da(x.get("toi_da"))})
    k["mon_dt"] = sach
    dn = str(k.get("dem_nguoc") or "").strip()
    if dn not in ("", "1"):
        raise ValueError("Ô đếm ngược chỉ bật hoặc tắt.")
    k["dem_nguoc"] = dn
    for ten in ("dem_chu_1", "dem_chu_2"):
        if len(str(k.get(ten) or "")) > 80:
            raise ValueError("Dòng chữ của ô đếm ngược tối đa 80 ký tự.")
    if len(str(k.get("nhan") or "")) > 30:
        raise ValueError("Nhãn bên phải tối đa 30 ký tự.")
    dong = [d for d in str(k.get("tieu_de") or "").split("\n") if d.strip()]
    if not 1 <= len(dong) <= 2:
        raise ValueError("Tiêu đề đợt có 1 hoặc 2 dòng.")
    return k


def trang_thai(k, luc):
    """THUẦN. luc: "YYYY-MM-DDTHH:MM" giờ Việt Nam. Trả chua_mo, mo hoặc da_chot."""
    if luc < (k.get("mo_don") or ""):
        return "chua_mo"
    if luc >= (k.get("chot_don") or ""):
        return "da_chot"
    return "mo"


def dot_dang_hien(khoi, hom_nay):
    """THUẦN. Đợt khách đang thấy: mục đầu tiên đang bật và trong khoảng ngày
    hiện (bat_dau, ket_thuc). Cùng luật khachThay của trang khách."""
    for k in khoi or []:
        if k.get("loai") != LOAI or k.get("hien") is not True:
            continue
        bd, kt = k.get("bat_dau") or "", k.get("ket_thuc") or ""
        if (bd and bd > hom_nay) or (kt and kt < hom_nay):
            continue
        return k
    return None


def dong_cua_dot(hang, ma_theo_khoa):
    """THUẦN. hang: [{"ma", "sl"}]; ma_theo_khoa: {khoa: set(mã size)}. Trả
    {khoa: số lượng} của các dòng thuộc món của đợt."""
    ra = {}
    for h in hang or []:
        for khoa, ds in (ma_theo_khoa or {}).items():
            if h.get("ma") in ds:
                ra[khoa] = ra.get(khoa, 0) + int(h.get("sl") or 0)
    return ra


def dem_da_dat(snapshots, ma_theo_khoa):
    """THUẦN. Cộng số lượng từng món của đợt trên các ảnh chụp đơn (chuỗi JSON
    hay dict, mục "mon": [{"ma", "sl"}]). Ảnh chụp hỏng thì bỏ qua."""
    ra = {}
    for s in snapshots or []:
        try:
            d = json.loads(s) if isinstance(s, str) else (s or {})
        except ValueError:
            continue
        for khoa, sl in dong_cua_dot(d.get("mon") or [], ma_theo_khoa).items():
            ra[khoa] = ra.get(khoa, 0) + sl
    return ra


def kiem_don(dot, hang, ma_theo_khoa, ngay_nhan, luc):
    """THUẦN. Lý do từ chối (chuỗi) hoặc None. Không có món của đợt thì None.
    ngay_nhan: "YYYY-MM-DD..." khách chọn; luc: giờ Việt Nam lúc nhận đơn."""
    if not dot:
        return None
    if not dong_cua_dot(hang, ma_theo_khoa):
        return None
    tt = trang_thai(dot, luc)
    if tt == "chua_mo":
        return CHUA_MO
    if tt == "da_chot":
        return DA_CHOT
    if str(ngay_nhan or "")[:10] not in (dot.get("ngay_giao") or []):
        return SAI_NGAY
    return None


def dot_de_xet(dot_dau, dot_moi):
    """THUẦN. Đợt dùng để xét lại dưới khoá đợt. Đọc lại vẫn đúng đợt khách đã
    đặt thì dùng bản mới (Marketing vừa sửa giờ chốt, ngày giao, số tối đa).
    Đợt vừa bị tắt, hết ngày hiện hay bị thay bằng đợt khác thì giữ bản đầu,
    để món của đợt không lọt qua như bánh thường sau giờ chốt."""
    if dot_moi and dot_dau and dot_moi.get("id") == dot_dau.get("id"):
        return dot_moi
    return dot_dau


def vuot_suat(dot, hang, ma_theo_khoa, da_dat):
    """THUẦN. Món vượt số lượng tối đa nếu nhận thêm đơn này: [{khoa, con}]."""
    them = dong_cua_dot(hang, ma_theo_khoa)
    ra = []
    for m in (dot or {}).get("mon_dt") or []:
        td = m.get("toi_da")
        if not td or m["khoa"] not in them:
            continue
        con = int(td) - int((da_dat or {}).get(m["khoa"], 0))
        if them[m["khoa"]] > con:
            ra.append({"khoa": m["khoa"], "con": max(con, 0)})
    return ra


# ------------------------------------------------------------------ Frappe

def luc_vn():
    """Giờ Việt Nam hiện tại "YYYY-MM-DDTHH:MM" (site đặt múi giờ Việt Nam)."""
    from frappe.utils import now_datetime

    return now_datetime().strftime("%Y-%m-%dT%H:%M")


def ma_theo_khoa(dot):
    """{khoa: set(mã size)} của các món trong đợt, đọc thẻ Bánh (Vagabond Banh Web)."""
    import frappe

    from vagabond.banh_web import DT, tach_dong

    khoa = [m["khoa"] for m in (dot or {}).get("mon_dt") or []]
    if not khoa:
        return {}
    ds = frappe.get_all(DT, filters={"khoa": ["in", khoa]}, fields=["khoa", "ma_hang"],
        limit_page_length=0, ignore_permissions=True)
    return {x.khoa: set(tach_dong(x.ma_hang)) for x in ds}


def dot_cong_khai():
    """Đợt khách đang thấy trên bản công khai, hoặc None."""
    from vagabond import noi_dung_web

    return dot_dang_hien((noi_dung_web._ban_cong_khai() or {}).get("khoi"), luc_vn()[:10])


def da_dat(dot, ma_khoa):
    """Số đã đặt từng món của đợt: mọi đơn web còn hiệu lực tạo từ lúc mở đơn.
    Đọc ĐỦ (không giới hạn số dòng): đây là số dùng để chặn bán quá suất."""
    import frappe

    from vagabond import don_web

    if not dot or not any(m.get("toi_da") for m in dot.get("mon_dt") or []):
        return {}
    tu = dot["mo_don"].replace("T", " ") + ":00"
    ds = frappe.get_all(don_web.DOCTYPE, filters={"creation": [">=", tu],
        "trang_thai": ["in", list(don_web.TRANG_THAI_CON_HIEU_LUC)]},
        fields=["snapshot"], limit_page_length=0, ignore_permissions=True)
    return dem_da_dat([x.snapshot for x in ds], ma_khoa)


def khoa_suat(dot):
    """Khoá tệp theo đợt: hai đơn cùng lấy suất cuối thì một đơn phải chờ."""
    from vagabond.don_web import filelock

    return filelock("vgb_dac_biet_" + str((dot or {}).get("id") or "")[:40], timeout=20)
