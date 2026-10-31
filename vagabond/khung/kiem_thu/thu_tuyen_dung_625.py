# -*- coding: utf-8 -*-
"""v625: tuyển dụng đợt 2 (anh Việt 31/10/2026).

Anh chốt và ca nào giữ điều đó:
  1. Form ứng tuyển dùng đúng 14 câu form Lark, giữ câu "Tổng thu nhập mà bạn
     cảm thấy xứng đáng với năng lực?"; câu giới tính, sinh nhật bắt buộc như
     Lark (_mac_dinh_lark).
  2. Minh Vũ thêm bớt câu trong trình biên tập; câu họ tên, số điện thoại, vị
     trí không xoá được; ô gõ tay là đầu vào không tin được (_chuan_form,
     _luu_form). Phần bấm thật ở hanh_vi/bien_tap_cau_hoi_625.js.
  3. AI đọc CV: không bao giờ thấy giới tính, sinh nhật, số điện thoại, email
     (_ai_khong_thay); điểm do MÁY tính và kẹp, CV không đổi được luật chấm
     (_ai_ket_qua); lỗi nào cũng ghi lý do lên hồ sơ (_ai_viec_nen).
  4. Câu đồng ý nói rõ CV đi qua dịch vụ AI (_dong_y_ai).
  5. Web: lương gọn, mục mô tả, ảnh theo bộ phận cho thẻ phương án A (_the_web).

Các ca chạy hàm THẬT trên site giả của thu_tuyen_dung_622 (không gọi thêm hàm
nội bộ nào ngoài chuỗi máy chạy, điều 15).
"""

import copy
import datetime as dt
import json
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, la, nem
from vagabond.khung.kiem_thu.thu_tuyen_dung_622 import _Site, _chay, _doc_tep, _loi, _vt, _fr, td
from vagabond import tuyen_dung_form as tf  # noqa: E402
from vagabond import tuyen_dung_ai as ai  # noqa: E402
from vagabond import noi_dung_web as nw  # noqa: E402

HN = dt.date(2026, 10, 31)

# Hai vị trí thật trên site ngày 31/10/2026 (tin tuyển dụng công khai).
VTT2 = _vt(name="VTT-0002", tieu_de="Nhân Viên Bán Hàng Online Qua Fanpage (Sales Online)", ten_bo_phan="Sales",
	bo_phan="Sales - TV", noi_lam="Xưởng sản xuất Tân Bình", hinh_thuc="Toàn thời gian", ket_thuc="2026-11-30",
	noi_dung="- Tư vấn, trả lời khách hàng đặt bánh qua 5 trang online (Facebook, Instagram, Zalo, Website, Tiktok)\n"
	"- Thu tiền đơn hàng qua chuyển khoản, cà thẻ,...\n- Ghi nhận doanh thu cuối ngày và báo cáo\n"
	"Thời gian làm việc\n- Thứ 2 - Chủ nhật (từ 07:00 đến 22:30)\n- Ca sáng: 7h - 15h30",
	yeu_cau="Ưu tiên ứng viên có kinh nghiệm trực fanpage, bán hàng online ngành F&B.\n"
	"Ứng viên thành thạo tin học, gõ máy tính nhanh\nCó phụ cấp ăn trưa (30,000/ngày).\n"
	"Tham gia đầy đủ BHXH, BHYT, BHTN khi ký hợp đồng.\nThưởng KPI hàng tháng.",
	muc_luong="Lương cơ bản được thoả thuận từ 7.500.000/tháng trở lên (thử việc 2 tháng, nhận 85% lương).")
VTT1 = _vt(name="VTT-0001", tieu_de="Nhân viên bếp bánh ngọt (Pastry)", ten_bo_phan="Bếp Pastry", bo_phan="Bếp Pastry - TV",
	noi_lam="Xưởng sản xuất Tân Bình", hinh_thuc="Toàn thời gian", ket_thuc="2026-11-30", noi_dung="- Cân đong nguyên liệu.",
	yeu_cau="Khéo tay.", muc_luong="Lương part-time: từ 32.000/h (thử việc 1 tháng, nhận 85% lương) "
	"Lương full-time: từ 7.000.0000/tháng (thử việc 2 tháng, nhận 85% lương)")


def _tl(**k):
	"""Đủ 14 câu mặc định như ứng viên điền (mã câu -> giá trị máy khách gửi)."""
	t = {"ho_ten": "Trần Thị Bình", "gioi_tinh": "Nữ (Female)", "sinh_nhat": "2001-05-17", "sdt": "0909 123 456",
		"email": "binh@gmail.com", "tham_nien": "Từ 1 - 2 năm", "thoi_gian": "Full-time", "hoc_van": "Tốt nghiệp THPT",
		"luong": "9000000", "biet_tin": "Mạng xã hội", "nguoi_gioi_thieu": "", "nhan_them": "Em thích làm bánh."}
	t.update(k)
	return t


# ------------------------------------------------------------ form câu hỏi

@ca("v625 form mặc định: đúng 14 câu Lark theo thứ tự, câu bắt buộc như Lark, giữ câu thu nhập xứng đáng")
def _mac_dinh_lark():
	f = tf.mac_dinh()
	la("14 câu đúng thứ tự", [c["ma"] for c in f["cau_hoi"]], ["ho_ten", "gioi_tinh", "sinh_nhat", "sdt", "email", "vi_tri",
		"tham_nien", "thoi_gian", "hoc_van", "cv", "luong", "biet_tin", "nguoi_gioi_thieu", "nhan_them"])
	la("câu bắt buộc như Lark", [c["ma"] for c in f["cau_hoi"] if c["bat_buoc"]],
		["ho_ten", "gioi_tinh", "sinh_nhat", "sdt", "email", "vi_tri", "hoc_van", "luong", "biet_tin"])
	la("câu anh dặn giữ nguyên chữ", [c["hoi"] for c in f["cau_hoi"] if c["ma"] == "luong"],
		["Tổng thu nhập mà bạn cảm thấy xứng đáng với năng lực?"])
	la("ba bước", sorted({c["buoc"] for c in f["cau_hoi"]}), [1, 2, 3])
	la("giới tính, sinh nhật, liên lạc không cho AI", [c["ma"] for c in f["cau_hoi"] if not c["ai"]],
		["ho_ten", "gioi_tinh", "sinh_nhat", "sdt", "email", "biet_tin", "nguoi_gioi_thieu"])
	la("bản mặc định qua được chuẩn hoá y nguyên", tf.chuan_form(f), f)
	la("cấu hình hỏng thì trang vẫn có 14 câu", len(tf.form_hien({"tuyen_dung_form": {"cau_hoi": "hỏng"}})["cau_hoi"]), 14)
	la("chưa lưu gì thì dùng mặc định", tf.form_hien({}), f)


@ca("v625 Minh Vũ sửa câu hỏi: câu gốc không xoá được và luôn bắt buộc; ô gõ tay chịu mọi cách điền; chặn cấu hình hỏng")
def _chuan_form():
	f = tf.mac_dinh()
	bo_sdt = copy.deepcopy(f)
	bo_sdt["cau_hoi"] = [c for c in bo_sdt["cau_hoi"] if c["ma"] != "sdt"]
	dung("xoá số điện thoại: báo đúng câu", "Số điện thoại" in _loi(lambda: tf.chuan_form(bo_sdt)))
	g = copy.deepcopy(f)
	for c in g["cau_hoi"]:
		if c["ma"] in ("ho_ten", "sdt"):
			c["bat_buoc"] = False
			c["vi_tri"] = ["VTT-0001"]
		if c["ma"] in ("gioi_tinh", "sinh_nhat"):
			c["ai"] = True
		if c["ma"] == "email":
			c["loai"] = "chon_mot"
		if c["ma"] == "tham_nien":
			c["hoi"] = "  Thâm   niên\tcho vị trí?  "
			c["buoc"] = "9"
			c["vi_tri"] = ["VTT-0001", "<script>", "VTT-0001"]
	r = {c["ma"]: c for c in tf.chuan_form(g)["cau_hoi"]}
	la("câu gốc vẫn bắt buộc, hỏi mọi vị trí", [(r[m]["bat_buoc"], r[m]["vi_tri"]) for m in ("ho_ten", "sdt")], [(True, [])] * 2)
	la("giới tính, sinh nhật không bật AI được", [r["gioi_tinh"]["ai"], r["sinh_nhat"]["ai"]], [False, False])
	la("câu hệ thống giữ loại theo mã", r["email"]["loai"], "email")
	la("chữ thừa khoảng trắng gọn lại", r["tham_nien"]["hoi"], "Thâm niên cho vị trí?")
	la("bước lạ về bước 1", r["tham_nien"]["buoc"], 1)
	la("mã vị trí lạ bị bỏ, trùng gộp", r["tham_nien"]["vi_tri"], ["VTT-0001"])

	def them(**c):
		h = copy.deepcopy(f)
		h["cau_hoi"].append(dict({"ma": "c_ab12cd", "hoi": "Bạn đi làm từ ngày nào?", "loai": "chu", "bat_buoc": False, "buoc": 3}, **c))
		return h
	la("câu tự thêm hợp lệ", tf.chuan_form(them())["cau_hoi"][-1]["ma"], "c_ab12cd")
	dung("mã lạ", "mã không hợp lệ" in _loi(lambda: tf.chuan_form(them(ma="x;drop"))))
	dung("mã có sẵn của hệ thống bị nhại", "mã không hợp lệ" in _loi(lambda: tf.chuan_form(them(ma="luong_moi"))))
	dung("câu tự thêm không chọn được loại Tệp", "chọn loại" in _loi(lambda: tf.chuan_form(them(loai="tep"))))
	dung("câu chọn cần 2 lựa chọn", "ít nhất 2" in _loi(lambda: tf.chuan_form(them(loai="chon_mot", lua_chon=["Có", " Có "]))))
	dung("câu không chữ", "chưa có chữ" in _loi(lambda: tf.chuan_form(them(hoi="  "))))
	trung = them(ma="tham_nien")
	dung("trùng câu", "trùng" in _loi(lambda: tf.chuan_form(trung)))
	nhieu = copy.deepcopy(f)
	nhieu["cau_hoi"] += [{"ma": "c_%06d" % i, "hoi": "Câu %d nè" % i, "loai": "chu", "buoc": 3} for i in range(17)]
	dung("quá 30 câu", "tối đa 30" in _loi(lambda: tf.chuan_form(nhieu)))
	dung("chuỗi JSON hỏng", "Tải lại" in _loi(lambda: tf.chuan_form("{hỏng")))
	pl = tf.chuan_form(dict(f, phuc_loi=[" Giảm 20% ", "Giảm 20%", "", "BHXH"]))["phuc_loi"]
	la("phúc lợi gọn, bỏ trùng, bỏ dòng trống", pl, ["Giảm 20%", "BHXH"])


@ca("v625 lưu câu hỏi qua trình biên tập: ghi cả công khai lẫn nháp, người khác vừa sửa thì báo, khách không thấy cấu hình thô")
def _luu_form():
	nd = nw.chuan_hoa(copy.deepcopy(nw.MAC_DINH))
	f = tf.mac_dinh()
	f["cau_hoi"][-1]["hoi"] = "Bạn muốn nhắn gì thêm?"
	moi = nw.ap_form_tuyen_dung(nd, f, nw.dau_van_tay(tf.form_hien(nd)))
	la("đã lưu đúng câu", tf.form_hien(moi)["cau_hoi"][-1]["hoi"], "Bạn muốn nhắn gì thêm?")
	la("chuẩn hoá nội dung web giữ cấu hình", nw.chuan_hoa(moi)["tuyen_dung_form"]["cau_hoi"][-1]["hoi"], "Bạn muốn nhắn gì thêm?")
	nem("dấu cũ khác bản đang có: báo có người vừa sửa", lambda: nw.ap_form_tuyen_dung(moi, f, "dau-cu"), nw.XungDot)
	hong = copy.deepcopy(f)
	hong["cau_hoi"] = hong["cau_hoi"][1:]
	dung("cấu hình hỏng: câu báo nói việc", "Họ tên" in _loi(lambda: nw.ap_form_tuyen_dung(moi, hong, None)))
	dung("chuẩn hoá nội dung không nhận cấu hình hỏng", "Họ tên" in _loi(lambda: nw.chuan_hoa(dict(moi, tuyen_dung_form=hong))))
	f2 = tf.mac_dinh()
	f2["cau_hoi"][-1]["hoi"] = "Câu từ bản cũ"
	cu_trong_lich_su = dict(moi, tuyen_dung_form=tf.chuan_form(f2))
	la("Nâng cao lưu bản cũ: giữ câu hỏi đang dùng", nw.giu_form_da_luu(cu_trong_lich_su, moi)["tuyen_dung_form"]["cau_hoi"][-1]["hoi"], "Bạn muốn nhắn gì thêm?")
	la("Nâng cao gửi bản thiếu khoá: vẫn giữ", nw.giu_form_da_luu({"khoi": []}, moi)["tuyen_dung_form"]["cau_hoi"][-1]["hoi"], "Bạn muốn nhắn gì thêm?")
	dung("chưa từng lưu: không tự thêm", "tuyen_dung_form" not in nw.giu_form_da_luu(cu_trong_lich_su, nd))
	m = _doc_tep("noi_dung_web.py")
	dung("lưu cả bản gọi phép giữ câu hỏi", "nd = giu_form_da_luu(nd, json.loads(d.ban_nhap" in m)
	dung("bản công khai bỏ cấu hình thô, chỉ đưa phúc lợi chung", 'ra.pop("tuyen_dung_form", None)' in m and '"tuyen_dung_chung"' in m)
	dung("lưu câu hỏi chặn quyền như các hàm lưu khác", "def luu_form_tuyen_dung(gia_tri, dau_cu=\"\"):\n\t\"\"\"v625" in m.replace("    ", "\t")
		or "kiem_quyen()" in m[m.index("def luu_form_tuyen_dung"):m.index("def luu_form_tuyen_dung") + 400])


# ------------------------------------------------------------ trả lời

@ca("v625 trả lời form: đủ câu thì đổ đúng ô hồ sơ; thiếu câu bắt buộc thì nói đúng câu; Khác tự ghi; ngày, tiền, email chặn sai")
def _tra_loi():
	f = tf.mac_dinh()
	cot, dong = tf.chuan_tra_loi(f, "VTT-0002", _tl(), HN, td.chuan_sdt, False)
	la("ô hồ sơ", {k: cot[k] for k in ("ho_ten", "sdt", "email", "sinh_nhat", "luong_mong_muon", "gioi_thieu")},
		{"ho_ten": "Trần Thị Bình", "sdt": td.chuan_sdt("0909 123 456"), "email": "binh@gmail.com", "sinh_nhat": "2001-05-17",
			"luong_mong_muon": 9000000, "gioi_thieu": "Em thích làm bánh."})
	la("dòng trả lời hiện kiểu người đọc", [d["tra_loi"] for d in dong if d["ma"] in ("sinh_nhat", "luong")], ["17/05/2001", "9.000.000 đ/tháng"])
	dung("câu bỏ trống không thành dòng", "nguoi_gioi_thieu" not in [d["ma"] for d in dong])
	dung("thiếu giới tính: nói đúng câu", "Bạn tự định nghĩa giới" in _loi(lambda: tf.chuan_tra_loi(f, "VTT-0002", _tl(gioi_tinh=""), HN, td.chuan_sdt)))
	la("Khác tự ghi", [d["tra_loi"] for d in tf.chuan_tra_loi(f, "VTT-0002", _tl(gioi_tinh="Genderfluid"), HN, td.chuan_sdt)[1]
		if d["ma"] == "gioi_tinh"], ["Genderfluid"])
	dung("lựa chọn lạ ở câu không cho Khác", "chọn một lựa chọn" in _loi(lambda: tf.chuan_tra_loi(f, "VTT-0002", _tl(hoc_van="Tiến sĩ vũ trụ"), HN, td.chuan_sdt)))
	dung("sinh nhật tương lai", "ngày, tháng, năm" in _loi(lambda: tf.chuan_tra_loi(f, "VTT-0002", _tl(sinh_nhat="2030-01-01"), HN, td.chuan_sdt)))
	dung("sinh nhật dở dang", "ngày, tháng, năm" in _loi(lambda: tf.chuan_tra_loi(f, "VTT-0002", _tl(sinh_nhat="thieu"), HN, td.chuan_sdt)))
	dung("email sai", "email" in _loi(lambda: tf.chuan_tra_loi(f, "VTT-0002", _tl(email="binh@"), HN, td.chuan_sdt)))
	dung("lương chữ", "số tiền" in _loi(lambda: tf.chuan_tra_loi(f, "VTT-0002", _tl(luong="thoả thuận"), HN, td.chuan_sdt)))
	la("lương gõ 9tr", tf.chuan_tra_loi(f, "VTT-0002", _tl(luong="9tr"), HN, td.chuan_sdt)[0]["luong_mong_muon"], 9000000)
	g = copy.deepcopy(f)
	g["cau_hoi"].append({"ma": "c_banh01", "hoi": "Bạn đã làm entremet chưa?", "loai": "chon_mot", "lua_chon": ["Rồi", "Chưa"],
		"bat_buoc": True, "buoc": 3, "vi_tri": ["VTT-0001"], "ai": True})
	g = tf.chuan_form(g)
	la("câu riêng của vị trí bếp không hỏi ứng viên sales", [d["ma"] for d in tf.chuan_tra_loi(g, "VTT-0002", _tl(c_banh01="Rồi"), HN, td.chuan_sdt)[1]
		if d["ma"] == "c_banh01"], [])
	dung("vị trí bếp thì câu đó bắt buộc", "entremet" in _loi(lambda: tf.chuan_tra_loi(g, "VTT-0001", _tl(), HN, td.chuan_sdt)))
	cv = copy.deepcopy(f)
	[c for c in cv["cau_hoi"] if c["ma"] == "cv"][0]["bat_buoc"] = True
	dung("CV bắt buộc mà không tải", "Tải CV" in _loi(lambda: tf.chuan_tra_loi(cv, "VTT-0002", _tl(), HN, td.chuan_sdt, False)))
	dung("không phải từ điển", "Không đọc được" in _loi(lambda: tf.chuan_tra_loi(f, "VTT-0002", "x", HN, td.chuan_sdt)))


@ca("v625 tiền và lương gọn: chịu mọi cách gõ; dòng lương thật trên phiếu Vị trí ra đúng chữ gọn")
def _tien():
	for vao, ra in (("9.000.000", 9000000), ("9tr", 9000000), ("9,5 triệu", 9500000), ("12 - 15 triệu", 12000000),
			("35k", 35000), ("9 000 000 đ", 9000000), ("", None), ("thoả thuận", None)):
		la("đọc " + repr(vao), tf.doc_tien(vao), ra)
	la("lương sales thật", tf.luong_gon(VTT2["muc_luong"]), "Từ 7,5 triệu/tháng")
	la("lương bếp thật, có số gõ dư một chữ 0", tf.luong_gon(VTT1["muc_luong"]), "Từ 7 triệu · 32.000đ/giờ")
	la("khung tháng", tf.luong_gon("7 - 9 triệu/tháng"), "7 - 9 triệu/tháng")
	la("khung giờ", tf.luong_gon("25.000 - 39.000đ/giờ"), "25.000 - 39.000đ/giờ")
	la("để trống", tf.luong_gon(""), "")


@ca("v625 mô tả công việc chia mục: tên mục quen thuộc mở mục mới, dòng việc ngắn không dấu chấm KHÔNG thành tên mục")
def _chia_muc():
	m = tf.chia_noi_dung(VTT2["noi_dung"])
	la("hai mục", [x["tieu_de"] for x in m], ["Bạn sẽ làm", "Thời gian làm việc"])
	la("dòng việc ngắn vẫn là việc (lỗi bắt khi đo dữ liệu thật 31/10)", m[0]["dong"][1], "Thu tiền đơn hàng qua chuyển khoản, cà thẻ,...")
	m = tf.chia_noi_dung("Tư vấn khách\nThu tiền chuyển khoản\nYÊU CẦU KHÁC\n- Siêng năng\nGhi chú:\nLàm từ thứ 2")
	la("viết hoa và dấu hai chấm là tên mục", [(x["tieu_de"], x["dong"]) for x in m],
		[("Bạn sẽ làm", ["Tư vấn khách", "Thu tiền chuyển khoản"]), ("Yêu cầu khác", ["Siêng năng"]), ("Ghi chú", ["Làm từ thứ 2"])])
	la("mô tả trống", tf.chia_noi_dung(""), [])


@ca("v625 thẻ web phương án A: lương gọn, Tuyển gấp, ảnh theo bộ phận, quyền lợi tách khỏi yêu cầu")
def _the_web():
	t = td.the_web(dict(VTT2, tuyen_gap=1), "2026-10-31")
	la("lương", (t["luong_gon"], t["luong"]), ("Từ 7,5 triệu/tháng", VTT2["muc_luong"]))
	la("tuyển gấp", t["tuyen_gap"], 1)
	la("ảnh theo bộ phận Sales", t["anh_the"], tf.ANH_QUAY)
	la("ảnh bếp", td.the_web(VTT1, "2026-10-31")["anh_the"], tf.ANH_BEP)
	la("quyền lợi", t["quyen_loi"], ["Có phụ cấp ăn trưa (30,000/ngày).", "Tham gia đầy đủ BHXH, BHYT, BHTN khi ký hợp đồng.", "Thưởng KPI hàng tháng."])
	la("chúng tôi cần", len(t["can"]), 2)
	la("mục mô tả", [m["tieu_de"] for m in t["muc"]], ["Bạn sẽ làm", "Thời gian làm việc"])
	la("ảnh chọn trên app", td.the_web(dict(VTT2, anh_web=tf.ANH_BEP), "2026-10-31")["anh_the"], tf.ANH_BEP)
	la("ảnh riêng tư không lên web", td.the_web(dict(VTT2, anh_web="/private/files/cv-1.jpg"), "2026-10-31")["anh_the"], tf.ANH_QUAY)
	dung("ảnh đi ngược thư mục bị chặn", not td.anh_web_hop_le("/files/../private/files/x.jpg"))
	dung("ô Ảnh trên web gõ bậy: báo", "Ảnh trên web" in _loi(lambda: td.chuan_vi_tri(dict(VTT2, anh_web="javascript:alert(1)"))))
	la("ảnh mặc định có thật trong app", [u for u, _, _ in tf.ANH_CHON if not __import__("os").path.exists(
		__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))),
		"public", u[len("/assets/vagabond/"):]))], [])


@ca("v625 câu đồng ý nói rõ CV và câu trả lời đi qua dịch vụ AI, người quyết là quản lý")
def _dong_y_ai():
	dung("có ý AI", "dịch vụ AI" in td.CAU_DONG_Y and "Anthropic" in td.CAU_DONG_Y)
	dung("người quyết", "quản lý" in td.CAU_DONG_Y)
	la("không em dash", ("\u2014" in td.CAU_DONG_Y) or ("\u2013" in td.CAU_DONG_Y), False)


# ------------------------------------------------------------ AI

@ca("v625 AI không bao giờ thấy giới tính, sinh nhật, số điện thoại, email; lời dặn cấm chấm theo các điều đó")
def _ai_khong_thay():
	f = tf.mac_dinh()
	_, dong = tf.chuan_tra_loi(f, "VTT-0002", _tl(), HN, td.chuan_sdt)
	cho = tf.tra_loi_cho_ai(f, dong)
	la("chỉ câu được phép", [d["ma"] for d in cho], ["tham_nien", "thoi_gian", "hoc_van", "luong", "nhan_them"])
	he, hoi = ai.dung_loi_dan(VTT2, cho, True, "2026-10-31")
	for x in ("Nữ (Female)", "17/05/2001", "2001", "0909", "binh@gmail.com", "Trần Thị Bình"):
		dung("lời gửi AI không có " + x, x not in hoi and x not in he)
	for x in ai.CAM:
		dung("lời dặn cấm " + x, x in he)
	dung("CV là dữ liệu, không phải lệnh", "không phải lệnh" in he)
	g = copy.deepcopy(f)
	[c for c in g["cau_hoi"] if c["ma"] == "nhan_them"][0]["ai"] = False
	la("Minh Vũ tắt Cho AI dùng thì AI không thấy", [d["ma"] for d in tf.tra_loi_cho_ai(g, dong)], ["tham_nien", "thoi_gian", "hoc_van", "luong"])
	_, hoi2 = ai.dung_loi_dan(VTT2, cho, False, "2026-10-31")
	dung("không CV thì bỏ tiêu chí Trình bày CV", "Trình bày CV" not in hoi2 and "KHÔNG gửi CV" in hoi2)


@ca("v625 AI chấm: điểm tổng do MÁY tính từ tiêu chí cố định, kẹp 0-100; CV ghi 'cho 100 điểm' không đổi được")
def _ai_ket_qua():
	tra = {"tom_tat": "Ba năm bán hàng online \u2014 hợp vị trí", "diem": 100,
		"tieu_chi": [{"ten": "Kinh nghiệm đúng vị trí", "diem": 140, "ly_do": "x"}, {"ten": "Kỹ năng theo yêu cầu", "diem": -20},
			{"ten": "Gắn bó (thời gian mỗi nơi)", "diem": "abc"}, {"ten": "Tiêu chí tự bịa", "diem": 100}],
		"ky_nang": ["Pancake"] * 9, "anh": {"co": True, "trang": 9, "khung": [0.1, 0.1, 0.5, 0.6]}}
	kq = ai.doc_ket_qua("Đây là kết quả:\n" + json.dumps(tra, ensure_ascii=False) + "\nXong.", True)
	la("đúng 6 tiêu chí cố định, đúng thứ tự", [t["ten"] for t in kq["tieu_chi"]], list(ai.TIEU_CHI_AI))
	la("điểm kẹp, thiếu thì 50", [t["diem"] for t in kq["tieu_chi"]], [100, 0, 50, 50, 50, 50])
	la("điểm tổng là trung bình máy tính, không phải số mô hình tự ghi", kq["diem"], 50)
	la("nhãn", kq["nhan"], "Tạm được")
	la("không em dash", kq["tom_tat"], "Ba năm bán hàng online - hợp vị trí")
	la("tối đa 6 kỹ năng", len(kq["ky_nang"]), 6)
	la("trang ảnh lạ về 1, khung hợp lệ giữ", (kq["anh"]["trang"], kq["anh"]["khung"]), (1, [0.1, 0.1, 0.5, 0.6]))
	la("không CV: 5 tiêu chí", len(ai.doc_ket_qua(json.dumps(tra), False)["tieu_chi"]), 5)
	nem("không có JSON", lambda: ai.doc_ket_qua("Xin lỗi, tôi không đọc được.", True), ValueError)
	la("ngưỡng nhãn", [ai.nhan_diem(x) for x in (80, 79, 65, 50, 49, None)], ["Rất phù hợp", "Phù hợp", "Phù hợp", "Tạm được", "Chưa phù hợp", ""])
	la("khung sai", [ai.khung_hop_le(k) for k in ([0.5, 0, 0.2, 1], [0, 0, 0.01, 0.01], "x", [0, 0, 1])], [None] * 4)
	la("chọn ảnh chân dung, bỏ ảnh phủ trang và ảnh nhỏ", ai.chon_anh([(1, 2480, 3508), (1, 40, 40), (1, 300, 400), (2, 500, 500)]), 3)
	la("ưu tiên trang AI chỉ", ai.chon_anh([(1, 300, 400), (2, 500, 500)], 1), 0)
	la("PDF quét", ai.la_trang_quet([(1, 1240, 1754)]), 0)
	for w, h, k in ((1000, 1400, None), (1000, 1400, [0.7, 0.05, 0.99, 0.3]), (300, 200, [0, 0, 1, 1])):
		x0, y0, x1, y1 = ai.vung_vuong(w, h, k)
		dung("hộp cắt vuông nằm trong ảnh %s" % ((w, h, k),), 0 <= x0 < x1 <= w and 0 <= y0 < y1 <= h and abs((x1 - x0) - (y1 - y0)) <= 1)
	la("loại tệp theo byte đầu, không theo đuôi", [ai.loai_tep(b) for b in (b"%PDF-1.7", b"\xff\xd8\xff\xe0", b"\x89PNG\r\n\x1a\nx", b"MZ\x90")],
		["application/pdf", "image/jpeg", "image/png", None])


def _uv_doc(**k):
	d = {"name": "UV-1", "vi_tri": "VTT-0002", "da_an_danh": 0, "tep_cv": "", "kinh_nghiem": "", "ca_ranh": "", "khu_vuc": "",
		"gioi_thieu": "", "tra_loi": [types.SimpleNamespace(ma="luong", cau_hoi="Lương", tra_loi="9.000.000 đ/tháng"),
			types.SimpleNamespace(ma="gioi_tinh", cau_hoi="Giới", tra_loi="Nữ (Female)")]}
	d.update(k)
	o = types.SimpleNamespace(**d)
	o.get = lambda x, m=None: d.get(x, m)
	return o


def _chay_ai(uv, khoa="sk-thu", goi=None, da_dung=0):
	ghi, gui = [], []

	def _goi(khoa_, mo_hinh, he, hoi, khoi):
		gui.append((mo_hinh, he, hoi, khoi))
		if isinstance(goi, Exception):
			raise goi
		return goi
	db = types.SimpleNamespace(get_value=lambda *a, **k: _fr._dict(VTT2), rollback=lambda *a, **k: None)
	ps = [um.patch.object(ai, "_khoa_mo_hinh", lambda: (khoa, "claude-thu")), um.patch.object(ai, "_da_dung_thang", lambda: da_dung),
		um.patch.object(ai, "_goi", _goi), um.patch.object(ai, "_ghi", lambda ten, v: ghi.append((ten, v))),
		um.patch.object(ai, "requests", types.SimpleNamespace()), um.patch.object(ai.frappe, "db", db),
		um.patch.object(ai.frappe, "get_doc", lambda *a, **k: uv), um.patch.object(ai.frappe, "log_error", lambda *a, **k: None, create=True),
		um.patch.object(ai.frappe, "get_traceback", lambda *a, **k: "", create=True),
		um.patch.object(ai.frappe.utils, "nowdate", lambda: "2026-10-31", create=True),
		um.patch.object(ai.frappe.utils, "now_datetime", lambda: dt.datetime(2026, 10, 31, 9), create=True),
		um.patch.object(td, "noi_dung_cong_khai", lambda: {})]
	for p in ps:
		p.start()
	try:
		ai.doc_ho_so("UV-1")
	finally:
		for p in reversed(ps):
			p.stop()
	return ghi, gui


@ca("v625 việc nền AI: chưa có khoá, hết trần tháng, mô hình lỗi đều ghi lý do lên hồ sơ; đọc xong ghi điểm và tóm tắt")
def _ai_viec_nen():
	ghi, gui = _chay_ai(_uv_doc(), khoa="")
	la("không khoá: Chưa bật AI, không gọi mạng", (ghi[0][1]["ai_trang_thai"], len(gui)), (ai.TT_CHUA_BAT, 0))
	ghi, gui = _chay_ai(_uv_doc(), da_dung=ai.TRAN_THANG)
	la("hết trần tháng", (ghi[0][1]["ai_trang_thai"], len(gui)), (ai.TT_LOI, 0))
	dung("lý do nói việc cần làm", "tháng" in ghi[0][1]["ai_loi"])
	ghi, gui = _chay_ai(_uv_doc(), goi=RuntimeError("Khoá AI hết hạn, vào Cài đặt thay khoá."))
	la("mô hình lỗi: ghi đúng câu", (ghi[-1][1]["ai_trang_thai"], ghi[-1][1]["ai_loi"]), (ai.TT_LOI, "Khoá AI hết hạn, vào Cài đặt thay khoá."))
	tra = json.dumps({"tom_tat": "Hợp vị trí", "tieu_chi": [{"ten": t, "diem": 80} for t in ai.TIEU_CHI_AI]})
	ghi, gui = _chay_ai(_uv_doc(), goi=tra)
	v = ghi[-1][1]
	la("đọc xong", (v["ai_trang_thai"], v["ai_diem"], v["ai_tom_tat"]), (ai.TT_XONG, 80, "Hợp vị trí"))
	la("kết quả đầy đủ để mở Hồ sơ AI", json.loads(v["ai_ket_qua"])["nhan"], "Rất phù hợp")
	dung("không CV: không gửi khối tệp", gui[0][3] is None)
	dung("giới tính trong câu trả lời không tới AI", "Nữ (Female)" not in gui[0][2])
	ghi, gui = _chay_ai(_uv_doc(da_an_danh=1), goi=tra)
	la("hồ sơ đã xoá theo hạn: không đọc", (ghi, gui), ([], []))
	m = _doc_tep("tuyen_dung_ai.py")
	dung("requests nạp mềm cho CI", "try:\n\timport requests\nexcept ImportError" in m)
	dung("xếp việc nền sau commit, không trùng", "enqueue_after_commit=True" in m and "deduplicate=True" in m)


# ------------------------------------------------------------ nộp hồ sơ

@ca("v625 nộp hồ sơ form mới: ghi ô và bảng trả lời, gắn CV theo mã tạm một lần; gửi lại cùng mã không tạo thêm")
def _ung_tuyen_moi():
	site = _Site(vt=[VTT2])
	site.bang("File").append(_fr._dict(name="F-CV1", file_url="/private/files/cv-aaaa.pdf"))
	cache = {"vgb_cv_tam:" + "a" * 24: "F-CV1"}
	cc = types.SimpleNamespace(get_value=lambda k: cache.get(k), delete_value=lambda k: cache.pop(k, None), set_value=lambda *a, **k: None)
	ma = "1b4e28ba-2fa1-11d2-883f-0016d3cca427"
	goi = {"vi_tri": "VTT-0002", "tra_loi": _tl(), "ma_cv": "a" * 24, "nguon": "Web Vagabond", "dong_y": 1, "web": ""}
	ps = [um.patch.object(td, "noi_dung_cong_khai", lambda: {}), um.patch.object(td.frappe, "cache", lambda: cc, create=True),
		um.patch.object(td, "_hom_nay", lambda: "2026-10-31")]
	for p in ps:
		p.start()
	try:
		kq = _chay(site, lambda: td.ung_tuyen(json.dumps(goi), ma))
		hs = site.bang(td.UV)
		la("một hồ sơ", len(hs), 1)
		h = hs[0]
		la("ô riêng", (h["ho_ten"], h["email"], h["sinh_nhat"], h["luong_mong_muon"], h["tep_cv"]),
			("Trần Thị Bình", "binh@gmail.com", "2001-05-17", 9000000, "/private/files/cv-aaaa.pdf"))
		la("bảng trả lời", [d["ma"] for d in h["tra_loi"]], ["ho_ten", "gioi_tinh", "sinh_nhat", "sdt", "email", "tham_nien",
			"thoi_gian", "hoc_van", "luong", "biet_tin", "nhan_them"])
		dung("CV gắn vào hồ sơ", ("File", "F-CV1", {"attached_to_doctype": td.UV, "attached_to_name": kq["ma"], "attached_to_field": "tep_cv"}) in site.set_value)
		la("mã tạm dùng xong bị xoá", cache, {})
		la("gửi lại cùng mã: hồ sơ cũ", _chay(site, lambda: td.ung_tuyen(json.dumps(goi), ma))["ma"], kq["ma"])
		la("vẫn một hồ sơ", len(site.bang(td.UV)), 1)
		ma2 = "2b4e28ba-2fa1-11d2-883f-0016d3cca427"
		dung("mã CV hết hạn: báo tải lại", "hết hạn" in _loi(lambda: _chay(site, lambda: td.ung_tuyen(json.dumps(dict(goi, tra_loi=_tl(ho_ten="Người khác"))), ma2))))
		dung("mã CV sai dạng", "không hợp lệ" in _loi(lambda: _chay(site, lambda: td.ung_tuyen(json.dumps(dict(goi, ma_cv="../x")), ma2))))
		dung("thiếu câu bắt buộc: báo đúng câu", "Trình độ học vấn" in _loi(lambda: _chay(site, lambda: td.ung_tuyen(
			json.dumps(dict(goi, ma_cv="", tra_loi=_tl(hoc_van=""))), ma2))))
		dung("chưa tích đồng ý", "đồng ý" in _loi(lambda: _chay(site, lambda: td.ung_tuyen(json.dumps(dict(goi, ma_cv="", dong_y=0)), ma2))))
		la("vẫn một hồ sơ sau các lần bị chặn", len(site.bang(td.UV)), 1)
	finally:
		for p in reversed(ps):
			p.stop()
	m = _doc_tep("tuyen_dung.py")
	dung("tải CV có trần lượt", "@frappe.whitelist(methods=[\"POST\"], allow_guest=True)\n@rate_limit(limit=10, seconds=600)\ndef tai_cv():" in m)
	dung("tệp CV riêng tư, tên do máy chủ đặt", "is_private=1" in m and '"cv-" + frappe.generate_hash(length=16)' in m)


@ca("v625 hồ sơ AI, CV, ảnh: chỉ quyền Tuyển dụng mở được; hồ sơ đã xoá theo hạn không mở")
def _quyen_ai():
	site = _Site(vt=[VTT2], uv=[{"name": "UV-1", "vi_tri": "VTT-0002", "da_an_danh": 0, "tep_cv": "/private/files/cv-a.pdf",
		"anh_dai_dien": "", "ai_ket_qua": json.dumps({"diem": 70, "anh": {"co": True}}), "ai_trang_thai": "Đã đọc", "ho_ten": "Bình"},
		{"name": "UV-2", "vi_tri": "VTT-0002", "da_an_danh": 1, "tep_cv": ""}])
	for ten, ham in (("xem_cv", lambda: td.xem_cv("UV-1")), ("anh_ung_vien", lambda: td.anh_ung_vien("UV-1")),
			("ho_so_ai", lambda: td.ho_so_ai("UV-1")), ("cham_lai", lambda: td.cham_lai("UV-1")), ("tai_cv_app", lambda: td.tai_cv_app("UV-1"))):
		dung(ten + " chặn người ngoài", _loi(lambda: _chay(site, ham, vai=("Sales User",))) != "")
	kq = _chay(site, lambda: td.ho_so_ai("UV-1"))
	la("hồ sơ AI không trả khung ảnh", (kq["kq"]["diem"], "anh" in kq["kq"], kq["co_cv"]), (70, False, 1))
	dung("hồ sơ đã xoá theo hạn", "đã xoá" in _loi(lambda: _chay(site, lambda: td.ho_so_ai("UV-2"))))


@ca("v625 hết hạn lưu: xoá cả CV, ảnh, sinh nhật, lương mong muốn, chữ AI; bản đã xoá vẫn lưu lại được (không kẹt vì ô ngày, ô tiền)")
def _an_danh():
	a = td.an_danh({})
	for k in ("sinh_nhat", "luong_mong_muon", "tep_cv", "anh_dai_dien", "ai_tom_tat", "ai_ket_qua", "ai_loi"):
		dung("xoá " + k, k in a and not a[k])
	da = dict(a, da_an_danh=1, sinh_nhat=None, luong_mong_muon=0.0, danh_gia=[], tra_loi=[])
	la("lưu lại hồ sơ đã xoá (trạng thái, vị trí) vẫn được", td.kiem_an_danh(da, 1), "")
	dung("ghi lại câu trả lời sau khi xoá: chặn", td.kiem_an_danh(dict(da, tra_loi=[{"tra_loi": "x"}]), 1) != "")
	dung("ghi lại sinh nhật sau khi xoá: chặn", td.kiem_an_danh(dict(da, sinh_nhat="2001-01-01"), 1) != "")


@ca("v625 doctype: ô mới có trong JSON đúng loại, bảng trả lời là bảng con, đổi bố cục có mốc modified mới")
def _doctype():
	uv = json.loads(_doc_tep("vagabond", "doctype", "vagabond_ung_vien", "vagabond_ung_vien.json"))
	tl = json.loads(_doc_tep("vagabond", "doctype", "vagabond_ung_vien_tra_loi", "vagabond_ung_vien_tra_loi.json"))
	vt = json.loads(_doc_tep("vagabond", "doctype", "vagabond_vi_tri_tuyen", "vagabond_vi_tri_tuyen.json"))
	o = {f["fieldname"]: f for f in uv["fields"]}
	la("loại ô", [o[k]["fieldtype"] for k in ("sinh_nhat", "luong_mong_muon", "tep_cv", "tra_loi", "ai_trang_thai", "ai_diem",
		"ai_ket_qua", "anh_dai_dien")], ["Date", "Currency", "Attach", "Table", "Select", "Int", "Long Text", "Long Text"])
	la("trạng thái AI trùng máy chủ", o["ai_trang_thai"]["options"].split("\n")[1:], [ai.TT_DANG, ai.TT_XONG, ai.TT_LOI, ai.TT_CHUA_BAT])
	la("bảng con", (tl.get("istable"), o["tra_loi"]["options"]), (1, "Vagabond Ung Vien Tra Loi"))
	la("ô vị trí mới", sorted(f["fieldname"] for f in vt["fields"] if f["fieldname"] in ("tuyen_gap", "anh_web")), ["anh_web", "tuyen_gap"])
	for j in (uv, tl, vt):
		la("%s: thứ tự ô đủ" % j["name"], j["field_order"], [f["fieldname"] for f in j["fields"]])
		dung("%s: mốc modified mới" % j["name"], str(j.get("modified", "")) >= "2026-10-31 20:00")
	for k in td.TRUONG_UV:
		dung("ô %s máy chủ đọc có trong JSON" % k, k in o or k in ("name", "creation"))


@ca("v625 web Vue Tuyển dụng phương án A: ca hành vi chạy thật bằng node đều đạt")
def _vue():
	import os
	import re
	import subprocess
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/tuyen_dung_vue_625.mjs"], cwd=goc, capture_output=True, text=True, timeout=60)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)
	m = re.search(r"(\d+) ca dat, 0 ca hong", r.stdout)
	dung("đủ số ca", m and int(m.group(1)) >= 7)


@ca("v625 trang ứng tuyển và trình biên tập: mọi tệp ?v= khớp nội dung (vượt cache immutable, #310)")
def _ma_bam():
	import hashlib
	import os
	import re
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	for trang in (("www", "ung-tuyen.html"), ("www", "bien-tap-web.html")):
		s = _doc_tep(*trang)
		ds = re.findall(r"/assets/vagabond/(web_order/[\w.-]+\.(?:css|js))\?v=([0-9a-f]+)", s)
		dung("%s có tệp gắn mã" % trang[1], len(ds) >= 2)
		for tep, ma in ds:
			with open(os.path.join(goc, "public", tep), "rb") as f:
				la("%s: %s" % (trang[1], tep), ma, hashlib.sha256(f.read()).hexdigest()[:12])
