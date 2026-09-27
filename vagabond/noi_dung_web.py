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


# #367: ba trang chính sách cùng đi luồng nháp, xuất bản, lịch sử của trang
# đặt bánh, không dựng doctype mới. Mỗi trang có bản tiếng Việt và tiếng Anh
# dạng Markdown, và một công tắc "hien": chưa bật thì trang công khai trả 404
# và chân trang không hiện đường dẫn.
CHINH_SACH = {
    "chinh_sach_bao_mat": {"ten": "Chính sách bảo mật", "duong": "/chinh-sach-bao-mat"},
    "dieu_khoan": {"ten": "Điều khoản sử dụng", "duong": "/dieu-khoan"},
    "giao_hang_doi_tra": {"ten": "Giao hàng và đổi trả", "duong": "/giao-hang-doi-tra"},
}
TRUONG_CHINH_SACH = {"hien", "vn", "en"}


# v532 (anh Việt 27/09/2026): chữ cố định trên thanh chọn, câu giờ chuẩn bị
# và trang đặt bàn cho marketing tự đổi, không phải sửa HTML. Khoá là cố
# định, chỉ đổi được chữ. Chữ trong {ngoặc nhọn} là chỗ máy điền số; khoá nào
# có chỗ điền thì bản sửa phải giữ đủ, kẻo con số biến mất khỏi câu.
# Bản mặc định ở đây PHẢI trùng chữ đang có sẵn trong trang, để trang chưa
# tải xong hay lỗi tải vẫn hiện đúng câu cũ.
NHAN = {
    "tab_season": {"ten": "Tab mùa vụ (chỉ hiện khi có mùa)", "mac_dinh": "In season"},
    "tab_store": {"ten": "Tab bánh trên tủ tại quầy", "mac_dinh": "In store"},
    "tab_today": {"ten": "Tab bánh có sẵn hôm nay", "mac_dinh": "Có sẵn hôm nay"},
    "tab_order": {"ten": "Tab đặt bánh trước", "mac_dinh": "Đặt bánh trước"},
    "nut_dat_ban": {"ten": "Nút Đặt bàn trên đầu trang", "mac_dinh": "Đặt bàn"},
    "nut_thanh_vien": {"ten": "Nút Thành viên trên đầu trang", "mac_dinh": "Thành viên"},
    "cau_co_san": {"ten": "Dòng số bánh có sẵn ({so} là số bánh)", "mac_dinh": "{so} bánh có sẵn"},
    "cau_nhan_tu": {"ten": "Dòng khung giờ nhận sớm nhất ({khung} là khung giờ)", "mac_dinh": "nhận từ {khung}"},
    "cau_het_khung": {"ten": "Dòng khi hôm nay hết khung giờ nhận", "mac_dinh": "hôm nay đã hết khung giờ nhận"},
    "cau_chuan_bi": {"ten": "Câu giờ bếp chuẩn bị ({gio} là số tiếng, {khung} là khung giờ)",
                     "mac_dinh": "Bếp cần khoảng {gio} tiếng để chuẩn bị và đóng gói, nên hôm nay nhận được từ khung {khung} trở đi."},
    "cau_chuan_bi_het": {"ten": "Câu khi hôm nay hết khung giờ nhận (dưới danh sách bánh)",
                         "mac_dinh": "Hôm nay đã hết khung giờ nhận. Anh chị đặt cho ngày mai giúp em nhé."},
    "dat_ban_nhan": {"ten": "Đặt bàn: dòng nhỏ trên tiêu đề", "mac_dinh": "HẸN MỘT BUỔI THONG THẢ"},
    "dat_ban_tieu_de": {"ten": "Đặt bàn: tiêu đề", "mac_dinh": "Đặt bàn tại tiệm."},
    "dat_ban_mo_ta": {"ten": "Đặt bàn: đoạn mô tả",
                      "mac_dinh": "Chọn ngày, giờ và số người. Tiệm sẽ liên hệ xác nhận chỗ; gửi yêu cầu chưa đồng nghĩa đã giữ được bàn."},
    "dat_ban_dong": {"ten": "Đặt bàn: câu hiện khi tiệm chưa mở nhận đặt bàn online",
                     "mac_dinh": "Tiệm chưa mở nhận đặt bàn online. Gọi 0931 224 334 để được hỗ trợ."},
    "dat_ban_nut": {"ten": "Đặt bàn: chữ trên nút gửi", "mac_dinh": "Gửi yêu cầu đặt bàn"},
    "dat_ban_ho_tro": {"ten": "Đặt bàn: câu trước số điện thoại hỗ trợ", "mac_dinh": "Cần hỗ trợ ngay?"},
}
DAI_NHAN = 300
RE_CHO_DIEN = re.compile(r"\{[a-z_]+\}")


def cho_dien(chu):
    """Các chỗ máy điền dạng {so}, {khung} trong một câu. THUẦN."""
    return sorted(set(RE_CHO_DIEN.findall(str(chu or ""))))


def _chuan_hoa_nhan(nhan):
    if not isinstance(nhan, dict) or set(nhan) - set(NHAN):
        raise ValueError("Nhãn không có trong danh sách cho phép. Tải lại trang biên tập.")
    for khoa, chu in nhan.items():
        if not isinstance(chu, str) or len(chu) > DAI_NHAN:
            raise ValueError("Nhãn %s quá dài hoặc không hợp lệ (tối đa %d ký tự)." % (NHAN[khoa]["ten"], DAI_NHAN))
        if "\n" in chu and not khoa.startswith("dat_ban_"):
            raise ValueError("Nhãn %s chỉ có một dòng." % NHAN[khoa]["ten"])
        if not chu.strip():
            continue  # để trống là dùng chữ mặc định
        thieu = set(cho_dien(NHAN[khoa]["mac_dinh"])) - set(cho_dien(chu))
        if thieu:
            raise ValueError("Nhãn %s phải giữ chỗ điền %s để máy điền số." % (NHAN[khoa]["ten"], ", ".join(sorted(thieu))))
        la = set(cho_dien(chu)) - set(cho_dien(NHAN[khoa]["mac_dinh"]))
        if la:
            raise ValueError("Nhãn %s có chỗ điền máy không hiểu: %s." % (NHAN[khoa]["ten"], ", ".join(sorted(la))))


def nhan_day_du(du_lieu):
    """Bộ nhãn đầy đủ để trang dùng: chữ marketing đã sửa, chỗ trống thì
    lấy mặc định. THUẦN, là NGUỒN DUY NHẤT ghép nhãn với mặc định."""
    da_sua = (du_lieu or {}).get("nhan") or {}
    ra = {}
    for khoa, v in NHAN.items():
        chu = da_sua.get(khoa)
        ra[khoa] = chu if isinstance(chu, str) and chu.strip() else v["mac_dinh"]
    return ra


def khoa_tu_duong(duong):
    """Khoá trang chính sách từ đường dẫn yêu cầu, "" nếu không phải trang
    chính sách. Frappe không truyền `defaults` của luật định tuyến vào
    form_dict, nên trang www/chinh_sach.py phải tự suy từ đường dẫn."""
    d = "/" + str(duong or "").split("?", 1)[0].strip().strip("/")
    for khoa, cs in CHINH_SACH.items():
        if d == cs["duong"]:
            return khoa
    return ""
DAI_CHINH_SACH = 30000
# Chỗ trong ngoặc vuông marketing phải điền trước khi bật trang, ví dụ
# "[số điện thoại]". Không bắt "[chữ](liên kết)" vì đó là liên kết Markdown.
RE_CHO_TRONG = re.compile(r"\[[^\]\n]{1,80}\](?!\()")


def cho_trong(md):
    """Các chỗ trong ngoặc vuông còn chưa điền trong một bản Markdown."""
    return RE_CHO_TRONG.findall(str(md or ""))


def _chuan_hoa_chinh_sach(cs):
    if not isinstance(cs, dict) or set(cs) - set(CHINH_SACH):
        raise ValueError("Chỉ có ba trang chính sách: bảo mật, điều khoản, giao hàng và đổi trả.")
    for khoa, v in cs.items():
        if not isinstance(v, dict) or set(v) - TRUONG_CHINH_SACH:
            raise ValueError("Trang chính sách có trường không được hỗ trợ.")
        if type(v.get("hien", False)) is not bool:
            raise ValueError("Chọn hiện hoặc ẩn cho trang " + CHINH_SACH[khoa]["ten"] + ".")
        for ngu in ("vn", "en"):
            chu = v.get(ngu, "")
            if not isinstance(chu, str) or len(chu) > DAI_CHINH_SACH:
                raise ValueError("Nội dung %s quá dài hoặc không hợp lệ." % CHINH_SACH[khoa]["ten"])
        if v.get("hien") and not str(v.get("vn") or "").strip():
            raise ValueError("Trang %s chưa có nội dung tiếng Việt nên chưa bật hiện được." % CHINH_SACH[khoa]["ten"])


def loi_xuat_ban(du_lieu):
    """Câu báo nếu bản sắp xuất bản còn chính sách bật hiện mà chưa điền đủ. THUẦN."""
    cs = (du_lieu or {}).get("chinh_sach") or {}
    loi = []
    for khoa, v in cs.items():
        if not v.get("hien"):
            continue
        con = cho_trong(v.get("vn")) + cho_trong(v.get("en"))
        if con:
            loi.append("%s còn %d chỗ chưa điền, ví dụ %s" % (CHINH_SACH[khoa]["ten"], len(con), con[0]))
    if not loi:
        return ""
    return "Chưa xuất bản được. " + "; ".join(loi) + ". Điền các chỗ trong ngoặc vuông hoặc tắt hiện trang đó rồi xuất bản lại."


VAI_SOAN = {"Marketing", "System Manager"}
DUONG_BANG = "/bien-tap-web"


def quyet_vao_bang(nguoi, vai):
    """Ai mở /bien-tap-web thì thấy gì. THUẦN.

    Trước #367 mục 8, khách vãng lai mở trang thì kiem_quyen() ném lỗi giữa
    lúc dựng trang: Minh Vũ thấy một bảng trống kèm câu lỗi kỹ thuật, không
    có nút đăng nhập nào. Nay:
      dang_nhap   chưa đăng nhập: chuyển sang trang đăng nhập, quay lại đây;
      khong_quyen đã đăng nhập mà thiếu vai Marketing: trang báo quyền;
      vao         có vai: vào bảng điều khiển.
    """
    if not nguoi or nguoi == "Guest":
        return "dang_nhap"
    if not (VAI_SOAN & set(vai or [])):
        return "khong_quyen"
    return "vao"


def chuan_hoa(du_lieu):
    """Giới hạn kích thước và cấu trúc trước khi lưu, dùng cả ở Document.save."""
    if isinstance(du_lieu, str):
        if len(du_lieu) > 250000:
            raise ValueError("Nội dung quá dài. Giảm số khối hoặc độ dài bài viết.")
        du_lieu = json.loads(du_lieu)
    if not isinstance(du_lieu, dict) or "khoi" not in du_lieu or set(du_lieu) - {"khoi", "chinh_sach", "nhan"}:
        raise ValueError("Nội dung phải có danh sách khối.")
    if "chinh_sach" in du_lieu:
        _chuan_hoa_chinh_sach(du_lieu["chinh_sach"])
    if "nhan" in du_lieu:
        _chuan_hoa_nhan(du_lieu["nhan"])
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


def _ban_cong_khai():
    if not frappe.db.exists(DOCTYPE, TEN):
        return copy.deepcopy(MAC_DINH)
    return json.loads(frappe.db.get_value(DOCTYPE, TEN, "ban_cong_khai") or json.dumps(MAC_DINH))


@frappe.whitelist(allow_guest=True)
def cong_khai():
    """Chỉ trả bản đã xuất bản, tuyệt đối không trả nháp hoặc lịch sử.

    Bỏ phần chính sách ra (#367): mỗi khách mở trang đặt bánh đều gọi hàm
    này, không cần tải theo ba bài viết dài mấy nghìn chữ.
    """
    ra = _ban_cong_khai()
    ra.pop("chinh_sach", None)
    # v532: trang luôn nhận bộ nhãn đầy đủ, không tự ghép mặc định ở phía khách.
    ra["nhan"] = nhan_day_du(ra)
    return ra


def nhan_cong_khai():
    """Bộ nhãn đã xuất bản cho các trang dựng ở máy chủ (đặt bàn)."""
    return nhan_day_du(_ban_cong_khai())


def chinh_sach_dang_hien():
    """Danh sách trang chính sách đã xuất bản và bật hiện, cho chân trang."""
    cs = (_ban_cong_khai().get("chinh_sach") or {})
    return [
        {"khoa": k, "ten": CHINH_SACH[k]["ten"], "duong": CHINH_SACH[k]["duong"]}
        for k in CHINH_SACH
        if (cs.get(k) or {}).get("hien") and str((cs.get(k) or {}).get("vn") or "").strip()
    ]


def trang_chinh_sach(khoa, ngon_ngu="vn"):
    """HTML đã làm sạch của một trang chính sách đã xuất bản, hoặc None.

    Markdown do marketing viết nên có thể chứa HTML; `md_to_html` của Frappe
    để nguyên HTML thô, nên BẮT BUỘC qua `sanitize_html(always_sanitize=True)`.
    """
    from frappe.utils import md_to_html
    from frappe.utils.html_utils import sanitize_html

    if khoa not in CHINH_SACH:
        return None
    v = (_ban_cong_khai().get("chinh_sach") or {}).get(khoa) or {}
    if not v.get("hien") or not str(v.get("vn") or "").strip():
        return None
    md = v.get("en") if ngon_ngu == "en" and str(v.get("en") or "").strip() else v.get("vn")
    return {
        "ten": CHINH_SACH[khoa]["ten"],
        "html": sanitize_html(md_to_html(md) or "", always_sanitize=True),
        "co_en": bool(str(v.get("en") or "").strip()),
        "ngon_ngu": "en" if md is v.get("en") and ngon_ngu == "en" else "vn",
    }


def gieo_tu_tep():
    """Đọc bản nháp ba chính sách đã duyệt trong vagabond/du_lieu/chinh_sach/
    rồi gieo. Dùng chung cho patch #367 và patch gieo lại v531."""
    import io
    import os
    thu_muc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "du_lieu", "chinh_sach")
    nhap = {}
    for khoa in CHINH_SACH:
        with io.open(os.path.join(thu_muc, khoa + ".md"), encoding="utf-8") as f:
            nhap[khoa] = f.read().strip() + "\n"
    return gieo_chinh_sach(nhap)


def gieo_chinh_sach(ban_nhap_vn):
    """Gieo bản nháp ba chính sách vào BẢN NHÁP, không đụng bản công khai.

    Lặp lại được: trang nào đã có trong nháp thì giữ nguyên, kể cả khi
    marketing đã xoá trắng nội dung. Chưa có bản ghi thì tạo với nội dung
    mặc định cho phần khối.
    """
    if frappe.db.exists(DOCTYPE, TEN):
        d = _doc()
        nhap = json.loads(d.ban_nhap or json.dumps(MAC_DINH))
    else:
        # v531: new_doc chứ không get_doc(dict). Bản ghi dựng bằng get_doc(dict)
        # không mang cờ "mới" nên is_new() trả False, nhánh dưới gọi save() và
        # Frappe đi tìm bản ghi chưa có: "Vagabond Noi Dung Web order not found".
        # Lỗi thật lúc deploy v529 ngày 27/09/2026, ba trang chính sách không
        # được gieo bản nháp.
        d = frappe.new_doc(DOCTYPE)
        d.name = TEN
        d.ban_nhap = json.dumps(MAC_DINH)
        d.ban_cong_khai = json.dumps(MAC_DINH)
        d.phien_ban = 0
        d.lich_su = "[]"
        nhap = copy.deepcopy(MAC_DINH)
    cs = nhap.setdefault("chinh_sach", {})
    doi = False
    for khoa, noi_dung in (ban_nhap_vn or {}).items():
        if khoa in CHINH_SACH and khoa not in cs:
            cs[khoa] = {"hien": False, "vn": noi_dung, "en": ""}
            doi = True
    if not doi:
        return False
    chuan_hoa(nhap)
    d.ban_nhap = json.dumps(nhap, ensure_ascii=False)
    d.flags.luu_noi_dung_web = True
    if d.is_new():
        d.insert(ignore_permissions=True)
    else:
        d.save(ignore_permissions=True)
    return True


@frappe.whitelist()
def doc_bang():
    kiem_quyen()
    # v532: bảng biên tập lấy danh sách nhãn (tên, mặc định) từ máy chủ, không
    # chép cứng trong JS, để thêm nhãn chỉ sửa một chỗ.
    if not frappe.db.exists(DOCTYPE, TEN):
        return {"nhap": copy.deepcopy(MAC_DINH), "cong_khai": copy.deepcopy(MAC_DINH), "phien_ban": 0, "lich_su": [],
                "nhan_mau": copy.deepcopy(NHAN)}
    d = _doc()
    return {"nhap": json.loads(d.ban_nhap), "cong_khai": json.loads(d.ban_cong_khai),
            "phien_ban": d.phien_ban, "lich_su": json.loads(d.lich_su or "[]"), "nguoi_sua": d.modified_by, "luc_sua": d.modified,
            "nhan_mau": copy.deepcopy(NHAN)}


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
    if hanh_dong == "xuat_ban" and loi_xuat_ban(nd):
        frappe.throw(loi_xuat_ban(nd))
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
