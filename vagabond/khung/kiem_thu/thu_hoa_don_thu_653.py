# -*- coding: utf-8 -*-
"""v653 tự đính hoá đơn nhà cung cấp từ hộp thư hoadon@ (issue #555 phần E).

Ca chốt:
  - đọc XML hoá đơn điện tử Thông tư 78 (có và không có namespace), bỏ XML lạ;
  - bung .zip nhà cung cấp gửi, bỏ "PDF" không phải PDF;
  - khớp hoá đơn M-Invoice: MST có đuôi chi nhánh, số có số 0 đầu, ký hiệu có
    mẫu số đứng đầu; hai ứng viên thì không khớp bừa;
  - hộp thư CHỈ ĐỌC: mở readonly, lấy thư bằng BODY.PEEK, không lệnh nào đổi cờ
    hay xoá thư; lượt sau chỉ đọc thư mới;
  - thư có XML và PDF: PDF của nhà cung cấp đính vào hoá đơn M-Invoice đúng tên
    HDDT- (chuỗi đính APP có sẵn lấy nó), XML vào hoá đơn mua; thư chỉ có đường
    dẫn thành Việc cần làm cho Thu mua.
"""

import io
import types
import unittest.mock as um
import zipfile

from vagabond.khung.kiem_thu.nen import Doi, ca, dung, gia_lap, la

fr = gia_lap()

from vagabond import hoa_don_thu as h  # noqa: E402

XML = """<?xml version="1.0" encoding="UTF-8"?>
<HDon xmlns="http://example/tt78"><DLHDon><TTChung><PBan>2.1.0</PBan><KHMSHDon>1</KHMSHDon><KHHDon>C26TPH</KHHDon>
<SHDon>00001234</SHDon><NLap>2026-11-05</NLap></TTChung><NDHDon><NBan><Ten>CÔNG TY TNHH PHP</Ten><MST>0312345678-001</MST></NBan>
<NMua><Ten>The Vagabond</Ten><MST>0316000000</MST></NMua><TToan><TgTTTBSo>12960000</TgTTTBSo></TToan></NDHDon></DLHDon></HDon>""".encode()
PDF = b"%PDF-1.4 hoa don php"


def _zip(*tep):
	b = io.BytesIO()
	with zipfile.ZipFile(b, "w") as z:
		for ten, noi in tep:
			z.writestr(ten, noi)
	return b.getvalue()


@ca("v653 THUẦN: đọc XML Thông tư 78, bung zip, đường dẫn tra cứu, khớp hoá đơn M-Invoice")
def _thuan():
	x = h.doc_xml(XML)
	la("đọc đủ trường", (x["mau"], x["ky_hieu"], x["so"], x["ngay"], x["mst_ban"], x["tong"]),
		("1", "C26TPH", "00001234", "2026-11-05", "0312345678-001", 12960000.0))
	la("XML không namespace", h.doc_xml(XML.replace(b' xmlns="http://example/tt78"', b""))["so"], "00001234")
	la("XML không phải hoá đơn", h.doc_xml(b"<a><b>1</b></a>"), None)
	la("XML hỏng", h.doc_xml(b"<a>"), None)
	xml, pdf = h.phan_loai_tep([("hd.zip", _zip(("thu_muc/hd.xml", XML), ("hd.pdf", PDF), ("ghi_chu.txt", b"x"))),
		("gia.pdf", b"<html>khong phai pdf"), ("le.xml", XML)])
	la("bung zip, bỏ tệp lạ, bỏ PDF giả", ([t for t, _ in xml], [t for t, _ in pdf]), (["hd.xml", "le.xml"], ["hd.pdf"]))
	la("zip hỏng", h.mo_zip("a.zip", b"PK\x03\x04hong"), [])
	la("đường dẫn tra cứu", h.duong_dan_hd("Xem hoá đơn tại https://tracuu.vnpt-invoice.com.vn/?ma=AB12. Cảm ơn https://shop.vn"),
		["https://tracuu.vnpt-invoice.com.vn/?ma=AB12"])
	u = [Doi(name="MI-1", mst_doi_tac="0312345678", so_hd="1234", ky_hieu="C26TPH"),
		Doi(name="MI-2", mst_doi_tac="0312345678", so_hd="1235", ky_hieu="C26TPH")]
	la("khớp: bỏ chi nhánh, số 0 đầu, mẫu số", h.chon_hd(x, u)["name"], "MI-1")
	la("hai ứng viên thì không khớp bừa", h.chon_hd(x, u + [Doi(name="MI-3", mst_doi_tac="0312345678-001", so_hd="01234", ky_hieu="1C26TPH")]), None)
	la("ký hiệu khác năm không khớp", h.chon_hd(x, [Doi(name="MI-9", mst_doi_tac="0312345678", so_hd="1234", ky_hieu="C25TPH")]), None)
	from vagabond.patches import v653_hop_thu_hoa_don as p
	la("bản vá: ô trống nhận mặc định, không đụng mật khẩu", p.can_dien({"hd_thu_dia_chi": "", "hd_thu_cong": 0}),
		{"hd_thu_dia_chi": "hoadon@thevagabondpatisserie.com", "hd_thu_may_chu": "pro10.emailserver.vn", "hd_thu_cong": 993, "hd_thu_bat": 1})


class Imap(object):
	"""Máy chủ IMAP giả: ghi mọi lệnh, chặn mọi lệnh đổi cờ hay xoá."""

	def __init__(self, thu):
		self.thu, self.lenh = thu, []

	def __call__(self, may, cong, timeout=None):
		self.lenh.append(("ket_noi", may, cong))
		return self

	def login(self, a, b):
		self.lenh.append(("login", a))

	def select(self, hop, readonly=False):
		self.lenh.append(("select", hop, readonly))
		return "OK", [b"3"]

	def response(self, k):
		return "OK", [b"77"]

	def uid(self, lenh, *a):
		self.lenh.append(("uid", lenh) + a)
		if lenh == "search":
			return "OK", [b" ".join(str(u).encode() for u in sorted(self.thu))]
		if lenh == "fetch":
			return "OK", [(b"x", self.thu[int(a[0])])]
		raise AssertionError("lệnh IMAP bị cấm: %s" % lenh)

	def store(self, *a):
		raise AssertionError("không được đổi cờ thư")

	def expunge(self):
		raise AssertionError("không được xoá thư")

	def logout(self):
		self.lenh.append(("logout",))


def _thu(tieu_de, tep=(), than="Kính gửi quý khách"):
	from email.message import EmailMessage

	m = EmailMessage()
	m["From"], m["Subject"], m["Message-ID"], m["Date"] = "PHP <hd@php.vn>", tieu_de, "<%s@php.vn>" % tieu_de, "Thu, 05 Nov 2026 10:00:00 +0700"
	m.set_content(than)
	for ten, b, kieu in tep:
		m.add_attachment(b, maintype=kieu[0], subtype=kieu[1], filename=ten)
	return m.as_bytes()


class Kho(object):
	"""Bản ghi giả: dòng Hoá đơn thư, tệp đính, M-Invoice, hoá đơn mua."""

	def __init__(self):
		self.dong, self.tep, self.moc = {}, [], "{}"
		self.pi = "ACC-PINV-2026-00777"
		self.mi = [Doi(name="MI-1", mst_doi_tac="0312345678", so_hd="1234", ky_hieu="C26TPH", loai="Đầu vào")]

	def get_doc(self, a, b=None, **k):
		if isinstance(a, dict):
			if a["doctype"] == "File":
				kho = self

				class F(Doi):
					flags = Doi()

					def insert(s, **k):
						s["name"] = "F%d" % (len(kho.tep) + 1)
						kho.tep.append(dict(s))
						return s
				return F(a)
			kho = self
			d = Doi(a)
			d["name"] = "HDT-%d" % (len(self.dong) + 1)
			d.insert = lambda **k: kho.dong.__setitem__(d["name"], d)
			d.db_set = lambda v, update_modified=True: d.update(v)
			return d
		if a == "File":
			f = [x for x in self.tep if x["name"] == b][0]
			return types.SimpleNamespace(get_content=lambda: f["content"])
		return self.dong[b]

	def exists(self, dt_, f=None, *a, **k):
		if dt_ == "DocType":
			return True
		if dt_ == "File":
			return any(all(x.get(kk) == vv for kk, vv in f.items()) for x in self.tep)
		if dt_ == h.DT:
			return any(d.get("message_id") == f.get("message_id") for d in self.dong.values())
		return False

	def get_all(self, dt_, filters=None, fields=None, pluck=None, **k):
		if dt_ == h.DT_HD:
			return list(self.mi)
		if dt_ == "File":
			return [Doi(name=x["name"], file_name=x["file_name"]) for x in self.tep
				if x["attached_to_doctype"] == filters["attached_to_doctype"] and x["attached_to_name"] == filters["attached_to_name"]]
		if dt_ == "Company":
			return [Doi(tax_id=x) for x in getattr(self, "cong_ty", [])]
		if dt_ == h.DT and "message_id" in (filters or {}):
			ds = [d for d in self.dong.values() if d.get("message_id") == filters["message_id"]]
			return [d["name"] for d in ds] if pluck else ds
		if dt_ == h.DT and "mst_ban" in (filters or {}):
			# v654 thư gửi lại: tìm dòng đã có cùng MST (đầu chuỗi) và số (đuôi chuỗi).
			m, so = filters["mst_ban"][1].rstrip("%"), filters["so_hd"][1].lstrip("%")
			return [Doi(d) for d in self.dong.values() if str(d.get("mst_ban") or "").startswith(m) and str(d.get("so_hd") or "").endswith(so)]
		if dt_ == h.DT:
			tt = filters.get("trang_thai")
			cho = tt[1] if isinstance(tt, list) else [tt]
			ds = [d for d in self.dong.values() if d["trang_thai"] in cho]
			return [d["name"] for d in ds] if pluck else [Doi(d, creation="2026-11-01 08:00:00") for d in ds]
		return []


def _chay(kho, ham):
	db = types.SimpleNamespace(exists=kho.exists, get_value=lambda dt_, f, *a, **k: kho.pi if dt_ == "Purchase Invoice" else None,
		sql=lambda q, *a, **k: [(1,)] if "get_lock" in q else [], commit=lambda: None, rollback=lambda: None,
		get_single_value=lambda dt_, k: kho.moc, set_single_value=lambda dt_, k, v: setattr(kho, "moc", v))
	vs = [um.patch.object(fr, "get_doc", kho.get_doc), um.patch.object(fr, "get_all", kho.get_all), um.patch.object(fr, "db", db),
		um.patch.object(fr, "log_error", lambda *a, **k: (_ for _ in ()).throw(AssertionError(a)))]
	for v in vs:
		v.start()
	try:
		return ham()
	finally:
		for v in reversed(vs):
			v.stop()


@ca("v653 hộp thư CHỈ ĐỌC: readonly, BODY.PEEK, không đổi cờ hay xoá; lượt sau chỉ đọc thư mới")
def _chi_doc():
	kho = Kho()
	may = Imap({5: _thu("HD1234", [("hd.xml", XML, ("application", "xml")), ("hd.pdf", PDF, ("application", "pdf"))]),
		6: _thu("HDlink", than="Tra cứu hoá đơn: https://tracuu.vnpt-invoice.com.vn/?ma=XY99")})
	ch = {"dia_chi": "hoadon@thevagabondpatisserie.com", "mat_khau": "x", "may_chu": "pro10.emailserver.vn", "cong": 993}
	with um.patch("imaplib.IMAP4_SSL", may):
		r = _chay(kho, lambda: h.doc_hop_thu(ch))
	la("đọc hai thư", r, {"so_thu": 2})
	la("mở hộp thư readonly", [x for x in may.lenh if x[0] == "select"], [("select", "INBOX", True)])
	dung("chỉ lấy thư bằng BODY.PEEK", all(x[3] == "(BODY.PEEK[])" for x in may.lenh if x[:2] == ("uid", "fetch")))
	dung("lần đầu đọc từ 13/08", ("uid", "search", None, "SINCE", "13-Aug-2026") in may.lenh)
	may.thu[7] = _thu("HD-moi")
	may.lenh.clear()
	with um.patch("imaplib.IMAP4_SSL", may):
		_chay(kho, lambda: h.doc_hop_thu(ch))
	la("lượt sau chỉ đọc thư mới", [x[2] for x in may.lenh if x[:2] == ("uid", "fetch")], ["7"])
	st = {d["tieu_de"]: d for d in kho.dong.values()}
	la("thư XML và PDF: khớp, đã đính", (st["HD1234"]["trang_thai"], st["HD1234"]["hd_dien_tu"], st["HD1234"]["hoa_don_mua"]),
		(h.TT_DINH, "MI-1", "ACC-PINV-2026-00777"))
	noi = sorted((x["attached_to_doctype"], x["file_name"]) for x in kho.tep if x["attached_to_doctype"] != h.DT)
	la("PDF vào M-Invoice tên HDDT-...-NCC (chuỗi đính APP lấy bản mới nhất), XML vào hoá đơn mua", noi,
		[("MInvoice Invoice", "HDDT-C26TPH-1234-NCC.pdf"), ("Purchase Invoice", "XMLHD-1C26TPH-00001234.xml")])
	la("thư chỉ có đường dẫn", (st["HDlink"]["trang_thai"], st["HDlink"]["duong_dan"]),
		(h.TT_LINK, "https://tracuu.vnpt-invoice.com.vn/?ma=XY99"))
	la("thư không có hoá đơn", st["HD-moi"]["trang_thai"], h.TT_KHONG)


@ca("v653 hoá đơn chưa có trên M-Invoice thì Chờ khớp; M-Invoice kéo về sau thì nhịp khớp lại đính được")
def _cho():
	kho = Kho()
	mi, kho.mi = kho.mi, []
	d = h.doc_thu_hd(_thu("HD1234", [("hd.zip", _zip(("hd.xml", XML), ("hd.pdf", PDF)), ("application", "zip"))]),
		__import__("vagabond.doi_soat_thu", fromlist=["x"]).doc_thu)
	_chay(kho, lambda: h.xu_ly_thu(d, 9))
	dong = list(kho.dong.values())[0]
	la("chưa có M-Invoice: Chờ khớp", dong["trang_thai"], h.TT_CHO)
	kho.mi = mi
	n = _chay(kho, h.khop_lai)
	la("khớp lại được", (n, dong["trang_thai"]), (1, h.TT_DINH))
	_chay(kho, lambda: h.xu_ly_thu(d, 9))
	la("thư đã đọc không ghi lần hai", len(kho.dong), 1)


XML2 = XML.replace(b"00001234", b"00001235").replace(b"12960000", b"500000")
CH = {"dia_chi": "hoadon@thevagabondpatisserie.com", "mat_khau": "x", "may_chu": "pro10.emailserver.vn", "cong": 993}


def _ghi_loi(ham, loi):
	with um.patch.object(fr, "log_error", lambda *a, **k: loi.append(a[-1] if a else "")):
		return ham()


@ca("v653 Codex #560: thư đọc hỏng không bị bỏ qua: lượt sau đọc lại; hỏng đủ năm lần thành Việc cần làm cho Thu mua")
def _thu_lai():
	la("THUẦN: tên PDF có số 0 đầu vẫn khớp", (h.pdf_cua_so("00001234.pdf", "00001234"), h.pdf_cua_so("HD_1234.PDF", "1234"),
		h.pdf_cua_so("00001235.pdf", "00001234"), h.pdf_cua_so("hd.pdf", "")), (True, True, False, False))
	kho, loi = Kho(), []
	may = Imap({5: None, 6: _thu("HDlink", than="Tra cứu hoá đơn: https://tracuu.vnpt-invoice.com.vn/?ma=XY99")})
	with um.patch("imaplib.IMAP4_SSL", may):
		r = _chay(kho, lambda: _ghi_loi(lambda: h.doc_hop_thu(CH), loi))
	import json

	m = json.loads(kho.moc)
	# v654: mốc là danh sách khoảng UID đã xong (đọc mới nhất trước), thư 5 chưa xong.
	la("thư 5 máy chủ không trả nội dung: chờ đọc lại, thư 6 vẫn đọc", (r["so_thu"], m["khoang"], m["thu_lai"], len(kho.dong)), (2, [[6, 6]], {"5": 1}, 1))
	dung("có ghi lỗi kỹ thuật", len(loi) == 1)
	may.thu[5] = _thu("HD1234", [("hd.xml", XML, ("application", "xml")), ("hd.pdf", PDF, ("application", "pdf"))])
	may.lenh.clear()
	with um.patch("imaplib.IMAP4_SSL", may):
		_chay(kho, lambda: _ghi_loi(lambda: h.doc_hop_thu(CH), loi))
	la("lượt sau đọc lại đúng thư 5", [x[2] for x in may.lenh if x[:2] == ("uid", "fetch")], ["5"])
	st = {d["tieu_de"]: d for d in kho.dong.values()}
	la("thư 5 đã đính, hết chờ đọc lại", (st["HD1234"]["trang_thai"], json.loads(kho.moc)["thu_lai"]), (h.TT_DINH, {}))
	kho2 = Kho()
	may2 = Imap({8: None})
	for _ in range(h.SO_LAN_THU):
		with um.patch("imaplib.IMAP4_SSL", may2):
			_chay(kho2, lambda: _ghi_loi(lambda: h.doc_hop_thu(CH), loi))
	d = list(kho2.dong.values())
	la("hỏng năm lần: một dòng Lỗi cho Thu mua, thôi đọc lại", ([(x["uid"], x["trang_thai"]) for x in d], json.loads(kho2.moc)["thu_lai"]),
		([("8", h.TT_LOI)], {}))
	dung("dòng Lỗi nói rõ phải làm gì", "webmail" in d[0]["ghi_chu"])


@ca("v653 Codex #560: khớp M-Invoice khi chưa có hoá đơn mua thì Thiếu tệp, có hoá đơn mua thì nhịp khớp lại đính XML rồi mới Đã đính")
def _thieu_xml():
	kho = Kho()
	kho.pi = None
	d = h.doc_thu_hd(_thu("HD1234", [("hd.xml", XML, ("application", "xml")), ("hd.pdf", PDF, ("application", "pdf"))]),
		__import__("vagabond.doi_soat_thu", fromlist=["x"]).doc_thu)
	_chay(kho, lambda: h.xu_ly_thu(d, 11))
	dong = list(kho.dong.values())[0]
	la("chưa có hoá đơn mua: Thiếu tệp, nói rõ chờ gì", (dong["trang_thai"], dong["hd_dien_tu"]), (h.TT_THIEU, "MI-1"))
	dung("ghi chú nói chờ hoá đơn mua", "hoá đơn mua" in dong["ghi_chu"])
	la("PDF đã sang M-Invoice, XML chưa đính đâu", sorted(x["attached_to_doctype"] for x in kho.tep if x["attached_to_doctype"] != h.DT),
		["MInvoice Invoice"])
	kho.pi = "ACC-PINV-2026-00888"
	n = _chay(kho, h.khop_lai)
	la("có hoá đơn mua: khớp lại đính XML, Đã đính", (n, dong["trang_thai"], dong["hoa_don_mua"], dong["ghi_chu"]),
		(1, h.TT_DINH, "ACC-PINV-2026-00888", ""))
	la("PDF không đính hai lần, XML vào hoá đơn mua", sorted((x["attached_to_doctype"], x["attached_to_name"]) for x in kho.tep
		if x["attached_to_doctype"] != h.DT), [("MInvoice Invoice", "MI-1"), ("Purchase Invoice", "ACC-PINV-2026-00888")])


@ca("v653 Codex #560: một thư hai hoá đơn, PDF tên có số 0 đầu: mỗi M-Invoice nhận đúng PDF của mình")
def _nhieu_pdf():
	kho = Kho()
	kho.mi.append(Doi(name="MI-2", mst_doi_tac="0312345678", so_hd="1235", ky_hieu="C26TPH", loai="Đầu vào"))
	d = h.doc_thu_hd(_thu("HD-doi", [("00001234.xml", XML, ("application", "xml")), ("00001235.xml", XML2, ("application", "xml")),
		("00001234.pdf", PDF, ("application", "pdf")), ("00001235.pdf", PDF + b"2", ("application", "pdf"))]),
		__import__("vagabond.doi_soat_thu", fromlist=["x"]).doc_thu)
	_chay(kho, lambda: h.xu_ly_thu(d, 12))
	la("hai dòng Đã đính", sorted((x["so_hd"], x["trang_thai"]) for x in kho.dong.values()), [("00001234", h.TT_DINH), ("00001235", h.TT_DINH)])
	la("mỗi M-Invoice một PDF đúng của mình", sorted((x["attached_to_name"], x["content"]) for x in kho.tep
		if x["attached_to_doctype"] == "MInvoice Invoice"), [("MI-1", PDF), ("MI-2", PDF + b"2")])
	kho2 = Kho()
	d2 = h.doc_thu_hd(_thu("HD-le", [("00001234.xml", XML, ("application", "xml")), ("00001235.xml", XML2, ("application", "xml")),
		("bang-ke.pdf", PDF, ("application", "pdf"))]), __import__("vagabond.doi_soat_thu", fromlist=["x"]).doc_thu)
	_chay(kho2, lambda: h.xu_ly_thu(d2, 13))
	st = {x["so_hd"]: x for x in kho2.dong.values()}
	la("PDF không mang số hoá đơn nào: Thiếu tệp, không Đã đính", st["00001234"]["trang_thai"], h.TT_THIEU)
	dung("ghi chú bảo đính tay PDF", "PDF" in st["00001234"]["ghi_chu"])
