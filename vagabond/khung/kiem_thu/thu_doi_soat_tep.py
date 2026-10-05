"""Dữ liệu giả: kiểm cửa đọc bytes, không giả làm file vendor gốc."""
import csv
import io
import json
from pathlib import Path
from vagabond.doi_soat_tep import doc_bang
from vagabond.doi_soat_nguon import LoiNguon
from vagabond.khung.kiem_thu.nen import ca, la, nem


@ca("Đối soát file: UTF16 TAB giữ số 0, dấu tiền và tọa độ nhiều dòng")
def _():
	b = 'Mã\tTiền\tGhi chú\r\n0001\t82.488\t"hai\r\ndòng"\r\n'.encode('utf-16')
	r = doc_bang(b, encoding='utf-16', dau='\t')
	la('chữ nguyên', r['dong'][0]['o'], ['0001', '82.488', 'hai\r\ndòng'])
	la('tọa độ', (r['dong'][0]['dong_dau'], r['dong'][0]['dong_cuoi']), (2, 3))
	la('chưa đủ nguồn', r['du_nguon'], False)


@ca("Đối soát file: BOM UTF8, preamble, dấu phẩy trong ô và dòng trống")
def _():
	b = 'Báo cáo\nMã,Tiền\n0002,"1,234.56"\n\n'.encode('utf-8-sig')
	r = doc_bang(b, encoding='utf-8-sig', dau=',', dong_tieu_de=2)
	la('tiền chưa diễn giải', r['dong'][0]['o'][1], '1,234.56')
	la('không bỏ dấu vết dòng trống', r['dong'][1]['trong'], True)
	la('hash ổn định', r['sha256'], doc_bang(b, encoding='utf-8-sig', dau=',', dong_tieu_de=2)['sha256'])


@ca("Đối soát file: không nuốt lỗi cột hoặc encoding để trả phần đã đọc")
def _():
	for b in (b',\n1,2', b'A,B\n1,2\n3', b'A,B\n"unclosed', b'\xff', b'A\x00,B'):
		nem('giữ nguồn lỗi', lambda: doc_bang(b, encoding='utf-8-sig', dau=','), LoiNguon)
	nem('encoding không được đoán', lambda: doc_bang(b'A,B', encoding='ascii', dau=','), LoiNguon)
	nem('header giữa ô', lambda: doc_bang(b'"x\ny"\nA,B', encoding='utf-8-sig', dau=',', dong_tieu_de=2), LoiNguon)


@ca("Đối soát file: giới hạn đầu vào và không tính công thức")
def _():
	for b in (b'', b'x' * (8 * 1024 * 1024 + 1), b'A\n' + b'x' * 20001, b'A\n' + b'1\n' * 10001):
		nem('giới hạn', lambda: doc_bang(b, encoding='utf-8-sig', dau=','), LoiNguon)
	r = doc_bang(b'A,B\n0001,=1+2', encoding='utf-8-sig', dau=',')
	la('không chạy', r['dong'][0]['o'][1], '=1+2')


@ca("Đối soát file: tiêu đề mọi mẫu đã thu thập đọc được, không đổi ô tiền")
def _():
	for ten in ('payoo', 'shopee', 'onepay', 'shinhan', 'greensm', 'be'):
		cot = json.loads((Path(__file__).parent / 'mau_doi_soat' / (ten + '.json')).read_text())['cot']
		s = io.StringIO(newline='')
		w = csv.writer(s, delimiter='\t')
		w.writerow(cot)
		w.writerow(['0001'] + ['82.488'] * (len(cot) - 1))
		r = doc_bang(s.getvalue().encode('utf-16'), encoding='utf-16', dau='\t')
		la('đúng tiêu đề', r['cot'], cot)
		la('không suy đơn vị', r['dong'][0]['o'][1], '82.488')


@ca("#422 P2: cột rỗng và trùng giữ vị trí không ghi đè ô")
def _():
	r = doc_bang(b',Amount,Amount,\n001,10,20,030', encoding='utf-8-sig', dau=',')
	la('đủ cột', r['cot'], ['', 'Amount', 'Amount', ''])
	la('đủ ô', r['dong'][0]['o'], ['001', '10', '20', '030'])
