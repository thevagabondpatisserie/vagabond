# -*- coding: utf-8 -*-
"""v527 phần B: đối chiếu hoá đơn điện tử bán ra giữa m-invoice và ERP.

Vì sao có tệp này
-----------------
Chị Dung 25/09/2026 đếm tay từng ngày, số đo lại trên site thật khớp đúng:

    ngày    m-invoice  ERP   thiếu
    17/09      175     173   14401, 14402 (thay thế tờ 14159, 14180)
    18/09      218     217   14576 (thay thế tờ 14514, đơn 92322)
    21/09      176     171   15228-15231 (tách đơn 94132 làm 4 tờ)
                             và 15217 (thay thế tờ 14634 về 0 đồng)
    22/09      162     159   15439-15441 (thay thế tờ 12736, 10749, 11191
                             của tháng 8 và đầu tháng 9)

Cả 11 tờ đều do kế toán lập thẳng trên cổng m-invoice. Máy kéo chúng về
bảng MInvoice Invoice đầy đủ (có cả số tờ gốc), nhưng bước dựng chứng từ
đóng dấu mọi tờ đầu ra không khớp mã là "Fabi xuất" rồi thôi, và không màn
nào so số tờ theo ngày. Bốn trong bảy tờ gốc đã được kế toán ghi tay trên
đơn (ô thay thế), ba tờ của 22/09 thì chưa.

Tệp này KHÔNG sửa hoá đơn nào, không ghi gì vào Sales Invoice đã ghi sổ
(AGENTS.md: không sửa dữ liệu quá khứ). Nó chỉ ĐỌC hai bảng và nối chúng:

- tờ phát hành từ ERP: khớp mã m-invoice hoặc số hoá đơn trên đơn;
- tờ thay thế/điều chỉnh: lần theo số tờ gốc (qua nhiều đời thay thế) về
  đơn bán, hoặc theo ô "thay thế" kế toán đã ghi trên đơn;
- còn lại là tờ tạo tay trên m-invoice (ví dụ tách một đơn thành bốn tờ),
  kèm gợi ý đơn cùng mã số thuế khi gợi ý đó là duy nhất.

Phần thuần ở trên (bộ kiểm chạy không cần Frappe), phần đọc Frappe ở dưới.
"""

import datetime
import re

TT_THAY = ("Thay thế", "Điều chỉnh")

LOAI_ERP = "erp"
LOAI_THAY = "thay_the"
LOAI_THAY_CHUA_NOI = "thay_the_chua_noi"
LOAI_TAO_TAY = "tao_tay"

NHAN_LOAI = {
	LOAI_ERP: "Phát hành từ ERP",
	LOAI_THAY: "Thay thế/điều chỉnh tờ của đơn",
	LOAI_THAY_CHUA_NOI: "Thay thế, tờ gốc không có trong ERP",
	LOAI_TAO_TAY: "Tạo tay trên m-invoice",
}

SO_DOI_TOI_DA = 6


def kh(x):
	"""Ký hiệu chuẩn hoá: 6 ký tự cuối, in hoa. m-invoice trả "C26MPV",
	đơn ERP ghi "1C26MPV" (thêm số mẫu đằng trước)."""
	s = str(x or "").strip().upper()
	return s[-6:] if len(s) > 6 else s


def so(x):
	"""Số hoá đơn chuẩn hoá thành chuỗi số không có số 0 đứng đầu."""
	if x is None:
		return ""
	s = str(x).strip()
	if not s:
		return ""
	try:
		n = int(float(s))
	except (TypeError, ValueError):
		return s
	return str(n) if n > 0 else ""


def tach_goc(chu):
	"""(ký hiệu, số) của tờ gốc từ ô hd_goc: "KH C26MPV - So 14180 - Ngay ..."."""
	m = re.search(r"KH\s*(\S*)\s*-\s*So\s*(\d+)", str(chu or ""))
	if not m:
		return None
	return (kh(m.group(1)), so(m.group(2)))


def tach_ghi_thay_the(chu):
	"""(ký hiệu, số) của tờ thay thế kế toán ghi tay trên đơn: "1C26MPV 14402"."""
	m = re.search(r"(\S+)\s+(\d+)\s*$", str(chu or "").strip())
	if not m:
		return None
	return (kh(m.group(1)), so(m.group(2)))


def mst(x):
	return re.sub(r"\D", "", str(x or ""))


def _ngay(v):
	if v is None or v == "":
		return None
	if isinstance(v, datetime.datetime):
		return v.date()
	if isinstance(v, datetime.date):
		return v
	return datetime.date.fromisoformat(str(v)[:10])


def ngay_lap_don(s):
	"""Ngày lập HĐĐT của một đơn: ngày chờ xuất nếu có, không thì ngày sổ."""
	return _ngay(s.get("vgb_hddt_ngay_xuat")) or _ngay(s.get("posting_date"))


class _ChiMuc:
	def __init__(self, si_ds, to_ds):
		self.id = {}
		self.so = {}
		self.thay = {}
		for s in si_ds or []:
			for k in ("custom_minvoice_id", "custom_hddt_id"):
				v = str(s.get(k) or "").strip()
				if v:
					self.id.setdefault(v, s)
			n = so(s.get("custom_hddt_so"))
			if n:
				self.so.setdefault(n, []).append(s)
			t = tach_ghi_thay_the(s.get("custom_hddt_thay_the"))
			if t:
				self.thay.setdefault(t, s)
		self.to = {}
		for t in to_ds or []:
			n = so(t.get("so_hd"))
			if n:
				self.to.setdefault((kh(t.get("ky_hieu")), n), t)

	def don_theo_so(self, k, n):
		"""Đơn mang số n. Ký hiệu hai bên đều có thì phải khớp; đơn cũ ghi
		thiếu ký hiệu (đường Python) thì chỉ nhận khi là đơn DUY NHẤT."""
		ds = self.so.get(n) or []
		khop = [s for s in ds if kh(s.get("custom_hddt_ky_hieu")) == k]
		if khop:
			return khop[0]
		trong = [s for s in ds if not kh(s.get("custom_hddt_ky_hieu"))]
		if len(trong) == 1 and len(ds) == 1:
			return trong[0]
		return None


def phan_loai(to_ds, si_ds, to_goc_ds=()):
	"""Nối từng tờ đầu ra của m-invoice về đơn bán. THUẦN.

	to_ds: tờ cần xếp loại (dict: name, so_hd, ky_hieu, trang_thai, hd_goc,
	mst_doi_tac, ...). to_goc_ds: tờ gốc nằm ngoài khoảng ngày, dùng để lần
	chuỗi thay thế nhiều đời. si_ds: đơn bán có số HĐĐT hoặc có ghi thay thế.

	Trả {tên tờ: {"loai", "don", "goi_y", "ly_do", "goc"}}.
	"""
	cm = _ChiMuc(si_ds, list(to_ds or []) + list(to_goc_ds or []))
	ra = {}
	bi_thay = {}
	for t in to_ds or []:
		k, n = kh(t.get("ky_hieu")), so(t.get("so_hd"))
		o = {"loai": "", "don": "", "goi_y": "", "ly_do": "", "goc": ""}
		s = cm.id.get(str(t.get("name") or "").strip()) or (cm.don_theo_so(k, n) if n else None)
		if s:
			o.update(loai=LOAI_ERP, don=s.get("name"))
			ra[t.get("name")] = o
			continue
		ghi = cm.thay.get((k, n)) if n else None
		goc = tach_goc(t.get("hd_goc"))
		if goc:
			o["goc"] = goc[1]
		if ghi:
			o.update(loai=LOAI_THAY, don=ghi.get("name"), ly_do="kế toán đã ghi tờ thay thế này trên đơn")
		elif str(t.get("trang_thai") or "").strip() in TT_THAY or goc:
			doi, g = 0, goc
			while g and doi < SO_DOI_TOI_DA:
				doi += 1
				s = cm.don_theo_so(*g)
				if s:
					o.update(loai=LOAI_THAY, don=s.get("name"),
						ly_do="thay tờ %s của đơn" % g[1] if doi == 1 else "thay tờ %s, lần theo %d đời thay thế" % (g[1], doi))
					break
				t2 = cm.to.get(g)
				g = tach_goc(t2.get("hd_goc")) if t2 else None
			if not o["loai"]:
				o.update(loai=LOAI_THAY_CHUA_NOI,
					ly_do="tờ gốc %s không có trong ERP" % (goc[1] if goc else "chưa rõ"))
		else:
			o["loai"] = LOAI_TAO_TAY
		if o["loai"] == LOAI_THAY and o["don"]:
			bi_thay.setdefault(o["don"], []).append(t)
		ra[t.get("name")] = o
	# Gợi ý cho tờ tạo tay: đơn cùng mã số thuế người mua. Ưu tiên đơn có tờ
	# vừa bị thay thế trong cùng đợt (tách một đơn thành nhiều tờ: tờ gốc thay
	# về 0 đồng rồi lập tờ mới). Chỉ gợi ý khi DUY NHẤT, không đoán.
	theo_mst = {}
	for s in si_ds or []:
		m = mst(s.get("vgb_xhd_mst"))
		if m:
			theo_mst.setdefault(m, {})[s.get("name")] = s
	for t in to_ds or []:
		o = ra.get(t.get("name"))
		if not o or o["loai"] != LOAI_TAO_TAY:
			continue
		ung = list((theo_mst.get(mst(t.get("mst_doi_tac"))) or {}).values())
		uu = [s for s in ung if s.get("name") in bi_thay]
		chon = uu if uu else ung
		if len(chon) == 1:
			o["goi_y"] = chon[0].get("name")
			o["ly_do"] = ("cùng mã số thuế, tờ của đơn này vừa bị thay thế" if uu
				else "đơn duy nhất cùng mã số thuế trong khoảng xem")
	return ra


def tong_hop_ngay(to_ds, ket, si_ngay_ds=()):
	"""Mỗi ngày lập một dòng. THUẦN.

	si_ngay_ds: đơn có số HĐĐT mang ngày lập trong khoảng xem, để đếm tờ ERP
	có mà m-invoice chưa kéo về, và tờ đẩy lên m-invoice sau nửa đêm (cách
	ERP nhìn thấy "ký sang ngày hôm sau": tờ chưa lên thì chưa ký được).
	"""
	ngay = {}

	def dong(d):
		return ngay.setdefault(d, {"ngay": str(d), "tren_minvoice": 0, "erp_phat_hanh": 0,
			"thay_the_noi": 0, "chua_noi": 0, "erp_ghi_nhan": 0, "lech": 0,
			"erp_chua_keo": 0, "xuat_sau_0h": 0})

	co_to = set()
	for t in to_ds or []:
		d = _ngay(t.get("ngay_lap"))
		if d is None:
			continue
		co_to.add(str(t.get("name") or ""))
		n = so(t.get("so_hd"))
		if n:
			co_to.add((kh(t.get("ky_hieu")), n))
		r = dong(d)
		r["tren_minvoice"] += 1
		loai = (ket.get(t.get("name")) or {}).get("loai")
		if loai == LOAI_ERP:
			r["erp_phat_hanh"] += 1
		elif loai == LOAI_THAY:
			r["thay_the_noi"] += 1
		else:
			r["chua_noi"] += 1
	for s in si_ngay_ds or []:
		d = ngay_lap_don(s)
		if d is None:
			continue
		r = dong(d)
		ids = {str(s.get(k) or "").strip() for k in ("custom_minvoice_id", "custom_hddt_id")} - {""}
		if not (ids & co_to) and (kh(s.get("custom_hddt_ky_hieu")), so(s.get("custom_hddt_so"))) not in co_to:
			r["erp_chua_keo"] += 1
		day = _ngay(s.get("custom_minvoice_ngay_day"))
		if day is not None and day > d:
			r["xuat_sau_0h"] += 1
	for r in ngay.values():
		r["erp_ghi_nhan"] = r["erp_phat_hanh"] + r["thay_the_noi"]
		r["lech"] = r["tren_minvoice"] - r["erp_ghi_nhan"]
	return [ngay[d] for d in sorted(ngay)]


# ------------------------------------------------------------ đọc Frappe

import frappe
from frappe.utils import add_days, flt, getdate

DT_TO = "MInvoice Invoice"
TRUONG_TO = ["name", "so_hd", "ky_hieu", "ngay_lap", "trang_thai", "hd_goc", "tong_tien",
	"nguoi_mua_ban", "mst_doi_tac"]
TRUONG_DON = ["name", "posting_date", "vgb_hddt_ngay_xuat", "custom_minvoice_id", "custom_hddt_id",
	"custom_hddt_so", "custom_hddt_ky_hieu", "custom_hddt_thay_the", "custom_minvoice_ngay_day",
	"vgb_xhd_mst", "custom_pancake_display_id"]


def _ky_hieu_he():
	"""Ký hiệu đang phát hành. Không có thì DỪNG (Codex #369): trả về chuỗi
	rỗng mà vẫn chạy là đếm lẫn cả dải Fabi C26MVO cùng nằm trong bảng tờ,
	mọi con số đối chiếu sai mà không ai biết."""
	try:
		k = kh(frappe.db.get_single_value("MInvoice Phat Hanh Settings", "ky_hieu"))
	except Exception:
		frappe.throw("Không đọc được ký hiệu hoá đơn đang phát hành trong Cài đặt phát hành m-invoice. "
			"Thử lại sau ít phút; còn lỗi thì báo quản trị.")
	if not k:
		frappe.throw("Chưa đặt ký hiệu hoá đơn đang phát hành trong Cài đặt phát hành m-invoice, "
			"nên chưa đối chiếu được. Nhờ quản trị điền ký hiệu rồi chạy lại.")
	return k


def _don(filters):
	return frappe.get_all("Sales Invoice", filters=filters, fields=TRUONG_DON, limit_page_length=0)


def doc(tu, den):
	"""(to_ds, to_goc_ds, si_ds, si_ngay_ds) của khoảng ngày lập [tu, den]."""
	tu, den = getdate(tu), getdate(den)
	k = _ky_hieu_he()
	to_ds = [t for t in frappe.get_all(DT_TO, filters={"loai": "Đầu ra", "ngay_lap": ["between", [tu, den]]},
		fields=TRUONG_TO, limit_page_length=0) if kh(t.get("ky_hieu")) == k]
	# Tờ gốc có thể nằm tháng trước (15441 thay tờ 11191 ngày 26/08): đọc
	# thêm theo SỐ, lần tối đa SO_DOI_TOI_DA đời.
	can_so = {so(t.get("so_hd")) for t in to_ds} - {""}
	to_goc, da_hoi, hoi = [], set(), {g[1] for g in (tach_goc(t.get("hd_goc")) for t in to_ds) if g}
	for _i in range(SO_DOI_TOI_DA):
		hoi = hoi - da_hoi
		if not hoi:
			break
		da_hoi |= hoi
		can_so |= hoi
		moi = [t for t in frappe.get_all(DT_TO, filters={"loai": "Đầu ra", "so_hd": ["in", sorted(hoi)]},
			fields=TRUONG_TO, limit_page_length=0) if kh(t.get("ky_hieu")) == k]
		to_goc += moi
		hoi = {g[1] for g in (tach_goc(t.get("hd_goc")) for t in moi) if g}
	si = {}
	if can_so:
		for s in _don({"custom_hddt_so": ["in", sorted(can_so)]}):
			si[s.name] = s
	ids = [t.get("name") for t in to_ds if t.get("name")]
	if ids:
		for s in _don({"custom_minvoice_id": ["in", ids]}):
			si[s.name] = s
	for s in _don({"custom_hddt_thay_the": ["is", "set"]}):
		si[s.name] = s
	msts = sorted({mst(t.get("mst_doi_tac")) for t in to_ds} - {""})
	if msts:
		for s in _don({"vgb_xhd_mst": ["in", msts], "posting_date": ["between", [add_days(tu, -31), den]],
				"docstatus": 1}):
			si[s.name] = s
	si_ngay = [s for s in _don({"custom_hddt_so": ["is", "set"], "docstatus": 1,
			"posting_date": ["between", [add_days(tu, -3), den]]})
		if ngay_lap_don(s) and tu <= ngay_lap_don(s) <= den]
	return to_ds, to_goc, list(si.values()), si_ngay


def bao_cao(tu, den, _cot):
	"""BC17. _cot truyền từ bao_cao để không nhập vòng."""
	to_ds, to_goc, si_ds, si_ngay = doc(tu, den)
	ket = phan_loai(to_ds, si_ds, to_goc)
	dong = tong_hop_ngay(to_ds, ket, si_ngay)
	ban = {s.get("name"): s.get("custom_pancake_display_id") or "" for s in si_ds}
	chi_tiet = []
	for t in sorted(to_ds, key=lambda x: (str(x.get("ngay_lap") or ""), so(x.get("so_hd")).zfill(9))):
		o = ket.get(t.get("name")) or {}
		if o.get("loai") == LOAI_ERP:
			continue
		don = o.get("don") or ""
		chi_tiet.append({
			"ngay": str(t.get("ngay_lap") or ""), "so_hd": so(t.get("so_hd")),
			"trang_thai": t.get("trang_thai") or "", "nguoi_mua": t.get("nguoi_mua_ban") or "",
			"mst": t.get("mst_doi_tac") or "", "tien": flt(t.get("tong_tien")),
			"to_goc": o.get("goc") or "", "loai": NHAN_LOAI.get(o.get("loai"), ""),
			"don": don, "don_ban": ban.get(don, ""), "goi_y": o.get("goi_y") or "",
			"ghi_chu": o.get("ly_do") or "",
		})
	return {
		"cot": _cot(
			("ngay", "Ngày lập", "ngay"), ("tren_minvoice", "Trên m-invoice", "so"),
			("erp_phat_hanh", "ERP phát hành", "so"), ("thay_the_noi", "Thay thế nối được về đơn", "so"),
			("erp_ghi_nhan", "ERP ghi nhận", "so"), ("chua_noi", "Chưa có trong ERP", "so"),
			("lech", "Lệch", "so"), ("erp_chua_keo", "ERP có, chưa kéo về", "so"),
			("xuat_sau_0h", "Đẩy lên sau 0h", "so"),
		),
		"dong": dong,
		"bieu_do": {"nhan": "ngay", "gia_tri": "tren_minvoice"},
		"phu": {
			"tieu_de": "Tờ lập thẳng trên m-invoice (thay thế, điều chỉnh, tạo tay)",
			"cot": _cot(
				("ngay", "Ngày lập", "ngay"), ("so_hd", "Số", "chu"), ("trang_thai", "Trạng thái", "chu"),
				("nguoi_mua", "Người mua", "chu"), ("mst", "Mã số thuế", "chu"), ("tien", "Tổng tiền", "tien"),
				("to_goc", "Tờ gốc", "chu"), ("loai", "Loại", "chu"), ("don", "Đơn ERP", "chu"),
				("don_ban", "Mã đơn", "chu"), ("goi_y", "Gợi ý đơn", "chu"), ("ghi_chu", "Ghi chú", "chu"),
			),
			# Trả ĐỦ: bao_cao.chay cắt cho màn hình và báo, Excel lấy bản đủ.
			"dong": chi_tiet,
		},
	}
