"""Anh Việt 15/10/2026: báo Telegram khi PR đủ điều kiện merge và deploy.

Lần 2 trong ngày anh chốt: chỉ báo khi ĐỦ để vào lệnh (bench, CI xanh, gồm main mới,
Codex rà đạt đúng SHA). PR có đổi app (thư mục vagabond/) thì tin ghi "merge và
deploy"; PR chỉ đổi .github/ hay docs/ thì ghi rõ không cần deploy app.
"""
import copy
import unittest
from unittest.mock import patch

from thong_bao import Loi, chay, thu_thap, xet_san_sang_merge

SHA = 'a' * 40
SHA2 = 'b' * 40
MAIN = 'c' * 40
MAIN2 = 'd' * 40


def ss(base=MAIN, behind=0, status='ahead'):
    """Phản hồi /compare/main...<sha> rút gọn: chỉ các trường máy đọc."""
    return {'status': status, 'behind_by': behind, 'ahead_by': 3, 'base_commit': {'sha': base}}


def pr(sha=SHA, draft=False):
    return {'number': 477, 'title': 'v595 phát hành', 'draft': draft, 'head': {'sha': sha}}


def check(name, conclusion='success', status='completed', sha=SHA, at='2026-09-12T00:01:00Z'):
    return {'name': name, 'status': status, 'conclusion': conclusion, 'head_sha': sha, 'completed_at': at}


APP = ['vagabond/public/js/bep/51-cai-dat-loi.js', 'vagabond/patches.txt']
KHONG_APP = ['.github/telegram/thong_bao.py', 'docs/thong-bao-telegram.md']


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
        self.chi_tiet = {'mergeable': True, 'state': 'open', 'draft': False, 'head': {'sha': SHA},
                         'base': {'ref': 'main'}}
        self.so_sanh = ss()
        self.comments = [codex()]
        self.tep = [{'filename': f} for f in APP]
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
        if path == '/pulls/477/files':
            return self.tep
        return []

    def goi(self, path, *args, **kw):
        self.goi_den.append(path)
        if path.startswith('/compare/'):
            return self.so_sanh
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
        kq = xet_san_sang_merge(pr(), du(), {'mergeable': True, 'state': 'open', 'head': {'sha': SHA}}, [codex()], ss(), APP)
        self.assertIn('PR #477 đủ điều kiện merge và deploy', kq['text'])
        self.assertIn('Codex rà đạt', kq['text'])
        self.assertIn('Vào Cowork nhắn: merge và deploy #477', kq['text'])
        self.assertEqual(kq['at'], '2026-09-12T00:01:30Z')

    def test_chi_doi_github_va_docs_thi_khong_can_deploy(self):
        # Anh Việt 15/10: PR như #479 (chỉ .github/ và docs/) merge xong là xong, không
        # có gì để deploy lên Frappe Cloud. Tin phải nói rõ, không bảo nhắn deploy.
        kq = xet_san_sang_merge(pr(), du(), {'mergeable': True, 'state': 'open', 'head': {'sha': SHA}}, [codex()], ss(), KHONG_APP)
        self.assertIn('PR #477 đủ điều kiện merge', kq['text'])
        self.assertIn('không cần deploy app', kq['text'])
        self.assertIn('Vào Cowork nhắn: merge #477', kq['text'])
        self.assertNotIn('deploy #477', kq['text'])

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
                self.assertIsNone(xet_san_sang_merge(p, c, ct, [codex()], ss(), APP))

    def test_codex_f5b07bb_chua_gom_main_moi_thi_khong_bao(self):
        ok = {'mergeable': True, 'state': 'open', 'head': {'sha': SHA}}
        ca = {
            'chậm hơn main': ss(MAIN2, behind=1, status='diverged'),
            'chỉ chậm, không có gì mới': ss(MAIN2, behind=1, status='behind'),
            'không đọc được so sánh': None,
            'so sánh thiếu SHA nền': {'status': 'ahead', 'behind_by': 0, 'base_commit': {}},
            'behind_by không rõ': {'status': 'ahead', 'base_commit': {'sha': MAIN}},
            'status lạ': ss(status='diverged'),
        }
        for ten, so in ca.items():
            with self.subTest(ten):
                self.assertIsNone(xet_san_sang_merge(pr(), du(), ok, [codex()], so, APP))
        for st in ('ahead', 'identical'):
            with self.subTest(st):
                self.assertIn('đã gồm main ' + MAIN[:9], xet_san_sang_merge(pr(), du(), ok, [codex()], ss(status=st), APP)['text'])
        # Biên nhận gồm SHA nền: cùng SHA đầu, nền khác thì chữ ký khác.
        self.assertNotEqual(xet_san_sang_merge(pr(), du(), ok, [codex()], ss(MAIN), APP)['signature'],
                            xet_san_sang_merge(pr(), du(), ok, [codex()], ss(MAIN2), APP)['signature'])

    def test_codex_chua_dat_dung_sha_thi_chua_bao(self):
        # Anh Việt 15/10 lần 2: tin là lúc anh vào lệnh được, nên Codex chưa rà đạt ĐÚNG
        # SHA đầu PR thì chưa báo (đạt SHA cũ, đang có góp ý, hay chưa rà).
        ok = {'mergeable': True, 'state': 'open', 'head': {'sha': SHA}}
        for ten, cm in (('đạt SHA khác', [codex(SHA2)]), ('có góp ý', [codex(dat=False)]), ('chưa rà', [])):
            with self.subTest(ten):
                self.assertIsNone(xet_san_sang_merge(pr(), du(), ok, cm, ss(), APP))


class ThuThapVaGui(unittest.TestCase):
    def setUp(self):
        p = patch('thong_bao.gio', return_value='2026-09-12T00:02:00Z')
        p.start()
        self.addCleanup(p.stop)

    def test_chi_bao_mot_tin_khi_du_ca_codex_moi_sha_mot_tin(self):
        kho, bot = Kho(), Bot()
        kho.comments = []
        # Bench, CI xanh mà Codex chưa rà đạt: im lặng.
        self.assertEqual(chay(kho, bot, '1'), 0)
        # Codex rà đạt đúng SHA: đúng một tin, ghi merge và deploy.
        kho.comments = [codex()]
        self.assertEqual(chay(kho, bot, '1'), 1)
        self.assertIn('đủ điều kiện merge và deploy', bot.sent[-1][1])
        # Lượt sau không có gì mới: im lặng, kể cả khi seen đã bị tỉa.
        self.assertEqual(chay(kho, bot, '1'), 0)
        kho.state['seen'] = {}
        self.assertEqual(chay(kho, bot, '1'), 0)
        # Đẩy SHA mới, bench xanh lại: chưa báo cho tới khi Codex đạt SHA mới.
        kho.pr = pr(SHA2)
        kho.checks = du(SHA2)
        kho.chi_tiet = {'mergeable': True, 'state': 'open', 'head': {'sha': SHA2}, 'base': {'ref': 'main'}}
        self.assertEqual(chay(kho, bot, '1'), 0)
        kho.comments = [codex(), codex(SHA2, at='2026-09-12T00:01:40Z')]
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

    def test_codex_f5b07bb_pr_cham_hon_main_khong_bao(self):
        # Codex f5b07bb: main tiến lên sau lượt bench của SHA đầu PR. GitHub vẫn báo
        # mergeable (không xung đột) và bench cũ vẫn xanh, nhưng PR CHƯA gồm main mới,
        # chưa được kiểm lại sau khi hợp nhất (AGENTS.md điều 2). Không được báo.
        kho, bot = Kho(), Bot()
        kho.so_sanh = ss(MAIN2, behind=2, status='diverged')
        self.assertEqual(chay(kho, bot, '1'), 0)
        self.assertEqual(bot.sent, [])
        # Merge main vào nhánh, bench chạy lại xanh trên SHA mới: lúc đó mới báo,
        # và tin ghi rõ main nào đã được gồm.
        kho.pr = pr(SHA2)
        kho.checks = du(SHA2)
        kho.chi_tiet = dict(kho.chi_tiet, head={'sha': SHA2})
        kho.so_sanh = ss(MAIN2)
        kho.comments = [codex(SHA2)]
        self.assertEqual(chay(kho, bot, '1'), 1)
        self.assertIn('đã gồm main ' + MAIN2[:9], bot.sent[-1][1])
        self.assertIn('/compare/main...' + SHA2 + '?per_page=1', kho.goi_den)

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
