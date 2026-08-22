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
