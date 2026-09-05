# -*- coding: utf-8 -*-
"""Hồ sơ thanh toán nhà cung cấp (APP) - lập, duyệt hai cấp, trả tiền, báo NCC.

Anh Việt 13/08/2026: "anh thấy thao tác trên desktop bị rối quá nên mình
làm trên app". Luồng thật ở tiệm:

  Thu mua gom hoá đơn mua đến hạn của MỘT nhà cung cấp thành một hồ sơ
  -> gửi kế toán (FIN) duyệt
  -> gửi giám đốc duyệt
  -> kế toán chuyển tiền
  -> máy dò SePay khớp giao dịch, sinh Payment Entry để clear công nợ
  -> bấm một nút gửi thư báo nhà cung cấp đã thanh toán

Vì sao KHÔNG dùng thẳng Payment Entry của ERPNext làm hồ sơ: Payment Entry
là bút toán chi tiền, nó sinh ra SAU khi đã duyệt. Cái thiếu là khúc TRƯỚC
đó - đề nghị, duyệt hai cấp, và dấu vết ai duyệt lúc nào. Doctype
Vagabond Ho So TT giữ khúc đó; đến lúc trả tiền mới sinh Payment Entry thật.

Ba điều phải giữ:
  1. Một hoá đơn không nằm trong hai hồ sơ còn hiệu lực (chặn ở doctype).
  2. Duyệt phải ĐÚNG THỨ TỰ: kế toán trước, giám đốc sau. Nhảy cóc là mất
     lớp kiểm soát.
  3. Người lập KHÔNG tự duyệt hồ sơ của chính mình.
"""

import base64
import io
import re

import frappe
from frappe.utils import add_days, cint, flt, getdate, now_datetime, nowdate

from vagabond import chon_ncc
from vagabond.lib import cfg

# Truoc buoc nao thi con go uy nhiem chi ra duoc. Lay tu tra_tien_app de hai
# ben khong bao gio lech nhau.
from vagabond.tra_tien_app import TT_GO_DUOC_UNC as TT_GO_DUOC_UNC_MAN
from vagabond.tra_tien_app import tach_ma as tach_ma_unc

# Bốn vai được đụng tới hồ sơ. Thu mua lập, kế toán duyệt cấp một, giám đốc
# duyệt cấp hai. System Manager có hết vì đó là anh Việt.
#
# Sửa 14/08/2026: trước đây VAI_GD nhận cả "Accounts Manager". Chị Dung mang
# vai đó, mà anh Việt lại vừa cho chị lập hồ sơ được bỏ qua bước FIN, nên
# chị vừa lập vừa duyệt cấp cuối được cho chính tờ mình lập - hai cấp duyệt
# coi như không còn. Giờ cấp giám đốc chỉ nhận vai "AP Giám đốc" (anh Việt
# và Dễ đang giữ), còn "Vagabond Giam doc" trong mã cũ vốn là vai KHÔNG TỒN
# TẠI trên site nên chưa bao giờ khớp với ai.
VAI_LAP = {"Purchase User", "Purchase Manager", "Accounts User", "Accounts Manager", "System Manager"}
VAI_FIN = {"Accounts User", "Accounts Manager", "AP Kiểm soát (FIN)", "System Manager"}
VAI_GD = {"AP Giám đốc", "System Manager"}

# Hop thu gui thu bao thanh toan cho nha cung cap, va hop thu nhan ban sao.
# De o day chu khong go thang trong ham: hai cho dung chung, va doi hop thu
# thi sua mot dong.
EMAIL_THU_MUA = "purchasing@thevagabondpatisserie.com"
EMAIL_KE_TOAN = "account@thevagabondpatisserie.com"
TEN_TIEM = "The Vagabond Pâtisserie"

# Ba loai ho so, khac nhau ca ve chung tu lan ve duong tien:
#   NCC        - cong ty no nha cung cap, tra thang cho ho tu MB
#   Hoan ung HD- Uyen da ung tien OCB mua hang CO hoa don, hang da nhap kho.
#                Gom cac hoa don CON NO lai, cong ty tra cho Uyen mot lan,
#                cong no nha cung cap sach luon (anh Viet chot 13/08/2026)
#   Hoan ung   - khoan le KHONG hoa don: hang test, phat sinh, bao tri.
#                Go tay tung khoan, gan voi giao dich chi ra tu OCB
LOAI_NCC = "NCC"
LOAI_HU_HD = "Hoan ung HD"
LOAI_HU = "Hoan ung"
LOAI_TKCT = "TK cong ty"

# Luong thu nam, KHONG phai mot ban ghi cua bang nay. Phieu tra truoc la mot
# Payment Entry: tien di truoc khi chua co hoa don nao. Man Ho so thanh toan
# van phai bay no ra, vi day la cho nguoi lap di tim no. Xem `tra_truoc.py`.
LOAI_TRA_TRUOC = "Tra truoc"

NHAN_LOAI = {
	LOAI_NCC: "Công nợ nhà cung cấp",
	LOAI_HU_HD: "Hoàn ứng có hoá đơn",
	LOAI_HU: "Hoàn ứng không hoá đơn",
	LOAI_TKCT: "Thanh toán từ TK công ty",
	LOAI_TRA_TRUOC: "Trả trước cho nhà cung cấp",
}

# Bóc tách chi phí lúc quyết toán thuế TNDN: khoản nào có hoá đơn GTGT mang
# tên Vagabond mới được trừ. Ghi ngay lúc lập hồ sơ, cuối năm khỏi ngồi đoán.
CP_HOP_LE = "Chi phi hop le"
CP_KHONG_HOP_LE = "Chi phi khong hop le"
NHAN_CP_THUE = {
	CP_HOP_LE: "Chi phí hợp lệ (có hoá đơn GTGT tên Vagabond)",
	CP_KHONG_HOP_LE: "Chi phí không hợp lệ tính thuế",
}

# Tai khoan quy tam ung OCB. Doc theo tai khoan ke toan 1411 chu khong theo
# ten Bank Account: ten thi ai doi cung duoc, con 1411 la tai khoan so cai
# da chot 04/08/2026 nen no gan nhu khong doi.
TK_QUY_TAM_UNG = "1411"

# Ca NHOM tai khoan tam ung, khong rieng OCB. Ngay 22/08/2026 v279 len that
# thi bang chon tai khoan hoan ung chi hien mot dong OCB, mat ACB, vi ACB nam
# o so cai 1412 chu khong phai 1411. Doi voi cau hoi "day co phai tai khoan
# tam ung khong" thi phai hoi ca nhom 141, con TK_QUY_TAM_UNG chi dung cho
# cho nao that su can dung ACB hay OCB cu the.
TK_NHOM_TAM_UNG = "141"

TT_NHAP = "Nhap"
TT_CHO_FIN = "Cho ke toan"
TT_CHO_GD = "Cho giam doc"
TT_DA_DUYET = "Da duyet"
TT_DA_TRA = "Da thanh toan"
TT_TU_CHOI = "Tu choi"
TT_HUY = "Huy"

# Tên hiển thị trên app. Cất trong mã bằng chữ không dấu để tránh lệ thuộc
# bảng mã của cột Select, còn màn hình thì luôn đọc bảng này.
NHAN = {
	TT_NHAP: "Nháp",
	TT_CHO_FIN: "Chờ kế toán duyệt",
	TT_CHO_GD: "Chờ giám đốc duyệt",
	TT_DA_DUYET: "Đã duyệt, chờ chuyển tiền",
	TT_DA_TRA: "Đã thanh toán",
	TT_TU_CHOI: "Từ chối",
	TT_HUY: "Huỷ",
}
THU_TU = [TT_NHAP, TT_CHO_FIN, TT_CHO_GD, TT_DA_DUYET, TT_DA_TRA, TT_TU_CHOI, TT_HUY]

# Ma ho so: APP.26.08.027 - anh Viet chot 13/08/2026, theo dung dang chung tu
# Uyen dang lap bang Excel (APP.26.08.027) va dang phieu thu tu dong da chay
# trong he (APP-26-08-001). So thu tu chay lai tu 001 moi thang.
#
# Ngan hang hay CAT dau cham trong noi dung chuyen khoan, nen khi do SePay
# phai so tren ban DA BO het dau cham va gach: APP2608027. Neu chi tim dung
# chuoi co dau cham thi gap giao dich that cung khong nhan ra.
RE_MA_APP = re.compile(r"APP\.?(\d{2})\.?(\d{2})\.?(\d{3})")
RE_MA_TRAN = re.compile(r"APP(\d{2})(\d{2})(\d{3})")


def _tran(s):
	"""Bo moi ky tu khong phai chu va so, viet hoa - de so ma tren noi dung
	chuyen khoan da bi ngan hang cat bot dau."""
	return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def _vai():
	return set(frappe.get_roles())


def _kiem(nhom, viec):
	if not (nhom & _vai()):
		frappe.throw("Tài khoản của bạn không có quyền %s." % viec)


def _sinh_ma(ngay=None):
	"""Mã hồ sơ dạng APP.26.08.027 - năm hai số, tháng hai số, số thứ tự ba số.

	Số thứ tự chạy lại từ 001 mỗi tháng. Đếm theo tiền tố của đúng tháng đó
	chứ không đếm tổng số hồ sơ: xoá một hồ sơ giữa tháng mà đếm tổng thì
	tháng sau sinh trùng mã, mà mã này đi vào nội dung chuyển khoản.
	"""
	d = getdate(ngay or nowdate())
	tien_to = "APP.%02d.%02d." % (d.year % 100, d.month)
	da_co = frappe.get_all(
		"Vagabond Ho So TT",
		filters={"ma": ["like", tien_to + "%"]},
		pluck="ma",
		limit_page_length=0,
	)
	lon_nhat = 0
	for m in da_co:
		duoi = str(m or "").rsplit(".", 1)[-1]
		if duoi.isdigit():
			lon_nhat = max(lon_nhat, int(duoi))
	for i in range(lon_nhat + 1, lon_nhat + 400):
		ma = tien_to + "%03d" % i
		if not frappe.db.exists("Vagabond Ho So TT", ma):
			return ma
	frappe.throw("Không sinh được mã hồ sơ, vui lòng thử lại.")


def _tien(v):
	try:
		return "{:,.0f}".format(float(v or 0)).replace(",", ".")
	except Exception:
		return str(v)


def _ngay_vn(s):
	t = str(s or "")
	return "/".join(reversed(t.split("-"))) if t else ""


def _ten_nguoi(email):
	"""Ten that thay vi dia chi thu.

	Anh Viet 13/08/2026 khoanh do man ho so: "hien thi ten dang hoang, chu
	khong phai hien email the nay". Phep doi da don ve mot cho duy nhat
	ngay 02/09/2026, xem `vagabond/ten_nguoi.py`.
	"""
	from vagabond import ten_nguoi

	return ten_nguoi.ten(email)


def _tk_nhan(ma_ncc):
	"""So tai khoan nhan tien cua mot nha cung cap, doc tu Bank Account.

	Tra ve dict rong neu chua khai - man hinh se bay o trong cho chi Dung
	go tay, khong chan luong.
	"""
	r = frappe.get_all(
		"Bank Account",
		filters={"party_type": "Supplier", "party": ma_ncc},
		fields=["account_name", "bank_account_no", "bank", "iban"],
		order_by="is_default desc, modified desc",
		limit_page_length=1,
	)
	if not r:
		return {}
	o = r[0]
	return {
		"ten_nhan": (o.get("account_name") or "").strip(),
		"stk_nhan": (o.get("bank_account_no") or o.get("iban") or "").strip(),
		"ngan_hang_nhan": (o.get("bank") or "").strip(),
	}


def _bo_dau(s):
	"""Bo dau tieng Viet - ngan hang chi nhan chu khong dau trong noi dung
	chuyen khoan, go co dau vao la ho bien thanh dau hoi."""
	import unicodedata

	t = unicodedata.normalize("NFD", str(s or ""))
	t = "".join(c for c in t if unicodedata.category(c) != "Mn")
	return t.replace("đ", "d").replace("Đ", "D")


# ------------------------------------------------------- chọn hoá đơn để lập


@frappe.whitelist()
def hoa_don_cho_tra(ncc=None, so_ngay=180, chi_qua_han=0, tu_khoa=""):
	"""Hoá đơn mua còn nợ của một nhà cung cấp, để thu mua tick vào hồ sơ.

	Bỏ sẵn những hoá đơn đang nằm trong hồ sơ khác còn hiệu lực - tick vào
	cũng bị chặn lúc lưu, bày ra chỉ tổ mất công.
	"""
	_kiem(VAI_LAP, "xem công nợ phải trả")
	loc = {"docstatus": 1, "outstanding_amount": [">", 0]}
	if ncc:
		loc["supplier"] = ncc
	if cint(so_ngay):
		loc["posting_date"] = [">=", add_days(nowdate(), -int(so_ngay))]
	ds = frappe.get_all(
		"Purchase Invoice",
		filters=loc,
		fields=[
			"name", "supplier", "supplier_name", "posting_date", "due_date",
			"grand_total", "outstanding_amount", "bill_no", "bill_date",
		],
		order_by="due_date asc, posting_date asc",
		limit_page_length=0,
	)
	da_gom = _hd_da_gom()
	hom_nay = getdate(nowdate())
	q = (tu_khoa or "").strip().lower()
	ra = []
	for r in ds:
		if r.name in da_gom:
			continue
		tre = (hom_nay - getdate(r.due_date)).days if r.due_date else 0
		if cint(chi_qua_han) and tre <= 0:
			continue
		# TIM NGAY LUC LAP. Codex neu tren #196: tim trong lich su sau khi
		# thanh toan khong thay duoc viec nay. Ho so hoan ung gom hang chuc
		# to cua nhieu nha, do bang mat het bang la cach de sot.
		# Khop ca ma hoa don trong he, so hoa don cua nha cung cap, va ten
		# nha - vi chi Dung cam to giay trong tay thi chi doc duoc so cua ho.
		if q and q not in (
				(r.name or "") + " " + (r.bill_no or "") + " "
				+ (r.supplier_name or "") + " " + (r.supplier or "")).lower():
			continue
		ra.append({
			"hoa_don": r.name,
			"ncc": r.supplier,
			"ten_ncc": r.supplier_name or r.supplier,
			"so_hd_ncc": r.bill_no or "",
			"ngay_hd": str(r.bill_date or r.posting_date or ""),
			"han_tra": str(r.due_date or ""),
			"tre_ngay": tre if tre > 0 else 0,
			"tong_hd": flt(r.grand_total),
			"con_no": flt(r.outstanding_amount),
		})
	return {
		"rows": ra,
		"tong": sum(x["con_no"] for x in ra),
		"qua_han": sum(x["con_no"] for x in ra if x["tre_ngay"] > 0),
		"so_hd": len(ra),
	}


@frappe.whitelist()
def ds_ncc_chon(so_ngay=365):
	"""Nguon du lieu cho O CHON nha cung cap (Issue #196).

	Man cu bay HET nha cung cap thanh mot bang chip dai, anh Viet keu roi.
	Doi thanh o chon thu gon, cham moi mo tam truot len co o tim. Muon tim
	duoc CA nha chi con hoa don nhap thi khong the dung `ds_ncc_con_no()`:
	ham do chi biet hoa don da ghi so.

	Gom so theo LO bang hai truy van group by, khong hoi tung nha mot. Site
	dang co hon nam tram nha cung cap, hoi tung nha la nam tram vong.

	Moi nha tra ve bon con so KHAC NHAU, va phai giu chung tach bach:
	  no_ghi_so    - tong con no tren hoa don da ghi so, khong gioi han ngay
	  lap_duoc_*   - phan THAT SU tick duoc ngay bay gio, tuc la da tru to
	                 dang nam trong ho so khac va to ngoai khoang ngay
	  qua_han_tien - phan qua han trong so lap duoc
	  nhap_*       - hoa don con nhap, KHONG cong vao no_ghi_so
	Codex neu tren #196: khong tach ra thi se co chip bao no ma mo bang ra
	trong, va tien nhap bi cong lan vao no la sai so.
	"""
	_kiem(VAI_LAP, "xem công nợ phải trả")
	moc = add_days(nowdate(), -int(cint(so_ngay) or 365))
	hom_nay = getdate(nowdate())
	da_gom = _hd_da_gom()
	gom = {}

	def o_cua(ma, ten):
		return gom.setdefault(ma, {
			"ncc": ma, "ten": ten or ma,
			"no_ghi_so": 0.0, "so_hd_no": 0,
			"lap_duoc_tien": 0.0, "lap_duoc_so": 0, "qua_han_tien": 0.0,
			"nhap_tien": 0.0, "nhap_so": 0,
		})

	for r in frappe.get_all(
		"Purchase Invoice",
		filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["name", "supplier", "supplier_name", "outstanding_amount",
			"posting_date", "due_date"],
		limit_page_length=0,
	):
		o = o_cua(r.supplier, r.supplier_name)
		o["no_ghi_so"] += flt(r.outstanding_amount)
		o["so_hd_no"] += 1
		if r.name in da_gom:
			continue
		if r.posting_date and str(r.posting_date) < str(moc):
			continue
		o["lap_duoc_tien"] += flt(r.outstanding_amount)
		o["lap_duoc_so"] += 1
		if r.due_date and getdate(r.due_date) < hom_nay:
			o["qua_han_tien"] += flt(r.outstanding_amount)

	for r in frappe.get_all(
		"Purchase Invoice",
		filters={"docstatus": 0},
		fields=["supplier", "supplier_name", "grand_total"],
		limit_page_length=0,
	):
		o = o_cua(r.supplier, r.supplier_name)
		o["nhap_so"] += 1
		o["nhap_tien"] += flt(r.grand_total)

	# DANH MUC DAY DU. Codex neu tren PR #198: gom o tren chi dung tu hoa don
	# con no va hoa don nhap, nen nha chi con hoa don DA TRA hoac DA HUY thi
	# khong tim ra, ma cung khong mo duoc "Vi sao thieu" de doc chinh nhung
	# ly do do. Nap them ca danh muc, nha khong co gi thi cac con so bang 0
	# va `xep_ncc` xep no xuong cuoi.
	for r in frappe.get_all(
		"Supplier",
		filters={"disabled": 0},
		fields=["name", "supplier_name"],
		limit_page_length=0,
	):
		o_cua(r.name, r.supplier_name)

	ra = chon_ncc.xep_ncc(list(gom.values()))
	for o in ra:
		o["chip"] = chon_ncc.chip_ncc(o)
	return {
		"ncc": ra,
		"so_ngay": int(cint(so_ngay) or 365),
		"moc_ngay": str(moc),
		"tong_lap_duoc": sum(x["lap_duoc_tien"] for x in ra),
		"tong_no": sum(x["no_ghi_so"] for x in ra),
	}


@frappe.whitelist()
def ly_do_thieu_hd(ncc=None, so_ngay=365, tu_khoa=""):
	"""Man "Xem vi sao thieu" (Issue #196, anh Viet chot 05/09/2026).

	Chi Dung noi *"list ra ma thieu co nghia la chua hach toan"*. Cau do
	khong dung: `hoa_don_cho_tra()` con loc theo ngay va con loai to dang
	nam trong ho so khac. Neu tin theo cau do ma moi nguoi go tay lai mot
	khoan da co to hoa don nhap, thi buoc giam doc duyet se sinh them mot
	hoa don mua nua - hoa don trung tren so.

	Nen o day liet ke DUNG ly do cua tung to, kem ma ho so dang giu no.
	Ham nay chi DOC. Khong sinh, khong sua, khong go to nao.
	"""
	_kiem(VAI_LAP, "xem công nợ phải trả")
	ncc = (ncc or "").strip()
	if not ncc:
		frappe.throw("Chưa chọn nhà cung cấp.")
	moc = add_days(nowdate(), -int(cint(so_ngay) or 365))
	ho_so_giu = _hd_ho_so_giu()
	ds = frappe.get_all(
		"Purchase Invoice",
		# KHONG loc docstatus o day. Codex neu tren PR #198: loc "< 2" la
		# vut to DA HUY di TRUOC khi `vi_sao_thieu` kip phan loai, nen nhan
		# "Da huy" khong bao gio hien ra, va man hinh con co the noi rang moi
		# to deu dang thay - trong khi to da huy dung la khong thay.
		filters={"supplier": ncc},
		fields=["name", "docstatus", "outstanding_amount", "grand_total",
			"posting_date", "due_date", "bill_no"],
		order_by="posting_date desc",
		limit_page_length=0,
	)
	hd = [{
		"name": r.name, "docstatus": r.docstatus,
		"outstanding": flt(r.outstanding_amount),
		"posting_date": str(r.posting_date or ""),
		"tong": flt(r.grand_total), "so_hd_ncc": r.bill_no or "",
	} for r in ds]
	# TIM TREN MAY CHU, khong chi loc tren man hinh.
	#
	# Codex neu vong hai tren PR #198: cat 500 to moi NHOM roi de man hinh
	# loc tren DOM thi to thu 501 khong bao gio tra ra duoc, du du lieu co
	# that. Loc theo tu khoa TRUOC khi cat thi go so hoa don nao cung ra,
	# ke ca to nam ngoai 500 to dau.
	q = (tu_khoa or "").strip().lower()
	if q:
		hd = [x for x in hd
			if q in ((x["name"] or "") + " " + (x["so_hd_ncc"] or "")).lower()]
	nhom, chon_duoc = chon_ncc.gom_ly_do(hd, str(moc), ho_so_giu)
	ra = []
	for ma in chon_ncc.THU_TU_LY_DO:
		to = nhom.get(ma) or []
		if not to:
			continue
		for x in to:
			x["ho_so_giu"] = ho_so_giu.get(x["name"], "")
		# Truoc day cat con 40 to. Codex neu tren PR #198: muc dich cua nut
		# nay la tra ra DUNG to dang thieu de khoi nhap trung, cat di thi to
		# thu 41 khong tra duoc, tuc la nut hong dung cai viec no sinh ra de
		# lam. Van chan tren 500 to MOI NHOM de khong ganh mot goi khong lo
		# ve dien thoai, nhung to nam ngoai khoang do van tra duoc: go tu
		# khoa vao thi bo loc o tren chay TRUOC luc cat.
		ra.append({"ly_do": ma, "so": len(to), "tien": sum(x["tong"] for x in to),
			"hoa_don": to[:500], "bi_cat": 1 if len(to) > 500 else 0})
	return {
		"ncc": ncc,
		"ten": frappe.db.get_value("Supplier", ncc, "supplier_name") or ncc,
		"moc_ngay": str(moc), "so_ngay": int(cint(so_ngay) or 365),
		"tu_khoa": q, "nhom": ra, "chon_duoc": len(chon_duoc),
	}


def _hd_ho_so_giu():
	"""Hoa don nao dang nam trong ho so nao. Giong `_hd_da_gom` nhung tra ve
	CA MA ho so, de man "Vi sao thieu" chi duoc dung cho ma tim."""
	rows = frappe.db.sql(
		"""select d.hoa_don, p.ma from `tabVagabond Ho So TT Dong` d
		inner join `tabVagabond Ho So TT` p on p.name = d.parent
		where p.trang_thai in ('Nhap', 'Cho ke toan', 'Cho giam doc', 'Da duyet')""",
		as_dict=True,
	)
	return dict((r["hoa_don"], r["ma"]) for r in rows if r["hoa_don"])


def _hd_da_gom():
	"""Hoá đơn đang nằm trong một hồ sơ còn hiệu lực."""
	rows = frappe.db.sql(
		"""select d.hoa_don from `tabVagabond Ho So TT Dong` d
		inner join `tabVagabond Ho So TT` p on p.name = d.parent
		where p.trang_thai in ('Nhap', 'Cho ke toan', 'Cho giam doc', 'Da duyet')""",
		as_dict=True,
	)
	return set(r["hoa_don"] for r in rows)


@frappe.whitelist()
def ds_ncc_con_no():
	"""Nhà cung cấp nào còn nợ, để app bày chip chọn."""
	_kiem(VAI_LAP, "xem công nợ phải trả")
	ds = frappe.get_all(
		"Purchase Invoice",
		filters={"docstatus": 1, "outstanding_amount": [">", 0]},
		fields=["supplier", "supplier_name", "outstanding_amount", "due_date"],
		limit_page_length=0,
	)
	da_gom = None
	hom_nay = getdate(nowdate())
	gom = {}
	for r in ds:
		o = gom.setdefault(r.supplier, {
			"ncc": r.supplier, "ten": r.supplier_name or r.supplier,
			"so_hd": 0, "tien": 0.0, "qua_han": 0.0,
		})
		o["so_hd"] += 1
		o["tien"] += flt(r.outstanding_amount)
		if r.due_date and getdate(r.due_date) < hom_nay:
			o["qua_han"] += flt(r.outstanding_amount)
	ra = sorted(gom.values(), key=lambda x: (-x["qua_han"], -x["tien"]))
	return {"ncc": ra, "tong": sum(x["tien"] for x in ra)}


# ------------------------------------------------------------------ lập hồ sơ


@frappe.whitelist()
def _buoc_ke_tiep_khi_gui(nguoi=None):
	"""Gửi đi duyệt thì rơi vào bước nào.

	Anh Việt 13/08/2026: *"chị Dung cũng có thể tạo hồ sơ thanh toán, và nếu
	là tài khoản chị ấy tạo thì sẽ bỏ qua bước duyệt FIN luôn, mà lên thẳng
	giám đốc duyệt"*. Hợp lý: chị Dung CHÍNH LÀ cấp duyệt kế toán, bắt chị tự
	duyệt hồ sơ của mình chỉ là một cú bấm thừa. Mà quy tắc người lập không
	tự duyệt vẫn còn nguyên - ở đây là bỏ hẳn một cấp, không phải tự duyệt.
	"""
	vai_nguoi = set(frappe.get_roles(nguoi)) if nguoi else _vai()
	return TT_CHO_GD if (VAI_FIN & vai_nguoi) else TT_CHO_FIN


@frappe.whitelist()
def tao(ncc=None, hoa_don=None, ghi_chu="", gui_luon=0, loai=None, tk_chi=None,
		loai_cp_thue=None, nguoi_ung=None, tk_hoan=None):
	"""Lập một hồ sơ từ danh sách hoá đơn đã tick.

	hoa_don: danh sách mã Purchase Invoice, hoặc danh sách
	{"hoa_don": ..., "so_tien": ...} khi trả một phần.

	nguoi_ung: bắt buộc với hồ sơ Hoàn ứng có hoá đơn. Đó là người đã ứng
	tiền mua hộ, tức người NHẬN lại tiền - khác hẳn nhà cung cấp trên từng
	dòng hoá đơn.

	tk_hoan: Bank Account nhận tiền, cũng chỉ dùng cho hồ sơ hoàn ứng. Trước
	28/08/2026 màn này không có ô chọn nên máy lấy đại tài khoản mặc định
	của người ứng; người ứng có cả ACB lẫn OCB thì đó là chuyển nhầm ngân
	hàng mà không ai biết. Nay người lập chọn tay, và lựa chọn đó được LƯU
	vào ô `tk_nhan` chứ không tan thành ba chuỗi rời.
	"""
	_kiem(VAI_LAP, "lập hồ sơ thanh toán")
	if isinstance(hoa_don, str):
		hoa_don = frappe.parse_json(hoa_don)
	if not hoa_don:
		frappe.throw("Chưa chọn hoá đơn nào.")

	dong = []
	ncc_thay = set()
	for x in hoa_don:
		ma = x if isinstance(x, str) else x.get("hoa_don")
		hd = frappe.db.get_value(
			"Purchase Invoice", ma,
			["name", "supplier", "supplier_name", "posting_date", "bill_date",
			 "bill_no", "due_date", "grand_total", "outstanding_amount", "docstatus"],
			as_dict=True,
		)
		if not hd:
			frappe.throw("Không có hoá đơn mua %s." % ma)
		if hd.docstatus != 1:
			frappe.throw("Hoá đơn %s chưa ghi sổ nên chưa đề nghị trả được." % ma)
		if flt(hd.outstanding_amount) <= 0:
			frappe.throw("Hoá đơn %s đã trả xong rồi." % ma)
		ncc_thay.add(hd.supplier)
		so_tien = flt(x.get("so_tien")) if isinstance(x, dict) and x.get("so_tien") else flt(hd.outstanding_amount)
		# PHIEU THANH TOAN NOI BO NOI VAO DAY CHI LA CHUNG TU, KHONG PHAI TIEN.
		#
		# Anh Viet chot 04/09/2026. Man hoan ung CO hoa don lay so tien theo
		# HOA DON, phieu noi vao chi de chung minh nhan vien da ung tien mua
		# hoa don do, va de keo anh chung tu cua phieu sang. Khong dong toi
		# mot dong nao cua `so_tien`.
		#
		# Nhung van phai KHOA phieu lai: phieu da dung lam chung tu o day ma
		# van hien trong bang chon cua man hoan ung khong hoa don thi co
		# nguoi noi lai lan hai va de nghi hoan tiep - dung duong chi hai lan
		# ma v413 vua bit ben kia.
		ma_phieu = (x.get("de_nghi_chi") or "").strip() if isinstance(x, dict) else ""
		dong.append({
			"de_nghi_chi": ma_phieu or None,
			"hoa_don": hd.name,
			"so_hd_ncc": hd.bill_no or "",
			"ngay_hd": hd.bill_date or hd.posting_date,
			"han_tra": hd.due_date,
			"tong_hd": flt(hd.grand_total),
			"con_no": flt(hd.outstanding_amount),
			"so_tien": so_tien,
			# Ten nha cung cap cua RIENG dong nay. Ho so gom nhieu nha thi
			# dau ho so khong con noi duoc dong nay cua ai; khong ghi o day
			# la ke toan phai mo tung hoa don ra doi chieu.
			"ben_ban": hd.supplier_name or hd.supplier or "",
		})

	# Mot ho so mot nha cung cap - NHUNG chi voi hai luong tra thang cho ho.
	#
	# Uyen 19/08/2026, qua anh Viet: *"phai gop duoc nha cung cap luc lam
	# APP hoan ung (hien tai chi lam duoc theo tung NCC rat mat thoi gian vi
	# hoan ung la toan mua le te lat nhat)"*.
	#
	# Ly do cu ghi o day la "chuyen tien la chuyen cho MOT nguoi". Dung voi
	# luong cong no NCC va luong chi tu TK cong ty: tien di thang toi nha
	# cung cap, hai nha trong mot ho so thi khong doi chieu duoc voi ai.
	#
	# Nhung voi HOAN UNG CO HOA DON thi tien KHONG di toi nha cung cap. Uyen
	# da tra ho ho bang tien mat roi; cong ty chuyen tra lai cho UYEN. Nen
	# so nha cung cap trong ho so khong lien quan gi den viec chuyen tien -
	# cai rang buoc do la ap nham tu luong kia sang.
	# Chan truoc khi lam bat cu viec gi khac: mot hoa don chi duoc nam trong
	# MOT ho so con song. Xem _chan_hoa_don_trung de biet vi sao chan cung.
	_chan_hoa_don_trung(dong)
	# `theo_tien=False`: o luong nay so tien lay theo hoa don chu khong theo
	# phieu, nen khong so hai so voi nhau. Van giu hai chot con lai: mot
	# phieu khong duoc noi hai dong, va phieu phai da qua duyet.
	_soi_phieu_noi_bo(dong, theo_tien=False)

	nhieu_ncc = (loai or "") == LOAI_HU_HD
	if len(ncc_thay) > 1 and not nhieu_ncc:
		frappe.throw(
			"Hồ sơ %s chỉ gom hoá đơn của MỘT nhà cung cấp, vì tiền chuyển "
			"thẳng cho họ. Đang chọn %d nhà: %s. Nếu đây là khoản anh chị đã "
			"ứng tiền mua hộ thì lập theo luồng \"Hoàn ứng có hoá đơn\", "
			"luồng đó gom được nhiều nhà cùng lúc."
			% (NHAN_LOAI.get(loai or LOAI_NCC, "thanh toán"),
			   len(ncc_thay), ", ".join(sorted(ncc_thay)))
		)
	ma_ncc = (ncc or "").strip() or sorted(ncc_thay)[0]

	doc = frappe.new_doc("Vagabond Ho So TT")
	doc.ma = _sinh_ma()
	if (loai or "") == LOAI_TKCT:
		# Chi tu TK cong ty, the "chi phi hop le": van tick hoa don GTGT that
		# nhu luong NCC, chi khac o cho tien di tu tai khoan cong ty da chon
		# va ho so mang san phan loai chi phi thue.
		tk_chi = (tk_chi or "").strip()
		if not tk_chi or not frappe.db.exists("Bank Account", tk_chi):
			frappe.throw("Chưa chọn tài khoản ngân hàng của công ty để chi.")
		if (loai_cp_thue or "").strip() != CP_HOP_LE:
			frappe.throw(
				"Luồng chi từ TK công ty có tick hoá đơn chỉ dùng cho chi phí hợp lệ. "
				"Khoản không hoá đơn thì gõ tay từng khoản ở màn riêng."
			)
		doc.loai = LOAI_TKCT
		doc.tk_chi = tk_chi
		doc.loai_cp_thue = CP_HOP_LE
	else:
		doc.loai = LOAI_HU_HD if (loai or "") == LOAI_HU_HD else LOAI_NCC
	doc.ngay = nowdate()
	doc.so_ncc = len(ncc_thay)

	if nhieu_ncc:
		# HO SO HOAN UNG: ben nhan tien la NGUOI DA UNG, khong phai nha cung
		# cap. Truoc day cho nay dien san so tai khoan cua nha cung cap vao
		# o nguoi thu huong roi de nguoi dung sua tay - mot cai bay that su,
		# vi bam Luu ma quen sua la tien di thang toi nha cung cap trong khi
		# ho da duoc tra tien mat roi. Ho so APP.26.08.007 lap 19/08/2026
		# mang dung hinh do: dau ho so ghi AEON, o nguoi thu huong lai la
		# mot ca nhan.
		ma_ung = (nguoi_ung or "").strip()
		if not ma_ung:
			frappe.throw(
				"Chưa chọn người được hoàn ứng. Đây là người đã ứng tiền mua hộ và sẽ nhận lại tiền, vui lòng chọn ở hàng chip trên cùng màn hình."
			)
		if not frappe.db.exists("Supplier", ma_ung):
			frappe.throw(
				"Không có nhà cung cấp %s. Người được hoàn ứng phải có sẵn hồ sơ "
				"nhà cung cấp để còn theo dõi công nợ." % ma_ung
			)
		doc.nguoi_ung = ma_ung
		doc.ten_nguoi_ung = frappe.db.get_value("Supplier", ma_ung, "supplier_name") or ma_ung
		# Dau ho so mang ten NGUOI DUOC HOAN UNG, dung y nhu ho so hoan ung
		# khong hoa don. Nha cung cap cua tung khoan nam o tung dong.
		doc.nha_cung_cap = ma_ung
		doc.ten_ncc = doc.ten_nguoi_ung
		# KHONG dien email nha cung cap: thu bao "da thanh toan" gui cho ho
		# la bao nham, tien cong ty tra la tra cho nguoi ung.
		doc.email_ncc = ""
		lay_tk = ma_ung
	else:
		doc.nha_cung_cap = ma_ncc
		doc.ten_ncc = frappe.db.get_value("Supplier", ma_ncc, "supplier_name") or ma_ncc
		doc.email_ncc = _email_ncc(ma_ncc)
		lay_tk = ma_ncc

	doc.trang_thai = _buoc_ke_tiep_khi_gui() if cint(gui_luon) else TT_NHAP
	doc.nguoi_tao = frappe.session.user
	doc.ghi_chu = (ghi_chu or "").strip()
	for k, v in (_tk_nhan(lay_tk) or {}).items():
		doc.set(k, v)
	# Tai khoan nguoi lap CHON de len tren tai khoan mac dinh, y het luong
	# hoan ung khong hoa don. Va lan nay giu lai ca cai LINK, de sau con
	# doi chieu duoc ho so nay da chuyen vao tai khoan nao.
	if nhieu_ncc:
		doc.tk_nhan = _dat_tk_nhan(doc, tk_hoan, doc.nguoi_ung)
	if not doc.ten_nhan:
		doc.ten_nhan = doc.ten_ncc
	for d in dong:
		doc.append("dong", d)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	# Khoa phieu noi bo NGAY SAU khi chen, y het `tao_hoan_ung`. Ham nay nem
	# loi khi phieu da thuoc ho so khac, va vi chua `frappe.db.commit()` nen
	# Frappe cuon nguoc ca ban ghi vua chen.
	_khoa_phieu_noi_bo(doc.name, dong)
	_dap_tep_phieu_noi_bo(doc)

	# Dinh PDF ban the hien cua tung hoa don vao ho so, de ke toan truong
	# duyet ngay tren phieu thay vi tai tay tu M-Invoice (anh Viet
	# 20/08/2026). Ham nay tu nuot loi: M-Invoice sap thi ho so van tao
	# duoc, chi thieu tep.
	from vagabond import minvoice_tep

	so_pdf = minvoice_tep.dinh_vao_ho_so(doc)

	frappe.db.commit()
	return {
		"ok": 1, "ma": doc.name, "tong_tien": flt(doc.tong_tien),
		"trang_thai": doc.trang_thai, "so_pdf_hddt": so_pdf,
	}


# ------------------------------------------------------------- APP hoàn ứng


# Hai mã món của luồng quỹ tạm ứng OCB, chốt 04/08/2026: hàng test và hàng
# mua lẻ KHÔNG nhập kho, KHÔNG qua đơn mua hàng, lập thẳng hoá đơn mua với
# hai mã này. Không theo dõi tồn, đổ vào tài khoản chi phí 6428.
MON_CO_VAT = "CP-MUANHO-HD"
MON_KHONG_VAT = "CP-MUANHO-KHD"


@frappe.whitelist()
def tao_hoan_ung(nguoi_ung=None, dong=None, ghi_chu="", da_tam_ung=0, gui_luon=0,
		tk_hoan=None):
	"""Lập hồ sơ hoàn ứng: gõ tay từng khoản đã chi hộ bằng tiền tạm ứng.

	Anh Việt 13/08/2026: "APP này có khả năng đính kèm các hoá đơn từ nhiều
	NCC nhỏ lẻ khác nhau, bao gồm cả hàng test không nhập kho, hàng phát
	sinh, chi phí (bảo trì,...)".

	Khác hẳn hồ sơ NCC ở chỗ: lúc lập CHƯA có hoá đơn mua nào trong hệ. Máy
	chỉ giữ những gì Uyên gõ; đến bước giám đốc duyệt mới sinh hoá đơn mua
	thật, xem _sinh_hoa_don_hoan_ung. Làm vậy để hồ sơ bị từ chối giữa chừng
	không để lại rác trên sổ.

	dong: danh sách {ngay_hd, so_hd_ncc, noi_dung, ben_ban, loai_chi,
	co_vat, so_tien, ghi_chu}.
	"""
	_kiem(VAI_LAP, "lập hồ sơ hoàn ứng")
	if isinstance(dong, str):
		dong = frappe.parse_json(dong)
	if not dong:
		frappe.throw("Chưa nhập khoản chi nào.")
	# Anh Viet 22/08/2026: man nay khong bat chon nha cung cap nua, chi chon
	# TAI KHOAN nhan tien (ACB hay OCB). Ma nha cung cap van phai co, vi so
	# cai treo cong no theo ma - nhung nay may tu suy tu tai khoan chu khong
	# bat nguoi lap doi trong danh sach vai tram dong.
	tk_hoan = (tk_hoan or "").strip()
	ma_ncc = (nguoi_ung or "").strip()
	if tk_hoan and not ma_ncc:
		ma_ncc = _ncc_cua_tk_hoan(tk_hoan)
	if not ma_ncc:
		frappe.throw(
			"Tài khoản %s chưa gắn với mã nhà cung cấp nào nên máy không treo công nợ được. Mở Bank Account đó bên Next, điền ô Party là mã người ứng, rồi lập lại." % tk_hoan
			if tk_hoan else
			"Chưa chọn tài khoản nhận tiền hoàn ứng. Vui lòng chọn ACB hay OCB."
		)
	if not frappe.db.exists("Supplier", ma_ncc):
		frappe.throw(
			"Không có nhà cung cấp %s. Người được hoàn ứng phải có sẵn hồ sơ "
			"nhà cung cấp để còn theo dõi công nợ." % ma_ncc
		)

	sach = []
	for x in dong:
		if not isinstance(x, dict):
			frappe.throw("Dòng hoàn ứng phải là một khoản chi có nội dung và số tiền.")
		tien = flt(x.get("so_tien"))
		noi_dung = (x.get("noi_dung") or "").strip()
		if tien <= 0:
			frappe.throw("Khoản \"%s\" ghi 0 đồng." % (noi_dung or "chưa đặt tên"))
		if not noi_dung:
			frappe.throw("Có khoản %s đ chưa ghi nội dung chi." % _tien(tien))
		# Chung tu cua rieng dong nay (anh Viet 22/08/2026, siet ho so hoan
		# ung). Loc qua _tep_hop_le de khong luu ma tep ma ma khong con tren
		# may chu: ban in gap ma la se im lang bo qua, ke toan tuong co anh
		# ma mo ra khong thay gi.
		ma_tep = _tep_hop_le(x.get("tep"))
		sach.append({
			"ngay_hd": x.get("ngay_hd") or nowdate(),
			"so_hd_ncc": (x.get("so_hd_ncc") or "").strip(),
			"noi_dung": noi_dung,
			"ben_ban": (x.get("ben_ban") or "").strip(),
			"loai_chi": (x.get("loai_chi") or "").strip(),
			"co_vat": 1 if cint(x.get("co_vat")) else 0,
			"so_tien": tien,
			"ma_giao_dich": (x.get("ma_giao_dich") or "").strip(),
			"ghi_chu": (x.get("ghi_chu") or "").strip(),
			"loai_chung_tu": (x.get("loai_chung_tu") or "").strip() or None,
			"tep": "\n".join(ma_tep),
			"de_nghi_chi": (x.get("de_nghi_chi") or "").strip() or None,
		})

	# Hang rao chung tu: chi chan khi GUI di duyet, luu nhap thi khong.
	# Nhap la cho lam do, bat du giay to ngay tu dong dau thi khong ai luu
	# nhap duoc nua (anh Viet chot 22/08/2026).
	# Chan hoa don trung o CA HAI luc, luu nhap lan gui di duyet. Khac voi
	# hang rao chung tu: thieu giay to thi con bo sung duoc nen chi chan luc
	# gui, con hoa don trung thi luu nhap da la sai roi.
	_chan_hoa_don_trung(sach)
	_soi_phieu_noi_bo(sach)

	if cint(gui_luon):
		_chan_thieu_chung_tu(sach)

	doc = frappe.new_doc("Vagabond Ho So TT")
	doc.ma = _sinh_ma()
	doc.loai = LOAI_HU
	doc.ngay = nowdate()
	doc.nha_cung_cap = ma_ncc
	doc.ten_ncc = frappe.db.get_value("Supplier", ma_ncc, "supplier_name") or ma_ncc
	doc.email_ncc = _email_ncc(ma_ncc)
	doc.da_tam_ung = flt(da_tam_ung)
	doc.trang_thai = _buoc_ke_tiep_khi_gui() if cint(gui_luon) else TT_NHAP
	doc.nguoi_tao = frappe.session.user
	doc.ghi_chu = (ghi_chu or "").strip()
	for k, v in (_tk_nhan(ma_ncc) or {}).items():
		doc.set(k, v)
	# Tai khoan nguoi lap CHON de len tren tai khoan mac dinh cua ma NCC:
	# nguoi ung co ca ACB lan OCB, cai chon tay moi la cai dung cho to nay.
	# Giu ca cai LINK chu khong chi ba chuoi, de sau con doi chieu duoc.
	doc.tk_nhan = _dat_tk_nhan(doc, tk_hoan, ma_ncc)
	if not doc.ten_nhan:
		doc.ten_nhan = doc.ten_ncc
	for d in sach:
		doc.append("dong", d)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	# Tep cua tung dong phai THUOC VE ho so, khong thi don don tep mo coi cua
	# Frappe don mat sau vai ngay va bo ho so thanh rong ruot.
	_gan_tep_ve_ho_so(doc.name, sach)
	# Dong nao lay tu phieu noi bo thi dong dau phieu do lai, khong cho nguoi
	# khac noi lan hai vao mot ho so khac.
	_khoa_phieu_noi_bo(doc.name, sach)
	frappe.db.commit()
	return {
		"ok": 1, "ma": doc.name, "tong_tien": flt(doc.tong_tien),
		"con_lai": flt(doc.con_lai), "trang_thai": doc.trang_thai,
	}



@frappe.whitelist()
def tao_chi_cong_ty(ncc=None, tk_chi=None, loai_cp_thue=None, dong=None, ghi_chu="", gui_luon=0,
		loai_chung_tu=None, tep=None):
	"""Lập hồ sơ chi thẳng từ tài khoản công ty, không qua Purchasing.

	Luồng thứ tư, anh Việt chốt 17/08/2026. Ba luồng cũ đều kết thúc bằng một
	hoá đơn mua và một Payment Entry xoá công nợ. Luồng này thì không: tiền đi
	thẳng từ tài khoản ngân hàng công ty cho các khoản phát sinh không qua bộ
	phận mua hàng - tiền điện, tiền nước, phí bảo trì. Trước đây kế toán phải
	mượn tạm luồng hoàn ứng, ghi sai bản chất dòng tiền.

	Kế toán tự định khoản: mỗi dòng tự chọn TK Nợ, TK Có để trống thì lấy tài
	khoản sổ cái của ngân hàng chi. Máy không gán cứng tài khoản chi phí nào.

	loai_cp_thue bắt buộc, để cuối năm lọc ra các khoản không được trừ khi
	quyết toán thuế TNDN mà không phải mở lại từng chứng từ.

	Chứng từ đính kèm nằm ở TỪNG DÒNG, không phải ở hồ sơ (anh Việt
	24/08/2026). Trước đó cả hồ sơ dùng chung một ô đính kèm và một loại
	chứng từ, nên một phiếu chi tiền điện, tiền nước và phí bảo trì chỉ khai
	được một loại, còn ba tệp thì nằm chung một rổ không biết tờ nào của
	khoản nào. Hai tham số `loai_chung_tu` và `tep` ở đây giữ lại cho những
	màn cũ còn gọi kiểu cũ: chúng chỉ được dùng khi dòng KHÔNG tự mang tệp.
	"""
	_kiem(VAI_LAP | VAI_FIN, "lập hồ sơ chi từ tài khoản công ty")
	if isinstance(dong, str):
		dong = frappe.parse_json(dong)
	if not dong:
		frappe.throw("Chưa nhập khoản chi nào.")

	ma_ncc = (ncc or "").strip()
	if not ma_ncc or not frappe.db.exists("Supplier", ma_ncc):
		frappe.throw("Chưa chọn bên nhận tiền, hoặc bên nhận chưa có hồ sơ nhà cung cấp.")

	tk_chi = (tk_chi or "").strip()
	if not tk_chi or not frappe.db.exists("Bank Account", tk_chi):
		frappe.throw("Chưa chọn tài khoản ngân hàng của công ty để chi.")
	tk_so_cai = frappe.db.get_value("Bank Account", tk_chi, "account")
	if not tk_so_cai:
		frappe.throw(
			"Tài khoản ngân hàng %s chưa gắn tài khoản sổ cái, chưa hạch toán được. Vui lòng mở Bank Account bên Next điền ô Account." % tk_chi
		)

	if isinstance(tep, str):
		tep = frappe.parse_json(tep)
	tep = tep or []
	loai_cp_thue = (loai_cp_thue or "").strip()
	loai_chung_tu = (loai_chung_tu or "").strip()
	if loai_cp_thue not in (CP_HOP_LE, CP_KHONG_HOP_LE):
		frappe.throw(
			"Chưa chọn loại chi phí thuế. Có hoá đơn GTGT mang tên Vagabond thì chọn "
			"chi phí hợp lệ, còn biên lai nội bộ hay hoá đơn đứng tên chủ nhà thì chọn "
			"không hợp lệ."
		)

	sach = []
	for x in dong:
		if not isinstance(x, dict):
			frappe.throw("Dòng chi phải là một khoản có nội dung và số tiền.")
		tien = flt(x.get("so_tien"))
		noi_dung = (x.get("noi_dung") or "").strip()
		if tien <= 0:
			frappe.throw("Khoản \"%s\" ghi 0 đồng." % (noi_dung or "chưa đặt tên"))
		if not noi_dung:
			frappe.throw("Có khoản %s đ chưa ghi nội dung chi." % _tien(tien))
		tk_no = (x.get("tk_no") or "").strip()
		if not tk_no:
			frappe.throw("Khoản \"%s\" chưa chọn tài khoản Nợ." % noi_dung)
		if not frappe.db.exists("Account", tk_no):
			frappe.throw("Không có tài khoản %s trong hệ thống tài khoản." % tk_no)
		tk_co = (x.get("tk_co") or "").strip()
		if tk_co and not frappe.db.exists("Account", tk_co):
			frappe.throw("Không có tài khoản %s trong hệ thống tài khoản." % tk_co)
		ma_tep = _tep_hop_le(x.get("tep"))
		sach.append({
			"ngay_hd": x.get("ngay_hd") or nowdate(),
			"so_hd_ncc": (x.get("so_hd_ncc") or "").strip(),
			"noi_dung": noi_dung,
			"ben_ban": (x.get("ben_ban") or "").strip(),
			"loai_chi": (x.get("loai_chi") or "").strip(),
			"co_vat": 1 if cint(x.get("co_vat")) else 0,
			"tk_no": tk_no,
			"tk_co": tk_co or tk_so_cai,
			"so_tien": tien,
			"ma_giao_dich": (x.get("ma_giao_dich") or "").strip(),
			"ghi_chu": (x.get("ghi_chu") or "").strip(),
			"loai_chung_tu": (x.get("loai_chung_tu") or "").strip() or None,
			"tep": "\n".join(ma_tep),
		})

	# Luong chi tu TK cong ty cung phai chan: dong o day co the mang hoa don.
	_chan_hoa_don_trung(sach)

	# Chung tu: xet TUNG DONG. Doi cu la mot o dinh kem chung cho ca ho so,
	# nay moi khoan tu mang giay to cua no. Van nhan duong cu (`loai_chung_tu`
	# va `tep` o muc ho so) cho dong nao khong tu mang gi, de ban app cu tren
	# may nguoi ta chua tai lai van lap duoc phieu.
	if loai_cp_thue == CP_KHONG_HOP_LE:
		# Khong co hoa don he thong thi ho so chi con dua vao chung tu roi.
		# Bat o day chu khong doi den luc duyet: de trong ma van luu duoc thi
		# ho so nam do khong ai nho quay lai dinh kem.
		chung = _tep_hop_le(tep)
		thieu = []
		for i, d in enumerate(sach):
			if not d["tep"] and chung:
				d["loai_chung_tu"] = d["loai_chung_tu"] or loai_chung_tu or None
				d["tep"] = "\n".join(chung)
			if not d["tep"]:
				thieu.append("  · Khoản %d - %s: chưa đính kèm chứng từ" % (i + 1, d["noi_dung"]))
			elif not d["loai_chung_tu"]:
				thieu.append("  · Khoản %d - %s: chưa chọn loại chứng từ" % (i + 1, d["noi_dung"]))
		if thieu:
			frappe.throw(
				"Chi không hoá đơn thì mỗi khoản phải tự mang chứng từ của nó:\n\n%s\n\n"
				"Bấm vào ô đính kèm ngay trên dòng đó để tải giấy tờ lên."
				% "\n".join(thieu)
			)

	doc = frappe.new_doc("Vagabond Ho So TT")
	doc.ma = _sinh_ma()
	doc.loai = LOAI_TKCT
	doc.ngay = nowdate()
	doc.tk_chi = tk_chi
	doc.loai_cp_thue = loai_cp_thue
	# O muc ho so chi con la NHAN cho de nhin tren danh sach: loai that
	# nam o tung dong. De trong het thi lay loai cua khoan dau tien.
	doc.loai_chung_tu = loai_chung_tu or next(
		(d["loai_chung_tu"] for d in sach if d.get("loai_chung_tu")), None
	)
	doc.nha_cung_cap = ma_ncc
	doc.ten_ncc = frappe.db.get_value("Supplier", ma_ncc, "supplier_name") or ma_ncc
	doc.email_ncc = _email_ncc(ma_ncc)
	doc.trang_thai = _buoc_ke_tiep_khi_gui() if cint(gui_luon) else TT_NHAP
	doc.nguoi_tao = frappe.session.user
	doc.ghi_chu = (ghi_chu or "").strip()
	for k, v in (_tk_nhan(ma_ncc) or {}).items():
		doc.set(k, v)
	if not doc.ten_nhan:
		doc.ten_nhan = doc.ten_ncc
	for d in sach:
		doc.append("dong", d)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)

	# File da duoc tai len truoc khi ho so ton tai (khong the lam nguoc lai),
	# gio moi tro ve ho so. Dung db.set_value chu khong save: File co validate
	# rieng, ma o day chi can doi con tro.
	_gan_tep_ve_ho_so(doc.name, sach)
	da_gan = sum(len(_tep_cua_dong(d.get("tep"))) for d in sach)
	if loai_cp_thue == CP_KHONG_HOP_LE and not da_gan:
		frappe.throw("Không gắn được chứng từ nào vào hồ sơ, vui lòng thử tải lại file.")

	frappe.db.commit()
	_ghi_vet(doc.name, "Lập hồ sơ chi từ TK công ty %s đ · %d chứng từ trên %d khoản" % (
		_tien(doc.tong_tien), da_gan, len(sach),
	))
	return {"ok": 1, "ma": doc.name, "trang_thai": doc.trang_thai}


def _tao_but_toan_tkct(doc, ngay, phuong_thuc):
	"""Chi thẳng từ tài khoản công ty: sinh Journal Entry theo định khoản kế toán chọn.

	Không đi qua Payment Entry vì không có hoá đơn mua nào để xoá công nợ.
	Mỗi dòng một bút toán Nợ; các dòng cùng TK Có thì gộp lại cho sổ gọn.
	"""
	from vagabond.tra_tien_app import chep_unc

	dong = [d for d in doc.dong if flt(d.so_tien) > 0]
	if not dong:
		frappe.throw("Hồ sơ %s không có khoản chi nào." % doc.name)

	tk_ngan_hang = frappe.db.get_value("Bank Account", doc.tk_chi, "account") if doc.tk_chi else None
	cong_ty = frappe.db.get_single_value("Global Defaults", "default_company")
	ttcp = frappe.db.get_value("Company", cong_ty, "cost_center")

	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Bank Entry"
	je.company = cong_ty
	je.posting_date = ngay
	je.cheque_no = doc.ma_giao_dich or doc.name
	je.cheque_date = ngay
	je.user_remark = "Hồ sơ thanh toán %s - %s - %s" % (
		doc.name, doc.ten_ncc or doc.nha_cung_cap, NHAN_CP_THUE.get(doc.loai_cp_thue, "")
	)

	gom_co = {}
	for d in dong:
		tk_no = d.tk_no
		if not tk_no:
			frappe.throw("Khoản \"%s\" chưa chọn tài khoản Nợ, chưa hạch toán được." % (d.noi_dung or ""))
		hang = {
			"account": tk_no,
			"debit_in_account_currency": flt(d.so_tien),
			"cost_center": ttcp,
			"user_remark": d.noi_dung or "",
		}
		loai_tk = frappe.db.get_value("Account", tk_no, "account_type")
		if loai_tk in ("Payable", "Receivable"):
			hang["party_type"] = "Supplier" if loai_tk == "Payable" else "Customer"
			hang["party"] = doc.nha_cung_cap
		je.append("accounts", hang)
		tk_co = d.tk_co or tk_ngan_hang
		if not tk_co:
			frappe.throw("Khoản \"%s\" chưa có tài khoản Có." % (d.noi_dung or ""))
		gom_co[tk_co] = gom_co.get(tk_co, 0.0) + flt(d.so_tien)

	for tk_co, tien in gom_co.items():
		hang = {
			"account": tk_co,
			"credit_in_account_currency": flt(tien),
			"cost_center": ttcp,
		}
		loai_tk = frappe.db.get_value("Account", tk_co, "account_type")
		if loai_tk in ("Payable", "Receivable"):
			hang["party_type"] = "Supplier" if loai_tk == "Payable" else "Customer"
			hang["party"] = doc.nha_cung_cap
		je.append("accounts", hang)

	je.flags.ignore_permissions = True
	je.insert(ignore_permissions=True)
	chep_unc(doc.name, "Journal Entry", je.name)
	je.submit()
	frappe.db.commit()
	return je.name


def _bank_account_quy():
	"""Bank Account cua quy tam ung dang dung, de lay sao ke mac dinh.

	Truoc 28/08/2026 ham nay go cung 1411, tuc quy OCB. Anh Viet bo tai
	khoan OCB ngay 28/08/2026, nen go cung nhu vay la man hinh doi mai mot
	sao ke khong bao gio ve nua.

	Nay hoi ca nhom 141 nhung CHI LAY TAI KHOAN CON BAT. Tat mot tai khoan
	ben Next la ham nay tu chuyen sang cai con lai, khong phai sua ma nguon.
	Uu tien 1411 neu no van con bat, de nhung ky so lieu cu doc ra khong
	doi cho.
	"""
	dang = frappe.get_all(
		"Bank Account",
		filters={
			"is_company_account": 1,
			"disabled": 0,
			"account": ["like", TK_NHOM_TAM_UNG + "%"],
		},
		fields=["name", "account"],
		order_by="name asc",
		limit_page_length=0,
	)
	if not dang:
		return None
	for b in dang:
		if str(b.get("account") or "").strip().startswith(TK_QUY_TAM_UNG):
			return b["name"]
	return dang[0]["name"]


def _gd_da_gom():
	"""Mã giao dịch đã nằm trong một hồ sơ còn hiệu lực."""
	rows = frappe.db.sql(
		"""select d.ma_giao_dich from `tabVagabond Ho So TT Dong` d
		inner join `tabVagabond Ho So TT` p on p.name = d.parent
		where ifnull(d.ma_giao_dich, '') != ''
		and p.trang_thai in ('Nhap', 'Cho ke toan', 'Cho giam doc', 'Da duyet', 'Da thanh toan')""",
		as_dict=True,
	)
	return set((r["ma_giao_dich"] or "").strip() for r in rows)


@frappe.whitelist()
def sepay_ocb(so_ngay=60, chi_chua_gom=1, tai_khoan=None):
	"""Giao dịch CHI RA từ quỹ tạm ứng OCB, để Uyên tick thay vì gõ tay.

	Anh Việt 13/08/2026: *"tất cả các loại hoàn ứng thì đều là trả lại tiền
	đã ứng cho tài khoản OCB của Uyên"*. Đúng vậy, nên nguồn đáng tin nhất
	không phải trí nhớ mà là sao kê: mỗi khoản đã chi đều có một giao dịch
	ngân hàng với ngày, số tiền và nội dung sẵn.

	Lấy giao dịch làm gốc thì hai cái lợi: số tiền và ngày không thể gõ sai,
	và mỗi khoản gắn đúng một giao dịch nên số dư quỹ 1411 tự khớp. Bỏ sẵn
	giao dịch đã nằm trong hồ sơ khác - tick vào cũng bị chặn lúc lưu.
	"""
	_kiem(VAI_LAP, "xem giao dịch quỹ tạm ứng")
	# Anh Viet 22/08/2026 mo them cua sao ke ACB. Truyen tai khoan thi doc
	# dung tai khoan do; bo trong thi giu nguyen nep cu, tu tim quy 1411.
	# Mot ham cho ca hai ngan hang, khong tach doi: tach doi la sau nay sua
	# mot ben quen ben kia.
	tk = (tai_khoan or "").strip() or _bank_account_quy()
	if not tk:
		return {"rows": [], "loi": "Chưa khai Bank Account nào trỏ vào tài khoản %s." % TK_QUY_TAM_UNG}
	if not frappe.db.exists("Bank Account", tk):
		return {"rows": [], "loi": "Không có tài khoản ngân hàng %s." % tk}
	ds = frappe.get_all(
		"Bank Transaction",
		filters={
			"bank_account": tk,
			"withdrawal": [">", 0],
			"date": [">=", add_days(nowdate(), -int(so_ngay or 60))],
			"docstatus": ["<", 2],
		},
		fields=["name", "date", "withdrawal", "description", "reference_number", "status"],
		order_by="date desc, creation desc",
		limit_page_length=0,
	)
	da_gom = _gd_da_gom() if cint(chi_chua_gom) else set()
	ra = []
	for r in ds:
		ma = (r.reference_number or r.name or "").strip()
		if ma in da_gom:
			continue
		ra.append({
			"ma_giao_dich": ma,
			"ngay": str(r.date or ""),
			"so_tien": flt(r.withdrawal),
			"noi_dung": (r.description or "").strip(),
			"trang_thai": r.status or "",
		})
	nh = frappe.db.get_value("Bank Account", tk, ["bank", "bank_account_no"], as_dict=True) or {}
	return {
		"rows": ra,
		"tong": sum(x["so_tien"] for x in ra),
		"tai_khoan": tk,
		"ngan_hang": (nh.get("bank") or "").strip(),
		"so_tk": (nh.get("bank_account_no") or "").strip(),
		"so_gd": len(ra),
	}


@frappe.whitelist()
def ds_nguoi_ung(tu_khoa=""):
	"""Nhà cung cấp để chọn làm người được hoàn ứng.

	Bày sẵn những người đã từng đứng tên hồ sơ hoàn ứng lên đầu - ở tiệm
	chỉ vài người ứng tiền, ngày nào cũng phải cuộn hết danh sách nhà cung
	cấp thì mệt.
	"""
	_kiem(VAI_LAP, "lập hồ sơ hoàn ứng")
	hay = frappe.get_all(
		"Vagabond Ho So TT",
		filters={"loai": ["in", [LOAI_HU, LOAI_HU_HD]]},
		fields=["nha_cung_cap", "ten_ncc"],
		order_by="creation desc",
		limit_page_length=200,
	)
	quen, thu_tu = {}, []
	for r in hay:
		if r.nha_cung_cap not in quen:
			quen[r.nha_cung_cap] = r.ten_ncc or r.nha_cung_cap
			thu_tu.append(r.nha_cung_cap)

	loc = {"disabled": 0}
	q = (tu_khoa or "").strip()
	if q:
		loc["supplier_name"] = ["like", "%" + q + "%"]
	ds = frappe.get_all(
		"Supplier", filters=loc, fields=["name", "supplier_name"],
		order_by="supplier_name asc", limit_page_length=300,
	)
	ten = {r.name: (r.supplier_name or r.name) for r in ds}
	ra = [{"ncc": m, "ten": quen[m], "hay_dung": 1} for m in thu_tu if not q or q.lower() in (quen[m] or "").lower()]
	da_co = set(thu_tu)
	for r in ds:
		if r.name in da_co:
			continue
		ra.append({"ncc": r.name, "ten": ten[r.name], "hay_dung": 0})
	return {"ncc": ra, "mon": {"co_vat": MON_CO_VAT, "khong_vat": MON_KHONG_VAT}}



@frappe.whitelist()
def ds_tk_cong_ty():
	"""Các tài khoản ngân hàng của công ty dùng để chi thẳng.

	Bỏ quỹ tạm ứng 1411 ra: quỹ đó là tiền Uyên ứng, không phải tiền công ty,
	chi từ đó là luồng hoàn ứng chứ không phải luồng này.
	"""
	_kiem(VAI_LAP | VAI_FIN, "xem tài khoản ngân hàng công ty")
	ra = []
	for b in frappe.get_all(
		"Bank Account",
		filters={"is_company_account": 1, "disabled": 0},
		fields=["name", "account_name", "bank", "bank_account_no", "account"],
		limit_page_length=0,
	):
		if not b.account:
			continue
		if str(b.account).strip().startswith(TK_NHOM_TAM_UNG):
			continue
		ra.append({
			"ma": b.name,
			"ten": b.account_name or b.name,
			"ngan_hang": b.bank or "",
			"so_tk": b.bank_account_no or "",
			"tk_so_cai": b.account,
		})
	return {"tk": ra}


@frappe.whitelist()
def ds_tai_khoan(tu_khoa="", gioi_han=40):
	"""Tra tài khoản sổ cái cho kế toán tự định khoản trên điện thoại.

	`gioi_han=0` nghĩa là LẤY HẾT danh mục, không cắt. Màn hình dùng đường đó
	để bày cả danh mục vào ô chọn rồi lọc ngay trên máy, khỏi bắt người ta
	đoán từ khoá trước khi được nhìn thấy gì.

	Hệ thống tài khoản là bảng có hạn, vài trăm dòng, nên lấy hết là an toàn.
	Đừng bắt chước chỗ này cho hoá đơn hay chứng từ: những bảng đó lớn dần
	theo thời gian.
	"""
	_kiem(VAI_LAP | VAI_FIN, "tra hệ thống tài khoản")
	q = (tu_khoa or "").strip()
	loc = {"is_group": 0, "disabled": 0}
	# Phep tinh so dong toi da nam o `chon_ncc.gioi_han_tk`, la phep THUAN nen
	# ca kiem goi that duoc chu khong chi do chuoi trong ma nguon (Codex neu
	# tren PR #207). Dau vao xau thi NEM LOI CO CHU, khong doan bua.
	from vagabond import chon_ncc

	try:
		han = chon_ncc.gioi_han_tk(gioi_han)
	except chon_ncc.GioiHanXau:
		frappe.throw(
			"Số dòng tối đa gửi lên không đọc được: %r. Gửi số nguyên không âm, "
			"hoặc gửi 0 để lấy hết danh mục, hoặc bỏ hẳn ô này để lấy %d dòng "
			"như mặc định." % (gioi_han, chon_ncc.HAN_TK_MAC_DINH),
			title="Số dòng tối đa không hợp lệ",
		)
	ds = []
	if q:
		ds = frappe.get_all(
			"Account", filters=loc,
			or_filters={"name": ["like", "%" + q + "%"], "account_name": ["like", "%" + q + "%"]},
			fields=["name", "account_name", "account_type", "root_type"],
			order_by="name asc", limit_page_length=han,
		)
	else:
		ds = frappe.get_all(
			"Account", filters=loc,
			fields=["name", "account_name", "account_type", "root_type"],
			order_by="name asc", limit_page_length=han,
		)
	return {"tk": [{
		"ma": a.name, "ten": a.account_name or a.name,
		"loai": a.root_type or "",
	} for a in ds]}


def _sinh_hoa_don_hoan_ung(doc):
	"""Dựng hoá đơn mua cho các khoản gõ tay, gắn ngược lại vào dòng hồ sơ.

	Chia làm hai kiểu, có lý do kế toán chứ không phải cho vui:
	  - Khoản CÓ hoá đơn VAT: mỗi số hoá đơn một Hoá đơn mua riêng, vì kê
	    khai thuế đầu vào đi theo từng số hoá đơn.
	  - Khoản KHÔNG có hoá đơn: gom hết vào MỘT hoá đơn mua nhiều dòng, đỡ
	    rác sổ.

	KHÔNG tự tách thuế GTGT: máy không biết thuế suất từng khoản, đoán bừa
	là sai số kê khai. Tổng ghi đúng bằng số tiền Uyên gõ; kế toán mở hoá
	đơn bên Next thêm dòng thuế nếu cần khấu trừ.
	"""
	da_co = [d.hoa_don for d in doc.dong if d.hoa_don]
	if da_co:
		return da_co

	for mon in (MON_CO_VAT, MON_KHONG_VAT):
		if not frappe.db.exists("Item", mon):
			frappe.throw(
				"Chưa có mã món <b>%s</b> trong hệ. Đây là mã dùng cho hàng mua lẻ không nhập kho; nhờ chị Dung tạo trước rồi duyệt lại." % mon
			)

	cong_ty = frappe.db.get_single_value("Global Defaults", "default_company")
	if not cong_ty:
		ds_ct = frappe.get_all("Company", pluck="name", limit_page_length=2)
		cong_ty = ds_ct[0] if ds_ct else None
	if not cong_ty:
		frappe.throw("Chưa khai công ty mặc định nên chưa lập được hoá đơn mua.")

	def _mot_hd(cac_dong, so_hd, ngay_hd, mon):
		pi = frappe.new_doc("Purchase Invoice")
		pi.company = cong_ty
		pi.supplier = doc.nha_cung_cap
		pi.set_posting_time = 1
		pi.posting_date = ngay_hd or doc.ngay or nowdate()
		pi.bill_no = so_hd or doc.name
		pi.bill_date = ngay_hd or doc.ngay
		pi.due_date = doc.ngay or nowdate()
		pi.update_stock = 0
		pi.remarks = "Hoàn ứng %s - %s" % (doc.name, doc.ten_ncc or doc.nha_cung_cap)
		for d in cac_dong:
			mo_ta = d.noi_dung or ""
			if d.ben_ban:
				mo_ta += " (mua của %s)" % d.ben_ban
			if d.loai_chi:
				mo_ta += " [%s]" % d.loai_chi
			pi.append("items", {
				"item_code": mon,
				"item_name": (d.noi_dung or mon)[:140],
				"description": mo_ta,
				"qty": 1,
				"rate": flt(d.so_tien),
				"uom": frappe.db.get_value("Item", mon, "stock_uom") or "Nos",
			})
		pi.flags.ignore_permissions = True
		pi.insert(ignore_permissions=True)
		pi.submit()
		return pi.name

	sinh = []
	try:
		co_vat = [d for d in doc.dong if cint(d.co_vat)]
		khong_vat = [d for d in doc.dong if not cint(d.co_vat)]
		for d in co_vat:
			ten_pi = _mot_hd([d], d.so_hd_ncc, d.ngay_hd, MON_CO_VAT)
			d.db_set("hoa_don", ten_pi, update_modified=False)
			sinh.append(ten_pi)
		if khong_vat:
			ngay = min([getdate(d.ngay_hd) for d in khong_vat if d.ngay_hd] or [getdate(doc.ngay or nowdate())])
			ten_pi = _mot_hd(khong_vat, doc.name, ngay, MON_KHONG_VAT)
			for d in khong_vat:
				d.db_set("hoa_don", ten_pi, update_modified=False)
			sinh.append(ten_pi)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: sinh hoa don hoan ung %s" % doc.name)
		frappe.throw(
			"Không lập được hoá đơn mua cho hồ sơ hoàn ứng %s. Hồ sơ giữ nguyên "
			"ở bước chờ giám đốc, chưa có gì vào sổ. Nhờ chị Dung xem lại mã món "
			"%s / %s và kỳ kế toán rồi duyệt lại." % (doc.name, MON_CO_VAT, MON_KHONG_VAT)
		)
	frappe.db.commit()
	_ghi_vet(doc.name, "Sinh hoá đơn mua cho hoàn ứng: %s" % ", ".join(sinh))
	return sinh


def _email_ncc(ma):
	"""Email nhà cung cấp: ưu tiên liên hệ chính, rồi tới email trên hồ sơ."""
	e = frappe.db.get_value("Supplier", ma, "email_id")
	if e:
		return e
	lh = frappe.db.get_value("Supplier", ma, "supplier_primary_contact")
	if lh:
		e = frappe.db.get_value("Contact", lh, "email_id")
		if e:
			return e
	rows = frappe.db.sql(
		"""select c.email_id from `tabContact` c
		inner join `tabDynamic Link` l on l.parent = c.name
		where l.link_doctype = 'Supplier' and l.link_name = %s
		and ifnull(c.email_id, '') != '' limit 1""",
		ma,
	)
	return rows[0][0] if rows else ""


# ------------------------------------------------------------------ danh sách


@frappe.whitelist()
def danh_sach(trang_thai=None, ncc=None, tu=None, den=None, tu_khoa="", so_ngay=90, loai=None,
		loai_cp_thue=None, tk_chi=None):
	"""Màn Hồ sơ thanh toán: danh sách kèm đếm theo trạng thái cho chip.

	`tk_chi` lọc theo tài khoản ngân hàng công ty đã chi. Lọc ở CUỐI hàm y
	hệt `trang_thai`, không đưa vào `loc` của `get_all`: bảng chip phải đếm
	trên bộ CHƯA lọc, đưa vào `loc` thì bấm một chip xong các chip kia rỗng
	hết và không bấm lại được.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem hồ sơ thanh toán")
	if tu and den:
		loc = {"ngay": ["between", [str(tu), str(den)]]}
	else:
		loc = {"ngay": [">=", add_days(nowdate(), -int(so_ngay or 90))]}
	if ncc:
		loc["nha_cung_cap"] = ncc
	if loai:
		loc["loai"] = loai
	if loai_cp_thue:
		loc["loai_cp_thue"] = loai_cp_thue
	ds = frappe.get_all(
		"Vagabond Ho So TT",
		filters=loc,
		fields=[
			"name", "ma", "loai", "ngay", "nha_cung_cap", "ten_ncc", "trang_thai",
			"tong_tien", "da_tra", "da_tam_ung", "con_lai",
			"han_tra_som_nhat", "nguoi_tao",
			"fin_boi", "gd_boi", "ngay_thanh_toan", "ma_giao_dich",
			"email_da_gui", "ly_do_tu_choi", "ghi_chu",
			"loai_cp_thue", "tk_chi", "unc_tep",
		],
		order_by="ngay desc, creation desc",
		limit_page_length=0,
	)
	so_dong = {}
	if ds:
		# Dem bang get_all chu khong viet SQL "in %s": danh sach mot phan tu
		# thi tuple Python ra ('X',) va cu phap SQL do khong chac chan giua
		# cac ban MariaDB.
		for d in frappe.get_all(
			"Vagabond Ho So TT Dong",
			filters={"parent": ["in", [r.name for r in ds]]},
			fields=["parent"],
			limit_page_length=0,
		):
			so_dong[d.parent] = so_dong.get(d.parent, 0) + 1

	hom_nay = getdate(nowdate())
	q = (tu_khoa or "").strip().lower()
	ra = []
	for r in ds:
		o = dict(r)
		o["so_hd"] = so_dong.get(r.name, 0)
		o["nhan"] = NHAN.get(r.trang_thai, r.trang_thai)
		o["loai"] = r.loai or "NCC"
		o["nhan_cp_thue"] = NHAN_CP_THUE.get(r.loai_cp_thue, "")
		# Ho so nao con thieu uy nhiem chi. De chi Dung nhin mot cai la biet
		# to nao can tai UNC ve truoc, khoi mo tung ho so ra do.
		o["co_unc"] = 1 if tach_ma_unc(r.get("unc_tep")) else 0
		o["nguoi_tao_ten"] = _ten_nguoi(r.nguoi_tao)
		o["fin_ten"] = _ten_nguoi(r.fin_boi)
		o["gd_ten"] = _ten_nguoi(r.gd_boi)
		o["tre_ngay"] = (
			(hom_nay - getdate(r.han_tra_som_nhat)).days
			if r.han_tra_som_nhat
			and getdate(r.han_tra_som_nhat) < hom_nay
			and r.trang_thai not in (TT_DA_TRA, TT_TU_CHOI, TT_HUY)
			else 0
		)
		if q and q not in ((r.ma or "") + " " + (r.ten_ncc or "") + " " + (r.ghi_chu or "")).lower():
			continue
		ra.append(o)

	# GHEP PHIEU TRA TRUOC VAO CUNG DANH SACH.
	#
	# Uyen 03/09/2026: lap phieu tra truoc xong thi tren app khong thay no o
	# dau. Dung vay: phieu tra truoc la Payment Entry, con vong lap tren chi
	# doc bang "Vagabond Ho So TT". Man Duyet phieu chi co thay, nhung man do
	# chia tab theo VAI nen nguoi lap khong mang vai duyet la khong thay buoc
	# nao. Ghep vao day de phieu quay ve dung cho nguoi ta di tim.
	#
	# Chi ghep khi nguoi dung dang xem "tat ca" hoac dang loc dung chip tra
	# truoc. Hong thi bo qua chu khong lam chet ca man: danh sach ho so that
	# quan trong hon cai cua so nhin them nay.
	if not loai or loai == LOAI_TRA_TRUOC:
		try:
			from vagabond import tra_truoc as tt

			for o in tt.gom_phieu(so_ngay=so_ngay, tu=tu, den=den, tu_khoa=tu_khoa):
				if ncc and o.get("nha_cung_cap") != ncc:
					continue
				o["nhan"] = NHAN.get(o["trang_thai"], o["trang_thai"])
				o["nhan_cp_thue"] = ""
				o["nguoi_tao_ten"] = _ten_nguoi(o.get("nguoi_tao"))
				o["fin_ten"] = ""
				o["gd_ten"] = ""
				ra.append(o)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ho_so_tt: ghep phieu tra truoc loi")
		ra.sort(key=lambda o: str(o.get("ngay") or ""), reverse=True)

	dem, tien = {}, {}
	for o in ra:
		dem[o["trang_thai"]] = dem.get(o["trang_thai"], 0) + 1
		tien[o["trang_thai"]] = tien.get(o["trang_thai"], 0) + flt(o["tong_tien"])
	# Chi bay chip cho nhung tai khoan CO THAT trong ky dang xem. Bay ca danh
	# muc ngan hang thi phan lon chip bam vao ra rong.
	tk_co = []
	for o in ra:
		t = (o.get("tk_chi") or "").strip()
		if t and t not in tk_co:
			tk_co.append(t)
	tk_co.sort()

	loc_ra = [o for o in ra if o["trang_thai"] == trang_thai] if trang_thai else ra
	if tk_chi:
		loc_ra = [o for o in loc_ra if (o.get("tk_chi") or "") == tk_chi]
	return {
		"rows": loc_ra,
		"tong_dong": len(loc_ra),
		"tong_tien": sum(flt(o["tong_tien"]) for o in loc_ra),
		"tat_ca": len(ra),
		"dem": dem,
		"tien": tien,
		"trang_thai_co": THU_TU,
		"tk_chi_co": tk_co,
		"nhan": NHAN,
		"quyen": {
			"lap": 1 if (VAI_LAP & _vai()) else 0,
			"fin": 1 if (VAI_FIN & _vai()) else 0,
			"gd": 1 if (VAI_GD & _vai()) else 0,
		},
	}


def _truong_hddt_pi():
	"""Những cột trên Hoá đơn mua đang giữ thông tin hoá đơn điện tử.

	Dò theo meta chứ không viết cứng tên cột: các trường này do bên m-invoice
	sinh ra, đặt cứng thì hôm nào đội kia đổi tên là màn hình trống trơn mà
	không ai biết vì sao.
	"""
	ra = []
	try:
		meta = frappe.get_meta("Purchase Invoice")
	except Exception:
		return ra
	for f in meta.fields:
		ten = (f.fieldname or "").lower()
		if f.fieldtype in ("Section Break", "Column Break", "Tab Break", "HTML"):
			continue
		if "hddt" in ten or "minvoice" in ten or "m_invoice" in ten or "hoa_don_dien_tu" in ten:
			ra.append((f.fieldname, f.label or f.fieldname))
	return ra


def _da_ghi_so(doctype, ten_ds):
	"""Lọc lấy những chứng từ ĐÃ GHI SỔ (docstatus = 1), giữ nguyên thứ tự.

	Nháp (0) và đã huỷ (2) đều bị loại. Hàm gọn để ca kiểm gọi thẳng.
	"""
	if not ten_ds:
		return []
	try:
		ok = {
			r["name"]
			for r in frappe.get_all(
				doctype,
				filters={"name": ["in", list(ten_ds)], "docstatus": 1},
				fields=["name"],
				limit_page_length=0,
			)
		}
	except Exception:
		return list(ten_ds)
	return [x for x in ten_ds if x in ok]


def _ho_so_chung_tu(ten_pi):
	"""Đơn mua hàng, phiếu nhập kho và bản scan gắn với một hoá đơn mua.

	Anh Việt 13/08/2026: "trong APP cũng chưa thấy hiển thị PO và Phiếu Nhập
	kho, bản scan chứng từ nhập kho của bên Kiên đính kèm vào".
	"""
	po, pnk = [], []
	try:
		for r in frappe.get_all(
			"Purchase Invoice Item",
			filters={"parent": ten_pi},
			fields=["purchase_order", "purchase_receipt"],
			limit_page_length=0,
		):
			if r.purchase_order and r.purchase_order not in po:
				po.append(r.purchase_order)
			if r.purchase_receipt and r.purchase_receipt not in pnk:
				pnk.append(r.purchase_receipt)
	except Exception:
		pass

	# CHI LAY CHUNG TU DA GHI SO (docstatus = 1).
	#
	# Anh Viet 23/08/2026: *"he thong dang keo/noi nham ban in PNK Nhap (ban
	# cho kiem dem, khong co so thuc nhan)"*.
	#
	# Da doi chieu tren site: rieng ho so APP.26.08.011 thi PNK-2026-00054
	# dang docstatus 1, so thuc nhan day du, va to giay trong bo ho so la ANH
	# SCAN kho dinh kem chu khong phai ban in may sinh ra. Nghia la ca do
	# khong phai do doan nay.
	#
	# Nhung van chot lai, vi hien tai KHONG co bo loc nao ca: mot phieu nhap
	# con nhap ma lot vao day thi bo ho so mang so luong chua kiem dem di
	# duyet chi tien. Doc chung tu da huy (docstatus 2) cung vay. Chan o day
	# re hon nhieu so voi phat hien sau khi tien da chuyen.
	po = _da_ghi_so("Purchase Order", po)
	pnk = _da_ghi_so("Purchase Receipt", pnk)
	scan = _dinh_kem([("Purchase Invoice", ten_pi)]
		+ [("Purchase Order", x) for x in po]
		+ [("Purchase Receipt", x) for x in pnk])
	return {"po": po, "pnk": pnk, "scan": scan}


def _unc_cho_man(name):
	"""Danh sách uỷ nhiệm chi của hồ sơ, dạng màn hình đọc được."""
	from vagabond.tra_tien_app import ds_unc_tho

	ra = []
	try:
		for f in ds_unc_tho(name):
			ra.append({
				"file": f.name, "ten": f.file_name or f.name,
				"url": f.file_url or "", "co": cint(f.file_size),
			})
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: doc danh sach UNC")
	return ra


def _dinh_kem(cap):
	"""File đính kèm của một loạt chứng từ, gộp lại thành một danh sách."""
	ra = []
	for dt, dn in cap:
		try:
			for f in frappe.get_all(
				"File",
				filters={"attached_to_doctype": dt, "attached_to_name": dn},
				fields=["name", "file_name", "file_url", "is_private", "file_size"],
				limit_page_length=0,
			):
				ra.append({
					"file": f.name, "ten": f.file_name or f.name,
					"url": f.file_url or "", "rieng": cint(f.is_private),
					"co": cint(f.file_size), "tu": "%s %s" % (dt, dn),
				})
		except Exception:
			continue
	return ra


@frappe.whitelist()
def chi_tiet(name):
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem hồ sơ thanh toán")
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	truong_hddt = _truong_hddt_pi()
	dong = []
	for d in doc.dong:
		o = {
			"hoa_don": d.hoa_don or "", "so_hd_ncc": d.so_hd_ncc or "",
			"ngay_hd": str(d.ngay_hd or ""), "han_tra": str(d.han_tra or ""),
			"tong_hd": flt(d.tong_hd), "con_no_luc_lap": flt(d.con_no),
			"con_no_hien_tai": 0.0, "so_tien": flt(d.so_tien),
			"noi_dung": d.noi_dung or "", "ben_ban": d.ben_ban or "",
			"loai_chi": d.loai_chi or "", "co_vat": cint(d.co_vat),
			"ma_giao_dich": d.ma_giao_dich or "",
			"tk_no": d.tk_no or "", "tk_co": d.tk_co or "",
			"ghi_chu": d.ghi_chu or "",
			"po": [], "pnk": [], "scan": [], "hddt": [],
			"ncc_hd": "", "trang_thai_hd": "",
			# Chung tu cua rieng dong nay (v278). `tep_dong` tach khoi `scan`
			# la co y: `scan` la giay to keo theo tu hoa don mua, con day la
			# thu nguoi lap tu dinh vao khoan chi. Tron hai thu vao nhau thi
			# ban in khong con noi duoc anh nao tu dau ra.
			"loai_chung_tu": d.get("loai_chung_tu") or "",
			"de_nghi_chi": d.get("de_nghi_chi") or "",
			"tep_dong": _ho_tep(_tep_cua_dong(d.get("tep"))),
		}
		if d.hoa_don:
			hd = frappe.db.get_value(
				"Purchase Invoice", d.hoa_don,
				["outstanding_amount", "grand_total", "supplier_name", "status", "bill_no", "bill_date"],
				as_dict=True,
			) or {}
			o["con_no_hien_tai"] = flt(hd.get("outstanding_amount"))
			o["ncc_hd"] = hd.get("supplier_name") or ""
			o["trang_thai_hd"] = hd.get("status") or ""
			if hd.get("bill_no") and not o["so_hd_ncc"]:
				o["so_hd_ncc"] = hd.get("bill_no")
			if hd.get("bill_date") and not o["ngay_hd"]:
				o["ngay_hd"] = str(hd.get("bill_date"))
			if truong_hddt:
				gt = frappe.db.get_value(
					"Purchase Invoice", d.hoa_don, [t[0] for t in truong_hddt], as_dict=True
				) or {}
				for ten_truong, nhan_truong in truong_hddt:
					v = gt.get(ten_truong)
					if v not in (None, "", 0):
						o["hddt"].append({"nhan": nhan_truong, "gia_tri": str(v)})
			ct = _ho_so_chung_tu(d.hoa_don)
			o["po"], o["pnk"], o["scan"] = ct["po"], ct["pnk"], ct["scan"]
		dong.append(o)

	return {
		"ho_so": {
			"ma": doc.name, "loai": doc.loai or "NCC", "ngay": str(doc.ngay or ""),
			"loai_cp_thue": doc.loai_cp_thue or "",
			"nhan_cp_thue": NHAN_CP_THUE.get(doc.loai_cp_thue, ""),
			"tk_chi": doc.tk_chi or "",
			"loai_chung_tu": doc.loai_chung_tu or "",
			"tep_dinh_kem": [
				{"ten": f.file_name or "", "url": f.file_url or ""}
				for f in frappe.get_all(
					"File",
					filters={"attached_to_doctype": "Vagabond Ho So TT", "attached_to_name": doc.name},
					fields=["file_name", "file_url"], limit_page_length=0,
				)
			],
			"ncc": doc.nha_cung_cap, "ten_ncc": doc.ten_ncc,
			"nguoi_ung": doc.get("nguoi_ung") or "",
			"ten_nguoi_ung": doc.get("ten_nguoi_ung") or "",
			# So nha cung cap that su co mat trong ho so. Doc lai tu cac dong
			# chu khong tin o o da luu: ho so cu lap truoc 19/08/2026 chua co
			# o nay, va man hinh van phai hien dung.
			"so_ncc": len({((d.get("ben_ban") or d.get("ncc_hd") or "").strip()) for d in dong
			               if (d.get("ben_ban") or d.get("ncc_hd") or "").strip()}),
			"email_ncc": doc.email_ncc or "",
			"trang_thai": doc.trang_thai, "nhan": NHAN.get(doc.trang_thai, doc.trang_thai),
			"tong_tien": flt(doc.tong_tien), "da_tra": flt(doc.da_tra),
			"da_tam_ung": flt(doc.da_tam_ung), "con_lai": flt(doc.con_lai) or flt(doc.tong_tien),
			"han_tra_som_nhat": str(doc.han_tra_som_nhat or ""),
			"nguoi_tao": doc.nguoi_tao, "nguoi_tao_ten": _ten_nguoi(doc.nguoi_tao),
			"fin_boi": doc.fin_boi, "fin_ten": _ten_nguoi(doc.fin_boi),
			"fin_luc": str(doc.fin_luc or ""),
			"gd_boi": doc.gd_boi, "gd_ten": _ten_nguoi(doc.gd_boi),
			"gd_luc": str(doc.gd_luc or ""), "ly_do_tu_choi": doc.ly_do_tu_choi or "",
			"ngay_thanh_toan": str(doc.ngay_thanh_toan or ""),
			"ma_giao_dich": doc.ma_giao_dich or "", "phuong_thuc": doc.phuong_thuc or "",
			"ten_nhan": doc.ten_nhan or "", "stk_nhan": doc.stk_nhan or "",
			"ngan_hang_nhan": doc.ngan_hang_nhan or "",
			# Chua ai bam nut sinh noi dung thi TU SINH tai cho, dung de ban
			# in ra dong "..............." roi ke toan go tay moi lan.
			#
			# Chi tinh de HIEN, khong ghi xuong co so du lieu o day: ham nay
			# la ham DOC, mot ham doc ma lang le ghi thi kho lan ra khi so
			# lieu sai. Nut "Sinh noi dung chuyen khoan" van la cho ghi.
			"noi_dung_ck": doc.noi_dung_ck or _noi_dung_ck(doc),
			"email_da_gui": cint(doc.email_da_gui),
			"email_gui_luc": str(doc.email_gui_luc or ""),
			"email_gui_toi": doc.email_gui_toi or "",
			"ghi_chu": doc.ghi_chu or "",
		},
		"dong": dong,
		"ho_so_dinh_kem": _dinh_kem([("Vagabond Ho So TT", doc.name)]),
		# UY NHIEM CHI tach thanh khoi rieng tren man hinh, nhung VAN nam
		# trong `ho_so_dinh_kem` de bo ho so xuat ra co day du giay to. Man
		# hinh tu loc trung.
		"unc": _unc_cho_man(doc.name),
		"unc_go_duoc": 1 if doc.trang_thai in TT_GO_DUOC_UNC_MAN else 0,
		"quyen": {
			"lap": 1 if (VAI_LAP & _vai()) else 0,
			"fin": 1 if (VAI_FIN & _vai()) else 0,
			"gd": 1 if (VAI_GD & _vai()) else 0,
		},
		"nhan": NHAN,
	}


# -------------------------------------------------------------------- duyệt


@frappe.whitelist()
def dinh_tep(name=None, tep=None):
	"""Dinh tep vao ho so: ban the hien hoa don, bang ke, giay to kem theo.

	Vi sao lam duong nay thay vi keo PDF tu M-Invoice (anh Viet chot
	21/08/2026: *"Phan ban the hien hoa don chac thoi khoi keo api... Em cho
	nut tai len luc lam APP la duoc roi"*): duong API cua M-Invoice tra 400
	o moi bien the ten tep da thu, va cho mot cai khong chac ay thi ke toan
	truong van khong co gi de duyet. Nguoi lap ho so mo M-Invoice bam tai
	ve, roi dinh len day - mot thao tac, chac chan.

	Tep da nam san tren may chu (man hinh tai len truoc bang upload_file),
	o day chi doi con tro `attached_to` cho no thuoc ve ho so. Dung
	db.set_value chu khong save: File co validate rieng, ma o day khong dung
	den noi dung tep.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "đính tệp vào hồ sơ")
	if not frappe.db.exists("Vagabond Ho So TT", name):
		frappe.throw("Không tìm thấy hồ sơ %s. Vui lòng quay lại danh sách rồi mở lại." % name)
	tt = frappe.db.get_value("Vagabond Ho So TT", name, "trang_thai")
	if tt in (TT_HUY, TT_TU_CHOI):
		frappe.throw(
			"Hồ sơ %s đã %s nên không đính thêm giấy tờ được. Lập hồ sơ mới "
			"nếu vẫn cần thanh toán." % (name, NHAN.get(tt, tt).lower())
		)
	if isinstance(tep, str):
		try:
			tep = frappe.parse_json(tep)
		except Exception:
			tep = [tep]
	if isinstance(tep, dict):
		tep = [tep]
	if not tep:
		frappe.throw("Chưa chọn tệp nào. Vui lòng bấm nút chọn tệp rồi thử lại.")
	da_gan = 0
	for t in tep:
		ma_tep = t.get("ma") if isinstance(t, dict) else t
		if not ma_tep or not frappe.db.exists("File", ma_tep):
			continue
		frappe.db.set_value("File", ma_tep, {
			"attached_to_doctype": "Vagabond Ho So TT",
			"attached_to_name": name,
			"is_private": 1,
		}, update_modified=False)
		da_gan += 1
	if not da_gan:
		frappe.throw(
			"Tệp gửi lên không còn trên máy chủ. Vui lòng chọn tệp rồi bấm đính lại."
		)
	try:
		frappe.get_doc("Vagabond Ho So TT", name).add_comment(
			"Comment", "Đính thêm %d tệp chứng từ vào hồ sơ." % da_gan
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: ghi vet dinh tep")
	frappe.db.commit()
	return {
		"ok": 1, "da_gan": da_gan,
		"tep": _dinh_kem([("Vagabond Ho So TT", name)]),
		"ghi_chu": "Đã đính %d tệp vào hồ sơ %s." % (da_gan, name),
	}


@frappe.whitelist()
def go_tep(name=None, tep=None):
	"""Go mot tep dinh nham khoi ho so. KHONG xoa tep, chi bo lien ket."""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "gỡ tệp khỏi hồ sơ")
	if not frappe.db.exists("Vagabond Ho So TT", name):
		frappe.throw("Không tìm thấy hồ sơ %s." % name)
	f = frappe.db.get_value(
		"File", {"name": tep, "attached_to_doctype": "Vagabond Ho So TT", "attached_to_name": name},
		["name", "file_name"], as_dict=True,
	)
	if not f:
		frappe.throw("Tệp này không nằm trên hồ sơ %s. Vui lòng tải lại trang." % name)
	frappe.db.set_value("File", f.name, {
		"attached_to_doctype": None, "attached_to_name": None,
	}, update_modified=False)
	try:
		frappe.get_doc("Vagabond Ho So TT", name).add_comment("Comment", "Gỡ tệp %s khỏi hồ sơ." % (f.file_name or f.name))
	except Exception:
		pass
	frappe.db.commit()
	return {"ok": 1, "tep": _dinh_kem([("Vagabond Ho So TT", name)])}


def _hoa_don_da_sinh(doc):
	"""Các hoá đơn mua ĐÃ GHI SỔ mà chính hồ sơ này sinh ra. THUẦN đọc."""
	ra = []
	for d in (doc.dong or []):
		ma = (getattr(d, "hoa_don", "") or "").strip()
		if not ma:
			continue
		try:
			if cint(frappe.db.get_value("Purchase Invoice", ma, "docstatus")) == 1:
				ra.append(ma)
		except Exception:
			continue
	return sorted(set(ra))


def _chan_giet_ho_so_da_sinh_hoa_don(doc, viec):
	"""Hồ sơ đã sinh hoá đơn mua ghi sổ thì không Từ chối hay Huỷ suông được.

	Bước giám đốc duyệt của luồng hoàn ứng gọi `_sinh_hoa_don_hoan_ung`, hàm
	đó lập VÀ ghi sổ Purchase Invoice thật. Trước 04/09/2026, sau đó bấm Từ
	chối hay Huỷ thì hồ sơ đổi trạng thái còn hoá đơn vẫn nằm nguyên trên sổ,
	công nợ nhà cung cấp treo lại mà không còn chứng từ nào giải thích. Nhìn
	trên app thì tờ đã chết, nhìn trên sổ thì tiền vẫn đang nợ.

	KHÔNG tự huỷ hoá đơn hộ. Huỷ một chứng từ đã ghi sổ là việc động vào sổ
	cái, anh Việt chốt 13/08/2026 là không tự quyết. Nên chặn lại và chỉ rõ
	thứ tự đúng: kế toán huỷ hoá đơn trước, rồi mới huỷ hồ sơ.
	"""
	hd = _hoa_don_da_sinh(doc)
	if not hd:
		return
	frappe.throw(
		"Hồ sơ %s đã sinh %d hoá đơn mua ĐÃ GHI SỔ: %s.\n\n"
		"%s hồ sơ bây giờ thì hoá đơn vẫn nằm trên sổ và công nợ treo lại, "
		"không còn chứng từ nào giải thích.\n\n"
		"Thứ tự đúng: nhờ kế toán huỷ những hoá đơn đó bên Next trước, "
		"rồi quay lại %s hồ sơ này."
		% (doc.name, len(hd), ", ".join(hd), viec, viec.lower()),
		title="Còn hoá đơn đã ghi sổ",
	)


def _nha_het_phieu_noi_bo(doc):
	"""Hồ sơ chết thì trả mọi phiếu nội bộ của nó về trạng thái chưa nối.

	Từ chối và Huỷ là hai cửa tử của một hồ sơ. Trước 04/09/2026 hai cửa
	này chỉ đổi `trang_thai` rồi thôi, phiếu nội bộ vẫn mang mã một hồ sơ đã
	chết. Mà `ds_phieu_noi_bo` lọc bỏ mọi phiếu đã có hồ sơ, `xem_phieu_noi_bo`
	thì ném lỗi "đã nối vào hồ sơ ... rồi". Riêng hồ sơ Huỷ còn không xoá dòng
	được nữa (`_kiem_sua_duoc_ruot` chỉ cho Nháp và Từ chối), nên phiếu KẸT
	VĨNH VIỄN: tiền quản lý đã ứng không bao giờ hoàn được qua máy nữa.

	Cùng đúng cái lý lẽ mà `_chan_hoa_don_trung` đã ghi từ lâu: hồ sơ Từ chối
	và Huỷ không được giữ chỗ, thứ trong đó phải dùng lại được, nếu không thì
	một lần lập nhầm là kẹt vĩnh viễn. Nay áp nốt cho phiếu nội bộ.
	"""
	for d in (doc.dong or []):
		ma = (getattr(d, "de_nghi_chi", "") or "").strip()
		if not ma:
			continue
		try:
			if frappe.db.get_value(DNC, ma, "ho_so_tt") == doc.name:
				frappe.db.set_value(DNC, ma, "ho_so_tt", None, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ho_so_tt: nha phieu noi bo khi ho so chet")


@frappe.whitelist()
def duyet(name, buoc, ly_do=""):
	"""buoc: gui_fin / fin / gd / tu_choi / huy.

	Duyệt phải đúng thứ tự: kế toán trước, giám đốc sau. Người lập không
	tự duyệt hồ sơ của chính mình - đó là cả điểm của việc duyệt hai cấp.
	"""
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	toi = frappe.session.user
	buoc = (buoc or "").strip()

	if buoc == "gui_fin":
		_kiem(VAI_LAP, "gửi hồ sơ đi duyệt")
		if doc.trang_thai not in (TT_NHAP, TT_TU_CHOI):
			frappe.throw("Hồ sơ đang ở trạng thái %s, không gửi lại được." % NHAN.get(doc.trang_thai))
		# Hang rao TAI KHOAN NHAN TIEN, chan ngay o cua gui di duyet.
		# Ho so hoan ung khong co so tai khoan thi ca day duyet phia sau
		# deu vo nghia: den luc chuyen tien khong ai biet chuyen di dau, ma
		# luc do thi ho so da qua hai cap ky roi, tra ve rat mat cong. Chan
		# theo SO TAI KHOAN chu khong theo link, de ho so cu chi go tay ba o
		# van di duoc.
		if (doc.loai or LOAI_NCC) in (LOAI_HU, LOAI_HU_HD) and not (doc.stk_nhan or "").strip():
			frappe.throw(
				"Hồ sơ %s chưa có tài khoản nhận tiền. Bấm nút Chọn TK nhận "
				"trên hồ sơ để chọn đúng ngân hàng của người được hoàn ứng, "
				"rồi gửi lại." % doc.name
			)
		doc.trang_thai = _buoc_ke_tiep_khi_gui()
		doc.ly_do_tu_choi = ""
		# Nhay thang len giam doc thi phai ghi ro AI da dam nhiem cap ke toan,
		# khong thi to trinh ky trong ra nhu chua qua kiem soat nao.
		if doc.trang_thai == TT_CHO_GD and not doc.fin_boi:
			doc.fin_boi = toi
			doc.fin_luc = now_datetime()

	elif buoc == "fin":
		_kiem(VAI_FIN, "duyệt hồ sơ ở cấp kế toán")
		if doc.trang_thai != TT_CHO_FIN:
			frappe.throw("Hồ sơ đang ở %s, chưa tới lượt kế toán duyệt." % NHAN.get(doc.trang_thai))
		if doc.nguoi_tao == toi and "System Manager" not in _vai():
			frappe.throw("Người lập hồ sơ không tự duyệt được, nhờ người khác duyệt giúp.")
		doc.trang_thai = TT_CHO_GD
		doc.fin_boi = toi
		doc.fin_luc = now_datetime()

	elif buoc == "gd":
		_kiem(VAI_GD, "duyệt hồ sơ ở cấp giám đốc")
		if doc.trang_thai != TT_CHO_GD:
			frappe.throw("Hồ sơ đang ở %s, chưa tới lượt giám đốc duyệt." % NHAN.get(doc.trang_thai))
		# HAI CHOT NAY CAP KE TOAN CO TU LAU, CAP GIAM DOC THI KHONG.
		#
		# Mot tai khoan mang ca vai ke toan lan vai giam doc thi: tu lap ho
		# so, bam Gui, `_buoc_ke_tiep_khi_gui` thay co vai ke toan nen nhay
		# thang len "Cho giam doc" va ghi luon `fin_boi` la chinh nguoi do,
		# roi nguoi do bam Duyet cap giam doc. Ho so sang "Da duyet" voi hai
		# chu ky cung mot cai ten. Ghi chu dau tep noi la da bit lo nay,
		# nhung moi bit o phia VAI chu chua bit o phia NGUOI.
		if doc.nguoi_tao == toi and "System Manager" not in _vai():
			frappe.throw("Người lập hồ sơ không tự duyệt được, nhờ người khác duyệt giúp.")
		if (doc.fin_boi or "") == toi and "System Manager" not in _vai():
			frappe.throw(
				"Bạn đã ký ở cấp kế toán cho hồ sơ này rồi. "
				"Hai cấp duyệt phải là hai người khác nhau."
			)
		# Ho so hoan ung: den day moi sinh hoa don mua that. Dat TRUOC khi
		# doi trang thai - ham nem loi thi ho so con nguyen o buoc cho giam
		# doc, khong co gi nua voi nua chin.
		if (doc.loai or LOAI_NCC) == LOAI_HU:
			_sinh_hoa_don_hoan_ung(doc)
			doc.reload()
		doc.trang_thai = TT_DA_DUYET
		doc.gd_boi = toi
		doc.gd_luc = now_datetime()

	elif buoc == "tu_choi":
		_kiem(VAI_FIN | VAI_GD, "từ chối hồ sơ")
		if not (ly_do or "").strip():
			frappe.throw("Từ chối thì phải ghi lý do, để người lập còn biết sửa gì.")
		if doc.trang_thai in (TT_DA_TRA, TT_HUY):
			frappe.throw("Hồ sơ đã %s, không từ chối được nữa." % NHAN.get(doc.trang_thai))
		_chan_giet_ho_so_da_sinh_hoa_don(doc, "Từ chối")
		doc.trang_thai = TT_TU_CHOI
		doc.ly_do_tu_choi = ly_do.strip()
		_nha_het_phieu_noi_bo(doc)

	elif buoc == "huy":
		_kiem(VAI_LAP, "huỷ hồ sơ")
		if doc.trang_thai == TT_DA_TRA:
			frappe.throw("Hồ sơ đã thanh toán rồi, không huỷ được.")
		_chan_giet_ho_so_da_sinh_hoa_don(doc, "Huỷ")
		doc.trang_thai = TT_HUY
		doc.ly_do_tu_choi = (ly_do or "").strip()
		_nha_het_phieu_noi_bo(doc)

	else:
		frappe.throw("Bước duyệt không hợp lệ: %s." % buoc)

	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	_ghi_vet(doc.name, "%s bởi %s%s" % (buoc, toi, (" - " + ly_do) if ly_do else ""))
	return {"ok": 1, "trang_thai": doc.trang_thai, "nhan": NHAN.get(doc.trang_thai)}


def _ghi_vet(name, viec):
	try:
		frappe.get_doc({
			"doctype": "Comment", "comment_type": "Info",
			"reference_doctype": "Vagabond Ho So TT", "reference_name": name,
			"content": viec,
		}).insert(ignore_permissions=True)
	except Exception:
		pass


# ------------------------------------------------------- SePay và clear công nợ


def _sepay_theo_ma_app(ds_ma):
	"""Giao dịch NGÂN HÀNG CHI RA có mã hồ sơ trong nội dung.

	Khác chiều với công nợ phải thu: ở đây tiền ĐI RA, nên lấy withdrawal
	trừ deposit. Kế toán chuyển khoản với nội dung chứa mã APPxxxxxx thì
	SePay đẩy về Bank Transaction, máy tự khớp.
	"""
	# So tren ban DA BO dau cham: ngan hang hay cat bot dau khi day noi dung
	# di, "APP.26.08.027" ve toi SePay co the thanh "APP2608027" hay
	# "APP 26 08 027". Truy van SQL vi vay chi loc tho theo "APP" roi doi
	# chieu chinh xac bang Python.
	tran = {}
	for m in ds_ma or []:
		g = RE_MA_APP.fullmatch(str(m or "").strip().upper()) or RE_MA_TRAN.fullmatch(_tran(m))
		if g:
			tran["APP" + "".join(g.groups())] = str(m).strip()
	if not tran:
		return {}
	try:
		gds = frappe.db.sql(
			"""select description, deposit, withdrawal, reference_number, date
			from `tabBank Transaction`
			where docstatus < 2 and description like %s""",
			("%APP%",), as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: doc SePay theo ma ho so")
		return {}
	ra = {}
	for g in gds:
		for k in RE_MA_TRAN.findall(_tran(g.get("description"))):
			khoa = "APP" + "".join(k)
			ten = tran.get(khoa)
			if not ten:
				continue
			o = ra.setdefault(ten, {"chi": 0.0, "so_gd": 0, "ma_gd": "", "ngay": None})
			o["chi"] += flt(g.get("withdrawal")) - flt(g.get("deposit"))
			o["so_gd"] += 1
			if not o["ma_gd"]:
				o["ma_gd"] = (g.get("reference_number") or "").strip()
			if not o["ngay"]:
				o["ngay"] = str(g.get("date") or "")
	return ra


@frappe.whitelist()
def kiem_sepay(name=None):
	"""Dò SePay xem hồ sơ đã chuyển tiền chưa. Không ghi gì, chỉ xem."""
	_kiem(VAI_FIN, "đối chiếu SePay")
	if name:
		ds = [frappe.db.get_value("Vagabond Ho So TT", name, ["name", "tong_tien", "con_lai", "trang_thai"], as_dict=True)]
	else:
		ds = frappe.get_all(
			"Vagabond Ho So TT",
			filters={"trang_thai": TT_DA_DUYET},
			fields=["name", "tong_tien", "con_lai", "trang_thai"],
			limit_page_length=0,
		)
	ds = [d for d in ds if d]
	g = _sepay_theo_ma_app([d["name"] for d in ds])
	ra = []
	for d in ds:
		o = g.get(d["name"]) or {}
		# SO VOI SO THAT SU CHUYEN DI, khong phai tong tien.
		#
		# Ho so co tru tam ung thi tien ngan hang chuyen di la `con_lai`, va
		# ban in cung ghi ro "CON LAI PHAI CHUYEN". So voi `tong_tien` thi
		# moi ho so co tru tam ung se VINH VIEN bao "chua du tien" du ngan
		# hang da chuyen dung, va ke toan de tuong tien chua di.
		phai_chuyen = flt(d.get("con_lai")) or flt(d["tong_tien"])
		ra.append({
			"ma": d["name"], "tong_tien": flt(d["tong_tien"]),
			"phai_chuyen": phai_chuyen,
			"da_chi": flt(o.get("chi")), "so_gd": o.get("so_gd") or 0,
			"ma_gd": o.get("ma_gd") or "", "ngay": o.get("ngay") or "",
			"du": 1 if flt(o.get("chi")) >= phai_chuyen - 1 else 0,
		})
	return {"rows": ra, "so_du": len([x for x in ra if x["du"]])}


@frappe.whitelist()
def danh_dau_da_tra(name, ngay=None, ma_giao_dich=None, phuong_thuc="Chuyển khoản", tao_but_toan=1, gui_thu=1, ly_do_som=None):
	"""Ghi nhận đã chuyển tiền, và sinh Payment Entry để clear công nợ.

	Bút toán mới là thứ thật sự xoá nợ trên sổ; hồ sơ chỉ là chứng từ đề
	nghị. Nếu ERPNext từ chối bút toán thì hồ sơ vẫn ở Đã duyệt để kế toán
	xử tay, KHÔNG đánh dấu đã trả - đánh dấu mà nợ vẫn treo là tệ hơn.
	"""
	from vagabond.tra_tien_app import dem_unc, du_unc, loi_thieu_unc

	_kiem(VAI_FIN, "ghi nhận thanh toán")
	# KHOA BAN GHI TRUOC KHI DOC TRANG THAI.
	#
	# Ham nay doc trang thai roi moi ghi, va o giua co `_tao_but_toan` tu
	# `frappe.db.commit()`. Khong khoa thi hai lan bam chong nhau (mang chap
	# chon, nguoi dung bam lai) deu doc thay "Da duyet" o cung mot luc, roi
	# ca hai cung sinh Payment Entry. Cong ty ghi so tra tien hai lan cho
	# mot ho so, ma tren man hinh nhin chi thay mot dong "Da thanh toan".
	#
	# `for_update` bat MySQL giu dong lai: lan bam thu hai dung o day cho
	# lan thu nhat xong, doc lai thay "Da thanh toan" va thoat ngay o cau
	# duoi. Phai khoa TRUOC `get_doc`, khoa sau thi da doc so cu roi.
	try:
		frappe.db.get_value("Vagabond Ho So TT", name, "trang_thai", for_update=True)
	except Exception:
		# Bo may du lieu khong cho khoa thi van chay tiep: chot `da_lam_roi`
		# ben duoi con do duoc phan lon truong hop, tha yeu con hon chet.
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: khong khoa duoc ho so khi ghi nhan")
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	if doc.trang_thai == TT_DA_TRA:
		return {"ok": 1, "da_lam_roi": 1, "trang_thai": doc.trang_thai}
	if doc.trang_thai != TT_DA_DUYET:
		frappe.throw(
			"Hồ sơ đang ở %s. Phải duyệt xong hai cấp mới chuyển tiền được."
			% NHAN.get(doc.trang_thai, doc.trang_thai)
		)
	# UY NHIEM CHI TRUOC, GHI NHAN SAU. Anh Viet chot 28/08/2026, ap cho
	# MOI loai ho so. Chan o day chu khong chi chan luc ghi so but toan:
	# chan o but toan thi ho so da doi trang thai xong roi moi hong, va
	# nguoi bam tren app khong co cho nao de dinh tep.
	if not du_unc(dem_unc(doc.name)):
		frappe.throw(loi_thieu_unc(doc.name), title="Chưa có uỷ nhiệm chi")

	# GIAO DICH NGAN HANG PHAI VE. Anh Viet 03/09/2026: *"ke toan chi tien
	# roi dinh kem UNC, khop giao dich SePay vao thi moi ghi so va chuyen
	# trang thai da thanh toan"*.
	#
	# To uy nhiem chi la lenh chuyen tien, khong phai bang chung tien da ra
	# khoi tai khoan: lenh co the bi ngan hang tu choi, co the bi go, co the
	# la anh chup cua lan chuyen truoc. Dong sao ke moi noi duoc tien da di.
	#
	# Duong thoat CO VET cho ke toan truong: chuyen lien ngan hang ngoai gio
	# thi sao ke ve cham vai tieng, ma tien da di that. Khong co duong nay
	# thi den luc ket nguoi ta se vong qua ca he thong, va vong qua thi
	# khong con vet nao het.
	from vagabond import duyet_chi

	ly_do = (ly_do_som or "").strip()
	da_chi = flt((_sepay_theo_ma_app([doc.name]).get(doc.name) or {}).get("chi"))
	# SO VOI SO THAT SU CHUYEN DI, khong phai tong tien.
	#
	# Ho so co tru tam ung thi ngan hang chi chuyen `con_lai`, va ban in
	# cung ghi ro "CON LAI PHAI CHUYEN". So voi `tong_tien` thi moi ho so co
	# tru tam ung se VINH VIEN khong ghi so duoc du ngan hang da chuyen dung
	# so, va ke toan buoc phai muon duong bo qua co ly do - tuc bien mot
	# duong thoat ngoai le thanh duong di hang ngay. Cung mot cai bay da sua
	# cho `kiem_sepay` o v413.
	phai_chuyen = flt(doc.con_lai) or flt(doc.tong_tien)
	if not duyet_chi.sepay_du(phai_chuyen, da_chi):
		if not (ly_do and (duyet_chi.VAI_BO_QUA_SEPAY & set(frappe.get_roles()))):
			frappe.throw(
				duyet_chi.cau_thieu(["chua_ve_tien"], phai_chuyen, da_chi),
				title="Chưa thấy tiền ra khỏi tài khoản",
			)
		doc.vgb_tt_ly_do_som = ly_do

	pe = None
	if cint(tao_but_toan):
		pe = _tao_but_toan(doc, ngay or nowdate(), phuong_thuc)

	doc.trang_thai = TT_DA_TRA
	doc.ngay_thanh_toan = ngay or nowdate()
	# CHI GHI DE KHI NGUOI TA THUC SU GO MA.
	#
	# Truoc 04/09/2026 dong nay ghi de vo dieu kien. Ke toan da khop tay mot
	# ma bang `gan_giao_dich`, sau do bam Ghi nhan da thanh toan ma bo trong
	# o hoi ma (man hinh cho phep bo trong) la ma cu bi xoa trang, mat luon
	# dau vet khop tay, phai do lai tu dau.
	if (ma_giao_dich or "").strip():
		doc.ma_giao_dich = ma_giao_dich.strip()
	doc.phuong_thuc = (phuong_thuc or "").strip()
	doc.da_tra = flt(doc.tong_tien)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	_ghi_vet(doc.name, "Đã thanh toán %s đ%s%s" % (
		_tien(doc.tong_tien),
		(" - bút toán " + pe) if pe else "",
		(" - ghi sổ sớm: " + ly_do) if (ly_do and not duyet_chi.sepay_du(phai_chuyen, da_chi)) else "",
	))
	# TRU TAM UNG THI SO CAI CHUA CAN BANG, PHAI NOI RA.
	#
	# But toan xoa cong no nha cung cap theo `tong_tien`, dung ve phia nha
	# cung cap. Nhung tien that ra khoi ngan hang chi la `con_lai`; phan
	# `da_tam_ung` von da ung tu quy 1411 tu truoc. Buoc bu tru 1411 hien
	# van do chi Dung lam TAY ben Next.
	#
	# Truoc 04/09/2026 khong co dong nao nhac, nen quen mot lan la quy tam
	# ung phinh ra ma khong ai truy duoc tu ho so nao. Ghi hang vet va tra
	# co ve man hinh de nguoi bam nhin thay ngay.
	nhac = ""
	if flt(doc.da_tam_ung) > 0:
		nhac = ("Hồ sơ này trừ %s đ tạm ứng. Bút toán vừa sinh xoá công nợ theo "
			"TỔNG %s đ, còn phần tạm ứng phải bù trừ tay với quỹ 1411 bên Next. "
			"Chưa bù là quỹ tạm ứng phình ra." % (_tien(doc.da_tam_ung), _tien(doc.tong_tien)))
		_ghi_vet(doc.name, nhac)
	thu = _tu_gui_thu_bao(doc, gui_thu)
	return {"ok": 1, "trang_thai": doc.trang_thai, "but_toan": pe or "", "thu": thu,
		"nhac_tam_ung": nhac}


def _tu_gui_thu_bao(doc, gui_thu=1):
	"""Tự gửi thư báo thanh toán ngay sau khi ghi nhận.

	Anh Việt 28/08/2026: thư báo phải TỰ đi, không chờ ai nhớ bấm nút.
	Nút gửi tay vẫn giữ, dùng để gửi lại hoặc gửi tới địa chỉ khác.

	Nuốt mọi lỗi: tiền đã ra khỏi tài khoản thật rồi, hồ sơ phải được ghi
	nhận xong xuôi cho dù hộp thư có trục trặc. Gửi hỏng thì trả lý do về
	màn hình để người bấm biết mà gửi tay.
	"""
	if not cint(gui_thu):
		return {"gui": 0, "vi_sao": "Không gửi thư theo yêu cầu."}
	if (doc.loai or LOAI_NCC) in (LOAI_HU, LOAI_HU_HD):
		return {"gui": 0, "vi_sao": "Hồ sơ hoàn ứng không gửi thư báo cho nhà cung cấp."}
	toi = (doc.email_ncc or "").strip()
	if not toi or "@" not in toi:
		return {
			"gui": 0,
			"vi_sao": "Nhà cung cấp %s chưa có email nên chưa gửi thư báo được."
			% (doc.ten_ncc or doc.nha_cung_cap or ""),
		}
	try:
		gui_email_ncc(doc.name, email=toi, gui_that=1)
		return {"gui": 1, "toi": toi}
	except Exception as loi:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: tu gui thu bao thanh toan")
		return {"gui": 0, "vi_sao": "Gửi thư báo chưa được: %s" % str(loi)[:200]}


def _tao_but_toan(doc, ngay, phuong_thuc):
	"""Sinh Payment Entry trả nhà cung cấp, phân bổ vào đúng từng hoá đơn.

	GOP THEO HOA DON truoc khi phan bo. Ho so hoan ung gom nhieu khoan khong
	hoa don vao MOT hoa don mua, moi khoan mot dong; de nguyen ma duyet tung
	dong thi Payment Entry co hai ba dong tro cung mot Purchase Invoice, va
	ERPNext se phan bo chong len nhau - tra 3 trieu ma so sach ghi tra 9.
	"""
	from vagabond.chung_tu_tien import dat_dien_giai
	from vagabond.tra_tien_app import chep_unc, loi_khong_ro_tk, tk_tien_chi, ty_gia_chi

	con = [d for d in doc.dong if d.hoa_don]
	# Chi tu TK cong ty co hai the: chon hoa don GTGT co that thi van la
	# Payment Entry xoa cong no nhu luong NCC; go tay khoan khong hoa don
	# thi khong co gi de xoa, ghi thang Journal Entry theo dinh khoan.
	if (doc.loai or LOAI_NCC) == LOAI_TKCT and not con:
		return _tao_but_toan_tkct(doc, ngay, phuong_thuc)

	if not con:
		frappe.throw(
			"Hồ sơ %s chưa có hoá đơn mua nào để xoá công nợ. Với hồ sơ hoàn ứng, "
			"hoá đơn được lập ở bước giám đốc duyệt." % doc.name
		)

	gom = {}
	for d in con:
		gom[d.hoa_don] = gom.get(d.hoa_don, 0.0) + flt(d.so_tien)

	# MOT BUT TOAN CHO MOI NHA CUNG CAP.
	#
	# Truoc 19/08/2026 cho nay dung mot Payment Entry duy nhat voi
	# pe.party = doc.nha_cung_cap. Dung chung nao ho so con bi chan mot nha
	# mot ho so. Tu khi ho so hoan ung gom duoc nhieu nha, mot Payment Entry
	# khong the xoa no cua hai ben khac nhau: truong party chi nhan MOT
	# nguoi, va ERPNext se tu choi cac dong tham chieu tro sang hoa don cua
	# ben khac.
	#
	# Nen gom theo NHA CUNG CAP THAT CUA TUNG HOA DON, khong doc dau ho so.
	# Dau ho so cua luong hoan ung mang ten NGUOI DUOC HOAN UNG, dung no lam
	# party la ghi no sai cua.
	theo_ncc = {}
	for ten_hd, tien in gom.items():
		hd = frappe.db.get_value(
			"Purchase Invoice", ten_hd,
			["supplier", "company", "grand_total", "outstanding_amount", "due_date"],
			as_dict=True,
		) or {}
		if not hd.get("supplier"):
			frappe.throw(
				"Hoá đơn %s không đọc được nhà cung cấp nên chưa sinh bút toán "
				"được. Nhờ kế toán mở hoá đơn đó kiểm lại." % ten_hd
			)
		o = theo_ncc.setdefault(hd["supplier"], {"cong_ty": hd.get("company"), "hd": []})
		o["hd"].append((ten_hd, tien, hd))

	ra = []
	for ma_ncc in sorted(theo_ncc):
		o = theo_ncc[ma_ncc]
		tong_nhom = sum(t for _, t, _ in o["hd"])
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Pay"
		pe.company = o["cong_ty"]
		pe.posting_date = ngay
		pe.party_type = "Supplier"
		pe.party = ma_ncc
		pe.paid_amount = flt(tong_nhom)
		pe.received_amount = flt(tong_nhom)
		pe.reference_no = doc.ma_giao_dich or doc.name
		pe.reference_date = ngay
		# Ho so tu khai ra minh la cha cua phieu nay. Day la CHO DUY NHAT
		# biet duoc mot khoan la hoan ung nhan vien hay tra nha cung cap
		# that: khoan hoan ung CO hoa don thi phieu chi lai mang ten nha
		# cung cap doc tu hoa don, khong mang ten nguoi duoc hoan ung, nen
		# nhin vao phieu khong tai nao doan ra. Xem vagabond/nghiep_vu_tien.py
		pe.vgb_ho_so_tt = doc.name
		dat_dien_giai(pe, "Thanh toán công nợ nhà cung cấp %s theo hồ sơ %s. "
			"Gồm %d hoá đơn: %s. Số tiền %s đ.%s" % (
				frappe.db.get_value("Supplier", ma_ncc, "supplier_name") or ma_ncc,
				doc.name, len(o["hd"]),
				", ".join(t for t, _x, _y in o["hd"]),
				"{:,.0f}".format(flt(tong_nhom)),
				(" Ghi chú: %s" % doc.ghi_chu) if doc.get("ghi_chu") else ""))
		if phuong_thuc and frappe.db.exists("Mode of Payment", phuong_thuc):
			pe.mode_of_payment = phuong_thuc
		for ten_hd, tien, hd in o["hd"]:
			pe.append("references", {
				"reference_doctype": "Purchase Invoice",
				"reference_name": ten_hd,
				"total_amount": flt(hd.get("grand_total")),
				"outstanding_amount": flt(hd.get("outstanding_amount")),
				"allocated_amount": min(flt(tien), flt(hd.get("outstanding_amount"))),
				"due_date": hd.get("due_date"),
			})
		# TIEN DI RA TU TAI KHOAN NAO - o bat buoc, va la cho da lam
		# chi Dung ket ngay 28/08/2026 voi cau bao "Ty gia nguon la bat
		# buoc". Truoc do chi ho so "Chi tu TK cong ty" moi dien o nay vi
		# no co o chon tren man hinh; ho so cong no nha cung cap khong co
		# o do nen bo trong, va ERPNext khong the tu doan ra.
		tk_nh, ba = tk_tien_chi(o["cong_ty"], phuong_thuc, doc.tk_chi)
		if not tk_nh:
			frappe.throw(loi_khong_ro_tk(o["cong_ty"]))
		pe.paid_from = tk_nh
		if ba:
			pe.bank_account = ba
		pe.setup_party_account_field()
		pe.set_missing_values()
		# Cung mot loai tien thi ty gia la 1. Khac loai tien thi DUNG LAI
		# chu khong dat bua: dat bua o day la ghi sai so tien len so cai.
		if not flt(pe.source_exchange_rate):
			tg = ty_gia_chi(
				pe.paid_from_account_currency
				or frappe.db.get_value("Account", tk_nh, "account_currency"),
				frappe.db.get_value("Company", o["cong_ty"], "default_currency"),
			)
			if not tg:
				frappe.throw(
					"Tài khoản chi %s không cùng loại tiền với sổ của công ty nên máy "
					"chưa dựng được bút toán. Nhờ kế toán chọn tài khoản chi bằng đồng "
					"Việt Nam, hoặc khai tỷ giá trước." % tk_nh
				)
			pe.source_exchange_rate = tg
		pe.flags.ignore_permissions = True
		pe.insert(ignore_permissions=True)
		# UY NHIEM CHI phai co mat TRUOC khi ghi so: hook
		# `chan_thieu_dinh_kem` dem tep tren chinh but toan nay.
		chep_unc(doc.name, "Payment Entry", pe.name)
		pe.submit()
		ra.append(pe.name)
	frappe.db.commit()
	return ", ".join(ra)


# --------------------------------------------------------- thư báo nhà cung cấp


@frappe.whitelist()
def gui_email_ncc(name, email=None, gui_that=1, thu_nghiem=0):
	"""Thư báo đã thanh toán kèm uỷ nhiệm chi, và đề nghị đối chiếu công nợ.

	Anh Việt 13/08/2026: "Purchasing hoặc Kế toán nhắn một cái là có thể
	gửi email thông báo được luôn". Anh mở rộng 28/08/2026: thư phải đính
	uỷ nhiệm chi, phải đề nghị nhà cung cấp đối chiếu công nợ, gửi từ hộp
	thư thu mua và gửi kèm bản sao cho kế toán.

	Vì sao gửi từ hộp THU MUA chứ không phải hộp erp: nhà cung cấp bấm Trả
	lời là thư về đúng người đang làm việc với họ. Hộp erp là hộp máy, không
	ai ngồi đọc.

	Vì sao gửi kèm bản sao cho kế toán: đối chiếu công nợ là việc của kế
	toán, mà thư đối chiếu lại đi từ thu mua. Không có bản sao thì kế toán
	không biết đã hẹn gì với nhà cung cấp.

	gui_that=0 chỉ dựng HTML để xem trước, không gửi cho ai.
	thu_nghiem=1 gửi đúng một địa chỉ để xem thử: không gửi bản sao cho ai,
	không đánh dấu hồ sơ là đã gửi thư.
	"""
	from vagabond.tra_tien_app import ds_unc_tho

	_kiem(VAI_LAP | VAI_FIN, "gửi thư báo nhà cung cấp")
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	# Ho so hoan ung: tien cong ty chuyen la chuyen cho NGUOI DA UNG, con
	# nha cung cap thi da duoc tra tien tu luc mua. Gui thu "chung toi da
	# thanh toan cong no" cho ho la bao mot viec khong xay ra, va voi ho so
	# gom nhieu nha thi con khong biet gui cho ai.
	if (doc.loai or LOAI_NCC) in (LOAI_HU, LOAI_HU_HD):
		frappe.throw(
			"Hồ sơ %s là hồ sơ hoàn ứng: tiền công ty chuyển là trả lại cho "
			"%s, còn nhà cung cấp đã được trả tiền từ lúc mua. Thư báo thanh "
			"toán chỉ dùng cho hồ sơ công nợ nhà cung cấp."
			% (doc.name, doc.ten_ncc or doc.nha_cung_cap)
		)
	# Gui THU thi khong doi ho so da tra: ca muc dich cua no la xem mat la
	# thu truoc khi no den tay nha cung cap. Thu di dung mot dia chi nguoi
	# bam tu go, khong cc ai, va tieu de mang san chu GUI THU.
	if doc.trang_thai != TT_DA_TRA and cint(gui_that) and not cint(thu_nghiem):
		frappe.throw(
			"Hồ sơ chưa ở trạng thái Đã thanh toán, gửi thư báo lúc này là "
			"báo nhầm cho nhà cung cấp. Muốn xem mặt lá thư thì bấm Gửi thử."
		)
	noi_dung = _thu_html(doc)
	if not cint(gui_that):
		return {"xem_truoc": 1, "html": noi_dung, "toi": email or doc.email_ncc or ""}

	toi = (email or doc.email_ncc or "").strip()
	if not toi or "@" not in toi:
		frappe.throw(
			"Chưa có email của nhà cung cấp %s. Anh chị điền email vào hồ sơ "
			"nhà cung cấp bên Next, hoặc gõ tay vào ô gửi tới." % (doc.ten_ncc or doc.nha_cung_cap)
		)

	thu = cint(thu_nghiem)
	dinh = _tep_dinh_thu(ds_unc_tho(doc.name))
	tieu_de = "%s%s - Thông báo thanh toán và đề nghị đối chiếu công nợ (%s)" % (
		"[GỬI THỬ] " if thu else "", TEN_TIEM, doc.name
	)
	frappe.sendmail(
		recipients=[toi],
		cc=[] if thu else [EMAIL_KE_TOAN],
		sender=EMAIL_THU_MUA,
		subject=tieu_de,
		message=noi_dung,
		attachments=dinh,
		# Gan thu vao chinh ho so: mo ho so ben Next la thay da gui gi, gui
		# luc nao, gui cho ai. Khong gan thi ban thu duy nhat nam trong hop
		# thu ca nhan cua nguoi bam nut.
		reference_doctype="Vagabond Ho So TT",
		reference_name=doc.name,
		delayed=False,
		retry=2,
	)
	if thu:
		_ghi_vet(doc.name, "Gửi thử thư báo thanh toán tới %s" % toi)
		return {"ok": 1, "toi": toi, "thu_nghiem": 1, "tep": len(dinh)}
	doc.db_set("email_da_gui", 1, update_modified=False)
	doc.db_set("email_gui_luc", now_datetime(), update_modified=False)
	doc.db_set("email_gui_toi", toi, update_modified=False)
	frappe.db.commit()
	_ghi_vet(doc.name, "Gửi thư báo thanh toán tới %s, kèm %d tệp." % (toi, len(dinh)))
	return {"ok": 1, "toi": toi, "tep": len(dinh)}


def _tep_dinh_thu(ds_tep):
	"""Đọc nội dung tệp lên để đính vào thư.

	Đính bằng NỘI DUNG chứ không bằng đường dẫn: uỷ nhiệm chi để chế độ
	riêng tư, gửi đường dẫn đi thì nhà cung cấp bấm vào chỉ thấy màn đăng
	nhập. Tệp nào đọc không được thì bỏ qua và ghi nhật ký, không làm hỏng
	cả lá thư.
	"""
	ra = []
	for f in ds_tep or []:
		try:
			tep = frappe.get_doc("File", f.name)
			ra.append({"fname": tep.file_name or f.name, "fcontent": tep.get_content()})
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ho_so_tt: doc tep dinh thu")
	return ra


def _thu_html(doc):
	"""Nội dung thư báo thanh toán. Tách riêng để xem trước được mà không gửi.

	Từ 03/09/2026 đi qua khuôn thư chung (vagabond/thu_khung.py). Bản trước
	(v369 tới v393) HỎNG: nút "Phản hồi đối chiếu" tham chiếu biến phông `mc`
	nằm ngoài phạm vi khai báo, mỗi lần bấm gửi là máy chủ ném NameError. Đây
	đúng là kiểu lỗi mà việc mỗi tệp tự dựng thư sinh ra.
	"""
	from vagabond import thu_khung as _tk

	h = _tk.h
	dong = [
		[h(d.so_hd_ncc or d.noi_dung or d.hoa_don), _ngay_vn(d.ngay_hd), _tien(d.so_tien) + " đ"]
		for d in doc.dong
	]
	bang = _tk.bang(
		[("Số hoá đơn", "left"), ("Ngày", "left"), ("Số tiền", "right")], dong,
		tong=("Tổng thanh toán", _tien(doc.tong_tien) + " đ"), goc_anh=_tk.goc_anh(),
	)

	chi_tiet_tra = [
		"Ngày thanh toán: <b>%s</b>" % _ngay_vn(doc.ngay_thanh_toan),
		"Hình thức: <b>%s</b>" % h(doc.phuong_thuc or "Chuyển khoản"),
	]
	if doc.ma_giao_dich:
		chi_tiet_tra.append("Mã giao dịch: <b>%s</b>" % h(doc.ma_giao_dich))
	if doc.noi_dung_ck:
		chi_tiet_tra.append("Nội dung chuyển khoản: <b>%s</b>" % h(doc.noi_dung_ck))
	chi_tiet_tra.append("Mã hồ sơ bên chúng tôi: <b>%s</b>" % h(doc.name))

	than = (
		_tk.doan("Kính gửi <b>%s</b>," % h(doc.ten_ncc or doc.nha_cung_cap))
		+ _tk.doan(
			"%s xin thông báo đã <b>thanh toán</b> cho quý công ty số tiền <b>%s đ</b> "
			"cho %d hoá đơn dưới đây. Uỷ nhiệm chi của giao dịch được đính kèm trong thư này."
			% (TEN_TIEM, _tien(doc.tong_tien), len(doc.dong))
		)
		+ bang
		+ _tk.nhan_hoa("Thông tin thanh toán")
		+ _tk.o_kem("<br>".join(chi_tiet_tra), goc_anh=_tk.goc_anh())
		+ _o_doi_chieu()
		+ _tk.doan("Trân trọng cảm ơn quý công ty đã đồng hành cùng chúng tôi.", cach=0)
	)
	return _tk.khung(
		"Thông báo thanh toán và đề nghị đối chiếu công nợ", than,
		nut_html=_nut_doi_chieu(doc), chan="ncc", nhan="Thanh toán công nợ",
	)


def _o_doi_chieu():
	"""Khối đề nghị đối chiếu công nợ, viền robin egg cho nổi khỏi phần trên.

	Nói rõ ba việc mong nhà cung cấp làm và một mốc thời gian. Không có
	mốc thì thư này chỉ là thư báo, không thành lời mời đối chiếu.
	"""
	from vagabond import thu_khung as _tk

	return (
		'<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
		'style="margin:16px 0 14px"><tr><td style="padding:14px 16px;border:2px solid '
		+ _tk.XANH + ';border-radius:6px;font-family:' + _tk.PHONG + ';font-size:13.5px;'
		'line-height:1.7;color:' + _tk.MUC + '">'
		'<div style="font-weight:bold;font-size:14px;margin:0 0 6px">Đề nghị đối chiếu công nợ</div>'
		"Kính mong quý công ty kiểm tra và phản hồi giúp ba điều:"
		'<div style="margin:7px 0 0">1. Số tiền trên đã về tài khoản của quý công ty chưa.</div>'
		'<div>2. Các hoá đơn liệt kê ở trên đã được ghi nhận thanh toán đủ chưa.</div>'
		'<div>3. Sau lần thanh toán này, công nợ hai bên còn lại bao nhiêu.</div>'
		'<div style="margin:9px 0 0">Nếu có sai lệch, xin quý công ty gửi lại bảng công nợ để '
		"hai bên soát chung. Không nhận được phản hồi trong <b>05 ngày làm việc</b>, chúng tôi "
		"xin phép hiểu là số liệu đã khớp.</div>"
		"</td></tr></table>"
	)


def _nut_doi_chieu(doc):
	"""Nút trả lời thẳng về hộp thư kế toán, tiêu đề điền sẵn."""
	from vagabond import thu_khung as _tk

	tieu_de = "Doi chieu cong no - %s" % doc.name
	dia_chi = "mailto:%s?subject=%s" % (EMAIL_KE_TOAN, tieu_de.replace(" ", "%20"))
	return (
		_tk.nut(dia_chi, "Phản hồi đối chiếu công nợ", goc_anh=_tk.goc_anh())
		+ '<div style="text-align:center;font-family:' + _tk.PHONG + ';font-size:12px;color:'
		+ _tk.XAM + ';margin:9px 0 0">Hoặc bấm Trả lời ngay trong thư này.</div>'
	)


# ------------------------------------------------- nội dung chuyển khoản (MB)


# Nguoi ta gioi han noi dung chuyen khoan quanh 90-100 ky tu tuy ngan hang.
# Cat o 90 cho chac, va cat o cho nao khong lam mat ma APP - ma nam ngay dau
# chuoi chinh la vi vay.
DAI_ND_CK = 90


def _so_hd_ncc(doc):
	"""Số hoá đơn của NHÀ CUNG CẤP trên từng dòng, theo đúng thứ tự dòng.

	Lấy số của NCC (bill_no) chứ không lấy mã HDM nội bộ: nhà cung cấp đối
	chiếu công nợ theo số của họ, mã HDM-2026-xxxxx họ không biết là gì.
	"""
	ra = []
	for d in doc.dong or []:
		so = str(getattr(d, "so_hd_ncc", "") or "").strip()
		if not so and getattr(d, "hoa_don", None):
			so = str(frappe.db.get_value("Purchase Invoice", d.hoa_don, "bill_no") or "").strip()
		so = re.sub(r"[^A-Za-z0-9]", "", _bo_dau(so)).upper()
		if so and so not in ra:
			ra.append(so)
	return ra


def _noi_dung_ck(doc):
	"""Nội dung chuyển khoản: mã hồ sơ đứng trước, rồi số hoá đơn NCC.

	Anh Việt 23/08/2026 đề nghị dạng:
	    THE VAGABOND THANH TOAN HD26957 HD26958 MA PHIEU APP.26.08.011

	ĐÃ ĐỔI MỘT ĐIỂM so với đề nghị đó, và đây là lý do, đừng đảo lại:
	mã hồ sơ phải đứng ĐẦU chứ không đứng cuối. Ngân hàng cắt nội dung ở
	ĐUÔI khi vượt hạn mức (quanh 90 ký tự tuỳ ngân hàng). Đặt mã ở cuối thì
	hồ sơ nào nhiều hoá đơn là mã bị cắt mất, mà mã chính là thứ
	`_sepay_theo_ma_app` dò để tự khớp tiền đã chi. Mất mã thì nút "Dò SePay"
	im lặng báo chưa chuyển trong khi tiền đã đi - sai lặng lẽ, không ai
	thấy. Số hoá đơn bị cắt bớt thì nhà cung cấp vẫn đối chiếu được vì đã có
	mã hồ sơ và số tiền.

	Bỏ dấu vì ngân hàng đẩy nội dung có dấu về SePay là thành dấu hỏi.
	"""
	viec = "HOAN UNG" if (doc.loai or LOAI_NCC) in (LOAI_HU, LOAI_HU_HD) else "THANH TOAN"
	phan = ["VAGABOND", doc.name, viec]
	phan += ["HD" + x for x in _so_hd_ncc(doc)]
	# Ten NCC dat CUOI CUNG: day la phan duoc phep mat khi ngan hang cat.
	ten = _bo_dau(doc.ten_nhan or doc.ten_ncc or doc.nha_cung_cap or "").upper()
	if ten:
		phan.append(ten)
	nd = " ".join(phan)
	nd = re.sub(r"[^A-Za-z0-9 .]", " ", nd)
	nd = re.sub(r"\s+", " ", nd).strip()
	return nd[:DAI_ND_CK].strip()


@frappe.whitelist()
def noi_dung_chuyen_khoan(name, luu=1):
	"""Sinh sẵn số tài khoản, tên thụ hưởng và nội dung để chị Dung copy.

	Anh Việt 13/08/2026: "generate ra stk, tên người thụ hưởng, nội dung
	chuyển khoản (kèm mã) để chị Dung chỉ việc copy paste vào file chuyển
	khoản theo lô của MB".

	Trả thêm dòng dán thẳng vào file lô: các cột phân cách bằng Tab, dán vào
	Excel là mỗi cột một ô, khỏi phải tách tay.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem hồ sơ thanh toán")
	doc = frappe.get_doc("Vagabond Ho So TT", name)

	# Chua khai tai khoan tren ho so thi thu doc lai tu Bank Account - co the
	# ke toan vua khai xong sau khi ho so da lap.
	if not (doc.stk_nhan or "").strip():
		for k, v in (_tk_nhan(doc.nha_cung_cap) or {}).items():
			if v and not doc.get(k):
				doc.set(k, v)
	if not (doc.ten_nhan or "").strip():
		doc.ten_nhan = doc.ten_ncc or doc.nha_cung_cap

	nd = _noi_dung_ck(doc)
	so_tien = flt(doc.con_lai) or flt(doc.tong_tien)
	if cint(luu):
		doc.db_set("noi_dung_ck", nd, update_modified=False)
		for k in ("ten_nhan", "stk_nhan", "ngan_hang_nhan"):
			if doc.get(k):
				doc.db_set(k, doc.get(k), update_modified=False)
		frappe.db.commit()

	thieu = []
	if not (doc.stk_nhan or "").strip():
		thieu.append("số tài khoản")
	if not (doc.ngan_hang_nhan or "").strip():
		thieu.append("tên ngân hàng")

	# Cau truc cot do ngan_hang.tep_lo quyet, KHONG dung o day nua.
	#
	# Anh Viet chot 17/08/2026: moi nut Xuat MB Biz tren app deu goi chung
	# mot ham backend. Truoc do cho nay va man hoan tien moi cho mot bang
	# cot rieng, va do dung la cai bay "hai ban song song" da lam hong ba
	# viec trong ngay 16/08.
	from vagabond.ngan_hang import tep_lo
	import json as _json

	lo = tep_lo(
		_json.dumps(
			[
				{
					"so_tk": doc.stk_nhan,
					"ten_nhan": doc.ten_nhan,
					"ngan_hang": doc.ngan_hang_nhan,
					"so_tien": so_tien,
					"noi_dung": nd,
				}
			]
		)
	)
	cot = lo["cot"]
	gia_tri = [str(x) for x in lo["bang"][0]]
	return {
		"tsv": lo["tsv"],
		"nhac_lo": lo.get("nhac", []),
		"ma": doc.name,
		"ten_nhan": (doc.ten_nhan or "").strip(),
		"ten_nhan_ck": _bo_dau(doc.ten_nhan or "").upper(),
		"stk": (doc.stk_nhan or "").strip(),
		"ngan_hang": (doc.ngan_hang_nhan or "").strip(),
		"so_tien": so_tien,
		"tong_tien": flt(doc.tong_tien),
		"da_tam_ung": flt(doc.da_tam_ung),
		"noi_dung": nd,
		"cot": cot,
		"dong_mb": "\t".join(gia_tri),
		"thieu": thieu,
	}


def _doi_tk_thi_ky_lai(doc):
	"""Đổi tài khoản nhận tiền sau khi đã duyệt thì phải xin chữ ký giám đốc lại.

	Trước 04/09/2026 hai hàm đổi tài khoản chỉ chặn đúng trạng thái đã thanh
	toán. Hồ sơ ở "Đã duyệt, chờ chuyển tiền" vẫn đổi được ba ô tên, số tài
	khoản, ngân hàng; lại ghi bằng `db_set(update_modified=False)` nên mốc
	sửa cũng không đổi, nhìn vào không thấy tờ đã bị đụng. Sáng hôm sau kế
	toán mở ra thấy trạng thái Đã duyệt, ba ô điền sẵn, nội dung chuyển khoản
	đúng mã hồ sơ, và chuyển tiền vào một tài khoản lạ.

	Không chặn cứng, vì đổi tài khoản là việc có thật (khai nhầm ngân hàng
	thì phải sửa). Nhưng đổi xong thì chữ ký giám đốc không còn giá trị với
	tờ này nữa, nên hạ về bước chờ giám đốc để ký lại.
	"""
	if doc.trang_thai != TT_DA_DUYET:
		return ""
	cu = "%s · %s · %s" % (doc.ten_nhan or "-", doc.stk_nhan or "-", doc.ngan_hang_nhan or "-")
	doc.db_set("trang_thai", TT_CHO_GD, update_modified=False)
	doc.db_set("gd_boi", "", update_modified=False)
	doc.db_set("gd_luc", None, update_modified=False)
	return cu


@frappe.whitelist()
def sua_tk_nhan(name, ten_nhan=None, stk_nhan=None, ngan_hang_nhan=None):
	"""Sửa tay tài khoản nhận tiền trên hồ sơ (khi Bank Account chưa khai)."""
	_kiem(VAI_LAP | VAI_FIN, "sửa tài khoản nhận tiền")
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	if doc.trang_thai == TT_DA_TRA:
		frappe.throw("Hồ sơ đã thanh toán rồi, không sửa tài khoản nhận nữa.")
	cu_tk = _doi_tk_thi_ky_lai(doc)
	if ten_nhan is not None:
		doc.db_set("ten_nhan", (ten_nhan or "").strip(), update_modified=False)
	if stk_nhan is not None:
		doc.db_set("stk_nhan", re.sub(r"\s+", "", str(stk_nhan or "")), update_modified=False)
	if ngan_hang_nhan is not None:
		doc.db_set("ngan_hang_nhan", (ngan_hang_nhan or "").strip(), update_modified=False)
	frappe.db.commit()
	_ghi_vet(doc.name, "Sửa tài khoản nhận tiền bởi %s" % frappe.session.user)
	if cu_tk:
		_ghi_vet(doc.name, "Đổi tài khoản nhận SAU khi đã duyệt (cũ: %s), "
			"hồ sơ hạ về chờ giám đốc ký lại." % cu_tk)
	return noi_dung_chuyen_khoan(name, luu=1)


@frappe.whitelist()
def doi_tk_nhan(name, tk_hoan=None):
	"""Đổi tài khoản nhận tiền của một hồ sơ bằng cách CHỌN, không gõ tay.

	QT-31 chốt ô ngân hàng phải là ô chọn. Gõ tay ba ô như đường cũ thì sai
	một chữ trong tên ngân hàng là uỷ nhiệm chi bị trả về, mà không ai biết
	sai ở đâu. Chọn một Bank Account thì cả ba ô lấy nguyên từ hồ sơ ngân
	hàng, và hồ sơ giữ được cái link để đối chiếu.

	Đường gõ tay `sua_tk_nhan` vẫn còn, cho những hồ sơ mà chị Dung chưa kịp
	khai Bank Account bên Next.
	"""
	_kiem(VAI_LAP | VAI_FIN, "sửa tài khoản nhận tiền")
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	if doc.trang_thai == TT_DA_TRA:
		frappe.throw("Hồ sơ đã thanh toán rồi, không sửa tài khoản nhận nữa.")
	cu_tk = _doi_tk_thi_ky_lai(doc)
	# Hoan ung thi tien ve tui NGUOI UNG, con cong no NCC thi ve tui nha
	# cung cap. Truyen dung chu tai khoan vao de hang rao o `_dat_tk_nhan`
	# soi duoc.
	chu = (doc.nguoi_ung or doc.nha_cung_cap or "").strip()
	doc.tk_nhan = _dat_tk_nhan(doc, tk_hoan, chu)
	for o in ("tk_nhan", "ten_nhan", "stk_nhan", "ngan_hang_nhan"):
		doc.db_set(o, doc.get(o) or "", update_modified=False)
	frappe.db.commit()
	_ghi_vet(doc.name, "Chọn tài khoản nhận tiền %s bởi %s" % (doc.tk_nhan, frappe.session.user))
	if cu_tk:
		_ghi_vet(doc.name, "Đổi tài khoản nhận SAU khi đã duyệt (cũ: %s), "
			"hồ sơ hạ về chờ giám đốc ký lại." % cu_tk)
	return noi_dung_chuyen_khoan(name, luu=1)


# --------------------------------------------------------- xuất bộ hồ sơ (ZIP)


@frappe.whitelist()
def xuat_ho_so(name):
	"""Gói cả bộ chứng từ của một hồ sơ thành MỘT tệp PDF khổ A4 dọc.

	Anh Việt 13/08/2026: *"khi bấm nút này thì sẽ xuất ra 1 file PDF size A4
	dọc combine của tất cả các file hồ sơ lại như file Uyên làm mà anh gửi
	em. Không xuất file Zip em ạ"*.

	Cách làm: dựng MỘT trang HTML dài gồm tờ đề nghị, bản in từng chứng từ,
	rồi mỗi ảnh scan một trang; ngắt trang giữa các phần; đưa qua một lượt
	get_pdf duy nhất. Làm vậy thì ảnh vào thẳng PDF mà không cần thư viện
	ghép, và cỡ giấy do CSS quyết nên chắc chắn A4 dọc.

	Tệp đính kèm là PDF thì không nhét vào HTML được. Có thư viện ghép thì
	nối vào cuối; không có thì liệt kê ở trang mục lục chứ không bỏ im - bộ
	hồ sơ thiếu tờ mà không ai biết là thiếu thì tệ hơn báo lỗi.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xuất bộ hồ sơ thanh toán")
	d = chi_tiet(name)
	hs = d["ho_so"]
	h = frappe.utils.escape_html

	# Xâu phông dùng chung, xem vagabond/phong_chu.py. Ba khối dưới đây từng
	# khai thẳng Arial, mà máy chủ không có Arial nên chữ có dấu bị mượn
	# phông khác và vỡ nét.
	from vagabond import mau_chuan as mc

	NGAT = '<div style="page-break-after:always"></div>'
	phan = [_to_app_html(name)]
	muc_luc, hong, pdf_rieng = ["Tờ đề nghị thanh toán %s" % hs["ma"]], [], []

	def _in_html(dt, dn, nhan):
		try:
			noi = frappe.get_print(dt, dn)
			phan.append(NGAT + '<div style="font-family:' + mc.PHONG + '">' + noi + "</div>")
			muc_luc.append("%s %s" % (nhan, dn))
			return True
		except Exception:
			hong.append("%s %s" % (nhan, dn))
			frappe.log_error(frappe.get_traceback(), "ho_so_tt: in %s %s" % (dt, dn))
			return False

	# BAN IN HOA DON CUA ERPNEXT: chi in khi ho so KHONG co ban the hien that.
	#
	# Anh Viet 23/08/2026, chi vao trang do: *"da co trang o tren noi dung nay
	# roi thi khong can trang nay nua, bo di"*. To de nghi o trang mot da liet
	# ke tung khoan chi, va ban the hien hoa don dinh kem moi la to co gia tri
	# phap ly - ban in lai cua ERPNext o giua chi noi lai lan ba.
	#
	# Vi sao van GIU khi chua co ban the hien: ho so nao chua kip tai ban the
	# hien ve ma bo luon ca trang nay thi chi tiet hoa don bien mat khoi bo ho
	# so, ke toan truong khong con gi de doi chieu. Bo mot to thua thi tiet
	# kiem giay; bo mat to duy nhat co so lieu thi hong ca bo.
	co_ban_the_hien = set()
	for x in d["dong"]:
		if not x.get("hoa_don"):
			continue
		for f in (x.get("scan") or []) + (x.get("tep_dong") or []):
			if str(f.get("ten") or "").lower().endswith(".pdf"):
				co_ban_the_hien.add(x["hoa_don"])
				break

	da_po, da_pnk = set(), set()
	for x in d["dong"]:
		if x["hoa_don"] and x["hoa_don"] not in co_ban_the_hien:
			_in_html("Purchase Invoice", x["hoa_don"], "Hoá đơn mua")
		for po in x["po"]:
			if po not in da_po:
				da_po.add(po)
				_in_html("Purchase Order", po, "Đơn mua hàng")
		for pnk in x["pnk"]:
			if pnk not in da_pnk:
				da_pnk.add(pnk)
				_in_html("Purchase Receipt", pnk, "Phiếu nhập kho")

	# Anh chung tu: 4 anh mot trang A4, moi anh co dong nhan ghi ro thuoc
	# khoan nao (anh Viet 22/08/2026). Truoc day moi anh mot trang, ba chuc
	# khoan la ba chuc to giay.
	anh, bo_qua = _gom_anh_ho_so(d)
	if anh:
		# Tieu de nam CHUNG trang voi luoi anh dau tien, khong chiem mot to
		# rieng. Anh Viet 23/08/2026: *"qua nhieu khoang trong gay phi giay"* -
		# mot dong tieu de ma an tron mot mat giay A4 la dung cai lang phi do.
		phan.append(
			NGAT
			+ '<div style="font-family:' + mc.PHONG + ';margin-bottom:4mm">'
			+ '<div style="font-size:14px;font-weight:bold">'
			+ 'CHỨNG TỪ ĐÍNH KÈM'
			+ '<span style="font-style:italic;font-weight:normal;'
			+ 'font-size:11px;color:#666"> · Supporting documents</span></div>'
			+ '<div style="font-size:10.5px;color:#666">'
			+ '%d ảnh, xếp 4 ảnh một trang. Dòng chữ dưới mỗi ảnh ghi rõ ảnh '
			'thuộc khoản chi nào.</div></div>' % len(anh)
			+ luoi_anh(anh)
		)
		muc_luc.append("Chứng từ đính kèm: %d ảnh" % len(anh))
	for f in bo_qua:
		if (f.get("duoi") or "") == "pdf":
			pdf_rieng.append({"file": f.get("file"), "ten": f.get("ten")})
		else:
			hong.append("%s (%s)" % (f.get("ten"), f.get("nhan")))

	# Trang muc luc dat o CUOI: doc xong bo ho so moi doi chieu lai cho tien.
	ml = (
		NGAT
		+ '<div style="font-family:' + mc.PHONG + ';font-size:12.5px">'
		+ '<div style="font-size:16px;font-weight:bold;margin-bottom:10px">MỤC LỤC BỘ HỒ SƠ %s</div>' % h(hs["ma"])
		+ "<ol>" + "".join("<li>%s</li>" % h(x) for x in muc_luc) + "</ol>"
	)
	if pdf_rieng or hong:
		ml += '<div style="margin-top:12px;color:#b3261e"><b>Chưa gộp được vào tệp này, xem trên Next:</b><ul>'
		ml += "".join("<li>%s</li>" % h(f["ten"] or f["file"]) for f in pdf_rieng)
		ml += "".join("<li>%s</li>" % h(x) for x in hong)
		ml += "</ul></div>"
	ml += "</div>"
	phan.append(ml)

	# Le giay lay tu MOT cho duy nhat, xem vagabond/mau_in/le_in.py. Truoc day
	# cho nay tu khai 12mm con ban ghi Print Format khai 15mm, hai luat cho
	# cung mot viec (anh Viet 23/08/2026 bao ban in bi tran le).
	from vagabond.mau_in.le_in import css_trang

	khung = (
		"<html><head><meta charset='utf-8'>"
		+ css_trang(phong=mc.PHONG)
		+ '</head><body><div class="vgb-in">'
		+ "".join(phan)
		+ "</div></body></html>"
	)

	from frappe.utils.pdf import get_pdf

	# Chép bộ phông tiếng Việt vào máy chủ trước khi in. Bộ hồ sơ này dựng
	# khung riêng (`le_in.css_trang`) nên không đi qua `mau_chuan.khung_trang`,
	# vì vậy phải gọi tay. Xem vagabond/phong_chu.py.
	try:
		from vagabond.phong_chu import bao_dam_phong

		bao_dam_phong()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: bao dam phong")

	noi_dung = get_pdf(khung, options={"page-size": "A4", "orientation": "Portrait"})

	# Noi them cac tep PDF dinh kem, neu moi truong co thu vien ghep.
	if pdf_rieng:
		try:
			from pypdf import PdfReader, PdfWriter
		except Exception:
			try:
				from PyPDF2 import PdfReader, PdfWriter
			except Exception:
				PdfReader = PdfWriter = None
		if PdfReader:
			try:
				w = PdfWriter()
				for tr in PdfReader(io.BytesIO(noi_dung)).pages:
					w.add_page(tr)
				for f in list(pdf_rieng):
					noi = frappe.get_doc("File", f["file"]).get_content()
					if isinstance(noi, str):
						noi = noi.encode("utf-8")
					for tr in PdfReader(io.BytesIO(noi)).pages:
						w.add_page(tr)
					muc_luc.append("Bản scan %s" % (f["ten"] or f["file"]))
					pdf_rieng.remove(f)
				bo = io.BytesIO()
				w.write(bo)
				noi_dung = bo.getvalue()
			except Exception:
				frappe.log_error(frappe.get_traceback(), "ho_so_tt: ghep PDF dinh kem %s" % name)

	con_thieu = [f["ten"] or f["file"] for f in pdf_rieng] + hong
	return {
		"ten_file": "ho-so-%s.pdf" % hs["ma"].replace(".", "-"),
		"b64": base64.b64encode(noi_dung).decode(),
		"so_tep": len(muc_luc),
		"hong": con_thieu,
		# De doi chieu sau khi deploy: thu vien nao dang dung de doi PDF sang
		# anh, va bao nhieu anh da vao luoi. Rong nghia la may thieu thu vien
		# va bo ho so dang quay ve duong noi PDF cu.
		"raster": _thu_vien_raster(),
		"so_anh": len(anh),
	}


@frappe.whitelist()
def xem_to_app(name):
	"""Tờ đề nghị thanh toán để xem trên màn hình, không cần tải cả bộ."""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem hồ sơ thanh toán")
	return {"html": _to_app_html(name)}


def _to_app_html(name):
	"""Tờ đề nghị thanh toán, dựng theo đúng khuôn bản in Đơn mua hàng.

	Anh Việt 14/08/2026: *"em làm theo cái mẫu PO của mình có logo, header,...
	thì đẹp hơn. Em thử cấu hình lại nhé vì file hiện tại hơi đơn giản"*, và
	khoanh đỏ yêu cầu **thêm một cột số hoá đơn NCC** tách khỏi cột số hoá
	đơn nội bộ.

	Dùng lại đúng dải logo, khối thông tin công ty và phông chữ của Print
	Format "Vagabond - Đơn đặt hàng" để hai tờ đứng cạnh nhau trông cùng một
	nhà. Phông DejaVu Sans đứng đầu danh sách là cố ý: wkhtmltopdf trên máy
	chủ chỉ có phông đó dựng đủ dấu tiếng Việt.
	"""
	from vagabond import mau_chuan as mc

	d = chi_tiet(name)
	hs, dong = d["ho_so"], d["dong"]
	h = frappe.utils.escape_html
	la_hu = hs["loai"] in (LOAI_HU, LOAI_HU_HD)

	# Lay tu khuon chuan, khong khai lai: khai lai la mo duong cho hai ban in
	# lech phong nhau ma khong ai de y.
	VIEN = mc.VIEN
	def _td(noi, canh="left", dam=False, khong_ngat=False):
		return (
			'<td style="border:%s;padding:5px 7px;font-size:10.5px;text-align:%s;%s%s">%s</td>'
			% (VIEN, canh, "font-weight:bold;" if dam else "",
			   "white-space:nowrap;" if khong_ngat else "", noi)
		)

	nhieu_nha = len({(x["ben_ban"] or x["ncc_hd"] or "").strip() for x in dong
	                 if (x["ben_ban"] or x["ncc_hd"] or "").strip()}) > 1
	hang = []
	for i, x in enumerate(dong, 1):
		hang.append(
			"<tr>"
			+ _td(str(i), "center")
			+ _td(_ngay_vn(x["ngay_hd"]) or "-", "center", khong_ngat=True)
			+ _td(h(x["hoa_don"] or "-"), khong_ngat=True)
			+ _td(h(x["so_hd_ncc"] or "-"), "center", khong_ngat=True)
			# Ho so gom nhieu nha thi ten nha cung cap phai nam TRONG bang,
			# khong the chi ghi mot lan o dau to nhu truoc.
			+ _td(h((("%s - " % (x["ben_ban"] or x["ncc_hd"])) if (nhieu_nha and (x["ben_ban"] or x["ncc_hd"])) else "")
			        + (x["noi_dung"] or ("" if nhieu_nha else (x["ncc_hd"] or "")))))
			+ _td(_tien(x["so_tien"]), "right", dam=True, khong_ngat=True)
			+ _td(h(x["ghi_chu"] or x["ben_ban"] or ""))
			+ "</tr>"
		)

	def _dong_tong(nhan, tien, dam=True):
		return (
			'<tr><td colspan="5" style="border:%s;padding:6px 7px;font-size:11px;'
			'text-align:right;%s">%s</td>'
			'<td style="border:%s;padding:6px 7px;font-size:11.5px;text-align:right;'
			'white-space:nowrap;%s">%s</td>'
			'<td style="border:%s"></td></tr>'
			% (VIEN, "font-weight:bold;" if dam else "", nhan,
			   VIEN, "font-weight:bold;" if dam else "", tien, VIEN)
		)

	cuoi_bang = _dong_tong(mc.sn("TỔNG CỘNG", "TOTAL", co_en="9px"), _tien(hs["tong_tien"]))
	if flt(hs.get("da_tam_ung")):
		cuoi_bang += _dong_tong(mc.sn("Trừ số tiền đã tạm ứng", "Less advance paid", co_en="9px"), _tien(hs["da_tam_ung"]), dam=False)
		cuoi_bang += _dong_tong(mc.sn("CÒN LẠI PHẢI CHUYỂN", "BALANCE TO TRANSFER", co_en="9px"), _tien(hs["con_lai"]))

	def _o_tt(nhan, gt):
		return (
			'<tr><td style="border:none;padding:1px 0;font-size:11px;color:#555;'
			'white-space:nowrap;width:34%%">%s</td>'
			'<td style="border:none;padding:1px 0;font-size:11px;font-weight:bold">%s</td></tr>'
			% (nhan, gt)
		)

	ben_nhan = (
		'<table style="width:100%;border:none;border-collapse:collapse">'
		+ _o_tt(mc.sn("Đề nghị thanh toán cho:", "Pay to", co_en="9px"),
		        h(hs["ten_nhan"] or hs["ten_ncc"] or hs["ncc"]))
		+ _o_tt(
			mc.sn("Người được hoàn ứng:" if la_hu else "Mã nhà cung cấp:",
			      "Settled to" if la_hu else "Supplier code", co_en="9px"),
			h(hs.get("ten_nguoi_ung") or hs["ncc"]),
		)
		+ (_o_tt(mc.sn("Gồm nhà cung cấp:", "Suppliers included", co_en="9px"),
		         "%d nhà, liệt kê trong bảng dưới" % hs.get("so_ncc", 0))
		   if nhieu_nha else "")
		+ _o_tt(mc.sn("Số tài khoản:", "Account no.", co_en="9px"),
		        h(hs["stk_nhan"] or "..............."))
		+ _o_tt(mc.sn("Ngân hàng:", "Bank", co_en="9px"),
		        h(hs["ngan_hang_nhan"] or "..............."))
		+ _o_tt(mc.sn("Nội dung chuyển khoản:", "Transfer remark", co_en="9px"),
		        h(hs["noi_dung_ck"] or "..............."))
		+ "</table>"
	)

	# KHONG ghep HTML tinh toan san vao chuoi dinh dang %.
	#
	# Ngay 22/08/2026 dung cai bay nay: `mc.dai_logo()` tra ve CSS co
	# `width:45%;`, ghep vao giua mot chuoi dinh dang thi Python doc `%;`
	# thanh mot lenh dinh dang va no "unsupported format character ';'".
	# Ca nut Xuat bo ho so chet, ke toan bam ra loi 500.
	#
	# Nen o day dinh dang TRUOC roi moi noi chuoi, va moi manh HTML dong deu
	# di qua %s chu khong ghep thang vao khuon.
	tieu_de_vi = "GIẤY ĐỀ NGHỊ HOÀN ỨNG" if la_hu else "GIẤY ĐỀ NGHỊ THANH TOÁN"
	tieu_de_en = "Advance Settlement Request" if la_hu else "Payment Request"

	dau_trang = (
		'<div style="text-align:center;margin:14px 0 2px">'
		'<div style="font-size:19px;font-weight:bold;letter-spacing:1px">%s</div>'
		'<div style="font-size:11.5px;font-style:italic;color:#666;margin-top:1px">%s</div>'
		'<div style="font-size:11px;color:#555;margin-top:4px">'
		"Số / No.: <b>%s</b> &nbsp;·&nbsp; Ngày / Date: <b>%s</b></div></div>"
		'<div style="font-size:11px;margin:12px 0 3px">Kính gửi: <b>Ban Giám đốc</b>'
		'<span style="font-style:italic;color:#777"> / To: Board of Directors</span></div>'
	) % (h(tieu_de_vi), h(tieu_de_en), h(hs["ma"]), _ngay_vn(hs["ngay"]))

	bang = (
		'<table style="width:100%%;border-collapse:collapse;margin-top:10px">'
		"<tr>%s%s%s%s%s%s%s</tr>%s%s</table>"
	) % (
		mc.o_th("STT", "No."),
		mc.o_th("Ngày hoá đơn", "Invoice date"),
		mc.o_th("Số hoá đơn", "Invoice no."),
		mc.o_th("Số hoá đơn NCC", "Supplier invoice no."),
		mc.o_th("Nội dung", "Description"),
		mc.o_th("Số tiền", "Amount"),
		mc.o_th("Ghi chú", "Remarks"),
		"".join(hang), cuoi_bang,
	)

	# Khoi chu ky CHUAN CHUNG, dung tu vagabond/mau_chuan.py. Moi ho so
	# thanh toan tren APP deu lay tu do ra, sua mot lan la ca he doi theo
	# (anh Viet 22/08/2026).
	chu_ky = mc.khoi_chu_ky({
		"NGƯỜI ĐỀ NGHỊ": hs["nguoi_tao_ten"],
		"KẾ TOÁN TRƯỞNG": hs["fin_ten"],
		"GIÁM ĐỐC": hs["gd_ten"],
	})

	return (
		'<div style="font-family:' + mc.PHONG + ';color:#1c1a17;font-size:12px;'
		'line-height:1.45">'
		+ mc.dai_logo()
		+ dau_trang
		+ ben_nhan
		+ bang
		+ chu_ky
		+ "</div>"
	)



# -------------------------------------------------------------------- Excel


@frappe.whitelist()
def xuat_excel(trang_thai=None, ncc=None, tu=None, den=None, tu_khoa="", so_ngay=90, loai=None,
		loai_cp_thue=None, tk_chi=None):
	"""Bộ hồ sơ ra Excel cho kế toán theo dõi: một dòng một hoá đơn.

	NHẬN ĐỦ MỌI Ô LỌC CỦA MÀN HÌNH. Tệp tải về phải đúng bằng cái đang bày
	trên màn: xuất ra một bộ rộng hơn cái người ta đang nhìn là lặng lẽ đưa
	nhầm số liệu, mà không ai đối chiếu lại.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xuất hồ sơ thanh toán")
	kq = danh_sach(
		trang_thai=trang_thai, ncc=ncc, tu=tu, den=den,
		tu_khoa=tu_khoa, so_ngay=so_ngay, loai=loai, loai_cp_thue=loai_cp_thue,
		tk_chi=tk_chi,
	)
	rows = kq["rows"]
	chi_tiet_dong = {}
	if rows:
		for d in frappe.get_all(
			"Vagabond Ho So TT Dong",
			filters={"parent": ["in", [r["name"] for r in rows]]},
			fields=["parent", "hoa_don", "so_hd_ncc", "ngay_hd", "han_tra",
				"con_no", "so_tien", "noi_dung", "ben_ban", "loai_chi", "co_vat",
				"tk_no", "tk_co"],
			order_by="parent asc, idx asc",
			limit_page_length=0,
		):
			chi_tiet_dong.setdefault(d.parent, []).append(d)

	bang = [
		["HỒ SƠ THANH TOÁN NHÀ CUNG CẤP"],
		["Từ %s đến %s%s" % (
			tu or ("%d ngày gần đây" % int(so_ngay or 90)), den or nowdate(),
			(" · %s" % NHAN.get(trang_thai, trang_thai)) if trang_thai else "",
		)],
		["Số hồ sơ", len(rows), "Tổng đề nghị trả", kq["tong_tien"]],
		[],
		["Mã hồ sơ", "Loại", "Loại chi phí thuế", "Ngày lập", "Nhà cung cấp", "Trạng thái", "Tổng hồ sơ",
		 "Trừ tạm ứng", "Còn lại chuyển",
		 "Hoá đơn", "Số HĐ NCC", "Ngày HĐ", "Nội dung", "Bên bán", "Loại chi", "Có VAT",
		 "TK Nợ", "TK Có",
		 "Hạn trả", "Còn nợ lúc lập", "Đề nghị trả",
		 "Người lập", "Kế toán duyệt", "Giám đốc duyệt", "Ngày thanh toán",
		 "Mã giao dịch", "Đã báo NCC"],
	]
	for r in rows:
		ds = chi_tiet_dong.get(r["name"]) or [None]
		for i, d in enumerate(ds):
			bang.append([
				r["ma"] if i == 0 else "",
				NHAN_LOAI.get(r.get("loai"), r.get("loai") or "") if i == 0 else "",
				NHAN_CP_THUE.get(r.get("loai_cp_thue"), "") if i == 0 else "",
				str(r["ngay"] or "") if i == 0 else "",
				(r["ten_ncc"] or r["nha_cung_cap"]) if i == 0 else "",
				NHAN.get(r["trang_thai"], r["trang_thai"]) if i == 0 else "",
				flt(r["tong_tien"]) if i == 0 else "",
				flt(r.get("da_tam_ung")) if i == 0 else "",
				flt(r.get("con_lai")) if i == 0 else "",
				(d.hoa_don or "") if d else "",
				(d.so_hd_ncc or "") if d else "",
				str(d.ngay_hd or "") if d else "",
				(d.noi_dung or "") if d else "",
				(d.ben_ban or "") if d else "",
				(d.loai_chi or "") if d else "",
				("Có" if cint(d.co_vat) else "") if d else "",
				(d.tk_no or "") if d else "",
				(d.tk_co or "") if d else "",
				str(d.han_tra or "") if d else "",
				flt(d.con_no) if d else "",
				flt(d.so_tien) if d else "",
				_ten_nguoi(r["nguoi_tao"]) if i == 0 else "",
				_ten_nguoi(r["fin_boi"]) if i == 0 else "",
				_ten_nguoi(r["gd_boi"]) if i == 0 else "",
				str(r["ngay_thanh_toan"] or "") if i == 0 else "",
				r["ma_giao_dich"] or "" if i == 0 else "",
				("Rồi" if cint(r["email_da_gui"]) else "Chưa") if i == 0 else "",
			])
	bang.append([])
	bang.append(["TỔNG", "", "", "", kq["tong_tien"]])

	from frappe.utils.xlsxutils import make_xlsx

	tep = make_xlsx(bang, "Ho so thanh toan")
	noi_dung = tep.getvalue() if isinstance(tep, io.BytesIO) else tep
	return {
		"ten_file": "ho-so-thanh-toan-%s.xlsx" % nowdate(),
		"b64": base64.b64encode(noi_dung).decode(),
	}


# ------------------------------------------- Tim giao dich de khop tay


@frappe.whitelist()
def tim_giao_dich(tu_khoa="", so_ngay=120, so_tien=None, chi_chua_gom=0, tai_khoan=None):
	"""Tra cuu giao dich ngan hang de kế toán tự khớp tay vào hồ sơ.

	Anh Việt 14/08/2026, về hai hồ sơ mang mã SePay cũ không dò được:
	*"tạo chức năng tìm kiếm giao dịch để khớp thủ công được không em? Sao em
	không đề xuất phương án nữa vậy?"*

	Vì sao cần: mã giao dịch trên hồ sơ được gõ tay hoặc lấy từ đợt đồng bộ
	SePay cũ, nên có tờ mang mã mà bảng Bank Transaction hiện tại không có.
	Trước đây gặp vậy thì chịu, không có đường nào nối lại. Màn này bày mọi
	giao dịch ra cho kế toán tự tìm theo số tiền, theo ngày, theo nội dung,
	rồi gán thẳng.

	Chỉ ĐỌC và GÁN MÃ. Không sinh bút toán, không đụng vào sổ - việc ghi sổ
	vẫn đi đường cũ qua danh_dau_da_tra.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "tra cứu giao dịch ngân hàng")
	dk = {
		"date": [">=", add_days(nowdate(), -int(so_ngay or 120))],
		"docstatus": ["<", 2],
	}
	if tai_khoan:
		dk["bank_account"] = tai_khoan
	rows = frappe.get_all(
		"Bank Transaction",
		filters=dk,
		fields=[
			"name", "date", "description", "deposit", "withdrawal",
			"bank_account", "reference_number", "status",
		],
		order_by="date desc, creation desc",
		limit_page_length=0,
	)
	da_gom = _gd_da_gom()
	k = (tu_khoa or "").strip().lower()
	muc = flt(so_tien) if so_tien else 0.0
	ra = []
	for r in rows:
		ma = (r.get("reference_number") or r.get("name") or "").strip()
		tien = flt(r.get("withdrawal")) or flt(r.get("deposit"))
		if muc and abs(tien - muc) > 1:
			continue
		if k and k not in (r.get("description") or "").lower() and k not in ma.lower():
			continue
		daco = ma in da_gom or (r.get("name") or "") in da_gom
		if cint(chi_chua_gom) and daco:
			continue
		ra.append({
			"ma": ma or r["name"],
			"ten_ban_ghi": r["name"],
			"ngay": str(r["date"] or ""),
			"noi_dung": (r.get("description") or "")[:300],
			"chi": flt(r.get("withdrawal")),
			"thu": flt(r.get("deposit")),
			"tien": tien,
			"tai_khoan": r.get("bank_account") or "",
			"da_gom": 1 if daco else 0,
		})
	return {
		"rows": ra[:300],
		"tong": len(ra),
		"con_nua": max(0, len(ra) - 300),
		"tai_khoan_quy": _bank_account_quy(),
		"sua_duoc": 1 if (VAI_FIN & _vai()) else 0,
	}


@frappe.whitelist()
def gan_giao_dich(name, ma_giao_dich, dong=None):
	"""Gán tay một mã giao dịch ngân hàng vào hồ sơ hoặc vào một dòng.

	dong: idx của dòng cần gán. Bỏ trống thì gán vào ô mã giao dịch của cả
	hồ sơ (dùng cho hồ sơ đã thanh toán mà mã cũ không dò ra).
	"""
	_kiem(VAI_FIN, "gán mã giao dịch")
	ma_gd = (ma_giao_dich or "").strip()
	if not ma_gd:
		frappe.throw("Chưa chọn giao dịch nào.")
	doc = frappe.get_doc("Vagabond Ho So TT", name)

	# Một giao dịch chỉ được nằm ở một chỗ. Chặn ở đây chứ không chỉ ở
	# validate của dòng, vì đường này gán thẳng vào hồ sơ cha.
	trung = frappe.db.sql(
		"""select p.name from `tabVagabond Ho So TT Dong` d
		inner join `tabVagabond Ho So TT` p on p.name = d.parent
		where d.ma_giao_dich = %s and p.name != %s""",
		(ma_gd, name),
	)
	if trung:
		frappe.throw("Giao dịch %s đã nằm trong hồ sơ %s." % (ma_gd, trung[0][0]))
	trung2 = frappe.db.get_value(
		"Vagabond Ho So TT", {"ma_giao_dich": ma_gd, "name": ["!=", name]}, "name"
	)
	if trung2:
		frappe.throw("Giao dịch %s đã gán cho hồ sơ %s." % (ma_gd, trung2))

	if dong:
		idx = cint(dong)
		hang = [d for d in doc.dong if d.idx == idx]
		if not hang:
			frappe.throw("Không thấy dòng số %s trong hồ sơ." % dong)
		hang[0].ma_giao_dich = ma_gd
		cho = "dòng %s" % idx
	else:
		doc.ma_giao_dich = ma_gd
		cho = "hồ sơ"
	doc.flags.ignore_validate_update_after_submit = True
	doc.save(ignore_permissions=True)
	doc.add_comment(
		"Comment",
		"Khớp tay giao dịch %s vào %s, người làm %s"
		% (ma_gd, cho, frappe.session.user),
	)
	return {"ok": 1, "loi_nhan": "Đã gán giao dịch %s vào %s %s." % (ma_gd, cho, name)}


# ============================================================================
# CHỨNG TỪ TỪNG DÒNG: loại chứng từ, tệp đính kèm, nối phiếu nội bộ
# ============================================================================
#
# Anh Việt 22/08/2026: *"Luồng 'Hoàn ứng không hóa đơn' hiện tại đang có rủi
# ro gian lận cao. Kế toán trưởng yêu cầu siết chặt hồ sơ, bắt buộc phải có
# chứng từ đính kèm"*.
#
# Lỗ hổng cụ thể: hồ sơ hoàn ứng không hoá đơn chỉ gồm mấy dòng gõ tay và
# một mã giao dịch ngân hàng. Mã giao dịch chứng minh TIỀN ĐÃ ĐI, không
# chứng minh tiền đi để MUA CÁI GÌ. Ai gõ được số cũng gõ được một dòng.
#
# Ba thứ bịt lỗ đó, và cả ba đều gắn vào TỪNG DÒNG chứ không phải cả hồ sơ:
#
#   1. Loại chứng từ  - khai rõ đang lấy gì làm bằng chứng cho khoản này.
#   2. Tệp chứng từ   - ảnh chụp bill, phiếu thu, biên bản.
#   3. Phiếu nội bộ   - khoản đã có phiếu quản lý duyệt thì nối thẳng vào,
#                       kéo cả số tiền lẫn tệp sang, khỏi khai lại.
#
# Vì sao gắn theo DÒNG chứ không theo hồ sơ: một hồ sơ hoàn ứng gom hàng
# chục khoản của nhiều người bán khác nhau. Đính một xấp ảnh vào hồ sơ thì
# kế toán vẫn phải ngồi đoán ảnh nào của khoản nào. Gắn theo dòng thì bản in
# ghi được "ảnh này thuộc khoản số 3", đối chiếu bằng mắt là xong.

DM_CHUNG_TU = "Vagabond Loai Chung Tu"
DNC = "Vagabond De Nghi Chi"

# Trạng thái phiếu nội bộ được phép nối vào hồ sơ hoàn ứng. Chỉ nhận phiếu
# đã qua cửa duyệt: nối phiếu còn nháp là mở lại đúng cái lỗ hổng vừa bịt.
TT_PHIEU_NOI_BO = ("Hoan tat", "Da chi")


@frappe.whitelist()
def ds_loai_chung_tu():
	"""Danh mục loại chứng từ cho ô chọn trên màn hình.

	Dùng chung đúng một danh mục với phiếu thanh toán nội bộ
	(`Vagabond Loai Chung Tu`), không dựng danh sách riêng. Hai màn khai hai
	bộ tên khác nhau thì đến lúc đối chiếu không ai ghép được.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "đọc danh mục chứng từ")
	try:
		from vagabond.de_nghi_chi import dung_danh_muc_chung_tu

		dung_danh_muc_chung_tu()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: dung danh muc chung tu")
	ds = frappe.get_all(
		DM_CHUNG_TU,
		filters={"dang_dung": 1},
		fields=["name", "ten", "la_hoa_don_vat", "bat_buoc_tep", "mo_ta", "thu_tu"],
		order_by="thu_tu asc, name asc",
		limit_page_length=0,
	)
	return {
		"ds": [
			{
				"ma": r["name"],
				"ten": r.get("ten") or r["name"],
				"vat": cint(r.get("la_hoa_don_vat")),
				"bat_buoc_tep": cint(r.get("bat_buoc_tep")),
				"mo_ta": r.get("mo_ta") or "",
			}
			for r in ds
		]
	}


def _tep_cua_dong(chuoi):
	"""Tách chuỗi mã tệp của một dòng thành danh sách. Chuỗi rỗng ra []."""
	return [x.strip() for x in str(chuoi or "").replace(",", "\n").split("\n") if x.strip()]


def _ho_tep(ma_tep):
	"""Thông tin hiển thị của một loạt mã tệp, giữ nguyên thứ tự đã lưu."""
	ma_tep = [m for m in (ma_tep or []) if m]
	if not ma_tep:
		return []
	try:
		co = {
			r["name"]: r
			for r in frappe.get_all(
				"File",
				filters={"name": ["in", ma_tep]},
				fields=["name", "file_name", "file_url", "is_private", "file_size"],
				limit_page_length=0,
			)
		}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: doc tep cua dong")
		return []
	ra = []
	for m in ma_tep:
		r = co.get(m)
		if not r:
			continue
		ten = r.get("file_name") or m
		duoi = ten.rsplit(".", 1)[-1].lower() if "." in ten else ""
		ra.append({
			"file": m,
			"ten": ten,
			"url": r.get("file_url") or "",
			"rieng": cint(r.get("is_private")),
			"co": cint(r.get("file_size")),
			"la_anh": 1 if duoi in ("jpg", "jpeg", "png", "gif", "bmp", "webp") else 0,
			"duoi": duoi,
		})
	return ra


@frappe.whitelist()
def ds_phieu_noi_bo(tu_khoa="", so_ngay=180, gioi_han=60):
	"""Phiếu thanh toán nội bộ đã duyệt, chưa nối vào hồ sơ nào.

	Anh Việt 22/08/2026: *"mở ra một Modal danh sách các 'Phiếu thanh toán
	nội bộ' (của các quản lý) có trạng thái Đã duyệt/Đã chi"*.

	Hai bộ lọc quan trọng:

	  - CHỈ trạng thái đã qua duyệt. Phiếu còn nháp mà nối được thì người
	    lập hồ sơ tự viết phiếu rồi tự nối, cửa duyệt thành vô nghĩa.
	  - CHỈ phiếu chưa nối hồ sơ nào (`ho_so_tt` còn trống). Một phiếu nội
	    bộ nối vào hai hồ sơ là công ty trả tiền hai lần cho một khoản. Đây
	    là rủi ro nặng nhất của cả tính năng này nên chặn ngay ở khâu liệt kê,
	    và chặn lần nữa lúc nối.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "đọc phiếu thanh toán nội bộ")
	loc = {
		"trang_thai": ["in", list(TT_PHIEU_NOI_BO)],
		"ho_so_tt": ["in", ["", None]],
	}
	if cint(so_ngay) > 0:
		loc["creation"] = [">=", add_days(nowdate(), -cint(so_ngay))]
	q = (tu_khoa or "").strip()
	try:
		ds = frappe.get_all(
			DNC,
			filters=loc,
			or_filters=(
				{
					"name": ["like", "%" + q + "%"],
					"ten_khoan_chi": ["like", "%" + q + "%"],
					"nguoi_tao": ["like", "%" + q + "%"],
					"dien_giai": ["like", "%" + q + "%"],
				}
				if q
				else None
			),
			fields=[
				"name", "ten_khoan_chi", "so_tien", "tong_tien", "trang_thai",
				"nguoi_tao", "ngay_can_tt", "dien_giai", "loai_nghiep_vu",
				"phan_loai", "creation", "hinh_thuc", "nha_cung_cap",
			],
			order_by="creation desc",
			limit_page_length=cint(gioi_han) or 60,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: doc ds phieu noi bo")
		return {"ds": [], "loi": "Chưa đọc được danh sách phiếu nội bộ."}
	ra = []
	for r in ds:
		tien = flt(r.get("tong_tien")) or flt(r.get("so_tien"))
		ra.append({
			"ma": r["name"],
			"ten": r.get("ten_khoan_chi") or r["name"],
			"so_tien": tien,
			"trang_thai": r.get("trang_thai") or "",
			"nguoi_tao": r.get("nguoi_tao") or "",
			"nguoi_ten": _ten_nguoi(r.get("nguoi_tao")),
			"ngay": str(r.get("ngay_can_tt") or "")[:10] or str(r.get("creation") or "")[:10],
			"dien_giai": r.get("dien_giai") or "",
			"loai": r.get("loai_nghiep_vu") or "",
			"phan_loai": r.get("phan_loai") or "",
			"so_tep": len(_dinh_kem([(DNC, r["name"])])),
		})
	return {"ds": ra, "tong": len(ra)}


@frappe.whitelist()
def xem_phieu_noi_bo(phieu=None):
	"""Đọc trọn một phiếu nội bộ để đắp vào dòng hoàn ứng.

	Trả về đúng ba thứ màn hình cần: số tiền, nội dung, và danh sách tệp
	đính kèm. Máy KHÔNG tự ghi vào hồ sơ ở đây - người lập xem rồi mới bấm
	nhận, vì đắp nhầm phiếu thì phải gỡ tay.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "đọc phiếu thanh toán nội bộ")
	phieu = (phieu or "").strip()
	if not phieu or not frappe.db.exists(DNC, phieu):
		frappe.throw("Không tìm thấy phiếu thanh toán nội bộ %s." % (phieu or "(trống)"))
	d = frappe.get_doc(DNC, phieu)
	if d.trang_thai not in TT_PHIEU_NOI_BO:
		frappe.throw(
			"Phiếu %s đang ở trạng thái \"%s\" nên chưa nối được. Chỉ nối phiếu "
			"đã duyệt xong hoặc đã chi." % (phieu, d.trang_thai)
		)
	if (d.get("ho_so_tt") or "").strip():
		frappe.throw(
			"Phiếu %s đã nối vào hồ sơ %s rồi. Một phiếu chỉ được nối một lần, "
			"không thì công ty trả tiền hai lần cho cùng một khoản."
			% (phieu, d.ho_so_tt)
		)
	tep = _dinh_kem([(DNC, phieu)])
	# Phieu nhieu dong thi gop noi dung lai cho gon, van giu tung so tien de
	# nguoi lap doi chieu duoc voi tong.
	cac_dong = []
	for r in (d.get("cac_khoan") or []):
		cac_dong.append({
			"noi_dung": r.get("noi_dung") or "",
			"so_tien": flt(r.get("so_tien")),
			"loai_chung_tu": r.get("loai_chung_tu") or "",
			"so_hoa_don": r.get("so_hoa_don") or "",
			"ten_ban": r.get("ten_ban") or "",
		})
	tong = flt(d.get("tong_tien")) or flt(d.get("so_tien"))
	noi_dung = (d.get("ten_khoan_chi") or "").strip()
	if not noi_dung and cac_dong:
		noi_dung = ", ".join(x["noi_dung"] for x in cac_dong if x["noi_dung"])[:180]
	return {
		"ma": phieu,
		"ten": d.get("ten_khoan_chi") or phieu,
		"noi_dung": noi_dung or phieu,
		"so_tien": tong,
		"trang_thai": d.trang_thai,
		"nguoi_tao": d.get("nguoi_tao") or "",
		"nguoi_ten": _ten_nguoi(d.get("nguoi_tao")),
		"ngay": str(d.get("ngay_can_tt") or "")[:10] or str(d.get("creation") or "")[:10],
		"dien_giai": d.get("dien_giai") or "",
		"ben_ban": d.get("nha_cung_cap") or "",
		"so_hoa_don": d.get("so_hoa_don") or "",
		"co_vat": 1 if (d.get("chung_tu_thue") or "").startswith("Có") else 0,
		"loai_chung_tu": (cac_dong[0]["loai_chung_tu"] if cac_dong else ""),
		"cac_dong": cac_dong,
		"tep": [{"ma": t["file"], "ten": t["ten"], "url": t["url"]} for t in tep],
	}


def _tep_hop_le(tep):
	"""Lọc danh sách tệp người dùng gửi lên, chỉ giữ mã còn thật trên máy chủ.

	Nhận cả ba dạng màn hình có thể gửi: chuỗi nhiều dòng, danh sách mã,
	danh sách {ma: ...}. Nhận rộng ở cửa vào để màn hình khỏi phải nhớ đúng
	một dạng, nhưng ra khỏi hàm này thì chỉ còn một dạng duy nhất.
	"""
	if isinstance(tep, str):
		try:
			tep = frappe.parse_json(tep)
		except Exception:
			tep = _tep_cua_dong(tep)
	if isinstance(tep, dict):
		tep = [tep]
	ra = []
	for t in (tep or []):
		ma = (t.get("ma") or t.get("file") or t.get("name")) if isinstance(t, dict) else t
		ma = str(ma or "").strip()
		if not ma or ma in ra:
			continue
		try:
			if frappe.db.exists("File", ma):
				ra.append(ma)
		except Exception:
			continue
	return ra


def _gan_tep_ve_ho_so(ten_ho_so, sach):
	"""Trỏ mọi tệp của mọi dòng về hồ sơ, và để chế độ riêng tư.

	Riêng tư là bắt buộc, không phải tuỳ chọn: hồ sơ thanh toán là giấy tờ
	tiền bạc, để công khai thì ai có đường dẫn cũng mở được.
	"""
	for d in (sach or []):
		for ma in _tep_cua_dong(d.get("tep")):
			try:
				frappe.db.set_value("File", ma, {
					"attached_to_doctype": "Vagabond Ho So TT",
					"attached_to_name": ten_ho_so,
					"is_private": 1,
				}, update_modified=False)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "ho_so_tt: gan tep dong ve ho so")


def _soi_phieu_noi_bo(sach, theo_tien=True):
	"""Soi các dòng có nối phiếu nội bộ TRƯỚC khi ghi. Ba việc, ba lý do.

	Trước 04/09/2026 máy chủ nhận thẳng `de_nghi_chi` và `so_tien` từ màn
	hình mà không đọc lại phiếu lần nào. Ba đường hỏng đi kèm:

	1. **Một phiếu nối vào hai dòng của cùng một hồ sơ.** Bảng chọn không
	   đánh dấu phiếu đã dùng ở dòng khác, nên chọn nhầm là chuyện thường.
	   Máy đè số tiền phiếu lên cả hai dòng, tổng hồ sơ dôi đúng một lần số
	   tiền phiếu. Người duyệt không nhìn ra vì màn hồ sơ không hiện mã phiếu.
	2. **Số tiền dòng khác số tiền phiếu.** Ô số tiền vẫn sửa tay tự do sau
	   khi nối, gõ thừa một số 0 trên điện thoại là hồ sơ đội lên mười lần mà
	   chứng từ đính kèm vẫn là bộ ảnh của phiếu số nhỏ. Gọi thẳng API thì
	   còn không có hàng rào nào cả.
	3. **Phiếu chưa qua duyệt.** `ds_phieu_noi_bo` và `xem_phieu_noi_bo` có
	   lọc trạng thái, nhưng cả hai đều là cửa XEM. Gọi thẳng API với mã một
	   phiếu còn nháp là lọt, đúng cái mà docstring của `ds_phieu_noi_bo` đã
	   cảnh báo: người lập tự viết phiếu rồi tự nối, cửa duyệt thành vô nghĩa.
	"""
	da_thay = {}
	for d in (sach or []):
		ma = (d.get("de_nghi_chi") or "").strip()
		if not ma:
			continue
		if ma in da_thay:
			frappe.throw(
				"Phiếu %s đang nối vào hai khoản trong cùng hồ sơ này. "
				"Mỗi phiếu chỉ được nối một lần, gỡ bớt một khoản đi." % ma
			)
		da_thay[ma] = 1
		r = frappe.db.get_value(
			DNC, ma, ["trang_thai", "tong_tien", "so_tien"], as_dict=True
		)
		if not r:
			frappe.throw("Không thấy phiếu thanh toán nội bộ %s." % ma)
		if r.get("trang_thai") not in TT_PHIEU_NOI_BO:
			frappe.throw(
				"Phiếu %s đang ở bước %s, chưa duyệt xong thì chưa nối vào hồ sơ được."
				% (ma, r.get("trang_thai") or "không rõ")
			)
		tien_phieu = flt(r.get("tong_tien")) or flt(r.get("so_tien"))
		if theo_tien and tien_phieu > 0 and abs(flt(d.get("so_tien")) - tien_phieu) > 1:
			frappe.throw(
				"Khoản nối phiếu %s ghi %s đ nhưng phiếu ghi %s đ. "
				"Số tiền phải bằng đúng số của phiếu."
				% (ma, _tien(d.get("so_tien")), _tien(tien_phieu))
			)


def _dap_tep_phieu_noi_bo(doc):
	"""Kéo tệp chứng từ của phiếu nội bộ sang dòng đã nối nó.

	Người lập nối phiếu vào một dòng hoá đơn là để nói "khoản này nhân viên
	đã ứng tiền mua, đây là phiếu". Bộ ảnh hoá đơn bán lẻ, phiếu thu, sao kê
	nằm bên phiếu; không kéo sang thì người duyệt phải mở hai màn để đối
	chiếu một khoản, và bản in bộ hồ sơ thiếu đúng phần chứng minh đó.

	GIỮ tệp sẵn có của dòng, chỉ THÊM tệp của phiếu vào sau, không đè.
	"""
	co_doi = 0
	for d in (doc.dong or []):
		ma = (getattr(d, "de_nghi_chi", "") or "").strip()
		if not ma:
			continue
		try:
			them = [t["file"] for t in _dinh_kem([(DNC, ma)]) if t.get("file")]
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ho_so_tt: dap tep phieu noi bo")
			continue
		cu = _tep_cua_dong(d.tep)
		moi = cu + [m for m in them if m not in cu]
		if moi != cu:
			d.tep = "\n".join(moi)
			co_doi = 1
	if co_doi:
		doc.flags.ignore_permissions = True
		doc.save(ignore_permissions=True)
		_gan_tep_ve_ho_so(doc.name, [{"tep": d.tep} for d in (doc.dong or [])])


def _khoa_phieu_noi_bo(ten_ho_so, sach):
	"""Đóng dấu hồ sơ lên phiếu nội bộ đã nối, để không ai nối lại lần hai.

	Đây là chốt chặn THỨ HAI. Chốt thứ nhất nằm ở `ds_phieu_noi_bo` và
	`xem_phieu_noi_bo`, nhưng hai người lập hai hồ sơ cùng lúc thì cả hai đều
	thấy phiếu còn trống. Chốt ở đây chạy lúc ghi, nên người sau ghi đè lên
	người trước là lộ ra ngay ở nhật ký.
	"""
	for d in (sach or []):
		ma = (d.get("de_nghi_chi") or "").strip()
		if not ma:
			continue
		cu = frappe.db.get_value(DNC, ma, "ho_so_tt")
		if cu and cu != ten_ho_so:
			# DUNG HAN, khong di tiep.
			#
			# Truoc 04/09/2026 cho nay chi ghi Error Log roi `continue`. Ma
			# ham nay chay SAU doc.insert va TRUOC frappe.db.commit, nen ho
			# so cua nguoi sau van ra doi day du, van mang dong so tien do,
			# van di qua hai cap duyet ngon lanh. Hai to nhin rieng deu hop
			# le, khong ai doi chieu, va cong ty chi hai lan cho mot khoan.
			# Nhat ky thi khong ai doc.
			#
			# Nem loi o day thi Frappe cuon nguoc ca ban ghi ho so vua chen.
			frappe.throw(
				"Phiếu %s đã nằm trong hồ sơ %s rồi, không nối lần nữa được. "
				"Có người vừa lập hồ sơ với phiếu này trước bạn một nhịp. "
				"Mở lại bảng chọn phiếu để lấy danh sách mới." % (ma, cu)
			)
		# Dong dau KHONG boc try/except: dong dau hong ma van cho ho so ra
		# doi thi phieu van hien trong bang chon va noi duoc vao ho so thu
		# hai, tuc lai chi hai lan. Tha hong han con hon hong nua voi.
		frappe.db.set_value(DNC, ma, "ho_so_tt", ten_ho_so, update_modified=False)


@frappe.whitelist()
def dinh_tep_dong(name=None, dong=None, tep=None):
	"""Đính thêm tệp cho MỘT dòng của hồ sơ đã lập.

	Dùng khi kế toán mở hồ sơ ra và thấy khoản nào còn thiếu giấy tờ. Lúc
	đang lập thì màn hình giữ tệp trong bộ nhớ rồi gửi một lượt qua
	`tao_hoan_ung`, không đi đường này.

	`dong` đếm từ 1 cho khớp cột STT người dùng nhìn thấy trên màn và trên
	bản in. Đếm từ 0 ở đây là mời gọi lệch một dòng.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "đính tệp vào khoản chi")
	if not frappe.db.exists("Vagabond Ho So TT", name):
		frappe.throw("Không tìm thấy hồ sơ %s." % name)
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	if doc.trang_thai in (TT_HUY, TT_TU_CHOI):
		frappe.throw(
			"Hồ sơ %s đã %s nên không đính thêm giấy tờ được."
			% (name, NHAN.get(doc.trang_thai, doc.trang_thai).lower())
		)
	i = cint(dong)
	if i < 1 or i > len(doc.dong):
		frappe.throw("Hồ sơ %s không có khoản số %s." % (name, dong))
	ma_moi = _tep_hop_le(tep)
	if not ma_moi:
		frappe.throw("Tệp gửi lên không còn trên máy chủ. Vui lòng chọn tệp rồi đính lại.")
	d = doc.dong[i - 1]
	da_co = _tep_cua_dong(d.tep)
	d.tep = "\n".join(da_co + [m for m in ma_moi if m not in da_co])
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	_gan_tep_ve_ho_so(name, [{"tep": d.tep}])
	try:
		doc.add_comment("Comment", "Đính %d tệp chứng từ cho khoản số %d." % (len(ma_moi), i))
	except Exception:
		pass
	frappe.db.commit()
	return {"ok": 1, "dong": i, "tep": _ho_tep(_tep_cua_dong(d.tep))}


@frappe.whitelist()
def go_tep_dong(name=None, dong=None, tep=None):
	"""Gỡ một tệp khỏi một dòng. KHÔNG xoá tệp, chỉ bỏ khỏi dòng đó."""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "gỡ tệp khỏi khoản chi")
	if not frappe.db.exists("Vagabond Ho So TT", name):
		frappe.throw("Không tìm thấy hồ sơ %s." % name)
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	# CUA DAN CHUNG TU KHONG DUOC MO SAU KHI DA DUYET.
	#
	# `dinh_tep_dong` co chan, rieng ham nay truoc 04/09/2026 khong kiem
	# trang thai mot dong nao. Nghia la go duoc anh chung tu khoi mot ho so
	# da duyet xong hoac da chi tien, tuc xoa dau vet giai trinh cua mot lan
	# tien that di ra, ma cung khong ghi vet lai.
	if doc.trang_thai in (TT_DA_DUYET, TT_DA_TRA):
		frappe.throw(
			"Hồ sơ đang ở %s, không gỡ chứng từ ra được nữa. "
			"Bộ hồ sơ là giải trình của một lần chuyển tiền, gỡ một tờ ra là "
			"làm thủng bộ đó." % NHAN.get(doc.trang_thai, doc.trang_thai)
		)
	i = cint(dong)
	if i < 1 or i > len(doc.dong):
		frappe.throw("Hồ sơ %s không có khoản số %s." % (name, dong))
	d = doc.dong[i - 1]
	con = [m for m in _tep_cua_dong(d.tep) if m != str(tep or "").strip()]
	d.tep = "\n".join(con)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	_ghi_vet(name, "Gỡ chứng từ khỏi khoản %s bởi %s" % (i, frappe.session.user))
	return {"ok": 1, "dong": i, "tep": _ho_tep(con)}


# ------------------------------------------------------- Dàn trang ảnh 2x2


# Bốn ảnh một trang A4, xếp 2 cột 2 dòng.
#
# Anh Việt 22/08/2026: *"yêu cầu bắt buộc là phải tiết kiệm giấy và chuẩn
# form mẫu... ép các ảnh này hiển thị 4 ảnh / 1 trang A4"*.
#
# Trước đây mỗi ảnh chiếm trọn một trang. Một hồ sơ hoàn ứng ba chục khoản
# là ba chục tờ giấy cho phần ảnh, kế toán in ra kẹp không nổi.
#
# Vì sao dùng BẢNG chứ không CSS Grid hay Flexbox, dù đề bài nói Grid:
# bản in đi qua wkhtmltopdf, engine WebKit đời cũ. Grid gần như không được
# hỗ trợ và Flexbox thì vỡ chỗ ngắt trang - ô cuối bị cắt đôi giữa hai
# trang. Bảng hai cột hai dòng cho ra đúng bố cục ấy và ngắt trang chuẩn.
# Đây là chỗ phải chọn cái CHẠY ĐƯỢC trên máy in thật thay vì cái đúng sách.
#
# Khung mỗi ô cao cố định, ảnh đặt `max-width`/`max-height` 100% nên ảnh
# đứng hay ảnh ngang đều co vừa khung mà KHÔNG méo, không tràn viền.

ANH_MOI_TRANG = 4

# PHEP TINH CHIEU CAO, doc truoc khi chinh mot con so nao o day.
#
# Vung in A4 doc sau le 15mm hai dau la 267mm. Mot trang luoi day du gom:
#     tieu de "CHUNG TU DINH KEM"        ~14mm  (chi co o trang dau)
#     2 hang x (khung anh + dem 6mm + nhan)
# Nay: 90 + 6 + 14 = 110mm moi hang, 2 hang 220mm, cong tieu de la 234mm
# tren 267mm. Du 33mm.
#
# Ban v281 lay 104mm nen mot hang thanh 120mm, hai hang 240mm, cong tieu de
# la 254mm - CHI CON 13mm du. Sat qua. May cua anh Viet no tran, wkhtmltopdf
# day hang thu hai sang trang moi, thanh 2 anh mot trang va nua duoi to giay
# bo trang. Do la loi anh Viet bao ngay 23/08/2026: *"cac anh van xep doc,
# de lai nhung khoang trang khong lo gay lang phi giay"*.
#
# BAI HOC: bo cuc in KHONG duoc vua khit. Moi ban wkhtmltopdf tinh le mot
# kieu, phai chua du rong rai thi moi may deu ra dung.
CAO_O_ANH = "90mm"

# Trang chi co MOT hang thi cho hang do cao gan het trang, dung de nua duoi
# trang tron. Van chua cho cho nhan nen khong lay tron 267mm.
CAO_O_1_HANG = "205mm"

# Chieu cao danh cho dong nhan duoi anh. Dat CO DINH de chieu cao mot hang
# doan truoc duoc, khong phu thuoc ten tep dai hay ngan.
CAO_NHAN = "14mm"
DUOI_ANH = ("jpg", "jpeg", "png", "gif", "bmp", "webp")


def _noi_tep(ma_tep):
	"""Đọc nội dung thô một tệp File thành bytes. Rỗng nếu đọc không được."""
	try:
		noi = frappe.get_doc("File", ma_tep).get_content()
		if isinstance(noi, str):
			noi = noi.encode("utf-8")
		return noi or b""
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: doc tep %s" % ma_tep)
		return b""


def _anh_b64(ma_tep):
	"""Đọc một tệp ảnh thành chuỗi base64 nhúng thẳng vào HTML.

	Nhúng thẳng thay vì để đường dẫn: tệp để riêng tư, mà wkhtmltopdf gọi
	lại máy chủ thì KHÔNG mang theo phiên đăng nhập nên tải về ảnh rỗng.
	Đã mất một buổi vì đúng chỗ này.
	"""
	try:
		noi = frappe.get_doc("File", ma_tep).get_content()
		if isinstance(noi, str):
			noi = noi.encode("utf-8")
		return base64.b64encode(noi).decode()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: doc anh %s" % ma_tep)
		return ""


# ---------------------------------------------------------------- PDF -> anh
#
# Anh Viet 23/08/2026: *"he thong dang khong in duoc 'Ban the hien hoa don'
# vi no la dinh dang PDF"*.
#
# Vi sao phai rasterize o MAY CHU
# --------------------------------
# wkhtmltopdf dung mot tep PDF vao giua mot tep PDF khac thi khong lam duoc:
# no chi biet dung HTML. Ban truoc vi vay phai NOI cac PDF dinh kem vao cuoi
# bo ho so bang pypdf, moi to mot trang nguyen kho A4 - mot to hoa don chiem
# tron mot mat giay du noi dung chi bang mot phan tu.
#
# Doi tung trang PDF thanh anh roi tha vao luoi 2x2 thi bon to an mot mat
# giay, va quan trong hon la ban the hien hoa don CUOI CUNG cung vao duoc bo
# ho so thay vi bi bo lai.
#
# Vi sao thu nhieu thu vien
# -------------------------
# PyMuPDF la banh xe thuan, khong can goi he dieu hanh, nen chay duoc tren
# may Frappe Cloud. pdf2image thi phai co binary poppler cua he dieu hanh,
# thuong VANG MAT tren anh Docker cua Frappe Cloud - de o day lam duong lui
# chu khong dat lam duong chinh. Khong co thu vien nao thi tra ve rong va
# ben goi tu quay ve loi cu la noi ca tep PDF vao cuoi, khong mat to nao.

# Do phan giai khi rasterize. 150 dpi du sac de doc so tien tren hoa don ma
# tep khong phinh to; 72 dpi thi con dau va chu ky nhoe thanh vet muc.
DPI_RASTER = 150

# Tran so trang doi tu MOT tep PDF. Mot ban ke ngan hang vai chuc trang lot
# vao day se lam bo ho so phinh ra va may chu ngoi ve anh ca phut.
TRANG_TOI_DA_MOI_PDF = 12


def _nap_pymupdf():
	"""Nạp PyMuPDF, thử tên mới trước tên cũ. None nếu máy không có.

	Bản mới của thư viện đổi tên mô đun thành `pymupdf` và đã in cảnh báo
	"the fitz API is deprecated" cho tên cũ. Thử tên mới trước thì hôm thư
	viện bỏ hẳn tên cũ, bản in vẫn chạy chứ không im lặng rơi về đường lui.
	"""
	try:
		import pymupdf

		return pymupdf
	except Exception:
		pass
	try:
		import fitz

		return fitz
	except Exception:
		return None


def _thu_vien_raster():
	"""Tên thư viện rasterize đang dùng được, hoặc chuỗi rỗng. Không ném lỗi."""
	if _nap_pymupdf() is not None:
		return "pymupdf"
	try:
		import pdf2image  # noqa: F401

		return "pdf2image"
	except Exception:
		pass
	return ""


def _pdf_ra_anh(noi_dung, toi_da=TRANG_TOI_DA_MOI_PDF, dpi=DPI_RASTER):
	"""Một tệp PDF -> danh sách ảnh PNG base64, mỗi trang một ảnh.

	Trả về danh sách RỖNG khi môi trường không có thư viện nào, để bên gọi
	quay về đường cũ. KHÔNG ném lỗi ra ngoài: xuất hồ sơ mà chết giữa chừng
	vì một tệp đính kèm hỏng thì kế toán mất cả bộ, tệ hơn nhiều so với
	thiếu một tờ và có dòng ghi rõ là thiếu.
	"""
	ten = _thu_vien_raster()
	if not ten:
		return []
	try:
		if ten == "pymupdf":
			mu = _nap_pymupdf()
			ra = []
			tap = mu.open(stream=noi_dung, filetype="pdf")
			try:
				for so, trang in enumerate(tap):
					if so >= toi_da:
						break
					px = trang.get_pixmap(dpi=dpi)
					ra.append(base64.b64encode(px.tobytes("png")).decode())
			finally:
				tap.close()
			return ra

		from pdf2image import convert_from_bytes

		ra = []
		for so, hinh in enumerate(convert_from_bytes(noi_dung, dpi=dpi)):
			if so >= toi_da:
				break
			bo = io.BytesIO()
			hinh.save(bo, format="PNG")
			ra.append(base64.b64encode(bo.getvalue()).decode())
		return ra
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: rasterize PDF")
		return []


def _o_anh(x, cao_o, ca_hang=False):
	"""Dựng MỘT ô ảnh kèm dòng nhãn. Hàm THUẦN, không chạm Frappe.

	Ba điều bắt buộc, đừng gỡ cái nào:

	1. Ảnh và nhãn nằm trong CÙNG MỘT khối `page-break-inside:avoid`. Nếu để
	   thành hai khối anh em thì trình in được phép ngắt trang GIỮA chúng.
	   Ngày 23/08/2026 đã ra đúng lỗi đó: ảnh IMG_2710 ở trang 6, dòng nhãn
	   của nó rơi sang trang 7 một mình.

	2. KHÔNG dùng `display:table-cell` cho div bên trong `<td>`. Div mang
	   display:table-cell mà không nằm trong table là cấu trúc không hợp lệ,
	   trình duyệt phải tự dựng bảng ẩn bao quanh, và WebKit đời cũ trong
	   wkhtmltopdf tính chiều cao khối ẩn đó theo cỡ THẬT của ảnh chứ không
	   theo cỡ đã co. Ảnh chụp điện thoại 4032px thành một khối cao vô lý,
	   đẩy hàng thứ hai sang trang mới. Canh giữa dọc bằng `line-height`
	   bằng đúng chiều cao khung, cách này wkhtmltopdf hiểu chắc chắn.

	3. Nhãn có chiều cao CỐ ĐỊNH và `word-break`, để một tên tệp dài không
	   tự ý kéo hàng cao thêm rồi làm vỡ phép tính chỗ.
	"""
	h = frappe.utils.escape_html
	return (
		'<td %sstyle="width:%s;padding:3mm;vertical-align:top;'
		'border:1px solid #e3ded7">'
		# Mot khoi duy nhat: anh va nhan khong bao gio tach trang.
		'<div style="page-break-inside:avoid">'
		'<div style="height:%s;line-height:%s;text-align:center">'
		'<img src="data:image/%s;base64,%s" '
		'style="max-width:100%%;max-height:%s;object-fit:contain;vertical-align:middle">'
		"</div>"
		'<div style="height:%s;overflow:hidden;font-size:9px;color:#555;'
		'margin-top:2mm;line-height:1.35;word-break:break-word">%s</div>'
		"</div></td>"
		% (
			'colspan="2" ' if ca_hang else "",
			"100%" if ca_hang else "50%",
			cao_o, cao_o,
			x.get("kieu") or "jpeg", x.get("b64") or "",
			cao_o,
			CAO_NHAN, h(x.get("nhan") or ""),
		)
	)


def luoi_anh(anh, moi_trang=ANH_MOI_TRANG):
	"""Xếp danh sách ảnh thành các trang lưới 2x2.

	anh: [{"b64":..., "kieu":"jpeg", "nhan": "Khoản 3 · bill điện"}]

	Trả về HTML đã kèm sẵn ngắt trang giữa các trang. Hàm THUẦN, không chạm
	Frappe, nên kiểm thử được không cần site.

	Dùng BẢNG hai cột chứ không CSS Grid hay Flexbox: bản in đi qua
	wkhtmltopdf (Print Settings của tiệm đang đặt wkhtmltopdf, đã kiểm ngày
	23/08/2026), engine WebKit đời cũ gần như không hỗ trợ Grid, còn Flexbox
	thì vỡ chỗ ngắt trang.
	"""
	if not anh:
		return ""
	trang = []
	for i in range(0, len(anh), moi_trang):
		lo = anh[i:i + moi_trang]
		# Chieu cao o tinh theo SO HANG THAT cua trang nay, khong dong cung.
		# Trang chi co mot hang thi cho hang do cao gan het trang - anh to ra,
		# giay khong phi met nao.
		so_hang = (len(lo) + 1) // 2
		cao_o = CAO_O_1_HANG if so_hang == 1 else CAO_O_ANH
		le = len(lo) % 2
		hang = ""
		for j in range(0, len(lo) - le, 2):
			hang += "<tr>" + _o_anh(lo[j], cao_o) + _o_anh(lo[j + 1], cao_o) + "</tr>"
		# Le mot anh thi cho no chiem CA HANG thay vi de mot o trong ben canh.
		# O trong ben canh mot to hoa don la mot nua mat giay khong in gi.
		if le:
			hang += "<tr>" + _o_anh(lo[-1], cao_o, ca_hang=True) + "</tr>"
		trang.append(
			'<div style="%s">'
			'<table style="width:100%%;border-collapse:collapse;table-layout:fixed">'
			% ("page-break-before:always" if i else "")
			+ hang + "</table></div>"
		)
	return "".join(trang)


def _gom_anh_ho_so(d):
	"""Gom mọi ảnh của một hồ sơ, mỗi ảnh mang theo nhãn nói rõ nó của đâu.

	Anh Việt 22/08/2026: *"Dưới mỗi ảnh đính kèm trong file PDF, in thêm một
	dòng text nhỏ ghi rõ ảnh này thuộc khoản chi nào (STT dòng hàng) để Kế
	toán dễ đối chiếu"*.

	Thứ tự gom là thứ tự đọc: hết ảnh của khoản 1 rồi mới sang khoản 2, cuối
	cùng mới tới giấy tờ đính chung cho cả hồ sơ. Ảnh trùng chỉ lấy một lần.
	"""
	h = frappe.utils.escape_html
	anh, da_lay, bo_qua = [], set(), []

	def _nap(f, nhan):
		ma = f.get("file")
		if not ma or ma in da_lay:
			return
		da_lay.add(ma)
		ten = f.get("ten") or ma
		duoi = ten.rsplit(".", 1)[-1].lower() if "." in ten else ""
		# Giu ca MA File that: khuc ghep PDF o duoi doc noi dung tep bang ma
		# nay. Chi giu ten hien thi la ghep hong ma khong ai biet vi sao.
		if duoi == "pdf":
			# Ban the hien hoa don gan nhu luon la PDF. Doi tung trang thanh
			# anh de no vao duoc luoi 2x2 nhu moi anh chup khac. Doi khong
			# duoc (may thieu thu vien, tep hong) thi tra ve bo_qua va ben goi
			# noi nguyen ca tep vao cuoi bo ho so nhu duong cu - khong bao gio
			# im lang lam mat mot to.
			trang = _pdf_ra_anh(_noi_tep(ma))
			if not trang:
				bo_qua.append({"file": ma, "ten": ten, "nhan": nhan, "duoi": duoi})
				return
			nhieu = len(trang) > 1
			for so, b64 in enumerate(trang, 1):
				anh.append({
					"b64": b64,
					"kieu": "png",
					"nhan": "%s · %s%s" % (nhan, ten, (" (trang %d/%d)" % (so, len(trang))) if nhieu else ""),
				})
			return
		if duoi not in DUOI_ANH:
			bo_qua.append({"file": ma, "ten": ten, "nhan": nhan, "duoi": duoi})
			return
		b64 = _anh_b64(ma)
		if not b64:
			bo_qua.append({"file": ma, "ten": ten, "nhan": nhan, "duoi": duoi})
			return
		anh.append({
			"b64": b64,
			"kieu": "png" if duoi == "png" else ("gif" if duoi == "gif" else "jpeg"),
			"nhan": "%s · %s" % (nhan, ten),
		})

	for i, x in enumerate(d["dong"], 1):
		# Nhan phai co STT dong, do la ca ly do dong nhan nay ton tai.
		goc = "Khoản %d" % i
		mo_ta = (x.get("noi_dung") or "").strip()
		if mo_ta:
			goc += ": " + mo_ta[:48]
		if x.get("loai_chung_tu"):
			goc += " [%s]" % x["loai_chung_tu"]
		if x.get("de_nghi_chi"):
			goc += " (phiếu %s)" % x["de_nghi_chi"]
		for f in (x.get("tep_dong") or []):
			_nap(f, goc)
		for f in (x.get("scan") or []):
			_nap(f, goc + " · kèm hoá đơn mua")
	for f in (d.get("ho_so_dinh_kem") or []):
		_nap(f, "Đính chung cả hồ sơ")
	return anh, bo_qua


# ============================================================================
# XOÁ MỘT DÒNG KHỎI HỒ SƠ - quy tắc chung, mọi màn đều phải có
# ============================================================================
#
# Anh Việt 22/08/2026: *"Em cho anh thêm nút xoá cái dòng nữa để có thể xoá
# dòng nếu add nhầm. Em viết hẳn phần này vào backend để tất cả các nơi đều
# phải có dòng xoá để xoá khi thao tác sai rồi mới chốt phiếu."*
#
# Vì sao phải là một cửa CHUNG ở backend chứ không phải mỗi màn tự cắt mảng
# của mình: thêm nhầm một dòng là chuyện xảy ra hàng ngày, mà hồ sơ đã lập
# rồi thì mảng nằm trong cơ sở dữ liệu chứ không còn trong bộ nhớ màn hình.
# Mỗi màn tự xoá kiểu của mình thì sớm muộn có màn quên trừ lại tổng tiền,
# quên gỡ tệp, hoặc cho xoá cả hồ sơ đã duyệt.
#
# Ba điều cửa này giữ, và giữ ở MỘT chỗ:
#
#   1. Chỉ xoá được khi hồ sơ CHƯA qua cửa duyệt nào. Hồ sơ đã gửi kế toán
#      mà người lập vẫn rút dòng ra được thì con số chị Dung nhìn lúc duyệt
#      không còn là con số được duyệt.
#   2. Xoá dòng cuối cùng là xoá hết ruột hồ sơ, chặn - bảo người ta huỷ cả
#      hồ sơ cho rõ ràng, đừng để lại một cái vỏ rỗng trong danh sách.
#   3. Dòng có nối phiếu nội bộ thì TRẢ phiếu đó về trạng thái chưa nối,
#      không thì phiếu kẹt vĩnh viễn, không hồ sơ nào nối lại được.

# Trạng thái còn được sửa ruột hồ sơ. Cố ý chỉ có Nháp và Bị trả lại.
TT_SUA_DUOC_RUOT = (TT_NHAP, TT_TU_CHOI)


def _kiem_sua_duoc_ruot(doc, viec="xoá khoản chi"):
	"""Hồ sơ này còn cho sửa ruột không. Dùng chung cho mọi thao tác cắt dòng."""
	if doc.trang_thai not in TT_SUA_DUOC_RUOT:
		frappe.throw(
			"Hồ sơ %s đang ở trạng thái \"%s\" nên không %s được nữa.\n\n"
			"Hồ sơ đã gửi đi duyệt thì con số phải đứng yên, không thì cái "
			"kế toán duyệt không còn là cái người lập gửi. Muốn sửa thì nhờ "
			"kế toán trả lại hồ sơ, hoặc huỷ rồi lập tờ mới."
			% (doc.name, NHAN.get(doc.trang_thai, doc.trang_thai), viec)
		)


def _tra_phieu_noi_bo(ma_phieu, ten_ho_so):
	"""Cắt dòng có nối phiếu nội bộ thì trả phiếu về trạng thái chưa nối.

	Bỏ bước này là phiếu kẹt vĩnh viễn: nó mang mã một hồ sơ không còn dòng
	nào của nó, mà `ds_phieu_noi_bo` lại lọc bỏ mọi phiếu đã có hồ sơ. Không
	ai nối lại được và cũng không ai hiểu vì sao.
	"""
	ma_phieu = (ma_phieu or "").strip()
	if not ma_phieu:
		return
	try:
		if frappe.db.get_value(DNC, ma_phieu, "ho_so_tt") != ten_ho_so:
			return
		# CON DONG NAO KHAC CUA CHINH HO SO NAY DANG GIU PHIEU THI DUNG NHA.
		#
		# Mot phieu co the bi noi vao hai dong cua cung mot ho so (bang chon
		# khong danh dau phieu da dung o dong khac). Xoa mot trong hai dong
		# ma nha phieu ra la phieu quay lai bang chon trong khi dong kia van
		# dang giu no, roi noi tiep vao mot ho so thu hai. Luc do khong lop
		# nao biet gi ca.
		# SQL thang, dung nep `_gd_da_gom`. `frappe.db.count` tren bang CON
		# di qua tang quyen cua Frappe va da tung hong voi doctype con, mà
		# hong o day thi phieu khong bao gio duoc nha - dung cai benh minh
		# vua chua. Cau nay thi khong the hong vi ly do do.
		con = frappe.db.sql(
			"""select count(*) from `tabVagabond Ho So TT Dong`
			where parent = %s and parenttype = 'Vagabond Ho So TT'
			and ifnull(de_nghi_chi, '') = %s""",
			(ten_ho_so, ma_phieu),
		)
		if con and cint(con[0][0]) > 0:
			return
		frappe.db.set_value(DNC, ma_phieu, "ho_so_tt", None, update_modified=False)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: tra phieu noi bo khi xoa dong")


@frappe.whitelist()
def xoa_dong(name=None, dong=None):
	"""Xoá một khoản chi khỏi hồ sơ đã lập.

	`dong` đếm từ 1 cho khớp cột STT trên màn và trên bản in.

	KHÔNG xoá tệp khỏi máy chủ, chỉ bỏ dòng. Tệp đính nhầm thì gỡ bằng
	`go_tep_dong`; xoá thẳng tệp ở đây thì người lập bấm nhầm một cái là mất
	ảnh chứng từ không lấy lại được.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xoá khoản chi khỏi hồ sơ")
	if not frappe.db.exists("Vagabond Ho So TT", name):
		frappe.throw("Không tìm thấy hồ sơ %s." % name)
	doc = frappe.get_doc("Vagabond Ho So TT", name)
	_kiem_sua_duoc_ruot(doc, "xoá khoản chi")
	i = cint(dong)
	if i < 1 or i > len(doc.dong):
		frappe.throw("Hồ sơ %s không có khoản số %s." % (name, dong))
	if len(doc.dong) <= 1:
		frappe.throw(
			"Đây là khoản cuối cùng của hồ sơ %s. Xoá nốt thì còn lại một hồ "
			"sơ rỗng nằm trong danh sách mà không ai biết để làm gì.\n\n"
			"Muốn bỏ hẳn thì huỷ cả hồ sơ." % name
		)
	d = doc.dong[i - 1]
	mo_ta = (d.noi_dung or "").strip() or "khoản số %d" % i
	so_tien = flt(d.so_tien)
	phieu = (d.get("de_nghi_chi") or "").strip()
	doc.remove(d)
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	_tra_phieu_noi_bo(phieu, name)
	try:
		doc.add_comment(
			"Comment",
			"Xoá khoản số %d: %s (%s đ)%s."
			% (i, mo_ta, _tien(so_tien), ", trả lại phiếu %s" % phieu if phieu else ""),
		)
	except Exception:
		pass
	frappe.db.commit()
	return {
		"ok": 1,
		"da_xoa": mo_ta,
		"con_lai": len(doc.dong),
		"tong_tien": flt(doc.tong_tien),
		"ghi_chu": "Đã xoá %s khỏi hồ sơ %s." % (mo_ta, name),
	}


# ============================================================================
# HÀNG RÀO CHỨNG TỪ: khoản từ 200.000đ trở lên phải có giấy tờ
# ============================================================================
#
# Anh Việt chốt 22/08/2026: *"em cho chặn luôn lúc lập gửi kế toán nhé, và
# ngưỡng tiền miễn trừ là 200k anh đồng ý"*.
#
# Từ đây "siết hồ sơ" không còn là lời nhắc trên màn mà là hàng rào thật:
# thiếu giấy tờ thì máy không cho gửi.
#
# Vì sao có ngưỡng miễn trừ: chặt đều tay mọi khoản thì Uyên phải chụp cả
# hoá đơn gửi xe 5.000đ. Công sức bỏ ra không đáng với rủi ro chặn được, mà
# quy trình nào phiền quá thì người ta tìm đường đi vòng - lúc đó mất cả
# những khoản đáng lẽ chặn được.
#
# Vì sao chặn lúc GỬI chứ không lúc lưu nháp: nháp là chỗ làm dở. Bắt đủ
# giấy tờ ngay từ khi gõ dòng đầu thì không ai lưu nháp được nữa, mà nháp
# chính là thứ giữ cho người ta khỏi phải làm một lèo trong một lần ngồi.

NGUONG_MIEN_CHUNG_TU = 200000.0


def thieu_chung_tu(dong, dm=None, nguong=NGUONG_MIEN_CHUNG_TU):
	"""Những khoản chưa đủ giấy tờ để gửi đi duyệt.

	Hàm THUẦN: không chạm Frappe, nhận sẵn danh mục qua `dm` nên kiểm thử
	được mà không cần site.

	dong: [{noi_dung, so_tien, loai_chung_tu, tep}] - `tep` là danh sách mã
	tệp hoặc chuỗi nhiều dòng.
	dm:   {ten loại chứng từ: {"bat_buoc_tep": 0/1}}

	Trả về danh sách {stt, noi_dung, so_tien, vi_sao}.
	"""
	dm = dm or {}
	ra = []
	for i, x in enumerate(dong or [], 1):
		tien = flt((x or {}).get("so_tien"))
		if tien < flt(nguong):
			continue
		loai = str((x or {}).get("loai_chung_tu") or "").strip()
		tep = (x or {}).get("tep")
		if isinstance(tep, str):
			tep = _tep_cua_dong(tep)
		co_tep = len([t for t in (tep or []) if t])
		mo_ta = str((x or {}).get("noi_dung") or "").strip() or "khoản số %d" % i
		if not loai:
			ra.append({
				"stt": i, "noi_dung": mo_ta, "so_tien": tien,
				"vi_sao": "chưa chọn loại chứng từ",
			})
			continue
		# Loai chung tu nao khai "bat buoc tep" thi phai co tep that. Loai
		# khong bat buoc (Bang ke khong hoa don, Khong co chung tu) van qua
		# duoc - do la cua thoat co chu dinh cho khoan that su khong co giay.
		if cint((dm.get(loai) or {}).get("bat_buoc_tep")) and not co_tep:
			ra.append({
				"stt": i, "noi_dung": mo_ta, "so_tien": tien,
				"vi_sao": 'loại "%s" bắt buộc có tệp chứng từ nhưng chưa đính' % loai,
			})
	return ra


# Trang thai coi la HO SO CON SONG, tuc hoa don trong do dang tren duong di
# lay tien. Chi Tu choi va Huy la chet han, hoa don trong do duoc dung lai.
TT_CON_SONG = (TT_NHAP, TT_CHO_FIN, TT_CHO_GD, TT_DA_DUYET, TT_DA_TRA)


def ho_so_dang_giu(ds_hoa_don, tru_ho_so=""):
	"""Hoá đơn nào trong danh sách đã nằm ở một hồ sơ CÒN SỐNG khác.

	Trả về {mã hoá đơn: [(mã hồ sơ, trạng thái), ...]}. Hàm tra cơ sở dữ
	liệu, ca kiểm gọi qua lớp giả lập.

	`tru_ho_so`: bỏ qua chính hồ sơ đang sửa, nếu không thì sửa lại hồ sơ cũ
	là tự nó báo trùng với chính nó.
	"""
	ds = [str(x or "").strip() for x in (ds_hoa_don or []) if str(x or "").strip()]
	if not ds:
		return {}
	dong = frappe.get_all(
		"Vagabond Ho So TT Dong",
		filters={"hoa_don": ["in", ds], "parenttype": "Vagabond Ho So TT"},
		fields=["hoa_don", "parent"],
		limit_page_length=0,
	)
	if not dong:
		return {}
	cha = {d["parent"] for d in dong if d["parent"] != tru_ho_so}
	if not cha:
		return {}
	tt = {
		r["name"]: r["trang_thai"]
		for r in frappe.get_all(
			"Vagabond Ho So TT",
			filters={"name": ["in", list(cha)], "trang_thai": ["in", list(TT_CON_SONG)]},
			fields=["name", "trang_thai"],
			limit_page_length=0,
		)
	}
	ra = {}
	for d in dong:
		if d["parent"] == tru_ho_so or d["parent"] not in tt:
			continue
		ra.setdefault(d["hoa_don"], []).append((d["parent"], tt[d["parent"]]))
	return ra


def _chan_hoa_don_trung(dong, tru_ho_so=""):
	"""Ném lỗi nếu một hoá đơn đã nằm trong hồ sơ khác còn sống.

	VÌ SAO CHẶN CỨNG CHỨ KHÔNG CHỈ CẢNH BÁO
	----------------------------------------
	Hai hồ sơ cùng chứa một hoá đơn thì cùng đi qua hai cấp duyệt và cùng
	được chuyển tiền, vì mỗi hồ sơ nhìn riêng ra đều hợp lệ. Không ai đối
	chiếu chéo giữa các hồ sơ bằng mắt. Sai này chỉ lộ khi nhà cung cấp báo
	thừa tiền, hoặc không lộ.

	Giao dịch SePay đã có chốt cùng kiểu từ trước (`Giao dịch %s đã nằm
	trong hồ sơ %s`), hoá đơn thì chưa - đây là chỗ trống, không phải quyết
	định có chủ đích.

	Hồ sơ Từ chối và Huỷ KHÔNG chặn: hoá đơn trong đó phải dùng lại được,
	nếu không thì một lần lập nhầm là hoá đơn kẹt vĩnh viễn.
	"""
	ds = [str((x or {}).get("hoa_don") or "").strip() for x in (dong or [])]
	giu = ho_so_dang_giu([x for x in ds if x], tru_ho_so)
	if not giu:
		return
	dong_loi = "\n".join(
		"  · Hoá đơn %s đã nằm trong hồ sơ %s (%s)"
		% (hd, o[0][0], NHAN.get(o[0][1], o[0][1]))
		for hd, o in sorted(giu.items())
	)
	frappe.throw(
		"Không lập được hồ sơ: có hoá đơn đang nằm ở hồ sơ khác.\n\n%s\n\n"
		"Trả tiền hai lần cho một hoá đơn thì rất khó đòi lại. Gỡ hoá đơn đó "
		"ra khỏi hồ sơ này, hoặc huỷ hồ sơ kia trước." % dong_loi
	)


def _chan_thieu_chung_tu(dong):
	"""Ném lỗi nếu còn khoản chưa đủ giấy tờ. Gọi ngay trước khi gửi đi duyệt."""
	try:
		from vagabond.de_nghi_chi import _dm_chung_tu

		dm = _dm_chung_tu()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: doc danh muc de chan chung tu")
		return
	thieu = thieu_chung_tu(dong, dm)
	if not thieu:
		return
	dong_loi = "\n".join(
		"  · Khoản %d - %s (%s đ): %s" % (t["stt"], t["noi_dung"], _tien(t["so_tien"]), t["vi_sao"])
		for t in thieu
	)
	frappe.throw(
		"Chưa gửi được. %d khoản từ %s đ trở lên còn thiếu chứng từ:\n\n%s\n\n"
		"Kế toán trưởng chốt 22/08/2026: khoản từ %s đ trở lên phải có giấy "
		"tờ đính kèm mới gửi đi duyệt được. Khoản nhỏ hơn thì không bắt.\n\n"
		"Thật sự không có giấy tờ thì chọn loại \"Bảng kê không hoá đơn\" "
		"hoặc \"Không có chứng từ\", hai loại đó không đòi tệp."
		% (len(thieu), _tien(NGUONG_MIEN_CHUNG_TU), dong_loi, _tien(NGUONG_MIEN_CHUNG_TU))
	)


@frappe.whitelist()
def soat_chung_tu(name=None, dong=None):
	"""Màn hình hỏi trước: hồ sơ này gửi được chưa, thiếu ở khoản nào.

	Cho màn hình bật cảnh báo SỚM, ngay lúc người ta còn đang gõ, thay vì để
	bấm Gửi rồi mới đổ ra một cục lỗi.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "soát chứng từ hồ sơ")
	if isinstance(dong, str):
		dong = frappe.parse_json(dong)
	if not dong and name:
		if not frappe.db.exists("Vagabond Ho So TT", name):
			frappe.throw("Không tìm thấy hồ sơ %s." % name)
		doc = frappe.get_doc("Vagabond Ho So TT", name)
		dong = [
			{
				"noi_dung": d.noi_dung, "so_tien": flt(d.so_tien),
				"loai_chung_tu": d.get("loai_chung_tu"), "tep": d.get("tep"),
			}
			for d in doc.dong
		]
	try:
		from vagabond.de_nghi_chi import _dm_chung_tu

		dm = _dm_chung_tu()
	except Exception:
		dm = {}
	thieu = thieu_chung_tu(dong or [], dm)
	return {
		"nguong": NGUONG_MIEN_CHUNG_TU,
		"thieu": thieu,
		"gui_duoc": 0 if thieu else 1,
	}


# ============================================================================
# HOÀN ỨNG KHÔNG HOÁ ĐƠN: hoàn về TÀI KHOẢN, không phải về nhà cung cấp
# ============================================================================
#
# Anh Việt 22/08/2026: *"không cần chọn danh sách NCC cho dạng hoàn ứng
# không hoá đơn bởi vì hoàn vào chỉ có 1 hoặc là ACB hoặc là OCB thôi (em
# cho hiển thị cả stk nhé)"*.
#
# Màn cũ bắt chọn một nhà cung cấp trong danh sách vài trăm dòng, mà bản
# chất khoản này KHÔNG thuộc về nhà cung cấp nào cả: đây là tiền của người
# ứng đã bỏ ra hộ công ty ở hàng chục chỗ khác nhau, giờ trả lại vào đúng
# một trong hai tài khoản ứng. Bắt chọn nhà cung cấp ở đây vừa vô nghĩa vừa
# là chỗ dễ chọn nhầm nhất trên cả màn hình.
#
# Số tài khoản hiện ra ngay cạnh tên, vì hai tài khoản dễ lẫn khi chỉ nhìn
# tên ngân hàng.

# Tài khoản quỹ tạm ứng: 1411 là nơi tiền ứng nằm. Ngược hẳn `ds_tk_cong_ty`
# vốn LOẠI 1411 ra vì màn kia chi tiền công ty, còn màn này trả tiền ứng.
def _tk_ung(b):
	"""Bank Account nay co phai tai khoan tam ung khong. Ca nhom 141."""
	return str(b.get("account") or "").strip().startswith(TK_NHOM_TAM_UNG)


def _cua_nguoi(b, ma_ncc):
	"""Bank Account nay co phai cua dung nguoi duoc hoan ung khong."""
	return (b.get("party_type") or "") == "Supplier" and (b.get("party") or "").strip() == ma_ncc


def _dat_tk_nhan(doc, tk_hoan, ma_nguoi=""):
	"""Ghi tài khoản nhận tiền lên hồ sơ hoàn ứng, trả về mã Bank Account.

	Một chỗ duy nhất cho cả hai luồng hoàn ứng, để hai màn hình không bao giờ
	cư xử khác nhau. Ba việc, theo đúng thứ tự:

	1. Tài khoản người lập CHỌN đè lên tài khoản mặc định. Người ứng có cả
	   ACB lẫn OCB, chỉ cái chọn tay mới là cái đúng cho tờ này.
	2. Tài khoản phải THUỘC VỀ đúng người được hoàn ứng. Chặn ở đây vì màn
	   hình có thể bị lùi trang, giữ chip cũ của người trước rồi gửi lên.
	   Chuyển tiền hoàn ứng vào túi người khác là mất tiền thật.
	3. Chọn rồi thì ba ô tên - số tài khoản - ngân hàng lấy thẳng từ Bank
	   Account, không ai gõ tay nữa nên không lệch một chữ.

	Không chọn gì thì trả về rỗng và giữ nguyên nếp cũ là đọc tài khoản mặc
	định, để hồ sơ nháp cũ vẫn lưu được.
	"""
	ten = (tk_hoan or "").strip()
	if not ten:
		return ""
	if not frappe.db.exists("Bank Account", ten):
		frappe.throw("Không có tài khoản ngân hàng %s. Vui lòng chọn lại." % ten)
	ma_nguoi = (ma_nguoi or "").strip()
	# Quy tam ung cua CONG TY khong thuoc rieng nguoi nao: do la tui tien
	# chung ma nguoi di mua rut ra, ai duoc hoan ung cung nhan tu do. Chan
	# o day la chan nham. Chi soi nhung tai khoan RIENG cua mot nha cung
	# cap, vi do moi la cho tien chay nham tui nguoi khac duoc.
	if cint(frappe.db.get_value("Bank Account", ten, "is_company_account")):
		for k, v in (_tk_tu_bank_account(ten) or {}).items():
			if v:
				doc.set(k, v)
		return ten
	chu = _ncc_cua_tk_hoan(ten)
	if ma_nguoi and chu and chu != ma_nguoi:
		frappe.throw(
			"Tài khoản %s là của %s, không phải của người được hoàn ứng. "
			"Tiền hoàn ứng phải về đúng túi người đã bỏ tiền ra, vui lòng chọn lại."
			% (ten, frappe.db.get_value("Supplier", chu, "supplier_name") or chu)
		)
	for k, v in (_tk_tu_bank_account(ten) or {}).items():
		if v:
			doc.set(k, v)
	return ten


@frappe.whitelist()
def tk_quy_tam_ung():
	"""Tài khoản sổ cái của quỹ tạm ứng đang dùng, cho màn hình gọi.

	Anh Việt bỏ tài khoản OCB ngày 28/08/2026. Màn phiếu mua hàng test
	trước đây gõ cứng `1411 - Tạm ứng - Nguyễn Hoàng Việt (OCB)` vào ô tài
	khoản chi, nên bỏ OCB rồi mà không sửa thì phiếu vẫn chi từ một quỹ
	không còn dùng.

	Trả về rỗng khi chưa khai tài khoản nào: màn hình sẽ lập phiếu KHÔNG
	đánh dấu đã trả, hơn là lập một phiếu chi sai quỹ.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem quỹ tạm ứng")
	ten = _bank_account_quy()
	if not ten:
		return {"bank_account": "", "tai_khoan": "", "nhan": ""}
	o = frappe.db.get_value(
		"Bank Account", ten, ["account", "bank", "bank_account_no"], as_dict=True
	) or {}
	nh = (o.get("bank") or "").split("-")[0].strip()
	return {
		"bank_account": ten,
		"tai_khoan": o.get("account") or "",
		"nhan": (nh or ten) + ((" · " + o["bank_account_no"]) if o.get("bank_account_no") else ""),
	}


@frappe.whitelist()
def ds_tk_hoan_ung(nguoi=None):
	"""Các tài khoản nhận tiền hoàn ứng: ACB và OCB của người ứng.

	Lấy đúng những Bank Account gắn vào tài khoản sổ cái quỹ tạm ứng 1411.
	Không có cái nào khớp thì trả về mọi tài khoản công ty còn dùng, kèm cờ
	`doan` để màn hình nói rõ đây là bản đoán - thà hiện thừa vài dòng còn
	hơn hiện bảng trống và chặn người ta lập hồ sơ.

	`nguoi` là mã nhà cung cấp của người được hoàn ứng. Truyền vào thì chỉ
	bày tài khoản CỦA CHÍNH người đó, vì tiền hoàn ứng chỉ được chảy về túi
	người đã bỏ tiền ra. Anh Việt 28/08/2026: màn hoàn ứng có hoá đơn trước
	đây không có ô này nên máy tự đoán tài khoản mặc định, người ứng có cả
	ACB lẫn OCB thì đoán sai là chuyển nhầm ngân hàng.

	Người đó chưa khai tài khoản nào trong nhóm 141 thì lùi về danh sách
	chung kèm cờ `doan`, không chặn Uyên lập hồ sơ.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem tài khoản hoàn ứng")
	tat_ca = frappe.get_all(
		"Bank Account",
		filters={"disabled": 0},
		fields=["name", "account_name", "bank", "bank_account_no", "account", "party", "party_type"],
		limit_page_length=0,
	)
	ung = [b for b in tat_ca if _tk_ung(b)]
	doan = 0
	ma_nguoi = (nguoi or "").strip()
	if ma_nguoi:
		rieng = [b for b in ung if _cua_nguoi(b, ma_nguoi)]
		if rieng:
			ung = rieng
		else:
			# Chua gan tai khoan nao cho nguoi nay: bay het nhom 141 va noi
			# ro day la ban doan, hon la de bang trong.
			doan = 1
	if not ung:
		doan = 1
		ung = [b for b in tat_ca if b.get("account")]
	ra = []
	for b in ung:
		ten_nh = (b.get("bank") or "").strip()
		ra.append({
			"ma": b["name"],
			"ten": b.get("account_name") or b["name"],
			"ngan_hang": ten_nh,
			"so_tk": b.get("bank_account_no") or "",
			"tk_so_cai": b.get("account") or "",
			# Nguoi dung tien voi tai khoan nay, de con treo cong no dung ma.
			"nguoi": b.get("party") if b.get("party_type") == "Supplier" else "",
			# Nhan gon cho chip tren man: "ACB · 1234567890"
			"nhan": (ten_nh or b.get("account_name") or b["name"])
			        + ((" · " + b["bank_account_no"]) if b.get("bank_account_no") else ""),
		})
	ra.sort(key=lambda x: x["nhan"])
	return {"tk": ra, "doan": doan}


def _tk_tu_bank_account(ten):
	"""Ba ô tài khoản nhận tiền, đọc từ một Bank Account cụ thể."""
	o = frappe.db.get_value(
		"Bank Account", ten,
		["account_name", "bank_account_no", "bank", "iban"], as_dict=True,
	) or {}
	return {
		"ten_nhan": (o.get("account_name") or "").strip(),
		"stk_nhan": (o.get("bank_account_no") or o.get("iban") or "").strip(),
		"ngan_hang_nhan": (o.get("bank") or "").strip(),
	}


def _ncc_cua_tk_hoan(ten):
	"""Mã nhà cung cấp gắn với một tài khoản hoàn ứng.

	Sổ cái treo công nợ theo MÃ nhà cung cấp, nên dù màn hình không bắt chọn
	nữa thì máy vẫn phải suy ra được mã. Tài khoản chưa gắn Party thì trả về
	rỗng và người gọi sẽ báo lỗi chỉ rõ chỗ phải khai.
	"""
	o = frappe.db.get_value(
		"Bank Account", ten, ["party", "party_type"], as_dict=True
	) or {}
	if (o.get("party_type") or "") == "Supplier" and (o.get("party") or "").strip():
		return o["party"].strip()
	return ""


@frappe.whitelist()
def dinh_tep_hoa_don(hoa_don=None, tep=None):
	"""Đính bản thể hiện của hoá đơn vào THẲNG hoá đơn mua, ngay lúc chọn.

	Anh Việt 22/08/2026: *"khi chọn hoá đơn để hoàn ứng cho đơn vị đó thì em
	cho luôn nút tải lên tệp thể hiện hoá đơn ở kế bên, bỏ cái nút đó ở bước
	sau cho nó chặt chẽ, rồi combine luôn vào file để in ra trong bộ hồ sơ
	pdf"*.

	Vì sao đính vào HOÁ ĐƠN chứ không vào hồ sơ: bản thể hiện là giấy tờ của
	tờ hoá đơn đó, không phải của hồ sơ. Đính vào hồ sơ thì lần sau hoá đơn
	ấy nằm trong hồ sơ khác lại phải tải lên lần nữa, và ai mở hoá đơn trên
	Next cũng không thấy bản thể hiện đâu.

	Đính vào hoá đơn thì `_chung_tu_cua_hoa_don` nhặt được ngay qua đường
	`scan`, nên bộ hồ sơ PDF tự gộp vào mà không phải nối thêm dây nào.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "đính bản thể hiện hoá đơn")
	hoa_don = (hoa_don or "").strip()
	if not hoa_don or not frappe.db.exists("Purchase Invoice", hoa_don):
		frappe.throw("Không tìm thấy hoá đơn mua %s." % (hoa_don or "(trống)"))
	ma_moi = _tep_hop_le(tep)
	if not ma_moi:
		frappe.throw("Tệp gửi lên không còn trên máy chủ. Vui lòng chọn tệp rồi đính lại.")
	for ma in ma_moi:
		try:
			frappe.db.set_value("File", ma, {
				"attached_to_doctype": "Purchase Invoice",
				"attached_to_name": hoa_don,
				"is_private": 1,
			}, update_modified=False)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "ho_so_tt: dinh ban the hien %s" % hoa_don)
	try:
		frappe.get_doc("Purchase Invoice", hoa_don).add_comment(
			"Comment", "Đính %d bản thể hiện hoá đơn từ app." % len(ma_moi)
		)
	except Exception:
		pass
	frappe.db.commit()
	return {"ok": 1, "hoa_don": hoa_don, "tep": _dinh_kem([("Purchase Invoice", hoa_don)])}



# Truoc buoc nao thi con go duoc ban the hien ra. Da thanh toan roi thi bo
# ho so la giay to giai trinh cua mot lan chuyen tien that: go mot to ra la
# lam thung bo do (QT-20, va luat khong dung vao du lieu qua khu anh Viet
# chot 13/08/2026).
TT_GO_DUOC_TEP = (TT_NHAP, TT_TU_CHOI, TT_CHO_FIN, TT_CHO_GD)


@frappe.whitelist()
def go_tep_hoa_don(name=None, hoa_don=None, tep=None):
	"""Go mot ban the hien dinh nham khoi hoa don mua. KHONG xoa tep.

	Anh Viet 24/08/2026: moi hinh thu nho phai co nut X. Truoc do man nay
	chi dinh vao duoc chu khong go ra duoc, nen dinh nham to cua hoa don
	khac la no nam do va di theo ca bo ho so PDF.

	Nhan ca `name` (ho so) de kiem trang thai: ho so da thanh toan thi
	khong con go duoc nua.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "gỡ bản thể hiện hoá đơn")
	hoa_don = (hoa_don or "").strip()
	if not hoa_don or not frappe.db.exists("Purchase Invoice", hoa_don):
		frappe.throw("Không tìm thấy hoá đơn mua %s." % (hoa_don or "(trống)"))

	if name:
		tt = frappe.db.get_value("Vagabond Ho So TT", name, "trang_thai")
		if tt and tt not in TT_GO_DUOC_TEP:
			frappe.throw(
				"Hồ sơ %s đang ở %s nên không gỡ bản thể hiện ra được nữa. Bộ hồ sơ "
				"này là giấy tờ giải trình của một lần chuyển tiền thật. Đính nhầm thì "
				"đính thêm tờ đúng vào, và báo bộ phận kỹ thuật."
				% (name, NHAN.get(tt, tt))
			)

	f = frappe.db.get_value(
		"File",
		{"name": tep, "attached_to_doctype": "Purchase Invoice", "attached_to_name": hoa_don},
		["name", "file_name"],
		as_dict=True,
	)
	if not f:
		frappe.throw(
			"Tệp này không nằm trên hoá đơn %s. Vui lòng tải lại trang rồi bấm lại." % hoa_don
		)
	frappe.db.set_value("File", f.name, {
		"attached_to_doctype": None, "attached_to_name": None,
	}, update_modified=False)
	try:
		frappe.get_doc("Purchase Invoice", hoa_don).add_comment(
			"Comment", "Gỡ bản thể hiện %s khỏi hoá đơn." % (f.file_name or f.name)
		)
	except Exception:
		pass
	frappe.db.commit()
	return {"ok": 1, "hoa_don": hoa_don, "tep": _dinh_kem([("Purchase Invoice", hoa_don)])}

@frappe.whitelist()
def dem_tep_hoa_don(hoa_don=None):
	"""Mỗi hoá đơn đang có mấy bản thể hiện, để màn hình tô nút cho đúng.

	Nhận một mã hoặc cả danh sách: màn chọn hoá đơn bày vài chục dòng một
	lúc, hỏi từng dòng một là vài chục lượt gọi mạng.
	"""
	_kiem(VAI_LAP | VAI_FIN | VAI_GD, "xem bản thể hiện hoá đơn")
	if isinstance(hoa_don, str):
		try:
			hoa_don = frappe.parse_json(hoa_don)
		except Exception:
			hoa_don = [hoa_don]
	ds = [str(x).strip() for x in (hoa_don or []) if str(x or "").strip()]
	if not ds:
		return {"dem": {}}
	dem = {m: 0 for m in ds}
	try:
		for f in frappe.get_all(
			"File",
			filters={"attached_to_doctype": "Purchase Invoice", "attached_to_name": ["in", ds]},
			fields=["attached_to_name"],
			limit_page_length=0,
		):
			m = f["attached_to_name"]
			dem[m] = dem.get(m, 0) + 1
	except Exception:
		frappe.log_error(frappe.get_traceback(), "ho_so_tt: dem ban the hien hoa don")
	return {"dem": dem}
