"""Dữ liệu trang Vue dùng nguyên cửa công khai hiện có, không đọc bản nháp."""
import re
from html.parser import HTMLParser
from vagabond import noi_dung_web, trang_khach


class CayChinhSach(HTMLParser):
    """HTML đã sanitize -> cây thẻ cho Vue h(), không biên dịch nội dung thành template."""
    THE = frozenset(('p', 'br', 'strong', 'em', 'b', 'i', 'u', 's', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'blockquote', 'pre', 'code', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td'))

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.goc = []
        self.ngan = [self.goc]
        self.the = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.THE:
            return
        a = dict(attrs)
        props = {}
        if tag == 'a':
            href = trang_khach._lien_ket_an_toan(a.get('href'))
            if href:
                props['href'] = href
                props['rel'] = 'noopener noreferrer'
        n = {'tag': tag, 'props': props, 'con': []}
        self.ngan[-1].append(n)
        if tag not in ('br', 'hr'):
            self.ngan.append(n['con'])
            self.the.append(tag)

    def handle_endtag(self, tag):
        if tag in self.the:
            i = len(self.the) - 1 - self.the[::-1].index(tag)
            self.the = self.the[:i]
            self.ngan = self.ngan[:i + 1]

    def handle_data(self, data):
        self.ngan[-1].append(data)


def chinh_sach_vue(ds, duong=None):
    """THUẦN (Codex #484): chính sách ở chân trang Vue giữ trong /web_moi, không
    nhảy sang trang cũ. Cùng luật lọc với trang đặt bánh Vue: chỉ /chu-thuong.

    v603: trang Vue đang phát ở đường công khai (biên nhận /banh/xong khi đã
    tráo) thì trỏ thẳng ba trang chính sách công khai, không lọt về /web_moi."""
    tien_to = '' if duong is not None and trang_chu_dat_banh(duong) == '/banh' else '/web_moi'
    return [dict(c, duong=tien_to + c['duong']) for c in ds or []
            if re.fullmatch(r'/[a-z-]+', str(c.get('duong') or ''))]


def nut_lien_he_bien_nhan(lh, nhan):
    """THUẦN (Codex #484): nút Zalo, Messenger của biên nhận Vue lấy chữ từ sổ
    nhãn đã xuất bản (Marketing sửa trong Editor), trống thì chữ mặc định."""
    ra = []
    for kenh, khoa, mac_dinh in trang_khach.NUT_LIEN_HE_BIEN_NHAN:
        u = trang_khach._lien_ket_an_toan((lh or {}).get(kenh))
        if u:
            chu = (nhan or {}).get(khoa)
            ra.append({'href': u, 'khoa': khoa, 'ten': chu.strip() if isinstance(chu, str) and chu.strip() else mac_dinh})
    # Cùng nút "Gọi" như biên nhận trang cũ (trang cũ cũng không có khoá nhãn cho nút này).
    so = str((lh or {}).get('dien_thoai_so') or '')
    if so and re.fullmatch(r'\+?[0-9]{6,15}', so):
        ra.append({'href': 'tel:' + so, 'khoa': '', 'ten': 'Gọi ' + str((lh or {}).get('dien_thoai') or so), 'lop': 'phu'})
    return ra


def bang_bien_nhan():
    """THUẦN (Codex #484): bảng câu nghiệp vụ -> nhãn cho biên nhận Vue, lấy từ
    đúng một nguồn với biên nhận trang cũ."""
    tien_to, khoa, mac_dinh = trang_khach.TIEN_TO_TU_LAY
    return {'gia_tri': {k: list(v) for k, v in trang_khach.GIA_TRI_BIEN_NHAN.items()},
            'tien_to': [tien_to, khoa, mac_dinh]}


def doi_ngon_ngu_html(duong, ngon_ngu, co_en, nhan):
    """THUẦN (Codex #484): link đổi ngôn ngữ trang chính sách Vue, chữ đọc từ nhãn
    ngon_ngu_vn / ngon_ngu_en như trang chính sách cũ."""
    nhan = nhan or {}
    chu = lambda k, d: (nhan.get(k).strip() if isinstance(nhan.get(k), str) and nhan.get(k).strip() else d)
    if ngon_ngu == 'en':
        return '<a href="%s">%s</a>' % (trang_khach._e(duong), trang_khach._e(chu('ngon_ngu_vn', 'Tiếng Việt')))
    if co_en:
        return '<a href="%s?ngon_ngu=en">%s</a>' % (trang_khach._e(duong), trang_khach._e(chu('ngon_ngu_en', 'English')))
    return ''


def cay_chinh_sach(html):
    p = CayChinhSach()
    p.feed(html or '')
    return p.goc


# v605 (anh Việt 18/10/2026, SEO trang đặt bánh trên tên miền chính).
# Trước đây mô tả và ảnh xem trước lấy từ khối Editor đầu tiên có ảnh, mà khối
# đó là "Mở các kênh đặt hàng" kèm logo Grab: Google và Facebook hiện đúng câu
# đó và logo Grab. Nay dùng mô tả, ảnh cố định của riêng tiệm. Chưa mở cho Editor
# sửa (Codex #491: nhãn chưa đăng ký trong noi_dung_web.NHAN thì Editor không lưu
# được); muốn mở thì đăng ký nhãn và kiểm qua đường lưu thật của Editor.
SEO_MO_TA = ("The Vagabond Pâtisserie, tiệm bánh ngọt Pháp tại 9 Trần Cao Vân, trung tâm TP.HCM. "
	"Đặt bánh sinh nhật, entremet và bánh theo mùa online, nhận tại tiệm hoặc giao tận nơi.")
SEO_ANH = "/assets/vagabond/web_order/og-banh.jpg"
TEN_TIEM = "The Vagabond Pâtisserie"
DIEN_THOAI = "+84931224334"


def du_lieu_cau_truc(goc, anh):
    """THUẦN: khối JSON-LD cho Google (tên tiệm, địa chỉ, điện thoại, logo).

    Trả chuỗi đã chặn "</" để nhúng thẳng vào thẻ script mà không đóng thẻ sớm."""
    import json
    d = [{
        "@context": "https://schema.org", "@type": "Bakery", "name": TEN_TIEM,
        "url": goc + "/", "image": anh, "logo": goc + "/assets/vagabond/pwa/icon-512.png",
        "telephone": DIEN_THOAI, "priceRange": "$$", "servesCuisine": "French pastry",
        "address": {"@type": "PostalAddress", "streetAddress": "9 Trần Cao Vân",
            "addressLocality": "Phường Sài Gòn", "addressRegion": "TP. Hồ Chí Minh", "addressCountry": "VN"},
        "hasMenu": goc + "/banh",
    }, {"@context": "https://schema.org", "@type": "WebSite", "name": TEN_TIEM, "url": goc + "/"}]
    return json.dumps(d, ensure_ascii=False).replace("</", "<\\/")


def seo_banh(mien="order.thevagabondpatisserie.com"):
    nd = noi_dung_web.cong_khai()
    nhan = nd.get('nhan') or {}
    goc = 'https://' + mien
    anh = goc + SEO_ANH
    return {'description': SEO_MO_TA[:300],
            'image': anh,
            'title': nhan.get('dat_banh_e7c59d5a1') or 'Đặt bánh · The Vagabond Pâtisserie',
            'url': goc + '/banh',
            'ld_json': du_lieu_cau_truc(goc, anh)}


# ------------------------------------------------------------ tráo /banh sang bản Vue
# Anh Việt 17/10/2026: chuyển trang đặt bánh sang bản Vue. Công tắc nằm ở Cài đặt
# (Vagabond Settings > Web & quảng cáo > "Dùng trang đặt bánh bản mới"), tắt là
# về trang cũ ngay, không cần deploy. Phần chạm Frappe ở vagabond/trang_banh_vue.py.

# Đường khách -> tệp Vue phát thay khi công tắc bật. Ba trang chính sách cố ý
# KHÔNG tráo: trang cũ dựng chữ ngay trên máy chủ, bộ kiểm của Meta và máy tìm
# kiếm đọc được không cần chạy JS; bản Vue dựng chữ bằng JS.
TEP_VUE = {"banh": "web_moi/banh", "banh/xong": "web_moi/xong"}


def tep_ban_vue(duong, bat, tham_so=None):
    """THUẦN: trả tệp Vue phát thay cho đường này, hoặc "" để giữ trang cũ.

    Nhận /banh (kể cả trang chủ tên miền order, Frappe đã đổi thành "banh"
    trước khi tới đây) và biên nhận /banh/xong[/<token>] (luật định tuyến đã
    đổi thành "banh/xong" và đặt token vào form_dict). v603: Editor xem trước
    (?bien_tap=1) đi theo công tắc, để Marketing xem đúng bản khách đang thấy.
    ?ban=cu luôn mở trang cũ, để nhân viên so hai bản.
    """
    tep = TEP_VUE.get(str(duong or "").strip("/"), "")
    if not tep:
        return ""
    try:
        bat = int(bat or 0)
    except (TypeError, ValueError):
        bat = 0
    if not bat:
        return ""
    q = tham_so or {}
    if str(q.get("ban") or "").strip().lower() == "cu":
        return ""
    return tep


def dung_ban_vue(duong, bat, tham_so=None):
    """THUẦN: đường dẫn này có phát trang Vue thay trang cũ không."""
    return bool(tep_ban_vue(duong, bat, tham_so))


def trang_chu_dat_banh(duong):
    """THUẦN: nút "Về trang đặt bánh" của biên nhận, chính sách Vue: đã tráo (đang
    phát ở /banh/...) thì về /banh, còn lại (đường thử /web_moi/...) về /web_moi/banh."""
    d = str(duong or "")
    return "/banh" if d == "/banh" or d.startswith("/banh/") else "/web_moi/banh"
