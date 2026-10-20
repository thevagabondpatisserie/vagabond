# -*- coding: utf-8 -*-
"""Kiểm thử v607: lý do tặng chọn sẵn, một nút lưu đơn tặng, số dư khách trả trước.

Ca gốc 20/10/2026:
  * Đơn #95631: cửa hàng chọn Hàng tặng, gõ lý do, bấm "Lưu phương thức thanh
    toán". Nút đó chỉ lưu phương thức, lý do mất, giám đốc bấm Duyệt thì bật
    "Không duyệt được". Các ca dưới chốt: mọi cửa lưu phương thức gặp đơn Hàng
    tặng thiếu lý do thì DỪNG, và cửa mới luu_tang lưu tất cả hoặc không gì.
  * Khách trả trước 50 triệu rồi trừ dần, các đơn bị ghi nhầm Hàng tặng. Các
    ca dưới chốt phép chia, phép cấn cũ trước, phép tính số dư, và hai hook.

Không ca nào ở đây import ban_hang (kéo requests, CI tay không không có).
Hàm của ban_hang được nạp riêng bằng cây cú pháp, cùng cách thu_su_co_290.
"""

import ast
import sys
import types
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import hang_tang as ht
from vagabond import tra_truoc_khach as tk
from vagabond import pt_thanh_toan, thu_tien

GOC = Path(__file__).resolve().parents[2]


class D(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v


class Chan(Exception):
	pass


def _nem(msg, *a, **k):
	raise Chan(msg)


def nap(tep, ten, g):
	cay = ast.parse((GOC / tep).read_text(encoding="utf-8"))
	ham = next(n for n in cay.body if isinstance(n, ast.FunctionDef) and n.name == ten)
	ham.decorator_list = []
	exec(compile(ast.Module(body=[ham], type_ignores=[]), tep, "exec"), g)
	return g[ten]


# ------------------------------------------------------- A. lý do chọn sẵn


@ca("v607 lý do tặng: bảng chọn sẵn đúng danh sách anh Việt duyệt, mỗi loại có lý do")
def _():
	la("mười tám lý do", len(ht.LY_DO_SAN), 18)
	ma = [r[0] for r in ht.LY_DO_SAN]
	la("mã không trùng", len(set(ma)), len(ma))
	for m, lo, nhan, can in ht.LY_DO_SAN:
		dung("%s thuộc loại có thật" % m, lo in ht.NHAN_LOAI)
		dung("%s cần thêm hợp lệ" % m, can in ("", "nguoi", "kol", "doi_tac", "tay"))
		dung("%s có nhãn tiếng Việt" % m, len(nhan) >= 4)
	for k, _t in ht.LOAI_TANG:
		dung("loại %s có ít nhất một lý do" % k, any(r[1] == k for r in ht.LY_DO_SAN))
		dung("loại %s có chip" % k, k in ht.CHIP_LOAI)
	la("đền bù cần người nhận", sorted({r[3] for r in ht.LY_DO_SAN if r[1] == "den_bu"}), ["nguoi"])
	la("chỉ K2 gõ tay", [r[0] for r in ht.LY_DO_SAN if r[3] == "tay"], ["K2"])
	la("không cần thêm gì", sorted(r[0] for r in ht.LY_DO_SAN if not r[3]), ["K1", "N1"])


@ca("v607 lý do tặng: bảng của bộ kiểm hành vi trùng tuyệt đối bảng máy chủ")
def _():
	src = (GOC / "khung" / "kiem_thu" / "hanh_vi" / "tang_tra_truoc_607.js").read_text(encoding="utf-8")
	for m, lo, nhan, can in ht.LY_DO_SAN:
		dung("bộ kiểm có dòng %s" % m, "['%s', '%s', '%s', '%s']" % (m, lo, nhan, can) in src)


@ca("v607 soan_ly_do: ghép nhãn với người nhận, chặn thiếu, không nhận mã lạ")
def _():
	la("V1 có người nhận", ht.soan_ly_do("V1", "Nguyễn Hoàng Việt"),
		("vip", "Tặng sinh nhật khách: Nguyễn Hoàng Việt", ""))
	la("gom khoảng trắng", ht.soan_ly_do("v1", "  Chị   Mai ")[1], "Tặng sinh nhật khách: Chị Mai")
	lo, ly, loi = ht.soan_ly_do("V1", "")
	la("thiếu người nhận thì không có câu lưu", ly, "")
	dung("câu lỗi nói rõ người nhận", "người nhận" in loi)
	la("N1 không cần thêm", ht.soan_ly_do("N1", ""), ("noi_bo", "Thử món, kiểm mẻ", ""))
	la("K1 không cần thêm", ht.soan_ly_do("K1", None)[1:], ("Từ thiện, cúng dường", ""))
	dung("K2 gõ chín ký tự bị chặn", ht.soan_ly_do("K2", "123456789")[2])
	la("K2 đủ mười ký tự", ht.soan_ly_do("K2", "Tặng chủ nhà")[:2], ("khac", "Khác: Tặng chủ nhà"))
	dung("mã lạ bị chặn", ht.soan_ly_do("Z9", "x")[2])
	dung("mã rỗng bị chặn", ht.soan_ly_do("", "x")[2])
	for m, lo, nhan, can in ht.LY_DO_SAN:
		them = "Tặng chủ nhà mặt bằng" if can else ""
		l2, ly2, loi2 = ht.soan_ly_do(m, them)
		la("%s hợp lệ" % m, loi2, "")
		la("%s không còn thiếu gì theo luật cũ" % m,
			ht.thieu_gi({"vgb_pt_thanh_toan": ht.PT_TANG, "vgb_tang_loai": l2, "vgb_tang_ly_do": ly2}), [])


@ca("v607 thieu_khi_dat_tang: chỉ xét đơn Hàng tặng, chỉ xét loại và lý do")
def _():
	la("Hàng tặng trống", ht.thieu_khi_dat_tang({"vgb_pt_thanh_toan": ht.PT_TANG}), ["ly_do", "loai"])
	la("đơn tiền mặt không xét", ht.thieu_khi_dat_tang({"vgb_pt_thanh_toan": "Tiền mặt"}), [])
	la("đủ thì không thiếu", ht.thieu_khi_dat_tang({"vgb_pt_thanh_toan": ht.PT_TANG,
		"vgb_tang_loai": "den_bu", "vgb_tang_ly_do": "Bánh hỏng, sai mẫu: Chị Mai"}), [])


@ca("v607 nguoi_dat_tang: người đổi sang Hàng tặng gần nhất, không có thì người lập")
def _():
	ls = [
		{"owner": "b@x", "data": {"changed": [["vgb_ghi_chu", "", "x"]]}},
		{"owner": "a@x", "data": {"changed": [["vgb_pt_thanh_toan", "Tiền mặt", "Hàng tặng"]]}},
	]
	la("lấy người đổi phương thức", ht.nguoi_dat_tang(ls, "chu@x"), "a@x")
	la("không có lượt đổi thì người lập", ht.nguoi_dat_tang(ls[:1], "chu@x"), "chu@x")


def _don_si(**o):
	d = D(name="SI-95631", docstatus=0, vgb_huy=0, custom_nguon="Pancake", vgb_pt_thanh_toan="Tiền mặt",
		vgb_tang_duyet="", flags=NS(), grand_total=750000)
	d.update(o)
	d.luu = []
	d.save = lambda **k: d.luu.append(dict(d))
	d.get = lambda k, mac=None: dict.get(d, k, mac)
	return d


def _goi_luu_tang(d, anh_cu=(), **kw):
	# Ảnh đính được phải hiện ra ở `_anh_cua_to` như File thật, vì từ vòng 2
	# (Codex #493 P1) `luu_tang` đếm lại ảnh SAU khi đính. Bản giả cũ trả danh
	# sách cố định nên ca "ảnh gửi kèm thì lưu" đỏ dù code đúng.
	dinh = []
	co = list(anh_cu)

	def _dinh(n, a):
		dinh.append(a)
		co.extend({"url": "/f/%s" % x.get("ten")} for x in a)
		return len(a)
	fr = NS(get_doc=lambda *a: d, throw=_nem, parse_json=lambda s: __import__("json").loads(s),
		db=NS(commit=lambda: None))
	bh = types.ModuleType("vagabond.ban_hang")
	bh._kiem_pt = lambda pt, nguon: pt
	with patch.object(ht, "frappe", fr), patch.object(ht, "_quyen", lambda: None), \
			patch.object(ht, "_anh_cua_to", lambda n: list(co)), \
			patch.object(ht, "_dinh_anh", _dinh), \
			patch.dict(sys.modules, {"vagabond.ban_hang": bh}):
		return ht.luu_tang("SI-95631", **kw), dinh


@ca("v607 luu_tang: một lần lưu cả phương thức, loại, lý do, mã lý do")
def _():
	d = _don_si()
	kq, _dinh = _goi_luu_tang(d, ma_ly_do="V1", them="Chị Mai", ghi_chu="ghi chú")
	la("lưu đúng một lần", len(d.luu), 1)
	s = d.luu[0]
	la("bốn ô cùng một lần lưu",
		[s["vgb_pt_thanh_toan"], s["vgb_tang_loai"], s["vgb_tang_ly_do"], s["vgb_tang_ma_ly_do"], s["vgb_ghi_chu"]],
		["Hàng tặng", "vip", "Tặng sinh nhật khách: Chị Mai", "V1", "ghi chú"])
	la("không còn thiếu", kq["thieu"], [])


@ca("v607 luu_tang: thiếu thì KHÔNG lưu gì, kể cả phương thức")
def _():
	for kw, tim in (({"ma_ly_do": "V1", "them": ""}, "người nhận"),
			({"ma_ly_do": "", "them": "x"}, "lý do"),
			({"ma_ly_do": "K2", "them": "ngắn"}, "10 ký tự")):
		d = _don_si()
		try:
			_goi_luu_tang(d, **kw)
		except Chan as e:
			dung("câu lỗi nói rõ %s" % tim, tim in str(e))
		else:
			dung("phải chặn %r" % kw, False)
		la("không lưu %r" % kw, d.luu, [])
		la("phương thức giữ nguyên %r" % kw, d.vgb_pt_thanh_toan, "Tiền mặt")


@ca("v607 luu_tang: đền bù phải có ảnh, ảnh cũ trên đơn hay ảnh gửi kèm đều được")
def _():
	d = _don_si()
	try:
		_goi_luu_tang(d, ma_ly_do="D3", them="Chị Mai")
	except Chan as e:
		dung("báo thiếu ảnh", "ẢNH" in str(e))
	else:
		dung("phải chặn đền bù không ảnh", False)
	la("không lưu", d.luu, [])
	d = _don_si()
	_goi_luu_tang(d, anh_cu=[{"url": "/a.jpg"}], ma_ly_do="D3", them="Chị Mai")
	la("có ảnh cũ thì lưu", len(d.luu), 1)
	d = _don_si()
	_kq, dinh = _goi_luu_tang(d, ma_ly_do="D3", them="Chị Mai",
		anh='[{"ten": "banh.jpg", "noi_dung": "data:image/jpeg;base64,AAA"}]')
	la("ảnh gửi kèm thì lưu và đính", (len(d.luu), len(dinh)), (1, 1))


@ca("v607 luu_tang: đơn bị từ chối lưu lại là xin duyệt mới; đơn đã ghi sổ không đụng")
def _():
	d = _don_si(vgb_tang_duyet=ht.TT_TU_CHOI, vgb_tang_y_kien="thiếu", vgb_tang_dau_van="x")
	_goi_luu_tang(d, ma_ly_do="N1")
	la("về Chờ duyệt, xoá ý kiến cũ", [d.vgb_tang_duyet, d.vgb_tang_y_kien, d.vgb_tang_dau_van], [ht.TT_CHO, "", ""])
	d = _don_si(docstatus=1)
	try:
		_goi_luu_tang(d, ma_ly_do="N1")
	except Chan:
		pass
	else:
		dung("đơn đã ghi sổ phải chặn", False)
	la("không lưu đơn đã ghi sổ", d.luu, [])


def _g_ban_hang(d, ghi):
	"""Bộ toàn cục tối thiểu để chạy THẬT bốn cửa lưu phương thức của ban_hang."""
	g = dict(
		frappe=NS(throw=_nem, db=NS(commit=lambda: ghi.append("commit"),
			get_value=lambda *a, **k: d, set_value=lambda *a, **k: ghi.append("set")),
			get_doc=lambda *a: d),
		_kiem_quyen_ban=lambda: None, _kiem_quyen_doc_luu_don=lambda: None,
		_pos_lay=lambda n: d, _kiem_pt=lambda p, n: p,
		quyen_quay=NS(them_giam_gia=lambda *a: False),
		luat_thanh_toan=NS(ma_can_ghi=lambda *a: ""),
		_chuan_ma_tham_chieu=lambda *a, **k: "", _kiem_trung_ma=lambda *a, **k: None,
		_nan_pt_tai_cho=lambda si: None, _giam_tu_diem=lambda si: 0,
		_chuan_bi_ghi_so=lambda *a, **k: None,
		flt=float, cint=int,
	)
	# Hàng rào THẬT của ban_hang, không phải bản giả: ca kiểm phải chạy đúng
	# cái cửa hàng chặn ngoài site.
	nap("ban_hang.py", "_chan_tang_thieu", g)
	return g


@ca("v607 ca #95631: nút Lưu phương thức (pos_chot) gặp Hàng tặng thiếu lý do thì dừng, không lưu")
def _():
	for ten, goi in (
		("pos_chot", lambda f: f("SI-95631", pt="Hàng tặng")),
		("pos_luu_don", lambda f: f("SI-95631", pt="Hàng tặng")),
		("luu_thanh_toan", lambda f: f("SI-95631", pt="Hàng tặng")),
	):
		ghi = []
		d = _don_si()
		d.save = lambda **k: ghi.append("save")
		g = _g_ban_hang(d, ghi)
		f = nap("ban_hang.py", ten, g)
		try:
			goi(f)
		except Chan as e:
			dung("%s chỉ đúng nút cần bấm" % ten, "Lưu và gửi giám đốc duyệt" in str(e))
		else:
			dung("%s phải chặn" % ten, False)
		la("%s không lưu, không commit" % ten, ghi, [])


@ca("v607 ca #95631: đơn Hàng tặng ĐÃ có lý do thì các cửa cũ vẫn lưu bình thường")
def _():
	for ten in ("pos_chot", "pos_luu_don", "luu_thanh_toan"):
		ghi = []
		d = _don_si(vgb_tang_loai="vip", vgb_tang_ly_do="Tặng sinh nhật khách: Chị Mai")
		d.save = lambda **k: ghi.append("save")
		f = nap("ban_hang.py", ten, _g_ban_hang(d, ghi))
		f("SI-95631", pt="Hàng tặng")
		dung("%s lưu" % ten, "save" in ghi)
	ghi = []
	d = _don_si()
	d.save = lambda **k: ghi.append("save")
	nap("ban_hang.py", "pos_chot", _g_ban_hang(d, ghi))("SI-95631", pt="Tiền mặt")
	dung("phương thức khác không bị chặn", "save" in ghi)


# --------------------------------------------------- B. số dư trả trước


@ca("v607 số dư: phương thức mới khai đúng nhóm tiền về ngày khác, không sinh phiếu thu")
def _():
	d = [x for x in pt_thanh_toan.MAC_DINH if x["ten"] == tk.PT_SO_DU]
	la("có đúng một dòng", len(d), 1)
	la("nhóm tiền về ngày khác", d[0]["tien_ve"], pt_thanh_toan.TIEN_NGAY_KHAC)
	la("hiện ở quầy và online", (d[0]["quay"], d[0]["online"]), (1, 1))
	dung("tên bị khoá", tk.PT_SO_DU in pt_thanh_toan.TEN_KHOA)
	dung("không sinh phiếu thu", thu_tien.khong_sinh_phieu(tk.PT_SO_DU))
	dung("không phải công nợ", not thu_tien.la_cong_no(tk.PT_SO_DU))
	dung("khác tên với Trả trước của đặt bánh", tk.PT_SO_DU != "Trả trước")


@ca("v607 số dư: phần trả bằng số dư theo bảng dòng hoặc theo phương thức chính")
def _():
	la("cả đơn", tk.phan_tra_truoc(tk.PT_SO_DU, [], 1250000), 1250000.0)
	la("phương thức khác", tk.phan_tra_truoc("Tiền mặt", [], 1250000), 0.0)
	dong = [{"pt": tk.PT_SO_DU, "so_tien": 300000}, {"pt": "Chuyển khoản", "so_tien": 950000}]
	la("chỉ dòng số dư", tk.phan_tra_truoc("Chuyển khoản", dong, 1250000), 300000.0)
	la("bảng dòng thắng phương thức chính", tk.phan_tra_truoc(tk.PT_SO_DU, [{"pt": "Tiền mặt", "so_tien": 1}], 1), 0.0)


@ca("v607 số dư: cấn khoản nạp cũ trước, thiếu thì báo đúng số thiếu")
def _():
	nguon = [{"loai": "PE", "ten": "B", "con": 300000, "ngay": "2026-10-02"},
		{"loai": "JE", "ten": "A", "con": 500000, "ngay": "2026-09-12"},
		{"loai": "PE", "ten": "C", "con": 0, "ngay": "2026-09-01"}]
	la("cũ trước, bỏ khoản hết tiền", tk.phan_bo(600000, nguon),
		([{"loai": "JE", "ten": "A", "so": 500000.0}, {"loai": "PE", "ten": "B", "so": 100000.0}], 0.0))
	la("thiếu", tk.phan_bo(900000, nguon)[1], 100000.0)
	la("không cần gì", tk.phan_bo(0, nguon), ([], 0.0))


@ca("v607 số dư: dùng được = chưa cấn trừ giữ chỗ; tạm tính thêm phiếu chờ ghi sổ")
def _():
	nap_ = [{"docstatus": 1, "tong": 50000000, "con": 48987500}, {"docstatus": 0, "tong": 2000000, "con": 2000000}]
	s = tk.tong_so(nap_, 1012500)
	la("bảng số", [s["da_nap"], s["da_tru"], s["con_chua_can"], s["cho_ghi_so"], s["giu_cho"], s["kha_dung"], s["kha_dung_tam"]],
		[50000000, 1012500, 48987500, 2000000, 1012500, 47975000, 49975000])
	la("không âm", tk.tong_so([], 5)["kha_dung"], 0.0)


@ca("v607 số dư: chia đơn khi thiếu, bắt chọn phương thức phần còn lại")
def _():
	la("đủ", tk.chia_don(1250000, 5000000, ""), ([{"pt": tk.PT_SO_DU, "so_tien": 1250000.0}], ""))
	la("thiếu có chọn", tk.chia_don(1250000, 300000, "Chuyển khoản")[0],
		[{"pt": tk.PT_SO_DU, "so_tien": 300000.0}, {"pt": "Chuyển khoản", "so_tien": 950000.0}])
	dung("thiếu không chọn thì lỗi", tk.chia_don(1250000, 300000, "")[1])
	dung("không cho phần còn lại cũng là số dư", tk.chia_don(1250000, 300000, tk.PT_SO_DU)[1])
	dung("hết số dư thì lỗi", tk.chia_don(1250000, 0, "Tiền mặt")[1])


@ca("v607 nạp: bắt ảnh với nguồn qua tài khoản, bắt quầy với tiền mặt và thẻ")
def _():
	la("chuyển khoản không ảnh", bool(tk.kiem_nap(1000000, "ck_cty", 0, "")), True)
	la("chuyển khoản có ảnh", tk.kiem_nap(1000000, "ck_cty", 1, ""), "")
	la("tiền mặt không quầy", bool(tk.kiem_nap(1000000, "tien_mat", 0, "")), True)
	la("tiền mặt có quầy", tk.kiem_nap(1000000, "tien_mat", 0, "TCV"), "")
	la("thẻ cần ảnh bill và quầy", [bool(tk.kiem_nap(1000000, "the_payoo", 0, "TCV")),
		bool(tk.kiem_nap(1000000, "the_payoo", 1, "")), tk.kiem_nap(1000000, "the_payoo", 1, "TCV")], [True, True, ""])
	la("Giám đốc thu hộ cần ảnh", bool(tk.kiem_nap(50000000, "gd_thu_ho", 0, "")), True)
	la("số tiền quá nhỏ", bool(tk.kiem_nap(5000, "tien_mat", 0, "TCV")), True)
	la("nguồn lạ", bool(tk.kiem_nap(1000000, "zzz", 1, "TCV")), True)


def _si_tt(**o):
	d = D(name="SI-1", docstatus=0, vgb_huy=0, customer="KL040476", customer_name="Mỹ Dung",
		vgb_pt_thanh_toan=tk.PT_SO_DU, grand_total=1250000, vgb_thanh_toan_nhieu=[], posting_date="2026-10-20")
	d.update(o)
	d.get = lambda k, mac=None: dict.get(d, k, mac)
	return d


@ca("v607 hook lưu: chặn khách lẻ và chặn thiếu số dư, bỏ qua lượt lưu lại không đổi gì")
def _():
	kh = types.ModuleType("vagabond.khach_hang")
	kh.la_khach_gop = lambda c: str(c).startswith("Khách lẻ")
	fr = NS(throw=_nem)

	def chay(d, so_du, cu=None):
		d.get_doc_before_save = lambda: cu
		with patch.object(tk, "frappe", fr), patch.object(tk, "so_du_khach", lambda k, tru=None: so_du), \
				patch.dict(sys.modules, {"vagabond.khach_hang": kh}):
			tk.kiem_khi_luu(d)

	du = tk.tong_so([{"docstatus": 1, "tong": 5000000, "con": 5000000}], 0)
	chay(_si_tt(), du)
	for d, tim in ((_si_tt(customer="Khách lẻ Online"), "đúng khách"),
			(_si_tt(grand_total=9000000), "chỉ còn")):
		try:
			chay(d, du)
		except Chan as e:
			dung("chặn: %s" % tim, tim in str(e))
		else:
			dung("phải chặn: %s" % tim, False)
	# Nhịp đồng bộ lưu lại đơn không đổi gì: KHÔNG chặn dù số dư đã hết.
	cu = _si_tt(grand_total=9000000)
	chay(_si_tt(grand_total=9000000), tk.tong_so([], 0), cu=cu)
	# Đơn không trả bằng số dư: không đụng gì.
	chay(_si_tt(vgb_pt_thanh_toan="Tiền mặt", customer="Khách lẻ Online"), tk.tong_so([], 0))


@ca("v607 hook ghi sổ: chỉ cấn phiếu nạp mang cờ, cũ trước, đủ số; thiếu thì chặn")
def _():
	adv = [
		D(reference_type="Payment Entry", reference_name="PE-COC", reference_row=None, amount=900000, paid_to="131"),
		D(reference_type="Payment Entry", reference_name="PE-NAP2", reference_row=None, amount=800000, paid_to="131"),
		D(reference_type="Journal Entry", reference_name="JE-NAP1", reference_row="r1", amount=500000),
	]
	ngay = {"PE-COC": "2026-09-01", "PE-NAP2": "2026-10-02", "JE-NAP1": "2026-09-12"}
	nap_ = [{"loai": "Payment Entry", "name": "PE-NAP2", "docstatus": 1},
		{"loai": "Journal Entry", "name": "JE-NAP1", "docstatus": 1},
		{"loai": "Payment Entry", "name": "PE-CHO", "docstatus": 0}]
	fr = NS(throw=_nem, db=NS(get_value=lambda dt, n, f: ngay[n]))

	def chay(d):
		d.get_advance_entries = lambda include_unallocated=True: adv
		d.advances = []
		d.set = lambda k, v: d.__setitem__(k, list(v))
		d.append = lambda k, v: d[k].append(v)
		d.tinh = 0
		d.calculate_taxes_and_totals = lambda: d.__setitem__("tinh", d.tinh + 1)
		with patch.object(tk, "frappe", fr), patch.object(tk, "cac_phieu_nap", lambda k: nap_), \
				patch.object(tk, "so_du_khach", lambda k, tru=None: tk.tong_so([], 0)):
			tk.can_tru_khi_ghi_so(d)
		return d

	d = chay(_si_tt())
	la("cấn JE cũ trước rồi PE, bỏ phiếu cọc không mang cờ",
		[(a["reference_name"], a["allocated_amount"]) for a in d.advances],
		[("JE-NAP1", 500000.0), ("PE-NAP2", 750000.0)])
	la("tính lại tổng một lần", d.tinh, 1)
	try:
		chay(_si_tt(grand_total=2000000))
	except Chan as e:
		dung("báo thiếu", "Chưa đủ" in str(e) or "cần trừ" in str(e))
	else:
		dung("thiếu phải chặn", False)
	d = chay(_si_tt(vgb_pt_thanh_toan="Tiền mặt"))
	la("đơn không trả bằng số dư thì không đụng", (d.advances, d.tinh), ([], 0))


@ca("v607 chốt ca: tiền nạp tại quầy vào két, tính cả phiếu chờ ghi sổ")
def _():
	loc = {}

	def ga(dt, filters=None, fields=None, limit_page_length=None):
		loc.update(filters)
		return [D(mode_of_payment="Tiền mặt", paid_amount=2000000), D(mode_of_payment="Tiền mặt", paid_amount=500000),
			D(mode_of_payment="Thẻ - Payoo", paid_amount=1000000)]

	with patch.object(tk, "frappe", NS(get_all=ga)):
		r = tk.thu_nap_tai_quay("tcv", "2026-10-20 07:00:00", "2026-10-20 22:00:00")
	la("cộng theo phương thức", r, {"Tiền mặt": 2500000.0, "Thẻ - Payoo": 1000000.0})
	la("lọc đúng quầy, cờ nạp, chưa huỷ", [loc["vgb_quay"], loc[tk.CO], loc["docstatus"]], ["TCV", 1, ["<", 2]])
	with patch.object(tk, "frappe", NS(get_all=ga)):
		la("không có quầy thì không đọc", tk.thu_nap_tai_quay("", "a", "b"), {})


@ca("v607 hook đăng ký đúng chỗ: kiểm khi lưu sau phương thức chính, cấn khi ghi sổ")
def _():
	from vagabond import hooks

	si = hooks.doc_events["Sales Invoice"]
	v = si["validate"]
	dung("có hook lưu", "vagabond.tra_truoc_khach.kiem_khi_luu" in v)
	dung("sau dat_pt_chinh", v.index("vagabond.tra_truoc_khach.kiem_khi_luu") > v.index("vagabond.thanh_toan_nhieu.dat_pt_chinh"))
	b = si["before_submit"]
	dung("có hook ghi sổ", "vagabond.tra_truoc_khach.can_tru_khi_ghi_so" in b)
	dung("sau kiểm dòng thanh toán", b.index("vagabond.tra_truoc_khach.can_tru_khi_ghi_so") > b.index("vagabond.thanh_toan_nhieu.kiem_truoc_ghi_so"))


# ------------------------------------------- Codex #493 P1: ảnh đính hỏng


def _goi_nap(nguon, so_dinh, anh='[{"ten": "ck.jpg", "noi_dung": "data:image/jpeg;base64,AAA"}]'):
	"""Chạy THẬT tao_phieu_nap, chỉ thay phần chạm Frappe; trả (lỗi, các lần commit)."""
	ghi = []

	class Phieu(D):
		def append(self, k, v):
			self.setdefault(k, []).append(v)

		def set(self, k, v):
			self[k] = v

	def moi(dt):
		p = Phieu(doctype=dt, name="NAP-1", flags=NS())
		p.insert = lambda **k: ghi.append("insert")
		p.setup_party_account_field = lambda: None
		p.set_missing_values = lambda: None
		return p

	fr = NS(throw=_nem, new_doc=moi, generate_hash=lambda length=6: "abc",
		parse_json=lambda s: __import__("json").loads(s),
		db=NS(exists=lambda *a: True, commit=lambda: ghi.append("commit")))
	kh = types.ModuleType("vagabond.khach_hang")
	kh.la_khach_gop = lambda c: False

	class Nang:
		def __enter__(self):
			return "nv@x"

		def __exit__(self, *a):
			return False

	from vagabond import thu_tien as tt_mod
	lib = types.ModuleType("vagabond.lib")
	lib.cfg = lambda: {"tk_gd_thu_ho": "1388 - GD"}
	pa = types.ModuleType("erpnext.accounts.party")
	pa.get_party_account = lambda *a: "131 - KH"
	with patch.object(tk, "frappe", fr), patch.object(tk, "_quyen", lambda: None), \
			patch.object(tk, "_cong_ty", lambda: "CTY"), patch.object(tk, "nowdate", lambda: "2026-10-20"), \
			patch.object(tk, "_dinh_tep", lambda dt, n, a: so_dinh), \
			patch.object(tt_mod, "nang_quyen_lap_phieu", Nang), patch.object(tt_mod, "_giu_chu", lambda *a: None), \
			patch.object(tt_mod, "tk_tien_thu", lambda c, p: ("1111 - TM", None)), \
			patch.dict(sys.modules, {"vagabond.khach_hang": kh, "vagabond.lib": lib, "erpnext.accounts.party": pa}):
		fr.db.exists = lambda *a: True
		tk.frappe.db.exists = lambda *a: True
		try:
			kq = tk.tao_phieu_nap("KL040476", 50000000, nguon, anh=anh, quay="TCV")
		except Chan as e:
			return str(e), ghi
	return kq, ghi


@ca("v607 Codex #493 P1: nạp bắt ảnh mà không đính được ảnh nào thì không commit, báo lập lại")
def _():
	for nguon in ("ck_cty", "gd_thu_ho", "the_payoo"):
		kq, ghi = _goi_nap(nguon, 0)
		dung("%s báo lỗi" % nguon, isinstance(kq, str) and "Không đính được ảnh" in kq)
		dung("%s không commit" % nguon, "commit" not in ghi)
		kq, ghi = _goi_nap(nguon, 1)
		dung("%s đính được thì lập" % nguon, isinstance(kq, dict) and kq.get("ok") == 1)
		dung("%s đính được thì commit" % nguon, "commit" in ghi)
	kq, ghi = _goi_nap("tien_mat", 0, anh="")
	dung("tiền mặt không bắt ảnh vẫn lập", isinstance(kq, dict) and "commit" in ghi)


@ca("v607 Codex #493 P1: đơn đền bù gửi ảnh mà đính hỏng thì không commit")
def _():
	d = _don_si()
	ghi = []
	fr = NS(get_doc=lambda *a: d, throw=_nem, parse_json=lambda s: __import__("json").loads(s),
		db=NS(commit=lambda: ghi.append("commit")))
	bh = types.ModuleType("vagabond.ban_hang")
	bh._kiem_pt = lambda pt, nguon: pt
	with patch.object(ht, "frappe", fr), patch.object(ht, "_quyen", lambda: None), \
			patch.object(ht, "_anh_cua_to", lambda n: []), patch.object(ht, "_dinh_anh", lambda n, a: 0), \
			patch.dict(sys.modules, {"vagabond.ban_hang": bh}):
		try:
			ht.luu_tang("SI-95631", ma_ly_do="D3", them="Chị Mai",
				anh='[{"ten": "banh.jpg", "noi_dung": "data:image/jpeg;base64,AAA"}]')
		except Chan as e:
			dung("báo không đính được ảnh", "Không đính được ảnh" in str(e))
		else:
			dung("phải chặn", False)
	la("không commit", ghi, [])
