"""Khách đăng ký tiệc trên trang đặt bánh (v586).

Minh Vũ vẽ thẻ "Tiệc" cho trình biên tập: tạo tiệc, đặt giá vé, số vé, hạn
bán. Anh Việt chốt 07/10/2026 làm tới mức GIỚI THIỆU VÀ ĐĂNG KÝ: khách gửi
tên, số điện thoại, số vé; sales gọi xác nhận và thu tiền như đơn đặt bàn.
Chưa thu tiền online, nên gửi đăng ký KHÔNG phải là đã có vé.

Vé còn = số vé của tiệc trừ tổng vé các đăng ký chưa huỷ. Đếm và ghi trong
cùng một khoá hàng để hai khách bấm cùng lúc không vượt số vé.
"""
# phần thuần
import hashlib
import json
import re
from datetime import datetime

TRANG_THAI = ("Chờ xác nhận", "Đã xác nhận", "Đã thanh toán", "Đã hủy")
VE_MOT_LAN_TOI_DA = 10
# v658 Vé sự kiện (anh Việt chọn A 14/11/2026): mục Tiệc nâng thành Vé sự kiện,
# vẫn là đăng ký giữ chỗ, Sales gọi xác nhận và thu tiền. Thêm mã vé, danh sách
# khách từng sự kiện và nút "Đã vào cửa" trên app cho Quầy, Sales, Marketing.
# Danh sách vai này trùng tuyệt đối QUYEN_SK trong bep/74-khach-su-kien.js
# (ca thu_ve_su_kien_658 chốt).
QUYEN_SK = ("Sales User", "Sales Manager", "System Manager", "VGB - Quản lý cửa hàng", "Marketing", "Giám đốc")


def ma_ve(ten):
    """Mã vé khách đọc ở cửa: 8 ký tự đầu của tên phiếu, chữ hoa. THUẦN.
    Một nguồn cho lúc đăng ký (trả về web) và màn danh sách khách; phiếu tạo
    trước v658 chưa có ô ma_ve vẫn ra đúng mã khách đã được báo."""
    return str(ten or "")[:8].upper()


def dong_khach(r):
    """Một dòng danh sách khách của sự kiện. THUẦN."""
    huy = r.get("trang_thai") == "Đã hủy"
    return {"name": r.get("name"), "ma_ve": r.get("ma_ve") or ma_ve(r.get("name")), "ten": r.get("ten") or "",
            "sdt": r.get("sdt") or "", "so_ve": int(r.get("so_ve") or 0), "trang_thai": r.get("trang_thai") or "",
            "da_vao": bool(int(r.get("da_vao_cua") or 0)) and not huy, "vao_luc": str(r.get("vao_cua_luc") or "")[:16],
            "ghi_chu": r.get("ghi_chu") or ""}


def tong_khach(ds):
    """Đếm của một sự kiện: số đăng ký và số vé chưa huỷ, số vé đã vào cửa. THUẦN."""
    con = [d for d in ds if d["trang_thai"] != "Đã hủy"]
    return {"so_dk": len(con), "so_ve": sum(d["so_ve"] for d in con),
            "da_vao": sum(d["so_ve"] for d in con if d["da_vao"])}


def ly_do_vao_cua(trang_thai, da_vao, muon):
    """Đổi dấu "Đã vào cửa" có hợp lệ không. THUẦN. Trả "" là được, "giu" là đã
    đúng trạng thái (bấm hai lần không đổi gì), còn lại là câu báo."""
    if trang_thai == "Đã hủy":
        return "Vé đã huỷ, không đánh dấu vào cửa được."
    if bool(da_vao) == bool(muon):
        return "giu"
    return ""


def con_ve(tiec, da_dang_ky):
    """Số vé còn nhận, None là không giới hạn. THUẦN."""
    so = str((tiec or {}).get("so_ve") or "")
    if not so:
        return None
    return max(0, int(so) - int(da_dang_ky or 0))


def ly_do_dong(tiec, hom_nay):
    """Câu nói vì sao tiệc không nhận đăng ký, "" là đang nhận. THUẦN."""
    if not tiec or tiec.get("loai") != "tiec" or not tiec.get("hien"):
        return "Tiệc này không còn trên website. Tải lại trang để xem tiệc đang mở."
    ngay = tiec.get("bat_dau") or ""
    han = tiec.get("han_ban") or ngay
    if ngay and ngay < hom_nay:
        return "Tiệc đã diễn ra."
    if han and han < hom_nay:
        return "Tiệc đã hết hạn đăng ký."
    return ""


def chuan_hoa(du_lieu, tiec, da_dang_ky, hom_nay):
    """Kiểm một lượt đăng ký của khách. THUẦN. Trả bản sạch để lưu."""
    if isinstance(du_lieu, str):
        if len(du_lieu) > 3000:
            raise ValueError("Đăng ký quá dài. Rút ngắn ghi chú rồi gửi lại.")
        du_lieu = json.loads(du_lieu)
    if not isinstance(du_lieu, dict):
        raise ValueError("Kiểm tra lại thông tin đăng ký.")
    dong = ly_do_dong(tiec, hom_nay)
    if dong:
        raise ValueError(dong)
    ten = str(du_lieu.get("ten") or "").strip()
    sdt = re.sub(r"[\s.()+-]", "", str(du_lieu.get("sdt") or ""))
    if sdt.startswith("84"):
        sdt = "0" + sdt[2:]
    if not ten or len(ten) > 120 or not re.fullmatch(r"0[35789]\d{8}", sdt):
        raise ValueError("Điền họ tên và số điện thoại di động Việt Nam hợp lệ.")
    so = du_lieu.get("so_ve")
    try:
        so = int(so)
        if str(so) != str(du_lieu.get("so_ve")) or not 1 <= so <= VE_MOT_LAN_TOI_DA:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError("Số vé từ 1 đến %d. Cần nhiều hơn quý khách gọi cho chúng tôi." % VE_MOT_LAN_TOI_DA)
    con = con_ve(tiec, da_dang_ky)
    if con is not None and so > con:
        raise ValueError("Tiệc chỉ còn %d vé." % con if con else "Tiệc đã hết vé.")
    email = str(du_lieu.get("email") or "").strip()
    if email and (len(email) > 140 or not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", email)):
        raise ValueError("Kiểm tra lại email, ví dụ ten@example.com, hoặc để trống.")
    ghi_chu = str(du_lieu.get("ghi_chu") or "").strip()
    if len(ghi_chu) > 500:
        raise ValueError("Ghi chú tối đa 500 ký tự.")
    gia = int(tiec.get("gia_ve") or 0)
    return {
        "tiec_id": tiec["id"], "ten_tiec": tiec.get("tieu_de") or "", "ngay_tiec": tiec.get("bat_dau") or None,
        "ten": ten, "sdt": sdt, "email": email, "so_ve": so, "gia_ve": gia, "tong_tien": gia * so,
        "ghi_chu": ghi_chu,
    }


def soan_tin(doc):
    """Tin gửi nhóm FOH, mỗi giá trị một dòng."""
    doc = {k: re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else v for k, v in doc.items()}
    ngay = ""
    if doc.get("ngay_tiec"):
        ngay = datetime.strptime(str(doc["ngay_tiec"])[:10], "%Y-%m-%d").strftime("%d/%m")
    dong = ["ĐĂNG KÝ TIỆC MỚI",
            "Tiệc: %s%s" % (doc.get("ten_tiec"), (" ngày " + ngay) if ngay else ""),
            "Tên: %s, SĐT: %s" % (doc.get("ten"), doc.get("sdt")),
            "Số vé: %s" % doc.get("so_ve")]
    for k, nhan in (("ghi_chu", "Ghi chú"), ("email", "Email")):
        if doc.get(k):
            dong.append("%s: %s" % (nhan, doc[k]))
    dong.append("Trạng thái: Chờ xác nhận. Mở phiếu: %s" % doc.get("url", ""))
    return "\n".join(dong)


import frappe
from frappe.rate_limiter import rate_limit

DOCTYPE = "Vagabond Dang Ky Tiec"


def dem_ve(ids, khoa=False):
    """Tổng vé đã đăng ký chưa huỷ theo từng tiệc: {id: số}.

    khoa=True là phép đọc HIỆN TẠI có khoá (for update), dùng ngay sau khi
    đã xếp hàng ở cửa đăng ký. MariaDB REPEATABLE READ cho phép đọc thường
    tiếp tục thấy ảnh chụp cũ từ trước lúc chờ khoá, nên hai khách cùng bấm
    sẽ cùng thấy một tổng vé và vượt số vé (Codex #453)."""
    if not ids:
        return {}
    ds = frappe.db.sql(
        """select tiec_id, sum(so_ve) from `tabVagabond Dang Ky Tiec`
        where tiec_id in %(ids)s and trang_thai != 'Đã hủy' group by tiec_id"""
        + (" for update" if khoa else ""),
        {"ids": tuple(ids)},
    )
    return {r[0]: int(r[1] or 0) for r in ds}


def _tiec_trong(ban, id_tiec):
    return next((k for k in ban.get("khoi") or [] if k.get("id") == id_tiec and k.get("loai") == "tiec"), None)


@frappe.whitelist(methods=["POST"], allow_guest=True)
@rate_limit(limit=5, seconds=600)
def dang_ky(du_lieu, ma_lan_gui):
    """Khách gửi đăng ký một tiệc. Gửi lại cùng mã lần gửi thì trả kết quả cũ."""
    if not isinstance(ma_lan_gui, str) or not re.fullmatch(r"[a-f0-9-]{36}", ma_lan_gui):
        frappe.throw("Tải lại trang để bắt đầu đăng ký.")
    try:
        raw = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
        chuoi = json.dumps(raw, sort_keys=True, ensure_ascii=False)
        if not isinstance(raw, dict) or len(chuoi) > 3000:
            raise ValueError("Đăng ký quá dài hoặc không hợp lệ.")
    except (TypeError, ValueError) as e:
        frappe.throw(str(e))
    dau = hashlib.sha256(chuoi.encode()).hexdigest()
    ten = hashlib.sha256(("tiec:" + ma_lan_gui).encode()).hexdigest()
    cu = _da_nhan(ten, dau)
    if cu:
        return cu
    # Khoá hàng nội dung web: mọi đăng ký tiệc xếp hàng qua đây. Sau khoá,
    # MỌI phép đọc phải là đọc hiện tại (for update), không dùng lại ảnh chụp
    # REPEATABLE READ có từ trước lúc chờ (Codex #453). Phép khoá đọc luôn bản
    # công khai, nên cấu hình tiệc (số vé, ẩn hiện, hạn bán) là bản Marketing
    # vừa lưu chứ không phải bản lúc khách bắt đầu gửi (Codex #454).
    from vagabond.noi_dung_web import _ban_cong_khai
    ban = _ban_cong_khai(khoa=True)
    cu = _da_nhan(ten, dau, khoa=True)
    if cu:
        return cu
    tiec = _tiec_trong(ban, str(raw.get("tiec_id") or ""))
    try:
        nd = chuan_hoa(raw, tiec, dem_ve([tiec["id"]], khoa=True).get(tiec["id"], 0) if tiec else 0,
                       str(frappe.utils.nowdate()))
    except (TypeError, ValueError) as e:
        frappe.throw(str(e))
    d = frappe.get_doc(dict(nd, doctype=DOCTYPE, name=ten, bam_noi_dung=dau, trang_thai="Chờ xác nhận", ma_ve=ma_ve(ten)))
    d.flags.dang_ky_web = True
    # Như dat_ban.dat: chưa có hàng nội dung web để khoá thì hai lần gửi cùng
    # mã vẫn có thể cùng tới đây; lần sau đâm khoá chính thì trả lại lần trước.
    moc = "dang_ky_tiec_" + frappe.generate_hash(length=12)
    frappe.db.savepoint(moc)
    so_thong_bao = len(frappe.local.message_log or [])
    try:
        d.insert(ignore_permissions=True)
    except frappe.DuplicateEntryError:
        frappe.db.rollback(save_point=moc)
        cu = _da_nhan(ten, dau, khoa=True)
        if not cu:
            raise
        # db_insert đã thêm thông báo Duplicate Name trước khi ném lỗi.
        del frappe.local.message_log[so_thong_bao:]
        return cu
    return {"ok": 1, "ma": ma_ve(d.name)}


def _da_nhan(ten, dau, khoa=False):
    """Đăng ký cùng mã lần gửi đã có thì trả kết quả cũ, khác nội dung thì chặn."""
    cu = frappe.db.get_value(DOCTYPE, ten, ["name", "bam_noi_dung"], as_dict=True, for_update=khoa)
    if not cu:
        return None
    if cu.bam_noi_dung != dau:
        frappe.throw("Đăng ký trước đã được nhận. Tải lại trang để đăng ký thêm.")
    return {"ok": 1, "ma": ma_ve(cu.name)}


def kiem_phieu(doc):
    """Sales chỉ đổi trạng thái và ghi chú xử lý, không sửa chữ khách đã gửi."""
    if doc.is_new():
        if not doc.flags.dang_ky_web:
            frappe.throw("Đăng ký tiệc chỉ nhận từ trang đặt bánh.")
        return
    cu = doc.get_doc_before_save()
    if cu:
        for ten in ("tiec_id", "ten_tiec", "ngay_tiec", "ten", "sdt", "email", "so_ve", "gia_ve", "tong_tien",
                    "ghi_chu", "bam_noi_dung", "ma_ve"):
            if str(cu.get(ten) or "") != str(doc.get(ten) or ""):
                frappe.throw("Giữ nguyên đăng ký khách đã gửi. Ghi thay đổi vào ghi chú xử lý.")
        chuyen = {"Chờ xác nhận": {"Đã xác nhận", "Đã thanh toán", "Đã hủy"},
                  "Đã xác nhận": {"Đã thanh toán", "Đã hủy"}, "Đã thanh toán": {"Đã hủy"}, "Đã hủy": set()}
        if doc.trang_thai != cu.trang_thai and doc.trang_thai not in chuyen.get(cu.trang_thai, set()):
            frappe.throw("Không chuyển ngược trạng thái được. Ghi rõ kết quả trong ghi chú xử lý.")
    if doc.trang_thai not in TRANG_THAI:
        frappe.throw("Chọn trạng thái đăng ký hợp lệ.")


def con_cho_xac_nhan(ten):
    """Tin Zalo loại việc hỏi lại ngay trước khi gửi: đăng ký còn chờ xác nhận không."""
    return frappe.db.get_value(DOCTYPE, ten, "trang_thai") == "Chờ xác nhận"


def bao_moi(doc, method=None):
    """v597: báo nhóm Zalo chủ đề Đặt bàn (FOH, cùng nhóm với đặt bàn), thay Lark.
    Lỗi báo không làm mất đăng ký."""
    if getattr(frappe.flags, "vagabond_kiem_that", False):
        return
    from vagabond import kenh_zalo
    try:
        d = doc.as_dict()
        d["url"] = frappe.utils.get_url_to_form(DOCTYPE, doc.name)
        tieu_de, dong = kenh_zalo.tach_tin(soan_tin(d))
    except Exception:
        frappe.log_error(title="Đăng ký tiệc: chưa ghi được tin Zalo", message="Phiếu %s." % doc.name)
        return
    # Codex #481: chưa có nhóm nhận thì để lại Error Log nêu tên phiếu.
    kenh_zalo.bao_hoac_ghi_loi("viec", "dat_ban", tieu_de, dong, khoa="tiec:%s" % doc.name,
                               kiem="tiec_cho", nguon=doc.name, ma_tin="bh_tiec")




# ---------------------------------------------------------------- v658 app

def _kiem_quyen_sk():
    if not set(QUYEN_SK) & set(frappe.get_roles()):
        frappe.throw("Màn này mở cho Quầy, Sales, Marketing và giám đốc.", frappe.PermissionError)


COT_KHACH = ["name", "ma_ve", "ten", "sdt", "so_ve", "trang_thai", "da_vao_cua", "vao_cua_luc", "ghi_chu"]


@frappe.whitelist()
def ds_su_kien():
    """Các sự kiện đang bán hoặc mới diễn ra (14 ngày), kèm số đăng ký và số
    vé đã vào cửa. Đọc ĐỦ mọi đăng ký (không giới hạn trang): số vé ở cửa
    phải đúng thật."""
    _kiem_quyen_sk()
    from datetime import date, timedelta
    from vagabond.noi_dung_web import _ban_cong_khai, LOAI_SU_KIEN

    hn = date.fromisoformat(str(frappe.utils.nowdate()))
    moc = str(hn - timedelta(days=14))
    sk = [k for k in (_ban_cong_khai().get("khoi") or []) if k.get("loai") == "tiec" and (k.get("bat_dau") or "9999") >= moc]
    rows = frappe.get_all(DOCTYPE, filters={"tiec_id": ["in", [k["id"] for k in sk] or ["-"]]},
                          fields=COT_KHACH + ["tiec_id"], limit_page_length=0)
    theo = {}
    for r in rows:
        theo.setdefault(r.get("tiec_id"), []).append(dong_khach(r))
    ra = []
    for k in sorted(sk, key=lambda x: (x.get("bat_dau") or "9999", x.get("gio_bat_dau") or "")):
        ra.append(dict(tong_khach(theo.get(k["id"], [])), id=k["id"], ten=k.get("tieu_de") or "", ngay=k.get("bat_dau") or "",
                       gio=k.get("gio_bat_dau") or "", loai=LOAI_SU_KIEN.get(k.get("loai_su_kien") or "tiec", "Tiệc"),
                       tong_cho=int(k.get("so_ve") or 0), hien=bool(k.get("hien"))))
    return {"hom_nay": str(hn), "su_kien": ra}


@frappe.whitelist()
def khach_su_kien(tiec_id):
    """Danh sách khách của một sự kiện, đọc đủ mọi đăng ký."""
    _kiem_quyen_sk()
    rows = frappe.get_all(DOCTYPE, filters={"tiec_id": str(tiec_id or "")}, fields=COT_KHACH,
                          order_by="creation asc", limit_page_length=0)
    ds = [dong_khach(r) for r in rows]
    return {"khach": ds, "tong": tong_khach(ds)}


@frappe.whitelist(methods=["POST"])
def vao_cua(ten, co=1):
    """Đánh dấu (hoặc bỏ dấu) "Đã vào cửa" cho một vé. Khoá đúng dòng rồi mới
    đọc trạng thái (hai máy ở cửa bấm cùng lúc vẫn đúng); bấm hai lần không
    đổi gì; vé đã huỷ thì không đánh dấu."""
    _kiem_quyen_sk()
    muon = str(co) not in ("0", "", "false", "False")
    r = frappe.db.get_value(DOCTYPE, ten, ["name", "trang_thai", "da_vao_cua"], as_dict=True, for_update=True)
    if not r:
        frappe.throw("Không tìm thấy vé này. Tải lại danh sách.")
    ly = ly_do_vao_cua(r.trang_thai, int(r.da_vao_cua or 0), muon)
    if ly and ly != "giu":
        frappe.throw(ly)
    if not ly:
        frappe.db.set_value(DOCTYPE, ten, {"da_vao_cua": 1 if muon else 0,
                                           "vao_cua_luc": frappe.utils.now_datetime() if muon else None})
    moi = frappe.db.get_value(DOCTYPE, ten, COT_KHACH, as_dict=True)
    return dong_khach(moi)
