# -*- coding: utf-8 -*-
"""Ca kiểm #367 PR1: đơn đặt bánh từ website đủ điều kiện chạy quảng cáo Meta.

Mỗi nhóm ca giữ một cái bẫy Codex và Claude đã chốt trên issue #367:

  A. Token trang biên nhận: không đoán được, máy chủ chỉ lưu băm, gửi trùng
     lấy lại ĐÚNG token cũ, và token khác hẳn event_id gửi Meta.
  B. Chống trùng 15 phút theo khoá: đổi thứ tự dòng không đổi khoá, đổi món,
     số lượng, giờ hay nonce thì đổi khoá.
  C. Phí giao: 999.999 không miễn, đúng 1.000.000 miễn, tự lấy không tính là
     ưu đãi, ngưỡng trống là tắt, Ahamove lỗi thì KHÔNG hiện 0.
  D. Pancake: mất phản hồi hay lỗi máy chủ là Chờ đối soát, 4xx là từ chối,
     và tao_don KHÔNG BAO GIỜ tự gửi lại.
  E. Thứ tự trong tao_don: ghi bản ghi, COMMIT, rồi mới gọi Pancake.
  F. Trang biên nhận không lộ số điện thoại, địa chỉ, email.
  G. Conversions API: băm đúng chuẩn Meta, không mang token, không mang số gốc.
  H. Đối soát: chỉ ghép khi có ĐÚNG một đơn khớp cả số, giờ, món.
  I. Ảnh bánh: ERP trước Pancake ở MỌI nhánh, qua một hàm.
  J. Chính sách: chỉ lộ bản đã xuất bản và bật hiện, chặn xuất bản còn ngoặc
     vuông, bảng marketing có lối đăng nhập.

Phần nào chạy trên trình duyệt thì nạp CẢ trang vào node qua
gia_lap_trang.js (bài học #205: dò chuỗi không phải kiểm thử).
"""

import ast
import contextlib
import io
import json
import os
import re
import subprocess
import types
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la, nem
from vagabond.khung.kiem_thu.thu_su_co_290 import D, nap

GOC = Path(__file__).resolve().parents[3]
GOI = GOC / "vagabond"


def _doc(p):
	return io.open(str(GOC / p), encoding="utf-8").read()


from vagabond import anh_web, don_web, noi_dung_web, trang_khach  # noqa: E402

KHOA = b"khoa-bi-mat-cua-site-thu"


# ------------------------------------------------------------------ A. token

@ca("#367 A token 43 ký tự base64url, lưu băm, gửi trùng ra đúng token cũ, khác event_id")
def _():
	muoi = don_web.sinh_muoi()
	t1 = don_web.sinh_token(KHOA, muoi, "n" * 24)
	t2 = don_web.sinh_token(KHOA, muoi, "n" * 24)
	la("cùng muối cùng nonce thì cùng token (lần gửi trùng lấy lại đúng link)", t1, t2)
	dung("đúng dạng 43 ký tự base64url", don_web.token_hop_le(t1))
	dung("khác muối thì khác token", t1 != don_web.sinh_token(KHOA, don_web.sinh_muoi(), "n" * 24))
	dung("khác nonce thì khác token", t1 != don_web.sinh_token(KHOA, muoi, "m" * 24))
	dung("khác khoá bí mật của site thì khác token", t1 != don_web.sinh_token(b"khac", muoi, "n" * 24))
	dung("băm lưu trong CSDL khác token trên đường dẫn", don_web.bam(t1) != t1 and len(don_web.bam(t1)) == 64)
	ev = don_web.sinh_event_id()
	dung("event_id là uuid, không phải token", ev != t1 and len(ev) == 36)
	for sai in ("", "a" * 42, "a" * 44, "a" * 42 + "/", "../" + "a" * 40):
		dung("token sai dạng bị loại: %r" % sai[:10], not don_web.token_hop_le(sai))
	dung("muối đủ 32 byte", len(muoi) == 64)


# ------------------------------------------------------------ B. chống trùng

@ca("#367 B khoá chống trùng: thứ tự dòng không đổi khoá, món/số/giờ/nonce đổi khoá")
def _():
	h1 = [{"variation_id": "BAWC00139", "quantity": 1}, {"variation_id": "BAPK00001", "quantity": 2}]
	h2 = list(reversed(h1))
	k = don_web.khoa_chong_trung("0931224334", h1, "2026-09-26T13:00:00", "x" * 20)
	la("đảo thứ tự dòng vẫn cùng khoá", don_web.khoa_chong_trung("0931224334", h2, "2026-09-26T13:00:00", "x" * 20), k)
	la("số có mã nước vẫn cùng khoá", don_web.khoa_chong_trung("+84 931 224 334", h1, "2026-09-26T13:00:00", "x" * 20), k)
	dung("khác nonce khác khoá", k != don_web.khoa_chong_trung("0931224334", h1, "2026-09-26T13:00:00", "y" * 20))
	dung("khác giờ khác khoá", k != don_web.khoa_chong_trung("0931224334", h1, "2026-09-26T15:00:00", "x" * 20))
	dung("khác số lượng khác khoá", k != don_web.khoa_chong_trung(
		"0931224334", [dict(h1[0], quantity=2), h1[1]], "2026-09-26T13:00:00", "x" * 20))
	dung("khác số điện thoại khác khoá", k != don_web.khoa_chong_trung("0909000000", h1, "2026-09-26T13:00:00", "x" * 20))
	dung("nonce hợp lệ", don_web.nonce_hop_le("A" * 16) and don_web.nonce_hop_le("a-_9" * 8))
	for sai in ("", "ngan", "a" * 65, "có dấu" * 4, "a b" * 8):
		dung("nonce sai dạng bị loại: %r" % sai[:8], not don_web.nonce_hop_le(sai))


# ------------------------------------------------------------------ C. phí giao

def _bao(phi):
	return {"ok": 1, "total_fee": phi}


@ca("#367 C ngưỡng miễn phí: 999.999 không, 1.000.000 có, 1.000.001 có, ô trống là tắt")
def _():
	q = don_web.quyet_phi_giao
	la("999.999 trả phí", q(999999, 1000000, False, _bao(36000))["phi_khach"], 36000)
	for tien in (1000000, 1000001):
		r = q(tien, 1000000, False, _bao(36000))
		la("%d khách trả 0" % tien, r["phi_khach"], 0)
		dung("%d được miễn" % tien, r["mien_phi"])
		la("%d tiệm chịu đúng phí Ahamove" % tien, r["tiem_chiu"], 36000)
		la("%d phí Ahamove giữ để kế toán thấy" % tien, r["phi_ahamove"], 36000)
	for tat in (None, "", 0, "0"):
		r = q(5000000, tat, False, _bao(36000))
		la("ngưỡng %r thì không miễn" % (tat,), (r["mien_phi"], r["phi_khach"]), (False, 36000))


@ca("#367 C tự lấy phí 0 KHÔNG phải ưu đãi miễn phí; Ahamove lỗi thì không hiện 0")
def _():
	q = don_web.quyet_phi_giao
	r = q(2000000, 1000000, True, None)
	la("tự lấy", (r["trang_thai"], r["phi_khach"], r["mien_phi"], r["tiem_chiu"]), ("tu_lay", 0, False, 0))
	r = q(500000, 1000000, False, {"ok": 0, "ly_do": "ahamove_loi"})
	la("Ahamove lỗi dưới ngưỡng: chưa rõ, không phải 0", (r["trang_thai"], r["phi_khach"]), ("chua_ro", None))
	r = q(500000, 1000000, False, _bao(0))
	la("báo giá 0 cũng là chưa rõ", r["trang_thai"], "chua_ro")
	r = q(1500000, 1000000, False, {"ok": 0})
	la("đủ ngưỡng mà Ahamove lỗi: khách vẫn trả 0", (r["trang_thai"], r["phi_khach"], r["phi_ahamove"]), ("mien_phi", 0, None))


@ca("#367 C tiền bánh máy chủ tự tính, mã thiếu giá tính 0 và báo ra")
def _():
	h = [{"variation_id": "A", "quantity": 2}, {"variation_id": "B", "quantity": 1}, {"variation_id": "C", "quantity": 3}]
	tong, thieu = don_web.tinh_tien_banh(h, {"A": 450000, "B": 110000})
	la("tổng", tong, 1010000)
	la("mã thiếu giá", thieu, ["C"])


# ------------------------------------------------------------------ D. Pancake

@ca("#367 D phản hồi Pancake: mất mạng, 5xx, trả lạ là Chờ đối soát; 4xx và 429 là từ chối")
def _():
	p = don_web.phan_loai_pancake
	la("mất mạng", p(0, None, True)["ket_qua"], "cho_doi_soat")
	la("500", p(500)["ket_qua"], "cho_doi_soat")
	la("502", p(502)["ket_qua"], "cho_doi_soat")
	la("200 không phải JSON", p(200, None)["ket_qua"], "cho_doi_soat")
	la("200 thiếu mã", p(200, {"success": True, "data": {}})["ket_qua"], "cho_doi_soat")
	r = p(200, {"data": {"id": "91428", "display_id": 91428}})
	la("200 có mã", (r["ket_qua"], r["pancake_id"], r["pancake_display_id"]), ("da_nhan", "91428", "91428"))
	la("201 dạng phẳng", p(201, {"id": 7})["ket_qua"], "da_nhan")
	for ma in (400, 401, 403, 422, 429):
		la("%d là từ chối" % ma, p(ma)["ket_qua"], "tu_choi")


# ------------------------------------------------------- E. thứ tự trong tao_don

class _Vet:
	def __init__(self):
		self.su = []


def _moi_truong_tao_don(pancake, trung=None):
	"""Dựng môi trường gọi tao_don THẬT, chặn mọi đường ra ngoài.

	`pancake(vet)` là hàm thay requests.post: ghi 'post' vào vết rồi trả về
	phản hồi giả hoặc ném lỗi mạng. Vết ghi đúng thứ tự: ghi bản ghi, commit,
	post, cập nhật, commit, xếp CAPI.
	"""
	vet = _Vet()

	class Doc(D):
		pass

	ban_ghi = Doc(name="DW-2609-00001", muoi="m" * 64, snapshot="{}", pancake_display_id="")

	@contextlib.contextmanager
	def khoa_ghi(k):
		vet.su.append("khoa")
		yield

	def tao_ban_ghi(nonce, truong):
		vet.su.append("ghi")
		vet.truong = truong
		ban_ghi.snapshot = truong["snapshot"]
		return ban_ghi

	def cap_nhat(bg, kq):
		vet.su.append("cap_nhat:" + kq["ket_qua"])

	def phan_hoi(bg, nonce, trung=False):
		return {"ok": 1, "trung": 1 if trung else 0, "duong_dan": "/banh/xong/" + "t" * 43, "ma_yeu_cau": bg.name}

	dw = types.SimpleNamespace(
		nonce_hop_le=don_web.nonce_hop_le, tinh_tien_banh=don_web.tinh_tien_banh,
		quyet_phi_giao=don_web.quyet_phi_giao, khoa_chong_trung=don_web.khoa_chong_trung,
		phan_loai_pancake=don_web.phan_loai_pancake, fb_hop_le=don_web.fb_hop_le,
		nguong_mien_phi=lambda: 1000000, khoa_ghi=khoa_ghi, tim_trung=lambda k: trung,
		tao_ban_ghi=tao_ban_ghi, cap_nhat_sau_pancake=cap_nhat, phan_hoi=phan_hoi,
		xep_capi=lambda *a, **k: vet.su.append("capi"),
	)
	fr = types.SimpleNamespace(
		db=types.SimpleNamespace(commit=lambda: vet.su.append("commit")),
		log_error=lambda *a, **k: None, get_traceback=lambda: "",
		get_all=lambda *a, **k: [],
	)

	def post(*a, **k):
		vet.su.append("post")
		vet.body = k.get("json")
		return pancake(vet)

	g = dict(
		json=json, re=re, frappe=fr, requests=types.SimpleNamespace(post=post),
		don_web=dw, PANCAKE="https://pancake.invalid", TIMEOUT=1,
		cfg=lambda: D(pancake_shop_id="67355", pancake_order_source_id=""),
		key=lambda c, f: "khoa-thu",
		phi_giao=lambda **k: {"ok": 1, "total_fee": 36000},
		_uuid_tu_ma=lambda c, k, ma: "uuid-" + ma,
		_gia_va_ten=lambda ds: ({m: 450000 for m in ds}, {m: "Bánh " + m for m in ds}),
		_ip_va_trinh_duyet=lambda: ("203.0.113.9", "Trinh duyet thu"),
	)
	for ten in ("_so", "_lam_sach_hang", "_lam_sach_the", "_ngay_iso", "_hoa_don_pancake"):
		nap("don_hang.py", ten, g)
	g["MAX_DONG"], g["MAX_SL"] = 30, 20
	g["_UUID"] = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
	return vet, nap("don_hang.py", "tao_don", g)


def _don(**them):
	d = {"ho_ten": "Nguyễn Văn An", "dien_thoai": "0931224334", "tu_lay": False,
		"dia_chi": "9 Trần Cao Vân, Quận 1", "ngay_nhan": "2026-09-26T13:00:00",
		"items": [{"variation_id": "BAWC00139", "quantity": 1}, {"variation_id": "BAWC00140", "quantity": 1}],
		"nonce": "N" * 24, "dong_y": True, "thanh_toan": "bank"}
	d.update(them)
	return d


class _Tra:
	def __init__(self, ma, du_lieu):
		self.status_code, self._d, self.text = ma, du_lieu, "x"

	def json(self):
		if self._d is None:
			raise ValueError("khong phai json")
		return self._d


@ca("#367 E ghi bản ghi và COMMIT trước khi gọi Pancake, gọi đúng một lần")
def _():
	vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "91500"}}))
	r = tao_don(_don())
	la("trả về có đường dẫn biên nhận", r.get("ok"), 1)
	su = vet.su
	dung("ghi bản ghi trước POST", su.index("ghi") < su.index("post"))
	dung("commit giữa ghi và POST", "commit" in su[su.index("ghi"):su.index("post")])
	la("gọi Pancake đúng một lần", su.count("post"), 1)
	dung("cập nhật kết quả rồi commit lần nữa", su.index("cap_nhat:da_nhan") < len(su) - 1 - su[::-1].index("commit"))
	la("CAPI xếp sau cùng", su[-1], "capi")


@ca("#367 E Pancake mất phản hồi: KHÔNG gửi lại, bản ghi Chờ đối soát, khách vẫn có biên nhận")
def _():
	def mat_mang(v):
		raise OSError("timeout")
	vet, tao_don = _moi_truong_tao_don(mat_mang)
	r = tao_don(_don())
	la("khách được báo đã nhận, không bảo đặt lại", r.get("ok"), 1)
	la("không tự gửi lại", vet.su.count("post"), 1)
	dung("bản ghi sang Chờ đối soát", "cap_nhat:cho_doi_soat" in vet.su)


@ca("#367 E Pancake từ chối (4xx): báo khách chưa gửi được, không xếp CAPI")
def _():
	vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(422, {"message": "sai"}))
	r = tao_don(_don())
	la("khách thấy chưa gửi được", (r.get("ok"), r.get("ly_do")), (0, "pancake_tu_choi"))
	dung("không gửi GuiDon cho đơn không tồn tại", "capi" not in vet.su)


@ca("#367 E gửi trùng trong 15 phút: trả lại bản ghi cũ, KHÔNG gọi Pancake lần hai")
def _():
	cu = D(name="DW-2609-00001", muoi="m" * 64, snapshot="{}")
	vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "1"}}), trung=cu)
	r = tao_don(_don())
	la("trả về bản cũ", (r.get("ok"), r.get("trung"), r.get("ma_yeu_cau")), (1, 1, "DW-2609-00001"))
	la("không POST", vet.su.count("post"), 0)
	la("không ghi thêm bản ghi", vet.su.count("ghi"), 0)


@ca("#367 E thiếu nonce hay chưa đồng ý: chặn ở máy chủ trước mọi việc khác")
def _():
	vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "1"}}))
	la("trang cũ không có nonce", tao_don(_don(nonce=""))["ly_do"], "can_tai_lai_trang")
	la("chưa tick đồng ý", tao_don(_don(dong_y=False))["ly_do"], "chua_dong_y_chinh_sach")
	la("chuỗi 'true' không phải đồng ý", tao_don(_don(dong_y="true"))["ly_do"], "chua_dong_y_chinh_sach")
	la("không ghi, không POST", (vet.su.count("ghi"), vet.su.count("post")), (0, 0))


@ca("#367 E miễn phí giao: Pancake nhận phí khách 0 nhưng phí hãng giữ đúng số Ahamove")
def _():
	vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "1"}}))
	tao_don(_don())  # hai bánh 450.000 = 900.000, dưới ngưỡng
	la("dưới ngưỡng: khách trả phí", (vet.body["shipping_fee"], vet.body["partner_fee"]), (36000, 36000))
	vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "1"}}))
	tao_don(_don(items=[{"variation_id": "BAWC00139", "quantity": 3}]))  # 1.350.000
	la("đủ ngưỡng: khách 0, hãng giữ", (vet.body["shipping_fee"], vet.body["partner_fee"]), (0, 36000))
	snap = json.loads(vet.truong["snapshot"])
	la("ảnh chụp giữ tiền bánh máy chủ tính", vet.truong["tien_banh"], 1350000)
	la("ảnh chụp giữ trạng thái phí", snap["phi"]["trang_thai"], "mien_phi")
	la("và giữ đủ món", [m["ma"] for m in snap["mon"]], ["BAWC00139"])


@ca("#367 E con số trình duyệt gửi lên không quyết tiền: tổng giả 99.000.000 vẫn bị bỏ qua")
def _():
	vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "1"}}))
	tao_don(_don(tong=99000000, tien_banh=99000000, phi_giao=0))
	la("tiền bánh do máy chủ tính", vet.truong["tien_banh"], 900000)
	la("vẫn thu phí giao", vet.body["shipping_fee"], 36000)


# ------------------------------------------------------- F. trang biên nhận

SNAP = {
	"mon": [{"ma": "BAWC00139", "ten": "Bánh Ổ Candle, size 12cm", "sl": 1, "gia": 650000}],
	"nguoi_dat": {"ho_ten": "Nguyễn Văn An", "dien_thoai": "0912345678", "email": "an.nguyen@example.com"},
	"nguoi_nhan": {"ho_ten": "Trần Thị Bình", "dien_thoai": "0909111222"},
	"tu_lay": False, "dia_chi": "12 Lý Tự Trọng, Phường Sài Gòn", "ngay_nhan": "2026-09-26T13:00:00",
	"thanh_toan": "card", "hoa_don": {"tax_code": "0318561568", "name": "Cong ty ABC"},
	"phi": {"trang_thai": "chinh_xac", "phi_khach": 36000, "phi_ahamove": 36000, "mien_phi": False},
}


@ca("#367 F biên nhận không lộ số điện thoại, email, địa chỉ, người nhận, MST")
def _():
	tt = don_web.tom_tat_bien_nhan({"name": "DW-2609-00001", "trang_thai": "Da nhan", "tien_banh": 650000}, SNAP)
	html = trang_khach.bien_nhan_html(tt, {"zalo": "https://zalo.me/0931224334", "messenger": "https://m.me/x"})
	chu = json.dumps(tt, ensure_ascii=False) + html
	for lo in ("0912345678", "912345678", "an.nguyen", "Lý Tự Trọng", "Trần Thị Bình", "0909111222", "0318561568", "Cong ty ABC", "Nguyễn Văn An"):
		dung("không lộ %s" % lo, lo not in chu)
	la("tên viết tắt", tt["ten"], "N. V. An")
	la("tổng có phí", tt["tong"], "686.000 đ")
	la("giờ nhận", (tt["ngay_nhan"], tt["khung_gio"]), ("Thứ 7, 26/09", "13h - 15h"))
	dung("không nói đã thanh toán", "đã thanh toán" not in html.lower())
	dung("có Zalo và Messenger và Đặt thêm", "Nhắn Zalo" in html and "Nhắn Messenger" in html and 'href="/banh"' in html)


@ca("#367 F Chờ đối soát: câu 'không cần đặt lại', không in mã Pancake; phí chưa rõ không thành 0")
def _():
	snap = dict(SNAP, phi={"trang_thai": "chua_ro", "phi_khach": None})
	tt = don_web.tom_tat_bien_nhan({"name": "DW-1", "trang_thai": "Cho doi soat", "tien_banh": 650000}, snap)
	la("trạng thái khách đọc", tt["trang_thai"], "Đang xác nhận")
	dung("câu không cần đặt lại", "Không cần đặt lại" in tt["cau"])
	la("phí giao chưa rõ", tt["phi_giao"], "Sales báo phí khi xác nhận")
	la("tổng không giả vờ đủ", tt["tong"], "Chờ Sales báo phí giao")
	tt = don_web.tom_tat_bien_nhan({"name": "DW-1", "trang_thai": "Da nhan", "tien_banh": 1200000},
		dict(SNAP, phi={"trang_thai": "mien_phi", "phi_khach": 0}))
	la("miễn phí", (tt["phi_giao"], tt["tong"]), ("Miễn phí giao", "1.200.000 đ"))


@ca("#367 F HTML biên nhận thoát ký tự: tên món có thẻ script không thành mã chạy")
def _():
	snap = dict(SNAP, mon=[{"ma": "X", "ten": "<script>alert(1)</script>", "sl": 1, "gia": 1}])
	tt = don_web.tom_tat_bien_nhan({"name": "DW-<b>", "trang_thai": "Da nhan", "tien_banh": 1}, snap)
	h = trang_khach.bien_nhan_html(tt, {"zalo": "javascript:alert(1)"})
	dung("không có thẻ script", "<script>" not in h)
	dung("không nhận liên kết javascript:", "javascript:" not in h)
	s = trang_khach.json_trong_script({"than": "</script><script>alert(1)</script>"})
	dung("JSON nhúng không đóng được thẻ script", "</script>" not in s)


def _get_context(tep, form, bn=None, cs=None, nguoi="Guest", vai=(), duong=""):
	"""Chạy get_context THẬT của trang www với Frappe giả, trả (context, lỗi).
	`duong` là đường dẫn yêu cầu (frappe.local.request.path) cho trang chính sách."""
	class KhongCo(Exception):
		pass

	class ChuyenHuong(Exception):
		pass

	dau = {}
	local = types.SimpleNamespace(no_cache=0, response_headers=dau, flags=types.SimpleNamespace(redirect_location=None),
		request=types.SimpleNamespace(path=duong), path=duong.strip("/"))
	fr = types.SimpleNamespace(
		local=local, form_dict=D(form), PageDoesNotExistError=KhongCo, Redirect=ChuyenHuong,
		session=types.SimpleNamespace(user=nguoi), get_roles=lambda u=None: list(vai),
		sessions=types.SimpleNamespace(get_csrf_token=lambda: "csrf"),
		utils=types.SimpleNamespace(escape_html=lambda s: s),
	)
	dw = types.SimpleNamespace(
		lien_he=lambda: {"dien_thoai": "0931 224 334", "dien_thoai_so": "0931224334", "zalo": "https://zalo.me/0931224334"},
		PHAP_NHAN=don_web.PHAP_NHAN, bien_nhan_theo_token=lambda t: bn, pixel_id=lambda: "123")
	nd = types.SimpleNamespace(chinh_sach_dang_hien=lambda: [], trang_chinh_sach=lambda k, n: cs,
		CHINH_SACH=noi_dung_web.CHINH_SACH, khoa_tu_duong=noi_dung_web.khoa_tu_duong, DUONG_BANG="/bien-tap-web", quyet_vao_bang=noi_dung_web.quyet_vao_bang)
	g = dict(frappe=fr, don_web=dw, noi_dung_web=nd, trang_khach=trang_khach,
		TIEU_DE={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Referrer-Policy": "no-referrer",
			"X-Robots-Tag": "noindex, nofollow"},
		DUONG_BANG="/bien-tap-web", quyet_vao_bang=noi_dung_web.quyet_vao_bang, get_fullname=lambda u: "Minh Vũ")
	ham = nap(tep, "get_context", g)
	ctx = D()
	try:
		ham(ctx)
		return ctx, None, local, dau
	except KhongCo:
		return ctx, "404", local, dau
	except ChuyenHuong:
		return ctx, "302:" + str(local.flags.redirect_location), local, dau


@ca("#367 F trang biên nhận: token sai 404 thật, không đệm, không gửi referrer, noindex")
def _():
	_c, loi, local, dau = _get_context("www/banh/xong.py", {"token": "a" * 43}, bn=None)
	la("token không có trong CSDL", loi, "404")
	bn = {"bien_nhan": don_web.tom_tat_bien_nhan({"name": "DW-1", "trang_thai": "Da nhan", "tien_banh": 650000}, SNAP),
		"su_kien": {"event_id": "ev", "gia_tri": 650000, "ma_mon": ["BAWC00139"], "ban": True}}
	ctx, loi, local, dau = _get_context("www/banh/xong.py", {"token": "a" * 43}, bn=bn)
	la("token đúng mở được", loi, None)
	dung("tắt đệm trang Frappe ở lượt tải", local.no_cache == 1 and ctx.no_cache == 1)
	dung("no-store", "no-store" in dau.get("Cache-Control", ""))
	la("không gửi referrer", dau.get("Referrer-Policy"), "no-referrer")
	dung("noindex", "noindex" in dau.get("X-Robots-Tag", ""))
	dung("dữ liệu script không mang token", "a" * 43 not in ctx.du_lieu)
	dung("có chân trang pháp nhân", "0318561568" in ctx.chan_trang)
	x = _doc("vagabond/www/banh/xong.py")
	dung("mô đun khai no_cache", re.search(r"^no_cache = 1$", x, re.M))


@ca("#367 F /banh/xong không token: trang vỏ đọc lại biên nhận trong tab, không 404, không Pixel")
def _():
	ctx, loi, _l, _d = _get_context("www/banh/xong.py", {}, bn=None)
	la("không lỗi", loi, None)
	dung("không có pixel", "pixel_id" not in ctx.du_lieu)


# ------------------------------------------------------- G. Conversions API

@ca("#367 G CAPI: băm số 84 và email thường, không số gốc, không token, URL là trang đặt bánh")
def _():
	g = don_web.goi_su_kien("GuiDon", "ev-1", 1790000000, 650000, ["BAWC00139"], sdt="0931 224 334",
		email=" An.Nguyen@Example.com ", fbp="fb.1.1790000000000.123456789", fbc="rác",
		trinh_duyet="UA", ip="203.0.113.9")
	la("băm điện thoại dạng 84", g["user_data"]["ph"], [don_web.bam("84931224334")])
	la("băm email viết thường bỏ khoảng trắng", g["user_data"]["em"], [don_web.bam("an.nguyen@example.com")])
	dung("fbp đúng dạng thì gửi", g["user_data"]["fbp"].startswith("fb.1."))
	dung("fbc sai dạng thì bỏ", "fbc" not in g["user_data"])
	chu = json.dumps(g)
	dung("không có số điện thoại gốc", "0931224334" not in chu and "931224334" not in chu.replace(don_web.bam("84931224334"), ""))
	dung("không có email gốc", "example.com" not in chu)
	la("URL nguồn", g["event_source_url"], "https://order.thevagabondpatisserie.com/banh")
	la("giữ event_id", g["event_id"], "ev-1")
	la("giá trị VND", (g["custom_data"]["value"], g["custom_data"]["currency"]), (650000, "VND"))
	la("số điện thoại lạ thì không gửi ph", "ph" in don_web.goi_su_kien("x", "e", 1, 1, [], sdt="123")["user_data"], False)


@ca("#367 G Purchase chỉ đến từ hoá đơn ghi sổ; hook không bao giờ chặn ghi sổ")
def _():
	h = _doc("vagabond/hooks.py")
	dung("hook on_submit Sales Invoice nối thêm, không thay", '"vagabond.don_web.khi_ghi_so_hoa_don"' in h
		and "_cu_dw" in h)
	vet = []

	class Loi(Exception):
		pass

	def get_value(dt, dk, truong):
		vet.append(dk)
		raise Loi("CSDL hỏng")
	fr = types.SimpleNamespace(flags=types.SimpleNamespace(), db=types.SimpleNamespace(get_value=get_value),
		log_error=lambda **k: vet.append("log"), get_traceback=lambda: "")
	g = dict(frappe=fr, DOCTYPE="Vagabond Don Web", xep_capi=lambda *a, **k: vet.append("capi"),
		now_datetime=lambda: "2026-09-26 10:00:00")
	ham = nap("don_web.py", "khi_ghi_so_hoa_don", g)
	ham(D(name="SINV-1", custom_pancake_id="1", custom_pancake_display_id="91500", grand_total=686000))
	dung("lỗi bị nuốt và ghi log, không ném ra chặn ghi sổ", "log" in vet)
	vet.clear()
	ham(D(name="SINV-2", custom_pancake_id="", custom_pancake_display_id=""))
	la("hoá đơn quầy không mã Pancake thì không truy vấn gì", vet, [])
	dung("xếp Purchase sau commit", "xep_capi(ten, \"Purchase\", sau_commit=True)" in _doc("vagabond/don_web.py"))


@ca("#367 G gửi CAPI: đã gửi thì không gửi lại, lỗi không ghi token vào nhật ký")
def _():
	x = _doc("vagabond/don_web.py")
	than = x[x.index("def gui_capi("):x.index("def khi_ghi_so_hoa_don(")]
	dung("cờ đã gửi chặn gửi lần hai", "if d.get(truong):" in than)
	dung("thử lại có giãn cách", "for cho in (0, 5, 20):" in than)
	log = than[than.index("frappe.log_error("):]
	dung("nhật ký không có token", "tk" not in log.split(")")[0] and "access_token" not in log.split(")")[0])
	dung("không gửi khi kiểm thử tích hợp", "vagabond_kiem_that" in than)


# ------------------------------------------------------------------ H. đối soát

def _don_pc(**k):
	o = {"id": "sys-1", "display_id": "91500", "bill_phone_number": "0931224334",
		"inserted_at": "2026-09-25T06:00:30",
		"items": [{"quantity": 1, "variation_info": {"display_id": "BAWC00139"}}]}
	o.update(k)
	return o


@ca("#367 H đối soát chỉ ghép khi đúng MỘT đơn khớp số, giờ, món; không ghép lại đơn đã có chủ")
def _():
	from vagabond.ngay_pancake import unix_tu_iso
	tao = unix_tu_iso("2026-09-25T06:00:00")  # 13:00 giờ Việt Nam, giờ UTC không khai múi
	hang = [{"variation_id": "BAWC00139", "quantity": 1}]
	o, ly_do = don_web.ghep_don_pancake("+84931224334", tao, hang, [_don_pc()])
	la("một đơn khớp", (ly_do, o and o["display_id"]), ("khop", "91500"))
	o, ly_do = don_web.ghep_don_pancake("0931224334", tao, hang, [_don_pc(), _don_pc(id="sys-2", display_id="91501")])
	la("hai đơn cùng khớp thì không đoán", (o, ly_do), (None, "nhieu"))
	o, ly_do = don_web.ghep_don_pancake("0931224334", tao, hang, [_don_pc(items=[{"quantity": 2, "variation_info": {"display_id": "BAWC00139"}}])])
	la("khác số lượng thì không ghép", ly_do, "khong_thay")
	o, ly_do = don_web.ghep_don_pancake("0931224334", tao, hang, [_don_pc(inserted_at="2026-09-25T08:00:30")])
	la("tạo sau hơn một giờ thì không ghép", ly_do, "khong_thay")
	o, ly_do = don_web.ghep_don_pancake("0931224334", tao, hang, [_don_pc(bill_phone_number="0909000000")])
	la("khác số điện thoại thì không ghép", ly_do, "khong_thay")
	o, ly_do = don_web.ghep_don_pancake("0931224334", tao, hang, [_don_pc()], da_gan=["91500"])
	la("đơn đã thuộc bản ghi khác thì bỏ", ly_do, "khong_thay")
	for tt in (6, 7, "6"):
		o, ly_do = don_web.ghep_don_pancake("0931224334", tao, hang, [_don_pc(status=tt)])
		la("đơn Pancake đã huỷ hoặc xoá (%r) không là ứng viên" % tt, (o, ly_do), (None, "khong_thay"))
	o, ly_do = don_web.ghep_don_pancake("0931224334", tao, hang, [_don_pc(status=6), _don_pc(id="sys-2", display_id="91501", status=0)])
	la("một đơn huỷ cạnh một đơn sống: ghép đúng đơn sống", (ly_do, o and o["display_id"]), ("khop", "91501"))
	la("đọc giờ UTC không khai múi", unix_tu_iso("2026-09-25T06:00:00"), unix_tu_iso("2026-09-25T13:00:00+07:00"))
	la("giờ có phần lẻ của giây", unix_tu_iso("2026-09-25T06:00:00.123456"), tao)
	la("chuỗi hỏng", unix_tu_iso("hôm qua"), None)


def _frappe_bao_sales(url, nhan):
	"""Frappe giả cho _bao_sales: ghi lại set_value, webhook trả `nhan`."""
	ghi, goi = [], []
	fr = types.SimpleNamespace(
		db=types.SimpleNamespace(set_value=lambda *a, **k: ghi.append(a), commit=lambda: None),
		log_error=lambda **k: goi.append(("log", k.get("title"))),
		utils=types.SimpleNamespace(get_url_to_form=lambda dt, n: "/app/x/" + n))
	gui = types.ModuleType("vagabond.gui_thu")
	gui.ban_webhook = lambda cau, url=None: goi.append(("webhook", url)) or nhan
	fr.db.exists = lambda *a, **k: False
	g = dict(frappe=fr, cfg_o=lambda k: url, soan_tin_sales=lambda r, u: "tin", now_datetime=lambda: "T",
		DOCTYPE="Vagabond Don Web", add_to_date=lambda d, **k: d, PHUT_BAO_SALES=30,
		TIEU_DE_THIEU_WEBHOOK=don_web.TIEU_DE_THIEU_WEBHOOK)
	# Nạp THẬT cả hàm báo thiếu webhook, cùng bộ Frappe giả (vòng 3).
	g["_bao_thieu_webhook"] = lambda r: nap("don_web.py", "_bao_thieu_webhook", g)(r)
	return g, gui, ghi, goi


@ca("#367 H báo Sales: chỉ đóng dấu đã báo SAU khi Lark nhận, lỗi hay thiếu URL thì nhịp sau thử lại (Codex)")
def _():
	import sys
	r = {"name": "DW-1"}
	for url, nhan, mong_ghi, mong_ket in (("https://lark/x", True, 1, True), ("https://lark/x", False, 0, False), ("", True, 0, False)):
		g, gui, ghi, goi = _frappe_bao_sales(url, nhan)
		cu = sys.modules.get("vagabond.gui_thu")
		sys.modules["vagabond.gui_thu"] = gui
		try:
			ket = nap("don_web.py", "_bao_sales", g)(r)
		finally:
			if cu is None:
				sys.modules.pop("vagabond.gui_thu", None)
			else:
				sys.modules["vagabond.gui_thu"] = cu
		la("kết quả url=%r nhận=%r" % (url, nhan), ket, mong_ket)
		la("số lần đóng dấu url=%r nhận=%r" % (url, nhan), len(ghi), mong_ghi)
		if url and not nhan:
			dung("gửi hỏng thì ghi Error Log", ("log", "Don web: chua bao duoc nhom Sales qua Lark") in goi)
		if not url:
			la("thiếu URL thì không gọi webhook", [x for x in goi if x[0] == "webhook"], [])
	dung("mốc đóng dấu là ô da_bao_sales_luc", ghi == [] or ghi[0][2] == "da_bao_sales_luc")


@ca("#367 H nhịp đối soát: một bản ghi hỏng không chặn bản ghi sau, mỗi bản ghi tự chịu lỗi (Codex)")
def _():
	x = _doc("vagabond/don_web.py")
	than = x[x.index("def doi_soat_tu_dong("):x.index("def _doi_soat_mot(")]
	dung("gọi từng bản ghi qua _doi_soat_mot trong try riêng", "try:\n\t\t\t\t_doi_soat_mot(r, dons, gan)" in than)
	dung("lỗi một bản ghi thì rollback và ghi log rồi đi tiếp", "frappe.db.rollback()" in than and "Don web: doi soat mot ban ghi" in than)
	da, log = [], []
	def mot(r, dons, gan):
		if r["name"] == "DW-HONG":
			raise ValueError("snapshot hỏng")
		da.append(r["name"])
	fr = types.SimpleNamespace(
		flags=types.SimpleNamespace(vagabond_kiem_that=False),
		db=types.SimpleNamespace(rollback=lambda: None),
		log_error=lambda **k: log.append(k.get("title")), get_traceback=lambda: "tb",
		get_all=lambda *a, **k: [])
	ds = [{"name": "DW-1", "creation": "2026-09-25 13:00:00"}, {"name": "DW-HONG", "creation": "2026-09-25 13:00:00"}, {"name": "DW-2", "creation": "2026-09-25 13:00:00"}]
	kb = types.ModuleType("vagabond.kiem_banh")
	kb.LoiPancake = RuntimeError
	kb._keo_don = lambda *a, **k: []
	import sys
	cu = sys.modules.get("vagabond.kiem_banh")
	sys.modules["vagabond.kiem_banh"] = kb
	try:
		g = dict(frappe=fr, _dang_cho=lambda: ds, cfg=lambda: types.SimpleNamespace(pancake_shop_id="1"), key=lambda c, k: "k",
			_unix=lambda t: 0, now_datetime=lambda: "T", add_to_date=lambda *a, **k: "T0", DOCTYPE="Vagabond Don Web",
			_doi_soat_mot=mot)
		nap("don_web.py", "doi_soat_tu_dong", g)()
	finally:
		if cu is None:
			sys.modules.pop("vagabond.kiem_banh", None)
		else:
			sys.modules["vagabond.kiem_banh"] = cu
	la("bản ghi trước và sau bản hỏng đều được xử lý", da, ["DW-1", "DW-2"])
	la("bản hỏng có Error Log riêng", log, ["Don web: doi soat mot ban ghi"])


def _mot_ban_ghi(snap, phut_truoc, da_bao=None):
	"""Chạy _doi_soat_mot THẬT với Frappe giả; trả (số lần báo Sales, log, lỗi thoát ra)."""
	import datetime as _dt
	bay_gio = _dt.datetime(2026, 9, 26, 12, 0, 0)
	bao, log = [], []
	fr = types.SimpleNamespace(
		db=types.SimpleNamespace(rollback=lambda: log.append("rollback"), commit=lambda: None),
		log_error=lambda **k: log.append(k.get("title")), get_traceback=lambda: "tb")
	g = dict(frappe=fr, json=json, ghep_don_pancake=lambda *a, **k: (None, "khong_thay"), _unix=lambda t: 0,
		get_datetime=lambda x: x, now_datetime=lambda: bay_gio,
		add_to_date=lambda d, minutes=0, hours=0, days=0: d + _dt.timedelta(minutes=minutes, hours=hours, days=days),
		PHUT_BAO_SALES=30, DOCTYPE="Vagabond Don Web", _bao_sales=lambda r: bao.append(r["name"]) or True)
	if hasattr(don_web, "can_bao_sales"):
		g["can_bao_sales"] = don_web.can_bao_sales
	r = {"name": "DW-1", "dien_thoai": "0931224334", "snapshot": snap, "da_bao_sales_luc": da_bao,
		"creation": bay_gio - _dt.timedelta(minutes=phut_truoc)}
	try:
		nap("don_web.py", "_doi_soat_mot", g)(r, [], set())
		loi = ""
	except Exception as e:
		loi = type(e).__name__
	return len(bao), log, loi


@ca("#367 H vòng 3: bản ghi không ghép được (snapshot hỏng) vẫn được báo Sales khi quá giờ, chỉ một lần (Codex 3a7a37a)")
def _():
	n, log, loi = _mot_ban_ghi("{hỏng", 120)
	la("không để lỗi thoát ra, báo Sales đúng một lần", (loi, n), ("", 1))
	dung("có Error Log riêng cho bản ghi không ghép được", "Don web: ban ghi khong ghep duoc, van bao Sales" in log)
	la("rollback phần ghép hỏng rồi mới ghi log", log[:2], ["rollback", "Don web: ban ghi khong ghep duoc, van bao Sales"])
	la("chưa quá 30 phút thì chưa báo", _mot_ban_ghi("{hỏng", 5)[:1], (0,))
	la("đã báo rồi thì không báo lại", _mot_ban_ghi("{hỏng", 120, da_bao="2026-09-26 11:00:00")[:1], (0,))
	la("snapshot lành, không khớp, quá giờ: báo một lần như cũ", _mot_ban_ghi('{"mon": []}', 120)[:1], (1,))


@ca("#367 H vòng 3: một nguồn cho luật 'đến lúc báo Sales' (thuần)")
def _():
	import datetime as _dt
	t = _dt.datetime(2026, 9, 26, 12, 0, 0)
	k = don_web.can_bao_sales
	la("quá 30 phút, chưa báo", k({"creation": t - _dt.timedelta(minutes=31)}, t), True)
	la("đúng 30 phút", k({"creation": t - _dt.timedelta(minutes=30)}, t), True)
	la("mới 29 phút", k({"creation": t - _dt.timedelta(minutes=29)}, t), False)
	la("đã báo", k({"creation": t - _dt.timedelta(hours=3), "da_bao_sales_luc": "x"}, t), False)
	la("ngày dạng chuỗi", k({"creation": "2026-09-26 11:00:00"}, t), True)
	x = _doc("vagabond/don_web.py")
	dung("không còn chỗ nào tự so mốc báo Sales ngoài can_bao_sales",
		"minutes=-PHUT_BAO_SALES" not in x and x.count("can_bao_sales(") == 2)


@ca("#367 H vòng 3: thiếu webhook nhóm Sales thì có Error Log hành động được, giãn 6 giờ một lần (Codex 3a7a37a)")
def _():
	import sys
	for co_gan_day, mong in ((False, 1), (True, 0)):
		g, gui, ghi, goi = _frappe_bao_sales("", True)
		hoi = []
		g["frappe"].db.exists = lambda dt, loc=None: hoi.append((dt, loc)) or co_gan_day
		g["add_to_date"] = lambda d, hours=0, **k: ("truoc", hours)
		cu = sys.modules.get("vagabond.gui_thu")
		sys.modules["vagabond.gui_thu"] = gui
		try:
			ket = nap("don_web.py", "_bao_sales", g)({"name": "DW-9"})
		finally:
			if cu is None:
				sys.modules.pop("vagabond.gui_thu", None)
			else:
				sys.modules["vagabond.gui_thu"] = cu
		la("vẫn chưa coi là đã báo (co_gan_day=%r)" % co_gan_day, (ket, len(ghi)), (False, 0))
		la("số Error Log thiếu webhook (co_gan_day=%r)" % co_gan_day,
			len([x for x in goi if x == ("log", "Don web: chua cau hinh webhook nhom Sales")]), mong)
		dung("giãn theo Error Log cùng tiêu đề trong 6 giờ", bool(hoi) and hoi[0][0] == "Error Log"
			and (hoi[0][1] or {}).get("method") == "Don web: chua cau hinh webhook nhom Sales")


@ca("#367 H tin Lark cho Sales đủ để gọi khách và chỉ đường xử lý tay")
def _():
	t = don_web.soan_tin_sales({"name": "DW-1", "ho_ten": "An", "dien_thoai": "0931224334",
		"tien_banh": 650000, "ngay_nhan": "2026-09-26 13:00:00"}, "https://erp/app/x")
	for chu in ("DW-1", "0931224334", "650.000 đ", "Thứ 7, 26/09 13h - 15h", "mã đơn Pancake", "https://erp/app/x"):
		dung("có " + chu, chu in t)
	dung("không dấu gạch dài", chr(0x2014) not in t and chr(0x2013) not in t)
	h = _doc("vagabond/hooks.py")
	dung("nhịp 5 phút nối thêm", '"vagabond.don_web.doi_soat_tu_dong"' in h and 'setdefault("*/5 * * * *", [])' in h)


@ca("#367 H sửa tay trên Desk: chỉ Đã nhận khi có mã Pancake, không ai đặt tay Đã ghi sổ")
def _():
	c = don_web.chuyen_hop_le
	dung("chờ đối soát sang đã nhận khi có mã", c("Cho doi soat", "Da nhan", "91500"))
	dung("thiếu mã thì không", not c("Cho doi soat", "Da nhan", ""))
	dung("huỷ được khi chưa ghi sổ", c("Da nhan", "Da huy", ""))
	dung("đã ghi sổ không huỷ tay", not c("Da ghi so", "Da huy", ""))
	dung("không đặt tay đã ghi sổ", not c("Da nhan", "Da ghi so", "1"))
	dung("không quay về đang gửi", not c("Cho doi soat", "Dang gui", ""))
	dung("máy đi mọi đường", c("Da nhan", "Da ghi so", "", may=True))
	for o in ("token_hash", "muoi", "snapshot", "tien_banh", "event_id_gui_don"):
		dung("khoá tay ô " + o, o in don_web.KHONG_DOI)


# --------------------------------------------------------------------- I. ảnh

@ca("#367 I ảnh: ERP trước Pancake, rồi ảnh dòng, rồi ảnh nền; bỏ ảnh riêng tư, tối đa 5")
def _():
	c = anh_web.chon_anh
	la("ERP trước", c("/files/erp.jpg", ["https://pc/1.jpg"], "https://pc/dong.jpg")[0], "/files/erp.jpg")
	la("thiếu ERP thì Pancake", c("", ["https://pc/1.jpg"], "https://pc/dong.jpg")[0], "https://pc/1.jpg")
	la("thiếu cả hai thì ảnh dòng", c(None, [], "https://pc/dong.jpg")[0], "https://pc/dong.jpg")
	la("không có gì thì ảnh nền, không ô đen", c(None, [], None)[0], anh_web.ANH_NEN)
	la("ảnh riêng tư bị bỏ", c("/private/files/a.jpg", ["https://pc/1.jpg"])[0], "https://pc/1.jpg")
	la("nhóm nhiều size: ảnh ERP theo thứ tự size", c(["", "/files/16.jpg", "/files/18.jpg"], ["https://pc/1.jpg"])[1][:2],
		["/files/16.jpg", "/files/18.jpg"])
	la("trùng chỉ giữ một", c("/files/a.jpg", ["/files/a.jpg"], "/files/a.jpg")[1], ["/files/a.jpg"])
	la("tối đa 5", len(c(["/files/%d.jpg" % i for i in range(9)])[1]), 5)


@ca("#367 I nhánh Hôm nay và Đặt trước: ảnh ERP thắng ảnh Pancake, kể cả khi chưa có khoá Pancake")
def _():
	for co_khoa in (True, False):
		g = dict(cfg=lambda: D(pancake_shop_id="67355" if co_khoa else ""), key=lambda c, f: "k" if co_khoa else "",
			_sp_pancake=lambda c, k, ma: {"anhs": ["https://pc/%s.jpg" % ma], "mo_ta": "Giới thiệu\nLớp một"},
			chon_anh=anh_web.chon_anh)
		ham = nap("kiem_banh.py", "_bo_anh_mo_ta", g)
		nhom = [{"ten": "Candle", "anh": "", "sizes": [
			{"ma": "A12", "_anh_erp": "", "_anh_dong": "https://pc/dong.jpg"},
			{"ma": "A16", "_anh_erp": "/files/candle16.jpg", "_anh_dong": ""}]}]
		ham(nhom)
		la("ảnh chính là ảnh ERP (khoá Pancake %s)" % co_khoa, nhom[0]["anh"], "/files/candle16.jpg")
		dung("không lộ khoá riêng ra khách", all("_anh_erp" not in s and "_anh_dong" not in s for s in nhom[0]["sizes"]))
		if not co_khoa:
			la("không khoá Pancake vẫn có ảnh dòng làm ảnh phụ", nhom[0]["anhs"], ["/files/candle16.jpg", "https://pc/dong.jpg"])


@ca("#367 I không nhánh ảnh web nào còn tự chọn thứ tự riêng")
def _():
	cam = ('d.hinh or x.get("image")', 'b.hinh or x.get("image")', 'anh_pancake.get(d.ma_hang) or d.hinh',
		"anh = anhs[0] if anhs else", "Anh dau tien cua Pancake la anh dang dung")
	for tep in ("vagabond/kiem_banh.py", "vagabond/kiem_kho.py", "vagabond/mua_vu.py"):
		x = _doc(tep)
		for c in cam:
			dung("%s không còn %s" % (tep, c), c not in x)
		dung(tep + " đi qua chon_anh", "chon_anh(" in x)


# ----------------------------------------------------------------- J. chính sách

def _nd_mau(**cs):
	return {"khoi": [], "chinh_sach": cs}


@ca("#367 J chính sách: nhận ba khoá VN/EN, chặn khoá lạ, chặn bật hiện khi chưa có chữ")
def _():
	noi_dung_web.chuan_hoa(_nd_mau(dieu_khoan={"hien": False, "vn": "# Điều khoản", "en": ""}))
	for sai in (_nd_mau(la={"hien": False, "vn": "", "en": ""}),
			_nd_mau(dieu_khoan={"hien": "true", "vn": "a", "en": ""}),
			_nd_mau(dieu_khoan={"hien": True, "vn": "  ", "en": ""}),
			_nd_mau(dieu_khoan={"hien": False, "vn": "a" * 30001, "en": ""}),
			_nd_mau(dieu_khoan={"hien": False, "vn": "a", "en": "", "html": "<b>"}),
			{"khoi": [], "gia": 1}):
		nem("chặn %s" % str(sai)[:40], lambda sai=sai: noi_dung_web.chuan_hoa(sai), (ValueError, TypeError))
	la("dữ liệu cũ chỉ có khối vẫn nhận", noi_dung_web.chuan_hoa({"khoi": []}), {"khoi": []})


@ca("#367 J xuất bản bị chặn khi trang bật hiện còn chỗ trong ngoặc vuông; liên kết Markdown không tính")
def _():
	la("liên kết Markdown không phải chỗ trống", noi_dung_web.cho_trong("xem [trang](/dieu-khoan) và [email]"), ["[email]"])
	nd = _nd_mau(chinh_sach_bao_mat={"hien": True, "vn": "Liên hệ: [số điện thoại]", "en": ""})
	dung("chặn xuất bản", "Chưa xuất bản được" in noi_dung_web.loi_xuat_ban(nd))
	nd = _nd_mau(chinh_sach_bao_mat={"hien": False, "vn": "Liên hệ: [số điện thoại]", "en": ""})
	la("trang còn ẩn thì không chặn", noi_dung_web.loi_xuat_ban(nd), "")
	x = _doc("vagabond/noi_dung_web.py")
	than = x[x.index("def luu("):]
	dung("luu kiểm trước khi ghi", than.index("loi_xuat_ban(nd)") < than.index("d.ban_nhap = json.dumps"))


@ca("#367 J bản nháp đã duyệt nằm nguyên văn trong repo, gieo vào NHÁP, không đụng bản công khai")
def _():
	for khoa in noi_dung_web.CHINH_SACH:
		t = _doc("vagabond/du_lieu/chinh_sach/%s.md" % khoa)
		dung(khoa + " có chữ", len(t) > 800)
		dung(khoa + " còn chỗ cho marketing điền", noi_dung_web.cho_trong(t))
		dung(khoa + " không dấu gạch dài", chr(0x2014) not in t and chr(0x2013) not in t)
	t = _doc("vagabond/du_lieu/chinh_sach/chinh_sach_bao_mat.md")
	for chu in ("0318561568", "Meta Pixel", "Nghị định 13/2023/NĐ-CP", "băm một chiều", "Ahamove"):
		dung("bảo mật có " + chu, chu in t)
	ghi = {}

	class Doc(D):
		def is_new(self):
			return False

		def save(self, **k):
			ghi["nhap"] = json.loads(self.ban_nhap)
			ghi["cong_khai"] = self.ban_cong_khai

	cong = json.dumps({"khoi": [{"id": "k"}]})
	doc = Doc(ban_nhap=json.dumps({"khoi": []}), ban_cong_khai=cong, flags=D())
	fr = types.SimpleNamespace(db=types.SimpleNamespace(exists=lambda *a: True))
	g = dict(frappe=fr, DOCTYPE="Vagabond Noi Dung Web", TEN="order", MAC_DINH=noi_dung_web.MAC_DINH,
		CHINH_SACH=noi_dung_web.CHINH_SACH, chuan_hoa=noi_dung_web.chuan_hoa, _doc=lambda: doc,
		json=json, copy=__import__("copy"))
	gieo = nap("noi_dung_web.py", "gieo_chinh_sach", g)
	dung("gieo lần đầu", gieo({"dieu_khoan": "# Điều khoản"}))
	la("vào nháp, còn ẩn", ghi["nhap"]["chinh_sach"]["dieu_khoan"], {"hien": False, "vn": "# Điều khoản", "en": ""})
	la("bản công khai giữ nguyên", ghi["cong_khai"], cong)
	doc.ban_nhap = json.dumps({"khoi": [], "chinh_sach": {"dieu_khoan": {"hien": True, "vn": "Đã sửa", "en": ""}}})
	dung("chạy lại không đè bài marketing đã sửa", not gieo({"dieu_khoan": "# Điều khoản"}))


@ca("#367 J công khai: trang đặt bánh không tải chính sách; trang chưa bật hiện là 404")
def _():
	x = _doc("vagabond/noi_dung_web.py")
	than = x[x.index("def cong_khai("):x.index("def chinh_sach_dang_hien(")]
	dung("bỏ chinh_sach khỏi dữ liệu trang đặt bánh", 'ra.pop("chinh_sach", None)' in than)
	cs = {"chinh_sach_bao_mat": {"hien": True, "vn": "# A", "en": ""}, "dieu_khoan": {"hien": False, "vn": "# B", "en": ""}}
	g = dict(_ban_cong_khai=lambda: {"khoi": [], "chinh_sach": cs}, CHINH_SACH=noi_dung_web.CHINH_SACH)
	la("chân trang chỉ trang đang hiện", [c["khoa"] for c in nap("noi_dung_web.py", "chinh_sach_dang_hien", g)()],
		["chinh_sach_bao_mat"])
	goi = []
	fu = types.ModuleType("frappe.utils")
	fu.md_to_html = lambda md: "<p>" + md + "</p>"
	fh = types.ModuleType("frappe.utils.html_utils")
	fh.sanitize_html = lambda h, always_sanitize=False: goi.append(always_sanitize) or h.replace("<script>", "")
	import sys
	cu = {k: sys.modules.get(k) for k in ("frappe.utils", "frappe.utils.html_utils")}
	sys.modules["frappe.utils"], sys.modules["frappe.utils.html_utils"] = fu, fh
	try:
		tr = nap("noi_dung_web.py", "trang_chinh_sach", g)
		la("chưa bật hiện là None (404)", tr("dieu_khoan"), None)
		la("khoá lạ là None", tr("khong_co"), None)
		r = tr("chinh_sach_bao_mat")
		dung("bật hiện thì có HTML", r and "<p>" in r["html"])
		la("luôn qua sanitize_html bắt buộc", goi, [True])
	finally:
		for k, v in cu.items():
			if v is None:
				sys.modules.pop(k, None)
			else:
				sys.modules[k] = v
	ctx, loi, _l, _d = _get_context("www/chinh_sach.py", {}, cs=None, duong="/dieu-khoan")
	la("trang công khai 404 khi chưa xuất bản", loi, "404")


@ca("#367 J khoá chính sách suy từ đường dẫn, không dựa vào defaults của luật định tuyến (Codex)")
def _():
	k = noi_dung_web.khoa_tu_duong
	la("bảo mật", k("/chinh-sach-bao-mat"), "chinh_sach_bao_mat")
	la("điều khoản", k("/dieu-khoan"), "dieu_khoan")
	la("giao hàng", k("/giao-hang-doi-tra"), "giao_hang_doi_tra")
	la("không gạch chéo đầu, có tham số", k("dieu-khoan?ngon_ngu=en"), "dieu_khoan")
	la("gạch chéo cuối", k("/dieu-khoan/"), "dieu_khoan")
	la("đường lạ là rỗng", k("/chinh-sach"), "")
	la("rỗng là rỗng", k(""), "")
	h = _doc("vagabond/hooks.py")
	dung("luật không còn defaults", '"defaults"' not in h[h.index("website_route_rules = list("):])
	trang = {"ten": "Điều khoản sử dụng", "html": "<p>A</p>", "ngon_ngu": "vn", "co_en": False}
	for duong, khoa in (("/chinh-sach-bao-mat", "chinh_sach_bao_mat"), ("/dieu-khoan", "dieu_khoan"),
			("/giao-hang-doi-tra", "giao_hang_doi_tra")):
		goi = []
		ctx, loi, _l, _d = _get_context("www/chinh_sach.py", {}, cs=trang, duong=duong)
		la("mở được " + duong, loi, None)
		dung("có thân trang " + duong, "<p>A</p>" in (ctx.get("than") or ""))
	_c, loi, _l, _d = _get_context("www/chinh_sach.py", {"khoa": "dieu_khoan"}, cs=trang, duong="/chinh-sach")
	la("form_dict khoa không thay được đường dẫn: đường lạ là 404", loi, "404")


@ca("#367 J ba đường chính sách và biên nhận: nối thêm vào luật định tuyến, thuộc miền khách")
def _():
	h = _doc("vagabond/hooks.py")
	for duong, dich in (("/banh/xong/<token>", "banh/xong"), ("/chinh-sach-bao-mat", "chinh-sach"),
			("/dieu-khoan", "chinh-sach"), ("/giao-hang-doi-tra", "chinh-sach")):
		dung("có luật " + duong, '"from_route": "%s", "to_route": "%s"' % (duong, dich) in h)
	dung("giữ luật của app /bep", "website_route_rules = list(website_route_rules) + [" in h)
	from vagabond import ten_mien
	for d in ("/chinh-sach-bao-mat", "/dieu-khoan", "/giao-hang-doi-tra", "/banh/xong/" + "a" * 43):
		la("miền khách giữ " + d, ten_mien.dich_chuyen_huong("order.thevagabondpatisserie.com", d), "")
	from vagabond.duong_app import bang_duong
	dung("không slug app nào trùng đường mới", not set(bang_duong()) & {"chinh-sach", "chinh-sach-bao-mat", "dieu-khoan", "giao-hang-doi-tra"})


@ca("#367 J bảng marketing: khách vãng lai về trang đăng nhập rồi quay lại, thiếu vai thì trang báo quyền")
def _():
	q = noi_dung_web.quyet_vao_bang
	la("khách vãng lai", q("Guest", []), "dang_nhap")
	la("không vai", q("vu@x.com", ["Website User"]), "khong_quyen")
	la("Marketing", q("vu@x.com", ["Marketing"]), "vao")
	la("System Manager", q("a@x.com", ["System Manager"]), "vao")
	_c, loi, local, dau = _get_context("www/bien_tap_web.py", {}, nguoi="Guest")
	la("chuyển hướng đúng đường quay lại", loi, "302:/login?redirect-to=/bien-tap-web")
	ctx, loi, local, dau = _get_context("www/bien_tap_web.py", {}, nguoi="vu@x.com", vai=["Website User"])
	la("thiếu vai: không lỗi, hiện trang báo", (loi, ctx.khong_quyen), (None, 1))
	dung("không đệm theo phiên", local.no_cache == 1 and "no-store" in dau.get("Cache-Control", ""))
	ctx, loi, _l, _d = _get_context("www/bien_tap_web.py", {}, nguoi="vu@x.com", vai=["Marketing"])
	la("có vai vào bảng", (loi, ctx.khong_quyen, ctx.ten_nguoi), (None, 0, "Minh Vũ"))
	ht = _doc("vagabond/www/bien-tap-web.html")
	dung("có nút Đăng xuất và tên người", 'href="/logout"' in ht and "{{ ten_nguoi }}" in ht)
	dung("trang thiếu quyền không nạp mã editor", ht.index("{% if khong_quyen %}") < ht.index("{% else %}") < ht.index("bien-tap.js"))


# ------------------------------------------------------------- K. cửa và cấu hình

@ca("#367 K cấu hình công khai không bao giờ mang token CAPI; Settings có đủ ô")
def _():
	x = _doc("vagabond/don_web.py")
	than = x[x.index("def cau_hinh_web("):x.index("def tim_trung(")]
	dung("không đọc token trong cấu hình công khai", "meta_capi_token" not in than and "key(" not in than)
	st = json.loads(_doc("vagabond/vagabond/doctype/vagabond_settings/vagabond_settings.json"))
	o = {f["fieldname"]: f for f in st["fields"]}
	for ten in ("mien_phi_giao_tu", "meta_pixel_id", "meta_capi_token", "web_dien_thoai", "web_email", "webhook_don_web"):
		dung("Settings có " + ten, ten in o)
	la("token là ô mật khẩu", o["meta_capi_token"]["fieldtype"], "Password")
	dt = json.loads(_doc("vagabond/vagabond/doctype/vagabond_don_web/vagabond_don_web.json"))
	f = {x["fieldname"]: x for x in dt["fields"]}
	dung("băm token là duy nhất", f["token_hash"].get("unique") == 1)
	dung("không có ô lưu token gốc", "token" not in f)
	for o2 in ("khoa_chong_trung", "pancake_display_id", "pancake_id", "dien_thoai"):
		dung("có chỉ mục " + o2, f[o2].get("search_index") == 1)
	la("tên theo mẫu của repo", dt["autoname"], "format:DW-{YY}{MM}-{#####}")


@ca("#367 K patch gieo chỉ điền ô trống, không chặn migrate khi lỗi")
def _():
	x = _doc("vagabond/patches/don_web_367.py")
	dung("chỉ khi chưa có dòng", "if _chua_co_dong(ten):" in x)
	dung("ngưỡng 1.000.000", '"mien_phi_giao_tu": 1000000' in x)
	la("hai khối bắt lỗi", x.count("except Exception:"), 2)
	p = _doc("vagabond/patches.txt")
	dung("patch đăng ký", "vagabond.patches.don_web_367" in p)


# ------------------------------------------- L. trang đặt bánh chạy thật trong node
#
# Nạp CẢ banh.html vào node (gia_lap_trang.js), dựng đúng chuỗi thao tác của
# khách. Không gọi thêm hàm "cho chắc" nào ngoài chuỗi đó (bài học #205).

from vagabond.khung.kiem_thu.thu_trang_dat_banh import _chay  # noqa: E402

GIO_CHUA_DONG_Y = """
CART.push({id:'BAWC00139',k:'Candle',cm:12,qty:1,adds:[],wish:'',price:650000});
EL('#f-name').value='Nguyen Van A';
EL('#f-phone').value='0912345678';
EL('#f-addr').value='9 Tran Cao Van, Quan 1, TP HCM';
setMode('ship');
var i13=SLOTS.findIndex(function(s){return s.from===13;});
pick(2); pickSlot(i13);
openCoUI();
await CHO_XONG();
"""
DON = """
function cacDon(){ return GHI.goiMang.filter(function(x){return x.opt&&x.opt.method==='POST';})
  .map(function(g){return JSON.parse(JSON.parse(g.opt.body).don);}); }
"""
CAU_HINH = """
apDungCauHinh({pixel_id:'', mien_phi_tu:1000000, lien_he:{dien_thoai:'0931 224 334', dien_thoai_so:'0931224334'},
  chinh_sach:[{khoa:'chinh_sach_bao_mat', ten:'Chính sách bảo mật', duong:'/chinh-sach-bao-mat'},
              {khoa:'x', ten:'Lạ', duong:'javascript:alert(1)'}],
  quan:[{ma:'q3', ten:'Quận 3', lat:10.7843, lng:106.6844}]});
"""


@ca("#367 L chưa tick đồng ý thì KHÔNG gửi; tick rồi thì gửi kèm nonce, đồng ý, cách thanh toán")
def _():
	r = _chay("2026-09-24T08:00:00", GIO_CHUA_DONG_Y + DON + r"""
GHI.goiMang.length=0; submitOrder();
var a={so:cacDon().length, tro:GHI.troVao};
tgl('dongy'); setPay('card');
GHI.goiMang.length=0; submitOrder(); await CHO_XONG();
var d=cacDon()[0]||{};
RA({a:a, dong_y:d.dong_y, nonce:d.nonce, tt:d.thanh_toan, aria:EL('#c-dongy').getAttribute('aria-checked')});
""")
	la("chưa đồng ý không gửi", r["a"]["so"], 0)
	la("con trỏ về ô đồng ý", r["a"]["tro"], "#c-dongy")
	la("gửi kèm đồng ý", r["dong_y"], True)
	dung("nonce 32 ký tự base64url", bool(re.match(r"^[A-Za-z0-9_-]{32}$", r["nonce"] or "")))
	la("gửi cách thanh toán cho biên nhận", r["tt"], "card")
	la("ô đồng ý báo trạng thái cho trình đọc màn hình", r["aria"], "true")


@ca("#367 L gửi lỗi rồi gửi lại: CÙNG nonce để máy chủ nhận ra cùng một đơn; thành công thì sang biên nhận")
def _():
	r = _chay("2026-09-24T08:00:00", GIO_CHUA_DONG_Y + DON + r"""
tgl('dongy');
var lan=0;
GHI.traLoi=function(url,opt){
  if(opt&&opt.method==='POST'){ lan++;
    return lan===1 ? {message:{ok:0, ly_do:'pancake_loi'}}
                   : {message:{ok:1, ma_yeu_cau:'DW-2609-00001', duong_dan:'/banh/xong/'+'a'.repeat(43)}}; }
  return null; };
GHI.goiMang.length=0; await submitOrder();
var hint=EL('#sendHint').innerHTML;
await submitOrder();
var ds=cacDon();
RA({so:ds.length, cung:ds[0].nonce===ds[1].nonce, hint:hint, chuyen:GHI.chuyenTrang, gio:CART.length, nonce_sau:CO.nonce});
""")
	la("hai lần gửi", r["so"], 2)
	dung("cùng nonce", r["cung"])
	dung("lần lỗi nói rõ chưa gửi được", "Chưa gửi được đơn" in r["hint"])
	la("thành công thì chuyển sang biên nhận", r["chuyen"], ["/banh/xong/" + "a" * 43])
	la("giỏ được dọn", r["gio"], 0)
	la("nonce bỏ để lần đặt sau là đơn mới", r["nonce_sau"], "")


@ca("#367 L máy chủ trả đường dẫn lạ thì KHÔNG chuyển trang")
def _():
	r = _chay("2026-09-24T08:00:00", GIO_CHUA_DONG_Y + DON + r"""
tgl('dongy');
GHI.traLoi=function(url,opt){ return (opt&&opt.method==='POST') ? {message:{ok:1, duong_dan:'https://evil.example/x'}} : null; };
await submitOrder();
RA({chuyen:GHI.chuyenTrang, hint:EL('#sendHint').innerHTML});
""")
	la("không chuyển", r["chuyen"], [])
	dung("vẫn báo đã nhận", "Tiệm đã nhận đơn" in r["hint"])


@ca("#367 L thanh giỏ: 999.999 nhắc ngưỡng, đúng 1.000.000 báo miễn phí; bảng tóm tắt không cộng phí")
def _():
	r = _chay("2026-09-24T08:00:00", CAU_HINH + r"""
CART.push({id:'A',k:'A',cm:12,qty:1,adds:[],wish:'',price:999999});
drawBar(); var a=EL('#barTxt').innerHTML;
CART[0].price=1000000; drawBar(); var b=EL('#barTxt').innerHTML;
EL('#f-addr').value='9 Tran Cao Van, Quan 1, TP HCM'; setMode('ship'); await CHO_XONG();
var S=coTotals();
RA({a:a, b:b, sum:EL('#sum').innerHTML, tong:S.total, hint:EL('#shipHint').innerHTML});
""")
	dung("dưới ngưỡng nhắc mức", "Miễn phí giao cho đơn từ 1.000.000 đ" in r["a"])
	dung("đủ ngưỡng báo được miễn", "Đơn này được miễn phí giao" in r["b"])
	dung("bảng tóm tắt ghi Miễn phí giao", "<b>Miễn phí giao</b>" in r["sum"])
	la("tổng không cộng phí giao", r["tong"], 1000000)
	dung("gợi ý dưới địa chỉ cũng nói miễn phí", "miễn phí giao" in r["hint"])


@ca("#367 L chọn khu vực là thấy phí giao dự kiến, gõ đủ địa chỉ thì ra số chính xác")
def _():
	r = _chay("2026-09-24T08:00:00", CAU_HINH + r"""
CART.push({id:'A',k:'A',cm:12,qty:1,adds:[],wish:'',price:500000});
GHI.traLoi=function(url){ if(url.indexOf('phi_giao')<0) return null;
  return {message:{ok:1,total_fee: url.indexOf('lat=10.7843')>=0 ? 30000 : 41000, diem_lay:'Bep Vagabond'}}; };
setMode('ship'); await CHO_XONG();
EL('#f-quan').value='q3'; chonQuan(); await CHO_XONG();
var duKien={sum:EL('#sum').innerHTML, tt:CO.shipTrangThai, url:GHI.goiMang.map(function(g){return g.url;}).filter(function(u){return u.indexOf('phi_giao')>=0;}).pop()};
EL('#f-addr').value='12 Ly Tu Trong, Quan 1, TP HCM'; quoteShip(); await CHO_XONG();
RA({duKien:duKien, tt:CO.shipTrangThai, ship:CO.ship, sum:EL('#sum').innerHTML, quan:EL('#quanBlock').style.display});
""")
	la("khối khu vực hiện khi có danh sách", r["quan"], "")
	la("dự kiến", r["duKien"]["tt"], "du_kien")
	dung("hỏi bằng tâm khu vực", "lat=10.7843" in r["duKien"]["url"])
	dung("bảng tóm tắt ghi Phí giao dự kiến", "Phí giao dự kiến" in r["duKien"]["sum"] and "30.000 đ" in r["duKien"]["sum"])
	la("gõ đủ địa chỉ thì chính xác", (r["tt"], r["ship"]), ("chinh_xac", 41000))
	dung("không còn chữ dự kiến", "dự kiến" not in r["sum"])


@ca("#367 L kết quả phí của lần hỏi CŨ về muộn không đè lên lần hỏi mới")
def _():
	r = _chay("2026-09-24T08:00:00", CAU_HINH + r"""
CART.push({id:'A',k:'A',cm:12,qty:1,adds:[],wish:'',price:500000});
setMode('ship'); await CHO_XONG();
var mo=null;
GHI.traLoi=function(url){ if(url.indexOf('phi_giao')<0) return null;
  if(url.indexOf('lat=10.7843')>=0) return new Promise(function(r){ mo=function(){ r({message:{ok:1,total_fee:99000}}); }; });
  return {message:{ok:1,total_fee:41000}}; };
EL('#f-quan').value='q3'; chonQuan();             /* lan hoi 1: tre */
EL('#f-addr').value='12 Ly Tu Trong, Quan 1, TP HCM'; quoteShip();   /* lan hoi 2: ve ngay */
await Promise.resolve(); await Promise.resolve(); await Promise.resolve();
mo();                                              /* lan 1 ve SAU */
await CHO_XONG();
RA({tt:CO.shipTrangThai, ship:CO.ship});
""")
	la("giữ số của lần hỏi mới nhất", (r["tt"], r["ship"]), ("chinh_xac", 41000))


@ca("#367 L Ahamove không báo được: không hiện 0, không hiện miễn phí khi chưa đủ ngưỡng")
def _():
	r = _chay("2026-09-24T08:00:00", CAU_HINH + r"""
CART.push({id:'A',k:'A',cm:12,qty:1,adds:[],wish:'',price:500000});
GHI.traLoi=function(url){ return url.indexOf('phi_giao')>=0 ? {message:{ok:0, ly_do:'ahamove_loi'}} : null; };
EL('#f-addr').value='9 Tran Cao Van, Quan 1, TP HCM'; setMode('ship'); await CHO_XONG();
RA({sum:EL('#sum').innerHTML, hint:EL('#shipHint').innerHTML, tong:coTotals().total});
""")
	dung("dòng phí nói Sales báo", "Sales báo phí khi xác nhận" in r["sum"])
	dung("nhãn tổng nói chưa gồm phí", "Tạm tính, chưa gồm phí giao" in r["sum"])
	dung("không nói miễn phí", "iễn phí" not in r["sum"] and "iễn phí" not in r["hint"])
	la("tổng chỉ tiền bánh", r["tong"], 500000)


@ca("#367 L nút +: một size thì thêm thẳng, nhiều size thì mở trang chi tiết, không đoán size")
def _():
	r = _chay("2026-09-24T08:00:00", r"""
TODAY={'BAWC00139':3,'BAWC00140':0}; TON_NAP_XONG=true;
var moi=null; openSheet=function(k){ moi=k; };
var c=CAKES.find(function(x){return x.k==='CANDLE';});
themNhanh('CANDLE',1);
var mot={gio:CART.length, ma:CART[0]&&CART[0].id, bar:EL('#bar').classList.contains('nhich')};
TODAY={'BAWC00139':3,'BAWC00140':2};
themNhanh('CANDLE',1);
RA({mot:mot, nhieu:{gio:CART.length, mo:moi}, html:card(c,true)});
""")
	la("một size thêm thẳng", (r["mot"]["gio"], r["mot"]["ma"]), (1, "BAWC00139"))
	dung("thanh giỏ nhích", r["mot"]["bar"])
	la("nhiều size mở trang chi tiết", r["nhieu"], {"gio": 1, "mo": "CANDLE"})
	dung("nút + nằm ngoài nút thẻ", '</button><button class="c-them"' in r["html"])
	dung("ảnh hỏng thay bằng ảnh nền", 'onerror="anhHong(this)"' in r["html"])


@ca("#367 L Pixel: đủ bốn mốc xem, thêm giỏ, bắt đầu đặt; xem trước của marketing KHÔNG nạp Pixel")
def _():
	r = _chay("2026-09-24T08:00:00", r"""
var ev=[];
window.fbq=function(){ ev.push(Array.prototype.slice.call(arguments)); };
PIXEL_ID='123';
var c=CAKES.find(function(x){return x.k==='CANDLE';});
renderSheet(c); cur=c; curSize=c.sizes[0]; addToCart();
openCoUI(); closeCoUI(); openCoUI();      /* mo dong gio hai lan */
var ten=ev.map(function(e){return e[1];});
PIXEL_ID=''; window.fbq=undefined; location.search='?bien_tap=1';
apDungCauHinh({pixel_id:'999', mien_phi_tu:0, quan:[], chinh_sach:[]});
RA({ten:ten, gia:(ev.filter(function(e){return e[1]==='AddToCart';})[0]||[])[2], xem_truoc:PIXEL_ID});
""")
	la("đủ ba sự kiện trình duyệt theo thứ tự", r["ten"], ["ViewContent", "AddToCart", "InitiateCheckout"])
	la("thêm giỏ kèm giá VND", (r["gia"]["value"], r["gia"]["currency"]), (650000, "VND"))
	la("xem trước không nạp Pixel", r["xem_truoc"], "")


@ca("#367 L khách đến từ quảng cáo (fbclid) mà chưa có cookie _fbc: vẫn gửi fbc đúng dạng")
def _():
	r = _chay("2026-09-24T08:00:00", GIO_CHUA_DONG_Y + DON + r"""
location.search='?fbclid=AbC_123'; document.cookie='_fbp=fb.1.1790000000000.555';
tgl('dongy'); GHI.goiMang.length=0; submitOrder(); await CHO_XONG();
var d=cacDon()[0];
RA({fbp:d.fbp, fbc:d.fbc});
""")
	la("fbp từ cookie", r["fbp"], "fb.1.1790000000000.555")
	dung("fbc dựng đúng dạng Meta", bool(re.match(r"^fb\.1\.\d{13}\.AbC_123$", r["fbc"] or "")))


@ca("#367 L chân trang: pháp nhân viết thẳng trong HTML, chỉ đường dẫn chính sách an toàn và đang hiện")
def _():
	w = _doc("vagabond/trang/banh.html")
	chan = w[w.index("<footer>"):w.index("</footer>")]
	for chu in ("Công ty TNHH Patisserie Vagabond", "Mã số thuế 0318561568", "9 Trần Cao Vân", "307/1 Nguyễn Văn Trỗi"):
		dung("HTML tĩnh có " + chu, chu in chan)
	r = _chay("2026-09-24T08:00:00", CAU_HINH + r"""
RA({cs:EL('#fChinhSach').innerHTML, doc:EL('#docChinhSach').innerHTML, lh:EL('#fLienHe').innerHTML, phi:EL('#fNotePhi').textContent});
""")
	dung("có đường dẫn chính sách bảo mật", 'href="/chinh-sach-bao-mat"' in r["cs"])
	dung("bỏ đường dẫn javascript:", "javascript" not in r["cs"])
	dung("dưới ô đồng ý có link đọc chính sách", "/chinh-sach-bao-mat" in r["doc"])
	dung("liên hệ từ cấu hình", "tel:0931224334" in r["lh"])
	dung("dòng giá nói ngưỡng miễn phí", "1.000.000 đ" in r["phi"])


@ca("#367 L chữ tiếng Việt và số dùng phông thường, tên bánh có dấu cũng vậy")
def _():
	w = _doc("vagabond/trang/banh.html")
	dung("tiêu đề mục dùng phông hệ thống, đè được cua-hang.css", "html body .h1{font-family:var(--sans)" in w)
	dung("không còn số ngày khổ lớn", "html body .h1 em#bigDate{display:none}" in w)
	r = _chay("2026-09-24T08:00:00", r"""
RA({vi:laChuViet('Phi Tử Tiếu'), en:laChuViet('Roman de la Rose'), dong:dongTrangThai(13,'13h - 15h','09:59'),
    het:dongTrangThai(null,'','21:00')});
""")
	la("tên có dấu", (r["vi"], r["en"]), (True, False))
	dung("một dòng trạng thái", "13 bánh</b> có sẵn · nhận từ <b>13h - 15h</b>" in r["dong"] and "cập nhật 09:59" in r["dong"])
	dung("chưa tải tồn thì không đoán số", "bánh</b> có sẵn" not in r["het"])


# --------------------------------------------------------------- M. trang biên nhận

def _chay_bien_nhan(du_lieu, bo_nho=None, duong="/banh/xong/" + "a" * 43):
	"""Chạy bien-nhan.js THẬT trong node với window, history, sessionStorage giả."""
	ma = r"""
const vm=require('vm'); const fs=require('fs');
const src=fs.readFileSync(process.argv[1],'utf8');
const vet=[]; const kho=new Map(JSON.parse(process.argv[3]));
const window={ VGB_BIEN_NHAN: JSON.parse(process.argv[2]),
  location:{pathname:process.argv[4]},
  history:{replaceState:(a,b,u)=>{ vet.push('replace:'+u); window.location.pathname=u; }},
  sessionStorage:{getItem:k=>kho.has(k)?kho.get(k):null, setItem:(k,v)=>{kho.set(k,String(v)); vet.push('ghi:'+k);}},
};
const el={innerHTML:''};
const document={ getElementById:()=>el, getElementsByTagName:()=>[{parentNode:{insertBefore:()=>vet.push('nap-script:'+window.location.pathname)}}],
  createElement:()=>({}) };
vm.runInNewContext(src, {window, document, console});
if(window.fbq) window.fbq.queue.forEach(q=>vet.push('fbq:'+Array.from(q).slice(0,2).join(',')+':'+window.location.pathname));
console.log(JSON.stringify({vet, html:el.innerHTML, kho:Array.from(kho.entries())}));
"""
	p = str(GOI / "public" / "web_order" / "bien-nhan.js")
	r = subprocess.run(["node", "-e", ma, p, json.dumps(du_lieu), json.dumps(bo_nho or []), duong],
		capture_output=True, text=True, timeout=30)
	if r.returncode != 0:
		raise AssertionError("bien-nhan.js lỗi: " + r.stderr[:400])
	return json.loads(r.stdout.strip().splitlines()[-1])


@ca("#367 M biên nhận: gỡ token khỏi đường dẫn TRƯỚC khi nạp Pixel; GuiDon bắn một lần")
def _():
	d = {"pixel_id": "123", "than": "<main>bien nhan</main>",
		"su_kien": {"event_id": "ev-1", "gia_tri": 650000, "ma_mon": ["BAWC00139"], "ban": True}}
	r = _chay_bien_nhan(d)
	v = r["vet"]
	la("việc đầu tiên là thay đường dẫn", v[0], "replace:/banh/xong")
	dung("script Meta nạp khi đường dẫn đã sạch", "nap-script:/banh/xong" in v)
	dung("mọi lệnh fbq chạy trên đường dẫn sạch", all(x.endswith(":/banh/xong") for x in v if x.startswith("fbq:")))
	dung("có GuiDon", any(x.startswith("fbq:trackCustom,GuiDon") for x in v))
	r2 = _chay_bien_nhan(d, bo_nho=r["kho"])
	dung("tải lại cùng tab không bắn GuiDon lần hai", not any(x.startswith("fbq:trackCustom,GuiDon") for x in r2["vet"]))
	r3 = _chay_bien_nhan({"khong_token": 1}, bo_nho=r["kho"], duong="/banh/xong")
	la("tải lại không token: đọc lại biên nhận trong tab", r3["html"], "<main>bien nhan</main>")
	dung("và không nạp Pixel", not any(x.startswith("nap-script") for x in r3["vet"]))
	r4 = _chay_bien_nhan({"pixel_id": "", "than": "x", "su_kien": {}})
	dung("Pixel trống thì không nạp gì", not any(x.startswith(("nap-script", "fbq")) for x in r4["vet"]))
	r5 = _chay_bien_nhan(dict(d, su_kien=dict(d["su_kien"], ban=False)))
	dung("đơn đã huỷ không bắn GuiDon", not any("GuiDon" in x for x in r5["vet"]))


# ------------------------------------------------ R. token đi trọn một vòng

@ca("#367 R token trên đường dẫn trả về đúng bản ghi: băm lưu lúc tạo khớp băm lúc mở trang")
def _():
	"""Nối ba hàm THẬT: tao_ban_ghi (lưu băm), phan_hoi (dựng đường dẫn),
	bien_nhan_theo_token (tìm bằng băm). Lệch nonce, lệch khoá hay lệch cách
	băm ở bất kỳ đâu thì khách bấm đường dẫn là gặp 404."""
	bang = []

	class Doc(D):
		def update(self, d):
			dict.update(self, d)

		def insert(self, **k):
			self["name"] = "DW-2609-%05d" % (len(bang) + 1)
			self["creation"] = "2026-09-25 08:00:00"
			bang.append(self)

	def get_all(dt, filters=None, fields=None, **k):
		return [D({f: r.get(f) for f in fields}) for r in bang
			if all(r.get(a) == b for a, b in (filters or {}).items())]

	fr = types.SimpleNamespace(new_doc=lambda dt: Doc(flags=D()), get_all=get_all)
	g = dict(frappe=fr, DOCTYPE="Vagabond Don Web", json=json, _khoa_bi_mat=lambda: KHOA,
		sinh_muoi=don_web.sinh_muoi, sinh_event_id=don_web.sinh_event_id, sinh_token=don_web.sinh_token,
		bam=don_web.bam, token_hop_le=don_web.token_hop_le, tom_tat_bien_nhan=don_web.tom_tat_bien_nhan)
	tao = nap("don_web.py", "tao_ban_ghi", g)
	g["token_cua"] = nap("don_web.py", "token_cua", g)
	ph = nap("don_web.py", "phan_hoi", g)
	tim = nap("don_web.py", "bien_nhan_theo_token", g)
	bg = tao("N" * 24, {"ho_ten": "An", "tien_banh": 650000, "snapshot": json.dumps(SNAP)})
	r = ph(bg, "N" * 24)
	token = r["duong_dan"].rsplit("/", 1)[1]
	dung("đường dẫn đúng dạng", r["duong_dan"].startswith("/banh/xong/") and don_web.token_hop_le(token))
	b = tim(token)
	la("mở đúng bản ghi", b and b["bien_nhan"]["ma"], bg["name"])
	la("event_id GuiDon đi kèm cho Pixel", b and b["su_kien"]["event_id"], bg["event_id_gui_don"])
	dung("event_id khác token", bg["event_id_gui_don"] != token)
	la("gửi trùng cùng nonce ra đúng đường dẫn cũ", ph(bg, "N" * 24)["duong_dan"], r["duong_dan"])
	la("nonce khác không mở được", tim(ph(bg, "M" * 24)["duong_dan"].rsplit("/", 1)[1]), None)
	dung("CSDL không có token gốc", token not in json.dumps(bang, default=str))


@ca("#367 N trang www có mã Python phải đặt tên theo đúng luật Frappe tìm (gạch nối thành gạch dưới)")
def _():
	"""Đo trên site thật 25/09/2026: /bien-tap-web trả thẻ csrf-token với nội
	dung là chữ "{{ csrf_token }}" nguyên văn. Nghĩa là get_context CHƯA TỪNG
	chạy: Frappe (website/page_renderers/template_page.py, set_pymodule) chỉ
	tìm mô đun `bien_tap_web.py`, còn tệp trong repo tên `bien-tap-web.py`.
	Hệ quả: không có cửa kiểm quyền, không có mã CSRF nên lưu nháp bị Frappe
	chặn, và khách vãng lai thấy bảng trống kèm câu "chưa được whitelist".
	Đó mới là gốc của mục 8 trên #367, không phải bộ nhớ đệm."""
	for html, py in (("bien-tap-web.html", "bien_tap_web.py"), ("chinh-sach.html", "chinh_sach.py"),
			("banh/xong.html", "banh/xong.py")):
		dung("%s có mô đun %s" % (html, py), (GOI / "www" / py).exists())
	for p in (GOI / "www").rglob("*.py"):
		if p.name in ("dat-ban.py", "thanh-vien.py"):
			# Hai trang của #300 cùng lỗi này, ngoài phạm vi #367: đã ghi vào
			# bàn giao, chưa đổi để không đụng trang đang chạy khi chưa kiểm.
			continue
		dung("%s không có gạch nối" % p.name, "-" not in p.name)


@ca("#367 H bấm Lưu trên Desk không đổi gì thì không bị chặn oan vì cách viết số, giờ")
def _():
	g = don_web.gia_tri_giong
	dung("650000 và 650000.0", g(650000, 650000.0))
	dung("chuỗi số và số", g("650000", 650000))
	dung("giờ có phần lẻ giây", g("2026-09-26 13:00:00", "2026-09-26 13:00:00.000000"))
	dung("giờ chữ T", g("2026-09-26T13:00:00", "2026-09-26 13:00:00"))
	dung("rỗng và None", g("", None))
	dung("khác tiền thì khác", not g(650000, 650001))
	dung("khác chữ thì khác", not g("abc", "abd"))
	dung("khác băm thì khác", not g("a" * 64, "b" * 64))


@ca("#367 G giờ Frappe không khai múi là giờ Việt Nam: event_time không lệch 7 tiếng")
def _():
	import datetime
	fu = types.SimpleNamespace(get_system_timezone=lambda: "Asia/Ho_Chi_Minh")
	g = dict(get_datetime=lambda d: d, frappe=types.SimpleNamespace(utils=fu))
	u = nap("don_web.py", "_unix", g)
	from vagabond.ngay_pancake import unix_tu_iso
	la("13:00 giờ VN bằng 06:00 UTC", u(datetime.datetime(2026, 9, 25, 13, 0, 0)), unix_tu_iso("2026-09-25T06:00:00"))


@ca("#367 G hoá đơn trả hàng hay hoá đơn thứ hai không đè đơn đã ghi sổ, không gửi Purchase lần nữa")
def _():
	vet = []
	gv = {"trang_thai": "Da ghi so"}

	def get_value(dt, dk, truong):
		vet.append(("get", truong))
		return "DW-1" if truong == "name" else gv.get(truong)
	fr = types.SimpleNamespace(flags=types.SimpleNamespace(),
		db=types.SimpleNamespace(get_value=get_value, set_value=lambda *a, **k: vet.append("set")),
		log_error=lambda **k: vet.append("log"), get_traceback=lambda: "")
	g = dict(frappe=fr, DOCTYPE="Vagabond Don Web", xep_capi=lambda *a, **k: vet.append("capi"),
		now_datetime=lambda: "2026-09-26 10:00:00")
	ham = nap("don_web.py", "khi_ghi_so_hoa_don", g)
	ham(D(name="SINV-RET", is_return=1, custom_pancake_display_id="91500", grand_total=-650000))
	la("trả hàng: không đọc gì", vet, [])
	ham(D(name="SINV-2", custom_pancake_display_id="91500", grand_total=650000))
	dung("đã ghi sổ rồi: không ghi đè, không xếp Purchase", "set" not in vet and "capi" not in vet)
	gv["trang_thai"] = "Da nhan"
	ham(D(name="SINV-3", custom_pancake_display_id="91500", grand_total=650000))
	dung("lần đầu thì ghi và xếp Purchase", "set" in vet and "capi" in vet)
