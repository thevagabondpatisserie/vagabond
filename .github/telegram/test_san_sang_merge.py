"""Anh Việt 15/10/2026: báo Telegram khi bench xanh, PR đủ điều kiện merge."""
import copy
import unittest
from unittest.mock import patch

from thong_bao import Loi, chay, thu_thap, xet_san_sang_merge

SHA = 'a' * 40
SHA2 = 'b' * 40


def pr(sha=SHA, draft=False):
    return {'number': 477, 'title': 'v595 phát hành', 'draft': draft, 'head': {'sha': sha}}


def check(name, conclusion='success', status='completed', sha=SHA, at='2026-09-12T00:01:00Z'):
    return {'name': name, 'status': status, 'conclusion': conclusion, 'head_sha': sha, 'completed_at': at}


def du(sha=SHA):
    return [check('kiem-thu', sha=sha), check('claude-review', sha=sha), check('bench', sha=sha)]


def codex(sha=SHA, at='2026-09-12T00:01:30Z', dat=True):
    body = ("Codex Review: Didn't find any major issues. :rocket:" if dat else 'Codex Review: 2 góp ý') \
        + '\n\n**Reviewed commit:** `' + sha[:10] + '`'
    return {'user': {'login': 'chatgpt-codex-connector[bot]'}, 'created_at': at, 'body': body}


class Kho:
    """Nguồn giả: đúng các đường thu_thap gọi, kèm kho trạng thái như test_thong_bao."""
    def __init__(self):
        self.state = {'start': '2026-09-12T00:00:00Z', 'cursor': '2026-09-12T00:00:00Z', 'seen': {}, 'pending': None}
        self.sha = 0
        self.pr = pr()
        self.checks = du()
        self.chi_tiet = {'mergeable': True, 'state': 'open', 'draft': False, 'head': {'sha': SHA}}
        self.comments = []
        self.goi_den = []

    def doc(self):
        return copy.deepcopy(self.state), self.sha

    def luu(self, state, sha):
        if sha != self.sha:
            raise Loi('Xung đột')
        self.state = copy.deepcopy(state)
        self.sha += 1
        return self.sha

    def trang(self, path, *args):
        if path == '/pulls?state=open':
            return [self.pr]
        if path.startswith('/commits/'):
            return [c for c in self.checks if path == '/commits/' + c['head_sha'] + '/check-runs']
        if path == '/issues/477/comments':
            return self.comments
        return []

    def goi(self, path, *args, **kw):
        self.goi_den.append(path)
        return self.chi_tiet


class Bot:
    def __init__(self):
        self.sent = []

    def kiem_bot(self):
        pass

    def gui(self, chat, text, nhom=False):
        self.sent.append((chat, text))
        return len(self.sent)


class XetThuan(unittest.TestCase):
    def test_du_dieu_kien_va_codex_dat(self):
        kq = xet_san_sang_merge(pr(), du(), {'mergeable': True, 'state': 'open', 'head': {'sha': SHA}}, [codex()])
        self.assertIn('PR #477 đủ điều kiện merge', kq['text'])
        self.assertIn('Codex: đã rà đạt đúng SHA này.', kq['text'])
        self.assertIn('merge #477', kq['text'])
        self.assertEqual(kq['at'], '2026-09-12T00:01:30Z')

    def test_chua_du_thi_khong_bao(self):
        ok = {'mergeable': True, 'state': 'open', 'head': {'sha': SHA}}
        ca = {
            'bench đang chạy': (pr(), du()[:2] + [check('bench', None, 'in_progress')], ok),
            'bench đỏ': (pr(), du()[:2] + [check('bench', 'failure')], ok),
            'không có bench': (pr(), du()[:2], ok),
            'một check khác đỏ': (pr(), [check('kiem-thu', 'failure')] + du()[1:], ok),
            'xung đột': (pr(), du(), {'mergeable': False, 'state': 'open', 'head': {'sha': SHA}}),
            'GitHub chưa tính xong': (pr(), du(), {'mergeable': None, 'state': 'open', 'head': {'sha': SHA}}),
            'bản nháp': (pr(draft=True), du(), ok),
            'check của SHA cũ': (pr(), du(SHA2), ok),
            'PR đã đổi đầu giữa chừng': (pr(), du(), {'mergeable': True, 'state': 'open', 'head': {'sha': SHA2}}),
            # Codex 6f45f8f: PR đóng giữa lúc liệt kê và lúc đọc chi tiết.
            'PR vừa đóng': (pr(), du(), {'mergeable': True, 'state': 'closed', 'head': {'sha': SHA}}),
        }
        for ten, (p, c, ct) in ca.items():
            with self.subTest(ten):
                self.assertIsNone(xet_san_sang_merge(p, c, ct, []))

    def test_codex_dat_sha_khac_hoac_co_gop_y_khong_tinh(self):
        ok = {'mergeable': True, 'state': 'open', 'head': {'sha': SHA}}
        for cm in ([codex(SHA2)], [codex(dat=False)]):
            with self.subTest(cm[0]['body'][:20]):
                kq = xet_san_sang_merge(pr(), du(), ok, cm)
                self.assertIn('Codex: chưa báo rà đạt cho SHA này.', kq['text'])


class ThuThapVaGui(unittest.TestCase):
    def setUp(self):
        p = patch('thong_bao.gio', return_value='2026-09-12T00:02:00Z')
        p.start()
        self.addCleanup(p.stop)

    def test_mot_tin_moi_sha_them_tin_khi_codex_dat(self):
        kho, bot = Kho(), Bot()
        self.assertEqual(chay(kho, bot, '1'), 1)
        self.assertIn('đủ điều kiện merge', bot.sent[-1][1])
        self.assertIn('chưa báo rà đạt', bot.sent[-1][1])
        # Lượt sau không có gì mới: im lặng, kể cả khi seen đã bị tỉa.
        self.assertEqual(chay(kho, bot, '1'), 0)
        kho.state['seen'] = {}
        self.assertEqual(chay(kho, bot, '1'), 0)
        # Codex rà đạt sau: thêm đúng một tin.
        kho.comments = [codex()]
        self.assertEqual(chay(kho, bot, '1'), 1)
        self.assertIn('Codex: đã rà đạt', bot.sent[-1][1])
        # Đẩy SHA mới, bench xanh lại: tin mới cho SHA mới.
        kho.pr = pr(SHA2)
        kho.checks = du(SHA2)
        kho.chi_tiet = {'mergeable': True, 'state': 'open', 'head': {'sha': SHA2}}
        kho.comments = []
        self.assertEqual(chay(kho, bot, '1'), 1)
        self.assertIn(SHA2[:9], bot.sent[-1][1])

    def test_codex_p1_pr_dung_im_qua_30_ngay_khong_gui_lap(self):
        # Codex 6f45f8f: entity bị tỉa sau 30 ngày theo mốc at cũ thì mỗi lượt 15 phút gửi lại.
        kho, bot = Kho(), Bot()
        self.assertEqual(chay(kho, bot, '1'), 1)
        # Lượt đối soát chạy liên tục (cách nhau dưới 30 ngày) suốt hơn hai tháng.
        for ngay in ('2026-09-30', '2026-10-15', '2026-10-21', '2026-11-08', '2026-11-27', '2026-12-20'):
            with patch('thong_bao.gio', return_value=ngay + 'T00:02:00Z'):
                self.assertEqual(chay(kho, bot, '1'), 0, ngay)
        self.assertEqual(len(bot.sent), 1)

    def test_codex_p2_mat_phan_hoi_gui_lai_dung_tin_san_sang_merge(self):
        # Codex 8292a1d: Telegram đã nhận nhưng mất phản hồi; 10 phút sau phải gửi
        # lại đúng tin "đủ điều kiện merge", không phải câu "mất phản hồi" chung.
        class BotRot(Bot):
            def __init__(self):
                super().__init__()
                self.lan = 0
            def gui(self, chat, text, nhom=False):
                self.lan += 1
                self.sent.append((chat, text))
                if self.lan == 1:
                    raise Loi('Chưa rõ')
                return self.lan
        kho, bot = Kho(), BotRot()
        with self.assertRaises(Loi):
            chay(kho, bot, '1')
        self.assertTrue(kho.state['pending'])
        with patch('thong_bao.gio', return_value='2026-09-12T00:13:00Z'):
            chay(kho, bot, '1')
        self.assertEqual(len(bot.sent), 2)
        self.assertIn('(gửi lại)', bot.sent[1][1])
        self.assertIn('PR #477 đủ điều kiện merge', bot.sent[1][1])
        self.assertNotIn('mất phản hồi', bot.sent[1][1])

    def test_bench_chua_xong_khong_goi_chi_tiet_pr(self):
        kho = Kho()
        kho.checks = du()[:2] + [check('bench', None, 'in_progress')]
        self.assertEqual(thu_thap(kho, kho.state), {})
        self.assertEqual(kho.goi_den, [])

    def test_nhom_bo_phan_khong_nhan_tin_merge(self):
        kho, bot = Kho(), Bot()
        self.assertEqual(chay(kho, bot, '1', chat_nhom='-100'), 1)
        self.assertEqual([c for c, _ in bot.sent], ['1'])


if __name__ == '__main__':
    unittest.main()
