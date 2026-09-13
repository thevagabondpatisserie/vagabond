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
            if str(cu.get(ten)) != str(doc.get(ten)):
                frappe.throw('Giữ nguyên yêu cầu khách đã gửi. Ghi thay đổi vào ghi chú xử lý.')
        chuyen = {'Chờ xác nhận':{'Đã xác nhận','Đã hủy'}, 'Đã xác nhận':{'Đã đến','Đã hủy'}, 'Đã đến':set(), 'Đã hủy':set()}
        if doc.trang_thai != cu.trang_thai and doc.trang_thai not in chuyen.get(cu.trang_thai, set()):
            frappe.throw('Không thể chuyển ngược trạng thái. Ghi rõ kết quả trong ghi chú xử lý.')
    if doc.trang_thai not in TRANG_THAI:
        frappe.throw('Chọn trạng thái đặt bàn hợp lệ.')


def _loi_lark(ten):
    # Không đưa URL chứa khóa hoặc nội dung khách vào Error Log.
    frappe.log_error(title='Đặt bàn: chưa gửi được Lark',
                     message='Phiếu %s. Kiểm tra webhook nhóm đặt bàn và hàng đợi.' % ten)


def bao_dat_ban_moi(doc, method=None):
    """Chỉ móc after_insert; lỗi hàng đợi không làm mất yêu cầu khách."""
    if getattr(frappe.flags, 'vagabond_kiem_that', False):
        return
    try:
        if not frappe.db.get_single_value('Vagabond Settings', 'webhook_dat_ban'):
            return
        frappe.db.after_commit.add(partial(_xep_lark, doc.name))
    except Exception:
        _loi_lark(doc.name)


def _xep_lark(ten):
    # Frappe background_jobs.enqueue_after_commit chỉ hoãn q.enqueue_call;
    # CallbackManager.run không bắt lỗi Redis. Bao ở chính callback sau commit
    # để lỗi xếp hàng không đổi phản hồi thành thất bại sau khi phiếu đã lưu.
    try:
        frappe.enqueue('vagabond.dat_ban.gui_lark', ten=ten, queue='short')
    except Exception:
        _loi_lark(ten)
        # Chỉ chạy sau commit phiếu: giao dịch mới này chỉ lưu Error Log.
        frappe.db.commit()


def gui_lark(ten):
    """Đọc phiếu sau commit; Lark lỗi không tác động trạng thái đặt bàn."""
    from vagabond.gui_thu import ban_webhook
    if getattr(frappe.flags, 'vagabond_kiem_that', False):
        return
    try:
        url = str(frappe.db.get_single_value('Vagabond Settings', 'webhook_dat_ban') or '').strip()
        if not url:
            return
        doc = frappe.get_doc(DOCTYPE, ten).as_dict()
        doc['url'] = frappe.utils.get_url_to_form(DOCTYPE, ten)
        if not ban_webhook(soan_tin_dat_ban(doc), url=url):
            _loi_lark(ten)
    except Exception:
        _loi_lark(ten)
