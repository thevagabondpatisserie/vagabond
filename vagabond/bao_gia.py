"""Phan he bao gia khach doanh nghiep, song ngu Viet - Anh.

Dung theo dung to Loan Anh dang gui khach (file VGB-PQ-2026-0011 anh Viet gui
ngay 14/08/2026): 9 muc, song ngu toan bo, menu co hinh mon va thong tin di
ung, bang bao gia tam tinh, dich vu them gia bang chu, timeline van hanh,
yeu cau van hanh, dieu khoan thanh toan, chinh sach huy, luu y, hai o ky.

Ba cho giu du lieu:
  - Bao Gia Thu Vien: mon thiet ke rieng va moi khoan phi (nhan cong, van
    chuyen, set up, gia cong khuon, thu banh), co hinh va song ngu, sua gia
    duoc. Anh Viet 14/08: *"phải lưu vào đâu để sau này thao tác nhanh"*.
  - Bao Gia Cai Dat: cau chu khung to, khai mot lan dung cho moi to.
  - vagabond.chon_mon: bang chon mon dung chung, luon kem hinh anh.
"""

import base64
import json
import re

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from vagabond.cong_no import (
	TEN_NGAN_HANG_DAY_DU,
	_chu_so_tien,
	_ngay_vn,
	_qr_data_uri,
	_tien_vn,
)

DT = "Bao Gia Ban Hang"
DT_TV = "Bao Gia Thu Vien"
DT_CD = "Bao Gia Cai Dat"

QUYEN_XEM = {
	"System Manager", "Sales User", "Sales Manager", "Accounts User",
	"Accounts Manager", "Purchase User", "Purchase Manager", "Bộ phận đặt hàng",
}
QUYEN_SUA = {
	"System Manager", "Sales User", "Sales Manager", "Accounts User",
	"Accounts Manager",
}

TRANG_THAI = [
	"Nháp", "Đã gửi khách", "Khách duyệt", "Khách từ chối",
	"Hết hiệu lực", "Đã lên hợp đồng",
]

CHIP_HIEU_LUC = [7, 15, 30, 45]
CHIP_VAT = [0, 8, 10]

# To da roi trang thai Nhap thi khach da cam ban do tren tay. Sua de len la
# xoa mat vat bang chung, nen tu day chi con mot duong: mo mot vong moi.
TT_KHONG_SUA_DE = {
	"Đã gửi khách", "Khách duyệt", "Khách từ chối", "Hết hiệu lực",
	"Đã lên hợp đồng",
}

# --------------------------------------------------------- phien ban 1A
#
# Anh Viet 15/08/2026 duyet phuong an 1A: moi vong thuong luong la MOT chung
# tu rieng tren cung doctype, danh so bang hau to -v2, -v3 dan vao ten to
# goc. Ban cu dong bang tuyet doi.
#
# Vi sao KHONG co truong "ban_moi_nhat" nhu ban phuong an ban dau: no la
# nguon su that thu hai, va no doi backfill cho cac to dang co tren he
# (cot Check them vao thi dong cu nhan 0, tuc bong nhien ca ba to that bi
# coi la ban cu). Dung "thay_the_boi con trong" cho ra dung cau tra loi do
# ma khong phai dung vao mot dong du lieu qua khu nao - dung luat anh chot
# ngay 13/08.
TRUONG_MOI = {
	"Bao Gia Ban Hang": [
		{
			"fieldname": "sec_phien_ban", "label": "Phiên bản thương lượng",
			"fieldtype": "Section Break", "insert_after": "ghi_chu_noi_bo",
			"collapsible": 1,
		},
		{
			"fieldname": "goc", "label": "Tờ gốc", "fieldtype": "Link",
			"options": DT, "insert_after": "sec_phien_ban", "read_only": 1,
			"description": "Tờ của vòng 1. Vòng 1 để trống.",
		},
		{
			"fieldname": "phien_ban", "label": "Vòng thứ", "fieldtype": "Int",
			"default": "1", "insert_after": "goc", "read_only": 1,
		},
		{
			"fieldname": "thay_the_boi", "label": "Đã bị thay bởi",
			"fieldtype": "Link", "options": DT, "insert_after": "phien_ban",
			"read_only": 1,
			"description": "Có giá trị nghĩa là tờ này đã đóng băng.",
		},
		{
			"fieldname": "ly_do_sua", "label": "Lý do mở vòng này",
			"fieldtype": "Small Text", "insert_after": "thay_the_boi",
			"read_only": 1,
		},
	]
}

F_PHIEN_BAN = ("goc", "phien_ban", "thay_the_boi", "ly_do_sua")

# --------------------------------------------------- mau in va phan loai
#
# Anh Viet 16/08/2026: *"Anh khong muon Sales phai vao trong to bao gia moi
# di chon mau. Hay chuyen thao tac nay ra ngay nut + (Lap bao gia moi)"*,
# va mau duoc chon phai dien san loi mo, dieu khoan, yeu cau van hanh theo
# dung van phong cua mau do.
#
# VI SAO KHONG DE RA DOCTYPE "Mau Bao Gia" MOI
# --------------------------------------------
# He DA co dung thu do roi: mot to bao gia mang co la_mau = 1, danh so
# rieng MAU-BG-, va ham tu_mau() da chep san cau chu sang to moi. De ra mot
# doctype nua la co hai nguon su that cho cung mot khai niem, va moi lan
# them truong vao to bao gia lai phai nho them ca ben kia.
#
# Cai con thieu chi la ba thu: mau chua mang theo BO CUC IN, chua mang
# theo PHAN LOAI, va he chua co mau nao san de bam ngay lan dau.
#
# Bo mau khoi dau khai TRONG MA NGUON chu khong gieo vao co so du lieu.
# Gieo vao CSDL thi site thu voi site that lech nhau, sua cau chu phai vao
# Desk, va khong qua duoc sau cong kiem truoc deploy - dung cai benh ma
# truong_tu_them.py sinh ra de chua.
MAU_IN = [
	{"ma": "", "ten": "Bản gốc", "ta": "Tờ đang dùng từ trước tới nay."},
	{"ma": "executive", "ten": "The Executive",
	 "ta": "Trang trọng, gọn, không kẻ ô. Hợp đơn B2B và khách doanh nghiệp."},
	{"ma": "lookbook", "ten": "The Lookbook",
	 "ta": "Kiểu tạp chí, có ảnh món, giá dồn xuống cuối. Hợp catering và sự kiện."},
	{"ma": "legal", "ten": "The Legal Addendum",
	 "ta": "Nặng điều khoản, không hình. Hợp hợp đồng khung và đơn nhiều ràng buộc."},
	{"ma": "heritage", "ten": "The Heritage",
	 "ta": "Viền thanh lịch, cổ điển. Hợp bánh thiết kế riêng và quà tặng."},
]

PHAN_LOAI = [
	{"ma": "", "ten": "Chưa phân loại", "mau_in": ""},
	{"ma": "b2b", "ten": "Thư báo giá B2B", "mau_in": "executive"},
	{"ma": "dn_ck", "ten": "Khách doanh nghiệp có chiết khấu", "mau_in": "executive"},
	{"ma": "catering", "ten": "Dịch vụ Catering và Sự kiện", "mau_in": "lookbook"},
	{"ma": "thiet_ke", "ten": "Bánh thiết kế riêng", "mau_in": "heritage"},
]

MA_MAU_IN = {x["ma"] for x in MAU_IN}
MA_PHAN_LOAI = {x["ma"] for x in PHAN_LOAI}

TRUONG_MAU = {
	"Bao Gia Ban Hang": [
		{
			"fieldname": "sec_mau_in", "label": "Mẫu in và phân loại",
			"fieldtype": "Section Break", "insert_after": "ten_mau",
		},
		{
			"fieldname": "phan_loai", "label": "Phân loại báo giá",
			"fieldtype": "Select", "insert_after": "sec_mau_in",
			"options": "\n".join(x["ma"] for x in PHAN_LOAI),
		},
		{
			"fieldname": "mau_in", "label": "Bố cục tờ in",
			"fieldtype": "Select", "insert_after": "phan_loai",
			"options": "\n".join(x["ma"] for x in MAU_IN),
			"description": "Để trống thì in bằng tờ gốc đang dùng.",
		},
		{
			"fieldname": "mo_ta_mau", "label": "Mô tả mẫu",
			"fieldtype": "Small Text", "insert_after": "mau_in",
			"description": "Chỉ có nghĩa trên tờ mẫu. Hiện ở bảng chọn khi "
						   "sales bấm nút lập báo giá mới.",
		},
	]
}

# ------------------------------------------------------------ email bao gia
#
# Ba thu duoi day deu KHAI TRONG CAI DAT chu khong chon cung trong ma nguon:
# dia chi gui, danh sach CC noi bo, va cac cau goi y cho o Loi nhan them.
# Nhan su doi, cau chu doi - anh Viet sua thang tren Desk, khong phai cho
# em deploy. Ma nguon chi giu bo mac dinh cho lan dau.
EMAIL_GUI_MAC_DINH = "sales@thevagabondpatisserie.com"
CC_NOI_BO_MAC_DINH = (
	"anhntl@thevagabondpatisserie.com",
	"vietnh@thevagabondpatisserie.com",
	"account@thevagabondpatisserie.com",
)
# {ngay} duoc app thay bang ngay het hieu luc CUA CHINH TO DANG MO. Bat go
# tay ngay thang la co ngay cau trong thu lech voi con so in tren to.
LOI_NHAN_MAU = (
	"Bên em còn giữ giá này tới hết ngày {ngay} ạ.",
	"Giá trên đã bao gồm phí giao hàng nội thành.",
	"Quý khách vui lòng chốt số lượng trước 3 ngày làm việc giúp bên em ạ.",
	"Bên em sẵn sàng gửi mẫu thử trước khi Quý khách quyết định ạ.",
	"Đơn giá trong báo giá đã bao gồm VAT.",
	"Bên em có thể điều chỉnh menu theo yêu cầu riêng của Quý khách ạ.",
)

# Cau goi y RIENG cho thu gui HOP DONG, khac bo cua bao gia vi hai buoc noi
# hai chuyen khac nhau: bao gia con thuong luong gia, hop dong da chot gia
# va chi con soat dieu khoan roi ky.
#
# Anh Viet 18/08/2026: *"em tao ra khoang 5 chip nhung loi nhan than thu
# thuong hay su dung nhat de sales chi viec lua chon chu khong phai go"*.
LOI_NHAN_HD_MAU = (
	"Anh chị xem giúp em phần Điều 2 rồi phản hồi trước thứ Sáu ạ.",
	"Anh chị ký đóng dấu rồi gửi lại bên em một bản scan giúp em ạ.",
	"Bên em đã đính kèm báo giá đã chốt làm Phụ lục 01 của Hợp đồng ạ.",
	"Sau khi nhận cọc đợt 1 bên em sẽ lên lịch sản xuất ngay ạ.",
	"Anh chị cần điều chỉnh chỗ nào thì báo em, bên em gửi lại bản mới ạ.",
	"Bản cứng bên em sẽ gửi kèm khi giao hàng để hai bên ký đối ạ.",
)

TRUONG_CAI_DAT = {
	"Bao Gia Cai Dat": [
		{
			"fieldname": "sec_email_bg", "label": "Email báo giá",
			"fieldtype": "Section Break", "insert_after": "moc_mau",
		},
		{
			"fieldname": "email_gui", "label": "Địa chỉ gửi báo giá",
			"fieldtype": "Data", "insert_after": "sec_email_bg",
			"default": EMAIL_GUI_MAC_DINH,
			"description": "Phải là một Tài khoản Email đang bật gửi đi. "
						   "Chưa có thì hệ tự dùng hộp thư mặc định.",
		},
		{
			"fieldname": "cc_noi_bo", "label": "CC nội bộ",
			"fieldtype": "Small Text", "insert_after": "email_gui",
			"default": "\n".join(CC_NOI_BO_MAC_DINH),
			"description": "Mỗi dòng một địa chỉ. Được CC vào mọi thư báo giá.",
		},
		{
			"fieldname": "loi_nhan_mau", "label": "Câu gợi ý cho Lời nhắn thêm",
			"fieldtype": "Small Text", "insert_after": "cc_noi_bo",
			"default": "\n".join(LOI_NHAN_MAU),
			"description": "Mỗi dòng một câu, hiện thành chip bấm nhanh. "
						   "Viết {ngay} thì app thay bằng ngày hết hiệu lực.",
		},
		{
			"fieldname": "loi_nhan_hd_mau",
			"label": "Câu gợi ý cho thư gửi Hợp đồng",
			"fieldtype": "Small Text", "insert_after": "loi_nhan_mau",
			"default": "\n".join(LOI_NHAN_HD_MAU),
			"description": "Mỗi dòng một câu, hiện thành chip bấm nhanh ở "
						   "bước gửi hợp đồng. Khác bộ câu của báo giá.",
		},
	]
}

# Cau chu mac dinh, dung khi Bao Gia Cai Dat chua duoc khai.
MAC_DINH = {
	"loi_mo_vi": (
		"Từ năm 2015, The Vagabond Pâtisserie làm bánh thủ công với nguyên liệu "
		"cao cấp, trong đó có bơ AOP Échiré vùng Charentes-Poitou, Pháp. Mọi món "
		"trong thực đơn catering đều giữ đúng tiêu chuẩn và sự tỉ mỉ đó."
	),
	"loi_mo_en": (
		"Since 2015, The Vagabond Pâtisserie has been crafting artisan pastries "
		"with premium ingredients, including AOP Échiré butter from "
		"Charentes-Poitou, France. Every item in our catering menu reflects the "
		"same dedication to quality and craftsmanship that defines our patisserie."
	),
	"thanh_toan_vi": (
		"Đặt cọc 50% khi ký xác nhận báo giá.\n"
		"Thanh toán 50% còn lại trong vòng 3 ngày làm việc sau khi bàn giao.\n"
		"Phương thức thanh toán: chuyển khoản ngân hàng."
	),
	"thanh_toan_en": (
		"A 50% deposit is required upon confirmation.\n"
		"The remaining 50% is due within 3 business days after delivery.\n"
		"Payment method: bank transfer."
	),
	"yeu_cau_vi": (
		"Bàn giao khu vực chuẩn bị và khu vực trưng bày bánh 2 tiếng trước khi "
		"sự kiện bắt đầu.\n"
		"Mặt bằng setup tối thiểu: 2m x 3m cho khu vực trưng bày.\n"
		"Lối đi cho xe giao hàng và thang máy (nếu venue ở tầng cao)."
	),
	"yeu_cau_en": (
		"Preparation and display area must be handed over 2 hours before the "
		"event.\nMinimum display area: 2m x 3m.\n"
		"Vehicle access and elevator required if venue is on upper floors."
	),
	"chinh_sach_huy_vi": (
		"Huỷ trước 7 ngày: hoàn 100% tiền cọc.\n"
		"Huỷ trong vòng 3 tới 7 ngày: hoàn 50% tiền cọc.\n"
		"Huỷ trong vòng 3 ngày: không hoàn cọc.\n"
		"Thay đổi số lượng: chấp nhận tăng giảm 10% nếu báo trước 3 ngày làm việc.\n"
		"Thay đổi menu: chấp nhận nếu báo trước 7 ngày làm việc, sau đó sẽ báo giá riêng."
	),
	"chinh_sach_huy_en": (
		"Cancellation 7+ days prior: 100% deposit refund.\n"
		"Cancellation 3 to 7 days prior: 50% deposit refund.\n"
		"Cancellation within 3 days: no refund.\n"
		"Quantity changes: 10% accepted if notified 3 business days prior.\n"
		"Menu changes accepted if notified 7 business days prior; later changes "
		"will be quoted separately."
	),
	"luu_y_vi": (
		"Linh hoạt: menu có thể điều chỉnh theo yêu cầu; phục vụ được thực đơn "
		"riêng cho khách dị ứng hoặc ăn kiêng nếu báo trước.\n"
		"Ràng buộc: giá có thể thay đổi tuỳ số lượng cuối cùng. Giá dựa trên giá "
		"nguyên liệu thị trường hiện tại; nếu có biến động lớn, Vagabond sẽ thông "
		"báo và thương lượng lại."
	),
	"luu_y_en": (
		"Flexible: menu can be adjusted upon request; special dietary or allergy "
		"menus available upon prior notice.\n"
		"Binding: prices may vary depending on final count. Prices are based on "
		"current market ingredient costs; in case of significant fluctuations, "
		"Vagabond will notify and renegotiate."
	),
	"ten_ban": "CÔNG TY TNHH PATISSERIE VAGABOND",
	"mst_ban": "0318561568",
	"dia_chi_ban": "9 Trần Cao Vân, Phường Sài Gòn, TP.HCM",
	"web_ban": "www.thevagabondpatisserie.com",
	"dai_dien_ban": "",
	"chuc_vu_ban": "",
	"dt_ban": "",
	"email_ban": "",
	# Nguoi KY hop dong cua Ben B, khac han bon o phia tren. Anh Viet
	# 18/08/2026: *"hien em dang lay thong tin email va so dien thoai cua
	# Loan Anh gan cho anh la sao"*. Khai mot lan o day, moi hop dong sau
	# tu dien.
	"nguoi_ky_ban": "",
	"chuc_vu_ky_ban": "Giám đốc",
	"dt_ky_ban": "",
	"email_ky_ban": "",
}

# Bo mau khoi dau. Moi mau chi khai NHUNG O NO MUON DOI so voi to trang;
# o nao khong khai thi lay theo Cai dat bao gia nhu cu. Van phong tung mau
# khac nhau that su, khong phai doi mot chu cho co.
MAU_GOC = {
	"b2b": {
		"ten_mau": "Thư báo giá B2B",
		"mo_ta_mau": "Đơn hàng sỉ, giao nhiều đợt. Điều khoản gọn, không có phần sự kiện.",
		"phan_loai": "b2b", "mau_in": "executive",
		"ten": "Báo giá bánh sỉ",
		"hieu_luc_ngay": 30, "dat_coc_pt": 30,
		"thanh_toan": (
			"Đặt cọc 30% khi xác nhận đơn hàng.\n"
			"Thanh toán phần còn lại trong vòng 15 ngày kể từ ngày giao hàng cuối.\n"
			"Phương thức thanh toán: chuyển khoản ngân hàng.\n"
			"Xuất hoá đơn giá trị gia tăng theo từng đợt giao."
		),
		"yeu_cau_vi": (
			"Đặt hàng trước tối thiểu 07 ngày làm việc cho mỗi đợt giao.\n"
			"Địa điểm nhận hàng có lối đi cho xe tải nhẹ.\n"
			"Bên mua cử người nhận hàng và ký biên bản bàn giao từng đợt."
		),
		"chinh_sach_huy_vi": (
			"Huỷ đơn trước 07 ngày so với ngày giao: hoàn 100% tiền cọc.\n"
			"Huỷ trong vòng 07 ngày: không hoàn cọc do nguyên liệu đã nhập.\n"
			"Điều chỉnh số lượng: chấp nhận tăng giảm 15% nếu báo trước 05 ngày làm việc."
		),
	},
	"dn_ck": {
		"ten_mau": "Khách doanh nghiệp có chiết khấu",
		"mo_ta_mau": "Quà tặng doanh nghiệp số lượng lớn. Có bậc chiết khấu và mốc chốt số lượng.",
		"phan_loai": "dn_ck", "mau_in": "executive",
		"ten": "Báo giá quà tặng doanh nghiệp",
		"hieu_luc_ngay": 15, "dat_coc_pt": 50, "chiet_khau_pt": 10,
		"thanh_toan": (
			"Đặt cọc 50% khi chốt số lượng.\n"
			"Thanh toán 50% còn lại trước ngày giao hàng 03 ngày làm việc.\n"
			"Mức chiết khấu trên áp dụng cho số lượng đã chốt; số lượng giảm "
			"quá 20% thì hai bên thống nhất lại mức chiết khấu.\n"
			"Phương thức thanh toán: chuyển khoản ngân hàng."
		),
		"yeu_cau_vi": (
			"Chốt số lượng cuối cùng trước ngày giao hàng ít nhất 10 ngày.\n"
			"Cung cấp logo dạng vector nếu có in ấn riêng trên bao bì.\n"
			"Danh sách địa điểm giao gửi trước 05 ngày làm việc."
		),
		"chinh_sach_huy_vi": (
			"Huỷ trước 10 ngày: hoàn 100% tiền cọc.\n"
			"Huỷ trong vòng 05 tới 10 ngày: hoàn 50% tiền cọc.\n"
			"Huỷ trong vòng 05 ngày: không hoàn cọc.\n"
			"Bao bì đã in riêng theo yêu cầu không hoàn tiền trong mọi trường hợp."
		),
	},
	"catering": {
		"ten_mau": "Dịch vụ Catering và Sự kiện",
		"mo_ta_mau": "Teabreak, tiệc, sự kiện. Có yêu cầu mặt bằng và mốc vận hành tại chỗ.",
		"phan_loai": "catering", "mau_in": "lookbook",
		"ten": "Báo giá teabreak và sự kiện",
		"hieu_luc_ngay": 15, "dat_coc_pt": 50,
		"thanh_toan": (
			"Đặt cọc 50% khi ký xác nhận báo giá.\n"
			"Thanh toán 50% còn lại trong vòng 03 ngày làm việc sau khi bàn giao.\n"
			"Phương thức thanh toán: chuyển khoản ngân hàng."
		),
		"yeu_cau_vi": (
			"Bàn giao khu vực chuẩn bị và khu vực trưng bày 02 tiếng trước khi "
			"sự kiện bắt đầu.\n"
			"Mặt bằng setup tối thiểu 2m x 3m cho khu vực trưng bày.\n"
			"Có nguồn điện 220V trong bán kính 5m nếu cần giữ nóng hoặc giữ lạnh.\n"
			"Lối đi cho xe giao hàng và thang máy nếu venue ở tầng cao.\n"
			"Bên mua xác nhận số khách chính thức trước 03 ngày làm việc."
		),
		"chinh_sach_huy_vi": (
			"Huỷ trước 07 ngày: hoàn 100% tiền cọc.\n"
			"Huỷ trong vòng 03 tới 07 ngày: hoàn 50% tiền cọc.\n"
			"Huỷ trong vòng 03 ngày: không hoàn cọc.\n"
			"Thay đổi số lượng: chấp nhận tăng giảm 10% nếu báo trước 03 ngày làm việc.\n"
			"Thay đổi menu: chấp nhận nếu báo trước 07 ngày làm việc."
		),
	},
	"thiet_ke": {
		"ten_mau": "Bánh thiết kế riêng",
		"mo_ta_mau": "Bánh cưới, bánh sự kiện làm riêng. Có mốc duyệt mẫu và lịch thử bánh.",
		"phan_loai": "thiet_ke", "mau_in": "heritage",
		"ten": "Báo giá bánh thiết kế riêng",
		"hieu_luc_ngay": 30, "dat_coc_pt": 50,
		"thanh_toan": (
			"Đặt cọc 50% khi duyệt bản thiết kế.\n"
			"Thanh toán 50% còn lại trước ngày giao 03 ngày làm việc.\n"
			"Phí thiết kế và phí gia công khuôn riêng không hoàn lại sau khi "
			"bản vẽ đã được duyệt.\n"
			"Phương thức thanh toán: chuyển khoản ngân hàng."
		),
		"yeu_cau_vi": (
			"Duyệt bản vẽ thiết kế trước ngày giao ít nhất 14 ngày.\n"
			"Mỗi bản thiết kế được chỉnh sửa tối đa 02 lần không tính phí.\n"
			"Lịch thử bánh đăng ký trước 07 ngày.\n"
			"Bánh nhiều tầng cần mặt bàn phẳng và phòng có điều hoà tại điểm nhận."
		),
		"chinh_sach_huy_vi": (
			"Huỷ trước khi duyệt bản vẽ: hoàn 100% tiền cọc.\n"
			"Huỷ sau khi duyệt bản vẽ: không hoàn phần phí thiết kế và gia công khuôn.\n"
			"Huỷ trong vòng 07 ngày trước ngày giao: không hoàn cọc.\n"
			"Đổi thiết kế sau khi đã duyệt sẽ được báo giá riêng."
		),
	},
}

MOC_MAC_DINH = [
	{
		"moc_vi": "T-10 ngày", "moc_en": "T-10 days",
		"noi_dung_vi": "Hoàn thiện thiết kế và sản xuất khuôn bánh.",
		"noi_dung_en": "Finalize mold design and production.",
		"trach_nhiem": "Vagabond / Seller",
	},
	{
		"moc_vi": "Trước ngày thử bánh ít nhất 07 ngày",
		"moc_en": "At least 07 days before the sample tasting",
		"noi_dung_vi": "Khách hàng đăng ký lịch thử bánh để Vagabond chuẩn bị mẫu thử.",
		"noi_dung_en": "The Buyer schedules the sample tasting so Vagabond can prepare samples.",
		"trach_nhiem": "Bên mua / Buyer",
	},
	{
		"moc_vi": "Theo lịch đã thống nhất", "moc_en": "Per agreed schedule",
		"noi_dung_vi": "Bàn giao hàng theo số đợt hai bên thống nhất.",
		"noi_dung_en": "Deliver in the number of batches agreed by both parties.",
		"trach_nhiem": "Vagabond / Seller",
	},
]


# ------------------------------------------------------------------- quyen


def _quyen(sua=False):
	vai = set(frappe.get_roles())
	if sua:
		if not QUYEN_SUA & vai:
			frappe.throw("Chỉ bộ phận kinh doanh và kế toán được lập hoặc sửa báo giá.")
		return
	if not QUYEN_XEM & vai:
		frappe.throw("Không có quyền xem báo giá.")


def _cd():
	"""Cai dat bao gia, tra ve dict da chen san mac dinh cho o con trong."""
	try:
		d = frappe.get_single(DT_CD).as_dict()
	except Exception:
		d = {}
	ra = {}
	for k, v in MAC_DINH.items():
		ra[k] = (d.get(k) or "").strip() or v
	ra["moc_mau"] = [
		{
			"moc_vi": m.get("moc_vi"), "moc_en": m.get("moc_en"),
			"noi_dung_vi": m.get("noi_dung_vi"), "noi_dung_en": m.get("noi_dung_en"),
			"trach_nhiem": m.get("trach_nhiem"),
		}
		for m in (d.get("moc_mau") or [])
	] or MOC_MAC_DINH
	ra["ngan_hang_vi"] = (d.get("ngan_hang_vi") or "").strip()
	ra["ngan_hang_en"] = (d.get("ngan_hang_en") or "").strip()
	ra["email_gui"] = (d.get("email_gui") or "").strip() or EMAIL_GUI_MAC_DINH
	ra["cc_noi_bo"] = _tach_dong(d.get("cc_noi_bo")) or list(CC_NOI_BO_MAC_DINH)
	ra["loi_nhan_mau"] = _tach_dong(d.get("loi_nhan_mau")) or list(LOI_NHAN_MAU)
	ra["loi_nhan_hd_mau"] = _tach_dong(d.get("loi_nhan_hd_mau")) or list(LOI_NHAN_HD_MAU)
	return ra


def _tach_dong(s):
	"""Chuoi nhieu dong thanh danh sach da bo dong trong. THUAN."""
	return [x.strip() for x in str(s or "").splitlines() if x.strip()]


# Du de chan cac loi go that: thieu @, thieu cham, co khoang trang. Khong
# co gang kiem dung chuan RFC - kiem chat qua thi chan ca dia chi hop le.
_RE_EMAIL = re.compile(r"^[^@\s,;]+@[^@\s,;]+\.[A-Za-z]{2,}$")


def _tach_email(chuoi):
	"""Chuoi nhieu email thanh (danh sach dung, danh sach sai). THUAN.

	Nhan dau phay lan dau cham phay lan xuong dong, vi Loan Anh chep dia chi
	tu email cua khach sang thi dinh du kieu dau. Bo trung, khong phan biet
	hoa thuong, nhung GIU nguyen cach viet dau tien de thu nhin tu te.
	"""
	tho = re.split(r"[,;\n]+", str(chuoi or ""))
	dung, sai, da_co = [], [], set()
	for x in tho:
		e = x.strip().strip("<>")
		if not e:
			continue
		if not _RE_EMAIL.match(e):
			sai.append(e)
		elif e.lower() not in da_co:
			da_co.add(e.lower())
			dung.append(e)
	return dung, sai


# ------------------------------------------------------------------- doc so


# ------------------------------------------------------------- tach thue
#
# Anh Viet 18/08/2026: *"phan thue cua cac mat hang tren bao gia va tren hop
# dong lam sao de co the tach ra duoc dong thue rieng vi cac mon cua
# Vagabond la luon bao gom thue nen can phai chia nguoc ra. Nhieu khach ho
# yeu cau so tien truoc thue va so tien sau thue, so tien thue. Dong thoi
# khi chiet khau thi phai chiet khau tren so tien truoc thue, roi moi tinh
# thue vao."*
#
# MOT DIEU VE THU TU CAN NOI RO
# Voi chiet khau tinh bang PHAN TRAM, tinh tren gia gom thue hay tren gia
# truoc thue deu ra CUNG mot tong, vi ca hai deu la phep nhan. Tong gom VAT
# 8% la 10.800.000 chiet khau 10%: duong nao cung ra hang 9.000.000, thue
# 720.000, tong 9.720.000. Cai doi khong phai so tien ma la TO IN RA CO CHO
# GHI ba con so do hay khong.
#
# Cho thu tu SAI THAT nam o day: chiet khau cua ca to phai duoc chia nguoc
# ve tung dong TRUOC khi tach thue tung dong. Khong lam buoc do thi tien
# thue duoc tinh tren nen chua tru chiet khau, tuc khai thue cao hon thuc
# thu, ma nhin con so van thay hop ly.


# Hai kieu chiet khau. Chuoi luu trong co so du lieu KHONG DAU, giong het
# nep cua phan he Khuyen mai (xem khuyen_mai.py), de hai noi cung mot ngon
# ngu va sau nay gom lai duoc.
CK_PT = "Phan tram"
CK_TIEN = "So tien"

# ------------------------------------------------------- cach tinh thue
#
# Su co 19/08/2026, to VGB-PQ-2026-0008 cua Loan Anh. To hien tren app la
# "Thue GTGT 8% = 2.566.929 d, tong 34.653.539 d", nhung to PDF gui khach
# lai in "Thue GTGT 0% / VAT 0" trong khi dong tong van la 34.653.539 d.
# Mot to bao gia ma cac dong khong cong lai ra dung dong tong.
#
# Chuoi nhan qua, doc tu du lieu that chu khong doan:
#
#   1. moi() khong tra ve o kieu_thue. App vi the khong co gia tri nao de
#      gui len.
#   2. _do_vao lam `doc.set(f, d.get(f) or None)` cho ca F_CHU, nen
#      kieu_thue thanh None.
#   3. _tinh doc None la "" nen chay NHANH CU: thue 8% tren tong. Ra
#      2.566.929 va 34.653.539.
#   4. Luc INSERT, cot kieu_thue trong doctype co "default": "Theo tung
#      dong", nen MariaDB dien gia tri do vao. To duoc GHI o mot che do
#      khac han che do vua dung de TINH.
#   5. Luc in, tom_tat_thue doc kieu_thue tu o dia (da la "Theo tung
#      dong") roi cong lai theo tung dong - moi dong 0% - ra 0.
#
# Va lan luu ke tiep thi app da co kieu_thue tu may chu gui xuong, nen no
# gui len "Theo tung dong" that, _tinh chay nhanh moi, va TIEN THUE BIEN
# MAT KHOI TONG. Do dung la to VGB-PQ-2026-0007: 34.653.539 tut ve
# 32.086.610 ma khong ai bam gi.
#
# Hai cai chan tu day tro di. Mot, mot cach doc duy nhat qua _kieu_thue(),
# de tinh va in khong bao gio doc khac nhau. Hai, _do_vao luon ghi mot gia
# tri RO RANG xuong o nay, va doctype khong con "default" - de khong con
# duong nao cho co so du lieu tu quyet che do thay minh.
KT_TO = "Theo tờ (cũ)"
KT_DONG = "Theo từng dòng"

# To moi lap tu app di theo cach moi. To da nam tren he ma de trong o nay
# thi doc la cach cu, dung y nhu truoc khi co tinh nang.
KT_MAC_DINH_TO_MOI = KT_DONG


def _kieu_thue(doc):
	"""Cach tinh thue cua mot to. MOT cach doc duy nhat cho ca he.

	De trong doc la cach cu. Chuoi la doc cung la cach cu, vi mot gia tri
	khong hieu duoc khong duoc phep doi cach tinh tien cua mot to da gui
	khach.
	"""
	v = str((doc.get("kieu_thue") if hasattr(doc, "get") else "") or "").strip()
	return KT_DONG if v == KT_DONG else KT_TO


def tien_chiet_khau(goc, kieu, gia_tri):
	"""So tien chiet khau tren mot goc. THUAN.

	Anh Viet chot 19/08/2026 sau yeu cau cua Loan Anh: chiet khau phai
	nhap duoc CA hai kieu, theo phan tram va theo so tien.

	kieu rong thi hieu la phan tram. Day la cho quan trong nhat cua ham
	nay: moi to bao gia cu deu co o kieu de trong, va chung phai chay y
	nguyen nhu truoc, khong lech mot dong.

	Ba chan cung:
	  - khong bao gio am
	  - khong bao gio vuot qua goc, du nguoi go 200% hay go so tien lon hon
	    ca to. Cho vuot la to bao gia ra so am.
	  - lam tron ve dong
	"""
	g = flt(goc)
	v = flt(gia_tri)
	if g <= 0 or v <= 0:
		return 0.0
	if (kieu or "") == CK_TIEN:
		return float(min(round(v, 0), round(g, 0)))
	return float(min(round(g * v / 100.0, 0), round(g, 0)))


def phan_bo_chiet_khau(cac_tien, tong_ck):
	"""Chia chiet khau cua ca to ve tung dong theo ti le. THUAN.

	Dong CUOI nhan phan du, nen tong cac phan chia LUON bang dung tong_ck,
	khong bao gio lech mot dong vi lam tron.
	"""
	tien = [flt(x) for x in (cac_tien or [])]
	tong = sum(tien)
	ck = flt(tong_ck)
	if not tien:
		return []
	if tong <= 0 or ck <= 0:
		return [0.0] * len(tien)
	ra, da = [], 0.0
	for i, t in enumerate(tien):
		x = (ck - da) if i == len(tien) - 1 else round(ck * t / tong, 0)
		ra.append(x)
		da += x
	return ra


def tach_thue(nen, pt, da_gom):
	"""Tach mot so tien thanh (tien hang, tien thue). THUAN.

	da_gom True nghia la so dua vao DA gom thue, phai chia nguoc ra bang
	cong thuc thue = nen x pt / (100 + pt).

	Phan du cua phep lam tron luon roi vao TIEN THUE chu khong roi vao tien
	hang. Ly do: con so neo la tong da gom thue - do la so khach tra va la
	so da in tren to bao gia khach cam. Tien hang cong tien thue phai bang
	dung con so neo do, khong duoc lech mot dong.
	"""
	n = flt(nen)
	p = flt(pt)
	if p <= 0:
		return (n, 0.0)
	if da_gom:
		hang = round(n * 100.0 / (100.0 + p), 0)
		return (hang, n - hang)
	return (n, round(n * p / 100.0, 0))


def bang_thue(dong, ck_to=0, phi_giao=0, phi_giao_pt=0, da_gom=1):
	"""Tach thue cho ca to bao gia. THUAN, khong doc co so du lieu.

	Phep bat bien: tien_hang + tien_thue phai bang dung tong_cong. Ca kiem
	soi dung cho nay, vi do la cho de vo nhat khi lam tron.
	"""
	ds = list(dong or [])
	tien = [flt(x.get("thanh_tien")) for x in ds]
	tru = phan_bo_chiet_khau(tien, ck_to)
	chi_tiet, theo_muc = [], {}
	t_hang = t_thue = 0.0
	for i, x in enumerate(ds):
		nen = tien[i] - tru[i]
		pt = flt(x.get("thue_pt"))
		hang, thue = tach_thue(nen, pt, da_gom)
		chi_tiet.append({"thue_pt": pt, "nen": nen, "tien_hang": hang, "tien_thue": thue})
		g = theo_muc.setdefault(pt, {"thue_pt": pt, "tien_hang": 0.0, "tien_thue": 0.0})
		g["tien_hang"] += hang
		g["tien_thue"] += thue
		t_hang += hang
		t_thue += thue
	# Phi giao la truong cua TO chu khong phai mot dong, nen di rieng va co
	# muc thue rieng. Chiet khau to khong an vao phi giao.
	pg = flt(phi_giao)
	if pg:
		ppt = flt(phi_giao_pt)
		hang, thue = tach_thue(pg, ppt, da_gom)
		g = theo_muc.setdefault(ppt, {"thue_pt": ppt, "tien_hang": 0.0, "tien_thue": 0.0})
		g["tien_hang"] += hang
		g["tien_thue"] += thue
		t_hang += hang
		t_thue += thue
	return {
		"chi_tiet": chi_tiet,
		"theo_muc": [theo_muc[k] for k in sorted(theo_muc)],
		"tien_hang": t_hang,
		"tien_thue": t_thue,
		"tong_cong": t_hang + t_thue,
	}


def _tinh(doc):
	"""Cong lai toan bo con so tren to bao gia, tinh o may chu.

	Don gia tren to Loan Anh gui khach la gia DA BAO GOM VAT (nhu file Elle
	ghi ro "Đơn giá (đã bao gồm VAT)"). Nen mac dinh khong cong them thue
	len tong; tat o gia_da_gom_vat thi moi cong.
	"""
	tam = 0.0
	for d in doc.get("dong") or []:
		d.so_luong = flt(d.so_luong)
		d.don_gia = flt(d.don_gia)
		d.chiet_khau = flt(d.chiet_khau)
		# Chiet khau cua RIENG dong nay. To cu de trong o kieu_ck thi doc
		# la phan tram, dung y nhu truoc khi co tinh nang nay.
		goc_dong = round(d.so_luong * d.don_gia, 0)
		d.ck_tien_dong = tien_chiet_khau(goc_dong, d.get("kieu_ck"), d.chiet_khau)
		d.thanh_tien = goc_dong - d.ck_tien_dong
		tam += d.thanh_tien
	doc.tam_tinh = tam
	doc.chiet_khau_tien = tien_chiet_khau(tam, doc.get("kieu_ck"), doc.chiet_khau_pt)
	sau_ck = tam - doc.chiet_khau_tien

	# NHANH MOI: thue khai theo tung dong, tach ra tien hang va tien thue.
	# To cu de trong o kieu_thue thi doc la "Theo to (cu)" va chay dung
	# nhanh duoi, con so khong doi mot dong. Khong co lenh nao chay len du
	# lieu qua khu.
	if _kieu_thue(doc) == KT_DONG:
		bt = bang_thue(
			[
				{"thanh_tien": flt(d.thanh_tien), "thue_pt": flt(d.thue_pt)}
				for d in (doc.get("dong") or [])
			],
			ck_to=doc.chiet_khau_tien,
			phi_giao=flt(doc.phi_giao),
			phi_giao_pt=flt(doc.get("thue_phi_giao_pt")),
			da_gom=1 if doc.gia_da_gom_vat else 0,
		)
		doc.thue_tien = bt["tien_thue"]
		doc.tong_cong = bt["tong_cong"]
		doc.dat_coc_tien = round(doc.tong_cong * flt(doc.dat_coc_pt) / 100.0, 0)
		return doc

	if doc.gia_da_gom_vat:
		doc.thue_tien = 0
		doc.tong_cong = sau_ck + flt(doc.phi_giao)
	else:
		doc.thue_tien = round(sau_ck * flt(doc.thue_pt) / 100.0, 0)
		doc.tong_cong = sau_ck + doc.thue_tien + flt(doc.phi_giao)
	doc.dat_coc_tien = round(doc.tong_cong * flt(doc.dat_coc_pt) / 100.0, 0)
	return doc


def _kiem_to_khop(d):
	"""Chan mot to bao gia ma cac dong khong cong lai ra dong tong.

	Ngay 19/08/2026 to VGB-PQ-2026-0008 in ra cho khach mot bang nhu the
	nay: cong tien hang chua thue 32.086.610, thue GTGT 0% la 0, roi TONG
	TIEN 34.653.539. Ba dong do khong the cung dung.

	Cai gia cua viec in bua la mot to sai gui thang tay khach hang. Cai gia
	cua viec dung lai la sales phai mo to ra bam Luu them mot lan. Khong
	can can nhac lau.
	"""
	tt = d.get("tom_tat_thue") or None
	tong = flt(d.get("tong_cong"))
	if tt:
		ra = flt(tt["tien_hang"]) + flt(tt["tien_thue"])
	else:
		ra = (flt(d.get("tam_tinh")) - flt(d.get("chiet_khau_tien"))
		      + flt(d.get("thue_tien")) + flt(d.get("phi_giao")))
	if abs(ra - tong) <= 1:
		return
	frappe.throw(
		"Tờ báo giá %s đang có số liệu không khớp nhau nên em chưa in được: "
		"cộng các dòng lại ra %s đ nhưng ô tổng đang lưu %s đ. Nhờ anh chị mở "
		"tờ này ra, kiểm lại mức thuế của từng dòng rồi bấm Lưu một lần nữa - "
		"máy sẽ tính lại toàn bộ và hai con số về khớp. Sau đó in lại được ngay."
		% (d.get("name") or "", _tien_vn(ra), _tien_vn(tong))
	)


def tom_tat_thue(doc):
	"""Bang Tom tat thue cua mot to. Tinh luc IN, khong luu xuong o dia.

	Khong luu la co y: bang nay chi la phep gom cac dong lai, ma thue_tien
	cua to duoc DINH NGHIA bang chinh tong do. Luu xuong thanh hai ban ghi
	roi la co ngay hai con so co the lech nhau vao mot ngay nao do.
	"""
	if _kieu_thue(doc) != KT_DONG:
		return None
	return bang_thue(
		[
			{"thanh_tien": flt(d.get("thanh_tien")), "thue_pt": flt(d.get("thue_pt"))}
			for d in (doc.get("dong") or [])
		],
		ck_to=flt(doc.get("chiet_khau_tien")),
		phi_giao=flt(doc.get("phi_giao")),
		phi_giao_pt=flt(doc.get("thue_phi_giao_pt")),
		da_gom=1 if doc.get("gia_da_gom_vat") else 0,
	)


F_CHU = (
	"ten", "ten_en", "khach_hang", "ten_khach", "ma_so_thue", "dia_chi",
	"nguoi_lien_he", "chuc_vu", "dien_thoai", "email", "loi_mo", "loi_mo_en",
	"thanh_toan", "thanh_toan_en", "yeu_cau_vi", "yeu_cau_en",
	"chinh_sach_huy_vi", "chinh_sach_huy_en", "luu_y_vi", "luu_y_en",
	"giao_hang", "dong_goi", "ghi_chu", "ghi_chu_noi_bo",
	"ten_nguoi_lap_in", "chuc_vu_lap", "dt_nguoi_lap", "email_lap",
	"kieu_thue", "kieu_ck",
)
F_SO = ("chiet_khau_pt", "thue_pt", "phi_giao", "dat_coc_pt", "thue_phi_giao_pt")
F_CO = ("song_ngu", "gia_da_gom_vat")
F_DONG = (
	"loai", "ma_mon", "ma_tv", "ten_mon", "ten_en", "dvt", "dvt_en", "hinh",
	"kich_thuoc", "mo_ta", "mo_ta_en", "di_ung_vi", "di_ung_en",
	"danh_muc_vi", "danh_muc_en",
)


def _tinh_khoa(doc):
	"""To nay con sua de duoc khong, va vi sao khong. THUAN, khong doc CSDL.

	Tra ve (khoa, ly_do). khoa = 1 nghia la chi con mot duong di tiep la mo
	mot vong thuong luong moi.
	"""
	if doc.get("la_mau"):
		return 0, ""
	if doc.get("thay_the_boi"):
		return 1, "Bản lịch sử, đã được thay bằng %s." % doc.get("thay_the_boi")
	tt = doc.get("trang_thai") or "Nháp"
	if tt == "Đã lên hợp đồng":
		return 1, "Đã lên hợp đồng %s." % (doc.get("hop_dong") or "")
	if tt in TT_KHONG_SUA_DE:
		return 1, "Khách đã cầm bản này, trạng thái đang là %s." % tt
	return 0, ""


def _goi(doc):
	ra = {"name": doc.name}
	for f in F_CHU:
		ra[f] = doc.get(f) or ""
	for f in F_SO:
		ra[f] = flt(doc.get(f))
	for f in F_CO:
		ra[f] = 1 if doc.get(f) else 0
	ra.update({
		"trang_thai": doc.trang_thai or "Nháp",
		"ngay_bao_gia": str(doc.ngay_bao_gia or ""),
		"hieu_luc_den": str(doc.hieu_luc_den or ""),
		"hieu_luc_ngay": int(doc.hieu_luc_ngay or 30),
		"hop_dong": doc.hop_dong or "",
		"nguoi_lap": doc.nguoi_lap or "",
		"tam_tinh": flt(doc.tam_tinh),
		"chiet_khau_tien": flt(doc.chiet_khau_tien),
		"thue_tien": flt(doc.thue_tien),
		"tong_cong": flt(doc.tong_cong),
		"dat_coc_tien": flt(doc.dat_coc_tien),
		"kieu_thue": _kieu_thue(doc),
		"thue_phi_giao_pt": flt(doc.get("thue_phi_giao_pt")),
		# Bang Tom tat thue, TINH LUC DOC chu khong luu. Man hinh chi viec
		# ve, khong tu cong lai - hai noi cung cong thi hai noi se lech.
		"tom_tat_thue": tom_tat_thue(doc),
	})
	# Phien ban. May chu tra luon KET LUAN "to nay con sua duoc khong" chu
	# khong de app tu suy tu trang thai: mot ngay nao do luat sua doi thi chi
	# sua o day, app khong phai biet gi them (QT-19).
	ra["goc"] = doc.get("goc") or ""
	ra["phien_ban"] = int(doc.get("phien_ban") or 1)
	ra["thay_the_boi"] = doc.get("thay_the_boi") or ""
	ra["ly_do_sua"] = doc.get("ly_do_sua") or ""
	ra["khoa"], ra["ly_do_khoa"] = _tinh_khoa(doc)
	ra["mau_in"] = doc.get("mau_in") or ""
	ra["phan_loai"] = doc.get("phan_loai") or ""
	ra["mo_ta_mau"] = doc.get("mo_ta_mau") or ""
	ra["dong"] = []
	for d in doc.get("dong") or []:
		x = {f: d.get(f) or "" for f in F_DONG}
		x.update({
			"so_luong": flt(d.so_luong),
			"don_gia": flt(d.don_gia),
			"chiet_khau": flt(d.chiet_khau),
			"kieu_ck": d.get("kieu_ck") or "",
			"ck_tien_dong": flt(d.get("ck_tien_dong")),
			"thue_pt": flt(d.thue_pt),
			"thanh_tien": flt(d.thanh_tien),
		})
		ra["dong"].append(x)
	ra["dich_vu"] = [
		{
			"ten_vi": d.ten_vi or "", "ten_en": d.ten_en or "",
			"gia_vi": d.gia_vi or "", "gia_en": d.gia_en or "",
		}
		for d in (doc.get("dich_vu") or [])
	]
	ra["moc"] = [
		{
			"moc_vi": d.moc_vi or "", "moc_en": d.moc_en or "",
			"noi_dung_vi": d.noi_dung_vi or "", "noi_dung_en": d.noi_dung_en or "",
			"trach_nhiem": d.trach_nhiem or "",
		}
		for d in (doc.get("moc") or [])
	]
	return ra


# ------------------------------------------------------------------ doc api


@frappe.whitelist()
def cai_dat():
	_quyen()
	return {
		"trang_thai": TRANG_THAI,
		"chip_hieu_luc": CHIP_HIEU_LUC,
		"chip_vat": CHIP_VAT,
		"duoc_sua": bool(QUYEN_SUA & set(frappe.get_roles())),
		"mau_in": MAU_IN,
		"phan_loai": PHAN_LOAI,
		"mac_dinh": _cd(),
	}


@frappe.whitelist()
def danh_sach(trang_thai=None, loc=None, tim=None, ban_cu=None):
	"""Danh sach bao gia kem so dem cho tung chip loc.

	Mac dinh CHI hien ban moi nhat cua moi cuoc thuong luong. Mua trung thu
	mot khach ba vong la danh sach gap ba, sales khong tim ra to nao that.
	Chip "Bản cũ" mo ra xem lai lich su khi can.
	"""
	_quyen()
	tat_ca = frappe.get_all(
		DT,
		# Mau bao gia khong phai to that nen khong nam trong danh sach.
		# Mau xem va quan ly rieng o man "Mau bao gia".
		filters={"la_mau": 0},
		fields=[
			"name", "ten", "trang_thai", "khach_hang", "ten_khach",
			"ngay_bao_gia", "hieu_luc_den", "tong_cong", "hop_dong",
			"nguoi_lap", "modified", "goc", "phien_ban", "thay_the_boi",
		],
		order_by="modified desc",
		limit_page_length=400,
	)
	# Loc bang "thay_the_boi con trong" chu khong bang mot co ban_moi_nhat:
	# co thi phai backfill cho cac to dang co, ma dung vao du lieu qua khu la
	# dieu anh Viet cam ngay 13/08. Cach nay dung ngay tu to dau tien, khong
	# phai chay mot lenh nao len du lieu cu.
	xem_cu = str(ban_cu or "") in ("1", "true", "True")
	ds = [x for x in tat_ca if not x.get("thay_the_boi")]
	so_ban_cu = len(tat_ca) - len(ds)
	hn = getdate(nowdate())
	toi = frappe.session.user
	for r in tat_ca:
		r["phien_ban"] = int(r.get("phien_ban") or 1)
		r["la_ban_cu"] = bool(r.get("thay_the_boi"))
		hl = getdate(r["hieu_luc_den"]) if r.get("hieu_luc_den") else None
		con = (hl - hn).days if hl else None
		r["con_ngay"] = con
		r["dang_mo"] = r["trang_thai"] in ("Nháp", "Đã gửi khách")
		r["qua_han"] = bool(r["dang_mo"] and con is not None and con < 0)
		r["sap_het"] = bool(r["dang_mo"] and con is not None and 0 <= con <= 3)
		r["cua_toi"] = r.get("nguoi_lap") == toi
	# Ban cu khong bao gio bi tinh la qua han hay sap het: no da xong doi
	# roi, keu len chi lam nhieu cai chuong cua sales.
	for r in tat_ca:
		if r["la_ban_cu"]:
			r["dang_mo"] = r["qua_han"] = r["sap_het"] = False

	dem = {
		"tat_ca": len(ds),
		"ban_cu": so_ban_cu,
		"cho_khach": len([x for x in ds if x["trang_thai"] == "Đã gửi khách"]),
		"nhap": len([x for x in ds if x["trang_thai"] == "Nháp"]),
		"sap_het": len([x for x in ds if x["sap_het"]]),
		"qua_han": len([x for x in ds if x["qua_han"]]),
		"cua_toi": len([x for x in ds if x["cua_toi"] and x["dang_mo"]]),
		"duyet": len([x for x in ds if x["trang_thai"] == "Khách duyệt"]),
	}
	for t in TRANG_THAI:
		dem["tt:" + t] = len([x for x in ds if x["trang_thai"] == t])

	ra = tat_ca if xem_cu else ds
	if trang_thai:
		ra = [x for x in ra if x["trang_thai"] == trang_thai]
	if loc == "cho_khach":
		ra = [x for x in ra if x["trang_thai"] == "Đã gửi khách"]
	elif loc == "sap_het":
		ra = [x for x in ra if x["sap_het"]]
	elif loc == "qua_han":
		ra = [x for x in ra if x["qua_han"]]
	elif loc == "cua_toi":
		ra = [x for x in ra if x["cua_toi"] and x["dang_mo"]]
	elif loc == "gia_tri":
		ra = sorted(ra, key=lambda x: -flt(x["tong_cong"]))
	if tim:
		t = str(tim).lower()
		ra = [
			x for x in ra
			if t in ((x.get("ten") or "") + " " + (x.get("ten_khach") or "")
					 + " " + x["name"]).lower()
		]
	return {"dem": dem, "ds": ra[:200]}


@frappe.whitelist()
def chi_tiet(name):
	_quyen()
	return _goi(frappe.get_doc(DT, name))


@frappe.whitelist()
def moi():
	"""Khung to bao gia trong, chep san cau chu tu Cai dat bao gia."""
	_quyen(sua=True)
	nd = frappe.session.user
	c = _cd()
	u = frappe.db.get_value("User", nd, ["full_name", "mobile_no"], as_dict=True) or {}
	return {
		"name": "", "trang_thai": "Nháp", "song_ngu": 1, "gia_da_gom_vat": 1,
		"ten": "", "ten_en": "", "khach_hang": "", "ten_khach": "",
		"ma_so_thue": "", "dia_chi": "", "nguoi_lien_he": "", "chuc_vu": "",
		"dien_thoai": "", "email": "",
		"ngay_bao_gia": nowdate(), "hieu_luc_ngay": 30,
		"hieu_luc_den": add_days(nowdate(), 30),
		"hop_dong": "",
		"loi_mo": c["loi_mo_vi"], "loi_mo_en": c["loi_mo_en"],
		"thanh_toan": c["thanh_toan_vi"], "thanh_toan_en": c["thanh_toan_en"],
		"yeu_cau_vi": c["yeu_cau_vi"], "yeu_cau_en": c["yeu_cau_en"],
		"chinh_sach_huy_vi": c["chinh_sach_huy_vi"],
		"chinh_sach_huy_en": c["chinh_sach_huy_en"],
		"luu_y_vi": c["luu_y_vi"], "luu_y_en": c["luu_y_en"],
		"giao_hang": "", "dong_goi": "", "ghi_chu": "", "ghi_chu_noi_bo": "",
		"chiet_khau_pt": 0, "chiet_khau_tien": 0, "kieu_ck": "", "thue_pt": 8, "thue_tien": 0,
		# BAT BUOC co mat. Thieu dong nay la app khong gui kieu_thue len,
		# may chu tinh mot dang roi co so du lieu ghi mot dang - dung su co
		# to VGB-PQ-2026-0008 ngay 19/08/2026.
		"kieu_thue": KT_MAC_DINH_TO_MOI,
		"phi_giao": 0, "dat_coc_pt": 50, "dat_coc_tien": 0,
		"tam_tinh": 0, "tong_cong": 0,
		"nguoi_lap": nd,
		"ten_nguoi_lap_in": c["dai_dien_ban"] or u.get("full_name") or "",
		"chuc_vu_lap": c["chuc_vu_ban"] or "",
		"dt_nguoi_lap": c["dt_ban"] or u.get("mobile_no") or "",
		"email_lap": c["email_ban"] or nd,
		"dong": [], "dich_vu": [], "moc": list(c["moc_mau"]),
	}


@frappe.whitelist()
def luu(du_lieu):
	"""Tao moi hoac ghi de mot to bao gia. App gui nguyen cuc JSON len."""
	_quyen(sua=True)
	d = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
	if not (d.get("ten") or "").strip():
		frappe.throw("Nhập tiêu đề báo giá đã nhé.")
	if not (d.get("ten_khach") or d.get("khach_hang")):
		frappe.throw("Chọn khách hàng hoặc nhập tên công ty khách.")

	name = d.get("name") or ""
	if name:
		doc = frappe.get_doc(DT, name)
		# Cua ai toan bo tinh nang phien ban. Ba dong doc.set(b, []) ngay ben
		# duoi XOA SACH ba bang con roi dung lai tu cuc JSON app gui len -
		# tuc sua mot to da gui khach la thoi bay noi dung cu, khong con mot
		# dau vet nao. Chan o day la bit dung cai lo do.
		khoa, vi_sao = _tinh_khoa(doc)
		if khoa:
			frappe.throw(
				"Không sửa đè được báo giá %s. %s Bấm \"Tạo phiên bản kế "
				"tiếp\" để mở một vòng thương lượng mới, bản đang có vẫn "
				"giữ nguyên từng dòng." % (doc.name, vi_sao)
			)
		for b in ("dong", "dich_vu", "moc"):
			doc.set(b, [])
	else:
		doc = frappe.new_doc(DT)
		doc.nguoi_lap = frappe.session.user

	_do_vao(doc, d)
	_tinh(doc)
	doc.save(ignore_permissions=True)
	return _goi(doc)


def _do_vao(doc, d):
	"""Do cuc JSON cua app vao mot doc. KHONG luu, KHONG dung toi CSDL.

	Tach rieng de ham luu() va ham xem truoc dung CHUNG mot phep anh xa.
	Hai phep anh xa khac nhau thi som muon to xem truoc va to in that lech
	nhau, ma loai lech do rat kho thay.
	"""
	# Che do thue cua to TRUOC khi do du lieu moi vao. Phai lay o day vi
	# vong lap F_CHU ngay duoi se ghi de o do bang None neu app khong gui.
	kt_cu = _kieu_thue(doc) if not doc.is_new() else ""
	for f in F_CHU:
		doc.set(f, d.get(f) or None)
	# O nay KHONG duoc de None. Doctype tung mang "default": "Theo tung
	# dong", nen mot o None luc INSERT se bi co so du lieu dien gia tri mac
	# dinh vao, va to bi GHI o mot che do khac han che do vua dung de TINH.
	# Ghi thang mot gia tri ro rang la bit han duong do, khong phu thuoc
	# vao viec doctype con default hay khong.
	#
	# App khong gui gi thi GIU NGUYEN che do cu cua to, khong tu doi. Doi
	# che do thue la doi so tien cuoi cung, viec do phai do nguoi bam.
	gui = str(d.get("kieu_thue") or "").strip()
	if gui in (KT_TO, KT_DONG):
		doc.kieu_thue = gui
	else:
		doc.kieu_thue = kt_cu or KT_MAC_DINH_TO_MOI
	# Bo cuc to in va phan loai. Kiem o MAY CHU chu khong tin app: app gui
	# len ma la thi to se in bang mot khuon khong ton tai (QT-19).
	if d.get("mau_in") in MA_MAU_IN:
		doc.mau_in = d.get("mau_in") or None
	if d.get("phan_loai") in MA_PHAN_LOAI:
		doc.phan_loai = d.get("phan_loai") or None
	if doc.get("la_mau"):
		doc.mo_ta_mau = d.get("mo_ta_mau") or None
	for f in ("ngay_bao_gia", "hieu_luc_den"):
		doc.set(f, d.get(f) or None)
	for f in F_SO:
		doc.set(f, flt(d.get(f)))
	for f in F_CO:
		doc.set(f, 1 if d.get(f) else 0)
	doc.hieu_luc_ngay = int(flt(d.get("hieu_luc_ngay")) or 30)
	if d.get("trang_thai") in TRANG_THAI:
		doc.trang_thai = d["trang_thai"]

	for x in d.get("dong") or []:
		if not (x.get("ten_mon") or x.get("ma_mon")):
			continue
		row = {f: (x.get(f) or None) for f in F_DONG}
		row["ten_mon"] = x.get("ten_mon") or x.get("ma_mon")
		row["loai"] = x.get("loai") or "Món"
		row["so_luong"] = flt(x.get("so_luong")) or 1
		row["don_gia"] = flt(x.get("don_gia"))
		row["chiet_khau"] = flt(x.get("chiet_khau"))
		# Kieu chiet khau cua dong. Chi nhan dung hai chuoi da biet, con
		# lai coi nhu de trong tuc phan tram - QT-19, khong tin may khach.
		row["kieu_ck"] = x.get("kieu_ck") if x.get("kieu_ck") in (CK_PT, CK_TIEN) else None
		# Dong khong khai muc thue thi lay muc cua to, de sales khong phai
		# go lai tung dong khi ca to cung mot muc.
		row["thue_pt"] = (
			flt(x.get("thue_pt")) if x.get("thue_pt") not in (None, "")
			else flt(doc.thue_pt)
		)
		doc.append("dong", row)
	if not doc.get("dong"):
		frappe.throw("Báo giá phải có ít nhất một dòng sản phẩm.")

	for x in d.get("dich_vu") or []:
		if not (x.get("ten_vi") or "").strip():
			continue
		doc.append("dich_vu", {
			"ten_vi": x.get("ten_vi"), "ten_en": x.get("ten_en") or None,
			"gia_vi": x.get("gia_vi") or None, "gia_en": x.get("gia_en") or None,
		})
	for x in d.get("moc") or []:
		if not (x.get("moc_vi") or "").strip():
			continue
		doc.append("moc", {
			"moc_vi": x.get("moc_vi"), "moc_en": x.get("moc_en") or None,
			"noi_dung_vi": x.get("noi_dung_vi") or None,
			"noi_dung_en": x.get("noi_dung_en") or None,
			"trach_nhiem": x.get("trach_nhiem") or "Vagabond / Seller",
		})
	return doc


@frappe.whitelist()
def doi_trang_thai(name, trang_thai):
	_quyen(sua=True)
	if trang_thai not in TRANG_THAI:
		frappe.throw("Trạng thái không hợp lệ.")
	cu = frappe.db.get_value(
		DT, name, ["trang_thai", "thay_the_boi", "la_mau"], as_dict=True
	) or {}
	if cu.get("thay_the_boi"):
		frappe.throw(
			"Báo giá %s là bản lịch sử, đã được thay bằng %s nên trạng thái "
			"của nó là chuyện đã rồi, không đổi được nữa. Đổi trạng thái "
			"trên %s nhé." % (name, cu["thay_the_boi"], cu["thay_the_boi"])
		)
	# Cam keo nguoc ve Nhap. Neu con duong nay mo thi tinh nang phien ban chi
	# la trang tri: sales muon sua de mot to da gui khach chi viec keo ve
	# Nhap, sua, roi keo len lai - va ban khach dang cam bien mat khong dau
	# vet, dung cai ma anh muon chan.
	if (
		trang_thai == "Nháp"
		and (cu.get("trang_thai") or "Nháp") != "Nháp"
		and not cu.get("la_mau")
	):
		frappe.throw(
			"Báo giá %s đã ở trạng thái %s, tức khách đã cầm bản này rồi nên "
			"không kéo ngược về Nháp được. Cần sửa thì bấm \"Tạo phiên bản "
			"kế tiếp\", bản mới sinh ra sẽ ở trạng thái Nháp để sửa thoải "
			"mái." % (name, cu.get("trang_thai"))
		)
	frappe.db.set_value(DT, name, "trang_thai", trang_thai)
	return trang_thai


@frappe.whitelist()
def xoa(name):
	_quyen(sua=True)
	o = frappe.db.get_value(
		DT, name, ["trang_thai", "thay_the_boi", "goc", "phien_ban"], as_dict=True
	) or {}
	if o.get("thay_the_boi"):
		frappe.throw(
			"Báo giá %s là bản lịch sử của một cuộc thương lượng, đã được "
			"thay bằng %s nên không xoá được. Đây là bằng chứng về những gì "
			"đã gửi khách." % (name, o["thay_the_boi"])
		)
	tt = o.get("trang_thai")
	if tt != "Nháp":
		frappe.throw(
			"Báo giá đã ở trạng thái %s nên không xoá được. "
			"Chuyển sang Khách từ chối để lưu lại dấu vết." % tt
		)
	# Xoa mot vong con Nhap la "huy vong vua mo". Phai go khoa cho ban truoc
	# no, neu khong ban truoc nam dong bang vinh vien voi mot con tro tro vao
	# khoang khong, va tu do khong ai sua duoc to nao trong cuoc nay nua.
	if o.get("goc"):
		truoc = frappe.db.get_value(DT, {"thay_the_boi": name}, "name")
		if truoc:
			frappe.db.set_value(
				DT, truoc, "thay_the_boi", None, update_modified=False
			)
			frappe.get_doc(DT, truoc).add_comment(
				"Comment",
				"Mở khoá: vòng %s vừa mở đã bị xoá khi còn Nháp."
				% (o.get("phien_ban") or ""),
			)
	frappe.delete_doc(DT, name, ignore_permissions=True)
	return 1


@frappe.whitelist()
def nhan_ban(name):
	"""Nhan ban mot to. Mua trung thu Loan Anh gui gan giong nhau cho hang
	chuc cong ty, chi khac ten khach va so luong."""
	_quyen(sua=True)
	cu = frappe.get_doc(DT, name)
	moi_ = frappe.copy_doc(cu)
	moi_.trang_thai = "Nháp"
	moi_.hop_dong = None
	moi_.ngay_bao_gia = nowdate()
	moi_.hieu_luc_den = add_days(nowdate(), int(cu.hieu_luc_ngay or 30))
	moi_.nguoi_lap = frappe.session.user
	# Nhan ban sang KHACH KHAC la mot cuoc thuong luong moi hoan toan, khong
	# phai vong tiep theo cua cuoc cu. Khong xoa bon truong nay thi to moi
	# thua ca "goc" lan "thay_the_boi" cua to cu, tuc no chao doi da o trang
	# thai dong bang va khong ai sua duoc.
	_xoa_dau_phien_ban(moi_)
	moi_.insert(ignore_permissions=True)
	return moi_.name


# ------------------------------------------------------ phien ban thuong luong


def _xoa_dau_phien_ban(doc):
	"""Go moi dau vet phien ban khoi mot ban sao. THUAN, chi set truong."""
	doc.goc = None
	doc.phien_ban = 1
	doc.thay_the_boi = None
	doc.ly_do_sua = None


def _goc_cua(doc):
	"""Ten to vong 1. Vong 2 tro di deu tro ve dung mot goc, khong noi chuoi
	v2 -> v3 -> v4; noi chuoi thi doc lich su phai lan nguoc tung buoc."""
	return doc.get("goc") or doc.name


def _chan_dong_bang(doc, viec):
	"""Chan moi thao tac ghi len mot ban da bi thay the."""
	if doc.get("thay_the_boi"):
		frappe.throw(
			"Báo giá %s là bản lịch sử, đã được thay bằng %s nên không %s "
			"được. Mở %s để làm tiếp nhé."
			% (doc.name, doc.thay_the_boi, viec, doc.thay_the_boi)
		)


@frappe.whitelist()
def tao_phien_ban(name, ly_do=None):
	"""Mo mot vong thuong luong moi tu to dang co.

	Ban cu KHONG bi dung toi mot chu: no chi duoc dan them mot con tro
	thay_the_boi, va con tro do chinh la cai khoa. Ban moi ke thua toan bo
	noi dung roi ve trang thai Nhap de sales sua thoai mai.
	"""
	_quyen(sua=True)
	ly_do = (ly_do or "").strip()
	if not ly_do:
		frappe.throw(
			"Ghi một dòng lý do mở vòng mới đã nhé, ví dụ \"Khách xin giảm "
			"5% và bỏ phần bánh mặn\". Câu này nằm lại trong lịch sử thương "
			"lượng, sau này mở ra là biết vì sao giá đổi."
		)
	cu = frappe.get_doc(DT, name)
	if cu.get("la_mau"):
		frappe.throw(
			"Đây là mẫu báo giá chứ không phải tờ gửi khách nên không có "
			"vòng thương lượng. Lập một tờ thật từ mẫu này rồi làm tiếp nhé."
		)
	_chan_dong_bang(cu, "mở vòng mới")

	goc = _goc_cua(cu)
	# Khoa dong goc lai truoc khi dem. Hai sales cung bam "Tao phien ban" tren
	# cung mot to trong cung mot giay thi ca hai deu doc ra vong 2 va ban thu
	# hai chet vi trung ten. Khoa o day bat ho xep hang, nguoi sau doc ra
	# vong 3.
	frappe.db.sql(
		"select name from `tabBao Gia Ban Hang` where name = %s for update",
		goc,
	)
	cao = frappe.db.sql(
		"""select max(ifnull(phien_ban, 1)) from `tabBao Gia Ban Hang`
		where name = %(g)s or goc = %(g)s""",
		{"g": goc},
	)
	so = int((cao and cao[0][0]) or 1) + 1

	moi_ = frappe.copy_doc(cu)
	moi_.goc = goc
	moi_.phien_ban = so
	moi_.thay_the_boi = None
	moi_.ly_do_sua = ly_do
	moi_.trang_thai = "Nháp"
	moi_.hop_dong = None
	moi_.la_mau = 0
	moi_.ten_mau = None
	moi_.ngay_bao_gia = nowdate()
	moi_.hieu_luc_den = add_days(nowdate(), int(cu.hieu_luc_ngay or 30))
	moi_.nguoi_lap = frappe.session.user
	moi_.insert(ignore_permissions=True)

	# Dong bang ban cu. Dung db.set_value chu khong doc.save vi:
	#   - save se chay validate, ma validate vua duoc dat de CHAN ghi len ban
	#     co thay_the_boi, tuc no se tu chan chinh no;
	#   - update_modified=False de moc thoi gian cua ban cu dung nguyen, dung
	#     tinh than QT-20 la khong dung vao so goc.
	frappe.db.set_value(
		DT, cu.name, "thay_the_boi", moi_.name, update_modified=False
	)
	cu.add_comment(
		"Comment",
		"Đóng băng: đã mở vòng %d là %s. Lý do: %s" % (so, moi_.name, ly_do),
	)
	moi_.add_comment(
		"Comment",
		"Vòng %d, kế thừa từ %s. Lý do: %s" % (so, cu.name, ly_do),
	)
	return {"name": moi_.name, "phien_ban": so, "cu": cu.name}


@frappe.whitelist()
def lich_su(name):
	"""Moi vong cua cung mot cuoc thuong luong, kem muc nhuong bo tung vong.

	Con so chenh lech tinh o may chu (QT-19), app chi in ra.
	"""
	_quyen()
	goc = frappe.db.get_value(DT, name, "goc") or name
	ds = frappe.get_all(
		DT,
		or_filters=[["name", "=", goc], ["goc", "=", goc]],
		fields=[
			"name", "phien_ban", "trang_thai", "ngay_bao_gia", "tam_tinh",
			"chiet_khau_pt", "chiet_khau_tien", "phi_giao", "tong_cong",
			"ly_do_sua", "thay_the_boi", "nguoi_lap", "creation",
		],
		# Frappe 16 chan moi loi goi ham trong order_by, ke ca ifnull(). Ma
		# to lap truoc dot nay co phien_ban rong nen khong xep bang SQL duoc.
		# Xep o Python, vua dung vua khong phu thuoc vao luat cua khung.
		order_by="creation asc",
		limit_page_length=0,
	)
	for r in ds:
		r["phien_ban"] = int(r.get("phien_ban") or 1)
	ds.sort(key=lambda x: (x["phien_ban"], str(x.get("creation") or "")))
	truoc = None
	for r in ds:
		r["la_moi_nhat"] = not r.get("thay_the_boi")
		r["dang_xem"] = r["name"] == name
		r["chenh"] = 0.0 if truoc is None else flt(r["tong_cong"]) - flt(truoc)
		truoc = r["tong_cong"]
	return {"goc": goc, "so_vong": len(ds), "ds": ds}


# --------------------------------------------------------------- thu vien


@frappe.whitelist()
def tv_danh_sach(loai=None, tim=None):
	_quyen()
	loc = {}
	if loai:
		loc["loai"] = loai
	ds = frappe.get_all(
		DT_TV,
		filters=loc,
		fields=[
			"name", "loai", "nhom", "ten_vi", "ten_en", "hinh", "don_gia",
			"dvt_vi", "gia_chu_vi", "kich_thuoc", "dung", "ma_item",
		],
		order_by="loai asc, thu_tu asc, ten_vi asc",
		limit_page_length=0,
	)
	if tim:
		t = str(tim).lower()
		ds = [
			x for x in ds
			if t in ((x.get("ten_vi") or "") + " " + (x.get("ten_en") or "")
					 + " " + (x.get("nhom") or "")).lower()
		]
	dem = {}
	for x in ds:
		dem[x["loai"]] = dem.get(x["loai"], 0) + 1
	return {"ds": ds, "dem": dem, "so_thieu_anh": len([x for x in ds if not x["hinh"]])}


@frappe.whitelist()
def tv_chi_tiet(name):
	_quyen()
	return frappe.get_doc(DT_TV, name).as_dict()


@frappe.whitelist()
def tv_luu(du_lieu):
	_quyen(sua=True)
	d = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
	if not (d.get("ten_vi") or "").strip():
		frappe.throw("Nhập tên tiếng Việt đã nhé.")
	name = d.get("name") or ""
	doc = frappe.get_doc(DT_TV, name) if name else frappe.new_doc(DT_TV)
	for f in (
		"loai", "nhom", "ten_vi", "ten_en", "ma_item", "hinh", "kich_thuoc",
		"dvt_vi", "dvt_en", "gia_chu_vi", "gia_chu_en", "mo_ta_vi", "mo_ta_en",
		"di_ung_vi", "di_ung_en", "ghi_chu_noi_bo",
	):
		if f in d:
			doc.set(f, d.get(f) or None)
	doc.don_gia = flt(d.get("don_gia"))
	doc.thu_tu = int(flt(d.get("thu_tu")))
	doc.dung = 0 if d.get("dung") in (0, "0", False) else 1
	doc.save(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def tv_xoa(name):
	_quyen(sua=True)
	frappe.delete_doc(DT_TV, name, ignore_permissions=True)
	return 1


@frappe.whitelist()
def tv_tu_dong(name_bao_gia, dong_idx):
	"""Luu mot dong dang soan tren to bao gia vao thu vien de lan sau chon lai."""
	_quyen(sua=True)
	doc = frappe.get_doc(DT, name_bao_gia)
	i = int(dong_idx)
	if i < 0 or i >= len(doc.dong):
		frappe.throw("Không có dòng này.")
	d = doc.dong[i]
	tv = frappe.new_doc(DT_TV)
	tv.loai = d.loai or "Món"
	tv.nhom = d.danh_muc_vi or ("Món thiết kế riêng" if not d.ma_mon else "")
	tv.ten_vi = d.ten_mon
	tv.ten_en = d.ten_en
	tv.ma_item = d.ma_mon
	tv.hinh = d.hinh
	tv.kich_thuoc = d.kich_thuoc
	tv.don_gia = flt(d.don_gia)
	tv.dvt_vi = d.dvt
	tv.dvt_en = d.dvt_en
	tv.mo_ta_vi = d.mo_ta
	tv.mo_ta_en = d.mo_ta_en
	tv.di_ung_vi = d.di_ung_vi
	tv.di_ung_en = d.di_ung_en
	tv.insert(ignore_permissions=True)
	frappe.db.set_value("Bao Gia Dong", d.name, "ma_tv", tv.name)
	return tv.name


@frappe.whitelist()
def cd_luu(du_lieu):
	"""Ghi lai cau chu khung to bao gia."""
	_quyen(sua=True)
	if "Sales Manager" not in frappe.get_roles() and "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản lý kinh doanh mới sửa được câu chữ khung tờ báo giá.")
	d = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
	doc = frappe.get_single(DT_CD)
	for f in (
		"ten_ban", "mst_ban", "dia_chi_ban", "web_ban", "dai_dien_ban",
		"chuc_vu_ban", "dt_ban", "email_ban",
		"nguoi_ky_ban", "chuc_vu_ky_ban", "dt_ky_ban", "email_ky_ban",
		"loi_mo_vi", "loi_mo_en",
		"thanh_toan_vi", "thanh_toan_en", "ngan_hang_vi", "ngan_hang_en",
		"yeu_cau_vi", "yeu_cau_en", "chinh_sach_huy_vi", "chinh_sach_huy_en",
		"luu_y_vi", "luu_y_en",
	):
		if f in d:
			doc.set(f, d.get(f) or None)
	doc.save(ignore_permissions=True)
	return 1


@frappe.whitelist()
def cd_doc():
	_quyen()
	return _cd()


# ------------------------------------------------------------ chon khach


@frappe.whitelist()
def tim_khach(tim=None, so_dong=60):
	"""Tim khach hang cho o chon khach cua to bao gia.

	Vi sao ham nay phai duoc goi LAI moi lan go
	--------------------------------------------
	Truoc 15/08/2026 man bao gia goi ham nay MOT lan khong kem tu khoa, lay
	ve 400 khach dau bang chu cai roi de trinh duyet tu loc trong 400 muc
	do. He dang co 43.186 khach, nen 400 cai ten dau bang chu cai gan nhu
	chac chan khong co cai nao bat dau bang "CONG TY": go gi cung ra "Khong
	tim thay", con Loan Anh thi tuong du lieu chua nhap.

	Loc o may khach tren mot tap da bi cat cut la loi kien truc, khong phai
	loi go nham. Nay app hoi nguoc len day moi lan go, va day tim tren ca
	43.186 khach.
	"""
	_quyen()
	q = (tim or "").strip()
	truong = ["name", "customer_name", "tax_id", "mobile_no", "customer_group"]
	n = max(10, min(int(so_dong or 60), 200))
	if not q:
		return frappe.get_all(
			"Customer",
			filters={"disabled": 0},
			fields=truong,
			order_by="modified desc",
			limit_page_length=n,
		)
	# Loan Anh nhieu khi chi cam moi cai ma so thue, hoac chi nho so dien
	# thoai. Tim mot cot ten thoi la bat ho phai nho dung ten dang ky.
	return frappe.get_all(
		"Customer",
		filters={"disabled": 0},
		or_filters={
			"name": ["like", "%%%s%%" % q],
			"customer_name": ["like", "%%%s%%" % q],
			"tax_id": ["like", "%%%s%%" % q],
			"mobile_no": ["like", "%%%s%%" % q],
		},
		fields=truong,
		order_by="customer_name asc",
		limit_page_length=n,
	)


# ------------------------------------------------- tao khach tu to bao gia

# Anh Viet 18/08/2026: "khach hang nhan bao gia co khi la khach hang moi thi
# sao em, dau co trong he thong dau, em de xuat cho nay xem lam sao, hay la co
# nut tao khach hang cho Loan Anh tao duoc khong?"
#
# Dung la mot lo hong that trong luong: to bao gia cho phep de trong o Khach
# hang - va nen the, vi bao gia thi gui cho ai cung duoc - nhung buoc CHOT
# THANH HOP DONG lai bat buoc phai co ho so khach, vi hop dong con phai gan
# hoa don va theo doi cong no. Truoc hom nay khong co duong nao di tu cai
# thu nhat sang cai thu hai ma khong bo app ra mo Desk.
#
# Ba dieu anh Viet chot 18/08/2026:
#   trung ma so thue  gan luon vao khach cu va bao ro, khong tao them dong
#   nhom khach        Commercial
#   dat o dau         ca trong o chon khach, ca o buoc chot hop dong

NHOM_KHACH_MOI = "Commercial"


def _chuan_mst(s):
	"""Ma so thue ve dang de so sanh: bo dau cach, dau gach, dau cham. THUAN.

	Nguoi go tay hay them dau gach o ma so thue don vi truc thuoc, kieu
	"0314693309-001". Hai cach go cua cung mot ma so phai coi la mot, neu
	khong thi phep do trung thanh vo dung.
	"""
	return "".join(c for c in str(s or "") if c.isdigit())


def _tim_theo_mst(mst):
	"""Cac khach dang co cung ma so thue. Tra ve danh sach, co the rong."""
	so = _chuan_mst(mst)
	if not so:
		return []
	# Loc tho o may chu roi so chinh xac o day: cot tax_id tren he go moi
	# kieu, khong the LIKE thang duoc.
	ds = frappe.get_all(
		"Customer",
		filters={"tax_id": ["like", "%%%s%%" % so[:10]]},
		fields=["name", "customer_name", "tax_id", "customer_group", "disabled"],
		limit_page_length=50,
	)
	return [d for d in ds if _chuan_mst(d.get("tax_id")) == so]


@frappe.whitelist()
def xem_truoc_tao_khach(name):
	"""To nay tao khach duoc chua, va tao ra se thanh cai gi.

	Bay het ra TRUOC khi bam, vi tao mot ho so khach la them mot dong vao
	so 43.220 khach dang co - va dong rac thi khong ai di don.
	"""
	_quyen()
	doc = frappe.get_doc(DT, name)
	ten = (doc.ten_khach or "").strip()
	mst = (doc.ma_so_thue or "").strip()
	trung = _tim_theo_mst(mst)
	# Trung TEN thi chi canh bao chu khong chan: hai cong ty khac ma so thue
	# van co the trung ten, va nguoi bam phai la nguoi quyet.
	gan_giong = []
	if ten:
		gan_giong = [
			d for d in frappe.get_all(
				"Customer",
				filters={"customer_name": ["like", "%%%s%%" % ten[:30]]},
				fields=["name", "customer_name", "tax_id"],
				limit_page_length=10,
			)
			if d["name"] not in {x["name"] for x in trung}
		]
	return {
		"da_gan": doc.khach_hang or "",
		"ten_khach": ten,
		"ma_so_thue": mst,
		"dia_chi": doc.dia_chi or "",
		"nguoi_lien_he": doc.nguoi_lien_he or "",
		"chuc_vu": doc.chuc_vu or "",
		"dien_thoai": doc.dien_thoai or "",
		"email": doc.email or "",
		"nhom": NHOM_KHACH_MOI,
		"trung_mst": trung,
		"gan_giong": gan_giong[:5],
		"thieu_ten": 0 if ten else 1,
	}


@frappe.whitelist()
def tao_khach(name):
	"""Tao ho so khach tu thong tin da go tren to bao gia, roi gan vao to.

	Do trung theo MA SO THUE truoc. Ma so thue la duy nhat theo luat, nen
	trung ma so nghia la cung mot phap nhan: luc do gan vao ho so cu chu
	KHONG tao them dong moi.
	"""
	_quyen(sua=True)
	doc = frappe.get_doc(DT, name)
	if doc.khach_hang and frappe.db.exists("Customer", doc.khach_hang):
		return {
			"khach": doc.khach_hang,
			"moi": 0,
			"ghi_chu": "Tờ này đã gắn khách %s rồi, em không tạo thêm." % doc.khach_hang,
		}
	ten = (doc.ten_khach or "").strip()
	if not ten:
		frappe.throw(
			"Chưa có tên công ty khách trên tờ báo giá. Anh chị bấm Sửa báo giá, "
			"điền ô Tên công ty khách rồi tạo lại nhé."
		)

	trung = _tim_theo_mst(doc.ma_so_thue)
	if trung:
		kh = trung[0]["name"]
		frappe.db.set_value(DT, name, "khach_hang", kh)
		frappe.db.commit()
		return {
			"khach": kh,
			"moi": 0,
			"ghi_chu": "Mã số thuế %s đã có sẵn hồ sơ khách %s. Em gắn tờ này "
			"vào hồ sơ đó thay vì tạo thêm một dòng trùng."
			% (doc.ma_so_thue, trung[0].get("customer_name") or kh),
		}

	nhom = NHOM_KHACH_MOI
	if not frappe.db.exists("Customer Group", nhom):
		nhom = frappe.db.get_value("Customer Group", {"is_group": 0}, "name")
	kh = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": ten,
		"customer_type": "Company",
		"customer_group": nhom,
		"tax_id": (doc.ma_so_thue or "").strip() or None,
		"mobile_no": (doc.dien_thoai or "").strip() or None,
	})
	kh.insert(ignore_permissions=True)

	# Dia chi va nguoi lien he la hai doctype rieng cua ERPNext, khong phai
	# hai o tren Customer. Thieu chung thi lan sau mo lai ho so khach se
	# trong tron, va nguoi ta lai go tay lan nua.
	if (doc.dia_chi or "").strip():
		try:
			dc = frappe.get_doc({
				"doctype": "Address",
				"address_title": ten[:100],
				"address_type": "Billing",
				"address_line1": (doc.dia_chi or "").strip()[:240],
				"city": "TP.HCM",
				"country": "Vietnam",
				"is_primary_address": 1,
				"links": [{"link_doctype": "Customer", "link_name": kh.name}],
			})
			dc.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "bao_gia: tao dia chi khach")

	if (doc.nguoi_lien_he or "").strip():
		try:
			cum = (doc.nguoi_lien_he or "").strip().split()
			lh = frappe.get_doc({
				"doctype": "Contact",
				"first_name": " ".join(cum[:-1]) or cum[0],
				"last_name": cum[-1] if len(cum) > 1 else "",
				"designation": (doc.chuc_vu or "").strip() or None,
				"is_primary_contact": 1,
				"links": [{"link_doctype": "Customer", "link_name": kh.name}],
			})
			if (doc.dien_thoai or "").strip():
				lh.append("phone_nos", {
					"phone": doc.dien_thoai.strip(), "is_primary_mobile_no": 1
				})
			if (doc.email or "").strip():
				lh.append("email_ids", {
					"email_id": doc.email.strip(), "is_primary": 1
				})
			lh.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "bao_gia: tao nguoi lien he khach")

	frappe.db.set_value(DT, name, "khach_hang", kh.name)
	frappe.db.commit()
	return {
		"khach": kh.name,
		"moi": 1,
		"ghi_chu": "Đã tạo hồ sơ khách %s, nhóm %s, và gắn vào tờ báo giá này. "
		"Giờ chốt thành hợp đồng được rồi." % (kh.name, nhom),
	}


@frappe.whitelist()
def thong_tin_khach(khach):
	_quyen()
	kh = frappe.db.get_value(
		"Customer", khach, ["customer_name", "tax_id", "mobile_no"], as_dict=True
	) or {}
	dc = frappe.db.sql(
		"""select a.address_line1, a.address_line2, a.city, a.state
		from `tabAddress` a join `tabDynamic Link` l on l.parent = a.name
		where l.link_doctype = 'Customer' and l.link_name = %s
		order by a.is_primary_address desc limit 1""",
		khach, as_dict=True,
	)
	dia_chi = ""
	if dc:
		dia_chi = ", ".join([
			x for x in [dc[0].address_line1, dc[0].address_line2, dc[0].city, dc[0].state] if x
		])
	lh = frappe.db.sql(
		"""select c.first_name, c.last_name, c.mobile_no, c.email_id, c.designation
		from `tabContact` c join `tabDynamic Link` l on l.parent = c.name
		where l.link_doctype = 'Customer' and l.link_name = %s
		order by c.is_primary_contact desc limit 1""",
		khach, as_dict=True,
	)
	ten_lh = dt = em = cv = ""
	if lh:
		ten_lh = (" ".join([x for x in [lh[0].first_name, lh[0].last_name] if x])).strip()
		dt = lh[0].mobile_no or ""
		em = lh[0].email_id or ""
		cv = lh[0].designation or ""
	return {
		"ten_khach": kh.get("customer_name") or khach,
		"ma_so_thue": kh.get("tax_id") or "",
		"dia_chi": dia_chi,
		"nguoi_lien_he": ten_lh,
		"chuc_vu": cv,
		"dien_thoai": dt or kh.get("mobile_no") or "",
		"email": em,
	}


# ------------------------------------------------------------------- to in

# Anh Viet 18/08/2026: *"Toan bo hop dong va phu luc bat buoc su dung font
# Arial"*. To bao gia chinh la phu luc cua hop dong nen phai doi theo,
# neu khong thi trong mot tep PDF co hai kieu chu khac nhau.
# Liberation Sans dung lam hang du: no do cung kich thuoc voi Arial va
# co du dau tieng Viet, may nao thieu Arial thi roi vao no chu khong
# roi vao mot phong khong co dau.
from vagabond.phong_chu import NGAN_XEP as PHONG  # noqa: E402
VIEN = "1px solid #c9c4bd"
LA_MA = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]


def _esc(s):
	# To bao gia di kem hop dong lam phu luc, nen theo dung luat trinh bay
	# cua hop dong: khong dau gach dai (anh Viet 18/08/2026). Doi tai day
	# thi ca to in lan thu gui khach deu sach, khong phai nho Sales go lai.
	from vagabond.hop_dong_pdf import don_dau_dai

	return frappe.utils.escape_html(don_dau_dai(s))


def _br(s):
	"""Doi xuong dong thanh <br>, giu nguyen phan con lai da escape."""
	return _esc(s).replace("\n", "<br>")


def _anh_data(url):
	"""Doc anh tren dia may chu thanh data URI de nhung thang vao PDF.

	wkhtmltopdf chay tien trinh rieng, tro src toi duong dan tuong doi thi co
	luc no khong tai duoc - to gui khach ma trong khung anh thi hong. Doc
	thang tu dia chac an hon.
	"""
	if not url:
		return ""
	if str(url).startswith("data:"):
		return url
	try:
		import os

		from frappe.utils import get_files_path

		u = str(url).split("?")[0]
		ten = os.path.basename(u)
		rieng = "/private/" in u
		duong = get_files_path(ten, is_private=rieng)
		if not os.path.exists(duong):
			return ""
		# LUON thu nho lai truoc khi nhung. Anh mon chup marketing hay nang 5
		# toi 6 MB moi tam, bon tam la to PDF hon 20 MB, gui email khong noi.
		# Cot Minh hoa chi in rong 80px nen 520px la du net.
		try:
			import io

			from PIL import Image

			im = Image.open(duong)
			if im.mode in ("RGBA", "LA", "P"):
				nen = Image.new("RGB", im.size, (255, 255, 255))
				im = im.convert("RGBA")
				nen.paste(im, mask=im.split()[-1])
				im = nen
			else:
				im = im.convert("RGB")
			im.thumbnail((520, 520))
			bo = io.BytesIO()
			im.save(bo, "JPEG", quality=84)
			return "data:image/jpeg;base64," + base64.b64encode(bo.getvalue()).decode()
		except Exception:
			pass
		if os.path.getsize(duong) > 2 * 1024 * 1024:
			return ""
		kieu = "image/png" if ten.lower().endswith(".png") else "image/jpeg"
		with open(duong, "rb") as f:
			return "data:%s;base64,%s" % (kieu, base64.b64encode(f.read()).decode())
	except Exception:
		return ""


def _html(name=None, d=None):
	"""To bao gia song ngu, dung khuon to Loan Anh dang gui khach.

	Nhan MOT trong hai: ten to da luu, hoac san cuc du lieu da goi. Duong
	thu hai de xem truoc to dang soan ma chua luu - va vi ca hai duong deu
	di qua dung mot ham nay, cai Loan Anh nhin thay khi xem truoc dung la
	cai se in ra, khong phai mot ban gan giong.
	"""
	if d is None:
		d = chi_tiet(name)
	c = _cd()
	sng = bool(d.get("song_ngu"))
	ra = []
	so_muc = [0]

	def muc(vi, en):
		so_muc[0] += 1
		nhan = LA_MA[min(so_muc[0] - 1, len(LA_MA) - 1)]
		t = "%s. %s%s" % (nhan, _esc(vi), nghieng_xuyet(en, "#555"))
		ra.append(
			'<div style="font-size:13px;font-weight:bold;margin:16px 0 7px;'
			'border-bottom:2px solid #1c1a17;padding-bottom:3px">%s</div>' % t
		)

	# ---------------------------------------------------------------------
	# MOT CUA DUY NHAT sinh chu tieng Anh tren to.
	#
	# Anh Viet 15/08/2026: *"Toan bo phan dich tieng Anh duoc generate ra
	# trong bao gia bat buoc phai dinh dang in nghieng"*.
	#
	# Truoc do co ba cho ghep chu Anh thang vao HTML sau dau gach cheo -
	# muc(), _ben() va dong_cong() - nen chung ra chu dung, trong khi sn()
	# va th() lai nghieng. To in ra nua nghieng nua dung.
	# Nay moi cho in tieng Anh deu phai di qua hai ham nay. Them mau moi o
	# Nhom 5 cung chi phai nho mot luat.
	def nghieng(chu, mau="#666", tho=False):
		"""Mot doan tieng Anh. Rong hoac to chi tieng Viet thi tra ve rong.

		tho = True khi chuoi DA la HTML dung san (vd da thay xuong dong bang
		the ngat dong), luc do khong thoat ky tu nua.
		"""
		if not (sng and str(chu or "").strip()):
			return ""
		return '<i style="font-style:italic;color:%s">%s</i>' % (
			mau, str(chu) if tho else _esc(chu)
		)

	def nghieng_xuyet(chu, mau="#666"):
		"""Dang " / English" dung ngay sau mot cum tieng Viet."""
		o = nghieng(chu, mau)
		return (" / " + o) if o else ""

	def sn(vi, en, co=None, tho=False):
		"""Mot o song ngu: tieng Viet tren, tieng Anh nghieng nho ben duoi.

		tho = True khi vi va en DA la HTML dung san (co the <b>), luc do
		khong escape nua - neu escape thi khach nhin thay chu <b> tren to.
		"""
		lam = (lambda x: str(x or "").replace("\n", "<br>")) if tho else _br
		o = '<div style="font-size:%s">%s</div>' % (co or "10.5px", lam(vi))
		if sng and (en or "").strip():
			# Di qua nghieng() de luat in nghieng chi nam o MOT cho. Chuoi da
			# duoc lam() xu ly xuong dong roi nen truyen vao dang tho.
			o += (
				'<div style="font-size:9.5px;margin-top:1px">%s</div>'
				% nghieng(lam(en), "#666", tho=True)
			)
		return o

	def th(vi, en, rong=None):
		return (
			'<th style="border:%s;padding:5px 6px;background:#f3f0ec;font-size:10px;'
			'font-weight:bold;text-align:center;%s">%s%s</th>'
			% (
				VIEN,
				("width:%s;" % rong) if rong else "",
				_esc(vi),
				('<div style="font-weight:normal">%s</div>' % nghieng(en, "#555"))
				if (sng and en) else "",
			)
		)

	def td(noi, canh="left", dam=False, ngat=True):
		return (
			'<td style="border:%s;padding:4px 6px;font-size:10.5px;text-align:%s;'
			'vertical-align:top;%s%s">%s</td>'
			% (VIEN, canh, "font-weight:bold;" if dam else "",
			   "" if ngat else "white-space:nowrap;", noi)
		)

	# ------------------------------------------------------------ dau to
	ra.append(
		'<div style="font-family:%s;color:#1c1a17;font-size:11px;line-height:1.4">' % PHONG
	)
	ra.append(
		'<table style="width:100%;border:none;border-collapse:collapse"><tr>'
		'<td style="border:none;width:42%;vertical-align:middle">'
		'<img src="/files/vagabond_logo_print.png" width="145" height="60" '
		'style="width:145px !important;height:60px !important;object-fit:contain"></td>'
		'<td style="border:none;text-align:right;vertical-align:middle;font-size:9px;'
		'color:#444;line-height:1.5">'
		'<b style="font-size:10px;color:#1c1a17">' + _esc(c["ten_ban"]) + "</b><br>"
		"MST: " + _esc(c["mst_ban"]) + "<br>"
		+ _esc(c["dia_chi_ban"]) + "<br>" + _esc(c["web_ban"])
		+ "</td></tr></table>"
	)
	# Anh Viet 15/08/2026: doi "BANG BAO GIA SAN PHAM" thanh "THU BAO GIA",
	# va "Production Price Quotation" thanh "Price Quotation". "Bang" nghe
	# nhu mot to liet ke hang, "Thu" dat dung vi the mot loi moi hop tac.
	# Anh da duyet viec cac to cu in lai cung mang tieu de moi: day la nhan
	# hien thi, khong dung toi mot con so nao.
	ra.append(
		'<div style="text-align:center;margin:12px 0 3px">'
		'<div style="font-size:18px;font-weight:bold;letter-spacing:1px">%s</div>%s%s</div>'
		% (
			"THƯ BÁO GIÁ",
			('<div style="font-size:11px">%s</div>' % nghieng("Price Quotation", "#555"))
			if sng else "",
			('<div style="font-size:12px;margin-top:4px">%s</div>' % sn(d["ten"], d.get("ten_en"), "12px"))
			if d.get("ten") else "",
		)
	)
	hl = d.get("hieu_luc_ngay") or 30
	ra.append(
		'<table style="width:100%%;border-collapse:collapse;margin-top:8px">'
		"<tr>%s%s</tr><tr>%s</tr></table>"
		% (
			td(sn("Mã báo giá: <b>%s</b>" % _esc(d["name"]), "Quotation No.", tho=True)),
			td(sn("Ngày báo giá: <b>%s</b>" % _ngay_vn(d["ngay_bao_gia"]), "Date", tho=True)),
			'<td colspan="2" style="border:%s;padding:4px 6px;font-size:10.5px">%s</td>'
			% (VIEN, sn(
				"Báo giá có hiệu lực trong vòng %d ngày kể từ ngày báo giá (đến hết %s)."
				% (hl, _ngay_vn(d["hieu_luc_den"])),
				"This quotation is valid for %d days from the date of issue." % hl,
			)),
		)
	)
	if (d.get("loi_mo") or "").strip():
		ra.append(
			'<div style="border:%s;padding:8px 10px;margin-top:8px;background:#faf8f5">%s</div>'
			% (VIEN, sn(d["loi_mo"], d.get("loi_mo_en")))
		)

	# --------------------------------------------- I. Thong tin dai dien
	muc("Thông tin đại diện", "Representative Information")
	def _ben(nhan_vi, nhan_en, ds):
		o = ['<div style="font-weight:bold;font-size:10.5px;margin-bottom:3px">%s%s</div>'
			 % (_esc(nhan_vi), nghieng_xuyet(nhan_en, "#555"))]
		for nvi, nen, gt in ds:
			if not (gt or "").strip():
				continue
			o.append(
				'<div style="font-size:10px;margin-top:2px"><span style="color:#666">%s%s:</span> '
				'<b>%s</b></div>' % (_esc(nvi), nghieng_xuyet(nen), _esc(gt))
			)
		return "".join(o)

	mua = _ben("Bên mua", "Buyer", [
		("Đơn vị", "Company", d.get("ten_khach")),
		("Mã số thuế", "Tax code", d.get("ma_so_thue")),
		("Đại diện", "Representative", d.get("nguoi_lien_he")),
		("Chức vụ", "Title", d.get("chuc_vu")),
		("Địa chỉ", "Address", d.get("dia_chi")),
		("Điện thoại", "Tel", d.get("dien_thoai")),
		("Email", "Email", d.get("email")),
	])
	ban = _ben("Bên bán", "Seller", [
		("Đơn vị", "Company", c["ten_ban"]),
		("Mã số thuế", "Tax code", c["mst_ban"]),
		("Đại diện", "Representative", d.get("ten_nguoi_lap_in")),
		("Chức vụ", "Title", d.get("chuc_vu_lap")),
		("Địa chỉ", "Address", c["dia_chi_ban"]),
		("Điện thoại", "Tel", d.get("dt_nguoi_lap")),
		("Email", "Email", d.get("email_lap")),
	])
	ra.append(
		'<table style="width:100%%;border-collapse:collapse"><tr>'
		'<td style="border:%s;padding:7px 9px;width:50%%;vertical-align:top">%s</td>'
		'<td style="border:%s;padding:7px 9px;width:50%%;vertical-align:top">%s</td>'
		"</tr></table>" % (VIEN, mua, VIEN, ban)
	)

	# ------------------------------------------------ II. Menu de xuat
	mons = [x for x in d["dong"] if (x.get("loai") or "Món") == "Món"]
	co_menu = any(
		(x.get("mo_ta") or x.get("hinh") or x.get("di_ung_vi") or x.get("kich_thuoc"))
		for x in mons
	)
	if mons and co_menu:
		muc("Các món đề xuất", "Proposed Menu")
		ra.append('<table style="width:100%;border-collapse:collapse">')
		ra.append(
			"<tr>" + th("No.", "", "30px") + th("Tên món", "Name")
			+ th("Mô tả", "Description") + th("Danh mục", "Category")
			+ th("Dị ứng", "Allergen") + th("Kích thước", "Size", "62px")
			+ th("Minh hoạ", "Image", "88px") + "</tr>"
		)
		for i, x in enumerate(mons, 1):
			anh = _anh_data(x.get("hinh"))
			o_anh = (
				'<img src="%s" style="width:80px;height:auto;max-height:70px;'
				'object-fit:contain">' % anh
			) if anh else '<span style="color:#bbb;font-size:9px">-</span>'
			ra.append(
				"<tr>" + td(str(i), "center") + td(sn(x["ten_mon"], x.get("ten_en")))
				+ td(sn(x.get("mo_ta"), x.get("mo_ta_en")))
				+ td(sn(x.get("danh_muc_vi"), x.get("danh_muc_en")))
				+ td(sn(x.get("di_ung_vi"), x.get("di_ung_en")))
				+ td(_esc(x.get("kich_thuoc")), "center")
				+ td(o_anh, "center") + "</tr>"
			)
		ra.append("</table>")

	# --------------------------------------------- III. Bao gia tam tinh
	muc("Báo giá tạm tính", "Estimated Quotation")
	ghi_vat = (
		"Đơn giá đã bao gồm VAT."
		if d.get("gia_da_gom_vat") else "Đơn giá chưa bao gồm VAT."
	)
	ghi_vat_en = (
		"Unit prices include VAT."
		if d.get("gia_da_gom_vat") else "Unit prices exclude VAT."
	)
	ra.append('<div style="margin-bottom:4px">%s</div>' % sn(ghi_vat, ghi_vat_en, "10px"))
	ra.append('<table style="width:100%;border-collapse:collapse">')
	co_ck = any(flt(x["chiet_khau"]) for x in d["dong"])
	ra.append(
		"<tr>" + th("No.", "", "30px") + th("Hạng mục", "Description")
		+ th("Đơn giá", "Unit price", "92px") + th("Số lượng", "Qty", "58px")
		+ (th("CK", "Disc.", "44px") if co_ck else "")
		+ th("Thành tiền", "Amount", "104px") + "</tr>"
	)
	for i, x in enumerate(d["dong"], 1):
		o = "<tr>" + td(str(i), "center") + td(sn(x["ten_mon"], x.get("ten_en")))
		o += td(_tien_vn(x["don_gia"]), "right", ngat=False)
		o += td(
			_tien_vn(x["so_luong"]) + (" " + _esc(x.get("dvt")) if x.get("dvt") else ""),
			"center", ngat=False,
		)
		if co_ck:
			if not flt(x["chiet_khau"]):
				o += td("-", "center")
			elif (x.get("kieu_ck") or "") == CK_TIEN:
				o += td(_tien_vn(x["chiet_khau"]), "center", ngat=False)
			else:
				o += td("%g%%" % flt(x["chiet_khau"]), "center")
		o += td(_tien_vn(x["thanh_tien"]), "right", dam=True, ngat=False) + "</tr>"
		ra.append(o)

	so_cot = 5 + (1 if co_ck else 0)

	def dong_cong(vi, en, tien, dam=False):
		return (
			'<tr><td colspan="%d" style="border:%s;padding:5px 6px;text-align:right;'
			'font-size:%s;%s">%s</td>'
			'<td style="border:%s;padding:5px 6px;text-align:right;white-space:nowrap;'
			'font-size:%s;%s">%s</td></tr>'
			% (
				so_cot - 1, VIEN, "11px" if dam else "10.5px",
				"font-weight:bold;" if dam else "",
				(_esc(vi) + nghieng_xuyet(en, "#555")),
				VIEN, "12px" if dam else "10.5px",
				"font-weight:bold;" if dam else "", _tien_vn(tien),
			)
		)

	_kiem_to_khop(d)
	if (flt(d["chiet_khau_tien"]) or flt(d["phi_giao"]) or flt(d["thue_tien"])
			or d.get("tom_tat_thue")):
		ra.append(dong_cong("Cộng tiền hàng", "Subtotal", d["tam_tinh"]))
	if flt(d["chiet_khau_tien"]):
		# In dung kieu dang dung. Chiet khau theo so tien ma in ra "%" thi
		# khach doc so 500000% - buon cuoi va mat uy tin.
		nhan_ck = ("Chiết khấu" if (d.get("kieu_ck") or "") == CK_TIEN
		           else "Chiết khấu %g%%" % flt(d["chiet_khau_pt"]))
		ra.append(dong_cong(nhan_ck, "Discount", -flt(d["chiet_khau_tien"])))
	if flt(d["phi_giao"]):
		ra.append(dong_cong("Phí giao hàng", "Delivery fee", d["phi_giao"]))
	# Ba dong khach hay hoi (anh Viet 18/08/2026): *"nhieu khach ho yeu cau
	# so tien truoc thue va so tien sau thue, so tien thue"*. Tron nhieu muc
	# thue thi in them mot dong cho tung muc.
	tt = d.get("tom_tat_thue") or None
	if tt:
		# TEN BIEN: co y KHONG dat la "muc".
		#
		# Nghiem thu tren site that 19/08/2026 vo ngay o day: trong ham nay
		# da co san mot ham ten muc() de in tua de tung muc cua to bao gia.
		# Dat bien trung ten la ghi de len ham do, va dong muc("Quy trinh
		# van hanh"...) phia duoi nem TypeError: 'list' object is not
		# callable. Ca to bao gia va ca phu luc cua hop dong tra ve 500.
		muc_thue = [m for m in tt["theo_muc"] if flt(m["tien_hang"]) or flt(m["tien_thue"])]
		ra.append(dong_cong("Cộng tiền hàng chưa thuế", "Subtotal excluding VAT", tt["tien_hang"]))
		if len(muc_thue) > 1:
			for m in muc_thue:
				ra.append(dong_cong(
					"Thuế GTGT %g%% trên %s" % (flt(m["thue_pt"]), _tien_vn(m["tien_hang"])),
					"VAT %g%%" % flt(m["thue_pt"]), m["tien_thue"],
				))
			ra.append(dong_cong("Cộng tiền thuế GTGT", "Total VAT", tt["tien_thue"]))
		else:
			ra.append(dong_cong(
				"Thuế GTGT %g%%" % (flt(muc_thue[0]["thue_pt"]) if muc_thue else 0),
				"VAT", tt["tien_thue"]
			))
	elif flt(d["thue_tien"]):
		ra.append(dong_cong("Thuế GTGT %g%%" % flt(d["thue_pt"]), "VAT", d["thue_tien"]))
	ra.append(dong_cong("TỔNG TIỀN TẠM TÍNH", "Estimated Total", d["tong_cong"], dam=True))
	ra.append("</table>")
	ra.append(
		'<div style="margin-top:5px;font-size:10.5px">%s</div>'
		% sn("Bằng chữ: <i>%s</i>" % _esc(_chu_so_tien(d["tong_cong"])), "", tho=True)
	)

	# ----------------------------------------------- IV. Dich vu them
	if d.get("dich_vu"):
		muc("Dịch vụ thêm", "Additional Services")
		ra.append('<table style="width:100%;border-collapse:collapse">')
		ra.append(
			"<tr>" + th("No.", "", "30px") + th("Hạng mục", "Description")
			+ th("Đơn giá", "Unit price", "190px") + "</tr>"
		)
		for i, x in enumerate(d["dich_vu"], 1):
			ra.append(
				"<tr>" + td(str(i), "center") + td(sn(x["ten_vi"], x.get("ten_en")))
				+ td(sn(x.get("gia_vi"), x.get("gia_en"))) + "</tr>"
			)
		ra.append("</table>")

	# --------------------------------------------- V. Quy trinh van hanh
	if d.get("moc"):
		muc("Quy trình vận hành", "Operation Process")
		ra.append('<table style="width:100%;border-collapse:collapse">')
		ra.append(
			"<tr>" + th("Mốc thời gian", "Timeline", "150px")
			+ th("Nội dung", "Action") + th("Trách nhiệm", "Responsibility", "120px") + "</tr>"
		)
		for x in d["moc"]:
			ra.append(
				"<tr>" + td(sn(x["moc_vi"], x.get("moc_en")))
				+ td(sn(x.get("noi_dung_vi"), x.get("noi_dung_en")))
				+ td(_esc(x.get("trach_nhiem")), "center") + "</tr>"
			)
		ra.append("</table>")

	def khoi(vi_key, en_key, nhan_vi, nhan_en):
		if not (d.get(vi_key) or "").strip():
			return
		muc(nhan_vi, nhan_en)
		ra.append(
			'<div style="border:%s;padding:7px 9px">%s</div>'
			% (VIEN, sn(d[vi_key], d.get(en_key)))
		)

	khoi("yeu_cau_vi", "yeu_cau_en", "Yêu cầu vận hành", "Operation Requirements")

	# ------------------------------------------ Dieu khoan thanh toan
	muc("Điều khoản thanh toán", "Payment Terms")
	from vagabond import tai_khoan

	try:
		qr = tai_khoan.tk_phieu_no() or {}
	except Exception:
		qr = {}
	tien_qr = flt(d["dat_coc_tien"]) or flt(d["tong_cong"])
	# Noi dung chuyen khoan: ma to la thu duy nhat can de doi soat. Ten khach
	# chi them khi VUA HET, cat lung chung nhin rat au tren to gui khach.
	_ten_kh = str(d.get("ten_khach") or "").strip()
	nd_qr = d["name"] + ((" " + _ten_kh) if len(_ten_kh) <= 22 else "")
	anh_qr = _qr_data_uri(qr, tien_qr, nd_qr) if qr.get("stk") else ""
	tt = []
	if (d.get("thanh_toan") or "").strip():
		tt.append(sn(d["thanh_toan"], d.get("thanh_toan_en")))
	if flt(d["dat_coc_tien"]):
		tt.append(
			'<div style="margin-top:5px;font-size:11.5px"><b>%s: %s đ</b></div>'
			% (
				"Số tiền đặt cọc (%g%%)" % flt(d["dat_coc_pt"])
				+ (" / Deposit" if sng else ""),
				_tien_vn(d["dat_coc_tien"]),
			)
		)
	if qr.get("stk"):
		tt.append(
			'<div style="margin-top:6px;font-size:10.5px;line-height:1.6">'
			'<b>%s</b><br>%s<br>%s: <b>%s</b> &nbsp; %s: %s<br>%s: <b>%s</b></div>'
			% (
				_esc(c["ten_ban"]),
				_esc(TEN_NGAN_HANG_DAY_DU.get(qr.get("bank") or "", qr.get("bank") or "")),
				"Số tài khoản" + (" / Account No." if sng else ""),
				_esc(qr.get("stk") or ""),
				"Số tiền" + (" / Amount" if sng else ""),
				_tien_vn(tien_qr) + " đ",
				"Nội dung" + (" / Reference" if sng else ""),
				_esc(nd_qr),
			)
		)
	o_qr = (
		'<td style="border:none;width:130px;text-align:center;vertical-align:top;'
		'padding-left:10px"><img src="%s" width="118" height="118" '
		'style="width:118px !important;height:118px !important">'
		'<div style="font-size:8.5px;color:#666;margin-top:2px">%s</div></td>'
		% (anh_qr, "Quét mã để chuyển khoản" + ("<br>Scan to pay" if sng else ""))
	) if anh_qr else ""
	ra.append(
		'<table style="width:100%%;border:%s;border-collapse:collapse"><tr>'
		'<td style="border:none;padding:7px 9px;vertical-align:top">%s</td>%s</tr></table>'
		% (VIEN, "".join(tt), o_qr)
	)

	khoi("chinh_sach_huy_vi", "chinh_sach_huy_en",
		 "Chính sách huỷ và thay đổi", "Cancellation & Amendment Policy")
	khoi("luu_y_vi", "luu_y_en", "Lưu ý", "Notes")

	them = []
	for nvi, nen, gt in (
		("Thời gian và địa điểm giao hàng", "Delivery", d.get("giao_hang")),
		("Quy cách đóng gói", "Packaging", d.get("dong_goi")),
		("Ghi chú", "Notes", d.get("ghi_chu")),
	):
		if (gt or "").strip():
			them.append(
				'<div style="margin-bottom:4px"><b>%s%s:</b> %s</div>'
				% (_esc(nvi), (" / " + _esc(nen)) if sng else "", _br(gt))
			)
	if them:
		muc("Nội dung khác", "Other Details")
		ra.append('<div style="border:%s;padding:7px 9px;font-size:10.5px">%s</div>'
				  % (VIEN, "".join(them)))

	# ------------------------------------------------------------ chu ky
	ngay = getdate(d["ngay_bao_gia"]) if d.get("ngay_bao_gia") else getdate(nowdate())
	ra.append(
		'<div style="text-align:right;margin-top:16px;font-size:10.5px">%s</div>'
		% sn(
			"Thành phố Hồ Chí Minh, ngày %02d tháng %02d năm %d" % (ngay.day, ngay.month, ngay.year),
			"Ho Chi Minh City, %s %d, %d" % (ngay.strftime("%B"), ngay.day, ngay.year),
		)
	)
	ra.append(
		'<table style="width:100%%;border:none;border-collapse:collapse;margin-top:8px">'
		'<tr><td style="border:none;width:50%%;text-align:center;font-size:10.5px">'
		"<b>Đại diện bên mua%s</b>"
		'<div style="font-size:9px;color:#666">(Ký, ghi rõ họ tên)</div>'
		'<div style="height:58px"></div>_____________________</td>'
		'<td style="border:none;width:50%%;text-align:center;font-size:10.5px">'
		"<b>Đại diện bên bán%s</b>"
		'<div style="font-size:9px;color:#666">(Ký, ghi rõ họ tên)</div>'
		'<div style="height:58px"></div>_____________________'
		'<div style="font-weight:bold;margin-top:3px">%s</div>'
		'<div style="font-size:9.5px;color:#555">%s</div></td></tr></table>'
		% (
			" / Buyer" if sng else "", " / Seller" if sng else "",
			_esc(d.get("ten_nguoi_lap_in")), _esc(d.get("chuc_vu_lap")),
		)
	)
	ra.append(
		'<div style="margin-top:10px;font-size:9px;color:#777;text-align:center">%s</div>'
		% (
			"Khi ký vào bảng báo giá này, hai bên đồng ý với toàn bộ điều khoản nêu trên."
			+ ("<br><i>By signing, both parties agree to the terms and conditions stated "
			   "in this quotation.</i>" if sng else "")
		)
	)
	ra.append("</div>")
	return "".join(ra)


@frappe.whitelist()
def xem_truoc(name):
	_quyen()
	return {"html": _html(name)}


@frappe.whitelist()
def xem_truoc_nhap(du_lieu=None, name=None):
	"""Ban in cua to DANG SOAN, chua luu.

	Anh Viet 16/08/2026: *"De Sales xem truoc ban in cua mau template hien
	tai truoc khi xuat file that gui khach. Tuyet doi thao tac nay khong
	duoc kich hoat ham tao phien ban hay luong gui email"*.

	BA DIEU HAM NAY KHONG LAM, va deu la co y:
	  - Khong goi doc.save, nen khong sinh phien ban, khong doi trang thai,
	    khong dung toi mot dong nao trong co so du lieu.
	  - Khong goi frappe.sendmail.
	  - Khong dung _chan_dong_bang: xem truoc mot ban lich su phai duoc,
	    chi sua no moi bi cam.

	Con so trong to xem truoc do MAY CHU tinh lai bang _tinh (QT-19), nen
	no dung bang con so se in ra chu khong phai con so app dang giu.
	"""
	_quyen()
	if not du_lieu:
		if not name:
			frappe.throw("Chưa có gì để xem trước. Nhập vài dòng rồi thử lại nhé.")
		return {"html": _html(name), "name": name}

	d = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
	# new_doc chi dung trong bo nho. Khong insert, khong save.
	tam = frappe.new_doc(DT)
	tam.nguoi_lap = frappe.session.user
	_do_vao(tam, d)
	_tinh(tam)
	goi = _goi(tam)
	# Doc chua luu thi khong co ma. Ghi ro la ban nhap chu khong de trong,
	# vi o trong tren to in nhin nhu loi.
	goi["name"] = d.get("name") or "(bản nháp, chưa lưu)"
	return {"html": _html(d=goi), "name": goi["name"]}


def _ten_tep(name):
	ten_kh = frappe.db.get_value(DT, name, "ten_khach") or ""
	from vagabond.danh_muc import khong_dau

	goi = khong_dau(ten_kh).replace(" ", "-")[:40] if ten_kh else ""
	return "%s%s" % (name, ("-" + goi) if goi else "")


@frappe.whitelist()
def xuat_pdf(name):
	"""To bao gia ra PDF A4 doc de gui khach."""
	_quyen()
	from frappe.utils.pdf import get_pdf
	from vagabond.phong_chu import bao_dam_phong

	bao_dam_phong()

	# To bao gia di kem hop dong lam phu luc nen phai dung CHUNG mot phong
	# voi hop dong. Quet bang dau sao cho moi the, xem chu thich dai o
	# hop_dong_pdf.khung_style.
	from vagabond.hop_dong_pdf import khung_style

	khung = (
		"<html><head><meta charset='utf-8'>"
		"<style>@page{margin:11mm 9mm}body{margin:0}" + khung_style(PHONG) +
		"table{page-break-inside:auto}tr{page-break-inside:avoid}</style>"
		"</head><body>" + _html(name) + "</body></html>"
	)
	noi_dung = get_pdf(khung, options={"page-size": "A4", "orientation": "Portrait"})
	return {
		"ten_file": "Bao-gia-%s.pdf" % _ten_tep(name),
		"b64": base64.b64encode(noi_dung).decode(),
		"kieu": "application/pdf",
	}


@frappe.whitelist()
def xem_nguoi_nhan(name, email=None):
	"""Ai se nhan thu nay. Cho bang xac nhan TRUOC khi bam gui.

	Gui nham cho ca phong ban ben khach la loai loi khong rut lai duoc, nen
	nguoi bam phai nhin thay DU tung dia chi, ke ca cac dia chi noi bo duoc
	them tu dong. Ham nay dung DUNG phep loc cua gui_email.
	"""
	_quyen()
	cd = _cd()
	nhan, sai = _tach_email(email or frappe.db.get_value(DT, name, "email") or "")
	cc, _ = _tach_email(", ".join(cd["cc_noi_bo"]))
	da_co = {x.lower() for x in nhan}
	toi_la = (frappe.session.user or "").strip().lower()
	cc = [x for x in cc if x.lower() not in da_co and x.lower() != toi_la]
	tu = (cd.get("email_gui") or "").strip()
	co_that = bool(
		tu and frappe.db.exists("Email Account", {"email_id": tu, "enable_outgoing": 1})
	)
	return {
		"nhan": nhan, "sai": sai, "cc": cc,
		"tu": tu if co_that else "", "tu_khai": tu, "tu_co_that": 1 if co_that else 0,
	}


@frappe.whitelist()
def gui_email(name, email=None, loi_nhan=None):
	"""Gui to bao gia PDF sang email khach, dong thoi doi trang thai."""
	_quyen(sua=True)
	doc = frappe.get_doc(DT, name)
	cd = _cd()

	# Kiem o MAY CHU chu khong tin app (QT-19). Gui nham cho ca phong ban ben
	# khach la loai loi khong rut lai duoc, nen tha chan som con hon.
	nhan, sai = _tach_email(email or doc.email or "")
	if sai:
		frappe.throw(
			"Địa chỉ này chưa đúng dạng email: %s. Anh chị sửa lại rồi gửi "
			"giúp em. Nhiều email thì ngăn nhau bằng dấu phẩy."
			% ", ".join(sai)
		)
	if not nhan:
		frappe.throw("Chưa có email khách để gửi. Nhập email vào rồi gửi lại nhé.")

	# CC noi bo. Bo ai da nam trong danh sach nhan chinh de khong ai nhan hai
	# ban, va bo chinh nguoi dang bam gui vi Frappe da luu ban gui vao ho so
	# chung tu roi.
	cc, _ = _tach_email(", ".join(cd["cc_noi_bo"]))
	da_co = {x.lower() for x in nhan}
	toi_la = (frappe.session.user or "").strip().lower()
	cc = [x for x in cc if x.lower() not in da_co and x.lower() != toi_la]

	tep = xuat_pdf(name)
	than = (
		'<div style="font-family:Arial,Liberation Sans,Helvetica,sans-serif;font-size:14px;'
		'line-height:1.6;color:#1c1a17">'
		"<p>Kính gửi Quý khách %s,</p>"
		"<p>The Vagabond Pâtisserie trân trọng gửi Quý khách bảng báo giá "
		"<b>%s</b> theo nội dung trao đổi. Chi tiết vui lòng xem tệp PDF đính kèm.</p>"
		"<p>Báo giá có hiệu lực đến hết ngày <b>%s</b>. Tổng giá trị tạm tính là "
		"<b>%s đ</b>.</p>%s"
		"<p>Quý khách cần điều chỉnh số lượng hoặc quy cách, xin vui lòng phản hồi "
		"lại email này hoặc liên hệ trực tiếp với chúng tôi.</p>"
		"<p>Trân trọng,<br><b>%s</b><br>%s<br>The Vagabond Pâtisserie<br>%s</p></div>"
	) % (
		_esc(doc.ten_khach or ""), _esc(doc.ten or ""),
		_ngay_vn(doc.hieu_luc_den) or "...", _tien_vn(doc.tong_cong),
		("<p>%s</p>" % _esc(loi_nhan)) if (loi_nhan or "").strip() else "",
		_esc(doc.ten_nguoi_lap_in or ""), _esc(doc.chuc_vu_lap or ""),
		_esc(_cd()["web_ban"]),
	)
	gui = {
		"recipients": nhan,
		"cc": cc or None,
		"subject": "Báo giá %s - The Vagabond Pâtisserie" % doc.name,
		"message": than,
		"attachments": [
			{"fname": tep["ten_file"], "fcontent": base64.b64decode(tep["b64"])}
		],
		"reference_doctype": DT,
		"reference_name": doc.name,
		"now": True,
	}
	# Chi ep dia chi gui khi hop thu do CO THAT va DANG BAT gui di. Khai bua
	# mot dia chi chua dung se lam ca lenh gui chet, tuc Loan Anh khong gui
	# duoc bao gia nao chi vi mot o cau hinh - khong dang.
	tu = (cd.get("email_gui") or "").strip()
	if tu and frappe.db.exists(
		"Email Account", {"email_id": tu, "enable_outgoing": 1}
	):
		gui["sender"] = tu
	elif tu:
		frappe.log_error(
			"Chua co Email Account bat gui di cho %s, dung hop thu mac dinh." % tu,
			"Vagabond: bao gia gui bang hop thu mac dinh",
		)

	frappe.sendmail(**gui)

	if doc.trang_thai == "Nháp":
		frappe.db.set_value(DT, name, "trang_thai", "Đã gửi khách")
	if not doc.email:
		frappe.db.set_value(DT, name, "email", ", ".join(nhan))
	return {"ok": 1, "toi": nhan, "cc": cc, "tu": gui.get("sender") or ""}


@frappe.whitelist()
def goi_y_hop_dong(name):
	"""Do san moi o cua man hinh tao hop dong de user chi viec xem lai.

	Anh Viet 18/08/2026: *"He thong can tu dong generate ra mot ma so hop
	dong goi y de dien san vao o input, user chi can xem lai hoac an chon
	cho nhanh thay vi go tay"*.

	Ba o nguoi ky do san nhung KHONG lay ten Sales:
	  - Ben A lay nguoi lien he ghi tren to bao gia, da bo Ms./Mr.
	  - Ben B lay dai dien khai trong Cai dat bao gia (Giam doc cong ty).
	User van sua duoc ca ba o, may chi do san chu khong chot.
	"""
	_quyen()
	from vagabond.hop_dong_pdf import (
		_ben_b,
		_bo_xung_ho as _bo_ho,
		so_hop_dong as _sinh_so,
		viet_tat_khach,
	)

	d = frappe.get_doc(DT, name)
	ngay = nowdate()
	b = _ben_b()
	# Nguoi ky ben B lay tu HOP DONG GAN NHAT da dien, khong lay o "dai
	# dien" trong Cai dat bao gia.
	#
	# Nghiem thu 18/08/2026 bat duoc: o do dang ghi "Loan Anh / Sales
	# Manager". Anh Viet: *"khong duoc lay mac dinh ten cua ban Sales"*.
	# Nho lai nguoi ky lan truoc thi lan dau phai go tay, tu lan hai tro di
	# may do san, va do san bang chinh cai NGUOI TA DA CHON chu khong phai
	# cai may doan.
	ky_b = frappe.db.sql(
		"""select nguoi_ky_b, chuc_vu_ky_b, dt_ky_b, email_ky_b
		from `tabHop Dong Ban Hang`
		where ifnull(nguoi_ky_b, '') != '' order by creation desc limit 1""",
		as_dict=True,
	)
	ky_b = ky_b[0] if ky_b else {}
	# Cai dat bao gia dung TRUOC hop dong gan nhat: cho do la cho anh Viet
	# khai co chu dich, con hop dong gan nhat chi la thoi quen.
	if (b.get("ky_ten") or "").strip():
		ky_b = {
			"nguoi_ky_b": b.get("ky_ten"), "chuc_vu_ky_b": b.get("ky_chuc_vu"),
			"dt_ky_b": b.get("ky_dt"), "email_ky_b": b.get("ky_email"),
		}
	return {
		"ngay": ngay,
		# Tra ca viet tat va ma loai de man hinh dung lai so khi user doi
		# ngay ky, khong phai goi lai may chu chi de doi tam chu so dau.
		"viet_tat": viet_tat_khach(d.ten_khach or d.khach_hang or ""),
		"loai": "HDMB",
		"so_goi_y": _sinh_so(ngay, d.ten_khach or d.khach_hang or ""),
		"ten_khach": d.ten_khach or "",
		"nguoi_ky_a": _bo_ho(d.nguoi_lien_he or ""),
		"chuc_vu_ky_a": (d.chuc_vu or "").strip() or "Giám đốc",
		"dt_ky_a": d.dien_thoai or "",
		"email_ky_a": d.email or "",
		"nguoi_ky_b": _bo_ho(ky_b.get("nguoi_ky_b") or ""),
		"chuc_vu_ky_b": (ky_b.get("chuc_vu_ky_b") or "").strip() or "Giám đốc",
		"dt_ky_b": ky_b.get("dt_ky_b") or "",
		"email_ky_b": ky_b.get("email_ky_b") or "",
	}


@frappe.whitelist()
def tao_hop_dong(name, so_hop_dong=None, ngay_ky=None, ngay_su_kien=None,
                 nguoi_ky_a=None, chuc_vu_ky_a=None, dt_ky_a=None, email_ky_a=None,
                 nguoi_ky_b=None, chuc_vu_ky_b=None, dt_ky_b=None, email_ky_b=None):
	"""Bao gia khach duyet thi bam mot nut ra Hop dong ban hang."""
	_quyen(sua=True)
	doc = frappe.get_doc(DT, name)
	_chan_dong_bang(doc, "lên hợp đồng")
	if doc.hop_dong and frappe.db.exists("Hop Dong Ban Hang", doc.hop_dong):
		frappe.throw("Báo giá này đã lên hợp đồng %s rồi." % doc.hop_dong)
	if not doc.khach_hang:
		frappe.throw(
			"Hợp đồng phải gắn với một khách hàng có trong hệ thống. "
			"Mở báo giá, chọn lại khách ở ô Khách hàng rồi thử lại nhé."
		)
	noi_dung = "\n".join(
		"%d. %s - %s %s x %s đ = %s đ"
		% (i, x.ten_mon or "", _tien_vn(x.so_luong), x.dvt or "",
		   _tien_vn(x.don_gia), _tien_vn(x.thanh_tien))
		for i, x in enumerate(doc.dong, 1)
	)
	if doc.thanh_toan:
		noi_dung += "\nĐiều kiện thanh toán: %s" % doc.thanh_toan
	if doc.giao_hang:
		noi_dung += "\nGiao hàng: %s" % doc.giao_hang
	# Chup lai (snapshot) thong tin Ben A tai thoi diem chot, khong tro sang
	# ho so khach hang.
	#
	# Sang nam khach doi ten cong ty hay doi nguoi dai dien thi to hop dong
	# da ky van phai doc ra dung cai da ky - do la ca diem cua mot to phap
	# ly. Bao gia cung da chup san cac o nay nen chi viec chep sang.
	from vagabond.hop_dong_pdf import (
		_bo_xung_ho as _bo_ho,
		chia_hai_dot,
		so_hop_dong as _sinh_so,
	)

	ngay = ngay_ky or nowdate()
	so = (so_hop_dong or "").strip() or _sinh_so(ngay, doc.ten_khach or doc.khach_hang)
	coc_pt = flt(doc.dat_coc_pt)
	coc_tien = chia_hai_dot(doc.tong_cong, coc_pt)[0]
	hd = frappe.get_doc({
		"doctype": "Hop Dong Ban Hang",
		"ten": doc.ten,
		"so_hop_dong": so,
		"loai": "B2B sỉ",
		"khach_hang": doc.khach_hang,
		"ngay_ky": ngay,
		"ngay_su_kien": ngay_su_kien or None,
		"gia_tri": flt(doc.tong_cong),
		"mo_ta": noi_dung,
		"ghi_chu": "Lập từ báo giá %s" % doc.name,
		"bao_gia": doc.name,
		"ten_khach": doc.ten_khach or "",
		"ma_so_thue": doc.ma_so_thue or "",
		"dia_chi": doc.dia_chi or "",
		"dai_dien": doc.nguoi_lien_he or "",
		"chuc_vu": doc.chuc_vu or "",
		"dien_thoai": doc.dien_thoai or "",
		"email": doc.email or "",
		"dat_coc_pt": coc_pt,
		"dat_coc_tien": coc_tien,
		"ngay_dot1": 3,
		"ngay_dot2": 3,
		"thoi_gian_giao": doc.giao_hang or "",
		# Nguoi ky KHONG mac dinh lay ten Sales (anh Viet 18/08/2026):
		# nguoi ky thuong la Giam doc chu khong phai ban lam bao gia. Man
		# hinh hoi rieng, va o day chi nhan lai. De trong thi de trong,
		# khong bia.
		"nguoi_ky_a": _bo_ho(nguoi_ky_a),
		"chuc_vu_ky_a": (chuc_vu_ky_a or "").strip(),
		"dt_ky_a": (dt_ky_a or "").strip(),
		"email_ky_a": (email_ky_a or "").strip(),
		"nguoi_ky_b": _bo_ho(nguoi_ky_b),
		"chuc_vu_ky_b": (chuc_vu_ky_b or "").strip(),
		"dt_ky_b": (dt_ky_b or "").strip(),
		"email_ky_b": (email_ky_b or "").strip(),
	})
	hd.insert(ignore_permissions=True)
	frappe.db.set_value(DT, name, {"hop_dong": hd.name, "trang_thai": "Đã lên hợp đồng"})
	return hd.name


# ---------------------------------------------------------- mau bao gia

# Anh Viet 15/08/2026: *"Thêm tính năng 'Lưu mẫu báo giá' để sau này dùng thì
# áp lên để app tự điền hết các phần thông tin theo mẫu (vì có những hợp đồng
# có quy trình vận hành giống nhau,...)"*.
#
# Mau chinh la mot to bao gia co co la_mau = 1: dung lai toan bo cach luu, cach
# doc, cach sua cua to thuong, khong dung them doctype nao. To co co nay bi an
# khoi danh sach bao gia va khong duoc xuat PDF gui khach.


@frappe.whitelist()
def mau_ds():
	"""Danh sach mau cho bang chon khi sales bam nut lap bao gia moi.

	Tra ve HOP cua hai nguon: bo mau khoi dau khai trong ma nguon, va cac
	mau Loan Anh tu luu lai. Mau trong ma nguon mang ma "goc:<ten>" de
	tu_mau() phan biet duoc no doc tu dau.
	"""
	_quyen()
	ra = [
		{
			"name": "goc:" + ma,
			"ten_mau": m["ten_mau"],
			"mo_ta_mau": m.get("mo_ta_mau") or "",
			"phan_loai": m.get("phan_loai") or "",
			"mau_in": m.get("mau_in") or "",
			"tu_ma_nguon": 1,
		}
		for ma, m in MAU_GOC.items()
	]
	ra += [
		dict(x, tu_ma_nguon=0)
		for x in frappe.get_all(
			DT,
			filters={"la_mau": 1},
			fields=["name", "ten_mau", "ten", "modified", "mo_ta_mau",
					"phan_loai", "mau_in"],
			order_by="ten_mau asc, modified desc",
			limit_page_length=100,
		)
	]
	return {"ds": ra, "mau_in": MAU_IN, "phan_loai": PHAN_LOAI}


@frappe.whitelist()
def mau_luu(name, ten_mau):
	"""Luu mot to dang co thanh mau dung lai."""
	_quyen(sua=True)
	ten_mau = (ten_mau or "").strip()
	if not ten_mau:
		frappe.throw("Đặt tên cho mẫu đã nhé, vd Mẫu trung thu doanh nghiệp.")
	cu = frappe.get_doc(DT, name)
	m = frappe.copy_doc(cu)
	m.la_mau = 1
	m.ten_mau = ten_mau
	m.trang_thai = "Nháp"
	m.hop_dong = None
	# Mau khong giu thong tin khach cua to goc, chi giu khung va cach lam.
	for f in ("khach_hang", "ten_khach", "ma_so_thue", "dia_chi",
			  "nguoi_lien_he", "chuc_vu", "dien_thoai", "email"):
		m.set(f, None)
	# Mau la khung dung lai, khong phai mot vong thuong luong. Khong go bon
	# truong nay thi luu mau tu mot ban da dong bang se de ra mot mau cung
	# mang co dong bang, va khong ai sua duoc mau do.
	_xoa_dau_phien_ban(m)
	m.insert(ignore_permissions=True)
	# mau_in va phan_loai da theo copy_doc sang; khong xoa vi day chinh la
	# thu Loan Anh muon giu lai khi luu mot to dep thanh mau.
	return {"name": m.name, "ten_mau": ten_mau}


@frappe.whitelist()
def mau_xoa(name):
	_quyen(sua=True)
	if not frappe.db.get_value(DT, name, "la_mau"):
		frappe.throw("Đây không phải mẫu.")
	frappe.delete_doc(DT, name, ignore_permissions=True)
	return 1


@frappe.whitelist()
def tu_mau(name_mau):
	"""Khung to moi dien san theo mau: cau chu, dieu khoan, timeline, dich vu
	them va ca cac dong san pham. Chua co khach hang, ngay lay hom nay."""
	_quyen(sua=True)

	# Mau khoi dau khai trong ma nguon. Khong doc CSDL, khong can migrate,
	# va sua cau chu la sua mot cho roi qua sau cong kiem.
	if str(name_mau or "").startswith("goc:"):
		ma = str(name_mau)[4:]
		if ma not in MAU_GOC:
			frappe.throw(
				"Không có mẫu %s. Anh chị chọn lại trong danh sách giúp em." % ma
			)
		m = MAU_GOC[ma]
		d = moi()
		for f, v in m.items():
			if f in ("ten_mau", "mo_ta_mau"):
				continue
			d[f] = v
		# Timeline lay theo Cai dat nhu to trang; mau khoi dau khong doi.
		d["tu_mau"] = m["ten_mau"]
		if d.get("hieu_luc_ngay"):
			d["hieu_luc_den"] = add_days(nowdate(), int(d["hieu_luc_ngay"]))
		return d

	if not frappe.db.get_value(DT, name_mau, "la_mau"):
		frappe.throw("Đây không phải mẫu.")
	m = _goi(frappe.get_doc(DT, name_mau))
	d = moi()
	giu = (
		"ten", "ten_en", "song_ngu", "gia_da_gom_vat", "loi_mo", "loi_mo_en",
		"phan_loai", "mau_in",
		"thanh_toan", "thanh_toan_en", "yeu_cau_vi", "yeu_cau_en",
		"chinh_sach_huy_vi", "chinh_sach_huy_en", "luu_y_vi", "luu_y_en",
		"giao_hang", "dong_goi", "ghi_chu", "chiet_khau_pt", "kieu_ck", "thue_pt",
		"phi_giao", "dat_coc_pt", "hieu_luc_ngay",
	)
	for f in giu:
		if m.get(f) not in (None, ""):
			d[f] = m[f]
	d["dong"] = m.get("dong") or []
	d["dich_vu"] = m.get("dich_vu") or []
	d["moc"] = m.get("moc") or []
	d["tu_mau"] = frappe.db.get_value(DT, name_mau, "ten_mau") or name_mau
	if d.get("hieu_luc_ngay"):
		d["hieu_luc_den"] = add_days(nowdate(), int(d["hieu_luc_ngay"]))
	return d


# ---------------------------------------------------- sua che do thue bi lech


# Moc thoi gian patch #v228 chay tren site that, doc tu Patch Log:
#   vagabond.patches.dong_bo_cau_truc #v228 -> 2026-08-19 13:47:11
# Truoc moc nay tren he KHONG co o "Cach tinh thue", nen khong mot to nao
# co the do NGUOI chon che do "Theo tung dong". To nao mang gia tri do ma
# lap truoc moc thi chac chan la do cot co "default" tu dien vao luc
# Migrate, khong phai y cua ai.
MOC_CO_O_KIEU_THUE = "2026-08-19 13:47:11"


def sua_kieu_thue_bi_dat_mac_dinh():
	"""Tra lai che do thue cho cac to bi cot default ghi de. LAP LAI DUOC.

	Vi sao phai co ham nay
	----------------------
	O "kieu_thue" ra doi o dot v228 va mang "default": "Theo tung dong".
	Khi Frappe Migrate them cot do, MariaDB dien gia tri mac dinh vao MOI
	dong da co. Ca 12 to bao gia dang co tren he, ke ca nhung to lap tu
	14/08, deu bi doi sang che do moi ma khong ai bam gi.

	Cai gia phai tra khong phai ly thuyet. To VGB-PQ-2026-0008 in ra cho
	khach: cong tien hang chua thue 32.086.610, thue GTGT 0%, tong tien
	34.653.539 - ba dong khong the cung dung. Va to VGB-PQ-2026-0007, khi
	Loan Anh bam Luu lan nua, tong tut tu 34.653.539 xuong 32.086.610 vi
	tien thue bien mat khoi tong.

	Ham nay KHONG dung vao mot o tien nao. No chi tra lai dung cai o che do
	ma he thong da tu doi, cho hai nhom to:

	  Nhom mot, to lap TRUOC khi o nay ton tai. Khong the do nguoi chon.
	  Nhom hai, to co con so luu KHONG khop voi che do dang mang. Tinh lai
	           theo che do cu thi khop - tuc luc luu no da chay che do cu.

	Nhom hai la phep thu co suc chung minh: mot to that su duoc luu o che
	do "Theo tung dong" thi tinh lai theo che do do phai ra dung con so da
	luu. Ra lech nghia la no chua bao gio duoc tinh o che do do.
	"""
	ra = {"xem": 0, "sua": [], "bo_qua": 0}
	try:
		ds = frappe.get_all(DT, filters={"kieu_thue": KT_DONG},
		                    fields=["name", "creation"], limit_page_length=0)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "bao_gia: doc danh sach to de sua kieu thue")
		return ra
	for r in ds:
		ra["xem"] += 1
		try:
			doc = frappe.get_doc(DT, r["name"])
		except Exception:
			continue
		vi_sao = ""
		if str(r["creation"]) < MOC_CO_O_KIEU_THUE:
			vi_sao = "tờ lập trước khi ô Cách tính thuế ra đời"
		else:
			bt = bang_thue(
				[{"thanh_tien": flt(d.thanh_tien), "thue_pt": flt(d.thue_pt)}
				 for d in (doc.get("dong") or [])],
				ck_to=flt(doc.chiet_khau_tien),
				phi_giao=flt(doc.phi_giao),
				phi_giao_pt=flt(doc.get("thue_phi_giao_pt")),
				da_gom=1 if doc.gia_da_gom_vat else 0,
			)
			sau_ck = flt(doc.tam_tinh) - flt(doc.chiet_khau_tien)
			cu = (sau_ck + flt(doc.phi_giao)) if doc.gia_da_gom_vat else (
				sau_ck + round(sau_ck * flt(doc.thue_pt) / 100.0, 0) + flt(doc.phi_giao))
			lech_dong = abs(flt(bt["tong_cong"]) - flt(doc.tong_cong))
			lech_to = abs(flt(cu) - flt(doc.tong_cong))
			if lech_dong > 1 and lech_to <= 1:
				vi_sao = ("số đang lưu %s đ khớp cách cũ chứ không khớp cách theo dòng (%s đ)"
				          % (_tien_vn(doc.tong_cong), _tien_vn(bt["tong_cong"])))
		if not vi_sao:
			ra["bo_qua"] += 1
			continue
		try:
			# set_value chu khong save: save se chay lai _tinh va doi con
			# so tien, ma o day em CHI duoc phep tra lai o che do.
			frappe.db.set_value(DT, r["name"], "kieu_thue", KT_TO, update_modified=False)
			frappe.get_doc({
				"doctype": "Comment", "comment_type": "Info",
				"reference_doctype": DT, "reference_name": r["name"],
				"content": ("Trả lại Cách tính thuế về \"%s\": %s. Không có ô tiền nào bị "
				            "sửa. (dọn hậu quả cột default của đợt v228)" % (KT_TO, vi_sao)),
			}).insert(ignore_permissions=True)
			ra["sua"].append({"to": r["name"], "vi_sao": vi_sao})
		except Exception:
			frappe.log_error(frappe.get_traceback(), "bao_gia: sua kieu thue %s" % r["name"])
	if ra["sua"]:
		frappe.db.commit()
	return ra


@frappe.whitelist()
def soi_kieu_thue():
	"""Xem truoc ham tren se dung vao nhung to nao. KHONG ghi gi."""
	_quyen()
	ds = frappe.get_all(DT, fields=["name", "creation", "kieu_thue", "tam_tinh",
	                                "chiet_khau_tien", "thue_tien", "tong_cong",
	                                "gia_da_gom_vat", "thue_pt", "trang_thai"],
	                    limit_page_length=0, order_by="creation")
	ra = []
	for r in ds:
		doc = frappe.get_doc(DT, r["name"])
		bt = bang_thue(
			[{"thanh_tien": flt(d.thanh_tien), "thue_pt": flt(d.thue_pt)}
			 for d in (doc.get("dong") or [])],
			ck_to=flt(doc.chiet_khau_tien), phi_giao=flt(doc.phi_giao),
			phi_giao_pt=flt(doc.get("thue_phi_giao_pt")),
			da_gom=1 if doc.gia_da_gom_vat else 0,
		)
		r["tong_theo_dong"] = flt(bt["tong_cong"])
		r["lech"] = flt(bt["tong_cong"]) - flt(r["tong_cong"])
		r["truoc_moc"] = 1 if str(r["creation"]) < MOC_CO_O_KIEU_THUE else 0
		ra.append(r)
	return {"rows": ra, "moc": MOC_CO_O_KIEU_THUE}
