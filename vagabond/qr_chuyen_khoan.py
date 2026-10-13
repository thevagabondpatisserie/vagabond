"""PR474: dựng VietQR tại máy, không tải ảnh ở cửa thanh toán.

Chuỗi chuẩn đối chứng bằng ảnh tham chiếu TCV 160000/TCVG8FRJ.
Không đổi qr_text Pancake; không đoán BIN hay cắt mất nội dung đối soát.
"""
import base64
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import io
import re
import unicodedata


def crc16(chuoi):
    crc = 0xFFFF
    for b in chuoi.encode('utf-8'):
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ (0x1021 if crc & 0x8000 else 0)) & 0xFFFF
    return '%04X' % crc


def _truong(ma, gia_tri):
    if len(gia_tri.encode('utf-8')) > 99:
        raise ValueError('Nội dung chuyển khoản quá dài để tạo mã QR. Vui lòng chuyển tay với đầy đủ nội dung.')
    return ma + '%02d' % len(gia_tri.encode('utf-8')) + gia_tri


def chuoi(bin_, stk, tien=0, noi_dung='', qr_text=''):
    if qr_text:
        return str(qr_text)
    bin_ = str(bin_ or '').strip()
    stk = str(stk or '').strip()
    if not re.fullmatch(r'[0-9]{6}', bin_):
        raise ValueError('Thiếu hoặc sai mã BIN ngân hàng. Kiểm tra tài khoản nhận tiền.')
    if not re.fullmatch(r'[A-Za-z0-9]{1,34}', stk):
        raise ValueError('Thiếu hoặc sai số tài khoản nhận tiền. Kiểm tra tài khoản trước khi chuyển.')
    try:
        so = Decimal(str(tien))
        if not so.is_finite() or so < 0:
            raise ValueError()
        so = so.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        if not so.is_finite() or so < 0 or so > 9999999999999:
            raise ValueError()
    except (InvalidOperation, ValueError):
        raise ValueError('Số tiền không hợp lệ để tạo mã QR.')
    nd = ''.join(c for c in unicodedata.normalize('NFD', str(noi_dung or '').replace('đ','d').replace('Đ','D')) if unicodedata.category(c) != 'Mn')
    if any(ord(c) < 32 or ord(c) > 126 for c in nd):
        raise ValueError('Nội dung có ký tự chưa hỗ trợ trong mã QR. Vui lòng chuyển tay.')
    tk = _truong('00', bin_) + _truong('01', stk)
    ra = '0002010102' + ('12' if so else '11') + _truong('38', '0010A000000727' + _truong('01', tk) + '0208QRIBFTTA') + '5303704'
    if so:
        ra += _truong('54', str(int(so)))
    ra += '5802VN'
    if nd:
        ra += _truong('62', _truong('08', nd))
    ra += '6304'
    return ra + crc16(ra)


def anh(chuoi_qr):
    """pyqrcode đã có trong Frappe; SVG không cần thêm gói PNG hay mạng."""
    import pyqrcode
    bo = io.BytesIO()
    pyqrcode.create(chuoi_qr, error='M', mode='binary', encoding='utf-8').svg(bo, scale=5, quiet_zone=4)
    return 'data:image/svg+xml;base64,' + base64.b64encode(bo.getvalue()).decode('ascii')
