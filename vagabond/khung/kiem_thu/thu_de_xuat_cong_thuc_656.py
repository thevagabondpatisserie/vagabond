# -*- coding: utf-8 -*-
"""v656 Phiếu Đề xuất công thức (anh Việt 13/11/2026, ảnh duyệt JPEG).

Ca chốt, dùng số thật trên site 13/11:
  - gõ "Pomelo confit" phải ra mã BTPB00215 "BTP Compote Pomelo, Bưởi" (ô tìm cũ
    khớp nguyên cụm nên không ra); gõ không dấu cũng ra;
  - nhập size 16 Very Berry, máy gợi ý 12, 18, 20 theo diện tích khuôn; dòng
    trang trí giữ nguyên; không đè ô bếp đã nhập; Slice không gợi ý;
  - kế hoạch tạo cấp: có dòng cấp 1 và cấp 2 thì cấp 2 gồm một cái cấp 1, thành
    phẩm gồm một cái cấp 2 cộng trang trí; không dòng nào vào cấp thì thành phẩm
    gồm thẳng thành phần (như Very Berry);
  - giá vốn dự kiến từng size, thành phần mới tính từ công thức con, thiếu giá
    được nêu tên (bản Pinkpom đầu tiên ghi sổ 1.373 đ vì cấp 2 giá 0);
  - bảng trước và sau: cấp 2 Pinkpom bản 002 lên 003 thêm Compote Pomelo 15 g;
  - kiểm phiếu trước khi gửi: thiếu cấp, thành phần mới thiếu công thức con,
    vòng công thức con, size chưa có gram;
  - việc cần làm đúng người.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import de_xuat_cong_thuc as x  # noqa: E402

UV = [
	{"ma": "BTPB00215", "ten": " BTPB00215 BTP Compote Pomelo, Bưởi"},
	{"ma": "NVLT00358", "ten": "Trái bưởi tươi, Kg"},
	{"ma": "BTPB00028", "ten": "BTP Cherry compote"},
	{"ma": "BTPB00107", "ten": "BTP Pastry cream Danish Đào"},
]


@ca("v656: gõ tên mới thì báo mã gần giống, tìm theo từng chữ, bỏ dấu")
def _goi_y():
	la("Pomelo confit ra Compote Pomelo bưởi trước", [u["ma"] for u in x.xep_goi_y("Pomelo confit", UV)][:1], ["BTPB00215"])
	la("Compote bưởi: Compote Pomelo bưởi trùng hai chữ đứng đầu", [u["ma"] for u in x.xep_goi_y("Compote bưởi", UV)][:1], ["BTPB00215"])
	la("gõ không dấu vẫn ra", [u["ma"] for u in x.xep_goi_y("compote buoi", UV)][:1], ["BTPB00215"])
	la("chữ chung chung không tính (btp, bánh, size)", x.xep_goi_y("BTP bánh size 16", UV), [])
	la("mã trong tên không tính là chữ", x.tach_chu(" BTPB00215 BTP Compote Pomelo, Bưởi"), ["compote", "pomelo", "buoi"])
	la("đ thành d", x.chuan_hoa("Đậu xanh đào"), "dau xanh dao")
	la("không trùng chữ nào thì không gợi ý", x.xep_goi_y("Lychee", UV), [])


@ca("v656: nhập một size, máy gợi ý size khác theo diện tích khuôn tròn (số thật Very Berry)")
def _size():
	la("đọc size", [x.so_size(s) for s in ("16", "16cm", "size 18 cm", "Slice", "", "0")], [16, 16, 18, None, None, None])
	la("Naked Very cherry 537 g size 16", [x.goi_y_size(537, "16", s) for s in ("12", "18", "20")], [302, 680, 839])
	la("Cherry compote 90 g", [x.goi_y_size(90, "16", s) for s in ("12", "18", "20")], [51, 114, 141])
	la("Slice không gợi ý", x.goi_y_size(90, "16", "Slice"), None)
	dong = {"dich": "cap2", "gram": {"16": 537, "20": 860}}
	la("không đè ô bếp đã nhập (20 giữ 860)", x.goi_y_dong(dong, ["12", "16", "18", "20"], "16"),
		{"16": 537, "20": 860, "12": 302, "18": 680})
	la("dòng trang trí giữ nguyên số", x.goi_y_dong({"dich": "thanh_pham", "gram": {"16": 0.005}}, ["16", "18"], "16"),
		{"16": 0.005, "18": 0.005})
	la("số nhỏ giữ ba số lẻ", x.goi_y_size(0.5, "16", "20"), 0.781)


def _phieu():
	return {"sizes": ["16", "18"], "dong": [
		{"id": "a", "ma": "BTPB00136", "ten": "Ruby Chocolate Crunchy", "dich": "cap1", "gram": {"16": 100, "18": 130}},
		{"id": "b", "ten": "Peach and Lychee Confit", "dich": "cap2", "gram": {"16": 90, "18": 114},
			"con": {"me": 1000, "dong": [{"ma": "NVLT00268", "ten": "Puree Ruby Peach", "sl": 600}, {"dong_id": "c", "ten": "Đào ganache", "sl": 400}]}},
		{"id": "c", "ten": "Đào ganache", "dich": "cap2", "gram": {},
			"con": {"me": 500, "dong": [{"ma": "NVLT00032", "ten": "Chocolate", "sl": 500}]}},
		{"id": "d", "ma": "NVLT00184", "ten": "Lá bạc trang trí", "dich": "thanh_pham", "gram": {"16": 0.005, "18": 0.005}},
	]}


@ca("v656: kế hoạch tạo cấp 1, cấp 2, thành phẩm từng size từ chip bếp chọn")
def _ke_hoach():
	k = x.ke_hoach(_phieu())
	la("thành phần mới tạo theo thứ tự: Đào ganache trước Confit dùng nó", k["moi"], ["c", "b"])
	s = k["size"]["16"]
	la("cấp 1 gồm crunchy", s["cap1"], [("dong", "a", 100.0)])
	la("cấp 2 gồm một cái cấp 1 và confit", s["cap2"], [("cap", "cap1", 1), ("dong", "b", 90.0)])
	la("thành phẩm gồm một cái cấp 2 và lá bạc", s["tp"], [("cap", "cap2", 1), ("dong", "d", 0.005)])
	la("Đào ganache không gram ở size nào: chỉ dùng trong công thức con", any(t[1] == "c" for n in k["size"].values() for v in n.values() for t in v if t[0] == "dong"), False)
	p = _phieu()
	for d in p["dong"]:
		d["dich"] = "thanh_pham"
	s = x.ke_hoach(p)["size"]["18"]
	la("không dòng nào vào cấp: thành phẩm gồm thẳng thành phần (như Very Berry)",
		(s["cap1"], s["cap2"], [k[1] for k in s["tp"]]), ([], [], ["a", "b", "d"]))
	p = _phieu()
	p["dong"][1]["dich"] = "cap1"
	s = x.ke_hoach(p)["size"]["16"]
	la("chỉ có cấp 1: thành phẩm gồm một cái cấp 1", (s["cap2"], s["tp"][0]), ([], ("cap", "cap1", 1)))


@ca("v656: giá vốn dự kiến từng size, thành phần mới tính từ công thức con, nêu tên dòng thiếu giá")
def _gia_von():
	gia = {"BTPB00136": 246.99, "NVLT00268": 200.0, "NVLT00032": 113.0, "NVLT00184": 12546.68}
	g = x.gia_von(_phieu(), gia)
	la("đơn giá Đào ganache = 500 x 113 / 500", round(g["don_gia_moi"]["c"], 2), 113.0)
	la("đơn giá Confit = (600 x 200 + 400 x 113) / 1000", round(g["don_gia_moi"]["b"], 2), 165.2)
	la("giá vốn size 16 = 100 x 246,99 + 90 x 165,2 + 0,005 x 12546,68", g["size"]["16"], round(100 * 246.99 + 90 * 165.2 + 0.005 * 12546.68))
	la("đủ giá thì không báo thiếu", g["thieu"], [])
	gia.pop("NVLT00184")
	la("lá bạc chưa có giá thì nêu tên", x.gia_von(_phieu(), gia)["thieu"], ["Lá bạc trang trí"])
	la("Pinkpom bản đầu: cấp 2 giá 0 thì báo thiếu", x.gia_von({"sizes": ["1"], "dong": [
		{"id": "a", "ma": "BTPB00218", "ten": "BTP CAP2 Sẵn sàng Bánh Pinkpom", "dich": "thanh_pham", "gram": {"1": 1}}]}, {})["thieu"],
		["BTP CAP2 Sẵn sàng Bánh Pinkpom"])
	la("% giá bán: Very Berry 16cm 151.539 / 830.000", x.ty_le(151539, 830000), 18)
	la("chưa có giá bán thì không tính %", x.ty_le(151539, 0), None)


@ca("v656: bảng trước và sau của phiếu điều chỉnh (cấp 2 Pinkpom bản 002 lên 003)")
def _doi_chieu():
	cu = [{"ma": "BTPB00136", "ten": "Crunchy", "sl": 16.667}, {"ma": "BTPB00219", "ten": "Mousse dừa", "sl": 72}]
	moi = [{"ma": "BTPB00136", "ten": "Crunchy", "sl": 16.667}, {"ma": "BTPB00219", "ten": "Mousse dừa", "sl": 80},
		{"ma": "BTPB00215", "ten": "Compote Pomelo", "sl": 15}]
	b = x.doi_chieu(cu, moi)
	la("giữ, đổi gram, thêm dòng", [(r["ma"], r["kieu"], r["cu"], r["moi"]) for r in b],
		[("BTPB00136", "giu", 16.667, 16.667), ("BTPB00219", "doi", 72.0, 80.0), ("BTPB00215", "them", None, 15.0)])
	la("bỏ dòng đứng cuối", [(r["ma"], r["kieu"]) for r in x.doi_chieu(cu, moi[:1])][-1], ("BTPB00219", "bot"))
	dung("có thay đổi", x.co_thay_doi(b))
	dung("y nguyên thì không thay đổi", not x.co_thay_doi(x.doi_chieu(cu, cu)))


@ca("v656: kiểm phiếu trước khi gửi Khải, câu nói việc cần làm")
def _kiem():
	la("phiếu đủ thì không lỗi", x.kiem_phieu(x.LOAI_MOI, "Pinkpom", _phieu()), [])
	p = _phieu()
	p["dong"][0]["dich"] = ""
	dung("chưa chọn vào đâu", any("ruột (cấp 1)" in e for e in x.kiem_phieu(x.LOAI_MOI, "Pinkpom", p)))
	p = _phieu()
	p["dong"][1]["con"] = {"me": 0, "dong": []}
	e = x.kiem_phieu(x.LOAI_MOI, "Pinkpom", p)
	dung("thành phần mới thiếu mẻ và công thức con", any("bao nhiêu gram" in s for s in e) and any("công thức con" in s for s in e))
	p = _phieu()
	p["dong"][2]["con"]["dong"].append({"dong_id": "b", "ten": "Confit", "sl": 10})
	dung("vòng công thức con", any("thành vòng" in s for s in x.kiem_phieu(x.LOAI_MOI, "Pinkpom", p)))
	nem("thu_tu_tao báo vòng", lambda: x.thu_tu_tao(p["dong"]), ValueError)
	p = _phieu()
	p["sizes"].append("20")
	dung("size chưa có gram", any("Size 20" in s for s in x.kiem_phieu(x.LOAI_MOI, "Pinkpom", p)))
	dung("thiếu tên bánh", any("tên bánh" in s for s in x.kiem_phieu(x.LOAI_MOI, " ", _phieu())))
	dc = {"sizes": [], "dong": [{"id": "a", "ten": "Mới", "gram": {"": 5}}]}
	dung("điều chỉnh chỉ nhận mã có sẵn", any("mã có sẵn" in s for s in x.kiem_phieu(x.LOAI_DIEU_CHINH, "x", dc, "BOM-1")))
	la("JSON hỏng thì coi như trống", x.doc_du_lieu("{hỏng"), {"sizes": [], "dong": []})


@ca("v656: mã kế tiếp, tên cấp theo nếp đang có trên site, việc cần làm đúng người")
def _ma_ten_viec():
	la("mã kế tiếp sau NBTP00069", x.ma_tiep("NBTP", "NBTP00069"), "NBTP00070")
	la("nhóm chưa có mã nào", x.ma_tiep("BTPB", None), "BTPB00001")
	la("tên cấp 2 size 16", x.ten_cap("cap2", "Bánh Ổ Very Berry", "16"), ("BTP Cấp 2 Bánh Ổ Very Berry", "size 16cm"))
	la("tên cấp 1 slice", x.ten_cap("cap1", "Pinkpom", "Slice"), ("BTP Cấp 1 Pinkpom", "Slice"))
	la("ghép tên như Desk", x.ghep_ten("BTP Cấp 2 Pinkpom", "size 16cm", ""), "BTP Cấp 2 Pinkpom, size 16cm")
	la("Khải thấy Chờ Khải và Đã tạo nháp",
		[x.ma_viec(t, True, False) for t in (x.TT_NHAP, x.TT_CHO, x.TT_DA_TAO, x.TT_TRA, x.TT_XONG)], [False, True, True, False, False])
	la("người đề xuất chỉ thấy phiếu mình bị trả lại",
		[x.ma_viec(t, False, True) for t in (x.TT_NHAP, x.TT_CHO, x.TT_TRA)], [False, False, True])
	la("người khác không thấy phiếu trả lại của người ta", x.ma_viec(x.TT_TRA, False, False), False)


@ca("v656 màn chạy thật trong node: bếp lập phiếu (mã gần giống, gợi ý size, thiếu giá), Khải lên mã, đề xuất điều chỉnh")
def _man():
	import os
	import subprocess

	goc = os.path.dirname(os.path.abspath(__file__))
	r = subprocess.run(["node", os.path.join(goc, "hanh_vi", "de_xuat_cong_thuc_656.js")], capture_output=True, text=True, timeout=120)
	la("de_xuat_cong_thuc_656.js chạy xanh", (r.returncode, (r.stderr or "")[-400:]), (0, ""))


@ca("v656 việc cần làm: lọc người đề xuất ngay trong câu đọc, không lọc sau giới hạn dòng")
def _viec_doc_du():
	import unittest.mock as um

	import sys
	import types

	import vagabond as goi
	fr = __import__("frappe")
	hoi = []
	vtd = types.ModuleType("vagabond.viec_tu_dong")
	vtd.dong_viec = lambda loai, ma, nhom, phu, ngay, qh: {"loai": loai, "ma": ma, "nhom": nhom}

	class R(dict):
		__getattr__ = dict.get

	kho = [R(name="DXCT-%03d" % i, loai="Mới", ten_banh="B%d" % i, trang_thai=x.TT_TRA, nguoi_de_xuat="khac@x",
		modified="2026-11-%02d" % (i % 28 + 1)) for i in range(40)]
	kho.append(R(name="DXCT-999", loai="Mới", ten_banh="Của Hân", trang_thai=x.TT_TRA, nguoi_de_xuat="han@x", modified="2026-11-30"))

	def gia_get_all(dt, filters=None, **k):
		hoi.append((filters, k.get("limit_page_length")))
		ra = [r for r in kho if all((r.get(c) in v[1]) if isinstance(v, list) else r.get(c) == v for c, v in filters.items())]
		n = k.get("limit_page_length")
		return ra[:n] if n else ra

	with um.patch.object(fr, "get_all", gia_get_all), um.patch.object(fr, "session", type("S", (), {"user": "han@x"})(), create=True), \
			um.patch.object(x, "_ten", lambda u: u), \
			um.patch.dict(sys.modules, {"vagabond.viec_tu_dong": vtd}), um.patch.object(goi, "viec_tu_dong", vtd, create=True), \
			um.patch.object(x, "_ct", lambda: type("C", (), {"_vai_ghi_so": staticmethod(lambda: {"Manufacturing Manager"})})):
		ra = x.viec({"Bếp phó"})
	la("Hân thấy đúng phiếu của mình dù có 40 phiếu trả lại của người khác", [r["ma"] for r in ra], ["DXCT-999"])
	dung("câu đọc có lọc người đề xuất", any((f or {}).get("nguoi_de_xuat") == "han@x" for f, _ in hoi))


@ca("v656 nút Gợi ý size: lấy size tròn đầu tiên đã có gram làm gốc, Slice và khuôn vuông không làm gốc")
def _goi_y_cac_size():
	r = x.goi_y_cac_size({"dich": "cap2", "gram": {"Slice": 40, "16": 100}}, ["Slice", "16", "20"])
	la("bỏ Slice, lấy 16 làm gốc", (r["goc"], r["gram"]["20"], r["gram"]["Slice"]), ("16", 156, 40))
	r = x.goi_y_cac_size({"dich": "thanh_pham", "gram": {"16": 3}}, ["12", "16", "20"])
	la("trang trí giữ nguyên số", (r["gram"]["12"], r["gram"]["20"]), (3, 3))
	la("chưa có size tròn nào có gram", x.goi_y_cac_size({"gram": {"Slice": 5}}, ["Slice", "16"])["goc"], None)


@ca("v656 Codex #563: cờ nổ từng dòng theo hợp đồng phantom (BTP thành phần nổ xuống, cấp 1, cấp 2 giữ tồn)")
def _co_dong():
	la("BTP thành phần không quản tồn có công thức: dòng phantom trỏ công thức con",
		x.co_dong(0, "BOM-BTPB00215-001"), {"is_phantom_item": 1, "bom_no": "BOM-BTPB00215-001", "do_not_explode": 0})
	la("ruột cấp 1, bánh khuôn cấp 2 quản tồn có công thức: chặn nổ, bỏ bom_no",
		x.co_dong(1, "BOM-NBTP00070-001"), {"is_phantom_item": 0, "bom_no": "", "do_not_explode": 1})
	la("nguyên liệu mua vào: để mặc định", x.co_dong(1, ""), {})
	la("mã không quản tồn chưa có công thức: để mặc định (chưa có gì để nổ)", x.co_dong(0, ""), {})
