# -*- coding: utf-8 -*-
"""Trợ lý hướng dẫn dùng app, nút nổi trong app Bếp.

Anh Việt chốt 26/08/2026, ba quyết định vận hành:

  1. Mở cho cấp QUẢN LÝ dùng và thử trước, chưa mở đại trà.
  2. Làm luôn giai đoạn 2: đấu mô hình ngôn ngữ dựa trên sổ tay tri thức,
     chấp nhận chi phí để nhân viên hỏi được bằng lời tự nhiên.
  3. Giai đoạn 3 tạm KHÔNG: trợ lý chưa được đọc dữ liệu thật của tiệm.

Ba yêu cầu kiến trúc kèm theo:

  - Trợ lý xưng "Hệ thống", giọng ngắn gọn, khách quan, chuyên nghiệp.
  - Dưới mỗi câu trả lời có nút báo không hữu ích, cắm cờ vào nhật ký.
  - Nhiệt độ mô hình để mức thấp nhất, chống bịa.


VÌ SAO KHÔNG "THAY MẶT ANH VIỆT"
================================

Ý ban đầu là trợ lý trả lời thay mặt chủ tiệm. Đã xin đổi và anh Việt đồng
ý. Trả lời sai về CÁCH DÙNG một màn hình thì người ta thử lại là biết. Trả
lời sai về CHÍNH SÁCH mà lại mang danh chủ tiệm thì cả tiệm làm theo như thể
đã được duyệt, và không ai biết cho tới lúc mất tiền.

Nên vai của trợ lý là hướng dẫn dùng app. Gặp câu cần quyết thì trả lời rằng
việc đó do anh Việt quyết, rồi dừng. Luật này nằm trong `LUAT` bên dưới chứ
không nằm ở lời dặn miệng.


BA CÁI CHẶN, VÀ VÌ SAO GIỮ CẢ BA
================================

**Chặn một: không có công cụ ghi.** Tệp này không gọi một hàm ghi nào của
nghiệp vụ. Trợ lý không sửa được đơn, không ghi sổ, không đổi giá. Kể cả khi
mô hình bị dụ, nó cũng không có tay để làm.

**Chặn hai: hạn mức lượt.** Mỗi người mỗi ngày và cả tiệm mỗi tháng. Một
vòng lặp hỏng ở máy khách có thể gọi hàng nghìn lượt trong một đêm, và hoá
đơn chỉ lộ ra vào cuối tháng.

**Chặn ba: nhật ký đủ câu hỏi và câu trả lời.** Không có nhật ký thì không
ai biết trợ lý đang dạy nhân viên điều gì. Nút báo không hữu ích cắm cờ vào
đúng dòng nhật ký đó.


VÌ SAO KHÔNG TRẢ LỜI KHI SỔ TAY KHÔNG CÓ GÌ KHỚP
================================================

`chon_muc` trả về rỗng nghĩa là không tìm được mục nào dính tới câu hỏi. Lúc
đó tệp này trả lời thẳng là chưa có tài liệu, KHÔNG gọi mô hình. Gọi mô hình
mà không đưa tư liệu là mời nó bịa, và bịa về một phần mềm nội bộ thì nghe
rất thật vì không ai đối chiếu được.
"""

import json

import frappe
import requests
from frappe.utils import cint, nowdate

from vagabond import tro_ly_so_tay, tro_ly_loi
from vagabond.lib import TIMEOUT, cfg, key
from vagabond.vai_cua_hang import VAI_QLCH

NHAT_KY = "Vagabond Nhat Ky Tro Ly"

# Giai doan 1: chi cap quan ly. Anh Viet chot 26/08/2026 la thu truoc roi
# moi mo dai tra, sau khi doc nhat ky xem tro ly noi gi voi nhan vien.
QUYEN_HOI = {"System Manager", "Giám đốc", "AP Giám đốc", "Accounts Manager",
	"Manufacturing Manager", "Purchase Manager", "Sales Manager",
	"Item Manager", VAI_QLCH}

API = "https://api.anthropic.com/v1/messages"
BAN_API = "2023-06-01"
MO_HINH_MAC_DINH = "claude-sonnet-4-5"

# Nhiet do THAP NHAT. Anh Viet chot 26/08/2026 de chong bia. Muc 0 nghia la
# cung mot cau hoi thi cung mot cau tra loi, va mo hinh bam sat tu lieu thay
# vi tu nghi ra cach dien dat moi.
NHIET_DO = 0

# Tran do dai. Cau hoi dai qua thuong la ai do dan nguyen mot man hinh vao.
DAI_CAU_HOI = 600
DAI_TRA_LOI = 900

# Han muc mac dinh, doi duoc o man Cai dat.
LUOT_NGAY_MAC_DINH = 30
LUOT_THANG_MAC_DINH = 1500

LUAT = """Bạn là trợ lý hướng dẫn sử dụng phần mềm quản trị nội bộ của tiệm
bánh The Vagabond Pâtisserie. Người hỏi là nhân viên của tiệm.

XƯNG HÔ VÀ GIỌNG VĂN
- Chỉ tự xưng là "Hệ thống". Tuyệt đối không dùng bất kỳ đại từ nhân xưng
  ngôi thứ nhất nào khác, kể cả lối xưng thân mật hay lối xưng của người
  ít tuổi hơn. Gọi người hỏi là "anh chị" hoặc không gọi.
- Ngắn gọn, khách quan, chuyên nghiệp. Không chào hỏi, không khách sáo.
- Trả lời thẳng vào việc, tối đa khoảng tám câu.
- Có các bước thao tác thì đánh số từng bước.
- Viết tiếng Việt có dấu. Không dùng dấu gạch ngang dài, chỉ dùng dấu gạch
  ngang thường.

CHỈ ĐƯỢC DỰA VÀO TƯ LIỆU
- Chỉ trả lời dựa trên phần TƯ LIỆU kèm bên dưới.
- Tư liệu không có thông tin thì trả lời đúng một câu: "Hệ thống chưa có tài
  liệu cho câu hỏi này. Vui lòng liên hệ bộ phận kỹ thuật." Không suy đoán,
  không bịa tên màn hình, không bịa tên nút.
- Tuyệt đối không bịa số liệu, không bịa số tiền, không bịa tồn kho. Hệ thống
  hiện chưa được đọc dữ liệu thật của tiệm.

KHÔNG QUYẾT THAY CHỦ TIỆM
- Câu hỏi về chính sách, giá, giảm giá, thưởng phạt, có được làm hay không
  thì trả lời: "Việc này do anh Việt quyết. Vui lòng hỏi trực tiếp." Không
  đưa ý kiến riêng.
- Không hướng dẫn cách lách một phép chặn của phần mềm. Phép chặn nào cũng
  sinh ra từ một sự cố có thật.

TƯ LIỆU
"""

KHONG_BIET = ("Hệ thống chưa có tài liệu cho câu hỏi này. "
	"Vui lòng liên hệ bộ phận kỹ thuật.")


def _quyen():
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not QUYEN_HOI & set(frappe.get_roles()):
		frappe.throw("Trợ lý đang mở cho cấp quản lý dùng thử. "
			"Vui lòng liên hệ bộ phận kỹ thuật nếu cần mở thêm.")


def _han_muc(c):
	ngay = cint(c.get("tro_ly_luot_ngay")) or LUOT_NGAY_MAC_DINH
	thang = cint(c.get("tro_ly_luot_thang")) or LUOT_THANG_MAC_DINH
	return ngay, thang


def _dem(loc):
	return frappe.db.count(NHAT_KY, loc)


def _soat_han_muc(c):
	"""Chặn trước khi gọi mô hình, không phải sau."""
	ngay, thang = _han_muc(c)
	hom_nay = nowdate()
	da_hoi = _dem({"owner": frappe.session.user, "ngay": hom_nay})
	if da_hoi >= ngay:
		frappe.throw("Đã hết lượt hỏi trong ngày (%d lượt). "
			"Vui lòng quay lại vào ngày mai." % ngay)
	dau_thang = hom_nay[:8] + "01"
	ca_thang = _dem({"ngay": [">=", dau_thang]})
	if ca_thang >= thang:
		frappe.throw("Trợ lý đã dùng hết lượt của tháng này. "
			"Vui lòng liên hệ bộ phận kỹ thuật.")


def _ghi_nhat_ky(cau_hoi, tra_loi, man, nguon, mo_hinh):
	d = frappe.get_doc({
		"doctype": NHAT_KY,
		"ngay": nowdate(),
		"man": (man or "")[:140],
		"cau_hoi": cau_hoi,
		"tra_loi": tra_loi,
		"nguon": ", ".join(nguon)[:500],
		"mo_hinh": mo_hinh,
	})
	d.flags.ignore_permissions = True
	d.insert()
	frappe.db.commit()
	return d.name


def _goi_mo_hinh(c, cau_hoi, tu_lieu, man):
	khoa = key(c, "tro_ly_khoa")
	if not khoa:
		frappe.throw("Chưa khai khoá API cho trợ lý trong màn Cài đặt.")
	mo_hinh = (c.get("tro_ly_mo_hinh") or "").strip() or MO_HINH_MAC_DINH
	nguoi = cau_hoi
	if man:
		nguoi = "Người hỏi đang mở màn hình: %s\n\n%s" % (man, cau_hoi)
	than = {
		"model": mo_hinh,
		"max_tokens": DAI_TRA_LOI,
		"temperature": NHIET_DO,
		"system": LUAT + tu_lieu,
		"messages": [{"role": "user", "content": nguoi}],
	}
	r = requests.post(
		API,
		headers={"x-api-key": khoa, "anthropic-version": BAN_API,
			"content-type": "application/json"},
		data=json.dumps(than),
		timeout=TIMEOUT,
	)
	if r.status_code >= 400:
		frappe.log_error(r.text[:2000], "tro_ly: goi mo hinh hong")
		# Noi ro BENH, dung noi chung chung. Ngay 26/08/2026 tro ly im tieng
		# vi tai khoan Anthropic het so du, ma man hinh chi bao "khong goi
		# duoc", nen anh Viet di do khoa API mat mot buoi. Moi loai loi o day
		# dan toi mot viec khac han: nap tien, dan lai khoa, sua ten mo hinh,
		# hay chi la cho.
		try:
			than = r.json()
		except Exception:
			than = r.text[:2000]
		frappe.throw(tro_ly_loi.loi_mo_hinh(r.status_code, than, mo_hinh),
			title="Trợ lý không gọi được mô hình")
	goi = r.json()
	cac_doan = [x.get("text") or "" for x in (goi.get("content") or [])
		if x.get("type") == "text"]
	return ("\n".join(cac_doan).strip() or KHONG_BIET), mo_hinh


@frappe.whitelist()
def hoi(cau_hoi=None, man=None):
	"""Hỏi trợ lý một câu về cách dùng app. CHỈ ĐỌC sổ tay, không chạm dữ liệu."""
	_quyen()
	cau_hoi = str(cau_hoi or "").strip()[:DAI_CAU_HOI]
	if not cau_hoi:
		frappe.throw("Vui lòng nhập câu hỏi.")
	c = cfg()
	if not cint(c.get("tro_ly_bat")):
		frappe.throw("Trợ lý đang tắt. Bật trong màn Cài đặt.")
	_soat_han_muc(c)

	cac_muc = tro_ly_so_tay.chon_muc(cau_hoi, tro_ly_so_tay.so_tay())
	nguon = [str(m.get("ten") or "") for m in cac_muc]
	if not cac_muc:
		# Khong co tu lieu thi KHONG goi mo hinh. Xem doan mo ta dau tep.
		ma = _ghi_nhat_ky(cau_hoi, KHONG_BIET, man, [], "")
		return {"tra_loi": KHONG_BIET, "nhat_ky": ma, "nguon": []}

	tu_lieu = tro_ly_so_tay.gon_tu_lieu(cac_muc)
	tra_loi, mo_hinh = _goi_mo_hinh(c, cau_hoi, tu_lieu, man)
	ma = _ghi_nhat_ky(cau_hoi, tra_loi, man, nguon, mo_hinh)
	return {"tra_loi": tra_loi, "nhat_ky": ma, "nguon": nguon}


@frappe.whitelist()
def bao_loi(nhat_ky=None, ly_do=None):
	"""Cắm cờ một câu trả lời là không hữu ích, để anh Việt xem lại."""
	_quyen()
	ma = str(nhat_ky or "").strip()
	if not ma or not frappe.db.exists(NHAT_KY, ma):
		frappe.throw("Không thấy dòng nhật ký này.")
	frappe.db.set_value(NHAT_KY, ma, {
		"bao_loi": 1,
		"ly_do_bao_loi": str(ly_do or "").strip()[:500],
	})
	frappe.db.commit()
	return {"ok": 1}


# --------------------------------------------------------------- man Cai dat
#
# Anh Viet 26/08/2026: "Anh khong thay cho anthropic key de nhap vao?"
#
# Dung vay. Ban v313 chi them cac o do vao Vagabond Settings ben Desk, con
# man Cai dat TRONG APP thi khong co muc nao. Nguoi dung app khong co duong
# nao toi do. Cai gi bat nguoi ta ra khoi app moi lam duoc thi coi nhu chua
# lam xong.

VAI_SUA_TRO_LY = {"System Manager", "Giám đốc"}


def _quyen_sua():
	if not VAI_SUA_TRO_LY & set(frappe.get_roles()):
		frappe.throw("Chỉ giám đốc và quản lý hệ thống mới sửa cấu hình trợ lý được.")


@frappe.whitelist()
def cai_dat():
	"""Cau hinh tro ly cho man Cai dat. KHONG BAO GIO tra khoa ra ngoai.

	Chi tra ra la CO khoa hay chua. Khoa da khai roi thi khong ai doc lai
	duoc tu app, ke ca giam doc - muon doi thi go khoa moi de len.
	"""
	_quyen_sua()
	c = cfg()
	ngay, thang = _han_muc(c)
	hom_nay = nowdate()
	return {
		"bat": 1 if cint(c.get("tro_ly_bat")) else 0,
		"co_khoa": 1 if key(c, "tro_ly_khoa") else 0,
		"mo_hinh": (c.get("tro_ly_mo_hinh") or "").strip(),
		"mo_hinh_mac_dinh": MO_HINH_MAC_DINH,
		"luot_ngay": ngay,
		"luot_thang": thang,
		"da_hoi_hom_nay": _dem({"ngay": hom_nay}),
		"da_hoi_thang_nay": _dem({"ngay": [">=", hom_nay[:8] + "01"]}),
		"bao_loi_thang_nay": _dem({"ngay": [">=", hom_nay[:8] + "01"], "bao_loi": 1}),
		"vai_duoc_hoi": sorted(QUYEN_HOI),
	}


@frappe.whitelist()
def luu_cai_dat(bat=None, khoa=None, mo_hinh=None, luot_ngay=None, luot_thang=None):
	"""Luu cau hinh tro ly.

	O khoa: de TRONG nghia la GIU NGUYEN khoa cu, khong phai xoa. Day dung
	la cai bay da lam mat du lieu ba lan trong repo nay - man hinh khong gui
	o nao len thi backend hieu la "xoa o do di". Muon go khoa that thi go
	chu xoa, khong phai de trong.
	"""
	_quyen_sua()
	d = frappe.get_single("Vagabond Settings")
	d.tro_ly_bat = 1 if cint(bat) else 0
	k = str(khoa or "").strip()
	if k.lower() in ("xoa", "xoá"):
		d.tro_ly_khoa = ""
	elif k:
		d.tro_ly_khoa = k
	m = str(mo_hinh or "").strip()
	if m:
		d.tro_ly_mo_hinh = m
	n = cint(luot_ngay)
	if n > 0:
		d.tro_ly_luot_ngay = n
	t = cint(luot_thang)
	if t > 0:
		d.tro_ly_luot_thang = t
	d.flags.ignore_permissions = True
	d.save()
	frappe.db.commit()
	return cai_dat()
