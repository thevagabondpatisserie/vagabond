"""#245: nhận yêu cầu đặt bàn, nhân viên xác nhận sau khi kiểm chỗ tại tiệm.

Không coi gửi form là đã có bàn. Lịch mở được quản lý riêng; mặc định tắt
cho tới khi quản lý chọn cơ sở và khung giờ thật.
"""
# phần thuần
from functools import partial
import hashlib
import json
import re
from datetime import datetime, timedelta

DIP = ('Không có dịp riêng', 'Sinh nhật', 'Kỷ niệm', 'Hẹn hò', 'Gặp đối tác', 'Họp nhóm', 'Khác')

TRANG_THAI = ('Chờ xác nhận', 'Đã xác nhận', 'Đã đến', 'Đã hủy')


def chuan_hoa(du_lieu, cau_hinh, luc):
    if isinstance(du_lieu, str):
        if len(du_lieu) > 5000:
            raise ValueError('Yêu cầu quá dài. Rút ngắn ghi chú rồi gửi lại.')
        du_lieu = json.loads(du_lieu)
    if not isinstance(du_lieu, dict):
        raise ValueError('Kiểm tra lại thông tin đặt bàn.')
    if not cau_hinh.get('bat'):
        raise ValueError('Tiệm chưa mở đặt bàn online. Gọi 0931 224 334 để được hỗ trợ.')
    ten = str(du_lieu.get('ten') or '').strip()
    sdt = re.sub(r'[\s.()+-]', '', str(du_lieu.get('sdt') or ''))
    if sdt.startswith('84'):
        sdt = '0' + sdt[2:]
    if not ten or len(ten) > 120 or not re.fullmatch(r'0[35789]\d{8}', sdt):
        raise ValueError('Điền họ tên và số điện thoại di động Việt Nam hợp lệ.')
    try:
        so = int(du_lieu.get('so_khach'))
        if str(so) != str(du_lieu.get('so_khach')) or not 1 <= so <= int(cau_hinh['toi_da_khach']):
            raise ValueError()
        ngay = datetime.strptime(str(du_lieu.get('ngay')), '%Y-%m-%d').date()
        gio = str(du_lieu.get('gio'))
        den = datetime.strptime(str(ngay) + ' ' + gio, '%Y-%m-%d %H:%M')
    except (TypeError, ValueError, KeyError):
        raise ValueError('Chọn ngày, giờ và số khách trong phạm vi tiệm nhận đặt bàn.')
    if gio not in cau_hinh.get('khung_gio', []):
        raise ValueError('Khung giờ này chưa mở đặt bàn. Chọn lại giờ trên trang.')
    if den <= luc + timedelta(minutes=60) or ngay > luc.date() + timedelta(days=int(cau_hinh['toi_da_ngay'])):
        raise ValueError('Đặt trước ít nhất 1 giờ và trong khoảng ngày tiệm đang nhận.')
    if du_lieu.get('co_so') != cau_hinh.get('co_so'):
        raise ValueError('Chọn đúng cơ sở đang nhận đặt bàn.')
    ghi_chu = str(du_lieu.get('ghi_chu') or '').strip()
    if len(ghi_chu) > 1000:
        raise ValueError('Ghi chú tối đa 1.000 ký tự.')
    dip = str(du_lieu.get('dip') or '').strip()
    khu = str(du_lieu.get('khu_vuc') or '').strip()
    if dip and dip not in DIP:
        raise ValueError('Chọn dịp trong danh sách trên form.')
    if khu and khu not in cau_hinh.get('khu_vuc', []):
        raise ValueError('Khu vực này không thuộc cơ sở đang nhận đặt bàn. Chọn lại khu vực.')
    tre = du_lieu.get('tre_em')
    if tre is None or tre == '':
        tre = 0
    try:
        n = int(tre)
        if str(n) != str(tre) or not 0 <= n <= so:
            raise ValueError()
    except (TypeError, ValueError):
        raise ValueError('Số trẻ em phải là số nguyên từ 0 đến tổng số khách.')
    email = str(du_lieu.get('email') or '').strip()
    if email and (len(email) > 140 or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', email)):
        raise ValueError('Kiểm tra lại email, ví dụ ten@example.com, hoặc để trống.')
    banh = str(du_lieu.get('banh_kem_theo') or '').strip()
    if len(banh) > 1000:
        raise ValueError('Bánh muốn đặt sẵn tối đa 1.000 ký tự.')
    return {'ten':ten, 'sdt':sdt, 'co_so':cau_hinh['co_so'], 'ngay':str(ngay), 'gio':gio, 'so_khach':so, 'ghi_chu':ghi_chu,
            'dip':dip, 'khu_vuc':khu, 'tre_em':n, 'email':email, 'banh_kem_theo':banh}


def soan_tin_dat_ban(doc):
    """Tin dành cho FOH; bỏ dòng tuỳ chọn rỗng để đọc nhanh trên điện thoại."""
    # Giữ nội dung gốc trong phiếu; khi gửi nhóm, mỗi giá trị chỉ ở một dòng.
    doc = {k: re.sub(r'\s+', ' ', v).strip() if isinstance(v, str) else v for k, v in doc.items()}
    ngay = datetime.strptime(str(doc.get('ngay'))[:10], '%Y-%m-%d').strftime('%d/%m')
    dong = ['YÊU CẦU ĐẶT BÀN MỚI',
            'Tên: %s, SĐT: %s' % (doc.get('ten'), doc.get('sdt')),
            'Cơ sở: %s' % (doc.get('ten_co_so') or doc.get('co_so')),
            'Ngày giờ: %s lúc %s' % (ngay, doc.get('gio')),
            'Số khách: %s' % doc.get('so_khach')]
    if doc.get('tre_em'):
        dong[-1] += ', trong đó %s trẻ em' % doc['tre_em']
    for ten, nhan in [('dip','Dịp'), ('khu_vuc','Khu vực'), ('banh_kem_theo','Bánh kèm theo'), ('ghi_chu','Ghi chú'), ('email','Email')]:
        gia = doc.get(ten)
        if gia and not (ten == 'dip' and gia == 'Không có dịp riêng'):
            dong.append('%s: %s' % (nhan, gia))
    dong.append('Trạng thái: Chờ xác nhận. Mở phiếu: %s' % doc.get('url', ''))
    return '\n'.join(dong)



import frappe
from frappe.rate_limiter import rate_limit

DOCTYPE = 'Vagabond Dat Ban'
CAU_HINH = 'Vagabond Cau Hinh Dat Ban'


def _cau_hinh():
    from vagabond import diem_ban
    d = frappe.get_single(CAU_HINH)
    co_so = diem_ban.theo_ma(d.co_so)
    return {'bat':bool(d.bat and co_so and co_so.get('bat') and co_so.get('quay')),
            'co_so':d.co_so, 'ten_co_so':(co_so or {}).get('ten', ''),
            'dia_chi':(co_so or {}).get('dia_chi', ''), 'khung_gio':str(d.khung_gio or '').split(),
            'khu_vuc':list(dict.fromkeys(x.strip() for x in str(d.get('khu_vuc') or '').splitlines() if x.strip())),
            'dip':list(DIP), 'toi_da_khach':d.toi_da_khach or 8, 'toi_da_ngay':d.toi_da_ngay or 30}


@frappe.whitelist(allow_guest=True)
def cau_hinh():
    return dict(_cau_hinh(), hom_nay=str(frappe.utils.nowdate()))


@frappe.whitelist(methods=['POST'], allow_guest=True)
@rate_limit(limit=5, seconds=600)
def gui(du_lieu, ma_lan_gui):
    if not isinstance(ma_lan_gui, str) or not re.fullmatch(r'[a-f0-9-]{36}', ma_lan_gui):
        frappe.throw('Tải lại trang để bắt đầu yêu cầu đặt bàn.')
    try:
        raw = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
        chuoi = json.dumps(raw, sort_keys=True, ensure_ascii=False)
        if not isinstance(raw, dict) or len(chuoi) > 5000:
            raise ValueError('Yêu cầu quá dài hoặc không hợp lệ.')
    except (TypeError, ValueError) as e:
        frappe.throw(str(e))
    dau = hashlib.sha256(chuoi.encode()).hexdigest()
    ten = hashlib.sha256(ma_lan_gui.encode()).hexdigest()
    # Đối soát khóa trước kiểm lịch: retry sau giờ hẹn hoặc khi tiệm tắt
    # nhận bàn vẫn phải nhận ra yêu cầu trước đã lưu, không báo mất đơn.
    cu = frappe.db.get_value(DOCTYPE, ten, ['name', 'bam_noi_dung'], as_dict=True)
    if cu:
        if cu.bam_noi_dung != dau:
            frappe.throw('Yêu cầu trước đã được nhận. Tải lại trang để đặt lịch khác.')
        return {'ok':1, 'ma':cu.name[:12].upper(), 'trang_thai':'Đã tiếp nhận'}
    try:
        nd = chuan_hoa(raw, _cau_hinh(), frappe.utils.now_datetime())
    except (TypeError, ValueError) as e:
        frappe.throw(str(e))
    d = frappe.get_doc(dict(nd, doctype=DOCTYPE, name=ten, bam_noi_dung=dau, trang_thai='Chờ xác nhận'))
    d.flags.dat_ban_web = True
    moc = 'dat_ban_' + frappe.generate_hash(length=12)
    frappe.db.savepoint(moc)
    so_thong_bao = len(frappe.local.message_log or [])
    try:
        d.insert(ignore_permissions=True)
    except frappe.DuplicateEntryError:
        frappe.db.rollback(save_point=moc)
        # Hai request có thể cùng đọc "chưa có". Đọc khóa hiện tại sau
        # unique constraint, không dùng lại snapshot REPEATABLE READ cũ.
        cu = frappe.db.get_value(DOCTYPE, ten, ['name', 'bam_noi_dung'], as_dict=True, for_update=True)
        if not cu:
            raise
        if cu.bam_noi_dung != dau:
            frappe.throw('Yêu cầu trước đã được nhận. Tải lại trang để đặt lịch khác.')
        # db_insert đã thêm thông báo Duplicate Name trước khi ném lỗi.
        # Đây là retry thành công; giữ thông báo cũ, bỏ phần của insert vừa lùi.
        del frappe.local.message_log[so_thong_bao:]
        return {'ok':1, 'ma':cu.name[:12].upper(), 'trang_thai':'Đã tiếp nhận'}
    return {'ok':1, 'ma':d.name[:12].upper(), 'trang_thai':'Chờ xác nhận'}


def kiem_phieu(doc):
    if doc.is_new():
        if doc.trang_thai != 'Chờ xác nhận':
            frappe.throw('Yêu cầu mới phải bắt đầu ở trạng thái Chờ xác nhận.')
        try:
            doc.update(chuan_hoa(doc.as_dict(), _cau_hinh(), frappe.utils.now_datetime()))
        except ValueError as e:
            frappe.throw(str(e))
    cu = doc.get_doc_before_save()
    if cu:
        for ten in ('ten', 'sdt', 'ngay', 'gio', 'so_khach', 'co_so', 'ghi_chu', 'bam_noi_dung', 'dip', 'khu_vuc', 'tre_em', 'email', 'banh_kem_theo'):
            if str(cu.get(ten) or "") != str(doc.get(ten) or ""):
                frappe.throw('Giữ nguyên yêu cầu khách đã gửi. Ghi thay đổi vào ghi chú xử lý.')
        chuyen = {'Chờ xác nhận':{'Đã xác nhận','Đã hủy'}, 'Đã xác nhận':{'Đã đến','Đã hủy'}, 'Đã đến':set(), 'Đã hủy':set()}
        if doc.trang_thai != cu.trang_thai and doc.trang_thai not in chuyen.get(cu.trang_thai, set()):
            frappe.throw('Không thể chuyển ngược trạng thái. Ghi rõ kết quả trong ghi chú xử lý.')
    if doc.trang_thai not in TRANG_THAI:
        frappe.throw('Chọn trạng thái đặt bàn hợp lệ.')


def _loi_zalo(ten):
    # Không đưa nội dung khách vào Error Log.
    frappe.log_error(title='Đặt bàn: chưa ghi được tin Zalo',
                     message='Phiếu %s. Kiểm tra bảng nhóm Zalo (chủ đề Đặt bàn).' % ten)


def con_cho_xac_nhan(ten):
    """Tin Zalo loại việc hỏi lại ngay trước khi gửi: phiếu còn chờ xác nhận không."""
    return frappe.db.get_value(DOCTYPE, ten, 'trang_thai') == 'Chờ xác nhận'


def bao_dat_ban_moi(doc, method=None):
    """v597 (anh Việt 16/10/2026: chuyển hết Lark sang Zalo): báo nhóm Zalo chủ đề
    Đặt bàn. kenh_zalo.bao ghi tin vào sổ trong giao dịch của phiếu rồi gửi sau
    commit; Zalo lỗi hay chưa có nhóm thì yêu cầu khách vẫn lưu nguyên."""
    if getattr(frappe.flags, 'vagabond_kiem_that', False):
        return
    from vagabond import diem_ban, kenh_zalo
    try:
        d = doc.as_dict()
        d['ten_co_so'] = (diem_ban.theo_ma(d.get('co_so')) or {}).get('ten') or d.get('co_so')
        d['url'] = frappe.utils.get_url_to_form(DOCTYPE, doc.name)
        tieu_de, dong = kenh_zalo.tach_tin(soan_tin_dat_ban(d))
    except Exception:
        _loi_zalo(doc.name)
        return
    # Không bọc bao(): nó tự nuốt lỗi lẻ, chỉ ném lỗi làm chết cả giao dịch.
    # Codex #481: hook chỉ chạy một lần lúc tạo phiếu; chưa có nhóm nhận thì để
    # lại Error Log nêu tên phiếu, gán nhóm sau không tự báo lại phiếu này.
    kenh_zalo.bao_hoac_ghi_loi('viec', 'dat_ban', tieu_de, dong, khoa='dat-ban:%s' % doc.name,
                               kiem='dat_ban_cho', nguon=doc.name, ma_tin='bh_dat_ban')




# ================================================================ v611
# Anh Việt 25/10/2026: nút "Thông tin đặt bàn" trong phân hệ Bán hàng. Quản lý
# cửa hàng xem đặt bàn từ web, Xác nhận (email khách theo mẫu đã duyệt + Zalo
# nhóm Bán hàng), Huỷ kèm lý do (email khách + Zalo), đánh dấu Khách đã đến.
# Nhắc Zalo khi yêu cầu còn chờ xác nhận mà chỉ còn GIO_NHAC giờ tới giờ hẹn.

QUYEN_DAT_BAN = ('Sales User', 'Sales Manager', 'System Manager', 'VGB - Quản lý cửa hàng')
KHOANG = ('hom_nay', 'ngay_mai', '7_ngay', 'da_qua')
NGAY_DA_QUA = 14
GIO_NHAC = 3
THU_NGAN = ('CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7')
LY_DO_MAU = ('Hết chỗ khung giờ này', 'Khách xin huỷ', 'Không liên lạc được khách', 'Tiệm đóng cửa hôm đó')


def khoang_ngay(khoang, hom_nay):
    """THUẦN: (từ, đến) của một chip ngày. 7_ngay là hôm nay tới 6 ngày sau."""
    from datetime import date
    h = hom_nay if isinstance(hom_nay, date) else datetime.strptime(str(hom_nay)[:10], '%Y-%m-%d').date()
    if khoang == 'ngay_mai':
        return h + timedelta(days=1), h + timedelta(days=1)
    if khoang == '7_ngay':
        return h, h + timedelta(days=6)
    if khoang == 'da_qua':
        return h - timedelta(days=NGAY_DA_QUA), h - timedelta(days=1)
    return h, h


def luc_hen(d):
    """THUẦN: datetime giờ khách đến, None nếu thiếu ngày giờ."""
    try:
        return datetime.strptime('%s %s' % (str(d.get('ngay'))[:10], str(d.get('gio'))[:5]), '%Y-%m-%d %H:%M')
    except (TypeError, ValueError):
        return None


def ngay_ngan(ngay):
    """THUẦN: '2026-10-25' -> 'CN 25/10'."""
    d = datetime.strptime(str(ngay)[:10], '%Y-%m-%d')
    return '%s %s' % (THU_NGAN[(d.weekday() + 1) % 7], d.strftime('%d/%m'))


def so_khach(d):
    tre = int(d.get('tre_em') or 0)
    return '%s khách%s' % (int(d.get('so_khach') or 0), (' (%d trẻ em)' % tre) if tre else '')


def _dong_dat_ban(d):
    """THUẦN: phần chung của tin xác nhận, huỷ, nhắc: khi nào, ở đâu, ai, bao nhiêu."""
    dong = ['%s lúc %s · %s' % (ngay_ngan(d.get('ngay')), d.get('gio'), d.get('ten_co_so') or d.get('co_so')),
            '%s · %s · %s' % (d.get('ten'), d.get('sdt'), so_khach(d))]
    them = []
    if d.get('khu_vuc'):
        them.append('Khu vực: %s' % d['khu_vuc'])
    if d.get('dip') and d.get('dip') != 'Không có dịp riêng':
        them.append('Dịp: %s' % d['dip'])
    if them:
        dong.append(' · '.join(them))
    if d.get('banh_kem_theo'):
        dong.append('Bánh đặt sẵn: %s' % re.sub(r'\s+', ' ', d['banh_kem_theo']).strip()[:160])
    return dong


def soan_tin_xac_nhan(d, ai, thu):
    """THUẦN: (tiêu đề, dòng) tin Zalo khi quản lý xác nhận. thu: câu trạng thái email."""
    return 'Đặt bàn đã xác nhận', _dong_dat_ban(d) + ['Xác nhận bởi %s · %s' % (ai, thu)]


def soan_tin_huy(d, ly_do, ai, thu):
    """THUẦN: (tiêu đề, dòng) tin Zalo khi quản lý huỷ, kèm lý do đã báo khách."""
    return 'Đặt bàn đã huỷ', _dong_dat_ban(d)[:2] + ['Lý do: %s' % ly_do, 'Huỷ bởi %s · %s' % (ai, thu)]


def can_nhac(rows, bay_gio, gio=GIO_NHAC):
    """THUẦN: phiếu còn chờ xác nhận mà giờ hẹn nằm trong `gio` giờ tới (chưa qua giờ)."""
    ra = []
    for r in rows or []:
        if r.get('trang_thai') != 'Chờ xác nhận':
            continue
        h = luc_hen(r)
        if h and bay_gio < h <= bay_gio + timedelta(hours=gio):
            ra.append(r)
    return ra


def qua_gio(d, bay_gio):
    """THUẦN: giờ hẹn đã tới hoặc đã qua (không còn xác nhận được)."""
    h = luc_hen(d)
    return bool(h and h <= bay_gio)


def dem_cho(rows, bay_gio):
    """THUẦN: số yêu cầu còn chờ xác nhận mà chưa qua giờ hẹn (số trên ô trang chủ)."""
    return len([r for r in rows or [] if r.get('trang_thai') == 'Chờ xác nhận' and not qua_gio(r, bay_gio)])


def cau_thu(gui, email, luc):
    """THUẦN: câu trạng thái email ghi lên phiếu và tin Zalo."""
    if not (email or '').strip():
        return 'khách không để email, nhớ gọi báo khách'
    if not gui:
        return 'không gửi email (quản lý tắt)'
    return 'đã gửi email cho khách lúc %s' % luc


def _kiem_quyen():
    if not set(QUYEN_DAT_BAN) & set(frappe.get_roles()):
        frappe.throw('Chỉ quản lý cửa hàng và Sales xem, xác nhận được đặt bàn.', frappe.PermissionError)


def _co_so(d):
    from vagabond import diem_ban
    cs = diem_ban.theo_ma(d.get('co_so')) or {}
    return cs.get('ten_ngan') or cs.get('ten') or d.get('co_so'), cs.get('ten') or d.get('co_so'), cs.get('dia_chi') or ''


@frappe.whitelist()
def ds_dat_ban(khoang='7_ngay'):
    """Đặt bàn theo chip ngày, kèm số đếm của từng chip để vẽ hàng chip."""
    _kiem_quyen()
    if khoang not in KHOANG:
        khoang = '7_ngay'
    hom_nay = datetime.strptime(str(frappe.utils.nowdate()), '%Y-%m-%d').date()
    tu, den = khoang_ngay(khoang, hom_nay)
    truong = ['name', 'ten', 'sdt', 'co_so', 'ngay', 'gio', 'so_khach', 'tre_em', 'dip', 'khu_vuc', 'email',
              'banh_kem_theo', 'ghi_chu', 'trang_thai', 'xu_ly', 'xu_ly_boi', 'xu_ly_luc', 'ly_do_huy', 'thu_khach']
    rows = frappe.get_all(DOCTYPE, filters={'ngay': ['between', [str(tu), str(den)]]}, fields=truong,
                          order_by='ngay asc, gio asc', limit_page_length=500)
    ten = {}
    for r in rows:
        if r.co_so not in ten:
            ten[r.co_so] = _co_so(r)[0]
        r['ten_co_so'] = ten[r.co_so]
        r['ngay'] = str(r.ngay)
        r['xu_ly_luc'] = str(r.xu_ly_luc or '')
    if khoang == 'da_qua':
        rows.reverse()
    dem = {}
    for k in KHOANG:
        a, b = khoang_ngay(k, hom_nay)
        dem[k] = frappe.db.count(DOCTYPE, {'ngay': ['between', [str(a), str(b)]], 'trang_thai': ['!=', 'Đã hủy']})
    return {'rows': rows, 'dem': dem, 'hom_nay': str(hom_nay), 'khoang': khoang, 'ly_do_mau': list(LY_DO_MAU)}


@frappe.whitelist()
def dem_cho_xac_nhan():
    """Số trên ô Thông tin đặt bàn ở trang chủ: yêu cầu còn chờ xác nhận, chưa qua giờ."""
    if not set(QUYEN_DAT_BAN) & set(frappe.get_roles()):
        return {'so': 0}
    bay_gio = frappe.utils.now_datetime()
    rows = frappe.get_all(DOCTYPE, filters={'trang_thai': 'Chờ xác nhận', 'ngay': ['>=', str(bay_gio.date())]},
                          fields=['ngay', 'gio', 'trang_thai'], limit_page_length=500)
    return {'so': dem_cho(rows, bay_gio)}


def _gui_thu(doc, loai, loi_nhan='', ly_do=''):
    """Gửi thư cho khách theo mẫu đã duyệt. Trả True nếu đã xếp thư."""
    from vagabond import thu_khung
    from vagabond import dat_ban_thu
    d = doc.as_dict()
    _ngan, d['ten_co_so'], d['dia_chi'] = _co_so(d)
    goc, quay = thu_khung.goc_anh(), thu_khung._cac_quay()
    html = (dat_ban_thu.thu_xac_nhan(d, loi_nhan, goc, quay) if loai == 'xac_nhan'
            else dat_ban_thu.thu_huy(d, ly_do, goc, quay))
    frappe.sendmail(recipients=[doc.email], subject=dat_ban_thu.tieu_de_thu(loai, d), message=html,
                    reference_doctype=DOCTYPE, reference_name=doc.name)
    return True


def _bao_xac_nhan(d, ai, thu):
    from vagabond import kenh_zalo
    tieu_de, dong = soan_tin_xac_nhan(d, ai, thu)
    kenh_zalo.bao('thong_bao', 'dat_ban', tieu_de, dong, link=frappe.utils.get_url('/thong-tin-dat-ban'),
                  khoa='dat-ban-xac_nhan:%s' % d.get('name'), ma_tin='bh_dat_ban_xac_nhan')


def _bao_huy(d, ly_do, ai, thu):
    from vagabond import kenh_zalo
    tieu_de, dong = soan_tin_huy(d, ly_do, ai, thu)
    kenh_zalo.bao('thong_bao', 'dat_ban', tieu_de, dong, link=frappe.utils.get_url('/thong-tin-dat-ban'),
                  khoa='dat-ban-huy:%s' % d.get('name'), ma_tin='bh_dat_ban_huy')


def _xu_ly(name, trang_thai, cho_phep, loi_nhan='', ly_do='', gui_email=1):
    """Đổi trạng thái một phiếu, ghi vết, gửi thư (nếu có), báo Zalo. Dùng chung ba nút."""
    _kiem_quyen()
    doc = frappe.get_doc(DOCTYPE, name, for_update=True)
    if doc.trang_thai == trang_thai:
        return {'ok': 1, 'da_co': 1, 'trang_thai': doc.trang_thai}
    if doc.trang_thai not in cho_phep:
        frappe.throw('Đặt bàn này đang ở trạng thái %s, không chuyển sang %s được.' % (doc.trang_thai, trang_thai))
    if trang_thai == 'Đã xác nhận' and qua_gio(doc.as_dict(), frappe.utils.now_datetime()):
        frappe.throw('Đã quá giờ hẹn của đặt bàn này, không gửi xác nhận cho khách nữa. Gọi khách hoặc bấm Huỷ.')
    ai = frappe.utils.get_fullname(frappe.session.user) or frappe.session.user
    luc = frappe.utils.now_datetime()
    gio = luc.strftime('%H:%M %d/%m')
    loai = {'Đã xác nhận': 'xac_nhan', 'Đã hủy': 'huy'}.get(trang_thai)
    gui = bool(int(gui_email or 0)) and bool((doc.email or '').strip()) and bool(loai)
    viec = {'Đã xác nhận': 'Xác nhận', 'Đã hủy': 'Huỷ', 'Đã đến': 'Khách đã đến'}[trang_thai]
    vet = '%s %s bởi %s.%s%s' % (gio, viec, ai, (' Lời nhắn: %s' % loi_nhan) if loi_nhan else '',
                                  (' Lý do: %s' % ly_do) if ly_do else '')
    doc.trang_thai = trang_thai
    doc.xu_ly = ((doc.xu_ly or '').strip() + '\n' + vet).strip()
    doc.xu_ly_boi = ai
    doc.xu_ly_luc = luc
    if ly_do:
        doc.ly_do_huy = ly_do
    if loai:
        doc.thu_khach = cau_thu(gui, doc.email, gio)
    doc.flags.ignore_permissions = True
    doc.save()
    if gui:
        try:
            _gui_thu(doc, loai, loi_nhan, ly_do)
        except Exception as e:
            # Codex #498 (4371394665): deadlock hay mất kết nối lúc xếp thư thì
            # MariaDB đã lùi cả lần lưu trạng thái phía trên. Nuốt lỗi là báo
            # "đã xác nhận" và nhắn Zalo trong khi phiếu vẫn ở trạng thái cũ.
            from vagabond.loi_csdl import chet_giao_dich
            if chet_giao_dich(e):
                raise
            frappe.log_error(title='Đặt bàn: chưa gửi được email khách', message='Phiếu %s.' % doc.name)
            doc.db_set('thu_khach', 'CHƯA gửi được email, gọi báo khách', update_modified=False)
    if loai:
        try:
            d = doc.as_dict()
            d['ten_co_so'] = _co_so(d)[0]
            thu = doc.thu_khach or cau_thu(gui, doc.email, gio)
            if loai == 'xac_nhan':
                _bao_xac_nhan(d, ai, thu)
            else:
                _bao_huy(d, ly_do, ai, thu)
        except Exception as e:
            from vagabond import kenh_zalo
            if kenh_zalo.chet_giao_dich(e):
                raise
            _loi_zalo(doc.name)
    return {'ok': 1, 'trang_thai': doc.trang_thai, 'thu_khach': doc.thu_khach or ''}


@frappe.whitelist(methods=['POST'])
def xac_nhan(name, loi_nhan='', gui_email=1):
    """Nút Xác nhận: giữ bàn, gửi email xác nhận theo mẫu, báo Zalo nhóm Bán hàng."""
    return _xu_ly(name, 'Đã xác nhận', ('Chờ xác nhận',), loi_nhan=(loi_nhan or '').strip()[:500], gui_email=gui_email)


@frappe.whitelist(methods=['POST'])
def huy(name, ly_do='', gui_email=1):
    """Nút Huỷ: bắt buộc lý do (khách đọc câu này), email báo khách, báo Zalo."""
    ly_do = re.sub(r'\s+', ' ', ly_do or '').strip()[:300]
    if len(ly_do) < 5:
        frappe.throw('Ghi lý do huỷ (khách sẽ đọc câu này), ít nhất vài chữ.')
    return _xu_ly(name, 'Đã hủy', ('Chờ xác nhận', 'Đã xác nhận'), ly_do=ly_do, gui_email=gui_email)


@frappe.whitelist(methods=['POST'])
def da_den(name):
    """Nút Khách đã đến: chỉ ghi nhận, không email, không Zalo."""
    return _xu_ly(name, 'Đã đến', ('Đã xác nhận',))


def nhac_sap_toi():
    """Lịch 15 phút: yêu cầu còn chờ xác nhận mà chỉ còn GIO_NHAC giờ tới giờ hẹn. Mỗi phiếu một tin."""
    try:
        from vagabond import kenh_zalo
        bay_gio = frappe.utils.now_datetime()
        rows = frappe.get_all(DOCTYPE, filters={'trang_thai': 'Chờ xác nhận',
                              'ngay': ['between', [str(bay_gio.date()), str((bay_gio + timedelta(hours=GIO_NHAC)).date())]]},
                              fields=['name', 'ten', 'sdt', 'co_so', 'ngay', 'gio', 'so_khach', 'tre_em', 'dip', 'khu_vuc',
                                      'banh_kem_theo', 'trang_thai'], limit_page_length=0)
        for r in can_nhac(rows, bay_gio):
            r['ten_co_so'] = _co_so(r)[0]
            con = int((luc_hen(r) - bay_gio).total_seconds() // 60)
            dong = _dong_dat_ban(r) + ['Còn %d giờ %02d phút tới giờ khách đến mà chưa ai xác nhận. Gọi khách rồi bấm Xác nhận hoặc Huỷ.'
                                       % (con // 60, con % 60)]
            kenh_zalo.bao('viec', 'dat_ban', 'Đặt bàn sắp tới giờ, chưa xác nhận', dong,
                          link=frappe.utils.get_url('/thong-tin-dat-ban'), khoa='dat-ban-gan:%s' % r['name'],
                          kiem='dat_ban_cho', nguon=r['name'], ma_tin='bh_dat_ban_sap_toi')
    except Exception:
        frappe.log_error(frappe.get_traceback(), 'dat_ban: nhac sap toi')
