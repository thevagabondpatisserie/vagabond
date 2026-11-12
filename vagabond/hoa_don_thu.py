# -*- coding: utf-8 -*-
"""Tự đính hoá đơn nhà cung cấp (PDF và XML) từ hộp thư hoadon@ (issue #555 phần E, v653).

Vì sao có tệp này
-----------------
Anh Việt 12/11/2026: phần APP chỉ còn một chỗ làm tay là tải bản thể hiện PDF
của hoá đơn nhà cung cấp về đính kèm cho kế toán duyệt. Nhà cung cấp gửi hoá
đơn về hoadon@thevagabondpatisserie.com: đo 704 thư từ 13/08 có 407 thư kèm XML,
17 thư chỉ PDF, 280 thư chỉ có đường dẫn, 0 tệp khoá mật khẩu. Anh chọn B: ERP
đọc thẳng hộp thư này, anh tự dán mật khẩu vào ô dựng sẵn trong Cài đặt lõi.

Luật
----
- CHỈ ĐỌC: mở thư mục ở chế độ readonly, lấy thư bằng BODY.PEEK nên không đánh
  dấu đã đọc; không xoá, không chuyển thư, không trả lời.
- XML hoá đơn điện tử (Thông tư 78) là nguồn để khớp: MST người bán, ký hiệu,
  số hoá đơn. Khớp với hoá đơn M-Invoice đầu vào (cùng MST, cùng số, ký hiệu
  khớp) rồi tới hoá đơn mua ERP qua ô custom_minvoice_id.
- PDF của chính nhà cung cấp đính vào hoá đơn M-Invoice đúng tên tệp HDDT-...pdf,
  nên chuỗi có sẵn (minvoice_tep.dinh_vao_ho_so) đính nó vào APP thay cho bản
  M-Invoice vẽ lại. XML đính vào hoá đơn mua để kế toán đối chiếu.
- Chưa khớp được (M-Invoice chưa kéo về) thì để Chờ khớp, nhịp sau thử lại.
  Thư chỉ có đường dẫn: ghi đường dẫn, thành Việc cần làm cho Thu mua tải tay.
- Không sửa hoá đơn mua, không sửa chứng từ đã ghi sổ, không ghi sổ gì.

Phần THUẦN đứng trước, phần chạm hệ sau.
"""

import io
import re
import zipfile

DT = "Vagabond Hoa Don Thu"
DT_HD = "MInvoice Invoice"
CAI_DAT = "Vagabond Settings"
DIA_CHI_MAC_DINH = "hoadon@thevagabondpatisserie.com"
MAY_CHU_MAC_DINH = "pro10.emailserver.vn"
BAT_DAU = "13-Aug-2026"
TOI_DA_MOI_LUOT = 40
TOI_DA_TEP = 8 * 1024 * 1024
TT_DINH, TT_CHO, TT_LINK, TT_KHONG, TT_LOI = "Đã đính", "Chờ khớp", "Chỉ có đường dẫn", "Không phải hoá đơn", "Lỗi"
TIEN_TO_XML = "XMLHD-"


# ================================================================== THUẦN

def _ten(tag):
	return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _tim(goc, *duong):
	"""Phần tử theo đường tên (bỏ namespace), tìm ở mọi tầng cho tầng đầu."""
	ds = [e for e in goc.iter() if _ten(e.tag) == duong[0]]
	for ten in duong[1:]:
		ds = [c for e in ds for c in e if _ten(c.tag) == ten]
	return ds[0] if ds else None


def _chu(goc, *duong):
	e = _tim(goc, *duong)
	return (e.text or "").strip() if e is not None and e.text else ""


def doc_xml(b):
	"""Đọc XML hoá đơn điện tử. Trả dict hoặc None nếu không phải hoá đơn. THUẦN.

	Thông tư 78: TTChung/KHMSHDon (mẫu số), KHHDon (ký hiệu), SHDon (số), NLap
	(ngày lập); NDHDon/NBan/MST, Ten; TToan/TgTTTBSo (tổng thanh toán)."""
	import xml.etree.ElementTree as ET

	if not b or len(b) > TOI_DA_TEP:
		return None
	try:
		goc = ET.fromstring(b)
	except ET.ParseError:
		return None
	so = _chu(goc, "TTChung", "SHDon")
	mst = re.sub(r"[^0-9-]", "", _chu(goc, "NBan", "MST"))
	if not (so and mst):
		return None
	try:
		tong = float(_chu(goc, "TToan", "TgTTTBSo") or 0)
	except ValueError:
		tong = 0.0
	return {"mau": _chu(goc, "TTChung", "KHMSHDon"), "ky_hieu": _chu(goc, "TTChung", "KHHDon"), "so": so,
		"ngay": _chu(goc, "TTChung", "NLap")[:10], "mst_ban": mst, "ten_ban": _chu(goc, "NBan", "Ten")[:140],
		"mst_mua": re.sub(r"[^0-9-]", "", _chu(goc, "NMua", "MST")), "tong": tong}


def mo_zip(ten, b):
	"""Tệp .zip nhà cung cấp hay gửi (VNPT, MISA): bung ra các tệp .xml, .pdf bên
	trong, bỏ thư mục, bỏ tệp quá lớn. THUẦN."""
	ra = []
	try:
		with zipfile.ZipFile(io.BytesIO(b)) as z:
			for i in z.infolist():
				n = i.filename.rsplit("/", 1)[-1]
				if i.is_dir() or i.file_size > TOI_DA_TEP or not n.lower().endswith((".xml", ".pdf")):
					continue
				ra.append((n, z.read(i)))
	except (zipfile.BadZipFile, OSError, RuntimeError):
		return []
	return ra


def phan_loai_tep(tep):
	"""[(tên, byte)] thành (danh sách XML, danh sách PDF), bung zip. THUẦN."""
	xml, pdf = [], []
	for ten, b in tep or []:
		t = (ten or "").lower()
		if t.endswith(".zip"):
			x, p = phan_loai_tep(mo_zip(ten, b))
			xml += x
			pdf += p
		elif t.endswith(".xml"):
			xml.append((ten, b))
		elif t.endswith(".pdf") and b[:4] == b"%PDF":
			pdf.append((ten, b))
	return xml, pdf


DUONG_DAN_HD = re.compile(r"https?://[^\s\"'<>]+", re.I)
TU_KHOA_LINK = ("tracuu", "tra-cuu", "hoadon", "invoice", "einvoice", "hddt", "meinvoice", "vnpt-invoice", "easyinvoice", "fast")


def duong_dan_hd(than):
	"""Đường dẫn tra cứu hoá đơn trong thân thư (Fast, VNPT, EasyInvoice, MISA...). THUẦN."""
	ra = []
	for u in DUONG_DAN_HD.findall(than or ""):
		u = u.rstrip(".,);]")
		if any(k in u.lower() for k in TU_KHOA_LINK) and u not in ra:
			ra.append(u)
	return ra[:5]


def so_nguyen(v):
	try:
		return int(str(v or "").strip().lstrip("0") or 0)
	except ValueError:
		return None


def khop_ky_hieu(a, b):
	"""Ký hiệu khớp: bỏ mẫu số đứng đầu (1C25TAA với C25TAA), không phân biệt hoa thường. THUẦN."""
	a, b = str(a or "").strip().upper(), str(b or "").strip().upper()
	if not a or not b:
		return True
	return a == b or a.endswith(b) or b.endswith(a)


def chon_hd(hd, ung_vien):
	"""Hoá đơn M-Invoice khớp một XML: cùng MST người bán (bỏ chi nhánh -xxx), cùng
	số (bỏ số 0 đầu), ký hiệu khớp. Đúng một ứng viên mới nhận. THUẦN."""
	mst = str(hd.get("mst_ban") or "").split("-")[0]
	so = so_nguyen(hd.get("so"))
	ra = [u for u in ung_vien or [] if str(u.get("mst_doi_tac") or "").split("-")[0] == mst
		and so_nguyen(u.get("so_hd")) == so and khop_ky_hieu(u.get("ky_hieu"), hd.get("ky_hieu"))]
	return ra[0] if len(ra) == 1 else None


def ten_xml(ky_hieu, so):
	from vagabond.minvoice_tep import ten_tep_pdf

	return TIEN_TO_XML + ten_tep_pdf(ky_hieu, so)[len("HDDT-"):-4] + ".xml"


# ================================================================== CHẠM HỆ

import frappe  # noqa: E402


def _frappe():
	import frappe

	return frappe


def cau_hinh():
	frappe = _frappe()
	c = frappe.get_doc(CAI_DAT)
	try:
		mk = c.get_password("hd_thu_mat_khau", raise_exception=False) or ""
	except Exception:
		mk = ""
	return {"bat": int(c.get("hd_thu_bat") or 0), "dia_chi": (c.get("hd_thu_dia_chi") or DIA_CHI_MAC_DINH).strip(),
		"may_chu": (c.get("hd_thu_may_chu") or MAY_CHU_MAC_DINH).strip(), "cong": int(c.get("hd_thu_cong") or 993),
		"mat_khau": mk}


def _moc():
	import json

	try:
		return json.loads(_frappe().db.get_single_value(CAI_DAT, "hd_thu_moc") or "{}") or {}
	except Exception:
		return {}


def _ghi_moc(m):
	import json

	_frappe().db.set_single_value(CAI_DAT, "hd_thu_moc", json.dumps(m))


def doc_dinh_ky():
	"""Lịch mỗi giờ: đọc thư mới, rồi thử khớp lại các dòng Chờ khớp."""
	frappe = _frappe()
	ch = cau_hinh()
	if not (ch["bat"] and ch["mat_khau"]):
		return
	frappe.set_user("Administrator")
	try:
		doc_hop_thu(ch)
	finally:
		khop_lai()


def doc_hop_thu(ch=None):
	"""Đọc thư mới (UID lớn hơn mốc), mỗi lượt tối đa TOI_DA_MOI_LUOT thư. Khoá có
	tên để lịch và nút "Đọc ngay" không chạy chồng."""
	import imaplib

	from vagabond.doi_soat_thu import doc_thu

	frappe = _frappe()
	ch = ch or cau_hinh()
	r = frappe.db.sql("select get_lock('vgb_hd_hop_thu', 0)")
	if not r or r[0][0] != 1:
		return {"so_thu": 0, "dang_chay": 1}
	so = 0
	try:
		m = imaplib.IMAP4_SSL(ch["may_chu"], ch["cong"], timeout=30)
		try:
			m.login(ch["dia_chi"], ch["mat_khau"])
			# readonly: máy chủ không đổi cờ Đã đọc của bất kỳ thư nào.
			kq, du = m.select("INBOX", readonly=True)
			if kq != "OK":
				raise RuntimeError("Không mở được hộp thư đến của %s." % ch["dia_chi"])
			uv = int((m.response("UIDVALIDITY")[1] or [b"0"])[0] or 0)
			moc = _moc()
			cuoi = int(moc.get("uid") or 0) if int(moc.get("uv") or 0) == uv else 0
			kq, du = (m.uid("search", None, "UID %d:*" % (cuoi + 1)) if cuoi else m.uid("search", None, "SINCE", BAT_DAU))
			uids = sorted(int(x) for x in (du[0] or b"").split() if int(x) > cuoi) if kq == "OK" else []
			for uid in uids[:TOI_DA_MOI_LUOT]:
				kq, du = m.uid("fetch", str(uid), "(BODY.PEEK[])")
				tho = next((x[1] for x in (du or []) if isinstance(x, tuple) and len(x) > 1), None)
				try:
					if tho:
						xu_ly_thu(doc_thu_hd(tho, doc_thu), uid)
					frappe.db.commit()
				except Exception:
					frappe.db.rollback()
					frappe.log_error(frappe.get_traceback(), "hoa_don_thu: thư UID %s" % uid)
				so += 1
				_ghi_moc({"uv": uv, "uid": uid, "luc": str(frappe.utils.now_datetime())[:19]})
				frappe.db.commit()
		finally:
			try:
				m.logout()
			except Exception:
				pass
	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "hoa_don_thu: đọc hộp thư")
		return {"so_thu": so, "loi": str(e)[:300]}
	finally:
		frappe.db.sql("select release_lock('vgb_hd_hop_thu')")
	return {"so_thu": so}


def doc_thu_hd(tho, doc_thu):
	"""Tách thư bằng đúng bộ đọc của hộp thư đối soát, rồi lấy cả .xml, .pdf, .zip.
	Bộ đọc kia chỉ giữ đuôi tệp đối soát, nên lấy lại tệp ở đây."""
	import email
	from email import policy

	from vagabond.doi_soat_thu import _phan_tep

	d = doc_thu(tho)
	msg = email.message_from_bytes(tho, policy=policy.default)
	tep = []
	for p in _phan_tep(msg):
		ten = p.get_filename()
		if ten and ten.lower().endswith((".xml", ".pdf", ".zip")):
			b = p.get_payload(decode=True) or b""
			if b and len(b) <= TOI_DA_TEP:
				tep.append((ten.replace("/", "_").replace("\\", "_")[:140], b))
	d["tep"] = tep
	return d


def _ung_vien(hd):
	frappe = _frappe()
	mst = str(hd.get("mst_ban") or "").split("-")[0]
	if not frappe.db.exists("DocType", DT_HD):
		return []
	so = so_nguyen(hd.get("so"))
	if not (mst and so):
		return []
	# Lọc cả theo số: nhà cung cấp lâu năm có hàng trăm tờ, chỉ lấy trang đầu theo
	# MST là có thể bỏ sót đúng tờ cần khớp (H8 loại 2). chon_hd so khớp chính xác.
	return frappe.get_all(DT_HD, filters={"loai": "Đầu vào", "mst_doi_tac": ["like", mst + "%"], "so_hd": ["like", "%" + str(so)]},
		fields=["name", "mst_doi_tac", "so_hd", "ky_hieu"], limit_page_length=0, order_by="ngay_lap desc")


def _dinh(b, ten, dt, ten_doc):
	"""Lưu tệp riêng tư gắn vào một bản ghi; đã có cùng tên thì thôi."""
	frappe = _frappe()
	if frappe.db.exists("File", {"attached_to_doctype": dt, "attached_to_name": ten_doc, "file_name": ten}):
		return None
	f = frappe.get_doc({"doctype": "File", "file_name": ten, "attached_to_doctype": dt, "attached_to_name": ten_doc,
		"content": b, "is_private": 1})
	f.flags.ignore_permissions = True
	f.insert(ignore_permissions=True)
	return f.name


def xu_ly_thu(d, uid):
	"""Một thư: ghi một dòng Hoá đơn thư cho mỗi XML hoá đơn (hoặc một dòng chỉ
	đường dẫn), đính tệp vào dòng đó, rồi thử khớp ngay."""
	frappe = _frappe()
	if d.get("message_id") and frappe.db.exists(DT, {"message_id": d["message_id"]}):
		return 0
	xml, pdf = phan_loai_tep(d.get("tep"))
	hds = [(t, b, doc_xml(b)) for t, b in xml]
	hds = [x for x in hds if x[2]]
	chung = {"tieu_de": d.get("tieu_de"), "nguoi_gui": d.get("nguoi_gui"), "gui_luc": d.get("gui_luc") or None,
		"uid": str(uid), "message_id": d.get("message_id")}
	if not hds:
		link = duong_dan_hd(d.get("than"))
		tt = TT_LINK if link else (TT_LOI if pdf else TT_KHONG)
		doc = frappe.get_doc(dict(chung, doctype=DT, trang_thai=tt, duong_dan="\n".join(link),
			ghi_chu="Thư chỉ có PDF, không có XML để khớp; Thu mua đính tay." if (pdf and not link) else ""))
		doc.insert(ignore_permissions=True)
		for t, b in pdf:
			_dinh(b, t, DT, doc.name)
		return 1
	for t, b, hd in hds:
		doc = frappe.get_doc(dict(chung, doctype=DT, trang_thai=TT_CHO, mst_ban=hd["mst_ban"], ten_ban=hd["ten_ban"],
			ky_hieu=(hd["mau"] or "") + (hd["ky_hieu"] or ""), so_hd=hd["so"], ngay_hd=hd["ngay"] or None, tong_tien=hd["tong"]))
		doc.insert(ignore_permissions=True)
		_dinh(b, ten_xml(doc.ky_hieu, hd["so"]), DT, doc.name)
		# Thư một hoá đơn thì mọi PDF thuộc hoá đơn đó; nhiều hoá đơn thì chỉ nhận
		# PDF có số hoá đơn trong tên tệp.
		for tp, bp in pdf:
			if len(hds) == 1 or str(so_nguyen(hd["so"])) in re.sub(r"\D", " ", tp).split():
				_dinh(bp, tp, DT, doc.name)
		khop(doc.name)
	return len(hds)


def khop(ten):
	"""Khớp một dòng Chờ khớp với hoá đơn M-Invoice; khớp thì đính PDF (đúng tên
	HDDT-...) vào hoá đơn M-Invoice và XML vào hoá đơn mua."""
	from vagabond.minvoice_tep import ten_tep_pdf

	frappe = _frappe()
	d = frappe.get_doc(DT, ten)
	if d.trang_thai != TT_CHO:
		return 0
	hd = {"mst_ban": d.mst_ban, "so": d.so_hd, "ky_hieu": d.ky_hieu}
	u = chon_hd(hd, _ung_vien(hd))
	if not u:
		return 0
	tep = frappe.get_all("File", filters={"attached_to_doctype": DT, "attached_to_name": ten},
		fields=["name", "file_name"], limit_page_length=20)
	pi = frappe.db.get_value("Purchase Invoice", {"custom_minvoice_id": u["name"], "docstatus": ["<", 2]}, "name")
	for f in tep:
		b = frappe.get_doc("File", f["name"]).get_content()
		if f["file_name"].lower().endswith(".pdf"):
			# Bản của chính nhà cung cấp thay chỗ bản M-Invoice vẽ lại trong chuỗi
			# đính APP (minvoice_tep._pdf_dang_co lấy tệp mới nhất tên HDDT-).
			# Đuôi -NCC để không trùng tên bản M-Invoice đã kéo trước đó; tệp mới
			# hơn nên _pdf_dang_co chọn bản của nhà cung cấp.
			_dinh(b, ten_tep_pdf(u.get("ky_hieu") or d.ky_hieu, u.get("so_hd") or d.so_hd)[:-4] + "-NCC.pdf", DT_HD, u["name"])
		elif pi:
			_dinh(b, f["file_name"], "Purchase Invoice", pi)
	d.db_set({"trang_thai": TT_DINH, "hd_dien_tu": u["name"], "hoa_don_mua": pi or None}, update_modified=True)
	return 1


def khop_lai(so_ngay=30):
	"""Thử khớp lại các dòng Chờ khớp trong so_ngay ngày (M-Invoice kéo về sau thư)."""
	frappe = _frappe()
	r = frappe.db.sql("select get_lock('vgb_hd_khop', 0)")
	if not r or r[0][0] != 1:
		return 0
	try:
		return _khop_lai(so_ngay)
	finally:
		frappe.db.sql("select release_lock('vgb_hd_khop')")


def _khop_lai(so_ngay):
	frappe = _frappe()
	n = 0
	for ten in frappe.get_all(DT, filters={"trang_thai": TT_CHO, "creation": [">", frappe.utils.add_days(frappe.utils.nowdate(), -so_ngay)]},
			pluck="name", limit_page_length=200):
		try:
			n += khop(ten)
			frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "hoa_don_thu: khớp lại %s" % ten)
	return n


def viec(vai):
	"""Việc cần làm cho Thu mua: thư chỉ có đường dẫn, thư chỉ PDF, dòng chờ khớp
	quá 3 ngày (M-Invoice không có tờ nào khớp)."""
	frappe = _frappe()
	from vagabond.ho_so_tt import VAI_LAP
	from vagabond import viec_tu_dong as vtd

	if not (set(vai or ()) & VAI_LAP):
		return []
	ra = []
	han = frappe.utils.add_days(frappe.utils.nowdate(), -3)
	for r in frappe.get_all(DT, filters={"trang_thai": ["in", [TT_LINK, TT_LOI, TT_CHO]]},
			fields=["name", "tieu_de", "trang_thai", "so_hd", "ten_ban", "gui_luc", "creation"], order_by="creation asc", limit_page_length=50):
		if r.trang_thai == TT_CHO and str(r.creation)[:10] > str(han):
			continue
		phu = {TT_LINK: "Thư chỉ có đường dẫn, tải hoá đơn về đính tay", TT_LOI: "Thư chỉ có PDF, đính tay vào hoá đơn mua",
			TT_CHO: "Chưa khớp hoá đơn M-Invoice nào sau 3 ngày"}[r.trang_thai]
		ra.append(vtd.dong_viec("hoa_don_thu", r.name, r.ten_ban or r.tieu_de or "Hoá đơn trong thư",
			"%s%s" % (phu, (" · HĐ " + r.so_hd) if r.so_hd else ""), r.gui_luc or r.creation, False))
	return ra


@frappe.whitelist(methods=["POST"])
def doc_ngay():
	"""Nút "Đọc hộp thư hoá đơn ngay" (quản trị, kế toán)."""
	if not ({"System Manager", "Accounts Manager"} & set(frappe.get_roles())):
		frappe.throw("Chỉ kế toán trưởng hoặc quản trị hệ thống bấm đọc hộp thư hoá đơn.")
	ch = cau_hinh()
	if not ch["mat_khau"]:
		frappe.throw("Dán mật khẩu hộp thư %s vào ô Mật khẩu hộp thư hoá đơn, bấm Lưu, rồi bấm lại." % ch["dia_chi"])
	kq = doc_hop_thu(ch)
	kq["khop_them"] = khop_lai()
	return kq
