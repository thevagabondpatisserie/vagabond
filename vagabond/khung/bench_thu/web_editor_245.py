"""#245: kiểm lưu thật trên bench riêng, không chạy trên site bán hàng.

bench --site <site-thu> execute vagabond.khung.bench_thu.web_editor_245.chay
Yêu cầu migrate trước, site_config.vagabond_bench_thu=1. Rollback toàn bộ.
"""
import copy
import json
import frappe
from vagabond import noi_dung_web as web


def chay():
    if not frappe.conf.get("vagabond_bench_thu"):
        frappe.throw("Chỉ chạy trên bench riêng có vagabond_bench_thu=1.")
    if frappe.db.exists(web.DOCTYPE, web.TEN):
        frappe.throw("Bench đã có nội dung order. Dùng site thử trống để không sửa dữ liệu có sẵn.")
    nguoi_cu = frappe.session.user
    frappe.db.savepoint("web_editor_245")
    ket_qua = []

    def dat(ten, dieu):
        if not dieu:
            raise AssertionError(ten)
        ket_qua.append(ten)

    def chan(ten, ham):
        try:
            ham()
        except frappe.ValidationError:
            ket_qua.append(ten)
            return
        except frappe.PermissionError:
            ket_qua.append(ten)
            return
        raise AssertionError(ten)

    try:
        frappe.set_user("Administrator")
        u = frappe.get_doc({"doctype":"User", "email":"web245-marketing@example.invalid", "first_name":"Web 245",
                            "send_welcome_email":0, "roles":[{"role":"Marketing"}]}).insert()
        frappe.set_user(u.name)
        dau = web.doc_bang()
        dat("Nháp mặc định chưa có bản ghi", dau["phien_ban"] == 0)
        nd = copy.deepcopy(dau["nhap"])
        nd["khoi"][0]["tieu_de"] = "BẢN NHÁP KHÔNG CÔNG KHAI"
        nhap = web.luu(json.dumps(nd), 0)
        frappe.clear_document_cache(web.DOCTYPE, web.TEN)
        dat("Nháp reload từ DB", web.doc_bang()["nhap"] == nd)
        dat("Lưu nháp tăng phiên bản", nhap["phien_ban"] == 1)
        frappe.set_user("Guest")
        dat("Guest không đọc được nháp", web.cong_khai() == web.MAC_DINH)
        chan("Guest không đọc dashboard", web.doc_bang)
        chan("Guest không ghi nội dung", lambda: web.luu(json.dumps(nd), 1))
        frappe.set_user(u.name)
        chan("Ngăn người sửa từ phiên bản cũ", lambda: web.luu(json.dumps(nd), 0, "xuat_ban"))
        dat("Xung đột không đổi nội dung công khai", web.cong_khai() == web.MAC_DINH)
        d = frappe.get_doc(web.DOCTYPE, web.TEN)
        d.ban_cong_khai = json.dumps(nd)
        chan("Document.save trực tiếp không vượt editor", d.save)
        xb = web.luu(json.dumps(nd), 1, "xuat_ban")
        dat("Xuất bản reload đúng nội dung", web.cong_khai() == nd)
        dat("Lịch sử giữ bản trước", xb["lich_su"][0]["noi_dung"] == web.MAC_DINH)
        phuc_hoi = web.luu(json.dumps(xb["lich_su"][0]["noi_dung"]), xb["phien_ban"])
        dat("Khôi phục chỉ đổi nháp", phuc_hoi["nhap"] == web.MAC_DINH and web.cong_khai() == nd)
        from vagabond.trang import dong_bo
        frappe.set_user("Administrator")
        dong_bo()
        dat("Đồng bộ Web Page không đè nội dung marketing", web.cong_khai() == nd)
        frappe.set_user("Guest")
        dat("Public API chỉ có khối", set(web.cong_khai()) == {"khoi"})
    finally:
        frappe.set_user(nguoi_cu)
        frappe.db.rollback(save_point="web_editor_245")
        frappe.clear_document_cache(web.DOCTYPE, web.TEN)
    return {"dat": len(ket_qua), "ket_qua": ket_qua}
