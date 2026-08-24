"""Kiểm thử danh mục màn hình và bảng đường dẫn app Bếp.

Lịch sử ngắn của tệp này, đọc trước khi sửa:

  v284  dựng bảng đường dẫn, HAI bảng gõ tay, ca kiểm đối chiếu hai bảng.
  v286  phát hiện ca kiểm đó vô dụng trong trường hợp quan trọng nhất: hai
        bảng KHỚP nhau tuyệt đối mà cùng SAI. Slug `don-da-huy` trỏ vào khoá
        `DTREO`, và `DTREO` là màn "Đơn còn treo".
  v288  bỏ bảng gõ tay bên JavaScript, máy sinh từ danh mục bên Python.

Nên các ca ở đây không còn đối chiếu hai bảng nữa (không còn hai bảng), mà
canh ba thứ khác: slug đang chạy thật không được đổi, slug không được trùng
nhau và không được trùng route Web Page, và mọi khoá trong danh mục phải có
nhánh thật trong `vgbGo` chứ không rơi vào nhánh vét cuối hàm.
"""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la

# .../vagabond/khung/kiem_thu/tep -> len BON bac moi toi goc repo.
GOC = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__)))))
TEP_JS = os.path.join(GOC, "vagabond", "public", "js", "bep", "02-trang-chu.js")


def _js():
	return io.open(TEP_JS, encoding="utf-8").read()


@ca("slugify: bỏ dấu tiếng Việt, gạch nối, chữ thường")
def _():
	from vagabond.duong_app import khong_dau, slugify

	la("bỏ dấu", khong_dau("Kiểm bánh hàng ngày"), "Kiem banh hang ngay")
	# Chu d gach khong tach duoc bang NFD vi no la mot chu cai khac chu khong
	# phai o co dau. Quen doi tay chu nay thi slug ra "-on-hang".
	la("chữ đ hoa và thường", khong_dau("Đơn hàng đủ"), "Don hang du")
	la("tên thường", slugify("Kiểm bánh hàng ngày"), "kiem-banh-hang-ngay")
	la("có dấu chấm phẩy", slugify("Hoá đơn, mua vào."), "hoa-don-mua-vao")
	la("khoảng trắng thừa hai đầu", slugify("  Nhà  cung cấp!!  "), "nha-cung-cap")
	la("chữ số giữ nguyên", slugify("Kho V2"), "kho-v2")
	la("toàn ký tự lạ thì ra rỗng", slugify("!!! ???"), "")
	la("rỗng vào rỗng ra", slugify(""), "")
	la("None vào rỗng ra", slugify(None), "")


@ca("đường app: slug ĐANG CHẠY THẬT không được đổi")
def _():
	"""Đổi một slug đang chạy là làm chết đường dẫn nhân viên đã lưu.

	Bảng SLUG_DA_CHAY chốt cứng 26 địa chỉ đã lên site từ v284 đến v287. Đổi
	tên một màn trong MAN mà vô tình đổi luôn slug thì ca này đỏ, và lúc đó
	phải ghi đè slug chứ không được để nó trôi.
	"""
	from vagabond.duong_app import SLUG_DA_CHAY, bang_duong

	b = bang_duong()
	for slug, khoa in sorted(SLUG_DA_CHAY.items()):
		la("/%s vẫn trỏ vào %s" % (slug, khoa), b.get(slug), khoa)


@ca("đường app: không hai màn nào dùng chung một slug")
def _():
	"""Trùng slug thì màn khai sau lặng lẽ nuốt màn khai trước.

	Phải đếm trên TỪNG CẶP chứ không đếm trên dict, vì nhét vào dict chính là
	lúc cặp trùng biến mất.
	"""
	from vagabond.duong_app import _cap_duong

	dem = {}
	for slug, khoa in _cap_duong():
		dem.setdefault(slug, []).append(khoa)
	trung = ["%s: %s" % (s, ", ".join(k)) for s, k in sorted(dem.items()) if len(k) > 1]
	dung("không slug nào trùng: " + ("; ".join(trung) or "sạch"), not trung)


@ca("đường app: slug không được trùng route của Web Page nào")
def _():
	"""Trùng route thì hook website_route_rules cướp trang thật của site.

	Ngày 23/08 màn "Bếp" suýt sinh ra slug `bep`, mà `bep` chính là route của
	Web Page chứa cả app. App tự nuốt chính mình. Ca này bắt được nên đã đổi
	tên màn thành "Bảng bếp hôm nay".
	"""
	from vagabond.duong_app import ROUTE_DA_CO, bang_duong

	dung_nhau = sorted(set(bang_duong()) & set(ROUTE_DA_CO))
	dung("không đụng Web Page nào: " + (", ".join(dung_nhau) or "sạch"), not dung_nhau)


@ca("đường app: slug chỉ gồm chữ thường, số và gạch nối")
def _():
	from vagabond.duong_app import bang_duong

	xau = [s for s in bang_duong() if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", s)]
	dung("mọi slug đều sạch: " + (", ".join(xau) or "sạch"), not xau)


@ca("đường app: bảng bên JavaScript phải ĐÚNG BẰNG bản máy sinh")
def _():
	"""Đối chiếu từng byte, y như dung_app_bep.py canh app_bep.js.

	Sửa tay vào bảng bên JavaScript thì ca này đỏ ngay, nên không còn đường
	nào để hai bên lệch nhau nữa.
	"""
	import sys

	if GOC not in sys.path:
		sys.path.insert(0, GOC)
	from sinh_duong import doan_dang_co
	from vagabond.duong_app import sinh_js

	dang_co = doan_dang_co(_js())
	dung("tìm thấy hai dấu mốc trong 02-trang-chu.js", bool(dang_co))
	dung("bảng trong tệp khớp từng byte với bản máy sinh (chạy sinh_duong.py nếu đỏ)",
		dang_co == sinh_js())


def _khoa_trong_vgbgo():
	"""Các khoá có nhánh THẬT trong vgbGo, đọc thẳng từ mã nguồn."""
	src = _js()
	i = src.index("function vgbGo(k) {")
	than = src[i:]
	ra = set(re.findall(r"k === '([A-Za-z0-9:]+)'", than))
	# Nhanh tien to cho ca ho danh muc va ca muoi hai phan he.
	if "k.indexOf('DM:') === 0" in than:
		ra.add("DM:*")
	if "k.indexOf('PH:') === 0" in than:
		ra.add("PH:*")
	return ra


@ca("đường app: mọi khoá trong danh mục phải có nhánh thật trong vgbGo")
def _():
	"""Khoá không có nhánh sẽ rơi xuống nhánh vét cuối hàm và vỡ màn.

	Nhánh vét là `go(function () { scrMRList(TYPES[k]); })`. Khoá lạ thì
	TYPES[k] là undefined, màn dựng ra rỗng, và không có lỗi nào hiện lên -
	đúng kiểu hỏng lặng lẽ mà bảng đường dẫn sinh ra để chặn.
	"""
	from vagabond.duong_app import bang_duong

	co = _khoa_trong_vgbgo()
	dung("đọc được các nhánh trong vgbGo", len(co) > 20)
	thieu = []
	for slug, khoa in sorted(bang_duong().items()):
		if khoa.startswith("DM:"):
			if "DM:*" not in co:
				thieu.append("%s (%s)" % (slug, khoa))
			continue
		if khoa.startswith("PH:"):
			if "PH:*" not in co:
				thieu.append("%s (%s)" % (slug, khoa))
			continue
		if khoa not in co:
			thieu.append("%s (%s)" % (slug, khoa))
	dung("không khoá nào thiếu nhánh: " + (", ".join(thieu) or "đủ"), not thieu)


@ca("đường app: luật định tuyến sinh đúng và sắp xếp ổn định")
def _():
	from vagabond.duong_app import TRANG_APP, bang_duong, luat_dinh_tuyen

	luat = luat_dinh_tuyen()
	la("số luật bằng số màn", len(luat), len(bang_duong()))
	dung("mọi luật đều trả về trang app",
		all(x["to_route"] == TRANG_APP for x in luat))
	dung("mọi luật đều bắt đầu bằng dấu gạch chéo",
		all(x["from_route"].startswith("/") for x in luat))
	# Thu tu on dinh thi hai lan chay ra cung mot danh sach, nen doc git diff
	# khong thay bien dong gia.
	la("chạy hai lần ra một kết quả", luat, luat_dinh_tuyen())


@ca("đường app: HÀNG RÀO có thật sự cắn không")
def _():
	"""Tự thử lại các hàng rào ở trên, vì hàng rào không cắn còn tệ hơn không có.

	Ngày 23/08 đã có một ca kiểm so vị trí chuỗi mà không bắt được lỗi thật,
	nên từ nay hàng rào nào cũng phải tự chứng minh nó đỏ khi lỗi quay lại.
	"""
	from vagabond.duong_app import ROUTE_DA_CO, slugify

	# 1. Dat ten man la "Bep" thi slug ra dung route cua Web Page chua app.
	dung("tên màn 'Bếp' sinh ra slug đụng Web Page", slugify("Bếp") in ROUTE_DA_CO)
	dung("tên màn 'Bảng bếp hôm nay' thì không đụng",
		slugify("Bảng bếp hôm nay") not in ROUTE_DA_CO)

	# 2. Hai man cung ten thi ra cung slug. Day la ly do ho DM: phai co tien to.
	la("hai màn cùng tên ra cùng slug",
		slugify("Nhà cung cấp"), slugify("Nhà cung cấp"))

	# 3. Ham doc nhanh vgbGo phai that su doc duoc, khong tra ve rong roi
	#    lam ca kiem o tren xanh gia.
	co = _khoa_trong_vgbgo()
	for k in ("DTREO", "DHUY", "PAY", "DM:*", "PH:*", "VCL"):
		dung("vgbGo có nhánh %s" % k, k in co)
	dung("vgbGo không có nhánh cho khoá bịa ra", "KHOA-BIA-RA" not in co)


# ---------------------------------------------------------------------------
# PHAN HE va DIA CHI THEO NAC (v292, 24/08/2026)
#
# Anh Viet: *"anh bam vao phan he ke toan, url khong co ke-toan. Ma bam vao
# hoa don mua thi co duoi url hoa-don-mua, nhung back ve thi trang van mang
# duoi hoa-don-mua. Em ra soat va fix triet de cho tat ca cac man."*
#
# Hai hong khac nhau, nen phai co hai bo hang rao khac nhau:
#   1. O LON khong di qua vgbGo, nen khong qua bang duong dan.
#   2. Dia chi la mot hieu ung phu bam vao luc bam nut, khong phai thuoc
#      tinh cua nac trong chong man hinh, nen lui thi khong co gi de lui.
# ---------------------------------------------------------------------------


TEP_KHUNG = os.path.join(GOC, "vagabond", "public", "js", "bep", "01-khung-app.js")
TEP_VD = os.path.join(GOC, "vagabond", "public", "js", "bep", "12-van-don.js")


def _khung():
	return io.open(TEP_KHUNG, encoding="utf-8").read()


def _nhom_trong_js():
	"""Doc truong `k` cua tung phan he trong VGB_NHOM, thang tu ma nguon JS."""
	src = _js()
	i = src.index("var VGB_NHOM = [")
	than = src[i:src.index("\n];", i)]
	return [m for m in re.findall(r"\{\s*k:\s*'([A-Za-z0-9_]+)'", than)]


@ca("phân hệ: bảng PHAN_HE phải khớp từng khoá với VGB_NHOM bên JavaScript")
def _():
	"""Lệch một khoá là ô lớn đó bấm vào không ra gì.

	`vgbGo('PH:KT')` tra khoá `KT` trong VGB_NHOM. Khoá bên Python có mà bên
	JS không có thì địa chỉ `/phan-he-ke-toan` sinh ra nhưng bấm vào ô lại
	rơi vào nhánh trả về rỗng, tức một ô lớn chết lặng.
	"""
	from vagabond.duong_app import PHAN_HE

	js = _nhom_trong_js()
	py = [k for k, _ten in PHAN_HE]
	dung("đọc được VGB_NHOM bên JavaScript", len(js) >= 10)
	la("hai bên cùng số phân hệ", len(py), len(js))
	la("hai bên cùng bộ khoá, cùng thứ tự", py, js)


@ca("phân hệ: mọi phân hệ đều có slug riêng và không đụng màn nào")
def _():
	from vagabond.duong_app import PHAN_HE, TIEN_TO_PHAN_HE, _cap_duong

	cap = list(_cap_duong())
	slug_ph = [s for s, k in cap if k.startswith("PH:")]
	la("đủ slug cho mọi phân hệ", len(slug_ph), len(PHAN_HE))
	dung("mọi slug phân hệ đều mang tiền tố",
		all(x.startswith(TIEN_TO_PHAN_HE + "-") for x in slug_ph))
	# Bon ten phan he TRUNG nguyen van voi ten mot man. Khong co tien to thi
	# bon slug nay nuot mat bon man that.
	khac = [s for s, k in cap if not k.startswith("PH:")]
	dung("không slug phân hệ nào đụng slug màn: " +
		(", ".join(sorted(set(slug_ph) & set(khac))) or "sạch"),
		not (set(slug_ph) & set(khac)))
	# Toan bang khong duoc co slug trung, ke ca sau khi them phan he.
	tat_ca = [s for s, _k in cap]
	trung = sorted({x for x in tat_ca if tat_ca.count(x) > 1})
	dung("toàn bảng không có slug trùng: " + (", ".join(trung) or "sạch"), not trung)


@ca("phân hệ: HÀNG RÀO tiền tố có thật sự cắn không")
def _():
	"""Bỏ tiền tố đi thì bốn phân hệ nuốt mất bốn màn. Tự chứng minh điều đó.

	Hàng rào không cắn còn tệ hơn không có hàng rào, nên ca này dựng lại
	đúng cái bảng SAI rồi đòi nó phải đụng.
	"""
	from vagabond.duong_app import MAN, PHAN_HE, slugify

	ten_man = {slugify(ghi_de or ten) for _k, ten, ghi_de in MAN}
	dung_do = sorted(slugify(ten) for _k, ten in PHAN_HE if slugify(ten) in ten_man)
	dung("bỏ tiền tố thì có phân hệ đụng màn: " + ", ".join(dung_do), len(dung_do) >= 4)
	for x in ("san-xuat", "nhap-kho", "kiem-ke", "bao-cao"):
		dung("phân hệ '%s' sẽ đụng nếu bỏ tiền tố" % x, x in dung_do)


@ca("phân hệ: vgbGo có nhánh tiền tố PH: và ô lớn đi qua vgbGo")
def _():
	"""Ô lớn gọi thẳng go() là bỏ qua CỬA DUY NHẤT đặt địa chỉ.

	Đúng lỗi anh Việt báo 24/08: `if (nh) go(function () { scrNhom(nh); })`.
	"""
	src = _js()
	dung("vgbGo có nhánh tiền tố PH:", "k.indexOf('PH:') === 0" in src)
	dung("vgbGo có nhánh cho Việc cần làm", "k === 'VCL'" in src)
	dung("ô lớn đi qua vgbGo chứ không go() thẳng", "vgbGo('PH:' + nh.k)" in src)
	dung("ô Việc cần làm cũng đi qua vgbGo", "vgbGo('VCL')" in src)
	dung("không còn chỗ nào gọi go(scrNhom) thẳng từ trang chủ",
		"if (nh) go(function () { scrNhom(nh); });" not in src)


@ca("địa chỉ: mỗi nấc trong chồng màn hình giữ slug của chính nó")
def _():
	"""Ba chỗ làm chồng đổi đều phải cập nhật S.duong và áp lại địa chỉ.

	Thiếu một chỗ là địa chỉ lệch khỏi màn đang xem, và người dùng F5 sẽ ra
	một màn khác hẳn.
	"""
	k = _khung()
	dung("khung app khai chồng địa chỉ S.duong", "S.duong = []" in k)
	dung("go() đẩy slug vào chồng địa chỉ", "S.duong.push(" in k)
	dung("back() cắt chồng địa chỉ", "S.duong.pop()" in k)
	dung("reset() dựng lại chồng địa chỉ", "S.duong = [slug]" in k)
	dung("go/back/reset đều áp lại địa chỉ", k.count("vgbApNac()") >= 3)

	# popstate co HAI duong lui: duong thang, va duong hoi lai khi dang soan
	# phieu do. Ca hai deu phai cat chong dia chi, nen dem chu khong chi hoi
	# "co xuat hien khong" - thieu mot duong thi chuoi van con o duong kia va
	# ca kiem xanh gia. Da thu lai bang tay: bo mot duong ma ca kiem khong do.
	vd = io.open(TEP_VD, encoding="utf-8").read()
	la("popstate cắt chồng địa chỉ ở CẢ HAI đường lui",
		vd.count("S.duong.length = d + 1"), 2)
	la("cả hai đường lui đều áp lại địa chỉ", vd.count("vgbApNac()"), 2)


@ca("địa chỉ: HÀNG RÀO thứ tự pushState có cắn không")
def _():
	"""Đây là nguyên nhân THẬT của lỗi Back mang địa chỉ cũ, phải canh riêng.

	Bản cũ đổi địa chỉ TRƯỚC rồi mới pushState:

	    vgbDatDuong(k);   // replaceState: ghi đè địa chỉ của mốc CHA
	    go(scrHdMua);     // pushState(location.href): mốc con cùng địa chỉ

	replaceState ghi đè địa chỉ của chính mốc đang đứng, tức mốc của màn cha.
	Nên sau một lần bấm, cả hai mốc đều mang `/hoa-don-mua`.

	Bản mới phải pushState TRƯỚC, rồi mới áp địa chỉ cho mốc vừa đẩy.
	"""
	k = _khung()
	i = k.index("function go(fn, replace) {")
	than = k[i:k.index("\nfunction back()", i)]
	vt_push = than.index("history.pushState(")
	vt_ap = than.index("vgbApNac()")
	dung("go() đẩy mốc TRƯỚC rồi mới áp địa chỉ", vt_push < vt_ap)
	# Ham doi dia chi cu khong duoc con ai goi nua.
	dung("không còn ai gọi vgbDatDuong", "vgbDatDuong(" not in _js())


@ca("địa chỉ: khoá màn sắp mở chỉ dùng được MỘT lần")
def _():
	"""Khoá dính lại sẽ đặt sai địa chỉ cho một màn hoàn toàn khác.

	Nhánh nào của vgbGo không gọi go() - ví dụ nhánh toast báo màn chưa dựng
	- thì khoá còn nguyên, và lần go() kế tiếp, dù của màn nào, cũng nhận
	đúng khoá đó. Nên vgbGo phải xoá khoá trong finally.
	"""
	src = _js()
	i = src.index("function vgbGo(k) {")
	than = src[i:src.index("\nfunction vgbNhomTheoKhoa(", i)] if "\nfunction vgbNhomTheoKhoa(" in src[i:] else src[i:]
	than = than[:than.index("\n}\n")] if "\n}\n" in than else than
	dung("vgbGo đặt khoá", "VGB_KHOA_MO = k" in than)
	dung("vgbGo xoá khoá trong finally", "finally" in than and "VGB_KHOA_MO = ''" in than)
	# Ham doc khoa cung phai tu xoa, de mot go() khong an khoa cua go() sau.
	j = src.index("function vgbSlugSapMo() {")
	than2 = src[j:src.index("\n}", j)]
	dung("vgbSlugSapMo xoá khoá ngay khi đọc", "VGB_KHOA_MO = ''" in than2)


@ca("địa chỉ: đọc địa chỉ lúc nạp trang, không đọc lại sau khi reset")
def _():
	"""reset() nay có đổi địa chỉ, nên đọc location.pathname muộn là đọc trượt.

	__boot gọi reset(scrHome) TRƯỚC vgbMoTheoDiaChi. Nếu vgbMoTheoDiaChi còn
	đọc location.pathname thì lúc đó địa chỉ đã bị reset ghi đè thành /bep,
	và F5 tại /hoa-don-mua sẽ ra trang chủ - đúng lỗi đã sửa ở v288.
	"""
	src = _js()
	dung("có chụp địa chỉ lúc nạp trang", "var VGB_DIA_NAP = String(location.pathname" in src)
	i = src.index("function vgbMoTheoDiaChi() {")
	than = src[i:src.index("\n}", i)]
	dung("vgbMoTheoDiaChi đọc bản chụp", "VGB_DIA_NAP" in than)
	dung("vgbMoTheoDiaChi KHÔNG đọc lại location.pathname", "location.pathname" not in than)


# ---------------------------------------------------------------------------
# Cac ca duoi day giu nguyen tu v284-v287: noi dung chuyen khoan, ho so thanh
# toan, va dinh tuyen ten mien. Chung khong lien quan toi bang duong dan
# nhung van o chung tep tu dau, doi tep khac se lam git diff kho doc.
# ---------------------------------------------------------------------------

@ca("noi dung chuyen khoan: ma ho so phai dung DAU chuoi")
def _():
	# Anh Viet 23/08/2026 de nghi dat MA PHIEU o CUOI. Da doi lai va day la
	# ly do, dung dao lai: ngan hang cat noi dung o DUOI khi vuot han muc
	# (quanh 90 ky tu). Dat ma o cuoi thi ho so nhieu hoa don la mat ma, ma
	# ma chinh la thu _sepay_theo_ma_app do de tu khop tien da chi. Mat ma
	# thi nut "Do SePay" im lang bao chua chuyen trong khi tien da di.
	import types

	from vagabond import ho_so_tt as t

	D = types.SimpleNamespace
	doc = D(name="APP.26.08.011", loai=t.LOAI_NCC,
		ten_nhan="CONG TY CO PHAN GOURMET PARTNER VIET NAM", ten_ncc="", nha_cung_cap="",
		dong=[D(so_hd_ncc="26957", hoa_don=None), D(so_hd_ncc="26958", hoa_don=None)])
	nd = t._noi_dung_ck(doc)
	dung("mã hồ sơ nằm ngay đầu chuỗi", nd.startswith("VAGABOND APP.26.08.011"))
	dung("có số hoá đơn nhà cung cấp", "HD26957" in nd and "HD26958" in nd)
	dung("không vượt trần %d ký tự" % t.DAI_ND_CK, len(nd) <= t.DAI_ND_CK)
	dung("không còn dấu tiếng Việt", not re.search(r"[^\x00-\x7f]", nd))

	# Ca thuc te: ho so nhieu hoa don, ten nha cung cap dai. Ma VAN phai con.
	doc2 = D(name="APP.26.08.099", loai=t.LOAI_NCC,
		ten_nhan="CONG TY TNHH MOT THANH VIEN THUONG MAI DICH VU XUAT NHAP KHAU ABC",
		ten_ncc="", nha_cung_cap="",
		dong=[D(so_hd_ncc=str(90000 + i), hoa_don=None) for i in range(12)])
	nd2 = t._noi_dung_ck(doc2)
	dung("hồ sơ 12 hoá đơn vẫn giữ được mã ở đầu", nd2.startswith("VAGABOND APP.26.08.099"))
	dung("hồ sơ 12 hoá đơn vẫn không vượt trần", len(nd2) <= t.DAI_ND_CK)
	# Chinh la phep thu chung minh vi sao khong dat ma o cuoi: chuoi DAI hon
	# tran nen phan duoi bi cat. Neu ma nam duoi thi chinh ma la phan mat.
	day_du = "VAGABOND APP.26.08.099 THANH TOAN " + " ".join(
		"HD%d" % (90000 + i) for i in range(12))
	dung("chuỗi đầy đủ dài hơn trần, tức là có bị cắt thật",
		len(day_du) > t.DAI_ND_CK)
	dung("tên nhà cung cấp là phần bị cắt, không phải mã", "ABC" not in nd2)


@ca("ho so: chi keo chung tu DA GHI SO, bo nhap va bo da huy")
def _():
	from vagabond import ho_so_tt as t

	src = io.open(os.path.join(GOC, "vagabond", "ho_so_tt.py"), encoding="utf-8").read()
	dung("có hàm lọc theo docstatus", "def _da_ghi_so(" in src)
	dung("lọc đúng docstatus 1", '"docstatus": 1' in src)
	# Phai ap cho CA don mua lan phieu nhap kho.
	than = src[src.index("def _ho_so_chung_tu("):]
	than = than[:than.index("def _dinh_kem(")]
	dung("áp cho phiếu nhập kho", '_da_ghi_so("Purchase Receipt"' in than)
	dung("áp cho đơn mua hàng", '_da_ghi_so("Purchase Order"' in than)
	# Ham giu nguyen thu tu, va rong vao thi rong ra.
	la("rỗng vào thì rỗng ra", t._da_ghi_so("Purchase Receipt", []), [])


@ca("ten mien: chi ba mien duoc khai moi bi ap luat, con lai di duong cu")
def _():
	# DAY LA CHOT AN TOAN QUAN TRONG NHAT cua tep ten_mien.py. Dat luat rong
	# roi chan nham la KHOA CUA CHINH MINH: khong vao duoc Desk de sua lai.
	# Ten mien mac dinh cua Frappe Cloud phai luon di duoc, vi do la duong
	# duy nhat con lai khi ten mien that hong.
	from vagabond.duong_app import DUONG
	from vagabond.ten_mien import dich_chuyen_huong

	for host in ("vagabond.s.frappe.cloud", "erpnext-qwy-acq.s.frappe.cloud",
			"localhost", "127.0.0.1", "", None, "thevagabondpatisserie.com"):
		for d in ("/app", "/bep", "/banh", "/app/user", "/"):
			la("miền lạ %r đường %s không bị đụng" % (host, d),
				dich_chuyen_huong(host, d, tuple(DUONG)), "")


@ca("ten mien: khong bao gio chan api, assets, files, dang nhap")
def _():
	# Chan may duong nay la app TRANG MAN: no goi API va tai tai nguyen qua
	# chinh ten mien cua no.
	#
	# TRUNG THUC VE CA KIEM NAY: da thu xoa "/api/" khoi CHUA_RA va ca kiem
	# VAN XANH. Ly do la luat mac dinh cua dich_chuyen_huong() da la CHO DI
	# TIEP khi duong khong thuoc nhom nao. Nghia la hom nay CHUA_RA chua ganh
	# viec gi, cai dang bao ve la luat mac dinh do.
	#
	# Van giu ca hai, va van giu ca kiem nay: ngay nao co nguoi doi luat mac
	# dinh thanh CHAN (vi du "mien app chi cho di /bep va cac slug"), thi
	# CHUA_RA thanh hang rao that va ca kiem nay bat dau can. Do dung la kieu
	# sua de gay ra su co lon nhat o day.
	from vagabond.duong_app import DUONG
	from vagabond.ten_mien import MIEN_APP, MIEN_DESK, MIEN_KHACH, dich_chuyen_huong

	duong = ("/api/method/x", "/assets/vagabond/js/app_bep.js", "/files/a.png",
		"/private/files/b.pdf", "/login", "/favicon.ico", "/manifest.json",
		"/sw.js", "/socket.io/x")
	for m in (MIEN_APP, MIEN_DESK, MIEN_KHACH):
		for d in duong:
			la("%s không chặn %s" % (m, d), dich_chuyen_huong(m, d, tuple(DUONG)), "")


@ca("ten mien: moi mien vao dung cua cua minh thi di tiep, vao nham thi da sang")
def _():
	from vagabond.duong_app import DUONG
	from vagabond.ten_mien import MIEN_APP, MIEN_DESK, MIEN_KHACH, dich_chuyen_huong

	D = tuple(DUONG)
	# Dung cua.
	la("app vào /bep", dich_chuyen_huong(MIEN_APP, "/bep", D), "")
	la("app vào màn con", dich_chuyen_huong(MIEN_APP, "/don-da-huy", D), "")
	la("erp vào Desk", dich_chuyen_huong(MIEN_DESK, "/app/user", D), "")
	la("order vào trang bánh", dich_chuyen_huong(MIEN_KHACH, "/banh", D), "")
	la("order vào trang thanh toán đơn", dich_chuyen_huong(MIEN_KHACH, "/tt", D), "")
	# Nham cua.
	la("app vào Desk thì về app", dich_chuyen_huong(MIEN_APP, "/app", D), "/bep")
	la("app vào trang khách thì về app", dich_chuyen_huong(MIEN_APP, "/banh", D), "/bep")
	la("erp vào app thì về Desk", dich_chuyen_huong(MIEN_DESK, "/bep", D), "/app")
	la("order vào app thì về trang bánh", dich_chuyen_huong(MIEN_KHACH, "/bep", D), "/banh")
	la("order vào Desk thì về trang bánh", dich_chuyen_huong(MIEN_KHACH, "/app", D), "/banh")
	# Goc cua tung mien.
	la("app vào gốc", dich_chuyen_huong(MIEN_APP, "/", D), "/bep")
	la("erp vào gốc", dich_chuyen_huong(MIEN_DESK, "/", D), "/app")
	la("order vào gốc", dich_chuyen_huong(MIEN_KHACH, "/", D), "/banh")


@ca("ten mien: chi co MOT khai bao update_website_context trong hooks")
def _():
	# Khai hai lan trong cung mot tep thi lan sau DE lan truoc va hook kia im
	# lang khong chay. Python khong bao gi ca, ca kiem khong bao gi ca, chi lo
	# khi co nguoi vao nham cua ma khong bi da sang.
	src = io.open(os.path.join(GOC, "vagabond", "hooks.py"), encoding="utf-8").read()
	la("số lần khai update_website_context", src.count("\nupdate_website_context = "), 1)
	dung("định tuyến tên miền nằm trong danh sách đó",
		"vagabond.hooks._dinh_tuyen_ten_mien" in src)
	dung("hook cũ og_theo_ten_mien vẫn còn, không bị gạt ra",
		"vagabond.lib.og_theo_ten_mien" in src)


@ca("ho so: mot hoa don khong duoc nam trong hai ho so con song")
def _():
	# Hai ho so cung chua mot hoa don thi cung di qua hai cap duyet va cung
	# duoc chuyen tien, vi moi ho so nhin rieng ra deu hop le. Khong ai doi
	# chieu cheo giua cac ho so bang mat.
	from vagabond import ho_so_tt as t

	src = io.open(os.path.join(GOC, "vagabond", "ho_so_tt.py"), encoding="utf-8").read()
	dung("có hàm chặn", "def _chan_hoa_don_trung(" in src)
	# Phai chan o CA BA luong lap ho so, thieu mot luong la thung mot lo.
	la("số luồng có gọi chốt chặn", src.count("\t_chan_hoa_don_trung("), 3)

	# Ho so Tu choi va Huy KHONG duoc chan: hoa don trong do phai dung lai
	# duoc, neu khong thi mot lan lap nham la hoa don ket vinh vien.
	dung("trạng thái còn sống không gồm Từ chối", t.TT_TU_CHOI not in t.TT_CON_SONG)
	dung("trạng thái còn sống không gồm Huỷ", t.TT_HUY not in t.TT_CON_SONG)
	dung("trạng thái còn sống có Đã thanh toán", t.TT_DA_TRA in t.TT_CON_SONG)
	dung("trạng thái còn sống có Nháp", t.TT_NHAP in t.TT_CON_SONG)


@ca("duong app: phai CHO trang chu ve xong roi moi mo man theo dia chi")
def _():
	# Loi that, do tren site sau khi deploy v284 ngay 23/08/2026: F5 tai
	# /don-da-huy van ra trang chu.
	#
	# Nguyen nhan: scrHome la ham `async`. No ve tam mot cai dong ho cat, roi
	# `await` du lieu, xong moi ve that. __boot goi reset(scrHome) roi mo
	# NGAY man theo dia chi, nhung scrHome ve that MUON hon va de len man vua
	# mo. Dia chi dung, man hinh sai.
	#
	# Cach sua: render() tra ve promise cua ham man hinh thay vi nuot di, va
	# __boot `await` no truoc khi goi vgbMoTheoDiaChi.
	#
	# Bai hoc chung: trong app nay ham man hinh phan lon la async, nen bat cu
	# cho nao ve hai man lien tiep deu phai cho man truoc ve xong.
	khung = io.open(os.path.join(GOC, "vagabond", "public", "js", "bep",
		"01-khung-app.js"), encoding="utf-8").read()
	vd = io.open(os.path.join(GOC, "vagabond", "public", "js", "bep",
		"12-van-don.js"), encoding="utf-8").read()

	dung("render trả về promise của hàm màn hình, không nuốt đi",
		"if (f) return f();" in khung)
	dung("reset trả lại kết quả của render", "return render();" in khung)
	# CA HAI nhanh vao man chinh deu phai cho, bo mot nhanh la nguoi dang
	# nhap kieu do van bi vang ve trang chu.
	la("số nhánh có await reset(scrHome)", vd.count("await reset(scrHome)"), 2)
	dung("không còn nhánh nào gọi reset(scrHome) mà không chờ",
		"adopt(real); reset(scrHome);" not in vd)
	# vgbMoTheoDiaChi phai nam SAU await, khong nam truoc.
	i = vd.index("async function __boot()")
	than = vd[i:vd.index("window.addEventListener('popstate'")]
	for k in range(than.count("vgbMoTheoDiaChi()")):
		vi = [m for m in range(len(than)) if than.startswith("vgbMoTheoDiaChi()", m)][k]
		truoc = than[:vi]
		dung("lần gọi thứ %d nằm sau một await reset(scrHome)" % (k + 1),
			"await reset(scrHome)" in truoc)
