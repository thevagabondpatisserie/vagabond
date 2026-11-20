"""Công tắc giao diện ui-b trên Frappe THẬT (bench CI dùng một lần), PR 1 nền.

Bản giả không chứng minh được ba điều dưới đây, vì chúng nằm trong cách
Frappe dựng và lưu đệm trang web:

  1. Trang /bep mang đúng trạng thái của TỪNG tài khoản ngay trong HTML trả
     về (đoạn script trong <head> chạy trước lần vẽ đầu).
  2. Frappe không lưu HTML của người này rồi trả cho người khác: hai người
     vào nối tiếp nhau trên cùng một tiến trình vẫn ra hai trạng thái, và
     trang không bao giờ ra từ bộ nhớ đệm.
  3. Đủ ba tầng công tắc đọc từ doctype thật, kể cả Tắt khẩn cấp thắng Luôn bật.

Gọi thẳng ứng dụng WSGI của Frappe bằng máy khách thử của Werkzeug: đăng nhập
bằng cookie thật, không mở cổng mạng, không nối ra ngoài.
"""
import json
import os
import re
import traceback
from pathlib import Path

SITE = "bench-ci.localhost"
A = "ui-b-a@bench-ci.localhost"
B = "ui-b-b@bench-ci.localhost"
MK = "Ui-b-Bench-476!"
DAU = {"X-Frappe-Site-Name": SITE}


def _mo():
	import frappe
	frappe.init(site=SITE, sites_path=".")
	frappe.connect()
	assert frappe.conf.get("vagabond_bench_thu"), "Thiếu khoá bench thử"
	frappe.set_user("Administrator")
	return frappe


def _dong(frappe, luu=True):
	if luu:
		frappe.db.commit()
	else:
		frappe.db.rollback()
	frappe.destroy()


def _dung_nen():
	"""Dựng trang /bep và hai tài khoản. Trả về tên Web Page nếu CHÍNH ca này tạo ra, để dọn lại.

	Bench CI trắng chưa có trang /bep; bước sau của workflow (phuc_vu_ci.tao_trang) tự dựng và
	sẽ dừng nếu thấy trang đã có. Nên ca này tạo gì thì phải gỡ đúng thứ đó khi xong.
	"""
	frappe = _mo()
	trang_tao = None
	try:
		from frappe.utils.password import update_password
		if not frappe.db.exists("Web Page", {"route": "bep"}):
			trang_tao = frappe.get_doc({"doctype": "Web Page", "title": "Màn hình nghiệp vụ", "route": "bep", "published": 1,
				"content_type": "HTML", "main_section_html": '<div id="vgb"></div>'}).insert(ignore_permissions=True).name
		for email in (A, B):
			if not frappe.db.exists("User", email):
				frappe.get_doc({"doctype": "User", "email": email, "first_name": "UI B", "send_welcome_email": 0,
					"user_type": "Website User"}).insert(ignore_permissions=True)
			update_password(email, MK)
		frappe.clear_cache()
	finally:
		_dong(frappe)
	return trang_tao


def _don(trang_tao):
	"""Trả bench về như trước: công tắc tắt hết, gỡ trang và hai tài khoản ca này tạo."""
	_dat(0, 0, {})
	frappe = _mo()
	con = {}
	try:
		if trang_tao and frappe.db.exists("Web Page", trang_tao):
			frappe.delete_doc("Web Page", trang_tao, force=1, ignore_permissions=True)
		for email in (A, B):
			try:
				if frappe.db.exists("User", email):
					frappe.delete_doc("User", email, force=1, ignore_permissions=True)
			except Exception:
				# Không xoá được (còn bản ghi trỏ tới) thì khoá tài khoản, không để lại tài khoản thử đăng nhập được.
				frappe.db.set_value("User", email, "enabled", 0)
		frappe.clear_cache()
		con["trang_bep"] = bool(frappe.db.exists("Web Page", {"route": "bep"}))
		con["tai_khoan_con_bat"] = [e for e in (A, B) if frappe.db.get_value("User", e, "enabled")]
	finally:
		_dong(frappe)
	return con


def _dat(khan_cap, chung, rieng):
	"""Đặt ba tầng công tắc trên doctype thật. rieng: {email: lựa chọn}."""
	frappe = _mo()
	try:
		d = frappe.get_doc("Vagabond Giao Dien")
		d.tat_khan_cap = khan_cap
		d.bat_chung = chung
		d.set("rieng", [])
		for email, lc in rieng.items():
			d.append("rieng", {"nguoi_dung": email, "lua_chon": lc})
		d.save(ignore_permissions=True)
	finally:
		_dong(frappe)


def _khach():
	from frappe.app import application
	from werkzeug.test import Client
	return Client(application)


def _vao(khach, email):
	r = khach.post("/api/method/login", data={"usr": email, "pwd": MK}, headers=DAU)
	assert r.status_code == 200, "Đăng nhập %s hỏng: %s %s" % (email, r.status_code, r.get_data(as_text=True)[:200])


def _trang(khach, duong="/bep"):
	r = khach.get(duong, headers=DAU)
	html = r.get_data(as_text=True)
	m = re.search(r'window\.__VGB_UI=\{b:(\d),v:"(\d*)"\}', html)
	return {
		"ma": r.status_code,
		"co_khoi": bool(m),
		"b": int(m.group(1)) if m else None,
		"v": m.group(2) if m else None,
		"gan_class": "document.documentElement.classList.add('ui-b')" in html,
		"truoc_than": bool(m) and html.find("window.__VGB_UI") < html.find("<body"),
		"cache_control": r.headers.get("Cache-Control", ""),
		"tu_dem": str(r.headers.get("X-From-Cache", "")),
	}


def chay():
	if os.environ.get("GITHUB_ACTIONS") != "true":
		raise RuntimeError("Chỉ chạy trên bench CI dùng một lần")
	from vagabond.giao_dien import LUON_BAT, LUON_TAT
	from vagabond.duong_app import DUONG
	ra = Path(os.environ["VGB_ARTIFACTS"])
	ket = {"dat": False, "ca": []}

	def ca(ten, dk, chi_tiet=None):
		ket["ca"].append({"ten": ten, "dat": bool(dk), "chi_tiet": chi_tiet})

	trang_tao = None
	try:
		trang_tao = _dung_nen()

		# 1. Cả tiệm tắt, không ai có lựa chọn riêng: khách vãng lai ra giao diện cũ.
		_dat(0, 0, {})
		k = _khach()
		t = _trang(k)
		ca("chưa đăng nhập, cả tiệm tắt: trang mở được", t["ma"] == 200, t)
		ca("chưa đăng nhập, cả tiệm tắt: có khối trạng thái, b bằng 0, không gắn class", t["co_khoi"] and t["b"] == 0 and not t["gan_class"], t)
		ca("khối trạng thái nằm trong head, trước thân trang", t["truoc_than"], t)
		ca("số phiên bản là chữ số", bool(t["v"]) and t["v"].isdigit(), t)
		ca("Cache-Control private, no-store", "no-store" in t["cache_control"] and "private" in t["cache_control"], t)
		t2 = _trang(k)
		ca("mở lần hai không ra từ bộ nhớ đệm", t2["tu_dem"] not in ("True", "1", "true"), t2)

		# 2. A đặt Luôn bật, cả tiệm tắt: chỉ A thấy mới. B vào ngay sau, cùng tiến trình máy chủ, vẫn cũ.
		# Mỗi tài khoản một máy khách (một hũ cookie) như hai trình duyệt; phần đăng xuất rồi
		# đăng nhập trên CÙNG trình duyệt là việc của app (tải lại trang), kiểm bằng máy chụp.
		_dat(0, 0, {A: LUON_BAT})
		ka, kb = _khach(), _khach()
		_vao(ka, A)
		ta = _trang(ka)
		ca("A Luôn bật, cả tiệm tắt: A thấy giao diện mới", ta["b"] == 1 and ta["gan_class"], ta)
		_vao(kb, B)
		tb = _trang(kb)
		ca("B vào ngay sau A: B thấy giao diện cũ", tb["b"] == 0 and not tb["gan_class"], tb)
		ca("trang của B không ra từ bộ nhớ đệm", tb["tu_dem"] not in ("True", "1", "true"), tb)
		ta2 = _trang(ka)
		ca("chiều ngược lại: A vào sau B vẫn thấy mới", ta2["b"] == 1 and ta2["gan_class"], ta2)
		tg = _trang(_khach())
		ca("khách chưa đăng nhập không dính trạng thái của A", tg["b"] == 0 and not tg["gan_class"], tg)

		# 3. Đường riêng của từng màn (F5 đứng nguyên màn) đi cùng một cửa.
		duong = "/" + sorted(DUONG)[0]
		td = _trang(ka, duong)
		ca("đường riêng %s cũng mang trạng thái của A" % duong, td["ma"] == 200 and td["b"] == 1 and td["gan_class"], td)

		# 4. Tắt khẩn cấp thắng Luôn bật.
		_dat(1, 1, {A: LUON_BAT})
		tk = _trang(ka)
		ca("Tắt khẩn cấp: A (Luôn bật, cả tiệm bật) về giao diện cũ", tk["b"] == 0 and not tk["gan_class"], tk)

		# 5. Cả tiệm bật: B (Theo chung) thấy mới; A đặt Luôn tắt thì vẫn cũ.
		_dat(0, 1, {A: LUON_TAT})
		tat = _trang(ka)
		ca("cả tiệm bật, A Luôn tắt: A vẫn cũ", tat["b"] == 0 and not tat["gan_class"], tat)
		tb2 = _trang(kb)
		ca("cả tiệm bật: B (Theo chung) thấy mới", tb2["b"] == 1 and tb2["gan_class"], tb2)

		# 6. Trang khác của site không bị đụng.
		r = _khach().get("/login", headers=DAU)
		ca("trang khác (/login) không mang khối trạng thái", "__VGB_UI" not in r.get_data(as_text=True), {"ma": r.status_code})

		ket["dat"] = bool(ket["ca"]) and all(c["dat"] for c in ket["ca"])
	except Exception:
		ket["loi"] = traceback.format_exc()
	finally:
		try:
			con = _don(trang_tao)
			ket["sau_don"] = con
			# Ca này tạo trang thì sau khi dọn không được còn trang, để bước dựng nền sau của workflow chạy được.
			if (trang_tao and con.get("trang_bep")) or con.get("tai_khoan_con_bat"):
				ket["dat"] = False
				ket["loi_don"] = "Dọn chưa sạch: %s" % con
		except Exception:
			ket["dat"] = False
			ket["loi_don"] = traceback.format_exc()
	(ra / "giao-dien-ui-b.json").write_text(json.dumps(ket, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
	print("Giao diện ui-b: " + json.dumps(ket, ensure_ascii=False, default=str), flush=True)
	if not ket["dat"]:
		raise SystemExit(1)


if __name__ == "__main__":
	chay()
