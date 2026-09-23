# -*- coding: utf-8 -*-
"""v520: thanh báo đếm đúng tờ nợ thật, và ô chọn đơn vị tìm được đơn vị
mang tên tiếng Anh.

Hai việc khác nhau nhưng cùng một gốc: dữ liệu CÓ mà màn hình không cho
người dùng thấy đúng, nên người dùng làm sai theo.
"""
import ast
from pathlib import Path
from types import SimpleNamespace

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.minvoice_chung_tu import NHOM_CHO_DUNG, khong_phai_hoa_don, nhom_cho_dung
from vagabond.tim_don_vi import chuan, khop, loc_don_vi

GOC = Path(__file__).resolve().parents[2]
MA_CT = (GOC / "minvoice_chung_tu.py").read_text(encoding="utf-8")
MA_DV = (GOC / "tim_don_vi.py").read_text(encoding="utf-8")


# ---------------------------------------------- thanh báo đếm tờ nợ thật

@ca("#520 bản ghi không số không ngày không phải hoá đơn, tờ vỏ ruột thật thì vẫn là")
def _thuan_dem():
	dung("không số không ngày", khong_phai_hoa_don("", ""))
	dung("None cũng vậy", khong_phai_hoa_don(None, None))
	dung("khoảng trắng cũng vậy", khong_phai_hoa_don("  ", " "))
	la("vỏ ruột thật: có ngày, chưa có số", khong_phai_hoa_don("", "2026-09-20"), False)
	la("có số mà thiếu ngày vẫn là hoá đơn", khong_phai_hoa_don("123", ""), False)
	la("đủ cả hai", khong_phai_hoa_don("123", "2026-09-20"), False)


def _chay_cho_dung(hd, pi, vo=()):
	"""Chạy `cho_dung_phieu_mua` THẬT lấy từ mã nguồn, nguồn dữ liệu là giả."""
	ham = [n for n in ast.parse(MA_CT).body
		if isinstance(n, ast.FunctionDef) and n.name == "cho_dung_phieu_mua"]

	def get_all(dt, filters=None, pluck=None, **k):
		if dt == "MInvoice Invoice":
			# Như SQL thật: BETWEEN không khớp ngày trống, tờ chưa có ngày chỉ
			# ra ở truy vấn "is not set".
			if (filters or {}).get("ngay_lap") == ["is", "not set"]:
				return [dict(x) for x in vo]
			return [dict(x) for x in hd if x.get("ngay_lap")]
		return [x for x in pi if x in filters["custom_minvoice_id"][1]]

	f = SimpleNamespace(get_all=get_all, whitelist=lambda: (lambda h: h),
		utils=SimpleNamespace(add_days=lambda d, n: "2026-03-26"))
	env = dict(frappe=f, _kiem_quyen=lambda: None, nowdate=lambda: "2026-09-23",
		cint=lambda n: int(n or 0), flt=lambda n: float(n or 0),
		DT_HD="MInvoice Invoice", PI="Purchase Invoice", LOAI_VAO="Đầu vào",
		TT_KHOI_DUNG=("Bị thay thế", "Đã huỷ"), nhom_cho_dung=nhom_cho_dung,
		NHOM_CHO_DUNG=NHOM_CHO_DUNG, khong_phai_hoa_don=khong_phai_hoa_don,
		rut_gon_loi=lambda s: s)
	exec(compile(ast.Module(body=ham, type_ignores=[]), "minvoice_chung_tu.py", "exec"), env)
	return env["cho_dung_phieu_mua"]()


@ca("#520 thanh báo KHÔNG đếm bản ghi rỗng cũ, vẫn đếm tờ nợ thật")
def _thanh_bao():
	# Ba loại nằm lẫn nhau, đúng như bảng thật ngày 23/09/2026.
	no_that = {"name": "uuid-1", "so_hd": 857, "ngay_lap": "2026-09-21", "tong_tien": 972000,
		"nguoi_mua_ban": "CÔNG TY A", "ly_do_bo_qua": "", "da_tao_chung_tu": 0, "so_lan_thu": 0}
	vo_ruot = {"name": "uuid-2", "so_hd": "", "ngay_lap": "2026-09-22", "tong_tien": 0,
		"nguoi_mua_ban": "", "ly_do_bo_qua": "", "da_tao_chung_tu": 0, "so_lan_thu": 0}
	rong = [{"name": "6ab31e97f475d1ec4eeca85%d" % i, "so_hd": "", "ngay_lap": None,
		"tong_tien": 0, "nguoi_mua_ban": "", "ly_do_bo_qua": "", "da_tao_chung_tu": 0,
		"so_lan_thu": 0} for i in range(5)]

	kq = _chay_cho_dung([no_that, vo_ruot], [], rong)
	la("chỉ đếm hai tờ thật", kq["so_to"], 2)
	la("không tờ rỗng nào lọt vào danh sách",
		[h for h in kq["ds"] if h["ma"].startswith("6ab31e")], [])
	la("tờ vỏ ruột vẫn nằm nhóm chờ nguồn",
		[h["nhom"] for h in kq["ds"] if h["ma"] == "uuid-2"], ["thieu_nguon"])
	la("tiền chỉ tính tờ thật", kq["tong_tien"], 972000)

	# Bỏ hết tờ thật đi thì thanh báo phải về 0, không còn 5 tờ rỗng.
	la("chỉ còn tờ rỗng thì không có gì để báo", _chay_cho_dung([], [], rong)["so_to"], 0)

	# Tờ đã thành chứng từ vẫn bị loại như cũ.
	la("tờ đã có phiếu mua thì thôi", _chay_cho_dung([no_that], ["uuid-1"], [])["so_to"], 0)


# ------------------------------------------------- ô chọn đơn vị tính

@ca("#520 phép khớp đơn vị: khớp tên lưu, ô tên, và tên đã dịch")
def _thuan_khop():
	la("gõ rỗng thì đơn vị nào cũng bày", khop(["Box", "Box", "Hộp"], ""), 0)
	la("khớp đầu chuỗi", khop(["Box", "Box", "Hộp"], "Bo"), 0)
	la("khớp đúng tên lưu dù bản dịch khác", khop(["Box", "Box", "Hộp"], "Box"), 0)
	la("khớp theo tên đã dịch", khop(["Box", "Box", "Hộp"], "Hộp"), 0)
	la("khớp giữa chuỗi xếp sau", khop(["Combo", "Combo", "Combo"], "omb"), 1)
	la("không dính thì thôi", khop(["Gram", "Gram", "Gram"], "xyz"), None)
	la("chuẩn hoá bỏ khoảng trắng thừa và chữ hoa", chuan("  Hộp  16 "), "hộp 16")


@ca("#520 lọc đơn vị: khớp đầu chuỗi lên trước, không trả bản trùng tên")
def _thuan_loc():
	hang = [("Box", "Box", "Hộp"), ("Hộp", "Hộp", "Hộp"), ("Hộp 16", "Hộp 16", "Hộp 16"),
		("Combo", "Combo", "Combo"), ("Gram", "Gram", "Gram")]
	la("gõ Box ra đúng Box", loc_don_vi(hang, "Box"), [["Box", "Hộp"]])
	ten = [x[0] for x in loc_don_vi(hang, "Hộp")]
	la("gõ Hộp ra cả ba", sorted(ten), ["Box", "Hộp", "Hộp 16"])
	la("Box mang mô tả là tên đã dịch", dict(loc_don_vi(hang, "Hộp")).get("Box"), "Hộp")
	la("đơn vị tên trùng bản dịch thì không bày mô tả thừa",
		dict(loc_don_vi(hang, "Hộp")).get("Hộp"), "")
	la("gõ rỗng thì bày hết", len(loc_don_vi(hang, "")), 5)
	la("giới hạn cắt đúng số", len(loc_don_vi(hang, "", 2)), 2)
	la("trùng tên chỉ lấy một", len(loc_don_vi(hang + [("Box", "Box", "Hộp")], "Box")), 1)
	# Chốt riêng thứ tự: khớp ĐẦU chuỗi phải đứng trước khớp giữa chuỗi, kể
	# cả khi khớp giữa chuỗi có tên xếp trước theo vần. Bỏ phép xếp này đi
	# thì hai dòng đảo chỗ, người gõ "op" sẽ thấy Hộp trước Opla.
	xep = [("Nop", "Nop", "Nop"), ("Opla", "Opla", "Opla")]
	la("khớp đầu chuỗi lên trước dù vần đứng sau",
		[x[0] for x in loc_don_vi(xep, "op")], ["Opla", "Nop"])


def _chay_tim_uom(ds, dich, txt, start=0, page_len=20, filters=None):
	"""Chạy `tim_uom` THẬT, chỉ thay danh mục và bảng dịch."""
	ham = [n for n in ast.parse(MA_DV).body
		if isinstance(n, ast.FunctionDef) and n.name in ("tim_uom", "_loc")]
	da_loc = {}

	def get_all(dt, filters=None, fields=None, **k):
		da_loc.update(filters or {})
		return [dict(d) for d in ds]

	f = SimpleNamespace(get_all=get_all, _=lambda s: dich.get(s, s),
		validate_and_sanitize_search_inputs=lambda h: h)
	env = dict(frappe=f, cint=lambda n: int(n or 0), loc_don_vi=loc_don_vi)
	exec(compile(ast.Module(body=ham, type_ignores=[]), "tim_don_vi.py", "exec"), env)
	return env["tim_uom"]("UOM", txt, "name", start, page_len, filters), da_loc


@ca("#520 ô chọn đơn vị: gõ Box ra Box, gõ Hộp ra cả Hộp lẫn Box")
def _tim_uom():
	ds = [{"name": "Box", "uom_name": "Box"}, {"name": "Hộp", "uom_name": "Hộp"},
		{"name": "Nos", "uom_name": "Nos"}, {"name": "Gram", "uom_name": "Gram"}]
	dich = {"Box": "Hộp", "Nos": "Số"}

	ra, _l = _chay_tim_uom(ds, dich, "Box")
	la("gõ Box ra đúng một dòng Box", ra, [["Box", "Hộp"]])

	ra, _l = _chay_tim_uom(ds, dich, "Hộp")
	la("gõ Hộp ra cả hai", sorted(x[0] for x in ra), ["Box", "Hộp"])

	ra, _l = _chay_tim_uom(ds, dich, "Nos")
	la("gõ Nos ra Nos", [x[0] for x in ra], ["Nos"])

	ra, _l = _chay_tim_uom(ds, dich, "Gram")
	la("đơn vị không có bản dịch vẫn tìm như cũ", ra, [["Gram", ""]])

	# Lọc của người gọi phải được giữ, và luôn thêm điều kiện đơn vị còn dùng.
	_ra, loc = _chay_tim_uom(ds, dich, "", filters={"must_be_whole_number": 1})
	la("giữ lọc của người gọi", loc.get("must_be_whole_number"), 1)
	la("tự thêm điều kiện còn dùng", loc.get("enabled"), 1)
	_ra, loc = _chay_tim_uom(ds, dich, "", filters={"enabled": 0})
	la("người gọi muốn xem đơn vị đã tắt thì tôn trọng", loc.get("enabled"), 0)

	ra, _l = _chay_tim_uom(ds, dich, "", start=1, page_len=2)
	la("cắt trang đúng", len(ra), 2)
