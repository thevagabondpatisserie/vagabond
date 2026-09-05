# -*- coding: utf-8 -*-
"""Ca kiểm cho issue #205: sửa cách trang đặt bánh hiện ngày, tồn kho và
bước chọn lịch trong giỏ hàng.

Trang đặt bánh là vagabond/trang/banh.html, một tệp HTML kèm JavaScript. Bộ
kiểm này KHÔNG dò chuỗi trong mã nguồn để đoán hành vi, vì cách đó từng cho
màu xanh giả: lời gọi nằm sau một câu return chết thì tìm chuỗi vẫn thấy.

Ở đây cắt thẳng các phép THUẦN ra khỏi trang rồi CHẠY chúng bằng node, đúng
lối mà thu_qr_xhd_cfd_push.py đã dùng. Phần chạm DOM thì chỉ neo bằng vài
phép đọc mã nguồn, và đã kiểm tay trên trang thật, ghi lại trong hồ sơ bàn
giao của PR.

Ba việc của #205:
1. Ngày hiện ra "6th 9" vì chữ th viết tắt của tháng đứng ngay sau số ngày.
2. Số tồn kho thô lọt ra ngoài giao diện, có chỗ hiện "Còn 1092".
3. Bước chọn ngày giờ bắt khách làm hai lần, mà hai bộ chọn còn lệch miền
   ngày: ngoài 14 ngày, trong giỏ hàng 10 ngày.
"""

import io
import json
import os
import re
import subprocess

from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	return os.path.dirname(
		os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	)


def _trang():
	return io.open(
		os.path.join(_goc(), "vagabond", "trang", "banh.html"), encoding="utf-8"
	).read()


TRANG = _trang()


def _node(ma):
	"""Chạy một đoạn JavaScript bằng node, trả về stdout đã cắt khoảng trắng."""
	r = subprocess.run(["node", "-e", ma], capture_output=True, text=True, timeout=20)
	if r.returncode != 0:
		raise AssertionError("node lỗi: " + (r.stderr or "").strip()[:400])
	return (r.stdout or "").strip()


def _ham(ten):
	"""Cắt nguyên một hàm `function ten(...) {...}` ở đầu dòng ra khỏi trang."""
	m = re.search(r"\nfunction %s\([^)]*\) ?\{.*?\n\}" % re.escape(ten), TRANG, re.S)
	if not m:
		raise AssertionError("không thấy hàm %s trong banh.html" % ten)
	return m.group(0)


def _than(ten):
	"""Thân của một hàm, để neo vài điều về phần chạm DOM."""
	return _ham(ten)


DAYS_JS = (
	"const DAYS=['Chủ nhật','Thứ 2','Thứ 3','Thứ 4','Thứ 5','Thứ 6','Thứ 7'];"
)


def _nguong():
	"""Lấy NGƯỠNG tồn kho THẬT trong trang, không tự chế lại trong bộ kiểm.

	Bản đầu của tệp này tự tiêm `var NGUONG_TON=10;` vào đoạn chạy node. Làm
	vậy là bộ kiểm tự trả lời câu hỏi của chính nó: đổi ngưỡng trong trang lên
	10000 để số tồn thô lọt ra lại thì bộ kiểm vẫn xanh. Đã đột biến và bắt
	được đúng lỗi đó ngày 06/09, nên nay đọc thẳng từ trang.
	"""
	m = re.search(r"var NGUONG_TON *= *(\d+) *;", TRANG)
	if not m:
		raise AssertionError("không thấy NGUONG_TON trong banh.html")
	return "var NGUONG_TON=" + m.group(1) + ";"


# ==================================================== 1. NHÃN TỒN KHO


@ca("#205 nhan ton: tren 10 thi khong khoe so nua")
def _ton_nhieu():
	ra = _node(_nguong() + _ham("nhanTon") + """
console.log(JSON.stringify([nhanTon(11),nhanTon(241,'phần'),nhanTon(1393),nhanTon(1092)]));
""")
	la("deu la Con hang", json.loads(ra),
		["Còn hàng", "Còn hàng", "Còn hàng", "Còn hàng"])


@ca("#205 nhan ton: tu 1 toi 10 thi noi ro con may cai")
def _ton_it():
	ra = _node(_nguong() + _ham("nhanTon") + """
console.log(JSON.stringify([nhanTon(1,'bánh'),nhanTon(2,'bánh'),nhanTon(10,'bánh'),nhanTon(10)]));
""")
	la("noi ro so con lai", json.loads(ra),
		["Chỉ còn 1 bánh", "Chỉ còn 2 bánh", "Chỉ còn 10 bánh", "Chỉ còn 10"])


@ca("#205 nhan ton: bang 0 hay am thi Tam het")
def _ton_het():
	ra = _node(_nguong() + _ham("nhanTon") + """
console.log(JSON.stringify([nhanTon(0),nhanTon(0,'bánh'),nhanTon(-3)]));
""")
	la("Tam het", json.loads(ra), ["Tạm hết", "Tạm hết", "Tạm hết"])


@ca("#205 nhan ton: chua tai xong hay loi thi IM, khong doan bua")
def _ton_chua_biet():
	# Doan bua chieu nao cung hai: bao con hang ma het thi khach dat hut,
	# bao het ma con thi minh mat don.
	ra = _node(_nguong() + _ham("nhanTon") + """
console.log(JSON.stringify([nhanTon(null),nhanTon(undefined),nhanTon(''),nhanTon('abc'),nhanTon(NaN)]));
""")
	la("deu la chuoi rong", json.loads(ra), ["", "", "", "", ""])


@ca("#205 moi cho hien ton deu goi nhanTon, khong ai tu ghep chuoi rieng")
def _ton_dung_chung():
	# Ba cho: the banh thuong, luoi hang theo mua, va sheet chi tiet hang mua.
	dung("the banh thuong goi nhanTon", "nhanTon(TODAY[s.id]" in TRANG)
	dung("the banh dat truoc goi nhanTon", "nhanTon(TRUOC[s.id]" in TRANG)
	dung("luoi hang theo mua goi nhanTon", "nhanTon(m.con,'phần')" in TRANG)
	# Khong con cho nao ghep so tho vao nhan hien ra man hinh.
	dung("khong con ghep 'Con '+m.con o luoi mua",
		"(het?'Hết hàng':'Còn '+m.con)" not in TRANG)
	dung("khong con ghep ' · còn '+TRUOC", "' · còn '+TRUOC[s.id]" not in TRANG)


@ca("#205 so ton THAT van duoc giu de chan khi them qua so luong")
def _ton_that_van_con():
	# Doi nhan hien thi thi duoc, nhung phep chan gioi han van phai dung so
	# that, va chot chan that van nam o may chu.
	dung("van so sanh voi m.con", "daCoTrongGio(ma)>=m.con" in TRANG)


# ==================================================== 2. NHÃN NGÀY


@ca("#205 nhan ngay: hom nay, ngay mai, roi den thu may")
def _ngay_ten():
	ra = _node(DAYS_JS + _ham("nhanNgay") + """
var moc=new Date(2026,8,6);
console.log(JSON.stringify([nhanNgay(0,moc,DAYS),nhanNgay(1,moc,DAYS),nhanNgay(2,moc,DAYS)]));
""")
	la("ten ngay", json.loads(ra), [
		{"ten": "Hôm nay", "ngay": "06/09"},
		{"ten": "Ngày mai", "ngay": "07/09"},
		{"ten": "Thứ 3", "ngay": "08/09"},
	])


@ca("#205 nhan ngay: ngay va thang luon du hai chu so, ngan cach bang gach cheo")
def _ngay_dinh_dang():
	ra = _node(DAYS_JS + _ham("nhanNgay") + """
var moc=new Date(2026,0,5);
console.log(JSON.stringify([nhanNgay(0,moc,DAYS).ngay,nhanNgay(4,moc,DAYS).ngay]));
""")
	la("co so 0 dung dau", json.loads(ra), ["05/01", "09/01"])


@ca("#205 nhan ngay: qua cuoi thang va cuoi nam van dung")
def _ngay_qua_moc():
	ra = _node(DAYS_JS + _ham("nhanNgay") + """
var a=new Date(2026,8,28);   /* 28/09, +3 ngay la sang thang 10 */
var b=new Date(2026,11,30);  /* 30/12, +3 ngay la sang nam sau */
var c=new Date(2028,1,27);   /* nam nhuan: 27/02/2028, +2 ngay la 29/02 */
console.log(JSON.stringify([nhanNgay(3,a,DAYS).ngay,nhanNgay(3,b,DAYS).ngay,nhanNgay(2,c,DAYS).ngay]));
""")
	la("khong lech moc", json.loads(ra), ["01/10", "02/01", "29/02"])


@ca("#205 khong con chu th dinh sau so ngay o bat cu bo chon nao")
def _het_th():
	than = _than("railHtml")
	dung("khong con small th", "<small>th " not in than)
	dung("dung nhanNgay", "nhanNgay(i,t,DAYS)" in than)
	dung("khong con getMonth ghep thang tay", "d.getMonth()+1}</small>" not in than)
	# dmy() la nhan hien thi chung, phai dung gach cheo cho dong bo.
	dung("dmy dung dau gach cheo", '"/"+String(d.getMonth()+1)' in TRANG)
	dung("dmy khong con dau cham", '"."+String(d.getMonth()+1)' not in TRANG)


@ca("#205 chuoi ngay hien ra KHONG duoc dung lam du lieu gui don")
def _khong_lay_nhan_lam_du_lieu():
	# Ngay gui len may chu van do mocGioNhan() tinh, khong phai chuoi man hinh.
	dung("payload dung mocGioNhan", "const ngayNhan=mocGioNhan();" in TRANG)
	dung("payload gui ngayNhan", "ngay_nhan:ngayNhan" in TRANG)
	dung("payload khong dung nhanNgay", "ngay_nhan:nhanNgay" not in TRANG)
	dung("payload khong dung dmy", "ngay_nhan:dmy" not in TRANG)


# ==================================================== 3. BƯỚC CHỌN LỊCH


@ca("#205 chi tom tat khi khach THAT SU da chon, chua bam Thay doi, gio con kip")
def _quyet_dinh_tom_tat():
	ra = _node(_ham("hienTomTatLich") + """
var r=[];
r.push(hienTomTatLich(true,  false, true ));  /* da chon, chua doi, gio kip */
r.push(hienTomTatLich(false, false, true ));  /* chua chon bao gio */
r.push(hienTomTatLich(true,  true,  true ));  /* dang bam Thay doi */
r.push(hienTomTatLich(true,  false, false));  /* gio het kip */
r.push(hienTomTatLich(false, true,  false));
console.log(JSON.stringify(r));
""")
	la("chi truong hop dau tien moi tom tat", json.loads(ra),
		[True, False, False, False, False])


@ca("#205 gia tri mac dinh cua trang KHONG duoc coi la khach da chon")
def _mac_dinh_khong_phai_da_chon():
	# picked=2 la mac dinh khi mo trang. Neu coi do la da chon thi khach chua
	# bam gi ma gio hang da bao "anh chi da chon ngay X" roi giao nham ngay.
	dung("co co rieng danh dau da chon", "let daChonLich=false;" in TRANG)
	dung("bam ngay moi bat co", "function pick(i){ picked=i; daChonLich=true;" in TRANG)
	dung("bam khung gio cung bat co",
		"function pickSlot(i){ pickedSlot=i; daChonLich=true;" in TRANG)


@ca("#205 hai bo chon ngay phai CUNG mien ngay")
def _cung_mien_ngay():
	# Truoc day ngoai 14 ngay, trong gio hang 10 ngay, nen khach chon ngay thu
	# 11 toi 14 o ngoai thi vao gio hang khong sua lai duoc.
	so = re.findall(r"railHtml\((\d+),'pick'\)", TRANG)
	la("hai noi goi railHtml", len(so), 2)
	la("cung mot so ngay", len(set(so)), 1)
	la("deu la 14 ngay", so[0], "14")


@ca("#205 bam Thay doi thi bung lai bo chon, va dua con tro vao do")
def _nut_thay_doi():
	dung("co nut Thay doi", 'onclick="doiLich()"' in TRANG)
	than = _than("doiLich")
	dung("mo lai bo chon", "moLich=true" in than)
	dung("ve lai muc 02", "drawCoDate()" in than)
	dung("dua con tro vao ngay dang chon", ".focus()" in than)
	# Mo lai gio hang thi tro ve the tom tat chu khong giu trang thai dang mo.
	dung("mo gio hang thi dong bo chon lai", "moLich=false;" in _than("openCoUI"))


@ca("#205 khung gio het kip thi phai NOI RO, khong lang le doi khung khac")
def _bao_gio_het_kip():
	than = _than("drawCoDate")
	dung("co tinh gio con kip khong", "const hongGio=!slotOk(picked,SLOTS[pickedSlot]);" in than)
	dung("gio hong thi khong tom tat", "hienTomTatLich(daChonLich, moLich, !hongGio)" in than)
	dung("co cau bao cho khach", "không còn kịp nữa" in than)


# ==================================================== 4. NGƯỜI NHẬN VÀ HOÁ ĐƠN


@ca("#205 hai khoi nguoi nhan va hoa don an san, bat moi bung")
def _an_mac_dinh():
	dung("khoi nguoi nhan an", '<div id="otherBlock" style="display:none"' in TRANG)
	dung("khoi hoa don an", '<div id="vatBlock" style="display:none">' in TRANG)
	dung("co khoi tao tat", "other:false" in TRANG and "vat:false" in TRANG)


@ca("#205 tat toggle thi KHONG gui du lieu cu len may chu")
def _tat_thi_khong_gui():
	dung("nguoi nhan gac theo CO.other", "nguoi_nhan: CO.other ?" in TRANG)
	dung("tat thi gui null", "CO.other ? {ho_ten:" in TRANG and ": null," in TRANG)
	dung("hoa don gac theo CO.vat", "const vat = CO.vat ? {" in TRANG)


@ca("#205 ba toggle doc lap nhau, nguoi khac nhan khong keo theo bo hoa don")
def _doc_lap():
	than = _than("tgl")
	dung("moi lan chi lat dung mot co", "CO[k]=!CO[k];" in than)
	dung("khong co cho nao lat co khac", "CO.gift=" not in than and "CO.vat=" not in than)


@ca("#205 bung thu co bao cho trinh doc man hinh va co dua con tro vao")
def _tro_giup_ban_phim():
	dung("nut nguoi nhan khai aria", 'id="c-other" onclick="tgl(\'other\')" aria-expanded="false"' in TRANG)
	dung("nut hoa don khai aria", 'id="c-vat" onclick="tgl(\'vat\')" aria-expanded="false"' in TRANG)
	than = _than("tgl")
	dung("cap nhat lai aria khi lat", "setAttribute('aria-expanded'" in than)
	dung("dua con tro vao o dau tien", "o.focus()" in than)


@ca("#205 thu lai KHONG duoc xoa chu khach vua go")
def _khong_xoa_chu():
	than = _than("tgl")
	dung("khong dat lai gia tri o nhap", ".value=''" not in than)
	dung("khong goi reset", ".reset()" not in than)


@ca("#205 nguong ton phai giu o 10 dung nhu anh Viet chot trong issue")
def _nguong_dung_muc():
	# Ngưỡng nằm trong trang chứ không nằm trong bộ kiểm. Nếu ai nâng ngưỡng
	# lên cao thì số tồn thô lại lọt ra giao diện, nên chốt luôn con số ở đây.
	m = re.search(r"var NGUONG_TON *= *(\d+) *;", TRANG)
	dung("co khai bao nguong", bool(m))
	la("nguong la 10", int(m.group(1)) if m else 0, 10)
