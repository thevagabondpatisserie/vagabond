"""Issue287: chỉ ghép private chat có mã dùng một lần do anh Việt gửi.

Artifact chỉ chứa chat ID đã mã hoá bằng public key của repository secret.
Người vận hành tải ciphertext và PUT vào TELEGRAM_CHAT_ID; không đọc token.
"""
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from thong_bao import HTTP, Loi, Telegram


def tim_chat(updates, code, now, nguoi=None):
    if not re.fullmatch(r'VGB-LINK-[A-F0-9]{10,64}', code):
        raise Loi('Mã ghép không đúng định dạng.')
    ds = set()
    for u in updates:
        m = u.get('message', {})
        chat = m.get('chat', {})
        loai_dung = (chat.get('type') in ('group', 'supergroup') and str(chat.get('id', '')).startswith('-')
                     if nguoi else chat.get('type') == 'private')
        tac_gia = str(m.get('from', {}).get('id')) == str(nguoi or chat.get('id'))
        if (m.get('text') == code and loai_dung
                and not m.get('forward_origin') and not m.get('via_bot')
                and tac_gia
                and not m.get('from', {}).get('is_bot')
                and now - 86400 <= m.get('date', 0) <= now + 60):
            ds.add(chat['id'])
    if len(ds) != 1:
        raise Loi('Chưa có đúng một chat khớp mã, loại và người ghép trong24giờ; không tự chọn chat.')
    return str(ds.pop())


def ghep(tg, code, key, key_id, encrypt, path, nguoi=None):
    tg.kiem_bot()
    if tg.goi('getWebhookInfo').get('url'):
        raise Loi('Bot có webhook khác; không xoá webhook để ghép.')
    updates = tg.goi('getUpdates', {'limit': 100, 'timeout': 0})
    if len(updates) == 100:
        raise Loi('Hàng đợi đủ100 tin; cần kiểm riêng, không tự bỏ tin cũ.')
    chat = tim_chat(updates, code, time.time(), nguoi=nguoi)
    cipher = encrypt(key, chat.encode())
    Path(path).write_text(json.dumps({'key_id': key_id, 'encrypted_value': cipher}))
    tin = 'VagabondERPBot đã xác minh đúng chat.\nĐây là tin ghép nối, chưa phải xác nhận hệ thống thông báo đã bật.'
    if nguoi:
        tg.gui(chat, tin, nhom=True)
    else:
        tg.gui(chat, tin)


def main():
    from nacl.public import PublicKey, SealedBox
    from nacl.encoding import Base64Encoder
    def encrypt(key, raw):
        return base64.b64encode(SealedBox(PublicKey(key, Base64Encoder)).encrypt(raw)).decode()
    loai = os.getenv('LOAI_CHAT', 'rieng')
    if loai not in ('rieng', 'bo-phan'):
        raise Loi('Loại chat không hợp lệ.')
    nguoi = os.getenv('TELEGRAM_CHAT_ID', '') if loai == 'bo-phan' else None
    if loai == 'bo-phan' and not re.fullmatch(r'[1-9]\d*', nguoi):
        raise Loi('Cần ghép private chat của anh Việt trước khi ghép nhóm.')
    ghep(Telegram(HTTP(), os.environ.get('TELEGRAM_BOT_TOKEN', '')),
         os.environ['MA_GHEP'], os.environ['PUBLIC_KEY'], os.environ['KEY_ID'],
         encrypt, 'chat-encrypted.json', nguoi=nguoi)
    print('Đã ghép; artifact ciphertext cho ' + ('TELEGRAM_CHAT_ID_BO_PHAN' if nguoi else 'TELEGRAM_CHAT_ID') + '.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(str(e) if isinstance(e, Loi) else 'Ghép thất bại; không in dữ liệu riêng.', file=sys.stderr)
        sys.exit(1)
