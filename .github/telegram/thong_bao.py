"""Issue287: báo việc cần xem trên mobile, không dùng model và không chép nội dung kín.

Dấu đang gửi được lưu TRƯỚC HTTP. Mất phản hồi thì giữ dấu để người vận hành
đối chiếu, không đoán là chưa gửi rồi gửi lặp. Nhánh trạng thái không được checkout.
"""
import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = 'thevagabondpatisserie/vagabond'
NHANH = 'codex/telegram-state'
TEP = '.telegram/state.json'
API = 'https://api.github.com/repos/' + REPO
WEB = 'https://github.com/' + REPO


def gio():
    return dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def lui(moc, giay):
    return (dt.datetime.fromisoformat(moc.replace('Z', '+00:00')) -
            dt.timedelta(seconds=giay)).strftime('%Y-%m-%dT%H:%M:%SZ')


def rut(chu, dai=180):
    return ' '.join(str(chu).split())[:dai]


def ma(gia_tri):
    return hashlib.sha256(json.dumps(gia_tri, sort_keys=True).encode()).hexdigest()[:24]


class Loi(Exception):
    pass


class HTTP:
    def goi(self, url, data=None, token=None, method=None):
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'Vagabond-Telegram'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        if data is not None:
            headers['Content-Type'] = 'application/json'
        try:
            req = urllib.request.Request(url, headers=headers,
                data=None if data is None else json.dumps(data).encode(), method=method)
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.load(r)
        except Exception as e:
            # URL Telegram chứa token: không in ngoại lệ gốc hay response body.
            so = e.code if isinstance(e, urllib.error.HTTPError) else 'khong-ro'
            raise Loi('Lỗi HTTP ' + str(so) + '; kiểm Actions và đối chiếu trước khi thử lại.') from None


class GitHub:
    def __init__(self, http, token):
        self.http, self.token = http, token

    def goi(self, path, data=None, method=None):
        return self.http.goi(API + path, data, self.token, method)

    def trang(self, path, khoa=None):
        ket = []
        for so in range(1, 11):
            sep = '&' if '?' in path else '?'
            kq = self.goi(path + sep + 'per_page=100&page=' + str(so))
            nhom = kq[khoa] if khoa else kq
            ket.extend(nhom)
            if len(nhom) < 100:
                return ket
        sep = '&' if '?' in path else '?'
        x = self.goi(path + sep + 'per_page=100&page=11')
        if not (x[khoa] if khoa else x):
            return ket
        raise Loi('Vượt 1000 bản ghi; giữ mốc cũ, cần thu hẹp hoặc chia lượt đối soát.')

    def doc(self):
        x = self.goi('/contents/' + TEP + '?ref=' + NHANH)
        if x.get('encoding') == 'none' or x.get('size', 0) > 1024 * 1024:
            # Contents API rỗng khi vượt1MB; đọc blob bất biến cùng SHA.
            blob = self.goi('/git/blobs/' + x['sha'])
            state = json.loads(base64.b64decode(blob['content']))
        else:
            state = json.loads(base64.b64decode(x['content']))
        return state, x['sha']

    def luu(self, state, sha):
        x = self.goi('/contents/' + TEP, {
            'branch': NHANH, 'message': 'Telegram: lưu dấu giao nhận',
            'sha': sha,
            'content': base64.b64encode(json.dumps(state, sort_keys=True).encode()).decode()
        }, 'PUT')
        return x['content']['sha']

    def khoi_tao(self):
        # Tạo nhánh phải thất bại nếu đã tồn tại; không ghi lại mốc nhận cũ.
        repo = self.goi('')
        ref = self.goi('/git/ref/heads/' + repo['default_branch'])
        self.goi('/git/refs', {'ref': 'refs/heads/' + NHANH, 'sha': ref['object']['sha']}, 'POST')
        now = gio()
        self.goi('/contents/' + TEP, {
            'branch': NHANH, 'message': 'Telegram: khởi tạo mốc nhận',
            'content': base64.b64encode(json.dumps({
                'start': now, 'cursor': now, 'seen': {}, 'entities': {}, 'pending': None
            }).encode()).decode()
        }, 'PUT')


class Telegram:
    def __init__(self, http, token):
        if not re.fullmatch(r'\d+:[A-Za-z0-9_-]+', token):
            raise Loi('Thiếu hoặc sai định dạng TELEGRAM_BOT_TOKEN.')
        self.http, self.token = http, token

    def goi(self, method, data=None):
        x = self.http.goi('https://api.telegram.org/bot' + self.token + '/' + method, data or {})
        if not x.get('ok'):
            raise Loi('Telegram từ chối; không tự gửi lại, kiểm cấu hình bot.')
        return x['result']

    def kiem_bot(self):
        if self.goi('getMe').get('username', '').lower() != 'vagabonderpbot':
            raise Loi('Secret không thuộc bot VagabondERPBot; dừng ghép/gửi.')

    def gui(self, chat, text):
        if not re.fullmatch(r'[1-9]\d*', str(chat)):
            raise Loi('Chỉ gửi tới private chat đã ghép.')
        x = self.goi('sendMessage', {'chat_id': str(chat), 'text': text,
            'link_preview_options': {'is_disabled': True}})
        if str(x.get('chat', {}).get('id')) != str(chat) or not x.get('message_id'):
            raise Loi('Phản hồi gửi không khớp; giữ trạng thái chưa rõ.')
        return x['message_id']


def thu_thap(gh, state):
    """Chỉ đọc metadata; nội dung comment, log và artifact không được chuyển đi."""
    since = urllib.parse.quote(lui(state['cursor'], 120), safe='')
    ket = {}

    def them(khoa, moc, text, entity=None, signature=None):
        if moc and moc >= state['start']:
            e = {'at': moc, 'text': text}
            if entity:
                e.update(entity=entity, signature=signature)
                e['silent'] = state.get('entities', {}).get(entity, {}).get('signature') == signature
            ket[khoa] = e

    for path, loai in [('/issues/comments', 'Comment'), ('/pulls/comments', 'Góp ý trên dòng code')]:
        for c in gh.trang(path + '?since=' + since + '&sort=updated&direction=asc'):
            link = c['html_url']
            # URL chỉ lấy từ API đúng repo, đồng thời chặn link lạc nơi nhận việc.
            if not link.startswith(WEB + '/'):
                raise Loi('Link comment ngoài repo; dừng đối soát.')
            nhan = ' (đã sửa)' if c['updated_at'] != c['created_at'] else ''
            dau = (c.get('body') or '').splitlines()[:1]
            muc = {'[CẦN DUYỆT]': 'Cần anh duyệt', '[BỊ CHẶN]': 'Tác vụ bị chặn',
                   '[SẴN SÀNG DEPLOY]': 'Đề nghị phát hành', '[ĐÃ DEPLOY]': 'Báo cáo phát hành'}
            nhom = muc.get(dau[0].strip() if dau else '', loai)
            text = f"Vagabond | {nhom}{nhan}\nTừ: {rut(c['user']['login'], 60)}\n{link}"
            entity = 'bot-comment:' + path + ':' + str(c['id'])
            la_bot = c['user'].get('type') == 'Bot' or c['user']['login'].endswith('[bot]')
            them('comment:' + path + ':' + str(c['id']) + ':' + c['updated_at'], c['updated_at'], text,
                 entity if la_bot else None, ma([re.sub(r'^([-*]\s+)\[[ xX]\]', r'\1[]', line.strip())
                     for line in (c.get('body') or '').splitlines() if line.strip()]))

    issues = gh.trang('/issues?state=all&sort=updated&direction=asc&since=' + since)
    prs = {p['number']: p for p in gh.trang('/pulls?state=open')}
    for i in issues:
        loai = 'PR' if 'pull_request' in i else 'Issue'
        if loai == 'PR':
            prs.setdefault(i['number'], i)
        labels = sorted(x['name'] for x in i.get('labels', []))
        merged = i.get('pull_request', {}).get('merged_at')
        draft = i.get('draft', prs.get(i['number'], {}).get('draft', False))
        tinh = [i['state'], labels, draft, merged, i['title']]
        text = f"Vagabond | {loai} #{i['number']}\n{rut(i['title'])}\nTrạng thái GitHub: {i['state']}"
        if labels:
            text += '\nNhãn: ' + rut(', '.join(labels))
        if loai == 'PR':
            text += '\nĐã merge (chưa chứng minh deploy).' if merged else ''
            text += '\nBản nháp.' if draft else ''
        text += f"\n{WEB}/{'pull' if loai == 'PR' else 'issues'}/{i['number']}"
        entity = 'item:' + str(i['id'])
        them(entity + ':' + i['updated_at'] + ':' + ma(tinh), i['updated_at'], text, entity, ma(tinh))
    for number in prs:
        for r in gh.trang('/pulls/' + str(number) + '/reviews'):
            if r['state'] == 'PENDING' or not r.get('submitted_at') or r['submitted_at'] < lui(state['cursor'], 120):
                continue
            them('review:' + str(r['id']) + ':' + r['state'], r.get('submitted_at'),
                 f"Vagabond | Review PR #{number}\nTừ: {rut(r['user']['login'], 60)}"
                 f"\nKết quả GitHub: {r['state']}\n{WEB}/pull/{number}#pullrequestreview-{r['id']}")
    # Quét cả lượt cũ chạy lại trong 7 ngày; thời gian gián đoạn dài lấy theo cursor.
    cua_run = min(lui(gio(), 7 * 86400), lui(state['cursor'], 120))
    moc = cua_run[:10]
    runs = []
    for status in ('failure', 'timed_out', 'action_required', 'startup_failure'):
        runs.extend(gh.trang('/actions/runs?status=' + status + '&created=' + urllib.parse.quote('>=' + moc), 'workflow_runs'))
    for r in runs:
        if r['updated_at'] < cua_run:
            continue
        if r['name'].startswith('Telegram') or r.get('conclusion') not in ('failure', 'timed_out', 'action_required', 'startup_failure'):
            continue
        them('run:' + str(r['id']) + ':' + str(r.get('run_attempt', 1)), r['updated_at'],
             f"Vagabond | Cần xem workflow\n{rut(r['name'])}: {r['conclusion']}"
             f"\nNhánh: {rut(r['head_branch'])}\n{WEB}/actions/runs/{r['id']}")
    return ket


def chay(gh, tg, chat, gom=False):
    if not re.fullmatch(r'[1-9]\d*', str(chat)):
        raise Loi('Thiếu TELEGRAM_CHAT_ID private; chưa ghi dấu gửi.')
    state, sha = gh.doc()
    if state['pending']:
        raise Loi('Có lần gửi chưa rõ kết quả. Đối chiếu mã sự kiện trong Telegram trước khi xử lý dấu pending.')
    moc = gio()
    han = time.monotonic() + 300
    if gom and state['cursor'] > lui(moc, 180):
        return 0
    state.setdefault('entities', {})
    events = thu_thap(gh, state)
    tg.kiem_bot()
    dem = 0
    for khoa, e in sorted(events.items(), key=lambda x: (x[1]['at'], x[0])):
        if khoa in state['seen']:
            continue
        # Giới hạn lượt, chưa đẩy cursor nên phần còn lại được đọc ở lượt sau.
        if e.get('silent'):
            state['entities'][e['entity']] = {'signature': e['signature'], 'at': e['at']}
            continue
        if dem == 30:
            return dem
        if time.monotonic() >= han:
            if dem == 0:
                raise Loi('Đọc nguồn quá5phút, còn tin chưa gửi; kiểm độ chậm API trước khi chạy lại.')
            return dem
        state['pending'] = {'key': khoa, 'at': e['at'], 'code': ma(khoa)}
        if e.get('entity'):
            state['pending'].update(entity=e['entity'], signature=e['signature'])
        sha = gh.luu(state, sha)
        tg.gui(chat, e['text'] + '\nMã tin: ' + ma(khoa))
        state['seen'][khoa] = e['at']
        if e.get('entity'):
            state['entities'][e['entity']] = {'signature': e['signature'], 'at': e['at']}
        state['pending'] = None
        sha = gh.luu(state, sha)
        dem += 1
    state['cursor'] = moc
    # Nguồn comment/item/review đã lọc since; run giữ đúng cửa7ngày.
    state['seen'] = {k: at for k, at in state['seen'].items()
                     if at >= lui(moc, 7 * 86400 if k.startswith('run:') else 120)}
    state['entities'] = {k: e for k, e in state['entities'].items()
                         if e['at'] >= lui(moc, 30 * 86400)}
    gh.luu(state, sha)
    return dem


def main():
    gh = GitHub(HTTP(), os.environ['GH_TOKEN'])
    if os.getenv('CHE_DO') == 'khoi-tao':
        gh.khoi_tao()
        print('Đã khởi tạo mốc; chưa gửi thông báo.')
        return
    dem = chay(gh, Telegram(HTTP(), os.environ.get('TELEGRAM_BOT_TOKEN', '')),
               os.environ.get('TELEGRAM_CHAT_ID', ''),
               gom=os.getenv('GITHUB_EVENT_NAME') != 'workflow_dispatch')
    print('Đã gửi ' + str(dem) + ' thông báo; không dùng model.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(str(e) if isinstance(e, Loi) else 'Lỗi khởi chạy (' + type(e).__name__ + '); kiểm cấu hình và dấu giao nhận.', file=sys.stderr)
        sys.exit(1)
