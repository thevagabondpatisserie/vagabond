"""v586: trình biên tập theo thẻ và đăng ký tiệc, chạy THẬT trên bench riêng.

Ca tầng khung dùng Frappe giả nên chưa từng ghi một phiếu Vagabond Dang Ky
Tiec, chưa ghi ô web_* của Settings, chưa đi qua tao_don với điểm nhận theo
mã (Codex #453). Tệp này chạy đúng chuỗi người dùng trên site thử rồi
rollback toàn bộ. Không gọi mạng ngoài, không gửi Lark (không khai webhook).
"""
import copy
import json

import frappe

from vagabond import noi_dung_web as web
from vagabond import tiec_web


def chay():
    if not frappe.conf.get("vagabond_bench_thu"):
        raise RuntimeError("Chỉ chạy trên bench riêng có vagabond_bench_thu=1.")
    nguoi_cu = frappe.session.user
    req = getattr(frappe.local, "request", None)
    ket = []
    frappe.db.savepoint("web_v586")

    def dat(ten, dieu):
        if not dieu:
            raise AssertionError(ten)
        ket.append(ten)

    def chan(ten, ham, chua=None):
        try:
            ham()
        except (frappe.ValidationError, frappe.PermissionError) as e:
            if chua and chua not in str(e):
                raise AssertionError("%s: câu báo khác (%s)" % (ten, e))
            ket.append(ten)
            return
        raise AssertionError(ten)

    # dang_ky có giới hạn tần suất theo IP; bench gọi thẳng hàm gốc phía sau
    # decorator, phần giới hạn đã có ca riêng của Frappe.
    dang_ky = getattr(tiec_web.dang_ky, "__wrapped__", tiec_web.dang_ky)
    try:
        frappe.local.request = None
        frappe.set_user("Administrator")
        webhook_cu = frappe.db.get_single_value("Vagabond Settings", "webhook_dat_ban")
        if webhook_cu:
            frappe.db.set_single_value("Vagabond Settings", "webhook_dat_ban", "")
        u = frappe.get_doc({"doctype": "User", "email": "web586-marketing@example.invalid", "first_name": "Web 586",
                            "send_welcome_email": 0, "roles": [{"role": "Marketing"}]}).insert()

        # 1. Marketing tạo tiệc qua thẻ Tiệc, khách thấy ngay.
        frappe.set_user(u.name)
        bang = web.bang_moi()
        ngay = str(frappe.utils.add_days(frappe.utils.nowdate(), 10))
        han = str(frappe.utils.add_days(frappe.utils.nowdate(), 8))
        tiec = {"id": "tiec-bench-586", "loai": "tiec", "vi_tri": "tiec", "hien": True, "tieu_de": "Tiệc bench 586",
                "bat_dau": ngay, "gio_bat_dau": "15:00", "gio_ket_thuc": "17:00", "dia_diem": "Cửa hàng Sài Gòn",
                "gia_ve": "100000", "so_ve": "3", "han_ban": han, "noi_dung": "Bench v586"}
        bang = web.luu_muc(json.dumps(tiec), "")
        frappe.clear_document_cache(web.DOCTYPE, web.TEN)
        frappe.set_user("Guest")
        ck = web.cong_khai()
        dat("Guest thấy tiệc vừa lưu", any(k.get("id") == tiec["id"] for k in ck["khoi"]))
        dat("Công khai có đủ phần dẫn xuất", {"thong_tin", "diem_nhan", "lien_he", "ve"} <= set(ck))
        dat("Điểm nhận mang mã cửa hàng", [d["id"] for d in ck["diem_nhan"]] == ["bep-tan-son-hoa", "cua-hang-sai-gon"])

        # 2. Guest đăng ký: ghi phiếu thật, gửi lại cùng mã trả cùng phiếu.
        du = {"tiec_id": tiec["id"], "ten": "Khách bench 586", "sdt": "0912345678", "so_ve": "2"}
        ma1 = "58600000-0000-4000-8000-000000000001"
        r1 = dang_ky(json.dumps(du), ma1)
        ten1 = frappe.db.get_value(tiec_web.DOCTYPE, {"tiec_id": tiec["id"], "sdt": "0912345678"}, "name")
        dat("Ghi phiếu đăng ký thật", bool(ten1) and r1["ok"] == 1)
        dat("Phiếu chờ xác nhận, đủ tiền", frappe.db.get_value(tiec_web.DOCTYPE, ten1, ["trang_thai", "tong_tien"]) == ("Chờ xác nhận", 200000))
        dat("Gửi lại cùng mã trả cùng phiếu", dang_ky(json.dumps(du), ma1)["ma"] == r1["ma"])
        dat("Gửi lại không sinh phiếu thứ hai", frappe.db.count(tiec_web.DOCTYPE, {"tiec_id": tiec["id"]}) == 1)
        chan("Cùng mã đổi nội dung bị chặn", lambda: dang_ky(json.dumps(dict(du, so_ve="1")), ma1), "đã được nhận")
        dat("Guest không đọc được phiếu", not frappe.has_permission(tiec_web.DOCTYPE, "read", doc=ten1))
        # Tiệc 3 vé, đã giữ 2: khách khác xin 2 vé phải bị chặn.
        chan("Vượt số vé bị chặn", lambda: dang_ky(json.dumps(dict(du, sdt="0987654321")),
                                                  "58600000-0000-4000-8000-000000000002"), "chỉ còn 1 vé")
        dat("Vé còn hiện đúng", web.cong_khai()["ve"].get(tiec["id"]) == 2)

        # 3. Sales chỉ đổi trạng thái theo chiều tới.
        frappe.set_user("Administrator")
        p = frappe.get_doc(tiec_web.DOCTYPE, ten1)
        p.trang_thai = "Đã xác nhận"
        p.save()
        p.reload()
        dat("Sales xác nhận được", p.trang_thai == "Đã xác nhận")
        p.so_ve = 3
        chan("Không sửa số vé khách gửi", p.save, "Giữ nguyên")
        p.reload()
        p.trang_thai = "Chờ xác nhận"
        chan("Không chuyển ngược trạng thái", p.save, "ngược")

        # 4. Thẻ Liên hệ ghi đúng ô web_* của Settings.
        frappe.set_user(u.name)
        bang = web.bang_moi()
        lh = dict(bang["lien_he"], dien_thoai="0909 586 586", messenger="https://m.me/bench586")
        web.luu_lien_he(json.dumps(lh), bang["dau_lien_he"])
        dat("Ghi số điện thoại vào Settings", frappe.db.get_single_value("Vagabond Settings", "web_dien_thoai") == "0909 586 586")
        dat("Ghi Messenger vào Settings", frappe.db.get_single_value("Vagabond Settings", "web_messenger") == "https://m.me/bench586")
        chan("Lưu bằng dấu cũ bị chặn", lambda: web.luu_lien_he(json.dumps(lh), bang["dau_lien_he"]), "vừa sửa")

        # 5. Tắt nhận bánh ở Sài Gòn: công khai chỉ còn Bếp, mã giữ nguyên.
        bang = web.bang_moi()
        ch = copy.deepcopy(bang["thong_tin"]["cua_hang"])
        for c in ch:
            if c["id"] == "cua-hang-sai-gon":
                c["nhan_banh"] = False
        web.luu_thong_tin("cua_hang", json.dumps(ch), bang["dau_thong_tin"]["cua_hang"])
        frappe.set_user("Guest")
        dat("Điểm đã tắt không còn ở công khai", [d["id"] for d in web.cong_khai()["diem_nhan"]] == ["bep-tan-son-hoa"])
        dat("Máy chủ đọc đúng điểm nhận theo mã", [d["id"] for d in web.diem_nhan(web._ban_cong_khai())] == ["bep-tan-son-hoa"])
    finally:
        frappe.set_user(nguoi_cu)
        frappe.local.request = req
        frappe.db.rollback(save_point="web_v586")
        frappe.clear_document_cache(web.DOCTYPE, web.TEN)
        frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
    return {"dat": len(ket), "ket_qua": ket}
