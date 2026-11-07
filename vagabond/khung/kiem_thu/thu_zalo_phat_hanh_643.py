"""v643 (còn tồn v604): bản tin phát hành Zalo đọc GitHub bị giới hạn lượt
(403 rate limit) hay hết giờ chờ thì nghỉ tới giờ GitHub hẹn, không ghi Error
Log mỗi 15 phút; đọc được bản tin của bản đang chạy thì thôi gọi GitHub.

Trên site: 01/11/2026 có 10 dòng "khong doc duoc ban tin tren GitHub" trong 4
giờ, đều là "403 rate limit exceeded"; 07/11 có "Read timed out"."""
import json
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

# Chạy riêng tệp này (đột biến) thì bản Frappe giả chưa có get_url mà
# kenh_zalo cần; bộ chạy đủ thì ca khác đã gắn.
_fr = gia_lap()
if not hasattr(_fr.utils, "get_url"):
	_fr.utils.get_url = lambda *a, **k: "https://vagabond.test"
from vagabond import zalo_phat_hanh as Z


def _cmt():
	khoi = {"version": "v585", "sha": "9" * 40, "live_verified": True, "features": ["Có màn Đối soát"]}
	return {"user": {"login": "thevagabondpatisserie"}, "author_association": "OWNER", "updated_at": "2026-10-07T12:00:00Z",
		"body": "[ĐÃ DEPLOY]\nbản tin\n<!-- telegram-release\n" + json.dumps(khoi, ensure_ascii=False) + "\n-->"}


class _Res:
	def __init__(s, ma, headers=None):
		s.status_code, s.headers = ma, headers or {}


class HTTPError(Exception):
	def __init__(s, msg, ma, headers=None):
		super().__init__(msg)
		s.response = _Res(ma, headers)


class ReadTimeout(Exception):
	pass


class _Nho(dict):
	def get_value(s, k):
		return s.get(k)

	def set_value(s, k, v, expires_in_sec=None):
		if v is None:
			s.pop(k, None)
		else:
			s[k] = v


def _chay(nho, doc, bay, bao_tra=lambda khoa: ["ZL-" + khoa[-6:]], da_co=lambda khoa: False):
	from vagabond import kenh_zalo
	log, goi, bao = [], [], []

	def d():
		goi.append(1)
		x = doc.pop(0)
		if isinstance(x, Exception):
			raise x
		return x
	with patch.object(kenh_zalo, "_bat", lambda: 1), patch.object(Z, "_ban_site", lambda: 585), \
			patch.object(Z, "_doc_comment", d), patch.object(Z.frappe, "cache", lambda: nho, create=True), \
			patch.object(kenh_zalo, "bao", lambda *a, **k: bao.append(k.get("khoa")) or bao_tra(k.get("khoa"))), \
			patch.object(Z, "_da_co_tin", da_co, create=True), \
			patch.object(Z.frappe, "log_error", lambda *a, **k: log.append(a[1] if len(a) > 1 else k.get("title")), create=True), \
			patch.object(Z.frappe, "get_traceback", lambda: "tb", create=True), \
			patch.object(Z.frappe.db, "commit", lambda: None, create=True), \
			patch("time.time", lambda: bay):
		so = Z.quet()
	return so, len(goi), log, bao


@ca("v643 Zalo phát hành: GitHub giới hạn lượt hay hết giờ thì nghỉ, không ghi Error Log mỗi nhịp; kéo dài quá 12 giờ mới báo một lần; lỗi thật vẫn báo; đọc được bản tin thì thôi gọi")
def _():
	la("403 rate limit là lỗi tạm", Z.loi_tam(HTTPError("403 Client Error: rate limit exceeded", 403)), True)
	la("403 khác không phải lỗi tạm", Z.loi_tam(HTTPError("403 Forbidden", 403)), False)
	la("hết giờ chờ là lỗi tạm", Z.loi_tam(ReadTimeout("read timed out")), True)
	la("GitHub 502, 503 là lỗi tạm; 404 không", [Z.loi_tam(HTTPError("502 Bad Gateway", 502)), Z.loi_tam(HTTPError("503", 503)), Z.loi_tam(HTTPError("404 Not Found", 404))], [True, True, False])
	la("giờ hẹn của GitHub", Z.giay_nghi({"X-RateLimit-Reset": "11200"}, 10000), 1200)
	la("kẹp trong 5 phút tới 1 giờ", (Z.giay_nghi({"x-ratelimit-reset": "10001"}, 10000), Z.giay_nghi({"Retry-After": "99999"}, 0)), (300, 3600))
	nho = _Nho()
	t0 = 1_800_000_000
	so, goi, log, _b = _chay(nho, [HTTPError("403 Client Error: rate limit exceeded", 403, {"X-RateLimit-Reset": str(t0 + 1200)})], t0)
	la("bị giới hạn: không ghi Error Log", (so, goi, log), (0, 1, []))
	so, goi, log, _b = _chay(nho, [], t0 + 900)
	la("trong giờ nghỉ: không gọi GitHub", (goi, log), (0, []))
	so, goi, log, _b = _chay(nho, [ReadTimeout("x")], t0 + 1300)
	la("hết giờ chờ lần nữa: vẫn im", log, [])
	so, goi, log, _b = _chay(nho, [ReadTimeout("x")], t0 + 13 * 3600)
	la("kéo dài quá 12 giờ: báo một dòng", len(log), 1)
	dung("dòng báo nói rõ GitHub từ chối lâu", "12 gio" in log[0])
	so, goi, log, _b = _chay(nho, [ReadTimeout("x")], t0 + 14 * 3600)
	la("cùng ngày không báo lại", log, [])
	so, goi, log, bao = _chay(nho, [[_cmt()]], t0 + 15 * 3600)
	la("đọc được: gửi đúng một bản", (so, len(bao)), (1, 1))
	dung("đọc được thì xoá mốc lỗi", "zph_loi_tu" not in nho)
	so, goi, log, bao = _chay(nho, [], t0 + 16 * 3600)
	la("bản đang chạy đã có bản tin: thôi gọi GitHub", (so, goi), (0, 0))
	nho2 = _Nho()
	so, goi, log, _b = _chay(nho2, [ValueError("GitHub trả dữ liệu lạ")], t0)
	la("lỗi thật: vẫn ghi Error Log ngay", len(log), 1)
	nho3 = _Nho()
	so, goi, log, bao = _chay(nho3, [[]], t0)
	dung("chưa có bản tin của bản đang chạy: nhịp sau còn hỏi", "zph_xong:585" not in nho3)


@ca("Codex PR #546 vòng 3: bản tin chưa ghi được vào hộp thư Zalo (lỗi ghi, không nhóm nào nhận) thì KHÔNG đánh dấu xong, nhịp sau đọc GitHub và ghi lại; đã có sẵn theo khoá chống trùng thì coi là xong")
def _codex546_ben():
	t0 = 1_800_000_000
	nho = _Nho()
	so, goi, log, bao = _chay(nho, [[_cmt()]], t0, bao_tra=lambda khoa: None)
	dung("ghi hỏng: chưa đánh dấu xong", "zph_xong:585" not in nho)
	so, goi, log, bao = _chay(nho, [[_cmt()]], t0 + 900, bao_tra=lambda khoa: [])
	la("nhịp sau vẫn đọc GitHub và thử ghi lại", (goi, len(bao)), (1, 1))
	dung("không nhóm nào nhận: chưa xong", "zph_xong:585" not in nho)
	so, goi, log, bao = _chay(nho, [[_cmt()]], t0 + 1800)
	dung("ghi được: xong", "zph_xong:585" in nho)
	nho2 = _Nho()
	_chay(nho2, [[_cmt()]], t0, bao_tra=lambda khoa: [], da_co=lambda khoa: khoa == "phat_hanh:" + "9" * 40)
	dung("đã có sẵn theo khoá chống trùng: xong", "zph_xong:585" in nho2)
	# _da_co_tin thật: hỏi đúng tên dòng chống trùng theo mã chat của nhóm nhận tin phát hành.
	from vagabond import kenh_zalo
	hoi = []
	with patch.object(kenh_zalo, "_cac_nhom", lambda: ["N1"]), patch.object(kenh_zalo, "chon_nhom", lambda ds, *a: [{"chat_id": "123"}] if ds else []), \
			patch.object(Z.frappe.db, "exists", lambda dt, f: hoi.append((dt, f)) or True, create=True):
		la("có dòng trong hộp thư", Z._da_co_tin("phat_hanh:abc"), True)
	la("hỏi đúng tên dòng", hoi, [("Vagabond Tin Kenh", {"name": ["in", [kenh_zalo.khoa_tin("phat_hanh:abc", "123")]]})])
	with patch.object(kenh_zalo, "_cac_nhom", lambda: []), patch.object(kenh_zalo, "chon_nhom", lambda ds, *a: []):
		la("không nhóm nào nhận: chưa có", Z._da_co_tin("phat_hanh:abc"), False)
