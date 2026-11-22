#!/usr/bin/env python3
"""Hook PreToolUse của Claude Code: trước `git commit` hoặc `git push` chạy
cong_cu/chot_chan.py trên cả phần chưa commit.

Từ ngày CHAN_TU, có lỗi thì trả mã 2 để Claude Code chặn lệnh và đưa lỗi cho
model sửa. Trước ngày đó, hoặc khi chính hook gặp trục trặc, luôn cho lệnh
chạy (mã 0): hook không bao giờ được làm kẹt phiên vì lỗi của chính nó.
"""
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
	try:
		lenh = (json.load(sys.stdin).get("tool_input") or {}).get("command") or ""
	except Exception:
		return 0
	if "git commit" not in lenh and "git push" not in lenh:
		return 0
	try:
		import chot_chan as cc
		loi, _canh = cc.chay(cay=True)
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
