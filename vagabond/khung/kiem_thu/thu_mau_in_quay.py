# -*- coding: utf-8 -*-
"""Mau in an tai quay: nhan vien chinh duoc noi dung ban in.

Anh Viet 26/08/2026: *"Anh thay em can lam them phan he Cau hinh mau in an
trong nut cai dat tren app, trong do co cau hinh mau in hoa don, cau hinh
mau in tem,... de nhan vien chinh duoc giong nhu ben ipos."*

HAI BAN MAC DINH, MOT SU THAT
-----------------------------
Gia tri mac dinh phai nam o hai noi: may chu (mau_in_quay.MAC_DINH) va app
(IN_MAU_MD trong 10-bill-quay.js). App can ban rieng vi no phai in duoc
ngay ca khi cau hinh chua ve, hoac ve thieu mot o moi them.

Hai ban do lech nhau la mot loi vo hinh: khong ai bao gi ca, chi la to bill
in ra o quay khac voi cai man Cai dat dang bay. Nen ca kiem duoi day doi
chieu TUNG O mot.
"""

import io
import os
import re

from vagabond import mau_in_quay
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _js(ten):
	goi = os.path.dirname(os.path.abspath(mau_in_quay.__file__))
	return io.open(
		os.path.join(goi, "public", "js", "bep", ten), encoding="utf-8").read()


def _py(ten):
	goi = os.path.dirname(os.path.abspath(mau_in_quay.__file__))
	return io.open(os.path.join(goi, ten), encoding="utf-8").read()


def _so(v):
	"""So viet ra JS: 11.5 giu nguyen, 14.0 thanh 14."""
	if isinstance(v, float) and v.is_integer():
		return str(int(v))
	return str(v)


@ca("mẫu in: ô thiếu, sai kiểu hay ngoài khoảng đều về mặc định của chính ô đó")
def _():
	md = mau_in_quay.MAC_DINH["hoa_don"]
	# Ban rong: moi o ve mac dinh.
	ra = mau_in_quay.chuan_mot("hoa_don", None)
	la("ô thiếu về mặc định", ra["co_chu"], md["co_chu"])
	la("dòng cảm ơn về mặc định", ra["chan_trang"], md["chan_trang"])
	# Sai kieu.
	ra = mau_in_quay.chuan_mot("hoa_don", {"co_chu": "to lên tí"})
	la("chữ không phải số thì về mặc định", ra["co_chu"], md["co_chu"])
	# Ngoai khoang: co chu hoa don chi cho 9 den 16.
	la("cỡ chữ 99 bị trả về mặc định",
		mau_in_quay.chuan_mot("hoa_don", {"co_chu": 99})["co_chu"], md["co_chu"])
	la("cỡ chữ 0 bị trả về mặc định",
		mau_in_quay.chuan_mot("hoa_don", {"co_chu": 0})["co_chu"], md["co_chu"])
	la("cỡ chữ 13 trong khoảng thì giữ",
		mau_in_quay.chuan_mot("hoa_don", {"co_chu": 13})["co_chu"], 13.0)
	# Mot o hong KHONG duoc keo do ca ban.
	ra = mau_in_quay.chuan_mot("hoa_don", {"co_chu": 999, "logo": 0})
	la("ô hỏng không kéo đổ ô lành", ra["logo"], 0)
	# O bat luon ra 1 hoac 0, khong bao gio ra chuoi.
	la("ô bật nhận chuỗi rỗng thành 0",
		mau_in_quay.chuan_mot("hoa_don", {"logo": ""})["logo"], 0)
	la("ô bật nhận chữ thành 1",
		mau_in_quay.chuan_mot("hoa_don", {"logo": "co"})["logo"], 1)


@ca("mẫu in: ô lạ do bản cũ để lại không chui được vào bản đã gõ")
def _():
	ra = mau_in_quay.chuan_mot("tem", {"co_chu": 9, "o_la_hoac_doc_hai": "<script>"})
	dung("ô lạ bị bỏ", "o_la_hoac_doc_hai" not in ra)
	la("số ô đúng bằng số ô đã khai", len(ra), len(mau_in_quay.O["tem"]))


@ca("mẫu in: dòng cảm ơn bị cắt đúng độ dài đã khai, không tràn ra giấy")
def _():
	dai = [o for o in mau_in_quay.O["hoa_don"] if o["k"] == "chan_trang"][0]["dai"]
	ra = mau_in_quay.chuan_mot("hoa_don", {"chan_trang": "a" * (dai + 50)})
	la("cắt đúng độ dài", len(ra["chan_trang"]), dai)
	la("cắt khoảng trắng hai đầu",
		mau_in_quay.chuan_mot("hoa_don", {"chan_trang": "  xin chào  "})["chan_trang"],
		"xin chào")


@ca("mẫu in: điểm bán chưa khai riêng thì theo bản dùng chung")
def _():
	het = mau_in_quay.chuan_het({
		"chung": {"hoa_don": {"co_chu": 12}},
		"diem": {"tcv": {"hoa_don": {"co_chu": 15}}},
	})
	dung("mã điểm được viết hoa", "TCV" in het["diem"])
	la("điểm có bản riêng thì lấy bản riêng",
		mau_in_quay.mau_cho(het, "TCV")["hoa_don"]["co_chu"], 15.0)
	la("chữ thường vẫn khớp đúng điểm",
		mau_in_quay.mau_cho(het, "tcv")["hoa_don"]["co_chu"], 15.0)
	la("điểm chưa khai riêng thì theo bản chung",
		mau_in_quay.mau_cho(het, "NVHTN")["hoa_don"]["co_chu"], 12.0)
	la("không nói điểm nào thì theo bản chung",
		mau_in_quay.mau_cho(het, "")["hoa_don"]["co_chu"], 12.0)


@ca("mẫu in: bản mặc định trên máy chủ và bản mặc định trong app khớp từng ô")
def _():
	src = _js("10-bill-quay.js")
	i = src.find("var IN_MAU_MD")
	dung("app có bản mặc định riêng", i > 0)
	khoi = src[i:src.find("\n};", i)]
	for vai, o in mau_in_quay.MAC_DINH.items():
		for k, v in o.items():
			if isinstance(v, str):
				mong = "'%s'" % v
			else:
				mong = _so(v)
			# Phai kem dau ket thuc, khong thi "co_chu: 11" khop nham vao
			# "co_chu: 11.5" va ca kiem nay tro thanh vo dung.
			co = re.search(r"\b%s\s*:\s*%s(?=[,}\s])" % (k, re.escape(mong)), khoi)
			dung("%s.%s trong app bằng %s" % (vai, k, mong), bool(co))


@ca("mẫu in: máy chủ gửi bản mẫu theo từng điểm bán, y như khổ giấy")
def _():
	src = _py("ban_hang.py")
	dung("có ô mẫu in chung", '"mau_in": mau_in_quay.theo_diem(),' in src)
	dung("có ô mẫu in theo điểm", '"mau_in_diem": {' in src)
	dung("mô đun được nhập", "mau_in_quay" in src.split("\n")[52] or "mau_in_quay," in src)


@ca("mẫu in: app đọc mẫu của đúng điểm bán đang đứng")
def _():
	src = _js("10-bill-quay.js")
	dung("có hàm inMau", "function inMau(vaiTro)" in src)
	dung("đọc bảng theo điểm trước", "(CFGBH || {}).mau_in_diem || {})[ma]" in src)
	dung("thiếu điểm thì về bảng chung", "(CFGBH || {}).mau_in || {}" in src)
	# Hoa don, phieu mon va tem deu phai goi inMau, khong con o nao go cung.
	for ham in ("posInBill", "posInPhieuMon", "posInTemLy"):
		j = src.find("function %s(" % ham)
		if j < 0:
			j = src.find("async function %s(" % ham)
		dung("%s có trong mã nguồn" % ham, j > 0)
		than = src[j:j + 6000]
		dung("%s dùng mẫu in" % ham, "inMau('" in than)


@ca("mẫu in: gộp dòng chỉ gộp khi mọi thứ giống nhau")
def _():
	src = _js("10-bill-quay.js")
	dung("có hàm gộp", "function posGopDongMon(mon)" in src)
	# Khoa gop phai gom du nam thanh phan. Thieu mot cai la gop nham hai ly
	# khac tuy chon lam mot, va quay bar lam sai.
	i = src.find("function posGopDongMon(mon)")
	than = src[i:i + 1200]
	for phan in ("m.ten", "m.rate", "m.combo", "m.tc", "m.gc"):
		dung("khoá gộp có %s" % phan, phan in than)
	dung("bỏ món 0 đồng trước rồi mới gộp",
		src.find("if (M.an_mon_0d)") < src.find("if (M.gop_mon)"))


@ca("mẫu in: mã đơn sàn giao hàng không bao giờ bị tắt theo ô dòng đầu tem")
def _():
	# Tat dong dau tem chi duoc bo dong ten tiem. Bo ca ma GrabFood la ban
	# dong goi giao nham tui, khong co cach nao biet.
	src = _js("10-bill-quay.js")
	i = src.find("var maApp = posMaAppCuaBill(d);")
	dung("có mã đơn sàn trên tem", i > 0)
	than = src[i:i + 3000]
	dung("mã sàn đi trước phép tắt",
		than.find("maApp\n        ? '<div class=\"app\">") > 0
		or "(maApp\n        ? '<div class=\"app\">" in than)
	dung("chỉ dòng tên tiệm mới bị tắt", "M.hien_dau ?" in than)


@ca("mẫu in: màn hình mới được nối vào Cài đặt và vào bộ định tuyến")
def _():
	src = _js("02-trang-chu.js")
	dung("có thẻ trong Cài đặt", "'CDMU')" in src)
	dung("có trong nhóm Cài đặt", "'CDMI', 'CDMU'" in src)
	dung("có đường dẫn ngắn", "'mau-in': 'CDMU'," in src)
	dung("bấm vào thì mở màn", "if (k === 'CDMU') return go(scrMauIn);" in src)
	man = _js("36-mau-in.js")
	dung("màn hình có hàm vào", "async function scrMauIn()" in man)
	dung("in thử dùng đúng đường in thật", "await posInTemLy(d)" in man)
	dung("in thử trả lại cấu hình cũ", "CFGBH.mau_in = giuChung;" in man)
