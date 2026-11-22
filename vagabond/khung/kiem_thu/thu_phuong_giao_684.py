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
