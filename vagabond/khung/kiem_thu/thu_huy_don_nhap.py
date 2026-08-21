# -*- coding: utf-8 -*-
"""Kiem thu phieu HUY DON CHUA GHI SO va hoan tien (anh Viet giao 21/08/2026).

Khach chot banh, chuyen tien, hai ba tieng sau bao huy. Hoa don moi o dang
nhap nen luong hoan tien cu khong nhan: no neo vao hoa don da ghi so.

Ca dat nhat trong tep nay khong phai ca tinh tien, ma la ca "tra ve dung
CON SO DA NHAN chu khong phai tong don". Khach dat coc mot phan roi huy thi
chi tra lai phan da nhan; lay tong don lam tran la mo duong chi ra mot khoan
chua bao gio nhan duoc.

Nhom ca thu hai chot lai rang phieu nay KHONG di duong khu doanh thu. Don
chua tung duoc ghi so thi khong co doanh thu nao de khu, va de khu duoc thi
truoc het phai ghi so mot to hoa don khong co that.
"""

import io
import os

from vagabond import hoan_tien as ht
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _ma_nguon(ten):
	goi = os.path.dirname(os.path.abspath(ht.__file__))
	return io.open(os.path.join(goi, ten), encoding="utf-8").read()


# ------------------------------------------------------------------ tran


@ca("huỷ đơn nháp: trần là SỐ ĐÃ NHẬN, không phải tổng đơn")
def _():
	# Khach dat banh 2 trieu, moi chuyen coc 500 nghin, roi huy. Chi duoc
	# tra lai 500 nghin. Lay tong don lam tran o day la chi ra 1,5 trieu
	# chua bao gio nhan duoc.
	duoc, tran, _vs = ht.tran_huy_nhap(500000, 2000000)
	dung("lập được phiếu", duoc)
	la("chỉ trả lại đúng phần đã nhận", tran, 500000)
	# Khach chuyen du roi huy: tra lai ca phan du, van bang so da nhan.
	duoc2, tran2, _vs2 = ht.tran_huy_nhap(2100000, 2000000)
	dung("chuyển dư rồi huỷ vẫn lập được", duoc2)
	la("trả lại cả phần dư", tran2, 2100000)
	# Chuyen dung bang don.
	la("chuyển đủ thì trả đủ", ht.tran_huy_nhap(2000000, 2000000)[1], 2000000)


@ca("huỷ đơn nháp: chưa thấy đồng nào về thì KHÔNG lập phiếu chi")
def _():
	# Khong co tien vao thi khong co gi de tra. Cho lap phieu o day la mo
	# duong chuyen tien cho mot nguoi chua tra dong nao.
	for nhan in (0, 0.4, -100000):
		duoc, tran, vi_sao = ht.tran_huy_nhap(nhan, 2000000)
		dung("chặn khi đã nhận %r" % nhan, not duoc)
		la("không cho trả đồng nào", tran, 0.0)
		dung("chỉ đường bấm Huỷ đơn thay vì lập phiếu", "Huỷ đơn" in vi_sao)
		dung("nhắc kiểm đối soát trước", "Đối soát" in vi_sao)


@ca("huỷ đơn nháp: đơn tổng 0 mà tiền đã về vẫn trả lại được")
def _():
	# Ca hiem nhung co that: don nhap bi xoa het dong hang ma tien da chuyen.
	# Luong tien du chan ca nay (tong 0 thi khong tinh duoc phan du), con
	# luong huy thi khong duoc chan: tien khach van dang nam trong tai khoan.
	duoc, tran, _vs = ht.tran_huy_nhap(300000, 0)
	dung("vẫn lập được", duoc)
	la("trả lại đúng số đã nhận", tran, 300000)
	# Doi chieu voi luong tien du de thay hai cua xu khac nhau co chu dich.
	dung("luồng tiền dư thì chặn đơn tổng 0", not ht.tran_tien_du(300000, 0)[0])


# --------------------------------------------------- khong dung toi doanh thu


@ca("huỷ đơn nháp: KHÔNG lập hoá đơn trả hàng, không khử doanh thu")
def _():
	ma = _ma_nguon("hoan_tien.py")
	than = ma.split("def _sinh_chung_tu(")[1].split("\ndef ")[0]
	# Hai loai khong dung toi doanh thu phai thoat SOM, truoc ca doan lap
	# hoa don tra hang.
	dung("hai loại đi chung một nhánh thoát sớm",
		"if loai in (LOAI_TIEN_DU, LOAI_HUY_NHAP):" in than)
	truoc = than.split("if loai in (LOAI_TIEN_DU, LOAI_HUY_NHAP):")[0]
	dung("nhánh đó nằm TRƯỚC đoạn lập hoá đơn trả hàng",
		"_lap_hoa_don_tra(" not in truoc)
	dung("nhánh đó nằm TRƯỚC đoạn thu hồi điểm", "_thu_hoi_diem(" not in truoc)
	dung("nhánh đó nằm TRƯỚC đoạn chuyển Kho Hàng Hủy",
		"_chuyen_kho_huy(" not in truoc)
	# Va phai nam TRUOC ca phep tim kho: mot cai kho chua dung xong khong
	# duoc phep chan duong tra tien cho khach.
	dung("nhánh đó nằm TRƯỚC phép tìm Kho Hàng Hủy", "kho_huy(" not in truoc)


@ca("huỷ đơn nháp: cửa kiểm đòi hoá đơn NHÁP, ngược hẳn cửa hoàn tiền cũ")
def _():
	ma = _ma_nguon("hoan_tien.py")
	cu = ma.split("def _kiem_tra_duoc(")[1].split("\ndef ")[0]
	moi = ma.split("def _kiem_huy_nhap_duoc(")[1].split("\ndef ")[0]
	dung("cửa cũ đòi đã ghi sổ", "cint(si.docstatus) != 1" in cu)
	dung("cửa mới đòi còn nháp", "cint(si.docstatus) != 0" in moi)
	# Phieu giu mon thi khach chua tra tien, khong co gi de hoan.
	dung("cửa mới chặn phiếu tạm tính", "vgb_tam_tinh" in moi)
	# Don nhap ma da co so hoa don dien tu la trang thai bat thuong.
	dung("cửa mới chặn đơn nháp đã mang số hoá đơn điện tử",
		"custom_hddt_so" in moi)
	dung("cửa mới chặn lập phiếu thứ hai", "trang_thai" in moi)


@ca("huỷ đơn nháp: đánh dấu huỷ TRƯỚC, lập phiếu SAU")
def _():
	# Day la ca quan trong nhat ve thu tu. Chuoi cuoi ngay luc 23:00 tu ghi
	# so nhung don nhap da nhan du tien roi xuat hoa don dien tu luon; no
	# chi chua ra don co co vgb_huy. Lam nguoc thu tu ma buoc sau hong thi
	# sang hom sau co mot to hoa don dien tu da gui co quan thue cho cai
	# banh chua bao gio lam.
	ma = _ma_nguon("hoan_tien.py")
	than = ma.split("def tao_huy_nhap(")[1].split("\ndef ")[0]
	vt_huy = than.find("chung_tu.danh_dau_huy(")
	vt_lap = than.find('"doctype": DT')
	dung("có gọi đánh dấu huỷ", vt_huy > 0)
	dung("có lập hồ sơ", vt_lap > 0)
	dung("đánh dấu huỷ đứng TRƯỚC lúc lập hồ sơ", vt_huy < vt_lap)
	# Phai chot du lieu ngay sau khi dat co, khong de treo trong mot giao
	# dich con dang do.
	sau_huy = than[vt_huy:vt_lap]
	dung("chốt dữ liệu ngay sau khi đặt cờ huỷ", "frappe.db.commit()" in sau_huy)


@ca("huỷ đơn nháp: đặt cờ huỷ vẫn phải qua mã OTP quản lý như nút Huỷ đơn")
def _():
	# Cua moi khong duoc tu mo mot duong vong quanh chot kiem soat da co.
	than = _ma_nguon("hoan_tien.py").split("def tao_huy_nhap(")[1].split("\ndef ")[0]
	dung("có nhận tham số otp", "otp=None" in than)
	dung("có gọi phép kiểm OTP", "_otp_kiem(otp" in than)


@ca("huỷ đơn nháp: máy chủ tự tính lại trần, không tin số màn hình gửi lên")
def _():
	than = _ma_nguon("hoan_tien.py").split("def tao_huy_nhap(")[1].split("\ndef ")[0]
	dung("tự đọc lại số đã nhận", "_tien_da_nhan(si)" in than)
	dung("tự tính lại trần", "tran_huy_nhap(nhan" in than)
	dung("chặn khi vượt trần", "tien > tran + 0.5" in than)
	dung("bắt đủ thông tin tài khoản khách", "ten_tk" in than and "so_tk" in than)


# ------------------------------------------------------------------ nhan


@ca("huỷ đơn nháp: loại phiếu có nhãn tiếng Việt riêng, không lẫn với trả hàng")
def _():
	la("nhãn của loại mới", ht.NHAN_LOAI_HOAN[ht.LOAI_HUY_NHAP], "Huỷ đơn chưa ghi sổ")
	la("nhãn trả hàng giữ nguyên", ht.NHAN_LOAI_HOAN[ht.LOAI_TRA_HANG], "Trả hàng")
	la("nhãn tiền nộp thừa giữ nguyên", ht.NHAN_LOAI_HOAN[ht.LOAI_TIEN_DU], "Tiền nộp thừa")
	# De trong van phai doc la Tra hang: moi phieu lap truoc 18/08/2026 deu
	# la phieu tra hang va khong co lenh nao chay len du lieu cu.
	la("để trống vẫn đọc là trả hàng", ht.NHAN_LOAI_HOAN[""], "Trả hàng")
	# Ba loai phai la ba chuoi khac nhau, khong thi bang tong hop gop nham.
	la("ba loại là ba chuỗi khác nhau",
		len({ht.LOAI_TRA_HANG, ht.LOAI_TIEN_DU, ht.LOAI_HUY_NHAP}), 3)


@ca("huỷ đơn nháp: ô Select của trường loại phiếu phải có đủ ba loại")
def _():
	# Thieu o day thi phieu luu xuong bi Frappe tu choi vi gia tri khong nam
	# trong danh sach, va loi chi lo ra dung luc Sales bam Gui duyet.
	khai = [d for d in ht.TRUONG_MOI[ht.DT] if d["fieldname"] == "loai_hoan"]
	la("có khai trường loại phiếu", len(khai), 1)
	tuy_chon = khai[0]["options"].split("\n")
	for x in ("", ht.LOAI_TRA_HANG, ht.LOAI_TIEN_DU, ht.LOAI_HUY_NHAP):
		dung("ô Select có %r" % x, x in tuy_chon)


@ca("huỷ đơn nháp: lý do huỷ là danh sách riêng, không dùng lý do trả hàng")
def _():
	# Ly do tra hang la "Banh hong", "Di ung" - do la chuyen cua hang da
	# giao. Don huy khi chua lam thi ly do khac han.
	dung("có lý do khách đổi ý", "Khach doi y" in ht.LY_DO_HUY)
	dung("có lý do bếp không kịp làm", "Bep khong kip lam" in ht.LY_DO_HUY)
	dung("có lý do Khác để còn ghi rõ", "Khac" in ht.LY_DO_HUY)
	for xau in ("Banh hong", "Di ung", "Giao sai mon", "Giao tre"):
		dung("KHÔNG lẫn lý do của hàng đã giao: %s" % xau, xau not in ht.LY_DO_HUY)
