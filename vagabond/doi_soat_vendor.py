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
# Codex #450 vòng 14: sự kiện một nguồn có trong báo cáo nhưng đã nhận ở nguồn
# khác (không ghi lại thành dòng). Giữ để tổng của bất kỳ tập nguồn nào cũng
# đúng phần các báo cáo đó thể hiện, mỗi sự kiện một lần.
DT_TRUNG = "Vagabond Doi Soat Trung"
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


def _cong_ty_demo():
	"""Pháp nhân demo ERPNext tự dựng lúc cài (Global Defaults). Site thật
	07/10/2026 có "The Vagabond (Demo)" nằm cạnh pháp nhân thật.
	Lỗi đọc thì NÉM RA (Codex #452): nuốt thành "" thì hộp thư khai pháp nhân
	demo bị coi là pháp nhân thật và thư vendor ghi nhầm vào đó."""
	return frappe.db.get_single_value("Global Defaults", "demo_company") or ""


def bo_demo(tat_ca, demo, mac_dinh):
	"""THUẦN. v585: bỏ pháp nhân demo khỏi danh sách được xem và được nhận tệp,
	trừ khi nó là pháp nhân mặc định hoặc là pháp nhân duy nhất."""
	if not demo or demo == mac_dinh or not (set(tat_ca) - {demo}):
		return list(tat_ca)
	return [c for c in tat_ca if c != demo]


def _cong_ty_xem():
	"""Codex #446 H1: các pháp nhân người đang dùng được xem (theo User
	Permission của Company). Mọi danh sách, đếm và chi tiết đối soát lọc theo
	đây; không có pháp nhân nào thì trả [""] để truy vấn ra rỗng."""
	from frappe.permissions import get_user_permissions

	tat_ca = bo_demo(frappe.get_all("Company", pluck="name"), _cong_ty_demo(),
		frappe.defaults.get_global_default("company"))
	duoc = {x.get("doc") for x in (get_user_permissions(frappe.session.user).get("Company") or [])}
	return chon_cong_ty(tat_ca, duoc)


def chon_cong_ty(tat_ca, duoc):
	"""THUẦN. Không có User Permission Company thì xem tất cả; có thì chỉ các
	pháp nhân được cấp. Rỗng trả [""] để truy vấn `in` ra rỗng chứ không lỗi."""
	return [c for c in tat_ca if not duoc or c in duoc] or [""]


def _chan_cong_ty(cong_ty):
	if cong_ty not in _cong_ty_xem():
		frappe.throw("Nguồn đối soát này thuộc pháp nhân anh/chị chưa được xem.", frappe.PermissionError)


def cong_ty_nhan(gui, duoc):
	"""THUẦN. Codex #450 vòng 16: pháp nhân nhận tệp tải tay phải rõ ràng,
	không lặng lẽ lấy pháp nhân mặc định của site. duoc là các pháp nhân người
	dùng được xem. Có gửi thì phải nằm trong đó; không gửi thì chỉ tự chọn khi
	người dùng có đúng một pháp nhân. Trả (pháp nhân, lời báo, lỗi quyền?)."""
	duoc = [c for c in duoc if c]
	gui = (gui or "").strip()
	if not duoc:
		return "", "Tài khoản chưa được cấp pháp nhân nào. Báo anh Việt cấp quyền pháp nhân.", True
	if gui:
		if gui in duoc:
			return gui, "", False
		return "", "Pháp nhân này anh/chị chưa được xem. Chọn lại pháp nhân nhận tệp.", True
	if len(duoc) == 1:
		return duoc[0], "", False
	return "", "Chọn pháp nhân nhận tệp trước khi xem trước hay nhận.", False


_TIEN_TO_CONG_TY = re.compile(r"^\s*(chi nhánh\s+)?(công ty|cty)\s+(tnhh|cổ phần|cp)?\s*(một thành viên|mtv)?\s*", re.I)
TOI_DA_NHAN_CHIP = 16


def nhan_ngan_cong_ty(ds):
	"""THUẦN. Codex #450 vòng 17: nhãn chip pháp nhân tối đa 16 ký tự, không
	trùng nhau (AGENTS.md mục 18). ds: [(tên đầy đủ, viết tắt)]. Bỏ tiền tố
	chung "CÔNG TY TNHH ..."; phần còn lại vừa 16 ký tự thì dùng, không thì
	dùng viết tắt của Company. Nhãn trùng nhau thì đổi sang viết tắt. Tên đầy
	đủ vẫn là giá trị gửi lên và nằm trong title của chip."""
	def cat(x):
		x = (x or "").strip()
		return x if len(x) <= TOI_DA_NHAN_CHIP else x[:TOI_DA_NHAN_CHIP - 1] + "…"

	ra = {}
	for ten, viet_tat in ds:
		gon = _TIEN_TO_CONG_TY.sub("", ten or "").strip()
		ra[ten] = gon if gon and len(gon) <= TOI_DA_NHAN_CHIP else cat(viet_tat or gon or ten)
	vt = dict(ds)
	# Vòng 18: đổi sang viết tắt có thể đụng nhãn của pháp nhân khác, nên đếm
	# lại sau mỗi lượt đổi cho tới khi không còn gì đổi được.
	for _ in range(len(ra)):
		dem = {}
		for v in ra.values():
			dem[v] = dem.get(v, 0) + 1
		doi = False
		for ten in ra:
			if dem[ra[ten]] > 1 and vt.get(ten) and cat(vt[ten]) != ra[ten]:
				ra[ten] = cat(vt[ten])
				doi = True
		if not doi:
			break
	# Còn trùng (viết tắt cũng trùng hoặc không có): thêm số thứ tự theo thứ tự
	# danh sách, vẫn trong 16 ký tự, không đụng nhãn nào khác.
	da = set()
	for ten, _vt in ds:
		nhan = ra[ten]
		if nhan in da:
			khac = set(ra.values())
			k = 2
			while True:
				duoi = " " + str(k)
				thu = nhan[:TOI_DA_NHAN_CHIP - len(duoi)].rstrip("… ") + duoi
				if thu not in da and thu not in khac:
					break
				k += 1
			nhan = ra[ten] = thu
		da.add(nhan)
	return ra


def _cong_ty_nhan(gui):
	ct, loi, quyen = cong_ty_nhan(gui, _cong_ty_xem())
	if loi:
		frappe.throw(loi, frappe.PermissionError if quyen else frappe.ValidationError)
	return ct


def tep_da_co(da, cong_ty, doc_lai=True):
	"""THUẦN. da: nguồn cùng mã băm (có name, trang_thai, company) hoặc None.
	Mã băm là duy nhất trên cả site, nên tệp đã nhận vào pháp nhân KHÁC thì
	không nhận lại, cũng không đọc lại vào nguồn của pháp nhân kia (Codex #450
	vòng 16). Trả "moi", "doc_lai", "da_co" hoặc "phap_nhan_khac"."""
	if not da:
		return "moi"
	lay = da.get if isinstance(da, dict) else (lambda k: getattr(da, k, None))
	if lay("company") != cong_ty:
		return "phap_nhan_khac"
	if doc_lai and khop.doc_lai_duoc(lay("trang_thai")):
		return "doc_lai"
	return "da_co"


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
	"""Codex #450 vòng 16: chỉ đọc tệp do CHÍNH người đang dùng tải lên (lối
	tai_len cất tệp riêng tư, chủ là người tải). Không nhận đường dẫn tệp riêng
	tư của người khác dù biết đường dẫn. Tệp trùng nội dung dùng chung đường
	dẫn nhưng mỗi người tải có bản ghi File của mình, nên lọc chủ vẫn tìm ra."""
	ten = frappe.db.get_value("File", {"file_url": file_url, "owner": frappe.session.user}, "name") if file_url else None
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
def xem_truoc(file_url=None, cong_ty=None):
	"""Đọc tệp và nói sẽ nhận gì vào pháp nhân đã chọn; không ghi gì."""
	_chan()
	cong_ty = _cong_ty_nhan(cong_ty)
	ten, byte = _doc_file(file_url)
	ra = []
	for t, kq, xt in _doc_va_xem(ten, byte, cong_ty):
		tt = tom_tat(kq, xt)
		tt["ten_tep"] = t["ten"]
		da = frappe.db.get_value(DT_NGUON, {"sha256": t["sha256"]}, ["name", "trang_thai", "company"], as_dict=True)
		kieu = tep_da_co(da, cong_ty)
		tt["da_co"] = da.name if kieu == "da_co" else ""
		tt["doc_lai"] = da.name if kieu == "doc_lai" else ""
		tt["phap_nhan_khac"] = 1 if kieu == "phap_nhan_khac" else 0
		tt["cong_ty"] = cong_ty
		ra.append(tt)
	return ra


@frappe.whitelist()
def nhan(file_url=None, cong_ty=None):
	"""Nhận tệp đã xem trước vào pháp nhân đã chọn: đọc lại ở máy chủ (không
	tin số máy khách gửi)."""
	_chan(True)
	cong_ty = _cong_ty_nhan(cong_ty)
	ten, byte = _doc_file(file_url)
	return _nhan_byte(ten, byte, "Tải tay", file_url=file_url, cong_ty=cong_ty)


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


def _nhan_byte(ten, byte, kenh, file_url=None, communication=None, chi_mau_quen=False, bo_qua=None, doc_lai=True,
		cong_ty=None):
	"""bo_qua: nếu là list, ghi tên tệp con bị bỏ qua vì chưa nhận ra mẫu
	hay đọc lỗi (chỉ khi chi_mau_quen), để xu_ly_thu quyết có ghi lại không.
	doc_lai=False: nguồn đã có thì dừng ở mã băm kể cả khi đang lỗi (lượt
	quét thư mỗi giờ không ghi lại mãi một tệp chưa có mẫu).
	cong_ty: tải tay luôn gửi pháp nhân đã kiểm quyền; thư tự đến (không có
	người dùng) mới lấy pháp nhân mặc định của site."""
	with khoa_doi_chieu():
		cong_ty = cong_ty or _cong_ty()
		ket = []
		for t, kq, xt in _doc_va_xem(ten, byte, cong_ty):
			if chi_mau_quen and not kq["mau"]:
				if bo_qua is not None:
					bo_qua.append(t["ten"])
				continue
			da = frappe.db.get_value(DT_NGUON, {"sha256": t["sha256"]}, ["name", "trang_thai", "company"], as_dict=True)
			kieu = tep_da_co(da, cong_ty, doc_lai)
			if kieu == "phap_nhan_khac":
				# Không lộ tên nguồn của pháp nhân kia, không ghi gì.
				ket.append(dict(name="", trang_thai="", da_co=1, phap_nhan_khac=1, ten_tep=t["ten"]))
				continue
			if kieu == "da_co":
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
	# Quan hệ "có trong báo cáo" của bản đọc cũ là dữ liệu dẫn xuất, dựng lại
	# ngay từ bản đọc mới.
	frappe.db.delete(DT_TRUNG, {"nguon": name})
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
				for x in xt["dong"] if x["trang_thai"] == "loi"][:300], lan_doc_truoc=lich_su or None,
			ban_sua=khop.ban_sua(xt, kq["nhom"], kq["vendor"], kq["tai_khoan"]) or None),
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
	trung = [x["dong"] for x in xt["dong"] if x["trang_thai"] == "trung"]
	for x in xt["dong"]:
		if x["trang_thai"] != "moi":
			continue
		d = x["dong"]
		frappe.db.savepoint("ds_dong")
		try:
			_chen_dong(nguon.name, cong_ty, kq["nhom"], kq["vendor"], kq["tai_khoan"], d)
		except frappe.DuplicateEntryError:
			# Nguồn khác vừa nhận cùng sự kiện giữa lúc xem trước và lúc ghi.
			frappe.db.rollback(save_point="ds_dong")
			trung_ve_sau += 1
			trung.append(d)
	_ghi_trung(nguon.name, cong_ty, [(d["khoa"], d["thuc_nhan"]) for d in trung])
	if trung_ve_sau:
		nguon.db_set({"so_moi": so["moi"] - trung_ve_sau, "so_trung": so["trung"] + trung_ve_sau})
	_doi_chieu(nguon.name)
	return dict(name=nguon.name, trang_thai=nguon.trang_thai, da_co=0, ten_tep=t["ten"])


def _chen_dong(ten_nguon, cong_ty, nhom, vendor, tai_khoan, d):
	"""Ghi một dòng sự kiện đang hiệu lực. Dùng chung cho lượt nhận tệp và
	"Dùng bản sửa", để hai lối ghi cùng một bộ trường."""
	dong = frappe.get_doc(dict(
		doctype=DT_DONG, nguon=ten_nguon, company=cong_ty, nhom=nhom, vendor=vendor,
		tai_khoan=tai_khoan, khoa=d["khoa"], dau_noi_dung=d["dau_noi_dung"],
		ma_su_kien=(d["ma_su_kien"] or "")[:140], ngay=d["ngay"] or None, gio=d.get("gio"),
		ngay_tien_ve=d.get("ngay_tien_ve") or None, loai=d["loai"], merchant=(d.get("merchant") or "")[:140],
		diem_ban=d.get("diem_ban"), ma_don=(d.get("ma_don") or "")[:140], ma_tham_chieu=(d.get("ma_tham_chieu") or "")[:140],
		ma_can_cu=(d.get("ma_can_cu") or "")[:140], hoa_don_nguon=(d.get("hoa_don") or "")[:140],
		mo_ta=(d.get("mo_ta") or "")[:140], nguoi=(d.get("nguoi") or "")[:140], giao_hang=1 if d.get("giao_hang") else 0,
		tien_hang=d["tien_hang"], giam_gia=d.get("giam_gia") or 0, phi=d.get("phi") or 0, dieu_chinh=d.get("dieu_chinh") or 0,
		thue=d.get("thue") or 0, thuc_nhan=d["thuc_nhan"], trang_thai_khop="Chưa nối"))
	dong.insert(ignore_permissions=True, ignore_links=True)
	return dong


def _ghi_trung(ten_nguon, cong_ty, cap):
	"""Ghi quan hệ nguồn có sự kiện đã nhận ở nguồn khác: cap là [(khoá, tiền)]."""
	if not cap:
		return
	luc, ai = frappe.utils.now(), frappe.session.user
	frappe.db.bulk_insert(DT_TRUNG, ["name", "creation", "modified", "owner", "modified_by", "docstatus",
		"nguon", "company", "khoa", "thuc_nhan"],
		[(frappe.generate_hash(length=12), luc, luc, ai, ai, 0, ten_nguon, cong_ty, k, t) for k, t in cap])


def nguon_sau_ban_sua(nguon, du_lieu, khoa_dung, tien):
	"""Số đếm, tiền và trạng thái của nguồn sau khi một dòng xung đột được
	dùng. THUẦN. tien là {tien_hang, phi, thuc_nhan} của dòng đó."""
	e = next(x for x in du_lieu.get("ban_sua") or [] if x["khoa"] == khoa_dung)
	dong_loi = [x for x in du_lieu.get("dong_loi") or [] if x.get("vi_tri") != e["vi_tri"]]
	so_loi = max(int(nguon.get("so_loi") or 0) - 1, 0)
	ra = dict(so_loi=so_loi, so_moi=int(nguon.get("so_moi") or 0) + 1,
		tien_hang=float(nguon.get("tien_hang") or 0) + float(tien.get("tien_hang") or 0),
		phi=float(nguon.get("phi") or 0) + float(tien.get("phi") or 0),
		thuc_nhan=float(nguon.get("thuc_nhan") or 0) + float(tien.get("thuc_nhan") or 0))
	if nguon.get("trang_thai") == "Cần xử lý" and not so_loi and not (du_lieu.get("loi") or []):
		ra.update(trang_thai="Đã nhận", ly_do="")
	elif so_loi:
		ra["ly_do"] = (("%s dòng lỗi. " % so_loi) + "; ".join((du_lieu.get("loi") or [])[:5]))[:1000]
	return ra, dong_loi


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


@frappe.whitelist()
def dung_ban_sua(name=None, khoa=None, dau_cu=None):
	"""Codex #450 vòng 14: vendor gửi lại một sự kiện đã nhận với nội dung khác
	(Grab đổi thẻ/ví thành tiền mặt). Kế toán bấm "Dùng bản sửa": dòng cũ thôi
	hiệu lực (Đã thay, giữ nguyên để tra), bản sửa thành dòng hiệu lực của nguồn
	này, rồi đối chiếu lại cả hai nguồn. Không tạo chứng từ.

	dau_cu: dấu nội dung của bản đang tính mà màn hình đã cho kế toán so
	(Codex #450 vòng 15). Trong lúc đó phiên khác có thể đã dùng một bản sửa
	khác cho cùng sự kiện; dấu không còn khớp thì chặn, bắt tải lại để so."""
	_chan(True)
	n0 = frappe.db.get_value(DT_NGUON, name, ["name", "company"], as_dict=True)
	if not n0 or not khoa:
		frappe.throw("Không thấy nguồn đối soát này. Tải lại màn hình.")
	_chan_cong_ty(n0.company)
	with khoa_doi_chieu():
		nguon = frappe.get_doc(DT_NGUON, name)
		du_lieu = json.loads(nguon.du_lieu or "{}")
		e = next((x for x in du_lieu.get("ban_sua") or [] if x["khoa"] == khoa and not x.get("da_dung")), None)
		if not e:
			frappe.throw("Bản sửa này không còn chờ xác nhận. Tải lại màn hình.")
		d = e["dong"]
		cu = frappe.db.get_value(DT_DONG, {"khoa": khoa}, ["name", "nguon", "dau_noi_dung", "thuc_nhan"], as_dict=True)
		if cu and cu.dau_noi_dung == d["dau_noi_dung"]:
			frappe.throw("Sự kiện này đã mang đúng nội dung bản sửa. Tải lại màn hình.")
		if (cu.dau_noi_dung if cu else "") != (dau_cu or ""):
			frappe.throw("Bản đang tính của sự kiện này vừa đổi (có thể đã dùng một bản sửa khác). Tải lại màn hình để so lại.")
		luc = frappe.utils.now()
		if cu:
			frappe.db.sql("""update `tab%s` set khoa_cu=khoa, khoa=concat('thay:', name), nguon_cu=nguon, nguon=NULL,
				trang_thai_khop=%%s, thay_luc=%%s where name=%%s""" % DT_DONG, (khop.DA_THAY, luc, cu.name))
			if cu.nguon and cu.nguon != name:
				# Báo cáo cũ vẫn có sự kiện này (bản trước khi sửa) trong tổng của nó.
				_ghi_trung(cu.nguon, nguon.company, [(khoa, cu.thuc_nhan)])
		moi = _chen_dong(name, nguon.company, e["nhom"], e["vendor"], e["tai_khoan"], d)
		if cu:
			frappe.db.set_value(DT_DONG, cu.name, {"thay_bang": moi.name, "ghi_chu_khop": "Thay bằng bản sửa ở nguồn %s." % name},
				update_modified=False)
		so, dong_loi = nguon_sau_ban_sua(nguon.as_dict(), du_lieu, khoa, d)
		e.update(da_dung=1, luc=str(luc), boi=frappe.session.user, thay=cu.name if cu else "")
		du_lieu["dong_loi"] = dong_loi
		nguon.db_set(dict(so, du_lieu=json.dumps(du_lieu, ensure_ascii=False, default=str)))
		_doi_chieu(name)
		if cu and cu.nguon and cu.nguon != name:
			_doi_chieu(cu.nguon)
	return dict(ok=1, nguon=name)


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
	bi_thay = bool(frappe.db.count(DT_DONG, {"nguon_cu": nguon.name, "thay_bang": ["is", "set"]}))
	tt, ds, ghi = khop.khop_ngan_hang(nguon.mau, int(round(nguon.thuc_nhan)), str(tu), str(den), gd, da_dung,
		ly_do_tay=khop.ly_do_khong_tu_nhan(nguon.mau, co_tien_mat, bi_thay))
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
		# v584: Frappe v16 chỉ nhận tên trường trong order_by của get_all, không
		# nhận hàm (coalesce làm màn Đối soát lỗi 417 trên site thật). Nguồn
		# chưa đọc ra kỳ (den_ngay trống) xếp cuối; chip Cần xử lý vẫn lọc ra.
		order_by="den_ngay desc, creation desc", start=trang * 50, page_length=51)
	tat_ca = frappe.get_all(DT_NGUON, filters=loc_chung, or_filters=or_loc,
		fields=["name", "nhom", "vendor", "trang_thai", "trang_thai_tien", "so_chua_noi", "thuc_nhan"], limit_page_length=0)
	dem, dem_vendor = dem_nguon(tat_ca, nhom, vendor)
	# Codex #450 vòng 16: các pháp nhân được nhận tệp tải tay (màn Tải file
	# hiện chip chọn khi có từ hai pháp nhân trở lên).
	return dict(hang=hang[:50], con=len(hang) > 50, dem=dem, vendor=sorted(dem_vendor.keys() - {"tat_ca"}),
		dem_vendor=dem_vendor, tong=tong_tien(tat_ca, nhom, vendor, trang_thai, _tong_duy_nhat),
		cong_ty_nhan=[c for c in ct if c],
		nhan_cong_ty=nhan_ngan_cong_ty([(c.name, c.abbr) for c in frappe.get_all("Company",
			filters={"name": ["in", [c for c in ct if c] or [""]]}, fields=["name", "abbr"])]))


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


def _tong_duy_nhat(ten):
	"""Tổng thực nhận của tập nguồn ten, mỗi sự kiện một lần (Codex #450 vòng
	14). Cùng nghĩa với khop.tong_duy_nhat: dòng hiệu lực của các nguồn trong
	tập, cộng sự kiện các nguồn đó có trong báo cáo nhưng dòng hiệu lực nằm
	ở nguồn ngoài tập (hoặc đã thôi hiệu lực)."""
	if not ten:
		return 0.0
	t = frappe.db.sql("""select coalesce(sum(x.t), 0) from (
			select d.thuc_nhan t from `tab%(dong)s` d where d.nguon in %%(n)s
			union all
			select max(m.thuc_nhan) t from `tab%(trung)s` m where m.nguon in %%(n)s
				and not exists (select 1 from `tab%(dong)s` d2 where d2.khoa = m.khoa and d2.nguon in %%(n)s)
			group by m.khoa) x""" % dict(dong=DT_DONG, trung=DT_TRUNG), {"n": tuple(ten)})
	return float(t[0][0] or 0)


def tong_tien(rows, nhom=None, vendor=None, trang_thai=None, tinh=None):
	"""Codex #450: thẻ tóm tắt có tổng thực nhận theo nhóm/nguồn đang chọn, và
	"Tổng theo bộ lọc" khi đang lọc trạng thái. THUẦN, cùng bộ lọc với danh sách.

	Vòng 14: tinh(tên các nguồn) trả tổng mỗi sự kiện một lần trên ĐÚNG tập
	nguồn đang thấy (báo cáo ngày và tháng chồng nhau không cộng hai lần, chỉ
	thấy báo cáo tháng thì vẫn ra đủ tổng báo cáo tháng)."""
	loc = {}
	if nhom:
		loc["nhom"] = nhom
	if vendor:
		loc["vendor"] = vendor
	chung = [r for r in rows if khop_loc(r, loc)]
	ra = dict(tat_ca=float(tinh([r["name"] for r in chung])))
	loc_tt = loc_trang_thai(trang_thai)
	if loc_tt:
		ra["theo_loc"] = float(tinh([r["name"] for r in chung if khop_loc(r, loc_tt)]))
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
			hoa_don_ky=d.get("hoa_don_ky_ghi_chu") or "", ghi_chu_don_vi=d.get("ghi_chu_don_vi") or "",
			ban_sua=_ban_sua_cho(d)),
		dong=dong[:100], con=len(dong) > 100)


def _ban_sua_cho(du_lieu):
	"""Bản sửa còn chờ kế toán chọn, kèm nội dung đang hiệu lực để so."""
	ra = []
	for e in [x for x in du_lieu.get("ban_sua") or [] if not x.get("da_dung")][:50]:
		cu = frappe.db.get_value(DT_DONG, {"khoa": e["khoa"]}, ["nguon", "mo_ta", "thuc_nhan", "ngay", "dau_noi_dung"],
			as_dict=True) or {}
		d = e["dong"]
		ra.append(dict(khoa=e["khoa"], vi_tri=e["vi_tri"], ma=d.get("ma_don") or d.get("ma_su_kien"), ngay=d.get("ngay"),
			dau_cu=cu.get("dau_noi_dung") or "",
			moi=dict(mo_ta=d.get("mo_ta") or "", thuc_nhan=d.get("thuc_nhan")),
			cu=dict(nguon=cu.get("nguon") or "", mo_ta=cu.get("mo_ta") or "", thuc_nhan=cu.get("thuc_nhan")) if cu else None))
	return ra


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
	try:
		cong_ty = _cong_ty_cua_thu(comm)
	except Exception:
		# Codex #452: đọc hộp thư lỗi thì KHÔNG đoán pháp nhân mặc định (ghi
		# sai pháp nhân không ai biết). Ghi log và bỏ lượt này; lượt quét mỗi
		# giờ đọc lại thư trong 2 ngày nên thư sẽ được thử lại.
		frappe.log_error(title="Đối soát vendor: không đọc được pháp nhân của hộp thư nhận %s" % comm)
		return ket
	sot = []  # đính kèm có tệp chưa nhận ra mẫu hoặc đọc lỗi
	for f in frappe.get_all("File", filters={"attached_to_doctype": "Communication", "attached_to_name": comm},
			fields=["name", "file_name", "file_url"]):
		if not (f.file_name or "").lower().endswith(DUOI):
			continue
		try:
			bo_qua = []
			ket.extend(_nhan_byte(f.file_name, _byte_tep(f.name), "Email", file_url=f.file_url,
				communication=comm, chi_mau_quen=True, bo_qua=bo_qua, cong_ty=cong_ty))
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
					communication=comm, doc_lai=False, cong_ty=cong_ty) if r.get("ten_tep") in ten_bo_qua)
			except Exception:
				frappe.db.rollback()
				frappe.log_error(title="Đối soát vendor: ghi đính kèm chưa có mẫu %s" % f.file_name)
	if not ket and c and thu_co_bao_cao(c.subject, c.content):
		ket.extend(_ghi_thu_khong_tep(comm, c, cong_ty))
	return ket


def cong_ty_thu(cua_hop_thu, mac_dinh, demo):
	"""THUẦN. v585: thư vendor vào pháp nhân của hộp thư nhận (ô Công ty trên
	Email Account); hộp thư chưa khai hoặc khai pháp nhân demo thì về pháp
	nhân mặc định của site như trước."""
	if cua_hop_thu and cua_hop_thu != demo:
		return cua_hop_thu
	return mac_dinh


def _cong_ty_cua_thu(comm):
	"""Lỗi đọc thì NÉM RA cho xu_ly_thu ghi log; chỉ hộp thư đọc được mà chưa
	khai hoặc khai demo mới về pháp nhân mặc định.
	Codex #452: lấy Communication.company TRƯỚC (ERPNext ghi pháp nhân của hộp
	thư lúc NHẬN thư, chỉ đọc), để quản trị đổi pháp nhân của hộp thư sau đó
	thì báo cáo cũ quét lại vẫn vào đúng pháp nhân cũ. Thư cũ chưa có ô này
	mới đọc pháp nhân hiện tại của hộp thư."""
	thu = frappe.db.get_value("Communication", comm, ["company", "email_account"], as_dict=True) or {}
	ct = thu.get("company")
	if not ct and thu.get("email_account"):
		ct = frappe.db.get_value("Email Account", thu.get("email_account"), "company")
	if ct and not frappe.db.exists("Company", ct):
		ct = None
	return cong_ty_thu(ct, _cong_ty(), _cong_ty_demo())


def _ghi_thu_khong_tep(comm, c, cong_ty=None):
	"""Thư báo cáo không có tệp đọc được (báo cáo nằm trong thân thư hoặc tệp
	chưa có mẫu): lưu một nguồn "Lỗi tệp" có lý do, để hiện ở Cần xử lý."""
	with khoa_doi_chieu():
		cong_ty = cong_ty or _cong_ty()
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
