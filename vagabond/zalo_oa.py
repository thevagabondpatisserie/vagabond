# -*- coding: utf-8 -*-
"""Zalo OA: mời khách quan tâm, nối hồ sơ, gửi tin Truyền thông theo chiến dịch (v617).

VÌ SAO CÓ TỆP NÀY
-----------------
Anh Việt 28/10/2026: "Làm luôn đi em. Và triển khai luôn đợt 2. OA Tăng trưởng
bên anh có rồi." Anh chọn cách "Mời quan tâm OA": quầy và web đưa mã QR mời
khách quan tâm OA; OA hỏi khách chia sẻ số điện thoại; khách chia sẻ thì máy
nối người quan tâm đó với hồ sơ khách và ghi đồng ý nhận tin Zalo (nơi ghi
"Zalo OA", kèm nguyên câu đã hỏi). Chiến dịch có kênh Zalo OA thì máy gửi tin
Truyền thông qua OA cho những khách đó, không cần Sales.

Luật Zalo (đọc kỹ trước khi đổi):
  - Tin Truyền thông chỉ gửi được tới người ĐANG quan tâm OA; số tin mỗi
    người mỗi tháng tuỳ gói OA. Zalo từ chối thì dòng của khách ghi Lỗi kèm
    câu Zalo trả về, không gửi lại tự động.
  - Tin hỏi thông tin (request_user_info) là tin tư vấn, chỉ gửi được trong
    7 ngày sau khi khách tương tác (quan tâm OA là một tương tác).
  - Điểm nhận sự kiện xác thực bằng chữ ký X-ZEvent-Signature:
    sha256(app_id + thân yêu cầu + timestamp + khoá bí mật OA). Không có khoá
    trong Cài đặt thì không nhận gì.

Định dạng thân yêu cầu theo tài liệu Open API v3 của Zalo; TRƯỚC KHI bật kênh
trong Cài đặt, dùng nút "Gửi thử tin OA" của chiến dịch gửi vào UID thử để
xác nhận một lần trên OA thật.

Phần THUẦN ở trên (không chạm Frappe, không thư viện mạng) để bộ kiểm tầng
khung gọi thẳng. Phần chạm hệ nạp frappe và requests trong thân hàm.
"""

import hashlib
import hmac
import json

OA_API = "https://openapi.zalo.me/v3.0/oa"
TT_QUAN_TAM = ("Đang quan tâm", "Đã bỏ quan tâm")
DT_QUAN_TAM = "Vagabond Zalo Quan Tam"
TIEU_DE_MAC_DINH = "Ưu đãi từ The Vagabond Pâtisserie"
# Trạng thái gửi OA của một dòng trong danh sách chiến dịch. Trống là chưa gửi.
TT_GUI = ("Đã gửi", "Lỗi", "Bỏ qua")
# Nghỉ giữa hai tin để không vượt trần tốc độ của Open API.
NGHI_GIUA_TIN = 0.25


# ================================================================ phần thuần

def chu_ky_dung(app_id, than, thoi_diem, khoa, chu_ky_gui):
	"""Chữ ký sự kiện Zalo có khớp không. THUẦN.

	chu_ky_gui là đầu thư X-ZEvent-Signature, dạng "mac=<hex>" (chấp nhận cả
	khi thiếu "mac="). Thiếu khoá hay thiếu chữ ký là KHÔNG khớp: điểm nhận mở
	cho khách vãng lai, không có khoá thì ai cũng giả được sự kiện.
	"""
	khoa = (khoa or "").strip()
	gui = (chu_ky_gui or "").strip()
	if gui.lower().startswith("mac="):
		gui = gui[4:]
	if not khoa or not gui:
		return False
	if isinstance(than, bytes):
		than = than.decode("utf-8")
	mau = hashlib.sha256(("%s%s%s%s" % (app_id or "", than or "", thoi_diem or "", khoa)).encode("utf-8")).hexdigest()
	return hmac.compare_digest(mau, gui.lower())


def doc_su_kien(goi):
	"""Thân sự kiện -> (loại, uid, thông tin). THUẦN.

	loại: "quan_tam", "bo_quan_tam", "chia_se" hoặc "" (sự kiện không xử lý).
	thông tin: {"ten", "sdt"} khi khách chia sẻ thông tin.
	"""
	goi = goi if isinstance(goi, dict) else {}
	ten_sk = str(goi.get("event_name") or "")
	if ten_sk == "follow":
		return "quan_tam", str(((goi.get("follower") or {}).get("id")) or ""), {}
	if ten_sk == "unfollow":
		return "bo_quan_tam", str(((goi.get("follower") or {}).get("id")) or ""), {}
	if ten_sk == "user_submit_info":
		info = goi.get("info") or {}
		return "chia_se", str(((goi.get("sender") or {}).get("id")) or ""), {
			"ten": str(info.get("name") or "").strip()[:140],
			"sdt": str(info.get("phone") or "").strip()[:20],
		}
	return "", "", {}


def than_hoi_sdt(uid, tieu_de, phu_de, anh=""):
	"""Thân tin tư vấn hỏi khách chia sẻ thông tin (request_user_info). THUẦN."""
	el = {"title": (tieu_de or "")[:100], "subtitle": (phu_de or "")[:500]}
	if anh:
		el["image_url"] = anh
	return {
		"recipient": {"user_id": str(uid)},
		"message": {"attachment": {"type": "template", "payload": {
			"template_type": "request_user_info", "elements": [el]}}},
	}


def than_truyen_thong(uid, tieu_de, noi_dung, ma="", han="", anh="", link=""):
	"""Thân tin Truyền thông (template promotion) cho một khách. THUẦN.

	Gồm ảnh bìa (khi có), tiêu đề, đoạn tin, bảng mã ưu đãi và hạn (khi chiến
	dịch phát mã), nút mở trang đặt bánh (khi có đường dẫn).
	"""
	el = []
	if anh:
		el.append({"type": "banner", "image_url": anh})
	el.append({"type": "header", "content": (tieu_de or TIEU_DE_MAC_DINH)[:100]})
	el.append({"type": "text", "align": "left", "content": (noi_dung or "")[:1000]})
	if ma:
		bang = [{"key": "Mã ưu đãi", "value": ma}]
		if han:
			bang.append({"key": "Dùng đến", "value": han})
		el.append({"type": "table", "content": bang})
	payload = {"template_type": "promotion", "language": "VI", "elements": el}
	if link:
		payload["buttons"] = [{"title": "Đặt bánh", "type": "oa.open.url", "payload": {"url": link}}]
	return {"recipient": {"user_id": str(uid)}, "message": {"attachment": {"type": "template", "payload": payload}}}


def ket_qua_zalo(j):
	"""Phản hồi Open API -> (thành công, câu lỗi). THUẦN. error 0 là được."""
	j = j if isinstance(j, dict) else {}
	try:
		ma = int(j.get("error"))
	except (TypeError, ValueError):
		return False, "Zalo không trả lời rõ ràng"
	if ma == 0:
		return True, ""
	return False, ("%s (mã %s)" % (j.get("message") or "Zalo từ chối tin", ma))[:300]


def ngay_vn(s):
	"""'2026-12-24' -> '24/12/2026'. THUẦN. Rỗng hay sai dạng thì trả nguyên."""
	s = str(s or "")[:10]
	p = s.split("-")
	return "%s/%s/%s" % (p[2], p[1], p[0]) if len(p) == 3 and len(p[0]) == 4 else s


def link_oa(oa_id):
	"""Đường dẫn mời quan tâm OA (mã QR quầy in ra). THUẦN."""
	oa_id = str(oa_id or "").strip()
	return ("https://zalo.me/%s" % oa_id) if oa_id else ""


# ================================================================ phần chạm hệ

import frappe  # noqa: E402

def _cfg():
	from vagabond.lib import cfg

	return cfg()


def oa_dang_bat():
	"""Kênh Zalo OA đã bật trong Cài đặt chưa. Lỗi đọc thì coi như tắt."""
	try:
		return bool(int(_cfg().get("zalo_oa_bat") or 0))
	except Exception:
		return False


def _post(duong, than):
	"""Gọi Open API OA. Trả (thành công, câu lỗi, json)."""
	from vagabond import zalo
	from vagabond.lib import TIMEOUT

	if frappe.flags.get("vagabond_kiem_that"):
		return False, "đang chạy kiểm thử tích hợp, không gửi tin ra ngoài", {}
	try:
		tok = zalo.token(_cfg())
	except Exception as e:
		return False, str(e)[:300], {}
	try:
		import requests

		r = requests.post("%s/%s" % (OA_API, duong), headers={"access_token": tok, "Content-Type": "application/json"},
			data=json.dumps(than, ensure_ascii=False).encode("utf-8"), timeout=TIMEOUT)
		j = r.json() if r.content else {}
	except Exception:
		frappe.log_error(title="Vagabond: Zalo OA lỗi mạng", message=frappe.get_traceback())
		return False, "Không gọi được Zalo", {}
	ok, loi = ket_qua_zalo(j)
	return ok, loi, j


def _ghi_quan_tam(uid, **v):
	"""Thêm hoặc sửa dòng người quan tâm theo UID (Zalo gửi lại sự kiện thì
	vẫn ra đúng một dòng)."""

	if frappe.db.exists(DT_QUAN_TAM, uid):
		frappe.db.set_value(DT_QUAN_TAM, uid, v, update_modified=True)
	else:
		d = {"doctype": DT_QUAN_TAM, "uid": uid}
		d.update(v)
		frappe.get_doc(d).insert(ignore_permissions=True)


def xu_ly_su_kien(goi):
	"""Áp một sự kiện đã xác thực. Trả loại sự kiện đã xử lý."""
	from frappe.utils import now_datetime

	loai, uid, tt = doc_su_kien(goi)
	if not loai or not uid:
		return ""
	luc = now_datetime()
	if loai == "quan_tam":
		_ghi_quan_tam(uid, trang_thai="Đang quan tâm", luc_quan_tam=luc)
		if oa_dang_bat() and not frappe.db.get_value(DT_QUAN_TAM, uid, "khach"):
			frappe.enqueue("vagabond.zalo_oa.hoi_sdt", queue="short", uid=uid, enqueue_after_commit=True,
				job_id="zalo_oa_hoi_" + uid, deduplicate=True)
	elif loai == "bo_quan_tam":
		if frappe.db.exists(DT_QUAN_TAM, uid):
			frappe.db.set_value(DT_QUAN_TAM, uid, {"trang_thai": "Đã bỏ quan tâm", "luc_bo": luc}, update_modified=True)
	elif loai == "chia_se":
		from vagabond import crm
		from vagabond.lib import sdt as chuan_sdt
		from vagabond.nhap_khach import khach_cho_don

		so = chuan_sdt(tt.get("sdt")) or ""
		ma = khach_cho_don(so, tt.get("ten")) if so else ""
		_ghi_quan_tam(uid, trang_thai="Đang quan tâm", khach=ma or None, sdt=so, ten_zalo=tt.get("ten") or "",
			luc_chia_se=luc)
		if ma:
			crm.ghi_dong_y_noi(ma, {"Zalo": "Đồng ý"}, "Zalo OA", cau_hoi=crm.CAU_HOI_OA, nguoi="Guest")
	return loai



@frappe.whitelist(allow_guest=True, methods=["POST"])
def nhan_su_kien():
	"""Điểm nhận sự kiện của Zalo OA (đăng ký đường dẫn này trên Zalo Developers).

	Chữ ký sai hay chưa có khoá thì trả 401, không ghi gì. Lỗi khi xử lý thì
	ghi Error Log và vẫn trả 200, để Zalo không bắn lại mãi một sự kiện hỏng.
	"""

	from vagabond.lib import key

	c = _cfg()
	than = frappe.request.get_data(as_text=True) if frappe.request else ""
	try:
		goi = json.loads(than or "{}")
	except ValueError:
		goi = {}
	if not chu_ky_dung((c.get("zalo_app_id") or "").strip(), than, (goi or {}).get("timestamp"),
			key(c, "zalo_oa_khoa_webhook"), frappe.get_request_header("X-ZEvent-Signature") or ""):
		frappe.local.response["http_status_code"] = 401
		return {"ok": 0}
	try:
		loai = xu_ly_su_kien(goi)
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Vagabond: Zalo OA xử lý sự kiện", message=frappe.get_traceback())
		return {"ok": 1, "loai": "loi"}
	return {"ok": 1, "loai": loai}


def hoi_sdt(uid):
	"""Gửi tin hỏi khách chia sẻ số điện thoại (việc nền sau khi khách quan tâm)."""
	from frappe.utils import now_datetime

	from vagabond import crm

	c = _cfg()
	ok, loi, _ = _post("message/cs", than_hoi_sdt(uid, "Nhận ưu đãi từ The Vagabond Pâtisserie", crm.CAU_HOI_OA,
		(c.get("zalo_oa_anh") or "").strip()))
	if frappe.db.exists(DT_QUAN_TAM, uid):
		frappe.db.set_value(DT_QUAN_TAM, uid, {"hoi_sdt_luc": now_datetime(), "hoi_sdt_loi": "" if ok else loi},
			update_modified=False)
	return {"ok": 1 if ok else 0, "loi": loi}


def _tin_cua(cd, ten, ma):
	from vagabond import crm

	c = _cfg()
	han = ngay_vn(cd.get("han")) if ma else ""
	web = (c.get("web_ten_mien_chinh") or "").strip()
	link = web if web.startswith("http") else (("https://" + web) if web else "")
	return lambda uid: than_truyen_thong(uid, cd.get("tieu_de_oa") or TIEU_DE_MAC_DINH,
		crm.tin_zalo_khach(cd.get("noi_dung_zalo"), ten, ma), ma, han, (c.get("zalo_oa_anh") or "").strip(), link)


@frappe.whitelist()
def gui_thu_oa(name=None):
	"""Gửi thử tin OA của một chiến dịch vào UID thử trong Cài đặt."""

	from vagabond import crm

	crm._kiem(crm.CRM_LAP, "gửi thử tin Zalo OA")
	doc = crm._cd(name)
	uid = (_cfg().get("zalo_oa_uid_thu") or "").strip()
	if not uid:
		frappe.throw("Chưa khai UID nhận tin thử trong Cài đặt, mục Zalo OA.")
	if len((doc.noi_dung_zalo or "").strip()) < 20:
		frappe.throw("Viết tin Zalo (ít nhất 20 chữ) rồi gửi thử.")
	ok, loi, _ = _post("message/promotion", _tin_cua(doc, "Khách thử", "THU123" if doc.ctkm else "")(uid))
	return {"ok": 1 if ok else 0, "loi": loi}


@frappe.whitelist()
def gui_chien_dich_oa(name=None):
	"""Xếp việc nền gửi tin OA cho mọi khách nhóm Nhận chưa gửi của chiến dịch.

	"Đã xếp" không phải "đã gửi" (bài học v602): màn đọc lại trạng thái từng
	dòng từ cơ sở dữ liệu, chiến dịch ghi "Đang gửi" tới khi việc nền xong.
	"""

	from vagabond import crm

	crm._kiem(crm.CRM_LAP, "gửi tin Zalo OA")
	if not oa_dang_bat():
		frappe.throw("Kênh Zalo OA đang tắt. Bật trong Cài đặt, mục Zalo OA, sau khi đã gửi thử thành công.")
	doc = crm._cd(name, khoa=True)
	if doc.trang_thai != "Đang chạy":
		frappe.throw("Chỉ gửi được khi chiến dịch đã chốt danh sách và đang chạy.")
	if not int(doc.get("kenh_oa") or 0):
		frappe.throw("Chiến dịch này không chọn kênh Zalo OA.")
	if doc.get("oa_trang_thai") == "Đang gửi":
		return {"ok": 1, "dang_gui": 1}
	frappe.db.set_value(crm.DT_CD, doc.name, "oa_trang_thai", "Đang gửi", update_modified=False)
	frappe.enqueue("vagabond.zalo_oa.gui_nen", queue="long", timeout=3000, name=doc.name,
		enqueue_after_commit=True, job_id="crm_oa_" + doc.name, deduplicate=True)
	return {"ok": 1, "dang_gui": 1}


def gui_nen(name):
	"""Việc nền: gửi từng khách, ghi kết quả từng dòng, commit sau mỗi khách."""
	import time

	from frappe.utils import now_datetime

	from vagabond import crm

	doc = frappe.get_doc(crm.DT_CD, name)
	cd = doc.as_dict()
	dem = {"Đã gửi": 0, "Lỗi": 0, "Bỏ qua": 0}
	try:
		rows = frappe.db.sql(
			"""select k.name, k.khach, k.ten_khach, k.ma_uu_dai, h.dy_zalo, ifnull(h.khong_quang_cao, 0) kqc,
			(select z.uid from `tab%s` z where z.khach = k.khach and z.trang_thai = 'Đang quan tâm'
			 order by z.modified desc limit 1) uid
			from `tab%s` k left join `tab%s` h on h.name = k.khach
			where k.chien_dich = %%s and k.nhanh = 'Nhận' and ifnull(k.oa_trang_thai, '') in ('', 'Lỗi')
			order by k.ten_khach""" % (DT_QUAN_TAM, crm.DT_CD_KHACH, crm.DT_HO_SO), (name,), as_dict=True)
		for r in rows:
			r["oa"] = 1 if r.uid else 0
			kenh = crm.kenh_lien_he_luc_nay(r, cd)
			if crm.KENH_OA not in kenh:
				# Khách rút đồng ý, bỏ quan tâm hay vào Danh sách không quảng cáo
				# sau lúc chốt: không gửi (Codex PR #505, đồng ý hiện tại).
				tt, loi = "Bỏ qua", "Khách không còn đồng ý nhận tin Zalo hoặc đã bỏ quan tâm OA."
			else:
				ok, loi, _ = _post("message/promotion", _tin_cua(cd, r.ten_khach, r.ma_uu_dai)(r.uid))
				tt = "Đã gửi" if ok else "Lỗi"
				time.sleep(NGHI_GIUA_TIN)
			dem[tt] += 1
			luc = now_datetime()
			frappe.db.set_value(crm.DT_CD_KHACH, r.name, {"oa_trang_thai": tt, "oa_loi": loi or "", "oa_luc": luc},
				update_modified=False)
			if tt == "Đã gửi":
				frappe.get_doc({"doctype": crm.DT_LIEN_HE, "khach": r.khach, "kenh": crm.KENH_OA,
					"ket_qua": "Đã gửi tin Truyền thông qua OA", "chien_dich": name, "nguoi": doc.owner,
					"luc": luc}).insert(ignore_permissions=True)
			frappe.db.commit()
	finally:
		frappe.db.set_value(crm.DT_CD, name, {"oa_trang_thai": "Đã gửi xong", "oa_gui_luc": now_datetime(),
			"oa_ket_qua": "Đã gửi %d khách, lỗi %d, bỏ qua %d." % (dem["Đã gửi"], dem["Lỗi"], dem["Bỏ qua"])},
			update_modified=False)
		frappe.db.commit()
	return dem
