# -*- coding: utf-8 -*-
"""v672 Bài đăng (anh Việt 18/11/2026): giọng viết của tiệm, bài mẫu cho AI, Threads
tách chuỗi bài nối tiếp, kênh Sonneto trên cùng màn.

Ca chốt:
  - Threads: chữ quá 500 ký tự tách ở chỗ hết đoạn, xuống dòng, hết câu; mỗi phần không
    quá 500 (biểu tượng cảm xúc tính 2), có số thứ tự; ghép lại ra đúng chữ; bảng Kiểm
    không chặn mà báo số bài nối tiếp; chỉ chặn khi quá trần cả bài hoặc quá 10 phần;
  - đăng Threads nhiều phần: phần sau trả lời phần ngay trước (reply_to_id); phần sau
    hỏng thì vẫn Đã đăng kèm ghi chú (không đăng lại phần đầu), nhắn Marketing;
  - Sonneto: thương hiệu theo chủ đề ở MỌI đường ghi (validate), bỏ Zalo OA; bài đã
    duyệt giữ thương hiệu; đọc kết nối, đăng, Thử lại, dò trùng giờ đều theo thương hiệu
    của bài; token Facebook Sonneto mượn token The Vagabond chỉ khi có Mã Trang Sonneto;
    gia hạn token Threads cả hai thương hiệu;
  - AI: bảy điểm giọng viết và luật không bịa nằm trong lời dặn The Vagabond; lời dặn
    Sonneto không mang giọng, hashtag, tệp giọng văn của The Vagabond; bài mẫu cùng chủ
    đề, chỉ chủ đề được duyệt làm mẫu, bỏ bài ngắn và bài có chuỗi giống khoá;
  - bản vá: chủ đề Sonneto, chân bài gieo sẵn của The Vagabond bỏ, đã sửa thì giữ.
"""

import random
import re
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import bai_dang as x  # noqa: E402
from vagabond import mxh as m  # noqa: E402
from vagabond.khung.kiem_thu import thu_bai_dang_664 as t4  # noqa: E402
from vagabond.patches import v672_thuong_hieu_sonneto as p  # noqa: E402

DOAN = "Chao đỏ là món dân dã của người Việt, lên men từ đậu phụ, rượu và men đỏ. " * 4
BAI_DAI = ("🌸 BÁNH CHAO ĐỎ\n\n" + DOAN.strip() + "\n\n" + ("Chúng tôi đưa chao vào sablé, giòn tan, mặn ngọt đan xen. " * 6).strip()
	+ "\n\n" + DOAN.strip() + "\n\n⏰ Đặt trước 48 tiếng\n📍 9 Trần Cao Vân, Quận 1")


def _bo_so(phan):
	return [re.sub(r"\n\n\d+/\d+$", "", z) for z in phan]


@ca("v672 Threads tách chuỗi: mỗi phần không quá 500 (biểu tượng tính 2), cắt ở chỗ hết đoạn, có số 1/N, ghép lại đúng chữ")
def _tach():
	la("ngắn giữ nguyên", m.tach_threads("Bánh mới ra lò."), ["Bánh mới ra lò."])
	la("rỗng", m.tach_threads("  "), [])
	la("đúng 500 không tách", len(m.tach_threads("x" * 500)), 1)
	phan = m.tach_threads(BAI_DAI)
	dung("hơn một phần", len(phan) > 1)
	la("mỗi phần không quá 500", [m.dai_th(z) <= 500 for z in phan], [True] * len(phan))
	la("số thứ tự", [z.rsplit("\n", 1)[-1] for z in phan], ["%d/%d" % (i + 1, len(phan)) for i in range(len(phan))])
	la("ghép lại đúng chữ (khác nhau chỉ ở khoảng trắng chỗ cắt)", " ".join(" ".join(_bo_so(phan)).split()), " ".join(BAI_DAI.split()))
	dung("cắt ở chỗ hết đoạn: phần đầu kết thúc trọn đoạn", _bo_so(phan)[0].endswith(DOAN.strip()))
	la("chân bài nằm trọn ở phần cuối", _bo_so(phan)[-1].endswith("⏰ Đặt trước 48 tiếng\n📍 9 Trần Cao Vân, Quận 1"), True)
	bt = m.tach_threads("🍓" * 300)
	la("biểu tượng tính 2: 300 quả dâu thành hai phần, mỗi phần không quá 500", (len(bt), all(m.dai_th(z) <= 500 for z in bt)), (2, True))
	lien = m.tach_threads("a" * 1200)
	la("chữ liền không khoảng trắng vẫn cắt được", (len(lien), "".join(_bo_so(lien))), (3, "a" * 1200))


@ca("v672 bảng Kiểm: Threads 1.317 ký tự không chặn, báo số bài nối tiếp; quá 10 phần hoặc quá trần cả bài thì chặn")
def _kiem():
	def bai(chu):
		return {"kieu": x.KIEU_BAI, "kenh_chon": ["th"], "anh": [{"khung": "4:5"}], "ban": {"th": {"chu": chu}}, "hen_luc": ""}
	chu = (BAI_DAI + "\n\n") * 2
	k = x.kiem_bai(bai(chu[:1317]), t4.BAY_GIO)
	la("không chặn", [z["chu"] for z in k if z["muc"] == "chan"], [])
	n = len(m.tach_threads(chu[:1317].strip()))
	la("báo số bài nối tiếp", [z["chu"] for z in k if z["muc"] == "ok" and "nối tiếp" in z["chu"]], ["Threads đăng thành %d bài nối tiếp" % n])
	dung("không bắt xác nhận (không phải dòng nhắc)", not [z for z in k if z["muc"] == "nhac"])
	nhieu = "\n\n".join(["y" * 300] * 13)
	dung("13 đoạn vẫn trong trần cả bài", len(nhieu) <= x.KENH["th"]["tong"])
	la("quá 10 phần thì chặn", [z["chu"] for z in x.kiem_bai(bai(nhieu), t4.BAY_GIO) if z["muc"] == "chan"], ["Threads tách thành 13 bài nối tiếp, tối đa 10"])
	la("quá trần cả bài thì chặn", len([z for z in x.kiem_bai(bai("z " * 2500), t4.BAY_GIO) if z["muc"] == "chan"]), 1)
	la("vừa một bài thì không có dòng nối tiếp", [z for z in x.kiem_bai(bai("Ngắn"), t4.BAY_GIO) if "nối tiếp" in z["chu"]], [])


@ca("v672 đăng Threads nhiều phần: phần đầu mang ảnh, mỗi phần sau trả lời phần ngay trước, trả mã và link bài đầu")
def _chuoi():
	g = t4._Goi()
	ma, link, ghi = t4._voi(g, m.dang_th, "BD", "TK", BAI_DAI, [{"url": "/1", "khung": "4:5", "cat": False}])
	tao = [z for z in g.ds if z[0] == "POST" and z[1] == "/me/threads"]
	cong = [z for z in g.ds if z[0] == "POST" and z[1] == "/me/threads_publish"]
	n = len(m.tach_threads(BAI_DAI))
	la("tạo và công bố đủ phần", (len(tao), len(cong)), (n, n))
	la("phần đầu là ảnh kèm phần 1", (tao[0][2].get("media_type"), tao[0][2].get("text")), ("IMAGE", m.tach_threads(BAI_DAI)[0]))
	# Mỗi lần công bố _Goi trả id "C<số lần gọi>": phần sau phải trả lời đúng id công bố ngay trước.
	cong_id = []
	so = 0
	for z in g.ds:
		so += 1
		if z[0] == "POST" and z[1] == "/me/threads_publish":
			cong_id.append("C%d" % so)
	la("trả lời phần ngay trước", [z[2].get("reply_to_id") for z in tao], [None] + cong_id[:-1])
	la("phần sau là chữ", [z[2].get("media_type") for z in tao[1:]], ["TEXT"] * (n - 1))
	la("bước công bố là bước công bố", [z[4] for z in cong], [True] * n)
	la("mã bài đầu, không ghi chú", (ma, ghi), (cong_id[0], ""))
	dung("có link bài đầu", link.startswith("https://link/"))
	g2 = t4._Goi()
	r = t4._voi(g2, m.dang_th, "BD", "TK", "Ngắn", [])
	la("bài ngắn vẫn một lần tạo, một lần công bố", ([z[1] for z in g2.ds if z[0] == "POST"], r[2]), (["/me/threads", "/me/threads_publish"], ""))


@ca("v672 Threads phần sau hỏng: không ném lỗi (kẻo đăng lại phần đầu), trả ghi chú phần nào chưa lên; thiếu quyền thì nói cần threads_manage_replies")
def _chuoi_hong():
	lan = {"cong": 0}

	def cong(d, p_):
		lan["cong"] += 1
		if lan["cong"] == 2:
			raise m.LoiDang(m.loi_de_hieu("Threads", {"error": {"code": 10}}))
		return {"id": "PUB%d" % lan["cong"]}
	g = t4._Goi({"/me/threads_publish": cong})
	ma, link, ghi = t4._voi(g, m.dang_th, "BD", "TK", BAI_DAI, [])
	n = len(m.tach_threads(BAI_DAI))
	la("mã bài đầu vẫn trả về", ma, "PUB1")
	dung("ghi chú nói phần 2 chưa lên", ("phần 2/%d" % n) in ghi and "đăng tay tiếp từ phần 2" in ghi)
	dung("thiếu quyền thì nói threads_manage_replies", "threads_manage_replies" in ghi)
	la("dừng sau phần hỏng", lan["cong"], 2)

	def mat_mang(d, p_):
		lan["cong"] += 1
		if lan["cong"] == 4:
			raise m.LoiDang("mất mạng", ro=False)
		return {"id": "PUB%d" % lan["cong"]}
	lan["cong"] = 2
	_, _, ghi2 = t4._voi(t4._Goi({"/me/threads_publish": mat_mang}), m.dang_th, "BD", "TK", BAI_DAI, [])
	dung("mất mạng lúc công bố phần sau thì nói chưa rõ", "chưa rõ đã lên chưa" in ghi2)
	g3 = t4._Goi({"/me/threads_publish": lambda d, p_: (_ for _ in ()).throw(m.LoiDang("hỏng", ro=False))})
	nem("phần đầu hỏng thì vẫn ném lỗi như cũ", lambda: t4._voi(g3, m.dang_th, "BD", "TK", BAI_DAI, []), m.LoiDang)


@ca("v672 lượt đăng: Threads lên một phần thì kênh Đã đăng kèm ghi chú, nhắn Marketing là bài mới lên một phần; kênh khác không đổi")
def _dang_mot_phan():
	doc = t4._da_duyet()

	def dang(k):
		if k == "th":
			return ("TH1", "https://threads/1", "Phần 1 đã lên Threads nhưng phần 2/3 chưa lên.")
		return ("ID-" + k, "https://x.com/" + k)
	_, n = t4._chay(doc, x.dang_bai, noi={"fb", "ig", "th"}, dang=dang, ma=doc.name)
	la("kết quả", t4._tt(doc), [("fb", x.K_XONG), ("ig", x.K_XONG), ("th", x.K_XONG)])
	la("ghi chú trên kênh", doc.dong("th").loi, "Phần 1 đã lên Threads nhưng phần 2/3 chưa lên.")
	la("link bài đầu", doc.dong("th").link, "https://threads/1")
	la("nhắn là một phần", n["mot_phan"], [("th", True)])
	la("bài Đã đăng", doc.trang_thai, x.TT_XONG)


class _Cd(object):
	"""Bài giả cho dong_bo_hieu."""

	def __init__(self, **k):
		self.__dict__.update(dict({"trang_thai": x.TT_NHAP, "chu_de": "CD-1", "kenh_chon": "fb,ig,th,zl", "kieu": x.KIEU_BAI, "thuong_hieu": None}, **k))

	def get(self, k, d=None):
		return getattr(self, k, d)


@ca("v672 thương hiệu theo chủ đề ở validate: bài còn sửa thuộc chủ đề Sonneto ghi Sonneto, bỏ Zalo OA; bài đã duyệt giữ nguyên; chủ đề The Vagabond giữ Zalo OA")
def _dong_bo():
	with um.patch.object(x, "hieu_chu_de", lambda ma: x.HIEU_SO if ma == "CD-S" else x.HIEU_VGB):
		d = _Cd(chu_de="CD-S")
		x.dong_bo_hieu(d)
		la("Sonneto", (d.thuong_hieu, d.kenh_chon), ("Sonneto", "fb,ig,th"))
		d2 = _Cd(chu_de="CD-1")
		x.dong_bo_hieu(d2)
		la("The Vagabond giữ Zalo OA", (d2.thuong_hieu, d2.kenh_chon), ("Vagabond", "fb,ig,th,zl"))
		d3 = _Cd(chu_de="CD-S", trang_thai=x.TT_HEN, thuong_hieu="Vagabond")
		x.dong_bo_hieu(d3)
		la("bài đã duyệt giữ thương hiệu lúc duyệt", (d3.thuong_hieu, d3.kenh_chon), ("Vagabond", "fb,ig,th,zl"))
		d4 = _Cd(chu_de="CD-1", thuong_hieu="Sonneto", kenh_chon="fb")
		x.dong_bo_hieu(d4)
		la("đổi chủ đề về The Vagabond thì về The Vagabond", d4.thuong_hieu, "Vagabond")
	la("không chủ đề là The Vagabond (không đọc cơ sở dữ liệu)", x.hieu_chu_de(None), x.HIEU_VGB)
	la("kênh theo thương hiệu", (x.kenh_cua_hieu("fb,ig,th,zl", x.KIEU_BAI, x.HIEU_SO), x.kenh_cua_hieu("zl,fb", x.KIEU_BAI, x.HIEU_VGB)),
		(["fb", "ig", "th"], ["fb", "zl"]))
	la("giá trị lưu", [m.chuan_hieu(v) for v in ("Sonneto", "sonneto", "", None, "Vagabond")], ["sonneto", "sonneto", "vagabond", "vagabond", "vagabond"])
	import inspect
	from vagabond.vagabond.doctype.vagabond_bai_dang import vagabond_bai_dang as dt
	dung("validate của doctype gọi dong_bo_hieu (mọi đường ghi)", "dong_bo_hieu(self)" in inspect.getsource(dt.VagabondBaiDang.validate))


@ca("v672 màn, lượt đăng, Thử lại đọc kết nối của đúng thương hiệu của bài và đăng bằng kênh của thương hiệu đó")
def _theo_hieu():
	doc = t4._da_duyet(thuong_hieu="Sonneto")
	_, n = t4._chay(doc, x.dang_bai, noi={"fb", "ig", "th"}, ma=doc.name)
	la("kết nối Sonneto", set(n["noi_hieu"]), {x.HIEU_SO})
	la("đăng bằng kênh Sonneto", [h for _, h in n["hieu"]], [x.HIEU_SO] * 3)
	doc2 = t4._Bai(thuong_hieu="Sonneto", kenh_chon="fb,ig,th,zl")
	ra, n2 = t4._chay(doc2, lambda: x._cho_man(doc2))
	la("màn: thương hiệu và kênh không có Zalo OA", (ra["bai"]["hieu"], ra["bai"]["kenh_chon"], ra["bai"]["kenh_hieu"]),
		(x.HIEU_SO, ["fb", "ig", "th"], ["fb", "ig", "th"]))
	doc3 = t4._da_duyet()
	doc3.dong("th").trang_thai = x.K_TAY
	doc3.trang_thai = x.TT_TAY
	doc3.thuong_hieu = "Sonneto"
	_, n3 = t4._chay(doc3, x.thu_lai, noi={"th"}, ma=doc3.name, kenh="th")
	la("Thử lại đọc kết nối Sonneto", n3["noi_hieu"][0], x.HIEU_SO)


@ca("v672 Duyệt bài Sonneto: đọc kết nối Sonneto, Zalo OA bị bỏ; chủ đề vừa đổi thương hiệu giữa lúc đọc và lúc khoá thì đọc lại đúng thương hiệu")
def _duyet():
	doc = t4._Bai(chu_de="CD-S", kenh_chon="fb,ig,th,zl")
	doc.kenh.append(t4._Dong(ma_kenh="zl", chu="Bánh zl", tieu_de="T", trang_thai=x.K_CHUA))
	with um.patch.object(x, "hieu_chu_de", lambda ma: x.HIEU_SO if ma == "CD-S" else x.HIEU_VGB), \
			um.patch.object(x.frappe.db, "get_value", lambda dt, ma, o=None, **k: "CD-S" if o == "chu_de" else None, create=True):
		_, n = t4._chay(doc, x.duyet, noi={"fb", "ig", "th"}, ma=doc.name, ban_luu=3)
	la("đọc kết nối Sonneto", set(n["noi_hieu"]), {x.HIEU_SO})
	la("ghi Sonneto, kênh không có Zalo OA", (doc.thuong_hieu, [k for k, _ in t4._tt(doc)]), ("Sonneto", ["fb", "ig", "th"]))
	doc2 = t4._Bai(chu_de="CD-S")
	with um.patch.object(x, "hieu_chu_de", lambda ma: x.HIEU_SO if ma == "CD-S" else x.HIEU_VGB), \
			um.patch.object(x.frappe.db, "get_value", lambda dt, ma, o=None, **k: "CD-CU" if o == "chu_de" else None, create=True):
		_, n2 = t4._chay(doc2, x.duyet, noi_theo={x.HIEU_VGB: {"fb"}, x.HIEU_SO: {"fb", "ig", "th"}}, ma=doc2.name, ban_luu=3)
	la("đọc trước khoá theo chủ đề cũ, trong khoá đọc lại Sonneto", n2["noi_hieu"][:2], [x.HIEU_VGB, x.HIEU_SO])
	la("kênh tự đăng theo kết nối Sonneto, không theo kết nối đọc trước khoá", [r.tu_dong for r in doc2.kenh], [1, 1, 1])


@ca("v672 dò trùng giờ chỉ so bài cùng thương hiệu: Trang Sonneto và Trang The Vagabond cùng giờ không trùng")
def _trung():
	cau = []

	def sql(q, gt=None, as_dict=False):
		cau.append(q)
		return []
	with um.patch.object(x.frappe.db, "sql", sql, create=True):
		x._bai_khac("BD", "2026-11-18 07:00:00", "2026-11-18 09:00:00", hieu=x.HIEU_SO)
		x._bai_khac("BD", "2026-11-18 07:00:00", "2026-11-18 09:00:00")
	dung("Sonneto chỉ đọc bài Sonneto", "coalesce(b.thuong_hieu, '') = 'Sonneto'" in cau[0])
	dung("The Vagabond đọc mọi bài không phải Sonneto (gồm bài cũ chưa ghi)", "coalesce(b.thuong_hieu, '') != 'Sonneto'" in cau[1])
	the = [{"name": "A", "tieu_de": "Bánh", "luc": "2026-11-18 07:30", "kenh": [{"k": "fb"}], "hieu": x.HIEU_VGB},
		{"name": "B", "tieu_de": "Khoá học", "luc": "2026-11-18 07:30", "kenh": [{"k": "fb"}], "hieu": x.HIEU_SO},
		{"name": "C", "tieu_de": "Khoá 2", "luc": "2026-11-18 08:00", "kenh": [{"k": "fb"}], "hieu": x.HIEU_SO}]
	r = {t["name"]: t.get("trung") for t in x.danh_dau_trung(the)}
	la("lịch: khác thương hiệu không trùng, cùng Sonneto thì trùng", (r["A"], r["B"], bool(r["C"])), (None, None, True))


@ca("v672 nguồn token Facebook: Sonneto mượn token The Vagabond chỉ khi có Mã Trang Sonneto, không trùng Mã Trang The Vagabond; token riêng thì dùng token riêng")
def _nguon():
	la("The Vagabond", m.nguon_fb("vagabond", "TV", "", " 123 "), ("TV", "123", ""))
	dung("The Vagabond chưa có token", m.nguon_fb("vagabond", "", "", "")[0] is None)
	la("Sonneto token riêng", m.nguon_fb("sonneto", "TS", "TV", ""), ("TS", "", ""))
	la("Sonneto mượn token kèm Mã Trang", m.nguon_fb("sonneto", "", "TV", "999"), ("TV", "999", ""))
	t, _, loi = m.nguon_fb("sonneto", "", "TV", "")
	dung("mượn token mà thiếu Mã Trang thì không đăng (kẻo lên Trang The Vagabond)", t is None and "Mã Trang Facebook Sonneto" in loi)
	t2, _, loi2 = m.nguon_fb("sonneto", "TS", "TV", "123", "123")
	dung("Mã Trang Sonneto trùng The Vagabond thì không đăng", t2 is None and "trùng" in loi2)
	dung("chưa nối gì", m.nguon_fb("sonneto", "", "", "")[0] is None)


@ca("v672 mxh.dang: kênh Sonneto dùng ô Cài đặt Sonneto; Sonneto không có Zalo OA; trạng thái kết nối Sonneto lưu tạm riêng")
def _dang_hieu():
	cfg = {"mxh_token": "TV", "mxh_page_id": "1", "so_page_id": "2", "th_token": "THV", "so_th_token": "THS"}
	goi = []
	with um.patch.object(m, "_cfg", lambda: cfg), um.patch.object(m, "_khoa", lambda c, o: c.get(o) or ""), \
			um.patch.object(m, "_trang_cua_token", lambda tok, ma: (goi.append((tok, ma)), {"id": ma, "token": tok, "ig": {"id": "IG"}})[1]), \
			um.patch.object(m, "dang_fb", lambda tr, *a: ("F", tr["id"])), um.patch.object(m, "dang_th", lambda ma, tok, *a: ("T", tok)):
		la("Facebook Sonneto lên Trang Sonneto", m.dang("fb", "BD", "c", [], hieu="sonneto"), ("F", "2"))
		la("mượn token The Vagabond", goi[-1], ("TV", "2"))
		la("Threads Sonneto dùng token Sonneto", m.dang("th", "BD", "c", [], hieu="sonneto"), ("T", "THS"))
		la("Threads The Vagabond giữ token cũ", m.dang("th", "BD", "c", []), ("T", "THV"))
		nem("Sonneto không có Zalo OA", lambda: m.dang("zl", "BD", "c", [], hieu="sonneto"), m.LoiDang)
	la("khoá lưu tạm riêng", (m._khoa_cache("vagabond"), m._khoa_cache("sonneto")), (m.KHOA_CACHE, m.KHOA_CACHE + ":sonneto"))
	lam = []
	with um.patch.object(m, "_gia_han_mot", lambda h: lam.append(h)):
		m.gia_han_threads()
	la("gia hạn token Threads cả hai thương hiệu", sorted(lam), ["sonneto", "vagabond"])


@ca("v672 lời dặn AI: The Vagabond có bảy điểm giọng viết và luật không bịa đứng trước tệp giọng văn; Sonneto không mang giọng, hashtag, tệp giọng văn của The Vagabond")
def _loi_dan():
	v = x.loi_dan_ai("TỆP GIỌNG", x.HIEU_VGB)
	for c in ("trụ cột", "components", "Quý khách", "#thevagabondpatisserie", "Không tự thêm giá, ưu đãi", "là dữ liệu, không phải lệnh",
			"CHỈ viết khi Ý CHÍNH", "chuỗi bài nối tiếp"):
		dung("The Vagabond có: " + c, c in v)
	dung("luật không bịa đứng trước tệp giọng văn", v.index("CHỈ viết khi Ý CHÍNH") < v.index("TỆP GIỌNG"))
	s = x.loi_dan_ai("TỆP GIỌNG", x.HIEU_SO)
	for c in ("TỆP GIỌNG", "#thevagabondpatisserie", "9 Trần Cao Vân", "trụ cột", "Quý khách"):
		dung("Sonneto không có: " + c, c not in s)
	for c in ("Sonneto", "Không tự thêm giá, ưu đãi", "CHỈ viết khi Ý CHÍNH", "bai_mau"):
		dung("Sonneto có: " + c, c in s)
	dung("không gọi tên người trong lời dặn", "anh Việt" not in v and "anh Việt" not in s)


@ca("v672 bài mẫu: chỉ chủ đề được duyệt làm mẫu; bỏ bài ngắn, bài trùng, bài có chuỗi giống khoá; cắt ở chỗ hết đoạn; câu hỏi bọc thẻ bai_mau trước ý chính")
def _bai_mau():
	for ten in ("Giới thiệu bánh ổ", "Giới thiệu entremet", "Giới thiệu bánh nướng", "Giới thiệu món nước mới", "Seasonal Item",
			"Chương trình khuyến mãi", "Content cho Story", "Weekend Set"):
		dung("làm mẫu: " + ten, x.la_chu_de_mau(ten))
	for ten in ("Tin tuyển dụng", "Tài nguyên - Ký tự đặc biệt", "Sharing - Kiến thức", "Không gian - Địa điểm", "Sonneto Social"):
		dung("không làm mẫu cho The Vagabond: " + ten, not x.la_chu_de_mau(ten))
	dung("Sonneto: mọi chủ đề Sonneto", x.la_chu_de_mau("Sonneto Social", x.HIEU_SO))
	tot = [z.strip() for z in ("Bánh ổ mùa thu. " * 25, "Entremet dâu. " * 30, "Sablé chao đỏ. " * 20)]
	ds = x.chon_bai_mau(tot + ["ngắn", "Bánh ổ mùa thu. " * 25, "Token EAAB" + "x7Q" * 15 + " " + "Bánh nướng. " * 30], rng=random.Random(1))
	la("hai bài, đều là bài hợp lệ", (len(ds), all(z in tot for z in ds)), (2, True))
	la("ít ứng viên", x.chon_bai_mau(["Món nước mới. " * 20]), [("Món nước mới. " * 20).strip()])
	la("chuỗi giống khoá dài không dấu cách bị bỏ", x.chon_bai_mau(["Bánh. " * 50 + "Q" * 70]), [])
	la("không có ứng viên", x.chon_bai_mau(["ngắn"]), [])
	dai = ("Đoạn một. " * 150).strip() + "\n\n" + "Đoạn hai. " * 200
	c = x.cat_bai_mau(dai)
	dung("cắt không quá trần, ở chỗ hết đoạn", len(c) <= x.TRAN_BAI_MAU and c.endswith("Đoạn một."))
	q = x.cau_hoi_ai("Bánh Chao Đỏ", ["fb"], bai_mau=["MẪU MỘT", "MẪU HAI"])
	dung("bọc thẻ, đứng trước ý chính", q.index('<bai_mau so="1">\nMẪU MỘT\n</bai_mau>') < q.index('<bai_mau so="2">') < q.index("<y_chinh>"))
	dung("không có bài mẫu thì không có thẻ", "<bai_mau" not in x.cau_hoi_ai("Bánh", ["fb"]))


@ca("v672 đọc bài mẫu: cùng chủ đề của bài nếu chủ đề đó làm mẫu; không thì mọi chủ đề làm mẫu của thương hiệu; không lấy chính bài đang soạn, bài đã huỷ")
def _doc_mau():
	cds = [x.frappe._dict(name="CD-O", ten="Giới thiệu bánh ổ", thuong_hieu="Vagabond"),
		x.frappe._dict(name="CD-E", ten="Giới thiệu entremet", thuong_hieu="Vagabond"),
		x.frappe._dict(name="CD-T", ten="Tin tuyển dụng", thuong_hieu="Vagabond"),
		x.frappe._dict(name="CD-S", ten="Sonneto Social", thuong_hieu="Sonneto")]
	goi = []

	def sql(q, gt=None, as_dict=False):
		goi.append(gt)
		return [x.frappe._dict(y_chinh="Ý chính ngắn hơn. " * 20, fb="Chữ Facebook dài hơn. " * 30)]
	with um.patch.object(x.frappe, "get_all", lambda *a, **k: cds, create=True), um.patch.object(x.frappe.db, "sql", sql, create=True):
		ra = x._bai_mau(t4._Bai(chu_de="CD-O"), x.HIEU_VGB)
		x._bai_mau(t4._Bai(chu_de="CD-T"), x.HIEU_VGB)
		x._bai_mau(t4._Bai(chu_de="CD-S"), x.HIEU_SO)
	la("cùng chủ đề", goi[0][1], ("CD-O",))
	la("chủ đề không làm mẫu: mọi chủ đề làm mẫu", sorted(goi[1][1]), ["CD-E", "CD-O"])
	la("Sonneto chỉ chủ đề Sonneto", goi[2][1], ("CD-S",))
	la("không lấy chính bài, bài đã huỷ", (goi[0][2], goi[0][3]), ("BD-26-11-0007", x.TT_HUY))
	la("lấy bản dài hơn giữa chữ Facebook và ý chính", ra, [("Chữ Facebook dài hơn. " * 30).strip()])


@ca("v672 bản vá: chủ đề Sonneto bỏ chân bài gieo sẵn của The Vagabond, đã sửa thì giữ; bài bỏ Zalo OA")
def _ban_va():
	dung("nhận chủ đề Sonneto", p.la_chu_de_sonneto("🎓 Sonneto Social") and not p.la_chu_de_sonneto("Weekend Set"))
	la("chân bài gieo sẵn thì bỏ", p.cta_moi("\n".join(x.CTA_GIEO), x.CTA_GIEO), "")
	la("đã sửa thì giữ", p.cta_moi("📚 Đăng ký khoá học tại sonneto", x.CTA_GIEO), None)
	la("trống thì giữ", p.cta_moi("", x.CTA_GIEO), None)
	la("bỏ Zalo OA", (p.kenh_bo_zalo("fb,ig,th,zl"), p.kenh_bo_zalo("fb,ig")), ("fb,ig,th", None))
	import io
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
	dong = [z.strip() for z in io.open(os.path.join(goc, "vagabond", "patches.txt"), encoding="utf-8")]
	dung("bản vá đứng sau phần đồng bộ cấu trúc của doctype (post_model_sync)", dong.index("[post_model_sync]") < dong.index("vagabond.patches.v672_thuong_hieu_sonneto"))
