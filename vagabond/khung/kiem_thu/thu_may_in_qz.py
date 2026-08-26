# -*- coding: utf-8 -*-
"""Gan ten may in that cho tung may trong so, ngay tren may quay.

Anh Viet 22/08/2026: *"Phan may in ben desk dua het len app o phan cai dat
may in dum anh nha, phan theo diem ban, de quan ly De vao do cai cho de chu
ban ay khong dung ban desktop."*

Truoc dot nay, viec "phieu nao ra may nao" nam o HAI o chu tren Desk
(`qz_may_in_hoa_don` va `qz_may_in_tem`). Ba diem hong:

  1. De khong dung Desk, nen moi lan doi may in la phai nho anh Viet.
  2. Hai o cho BON loai phieu. "Phieu lam mon" va "Phieu chot ca" khong co
     duong rieng, chung an nho duong cua hoa don.
  3. Mot cap o cho CA TIEM. Hai diem ban dung hai doi may khac hang thi
     khong co cach nao khai cho ca hai.

Cach chua: so may in tren app von da co san diem ban, loai phieu va kho
giay cho tung may. Chi con thieu dung mot o - ten may in tren may tinh -
nen them o do vao so, va cho nguoi dung CHAM CHON tu danh sach QZ doc duoc
ngay tren may quay chu khong bat go tay.
"""

import io
import os

from vagabond import may_in
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _js(ten):
	goi = os.path.dirname(os.path.abspath(may_in.__file__))
	return io.open(
		os.path.join(goi, "public", "js", "bep", ten), encoding="utf-8").read()


def _py(ten):
	goi = os.path.dirname(os.path.abspath(may_in.__file__))
	return io.open(os.path.join(goi, ten), encoding="utf-8").read()


@ca("máy in QZ: mỗi máy trong sổ có ô tên máy in trên máy tính")
def _():
	src = _py("may_in.py")
	dung("_chuan có ô qz", '"qz": str((d or {}).get("qz") or "").strip(),' in src)
	d = may_in._chuan({"ma": "MI9", "ten": "Thử", "qz": "  XP-350  "})
	la("cắt khoảng trắng hai đầu", d["qz"], "XP-350")
	la("không khai thì rỗng", may_in._chuan({"ma": "MI8"})["qz"], "")


@ca("máy in QZ: tuyến trả về DANH SÁCH mảnh tên, không phải một chuỗi")
def _():
	src = _py("may_in.py")
	dung("có hàm tuyen_qz", "def tuyen_qz(" in src)
	dung("gom vào danh sách", "ra[v].append(manh)" in src)
	dung("không trùng mảnh", "manh not in ra[v]" in src)


@ca("máy in QZ: tuyến đủ bốn loại phiếu, không phải hai")
def _():
	src = _py("may_in.py")
	dung("dựng khung từ VAI_TRO", 'ra = {v["k"]: [] for v in VAI_TRO}' in src)
	la("sổ đang khai bốn loại phiếu", len(may_in.VAI_TRO), 4)
	for k in ("hoa_don", "phieu_mon", "tem", "chot_ca"):
		dung("có loại %s" % k, any(v["k"] == k for v in may_in.VAI_TRO))


@ca("máy in QZ: lọc theo điểm bán, và máy tắt thì không tính")
def _():
	src = _py("may_in.py")
	dung("chỉ đọc máy đang bật", "ds(chi_bat=True)" in src)
	dung("lọc theo điểm", 'if diem and m.get("diem") and m["diem"] != diem:' in src)
	dung("máy chưa gán tên thì bỏ qua", "if not manh:" in src)


@ca("máy in QZ: cửa dinh_tuyen nhận điểm bán và trả thêm ô tuyen")
def _():
	src = _py("in_ngam.py")
	dung("nhận tham số điểm", 'def dinh_tuyen(diem=""):' in src)
	dung("gọi sổ máy in", "may_in.tuyen_qz(diem)" in src)
	dung("trả ô tuyen", '"tuyen": tuyen,' in src)
	dung("hỏng sổ không được làm chết cửa", "in_ngam: doc so may in" in src)


@ca("máy in QZ: GIỮ hai ô cũ trên Desk làm lưới đỡ")
def _():
	# Bo hai o nay ngay bay gio la ai chua kip gan ten se mat duong in ngam
	# giua ca ban hang. Chi duoc bo khi moi may trong so deu da co ten.
	src = _py("in_ngam.py")
	dung("còn ô hoá đơn cũ", '"hoa_don": (cd.get("qz_may_in_hoa_don")' in src)
	dung("còn ô tem cũ", '"tem": (cd.get("qz_may_in_tem")' in src)


@ca("máy in QZ: sổ đi trước, ô cũ trên Desk đi sau")
def _():
	js = _js("27-in-ngam.js")
	dung("có hàm dựng danh sách mảnh", "function inManhCho(" in js)
	khuc = js.split("function inManhCho(")[1].split("\n}")[0]
	vt_so = khuc.find("t.tuyen && t.tuyen[vaiTro]")
	vt_cu = khuc.find("vaiTro === 'tem' ? t.tem : t.hoa_don")
	dung("cả hai nguồn đều có mặt", vt_so >= 0 and vt_cu >= 0)
	dung("sổ đứng trước ô cũ trong danh sách", vt_so < vt_cu)


@ca("máy in QZ: dò hết danh sách rồi mới chịu thua, không in bừa")
def _():
	js = _js("27-in-ngam.js")
	khuc = js.split("function inChonMay(")[1].split("\n}")[0]
	dung("duyệt cả danh sách", "for (var i = 0; i < manh.length; i++)" in khuc)
	dung("không khớp thì trả null", "return null;" in khuc)
	dung("KHÔNG lấy máy đầu tiên cho xong", "IN_QZ.may[0]" not in khuc)


@ca("máy in QZ: khối tình trạng bày đủ bốn loại phiếu")
def _():
	js = _js("27-in-ngam.js")
	dung("dựng bảng theo vai", "theo_vai[k] = { may: inChonMay(k), manh: inManhCho(k) };" in js)
	for k in ("hoa_don", "phieu_mon", "tem", "chot_ca"):
		dung("có %s" % k, "'%s'" % k in js)
	js18 = _js("18-doi-chieu-may-in.js")
	dung("màn cài đặt đọc theo_vai", "(t.theo_vai || {})[v.k]" in js18)


@ca("máy in QZ: màn sửa máy in cho chạm chọn tên, không bắt gõ tay")
def _():
	js = _js("18-doi-chieu-may-in.js")
	dung("có ô nhập", 'id="miQz"' in js)
	dung("miDoc đọc ô đó", "if ((g = v('miQz')) !== null) d.qz = g;" in js)
	dung("có chip chạm chọn", "data-miqz=" in js)
	dung("bắt sự kiện chạm", "d.qz = t.getAttribute('data-miqz');" in js)
	dung("lấy tên từ QZ dò được", "IN_QZ.may" in js)


@ca("máy in QZ: gợi ý mảnh ngắn hơn để sống sót qua đổi cổng USB")
def _():
	js = _js("18-doi-chieu-may-in.js")
	dung("có hàm gợi ý", "function miQzGoiY(" in js)
	dung("bỏ đuôi trong ngoặc", "replace(/\\s*\\(.*?\\)\\s*$/" in js)


@ca("máy in QZ: cảnh báo khi một mảnh khớp nhiều máy")
def _():
	js = _js("18-doi-chieu-may-in.js")
	dung("có hàm đếm khớp", "function miQzKhop(" in js)
	dung("nói rõ khớp mấy máy", "khớp ' + khop.length + ' máy" in js)
	dung("nói rõ máy sẽ lấy cái đầu", "lấy cái đầu tiên" in js)
	dung("báo khi chưa khớp cái nào", "Chưa khớp máy in nào" in js)


@ca("máy in QZ: vào thẳng màn sửa cũng dò QZ để có danh sách mà chạm")
def _():
	js = _js("18-doi-chieu-may-in.js")
	khuc = js.split("function scrMayInSua(")[1]
	dung("có gọi dò", "inNgamDo()" in khuc)
	dung("chỉ dò khi chưa dò lần nào", "!IN_QZ.do_roi" in khuc)
	dung("dò hỏng không làm chết màn", ".catch(function () { });" in khuc)


# --------------------------------------------------------- chu ky in ngam
#
# De 25/08/2026: *"da cai dat may in nhung qz tray van bao loi invalid voi
# may in GODEX khi in tem. Chi co may in epson thi da in silent duoc"*.
#
# Hop QZ bao "wants to access connected printers - Cannot verify trust -
# Invalid Signature". Doc ky hai manh do thi ra: hop nay khong dinh gi toi
# may in tem ca. "access connected printers" la loi nhac cua QZ cho lenh
# `printers.find`, tuc buoc DEM MAY IN, chay truoc moi lan in bat ke in ra
# may nao. Nghia la chu ky hong tu goc, ca may EPSON cung dang hong; EPSON
# im tieng chi vi da co nguoi tich "Remember this decision" mot lan, va QZ
# xet cai da nho TRUOC khi xet chu ky.
#
# Ba ca duoi day chot ba cho da sua, de khong ai vo tinh dat lai.


@ca("chữ ký in: chốt thuật toán SAU khi nối được, không chốt trước")
def _():
	js = _js("27-in-ngam.js")
	i = js.find("async function inNoiQz(")
	than = js[i:js.find("\n}\n", i)]
	noi = than.find("qz.websocket.connect(")
	dat = than.find("setSignatureAlgorithm(")
	dung("có nối", noi > 0)
	dung("có chốt thuật toán", dat > 0)
	# Day la ca ban chat cua loi. Thu vien qz-tray.js chi do duoc phien ban
	# QZ Tray SAU khi noi; goi setSignatureAlgorithm truoc do thi hang rao
	# tuong thich cua no khong do duoc gi, va may quay chay QZ Tray doi 2.0
	# se nhan chu ky SHA512 trong khi no chi doi chieu duoc SHA1.
	dung("chốt thuật toán nằm SAU lệnh nối", dat > noi)
	dung("đọc lại thuật toán thật", "getSignatureAlgorithm()" in than)
	dung("nhớ vào IN_QZ.ky", "IN_QZ.ky =" in than)


@ca("chữ ký in: không bao giờ đẩy xuống QZ một chữ ký rỗng")
def _():
	js = _js("27-in-ngam.js")
	i = js.find("setSignaturePromise(")
	than = js[i:i + 900]
	# Ban cu: ok((r && r.chu_ky) || ''). Chu ky rong bi QZ doc la lenh in
	# KHONG duoc ky, va no bung dung cai hop Invalid Signature ra quay.
	# Do trong THAN ham chu khong do ca tep: chu thich phia tren co dan lai
	# dong cu de nguoi doc sau biet vi sao khong duoc viet nhu the.
	dung("không còn đường ok thẳng chữ ký", "ok((r && r.chu_ky) || '')" not in than)
	dung("thiếu chữ ký thì báo hỏng", "return hong(" in than)
	dung("chỉ ok sau khi đã kiểm", than.find("if (!ck)") < than.find("ok(ck);"))
	dung("gửi thuật toán đang dùng thật", "thuat_toan: IN_QZ.ky" in than)
	dung("không chốt cứng SHA512 lúc xin ký", "thuat_toan: 'SHA512'" not in js)


@ca("chữ ký in: máy chủ đối chiếu được chứng thư với khoá riêng")
def _():
	src = _py("in_ngam.py")
	dung("có cửa tự kiểm", "def tu_kiem():" in src)
	dung("cửa đó mở ra ngoài", "@frappe.whitelist()\ndef tu_kiem():" in src)
	# Ky thu roi tu doi chieu bang khoa cong khai doc tu chinh chung thu:
	# lech cap thi bat duoc ngay o may chu, khong phai doan tu quay.
	dung("đọc chứng thư", "load_pem_x509_certificate(" in src)
	dung("ký thử rồi đối chiếu", "cong.verify(" in src)
	dung("gọi tên đúng bệnh lệch cặp", '"lech_cap"' in src)
	dung("KHÔNG ghi gì vào cơ sở dữ liệu", "db.set_value" not in src)
	js = _js("27-in-ngam.js")
	dung("màn Cài đặt có hỏi", "vagabond.in_ngam.tu_kiem" in js)
	# Duong in phai nhe: chi man Cai dat hoi, khong hoi giua luc tinh tien.
	i = js.find("async function inGiay(")
	dung("đường in không hỏi", "tu_kiem" not in js[i:js.find("\n}\n", i)])


@ca("chữ ký in: hộp xanh không được nói êm khi chữ ký đang hỏng")
def _():
	js = _js("18-doi-chieu-may-in.js")
	dung("có khối cảnh báo chữ ký", "function miChuKy(" in js)
	i = js.find("async function miVeQz(")
	than = js[i:i + 3000]
	dung("hộp xanh có gắn cảnh báo", than.count("miChuKy(t)") >= 2)
	dung("nói thẳng chữ ký hỏng", "Chữ ký in đang hỏng" in js)
	# QZ chi thoi hoi khi isVerified() = certificate.isTrusted() && validity
	# == TRUSTED. Chua moi chu ky thi hop van hien, chi doi dong do sang
	# "Untrusted website" - phai noi ra khong nguoi sua tuong minh that bai.
	dung("nói cả nửa chứng thư", "override.crt" in js)
	dung("nói rõ thiếu nửa kia thì vẫn hiện", "Untrusted website" in js)
	# Tich Remember thi QZ tu tat nut Allow. Khong noi ra thi quay tuong may hong.
	dung("giải thích nút Allow bị mờ", "Remember this decision" in js)
	dung("bày cả phiên bản QZ Tray", "'QZ Tray ' + h(t.ban)" in js)
	dung("nhắc nâng cấp khi còn SHA1", "chỉ đọc được SHA1" in js)


# ------------------------------------------------- o khoa rieng bi dan nham
#
# Anh Viet 26/08/2026 gui anh man Vagabond Settings: o "Khoa rieng QZ Tray"
# dang chua chuoi `Vagabond16xx@`, tuc mot MAT KHAU chu khong phai khoa RSA.
# Kem theo la thanh do manh mat khau va dong "Include symbols, numbers and
# capital letters" cua trinh duyet - dau hieu Chrome tu dien mat khau da luu
# vao o do, vi Frappe khai o kieu Password nen trinh duyet tuong la o dang
# nhap. Khong co khoa that thi khong the ky dung, va day chinh la goc cua
# hop "Invalid Signature".
#
# Nhin man hinh khong bao gio thay duoc benh nay: o Password che sach noi
# dung. Nen may chu phai tu goi ten no ra.


@ca("khoá riêng QZ: gọi tên được cảnh ô bị điền nhầm mật khẩu")
def _():
	from vagabond.in_ngam import _la_pem
	dung("mật khẩu không phải PEM", not _la_pem("Vagabond1606@"))
	dung("ô rỗng không phải PEM", not _la_pem(""))
	dung("khối PEM thì nhận", _la_pem("-----BEGIN PRIVATE KEY-----\nAAAA\n-----END PRIVATE KEY-----"))
	src = _py("in_ngam.py")
	dung("cửa ký chặn trước khi ký", "if not _la_pem(khoa):" in src)
	dung("tự kiểm cũng gọi tên bệnh", '"khoa_khong_phai_pem"' in src)
	# Phai noi ro thu pham la trinh duyet tu dien, khong thi nguoi doc tuong
	# minh dan sai va dan lai dung cai cu.
	dung("chỉ mặt trình duyệt tự điền", "trình duyệt tự điền" in src or "trình duyệt hay tự điền" in src)


@ca("khoá riêng QZ: ô Password nuốt xuống dòng thì máy chủ dựng lại PEM")
def _():
	"""O Password cua Frappe la o MOT DONG. Dan mot khoa hai muoi may dong
	vao do thi trinh duyet noi het lai, hoac doi xuong dong thanh dau cach.
	Khong doi o sang Text duoc: kieu Password la thu khien Frappe ma hoa
	khoa luc luu."""
	from vagabond.in_ngam import _chuan_pem
	than = "A" * 200
	goc = "-----BEGIN PRIVATE KEY-----\n" + than + "\n-----END PRIVATE KEY-----"
	mong = _chuan_pem(goc)
	# Ba kieu bi bam nat deu phai ve dung mot ket qua.
	la("nuốt sạch xuống dòng", _chuan_pem(goc.replace("\n", "")), mong)
	la("xuống dòng thành dấu cách", _chuan_pem(goc.replace("\n", " ")), mong)
	la("thừa khoảng trắng hai đầu", _chuan_pem("  " + goc + "  \n"), mong)
	# Xuong dong dung chuan PEM la 64 ky tu mot dong.
	dong = mong.splitlines()
	la("dòng ruột dài 64 ký tự", len(dong[1]), 64)
	la("giữ nguyên nhãn", dong[0], "-----BEGIN PRIVATE KEY-----")
	# Khong phai PEM thi tra nguyen si, khong duoc tu bien.
	la("chuỗi lạ trả nguyên si", _chuan_pem("Vagabond1606@"), "Vagabond1606@")
	la("ô rỗng vẫn rỗng", _chuan_pem(None), "")


@ca("khoá riêng QZ: máy chủ CHẶN lưu khi ô bị điền đè mật khẩu")
def _():
	"""Anh Viet 26/08/2026 mo man Vagabond Settings, Chrome tu dien
	`Vagabond16xx@` vao o khoa rieng ngay luc trang nap xong, tieu de nhay
	sang "Chua luu". Bam Luu la mat khoa in cua ca tiem. Da xay ra hai lan
	trong mot buoi, va lan nao cung phai do lai tu dau moi ra.

	Chan o buoc validate thi du ai bam Luu, du trinh duyet dien gi vao, khoa
	dang chay cung khong mat."""
	import io as _io
	import os as _os
	goi = _os.path.dirname(_os.path.abspath(may_in.__file__))
	src = _io.open(_os.path.join(
		goi, "vagabond", "doctype", "vagabond_settings", "vagabond_settings.py"),
		encoding="utf-8").read()
	dung("có chốt chặn", "def _chan_khoa_qz_bi_dien_de(" in src)
	dung("gọi trong validate", "self._chan_khoa_qz_bi_dien_de()" in src)
	dung("nhận ra khoá thật qua BEGIN và END",
		'"-----BEGIN" in khoa and "-----END" in khoa' in src)
	# O rong la cach tat in ngam co y, khong duoc chan.
	dung("ô rỗng vẫn cho qua", "if not khoa:\n\t\t\treturn" in src)
	dung("chặn bằng throw chứ không âm thầm sửa", "frappe.throw(" in src)
	# Noi ro thu pham, khong thi nguoi doc tuong minh dan sai.
	dung("chỉ mặt trình duyệt tự điền", "trình duyệt vừa tự điền" in src)
	dung("chỉ chỗ xoá mật khẩu đã lưu", "chrome://password-manager" in src)


@ca("in ngầm: mật độ điểm phải đổi theo đơn vị mm, không đưa thẳng DPI")
def _():
	"""Anh Viet 26/08/2026: bam In thi bill ra be bang mot soi giay, bam In
	tem mon thi ra mot dai giay dai trang tron.

	QZ quy dinh don vi cua `density` bam theo `units`: units 'in' thi
	density la DPI, units 'mm' thi density la diem tren mot mi li met. Khai
	thang 203 trong khi units la 'mm' la bao QZ rang anh co 203 diem moi mi
	li met, tuc anh bill rong 575 diem chi be co 2,8mm.

	Ca kiem nay chot ca hai cho goi qz.configs.create, vi ban in tu duong
	dan (tem HACCP theo lo) dung mot cau hinh rieng va da tung bi bo sot."""
	js = _js("27-in-ngam.js")
	dung("không còn đưa thẳng DPI", "density: dpi," not in js)
	dung("bản in thường đã đổi đơn vị", "density: dpi / 25.4," in js)
	# Hai cho: inGiay va inToTuDuongDan.
	la("cả hai cấu hình đều đổi", js.count("density: dpi / 25.4"), 2)
	# Don vi van la mm, vi size.width khai bang mm.
	la("vẫn khai đơn vị mm", js.count("units: 'mm'"), 2)
	dung("nói rõ vì sao trong chú thích", "diem tren mot MI" in js or "diem tren mot mi li met" in js)
