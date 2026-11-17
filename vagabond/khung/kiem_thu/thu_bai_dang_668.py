# -*- coding: utf-8 -*-
"""v668 Bài đăng: cỡ ảnh Facebook theo bảng anh Việt gửi 17/11/2026.

Bảng (ảnh CleverAds): ảnh đơn vuông 1200x1200, dọc 960x1200, ngang 1200x800;
2 ảnh ngang 1200x600 hoặc dọc 600x1200; 3 ảnh: ảnh chính 1920x960 hoặc
960x1920 cộng 2 ảnh vuông 1920x1920; 4 ảnh vuông 1920x1920; 5 ảnh trở lên:
ảnh vuông 1920x1920, ảnh phụ 1920x1920 hoặc 1920x1280; Story 1080x1920.

Ca chốt:
  - khung từng ô của lưới Facebook theo số ảnh và hướng ảnh đầu;
  - ảnh đã đúng ô thì đăng nguyên bản, lệch thì hệ thống cắt đúng ô đó
    (trước đây mọi ảnh Facebook bị cắt vuông);
  - bảng Kiểm nhắc đúng ảnh nào bị cắt, cỡ nên làm, ảnh nhỏ hơn cỡ khuyên dùng;
  - nhắc, không chặn duyệt.
"""

import datetime as dt

from vagabond.khung.kiem_thu.nen import ca, gia_lap, la

gia_lap()

from vagabond import bai_dang as x  # noqa: E402

BAY_GIO = dt.datetime(2026, 11, 17, 20, 0)


def _a(khung, rong=0, cao=0, ten=""):
	return {"ten": ten or khung, "url": "/%s.jpg" % khung, "khung": khung, "rong": rong, "cao": cao}


def _bai(anh, kenh=("fb",)):
	return {"kieu": x.KIEU_BAI, "kenh_chon": list(kenh), "anh": anh,
		"ban": {"fb": {"chu": "a"}, "ig": {"chu": "b"}}, "hen_luc": ""}


def _nhac(kiem):
	return [z["chu"] for z in kiem if z["muc"] == "nhac"]


@ca("v668 khung mới nhận ra: 2:1 (1200x600, 1920x960), 1:2 (600x1200), 3:2 (1200x800, 1920x1280); khung cũ không đổi")
def _khung_moi():
	la("1200x600", x.doc_khung(1200, 600), "2:1")
	la("1920x960", x.doc_khung(1920, 960), "2:1")
	la("600x1200", x.doc_khung(600, 1200), "1:2")
	la("1200x800 và 1920x1280", (x.doc_khung(1200, 800), x.doc_khung(1920, 1280)), ("3:2", "3:2"))
	la("khung cũ giữ nguyên", [x.doc_khung(*s) for s in ((1080, 1080), (1080, 1350), (1080, 1920), (1920, 1080), (1200, 628))],
		["1:1", "4:5", "9:16", "16:9", "1.91:1"])


@ca("v668 lưới Facebook: khung từng ô theo số ảnh và hướng ảnh đầu, đúng bảng cỡ ảnh anh Việt gửi")
def _bo_cuc():
	la("1 ảnh dọc, vuông, ngang", [x.bo_cuc_fb([_a(k)]) for k in ("4:5", "1:1", "3:2")], [["4:5"], ["1:1"], ["3:2"]])
	la("1 ảnh 9:16 thì làm 4:5", x.bo_cuc_fb([_a("9:16")]), ["4:5"])
	la("1 ảnh 16:9 thì làm 3:2", x.bo_cuc_fb([_a("16:9")]), ["3:2"])
	la("2 ảnh ngang", x.bo_cuc_fb([_a("2:1"), _a("1:1")]), ["2:1", "2:1"])
	la("2 ảnh dọc", x.bo_cuc_fb([_a("1:2"), _a("4:5")]), ["1:2", "1:2"])
	la("2 ảnh vuông", x.bo_cuc_fb([_a("1:1"), _a("4:5")]), ["1:1", "1:1"])
	la("3 ảnh chính ngang", x.bo_cuc_fb([_a("2:1"), _a("1:1"), _a("4:5")]), ["2:1", "1:1", "1:1"])
	la("3 ảnh chính dọc", x.bo_cuc_fb([_a("4:5"), _a("1:1"), _a("1:1")]), ["1:2", "1:1", "1:1"])
	la("4 ảnh vuông dù ảnh đầu dọc", x.bo_cuc_fb([_a("4:5")] * 4), ["1:1"] * 4)
	la("5 ảnh: ô phụ 3:2 giữ nguyên, ô khác vuông", x.bo_cuc_fb([_a("1:1"), _a("4:5"), _a("3:2"), _a("1:1"), _a("9:16")]),
		["1:1", "1:1", "3:2", "1:1", "1:1"])
	la("không ảnh", x.bo_cuc_fb([]), [])


@ca("v668 ảnh cho Facebook: ảnh đúng ô đăng nguyên bản, lệch ô thì cắt đúng ô; kênh khác và Story không đổi")
def _anh_fb():
	ra = x.anh_cho_kenh([_a("4:5")], "fb")
	la("1 ảnh 4:5: không còn bị cắt vuông", [(a["khung"], a["cat"]) for a in ra], [("4:5", False)])
	ra = x.anh_cho_kenh([_a("2:1"), _a("1:1"), _a("1:1")], "fb")
	la("3 ảnh đúng mẫu: không cắt", [(a["khung"], a["cat"]) for a in ra], [("2:1", False), ("1:1", False), ("1:1", False)])
	ra = x.anh_cho_kenh([_a("4:5"), _a("4:5")], "fb")
	la("2 ảnh 4:5: cắt về 1:2 đúng lưới 2 ảnh dọc", [(a["khung"], a["cat"]) for a in ra], [("1:2", True), ("1:2", True)])
	la("Instagram vẫn 4:5", [a["khung"] for a in x.anh_cho_kenh([_a("1:1"), _a("4:5")], "ig")], ["4:5", "4:5"])
	la("Story Facebook vẫn 9:16", [a["khung"] for a in x.anh_cho_kenh([_a("4:5")], "fb", x.KIEU_STORY)], ["9:16"])


@ca("v668 bảng Kiểm Facebook: nhắc ảnh nào bị cắt kèm cỡ nên làm, nhắc ảnh nhỏ hơn cỡ khuyên dùng; chỉ nhắc, không chặn")
def _kiem_fb():
	k = x.kiem_bai(_bai([_a("1:1", 1200, 1200), _a("4:5", 1080, 1350)]), BAY_GIO)
	la("2 ảnh, ảnh 2 lệch ô vuông", _nhac(k), ["Facebook sẽ cắt ảnh 2 cho đúng lưới 2 ảnh vuông"])
	goi = [z.get("goi_y") for z in k if z["chu"].startswith("Facebook sẽ cắt")][0]
	la("gợi ý cỡ nên làm", goi, "Nên làm ảnh 2 khung 1:1 (1200x1200). Hệ thống cắt giữa ảnh, chữ ở mép có thể mất.")
	la("không chặn", [z["chu"] for z in k if z["muc"] == "chan"], [])
	k = x.kiem_bai(_bai([_a("1:1", 1920, 1920)] * 4), BAY_GIO)
	la("4 ảnh vuông 1920: không nhắc", _nhac(k), [])
	k = x.kiem_bai(_bai([_a("1:1", 1080, 1080)] * 4), BAY_GIO)
	la("4 ảnh vuông 1080 (cỡ phổ biến): không nhắc mờ", _nhac(k), [])
	k = x.kiem_bai(_bai([_a("1:1", 1080, 1080), _a("1:1", 800, 800), _a("1:1", 1079, 1079), _a("1:1", 1920, 1920)]), BAY_GIO)
	la("ảnh dưới 1080 px: nhắc đúng ảnh", _nhac(k), ["Ảnh 2, 3 nhỏ hơn cỡ Facebook khuyên dùng"])
	la("gợi ý cỡ theo bảng", [z.get("goi_y") for z in k if z["chu"].startswith("Ảnh 2")][0],
		"Ảnh dưới 1080 px dễ bị mờ. Cỡ nên làm: 1:1 1920x1920.")
	k = x.kiem_bai(_bai([_a("4:5", 960, 1200)]), BAY_GIO)
	la("1 ảnh dọc 960x1200 đúng bảng: không nhắc", _nhac(k), [])
	k = x.kiem_bai(_bai([_a("4:5", 1080, 1350)]), BAY_GIO)
	la("1 ảnh 1080x1350 của Instagram: không nhắc", _nhac(k), [])
	k = x.kiem_bai(_bai([_a("1:1")] * 2), BAY_GIO)
	la("ảnh không rõ cỡ: không nhắc cỡ", _nhac(k), [])
	k = x.kiem_bai(_bai([_a("1:1", 600, 600), _a("4:5", 1080, 1350)], kenh=("ig",)), BAY_GIO)
	la("không chọn Facebook: không nhắc lưới Facebook", _nhac(k), [])
