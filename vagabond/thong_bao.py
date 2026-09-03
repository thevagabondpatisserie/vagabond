# -*- coding: utf-8 -*-
"""Thông báo đẩy (Web Push) cho app Vagabond.

Anh Việt 20/08/2026: *"Khi có một phiếu mới chuyển sang trạng thái chờ duyệt
của đúng User đó, hệ thống phải bắn notification làm rung điện thoại và hiện
chuông báo trên App."*

Chia làm hai lớp, và cố ý deploy làm hai lần
--------------------------------------------
Lớp một (v242): sinh cặp khoá VAPID, nhận và giữ đăng ký của từng máy, và
một hàm `gui` biết tự im lặng khi chưa gửi được.

Lớp hai (v243, ĐÃ BẬT): `pywebpush` vào phần phụ thuộc của app, khoá riêng
đổi sang dạng PEM trước khi ký, và một đường `thu_gui` để tự kiểm thử.

Vì sao tách: thêm một thư viện Python là đổi bước dựng bản build trên Frappe
Cloud. Dựng hỏng thì HỎNG CẢ LẦN DEPLOY, tức là mọi thứ khác trong cùng bản
cũng không lên được site. Ghép chung với phần sửa giao diện là lấy rủi ro của
một việc gán cho cả năm việc.

Khoá riêng KHÔNG bao giờ đi ra khỏi máy chủ
-------------------------------------------
Cặp khoá do CHÍNH máy chủ sinh ra và cất trong Vagabond Settings ở ô kiểu
Password. Không ai phải gõ khoá vào đâu cả, và khoá riêng không có đường nào
đi ra màn hình. Chỉ khoá công khai được gửi xuống trình duyệt, đúng như thiết
kế của Web Push.
"""

import base64
import json

import frappe
from frappe.utils import cint

DT_DK = "Vagabond Push Dang Ky"
STG = "Vagabond Settings"


def _b64(raw):
	"""base64url không có dấu bằng, đúng dạng Web Push đòi."""
	return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _sinh_khoa():
	"""Sinh cặp khoá VAPID bằng thư viện cryptography đã có sẵn trên bench.

	KHÔNG cần py_vapid: cặp khoá VAPID chỉ là một khoá EC P-256 thường.
	"""
	from cryptography.hazmat.primitives import serialization
	from cryptography.hazmat.primitives.asymmetric import ec

	kr = ec.generate_private_key(ec.SECP256R1())
	so = kr.private_numbers().private_value.to_bytes(32, "big")
	cong = kr.public_key().public_bytes(
		serialization.Encoding.X962,
		serialization.PublicFormat.UncompressedPoint,
	)
	return _b64(so), _b64(cong)


def _khoa_vapid(rieng):
	"""Đối tượng Vapid cho pywebpush, dựng từ khoá riêng đang lưu.

	VÌ SAO KHÔNG ĐƯA CHUỖI NỮA (sửa 03/09/2026)
	-------------------------------------------
	Bản trước đổi khoá sang PEM rồi đưa CHUỖI PEM cho `webpush(...)`, với
	lý lẽ "PEM thì phiên bản nào cũng đọc được". Sai. pywebpush chỉ đọc PEM
	khi chuỗi đó là ĐƯỜNG DẪN TỆP; đưa nguyên văn PEM thì nó gọi
	`Vapid.from_string`, hàm này base64 giải mã cả cái chuỗi "-----BEGIN"
	rồi ném "ASN.1 parsing error: invalid length". Máy dựng ảnh Python 3.14
	kéo pywebpush 2.x nên từ đó tới 03/09 không một thông báo nào đi được,
	53 lần ghi Nhật ký lỗi mà ngoài chỉ thấy "không thấy thông báo".

	Đường chắc nhất là đường pywebpush ghi trong tài liệu của nó: đưa MỘT
	ĐỐI TƯỢNG Vapid, nó không phải đoán định dạng gì cả. Khoá đang lưu là
	32 byte base64url do `_sinh_khoa` sinh ra, nên `from_raw` là đúng dạng;
	ai lỡ dán PEM vào ô Cài đặt thì đi `from_pem`.
	"""
	from py_vapid import Vapid

	s = (rieng or "").strip()
	if "-----BEGIN" in s:
		return Vapid.from_pem(s.encode())
	return Vapid.from_raw(s.encode())


def dang_khoa_rieng(rieng):
	"""Khoá riêng đang lưu là dạng gì. Hàm THUẦN, để kiểm thử không cần site.

	"raw" là 32 byte base64url (dạng `_sinh_khoa` sinh ra), "pem" là chuỗi
	PEM, "hong" là không phải hai dạng đó. Chỉ hai dạng đầu gửi được.
	"""
	s = (rieng or "").strip()
	if not s:
		return "hong"
	if "-----BEGIN" in s:
		return "pem"
	try:
		raw = base64.urlsafe_b64decode((s + "=" * ((4 - len(s) % 4) % 4)).encode())
	except Exception:
		return "hong"
	return "raw" if len(raw) == 32 else "hong"


def _cai_dat():
	return frappe.get_single(STG)


@frappe.whitelist()
def khoa_cong_khai():
	"""Khoá công khai cho trình duyệt đăng ký nhận thông báo.

	Lần đầu gọi thì tự sinh cặp khoá luôn, để không ai phải đi khai tay.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	try:
		c = _cai_dat()
		cong = (c.get("push_khoa_cong_khai") or "").strip()
		if not cong:
			rieng, cong = _sinh_khoa()
			frappe.db.set_single_value(STG, "push_khoa_rieng", rieng)
			frappe.db.set_single_value(STG, "push_khoa_cong_khai", cong)
			frappe.db.commit()
		return {"khoa": cong}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thong_bao: sinh khoa VAPID loi")
		return {"khoa": ""}


@frappe.whitelist()
def dang_ky(goi=None):
	"""Nhận đăng ký nhận thông báo của một máy.

	Một người có thể có nhiều máy (điện thoại, máy quầy), nên khoá theo
	`endpoint` chứ không khoá theo người: khoá theo người thì cài app trên
	máy thứ hai là mất thông báo ở máy thứ nhất.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	d = frappe.parse_json(goi) if isinstance(goi, str) else (goi or {})
	if not isinstance(d, dict):
		frappe.throw("Gói đăng ký không đúng định dạng.")
	ep = (d.get("endpoint") or "").strip()
	if not ep:
		frappe.throw("Gói đăng ký thiếu endpoint, trình duyệt chưa đăng ký được.")
	kh = (d.get("keys") or {})
	cu = frappe.db.get_value(DT_DK, {"endpoint": ep}, "name")
	gia_tri = {
		"nguoi": frappe.session.user,
		"endpoint": ep,
		"khoa_p256dh": (kh.get("p256dh") or "").strip(),
		"khoa_auth": (kh.get("auth") or "").strip(),
		"con_dung": 1,
	}
	if cu:
		frappe.db.set_value(DT_DK, cu, gia_tri)
	else:
		doc = frappe.get_doc(dict(doctype=DT_DK, **gia_tri))
		doc.flags.ignore_permissions = True
		doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1}


def _ds_dang_ky(nguoi):
	return frappe.get_all(
		DT_DK,
		filters={"nguoi": nguoi, "con_dung": 1},
		fields=["name", "endpoint", "khoa_p256dh", "khoa_auth"],
		limit_page_length=0,
	)


def gui(nguoi, tieu_de, than, duong_dan="/bep", tag=None):
	"""Bắn thông báo tới mọi máy của một người. KHÔNG BAO GIỜ ném lỗi.

	Hàm này được gọi từ giữa luồng duyệt phiếu. Một phiếu đã duyệt xong rồi
	mà lời gọi thông báo ném lỗi thì cả thao tác duyệt bị cuốn theo - tức là
	mất một việc thật vì một cái chuông. Nên mọi thứ ở đây đều nuốt lỗi và
	chỉ ghi log.
	"""
	# Bộ kiểm thử tích hợp đang chạy thì TUYỆT ĐỐI không bắn ra ngoài. Điểm
	# lưu của cơ sở dữ liệu lùi lại được một chứng từ ảo, nhưng không lùi
	# lại được một cái chuông đã kêu trên điện thoại người thật lúc nửa
	# đêm. Xem vagabond/khung/kiem_that/nen.py.
	if frappe.flags.get("vagabond_kiem_that"):
		return {"gui": 0, "vi_sao": "dang chay kiem thu tich hop"}
	try:
		ds = _ds_dang_ky(nguoi)
		if not ds:
			return {"gui": 0, "vi_sao": "nguoi nay chua dang ky may nao"}
		c = _cai_dat()
		rieng = c.get_password("push_khoa_rieng", raise_exception=False) or ""
		if not rieng:
			return {"gui": 0, "vi_sao": "chua co khoa VAPID"}
		try:
			from pywebpush import webpush
		except ImportError:
			# Bản build thiếu thư viện. Không nuốt hẳn: ghi log để còn tra ra,
			# vì triệu chứng ở ngoài chỉ là "không thấy thông báo".
			frappe.log_error(
				"Ban build nay chua co pywebpush. Kiem lai pyproject.toml roi "
				"deploy lai tren Frappe Cloud.",
				"thong_bao: thieu pywebpush",
			)
			return {"gui": 0, "vi_sao": "ban build chua co pywebpush"}
		if dang_khoa_rieng(rieng) == "hong":
			frappe.log_error(
				"Khoa rieng trong Cai dat khong phai 32 byte base64url, cung khong "
				"phai PEM. Xoa o push_khoa_rieng va push_khoa_cong_khai roi mo lai "
				"app de may sinh cap khoa moi; moi may phai dang ky nhan lai.",
				"thong_bao: khoa VAPID hong",
			)
			return {"gui": 0, "vi_sao": "khoa VAPID hong"}
		try:
			khoa = _khoa_vapid(rieng)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "thong_bao: khoa VAPID hong")
			return {"gui": 0, "vi_sao": "khoa VAPID hong"}

		than_goi = json.dumps({
			"tieu_de": tieu_de, "than": than,
			"duong_dan": duong_dan, "tag": tag or "vagabond",
		}, ensure_ascii=False)
		n = 0
		for d in ds:
			try:
				webpush(
					subscription_info={
						"endpoint": d["endpoint"],
						"keys": {"p256dh": d["khoa_p256dh"], "auth": d["khoa_auth"]},
					},
					data=than_goi,
					vapid_private_key=khoa,
					vapid_claims={"sub": "mailto:thevagabondbakery@gmail.com"},
				)
				n += 1
			except Exception as e:
				# 404 và 410 nghĩa là máy đó đã gỡ app hoặc xoá đăng ký. Tắt
				# cờ để lần sau khỏi gọi lại, chứ không xoá (QT-20).
				if "404" in str(e) or "410" in str(e):
					frappe.db.set_value(DT_DK, d["name"], "con_dung", 0)
				else:
					frappe.log_error(frappe.get_traceback(), "thong_bao: gui that bai")
		frappe.db.commit()
		return {"gui": n}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thong_bao: gui loi")
		return {"gui": 0}


@frappe.whitelist()
def tinh_hinh():
	"""Máy này đã đăng ký chưa, và cả hệ có bao nhiêu máy đang nhận.

	Màn Cài đặt đọc để nói đúng tình trạng chứ không đoán: người dùng bấm
	Bật rồi mà không thấy gì thì phải biết là kẹt ở bước nào.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	co_thu_vien = 1
	try:
		import pywebpush  # noqa: F401
	except ImportError:
		co_thu_vien = 0
	cong = ""
	try:
		cong = (_cai_dat().get("push_khoa_cong_khai") or "").strip()
	except Exception:
		cong = ""
	return {
		"may_cua_toi": len(_ds_dang_ky(frappe.session.user)),
		"co_thu_vien": co_thu_vien,
		"co_khoa": 1 if cong else 0,
		"tong_may": frappe.db.count(DT_DK, {"con_dung": 1}),
	}


@frappe.whitelist()
def thu_gui():
	"""Bắn một tin kiểm thử về CHÍNH máy của người đang bấm.

	Chỉ gửi cho bản thân, không có tham số người nhận: một đường gửi thông
	báo tuỳ ý ai cũng gọi được là một cái loa cho kẻ xấu.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	kq = gui(
		frappe.session.user,
		"Vagabond: thử chuông",
		"Nếu điện thoại vừa rung thì thông báo đã chạy đúng.",
		"/bep",
		"thu-chuong",
	) or {}
	if kq.get("gui"):
		return {"ok": 1, "loi_nhan": "Đã bắn tới %d máy. Kiểm điện thoại xem có rung không." % kq["gui"]}
	vi_sao = kq.get("vi_sao") or "chưa rõ"
	cach = {
		"nguoi nay chua dang ky may nao": (
			"Máy này chưa đăng ký. Bấm nút Bật thông báo ở trên, và nhớ phải "
			"thêm app ra màn hình chính trước thì trình duyệt mới cho bật."
		),
		"ban build chua co pywebpush": (
			"Bản build trên máy chủ còn thiếu thư viện gửi. Báo anh Việt deploy "
			"lại bản mới nhất trên Frappe Cloud."
		),
		"chua co khoa VAPID": "Máy chủ chưa sinh khoá. Bấm Bật thông báo một lần rồi thử lại.",
		"khoa VAPID hong": "Khoá trên máy chủ hỏng. Báo anh Việt xem nhật ký lỗi.",
	}.get(vi_sao, "Chưa gửi được. Báo anh Việt xem nhật ký lỗi trên Desk.")
	return {"ok": 0, "loi_nhan": cach}


def bao_cho_vai(vai, tieu_de, than, duong_dan="/bep", tag=None):
	"""Bắn cho MỌI người đang giữ một trong các vai này.

	Dùng khi một phiếu chuyển sang bước chờ duyệt: người duyệt là một VAI
	chứ không phải một cái tên, và viết cứng tên người thì ai nghỉ phép là
	tắc (cùng lý do đã ghi trong de_nghi_chi.py).
	"""
	try:
		nguoi = set()
		for v in vai or []:
			for r in frappe.get_all(
				"Has Role", filters={"role": v, "parenttype": "User"},
				fields=["parent"], limit_page_length=0,
			):
				nguoi.add(r["parent"])
		n = 0
		for u in nguoi:
			if not frappe.db.get_value("User", u, "enabled"):
				continue
			n += (gui(u, tieu_de, than, duong_dan, tag) or {}).get("gui", 0)
		return {"gui": n, "so_nguoi": len(nguoi)}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "thong_bao: bao cho vai loi")
		return {"gui": 0}
