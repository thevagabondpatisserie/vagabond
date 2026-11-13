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

v654 (anh Việt 13/11/2026, ca HDM-26-11-00195 An Phú số 8882)
--------------------------------------------------------------
Đo trên site 13/11 11:17: hộp thư chỉ bắt đầu được đọc lúc 10:20 hôm nay, và
máy đọc từ thư CŨ NHẤT (13/08) lên, 40 thư mỗi giờ: tới 11:17 mới tới thư
20/08, còn gần ba tháng thư phía trước, nên thư hoá đơn ngày 12/11 phải chờ
khoảng hai ngày. Từ v654:
- Đọc thư MỚI NHẤT trước, phần thư cũ đọc dần phía sau. Mốc đọc là danh sách
  khoảng UID đã xong (`khoang`), không còn là một con trỏ chỉ đi lên.
- Nhịp 15 phút thay cho mỗi giờ.
- Khớp thêm điều kiện người mua: MST người mua trên XML phải là MST của công
  ty; khác thì không đính, ghi rõ lý do.
- Thư gửi lại (cùng hoá đơn, khác mã thư) không tạo dòng thứ hai: bổ sung tệp
  còn thiếu vào dòng đã có.
- Chưa khớp được thì ghi lý do (chưa có M-Invoice, nhiều tờ trùng) để kế toán
  thấy trên màn Hoá đơn mua vào.
- Nút "Quét lại thư cũ": đọc lại từ một ngày, chỉ bổ sung tệp còn thiếu,
  không tạo hoá đơn hay tệp trùng (chống trùng theo mã thư và tên tệp).

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
# Đã khớp M-Invoice nhưng còn thiếu tệp (chưa có hoá đơn mua để đính XML, hay
# PDF trong thư không khớp số hoá đơn). Nhịp khớp lại thử tiếp (Codex #560).
TT_THIEU = "Thiếu tệp"
# Một thư đọc hỏng (máy chủ không trả nội dung, lỗi ghi) thì lượt sau đọc lại;
# hỏng đủ số lần này thì thành Việc cần làm cho Thu mua (Codex #560).
SO_LAN_THU = 5
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


def pdf_cua_so(ten_tep, so):
	"""THUẦN. Tên tệp PDF có chứa số hoá đơn không. Bỏ số 0 đầu ở CẢ HAI phía:
	00001234.pdf và HD_1234.pdf đều là hoá đơn 1234 (Codex #560)."""
	n = so_nguyen(so)
	if not n:
		return False
	return any(so_nguyen(t) == n for t in re.findall(r"\d+", str(ten_tep or "")))


def con_thieu(co_xml, co_pdf, co_hoa_don_mua, so_pdf_trong_thu):
	"""THUẦN. Những việc còn thiếu của một dòng đã khớp M-Invoice; rỗng là xong."""
	ra = []
	if co_xml and not co_hoa_don_mua:
		ra.append("Chờ hoá đơn mua trên ERP để đính XML (máy tự thử lại mỗi 15 phút)")
	if not co_pdf and int(so_pdf_trong_thu or 0) > 0:
		ra.append("PDF trong thư không khớp số hoá đơn: đính tay PDF vào dòng này, máy tự chuyển sang hoá đơn")
	return ra


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


def _so(x):
	try:
		return int(x)
	except (TypeError, ValueError):
		return None


def da_xong(uid, khoang, thu_lai=None):
	"""UID này đã đọc xong chưa: nằm trong một khoảng đã xong và không đang chờ
	đọc lại. THUẦN."""
	if thu_lai and (uid in thu_lai or str(uid) in thu_lai):
		return False
	return any(a <= uid <= b for a, b in khoang or [])


def them_khoang(khoang, xong, tat_ca):
	"""Gộp các UID vừa đọc xong vào danh sách khoảng. Hai khoảng nối nhau khi
	giữa chúng không còn thư nào của hộp thư (theo danh sách tat_ca). THUẦN."""
	ds = sorted([list(k) for k in khoang or []] + [[u, u] for u in xong or []])
	tat = sorted(set(tat_ca or []))
	ra = []
	for a, b in ds:
		if ra:
			pa, pb = ra[-1]
			giua = [u for u in tat if pb < u < a]
			if a <= pb + 1 or not giua:
				ra[-1][1] = max(pb, b)
				continue
		ra.append([a, b])
	return ra


def bo_tu(khoang, u0):
	"""Bỏ dấu đã xong của mọi UID từ u0 trở lên (quét lại thư cũ). THUẦN."""
	ra = []
	for a, b in khoang or []:
		if b < u0:
			ra.append([a, b])
		elif a < u0:
			ra.append([a, u0 - 1])
	return ra


def chon_luot(tat_ca, khoang, thu_lai, toi_da):
	"""UID cần đọc lượt này: thư MỚI NHẤT trước (v654), tối đa toi_da. THUẦN."""
	con = [u for u in sorted(set(tat_ca or []), reverse=True) if not da_xong(u, khoang, thu_lai)]
	return con[:toi_da]


def moc_khoang(moc, tat_ca):
	"""Đọc mốc cũ hay mới thành (khoảng, thư chờ đọc lại). Mốc v653 chỉ có một
	con trỏ uid (mọi thư tới uid đã đọc) thì đổi thành một khoảng. THUẦN."""
	thu_lai = {int(k): int(v) for k, v in (moc.get("thu_lai") or {}).items()}
	if moc.get("khoang") is not None:
		return [[int(a), int(b)] for a, b in moc["khoang"]], thu_lai
	cu = _so(moc.get("uid")) or 0
	if not cu:
		return [], thu_lai
	thap = min([u for u in tat_ca or [] if u <= cu] or [cu])
	return [[thap, cu]], thu_lai


THANG_IMAP = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def ngay_imap(v):
	"""2026-11-01 thành 01-Nov-2026 (cú pháp SINCE của IMAP). THUẦN."""
	y, m, d = str(v)[:10].split("-")
	return "%02d-%s-%s" % (int(d), THANG_IMAP[int(m) - 1], y)


def mst_goc(v):
	return re.sub(r"[^0-9]", "", str(v or "").split("-")[0])


def nguoi_mua_sai(mst_mua, mst_cong_ty):
	"""Câu lý do khi XML ghi người mua không phải công ty; None là đúng hoặc XML
	không ghi MST người mua (hộ kinh doanh xuất cho khách lẻ). THUẦN."""
	m = mst_goc(mst_mua)
	ct = {mst_goc(x) for x in mst_cong_ty or [] if mst_goc(x)}
	if not m or not ct or m in ct:
		return None
	return ("Hoá đơn ghi người mua MST %s, không phải MST công ty (%s). Máy không đính vào hoá đơn mua nào; "
		"nhà cung cấp gửi nhầm thì nhờ họ xuất lại." % (m, ", ".join(sorted(ct))))


def ly_do_chua_khop(hd, ung_vien):
	"""Lý do chưa khớp một dòng (cho kế toán đọc). THUẦN."""
	mst = mst_goc(hd.get("mst_ban"))
	so = so_nguyen(hd.get("so"))
	cung = [u for u in ung_vien or [] if mst_goc(u.get("mst_doi_tac")) == mst and so_nguyen(u.get("so_hd")) == so]
	khop = [u for u in cung if khop_ky_hieu(u.get("ky_hieu"), hd.get("ky_hieu"))]
	if len(khop) > 1:
		return "Có %d hoá đơn M-Invoice cùng MST, số và ký hiệu: kế toán chọn tay tờ đúng." % len(khop)
	if cung and not khop:
		return "Có hoá đơn M-Invoice cùng MST và số nhưng khác ký hiệu (%s): kế toán xem lại." % ", ".join(
			sorted({str(u.get("ky_hieu") or "") for u in cung}))
	return "Chưa thấy hoá đơn M-Invoice đầu vào cùng MST %s số %s: chờ M-Invoice kéo về, máy tự thử lại." % (mst, so)


def la_cung_hoa_don(a, b):
	"""Hai dòng (thư) cùng một hoá đơn: cùng MST người bán, số, ký hiệu khớp. THUẦN."""
	return (mst_goc(a.get("mst_ban")) == mst_goc(b.get("mst_ban")) and so_nguyen(a.get("so_hd")) == so_nguyen(b.get("so_hd"))
		and so_nguyen(a.get("so_hd")) and khop_ky_hieu(a.get("ky_hieu"), b.get("ky_hieu")))


def ly_do_tep(co_xml, co_pdf, dong):
	"""Lý do thiếu tệp hiện dưới hoá đơn mua; dong là dòng Hoá đơn thư khớp với nó
	(hoặc None). Rỗng khi đủ hai tệp hoặc chưa có dòng thư nào. THUẦN."""
	if co_xml and co_pdf:
		return ""
	if not dong:
		return ""
	if dong.get("trang_thai") in (TT_CHO, TT_THIEU, TT_LOI) and dong.get("ghi_chu"):
		return dong.get("ghi_chu")
	thieu = [x for x, co in (("XML", co_xml), ("PDF", co_pdf)) if not co]
	return "Thư hoá đơn của nhà cung cấp không kèm %s. Cần thì xin nhà cung cấp gửi lại." % " và ".join(thieu)


def nhan_tep(ten_tep):
	"""Phân tệp đính kèm theo đuôi: 'xml', 'pdf' hay None. THUẦN."""
	t = str(ten_tep or "").lower()
	return "xml" if t.endswith(".xml") else "pdf" if t.endswith(".pdf") else None


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
	"""Lịch 15 phút (v654): đọc thư mới nhất trước, rồi thử khớp lại các dòng Chờ khớp."""
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
	"""Đọc thư chưa đọc, MỚI NHẤT trước (v654), mỗi lượt tối đa TOI_DA_MOI_LUOT
	thư. Khoá có tên để lịch và nút "Đọc ngay" không chạy chồng."""
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
			cung = int(moc.get("uv") or 0) == uv
			kq, du = m.uid("search", None, "SINCE", BAT_DAU)
			tat_ca = sorted(int(x) for x in (du[0] or b"").split()) if kq == "OK" else []
			khoang, thu_lai = moc_khoang(moc, tat_ca) if cung else ([], {})
			if cung and moc.get("quet_lai_tu"):
				# Nút "Quét lại thư cũ": bỏ dấu đã xong từ thư đầu tiên của ngày đó.
				kq2, du2 = m.uid("search", None, "SINCE", ngay_imap(moc["quet_lai_tu"]))
				tu = sorted(int(x) for x in (du2[0] or b"").split()) if kq2 == "OK" else []
				if tu:
					khoang = bo_tu(khoang, tu[0])
			for uid in chon_luot(tat_ca, khoang, thu_lai, TOI_DA_MOI_LUOT):
				ok = False
				try:
					kq, du = m.uid("fetch", str(uid), "(BODY.PEEK[])")
					tho = next((x[1] for x in (du or []) if isinstance(x, tuple) and len(x) > 1), None)
					if not tho:
						raise RuntimeError("Máy chủ thư không trả nội dung thư UID %s." % uid)
					xu_ly_thu(doc_thu_hd(tho, doc_thu), uid)
					frappe.db.commit()
					ok = True
				except Exception:
					frappe.db.rollback()
					frappe.log_error(frappe.get_traceback(), "hoa_don_thu: thư UID %s" % uid)
				xong = ok
				if ok:
					thu_lai.pop(uid, None)
				else:
					n = thu_lai.get(uid, 0) + 1
					if n >= SO_LAN_THU:
						thu_lai.pop(uid, None)
						_ghi_thu_hong(uid, n)
						xong = True
					else:
						thu_lai[uid] = n
				so += 1
				if xong:
					khoang = them_khoang(khoang, [uid], tat_ca)
				_ghi_moc({"uv": uv, "khoang": khoang, "luc": str(frappe.utils.now_datetime())[:19],
					"thu_lai": {str(k): v for k, v in sorted(thu_lai.items())},
					"con": len([u for u in tat_ca if not da_xong(u, khoang, thu_lai)])})
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


def _ghi_thu_hong(uid, so_lan):
	"""Thư đọc hỏng đủ SO_LAN_THU lần: một dòng Lỗi để Thu mua tìm thư và đính tay."""
	frappe = _frappe()
	if frappe.db.exists(DT, {"uid": str(uid), "trang_thai": TT_LOI}):
		return
	doc = frappe.get_doc({"doctype": DT, "trang_thai": TT_LOI, "uid": str(uid),
		"tieu_de": "Thư UID %s máy đọc không được" % uid,
		"ghi_chu": "Máy đọc thư này hỏng %d lần. Mở webmail hoadon@, tìm thư theo UID hay giờ nhận, tải hoá đơn về đính tay." % so_lan})
	doc.insert(ignore_permissions=True)


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


def _mst_cong_ty():
	frappe = _frappe()
	try:
		return [r.tax_id for r in frappe.get_all("Company", fields=["tax_id"], limit_page_length=0) if r.get("tax_id")]
	except Exception:
		return []


def _bo_sung(ten_doc, tep):
	"""Đính các tệp còn thiếu (theo tên) vào một dòng đã có. Trả số tệp mới."""
	n = 0
	for t, b in tep:
		if _dinh(b, t, DT, ten_doc):
			n += 1
	return n


def _dong_cung_hd(hd):
	"""Dòng Hoá đơn thư đã có cho đúng hoá đơn này (thư gửi lại), nếu có."""
	frappe = _frappe()
	so = so_nguyen(hd.get("so"))
	if not so:
		return None
	for r in frappe.get_all(DT, filters={"mst_ban": ["like", mst_goc(hd.get("mst_ban")) + "%"],
			"so_hd": ["like", "%" + str(so)]}, fields=["name", "mst_ban", "so_hd", "ky_hieu"],
			order_by="creation asc", limit_page_length=0):
		if la_cung_hoa_don(r, {"mst_ban": hd.get("mst_ban"), "so_hd": hd.get("so"),
				"ky_hieu": (hd.get("mau") or "") + (hd.get("ky_hieu") or "")}):
			return r.name
	return None


def xu_ly_thu(d, uid):
	"""Một thư: ghi một dòng Hoá đơn thư cho mỗi XML hoá đơn (hoặc một dòng chỉ
	đường dẫn), đính tệp vào dòng đó, rồi thử khớp ngay.

	v654: thư đã đọc (cùng mã thư, quét lại) hay thư gửi lại cùng hoá đơn thì
	chỉ bổ sung tệp còn thiếu vào dòng đã có, không tạo dòng hay tệp trùng."""
	frappe = _frappe()
	xml, pdf = phan_loai_tep(d.get("tep"))
	hds = [(t, b, doc_xml(b)) for t, b in xml]
	hds = [x for x in hds if x[2]]
	if d.get("message_id") and frappe.db.exists(DT, {"message_id": d["message_id"]}):
		n = 0
		for ten in frappe.get_all(DT, filters={"message_id": d["message_id"]}, pluck="name", limit_page_length=0):
			dong = frappe.get_doc(DT, ten)
			cua = [(t, b) for t, b, hd in hds if not dong.so_hd or so_nguyen(hd["so"]) == so_nguyen(dong.so_hd)]
			for t, b in cua:
				if _dinh(b, ten_xml(dong.ky_hieu, dong.so_hd), DT, ten):
					n += 1
			n += _bo_sung(ten, [(tp, bp) for tp, bp in pdf if len(hds) <= 1 or pdf_cua_so(tp, dong.so_hd)])
			if dong.trang_thai in (TT_CHO, TT_THIEU) or n:
				khop(ten, bo_sung=bool(n))
		return 0
	chung = {"tieu_de": d.get("tieu_de"), "nguoi_gui": d.get("nguoi_gui"), "gui_luc": d.get("gui_luc") or None,
		"uid": str(uid), "message_id": d.get("message_id"), "pdf_trong_thu": len(pdf)}
	if not hds:
		link = duong_dan_hd(d.get("than"))
		tt = TT_LINK if link else (TT_LOI if pdf else TT_KHONG)
		doc = frappe.get_doc(dict(chung, doctype=DT, trang_thai=tt, duong_dan="\n".join(link),
			ghi_chu="Thư chỉ có PDF, không có XML để khớp; Thu mua đính tay." if (pdf and not link) else ""))
		doc.insert(ignore_permissions=True)
		for t, b in pdf:
			_dinh(b, t, DT, doc.name)
		return 1
	ct = _mst_cong_ty()
	moi = 0
	for t, b, hd in hds:
		ky = (hd["mau"] or "") + (hd["ky_hieu"] or "")
		cua_pdf = [(tp, bp) for tp, bp in pdf if len(hds) == 1 or pdf_cua_so(tp, hd["so"])]
		sai = nguoi_mua_sai(hd.get("mst_mua"), ct)
		cu = None if sai else _dong_cung_hd(hd)
		if cu:
			# Thư gửi lại cùng hoá đơn: bổ sung tệp vào dòng đã có.
			n = (1 if _dinh(b, ten_xml(ky, hd["so"]), DT, cu) else 0) + _bo_sung(cu, cua_pdf)
			if n or frappe.db.get_value(DT, cu, "trang_thai") in (TT_CHO, TT_THIEU):
				khop(cu, bo_sung=bool(n))
			continue
		doc = frappe.get_doc(dict(chung, doctype=DT, trang_thai=TT_LOI if sai else TT_CHO, mst_ban=hd["mst_ban"],
			ten_ban=hd["ten_ban"], ky_hieu=ky, so_hd=hd["so"], ngay_hd=hd["ngay"] or None, tong_tien=hd["tong"],
			ghi_chu=sai or ""))
		doc.insert(ignore_permissions=True)
		moi += 1
		_dinh(b, ten_xml(doc.ky_hieu, hd["so"]), DT, doc.name)
		# Thư một hoá đơn thì mọi PDF thuộc hoá đơn đó; nhiều hoá đơn thì chỉ nhận
		# PDF có số hoá đơn trong tên tệp.
		_bo_sung(doc.name, cua_pdf)
		if not sai:
			khop(doc.name)
	return moi


def khop(ten, bo_sung=False):
	"""Khớp một dòng Chờ khớp với hoá đơn M-Invoice; khớp thì đính PDF (đúng tên
	HDDT-...) vào hoá đơn M-Invoice và XML vào hoá đơn mua.

	bo_sung (v654): dòng đã Đã đính vừa được thêm tệp (thư gửi lại, quét lại)
	thì chuyển tiếp tệp mới sang hoá đơn; tệp đã có theo tên thì bỏ qua."""
	from vagabond.minvoice_tep import ten_tep_pdf

	frappe = _frappe()
	d = frappe.get_doc(DT, ten)
	if d.trang_thai not in ((TT_CHO, TT_THIEU, TT_DINH) if bo_sung else (TT_CHO, TT_THIEU)):
		return 0
	hd = {"mst_ban": d.mst_ban, "so": d.so_hd, "ky_hieu": d.ky_hieu}
	uv = _ung_vien(hd)
	u = chon_hd(hd, uv)
	if not u:
		# v654: nói rõ vì sao chưa khớp, để kế toán thấy trên màn Hoá đơn mua vào.
		ly = ly_do_chua_khop(hd, uv)
		if (d.get("ghi_chu") or "") != ly:
			d.db_set({"ghi_chu": ly}, update_modified=False)
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
	ten_tep = [str(f["file_name"]).lower() for f in tep]
	# Codex #560: chỉ Đã đính khi đủ tệp. Chưa có hoá đơn mua (XML chưa đính)
	# hay PDF không khớp thì Thiếu tệp, nhịp khớp lại thử tiếp.
	thieu = con_thieu(any(t.endswith(".xml") for t in ten_tep), any(t.endswith(".pdf") for t in ten_tep), bool(pi),
		d.get("pdf_trong_thu"))
	d.db_set({"trang_thai": TT_THIEU if thieu else TT_DINH, "hd_dien_tu": u["name"], "hoa_don_mua": pi or None,
		"ghi_chu": "; ".join(thieu)}, update_modified=True)
	return 0 if thieu else 1


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
	for ten in frappe.get_all(DT, filters={"trang_thai": ["in", [TT_CHO, TT_THIEU]], "creation": [">", frappe.utils.add_days(frappe.utils.nowdate(), -so_ngay)]},
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
	for r in frappe.get_all(DT, filters={"trang_thai": ["in", [TT_LINK, TT_LOI, TT_CHO, TT_THIEU]]},
			fields=["name", "tieu_de", "trang_thai", "so_hd", "ten_ban", "gui_luc", "creation", "ghi_chu"], order_by="creation asc", limit_page_length=50):
		if r.trang_thai in (TT_CHO, TT_THIEU) and str(r.creation)[:10] > str(han):
			continue
		phu = {TT_LINK: "Thư chỉ có đường dẫn, tải hoá đơn về đính tay", TT_LOI: r.get("ghi_chu") or "Thư chỉ có PDF, đính tay vào hoá đơn mua",
			TT_CHO: "Chưa khớp hoá đơn M-Invoice nào sau 3 ngày", TT_THIEU: r.get("ghi_chu") or "Còn thiếu tệp"}[r.trang_thai]
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


@frappe.whitelist(methods=["POST"])
def quet_lai(tu_ngay=None):
	"""Nút "Quét lại thư cũ" (kế toán trưởng, quản trị): lượt đọc sau đọc lại
	mọi thư từ tu_ngay, chỉ bổ sung tệp còn thiếu. Không tạo dòng, hoá đơn hay
	tệp trùng: thư đã có theo mã thư, tệp đã có theo tên."""
	if not ({"System Manager", "Accounts Manager"} & set(frappe.get_roles())):
		frappe.throw("Chỉ kế toán trưởng hoặc quản trị hệ thống quét lại hộp thư hoá đơn.")
	tu = str(tu_ngay or "2026-08-13")[:10]
	try:
		frappe.utils.getdate(tu)
	except Exception:
		frappe.throw("Ngày bắt đầu quét lại không hợp lệ: %s." % tu)
	m = _moc()
	m["quet_lai_tu"] = tu
	_ghi_moc(m)
	frappe.db.commit()
	return {"ok": 1, "tu": tu}


def gan_tep(rows):
	"""Thêm `tep_xml`, `tep_pdf` (đường dẫn tệp thật đang có) và `tep_ly_do` vào các
	dòng hoá đơn mua (cần name, custom_minvoice_id). Màn Hoá đơn mua vào hiện nhãn
	XML, PDF bấm mở được; thiếu thì hiện lý do (v654). Một lượt đọc cho cả trang."""
	frappe = _frappe()
	if not rows:
		return rows
	pi = [r["name"] for r in rows]
	mi = [r.get("custom_minvoice_id") for r in rows if r.get("custom_minvoice_id")]
	tep = frappe.get_all("File", filters={"attached_to_doctype": ["in", ["Purchase Invoice", DT_HD]],
		"attached_to_name": ["in", pi + mi]}, fields=["attached_to_name", "file_name", "file_url", "creation"],
		order_by="creation desc", limit_page_length=0)
	theo = {}
	for f in tep:
		k = nhan_tep(f.get("file_name"))
		if k:
			o = theo.setdefault(f.get("attached_to_name"), {})
			# Bản của chính nhà cung cấp (-NCC) đứng trước bản M-Invoice vẽ lại.
			if k not in o or str(f.get("file_name") or "").endswith("-NCC.pdf"):
				o[k] = f.get("file_url")
	ly = {}
	if mi:
		for r in frappe.get_all(DT, filters={"hd_dien_tu": ["in", mi]}, fields=["name", "hd_dien_tu", "ghi_chu", "trang_thai"],
				order_by="creation desc", limit_page_length=0):
			ly.setdefault(r.hd_dien_tu, r)
	con = int(_moc().get("con") or 0)
	for r in rows:
		a = theo.get(r["name"], {})
		b = theo.get(r.get("custom_minvoice_id"), {})
		r["tep_xml"] = a.get("xml") or b.get("xml") or ""
		r["tep_pdf"] = a.get("pdf") or b.get("pdf") or ""
		r["tep_ly_do"] = ly_do_tep(r["tep_xml"], r["tep_pdf"], ly.get(r.get("custom_minvoice_id")))
		if not (r["tep_xml"] and r["tep_pdf"]) and not r["tep_ly_do"]:
			r["tep_ly_do"] = ("Chưa thấy thư hoá đơn này trong hộp thư %s" % DIA_CHI_MAC_DINH) + (
				" (máy còn %d thư chưa đọc, đọc mới nhất trước)" % con if con else "")
	return rows

