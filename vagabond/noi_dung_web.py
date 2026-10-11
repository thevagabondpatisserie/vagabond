"""Marketing sửa nội dung độc lập với Web Page do Git quản lý (#245).

Giá, tồn và giao dịch vẫn lấy từ API đặt bánh. Khối chỉ chứa nội dung;
không nhận HTML/JS hay giá bán do người soạn gửi lên.
"""

# phần thuần
import copy
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

LOAI = {"tieu_de_muc", "anh_bia", "cau_chuyen", "anh_chu", "thong_bao", "hoi_dap", "uu_dai", "tuyen_dung", "tiec", "kenh_dat_hang", "zalo_oa", "nut_kenh"}
# v586 (Minh Vũ đề xuất, anh Việt duyệt 07/10/2026): ưu đãi có điều kiện đơn
# tối thiểu và khung giờ, tuyển dụng có yêu cầu và quyền lợi, thêm loại Tiệc
# có giá vé, số vé, hạn đăng ký. Mọi trường vẫn là CHUỖI để giữ một phép kiểm
# chung cho chữ; con số được kiểm riêng là chuỗi chữ số.
TRUONG_MOI_586 = {"don_toi_thieu", "gio_bat_dau", "gio_ket_thuc", "dieu_kien", "yeu_cau",
                  "gia_ve", "so_ve", "han_ban", "dia_diem"}
TRUONG = {"id", "loai", "hien", "nhan", "tieu_de", "noi_dung", "anh", "mo_ta_anh", "nut", "lien_ket", "vi_tri", "bat_dau", "ket_thuc", "nhom", "ma_uu_dai", "noi_lam", "hinh_thuc", "email"} | TRUONG_MOI_586
VI_TRI = {"dau_trang", "today", "order", "store", "season", "cuoi_trang", "uu_dai", "tuyen_dung", "tiec"}
# Ba loại có thẻ riêng trong trình biên tập mới, mỗi mục một thẻ trên web.
LOAI_MUC = ("uu_dai", "tuyen_dung", "tiec")
# Trước v586 tối đa 30 khối; nay ưu đãi, tuyển dụng, tiệc cũng là khối nên
# nâng trần. Giới hạn 250 KB của cả bản vẫn giữ.
SO_KHOI_TOI_DA = 80
MAC_DINH = {"khoi": [
    {"id":"tieu-de-hom-nay", "loai":"tieu_de_muc", "hien":True, "vi_tri":"today", "tieu_de":"Bánh\nhôm nay"},
    {"id":"tieu-de-dat-truoc", "loai":"tieu_de_muc", "hien":True, "vi_tri":"order", "tieu_de":"Đặt\nbánh trước"},
    {"id":"tieu-de-tai-quay", "loai":"tieu_de_muc", "hien":True, "vi_tri":"store", "tieu_de":"Bánh trên tủ\ntại quầy"},
    {"id": "loi-chao", "loai": "thong_bao", "hien": False, "vi_tri": "dau_trang",
     "nhan": "THE VAGABOND PÂTISSERIE · SINCE 2015", "tieu_de": "Một chiếc bánh, một khoảnh khắc đáng nhớ.",
     "noi_dung": "", "anh": "", "mo_ta_anh": "", "nut": "", "lien_ket": ""},
    {"id": "cau-chuyen", "loai": "cau_chuyen", "hien": True, "vi_tri": "cuoi_trang",
     "nhan": "TỪ THE VAGABOND PÂTISSERIE", "tieu_de": "Những khoảnh khắc ngọt ngào",
     "noi_dung": "Một chiếc bánh, một dịp gặp nhau. Chọn bánh có sẵn hôm nay hoặc đặt trước cho những ngày đặc biệt.",
     "anh": "", "mo_ta_anh": "", "nut": "Đặt bánh trước", "lien_ket": "#/dat-truoc"}
]}
MAC_DINH["khoi"].extend([
    {"id":"ho-tro", "loai":"thong_bao", "hien":False, "vi_tri":"cuoi_trang", "nhan":"HỖ TRỢ ĐẶT BÁNH", "tieu_de":"Chúng tôi mong được phục vụ cho quý khách", "noi_dung":"Quý khách có thể chọn bánh, ngày nhận và điền lời chúc ngay trên website."},
    {"id":"hoi-lich-nhan", "loai":"hoi_dap", "hien":True, "vi_tri":"cuoi_trang", "tieu_de":"Tôi muốn nhận bánh hôm nay?", "noi_dung":"Quý khách chọn mục Có sẵn hôm nay và một khung giờ còn nhận. Lịch trên website cập nhật theo thời gian chuẩn bị của bếp."},
    {"id":"hoi-xac-nhan", "loai":"hoi_dap", "hien":True, "vi_tri":"cuoi_trang", "tieu_de":"Gửi đơn xong đã thanh toán chưa?", "noi_dung":"Biên nhận xác nhận chúng tôi đã tiếp nhận yêu cầu. Nhân viên sẽ liên hệ xác nhận đơn và hướng dẫn thanh toán."},
    {"id":"hoi-loi-chuc", "loai":"hoi_dap", "hien":True, "vi_tri":"cuoi_trang", "tieu_de":"Tôi có thể gửi lời chúc riêng?", "noi_dung":"Quý khách điền lời chúc trên trang từng bánh trước khi thêm vào giỏ. Mỗi bánh có thể có một lời chúc riêng."},
])


# #436: nguồn link do anh Việt cung cấp, kiểm trên Beacons ngày 06/10/2026.
KENH_MAC_DINH = [
    {"id":"nut-kenh", "loai":"nut_kenh", "hien":True, "vi_tri":"cuoi_trang", "tieu_de":"Mở các kênh đặt hàng", "anh":"/assets/vagabond/web_order/logo-kenh/grab.png"},
    {"id":"kenh-grab", "anh":"/assets/vagabond/web_order/logo-kenh/grab.png", "loai":"kenh_dat_hang", "hien":True, "vi_tri":"cuoi_trang", "tieu_de":"GrabFood", "nut":"Grab", "lien_ket":"https://r.grab.com/g/6-20250920_005603_BAC6857576104ED4BB3FDE35D1BF1115_MEXMPS-5-C4E1NPWGG2WZFA"},
    {"id":"kenh-shopee", "anh":"/assets/vagabond/web_order/logo-kenh/shopeefood.png", "loai":"kenh_dat_hang", "hien":True, "vi_tri":"cuoi_trang", "tieu_de":"ShopeeFood", "nut":"Shopee", "lien_ket":"https://shopeefood.vn/now-food/shop/1228609"},
    {"id":"kenh-be", "anh":"/assets/vagabond/web_order/logo-kenh/be.png", "loai":"kenh_dat_hang", "hien":True, "vi_tri":"cuoi_trang", "tieu_de":"beFood", "nut":"be", "lien_ket":"https://begroup.onelink.me/ZOqn/c2ba8ar9"},
    {"id":"kenh-xanh", "anh":"/assets/vagabond/web_order/logo-kenh/xanh-sm.png", "loai":"kenh_dat_hang", "hien":True, "vi_tri":"cuoi_trang", "tieu_de":"XanhSM", "nut":"Xanh", "lien_ket":"https://xanhsmngon.onelink.me/14WJ/72fp2t58"},
    {"id":"kenh-beacons", "anh":"/assets/vagabond/web_order/logo-kenh/beacons.png", "loai":"kenh_dat_hang", "hien":True, "vi_tri":"cuoi_trang", "tieu_de":"Xem tất cả kênh đặt hàng", "nut":"↗", "lien_ket":"https://beacons.ai/thevagabondpatisserie"},
    {"id":"kenh-zalo", "anh":"/assets/vagabond/web_order/logo-kenh/zalo.png", "loai":"zalo_oa", "hien":True, "vi_tri":"cuoi_trang", "tieu_de":"Nhắn Zalo", "lien_ket":"https://zalo.me/thevagabondsaigon"},
]
MAC_DINH["khoi"].extend(KENH_MAC_DINH)


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
                         "mac_dinh": "Hôm nay đã hết khung giờ nhận. Quý khách vui lòng chọn ngày mai."},
    "dat_ban_nhan": {"ten": "Đặt bàn: dòng nhỏ trên tiêu đề", "mac_dinh": "HẸN MỘT BUỔI THONG THẢ"},
    "dat_ban_tieu_de": {"ten": "Đặt bàn: tiêu đề", "mac_dinh": "Đặt bàn tại Vagabond."},
    "dat_ban_mo_ta": {"ten": "Đặt bàn: đoạn mô tả",
                      "mac_dinh": "Chọn ngày, giờ và số người. Chúng tôi sẽ liên hệ xác nhận chỗ; gửi yêu cầu chưa đồng nghĩa đã giữ được bàn."},
    "dat_ban_dong": {"ten": "Đặt bàn: câu hiện khi tiệm chưa mở nhận đặt bàn online",
                     "mac_dinh": "Chúng tôi chưa mở nhận đặt bàn online. Gọi 0931 224 334 để được hỗ trợ."},
    "dat_ban_nut": {"ten": "Đặt bàn: chữ trên nút gửi", "mac_dinh": "Gửi yêu cầu đặt bàn"},
    "dat_ban_ho_tro": {"ten": "Đặt bàn: câu trước số điện thoại hỗ trợ", "mac_dinh": "Cần hỗ trợ ngay?"},
}
DAI_NHAN = 300
# Danh mục dùng chung với bản mặc định của web. Khóa ổn định qua các lần
# sửa chữ để lịch sử đã xuất bản không mất liên kết với chỗ đang hiển thị.
with (Path(__file__).parent / "public/web_order/chu-mac-dinh.json").open(encoding="utf-8") as _tep_chu:
    NHAN.update(json.load(_tep_chu))
RE_CHO_DIEN = re.compile(r"\{[a-z_]+\}")


def cho_dien(chu):
    """Các chỗ máy điền dạng {so}, {khung} trong một câu. THUẦN."""
    return sorted(set(RE_CHO_DIEN.findall(str(chu or ""))))


def _chuan_hoa_nhan(nhan):
    if not isinstance(nhan, dict) or set(nhan) - set(NHAN):
        raise ValueError("Nhãn không có trong danh sách cho phép. Tải lại trang biên tập.")
    for khoa, chu in nhan.items():
        gioi_han = 4000 if NHAN[khoa].get("nhieu_dong") else DAI_NHAN
        if not isinstance(chu, str) or len(chu) > gioi_han:
            raise ValueError("Nhãn %s quá dài hoặc không hợp lệ (tối đa %d ký tự)." % (NHAN[khoa]["ten"], gioi_han))
        if "\n" in chu and not (khoa.startswith("dat_ban_") or NHAN[khoa].get("nhieu_dong")):
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


RE_GIO = re.compile(r"(?:[01][0-9]|2[0-3]):[0-5][0-9]")
RE_EMAIL = re.compile(r"[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def _so(v, ten, toi_da=12):
    """Ô số lưu dạng chuỗi chữ số. Trống là không đặt."""
    if v and not re.fullmatch(r"[0-9]{1,%d}" % toi_da, v):
        raise ValueError("%s chỉ gõ chữ số, không dấu chấm hay chữ đ." % ten)


def _kiem_truong_586(k):
    """Kiểm các trường thêm ở v586. THUẦN."""
    from datetime import date
    _so(k.get("don_toi_thieu", ""), "Đơn tối thiểu")
    _so(k.get("gia_ve", ""), "Giá vé")
    _so(k.get("so_ve", ""), "Số vé", 5)
    if k.get("so_ve") and int(k["so_ve"]) < 1:
        raise ValueError("Số vé phải từ 1 trở lên, để trống là không giới hạn.")
    g1, g2 = k.get("gio_bat_dau", ""), k.get("gio_ket_thuc", "")
    for g in (g1, g2):
        if g and not RE_GIO.fullmatch(g):
            raise ValueError("Giờ gõ dạng 07:00 hoặc 21:30.")
    if bool(g1) != bool(g2):
        raise ValueError("Điền cả hai ô giờ, hoặc bỏ trống cả hai để áp dụng cả ngày.")
    if g1 and g2 and g1 >= g2:
        raise ValueError("Giờ kết thúc phải sau giờ bắt đầu.")
    if k.get("han_ban"):
        try:
            date.fromisoformat(k["han_ban"])
        except ValueError:
            raise ValueError("Hạn đăng ký không hợp lệ.")
        if k.get("bat_dau") and k["han_ban"] > k["bat_dau"]:
            raise ValueError("Hạn đăng ký không được sau ngày diễn ra tiệc.")


# v586: cửa hàng và điểm nhận bánh, MỘT nguồn cho mọi chỗ trên web (anh Việt
# chốt 07/10/2026). Mặc định PHẢI trùng chữ đang gõ cứng trong trang, để
# deploy xong khách thấy y nguyên cho tới khi marketing sửa.
# Hai điểm nhận bánh giữ ĐÚNG thứ tự cũ (Bếp trước, Cửa hàng sau): giỏ hàng
# khách lưu trong trình duyệt nhớ điểm nhận theo số thứ tự.
# Liên hệ (điện thoại, email, mạng xã hội) KHÔNG nằm ở đây: nguồn của nó đã
# có từ #367 là các ô web_* của Vagabond Settings (don_web.lien_he), chân
# trang và biên nhận đang đọc ở đó. Thẻ Liên hệ ghi thẳng vào các ô đó.
TRUONG_CUA_HANG = {"id", "ten", "dia_chi", "gio_mo_cua", "hotline", "chi_duong", "loai", "nhan_banh", "hien"}
THONG_TIN_MAC_DINH = {
    "cua_hang": [
        {"id": "bep-tan-son-hoa", "ten": "Bếp Tân Sơn Hoà", "dia_chi": "307/1 Nguyễn Văn Trỗi, P. Tân Sơn Hoà",
         "gio_mo_cua": "", "hotline": "", "chi_duong": "", "loai": "bep", "nhan_banh": True, "hien": False},
        {"id": "cua-hang-sai-gon", "ten": "Cửa hàng Sài Gòn", "dia_chi": "9 Trần Cao Vân, P. Sài Gòn",
         "gio_mo_cua": "", "hotline": "", "chi_duong": "", "loai": "cua_hang", "nhan_banh": True, "hien": True},
        {"id": "nha-van-hoa-thanh-nien", "ten": "Nhà Văn Hóa Thanh Niên", "dia_chi": "21 Phạm Ngọc Thạch, Quận 3",
         "gio_mo_cua": "", "hotline": "", "chi_duong": "", "loai": "cua_hang", "nhan_banh": False, "hien": False},
    ],
}
TRUONG_LIEN_HE = ("dien_thoai", "email", "zalo", "messenger", "facebook", "instagram", "tiktok")
# Ô Settings tương ứng, viết đủ tên để bộ kiểm ô cài đặt đọc được.
O_LIEN_HE = {"dien_thoai": "web_dien_thoai", "email": "web_email", "zalo": "web_zalo", "messenger": "web_messenger",
             "facebook": "web_facebook", "instagram": "web_instagram", "tiktok": "web_tiktok"}
TEN_LIEN_HE = {"dien_thoai": "Số điện thoại", "email": "Email", "zalo": "Zalo", "messenger": "Messenger",
               "facebook": "Facebook", "instagram": "Instagram", "tiktok": "TikTok"}


def chu_so_dien_thoai(sdt):
    """Số điện thoại chỉ còn chữ số, để làm đường dẫn tel:. THUẦN."""
    return re.sub(r"[^0-9+]", "", str(sdt or ""))


def _https(v, ten):
    if not v:
        return
    u = urlsplit(v)
    if any(ord(c) < 33 for c in v) or "\\" in v or u.scheme != "https" or not u.hostname or u.username or u.password:
        raise ValueError("%s phải là liên kết bắt đầu bằng https://." % ten)


def kiem_lien_he(lh):
    """Kiểm thẻ Liên hệ trước khi ghi vào Settings. THUẦN. Trả bản đã gọt."""
    if not isinstance(lh, dict) or set(lh) - set(TRUONG_LIEN_HE):
        raise ValueError("Thẻ Liên hệ có ô không được hỗ trợ. Tải lại trang.")
    ra = {}
    for k in TRUONG_LIEN_HE:
        v = lh.get(k, "")
        if not isinstance(v, str) or len(v) > 300:
            raise ValueError("%s quá dài hoặc không hợp lệ." % TEN_LIEN_HE[k])
        ra[k] = v.strip()
    if ra["dien_thoai"] and not re.fullmatch(r"\+?[0-9]{8,12}", chu_so_dien_thoai(ra["dien_thoai"])):
        raise ValueError("Số điện thoại chỉ gồm 8 đến 12 chữ số, ví dụ 0931 224 334 hoặc 1900 1234.")
    if ra["email"] and not RE_EMAIL.fullmatch(ra["email"]):
        raise ValueError("Email không hợp lệ, ví dụ hello@thevagabondpatisserie.com.")
    for k in ("zalo", "messenger", "facebook", "instagram", "tiktok"):
        _https(ra[k], TEN_LIEN_HE[k])
    return ra


def _chuan_hoa_thong_tin(tt):
    if not isinstance(tt, dict) or set(tt) - {"cua_hang"}:
        raise ValueError("Thông tin website chỉ gồm danh sách cửa hàng.")
    ch = tt.get("cua_hang", [])
    if not isinstance(ch, list) or len(ch) > 12:
        raise ValueError("Tối đa 12 cửa hàng và điểm nhận bánh.")
    da_co = set()
    for c in ch:
        if not isinstance(c, dict) or set(c) - TRUONG_CUA_HANG:
            raise ValueError("Cửa hàng có ô không được hỗ trợ.")
        if not re.fullmatch(r"[a-z0-9-]{1,60}", str(c.get("id", ""))) or c["id"] in da_co:
            raise ValueError("Mã cửa hàng bị trùng hoặc không hợp lệ. Tải lại trang.")
        da_co.add(c["id"])
        for k in ("hien", "nhan_banh"):
            if type(c.get(k, False)) is not bool:
                raise ValueError("Chọn bật hoặc tắt cho từng cửa hàng.")
        for k in TRUONG_CUA_HANG - {"hien", "nhan_banh"}:
            v = c.get(k, "")
            if not isinstance(v, str) or len(v) > 300:
                raise ValueError("Chữ của cửa hàng quá dài hoặc không hợp lệ.")
        if c.get("loai", "cua_hang") not in ("cua_hang", "bep"):
            raise ValueError("Chọn loại: cửa hàng hay bếp.")
        if not c.get("ten", "").strip():
            raise ValueError("Cửa hàng cần có tên.")
        if (c.get("hien") or c.get("nhan_banh")) and not c.get("dia_chi", "").strip():
            raise ValueError("%s cần địa chỉ trước khi hiện trên web hoặc nhận bánh." % c["ten"])
        if c.get("hotline") and not re.fullmatch(r"\+?[0-9]{8,12}", chu_so_dien_thoai(c["hotline"])):
            raise ValueError("Hotline của %s chỉ gồm 8 đến 12 chữ số." % c["ten"])
        _https(c.get("chi_duong", ""), "Chỉ đường của " + c["ten"])


def thong_tin_day_du(du_lieu):
    """Danh sách cửa hàng để trang dùng: bản đã sửa, chưa từng sửa thì lấy
    mặc định. THUẦN, là NGUỒN DUY NHẤT ghép với mặc định."""
    tt = (du_lieu or {}).get("thong_tin") or {}
    ch = tt["cua_hang"] if isinstance(tt.get("cua_hang"), list) else THONG_TIN_MAC_DINH["cua_hang"]
    return {"cua_hang": copy.deepcopy(ch)}


def diem_nhan(du_lieu):
    """Điểm nhận bánh khách được chọn ở bước Tự lấy: cửa hàng bật "Nhận bánh
    tại đây" và có địa chỉ. THUẦN, máy chủ và trang khách cùng theo một luật.
    Danh sách rỗng là marketing đã tắt hết, KHÔNG quay về điểm cũ (Codex #453).
    Mỗi điểm mang mã cửa hàng (duy nhất, kiểm ở _chuan_hoa_thong_tin): trang và
    máy chủ nhận diện điểm bằng mã, không bằng tên hay vị trí."""
    return [{"id": str(c.get("id") or ""), "n": str(c.get("ten") or "").strip(), "a": str(c.get("dia_chi") or "").strip()}
            for c in thong_tin_day_du(du_lieu)["cua_hang"]
            if isinstance(c, dict) and c.get("nhan_banh") and str(c.get("dia_chi") or "").strip()
            and str(c.get("ten") or "").strip() and str(c.get("id") or "")]


def chuan_hoa(du_lieu):
    """Giới hạn kích thước và cấu trúc trước khi lưu, dùng cả ở Document.save."""
    if isinstance(du_lieu, str):
        if len(du_lieu) > 250000:
            raise ValueError("Nội dung quá dài. Giảm số khối hoặc độ dài bài viết.")
        du_lieu = json.loads(du_lieu)
    if not isinstance(du_lieu, dict) or "khoi" not in du_lieu or set(du_lieu) - {"khoi", "chinh_sach", "nhan", "san_pham", "thong_tin"}:
        raise ValueError("Nội dung phải có danh sách khối.")
    if "thong_tin" in du_lieu:
        _chuan_hoa_thong_tin(du_lieu["thong_tin"])
    if "chinh_sach" in du_lieu:
        _chuan_hoa_chinh_sach(du_lieu["chinh_sach"])
    if "nhan" in du_lieu:
        _chuan_hoa_nhan(du_lieu["nhan"])
    san_pham = du_lieu.get("san_pham", {})
    if not isinstance(san_pham, dict) or len(san_pham) > 500:
        raise ValueError("Tối đa 500 mã sản phẩm có nội dung riêng.")
    for ma, chu in san_pham.items():
        if ma in {"__proto__", "constructor", "prototype"} or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", ma) or not isinstance(chu, dict) or set(chu) - {"ten", "mo_ta", "tang", "theo_mua", "khau_phan"}:
            raise ValueError("Nội dung sản phẩm không hợp lệ. Tải lại danh mục.")
        if any(not isinstance(v, str) or len(v) > 4000 for v in chu.values()):
            raise ValueError("Mỗi ô nội dung sản phẩm tối đa 4.000 ký tự.")
    ds = du_lieu["khoi"]
    if not isinstance(ds, list) or len(ds) > SO_KHOI_TOI_DA:
        raise ValueError("Mỗi trang có tối đa %d mục và khối. Xoá bớt ưu đãi hay vị trí đã hết hạn." % SO_KHOI_TOI_DA)
    da_co = set()
    tieu_de_da_co = set()
    zalo_da_co = False
    nut_kenh_da_co = False
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
        if k['loai'] not in LOAI_MUC and k.get('vi_tri') in LOAI_MUC:
            raise ValueError('Khối nội dung thường cần chọn vị trí trên trang bán hàng.')
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
            if not isinstance(v, str) or len(v) > (4000 if ten in ("noi_dung", "yeu_cau") else 1000):
                raise ValueError("Chữ trong khối quá dài hoặc không hợp lệ: " + ten)
        _kiem_truong_586(k)
        if k['loai'] == 'nut_kenh':
            if nut_kenh_da_co:
                raise ValueError('Chỉ dùng một nút mở kênh đặt hàng. Sửa nút đã có.')
            nut_kenh_da_co = True
            if k['hien'] and not k.get('tieu_de', '').strip():
                raise ValueError('Điền tên trợ năng cho nút mở kênh đặt hàng.')
        if k['loai'] == 'zalo_oa' and k['hien']:
            if zalo_da_co:
                raise ValueError('Chỉ bật một nút Zalo OA trên website.')
            zalo_da_co = True
        if k['loai'] in ('kenh_dat_hang', 'zalo_oa'):
            u = urlsplit(k.get('lien_ket', ''))
            if k['hien'] and (not k.get('tieu_de', '').strip() or u.scheme != 'https' or not u.hostname):
                raise ValueError('Nút nổi cần tên và liên kết HTTPS trước khi bật.')
            if k['loai'] == 'zalo_oa' and k.get('lien_ket') and (u.hostname != 'zalo.me' or not re.fullmatch(r'/(?:[0-9]{15,25}|[A-Za-z][A-Za-z0-9._-]{2,59})/?', u.path)):
                raise ValueError('Dùng đường dẫn Zalo OA dạng https://zalo.me/tên-OA hoặc mã OA, không dùng số điện thoại cá nhân.')
        if k['loai'] in LOAI_MUC:
            if not k.get('tieu_de', '').strip():
                raise ValueError('Ưu đãi, tiệc và vị trí tuyển dụng cần có tên.')
            from datetime import date
            for ten in ('bat_dau', 'ket_thuc'):
                if k.get(ten):
                    try: date.fromisoformat(k[ten])
                    except ValueError: raise ValueError('Ngày bắt đầu/kết thúc không hợp lệ.')
            if k.get('bat_dau') and k.get('ket_thuc') and k['bat_dau'] > k['ket_thuc']:
                raise ValueError('Ngày kết thúc không được trước ngày bắt đầu.')
            if k.get('email') and not re.fullmatch(r'[A-Za-z0-9_.+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', k['email']):
                raise ValueError('Email nhận hồ sơ không hợp lệ.')
            if k['loai'] == 'tuyen_dung' and k['hien'] and not (k.get('email') or k.get('lien_ket')):
                raise ValueError('Điền email hoặc liên kết ứng tuyển trước khi bật vị trí.')
            if k['loai'] == 'tiec' and k['hien'] and not k.get('bat_dau'):
                raise ValueError('Chọn ngày diễn ra tiệc trước khi bật hiện trên web.')
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


class XungDot(ValueError):
    """Người khác vừa sửa đúng mục này sau lúc mình mở ra."""


def dau_van_tay(x):
    """Dấu ngắn của một mục để biết mục có bị ai sửa trong lúc mình đang sửa
    không. THUẦN. None (mục chưa có) cho dấu rỗng."""
    import hashlib
    if x is None:
        return ""
    return hashlib.sha1(json.dumps(x, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _vi_tri_muc(nd, id_muc):
    for i, k in enumerate(nd.get("khoi") or []):
        if k.get("id") == id_muc:
            return i
    return -1


def ap_muc(nd, muc, dau_cu=None):
    """Đặt MỘT mục ưu đãi, tuyển dụng hoặc tiệc vào bản nội dung. THUẦN.

    Trình biên tập mới lưu từng mục và khách thấy ngay (v586). Không lưu cả
    bản như trình cũ nên không cuốn theo phần nháp người khác chưa xuất bản.
    dau_cu: dấu của mục lúc mình mở ra ("" là mục mới). None là không soát,
    dùng cho bản nháp vì nháp có thể đang khác bản công khai.
    Mục mới chèn lên ĐẦU nhóm cùng loại: ưu đãi vừa tạo phải đứng trên cùng.
    """
    if not isinstance(muc, dict) or muc.get("loai") not in LOAI_MUC:
        raise ValueError("Chỉ lưu được ưu đãi, tiệc và vị trí tuyển dụng ở đây.")
    nd = copy.deepcopy(nd)
    ds = nd.setdefault("khoi", [])
    muc = dict(muc, vi_tri=muc["loai"])
    i = _vi_tri_muc(nd, muc.get("id"))
    cu = ds[i] if i >= 0 else None
    if dau_cu is not None and dau_van_tay(cu) != dau_cu:
        raise XungDot("Có người vừa sửa hoặc xoá mục này. Tải lại để xem bản mới rồi sửa tiếp.")
    if cu is not None:
        if cu.get("loai") != muc["loai"]:
            raise ValueError("Mã mục đã dùng cho loại khác. Tải lại trang.")
        ds[i] = muc
    else:
        dau = next((j for j, k in enumerate(ds) if k.get("loai") == muc["loai"]), len(ds))
        ds.insert(dau, muc)
    return nd


def xoa_muc(nd, id_muc, dau_cu=None):
    """Bỏ một mục ra khỏi bản nội dung. THUẦN. Mục đã không còn thì thôi."""
    nd = copy.deepcopy(nd)
    i = _vi_tri_muc(nd, id_muc)
    cu = nd["khoi"][i] if i >= 0 else None
    if dau_cu is not None and dau_van_tay(cu) != dau_cu:
        raise XungDot("Có người vừa sửa mục này. Tải lại để xem bản mới trước khi xoá.")
    if cu is not None:
        if cu.get("loai") not in LOAI_MUC:
            raise ValueError("Khối này chỉ xoá ở mục Nâng cao.")
        del nd["khoi"][i]
    return nd


def ap_thong_tin(nd, phan, gia_tri, dau_cu=None):
    """Thay một phần (lien_he hoặc cua_hang) của thông tin website. THUẦN."""
    if phan != "cua_hang":
        raise ValueError("Chỉ sửa được danh sách cửa hàng ở đây.")
    nd = copy.deepcopy(nd)
    hien_tai = thong_tin_day_du(nd)
    if dau_cu is not None and dau_van_tay(hien_tai[phan]) != dau_cu:
        raise XungDot("Có người vừa sửa phần này. Tải lại để xem bản mới rồi sửa tiếp.")
    hien_tai[phan] = gia_tri
    nd["thong_tin"] = hien_tai
    return nd


def ap_nhan(nd, thay, soat=True):
    """Đổi một số nhãn chữ. thay = {khoá: [chữ lúc mở, chữ mới]}. THUẦN.

    Chữ mới để trống là quay về chữ mặc định. Soát từng khoá: ai vừa đổi
    đúng khoá đó thì báo, khoá khác không ảnh hưởng.
    """
    if not isinstance(thay, dict) or not thay or set(thay) - set(NHAN):
        raise ValueError("Nhãn không có trong danh sách cho phép. Tải lại trang biên tập.")
    nd = copy.deepcopy(nd)
    nhan = dict(nd.get("nhan") or {})
    for khoa, cap in thay.items():
        if not isinstance(cap, (list, tuple)) or len(cap) != 2 or not all(isinstance(x, str) for x in cap):
            raise ValueError("Dữ liệu nhãn không hợp lệ. Tải lại trang biên tập.")
        cu, moi = cap
        if soat and (nhan.get(khoa) or "") != cu:
            raise XungDot("Có người vừa sửa câu \"%s\". Tải lại để xem bản mới." % NHAN[khoa]["ten"])
        if moi.strip():
            nhan[khoa] = moi
        else:
            nhan.pop(khoa, None)
    nd["nhan"] = nhan
    return nd


def trang_thai_muc(muc, hom_nay):
    """Nhãn trạng thái của một mục trên danh sách biên tập. THUẦN.

    hom_nay: chuỗi YYYY-MM-DD theo giờ Việt Nam. Trả (mã, chữ) để màn tô màu.
    Trang khách cũng ẩn mục đã hết hạn theo đúng mốc này (chuyen-muc.js).
    """
    loai = muc.get("loai")
    bd, kt = muc.get("bat_dau") or "", muc.get("ket_thuc") or ""
    if loai == "tiec":
        if bd and bd < hom_nay:
            return ("het", "Đã diễn ra")
        han = muc.get("han_ban") or bd
        if han and han < hom_nay:
            return ("het", "Hết hạn đăng ký")
        return ("dang", "Đang mở đăng ký")
    if kt and kt < hom_nay:
        return ("het", "Đã kết thúc" if loai == "uu_dai" else "Hết hạn nhận hồ sơ")
    if loai == "uu_dai" and bd and bd > hom_nay:
        return ("sap", "Sắp diễn ra")
    return ("dang", "Đang diễn ra" if loai == "uu_dai" else "Đang tuyển")


import frappe

TEN = "order"
DOCTYPE = "Vagabond Noi Dung Web"


def kiem_quyen():
    if frappe.session.user == "Guest" or not ({"Marketing", "System Manager"} & set(frappe.get_roles())):
        frappe.throw("Bạn cần quyền Marketing để chỉnh nội dung website.", frappe.PermissionError)


def _doc():
    return frappe.get_doc(DOCTYPE, TEN)


def _ban_cong_khai(khoa=False):
    """Bản công khai. khoa=True vừa khoá hàng nội dung web vừa đọc HIỆN TẠI
    (for update): bên ghi cần xếp hàng với Marketing phải đọc đúng bản sau
    khoá, đọc thường trong REPEATABLE READ có thể trả ảnh chụp từ trước lúc
    chờ (Codex #454)."""
    if khoa:
        hang = frappe.db.sql("select ban_cong_khai from `tabVagabond Noi Dung Web` where name=%s for update", (TEN,))
        if not hang:
            return copy.deepcopy(MAC_DINH)
        return json.loads(hang[0][0] or json.dumps(MAC_DINH))
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
    # v589 (anh Việt 09/10/2026): ưu đãi lấy từ ERP, nguồn duy nhất. Ưu đãi gõ
    # tay cũ vẫn nằm trong dữ liệu (khôi phục được) nhưng không ra trang khách.
    ra["khoi"] = thay_uu_dai_erp(ra.get("khoi") or [], _the_uu_dai_erp())
    # v532: trang luôn nhận bộ nhãn đầy đủ, không tự ghép mặc định ở phía khách.
    ra["nhan"] = nhan_day_du(ra)
    # v586: cửa hàng, liên hệ và số vé tiệc đã đăng ký, cùng một lượt tải.
    # Liên hệ đọc từ nguồn #367 (Settings) để mọi trang thay đúng số gọi.
    from vagabond.don_web import lien_he
    ra["thong_tin"] = thong_tin_day_du(ra)
    ra["diem_nhan"] = diem_nhan(ra)
    ra["lien_he"] = lien_he()
    ra["ve"] = _dem_ve(ra)
    return ra


def thay_uu_dai_erp(khoi, the_erp):
    """THUẦN. Bỏ mọi khối ưu đãi gõ tay, chèn thẻ ưu đãi từ ERP vào đúng chỗ
    khối ưu đãi đầu tiên từng đứng (không có thì nối cuối)."""
    vi_tri = next((i for i, k in enumerate(khoi) if k.get("loai") == "uu_dai"), None)
    con = [k for k in khoi if k.get("loai") != "uu_dai"]
    if vi_tri is None:
        return con + list(the_erp)
    truoc = sum(1 for k in khoi[:vi_tri] if k.get("loai") != "uu_dai")
    return con[:truoc] + list(the_erp) + con[truoc:]


def giu_uu_dai_da_luu(khoi_moi, khoi_cu):
    """THUẦN. Codex #460: ưu đãi nay chỉ đọc từ ERP, nên khi lưu cả bản (mục
    Nâng cao) bỏ mọi khối ưu đãi gửi lên và đặt lại đúng các khối ưu đãi đã
    lưu. Chỗ đặt: chỗ khối ưu đãi đầu tiên trong bản gửi lên, không có thì
    theo chỗ cũ (tính bằng số khối khác đứng trước)."""
    cu_uu = [k for k in khoi_cu if k.get("loai") == "uu_dai"]
    con = [k for k in khoi_moi if k.get("loai") != "uu_dai"]
    if not cu_uu:
        return con
    nguon = khoi_moi if any(k.get("loai") == "uu_dai" for k in khoi_moi) else khoi_cu
    vi_tri = next(i for i, k in enumerate(nguon) if k.get("loai") == "uu_dai")
    truoc = sum(1 for k in nguon[:vi_tri] if k.get("loai") != "uu_dai")
    return con[:truoc] + copy.deepcopy(cu_uu) + con[truoc:]


def _the_uu_dai_erp():
    try:
        from vagabond import khuyen_mai
        return khuyen_mai.the_web_dang_hien(_hom_nay_vn())
    except Exception:
        frappe.log_error(title="Vagabond: ưu đãi web từ ERP", message=frappe.get_traceback())
        return []


def _hom_nay_vn():
    from frappe.utils import nowdate
    return nowdate()


def nhan_cong_khai():
    """Bộ nhãn đã xuất bản cho các trang dựng ở máy chủ (đặt bàn)."""
    return nhan_day_du(_ban_cong_khai())


def chinh_sach_dang_hien():
    """Danh sách trang chính sách đã xuất bản và bật hiện, cho chân trang."""
    nd = _ban_cong_khai()
    cs = nd.get("chinh_sach") or {}
    nhan = nhan_day_du(nd)
    return [
        {"khoa": k, "ten": nhan.get(k + "_ten", CHINH_SACH[k]["ten"]), "duong": CHINH_SACH[k]["duong"]}
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
        "ten": nhan_cong_khai().get(khoa + "_ten", CHINH_SACH[khoa]["ten"]),
        "html": sanitize_html(md_to_html(md) or "", always_sanitize=True),
        "co_en": bool(str(v.get("en") or "").strip()),
        "ngon_ngu": "en" if md is v.get("en") and ngon_ngu == "en" else "vn",
    }



def noi_dung_da_duyet_367(nd):
    """Chuyển đúng câu mặc định cũ, thêm hỗ trợ đã duyệt. Không xuất bản nháp."""
    nd = copy.deepcopy(nd)
    cu = {
        "cau_chuan_bi_het": "Hôm nay đã hết khung giờ nhận. Anh chị đặt cho ngày mai giúp em nhé.",
        "dat_ban_tieu_de": "Đặt bàn tại tiệm.",
        "dat_ban_mo_ta": "Chọn ngày, giờ và số người. Tiệm sẽ liên hệ xác nhận chỗ; gửi yêu cầu chưa đồng nghĩa đã giữ được bàn.",
        "dat_ban_dong": "Tiệm chưa mở nhận đặt bàn online. Gọi 0931 224 334 để được hỗ trợ.",
    }
    nhan = nd.get("nhan") or {}
    for k, chu_cu in cu.items():
        if nhan.get(k) == chu_cu:
            nhan[k] = NHAN[k]["mac_dinh"]
    for k in nd["khoi"]:
        if k.get("nhan") == "TỪ TIỆM BÁNH":
            k["nhan"] = "TỪ THE VAGABOND PÂTISSERIE"
        if k.get("tieu_de") == "Mình giúp gì cho bạn hôm nay?":
            k["tieu_de"] = "Chúng tôi mong được phục vụ cho quý khách"
    da_co = {k["id"] for k in nd["khoi"]}
    for k in MAC_DINH["khoi"]:
        if k["id"] in {"ho-tro", "hoi-lich-nhan", "hoi-xac-nhan", "hoi-loi-chuc"} and k["id"] not in da_co and len(nd["khoi"]) < 30:
            nd["khoi"].append(copy.deepcopy(k))
    return chuan_hoa(nd)


def xuat_ban_chu_da_duyet_367(bien_doi=noi_dung_da_duyet_367):
    """Patch một lần: nháp và công khai chuyển riêng, giữ lịch sử công khai."""
    if not frappe.db.exists(DOCTYPE, TEN):
        return False  # cong_khai/doc_bang dùng MAC_DINH đã cập nhật.
    frappe.db.sql("select name from `tabVagabond Noi Dung Web` where name=%s for update", (TEN,))
    d = _doc()
    nhap_cu = json.loads(d.ban_nhap)
    cong_khai_cu = json.loads(d.ban_cong_khai)
    nhap = bien_doi(nhap_cu)
    cong_khai = bien_doi(cong_khai_cu)
    if nhap == nhap_cu and cong_khai == cong_khai_cu:
        return False
    if cong_khai != cong_khai_cu:
        ls = json.loads(d.lich_su or "[]")
        ls.insert(0, {"phien_ban": int(d.phien_ban or 0), "luc": str(frappe.utils.now()),
                      "nguoi": frappe.session.user, "noi_dung": cong_khai_cu})
        d.lich_su = json.dumps(ls[:20], ensure_ascii=False)
    d.ban_nhap = json.dumps(nhap, ensure_ascii=False)
    d.ban_cong_khai = json.dumps(cong_khai, ensure_ascii=False)
    d.flags.luu_noi_dung_web = True
    d.save(ignore_permissions=True)
    return True


def rut_gon_va_kenh_436(nd):
    """Ẩn hai khối anh Việt chỉ ra, giữ chữ để phục hồi; nháp không tràn sang công khai."""
    nd = copy.deepcopy(nd)
    for k in nd['khoi']:
        if k.get('id') in ('loi-chao', 'ho-tro'):
            k['hien'] = False
        if k.get('loai') not in ('uu_dai', 'tuyen_dung') and k.get('vi_tri') in ('uu_dai', 'tuyen_dung'):
            k['vi_tri'] = 'cuoi_trang'
    ids = {k['id'] for k in nd['khoi']}
    for k in KENH_MAC_DINH:
        if k['id'] not in ids and len(nd['khoi']) < 30:
            nd['khoi'].append(copy.deepcopy(k))
    return chuan_hoa(nd)


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
                "nhan_mau": copy.deepcopy(NHAN), "so_khoi_toi_da": SO_KHOI_TOI_DA}
    d = _doc()
    # Codex #454: bảng Nâng cao nhận trần số khối từ đây, không tự chép số.
    return {"nhap": json.loads(d.ban_nhap), "cong_khai": json.loads(d.ban_cong_khai),
            "phien_ban": d.phien_ban, "lich_su": json.loads(d.lich_su or "[]"), "nguoi_sua": d.modified_by, "luc_sua": d.modified,
            "nhan_mau": copy.deepcopy(NHAN), "so_khoi_toi_da": SO_KHOI_TOI_DA}


def _uu_dai_erp_bien_tap():
    """v589: thẻ Ưu đãi của trình biên tập chỉ đọc, lấy từ ERP."""
    try:
        from vagabond import khuyen_mai
        return khuyen_mai.ds_web_bien_tap(_hom_nay_vn())
    except Exception:
        frappe.log_error(title="Vagabond: ưu đãi web cho biên tập", message=frappe.get_traceback())
        return []


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
    # Codex #460: ưu đãi chỉ tạo, sửa, bật tắt trên ERP. Lưu cả bản cũng không
    # thêm, sửa, xoá được khối ưu đãi gõ tay; giữ nguyên khối đã lưu.
    nd["khoi"] = giu_uu_dai_da_luu(nd.get("khoi") or [], json.loads(d.ban_nhap or "{}").get("khoi") or [])
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


# ------------------------------------------------ trình biên tập theo thẻ (v586)
#
# Minh Vũ đề xuất 07/10/2026: bảng theo khối khó dùng, người soạn phải hiểu
# "loại khối", "vị trí". Trình mới chia theo VIỆC (Ưu đãi, Tiệc, Tuyển dụng,
# Cửa hàng, Trang và chữ, Liên hệ). Mỗi lần Lưu là khách thấy ngay, đúng câu
# trên màn hình "Lưu xong khách thấy ngay": ghi CÙNG LÚC vào bản công khai
# và bản nháp, chỉ phần vừa sửa, không cuốn theo nháp chưa xuất bản của
# trình cũ (mục Nâng cao).


def _nhom_nhan():
    """Tên dễ đọc cho từng nhóm nhãn, theo trang khách nhìn thấy."""
    return {
        "": "Thanh chọn và đầu trang", "dat_banh": "Trang đặt bánh", "gio_hang": "Giỏ hàng và thanh toán",
        "san_pham": "Trang từng bánh", "dat_ban": "Trang đặt bàn", "thanh_vien": "Trang thành viên",
        "bien_nhan": "Biên nhận sau khi đặt", "chinh_sach": "Chân trang và chính sách",
        "Ưu đãi, tuyển dụng và đặt bánh": "Ưu đãi, tiệc và tuyển dụng", "Kênh đặt hàng": "Kênh đặt hàng",
        "uu_dai": "Ưu đãi, tiệc và tuyển dụng",
    }


def _dem_ve(cong):
    ids = [k["id"] for k in cong.get("khoi") or [] if k.get("loai") == "tiec"]
    if not ids:
        return {}
    try:
        from vagabond.tiec_web import dem_ve
        return dem_ve(ids)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "Biên tập web: không đếm được vé tiệc")
        return {}


@frappe.whitelist()
def bang_moi():
    """Dữ liệu cho trình biên tập theo thẻ: bản KHÁCH ĐANG THẤY."""
    kiem_quyen()
    from vagabond.don_web import PHAP_NHAN
    if frappe.db.exists(DOCTYPE, TEN):
        d = _doc()
        cong, nhap, pb = json.loads(d.ban_cong_khai), json.loads(d.ban_nhap), d.phien_ban
    else:
        cong, nhap, pb = copy.deepcopy(MAC_DINH), copy.deepcopy(MAC_DINH), 0
    return {
        "khoi": [k for k in cong.get("khoi") or [] if k.get("loai") in LOAI_MUC],
        "dau": {k["id"]: dau_van_tay(k) for k in cong.get("khoi") or [] if k.get("loai") in LOAI_MUC},
        "thong_tin": thong_tin_day_du(cong),
        "dau_thong_tin": {p: dau_van_tay(v) for p, v in thong_tin_day_du(cong).items()},
        "lien_he": _lien_he_tho(),
        "dau_lien_he": dau_van_tay(_lien_he_tho()),
        "nhan": cong.get("nhan") or {},
        "nhan_mau": copy.deepcopy(NHAN),
        "nhom_nhan": _nhom_nhan(),
        "ve": _dem_ve(cong),
        "hom_nay": str(frappe.utils.nowdate()),
        "phap_nhan": PHAP_NHAN,
        "nhap_chua_xuat_ban": 1 if nhap != cong else 0,
        "phien_ban": pb,
        # v589: thẻ Ưu đãi chỉ đọc, lấy từ ERP (nguồn duy nhất).
        "uu_dai_erp": _uu_dai_erp_bien_tap(),
    }


def _ghi_ca_hai(ham, ham_nhap=None):
    """Áp một thay đổi vào bản công khai (có soát) và bản nháp (không soát).

    Khoá hàng như `luu`, giữ bản công khai cũ vào lịch sử để còn khôi phục.
    """
    hang = frappe.db.sql("select name from `tabVagabond Noi Dung Web` where name=%s for update", (TEN,))
    if hang:
        d = _doc()
        cong, nhap = json.loads(d.ban_cong_khai), json.loads(d.ban_nhap)
    else:
        d = frappe.new_doc(DOCTYPE)
        d.name = TEN
        d.lich_su = "[]"
        cong, nhap = copy.deepcopy(MAC_DINH), copy.deepcopy(MAC_DINH)
    try:
        cong_moi = chuan_hoa(ham(cong))
        nhap_moi = chuan_hoa((ham_nhap or ham)(nhap))
    except XungDot as e:
        frappe.throw(str(e), title="Có người vừa sửa")
    except (ValueError, TypeError) as e:
        frappe.throw(str(e))
    if hang:
        ls = json.loads(d.lich_su or "[]")
        ls.insert(0, {"phien_ban": int(d.phien_ban or 0), "luc": str(frappe.utils.now()),
                      "nguoi": frappe.session.user, "noi_dung": cong})
        d.lich_su = json.dumps(ls[:20], ensure_ascii=False)
    d.ban_cong_khai = json.dumps(cong_moi, ensure_ascii=False)
    d.ban_nhap = json.dumps(nhap_moi, ensure_ascii=False)
    d.flags.luu_noi_dung_web = True
    if hang:
        d.save(ignore_permissions=True)
    else:
        d.insert(ignore_permissions=True)
    return bang_moi()


def _doc_json(v, mac_dinh=None):
    if isinstance(v, str):
        try:
            return json.loads(v)
        except ValueError:
            frappe.throw("Dữ liệu gửi lên không đọc được. Tải lại trang.")
    return mac_dinh if v is None else v


@frappe.whitelist(methods=["POST"])
def luu_muc(muc, dau_cu=""):
    """Lưu một ưu đãi, tiệc hoặc vị trí tuyển dụng. Khách thấy ngay."""
    kiem_quyen()
    muc = _doc_json(muc)
    if isinstance(muc, dict) and muc.get("loai") == "uu_dai":
        # v589: ưu đãi chỉ tạo và bật tắt trên ERP, web đồng bộ theo.
        frappe.throw("Ưu đãi nay tạo, sửa và bật tắt trên app ERP: Bán hàng, Chương trình khuyến mãi, mục Website.")
    return _ghi_ca_hai(lambda nd: ap_muc(nd, muc, dau_cu or ""), lambda nd: ap_muc(nd, muc, None))


@frappe.whitelist(methods=["POST"])
def xoa_muc_web(id_muc, dau_cu=""):
    """Xoá một ưu đãi, tiệc hoặc vị trí. Bản cũ vẫn nằm trong lịch sử."""
    kiem_quyen()
    return _ghi_ca_hai(lambda nd: xoa_muc(nd, id_muc, dau_cu or ""), lambda nd: xoa_muc(nd, id_muc, None))


@frappe.whitelist(methods=["POST"])
def luu_thong_tin(phan, gia_tri, dau_cu=""):
    """Lưu thẻ Liên hệ hoặc Cửa hàng. Khách thấy ngay."""
    kiem_quyen()
    gia_tri = _doc_json(gia_tri)
    return _ghi_ca_hai(lambda nd: ap_thong_tin(nd, phan, gia_tri, dau_cu or ""),
                       lambda nd: ap_thong_tin(nd, phan, gia_tri, None))


def _lien_he_tho():
    """Đúng chữ đang lưu ở các ô web_* của Settings, không suy thêm gì (bản
    công khai don_web.lien_he tự suy Zalo từ số điện thoại; ở màn sửa phải
    thấy ô trống là trống)."""
    from vagabond.lib import cfg_o
    return {k: str(cfg_o(O_LIEN_HE[k]) or "").strip() for k in TRUONG_LIEN_HE}


@frappe.whitelist(methods=["POST"])
def luu_lien_he(gia_tri, dau_cu=""):
    """Lưu thẻ Liên hệ vào các ô web_* của Vagabond Settings. Khách thấy ngay.

    Đây là nguồn #367 đã dùng cho chân trang và biên nhận, nên sửa ở đây là
    đổi ở mọi trang khách. Chỉ đúng bảy ô này, không đụng ô Settings khác.
    """
    kiem_quyen()
    try:
        lh = kiem_lien_he(_doc_json(gia_tri))
    except (ValueError, TypeError) as e:
        frappe.throw(str(e))
    # Cùng khoá hàng với nội dung web để hai người lưu liên hệ không chen nhau.
    frappe.db.sql("select name from `tabVagabond Noi Dung Web` where name=%s for update", (TEN,))
    if dau_van_tay(_lien_he_tho()) != (dau_cu or ""):
        frappe.throw("Có người vừa sửa thẻ Liên hệ. Tải lại để xem bản mới rồi sửa tiếp.", title="Có người vừa sửa")
    for k, v in lh.items():
        frappe.db.set_single_value("Vagabond Settings", O_LIEN_HE[k], v)
    frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")
    return bang_moi()


@frappe.whitelist(methods=["POST"])
def luu_nhan(thay):
    """Lưu các câu chữ vừa sửa ở thẻ Trang và chữ. Khách thấy ngay."""
    kiem_quyen()
    thay = _doc_json(thay)
    return _ghi_ca_hai(lambda nd: ap_nhan(nd, thay), lambda nd: ap_nhan(nd, thay, soat=False))


@frappe.whitelist()
def san_pham_bien_tap():
    """Đọc danh mục bán công khai cho editor, không tạo một danh mục giá mới."""
    kiem_quyen()
    from vagabond.kiem_banh import co_the_ban_hom_nay
    from vagabond.mua_vu import hang_theo_mua
    from vagabond.kiem_kho import con_tren_quay_web
    banh = co_the_ban_hom_nay() or {}
    ra, da_co = [], set()
    for g in list(banh.get("nhom") or []) + list((banh.get("dat_truoc") or {}).get("nhom") or []):
        for size in g.get("sizes") or []:
            ma = size.get("ma")
            if not ma or ma in da_co:
                continue
            da_co.add(ma)
            ra.append({"ma": ma, "ten": g.get("ten") or ma, "mo_ta": g.get("mo_ta") or "", "tang": "\n".join(g.get("tang") or [])})
    mua = hang_theo_mua() or {}
    for m in mua.get("mon") or []:
        if m.get("ma") and m["ma"] not in da_co:
            ra.append({"ma": m["ma"], "ten": m.get("ten") or m["ma"], "mo_ta": m.get("ruot") or ""})
    for q in (con_tren_quay_web() or {}).get("quay") or []:
        for m in q.get("mon") or []:
            if m.get("ma") and m["ma"] not in {x["ma"] for x in ra}:
                ra.append({"ma":m["ma"], "ten":m.get("ten") or m["ma"]})
    with (Path(__file__).parent / "public/web_order/san-pham-mac-dinh.json").open(encoding="utf-8") as f:
        mac_dinh = json.load(f)
    theo_ma = {m["ma"]:m for m in ra}
    for m in mac_dinh:
        if m["ma"] not in theo_ma:
            ra.append(m)
        else:
            for k, v in m.items():
                if not theo_ma[m["ma"]].get(k):
                    theo_ma[m["ma"]][k] = v
    # Mã cũ Marketing từng sửa vẫn tìm được để sửa/xóa nội dung.
    d = _doc() if frappe.db.exists(DOCTYPE, TEN) else None
    for ma in (json.loads(d.ban_nhap).get("san_pham") or {}) if d else {}:
        if ma not in {m["ma"] for m in ra}:
            ra.append({"ma":ma, "ten":ma})
    return ra[:500]
