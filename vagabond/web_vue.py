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


def chinh_sach_vue(ds):
    """THUẦN (Codex #484): chính sách ở chân trang Vue giữ trong /web_moi, không
    nhảy sang trang cũ. Cùng luật lọc với trang đặt bánh Vue: chỉ /chu-thuong."""
    return [dict(c, duong='/web_moi' + c['duong']) for c in ds or []
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
    return ra


def cay_chinh_sach(html):
    p = CayChinhSach()
    p.feed(html or '')
    return p.goc


def seo_banh():
    nd = noi_dung_web.cong_khai()
    nhan = nd.get('nhan') or {}
    # Dùng đúng nhãn tiêu đề đã có trong Editor, không tạo kho cấu hình khác.
    khoi = next((k for k in nd.get('khoi') or [] if k.get('hien') and k.get('anh') and k.get('tieu_de')), {})
    anh = trang_khach._lien_ket_an_toan(khoi.get('anh'))
    if anh.startswith('/'):
        anh = 'https://order.thevagabondpatisserie.com' + anh
    return {'description': str(khoi.get('noi_dung') or khoi.get('tieu_de') or '')[:300],
            'image': anh if anh.startswith('https://') else '',
            'title': nhan.get('dat_banh_e7c59d5a1') or 'Đặt bánh · The Vagabond Pâtisserie',
            'url': 'https://order.thevagabondpatisserie.com/banh'}
