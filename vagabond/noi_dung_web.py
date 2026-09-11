"""Marketing sửa nội dung độc lập với Web Page do Git quản lý (#245).

Giá, tồn và giao dịch vẫn lấy từ API đặt bánh. Khối chỉ chứa nội dung;
không nhận HTML/JS hay giá bán do người soạn gửi lên.
"""

# phần thuần
import copy
import json
import re
from urllib.parse import urlsplit

LOAI = {"tieu_de_muc", "anh_bia", "cau_chuyen", "anh_chu", "thong_bao"}
TRUONG = {"id", "loai", "hien", "nhan", "tieu_de", "noi_dung", "anh", "mo_ta_anh", "nut", "lien_ket", "vi_tri"}
VI_TRI = {"dau_trang", "today", "order", "store", "season", "cuoi_trang"}
MAC_DINH = {"khoi": [
    {"id":"tieu-de-hom-nay", "loai":"tieu_de_muc", "hien":True, "vi_tri":"today", "tieu_de":"Bánh\nhôm nay"},
    {"id":"tieu-de-dat-truoc", "loai":"tieu_de_muc", "hien":True, "vi_tri":"order", "tieu_de":"Đặt\nbánh trước"},
    {"id":"tieu-de-tai-quay", "loai":"tieu_de_muc", "hien":True, "vi_tri":"store", "tieu_de":"Bánh trên tủ\ntại quầy"},
    {"id": "loi-chao", "loai": "thong_bao", "hien": True, "vi_tri": "dau_trang",
     "nhan": "THE VAGABOND PÂTISSERIE · SINCE 2015", "tieu_de": "Một chiếc bánh, một khoảnh khắc đáng nhớ.",
     "noi_dung": "", "anh": "", "mo_ta_anh": "", "nut": "", "lien_ket": ""},
    {"id": "cau-chuyen", "loai": "cau_chuyen", "hien": True, "vi_tri": "cuoi_trang",
     "nhan": "TỪ TIỆM BÁNH", "tieu_de": "Những khoảnh khắc ngọt ngào",
     "noi_dung": "Một chiếc bánh, một dịp gặp nhau. Chọn bánh có sẵn hôm nay hoặc đặt trước cho những ngày đặc biệt.",
     "anh": "", "mo_ta_anh": "", "nut": "Đặt bánh trước", "lien_ket": "#/dat-truoc"}
]}


def chuan_hoa(du_lieu):
    """Giới hạn kích thước và cấu trúc trước khi lưu, dùng cả ở Document.save."""
    if isinstance(du_lieu, str):
        if len(du_lieu) > 100000:
            raise ValueError("Nội dung quá dài. Giảm số khối hoặc độ dài bài viết.")
        du_lieu = json.loads(du_lieu)
    if not isinstance(du_lieu, dict) or set(du_lieu) != {"khoi"}:
        raise ValueError("Nội dung phải có danh sách khối.")
    ds = du_lieu["khoi"]
    if not isinstance(ds, list) or len(ds) > 30:
        raise ValueError("Mỗi trang có tối đa 30 khối.")
    da_co = set()
    tieu_de_da_co = set()
    for k in ds:
        if not isinstance(k, dict) or set(k) - TRUONG:
            raise ValueError("Khối có trường không được hỗ trợ.")
        if k.get("loai") not in LOAI or not re.fullmatch(r"[a-zA-Z0-9_-]{1,60}", str(k.get("id", ""))):
            raise ValueError("Loại hoặc mã khối không hợp lệ.")
        if k["id"] in da_co:
            raise ValueError("Mã khối bị trùng. Tải lại rồi thêm khối mới.")
        da_co.add(k["id"])
        if k.get("vi_tri", "cuoi_trang") not in VI_TRI:
            raise ValueError("Chọn vị trí khối trên trang đặt bánh.")
        if k['loai'] == 'tieu_de_muc':
            vi_tri = k.get('vi_tri')
            if vi_tri not in ('today', 'order', 'store') or vi_tri in tieu_de_da_co:
                raise ValueError('Mỗi mục bán hàng chỉ có một khối tiêu đề.')
            if not k.get('tieu_de', '').strip() or len(k['tieu_de']) > 120:
                raise ValueError('Tiêu đề mục cần có chữ và tối đa 120 ký tự.')
            tieu_de_da_co.add(vi_tri)
        if type(k.get("hien")) is not bool:
            raise ValueError("Chọn hiện hoặc ẩn cho từng khối.")
        for ten in TRUONG - {"hien"}:
            v = k.get(ten, "")
            if not isinstance(v, str) or len(v) > (4000 if ten == "noi_dung" else 1000):
                raise ValueError("Chữ trong khối quá dài hoặc không hợp lệ: " + ten)
        for ten in ("anh", "lien_ket"):
            v = k.get(ten, "")
            if not v:
                continue
            if any(ord(c) < 33 for c in v) or "\\" in v:
                raise ValueError("Liên kết không hợp lệ: " + ten)
            u = urlsplit(v)
            noi_bo = v.startswith("/") and not v.startswith("//")
            neo = ten == "lien_ket" and v.startswith("#")
            if not (noi_bo or neo or (u.scheme == "https" and u.hostname and not u.username and not u.password)):
                raise ValueError("Chỉ dùng liên kết HTTPS hoặc đường dẫn trong website.")
            if ten == "anh" and (v.startswith("/private/") or v.lower().split("?")[0].endswith(".svg")):
                raise ValueError("Chọn ảnh công khai PNG, JPG hoặc WebP.")
    return copy.deepcopy(du_lieu)


import frappe

TEN = "order"
DOCTYPE = "Vagabond Noi Dung Web"


def kiem_quyen():
    if frappe.session.user == "Guest" or not ({"Marketing", "System Manager"} & set(frappe.get_roles())):
        frappe.throw("Bạn cần quyền Marketing để chỉnh nội dung website.", frappe.PermissionError)


def _doc():
    return frappe.get_doc(DOCTYPE, TEN)


@frappe.whitelist(allow_guest=True)
def cong_khai():
    """Chỉ trả bản đã xuất bản, tuyệt đối không trả nháp hoặc lịch sử."""
    if not frappe.db.exists(DOCTYPE, TEN):
        return copy.deepcopy(MAC_DINH)
    return json.loads(frappe.db.get_value(DOCTYPE, TEN, "ban_cong_khai") or json.dumps(MAC_DINH))


@frappe.whitelist()
def doc_bang():
    kiem_quyen()
    if not frappe.db.exists(DOCTYPE, TEN):
        return {"nhap": copy.deepcopy(MAC_DINH), "cong_khai": copy.deepcopy(MAC_DINH), "phien_ban": 0, "lich_su": []}
    d = _doc()
    return {"nhap": json.loads(d.ban_nhap), "cong_khai": json.loads(d.ban_cong_khai),
            "phien_ban": d.phien_ban, "lich_su": json.loads(d.lich_su or "[]"), "nguoi_sua": d.modified_by, "luc_sua": d.modified}


@frappe.whitelist(methods=["POST"])
def tai_anh():
    """Ảnh marketing là tài nguyên công khai, chỉ nhận bitmap đã giải mã được."""
    kiem_quyen()
    from io import BytesIO
    from PIL import Image
    from frappe.utils.file_manager import save_file
    tep = frappe.request.files.get("file")
    if not tep:
        frappe.throw("Chọn ảnh PNG, JPG hoặc WebP để tải lên.")
    noi_dung = tep.stream.read(10 * 1024 * 1024 + 1)
    if len(noi_dung) > 10 * 1024 * 1024:
        frappe.throw("Ảnh lớn hơn 10 MB. Thu nhỏ ảnh rồi tải lại.")
    try:
        with Image.open(BytesIO(noi_dung)) as anh:
            duoi = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}.get(anh.format)
            if not duoi or anh.width * anh.height > 25000000:
                raise ValueError("Ảnh không hợp lệ")
            anh.verify()
    except Exception:
        frappe.throw("Không đọc được ảnh. Chọn ảnh PNG, JPG hoặc WebP dưới 25 triệu điểm ảnh.")
    # Frappe utils/file_manager.py:save_file tự kiểm cỡ, băm và lưu File.
    # Tên tạo ở máy chủ để tên người dùng không trở thành đường dẫn.
    f = save_file("web-" + frappe.generate_hash(length=12) + "." + duoi, noi_dung, None, None, is_private=0)
    return {"url": f.file_url}


@frappe.whitelist(methods=["POST"])
def luu(noi_dung, phien_ban, hanh_dong="nhap"):
    kiem_quyen()
    if hanh_dong not in ("nhap", "xuat_ban"):
        frappe.throw("Chọn Lưu nháp hoặc Xuất bản.")
    try:
        nd = chuan_hoa(noi_dung)
        pb = int(phien_ban)
    except (ValueError, TypeError) as e:
        frappe.throw(str(e))
    # Khóa hàng trước khi so phiên bản, tránh hai người cùng xuất bản ghi đè.
    hang = frappe.db.sql("select name from `tabVagabond Noi Dung Web` where name=%s for update", (TEN,))
    if hang:
        d = _doc()
    else:
        d = frappe.get_doc({"doctype": DOCTYPE, "name": TEN, "ban_nhap": json.dumps(MAC_DINH),
                             "ban_cong_khai": json.dumps(MAC_DINH), "phien_ban": 0, "lich_su": "[]"})
    if pb != int(d.phien_ban or 0):
        frappe.throw("Có người vừa sửa trang. Sao chép phần đang viết rồi tải lại trước khi lưu.")
    d.ban_nhap = json.dumps(nd, ensure_ascii=False)
    if hanh_dong == "xuat_ban":
        ls = json.loads(d.lich_su or "[]")
        ls.insert(0, {"phien_ban": int(d.phien_ban or 0), "luc": str(frappe.utils.now()),
                      "nguoi": frappe.session.user, "noi_dung": json.loads(d.ban_cong_khai)})
        d.lich_su = json.dumps(ls[:20], ensure_ascii=False)
        d.ban_cong_khai = d.ban_nhap
    d.flags.luu_noi_dung_web = True
    if hang:
        d.save()
    else:
        d.insert()
    return doc_bang()
