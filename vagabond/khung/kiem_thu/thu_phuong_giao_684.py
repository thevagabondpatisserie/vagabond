# -*- coding: utf-8 -*-
"""v684 (BẢN 2 mục 2.3): ô Phường giao theo phường mới.

Bảng phường (phuong_giao.py) là dữ liệu tay theo Nghị quyết 1685, tên và mã
theo Pancake. Không có phí dự kiến (anh Việt bỏ 22/11/2026). Ở đây chốt: đủ
20 khu vực đang giao, không thừa phường ngoài vùng; năm phường có phần ngoài
vùng đúng như anh duyệt; địa chỉ gửi
Pancake mang tên phường mới đúng một lần; tao_don THẬT ghi phường vào ảnh
chụp đơn và bỏ qua mã phường lạ.
"""

import json

from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("v684 bảng phường: đủ 20 khu vực đang giao, mã duy nhất theo Pancake, không phường ngoài vùng, chỉ 3 loại")
def _():
	from vagabond import don_web, phuong_giao as g
	ds = g.danh_sach()
	la("83 phường, xã mới", len(ds), 83)
	la("mã không trùng", len({p["ma"] for p in ds}), 83)
	la("đủ đúng 20 khu vực đang giao", sorted({p["khu"] for p in ds}), sorted(q["ma"] for q in don_web.QUAN))
	dung("mã theo Pancake", all(p["ma"].startswith("84_VN129") for p in ds))
	dung("tên có Phường hoặc Xã", all(p["ten"].startswith(("Phường ", "Xã ")) for p in ds))
	la("loại", sorted({p["loai"] for p in ds}), ["", "mot_phan"])
	la("phường có phần ngoài vùng (anh Việt duyệt 22/11)",
		sorted(p["ten"] for p in ds if p["loai"] == "mot_phan"),
		["Phường Bình Đông", "Phường Tân Tạo", "Xã Bình Hưng", "Xã Tân Nhựt", "Xã Tân Vĩnh Lộc"])
	dung("không có phí trong bảng (anh Việt bỏ phí dự kiến 22/11)", not any("phi" in p for p in ds))
	dung("không lọt phường Bình Dương, Bà Rịa Vũng Tàu", not any(p["ten"] in ("Phường Dĩ An", "Phường Vũng Tàu", "Phường Thủ Dầu Một") for p in ds))
	la("phường cũ ghi tắt đọc thành chữ", g.tim("84_VN129015")["cu"][:2], ["Phường 1", "Phường 2"])
	la("mã lạ", (g.tim("84_VN12999"), g.tim(""), g.tim(None)), (None, None, None))


@ca("v684 địa chỉ gửi Pancake mang tên phường mới đúng một lần, gõ không dấu cũng nhận ra đã có")
def _():
	from vagabond import phuong_giao as g
	p = g.tim("84_VN12903")
	la("nối thêm", g.dia_chi_co_phuong("10 Lê Lợi, Quận 1", p), "10 Lê Lợi, Quận 1, Phường Bến Thành")
	la("đã có thì giữ", g.dia_chi_co_phuong("10 Lê Lợi, Phường Bến Thành", p), "10 Lê Lợi, Phường Bến Thành")
	la("không dấu vẫn nhận ra", g.dia_chi_co_phuong("10 le loi, p ben thanh", p), "10 le loi, p ben thanh")
	la("dấu phẩy thừa cuối", g.dia_chi_co_phuong("10 Lê Lợi, ", p), "10 Lê Lợi, Phường Bến Thành")
	la("không chọn phường", g.dia_chi_co_phuong("10 Lê Lợi", None), "10 Lê Lợi")
	la("xã", g.dia_chi_co_phuong("Ấp 3", g.tim("84_VN129134")), "Ấp 3, Xã Nhà Bè")


@ca("v684 tao_don THẬT: khách chọn phường thì địa chỉ Pancake và ảnh chụp mang phường mới; mã lạ bị bỏ; tự lấy không có phường")
def _():
	from vagabond.khung.kiem_thu.thu_don_web_367 import _Tra, _don, _moi_truong_tao_don
	vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "1"}}))
	d = _don(phuong="84_VN12903")
	goc = d.get("dia_chi") or ""
	kq = tao_don(d)
	la("đơn thành", kq.get("ok"), 1)
	dung("địa chỉ Pancake có phường mới", vet.body["shipping_address"]["address"].endswith("Phường Bến Thành") or "Bến Thành" in goc)
	sn = json.loads(vet.truong["snapshot"])
	la("ảnh chụp ghi phường", sn.get("phuong"), {"ma": "84_VN12903", "ten": "Phường Bến Thành"})
	vet2, tao_don2 = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "2"}}))
	tao_don2(_don(phuong="84_VN_LA"))
	sn2 = json.loads(vet2.truong["snapshot"])
	dung("mã lạ: không có phường, địa chỉ giữ nguyên", "phuong" not in sn2 and vet2.body["shipping_address"]["address"] == goc)


@ca("v684 Codex #606: báo phí trên trang hỏi ĐÚNG nơi lúc gửi đơn hỏi: phi_giao nhận mã phường và ghép phường bằng cùng hàm; đổi phường là đổi nơi hỏi; mã lạ bị bỏ")
def _():
	import sys
	import types

	import vagabond.giao_hang as gh
	from vagabond import phuong_giao as g
	from vagabond.khung.kiem_thu.nen import Doi

	hoi = []
	dc = types.ModuleType("vagabond.dia_chi")
	dc.geocode = lambda c, addr: (hoi.append(addr), None)[1]
	cu_mod, cu = sys.modules.get("vagabond.dia_chi"), (gh.cfg, gh.key)
	sys.modules["vagabond.dia_chi"] = dc
	gh.cfg = lambda: Doi({"nguon_phi_giao_web": "Ahamove", "ahamove_api_key": "k",
		"ahamove_base": "https://x", "ahamove_mobile": "84900000000"})
	gh.key = lambda doc, f: str(doc.get(f) or "")
	try:
		for ma in ("84_VN12903", "84_VN12901", "84_VN_LA", None):
			kq = gh.phi_giao(addr="10 Lê Lợi", phuong=ma)
			la("không tìm thấy địa chỉ giả", kq.get("ly_do"), "khong_tim_thay_dia_chi")
	finally:
		gh.cfg, gh.key = cu
		if cu_mod is None:
			sys.modules.pop("vagabond.dia_chi", None)
		else:
			sys.modules["vagabond.dia_chi"] = cu_mod
	la("nơi hỏi phí theo phường", hoi, [
		g.dia_chi_co_phuong("10 Lê Lợi", g.tim("84_VN12903")),
		g.dia_chi_co_phuong("10 Lê Lợi", g.tim("84_VN12901")),
		"10 Lê Lợi", "10 Lê Lợi"])
	dung("hai phường khác nhau là hai nơi hỏi khác nhau", hoi[0] != hoi[1])


@ca("v684 Codex #606: chữ khách thấy không do máy chủ ghép: tên quận cũ không kèm chữ cũ, thẻ ĐƠN HÀNG chỉ trả lựa chọn đã lưu")
def _():
	from vagabond import bien_nhan_web as b, phuong_giao as g
	dung("quận cũ là dữ liệu", all(not p["quan_cu"].endswith(" cũ") for p in g.danh_sach()))
	import json as _j
	s = _j.dumps(b.dong_don({"mon": [{"ma": "B1", "sl": 1, "gia": 1}, {"ma": "BAPK00020", "sl": 2, "gia": 0}],
		"chiec": [{"ma": "B1", "ten": "Epi", "co": False, "thiep": "nho", "loi_thiep": "Yêu"}]}), ensure_ascii=False)
	for chu in ("Không cờ", "Cờ chưa", "Thiệp nhỏ", "Không thiệp", "tặng kèm", "Dĩa", "dĩa", "nĩa"):
		dung("máy chủ không trả chữ " + chu, chu not in s)


@ca("v684 Codex #606: địa chỉ kiểu cũ (còn Quận, Huyện) mang tên phường CŨ: Phường Tân Phú, Quận 7 cũ nay là Tân Mỹ; máy chủ vẫn ghi rõ phường mới, không coi là đã có")
def _():
	from vagabond import phuong_giao as g
	cu = "10 Nguyễn Lương Bằng, Phường Tân Phú, Quận 7, TP. Hồ Chí Minh"
	la("nhận ra kiểu cũ", [g.la_dia_chi_cu(cu), g.la_dia_chi_cu("12 Võ Văn Ngân, TP. Thủ Đức"),
		g.la_dia_chi_cu("5 Hai Bà Trưng, Phường Tân Định, Thành phố Hồ Chí Minh")], [True, True, False])
	la("chọn phường Tân Phú mới mà địa chỉ ghi Tân Phú cũ: vẫn ghi rõ phường mới", g.dia_chi_co_phuong(cu, g.tim("84_VN12965")),
		cu + ", Phường Tân Phú")
	la("chọn Tân Mỹ: ghi Tân Mỹ", g.dia_chi_co_phuong(cu, g.tim("84_VN12920")), cu + ", Phường Tân Mỹ")
	la("địa chỉ kiểu mới đã có tên: giữ nguyên", g.dia_chi_co_phuong("5 Hai Bà Trưng, Phường Tân Định", g.tim("84_VN12902")), "5 Hai Bà Trưng, Phường Tân Định")


@ca("v684 Codex #606 vòng 2: phường chỉ tính là đã có khi là MỘT phần riêng của địa chỉ; đường trùng tên phường (10 Tân Sơn) hay phường dài hơn (Tân Sơn Nhì) không tính")
def _():
	from vagabond import phuong_giao as g
	ts, tsn = g.tim("84_VN12961"), [p for p in g.danh_sach() if p["ten"] == "Phường Tân Sơn Nhì"][0]
	la("đường trùng tên: vẫn ghi phường", g.dia_chi_co_phuong("10 Tân Sơn", ts), "10 Tân Sơn, Phường Tân Sơn")
	la("phường dài hơn không tính là có", g.dia_chi_co_phuong("7 Lũy Bán Bích, Phường Tân Sơn Nhì", ts),
		"7 Lũy Bán Bích, Phường Tân Sơn Nhì, Phường Tân Sơn")
	la("viết tắt P. là có", [g.dia_chi_co_phuong(a, ts) for a in ("10 Tân Sơn, P. Tân Sơn", "10 x, p tan son", "10 x, P.Tân Sơn")],
		["10 Tân Sơn, P. Tân Sơn", "10 x, p tan son", "10 x, P.Tân Sơn"])
	la("đúng phường dài hơn thì giữ", g.dia_chi_co_phuong("7 Lũy Bán Bích, Phường Tân Sơn Nhì", tsn), "7 Lũy Bán Bích, Phường Tân Sơn Nhì")
