"""Issue287: mất một biên nhận không được làm đứng kênh hoặc gửi lại vô hạn."""
import copy
import unittest
from unittest.mock import patch
from test_thong_bao import Kho, Bot
import test_thong_bao as cu
from thong_bao import chay, Telegram, Loi, HTTP
from ghep_chat import tim_chat


class PhucHoi(unittest.TestCase):
    def setUp(self):
        self.kho = Kho(); self.bot = Bot(self.kho)
        self.e = {'comment:/issues/comments:8:2026-09-12T00:01:00Z': {
            'at': '2026-09-12T00:01:00Z', 'text': 'Nội dung dành riêng',
            'entity': 'item:8', 'signature': 'abc'}}
        self.key = next(iter(self.e))
        self.moc = patch('thong_bao.gio', return_value='2026-09-12T02:00:00Z')
        self.clock = self.moc.start(); self.addCleanup(self.moc.stop)
        self.gom = patch('thong_bao.thu_thap', return_value=self.e)
        self.gom.start(); self.addCleanup(self.gom.stop)
    def hong_lan_dau(self):
        self.bot.loi = True
        with self.assertRaises(Loi): chay(self.kho, self.bot, '1')
        self.bot.loi = False
    def test_backlog_cu_nhung_pending_moi_khong_gui_lai(self):
        self.hong_lan_dau()
        self.clock.return_value = '2026-09-12T02:01:00Z'
        with self.assertRaises(Loi): chay(self.kho, self.bot, '1')
        self.assertEqual(len(self.bot.sent), 1)
        self.assertEqual(self.kho.state['pending']['ghi_luc'], '2026-09-12T02:00:00Z')
    def test_qua_10_phut_gui_lai_cap_nhat_entity_va_di_tiep(self):
        self.hong_lan_dau()
        self.clock.return_value = '2026-09-12T02:11:00Z'
        self.e['moi'] = {'at': '2026-09-12T02:10:00Z', 'text': 'Tin mới'}
        self.assertEqual(chay(self.kho, self.bot, '1'), 2)
        self.assertIn('(gửi lại)', self.bot.sent[1])
        self.assertEqual(self.kho.state['entities']['item:8']['signature'], 'abc')
        self.assertIsNone(self.kho.state['pending'])
    def test_mat_nguon_gui_tin_ngan_khong_chet(self):
        self.hong_lan_dau(); self.e.clear()
        self.clock.return_value = '2026-09-12T02:11:00Z'
        self.assertEqual(chay(self.kho, self.bot, '1'), 1)
        self.assertIn('mất phản hồi', self.bot.sent[-1])
        self.assertNotIn('Nội dung dành riêng', self.bot.sent[-1])
    def test_pending_legacy_bat_dau_dong_ho_moi(self):
        self.hong_lan_dau(); del self.kho.state['pending']['ghi_luc']
        self.clock.return_value = '2026-09-13T02:00:00Z'
        with self.assertRaises(Loi): chay(self.kho, self.bot, '1')
        self.assertEqual(len(self.bot.sent), 1)
        self.assertEqual(self.kho.state['pending']['ghi_luc'], self.clock.return_value)
    def test_chi_gui_lai_mot_lan_roi_giu_vet_khong_chan_tin_moi(self):
        self.hong_lan_dau(); self.bot.loi = True
        self.clock.return_value = '2026-09-12T02:11:00Z'
        with self.assertRaises(Loi): chay(self.kho, self.bot, '1')
        self.bot.loi = False; self.clock.return_value = '2026-09-12T02:22:00Z'
        self.e['moi'] = {'at': '2026-09-12T02:21:00Z', 'text': 'Tin mới'}
        self.assertEqual(chay(self.kho, self.bot, '1'), 1)
        self.assertIn(self.key, self.kho.state['can_doi_chieu'])
        self.assertEqual(len(self.bot.sent), 3)
        self.assertEqual(chay(self.kho, self.bot, '1'), 0)
    def test_put_seen_loi_receipt_giup_luot_sau_khong_gui_lap(self):
        luu = self.kho.luu
        def hong(s, sha):
            if s['pending'] is None: raise Loi('GitHub không ghi được seen')
            return luu(s, sha)
        with patch.object(self.kho, 'luu', side_effect=hong):
            with self.assertRaises(Loi): chay(self.kho, self.bot, '1')
        self.assertEqual(self.kho.state['pending']['message_id'], 1)
        self.assertEqual(chay(self.kho, self.bot, '1'), 0)
        self.assertEqual(len(self.bot.sent), 1)
    def test_put_da_commit_nhung_mat_phan_hoi_khong_gui_lap(self):
        luu = self.kho.luu
        def mat(s, sha):
            kq = luu(s, sha)
            if s.get('pending', {}).get('message_id') if s.get('pending') else False:
                raise Loi('GitHub timeout sau commit')
            return kq
        with patch.object(self.kho, 'luu', side_effect=mat):
            self.assertEqual(chay(self.kho, self.bot, '1'), 1)
        self.assertEqual(len(self.bot.sent), 1)
    def test_put_receipt_loi_mot_lan_thu_lai_khong_gui_http_lan_hai(self):
        luu = self.kho.luu; so = []
        def loi(s, sha):
            if s.get('pending') and s['pending'].get('message_id') and not so:
                so.append(1); raise Loi('GitHub tạm lỗi')
            return luu(s, sha)
        with patch.object(self.kho, 'luu', side_effect=loi):
            self.assertEqual(chay(self.kho, self.bot, '1'), 1)
        self.assertEqual(len(self.bot.sent), 1)
    def test_sha_doi_khong_ghi_de(self):
        luu = self.kho.luu
        def doi(s, sha):
            self.kho.sha += 1; self.kho.state['cua_nguoi_khac'] = 1
            raise Loi('SHA đổi')
        with patch.object(self.kho, 'luu', side_effect=doi):
            with self.assertRaises(Loi): chay(self.kho, self.bot, '1')
        self.assertEqual(self.bot.sent, [])
        self.assertEqual(self.kho.state['cua_nguoi_khac'], 1)


class Nhom(unittest.TestCase):
    def setUp(self):
        self.k = Kho()
        self.k.state['bo_phan'] = copy.deepcopy(self.k.state)
        self.sent = []
        class BotNhom:
            def kiem_bot(b): pass
            def gui(b, chat, text, nhom=False):
                s = self.k.state['bo_phan'] if nhom else self.k.state
                assert s['pending']
                self.sent.append((chat, text, nhom))
                if chat == '1' and self.hong: raise Loi('Timeout Telegram')
                if nhom and self.hong_nhom: raise Loi('Timeout nhóm')
                return len(self.sent)
        self.bot = BotNhom(); self.hong = False; self.hong_nhom = False
        self.events = {'release:a': {'at': '2026-09-12T00:01:00Z', 'text': 'Riêng https://github.com SHA',
            'text_nhom': 'Vagabond | Cập nhật v489 | 2026-09-12\n- Tính năng', 'entity': 'release:a', 'signature': 'sig'},
            'comment:b': {'at': '2026-09-12T00:01:01Z', 'text': 'Kỹ thuật'}}
        p=patch('thong_bao.thu_thap', return_value=self.events);p.start();self.addCleanup(p.stop)
        p=patch('thong_bao.gio', return_value='2026-09-12T00:02:00Z');self.clock=p.start();self.addCleanup(p.stop)
    def test_release_hai_chat_comment_chi_rieng_va_khong_lap(self):
        self.assertEqual(chay(self.k,self.bot,'1',chat_nhom='-1001'),3)
        nhom=[x for x in self.sent if x[2]]
        self.assertEqual(len(nhom),1)
        self.assertNotIn('github',nhom[0][1]);self.assertNotIn('SHA',nhom[0][1])
        self.assertEqual(chay(self.k,self.bot,'1',chat_nhom='-1001'),0)
        self.assertEqual(self.k.state['entities']['release:a']['signature'],'sig')
        self.assertEqual(self.k.state['bo_phan']['entities']['release:a']['signature'],'sig')
    def test_khong_secret_nhom_khong_loi(self):
        self.assertEqual(chay(self.k,self.bot,'1'),2)
        self.assertTrue(all(x[0]=='1' for x in self.sent))
    def test_private_pending_nhung_nhom_van_nhan(self):
        self.hong=True
        with self.assertRaises(Loi):chay(self.k,self.bot,'1',chat_nhom='-1001')
        self.assertTrue(self.k.state['pending'])
        self.assertIsNone(self.k.state['bo_phan']['pending'])
        self.assertEqual(len([x for x in self.sent if x[2]]),1)
    def test_nhom_mat_nguon_khong_gui_tin_ky_thuat(self):
        self.hong_nhom = True
        with self.assertRaises(Loi): chay(self.k,self.bot,'1',chat_nhom='-1001')
        self.events.clear(); self.hong_nhom = False
        self.clock.return_value = '2026-09-12T00:13:00Z'
        self.assertEqual(chay(self.k,self.bot,'1',chat_nhom='-1001'),0)
        self.assertEqual(len([x for x in self.sent if x[2]]),1)
        self.assertIn('release:a',self.k.state['bo_phan']['can_doi_chieu'])
        self.assertIsNone(self.k.state['bo_phan']['pending'])
    def test_nhom_hong_khong_chan_rieng_va_gui_lai_dung_features(self):
        self.hong_nhom = True
        with self.assertRaises(Loi): chay(self.k,self.bot,'1',chat_nhom='-1001')
        self.assertEqual(len([x for x in self.sent if not x[2]]),2)
        self.assertIsNone(self.k.state['pending'])
        self.assertTrue(self.k.state['bo_phan']['pending'])
        self.hong_nhom = False; self.clock.return_value = '2026-09-12T00:13:00Z'
        self.assertEqual(chay(self.k,self.bot,'1',chat_nhom='-1001'),1)
        tin=[x[1] for x in self.sent if x[2]][-1]
        self.assertEqual(tin,'(gửi lại)\n'+self.events['release:a']['text_nhom'])
        self.assertNotIn('github',tin)
    def test_nhom_hong_hai_lan_giu_vet_va_nhan_release_moi(self):
        self.hong_nhom = True
        with self.assertRaises(Loi): chay(self.k,self.bot,'1',chat_nhom='-1001')
        self.clock.return_value = '2026-09-12T00:13:00Z'
        with self.assertRaises(Loi): chay(self.k,self.bot,'1',chat_nhom='-1001')
        self.clock.return_value = '2026-09-12T00:24:00Z'; self.hong_nhom = False
        self.events.pop('comment:b')  # Nguồn thật đã lọc comment trước cursor.
        self.events['release:b'] = {'at':'2026-09-12T00:23:00Z','text':'Tin riêng mới',
            'text_nhom':'Tính năng mới','entity':'release:b','signature':'moi'}
        self.assertEqual(chay(self.k,self.bot,'1',chat_nhom='-1001'),2)
        self.assertIn('release:a',self.k.state['bo_phan']['can_doi_chieu'])
        self.assertEqual(len([x for x in self.sent if x[2]]),3)
        self.assertEqual(self.sent[-1][1],'Tính năng mới')
    def test_bot_kiem_phan_hoi_dung_chat_nhom(self):
        from unittest.mock import Mock
        h=Mock();h.goi.return_value={'ok':True,'result':{'message_id':7,'chat':{'id':-1001}}}
        self.assertEqual(Telegram(h,'1:abc').gui('-1001','Tin',nhom=True),7)
        with self.assertRaises(Loi):Telegram(h,'1:abc').gui('-1002','Tin',nhom=True)
    def test_nhom_ghi_moc_khi_gom_luot_dau(self):
        del self.k.state['bo_phan']
        chay(self.k,self.bot,'1',gom=True,chat_nhom='-1001')
        self.assertEqual(self.k.state['bo_phan']['start'],'2026-09-12T00:02:00Z')


class GhepNhom(unittest.TestCase):
    def test_chi_anh_viet_gui_ma_trong_dung_nhom(self):
        m=cu.Ghep().msg();m['message']['chat']={'id':-1001,'type':'supergroup'}
        self.assertEqual(tim_chat([m],cu.Ghep.code,100010,nguoi='17'),'-1001')
        with self.assertRaises(Loi):tim_chat([m],cu.Ghep.code,100010,nguoi='18')
        m['message']['forward_origin']={'type':'user'}
        with self.assertRaises(Loi):tim_chat([m],cu.Ghep.code,100010,nguoi='17')
    def test_loi_http_co_nguon_khong_co_token(self):
        with patch('urllib.request.urlopen',side_effect=OSError('SECRET')):
            with self.assertRaises(Loi) as e:HTTP().goi('https://api.telegram.org/botSECRET/sendMessage')
        self.assertIn('Telegram',str(e.exception));self.assertNotIn('SECRET',str(e.exception))

class MauNhom(unittest.TestCase):
    def test_ban_tin_that_tach_noi_dung_nhom(self):
        from thong_bao import thu_thap
        f=cu.PhatHanh(); f.setUp()
        try:
            f.comments=[f.comment()]
            e=next(iter(thu_thap(f.kho,f.kho.state).values()))
            self.assertIn('https://github.com', e['text'])
            self.assertNotIn('https://github.com', e['text_nhom'])
            self.assertNotIn('KHONG_GUI', e['text_nhom'])
            self.assertIn('2026-09-12', e['text_nhom'])
            self.assertIn(f.data['features'][0], e['text_nhom'])
        finally:f.doCleanups()
    def test_ghep_nhom_ma_hoa_id_am_va_khong_gui_rieng(self):
        from ghep_chat import ghep
        from unittest.mock import Mock
        from pathlib import Path
        import tempfile,json
        m=cu.Ghep().msg();m['message']['chat']={'id':-1001,'type':'supergroup'}
        tg=Mock();tg.goi.side_effect=[{},[m]]
        with tempfile.TemporaryDirectory() as d,patch('ghep_chat.time.time',return_value=100010):
            p=Path(d)/'id.json'
            def ma_hoa(key,raw):
                self.assertEqual(raw,b'-1001');return 'CIPHERTEXT'
            ghep(tg,cu.Ghep.code,'key','id',ma_hoa,p,nguoi='17')
            self.assertEqual(json.loads(p.read_text()),{'key_id':'id','encrypted_value':'CIPHERTEXT'})
        self.assertTrue(tg.gui.call_args.kwargs['nhom'])
