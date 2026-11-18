# -*- coding: utf-8 -*-
"""v674: Bảng kê chi phí trả trước (242) và phân bổ hằng tháng.

Vì sao có tệp này
--------------------------------------------------------------------
Khải (kế toán giá thành) báo anh Việt 18/11/2026 hai chỗ hở:

1. "Với 242 thì chưa thấy Bảng kê theo dõi 242." Hoá đơn mua công cụ dụng cụ đi
   thẳng 242 từ v525, nhưng không có chỗ nào cho biết khoản nào đã phân bổ bao
   nhiêu, còn bao nhiêu, phân bổ cho bộ phận nào. Trên site lúc đó có 21 dòng sổ
   cái vào 242 (19 từ hoá đơn mua, 2 từ bút toán) mà không một dòng phân bổ.
2. "Bếp yêu cầu xuất ra để sử dụng thì hiện tại chưa có Phiếu xuất dùng dạng
   Phân bổ nhiều kỳ." Anh Việt duyệt cho 89 mã CCDC chuyển sang theo dõi tồn kho
   cùng ngày: mua về nhập kho Tổng, bếp xin xuất dùng. Phiếu xuất dùng nội bộ
   lúc đó chỉ ghi thẳng vào chi phí.

Anh Việt chốt: làm chung một PR, máy đề xuất hạch toán nhưng phải luôn có đường
làm thủ công bên cạnh.

Luật của bảng kê
--------------------------------------------------------------------
- MỖI CHỨNG TỪ ghi Nợ 242 là MỘT khoản (khoá "<loại chứng từ>:<số chứng từ>").
  Máy chỉ ĐỌC sổ cái để dựng dòng bảng kê; không sửa hoá đơn, phiếu hay bút
  toán cũ nào (luật không đụng dữ liệu quá khứ đã ghi sổ).
- Khoản cũ chưa biết phân bổ mấy tháng thì nằm ở "Chờ khai số tháng"; kế toán
  khai số tháng, tháng bắt đầu, bộ phận và tài khoản chi phí. Khoản đã phân bổ
  một phần bên ngoài hệ thống (sổ Excel cũ) thì khai ở ô "Đã phân bổ trước".
- Số đã phân bổ của một khoản = tổng Có 242 trên các bút toán ĐÃ GHI SỔ có gắn
  khoản đó (ô vgb_khoan_242 trên dòng bút toán), cộng "Đã phân bổ trước". Một
  nguồn duy nhất cho mọi nơi: màn bảng kê, xem trước, lập bút toán, hook chặn.
- Số cần phân bổ tháng M = luỹ kế theo lịch tới hết M trừ số đã phân bổ. Tháng
  nào lỡ chưa phân bổ thì tháng sau tự bù; kế toán phân bổ tay một phần thì máy
  trừ đi, không phân bổ trùng.
- Mỗi tháng máy lập MỘT bút toán nháp (but_toan_nhap), kế toán ghi sổ.
- Đường thủ công: kế toán phân bổ tay một khoản (bút toán nháp riêng), hoặc tự
  lập trên Desk/Hạch toán tay rồi chọn khoản ở dòng Có 242. Dòng Có 242 nào chưa
  gắn khoản thì máy KHÔNG lập bút toán tháng, vì không biết khoản nào đã được
  phân bổ; màn bảng kê liệt kê các dòng đó để kế toán gắn khoản ngay trên app.
- Hook trước khi ghi sổ mọi bút toán có gắn khoản: không cho phân bổ vượt
  nguyên giá, kể cả bút toán lập tay trên Desk.
"""

from vagabond import but_toan_nhap as BN

DT = "Vagabond Khoan 242"
SO_TK = "242"
SO_KY_TOI_DA = 36
CHON_SO_KY = (2, 3, 6, 12, 18, 24, 36)

TT_CHO = "Chờ khai số tháng"
TT_DANG = "Đang phân bổ"
TT_XONG = "Đã phân bổ xong"
TT_NGUNG = "Không phân bổ"
TT_HUY = "Chứng từ gốc đã huỷ"
CAC_TT = (TT_CHO, TT_DANG, TT_XONG, TT_NGUNG, TT_HUY)

NGUON_XUAT = "Phiếu xuất CCDC"
NGUON_HD = "Hoá đơn mua"
NGUON_BT = "Bút toán"
NGUON_KHAC = "Chứng từ khác"
NGUON_THEO_LOAI = {"Stock Entry": NGUON_XUAT, "Purchase Invoice": NGUON_HD, "Journal Entry": NGUON_BT}

# Tài khoản chi phí khi phân bổ, theo khối của bộ phận chịu (cây bo_phan.CAY).
# Dãy ưu tiên, khớp chính xác qua xuat_kho.chon_tai_khoan.
TK_THEO_KHOI = {
	"Khối sản xuất": ("6273", "627", "6423"),
	"Khối kinh doanh": ("6413", "641", "6423"),
	"Khối hỗ trợ": ("6423", "642"),
}
TK_MAC_DINH = ("6423", "642")


# ------------------------------------------------------------- phần thuần


def lich_phan_bo(nguyen_gia, so_ky):
	"""Số phân bổ từng tháng, nguyên đồng, cộng lại đúng nguyên giá. THUẦN.

	Chia đều, phần lẻ đồng dồn vào tháng cuối: kế toán đọc lịch thấy các tháng
	bằng nhau, chỉ tháng cuối chênh vài đồng."""
	ng = BN.lam_tron_dong(nguyen_gia)
	n = int(so_ky or 0)
	if n <= 0 or ng <= 0:
		return []
	moi = ng // n
	ra = [moi] * n
	ra[-1] = ng - moi * (n - 1)
	return ra


def luy_ke_toi(nguyen_gia, so_ky, ky_bat_dau, ky):
	"""Luỹ kế phải phân bổ tính tới HẾT tháng ky. THUẦN."""
	lich = lich_phan_bo(nguyen_gia, so_ky)
	if not lich or not BN.ky_hop_le(ky_bat_dau) or not BN.ky_hop_le(ky):
		return 0
	i = BN.so_thang_giua(ky_bat_dau, ky)
	if i < 0:
		return 0
	return sum(lich[: i + 1])


def can_phan_bo(khoan, ky, da_phan_bo):
	"""Số cần phân bổ trong tháng ky cho một khoản. THUẦN.

	khoan: dict nguyen_gia, so_ky, ky_bat_dau, trang_thai. Khoản chưa khai, ngừng
	hay chứng từ gốc đã huỷ thì 0. Không bao giờ âm, không vượt phần còn lại."""
	if (khoan.get("trang_thai") or "") in (TT_NGUNG, TT_HUY):
		return 0
	if not int(khoan.get("so_ky") or 0) or not khoan.get("ky_bat_dau"):
		return 0
	ng = BN.lam_tron_dong(khoan.get("nguyen_gia"))
	da = BN.lam_tron_dong(da_phan_bo)
	# Luỹ kế theo lịch không bao giờ vượt nguyên giá (lịch cộng lại đúng nguyên giá),
	# nên phần cần không vượt phần còn lại; chỉ cần chặn âm khi đã phân bổ tay quá lịch.
	return max(0, luy_ke_toi(ng, khoan.get("so_ky"), khoan.get("ky_bat_dau"), ky) - da)


def trang_thai_hien(khoan, da_phan_bo):
	"""Trạng thái hiện trên bảng kê, tính lại mỗi lần đọc. THUẦN."""
	tt = khoan.get("trang_thai") or ""
	if tt in (TT_HUY, TT_NGUNG):
		return tt
	if not int(khoan.get("so_ky") or 0) or not khoan.get("ky_bat_dau"):
		return TT_CHO
	if BN.lam_tron_dong(da_phan_bo) >= BN.lam_tron_dong(khoan.get("nguyen_gia")) > 0:
		return TT_XONG
	return TT_DANG


def tk_uu_tien_theo_khoi(khoi):
	"""Dãy tài khoản chi phí theo khối của bộ phận. THUẦN."""
	return TK_THEO_KHOI.get(khoi or "", TK_MAC_DINH)


def kiem_khai(so_ky, nguyen_gia, da_truoc, ky_bat_dau):
	"""Các câu nhắc khi kế toán khai một khoản. THUẦN. Rỗng là đủ."""
	nhac = []
	try:
		n = int(so_ky)
	except (TypeError, ValueError):
		n = None
	if n is None or n < 1 or n > SO_KY_TOI_DA:
		nhac.append("Số tháng phân bổ phải từ 1 tới %d." % SO_KY_TOI_DA)
	if not BN.ky_hop_le(ky_bat_dau):
		nhac.append("Chưa chọn tháng bắt đầu phân bổ.")
	ng = BN.lam_tron_dong(nguyen_gia)
	dt = BN.lam_tron_dong(da_truoc)
	if dt < 0:
		nhac.append("Đã phân bổ trước không được âm.")
	elif dt > ng:
		nhac.append("Đã phân bổ trước lớn hơn nguyên giá %s đ." % so_vn(ng))
	return nhac


def so_vn(x):
	return "{:,}".format(BN.lam_tron_dong(x)).replace(",", ".")


def dong_but_toan_thang(cac_can, tk_242, ky):
	"""Các dòng bút toán phân bổ tháng ky. THUẦN.

	cac_can: [{khoan, so_tien, tk_chi_phi, bo_phan, dien_giai}] đã lọc số > 0.
	Mỗi khoản HAI dòng mang cùng khoản: Nợ tài khoản chi phí theo bộ phận, Có
	242. Dòng Có mang khoản để số đã phân bổ đọc được từ sổ; dòng Nợ mang khoản
	để tra ngược khi đọc báo cáo chi phí."""
	dong = []
	thang = "%s/%s" % (ky[5:7], ky[:4])
	for c in cac_can:
		tien = BN.lam_tron_dong(c["so_tien"])
		if tien <= 0:
			continue
		nhan = ("Phân bổ %s tháng %s" % ((c.get("dien_giai") or c["khoan"])[:90], thang))
		dong.append({"account": c["tk_chi_phi"], "cost_center": c.get("bo_phan") or "", "debit": tien, "credit": 0,
			"khoan": c["khoan"], "user_remark": nhan})
		dong.append({"account": tk_242, "cost_center": c.get("bo_phan") or "", "debit": 0, "credit": tien,
			"khoan": c["khoan"], "user_remark": nhan})
	return dong


def gom_dem(rows):
	"""Đếm theo trạng thái và theo nguồn cho hàng chip. THUẦN."""
	tt = {"": 0}
	ng = {"": 0}
	for r in rows:
		tt[""] += 1
		tt[r["trang_thai_hien"]] = tt.get(r["trang_thai_hien"], 0) + 1
		ng[""] += 1
		ng[r["nguon_loai"]] = ng.get(r["nguon_loai"], 0) + 1
	return {"trang_thai": tt, "nguon": ng}


def loc_khoang(ngay, khoang, hom_nay):
	"""Ngày ghi nhận có nằm trong khoảng chip không. THUẦN.

	khoang: "thang" (tháng này), "3thang", "nam" (năm nay), "" (tất cả)."""
	if not khoang:
		return True
	s = str(ngay or "")[:10]
	hn = str(hom_nay)[:10]
	if khoang == "thang":
		return s[:7] == hn[:7]
	if khoang == "3thang":
		return s[:7] >= BN.cong_thang(hn[:7], -2)
	if khoang == "nam":
		return s[:4] == hn[:4]
	return True


def vuot_nguyen_gia(nguyen_gia, da_truoc, da_ghi, them):
	"""Phân bổ thêm `them` có vượt nguyên giá không. THUẦN. Trả số vượt (0 là ổn)."""
	con = BN.lam_tron_dong(nguyen_gia) - BN.lam_tron_dong(da_truoc) - BN.lam_tron_dong(da_ghi)
	return max(0, BN.lam_tron_dong(them) - con)


# ------------------------------------------------ phần chạm Frappe

import frappe  # noqa: E402
from frappe.utils import cint, flt, getdate, now_datetime, nowdate  # noqa: E402


def _cty(cty=None):
	if cty:
		return cty
	from vagabond import xuat_kho

	return xuat_kho._cong_ty()


def tk_242(cty):
	"""Các tài khoản lá 242 của công ty (khớp số hiệu chính xác hoặc 242x)."""
	ds = frappe.get_all("Account", filters={"company": cty, "is_group": 0, "disabled": 0},
		fields=["name", "account_number"], limit_page_length=0)
	ra = [a["name"] for a in ds if str(a.get("account_number") or "").startswith(SO_TK)
		or str(a.get("name") or "").startswith(SO_TK + " ")]
	return ra


def tk_242_chinh(cty):
	from vagabond import xuat_kho

	ds = frappe.get_all("Account", filters={"company": cty, "is_group": 0, "disabled": 0},
		fields=["name", "account_number"], limit_page_length=0)
	tk = xuat_kho.chon_tai_khoan(ds, (SO_TK,))
	if not tk:
		frappe.throw("Công ty %s chưa có tài khoản 242 dùng được. Kế toán dựng tài khoản 242 rồi bấm lại." % cty)
	return tk


def tk_chi_phi_goi_y(cty, bo_phan_cc):
	"""Tài khoản chi phí gợi ý theo khối của bộ phận (Cost Center)."""
	from vagabond import bo_phan, xuat_kho

	ten = ""
	if bo_phan_cc:
		ten = frappe.db.get_value("Cost Center", bo_phan_cc, "cost_center_name") or ""
	khoi = bo_phan.nhom_cua(ten) if ten else ""
	ds = frappe.get_all("Account", filters={"company": cty, "is_group": 0, "disabled": 0, "root_type": "Expense"},
		fields=["name", "account_number"], limit_page_length=0)
	return xuat_kho.chon_tai_khoan(ds, tk_uu_tien_theo_khoi(khoi)) or ""


def da_phan_bo_theo_khoan(ten_khoan, den_ngay=None):
	"""{khoản: số đã phân bổ trên sổ} = tổng Có trừ Nợ 242 trên bút toán ĐÃ GHI
	SỔ có gắn khoản. MỘT nguồn cho mọi nơi đọc số đã phân bổ."""
	if not ten_khoan:
		return {}
	dk = ""
	gt = {"k": tuple(ten_khoan)}
	if den_ngay:
		dk = " and je.posting_date <= %(d)s"
		gt["d"] = getdate(den_ngay)
	rows = frappe.db.sql(
		"""select jea.vgb_khoan_242 k,
			sum(jea.credit_in_account_currency) - sum(jea.debit_in_account_currency) t
		from `tabJournal Entry Account` jea
		join `tabJournal Entry` je on je.name = jea.parent
		join `tabAccount` a on a.name = jea.account
		where je.docstatus = 1 and jea.vgb_khoan_242 in %(k)s
			and (a.account_number like '242%%' or a.name like '242 %%')""" + dk + """
		group by jea.vgb_khoan_242""",
		gt,
	)
	return {r[0]: BN.lam_tron_dong(r[1]) for r in rows}


def _co_242_chua_gan(cty):
	"""Dòng Có 242 trên bút toán đã ghi sổ mà chưa gắn khoản (đường tay quên gắn)."""
	tks = tk_242(cty)
	if not tks:
		return []
	return frappe.db.sql(
		"""select jea.name dong, je.name je, je.posting_date ngay, jea.credit_in_account_currency tien,
			coalesce(jea.user_remark, je.user_remark, '') dien_giai
		from `tabJournal Entry Account` jea join `tabJournal Entry` je on je.name = jea.parent
		where je.docstatus = 1 and je.company = %(c)s and jea.account in %(t)s
			and jea.credit_in_account_currency > 0 and coalesce(jea.vgb_khoan_242, '') = ''
		order by je.posting_date""",
		{"c": cty, "t": tuple(tks)}, as_dict=True)


def _dong_tu_so_cai(cty):
	"""Mỗi chứng từ ghi Nợ 242: tổng Nợ trừ Có 242 (đang hiệu lực) và tổng đã huỷ."""
	tks = tk_242(cty)
	if not tks:
		return []
	return frappe.db.sql(
		"""select voucher_type, voucher_no, min(posting_date) ngay,
			sum(case when is_cancelled = 0 then debit - credit else 0 end) con,
			sum(case when is_cancelled = 1 then debit else 0 end) huy,
			max(case when is_cancelled = 0 then cost_center else null end) bo_phan
		from `tabGL Entry`
		where company = %(c)s and account in %(t)s
		group by voucher_type, voucher_no
		having sum(debit) > 0""",
		{"c": cty, "t": tuple(tks)}, as_dict=True)


def _dien_giai(vt, vn):
	try:
		if vt == "Purchase Invoice":
			r = frappe.db.get_value(vt, vn, ["supplier_name", "bill_no"], as_dict=True) or {}
			mon = frappe.db.get_value("Purchase Invoice Item", {"parent": vn}, "item_name") or ""
			return ("%s%s%s" % (mon, " - " if mon and r.get("supplier_name") else "", r.get("supplier_name") or ""))[:140]
		if vt == "Stock Entry":
			mon = frappe.get_all("Stock Entry Detail", filters={"parent": vn}, fields=["item_name"], limit_page_length=3)
			n = frappe.db.count("Stock Entry Detail", {"parent": vn})
			ten = ", ".join(m.item_name for m in mon)
			return (ten + (" và %d món nữa" % (n - len(mon)) if n > len(mon) else ""))[:140]
		if vt == "Journal Entry":
			return (frappe.db.get_value(vt, vn, "user_remark") or vn)[:140]
	except Exception:
		pass
	return vn


def quet(cty=None):
	"""Dựng hoặc cập nhật dòng bảng kê từ sổ cái 242. Chạy lại không đổi gì.

	Chỉ đọc chứng từ; bản ghi bảng kê là dữ liệu riêng của bảng kê."""
	cty = _cty(cty)
	moi = 0
	for r in _dong_tu_so_cai(cty):
		khoa = "%s:%s" % (r.voucher_type, r.voucher_no)
		ten = frappe.db.get_value(DT, {"khoa": khoa}, "name")
		con = BN.lam_tron_dong(r.con)
		if ten:
			cu = frappe.db.get_value(DT, ten, ["trang_thai", "nguyen_gia"], as_dict=True)
			if con <= 0 and cu.trang_thai != TT_HUY:
				frappe.db.set_value(DT, ten, "trang_thai", TT_HUY, update_modified=False)
			elif con > 0 and cu.trang_thai == TT_HUY:
				frappe.db.set_value(DT, ten, "trang_thai", "", update_modified=False)
			if con > 0 and BN.lam_tron_dong(cu.nguyen_gia) != con:
				frappe.db.set_value(DT, ten, "nguyen_gia", con, update_modified=False)
			continue
		if con <= 0:
			continue
		d = frappe.new_doc(DT)
		d.khoa = khoa
		d.company = cty
		d.nguon_loai = NGUON_THEO_LOAI.get(r.voucher_type, NGUON_KHAC)
		d.nguon_doctype = r.voucher_type
		d.nguon_so = r.voucher_no
		d.ngay = r.ngay
		d.nguyen_gia = con
		d.dien_giai = _dien_giai(r.voucher_type, r.voucher_no)
		d.bo_phan = r.bo_phan or None
		if r.voucher_type == "Stock Entry" and frappe.db.has_column("Stock Entry", "vgb_so_ky_phan_bo"):
			se = frappe.db.get_value("Stock Entry", r.voucher_no, ["vgb_so_ky_phan_bo", "posting_date"], as_dict=True) or {}
			if cint(se.get("vgb_so_ky_phan_bo")) > 0:
				d.so_ky = cint(se.get("vgb_so_ky_phan_bo"))
				d.ky_bat_dau = BN.ky_cua(se.get("posting_date") or r.ngay)
		d.tk_chi_phi = tk_chi_phi_goi_y(cty, d.bo_phan) or None
		d.flags.ignore_permissions = True
		d.flags.vgb_bang_ke = True
		d.insert(ignore_permissions=True)
		moi += 1
	return {"moi": moi}


def quet_tu_dong():
	"""Nhịp hằng ngày: mọi công ty có tài khoản 242."""
	for c in frappe.get_all("Company", pluck="name", limit_page_length=0):
		try:
			if tk_242(c):
				quet(c)
				frappe.db.commit()
		except Exception:
			frappe.db.rollback()
			frappe.log_error(frappe.get_traceback(), "Quét bảng kê 242 lỗi")


def khi_ghi_so_xuat(se_name):
	"""Phiếu xuất CCDC phân bổ nhiều tháng vừa ghi sổ: dựng ngay dòng bảng kê,
	không chờ nhịp quét đêm. Cùng một đường quet() nên không có bản thứ hai."""
	cty = frappe.db.get_value("Stock Entry", se_name, "company")
	quet(cty)


def _rows(cty):
	ds = frappe.get_all(DT, filters={"company": cty},
		fields=["name", "khoa", "nguon_loai", "nguon_doctype", "nguon_so", "ngay", "dien_giai", "nguyen_gia",
			"so_ky", "ky_bat_dau", "bo_phan", "tk_chi_phi", "da_phan_bo_truoc", "trang_thai", "ghi_chu"],
		order_by="ngay desc, name desc", limit_page_length=0)
	da = da_phan_bo_theo_khoan([d.name for d in ds])
	anh = _anh_dau(ds)
	for d in ds:
		d["anh"] = anh.get(d.name, "")
		d["da_tren_so"] = da.get(d.name, 0)
		d["da_phan_bo"] = d["da_tren_so"] + BN.lam_tron_dong(d.da_phan_bo_truoc)
		d["con_lai"] = max(0, BN.lam_tron_dong(d.nguyen_gia) - d["da_phan_bo"])
		d["trang_thai_hien"] = trang_thai_hien(d, d["da_phan_bo"])
	return ds


def _anh_dau(ds):
	"""Ảnh món đầu tiên của chứng từ gốc (phiếu xuất CCDC, hoá đơn mua) cho dòng bảng kê."""
	from vagabond import xuat_kho

	mon = {}
	for dt, con in (("Stock Entry", "Stock Entry Detail"), ("Purchase Invoice", "Purchase Invoice Item")):
		so = [d.nguon_so for d in ds if d.nguon_doctype == dt and d.nguon_so]
		if not so:
			continue
		for r in frappe.get_all(con, filters={"parent": ["in", so]}, fields=["parent", "item_code", "idx"],
				order_by="idx asc", limit_page_length=0):
			mon.setdefault((dt, r.parent), r.item_code)
	anh = xuat_kho.anh_theo_ma([m for m in mon.values() if m])
	return {d.name: anh.get(mon.get((d.nguon_doctype, d.nguon_so)) or "", "") for d in ds}


@frappe.whitelist()
def danh_muc():
	"""Danh mục cho ô chọn có tìm: bộ phận (lá) và tài khoản chi phí (lá) của công ty."""
	BN.kiem_quyen(BN.QUYEN_XEM, "xem bảng kê chi phí trả trước")
	cty = _cty()
	cc = frappe.get_all("Cost Center", filters={"company": cty, "is_group": 0, "disabled": 0},
		fields=["name", "cost_center_name", "parent_cost_center"], order_by="lft asc", limit_page_length=0)
	tk = frappe.get_all("Account", filters={"company": cty, "is_group": 0, "disabled": 0, "root_type": "Expense"},
		fields=["name", "account_number", "account_name"], order_by="account_number asc", limit_page_length=0)
	duoi = " - " + (frappe.db.get_value("Company", cty, "abbr") or "")
	return {
		"bo_phan": [{"value": c.name, "label": c.cost_center_name, "phu": (c.parent_cost_center or "").rsplit(" - ", 1)[0]} for c in cc],
		"tai_khoan": [{"value": a.name, "label": a.name[: -len(duoi)] if a.name.endswith(duoi) else a.name,
			"phu": "Tài khoản chi phí"} for a in tk],
	}


@frappe.whitelist()
def danh_sach(trang_thai=None, nguon=None, khoang=None, tu_khoa=None):
	"""Bảng kê 242 cho màn app. Đếm chip tính trên toàn bộ khoản trong khoảng ngày
	đang chọn (chip trạng thái và chip nguồn cùng một tập), danh sách lọc thêm."""
	BN.kiem_quyen(BN.QUYEN_XEM, "xem bảng kê chi phí trả trước")
	cty = _cty()
	quet(cty)
	tat_ca = _rows(cty)
	hn = nowdate()
	trong_khoang = [r for r in tat_ca if loc_khoang(r.ngay, khoang or "", hn)]
	dem = gom_dem(trong_khoang)
	tk = (tu_khoa or "").strip().lower()
	ra = [r for r in trong_khoang
		if (not trang_thai or r["trang_thai_hien"] == trang_thai)
		and (not nguon or r.nguon_loai == nguon)
		and (not tk or tk in " ".join(str(r.get(k) or "") for k in ("dien_giai", "nguon_so", "name", "bo_phan")).lower())]
	tong = {
		"nguyen_gia": sum(BN.lam_tron_dong(r.nguyen_gia) for r in ra),
		"da_phan_bo": sum(r["da_phan_bo"] for r in ra),
		"con_lai": sum(r["con_lai"] for r in ra),
	}
	chua_gan = _co_242_chua_gan(cty)
	return {
		"rows": ra,
		"dem": dem,
		"tong": tong,
		"co_chua_gan": [dict(x, tien=BN.lam_tron_dong(x["tien"])) for x in chua_gan],
		"duoc_lap": 1 if BN.co_quyen(BN.QUYEN_LAP) else 0,
		"duoc_ghi": 1 if BN.co_quyen(BN.QUYEN_GHI) else 0,
		"hom_nay": hn,
	}


@frappe.whitelist()
def chi_tiet(ten):
	BN.kiem_quyen(BN.QUYEN_XEM, "xem bảng kê chi phí trả trước")
	d = frappe.get_doc(DT, ten)
	da = da_phan_bo_theo_khoan([d.name]).get(d.name, 0)
	da_tong = da + BN.lam_tron_dong(d.da_phan_bo_truoc)
	lich = lich_phan_bo(d.nguyen_gia, d.so_ky) if d.so_ky else []
	cac_thang = []
	if lich and d.ky_bat_dau:
		for i, t in enumerate(lich):
			ky = BN.cong_thang(d.ky_bat_dau, i)
			cac_thang.append({"ky": ky, "so_tien": t})
	lan = frappe.db.sql(
		"""select je.name, je.posting_date, je.docstatus, coalesce(je.vgb_huy, 0) huy, coalesce(je.vgb_tu_lap, '') tu_lap,
			sum(jea.credit_in_account_currency) - sum(jea.debit_in_account_currency) tien
		from `tabJournal Entry Account` jea join `tabJournal Entry` je on je.name = jea.parent
		join `tabAccount` a on a.name = jea.account
		where jea.vgb_khoan_242 = %s and je.docstatus < 2
			and (a.account_number like '242%%' or a.name like '242 %%')
		group by je.name order by je.posting_date""", d.name, as_dict=True)
	mon = []
	if d.nguon_doctype == "Stock Entry":
		from vagabond import xuat_kho

		it = frappe.get_all("Stock Entry Detail", filters={"parent": d.nguon_so},
			fields=["item_code", "item_name", "qty", "uom", "amount"], limit_page_length=0)
		anh = xuat_kho.anh_theo_ma([x.item_code for x in it])
		mon = [{"ma": x.item_code, "ten": x.item_name, "sl": flt(x.qty), "dvt": x.uom, "tien": flt(x.amount),
			"anh": anh.get(x.item_code, "")} for x in it]
	return {
		"name": d.name, "khoa": d.khoa, "nguon_loai": d.nguon_loai, "nguon_doctype": d.nguon_doctype,
		"nguon_so": d.nguon_so, "ngay": str(d.ngay or ""), "dien_giai": d.dien_giai, "nguyen_gia": BN.lam_tron_dong(d.nguyen_gia),
		"so_ky": cint(d.so_ky), "ky_bat_dau": d.ky_bat_dau or "", "bo_phan": d.bo_phan or "", "tk_chi_phi": d.tk_chi_phi or "",
		"da_phan_bo_truoc": BN.lam_tron_dong(d.da_phan_bo_truoc), "da_tren_so": da, "da_phan_bo": da_tong,
		"con_lai": max(0, BN.lam_tron_dong(d.nguyen_gia) - da_tong), "trang_thai": d.trang_thai or "",
		"trang_thai_hien": trang_thai_hien(d.as_dict(), da_tong), "ghi_chu": d.ghi_chu or "",
		"khai_boi": frappe.db.get_value("User", d.khai_boi, "full_name") if d.khai_boi else "",
		"khai_luc": str(d.khai_luc or ""), "lich": cac_thang,
		"lan_phan_bo": [{"je": x.name, "ngay": str(x.posting_date), "docstatus": cint(x.docstatus), "huy": cint(x.huy),
			"may_lap": 1 if x.tu_lap else 0, "tien": BN.lam_tron_dong(x.tien)} for x in lan],
		"mon": mon, "chon_so_ky": list(CHON_SO_KY), "so_ky_toi_da": SO_KY_TOI_DA,
		"duoc_lap": 1 if BN.co_quyen(BN.QUYEN_LAP) else 0, "duoc_ghi": 1 if BN.co_quyen(BN.QUYEN_GHI) else 0,
	}


def _kiem_cost_center(cty, cc):
	if not cc:
		frappe.throw("Chưa chọn bộ phận chịu chi phí.")
	r = frappe.db.get_value("Cost Center", cc, ["company", "is_group", "disabled"], as_dict=True)
	if not r or r.company != cty or cint(r.is_group) or cint(r.disabled):
		frappe.throw("Bộ phận %s không dùng được cho công ty này. Chọn lại trong danh sách bộ phận." % cc)


def _kiem_tk_chi_phi(cty, tk):
	if not tk:
		frappe.throw("Chưa chọn tài khoản chi phí.")
	r = frappe.db.get_value("Account", tk, ["company", "is_group", "disabled", "root_type"], as_dict=True)
	if not r or r.company != cty or cint(r.is_group) or cint(r.disabled):
		frappe.throw("Tài khoản %s không dùng được: phải là tài khoản chi tiết của công ty này." % tk)
	if r.root_type != "Expense":
		frappe.throw("Tài khoản %s không phải tài khoản chi phí. Phân bổ 242 chỉ vào tài khoản chi phí (6xx)." % tk)


@frappe.whitelist(methods=["POST"])
def khai(ten, so_ky=None, ky_bat_dau=None, bo_phan=None, tk_chi_phi=None, da_phan_bo_truoc=None, ghi_chu=None):
	"""Kế toán khai cách phân bổ một khoản. Máy chủ kiểm mã danh mục ở đây cho
	mọi đường gọi (H8 loại 12): bộ phận và tài khoản phải có thật, đúng công ty."""
	BN.kiem_quyen(BN.QUYEN_LAP, "khai khoản chi phí trả trước")
	frappe.db.sql("select name from `tabVagabond Khoan 242` where name=%s for update", ten)
	d = frappe.get_doc(DT, ten)
	if d.trang_thai == TT_HUY:
		frappe.throw("Chứng từ gốc của khoản này đã huỷ nên không khai được nữa.")
	# Giá trị 0 hợp lệ ở ô Đã phân bổ trước: đọc bằng is None (H8 loại 14).
	dt = BN.lam_tron_dong(d.da_phan_bo_truoc) if da_phan_bo_truoc in (None, "") else BN.lam_tron_dong(flt(da_phan_bo_truoc))
	nhac = kiem_khai(so_ky, d.nguyen_gia, dt, ky_bat_dau)
	if nhac:
		frappe.throw(" ".join(nhac))
	_kiem_cost_center(d.company, bo_phan)
	_kiem_tk_chi_phi(d.company, tk_chi_phi)
	da = da_phan_bo_theo_khoan([d.name]).get(d.name, 0)
	if dt + da > BN.lam_tron_dong(d.nguyen_gia):
		frappe.throw("Đã phân bổ trước %s đ cộng số đã phân bổ trên sổ %s đ vượt nguyên giá %s đ."
			% (so_vn(dt), so_vn(da), so_vn(d.nguyen_gia)))
	d.so_ky = int(so_ky)
	d.ky_bat_dau = str(ky_bat_dau)
	d.bo_phan = bo_phan
	d.tk_chi_phi = tk_chi_phi
	d.da_phan_bo_truoc = dt
	if ghi_chu is not None:
		d.ghi_chu = (ghi_chu or "").strip()[:500]
	if d.trang_thai == TT_NGUNG:
		d.trang_thai = ""
	d.khai_boi = frappe.session.user
	d.khai_luc = now_datetime()
	d.flags.ignore_permissions = True
	d.flags.vgb_bang_ke = True
	d.save(ignore_permissions=True)
	return {"ok": 1}


@frappe.whitelist(methods=["POST"])
def ngung(ten, ly_do=None):
	"""Khoản này không phân bổ qua bảng kê (ví dụ tiền thuê kế toán tự xử lý)."""
	BN.kiem_quyen(BN.QUYEN_LAP, "đổi trạng thái khoản chi phí trả trước")
	if not (ly_do or "").strip():
		frappe.throw("Ghi lý do không phân bổ để người sau còn hiểu.")
	d = frappe.get_doc(DT, ten)
	if d.trang_thai == TT_HUY:
		frappe.throw("Chứng từ gốc của khoản này đã huỷ.")
	d.trang_thai = TT_NGUNG
	d.ghi_chu = ("Không phân bổ: %s" % ly_do.strip())[:500]
	d.khai_boi = frappe.session.user
	d.khai_luc = now_datetime()
	d.flags.ignore_permissions = True
	d.flags.vgb_bang_ke = True
	d.save(ignore_permissions=True)
	return {"ok": 1}


def _can_thang(cty, ky):
	"""Danh sách khoản cần phân bổ tháng ky (đọc sau khoá ở nơi gọi)."""
	rows = _rows(cty)
	can = []
	cho = []
	for r in rows:
		if r["trang_thai_hien"] == TT_CHO:
			cho.append(r)
			continue
		if r.ngay and BN.ky_cua(r.ngay) > ky:
			continue
		tien = can_phan_bo(r, ky, r["da_phan_bo"])
		if tien > 0:
			if not r.tk_chi_phi or not r.bo_phan:
				cho.append(r)
				continue
			can.append({"khoan": r.name, "so_tien": tien, "tk_chi_phi": r.tk_chi_phi, "bo_phan": r.bo_phan,
				"dien_giai": r.dien_giai, "nguon_so": r.nguon_so})
	return can, cho


@frappe.whitelist()
def xem_thang(ky):
	"""Xem trước bút toán phân bổ tháng ky và tình trạng bản nháp."""
	BN.kiem_quyen(BN.QUYEN_XEM, "xem phân bổ chi phí trả trước")
	if not BN.ky_hop_le(ky):
		frappe.throw("Tháng không hợp lệ.")
	cty = _cty()
	quet(cty)
	bg = BN.doc_ban_ghi(BN.LOAI_242, cty, ky)
	tt, info = BN.tinh_trang(bg)
	can, cho = _can_thang(cty, ky)
	chua_gan = _co_242_chua_gan(cty)
	return {
		"ky": ky, "trang_thai": tt, "journal_entry": bg.journal_entry if bg else "",
		"dong": can, "tong": sum(c["so_tien"] for c in can),
		"cho_khai": [{"name": r.name, "dien_giai": r.dien_giai, "nguyen_gia": BN.lam_tron_dong(r.nguyen_gia)} for r in cho],
		"co_chua_gan": [dict(x, tien=BN.lam_tron_dong(x["tien"])) for x in chua_gan],
		"tuong_lai": 1 if BN.la_thang_tuong_lai(ky) else 0,
		"duoc_lap": 1 if BN.co_quyen(BN.QUYEN_LAP) else 0, "duoc_ghi": 1 if BN.co_quyen(BN.QUYEN_GHI) else 0,
	}


@frappe.whitelist(methods=["POST"])
def lap_thang(ky):
	"""Lập hoặc cập nhật bút toán nháp phân bổ tháng ky. Không ghi sổ."""
	BN.kiem_quyen(BN.QUYEN_LAP, "lập bút toán phân bổ")
	if not BN.ky_hop_le(ky):
		frappe.throw("Tháng không hợp lệ.")
	if BN.la_thang_tuong_lai(ky):
		frappe.throw("Chưa tới tháng %s/%s nên chưa phân bổ được." % (ky[5:7], ky[:4]))
	cty = _cty()
	quet(cty)
	# Khoá bản ghi TRƯỚC khi đọc số đã phân bổ (H8 loại 1): hai người bấm cùng
	# lúc thì người sau đọc số sau khi người trước đã xong.
	BN.khoa_ban_ghi(BN.LOAI_242, cty, ky)
	chua_gan = _co_242_chua_gan(cty)
	if chua_gan:
		frappe.throw(
			"Có %d dòng Có 242 trên bút toán đã ghi sổ chưa gắn khoản (ví dụ %s). Hệ thống không biết khoản nào "
			"đã được phân bổ nên chưa lập bút toán tháng. Gắn khoản cho các dòng đó ở Bảng kê 242 rồi bấm lại."
			% (len(chua_gan), chua_gan[0]["je"])
		)
	can, cho = _can_thang(cty, ky)
	if not can:
		frappe.throw("Tháng %s/%s không còn khoản nào cần phân bổ.%s" % (
			ky[5:7], ky[:4], (" Còn %d khoản chờ khai số tháng." % len(cho)) if cho else ""))
	dong = dong_but_toan_thang(can, tk_242_chinh(cty), ky)
	kq = BN.lap_hoac_cap_nhat(BN.LOAI_242, cty, ky, dong,
		"Phân bổ chi phí trả trước tháng %s/%s (hệ thống lập, kế toán ghi sổ)" % (ky[5:7], ky[:4]),
		ban_ke={"khoan": can})
	kq["tong"] = sum(c["so_tien"] for c in can)
	kq["so_khoan"] = len(can)
	return kq


@frappe.whitelist(methods=["POST"])
def ghi_so_thang(ky):
	cty = _cty()
	return BN.ghi_so(BN.LOAI_242, cty, ky)


@frappe.whitelist(methods=["POST"])
def bo_nhap_thang(ky, ly_do=None):
	BN.kiem_quyen(BN.QUYEN_LAP, "bỏ bút toán nháp")
	return BN.bo_nhap(BN.LOAI_242, _cty(), ky, ly_do)


@frappe.whitelist(methods=["POST"])
def phan_bo_tay(ten, ky, so_tien, tk_chi_phi=None, bo_phan=None, ghi_so=0):
	"""Đường thủ công: kế toán phân bổ một khoản với số tự chọn. Lập bút toán
	riêng (không đụng bút toán tháng của máy); ghi sổ ngay nếu có quyền và chọn."""
	BN.kiem_quyen(BN.QUYEN_LAP, "phân bổ tay khoản chi phí trả trước")
	if not BN.ky_hop_le(ky):
		frappe.throw("Tháng không hợp lệ.")
	frappe.db.sql("select name from `tabVagabond Khoan 242` where name=%s for update", ten)
	d = frappe.get_doc(DT, ten)
	if d.trang_thai == TT_HUY:
		frappe.throw("Chứng từ gốc của khoản này đã huỷ.")
	tien = BN.lam_tron_dong(flt(so_tien))
	if tien <= 0:
		frappe.throw("Số tiền phân bổ phải lớn hơn 0.")
	tk = tk_chi_phi or d.tk_chi_phi
	cc = bo_phan or d.bo_phan
	_kiem_cost_center(d.company, cc)
	_kiem_tk_chi_phi(d.company, tk)
	da = da_phan_bo_theo_khoan([d.name]).get(d.name, 0)
	vuot = vuot_nguyen_gia(d.nguyen_gia, d.da_phan_bo_truoc, da, tien)
	if vuot:
		frappe.throw("Phân bổ %s đ vượt phần còn lại của khoản %s đ." % (so_vn(tien), so_vn(tien - vuot)))
	ngay = BN.ngay_cuoi_thang(ky)
	BN.chan_khoa_so(ngay)
	tk2 = tk_242_chinh(d.company)
	je = frappe.new_doc("Journal Entry")
	je.voucher_type = "Journal Entry"
	je.company = d.company
	je.posting_date = ngay
	je.user_remark = "Phân bổ tay %s tháng %s/%s" % ((d.dien_giai or d.name)[:90], ky[5:7], ky[:4])
	for a, no, co in ((tk, tien, 0), (tk2, 0, tien)):
		je.append("accounts", {"account": a, "cost_center": cc, "debit_in_account_currency": no,
			"credit_in_account_currency": co, "vgb_khoan_242": d.name})
	je.flags.ignore_permissions = True
	je.insert(ignore_permissions=True)
	if cint(ghi_so):
		BN.kiem_quyen(BN.QUYEN_GHI, "ghi sổ bút toán")
		je.submit()
	return {"ok": 1, "journal_entry": je.name, "da_ghi_so": 1 if cint(ghi_so) else 0}


@frappe.whitelist(methods=["POST"])
def gan_khoan(dong, ten):
	"""Gắn khoản cho một dòng Có 242 đã ghi sổ mà chưa gắn (đường tay quên gắn).
	Ô vgb_khoan_242 cho sửa sau ghi sổ; hook before_update_after_submit kiểm vượt."""
	BN.kiem_quyen(BN.QUYEN_LAP, "gắn khoản chi phí trả trước")
	# Khoá dòng trước khi đọc (H8 loại 1): hai người cùng gắn một dòng thì người sau thấy đã gắn.
	frappe.db.sql("select name from `tabJournal Entry Account` where name=%s for update", dong)
	r = frappe.db.get_value("Journal Entry Account", dong, ["parent", "account", "credit_in_account_currency", "vgb_khoan_242"], as_dict=True)
	if not r:
		frappe.throw("Không thấy dòng bút toán này.")
	if r.vgb_khoan_242:
		frappe.throw("Dòng này đã gắn khoản %s." % r.vgb_khoan_242)
	je = frappe.get_doc("Journal Entry", r.parent)
	if je.docstatus != 1:
		frappe.throw("Chỉ gắn cho bút toán đã ghi sổ; bút toán nháp thì sửa ngay trên bút toán.")
	k = frappe.db.get_value(DT, ten, ["company"], as_dict=True)
	if not k or k.company != je.company:
		frappe.throw("Khoản %s không thuộc công ty của bút toán." % ten)
	for x in je.accounts:
		if x.name == dong:
			x.vgb_khoan_242 = ten
	je.flags.ignore_permissions = True
	je.save(ignore_permissions=True)
	return {"ok": 1}


def kiem_je(doc, method=None):
	"""Hook Journal Entry (before_submit, before_update_after_submit): dòng có gắn
	khoản 242 thì không cho phân bổ vượt nguyên giá. Áp cho mọi đường: app, Desk,
	Hạch toán tay. Bút toán không gắn khoản nào thì không làm gì."""
	gan = [x for x in (doc.get("accounts") or []) if x.get("vgb_khoan_242")]
	if not gan:
		return
	tks = set(tk_242(doc.company))
	them = {}
	for x in gan:
		k = x.vgb_khoan_242
		r = frappe.db.get_value(DT, k, ["company", "trang_thai"], as_dict=True)
		if not r or r.company != doc.company:
			frappe.throw("Dòng %s gắn khoản %s không có hoặc khác công ty." % (x.idx, k))
		if x.account in tks:
			if r.trang_thai == TT_HUY:
				frappe.throw("Khoản %s có chứng từ gốc đã huỷ, không phân bổ tiếp được." % k)
			them[k] = them.get(k, 0) + BN.lam_tron_dong(x.credit_in_account_currency) - BN.lam_tron_dong(x.debit_in_account_currency)
	if not them:
		return
	# Khoá từng khoản rồi mới đọc số đã ghi (H8 loại 1).
	for k in sorted(them):
		frappe.db.sql("select name from `tabVagabond Khoan 242` where name=%s for update", k)
	da = da_phan_bo_theo_khoan(list(them))
	# Bút toán đang sửa sau ghi sổ đã nằm trong số đọc từ sổ: trừ phần cũ của chính nó.
	cu = {}
	if method == "before_update_after_submit":
		for r in frappe.db.sql(
			"""select vgb_khoan_242, sum(credit_in_account_currency) - sum(debit_in_account_currency)
			from `tabJournal Entry Account` where parent=%s and coalesce(vgb_khoan_242,'') != ''
				and account in %s group by vgb_khoan_242""", (doc.name, tuple(tks) or ("",))):
			cu[r[0]] = BN.lam_tron_dong(r[1])
	for k, t in them.items():
		r = frappe.db.get_value(DT, k, ["nguyen_gia", "da_phan_bo_truoc"], as_dict=True)
		vuot = vuot_nguyen_gia(r.nguyen_gia, r.da_phan_bo_truoc, da.get(k, 0) - cu.get(k, 0), t)
		if vuot:
			frappe.throw(
				"Khoản %s chỉ còn %s đ chưa phân bổ, bút toán này phân bổ %s đ (vượt %s đ). Sửa số tiền hoặc "
				"mở Bảng kê 242 xem các lần đã phân bổ." % (k, so_vn(t - vuot), so_vn(t), so_vn(vuot)))


TRUONG_MOI = {
	"Stock Entry": [
		{
			"fieldname": "vgb_so_ky_phan_bo",
			"label": "Số tháng phân bổ (CCDC)",
			"fieldtype": "Int",
			"read_only": 1,
			"insert_after": "vgb_muc_dich_xuat",
			"description": "Phiếu đưa công cụ dụng cụ vào dùng, phân bổ nhiều tháng: hàng xuất ghi Nợ 242, "
				"Bảng kê 242 dựng khoản và phân bổ hằng tháng. Để trống là phân bổ một lần.",
		}
	],
}
