"""Deterministic issue inbox. No model, shell commands, or ERP writes."""
import datetime as dt
import json
import hashlib
import os
import re
import urllib.error
import urllib.request

PREFIX = '<!-- codex-inbox-v1 '
BOT = 'github-actions[bot]'
LABEL = 'codex:queued'
LIMIT = 3


def command(body):
    """Only a standalone directive outside quotes/fences/HTML comments."""
    body = re.sub(r'<!--.*?-->', '', body or '', flags=re.S)
    fence = None
    for line in body.splitlines():
        s = line.strip()
        if s.startswith(('```', '~~~')):
            kind = s[:3]
            fence = None if fence == kind else (fence or kind)
            continue
        if fence or line.startswith(('    ', '\t')) or s.startswith('>'):
            continue
        if re.match(r'^@codex(?:\s|$)', s, re.I):
            return s
    return None


def receipt(comment):
    # A user-pasted marker is not a receipt. Only the Actions identity owns it.
    user = comment.get('user') or {}
    if user.get('login') != BOT or user.get('type') != 'Bot':
        return None
    body = comment.get('body') or ''
    if not body.startswith(PREFIX):
        return None
    try:
        data = json.loads(body[len(PREFIX):body.index(' -->')])
        if data['status'] not in {'queued', 'working', 'done', 'blocked', 'cancelled', 'limited'}:
            return None
        if not re.fullmatch(r'(issue|comment):[0-9]+', data['source']):
            return None
        when = dt.datetime.fromisoformat(data['received'])
        if when.tzinfo is None:
            return None
        return data
    except (ValueError, KeyError, TypeError):
        return None


def render(data, source_url, run_url):
    labels = {'queued': 'Đã nhận - chờ Codex xử lý', 'limited': 'Tạm chặn - đủ 3 yêu cầu trong 24 giờ'}
    status = labels[data['status']]
    return (PREFIX + json.dumps(data, sort_keys=True) + ' -->\n'
            f'**{status}.**\n\nYêu cầu: {source_url}\n\n'
            f'Mã nhận: `{data["source"]}`. [Lượt tiếp nhận]({run_url}).\n\n'
            'Đây là xác nhận tiếp nhận, chưa phải đã chạy model hoặc hoàn thành công việc. '
            'Một body/comment chỉ nhận một lần; muốn giao việc mới hãy viết comment mới. '
            'Yêu cầu bị giới hạn không tự chạy lại; sau 24 giờ có thể gửi comment mới.')


class GitHub:
    def __init__(self, repo, token):
        if not re.fullmatch(r'[\w.-]+/[\w.-]+', repo):
            raise ValueError('Invalid repository')
        self.repo = repo
        self.token = token

    def request(self, method, path, data=None):
        req = urllib.request.Request('https://api.github.com/repos/' + self.repo + path,
            data=None if data is None else json.dumps(data).encode(), method=method,
            headers={'Authorization': 'Bearer ' + self.token, 'Accept': 'application/vnd.github+json',
                     'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'codex-issue-inbox'})
        # No automatic retry on POST: ambiguous response must be reconciled by source ID.
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.load(response)

    def pages(self, path):
        result = []
        sep = '&' if '?' in path else '?'
        for page in range(1, 101):
            rows = self.request('GET', f'{path}{sep}per_page=100&page={page}')
            result.extend(rows)
            if len(rows) < 100:
                return result
        raise RuntimeError('Pagination limit reached; no silent truncation')

    def allowed(self, user):
        # Reject bot-to-bot loops. Claude Desktop posts as the authorized human user.
        if user.get('type') != 'User':
            return False
        login = user['login']
        if not re.fullmatch(r'[A-Za-z0-9-]+', login):
            return False
        result = self.request('GET', f'/collaborators/{login}/permission')
        return result.get('permission') in {'admin', 'write', 'maintain'}


def reconcile(api, issue, now, run_url, since=None):
    if issue.get('pull_request') or issue['state'] != 'open':
        return 0
    number = issue['number']
    comments = api.pages(f'/issues/{number}/comments')
    known = [r for c in comments if (r := receipt(c))]
    seen = {r['source'] for r in known}
    sources = [('issue:' + str(issue['id']), issue)] + [('comment:' + str(c['id']), c) for c in comments]
    accepted = 0
    permissions = {}
    for source, item in sources:
        if since and dt.datetime.fromisoformat(item['created_at'].replace('Z', '+00:00')) < since:
            continue
        if source in seen or not command(item.get('body')):
            continue
        user = item.get('user') or {}
        login = user.get('login')
        if login not in permissions:
            permissions[login] = api.allowed(user)
        if not permissions[login]:
            continue
        recent = sum(r['status'] != 'limited' and dt.datetime.fromisoformat(r['received']) > now - dt.timedelta(hours=24)
                     for r in known)
        data = {'source': source, 'status': 'queued' if recent < LIMIT else 'limited',
                'received': now.isoformat(), 'requester': login,
                'body_sha256': hashlib.sha256((item.get('body') or '').encode()).hexdigest()}
        api.request('POST', f'/issues/{number}/comments', {'body': render(data, item['html_url'], run_url)})
        known.append(data)
        seen.add(source)
        accepted += data['status'] == 'queued'
    # Recover label if comment POST succeeded but a later API call failed.
    active = any(r['status'] in {'queued', 'working', 'blocked'} for r in known)
    labelled = any((x.get('name') if isinstance(x, dict) else x) == LABEL
                   for x in issue.get('labels', []))
    if active and not labelled:
        api.request('POST', f'/issues/{number}/labels', {'labels': [LABEL]})
    elif labelled and not active:
        api.request('DELETE', f'/issues/{number}/labels/{LABEL}')
    return accepted


def sweep(api, issues, now, run_url, since):
    # Một issue lỗi không được làm mất lượt nhận của mọi issue đứng sau.
    count, errors = 0, []
    for issue in issues:
        try:
            count += reconcile(api, issue, now, run_url, since)
        except (OSError, ValueError, KeyError, AttributeError, TypeError, RuntimeError) as exc:
            errors.append(f"#{issue.get('number', '?')}: {type(exc).__name__}")
    if errors:
        # Giữ job đỏ nhưng không đưa payload hoặc token vào thông báo.
        raise RuntimeError('Chưa nhận được các issue: ' + ', '.join(errors))
    return count


def main():
    start = os.environ.get('CODEX_INBOX_SINCE', '').strip()
    if not start:
        raise ValueError('Chưa đặt CODEX_INBOX_SINCE; không được nhận lại lịch sử cũ.')
    since = dt.datetime.fromisoformat(start.replace('Z', '+00:00'))
    if since.tzinfo is None:
        raise ValueError('CODEX_INBOX_SINCE must include timezone')
    api = GitHub(os.environ['GITHUB_REPOSITORY'], os.environ['GH_TOKEN'])
    # Whole queue reconciliation recovers coalesced Actions events and old mentions.
    api.request('GET', '/labels/' + LABEL)  # Provisioned by maintainer before enabling.
    issues = api.pages('/issues?state=open&sort=created&direction=asc')
    now = dt.datetime.now(dt.timezone.utc)
    run_url = f'https://github.com/{api.repo}/actions/runs/{os.environ["GITHUB_RUN_ID"]}'
    count = sweep(api, issues, now, run_url, since)
    print(f'Inbox reconciled: {count} newly accepted request(s).')


if __name__ == '__main__':
    main()
