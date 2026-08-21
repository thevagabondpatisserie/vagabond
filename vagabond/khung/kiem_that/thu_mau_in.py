"""Ca kiem tich hop cho bieu mau in Chung tu thanh toan.

Tang khung chi doc duoc ma nguon mau in. Chi tang nay moi tra loi duoc cau
hoi that: BAN IN RA CO CHU KHONG.

Anh Viet 21/08/2026: "xuat PDF ra luc nao cung phai co noi dung giai trinh".
Nen ca kiem o day dung phieu that trong bo nho, goi dung ham render cua
Frappe, roi DOC LAI ban HTML sinh ra de xem o Ma doi tac va bang Noi dung
co chu hay khong.

Khong ghi so, khong gui di dau. Phieu dung xong bi diem luu lui lai het,
xem nen.py.
"""

import re

import frappe

from vagabond.khung.kiem_that.nen import ca, cong_ty, dung, khong_nem, la

MAU = "Vagabond - Chứng từ thanh toán"


def _bo_the(s):
	"""Bo the HTML, gop khoang trang. De doc bang mat khi ca kiem do."""
	s = re.sub(r"<[^>]+>", " ", s or "")
	return " ".join(s.split())


def _o_bang(html):
	"""Cac o Noi dung trong bang chi tiet, da bo the."""
	return [_bo_the(k.split("</td>")[0])
		for k in (html or "").split('<td class="nd">')[1:]]


def _render(pe):
	"""Goi dung duong Frappe dung khi bam nut In."""
	return frappe.get_print(
		"Payment Entry", pe.name, print_format=MAU, doc=pe, no_letterhead=1)


def _phieu_nhap(loai_neo=None, ten_neo=None, tien=1000.0, dien_giai=""):
	"""Dung mot Payment Entry o dang NHAP. Khong ghi so."""
	from vagabond.chung_tu_tien import dat_dien_giai

	cty = cong_ty()
	ncc = frappe.db.get_value("Supplier", {"disabled": 0}, "name")
	if not ncc:
		frappe.throw("Site chưa có nhà cung cấp nào để dựng phiếu thử.")
	tk = frappe.db.get_value(
		"Account", {"company": cty, "account_type": "Bank", "is_group": 0}, "name")
	if not tk:
		frappe.throw("Site chưa có tài khoản ngân hàng nào để dựng phiếu thử.")
	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = "Pay"
	pe.company = cty
	pe.party_type = "Supplier"
	pe.party = ncc
	pe.paid_from = tk
	pe.posting_date = frappe.utils.today()
	pe.reference_date = frappe.utils.today()
	pe.reference_no = "KIEM-THU-MAU-IN"
	pe.paid_amount = tien
	pe.received_amount = tien
	if loai_neo and ten_neo:
		pe.append("references", {
			"reference_doctype": loai_neo,
			"reference_name": ten_neo,
			"allocated_amount": tien,
		})
	dat_dien_giai(pe, dien_giai)
	return pe


@ca("mau in: ban ghi Print Format phai khop tung byte voi tep trong repo")
def _khop_repo():
	# Neu lech thi co nguoi da sua thang tren Desk, va lan Migrate sau se
	# de len. Bat o day de biet ma gop nguoc lai vao repo.
	from vagabond import mau_in

	dung("ban ghi %s ton tai" % MAU, bool(frappe.db.exists("Print Format", MAU)))
	tren_he = frappe.db.get_value("Print Format", MAU, "html") or ""
	trong_repo = mau_in.doc_mau(mau_in.MAU_IN[MAU][0])
	la("mau tren he khop voi repo", tren_he.strip() == trong_repo.strip(), True)


@ca("mau in: phieu tra truoc neo vao DON MUA HANG in ra bang co chu")
def _tra_truoc():
	don = frappe.db.get_value(
		"Purchase Order", {"docstatus": 1}, "name", order_by="creation desc")
	if not don:
		dung("site chua co don mua hang nao da duyet de kiem", False)
		return
	pe = _phieu_nhap("Purchase Order", don, 1000.0,
		"Trả trước 1.000 đ cho đơn mua %s. Ca kiểm thử tích hợp." % don)
	html = khong_nem("render bản in phiếu trả trước", lambda: _render(pe))
	if not html:
		return
	o = _o_bang(html)
	la("bang co dung mot dong", len(o), 1)
	dung("dong do co chu, khong de trong", len(o[0]) > 20 if o else False)
	dung("noi dung nhac toi don mua", don in (o[0] if o else ""))
	dung("nhan cot doi thanh So chung tu", "Số chứng từ" in html)


@ca("mau in: phieu KHONG neo chung tu nao van in ra noi dung giai trinh")
def _hoan_ung():
	# Day la luong hoan ung khong hoa don va hoan tien khach: khong co
	# Purchase Invoice nao de bam vao.
	giai_trinh = ("Hoàn ứng ba khoản mua lặt vặt không có hoá đơn GTGT. "
		"Ca kiểm thử tích hợp.")
	pe = _phieu_nhap(None, None, 1250.0, giai_trinh)
	html = khong_nem("render bản in phiếu hoàn ứng", lambda: _render(pe))
	if not html:
		return
	o = _o_bang(html)
	la("van co dung mot dong", len(o), 1)
	dung("dong do lay dien giai cua phieu",
		"Hoàn ứng ba khoản" in (o[0] if o else ""))


@ca("mau in: o Ma doi tac KHONG ra ten cong ty mot lan nua")
def _ma_doi_tac():
	pe = _phieu_nhap(None, None, 500.0, "Ca kiểm ô Mã đối tác.")
	html = khong_nem("render bản in", lambda: _render(pe))
	if not html:
		return
	ten = frappe.db.get_value("Supplier", pe.party, "supplier_name") or ""
	i = html.find("Vendor code")
	dung("van con o Ma NCC tren ban in", i > -1)
	if i < 0:
		return
	khuc = _bo_the(html[i:i + 500])
	gia_tri = khuc.split("Vendor code:")[-1].strip()[:120]
	dung("o ma co gia tri", len(gia_tri) > 0)
	dung("o ma khong phai ten cong ty (%s)" % gia_tri[:60],
		not gia_tri.startswith(ten[:30]) if ten else True)


@ca("mau in: dien giai cua minh KHONG bi ERPNext ghi de khi luu phieu")
def _dien_giai_song_sot():
	# Chinh la loi anh Viet bao. Luu phieu that xuong co so du lieu roi doc
	# lai o Dien giai: phai con nguyen cau tieng Viet.
	cau = "Trả trước cho đơn mua hàng, ca kiểm thử tích hợp không được xoá."
	pe = _phieu_nhap(None, None, 700.0, cau)
	pe.flags.ignore_permissions = True
	khong_nem("lưu phiếu nháp", lambda: pe.insert(ignore_permissions=True))
	if not pe.get("name"):
		return
	tren_he = frappe.db.get_value("Payment Entry", pe.name, "remarks") or ""
	dung("cau cua minh con nguyen sau khi luu", cau in tren_he)
	dung("khong bi thay bang cau may sinh cua ERPNext",
		"paid to" not in tren_he and "Amount " not in tren_he)


@ca("mau in: LUU LAI LAN HAI van khong mat dien giai")
def _luu_lai_lan_hai():
	# Diem khac biet giua hai cach chua. Phieu tien cua tiem con duoc luu
	# nhieu lan nua sau khi tao: duyet workflow ba cap, dinh kem uy nhiem
	# chi. Cach ghi lai sau insert chi dung lan dau; bat co thi dung mai.
	cau = "Diễn giải phải sống sót qua lần lưu thứ hai."
	pe = _phieu_nhap(None, None, 800.0, cau)
	pe.flags.ignore_permissions = True
	khong_nem("lưu lần một", lambda: pe.insert(ignore_permissions=True))
	if not pe.get("name"):
		return
	pe.reference_no = "KIEM-THU-LUU-LAI"
	khong_nem("lưu lần hai", lambda: pe.save(ignore_permissions=True))
	tren_he = frappe.db.get_value("Payment Entry", pe.name, "remarks") or ""
	dung("cau cua minh van con sau lan luu thu hai", cau in tren_he)
