# -*- coding: utf-8 -*-
"""v563: gom nhóm trong từng phân hệ, ô tìm nghiệp vụ và ô ghim.

Anh Việt giao 03/10/2026, ba việc trên cùng một màn:

  1. *"thêm ô 'Tìm kiếm nghiệp vụ' để gõ là ra nút để truy cập luôn"*
  2. *"thêm tính năng được pin 5 ô hay truy cập nhất cho từng user"*
  3. *"bên trong tất cả các nút phân hệ em cho nhóm lại dùm anh các nút tính
     năng sao cho phù hợp"*

Bộ ca dưới đây chốt phần LUẬT, không chốt hành vi màn hình: hành vi (gõ, bấm
ghim, bấm ô, vẽ nhóm) chạy thật trong node ở
vagabond/khung/kiem_thu/hanh_vi/trang_chu_563.js, theo đúng điều 16 của
CLAUDE.md - dò chuỗi trong mã nguồn không phải là kiểm thử.

Việc đắt nhất ở đây là ca "mọi phân hệ phủ hết ô": sửa bảng nhóm mà bỏ sót
một khoá thì ô đó rơi xuống nhóm "Khác" ở cuối màn. Không mất nút, nhưng
nhóm "Khác" mọc dần ra là dấu hiệu bảng nhóm đang cũ đi, nên cổng phải đỏ
ngay lần đầu chứ không chờ ai nhìn thấy.

Toàn phép thuần, không Frappe, không requests.
"""

import io
import json
import os
import subprocess

from vagabond import ghim
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JS = os.path.join(GOI, "public", "js", "bep", "02-trang-chu.js")


def _ma_js():
	return io.open(JS, encoding="utf-8").read()


def _bang_nhom():
	"""Đọc THẬT bảng VGB_NHOM bằng node, không đọc bằng biểu thức chính quy.

	Vì sao gọi node: bảng này có lời gọi VGB_DM.map(), có chú thích nhiều
	dòng và có dấu nháy trong tiếng Việt. Đọc bằng biểu thức chính quy là tự
	viết lại một bộ phân tích JavaScript nửa vời, và nó sẽ sai vào một ngày
	ai đó thêm dấu phẩy vào chú thích. Máy chạy CI có node: công đoạn 2 của
	cổng đã dùng `node --check` trước khi tới đây.
	"""
	ma = (
		'var fs=require("fs");'
		'var s=fs.readFileSync(process.argv[1],"utf8");'
		'var a=s.indexOf("var VGB_DM = [");'
		'var b=s.indexOf("var VGB_HUB = {};");'
		'var f=new Function(s.slice(a,b)+"; return {dm:VGB_DM, nhom:VGB_NHOM};");'
		'process.stdout.write(JSON.stringify(f()));'
	)
	ra = subprocess.run(["node", "-e", ma, JS], capture_output=True, check=True)
	return json.loads(ra.stdout.decode("utf-8"))


# ------------------------------------------------------- bảng nhóm phân hệ


@ca("gom nhóm: mọi khoá trong bảng nhóm đều là khoá CÓ THẬT của phân hệ đó")
def _():
	for nh in _bang_nhom()["nhom"]:
		co = set(nh["keys"])
		for g in nh.get("nhom") or []:
			for k in g["keys"]:
				dung("%s / %s: khoá %s phải thuộc phân hệ" % (nh["ten"], g["t"], k), k in co)


@ca("gom nhóm: không khoá nào nằm ở hai nhóm cùng lúc trong một phân hệ")
def _():
	for nh in _bang_nhom()["nhom"]:
		da = []
		for g in nh.get("nhom") or []:
			for k in g["keys"]:
				dung("%s: khoá %s chỉ được xếp một nhóm" % (nh["ten"], k), k not in da)
				da.append(k)


@ca("gom nhóm: phân hệ nào đã khai nhóm thì phải phủ HẾT ô, không bỏ sót")
def _():
	# Bo sot thi o do roi xuong nhom "Khac" o cuoi man chu khong mat (ca kiem
	# hanh vi chot cho do). Nhung nhom "Khac" moc dan ra la dau hieu bang nhom
	# dang cu di, nen cong phai do ngay lan dau.
	for nh in _bang_nhom()["nhom"]:
		if not nh.get("nhom"):
			continue
		da = set()
		for g in nh["nhom"]:
			da.update(g["keys"])
		thieu = [k for k in nh["keys"] if k not in da]
		la("phân hệ %s không bỏ sót ô nào" % nh["ten"], thieu, [])


@ca("gom nhóm: ba màn ba ô (Nhập kho, Kiểm kê, Nhân sự) CỐ Ý không gom")
def _():
	# Anh Viet duyet mockup 03/10/2026: ba man nay chi co ba o, gom vao chi
	# them mot lop chu de doc chu khong giup tim nhanh hon.
	m = {x["k"]: x for x in _bang_nhom()["nhom"]}
	for k in ("NK", "KK", "NS"):
		dung("phân hệ %s không khai nhóm" % k, not m[k].get("nhom"))
		la("phân hệ %s vẫn đúng ba ô" % k, len(m[k]["keys"]), 3)


@ca("gom nhóm: tên nhóm xuất kho theo SAP, 'Xuất nội bộ' chứ không 'trong nhà'")
def _():
	# Anh Viet chot 03/10/2026: *"Xuat trong nha phai doi thanh Xuat noi bo"*,
	# va *"em tra cuu them nhung phan mem lon nhu SAP di chu de dung thuat ngu
	# cho dung"*. SAP S/4HANA chia Goods Movement thanh Goods Receipt, Goods
	# Issue va Stock Transfer; Stock Transfer la hang van trong nha. Ba nhom o
	# day di theo cach chia do.
	m = {x["k"]: x for x in _bang_nhom()["nhom"]}
	ten = [g["t"] for g in m["XK"]["nhom"]]
	la("ba nhóm xuất kho", ten, ["Xuất nội bộ", "Xuất ra ngoài", "Xuất bỏ"])
	nb = [g for g in m["XK"]["nhom"] if g["t"] == "Xuất nội bộ"][0]
	dung("điều chuyển nội bộ thuộc nhóm nội bộ", "XKD" in nb["keys"])
	ra = [g for g in m["XK"]["nhom"] if g["t"] == "Xuất ra ngoài"][0]
	dung("bán sỉ là hàng rời tiệm", "XKSI" in ra["keys"])
	dung("trả nhà cung cấp là hàng rời tiệm", "XKTRA" in ra["keys"])


@ca("gom nhóm: hai ô bản khung đã ẩn khỏi phân hệ Thu mua")
def _():
	# Anh Viet 03/10/2026: *"Dong y an luon ban khung di"*. Hai MAN van con
	# trong vgbGo de ai co dia chi van mo duoc ma soi; chi bo cai NUT.
	m = {x["k"]: x for x in _bang_nhom()["nhom"]}
	for k in ("KHPO", "KHHDM"):
		dung("khoá %s không còn trong phân hệ Thu mua" % k, k not in m["TM"]["keys"])
	la("phân hệ Thu mua còn năm ô", len(m["TM"]["keys"]), 5)
	ma = _ma_js()
	dung("không còn nút nào dựng ô bản khung", "'KHPO')" not in ma.split("var VGB_DM")[0])
	dung("vẫn còn đường đi tới màn bản khung", "if (k === 'KHPO')" in ma)


@ca("gom nhóm: phân hệ Danh mục gom theo 16 danh mục nền tảng, không sót")
def _():
	b = _bang_nhom()
	dm = {"DM:" + x["m"] for x in b["dm"]}
	m = {x["k"]: x for x in b["nhom"]}
	da = set()
	for g in m["DM"]["nhom"]:
		da.update(g["keys"])
	la("bảng nhóm phủ đúng 16 danh mục", sorted(da), sorted(dm))


# ------------------------------------------------------------------ ô ghim


@ca("ghim: trần số ô ghim bên JS và bên Python phải BẰNG nhau")
def _():
	# Hai ben lech nhau thi man hinh chan o thu sau trong khi may chu cat sau
	# o, hoac nguoc lai: nguoi dung ghim duoc sau o roi mo app lai thi mat mot.
	ma = _ma_js()
	dung("JS khai trần số", "var VGB_GHIM_TOI_DA = 5;" in ma)
	la("Python khai cùng con số", ghim.TOI_DA, 5)


@ca("ghim: bỏ trùng, cắt còn tối đa năm, GIỮ đúng thứ tự người dùng xếp")
def _():
	la("bỏ trùng", ghim.chuan(["POS", "CN", "POS"]), ["POS", "CN"])
	la("giữ thứ tự chứ không xếp lại", ghim.chuan(["VD", "CN", "POS"]), ["VD", "CN", "POS"])
	la("cắt còn năm", ghim.chuan(["a", "b", "c", "d", "e", "f", "g"]),
		["a", "b", "c", "d", "e"])
	la("danh sách rỗng", ghim.chuan([]), [])
	la("không truyền gì", ghim.chuan(None), [])


@ca("ghim: chỉ nhận khoá hình thức đúng, chặn chuỗi lạ nhét vào bảng mặc định")
def _():
	# Cua nay ghi vao bang DefaultValue cua Frappe. Khoa nghiep vu that chi gom
	# chu, so, dau noi va dau hai cham (POS, CNPT, BC:BC05, DM:DMSP).
	la("giữ khoá có dấu hai chấm", ghim.chuan(["BC:BC05", "DM:DMSP"]), ["BC:BC05", "DM:DMSP"])
	la("bỏ khoảng trắng và dấu lạ", ghim.chuan(["a b", "c<d", "e'f", "POS"]), ["POS"])
	la("bỏ chuỗi rỗng", ghim.chuan(["", "   ", "POS"]), ["POS"])
	la("bỏ khoá dài quá", ghim.chuan(["X" * 41, "POS"]), ["POS"])
	la("bỏ thứ không phải chữ", ghim.chuan([1, None, {}, ["POS"], "POS"]), ["POS"])


@ca("ghim: bản cất hỏng thì đọc ra rỗng, KHÔNG nổ giữa trang chủ")
def _():
	# Ham nay chay moi lan mo app. No no la ca trang chu trang.
	la("chưa ghim gì", ghim.doc_chuoi(""), [])
	la("chưa có dòng nào", ghim.doc_chuoi(None), [])
	la("rác không phải JSON", ghim.doc_chuoi("{khong phai json"), [])
	la("JSON nhưng không phải mảng", ghim.doc_chuoi('{"a": 1}'), [])
	la("mảng lẫn rác", ghim.doc_chuoi('["POS", 7, "CN"]'), ["POS", "CN"])
	la("mảng quá dài vẫn cắt", ghim.doc_chuoi('["a","b","c","d","e","f"]'),
		["a", "b", "c", "d", "e"])


@ca("ghim: hai hàm thuần không chạm Frappe, đọc được mà không cần site")
def _():
	import inspect

	for ham in (ghim.chuan, ghim.doc_chuoi):
		nguon = inspect.getsource(ham)
		dung("%s không gọi frappe" % ham.__name__, "frappe." not in nguon)


# ---------------------------------------------------------- ô tìm nghiệp vụ


@ca("ô tìm: nhãn trên màn đúng câu anh Việt chốt, không phải 'Ô ghim của tôi'")
def _():
	# Anh Viet 03/10/2026: *"O ghim cua toi doi thanh Ghim nghiep vu hay dung"*.
	ma = _ma_js()
	dung("nhãn khối ghim", "Ghim nghi\\u1ec7p v\\u1ee5 hay d\\u00f9ng" in ma)
	dung("không còn nhãn cũ", "Ô ghim của tôi" not in ma)
	dung("ô tìm có chỗ gợi ý gõ gì", "vgbtim" in ma)


@ca("ô tìm: phép bỏ dấu phải bỏ cả chữ đ, không chỉ bỏ dấu thanh")
def _():
	# normalize('NFD') tach duoc dau thanh nhung KHONG tach duoc chu d gach.
	# Thieu dong replace cuoi thi go "don" khong ra "Don con treo".
	ma = _ma_js()
	than = ma.split("function vgbBoDau(")[1].split("\n}")[0]
	dung("có bước bỏ dấu thanh", "normalize('NFD')" in than)
	dung("có bước bỏ chữ đ gạch", "\\u0111" in than)


@ca("ô tìm: cửa ngõ ghim đi qua api đúng tên mô đun bên Python")
def _():
	# Go sai ten duong la man im lang khong ghim duoc, va khong ai biet vi sao.
	ma = _ma_js()
	dung("đường lấy ghim", "'vagabond.ghim.lay'" in ma)
	dung("đường cất ghim", "'vagabond.ghim.luu'" in ma)
	dung("mô đun bên Python mở đúng hai cửa đó",
		hasattr(ghim, "lay") and hasattr(ghim, "luu"))
