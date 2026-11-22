"""Chốt chặn tự động (cong_cu/chot_chan.py) và bố cục luật ba tầng (anh Việt chốt 22/11/2026).

Dữ liệu mẫu ở đây dựng lúc chạy bằng cách ghép chuỗi, để chính tệp này không
chứa dãy số hay token trông như thật (chốt chặn quét cả tệp kiểm).
"""
import io
import json
import os
import re
import sys
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(GOC, "cong_cu"))
import chot_chan as CC  # noqa: E402
import hook_truoc_commit as HK  # noqa: E402


@ca("chốt chặn C4: APPVER lùi hoặc đứng yên khi đổi mã app là lỗi; ca #592 và #594 cùng v675")
def _appver():
	la("đọc APPVER", CC.doc_appver("x\n\tvar APPVER = '683';\n"), 683)
	la("tăng là được", CC.kiem_appver(683, 684, True), [])
	dung("lùi là lỗi", CC.kiem_appver(683, 682, False) and "lùi" in CC.kiem_appver(683, 682, False)[0])
	# #592 merge trước với v675; #594 cũng đặt v675 và đổi mã app.
	loi = CC.kiem_appver(675, 675, True)
	dung("PR merge sau cùng số là lỗi: %s" % loi, len(loi) == 1 and "675" in loi[0])
	la("chỉ đổi tài liệu, ca kiểm, sổ tay thì không cần nâng", CC.kiem_appver(683, 683, False), [])
	la("phân loại tệp", [CC.la_ma_app(t) for t in ("vagabond/chi_phi_meta.py", "vagabond/public/js/bep/12-van-don.js",
		"vagabond/khung/kiem_thu/thu_x.py", "vagabond/so_tay/ke-toan.md", "AGENTS.md", "docs/a.md", "vagabond/AGENTS.md")],
		[True, True, False, False, False, False, False])


@ca("chốt chặn C6: patches.txt giữ mọi dòng của nhánh nền, có đúng một dòng cho số mới, không trùng")
def _patches():
	d = CC.DONG_PATCH
	nen = "a.b\n%s #v682\n%s #v683\n" % (d, d)
	la("đủ dòng cũ, thêm dòng số mới", CC.kiem_patches(nen, nen + "%s #v684\n" % d, 683, 684), [])
	loi = CC.kiem_patches(nen, "a.b\n%s #v684\n" % d, 683, 684)
	dung("mất dòng của phiên khác là lỗi", any("mất dòng" in x and "#v683" in x for x in loi))
	loi = CC.kiem_patches(nen, nen, 683, 684)
	dung("nâng số mà thiếu dòng là lỗi", any("chưa có dòng" in x for x in loi))
	loi = CC.kiem_patches(nen, nen + "%s #v684\n%s #v684\n" % (d, d), 683, 684)
	dung("dòng trùng là lỗi", any("trùng" in x for x in loi))


DIFF = """diff --git a/docs/a.md b/docs/a.md
--- a/docs/a.md
+++ b/docs/a.md
@@ -3,0 +4,2 @@
+dòng một
+dòng hai
diff --git a/anh.png b/anh.png
Binary files differ
@@ -10 +12 @@
"""


@ca("chốt chặn: đọc đúng dòng thêm mới và số dòng từ git diff -U0")
def _dong_them():
	la("dòng thêm", CC.dong_them(DIFF), [("docs/a.md", 4, "dòng một"), ("docs/a.md", 5, "dòng hai")])


@ca("chốt chặn C7: em dash, en dash trên dòng thêm mới của tệp chữ")
def _gach():
	r = CC.tim_gach([("docs/a.md", 1, "a \u2014 b"), ("x.py", 2, "a \u2013 b"), ("anh.png", 3, "\u2014"), ("x.py", 4, "a - b")])
	la("bắt đúng hai dòng", [(t, s) for t, s, _ in r], [("docs/a.md", 1), ("x.py", 2)])


@ca("chốt chặn C9: token và khoá trên dòng thêm mới, mọi tệp")
def _bi_mat():
	gia = "gh" + "p_" + "A1b2C3d4" * 5
	meta = "EA" + "AB" + "x9Y8z7W6" * 6
	r = CC.tim_bi_mat([("vagabond/a.py", 1, "TOKEN = '%s'" % gia), ("docs/b.md", 2, "ma: %s" % meta),
		("vagabond/a.py", 3, "doc khoa tu Cai dat, khong ghi vao ma")])
	la("bắt token GitHub và mã Meta", [s for _, s, _ in r], [1, 2])


@ca("chốt chặn C8: dữ liệu thật trên dòng thêm mới của ca kiểm, tài liệu (ca #592); dữ liệu giả hay định danh công khai thì cho qua")
def _du_lieu():
	so_tk = "10" + "3350" + "7466"
	the = "4" + "5391488" + "03436467"
	dt = "0" + "916384572"
	email = "nguyenvan" + "a1987" + "@gmail.com"
	dong = [
		("vagabond/khung/kiem_thu/thu_x.py", 1, "'MBVCB.CT tu %s NGUYEN VAN A toi 00000001'" % so_tk),
		("vagabond/khung/kiem_thu/thu_x.py", 2, "'RetailVISA-%s'" % the),
		("docs/a.md", 3, "goi %s" % dt),
		("docs/a.md", 4, "lien he %s" % email),
		("vagabond/khung/kiem_thu/thu_x.py", 5, "'CT tu %s'  # du-lieu-gia" % so_tk),
		("vagabond/khung/kiem_thu/thu_x.py", 6, "'0909111222', '0912345678', 'The 000000001'"),
		("vagabond/khung/kiem_thu/thu_x.py", 7, "'MST: 0318561568', 'goi 0931 224 334', 'ketoan@thevagabondpatisserie.com'"),
		("vagabond/chi_phi_meta.py", 8, "'CT tu %s'" % so_tk),
	]
	r = CC.tim_du_lieu_that(dong)
	la("bắt bốn dòng thật, bỏ qua dòng ghi giả, số giả, định danh công khai, tệp ngoài vùng", [s for _, s, _ in r], [1, 2, 3, 4])
	dung("câu báo chỉ cách sửa", all("du-lieu-gia" in c for _, _, c in r))
	la("số giả", [CC.la_so_gia(x) for x in ("0909111222", "0912345678", "0903000111", "000000001", "0909121912", so_tk, dt)],
		[True, True, True, True, True, False, False])
	la("hotline viết kiểu +84 vẫn là định danh công khai", CC.la_so_gia("+84" + "931224334"), True)
	la("Luhn", (CC.luhn(the), CC.luhn("4" + "5391488" + "03436468")), (True, False))


@ca("chốt chặn C10: chỉ cảnh báo khi PR xoá nhiều dòng một tệp")
def _xoa():
	r = CC.xoa_nhieu("3\t120\tAGENTS.md\n10\t5\tx.py\n-\t-\tanh.png\n")
	la("một cảnh báo", len(r), 1)
	dung("nêu tên tệp", "AGENTS.md" in r[0])


@ca("chốt chặn: cảnh báo 3 ngày đầu, từ CHAN_TU mới chặn (anh Việt chốt 22/11/2026)")
def _che_do():
	la("mốc", CC.CHAN_TU, "2026-11-26")
	la("trước, đúng ngày, sau", [CC.dang_chan(x) for x in ("2026-11-25", "2026-11-26", "2026-12-01")], [False, True, True])


@ca("hook trước commit: chỉ xét git commit, git push; chặn mã 2 khi đã tới ngày chặn; hook hỏng thì không làm kẹt phiên")
def _hook():
	import datetime
	that = datetime.date

	def chay(lenh, loi, ngay, hong=False):
		def gia_chay(cay=False):
			if hong:
				raise RuntimeError("git hỏng")
			return loi, []
		with um.patch.object(sys, "stdin", io.StringIO(json.dumps({"tool_input": {"command": lenh}}))), \
				um.patch.object(CC, "chay", gia_chay), um.patch.object(sys, "stderr", io.StringIO()), \
				um.patch.object(HK.datetime, "date", um.Mock(today=lambda: that(*ngay))):
			return HK.main()
	l1 = [("docs/a.md", 1, "C7 có em dash")]
	la("lệnh khác thì bỏ qua", chay("ls -la", l1, (2026, 12, 1)), 0)
	la("trước ngày chặn chỉ cảnh báo", chay("git commit -m x", l1, (2026, 11, 24)), 0)
	la("từ ngày chặn thì chặn", chay("git commit -m x", l1, (2026, 11, 26)), 2)
	la("git push cũng chặn", chay("git push origin HEAD:x", l1, (2026, 12, 1)), 2)
	la("không lỗi thì cho chạy", chay("git commit -m x", [], (2026, 12, 1)), 0)
	la("chốt chặn hỏng thì cho chạy", chay("git commit -m x", l1, (2026, 12, 1), hong=True), 0)


@ca("luật ba tầng: AGENTS.md gốc gọn, CLAUDE.md dẫn về nó, mọi đường dẫn trong luật gốc có thật")
def _luat():
	goc = io.open(os.path.join(GOC, "AGENTS.md"), encoding="utf-8").read()
	dung("AGENTS.md gốc dưới 160 dòng: %d" % goc.count("\n"), goc.count("\n") < 160)
	la("CLAUDE.md gốc chỉ dẫn về AGENTS.md", io.open(os.path.join(GOC, "CLAUDE.md"), encoding="utf-8").read().strip(), "@AGENTS.md")
	thieu = [p for p in re.findall(r"\]\(([^)#]+)\)", goc) if not p.startswith("http") and not os.path.exists(os.path.join(GOC, p))]
	la("đường dẫn chết trong luật gốc", thieu, [])
	for d in ("vagabond/public/js/bep", "vagabond/khung/kiem_thu", "vagabond/khung/kiem_that", "vagabond/public/web_vue",
			"vagabond/public/web_order", "vagabond/patches"):
		dung("%s có AGENTS.md và CLAUDE.md dẫn về nó" % d, os.path.exists(os.path.join(GOC, d, "AGENTS.md"))
			and io.open(os.path.join(GOC, d, "CLAUDE.md"), encoding="utf-8").read().strip() == "@AGENTS.md")
	dung("không đặt luật trong www (Frappe phát thành trang công khai)",
		not any(f.upper().startswith(("AGENTS", "CLAUDE")) for f in os.listdir(os.path.join(GOC, "vagabond", "www"))))
	for p in ("vgb-control-tower/README.md", "docs/van-hanh-agent/luat-cu.md", "docs/van-hanh-agent/so-mau-loi.md",
			"docs/van-hanh-agent/nghiem-thu-va-ra.md"):
		dung("có %s" % p, os.path.exists(os.path.join(GOC, p)))
	hook = json.load(io.open(os.path.join(GOC, ".claude", "settings.json"), encoding="utf-8"))
	dung("hook Claude Code gọi chốt chặn", "hook_truoc_commit.py" in json.dumps(hook))
