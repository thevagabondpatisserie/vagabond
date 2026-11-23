#!/usr/bin/env python3
"""Hook PreToolUse của Claude Code: trước `git commit` hoặc `git push` chạy
cong_cu/chot_chan.py trên đúng thứ lệnh sẽ ghi hay đẩy đi.

- `git commit`: dựng một index tạm giống hệt index Git sẽ ghi rồi xét nó:
  - không tham số tệp: index hiện tại;
  - `-a`, `--all`: index hiện tại cộng bản làm việc của mọi tệp đang theo dõi (`git add -u`);
  - có đường dẫn (mặc định `--only`): HEAD cộng bản làm việc của đúng các đường dẫn đó;
  - `-i`, `--include` kèm đường dẫn: index hiện tại cộng bản làm việc của các đường dẫn đó.
  Không xét HEAD, để commit sửa lỗi của commit cũ (kể cả --amend) đi được.
  Các `git add` đứng trước commit trong cùng lệnh được chạy lại trên index tạm;
  `cd` được theo. Có lệnh khác đứng trước (có thể đổi tệp), không đọc được lệnh
  (dấu nháy hở, --pathspec-from-file) hay dựng index tạm hỏng thì xét chặt cả
  index lẫn bản làm việc.
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


AN_TOAN = {"cd", "pwd", "ls", "echo", "true", ":"}
GIT_CHI_DOC = {"status", "diff", "log", "fetch", "show", "rev-parse", "branch"}
ADD_TUONG_TAC = {"-p", "--patch", "-i", "--interactive", "-e", "--edit"}


def tach_cau(tu):
	"""Chia các từ thành từng lệnh theo toán tử."""
	ra, cau = [], []
	for t in tu:
		if t in TOAN_TU:
			if cau:
				ra.append(cau)
			cau = []
		else:
			cau.append(t)
	if cau:
		ra.append(cau)
	return ra


def doc_commit(lenh, cwd=None):
	"""Đọc lần `git commit` đầu tiên trong lệnh shell và các lệnh đứng trước nó.
	Trả None khi lệnh không có commit, "?" khi không đọc được, còn lại là dict:
	all, include, duong_dan (của commit); truoc: [(thư mục, tham số)] của các
	`git add` đứng trước; chat: có lệnh đứng trước có thể đổi tệp mà hook không
	mô phỏng được; cwd: thư mục sau các lệnh cd."""
	try:
		tu = tach_lenh(lenh)
	except ValueError:
		return "?" if "git commit" in lenh else None
	cwd = cwd or os.getcwd()
	truoc, chat = [], False
	for cau in tach_cau(tu):
		if cau[:2] == ["git", "commit"]:
			kq = _doc_tham_so_commit(cau[2:])
			if kq != "?":
				kq.update(truoc=truoc, chat=chat, cwd=cwd)
			return kq
		if cau[0] == "cd":
			dich = os.path.expandvars(os.path.expanduser(cau[1] if len(cau) > 1 else "~"))
			cwd = os.path.normpath(os.path.join(cwd, dich))
		elif cau[0] in AN_TOAN:
			pass
		elif cau[0] == "git" and len(cau) > 1 and cau[1] == "add" and not ADD_TUONG_TAC.intersection(cau[2:]):
			truoc.append((cwd, cau[2:]))
		elif cau[0] == "git" and len(cau) > 1 and cau[1] in GIT_CHI_DOC:
			pass
		else:
			chat = True
	return None


def _doc_tham_so_commit(ts):
	kq = {"all": False, "include": False, "duong_dan": []}
	j, het_tham_so = 0, False
	while j < len(ts):
		t = ts[j]
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
	"""Dựng index tạm giống index `git commit` sẽ ghi, sau cả các `git add` đứng
	trước trong cùng lệnh. Trả đường dẫn tệp tạm, hoặc None khi index hiện tại đã
	đúng là thứ sẽ ghi. Lỗi git thì ném ngoại lệ để nơi gọi chuyển sang xét chặt."""
	if not pt["all"] and not pt["duong_dan"] and not pt["truoc"]:
		return None
	goc = os.path.abspath(subprocess.run(("git", "rev-parse", "--git-path", "index"),
		capture_output=True, text=True, check=True).stdout.strip())
	thu_muc = tempfile.mkdtemp(prefix="chot_chan_")
	tam = os.path.join(thu_muc, "index")
	if os.path.exists(goc):
		shutil.copyfile(goc, tam)
	env = dict(os.environ, GIT_INDEX_FILE=tam)
	for noi, ts in pt["truoc"]:
		subprocess.run(("git", "add") + tuple(ts), cwd=noi, env=env, capture_output=True, text=True, check=True)
	dd = pt["duong_dan"]
	if pt["all"]:
		_git(env, "add", "-u")
	elif dd and pt["include"]:
		_git(env, "add", "-u", "--", *dd)
	elif dd:
		# --only: HEAD, cộng tệp mới đã stage khớp đường dẫn, cộng bản làm việc của các đường dẫn.
		# -z: tên tệp có dấu ra nguyên chữ, không bị đặt trong dấu nháy.
		moi = subprocess.run(("git", "diff", "--cached", "--name-only", "-z", "--diff-filter=A", "--", *dd),
			env=env, capture_output=True, text=True, check=True).stdout.split("\0")
		tam = os.path.join(thu_muc, "index-only")
		env = dict(os.environ, GIT_INDEX_FILE=tam)
		_git(env, "read-tree", "HEAD")
		moi = [x for x in moi if x]
		if moi:
			_git(env, "add", "--", *moi)
		_git(env, "add", "-u", "--", *dd)
	return tam


def kieu_can_xet(lenh):
	"""[(tham số cho chot_chan.chay, index tạm hoặc None)] cho một lệnh shell."""
	chat = [({"muc": True}, None), ({"cay": True}, None)]
	pt = doc_commit(lenh)
	if pt == "?":
		return chat
	if pt is not None:
		if os.path.isdir(pt["cwd"]):
			os.chdir(pt["cwd"])
		try:
			tam = dung_muc_tam(pt)
		except Exception:
			return chat
		return [({"muc": True}, tam)] + ([({"cay": True}, None)] if pt["chat"] else [])
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
	cu = os.getcwd()
	try:
		import chot_chan as cc
		kieu_xet = kieu_can_xet(lenh)
		if not kieu_xet:
			return 0
		loi = xet(cc, kieu_xet)
	except Exception:
		return 0
	finally:
		os.chdir(cu)
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
