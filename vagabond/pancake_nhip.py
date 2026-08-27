# -*- coding: utf-8 -*-
"""Nhịp gọi Pancake: một chỗ duy nhất biết Pancake đang khoẻ hay đang chặn.

VÌ SAO PHẢI CÓ TỆP NÀY - CHUYỆN THẬT NGÀY 26 VÀ 27/08/2026
-----------------------------------------------------------
Pancake trả 403 từ sáng 26/08. Hậu quả đo được trên dữ liệu thật:

    hoá đơn sinh từ đơn Pancake   25/08: 45 đơn
                                  26/08: 12 đơn
                                  27/08:  1 đơn

Không một bản ghi nào bị xoá, không một hoá đơn nào bị huỷ. Đơn chỉ đơn giản
là KHÔNG VỀ. Vậy mà suốt hai ngày không màn hình nào nói một câu nào, vì
chuỗi cuối ngày bắt lỗi Pancake rồi chạy tiếp:

    try:
        _dong_bo_doanh_so(ngay)
    except Exception:
        frappe.log_error(...)      # chỉ ghi nhật ký, không ai đọc

Sales mở màn Hoá đơn thấy ít hơn hẳn và chỉ có thể đoán. Anh Việt tưởng dữ
liệu bị mất. Cái hỏng nặng nhất ở đây không phải mã 403 - mã đó là chuyện của
Pancake - mà là HỆ IM LẶNG. Một cái hỏng không nói ra thì không ai chữa.

BA VIỆC TỆP NÀY LÀM
-------------------
1. NHỚ. Lần cuối kéo được là lúc nào, lần cuối hỏng là lúc nào và vì sao.
   Mọi màn đọc chung một chỗ nên không màn nào nói khác màn nào.
2. NGHỈ CHUNG. Một mô đun bị chặn thì CẢ HỆ nghỉ, không phải từng mô đun tự
   đếm giờ riêng rồi thay nhau đập cửa. Đây chính là thứ đã nuôi cái 403:
   màn kiểm bánh gọi 30 giây một lần, nhân với số máy đang mở, cộng màn mua
   vụ và màn vận đơn.
3. NÓI RA. `tinh_trang()` trả về một câu tiếng Việt để màn hình dán thẳng lên
   đầu bảng, không phải một mã lỗi cho lập trình viên.

VÌ SAO GHI VÀO VAGABOND SETTINGS CHỨ KHÔNG PHẢI BỘ NHỚ ĐỆM
-----------------------------------------------------------
Bộ nhớ đệm bị xoá là mất, và mất nghĩa là màn hình lại im lặng - đúng cái
đang chữa. Ô này chỉ ghi khi TRẠNG THÁI ĐỔI (đang khoẻ thành hỏng, hoặc
ngược lại), nên cả ngày hỏng cũng chỉ ghi một lần.

Riêng ký nghỉ thì để trong bộ nhớ đệm: nó chỉ sống vài phút, mất thì cùng
lắm là gọi sớm hơn dự định một nhịp.
"""

import json
import time

import frappe

from vagabond.lib import cfg, giau_khoa

TRUONG = "vgb_pancake_nhip"
KHOA_NGHI = "vgb_pancake_nghi_den"

# Pancake từ chối thì nghỉ bao lâu rồi mới thử lại. Cả hệ nghỉ chung.
NGHI_GIAY = 180

# Quá ngần này không kéo được đơn nào thì màn hình phải kêu lên, dù cho lần
# hỏng gần nhất có được ghi lại hay không. Hai tiếng là quá đủ cho một tiệm
# bánh: giờ nào cũng có đơn.
IM_QUA_LAU_GIAY = 2 * 3600


# ------------------------------------------------------------- phần thuần


def cau_bao(t, hom_nay_giay=None):
	"""Một câu tiếng Việt mô tả tình trạng, hoặc chuỗi rỗng khi mọi thứ ổn.

	Hàm THUẦN: vào là một vật thể, ra là một chuỗi. Không chạm Frappe, không
	chạm mạng, nên bộ kiểm thử tầng khung đọc được nó mà không cần site.
	"""
	t = t if isinstance(t, dict) else {}
	bay_gio = float(hom_nay_giay if hom_nay_giay is not None else time.time())
	ok = float(t.get("luc_ok") or 0)
	hong = float(t.get("luc_hong") or 0)
	# Lần cuối hỏng mới hơn lần cuối kéo được: đang hỏng.
	if hong and hong > ok:
		return (
			"Đơn Pancake chưa về. %s Số dưới đây là của lần kéo được gần nhất%s."
			% (
				str(t.get("loi") or "Pancake đang từ chối lượt gọi."),
				(" lúc " + str(t.get("ok_luc_nao") or "")) if t.get("ok_luc_nao") else "",
			)
		)
	# Chưa bao giờ kéo được: chưa khai khoá, hoặc mới dựng.
	if not ok:
		return "Chưa lần nào kéo được đơn Pancake về. Kiểm tra khoá API trong Cài đặt."
	# Kéo được, nhưng đã lâu quá.
	if bay_gio - ok > IM_QUA_LAU_GIAY:
		gio = int((bay_gio - ok) // 3600)
		return (
			"Đã %d tiếng chưa kéo được đơn Pancake nào về%s. Danh sách có thể thiếu."
			% (gio, (" (lần cuối lúc " + str(t.get("ok_luc_nao") or "") + ")") if t.get("ok_luc_nao") else "")
		)
	return ""


# --------------------------------------------------------- chạm hệ thống


def _doc():
	try:
		return json.loads((cfg().get(TRUONG) or "").strip() or "{}")
	except Exception:
		return {}


def _ghi(t):
	frappe.db.set_single_value(
		"Vagabond Settings", TRUONG, json.dumps(t, ensure_ascii=False)
	)
	frappe.db.commit()
	frappe.clear_document_cache("Vagabond Settings", "Vagabond Settings")


def ghi_ok():
	"""Vừa kéo được đơn về. Chỉ ghi khi trạng thái ĐỔI, khỏi ghi cả ngày."""
	t = _doc()
	dang_hong = float(t.get("luc_hong") or 0) > float(t.get("luc_ok") or 0)
	bay_gio = time.time()
	# Đang khoẻ sẵn và vừa ghi trong vòng mười phút thì thôi, khỏi ghi lại.
	if not dang_hong and bay_gio - float(t.get("luc_ok") or 0) < 600:
		return
	t["luc_ok"] = bay_gio
	t["ok_luc_nao"] = frappe.utils.now_datetime().strftime("%H:%M %d/%m")
	t["loi"] = ""
	try:
		_ghi(t)
	except Exception:
		pass
	xoa_nghi()


def ghi_hong(loi, nghi=True):
	"""Vừa bị Pancake từ chối. `loi` là câu cho người đọc, đã giấu khoá."""
	t = _doc()
	bay_gio = time.time()
	sach = giau_khoa(loi)[:300]
	doi = (float(t.get("luc_hong") or 0) <= float(t.get("luc_ok") or 0)) or (t.get("loi") != sach)
	t["luc_hong"] = bay_gio
	t["loi"] = sach
	if doi:
		try:
			_ghi(t)
		except Exception:
			pass
	if nghi:
		bat_dau_nghi()


def bat_dau_nghi(giay=None):
	"""Cả hệ nghỉ gọi Pancake trong ngần này giây."""
	try:
		frappe.cache().set_value(KHOA_NGHI, time.time() + float(giay or NGHI_GIAY))
	except Exception:
		pass


def xoa_nghi():
	try:
		frappe.cache().delete_value(KHOA_NGHI)
	except Exception:
		pass


def con_nghi():
	"""Còn bao nhiêu giây nữa mới được gọi Pancake. 0 là gọi được ngay."""
	try:
		den = float(frappe.cache().get_value(KHOA_NGHI) or 0)
	except Exception:
		return 0
	con = den - time.time()
	return int(con) if con > 0 else 0


def tinh_trang():
	"""Tình trạng cho màn hình dán lên đầu bảng."""
	t = _doc()
	return {
		"cau_bao": cau_bao(t),
		"ok_luc_nao": t.get("ok_luc_nao") or "",
		"con_nghi": con_nghi(),
	}
