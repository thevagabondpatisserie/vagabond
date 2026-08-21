"""Ca kiểm cho màn Đơn Pancake đã huỷ chờ hoàn tiền.

Mọi ca ở đây chạy trên phép THUẦN, không cần Frappe, không cần site, không
cần mạng. Phần chạm hệ có ca kiểm tích hợp riêng ở khung/kiem_that.
"""

from vagabond import don_huy as dh
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("don huy: chi lay trang thai 6 la da huy, KHONG lay 7 la da xoa")
def _chi_lay_huy():
	# Don bi XOA la don nhap nham, khong co khach nao chuyen tien cho no.
	# Lay ca 7 la loi ra mot danh sach rac khong ai doc.
	dung("trang thai 6 la huy", dh.la_don_huy({"status": 6}))
	dung("trang thai 7 KHONG lay", not dh.la_don_huy({"status": 7}))
	dung("trang thai 3 KHONG lay", not dh.la_don_huy({"status": 3}))
	dung("don rong khong no", not dh.la_don_huy(None))
	dung("status chu khong phai so", not dh.la_don_huy({"status": "abc"}))


@ca("don huy: chua thay dong nao thi KHONG PHAI HOAN, khong lot vao hang cho")
def _chua_co_tien():
	# Khach huy truoc khi chuyen tien la ca thuong gap nhat. Loi ca dam do
	# vao danh sach cho hoan thi sales phai loc tay moi ngay va se bo sot
	# ca that.
	la("chua chuyen dong nao", dh.trang_thai_don(0), dh.KHONG_PHAI)
	la("so am cung vay", dh.trang_thai_don(-1), dh.KHONG_PHAI)
	la("co tien thi cho hoan", dh.trang_thai_don(705000), dh.CHO_HOAN)


@ca("don huy: ho so bi huy thi don QUAY LAI hang cho, khong duoc coi la xong")
def _ho_so_bi_huy():
	# Tien van con o minh. Coi la xong la mat dau mot khoan phai tra.
	la("ho so da huy", dh.trang_thai_don(705000, "Da huy"), dh.CHO_HOAN)
	la("dang cho chi", dh.trang_thai_don(705000, "Cho chi"), dh.DANG_HOAN)
	la("da chi chua doi soat", dh.trang_thai_don(705000, "Da chi"), dh.DANG_HOAN)
	la("hoan thanh", dh.trang_thai_don(705000, "Hoan thanh"), dh.DA_HOAN)


@ca("don huy: nguoi da bam Bo qua thi ton trong, khong loi ra nua")
def _bo_qua():
	la("bo qua thang", dh.trang_thai_don(920000, None, 1), dh.BO_QUA)
	# Bo qua thang ca khi CO tien: do la mot quyet dinh cua nguoi, khong
	# phai mot suy doan cua may.
	la("bo qua manh hon co tien", dh.trang_thai_don(920000, "Cho chi", 1), dh.BO_QUA)


@ca("don huy: muc hoan mac dinh la 100% so khach da chuyen")
def _muc_hoan():
	# Anh Viet chot 21/08/2026: hoan ngang bang so da nhan, de so sua duoc.
	la("hoan het so da nhan", dh.muc_hoan(705000), 705000)
	la("khong co tien thi 0", dh.muc_hoan(0), 0)
	la("so am ve 0", dh.muc_hoan(-50000), 0)


@ca("don huy: chip dem tren TOAN BANG, va tien cho hoan chi tinh don con no")
def _dem_chip():
	bang = [
		{"trang_thai": dh.CHO_HOAN, "da_nhan": 705000},
		{"trang_thai": dh.CHO_HOAN, "da_nhan": 920000},
		{"trang_thai": dh.DANG_HOAN, "da_nhan": 750000},
		{"trang_thai": dh.DA_HOAN, "da_nhan": 300000},
		{"trang_thai": dh.KHONG_PHAI, "da_nhan": 0},
	]
	dem = dh.dem_theo_chip(bang)
	la("cho hoan", dem[dh.CHO_HOAN], 2)
	la("dang hoan", dem[dh.DANG_HOAN], 1)
	la("da hoan", dem[dh.DA_HOAN], 1)
	la("tat ca", dem["tat_ca"], 5)
	# Da hoan roi thi tien khong con o minh nua, khong duoc cong vao.
	la("tien dang giu ho", dh.tien_cho_hoan(bang), 705000 + 920000 + 750000)


@ca("don huy: dien giai PHAI mang so don, vi 131 theo doi bang so don")
def _dien_giai():
	# Chi Dung chot dieu 4: don online do chung vao ma "Khach le Online",
	# nen so don trong dien giai la thu duy nhat tach duoc tung nguoi.
	cau = dh.dien_giai_don("92252", "MD92252", "Ms.Nhu Duyen")
	dung("co ma hien thi", "MD92252" in cau)
	dung("co ID noi bo", "92252" in cau)
	dung("co ten khach", "Nhu Duyen" in cau)
	# Ma hien thi trung ID thi khong lap lai cho thua.
	la("khong lap ma", dh.dien_giai_don("92252", "92252"), "Don 92252")


@ca("don huy: noi dung chuyen khoan dung cu phap chot 16/08/2026")
def _noi_dung_ck():
	# Dong sao ke chi co MOT o noi dung, va ba thang sau do la thu duy nhat
	# ke toan doc duoc.
	la("theo ma hien thi", dh.noi_dung_chuyen_khoan("92252", "MD92252"),
		"THE VAGABOND HOAN TIEN MD92252")
	la("khong co ma hien thi thi lay ID", dh.noi_dung_chuyen_khoan("92156"),
		"THE VAGABOND HOAN TIEN 92156")


@ca("don huy: han giu ban dem dem theo NGAY, khong dem theo gio")
def _qua_han():
	dung("dung 30 ngay thi CHUA qua han",
		not dh.qua_han_don_dep("2026-07-22 09:00:00", "2026-08-21 23:59:00"))
	dung("31 ngay thi qua han",
		dh.qua_han_don_dep("2026-07-21 23:00:00", "2026-08-21 01:00:00"))
	dung("khong co moc thi khong don", not dh.qua_han_don_dep(None, "2026-08-21"))
	dung("moc hong thi khong don", not dh.qua_han_don_dep("khong-phai-ngay", "2026-08-21"))


@ca("don huy: ba don anh Viet gui ngay 21/08/2026 chay dung tu dau toi cuoi")
def _ba_don_that():
	# Chot lai bang so that: 92252 (705.000), 92245 (920.000), 92156 (750.000).
	# Ca nay la ca doc de nhat trong tep, co y giu nguyen so lieu that.
	bang = []
	for ma, ten, tien in (("92252", "Ms.Nhu Duyen", 705000),
			("92245", "Mr.Khoa Le", 920000),
			("92156", "Ms.Vi Aibi", 750000)):
		bang.append({
			"ma_don": ma, "ten_khach": ten, "da_nhan": tien,
			"trang_thai": dh.trang_thai_don(tien),
		})
	la("ca ba deu cho hoan", dh.dem_theo_chip(bang)[dh.CHO_HOAN], 3)
	la("tong dang giu ho", dh.tien_cho_hoan(bang), 2375000)
	la("moi don hoan het so da nhan",
		[dh.muc_hoan(d["da_nhan"]) for d in bang], [705000, 920000, 750000])


@ca("don huy: moc quet Pancake phai la UNIX GIAY, truyen chuoi ISO ra 0 don")
def _moc_unix():
	# Ca nay sinh ra tu su co that ngay 21/08/2026: v264 deploy sach, dong_bo
	# chay khong loi, tra ve quet 0 trong khi Pancake dang co ba don huy.
	# Nguyen nhan: truyen startDateTime kieu "2026-07-22 18:20:00". Pancake
	# tra HTTP 200 voi data rong, khong he bao loi. Cung cai bay da ghi o dau
	# tep kiem_banh.py ma phien nay van roi vao.
	from datetime import datetime, timedelta
	from zoneinfo import ZoneInfo

	tz = ZoneInfo("Asia/Ho_Chi_Minh")
	moc = datetime(2026, 8, 21, 18, 20, 0, tzinfo=tz)
	dau, cuoi = dh.khoang_quet(30, moc)
	dung("moc dau la so nguyen", isinstance(dau, int))
	dung("moc cuoi la so nguyen", isinstance(cuoi, int))
	la("cuoi dung bang moc truyen vao", cuoi, int(moc.timestamp()))
	la("dau lui dung 30 ngay", cuoi - dau, 30 * 86400)
	la("mot ngay thi lui dung mot ngay",
		dh.khoang_quet(1, moc)[0], int((moc - timedelta(days=1)).timestamp()))


@ca("don huy: chan hoi quy - tep nguon khong duoc truyen moc quet dang chuoi")
def _khong_chuoi_iso():
	# Doc thang ma nguon. Ca tren chi kiem ham thuan, nhung neu mai mot co
	# nguoi sua lai cho goi Pancake thanh chuoi thi ham thuan van xanh ma
	# that te van hong. Ca nay dong dinh dung cho goi that.
	import ast
	import os

	tep = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
		os.path.abspath(__file__)))), "don_huy.py")
	with open(tep, encoding="utf-8") as f:
		cay = ast.parse(f.read())
	thay = 0
	for nut in ast.walk(cay):
		if not isinstance(nut, ast.Dict):
			continue
		for khoa, gia_tri in zip(nut.keys, nut.values):
			if not (isinstance(khoa, ast.Constant)
					and khoa.value in ("startDateTime", "endDateTime")):
				continue
			thay += 1
			dung("%s phai la bien so nguyen, khong duoc la chuoi hay cat lat"
				% khoa.value, isinstance(gia_tri, ast.Name))
	la("van con dung hai moc trong loi goi Pancake", thay, 2)
