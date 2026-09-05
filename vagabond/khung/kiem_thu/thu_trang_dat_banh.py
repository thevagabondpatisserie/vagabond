# -*- coding: utf-8 -*-
"""Ca kiểm cho issue #205: sửa cách trang đặt bánh hiện ngày, tồn kho và
bước chọn lịch trong giỏ hàng.

Trang đặt bánh là vagabond/trang/banh.html, một tệp HTML kèm JavaScript. Bộ
kiểm này KHÔNG dò chuỗi trong mã nguồn để đoán hành vi, vì cách đó từng cho
màu xanh giả: lời gọi nằm sau một câu return chết thì tìm chuỗi vẫn thấy.

Ở đây làm hai tầng:

1. Cắt thẳng các phép THUẦN ra khỏi trang rồi CHẠY chúng bằng node, đúng lối
   mà thu_qr_xhd_cfd_push.py đã dùng.
2. NẠP TOÀN BỘ mã của trang vào một bối cảnh node, với ĐỒNG HỒ ĐIỀU KHIỂN
   ĐƯỢC và DOM giả lập (gia_lap_trang.js), rồi chạy thật các chuỗi thao tác
   của khách và đọc lại kết quả.

Tầng 2 là bắt buộc, không phải cho đẹp. Vòng một của #205 chỉ có tầng 1 cộng
với vài phép dò chuỗi, và Codex bắt được ba lỗi mà cách đó KHÔNG THỂ thấy:
đồng hồ đọc sai thời điểm, ngày lệch sau nửa đêm, và bấm một ngày đã bị coi
là chốt luôn cả khung giờ mặc định. Dò chuỗi thấy đủ mọi lời gọi mà vẫn xanh.

Kiểm giao diện, kích thước và bố cục thì không làm ở đây được: node không
tính CSS. Phần đó kiểm bằng trình duyệt thật, ghi trong hồ sơ bàn giao PR.

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


def _chay(gio, kich_ban):
	"""Nạp TOÀN BỘ mã của trang vào node với đồng hồ đặt ở `gio`, chạy kịch
	bản, rồi đọc lại JSON mà kịch bản in ra.

	Trong kịch bản có sẵn: EL('#id') lấy phần tử, TUA(phút) và DAT(iso) chỉnh
	đồng hồ, GHI.goiMang là các lời gọi mạng đã bị chặn lại, RA(obj) in kết
	quả. Mọi hàm của trang gọi thẳng được.
	"""
	js = os.path.join(_goc(), "vagabond", "khung", "kiem_thu", "gia_lap_trang.js")
	trang = os.path.join(_goc(), "vagabond", "trang", "banh.html")
	r = subprocess.run(
		["node", js, trang, gio, kich_ban],
		capture_output=True, text=True, timeout=60,
	)
	if r.returncode != 0:
		raise AssertionError("gia lập trang lỗi: " + (r.stderr or "").strip()[:600])
	ra = (r.stdout or "").strip()
	if not ra:
		raise AssertionError("kịch bản không in ra gì")
	return json.loads(ra.splitlines()[-1])


I13 = "var i13=SLOTS.findIndex(function(s){return s.from===13;});"
I16 = "var i16=SLOTS.findIndex(function(s){return s.from===16;});"
GIO_HANG = """
CART.push({id:'X1',k:'Test',cm:12,qty:1,adds:[],wish:'',p:100000});
EL('#f-name').value='Nguyen Van A';
EL('#f-phone').value='0931224334';
EL('#f-addr').value='9 Tran Cao Van, Quan 1, TP HCM';
setMode('ship');
"""
DON_GUI = """
function donDaGui(){
  var g=GHI.goiMang.filter(function(x){return x.opt&&x.opt.method==='POST';})[0];
  return g?JSON.parse(JSON.parse(g.opt.body).don):null;
}
"""


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


@ca("#205 sheet chi tiet banh thuong cung KHONG duoc lo so tho ra")
def _sheet_khong_lo_so():
	# Hai cho Codex chi ra o vong mot: dong tong "con X banh" tren dau sheet,
	# va nhan tung co trong sheet. Chay THAT ham renderSheet roi doc lai chu.
	r = _chay("2026-09-06T08:00:00", r"""
var mon=CAKES[0], s0=mon.sizes[0];
var ra=[];
[[0,0],[1,0],[10,0],[11,0],[1393,0],[null,0],[0,5],[0,1393]].forEach(function(c){
  TODAY[s0.id]=c[0]; TRUOC[s0.id]=c[1];
  renderSheet(mon);
  /* Chi doc PHAN NHAN TON: dong tren dau sheet, va cac the <em> trong tung
     co. Khong doc gia tien hay so do, hai thu do von la so that. */
  var tren=EL('#s-avail').innerHTML.replace(/<[^>]*>/g,' ');
  var em=(EL('#s-sizes').innerHTML.match(/<em>[^<]*<\/em>/g)||[])
          .map(function(x){return x.replace(/<[^>]*>/g,'');});
  ra.push({today:c[0], truoc:c[1], tren:tren.replace(/\s+/g,' ').trim(), em:em});
});
RA(ra);
""")
	la("thu du tam muc ton", len(r), 8)
	for d in r:
		nhan = " ".join([d["tren"]] + d["em"])
		# Muc ton THAT khong duoc xuat hien nguyen si, tru khi no nam trong
		# nguong va dung la cau "Chi con X".
		for muc in (d["today"], d["truoc"]):
			if muc in (None, 0) or 0 < muc <= 10:
				continue
			dung("nhan ton khong lo so %s: %s" % (muc, nhan), str(muc) not in nhan)
	la("11 banh thi noi Con hang", "Còn hàng" in " ".join(r[3]["em"]), True)
	la("1393 banh cung chi noi Con hang", "Còn hàng" in " ".join(r[4]["em"]), True)
	la("dong tren dau sheet cung khong khoe so", r[4]["tren"],
		"Có sẵn hôm nay · Còn hàng")
	la("10 banh thi noi ro con 10", "Chỉ còn 10 bánh" in " ".join(r[2]["em"]), True)
	la("chua tai xong thi khong ghi ton", r[5]["em"], [])
	la("het hom nay van dat truoc duoc",
		"Đặt trước · Chỉ còn 5 bánh" in " ".join(r[6]["em"]), True)


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
	# CHAY THAT: vao gio hang, chua bam gi thi phai thay bo chon.
	r = _chay("2026-09-06T08:00:00", """
openCoUI();
RA({tomtat:EL('#c-tomtat').style.display, boChon:EL('#c-chon').style.display});
""")
	la("chua bam gi thi khong tom tat", r["tomtat"], "none")
	la("chua bam gi thi bung bo chon", r["boChon"], "")


@ca("#205 bam RIENG mot ngay chua phai la da chot ca khung gio")
def _bam_ngay_chua_la_chot():
	# Codex bat duoc o vong mot: pick() bat co roi renderRail thu ngay bo chon,
	# ke ca cac nut gio. Khach di thang toi nut gui thi don mang khung gio mac
	# dinh cua trang chu khong phai khung khach chon.
	r = _chay("2026-09-06T08:00:00", """
openCoUI();
var a={tomtat:EL('#c-tomtat').style.display, boChon:EL('#c-chon').style.display};
pick(3);
var b={tomtat:EL('#c-tomtat').style.display, boChon:EL('#c-chon').style.display};
""" + I16 + """
pickSlot(i16);
var c={tomtat:EL('#c-tomtat').style.display, boChon:EL('#c-chon').style.display,
       chu:(EL('#c-tomtat').innerHTML.match(/<b>([^<]*)<\/b>/)||[])[1]};
RA({vao:a, chi_ngay:b, du_ca_hai:c});
""")
	la("chi bam ngay thi bo chon van mo", r["chi_ngay"]["boChon"], "")
	la("chi bam ngay thi chua tom tat", r["chi_ngay"]["tomtat"], "none")
	la("du ca hai thi moi tom tat", r["du_ca_hai"]["tomtat"], "")
	la("du ca hai thi thu bo chon", r["du_ca_hai"]["boChon"], "none")
	la("tom tat ghi dung ngay va khung", r["du_ca_hai"]["chu"], "Thứ 4, 09/09 · 16h - 18h")


@ca("#205 bam RIENG mot khung gio chua phai la da chot ca ngay")
def _bam_gio_chua_la_chot():
	r = _chay("2026-09-06T08:00:00", """
openCoUI();
""" + I16 + """
pickSlot(i16);
RA({tomtat:EL('#c-tomtat').style.display, boChon:EL('#c-chon').style.display});
""")
	la("chua tom tat", r["tomtat"], "none")
	la("bo chon van mo", r["boChon"], "")


@ca("#205 chua chot du lich thi nut gui KHONG duoc goi may chu")
def _chua_chot_thi_khong_gui():
	r = _chay("2026-09-06T08:00:00", GIO_HANG + DON_GUI + """
openCoUI();
GHI.goiMang.length=0;
submitOrder();
var a={goi:GHI.goiMang.filter(function(x){return x.opt&&x.opt.method==='POST';}).length,
       boChon:EL('#c-chon').style.display};
pick(2);""" + I13 + """
pickSlot(i13);
GHI.goiMang.length=0;
submitOrder();
var don=donDaGui();
RA({chua_chot:a, da_chot_goi: don?1:0, ngay_nhan: don?don.ngay_nhan:null});
""")
	la("chua chot thi khong gui don", r["chua_chot"]["goi"], 0)
	la("va bung bo chon ra", r["chua_chot"]["boChon"], "")
	la("chot roi thi gui duoc", r["da_chot_goi"], 1)
	la("gui dung ngay da chon", r["ngay_nhan"], "2026-09-08T13:00:00")


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
	# CHAY THAT co TUA DONG HO. Ban cu cua ca kiem nay chi do chuoi trong ma
	# nguon nen van xanh trong khi loi van con: slotOk doc NOW la ban chup luc
	# tai trang, tab mo lau thi khung da qua van duoc coi la con kip.
	r = _chay("2026-09-06T08:00:00", GIO_HANG + I13 + """
pick(0); pickSlot(i13);
var truoc={tomtat:EL('#c-tomtat').style.display, ok:slotOk(picked,SLOTS[pickedSlot])};
DAT('2026-09-06T14:00:00');   /* de tab mo toi qua gio bat dau */
openCoUI();
RA({truoc:truoc,
    sau_ok: slotOk(picked,SLOTS[pickedSlot]),
    sau_tomtat: EL('#c-tomtat').style.display,
    sau_boChon: EL('#c-chon').style.display,
    loi_nhan: EL('#c-prep').innerHTML});
""")
	la("luc 08h thi khung 13h con kip", r["truoc"]["ok"], True)
	la("va dang hien the tom tat", r["truoc"]["tomtat"], "")
	la("qua 14h thi khung 13h het kip", r["sau_ok"], False)
	la("phai bo the tom tat di", r["sau_tomtat"], "none")
	la("va bung bo chon ra", r["sau_boChon"], "")
	dung("co cau bao cho khach", "không còn kịp nữa" in r["loi_nhan"])


@ca("#205 lich het kip thi nut gui cung phai chan lai")
def _het_kip_thi_chan_gui():
	r = _chay("2026-09-06T08:00:00", GIO_HANG + DON_GUI + I13 + """
pick(0); pickSlot(i13);
DAT('2026-09-06T14:00:00');
GHI.goiMang.length=0;
submitOrder();
RA({goi: GHI.goiMang.filter(function(x){return x.opt&&x.opt.method==='POST';}).length,
    boChon: EL('#c-chon').style.display});
""")
	la("khong gui don voi lich da qua", r["goi"], 0)
	la("bung bo chon de khach chon lai", r["boChon"], "")


@ca("#205 qua nua dem: the tom tat, phi giao va don PHAI cung mot ngay")
def _qua_nua_dem():
	# picked chi la do lech so voi "hom nay", ma "hom nay" doi luc nua dem.
	# 23:59 chon D+2 ra 08/09, 00:01 hom sau payload thanh 09/09 trong khi the
	# tom tat van ghi 08/09. Neo ngay that lai thi hai cho khong the lech.
	r = _chay("2026-09-06T23:59:00", GIO_HANG + DON_GUI + I13 + """
pick(2); pickSlot(i13);
openCoUI();
var truoc={chu:(EL('#c-tomtat').innerHTML.match(/<b>([^<]*)<\/b>/)||[])[1], moc:mocGioNhan()};
DAT('2026-09-07T00:01:00');   /* qua nua dem, khach KHONG cham gi them */
openCoUI();
GHI.goiMang.length=0;
quoteShip();
var url=GHI.goiMang.map(function(g){return g.url;}).join(' ');
var lucGiao=decodeURIComponent((url.match(/luc_giao=([^&]*)/)||[])[1]||'');
GHI.goiMang.length=0;
submitOrder();
var don=donDaGui();
RA({truoc:truoc,
    sau_chu:(EL('#c-tomtat').innerHTML.match(/<b>([^<]*)<\/b>/)||[])[1],
    sau_moc:mocGioNhan(), luc_giao:lucGiao,
    ngay_nhan:don?don.ngay_nhan:null});
""")
	la("truoc nua dem tom tat ghi 08/09", "08/09" in r["truoc"]["chu"], True)
	la("truoc nua dem payload la 08/09", r["truoc"]["moc"], "2026-09-08T13:00:00")
	la("sau nua dem tom tat van 08/09", "08/09" in r["sau_chu"], True)
	la("sau nua dem payload van 08/09", r["sau_moc"], "2026-09-08T13:00:00")
	la("phi giao hoi dung ngay do", r["luc_giao"], "2026-09-08T13:00:00")
	la("don gui dung ngay do", r["ngay_nhan"], "2026-09-08T13:00:00")


@ca("#205 moc gio nhan doc NGAY DA NEO, khong tinh lai tu do lech")
def _moc_doc_ngay_neo():
	# Ca tren mot minh chua du: khi do lech duoc dong bo lai thi tinh nguoc tu
	# do lech VAN ra dung ngay, nen bo mat nhanh doc ngay neo van xanh. Da đột
	# biến và bắt được đúng chỗ đó ngày 06/09. Ở đây gọi mocGioNhan() NGAY sau
	# khi tua đồng hồ, chưa vẽ lại gì cả, để hai cách tính thật sự khác nhau.
	r = _chay("2026-09-06T23:59:00", I13 + """
pick(2); pickSlot(i13);
var truoc=mocGioNhan();
DAT('2026-09-07T00:01:00');   /* KHONG goi openCoUI, khong ve lai gi */
RA({truoc:truoc, picked_van_la:picked, sau:mocGioNhan()});
""")
	la("truoc nua dem la 08/09", r["truoc"], "2026-09-08T13:00:00")
	la("do lech van con nguyen", r["picked_van_la"], 2)
	la("nhung moc gio van neo o 08/09", r["sau"], "2026-09-08T13:00:00")


@ca("#205 chon ngay xa o ngoai roi vao gio hang van sua lai duoc, ba cho khop nhau")
def _chuoi_day_du():
	# Chuoi Codex yeu cau: chon o ngoai, vao gio hang, bam Thay doi, chon ngay
	# thu 12 toi 14, chon khung gio, quay lai. Roi doi chieu the tom tat,
	# luc_giao trong request hoi phi, va ngay_nhan cung the khung gio trong
	# request tao don.
	r = _chay("2026-09-06T08:00:00", GIO_HANG + DON_GUI + I16 + """
var ra=[];
[11,12,13].forEach(function(n){
  pick(n); openCoUI(); doiLich();
  var soNut=(EL('#c-days').innerHTML.match(/class="day /g)||[]).length;
  var dangChon=(EL('#c-days').innerHTML.split('<button').findIndex(function(x){return /class="day on/.test(x);}))-1;
  pick(n); pickSlot(i16);
  closeCoUI(); openCoUI();
  GHI.goiMang.length=0; quoteShip();
  var url=GHI.goiMang.map(function(g){return g.url;}).join(' ');
  var lucGiao=decodeURIComponent((url.match(/luc_giao=([^&]*)/)||[])[1]||'');
  GHI.goiMang.length=0; submitOrder();
  var don=donDaGui();
  ra.push({lech:n, soNut:soNut, dangChon:dangChon,
    tomtat:(EL('#c-tomtat').innerHTML.match(/<b>([^<]*)<\/b>/)||[])[1],
    luc_giao:lucGiao, ngay_nhan:don?don.ngay_nhan:null,
    tag_slot:don?don.tags[0]:null});
  CART.length=0;
  CART.push({id:'X1',k:'Test',cm:12,qty:1,adds:[],wish:'',p:100000});
});
RA(ra);
""")
	la("thu ba ngay xa", len(r), 3)
	for d in r:
		la("gio hang co du 14 nut ngay", d["soNut"], 14)
		la("nut dang chon dung vi tri", d["dangChon"], d["lech"])
		la("phi giao va don cung mot moc", d["luc_giao"], d["ngay_nhan"])
		la("the khung gio la 16h - 18h", d["tag_slot"], 92)
	la("ngay thu 12 la 17/09", r[0]["ngay_nhan"], "2026-09-17T16:00:00")
	la("ngay thu 13 la 18/09", r[1]["ngay_nhan"], "2026-09-18T16:00:00")
	la("ngay thu 14 la 19/09", r[2]["ngay_nhan"], "2026-09-19T16:00:00")


# ==================================================== 4. NGƯỜI NHẬN VÀ HOÁ ĐƠN


@ca("#205 hai khoi nguoi nhan va hoa don an san, bat moi bung")
def _an_mac_dinh():
	dung("khoi nguoi nhan an", '<div id="otherBlock" style="display:none"' in TRANG)
	dung("khoi hoa don an", '<div id="vatBlock" style="display:none">' in TRANG)
	dung("co khoi tao tat", "other:false" in TRANG and "vat:false" in TRANG)


@ca("#205 tat toggle thi KHONG gui du lieu cu len may chu")
def _tat_thi_khong_gui():
	# CHAY THAT: go chu vao hai khoi, tat ca hai, roi doc PAYLOAD that.
	r = _chay("2026-09-06T08:00:00", GIO_HANG + DON_GUI + I13 + """
tgl('other');
EL('#f-rname').value='Chi Lan'; EL('#f-rphone').value='0900000000';
tgl('vat');
EL('#f-mst').value='0318561568'; EL('#f-cname').value='Cong ty ABC';
tgl('other'); tgl('vat');            /* tat ca hai lai */
pick(2); pickSlot(i13);
GHI.goiMang.length=0; submitOrder();
var don=donDaGui();
RA({nguoi_nhan:don.nguoi_nhan, hoa_don:don.hoa_don, tags:don.tags,
    chu_con_trong_o: EL('#f-rname').value});
""")
	la("tat thi nguoi nhan gui null", r["nguoi_nhan"], None)
	la("tat thi hoa don gui null", r["hoa_don"], None)
	dung("khong gan the xuat hoa don", 74 not in r["tags"])
	la("nhung chu khach go van con trong o", r["chu_con_trong_o"], "Chi Lan")


@ca("#205 ba toggle doc lap nhau, nguoi khac nhan khong keo theo bo hoa don")
def _doc_lap():
	r = _chay("2026-09-06T08:00:00", """
var ra=[];
tgl('other'); ra.push({o:CO.other,g:CO.gift,v:CO.vat});
tgl('vat');   ra.push({o:CO.other,g:CO.gift,v:CO.vat});
tgl('gift');  ra.push({o:CO.other,g:CO.gift,v:CO.vat});
tgl('other'); ra.push({o:CO.other,g:CO.gift,v:CO.vat});
RA(ra);
""")
	la("bat nguoi nhan, hai co kia yen", r[0], {"o": True, "g": False, "v": False})
	la("bat hoa don, hai co kia yen", r[1], {"o": True, "g": False, "v": True})
	la("bat banh tang, hai co kia yen", r[2], {"o": True, "g": True, "v": True})
	la("tat nguoi nhan, hai co kia yen", r[3], {"o": False, "g": True, "v": True})


@ca("#205 bung thu co bao cho trinh doc man hinh va co dua con tro vao")
def _tro_giup_ban_phim():
	dung("nut nguoi nhan khai aria", 'id="c-other" onclick="tgl(\'other\')" aria-expanded="false"' in TRANG)
	dung("nut hoa don khai aria", 'id="c-vat" onclick="tgl(\'vat\')" aria-expanded="false"' in TRANG)
	r = _chay("2026-09-06T08:00:00", """
tgl('vat');
var a={aria:EL('#c-vat').getAttribute('aria-expanded'), tro:GHI.troVao};
tgl('vat');
RA({bat:a, tat:{aria:EL('#c-vat').getAttribute('aria-expanded')}});
""")
	la("bung ra thi aria la mo", r["bat"]["aria"], "true")
	dung("va con tro vao o dau tien", bool(r["bat"]["tro"]))
	la("thu lai thi aria la dong", r["tat"]["aria"], "false")


@ca("#205 nut Thay doi dat chuan cham 44 diem va chu 13 diem cua AGENTS.md")
def _nut_thay_doi_du_lon():
	# AGENTS.md dieu 13: nut cao it nhat 44 diem, chu it nhat 13 diem.
	m = re.search(r"\.tt-doi\{([^}]*)\}", TRANG, re.S)
	dung("co kieu cho nut Thay doi", bool(m))
	kieu = m.group(1) if m else ""
	cao = re.search(r"min-height:(\d+(?:\.\d+)?)px", kieu)
	chu = re.search(r"font-size:(\d+(?:\.\d+)?)px", kieu)
	dung("co dat chieu cao toi thieu", bool(cao))
	dung("co dat co chu", bool(chu))
	dung("cao it nhat 44 diem", float(cao.group(1)) >= 44 if cao else False)
	dung("chu it nhat 13 diem", float(chu.group(1)) >= 13 if chu else False)


@ca("#205 thu lai KHONG duoc xoa chu khach vua go")
def _khong_xoa_chu():
	r = _chay("2026-09-06T08:00:00", """
tgl('other');
EL('#f-rname').value='Chi Lan'; EL('#f-rphone').value='0900000000';
tgl('other');                       /* thu lai */
var giua={ten:EL('#f-rname').value, sdt:EL('#f-rphone').value,
          aria:EL('#c-other').getAttribute('aria-expanded')};
tgl('other');                       /* bung lai */
RA({giua:giua, sau:{ten:EL('#f-rname').value, sdt:EL('#f-rphone').value,
    aria:EL('#c-other').getAttribute('aria-expanded'), tro:GHI.troVao}});
""")
	la("thu lai khong xoa ten", r["giua"]["ten"], "Chi Lan")
	la("thu lai khong xoa so dien thoai", r["giua"]["sdt"], "0900000000")
	la("thu lai thi bao aria la dong", r["giua"]["aria"], "false")
	la("bung lai van con nguyen chu", r["sau"]["ten"], "Chi Lan")
	la("bung lai bao aria la mo", r["sau"]["aria"], "true")
	dung("bung lai co dua con tro vao o dau tien", bool(r["sau"]["tro"]))


@ca("#205 nguong ton phai giu o 10 dung nhu anh Viet chot trong issue")
def _nguong_dung_muc():
	# Ngưỡng nằm trong trang chứ không nằm trong bộ kiểm. Nếu ai nâng ngưỡng
	# lên cao thì số tồn thô lại lọt ra giao diện, nên chốt luôn con số ở đây.
	m = re.search(r"var NGUONG_TON *= *(\d+) *;", TRANG)
	dung("co khai bao nguong", bool(m))
	la("nguong la 10", int(m.group(1)) if m else 0, 10)
