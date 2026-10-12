"""#245: kiểm lưu thật trên bench riêng, không chạy trên site bán hàng.

bench --site <site-thu> execute vagabond.khung.bench_thu.web_editor_245.chay
Yêu cầu migrate trước, site_config.vagabond_bench_thu=1. Rollback toàn bộ.
"""
import copy
import json
import frappe
from vagabond import noi_dung_web as web


# Phần cong_khai() tự ghép thêm, không nằm trong nội dung đã lưu: "nhan" từ
# v532; thông tin cửa hàng, điểm nhận, liên hệ và số vé tiệc từ v586.
DAN_XUAT = ("nhan", "thong_tin", "diem_nhan", "lien_he", "ve")


def _bo_nhan(x):
    """Nội dung công khai bỏ các phần dẫn xuất, chỉ còn phần đã lưu để so.
    Các phần dẫn xuất kiểm riêng (bộ nhãn ở đây, phần v586 ở web_v586)."""
    ra = dict(x or {})
    for k in DAN_XUAT:
        ra.pop(k, None)
    return ra


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
        dat("Guest không đọc được nháp", _bo_nhan(web.cong_khai()) == web.MAC_DINH)
        dat("Guest nhận đủ bộ nhãn mặc định", web.cong_khai().get("nhan") == web.nhan_day_du({}))
        chan("Guest không đọc dashboard", web.doc_bang)
        chan("Guest không ghi nội dung", lambda: web.luu(json.dumps(nd), 1))
        frappe.set_user(u.name)
        chan("Ngăn người sửa từ phiên bản cũ", lambda: web.luu(json.dumps(nd), 0, "xuat_ban"))
        dat("Xung đột không đổi nội dung công khai", _bo_nhan(web.cong_khai()) == web.MAC_DINH)
        d = frappe.get_doc(web.DOCTYPE, web.TEN)
        d.ban_cong_khai = json.dumps(nd)
        chan("Document.save trực tiếp không vượt editor", d.save)
        xb = web.luu(json.dumps(nd), 1, "xuat_ban")
        dat("Xuất bản reload đúng nội dung", _bo_nhan(web.cong_khai()) == nd)
        dat("Lịch sử giữ bản trước", xb["lich_su"][0]["noi_dung"] == web.MAC_DINH)
        phuc_hoi = web.luu(json.dumps(xb["lich_su"][0]["noi_dung"]), xb["phien_ban"])
        dat("Khôi phục chỉ đổi nháp", phuc_hoi["nhap"] == web.MAC_DINH and _bo_nhan(web.cong_khai()) == nd)
        from vagabond.trang import dong_bo
        frappe.set_user("Administrator")
        dong_bo()
        dat("Đồng bộ Web Page không đè nội dung marketing", _bo_nhan(web.cong_khai()) == nd)
        frappe.set_user("Guest")
        dat("Public API chỉ có khối và các phần dẫn xuất", set(web.cong_khai()) == {"khoi", *DAN_XUAT})
        dat("Guest không thấy nháp qua thông tin cửa hàng", web.cong_khai()["thong_tin"] == web.thong_tin_day_du(nd))
    finally:
        frappe.set_user(nguoi_cu)
        frappe.db.rollback(save_point="web_editor_245")
        frappe.clear_document_cache(web.DOCTYPE, web.TEN)
    return {"dat": len(ket_qua), "ket_qua": ket_qua}
