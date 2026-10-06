"""v579 (#420): đối soát nhà cung cấp chạy thật trên site.

Tầng khung kiểm từng phép thuần (đọc mẫu, xem trước, luật nối). Nó không
chứng minh được: hai doctype mới đã dựng đúng khoá duy nhất sau migrate, tệp
riêng tư ghi được, dòng đã nhận không nhân đôi khi kế toán tải lại hoặc tải
báo cáo tháng chứa các ngày đã có, dòng GrabFood nối đúng Hoá đơn bán thật
theo mã, tổng thực nhận gặp đúng Giao dịch ngân hàng thật, và hook thư chỉ
xếp việc cho thư vendor. Các ca dưới dựng hoá đơn, giao dịch, tệp THẬT trong
điểm lưu của nen.py rồi gọi đúng cửa màn hình như kế toán bấm.

Anh Việt 06/10/2026: bấm nhận CHỈ LƯU VÀ ĐỐI CHIẾU. Ca cuối chốt điều đó
trên site: nhận xong không thêm Journal Entry, Payment Entry nào.

Nội dung tệp: bộ đọc PDF cần PyMuPDF và tệp PDF thật; tầng khung đã kiểm
phép đọc trên chữ đã tách. Ở đây thay đúng một bước doc_tep bằng chữ đã tách
để ca không phụ thuộc phông chữ khi dựng PDF, mọi bước sau chạy thật.
"""
import base64
import json
from unittest.mock import patch

import frappe
from frappe.utils import flt, nowdate

from vagabond import doi_soat_doc as tep_doc
from vagabond import doi_soat_vendor as dv
from vagabond import ban_hang
from vagabond.khung.kiem_that.nen import ca, la, dung, _DA_TAO
from vagabond.khung.kiem_that.thu_cua_thue_243 import _nen, _mon
from vagabond.khung.kiem_that.thu_ho_so_tt_v445 import _tk_ngan_hang
from vagabond.khung.kiem_that.thu_sepay_mb_247 import _tai_khoan_cong_ty_moi
from vagabond.khung.kiem_that.thu_gom_phap_nhan_576 import _khach


_THANG = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9", 10: "10", 11: "11", 12: "12"}


def _bao_cao_grab(ngay, ma_so):
	"""Chữ đã tách của một báo cáo ngày GrabFood (cùng hình dạng với tầng khung)."""
	y, m, d = ngay.split("-")
	return [
		"Báo cáo kinh doanh hàng ngày",
		"%s tháng %s %s, thứ hai                                     https://grb.to/hotrodoitacnhahang" % (int(d), _THANG[int(m)], y),
		"The Vagabond Pâtisserie & Café - Trần Cao Vân",
		"Tóm tắt thông tin",
		"  Tổng thu nhập          Còn thiếu Grab          Tổng số đơn hàng",
		" VND 355.617              VND 0          2 đơn hàng",
		"Thu nhập",
		" 430.000   0   0   0   -61.383   -13.000   0   0   355.617   0",
		"Đơn hàng từ ứng dụng và web",
		" Đơn hàng Delivery",
		" 9:28 PM      GF-%s       Trả thẻ / Ví        260.000      0        -          0        -36.359       -13.000   210.641" % ma_so,
		" 12:42 PM     GF-%sF      Tiền mặt            170.000      0        -          0        -25.024             0   144.976" % (ma_so + 1),
		"                                                                                              355.617",
		" Tổng cộng                                       VND 355.617",
		"Hướng dẫn đọc hiểu báo cáo",
	]


def _tep(ten, dong, sha):
	return [dict(ten=ten, loai="pdf", sha256=sha, trang=[dict(ten="Trang 1", dong=dong)])]


def _ke_toan():
	u = frappe.get_doc({"doctype": "User", "email": "kt579-ketoan-%s@example.invalid" % frappe.generate_hash(length=8),
		"first_name": "Kiểm Kế toán 579", "enabled": 1, "send_welcome_email": 0,
		"roles": [{"role": "Accounts User"}]}).insert(ignore_permissions=True)
	_DA_TAO.append((u.doctype, u.name))
	return u.name


def _thu_ngan():
	u = frappe.get_doc({"doctype": "User", "email": "kt579-tn-%s@example.invalid" % frappe.generate_hash(length=8),
		"first_name": "Kiểm Thu ngân 579", "enabled": 1, "send_welcome_email": 0,
		"roles": [{"role": "Sales User"}]}).insert(ignore_permissions=True)
	_DA_TAO.append((u.doctype, u.name))
	return u.name


def _hd_grab(tk, cty, ma, tien):
	"""Hoá đơn GrabFood đã ghi sổ, thu ngân gõ mã GF-<số> như ở quầy."""
	from vagabond import diem_ban
	kh = _khach("Grab579")
	cac_diem = diem_ban.diem_cua_nguon("GrabFood")
	quay = next((x for x in cac_diem if not diem_ban.theo_ma(x)["quay"]), cac_diem[0])
	with patch.object(ban_hang, "_cong_ty", return_value=cty), patch.object(ban_hang, "_khach_le", return_value=kh):
		ra = ban_hang.tao_don_tay(nguon="GrabFood", quay=quay, ma_don="KT579-" + frappe.generate_hash(length=8),
			items=[dict(item_code=_mon(tk), qty=1, rate=tien)], tam_tinh=1)
	_DA_TAO.append(("Sales Invoice", ra["name"]))
	si = frappe.get_doc("Sales Invoice", ra["name"])
	si.vgb_tam_tinh = 0
	si.vgb_pt_thanh_toan = "GrabFood"
	si.vgb_ma_tham_chieu = ma
	si.save(ignore_permissions=True)
	si.submit(); si.reload()
	la("hoá đơn mang nguồn GrabFood", si.get("custom_nguon") in dv.NGUON_THEO_KIEU["grab"], True)
	la("tiền hoá đơn", int(round(flt(si.rounded_total or si.grand_total))), tien)
	return si


def _gd(ba, tien, mo_ta, ngay):
	ref = "FTKT579" + frappe.generate_hash(length=10)
	g = frappe.get_doc({"doctype": "Bank Transaction", "date": ngay, "bank_account": ba, "deposit": tien,
		"withdrawal": 0, "currency": "VND", "description": mo_ta, "reference_number": ref, "transaction_id": ref})
	g.insert(ignore_permissions=True); _DA_TAO.append((g.doctype, g.name))
	g.submit()
	return g


def _goi(ai, ham):
	truoc = frappe.session.user
	try:
		frappe.set_user(ai)
		return ham()
	finally:
		frappe.set_user(truoc)


def _pdf_hop_le(dau):
	"""PDF một trang tối thiểu nhưng ĐÚNG cấu trúc (có bảng xref). Frappe mở
	thử mọi PDF trước khi cất (dò mã chạy ngầm), nên byte giả "%PDF-1.4 ..."
	làm thư viện đọc PDF nổ và ca kiểm chết trước khi tới phần cần kiểm."""
	vat = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
		b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 10 10] >>"]
	ra = b"%PDF-1.4\n%" + dau.encode() + b"\n"
	vi_tri = []
	for i, v in enumerate(vat, 1):
		vi_tri.append(len(ra))
		ra += b"%d 0 obj\n" % i + v + b"\nendobj\n"
	xref = len(ra)
	ra += b"xref\n0 %d\n0000000000 65535 f \n" % (len(vat) + 1)
	ra += b"".join(b"%010d 00000 n \n" % x for x in vi_tri)
	ra += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(vat) + 1, xref)
	return ra


def _tai(ai, ten):
	noi = "data:application/pdf;base64," + base64.b64encode(_pdf_hop_le("KT579 " + frappe.generate_hash())).decode()
	up = _goi(ai, lambda: dv.tai_len(ten=ten, noi_dung=noi))
	_DA_TAO.append(("File", frappe.db.get_value("File", {"file_url": up["file_url"]}, "name")))
	return up["file_url"]


@ca("v579 site: hai doctype đối soát có khoá duy nhất, hook thư gắn sau khi lưu, không gắn trên '*'")
def _():
	la("mã băm tệp duy nhất", frappe.get_meta(dv.DT_NGUON).get_field("sha256").unique, 1)
	la("khoá sự kiện duy nhất", frappe.get_meta(dv.DT_DONG).get_field("khoa").unique, 1)
	sk = frappe.get_hooks("doc_events") or {}
	dung("hook Communication.after_insert", "vagabond.doi_soat_vendor.khi_co_thu" in
		(sk.get("Communication") or {}).get("after_insert", []))
	dung("không gắn trên mọi doctype", "vagabond.doi_soat_vendor.khi_co_thu" not in str((sk.get("*") or {})))


@ca("v579 site: tải báo cáo GrabFood, nối Hoá đơn bán thật theo mã, thấy tiền về, tải lại hay báo cáo tháng không nhân đôi")
def _():
	cty, tk, _mau = _nen()
	ngay = nowdate()
	so = int(frappe.generate_hash(length=6), 16) % 9000000 + 1000000
	si = _hd_grab(tk, cty, "GF-%s" % so, 260000)
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	g = _gd(ba, 355617, "Grab TT 118203316 KT579 Tran Cao Van", ngay)
	ai = _ke_toan()
	sha = "kt579-" + frappe.generate_hash(length=20)
	url = _tai(ai, "5-C4E1NPWGG2WZFA-%s.pdf" % ngay.replace("-", ""))
	with patch.object(tep_doc, "doc_tep", lambda ten, byte: _tep(ten, _bao_cao_grab(ngay, so), sha)), \
			patch.object(dv, "_cong_ty", return_value=cty):
		xt = _goi(ai, lambda: dv.xem_truoc(file_url=url))
		la("xem trước: hai dòng mới, chưa ghi gì", (xt[0]["so"], frappe.db.count(dv.DT_NGUON, {"sha256": sha})),
			(dict(moi=2, trung=0, loi=0), 0))
		ra = _goi(ai, lambda: dv.nhan(file_url=url))
		_DA_TAO.append((dv.DT_NGUON, ra[0]["name"]))
		n = frappe.get_doc(dv.DT_NGUON, ra[0]["name"])
		la("nguồn", (n.trang_thai, n.vendor, n.so_moi, int(n.thuc_nhan), n.kenh_nhan), ("Đã nhận", "GrabFood", 2, 355617, "Tải tay"))
		dong = {d.ma_don: d for d in frappe.get_all(dv.DT_DONG, filters={"nguon": n.name}, fields=["*"])}
		la("dòng GF nối đúng hoá đơn thật", (dong["GF-%s" % so].trang_thai_khop, dong["GF-%s" % so].sales_invoice), ("Đã nối", si.name))
		la("tiền về gặp giao dịch thật", (n.trang_thai_tien, n.giao_dich_ngan_hang), ("Đã thấy tiền về", g.name))
		la("khối trên hoá đơn", [r.nguon for r in _goi(ai, lambda: dv.cua_hoa_don(si=si.name))], [n.name])
		# Tải lại đúng tệp: dừng ở mã băm.
		ra2 = _goi(ai, lambda: dv.nhan(file_url=url))
		la("tải lại", (ra2[0]["name"], ra2[0]["da_co"]), (n.name, 1))
	# Báo cáo tháng chứa đúng các đơn đó, tệp khác (mã băm khác).
	sha_t = "kt579-thang-" + frappe.generate_hash(length=16)
	url_t = _tai(ai, "5-C4E1NPWGG2WZFA-thang.pdf")
	with patch.object(tep_doc, "doc_tep", lambda ten, byte: _tep(ten, _bao_cao_grab(ngay, so), sha_t)), \
			patch.object(dv, "_cong_ty", return_value=cty):
		ra3 = _goi(ai, lambda: dv.nhan(file_url=url_t))
	_DA_TAO.append((dv.DT_NGUON, ra3[0]["name"]))
	n3 = frappe.get_doc(dv.DT_NGUON, ra3[0]["name"])
	la("báo cáo tháng: đã có từ trước, không thêm dòng", (n3.so_moi, n3.so_trung, frappe.db.count(dv.DT_DONG, {"nguon": n3.name})), (0, 2, 0))
	la("hoá đơn vẫn chỉ nối một dòng", frappe.db.count(dv.DT_DONG, {"sales_invoice": si.name}), 1)
	_goi(ai, lambda: dv.doi_chieu_lai(name=n.name))
	la("đối chiếu lại không đổi", frappe.db.get_value(dv.DT_DONG, {"nguon": n.name, "ma_don": "GF-%s" % so}, "sales_invoice"), si.name)
	try:
		frappe.get_doc(dv.DT_NGUON, n.name).delete(ignore_permissions=True)
		xoa = True
	except frappe.ValidationError:
		xoa = False
	la("không xoá được nguồn đã nhận", xoa, False)


@ca("v579 site: nhận xong chỉ lưu và đối chiếu, không lập Journal Entry hay Payment Entry")
def _():
	cty, tk, _mau = _nen()
	ngay = nowdate()
	so = int(frappe.generate_hash(length=6), 16) % 9000000 + 1000000
	ai = _ke_toan()
	truoc = (frappe.db.count("Journal Entry"), frappe.db.count("Payment Entry"))
	url = _tai(ai, "grab-kt579.pdf")
	sha = "kt579-pe-" + frappe.generate_hash(length=16)
	with patch.object(tep_doc, "doc_tep", lambda ten, byte: _tep(ten, _bao_cao_grab(ngay, so), sha)), \
			patch.object(dv, "_cong_ty", return_value=cty):
		ra = _goi(ai, lambda: dv.nhan(file_url=url))
	_DA_TAO.append((dv.DT_NGUON, ra[0]["name"]))
	la("không thêm bút toán, phiếu", (frappe.db.count("Journal Entry"), frappe.db.count("Payment Entry")), truoc)


@ca("Codex #450 bench: đọc lại nguồn Cần xử lý: bản mới có hiệu lực, dòng bản cũ còn nguyên ở trạng thái Đã thay")
def _():
	cty, tk, _mau = _nen()
	ngay = nowdate()
	so_cu = int(frappe.generate_hash(length=6), 16) % 9000000 + 1000000
	so_moi = so_cu + 5
	ai = _ke_toan()
	sha = "kt450-doclai-" + frappe.generate_hash(length=16)
	url = _tai(ai, "5-C4E1NPWGG2WZFA-doclai.pdf")
	with patch.object(tep_doc, "doc_tep", lambda ten, byte: _tep(ten, _bao_cao_grab(ngay, so_cu), sha)), \
			patch.object(dv, "_cong_ty", return_value=cty):
		ra = _goi(ai, lambda: dv.nhan(file_url=url))
	_DA_TAO.append((dv.DT_NGUON, ra[0]["name"]))
	ten = ra[0]["name"]
	cu = sorted(frappe.get_all(dv.DT_DONG, filters={"nguon": ten}, pluck="ma_don"))
	khoa_goc = sorted(frappe.get_all(dv.DT_DONG, filters={"nguon": ten}, pluck="khoa"))
	la("bản cũ", cu, sorted(["GF-%s" % so_cu, "GF-%sF" % (so_cu + 1)]))
	# Giả như bộ đọc cũ đọc sai và nguồn đang ở Cần xử lý; bộ đọc đã sửa ra mã khác.
	frappe.db.set_value(dv.DT_NGUON, ten, "trang_thai", "Cần xử lý")
	with patch.object(tep_doc, "doc_tep", lambda ten_, byte: _tep(ten_, _bao_cao_grab(ngay, so_moi), sha)), \
			patch.object(dv, "_cong_ty", return_value=cty):
		ra2 = _goi(ai, lambda: dv.nhan(file_url=url))
	la("đọc lại vào đúng nguồn cũ", ra2[0]["name"], ten)
	moi_ = sorted(frappe.get_all(dv.DT_DONG, filters={"nguon": ten}, pluck="ma_don"))
	la("chỉ còn dòng của bản đọc mới", moi_, sorted(["GF-%s" % so_moi, "GF-%sF" % (so_moi + 1)]))
	la("số dòng khớp số dòng của nguồn", len(moi_), frappe.db.get_value(dv.DT_NGUON, ten, "so_dong"))
	thay = frappe.get_all(dv.DT_DONG, filters={"nguon_cu": ten}, fields=["ma_don", "khoa", "khoa_cu", "trang_thai_khop", "nguon"])
	la("dòng bản cũ vẫn còn, Đã thay, tách khỏi nguồn, giữ khoá gốc",
		(sorted(d.ma_don for d in thay), {d.trang_thai_khop for d in thay}, {d.nguon for d in thay}, sorted(d.khoa_cu for d in thay)),
		(cu, {"Đã thay"}, {None}, khoa_goc))
	dung("khoá của dòng đã thay không chặn khoá bản mới", all(d.khoa.startswith("thay:") for d in thay))
	ls = json.loads(frappe.db.get_value(dv.DT_NGUON, ten, "du_lieu") or "{}").get("lan_doc_truoc") or []
	la("lịch sử số dòng lần đọc trước", (len(ls), ls[0]["so_dong"] if ls else None), (1, 2))


@ca("Codex #450 bench: PDF hỏng tải lên báo lời người dùng, không lộ lỗi thư viện đọc PDF")
def _():
	# Bench bee4853e8: byte giả "%PDF-1.4 ..." làm File.check_content của
	# Frappe (dò mã chạy ngầm trong PDF) nổ lỗi pypdf ngay trong tai_len.
	ai = _ke_toan()
	hong = "data:application/pdf;base64," + base64.b64encode(b"%PDF-1.4 hong " + frappe.generate_hash().encode()).decode()
	loi = ""
	try:
		_goi(ai, lambda: dv.tai_len(ten="hong-kt450.pdf", noi_dung=hong))
	except frappe.ValidationError as e:
		loi = str(e)
	dung("báo tệp hỏng bằng lời người dùng", "tệp bị hỏng" in loi)
	la("không cất tệp nào", frappe.db.count("File", {"file_name": "hong-kt450.pdf"}), 0)


@ca("v579 site: thu ngân không mở được đối soát nhà cung cấp, máy chủ chặn thật")
def _():
	ai = _thu_ngan()
	try:
		_goi(ai, lambda: dv.ds(nhom="Tiền bán"))
		bi_chan = False
	except frappe.PermissionError:
		bi_chan = True
	la("bị chặn", bi_chan, True)


@ca("v579 site: thư vendor xếp việc đọc đính kèm sau khi lưu; thư nội bộ không")
def _():
	goi = []
	with patch.object(frappe, "enqueue", lambda *a, **k: goi.append((a, k))):
		for nguoi in ("Grab <no-reply@grab.com>", "ke-toan@thevagabondpatisserie.com"):
			c = frappe.get_doc({"doctype": "Communication", "communication_type": "Communication",
				"communication_medium": "Email", "sent_or_received": "Received", "sender": nguoi,
				"subject": "KT579 " + frappe.generate_hash(length=6), "content": "kiem"})
			c.insert(ignore_permissions=True)
			_DA_TAO.append((c.doctype, c.name))
	viec = [x for x in goi if x[0] and x[0][0] == "vagabond.doi_soat_vendor.xu_ly_thu"]
	la("đúng một việc, cho thư Grab", len(viec), 1)
	la("xếp sau khi lưu", viec[0][1].get("enqueue_after_commit"), True)


def _nguon_tay(cty, vendor, mau, tien, ngay, gd=""):
	n = frappe.get_doc(dict(doctype=dv.DT_NGUON, company=cty, nhom="Tiền bán", vendor=vendor, mau=mau,
		tai_khoan=vendor.upper(), tu_ngay=ngay, den_ngay=ngay, ngay_tien_ve=ngay, trang_thai="Đã nhận",
		kenh_nhan="Tải tay", ten_tep="kt579-%s.csv" % frappe.generate_hash(length=6),
		sha256="kt579-gd-" + frappe.generate_hash(length=20), so_dong=1, thuc_nhan=tien,
		trang_thai_tien="Chưa đối chiếu", giao_dich_ngan_hang=gd))
	n.insert(ignore_permissions=True)
	_DA_TAO.append((n.doctype, n.name))
	return n


@ca("Codex #446 F2 site: giao dịch đã gắn cho Payoo không bị nguồn Shinhan cùng số tiền lấy lại")
def _():
	cty, _tk, _mau = _nen()
	ngay = nowdate()
	ba = _tai_khoan_cong_ty_moi(_tk_ngan_hang(cty)).name
	tien = 700000 + int(frappe.generate_hash(length=4), 16) % 9000
	g = _gd(ba, tien, "Payoo TT TD KT579 VAGABOND TONG", ngay)
	_nguon_tay(cty, "Payoo", "payoo_the", tien, ngay, gd=g.name)
	sh = _nguon_tay(cty, "Shinhan POS", "shinhan_ngay", tien, ngay)
	dv._tien_ve(sh)
	sh.reload()
	dung("Shinhan không nhận giao dịch của Payoo", g.name not in (sh.giao_dich_ngan_hang or ""))


@ca("Codex #446 F1 site: lưu tay nguồn đối soát bị chặn, cửa máy vẫn ghi được")
def _():
	cty, _tk, _mau = _nen()
	n = _nguon_tay(cty, "Payoo", "payoo_the", 1000, nowdate())
	d = frappe.get_doc(dv.DT_NGUON, n.name)
	d.thuc_nhan = 999999
	try:
		d.save()
		chan = False
	except frappe.ValidationError:
		chan = True
	la("lưu tay bị chặn", chan, True)
	la("số tiền không đổi", int(frappe.db.get_value(dv.DT_NGUON, n.name, "thuc_nhan")), 1000)
