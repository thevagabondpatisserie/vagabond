"""Issue287: giữ ranh giới giao nhận, không chỉ dò chữ trong workflow."""
import copy
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from thong_bao import HTTP, GitHub, Loi, Telegram, chay, thu_thap
from ghep_chat import tim_chat, ghep


class Kho:
    def __init__(self):
        self.state = {'start': '2026-09-12T00:00:00Z', 'cursor': '2026-09-12T00:00:00Z', 'seen': {}, 'pending': None}
        self.sha = 0
        self.writes = []
    def doc(self):
        return copy.deepcopy(self.state), self.sha
    def luu(self, state, sha):
        if sha != self.sha:
            raise Loi('Xung đột')
        self.state = copy.deepcopy(state)
        self.writes.append(copy.deepcopy(state))
        self.sha += 1
        return self.sha


class Bot:
    def __init__(self, kho, loi=False):
        self.kho, self.loi, self.sent = kho, loi, []
    def kiem_bot(self): pass
    def gui(self, chat, text):
        assert self.kho.state['pending'], 'Chưa lưu ý định trước HTTP'
        self.sent.append(text)
        if self.loi:
            raise Loi('Chưa rõ')
        return 1


class GiaoNhan(unittest.TestCase):
    def events(self, n=1):
        return {str(i): {'at': '2026-09-12T00:01:00Z', 'text': 'Tin'} for i in range(n)}
    def test_chat_sai_khong_de_lai_pending(self):
        kho = Kho(); bot = Bot(kho)
        with self.assertRaises(Loi): chay(kho, bot, '')
        self.assertEqual(kho.writes, [])
        self.assertEqual(bot.sent, [])
    def test_hai_luot_khong_gui_lap(self):
        kho = Kho(); bot = Bot(kho)
        with patch('thong_bao.thu_thap', return_value=self.events()):
            self.assertEqual(chay(kho, bot, '1'), 1)
            self.assertEqual(chay(kho, bot, '1'), 0)
        self.assertEqual(len(bot.sent), 1)
        self.assertIsNone(kho.state['pending'])
    def test_mat_phan_hoi_khong_gui_lai(self):
        kho = Kho(); bot = Bot(kho, True)
        with patch('thong_bao.thu_thap', return_value=self.events()):
            with self.assertRaises(Loi): chay(kho, bot, '1')
            with self.assertRaises(Loi): chay(kho, bot, '1')
        self.assertEqual(len(bot.sent), 1)
        self.assertTrue(kho.state['pending'])
    def test_luu_ket_qua_hong_giu_pending(self):
        kho = Kho(); bot = Bot(kho)
        luu = kho.luu
        def hong(s, sha):
            if not s['pending']: raise Loi('HTTP ghi kết quả lỗi')
            return luu(s, sha)
        with patch.object(kho, 'luu', side_effect=hong), patch('thong_bao.thu_thap', return_value=self.events()):
            with self.assertRaises(Loi): chay(kho, bot, '1')
        self.assertTrue(kho.state['pending'])
        self.assertEqual(len(bot.sent), 1)
    def test_luu_y_dinh_hong_khong_gui(self):
        kho = Kho(); bot = Bot(kho)
        with patch.object(kho, 'luu', side_effect=Loi('HTTP')), patch('thong_bao.thu_thap', return_value=self.events()):
            with self.assertRaises(Loi): chay(kho, bot, '1')
        self.assertEqual(bot.sent, [])
    def test_gioi_han_khong_mat_phan_con_lai(self):
        kho = Kho(); bot = Bot(kho); cursor = kho.state['cursor']
        with patch('thong_bao.thu_thap', return_value=self.events(31)):
            self.assertEqual(chay(kho, bot, '1'), 30)
            self.assertEqual(kho.state['cursor'], cursor)
            self.assertEqual(chay(kho, bot, '1'), 1)
        self.assertEqual(len(bot.sent), 31)
    def test_doc_nguon_loi_khong_day_cursor(self):
        kho = Kho(); bot = Bot(kho); before = copy.deepcopy(kho.state)
        with patch('thong_bao.thu_thap', side_effect=Loi('API')):
            with self.assertRaises(Loi): chay(kho, bot, '1')
        self.assertEqual(before, kho.state)


class Mang(unittest.TestCase):
    def test_http_khong_ro_token_body(self):
        with patch('urllib.request.urlopen', side_effect=OSError('https://token SECRET BODY')):
            with self.assertRaises(Loi) as c: HTTP().goi('https://api.telegram.org/botSECRET/getMe')
        self.assertNotIn('SECRET', str(c.exception))
        self.assertNotIn('BODY', str(c.exception))
    def test_telegram_false_la_loi(self):
        http = unittest.mock.Mock(); http.goi.return_value = {'ok': False, 'description': 'SECRET'}
        with self.assertRaises(Loi): Telegram(http, '1:abc').gui('10', 'Tin')
    def test_khong_gui_group(self):
        http = unittest.mock.Mock()
        with self.assertRaises(Loi): Telegram(http, '1:abc').gui('-10012', 'Tin')
        http.goi.assert_not_called()
    def test_sai_bot(self):
        http = unittest.mock.Mock(); http.goi.return_value = {'ok': True, 'result': {'username': 'other'}}
        with self.assertRaises(Loi): Telegram(http, '1:abc').kiem_bot()
    def test_phan_trang_day_bao_loi(self):
        http = unittest.mock.Mock(); http.goi.return_value = [{}] * 100
        with self.assertRaises(Loi): GitHub(http, 'x').trang('/issues')
        self.assertEqual(http.goi.call_count, 10)


class Ghep(unittest.TestCase):
    code = 'VGB-LINK-123456ABCDEF'
    def msg(self, chat=17):
        return {'message': {'text': self.code, 'date': 100000, 'chat': {'id': chat, 'type': 'private'}, 'from': {'id': chat, 'is_bot': False}}}
    def test_dung_ma_va_private(self):
        self.assertEqual(tim_chat([self.msg()], self.code, 100010), '17')
    def test_hai_chat_khong_tu_chon(self):
        with self.assertRaises(Loi): tim_chat([self.msg(), self.msg(18)], self.code, 100010)
    def test_sai_ma_group_forward_het_han(self):
        for field, value in [('text', 'other'), ('chat', {'id': -1, 'type': 'group'}), ('forward_origin', {'type': 'user'}), ('date', 1)]:
            x = self.msg(); x['message'][field] = value
            with self.subTest(field=field), self.assertRaises(Loi): tim_chat([x], self.code, 100010)
    def test_khong_xoa_webhook(self):
        bot = unittest.mock.Mock(); bot.goi.return_value = {'url': 'https://other'}
        with self.assertRaises(Loi): ghep(bot, self.code, 'key', 'id', None, '/tmp/no-write')
        bot.goi.assert_called_once_with('getWebhookInfo')
    def test_artifact_chi_chua_ciphertext(self):
        bot = unittest.mock.Mock(); bot.goi.side_effect = [{}, [self.msg()]]
        with tempfile.TemporaryDirectory() as d, patch('ghep_chat.time.time', return_value=100010):
            path = Path(d)/'chat.json'
            ghep(bot, self.code, 'key', 'id', lambda k, raw: 'ENCRYPTED', path)
            self.assertEqual(json.loads(path.read_text()), {'key_id': 'id', 'encrypted_value': 'ENCRYPTED'})
        bot.gui.assert_called_once()


class ThuThap(unittest.TestCase):
    def test_noi_dung_kin_khong_gui_va_comment_bot_van_doc(self):
        gh = unittest.mock.Mock()
        c = {'id': 8, 'created_at': '2026-09-12T00:01:00Z', 'updated_at': '2026-09-12T00:02:00Z',
             'html_url': 'https://github.com/thevagabondpatisserie/vagabond/issues/287#issuecomment-8',
             'user': {'login': 'github-actions[bot]'}, 'body': '[CẦN DUYỆT]\nSECRET tài khoản số...'}
        gh.trang.side_effect = lambda path, *args: [c] if path.startswith('/issues/comments') else []
        events = thu_thap(gh, Kho().state)
        text = next(iter(events.values()))['text']
        self.assertIn('Cần anh duyệt', text)
        self.assertIn('github-actions[bot]', text)
        self.assertNotIn('SECRET', text)
        self.assertEqual(len(events), 1)
    def test_truoc_moc_khong_phat_lai(self):
        gh = unittest.mock.Mock()
        c = {'id': 8, 'created_at': '2026-09-11T00:00:00Z', 'updated_at': '2026-09-11T00:00:00Z',
             'html_url': 'https://github.com/thevagabondpatisserie/vagabond/issues/287#issuecomment-8',
             'user': {'login': 'bot'}, 'body': 'old'}
        gh.trang.side_effect = lambda path, *args: [c] if path.startswith('/issues/comments') else []
        self.assertEqual(thu_thap(gh, Kho().state), {})


if __name__ == '__main__': unittest.main()
