#!/usr/bin/env python3
"""Hook PreToolUse của Claude Code: trước `git commit` hoặc `git push` chạy
cong_cu/chot_chan.py trên đúng thứ lệnh sẽ ghi hay đẩy đi.

- `git commit`: dựng một index tạm giống hệt index Git sẽ ghi rồi xét nó:
  - không tham số tệp: index hiện tại;
  - `-a`, `--all`: index hiện tại cộng bản làm việc của mọi tệp đang theo dõi (`git add -u`);
  - có đường dẫn (mặc định `--only`): HEAD cộng bản làm việc của đúng các đường dẫn đó;
  - `-i`, `--include` kèm đường dẫn: index hiện tại cộng bản làm việc của các đường dẫn đó.
  Không xét HEAD, để commit sửa lỗi của commit cũ (kể cả --amend) đi được.
  Không đọc được lệnh (heredoc lạ, dấu nháy hở) thì xét cả index lẫn bản làm việc.
- `git push` (không kèm commit trong cùng lệnh): HEAD.

Từ ngày CHAN_TU, có lỗi thì trả mã 2 để Claude Code chặn lệnh và đưa lỗi cho
model sửa. Trước ngày đó, hoặc khi chính hook gặp trục trặc, luôn cho lệnh
chạy (mã 0): hook không bao giờ được làm kẹt phiên vì lỗi của chính nó.
"""
import datetime
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TOAN_TU = {"&&", "||", ";", "|", "&", "\n", "<", "<<", "<<<", ">", ">>", "(", ")"}
# Tham số của git commit có giá trị đi kèm.
CO_GIA_TRI_NGAN = set("mFCct")
CO_GIA_TRI_DAI = {"--message", "--file", "--reuse-message", "--reedit-message", "--author", "--date",
	"--template", "--fixup", "--squash", "--cleanup", "--trailer", "--pathspec-from-file"}


def tach_lenh(lenh):
	"""Các từ của lệnh shell; toán tử (&&, ;, |, xuống dòng, <<) là một từ riêng."""
	l = shlex.shlex(lenh, posix=True, punctuation_chars="();<>|&\n")
	l.whitespace = " \t\r"
	l.whitespace_split = True
	return list(l)


def doc_commit(lenh):
	"""Đọc lần `git commit` đầu tiên trong lệnh shell.
	Trả None khi lệnh không có commit, "?" khi không đọc được,
	còn lại là dict {all, include, duong_dan}."""
	try:
		tu = tach_lenh(lenh)
	except ValueError:
		return "?" if "git commit" in lenh else None
	for i in range(len(tu) - 1):
		if tu[i] == "git" and tu[i + 1] == "commit":
			break
	else:
		return None
	kq = {"all": False, "include": False, "duong_dan": []}
	j, het_tham_so = i + 2, False
	while j < len(tu) and tu[j] not in TOAN_TU:
		t = tu[j]
		j += 1
		if het_tham_so or not t.startswith("-") or t == "-":
			kq["duong_dan"].append(t)
		elif t == "--":
			het_tham_so = True
		elif t.startswith("--"):
			ten = t.split("=", 1)[0]
			if ten == "--pathspec-from-file":
				return "?"  # đường dẫn nằm trong tệp: không đoán, xét chặt
			if ten == "--all":
				kq["all"] = True
			elif ten == "--include":
				kq["include"] = True
			elif ten in CO_GIA_TRI_DAI and "=" not in t:
				j += 1
		else:
			for k, c in enumerate(t[1:]):
				if c == "a":
					kq["all"] = True
				elif c == "i":
					kq["include"] = True
				elif c in CO_GIA_TRI_NGAN:
					if not t[k + 2:]:
						j += 1
					break
	return kq


def _git(env, *a):
	subprocess.run(("git",) + a, env=env, capture_output=True, text=True, check=True)


def dung_muc_tam(pt):
	"""Dựng index tạm giống index `git commit` sẽ ghi. Trả đường dẫn tệp tạm, hoặc
	None khi index hiện tại đã đúng là thứ sẽ ghi."""
	if not pt["all"] and not pt["duong_dan"]:
		return None
	goc = subprocess.run(("git", "rev-parse", "--git-path", "index"), capture_output=True, text=True, check=True).stdout.strip()
	thu_muc = tempfile.mkdtemp(prefix="chot_chan_")
	tam = os.path.join(thu_muc, "index")
	env = dict(os.environ, GIT_INDEX_FILE=tam)
	dd = pt["duong_dan"]
	if pt["all"]:
		shutil.copyfile(goc, tam)
		_git(env, "add", "-u")
	elif pt["include"]:
		shutil.copyfile(goc, tam)
		_git(env, "add", "-u", "--", *dd)
	else:
		# --only: HEAD, cộng tệp mới đã stage khớp đường dẫn, cộng bản làm việc của các đường dẫn.
		moi = subprocess.run(("git", "diff", "--cached", "--name-only", "--diff-filter=A", "--", *dd),
			capture_output=True, text=True, check=True).stdout.split("\n")
		_git(env, "read-tree", "HEAD")
		moi = [x for x in moi if x]
		if moi:
			_git(env, "add", "--", *moi)
		_git(env, "add", "-u", "--", *dd)
	return tam


def kieu_can_xet(lenh):
	"""[(tham số cho chot_chan.chay, index tạm hoặc None)] cho một lệnh shell."""
	pt = doc_commit(lenh)
	if pt == "?":
		return [({"muc": True}, None), ({"cay": True}, None)]
	if pt is not None:
		return [({"muc": True}, dung_muc_tam(pt))]
	if "git push" in lenh:
		return [({}, None)]
	return []


def xet(cc, kieu_xet):
	loi = []
	cu = os.environ.get("GIT_INDEX_FILE")
	try:
		for kieu, tam in kieu_xet:
			if tam:
				os.environ["GIT_INDEX_FILE"] = tam
			try:
				for x in cc.chay(**kieu)[0]:
					if x not in loi:
						loi.append(x)
			finally:
				if cu is None:
					os.environ.pop("GIT_INDEX_FILE", None)
				else:
					os.environ["GIT_INDEX_FILE"] = cu
				if tam:
					shutil.rmtree(os.path.dirname(tam), ignore_errors=True)
	finally:
		for _kieu, tam in kieu_xet:
			if tam:
				shutil.rmtree(os.path.dirname(tam), ignore_errors=True)
	return loi


def main():
	try:
		lenh = (json.load(sys.stdin).get("tool_input") or {}).get("command") or ""
	except Exception:
		return 0
	try:
		import chot_chan as cc
		kieu_xet = kieu_can_xet(lenh)
		if not kieu_xet:
			return 0
		loi = xet(cc, kieu_xet)
	except Exception:
		return 0
	if not loi:
		return 0
	chu = "\n".join("%s:%d %s" % x for x in loi)
	if cc.dang_chan(datetime.date.today()):
		sys.stderr.write("Chốt chặn (cong_cu/chot_chan.py) chặn lệnh này:\n" + chu + "\n")
		return 2
	sys.stderr.write("Chốt chặn cảnh báo (chưa chặn trước %s):\n%s\n" % (cc.CHAN_TU, chu))
	return 0


if __name__ == "__main__":
	sys.exit(main())
