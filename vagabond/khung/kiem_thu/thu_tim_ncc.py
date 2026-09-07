# -*- coding: utf-8 -*-
"""Moi cho chon nha cung cap deu phai co duong TAO MOI ngay tai cho.

Anh Viet 21/08/2026: chi Dung lap phieu dong BHXH, go "BHXH CO SO TAN DINH"
roi go tiep "bao hiem xa hoi", ca hai lan deu khong ra gi. Man hinh bao
"Chua chon ben nhan tien" va het duong. Kiem lai tren site that: ca tiem co
520 nha cung cap, khong cai nao la ben bao hiem.

Loi khong nam o phep tim - `ds_nguoi_ung` co tim theo `supplier_name like`
dang hoang. Loi nam o cho: KHONG TIM THAY thi khong lam gi duoc nua.

Nen luat cua tep nay: man nao cho chon nha cung cap thi phai co du ba thu.

  1. Mot o de go tim.
  2. Cau noi ro la khong tim thay, chu khong im lang de danh sach rong.
  3. Nut tao moi, va nut do phai mang SAN cai ten vua go sang man tao.

Diem thu ba de bi bo qua nhat, ma no la diem quan trong nhat: bat nguoi ta
go lai lan thu ba cai ten ho vua go hai lan khong ra gi la cach nhanh nhat
de ho bo cuoc va di nhan tin hoi.
"""

import io
import os

from vagabond import ho_so_tt as hs
from vagabond.khung.kiem_thu.nen import ca, dung


def _js(ten):
	goi = os.path.dirname(os.path.abspath(hs.__file__))
	return io.open(
		os.path.join(goi, "public", "js", "bep", ten), encoding="utf-8").read()


def _bo_chu_thich(js):
	"""Bo moi chu thich khoi ma nguon JS.

	Do chuoi tren ban con chu thich la tu lua: chinh cau chu thich ke lai
	"truoc day cho nay bay `ncc.slice(0, 40)`" se bi tinh la vi pham. Cat
	bo hai kieu chu thich cua JS roi moi do. Khong dung cach cat theo dong
	dau dong, vi khoi chu thich nhieu dong cua repo nay thut le va dong
	tiep theo khong mang dau hieu nao.
	"""
	ra, i, n = [], 0, len(js)
	while i < n:
		hai = js[i:i + 2]
		if hai == "/*":
			j = js.find("*/", i + 2)
			i = n if j < 0 else j + 2
		elif hai == "//":
			j = js.find("\n", i)
			i = n if j < 0 else j
		else:
			ra.append(js[i])
			i += 1
	return "".join(ra)


# ------------------------------------------------------ dung cu dung chung


@ca("tìm NCC: có khung dùng chung, không rải mỗi màn một kiểu")
def _():
	js = _js("19-ho-so-tt.js")
	# 06/09/2026, Issue #196: gom het ve MOT cua. Truoc do co ba ham rieng
	# (`hsOTimNcc`, `hsKhungTimNcc`, `hsNoiNutTaoNcc`) dung o tim va nut tao
	# moi ngay tren form, canh mot bang chip dai. Bang chip do chinh la thu
	# anh Viet keu. Nay ca ba deu nam trong tam truot.
	dung("có tấm trượt dùng chung", "function hsMoChonBenNhan(" in js)
	dung("có thẻ thu gọn dùng chung", "function hsTheBenNhan(" in js)
	dung("nút mang tên vừa gõ sang màn tạo", "nccTaoNhanh(" in js)
	# Chot nguoc lai: ba ham cu phai BIEN MAT. De lai thi lan sau co nguoi
	# goi va bang chip moc lai y nhu lan nay.
	for cu in ("function hsOTimNcc(", "function hsKhungTimNcc(",
			"function hsNoiNutTaoNcc("):
		dung("đã gỡ %s" % cu, cu not in js)
	# Chi duy nhat tam truot duoc mo man tao nha cung cap. Rai ra nhieu cho
	# la moi cho mot kieu, dung cai vua phai sua lai.
	dung("chỉ một chỗ mở màn tạo", js.count("nccTaoNhanh(") == 1)


@ca("tìm NCC: màn tạo nhà cung cấp nhận được việc phải làm sau khi lưu")
def _():
	js = _js("16-mua-hang.js")
	dung("có chỗ để màn gọi cài lại việc", "var nccXongThi = null;" in js)
	dung("có cửa mở nhanh", "function nccTaoNhanh(" in js)
	dung("điền sẵn tên vừa gõ", "nccF.ten = g;" in js)
	# Phai XOA sau khi dung: de lai la lan sau ai mo man tao tu man Mua
	# hang cung bi nem di cho khac.
	than = js.split("var cb = nccXongThi;")[1]
	dung("lấy ra xong thì xoá ngay", "nccXongThi = null;" in than[:120])


# --------------------------------------------------- du cac man deu mot cua


@ca("tìm NCC: màn nào CÒN chọn bên nhận tiền thì phải đi qua một cửa")
def _():
	js = _js("19-ho-so-tt.js")
	# Truoc 22/08/2026 co BA man chon nha cung cap. Nay con HAI, cong them
	# o "Nguoi duoc hoan ung" cua man hoan ung co hoa don.
	#
	# `scrHoanUngTao` (hoan ung khong hoa don) da bo han o chon nha cung
	# cap: anh Viet chot khoan hoan ung khong hoa don khong thuoc ve nha
	# cung cap nao ca, tien tra ve dung mot trong hai tai khoan ung, nen man
	# do gio chon TAI KHOAN. Day KHONG phai lo sot - dung khoi phuc lai o
	# chon nha cung cap o man ay.
	for man, the in (("scrChiCongTyTao", "huMoBen"), ("scrHoSoTTTao", "hsMoNcc")):
		than = js.split("function " + man)[1].split("\nasync function ")[0]
		dung("%s bày thẻ thu gọn" % man, "hsTheBenNhan('%s'" % the in than)
		dung("%s nối thẻ vào tấm trượt" % man,
			"document.getElementById('%s')" % the in than)
	than_hs = js.split("function scrHoSoTTTao")[1].split("\nasync function ")[0]
	dung("màn hoàn ứng có HĐ bày thẻ người nhận", "hsTheBenNhan('hsMoUng'" in than_hs)
	dung("và nối thẻ đó vào tấm trượt", "hsMoChonNguoiNhan(hay, hsTaoNguoiUng" in than_hs)
	# Chot nguoc lai: man hoan ung khong hoa don KHONG duoc chon NCC nua.
	than_hu = js.split("function scrHoanUngTao")[1].split("\nasync function ")[0]
	dung("scrHoanUngTao KHÔNG còn chọn nhà cung cấp", "hsTheBenNhan(" not in than_hu)
	dung("scrHoanUngTao chọn tài khoản thay vào đó", "ds_tk_hoan_ung" in than_hu)


@ca("tìm NCC: KHÔNG màn nào được bày lại danh mục thành bảng chip thường trực")
def _():
	# Day la ca kiem chot cho chinh lan sot cua #196. Bang chip cu duoc dung
	# bang `posChipNut('data-hun=...` va `posChipNut('data-hsu=...`. Con mot
	# cai trong nguon la form lai bay danh muc ngay tren man.
	ma = _bo_chu_thich(_js("19-ho-so-tt.js"))
	# CHONG TU LUA: phep bo chu thich cat thoi la moi chuoi deu "khong con",
	# ca kiem xanh oan. Nen truoc khi ket luan gi, doi ban da cat phai con
	# giu duoc nhung thu chac chan phai co.
	dung("bản đã cắt vẫn còn chip tài khoản", 'data-hutk="' in ma)
	dung("bản đã cắt vẫn còn thẻ thu gọn", "hsTheBenNhan('huMoBen'" in ma)
	dung("bản đã cắt không mất quá nửa tệp", len(ma) > len(_js("19-ho-so-tt.js")) * 0.5)
	for xau in ("data-hun=", "data-hsu=", "data-hsn="):
		dung("không còn chip %s" % xau, xau not in ma)
	# Va khong duoc cat danh sach roi bay tam: cat la phan con lai khong co
	# duong nao cham toi.
	for man in ("scrChiCongTyTao", "scrHoSoTTTao"):
		than = ma.split("function " + man)[1].split("\nasync function ")[0]
		for cat in (".slice(0, 40)", ".slice(0, 8)"):
			dung("%s không cắt %s" % (man, cat), cat not in than)


@ca("tìm NCC: tạo xong thì chọn luôn người vừa tạo, không bắt tìm lại")
def _():
	js = _js("19-ho-so-tt.js")
	# Moi cau hinh cua tam truot phai khai `tao_xong`, khong thi tao xong
	# man ve lai ma o chon van rong.
	dung("có ba cấu hình đều khai tao_xong", js.count("tao_xong:") >= 3)
	than = js[js.index("function hsMoChonBenNhan("):js.index("function hsMoChonNcc(")]
	dung("tấm trượt thật sự gọi tao_xong", "nccTaoNhanh(t, o.tao_xong || o.chon)" in than)


@ca("tìm NCC: màn người được hoàn ứng phải nạp lại danh sách sau khi tạo")
def _():
	# `hsTaoDsUng` duoc cache mot lan. Khong xoa cache thi nguoi vua tao
	# khong co trong danh sach va the van hien ten cu - nguoi dung tuong may
	# khong luu duoc.
	js = _js("19-ho-so-tt.js")
	than = js.split("hsMoChonNguoiNhan(hay, hsTaoNguoiUng")[1][:400]
	dung("xoá cache trước khi vẽ lại", "hsTaoDsUng = null;" in than)


@ca("tìm NCC: bày ĐỦ người và với được cả phần nằm ngoài danh sách đã tải")
def _():
	# Ban cu chi bay 40 chip dau roi loc bang cach VE LAI MAN moi lan go.
	# Hai cai deu hong: ai khong nam trong 40 thi go mai khong ra o nhanh
	# hop le, va ve lai man thi ban phim dien thoai tut xuong sau MOI chu.
	js = _js("19-ho-so-tt.js")
	than = js[js.index("function hsMoChonNguoiNhan("):]
	than = than[:than.index("\n}")]
	dung("có đường hỏi thẳng máy chủ", "'vagabond.ho_so_tt.ds_nguoi_ung', { tu_khoa: q }" in than)
	tt = js[js.index("function hsMoChonBenNhan("):js.index("function hsMoChonNcc(")]
	dung("bấm Enter mới hỏi máy chủ", "if (e.key !== 'Enter') return;" in tt)
	dung("có trạng thái đang tải", "Đang hỏi máy chủ" in tt)
	dung("có trạng thái lỗi và chỉ đường làm lại", "bấm Enter tìm lại" in tt)
	# Man chinh KHONG duoc ve lai chi de loc nua.
	chi = js.split("function scrChiCongTyTao")[1].split("\nasync function ")[0]
	dung("màn chi công ty không truyền từ khoá khi nạp",
		"'vagabond.ho_so_tt.ds_nguoi_ung', {})" in chi)


@ca("tìm NCC: nút tạo mới mang cái ĐANG gõ, không mang biến đã lưu")
def _():
	# Nguoi ta go ten xong bam thang nut Tao moi, chua he roi khoi o nen
	# bien da luu van con rong. Doc thang gia tri trong o moi dung.
	js = _js("19-ho-so-tt.js")
	than = js[js.index("function hsMoChonBenNhan("):js.index("function hsMoChonNcc(")]
	i = than.index("nutTao.onclick")
	dung("đọc thẳng giá trị trong ô", "var t = inp.value.trim();" in than[i:i + 400])


@ca("tìm NCC: nút tạo mới chỉ hiện cho người có quyền thu mua")
def _():
	# Bay nut ra ma bam vao bi tu choi quyen thi con te hon la khong co nut.
	js = _js("19-ho-so-tt.js")
	dung("ba cấu hình đều hỏi quyền", js.count("tao_moi: coQuyenMua()") >= 3)
	than = js[js.index("function hsMoChonBenNhan("):js.index("function hsMoChonNcc(")]
	dung("không có quyền thì không dựng nút", "(o.tao_moi\n      ?" in than)


@ca("tìm NCC: kế toán phải tự tạo được nhà cung cấp")
def _():
	# Bay nut ra ma bam vao bi tu choi quyen thi con te hon la khong co
	# nut. Chi Dung mang vai Accounts Manager va Accounts User.
	from vagabond import nha_cung_cap as ncc

	dung("Accounts Manager tạo được", "Accounts Manager" in ncc.VAI_SUA)
	dung("Accounts User tạo được", "Accounts User" in ncc.VAI_SUA)
	dung("thu mua tạo được", "Purchase Manager" in ncc.VAI_SUA)
