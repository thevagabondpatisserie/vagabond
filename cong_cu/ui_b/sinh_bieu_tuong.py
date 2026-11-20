# -*- coding: utf-8 -*-
"""Sinh khối biểu tượng trong 81-ui-b.js và bảng đối chiếu trong docs.

    python3 cong_cu/ui_b/sinh_bieu_tuong.py           ghi lại
    python3 cong_cu/ui_b/sinh_bieu_tuong.py --kiem    chỉ so, lệch trả mã 1
    python3 cong_cu/ui_b/sinh_bieu_tuong.py --lay <thư mục lucide-static/icons>
        cập nhật lucide.json từ gói npm lucide-static (chỉ người giữ tích hợp chạy)

Nét vẽ lấy từ bộ Lucide (giấy phép ISC), lưu sẵn trong cong_cu/ui_b/lucide.json
để repo không cần npm. App nhúng SVG trong mã, không tải ngoài.
"""
import io
import json
import os
import re
import sys

O_DAY = os.path.dirname(os.path.abspath(__file__))
GOC = os.path.dirname(os.path.dirname(O_DAY))
sys.path.insert(0, O_DAY)
import bieu_tuong_nguon as N  # noqa: E402

TEP_LUCIDE = os.path.join(O_DAY, "lucide.json")
TEP_JS = os.path.join(GOC, "vagabond", "public", "js", "bep", "81-ui-b.js")
TEP_DOC = os.path.join(GOC, "docs", "ui-nghe-si", "bang-bieu-tuong.md")
MOC_DAU = "/* === BIEU TUONG UI-B: MAY SINH RA, DUNG SUA TAY === */"
MOC_CUOI = "/* === HET BIEU TUONG UI-B === */"


def ten_can():
	return sorted(set(N.GOC.values()) | set(N.DE_XUAT.values()) | set(N.KHUNG))


def lay(thu_muc):
	kq = {}
	thieu = []
	for ten in ten_can():
		d = os.path.join(thu_muc, ten + ".svg")
		if not os.path.exists(d):
			thieu.append(ten)
			continue
		s = io.open(d, encoding="utf-8").read()
		trong = re.search(r"<svg[^>]*>(.*)</svg>", s, re.S).group(1)
		kq[ten] = re.sub(r"\s+", " ", trong).replace("> <", "><").replace(" />", "/>").strip()
	if thieu:
		print("THIẾU trong lucide-static: " + ", ".join(thieu))
		return 1
	pb = json.load(io.open(os.path.join(os.path.dirname(thu_muc), "package.json"), encoding="utf-8"))["version"]
	io.open(TEP_LUCIDE, "w", encoding="utf-8").write(json.dumps(
		{"nguon": "lucide-static", "phien_ban": pb, "giay_phep": "ISC", "net": kq}, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
	print("Đã ghi lucide.json: %d biểu tượng, lucide-static %s" % (len(kq), pb))
	return 0


def khoi_js():
	L = json.load(io.open(TEP_LUCIDE, encoding="utf-8"))
	emoji = {}
	emoji.update(N.DE_XUAT)
	emoji.update(N.GOC)
	d = [MOC_DAU]
	d.append("/* Nguon: cong_cu/ui_b/bieu_tuong_nguon.py va lucide.json (lucide-static %s, giay phep ISC)." % L["phien_ban"])
	d.append("   Sua ben do roi chay: python3 cong_cu/ui_b/sinh_bieu_tuong.py */")
	d.append("var UIB_NET = {")
	ten = ten_can()
	for i, t in enumerate(ten):
		d.append("  %s: %s%s" % (json.dumps(t), json.dumps(L["net"][t], ensure_ascii=False), "," if i < len(ten) - 1 else ""))
	d.append("};")
	d.append("var UIB_EMOJI = {")
	cap = sorted(emoji.items())
	for i, (e, t) in enumerate(cap):
		d.append("  %s: %s%s" % (json.dumps(e, ensure_ascii=False), json.dumps(t), "," if i < len(cap) - 1 else ""))
	d.append("};")
	d.append("var UIB_CHAM = " + json.dumps(N.CHAM, ensure_ascii=False, sort_keys=True) + ";")
	d.append(MOC_CUOI)
	return "\n".join(d)


def doc_md():
	L = json.load(io.open(TEP_LUCIDE, encoding="utf-8"))
	d = ["# Bảng đối chiếu emoji sang biểu tượng (giao diện ui-b)", "",
		"Tệp do `cong_cu/ui_b/sinh_bieu_tuong.py` sinh ra từ `cong_cu/ui_b/bieu_tuong_nguon.py`. Đừng sửa tay.",
		"Bộ nét: Lucide (lucide-static %s, giấy phép ISC), nét 1.6, nhúng trong app." % L["phien_ban"], "",
		"Việc thay chỉ làm ở LỚP VẼ giao diện. Chuỗi dữ liệu, tin gửi đi và mẫu in giữ nguyên emoji.", "",
		"## Bảng gốc anh Việt đã duyệt (%d ký tự)" % len(N.GOC), "", "| Emoji | Biểu tượng |", "|---|---|"]
	for e, t in N.GOC.items():
		d.append("| %s | %s |" % (e, t))
	d += ["", "## Đề xuất cho phần còn lại (%d ký tự, chờ duyệt)" % len(N.DE_XUAT), "",
		"Một số ký tự (trái cây, hoa, lá cờ) chỉ xuất hiện trong tên món hoặc nội dung, không phải biểu tượng chức năng; vẫn có dòng để không sót.", "",
		"| Emoji | Biểu tượng đề xuất |", "|---|---|"]
	for e, t in N.DE_XUAT.items():
		d.append("| %s | %s |" % (e, t))
	nghia = {"xong": "Xong (#116B4A)", "cho": "Chờ (#9C4A08)", "loi": "Cần xử lý (#C2361F)", "huy": "Huỷ (#656D73)", "nhom": "màu nhóm"}
	d += ["", "## Chấm màu trạng thái (%d ký tự)" % len(N.CHAM), "", "Vẽ thành chấm tròn tô màu, không thành biểu tượng nét.", "",
		"| Emoji | Chấm |", "|---|---|"]
	for e, t in N.CHAM.items():
		d.append("| %s | %s |" % (e, nghia[t]))
	d += ["", "## Biểu tượng khung chung gọi theo tên", "", ", ".join(N.KHUNG) + ".", ""]
	return "\n".join(d)


def ghi_js(kiem):
	s = io.open(TEP_JS, encoding="utf-8").read()
	a, b = s.find(MOC_DAU), s.find(MOC_CUOI)
	if a < 0 or b < 0:
		print("Không thấy hai dấu mốc trong 81-ui-b.js")
		return 1
	moi = s[:a] + khoi_js() + s[b + len(MOC_CUOI):]
	if moi == s:
		return 0
	if kiem:
		print("LỆCH: khối biểu tượng trong 81-ui-b.js không khớp nguồn.")
		return 1
	io.open(TEP_JS, "w", encoding="utf-8").write(moi)
	print("Đã ghi khối biểu tượng vào 81-ui-b.js")
	return 0


def ghi_doc(kiem):
	moi = doc_md()
	cu = io.open(TEP_DOC, encoding="utf-8").read() if os.path.exists(TEP_DOC) else None
	if cu == moi:
		return 0
	if kiem:
		print("LỆCH: docs/ui-nghe-si/bang-bieu-tuong.md không khớp nguồn.")
		return 1
	io.open(TEP_DOC, "w", encoding="utf-8").write(moi)
	print("Đã ghi docs/ui-nghe-si/bang-bieu-tuong.md")
	return 0


def main(argv):
	if "--lay" in argv:
		return lay(argv[argv.index("--lay") + 1])
	kiem = "--kiem" in argv
	ma = ghi_js(kiem) | ghi_doc(kiem)
	if kiem and not ma:
		print("Khớp: khối biểu tượng và bảng đối chiếu trùng nguồn.")
	return ma


if __name__ == "__main__":
	sys.exit(main(sys.argv[1:]))
