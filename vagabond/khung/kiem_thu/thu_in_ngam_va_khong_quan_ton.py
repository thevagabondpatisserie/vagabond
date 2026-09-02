# -*- coding: utf-8 -*-
"""Kiem thu bon viec anh Viet chot ngay 02/09/2026 (dot hai).

1. IN NGAM CHO MOI TAI KHOAN
   *"2 tai khoan cua nhan vien thu ngan khi dang nhap vao (Gia Bao va Hoang
   Ngan) thi khi in may lai bao hop thoai allow cua qz tray. Em kiem tra fix
   o backend dum anh, toan bo tai khoan trong he thong deu phai dung duoc
   qz tray de in ngam."*

   Nguyen nhan da do ra: hang rao cu chan theo mot danh sach vai go cung,
   ma hai ban do chi mang cac vai Bo phan dat hang, Kiem ke vien, Sales
   User, Nhan hang dieu chuyen. Khong vai nao nam trong danh sach nen may
   chu tu choi ky, man hinh quay ve duong in khong chu ky, va QZ Tray hien
   hop Allow.

2. ANH MON O BANG KIEM KHO
   *"tren hinh 1 thi ten mon khong co anh mon, anh nho dieu nay da noi em
   fix o backend roi ma."* Quy tac thuong truc tu 01/09/2026: anh phai la
   ANH THAT, mon chua co anh thi de o TRONG, khong lay chu cai dau ten mon
   thay anh.

3. DUONG VE DUNG THU TU
   *"man kiem banh chi co the quay thang ra man hinh nghiep vu neu nhan
   back, anh can no quay ra phan he ban hang moi dung thu tu chu."*

4. MON KHONG QUAN TON KHONG BAO GIO THIEU
   *"mon Nuoc, ml (em doi lai thanh Nuoc, gr dum anh) van bi quan ton va
   bao thieu trong khi cai nay la nuoc may, khong quan."*

   Hai loi rieng biet nam chong len nhau o day, va ca kiem nay chot ca hai:

   a. Mon do KHONG quan ton, tuc khong co phieu nhap va khong co ton kho.
      Ton doc ra luon bang khong, nen phep tru nao cung ra thieu. Bep nhin
      chip do gia mai thanh quen roi bo qua ca luc thieu that.
   b. Ten hien tren man la "Nuoc, ml" trong khi danh muc da ghi "Nuoc,
      gram" tu lau. ERPNext chep ten mon vao dong cong thuc luc them dong
      va KHONG bao gio chep lai; dung 43 cong thuc dang giu cai ten cu do.
      Sua bang cach doc ten thang tu danh muc, chu khong phai di sua 43
      cong thuc.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import in_ngam, ke_hoach_sx

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))


def _doc(duong):
	with io.open(os.path.join(GOC, duong), encoding="utf-8") as f:
		return f.read()


# ------------------------------------------------------ in ngam QZ Tray

@ca("in ngam: moi tai khoan da dang nhap deu xin duoc chu ky, chi chan khach vang lai")
def _():
	m = _doc("vagabond/in_ngam.py")
	i = m.find("def _chan():")
	dung("co ham chan", i > 0)
	than = m[i:m.find("def _cai_dat():")]
	dung("van chan khach vang lai", 'frappe.session.user == "Guest"' in than)
	dung("khong con chan theo vai", "frappe.get_roles()" not in than)
	dung("khong con doi chieu danh sach vai", "QUYEN_IN" not in than)


@ca("in ngam: danh sach vai cu giu lai de doc lich su, khong duoc dung de chan")
def _():
	dung("da doi ten thanh ban cu", hasattr(in_ngam, "QUYEN_IN_CU"))
	dung("khong con ten cu de ai do vo tinh dung lai",
		not hasattr(in_ngam, "QUYEN_IN"))
	m = _doc("vagabond/in_ngam.py")
	# Hai ban ma hai ban Gia Bao va Hoang Ngan mang, de phien sau doc ra
	# ngay vi sao hang rao cu sai.
	dung("ghi lai nguyen nhan that", "Sales User" in m and "Kiểm kê viên" in m)


@ca("in ngam: hai cua ky va dinh tuyen van di qua hang rao dang nhap")
def _():
	m = _doc("vagabond/in_ngam.py")
	for ten in ("def chung_thu():", "def ky(", "def dinh_tuyen("):
		i = m.find(ten)
		dung("co %s" % ten, i > 0)
		dung("%s goi _chan" % ten, "_chan()" in m[i:i + 900])


# --------------------------------------------------- anh mon o kiem kho

@ca("kiem kho: ten va anh doc thang tu danh muc moi lan mo bang")
def _():
	m = _doc("vagabond/kiem_kho.py")
	dung("co ham doc ho so mon", "def _ho_so_hang(" in m)
	dung("doc ca anh", '"image"' in m)
	i = m.find("def bang(")
	than = m[i:m.find("def luu_o(")]
	dung("bang tra ve anh", '"hinh"' in than)
	dung("ten lay tu danh muc", 'h.get("ten")' in than)
	j = m.find("def tim_mon(")
	tim = m[j:m.find("def chot(")]
	# Neo vao ca hai dau: co xin cot anh khi doc, VA co dua anh ra ngoai.
	# Thieu mot trong hai la o tim ma lai ra ten tro.
	dung("o tim ma co xin cot anh", '"name", "item_name", "image"' in tim)
	dung("va dua anh ra ngoai", '"hinh": d.get("image")' in tim)


@ca("kiem kho: mon chua co anh de O TRONG, khong lay chu cai thay anh")
def _():
	j = _doc("vagabond/trang/kiem-banh.js")
	i = j.find("function anhMon(")
	dung("co ham ve anh", i > 0)
	than = j[i:i + 400]
	dung("khong co anh thi ve o rong", "kb-noimg" in than)
	dung("co anh thi dung the img", "<img src=" in than)
	# Khong duoc lay ky tu dau ten mon lam anh du phong.
	dung("khong lay chu cai dau thay anh",
		"charAt(0)" not in than and "slice(0, 1)" not in than and "[0]" not in than)


# ------------------------------------------------------- duong ve dung

@ca("kiem banh: nut quay lai ra PHAN HE BAN HANG chu khong nhay thang ve man goc")
def _():
	x = _doc("vagabond/trang/kiem-banh.html")
	dung("tro ve phan he ban hang", 'href="/phan-he-ban-hang"' in x)
	dung("chu tren nut noi ro noi den", "Phân hệ Bán hàng" in x)
	dung("khong con tro thang ve man goc", 'class="kb-back" href="/bep"' not in x)

	# Duong /phan-he-ban-hang phai la duong CO THAT do bang duong sinh ra,
	# khong phai chuoi go tay. Go sai mot chu la nut dan vao trang 404.
	from vagabond.duong_app import DUONG

	dung("duong nay co that trong bang duong", "phan-he-ban-hang" in DUONG)
	la("va tro dung phan he Ban hang", DUONG.get("phan-he-ban-hang"), "PH:BH")


# --------------------------------------------- mon khong quan ton kho

@ca("ke hoach sx: mon khong quan ton luon du, khong bao gio bao thieu")
def _():
	# Nuoc may: can 744, ton doc ra 0. Quan ton thi ra thieu, khong quan
	# ton thi phai la du.
	la("quan ton thi thieu that", ke_hoach_sx.muc_cua(744, 0), ke_hoach_sx.MUC_THIEU)
	la("khong quan ton thi du", ke_hoach_sx.muc_cua(744, 0, quan_ton=False),
		ke_hoach_sx.MUC_DU)
	la("va khong con gi phai lam", ke_hoach_sx.con_phai_lam(744, 0, quan_ton=False), 0.0)
	la("quan ton thi van tinh dung", ke_hoach_sx.con_phai_lam(744, 0), 744.0)


@ca("ke hoach sx: chua co cong thuc van dung TRUOC moi thu, ke ca khong quan ton")
def _():
	# Dong chua co cong thuc thi may khong tinh duoc gi ca. Gan chip "du"
	# len no la noi doi, du no co quan ton hay khong.
	la("khong cong thuc, co quan ton",
		ke_hoach_sx.muc_cua(10, 0, co_bom=False), ke_hoach_sx.MUC_CHUA_BOM)
	la("khong cong thuc, khong quan ton",
		ke_hoach_sx.muc_cua(10, 0, co_bom=False, quan_ton=False),
		ke_hoach_sx.MUC_CHUA_BOM)


@ca("ke hoach sx: chip thieu nguyen lieu tren man danh sach lenh cung bo qua mon khong quan ton")
def _():
	dong = [
		{"ma": "NVLT00231", "can": 744, "kho": "Bếp"},   # nuoc may
		{"ma": "NVLT00078", "can": 100, "kho": "Bếp"},   # co quan ton, thieu that
	]
	ton = {("NVLT00231", "Bếp"): 0.0, ("NVLT00078", "Bếp"): 0.0}
	la("khong loc thi bao thieu ca hai",
		ke_hoach_sx.thieu_cua_lenh(dong, ton, 1.0), ["NVLT00231", "NVLT00078"])
	la("loc roi thi chi con mon thieu that",
		ke_hoach_sx.thieu_cua_lenh(dong, ton, 1.0, {"NVLT00231"}), ["NVLT00078"])


@ca("ke hoach sx: ten mon doc tu danh muc, khong lay ten chep san trong cong thuc")
def _():
	m = _doc("vagabond/ke_hoach_sx.py")
	dung("co ham doc ho so mon", "def _ho_so_cua(" in m)
	dung("doc ca ten va co quan ton", '"item_name", "is_stock_item"' in m)
	i = m.find("def xem(")
	than = m[i:]
	dung("lay ten that", "ten_that" in than)
	dung("ten danh muc di truoc ten chep san", 'ten_that.get(ma) or ten_mon' in than)
	dung("va truyen co quan ton vao chip", "quan_ton=qt" in than)
	dung("nhip doc mot luot cho ca lo", "_ho_so_cua(cac_ma)" in than)


@ca("ke hoach sx: man hinh khong in con so ton vo nghia cho mon khong quan ton")
def _():
	j = _doc("vagabond/public/js/bep/38-ke-hoach-sx.js")
	dung("man hinh biet co quan ton", "n.quan_ton === 0" in j)
	dung("va ghi ro thay vi in so khong", "không quản tồn" in j)
	dung("chip thieu van doc theo con_lam", "n.con_lam > 0" in j)
