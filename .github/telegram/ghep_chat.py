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


def tim_chat(updates, code, now):
    if not re.fullmatch(r'VGB-LINK-[A-F0-9]{12,64}', code):
        raise Loi('Mã ghép không đúng định dạng.')
    ds = set()
    for u in updates:
        m = u.get('message', {})
        chat = m.get('chat', {})
        if (m.get('text') == code and chat.get('type') == 'private'
                and not m.get('forward_origin') and not m.get('via_bot')
                and m.get('from', {}).get('id') == chat.get('id')
                and not m.get('from', {}).get('is_bot')
                and now - 86400 <= m.get('date', 0) <= now + 60):
            ds.add(chat['id'])
    if len(ds) != 1:
        raise Loi('Chưa có đúng một private chat khớp mã trong 24 giờ; không tự chọn chat.')
    return str(ds.pop())


def ghep(tg, code, key, key_id, encrypt, path):
    tg.kiem_bot()
    if tg.goi('getWebhookInfo').get('url'):
        raise Loi('Bot có webhook khác; không xoá webhook để ghép.')
    updates = tg.goi('getUpdates', {'limit': 100, 'timeout': 0})
    if len(updates) == 100:
        raise Loi('Hàng đợi đủ100 tin; cần kiểm riêng, không tự bỏ tin cũ.')
    chat = tim_chat(updates, code, time.time())
    cipher = encrypt(key, chat.encode())
    Path(path).write_text(json.dumps({'key_id': key_id, 'encrypted_value': cipher}))
    tg.gui(chat, 'VagabondERPBot đã xác minh đúng chat của anh.\n'
           'Đây là tin ghép nối, chưa phải xác nhận hệ thống thông báo đã bật.')


def main():
    from nacl.public import PublicKey, SealedBox
    from nacl.encoding import Base64Encoder
    def encrypt(key, raw):
        return base64.b64encode(SealedBox(PublicKey(key, Base64Encoder)).encrypt(raw)).decode()
    ghep(Telegram(HTTP(), os.environ.get('TELEGRAM_BOT_TOKEN', '')),
         os.environ['MA_GHEP'], os.environ['PUBLIC_KEY'], os.environ['KEY_ID'],
         encrypt, 'chat-encrypted.json')
    print('Đã ghép; artifact chỉ chứa ciphertext để lưu TELEGRAM_CHAT_ID.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(str(e) if isinstance(e, Loi) else 'Ghép thất bại; không in dữ liệu riêng.', file=sys.stderr)
        sys.exit(1)
