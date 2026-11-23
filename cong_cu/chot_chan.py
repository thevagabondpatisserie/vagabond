#!/usr/bin/env python3
"""Chốt chặn tự động trên mọi PR (anh Việt chốt 22/11/2026, đề xuất #607 mục 5).

Đổi các luật trước đây chỉ dựa vào trí nhớ của agent thành phép kiểm máy:

  C4  APPVER không lùi; PR đổi mã app thì APPVER phải lớn hơn bản trên nhánh nền.
  C5  Hai PR cùng số phiên bản: C4 cộng luật "nhánh phải cập nhật với main" của
      bảo vệ nhánh làm PR merge sau đỏ cho tới khi nâng số (ca #592 và #594).
  C6  patches.txt giữ mọi dòng của nhánh nền; số mới có đúng một dòng
      dong_bo_cau_truc #vNNN, không trùng dòng cũ.
  C7  Không em dash, en dash trên dòng THÊM MỚI.
  C8  Không dữ liệu thật trên dòng thêm mới của ca kiểm và tài liệu: số thẻ,
      số điện thoại, mã số thuế, số tài khoản, email người thật (ca #592).
  C9  Không bí mật (token, khoá) trên dòng thêm mới.
  C10 Cảnh báo (không chặn) khi PR xoá nhiều dòng của một tệp.

Chỉ xét phần PR THÊM hoặc ĐỔI, không bắt lỗi cũ đã nằm trên main.

Trước ngày CHAN_TU mọi lỗi chỉ là cảnh báo (anh Việt chốt: cảnh báo 3 ngày
đầu để xem có chặn nhầm không). Từ ngày đó lỗi làm đỏ CI và chặn merge.

Dòng dữ liệu giả mà máy vẫn nghi là thật: thêm chữ `du-lieu-gia` vào cuối dòng
(trong chú thích) để bỏ qua C8. Không dùng cách này cho C9.

Cách chạy:
  python3 cong_cu/chot_chan.py              so với nhánh nền (CI: HEAD^1; máy: merge-base origin/main)
  python3 cong_cu/chot_chan.py --cay        so cả phần chưa commit (hook trước commit)
  python3 cong_cu/chot_chan.py --base REF   so với REF
"""
import datetime
import os
import re
import subprocess
import sys

CHAN_TU = "2026-11-26"
TEP_APPVER = "vagabond/public/js/bep/12-van-don.js"
TEP_PATCHES = "vagabond/patches.txt"
DONG_PATCH = "vagabond.patches.dong_bo_cau_truc"
NGUONG_XOA = 80

DUOI_CHU = (".md", ".py", ".js", ".cjs", ".mjs", ".json", ".html", ".css", ".txt", ".yml", ".yaml", ".sh")
# Chỗ hay có dữ liệu mẫu: ca kiểm, tài liệu, công cụ.
VUNG_DU_LIEU = ("vagabond/khung/", "docs/", "cong_cu/", "tai_lieu/", "vgb-control-tower/")
BO_QUA = "du-lieu-gia"
TEN_MIEN_GIA = ("example.com", "example.org", "example.net", "kiem.thu", "test", "invalid", "local", "localhost")
# Hộp thư cá nhân miễn phí: email người thật hay nằm ở đây. Email công việc theo
# tên miền doanh nghiệp (ketoan@..., admin@ngân hàng) không coi là dữ liệu cá nhân.
MIEN_CA_NHAN = ("gmail.com", "yahoo.com", "yahoo.com.vn", "hotmail.com", "outlook.com", "icloud.com", "live.com")
# Định danh công khai của chính công ty (in trên hoá đơn, trên trang web), không phải dữ liệu cá nhân.
DINH_DANH_CONG_KHAI = ("0318561568", "0931224334")  # mã số thuế, hotline in trên web

MAU_APPVER = re.compile(r"""var\s+APPVER\s*=\s*['"](\d+)['"]""")
MAU_GACH = re.compile("[\u2013\u2014]")
MAU_BI_MAT = (
	("token GitHub", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b")),
	("token GitHub", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
	("khoá Anthropic hoặc OpenAI", re.compile(r"\bsk-(ant-)?[A-Za-z0-9_-]{20,}\b")),
	("khoá AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
	("token Slack", re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{10,}\b")),
	("mã truy cập Meta", re.compile(r"\bEAA[A-Za-z0-9]{40,}\b")),
	("khoá riêng", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
	("token Bearer", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{30,}")),
	("khoá API gán thẳng", re.compile(r"""(?i)\b(api[_-]?key|api[_-]?secret|secret[_-]?key|access[_-]?token|password)\s*[:=]\s*['"][^'"\s]{16,}['"]""")),
)
MAU_THE = re.compile(r"(?<![\d.])(\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{1,7})(?![\d.])")
MAU_SDT = re.compile(r"(?<![\d.])((?:\+?84|0)[35789]\d{8})(?![\d.])")
MAU_MST = re.compile(r"(?i)\b(?:mst|ma so thue|mã số thuế|tax ?code)\s*[:=#]?\s*(\d{10}(?:-\d{3})?)\b")
MAU_STK = re.compile(r"(?i)\b(?:stk|so tk|số tk|so tai khoan|số tài khoản|tai khoan|tài khoản|account(?: no| number)?|tk)\s*[:=#]?\s*(\d{6,19})\b")
# Mô tả sao kê ngân hàng: "CT tu <số tài khoản> <tên> toi <số tài khoản>", "-The <số thẻ>" (ca #592).
MAU_SAO_KE = re.compile(r"(?i)(?:\bct tu|\btu tk|\btoi|\bden tk|-the|\bthe)\s+(\d{8,16})\b")
MAU_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)\b")


# --------------------------------------------------------------- phép thuần

def doc_appver(chu):
	m = MAU_APPVER.search(chu or "")
	return int(m.group(1)) if m else None


def la_ma_app(tep):
	"""Tệp đổi thì phải phát hành bản mới (cần nâng APPVER)."""
	if not tep.startswith("vagabond/") or tep.endswith(".md"):
		return False
	return not tep.startswith(("vagabond/khung/", "vagabond/so_tay/"))


def kiem_appver(nen, pr, doi_ma_app):
	"""C4. nen, pr: APPVER hai bên (None nếu không đọc được)."""
	if nen is None or pr is None:
		return []
	if pr < nen:
		return ["C4 APPVER lùi: nhánh nền %d, PR %d. Đọc origin/main rồi đặt số lớn hơn." % (nen, pr)]
	if doi_ma_app and pr == nen:
		return ["C4 PR đổi mã app nhưng APPVER vẫn %d như nhánh nền. Nâng số mới (PR khác có thể vừa merge cùng số)." % pr]
	return []


def kiem_patches(nen_chu, pr_chu, appver_nen, appver_pr):
	"""C6."""
	loi = []
	pr_dong = [d.strip() for d in (pr_chu or "").splitlines()]
	con = set(pr_dong)
	for d in (nen_chu or "").splitlines():
		d = d.strip()
		if d and d not in con:
			loi.append("C6 patches.txt mất dòng đang có trên nhánh nền: %s" % d)
	dem = {}
	for d in pr_dong:
		if d.startswith(DONG_PATCH):
			dem[d] = dem.get(d, 0) + 1
	for d, n in sorted(dem.items()):
		if n > 1:
			loi.append("C6 patches.txt có %d dòng trùng: %s" % (n, d))
	if appver_pr is not None and appver_nen is not None and appver_pr > appver_nen:
		can = "%s #v%d" % (DONG_PATCH, appver_pr)
		if dem.get(can, 0) == 0:
			loi.append("C6 APPVER %d nhưng patches.txt chưa có dòng '%s'. Thiếu dòng này thì Frappe Cloud không chạy migrate." % (appver_pr, can))
	return loi


def giai_ten_git(ten):
	"""Tên tệp trong tiêu đề diff. Git đặt tên có dấu, dấu nháy, tab trong dấu nháy
	và mã hoá bát phân theo byte UTF-8 ("b/ghi-ch\\303\\272.md")."""
	if not (len(ten) >= 2 and ten[0] == ten[-1] == '"'):
		return ten
	thoat = {"n": b"\n", "t": b"\t", '"': b'"', "\\": b"\\", "a": b"\a", "b": b"\b", "f": b"\f", "r": b"\r", "v": b"\v"}
	ra, i, s = bytearray(), 0, ten[1:-1]
	while i < len(s):
		c = s[i]
		if c == "\\" and i + 1 < len(s):
			if s[i + 1:i + 4].isdigit() and len(s[i + 1:i + 4]) == 3:
				ra.append(int(s[i + 1:i + 4], 8))
				i += 4
				continue
			ra += thoat.get(s[i + 1], s[i + 1].encode("utf-8"))
			i += 2
			continue
		ra += c.encode("utf-8")
		i += 1
	return ra.decode("utf-8", "replace")


def dong_them(diff):
	"""[(tệp, số dòng, nội dung)] từ `git diff -U0`."""
	ra, tep, so = [], None, 0
	for d in diff.splitlines():
		if d.startswith("+++ "):
			ten = giai_ten_git(d[4:].rstrip("\t"))
			tep = ten[2:] if ten.startswith("b/") else None
		elif d.startswith("@@"):
			m = re.search(r"\+(\d+)", d)
			so = int(m.group(1)) if m else 0
		elif d.startswith("+") and tep:
			ra.append((tep, so, d[1:]))
			so += 1
	return ra


def tim_gach(dong):
	"""C7."""
	return [(t, s, "C7 có em dash hoặc en dash, dùng gạch ngang thường") for t, s, c in dong
		if t.endswith(DUOI_CHU) and MAU_GACH.search(c)]


def tim_bi_mat(dong):
	"""C9. Áp cho mọi tệp."""
	ra = []
	for t, s, c in dong:
		for ten, mau in MAU_BI_MAT:
			if mau.search(c):
				ra.append((t, s, "C9 có dạng %s trên dòng thêm mới. Không đưa bí mật vào repo" % ten))
				break
	return ra


def la_so_gia(so):
	"""Dãy số rõ là giả: ít chữ số khác nhau (0909111222), có đoạn tăng dần 4 chữ số
	(0912345678), ba số lặp (0903000111), nhiều số 0 liền, hay định danh công khai
	của công ty. Số thật hiếm khi như vậy; số giả người viết ca hay đặt như vậy."""
	so = re.sub(r"\D", "", so)
	if so.startswith("84") and len(so) == 11:
		so = "0" + so[2:]
	if not so or so in DINH_DANH_CONG_KHAI:
		return True
	if len(set(so)) <= 5 or "0000" in so:
		return True
	if any(so[i:i + 3] == so[i] * 3 for i in range(len(so) - 2)):
		return True
	tang = "0123456789"
	return any(so[i:i + 4] in tang or so[i:i + 4] in tang[::-1] for i in range(len(so) - 3))


def luhn(so):
	so = re.sub(r"\D", "", so)
	tong = 0
	for i, ch in enumerate(reversed(so)):
		n = int(ch)
		if i % 2:
			n *= 2
			if n > 9:
				n -= 9
		tong += n
	return tong % 10 == 0


def tim_du_lieu_that(dong):
	"""C8. Chỉ xét ca kiểm, tài liệu, công cụ và tệp .md."""
	ra = []
	for t, s, c in dong:
		if BO_QUA in c or not (t.startswith(VUNG_DU_LIEU) or t.endswith(".md")):
			continue
		ly = None
		for m in MAU_THE.finditer(c):
			so = re.sub(r"\D", "", m.group(1))
			if 13 <= len(so) <= 19 and luhn(so) and not la_so_gia(so):
				ly = "số giống số thẻ"
				break
		if not ly:
			for mau, ten in ((MAU_SDT, "số điện thoại"), (MAU_MST, "mã số thuế"), (MAU_STK, "số tài khoản"),
					(MAU_SAO_KE, "số tài khoản hoặc số thẻ trong mô tả sao kê")):
				# Xét MỌI số trên dòng: số giả đứng trước không được che số thật phía sau.
				if any(not la_so_gia(m.group(1)) for m in mau.finditer(c)):
					ly = ten
					break
		if not ly:
			for m in MAU_EMAIL.finditer(c):
				mien = m.group(1).lower()
				ten = c[m.start():m.end()].split("@")[0].lower()
				# Email cá nhân thật: hộp thư miễn phí, tên dài hoặc có số (ten.ho1996@...).
				if mien in MIEN_CA_NHAN and not ten.startswith(("thevagabond", "kiem", "test", "gia", "noreply")) \
						and (len(ten) >= 10 or re.search(r"\d", ten)):
					ly = "email cá nhân"
					break
		if ly:
			ra.append((t, s, "C8 dòng thêm mới có %s trông như dữ liệu thật. Dùng dữ liệu giả cùng dạng; chắc chắn là giả thì ghi chú '%s' cuối dòng" % (ly, BO_QUA)))
	return ra


def xoa_nhieu(numstat):
	"""C10, chỉ cảnh báo. numstat: dòng của `git diff --numstat`."""
	ra = []
	for d in numstat.splitlines():
		p = d.split("\t")
		if len(p) == 3 and p[1].isdigit() and int(p[1]) >= NGUONG_XOA:
			ra.append("C10 PR xoá %s dòng ở %s. Người rà kiểm đây có phải phần của PR không, hay mất code phiên khác" % (p[1], p[2]))
	return ra


def dang_chan(hom_nay, chan_tu=CHAN_TU):
	return str(hom_nay) >= chan_tu


# --------------------------------------------------------------- phần chạm git

def _git(*a, kiem=True):
	# core.quotePath=false: tên tệp có dấu ra nguyên chữ, không bị đặt trong dấu nháy.
	r = subprocess.run(("git", "-c", "core.quotePath=false") + a, capture_output=True, text=True)
	if kiem and r.returncode:
		raise RuntimeError("git %s: %s" % (" ".join(a), r.stderr.strip()))
	return r.stdout


def _tim_nen(ep):
	if ep:
		return ep
	if os.environ.get("GITHUB_ACTIONS"):
		# CI lấy commit gộp của PR (cha đầu là nhánh nền). Checkout nông thì đào thêm một tầng.
		if subprocess.run(("git", "rev-parse", "-q", "--verify", "HEAD^1"), capture_output=True).returncode:
			_git("fetch", "-q", "--deepen=1", "origin", kiem=False)
		return _git("rev-parse", "HEAD^1").strip()
	return _git("merge-base", "origin/main", "HEAD").strip()


MUC = ":"  # bản đã stage (index)


def _doc(rev, tep):
	if rev is None:
		try:
			return open(tep, encoding="utf-8").read()
		except OSError:
			return ""
	return _git("show", (":" + tep) if rev == MUC else "%s:%s" % (rev, tep), kiem=False)


def chay(base=None, cay=False, muc=False):
	"""Trả (lỗi, cảnh báo): lỗi là danh sách (tệp, dòng, câu).
	Mặc định so HEAD; cay=True so bản làm việc; muc=True so bản đã stage, là thứ `git commit` sẽ ghi."""
	nen = _tim_nen(base)
	# Thứ tự đối số: luôn nền trước, bản PR sau.
	doi = ["--cached", nen] if muc else ([nen] if cay else [nen, "HEAD"])
	diff = _git("diff", "-U0", "--no-color", "--no-ext-diff", *doi)
	ten = [giai_ten_git(t) for t in _git("diff", "--name-only", *doi).splitlines() if t]
	numstat = _git("diff", "--numstat", *doi)
	pr_rev = MUC if muc else (None if cay else "HEAD")
	loi = []
	an, ap = doc_appver(_doc(nen, TEP_APPVER)), doc_appver(_doc(pr_rev, TEP_APPVER))
	loi += [(TEP_APPVER, 0, c) for c in kiem_appver(an, ap, any(la_ma_app(t) for t in ten))]
	if TEP_PATCHES in ten or (an is not None and ap is not None and ap > an):
		loi += [(TEP_PATCHES, 0, c) for c in kiem_patches(_doc(nen, TEP_PATCHES), _doc(pr_rev, TEP_PATCHES), an, ap)]
	them = dong_them(diff)
	loi += tim_gach(them) + tim_bi_mat(them) + tim_du_lieu_that(them)
	return loi, xoa_nhieu(numstat)


def main(argv):
	base, cay, ep_canh_bao = None, "--cay" in argv, "--canh-bao" in argv
	if "--base" in argv:
		base = argv[argv.index("--base") + 1]
	loi, canh = chay(base, cay)
	chan = dang_chan(datetime.date.today()) and not ep_canh_bao
	gh = bool(os.environ.get("GITHUB_ACTIONS"))
	muc = "error" if chan else "warning"
	for t, s, c in loi:
		if gh:
			print("::%s file=%s,line=%d::%s" % (muc, t, max(s, 1), c))
		else:
			print("%s %s:%d %s" % ("LỖI" if chan else "CẢNH BÁO", t, s, c))
	for c in canh:
		print("::warning::%s" % c if gh else "CẢNH BÁO " + c)
	if not loi:
		print("Chốt chặn: không có lỗi.")
	elif not chan:
		print("Chốt chặn: %d lỗi, đang ở chế độ cảnh báo tới hết ngày trước %s." % (len(loi), CHAN_TU))
	return 1 if (loi and chan) else 0


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
