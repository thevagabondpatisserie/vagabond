"""Gui tin Zalo ZNS qua Zalo OA.

Tach rieng khoi dang_nhap.py vi tu 06/08/2026 co hai cho dung: ma dang nhap
cho khach, va tin yeu cau thanh toan sau khi sales chot duoc don.

ZNS gui duoc toi moi so dien thoai, khach KHONG can quan tam OA - do chinh la
ly do chon kenh nay thay cho cach goi dien roi xin ket ban Zalo.
"""

import json

from datetime import datetime

import frappe
from frappe.utils import now_datetime, get_datetime

# v652: nạp mềm. Bộ kiểm CI không có requests mà ca điểm web nạp diem_otp (kéo
# zalo); máy chủ thật luôn có requests nên đường gửi tin không đổi.
try:
	import requests
except ImportError:  # pragma: no cover
	requests = None

from vagabond.lib import TIMEOUT, key

ZALO_OA = "https://business.openapi.zalo.me"
ZALO_OAUTH = "https://oauth.zaloapp.com/v4/oa/access_token"


# v687 (23/11/2026): làm mới token có khoá. Sự cố 22/11: refresh token bị
# Zalo báo -14014 "Invalid refresh token" từ 04:48 sáng 22/11, mọi tin Zalo
# ngừng. Lúc 09:48 ngày 23/11 thấy một đợt việc nền gọi token() 13 lần trong
# 4 giây, mỗi lần tự xin Zalo làm mới bằng CÙNG một refresh token. Zalo huỷ
# refresh token cũ mỗi lần cấp mới, nên nhiều lượt chạy song song có thể để
# lại trong Cài đặt một mã đã bị huỷ. Từ bản này:
# - chỉ MỘT lượt được làm mới (GET_LOCK), lượt khác chờ rồi đọc lại Cài đặt;
# - Zalo từ chối một refresh token thì nghỉ NGHI_GIAY với đúng mã đó: không
#   gọi lại, không ghi Error Log mỗi tin; dán mã mới thì thử ngay;
# - ghi mã mới bằng phép ghi thẳng, refresh token trước, rồi commit ngay, để
#   một lỗi ở ô khác của Cài đặt không làm mất mã Zalo vừa cấp;
# - mỗi lần làm mới ghi một dòng vào nhật ký vagabond_zalo (dấu vân tay của
#   mã, không ghi mã) để dò khi mã lại bị huỷ.
KHOA_LAM_MOI = "vgb_zalo_lam_moi_token"
CHO_KHOA_GIAY = 20
NGHI_GIAY = 600
KHOA_NGHI = "vgb_zalo_nghi_refresh"
CAU_HONG = "Zalo không cấp được token, nhờ anh chị kiểm tra lại cấu hình Zalo OA"


def van_tay(ma):
	"""12 ký tự đầu sha256 của một mã bí mật, để so hai mã mà không ghi mã. THUẦN."""
	import hashlib

	return hashlib.sha256((ma or "").encode("utf-8")).hexdigest()[:12]


def con_han(tok, han, bay_gio):
	"""Access token còn dùng được. THUẦN."""
	return bool(tok and han and bay_gio < han)


def dang_nghi(nghi, dau):
	"""Refresh token này vừa bị Zalo từ chối, đang trong lúc nghỉ. THUẦN.

	`nghi` là giá trị đọc từ bộ nhớ đệm (dict có van_tay) hoặc None. Mã khác
	(người vừa dán mã mới) thì không nghỉ."""
	return bool(isinstance(nghi, dict) and dau and nghi.get("van_tay") == dau)


def _han(v):
	# Hạn có thể về dạng chuỗi tuỳ cách đọc Cài đặt. So datetime với chuỗi thì
	# Python ném TypeError, mà lỗi đó bị bắt ở gui_tin rồi báo ra thành "không
	# gửi được": nhìn tưởng hết tiền ZNS, thực ra là lỗi kiểu dữ liệu (14/08/2026).
	if v and not isinstance(v, datetime):
		try:
			return get_datetime(v)
		except Exception:
			return None
	return v or None


def token(c):
	"""Access token của OA, tự làm mới bằng refresh token khi hết hạn.

	Hạn của access token lấy theo `expires_in` Zalo trả. Mỗi lần làm mới Zalo
	trả refresh token MỚI và huỷ cái cũ, nên bắt buộc ghi lại vào Cài đặt;
	quên ghi là lần sau hết đường làm mới. Xem ghi chú v687 ở trên.
	"""
	tok = key(c, "zalo_access_token")
	if con_han(tok, _han(c.get("zalo_token_het_han")), now_datetime()):
		return tok
	return _lam_moi()


def _khoa():
	r = frappe.db.sql("select get_lock(%s, %s)", (KHOA_LAM_MOI, CHO_KHOA_GIAY))
	return bool(r and r[0][0] == 1)


def _mo_khoa():
	frappe.db.sql("select release_lock(%s)", (KHOA_LAM_MOI,))


def _doc_moi():
	"""Cài đặt đọc thẳng từ cơ sở dữ liệu, không qua bản lưu đệm."""
	# Commit để mở ảnh dữ liệu mới sau khi chờ khoá: lượt vừa nhả khoá có thể
	# đã ghi token mới. Đường làm mới cũ vốn đã commit sau khi ghi token.
	frappe.db.commit()
	return frappe.get_doc("Vagabond Settings")


def _goi_zalo(app_id, bi_mat, refresh):
	r = requests.post(
		ZALO_OAUTH,
		headers={"secret_key": bi_mat, "Content-Type": "application/x-www-form-urlencoded"},
		data={"app_id": app_id, "refresh_token": refresh, "grant_type": "refresh_token"},
		timeout=TIMEOUT,
	)
	return r.json() if r.content else {}


def _nghi_doc():
	return frappe.cache().get_value(KHOA_NGHI)


def _nghi_ghi(dau):
	frappe.cache().set_value(KHOA_NGHI, {"van_tay": dau}, expires_in_sec=NGHI_GIAY)


def _ghi_token(tok, refresh_moi, het_han):
	"""Ghi thẳng ba ô token rồi commit. Refresh token ghi TRƯỚC: Zalo đã huỷ mã
	cũ, nếu mất mã mới thì chỉ còn cách người dán tay lại."""
	from frappe.utils.password import set_encrypted_password

	dt = "Vagabond Settings"
	if refresh_moi:
		set_encrypted_password(dt, dt, refresh_moi, "zalo_refresh_token")
	set_encrypted_password(dt, dt, tok, "zalo_access_token")
	frappe.db.set_single_value(dt, "zalo_token_het_han", het_han)
	frappe.db.commit()
	frappe.clear_cache(doctype=dt)


def _nhat_ky(**v):
	try:
		frappe.logger("vagabond_zalo", allow_site=True).info(json.dumps(v, default=str))
	except Exception:
		pass


def _lam_moi():
	from datetime import timedelta

	if not _khoa():
		frappe.throw("Zalo đang được làm mới ở lượt khác, thử lại sau ít giây")
	try:
		doc = _doc_moi()
		tok = key(doc, "zalo_access_token")
		han = _han(doc.get("zalo_token_het_han"))
		if con_han(tok, han, now_datetime()):
			return tok  # lượt khác vừa làm mới trong lúc chờ khoá
		app_id = (doc.get("zalo_app_id") or "").strip()
		bi_mat = key(doc, "zalo_app_secret")
		refresh = key(doc, "zalo_refresh_token")
		if not (app_id and bi_mat and refresh):
			frappe.throw("Chưa điền App ID, App Secret hoặc Refresh Token của Zalo OA trong Vagabond Settings")
		dau = van_tay(refresh)
		if dang_nghi(_nghi_doc(), dau):
			frappe.throw(CAU_HONG)
		j = _goi_zalo(app_id, bi_mat, refresh)
		tok = j.get("access_token")
		if not tok:
			_nghi_ghi(dau)
			_nhat_ky(viec="tu_choi", van_tay=dau, zalo=j.get("error"), han_cu=han)
			frappe.log_error(title="Vagabond: Zalo khong cap token", message=json.dumps({
				"zalo": j, "van_tay_refresh": dau, "han_access_token_cu": str(han or ""),
				"ghi_chu": "Nghỉ %d phút với đúng mã này. Dán refresh token mới thì máy thử lại ngay." % (NGHI_GIAY // 60),
			}, ensure_ascii=False)[:1000])
			frappe.throw(CAU_HONG)
		try:
			song = int(j.get("expires_in") or 3600)
		except (TypeError, ValueError):
			song = 3600
		het_han = now_datetime() + timedelta(seconds=max(300, song - 300))
		_ghi_token(tok, j.get("refresh_token"), het_han)
		_nhat_ky(viec="lam_moi", van_tay_cu=dau, van_tay_moi=van_tay(j.get("refresh_token")),
			song=song, het_han=het_han)
		return tok
	finally:
		_mo_khoa()


def gui_mau(c, sdt84, template_id, du_lieu, dau_vet=None):
	"""Gui mot tin theo mau qua so dien thoai. Tra NGUYEN phan hoi Zalo (dict).

	Ben goi can ma loi (vd -140 khach chua du dieu kien nhan tin khuyen mai,
	-1441 het han muc thang) de quyet dung ca luot hay chi bo mot khach, nen
	ham nay khong rut gon thanh (dung, sai). Loi mang tra {"error": -1}.
	"""
	# Bộ kiểm thử tích hợp đang chạy thì TUYỆT ĐỐI không bắn tin ra ngoài.
	#
	# Vì sao cửa này đặt ở ĐÂY chứ không đặt ở từng nơi gọi: có nhiều đường
	# gọi (dang_nhap.py mã đăng nhập, diem_otp.py mã duyệt sửa hoá đơn,
	# thanh_toan.py tin yêu cầu khách chuyển tiền, zalo_kich_ban.py tin tự
	# động, zalo_oa.py tin chiến dịch). Chặn ở một chỗ thì che tất cả, và che
	# sẵn cho đường mai mốt ai đó viết thêm.
	#
	# Vì sao nghiêm trọng: điểm lưu của cơ sở dữ liệu lùi lại được một chứng
	# từ ảo, nhưng KHÔNG lùi lại được một tin nhắn đã nằm trong máy khách
	# thật. Riêng đường thanh_toan.py gửi tin đòi tiền, nên một lần chạy kiểm
	# thử là một lần khách thật bị đòi tiền cho một đơn không có thật.
	#
	# Cùng cách làm với thong_bao.gui. Xem vagabond/khung/kiem_that/nen.py.
	if frappe.flags.get("vagabond_kiem_that"):
		return {"error": -1, "message": "đang chạy kiểm thử tích hợp, không gửi tin ra ngoài"}
	if not template_id:
		return {"error": -1, "message": "Chưa khai mã mẫu ZNS trong Vagabond Settings"}
	try:
		tok = token(c)
	except Exception as e:
		return {"error": -1, "message": str(e)}
	try:
		r = requests.post(
			"%s/message/template" % ZALO_OA,
			headers={"access_token": tok, "Content-Type": "application/json"},
			json={
				"phone": sdt84,
				"template_id": template_id,
				"template_data": du_lieu,
				"tracking_id": dau_vet or ("vgb-%s" % sdt84),
			},
			timeout=TIMEOUT,
		)
		j = r.json() if r.content else {}
	except Exception:
		frappe.log_error(title="Vagabond: ZNS loi mang", message=frappe.get_traceback())
		return {"error": -1, "message": "Không gọi được Zalo"}
	if j.get("error") not in (0, None):
		frappe.log_error(title="Vagabond: ZNS khong gui duoc", message=json.dumps(j)[:1000])
	return j if isinstance(j, dict) else {"error": -1, "message": "Zalo không trả lời rõ ràng"}


def gui_tin(c, sdt84, template_id, du_lieu, dau_vet=None):
	"""Gui mot tin ZNS. Tra ve (thanh_cong, loi).

	KHONG nem loi ra ngoai khi Zalo tu choi - cho ben goi tu quyet dinh, vi co
	cho chi can bao "khong gui duoc" chu khong duoc lam hong ca nghiep vu.
	"""
	# Cửa cờ kiểm thật đặt ở gui_mau (mọi đường gửi đi qua đó). Nhắc lại ở đây
	# để gui_tin tự đứng được nếu mai mốt ai đó tách gui_mau ra.
	if frappe.flags.get("vagabond_kiem_that"):
		return False, "đang chạy kiểm thử tích hợp, không gửi tin ra ngoài"
	if not template_id:
		return False, "Chưa khai mã mẫu ZNS trong Vagabond Settings"
	j = gui_mau(c, sdt84, template_id, du_lieu, dau_vet)
	if j.get("error") not in (0, None):
		return False, j.get("message") or "Zalo từ chối tin"
	return True, ""


def doc_mau(template_id):
	"""CHI DOC: trang thai va bo tham so cua mot mau (template/info/v2).

	Duong cu /template/info tra -106 "Method unsupported" tu khi ZNS gop vao
	ZBS (kiem 29/10/2026). Khong gui tin nao, khong ton tien.
	"""
	from vagabond.lib import cfg

	try:
		tok = token(cfg())
	except Exception as e:
		return {"ok": 0, "loi": str(e)}
	try:
		r = requests.get(
			"%s/template/info/v2" % ZALO_OA,
			headers={"access_token": tok},
			params={"template_id": str(template_id or "").strip()},
			timeout=TIMEOUT,
		)
		j = r.json() if r.content else {}
	except Exception:
		frappe.log_error(title="Vagabond: doc mau ZNS loi mang", message=frappe.get_traceback())
		return {"ok": 0, "loi": "Không gọi được Zalo"}
	if j.get("error") not in (0, None):
		return {"ok": 0, "loi": j.get("message") or "Zalo từ chối", "tho": j}
	d = j.get("data") or {}
	return {
		"ok": 1,
		"template_id": str(d.get("templateId") or template_id),
		"ten": d.get("templateName") or "",
		"trang_thai": d.get("status") or "",
		"ly_do": d.get("reason") or "",
		"tag": d.get("templateTag") or "",
		"gia_sdt": d.get("price_sdt") or d.get("price") or "",
		"xem_truoc": d.get("previewUrl") or "",
		"tham_so": [
			{"name": p.get("name"), "type": p.get("type"), "maxLength": p.get("maxLength"), "require": bool(p.get("require", True))}
			for p in (d.get("listParams") or [])
		],
	}


def han_muc():
	"""CHI DOC: han muc gui tin cua OA hom nay va tin khuyen mai thang nay."""
	from vagabond.lib import cfg

	try:
		tok = token(cfg())
		r = requests.get("%s/message/quota" % ZALO_OA, headers={"access_token": tok}, timeout=TIMEOUT)
		j = r.json() if r.content else {}
	except Exception as e:
		return {"ok": 0, "loi": str(e)[:200]}
	if j.get("error") not in (0, None):
		return {"ok": 0, "loi": j.get("message") or "Zalo từ chối"}
	d = j.get("data") or {}
	return {
		"ok": 1,
		"ngay": d.get("dailyQuota") or 0,
		"con_ngay": d.get("remainingQuota") or 0,
		"km_thang": d.get("monthlyPromotionQuota") or 0,
		"con_km_thang": d.get("remainingMonthlyPromotionQuota") or 0,
		"con_km_ngay": d.get("remainingQuotaPromotion") or 0,
		"km_thang_sau": d.get("estimatedNextMonthPromotionQuota") or 0,
	}


@frappe.whitelist()
def thu_mau(template_id=None):
	"""CHI DOC: hoi Zalo xem mot mau ZNS co nhung tham so gi.

	Vi sao can ham nay
	------------------
	Moi mau ZNS co bo tham so rieng do nguoi tao mau dat ten. Gui sai ten
	mot tham so la Zalo tu choi ca tin, va loi tra ve chi noi chung chung.
	Truoc khi tat che gia lap de gui that cho khach, phai doi chieu bo tham
	so cua mau voi dict ma code dang gui (xem diem_otp._gui_zns).

	Ham nay KHONG gui tin nao, khong ton mot tin ZNS nao.
	"""
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản trị hệ thống mới xem được mẫu ZNS.")
	from vagabond.lib import cfg

	ma = str(template_id or "").strip()
	if not ma:
		frappe.throw("Chưa nhập mã mẫu ZNS. Ví dụ 623902.")
	c = cfg()
	try:
		tok = token(c)
	except Exception as e:
		return {"ok": 0, "loi": str(e)}
	try:
		r = requests.get(
			# Đường cũ /template/info trả -106 từ khi ZNS gộp vào ZBS (29/10/2026).
			"%s/template/info/v2" % ZALO_OA,
			headers={"access_token": tok},
			params={"template_id": ma},
			timeout=TIMEOUT,
		)
		j = r.json() if r.content else {}
	except Exception:
		frappe.log_error(title="Vagabond: doc mau ZNS loi mang", message=frappe.get_traceback())
		return {"ok": 0, "loi": "Không gọi được Zalo"}
	if j.get("error") not in (0, None):
		return {"ok": 0, "loi": j.get("message") or "Zalo từ chối", "tho": j}
	d = j.get("data") or {}
	return {
		"ok": 1,
		"template_id": d.get("templateId") or ma,
		"ten": d.get("templateName") or "",
		"trang_thai": d.get("status") or "",
		"chat_luong": d.get("templateQuality") or "",
		"gia": d.get("price") or "",
		"tham_so": [
			{
				"ten": p.get("name"),
				"kieu": p.get("type"),
				"bat_buoc": p.get("require"),
				"toi_da": p.get("maxLength"),
			}
			for p in (d.get("listParams") or [])
		],
	}
