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
