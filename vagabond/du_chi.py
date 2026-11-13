# -*- coding: utf-8 -*-
"""Dự chi công nợ nhà cung cấp: trả hai đợt ngày 10 và 20 (issue #555, v653).

Vì sao có tệp này
-----------------
Trước 12/11/2026 tiền trả nhà cung cấp được lập trong một bảng Excel tay
("Dự chi công nợ tháng 10/2026") rồi mới lập từng hồ sơ thanh toán (APP) và
duyệt từng tờ. Bảng tay lệch số ERP (Printeco ghi 362.690.082, ERP còn
231.105.722), và gần như mọi hoá đơn mua có hạn trả bằng đúng ngày hoá đơn
(574 trên 576 dòng đã trả), nên màn Công nợ phải trả báo cả 350 tờ "Quá hạn".

Anh Việt 12/11/2026: *"thêm luồng phân hệ dự trù công nợ cần trả (thường trả
1 tháng 2 đợt vào 10 và 20 hàng tháng), đi thương lượng với các nhà cung cấp
để trả hết toàn bộ hoặc trả một phần với các hoá đơn nào và tính ra phần công
nợ còn lại sau khi trả"*. Anh chọn (bốn ảnh duyệt cùng ngày):

1. Hạn trả theo ô "Số ngày được nợ" trên hồ sơ nhà cung cấp, máy gợi số theo
   lịch sử trả, Uyên xác nhận dần. Hoá đơn đã ghi sổ không bị sửa hạn: máy chỉ
   TỰ TÍNH hạn dự tính để xếp thứ tự (`han_du_tinh`, một nguồn cho cả màn Công
   nợ phải trả).
2. Duyệt cả đợt một lần: kế toán soát, giám đốc duyệt trên đợt. Giám đốc duyệt
   xong máy chốt luôn: lập APP từng nhà cung cấp đúng số đã chọn, APP mang sẵn
   dấu duyệt của đợt, người lập APP là người lập đợt.
3. Người thương lượng là Uyên (thu mua).

Luật số (Codex PR #556 vòng 1)
------------------------------
Số còn đề nghị được của một hoá đơn = dư nợ trừ phần APP khác còn hiệu lực
đang giữ, tính bằng đúng `phan_bo_app.dang_giu_chi_tiet` (không tự tính lại).
Lúc lưu và lúc chốt đọc lại DƯỚI KHOÁ; dòng nào vượt thì dừng dòng đó, báo số
mới. Gia hạn = còn đề nghị được trừ trả đợt này, máy tính, người không gõ.

Phần THUẦN đứng trước vạch, phần chạm hệ đứng sau.
"""

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

DT = "Vagabond Dot Chi"
DT_DONG = "Vagabond Dot Chi Dong"

TT_NHAP = "Nhap"
TT_CHO_FIN = "Cho ke toan"
TT_CHO_GD = "Cho giam doc"
TT_DA_DUYET = "Da duyet"
TT_DA_CHOT = "Da chot"
TT_HUY = "Huy"
TT_SONG = (TT_NHAP, TT_CHO_FIN, TT_CHO_GD, TT_DA_DUYET)
NHAN = {
	TT_NHAP: "Thu mua đang thương lượng",
	TT_CHO_FIN: "Chờ kế toán soát",
	TT_CHO_GD: "Chờ giám đốc duyệt",
	TT_DA_DUYET: "Đã duyệt, đang lập APP",
	TT_DA_CHOT: "Đã lập APP",
	TT_HUY: "Huỷ",
}

NGAY_DOT = (10, 20)
SO_NGAY_SOAN_TRUOC = 3
SO_NGAY_NO_MAC_DINH = 30
SO_MAU_TOI_THIEU = 3
TRUONG_SO_NGAY_NO = "vgb_so_ngay_no"


# ================================================================== THUẦN


def tien(v):
	"""Decimal hữu hạn, không âm. Ô trống là 0; chữ, NaN, số âm là lỗi."""
	if v is None or (isinstance(v, str) and not v.strip()):
		return Decimal(0)
	if isinstance(v, bool):
		raise ValueError("Số tiền phải là số.")
	try:
		d = Decimal(str(v).strip().replace(",", ""))
	except (InvalidOperation, ValueError, TypeError):
		raise ValueError("Số tiền phải là số.") from None
	if not d.is_finite() or d < 0:
		raise ValueError("Số tiền phải là số không âm.")
	return d


def ngay(v):
	"""date từ date hoặc chuỗi YYYY-MM-DD; trống là None."""
	if not v:
		return None
	if isinstance(v, date):
		return v
	return date.fromisoformat(str(v)[:10])


def ngay_dot_ke_tiep(hom_nay):
	"""Ngày đợt gần nhất từ hôm nay trở đi: 10 hoặc 20 tháng này, hoặc 10 tháng sau.

	Hôm nay đúng ngày 10 thì đợt là hôm nay (đợt đang chạy chưa qua)."""
	h = ngay(hom_nay)
	for d in NGAY_DOT:
		if h.day <= d:
			return date(h.year, h.month, d)
	nam, thang = (h.year + 1, 1) if h.month == 12 else (h.year, h.month + 1)
	return date(nam, thang, NGAY_DOT[0])


def ngay_soan(ngay_dot):
	"""Máy soạn đợt nháp trước ngày đợt ba ngày (7 cho đợt 10, 17 cho đợt 20)."""
	return ngay(ngay_dot) - timedelta(days=SO_NGAY_SOAN_TRUOC)


def ma_dot(ngay_dot):
	"""DC-26-12-10: năm hai số, tháng hai số, ngày đợt."""
	d = ngay(ngay_dot)
	return "DC-%02d-%02d-%02d" % (d.year % 100, d.month, d.day)


def trung_vi(so):
	ds = sorted(int(x) for x in so)
	if not ds:
		return None
	g = len(ds) // 2
	return ds[g] if len(ds) % 2 else (ds[g - 1] + ds[g]) // 2


def goi_y_so_ngay_no(cap):
	"""Số ngày nợ máy gợi từ lịch sử: trung vị (ngày trả - ngày hoá đơn).

	cap: [(ngày hoá đơn, ngày trả)]. Dưới ba lần trả thì chưa đủ để gợi (None).
	Lần trả trước ngày hoá đơn (trả trước, cọc) không tính."""
	so = []
	for hd, tra in cap:
		a, b = ngay(hd), ngay(tra)
		if a and b and b >= a:
			so.append((b - a).days)
	if len(so) < SO_MAU_TOI_THIEU:
		return None
	return trung_vi(so)


def so_ngay_dung(da_khai, goi_y):
	"""Số ngày được nợ đang áp: Uyên đã khai thì theo khai; chưa thì theo gợi ý
	lịch sử; chưa có lịch sử thì 30. Trả (số ngày, nguồn)."""
	try:
		k = int(da_khai or 0)
	except (TypeError, ValueError):
		k = 0
	if k > 0:
		return k, "khai"
	if goi_y:
		return int(goi_y), "goi_y"
	return SO_NGAY_NO_MAC_DINH, "mac_dinh"


def han_du_tinh(ngay_hd, so_ngay_no):
	"""Hạn trả dự tính = ngày hoá đơn + số ngày được nợ. MỘT nguồn cho màn Dự
	chi và chip Quá hạn của màn Công nợ phải trả. Không đụng hạn đã ghi sổ."""
	d = ngay(ngay_hd)
	if not d:
		return None
	return d + timedelta(days=int(so_ngay_no or 0))


def goi_y_tra(co_the_tra, han, ngay_dot):
	"""Số trả máy điền sẵn: tờ tới hạn trước hoặc đúng ngày đợt thì đề nghị trả
	hết phần còn đề nghị được, tờ chưa tới hạn để 0. Đây là số ĐẶT, người sửa."""
	ct = tien(co_the_tra)
	h, d = ngay(han), ngay(ngay_dot)
	if ct <= 0:
		return Decimal(0)
	if h and d and h <= d:
		return ct
	return Decimal(0)


def kiem_so_tra(so_tra, co_the_tra):
	"""Trả (số trả, gia hạn) hoặc ném ValueError có câu nói việc làm tiếp."""
	st = tien(so_tra)
	ct = tien(co_the_tra)
	if st > ct:
		raise ValueError(
			"Số trả %s lớn hơn phần còn đề nghị được %s. Phần chênh đang nằm trong APP "
			"khác hoặc đã trả; giảm số trả rồi lưu lại." % (dinh_dang(st), dinh_dang(ct)))
	return st, ct - st


def dinh_dang(v):
	d = Decimal(str(v or 0)).quantize(Decimal(1))
	return format(int(d), ",").replace(",", ".")


def tong(dong):
	"""Ba tổng của đợt từ các dòng: còn đề nghị được, trả, gia hạn."""
	a = b = c = Decimal(0)
	for r in dong or []:
		a += tien(r.get("co_the_tra"))
		b += tien(r.get("so_tra"))
		c += tien(r.get("gia_han"))
	return a, b, c


def gop_theo_ncc(dong):
	"""Nhóm dòng theo nhà cung cấp, giữ thứ tự gặp. Chỉ dòng có trả > 0 và chưa
	có APP. Trả [(ncc, [dòng])]."""
	thu_tu, nhom = [], {}
	for r in dong or []:
		if tien(r.get("so_tra")) <= 0 or r.get("ho_so_app"):
			continue
		k = r.get("nha_cung_cap")
		if k not in nhom:
			nhom[k] = []
			thu_tu.append(k)
		nhom[k].append(r)
	return [(k, nhom[k]) for k in thu_tu]


def buoc_gui(vai_nguoi_gui, vai_fin):
	"""Gửi đợt đi duyệt thì vào bước nào: người gửi có vai kế toán thì bỏ qua
	bước kế toán soát (chép đúng nếp `ho_so_tt._buoc_ke_tiep_khi_gui`)."""
	return TT_CHO_GD if set(vai_nguoi_gui or ()) & set(vai_fin) else TT_CHO_FIN


def kiem_nguoi_duyet(buoc, nguoi, nguoi_lap, fin_boi, la_quan_tri):
	"""Câu chặn khi người duyệt trùng người lập hoặc trùng cấp trước; None là được."""
	if la_quan_tri:
		return None
	if nguoi == nguoi_lap:
		return "Người lập đợt không tự duyệt được, nhờ người khác duyệt giúp."
	if buoc == "gd" and nguoi == fin_boi:
		return "Bạn đã soát đợt này ở cấp kế toán. Hai cấp duyệt phải là hai người khác nhau."
	return None


def giu_lua_chon(cu, moi):
	"""Soạn lại đợt nháp: giữ số trả, ghi chú, hẹn Uyên đã nhập cho hoá đơn còn
	trên đợt, kẹp số trả theo phần còn đề nghị được mới. THUẦN.

	cu: {hoa_don: dòng cũ}; moi: [dòng mới máy dựng]."""
	ra = []
	for r in moi:
		c = cu.get(r.get("hoa_don"))
		if c and c.get("da_sua"):
			st = min(tien(c.get("so_tra")), tien(r.get("co_the_tra")))
			r = dict(r, so_tra=st, ghi_chu=c.get("ghi_chu") or "", hen_dot=c.get("hen_dot"), da_sua=1)
		r["gia_han"] = tien(r.get("co_the_tra")) - tien(r.get("so_tra"))
		ra.append(r)
	return ra


# ================================================================== CHẠM HỆ

import frappe  # noqa: E402
from frappe.utils import cint, flt, getdate, now_datetime, nowdate  # noqa: E402


def _ho_so():
	from vagabond import ho_so_tt
	return ho_so_tt


def _vai(nguoi=None):
	return set(frappe.get_roles(nguoi or frappe.session.user))


def _chan(nhom, viec):
	if not (set(nhom) & _vai()):
		frappe.throw("Tài khoản của bạn không có quyền %s." % viec)


def _qt():
	return "System Manager" in _vai()


def ncc_can_tru_san():
	"""Nhà cung cấp là sàn (Grab, ShopeeFood, Be...): phí sàn được cấn trừ vào
	tiền sàn trả, không chuyển khoản. Nhận ra theo phiếu Cấn trừ sàn đã có,
	không gõ cứng tên (Q-D5)."""
	try:
		return set(frappe.get_all("Vagabond Can Tru San", filters={"docstatus": ["<", 2]},
			pluck="nha_cung_cap", distinct=True, limit_page_length=0)) - {None, ""}
	except Exception:
		return set()


def lich_su_tra(ds_ncc):
	"""{ncc: [(ngày hoá đơn, ngày trả)]} từ hồ sơ APP đã thanh toán."""
	if not ds_ncc:
		return {}
	rows = frappe.db.sql("""select p.nha_cung_cap, d.ngay_hd, p.ngay_thanh_toan
		from `tabVagabond Ho So TT Dong` d join `tabVagabond Ho So TT` p on p.name=d.parent
		where p.trang_thai='Da thanh toan' and p.loai='NCC' and p.nha_cung_cap in %s
		and ifnull(d.hoa_don,'')!='' and p.ngay_thanh_toan is not null""", (tuple(ds_ncc),), as_dict=True)
	ra = {}
	for r in rows:
		ra.setdefault(r.nha_cung_cap, []).append((r.ngay_hd, r.ngay_thanh_toan))
	return ra


def so_ngay_no_cua(ds_ncc):
	"""{ncc: (số ngày, nguồn, gợi ý)} cho một loạt nhà cung cấp. MỘT nguồn."""
	if not ds_ncc:
		return {}
	khai = {}
	try:
		for r in frappe.get_all("Supplier", filters={"name": ["in", list(ds_ncc)]},
				fields=["name", TRUONG_SO_NGAY_NO], limit_page_length=0):
			khai[r.name] = r.get(TRUONG_SO_NGAY_NO)
	except Exception:
		pass
	ls = lich_su_tra(ds_ncc)
	ra = {}
	for k in ds_ncc:
		g = goi_y_so_ngay_no(ls.get(k) or [])
		so, nguon = so_ngay_dung(khai.get(k), g)
		ra[k] = (so, nguon, g)
	return ra


def gan_han_du_tinh(rows):
	"""Thêm `han_du_tinh` vào các dòng hoá đơn mua (có supplier, bill_date hoặc
	posting_date). Dùng cho màn Công nợ phải trả để chip Quá hạn đúng nghĩa."""
	ncc = {r.get("supplier") for r in rows if r.get("supplier")}
	so = so_ngay_no_cua(ncc)
	for r in rows:
		s = so.get(r.get("supplier"))
		if s:
			h = han_du_tinh(r.get("bill_date") or r.get("posting_date"), s[0])
			r["han_du_tinh"] = str(h) if h else ""
	return rows


def _so_du_tk_chi():
	"""Số dư tài khoản chi chuyển khoản theo SePay. Không đọc được thì None."""
	try:
		from vagabond import tai_chinh
		from vagabond.tra_tien_app import tk_tien_chi
		cong_ty = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
		_tk, ba = tk_tien_chi(cong_ty, "Chuyển khoản")
		so_tk = frappe.db.get_value("Bank Account", ba, "bank_account_no") if ba else None
		bao = tai_chinh._sepay_so_bao()
		v = bao.get(str(so_tk or "").strip())
		return flt(v) if v is not None else None
	except Exception:
		return None


def _hd_trong_dot_khac(tru_ma):
	"""Hoá đơn đang nằm trong một đợt khác còn sống: {hoá đơn: mã đợt}."""
	rows = frappe.db.sql("""select d.hoa_don, p.name from `tabVagabond Dot Chi Dong` d
		join `tabVagabond Dot Chi` p on p.name=d.parent
		where p.trang_thai in %s and p.name!=%s and ifnull(d.hoa_don,'')!='' and ifnull(d.ho_so_app,'')=''""",
		(TT_SONG, tru_ma or ""), as_dict=True)
	return {r.hoa_don: r.name for r in rows}


def _dang_giu(ds_hd, khoa=False):
	"""{hoá đơn: tiền APP khác đang giữ}, từ đúng hàm của phan_bo_app."""
	if not ds_hd:
		return {}
	from vagabond.phan_bo_app import dang_giu_chi_tiet
	ra = {}
	for (_ten, _ma, hd), t in dang_giu_chi_tiet(khoa=khoa, hoa_don=ds_hd).items():
		ra[hd] = ra.get(hd, Decimal(0)) + Decimal(str(t))
	return ra


def dung_dong(ngay_dot, tru_ma=None):
	"""Dựng các dòng đợt từ hoá đơn mua còn nợ (đọc thường, chưa khoá)."""
	san = ncc_can_tru_san()
	pi = frappe.get_all("Purchase Invoice",
		filters={"docstatus": 1, "outstanding_amount": [">", 0], "is_return": 0},
		fields=["name", "supplier", "supplier_name", "posting_date", "bill_date", "bill_no", "outstanding_amount"],
		order_by="posting_date asc", limit_page_length=0)
	pi = [r for r in pi if r.supplier not in san]
	dot_khac = _hd_trong_dot_khac(tru_ma)
	pi = [r for r in pi if r.name not in dot_khac]
	giu = _dang_giu([r.name for r in pi])
	so = so_ngay_no_cua({r.supplier for r in pi})
	nhom = {}
	try:
		for r in frappe.get_all("Supplier", filters={"name": ["in", list({x.supplier for x in pi}) or [""]]},
				fields=["name", "supplier_group"], limit_page_length=0):
			nhom[r.name] = r.supplier_group or ""
	except Exception:
		pass
	ra = []
	for r in pi:
		no = Decimal(str(r.outstanding_amount or 0))
		g = giu.get(r.name, Decimal(0))
		ct = max(Decimal(0), no - g)
		if ct <= 0:
			continue
		ngay_hd = r.bill_date or r.posting_date
		h = han_du_tinh(ngay_hd, so.get(r.supplier, (SO_NGAY_NO_MAC_DINH,))[0])
		st = goi_y_tra(ct, h, ngay_dot)
		ra.append({
			"nha_cung_cap": r.supplier, "ten_ncc": r.supplier_name or r.supplier,
			"nhom_ncc": nhom.get(r.supplier, ""), "hoa_don": r.name, "so_hd_ncc": r.bill_no or "",
			"ngay_hd": ngay_hd, "han_du_tinh": h, "con_no": no, "dang_giu": g, "co_the_tra": ct,
			"so_tra": st, "gia_han": ct - st, "ghi_chu": "", "hen_dot": None,
		})
	ra.sort(key=lambda x: (x["ten_ncc"] or "", str(x["han_du_tinh"] or ""), x["hoa_don"]))
	return ra


def _ghi_chu_dot_truoc(ds_hd, tru_ma):
	"""Ghi chú thương lượng, hẹn trả của đợt đã chốt gần nhất cho từng hoá đơn."""
	if not ds_hd:
		return {}
	rows = frappe.db.sql("""select d.hoa_don, d.ghi_chu, d.hen_dot from `tabVagabond Dot Chi Dong` d
		join `tabVagabond Dot Chi` p on p.name=d.parent
		where p.trang_thai=%s and p.name!=%s and d.hoa_don in %s and ifnull(d.ghi_chu,'')!=''
		order by p.ngay_dot desc""", (TT_DA_CHOT, tru_ma or "", tuple(ds_hd)), as_dict=True)
	ra = {}
	for r in rows:
		ra.setdefault(r.hoa_don, r)
	return ra


def _dat_tong(doc):
	a, b, c = tong([d.as_dict() for d in doc.dong])
	doc.tong_de_nghi, doc.tong_tra, doc.tong_gia_han = flt(a), flt(b), flt(c)


def _ghi_dong(doc, dong):
	doc.set("dong", [])
	for r in dong:
		x = {k: v for k, v in r.items() if k != "da_sua"}
		for k in ("con_no", "dang_giu", "co_the_tra", "so_tra", "gia_han"):
			x[k] = flt(x.get(k))
		doc.append("dong", x)


def soan(ngay_dot=None, nguoi=None):
	"""Soạn hoặc soạn lại đợt nháp của ngày đợt. Đợt đã gửi duyệt thì không đụng.

	Gọi từ nhịp tự động (ngày 7 và 17) và từ nút Soạn lại trên màn."""
	nd = ngay(ngay_dot) if ngay_dot else ngay_dot_ke_tiep(getdate(nowdate()))
	ma = ma_dot(nd)
	if frappe.db.exists(DT, ma):
		doc = frappe.get_doc(DT, ma, for_update=True)
		if doc.trang_thai != TT_NHAP:
			return doc
		cu = {d.hoa_don: dict(d.as_dict(), da_sua=1 if d.get("ghi_chu") or d.get("hen_dot") or flt(d.so_tra) != flt(goi_y_tra(d.co_the_tra, d.han_du_tinh, nd)) else 0) for d in doc.dong}
	else:
		doc = frappe.new_doc(DT)
		doc.ma = ma
		doc.ngay_dot = nd
		doc.trang_thai = TT_NHAP
		doc.nguoi_lap = nguoi or frappe.session.user
		cu = {}
	moi = dung_dong(nd, tru_ma=ma)
	truoc = _ghi_chu_dot_truoc([r["hoa_don"] for r in moi], ma)
	for r in moi:
		t = truoc.get(r["hoa_don"])
		if t and r["hoa_don"] not in cu:
			r["ghi_chu"] = "Đợt trước: %s" % t.ghi_chu
			r["hen_dot"] = t.hen_dot
	_ghi_dong(doc, giu_lua_chon(cu, moi))
	_dat_tong(doc)
	doc.so_du_mb = _so_du_tk_chi()
	doc.flags.ignore_permissions = True
	doc.flags.vgb_du_chi = True
	if not doc.is_new():
		doc.save(ignore_permissions=True)
		return doc
	try:
		doc.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# Nhịp ngày 7 và nút Soạn đợt của Uyên chạy cùng lúc: bên đến sau đọc
		# lại đợt bên kia vừa tạo (dưới khoá) thay vì báo lỗi trùng mã.
		frappe.db.rollback()
		return soan(nd, nguoi)
	return doc


def _cho_man(doc):
	ho = _ho_so()
	dong = []
	for d in doc.dong:
		dong.append({
			"idx": d.idx, "ncc": d.nha_cung_cap, "ten_ncc": d.ten_ncc, "nhom": d.nhom_ncc,
			"hoa_don": d.hoa_don, "so_hd": d.so_hd_ncc, "ngay_hd": str(d.ngay_hd or ""),
			"han": str(d.han_du_tinh or ""), "con_no": flt(d.con_no), "dang_giu": flt(d.dang_giu),
			"co_the_tra": flt(d.co_the_tra), "so_tra": flt(d.so_tra), "gia_han": flt(d.gia_han),
			"ghi_chu": d.ghi_chu or "", "hen_dot": str(d.hen_dot or ""), "app": d.ho_so_app or "",
			"ket_qua": d.ket_qua or "",
		})
	so = so_ngay_no_cua({d["ncc"] for d in dong})
	return {
		"ma": doc.name, "ngay_dot": str(doc.ngay_dot), "trang_thai": doc.trang_thai,
		"nhan": NHAN.get(doc.trang_thai, doc.trang_thai), "tong_de_nghi": flt(doc.tong_de_nghi),
		"tong_tra": flt(doc.tong_tra), "tong_gia_han": flt(doc.tong_gia_han),
		"so_du": doc.so_du_mb if doc.so_du_mb not in (None, "") else None,
		"nguoi_lap": doc.nguoi_lap, "ten_nguoi_lap": ho._ten_nguoi(doc.nguoi_lap) if doc.nguoi_lap else "",
		"fin_boi": ho._ten_nguoi(doc.fin_boi) if doc.fin_boi else "", "fin_luc": str(doc.fin_luc or ""),
		"gd_boi": ho._ten_nguoi(doc.gd_boi) if doc.gd_boi else "", "gd_luc": str(doc.gd_luc or ""),
		"ly_do_tra_lai": doc.ly_do_tra_lai or "", "dong": dong,
		"so_ngay_no": {k: {"so": v[0], "nguon": v[1], "goi_y": v[2]} for k, v in so.items()},
		"quyen": {"sua": 1 if (_vai() & ho.VAI_LAP) else 0, "fin": 1 if (_vai() & ho.VAI_FIN) else 0,
			"gd": 1 if (_vai() & ho.VAI_GD) else 0},
	}


@frappe.whitelist()
def ds(so_dot=8):
	"""Danh sách đợt mới nhất trước, kèm đợt kế tiếp chưa soạn."""
	ho = _ho_so()
	_chan(ho.VAI_LAP | ho.VAI_FIN | ho.VAI_GD, "xem dự chi công nợ")
	rows = frappe.get_all(DT, fields=["name", "ngay_dot", "trang_thai", "tong_tra", "tong_gia_han", "tong_de_nghi"],
		order_by="ngay_dot desc", limit_page_length=cint(so_dot) or 8)
	ke = ngay_dot_ke_tiep(getdate(nowdate()))
	return {"dot": [dict(r, nhan=NHAN.get(r.trang_thai, r.trang_thai), ngay_dot=str(r.ngay_dot)) for r in rows],
		"ke_tiep": str(ke), "ma_ke_tiep": ma_dot(ke), "da_co": 1 if frappe.db.exists(DT, ma_dot(ke)) else 0}


@frappe.whitelist()
def chi_tiet(ma):
	ho = _ho_so()
	_chan(ho.VAI_LAP | ho.VAI_FIN | ho.VAI_GD, "xem dự chi công nợ")
	return _cho_man(frappe.get_doc(DT, ma))


@frappe.whitelist(methods=["POST"])
def soan_lai(ngay_dot=None):
	"""Nút Soạn đợt / Soạn lại: đọc lại dư nợ ERP, giữ số Uyên đã sửa."""
	ho = _ho_so()
	_chan(ho.VAI_LAP, "soạn dự chi công nợ")
	doc = soan(ngay_dot)
	if doc.trang_thai != TT_NHAP:
		frappe.throw("Đợt %s đang ở bước %s, không soạn lại được." % (doc.name, NHAN.get(doc.trang_thai)))
	frappe.db.commit()
	return _cho_man(doc)


@frappe.whitelist(methods=["POST"])
def luu(ma, dong=None):
	"""Lưu số trả, ghi chú, hẹn của các dòng. Đọc lại dư nợ và phần APP khác
	đang giữ DƯỚI KHOÁ rồi mới kiểm (H8 loại 1, Codex #556)."""
	ho = _ho_so()
	_chan(ho.VAI_LAP, "sửa dự chi công nợ")
	if isinstance(dong, str):
		dong = frappe.parse_json(dong)
	doc = frappe.get_doc(DT, ma, for_update=True)
	if doc.trang_thai != TT_NHAP:
		frappe.throw("Đợt %s đang ở bước %s. Muốn sửa thì nhờ kế toán hoặc giám đốc trả lại." % (doc.name, NHAN.get(doc.trang_thai)))
	theo = {str(x.get("hoa_don")): x for x in (dong or []) if x.get("hoa_don")}
	ds_hd = [d.hoa_don for d in doc.dong if d.hoa_don in theo]
	if ds_hd:
		frappe.db.sql("select name from `tabPurchase Invoice` where name in %s for update", (tuple(ds_hd),))
	no = {r.name: Decimal(str(r.outstanding_amount or 0)) for r in frappe.get_all("Purchase Invoice",
		filters={"name": ["in", ds_hd or [""]]}, fields=["name", "outstanding_amount"], limit_page_length=0)}
	giu = _dang_giu(ds_hd, khoa=True)
	loi = []
	for d in doc.dong:
		x = theo.get(d.hoa_don)
		if not x:
			continue
		ct = max(Decimal(0), no.get(d.hoa_don, Decimal(0)) - giu.get(d.hoa_don, Decimal(0)))
		# Codex #560: lưu chỉ ghi chú hay ngày hẹn thì màn không gửi so_tra; giữ
		# số đang lưu (kẹp theo phần còn trả được), không hiểu thành 0. Số 0
		# gửi lên rõ ràng vẫn là 0.
		vao = x.get("so_tra") if ("so_tra" in x and x.get("so_tra") not in (None, "")) else min(tien(d.so_tra), ct)
		try:
			st, gh = kiem_so_tra(vao, ct)
		except ValueError as e:
			loi.append("%s (%s): %s" % (d.so_hd_ncc or d.hoa_don, d.ten_ncc, e))
			continue
		d.con_no, d.dang_giu, d.co_the_tra = flt(no.get(d.hoa_don, 0)), flt(giu.get(d.hoa_don, 0)), flt(ct)
		d.so_tra, d.gia_han = flt(st), flt(gh)
		if "ghi_chu" in x:
			d.ghi_chu = (x.get("ghi_chu") or "").strip()
		if "hen_dot" in x:
			d.hen_dot = x.get("hen_dot") or None
	if loi:
		frappe.throw("Chưa lưu được %d dòng:<br>%s" % (len(loi), "<br>".join(loi[:8]) + ("<br>và %d dòng nữa" % (len(loi) - 8) if len(loi) > 8 else "")))
	_dat_tong(doc)
	doc.flags.ignore_permissions = True
	doc.flags.vgb_du_chi = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return _cho_man(doc)


@frappe.whitelist(methods=["POST"])
def gui(ma):
	ho = _ho_so()
	_chan(ho.VAI_LAP, "gửi đợt dự chi đi duyệt")
	doc = frappe.get_doc(DT, ma, for_update=True)
	if doc.trang_thai != TT_NHAP:
		frappe.throw("Đợt %s đang ở bước %s, không gửi lại được." % (doc.name, NHAN.get(doc.trang_thai)))
	if flt(doc.tong_tra) <= 0:
		frappe.throw("Đợt chưa có dòng nào trả. Nhập số trả cho ít nhất một hoá đơn rồi gửi.")
	doc.trang_thai = buoc_gui(_vai(), ho.VAI_FIN)
	if doc.trang_thai == TT_CHO_GD:
		doc.fin_boi, doc.fin_luc = frappe.session.user, now_datetime()
	# Người gửi là người đã thương lượng (đợt nháp có thể do máy soạn): ghi
	# người này làm người lập để hai cấp duyệt không tự duyệt tờ của mình.
	doc.nguoi_lap = frappe.session.user
	doc.ly_do_tra_lai = ""
	doc.flags.ignore_permissions = True
	doc.flags.vgb_du_chi = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return _cho_man(doc)


@frappe.whitelist(methods=["POST"])
def duyet(ma, buoc, ly_do=""):
	"""buoc: fin (kế toán soát) / gd (giám đốc duyệt, máy chốt luôn) /
	tra_lai (về Uyên sửa, phải có lý do) / huy."""
	ho = _ho_so()
	toi = frappe.session.user
	doc = frappe.get_doc(DT, ma, for_update=True)
	buoc = (buoc or "").strip()
	if buoc == "fin":
		_chan(ho.VAI_FIN, "soát đợt dự chi ở cấp kế toán")
		if doc.trang_thai != TT_CHO_FIN:
			frappe.throw("Đợt đang ở %s, chưa tới lượt kế toán soát." % NHAN.get(doc.trang_thai))
		c = kiem_nguoi_duyet("fin", toi, doc.nguoi_lap, None, _qt())
		if c:
			frappe.throw(c)
		doc.trang_thai, doc.fin_boi, doc.fin_luc = TT_CHO_GD, toi, now_datetime()
	elif buoc == "gd":
		_chan(ho.VAI_GD, "duyệt đợt dự chi ở cấp giám đốc")
		if doc.trang_thai != TT_CHO_GD:
			frappe.throw("Đợt đang ở %s, chưa tới lượt giám đốc duyệt." % NHAN.get(doc.trang_thai))
		c = kiem_nguoi_duyet("gd", toi, doc.nguoi_lap, doc.fin_boi, _qt())
		if c:
			frappe.throw(c)
		doc.trang_thai, doc.gd_boi, doc.gd_luc = TT_DA_DUYET, toi, now_datetime()
	elif buoc == "tra_lai":
		_chan(ho.VAI_FIN | ho.VAI_GD, "trả lại đợt dự chi")
		if not (ly_do or "").strip():
			frappe.throw("Trả lại thì ghi lý do, để Thu mua biết sửa gì.")
		if doc.trang_thai not in (TT_CHO_FIN, TT_CHO_GD):
			frappe.throw("Đợt đang ở %s, không trả lại được." % NHAN.get(doc.trang_thai))
		doc.trang_thai, doc.ly_do_tra_lai = TT_NHAP, ly_do.strip()
		doc.fin_boi = doc.fin_luc = doc.gd_boi = doc.gd_luc = None
	elif buoc == "huy":
		_chan(ho.VAI_LAP | ho.VAI_GD, "huỷ đợt dự chi")
		if doc.trang_thai not in (TT_NHAP, TT_CHO_FIN, TT_CHO_GD):
			frappe.throw("Đợt đang ở %s, không huỷ được." % NHAN.get(doc.trang_thai))
		doc.trang_thai, doc.ly_do_tra_lai = TT_HUY, (ly_do or "").strip()
	else:
		frappe.throw("Bước duyệt không hợp lệ: %s." % buoc)
	doc.flags.ignore_permissions = True
	doc.flags.vgb_du_chi = True
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	if buoc == "gd":
		chot(doc.name)
		doc = frappe.get_doc(DT, doc.name)
	return _cho_man(doc)


def ghi_chu_app(ma):
	"""Ghi chú trên APP sinh từ đợt; cũng là dấu để nhận lại APP khi chốt lại."""
	return "Theo đợt dự chi %s" % ma


def _app_da_lap(ma, ds_hd):
	"""APP còn sống đã lập cho đúng các hoá đơn này từ đúng đợt này, nếu có."""
	if not ds_hd:
		return None
	r = frappe.db.sql("""select distinct p.name from `tabVagabond Ho So TT` p
		join `tabVagabond Ho So TT Dong` d on d.parent=p.name
		where p.ghi_chu=%s and p.trang_thai not in ('Huy','Tu choi') and d.hoa_don in %s""",
		(ghi_chu_app(ma), tuple(ds_hd)))
	return r[0][0] if r else None


def _ap_dau_duyet(ten_app, dot):
	"""APP sinh từ đợt: người lập là người lập đợt, hai chữ ký là của đợt."""
	ho = _ho_so()
	frappe.db.set_value("Vagabond Ho So TT", ten_app, {
		"trang_thai": ho.TT_DA_DUYET, "nguoi_tao": dot.nguoi_lap,
		"fin_boi": dot.fin_boi, "fin_luc": dot.fin_luc, "gd_boi": dot.gd_boi, "gd_luc": dot.gd_luc,
	})
	ho._ghi_vet(ten_app, "Duyệt theo đợt dự chi %s: kế toán %s, giám đốc %s" % (dot.name, dot.fin_boi or "", dot.gd_boi or ""))


def _lap_app_thay(nguoi_lap, ncc, ds_dong, ma):
	"""Lập APP đứng tên người lập đợt (Uyên), kể cả khi người bấm là giám đốc.

	ho_so_tt.tao chỉ cho vai lập hồ sơ gọi; giám đốc chỉ có vai AP Giám đốc
	nên gọi thẳng thì mọi nhà cung cấp đều hỏng. Đợt đã qua đủ hai cấp duyệt,
	nên máy lập thay đúng người đã lập đợt rồi trả lại phiên như cũ."""
	ho = _ho_so()
	cu = frappe.session.user
	doi = bool(nguoi_lap) and nguoi_lap != cu
	if doi:
		frappe.set_user(nguoi_lap)
	try:
		r = ho.tao(ncc=ncc, hoa_don=[{"hoa_don": d["hoa_don"], "so_tien": flt(d["so_tra"])} for d in ds_dong],
			ghi_chu=ghi_chu_app(ma), gui_luon=0)
	finally:
		if doi:
			frappe.set_user(cu)
	return r["ma"]


@frappe.whitelist(methods=["POST"])
def chot(ma):
	"""Lập APP từng nhà cung cấp cho đợt đã duyệt. Chạy lại được: dòng đã có APP
	thì bỏ qua, nhà cung cấp lỗi thì ghi lỗi vào dòng và đi tiếp (Q-D4)."""
	ho = _ho_so()
	_chan(ho.VAI_LAP | ho.VAI_GD, "chốt đợt dự chi")
	# Mỗi nhà cung cấp commit riêng (ho_so_tt.tao tự commit) nên khoá dòng của đợt
	# chỉ giữ tới lần commit đầu. Khoá có tên giữ suốt lượt: giám đốc vừa duyệt
	# (máy chốt) mà Uyên bấm Lập APP cho phần còn lỗi thì lượt sau chờ, không lập
	# trùng APP (H8 loại 1 và 4).
	r = frappe.db.sql("select get_lock(%s, 30)", ("vgb_du_chi_chot:%s" % ma,))
	if not r or r[0][0] != 1:
		frappe.throw("Đợt %s đang được lập APP ở một lượt khác. Chờ một phút rồi mở lại đợt." % ma)
	try:
		return _chot(ho, ma)
	finally:
		frappe.db.sql("select release_lock(%s)", ("vgb_du_chi_chot:%s" % ma,))


def _chot(ho, ma):
	dot = frappe.get_doc(DT, ma, for_update=True)
	if dot.trang_thai != TT_DA_DUYET:
		frappe.throw("Đợt %s đang ở %s, chưa chốt được." % (dot.name, NHAN.get(dot.trang_thai)))
	# Codex #560: không tin riêng ô trạng thái. Đợt phải có dấu giám đốc duyệt
	# ghi bởi duyet(); thiếu dấu thì không lập APP đã duyệt.
	if not dot.get("gd_boi") or not dot.get("gd_luc"):
		frappe.throw("Đợt %s chưa có dấu giám đốc duyệt trên màn Dự chi công nợ, chưa chốt được." % dot.name)
	ket = {"lap": [], "loi": []}
	for ncc, ds_dong in gop_theo_ncc([d.as_dict() for d in dot.dong]):
		ten = [d["name"] for d in ds_dong]
		try:
			# Lần chốt trước đã lập APP rồi hỏng ở bước sau (ho_so_tt.tao tự
			# commit): nhận lại đúng APP đó, không lập lần hai.
			app = _app_da_lap(dot.name, [d["hoa_don"] for d in ds_dong])
			if not app:
				app = _lap_app_thay(dot.nguoi_lap, ncc, ds_dong, dot.name)
			_ap_dau_duyet(app, dot)
			for t in ten:
				frappe.db.set_value(DT_DONG, t, {"ho_so_app": app, "ket_qua": ""})
			frappe.db.commit()
			ket["lap"].append(app)
		except Exception as e:
			frappe.db.rollback()
			cau = str(getattr(e, "message", "") or e)[:300]
			for t in ten:
				frappe.db.set_value(DT_DONG, t, "ket_qua", cau)
			frappe.db.commit()
			ket["loi"].append({"ncc": ncc, "loi": cau})
			frappe.log_error(frappe.get_traceback(), "du_chi.chot %s %s" % (ma, ncc))
	dot = frappe.get_doc(DT, ma)
	con = [d for d in dot.dong if flt(d.so_tra) > 0 and not d.ho_so_app]
	if not con:
		dot.db_set({"trang_thai": TT_DA_CHOT, "chot_luc": now_datetime()})
		frappe.db.commit()
	ket["con"] = len(con)
	return ket


@frappe.whitelist()
def ds_chuyen_khoan(ma):
	"""Danh sách chuyển khoản của đợt đã chốt: mỗi APP một dòng, kèm nội dung CK."""
	ho = _ho_so()
	_chan(ho.VAI_LAP | ho.VAI_FIN | ho.VAI_GD, "xem danh sách chuyển khoản")
	app = sorted({d.ho_so_app for d in frappe.get_doc(DT, ma).dong if d.ho_so_app})
	ra = []
	for a in app:
		x = frappe.db.get_value("Vagabond Ho So TT", a, ["name", "ten_ncc", "ten_nhan", "stk_nhan",
			"ngan_hang_nhan", "tong_tien", "trang_thai", "noi_dung_ck"], as_dict=True)
		if x:
			ra.append(dict(x, nhan=ho.NHAN.get(x.trang_thai, x.trang_thai), tong_tien=flt(x.tong_tien)))
	return {"dong": ra}


@frappe.whitelist(methods=["POST"])
def luu_so_ngay_no(ncc, so_ngay):
	"""Uyên xác nhận số ngày được nợ của một nhà cung cấp (0 là bỏ khai)."""
	ho = _ho_so()
	_chan(ho.VAI_LAP, "khai số ngày được nợ")
	try:
		n = int(str(so_ngay).strip() or 0)
	except ValueError:
		frappe.throw("Số ngày được nợ phải là số nguyên, ví dụ 30.")
	if n < 0 or n > 365:
		frappe.throw("Số ngày được nợ từ 0 tới 365.")
	if not frappe.db.exists("Supplier", ncc):
		frappe.throw("Không có nhà cung cấp %s." % ncc)
	frappe.db.set_value("Supplier", ncc, TRUONG_SO_NGAY_NO, n)
	frappe.db.commit()
	return {"ok": 1, "so_ngay": n}


# ------------------------------------------------- nhịp tự động, Việc cần làm

TRUONG_MOI = {
	"Supplier": [
		{
			"fieldname": TRUONG_SO_NGAY_NO,
			"label": "Số ngày được nợ",
			"fieldtype": "Int",
			"insert_after": "supplier_group",
			"description": "Số ngày nhà cung cấp cho nợ kể từ ngày hoá đơn. Để 0 thì máy dùng số gợi ý theo lịch sử trả (màn Dự chi công nợ).",
		},
	],
}


def lam_soan_tu_dong(c, bay):
	"""Nhịp Cài đặt tự động hoá: đúng ngày soạn (7, 17) sau giờ chạy thì soạn đợt
	nháp và nhắn nhóm Thu mua một lần."""
	from vagabond import kenh_zalo, viec_tu_dong as vtd

	hom = getdate(nowdate())
	nd = ngay_dot_ke_tiep(hom)
	if hom < ngay_soan(nd) or not vtd.da_qua(c.get("gio"), bay):
		return
	khoa = "vtd-du-chi:%s" % ma_dot(nd)
	if not vtd._chua_bao(khoa):
		return
	doc = soan(nd, nguoi="Administrator")
	kenh_zalo.bao_hoac_ghi_loi("viec", "kho", "Dự chi công nợ đợt %s đã soạn" % nd.strftime("%d/%m"),
		["Máy soạn sẵn đợt %s: đề nghị trả %s đ, gia hạn %s đ." % (doc.name, dinh_dang(doc.tong_tra), dinh_dang(doc.tong_gia_han)),
			"Mở Dự chi công nợ, thương lượng từng nhà cung cấp rồi bấm Gửi duyệt trước %s." % (c.get("han") or "hạn")],
		link=vtd._url("/du-chi-cong-no"), khoa=khoa, ma_tin="tm_du_chi")
	vtd._da_bao(khoa)


def viec(vai):
	"""Dòng Việc cần làm: Uyên thấy đợt nháp; kế toán thấy đợt chờ soát; giám
	đốc thấy đợt chờ duyệt."""
	ho = _ho_so()
	buoc = []
	if vai & ho.VAI_LAP:
		buoc.append(TT_NHAP)
	if vai & ho.VAI_FIN:
		buoc.append(TT_CHO_FIN)
	if vai & ho.VAI_GD:
		buoc.append(TT_CHO_GD)
	if not buoc:
		return []
	from vagabond import viec_tu_dong as vtd
	ra = []
	for r in frappe.get_all(DT, filters={"trang_thai": ["in", buoc]},
			fields=["name", "ngay_dot", "trang_thai", "tong_tra", "tong_gia_han"], order_by="ngay_dot asc", limit_page_length=10):
		qua = getdate(r.ngay_dot) <= getdate(nowdate())
		ra.append(vtd.dong_viec("du_chi", r.name, NHAN.get(r.trang_thai),
			"Đợt %s · trả %s đ · gia hạn %s đ" % (getdate(r.ngay_dot).strftime("%d/%m"), dinh_dang(r.tong_tra), dinh_dang(r.tong_gia_han)),
			r.ngay_dot, qua))
	return ra
