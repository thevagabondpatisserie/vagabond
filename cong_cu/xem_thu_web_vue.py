#!/usr/bin/env python3
"""Xem thử web bản Vue bằng dữ liệu giả, không cần Frappe, không chạm site thật.

    python3 cong_cu/xem_thu_web_vue.py [cổng]

Mở http://127.0.0.1:8790/web_moi/banh (bản Vue) và http://127.0.0.1:8790/banh
(bản cũ) để so ảnh cùng một bộ dữ liệu. Chỉ nghe localhost.

- Tồn bánh, hàng mùa, quầy, cấu hình, phí giao, ưu đãi là FIXTURE cố định.
- POST chỉ có hai đường giả lập: xem_uu_dai (mã GIAM10 giảm 10%) và tao_don
  (trả đường dẫn biên nhận giả). Không gửi gì ra ngoài.
- Ảnh Pancake (content.pancake.vn) không tải từ máy này: trang tự thay ảnh nền.
- VGB_BAN_CU=<tệp html> để so với một bản cũ khác vagabond/trang/banh.html.
- VGB_TAI_SAN_CU=<thư mục web_order> để phục vụ tài sản của bản cũ đó.
"""
import ast
import json
import mimetypes
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
CONG = int(sys.argv[1]) if len(sys.argv) > 1 else 8790
BAN_CU = Path(os.environ.get('VGB_BAN_CU') or GOC / 'vagabond/trang/banh.html')
TAI_SAN_CU = Path(os.environ.get('VGB_TAI_SAN_CU') or GOC / 'vagabond/public/web_order')


def _hang(ten):
	cay = ast.parse((GOC / 'vagabond/noi_dung_web.py').read_text())
	for n in cay.body:
		if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == ten for t in n.targets):
			try:
				return ast.literal_eval(n.value)
			except Exception:
				return None
	return None


def noi_dung():
	nd = _hang('MAC_DINH') or {'khoi': []}
	nhan = dict(_hang('NHAN') or {})
	so_tay = json.loads((GOC / 'vagabond/public/web_order/chu-mac-dinh.json').read_text())
	for k, v in so_tay.items():
		nhan.setdefault(k, v.get('mac_dinh', '') if isinstance(v, dict) else v)
	nhan = {k: (v.get('mac_dinh', '') if isinstance(v, dict) else v) for k, v in nhan.items()}
	return {'khoi': nd.get('khoi', []), 'nhan': nhan, 'lien_he': {'dien_thoai': '0931 224 334', 'dien_thoai_so': '0931224334',
		'messenger': 'https://m.me/thevagabond.saigon'}, 'thong_tin': nd.get('thong_tin', {}), 'san_pham': {},
		'diem_nhan': [{'id': 'bep-tan-son-hoa', 'n': 'Bếp Tân Sơn Hoà', 'a': '307/1 Nguyễn Văn Trỗi, P. Tân Sơn Hoà'},
			{'id': 'cua-hang-sai-gon', 'n': 'Cửa hàng Sài Gòn', 'a': '9 Trần Cao Vân, P. Sài Gòn'}]}


TON = {'banh': {'BAWC00139': 4, 'BAWC00140': 2, 'BAWC00122': 12}, 'nhom': [],
	'dat_truoc': {'nhom': [{'ten': 'CANDLE', 'sizes': [{'cm': 12, 'ma': 'BAWC00139', 'gia': 650000, 'con': 6}, {'cm': 16, 'ma': 'BAWC00140', 'gia': 880000, 'con': 3}]},
		{'ten': 'Kankin', 'sizes': [{'cm': 16, 'ma': 'BAWC00123', 'gia': 910000, 'con': 5}]},
		{'ten': 'Phi Tử Tiếu', 'sizes': [{'cm': 12, 'ma': 'BAWC00135', 'gia': 660000, 'con': 8}, {'cm': 16, 'ma': 'BAWC00136', 'gia': 880000, 'con': 8}]}]}}
MUA = {'co': 1, 'ten_mua': 'Trung thu 2026', 'den_ngay': '2026-10-20', 'mon': [
	{'ma': 'TTHOP01', 'ten': 'Hộp Trăng Rằm', 'gia': 890000, 'con': 24, 'het': 0, 'anh': '/assets/vagabond/web_order/tay-lam-banh-minh-hoa.jpg',
		'ruot': '1 x Dừa Bưởi Xí Muội, 80gram, 1 x Đậu Xanh Trà Xanh, 80gram'},
	{'ma': 'TTHOP02', 'ten': 'Hộp Sương Thu', 'gia': 650000, 'con': 0, 'het': 1, 'anh': ''}]}
QUAY = {'cap_nhat': '2026-10-11 09:41:00', 'quay': [
	{'ma': 'TCV', 'ten': 'Trần Cao Vân', 'dia_chi': '9 Trần Cao Vân', 'mon': [
		{'ma': 'TEST1', 'ten': 'Biscotti', 'nhom': 'Bánh nhẹ', 'con': 12, 'gia': 90000, 'anh': '/assets/vagabond/web_order/anh-bia.png'}]},
	{'ma': 'NVHTN', 'ten': 'Nhà Văn hoá Thanh Niên', 'dia_chi': '21 Phạm Ngọc Thạch', 'mon': []}]}
CAU_HINH = {'mien_phi_tu': 0, 'pixel_id': '', 'lien_he': {'dien_thoai': '0931 224 334', 'dien_thoai_so': '0931224334'},
	'chinh_sach': [{'duong': '/chinh-sach', 'ten': 'Chính sách bảo mật', 'khoa': 'chinh_sach_bao_mat'}],
	'quan': [{'ma': 'Q1', 'ten': 'Quận 1 cũ', 'lat': 10.776, 'lng': 106.700}, {'ma': 'BT', 'ten': 'Bình Thạnh', 'lat': 10.81, 'lng': 106.71}]}


def tra_loi_get(phuong, q):
	if phuong == 'cong_khai':
		return noi_dung()
	if phuong == 'co_the_ban_hom_nay':
		return TON
	if phuong == 'hang_theo_mua':
		return MUA
	if phuong == 'con_tren_quay_web':
		return QUAY
	if phuong == 'cau_hinh_web':
		return CAU_HINH
	if phuong == 'phi_giao':
		return {'ok': True, 'total_fee': 42000, 'distance': 5.2, 'diem_lay': 'Bep Vagabond', 'theo_gio': True}
	if phuong == 'goi_y_dia_chi':
		return {'suggestions': [{'mo_ta': '12 Nguyễn Huệ, Bến Nghé, Quận 1', 'place_id': 'p1'}]}
	if phuong == 'chi_tiet_dia_chi':
		return {'lat': 10.774, 'lng': 106.703, 'dia_chi': '12 Nguyễn Huệ, Phường Sài Gòn, TP. Hồ Chí Minh'}
	if phuong == 'tra_khach':
		return {'addresses': []}
	if phuong == 'tra_mst':
		return {'ok': True, 'ten': 'CÔNG TY TNHH MẪU', 'dia_chi': '1 Lê Lợi, Quận 1'}
	return {}


def tra_loi_post(phuong, than):
	try:
		don = json.loads((than or {}).get('don') or '{}')
	except Exception:
		don = {}
	if phuong == 'xem_uu_dai':
		ma = str(don.get('ma_uu_dai') or '').upper()
		if ma and ma != 'GIAM10':
			return {'ok': False, 'ly_do': 'ma_uu_dai', 'chi_tiet': 'Mã ưu đãi không đúng hoặc đã hết hạn.'}
		if ma == 'GIAM10':
			return {'ok': True, 'giam': 100000, 'ap': [{'ten': 'Giảm 100.000 đ cho đơn bánh'}]}
		return {'ok': True, 'giam': 0, 'ap': []}
	if phuong == 'tao_don':
		return {'ok': True, 'ma_yeu_cau': 'YC-THU-0001', 'duong_dan': '/banh/xong/thu0001'}
	return {}


class Xu(BaseHTTPRequestHandler):
	def gui(self, ma, kieu, than):
		self.send_response(ma)
		self.send_header('Content-Type', kieu)
		self.send_header('Cache-Control', 'no-store')
		self.end_headers()
		self.wfile.write(than if isinstance(than, bytes) else than.encode())

	def do_GET(self):
		duong, _, q = self.path.partition('?')
		if duong.startswith('/api/method/'):
			kq = tra_loi_get(duong.rsplit('.', 1)[-1], q)
			return self.gui(200, 'application/json', json.dumps({'message': kq}, ensure_ascii=False))
		if duong.startswith('/assets/vagabond/'):
			con = duong[len('/assets/vagabond/'):]
			goc = TAI_SAN_CU if con.startswith('web_order/') else GOC / 'vagabond/public'
			tep = ((goc / con[len('web_order/'):]) if con.startswith('web_order/') else (goc / con)).resolve()
			if not tep.exists() and con.startswith('web_order/'):
				tep = (GOC / 'vagabond/public' / con).resolve()
			if not tep.exists() or not (tep.is_relative_to(goc.resolve()) or tep.is_relative_to((GOC / 'vagabond/public').resolve())):
				return self.gui(404, 'text/plain', 'khong co')
			kieu = mimetypes.guess_type(str(tep))[0] or 'application/octet-stream'
			if tep.suffix == '.js':
				kieu = 'text/javascript; charset=utf-8'
			return self.gui(200, kieu, tep.read_bytes())
		if duong == '/web_moi/banh':
			s = (GOC / 'vagabond/www/web_moi/banh.html').read_text().replace('{{ csrf_token }}', 'thu')
			return self.gui(200, 'text/html; charset=utf-8', s)
		if duong == '/banh':
			return self.gui(200, 'text/html; charset=utf-8', BAN_CU.read_text())
		return self.gui(404, 'text/plain', 'khong co')

	def do_POST(self):
		duong = self.path.split('?')[0]
		dai = int(self.headers.get('Content-Length') or 0)
		try:
			than = json.loads(self.rfile.read(dai) or b'{}')
		except Exception:
			than = {}
		if not duong.startswith('/api/method/'):
			return self.gui(404, 'text/plain', 'khong co')
		kq = tra_loi_post(duong.rsplit('.', 1)[-1], than)
		return self.gui(200, 'application/json', json.dumps({'message': kq}, ensure_ascii=False))

	def log_message(self, *a):
		pass


if __name__ == '__main__':
	print('Xem thử web Vue: http://127.0.0.1:%d/web_moi/banh  (bản cũ: /banh)' % CONG, flush=True)
	ThreadingHTTPServer(('127.0.0.1', CONG), Xu).serve_forever()
