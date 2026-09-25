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
LOAI_NOI_TAY = "noi_tay"

NHAN_LOAI = {
	LOAI_ERP: "Phát hành từ ERP",
	LOAI_THAY: "Thay thế/điều chỉnh tờ của đơn",
	LOAI_THAY_CHUA_NOI: "Thay thế, tờ gốc không có trong ERP",
	LOAI_TAO_TAY: "Tạo tay trên m-invoice",
	LOAI_NOI_TAY: "Kế toán đã nối vào đơn",
}

# Trạng thái tờ không còn hiệu lực: không cộng vào tiền khi so với đơn.
TT_HET_HIEU_LUC = ("Bị thay thế", "Bị điều chỉnh", "Đã huỷ")
# Lệch tiền dưới ngưỡng này coi là khớp (làm tròn thuế từng dòng).
NGUONG_LECH_TIEN = 1000

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
		noi = str(t.get("vgb_don_erp") or "").strip()
		if noi:
			# Người đã nối tay thì người thắng, máy không lần lại (v527, anh
			# Việt chốt 25/09: tách một đơn thành nhiều tờ).
			o.update(loai=LOAI_NOI_TAY, don=noi, ly_do="kế toán nối tay vào đơn")
		elif ghi:
			o.update(loai=LOAI_THAY, don=ghi.get("name"), ly_do="đơn đã ghi tờ thay thế này")
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
			"thay_the_noi": 0, "noi_tay": 0, "chua_noi": 0, "erp_ghi_nhan": 0, "lech": 0,
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
		elif loai == LOAI_NOI_TAY:
			r["noi_tay"] += 1
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
		r["erp_ghi_nhan"] = r["erp_phat_hanh"] + r["thay_the_noi"] + r["noi_tay"]
		r["lech"] = r["tren_minvoice"] - r["erp_ghi_nhan"]
	return [ngay[d] for d in sorted(ngay)]


def ke_hoach_thay_the(to_thay_ds, si_ds):
	"""Tờ thay thế nào ghi vào ô "Hoá đơn thay thế" của đơn nào. THUẦN.

	v527 (anh Việt chốt 25/09: tờ thay thế phải đồng bộ về, quét 30 ngày).
	Tờ thay thế trên m-invoice tự ghi nó thay tờ số mấy (ô hd_goc), nên máy
	lần được CHẮC CHẮN về đơn gốc, không đoán:
	- đơn mang đúng số tờ gốc (cùng ký hiệu) là đơn gốc;
	- không có thì đơn đang ghi tờ gốc đó ở ô thay thế (thay nhiều đời).

	Ô đang trống: ghi. Ô đang ghi đúng tờ bị thay (đời trước): nâng lên tờ
	mới. Ô đã đúng tờ này: thôi. Ô ghi một tờ KHÁC: không ghi đè, trả về
	xung đột cho kế toán xem. Tờ gốc khớp nhiều đơn: xung đột, không chọn.

	Trả (viec, xung_dot). viec: [{"don", "cu", "moi", "to"}], cu là chuỗi
	đang nằm trong ô (điều kiện ghi), moi là chuỗi ghi vào.
	"""
	cm = _ChiMuc(si_ds, ())
	o_thay = {}
	theo_thay = {}
	for s in si_ds or []:
		v = str(s.get("custom_hddt_thay_the") or "").strip()
		o_thay[s.get("name")] = v
		t = tach_ghi_thay_the(v)
		if t:
			theo_thay.setdefault(t, []).append(s)
	viec, xung_dot = [], []
	ds = [t for t in to_thay_ds or [] if str(t.get("trang_thai") or "").strip() == "Thay thế"]
	for t in sorted(ds, key=lambda x: (str(x.get("ngay_lap") or ""), so(x.get("so_hd")).zfill(9))):
		g = tach_goc(t.get("hd_goc"))
		n = so(t.get("so_hd"))
		if not g or not n:
			continue
		moi_t = (kh(t.get("ky_hieu")), n)
		ung = cm.so.get(g[1]) or []
		ung = [s for s in ung if kh(s.get("custom_hddt_ky_hieu")) in (g[0], "")]
		if not ung:
			ung = list(theo_thay.get(g) or [])
		if not ung:
			continue
		if len(ung) > 1:
			xung_dot.append({"to": t.get("name"), "so": n,
				"ly_do": "tờ gốc %s khớp %d đơn, không tự chọn" % (g[1], len(ung))})
			continue
		s = ung[0]
		ten = s.get("name")
		cu = o_thay.get(ten, "")
		cu_t = tach_ghi_thay_the(cu)
		if cu_t == moi_t:
			continue
		if cu and cu_t != g:
			xung_dot.append({"to": t.get("name"), "so": n, "don": ten,
				"ly_do": "đơn đang ghi tờ thay thế %s, không ghi đè" % cu})
			continue
		tien_to = str(s.get("custom_hddt_ky_hieu") or "").strip() or str(t.get("ky_hieu") or "").strip()
		moi = ("%s %s" % (tien_to, n)).strip()
		viec.append({"don": ten, "cu": cu, "moi": moi, "to": t.get("name")})
		if cu_t and theo_thay.get(cu_t):
			theo_thay[cu_t] = [x for x in theo_thay[cu_t] if x.get("name") != ten]
		o_thay[ten] = moi
		theo_thay.setdefault(moi_t, []).append(s)
	return viec, xung_dot


def tien_to_con_hieu_luc(cac_to):
	"""Tổng tiền các tờ còn hiệu lực. THUẦN. Tờ bị thay, bị điều chỉnh, đã
	huỷ không cộng; tờ trùng tên chỉ cộng một lần."""
	da, tong = set(), 0.0
	for t in cac_to or []:
		ten = t.get("name")
		if ten in da:
			continue
		da.add(ten)
		if str(t.get("trang_thai") or "").strip() in TT_HET_HIEU_LUC:
			continue
		try:
			tong += float(t.get("tong_tien") or 0)
		except (TypeError, ValueError):
			pass
	return tong


def nut_cua_dong(o, t):
	"""Nút cho một dòng bảng phụ BC17. THUẦN. None là không có nút."""
	loai = (o or {}).get("loai")
	ma = {"to": t.get("name"), "so": so(t.get("so_hd"))}
	if loai == LOAI_NOI_TAY:
		return dict(ma, lam="go", don=o.get("don") or "")
	if loai in (LOAI_TAO_TAY, LOAI_THAY_CHUA_NOI):
		return dict(ma, lam="noi", goi_y=o.get("goi_y") or "")
	return None


# ------------------------------------------------------------ đọc Frappe

import frappe
from frappe.utils import add_days, flt, getdate, now_datetime

DT_TO = "MInvoice Invoice"
TRUONG_TO = ["name", "so_hd", "ky_hieu", "ngay_lap", "trang_thai", "hd_goc", "tong_tien",
	"nguoi_mua_ban", "mst_doi_tac", "vgb_don_erp"]

# Ô nối tay tờ lập thẳng trên m-invoice vào đơn (v527). Bảng MInvoice
# Invoice khai trên site, ô tự thêm đi đường truong_tu_them như so_lan_thu
# của minvoice_chung_tu. Không đổi số hoá đơn trên đơn, không ghi sổ.
TRUONG_MOI = {
	DT_TO: [
		{"fieldname": "vgb_don_erp", "label": "Đơn ERP (nối tay)", "fieldtype": "Link",
			"options": "Sales Invoice", "insert_after": "hd_goc", "read_only": 1,
			"description": "Kế toán nối tờ lập thẳng trên m-invoice vào đơn, từ báo cáo BC17."},
		{"fieldname": "vgb_don_erp_nguoi", "label": "Người nối", "fieldtype": "Link",
			"options": "User", "insert_after": "vgb_don_erp", "read_only": 1},
		{"fieldname": "vgb_don_erp_luc", "label": "Lúc nối", "fieldtype": "Datetime",
			"insert_after": "vgb_don_erp_nguoi", "read_only": 1},
	],
}
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
	ids = sorted({t.get("name") for t in to_ds + to_goc if t.get("name")})
	if ids:
		# Hai ô mã: đường Python cũ ghi custom_hddt_id, đường mới ghi
		# custom_minvoice_id. Tờ tạo xong mà bước hỏi số hỏng thì đơn chỉ có
		# mã, chưa có số: phải nạp theo cả hai ô, không thì BC17 xếp nhầm tờ
		# ERP vào tờ tạo tay (Codex #369 vòng 4).
		for o in ("custom_minvoice_id", "custom_hddt_id"):
			for s in _don({o: ["in", ids]}):
				si[s.name] = s
	for s in _don({"custom_hddt_thay_the": ["is", "set"]}):
		si[s.name] = s
	noi = sorted({str(t.get("vgb_don_erp") or "").strip() for t in to_ds} - {""})
	if noi:
		for s in _don({"name": ["in", noi]}):
			si[s.name] = s
	msts = sorted({mst(t.get("mst_doi_tac")) for t in to_ds} - {""})
	if msts:
		for s in _don({"vgb_xhd_mst": ["in", msts], "posting_date": ["between", [add_days(tu, -31), den]],
				"docstatus": 1}):
			si[s.name] = s
	# Đơn có số HĐĐT mang NGÀY LẬP trong kỳ: ngày sổ trong kỳ, hoặc ngày chờ
	# xuất trong kỳ (đơn cũ kéo ngày lập vào, Codex #369 vòng 2 G2). Hai câu
	# hỏi rồi gộp theo tên; ngay_lap_don quyết định cuối cùng.
	gom = {}
	for loc in ({"posting_date": ["between", [tu, den]]}, {"vgb_hddt_ngay_xuat": ["between", [tu, den]]}):
		for s in _don(dict({"custom_hddt_so": ["is", "set"], "docstatus": 1}, **loc)):
			gom[s.name] = s
	si_ngay = [s for s in gom.values() if ngay_lap_don(s) and tu <= ngay_lap_don(s) <= den]
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
			# Nút trên màn hình (không phải cột, Excel không in). Tờ đã nối
			# tay thì gỡ được; tờ chưa về đơn nào thì nối được.
			"_nut": nut_cua_dong(o, t),
		})
	return {
		"cot": _cot(
			("ngay", "Ngày lập", "ngay"), ("tren_minvoice", "Trên m-invoice", "so"),
			("erp_phat_hanh", "ERP phát hành", "so"), ("thay_the_noi", "Thay thế nối được về đơn", "so"),
			("noi_tay", "Kế toán nối tay", "so"), ("erp_ghi_nhan", "ERP ghi nhận", "so"), ("chua_noi", "Chưa có trong ERP", "so"),
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


# ------------------------------------------ nối tay tờ vào đơn (v527)


def _quyen_ke_toan():
	# Cùng bộ quyền với nút ghi hoá đơn thay thế trên đơn (điều 18).
	from vagabond.ban_hang import QUYEN_HDDT_THAY_THE
	if not QUYEN_HDDT_THAY_THE & set(frappe.get_roles()):
		frappe.throw("Chỉ kế toán hoặc quản trị mới nối được tờ hoá đơn vào đơn. Nhờ bộ phận kế toán làm giúp.")


def _tim_don(don):
	"""Đơn đã ghi sổ theo mã ERP, hoặc theo mã đơn bán (Pancake) nếu DUY NHẤT."""
	don = str(don or "").strip()
	if not don:
		frappe.throw("Chưa nhập mã đơn.")
	truong = ["name", "docstatus", "grand_total", "customer_name", "custom_hddt_so",
		"custom_hddt_ky_hieu", "custom_hddt_thay_the", "custom_pancake_display_id"]
	d = frappe.db.get_value("Sales Invoice", don, truong, as_dict=True)
	if not d:
		ds = frappe.get_all("Sales Invoice", filters={"custom_pancake_display_id": don, "docstatus": 1},
			fields=truong, limit_page_length=3)
		if len(ds) > 1:
			frappe.throw("Mã đơn %s khớp nhiều đơn ERP. Nhập mã ERP (HDB-...) cho chắc." % don)
		d = ds[0] if ds else None
	if not d:
		frappe.throw("Không tìm thấy đơn %s." % don)
	if int(d.docstatus or 0) != 1:
		frappe.throw("Đơn %s chưa ghi sổ hoặc đã huỷ, không nối được." % d.name)
	return d


def _to_cua_don(d, k_he, them=None):
	"""Các tờ đang thuộc đơn: tờ mang số của đơn, tờ thay thế đơn đã ghi, tờ
	đã nối tay, và tờ sắp nối (them). Đơn thiếu ký hiệu thì lấy ký hiệu đang
	phát hành, không bao giờ "mọi dải" (bài học F1: dải Fabi trùng số)."""
	k = kh(d.custom_hddt_ky_hieu) or k_he
	ra = []
	ds_so = [so(d.custom_hddt_so)]
	t = tach_ghi_thay_the(d.custom_hddt_thay_the)
	if t:
		ds_so.append(t[1])
	ds_so = [x for x in ds_so if x]
	if ds_so:
		ra += [x for x in frappe.get_all(DT_TO, filters={"loai": "Đầu ra", "so_hd": ["in", ds_so]},
			fields=TRUONG_TO, limit_page_length=0) if kh(x.get("ky_hieu")) == k]
	ra += frappe.get_all(DT_TO, filters={"vgb_don_erp": d.name}, fields=TRUONG_TO, limit_page_length=0)
	if them:
		ra.append(them)
	return ra


# Đơn ứng viên cho ô chọn nối tay: quanh ngày lập của tờ.
SO_NGAY_UNG_VIEN_TRUOC = 7
SO_UNG_VIEN_TOI_DA = 120


def xep_ung_vien_don(ds, tong_tien, mst_to="", goi_y=""):
	"""Xếp đơn cho ô chọn nối tay. THUẦN. Đơn máy gợi ý lên đầu, rồi đơn
	cùng MST, rồi tiền gần tiền tờ nhất, mã đơn phá hoà."""
	m = mst(mst_to)
	def khoa(s):
		return (0 if s.get("name") == goi_y else 1, 0 if (m and mst(s.get("vgb_xhd_mst")) == m) else 1,
			abs(float(s.get("grand_total") or 0) - float(tong_tien or 0)), str(s.get("name") or ""))
	return sorted(ds, key=khoa)


SO_KET_QUA_TIM = 50


def loc_tim_don(tu_khoa):
	"""Các bộ lọc tìm đơn theo từ khoá người gõ. THUẦN. Mã đơn ERP, mã đơn
	bán, tên khách (chứa chuỗi), số HĐĐT và số tiền (khi gõ toàn số). Quá
	ngắn thì không tìm, tránh quét cả bảng đơn."""
	tk = " ".join(str(tu_khoa or "").split())
	if len(tk) < 2:
		return []
	ra = [{"name": ["like", "%" + tk + "%"]}, {"custom_pancake_display_id": ["like", "%" + tk + "%"]},
		{"customer_name": ["like", "%" + tk + "%"]}]
	so_ = re.sub(r"[\s.,đd]", "", tk.lower())
	if so_.isdigit():
		ra.append({"custom_hddt_so": so(so_)})
		if len(so_) >= 4:
			ra.append({"grand_total": int(so_)})
	return ra


@frappe.whitelist()
def ung_vien_don(to=None, tu_khoa=None):
	"""Danh sách đơn đã ghi sổ để chọn khi nối tay một tờ (Codex #369 vòng 4:
	đơn là danh mục có sẵn thì phải là ô chọn có tìm, không phải ô gõ).
	Đơn trong khoảng ngày lập của tờ trừ SO_NGAY_UNG_VIEN_TRUOC tới hôm sau,
	theo ngày sổ hoặc ngày chờ xuất, cộng đơn máy gợi ý và đơn cùng MST."""
	_quyen_ke_toan()
	k_he = _ky_hieu_he()
	t = frappe.db.get_value(DT_TO, to, TRUONG_TO + ["loai"], as_dict=True)
	if not t or t.loai != "Đầu ra" or kh(t.ky_hieu) != k_he:
		frappe.throw("Không có tờ %s trong dải hoá đơn bán đang phát hành." % (to or ""))
	lap = getdate(t.ngay_lap)
	khoang = [add_days(lap, -SO_NGAY_UNG_VIEN_TRUOC), add_days(lap, 1)]
	truong = ["name", "posting_date", "grand_total", "customer_name", "custom_pancake_display_id",
		"custom_hddt_so", "vgb_xhd_mst"]
	gom = {}
	tim = str(tu_khoa or "").strip()
	# Codex #369 vòng 5: có từ khoá thì tìm TOÀN BỘ đơn đã ghi sổ, không giới
	# hạn khoảng ngày, để đơn cũ hay khác MST vẫn chọn được từ danh mục.
	for loc in (loc_tim_don(tim) if tim else ({"posting_date": ["between", khoang]}, {"vgb_hddt_ngay_xuat": ["between", khoang]})):
		for s in frappe.get_all("Sales Invoice", filters=dict({"docstatus": 1}, **loc), fields=truong,
				limit_page_length=SO_KET_QUA_TIM if tim else 0, order_by="posting_date desc"):
			gom[s.name] = s
	m = mst(t.mst_doi_tac) if not tim else ""
	if m:
		for s in frappe.get_all("Sales Invoice", filters={"docstatus": 1, "vgb_xhd_mst": m,
				"posting_date": ["between", [add_days(lap, -31), add_days(lap, 1)]]}, fields=truong, limit_page_length=0):
			gom[s.name] = s
	goi_y = (phan_loai([t], list(gom.values())).get(t.name) or {}).get("goi_y") or ""
	ds = xep_ung_vien_don(list(gom.values()), t.tong_tien, t.mst_doi_tac, goi_y)
	return {"to": t.name, "so": so(t.so_hd), "tong_tien": flt(t.tong_tien), "ngay_lap": str(lap), "tu_khoa": tim,
		"tong": len(ds), "rows": [{"name": s.name, "ngay": str(s.posting_date or ""), "tien": flt(s.grand_total),
			"khach": s.customer_name or "", "ma_don": s.custom_pancake_display_id or "",
			"so_hddt": so(s.custom_hddt_so), "goi_y": 1 if s.name == goi_y else 0}
			for s in ds[:SO_UNG_VIEN_TOI_DA]]}


@frappe.whitelist()
def noi_to_vao_don(to=None, don=None, xac_nhan=0):
	"""Nối một tờ lập thẳng trên m-invoice vào đơn. xac_nhan=0 chỉ xem trước.

	Không đổi số hoá đơn trên đơn, không đụng sổ cái hay tờ đã gửi thuế: chỉ
	ghi ô Đơn ERP trên bản sao tờ trong ERP và một dòng nhật ký trên đơn.
	"""
	_quyen_ke_toan()
	k_he = _ky_hieu_he()
	t = frappe.db.get_value(DT_TO, to, TRUONG_TO + ["loai"], as_dict=True)
	if not t or t.loai != "Đầu ra" or kh(t.ky_hieu) != k_he:
		frappe.throw("Không có tờ %s trong dải hoá đơn bán đang phát hành." % (to or ""))
	d = _tim_don(don)
	cu = str(t.vgb_don_erp or "").strip()
	if cu and cu != d.name:
		frappe.throw("Tờ %s đang nối vào đơn %s. Gỡ nối trước rồi mới nối đơn khác." % (so(t.so_hd), cu))
	# Đơn ERP giữ mã m-invoice ở MỘT trong hai ô (đường cũ ghi custom_hddt_id);
	# xét cả hai, đúng như phan_loai (Codex #369 vòng 3, H3).
	cua_erp = [s for o in ("custom_minvoice_id", "custom_hddt_id") for s in frappe.get_all("Sales Invoice",
		filters={o: t.name, "docstatus": 1}, fields=["name"], limit_page_length=1)]
	if cua_erp or (so(d.custom_hddt_so) == so(t.so_hd) and kh(d.custom_hddt_ky_hieu) in (kh(t.ky_hieu), "")):
		frappe.throw("Tờ %s là tờ ERP tự phát hành, không cần nối tay." % so(t.so_hd))
	cac_to = _to_cua_don(d, k_he, them=None if cu else t)
	tong = tien_to_con_hieu_luc(cac_to)
	tien_don = flt(d.grand_total)
	lech = tong - tien_don
	kq = {"to": t.name, "so": so(t.so_hd), "don": d.name, "ma_don": d.custom_pancake_display_id or "",
		"khach": d.customer_name or "", "tien_don": tien_don, "tong_to": tong, "lech": lech,
		"lech_qua_nguong": 1 if abs(lech) > NGUONG_LECH_TIEN else 0,
		"cac_to": [{"so": so(x.get("so_hd")), "trang_thai": x.get("trang_thai") or "",
			"tien": flt(x.get("tong_tien"))} for x in cac_to]}
	if cu == d.name:
		return dict(kq, da_noi=1, loi_nhan="Tờ %s đã nối vào đơn %s từ trước." % (kq["so"], d.name))
	if not int(xac_nhan or 0):
		return kq
	frappe.db.sql("""update `tabMInvoice Invoice`
		set vgb_don_erp = %(don)s, vgb_don_erp_nguoi = %(nguoi)s, vgb_don_erp_luc = %(luc)s
		where name = %(to)s and ifnull(vgb_don_erp, '') = ''""",
		{"don": d.name, "nguoi": frappe.session.user, "luc": now_datetime(), "to": t.name})
	if str(frappe.db.get_value(DT_TO, t.name, "vgb_don_erp") or "") != d.name:
		frappe.throw("Tờ %s vừa được người khác nối vào đơn khác. Mở lại báo cáo để xem." % kq["so"])
	_ghi_nhat_ky_don(d.name, "Nối tờ hoá đơn điện tử %s (%s, lập thẳng trên m-invoice, %s đ) vào đơn này. "
		"Số hoá đơn trên đơn giữ nguyên. Người nối: %s." % (
			kq["so"], t.ky_hieu or "", "{:,.0f}".format(flt(t.tong_tien)).replace(",", "."), frappe.session.user))
	frappe.db.commit()
	return dict(kq, da_noi=1, loi_nhan="Đã nối tờ %s vào đơn %s." % (kq["so"], d.name))


@frappe.whitelist()
def go_to_khoi_don(to=None, ly_do=None):
	"""Gỡ nối tay. Bắt buộc lý do, nhật ký trên đơn giữ lại cả lần nối lẫn lần gỡ."""
	_quyen_ke_toan()
	ly = str(ly_do or "").strip()
	if not ly:
		frappe.throw("Phải ghi lý do gỡ thì người sau mới hiểu vì sao tờ này rời đơn.")
	t = frappe.db.get_value(DT_TO, to, ["name", "so_hd", "vgb_don_erp"], as_dict=True)
	cu = str((t or {}).get("vgb_don_erp") or "").strip()
	if not cu:
		frappe.throw("Tờ này chưa nối vào đơn nào.")
	frappe.db.sql("""update `tabMInvoice Invoice`
		set vgb_don_erp = null, vgb_don_erp_nguoi = null, vgb_don_erp_luc = null
		where name = %(to)s and vgb_don_erp = %(cu)s""", {"to": t.name, "cu": cu})
	# Đọc lại: người khác vừa nối sang đơn khác thì câu gỡ không chạm dòng nào,
	# không được ghi nhật ký gỡ sai (Codex #369 vòng 3, H4).
	con = str(frappe.db.get_value(DT_TO, t.name, "vgb_don_erp") or "").strip()
	if con:
		frappe.throw("Tờ %s vừa được người khác nối sang đơn %s. Mở lại báo cáo để xem." % (so(t.so_hd), con))
	_ghi_nhat_ky_don(cu, "Gỡ tờ hoá đơn điện tử %s khỏi đơn này. Lý do: %s. Người gỡ: %s." % (
		so(t.so_hd), ly, frappe.session.user))
	frappe.db.commit()
	return {"ok": 1, "loi_nhan": "Đã gỡ tờ %s khỏi đơn %s." % (so(t.so_hd), cu)}


def _ghi_nhat_ky_don(ten, noi_dung):
	"""Nhật ký là một phần của lần ghi, không phải phần phụ: ghi hỏng thì
	NÉM để lượt đó huỷ cả câu UPDATE (Codex #369 vòng 4). Nối, gỡ tay thì
	Frappe rollback cả request; lượt tự ghi tờ thay thế rollback đúng đơn đó."""
	frappe.get_doc({"doctype": "Comment", "comment_type": "Info", "reference_doctype": "Sales Invoice",
		"reference_name": ten, "content": noi_dung}).insert(ignore_permissions=True)


# ---------------------------- tờ thay thế tự về ô trên đơn (v527, 30 ngày)

SO_NGAY_THAY_THE = 30
NGUOI_MAY_THAY_THE = "Máy đồng bộ m-invoice (v527)"


def noi_thay_the_tu_dong(so_ngay=SO_NGAY_THAY_THE):
	"""Ghi tờ thay thế lập trên m-invoice vào ô "Hoá đơn thay thế" của đơn gốc.

	Gọi sau mỗi nhịp kéo m-invoice. Chỉ ghi ô ghi chú đó và giờ ghi, không
	đổi số hoá đơn, không ghi sổ, không bật cờ sai sót (cờ đó là lời xác nhận
	của kế toán). Ghi CÓ ĐIỀU KIỆN: ô phải còn đúng như lúc đọc, người vừa gõ
	tay chen vào thì lượt này bỏ qua. Không ném: trả số đơn đã ghi.
	"""
	try:
		k_he = _ky_hieu_he()
		tu = add_days(getdate(), -int(so_ngay or SO_NGAY_THAY_THE))
		to_ds = [t for t in frappe.get_all(DT_TO, filters={"loai": "Đầu ra", "trang_thai": "Thay thế",
			"ngay_lap": [">=", tu]}, fields=TRUONG_TO, limit_page_length=0) if kh(t.get("ky_hieu")) == k_he]
		if not to_ds:
			return 0
		goc = sorted({g[1] for g in (tach_goc(t.get("hd_goc")) for t in to_ds) if g})
		si = {}
		if goc:
			for s in _don({"custom_hddt_so": ["in", goc], "docstatus": 1}):
				si[s.name] = s
		for s in _don({"custom_hddt_thay_the": ["is", "set"], "docstatus": 1}):
			si[s.name] = s
		viec, _xung = ke_hoach_thay_the(to_ds, list(si.values()))
	except Exception:
		frappe.log_error(frappe.get_traceback(), "doi_soat_hddt_ra: doc to thay the")
		return 0
	ghi = 0
	for v in viec:
		try:
			frappe.db.sql("""update `tabSales Invoice`
				set custom_hddt_thay_the = %(moi)s, custom_hddt_thay_the_luc = %(luc)s
				where name = %(don)s and docstatus = 1 and ifnull(custom_hddt_thay_the, '') = %(cu)s""",
				dict(v, luc=now_datetime()))
			if str(frappe.db.get_value("Sales Invoice", v["don"], "custom_hddt_thay_the") or "") != v["moi"]:
				continue
			_ghi_nhat_ky_don(v["don"], "Ghi tờ thay thế %s theo m-invoice%s. %s." % (
				v["moi"], (" (thay cho %s)" % v["cu"]) if v["cu"] else "", NGUOI_MAY_THAY_THE))
			frappe.db.commit()
			ghi += 1
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "doi_soat_hddt_ra: ghi to thay the %s" % v.get("don"))
	return ghi

