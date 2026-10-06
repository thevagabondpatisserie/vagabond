# -*- coding: utf-8 -*-
"""#420 v579: đọc tệp báo cáo vendor thành bảng ô thô, chưa hiểu nghiệp vụ.

Anh Việt 06/10/2026 giao Claude cầm đầu đối soát vendor, "làm trọn một lần":
mười nguồn (Payoo, OnePay, Shinhan POS, ShopeeFood, Xanh SM Ngon, GrabFood,
Be, Grab for Business, Xanh SM Taxi, thẻ tín dụng Shinhan). Mỗi nguồn gửi
một kiểu tệp: CSV (Payoo), xlsx (OnePay, Xanh SM, Be, Grab), xls (Shinhan),
PDF (GrabFood, sao kê thẻ), có khi gói trong zip.

Tệp này chỉ làm một việc: biến byte của tệp thành các trang, mỗi trang là
lưới ô (danh sách dòng, mỗi dòng danh sách ô), hoặc các dòng chữ của PDF.
Không đổi tiền, không đoán cột. Phần hiểu từng mẫu nằm ở doi_soat_mau.py.

Vì sao tách: bộ kiểm thử trên máy CI không có openpyxl, xlrd hay PyMuPDF.
Mẫu được kiểm bằng lưới ô dựng sẵn; ở đây chỉ còn lớp mỏng gọi thư viện,
và mỗi thư viện chỉ nạp khi gặp đúng loại tệp.
"""

# phần thuần
import csv
import hashlib
import io
import zipfile

TOI_DA_BYTE = 20 * 1024 * 1024
TOI_DA_TEP_ZIP = 20
TOI_DA_DONG = 20000
TOI_DA_COT = 200


class LoiTep(ValueError):
	"""Tệp không đọc được; câu lỗi nói người dùng làm gì tiếp."""


def bam(noi_dung):
	return hashlib.sha256(noi_dung).hexdigest()


def loai_tep(ten, noi_dung):
	"""Nhận loại theo chữ ký byte trước, đuôi tên sau.

	Tệp tải từ email hay bị đổi đuôi (ví dụ .xls mà thật ra là xlsx), nên
	không tin đuôi tên khi byte nói khác.
	"""
	dau = noi_dung[:8]
	ten = (ten or "").lower()
	if dau.startswith(b"%PDF"):
		return "pdf"
	if dau.startswith(b"PK\x03\x04"):
		# xlsx cũng là zip; phân biệt bằng tệp [Content_Types].xml bên trong.
		try:
			with zipfile.ZipFile(io.BytesIO(noi_dung)) as z:
				ds = z.namelist()
		except zipfile.BadZipFile:
			raise LoiTep("Tệp nén bị hỏng; tải lại tệp gốc từ email.") from None
		if "[Content_Types].xml" in ds and any(n.startswith("xl/") for n in ds):
			return "xlsx"
		return "zip"
	if dau.startswith(b"\xd0\xcf\x11\xe0"):
		return "xls"
	if ten.endswith((".csv", ".txt", ".tsv")) or _giong_chu(noi_dung):
		return "csv"
	raise LoiTep("Chưa đọc được loại tệp này; gửi tệp gốc dạng CSV, Excel hoặc PDF.")


def _giong_chu(noi_dung):
	mau = noi_dung[:4096]
	if mau.startswith((b"\xef\xbb\xbf", b"\xff\xfe", b"\xfe\xff")):
		return True
	try:
		mau.decode("utf-8")
	except UnicodeDecodeError:
		return False
	return b"\x00" not in mau


def doc_csv(noi_dung):
	"""CSV/TAB thành một trang. Thử UTF-8 (có/không BOM) rồi UTF-16.

	Dấu phân cách chọn theo dòng đầu có nhiều ô nhất trong ba ứng viên; không
	dùng csv.Sniffer vì nó hay nhận nhầm dấu chấm trong số tiền.
	"""
	chu = None
	for ma in ("utf-8-sig", "utf-16"):
		try:
			chu = noi_dung.decode(ma)
			if ma == "utf-16" and not noi_dung.startswith((b"\xff\xfe", b"\xfe\xff")):
				chu = None
				continue
			break
		except UnicodeDecodeError:
			chu = None
	if chu is None:
		raise LoiTep("Tệp CSV không phải UTF-8; mở bằng Excel rồi lưu lại dạng CSV UTF-8.")
	if "\x00" in chu:
		raise LoiTep("Tệp có ký tự rỗng; kiểm tra lại tệp gốc.")
	dong_dau = chu.splitlines()[0] if chu.strip() else ""
	dau = max((",", ";", "\t"), key=lambda d: dong_dau.count(d))
	try:
		o = [hang for hang in csv.reader(io.StringIO(chu, newline=""), delimiter=dau, strict=True)]
	except csv.Error:
		raise LoiTep("CSV lỗi cấu trúc (dấu ngoặc kép lệch); tải lại tệp gốc.") from None
	_kiem_co(o)
	return [dict(ten="CSV", o=o)]


def _kiem_co(o):
	if len(o) > TOI_DA_DONG:
		raise LoiTep("Tệp quá %s dòng; chia theo kỳ rồi tải từng phần." % TOI_DA_DONG)
	if any(len(h) > TOI_DA_COT for h in o):
		raise LoiTep("Tệp có dòng quá %s cột; kiểm lại tệp gốc." % TOI_DA_COT)


def doc_xlsx(noi_dung):
	import openpyxl

	try:
		sach = openpyxl.load_workbook(io.BytesIO(noi_dung), read_only=True, data_only=True)
	except Exception:
		raise LoiTep("Không mở được tệp Excel; tệp có thể có mật khẩu hoặc bị hỏng.") from None
	trang = []
	for ws in sach.worksheets:
		o = []
		for hang in ws.iter_rows(values_only=True):
			o.append(list(hang))
			if len(o) > TOI_DA_DONG:
				break
		# read_only giữ cột rỗng cuối dòng; cắt cho gọn để so cột dễ.
		while o and all(v in (None, "") for v in o[-1]):
			o.pop()
		_kiem_co(o)
		trang.append(dict(ten=ws.title, o=o))
	sach.close()
	return trang


def doc_xls(noi_dung):
	try:
		import xlrd
	except ImportError:
		raise LoiTep("Máy chủ chưa có bộ đọc tệp .xls; mở tệp bằng Excel, lưu dạng .xlsx rồi tải lại.") from None
	try:
		sach = xlrd.open_workbook(file_contents=noi_dung)
	except Exception:
		raise LoiTep("Không mở được tệp .xls; tệp có thể có mật khẩu hoặc bị hỏng.") from None
	trang = []
	for ws in sach.sheets():
		o = []
		for r in range(min(ws.nrows, TOI_DA_DONG + 1)):
			hang = []
			for c in range(ws.ncols):
				o_ = ws.cell(r, c)
				if o_.ctype == xlrd.XL_CELL_DATE:
					hang.append(xlrd.xldate.xldate_as_datetime(o_.value, sach.datemode))
				elif o_.ctype == xlrd.XL_CELL_EMPTY:
					hang.append(None)
				else:
					hang.append(o_.value)
			o.append(hang)
		_kiem_co(o)
		trang.append(dict(ten=ws.name, o=o))
	return trang


def doc_pdf(noi_dung):
	"""PDF thành dòng chữ theo từng trang, giữ thứ tự đọc của PyMuPDF.

	PDF bị khoá mật khẩu thì dừng ở đây, không thử đoán mật khẩu.
	"""
	try:
		import pymupdf as fitz
	except ImportError:
		try:
			import fitz
		except ImportError:
			raise LoiTep("Máy chủ chưa có bộ đọc PDF; báo quản trị cài PyMuPDF.") from None
	try:
		tl = fitz.open(stream=noi_dung, filetype="pdf")
	except Exception:
		raise LoiTep("Không mở được PDF; tải lại tệp gốc.") from None
	if tl.needs_pass:
		raise LoiTep("PDF có mật khẩu; mở bằng mật khẩu rồi in lại thành PDF không khoá.")
	trang = []
	for so, tr in enumerate(tl, 1):
		dong = [d.rstrip() for d in tr.get_text("text", sort=True).splitlines()]
		trang.append(dict(ten="Trang %s" % so, dong=[d for d in dong if d.strip()]))
	tl.close()
	return trang


def doc_zip(noi_dung, sau=0):
	if sau > 1:
		raise LoiTep("Tệp nén lồng nhiều tầng; giải nén rồi tải từng tệp.")
	ra = []
	with zipfile.ZipFile(io.BytesIO(noi_dung)) as z:
		ds = [i for i in z.infolist() if not i.is_dir() and not i.filename.startswith("__MACOSX")]
		if len(ds) > TOI_DA_TEP_ZIP:
			raise LoiTep("Tệp nén có quá %s tệp; tải từng tệp." % TOI_DA_TEP_ZIP)
		for i in ds:
			if i.flag_bits & 0x1:
				raise LoiTep("Tệp nén có mật khẩu; giải nén bằng mật khẩu rồi tải tệp bên trong.")
			if i.file_size > TOI_DA_BYTE:
				raise LoiTep("Tệp trong gói nén quá 20 MB; tải riêng tệp đó.")
			ra.append((i.filename.rsplit("/", 1)[-1], z.read(i)))
	return ra


def doc_tep(ten, noi_dung, sau=0):
	"""Trả danh sách tệp đã đọc: [{ten, loai, sha256, trang}].

	Zip trả nhiều phần tử (mỗi tệp bên trong một bản), tệp đơn trả một.
	"""
	if not isinstance(noi_dung, (bytes, bytearray)) or not noi_dung:
		raise LoiTep("Tệp trống; chọn lại tệp.")
	if len(noi_dung) > TOI_DA_BYTE:
		raise LoiTep("Tệp quá 20 MB; chia theo kỳ rồi tải từng phần.")
	noi_dung = bytes(noi_dung)
	loai = loai_tep(ten, noi_dung)
	if loai == "zip":
		ra = []
		for ten_con, byte_con in doc_zip(noi_dung, sau):
			ra.extend(doc_tep(ten_con, byte_con, sau + 1))
		return ra
	doc = {"csv": doc_csv, "xlsx": doc_xlsx, "xls": doc_xls, "pdf": doc_pdf}[loai]
	return [dict(ten=ten, loai=loai, sha256=bam(noi_dung), trang=doc(noi_dung))]
