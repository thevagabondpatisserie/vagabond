"""v585: bản tin phát hành vào nhóm Zalo, cùng nguồn [ĐÃ DEPLOY] với Telegram.

Site thật 07/10/2026: bot Zalo bật, nhóm ERP Văn Phòng nhận loại Phát hành,
nhưng sổ tin Zalo 0 dòng vì không chỗ nào gọi kenh_zalo.bao("phat_hanh").
Ca dưới chạy quet() THẬT, chỉ thay GitHub (requests) và kenh_zalo.bao.
"""
import json

from vagabond import zalo_phat_hanh as Z
from vagabond.khung.kiem_thu.nen import ca, dung, la

SHA = "9894dd7e7ae6b97c0ba911ca0ea56a4b41e00d44"


def _cmt(ban="v585", sha=SHA, dong_dau="[ĐÃ DEPLOY]", chu="thevagabondpatisserie", vai="OWNER",
		tinh=None, live=True, luc="2026-10-07T12:00:00Z"):
	khoi = {"version": ban, "sha": sha, "live_verified": live, "features": tinh or ["Có màn Đối soát", "Đổi Bộ phận"]}
	return {"user": {"login": chu}, "author_association": vai, "updated_at": luc,
		"body": dong_dau + "\nbản tin\n<!-- telegram-release\n" + json.dumps(khoi, ensure_ascii=False) + "\n-->"}


@ca("v585 Zalo phát hành: đọc khối cùng luật với Telegram")
def _():
	dung("đúng chủ repo, đã kiểm site", Z.ban_phat_hanh(_cmt()) is not None)
	for ten, c in (("người khác", _cmt(chu="ai-do", vai="CONTRIBUTOR")), ("bot", _cmt(vai="NONE")),
			("dòng đầu sai", _cmt(dong_dau="[SẴN SÀNG DEPLOY]")), ("chưa kiểm site", _cmt(live=False)),
			("sha sai", _cmt(sha="abc")), ("quá 5 dòng", _cmt(tinh=["a"] * 6)), ("dòng rỗng", _cmt(tinh=[" "]))):
		la("bỏ: " + ten, Z.ban_phat_hanh(c), None)
	c = _cmt()
	c["body"] += "\n<!-- telegram-release\n{}\n-->"
	la("hai khối thì bỏ", Z.ban_phat_hanh(c), None)


@ca("v585 Zalo phát hành: chỉ báo đúng bản đang chạy trên site, comment sửa sau cùng thắng")
def _():
	la("số bản từ patches.txt", Z.so_ban("a\nb.dong_bo_cau_truc #v583\nc #v585\nd #v584\n"), 585)
	la("không có dấu", Z.so_ban("a\nb\n"), 0)
	cu = _cmt(ban="v584", sha="1" * 40)
	moi = _cmt(tinh=["bản đầu"], luc="2026-10-07T12:00:00Z")
	sua = _cmt(tinh=["bản sửa"], luc="2026-10-07T13:00:00Z")
	ra = Z.chon_ban([sua, cu, moi], 585)
	la("một bản của v585, lấy bản sửa", [(x["version"], x["features"]) for x in ra], [("v585", ["bản sửa"])])
	la("bản chưa lên site thì chưa báo", Z.chon_ban([_cmt(ban="v586", sha="2" * 40)], 585), [])


def _quet(bat=1, cmt=None, loi=None, ban=585):
	from unittest.mock import patch
	from vagabond import kenh_zalo
	goi = []

	def doc():
		if loi:
			raise loi
		return cmt or []
	with patch.object(kenh_zalo, "_bat", lambda: bat), patch.object(Z, "_ban_site", lambda: ban), \
			patch.object(Z, "_doc_comment", doc), \
			patch.object(kenh_zalo, "bao", lambda *a, **k: goi.append((a, k))), \
			patch.object(Z.frappe, "log_error", lambda *a, **k: goi.append(("LOG",)), create=True), \
			patch.object(Z.frappe.db, "commit", lambda: None, create=True):
		so = Z.quet()
	return so, goi


@ca("v585 Zalo phát hành: quét gọi kenh_zalo.bao đúng loại, chủ đề, khoá chống trùng theo sha")
def _():
	so, goi = _quet(cmt=[_cmt(), _cmt(ban="v584", sha="1" * 40)])
	la("gửi một bản", so, 1)
	a, k = goi[0]
	la("loại và chủ đề Phát hành", a[:2], ("phat_hanh", "phat_hanh"))
	dung("tiêu đề có số bản", "v585" in a[2])
	la("các dòng là tính năng", k["dong"], ["Có màn Đối soát", "Đổi Bộ phận"])
	la("khoá theo sha", k["khoa"], "phat_hanh:" + SHA)
	so, goi = _quet(bat=0, cmt=[_cmt()])
	la("bot Zalo tắt thì không đọc GitHub, không gửi", (so, goi), (0, []))
	so, goi = _quet(loi=OSError("mang"))
	la("lỗi mạng: không ném ra, ghi log", (so, goi), (0, [("LOG",)]))


@ca("v585 Zalo phát hành: không đọc được số bản trên site thì ghi Error Log, không im lặng (Codex #452)")
def _():
	# Chạy _ban_site THẬT; chỉ thay chỗ lấy đường dẫn tệp. Bản cũ trả 0 rồi
	# quet() thoát êm: 0 tin, 0 log, kênh tắt mãi mà không ai biết.
	import os
	import tempfile
	from unittest.mock import patch
	from vagabond import kenh_zalo

	def quet_voi(lay_duong):
		log = []
		with patch.object(kenh_zalo, "_bat", lambda: 1), \
				patch.object(Z.frappe, "get_app_path", lay_duong, create=True), \
				patch.object(Z.frappe, "log_error", lambda *a, **k: log.append(a), create=True), \
				patch.object(Z, "_doc_comment", lambda: [_cmt()]), \
				patch.object(kenh_zalo, "bao", lambda *a, **k: log.append(("BAO",))):
			return Z.quet(), log

	def mat(*a):
		raise IOError("không có patches.txt")
	so, log = quet_voi(mat)
	la("mất tệp: không gửi", so, 0)
	la("mất tệp: một dòng Error Log", len(log), 1)
	dung("tiêu đề log nói rõ số bản", "so ban" in log[0][1])
	with tempfile.TemporaryDirectory() as d:
		f = os.path.join(d, "patches.txt")
		open(f, "w").write("a.b\nc.d\n")
		so, log = quet_voi(lambda *a: f)
		la("tệp không có dấu #v: không gửi, có log", (so, len(log)), (0, 1))
		open(f, "w").write("a.b #v585\n")
		so, log = quet_voi(lambda *a: f)
		la("tệp đúng: gửi và không log", (so, log), (1, [("BAO",)]))


def _github(trang, goi):
	import types

	class R:
		def __init__(s, d):
			s.d = d

		def raise_for_status(s):
			pass

		def json(s):
			return s.d
	m = types.ModuleType("requests")

	def get(url, params=None, **k):
		goi.append(params.get("page"))
		return R(trang.get(params.get("page"), []))
	m.get = get
	return m


@ca("v585 Zalo phát hành: đọc đủ mọi trang comment, biên nhận ở trang 2 vẫn được báo (Codex #452)")
def _():
	# Chạy _doc_comment THẬT với GitHub giả theo trang. Bản cũ chỉ gọi trang 1
	# (100 dòng), biên nhận bị 100 comment mới hơn đẩy xuống là mất hẳn.
	import sys
	from unittest.mock import patch
	rac = {"user": {"login": "x"}, "author_association": "NONE", "updated_at": "2026-10-07T14:00:00Z", "body": "ok"}
	goi = []
	with patch.dict(sys.modules, {"requests": _github({1: [rac] * 100, 2: [_cmt()]}, goi)}), \
			patch.object(Z, "_moc", lambda: "2026-10-04T00:00:00Z"):
		ds = Z._doc_comment()
	la("gọi trang 1 rồi trang 2", goi, [1, 2])
	la("đủ 101 comment", len(ds), 101)
	la("chọn được bản v585", [x["version"] for x in Z.chon_ban(ds, 585)], ["v585"])
	goi = []
	with patch.dict(sys.modules, {"requests": _github({1: [_cmt()]}, goi)}), \
			patch.object(Z, "_moc", lambda: "2026-10-04T00:00:00Z"):
		la("trang thiếu thì dừng, không gọi thừa", (len(Z._doc_comment()), goi), (1, [1]))
	# Quá 10 trang đầy mà vẫn còn: ném lỗi (quet ghi log), không lặng lẽ cắt.
	day = {so: [rac] * 100 for so in range(1, 12)}
	try:
		Z.gom_trang(lambda so: day.get(so, []))
		dung("quá 1000 dòng phải ném lỗi", False)
	except ValueError:
		dung("quá 1000 dòng phải ném lỗi", True)
	la("đúng 10 trang đầy, trang 11 rỗng: nhận đủ", len(Z.gom_trang(lambda so: [rac] * 100 if so <= 10 else [])), 1000)


@ca("v585 Zalo phát hành: mốc since gửi GitHub là giờ UTC thật, không phải giờ site gắn Z (Codex #452)")
def _():
	# Site chạy Asia/Ho_Chi_Minh: 19:00 giờ VN là 12:00Z. Bản cũ lấy
	# now_datetime() (giờ site, không múi) rồi gắn Z nên ra 19:00Z, hụt 7 giờ.
	from datetime import datetime, timedelta, timezone
	from unittest.mock import patch
	vn = timezone(timedelta(hours=7))
	la("19:00 giờ VN lùi 3 ngày", Z.moc_utc(datetime(2026, 10, 7, 19, 0, tzinfo=vn)), "2026-10-04T12:00:00Z")
	la("qua nửa đêm UTC", Z.moc_utc(datetime(2026, 10, 7, 3, 0, tzinfo=vn)), "2026-10-03T20:00:00Z")
	try:
		Z.moc_utc(datetime(2026, 10, 7, 19, 0))
		dung("giờ không múi phải bị từ chối", False)
	except ValueError:
		dung("giờ không múi phải bị từ chối", True)
	# _moc THẬT không được dựa vào giờ site: đổi now_datetime của Frappe sang
	# giờ VN không múi thì kết quả vẫn phải khớp giờ UTC thật.
	import frappe.utils as fu
	that = datetime.now(timezone.utc)
	with patch.object(fu, "now_datetime", lambda: that.astimezone(vn).replace(tzinfo=None), create=True):
		ra = datetime.strptime(Z._moc(), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
	lech = abs((that - timedelta(days=Z.LUI_NGAY) - ra).total_seconds())
	dung("_moc lệch giờ UTC thật dưới 1 phút (được %d giây)" % lech, lech < 60)


@ca("v585 Zalo phát hành: luật đọc khối khớp với bộ gửi Telegram (không lệch hai kênh)")
def _():
	# Dò chuỗi vì không chạy được thong_bao.py ở đây (cần GitHub): chốt các điều
	# kiện cốt lõi vẫn còn nguyên bên Telegram; đổi bên kia thì ca này đỏ để sửa cả hai.
	import os
	goc = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".github", "telegram", "thong_bao.py")
	if not os.path.exists(goc):
		return
	t = open(goc, encoding="utf-8").read()
	for mau in ("'[ĐÃ DEPLOY]'", "author_association') != 'OWNER'", "<!-- telegram-release",
			"{'version', 'sha', 'features', 'live_verified'}", "1 <= len(features) <= 5", "len(f) > 220"):
		dung("Telegram vẫn có: " + mau, mau in t)
