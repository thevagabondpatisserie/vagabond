"""Tra hang va hoan tien cho khach.

Chot voi anh Viet va chi Dung 16/08/2026.

Vi sao boc lai nut Return cua ERPNext chu khong viet lai tu dau
--------------------------------------------------------------
ERPNext da co san hoa don tra hang (is_return, return_against) va no dung
ve ke toan. Viet lai tu dau la tu de ra mot he ke toan thu hai chay song
song, va hai he do se lech nhau vao mot ngay khong ai doan truoc.

Nhung de nguyen thi thieu ba thu ma nghiep vu banh can:
  1. No tra hang ve DUNG KHO DA XUAT. Nghia la cai banh khach tra vi di
     ung se nam trong kho ban va duoc ban lai cho nguoi tiep theo. Voi
     nganh banh day khong phai loi so sach, day la chuyen co the lam ai
     do nhap vien.
  2. No khong hoi ly do.
  3. No khong biet gi ve so diem.

Nen ham o day lam ba viec do, roi giao phan ke toan lai cho ERPNext.

Dong tien (chi Dung chot 16/08/2026)
------------------------------------
Tien hoan cho khach di THANG tu tai khoan ngan hang cong ty (MB Bank),
KHONG di qua quy tam ung OCB nua. Ly do: quy OCB tro vao tai khoan 1411
Tam ung ca nhan, nen hoan tien qua do thi moi lan tra khach mot cai banh
hong lai thanh "anh Viet tam ung them mot khoan", va sau mot nam so du
1411 phinh len bang nhung thu khong phai tam ung.

Phieu chi de o trang thai NHAP. May khong ghi so ho: luc do tien chua that
su chuyen di. Ke toan mo phieu, chuyen khoan that, dinh kem uy nhiem chi,
roi moi ghi so.
"""

import base64
import json
import re

import frappe
from frappe.utils import add_days, cint, flt, now_datetime, nowdate

from vagabond.lib import cfg, sdt

DT = "Vagabond Hoan Tien"
SI = "Sales Invoice"
PE = "Payment Entry"

TEN_KHO_HUY = "Kho Hàng Hủy"
# Cu phap noi dung chuyen khoan, anh Viet chot 16/08/2026.
#
# Doi tu "HT <ma>" sang chuoi day du: dong sao ke ngan hang chi co mot o
# noi dung, va do la thu duy nhat ke toan doc duoc sau ba thang. "HT" thi
# ngan gon nhung khong ai doan ra la gi; "THE VAGABOND HOAN TIEN" thi
# nhin phat biet ngay.
TIEN_TO_CK = "THE VAGABOND HOAN TIEN"

LY_DO = ("Khach doi y", "Banh hong", "Di ung", "Giao sai mon", "Giao tre", "Khac")

# Ly do nao thi hang chac chan KHONG dung lai duoc nua. Ca sau nay deu vao
# kho huy het, nhung ba ly do nay con dung de bao cao ty le hong cho bep.
LY_DO_HONG = {"Banh hong", "Di ung", "Giao sai mon"}

# --------------------------------------------------- tien nop thua
#
# Anh Viet 18/08/2026: *"anh nho em thiet ke luon 1 nut rieng ke ben nut
# Hoan tien do la nut Chuyen lai cho khach thanh toan du... cung co nhieu
# truong hop nhu vay, vi du khach chuyen bao gom ca tien ship nhung ma sau
# do doi y muon den tiem pickup, can chuyen lai cho khach phan tien ship bi
# du ra"*.
#
# VI SAO PHAI TACH RIENG KHOI LUONG HOAN TIEN
#
# Luong hoan tien hien co duoc dung cho TRA HANG: khach tra banh ve, minh
# tra tien lai, doanh thu phai khu di dung phan hang quay ve. Voi ca do thi
# lap hoa don tra hang la dung.
#
# Tien nop thua khong phai tra hang. Khach nhan du hang, gia dung, doanh
# thu dung. Khach chi chuyen du tien. Khoan du do la tien minh GIU HO khach
# va phai tra lai, khong phai doanh thu bi khu.
#
# Ca 91433 ngay 18/08/2026 la vi du: khach dat banh 18cm chuyen 1.100.000,
# bep thieu nguyen lieu nen xin doi xuong 16cm con 915.000, hoa don dien tu
# 10609 da xuat DUNG 915.000. Neu chay duong tra hang thi so ghi doanh thu
# 730.000 trong khi to hoa don ghi 915.000, lech dung 185.000, va tu do
# sinh ra ap luc di sua mot to hoa don DANG DUNG cho khop mot con so DANG
# SAI. Anh Viet da tu choi phieu do va chuyen sang duong nay.
LY_DO_DU = (
	"Doi size nho hon",
	"Khach tu den lay, khong giao",
	"Bo bot mon",
	"Chuyen du tien",
	"Khac",
)

LOAI_TRA_HANG = "Tra hang"
LOAI_TIEN_DU = "Tien nop thua"

# --------------------------------------------------- huy don chua ghi so
#
# Anh Viet 21/08/2026: khach chot banh, chuyen tien, hai ba tieng sau bao
# huy. Hoa don moi o dang nhap nen khong co gi de dinh vao phieu hoan tien.
#
# VI SAO PHAI CO CUA RIENG, KHONG DUNG LAI HAI CUA CU
#
# Ca hai luong cu deu neo vao mot hoa don DA GHI SO. `_kiem_tra_duoc` tu
# choi thang moi hoa don docstatus khac 1, va cau tu choi la "Bill chua ghi
# so thi sua hoac huy thang la duoc". Cau do dung khi chua co dong nao chay
# qua, nhung o day tien khach DA VE that. Huy thang thi con lai mot khoan
# tien vao khong chung tu va mot khoan tien ra khong chung tu.
#
# CAI BAY THAT SU KHONG NAM O KE TOAN, NO NAM O DONG HO
#
# `ban_hang.tu_ghi_so_cuoi_ngay` chay khoang 23:00 moi ngay, quet don
# Pancake con nhap va TU GHI SO nhung don da du dieu kien, roi phat hanh
# hoa don dien tu luon. "Du dieu kien" chinh la chuyen khoan va SePay da
# thay du tien - dung cai don nay. No chi chua ra don co co `vgb_huy`.
#
# Nen viec dau tien cua `tao_huy_nhap` khong phai lap phieu, ma la DANH DAU
# HUY cai don nhap do. Danh dau truoc, lap phieu sau. Lam nguoc lai ma buoc
# sau hong thi con lai mot don chua danh dau, va toi 23:00 no thanh mot to
# hoa don dien tu da gui co quan thue cho cai banh chua bao gio lam - dung
# vung cam anh Viet chot 13/08.
LOAI_HUY_NHAP = "Huy don chua ghi so"

# Don Pancake DA HUY ma chua bao gio ve ERPNext. Khac han LOAI_HUY_NHAP: ca
# kia con mot hoa don nhap de bam vao, ca nay khong co gi ca. Xem dau tep
# vagabond/don_huy.py.
LOAI_HUY_PANCAKE = "Huy don Pancake"

LY_DO_HUY = (
	"Khach doi y",
	"Khach dat nham ngay",
	"Bep khong kip lam",
	"Het nguyen lieu",
	"Trung don",
	"Khac",
)

# Chu tieng Viet cho hai o Select. Chi dung khi XUAT RA cho nguoi doc (tep
# Excel cua chi Dung); trong co so du lieu van la chuoi khong dau, vi doi
# gia tri Select la phai chay len toan bo du lieu cu.
NHAN_LOAI_HOAN = {
	"": "Trả hàng",
	LOAI_TRA_HANG: "Trả hàng",
	LOAI_TIEN_DU: "Tiền nộp thừa",
	LOAI_HUY_NHAP: "Huỷ đơn chưa ghi sổ",
	LOAI_HUY_PANCAKE: "Huỷ đơn Pancake",
}
NHAN_TRANG_THAI = {
	"Cho chi": "Chờ chi",
	"Da chi": "Đã chi",
	"Da doi soat": "Đã đối soát",
	"Hoan thanh": "Hoàn thành",
	"Da huy": "Đã huỷ / Từ chối",
}


def _tien_vn(v):
	"""So tien dang nguoi Viet doc duoc: 1234567 -> "1.234.567".

	Ham nay dang duoc goi o BA cho trong tep tu truoc ma CHUA BAO GIO duoc
	dinh nghia. Hai cho nam trong nhanh bao loi nen khong ai vap; cho thu
	ba nam giua luong sinh chung tu cua phieu tien nop thua, va no da no
	that ngay 19/08/2026 voi phieu HT-2026-00899:

	    NameError: name '_tien_vn' is not defined

	Hau qua khong dung o mot dong bao loi xau. Xem ghi chu trong doi_soat().
	"""
	try:
		return "{:,.0f}".format(float(v or 0)).replace(",", ".")
	except Exception:
		return str(v)


def tran_tien_du(da_nhan, tong_don):
	"""So tien du toi da duoc phep chuyen lai. THUAN.

	Tra ve (duoc, tran, cau_nhac). Tran chinh la phan khach chuyen VUOT
	tong don. Chan cung o may chu chu khong tin o nhap tren man (QT-19).

	Vi sao khong lay tran bang tong don nhu luong tra hang: tra hang thi
	toi da tra lai ca don, con tien du thi toi da chi bang dung phan du.
	Cho vuot qua la chi mot khoan chua bao gio nhan duoc.
	"""
	nhan, tong = flt(da_nhan), flt(tong_don)
	du = round(nhan - tong, 0)
	if tong <= 0:
		return False, 0.0, "Đơn này tổng tiền bằng 0 nên không tính được phần dư."
	if du <= 0.5:
		return False, 0.0, (
			"Đơn này chưa nhận dư đồng nào: đã nhận %s đ, đơn %s đ. Nếu khách "
			"trả hàng thì dùng nút Hoàn tiền, còn nếu tiền vừa về mà máy chưa "
			"thấy thì chờ đối soát rồi mở lại màn này."
			% (_tien_vn(nhan), _tien_vn(tong))
		)
	return True, du, ""


def tran_huy_nhap(da_nhan, tong_don):
	"""So tien toi da duoc tra lai khi huy mot don CHUA GHI SO. THUAN.

	Tra ve (duoc, tran, cau_nhac).

	Tran la so tien THAT SU DA NHAN, khong phai tong don. Hai con so nay
	khac nhau o ca khach dat coc mot phan: don 2.000.000 ma khach moi chuyen
	500.000 thi huy don chi duoc tra lai 500.000. Lay tong don lam tran o
	day la mo duong chi ra mot khoan chua bao gio nhan duoc.

	Chua thay dong nao ve thi KHONG lap phieu. Khong co tien vao thi khong
	co gi de tra, va cai can lam chi la bam Huy don.
	"""
	nhan, tong = flt(da_nhan), flt(tong_don)
	if nhan <= 0.5:
		return False, 0.0, (
			"Máy chưa thấy đồng nào về cho đơn này nên chưa có gì để hoàn. Nếu chỉ "
			"cần huỷ đơn thì bấm nút Huỷ đơn là đủ. Còn nếu chắc chắn khách đã "
			"chuyển thật mà máy không thấy, mở màn Đối soát kiểm lại trước, đừng "
			"lập phiếu chi khi chưa biết tiền có về hay không."
		)
	if tong > 0 and nhan > tong + 0.5:
		# Khach chuyen vuot roi huy: van tra lai DUNG so da nhan, ca phan
		# vuot. Ghi lai o day de nguoi doc sau khong tuong la bo sot.
		return True, round(nhan, 0), ""
	return True, round(nhan, 0), ""


def _tien_da_nhan(si):
	"""Tien SePay da nhan cho mot hoa don. Khong doc duoc thi tra 0."""
	try:
		from vagabond.ban_hang import _sepay_theo_don, cfg

		ma = str(si.get("custom_pancake_display_id") or "").strip()
		if not ma:
			return 0.0
		g = _sepay_theo_don(cfg().pancake_shop_id, [ma]).get(ma)
		return flt((g or {}).get("nhan"))
	except Exception:
		return 0.0


TRUONG_MOI = {
	# Tu choi hoan tien (anh Viet 18/08/2026): "phong truong hop khach doi y
	# hoac bang chung khong hop le". QT-20 cam xoa vinh vien, nen tu choi la
	# huy MEM co ghi vet: ai tu choi, luc nao, vi ly do gi. Ba truong nay
	# la ban ghi vet do.
	DT: [
		{
			# De trong doc la "Tra hang": moi phieu lap truoc 18/08/2026 deu
			# la phieu tra hang, va khong co lenh nao chay len du lieu cu.
			"fieldname": "loai_hoan", "label": "Loại phiếu",
			"fieldtype": "Select", "insert_after": "so_tien",
			"options": "\n".join(("", LOAI_TRA_HANG, LOAI_TIEN_DU, LOAI_HUY_NHAP, LOAI_HUY_PANCAKE)),
			"read_only": 1,
			"description": (
				"Trả hàng thì khử doanh thu bằng hoá đơn trả hàng. Tiền nộp thừa "
				"và Huỷ đơn chưa ghi sổ thì KHÔNG đụng doanh thu: một bên trả lại "
				"khoản khách chuyển dư, một bên trả lại tiền của đơn chưa từng "
				"được ghi nhận doanh thu."
			),
		},
		{
			# Don Pancake da huy khong co Sales Invoice de bam vao, nen ma
			# don phai co cho dung cua no. Chi Dung chot 21/08/2026 dieu 4:
			# theo doi 131 theo SO DON, vi don online do chung vao mot ma
			# khach "Khach le Online".
			"fieldname": "ma_don_pancake", "label": "Mã đơn Pancake",
			"fieldtype": "Data", "insert_after": "hoa_don", "read_only": 1,
			"description": (
				"Điền khi phiếu thuộc loại Huỷ đơn Pancake. Đơn đó chưa bao giờ "
				"có hoá đơn trong ERPNext nên không có gì để liên kết."
			),
		},
		{
			# Phiếu thu của luồng huỷ đơn Pancake. Luồng đó sinh HAI chân:
			# một phiếu thu cho khoản khách đã chuyển vào, một phiếu chi trả
			# lại. Ô `phieu_chi` sẵn có giữ chân ra, còn chân vào trước đây
			# không có chỗ nào ghi, nên mở phiếu ra không lần được cặp bút
			# toán khớp nhau.
			"fieldname": "phieu_thu", "label": "Phiếu thu khoản khách chuyển",
			"fieldtype": "Link", "options": "Payment Entry",
			"insert_after": "phieu_chi", "read_only": 1,
			"description": (
				"Chỉ có ở phiếu thuộc loại Huỷ đơn Pancake. Đơn đó chưa từng ghi "
				"doanh thu nên khoản khách chuyển vào là tiền giữ hộ, phải ghi "
				"nhận trước khi trả lại."
			),
		},
		{
			"fieldname": "sec_tc", "label": "Từ chối hoàn tiền",
			"fieldtype": "Section Break", "insert_after": "noi_dung_ck",
		},
		{
			"fieldname": "ly_do_tu_choi", "label": "Lý do từ chối",
			"fieldtype": "Small Text", "insert_after": "sec_tc", "read_only": 1,
			"description": "Bắt buộc điền khi bấm Từ chối. In lại trên màn chi tiết.",
		},
		{
			"fieldname": "nguoi_tu_choi", "label": "Người từ chối",
			"fieldtype": "Data", "insert_after": "ly_do_tu_choi", "read_only": 1,
		},
		{
			"fieldname": "ngay_tu_choi", "label": "Ngày từ chối",
			"fieldtype": "Datetime", "insert_after": "nguoi_tu_choi", "read_only": 1,
		},
		# Doi chieu TAY khoan tien VAO (anh Viet 19/08/2026, ca Ms.Giang).
		#
		# Cach doi soat tu dong dua hoan toan vao noi dung chuyen khoan: no
		# tim mach S<shop>O<so don>T do Pancake sinh trong ma QR. Khach nao
		# tu go noi dung - "TRUONG LINH GIANG chuyen tien" - thi khong mach
		# nao de bam, va don trong nhu chua nhan dong nao du tien da nam
		# trong tai khoan cong ty. Truong nay giu dong Bank Transaction ma
		# NGUOI da nhin va xac nhan, de chi Dung quyet chi co can cu.
		{
			"fieldname": "loi_sinh_ct", "label": "Lỗi khi sinh chứng từ",
			"fieldtype": "Small Text", "insert_after": "ngay_tu_choi", "read_only": 1,
			"description": (
				"Tiền đã ra và đã khớp sao kê nhưng máy chưa sinh được hoá đơn trả "
				"hàng hoặc phiếu chi. Để trống là mọi thứ bình thường."
			),
		},
		{
			"fieldname": "sec_gd_vao", "label": "Giao dịch tiền vào đã đối chiếu",
			"fieldtype": "Section Break", "insert_after": "ngay_tu_choi",
		},
		{
			"fieldname": "gd_vao", "label": "Giao dịch tiền vào",
			"fieldtype": "Link", "options": "Bank Transaction",
			"insert_after": "sec_gd_vao", "read_only": 1,
			"description": (
				"Khoản khách đã chuyển vào, do người đối chiếu tay chọn khi nội "
				"dung chuyển khoản không mang mã đơn."
			),
		},
		{
			"fieldname": "nguoi_gan_gd_vao", "label": "Người đối chiếu",
			"fieldtype": "Data", "insert_after": "gd_vao", "read_only": 1,
		},
		# Khop SePay THU CONG cho dong tien RA (anh Viet 24/08/2026).
		#
		# Khac han hai truong `gd_vao` ngay tren: o do la tien khach chuyen
		# VAO, con o day la lenh chi da di RA. Nham hai chuyen nay la ghi so
		# nguoc chieu, nen chung phai co hai o rieng va hai cai ten noi ro.
		{
			"fieldname": "nguoi_khop_tay", "label": "Người khớp SePay thủ công",
			"fieldtype": "Data", "insert_after": "ngay_doi_soat", "read_only": 1,
			"description": (
				"Để trống nghĩa là máy tự khớp theo nội dung chuyển khoản. Có tên "
				"nghĩa là người này đã nhìn sao kê và tự chọn dòng tiền ra."
			),
		},
		{
			"fieldname": "ngay_khop_tay", "label": "Lúc khớp thủ công",
			"fieldtype": "Datetime", "insert_after": "nguoi_khop_tay", "read_only": 1,
		},
		# Luong KET THUC phieu hoan tien (anh Viet 19/08/2026): *"Thiet ke
		# nut de dinh kem uy nhiem chi cho phieu hoan tien sau khi da doi
		# soat -> chi Dung vao dinh kem file cho sales lay de gui khach ->
		# hoan thanh -> may tu ghi so. Hien chua co luong ket thuc cho cai
		# phieu nay."*
		#
		# Vi sao van giu HAI nhip chu khong ghi so ngay luc dinh tep: chi
		# Dung chot 16/08 rang nut ghi so phai nam trong tay ke toan. Dinh
		# tep la mot viec, quyet ghi so la mot viec khac - va giua hai nhip
		# do la khoang thoi gian Sales tai tep ve gui khach. Gop lam mot thi
		# mat dung cai khoang ay.
		#
		# Ban than TEP UNC khong luu o day. No dinh vao Payment Entry, vi
		# hook chan_thieu_uy_nhiem_chi dem tep tren Payment Entry chu khong
		# dem o day; va vi o hoa don nay con dinh anh bang chung cua Sales,
		# tron hai loai vao mot cho thi man hinh khong tach ra duoc nua.
		{
			"fieldname": "nguoi_dinh_unc", "label": "Người đính uỷ nhiệm chi",
			"fieldtype": "Data", "insert_after": "ngay_gan_gd_vao", "read_only": 1,
		},
		{
			"fieldname": "ngay_dinh_unc", "label": "Lúc đính uỷ nhiệm chi",
			"fieldtype": "Datetime", "insert_after": "nguoi_dinh_unc", "read_only": 1,
		},
		{
			"fieldname": "nguoi_hoan_thanh", "label": "Người kết thúc phiếu",
			"fieldtype": "Data", "insert_after": "ngay_dinh_unc", "read_only": 1,
		},
		{
			"fieldname": "ngay_hoan_thanh", "label": "Lúc kết thúc phiếu",
			"fieldtype": "Datetime", "insert_after": "nguoi_hoan_thanh", "read_only": 1,
		},
		{
			"fieldname": "ngay_gan_gd_vao", "label": "Lúc đối chiếu",
			"fieldtype": "Datetime", "insert_after": "nguoi_gan_gd_vao", "read_only": 1,
		},
		# NOI MA HOA DON THAY THE (anh Viet 20/08/2026).
		#
		# Chi Dung: *"khong can nut click vao m-invoice vi moi hoa don ben
		# m-invoice khong co link rieng. Chi ay se tu tim hoa don roi tu thay
		# the."* Anh Viet: *"vi du hoa don da thay the roi thi em viet luong
		# automation de noi ma hoa don da thay the do vao don hang truoc do
		# va vao phieu hoan tien luon duoc khong?"*
		#
		# Ba truong nay la cho ghi ma do. Viec THAY THE van do chi Dung lam
		# tay ben M-Invoice; he thong tuyet doi khong phat hanh, khong huy,
		# khong thay the mot to nao - anh Viet da dan 13/08/2026.
		{
			"fieldname": "sec_htt", "label": "Hoá đơn thay thế",
			"fieldtype": "Section Break", "insert_after": "ngay_gan_gd_vao",
		},
		{
			"fieldname": "so_hddt_thay_the", "label": "Số hoá đơn thay thế",
			"fieldtype": "Data", "insert_after": "sec_htt", "read_only": 1,
			"description": (
				"Số tờ hoá đơn đã thay thế tờ cũ bên M-Invoice. Ghi từ màn phiếu "
				"hoàn tiền, máy tự nối ngược lên đơn hàng gốc."
			),
		},
		{
			"fieldname": "ky_hieu_hddt_thay_the", "label": "Ký hiệu hoá đơn thay thế",
			"fieldtype": "Data", "insert_after": "so_hddt_thay_the", "read_only": 1,
		},
		{
			"fieldname": "nguoi_ghi_thay_the", "label": "Người ghi hoá đơn thay thế",
			"fieldtype": "Data", "insert_after": "ky_hieu_hddt_thay_the", "read_only": 1,
		},
		{
			"fieldname": "ngay_ghi_thay_the", "label": "Lúc ghi hoá đơn thay thế",
			"fieldtype": "Datetime", "insert_after": "nguoi_ghi_thay_the", "read_only": 1,
		},
	],
	# Doi ung tren DON HANG GOC. Ghi o ca hai noi chu khong chi mot: ke toan
	# tra tu don hang ra, sales tra tu phieu hoan tien ra, va hai duong do
	# khong bao gio gap nhau neu chi ghi mot ben.
	"Sales Invoice": [
		{
			"fieldname": "custom_hddt_thay_the", "label": "Hoá đơn thay thế",
			"fieldtype": "Data", "insert_after": "custom_hddt_so", "read_only": 1,
			"description": (
				"Tờ hoá đơn điện tử đã thay thế tờ ghi ở ô Số hoá đơn. Ghi từ màn "
				"phiếu hoàn tiền trên app. Máy KHÔNG tự phát hành hay huỷ tờ nào."
			),
		},
		{
			"fieldname": "custom_hddt_thay_the_luc", "label": "Lúc ghi hoá đơn thay thế",
			"fieldtype": "Datetime", "insert_after": "custom_hddt_thay_the", "read_only": 1,
		},
		{
			"fieldname": "custom_hddt_thay_the_phieu", "label": "Phiếu hoàn tiền ghi nhận",
			"fieldtype": "Data", "insert_after": "custom_hddt_thay_the_luc", "read_only": 1,
		},
	],
	"Payment Entry": [
		{
			"fieldname": "vgb_hoan_tien",
			"label": "Phiếu chi hoàn tiền khách",
			"fieldtype": "Link",
			"options": DT,
			"insert_after": "reference_no",
			"read_only": 1,
			"description": (
				"Phiếu chi sinh từ luồng hoàn tiền. Phiếu mang cờ này thì bắt buộc "
				"phải đính kèm uỷ nhiệm chi mới ghi sổ được."
			),
		}
	]
}


# ------------------------------------------------------------------ cai dat


def _cd():
	"""Kho huy va tai khoan chi. Roi ve mac dinh khi Cai dat chua khai."""
	try:
		c = cfg()
	except Exception:
		return {"kho_huy": "", "tk_chi": ""}
	return {
		"kho_huy": (c.get("kho_hang_huy") or "").strip(),
		"tk_chi": (c.get("tk_hoan_tien") or "").strip(),
	}


def _cong_ty(si=None):
	if si and si.get("company"):
		return si["company"]
	return frappe.defaults.get_global_default("company") or ""


def kho_huy(cong_ty=None):
	"""Kho Hang Huy dang dung. Tu tao neu chua co."""
	ten = _cd()["kho_huy"]
	if ten and frappe.db.exists("Warehouse", ten):
		return ten
	return dung_kho_huy(cong_ty)


def dung_kho_huy(cong_ty=None):
	"""Tao kho Hang Huy neu chua co. LAP LAI DUOC, goi bao nhieu lan cung duoc.

	Goi tu patch dong_bo_cau_truc nen moi lan Migrate deu duoc dung lai.

	Kho nam TRUC TIEP duoi All Warehouses chu khong duoi bep nao: hang huy
	khong thuoc bep nao ca, va de duoi mot bep thi bao cao ton kho cua bep
	do se mang theo hang da chet.
	"""
	cty = cong_ty or _cong_ty()
	if not cty:
		return ""
	viet_tat = frappe.db.get_value("Company", cty, "abbr") or ""
	ten_day_du = "%s - %s" % (TEN_KHO_HUY, viet_tat) if viet_tat else TEN_KHO_HUY
	if frappe.db.exists("Warehouse", ten_day_du):
		return ten_day_du
	# Co the ai do da tao tay voi ten khac hoa; tim theo warehouse_name truoc.
	cu = frappe.db.get_value("Warehouse", {"warehouse_name": TEN_KHO_HUY, "company": cty}, "name")
	if cu:
		return cu
	goc = frappe.db.get_value("Warehouse", {"company": cty, "is_group": 1, "parent_warehouse": ["is", "not set"]}, "name")
	doc = frappe.get_doc(
		{
			"doctype": "Warehouse",
			"warehouse_name": TEN_KHO_HUY,
			"company": cty,
			"is_group": 0,
			"parent_warehouse": goc,
			"disabled": 0,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc.name


def tk_chi(cong_ty=None):
	"""Tai khoan ngan hang CONG TY dung de chi hoan tien.

	Chi Dung chot 16/08/2026: MB Bank, khong dung quy tam ung OCB.

	Neu Cai dat chua khai thi tu tim mot Bank Account cua cong ty. KHONG
	roi ve tai khoan bat ky: chi nham tai khoan la tien ra khoi mot noi
	khong ai theo doi.
	"""
	ten = _cd()["tk_chi"]
	if ten and frappe.db.exists("Bank Account", ten):
		return ten
	cty = cong_ty or _cong_ty()
	ds = frappe.get_all(
		"Bank Account",
		filters={"company": cty, "is_company_account": 1},
		fields=["name", "account"],
		limit_page_length=0,
	)
	# Uu tien tai khoan tro vao 112x (tien gui ngan hang) chu khong phai
	# 1411 (tam ung ca nhan) - day chinh la cho chi Dung vua be lai.
	for d in ds:
		if str(d.get("account") or "").strip().startswith("112"):
			return d["name"]
	return ds[0]["name"] if ds else ""


# --------------------------------------------------------------- phep tinh
#
# Hai ham THUAN, khong doc co so du lieu. Bo kiem thu chay duoc khong can site.


def noi_dung_ck(ma_hoa_don):
	"""Noi dung chuyen khoan ke toan go vao MB Biz. THUAN.

	Cu phap anh Viet chot 16/08/2026:

	    THE VAGABOND HOAN TIEN <ma hoa don goc>

	Vi sao mang ma HOA DON GOC chu khong mang ma phieu HT-: ke toan, khach,
	va ca nguoi doc sao ke sau nay deu tra cuu theo ma don. Mot dong sao ke
	ghi "HT-2026-00775" thi khong ai biet la cua don nao neu khong tra bang.

	Vi sao doi soat theo NOI DUNG chu khong theo SO TIEN: hai khach cung
	duoc hoan 250.000 d trong mot ngay la chuyen thuong, do theo so tien la
	khop nham.
	"""
	return "%s %s" % (TIEN_TO_CK, str(ma_hoa_don or "").strip())


# Ma hoa don tren he co HAI dang, va day la cho de sai nhat cua ca luong
# doi soat. Em dem 16/08/2026 tren 43.458 hoa don:
#
#     HDB-2026-01593     dang cu,  HAI nhom so   - chiem phan lon
#     HDB-26-08-00323    dang moi, BA nhom so
#
# Anh Viet dua regex HDB-\d+-\d+-\d+; regex do bat dung dang moi va BO SOT
# toan bo dang cu. Nen o day noi thanh 1 den 3 nhom so, va van chan hai dau
# de "HDB-2026-0160" khong an nham giao dich cua "HDB-2026-01604" - dung
# cai bay da gap voi ma WOO.
RX_MA_HD = re.compile(r"(?<![0-9A-Za-z])(HDB-[0-9]+(?:-[0-9]+){1,3})(?![0-9A-Za-z])", re.IGNORECASE)


def _got(chu):
	"""Bo moi ky tu khong phai chu hoac so, roi viet HOA. THUAN.

	Vi sao can: ngan hang khong tra lai noi dung y nguyen. Cung mot lenh
	chi, sao ke co the ve thanh "THE VAGABOND HOAN TIEN HDB 26 08 00323"
	(mat dau gach), hoac dinh them ma tham chieu o hai dau. So hai chuoi
	tho voi nhau la truot.
	"""
	return re.sub(r"[^0-9A-Za-z]+", "", str(chu or "")).upper()


def tim_ma_hoa_don(mo_ta):
	"""Doc mot dong sao ke, tra ve ma hoa don nam trong do. THUAN.

	Tra chuoi rong neu khong thay. Dung cho duong SePay quet tien RA: doc
	dong tien roi tu tim xem no thuoc phieu nao, khong can biet truoc.
	"""
	m = RX_MA_HD.search(str(mo_ta or ""))
	return m.group(1).upper() if m else ""


def khop_giao_dich(mo_ta, ma_hoa_don):
	"""Mot dong sao ke co phai la lenh chi cua don nay khong. THUAN.

	Xet HAI duong, trung mot duong la khop:
	  1. Doc thang ma hoa don trong mo ta, khi dau gach con nguyen.
	  2. So sau khi got het ky tu ngan cach, bat duoc ca dong bi ngan hang
	     lam mat dau gach.
	"""
	ma = str(ma_hoa_don or "").strip()
	if not ma:
		return False
	if tim_ma_hoa_don(mo_ta).upper() == ma.upper():
		return True
	g_ma, g_mo = _got(ma), _got(mo_ta)
	if not g_ma or g_ma not in g_mo:
		return False
	# Chan hai dau tren ban da got: ma ngan khong duoc an nham ma dai.
	vt = g_mo.find(g_ma)
	sau = g_mo[vt + len(g_ma):vt + len(g_ma) + 1]
	return not sau.isdigit()


def ma_do_soat(ho_so):
	"""Chuỗi dùng để dò dòng sao kê cho một hồ sơ hoàn tiền. THUẦN.

	Nhận một dict (hoặc doc) có `hoa_don`, `loai_hoan`, `noi_dung_ck`.
	Trả chuỗi rỗng nghĩa là hồ sơ này chưa dò được, phải bỏ qua.

	VÌ SAO KHÔNG PHẢI LÚC NÀO CŨNG LÀ MÃ HOÁ ĐƠN
	----------------------------------------------
	Phiếu hoàn của luồng trả hàng luôn neo vào một hoá đơn, nên mã hoá đơn
	vừa là khoá vừa là thứ ghi trong nội dung chuyển khoản.

	Phiếu hoàn của đơn Pancake đã huỷ thì KHÔNG có hoá đơn nào - đó chính là
	lý do luồng đó tồn tại. Thứ duy nhất đi được vào ô nội dung chuyển khoản
	là mã đơn.

	Dò theo CẢ CÂU nội dung chuyển khoản chứ không dò theo mã đơn trần. Mã
	đơn Pancake chỉ có năm chữ số, mà `khop_giao_dich` chỉ chặn chữ số ở
	phía SAU chứ không chặn phía trước, nên dò "92252" sẽ dính nhầm vào một
	dòng chứa "192252". Cả câu "THE VAGABOND HOAN TIEN 92252" thì không.
	"""
	g = ho_so.get if hasattr(ho_so, "get") else (lambda k, d=None: getattr(ho_so, k, d))
	hd = str(g("hoa_don") or "").strip()
	if hd:
		return hd
	if str(g("loai_hoan") or "").strip() == LOAI_HUY_PANCAKE:
		return str(g("noi_dung_ck") or "").strip()
	return ""


def chon_ma_khop(mo_ta, ds_ma):
	"""Trong danh sach ma dang cho, ma nao khop voi dong sao ke nay. THUAN.

	Tra chuoi rong neu khong ma nao khop.

	Vi sao co ham nay, va day la lan thu BA trong ngay 16/08/2026
	------------------------------------------------------------
	Sang nay mat mot ban va vi hai cho dinh tuyen chep gan giong nhau roi
	lech nhau. Chieu nay lai suyt chep regex vao bo kiem. Va toi nay, khi
	chay thu tren he ngay sau khi deploy v192, phat hien dung cai do lan
	nua: hai duong doi soat cung mot viec nhung dung hai phep khac nhau.

	    doi_soat()       chay theo gio, doc Bank Transaction -> khop_giao_dich
	    sepay_tien_ra()  SePay goi thang                     -> tim_ma_hoa_don

	khop_giao_dich co duong got nen bat duoc dong bi ngan hang lam mat dau
	gach. tim_ma_hoa_don thi khong. Nen cung mot dong tien, vao duong nay
	thi khop, vao duong kia thi thanh mo coi.

	Nay ca hai duong deu di qua ham nay. Mot phep, mot cho.
	"""
	mo = str(mo_ta or "")
	if not mo:
		return ""
	# Uu tien doc thang ma trong mo ta: nhanh, va chac chan dung khi dau
	# gach con nguyen.
	ma = tim_ma_hoa_don(mo)
	if ma and ma in {str(x or "").upper() for x in (ds_ma or [])}:
		return ma
	# Khong doc duoc thi doi chieu tung ma dang cho, qua duong got.
	for x in ds_ma or []:
		if khop_giao_dich(mo, x):
			return str(x)
	return ""


def ty_le_hop_le(so_tien_hoan, tong_don):
	"""So tien hoan nay co nam trong tong don khong. THUAN.

	Tra (duoc, cau_nhac). Chan cung o may chu chu khong tin o nhap tren man
	(QT-19). Cau nhac viet theo QT-24: noi ro nguoi dung lam gi tiep.
	"""
	tien, tong = flt(so_tien_hoan), flt(tong_don)
	if tong <= 0:
		return False, "Đơn này tổng tiền bằng 0 nên không có gì để hoàn."
	if tien <= 0:
		return False, "Số tiền hoàn phải lớn hơn 0. Nhập lại giúp em."
	if tien > tong + 0.5:
		return False, (
			"Số tiền hoàn %s đ lớn hơn tổng đơn %s đ. Sửa lại số tiền cho nhỏ hơn "
			"hoặc bằng tổng đơn rồi gửi lại."
			% ("{:,.0f}".format(tien).replace(",", "."), "{:,.0f}".format(tong).replace(",", "."))
		)
	return True, ""


# --------------------------------------------------------------- viec chinh


@frappe.whitelist()
def tao(
	si_name=None,
	ly_do=None,
	dien_giai="",
	so_tien=0,
	ten_tk="",
	so_tk="",
	ngan_hang="",
	sdt_khach="",
	tep=None,
	otp=None,
):
	"""Sales gui YEU CAU hoan tien. Chua sinh chung tu, chua dong tien nao.

	Anh Viet chot 16/08/2026: doi tu luong "bam la xong" sang luong CO DUYET
	--------------------------------------------------------------------
	Truoc do mot cu bam la sinh ngay bon thu: hoa don tra, but diem, phieu
	kho, phieu chi. Doi lai bang mot ma PIN quan ly go tai quay.

	Nay tach lam hai nhip:
	  Nhip 1 (ham nay)  - Sales lap YEU CAU. Khong sinh chung tu nao het.
	  Nhip 2 (_sinh_chung_tu) - chi chay khi SePay bao TIEN DA RA THAT.

	Vi sao bo ma PIN: PIN o quay chan duoc mot nguoi go nham, nhung no khong
	chan duoc mot khoan chi sai - vi luc go PIN thi tien van chua di dau ca.
	Cua duyet that nam o ke toan, la nguoi cam tay chuyen khoan. Nen cai
	phai bat buoc khong phai ma PIN ma la BANG CHUNG: anh chup khach phan
	anh, anh banh hong. Khong co anh thi khong gui duoc yeu cau.

	Va vi sao chung tu doi den luc tien ra moi sinh: yeu cau bi tu choi giua
	chung la chuyen thuong. Sinh hoa don tra tu dau roi bi tu choi thi phai
	di huy mot to da ghi so, tuc la de lai vet trong so sach cho mot viec
	chua bao gio xay ra.
	"""
	from vagabond.ban_hang import _kiem_quyen

	# KHONG con hoi ma PIN (anh Viet chot 16/08/2026). Tham so otp giu lai
	# de man cu goi vao khong vo, nhung khong dung den.
	_kiem_quyen()
	si = frappe.get_doc(SI, si_name)
	_kiem_tra_duoc(si)

	ly_do = (ly_do or "").strip()
	if ly_do not in LY_DO:
		frappe.throw("Phải chọn lý do hoàn. Chọn một trong: %s." % ", ".join(LY_DO))
	if ly_do == "Khac" and not (dien_giai or "").strip():
		frappe.throw("Lý do \"Khác\" thì phải ghi rõ vì sao hoàn. Gõ vào ô Diễn giải giúp em.")

	# TRAN SO TIEN TINH LAI O MAY CHU (QT-19). Man co chan roi, nhung con so
	# di qua duong mang thi khong tin duoc.
	tien = flt(so_tien) or flt(si.grand_total)
	duoc, nhac = ty_le_hop_le(tien, flt(si.grand_total))
	if not duoc:
		frappe.throw(nhac)

	tk = re.sub(r"\s+", "", str(so_tk or ""))
	if not tk or not (ten_tk or "").strip() or not (ngan_hang or "").strip():
		frappe.throw(
			"Còn thiếu thông tin tài khoản nhận tiền. Điền đủ tên ngân hàng, số tài "
			"khoản và tên chủ tài khoản của khách rồi gửi lại."
		)

	# BANG CHUNG BAT BUOC. Ke toan ngoi xa quay, khong nhin thay cai banh
	# hong, nen cai duy nhat ho co de quyet la anh chup.
	anh = _doc_tep(tep)
	if not anh:
		frappe.throw(
			"Phải đính kèm ít nhất một ảnh làm căn cứ (ảnh khách phản ánh, hoặc ảnh "
			"bánh hỏng). Bấm nút thêm ảnh ở ô Bằng chứng rồi gửi lại."
		)

	ho_so = frappe.get_doc(
		{
			"doctype": DT,
			"hoa_don": si.name,
			"khach": si.customer,
			"so_tien": tien,
			"ly_do": ly_do,
			"dien_giai": (dien_giai or "").strip(),
			"trang_thai": "Cho chi",
			"ten_tk": (ten_tk or "").strip(),
			"so_tk": tk,
			"ngan_hang": (ngan_hang or "").strip() or None,
			"sdt": sdt(sdt_khach) or "",
			"nguoi_duyet": frappe.session.user,
			"cach_duyet": "Gui duyet tu man Chi tiet don",
			"noi_dung_ck": noi_dung_ck(si.name),
		}
	)
	ho_so.flags.ignore_permissions = True
	ho_so.insert(ignore_permissions=True)

	dinh = _dinh_kem(ho_so.name, anh)
	frappe.db.commit()

	da_gui, nguoi_nhan = _bao_ke_toan(ho_so, si)

	return {
		"ok": 1,
		"ho_so": ho_so.name,
		"so_tien": tien,
		"tong_don": flt(si.grand_total),
		"mot_phan": 1 if tien < flt(si.grand_total) - 0.5 else 0,
		"so_anh": dinh,
		"noi_dung_ck": ho_so.noi_dung_ck,
		"da_bao_ke_toan": da_gui,
		"nguoi_nhan": nguoi_nhan,
		"canh_bao_hddt": (si.get("custom_hddt_so") or "").strip(),
	}


@frappe.whitelist()
def xem_tien_du(si_name=None):
	"""Don nay dang du bao nhieu tien. Cho man hinh hoi TRUOC khi mo form.

	Tra ve du con so de man hinh giai thich cho sales hieu vi sao duoc hoac
	khong duoc, thay vi chi bao mot cau cut ngun.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	si = frappe.get_doc(SI, si_name)
	nhan = _tien_da_nhan(si)
	duoc, tran, nhac = tran_tien_du(nhan, flt(si.grand_total))
	cu = frappe.db.get_value(
		DT, {"hoa_don": si.name, "trang_thai": ["!=", "Da huy"]},
		["name", "trang_thai", "so_tien", "loai_hoan"], as_dict=True,
	)
	return {
		"duoc": 1 if duoc and not cu else 0,
		"tran": tran,
		"da_nhan": nhan,
		"tong_don": flt(si.grand_total),
		"ly_do": list(LY_DO_DU),
		"da_co": cu or None,
		"vi_sao": (
			("Đơn này đã có phiếu %s đang ở trạng thái \"%s\", xử lý xong phiếu đó rồi mới lập phiếu mới được."
			 % (cu["name"], cu["trang_thai"])) if cu else nhac
		),
		"canh_bao_hddt": (si.get("custom_hddt_so") or "").strip(),
	}


@frappe.whitelist()
def tao_tien_du(
	si_name=None,
	ly_do=None,
	dien_giai="",
	so_tien=0,
	ten_tk="",
	so_tk="",
	ngan_hang="",
	sdt_khach="",
	tep=None,
):
	"""Sales lap yeu cau CHUYEN LAI TIEN KHACH NOP THUA.

	Anh Viet 18/08/2026 chot: chi Dung duyet nhu hoan tien. Nen phieu nay di
	dung mot cua duyet voi phieu tra hang, cung vao mot danh sach cho chi,
	cung ra tien tu tai khoan MB cong ty, cung doi soat SePay.

	KHAC phieu tra hang o hai cho.

	Mot, TRAN. Tra hang thi toi da tra lai ca don. Tien du thi toi da chi
	bang dung phan khach chuyen VUOT tong don, tinh lai o may chu.

	Hai, ANH KHONG BAT BUOC. Voi tra hang thi anh chup la bang chung duy
	nhat ke toan co de quyet, vi ho ngoi xa quay khong nhin thay cai banh
	hong. Voi tien du thi bang chung nam ngay trong so sach: sao ke bao da
	nhan bao nhieu, hoa don ghi bao nhieu, phan chenh la con so may tu tinh
	ra chu khong ai khai. Bat anh o day la bat mot thu khong noi them dieu gi.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	si = frappe.get_doc(SI, si_name)
	_kiem_tra_duoc(si)

	ly_do = (ly_do or "").strip()
	if ly_do not in LY_DO_DU:
		frappe.throw("Phải chọn lý do. Chọn một trong: %s." % ", ".join(LY_DO_DU))
	if ly_do == "Khac" and not (dien_giai or "").strip():
		frappe.throw("Lý do \"Khác\" thì phải ghi rõ vì sao dư. Gõ vào ô Diễn giải giúp em.")

	# TRAN TINH LAI O MAY CHU (QT-19), khong tin con so man hinh gui len.
	nhan = _tien_da_nhan(si)
	duoc, tran, nhac = tran_tien_du(nhan, flt(si.grand_total))
	if not duoc:
		frappe.throw(nhac)
	tien = flt(so_tien) or tran
	if tien > tran + 0.5:
		frappe.throw(
			"Số tiền chuyển lại (%s đ) lớn hơn phần khách nộp dư (%s đ). Đơn này "
			"đã nhận %s đ, giá trị đơn %s đ. Sửa lại số tiền cho đúng phần dư, "
			"hoặc nếu khách trả hàng thì dùng nút Hoàn tiền."
			% (_tien_vn(tien), _tien_vn(tran), _tien_vn(nhan), _tien_vn(si.grand_total))
		)

	tk = re.sub(r"\s+", "", str(so_tk or ""))
	if not tk or not (ten_tk or "").strip() or not (ngan_hang or "").strip():
		frappe.throw(
			"Còn thiếu thông tin tài khoản nhận tiền. Điền đủ tên ngân hàng, số tài "
			"khoản và tên chủ tài khoản của khách rồi gửi lại."
		)

	ho_so = frappe.get_doc({
		"doctype": DT,
		"hoa_don": si.name,
		"khach": si.customer,
		"so_tien": tien,
		"loai_hoan": LOAI_TIEN_DU,
		"ly_do": "Khac",
		"dien_giai": ("[Tiền nộp thừa] %s. %s" % (ly_do, (dien_giai or "").strip())).strip(),
		"trang_thai": "Cho chi",
		"ten_tk": (ten_tk or "").strip(),
		"so_tk": tk,
		"ngan_hang": (ngan_hang or "").strip() or None,
		"sdt": sdt(sdt_khach) or "",
		"nguoi_duyet": frappe.session.user,
		"cach_duyet": "Gui duyet tu man Chi tiet don (tien nop thua)",
		"noi_dung_ck": noi_dung_ck(si.name),
	})
	ho_so.flags.ignore_permissions = True
	ho_so.insert(ignore_permissions=True)

	anh = _doc_tep(tep)
	dinh = _dinh_kem(ho_so.name, anh) if anh else 0
	frappe.db.commit()

	da_gui, nguoi_nhan = _bao_ke_toan(ho_so, si)
	return {
		"ok": 1,
		"ho_so": ho_so.name,
		"so_tien": tien,
		"tran": tran,
		"da_nhan": nhan,
		"tong_don": flt(si.grand_total),
		"so_anh": dinh,
		"noi_dung_ck": ho_so.noi_dung_ck,
		"da_bao_ke_toan": da_gui,
		"nguoi_nhan": nguoi_nhan,
	}


def _doc_tep(tep):
	"""Chuan hoa danh sach tep tu man gui len. Tra list rong neu khong co."""
	if not tep:
		return []
	if isinstance(tep, str):
		try:
			tep = json.loads(tep)
		except Exception:
			return []
	if isinstance(tep, dict):
		tep = [tep]
	ra = []
	for t in tep or []:
		if not isinstance(t, dict):
			continue
		if (t.get("noi_dung") or "").strip():
			ra.append({"ten": (t.get("ten") or "bang-chung.jpg").strip(), "noi_dung": t["noi_dung"]})
	return ra


def _dinh_kem(ma_ho_so, anh):
	"""Ghi anh bang chung vao ho so. Tra so tep dinh duoc.

	Loi mot tep khong duoc lam do ca yeu cau: ho so da lap roi, va Sales
	dinh bu duoc tep con thieu tren man danh sach.
	"""
	n = 0
	for a in anh:
		try:
			noi = a["noi_dung"]
			if "," in noi and noi[:5] in ("data:", "DATA:"):
				noi = noi.split(",", 1)[1]
			f = frappe.get_doc(
				{
					"doctype": "File",
					"file_name": a["ten"],
					"attached_to_doctype": DT,
					"attached_to_name": ma_ho_so,
					"content": noi,
					"decode": True,
					"is_private": 1,
				}
			)
			f.flags.ignore_permissions = True
			f.insert(ignore_permissions=True)
			n += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "hoan_tien: dinh kem bang chung loi")
	return n


VAI_KE_TOAN = ("Accounts Manager", "Accounts User")


def _bao_ke_toan(ho_so, si):
	"""Gui thu bao ke toan co yeu cau hoan tien moi. Tra (da_gui, danh_sach).

	Anh Viet chot 16/08/2026: gui cho MOI nguoi mang vai tro ke toan tren
	he, khong khai dia chi co dinh. Ai duoc them vai tro sau nay thi tu
	dong nhan, khong phai sua ma.

	Ham nay KHONG BAO GIO nem loi: ho so da lap xong roi, may chu thu hong
	thi ke toan van thay yeu cau tren man danh sach. Nem loi o day la lam
	hong mot viec da thanh cong.
	"""
	try:
		nguoi = set()
		for vai in VAI_KE_TOAN:
			for u in frappe.get_all("Has Role", filters={"role": vai}, fields=["parent"], limit_page_length=0):
				nguoi.add(u["parent"])
		mail = []
		for u in nguoi:
			d = frappe.db.get_value("User", u, ["email", "enabled"], as_dict=True)
			if d and cint(d.get("enabled")) and (d.get("email") or "").strip():
				mail.append(d["email"].strip())
		mail = sorted(set(mail))
		if not mail:
			frappe.log_error(
				"Khong tim thay nguoi dung nao mang vai tro ke toan, nen khong gui duoc "
				"thu bao ho so %s." % ho_so.name,
				"hoan_tien: khong co nguoi nhan",
			)
			return 0, []

		tien = "{:,.0f}".format(flt(ho_so.so_tien)).replace(",", ".")
		tong = "{:,.0f}".format(flt(si.grand_total)).replace(",", ".")
		phan = "toàn bộ đơn" if flt(ho_so.so_tien) >= flt(si.grand_total) - 0.5 else "một phần đơn"
		than = (
			"<p>Có một yêu cầu hoàn tiền mới chờ chi.</p>"
			"<table cellpadding='6' style='border-collapse:collapse'>"
			"<tr><td><b>Phiếu</b></td><td>%s</td></tr>"
			"<tr><td><b>Hoá đơn gốc</b></td><td>%s (tổng %s đ)</td></tr>"
			"<tr><td><b>Số tiền hoàn</b></td><td><b>%s đ</b> - %s</td></tr>"
			"<tr><td><b>Lý do</b></td><td>%s%s</td></tr>"
			"<tr><td><b>Người gửi</b></td><td>%s</td></tr>"
			"<tr><td><b>Tài khoản nhận</b></td><td>%s - %s - %s</td></tr>"
			"<tr><td><b>Nội dung chuyển khoản</b></td><td><b>%s</b></td></tr>"
			"</table>"
			"<p>Mở app, vào Bán hàng, Hoàn tiền / Trả hàng để xem ảnh khách gửi kèm "
			"và bấm Xuất thông tin chuyển khoản MB Biz.</p>"
			"<p style='color:#92400e'>Tiền chỉ được ghi sổ sau khi có Uỷ nhiệm chi tải "
			"từ e-banking đính kèm. Dòng sao kê SePay chỉ để biết tiền đã đi chưa.</p>"
		) % (
			ho_so.name,
			si.name,
			tong,
			tien,
			phan,
			frappe.utils.escape_html(ho_so.ly_do or ""),
			(": " + frappe.utils.escape_html(ho_so.dien_giai)) if ho_so.dien_giai else "",
			frappe.utils.escape_html(ho_so.nguoi_duyet or ""),
			frappe.utils.escape_html(ho_so.ten_tk or ""),
			frappe.utils.escape_html(ho_so.so_tk or ""),
			frappe.utils.escape_html(str(ho_so.ngan_hang or "")),
			frappe.utils.escape_html(ho_so.noi_dung_ck or ""),
		)
		frappe.sendmail(
			recipients=mail,
			subject="[Vagabond] Yêu cầu hoàn tiền %s - %s đ - đơn %s" % (ho_so.name, tien, si.name),
			message=than,
			reference_doctype=DT,
			reference_name=ho_so.name,
			now=False,
		)
		return 1, mail
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: gui thu bao ke toan loi")
		return 0, []


def _kiem_tra_duoc(si):
	"""Hoa don nay con tra duoc khong. Nem loi theo QT-24 neu khong."""
	if cint(si.docstatus) != 1:
		frappe.throw(
			"Hoá đơn %s chưa ghi sổ nên không dùng luồng hoàn tiền. Bill chưa ghi sổ "
			"thì sửa hoặc huỷ thẳng là được." % si.name
		)
	if cint(si.get("vgb_huy")):
		frappe.throw("Hoá đơn %s đã mang dấu huỷ nên không hoàn tiền được." % si.name)
	cu = frappe.db.get_value(SI, {"return_against": si.name, "docstatus": 1}, "name")
	if cu:
		frappe.throw(
			"Hoá đơn %s đã có phiếu trả hàng %s rồi. Mở phiếu đó ra xem, đừng lập "
			"thêm phiếu thứ hai." % (si.name, cu)
		)
	# Yeu cau dang cho ke toan xu thi khong cho gui yeu cau thu hai. Khong
	# co chot nay thi Sales bam hai lan la ke toan nhan hai thu giong nhau
	# va chuyen tien hai lan.
	ho = frappe.db.get_value(
		DT, {"hoa_don": si.name, "trang_thai": ["!=", "Da huy"]}, ["name", "trang_thai"], as_dict=True
	)
	if ho:
		frappe.throw(
			"Đơn %s đã có yêu cầu hoàn tiền %s đang ở trạng thái \"%s\". Mở màn Hoàn "
			"tiền / Trả hàng để xem, đừng gửi thêm yêu cầu thứ hai."
			% (si.name, ho["name"], ho["trang_thai"])
		)


def _kiem_huy_nhap_duoc(si):
	"""Don nhap nay co lap phieu huy va hoan tien duoc khong.

	Nguoc han `_kiem_tra_duoc`: o kia doi docstatus PHAI bang 1, o day doi
	PHAI bang 0. Hai cua khong dung chung duoc mot phep kiem.
	"""
	if cint(si.docstatus) != 0:
		frappe.throw(
			"Hoá đơn %s đã ghi sổ rồi nên không dùng cửa này. Đơn đã ghi sổ thì "
			"dùng nút Hoàn tiền hoặc Chuyển lại tiền dư, vì lúc đó doanh thu đã "
			"ghi nhận và phải khử bằng một tờ ngược chiều." % si.name
		)
	if cint(si.get("vgb_tam_tinh") or 0):
		frappe.throw(
			"Phiếu %s là phiếu tạm tính, tức phiếu giữ món chứ khách chưa trả "
			"tiền. Không có khoản nào để hoàn." % si.name
		)
	# Don nhap thi khong the co hoa don dien tu. Neu co that thi du lieu dang
	# o trang thai khong ai luong truoc duoc, dung cho may tu quyet.
	so_hddt = (si.get("custom_hddt_so") or "").strip()
	if so_hddt:
		frappe.throw(
			"Đơn %s còn ở dạng nháp mà đã mang số hoá đơn điện tử %s. Đây là "
			"trạng thái bất thường, máy không tự xử. Báo anh Việt trước khi làm "
			"gì tiếp." % (si.name, so_hddt)
		)
	ho = frappe.db.get_value(
		DT, {"hoa_don": si.name, "trang_thai": ["!=", "Da huy"]},
		["name", "trang_thai"], as_dict=True,
	)
	if ho:
		frappe.throw(
			"Đơn %s đã có phiếu hoàn tiền %s đang ở trạng thái \"%s\". Mở màn Hoàn "
			"tiền để xem, đừng gửi thêm phiếu thứ hai."
			% (si.name, ho["name"], ho["trang_thai"])
		)


@frappe.whitelist()
def xem_huy_nhap(si_name=None):
	"""Don nhap nay huy va hoan lai duoc bao nhieu. Man hinh hoi TRUOC khi mo form."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	si = frappe.get_doc(SI, si_name)
	nhan = _tien_da_nhan(si)
	duoc, tran, nhac = tran_huy_nhap(nhan, flt(si.grand_total))
	cu = frappe.db.get_value(
		DT, {"hoa_don": si.name, "trang_thai": ["!=", "Da huy"]},
		["name", "trang_thai", "so_tien", "loai_hoan"], as_dict=True,
	)
	da_huy = cint(si.get("vgb_huy") or 0)
	return {
		"duoc": 1 if duoc and not cu and cint(si.docstatus) == 0 else 0,
		"tran": tran,
		"da_nhan": nhan,
		"tong_don": flt(si.grand_total),
		"da_huy": da_huy,
		"ly_do": list(LY_DO_HUY),
		"da_co": cu or None,
		"vi_sao": (
			("Đơn này đã có phiếu %s đang ở trạng thái \"%s\", xử lý xong phiếu đó "
			 "rồi mới lập phiếu mới được." % (cu["name"], cu["trang_thai"])) if cu
			else ("Hoá đơn này đã ghi sổ rồi, dùng nút Hoàn tiền chứ không dùng cửa này."
			      if cint(si.docstatus) != 0 else nhac)
		),
	}


@frappe.whitelist()
def tao_huy_nhap(
	si_name=None,
	ly_do=None,
	dien_giai="",
	so_tien=0,
	ten_tk="",
	so_tk="",
	ngan_hang="",
	sdt_khach="",
	otp=None,
	tep=None,
):
	"""Huy mot don CHUA GHI SO va tra lai tien khach da chuyen.

	Anh Viet giao 21/08/2026.

	THU TU HAI BUOC KHONG DUOC DAO
	------------------------------
	Danh dau huy don TRUOC, lap phieu SAU.

	Lam nguoc lai ma buoc sau hong thi con lai mot don nhap chua danh dau,
	va chuoi cuoi ngay luc 23:00 se ghi so no roi phat hanh hoa don dien tu.
	Con lam dung thu tu ma buoc sau hong thi chi con mot don da huy khong co
	phieu hoan - kho chiu, nhung sua lai duoc bang cach bam lai, va khong to
	hoa don thue nao bi dinh vao.

	VE KE TOAN
	----------
	Tien khach chuyen vao khi chua giao hang va chua ghi so KHONG phai doanh
	thu. Do la tien khach ung truoc, minh giu ho va dang no khach dung bang
	so do. Huy don la tra lai khoan giu ho. Nen o day KHONG lap hoa don tra
	hang, khong khu doanh thu, khong dinh gi den hoa don dien tu - giong het
	luong Tien nop thua, chi khac ly do.

	OTP: dat co huy la thao tac da co san mot chot kiem soat la ma OTP quan
	ly. Cua moi nay dung lai dung chot do chu khong tu mo mot duong vong.
	"""
	from vagabond import chung_tu
	from vagabond.ban_hang import _ghi_vet, _kiem_quyen, _otp_kiem

	_kiem_quyen()
	si = frappe.get_doc(SI, si_name)
	_kiem_huy_nhap_duoc(si)

	ly_do = (ly_do or "").strip()
	if ly_do not in LY_DO_HUY:
		frappe.throw("Phải chọn lý do huỷ. Chọn một trong: %s." % ", ".join(LY_DO_HUY))
	if ly_do == "Khac" and not (dien_giai or "").strip():
		frappe.throw("Lý do \"Khác\" thì phải ghi rõ vì sao huỷ. Gõ vào ô Diễn giải giúp em.")

	# TRAN TINH LAI O MAY CHU (QT-19), khong tin con so man hinh gui len.
	nhan = _tien_da_nhan(si)
	duoc, tran, nhac = tran_huy_nhap(nhan, flt(si.grand_total))
	if not duoc:
		frappe.throw(nhac)
	tien = flt(so_tien) or tran
	if tien > tran + 0.5:
		frappe.throw(
			"Số tiền hoàn (%s đ) lớn hơn số máy thấy đã nhận cho đơn này (%s đ). "
			"Chỉ trả lại được đúng phần đã thật sự nhận."
			% (_tien_vn(tien), _tien_vn(tran))
		)

	tk = re.sub(r"\s+", "", str(so_tk or ""))
	if not tk or not (ten_tk or "").strip() or not (ngan_hang or "").strip():
		frappe.throw(
			"Còn thiếu thông tin tài khoản nhận tiền. Điền đủ tên ngân hàng, số tài "
			"khoản và tên chủ tài khoản của khách rồi gửi lại."
		)

	cach = _otp_kiem(otp, "huỷ đơn chưa ghi sổ và hoàn tiền")

	ghi = ("[Huỷ đơn chưa ghi sổ] %s. %s" % (ly_do, (dien_giai or "").strip())).strip()

	# BUOC MOT: danh dau huy. Lam truoc de chuoi ghi so cuoi ngay khong bao
	# gio cham toi don nay nua, ke ca khi buoc hai o duoi hong.
	if not cint(si.get("vgb_huy") or 0):
		_ghi_vet(
			si.name,
			"Huỷ đơn chưa ghi sổ và hoàn %s đ cho khách. Lý do: %s"
			% (_tien_vn(tien), ly_do),
			cach,
		)
		chung_tu.danh_dau_huy(si, ghi, ghi_vet=False)
		frappe.db.commit()

	# BUOC HAI: lap phieu gui ke toan.
	ho_so = frappe.get_doc({
		"doctype": DT,
		"hoa_don": si.name,
		"khach": si.customer,
		"so_tien": tien,
		"loai_hoan": LOAI_HUY_NHAP,
		"ly_do": "Khac",
		"dien_giai": ghi,
		"trang_thai": "Cho chi",
		"ten_tk": (ten_tk or "").strip(),
		"so_tk": tk,
		"ngan_hang": (ngan_hang or "").strip() or None,
		"sdt": sdt(sdt_khach) or "",
		"nguoi_duyet": frappe.session.user,
		"cach_duyet": "Gui duyet tu man Chi tiet don (huy don chua ghi so)",
		"noi_dung_ck": noi_dung_ck(si.name),
	})
	ho_so.flags.ignore_permissions = True
	ho_so.insert(ignore_permissions=True)

	anh = _doc_tep(tep)
	dinh = _dinh_kem(ho_so.name, anh) if anh else 0
	frappe.db.commit()

	da_gui, nguoi_nhan = _bao_ke_toan(ho_so, si)
	return {
		"ok": 1,
		"ho_so": ho_so.name,
		"so_tien": tien,
		"tran": tran,
		"da_nhan": nhan,
		"tong_don": flt(si.grand_total),
		"da_huy_don": 1,
		"so_anh": dinh,
		"noi_dung_ck": ho_so.noi_dung_ck,
		"da_bao_ke_toan": da_gui,
		"nguoi_nhan": nguoi_nhan,
	}


def _sinh_chung_tu(ho_so):
	"""Nhip 2: TIEN DA RA THAT roi thi moi sinh chung tu.

	Chay tu duong doi soat SePay, khong ai goi tay. Sinh theo dung thu tu:
	  1. Hoa don tra hang  - khu doanh thu dung bang so tien da hoan
	  2. But diem hai chieu - thu hoi diem tang, tra lai diem khach da tieu
	  3. Phieu chuyen kho sang Kho Hang Huy, de NHAP - chi khi hoan TOAN BO
	  4. Phieu chi, de NHAP - ke toan dinh UNC roi moi ghi so

	Vi sao hoan MOT PHAN thi khong lap phieu kho: hoan mot phan nghia la
	khach giu lai banh va duoc bu mot phan tien. Khong co cai banh nao di
	ve kho ca. Lap phieu kho luc do la khai mot duong hang khong ton tai.

	Vi sao phieu chi van de NHAP du tien da di roi: chi Dung chot 16/08 -
	dong sao ke SePay KHONG phai giay bao No hop le, ho so lam viec voi Cuc
	Thue bat buoc co tep Uy nhiem chi tai tu e-banking. Nen may dien san moi
	o, con nut ghi so van nam trong tay ke toan sau khi dinh kem UNC.

	Ham nay chay mot lan cho moi ho so. Da co hoa don tra thi thoat ngay.
	"""
	if ho_so.get("hoa_don_tra"):
		return {"bo_qua": 1, "vi_sao": "Hồ sơ này đã sinh chứng từ rồi."}
	loai = (ho_so.get("loai_hoan") or "").strip()

	# HUỶ ĐƠN PANCAKE: không có hoá đơn nào để mở, nên nhánh này phải đứng
	# TRƯỚC dòng đọc Sales Invoice bên dưới, nếu không là nổ ngay tại đó.
	#
	# Cả cụm sinh ở đây chứ không sinh lúc Sales bấm gửi. Lý do đầy đủ nằm ở
	# đầu `_lap_cap_phieu_huy_don`.
	if loai == LOAI_HUY_PANCAKE:
		if ho_so.get("phieu_chi"):
			return {"bo_qua": 1, "vi_sao": "Hồ sơ này đã sinh chứng từ rồi."}
		thu, chi = _lap_cap_phieu_huy_don(ho_so)
		ho_so.phieu_chi = chi.name if chi else None
		if thu and ho_so.meta.has_field("phieu_thu"):
			ho_so.phieu_thu = thu.name
		ho_so.flags.ignore_permissions = True
		ho_so.save(ignore_permissions=True)
		return {
			"bo_qua": 0, "hoa_don_tra": "", "phieu_kho": "",
			"phieu_chi": ho_so.phieu_chi, "phieu_thu": thu.name if thu else "",
			"toan_bo": 0, "loai": loai,
		}

	si = frappe.get_doc(SI, ho_so.hoa_don)

	# HAI LOAI PHIEU KHONG DUNG TOI DOANH THU di chung mot duong: chi mot
	# phieu chi, khong hoa don tra hang, khong thu hoi diem, khong phieu kho.
	#
	# TIEN NOP THUA: khach nhan du hang, gia dung, doanh thu dung. Khoan du
	# la tien minh giu ho khach. Khu doanh thu de tra mot khoan nop thua la
	# ghi sai ban chat, va lam so lech voi to hoa don dien tu dang DUNG.
	#
	# HUY DON CHUA GHI SO: don chua bao gio duoc ghi nhan doanh thu, khong co
	# gi de khu. Tien khach chuyen vao khi chua giao hang la tien ung truoc,
	# minh giu ho. Lap hoa don tra hang o day la khu mot khoan doanh thu chua
	# ton tai, va de lam duoc dieu do thi truoc het phai ghi so mot to hoa
	# don khong co that.
	#
	# Nhanh nay dat TRUOC phep tim Kho Hang Huy la co y: hai loai phieu nay
	# khong dung den kho, nen mot cai kho chua dung xong khong duoc phep chan
	# duong tra tien cho khach.
	if loai in (LOAI_TIEN_DU, LOAI_HUY_NHAP):
		pe = _lap_phieu_chi_du(si, ho_so)
		ho_so.phieu_chi = pe.name if pe else None
		ho_so.dien_giai = (
			(ho_so.dien_giai or "").strip()
			+ ("\n" if ho_so.dien_giai else "")
			+ (
				("Trả lại tiền khách nộp thừa. KHÔNG lập hoá đơn trả hàng, doanh thu "
				 "của đơn giữ nguyên %s đ và hoá đơn điện tử không phải điều chỉnh."
				 % _tien_vn(si.grand_total))
				if loai == LOAI_TIEN_DU
				else
				("Trả lại tiền của đơn đã huỷ khi còn ở dạng nháp. Đơn chưa từng "
				 "được ghi sổ nên KHÔNG có doanh thu để khử, KHÔNG lập hoá đơn trả "
				 "hàng và KHÔNG có hoá đơn điện tử nào phải xử lý.")
			)
		).strip()
		ho_so.flags.ignore_permissions = True
		ho_so.save(ignore_permissions=True)
		return {
			"bo_qua": 0, "hoa_don_tra": "", "phieu_kho": "",
			"phieu_chi": ho_so.phieu_chi, "toan_bo": 0, "loai": loai,
		}

	kho = kho_huy(si.company)
	if not kho:
		frappe.log_error("Chua dung duoc Kho Hang Huy", "hoan_tien: sinh chung tu loi")
		return {"bo_qua": 1, "vi_sao": "Chưa dựng được Kho Hàng Hủy."}

	tien = flt(ho_so.so_tien)
	toan_bo = tien >= flt(si.grand_total) - 0.5

	tra = _lap_hoa_don_tra(si, kho, ho_so.ly_do, ho_so.name, tien)
	ho_so.hoa_don_tra = tra.name

	_thu_hoi_diem(si, tra.name, ho_so.ly_do)

	phieu_kho = ""
	if toan_bo:
		phieu_kho = _chuyen_kho_huy(si, tra, kho, ho_so.ly_do)
	else:
		ho_so.dien_giai = (
			(ho_so.dien_giai or "").strip()
			+ ("\n" if ho_so.dien_giai else "")
			+ "Hoàn một phần nên khách giữ lại hàng, không lập phiếu chuyển Kho Hàng Hủy."
		).strip()

	pe = _lap_phieu_chi(si, tra, ho_so)
	ho_so.phieu_chi = pe.name if pe else None
	ho_so.flags.ignore_permissions = True
	ho_so.save(ignore_permissions=True)
	return {
		"bo_qua": 0,
		"hoa_don_tra": tra.name,
		"phieu_kho": phieu_kho,
		"phieu_chi": ho_so.phieu_chi,
		"toan_bo": 1 if toan_bo else 0,
	}


def _lap_hoa_don_tra(si, kho, ly_do, ma_ho_so, so_tien=0):
	"""Hoa don tra hang, hang ve KHO HANG HUY chu khong ve kho ban.

	Hoan MOT PHAN (anh Viet mo muc 50% ngay 16/08/2026)
	---------------------------------------------------
	Hoan mot phan thi khach GIU LAI banh, chi duoc bu mot phan tien. Nen to
	tra hang phai mang dung so tien hoan chu khong phai ca don.

	Cach lam: ha don gia tung dong theo dung ty le, GIU NGUYEN so luong.
	Co y KHONG dung o chiet khau tong, vi dung chiet khau thi to nay dinh
	dung cai loi em vua tim ra sang nay - duong xuat hoa don dien tu doc
	so tien TRUOC chiet khau, va da lam 213 to xuat cao hon so thuc thu.
	Ha don gia thi moi duong doc ra deu ra cung mot con so.
	"""
	from erpnext.accounts.doctype.sales_invoice.sales_invoice import make_sales_return

	tra = make_sales_return(si.name)
	tong = flt(si.grand_total)
	tien = flt(so_tien) or tong
	ty_le = (tien / tong) if tong > 0 else 1.0
	if ty_le < 0.9999:
		for d in tra.items:
			d.rate = flt(d.rate) * ty_le
			d.price_list_rate = flt(d.get("price_list_rate")) * ty_le
			d.discount_amount = 0
			d.discount_percentage = 0
	# update_stock = 0, GIONG HET moi hoa don khac cua he.
	#
	# Ban dau em dat 1 de hang tu chay thang vao kho huy. Chay thu that
	# ngay 16/08/2026 thi ERPNext tu choi:
	#
	#     'Cap nhat kho' khong the chon vi MH khong duoc giao qua HDB-...
	#
	# Doc lai moi hieu: CA HE nay chay update_stock = 0 co chu y - ghi chu
	# dau ban_hang.py noi ro "GIAI DOAN 1 KHONG cap nhat kho, chi ghi doanh
	# thu", kho do kiem banh lo rieng. Ban ra khong tru kho, nen tra ve ma
	# cong kho la CONG KHONG cua ai ca: ton kho phinh len bang so hang von
	# chua bao gio bi tru.
	#
	# Nen to tra hang theo dung nep cua he, con duong hang di vao kho huy
	# tach ra thanh mot phieu chuyen kho rieng - xem _chuyen_kho_huy.
	tra.update_stock = 0
	tra.set_posting_time = 1
	tra.posting_date = nowdate()
	for d in tra.items:
		# Van ghi kho huy len tung dong de doc to nay la biet hang di dau,
		# du dong nay khong sinh but kho nao.
		d.warehouse = kho
		d.target_warehouse = None
	# CHEP LAI CAC TRUONG TU THEM CUA HE.
	#
	# make_sales_return chi chep nhung truong ERPNext biet; cac truong do
	# minh tu them thi no khong biet, nen to tra hang ra doi TRONG khong.
	# Va hook kiem_truoc_khi_luu chan ngay: "Hoa don chua chon nguon don".
	# Bat duoc khi chay thu that 16/08/2026.
	#
	# Chep chu khong dat mac dinh: to tra hang phai doi soat ve dung cai san
	# va dung cai quay ma don goc da ban, khong thi cuoi thang so lieu tra
	# hang khong khop voi so lieu ban ra o bat ky kenh nao.
	for o in (
		"custom_nguon", "vgb_pt_thanh_toan", "vgb_quay", "vgb_khach_no",
		"vgb_so_ban", "vgb_xhd_ten", "vgb_ma_tham_chieu",
	):
		try:
			if si.get(o) is not None and tra.meta.has_field(o):
				tra.set(o, si.get(o))
		except Exception:
			pass
	tra.remarks = ("Trả hàng %s. Lý do: %s. Hồ sơ %s." % (si.name, ly_do, ma_ho_so))[:500]
	tra.flags.ignore_permissions = True
	# Nhip dong bo Pancake khoa mot ma don cho mot hoa don; to tra hang mang
	# cung ma se dinh chot do, nen bo ma di. To tra hang khong phai mot don
	# ban moi.
	tra.custom_pancake_id = None
	tra.insert(ignore_permissions=True)
	tra.submit()
	return tra


def _chuyen_kho_huy(si, tra, kho, ly_do):
	"""Phieu chuyen hang tu kho ban sang Kho Hang Huy. De o trang thai NHAP.

	Vi sao la mot phieu rieng chu khong nam trong hoa don tra
	---------------------------------------------------------
	He nay ban ra KHONG tru kho (update_stock = 0, xem ghi chu dau
	ban_hang.py). Nen neu to tra hang lai cong kho thi ton kho phinh len
	bang so hang von chua bao gio bi tru. Hang van dang nam o kho ban tren
	so sach, va viec dung la CHUYEN no sang kho huy - khong de ra so luong
	moi.

	Vi sao de NHAP: anh Viet viet "cho kiem ke tieu huy". Luc lap phieu thi
	banh con nam tren quay, chua ai dem va chua ai do bo. Kho bam ghi so khi
	that su nhan hang.

	Bo qua mat hang khong theo doi ton kho (ve workshop, phi giao...): ep
	chuyen kho nhung thu do la nem loi vo ich giua mot luong dang chay.
	"""
	try:
		dong = []
		for d in tra.items:
			ma = (d.get("item_code") or "").strip()
			if not ma:
				continue
			if not cint(frappe.db.get_value("Item", ma, "is_stock_item")):
				continue
			nguon = _kho_nguon(si, ma)
			if not nguon or nguon == kho:
				continue
			dong.append(
				{
					"item_code": ma,
					"qty": abs(flt(d.get("qty"))),
					"s_warehouse": nguon,
					"t_warehouse": kho,
				}
			)
		if not dong:
			return ""
		pk = frappe.new_doc("Stock Entry")
		pk.stock_entry_type = "Material Transfer"
		pk.company = si.company
		pk.set_posting_time = 1
		pk.posting_date = nowdate()
		pk.remarks = "Hàng khách trả từ %s (%s), chuyển sang %s chờ kiểm kê tiêu huỷ." % (
			si.name, ly_do, kho,
		)
		for r in dong:
			pk.append("items", r)
		pk.flags.ignore_permissions = True
		pk.insert(ignore_permissions=True)
		return pk.name
	except Exception:
		# Hoa don tra da ghi so roi. Phieu kho hong thi kho lap tay duoc,
		# KHONG duoc nem loi lam hong ca luong hoan tien.
		frappe.log_error(frappe.get_traceback(), "hoan_tien: lap phieu chuyen kho huy loi")
		return ""


def _kho_nguon(si, ma_hang):
	"""Kho hang da nam truoc khi tra. Uu tien kho ghi tren chinh dong ban."""
	for d in si.get("items") or []:
		if (d.get("item_code") or "") == ma_hang and (d.get("warehouse") or ""):
			return d.get("warehouse")
	# Khong co thi lay kho dang con ton nhieu nhat cua mat hang do.
	r = frappe.db.sql(
		"""select warehouse from `tabBin` where item_code = %s and actual_qty > 0
		order by actual_qty desc limit 1""",
		(ma_hang,),
	)
	return r[0][0] if r else ""


def _thu_hoi_diem(si, ma_tra, ly_do):
	"""Rut ve diem quan da tang, va tra lai diem khach da tieu.

	Hai viec nguoc chieu nhau nen phai la hai buoc:
	  - diem quan TANG cho don do  -> rut ve (but am)
	  - diem khach da TIEU tren don -> tra lai (but duong)

	Bat loi rieng tung buoc: thu hoi diem hong khong duoc lam hong ca luong
	tra hang, vi luc do hoa don tra da ghi so roi.
	"""
	from vagabond import diem_otp
	from vagabond.khach_hang import SO_DIEM, _ghi_so_diem, _khach_that

	try:
		kh = _khach_that(si)
		if kh:
			da = frappe.db.sql(
				"select sum(diem) from `tab%s` where hoa_don = %%s and loai = %%s" % SO_DIEM,
				(si.name, "Tich tu hoa don"),
			)
			diem = flt((da or [[0]])[0][0])
			if diem > 0 and not frappe.db.exists(
				SO_DIEM, {"hoa_don": si.name, "loai": "Hoan lai khi huy hoa don"}
			):
				_ghi_so_diem(
					kh, -diem, "Hoan lai khi huy hoa don", si.name,
					"Khách trả hàng (%s), thu hồi điểm đã tích. Phiếu %s." % (ly_do, ma_tra),
				)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: thu hoi diem tich loi")

	try:
		diem_otp.hoan_diem_don(si.name, "Khách trả hàng (%s), trả lại điểm đã dùng" % ly_do)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: tra lai diem da dung loi")


def _lap_cap_phieu_huy_don(ho_so):
	"""HAI phiếu tiền cho một hồ sơ hoàn của đơn Pancake đã huỷ. Để NHÁP.

	VÌ SAO SINH Ở ĐÂY CHỨ KHÔNG SINH LÚC SALES BẤM GỬI
	---------------------------------------------------
	Trước 23/08/2026 hai phiếu này sinh ngay trong yêu cầu của Sales, ở
	`don_huy.tao_hoan`. Kết quả: luồng chưa từng chạy được một lần nào.
	Ngày 23/08 chị Loan Anh bấm Gửi kế toán duyệt và nhận:

	    Người dùng ntla.3008@gmail.com không có quyền truy cập doctype qua
	    quyền vai trò cho tài liệu Phiếu thu/chi

	Sales không có quyền trên Payment Entry, và ĐÚNG là không nên có. Cấp
	quyền kế toán cho Sales để chữa một màn là mở một cánh cửa rộng hơn
	nhiều so với chỗ đang vướng.

	`ignore_permissions` trên từng tài liệu KHÔNG cứu được. Đọc thẳng mã
	nguồn Frappe version-16, `frappe/__init__.py`:

	    def has_permission(doctype=None, ptype="read", doc=None, ...):
	        out = frappe.permissions.has_permission(doctype, ptype, doc=doc, ...)

	Hàm này không hề nhìn `frappe.flags.ignore_permissions`, cũng không nhìn
	cờ trên tài liệu. Cờ đó chỉ chặn được `doc.check_permission()` bên trong
	`Document.insert()`; mọi lời gọi `frappe.has_permission(...)` trần nằm
	rải trong ERPNext và trong tầng workflow thì nó không với tới.

	Nên anh Việt chốt 23/08/2026: Sales chỉ lập hồ sơ, hai phiếu sinh muộn
	hơn một nhịp, tại bước đối soát, dưới tay người vốn có quyền. Ý ban đầu
	của chị Dung giữ nguyên: hai phiếu vẫn ở dạng NHÁP, kế toán vẫn đính
	giấy báo Có và uỷ nhiệm chi rồi mới ghi sổ.

	Và đây cũng đúng nếp của chính luồng hoàn tiền chính, vốn sinh phiếu chi
	tại bước đối soát chứ không sinh sẵn từ lúc Sales gửi.

	HAI CHÂN, KHÔNG PHẢI MỘT
	-------------------------
	Chị Dung chốt 21/08/2026 điều 2. Chân thu ghi nhận khoản khách đã chuyển
	vào lúc đặt đơn; chân chi trả lại. Chỉ lập phiếu chi thì TK 131 của mã
	"Khách lẻ Online" dư Nợ, trông như khách còn nợ đúng bằng số vừa trả.

	Trả về (thu, chi). Cái nào không lập được thì trả None chỗ đó và ghi
	nhật ký - KHÔNG ném lỗi làm hỏng cả bước đối soát, vì lúc này tiền đã ra
	khỏi tài khoản thật rồi, dấu đối soát phải giữ được.
	"""
	from vagabond.chung_tu_tien import dat_dien_giai

	cong_ty = _cong_ty()
	tk = tk_chi(cong_ty)
	if not tk:
		frappe.log_error("Chua khai tai khoan ngan hang cong ty",
			"hoan_tien: khong lap duoc cap phieu huy don")
		return None, None
	tk_ke_toan = frappe.db.get_value("Bank Account", tk, "account")
	if not tk_ke_toan:
		return None, None

	ma_don = str(ho_so.get("ma_don_pancake") or "").strip()
	# Số khách đã chuyển vào nằm ở bảng đệm đơn huỷ. Không có thì lấy đúng
	# số đang hoàn, để chân thu và chân chi ít nhất vẫn cân nhau.
	da_nhan = flt(frappe.db.get_value("Vagabond Don Huy", {"ma_don": ma_don}, "da_nhan")) if ma_don else 0.0
	if da_nhan <= 0:
		da_nhan = flt(ho_so.so_tien)
	noi_dung = str(ho_so.get("noi_dung_ck") or "").strip()

	def _mot(loai, so_tien, dien_giai, tham_chieu):
		try:
			pe = frappe.new_doc(PE)
			pe.payment_type = loai
			pe.party_type = "Customer"
			pe.party = ho_so.khach
			pe.company = cong_ty
			pe.posting_date = nowdate()
			if loai == "Receive":
				pe.paid_to = tk_ke_toan
			else:
				pe.paid_from = tk_ke_toan
			pe.paid_amount = flt(so_tien)
			pe.received_amount = flt(so_tien)
			pe.reference_no = tham_chieu
			pe.reference_date = nowdate()
			pe.vgb_hoan_tien = ho_so.name
			dat_dien_giai(pe, dien_giai)
			pe.flags.ignore_permissions = True
			pe.insert(ignore_permissions=True)
			return pe
		except Exception:
			frappe.log_error(frappe.get_traceback(),
				"hoan_tien: lap phieu %s cho huy don loi" % loai)
			return None

	mo_ta = "đơn Pancake %s đã huỷ" % (ma_don or ho_so.name)
	thu = _mot("Receive", da_nhan,
		"Khách chuyển trước cho %s. Đơn đã huỷ, chưa từng ghi doanh thu nên khoản "
		"này là tiền công ty giữ hộ, KHÔNG phải doanh thu. Chứng từ gốc: giấy báo "
		"Có tải từ e-banking." % mo_ta,
		(ho_so.get("ma_gd") or "").strip() or noi_dung)
	chi = _mot("Pay", flt(ho_so.so_tien),
		"Trả lại tiền khách đã chuyển cho %s theo hồ sơ %s. Đơn huỷ trước khi về hệ "
		"nên KHÔNG có hoá đơn, KHÔNG có hoá đơn trả hàng, KHÔNG có hoá đơn điện tử. "
		"Nội dung chuyển khoản: %s. Chứng từ gốc: uỷ nhiệm chi tải từ e-banking."
		% (mo_ta, ho_so.name, noi_dung),
		noi_dung)
	if chi:
		_chep_bang_chung_sang_phieu(ho_so.name, chi.name)
	return thu, chi


def _chep_bang_chung_sang_phieu(ten_ho_so, ten_pe):
	"""Chép ảnh bằng chứng của hồ sơ sang phiếu chi, để chế độ riêng tư.

	Sales đính ảnh khung chat vào hồ sơ lúc lập. Kế toán thì làm việc trên
	chứng từ bên ERPNext, nên chép một bản sang đó để mở phiếu ra là thấy
	ngay căn cứ, không phải lần ngược sang màn khác.

	Là bản NHÂN ĐÔI chứ không phải chuyển chỗ: một tệp trong Frappe chỉ đính
	vào đúng một chứng từ, mà hồ sơ vẫn phải giữ ảnh cho Sales xem.

	Không ném lỗi: lúc gọi hàm này thì tiền đã ra khỏi tài khoản thật rồi,
	một cái ảnh không chép được không đáng làm hỏng bước đối soát.
	"""
	try:
		ds = frappe.get_all(
			"File",
			filters={"attached_to_doctype": DT, "attached_to_name": ten_ho_so},
			fields=["name", "file_name", "file_url"],
			limit_page_length=0,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: doc bang chung cua ho so")
		return
	for f in ds:
		try:
			ban = frappe.get_doc({
				"doctype": "File",
				"file_name": f.get("file_name"),
				"file_url": f.get("file_url"),
				"is_private": 1,
				"attached_to_doctype": PE,
				"attached_to_name": ten_pe,
			})
			ban.flags.ignore_permissions = True
			ban.insert(ignore_permissions=True, ignore_if_duplicate=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "hoan_tien: chep bang chung sang phieu chi")


def _lap_phieu_chi_du(si, ho_so):
	"""Phieu chi cho hai loai KHONG dung toi doanh thu, de o trang thai NHAP.

	Dung chung cho phieu Tien nop thua va phieu Huy don chua ghi so. Ca hai
	deu tra lai mot khoan tien minh dang giu ho khach, khac nhau o ly do chu
	khong khac o but toan.

	Khac phieu chi cua luong tra hang o mot diem cot loi: KHONG tro vao mot
	hoa don nao ca. Khoan nay khong gan voi doanh thu cua to hoa don, no la
	tien minh giu ho khach.

	Sau khi ke toan ghi nhan phieu thu du so tien khach da chuyen, ba con so
	tu can: thu 1.100.000, hoa don 915.000, chi 185.000, con no bang 0. Nen
	ham nay khong dung toi doanh thu va khong dung toi to hoa don dien tu.

	De NHAP giong het luong tra hang: chi Dung chot 16/08 rang dong sao ke
	SePay khong phai giay bao No hop le, phai dinh kem uy nhiem chi roi ke
	toan moi bam ghi so.
	"""
	try:
		tk = tk_chi(si.company)
		if not tk:
			frappe.log_error(
				"Chua khai tai khoan ngan hang cong ty", "hoan_tien: khong lap duoc phieu chi du"
			)
			return None
		tk_ke_toan = frappe.db.get_value("Bank Account", tk, "account")
		if not tk_ke_toan:
			return None
		pe = frappe.new_doc(PE)
		pe.payment_type = "Pay"
		pe.party_type = "Customer"
		pe.party = si.customer
		pe.company = si.company
		pe.posting_date = nowdate()
		pe.paid_from = tk_ke_toan
		pe.paid_amount = flt(ho_so.so_tien)
		pe.received_amount = flt(ho_so.so_tien)
		pe.reference_no = ho_so.noi_dung_ck or noi_dung_ck(si.name)
		pe.reference_date = nowdate()
		pe.vgb_hoan_tien = ho_so.name
		from vagabond.chung_tu_tien import dat_dien_giai

		if (ho_so.get("loai_hoan") or "") == LOAI_HUY_NHAP:
			dat_dien_giai(pe, (
				"Trả lại tiền của đơn %s theo phiếu %s. Đơn đã huỷ khi còn ở dạng "
				"nháp, chưa từng ghi sổ nên KHÔNG có doanh thu, KHÔNG có hoá đơn "
				"trả hàng và KHÔNG có hoá đơn điện tử. Khoản này là tiền khách "
				"chuyển trước, công ty giữ hộ và nay trả lại. Nội dung chuyển "
				"khoản: %s" % (si.name, ho_so.name, ho_so.noi_dung_ck)
			))
		else:
			dat_dien_giai(pe, (
				"Trả lại tiền khách nộp thừa cho đơn %s theo phiếu %s. Khách đã chuyển "
				"dư so với giá trị đơn; doanh thu của đơn giữ nguyên, KHÔNG lập hoá đơn "
				"trả hàng và KHÔNG điều chỉnh hoá đơn điện tử. Nội dung chuyển khoản: %s"
				% (si.name, ho_so.name, ho_so.noi_dung_ck)
			))
		pe.flags.ignore_permissions = True
		pe.insert(ignore_permissions=True)
		return pe
	except Exception:
		# Khong duoc nem loi lam hong ca luong: ke toan lap tay duoc.
		frappe.log_error(frappe.get_traceback(), "hoan_tien: lap phieu chi tien du loi")
		return None


def _lap_phieu_chi(si, tra, ho_so):
	"""Phieu chi hoan tien, de o trang thai NHAP.

	Co y de nhap: luc nay tien chua that su chuyen di. May ghi so ho la so
	sach noi da tra tien trong khi tien con nam trong tai khoan.
	"""
	try:
		tk = tk_chi(si.company)
		if not tk:
			frappe.log_error("Chua khai tai khoan ngan hang cong ty", "hoan_tien: khong lap duoc phieu chi")
			return None
		tk_ke_toan = frappe.db.get_value("Bank Account", tk, "account")
		if not tk_ke_toan:
			return None
		# DUNG get_payment_entry CUA ERPNEXT chu khong tu dung tay.
		#
		# Ban dau em tu dung: dat total_amount, outstanding_amount va
		# allocated_amount deu bang so DUONG. Chay thu that 16/08/2026 thi
		# ERPNext tu choi:
		#
		#     Dong #1: So tien phan bo khong duoc lon hon so du no.
		#
		# Ly do: to TRA HANG mang grand_total AM (-60.000), nen so du no cua
		# no cung am. Doi chieu mot so duong voi mot so am thi con so nao
		# cung "lon hon". Dau cua tung o tren Payment Entry co luat rieng
		# cho hoa don tra hang, va do la luat cua ERPNext chu khong phai cua
		# minh - nen giao lai cho no dung.
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		pe = get_payment_entry(SI, tra.name)
		tien = abs(flt(pe.paid_amount)) or abs(flt(tra.grand_total))
		pe.payment_type = "Pay"
		pe.posting_date = nowdate()
		pe.paid_from = tk_ke_toan
		pe.reference_no = ho_so.noi_dung_ck or noi_dung_ck(tra.name)
		pe.reference_date = nowdate()
		pe.vgb_hoan_tien = ho_so.name
		from vagabond.chung_tu_tien import dat_dien_giai

		dat_dien_giai(pe, "Hoàn tiền khách theo phiếu %s cho hoá đơn trả hàng %s. "
			"Nội dung chuyển khoản: %s" % (ho_so.name, tra.name, ho_so.noi_dung_ck))
		pe.flags.ignore_permissions = True
		pe.insert(ignore_permissions=True)
		return pe
	except Exception:
		# Hoa don tra da ghi so roi; phieu chi hong thi ke toan lap tay
		# duoc. KHONG duoc nem loi lam hong ca luong.
		frappe.log_error(frappe.get_traceback(), "hoan_tien: lap phieu chi loi")
		return None


# ------------------------------------------------------- chan ghi so phieu chi


def chan_thieu_uy_nhiem_chi(doc, method=None):
	"""Hook before_submit cua Payment Entry.

	Phieu chi sinh tu luong hoan tien ma chua dinh kem uy nhiem chi thi
	khong ghi so duoc. Chan o BACKEND chu khong chi nhac tren man: nhac
	tren man thi bo qua duoc, ma day la chung tu goc de giai trinh.
	"""
	try:
		if not doc.get("vgb_hoan_tien"):
			return
		n = frappe.db.count(
			"File", {"attached_to_doctype": PE, "attached_to_name": doc.name}
		)
		if n:
			return
		from vagabond.chung_tu_tien import ten_chung_tu

		ten = ten_chung_tu(doc.get("payment_type"), doc.get("paid_from"))
		frappe.throw(
			"%s %s là chứng từ hoàn tiền cho khách nên bắt buộc phải có Uỷ nhiệm chi "
			"đính kèm mới ghi sổ được. Tải UNC từ e-banking về, bấm nút kẹp giấy ở góc "
			"phải để đính kèm, rồi ghi sổ lại." % (ten, doc.name)
		)
	except frappe.ValidationError:
		raise
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: kiem uy nhiem chi loi")


def khi_ghi_so_phieu_chi(doc, method=None):
	"""Hook on_submit cua Payment Entry: danh dau ho so da chi."""
	try:
		if not doc.get("vgb_hoan_tien"):
			return
		frappe.db.set_value(DT, doc.vgb_hoan_tien, "trang_thai", "Da chi")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: danh dau da chi loi")


# ------------------------------------------------------------ doi soat SePay


def _gd_da_chiem(tru_ho_so=None):
	"""Cac ma giao dich ngan hang DA duoc mot phieu hoan tien khac chiem.

	Vi sao phai co: mot dong tien ra tren sao ke la MOT lan tien roi khoi
	tai khoan. Cho hai phieu cung tro vao no la khai hai lan chi cho mot lan
	chuyen, va vi moi phieu khop xong deu sinh mot phieu chi rieng nen so
	se phinh len dung bang so tien khong he ra khoi ngan hang.

	Duong nay khong phai gia thuyet. Vong quet trong doi_soat() lap NGOAI la
	ho so, TRONG la giao dich, va khong giu dau vet giao dich nao da dung.
	Hai phieu hoan cua CUNG mot hoa don goc, cung so tien - chuyen rat hay
	gap khi khach doi banh hai lan tren mot don - se cung bam vao dong tien
	ra dau tien tim thay.

	Cho phep mot phieu giu lai chinh giao dich cua no (tham so tru_ho_so),
	de ke toan bam lai nut Doi soat cho phieu dang vuong loi_sinh_ct thi
	khong bi chinh minh chan.

	Phieu DA HUY thi nha giao dich ra, vi tien do hoac chua ra, hoac da duoc
	thu lai bang mot phieu khac.
	"""
	loc = {"trang_thai": ["!=", "Da huy"], "ma_gd": ["!=", ""]}
	if tru_ho_so:
		loc["name"] = ["!=", tru_ho_so]
	ra = {}
	for r in frappe.get_all(DT, filters=loc, fields=["name", "ma_gd"], limit_page_length=0):
		ma = (r.get("ma_gd") or "").strip()
		if ma:
			ra.setdefault(ma, r["name"])
	return ra


@frappe.whitelist()
def doi_soat(ho_so=None, so_ngay=30):
	"""Tim giao dich CHI tren sao ke ngan hang khop voi phieu hoan tien.

	SePay day sao ke vao `Bank Transaction` cua ERPNext, va cot `withdrawal`
	la tien RA. Duong ong nay da co san tu truoc, o day chi them mach buoc
	giao dich vao dung mot phieu.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	# Phieu da huy hoac bi tu choi KHONG duoc tu khop.
	#
	# Duong SePay goi thang (sepay_tien_ra) da loai "Da huy" tu 16/08, nhung
	# duong chay theo gio o day thi khong - nen mot phieu ke toan vua tu
	# choi ma ngan hang tinh co co dong tien ra trung so tien la may van
	# danh dau da doi soat va SINH LUON phieu chi. Hai duong phai giong
	# nhau, neu khong thi cai chat hon chi la trang tri.
	loc = {"da_doi_soat": 0, "trang_thai": ["!=", "Da huy"]}
	if ho_so:
		loc = {"name": ho_so, "trang_thai": ["!=", "Da huy"]}
	ds = frappe.get_all(
		DT,
		filters=loc,
		fields=["name", "hoa_don", "hoa_don_tra", "so_tien", "trang_thai",
			"loai_hoan", "noi_dung_ck"],
		limit_page_length=0,
	)
	# Do theo MA HOA DON GOC chu khong theo ma to tra hang.
	#
	# Doi tu 16/08/2026: truoc day noi dung chuyen khoan mang ma to tra hang,
	# nen phieu phai co to tra hang truoc thi moi doi soat duoc. Nay nguoc
	# lai - to tra hang chi sinh SAU khi tien ra - nen moc de do phai la thu
	# ton tai ngay tu luc Sales gui yeu cau, tuc ma hoa don goc.
	# Giữ lại hồ sơ nào DÒ ĐƯỢC, chứ không riêng hồ sơ có hoá đơn.
	#
	# Anh Việt chốt 23/08/2026: phiếu hoàn của đơn Pancake đã huỷ cũng về
	# chung màn Phiếu hoàn tiền để chị Dung xử lý một chỗ. Những phiếu đó
	# không có hoá đơn nào, nên nếu vẫn lọc theo `hoa_don` thì chúng bị gạt
	# ra khỏi vòng quét và mãi mãi nằm ở "Chờ chi".
	for d in ds:
		d["ma_do"] = ma_do_soat(d)
	ds = [d for d in ds if d.get("ma_do")]
	if not ds:
		return {"da_khop": 0, "xem_xet": [], "ghi_chu": "Không có phiếu nào chờ đối soát."}

	try:
		gds = frappe.db.sql(
			"""select name, description, withdrawal, date, reference_number
			from `tabBank Transaction`
			where docstatus < 2 and ifnull(withdrawal, 0) > 0
			  and date >= DATE_SUB(CURDATE(), INTERVAL %s DAY)""",
			(cint(so_ngay) or 30,),
			as_dict=True,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: doc sao ke loi")
		return {"da_khop": 0, "xem_xet": [], "ghi_chu": "Chưa đọc được sao kê ngân hàng."}

	# Khoa trung giao dich. Doc mot lan truoc vong quet, roi BOI THEM ngay
	# trong vong: hai ho so cung duoc khop trong CUNG mot lan chay thi ho so
	# thu hai phai thay dau ho so thu nhat vua dat, chu khong doc lai co so
	# du lieu (o thoi diem do ban ghi da co nhung doc lai moi dong la mot
	# cau truy van cho moi cap ho so - giao dich).
	da_chiem = _gd_da_chiem(tru_ho_so=ho_so)

	da, xem, sinh = 0, [], []
	for d in ds:
		for g in gds:
			mo_ta = "%s %s" % (g.get("description") or "", g.get("reference_number") or "")
			if not khop_giao_dich(mo_ta, d["ma_do"]):
				continue
			chu_cu = da_chiem.get(g["name"])
			if chu_cu and chu_cu != d["name"]:
				# Bay len cho NGUOI xem chu khong im lang bo qua: day co the
				# la hai phieu that cho hai lan hoan that, va luc do sao ke
				# con thieu mot dong chu khong phai phieu sai.
				xem.append({
					"ho_so": d["name"],
					"hoa_don": d["hoa_don"],
					"tien_phieu": flt(d["so_tien"]),
					"tien_chuyen": flt(g["withdrawal"]),
					"giao_dich": g["name"],
					"trung_voi": chu_cu,
				})
				continue
			# Khop noi dung roi van phai so TIEN. Noi dung dung ma so tien
			# lech nghia la ke toan chuyen thieu hoac thua, va do la viec
			# nguoi phai xem chu khong phai may tu dong danh dau xong.
			if abs(flt(g["withdrawal"]) - flt(d["so_tien"])) > 1:
				xem.append(
					{
						"ho_so": d["name"],
						"hoa_don": d["hoa_don"],
						"tien_phieu": flt(d["so_tien"]),
						"tien_chuyen": flt(g["withdrawal"]),
						"giao_dich": g["name"],
					}
				)
				continue
			frappe.db.set_value(
				DT,
				d["name"],
				{
					"da_doi_soat": 1,
					"ma_gd": g["name"],
					"ngay_doi_soat": now_datetime(),
					"trang_thai": "Da doi soat",
					"loi_sinh_ct": "",
				},
			)
			da_chiem[g["name"]] = d["name"]
			# GHI XUONG NGAY, TRUOC khi sinh chung tu.
			#
			# Truoc 19/08/2026 hai viec nay nam chung mot giao dich co so du
			# lieu: danh dau da doi soat, roi sinh chung tu, hong thi
			# rollback. Ma rollback do xoa luon cai dau da doi soat vua ghi.
			#
			# Ket qua thay tren phieu HT-2026-00899: tien 185.000 d DA RA
			# khoi tai khoan MB luc 18:00, sao ke co dung dong do voi dung
			# noi dung "THE VAGABOND HOAN TIEN HDB-26-08-00581", may khop
			# dung phieu - nhung mot loi NameError trong buoc sinh chung tu
			# lam rollback xoa het, nen phieu van nam o "Cho chi". Nhip cham
			# 35 phut moi gio lai chay lai, lai hong, lai xoa dau. Ca chuoi
			# lap vo tan va khong ai nhin thay gi ngoai mot phieu mai khong
			# nhuc nhich.
			#
			# Hai su that khac han nhau, khong duoc gop lam mot:
			#   tien da ra va da khop  -> la SU THAT, ghi xuong ngay.
			#   chung tu sinh duoc chua -> la viec sau, hong thi ghi ro loi.
			frappe.db.commit()
			da += 1
			# TIEN DA RA THAT. Day la moc duy nhat sinh chung tu.
			#
			# Boc rieng tung ho so: mot ho so hong khong duoc keo theo ca me
			# dang quet, vi cac ho so khac da duoc danh dau doi soat roi.
			try:
				ho = frappe.get_doc(DT, d["name"])
				kq = _sinh_chung_tu(ho)
				if not kq.get("bo_qua"):
					kq["ho_so"] = d["name"]
					sinh.append(kq)
				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
				frappe.log_error(
					frappe.get_traceback(), "hoan_tien: sinh chung tu sau doi soat loi %s" % d["name"]
				)
				# Ghi loi LEN CHINH PHIEU. Error Log chi ke toan biet duong
				# mo, ma nguoi ngoi truoc phieu moi la nguoi can biet vi sao
				# chua co phieu chi.
				try:
					frappe.db.set_value(
						DT, d["name"], "loi_sinh_ct",
						("Tiền đã ra và đã khớp sao kê, nhưng máy chưa sinh được "
						 "chứng từ: %s. Nhờ kế toán bấm lại nút Đối soát lệnh chi, "
						 "còn không được thì báo anh Việt."
						 % str(frappe.get_traceback()).strip().splitlines()[-1][:200]),
					)
					frappe.db.commit()
				except Exception:
					pass
			break
	frappe.db.commit()
	return {"da_khop": da, "xem_xet": xem[:50], "so_phieu_quet": len(ds), "da_sinh": sinh}


@frappe.whitelist()
def sepay_tien_ra(mo_ta="", so_tien=0, ma_gd=""):
	"""Duong SePay bao mot dong TIEN RA, may tu tim phieu hoan tien khop.

	Anh Viet 16/08/2026: "quet dong tien ra, neu noi dung chua ma hoa don
	thi tu map vao phieu HT- tuong ung".

	Ham nay lam dung viec do cho MOT dong, dung khi SePay goi thang vao.
	Con duong chay theo gio thi van la doi_soat() doc bang Bank Transaction.
	Hai duong dung chung mot phep khop va chung mot buoc sinh chung tu, nen
	khong the lech nhau.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	# Doi chieu voi cac phieu DANG CHO, qua chon_ma_khop - dung phep ma
	# duong chay theo gio dung, khong de hai duong lech nhau.
	cho = frappe.get_all(
		DT, filters={"da_doi_soat": 0, "trang_thai": ["!=", "Da huy"]},
		fields=["name", "hoa_don", "so_tien", "trang_thai", "loai_hoan", "noi_dung_ck"],
		limit_page_length=0,
	)
	# Dò theo cùng một phép với đường chạy theo giờ. Xem ghi chú ở
	# `chon_ma_khop` về việc hai đường lệch nhau đã tốn của tiệm một ngày.
	for c in cho:
		c["ma_do"] = ma_do_soat(c)
	ma = chon_ma_khop(mo_ta, [c["ma_do"] for c in cho if c.get("ma_do")])
	if not ma:
		doc_duoc = tim_ma_hoa_don(mo_ta)
		return {
			"khop": 0,
			"ma": doc_duoc,
			"vi_sao": (
				"Không có phiếu hoàn tiền nào đang chờ cho đơn %s." % doc_duoc
				if doc_duoc
				else "Nội dung chuyển khoản không chứa mã hoá đơn nào."
			),
		}
	d = next((c for c in cho if str(c["ma_do"]).upper() == ma.upper()), None)
	if not d:
		return {"khop": 0, "ma": ma, "vi_sao": "Không có phiếu hoàn tiền nào đang chờ cho đơn %s." % ma}
	if flt(so_tien) and abs(flt(so_tien) - flt(d["so_tien"])) > 1:
		return {
			"khop": 0,
			"ma": ma,
			"ho_so": d["name"],
			"vi_sao": "Số tiền chuyển %s đ lệch với số trên phiếu %s đ. Kế toán mở phiếu ra "
			"xem lại rồi khớp tay." % (
				"{:,.0f}".format(flt(so_tien)).replace(",", "."),
				"{:,.0f}".format(flt(d["so_tien"])).replace(",", "."),
			),
		}
	# Khoa trung giao dich, giong het duong chay theo gio. SePay co the goi
	# lai cung mot giao dich (co che thu lai cua ho), va hai phieu hoan cua
	# cung mot hoa don goc thi deu khop noi dung nhu nhau. Thieu khoa nay la
	# mot lan tien ra sinh ra hai phieu chi.
	ma_gd_sach = (ma_gd or "").strip()
	if ma_gd_sach:
		chu_cu = _gd_da_chiem(tru_ho_so=d["name"]).get(ma_gd_sach)
		if chu_cu:
			return {
				"khop": 0,
				"ma": ma,
				"ho_so": d["name"],
				"trung_voi": chu_cu,
				"vi_sao": "Giao dịch %s đã được gắn cho phiếu %s rồi. Một lần tiền ra "
				"chỉ khớp cho một phiếu hoàn. Nếu đây thật sự là hai lần hoàn khác "
				"nhau thì sao kê còn thiếu một dòng, báo anh Việt nạp bù giúp."
				% (ma_gd_sach, chu_cu),
			}
	frappe.db.set_value(
		DT,
		d["name"],
		{
			"da_doi_soat": 1,
			"ma_gd": ma_gd_sach,
			"ngay_doi_soat": now_datetime(),
			"trang_thai": "Da doi soat",
		},
	)
	ho = frappe.get_doc(DT, d["name"])
	kq = _sinh_chung_tu(ho)
	frappe.db.commit()
	kq["khop"] = 1
	kq["ho_so"] = d["name"]
	kq["ma"] = ma
	return kq


def doi_soat_tu_dong():
	"""Chay hang gio. Ham tu thoat neu khong co phieu nao cho."""
	try:
		frappe.set_user("Administrator")
		doi_soat()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: doi soat tu dong loi")


# --------------------------------------------------------------- doc cho man


def noi_dung_dung(loai_hoan, hoa_don, noi_dung_hien, da_doi_soat,
		noi_dung_pancake=""):
	"""Chuoi noi dung chuyen khoan DUNG cua mot phieu hoan tien. THUAN.

	MOT CHO DUY NHAT quyet dinh chuoi nay. Truoc v292 co hai duong: luc lap
	phieu thi don_huy dung `noi_dung_chuyen_khoan(ma_don, ma_hien_thi)`, con
	luc MO phieu thi `thong_tin_chuyen_khoan` dung `noi_dung_ck(hoa_don)`.
	Hai duong cho hai ket qua khac nhau tren cung mot phieu, va duong thu hai
	con GHI DE len duong thu nhat.

	LOI ANH VIET BAO 24/08/2026, va day la nguyen nhan that
	-------------------------------------------------------
	*"phieu hoan tien da thong nhat la hoan theo don huy thi noi dung se hoan
	theo ma don pancake nhung o noi dung chuyen khoan cua phieu thi khong
	thay de ma don. Ben ngoai co ma, ma ben trong thi khong co ma."*

	Phieu hoan cua don Pancake da huy KHONG co hoa don nao - do chinh la ly
	do luong do ton tai. Ma cau sua chua cu khong he hoi den chuyen do:

	    if not da_doi_soat and not khop_giao_dich(nd, hoa_don):
	            nd = noi_dung_ck(hoa_don)

	`hoa_don` rong nen `khop_giao_dich` tra False ngay dong dau, dieu kien
	thanh that, va may GHI DE chuoi dung "THE VAGABOND HOAN TIEN 92156" bang
	`noi_dung_ck("")` tuc "THE VAGABOND HOAN TIEN" tron - roi ghi luon xuong
	co so du lieu. Mo phieu mot lan la mat ma don vinh vien. Danh sach van
	con chip "don 92156" vi chip do doc o `ma_don_pancake`, mot o khac.

	Hong nay khong dung o cho mat mot dong chu: chuoi noi dung chinh la thu
	DUY NHAT `ma_do_soat` dem tim tren sao ke cho phieu Pancake, nen phieu bi
	xoa ma thi khong bao gio tu khop duoc nua, nam mai o "Cho chi".

	Cau sua chua cu van con, nhung nay chi ap cho phieu CO hoa don - dung
	pham vi no sinh ra de phuc vu: doi cu phap cu "HT <ma to tra hang>" cua
	truoc 16/08/2026 sang ma hoa don goc.

	KHONG dung vao phieu DA doi soat. Chuoi tren phieu do la thu ke toan da
	go vao ngan hang that; sua no la sua lai qua khu.

	`noi_dung_pancake` la chuoi dung phai, do noi goi doc lai tu ban ghi Don
	da huy. Rong thi giu nguyen chuoi dang co chu khong bia ra chuoi moi.
	"""
	nd = str(noi_dung_hien or "").strip()
	try:
		da = int(da_doi_soat or 0)
	except (TypeError, ValueError):
		da = 0
	if da:
		return nd
	if str(loai_hoan or "").strip() == LOAI_HUY_PANCAKE:
		return str(noi_dung_pancake or "").strip() or nd
	hd = str(hoa_don or "").strip()
	if hd and not khop_giao_dich(nd, hd):
		return noi_dung_ck(hd)
	return nd


def _noi_dung_pancake(ho_so):
	"""Chuoi noi dung chuyen khoan dung phai cua mot phieu hoan Pancake.

	Doc lai tu ban ghi Don da huy chu KHONG tu ghep chuoi tu `ma_don_pancake`:
	don Pancake co HAI ma, `ma_don` la ma he thong va `ma_hien_thi` la so don
	nhan vien doc, va noi dung chuyen khoan luc lap phieu lay `ma_hien_thi`
	truoc. Ghep tay o day thi co ngay mot chuoi khac chuoi da lap, ma khac
	mot ky tu la phep doi soat truot.
	"""
	ma = str(ho_so.get("ma_don_pancake") or "").strip()
	if not ma:
		return ""
	from vagabond.don_huy import DT as DH
	from vagabond.don_huy import noi_dung_chuyen_khoan

	r = frappe.db.get_value(DH, {"ma_don": ma}, ["ma_don", "ma_hien_thi"], as_dict=True)
	if not r:
		return ""
	return noi_dung_chuyen_khoan(r.get("ma_don"), r.get("ma_hien_thi"))


def _noi_dung_dung(d):
	"""Doc chuoi dung, tu sua xuong co so du lieu neu dang sai. Cham he."""
	cu = str(d.noi_dung_ck or "").strip()
	nd = noi_dung_dung(
		d.loai_hoan, d.hoa_don, cu, cint(d.da_doi_soat),
		_noi_dung_pancake(d) if str(d.loai_hoan or "").strip() == LOAI_HUY_PANCAKE else "",
	)
	if nd != cu:
		frappe.db.set_value(DT, d.name, "noi_dung_ck", nd, update_modified=False)
		frappe.db.commit()
	return nd


@frappe.whitelist()
def thong_tin_chuyen_khoan(ho_so=None):
	"""Cuc chu de ke toan copy mot phat vao MB Biz, khoi go tay tung o.

	Go tay so tai khoan la duong de sai nhat trong ca luong: sai mot chu so
	la tien di vao mot tai khoan khong quen biet, va lay lai rat kho.

	Tra ba dang cua cung mot thong tin, vi ba dang phuc vu ba viec khac
	nhau (dung y het nep ho so thanh toan APP dang chay):
	  chu      - doc bang mat, kiem truoc khi bam
	  dong_tab - dan thang vao tep lo cua MB, moi cot mot o
	  noi_dung - chuoi rieng de bam chep cho o Noi dung tren MB Biz
	"""
	from vagabond.ban_hang import _kiem_quyen
	from vagabond.ho_so_tt import _bo_dau

	_kiem_quyen()
	d = frappe.get_doc(DT, ho_so)
	ten_nh = ""
	if d.ngan_hang:
		ten_nh = frappe.db.get_value("Bank", d.ngan_hang, "bank_name") or d.ngan_hang

	# Phieu lap TRUOC 16/08/2026 mang noi dung theo cu phap cu "HT <ma to tra
	# hang>". Duong doi soat moi do theo MA HOA DON GOC, nen noi dung cu se
	# khong bao gio khop, va phieu nam mai o Cho chi ma khong ai biet vi sao.
	#
	# Bat duoc khi kiem tren he ngay sau khi deploy v192: phieu cu tra ve
	# "HT HDB-26-08-00341" - do la ma TO TRA HANG, khong phai ma don.
	#
	# Chi dung lai cho phieu CHUA doi soat. Phieu da doi soat thi noi dung do
	# la thu ke toan da go vao ngan hang that, sua no la sua lai qua khu.
	nd = _noi_dung_dung(d)
	tien_so = "%d" % int(round(flt(d.so_tien)))
	tien_dep = "{:,.0f}".format(flt(d.so_tien)).replace(",", ".")
	# Ten chu tai khoan phai BO DAU VIET HOA: ngan hang khong nhan tieng
	# Viet co dau o o nguoi thu huong, va go lai tay la them mot cho sai.
	ten_ck = _bo_dau(d.ten_tk or "").upper()

	dong = [
		"Ngân hàng: %s" % (ten_nh or "(chưa khai)"),
		"Số tài khoản: %s" % (d.so_tk or "(chưa khai)"),
		"Tên chủ tài khoản: %s" % (ten_ck or "(chưa khai)"),
		"Số tiền: %s" % tien_dep,
		"Nội dung: %s" % nd,
	]
	# Cau truc cot cua tep lo do ngan_hang.tep_lo quyet, KHONG dung o day.
	# Anh Viet chot 17/08/2026: moi nut Xuat MB Biz tren app deu goi chung
	# mot ham backend, khong cho nao tu dung cot rieng.
	from vagabond.ngan_hang import tep_lo

	lo = tep_lo(
		json.dumps(
			[
				{
					"so_tk": d.so_tk,
					"ten_nhan": d.ten_tk,
					"ngan_hang": ten_nh,
					"so_tien": flt(d.so_tien),
					"noi_dung": nd,
				}
			]
		)
	)
	cot = lo["cot"]
	gia_tri = [str(x) for x in lo["bang"][0]]

	thieu = [x for x in ("so_tk", "ten_tk", "ngan_hang") if not d.get(x)]
	ten_thieu = {"so_tk": "số tài khoản", "ten_tk": "tên chủ tài khoản", "ngan_hang": "ngân hàng"}
	return {
		"ma": d.name,
		"hoa_don": d.hoa_don,
		"chu": "\n".join(dong),
		"cot": cot,
		"gia_tri": gia_tri,
		"dong_tab": "\t".join(gia_tri),
		"tieu_de_tab": "\t".join(cot),
		"so_tien": flt(d.so_tien),
		"ten_ck": ten_ck,
		"so_tk": (d.so_tk or "").strip(),
		"ngan_hang": ten_nh,
		"tsv": lo["tsv"],
		"nhac_lo": lo.get("nhac", []),
		"thieu": thieu,
		"nhac": (
			"Còn thiếu %s. Bổ sung vào phiếu rồi bấm lại thì mới chuyển được."
			% ", ".join(ten_thieu[x] for x in thieu)
			if thieu
			else ""
		),
		"noi_dung_ck": nd,
		"da_doi_soat": cint(d.da_doi_soat),
	}


@frappe.whitelist()
def ds_ngan_hang(tim=""):
	"""Danh sach ngan hang cho o chon tren app."""
	loc = {}
	if (tim or "").strip():
		loc = {"name": ["like", "%%%s%%" % tim.strip()]}
	return frappe.get_all("Bank", filters=loc, fields=["name"], limit_page_length=60, order_by="name")


@frappe.whitelist()
def tinh_trang(si_name=None):
	"""Man Chi tiet don hoi: don nay hoan tien duoc khong, da hoan chua."""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	d = frappe.db.get_value(
		SI, si_name, ["name", "docstatus", "vgb_huy", "grand_total", "custom_hddt_so"], as_dict=True
	)
	if not d:
		return {"duoc": 0, "vi_sao": "Không có hoá đơn này."}
	# Phieu DA BI TU CHOI thi khong duoc chan don nay nua.
	#
	# Anh Viet bat duoc 19/08/2026 tren don 91433: phieu HT-2026-00871 anh da
	# tu choi, vay ma man Chi tiet don van bao "Đã hoàn tiền ... đã huỷ" va
	# van khong cho lap phieu moi. Sales ket cung, khong hoan duoc dong nao
	# cho khach.
	#
	# Cho nay la mot cho lech cua chinh tep nay: cac ham khac (dong 545, 813,
	# 1262, 1364) deu da loai "Da huy" ra tu lau, rieng tinh_trang thi khong.
	# Nen day khong phai doi luat, day la sua cho quen.
	CON_SONG = ["name", "trang_thai", "so_tien", "da_doi_soat"]
	song = frappe.db.get_value(
		DT, {"hoa_don": si_name, "trang_thai": ["!=", "Da huy"]}, CON_SONG, as_dict=True
	)
	if song:
		return {
			"duoc": 0,
			"da_hoan": song,
			"vi_sao": "Đơn này đã có yêu cầu hoàn tiền %s, đang ở trạng thái \"%s\"."
			% (song["name"], song["trang_thai"]),
		}
	# Khong con phieu song. Van tra ve phieu bi tu choi gan nhat de man hinh
	# noi ro cho sales biet da tung co mot phieu va no bi tu choi, chu khong
	# im lang nhu chua tung co gi.
	bi_tu_choi = frappe.db.get_value(
		DT, {"hoa_don": si_name, "trang_thai": "Da huy"}, CON_SONG,
		as_dict=True, order_by="creation desc",
	)
	if cint(d.docstatus) != 1:
		return {"duoc": 0, "bi_tu_choi": bi_tu_choi, "vi_sao": "Đơn chưa ghi sổ nên sửa hoặc huỷ thẳng được, không cần hoàn tiền."}
	if cint(d.get("vgb_huy")):
		return {"duoc": 0, "bi_tu_choi": bi_tu_choi, "vi_sao": "Đơn đã mang dấu huỷ."}
	# Goi y san tai khoan khach da dung o lan truoc, neu co. Doc tu chinh
	# ho so hoan tien cu cua khach nay chu khong doan.
	goi_y = {}
	kh = frappe.db.get_value(SI, si_name, "customer")
	if kh:
		cu = frappe.db.get_value(
			DT, {"khach": kh, "so_tk": ["is", "set"]}, ["ten_tk", "so_tk", "ngan_hang"],
			as_dict=True, order_by="creation desc",
		)
		if cu:
			goi_y = {k: v for k, v in cu.items() if v}
	return {
		"duoc": 1,
		"bi_tu_choi": bi_tu_choi,
		"so_tien": flt(d.grand_total),
		"ly_do_co_the": list(LY_DO),
		"goi_y_tk": goi_y,
		"khach": _khach_tren_don(si_name, kh),
		"canh_bao_hddt": (d.get("custom_hddt_so") or "").strip(),
	}


KHACH_LE = "Khách lẻ Online"


def tach_ghi_chu_don(ghi_chu):
	"""Doc ten khach va so dien thoai tu o ghi chu cua hoa don. THUAN.

	ban_hang.tao_don_tay dung o remarks theo khuon:

	    <nguon> #<ma don> - <ten khach>[ - <so dien thoai>][ - Quay <ma>]

	Vi du that tren he:
	    "Pancake #91759 - Loan Anh - 0933751352"
	    "Mang về #TEST-HT-02 - Khách thử hoàn tiền 2 - Quầy TCV"

	Tra (ten, sdt), cai nao khong co thi la chuoi rong.

	Vi sao phai doc tu day chu khong doc mot o cho tu te: so dien thoai
	khach le KHONG duoc luu thanh truong rieng tren hoa don - kiem tren he
	17/08/2026 thi contact_mobile va contact_phone deu rong. Cho duy nhat
	con giu la o ghi chu. Doc no la hoi lai mot thu da co san, con hon bat
	nhan vien go lai mot so ma khach vua doc xong cach do ba phut.
	"""
	s = str(ghi_chu or "").strip()
	if " - " not in s:
		return "", ""
	# Bo phan dau "<nguon> #<ma don>", giu phan sau dau gach dau tien.
	phan = [x.strip() for x in s.split(" - ")]
	phan = phan[1:]
	# Bo duoi "Quay <ma>" neu co - do khong phai thong tin khach.
	phan = [x for x in phan if x and not x.lower().startswith("quầy") and not x.lower().startswith("quay")]
	ten, so = "", ""
	for x in phan:
		chi_so = re.sub(r"[^0-9]", "", x)
		# Mot manh toan chu so va dai bang mot so dien thoai thi la so.
		if chi_so and len(chi_so) >= 9 and len(chi_so) >= len(x) - 2:
			if not so:
				so = chi_so
		elif not ten:
			ten = x
	return ten, so


def _khach_tren_don(si_name, ma_khach=None):
	"""Ten va so dien thoai khach de dien san vao form. Tra dict.

	Anh Viet 17/08/2026: "nhan vien khong phai go lai".

	Doc theo thu tu tin cay giam dan:
	  1. Khach thanh vien tren don (vgb_khach_no) - chac nhat, co ho so
	  2. Ten khach tren don, neu khong phai ten khach le chung
	  3. O ghi chu cua don - noi duy nhat con giu so cua khach le

	KHONG tron nguon cho tung o: neu lay duoc ho so khach thanh vien thi
	lay ca ten lan so tu do. Tron ten cua nguoi nay voi so cua nguoi kia la
	dua ke toan mot dia chi nhan tien khong thuoc ve ai.
	"""
	ra = {"ten": "", "sdt": "", "nguon": ""}
	try:
		d = frappe.db.get_value(
			SI, si_name, ["customer_name", "vgb_khach_no", "remarks", "customer"], as_dict=True
		) or {}
		tv = d.get("vgb_khach_no") or (ma_khach if ma_khach and ma_khach != KHACH_LE else "")
		if tv:
			kh = frappe.db.get_value("Customer", tv, ["customer_name", "mobile_no"], as_dict=True) or {}
			if (kh.get("customer_name") or "").strip() and kh["customer_name"] != KHACH_LE:
				ra["ten"] = kh["customer_name"].strip()
				ra["sdt"] = sdt(kh.get("mobile_no") or "")
				ra["nguon"] = "hồ sơ khách thành viên"
		if not ra["ten"]:
			ten_don = (d.get("customer_name") or "").strip()
			if ten_don and ten_don != KHACH_LE:
				ra["ten"] = ten_don
				ra["nguon"] = "tên khách trên đơn"
		if not ra["ten"] or not ra["sdt"]:
			ten_gc, so_gc = tach_ghi_chu_don(d.get("remarks"))
			if not ra["ten"] and ten_gc:
				ra["ten"] = ten_gc
				ra["nguon"] = "ghi chú trên đơn"
			if not ra["sdt"] and so_gc:
				ra["sdt"] = sdt(so_gc) or so_gc
				if not ra["nguon"]:
					ra["nguon"] = "ghi chú trên đơn"
	except Exception:
		# Doc goi y hong thi form van mo duoc, nhan vien go tay. KHONG nem
		# loi lam chet ca man vi mot o dien san.
		frappe.log_error(frappe.get_traceback(), "hoan_tien: doc khach tren don loi")
	return ra


def dong_bo_so_hddt(ma_phieu, ma_don, dang_luu=""):
	"""Lay so hoa don dien tu cua don goc, va va lai neu phieu dang giu so cu.

	KHONG whitelist: ham nay GHI vao co so du lieu va chi duoc goi tu ben
	trong. Ca kiem `thu_cua_ngo` chot dieu do. Dat ham nay ngay tren `ds` da
	tung lam decorator @frappe.whitelist() cua `ds` bam nham sang day va man
	Hoan tien tren app chet ngay, 19/08/2026.

	Chi Dung 19/08/2026: *"phieu hoan tien neu co them so hoa don dien tu thi
	nhanh hon do phai kiem a, thi c se thay the hoa don nhanh hon a"*.

	Vi sao khong de mac fetch_from lo het: Frappe chi keo lai gia tri fetch
	moi lan LUU phieu. Ma trinh tu that thi nguoc: phieu hoan tien duoc lap
	NGAY LUC khach doi tra, con hoa don dien tu thi phat hanh sau, co khi
	sang hom sau. Den luc so hoa don co that thi khong ai luu lai phieu nua,
	nen o do nam trong mai mai - dung cai o ma ke toan can nhat.

	Nen moi lan man hinh doc phieu, doc luon so tren don goc. Lech thi va
	lai vao phieu, khong doi modified de khong lam ban lich su sua doi.
	"""
	if not ma_don:
		return (dang_luu or "").strip()
	that = (frappe.db.get_value(SI, ma_don, "custom_hddt_so") or "").strip()
	if that and that != (dang_luu or "").strip():
		frappe.db.set_value(DT, ma_phieu, "so_hddt", that, update_modified=False)
		return that
	return (dang_luu or "").strip() or that


@frappe.whitelist()
def ds(trang_thai="", so_dong=100, tim=""):
	"""Danh sach phieu hoan tien cho man Hoan tien tren app.

	Bo loc va o tim chay o MAY CHU (QT-19). Doanh so mot mua co the sinh vai
	tram phieu, keo het ve dien thoai roi loc bang JavaScript la treo may -
	va con sai, vi so tren chip se chi dem phan da keo ve.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	loc = {}
	tt = (trang_thai or "").strip()
	if tt and tt != "tat_ca":
		loc["trang_thai"] = tt
	tim = (tim or "").strip()
	if tim:
		# Ba cho nguoi ta go vao o tim: ten khach, ma phieu, ma hoa don.
		# frappe.get_all khong co "hoac" giua nhieu truong nen phai dung
		# or_filters.
		ma_kh_tim = [
			c["name"]
			for c in frappe.get_all(
				"Customer",
				filters={"customer_name": ["like", "%%%s%%" % tim]},
				fields=["name"],
				limit_page_length=200,
			)
		]
		hoac = [
			["name", "like", "%%%s%%" % tim],
			["hoa_don", "like", "%%%s%%" % tim],
			# Phiếu của đơn Pancake đã huỷ không có mã hoá đơn nào, thứ kế
			# toán gõ vào ô tìm sẽ là mã đơn.
			["ma_don_pancake", "like", "%%%s%%" % tim],
			["ten_tk", "like", "%%%s%%" % tim],
			["so_tk", "like", "%%%s%%" % tim],
		]
		if ma_kh_tim:
			hoac.append(["khach", "in", ma_kh_tim])
	else:
		hoac = None

	ds_ = frappe.get_all(
		DT,
		filters=loc,
		or_filters=hoac,
		fields=[
			"name", "hoa_don", "ma_don_pancake", "hoa_don_tra", "phieu_chi", "khach", "so_tien",
			"ly_do", "trang_thai", "da_doi_soat", "noi_dung_ck", "creation",
			"ten_tk", "so_tk", "ngan_hang", "nguoi_duyet", "loai_hoan",
			# ma_gd la ma giao dich ngan hang da khop. Thieu no thi cot do
			# trong tep Excel cua chi Dung luon rong, ma do lai chinh la cot
			# ke toan dung de doi chieu voi sao ke.
			"so_hddt", "loi_sinh_ct", "ma_gd",
		],
		order_by="creation desc",
		limit_page_length=max(1, min(500, cint(so_dong) or 100)),
	)
	ma_kh = list({d["khach"] for d in ds_ if d.get("khach")})
	ten = {}
	if ma_kh:
		for c in frappe.get_all(
			"Customer", filters={"name": ["in", ma_kh]}, fields=["name", "customer_name"], limit_page_length=0
		):
			ten[c["name"]] = c["customer_name"]
	# Phieu chi da ghi so chua - de man hinh biet cai nao con cho ke toan.
	ma_pc = list({d["phieu_chi"] for d in ds_ if d.get("phieu_chi")})
	pc = {}
	if ma_pc:
		for p in frappe.get_all(
			PE, filters={"name": ["in", ma_pc]}, fields=["name", "docstatus"], limit_page_length=0
		):
			pc[p["name"]] = cint(p["docstatus"])
	# Da co uy nhiem chi chua - dem mot luot cho ca trang chu khong moi
	# dong mot cau. Chi Dung can nhin luot la biet phieu nao con cho minh
	# dinh giay to, khong phai mo tung phieu ra xem.
	unc = {}
	if ma_pc:
		for f in frappe.get_all(
			"File",
			filters={"attached_to_doctype": PE, "attached_to_name": ["in", ma_pc]},
			fields=["attached_to_name"],
			limit_page_length=0,
		):
			unc[f["attached_to_name"]] = unc.get(f["attached_to_name"], 0) + 1
	# Anh bang chung: ke toan ngoi xa quay, cai duy nhat ho co de quyet la
	# anh Sales chup. Tra thang duong dan de man ve thanh o anh bam xem to.
	anh = {}
	if ds_:
		for f in frappe.get_all(
			"File",
			filters={"attached_to_doctype": DT, "attached_to_name": ["in", [d["name"] for d in ds_]]},
			fields=["attached_to_name", "file_url", "file_name"],
			limit_page_length=0,
		):
			anh.setdefault(f["attached_to_name"], []).append(
				{"url": f["file_url"], "ten": f["file_name"]}
			)
	# So hoa don dien tu cua don goc: doc mot luot cho ca trang roi va lai o
	# nao con trong. Mot cau truy van cho ca danh sach, khong phai moi dong
	# mot cau.
	ma_don = list({d["hoa_don"] for d in ds_ if d.get("hoa_don")})
	so_hddt = {}
	if ma_don:
		for si in frappe.get_all(
			SI, filters={"name": ["in", ma_don]},
			fields=["name", "custom_hddt_so"], limit_page_length=0
		):
			so_hddt[si["name"]] = (si["custom_hddt_so"] or "").strip()
	for d in ds_:
		d["ten_khach"] = ten.get(d.get("khach") or "", d.get("khach") or "")
		d["phieu_chi_da_ghi"] = 1 if pc.get(d.get("phieu_chi") or "") == 1 else 0
		d["co_unc"] = 1 if unc.get(d.get("phieu_chi") or "") else 0
		d["anh"] = anh.get(d["name"], [])
		that = so_hddt.get(d.get("hoa_don") or "", "")
		if that and that != (d.get("so_hddt") or "").strip():
			frappe.db.set_value(DT, d["name"], "so_hddt", that, update_modified=False)
			d["so_hddt"] = that
	# Con so tren chip la so THAT cua ca so, khong phai so dong dang hien.
	# Dem theo dung o tim dang go, neu khong thi go "Nhung" ra 3 dong ma
	# chip van bao 40, va ke toan khong biet tin cai nao.
	dem = {}
	for t in ("Cho chi", "Da chi", "Da doi soat", "Hoan thanh", "Da huy"):
		l2 = dict(loc)
		l2["trang_thai"] = t
		dem[t] = len(
			frappe.get_all(DT, filters=l2, or_filters=hoac, fields=["name"], limit_page_length=0)
		)
	dem["tat_ca"] = sum(dem.values())
	return {
		"ds": ds_,
		"dem": dem,
		"kho_huy": _cd()["kho_huy"],
		"tk_chi": _cd()["tk_chi"],
		"duoc_tu_choi": 1 if _duoc_tu_choi() else 0,
	}


def _duoc_tu_choi(nguoi=None):
	"""Ai duoc bam Tu choi hoan tien. THUAN theo nghia khong ghi gi.

	Tu choi la chan MOT dong tien sap ra, nen dat cung mot cua voi nguoi
	quyet chi: ke toan va giam doc. Sales lap phieu duoc nhung khong tu
	quyet duoc phieu cua chinh minh.
	"""
	vai = set(frappe.get_roles(nguoi or frappe.session.user))
	return bool(vai & {"System Manager", "Accounts Manager", "Accounts User", "Giám đốc"})


@frappe.whitelist()
def dem_cho_chi():
	"""So phieu dang cho chi - de trang chu cham badge do tren o Ke toan.

	Anh Viet 18/08/2026: "neu co phieu o trang thai Cho chi, hien badge do
	bao so luong tren icon de chi Dung Ke toan truong de nhan biet".

	Ham nay co the bi goi moi lan mo trang chu nen phai re: mot phep dem,
	khong keo dong nao ve.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	return {"cho_chi": frappe.db.count(DT, {"trang_thai": "Cho chi"})}


@frappe.whitelist()
def xuat_excel(trang_thai="", tim="", so_dong=500):
	"""Danh sach phieu hoan tien ra Excel cho chi Dung theo doi.

	Chi Dung 19/08/2026, qua anh Viet: *"cho anh nut xuat duoc danh sach
	hoan tien nay ra excel"*.

	Xuat DUNG cai dang hien tren man: cung bo loc, cung o tim, cung thu tu.
	Tep Excel ma khac man hinh la mot ngay nao do hai ben cai nhau ve mot
	con so, nen o day goi thang ds() chu khong viet lai truy van.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	kq = ds(trang_thai=trang_thai, so_dong=so_dong, tim=tim)
	# ds() tra danh sach duoi khoa "ds", KHONG phai "rows".
	#
	# Ban dau em viet kq.get("rows") - doc theo tri nho tu ho_so_tt.danh_sach
	# von dung khoa "rows" - nen tep Excel dau tien xuat ra rong tron, 0 dong,
	# trong khi man hinh dang hien 8 phieu. Bo kiem luc do khong bat duoc vi
	# no chi soi chu trong ma nguon chu khong chay thu. Nay co ca kiem doi
	# chieu ten khoa that.
	rows = kq.get("ds") or []

	bang = [
		["PHIẾU HOÀN TIỀN (CASH-BACK)"],
		[
			"Xuất lúc", str(now_datetime())[:19],
			"Bộ lọc", NHAN_TRANG_THAI.get(trang_thai, "Tất cả") if trang_thai else "Tất cả",
			"Ô tìm", tim or "(không)",
		],
		["Số phiếu", len(rows), "Tổng tiền", sum(flt(r.get("so_tien")) for r in rows)],
		[],
		[
			"Mã phiếu", "Ngày lập", "Khách", "Loại phiếu", "Hoá đơn gốc",
			"Số tiền", "Trạng thái", "Đã đối soát", "Mã giao dịch ngân hàng",
			"Hoá đơn trả hàng", "Phiếu chi", "Uỷ nhiệm chi", "Số hoá đơn điện tử",
			"Chủ tài khoản", "Số tài khoản", "Ngân hàng", "Nội dung chuyển khoản",
			"Người duyệt", "Lý do", "Cảnh báo",
		],
	]
	for r in rows:
		bang.append([
			r.get("name") or "",
			str(r.get("creation") or "")[:10],
			r.get("ten_khach") or r.get("khach") or "",
			NHAN_LOAI_HOAN.get(r.get("loai_hoan") or "", "Trả hàng"),
			r.get("hoa_don") or "",
			flt(r.get("so_tien")),
			NHAN_TRANG_THAI.get(r.get("trang_thai"), r.get("trang_thai") or ""),
			"Rồi" if cint(r.get("da_doi_soat")) else "Chưa",
			r.get("ma_gd") or "",
			r.get("hoa_don_tra") or "",
			r.get("phieu_chi") or "",
			# Cot nay chinh la cai chi Dung dung de biet phieu nao con thieu
			# giay to goc. Thieu UNC thi ho so khong giai trinh duoc, du tien
			# da ra va sao ke da khop.
			"Đã đính" if cint(r.get("co_unc")) else "Chưa đính",
			r.get("so_hddt") or "",
			r.get("ten_tk") or "",
			# Ep chuoi: so tai khoan bat dau bang so 0 ma de dang so thi
			# Excel an mat so 0 dau, va ke toan chuyen nham tai khoan.
			"'" + str(r.get("so_tk") or ""),
			r.get("ngan_hang") or "",
			r.get("noi_dung_ck") or "",
			r.get("nguoi_duyet") or "",
			r.get("ly_do") or "",
			r.get("loi_sinh_ct") or "",
		])
	bang.append([])
	bang.append(["TỔNG", "", "", "", "", sum(flt(r.get("so_tien")) for r in rows)])

	from frappe.utils.xlsxutils import make_xlsx

	tep = make_xlsx(bang, "Phieu hoan tien")
	noi_dung = tep.getvalue() if hasattr(tep, "getvalue") else tep
	return {
		"ten_file": "phieu-hoan-tien-%s.xlsx" % nowdate(),
		"b64": base64.b64encode(noi_dung).decode(),
		"so_dong": len(rows),
	}


@frappe.whitelist()
def chi_tiet(ho_so):
	"""Mot phieu hoan tien, du thu de ke toan quyet chi hay tu choi.

	Anh Viet 18/08/2026: "man danh sach khong click vao xem chi tiet duoc".
	Man danh sach chi bay duoc nhung gi nhin luot; con anh bang chung to,
	so tai khoan khach, hoa don goc gom nhung mon gi, ai lap luc nao thi
	phai co mot cho rieng.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not frappe.db.exists(DT, ho_so):
		frappe.throw(
			"Không tìm thấy phiếu hoàn tiền %s. Có thể phiếu đã bị xoá trên "
			"Desk; anh chị quay lại danh sách rồi mở phiếu khác giúp em." % ho_so
		)
	d = frappe.get_doc(DT, ho_so)
	ra = d.as_dict()
	for k in list(ra.keys()):
		if k.startswith("_"):
			ra.pop(k, None)

	ra["ten_khach"] = (
		frappe.db.get_value("Customer", d.khach, "customer_name") if d.khach else ""
	) or (d.khach or "")
	# Noi dung chuyen khoan di qua DUNG mot cho voi man Chuyen khoan. Truoc
	# v292 man chi tiet doc thang o `noi_dung_ck` con man Chuyen khoan thi tu
	# sua chua, nen hai man noi hai chuoi khac nhau tren cung mot phieu.
	ra["noi_dung_ck"] = _noi_dung_dung(d)
	# So hoa don dien tu cua don goc, doc lai tu don chu khong tin o dang
	# luu: hoa don thuong duoc phat hanh SAU luc lap phieu hoan tien.
	ra["so_hddt"] = dong_bo_so_hddt(d.name, d.hoa_don, d.get("so_hddt"))
	ra["anh"] = [
		{"url": f["file_url"], "ten": f["file_name"]}
		for f in frappe.get_all(
			"File",
			filters={"attached_to_doctype": DT, "attached_to_name": ho_so},
			fields=["file_url", "file_name"],
			limit_page_length=0,
		)
	]

	# Hoa don goc: ke toan can biet don nay ban gi, bao nhieu tien, da thu
	# chua - de doi chieu voi so tien dang doi hoan.
	ra["don"] = None
	if d.hoa_don and frappe.db.exists(SI, d.hoa_don):
		si = frappe.get_doc(SI, d.hoa_don)
		ra["don"] = {
			"name": si.name,
			"ngay": str(si.posting_date or ""),
			# Ke toan phai nhin thay CA HAI con so de quyet: tien SePay da
			# nhan va tong don. Voi phieu tien nop thua thi chenh lech giua
			# hai con so nay chinh la can cu duy nhat, khong co anh chup nao
			# thay the duoc.
			"da_nhan_sepay": _tien_da_nhan(si),
			"tong": flt(si.grand_total),
			"da_thu": flt(si.grand_total) - flt(si.outstanding_amount),
			# Ma don Pancake (anh Viet 19/08/2026: *"bo sung luon truong ma
			# don hang Pancake tu keo ben hoa don HDB- ve, can truong do de
			# doi chieu"*). Day khong phai mot o trang tri: chinh chuoi nay
			# la thu duy nhat _sepay_theo_don dem tim trong noi dung chuyen
			# khoan. De trong nghia la dong "SePay da nhan" CHAC CHAN ra 0,
			# va nguoi doc can biet ngay do la vi sao chu khong doan.
			"ma_pancake": (si.get("custom_pancake_display_id") or "").strip(),
			"diem_ban": si.get("custom_diem_ban") or "",
			"mon": [
				{"ten": r.item_name, "sl": flt(r.qty), "tien": flt(r.amount)}
				for r in (si.items or [])
			][:40],
		}

	# Don Pancake da huy: phieu loai nay KHONG co hoa don nao, nen khoi
	# "don goc" o tren luon rong va man chi tiet truoc v292 khong he noi phieu
	# thuoc don nao. Danh sach thi co chip "don 92156" con phieu thi trong -
	# dung cho anh Viet bao 24/08/2026 la "ben ngoai co ma, ben trong khong".
	ra["don_huy"] = None
	if str(d.loai_hoan or "").strip() == LOAI_HUY_PANCAKE and d.get("ma_don_pancake"):
		from vagabond.don_huy import DT as DH

		r = frappe.db.get_value(
			DH, {"ma_don": str(d.get("ma_don_pancake") or "").strip()},
			["name", "ma_don", "ma_hien_thi", "ten_khach", "sdt", "tong_don",
			 "da_nhan", "ngay_dat", "ngay_giao", "trang_thai", "huy_luc"],
			as_dict=True,
		)
		ra["don_huy"] = r or {"ma_don": str(d.get("ma_don_pancake") or "").strip()}

	# Phieu chi: con so duy nhat noi len tien da that su ra khoi tai khoan.
	ra["phieu_chi_trang_thai"] = ""
	if d.phieu_chi and frappe.db.exists(PE, d.phieu_chi):
		ds_ = cint(frappe.db.get_value(PE, d.phieu_chi, "docstatus"))
		ra["phieu_chi_trang_thai"] = {0: "Bản nháp", 1: "Đã ghi sổ", 2: "Đã huỷ"}.get(ds_, "")

	ra["duoc_tu_choi"] = 1 if _duoc_tu_choi() else 0
	# Tien da ra roi thi khong con gi de tu choi nua, chi con duong lap
	# phieu thu lai. Tra thang co nay ra de man hinh khong bay nut vo nghia.
	ra["con_tu_choi_duoc"] = (
		1 if (d.trang_thai == "Cho chi" and not cint(d.da_doi_soat) and not d.phieu_chi) else 0
	)
	ra["kho_huy"] = _cd()["kho_huy"]
	ra["tk_chi"] = _cd()["tk_chi"]

	# Giao dich tien vao da doi chieu tay, neu co.
	ra["gd_vao_ct"] = None
	if d.get("gd_vao") and frappe.db.exists("Bank Transaction", d.get("gd_vao")):
		g = frappe.db.get_value(
			"Bank Transaction", d.get("gd_vao"),
			["name", "date", "deposit", "description", "reference_number", "bank_account"],
			as_dict=True,
		)
		ra["gd_vao_ct"] = g
	ra["duoc_doi_chieu"] = 1 if _duoc_tu_choi() else 0
	ra["hddt"] = _hddt_cua_don(d.hoa_don)

	# Uy nhiem chi va luong ket thuc. Ba co duoi day quyet dinh man hinh ve
	# nut nao, va deu tinh o may chu chu khong de man tu suy (QT-19).
	ra["unc"] = _ds_unc(d.phieu_chi)
	ra["co_unc"] = 1 if ra["unc"] else 0
	# Duoc dinh UNC: da doi soat, co phieu chi con song, va nguoi dang xem
	# la ke toan. Thieu mot trong ba thi man khong ve nut, de khong ai bam
	# vao mot cai nut chi de nhan lai mot dong loi.
	ra["dinh_duoc_unc"] = 1 if (
		_duoc_tu_choi()
		and cint(d.da_doi_soat)
		and d.phieu_chi
		and ra["phieu_chi_trang_thai"] in ("Bản nháp", "Đã ghi sổ")
		and d.trang_thai != "Da huy"
	) else 0
	# Duoc bam Hoan thanh: nhu tren, cong them DA CO tep UNC va phieu chua
	# dong. Phieu chi da ghi so tu truoc van cho bam, vi luc do viec con lai
	# chi la dong ho so.
	ra["ket_thuc_duoc"] = 1 if (
		ra["dinh_duoc_unc"] and ra["co_unc"] and d.trang_thai != "Hoan thanh"
	) else 0
	return ra


@frappe.whitelist()
def gan_gd_vao(ho_so=None, gd=None):
	"""Gan tay mot giao dich tien vao cho phieu hoan tien.

	Vi sao viec nay phai co nguoi bam chu khong de may tu doan: mot khoan
	650.000 d vao ngay 13/08 co the la cua bat ky don nao cung so tien do.
	May chi loc ra ung vien; chon ai la trach nhiem cua nguoi doi chieu, va
	ten nguoi do duoc ghi lai ngay canh giao dich.

	KHONG doi so tien cua phieu, khong sinh chung tu. Day thuan tuy la mot
	dau vet de chi Dung quyet chi.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not _duoc_tu_choi():
		frappe.throw("Chỉ kế toán hoặc giám đốc mới đối chiếu giao dịch tiền vào được.")
	if not frappe.db.exists(DT, ho_so):
		frappe.throw("Không tìm thấy phiếu hoàn tiền %s. Tải lại danh sách giúp em." % ho_so)
	d = frappe.get_doc(DT, ho_so)
	if d.trang_thai == "Da huy":
		frappe.throw("Phiếu %s đã huỷ nên không đối chiếu thêm được." % ho_so)

	gd = (gd or "").strip()
	if not gd:
		# Bo gan: van la mot thao tac co ghi vet, khong xoa vet cu di dau.
		frappe.db.set_value(DT, ho_so, {
			"gd_vao": None,
			"nguoi_gan_gd_vao": frappe.session.user,
			"ngay_gan_gd_vao": frappe.utils.now(),
		})
		frappe.db.commit()
		return {"ok": 1, "gd": ""}

	g = frappe.db.get_value(
		"Bank Transaction", gd,
		["name", "date", "deposit", "withdrawal", "docstatus", "description"], as_dict=True,
	)
	if not g:
		frappe.throw("Không có giao dịch ngân hàng %s. Tìm lại giúp em." % gd)
	if cint(g["docstatus"]) >= 2:
		frappe.throw("Giao dịch %s đã bị huỷ nên không dùng làm căn cứ được." % gd)
	if flt(g["deposit"]) <= 0:
		frappe.throw(
			"Giao dịch %s là tiền RA khỏi tài khoản, không phải tiền khách nộp "
			"vào. Chọn lại một dòng có cột tiền vào giúp em." % gd
		)

	# Mot giao dich chi lam can cu cho MOT phieu. Cho hai phieu cung tro vao
	# mot khoan la mo duong chi hai lan cho mot lan khach chuyen.
	khac = frappe.db.get_value(
		DT, {"gd_vao": gd, "name": ["!=", ho_so], "trang_thai": ["!=", "Da huy"]}, "name"
	)
	if khac:
		frappe.throw(
			"Giao dịch %s đã được gắn cho phiếu %s rồi. Một khoản tiền vào chỉ "
			"làm căn cứ cho một phiếu hoàn." % (gd, khac)
		)

	frappe.db.set_value(DT, ho_so, {
		"gd_vao": gd,
		"nguoi_gan_gd_vao": frappe.session.user,
		"ngay_gan_gd_vao": frappe.utils.now(),
	})
	frappe.db.commit()
	return {"ok": 1, "gd": gd, "so_tien": flt(g["deposit"]), "ngay": str(g["date"] or "")}


@frappe.whitelist()
def tim_gd_ra(ho_so=None, so_ngay=45, tu_khoa=""):
	"""Cac dong tien RA tren sao ke co the la lenh chi cua phieu nay.

	Anh Viet 24/08/2026: *"thieu nut Khop Sepay thu cong (de tu chon giao
	dich tien ra)"*.

	VI SAO CAN BAN TAY, du da co doi soat tu dong. Phep tu dong do CHUOI noi
	dung chuyen khoan. Ke toan chuyen tien tren MB Biz va go noi dung tay,
	nen chi can go thieu mot chu, go dau tieng Viet, hay ngan hang cat bot
	do dai la chuoi khong con khop, va phieu nam mai o "Cho chi" du tien da
	ra that. Man nay khong tu quyet: no chi bay ra cac dong gan dung so tien
	roi de nguoi nhin va chon.

	Ba thu bi loai ngay tai day, de nguoi bam khong phai nho:
	  - dong da bi mot phieu khac chiem
	  - dong da huy (docstatus 2)
	  - dong tien VAO, vi lenh chi thi phai o cot tien ra
	"""
	from frappe.utils import add_days, nowdate

	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not _duoc_tu_choi():
		frappe.throw("Chỉ kế toán hoặc giám đốc mới khớp lệnh chi được.")
	d = frappe.get_doc(DT, ho_so)
	tien = flt(d.so_tien)
	n = max(1, min(cint(so_ngay) or 45, 180))
	moc = nowdate()
	ds = frappe.get_all(
		"Bank Transaction",
		filters=[
			["date", "between", [add_days(moc, -n), add_days(moc, 1)]],
			["withdrawal", ">", 0],
			["docstatus", "<", 2],
		],
		fields=["name", "date", "withdrawal", "description", "reference_number",
			"bank_account"],
		order_by="date desc", limit_page_length=400,
	)
	# Giu lai chinh giao dich cua phieu nay, de ke toan mo ra con thay minh
	# dang tro vao dong nao va doi sang dong khac duoc.
	da_chiem = _gd_da_chiem(tru_ho_so=d.name)
	tk = str(tu_khoa or "").strip().lower()
	ra = []
	for r in ds:
		if da_chiem.get(r["name"]):
			continue
		mo_ta = "%s %s" % (r.get("description") or "", r.get("reference_number") or "")
		if tk and tk not in mo_ta.lower():
			continue
		lech = abs(flt(r["withdrawal"]) - tien)
		r["lech"] = lech
		r["khop_noi_dung"] = 1 if khop_giao_dich(mo_ta, ma_do_soat(d)) else 0
		r["dung_tien"] = 1 if lech <= 1 else 0
		ra.append(r)
	# Xep theo: khop noi dung truoc, roi dung so tien, roi lech it nhat.
	ra.sort(key=lambda r: (-r["khop_noi_dung"], -r["dung_tien"], r["lech"]))
	return {
		"rows": ra[:60],
		"so_tien": tien,
		"ma_do": ma_do_soat(d),
		"noi_dung_ck": _noi_dung_dung(d),
		"ma_gd_dang_gan": d.ma_gd or "",
	}


@frappe.whitelist()
def khop_tay(ho_so=None, gd=None):
	"""Khop TAY mot dong tien ra vao phieu hoan tien, roi sinh chung tu.

	Duong nay di den DUNG cai dich cua doi soat tu dong, chi khac cho chon
	dong: o kia may doc noi dung chuyen khoan, o day nguoi nhin sao ke va
	chi. Nen no phai lam DU nhung viec kia lam, khong duoc lam thieu:

	  1. danh dau da doi soat va ghi ma giao dich
	  2. GHI XUONG NGAY truoc khi sinh chung tu
	  3. sinh chung tu, hong thi ghi loi len chinh phieu chu khong rollback
	     mat cai dau vua ghi

	Diem 2 va 3 la bai hoc cua phieu HT-2026-00899 ngay 19/08/2026: gop hai
	viec vao mot giao dich co so du lieu thi mot loi o buoc sinh chung tu se
	rollback xoa luon dau "da doi soat", va phieu nam mai o "Cho chi" du tien
	da ra khoi tai khoan.

	Ghi ten nguoi bam. Day la mot chu ky cua nguoi chu khong phai mot phep
	may, va ba thang sau ke toan phai tra loi duoc "ai bao dong nay la cua
	phieu nay".
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not _duoc_tu_choi():
		frappe.throw("Chỉ kế toán hoặc giám đốc mới khớp lệnh chi được.")
	if not frappe.db.exists(DT, ho_so):
		frappe.throw("Không tìm thấy phiếu hoàn tiền %s. Tải lại danh sách giúp em." % ho_so)
	d = frappe.get_doc(DT, ho_so)
	if d.trang_thai == "Da huy":
		frappe.throw("Phiếu %s đã bị từ chối nên không khớp lệnh chi được." % ho_so)
	if cint(d.da_doi_soat):
		frappe.throw(
			"Phiếu %s đã đối soát với giao dịch %s rồi. Khớp lại là ghi hai lần "
			"cho một lần tiền ra." % (ho_so, d.ma_gd or "(không rõ)")
		)

	gd = str(gd or "").strip()
	if not gd:
		frappe.throw("Chưa chọn dòng tiền ra nào.")
	g = frappe.db.get_value(
		"Bank Transaction", gd,
		["name", "date", "withdrawal", "docstatus", "description", "reference_number"],
		as_dict=True,
	)
	if not g:
		frappe.throw("Không có giao dịch ngân hàng %s. Tìm lại giúp em." % gd)
	if cint(g["docstatus"]) >= 2:
		frappe.throw("Giao dịch %s đã bị huỷ nên không dùng làm căn cứ được." % gd)
	if flt(g["withdrawal"]) <= 0:
		frappe.throw(
			"Giao dịch %s là tiền VÀO tài khoản, không phải lệnh chi. Lệnh chi "
			"phải nằm ở cột tiền ra. Chọn lại giúp em." % gd
		)
	chu_cu = _gd_da_chiem(tru_ho_so=d.name).get(gd)
	if chu_cu:
		frappe.throw(
			"Giao dịch %s đã được phiếu %s dùng rồi. Một lần tiền ra chỉ ứng "
			"với một phiếu hoàn." % (gd, chu_cu)
		)

	# Lech tien thi CANH BAO chu khong chan: ngan hang co the tru phi, hoac
	# ke toan chuyen lam hai lan. Nhung con so phai duoc noi ra thanh loi,
	# khong de nguoi bam xong roi moi thac mac.
	lech = flt(g["withdrawal"]) - flt(d.so_tien)

	frappe.db.set_value(DT, d.name, {
		"da_doi_soat": 1,
		"ma_gd": gd,
		"ngay_doi_soat": now_datetime(),
		"trang_thai": "Da doi soat",
		"loi_sinh_ct": "",
		"nguoi_khop_tay": frappe.session.user,
		"ngay_khop_tay": now_datetime(),
	})
	frappe.db.commit()

	sinh, loi = None, ""
	try:
		ho = frappe.get_doc(DT, d.name)
		kq = _sinh_chung_tu(ho)
		if not kq.get("bo_qua"):
			sinh = kq
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "hoan_tien: khop tay sinh chung tu loi %s" % d.name)
		loi = (
			"Tiền đã ra và đã khớp, nhưng máy chưa sinh được chứng từ: %s. "
			"Nhờ kế toán bấm lại nút Đối soát lệnh chi, còn không được thì báo "
			"anh Việt." % str(frappe.get_traceback()).strip().splitlines()[-1][:200]
		)
		try:
			frappe.db.set_value(DT, d.name, "loi_sinh_ct", loi)
			frappe.db.commit()
		except Exception:
			pass

	return {
		"ok": 1,
		"gd": gd,
		"so_tien_chuyen": flt(g["withdrawal"]),
		"so_tien_phieu": flt(d.so_tien),
		"lech": lech,
		"da_sinh": sinh,
		"loi": loi,
		"nhac": (
			("Đã khớp. Số tiền trên sao kê lệch %s đ so với phiếu, anh chị xem lại "
			 "giúp em." % "{:,.0f}".format(abs(lech)).replace(",", "."))
			if abs(lech) > 1 else "Đã khớp lệnh chi và sinh chứng từ."
		),
	}


@frappe.whitelist()
def tu_choi(ho_so, ly_do=None):
	"""Tu choi mot phieu hoan tien. Huy MEM, co ghi vet (QT-20).

	Anh Viet 18/08/2026: "bo sung nut Tu choi hoan tien kem form dien ly do
	bat buoc phong truong hop khach doi y hoac bang chung khong hop le".

	Ba cai chan o day, va deu chan o MAY CHU chu khong o man hinh:

	  ai bam    chi ke toan va giam doc, vi day la chan mot dong tien
	  luc nao   chi khi tien CHUA ra; da doi soat thi tu choi la noi doi so
	  ly do gi  bat buoc, va phai la mot cau chu khong phai mot dau cham
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not _duoc_tu_choi():
		frappe.throw(
			"Từ chối hoàn tiền là quyền của Kế toán và Giám đốc. Anh chị nhờ "
			"chị Dung hoặc anh Việt bấm giúp, hoặc báo em cấp thêm chức vụ "
			"trong màn Quản lý người dùng."
		)
	ly_do = (ly_do or "").strip()
	if len(ly_do) < 5:
		frappe.throw(
			"Phải ghi rõ lý do từ chối, ít nhất 5 ký tự. Câu này sẽ nằm lại "
			"trong hồ sơ và là thứ duy nhất giải thích được vì sao khách "
			"không nhận được tiền, nên anh chị viết đủ ý giúp em."
		)
	if not frappe.db.exists(DT, ho_so):
		frappe.throw("Không tìm thấy phiếu hoàn tiền %s. Anh chị mở lại danh sách giúp em." % ho_so)
	d = frappe.get_doc(DT, ho_so)
	if d.trang_thai == "Da huy":
		frappe.throw(
			"Phiếu này đã bị từ chối trước đó rồi%s. Không cần bấm lại."
			% ((" (lý do: %s)" % d.get("ly_do_tu_choi")) if d.get("ly_do_tu_choi") else "")
		)
	if cint(d.da_doi_soat) or d.phieu_chi:
		frappe.throw(
			"Tiền của phiếu này đã ra khỏi tài khoản công ty rồi, không từ "
			"chối được nữa. Muốn thu lại thì lập phiếu thu riêng và ghi rõ "
			"lý do, đừng sửa phiếu hoàn tiền cũ."
		)
	frappe.db.set_value(
		DT,
		ho_so,
		{
			"trang_thai": "Da huy",
			"ly_do_tu_choi": ly_do,
			"nguoi_tu_choi": frappe.session.user,
			"ngay_tu_choi": now_datetime(),
		},
	)
	# Ghi them mot dong vao so nhat ky cua chinh ho so, de nguoi doc sau
	# nay thay ca hai: truong da doi va mot dong ke chuyen.
	try:
		frappe.get_doc(DT, ho_so).add_comment(
			"Comment",
			"Từ chối hoàn tiền. Lý do: %s" % ly_do,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: ghi vet tu choi")
	frappe.db.commit()
	return {
		"ok": 1,
		"ho_so": ho_so,
		"ghi_chu": "Đã từ chối phiếu %s. Phiếu chuyển sang Đã huỷ và không "
		"còn được máy tự đối soát nữa." % ho_so,
	}


# ------------------------------------------------- ket thuc phieu hoan tien
#
# Anh Viet 19/08/2026: *"Thiet ke nut de dinh kem uy nhiem chi cho phieu
# hoan tien sau khi da doi soat -> chi Dung vao dinh kem file cho sales lay
# de gui khach -> hoan thanh -> may tu ghi so. Hien chua co luong ket thuc
# cho cai phieu nay."*
#
# Truoc hom nay phieu hoan tien di den "Da doi soat" roi dung lai o do mai
# mai. Muon ghi so, ke toan phai roi man /bep, vao Desk, tim dung Payment
# Entry giua hang tram phieu, dinh tep vao do roi bam Submit. Khong ai lam
# duoc viec do neu khong thuoc duong di, nen tren thuc te chung tu nam nhap
# vo thoi han.
#
# Ba ham duoi day dung lai doan duong ay ngay tren man hoan tien.


def _pe_cua(ho_so):
	"""Payment Entry cua ho so, kem docstatus. Nem loi neu thieu.

	Tach rieng vi ca ba ham ket thuc deu can dung mot phep kiem, va thong
	bao loi phai chi duong ra chu khong chi bao hong (QT-24).
	"""
	d = frappe.get_doc(DT, ho_so)
	if d.trang_thai == "Da huy":
		frappe.throw(
			"Phiếu %s đã huỷ hoặc bị từ chối nên không kết thúc được. Nếu tiền "
			"đã lỡ chuyển đi thì lập phiếu thu lại, đừng mở lại phiếu này." % ho_so
		)
	# Hỏi PHIẾU CHI trước, đối soát sau. Thứ tự này có lý do.
	#
	# Luồng hoàn tiền thường sinh phiếu chi TẠI bước đối soát, nên chưa đối
	# soát thì đúng là chưa có gì để đính. Nhưng luồng huỷ đơn Pancake sinh
	# sẵn hai phiếu nháp ngay lúc lập hồ sơ, trước khi tiền ra. Hỏi đối soát
	# trước thì kế toán cầm uỷ nhiệm chi thật trong tay vẫn bị chặn, mà chặn
	# xong cũng không ai gỡ được vì phiếu chi thì đã có sẵn rồi.
	#
	# Nên phép kiểm thật là "có phiếu chi hay không". Đối soát chỉ còn là câu
	# giải thích cho trường hợp chưa có.
	if not d.phieu_chi:
		if not cint(d.da_doi_soat):
			frappe.throw(
				"Phiếu %s chưa đối soát được với sao kê ngân hàng nên chưa có phiếu "
				"chi để đính uỷ nhiệm chi. Vào thẻ Giao dịch ngân hàng bấm Đối soát, "
				"hoặc gắn tay giao dịch tiền ra, rồi quay lại đây." % ho_so
			)
		frappe.throw(
			"Phiếu %s đã đối soát nhưng máy chưa sinh được phiếu chi. Xem dòng "
			"\"Lỗi khi sinh chứng từ\" ngay trên màn này để biết vướng ở đâu, "
			"báo em rồi hãy đính uỷ nhiệm chi." % ho_so
		)
	if not frappe.db.exists(PE, d.phieu_chi):
		frappe.throw(
			"Phiếu chi %s ghi trên hồ sơ nhưng không còn trên hệ thống. Dừng lại "
			"ở đây và báo em, đừng lập phiếu chi mới đè lên." % d.phieu_chi
		)
	return d, cint(frappe.db.get_value(PE, d.phieu_chi, "docstatus"))


def _dem_unc(ma_pe):
	"""So tep dang dinh tren mot Payment Entry. Dem THAT o may chu.

	QT-19: khong tin co unc_da_dinh nao tren man, cung khong tin truong
	ngay_dinh_unc. Tep co the bi go tren Desk sau khi da ghi vet, va luc do
	con so duy nhat dung la con so dem ngay luc hoi.
	"""
	try:
		return cint(
			frappe.db.count("File", {"attached_to_doctype": PE, "attached_to_name": ma_pe})
		)
	except Exception:
		return 0


DUOI_ANH = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".heic")


def _la_anh(ten):
	t = str(ten or "").lower()
	return any(t.endswith(d) for d in DUOI_ANH)


def _ds_unc(ma_pe):
	"""Danh sach tep UNC de Sales xem va tai ve gui khach.

	Tra kem ma File (tep) va co la_anh: tu 20/08/2026 man hinh ve anh UNC
	thanh hinh nho thay vi mot dong ten tep IMG_xxx.jpg (anh Viet: "Dung
	the hinh anh de render anh duoi dang Thumbnail nho, click vao thi
	phong to"). Anh di qua duong tai_unc chu khong qua /private/files, vi
	tep dinh vao Payment Entry ma Sales khong co quyen doc doctype do.
	"""
	if not ma_pe:
		return []
	try:
		return [
			{
				"url": f["file_url"], "ten": f["file_name"],
				"luc": str(f["creation"]), "tep": f["name"],
				"la_anh": 1 if _la_anh(f["file_name"] or f["file_url"]) else 0,
				"co": cint(f["file_size"]),
			}
			for f in frappe.get_all(
				"File",
				filters={"attached_to_doctype": PE, "attached_to_name": ma_pe},
				fields=["name", "file_url", "file_name", "creation", "file_size"],
				order_by="creation asc",
				limit_page_length=0,
			)
		]
	except Exception:
		return []


@frappe.whitelist()
def tai_unc(ho_so=None, tep=None, co="lon"):
	"""Ruot mot tep UNC, tra ve base64 de man hinh ve hinh va tai ve.

	Vi sao khong dua thang duong /private/files: tep UNC dinh vao PAYMENT
	ENTRY, ma Sales khong co quyen doc Payment Entry nen Frappe tra 403.
	Duong nay kiem quyen theo PHIEU HOAN TIEN - ai xem duoc phieu thi xem
	duoc UNC cua phieu do - roi tu doc tep ho.

	Chong doc chui (IDOR): tep phai dang dinh vao dung phieu chi cua ho so
	nay. Dua ma File cua phieu khac la bi tu choi, du ma do co that.

	co="nho" tra ve hinh thu nho ~360px cho luoi anh; "lon" tra nguyen
	ruot tep de phong to va tai ve.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not ho_so or not frappe.db.exists(DT, ho_so):
		frappe.throw("Không tìm thấy phiếu hoàn tiền %s. Tải lại danh sách giúp em." % ho_so)
	ma_pe = frappe.db.get_value(DT, ho_so, "phieu_chi")
	if not ma_pe:
		frappe.throw("Phiếu này chưa có phiếu chi nên chưa có uỷ nhiệm chi nào.")
	f = frappe.db.get_value(
		"File", {"name": tep, "attached_to_doctype": PE, "attached_to_name": ma_pe},
		["name", "file_name", "file_url"], as_dict=True,
	)
	if not f:
		frappe.throw(
			"Tệp này không nằm trên phiếu chi của phiếu hoàn tiền %s. Tải lại "
			"trang rồi bấm lại giúp em." % ho_so
		)
	doc_tep = frappe.get_doc("File", f.name)
	try:
		ruot = doc_tep.get_content()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: doc tep UNC")
		frappe.throw(
			"Tệp %s có trong sổ nhưng máy đọc không ra nội dung. Có thể tệp đã "
			"bị gỡ trên Desk; nhờ chị Dung đính lại giúp." % (f.file_name or tep)
		)
	if isinstance(ruot, str):
		ruot = ruot.encode("utf-8")

	mime = "application/octet-stream"
	ten_thap = str(f.file_name or f.file_url or "").lower()
	if _la_anh(ten_thap):
		mime = "image/" + ("jpeg" if ten_thap.endswith((".jpg", ".jpeg")) else ten_thap.rsplit(".", 1)[-1])
	elif ten_thap.endswith(".pdf"):
		mime = "application/pdf"

	if (co or "") == "nho" and _la_anh(ten_thap):
		# Hinh thu nho cho luoi anh: giu payload nhe de mo phieu khong cho
		# ca chuc MB anh chup man hinh e-banking.
		try:
			from io import BytesIO

			from PIL import Image

			im = Image.open(BytesIO(ruot))
			im.thumbnail((360, 360))
			if im.mode not in ("RGB", "L"):
				im = im.convert("RGB")
			ra = BytesIO()
			im.save(ra, format="JPEG", quality=80)
			ruot = ra.getvalue()
			mime = "image/jpeg"
		except Exception:
			# Khong nen duoc thi tra nguyen ban, cham hon nhung van xem duoc.
			pass

	return {
		"ok": 1, "ten": f.file_name or "uy-nhiem-chi",
		"mime": mime, "b64": base64.b64encode(ruot).decode("ascii"),
	}


@frappe.whitelist()
def dinh_unc(ho_so=None, ten=None, noi_dung=None):
	"""Chi Dung dinh uy nhiem chi vao phieu chi cua mot ho so hoan tien.

	KHONG ghi so o buoc nay. Dinh xong thi Sales tai tep ve gui khach, roi
	ke toan moi bam Hoan thanh. Xem ghi chu o dau muc nay ve vi sao hai
	nhip.

	Tep dinh vao PAYMENT ENTRY chu khong vao ho so, vi hook
	chan_thieu_uy_nhiem_chi dem tep tren Payment Entry, va vi ho so con
	dang giu anh bang chung cua Sales.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not _duoc_tu_choi():
		frappe.throw(
			"Chỉ kế toán hoặc giám đốc mới đính uỷ nhiệm chi được. Nhờ chị Dung "
			"đính giúp rồi anh chị tải về gửi khách."
		)
	if not frappe.db.exists(DT, ho_so):
		frappe.throw("Không tìm thấy phiếu hoàn tiền %s. Tải lại danh sách giúp em." % ho_so)

	d, ds_pe = _pe_cua(ho_so)
	if ds_pe >= 2:
		frappe.throw(
			"Phiếu chi %s đã bị huỷ nên đính thêm giấy tờ vào đó không còn ý "
			"nghĩa. Báo em để dựng lại chứng từ." % d.phieu_chi
		)

	ten = (ten or "").strip() or "uy-nhiem-chi.pdf"
	noi = (noi_dung or "").strip()
	if not noi:
		frappe.throw(
			"Chưa chọn tệp uỷ nhiệm chi. Tải UNC từ e-banking về máy rồi bấm "
			"Chọn tệp lại giúp em."
		)
	if "," in noi and noi[:5].lower() == "data:":
		noi = noi.split(",", 1)[1]

	# Kiem kich thuoc THAT sau khi giai ma, khong tin do dai chuoi tren man.
	try:
		so_byte = len(base64.b64decode(noi))
	except Exception:
		frappe.throw(
			"Tệp gửi lên bị hỏng giữa đường nên máy không đọc được. Chọn lại "
			"tệp và thử lần nữa giúp em."
		)
	if so_byte <= 0:
		frappe.throw("Tệp uỷ nhiệm chi rỗng. Kiểm lại tệp tải từ e-banking giúp em.")
	if so_byte > 12 * 1024 * 1024:
		frappe.throw(
			"Tệp uỷ nhiệm chi nặng %s MB, quá 12 MB nên máy không nhận. Xuất "
			"lại bản PDF hoặc chụp nhỏ hơn giúp em."
			% ("{:.1f}".format(so_byte / 1024.0 / 1024.0))
		)

	f = frappe.get_doc({
		"doctype": "File",
		"file_name": ten,
		"attached_to_doctype": PE,
		"attached_to_name": d.phieu_chi,
		"content": noi,
		"decode": True,
		"is_private": 1,
	})
	f.flags.ignore_permissions = True
	f.insert(ignore_permissions=True)

	frappe.db.set_value(DT, ho_so, {
		"nguoi_dinh_unc": frappe.session.user,
		"ngay_dinh_unc": now_datetime(),
	})
	try:
		frappe.get_doc(DT, ho_so).add_comment(
			"Comment", "Đính uỷ nhiệm chi %s vào phiếu chi %s." % (ten, d.phieu_chi)
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: ghi vet dinh UNC")
	frappe.db.commit()
	return {
		"ok": 1,
		"ho_so": ho_so,
		"phieu_chi": d.phieu_chi,
		"unc": _ds_unc(d.phieu_chi),
		"ghi_chu": "Đã đính %s vào phiếu chi %s. Sales tải tệp này gửi khách, "
		"xong thì bấm Hoàn thành để máy ghi sổ." % (ten, d.phieu_chi),
	}


@frappe.whitelist()
def hoan_thanh(ho_so=None):
	"""Ket thuc phieu: ghi so phieu chi va dong ho so.

	Day la cho DUY NHAT trong ca luong nay may tu bam Submit ho nguoi. Nen
	no chi chay khi ba dieu deu that o may chu: da doi soat, co phieu chi,
	va tren phieu chi co it nhat mot tep dinh kem. Ba dieu do deu doc lai
	tu co so du lieu chu khong nhan tu man hinh (QT-19).

	Lap lai duoc: phieu chi da ghi so roi thi khong ghi lan hai, chi dong
	ho so lai. Ke toan bam nham hai lan khong sinh ra hai but toan.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not _duoc_tu_choi():
		frappe.throw("Chỉ kế toán hoặc giám đốc mới kết thúc phiếu hoàn tiền được.")
	if not frappe.db.exists(DT, ho_so):
		frappe.throw("Không tìm thấy phiếu hoàn tiền %s. Tải lại danh sách giúp em." % ho_so)

	d, ds_pe = _pe_cua(ho_so)
	if ds_pe >= 2:
		frappe.throw(
			"Phiếu chi %s đã bị huỷ nên không ghi sổ được. Báo em để dựng lại "
			"chứng từ trước khi kết thúc phiếu." % d.phieu_chi
		)

	if not _dem_unc(d.phieu_chi):
		frappe.throw(
			"Phiếu chi %s chưa có uỷ nhiệm chi nào đính kèm nên chưa ghi sổ "
			"được. Dòng sao kê SePay không thay được UNC khi giải trình với cơ "
			"quan thuế. Bấm Đính uỷ nhiệm chi ở ngay trên rồi quay lại."
			% d.phieu_chi
		)

	da_ghi_san = ds_pe == 1
	if not da_ghi_san:
		pe = frappe.get_doc(PE, d.phieu_chi)
		pe.flags.ignore_permissions = True
		# Hook chan_thieu_uy_nhiem_chi van chay o day va van la hang rao
		# that: co tinh KHONG tat no di, vi day dung la truong hop no sinh
		# ra de canh.
		pe.submit()

	frappe.db.set_value(DT, ho_so, {
		"trang_thai": "Hoan thanh",
		"nguoi_hoan_thanh": frappe.session.user,
		"ngay_hoan_thanh": now_datetime(),
	})
	try:
		frappe.get_doc(DT, ho_so).add_comment(
			"Comment",
			"Kết thúc phiếu hoàn tiền. Phiếu chi %s %s."
			% (d.phieu_chi, "đã ghi sổ từ trước" if da_ghi_san else "vừa được ghi sổ"),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: ghi vet hoan thanh")
	frappe.db.commit()
	return {
		"ok": 1,
		"ho_so": ho_so,
		"phieu_chi": d.phieu_chi,
		"da_ghi_san": 1 if da_ghi_san else 0,
		"ghi_chu": (
			"Phiếu chi %s đã ghi sổ từ trước, em chỉ đóng hồ sơ lại." % d.phieu_chi
			if da_ghi_san
			else "Đã ghi sổ phiếu chi %s và đóng phiếu hoàn tiền %s."
			% (d.phieu_chi, ho_so)
		),
	}


# ---------------------------------------- hoá đơn điện tử của đơn gốc
#
# Anh Việt 20/08/2026: *"Hiển thị mã hóa đơn VAT: Truy xuất và hiển thị mã
# hóa đơn điện tử (M-Invoice) đã xuất cho đơn hàng gốc đó. Nút Liên kết trực
# tiếp: bấm vào sẽ mở thẳng tới chứng từ đó trên hệ thống M-invoice."*
#
# Khối này CHỈ ĐỌC và CHỈ mở liên kết. Tuyệt đối không phát hành, không ký,
# không huỷ, không sửa một tờ hoá đơn nào.
#
# Anh Việt dặn 13/08/2026 sau lần phải đi xoá tay hoá đơn bên m-invoice:
# *"những vấn đề liên quan đến hoá đơn điện tử gửi sang cơ quan thuế, rất
# nhạy cảm, khó sửa chữa"*. Nên ở đây chỉ có đường đọc, không có đường ghi.


def _mau_lien_ket_hddt():
	"""Mẫu đường dẫn tới một tờ hoá đơn bên M-Invoice.

	ĐỂ TRONG CÀI ĐẶT chứ không viết cứng, vì em KHÔNG biết chắc đường dẫn
	sâu của M-Invoice. Tra tài liệu của họ thì trang hướng dẫn lỗi máy chủ,
	còn trang tra cứu là ứng dụng JavaScript nên không đọc được đường dẫn từ
	mã nguồn. Đoán một đường dẫn rồi in ra nút bấm là đưa cho chị Dung một
	cái nút dẫn tới trang lỗi.

	Nên: chị Dung mở một tờ hoá đơn bên M-Invoice, chép đường dẫn trên thanh
	địa chỉ, dán vào Cài đặt và thay phần mã tờ hoá đơn bằng {id}. Từ đó nút
	này dẫn đúng tới từng tờ.

	Ba chỗ thay được: {host} {id} {so} {sobaomat}
	"""
	try:
		return (cfg().get("minvoice_mau_lien_ket") or "").strip()
	except Exception:
		return ""


@frappe.whitelist()
def ghi_hddt_thay_the(ma_phieu, so, ky_hieu=None):
	"""Nối mã hoá đơn THAY THẾ vào phiếu hoàn tiền VÀ vào đơn hàng gốc.

	Anh Việt 20/08/2026: *"ví dụ hoá đơn đã thay thế rồi thì em viết luồng
	automation để nối mã hoá đơn đã thay thế đó vào đơn hàng trước đó và vào
	phiếu hoàn tiền luôn được không?"*

	Ranh giới, cố ý và không thương lượng
	-------------------------------------
	Hàm này CHỈ GHI LẠI một con số người thật đã đọc bên M-Invoice. Nó không
	phát hành, không huỷ, không thay thế, không gửi gì sang cơ quan thuế.
	Anh Việt dặn 13/08/2026 sau lần phải đi xoá tay hoá đơn bên M-Invoice:
	*"những vấn đề liên quan đến hoá đơn điện tử gửi sang cơ quan thuế, rất
	nhạy cảm, khó sửa chữa"*. Việc thay thế vẫn nằm trong tay chị Dung.

	Automation ở đây là chỗ NỐI: ghi một lần trên phiếu hoàn tiền thì đơn
	hàng gốc, phiếu hoàn tiền và nhật ký đều có, thay vì chị Dung phải nhớ
	mở ba nơi. Đó đúng là phần máy làm được mà không đụng tới hoá đơn thật.
	"""
	_kiem_quyen()
	so = (str(so or "")).strip()
	if not so:
		frappe.throw(
			"Chưa nhập số hoá đơn thay thế. Mở tờ hoá đơn mới bên M-Invoice, "
			"chép số hoá đơn rồi dán vào ô này."
		)
	if len(so) > 30:
		frappe.throw("Số hoá đơn dài bất thường (%d ký tự). Kiểm lại xem có dán nhầm cả dòng không." % len(so))
	kh = (str(ky_hieu or "")).strip()

	d = frappe.get_doc(DT, ma_phieu)
	if not d.hoa_don or not frappe.db.exists(SI, d.hoa_don):
		frappe.throw(
			"Phiếu này chưa gắn đơn hàng gốc nên không có tờ hoá đơn nào để "
			"thay thế. Gắn đơn hàng cho phiếu trước đã."
		)
	cu_so = (frappe.db.get_value(SI, d.hoa_don, "custom_hddt_so") or "").strip()
	if cu_so and so == cu_so:
		frappe.throw(
			"Số vừa nhập trùng đúng số hoá đơn cũ (%s). Tờ thay thế phải mang "
			"số khác. Kiểm lại bên M-Invoice xem đã chép đúng tờ mới chưa." % cu_so
		)

	luc = now_datetime()
	frappe.db.set_value(DT, d.name, {
		"so_hddt_thay_the": so,
		"ky_hieu_hddt_thay_the": kh,
		"nguoi_ghi_thay_the": frappe.session.user,
		"ngay_ghi_thay_the": luc,
	}, update_modified=False)
	# Đơn hàng gốc: ghi cả mã phiếu đã ghi nhận, để từ đơn hàng lần ngược ra
	# được phiếu hoàn tiền chứ không phải đi tìm.
	frappe.db.set_value(SI, d.hoa_don, {
		"custom_hddt_thay_the": ("%s %s" % (kh, so)).strip(),
		"custom_hddt_thay_the_luc": luc,
		"custom_hddt_thay_the_phieu": d.name,
	}, update_modified=False)
	# Dấu vết trên chính đơn hàng. QT-20: không xoá gì, và mọi lần ghi đè
	# đều còn lại một dòng để đối chiếu.
	try:
		frappe.get_doc({
			"doctype": "Comment", "comment_type": "Info",
			"reference_doctype": SI, "reference_name": d.hoa_don,
			"content": (
				"Ghi nhận hoá đơn thay thế %s (ký hiệu %s) cho tờ cũ %s, "
				"từ phiếu hoàn tiền %s."
				% (so, kh or "chưa ghi", cu_so or "chưa ghi", d.name)
			),
		}).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hoan_tien: ghi vet hoa don thay the")
	frappe.db.commit()
	return {
		"ok": 1,
		"so": so,
		"ky_hieu": kh,
		"so_cu": cu_so,
		"don": d.hoa_don,
		"loi_nhan": "Đã nối %s vào đơn %s và vào phiếu %s." % (so, d.hoa_don, d.name),
		"hddt": _hddt_cua_don(d.hoa_don),
	}


@frappe.whitelist()
def go_hddt_thay_the(ma_phieu, ly_do):
	"""Gỡ mã hoá đơn thay thế đã ghi nhầm. Bắt buộc ghi lý do.

	Không xoá lặng lẽ: ô trống lại nhưng nhật ký vẫn giữ cả số cũ lẫn lý do
	gỡ, đúng QT-20.
	"""
	_kiem_quyen()
	ly_do = (str(ly_do or "")).strip()
	if not ly_do:
		frappe.throw("Phải ghi lý do gỡ thì người sau mới hiểu vì sao ô này trống lại.")
	d = frappe.get_doc(DT, ma_phieu)
	cu = (d.get("so_hddt_thay_the") or "").strip()
	if not cu:
		frappe.throw("Phiếu này chưa ghi hoá đơn thay thế nào, không có gì để gỡ.")
	frappe.db.set_value(DT, d.name, {
		"so_hddt_thay_the": "", "ky_hieu_hddt_thay_the": "",
	}, update_modified=False)
	if d.hoa_don and frappe.db.exists(SI, d.hoa_don):
		frappe.db.set_value(SI, d.hoa_don, {
			"custom_hddt_thay_the": "", "custom_hddt_thay_the_phieu": "",
		}, update_modified=False)
		try:
			frappe.get_doc({
				"doctype": "Comment", "comment_type": "Info",
				"reference_doctype": SI, "reference_name": d.hoa_don,
				"content": "Gỡ hoá đơn thay thế %s (phiếu %s). Lý do: %s" % (cu, d.name, ly_do),
			}).insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "hoan_tien: ghi vet go hoa don thay the")
	frappe.db.commit()
	return {"ok": 1, "loi_nhan": "Đã gỡ %s. Nhật ký trên đơn hàng vẫn giữ lại vết." % cu}


@frappe.whitelist()
def can_ghi_thay_the(so_ngay=90):
	"""Phiếu hoàn tiền có hoá đơn gốc mà CHƯA ghi tờ thay thế.

	Danh sách nhắc việc cho chị Dung: thay thế xong bên M-Invoice rồi thì
	còn một bước nối mã về đây, và bước đó rất dễ quên vì nó nằm ở phần mềm
	khác.
	"""
	_kiem_quyen()
	tu = add_days(nowdate(), -int(so_ngay or 90))
	ra = []
	for d in frappe.get_all(
		DT,
		filters={"creation": [">=", tu]},
		fields=["name", "hoa_don", "so_hddt", "so_hddt_thay_the", "trang_thai", "creation"],
		order_by="creation desc",
		limit_page_length=200,
	):
		if (d.get("so_hddt_thay_the") or "").strip():
			continue
		if not (d.get("so_hddt") or "").strip():
			continue
		ra.append({
			"phieu": d["name"], "don": d.get("hoa_don") or "",
			"so_hddt": (d.get("so_hddt") or "").strip(),
			"trang_thai": d.get("trang_thai") or "",
			"ngay": str(d.get("creation") or "")[:10],
		})
	return {
		"dong": ra,
		"tong": len(ra),
		"ghi_chu": (
			"" if ra else
			"Không còn phiếu nào chờ nối mã hoá đơn thay thế trong %d ngày gần đây." % int(so_ngay or 90)
		),
	}


def _hddt_cua_don(ma_don):
	"""Thông tin hoá đơn điện tử của một đơn, để màn hình hiện và mở liên kết."""
	if not ma_don:
		return None
	try:
		d = frappe.db.get_value(
			SI, ma_don,
			["custom_hddt_ky_hieu", "custom_hddt_so", "custom_hddt_trang_thai",
			 "custom_hddt_id", "custom_hddt_sobaomat",
			 "custom_hddt_thay_the", "custom_hddt_thay_the_luc"],
			as_dict=True,
		) or {}
	except Exception:
		# Trường có thể chưa có trên site cũ. Thiếu hoá đơn điện tử không
		# được phép làm hỏng cả màn phiếu hoàn tiền.
		frappe.log_error(frappe.get_traceback(), "hoan_tien: doc hoa don dien tu loi")
		return None

	so = str(d.get("custom_hddt_so") or "").strip()
	kh = (d.get("custom_hddt_ky_hieu") or "").strip()
	if not (so or kh):
		return None

	host = ""
	try:
		host = (cfg().get("minvoice_host") or "").strip().rstrip("/")
		if host and not host.startswith("http"):
			host = "https://" + host
	except Exception:
		host = ""

	lien_ket = ""
	mau = _mau_lien_ket_hddt()
	if mau and host:
		lien_ket = (
			mau.replace("{host}", host)
			.replace("{id}", str(d.get("custom_hddt_id") or ""))
			.replace("{so}", so)
			.replace("{sobaomat}", str(d.get("custom_hddt_sobaomat") or ""))
		)
	return {
		"ky_hieu": kh,
		"so": so,
		"ma": ("%s %s" % (kh, so)).strip(),
		"trang_thai": (d.get("custom_hddt_trang_thai") or "").strip(),
		"id": str(d.get("custom_hddt_id") or ""),
		"so_bao_mat": str(d.get("custom_hddt_sobaomat") or ""),
		"host": host,
		"lien_ket": lien_ket,
		# Chưa khai mẫu đường dẫn thì màn hình mở trang chủ M-Invoice và chép
		# sẵn mã tra cứu, vẫn dùng được ngay chứ không đứng chờ.
		"da_khai_mau": 1 if lien_ket else 0,
		# Tờ đã thay thế tờ này, nếu có ai ghi nhận. Đọc từ ĐƠN HÀNG chứ
		# không từ phiếu hoàn tiền: một đơn có thể có nhiều phiếu, nhưng chỉ
		# có một tờ hoá đơn đang có hiệu lực.
		"thay_the": (d.get("custom_hddt_thay_the") or "").strip(),
		"thay_the_luc": str(d.get("custom_hddt_thay_the_luc") or ""),
	}
