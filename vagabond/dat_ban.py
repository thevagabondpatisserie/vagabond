"""#245: nhận yêu cầu đặt bàn, nhân viên xác nhận sau khi kiểm chỗ tại tiệm.

Không coi gửi form là đã có bàn. Lịch mở được quản lý riêng; mặc định tắt
cho tới khi quản lý chọn cơ sở và khung giờ thật.
"""
# phần thuần
import hashlib
import json
import re
from datetime import datetime, timedelta

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
    return {'ten':ten, 'sdt':sdt, 'co_so':cau_hinh['co_so'], 'ngay':str(ngay), 'gio':gio, 'so_khach':so, 'ghi_chu':ghi_chu}


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
            'toi_da_khach':d.toi_da_khach or 8, 'toi_da_ngay':d.toi_da_ngay or 30}


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
    d.insert(ignore_permissions=True)
    return {'ok':1, 'ma':d.name[:12].upper(), 'trang_thai':'Chờ xác nhận'}


def kiem_phieu(doc):
    if doc.is_new():
        if doc.trang_thai != 'Chờ xác nhận':
            frappe.throw('Yêu cầu mới phải bắt đầu ở trạng thái Chờ xác nhận.')
        try:
            chuan_hoa(doc.as_dict(), _cau_hinh(), frappe.utils.now_datetime())
        except ValueError as e:
            frappe.throw(str(e))
    cu = doc.get_doc_before_save()
    if cu:
        for ten in ('ten', 'sdt', 'ngay', 'gio', 'so_khach', 'co_so', 'bam_noi_dung'):
            if str(cu.get(ten)) != str(doc.get(ten)):
                frappe.throw('Giữ nguyên yêu cầu khách đã gửi. Ghi thay đổi vào ghi chú xử lý.')
        chuyen = {'Chờ xác nhận':{'Đã xác nhận','Đã hủy'}, 'Đã xác nhận':{'Đã đến','Đã hủy'}, 'Đã đến':set(), 'Đã hủy':set()}
        if doc.trang_thai != cu.trang_thai and doc.trang_thai not in chuyen.get(cu.trang_thai, set()):
            frappe.throw('Không thể chuyển ngược trạng thái. Ghi rõ kết quả trong ghi chú xử lý.')
    if doc.trang_thai not in TRANG_THAI:
        frappe.throw('Chọn trạng thái đặt bàn hợp lệ.')
