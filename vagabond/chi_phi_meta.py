# -*- coding: utf-8 -*-
"""v674: chi phí quảng cáo Meta vào sổ theo ĐÚNG số trừ thẻ Shinhan, một bút toán
nháp mỗi tháng, kế toán kiểm rồi ghi sổ.

Quyết định đã chốt (anh Việt và chị Dung, 18/11/2026; prompt anh dán mục 1 và 4)
--------------------------------------------------------------------
- Số tiền THỰC TRỪ THẺ lấy từ sao kê thẻ tín dụng Shinhan đứng tên công ty, qua
  luồng đối soát đang có (hộp thư doisoat@ và tải tay có duyệt). Không coi số
  Meta báo đã tiêu là số đã thanh toán; ba con số Đã tiêu trên Meta, Đã trừ trên
  thẻ, Đã ghi sổ hiện riêng, lệch không tự là sai.
- Mỗi tháng một Journal Entry NHÁP: Nợ 6417 / Có 3411 cho chi quảng cáo; phí thẻ
  đi kèm dòng FACEBK vào Nợ 6427 / Có 3411 cùng bút toán. Lãi thẻ, phí thường
  niên không thuộc luồng này. Không tách VAT, không làm hoá đơn mua.
- Kỳ theo NGÀY GIAO DỊCH trong tháng dương lịch, không theo kỳ sao kê. Chỉ lập
  khi sao kê của ngân hàng đã phủ đủ các ngày có thể ghi nợ giao dịch của tháng;
  thiếu thì báo "Chưa đủ sao kê", không lập số thiếu.
- Trả dư nợ thẻ (Nợ 3411 / Có 112) là việc kế toán, máy không làm.

Loại trùng (mục 4)
--------------------------------------------------------------------
Mỗi giao dịch thẻ thường có ở HAI bản: PDF ngân hàng và bảng gõ tay. Trên site
18/11/2026 có 42 dòng FACEBK cho khoảng 21 giao dịch. Căn cước giao dịch là
(4 số cuối thẻ, ngày giao dịch, ngày bút toán, đơn vị chấp nhận thẻ, số tiền) lấy
từ ma_su_kien của doi_soat_mau; mã băm tệp khác nhau không làm ra giao dịch mới.
- Cùng căn cước ở hai bản: một giao dịch, giữ cả hai bằng chứng.
- Cùng căn cước lặp lại TRONG một bản: hai giao dịch thật (ngân hàng in hai dòng).
- Hai bản đếm lệch nhau (bản này 2 dòng, bản kia 1): máy không tự quyết, kế toán
  chọn số giao dịch thật.
- Cùng thẻ, ngày, số tiền mà chữ đơn vị chấp nhận thẻ khác nhau giữa hai bản (gõ
  tay sai chữ): nghi trùng, kế toán chọn "một giao dịch" hay "hai giao dịch".
Chưa quyết xong thì không lập bút toán.

Đường thủ công (anh Việt 18/11/2026)
--------------------------------------------------------------------
Kế toán chọn tay từng phí chưa xác định có vào bút toán không; sửa bút toán nháp
ở Hạch toán tay hay Desk (máy thấy đã sửa tay thì không ghi đè); hoặc tự lập bút
toán Meta bằng tay. Chứng từ Meta có sẵn bằng đường khác trong tháng (hoá đơn mua
nhà cung cấp Meta, bút toán tay ghi 6417 có chữ FACEBK, Meta, Facebook) thì máy
dừng lại cho kế toán xem: không sửa chứng từ đó, không ghi chi phí hai lần.
"""

import json
import re
from datetime import timedelta

from vagabond import but_toan_nhap as BN

TK_QC = "6417"
TK_PHI = "6427"
TK_THE = "3411"
NGAY_TRE = 10
MAU_PDF = "the_shinhan"
MAU_BANG = "the_shinhan_bang"
MAU_META = (re.compile(r"^\s*FACEBK\b", re.I), re.compile(r"^\s*FACEBOOK\b", re.I), re.compile(r"^\s*META\s+(PLATFORMS|ADS)\b", re.I))
MAU_PHI_NGOAI = re.compile(r"FOREIGN|NGOAI\s*TE|NGOẠI\s*TỆ|CONVERSION|CROSS\s*BORDER|\bFX\b|TRANSACTION\s*FEE|PHI\s*GIAO\s*DICH|PHÍ\s*GIAO\s*DỊCH", re.I)
MAU_KHONG = re.compile(r"ANNUAL|THUONG\s*NIEN|THƯỜNG\s*NIÊN|INTEREST|\bLAI\b|\bLÃI\b|LATE|CHAM\s*TRA|CHẬM\s*TRẢ", re.I)

# Trạng thái từng giao dịch trên màn đối soát
GD_VAO = "Vào bút toán"
GD_DA_GHI = "Đã ghi sổ"
GD_CT_KHAC = "Đã có chứng từ khác"
GD_CHO = "Chờ kế toán chọn"
GD_BO = "Kế toán bỏ"
GD_KHONG = "Không thuộc Meta"

# Trạng thái tháng (chip màn đối soát, prompt mục 4)
TH_KHOP = "Khớp"
TH_LECH = "Lệch"
TH_CHUA_SK = "Chưa có sao kê"
TH_CHUA_DU = "Chưa đủ chứng từ"
CAC_TH = (TH_KHOP, TH_LECH, TH_CHUA_SK, TH_CHUA_DU)


# ------------------------------------------------------------- phần thuần


def la_meta(dv):
	return any(m.search(str(dv or "")) for m in MAU_META)


def tach_su_kien(ma_su_kien):
	"""ma_su_kien của sao kê thẻ "the4:ngày GD:ngày bút toán:đơn vị:tiền:thứ tự".
	THUẦN. Đơn vị chấp nhận thẻ có thể chứa dấu hai chấm nên ghép phần giữa."""
	p = str(ma_su_kien or "").split(":")
	if len(p) < 6:
		return None
	try:
		n = int(p[-1])
		tien = int(p[-2])
	except ValueError:
		return None
	return {"the4": p[0], "ngay_gd": p[1], "ngay_bt": p[2], "dv": ":".join(p[3:-2]), "tien": tien, "n": n}


def chuan_dv(dv):
	return re.sub(r"\s+", " ", str(dv or "")).strip().upper()


def phan_loai(loai, dv):
	"""Một dòng sao kê thẻ thuộc luồng Meta thế nào. THUẦN.

	"meta": chi quảng cáo (hoặc hoàn tiền) FACEBK; "phi_meta": phí ghi rõ FACEBK;
	"phi_chua_ro": phí ngoại tệ, phí giao dịch không ghi rõ của giao dịch nào, để
	kế toán chọn; "khong": phần còn lại (lãi, phí thường niên, chi khác)."""
	loai = str(loai or "")
	if loai in ("phat_sinh", "hoan"):
		return "meta" if la_meta(dv) else "khong"
	if loai == "phi":
		if MAU_KHONG.search(str(dv or "")):
			return "khong"
		if la_meta(dv):
			return "phi_meta"
		if MAU_PHI_NGOAI.search(str(dv or "")):
			return "phi_chua_ro"
	return "khong"


def gop_giao_dich(dong, quyet_dinh=None):
	"""Gộp dòng sao kê của nhiều bản thành giao dịch, theo luật loại trùng. THUẦN.

	dong: [{name, nguon, the4, ngay_gd, ngay_bt, dv, tien, n, phan_loai, purchase_invoice}].
	Trả list giao dịch {khoa, the4, ngay_gd, ngay_bt, dv, tien, phan_loai, bang_chung:[name],
	can_quyet: None | {"loai", "khoa_quyet", "mo"}, purchase_invoice}."""
	qd = quyet_dinh or {}
	nhom = {}
	for d in dong:
		goc = (d["the4"], d["ngay_gd"], d["ngay_bt"], chuan_dv(d["dv"]), int(d["tien"]))
		g = nhom.setdefault(goc, {"theo_ban": {}, "dong": [], "mau": d})
		g["theo_ban"].setdefault(d["nguon"], []).append(d)
		g["dong"].append(d)
	ra = []
	for goc, g in sorted(nhom.items()):
		dem = sorted(len(v) for v in g["theo_ban"].values())
		it, nhieu = dem[0], dem[-1]
		khoa_goc = "%s:%s:%s:%s:%s" % goc
		so = nhieu
		cho = None
		if len(dem) > 1 and it != nhieu:
			k = "dem:" + khoa_goc
			if k in qd:
				so = max(it, min(nhieu, int(qd[k].get("gia_tri") or it)))
			else:
				cho = {"loai": "dem", "khoa_quyet": k, "it": it, "nhieu": nhieu,
					"mo": "Bản sao kê này có %d dòng, bản kia %d dòng cùng thẻ, ngày, số tiền. Chọn số giao dịch thật." % (nhieu, it)}
		pi = next((x.get("purchase_invoice") for x in g["dong"] if x.get("purchase_invoice")), "")
		for i in range(1, so + 1):
			bc = [v[i - 1]["name"] for v in g["theo_ban"].values() if len(v) >= i]
			ra.append({"khoa": "%s:%d" % (khoa_goc, i), "the4": goc[0], "ngay_gd": goc[1], "ngay_bt": goc[2],
				"dv": g["mau"]["dv"], "tien": goc[4], "phan_loai": g["mau"]["phan_loai"], "bang_chung": bc,
				"can_quyet": cho if (cho and i > it) else None, "purchase_invoice": pi})
	# Nghi trùng khác chữ: cùng thẻ, ngày GD, ngày bút toán, số tiền; khác chữ đơn vị; mỗi căn cước
	# chỉ nằm ở một bản và hai bản khác nhau.
	theo_so = {}
	for g in ra:
		theo_so.setdefault((g["the4"], g["ngay_gd"], g["ngay_bt"], g["tien"]), []).append(g)
	for k, ds in theo_so.items():
		chu = {chuan_dv(x["dv"]) for x in ds}
		if len(chu) < 2:
			continue
		ban = [frozenset(_ban_cua(x, dong)) for x in ds]
		if len(set(ban)) < 2 or any(len(b) != 1 for b in ban):
			continue
		kq = "trung:%s:%s:%s:%s" % k
		quyet = (qd.get(kq) or {}).get("gia_tri")
		if quyet == "hai":
			continue
		if quyet == "mot":
			# Giữ giao dịch đầu theo thứ tự chữ, bỏ các dòng còn lại (bằng chứng vẫn giữ ở dòng giữ lại).
			ds_sx = sorted(ds, key=lambda x: chuan_dv(x["dv"]))
			for x in ds_sx[1:]:
				x["bo_vi_trung"] = ds_sx[0]["khoa"]
				ds_sx[0]["bang_chung"] = ds_sx[0]["bang_chung"] + x["bang_chung"]
			continue
		for x in ds:
			x["can_quyet"] = {"loai": "trung", "khoa_quyet": kq,
				"mo": "Cùng thẻ, cùng ngày, cùng %s đ nhưng chữ đơn vị chấp nhận thẻ khác nhau giữa hai bản sao kê. Một giao dịch hay hai?" % _so(x["tien"])}
	return [x for x in ra if not x.get("bo_vi_trung")]


def _ban_cua(gd, dong):
	ten = set(gd["bang_chung"])
	return {d["nguon"] for d in dong if d["name"] in ten}


def _so(x):
	return "{:,}".format(int(x)).replace(",", ".")


def thieu_sao_ke(chu_ky, ky, hom_nay, tre=NGAY_TRE):
	"""Các khoảng ngày bút toán chưa có sao kê ngân hàng phủ. THUẦN.

	Giao dịch của tháng ky có thể được ngân hàng ghi nợ tới tre ngày sau cuối
	tháng, nên cần phủ [đầu tháng, cuối tháng + tre]. chu_ky: [(từ, đến)] của sao
	kê PDF ngân hàng (chu kỳ do ngân hàng in, không phải kỳ máy suy ra)."""
	a = BN.ngay_dau_thang(ky)
	b = BN.ngay_cuoi_thang(ky) + timedelta(days=tre)
	if b >= hom_nay:
		thieu_sau = (max(a, hom_nay), b)
	else:
		thieu_sau = None
	khoang = sorted((max(a, x), min(b, y)) for x, y in chu_ky if y >= a and x <= b)
	thieu = []
	con = a
	for x, y in khoang:
		if x > con:
			thieu.append((con, x - timedelta(days=1)))
		con = max(con, y + timedelta(days=1))
	if con <= b:
		thieu.append((con, b))
	if thieu_sau and not any(t[0] <= thieu_sau[0] <= t[1] for t in thieu):
		thieu.append(thieu_sau)
	return thieu


def chon_giao_dich(gd_thang, quyet_dinh, da_ghi):
	"""Trạng thái từng giao dịch của tháng và danh sách được đưa vào bút toán. THUẦN.

	da_ghi: tập khoá đã nằm trong bút toán Meta đã ghi sổ của tháng."""
	qd = quyet_dinh or {}
	vao = []
	for g in gd_thang:
		pl = g["phan_loai"]
		chon = (qd.get("chon:" + g["khoa"]) or {}).get("gia_tri")
		if pl == "khong":
			g["trang_thai"] = GD_KHONG
		elif g.get("purchase_invoice"):
			g["trang_thai"] = GD_CT_KHAC
		elif g["khoa"] in da_ghi:
			g["trang_thai"] = GD_DA_GHI
		elif g.get("can_quyet"):
			g["trang_thai"] = GD_CHO
		elif pl == "phi_chua_ro" and chon not in ("vao", "bo"):
			g["trang_thai"] = GD_CHO
			g["can_quyet"] = {"loai": "chon", "khoa_quyet": "chon:" + g["khoa"],
				"mo": "Phí này không ghi rõ của giao dịch nào. Có phải phí đi kèm quảng cáo Meta không?"}
		elif chon == "bo":
			g["trang_thai"] = GD_BO
		else:
			g["trang_thai"] = GD_VAO
			vao.append(g)
	return vao


def nut_tay(g, quyet_dinh):
	"""Đường làm tay cho một giao dịch đã có trạng thái (Codex #590). THUẦN.

	Vào bút toán: kế toán bỏ ra vì đã ghi ở chứng từ khác (bắt lý do).
	Kế toán bỏ: đưa lại vào bút toán. Đã ghi sổ, chờ chọn, không thuộc Meta: không có."""
	tt = g.get("trang_thai")
	k = "chon:" + g["khoa"]
	if tt == GD_VAO:
		return {"khoa_quyet": k, "gia_tri": "bo", "ly_do": 1, "nhan": "Đã ghi ở chứng từ khác"}
	if tt == GD_BO:
		return {"khoa_quyet": k, "gia_tri": "vao", "ly_do": 0, "nhan": "Đưa lại vào bút toán",
			"ly_do_bo": ((quyet_dinh or {}).get(k) or {}).get("ly_do") or ""}
	return None


def nhap_da_cu(lan_lap, khoa_moi, qc_moi, phi_moi):
	"""THUẦN. So giao dịch và số tiền lúc lập nháp với hiện tại. "" là còn đúng."""
	if not lan_lap:
		return "không còn bản kê giao dịch lúc lập"
	bot = sorted(set(lan_lap.get("khoa") or []) - set(khoa_moi))
	them = sorted(set(khoa_moi) - set(lan_lap.get("khoa") or []))
	ra = []
	if bot:
		ra.append("%d giao dịch không còn vào bút toán (kế toán bỏ, hoặc đã ghi ở chứng từ khác)" % len(bot))
	if them:
		ra.append("%d giao dịch mới vào bút toán" % len(them))
	if not ra and (int(lan_lap.get("qc") or 0), int(lan_lap.get("phi") or 0)) != (int(qc_moi), int(phi_moi)):
		ra.append("số tiền đổi")
	return "; ".join(ra)


def dong_but_toan(vao, tk_qc, tk_phi, tk_the, bo_phan, ky):
	"""Các dòng bút toán Meta của tháng. THUẦN. Hoàn tiền ghi giảm 6417.

	Số có dấu cho từng tài khoản rồi đổi ra bên Nợ hoặc Có, để tháng hoàn nhiều
	hơn chi vẫn lập đúng chiều."""
	qc = sum(int(g["tien"]) for g in vao if g["phan_loai"] == "meta")
	phi = sum(int(g["tien"]) for g in vao if g["phan_loai"] in ("phi_meta", "phi_chua_ro"))
	thang = "%s/%s" % (ky[5:7], ky[:4])
	ra = []
	for tk, so, cc, nhan in ((tk_qc, qc, bo_phan, "Chi quảng cáo Meta tháng %s theo sao kê thẻ" % thang),
			(tk_phi, phi, bo_phan, "Phí thẻ đi kèm quảng cáo Meta tháng %s" % thang),
			(tk_the, -(qc + phi), "", "Nợ thẻ tín dụng Shinhan, quảng cáo Meta tháng %s" % thang)):
		if not so:
			continue
		ra.append({"account": tk, "cost_center": cc, "debit": so if so > 0 else 0, "credit": -so if so < 0 else 0,
			"user_remark": nhan})
	return ra, qc, phi


def trang_thai_thang(co_sao_ke, thieu, con_quyet, ct_khac_chua_xem, da_tru, da_ghi_so):
	"""Chip trạng thái một tháng trên màn đối soát. THUẦN."""
	if not co_sao_ke:
		return TH_CHUA_SK
	if thieu or con_quyet or ct_khac_chua_xem:
		return TH_CHUA_DU
	return TH_KHOP if int(da_tru) == int(da_ghi_so) else TH_LECH


def khoa_da_ghi(lich_su, je_da_ghi):
	"""Tập khoá giao dịch đã vào bút toán Meta ĐÃ GHI SỔ của tháng. THUẦN.

	lich_su: [{je, khoa:[...]}] cất trong bản ghi khoá; je_da_ghi: tập JE đã ghi sổ."""
	ra = set()
	for l in lich_su or []:
		if l.get("je") in je_da_ghi:
			ra.update(l.get("khoa") or [])
	return ra


# ------------------------------------------------ phần chạm Frappe

import frappe  # noqa: E402
from frappe.utils import cint, getdate, now_datetime, nowdate  # noqa: E402


def _cty(cty=None):
	if cty:
		return cty
	from vagabond import xuat_kho

	return xuat_kho._cong_ty()


def _tk(cty, so):
	from vagabond import xuat_kho

	ds = frappe.get_all("Account", filters={"company": cty, "is_group": 0, "disabled": 0},
		fields=["name", "account_number", "account_currency"], limit_page_length=0)
	ten = xuat_kho.chon_tai_khoan(ds, (so,))
	if not ten:
		frappe.throw("Công ty %s chưa có tài khoản %s dùng được (tài khoản chi tiết, đang dùng). Kế toán kiểm bảng tài khoản rồi bấm lại." % (cty, so))
	r = next(a for a in ds if a["name"] == ten)
	if (r.get("account_currency") or "VND") != "VND":
		frappe.throw("Tài khoản %s không phải tiền VND." % ten)
	if frappe.db.get_value("Account", ten, "freeze_account") == "Yes":
		frappe.throw("Tài khoản %s đang đóng băng." % ten)
	return ten


def _bo_phan_marketing(cty):
	from vagabond import bo_phan

	vt = frappe.db.get_value("Company", cty, "abbr") or ""
	cc = bo_phan.ten_that("Marketing", vt)
	return cc if frappe.db.exists("Cost Center", cc) else (frappe.db.get_value("Company", cty, "cost_center") or "")


def _doc_dong_the(cty):
	"""Dòng sao kê thẻ tín dụng hợp lệ của công ty: bỏ dòng đã bị thay bởi lần nạp
	sau, bỏ bản chờ giám đốc duyệt hoặc bị từ chối, bỏ tệp lỗi."""
	rows = frappe.db.sql(
		"""select d.name, d.nguon, d.loai, d.ma_su_kien, d.ma_don, d.mo_ta, d.thuc_nhan, d.ngay,
			coalesce(d.purchase_invoice, '') purchase_invoice, n.mau
		from `tabVagabond Doi Soat Dong` d join `tabVagabond Doi Soat Nguon` n on n.name = d.nguon
		where n.nhom = 'Thẻ tín dụng' and n.company = %(c)s and coalesce(d.thay_bang, '') = ''
			and n.trang_thai != 'Lỗi tệp' and coalesce(n.duong_vao, '') not in ('Chờ duyệt', 'Từ chối')""",
		{"c": cty}, as_dict=True)
	ra = []
	for r in rows:
		sk = tach_su_kien(r.ma_su_kien)
		if not sk:
			continue
		ra.append({"name": r.name, "nguon": r.nguon, "the4": sk["the4"], "ngay_gd": sk["ngay_gd"], "ngay_bt": sk["ngay_bt"],
			"dv": sk["dv"], "tien": BN.lam_tron_dong(r.thuc_nhan), "n": sk["n"], "phan_loai": phan_loai(r.loai, sk["dv"]),
			"purchase_invoice": r.purchase_invoice})
	return ra


def _chu_ky(cty):
	return [(getdate(r.tu_ngay), getdate(r.den_ngay)) for r in frappe.db.sql(
		"""select tu_ngay, den_ngay from `tabVagabond Doi Soat Nguon`
		where nhom='Thẻ tín dụng' and company=%s and mau=%s and trang_thai != 'Lỗi tệp'
			and coalesce(duong_vao, '') not in ('Chờ duyệt', 'Từ chối') and tu_ngay is not null and den_ngay is not null""",
		(cty, MAU_PDF), as_dict=True)]


def _sao_ke_cho_duyet(cty):
	return frappe.db.count("Vagabond Doi Soat Nguon", {"nhom": "Thẻ tín dụng", "company": cty, "duong_vao": "Chờ duyệt"})


def _chung_tu_khac(cty, ky, tk_qc):
	"""Chứng từ Meta có sẵn bằng đường khác trong tháng (không do máy lập)."""
	a, b = BN.ngay_dau_thang(ky), BN.ngay_cuoi_thang(ky)
	ra = []
	for r in frappe.db.sql(
			"""select name, posting_date, supplier_name, grand_total, docstatus from `tabPurchase Invoice`
			where company=%s and docstatus < 2 and coalesce(vgb_huy, 0) = 0 and posting_date between %s and %s
				and (supplier_name like '%%meta%%' or supplier_name like '%%facebook%%' or supplier like '%%meta%%' or supplier like '%%facebook%%')""",
			(cty, a, b), as_dict=True):
		ra.append({"doctype": "Purchase Invoice", "name": r.name, "ngay": str(r.posting_date), "mo": r.supplier_name,
			"tien": BN.lam_tron_dong(r.grand_total), "da_ghi_so": 1 if r.docstatus == 1 else 0})
	for r in frappe.db.sql(
			"""select je.name, je.posting_date, je.docstatus, coalesce(je.user_remark, '') mo,
				sum(jea.debit_in_account_currency) - sum(jea.credit_in_account_currency) tien
			from `tabJournal Entry` je join `tabJournal Entry Account` jea on jea.parent = je.name
			where je.company=%s and je.docstatus < 2 and coalesce(je.vgb_huy, 0) = 0 and je.posting_date between %s and %s
				and coalesce(je.vgb_tu_lap, '') not like 'META:%%' and jea.account = %s
				and (je.user_remark like '%%FACEBK%%' or je.user_remark like '%%meta%%' or je.user_remark like '%%facebook%%'
					or jea.user_remark like '%%FACEBK%%' or jea.user_remark like '%%meta%%' or jea.user_remark like '%%facebook%%')
			group by je.name""", (cty, a, b, tk_qc), as_dict=True):
		ra.append({"doctype": "Journal Entry", "name": r.name, "ngay": str(r.posting_date), "mo": r.mo[:140],
			"tien": BN.lam_tron_dong(r.tien), "da_ghi_so": 1 if r.docstatus == 1 else 0})
	return ra


def _quyet_dinh(bg):
	try:
		return json.loads((bg.get("quyet_dinh") if bg else "") or "{}") or {}
	except Exception:
		return {}


def _lich_su(bg):
	try:
		return (json.loads((bg.get("ban_ke") if bg else "") or "{}") or {}).get("lan") or []
	except Exception:
		return []


def _je_da_ghi(lich_su):
	ten = [l.get("je") for l in lich_su if l.get("je")]
	if not ten:
		return set()
	return set(frappe.get_all("Journal Entry", filters={"name": ["in", ten], "docstatus": 1}, pluck="name", limit_page_length=0))


def _so_da_ghi(cty, ky, je_da_ghi):
	if not je_da_ghi:
		return 0
	tks = (_tk(cty, TK_QC), _tk(cty, TK_PHI))
	r = frappe.db.sql(
		"""select sum(debit_in_account_currency) - sum(credit_in_account_currency) from `tabJournal Entry Account`
		where parent in %s and account in %s""", (tuple(je_da_ghi), tks))
	return BN.lam_tron_dong(r[0][0] if r and r[0][0] else 0)


def _da_tieu_meta(ky):
	a, b = BN.ngay_dau_thang(ky), BN.ngay_cuoi_thang(ky)
	ra = {}
	for r in frappe.db.sql(
			"""select tien_te, sum(so_tien) from `tabVagabond Chi Phi Quang Cao Ngay` where ngay between %s and %s group by tien_te""",
			(a, b)):
		ra[r[0] or ""] = round(float(r[1] or 0), 2)
	return ra


def tinh_thang(cty, ky, bg=None):
	"""Mọi số và trạng thái của một tháng. Một hàm cho cả màn xem lẫn lúc lập."""
	tk_qc = _tk(cty, TK_QC)
	qd = _quyet_dinh(bg)
	ls = _lich_su(bg)
	je_ghi = _je_da_ghi(ls)
	da_ghi_khoa = khoa_da_ghi(ls, je_ghi)
	dong = _doc_dong_the(cty)
	gd = gop_giao_dich(dong, qd)
	gd_thang = [g for g in gd if g["ngay_gd"][:7] == ky and g["phan_loai"] != "khong"]
	vao = chon_giao_dich(gd_thang, qd, da_ghi_khoa)
	chu_ky = _chu_ky(cty)
	thieu = thieu_sao_ke(chu_ky, ky, getdate(nowdate()))
	ct = _chung_tu_khac(cty, ky, tk_qc)
	ct_chua_xem = [c for c in ct if ("ct:%s:%s" % (c["doctype"], c["name"])) not in qd]
	da_tru = sum(int(g["tien"]) for g in gd_thang if g["trang_thai"] in (GD_VAO, GD_DA_GHI))
	da_ghi_so = _so_da_ghi(cty, ky, je_ghi)
	con_quyet = [g for g in gd_thang if g["trang_thai"] == GD_CHO]
	co_sk = bool(gd_thang) or any(y >= BN.ngay_dau_thang(ky) and x <= BN.ngay_cuoi_thang(ky) for x, y in chu_ky)
	return {
		"ky": ky, "giao_dich": gd_thang, "vao": vao, "thieu": [(str(a), str(b)) for a, b in thieu],
		"chung_tu_khac": [dict(c, da_xem=1 if ("ct:%s:%s" % (c["doctype"], c["name"])) in qd else 0) for c in ct],
		"ct_chua_xem": ct_chua_xem, "con_quyet": con_quyet, "da_tru": da_tru, "da_ghi_so": da_ghi_so,
		"da_tieu": _da_tieu_meta(ky), "trang_thai": trang_thai_thang(co_sk, thieu, con_quyet, ct_chua_xem, da_tru, da_ghi_so),
		"da_ghi_khoa": da_ghi_khoa, "lich_su": ls, "quyet_dinh": qd,
	}


def _ds_ky(so_thang):
	hn = BN.ky_cua(nowdate())
	return [BN.cong_thang(hn, -i) for i in range(int(so_thang))]


@frappe.whitelist()
def ds_thang(so_thang=6, trang_thai=None):
	"""Danh sách tháng cho màn Đối soát chi phí Meta."""
	BN.kiem_quyen(BN.QUYEN_XEM, "xem đối soát chi phí Meta")
	cty = _cty()
	n = max(1, min(24, cint(so_thang) or 6))
	rows = []
	dem = {"": 0}
	for ky in _ds_ky(n):
		bg = BN.doc_ban_ghi(BN.LOAI_META, cty, ky)
		t = tinh_thang(cty, ky, bg)
		tt, _info = BN.tinh_trang(bg)
		dem[""] += 1
		dem[t["trang_thai"]] = dem.get(t["trang_thai"], 0) + 1
		if trang_thai and t["trang_thai"] != trang_thai:
			continue
		rows.append({"ky": ky, "trang_thai": t["trang_thai"], "da_tieu": t["da_tieu"], "da_tru": t["da_tru"],
			"da_ghi_so": t["da_ghi_so"], "so_giao_dich": len(t["giao_dich"]), "so_cho": len(t["con_quyet"]),
			"thieu": t["thieu"], "but_toan": tt, "journal_entry": bg.journal_entry if bg else ""})
	return {"rows": rows, "dem": dem, "cho_duyet_sao_ke": _sao_ke_cho_duyet(cty),
		"duoc_lap": 1 if BN.co_quyen(BN.QUYEN_LAP) else 0, "duoc_ghi": 1 if BN.co_quyen(BN.QUYEN_GHI) else 0}


@frappe.whitelist()
def chi_tiet_thang(ky):
	BN.kiem_quyen(BN.QUYEN_XEM, "xem đối soát chi phí Meta")
	if not BN.ky_hop_le(ky):
		frappe.throw("Tháng không hợp lệ.")
	cty = _cty()
	bg = BN.doc_ban_ghi(BN.LOAI_META, cty, ky)
	t = tinh_thang(cty, ky, bg)
	tt, info = BN.tinh_trang(bg)
	dong, qc, phi = dong_but_toan(t["vao"], _tk(cty, TK_QC), _tk(cty, TK_PHI), _tk(cty, TK_THE), _bo_phan_marketing(cty), ky)
	gd = []
	for g in t["giao_dich"]:
		gd.append({"khoa": g["khoa"], "the4": g["the4"], "ngay_gd": g["ngay_gd"], "ngay_bt": g["ngay_bt"], "dv": g["dv"],
			"tien": g["tien"], "phan_loai": g["phan_loai"], "trang_thai": g["trang_thai"], "so_bang_chung": len(g["bang_chung"]),
			"can_quyet": g.get("can_quyet"), "purchase_invoice": g.get("purchase_invoice") or "",
			"nut_tay": nut_tay(g, t.get("quyet_dinh"))})
	return {
		"ky": ky, "trang_thai": t["trang_thai"], "da_tieu": t["da_tieu"], "da_tru": t["da_tru"], "da_ghi_so": t["da_ghi_so"],
		"thieu": t["thieu"], "giao_dich": gd, "chung_tu_khac": t["chung_tu_khac"],
		"but_toan": {"trang_thai": tt, "journal_entry": bg.journal_entry if bg else "", "du_kien_qc": qc, "du_kien_phi": phi,
			"nhap_cu": nhap_da_cu(next((l for l in reversed(_lich_su(bg)) if l.get("je") == bg.journal_entry), None),
				[g["khoa"] for g in t["vao"]], qc, phi) if tt in (BN.TT_NHAP, BN.TT_SUA_TAY) else "",
			"dong": [dict(d, debit=BN.lam_tron_dong(d["debit"]), credit=BN.lam_tron_dong(d["credit"])) for d in dong]},
		"tk": {"qc": _tk(cty, TK_QC), "phi": _tk(cty, TK_PHI), "the": _tk(cty, TK_THE)},
		"cho_duyet_sao_ke": _sao_ke_cho_duyet(cty),
		"duoc_lap": 1 if BN.co_quyen(BN.QUYEN_LAP) else 0, "duoc_ghi": 1 if BN.co_quyen(BN.QUYEN_GHI) else 0,
	}


LOAI_QUYET = {
	"chon": ("vao", "bo"),
	"trung": ("mot", "hai"),
	"dem": None,  # số nguyên trong khoảng [ít, nhiều]
	"ct": ("da_xem",),
}


@frappe.whitelist(methods=["POST"])
def quyet(ky, khoa_quyet, gia_tri, ly_do=None):
	"""Quyết định tay của kế toán cho một dòng (đường thủ công). Ghi người, giờ, lý do."""
	BN.kiem_quyen(BN.QUYEN_LAP, "quyết định dòng đối soát Meta")
	if not BN.ky_hop_le(ky):
		frappe.throw("Tháng không hợp lệ.")
	loai = str(khoa_quyet or "").split(":", 1)[0]
	if loai not in LOAI_QUYET:
		frappe.throw("Loại quyết định không hợp lệ.")
	cho_phep = LOAI_QUYET[loai]
	gia_tri = str(gia_tri or "").strip()
	if cho_phep is not None and gia_tri not in cho_phep:
		frappe.throw("Giá trị quyết định không hợp lệ.")
	if loai == "dem" and not gia_tri.isdigit():
		frappe.throw("Số giao dịch phải là số.")
	if (loai in ("trung", "dem", "ct") or (loai == "chon" and gia_tri == "bo")) and not (ly_do or "").strip():
		frappe.throw("Ghi lý do để người sau còn đối chiếu.")
	cty = _cty()
	bg = BN.khoa_ban_ghi(BN.LOAI_META, cty, ky)
	qd = _quyet_dinh(bg)
	qd[khoa_quyet] = {"gia_tri": gia_tri, "ly_do": (ly_do or "").strip()[:300], "boi": frappe.session.user, "luc": str(now_datetime())}
	bg.quyet_dinh = json.dumps(qd, ensure_ascii=False)
	bg.flags.vgb_tu_lap = True
	bg.flags.ignore_permissions = True
	bg.save(ignore_permissions=True)
	return {"ok": 1}


@frappe.whitelist(methods=["POST"])
def lap(ky):
	"""Lập hoặc cập nhật bút toán nháp Meta của tháng. Không ghi sổ."""
	BN.kiem_quyen(BN.QUYEN_LAP, "lập bút toán chi phí Meta")
	if not BN.ky_hop_le(ky):
		frappe.throw("Tháng không hợp lệ.")
	if BN.la_thang_tuong_lai(ky):
		frappe.throw("Chưa tới tháng %s/%s." % (ky[5:7], ky[:4]))
	cty = _cty()
	bg = BN.khoa_ban_ghi(BN.LOAI_META, cty, ky)
	t = tinh_thang(cty, ky, bg)
	if t["thieu"]:
		a, b = t["thieu"][0]
		frappe.throw("Chưa đủ sao kê: chưa có sao kê thẻ của ngân hàng cho ngày bút toán %s tới %s. Giao dịch tháng %s/%s có thể "
			"được ghi nợ tới %d ngày sau cuối tháng. Chờ sao kê về rồi bấm lại." % (
				getdate(a).strftime("%d/%m/%Y"), getdate(b).strftime("%d/%m/%Y"), ky[5:7], ky[:4], NGAY_TRE))
	if t["con_quyet"]:
		frappe.throw("Còn %d dòng chờ kế toán chọn. Chọn xong rồi bấm lại." % len(t["con_quyet"]))
	if t["ct_chua_xem"]:
		c = t["ct_chua_xem"][0]
		frappe.throw("Tháng này đã có chứng từ Meta khác (%s %s). Kế toán xem chứng từ đó và xác nhận không trùng trước khi lập." % (c["doctype"], c["name"]))
	if not t["vao"]:
		frappe.throw("Tháng %s/%s không còn giao dịch Meta nào chưa ghi sổ." % (ky[5:7], ky[:4]))
	dong, qc, phi = dong_but_toan(t["vao"], _tk(cty, TK_QC), _tk(cty, TK_PHI), _tk(cty, TK_THE), _bo_phan_marketing(cty), ky)
	kq = BN.lap_hoac_cap_nhat(BN.LOAI_META, cty, ky, dong,
		"Chi phí quảng cáo Meta tháng %s/%s theo sao kê thẻ Shinhan (hệ thống lập, kế toán ghi sổ)" % (ky[5:7], ky[:4]))
	# Lịch sử: mỗi bút toán nhớ khoá giao dịch của nó, để bút toán bổ sung sau này
	# không lấy lại giao dịch đã ghi sổ.
	bg = frappe.get_doc(BN.DT, bg.name)
	ls = [l for l in _lich_su(bg) if l.get("je") != kq["journal_entry"]] + [{"je": kq["journal_entry"], "khoa": [g["khoa"] for g in t["vao"]],
		"bang_chung": sorted({b for g in t["vao"] for b in g["bang_chung"]}), "qc": qc, "phi": phi, "luc": str(now_datetime())}]
	bg.ban_ke = json.dumps({"lan": ls}, ensure_ascii=False)
	bg.flags.vgb_tu_lap = True
	bg.flags.ignore_permissions = True
	bg.save(ignore_permissions=True)
	kq.update({"qc": qc, "phi": phi, "so_giao_dich": len(t["vao"])})
	return kq


@frappe.whitelist(methods=["POST"])
def ghi_so(ky):
	cty = _cty()

	def kiem_cu(bg):
		t = tinh_thang(cty, ky, bg)
		lan = [l for l in _lich_su(bg) if l.get("je") == bg.journal_entry]
		_d, qc, phi = dong_but_toan(t["vao"], "qc", "phi", "the", "", ky)
		return nhap_da_cu(lan[-1] if lan else None, [g["khoa"] for g in t["vao"]], qc, phi)

	return BN.ghi_so(BN.LOAI_META, cty, ky, kiem_cu=kiem_cu)


@frappe.whitelist(methods=["POST"])
def bo_nhap(ky, ly_do=None):
	BN.kiem_quyen(BN.QUYEN_LAP, "bỏ bút toán nháp")
	return BN.bo_nhap(BN.LOAI_META, _cty(), ky, ly_do)
