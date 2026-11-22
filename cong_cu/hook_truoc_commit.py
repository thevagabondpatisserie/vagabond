#!/usr/bin/env python3
"""Hook PreToolUse của Claude Code: trước `git commit` hoặc `git push` chạy
cong_cu/chot_chan.py trên đúng thứ lệnh sẽ ghi hay đẩy đi:
- `git commit`: bản đã stage; thêm bản làm việc khi có `-a` hoặc `--all`.
  Không xét HEAD, để commit sửa lỗi của commit cũ (kể cả --amend) đi được.
- `git push` (không kèm commit trong cùng lệnh): HEAD.

Từ ngày CHAN_TU, có lỗi thì trả mã 2 để Claude Code chặn lệnh và đưa lỗi cho
model sửa. Trước ngày đó, hoặc khi chính hook gặp trục trặc, luôn cho lệnh
chạy (mã 0): hook không bao giờ được làm kẹt phiên vì lỗi của chính nó.
"""
import datetime
import json
import os
import re
import sys

MAU_COMMIT_A = re.compile(r"(?:^|\s)(?:-[A-Za-z]*a[A-Za-z]*|--all)(?=\s|$)")


def kieu_can_xet(lenh):
	"""Các bản cần xét cho một lệnh shell, theo tham số của chot_chan.chay."""
	if "git commit" in lenh:
		sau = lenh.split("git commit", 1)[1].split("&&")[0].split(";")[0]
		return [{"muc": True}] + ([{"cay": True}] if MAU_COMMIT_A.search(sau) else [])
	if "git push" in lenh:
		return [{}]
	return []

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
	try:
		lenh = (json.load(sys.stdin).get("tool_input") or {}).get("command") or ""
	except Exception:
		return 0
	kieu_xet = kieu_can_xet(lenh)
	if not kieu_xet:
		return 0
	try:
		import chot_chan as cc
		loi = []
		for kieu in kieu_xet:
			for x in cc.chay(**kieu)[0]:
				if x not in loi:
					loi.append(x)
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
