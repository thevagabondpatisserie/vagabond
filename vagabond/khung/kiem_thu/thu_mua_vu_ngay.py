"""Kiem thu bang CO THE BAN theo tung ngay cua mua vu (v274).

Bang nay la phep cua vagabond/kiem_banh.py bung sang mua vu, tung cot mot:

    Ton dau + Bep lam - Da dat - Phat sinh - Cho chot - Kenh khac = Co the ban

Khac mot cho: ton dau ngay khong ai go tay, may CUON tu ngay dau mua. Cac ca
duoi day soi dung cho cuon do, cong voi phep ghep nguoc cua hop.

KHONG nap Frappe that. Moi ca chay duoc voi python3 tran, khong can requests,
khong can site.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la

# Mot mua vu thu nho, du hai hop va ba banh le, giong hinh mua Trung thu that.
DM = [
	{"ma_hop": "HOPA", "ma_banh": "LE1", "so_luong": 2},
	{"ma_hop": "HOPA", "ma_banh": "LE2", "so_luong": 2},
	{"ma_hop": "HOPB", "ma_banh": "LE3", "so_luong": 4},
]


def _mv():
	from vagabond import mua_vu

	return mua_vu


# ------------------------------------------------------- day_ngay


@ca("day_ngay() dựng đúng dãy ngày liên tục và chặn được dãy quá dài")
def _():
	mv = _mv()
	la("ba ngày", mv.day_ngay("2026-09-01", "2026-09-03"),
		["2026-09-01", "2026-09-02", "2026-09-03"])
	la("một ngày", mv.day_ngay("2026-09-01", "2026-09-01"), ["2026-09-01"])
	la("ngày cuối trước ngày đầu thì rỗng", mv.day_ngay("2026-09-05", "2026-09-01"), [])
	la("bắc cầu qua tháng", mv.day_ngay("2026-08-30", "2026-09-02"),
		["2026-08-30", "2026-08-31", "2026-09-01", "2026-09-02"])
	dai = mv.day_ngay("2020-01-01", "2026-09-01", toi_da=5)
	la("cắt còn đúng trần", len(dai), 5)
	la("giữ lại phần CUỐI chứ không phải phần đầu", dai[-1], "2026-09-01")


# --------------------------------------------------- cuon_ton_theo_ngay


@ca("Tồn cuối ngày hôm trước chảy sang thành tồn đầu ngày hôm sau")
def _():
	mv = _mv()
	ngay = ["2026-09-01", "2026-09-02", "2026-09-03"]
	ra = mv.cuon_ton_theo_ngay(
		ngay,
		{"LE1": 100},
		{("LE1", "2026-09-02"): 50},
		{("LE1", "2026-09-01"): {"da_dat": 30}},
		[],
	)
	la("ngày 1 tồn đầu là số mở sổ", ra["2026-09-01"]["LE1"]["ton_dau"], 100)
	la("ngày 1 bán được 100 trừ 30", ra["2026-09-01"]["LE1"]["co_the_ban"], 70)
	la("ngày 2 tồn đầu bằng còn lại ngày 1", ra["2026-09-02"]["LE1"]["ton_dau"], 70)
	la("ngày 2 bếp làm thêm 50", ra["2026-09-02"]["LE1"]["them"], 50)
	la("ngày 2 bán được 70 cộng 50", ra["2026-09-02"]["LE1"]["co_the_ban"], 120)
	la("ngày 3 không ai đặt, số giữ nguyên", ra["2026-09-03"]["LE1"]["co_the_ban"], 120)


@ca("Đủ bốn cột trừ: đã đặt, phát sinh, chờ chốt, kênh khác")
def _():
	mv = _mv()
	ra = mv.cuon_ton_theo_ngay(
		["2026-09-01"],
		{"LE1": 100},
		{},
		{("LE1", "2026-09-01"): {
			"da_dat": 10, "phat_sinh": 5, "cho_chot": 3, "don_khac": 2}},
		[],
	)
	o = ra["2026-09-01"]["LE1"]
	la("đã đặt", o["da_dat"], 10)
	la("phát sinh", o["phat_sinh"], 5)
	la("chờ chốt", o["cho_chot"], 3)
	la("kênh khác", o["don_khac"], 2)
	la("100 trừ hết bốn cột", o["co_the_ban"], 80)


@ca("Bán quá tay thì số ÂM, không được ép về 0")
def _():
	mv = _mv()
	ra = mv.cuon_ton_theo_ngay(
		["2026-09-01", "2026-09-02"],
		{"LE1": 10},
		{},
		{("LE1", "2026-09-01"): {"da_dat": 25}},
		[],
	)
	la("âm 15 chứ không phải 0", ra["2026-09-01"]["LE1"]["co_the_ban"], -15)
	la("số âm chảy sang ngày sau", ra["2026-09-02"]["LE1"]["ton_dau"], -15)


@ca("Bán một hộp ăn ruột của CHÍNH ngày bán, không ăn của ngày khác")
def _():
	mv = _mv()
	ngay = ["2026-09-01", "2026-09-02"]
	ra = mv.cuon_ton_theo_ngay(
		ngay,
		{"HOPA": 50, "LE1": 100, "LE2": 100},
		{},
		{("HOPA", "2026-09-02"): {"da_dat": 10}},
		DM,
	)
	la("ngày 1 chưa bán hộp nào, ruột nguyên", ra["2026-09-01"]["LE1"]["trong_hop"], 0)
	la("ngày 1 LE1 còn nguyên 100", ra["2026-09-01"]["LE1"]["co_the_ban"], 100)
	la("ngày 2 bán 10 hộp ăn 20 cái LE1", ra["2026-09-02"]["LE1"]["trong_hop"], 20)
	la("ngày 2 LE1 còn 80", ra["2026-09-02"]["LE1"]["co_the_ban"], 80)
	la("ngày 2 LE2 cũng bị ăn 20", ra["2026-09-02"]["LE2"]["co_the_ban"], 80)
	la("LE3 không nằm trong HOPA nên không đụng tới",
		ra["2026-09-02"].get("LE3", {}).get("co_the_ban", 0), 0)
	la("vỏ hộp còn 40", ra["2026-09-02"]["HOPA"]["co_the_ban"], 40)
	la("dòng hộp không tự ăn chính nó", ra["2026-09-02"]["HOPA"]["trong_hop"], 0)


@ca("Chờ chốt của hộp cũng ăn ruột, y như đã đặt")
def _():
	mv = _mv()
	ra = mv.cuon_ton_theo_ngay(
		["2026-09-01"],
		{"HOPA": 50, "LE1": 100, "LE2": 100},
		{},
		{("HOPA", "2026-09-01"): {"cho_chot": 5, "don_khac": 5}},
		DM,
	)
	la("5 chờ chốt cộng 5 kênh khác là 10 hộp, ăn 20 ruột",
		ra["2026-09-01"]["LE1"]["trong_hop"], 20)


@ca("Vỏ hộp nhà in giao giữa mùa vào đúng ngày về, không vào sớm hơn")
def _():
	mv = _mv()
	ra = mv.cuon_ton_theo_ngay(
		["2026-09-01", "2026-09-02", "2026-09-03"],
		{},
		{("HOPB", "2026-09-02"): 300},
		{},
		DM,
	)
	la("ngày 1 chưa có vỏ nào", ra["2026-09-01"]["HOPB"]["co_the_ban"], 0)
	la("ngày 2 vỏ về 300", ra["2026-09-02"]["HOPB"]["them"], 300)
	la("ngày 2 còn 300", ra["2026-09-02"]["HOPB"]["co_the_ban"], 300)
	la("ngày 3 tồn đầu là 300", ra["2026-09-03"]["HOPB"]["ton_dau"], 300)


@ca("Danh sách ngày rỗng thì trả bảng rỗng, không nổ")
def _():
	mv = _mv()
	la("rỗng", mv.cuon_ton_theo_ngay([], {"LE1": 5}, {}, {}, DM), {})


# --------------------------------------------------------- ghep_theo_ngay


@ca("Hộp lấy số NHỎ HƠN giữa vỏ hộp còn và ruột ghép được")
def _():
	mv = _mv()
	ra = mv.cuon_ton_theo_ngay(
		["2026-09-01"], {"HOPA": 300, "LE1": 100, "LE2": 60}, {}, {}, DM
	)
	o = mv.ghep_theo_ngay(ra["2026-09-01"], DM)
	la("LE2 chỉ đủ 30 hộp nên ghép được 30", o["HOPA"]["ghep_duoc"], 30)
	la("vỏ 300 nhưng ruột 30, bán được thật là 30", o["HOPA"]["con_thuc_te"], 30)
	la("cột vỏ hộp vẫn giữ nguyên 300 để nhìn ra chỗ nghẽn",
		o["HOPA"]["co_the_ban"], 300)
	la("HOPA là hộp", o["HOPA"]["la_hop"], 1)
	la("LE1 không phải hộp", o["LE1"]["la_hop"], 0)
	la("bánh lẻ thì bán được thật bằng chính nó", o["LE1"]["con_thuc_te"], 100)


@ca("Hộp chưa khai định mức ruột thì phải bật cờ cảnh báo")
def _():
	mv = _mv()
	dm = [{"ma_hop": "HOPA", "ma_banh": "LE1", "so_luong": 2}]
	ra = mv.cuon_ton_theo_ngay(["2026-09-01"], {"HOPA": 20, "HOPB": 20}, {}, {}, dm)
	# HOPB khong co trong dinh muc nen khong phai hop trong bang nay.
	o = mv.ghep_theo_ngay(ra["2026-09-01"], dm)
	la("HOPA có ràng buộc nên không bật cờ", o["HOPA"]["ruot_khong_rang_buoc"], 0)
	la("HOPB không nằm trong định mức nên coi như bánh lẻ", o["HOPB"]["la_hop"], 0)


@ca("Ruột mang cờ khong_tran bị bỏ khỏi phép ghép, không kéo cả hộp về 0")
def _():
	mv = _mv()
	# LE2 la banh 80g chi lam theo hop, khong co lo rieng nen con 0.
	ra = mv.cuon_ton_theo_ngay(
		["2026-09-01"], {"HOPA": 300, "LE1": 100, "LE2": 0}, {}, {}, DM
	)
	khong = mv.ghep_theo_ngay(ra["2026-09-01"], DM)
	la("không khai cờ thì LE2 kéo hộp về 0", khong["HOPA"]["con_thuc_te"], 0)

	ra2 = mv.cuon_ton_theo_ngay(
		["2026-09-01"], {"HOPA": 300, "LE1": 100, "LE2": 0}, {}, {}, DM
	)
	co = mv.ghep_theo_ngay(ra2["2026-09-01"], DM, {"LE2"})
	la("khai cờ rồi thì chỉ còn LE1 nói lên, 100 chia 2 là 50",
		co["HOPA"]["ghep_duoc"], 50)
	la("bán được thật là 50 chứ không phải 0", co["HOPA"]["con_thuc_te"], 50)


# ------------------------------------------------- tach Phat sinh khoi Da dat


@ca("_ngay_tao() đổi múi giờ trước khi cắt ngày, đơn nửa đêm không xếp nhầm")
def _():
	mv = _mv()
	la("UTC 17h30 ngày 19 là 0h30 ngày 20 giờ Việt Nam",
		mv._ngay_tao({"inserted_at": "2026-09-19T17:30:00Z"}), "2026-09-20")
	la("UTC 09h00 vẫn trong cùng ngày",
		mv._ngay_tao({"inserted_at": "2026-09-20T09:00:00Z"}), "2026-09-20")
	la("có sẵn múi giờ Việt Nam thì giữ nguyên",
		mv._ngay_tao({"inserted_at": "2026-09-20T08:00:00+07:00"}), "2026-09-20")
	la("thiếu ô thì trả rỗng", mv._ngay_tao({}), "")
	la("rác không làm sập", mv._ngay_tao({"inserted_at": "khong-phai-ngay"}), "")


def _don(ma, sl, ngay_giao, ngay_tao, tt=1, khach="Khach A"):
	return {
		"status": tt,
		"estimate_delivery_date": ngay_giao,
		"inserted_at": ngay_tao,
		"bill_full_name": khach,
		"items": [{"quantity": sl, "variation_info": {"display_id": ma, "name": "Banh " + ma}}],
	}


@ca("_dem() tách Phát sinh khỏi Đã đặt đúng như màn kiểm bánh hàng ngày")
def _():
	mv = _mv()
	dons = [
		# Tao tu hom truoc, giao 20/09 -> DA DAT
		_don("BASS001", 10, "2026-09-20", "2026-09-18T03:00:00Z"),
		# Tao dung 20/09, giao 20/09 -> PHAT SINH
		_don("BASS001", 4, "2026-09-20", "2026-09-20T03:00:00Z", khach="Khach B"),
		# Trang thai Moi -> CHO CHOT, khong bao gio la phat sinh
		_don("BASS001", 3, "2026-09-20", "2026-09-20T04:00:00Z", tt=0, khach="Khach C"),
		# Da huy -> khong dem
		_don("BASS001", 99, "2026-09-20", "2026-09-20T04:00:00Z", tt=6),
	]
	_chot, _cho, theo_ngay, _ten, _hinh = mv._dem(dons)
	o = theo_ngay[("BASS001", "2026-09-20")]
	la("tổng đã chốt là 14, giữ nguyên nghĩa cũ", o["chot"], 14)
	la("trong đó phát sinh 4", o["phat_sinh"], 4)
	la("đã đặt là 14 trừ 4", o["chot"] - o["phat_sinh"], 10)
	la("chờ chốt 3", o["cho"], 3)
	la("tên khách phát sinh tách riêng", o["khach_ps"], ["Khach B"])
	dung("khách chờ nằm trong danh sách khách chung", "Khach C" in o["khach"])


@ca("Đơn huỷ và đơn xoá không lọt vào bảng theo ngày")
def _():
	mv = _mv()
	dons = [
		_don("BASS001", 5, "2026-09-20", "2026-09-19T03:00:00Z", tt=6),
		_don("BASS001", 7, "2026-09-20", "2026-09-19T03:00:00Z", tt=7),
	]
	_c, _ch, theo_ngay, _t, _h = mv._dem(dons)
	la("không sinh dòng nào", theo_ngay, {})


@ca("Mã không thuộc mùa vụ bị loại khỏi phép đếm")
def _():
	mv = _mv()
	dons = [_don("PHIGIAO01", 5, "2026-09-20", "2026-09-19T03:00:00Z")]
	_c, _ch, theo_ngay, _t, _h = mv._dem(dons)
	la("không đếm mã ngoài tiền tố", theo_ngay, {})


# --------------------------------------- o San xuat KHONG duoc nuot so go tay


@ca("Ô Sản xuất là TỔNG hai nguồn, bếp nhập theo ngày không nuốt số gõ tay")
def _():
	import inspect

	from vagabond.vagabond.doctype.vagabond_mua_vu import vagabond_mua_vu

	# Bo dong ghi chu truoc khi soi. Chinh ham nay CO nhac lai cau lenh cu
	# trong phan giai thich vi sao no bi bo, va soi ca dong ghi chu thi ca kiem
	# bao hong trong khi ma that da dung - dung cai bay da mat cong mot lan
	# hom 21/08 voi chuoi "chua khai dinh muc ruot".
	nguon = "\n".join(
		d for d in inspect.getsource(vagabond_mua_vu.VagabondMuaVu.validate).split("\n")
		if not d.strip().startswith("#")
	)
	dung("không còn phép thay thế thẳng ô Sản xuất bằng tổng bếp nhập",
		"d.san_xuat = bep[d.ma_hang]" not in nguon)
	dung("phải cộng sx_dau_mua với tổng bếp nhập",
		"d.san_xuat = cint(d.sx_dau_mua) + cint(bep.get(d.ma_hang, 0))" in nguon)


@ca("san_luong_theo_ma() cộng dồn nhiều ngày của cùng một mã")
def _():
	mv = _mv()
	la("ba ngày cộng lại", mv.san_luong_theo_ma([
		{"ma_hang": "LE1", "so_luong": 100},
		{"ma_hang": "LE1", "so_luong": 50},
		{"ma_hang": "LE2", "so_luong": 7},
	]), {"LE1": 150, "LE2": 7})
	la("chưa ai nhập thì rỗng, ô gõ tay giữ nguyên hiệu lực",
		mv.san_luong_theo_ma([]), {})


# ------------------------- o "Tong nha in giao" go tay van phai co hieu luc


@ca("Mã chưa khai đợt nào thì ô Tổng nhà in giao gõ tay vẫn tính vào tồn mở sổ")
def _():
	"""Bẫy đã gặp thật ngày 22/08/2026.

	Mùa Trung thu 2026 không khai đợt hàng nào, số vỏ hộp 1600 và 100 là người gõ
	thẳng vào ô "Tổng nhà in giao". Bản đầu của _mo_so_va_them chỉ đọc bảng đợt,
	nên hai dòng HỘP hiện 0 trên bảng theo ngày trong khi bảng Sản phẩm báo 1600.
	Luật đúng là luật của han_muc_tu_dot: chưa khai đợt thì ô gõ tay giữ nguyên
	hiệu lực; khai rồi thì đợt nói lên, ô gõ tay thôi.
	"""
	import inspect

	mv = _mv()
	nguon = "\n".join(
		d for d in inspect.getsource(mv._mo_so_va_them).split("\n")
		if not d.strip().startswith("#")
	)
	dung("phải dựng tập mã đã khai đợt", "co_dot" in nguon)
	dung("mã không có đợt thì cộng ô nhà in giao vào tồn mở sổ",
		'mo_so[d.ma_hang] += cint(d.get("nha_in_giao"))' in nguon)


@ca("Vỏ hộp gõ tay chảy đúng vào phép cuộn và ghép ngược")
def _():
	mv = _mv()
	# HOPA co 300 vo go tay, ruot du ghep 50 -> ban duoc that la 50.
	ra = mv.cuon_ton_theo_ngay(
		["2026-09-01"], {"HOPA": 300, "LE1": 100, "LE2": 0}, {}, {}, DM
	)
	o = mv.ghep_theo_ngay(ra["2026-09-01"], DM, {"LE2"})
	la("vỏ hộp gõ tay vào đúng tồn đầu", o["HOPA"]["ton_dau"], 300)
	la("bán được thật là 50", o["HOPA"]["con_thuc_te"], 50)


# ------------------------- ba trang thai cua o "Ruot ghep duoc"


@ca("Hộp khai đủ định mức mà ruột không đặt trần thì KHÔNG được báo chưa khai")
def _():
	"""Anh Việt bắt được 22/08/2026.

	MOONGARDEN khai đủ 5 ruột, cả 5 đều mang cờ "không đặt trần" nên
	ghep_duoc_tu_ruot bỏ qua hết và trả None. Bản cũ đọc None thành "chưa khai
	định mức ruột" - nói oan cho người đã khai. Ba trạng thái phải tách rõ.
	"""
	mv = _mv()
	dm = [
		{"ma_hop": "HOPA", "ma_banh": "LE1", "so_luong": 1},
		{"ma_hop": "HOPA", "ma_banh": "LE2", "so_luong": 1},
	]
	ra = mv.cuon_ton_theo_ngay(
		["2026-09-01"], {"HOPA": 500, "HOPB": 40, "LE1": 90, "LE2": 90}, {}, {}, dm
	)
	o = mv.ghep_theo_ngay(ra["2026-09-01"], dm, {"LE1", "LE2"})
	la("HOPA đã khai định mức", o["HOPA"]["chua_khai_dinh_muc"], 0)
	la("nhưng không ruột nào ràng buộc", o["HOPA"]["ruot_khong_rang_buoc"], 1)
	la("nên chỉ vỏ hộp chặn, bán được 500", o["HOPA"]["con_thuc_te"], 500)


@ca("Hộp CHƯA khai định mức nào thì mới được báo chưa khai")
def _():
	mv = _mv()
	dm = [{"ma_hop": "HOPA", "ma_banh": "LE1", "so_luong": 1}]
	ra = mv.cuon_ton_theo_ngay(["2026-09-01"], {"HOPA": 500, "LE1": 90}, {}, {}, dm)
	o = mv.ghep_theo_ngay(ra["2026-09-01"], dm)
	la("HOPA khai rồi", o["HOPA"]["chua_khai_dinh_muc"], 0)
	la("ruột ràng buộc bình thường", o["HOPA"]["ruot_khong_rang_buoc"], 0)
	la("ghép được 90", o["HOPA"]["ghep_duoc"], 90)
	la("bánh lẻ không bao giờ mang cờ này", o["LE1"]["chua_khai_dinh_muc"], 0)


# --------------------- hàng chip ngày bên màn hình: bẫy múi giờ


@ca("mvNgaySau bên màn hình không được đi qua toISOString")
def _():
	"""Anh Việt bắt được 22/08/2026: cả bảy chip đều ghi "Thứ bảy 22/08".

	new Date('2026-08-22T00:00:00') là nửa đêm GIỜ MÁY, tức 17h00 ngày 21 giờ
	UTC. toISOString() trả giờ UTC nên cắt ra '2026-08-21', lùi đúng một ngày;
	cộng 1 vào lại thành 22 - vòng tròn, ngày không bao giờ nhích. Máy ở Việt
	Nam (UTC+7) dính chắc chắn chứ không phải ngẫu nhiên, nên bộ kiểm phải giữ
	cửa này chứ không trông vào việc thử tay.

	Ca kiểm đọc thẳng mã nguồn vì tầng khung không chạy được JavaScript.
	"""
	import os
	import re

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	tep = os.path.join(goc, "public", "js", "bep", "11-khach-ca-hop-dong.js")
	nguon = io_doc(tep)

	m = re.search(r"function mvNgaySau\(s\) \{(.*?)\n\}", nguon, re.S)
	dung("tìm thấy hàm mvNgaySau", bool(m))
	if not m:
		return
	than = m.group(1)
	dung("KHÔNG được dùng toISOString trong phép cộng ngày",
		"toISOString" not in than)
	dung("phải tự ghép chuỗi từ getFullYear", "getFullYear" in than)


def io_doc(duong_dan):
	import io as _io

	return _io.open(duong_dan, encoding="utf-8").read()


# ------------------------------------------------------- cai bay _doc_mua


@ca("_doc_mua tra BO BA, moi cho goi phai mo ra ba bien")
def _bay_doc_mua():
	"""Ca canh gac cho dung mot cai bay da lam hong bon ham.

	`_doc_mua` tra ve `(dong, dinh_muc, doc)`, nhung cai ten "doc" o dau ham
	lam nguoi doc tuong no tra ve mot ban ghi. Bon ham `dat_san_luong`,
	`them_san_luong`, `sua_san_luong`, `xoa_san_luong` da viet:

	    doc = _doc_mua(mua)
	    ... doc.dong ...

	Ket qua: `'tuple' object has no attribute 'dong'`, loi 500 ngay khi bep
	go so san xuat. Bon ham do them tu v272 va v274 va CHUA TUNG chay duoc
	mot lan nao, mai 23/08/2026 anh Viet go so moi lo ra.

	Ca nay soi ma nguon: moi lan goi `_doc_mua` phai la mot phep mo ba bien.
	Ai lo viet lai kieu mot bien la do ngay, khong doi toi luc co nguoi bam.
	"""
	import ast
	import io
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	src = io.open(os.path.join(goc, "mua_vu.py"), encoding="utf-8").read()

	# Doc bang CAY CU PHAP chu khong do chuoi tung dong: do chuoi thi dinh ca
	# dong vi du nam trong phan ghi chu, va ca nay se do oan.
	cay = ast.parse(src)
	hong = []
	for nut in ast.walk(cay):
		if not isinstance(nut, ast.Assign):
			continue
		gt = nut.value
		if not (isinstance(gt, ast.Call) and isinstance(gt.func, ast.Name)
				and gt.func.id == "_doc_mua"):
			continue
		for dich in nut.targets:
			# Mo ba bien thi ve trai la Tuple. Mot bien tran la dinh bay.
			if not isinstance(dich, ast.Tuple):
				hong.append("dong %d" % nut.lineno)
	dung("khong cho nao coi _doc_mua nhu mot ban ghi: " + ("; ".join(hong) or "sach"),
		not hong)


@ca("bon ham san luong dung _ban_ghi_mua, va ham do noi ro no tra gi")
def _dung_ban_ghi_mua():
	import io
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	src = io.open(os.path.join(goc, "mua_vu.py"), encoding="utf-8").read()

	dung("co ham lay ban ghi", "def _ban_ghi_mua(" in src)
	for ten in ("dat_san_luong", "them_san_luong", "sua_san_luong", "xoa_san_luong"):
		i = src.find("def %s(" % ten)
		dung("co ham %s" % ten, i > 0)
		than = src[i:i + 1200]
		dung("%s lay dung ban ghi" % ten, "_ban_ghi_mua(mua)" in than)
	# Mua rong hay mua da xoa thi phai noi ro, khong de Frappe nem DoesNotExist.
	j = src.find("def _ban_ghi_mua(")
	nen = src[j:j + 2000]
	dung("chan mua rong", "frappe.db.exists(DT, ma)" in nen)
	dung("cau bao loi chi duong ra", "chọn lại mùa" in nen)


# ---------------------------------------------------------------------------
# CHOT TON DAU NGAY (v291, 23/08/2026)
#
# Anh Viet: *"cai so ton dau o man kiem banh trung thu CHO PHEP SUA SO DUOC de
# Loan Anh sua so cho khop so ton hien tai"*.
#
# "Ton dau ngay" khong phai so duoc luu, no la ket qua cua phep cuon. Nen viec
# cho sua khong phai la them mot o cho go, ma la them mot duong CAT DUT phep
# cuon tai dung mot ngay. Cac ca duoi day canh dung cho cat do.
# ---------------------------------------------------------------------------


@ca("chốt tồn: có người đếm tay thì ngày đó lấy số của họ, không cuộn từ hôm trước")
def _():
	from vagabond.mua_vu import cuon_ton_theo_ngay

	ngay = ["2026-08-23", "2026-08-24"]
	# Khong chot: 100 tru 10 con 90, hom sau ton dau 90.
	khong = cuon_ton_theo_ngay(
		ngay, {"B1": 100}, {}, {("B1", "2026-08-23"): {"da_dat": 10}}, [])
	la("chưa chốt, ngày đầu tồn đầu 100", khong["2026-08-23"]["B1"]["ton_dau"], 100)
	la("chưa chốt, ngày sau cuộn ra 90", khong["2026-08-24"]["B1"]["ton_dau"], 90)

	# Loan Anh dem thuc te ngay 24 chi con 70.
	co = cuon_ton_theo_ngay(
		ngay, {"B1": 100}, {}, {("B1", "2026-08-23"): {"da_dat": 10}}, [],
		{("B1", "2026-08-24"): 70})
	la("chốt rồi thì ngày 24 lấy số đếm được", co["2026-08-24"]["B1"]["ton_dau"], 70)
	la("ngày TRƯỚC ngày chốt không bị đụng tới",
		co["2026-08-23"]["B1"]["ton_dau"], 100)


@ca("chốt tồn: cuộn tiếp từ số đã chốt chứ không quay về số cũ")
def _():
	"""Chot ma khong cuon tiep tu no thi ngay ke tiep so lai vot len, va nguoi
	dem thay cong suc cua minh bay mat sau dung mot ngay."""
	from vagabond.mua_vu import cuon_ton_theo_ngay

	ngay = ["2026-08-23", "2026-08-24", "2026-08-25"]
	r = cuon_ton_theo_ngay(
		ngay, {"B1": 100}, {},
		{("B1", "2026-08-24"): {"da_dat": 5}}, [],
		{("B1", "2026-08-24"): 70})
	la("ngày chốt lấy 70", r["2026-08-24"]["B1"]["ton_dau"], 70)
	la("ngày chốt còn bán 65", r["2026-08-24"]["B1"]["co_the_ban"], 65)
	la("ngày SAU cuộn tiếp từ 65", r["2026-08-25"]["B1"]["ton_dau"], 65)


@ca("chốt tồn: số 0 là con số đếm được thật, không phải dấu hiệu xoá")
def _():
	"""Het sach hang la mot su that phai ghi duoc. Muon so 0 lam dau hieu xoa
	thi lan dau ai do dem ra 0 se thay o nhay ve so may cuon, va mat long tin
	vao ca man hinh."""
	from vagabond.mua_vu import cuon_ton_theo_ngay

	r = cuon_ton_theo_ngay(
		["2026-08-23"], {"B1": 100}, {}, {}, [], {("B1", "2026-08-23"): 0})
	la("chốt 0 thì tồn đầu bằng 0 chứ không phải 100",
		r["2026-08-23"]["B1"]["ton_dau"], 0)
	la("và cờ chốt tay vẫn bật", r["2026-08-23"]["B1"]["chot_tay"], 1)


@ca("chốt tồn: cờ chốt_tay phải bật ĐÚNG ô được chốt, không lan sang ô khác")
def _():
	"""Khong co co nay thi ba hom sau so venh voi phep cuon va khong ai truy
	duoc la do dem tay hay do may tinh sai. Bat nham o cung te y het."""
	from vagabond.mua_vu import cuon_ton_theo_ngay

	ngay = ["2026-08-23", "2026-08-24"]
	r = cuon_ton_theo_ngay(
		ngay, {"B1": 100, "B2": 50}, {}, {}, [], {("B1", "2026-08-24"): 70})
	la("ô được chốt bật cờ", r["2026-08-24"]["B1"]["chot_tay"], 1)
	la("mã khác cùng ngày KHÔNG bật cờ", r["2026-08-24"]["B2"]["chot_tay"], 0)
	la("cùng mã ngày khác KHÔNG bật cờ", r["2026-08-23"]["B1"]["chot_tay"], 0)
	la("mã khác cùng ngày giữ nguyên số cuộn",
		r["2026-08-24"]["B2"]["ton_dau"], 50)


@ca("chốt tồn: mã chỉ xuất hiện trong bảng chốt vẫn phải có mặt trong bảng")
def _():
	"""Bo sot thi go so cho mot ma xong lam moi lai la dong do bien mat."""
	from vagabond.mua_vu import cuon_ton_theo_ngay

	r = cuon_ton_theo_ngay(
		["2026-08-23"], {}, {}, {}, [], {("BLA", "2026-08-23"): 12})
	dung("mã BLA có trong bảng", "BLA" in r["2026-08-23"])
	la("và mang đúng số đã chốt", r["2026-08-23"]["BLA"]["ton_dau"], 12)


@ca("chốt tồn: không truyền bảng chốt thì kết quả y hệt bản cũ")
def _():
	"""Hang rao chong hoi quy: ham nay dang chay that cho ca mua trung thu,
	them tham so moi ma doi ket qua cu la lam lech so cua ca tiem."""
	from vagabond.mua_vu import cuon_ton_theo_ngay

	ngay = ["2026-08-23", "2026-08-24"]
	cam = {("B1", "2026-08-23"): {"da_dat": 10, "cho_chot": 3}}
	khong_truyen = cuon_ton_theo_ngay(ngay, {"B1": 100}, {}, cam, [])
	truyen_rong = cuon_ton_theo_ngay(ngay, {"B1": 100}, {}, cam, [], {})
	truyen_none = cuon_ton_theo_ngay(ngay, {"B1": 100}, {}, cam, [], None)
	la("bảng rỗng cho kết quả y hệt", truyen_rong, khong_truyen)
	la("None cho kết quả y hệt", truyen_none, khong_truyen)
	la("số cũ vẫn đúng", khong_truyen["2026-08-24"]["B1"]["ton_dau"], 87)


@ca("chốt tồn: HÀNG RÀO có thật sự cắn không")
def _():
	"""Dung lai dung ba cach hong, phai thay ket qua sai ngay.

	Ngay 23/08 da co mot ca kiem so vi tri chuoi ma khong bat duoc loi that,
	nen tu nay hang rao nao cung phai tu chung minh no do khi loi quay lai.
	"""
	from vagabond.mua_vu import cuon_ton_theo_ngay

	ngay = ["2026-08-23", "2026-08-24", "2026-08-25"]

	# 1. Neu chot KHONG cat duoc phep cuon thi ngay 24 van ra 100.
	r = cuon_ton_theo_ngay(ngay, {"B1": 100}, {}, {}, [],
		{("B1", "2026-08-24"): 70})
	dung("chốt có cắt được phép cuộn", r["2026-08-24"]["B1"]["ton_dau"] != 100)

	# 2. Neu chot khong cuon tiep thi ngay 25 se ra 100 chu khong phai 70.
	dung("ngày sau cuộn tiếp từ số đã chốt",
		r["2026-08-25"]["B1"]["ton_dau"] == 70)

	# 3. Neu co chot_tay khong ton tai thi man hinh khong hien duoc dau.
	dung("kết quả có mang cờ chốt_tay", "chot_tay" in r["2026-08-24"]["B1"])
