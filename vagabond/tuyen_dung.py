# -*- coding: utf-8 -*-
"""Phân hệ Tuyển dụng (v622).

Anh Việt 30/10/2026, sau bản đề xuất đối chiếu Greenhouse, Workstream, Base,
MISA AMIS (project doc de-xuat-phan-he-tuyen-dung-30-10-2026):

  1. Làm ngay trong app Vagabond, không cài HRMS.
  2. Mọi quản lý bộ phận xem hồ sơ ứng viên và chốt nhận người.
  3. (TopCV: soạn email hỏi, kết nối API làm sau khi TopCV trả lời.)
  4. Ứng viên BẮT BUỘC tích đồng ý lưu hồ sơ khi nộp.
  5. Buổi làm thử ở bếp và quầy CÓ trả công.
  6. Mục Tuyển dụng trên web lấy thẳng từ app: bật, tắt vị trí trên app là web
     đổi theo, giống ưu đãi (v589). Ứng viên bấm "Ứng tuyển" mở form /ung-tuyen
     ghi thẳng vào app, không còn mở email.

Bài học gốc của lao động theo ca (Workstream, HigherMe): người tốt nộp nhiều nơi
cùng lúc, ai gọi lại trước thì giữ được người. Nên phân hệ đo và báo đúng một
thứ trước tiên: hồ sơ nào quá 24 giờ chưa ai liên hệ.

Dữ liệu cá nhân (Luật Bảo vệ dữ liệu cá nhân 2025, hiệu lực 01/01/2026): chỉ
hỏi thông tin phục vụ tuyển dụng; hết hạn lưu đã ghi trong câu đồng ý thì máy
xoá thông tin cá nhân của người KHÔNG được nhận, giữ lại dòng trống tên để
thống kê theo kênh (QT-20: không xoá cứng dòng nghiệp vụ).
"""

# ------------------------------------------------------------------ phần thuần

import json
import re
from datetime import datetime, timedelta

VT = "Vagabond Vi Tri Tuyen"
UV = "Vagabond Ung Vien"

HINH_THUC = ("Toàn thời gian", "Bán thời gian", "Thời vụ", "Thực tập")
CA_RANH = ("Sáng", "Chiều", "Tối", "Cuối tuần", "Linh hoạt")
NGUON = ("Web Vagabond", "QR tại cửa hàng", "TopCV", "Trang việc làm khác", "Facebook, Zalo",
	"Người quen giới thiệu", "Đến trực tiếp")
NGUON_WEB = ("Web Vagabond", "QR tại cửa hàng")

# Trạng thái một lượt ứng tuyển. Mã lưu chính là chữ hiển thị.
MOI, LIEN_HE, HEN_PV, LAM_THU, DE_NGHI, NHAN_VIEC, DUNG = (
	"Mới nhận", "Đã liên hệ", "Hẹn phỏng vấn", "Làm thử", "Đề nghị nhận việc", "Đã nhận việc", "Dừng")
TRANG_THAI = (MOI, LIEN_HE, HEN_PV, LAM_THU, DE_NGHI, NHAN_VIEC, DUNG)
# Trạng thái cần ngày giờ hẹn (ứng viên phải biết tới lúc nào).
CAN_HEN = (HEN_PV, LAM_THU)
LY_DO_DUNG = ("Không phù hợp", "Ứng viên rút", "Không liên lạc được", "Đã đủ người")
VONG = ("Phỏng vấn", "Làm thử")
KET_LUAN = ("Nên nhận", "Cân nhắc", "Không nên nhận")

GIO_GOI_LAI = 24
THANG_LUU = 12
# Tiêu chí mặc định khi vị trí chưa khai, theo nhóm việc. Anh Việt sửa ở màn vị trí.
TIEU_CHI_MAC_DINH = ("Thái độ, giao tiếp", "Nhanh nhẹn, chịu được giờ cao điểm",
	"Ca rảnh khớp lịch tiệm", "Vệ sinh, an toàn thực phẩm")
TOI_DA_TIEU_CHI = 8

CAU_DONG_Y = ("Tôi đồng ý để Công ty TNHH Patisserie Vagabond dùng thông tin trên cho việc tuyển dụng "
	"và lưu hồ sơ trong %d tháng để liên hệ khi có vị trí phù hợp. Tôi có thể yêu cầu xoá hồ sơ bất cứ "
	"lúc nào." % THANG_LUU)


class LoiNhap(ValueError):
	"""Dữ liệu người dùng gửi lên không hợp lệ; câu lỗi đọc được, nói việc làm tiếp."""


def chuan_sdt(s):
	"""THUẦN: '+84 909.123.456' -> '0909123456'. '' nếu không phải số di động VN."""
	x = re.sub(r"[\s.()+-]", "", str(s or ""))
	if x.startswith("84"):
		x = "0" + x[2:]
	return x if re.fullmatch(r"0[35789]\d{8}", x) else ""


def _chu(v, toi_da, ten):
	v = re.sub(r"[ \t]+", " ", str(v or "")).strip()
	if len(v) > toi_da:
		raise LoiNhap("%s tối đa %s ký tự." % (ten, "{:,}".format(toi_da).replace(",", ".")))
	return v


def chuan_ca(ds):
	"""THUẦN: danh sách ca rảnh -> chuỗi gọn theo đúng thứ tự CA_RANH. Bỏ giá trị lạ."""
	if isinstance(ds, str):
		ds = [x.strip() for x in ds.split(",")]
	chon = set(ds or [])
	return ", ".join(c for c in CA_RANH if c in chon)


def chuan_ho_so(du_lieu, vi_tri_mo, nguon_mac_dinh="Web Vagabond"):
	"""THUẦN: dữ liệu form ứng tuyển -> dict sạch để ghi.

	vi_tri_mo: tập tên các vị trí đang nhận hồ sơ. Ứng viên chỉ nộp được vào
	vị trí đang mở; vị trí vừa tắt thì báo để chọn vị trí khác.
	Bắt buộc tích đồng ý (anh Việt 30/10/2026: bắt ứng viên tích giữ hồ sơ)."""
	if isinstance(du_lieu, str):
		if len(du_lieu) > 8000:
			raise LoiNhap("Hồ sơ quá dài. Rút ngắn phần giới thiệu rồi gửi lại.")
		try:
			du_lieu = json.loads(du_lieu)
		except ValueError:
			raise LoiNhap("Không đọc được hồ sơ. Tải lại trang rồi gửi lại.")
	if not isinstance(du_lieu, dict):
		raise LoiNhap("Không đọc được hồ sơ. Tải lại trang rồi gửi lại.")
	vt = str(du_lieu.get("vi_tri") or "").strip()
	if not vt or vt not in set(vi_tri_mo or ()):
		raise LoiNhap("Vị trí này đã ngừng nhận hồ sơ. Chọn một vị trí khác đang tuyển.")
	ten = _chu(du_lieu.get("ho_ten"), 120, "Họ tên")
	if len(ten) < 2:
		raise LoiNhap("Điền họ tên của bạn.")
	sdt = chuan_sdt(du_lieu.get("sdt"))
	if not sdt:
		raise LoiNhap("Điền số điện thoại di động Việt Nam, ví dụ 0909 123 456.")
	email = _chu(du_lieu.get("email"), 140, "Email")
	if email and not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]{2,}", email):
		raise LoiNhap("Kiểm tra lại email, ví dụ ten@gmail.com, hoặc để trống.")
	cv = _chu(du_lieu.get("lien_ket_cv"), 500, "Đường dẫn CV")
	if cv and not re.fullmatch(r"https://[^\s<>\"']+", cv):
		raise LoiNhap("Đường dẫn CV phải bắt đầu bằng https://, ví dụ link Google Drive hoặc TopCV.")
	nguon = str(du_lieu.get("nguon") or nguon_mac_dinh).strip()
	if nguon not in NGUON:
		nguon = nguon_mac_dinh
	if not du_lieu.get("dong_y") in (True, 1, "1", "true"):
		raise LoiNhap("Tích ô đồng ý lưu hồ sơ để gửi. Chúng tôi chỉ dùng thông tin này cho việc tuyển dụng.")
	return {
		"vi_tri": vt, "ho_ten": ten, "sdt": sdt, "email": email,
		"khu_vuc": _chu(du_lieu.get("khu_vuc"), 120, "Khu vực đang ở"),
		"ca_ranh": chuan_ca(du_lieu.get("ca_ranh")),
		"kinh_nghiem": _chu(du_lieu.get("kinh_nghiem"), 1500, "Kinh nghiệm"),
		"gioi_thieu": _chu(du_lieu.get("gioi_thieu"), 1500, "Lời nhắn"),
		"lien_ket_cv": cv, "nguon": nguon,
		"nguoi_gioi_thieu": _chu(du_lieu.get("nguoi_gioi_thieu"), 120, "Người giới thiệu"),
		"dong_y": 1,
	}


def han_luu(luc, thang=THANG_LUU):
	"""THUẦN: ngày hết hạn lưu hồ sơ, tính từ lúc đồng ý (cộng tròn tháng, ngày 31 lùi về cuối tháng)."""
	d = luc.date() if isinstance(luc, datetime) else luc
	m = d.month - 1 + int(thang)
	nam, thang_moi = d.year + m // 12, m % 12 + 1
	for ngay in (d.day, 30, 29, 28):
		try:
			return d.replace(year=nam, month=thang_moi, day=ngay)
		except ValueError:
			continue


def con_mo(vt, hom_nay):
	"""THUẦN: vị trí còn nhận hồ sơ không (bật Đang tuyển và chưa qua hạn)."""
	if not int(vt.get("dang_tuyen") or 0):
		return False
	kt = str(vt.get("ket_thuc") or "")[:10]
	return not (kt and kt < str(hom_nay)[:10])


def the_web(vt, hom_nay):
	"""THUẦN: một vị trí trên app -> một thẻ tuyển dụng đúng định dạng trang khách
	(chuyen-muc.js và web Vue cùng đọc). None khi vị trí không được hiện."""
	if not con_mo(vt, hom_nay):
		return None
	yc = [x.strip() for x in str(vt.get("yeu_cau") or "").splitlines() if x.strip()]
	if str(vt.get("muc_luong") or "").strip():
		yc.insert(0, "Mức lương: " + str(vt["muc_luong"]).strip())
	nhom = str(vt.get("ten_bo_phan") or "").strip() or "Cửa hàng"
	return {
		"id": "erp-td-" + str(vt.get("name")),
		"loai": "tuyen_dung", "vi_tri": "tuyen_dung", "hien": True, "nguon": "erp",
		"tieu_de": vt.get("tieu_de") or vt.get("name"),
		"noi_dung": str(vt.get("noi_dung") or "").strip(),
		"yeu_cau": "\n".join(yc),
		"noi_lam": str(vt.get("noi_lam") or "").strip(),
		"hinh_thuc": vt.get("hinh_thuc") or "",
		"ket_thuc": str(vt.get("ket_thuc") or "")[:10],
		"nhom": nhom,
		"anh": "", "email": "",
		"lien_ket": "/ung-tuyen?vt=" + str(vt.get("name")),
		"nut": "Ứng tuyển vị trí này",
	}


def trang_thai_web(vt, hom_nay):
	"""THUẦN: câu trạng thái của vị trí cho trình biên tập web và màn app."""
	if not int(vt.get("dang_tuyen") or 0):
		return "Đang tắt trên app, khách không thấy"
	if not con_mo(vt, hom_nay):
		return "Đã hết hạn nhận hồ sơ, khách không thấy"
	return "Khách đang thấy"


def tieu_chi_cua(vt):
	"""THUẦN: danh sách tiêu chí chấm của một vị trí (mỗi dòng một tiêu chí)."""
	ds = []
	for x in str((vt or {}).get("tieu_chi") or "").splitlines():
		x = x.strip(" -\t")
		if x and x not in ds:
			ds.append(x[:80])
	return ds[:TOI_DA_TIEU_CHI] or list(TIEU_CHI_MAC_DINH)


def chuan_vi_tri(du_lieu):
	"""THUẦN: form vị trí trên app -> dict sạch."""
	if isinstance(du_lieu, str):
		du_lieu = json.loads(du_lieu or "{}")
	if not isinstance(du_lieu, dict):
		raise LoiNhap("Không đọc được vị trí. Tải lại màn rồi lưu lại.")
	ten = _chu(du_lieu.get("tieu_de"), 140, "Tên vị trí")
	if len(ten) < 3:
		raise LoiNhap("Điền tên vị trí, ví dụ Thu ngân ca tối hoặc Phụ bếp Pastry.")
	ht = str(du_lieu.get("hinh_thuc") or HINH_THUC[0])
	if ht not in HINH_THUC:
		raise LoiNhap("Chọn hình thức làm việc trong danh sách.")
	kt = str(du_lieu.get("ket_thuc") or "").strip()[:10]
	if kt:
		try:
			datetime.strptime(kt, "%Y-%m-%d")
		except ValueError:
			raise LoiNhap("Hạn nhận hồ sơ không hợp lệ. Chọn lại ngày hoặc để trống.")
	try:
		so = du_lieu.get("so_can")
		so_can = 1 if so is None or str(so).strip() == "" else int(so)
		cong = int(float(str(du_lieu.get("cong_lam_thu") or 0).replace(".", "").replace(",", "")))
		gio = float(str(du_lieu.get("gio_lam_thu") or 0).replace(",", "."))
	except (TypeError, ValueError):
		raise LoiNhap("Số người cần, giờ làm thử và tiền công làm thử phải là số.")
	if not 1 <= so_can <= 50:
		raise LoiNhap("Số người cần từ 1 đến 50.")
	if cong < 0 or gio < 0 or gio > 12:
		raise LoiNhap("Giờ làm thử từ 0 đến 12, tiền công không âm.")
	tc = tieu_chi_cua({"tieu_chi": du_lieu.get("tieu_chi")}) if str(du_lieu.get("tieu_chi") or "").strip() else []
	return {
		"tieu_de": ten,
		"bo_phan": str(du_lieu.get("bo_phan") or "").strip(),
		"noi_lam": _chu(du_lieu.get("noi_lam"), 140, "Nơi làm"),
		"hinh_thuc": ht, "so_can": so_can,
		"dang_tuyen": 1 if du_lieu.get("dang_tuyen") in (True, 1, "1", "true") else 0,
		"ket_thuc": kt or None,
		"noi_dung": _chu(du_lieu.get("noi_dung"), 2000, "Mô tả công việc"),
		"yeu_cau": "\n".join(x.strip() for x in str(du_lieu.get("yeu_cau") or "").splitlines() if x.strip())[:3000],
		"muc_luong": _chu(du_lieu.get("muc_luong"), 140, "Mức lương"),
		"tieu_chi": "\n".join(tc),
		"cong_lam_thu": cong, "gio_lam_thu": gio,
	}


def kiem_chuyen(cu, moi, lich_hen=None, ly_do=None):
	"""THUẦN: câu lỗi nếu không chuyển được trạng thái, '' nếu được.

	Quản lý được đi tới và lùi (hẹn lại, gọi lại), trừ hai điều: người đã nhận
	việc không quay lại vòng tuyển; dừng thì phải có lý do; hẹn thì phải có giờ."""
	if moi not in TRANG_THAI:
		return "Chọn trạng thái trong danh sách."
	if cu == NHAN_VIEC and moi != NHAN_VIEC:
		return "Ứng viên đã nhận việc. Có thay đổi thì ghi chú, không đưa lại về vòng tuyển."
	if moi in CAN_HEN and not lich_hen:
		return "Chọn ngày giờ hẹn %s để ứng viên biết lúc nào tới." % ("phỏng vấn" if moi == HEN_PV else "làm thử")
	if moi == DUNG and len(re.sub(r"\s+", " ", str(ly_do or "")).strip()) < 3:
		return "Chọn lý do dừng để sau này còn biết vì sao."
	return ""


def qua_han_goi(row, bay_gio, gio=GIO_GOI_LAI):
	"""THUẦN: hồ sơ còn Mới nhận mà đã nộp quá `gio` giờ."""
	if row.get("trang_thai") != MOI:
		return False
	luc = row.get("creation")
	if isinstance(luc, str):
		try:
			luc = datetime.strptime(luc[:19], "%Y-%m-%d %H:%M:%S")
		except ValueError:
			return False
	return bool(luc) and luc <= bay_gio - timedelta(hours=gio)


def diem_tb(diem):
	"""THUẦN: điểm trung bình (1 tới 4) của một phiếu chấm, bỏ ô chưa chấm."""
	so = []
	for v in (diem or {}).values():
		try:
			n = int(v)
		except (TypeError, ValueError):
			continue
		if 1 <= n <= 4:
			so.append(n)
	return round(sum(so) / len(so), 2) if so else 0


def chuan_phieu_cham(tieu_chi, diem, ket_luan, vong):
	"""THUẦN: kiểm một phiếu chấm. Trả dict điểm theo đúng danh sách tiêu chí."""
	if vong not in VONG:
		raise LoiNhap("Chọn vòng chấm: Phỏng vấn hay Làm thử.")
	if ket_luan not in KET_LUAN:
		raise LoiNhap("Chọn kết luận: Nên nhận, Cân nhắc hay Không nên nhận.")
	if isinstance(diem, str):
		diem = json.loads(diem or "{}")
	ra = {}
	for t in tieu_chi:
		v = (diem or {}).get(t)
		try:
			v = int(v)
		except (TypeError, ValueError):
			v = 0
		if not 1 <= v <= 4:
			raise LoiNhap("Chấm đủ các tiêu chí (1 đến 4 điểm), còn thiếu: %s." % t)
		ra[t] = v
	return ra


def an_danh(row):
	"""THUẦN: giá trị ghi đè khi hết hạn lưu. Giữ vị trí, nguồn, trạng thái, ngày
	để thống kê kênh; xoá mọi thông tin nhận ra được người."""
	return {
		"ho_ten": "Hồ sơ đã xoá theo hạn lưu", "sdt": "", "email": "", "khu_vuc": "",
		"kinh_nghiem": "", "gioi_thieu": "", "lien_ket_cv": "", "nguoi_gioi_thieu": "",
		"ca_ranh": "", "nhat_ky": "", "da_an_danh": 1,
	}


def can_xoa(row, hom_nay):
	"""THUẦN: hồ sơ đã tới hạn xoá chưa. Người đã nhận việc chuyển sang hồ sơ
	nhân viên nên không xoá ở đây."""
	if int(row.get("da_an_danh") or 0) or row.get("trang_thai") == NHAN_VIEC:
		return False
	h = str(row.get("han_luu") or "")[:10]
	return bool(h) and h < str(hom_nay)[:10]


def tom_tat(rows, hom_nay, bay_gio):
	"""THUẦN: ba con số đầu màn: mới chưa gọi (và số quá 24 giờ), hẹn hôm nay,
	công làm thử chưa trả."""
	moi = [r for r in rows if r.get("trang_thai") == MOI]
	return {
		"moi": len(moi),
		"qua_han": len([r for r in moi if qua_han_goi(r, bay_gio)]),
		"hen_hom_nay": len([r for r in rows if r.get("trang_thai") in CAN_HEN
			and str(r.get("lich_hen") or "")[:10] == str(hom_nay)[:10]]),
		"cong_chua_tra": len([r for r in rows if float(r.get("tien_cong_thu") or 0) > 0
			and not int(r.get("da_tra_cong") or 0)]),
	}


def soan_tin_moi(r):
	"""THUẦN: (tiêu đề, dòng) tin Zalo khi có hồ sơ mới."""
	dong = ["%s · %s" % (r.get("ho_ten"), r.get("sdt")),
		"Vị trí: %s" % (r.get("ten_vi_tri") or r.get("vi_tri"))]
	phu = [x for x in (r.get("ca_ranh") and "Ca rảnh: " + r["ca_ranh"], r.get("khu_vuc") and "Ở " + r["khu_vuc"]) if x]
	if phu:
		dong.append(" · ".join(phu))
	dong.append("Nguồn: %s%s" % (r.get("nguon") or "Web Vagabond",
		(", giới thiệu bởi " + r["nguoi_gioi_thieu"]) if r.get("nguoi_gioi_thieu") else ""))
	dong.append("Gọi lại trong %d giờ, rồi cập nhật trên app: Nhân sự, Tuyển dụng." % GIO_GOI_LAI)
	return "Hồ sơ ứng tuyển mới", dong


def soan_tin_qua_han(r, bay_gio):
	"""THUẦN: (tiêu đề, dòng) tin nhắc hồ sơ quá 24 giờ chưa liên hệ."""
	luc = r.get("creation")
	if isinstance(luc, str):
		luc = datetime.strptime(luc[:19], "%Y-%m-%d %H:%M:%S")
	gio = int((bay_gio - luc).total_seconds() // 3600) if luc else GIO_GOI_LAI
	return "Hồ sơ quá %d giờ chưa ai gọi" % GIO_GOI_LAI, [
		"%s · %s" % (r.get("ho_ten"), r.get("sdt")),
		"Vị trí: %s · nộp cách đây %d giờ" % (r.get("ten_vi_tri") or r.get("vi_tri"), gio),
		"Người tốt nộp nhiều nơi cùng lúc. Gọi ngay rồi bấm Cập nhật trên app.",
	]


# ------------------------------------------------------------------ chạm Frappe

import frappe  # noqa: E402

try:
	from frappe.rate_limiter import rate_limit
except Exception:  # bản Frappe giả của ca kiểm
	def rate_limit(**k):
		return lambda f: f

# Anh Việt 30/10/2026: "tất cả các bạn quản lý bộ phận". Lấy đúng các vai của
# những gói chức vụ bậc quản lý trong nguoi_dung.GOI (Quản lý cửa hàng, Quản lý
# sản xuất, Kho, Thu mua, Kế toán, Giám đốc), cộng vai riêng "VGB - Tuyển dụng"
# để anh gán thêm người khác mà không phải cho cả gói quản lý.
VAI_TUYEN_DUNG = "VGB - Tuyển dụng"
QUYEN_TUYEN_DUNG = (
	"System Manager", "Giám đốc", "AP Giám đốc",
	"VGB - Quản lý cửa hàng", "Manufacturing Manager", "Stock Manager",
	"Purchase Manager", "Thu mua", "Accounts Manager", VAI_TUYEN_DUNG,
)


def co_quyen():
	return bool(set(QUYEN_TUYEN_DUNG) & set(frappe.get_roles()))


def _kiem_quyen():
	if not co_quyen():
		frappe.throw("Phân hệ Tuyển dụng chỉ mở cho quản lý các bộ phận và giám đốc. Cần dùng thì báo anh Việt "
			"gán chức vụ VGB - Tuyển dụng trong màn Quản lý người dùng.", frappe.PermissionError)


def _hom_nay():
	return str(frappe.utils.nowdate())


def _ten_bo_phan(bp):
	from vagabond.bo_phan_nguoi import ten_ngan_bo_phan
	return ten_ngan_bo_phan(bp)


TRUONG_VT = ["name", "tieu_de", "bo_phan", "noi_lam", "hinh_thuc", "so_can", "dang_tuyen", "ket_thuc",
	"noi_dung", "yeu_cau", "muc_luong", "tieu_chi", "cong_lam_thu", "gio_lam_thu", "modified"]


def _ds_vi_tri():
	rows = frappe.get_all(VT, fields=TRUONG_VT, order_by="dang_tuyen desc, modified desc", limit_page_length=200)
	for r in rows:
		r["ten_bo_phan"] = _ten_bo_phan(r.get("bo_phan"))
		r["ket_thuc"] = str(r.get("ket_thuc") or "")
	return rows


def the_web_dang_hien():
	"""Các thẻ tuyển dụng trang khách đang hiện (noi_dung_web.cong_khai gọi)."""
	hn = _hom_nay()
	return [t for t in (the_web(r, hn) for r in _ds_vi_tri()) if t]


def ds_web_bien_tap():
	"""Cho trình biên tập web: mọi vị trí kèm trạng thái, chỉ xem."""
	hn = _hom_nay()
	ra = []
	for r in _ds_vi_tri():
		the = the_web(dict(r, dang_tuyen=1, ket_thuc=""), hn)
		the["ket_thuc"] = r.get("ket_thuc") or ""
		thay = the_web(r, hn) is not None
		ra.append(dict(the, ma_vi_tri=r["name"], khach_thay=1 if thay else 0, trang_thai_erp=trang_thai_web(r, hn)))
	return ra


def _noi_lam_mau():
	"""Nơi làm gợi ý: các điểm bán có quầy, cộng xưởng sản xuất."""
	ra = []
	try:
		from vagabond import diem_ban
		for d in diem_ban.ds(chi_bat=True):
			if d.get("quay") and d.get("ten") and d["ten"] not in ra:
				ra.append(d["ten"])
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tuyen_dung: doc diem ban")
	ra.append("Xưởng sản xuất Tân Bình")
	return ra


# ------------------------------------------------------------------ trang khách


@frappe.whitelist(allow_guest=True)
def vi_tri_cong_khai():
	"""Trang /ung-tuyen: vị trí đang nhận hồ sơ và câu đồng ý. Không trả dữ liệu ứng viên."""
	return {"vi_tri": the_web_dang_hien(), "ca_ranh": list(CA_RANH), "cau_dong_y": CAU_DONG_Y,
		"thang_luu": THANG_LUU}


def _bam(chuoi):
	import hashlib
	return hashlib.sha256(chuoi.encode()).hexdigest()


@frappe.whitelist(methods=["POST"], allow_guest=True)
@rate_limit(limit=5, seconds=600)
def ung_tuyen(du_lieu, ma_lan_gui):
	"""Ứng viên gửi hồ sơ từ /ung-tuyen. Gửi lại cùng mã thì trả kết quả cũ, không
	tạo hồ sơ thứ hai (mất mạng giữa chừng, bấm Gửi lại) - khuôn dat_ban.gui."""
	if not isinstance(ma_lan_gui, str) or not re.fullmatch(r"[a-f0-9-]{36}", ma_lan_gui):
		frappe.throw("Tải lại trang để bắt đầu nộp hồ sơ.")
	try:
		raw = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
		chuoi = json.dumps(raw, sort_keys=True, ensure_ascii=False)
		if not isinstance(raw, dict) or len(chuoi) > 8000:
			raise ValueError("Hồ sơ quá dài hoặc không hợp lệ.")
	except (TypeError, ValueError) as e:
		frappe.throw(str(e))
	# Ô bẫy: người thật không thấy ô này, máy tự điền thì bỏ qua im lặng.
	if str(raw.get("web") or "").strip():
		return {"ok": 1, "ma": "OK"}
	khoa = _bam(ma_lan_gui)
	cu = frappe.db.get_value(UV, {"bam_lan_gui": khoa}, ["name", "bam_noi_dung"], as_dict=True)
	if cu:
		if cu.bam_noi_dung != _bam(chuoi):
			frappe.throw("Hồ sơ trước đã được nhận. Tải lại trang nếu muốn nộp vị trí khác.")
		return {"ok": 1, "ma": cu.name}
	hn = _hom_nay()
	mo = [r["name"] for r in _ds_vi_tri() if con_mo(r, hn)]
	try:
		nd = chuan_ho_so(raw, mo, "QR tại cửa hàng" if raw.get("nguon") == "QR tại cửa hàng" else "Web Vagabond")
	except LoiNhap as e:
		frappe.throw(str(e))
	luc = frappe.utils.now_datetime()
	d = frappe.get_doc(dict(nd, doctype=UV, trang_thai=MOI, dong_y_luc=luc, han_luu=str(han_luu(luc)),
		bam_lan_gui=khoa, bam_noi_dung=_bam(chuoi)))
	moc = "ung_tuyen_" + frappe.generate_hash(length=10)
	frappe.db.savepoint(moc)
	so_tb = len(frappe.local.message_log or [])
	try:
		d.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		frappe.db.rollback(save_point=moc)
		cu = frappe.db.get_value(UV, {"bam_lan_gui": khoa}, ["name", "bam_noi_dung"], as_dict=True, for_update=True)
		if not cu:
			raise
		del frappe.local.message_log[so_tb:]
		if cu.bam_noi_dung != _bam(chuoi):
			frappe.throw("Hồ sơ trước đã được nhận. Tải lại trang nếu muốn nộp vị trí khác.")
		return {"ok": 1, "ma": cu.name}
	return {"ok": 1, "ma": d.name}


def bao_moi(doc, method=None):
	"""Hook sau khi tạo hồ sơ: báo nhóm Zalo nhận tin Tuyển dụng. Lỗi Zalo không
	làm mất hồ sơ (kenh_zalo ghi sổ trong giao dịch, gửi sau commit)."""
	if getattr(frappe.flags, "vagabond_kiem_that", False):
		return
	from vagabond import kenh_zalo
	try:
		tieu_de, dong = soan_tin_moi(doc.as_dict())
	except Exception:
		frappe.log_error(title="Tuyển dụng: chưa soạn được tin Zalo", message="Hồ sơ %s." % doc.name)
		return
	kenh_zalo.bao_hoac_ghi_loi("viec", "tuyen_dung", tieu_de, dong, link=frappe.utils.get_url("/tuyen-dung"),
		khoa="ung-vien:%s" % doc.name, kiem="ung_vien_moi", nguon=doc.name, ma_tin="ns_ung_vien_moi")


def con_moi_nhan(ten):
	"""Tin việc hỏi lại ngay trước khi gửi: hồ sơ còn chưa ai liên hệ không."""
	return frappe.db.get_value(UV, ten, "trang_thai") == MOI


def nhac_qua_han():
	"""Mỗi giờ: hồ sơ còn Mới nhận quá 24 giờ, mỗi hồ sơ một tin (khoá chống trùng)."""
	try:
		from vagabond import kenh_zalo
		bay_gio = frappe.utils.now_datetime()
		rows = frappe.get_all(UV, filters={"trang_thai": MOI, "da_an_danh": 0,
			"creation": ["<=", bay_gio - timedelta(hours=GIO_GOI_LAI)]},
			fields=["name", "ho_ten", "sdt", "vi_tri", "ten_vi_tri", "creation", "trang_thai"], limit_page_length=200)
		for r in rows:
			if not qua_han_goi(r, bay_gio):
				continue
			tieu_de, dong = soan_tin_qua_han(r, bay_gio)
			kenh_zalo.bao("viec", "tuyen_dung", tieu_de, dong, link=frappe.utils.get_url("/tuyen-dung"),
				khoa="ung-vien-qua-han:%s" % r["name"], kiem="ung_vien_moi", nguon=r["name"],
				ma_tin="ns_ung_vien_qua_han")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tuyen_dung: nhac qua han")


def xoa_het_han():
	"""Hằng đêm: xoá thông tin cá nhân của hồ sơ không được nhận đã qua hạn lưu.
	Không xoá dòng (QT-20), chỉ ghi đè các ô nhận ra được người."""
	try:
		hn = _hom_nay()
		rows = frappe.get_all(UV, filters={"da_an_danh": 0, "han_luu": ["<", hn], "trang_thai": ["!=", NHAN_VIEC]},
			fields=["name", "trang_thai", "han_luu", "da_an_danh"], limit_page_length=500)
		for r in rows:
			if can_xoa(r, hn):
				frappe.db.set_value(UV, r["name"], an_danh(r), update_modified=False)
				# Bảng chấm giữ điểm số nhưng bỏ nhận xét chữ (có thể nhắc tên, đời tư).
				frappe.db.sql("update `tabVagabond Ung Vien Danh Gia` set nhan_xet='' where parent=%s", r["name"])
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tuyen_dung: xoa het han")


# ------------------------------------------------------------------ màn app


TRUONG_UV = ["name", "vi_tri", "ten_vi_tri", "ho_ten", "sdt", "email", "khu_vuc", "ca_ranh", "kinh_nghiem",
	"gioi_thieu", "lien_ket_cv", "nguon", "nguoi_gioi_thieu", "trang_thai", "ly_do_dung", "lich_hen",
	"lien_he_luc", "nhat_ky", "xu_ly_boi", "xu_ly_luc", "gio_lam_thu", "tien_cong_thu", "da_tra_cong",
	"tra_cong_boi", "tra_cong_luc", "han_luu", "creation", "da_an_danh"]


@frappe.whitelist()
def tong_quan():
	"""Dữ liệu màn Tuyển dụng: vị trí, hồ sơ 120 ngày gần nhất (kèm hồ sơ cũ còn
	đang xử lý), số đầu màn."""
	_kiem_quyen()
	hn = _hom_nay()
	bay_gio = frappe.utils.now_datetime()
	vt = _ds_vi_tri()
	moc = str((bay_gio - timedelta(days=120)).date())
	rows = frappe.get_all(UV, filters={"da_an_danh": 0}, or_filters={"creation": [">=", moc],
		"trang_thai": ["in", [MOI, LIEN_HE, HEN_PV, LAM_THU, DE_NGHI]]},
		fields=TRUONG_UV, order_by="creation desc", limit_page_length=500)
	ten_cham = {}
	if rows:
		for c in frappe.get_all("Vagabond Ung Vien Danh Gia", filters={"parent": ["in", [r["name"] for r in rows]],
				"parenttype": UV}, fields=["parent", "vong", "nguoi", "luc", "diem", "diem_tb", "ket_luan", "nhan_xet"],
				order_by="luc asc", limit_page_length=0):
			c["luc"] = str(c.get("luc") or "")
			ten_cham.setdefault(c["parent"], []).append(c)
	dem_sdt = {}
	for r in rows:
		dem_sdt[r["sdt"]] = dem_sdt.get(r["sdt"], 0) + 1
	for r in rows:
		r["creation"] = str(r.get("creation") or "")
		r["lich_hen"] = str(r.get("lich_hen") or "")
		r["lien_he_luc"] = str(r.get("lien_he_luc") or "")
		r["xu_ly_luc"] = str(r.get("xu_ly_luc") or "")
		r["tra_cong_luc"] = str(r.get("tra_cong_luc") or "")
		r["han_luu"] = str(r.get("han_luu") or "")
		r["qua_han"] = 1 if qua_han_goi(dict(r, creation=r["creation"]), bay_gio) else 0
		r["lan_nop"] = dem_sdt.get(r["sdt"], 1)
		r["cham"] = ten_cham.get(r["name"], [])
	so_hs = {}
	for r in rows:
		so_hs[r["vi_tri"]] = so_hs.get(r["vi_tri"], 0) + 1
	for v in vt:
		v["so_ho_so"] = so_hs.get(v["name"], 0)
		v["trang_thai_web"] = trang_thai_web(v, hn)
		v["khach_thay"] = 1 if con_mo(v, hn) else 0
		v["ds_tieu_chi"] = tieu_chi_cua(v)
	bo_phan = [{"k": d["name"], "ten": _ten_bo_phan(d["name"])} for d in frappe.get_all("Department",
		filters={"disabled": 0, "is_group": 0}, fields=["name"], order_by="name", limit_page_length=100)
		if d["name"] != "All Departments"]
	return {
		"vi_tri": vt, "rows": rows, "hom_nay": hn, "bay_gio": str(bay_gio)[:19],
		"tom_tat": tom_tat(rows, hn, bay_gio), "nguon": list(NGUON), "ly_do_dung": list(LY_DO_DUNG),
		"hinh_thuc": list(HINH_THUC), "ca_ranh": list(CA_RANH), "noi_lam": _noi_lam_mau(),
		"bo_phan": bo_phan, "tieu_chi_mac_dinh": list(TIEU_CHI_MAC_DINH), "cau_dong_y": CAU_DONG_Y,
		"gio_goi_lai": GIO_GOI_LAI, "thang_luu": THANG_LUU, "link_ung_tuyen": _link_ung_tuyen(),
	}


def _link_ung_tuyen():
	"""Địa chỉ form ứng tuyển trên miền khách (mã QR in ra giấy phải là miền khách,
	không phải miền app nội bộ, xem ten_mien.link_khach)."""
	try:
		from vagabond.ten_mien import link_khach
		return link_khach("/ung-tuyen")
	except Exception:
		return frappe.utils.get_url("/ung-tuyen")


@frappe.whitelist()
def dem_cho_goi():
	"""Số trên ô Tuyển dụng ở trang chủ: hồ sơ mới chưa ai liên hệ."""
	if not co_quyen():
		return {"so": 0}
	return {"so": frappe.db.count(UV, {"trang_thai": MOI, "da_an_danh": 0})}


def _ai():
	return frappe.utils.get_fullname(frappe.session.user) or frappe.session.user


def _ghi_vet(doc, cau):
	luc = frappe.utils.now_datetime()
	doc.nhat_ky = ((doc.nhat_ky or "").strip() + "\n%s %s: %s" % (luc.strftime("%H:%M %d/%m"), _ai(), cau)).strip()[-6000:]
	doc.xu_ly_boi = _ai()
	doc.xu_ly_luc = luc


@frappe.whitelist(methods=["POST"])
def luu_vi_tri(du_lieu, name=None):
	"""Tạo hoặc sửa một vị trí. Bật Đang tuyển là web hiện ngay."""
	_kiem_quyen()
	try:
		nd = chuan_vi_tri(du_lieu)
	except (LoiNhap, ValueError) as e:
		frappe.throw(str(e))
	if nd["bo_phan"] and not frappe.db.exists("Department", nd["bo_phan"]):
		frappe.throw("Bộ phận này không có trong danh mục. Chọn lại bộ phận.")
	if name:
		doc = frappe.get_doc(VT, name, for_update=True)
		doc.update(nd)
	else:
		doc = frappe.get_doc(dict(nd, doctype=VT))
	doc.flags.ignore_permissions = True
	doc.save() if name else doc.insert()
	return {"ok": 1, "name": doc.name}


@frappe.whitelist(methods=["POST"])
def bat_tat_vi_tri(name, bat):
	"""Công tắc Đang tuyển trên màn danh sách vị trí. Web đổi theo ngay."""
	_kiem_quyen()
	bat = 1 if str(bat) in ("1", "true", "True") else 0
	doc = frappe.get_doc(VT, name, for_update=True)
	if int(doc.dang_tuyen or 0) != bat:
		doc.dang_tuyen = bat
		doc.flags.ignore_permissions = True
		doc.save()
	return {"ok": 1, "dang_tuyen": bat, "trang_thai_web": trang_thai_web(doc.as_dict(), _hom_nay())}


@frappe.whitelist(methods=["POST"])
def them_ho_so(du_lieu):
	"""Quản lý thêm tay hồ sơ đến từ TopCV, trang việc làm khác, người quen, đến
	trực tiếp. Vẫn bắt xác nhận ứng viên đã đồng ý lưu hồ sơ."""
	_kiem_quyen()
	raw = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
	try:
		vt_co = [r["name"] for r in _ds_vi_tri()]
		nd = chuan_ho_so(raw, vt_co, "Đến trực tiếp")
	except LoiNhap as e:
		frappe.throw(str(e).replace("Tích ô đồng ý lưu hồ sơ để gửi. Chúng tôi chỉ dùng thông tin này cho việc tuyển dụng.",
			"Hỏi ứng viên đã đồng ý lưu hồ sơ chưa, rồi bật ô xác nhận."))
	luc = frappe.utils.now_datetime()
	doc = frappe.get_doc(dict(nd, doctype=UV, trang_thai=MOI, dong_y_luc=luc, han_luu=str(han_luu(luc))))
	_ghi_vet(doc, "Thêm hồ sơ tay, nguồn %s" % nd["nguon"])
	doc.insert(ignore_permissions=True)
	return {"ok": 1, "name": doc.name}


@frappe.whitelist(methods=["POST"])
def cap_nhat(name, trang_thai, lich_hen=None, ly_do=None, ghi_chu=None):
	"""Đổi trạng thái một hồ sơ, ghi vết ai làm lúc nào."""
	_kiem_quyen()
	doc = frappe.get_doc(UV, name, for_update=True)
	if int(doc.da_an_danh or 0):
		frappe.throw("Hồ sơ này đã xoá thông tin theo hạn lưu, không cập nhật được nữa.")
	lich_hen = str(lich_hen or "").strip().replace("T", " ")[:16] or None
	if lich_hen:
		try:
			datetime.strptime(lich_hen, "%Y-%m-%d %H:%M")
		except ValueError:
			frappe.throw("Ngày giờ hẹn không hợp lệ. Chọn lại ngày và giờ.")
	loi = kiem_chuyen(doc.trang_thai, trang_thai, lich_hen, ly_do)
	if loi:
		frappe.throw(loi)
	cu = doc.trang_thai
	ghi = re.sub(r"\s+", " ", str(ghi_chu or "")).strip()[:500]
	cau = cu + " -> " + trang_thai if cu != trang_thai else trang_thai
	if trang_thai in CAN_HEN:
		doc.lich_hen = lich_hen + ":00"
		cau += ", hẹn " + datetime.strptime(lich_hen, "%Y-%m-%d %H:%M").strftime("%H:%M %d/%m")
	if trang_thai == DUNG:
		doc.ly_do_dung = re.sub(r"\s+", " ", str(ly_do)).strip()[:140]
		cau += " (" + doc.ly_do_dung + ")"
	else:
		doc.ly_do_dung = ""
	if cu == MOI and trang_thai != MOI and not doc.lien_he_luc:
		doc.lien_he_luc = frappe.utils.now_datetime()
	if ghi:
		cau += ". " + ghi
	doc.trang_thai = trang_thai
	_ghi_vet(doc, cau)
	doc.flags.ignore_permissions = True
	doc.save()
	return {"ok": 1, "trang_thai": doc.trang_thai}


@frappe.whitelist(methods=["POST"])
def cham(name, vong, diem, ket_luan, nhan_xet=None):
	"""Nộp một phiếu chấm (mỗi người phỏng vấn một phiếu). Thêm dòng, không dựng
	lại bảng (bài học v619: dựng lại bảng con làm lịch sử sửa phình)."""
	_kiem_quyen()
	doc = frappe.get_doc(UV, name, for_update=True)
	vt = frappe.db.get_value(VT, doc.vi_tri, ["tieu_chi"], as_dict=True) or {}
	try:
		d = chuan_phieu_cham(tieu_chi_cua(vt), diem, ket_luan, vong)
	except (LoiNhap, ValueError) as e:
		frappe.throw(str(e))
	doc.append("danh_gia", {"vong": vong, "nguoi": _ai(), "luc": frappe.utils.now_datetime(),
		"diem": json.dumps(d, ensure_ascii=False), "diem_tb": diem_tb(d), "ket_luan": ket_luan,
		"nhan_xet": re.sub(r"\s+", " ", str(nhan_xet or "")).strip()[:1000]})
	_ghi_vet(doc, "Chấm %s: %s, điểm %s" % (vong.lower(), ket_luan, diem_tb(d)))
	doc.flags.ignore_permissions = True
	doc.save()
	return {"ok": 1, "diem_tb": diem_tb(d)}


@frappe.whitelist(methods=["POST"])
def ghi_cong_thu(name, gio, tien, da_tra=0):
	"""Ghi công buổi làm thử (anh Việt 30/10/2026: làm thử có trả công) và đánh
	dấu đã trả. Tiền thật trả tại quầy hoặc chuyển khoản; ở đây ghi để không sót."""
	_kiem_quyen()
	try:
		gio = float(str(gio or 0).replace(",", "."))
		tien = int(float(str(tien or 0).replace(".", "").replace(",", "")))
	except (TypeError, ValueError):
		frappe.throw("Giờ làm thử và tiền công phải là số.")
	if not 0 < gio <= 12 or tien <= 0:
		frappe.throw("Ghi số giờ làm thử (tối đa 12) và tiền công lớn hơn 0.")
	doc = frappe.get_doc(UV, name, for_update=True)
	if int(doc.da_tra_cong or 0):
		frappe.throw("Công làm thử của hồ sơ này đã ghi là đã trả lúc %s." % str(doc.tra_cong_luc or "")[:16])
	doc.gio_lam_thu = gio
	doc.tien_cong_thu = tien
	cau = "Công làm thử %s giờ, %s đ" % (("%g" % gio).replace(".", ","), "{:,}".format(tien).replace(",", "."))
	if str(da_tra) in ("1", "true", "True"):
		doc.da_tra_cong = 1
		doc.tra_cong_boi = _ai()
		doc.tra_cong_luc = frappe.utils.now_datetime()
		cau += ", đã trả"
	_ghi_vet(doc, cau)
	doc.flags.ignore_permissions = True
	doc.save()
	return {"ok": 1}
