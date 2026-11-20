# -*- coding: utf-8 -*-
"""Kiểm KHAI BÁO của lớp vẽ ui-b (bản 4 mục 7 và mục 9): chạy trên mã nguồn, không cần trình duyệt.

    python3 cong_cu/ui_b/kiem_khai_bao.py        mã trả 0 là đạt

Lấy đúng chuỗi CSS mà app sẽ chèn (gọi uiBCss() của 81-ui-b.js bằng node) rồi soi:
  - màu: chỉ màu trong bộ chuẩn (mục 3), trắng, và các lớp mờ dựng từ đúng các màu đó;
  - cỡ chữ: chỉ 5 cỡ Be Vietnam Pro và 3 cỡ Doto;
  - bo góc: chỉ 6 mức có tên (qua biến --ui-r-*), hoặc 0;
  - khoảng cách (margin, padding, gap): bội số của 4, hoặc biến có tên;
  - phông: chỉ qua biến --ui-font, --ui-dot hoặc inherit;
  - mọi khai báo nằm dưới html.ui-b (trừ @font-face).
Luật bội số của 4 chỉ áp cho margin, padding, gap; chiều rộng, cao, vị trí không thuộc phép này.
Kết quả hiển thị (vùng bấm, tương phản, tràn chữ) do máy chụp cong_cu/ui_b/chup.cjs đo.
"""
import os
import re
import subprocess
import sys

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEP = os.path.join(GOC, "vagabond", "public", "js", "bep", "81-ui-b.js")

MAU = set(x.lower() for x in (
	"#F3EFE7", "#FEFEFD", "#EAF4F3", "#121619", "#4B5359", "#656D73", "#4FDBF2", "#0A7186", "#23245C",
	"#116B4A", "#9C4A08", "#C2361F", "#FDB738", "#F36E3E", "#5FD69B", "#8E9BFF", "#E8C98A", "#fff", "#ffffff", "#000"))
RGB = set(("255,255,255", "18,22,25", "243,239,231", "79,219,242", "253,183,56", "142,155,255", "243,110,62", "95,214,155", "232,201,138"))
CO_CHU = set((13, 15, 17, 20, 24, 30, 40, 48))
BO_GOC = set((14, 16, 18, 24, 26, 999))


def lay_css():
	ma = (
		'var fs=require("fs"),vm=require("vm");'
		'var s=fs.readFileSync(process.argv[1],"utf8");'
		'var c={console:console};vm.createContext(c);'
		'vm.runInContext(s+";this.__css=uiBCss();",c);'
		'process.stdout.write(c.__css);'
	)
	ra = subprocess.run(["node", "-e", ma, TEP], capture_output=True)
	if ra.returncode != 0:
		raise RuntimeError("Không chạy được uiBCss(): " + ra.stderr.decode("utf-8")[-400:])
	return ra.stdout.decode("utf-8")


def tach_luat(css):
	"""[(bộ chọn, khai báo)] phẳng, bỏ @font-face, mở @media và @supports."""
	kq = []
	i = 0
	n = len(css)
	while i < n:
		j = css.find("{", i)
		if j < 0:
			break
		dau = css[i:j].strip()
		if dau.startswith("@font-face"):
			i = css.find("}", j) + 1
			continue
		if dau.startswith("@media") or dau.startswith("@supports"):
			sau, k = 1, j + 1
			while k < n and sau:
				sau += css[k] == "{"
				sau -= css[k] == "}"
				k += 1
			kq.extend(tach_luat(css[j + 1:k - 1]))
			i = k
			continue
		k = css.find("}", j)
		kq.append((dau, css[j + 1:k]))
		i = k + 1
	return kq


# Luật khung chung PHẢI có. Thiếu là chuỗi CSS lấy ra không phải lớp vẽ thật.
PHAI_CO = ("html.ui-b .vh", "html.ui-b .vf", "html.ui-b .card", "html.ui-b .btn", "html.ui-b .gt")


def kiem(css):
	loi = []
	if not tach_luat(css):
		loi.append("không đọc được luật CSS nào: chưa kiểm được gì")
	for chon, kb in tach_luat(css):
		for c in chon.split(","):
			if not c.strip().startswith("html.ui-b"):
				loi.append("bộ chọn không nằm dưới html.ui-b: " + c.strip()[:60])
		for dong in re.split(r";(?![^(]*\))", kb):
			if ":" not in dong:
				continue
			tt, gt = dong.split(":", 1)
			tt, gt = tt.strip(), gt.strip()
			khong_url = re.sub(r"url\((\"[^\"]*\"|[^)]*)\)", "", gt)
			for m in re.findall(r"#[0-9a-fA-F]{3,8}\b", khong_url):
				if m.lower() not in MAU:
					loi.append("%s { %s } màu ngoài bộ chuẩn: %s" % (chon[:40], tt, m))
			for m in re.findall(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)", khong_url):
				if ",".join(m) not in RGB:
					loi.append("%s { %s } màu ngoài bộ chuẩn: rgb(%s)" % (chon[:40], tt, ",".join(m)))
			if tt.startswith("--"):
				continue
			if tt == "font-size":
				m = re.match(r"^(\d+(?:\.\d+)?)px$", gt)
				if not (m and float(m.group(1)) in CO_CHU) and not gt.startswith("var(--ui-fs-"):
					loi.append("%s cỡ chữ ngoài thang: %s" % (chon[:40], gt))
			elif tt == "font-family":
				if gt not in ("var(--ui-font)", "var(--ui-dot)", "inherit"):
					loi.append("%s phông không qua biến: %s" % (chon[:40], gt))
			elif tt == "border-radius":
				for p in gt.split():
					if p == "0" or p.startswith("var(--ui-r-"):
						continue
					loi.append("%s bo góc không qua biến có tên: %s" % (chon[:40], gt))
					break
			elif re.match(r"^(margin|padding|gap)(-(top|right|bottom|left))?$", tt):
				bo_var = re.sub(r"var\([^()]*\)", "", re.sub(r"env\([^()]*\)", "", gt))
				for so in re.findall(r"-?\d+(?:\.\d+)?px", bo_var):
					if float(so[:-2]) % 4:
						loi.append("%s { %s: %s } khoảng cách không phải bội số của 4 và không qua biến có tên" % (chon[:40], tt, gt))
	return loi


def main():
	css = lay_css()
	loi = kiem(css)
	chon = [c for c, _ in tach_luat(css)]
	for can in PHAI_CO:
		if not any(can in c for c in chon):
			loi.append("thiếu luật khung chung " + can + ": chuỗi CSS lấy ra không đủ")
	for x in loi:
		print("TRƯỢT  " + x)
	print("%d luật, %d khai báo trượt." % (len(tach_luat(css)), len(loi)))
	return 1 if loi else 0


if __name__ == "__main__":
	sys.exit(main())
