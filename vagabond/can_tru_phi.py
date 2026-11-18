"""v673 (chị Dung 18/11/2026): cấn trừ hoá đơn phí của đối tác theo đối soát.

Grab, ShopeeFood, Xanh SM, OnePay, Payoo, Shinhan giữ phí lại khi chuyển tiền
bán hàng về, rồi xuất hoá đơn phí. Hoá đơn phí lên Công nợ phải trả và treo
331 dù tiệm không chuyển đồng nào. Đối soát theo đơn đã biết phí của từng đơn,
nên máy lập sẵn phiếu cấn trừ (Vagabond Can Tru San, luồng #262 đã có):

    Nợ 331 nhà cung cấp phí (đúng hoá đơn phí)
    Có 131 khách công nợ của đối tác (đúng hoá đơn bán còn dư)      hoặc
    Có tài khoản chờ tiền về của hình thức thanh toán (hoá đơn đã thu qua
       hình thức đó, hay phí kỳ như quảng cáo không gắn hoá đơn)

Không lập luồng bút toán song song: phiếu đi qua kiểm, duyệt và ghi sổ của
Vagabond Can Tru San. Kế toán lập phiếu (đã kiểm phí bị giữ), kế toán trưởng
xác nhận mới ghi sổ. Máy không đoán khi không biết phí nằm ở tài khoản nào:
báo rõ phần chưa đặt được và không cho lập.
"""
import calendar
import datetime
import re
from decimal import Decimal

# ------------------------------------------------------------ phần thuần

# khoá -> (tên hiện, vendor trên nguồn đối soát, nhãn trên phiếu, hình thức thanh toán của đối tác)
DOI_TAC = {
	"grab": ("GrabFood", "GrabFood", "GrabFood", "GrabFood"),
	"shopee": ("ShopeeFood", "ShopeeFood", "ShopeeFood", "ShopeeFood"),
	"greensm": ("Xanh SM Ngon", "Xanh SM Ngon", "GreenSM Food", "GreenSM Food"),
	"onepay": ("OnePay", "OnePay", "OnePay", "OnePay"),
	"payoo": ("Thẻ Payoo", "Payoo", "Payoo", "Thẻ - Payoo"),
	"shinhan": ("Thẻ Shinhan POS", "Shinhan POS", "Shinhan POS", "Thẻ - ShinhanBank"),
}
THU_TU = ("grab", "shopee", "greensm", "onepay", "payoo", "shinhan")
# Loại phí: theo đơn (hoa hồng sàn, phí thẻ) đi với dòng bán/hoàn; phí kỳ
# (quảng cáo Grab) là dòng không gắn đơn của báo cáo.
LOAI = {"don": ("Phí theo đơn", ("ban", "hoan")), "ky": ("Phí kỳ, quảng cáo", ("phi_ky",))}
_TU_KHOA = (("grab", r"grab"), ("shopee", r"shopee"), ("greensm", r"xanh ?sm|green ?sm|gsm"),
	("onepay", r"onepay"), ("payoo", r"payoo"), ("shinhan", r"shinhan"))


def khong_dau(s):
	import unicodedata
	s = unicodedata.normalize("NFD", str(s or "")).replace("đ", "d").replace("Đ", "D")
	return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def doan_doi_tac(*chu):
	"""THUẦN. Đối tác theo tên nhà cung cấp và nội dung hoá đơn; None khi không rõ."""
	s = khong_dau(" ".join(str(x or "") for x in chu))
	for k, m in _TU_KHOA:
		if re.search(m, s):
			return k
	return None


def doan_loai(noi_dung):
	"""THUẦN. Hoá đơn ghi quảng cáo là phí kỳ, còn lại là phí theo đơn."""
	return "ky" if re.search(r"quang cao|marketing|\bads\b", khong_dau(noi_dung)) else "don"


def _thang(y, m):
	return "%04d-%02d-01" % (y, m), "%04d-%02d-%02d" % (y, m, calendar.monthrange(y, m)[1])


def _iso(d, m, y):
	try:
		return datetime.date(int(y), int(m), int(d)).isoformat()
	except ValueError:
		return None


def doan_ky(noi_dung, ngay_hd):
	"""THUẦN. Kỳ phí: "từ ngày 01/10/2026 đến ngày 31/10/2026" (OnePay), "tháng
	10/2026" (Grab quảng cáo); không ghi thì tháng trước tháng của hoá đơn (phí
	hoa hồng xuất đầu tháng sau). Trả (từ, đến, cách đoán)."""
	s = khong_dau(noi_dung)
	m = re.search(r"tu ngay (\d{1,2})[/.-](\d{1,2})[/.-](\d{4}) den ngay (\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", s)
	if m:
		tu, den = _iso(*m.group(1, 2, 3)), _iso(*m.group(4, 5, 6))
		if tu and den and tu <= den:
			return tu, den, "ghi trên hoá đơn"
	m = re.search(r"thang (\d{1,2})[/.-](\d{4})", s)
	if m and 1 <= int(m.group(1)) <= 12:
		return _thang(int(m.group(2)), int(m.group(1))) + ("ghi trên hoá đơn",)
	d = datetime.date.fromisoformat(str(ngay_hd)[:10])
	y, mo = (d.year, d.month - 1) if d.month > 1 else (d.year - 1, 12)
	return _thang(y, mo) + ("tháng trước ngày hoá đơn",)


def cac_thang(ngay_hd, so=4):
	"""THUẦN. Chip kỳ: tháng của hoá đơn và các tháng trước đó."""
	d = datetime.date.fromisoformat(str(ngay_hd)[:10])
	y, m, ra = d.year, d.month, []
	for _i in range(so):
		tu, den = _thang(y, m)
		ra.append(dict(tu=tu, den=den, ten="Tháng %02d/%04d" % (m, y)))
		y, m = (y, m - 1) if m > 1 else (y - 1, 12)
	return ra


def _so(x):
	return int(Decimal(str(x or 0)).quantize(Decimal("1")))


def phan_bo(phi_si, phi_khong_si, can_bu, tk_doi_tac):
	"""THUẦN. Đặt can_bu đồng phí vào đúng chỗ đang giữ tiền của đối tác.

	phi_si: [dict(si, phi, du, tk)] theo thứ tự ngày; phi là phí ròng của hoá
	đơn (đã trừ hoàn phí), du là phần hoá đơn còn nợ ở 131, tk là tài khoản chờ
	tiền về của hình thức thanh toán đã thu hoá đơn (None nếu không dùng được).
	phi_khong_si: [phí] của dòng không gắn hoá đơn (quảng cáo, đơn chưa có hoá đơn).
	tk_doi_tac: tài khoản chờ tiền về của đối tác (None nếu chưa khai).

	Luật: phí của hoá đơn trừ vào chính hoá đơn trước (131 còn dư); phần còn
	lại của hoá đơn đã thu qua hình thức thanh toán đi vào tài khoản của hình
	thức đó. Phí không gắn hoá đơn (và phần còn lại không có tài khoản) trừ vào
	hoá đơn khác của kỳ còn dư 131, rồi mới vào tài khoản chờ của đối tác. Đặt
	đủ can_bu thì dừng. Phần không đặt được trả ở "thieu", không đoán.
	"""
	con = _so(can_bu)
	ban, tk = {}, {}
	du = {x["si"]: max(0, _so(x.get("du"))) for x in phi_si}

	def dat_si(si, a):
		nonlocal con
		a = min(a, du[si], con)
		if a > 0:
			ban[si] = ban.get(si, 0) + a
			du[si] -= a
			con -= a
		return a

	def dat_tk(t, a, ghi):
		nonlocal con
		a = min(a, con)
		if a > 0:
			cu = tk.get(t) or dict(so=0, ghi=ghi)
			cu["so"] += a
			tk[t] = cu
			con -= a
		return a

	cho = []
	for x in phi_si:
		f = _so(x["phi"])
		if f <= 0:
			continue
		r = f - dat_si(x["si"], f)
		if r > 0:
			cho.append((r, x.get("tk"), x["si"]))
	for f in phi_khong_si:
		if _so(f) > 0:
			cho.append((_so(f), None, None))
	for r, t, si in cho:
		if con <= 0:
			break
		if t:
			r -= dat_tk(t, r, "Phí hoá đơn đã thu qua hình thức thanh toán")
		else:
			for x in phi_si:
				if r <= 0 or con <= 0:
					break
				r -= dat_si(x["si"], r)
			if r > 0 and tk_doi_tac:
				r -= dat_tk(tk_doi_tac, r, "Phí không gắn hoá đơn còn dư")
	# Phần chưa đặt được là đúng phần còn thiếu để đủ số được bù.
	return dict(ban=[dict(si=k, so_tien=v) for k, v in ban.items()],
		tk=[dict(tai_khoan=k, so_tien=v["so"], ghi_chu=v["ghi"]) for k, v in tk.items()],
		da_dat=_so(can_bu) - con, thieu=con)


def can_bu(con_no_hd, tong_doi_soat, da_bu_truoc):
	"""THUẦN. Số được bù: không quá dư hoá đơn phí, không quá phần phí đối tác
	đã giữ (theo đối soát) chưa bù cho hoá đơn khác cùng kỳ."""
	return max(0, min(_so(con_no_hd), _so(tong_doi_soat) - _so(da_bu_truoc)))


def gop_phi(dong):
	"""THUẦN. Phí ròng theo hoá đơn bán (giữ thứ tự xuất hiện) và phí không gắn
	hoá đơn. dong: [dict(sales_invoice, phi)]."""
	theo_si, khong = {}, []
	for d in dong:
		if d.get("sales_invoice"):
			theo_si[d["sales_invoice"]] = theo_si.get(d["sales_invoice"], 0) + _so(d.get("phi"))
		else:
			khong.append(_so(d.get("phi")))
	return theo_si, khong


def bang_ke_csv(dong):
	"""THUẦN. Bảng kê căn cứ đính vào phiếu: mỗi dòng đối soát một hàng."""
	import csv
	import io
	o = io.StringIO()
	w = csv.writer(o)
	w.writerow(["Nguồn đối soát", "Ngày", "Loại", "Mã đơn", "Hoá đơn bán", "Phí"])
	for d in dong:
		w.writerow([d.get("nguon"), str(d.get("ngay") or "")[:10], d.get("loai"), d.get("ma_don") or "",
			d.get("sales_invoice") or "", _so(d.get("phi"))])
	return "﻿" + o.getvalue()


# ------------------------------------------------------------ phần chạm hệ

import frappe  # noqa: E402

DT = "Vagabond Can Tru San"
DT_NGUON = "Vagabond Doi Soat Nguon"
DT_DONG = "Vagabond Doi Soat Dong"
VAI_LAP = {"Accounts User", "Accounts Manager", "System Manager"}


def _chan_lap():
	if not set(frappe.get_roles()) & VAI_LAP:
		frappe.throw("Chỉ Kế toán lập được phiếu cấn trừ phí đối tác.", frappe.PermissionError)


def _hoa_don(hoa_don, khoa=False):
	if khoa:
		frappe.db.sql("select name from `tabPurchase Invoice` where name=%s for update", (hoa_don,))
	hd = frappe.get_doc("Purchase Invoice", hoa_don)
	if hd.docstatus != 1 or hd.get("is_return"):
		frappe.throw("Hoá đơn %s chưa ghi sổ hoặc là hoá đơn trả lại; chỉ cấn trừ hoá đơn phí đã ghi sổ." % hoa_don)
	if hd.currency != "VND":
		frappe.throw("Hoá đơn %s không phải tiền VND." % hoa_don)
	return hd


def _noi_dung(hd):
	return " ".join([hd.get("remarks") or ""] + [(x.get("item_name") or "") + " " + (x.get("description") or "")
		for x in (hd.get("items") or [])])


def _tk_cho(cong_ty, pt):
	"""Tài khoản chờ tiền về của một hình thức thanh toán, chỉ khi dùng được làm
	vế Có không đối tượng: không phải ngân hàng, tiền mặt, phải thu, phải trả."""
	from vagabond import thu_tien

	tk = thu_tien.tk_tien_thu(cong_ty, pt)[0] if pt else None
	if not tk:
		return None
	a = frappe.db.get_value("Account", tk, ["account_type", "is_group", "disabled", "company", "account_currency"],
		as_dict=True) or {}
	if a.get("is_group") or a.get("disabled") or a.get("company") != cong_ty or (a.get("account_currency") or "VND") != "VND":
		return None
	if a.get("account_type") in ("Bank", "Cash", "Receivable", "Payable"):
		return None
	return tk


def _dong(cong_ty, doi_tac, loai, tu, den):
	"""Dòng đối soát hiệu lực của đối tác trong kỳ: nguồn Tiền bán đã nhận, giám
	đốc không từ chối, dòng chưa bị bản sửa thay. Đọc đủ, không phân trang."""
	return frappe.db.sql("""select d.name, d.nguon, d.ngay, d.loai, d.ma_don, d.phi, d.sales_invoice,
			n.xac_nhan_luc
		from `tabVagabond Doi Soat Dong` d join `tabVagabond Doi Soat Nguon` n on n.name = d.nguon
		where n.company = %(ct)s and n.vendor = %(v)s and n.nhom = 'Tiền bán' and n.trang_thai = 'Đã nhận'
		  and ifnull(n.duong_vao, '') != 'Từ chối' and ifnull(d.thay_bang, '') = ''
		  and d.loai in %(loai)s and d.ngay between %(tu)s and %(den)s
		order by d.ngay, d.name""",
		dict(ct=cong_ty, v=DOI_TAC[doi_tac][1], loai=tuple(LOAI[loai][1]), tu=tu, den=den), as_dict=True)


def _da_bu_truoc(cong_ty, doi_tac, loai, tu, den, tru=None):
	"""Phí của cùng đối tác, loại, kỳ (chồng lấn) đã đưa vào phiếu cấn trừ khác còn hiệu lực."""
	f = dict(company=cong_ty, doi_soat=1, san=DOI_TAC[doi_tac][2], loai_phi=LOAI[loai][0], docstatus=["<", 2],
		tu_ngay=["<=", den], den_ngay=[">=", tu])
	if tru:
		f["name"] = ["!=", tru]
	return sum(_so(x.tong_bu) for x in frappe.get_all(DT, filters=f, fields=["tong_bu"], limit_page_length=0))


def _hoa_don_ban(cong_ty, ten):
	"""Dư 131 và tài khoản chờ tiền về của từng hoá đơn bán (đọc đủ theo lô)."""
	ra = {}
	ten = list(ten)
	for i in range(0, len(ten), 500):
		for r in frappe.get_all("Sales Invoice", filters={"name": ["in", ten[i:i + 500]]}, fields=["name", "company",
				"docstatus", "outstanding_amount", "debit_to", "vgb_pt_thanh_toan", "posting_date", "customer"],
				limit_page_length=0):
			ra[r.name] = r
	tk_pt, loai_tk = {}, {}
	for r in ra.values():
		if r.debit_to not in loai_tk:
			loai_tk[r.debit_to] = frappe.db.get_value("Account", r.debit_to, "account_type")
		pt = r.get("vgb_pt_thanh_toan") or ""
		if pt not in tk_pt:
			tk_pt[pt] = _tk_cho(cong_ty, pt)
		ok = r.company == cong_ty and r.docstatus == 1
		r.du = _so(r.outstanding_amount) if ok and loai_tk[r.debit_to] == "Receivable" else 0
		r.tk = tk_pt[pt] if ok else None
		r.hop_le = ok
	return ra


def _tinh(hd, doi_tac, loai, tu, den, tru=None):
	cong_ty = hd.company
	dong = _dong(cong_ty, doi_tac, loai, tu, den)
	theo_si, khong = gop_phi(dong)
	tong = sum(theo_si.values()) + sum(khong)
	da_bu = _da_bu_truoc(cong_ty, doi_tac, loai, tu, den, tru)
	cb = can_bu(hd.outstanding_amount, tong, da_bu)
	si = _hoa_don_ban(cong_ty, theo_si)
	# Hoá đơn bán đã huỷ, khác pháp nhân: phí của nó coi như không gắn hoá đơn.
	phi_si = []
	for k, v in theo_si.items():
		r = si.get(k)
		if r and r.hop_le:
			phi_si.append(dict(si=k, phi=v, du=r.du, tk=r.tk, ngay=str(r.posting_date)))
		else:
			khong.append(v)
	phi_si.sort(key=lambda x: (x["ngay"], x["si"]))
	tk_dt = _tk_cho(cong_ty, DOI_TAC[doi_tac][3])
	pb = phan_bo(phi_si, khong, cb, tk_dt)
	nguon = {d.nguon: d.xac_nhan_luc for d in dong}
	return dict(dong=dong, tong=tong, da_bu=da_bu, can_bu=cb, pb=pb, tk_doi_tac=tk_dt, si=si,
		so_nguon=len(nguon), chua_xn=sum(1 for v in nguon.values() if not v))


def _chan_cty(cong_ty):
	from vagabond import doi_soat_vendor as dsv

	dsv._chan_cong_ty(cong_ty)


def _nhan_tk(tk):
	from vagabond.cong_no_ncc import _nhan_tk as n

	return n(tk)


def _phieu_cua(hoa_don):
	ten = frappe.get_all("Vagabond Can Tru Phi", filters={"hoa_don": hoa_don, "parenttype": DT}, pluck="parent")
	if not ten:
		return []
	return [dict(name=x.name, docstatus=x.docstatus, trang_thai=x.trang_thai or "", ly_do=x.ly_do or "",
		tong_bu=float(x.tong_bu or 0), but_toan=x.but_toan or "", tu=str(x.tu_ngay), den=str(x.den_ngay),
		doi_soat=x.doi_soat)
		for x in frappe.get_all(DT, filters={"name": ["in", list(set(ten))]}, fields=["name", "docstatus",
			"trang_thai", "ly_do", "tong_bu", "but_toan", "tu_ngay", "den_ngay", "doi_soat"], order_by="creation desc")]


def _doc_chon(hd, doi_tac, loai, tu, den):
	nd = _noi_dung(hd)
	tu_d, den_d, doan = doan_ky(nd, hd.get("bill_date") or hd.posting_date)
	doi_tac = doi_tac if doi_tac in DOI_TAC else (_doi_tac_cu(hd.supplier) or doan_doi_tac(hd.supplier_name, nd))
	loai = loai if loai in LOAI else doan_loai(nd)
	if tu and den:
		tu, den = str(frappe.utils.getdate(tu)), str(frappe.utils.getdate(den))
		doan = "kế toán chọn"
	else:
		tu, den = tu_d, den_d
	if tu > den:
		frappe.throw("Kỳ đối soát không hợp lệ: từ ngày sau đến ngày.")
	return doi_tac, loai, tu, den, doan, (tu_d, den_d)


def _doi_tac_cu(ncc):
	"""Nhớ lựa chọn: phiếu cấn trừ gần nhất của cùng nhà cung cấp."""
	x = frappe.get_all(DT, filters={"nha_cung_cap": ncc, "doi_soat": 1, "docstatus": ["<", 2]}, fields=["san"],
		order_by="creation desc", limit_page_length=1)
	if not x:
		return None
	return next((k for k, v in DOI_TAC.items() if v[2] == x[0].san), None)


@frappe.whitelist()
def de_xuat(hoa_don=None, doi_tac=None, loai=None, tu=None, den=None):
	"""Đề xuất cấn trừ một hoá đơn phí theo đối soát (chỉ đọc)."""
	_chan_lap()
	hd = _hoa_don(hoa_don)
	_chan_cty(hd.company)
	doi_tac, loai, tu, den, doan, ky_hd = _doc_chon(hd, doi_tac, loai, tu, den)
	ra = dict(hoa_don=dict(name=hd.name, bill_no=hd.get("bill_no") or "", ten_ncc=hd.supplier_name,
			con_no=float(hd.outstanding_amount or 0), ngay=str(hd.get("bill_date") or hd.posting_date),
			noi_dung=_noi_dung(hd).strip()[:200]),
		doi_tac=doi_tac, doi_tac_ds=[dict(k=k, ten=DOI_TAC[k][0]) for k in THU_TU],
		loai=loai, loai_ds=[dict(k=k, ten=v[0]) for k, v in LOAI.items()],
		ky=dict(tu=tu, den=den, doan=doan), ky_ds=[dict(tu=ky_hd[0], den=ky_hd[1], ten="Kỳ trên hoá đơn")]
			+ cac_thang(hd.get("bill_date") or hd.posting_date),
		phieu=_phieu_cua(hd.name), quyen=dict(xac_nhan=bool(set(frappe.get_roles()) & {"Accounts Manager", "System Manager"})))
	if not doi_tac:
		ra.update(lap_duoc=False, ly_do="Chưa nhận ra đối tác của hoá đơn này. Chọn đối tác ở hàng chip.")
		return ra
	t = _tinh(hd, doi_tac, loai, tu, den)
	pb = t["pb"]
	ly_do = ""
	if not t["dong"]:
		ly_do = "Chưa có dòng đối soát %s nào của %s trong kỳ. Kiểm kỳ, loại phí, hoặc nhận đủ báo cáo đối tác trước." % (
			LOAI[loai][0].lower(), DOI_TAC[doi_tac][0])
	elif t["can_bu"] <= 0:
		ly_do = "Không còn phí nào để bù: hoá đơn hết dư hoặc phí của kỳ đã bù cho hoá đơn khác."
	elif pb["thieu"] > 0:
		ly_do = ("Còn %s đ phí chưa biết đang nằm ở đâu: hoá đơn bán đã hết dư và hình thức %s chưa khai tài khoản chờ "
			"tiền về (không phải ngân hàng, tiền mặt). Quản trị khai tài khoản cho hình thức thanh toán, hoặc kế toán "
			"hạch toán tay phần này.") % ("{:,}".format(pb["thieu"]).replace(",", "."), DOI_TAC[doi_tac][3])
	si = t["si"]
	dk = [dict(ve="Nợ", tk=_nhan_tk(hd.credit_to), doi=hd.supplier_name, so=t["can_bu"])]
	co131 = {}
	for b in pb["ban"]:
		r = si[b["si"]]
		k = (r.debit_to, r.customer)
		co131[k] = co131.get(k, 0) + b["so_tien"]
	dk += [dict(ve="Có", tk=_nhan_tk(k[0]), doi=k[1], so=v) for k, v in co131.items()]
	dk += [dict(ve="Có", tk=_nhan_tk(x["tai_khoan"]), doi="", so=x["so_tien"]) for x in pb["tk"]]
	ra.update(lap_duoc=not ly_do, ly_do=ly_do, tong_doi_soat=t["tong"], da_bu_truoc=t["da_bu"], can_bu=t["can_bu"],
		lech=float(hd.outstanding_amount or 0) - t["can_bu"], so_nguon=t["so_nguon"], nguon_chua_xn=t["chua_xn"],
		so_dong=len(t["dong"]), so_hd_ban=len(pb["ban"]), dinh_khoan=dk if not ly_do else [])
	return ra


@frappe.whitelist()
def lap(hoa_don=None, doi_tac=None, loai=None, tu=None, den=None):
	"""Kế toán lập phiếu cấn trừ (nháp, đã kiểm phí bị giữ) cho kế toán trưởng
	xác nhận. Khoá hoá đơn phí rồi mới tính, để hai lần bấm không lập hai phiếu
	trên cùng phần dư. Có phiếu nháp cùng hoá đơn thì cập nhật phiếu đó."""
	_chan_lap()
	hd = _hoa_don(hoa_don, khoa=True)
	_chan_cty(hd.company)
	doi_tac, loai, tu, den, _d, _k = _doc_chon(hd, doi_tac, loai, tu, den)
	if not doi_tac:
		frappe.throw("Chọn đối tác của hoá đơn phí.")
	hom_nay = frappe.utils.nowdate()
	if den > hom_nay:
		frappe.throw("Kỳ %s đến %s chưa hết; lập phiếu khi đã nhận đủ đối soát của kỳ." % (tu, den))
	nhap = [x for x in _phieu_cua(hd.name) if x["docstatus"] == 0 and x["doi_soat"]]
	cu = nhap[0]["name"] if nhap else None
	t = _tinh(hd, doi_tac, loai, tu, den, tru=cu)
	pb = t["pb"]
	if not t["dong"] or t["can_bu"] <= 0 or pb["thieu"] > 0 or not (pb["ban"] or pb["tk"]):
		frappe.throw("Chưa lập được: mở lại đề xuất để xem lý do.")
	d = frappe.get_doc(DT, cu) if cu else frappe.new_doc(DT)
	d.update(dict(company=hd.company, san=DOI_TAC[doi_tac][2], doi_soat=1, loai_phi=LOAI[loai][0], diem_ban="",
		khach_hang=None, nha_cung_cap=hd.supplier, tu_ngay=tu, den_ngay=den, ngay_bu=max(hom_nay, str(hd.posting_date)),
		tham_chieu="DS %s %s %s-%s %s" % (DOI_TAC[doi_tac][0], loai, tu, den, hd.name), xac_nhan=1))
	d.set("phi", [dict(hoa_don=hd.name, so_tien=t["can_bu"])])
	d.set("ban", [dict(hoa_don=x["si"], so_tien=x["so_tien"]) for x in pb["ban"]])
	d.set("tk", [dict(tai_khoan=x["tai_khoan"], so_tien=x["so_tien"], ghi_chu=x["ghi_chu"]) for x in pb["tk"]])
	f = frappe.get_doc(dict(doctype="File", file_name="bang-ke-phi-%s-%s.csv" % (doi_tac, hd.name), is_private=1,
		content=bang_ke_csv(t["dong"]))).insert(ignore_permissions=True)
	d.can_cu = f.file_url
	d.save() if cu else d.insert()
	frappe.db.set_value("File", f.name, {"attached_to_doctype": DT, "attached_to_name": d.name}, update_modified=False)
	return dict(name=d.name, tong_bu=float(d.tong_bu or 0))


@frappe.whitelist()
def xac_nhan(ten=None):
	"""Kế toán trưởng xác nhận phiếu nháp: máy kiểm lại toàn bộ rồi ghi sổ bút
	toán cấn trừ (hoặc giữ Chờ đối soát khi hoá đơn bán chưa đủ điều kiện)."""
	from vagabond import can_tru_san as ct

	ct.kiem_quyen_duyet()
	d = frappe.get_doc(DT, ten)
	_chan_cty(d.company)
	if d.docstatus != 0 or not d.doi_soat:
		frappe.throw("Phiếu %s không còn là phiếu nháp lập từ đối soát. Tải lại màn hình." % ten)
	d.xac_nhan = 1
	d.submit()
	d = frappe.get_doc(DT, ten)
	return dict(name=d.name, trang_thai=d.trang_thai or "", ly_do=d.ly_do or "", but_toan=d.but_toan or "")


def kiem_phieu_doi_soat(d):
	"""Kiểm phiếu lập từ đối soát ở MỌI đường ghi (app, Desk, nhập): đúng một
	hoá đơn phí, hoá đơn bán thuộc đúng đối soát của đối tác trong kỳ, tài khoản
	là tài khoản chờ tiền về của đối tác hay của hình thức đã thu hoá đơn, tổng
	không vượt phần phí đối tác đã giữ chưa bù cho phiếu khác."""
	doi_tac = next((k for k, v in DOI_TAC.items() if v[2] == d.san), None)
	loai = next((k for k, v in LOAI.items() if v[0] == d.loai_phi), None)
	if not doi_tac or not loai:
		frappe.throw("Phiếu từ đối soát phải có đối tác thanh toán và loại phí hợp lệ.")
	if len(d.phi or []) != 1:
		frappe.throw("Phiếu từ đối soát cấn trừ đúng một hoá đơn phí.")
	tu, den = str(frappe.utils.getdate(d.tu_ngay)), str(frappe.utils.getdate(d.den_ngay))
	dong = _dong(d.company, doi_tac, loai, tu, den)
	theo_si, khong = gop_phi(dong)
	tong = sum(theo_si.values()) + sum(khong)
	si = _hoa_don_ban(d.company, theo_si)
	duoc_tk = {x for x in [_tk_cho(d.company, DOI_TAC[doi_tac][3])] + [r.tk for r in si.values()] if x}
	for x in d.ban or []:
		if x.hoa_don not in theo_si:
			frappe.throw("Hoá đơn bán %s không có trong đối soát %s của kỳ." % (x.hoa_don, DOI_TAC[doi_tac][0]))
	for x in d.get("tk") or []:
		if x.tai_khoan not in duoc_tk:
			frappe.throw("Tài khoản %s không phải tài khoản chờ tiền về của %s. Lập lại phiếu từ màn Công nợ phải trả." % (
				x.tai_khoan, DOI_TAC[doi_tac][0]))
	con = tong - _da_bu_truoc(d.company, doi_tac, loai, tu, den, tru=d.name if not d.is_new() else None)
	if _so(d.tong_bu) > con:
		frappe.throw("Phiếu bù %s đ, vượt phần phí đối tác đã giữ còn chưa bù (%s đ) theo đối soát." % (
			_so(d.tong_bu), con))
	d.tong_doi_soat = tong
