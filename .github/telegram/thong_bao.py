"""Issue287: báo việc cần xem trên mobile, không dùng model và không chép nội dung kín.

Dấu đang gửi được lưu TRƯỚC HTTP. Sau10phút chỉ thử lại một lần có nhãn;
chấp nhận trùng tin thông báo theo duyệt287, không áp dụng cho chứng từ. Nhánh trạng thái không được checkout.
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
            nguon = 'Telegram' if url.startswith('https://api.telegram.org/') else 'GitHub'
            raise Loi('Lỗi HTTP ' + str(so) + ' từ ' + nguon + '; kiểm Actions và đối chiếu trước khi thử lại.') from None


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

    def gui(self, chat, text, nhom=False):
        if not re.fullmatch(r'-[1-9]\d*' if nhom else r'[1-9]\d*', str(chat)):
            raise Loi('Chỉ gửi tới đúng loại chat đã ghép.')
        x = self.goi('sendMessage', {'chat_id': str(chat), 'text': text,
            'link_preview_options': {'is_disabled': True}})
        if str(x.get('chat', {}).get('id')) != str(chat) or not x.get('message_id'):
            raise Loi('Phản hồi gửi không khớp; giữ trạng thái chưa rõ.')
        return x['message_id']



def ban_can_duyet(c):
    """Chỉ gửi phần phương án chủ repo soạn riêng, không sao chép log/comment."""
    body = c.get('body') or ''
    if (c.get('user', {}).get('login') != REPO.split('/')[0]
            or c.get('author_association') != 'OWNER'
            or not body.splitlines() or body.splitlines()[0].strip() != '[CẦN DUYỆT]'):
        return None
    blocks = re.findall(r'<!-- telegram-approval\s*([\s\S]*?)-->', body)
    if len(blocks) != 1 or len(blocks[0]) > 2500:
        return None
    try:
        x = json.loads(blocks[0])
    except (ValueError, TypeError):
        return None
    keys = ('van_de', 'de_xuat', 'anh_huong', 'cau_hoi')
    if not isinstance(x, dict) or set(x) != set(keys):
        return None
    if any(not isinstance(x[k], str) or not x[k].strip() or len(x[k]) > 500 or any(ord(ch) < 32 for ch in x[k]) for k in keys):
        return None
    return '\n'.join(label + ': ' + x[k].strip() for k, label in zip(keys,
        ('Việc cần quyết', 'Em đề xuất', 'Ảnh hưởng', 'Anh duyệt giúp')))


def tom_tat_comment(c):
    """Chỉ đọc khối ngắn do chủ repo HOẶC bot Codex soạn, không suy tóm tắt từ log.

    Codex #478 (8b3703d): phân công 15/10 bắt Codex đính khối telegram-tomtat vào
    kết luận rà soát; trước đây khối từ bot bị bỏ nên tin mất phần kết luận
    nghiệp vụ. Tên đăng nhập kết thúc bằng [bot] là tài khoản ứng dụng GitHub,
    người ngoài không mạo danh được."""
    u = c.get('user', {})
    la_chu = u.get('login') == REPO.split('/')[0] and c.get('author_association') == 'OWNER'
    la_codex = u.get('login') == CODEX and u.get('type', 'Bot') == 'Bot'
    if not (la_chu or la_codex):
        return None, False
    body = c.get('body') or ''
    blocks = re.findall(r'<!-- telegram-tomtat\s*([\s\S]*?)-->', body)
    if len(blocks) != 1 or len(blocks[0]) > 1000:
        return None, True
    try:
        x = json.loads(blocks[0])
    except (ValueError, TypeError):
        return None, True
    keys = ('tom_tat', 'tiep_theo')
    if (not isinstance(x, dict) or set(x) != set(keys)
            or any(not isinstance(x[k], str) or not x[k].strip()
                   or len(x[k]) > 220 or any(not ch.isprintable() for ch in x[k])
                   for k in keys)):
        return None, True
    return 'Tóm tắt: ' + x['tom_tat'].strip() + '\nTiếp theo: ' + x['tiep_theo'].strip(), True


def tom_tat_codex(c):
    """Lấy đúng ý đầu của Summary, không để link hoặc định dạng lọt vào tin."""
    if c.get('user', {}).get('login') != 'chatgpt-codex-connector[bot]':
        return None
    trong_summary = False
    for line in (c.get('body') or '').splitlines():
        if re.match(r'^\s{0,3}#{1,6}\s+Summary\s*$', line, re.IGNORECASE):
            trong_summary = True
            continue
        if trong_summary and re.match(r'^\s{0,3}#{1,6}\s+', line):
            break
        if trong_summary and re.match(r'^\s*[-*+]\s+', line):
            chu = re.sub(r'^\s*[-*+]\s+', '', line)
            chu = re.sub(r'!\[([^]]*)\]\([^)]*\)', r'\1', chu)
            chu = re.sub(r'\[([^]]+)\]\([^)]*\)', r'\1', chu)
            chu = re.sub(r'<https?://[^>]+>', '', chu)
            chu = re.sub(r'https?://\S+', '', chu)
            chu = re.sub(r'<[^>]+>', '', chu)
            chu = re.sub(r'[`*_~>#]', '', chu)
            return rut(chu, 200) or None
    return None


def ban_phat_hanh(c):
    """Chỉ chuyển bản tin được chủ repo soạn riêng cho Telegram sau kiểm live.

    Đây là biên nhận của người phát hành, không phải bot tự kiểm Cloud.
    Không lấy các đoạn văn/log còn lại trong comment làm nội dung gửi.
    """
    body = c.get('body') or ''
    if (c.get('user', {}).get('login') != REPO.split('/')[0]
            or c.get('author_association') != 'OWNER'
            or not body.splitlines() or body.splitlines()[0].strip() != '[ĐÃ DEPLOY]'):
        return None
    blocks = re.findall(r'<!-- telegram-release\s*([\s\S]*?)-->', body)
    if len(blocks) != 1 or len(blocks[0]) > 3000:
        return None
    try:
        x = json.loads(blocks[0])
    except (ValueError, TypeError):
        return None
    if not isinstance(x, dict) or set(x) != {'version', 'sha', 'features', 'live_verified'}:
        return None
    if (x['live_verified'] is not True or not isinstance(x['version'], str)
            or not re.fullmatch(r'v[1-9][0-9]{0,7}', x['version'])
            or not isinstance(x['sha'], str) or not re.fullmatch(r'[0-9a-f]{40}', x['sha'])):
        return None
    features = x['features']
    if (not isinstance(features, list) or not 1 <= len(features) <= 5
            or any(not isinstance(f, str) or not f.strip() or len(f) > 220
                   or any(ord(ch) < 32 for ch in f) for f in features)):
        return None
    return x


CODEX = 'chatgpt-codex-connector[bot]'
CHECK_DAT = ('success', 'neutral', 'skipped')


# Thư mục mà đổi trong đó KHÔNG cần deploy app lên Frappe Cloud (Codex 8050470).
KHONG_DEPLOY = ('.github/', 'docs/')


def xet_san_sang_merge(pr, checks, chi_tiet, comments, so_sanh, tep):
    """PR đủ điều kiện merge (và deploy) chưa. Hàm THUẦN, không gọi mạng.

    Đủ khi: không phải bản nháp, GitHub báo merge được (không xung đột), có
    check `bench` xanh và MỌI check trên đúng SHA đầu PR đã xong và đạt, VÀ SHA
    đầu PR đã gồm đầu nhánh nền hiện tại (`so_sanh` là /compare/<nền>...<sha>,
    behind_by == 0). Codex f5b07bb: mergeable chỉ nói không xung đột; PR chậm hơn
    main thì bench xanh là bench của bản chưa hợp nhất, chưa được báo.
    Anh Việt 15/10/2026 (lần 2): chỉ báo khi ĐỦ để vào lệnh, nên Codex phải rà đạt
    ĐÚNG SHA đầu PR ("Didn't find any major issues" kèm SHA). `tep` là danh sách
    tên tệp PR đổi: mọi tệp đều trong .github/ hoặc docs/ thì merge là xong, tin nói
    không cần deploy; còn lại (app, pyproject.toml, requirements.txt...) ghi "merge và
    deploy".
    Trả None hoặc dict(at, text, signature).
    """
    sha = (pr.get('head') or {}).get('sha') or ''
    if not re.fullmatch(r'[0-9a-f]{40}', sha) or pr.get('draft') or chi_tiet.get('draft'):
        return None
    if (chi_tiet.get('state') != 'open' or chi_tiet.get('mergeable') is not True
            or (chi_tiet.get('head') or {}).get('sha') != sha):
        return None
    if not checks or any(c.get('head_sha', sha) != sha for c in checks):
        return None
    if any(c.get('status') != 'completed' or c.get('conclusion') not in CHECK_DAT for c in checks):
        return None
    if not any(c.get('name') == 'bench' and c.get('conclusion') == 'success' for c in checks):
        return None
    nen = ((so_sanh or {}).get('base_commit') or {}).get('sha') or ''
    if (not re.fullmatch(r'[0-9a-f]{40}', nen) or (so_sanh or {}).get('behind_by') != 0
            or so_sanh.get('status') not in ('ahead', 'identical')):
        return None
    at = max(c.get('completed_at') or '' for c in checks)
    codex = None
    for c in comments:
        body = c.get('body') or ''
        if (c.get('user', {}).get('login') == CODEX and sha[:10] in body
                and "Didn't find any major issues" in body):
            codex = c.get('created_at') or ''
    if not codex:
        return None
    at = max(at, codex)
    so = pr['number']
    # Codex 8050470: chỉ PR mà MỌI tệp nằm trong vùng an toàn mới không cần deploy.
    # Tệp gốc như pyproject.toml, requirements.txt đổi môi trường cài trên Frappe Cloud;
    # danh sách rỗng (không đọc được) cũng coi là cần deploy.
    can_deploy = not tep or not all(str(f or '').startswith(KHONG_DEPLOY) for f in tep)
    text = (f"Vagabond | PR #{so} đủ điều kiện merge" + (' và deploy' if can_deploy else ' (không cần deploy app)')
            + f"\n{rut(pr.get('title', ''))}"
            f"\nBench và CI xanh, Codex rà đạt, không xung đột, đã gồm main {nen[:9]}. SHA {sha[:9]}."
            + f"\nVào Cowork nhắn: merge{' và deploy' if can_deploy else ''} #{so}\n{WEB}/pull/{so}")
    return {'at': at, 'text': text, 'signature': ma([sha, nen, can_deploy])}


def thu_thap(gh, state):
    """Metadata hoặc bản tin phát hành được soạn riêng; không chuyển log/artifact."""
    since = urllib.parse.quote(lui(state['cursor'], 120), safe='')
    ket = {}

    def them(khoa, moc, text, entity=None, signature=None, text_nhom=None):
        if moc and moc >= state['start']:
            e = {'at': moc, 'text': text}
            if text_nhom:
                e['text_nhom'] = text_nhom
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
            release = ban_phat_hanh(c) if path == '/issues/comments' else None
            if release:
                signature = ma([release['version'], release['features']])
                entity = 'release:' + release['sha']
                text = ('Vagabond | Cập nhật ' + release['version']
                        + '\nĐã deploy và kiểm site thật (theo xác nhận phát hành).\n'
                        + '\n'.join('- ' + f.strip() for f in release['features'])
                        + '\nChi tiết: ' + link)
                tom_tat, _ = tom_tat_comment(c)
                text += '\n' + (tom_tat or 'Khối tóm tắt chưa hợp lệ')
                text_nhom = ('Vagabond | Cập nhật ' + release['version'] + ' | ' + c['updated_at'][:10]
                             + '\n' + '\n'.join('- ' + f.strip() for f in release['features']))
                them(entity + ':' + c['updated_at'] + ':' + signature, c['updated_at'], text, entity, signature, text_nhom)
                continue
            nhan = ' (đã sửa)' if c['updated_at'] != c['created_at'] else ''
            dau = (c.get('body') or '').splitlines()[:1]
            muc = {'[CẦN DUYỆT]': 'Cần anh duyệt', '[BỊ CHẶN]': 'Tác vụ bị chặn',
                   '[ĐÃ SỬA XONG]': 'Đã sửa xong, chờ review',
                   '[SẴN SÀNG DEPLOY]': 'Đề nghị phát hành', '[ĐÃ DEPLOY]': 'Báo cáo phát hành'}
            nhom = muc.get(dau[0].strip() if dau else '', loai)
            text = f"Vagabond | {nhom}{nhan}\nTừ: {rut(c['user']['login'], 60)}\n{link}"
            tom_tat = ban_can_duyet(c)
            if tom_tat:
                text += '\n' + tom_tat + '\nTrả lời trong Codex; bot Telegram chưa nhận lệnh duyệt.'
            elif dau and dau[0].strip() == '[CẦN DUYỆT]' and 'telegram-approval' in (c.get('body') or ''):
                text += '\nKhối phương án chưa hợp lệ hoặc chưa đúng người đăng; chưa gửi nội dung cần duyệt.'
            tom_tat, la_chu_repo = tom_tat_comment(c)
            if tom_tat:
                text += '\n' + tom_tat
            elif la_chu_repo:
                text += '\nKhối tóm tắt chưa hợp lệ'
            # Đã có khối tóm tắt của Codex thì không chép thêm ý Summary cho khỏi trùng.
            codex = None if tom_tat else tom_tat_codex(c)
            if codex:
                text += '\nCodex: ' + codex
            if (dau and dau[0].strip() == '[ĐÃ DEPLOY]'
                    and '<!-- telegram-release' in (c.get('body') or '')):
                text += '\nKhối bản tin chưa hợp lệ hoặc chưa đúng người đăng; chưa gửi tóm tắt tính năng.'
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
    # Báo PR đủ điều kiện merge và deploy (anh Việt 15/10/2026): một tin cho mỗi SHA
    # đầu PR, chỉ khi Codex đã rà đạt đúng SHA đó. Chỉ kênh riêng, nhóm bộ phận không nhận.
    for number, pr in prs.items():
        sha = (pr.get('head') or {}).get('sha')
        if not sha or pr.get('draft'):
            continue
        checks = gh.trang('/commits/' + sha + '/check-runs', 'check_runs')
        if not checks or any(c.get('status') != 'completed' or c.get('conclusion') not in CHECK_DAT
                             for c in checks):
            continue
        chi_tiet = gh.goi('/pulls/' + str(number))
        nen = (chi_tiet.get('base') or {}).get('ref') or ''
        if chi_tiet.get('mergeable') is not True or not re.fullmatch(r'[A-Za-z0-9._/-]+', nen):
            continue
        # So đầu nhánh nền HIỆN TẠI với đúng SHA đã chạy bench (Codex f5b07bb).
        so_sanh = gh.goi('/compare/' + urllib.parse.quote(nen, safe='/') + '...' + sha + '?per_page=1')
        tep = [f.get('filename') for f in gh.trang('/pulls/' + str(number) + '/files')]
        kq = xet_san_sang_merge(pr, checks, chi_tiet, gh.trang('/issues/' + str(number) + '/comments'), so_sanh, tep)
        if kq:
            entity = 'san-sang-merge:' + str(number)
            # Khoá ỔN ĐỊNH theo PR và chữ ký (SHA, Codex), để lượt gửi lại sau khi mất
            # phản hồi tìm lại đúng tin (Codex 8292a1d). Mốc là lúc đối soát: khi khoá đã
            # bị tỉa khỏi seen (sau 120 giây), lượt kế đi nhánh im lặng và làm mới hạn giữ
            # entity, nên PR đứng im nhiều tháng cùng SHA vẫn chỉ một tin (Codex 6f45f8f).
            them(entity + ':' + kq['signature'], max(kq['at'], gio()), kq['text'], entity, kq['signature'])
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


def luu_chac(gh, state, sha):
    """Chỉ thử lại PUT khi cùng SHA, hoặc nhận lần PUT mất phản hồi đã thành công."""
    try:
        return gh.luu(state, sha)
    except Loi:
        moi, ma_moi = gh.doc()
        if moi == state:
            return ma_moi
        if ma_moi != sha:
            raise Loi('GitHub: trạng thái đã đổi; không ghi đè phiên khác.') from None
        return gh.luu(state, ma_moi)


def ghi_xong(state, p):
    state['seen'][p['key']] = p['at']
    if p.get('entity'):
        state['entities'][p['entity']] = {'signature': p['signature'], 'at': p['at']}
    state['pending'] = None


def tin_mat_nguon(p, nhom):
    # Nhóm nhân viên không nhận link GitHub hoặc mã kỹ thuật.
    if nhom:
        return 'Vagabond | Bản tin trước mất phản hồi. Vui lòng hỏi quản lý về bản cập nhật gần nhất.'
    k = p['key']
    link = WEB
    m = re.fullmatch(r'comment:/issues/comments:(\d+):.+', k)
    if m:
        link += '/issues/287'  # Nguồn đã mất: đầu mối đối chiếu, không dựng URL comment giả.
    m = re.fullmatch(r'run:(\d+):\d+', k)
    if m:
        link += '/actions/runs/' + m[1]
    return 'Vagabond | Tin ' + p['code'] + ' mất phản hồi lúc ' + p['at'] + '.\nĐối chiếu: ' + link


def chay_kenh(gh, tg, chat, gom=False, nhom=False, han=None):
    if not re.fullmatch(r'-[1-9]\d*' if nhom else r'[1-9]\d*', str(chat)):
        raise Loi('Thiếu hoặc sai loại chat Telegram; chưa ghi dấu gửi.')
    state, sha = gh.doc()
    state.setdefault('entities', {})
    state.setdefault('bien_nhan', {})
    state.setdefault('can_doi_chieu', {})
    moc = gio()
    if han is None:
        han = time.monotonic() + 300
    p = state.get('pending')
    if p and p.get('message_id'):
        ghi_xong(state, p)
        sha = luu_chac(gh, state, sha)
        p = None
    if p and not p.get('ghi_luc'):
        # Dữ liệu cũ dùng at của sự kiện, không phải giờ gửi: bắt đầu đếm từ lúc nâng cấp.
        p['ghi_luc'] = moc
        sha = luu_chac(gh, state, sha)
    if p and p['ghi_luc'] > lui(moc, 600):
        raise Loi('Tin đang chờ phản hồi chưa đủ10phút; giữ dấu, không gửi trùng.')
    if gom and not p and state['cursor'] > lui(moc, 180):
        return 0
    events = thu_thap(gh, state)
    if nhom:
        events = {k: e for k, e in events.items() if e.get('text_nhom')}
    tg.kiem_bot()
    dem = 0

    def gui(khoa, e, lap=False):
        nonlocal sha, dem
        y = {'key': khoa, 'at': e['at'], 'code': ma(khoa), 'ghi_luc': gio(), 'gui_lai': int(lap)}
        if e.get('entity'):
            y.update(entity=e['entity'], signature=e['signature'])
        state['pending'] = y
        sha = luu_chac(gh, state, sha)
        text = e.get('text_nhom', e['text']) if nhom else e['text']
        text = ('(gửi lại)\n' if lap else '') + text
        if not nhom:
            text += '\nMã tin: ' + y['code']
        mid = tg.gui(chat, text, nhom=True) if nhom else tg.gui(chat, text)
        # Log ngay sau OK: dù GitHub ngắt sau đó vẫn có receipt để vận hành đối chiếu.
        print('Đã gửi mã tin ' + y['code'] + ', message_id ' + str(mid)
              + ', kênh ' + ('bộ phận' if nhom else 'riêng'), flush=True)
        y['message_id'] = mid
        state['bien_nhan'][y['code']] = {'message_id': mid, 'at': gio()}
        sha = luu_chac(gh, state, sha)
        ghi_xong(state, y)
        sha = luu_chac(gh, state, sha)
        dem += 1

    if p:
        if p.get('gui_lai') or (nhom and p['key'] not in events):
            # Nhóm chỉ nhận features còn xác minh được; mất nguồn không gửi tin kỹ thuật.
            # Đã thử đúng một lần: giữ vết chưa rõ để người đối chiếu, nhường kênh cho tin khác.
            state['can_doi_chieu'][p['key']] = dict(p)
            ghi_xong(state, p)
            sha = luu_chac(gh, state, sha)
            ly_do = 'đã hết một lần gửi lại' if p.get('gui_lai') else 'nhóm không còn nguồn release hợp lệ'
            print('Cần đối chiếu mã tin ' + p['code'] + '; ' + ly_do + '.', flush=True)
        else:
            if time.monotonic() >= han:
                raise Loi('Đọc nguồn quá5phút; giữ pending cho lượt sau.')
            e = events.get(p['key']) or {'at': p['at'], 'text': tin_mat_nguon(p, nhom),
                                        **{k: p[k] for k in ('entity', 'signature') if k in p}}
            gui(p['key'], e, lap=True)
    for khoa, e in sorted(events.items(), key=lambda x: (x[1]['at'], x[0])):
        if khoa in state['seen'] or khoa in state['can_doi_chieu']:
            continue
        silent = (e.get('entity') and
                  state['entities'].get(e['entity'], {}).get('signature') == e.get('signature'))
        if silent:
            state['entities'][e['entity']] = {'signature': e['signature'], 'at': e['at']}
            continue
        if dem == 30:
            return dem
        if time.monotonic() >= han:
            if dem == 0:
                raise Loi('Đọc nguồn quá5phút, còn tin chưa gửi; kiểm độ chậm API trước khi chạy lại.')
            return dem
        gui(khoa, e)
    state['cursor'] = moc
    state['seen'] = {k: at for k, at in state['seen'].items()
                     if at >= lui(moc, 7 * 86400 if k.startswith('run:') else 120)}
    state['entities'] = {k: e for k, e in state['entities'].items()
                         if e['at'] >= lui(moc, 30 * 86400)}
    state['bien_nhan'] = {k: e for k, e in state['bien_nhan'].items()
                          if e['at'] >= lui(moc, 30 * 86400)}
    luu_chac(gh, state, sha)
    return dem


class KenhNhom:
    """Kho riêng trong cùng tệp; không lưu chat ID, không dùng seen của chat cá nhân."""
    def __init__(self, gh):
        self.gh = gh
    def doc(self):
        self.goc, sha = self.gh.doc()
        if 'bo_phan' not in self.goc:
            moc = gio()
            self.goc['bo_phan'] = {'start': moc, 'cursor': moc, 'seen': {}, 'entities': {}, 'pending': None}
            sha = self.gh.luu(self.goc, sha)
        return self.goc['bo_phan'], sha
    def luu(self, state, sha):
        self.goc['bo_phan'] = state
        return self.gh.luu(self.goc, sha)
    def trang(self, *args):
        return self.gh.trang(*args)
    def goi(self, *args, **kw):
        return self.gh.goi(*args, **kw)


def chay(gh, tg, chat, gom=False, chat_nhom=''):
    dem, loi = 0, []
    han = time.monotonic() + 300
    for kho, dich, nhom in [(gh, chat, False)] + ([(KenhNhom(gh), chat_nhom, True)] if chat_nhom else []):
        try:
            dem += chay_kenh(kho, tg, dich, gom=gom, nhom=nhom, han=han)
        except Loi as e:
            loi.append(('Bộ phận: ' if nhom else 'Riêng: ') + str(e))
    if loi:
        raise Loi('; '.join(loi))
    return dem


def main():
    gh = GitHub(HTTP(), os.environ['GH_TOKEN'])
    if os.getenv('CHE_DO') == 'khoi-tao':
        gh.khoi_tao()
        print('Đã khởi tạo mốc; chưa gửi thông báo.')
        return
    dem = chay(gh, Telegram(HTTP(), os.environ.get('TELEGRAM_BOT_TOKEN', '')),
               os.environ.get('TELEGRAM_CHAT_ID', ''),
               gom=os.getenv('GITHUB_EVENT_NAME') != 'workflow_dispatch',
               chat_nhom=os.environ.get('TELEGRAM_CHAT_ID_BO_PHAN', ''))
    print('Đã gửi ' + str(dem) + ' thông báo; không dùng model.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(str(e) if isinstance(e, Loi) else 'Lỗi khởi chạy (' + type(e).__name__ + '); kiểm cấu hình và dấu giao nhận.', file=sys.stderr)
        sys.exit(1)
