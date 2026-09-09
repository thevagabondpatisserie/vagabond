"""Nguồn HTTP giả lập #257, không thay hàm đồng bộ, ngày, cache hoặc DB."""
import json
from datetime import datetime
from urllib.parse import urlparse


def tra(url, params, don):
    p = urlparse(url)
    goc = '/api/v1/shops/THU257/orders'
    if p.scheme != 'https' or p.netloc != 'pos.pages.fm' or p.query:
        raise ValueError('Không phải URL nguồn thử đã khai.')
    if params.get('api_key') != 'THU257':
        raise ValueError('Không phải khoá thử.')
    if p.path == goc + '/' + don['id']:
        return {'success': True, 'data': don}
    if p.path != goc or params.get('updateStatus') != 'estimate_delivery_date':
        raise ValueError('Đường gọi ngoài hợp đồng thử.')
    if int(params.get('page_number', 0)) != 1:
        raise ValueError('Nguồn thử chỉ có một trang.')
    moc = datetime.fromisoformat(don['estimate_delivery_date']).timestamp()
    co = int(params['startDateTime']) <= moc <= int(params['endDateTime'])
    return {'success': True, 'data': [don] if co else []}


def gan(don, tep_log):
    """Chỉ gateway CI đã kiểm khoá gọi hàm này, không cài hook production."""
    import requests
    def gui(session, method, url, **kw):
        if method.upper() != 'GET':
            raise RuntimeError('Nguồn thử không cho ghi ra ngoài.')
        body = tra(url, kw.get('params') or {}, don)
        with tep_log.open('a') as f:
            f.write(json.dumps({'duong': urlparse(url).path,
                                'so_don': len(body['data']) if isinstance(body['data'], list) else 1}) + '\n')
        r = requests.Response()
        r.status_code = 200
        r._content = json.dumps(body).encode()
        r.headers['Content-Type'] = 'application/json'
        r.url = url
        return r
    requests.sessions.Session.request = gui
