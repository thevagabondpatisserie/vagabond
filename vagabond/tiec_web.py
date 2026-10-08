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
    if doc.get("tong_tien"):
        dong.append("Tạm tính: {:,} đ".format(int(doc["tong_tien"])).replace(",", "."))
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
    d = frappe.get_doc(dict(nd, doctype=DOCTYPE, name=ten, bam_noi_dung=dau, trang_thai="Chờ xác nhận"))
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
    return {"ok": 1, "ma": d.name[:8].upper()}


def _da_nhan(ten, dau, khoa=False):
    """Đăng ký cùng mã lần gửi đã có thì trả kết quả cũ, khác nội dung thì chặn."""
    cu = frappe.db.get_value(DOCTYPE, ten, ["name", "bam_noi_dung"], as_dict=True, for_update=khoa)
    if not cu:
        return None
    if cu.bam_noi_dung != dau:
        frappe.throw("Đăng ký trước đã được nhận. Tải lại trang để đăng ký thêm.")
    return {"ok": 1, "ma": cu.name[:8].upper()}


def kiem_phieu(doc):
    """Sales chỉ đổi trạng thái và ghi chú xử lý, không sửa chữ khách đã gửi."""
    if doc.is_new():
        if not doc.flags.dang_ky_web:
            frappe.throw("Đăng ký tiệc chỉ nhận từ trang đặt bánh.")
        return
    cu = doc.get_doc_before_save()
    if cu:
        for ten in ("tiec_id", "ten_tiec", "ngay_tiec", "ten", "sdt", "email", "so_ve", "gia_ve", "tong_tien",
                    "ghi_chu", "bam_noi_dung"):
            if str(cu.get(ten) or "") != str(doc.get(ten) or ""):
                frappe.throw("Giữ nguyên đăng ký khách đã gửi. Ghi thay đổi vào ghi chú xử lý.")
        chuyen = {"Chờ xác nhận": {"Đã xác nhận", "Đã thanh toán", "Đã hủy"},
                  "Đã xác nhận": {"Đã thanh toán", "Đã hủy"}, "Đã thanh toán": {"Đã hủy"}, "Đã hủy": set()}
        if doc.trang_thai != cu.trang_thai and doc.trang_thai not in chuyen.get(cu.trang_thai, set()):
            frappe.throw("Không chuyển ngược trạng thái được. Ghi rõ kết quả trong ghi chú xử lý.")
    if doc.trang_thai not in TRANG_THAI:
        frappe.throw("Chọn trạng thái đăng ký hợp lệ.")


def bao_moi(doc, method=None):
    """Báo nhóm FOH qua đúng kênh Lark của đặt bàn. Lỗi báo không làm mất đăng ký."""
    if getattr(frappe.flags, "vagabond_kiem_that", False):
        return
    try:
        if not frappe.db.get_single_value("Vagabond Settings", "webhook_dat_ban"):
            return
        frappe.db.after_commit.add(lambda: _xep(doc.name))
    except Exception:
        frappe.log_error(title="Đăng ký tiệc: chưa gửi được Lark", message="Phiếu %s." % doc.name)


def _xep(ten):
    try:
        frappe.enqueue("vagabond.tiec_web.gui_lark", ten=ten, queue="short")
    except Exception:
        frappe.log_error(title="Đăng ký tiệc: chưa gửi được Lark", message="Phiếu %s." % ten)
        frappe.db.commit()


def gui_lark(ten):
    from vagabond.gui_thu import ban_webhook
    try:
        url = str(frappe.db.get_single_value("Vagabond Settings", "webhook_dat_ban") or "").strip()
        if not url:
            return
        doc = frappe.get_doc(DOCTYPE, ten).as_dict()
        doc["url"] = frappe.utils.get_url_to_form(DOCTYPE, ten)
        if not ban_webhook(soan_tin(doc), url=url):
            frappe.log_error(title="Đăng ký tiệc: chưa gửi được Lark", message="Phiếu %s." % ten)
    except Exception:
        frappe.log_error(title="Đăng ký tiệc: chưa gửi được Lark", message="Phiếu %s." % ten)
