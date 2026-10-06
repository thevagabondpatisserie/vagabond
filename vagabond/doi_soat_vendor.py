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
import re
from contextlib import contextmanager

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
VENDOR_THEO_MIEN = {"greensm.com": "Xanh SM", "xanhsm.com": "Xanh SM", "grab.com": "Grab", "grabtaxi.com": "Grab",
	"onepay.vn": "OnePay", "payoo.com.vn": "Payoo", "shopeefood.vn": "ShopeeFood", "shopee.vn": "ShopeeFood",
	"shinhan.com.vn": "Shinhan", "be.com.vn": "Be for Business"}
_TU_BAO_CAO = ("bao cao", "sao ke", "doi soat", "bien ban", "statement", "settlement", "report", "tam ung",
	"thanh toan")

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


def vendor_theo_thu(nguoi_gui):
	"""THUẦN. Tên vendor đoán từ tên miền người gửi, để nguồn lỗi vẫn hiện đúng nhóm."""
	s = (nguoi_gui or "").strip().lower()
	if "<" in s and ">" in s:
		s = s[s.index("<") + 1:s.index(">")]
	mien = s.rsplit("@", 1)[-1] if "@" in s else ""
	return next((v for m, v in VENDOR_THEO_MIEN.items() if mien == m or mien.endswith("." + m)), "")


def thu_co_bao_cao(tieu_de, noi_dung):
	"""THUẦN. Codex #446 H2: thư vendor không có tệp đọc được nhưng tiêu đề hay
	thân thư nói tới báo cáo, sao kê, đối soát, thanh toán thì phải hiện cho
	kế toán thấy, không được im lặng như thư quảng cáo."""
	from vagabond.doi_soat_mau import chuan

	chu = chuan((tieu_de or "") + " " + re.sub(r"<[^>]+>", " ", noi_dung or "")[:5000])
	return any(t in chu for t in _TU_BAO_CAO)


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


def _cong_ty_xem():
	"""Codex #446 H1: các pháp nhân người đang dùng được xem (theo User
	Permission của Company). Mọi danh sách, đếm và chi tiết đối soát lọc theo
	đây; không có pháp nhân nào thì trả [""] để truy vấn ra rỗng."""
	from frappe.permissions import get_user_permissions

	tat_ca = frappe.get_all("Company", pluck="name")
	duoc = {x.get("doc") for x in (get_user_permissions(frappe.session.user).get("Company") or [])}
	return chon_cong_ty(tat_ca, duoc)


def chon_cong_ty(tat_ca, duoc):
	"""THUẦN. Không có User Permission Company thì xem tất cả; có thì chỉ các
	pháp nhân được cấp. Rỗng trả [""] để truy vấn `in` ra rỗng chứ không lỗi."""
	return [c for c in tat_ca if not duoc or c in duoc] or [""]


def _chan_cong_ty(cong_ty):
	if cong_ty not in _cong_ty_xem():
		frappe.throw("Nguồn đối soát này thuộc pháp nhân anh/chị chưa được xem.", frappe.PermissionError)


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
	try:
		f.insert(ignore_permissions=True)
	except frappe.ValidationError:
		raise
	except Exception:
		# Frappe mở thử PDF trước khi cất (dò mã chạy ngầm); PDF hỏng làm thư
		# viện đọc PDF nổ lỗi kỹ thuật. Báo bằng lời của người dùng.
		frappe.log_error(title="Đối soát vendor: cất tệp tải lên %s" % ten)
		frappe.throw("Không cất được tệp này: tệp bị hỏng hoặc không mở được. Tải lại tệp gốc từ email vendor rồi thử lại.")
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
		if t.get("loai") == "loi":
			kq = mau_bc.ket_qua("", "", "", "")
			kq["loi"].append(t.get("loi") or "Tệp trong gói nén đọc không được.")
			ra.append((t, kq, khop.xem_truoc(kq, cong_ty)))
			continue
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
	_chan_cong_ty(cong_ty)
	ra = []
	for t, kq, xt in _doc_va_xem(ten, byte, cong_ty):
		tt = tom_tat(kq, xt)
		tt["ten_tep"] = t["ten"]
		da = frappe.db.get_value(DT_NGUON, {"sha256": t["sha256"]}, ["name", "trang_thai"], as_dict=True)
		lai = bool(da) and khop.doc_lai_duoc(da.trang_thai)
		tt["da_co"] = da.name if da and not lai else ""
		tt["doc_lai"] = da.name if lai else ""
		ra.append(tt)
	return ra


@frappe.whitelist()
def nhan(file_url=None):
	"""Nhận tệp đã xem trước: đọc lại ở máy chủ (không tin số máy khách gửi)."""
	_chan(True)
	_chan_cong_ty(_cong_ty())
	ten, byte = _doc_file(file_url)
	return _nhan_byte(ten, byte, "Tải tay", file_url=file_url)


KHOA_DOI_CHIEU = "vgb_doi_soat_vendor"


@contextmanager
def khoa_doi_chieu(db=None, cho=60):
	"""Codex #446: mọi lượt nhận tệp và đối chiếu chạy nối tiếp nhau.

	Hai lượt song song (hai thư cùng đến, kế toán bấm lúc thư đang đọc) cùng
	đọc "giao dịch ngân hàng / hoá đơn nào còn trống" trước khi bên kia ghi,
	rồi cùng nhận một giao dịch hay một hoá đơn. Khoá có tên của MariaDB giữ
	qua commit, nên: lấy khoá, commit để mở ảnh dữ liệu mới (không dùng ảnh
	đọc từ trước khi chờ khoá), làm việc, commit, rồi mới nhả khoá.
	"""
	db = db or frappe.db
	r = db.sql("select get_lock(%s, %s)", (KHOA_DOI_CHIEU, cho))
	if not r or r[0][0] != 1:
		frappe.throw("Đang có lượt đối soát khác chạy. Đợi ít phút rồi bấm lại.")
	try:
		db.commit()
		yield
		db.commit()
	finally:
		db.sql("select release_lock(%s)", (KHOA_DOI_CHIEU,))


def _nhan_byte(ten, byte, kenh, file_url=None, communication=None, chi_mau_quen=False, bo_qua=None, doc_lai=True):
	"""bo_qua: nếu là list, ghi tên tệp con bị bỏ qua vì chưa nhận ra mẫu
	hay đọc lỗi (chỉ khi chi_mau_quen), để xu_ly_thu quyết có ghi lại không.
	doc_lai=False: nguồn đã có thì dừng ở mã băm kể cả khi đang lỗi (lượt
	quét thư mỗi giờ không ghi lại mãi một tệp chưa có mẫu)."""
	with khoa_doi_chieu():
		cong_ty = _cong_ty()
		ket = []
		for t, kq, xt in _doc_va_xem(ten, byte, cong_ty):
			if chi_mau_quen and not kq["mau"]:
				if bo_qua is not None:
					bo_qua.append(t["ten"])
				continue
			da = frappe.db.get_value(DT_NGUON, {"sha256": t["sha256"]}, ["name", "trang_thai"], as_dict=True)
			if da and not (doc_lai and khop.doc_lai_duoc(da.trang_thai)):
				ket.append(dict(name=da.name, trang_thai=da.trang_thai, da_co=1, ten_tep=t["ten"]))
				continue
			ket.append(_ghi_nguon(cong_ty, t, kq, xt, kenh, file_url, communication, co_san=da.name if da else None))
	return ket


def _bo_dong_cu(name):
	"""Codex #450: đọc lại một nguồn (sau khi sửa mẫu) thì bản đọc mới là bản
	có hiệu lực. Dòng của bản cũ KHÔNG xoá: chuyển thành dòng "Đã thay", tách
	khỏi nguồn (nguon_cu giữ nguồn gốc), khoá đổi thành "thay:<tên dòng>" (khoá
	gốc giữ ở khoa_cu) để bản mới ghi được cùng sự kiện. Liên kết hoá đơn, vận
	đơn giữ nguyên làm vết; mọi truy vấn "đã dùng" bỏ qua dòng Đã thay.
	Trả lịch sử số dòng các lần đọc của nguồn."""
	cu = frappe.db.get_value(DT_NGUON, name, ["du_lieu", "so_dong", "thuc_nhan"], as_dict=True) or {}
	try:
		lich_su = (json.loads(cu.get("du_lieu") or "{}").get("lan_doc_truoc") or [])
	except ValueError:
		lich_su = []
	luc = frappe.utils.now()
	so = frappe.db.count(DT_DONG, {"nguon": name})
	frappe.db.sql("""update `tab%s` set khoa_cu=khoa, khoa=concat('thay:', name), nguon_cu=nguon, nguon=NULL,
		trang_thai_khop=%%s, thay_luc=%%s where nguon=%%s""" % DT_DONG, (khop.DA_THAY, luc, name))
	lich_su.append(dict(luc=str(luc), so_dong=so, thuc_nhan=cu.get("thuc_nhan")))
	return lich_su[-50:]


def _ghi_nguon(cong_ty, t, kq, xt, kenh, file_url, communication, co_san=None):
	lich_su = None
	if co_san:
		# Gỡ dòng bản cũ TRƯỚC rồi mới xem trước lại: nếu không, dòng cũ cùng
		# khoá bị tính là "đã có" và bản đọc mới không ghi được dòng đúng.
		lich_su = _bo_dong_cu(co_san)
		xt = khop.xem_truoc(kq, cong_ty, _da_nhan(cong_ty, kq))
	tong_tep = (kq.get("tong") or {}).get("thuc_nhan")
	so = xt["so"]
	ly_do = "; ".join(xt["loi"][:5])
	if so["loi"]:
		ly_do = ("%s dòng lỗi. " % so["loi"]) + ly_do
	truong = dict(
		company=cong_ty, nhom=khop.NHOM_TEN.get(kq["nhom"]) or "Tiền bán",
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
				for x in xt["dong"] if x["trang_thai"] == "loi"][:300], lan_doc_truoc=lich_su or None),
			ensure_ascii=False, default=str),
	)
	if co_san:
		# Codex #446 H4: nguồn lỗi hay cần xử lý được đọc lại bằng chính tệp
		# đó (sau khi sửa mẫu hoặc cài thư viện). Cập nhật đúng bản ghi cũ,
		# dòng đã có cùng nội dung thành "đã có", chỉ thêm dòng mới.
		nguon = frappe.get_doc(DT_NGUON, co_san)
		nguon.db_set({k: v for k, v in truong.items() if k not in ("sha256", "company")})
		nguon.reload()
	else:
		nguon = frappe.get_doc(dict(doctype=DT_NGUON, **truong))
	frappe.db.savepoint("ds_nguon")
	try:
		if not co_san:
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
	_chan_cong_ty(frappe.db.get_value(DT_NGUON, name, "company"))
	with khoa_doi_chieu():
		_doi_chieu(name)
	return chi_tiet(name)


@frappe.whitelist()
def xac_nhan_noi(name=None):
	"""Codex #450: kế toán xác nhận một gợi ý "Nối theo tiền" là đúng. Chỉ
	lưu xác nhận trên dòng đối soát, không tạo chứng từ. Đối chiếu lại về sau
	giữ nguyên dòng đã xác nhận."""
	_chan(True)
	d = frappe.db.get_value(DT_DONG, name, ["name", "nguon", "company", "trang_thai_khop", "sales_invoice"], as_dict=True)
	if not d or not d.nguon:
		frappe.throw("Không thấy dòng đối soát này. Tải lại màn hình.")
	_chan_cong_ty(d.company)
	with khoa_doi_chieu():
		d = frappe.db.get_value(DT_DONG, name, ["name", "nguon", "trang_thai_khop", "sales_invoice"], as_dict=True)
		if d.trang_thai_khop != "Nối theo tiền" or not d.sales_invoice:
			frappe.throw("Dòng này không còn là gợi ý nối theo tiền (có thể vừa được đối chiếu lại). Tải lại màn hình.")
		if not _goi_y_con_dung(name):
			frappe.throw("Hoá đơn %s không còn hợp lệ (đã huỷ, đổi tiền hoặc đổi ngày bán). Bấm Đối chiếu lại để máy tìm lại." % d.sales_invoice)
		kieu = _kieu_nguon(d.nguon)
		khac = next((r.nguon for r in frappe.get_all(DT_DONG, filters={"sales_invoice": d.sales_invoice, "name": ["!=", name],
			"trang_thai_khop": ["in", list(khop.GIU_HOA_DON)]}, fields=["nguon"]) if _kieu_nguon(r.nguon) == kieu), None)
		if khac:
			frappe.throw("Hoá đơn %s đã nối chắc với một dòng của nguồn %s. Bấm Đối chiếu lại để máy tìm lại." % (d.sales_invoice, khac))
		frappe.db.set_value(DT_DONG, name, {"trang_thai_khop": "Đã nối", "xac_nhan_boi": frappe.session.user,
			"xac_nhan_luc": frappe.utils.now(), "ghi_chu_khop": "Kế toán xác nhận nối theo tiền với %s." % d.sales_invoice},
			update_modified=False)
		_dem_noi(frappe.get_doc(DT_NGUON, d.nguon))
	return dict(ok=1, nguon=d.nguon)


def _goi_y_con_dung(name):
	"""Codex #450: lúc kế toán bấm xác nhận, hoá đơn gợi ý phải CÒN là ứng viên
	hợp lệ, cùng một phép kiểm với lượt đối chiếu (khop.xac_nhan_con_dung)."""
	d = frappe.db.get_value(DT_DONG, name, ["nguon", "ngay", "tien_hang", "giam_gia", "sales_invoice"], as_dict=True)
	n = frappe.db.get_value(DT_NGUON, d.nguon, ["mau", "company"], as_dict=True)
	kieu = khop.KIEU_THEO_MAU.get(n.mau)
	if not kieu or not d.ngay:
		return False
	lech = khop.LECH_NGAY.get(kieu, 0)
	uv = _ung_vien_hd(kieu, frappe.utils.add_days(d.ngay, -lech), frappe.utils.add_days(d.ngay, lech), n.company)
	return khop.xac_nhan_con_dung(kieu, dict(tien_hang=int(d.tien_hang or 0), giam_gia=int(d.giam_gia or 0),
		sales_invoice=d.sales_invoice), uv)


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
	_dem_noi(nguon)


def _dem_noi(nguon):
	"""Số dòng đã nối / chưa nối của nguồn. Một nguồn: khop.DA_NOI và
	khop.KHONG_TINH_CHUA_NOI (Nối theo tiền còn chờ xác nhận nên chưa nối)."""
	dem = frappe.db.sql("""select sum(trang_thai_khop in %%(da)s), sum(trang_thai_khop not in %%(khong)s)
		from `tab%s` where nguon=%%(n)s""" % DT_DONG, dict(da=khop.DA_NOI, khong=khop.KHONG_TINH_CHUA_NOI, n=nguon.name))[0]
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
	uv = _ung_vien_hd(kieu, tu, den, nguon.company)
	# Hoá đơn đã nối với dòng của nguồn khác thì không đưa vào lại (một đối một toàn hệ).
	# Hoá đơn đã nối CHẮC (theo mã hoặc đã xác nhận) với dòng của nguồn khác thì
	# không đưa vào lại. Gợi ý nối theo tiền chưa xác nhận không giữ hoá đơn.
	# Codex #450: giữ theo TỪNG KÊNH thanh toán. Một bill trả nửa Payoo nửa
	# Shinhan có hai chân thanh toán; nguồn Payoo nối chân Payoo không được chặn
	# nguồn Shinhan nối chân Shinhan của cùng bill.
	da_noi = {r.sales_invoice for r in frappe.get_all(DT_DONG, filters={"sales_invoice": ["in", [u["name"] for u in uv] or [""]],
		"nguon": ["!=", nguon.name], "trang_thai_khop": ["in", list(khop.GIU_HOA_DON)]}, fields=["sales_invoice", "nguon"])
		if _kieu_nguon(r.nguon) == kieu}
	# Dòng kế toán đã xác nhận: còn đúng (hoá đơn còn hợp lệ, cùng tiền) thì giữ
	# nguyên và hoá đơn không đưa cho dòng khác; không còn đúng thì bỏ xác nhận
	# và đối chiếu lại như dòng thường, ghi rõ lý do.
	xac_nhan, hong_xn = set(), set()
	for d in dong:
		if not d.get("xac_nhan_boi"):
			continue
		if khop.xac_nhan_con_dung(kieu, dict(tien_hang=int(d.tien_hang or 0), giam_gia=int(d.giam_gia or 0),
				sales_invoice=d.sales_invoice), uv):
			xac_nhan.add(d.name)
			da_noi.add(d.sales_invoice)
		else:
			hong_xn.add(d.name)
	uv = [u for u in uv if u["name"] not in da_noi]
	# Codex #450: dòng đã xác nhận còn đúng KHÔNG vào lượt khớp, để nó không
	# "chiếm" một hoá đơn cùng tiền khác của dòng chưa nối.
	can_khop = [d for d in dong if d.name not in xac_nhan]
	dong_ds = [dict(loai=d.loai, ngay=str(d.ngay), ma_tham_chieu=d.ma_tham_chieu or "", tien_hang=int(d.tien_hang),
		giam_gia=int(d.giam_gia)) for d in can_khop]
	kq = khop.khop_hoa_don(kieu, dong_ds, uv)
	for i, d in enumerate(can_khop):
		r = kq.get(i)
		if not r:
			continue
		cap = {"trang_thai_khop": r["trang_thai"], "sales_invoice": r["hoa_don"] or None, "ghi_chu_khop": r["ghi_chu"]}
		if d.name in hong_xn:
			cap.update(xac_nhan_boi=None, xac_nhan_luc=None, ghi_chu_khop=("Hoá đơn %s đã xác nhận trước đây nay không còn "
				"hợp lệ (đã huỷ hoặc đổi tiền); xem lại. " % d.sales_invoice) + (r["ghi_chu"] or ""))
		frappe.db.set_value(DT_DONG, d.name, cap, update_modified=False)


def _kieu_nguon(ten):
	"""Kênh thanh toán (khop.KIEU_THEO_MAU) của một nguồn."""
	return khop.KIEU_THEO_MAU.get(frappe.db.get_value(DT_NGUON, ten, "mau") or "")


def _dk_hd(co_ngay_ban, co_huy):
	"""Điều kiện chung cho hoá đơn bán làm ứng viên nối. THUẦN.

	Codex #450: bill nháp duyệt ngày sau thì posting_date đổi sang ngày ghi sổ,
	ngày bán thật giữ ở vgb_ngay_ban. Báo cáo vendor ghi theo ngày bán, nên
	chọn và trả ngày theo ngày bán (một nguồn: vagabond.ngay_ban)."""
	from vagabond import ngay_ban
	dk = ["s.docstatus=1", "s.company=%(ct)s",
		ngay_ban.dk_khoang_sql("s") if co_ngay_ban else "s.posting_date between %(tu)s and %(den)s"]
	if co_huy:
		dk.append("ifnull(s.vgb_huy, 0)=0")
	return " and ".join(dk), (ngay_ban.bieu_ngay_sql("s") if co_ngay_ban else "s.posting_date")


def _ung_vien_hd(kieu, tu, den, cong_ty):
	"""Hoá đơn bán đã ghi sổ, chưa huỷ mềm, trong khoảng NGÀY BÁN, đúng nguồn/phương thức."""
	# Codex #446 H1: chỉ hoá đơn của đúng pháp nhân nguồn (s.company=%(ct)s trong _dk_hd).
	meta = frappe.get_meta("Sales Invoice")
	dk, bieu_ngay = _dk_hd(meta.has_field("vgb_ngay_ban"), meta.has_field("vgb_huy"))
	co_ma = meta.has_field("vgb_ma_tham_chieu")
	cot = "s.name, %s as ngay, s.grand_total, s.rounded_total%s" % (bieu_ngay, ", s.vgb_ma_tham_chieu" if co_ma else "")
	tham = dict(tu=tu, den=den, ct=cong_ty)
	ra = []
	tt = TIEN_TO_THEO_KIEU.get(kieu, {})
	if kieu in NGUON_THEO_KIEU and meta.has_field("custom_nguon"):
		for r in frappe.db.sql("select %s from `tabSales Invoice` s where %s and s.custom_nguon in %%(nguon)s limit 5000"
				% (cot, dk), dict(tham, nguon=tuple(NGUON_THEO_KIEU[kieu])), as_dict=True):
			ra.append(dict(name=r.name, ngay=str(r.ngay), tien=int(round(r.rounded_total or r.grand_total or 0)),
				ma=[r.get("vgb_ma_tham_chieu") or ""] + _ma_dong_tt(r.name), tien_to=tt.get("nguon", "")))
	pt = PT_THEO_KIEU.get(kieu, ())
	if not pt:
		return ra
	da_co = {u["name"] for u in ra}
	# Một bill trả nhiều kênh: lấy đúng dòng thanh toán của phương thức này.
	dong_tt = frappe.db.sql("""select d.parent, d.so_tien, d.ma_tham_chieu, %s as ngay
		from `tabVagabond Dong Thanh Toan` d join `tabSales Invoice` s on s.name = d.parent
		where d.parenttype='Sales Invoice' and d.pt in %%(pt)s and %s""" % (bieu_ngay, dk), dict(tham, pt=pt), as_dict=True) \
		if frappe.db.table_exists("Vagabond Dong Thanh Toan") else []
	co_dong = set()
	for r in dong_tt:
		if r.parent in da_co:
			continue
		co_dong.add(r.parent)
		ra.append(dict(name=r.parent, ngay=str(r.ngay), tien=int(round(r.so_tien or 0)), ma=[r.ma_tham_chieu or ""],
			tien_to=tt.get("pt", "")))
	if meta.has_field("vgb_pt_thanh_toan"):
		for r in frappe.db.sql("select %s from `tabSales Invoice` s where %s and s.vgb_pt_thanh_toan in %%(pt)s limit 5000"
				% (cot, dk), dict(tham, pt=tuple(pt)), as_dict=True):
			if r.name in co_dong or r.name in da_co:
				continue
			ra.append(dict(name=r.name, ngay=str(r.ngay), tien=int(round(r.rounded_total or r.grand_total or 0)),
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
	if nguon.trang_thai != "Đã nhận":
		# Codex #450: nguồn còn dòng lỗi thì tổng thực nhận chỉ là phần đọc được;
		# dò tiền về bằng tổng đó dễ gặp nhầm một giao dịch khác cùng số.
		nguon.db_set({"trang_thai_tien": "Chưa đối chiếu", "giao_dich_ngan_hang": ""})
		_ghi_them(nguon.name, tien_ve="Nguồn còn dòng cần xử lý; đối chiếu tiền về sau khi đọc đủ dòng.")
		return
	goc = nguon.ngay_tien_ve or nguon.den_ngay
	if not goc:
		nguon.db_set({"trang_thai_tien": "Chưa thấy tiền về", "giao_dich_ngan_hang": ""})
		return
	tu = frappe.utils.add_days(goc, -1)
	den = frappe.utils.add_days(goc, 6)
	gd = [dict(name=r.name, ngay=str(r.date), tien=int(round(r.deposit or 0)),
		mo_ta=" ".join(x for x in (r.description, r.reference_number) if x))
		for r in frappe.get_all("Bank Transaction", filters=dict({"docstatus": 1, "date": ["between", [tu, den]],
			"deposit": [">", 0]}, **({"company": nguon.company} if frappe.get_meta("Bank Transaction").has_field("company") else {})), fields=["name", "date", "deposit", "description", "reference_number"],
			order_by="date asc, name asc", limit_page_length=5000)]
	da_dung = set()
	# Codex #446 F2: một giao dịch đã gắn cho nguồn bất kỳ (mọi vendor) thì
	# không đưa cho nguồn khác nữa. Shinhan không có mẫu nội dung, lọc theo
	# vendor sẽ để Shinhan "thấy tiền về" bằng giao dịch của Payoo cùng số.
	for r in frappe.get_all(DT_NGUON, filters={"name": ["!=", nguon.name],
			"giao_dich_ngan_hang": ["is", "set"], "den_ngay": [">=", frappe.utils.add_days(goc, -60)]},
			pluck="giao_dich_ngan_hang"):
		da_dung.update(x for x in (r or "").split("\n") if x)
	co_tien_mat = bool(frappe.db.count(DT_DONG, {"nguon": nguon.name, "mo_ta": ["like", "%tiền mặt"]}))
	tt, ds, ghi = khop.khop_ngan_hang(nguon.mau, int(round(nguon.thuc_nhan)), str(tu), str(den), gd, da_dung,
		ly_do_tay=khop.ly_do_khong_tu_nhan(nguon.mau, co_tien_mat))
	# Codex #450: chỉ khi khớp đúng một giao dịch mới ghi vào giao_dich_ngan_hang
	# (trường này là danh sách giao dịch đã dùng cho mọi nguồn khác). Gợi ý của
	# "Lệch tiền về" nằm trong ghi chú.
	nguon.db_set({"trang_thai_tien": tt, "giao_dich_ngan_hang": "\n".join(ds) if tt == khop.GIU_GIAO_DICH else ""})
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
	ncc = _ncc_theo_mau(nguon.mau)
	hd_ky = _hoa_don_ky(nguon, ncc)
	for d in dong:
		if d.loai not in ("chuyen", "phi_quan_ly", "dieu_chinh"):
			continue
		cap = {"van_don": None, "purchase_invoice": None}
		v = vd.get(d.ma_su_kien) or vd.get(d.ma_don)
		if v:
			cap["van_don"] = v
		if d.hoa_don_nguon and co_hd and "#" in d.hoa_don_nguon:
			ky, so = d.hoa_don_nguon.split("#", 1)
			# Codex #450: chỉ hoá đơn mua của đúng người bán (số hoá đơn không
			# duy nhất giữa các người bán). Chưa có nhà cung cấp mang MST thì
			# không đoán, để dòng thiếu hoá đơn mua.
			loc = dict({"docstatus": ["<", 2], "company": nguon.company, "custom_hddt_so": ["in", [so, so.lstrip("0")]],
				"supplier": ["in", ncc or [""]]}, **_loc_pi_con_hieu_luc(pi_meta))
			ung = frappe.get_all("Purchase Invoice", filters=loc, fields=["name", "grand_total"] + (
				["custom_hddt_ky_hieu"] if pi_meta.has_field("custom_hddt_ky_hieu") else []), limit_page_length=5)
			ung = [u for u in ung if not u.get("custom_hddt_ky_hieu") or ky.endswith(u.custom_hddt_ky_hieu) or u.custom_hddt_ky_hieu.endswith(ky[-6:])]
			if len(ung) == 1:
				cap["purchase_invoice"] = ung[0].name
		cap["trang_thai_khop"], cap["ghi_chu_khop"] = khop.chung_tu_chuyen(
			d.giao_hang, d.hoa_don_nguon, cap["van_don"], cap["purchase_invoice"], hd_ky)
		frappe.db.set_value(DT_DONG, d.name, cap, update_modified=False)


def _hoa_don_ky(nguon, ncc):
	"""Nguồn xuất một hoá đơn cả kỳ (Be, Xanh SM): tìm hoá đơn mua của đúng
	người bán, cùng tổng tiền, sau kỳ. Trả None nếu nguồn không theo kiểu này,
	ngược lại dict(pi, nhieu) dùng cho chung_tu_chuyen; ghi kèm vào nguồn để
	màn chi tiết hiện."""
	if nguon.mau not in KY_MOT_HOA_DON:
		return None
	hop = []
	if nguon.den_ngay and nguon.thuc_nhan:
		pi = frappe.get_all("Purchase Invoice", filters=dict({"docstatus": ["<", 2], "company": nguon.company, "supplier": ["in", ncc or [""]],
			"posting_date": ["between", [nguon.tu_ngay, frappe.utils.add_days(nguon.den_ngay, 40)]]},
			**_loc_pi_con_hieu_luc(frappe.get_meta("Purchase Invoice"))),
			fields=["name", "grand_total"], limit_page_length=50)
		hop = [p.name for p in pi if int(round(p.grand_total or 0)) == int(round(nguon.thuc_nhan))]
	_ghi_them(nguon.name, hoa_don_ky=hop, hoa_don_ky_ghi_chu=(
		"Hoá đơn mua cùng tổng tiền: " + ", ".join(hop)) if hop else "Chưa thấy hoá đơn mua cùng tổng tiền của kỳ.")
	return dict(pi=hop[0] if len(hop) == 1 else None, nhieu=hop)


# Nguồn chuyến đi xuất MỘT hoá đơn cho cả kỳ (không có số hoá đơn từng chuyến).
KY_MOT_HOA_DON = ("be", "xanh_taxi")


def _loc_pi_con_hieu_luc(pi_meta):
	"""Codex #450: hoá đơn mua huỷ mềm (chung_tu.danh_dau_huy: vẫn nháp, vgb_huy=1)
	không phải chứng từ. Một chỗ cho mọi lần tìm hoá đơn mua của chuyến đi."""
	return {"vgb_huy": 0} if pi_meta.has_field("vgb_huy") else {}


def _ncc_theo_mau(mau):
	mst = khop.MST_NCC.get(mau)
	return frappe.get_all("Supplier", filters={"tax_id": mst}, pluck="name") if mst else []


def _ky_the(nguon):
	"""Dựng phương trình số dư thẻ với sao kê kỳ trước cùng tài khoản."""
	d = json.loads(nguon.du_lieu or "{}")
	truoc = frappe.get_all(DT_NGUON, filters={"mau": nguon.mau, "tai_khoan": nguon.tai_khoan, "company": nguon.company,
		"den_ngay": ["<", nguon.tu_ngay], "name": ["!=", nguon.name]}, fields=["du_lieu"],
		order_by="den_ngay desc", limit_page_length=1)
	tong_truoc = json.loads(truoc[0].du_lieu or "{}").get("tong") if truoc else None
	_ghi_them(nguon.name, ky_the=khop.ky_the(d.get("tong"), tong_truoc))


def _tong_hop(nguon):
	"""Biên bản tháng OnePay: so tổng biên bản với các thông báo ngày đã nhận."""
	d = json.loads(nguon.du_lieu or "{}")
	kenh = (d.get("them") or {}).get("kenh") or ""
	tien = frappe.db.sql("""select coalesce(sum(tien_hang),0), coalesce(sum(phi),0), coalesce(sum(thuc_nhan),0), count(*)
		from `tab%s` where vendor='OnePay' and company=%%s and ma_su_kien like %%s and ngay_tien_ve between %%s and %%s
		and trang_thai_khop!=%%s""" % DT_DONG,
		(nguon.company, "%s:%%" % kenh, nguon.tu_ngay, frappe.utils.add_days(nguon.den_ngay, 5), khop.DA_THAY))[0]
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

	ct = _cong_ty_xem()
	# Codex #450: số trên thẻ, chip nhóm, chip nguồn đếm trong CÙNG phạm vi với
	# danh sách (pháp nhân, kỳ, ô tìm), chỉ bỏ đúng tầng chip đó ra: thẻ trạng
	# thái giữ nhóm và nguồn đang chọn, chip nhóm bỏ nhóm và nguồn, chip nguồn
	# bỏ nguồn. Bấm thẻ nào thì danh sách ra đúng số trên thẻ đó.
	loc_chung = {"company": ["in", ct]}
	a, b = khoang_ky(ky, frappe.utils.nowdate(), tu, den)
	if a or b:
		loc_chung["den_ngay"] = ["between", [a or "2000-01-01", b or "2100-12-31"]]
	or_loc = None
	if tim:
		t = "%%%s%%" % tim.strip()
		or_loc = [["ten_tep", "like", t], ["vendor", "like", t], ["name", "like", t], ["tai_khoan", "like", t]]
	loc = dict(loc_chung)
	if nhom:
		loc["nhom"] = nhom
	if vendor:
		loc["vendor"] = vendor
	loc.update(loc_trang_thai(trang_thai))
	trang = int(trang or 0)
	hang = frappe.get_all(DT_NGUON, filters=loc, or_filters=or_loc, fields=["name", "nhom", "vendor", "ten_mau",
		"tu_ngay", "den_ngay", "ngay_tien_ve", "trang_thai", "trang_thai_tien", "thuc_nhan", "so_dong", "so_moi",
		"so_trung", "so_loi", "so_da_noi", "so_chua_noi", "kenh_nhan", "ten_tep", "creation"],
		order_by="coalesce(den_ngay, creation) desc, creation desc", start=trang * 50, page_length=51)
	tat_ca = frappe.get_all(DT_NGUON, filters=loc_chung, or_filters=or_loc,
		fields=["nhom", "vendor", "trang_thai", "trang_thai_tien", "so_chua_noi", "thuc_nhan"], limit_page_length=0)
	dem, dem_vendor = dem_nguon(tat_ca, nhom, vendor)
	return dict(hang=hang[:50], con=len(hang) > 50, dem=dem, vendor=sorted(dem_vendor.keys() - {"tat_ca"}),
		dem_vendor=dem_vendor, tong=tong_tien(tat_ca, nhom, vendor, trang_thai))


def loc_trang_thai(trang_thai):
	"""Bộ lọc của một khoá trạng thái (thẻ hay chip). THUẦN. Cùng nghĩa với dem_nguon."""
	if trang_thai == "Cần xử lý":
		return {"trang_thai": ["in", ["Cần xử lý", "Lỗi tệp"]]}
	if trang_thai == khop.NHOM_CHO_TIEN:
		# Codex #450: thẻ "Chờ tiền về" đếm cả ba trạng thái chờ thì bấm vào
		# cũng lọc đủ ba, không chỉ một.
		return {"trang_thai_tien": ["in", list(khop.CHO_TIEN_VE)]}
	if trang_thai in khop.CHO_TIEN_VE:
		return {"trang_thai_tien": trang_thai}
	if trang_thai == "Chưa nối đủ":
		return {"so_chua_noi": [">", 0]}
	return {}


def khop_loc(r, loc):
	"""Một nguồn có thuộc bộ lọc kiểu Frappe không. THUẦN (các dạng ds dùng)."""
	for k, v in loc.items():
		x = r.get(k)
		if isinstance(v, list):
			if v[0] == "in" and x not in v[1]:
				return False
			if v[0] == ">" and not ((x or 0) > v[1]):
				return False
		elif x != v:
			return False
	return True


def tong_tien(rows, nhom=None, vendor=None, trang_thai=None):
	"""Codex #450: thẻ tóm tắt có tổng thực nhận theo nhóm/nguồn đang chọn, và
	"Tổng theo bộ lọc" khi đang lọc trạng thái. THUẦN, cùng bộ lọc với danh sách."""
	loc = {}
	if nhom:
		loc["nhom"] = nhom
	if vendor:
		loc["vendor"] = vendor
	chung = [r for r in rows if khop_loc(r, loc)]
	ra = dict(tat_ca=sum(float(r.get("thuc_nhan") or 0) for r in chung))
	loc_tt = loc_trang_thai(trang_thai)
	if loc_tt:
		ra["theo_loc"] = sum(float(r.get("thuc_nhan") or 0) for r in chung if khop_loc(r, loc_tt))
	return ra


def dem_nguon(rows, nhom=None, vendor=None):
	"""Đếm cho thẻ và chip. THUẦN. rows là mọi nguồn trong phạm vi chung
	(pháp nhân, kỳ, ô tìm). Trả (dem, dem_vendor)."""
	dem, dem_vendor = {}, {}
	for r in rows:
		nh, vd = r.get("nhom") or "", r.get("vendor") or ""
		dem["nhom:" + nh] = dem.get("nhom:" + nh, 0) + 1
		if (nhom or "Tiền bán") == nh:
			dem_vendor[vd] = dem_vendor.get(vd, 0) + 1
		if (nhom and nh != nhom) or (vendor and vd != vendor):
			continue
		dem["tat_ca"] = dem.get("tat_ca", 0) + 1
		if r.get("trang_thai") in ("Cần xử lý", "Lỗi tệp"):
			dem["Cần xử lý"] = dem.get("Cần xử lý", 0) + 1
		ttt = r.get("trang_thai_tien")
		if ttt in khop.CHO_TIEN_VE:
			dem[ttt] = dem.get(ttt, 0) + 1
			dem[khop.NHOM_CHO_TIEN] = dem.get(khop.NHOM_CHO_TIEN, 0) + 1
		if (r.get("so_chua_noi") or 0) > 0:
			dem["Chưa nối đủ"] = dem.get("Chưa nối đủ", 0) + 1
	dem_vendor["tat_ca"] = sum(dem_vendor.values())
	return dem, dem_vendor


@frappe.whitelist()
def chi_tiet(name=None, loc=None, trang=0):
	_chan()
	n = frappe.get_doc(DT_NGUON, name)
	_chan_cong_ty(n.company)
	d = json.loads(n.du_lieu or "{}")
	f = {"nguon": name}
	if loc == "chua_noi":
		f["trang_thai_khop"] = ["not in", list(khop.KHONG_TINH_CHUA_NOI)]
	elif loc == "da_noi":
		f["trang_thai_khop"] = ["in", list(khop.DA_NOI)]
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
	return frappe.get_all(DT_DONG, filters={"sales_invoice": si, "company": ["in", _cong_ty_xem()],
		"trang_thai_khop": ["!=", khop.DA_THAY]}, fields=["name", "nguon", "vendor", "ngay",
		"ma_don", "tien_hang", "giam_gia", "phi", "thuc_nhan", "trang_thai_khop", "ghi_chu_khop", "ngay_tien_ve"])


@frappe.whitelist()
def suc_khoe():
	"""Mỗi nguồn: lần nhận gần nhất, kỳ mới nhất, số nguồn cần xử lý, số chưa
	thấy tiền về. Nguồn chưa từng nhận hiện "Chưa có", không hiện số 0."""
	_chan()
	ra = []
	ct = _cong_ty_xem()
	for vendor, nhom in [(t, n) for _k, _a, _b, t, n in mau_bc.MAU]:
		r = frappe.db.sql("""select max(den_ngay), max(creation), sum(trang_thai in ('Cần xử lý','Lỗi tệp')),
			sum(trang_thai_tien in %%(cho)s), count(*) from `tab%s`
			where vendor=%%(v)s and company in %%(ct)s""" % DT_NGUON, dict(v=vendor, ct=ct, cho=khop.CHO_TIEN_VE))[0]
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


def _byte_tep(ten_file):
	byte = frappe.get_doc("File", ten_file).get_content()
	return byte.encode("utf-8") if isinstance(byte, str) else byte


def xu_ly_thu(comm):
	ket = []
	sot = []  # đính kèm có tệp chưa nhận ra mẫu hoặc đọc lỗi
	for f in frappe.get_all("File", filters={"attached_to_doctype": "Communication", "attached_to_name": comm},
			fields=["name", "file_name", "file_url"]):
		if not (f.file_name or "").lower().endswith(DUOI):
			continue
		try:
			bo_qua = []
			ket.extend(_nhan_byte(f.file_name, _byte_tep(f.name), "Email", file_url=f.file_url,
				communication=comm, chi_mau_quen=True, bo_qua=bo_qua))
			if bo_qua:
				sot.append((f, set(bo_qua)))
		except Exception:
			frappe.db.rollback()
			frappe.log_error(title="Đối soát vendor: đọc đính kèm %s" % f.file_name)
	c = None
	if sot or not ket:
		c = frappe.db.get_value("Communication", comm, ["subject", "content", "sender"], as_dict=True)
	# Codex #450: thư đã chắc là thư báo cáo (có tệp nhận ra mẫu, hoặc tiêu
	# đề/thân thư nói là báo cáo) thì mọi đính kèm đọc lỗi hay chưa có mẫu đều
	# hiện ở Cần xử lý, không lặng lẽ bỏ. Thư quảng cáo không có tệp nào nhận
	# ra mẫu thì vẫn bỏ qua như cũ. Đi lại đúng một lối _nhan_byte: tệp con đã
	# nhận ở lượt đầu dừng ở mã băm, chỉ tệp con bị bỏ qua được ghi thêm.
	if sot and (ket or (c and thu_co_bao_cao(c.subject, c.content))):
		for f, ten_bo_qua in sot:
			try:
				# Chỉ lấy tệp con đã bị bỏ qua (tệp con đã nhận ở lượt đầu không
				# lặp lại). Tệp con lỗi đã ghi từ lượt quét trước trả da_co, vẫn
				# tính vào ket để không sinh thêm nguồn "thân thư" thừa.
				ket.extend(r for r in _nhan_byte(f.file_name, _byte_tep(f.name), "Email", file_url=f.file_url,
					communication=comm, doc_lai=False) if r.get("ten_tep") in ten_bo_qua)
			except Exception:
				frappe.db.rollback()
				frappe.log_error(title="Đối soát vendor: ghi đính kèm chưa có mẫu %s" % f.file_name)
	if not ket and c and thu_co_bao_cao(c.subject, c.content):
		ket.extend(_ghi_thu_khong_tep(comm, c))
	return ket


def _ghi_thu_khong_tep(comm, c):
	"""Thư báo cáo không có tệp đọc được (báo cáo nằm trong thân thư hoặc tệp
	chưa có mẫu): lưu một nguồn "Lỗi tệp" có lý do, để hiện ở Cần xử lý."""
	with khoa_doi_chieu():
		cong_ty = _cong_ty()
		sha = tep_doc.bam(("than-thu:" + comm).encode("utf-8"))
		if frappe.db.exists(DT_NGUON, {"sha256": sha}):
			return []
		kq = mau_bc.ket_qua("", "", vendor_theo_thu(c.sender), "")
		kq["loi"].append("Thư báo cáo của vendor không có tệp đọc được (báo cáo nằm trong thân thư hoặc tệp chưa có mẫu). "
			"Tải bản CSV hoặc Excel gốc từ cổng vendor rồi bấm Tải file.")
		t = dict(ten=(c.subject or "Thư vendor không có tệp")[:140], sha256=sha, loai="")
		return [_ghi_nguon(cong_ty, t, kq, khop.xem_truoc(kq, cong_ty), "Email", None, comm)]


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
