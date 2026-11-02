# -*- coding: utf-8 -*-
"""Quỹ tiền mặt công ty (v628, anh Việt duyệt mẫu 4 màn ngày 02/11/2026).

Anh Việt hỏi: "các bên nộp tiền về thì cộng vào, chị Dung có thể sửa (có ghi record),
rồi khi nộp tiền mặt vào tài khoản thì hệ thống có chỗ cho chị ấy chuyển". Đã chốt:

  - Tiền vào quỹ vẫn qua Biên nhận nộp tiền mặt, ký nhận là quỹ cộng (tai_chinh.tinh_quy).
  - Không ai gõ đè số dư. Muốn sửa thì KIỂM QUỸ: đếm theo mệnh giá, máy so với số máy
    tính, lệch thì bắt lý do và lập bút toán chênh lệch (thiếu vào tài khoản thiếu chờ
    xử lý, thừa vào tài khoản thừa chờ giải quyết, kế toán chọn một lần).
  - Lệch QUÁ 2.000.000 đ thì chờ Giám đốc duyệt (anh Việt 02/11/2026), quỹ giữ số cũ
    tới khi duyệt; người duyệt khác người kiểm.
  - NỘP TIỀN MẶT VÀO NGÂN HÀNG: bút toán Nợ ngân hàng / Có quỹ ngay lúc ghi; máy tự ghép
    giao dịch SePay cùng tài khoản, cùng số tiền trong 3 ngày để khoản đó không bị báo
    nhầm là tiền chưa gắn chứng từ. Quá 2 ngày chưa khớp thì nhóm Zalo Kế toán nhận tin.

Phép THUẦN đứng đầu tệp (ca kiểm chạy không cần site); phần chạm hệ ở dưới.
"""

import json
from datetime import timedelta

import frappe
from frappe.utils import add_days, cint, getdate, now_datetime, nowdate

DT = "Vagabond Phieu Quy"
DT_CAI = "Vagabond Tai Chinh Cai Dat"
KIEM = "Kiểm quỹ"
NOP = "Nộp ngân hàng"
THAY = "Đã thay"  # Codex #527 vòng 2: phiếu chờ duyệt bị lần kiểm sau thay, không ghi sổ
NGUONG_DUYET = 2000000  # anh Việt 02/11/2026: lệch quá 2 triệu thì anh duyệt
NGAY_KHOP = 3  # tiền nộp ở quầy ngân hàng vào tài khoản trễ tối đa 3 ngày
NGAY_NHAC = 2  # quá 2 ngày chưa khớp thì báo kế toán
MENH_GIA = (500000, 200000, 100000, 50000, 20000, 10000, 5000, 2000, 1000, 500)
LY_DO = (
	("chi_chua_nhap", "Chi chưa nhập app"),
	("thu_chua_nhap", "Thu chưa nhập app"),
	("dem_sai", "Lần trước đếm sai"),
	("chua_ro", "Chưa rõ"),
)
TEN_LY_DO = dict(LY_DO)
VAI_DUYET = ("System Manager", "Giám đốc")


def _f(x):
	try:
		return float(x or 0)
	except Exception:
		return 0.0


def tien(x):
	return "{:,.0f}".format(round(_f(x))).replace(",", ".") + " đ"


def doc_bang_dem(bang):
	"""THUẦN. Bảng đếm {mệnh giá: số tờ} (dict, list cặp, hoặc JSON) -> (dòng sạch, tổng,
	lỗi). Số tờ phải là số nguyên không âm; mệnh giá phải nằm trong danh mục."""
	if isinstance(bang, str):
		try:
			bang = json.loads(bang or "{}")
		except Exception:
			return [], 0.0, "Bảng đếm mệnh giá không đọc được, mở lại màn rồi đếm lại."
	if isinstance(bang, dict):
		cap = list(bang.items())
	else:
		cap = [((x or {}).get("menh_gia"), (x or {}).get("so_to")) for x in (bang or [])]
	dong, tong = [], 0.0
	for mg, so in cap:
		try:
			mg_i = int(float(str(mg).replace(".", "").replace(",", "")))
		except Exception:
			return [], 0.0, "Mệnh giá %s không có trong danh mục." % mg
		if mg_i not in MENH_GIA:
			return [], 0.0, "Mệnh giá %s không có trong danh mục." % mg
		s = str(so if so is not None else "").strip()
		if s in ("", "0"):
			continue
		if not s.isdigit():
			return [], 0.0, "Số tờ %s của mệnh giá %s phải là số nguyên không âm." % (s, tien(mg_i))
		dong.append({"menh_gia": mg_i, "so_to": int(s), "thanh_tien": mg_i * int(s)})
		tong += mg_i * int(s)
	dong.sort(key=lambda x: -x["menh_gia"])
	return dong, tong, ""


def phan_loai_lech(so_may, so_dem, nguong=NGUONG_DUYET):
	"""THUẦN. Lệch = đếm được - máy tính. Lệch dưới 1 đồng coi như khớp."""
	lech = round(_f(so_dem) - _f(so_may))
	if abs(lech) < 1:
		return {"lech": 0, "loai": "khop", "can_duyet": 0}
	return {"lech": lech, "loai": "thua" if lech > 0 else "thieu", "can_duyet": 1 if abs(lech) > _f(nguong) else 0}


def dong_but_toan_lech(lech, tk_quy, tk_thieu, tk_thua):
	"""THUẦN. Hai dòng bút toán chênh lệch quỹ. Thiếu: Nợ TK thiếu / Có quỹ. Thừa: Nợ quỹ /
	Có TK thừa."""
	so = abs(round(_f(lech)))
	if not so:
		return []
	if _f(lech) < 0:
		return [{"tk": tk_thieu, "no": so, "co": 0}, {"tk": tk_quy, "no": 0, "co": so}]
	return [{"tk": tk_quy, "no": so, "co": 0}, {"tk": tk_thua, "no": 0, "co": so}]


def dong_but_toan_nop(so_tien, tk_ngan_hang, tk_quy):
	"""THUẦN. Nộp tiền mặt vào ngân hàng: Nợ tài khoản ngân hàng / Có quỹ."""
	so = round(_f(so_tien))
	return [{"tk": tk_ngan_hang, "no": so, "co": 0}, {"tk": tk_quy, "no": 0, "co": so}]


def kiem_nop(so_tien, quy_dang_co, ngay, ngay_moc, hom_nay):
	"""THUẦN. Lỗi chặn một phiếu nộp ngân hàng, rỗng nếu được."""
	if _f(so_tien) <= 0:
		return "Gõ số tiền mang đi nộp."
	if quy_dang_co is None:
		return "Quỹ chưa chốt số dư đầu. Chốt ở Cài đặt tài chính trước, rồi mới ghi nộp tiền."
	if _f(so_tien) > _f(quy_dang_co) + 1:
		return "Quỹ chỉ còn %s, không nộp được %s. Kiểm quỹ trước nếu tiền thật nhiều hơn." % (
			tien(quy_dang_co), tien(so_tien))
	if not ngay:
		return "Chọn ngày nộp."
	if ngay > hom_nay:
		return "Ngày nộp không được sau hôm nay."
	if ngay_moc and ngay <= ngay_moc:
		return ("Ngày nộp %s không sau mốc chốt quỹ %s: số chốt đã gồm mọi khoản tới hết ngày đó. "
			"Chọn ngày sau mốc, hoặc chốt lại quỹ." % (ngay.strftime("%d/%m/%Y"), ngay_moc.strftime("%d/%m/%Y")))
	return ""


def _ngay(x):
	"""THUẦN: date từ date, datetime hoặc chuỗi YYYY-MM-DD."""
	from datetime import date, datetime
	if isinstance(x, datetime):
		return x.date()
	if isinstance(x, date):
		return x
	return date(*[int(p) for p in str(x)[:10].split("-")])


def chon_gd_khop(phieu, cac_gd, co_chu=()):
	"""THUẦN. Giao dịch SePay cho một phiếu nộp: cùng tài khoản, cùng số tiền (lệch tối đa
	1 đồng), từ ngày nộp tới NGAY_KHOP ngày sau, chưa ai giữ. Nhiều khoản giống nhau thì
	lấy khoản sớm nhất. Trả tên giao dịch hoặc ""."""
	ngay = _ngay(phieu.get("ngay"))
	het = ngay + timedelta(days=NGAY_KHOP)
	ung = []
	for g in cac_gd or []:
		if g.get("ten") in co_chu:
			continue
		if str(g.get("bank_account") or "") != str(phieu.get("bank_account") or ""):
			continue
		if abs(_f(g.get("deposit")) - _f(phieu.get("so_tien"))) > 1:
			continue
		d = _ngay(g.get("date"))
		if d < ngay or d > het:
			continue
		ung.append((str(d), str(g.get("creation") or ""), g.get("ten")))
	return sorted(ung)[0][2] if ung else ""


def soan_lech_cho_duyet(p, ten_nguoi):
	"""THUẦN: (tiêu đề, dòng) tin Zalo khi kiểm quỹ lệch quá ngưỡng."""
	lech = _f(p.get("lech"))
	td = "Kiểm quỹ %s %s, chờ giám đốc duyệt" % ("thiếu" if lech < 0 else "thừa", tien(abs(lech)))
	dong = [
		"%s kiểm quỹ tiền mặt công ty lúc %s" % (ten_nguoi or "Kế toán", str(p.get("luc") or "")[11:16]),
		"Máy tính: %s · Đếm được: %s" % (tien(p.get("so_may")), tien(p.get("so_dem"))),
		"Lý do: %s%s" % (TEN_LY_DO.get(p.get("ly_do"), p.get("ly_do") or ""),
			(" · \"%s\"" % p.get("ghi_chu")) if p.get("ghi_chu") else ""),
		"Lệch quá %s nên quỹ giữ số cũ tới khi giám đốc duyệt." % tien(NGUONG_DUYET),
	]
	return td, dong


def soan_nop_chua_khop(ds):
	"""THUẦN: (tiêu đề, dòng) tin nhắc kế toán các phiếu nộp ngân hàng chưa thấy tiền về."""
	td = "Tiền mặt đã nộp ngân hàng chưa thấy về tài khoản"
	dong = ["%d phiếu, tổng %s, quá %d ngày chưa khớp SePay" % (len(ds), tien(sum(_f(x.get("so_tien")) for x in ds)), NGAY_NHAC)]
	for x in ds[:8]:
		dong.append("%s · %s · %s · nộp %s" % (x.get("name"), tien(x.get("so_tien")), x.get("ten_tai_khoan") or "",
			str(x.get("ngay") or "")[8:10] + "/" + str(x.get("ngay") or "")[5:7]))
	dong.append("Kế toán kiểm sao kê: tiền về số khác thì sửa phiếu, nộp nhầm tài khoản thì huỷ phiếu rồi lập lại.")
	return td, dong


def dong_cuoi_ngay(cac_phieu):
	"""THUẦN: dòng cho tin Tiền cuối ngày về các lần kiểm quỹ trong ngày (lệch nhỏ ghi ngay
	vẫn phải tới Ban giám đốc)."""
	ra = []
	for p in cac_phieu or []:
		lech = _f(p.get("lech"))
		if not lech:
			ra.append("Kiểm quỹ %s: khớp" % str(p.get("luc") or "")[11:16])
			continue
		ra.append("Kiểm quỹ %s: %s %s (%s)%s" % (str(p.get("luc") or "")[11:16], "thiếu" if lech < 0 else "thừa",
			tien(abs(lech)), TEN_LY_DO.get(p.get("ly_do"), p.get("ly_do") or ""),
			", chờ duyệt" if p.get("trang_thai") == "Chờ duyệt" else ""))
	return ra


# ======================================================= phần chạm hệ

def _vai():
	return set(frappe.get_roles())


def _vai_quy():
	from vagabond import nop_quy
	return set(nop_quy.VAI_KY_NHAN) | {"Giám đốc"}


def _duoc_lam():
	return bool(_vai() & _vai_quy())


def _duoc_xem():
	from vagabond import tai_chinh
	return _duoc_lam() or tai_chinh.co_quyen()


def _kiem_xem():
	if not _duoc_xem():
		frappe.throw("Quỹ tiền mặt công ty chỉ mở cho kế toán, Giám đốc và người Giám đốc chọn.", frappe.PermissionError)


def _kiem_lam():
	if not _duoc_lam():
		frappe.throw("Chỉ kế toán và Giám đốc được kiểm quỹ, ghi nộp tiền.", frappe.PermissionError)


def _la_giam_doc():
	return bool(_vai() & set(VAI_DUYET))


def _cai():
	try:
		d = frappe.get_doc(DT_CAI)
		return {"tk_quy": d.get("tk_quy") or "", "tk_thieu": d.get("tk_thieu") or "", "tk_thua": d.get("tk_thua") or ""}
	except Exception:
		return {"tk_quy": "", "tk_thieu": "", "tk_thua": ""}


def _goi_y_tk():
	from vagabond import but_toan
	ra = {}
	for k, so in (("tk_quy", "1111"), ("tk_thieu", "1381"), ("tk_thua", "3381")):
		r = but_toan._tim_tk(so)
		ra[k] = r["name"] if r else ""
	return ra


def _nhan_tk(ten):
	if not ten:
		return ""
	r = frappe.db.get_value("Account", ten, ["account_number", "account_name"], as_dict=True)
	if not r:
		return ten
	from vagabond import but_toan
	return but_toan.nhan_tk(r.account_number, r.account_name)


def _khoa_quy():
	"""Khoá dòng tài khoản quỹ: hai người cùng kiểm quỹ hoặc cùng ghi nộp thì người sau
	chờ, rồi đọc số quỹ đã gồm phiếu của người trước."""
	tk = _tk_dung("tk_quy")
	if tk:
		# Codex #527 vòng 3: MariaDB REPEATABLE READ chụp ảnh số liệu ở lần đọc thường
		# ĐẦU TIÊN của giao dịch. Các cửa gọi hàm này đã đọc (tài khoản ngân hàng, quyền)
		# trước khi xin khoá, nên ảnh chụp có thể có từ trước lúc người giữ khoá trước ghi
		# xong. Kết thúc giao dịch đang đọc (chưa ghi gì) rồi mới xin khoá: lần đọc số quỹ
		# sau khoá chụp ảnh mới, thấy phiếu người trước vừa commit.
		frappe.db.commit()
		frappe.db.sql("select name from `tabAccount` where name=%s for update", (tk,))


def _so_quy():
	"""(số đang có hoặc None, mốc)."""
	from vagabond import tai_chinh
	m = tai_chinh.moc_quy()
	if not m:
		return None, None
	return tai_chinh.tinh_quy(m)["so_du"], m


def _tai_khoan_nh():
	ds = frappe.get_all("Bank Account", filters={"is_company_account": 1, "disabled": 0},
		fields=["name", "bank", "bank_account_no", "account"], order_by="name asc", limit_page_length=0)
	ra = []
	for b in ds:
		if not b.account:
			continue
		so = "".join(c for c in str(b.bank_account_no or "") if c.isdigit())
		ra.append({"ma": b.name, "ten": "%s ···%s" % (b.bank or "Ngân hàng", so[-4:]) if so else (b.bank or b.name),
			"tk": b.account})
	# MB công ty lên đầu: tài khoản chính nhận tiền khách.
	ra.sort(key=lambda x: (0 if "MB" in x["ten"].upper() else 1, x["ten"]))
	return ra


def _ten(user):
	return frappe.db.get_value("User", user, "full_name") or user if user else ""


def _lap_but_toan(dong, ngay, dien_giai):
	from vagabond import but_toan
	je = frappe.get_doc({"doctype": "Journal Entry", "voucher_type": "Journal Entry", "company": but_toan._cty(),
		"posting_date": str(ngay), "user_remark": dien_giai[:500], "accounts": []})
	for x in dong:
		if not x["tk"] or not frappe.db.exists("Account", x["tk"]):
			frappe.throw("Chưa chọn đủ tài khoản hạch toán của quỹ. Mở mục Tài khoản hạch toán quỹ ở cuối màn Quỹ tiền mặt.")
		je.append("accounts", {"account": x["tk"], "debit_in_account_currency": x["no"],
			"credit_in_account_currency": x["co"], "user_remark": dien_giai[:140]})
	je.flags.ignore_permissions = True
	je.insert(ignore_permissions=True)
	je.submit()
	return je.name


def _lich_su(m, gioi_han=40):
	"""Tiền vào, ra quỹ sau mốc: biên nhận đã ký nhận, bút toán 111x không thuộc két, phiếu
	quỹ chờ duyệt. Mới nhất lên đầu."""
	from vagabond import tai_chinh
	if not m:
		return []
	ra = []
	for r in frappe.get_all("Vagabond Nop Quy", filters={"trang_thai": "Đã nộp quỹ"},
			fields=["name", "ten_diem_ban", "diem_ban", "nhan_luc", "giao_luc", "ngay", "tong_thuc_nhan", "tien_ky_vong",
				"ten_nguoi_nhan"], order_by="nhan_luc desc", limit_page_length=200):
		luc = r.nhan_luc or r.giao_luc
		if not luc or getdate(luc) <= getdate(m["ngay_chot"]):
			continue
		ra.append({"luc": str(luc)[:16], "loai": "nop_quy", "ma": r.name, "tien": _f(r.tong_thuc_nhan) or _f(r.tien_ky_vong),
			"ten": "Biên nhận nộp tiền mặt", "phu": "%s · %s ký nhận" % (r.ten_diem_ban or r.diem_ban or "", r.ten_nguoi_nhan or "")})
	gl = frappe.db.sql("""select g.voucher_type, g.voucher_no, g.posting_date, max(g.creation) luc,
			sum(g.debit) no, sum(g.credit) co, max(g.remarks) dien_giai
		from `tabGL Entry` g join `tabAccount` a on a.name=g.account
		where """ + tai_chinh.DK_QUY_CONG_TY + """ and g.posting_date>%s
		group by g.voucher_type, g.voucher_no, g.posting_date order by g.posting_date desc, luc desc limit 200""",
		(str(m["ngay_chot"]),), as_dict=True)
	je = [x.voucher_no for x in gl if x.voucher_type == "Journal Entry"]
	phieu = {}
	if je:
		for p in frappe.get_all(DT, filters={"but_toan": ["in", je]}, fields=["name", "but_toan", "loai", "ly_do",
				"ten_tai_khoan", "ten_nguoi", "trang_thai", "gd_sepay"], limit_page_length=0):
			phieu[p.but_toan] = p
	for x in gl:
		p = phieu.get(x.voucher_no)
		tien_ = _f(x.no) - _f(x.co)
		if p and p.loai == NOP:
			ten, phu = "Nộp vào %s" % (p.ten_tai_khoan or "ngân hàng"), p.ten_nguoi or ""
			chip = "Đã khớp SePay" if p.trang_thai == "Đã khớp" else "Chờ tiền về" if p.trang_thai == "Chờ tiền về" else ""
		elif p:
			ten = "Kiểm quỹ: %s" % ("thừa" if tien_ > 0 else "thiếu")
			phu, chip = "Lý do: %s" % TEN_LY_DO.get(p.ly_do, p.ly_do or ""), ""
		else:
			ten = "Phiếu chi" if x.voucher_type == "Payment Entry" and tien_ < 0 else "Phiếu thu" if x.voucher_type == "Payment Entry" else "Bút toán"
			phu, chip = (x.dien_giai or "")[:90], ""
		ra.append({"luc": str(x.luc)[:16] if x.luc else str(x.posting_date), "ngay": str(x.posting_date), "loai": "so_cai",
			"ma": (p.name if p else x.voucher_no), "tien": tien_, "ten": ten, "phu": phu, "chip": chip})
	for p in frappe.get_all(DT, filters={"trang_thai": "Chờ duyệt"}, fields=["name", "luc", "lech", "ly_do", "ten_nguoi"],
			order_by="luc desc", limit_page_length=20):
		ra.append({"luc": str(p.luc)[:16], "loai": "cho_duyet", "ma": p.name, "tien": _f(p.lech),
			"ten": "Kiểm quỹ: %s, chờ giám đốc duyệt" % ("thừa" if _f(p.lech) > 0 else "thiếu"),
			"phu": "%s · %s" % (p.ten_nguoi or "", TEN_LY_DO.get(p.ly_do, p.ly_do or "")), "cho": 1})
	ra.sort(key=lambda x: x["luc"], reverse=True)
	return ra[:gioi_han]


@frappe.whitelist()
def man_quy():
	"""Màn Quỹ tiền mặt công ty."""
	_kiem_xem()
	so, m = _so_quy()
	cai = _cai()
	goi_y = _goi_y_tk()
	kiem = frappe.get_all(DT, filters={"loai": KIEM, "trang_thai": ["in", ["Khớp", "Đã ghi", "Chờ duyệt"]]},
		fields=["name", "luc", "lech", "ten_nguoi", "trang_thai"], order_by="luc desc", limit_page_length=1)
	cho = frappe.get_all(DT, filters={"loai": KIEM, "trang_thai": "Chờ duyệt"},
		fields=["name", "luc", "ngay", "so_may", "so_dem", "lech", "ly_do", "ghi_chu", "anh", "nguoi", "ten_nguoi"],
		order_by="luc desc", limit_page_length=20)
	ba_lan = frappe.get_all(DT, filters={"loai": KIEM, "trang_thai": ["in", ["Khớp", "Đã ghi"]]},
		fields=["ngay", "lech"], order_by="luc desc", limit_page_length=3)
	for c in cho:
		c["anh"] = _anh(c.get("anh"))
		c["ly_do_ten"] = TEN_LY_DO.get(c.get("ly_do"), c.get("ly_do") or "")
	return {
		"so_du": so, "moc": ({"ngay_chot": str(m["ngay_chot"]), "so_du": _f(m["so_du"])} if m else None),
		"lan_kiem": kiem[0] if kiem else None, "cho_duyet": cho, "ba_lan": ba_lan,
		"lich_su": _lich_su(m), "tai_khoan_nh": _tai_khoan_nh(),
		"menh_gia": list(MENH_GIA), "ly_do": [{"ma": k, "ten": v} for k, v in LY_DO], "nguong": NGUONG_DUYET,
		"duoc_lam": 1 if _duoc_lam() else 0, "duoc_duyet": 1 if _la_giam_doc() else 0, "toi": frappe.session.user,
		"tk": {k: {"ma": cai[k], "ten": _nhan_tk(cai[k]), "goi_y": goi_y.get(k) or "", "ten_goi_y": _nhan_tk(goi_y.get(k))}
			for k in ("tk_quy", "tk_thieu", "tk_thua")},
		"hom_nay": nowdate(),
	}


def _anh(gt):
	from vagabond import tep_dinh_kem
	return tep_dinh_kem.doc_ds(gt)


def _tk_dung(k):
	"""Tài khoản đã chọn, chưa chọn thì gợi ý theo số hiệu (1111, 1381, 3381)."""
	return _cai().get(k) or _goi_y_tk().get(k) or ""


@frappe.whitelist(methods=["POST"])
def kiem_quy(bang=None, ly_do="", ghi_chu="", anh=None):
	"""Kiểm quỹ: đếm theo mệnh giá. Khớp thì chỉ ghi lại; lệch tới 2 triệu ghi bút toán
	ngay; lệch quá 2 triệu chờ Giám đốc duyệt."""
	from vagabond import tep_dinh_kem
	_kiem_lam()
	dong, so_dem, loi = doc_bang_dem(bang)
	if loi:
		frappe.throw(loi)
	# Khoá mốc quỹ để hai người cùng bấm không ra hai phiếu lệch từ cùng một số máy.
	_khoa_quy()
	so_may, m = _so_quy()
	if so_may is None:
		frappe.throw("Quỹ chưa chốt số dư đầu. Chốt ở Cài đặt tài chính trước, rồi mới kiểm quỹ.")
	hom = getdate(nowdate())
	if getdate(m["ngay_chot"]) >= hom:
		frappe.throw("Hôm nay vừa chốt số dư quỹ, số chốt đã là số đếm. Kiểm quỹ từ ngày mai.")
	pl = phan_loai_lech(so_may, so_dem)
	ly_do = str(ly_do or "").strip()
	if pl["lech"] and ly_do not in TEN_LY_DO:
		frappe.throw("Quỹ lệch %s: chọn lý do lệch." % tien(pl["lech"]))
	if pl["lech"] and ly_do == "chua_ro" and len(str(ghi_chu or "").strip()) < 5:
		frappe.throw("Lý do Chưa rõ: ghi thêm vài chữ để Giám đốc biết đã kiểm những gì.")
	tk_quy, tk_thieu, tk_thua = _tk_dung("tk_quy"), _tk_dung("tk_thieu"), _tk_dung("tk_thua")
	if pl["lech"] and not (tk_quy and (tk_thieu if pl["lech"] < 0 else tk_thua)):
		frappe.throw("Chưa chọn tài khoản %s. Mở mục Tài khoản hạch toán quỹ ở cuối màn." % (
			"thiếu chờ xử lý" if pl["lech"] < 0 else "thừa chờ giải quyết"))
	trang_thai = "Khớp" if not pl["lech"] else ("Chờ duyệt" if pl["can_duyet"] else "Đã ghi")
	doc = frappe.get_doc({"doctype": DT, "loai": KIEM, "trang_thai": trang_thai, "ngay": str(hom), "luc": now_datetime(),
		"nguoi": frappe.session.user, "ten_nguoi": _ten(frappe.session.user), "so_may": so_may, "so_dem": so_dem,
		"lech": pl["lech"], "menh_gia": json.dumps(dong, ensure_ascii=False), "ly_do": ly_do if pl["lech"] else "",
		"ghi_chu": str(ghi_chu or "").strip()[:500]})
	doc.insert(ignore_permissions=True)
	# Codex #527 vòng 2: phiếu lệch trước còn chờ duyệt thì số máy CHƯA đổi, nên lần
	# kiểm này đo lại đúng khoản lệch đó. Để cả hai cùng chờ là Giám đốc duyệt hai lần,
	# quỹ bị trừ hai lần. Lần kiểm mới nhất là số thật: phiếu chờ cũ chuyển "Đã thay".
	for cu in frappe.get_all(DT, filters={"loai": KIEM, "trang_thai": "Chờ duyệt", "name": ["!=", doc.name]},
			fields=["name"], limit_page_length=0):
		frappe.db.set_value(DT, cu.name, {"trang_thai": THAY,
			"ly_do_tra": "Lần kiểm sau %s thay phiếu này, phiếu này không ghi sổ." % doc.name}, update_modified=False)
	ds_anh = tep_dinh_kem.gan_vao(DT, doc.name, "anh", anh)
	if ds_anh:
		doc.db_set("anh", tep_dinh_kem.ghi_ds(ds_anh), update_modified=False)
	if trang_thai == "Đã ghi":
		je = _lap_but_toan(dong_but_toan_lech(pl["lech"], tk_quy, tk_thieu, tk_thua), hom,
			"Kiểm quỹ %s: %s %s, lý do %s" % (doc.name, "thừa" if pl["lech"] > 0 else "thiếu", tien(abs(pl["lech"])),
				TEN_LY_DO[ly_do]))
		doc.db_set("but_toan", je, update_modified=False)
	if trang_thai == "Chờ duyệt":
		from vagabond import kenh_zalo
		td, dl = soan_lech_cho_duyet(doc.as_dict(), doc.ten_nguoi)
		kenh_zalo.bao_hoac_ghi_loi("viec", "cong_no", td, dl, link=_url("/quy-tien-mat-cong-ty"), nguoi="Giám đốc",
			han="trong ngày", khoa="kiem-quy:%s" % doc.name, nguon=doc.name, ma_tin="bgd_kiem_quy_lech")
	return {"ok": 1, "name": doc.name, "trang_thai": trang_thai, "lech": pl["lech"], "so_may": so_may, "so_dem": so_dem}


@frappe.whitelist(methods=["POST"])
def duyet_kiem_quy(name=None, dong_y=0, ly_do=""):
	"""Giám đốc duyệt phiếu kiểm quỹ lệch quá ngưỡng. Người duyệt khác người kiểm."""
	if not _la_giam_doc():
		frappe.throw("Chỉ Giám đốc duyệt được kiểm quỹ lệch.", frappe.PermissionError)
	frappe.db.sql("select name from `tab%s` where name=%%s for update" % DT, (name,))
	doc = frappe.get_doc(DT, name)
	if doc.loai != KIEM or doc.trang_thai != "Chờ duyệt":
		frappe.throw("Phiếu %s không còn chờ duyệt." % name)
	if doc.nguoi == frappe.session.user:
		frappe.throw("Người kiểm quỹ không tự duyệt phiếu của mình.")
	# Codex #527 vòng 2: có lần kiểm SAU phiếu này thì số máy đã được đo lại; duyệt
	# phiếu cũ là ghi chênh lệch trên một số đã lỗi thời.
	sau = frappe.get_all(DT, filters={"loai": KIEM, "trang_thai": ["in", ["Khớp", "Đã ghi", "Chờ duyệt"]],
		"luc": [">", doc.luc], "name": ["!=", doc.name]}, fields=["name"], limit_page_length=1)
	if sau:
		frappe.throw("Đã có lần kiểm quỹ sau phiếu này (%s). Duyệt phiếu mới nhất thay vì phiếu %s." % (sau[0].name, name))
	doc.duyet_boi = frappe.session.user
	doc.duyet_luc = now_datetime()
	if cint(dong_y):
		# Codex #527 vòng 3: quỹ đã chốt số dư lại từ ngày kiểm trở đi thì số chốt đã gồm
		# lần đếm này; ghi thêm chênh lệch là trừ quỹ hai lần.
		from vagabond import tai_chinh
		moc = tai_chinh.moc_quy() or {}
		if moc.get("ngay_chot") and getdate(moc["ngay_chot"]) >= getdate(doc.ngay):
			frappe.throw("Quỹ đã chốt số dư lại ngày %s, số chốt đã tính cả lần đếm của phiếu %s. Bấm Trả lại phiếu này thay vì duyệt." % (
				getdate(moc["ngay_chot"]).strftime("%d/%m/%Y"), name))
		hom = getdate(nowdate())
		je = _lap_but_toan(dong_but_toan_lech(doc.lech, _tk_dung("tk_quy"), _tk_dung("tk_thieu"), _tk_dung("tk_thua")), hom,
			"Kiểm quỹ %s: %s %s, lý do %s, Giám đốc duyệt" % (doc.name, "thừa" if _f(doc.lech) > 0 else "thiếu",
				tien(abs(_f(doc.lech))), TEN_LY_DO.get(doc.ly_do, doc.ly_do or "")))
		doc.but_toan = je
		doc.trang_thai = "Đã ghi"
	else:
		if len(str(ly_do or "").strip()) < 3:
			frappe.throw("Ghi lý do trả lại để người kiểm biết cần đếm lại chỗ nào.")
		doc.trang_thai = "Trả lại"
		doc.ly_do_tra = str(ly_do).strip()[:500]
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	return {"ok": 1, "trang_thai": doc.trang_thai, "but_toan": doc.get("but_toan") or ""}


@frappe.whitelist(methods=["POST"])
def nop_ngan_hang(so_tien=None, bank_account=None, ngay=None, anh=None, nguoi_nop=""):
	"""Ghi mang tiền mặt của quỹ đi nộp vào tài khoản: bút toán Nợ ngân hàng / Có quỹ,
	rồi máy tự ghép giao dịch SePay khi tiền về."""
	from vagabond import tai_chinh, tep_dinh_kem
	_kiem_lam()
	so = tai_chinh.doc_so_tien(so_tien)
	nh = {x["ma"]: x for x in _tai_khoan_nh()}.get(str(bank_account or ""))
	if not nh:
		frappe.throw("Chọn tài khoản ngân hàng công ty nhận tiền.")
	if not tep_dinh_kem.doc_ds(anh):
		frappe.throw("Đính ảnh giấy nộp tiền của ngân hàng.")
	_khoa_quy()
	quy, m = _so_quy()
	d = tai_chinh.doc_ngay(ngay) or getdate(nowdate())
	loi = kiem_nop(so, quy, d, getdate(m["ngay_chot"]) if m else None, getdate(nowdate()))
	if loi:
		frappe.throw(loi)
	tk_quy = _tk_dung("tk_quy")
	doc = frappe.get_doc({"doctype": DT, "loai": NOP, "trang_thai": "Chờ tiền về", "ngay": str(d), "luc": now_datetime(),
		"nguoi": frappe.session.user, "ten_nguoi": _ten(frappe.session.user), "so_tien": so, "bank_account": nh["ma"],
		"ten_tai_khoan": nh["ten"], "nguoi_nop": str(nguoi_nop or "").strip()[:140] or _ten(frappe.session.user)})
	doc.insert(ignore_permissions=True)
	ds_anh = tep_dinh_kem.gan_vao(DT, doc.name, "anh", anh)
	doc.db_set("anh", tep_dinh_kem.ghi_ds(ds_anh), update_modified=False)
	je = _lap_but_toan(dong_but_toan_nop(so, nh["tk"], tk_quy), d,
		"Nộp tiền mặt vào %s, phiếu %s" % (nh["ten"], doc.name))
	doc.db_set("but_toan", je, update_modified=False)
	try:
		khop_nop_ngan_hang(chi=[doc.name])
	except Exception as e:
		from vagabond import kenh_zalo
		if kenh_zalo.chet_giao_dich(e):
			raise
		frappe.log_error(frappe.get_traceback(), "quy_tien_mat: khop ngay khi ghi nop")
	return {"ok": 1, "name": doc.name, "trang_thai": frappe.db.get_value(DT, doc.name, "trang_thai")}


@frappe.whitelist(methods=["POST"])
def huy_phieu(name=None, ly_do=""):
	"""Huỷ phiếu nộp ghi nhầm (huỷ bút toán, nhả giao dịch). Kiểm quỹ đã ghi thì chỉ
	Giám đốc huỷ. Phiếu vẫn nằm lại để đối chiếu."""
	_kiem_lam()
	if len(str(ly_do or "").strip()) < 3:
		frappe.throw("Ghi lý do huỷ.")
	doc = frappe.get_doc(DT, name)
	if doc.trang_thai in ("Đã huỷ", "Trả lại", THAY):
		frappe.throw("Phiếu %s đã %s." % (name, doc.trang_thai.lower()))
	if doc.loai == KIEM and not _la_giam_doc():
		frappe.throw("Chỉ Giám đốc huỷ được phiếu kiểm quỹ.", frappe.PermissionError)
	if doc.get("but_toan"):
		je = frappe.get_doc("Journal Entry", doc.but_toan)
		if je.docstatus == 1:
			je.flags.ignore_permissions = True
			je.cancel()
	doc.trang_thai = "Đã huỷ"
	doc.gd_sepay = ""
	doc.huy_boi = frappe.session.user
	doc.huy_luc = now_datetime()
	doc.ly_do_huy = str(ly_do).strip()[:500]
	doc.flags.ignore_permissions = True
	doc.save(ignore_permissions=True)
	return {"ok": 1}


@frappe.whitelist(methods=["POST"])
def luu_tai_khoan(tk_quy=None, tk_thieu=None, tk_thua=None):
	"""Kế toán chọn ba tài khoản hạch toán quỹ một lần. Quỹ phải là 111x để màn Tiền hiện
	có đọc được sổ cái."""
	_kiem_lam()
	ghi = {}
	for k, v in (("tk_quy", tk_quy), ("tk_thieu", tk_thieu), ("tk_thua", tk_thua)):
		v = str(v or "").strip()
		if not v:
			continue
		r = frappe.db.get_value("Account", v, ["is_group", "account_number"], as_dict=True)
		if not r or cint(r.is_group):
			frappe.throw("Tài khoản %s không hạch toán thẳng được." % v)
		if k == "tk_quy" and not str(r.account_number or "").startswith("111"):
			frappe.throw("Tài khoản quỹ phải là tiền mặt 111x.")
		ghi[k] = v
	for k, v in ghi.items():
		frappe.db.set_single_value(DT_CAI, k, v)
	return {"ok": 1}


@frappe.whitelist()
def tim_tai_khoan(tu_khoa=""):
	_kiem_lam()
	t = str(tu_khoa or "").strip()
	loc = [["is_group", "=", 0]]
	or_loc = [["account_number", "like", t + "%"], ["account_name", "like", "%" + t + "%"]] if t else None
	ds = frappe.get_all("Account", filters=loc, or_filters=or_loc, fields=["name", "account_number", "account_name"],
		order_by="account_number asc", limit_page_length=30)
	from vagabond import but_toan
	return [{"ma": r.name, "ten": but_toan.nhan_tk(r.account_number, r.account_name)} for r in ds]


def _url(duong):
	try:
		return frappe.utils.get_url(duong)
	except Exception:
		return duong


def khop_nop_ngan_hang(chi=None):
	"""Lịch mỗi giờ (và ngay khi ghi phiếu): ghép phiếu nộp đang chờ với giao dịch SePay."""
	from vagabond import ban_hang
	loc = {"loai": NOP, "trang_thai": "Chờ tiền về"}
	if chi:
		loc["name"] = ["in", list(chi)]
	ds = frappe.get_all(DT, filters=loc, fields=["name", "ngay", "so_tien", "bank_account"], order_by="ngay asc, luc asc",
		limit_page_length=0)
	if not ds:
		return 0
	tu = min(getdate(p.ngay) for p in ds)
	gd = frappe.db.sql("""select name ten, bank_account, deposit, date, creation, description mo_ta, reference_number tham_chieu,
		unallocated_amount from `tabBank Transaction` where docstatus=1 and deposit>0 and date>=%s and bank_account in %s""",
		(str(tu), tuple({p.bank_account for p in ds})), as_dict=True)
	if not gd:
		return 0
	# Codex #527 vòng 2: giữ số ĐÃ PHÂN BỔ thật. Dòng đã khớp chứng từ trong Đối chiếu
	# ngân hàng của ERPNext là có chủ (doi_soat_ck.chu_theo_noi_dung: > 1 đồng).
	co_chu = set((ban_hang._gd_co_chu_toan_he([{"ten": g.ten, "mo_ta": g.mo_ta or "", "tham_chieu": g.tham_chieu or "",
		"da_phan_bo": da_phan_bo(g.deposit, g.get("unallocated_amount"))} for g in gd]) or {}).keys())
	da = 0
	for p in ds:
		ten = chon_gd_khop(p, gd, co_chu)
		if not ten:
			continue
		co_chu.add(ten)
		if not _giu_gd(p.name, ten):
			continue
		frappe.db.set_value(DT, p.name, {"gd_sepay": ten, "khop_luc": now_datetime(), "trang_thai": "Đã khớp"})
		da += 1
	return da


def da_phan_bo(tien, chua_phan_bo):
	"""Số đã phân bổ của một dòng sao kê. THUẦN. Ô chưa phân bổ trống là chưa biết: 0."""
	if chua_phan_bo is None:
		return 0.0
	return max(0.0, _f(tien) - _f(chua_phan_bo))


def _giu_gd(phieu, ten_gd):
	"""Codex #527 vòng 2: hai lượt ghép chạy chen nhau (lịch mỗi giờ và lần ghép ngay khi
	lưu phiếu) cùng đọc một giao dịch chưa có chủ. Khoá dòng giao dịch và dòng phiếu, rồi
	đọc lại BẰNG CÂU CÓ KHOÁ (thấy bản đã commit mới nhất, không phải ảnh chụp đầu giao
	dịch): giao dịch đã thuộc phiếu quỹ khác, hoặc phiếu không còn chờ, thì bỏ qua."""
	frappe.db.sql("select name from `tabBank Transaction` where name=%s for update", (ten_gd,))
	tt = frappe.db.sql("select trang_thai from `tab%s` where name=%%s for update" % DT, (phieu,))
	if tt and tt[0][0] != "Chờ tiền về":
		return False
	khac = frappe.db.sql("select name from `tab%s` where gd_sepay=%%s and trang_thai!='Đã huỷ' and name!=%%s for update" % DT,
		(ten_gd, phieu))
	return not khac


def lich_khop():
	"""Nhịp lập lịch mỗi giờ."""
	try:
		khop_nop_ngan_hang()
		frappe.db.commit()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "quy_tien_mat: khop moi gio")


def nhac_nop_chua_khop():
	"""Lịch 08:10: phiếu nộp ngân hàng quá NGAY_NHAC ngày chưa thấy tiền về."""
	from vagabond import kenh_zalo
	try:
		lich_khop()
		het = add_days(nowdate(), -NGAY_NHAC)
		ds = frappe.get_all(DT, filters={"loai": NOP, "trang_thai": "Chờ tiền về", "ngay": ["<=", het]},
			fields=["name", "ngay", "so_tien", "ten_tai_khoan"], order_by="ngay asc", limit_page_length=0)
		if not ds:
			return
		td, dong = soan_nop_chua_khop(ds)
		kenh_zalo.bao_hoac_ghi_loi("viec", "cong_no", td, dong, link=_url("/quy-tien-mat-cong-ty"), nguoi="Kế toán",
			han="trong ngày", khoa="nop-nh-chua-khop:%s" % nowdate(), ma_tin="kt_nop_nh_chua_khop")
	except Exception as e:
		if kenh_zalo.chet_giao_dich(e):
			raise
		frappe.log_error(frappe.get_traceback(), "quy_tien_mat: nhac nop chua khop")


def kiem_quy_trong_ngay(ngay):
	"""Các lần kiểm quỹ của một ngày, cho tin Tiền cuối ngày."""
	return frappe.get_all(DT, filters={"loai": KIEM, "ngay": str(ngay), "trang_thai": ["in", ["Khớp", "Đã ghi", "Chờ duyệt"]]},
		fields=["luc", "lech", "ly_do", "trang_thai"], order_by="luc asc", limit_page_length=0)
