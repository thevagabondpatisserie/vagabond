"""#245: màn thành viên dùng phiên OTP của Claude và sổ điểm thật tại quầy.

Cookie HttpOnly giữ vé phiên ngoài JavaScript; dữ liệu khách luôn lấy từ
số đã xác thực, không nhận mã Customer từ trình duyệt.
"""
import frappe
from frappe.rate_limiter import rate_limit
from vagabond import dang_nhap
from vagabond.lib import cfg, key

COOKIE = 'vgb_thanh_vien'


def _khong_cache():
    frappe.local.response_headers['Cache-Control'] = 'private, no-store'


@frappe.whitelist(allow_guest=True)
def san_sang():
    return {'otp':bool(cfg().get('zns_template_otp'))}


@frappe.whitelist(allow_guest=True, methods=['POST'])
@rate_limit(limit=12, seconds=600)
def gui_ma(sdt):
    if not cfg().get('zns_template_otp'):
        return {'ok':0, 'ly_do':'chua_mo'}
    r = dang_nhap.gui_ma(sdt)
    return {'ok':r.get('ok',0), 'ly_do':r.get('ly_do',''), 'song_giay':r.get('song_giay',0)}


@frappe.whitelist(allow_guest=True, methods=['POST'])
@rate_limit(limit=30, seconds=600)
def xac_thuc(sdt, ma):
    r = dang_nhap.xac_thuc(sdt, ma)
    if not r.get('ok'):
        return {'ok':0, 'ly_do':r.get('ly_do','ma_khong_dung')}
    # Frappe auth.CookieManager.set_cookie: không đặt domain, cookie chỉ ở
    # đúng hostname khách đăng nhập, không chia sẻ sang app/ERP subdomain.
    frappe.local.cookie_manager.set_cookie(COOKIE, r['token'], httponly=True,
        secure=True, samesite='Strict', max_age=dang_nhap.PHIEN_SONG_NGAY*86400)
    _khong_cache()
    return {'ok':1}


@frappe.whitelist(allow_guest=True, methods=['POST'])
def thoat():
    dang_nhap.thoat(frappe.request.cookies.get(COOKIE))
    frappe.local.cookie_manager.delete_cookie(COOKIE)
    _khong_cache()
    return {'ok':1}


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=30, seconds=600)
def toi():
    _khong_cache()
    so = dang_nhap._phien(frappe.request.cookies.get(COOKIE))
    if not so:
        return {'ok':0,'ly_do':'chua_dang_nhap'}
    noi_dia = dang_nhap._sdt_noi_dia(so)
    ds = frappe.get_all('Customer', filters={'mobile_no':noi_dia, 'disabled':0},
        fields=['name','customer_name','vgb_hang'], limit_page_length=2)
    if len(ds) > 1:
        return {'ok':0,'ly_do':'can_doi_chieu'}
    kh = ds[0] if ds else {}
    hang = frappe.db.get_value('Vagabond Hang Khach', kh.get('vgb_hang'),
        ['ten_hang','anh','mo_ta','giam_gia','tich_diem'], as_dict=True) if kh.get('vgb_hang') else None
    from vagabond.diem_otp import _so_du
    diem = _so_du(kh['name']) if kh else 0
    c = cfg(); k = key(c, 'pancake_api_key')
    don = dang_nhap._don_pancake(c, k, noi_dia) if k and c.pancake_shop_id else []
    return {'ok':1, 'ten':kh.get('customer_name',''), 'sdt':noi_dia, 'hang':hang,
            'diem':diem, 'don':don, 'co_ho_so':bool(kh)}
