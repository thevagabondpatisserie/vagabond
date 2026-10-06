# -*- coding: utf-8 -*-
"""#420 v579: cửa máy chủ của đối soát vendor (tải tay, email, xem, đối chiếu).

Anh Việt 06/10/2026: "Sửa triệt để, cầm đầu codex nhé" và chốt qua câu hỏi:
làm trọn một lần (đủ mười nguồn, nối từng hoá đơn, email tự nhận); kế toán
bấm nhận thì CHỈ LƯU VÀ ĐỐI CHIẾU, không lập phiếu, không bút toán phí.

Luồng một tệp (tải tay hay đính kèm email đều đi đúng một đường _nhan_byte):
  byte -> doi_soat_doc (bảng ô) -> doi_soat_mau (dòng chuẩn) ->
  doi_soat_khop.xem_truoc (mới / đã có / lỗi) -> ghi Vagabond Doi Soat Nguon
  + các Vagabond Doi Soat Dong mới -> nối hoá đơn / vận đơn / hoá đơn mua ->
  dò tiền về ngân hàng.

Chống trùng ở tầng cơ sở dữ liệu, không chỉ ở bước xem trước:
- sha256 của tệp là duy nhất trên Doi Soat Nguon: cùng tệp tải hai lần (hay
  tải tay rồi email lại gửi) chỉ có một nguồn.
- khoá sự kiện là duy nhất trên Doi Soat Dong: báo cáo ngày và báo cáo tháng
  cùng chứa một giao dịch thì lần nhận sau thành "đã có".
Không có gì ở đây tạo Payment Entry, Journal Entry hay gạch Bank Transaction.
"""

import base64
import json

import frappe

from vagabond import doi_soat_doc as tep_doc
from vagabond import doi_soat_khop as khop
from vagabond import doi_soat_mau as mau_bc

DT_NGUON = "Vagabond Doi Soat Nguon"
DT_DONG = "Vagabond Doi Soat Dong"
DUOI = (".csv", ".txt", ".xlsx", ".xlsm", ".xls", ".pdf", ".zip")

# Tên miền người gửi báo cáo, theo sheet Doi_Soat_Tong_Hop của tiệm.
TEN_MIEN_VENDOR = ("greensm.com", "xanhsm.com", "grab.com", "grabtaxi.com", "onepay.vn", "payoo.com.vn",
	"shopeefood.vn", "shopee.vn", "shinhan.com.vn", "be.com.vn")

# Mode of Payment / nguồn đơn trên hoá đơn bán ứng với từng kiểu nối.
PT_THEO_KIEU = {
	"payoo": ("Thẻ - Payoo",), "shinhan": ("Thẻ - ShinhanBank",), "onepay": ("OnePay",),
	# Báo cáo GrabFood gồm cả đơn Grab Dine-Out (mã GD-). Bill Dine-Out ghi ở
	# quầy với phương thức Grab Dine-Out, không mang nguồn GrabFood.
	"grab": ("Grab Dine-Out",),
}
# Tiền tố mã của từng nhóm ứng viên, để lượt nối theo tiền không ghép đơn
# Dine-Out (GD-) với bill giao hàng (GF-) chỉ vì trùng số tiền.
TIEN_TO_THEO_KIEU = {"grab": {"nguon": "GF-", "pt": "GD-"}}
NGUON_THEO_KIEU = {
	"grab": ("GrabFood", "Grab", "Grab Online"), "shopee": ("ShopeeFood",),
	"greensm": ("GreenSM Food", "GreenSM"),
}


# ------------------------------------------------------------ phần thuần

def la_thu_vendor(nguoi_gui):
	"""Thư từ tên miền vendor đã khai. THUẦN."""
	s = (nguoi_gui or "").strip().lower()
	if "<" in s and ">" in s:
		s = s[s.index("<") + 1:s.index(">")]
	mien = s.rsplit("@", 1)[-1] if "@" in s else ""
	return any(mien == m or mien.endswith("." + m) for m in TEN_MIEN_VENDOR)


def tom_tat(kq, xt):
	"""Bản tóm tắt gửi về màn hình (không kèm dữ liệu cá nhân). THUẦN."""
	moi = [x["dong"] for x in xt["dong"] if x["trang_thai"] == "moi"]
	return dict(
		mau=kq["mau"], ten_mau=mau_bc.TEN_MAU.get(kq["mau"], kq["mau"] or "Chưa nhận ra"),
		vendor=kq["vendor"], nhom=khop.NHOM_TEN.get(kq["nhom"], ""), tu_ngay=kq["tu_ngay"],
		den_ngay=kq["den_ngay"], ngay_tien_ve=kq["ngay_tien_ve"], trang_thai=xt["trang_thai"],
		so=xt["so"], tong=xt["tong"], tong_tep=kq.get("tong") or {}, loi=xt["loi"][:20],
		canh_bao=xt["canh_bao"][:10], ghi_chu_don_vi=kq.get("ghi_chu_don_vi") or "",
		dong_loi=[dict(vi_tri=x["vi_tri"], ly_do=x.get("ly_do", "")) for x in xt["dong"] if x["trang_thai"] == "loi"][:50],
		mau_dong=[dict(ngay=d["ngay"], loai=d["loai"], ma=d["ma_don"] or d["ma_su_kien"][:30],
			tien=d["tien_hang"], phi=d["phi"], nhan=d["thuc_nhan"], mo_ta=d["mo_ta"]) for d in moi[:30]])


def _so_vn(n):
	return "{:,}".format(int(n or 0)).replace(",", ".")


# ------------------------------------------------------------ quyền

def _chan(ghi=False):
	"""Đọc: kế toán và giám đốc. Nhận tệp: kế toán và giám đốc. Máy chủ chặn
	thật; ô trên app chỉ ẩn cho gọn."""
	from vagabond.viec_can_lam import VAI_GIAM_DOC, VAI_KE_TOAN

	if not (set(frappe.get_roles()) & (VAI_KE_TOAN | VAI_GIAM_DOC)):
		frappe.throw("Đối soát nhà cung cấp chỉ mở cho Kế toán và Giám đốc. Cần dùng thì báo anh Việt cấp chức vụ.",
			frappe.PermissionError)


def _cong_ty():
	return frappe.defaults.get_global_default("company") or frappe.get_all("Company", pluck="name", limit=1)[0]


# ------------------------------------------------------------ tải tay

@frappe.whitelist()
def tai_len(ten=None, noi_dung=None):
	"""Cất tệp riêng tư, trả đường dẫn để xem trước rồi nhận."""
	_chan(True)
	ten = (ten or "").strip() or "doi-soat"
	if not ten.lower().endswith(DUOI):
		frappe.throw("Chỉ nhận tệp CSV, Excel (.xlsx, .xls), PDF hoặc .zip. Tải đúng tệp gốc vendor gửi qua email.")
	noi = (noi_dung or "").strip()
	if "," in noi and noi[:5].lower() == "data:":
		noi = noi.split(",", 1)[1]
	try:
		byte = base64.b64decode(noi)
	except Exception:
		frappe.throw("Tệp gửi lên hỏng giữa đường. Chọn lại tệp rồi thử lại.")
	if not byte:
		frappe.throw("Tệp rỗng. Kiểm lại tệp vendor gửi.")
	if len(byte) > tep_doc.TOI_DA_BYTE:
		frappe.throw("Tệp quá 20 MB. Chia theo kỳ rồi tải từng tệp.")
	f = frappe.get_doc({"doctype": "File", "file_name": ten, "content": noi, "decode": True, "is_private": 1})
	f.flags.ignore_permissions = True
	f.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"file_url": f.file_url, "ten": ten}


def _doc_file(file_url):
	ten = frappe.db.get_value("File", {"file_url": file_url}, "name")
	if not ten:
		frappe.throw("Không thấy tệp vừa tải. Tải lại tệp rồi thử lại.")
	f = frappe.get_doc("File", ten)
	noi = f.get_content()
	return f.file_name, noi if isinstance(noi, bytes) else noi.encode("utf-8")


def _doc_va_xem(ten, byte, cong_ty):
	"""Trả [(tệp con, kq mẫu, xem trước)]. Lỗi đọc tệp thành kq rỗng có lý do."""
	try:
		ds = tep_doc.doc_tep(ten, byte)
	except tep_doc.LoiTep as e:
		kq = mau_bc.ket_qua("", "", "", "")
		kq["loi"].append(str(e))
		return [(dict(ten=ten, sha256=tep_doc.bam(byte), loai=""), kq, khop.xem_truoc(kq, cong_ty))]
	ra = []
	for t in ds:
		kq = mau_bc.doc(t)
		da_nhan = _da_nhan(cong_ty, kq)
		ra.append((t, kq, khop.xem_truoc(kq, cong_ty, da_nhan)))
	return ra


def _da_nhan(cong_ty, kq):
	"""Snapshot {khoá: dấu nội dung} của các sự kiện tệp này đã có trong DB."""
	khoa_ds = [khop.khoa(cong_ty, kq["vendor"], kq["tai_khoan"] or "-", d["ma_su_kien"]) for d in kq["dong"]]
	ra = {}
	for i in range(0, len(khoa_ds), 500):
		for r in frappe.get_all(DT_DONG, filters={"khoa": ["in", khoa_ds[i:i + 500]]}, fields=["khoa", "dau_noi_dung"]):
			ra[r.khoa] = r.dau_noi_dung
	return ra


@frappe.whitelist()
def xem_truoc(file_url=None):
	"""Đọc tệp và nói sẽ nhận gì; không ghi gì."""
	_chan()
	ten, byte = _doc_file(file_url)
	cong_ty = _cong_ty()
	ra = []
	for t, kq, xt in _doc_va_xem(ten, byte, cong_ty):
		tt = tom_tat(kq, xt)
		tt["ten_tep"] = t["ten"]
		tt["da_co"] = frappe.db.get_value(DT_NGUON, {"sha256": t["sha256"]}, "name") or ""
		ra.append(tt)
	return ra


@frappe.whitelist()
def nhan(file_url=None):
	"""Nhận tệp đã xem trước: đọc lại ở máy chủ (không tin số máy khách gửi)."""
	_chan(True)
	ten, byte = _doc_file(file_url)
	return _nhan_byte(ten, byte, "Tải tay", file_url=file_url)


def _nhan_byte(ten, byte, kenh, file_url=None, communication=None, chi_mau_quen=False):
	cong_ty = _cong_ty()
	ket = []
	for t, kq, xt in _doc_va_xem(ten, byte, cong_ty):
		if chi_mau_quen and not kq["mau"]:
			continue
		da = frappe.db.get_value(DT_NGUON, {"sha256": t["sha256"]}, ["name", "trang_thai"], as_dict=True)
		if da:
			ket.append(dict(name=da.name, trang_thai=da.trang_thai, da_co=1, ten_tep=t["ten"]))
			continue
		ket.append(_ghi_nguon(cong_ty, t, kq, xt, kenh, file_url, communication))
	frappe.db.commit()
	return ket


def _ghi_nguon(cong_ty, t, kq, xt, kenh, file_url, communication):
	tong_tep = (kq.get("tong") or {}).get("thuc_nhan")
	so = xt["so"]
	ly_do = "; ".join(xt["loi"][:5])
	if so["loi"]:
		ly_do = ("%s dòng lỗi. " % so["loi"]) + ly_do
	nguon = frappe.get_doc(dict(
		doctype=DT_NGUON, company=cong_ty, nhom=khop.NHOM_TEN.get(kq["nhom"]) or "Tiền bán",
		vendor=kq["vendor"] or "Chưa nhận ra", mau=kq["mau"], ten_mau=mau_bc.TEN_MAU.get(kq["mau"], ""),
		tai_khoan=kq["tai_khoan"], tu_ngay=kq["tu_ngay"] or None, den_ngay=kq["den_ngay"] or None,
		ngay_tien_ve=kq["ngay_tien_ve"] or None, trang_thai=xt["trang_thai"], ly_do=ly_do[:1000],
		kenh_nhan=kenh, ten_tep=(t["ten"] or "")[:140], tep=file_url, sha256=t["sha256"],
		communication=communication, phien_ban=mau_bc.PHIEN_BAN, so_dong=len(kq["dong"]),
		so_moi=so["moi"], so_trung=so["trung"], so_loi=so["loi"], tien_hang=xt["tong"]["tien_hang"],
		phi=xt["tong"]["phi"], thuc_nhan=xt["tong"]["thuc_nhan"], tong_tep=tong_tep,
		trang_thai_tien="Chưa đối chiếu",
		du_lieu=json.dumps(dict(loi=xt["loi"], canh_bao=xt["canh_bao"], tong=kq.get("tong"), them=kq.get("them"),
			ghi_chu_don_vi=kq.get("ghi_chu_don_vi"), dong_loi=[dict(vi_tri=x["vi_tri"], ly_do=x.get("ly_do", ""))
				for x in xt["dong"] if x["trang_thai"] == "loi"][:300]), ensure_ascii=False, default=str),
	))
	frappe.db.savepoint("ds_nguon")
	try:
		nguon.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		# Hai lượt nhận cùng tệp chạy song song: lượt sau dừng ở đây, không
		# lùi các tệp khác trong cùng gói zip đã ghi.
		frappe.db.rollback(save_point="ds_nguon")
		ten = frappe.db.get_value(DT_NGUON, {"sha256": t["sha256"]}, "name")
		return dict(name=ten, trang_thai="", da_co=1, ten_tep=t["ten"])
	trung_ve_sau = 0
	for x in xt["dong"]:
		if x["trang_thai"] != "moi":
			continue
		d = x["dong"]
		dong = frappe.get_doc(dict(
			doctype=DT_DONG, nguon=nguon.name, company=cong_ty, nhom=kq["nhom"], vendor=kq["vendor"],
			tai_khoan=kq["tai_khoan"], khoa=d["khoa"], dau_noi_dung=d["dau_noi_dung"],
			ma_su_kien=d["ma_su_kien"][:140], ngay=d["ngay"] or None, gio=d["gio"],
			ngay_tien_ve=d["ngay_tien_ve"] or None, loai=d["loai"], merchant=d["merchant"][:140],
			diem_ban=d["diem_ban"], ma_don=(d["ma_don"] or "")[:140], ma_tham_chieu=(d["ma_tham_chieu"] or "")[:140],
			ma_can_cu=(d.get("ma_can_cu") or "")[:140], hoa_don_nguon=(d.get("hoa_don") or "")[:140],
			mo_ta=(d["mo_ta"] or "")[:140], nguoi=(d.get("nguoi") or "")[:140], giao_hang=1 if d.get("giao_hang") else 0,
			tien_hang=d["tien_hang"], giam_gia=d["giam_gia"], phi=d["phi"], dieu_chinh=d["dieu_chinh"],
			thue=d["thue"], thuc_nhan=d["thuc_nhan"], trang_thai_khop="Chưa nối"))
		frappe.db.savepoint("ds_dong")
		try:
			dong.insert(ignore_permissions=True, ignore_links=True)
		except frappe.DuplicateEntryError:
			# Nguồn khác vừa nhận cùng sự kiện giữa lúc xem trước và lúc ghi.
			frappe.db.rollback(save_point="ds_dong")
			trung_ve_sau += 1
	if trung_ve_sau:
		nguon.db_set({"so_moi": so["moi"] - trung_ve_sau, "so_trung": so["trung"] + trung_ve_sau})
	_doi_chieu(nguon.name)
	return dict(name=nguon.name, trang_thai=nguon.trang_thai, da_co=0, ten_tep=t["ten"])


# ------------------------------------------------------------ đối chiếu

@frappe.whitelist()
def doi_chieu_lai(name=None):
	_chan(True)
	_doi_chieu(name)
	frappe.db.commit()
	return chi_tiet(name)


def _doi_chieu(name):
	nguon = frappe.get_doc(DT_NGUON, name)
	dong = frappe.get_all(DT_DONG, filters={"nguon": name}, fields=["*"], order_by="ngay asc, gio asc",
		limit_page_length=20000)
	if nguon.nhom == "Tiền bán":
		_noi_hoa_don_ban(nguon, dong)
		_tien_ve(nguon)
	elif nguon.nhom == "Chuyến đi":
		_noi_chuyen(nguon, dong)
		nguon.db_set("trang_thai_tien", "Không áp dụng")
	elif nguon.nhom == "Thẻ tín dụng":
		_ky_the(nguon)
		nguon.db_set("trang_thai_tien", "Không áp dụng")
	else:
		_tong_hop(nguon)
		nguon.db_set("trang_thai_tien", "Không áp dụng")
	dem = frappe.db.sql("""select sum(trang_thai_khop in ('Đã nối','Nối theo tiền')),
		sum(trang_thai_khop not in ('Đã nối','Nối theo tiền','Không áp dụng'))
		from `tab%s` where nguon=%%s""" % DT_DONG, name)[0]
	nguon.db_set({"so_da_noi": int(dem[0] or 0), "so_chua_noi": int(dem[1] or 0)})


def _noi_hoa_don_ban(nguon, dong):
	kieu = khop.KIEU_THEO_MAU.get(nguon.mau)
	ban = [d for d in dong if d.loai in ("ban", "hoan")]
	if not kieu or not ban:
		for d in dong:
			if d.loai not in ("ban", "hoan"):
				frappe.db.set_value(DT_DONG, d.name, "trang_thai_khop", "Không áp dụng", update_modified=False)
		return
	lech = khop.LECH_NGAY.get(kieu, 0)
	tu = frappe.utils.add_days(min(str(d.ngay) for d in ban), -lech)
	den = frappe.utils.add_days(max(str(d.ngay) for d in ban), lech)
	uv = _ung_vien_hd(kieu, tu, den)
	# Hoá đơn đã nối với dòng của nguồn khác thì không đưa vào lại (một đối một toàn hệ).
	da_noi = set(frappe.get_all(DT_DONG, filters={"sales_invoice": ["in", [u["name"] for u in uv] or [""]],
		"nguon": ["!=", nguon.name]}, pluck="sales_invoice"))
	uv = [u for u in uv if u["name"] not in da_noi]
	dong_ds = [dict(loai=d.loai, ngay=str(d.ngay), ma_tham_chieu=d.ma_tham_chieu or "", tien_hang=int(d.tien_hang),
		giam_gia=int(d.giam_gia)) for d in dong]
	kq = khop.khop_hoa_don(kieu, dong_ds, uv)
	for i, d in enumerate(dong):
		r = kq.get(i)
		if not r:
			continue
		frappe.db.set_value(DT_DONG, d.name, {"trang_thai_khop": r["trang_thai"], "sales_invoice": r["hoa_don"] or None,
			"ghi_chu_khop": r["ghi_chu"]}, update_modified=False)


def _ung_vien_hd(kieu, tu, den):
	"""Hoá đơn bán đã ghi sổ, chưa huỷ mềm, trong khoảng ngày, đúng nguồn/phương thức."""
	loc = {"docstatus": 1, "posting_date": ["between", [tu, den]]}
	meta = frappe.get_meta("Sales Invoice")
	if meta.has_field("vgb_huy"):
		loc["vgb_huy"] = 0
	truong = ["name", "posting_date", "grand_total", "rounded_total"]
	for f in ("vgb_ma_tham_chieu", "vgb_pt_thanh_toan", "custom_nguon"):
		if meta.has_field(f):
			truong.append(f)
	ra = []
	tt = TIEN_TO_THEO_KIEU.get(kieu, {})
	if kieu in NGUON_THEO_KIEU and meta.has_field("custom_nguon"):
		loc_n = dict(loc, custom_nguon=["in", list(NGUON_THEO_KIEU[kieu])])
		for r in frappe.get_all("Sales Invoice", filters=loc_n, fields=truong, limit_page_length=5000):
			ra.append(dict(name=r.name, ngay=str(r.posting_date), tien=int(round(r.rounded_total or r.grand_total or 0)),
				ma=[r.get("vgb_ma_tham_chieu") or ""] + _ma_dong_tt(r.name), tien_to=tt.get("nguon", "")))
	pt = PT_THEO_KIEU.get(kieu, ())
	if not pt:
		return ra
	da_co = {u["name"] for u in ra}
	# Một bill trả nhiều kênh: lấy đúng dòng thanh toán của phương thức này.
	dong_tt = frappe.db.sql("""select d.parent, d.so_tien, d.ma_tham_chieu, s.posting_date
		from `tabVagabond Dong Thanh Toan` d join `tabSales Invoice` s on s.name = d.parent
		where d.parenttype='Sales Invoice' and d.pt in %(pt)s and s.docstatus=1
			and s.posting_date between %(tu)s and %(den)s""", dict(pt=pt, tu=tu, den=den), as_dict=True) \
		if frappe.db.table_exists("Vagabond Dong Thanh Toan") else []
	co_dong = set()
	for r in dong_tt:
		if r.parent in da_co:
			continue
		co_dong.add(r.parent)
		ra.append(dict(name=r.parent, ngay=str(r.posting_date), tien=int(round(r.so_tien or 0)), ma=[r.ma_tham_chieu or ""],
			tien_to=tt.get("pt", "")))
	if meta.has_field("vgb_pt_thanh_toan"):
		loc_p = dict(loc, vgb_pt_thanh_toan=["in", list(pt)])
		for r in frappe.get_all("Sales Invoice", filters=loc_p, fields=truong, limit_page_length=5000):
			if r.name in co_dong or r.name in da_co:
				continue
			ra.append(dict(name=r.name, ngay=str(r.posting_date), tien=int(round(r.rounded_total or r.grand_total or 0)),
				ma=[r.get("vgb_ma_tham_chieu") or ""], tien_to=tt.get("pt", "")))
	return ra


def _ma_dong_tt(si):
	if not frappe.db.table_exists("Vagabond Dong Thanh Toan"):
		return []
	return [m for m in frappe.get_all("Vagabond Dong Thanh Toan", filters={"parent": si, "parenttype": "Sales Invoice"},
		pluck="ma_tham_chieu") if m]


def _tien_ve(nguon):
	"""Dò giao dịch tiền vào khớp tổng thực nhận của nguồn (chỉ đọc)."""
	if not nguon.thuc_nhan or nguon.mau == "onepay_thang" or nguon.mau == "shinhan_thang":
		# Báo cáo tháng gộp nhiều đợt trả; mỗi đợt đã đối chiếu ở báo cáo ngày.
		nguon.db_set({"trang_thai_tien": "Không áp dụng"})
		return
	goc = nguon.ngay_tien_ve or nguon.den_ngay
	if not goc:
		nguon.db_set({"trang_thai_tien": "Chưa thấy tiền về", "giao_dich_ngan_hang": ""})
		return
	tu = frappe.utils.add_days(goc, -1)
	den = frappe.utils.add_days(goc, 6)
	gd = [dict(name=r.name, ngay=str(r.date), tien=int(round(r.deposit or 0)),
		mo_ta=" ".join(x for x in (r.description, r.reference_number) if x))
		for r in frappe.get_all("Bank Transaction", filters={"docstatus": 1, "date": ["between", [tu, den]],
			"deposit": [">", 0]}, fields=["name", "date", "deposit", "description", "reference_number"],
			order_by="date asc, name asc", limit_page_length=5000)]
	da_dung = set()
	# Codex #446 F2: một giao dịch đã gắn cho nguồn bất kỳ (mọi vendor) thì
	# không đưa cho nguồn khác nữa. Shinhan không có mẫu nội dung, lọc theo
	# vendor sẽ để Shinhan "thấy tiền về" bằng giao dịch của Payoo cùng số.
	for r in frappe.get_all(DT_NGUON, filters={"name": ["!=", nguon.name],
			"giao_dich_ngan_hang": ["is", "set"], "den_ngay": [">=", frappe.utils.add_days(goc, -60)]},
			pluck="giao_dich_ngan_hang"):
		da_dung.update(x for x in (r or "").split("\n") if x)
	tt, ds, ghi = khop.khop_ngan_hang(nguon.mau, int(round(nguon.thuc_nhan)), str(tu), str(den), gd, da_dung)
	nguon.db_set({"trang_thai_tien": tt, "giao_dich_ngan_hang": "\n".join(ds)})
	_ghi_them(nguon.name, tien_ve=ghi)


def _ghi_them(name, **k):
	cu = frappe.db.get_value(DT_NGUON, name, "du_lieu")
	try:
		d = json.loads(cu or "{}")
	except ValueError:
		d = {}
	d.update(k)
	frappe.db.set_value(DT_NGUON, name, "du_lieu", json.dumps(d, ensure_ascii=False, default=str), update_modified=False)


def _noi_chuyen(nguon, dong):
	"""Chuyến giao hàng nối Vận đơn theo mã đặt chuyến; chuyến có số hoá đơn
	riêng (Grab for Business) nối Hoá đơn mua theo ký hiệu + số."""
	ma = [d.ma_su_kien for d in dong] + [d.ma_don for d in dong if d.ma_don]
	vd = {}
	if ma and frappe.db.table_exists("Van Don") and frappe.get_meta("Van Don").has_field("booking_id"):
		for i in range(0, len(ma), 500):
			for r in frappe.get_all("Van Don", filters={"booking_id": ["in", ma[i:i + 500]]}, fields=["name", "booking_id"]):
				vd[r.booking_id] = r.name
	pi_meta = frappe.get_meta("Purchase Invoice")
	co_hd = pi_meta.has_field("custom_hddt_so")
	for d in dong:
		if d.loai not in ("chuyen", "phi_quan_ly", "dieu_chinh"):
			continue
		cap = {}
		v = vd.get(d.ma_su_kien) or vd.get(d.ma_don)
		if v:
			cap["van_don"] = v
		if d.hoa_don_nguon and co_hd and "#" in d.hoa_don_nguon:
			ky, so = d.hoa_don_nguon.split("#", 1)
			loc = {"docstatus": ["<", 2], "custom_hddt_so": ["in", [so, so.lstrip("0")]]}
			ung = frappe.get_all("Purchase Invoice", filters=loc, fields=["name", "grand_total"] + (
				["custom_hddt_ky_hieu"] if pi_meta.has_field("custom_hddt_ky_hieu") else []), limit_page_length=5)
			ung = [u for u in ung if not u.get("custom_hddt_ky_hieu") or ky.endswith(u.custom_hddt_ky_hieu) or u.custom_hddt_ky_hieu.endswith(ky[-6:])]
			if len(ung) == 1:
				cap["purchase_invoice"] = ung[0].name
		if cap.get("purchase_invoice") or cap.get("van_don"):
			cap["trang_thai_khop"] = "Đã nối"
			cap["ghi_chu_khop"] = ", ".join(x for x in (("Vận đơn " + cap["van_don"]) if cap.get("van_don") else "",
				("Hoá đơn mua " + cap["purchase_invoice"]) if cap.get("purchase_invoice") else "") if x)
		else:
			cap["trang_thai_khop"] = "Không thấy chứng từ" if d.giao_hang or d.hoa_don_nguon else "Chưa nối"
			cap["ghi_chu_khop"] = "Chưa thấy vận đơn hoặc hoá đơn mua cùng mã." if cap["trang_thai_khop"] != "Chưa nối" else ""
		frappe.db.set_value(DT_DONG, d.name, cap, update_modified=False)
	# Hoá đơn gộp cả kỳ (Be, Xanh SM): tìm hoá đơn mua cùng tổng tiền sau kỳ.
	if nguon.mau in ("be", "xanh_taxi") and nguon.den_ngay and nguon.thuc_nhan:
		mst = {"be": "0108269207", "xanh_taxi": "0110269067"}[nguon.mau]
		ncc = frappe.get_all("Supplier", filters={"tax_id": mst}, pluck="name")
		pi = frappe.get_all("Purchase Invoice", filters={"docstatus": ["<", 2], "supplier": ["in", ncc or [""]],
			"posting_date": ["between", [nguon.tu_ngay, frappe.utils.add_days(nguon.den_ngay, 40)]]},
			fields=["name", "grand_total"], limit_page_length=50)
		hop = [p.name for p in pi if int(round(p.grand_total or 0)) == int(round(nguon.thuc_nhan))]
		_ghi_them(nguon.name, hoa_don_ky=hop, hoa_don_ky_ghi_chu=(
			"Hoá đơn mua cùng tổng tiền: " + ", ".join(hop)) if hop else "Chưa thấy hoá đơn mua cùng tổng tiền của kỳ.")


def _ky_the(nguon):
	"""Dựng phương trình số dư thẻ với sao kê kỳ trước cùng tài khoản."""
	d = json.loads(nguon.du_lieu or "{}")
	truoc = frappe.get_all(DT_NGUON, filters={"mau": nguon.mau, "tai_khoan": nguon.tai_khoan,
		"den_ngay": ["<", nguon.tu_ngay], "name": ["!=", nguon.name]}, fields=["du_lieu"],
		order_by="den_ngay desc", limit_page_length=1)
	tong_truoc = json.loads(truoc[0].du_lieu or "{}").get("tong") if truoc else None
	_ghi_them(nguon.name, ky_the=khop.ky_the(d.get("tong"), tong_truoc))


def _tong_hop(nguon):
	"""Biên bản tháng OnePay: so tổng biên bản với các thông báo ngày đã nhận."""
	d = json.loads(nguon.du_lieu or "{}")
	kenh = (d.get("them") or {}).get("kenh") or ""
	tien = frappe.db.sql("""select coalesce(sum(tien_hang),0), coalesce(sum(phi),0), coalesce(sum(thuc_nhan),0), count(*)
		from `tab%s` where vendor='OnePay' and ma_su_kien like %%s and ngay_tien_ve between %%s and %%s""" % DT_DONG,
		("%s:%%" % kenh, nguon.tu_ngay, frappe.utils.add_days(nguon.den_ngay, 5)))[0]
	bb = d.get("tong") or {}
	lech = {k: int(bb.get(k) or 0) - int(v or 0) for k, v in zip(("tien_hang", "phi", "thuc_nhan"), tien[:3])}
	_ghi_them(nguon.name, doi_bien_ban=dict(da_nhan=dict(tien_hang=int(tien[0]), phi=int(tien[1]),
		thuc_nhan=int(tien[2]), so_dong=int(tien[3])), lech=lech, khop=not any(lech.values())))


# ------------------------------------------------------------ đọc cho màn hình

@frappe.whitelist()
def ds(nhom=None, trang_thai=None, vendor=None, tim=None, ky=None, tu=None, den=None, trang=0):
	"""Danh sách nguồn + số cho thẻ tóm tắt và ba hàng chip (máy chủ đếm).

	ky là khoá chip ngày dùng chung (khung/cong_cu_ds.khoang_ky), lọc theo
	ngày cuối kỳ của báo cáo. Nguồn lỗi chưa đọc ra kỳ chỉ hiện ở "Mọi ngày".
	"""
	_chan()
	from vagabond.khung.cong_cu_ds import khoang_ky

	loc = {}
	a, b = khoang_ky(ky, frappe.utils.nowdate(), tu, den)
	if a or b:
		loc["den_ngay"] = ["between", [a or "2000-01-01", b or "2100-12-31"]]
	if nhom:
		loc["nhom"] = nhom
	if vendor:
		loc["vendor"] = vendor
	if trang_thai == "Cần xử lý":
		loc["trang_thai"] = ["in", ["Cần xử lý", "Lỗi tệp"]]
	elif trang_thai in ("Chưa thấy tiền về", "Lệch tiền về"):
		loc["trang_thai_tien"] = trang_thai
	elif trang_thai == "Chưa nối đủ":
		loc["so_chua_noi"] = [">", 0]
	or_loc = None
	if tim:
		t = "%%%s%%" % tim.strip()
		or_loc = [["ten_tep", "like", t], ["vendor", "like", t], ["name", "like", t], ["tai_khoan", "like", t]]
	trang = int(trang or 0)
	hang = frappe.get_all(DT_NGUON, filters=loc, or_filters=or_loc, fields=["name", "nhom", "vendor", "ten_mau",
		"tu_ngay", "den_ngay", "ngay_tien_ve", "trang_thai", "trang_thai_tien", "thuc_nhan", "so_dong", "so_moi",
		"so_trung", "so_loi", "so_da_noi", "so_chua_noi", "kenh_nhan", "ten_tep", "creation"],
		order_by="coalesce(den_ngay, creation) desc, creation desc", start=trang * 50, page_length=51)
	dem = {}
	for nh, tt, ttt, cn, n in frappe.db.sql("""select nhom, trang_thai, trang_thai_tien, so_chua_noi > 0, count(*)
			from `tab%s` group by 1, 2, 3, 4""" % DT_NGUON):
		dem.setdefault("nhom:" + nh, 0)
		dem["nhom:" + nh] += n
		if tt in ("Cần xử lý", "Lỗi tệp"):
			dem["Cần xử lý"] = dem.get("Cần xử lý", 0) + n
		if ttt in ("Chưa thấy tiền về", "Lệch tiền về"):
			dem[ttt] = dem.get(ttt, 0) + n
		if cn:
			dem["Chưa nối đủ"] = dem.get("Chưa nối đủ", 0) + n
		dem["tat_ca"] = dem.get("tat_ca", 0) + n
	dem_vendor = dict(frappe.db.sql("select vendor, count(*) from `tab%s` where nhom=%%s group by vendor" % DT_NGUON,
		nhom or "Tiền bán"))
	dem_vendor["tat_ca"] = sum(dem_vendor.values())
	return dict(hang=hang[:50], con=len(hang) > 50, dem=dem, vendor=sorted(dem_vendor.keys() - {"tat_ca"}),
		dem_vendor=dem_vendor)


@frappe.whitelist()
def chi_tiet(name=None, loc=None, trang=0):
	_chan()
	n = frappe.get_doc(DT_NGUON, name)
	d = json.loads(n.du_lieu or "{}")
	f = {"nguon": name}
	if loc == "chua_noi":
		f["trang_thai_khop"] = ["not in", ["Đã nối", "Nối theo tiền", "Không áp dụng"]]
	elif loc == "da_noi":
		f["trang_thai_khop"] = ["in", ["Đã nối", "Nối theo tiền"]]
	trang = int(trang or 0)
	dong = frappe.get_all(DT_DONG, filters=f, fields=["name", "ngay", "gio", "loai", "ma_don", "ma_tham_chieu",
		"mo_ta", "nguoi", "tien_hang", "giam_gia", "phi", "thuc_nhan", "trang_thai_khop", "sales_invoice",
		"purchase_invoice", "van_don", "ghi_chu_khop", "diem_ban"], order_by="ngay asc, gio asc",
		start=trang * 100, page_length=101)
	return dict(nguon=dict((k, n.get(k)) for k in ("name", "nhom", "vendor", "ten_mau", "tai_khoan", "tu_ngay",
		"den_ngay", "ngay_tien_ve", "trang_thai", "ly_do", "kenh_nhan", "ten_tep", "tep", "so_dong", "so_moi",
		"so_trung", "so_loi", "tien_hang", "phi", "thuc_nhan", "tong_tep", "trang_thai_tien", "giao_dich_ngan_hang",
		"so_da_noi", "so_chua_noi", "creation", "communication")),
		them=dict(loi=d.get("loi") or [], canh_bao=d.get("canh_bao") or [], dong_loi=(d.get("dong_loi") or [])[:100],
			tien_ve=d.get("tien_ve") or "", ky_the=d.get("ky_the"), doi_bien_ban=d.get("doi_bien_ban"),
			hoa_don_ky=d.get("hoa_don_ky_ghi_chu") or "", ghi_chu_don_vi=d.get("ghi_chu_don_vi") or ""),
		dong=dong[:100], con=len(dong) > 100)


@frappe.whitelist()
def cua_hoa_don(si=None):
	"""Các dòng vendor đã nối với một hoá đơn bán (vùng Đối soát trên hoá đơn)."""
	_chan()
	return frappe.get_all(DT_DONG, filters={"sales_invoice": si}, fields=["name", "nguon", "vendor", "ngay",
		"ma_don", "tien_hang", "giam_gia", "phi", "thuc_nhan", "trang_thai_khop", "ghi_chu_khop", "ngay_tien_ve"])


@frappe.whitelist()
def suc_khoe():
	"""Mỗi nguồn: lần nhận gần nhất, kỳ mới nhất, số nguồn cần xử lý, số chưa
	thấy tiền về. Nguồn chưa từng nhận hiện "Chưa có", không hiện số 0."""
	_chan()
	ra = []
	for vendor, nhom in [(t, n) for _k, _a, _b, t, n in mau_bc.MAU]:
		r = frappe.db.sql("""select max(den_ngay), max(creation), sum(trang_thai in ('Cần xử lý','Lỗi tệp')),
			sum(trang_thai_tien in ('Chưa thấy tiền về','Lệch tiền về')), count(*) from `tab%s`
			where vendor=%%s""" % DT_NGUON, vendor)[0]
		ra.append(dict(vendor=vendor, nhom=khop.NHOM_TEN.get(nhom), ky_moi=str(r[0] or ""),
			nhan_luc=str(r[1] or ""), can_xu_ly=int(r[2] or 0), chua_tien=int(r[3] or 0), so_nguon=int(r[4] or 0)))
	return ra


# ------------------------------------------------------------ email

def khi_co_thu(doc, method=None):
	"""Hook Communication.after_insert: thư từ vendor thì xếp việc đọc đính kèm
	SAU khi lưu xong (đính kèm được ghi sau insert). Không bao giờ làm hỏng
	việc nhận thư: mọi lỗi nuốt ở đây chỉ vì đây là hook của hạ tầng thư."""
	try:
		if doc.communication_type != "Communication" or doc.sent_or_received != "Received":
			return
		if not la_thu_vendor(doc.sender):
			return
		frappe.enqueue("vagabond.doi_soat_vendor.xu_ly_thu", queue="long", enqueue_after_commit=True,
			job_id="doi-soat-thu-%s" % doc.name, deduplicate=True, comm=doc.name)
	except Exception:
		frappe.log_error(title="Đối soát vendor: xếp việc đọc thư")


def xu_ly_thu(comm):
	ket = []
	for f in frappe.get_all("File", filters={"attached_to_doctype": "Communication", "attached_to_name": comm},
			fields=["name", "file_name", "file_url"]):
		if not (f.file_name or "").lower().endswith(DUOI):
			continue
		try:
			byte = frappe.get_doc("File", f.name).get_content()
			if isinstance(byte, str):
				byte = byte.encode("utf-8")
			ket.extend(_nhan_byte(f.file_name, byte, "Email", file_url=f.file_url, communication=comm, chi_mau_quen=True))
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title="Đối soát vendor: đọc đính kèm %s" % f.file_name)
	return ket


@frappe.whitelist()
def quet_email(so_ngay=3):
	"""Đọc lại đính kèm của thư vendor trong N ngày (nút "Nhận lại từ email" và
	lượt quét mỗi giờ). Tệp đã nhận thì dừng ở mã băm, không nhận hai lần."""
	if frappe.session.user != "Administrator":
		_chan(True)
	so_ngay = max(1, min(int(so_ngay or 3), 31))
	dem = 0
	for c in frappe.get_all("Communication", filters={"sent_or_received": "Received", "communication_type": "Communication",
			"creation": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -so_ngay)]}, fields=["name", "sender"],
			limit_page_length=2000):
		if la_thu_vendor(c.sender):
			dem += len(xu_ly_thu(c.name))
	return dict(so_tep=dem)


def quet_moi_gio():
	frappe.set_user("Administrator")
	quet_email(2)
