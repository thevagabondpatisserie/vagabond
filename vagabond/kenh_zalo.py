# -*- coding: utf-8 -*-
"""Bắn tin ERP vào nhóm Zalo qua Zalo Bot (#410, bản thử v562).

Anh Việt 02/10/2026: muốn ERP tự bắn tin vào nhóm của từng bộ phận, có chỗ
điền nhóm, tin chia loại. Ban đầu bàn Lark, sau chọn Zalo vì nhân viên quen
dùng. Codex góp ý thiết kế trên #410; tệp này làm phần lõi theo góp ý đó:

  - MỘT hàm `bao()` cho mọi nơi trong app gọi; gửi SAU commit qua hàng đợi,
    Zalo lỗi không bao giờ làm hỏng chứng từ (khuôn của dat_ban.py).
  - Năm loại tin, mỗi loại một biểu tượng đầu tin (Zalo Bot chỉ gửi chữ).
  - Giờ im theo từng nhóm: chỉ Cảnh báo vượt giờ im; tin khác hoãn, hết giờ
    im thì gửi MỘT tin tổng hợp còn tồn, không xả từng tin cũ.
  - Chống trùng: khoá = sự kiện + nhóm, ghi vào "Vagabond Tin Kenh" với tên
    bản ghi CHÍNH LÀ khoá, nên hai worker cùng claim thì một bên vấp khoá
    chính và bỏ qua. Timeout ghi "Chưa rõ", không hứa tuyệt đối không trùng
    vì Zalo không có khoá idempotency.
  - Token bot nằm ở ô Password; không đưa token, nội dung tin hay chat_id
    vào Error Log.

Zalo Bot API (bot.zaloplatforms.com): gọi `https://bot-api.zaloplatforms.com
/bot<token>/<method>`, trả {ok, result | error_code, description}. Nhận cập
nhật qua webhook có header `X-Bot-Api-Secret-Token`. Đối chiếu tài liệu chính
thức 03/10/2026 (docs.zaloplatforms.com/docs/BOT/apis/...): sendMessage nhận
chat_id của người hoặc cuộc trò chuyện, chữ 1 đến 2.000 ký tự; setWebhook lưu
URL kể cả khi gọi thử thất bại, kết quả gọi thử ở result.verification;
testWebhook trả kết quả gọi thử ở result. Nhóm: thêm bot vào nhóm, ai đó
@nhắc bot một lần để máy biết mã nhóm; điểm này cần kiểm bằng gửi thử.
"""

import hmac
import json
import re
import secrets

import frappe
from frappe.utils import cint, get_url, now_datetime

API = "https://bot-api.zaloplatforms.com"
TIMEOUT = 10
TOI_DA_KY_TU = 2000
GIU_CHAT_MOI = 20
TOI_DA_DONG_GOP = 600
LO_GOP = 200

# Mã loại -> (biểu tượng, tên). Thứ tự là thứ tự hiện trong Cài đặt.
LOAI = {
	"thong_bao": ("ℹ️", "Thông báo"),
	"viec": ("✅", "Việc cần làm"),
	"canh_bao": ("🚨", "Cảnh báo"),
	"ban_tin": ("📊", "Bản tin"),
	"phat_hanh": ("🚀", "Phát hành"),
}
# v597: "he_thong" cho còi báo động thư hỏng (thay webhook Lark nhóm quản trị).
# v602: "hoa_don" tách khỏi "ban_hang" để chuông kẹt ghi sổ, kẹt hoá đơn điện tử
# vào đúng nhóm kế toán chọn, không đổ hết vào nhóm Sales (anh Việt 18/10/2026).
CHU_DE = ("kho", "san_xuat", "cong_no", "ban_hang", "hoa_don", "don_web", "dat_ban", "phat_hanh", "he_thong")
# Tên có dấu của chủ đề, khớp hộp chọn ở Cài đặt lõi (cai_dat_loi_chung.js).
TEN_CHU_DE = {"kho": "Kho", "san_xuat": "Sản xuất", "cong_no": "Công nợ", "ban_hang": "Bán hàng",
	"hoa_don": "Hoá đơn", "don_web": "Đơn web", "dat_ban": "Đặt bàn", "phat_hanh": "Phát hành app", "he_thong": "Hệ thống"}

# v604: anh Việt 18/10/2026 bỏ hẳn thư cảnh báo nội bộ, mọi tin nhắc việc và báo sự
# cố cho nhân viên đi qua nhóm Zalo. Mỗi nhóm trong Cài đặt có ô "Tin nhận": anh
# tích đúng những tin nhóm đó cần, không phải đoán qua Loại tin và Chủ đề. Bảng
# dưới là danh mục DUY NHẤT của các tin đó; mỗi nơi gọi bao() phải truyền ma_tin
# có trong bảng (ca thu_tin_zalo_604 dò mã nguồn để chốt), và bản JS VGB_ZALO_TIN
# trong cai_dat_loi_chung.js phải trùng từng chữ.
# Mã -> (bộ phận, tên, giải thích một dòng, loại, chủ đề). Loại và chủ đề giữ cho
# nhóm chưa chọn Tin nhận (lọc kiểu cũ) và cho giờ im (chỉ Cảnh báo vượt giờ im).
# v609: thêm "Thu mua" và "Kho" (anh Việt duyệt mẫu tin 22/10/2026).
BO_PHAN = ("Ban giám đốc", "Hoá đơn, kế toán", "Bán hàng, cửa hàng", "Bếp", "Thu mua", "Kho", "Hệ thống")
TIN = {
	"bgd_bao_cao_ngay": ("Ban giám đốc", "Báo cáo cuối ngày (23:30)",
		"23:30 mỗi tối: doanh thu, giảm giá, sửa huỷ, điểm cần để ý. Nhóm nhận đừng đặt giờ im lúc 23:30.", "ban_tin", "ban_hang"),
	# v613 (anh Việt 27/10/2026): báo từng bước duyệt phiếu chi APP.
	"bgd_app_cho_duyet": ("Ban giám đốc", "Phiếu chi chờ giám đốc duyệt",
		"Kế toán đã kiểm phiếu chi trả nhà cung cấp, chờ giám đốc duyệt.", "viec", "cong_no"),
	"hd_ket_ghi_so": ("Hoá đơn, kế toán", "Kẹt ghi sổ, kẹt hoá đơn cuối ngày",
		"20 và 45 phút sau giờ chạy cuối ngày, và 07:30 sáng hôm sau, còn đơn chưa ghi sổ.", "canh_bao", "hoa_don"),
	"hd_don_chua_ghi_so": ("Hoá đơn, kế toán", "Đơn chưa ghi sổ còn sót lúc 23:55",
		"23:55 mỗi ngày, còn đơn bán chưa ghi sổ được.", "canh_bao", "hoa_don"),
	"hd_hddt_sot": ("Hoá đơn, kế toán", "Đã ghi sổ mà chưa xuất hoá đơn điện tử",
		"23:55 mỗi ngày, còn tờ đã ghi sổ mà chưa có hoá đơn điện tử.", "canh_bao", "hoa_don"),
	"hd_giu_ngay_cu": ("Hoá đơn, kế toán", "Hoá đơn ngày cũ bị giữ lại, không phát hành",
		"Khi chuỗi cuối ngày giữ hoá đơn lại vì còn nợ ngày cũ chưa đối soát.", "canh_bao", "hoa_don"),
	"hd_trung": ("Hoá đơn, kế toán", "Đơn có hoá đơn trùng (doanh thu tính đôi)",
		"02:00 mỗi đêm, có đơn mang từ hai hoá đơn bán hàng trở lên.", "canh_bao", "hoa_don"),
	"hd_dau_vao": ("Hoá đơn, kế toán", "Hoá đơn đầu vào m-invoice tắc nhịp hoặc trùng",
		"08:25 mỗi sáng, hoá đơn mua vào chưa dựng được chứng từ hoặc có chứng từ trùng.", "canh_bao", "hoa_don"),
	"kt_tra_truoc_erp": ("Hoá đơn, kế toán", "Khoản trả trước chờ duyệt",
		"Thu mua gửi một khoản đã trả trước khi lên ERP, chờ kế toán duyệt.", "viec", "cong_no"),
	"kt_hoan_tien": ("Hoá đơn, kế toán", "Yêu cầu hoàn tiền chờ chi",
		"Sales gửi yêu cầu hoàn tiền cho khách, chờ kế toán chuyển khoản.", "viec", "cong_no"),
	"kt_de_nghi_chi": ("Hoá đơn, kế toán", "Đề nghị chi chờ duyệt hoặc bị trả lại",
		"Đề nghị chi chuyển sang bước duyệt kế tiếp, hoặc bị trả về người lập.", "viec", "cong_no"),
	"kt_tra_truoc_kiem": ("Hoá đơn, kế toán", "Phiếu trả trước chờ kiểm",
		"Có phiếu trả trước nhà cung cấp chờ kế toán kiểm tra.", "viec", "cong_no"),
	"kt_diem_het_han": ("Hoá đơn, kế toán", "Điểm khách hết hạn: máy tự dừng vì chạm trần",
		"05:00 sáng, số khách tới hạn đốt điểm vượt mức an toàn nên máy chưa đốt.", "viec", "ban_hang"),
	"kt_hop_dong_dc": ("Hoá đơn, kế toán", "Hợp đồng vừa điều chỉnh",
		"Sales vừa chốt một lần điều chỉnh hợp đồng so với bản gốc.", "thong_bao", "ban_hang"),
	"kt_xuat_huy_gia_von": ("Hoá đơn, kế toán", "Xuất huỷ đã ghi sổ, kèm giá vốn",
		"Phiếu xuất huỷ vừa ghi sổ: kho, lý do, tên hàng và giá vốn đã trừ.", "thong_bao", "kho"),
	"kt_kiem_ke_lech": ("Hoá đơn, kế toán", "Kiểm kê đã ghi sổ, kèm giá trị chênh lệch",
		"Kiểm kê vừa điều chỉnh tồn: tên hàng lệch và giá trị chênh lệch đã vào sổ.", "thong_bao", "kho"),
	"kt_tien_chua_gan": ("Hoá đơn, kế toán", "Tiền vào tài khoản công ty chưa gắn chứng từ (08:00)",
		"08:00 mỗi sáng: khoản tiền vào tài khoản chính công ty quá 24 giờ mà chưa thuộc đơn hay phiếu nào.", "viec", "cong_no"),
	"kt_app_da_duyet": ("Hoá đơn, kế toán", "Phiếu chi giám đốc đã duyệt, chờ chuyển tiền",
		"Giám đốc vừa duyệt phiếu chi; kế toán chuyển khoản rồi xác nhận đã chuyển.", "viec", "cong_no"),
	"kt_app_tra_lai": ("Hoá đơn, kế toán", "Phiếu chi bị trả lại",
		"Phiếu chi bị trả về người lập, kèm người trả và lý do.", "viec", "cong_no"),
	"kt_app_da_chi": ("Hoá đơn, kế toán", "Phiếu chi đã chuyển tiền và ghi sổ",
		"Kế toán xác nhận đã chuyển tiền, phiếu chi đã ghi sổ.", "thong_bao", "cong_no"),
	"kt_de_nghi_chi_da_chi": ("Hoá đơn, kế toán", "Đề nghị chi đã chi xong",
		"Khoản chi của đề nghị chi đã khớp sao kê ngân hàng, người lập biết tiền đã đi.", "thong_bao", "cong_no"),
	"bh_don_web_treo": ("Bán hàng, cửa hàng", "Đơn web treo quá 30 phút chưa vào Pancake",
		"Đơn đặt bánh trên web quá 30 phút mà chưa tạo được trên Pancake.", "viec", "don_web"),
	"bh_ton_web_loi": ("Bán hàng, cửa hàng", "Lỗi kiểm tồn khi khách đặt web",
		"Phép kiểm tồn bánh lỗi lúc khách đặt; Sales kiểm lại tồn trước khi xác nhận.", "canh_bao", "don_web"),
	"bh_ahamove_huy": ("Bán hàng, cửa hàng", "Tài xế Ahamove huỷ hoặc giao thất bại",
		"Tài xế huỷ hoặc giao không được, vận đơn về Chờ giao để phân công lại.", "viec", "ban_hang"),
	"bh_dat_ban": ("Bán hàng, cửa hàng", "Đặt bàn mới",
		"Khách vừa gửi yêu cầu đặt bàn, chờ cửa hàng xác nhận.", "viec", "dat_ban"),
	"bh_dat_ban_xac_nhan": ("Bán hàng, cửa hàng", "Đặt bàn đã xác nhận",
		"Quản lý vừa xác nhận một đặt bàn: ngày giờ, tên, số điện thoại, số khách.", "thong_bao", "dat_ban"),
	"bh_dat_ban_huy": ("Bán hàng, cửa hàng", "Đặt bàn đã huỷ",
		"Quản lý vừa huỷ một đặt bàn, kèm lý do đã báo khách.", "thong_bao", "dat_ban"),
	"bh_dat_ban_sap_toi": ("Bán hàng, cửa hàng", "Đặt bàn còn 3 giờ mà chưa xác nhận",
		"Mỗi 15 phút: yêu cầu đặt bàn còn chờ xác nhận khi chỉ còn 3 giờ tới giờ khách đến.", "viec", "dat_ban"),
	"bh_thong_tin_hd_sai": ("Bán hàng, cửa hàng", "Thông tin xuất hoá đơn sai, đơn chưa ghi sổ",
		"m-invoice từ chối thông tin người mua (email, mã số thuế, tên): đơn nào, sai chỗ nào để Sales sửa.", "canh_bao", "hoa_don"),
	"bh_tiec": ("Bán hàng, cửa hàng", "Đăng ký tiệc mới",
		"Khách vừa đăng ký vé tiệc, chờ cửa hàng xác nhận.", "viec", "dat_ban"),
	"bh_pancake_lech_tong": ("Bán hàng, cửa hàng", "Đơn web lệch tổng tiền trên Pancake",
		"Tổng tiền trên Pancake khác số máy chủ chốt; Sales kiểm trước khi gửi mã QR.", "canh_bao", "don_web"),
	"bh_ahamove_phi": ("Bán hàng, cửa hàng", "Không lấy được phí giao Ahamove",
		"Trang đặt bánh không tính được phí giao vì Ahamove không trả lời.", "canh_bao", "don_web"),
	"bh_don_web_moi": ("Bán hàng, cửa hàng", "Đơn web mới đã vào Pancake",
		"Khách vừa đặt trên web: giờ nhận, món, tổng tiền, miễn phí giao hay không.", "thong_bao", "don_web"),
	"bh_hoan_tien_xong": ("Bán hàng, cửa hàng", "Đã hoàn tiền cho khách",
		"Kế toán đã chuyển xong tiền hoàn, Sales báo khách.", "thong_bao", "ban_hang"),
	"bep_ke_hoach_sx": ("Bếp", "Kế hoạch sản xuất hôm nay (05:00)",
		"05:00 sáng, kế hoạch sản xuất trong ngày đã sẵn, bếp đọc rồi chốt.", "viec", "san_xuat"),
	"bep_lenh_sx_xuat_nvl": ("Bếp", "Lệnh sản xuất đã xuất nguyên liệu",
		"Phiếu sản xuất vừa ghi sổ: thành phẩm và nguyên liệu đã trừ kho.", "thong_bao", "san_xuat"),
	"bep_ycsx_moi": ("Bếp", "Yêu cầu sản xuất mới",
		"Bộ phận vừa gửi yêu cầu sản xuất cho bếp: món, số lượng, ngày cần; cần trong hôm nay thì ghi GẤP.", "viec", "san_xuat"),
	"bep_ycsx_huy": ("Bếp", "Yêu cầu sản xuất bị huỷ",
		"Yêu cầu sản xuất đã gửi bếp vừa bị huỷ, bếp bỏ khỏi kế hoạch.", "thong_bao", "san_xuat"),
	"bep_ycsx_ngay_mai": ("Bếp", "Tổng yêu cầu sản xuất cho ngày mai (20:30)",
		"20:30 mỗi tối, một tin mỗi bếp: cộng món và số lượng của các yêu cầu cần ngày mai.", "viec", "san_xuat"),
	"bep_thieu_nvl_ngay_mai": ("Bếp", "Thiếu nguyên liệu cho yêu cầu ngày mai (20:45)",
		"20:45 mỗi tối, một tin mỗi bếp: nguyên liệu trong kho bếp không đủ làm theo công thức.", "viec", "san_xuat"),
	"bep_san_luong_ngay": ("Bếp", "Sản lượng cuối ngày từng bếp, kèm ảnh bảng (21:00)",
		"21:00 mỗi tối, một ảnh mỗi bếp: yêu cầu hôm nay, số đã làm, món còn thiếu.", "ban_tin", "san_xuat"),
	"bep_lenh_chua_xong": ("Bếp", "Lệnh sản xuất quá ngày chưa ghi hoàn tất (08:00)",
		"08:00 mỗi sáng: lệnh sản xuất từ hôm qua trở về trước chưa ghi làm xong, kho chưa có hàng.", "viec", "san_xuat"),
	"tm_yeu_cau_mua": ("Thu mua", "Yêu cầu mua hàng mới",
		"Bộ phận vừa lập yêu cầu mua: tên hàng, số lượng, ngày cần.", "viec", "kho"),
	"tm_don_mua_moi": ("Thu mua", "Đơn mua hàng vừa đặt",
		"Đơn mua vừa ghi sổ: nhà cung cấp, ngày hẹn về, tên hàng, tổng tiền.", "thong_bao", "kho"),
	"tm_don_mua_tre_hen": ("Thu mua", "Đơn mua trễ hẹn chưa về đủ (08:00)",
		"08:00 mỗi sáng, đơn mua đã qua ngày hẹn mà hàng chưa về đủ.", "viec", "kho"),
	"tm_hang_ve_chua_hoa_don": ("Thu mua", "Hàng về quá 3 ngày chưa có hoá đơn (08:25)",
		"08:25 mỗi sáng, phiếu nhập đã ghi sổ quá 3 ngày mà chưa có hoá đơn mua.", "viec", "kho"),
	"kho_nhap_cho_kiem": ("Kho", "Phiếu nhập chờ kho đếm và ghi sổ",
		"Có phiếu nhập còn nháp chờ kho đếm hàng rồi ghi sổ.", "viec", "kho"),
	"kho_da_nhap": ("Kho", "Đã nhập hàng vào kho",
		"Phiếu nhập vừa ghi sổ: tên hàng, số lượng, lệch so với đơn mua, hạn lô.", "thong_bao", "kho"),
	"kho_da_chuyen": ("Kho", "Đã chuyển hàng giữa kho",
		"Phiếu điều chuyển vừa ghi sổ: kho đi, kho đến, tên hàng, số lượng.", "thong_bao", "kho"),
	"kho_da_nhan_chuyen": ("Kho", "Kho nhận đã xác nhận hàng điều chuyển",
		"Kho nhận vừa xác nhận số thực nhận; nhận thiếu thì báo kèm dòng lệch.", "thong_bao", "kho"),
	"kho_chuyen_chua_nhan": ("Kho", "Hàng chuyển tới quá 2 giờ chưa xác nhận",
		"Mỗi giờ: phiếu điều chuyển đã ghi sổ từ 2 giờ mà kho nhận chưa xác nhận.", "viec", "kho"),
	"kho_ycdc_moi": ("Kho", "Yêu cầu điều chuyển mới",
		"Bộ phận vừa gửi yêu cầu chuyển hàng giữa kho: kho đi, kho đến, tên hàng, ngày cần.", "viec", "kho"),
	"kho_ycdc_treo": ("Kho", "Yêu cầu điều chuyển treo quá 2 ngày (08:00)",
		"08:00 mỗi sáng: yêu cầu điều chuyển đã gửi quá 2 ngày mà chưa chuyển xong.", "viec", "kho"),
	"kho_nhan_thieu_ton": ("Kho", "Nhận hàng không được vì kho xuất chưa đủ hàng",
		"Kho nhận bấm xác nhận mà kho xuất chưa đủ hàng trên máy: tên hàng, kho, số lượng còn thiếu.", "canh_bao", "kho"),
	"kho_huy_cho_ghi_so": ("Kho", "Phiếu xuất huỷ chờ ghi sổ",
		"Có phiếu xuất huỷ còn nháp chờ người có quyền ghi sổ.", "viec", "kho"),
	"kho_da_huy": ("Kho", "Đã xuất huỷ",
		"Phiếu xuất huỷ vừa ghi sổ: kho, lý do, tên hàng, số lượng.", "thong_bao", "kho"),
	"kho_xuat_noi_bo": ("Kho", "Đã xuất dùng nội bộ",
		"Phiếu xuất nội bộ vừa ghi sổ: mục đích, tên hàng, số lượng.", "thong_bao", "kho"),
	"kho_giao_si": ("Kho", "Đã xuất giao khách sỉ",
		"Phiếu giao hàng sỉ vừa ghi sổ: khách, kho, tên hàng, số lượng.", "thong_bao", "kho"),
	"kho_kiem_ke_cho_duyet": ("Kho", "Phiếu kiểm kê chờ duyệt",
		"Phiếu kiểm kê vừa chuyển sang Chờ duyệt, kèm các dòng lệch.", "viec", "kho"),
	"kho_kiem_ke_da_ghi_so": ("Kho", "Kiểm kê đã ghi sổ",
		"Phiếu kiểm kê đã ghi sổ điều chỉnh tồn, kèm các dòng lệch.", "thong_bao", "kho"),
	"kho_lo_sap_het_han": ("Kho", "Lô sắp hết hạn trong 3 ngày (07:00)",
		"07:00 mỗi sáng, một tin mỗi kho: lô còn tồn mà hết hạn trong 3 ngày.", "viec", "kho"),
	"kho_ton_duoi_muc": ("Kho", "Tồn kho dưới mức tối thiểu (07:00)",
		"07:00 mỗi sáng, một tin mỗi kho: món có tồn thấp hơn mức tối thiểu đã khai.", "viec", "kho"),
	"kho_ton_quay_cuoi_ngay": ("Kho", "Tồn bánh cuối ngày từng chi nhánh, kèm ảnh bảng (23:00)",
		"23:00 mỗi tối, một ảnh mỗi chi nhánh: đầu ngày, nhập, bán, hỏng, còn lại của từng bánh.", "ban_tin", "kho"),
	"kho_ton_am": ("Kho", "Tồn âm trên máy (08:00)",
		"08:00 mỗi sáng: món đang âm kho, tức còn phiếu nhập hay sản xuất chưa ghi.", "viec", "kho"),
	"kho_hang_nam_im": ("Kho", "Hàng nằm im 30 ngày (Thứ Hai 08:05)",
		"Thứ Hai hằng tuần: nguyên liệu, bao bì còn tồn mà 30 ngày không xuất lần nào.", "thong_bao", "kho"),
	"ht_email_loi": ("Hệ thống", "Email của tiệm không gửi được",
		"Trong một giờ có từ 5 thư lỗi; báo lại sau 3 giờ nếu còn lỗi.", "canh_bao", "he_thong"),
	"ht_phat_hanh": ("Hệ thống", "Bản tin cập nhật app sau mỗi deploy",
		"App vừa lên bản mới: thêm gì, bộ phận cần làm gì.", "phat_hanh", "phat_hanh"),
}

# Codex #413 P2: tin "việc cần làm" phải kiểm lại việc còn mở ngay trước khi
# gửi. Mã kiểm -> hàm(nguon) trả True nếu việc vẫn cần làm. Chỉ tra trong bảng
# này, không gọi hàm theo tên tuỳ ý.
DIEU_KIEN = {
	"cho_duyet_truoc_erp": "vagabond.cong_no_ncc.con_cho_duyet_truoc_erp",
	# v597: đặt bàn, đăng ký tiệc đã có người xác nhận hoặc huỷ thì không nhắc nữa.
	"dat_ban_cho": "vagabond.dat_ban.con_cho_xac_nhan",
	"tiec_cho": "vagabond.tiec_web.con_cho_xac_nhan",
}
BO_QUA = "Bỏ qua (đã xử lý)"
CHO_GUI = "Chờ gửi"
DANG_GUI = "Đang gửi"
CHUA_RO = "Chưa rõ"
# Dòng nằm "Đang gửi" quá chừng này phút là worker đã chết TRƯỚC khi gọi Zalo
# (trước khi gọi máy luôn đổi sang "Chưa rõ"), nên trả về Chờ gửi là an toàn.
KET_PHUT = 10
NHOM_TAT = "Nhóm đã tắt hoặc bị gỡ khỏi bảng."
# Codex #425 vòng 11: kết quả nội bộ của _goi khi lỗi mạng xảy ra TRƯỚC khi gửi
# được gì tới Zalo (DNS, không mở được kết nối). Không ghi vào sổ: dòng được trả
# về trạng thái chờ để gửi lại. Lỗi mạng không rõ đã gửi hay chưa thì là Chưa rõ.
MANG_LOI = "Chưa kết nối được Zalo"
LOI_CHUA_GUI = ("ConnectTimeout", "ConnectTimeoutError", "NewConnectionError", "NameResolutionError",
	"gaierror", "ConnectionRefusedError", "ProxyError")


# ------------------------------------------------------------------ THUẦN

def tach_tin(chu):
	"""THUẦN: tin nhiều dòng soạn sẵn (khuôn tin Lark cũ) -> (tiêu đề, các dòng).

	v597: các nơi từng bắn Lark giữ nguyên hàm soạn chữ (đã có ca kiểm nội dung),
	chỉ đổi đường gửi sang bao(). Dòng đầu là tiêu đề, bỏ dòng trống."""
	ds = [x.strip() for x in str(chu or "").splitlines() if x.strip()]
	return (ds[0] if ds else ""), ds[1:]


def chu_chua_nhom(loai, chu_de, nguon=None, ma_tin=None):
	"""THUẦN: (tiêu đề, lời) Error Log khi bao() không ghi được dòng tin nào.

	v597 Codex #481: Zalo tắt hoặc chưa có nhóm bật nhận đúng loại và chủ đề thì
	bao() trả rỗng mà không ném lỗi; người trực phải biết để gán nhóm và báo tay.
	v604: tin có mã thì gọi đúng tên tin (người trực tìm đúng ô cần tích)."""
	ten_tin = TIN.get(ma_tin, (None, None))[1] if ma_tin else None
	if ten_tin:
		tieu_de = "Zalo: chưa có nhóm nhận tin %s" % ten_tin
		loi = ("Tin \"%s\" không ghi được cho nhóm Zalo nào: Zalo đang tắt hoặc chưa nhóm nào bật nhận "
			"tin này. Vào Cài đặt lõi, mục Thông báo, mở nhóm cần nhận, tích tin này ở phần Tin nhận." % ten_tin)
		if nguon:
			loi += " Chứng từ %s chưa được báo, cần báo tay." % nguon
		return tieu_de[:140], loi
	ten_loai = LOAI.get(loai, ("", loai))[1]
	ten_cd = TEN_CHU_DE.get(chu_de, chu_de)
	tieu_de = "Zalo: chưa có nhóm nhận %s, chủ đề %s" % (ten_loai, ten_cd)
	loi = ("Tin %s, chủ đề %s không ghi được cho nhóm Zalo nào: Zalo đang tắt hoặc chưa có nhóm bật "
		"nhận đúng loại và chủ đề. Vào Cài đặt lõi, mục Thông báo, gán nhóm." % (ten_loai, ten_cd))
	if nguon:
		loi += " Chứng từ %s chưa được báo, cần báo tay." % nguon
	return tieu_de[:140], loi


def tach_ds(s):
	"""THUẦN: "viec, canh_bao" -> {"viec", "canh_bao"}; rỗng -> set()."""
	return {x.strip() for x in str(s or "").replace(";", ",").split(",") if x.strip()}


def soan_tin(loai, tieu_de, dong=None, link=None, nguoi=None, han=None):
	"""THUẦN: một tin chữ cho Zalo, không quá TOI_DA_KY_TU ký tự.

	Codex #410: tin nói rõ việc gì, ai phụ trách, hạn, một đường mở đúng màn."""
	bt, ten = LOAI.get(loai, ("ℹ️", "Thông báo"))
	ra = ["%s %s: %s" % (bt, ten.upper(), (tieu_de or "").strip())]
	for d in (dong or []):
		d = str(d or "").strip()
		if d:
			ra.append("- " + d)
	if nguoi:
		ra.append("Phụ trách: %s" % nguoi)
	if han:
		ra.append("Hạn: %s" % han)
	if link:
		ra.append("Mở: %s" % link)
	tin = "\n".join(ra)
	if len(tin) > TOI_DA_KY_TU:
		duoi = ("\nMở: %s" % link) if link else ""
		tin = tin[:TOI_DA_KY_TU - len(duoi) - 2].rstrip() + "…" + duoi
	return tin


# v613 (anh Việt 27/10/2026): tin đơn hàng không hiện tổng tiền. Luật gom về MỘT chỗ:
# tin của các bộ phận ngoài danh sách dưới đây không được mang số tiền. Nơi phát đã soạn
# không tiền; cửa ghi sổ tin vẫn lọc lần cuối để một chỗ quên không lọt ra nhóm.
BO_PHAN_DUOC_TIEN = ("Ban giám đốc", "Hoá đơn, kế toán", "Hệ thống")
MAU_TIEN = re.compile(r"\d[\d.,]*\s*(?:đ|₫|vnđ|vnd)(?!\w)", re.I)


def khong_duoc_tien(ma_tin):
	"""THUẦN: tin mang mã này có bị cấm hiện số tiền không (theo bộ phận của tin)."""
	v = TIN.get(ma_tin or "")
	return bool(v) and v[0] not in BO_PHAN_DUOC_TIEN


def bo_dong_tien(noi_dung):
	"""THUẦN: bỏ số tiền khỏi một tin. Dòng đầu (tiêu đề) chỉ xoá con số; dòng sau có
	số tiền thì bỏ cả dòng. Trả (tin sạch, số chỗ đã bỏ)."""
	ds = str(noi_dung or "").split("\n")
	ra, bo = [], 0
	for i, d in enumerate(ds):
		if not MAU_TIEN.search(d):
			ra.append(d)
			continue
		bo += 1
		if i == 0:
			ra.append(re.sub(r"\s{2,}", " ", MAU_TIEN.sub("", d)).strip())
	return "\n".join(ra), bo


def tin_soan_san(noi_dung):
	"""THUẦN (v606): tin soạn sẵn, bỏ khoảng trắng đầu cuối, không quá TOI_DA_KY_TU ký tự."""
	t = str(noi_dung or "").strip()
	if len(t) > TOI_DA_KY_TU:
		t = t[:TOI_DA_KY_TU - 1].rstrip() + "…"
	return t


def trong_gio_im(gio, im_tu, im_den):
	"""THUẦN: gio "HH:MM" có nằm trong [im_tu, im_den) không; qua nửa đêm được."""
	a, b, g = gio_hop_le(im_tu), gio_hop_le(im_den), gio_hop_le(gio)
	if a is None or b is None or g is None or a == b:
		return False
	return a <= g < b if a < b else (g >= a or g < b)


def chon_nhom(ds, loai, chu_de, ma_tin=None):
	"""THUẦN: các dòng nhóm nhận tin (loai, chu_de, ma_tin). Dòng là dict.

	Thiếu mã chat hoặc tắt thì bỏ. v604: nhóm đã tích Tin nhận thì CHỈ nhận đúng
	các tin đã tích, không xét Loại tin và Chủ đề nữa; tin không mang mã không bao
	giờ tới nhóm đó. Nhóm chưa tích tin nào giữ luật cũ: loại hoặc chủ đề để trống
	là nhận tất (để nhóm cũ không mất tin ngay sau khi cập nhật)."""
	ra = []
	for r in ds or []:
		if not cint(r.get("bat")) or not str(r.get("chat_id") or "").strip():
			continue
		tn = tach_ds(r.get("tin_nhan"))
		if tn:
			if ma_tin and ma_tin in tn:
				ra.append(r)
			continue
		lt, cd = tach_ds(r.get("loai_tin")), tach_ds(r.get("chu_de"))
		if lt and loai not in lt:
			continue
		if cd and chu_de and chu_de not in cd:
			continue
		ra.append(r)
	return ra


def khoa_tin(khoa_su_kien, chat_id):
	"""THUẦN: tên bản ghi chống trùng, gọn trong 140 ký tự.

	Codex #417: khoá theo MÃ CHAT (người nhận thật), không theo tên nhóm sửa
	được. Hai dòng trùng tên khác mã chat trước đây vấp chung một khoá nên
	một nhóm mất tin; đổi tên nhóm cũng không làm mất tin đang hoãn."""
	import hashlib
	tho = "%s|%s" % (khoa_su_kien or "", str(chat_id or "").strip())
	return "ZL-" + hashlib.sha1(tho.encode("utf-8")).hexdigest()[:24]


def doc_ket_qua(goi):
	"""THUẦN: (trạng thái, lỗi) từ JSON Zalo trả về."""
	if isinstance(goi, dict) and goi.get("ok") is True:
		return "Đã gửi", ""
	if isinstance(goi, dict):
		return "Lỗi", ("Zalo báo lỗi %s: %s" % (goi.get("error_code", "?"), goi.get("description", "")))[:300]
	return "Chưa rõ", "Zalo trả về dữ liệu lạ."


def kiem_nhom_trung(ds):
	"""THUẦN: lỗi nếu bảng Nhóm nhận tin có hai dòng trùng tên hoặc trùng mã chat."""
	loi, ten, ma = [], {}, {}
	for i, r in enumerate(ds or [], 1):
		t = str(r.get("ten_nhom") or "").strip().lower()
		c = str(r.get("chat_id") or "").strip()
		if t and t in ten:
			loi.append("dòng %s và %s cùng tên nhóm \"%s\"" % (ten[t], i, r.get("ten_nhom")))
		if c and c in ma:
			loi.append("dòng %s và %s cùng mã chat" % (ma[c], i))
		ten.setdefault(t, i)
		if c:
			ma.setdefault(c, i)
	return ("Bảng Nhóm nhận tin Zalo: " + "; ".join(loi) + ". Mỗi nhóm một dòng.") if loi else ""


def kiem_bo_loc(ds):
	"""THUẦN: lỗi nếu ô Loại tin / Chủ đề của một dòng có mã ngoài danh mục.

	Codex #417: hai ô này là chữ tự do; gõ sai (ví dụ "việc" thay vì "viec")
	thì chon_nhom lặng lẽ bỏ nhóm đó và tin cần gửi biến mất. Chặn ngay lúc lưu."""
	loi, la_tin = [], []
	for i, r in enumerate(ds or [], 1):
		la_loai = sorted(tach_ds(r.get("loai_tin")) - set(LOAI))
		la_cd = sorted(tach_ds(r.get("chu_de")) - set(CHU_DE))
		if la_loai:
			loi.append("dòng %s Loại tin không có: %s" % (i, ", ".join(la_loai)))
		if la_cd:
			loi.append("dòng %s Chủ đề không có: %s" % (i, ", ".join(la_cd)))
		# v604: mã tin lạ (gõ tay, hoặc tin đã bỏ khỏi danh mục) thì nhóm lặng lẽ
		# không nhận gì; chặn lúc lưu, nói tên nhóm để người sửa biết mở nhóm nào.
		la = sorted(tach_ds(r.get("tin_nhan")) - set(TIN))
		if la:
			la_tin.append("nhóm %s có %d tin không còn trong danh mục (%s)" % (
				str(r.get("ten_nhom") or "").strip() or ("dòng %s" % i), len(la), ", ".join(la)))
	if not loi and not la_tin:
		return ""
	ra = []
	if loi:
		ra.append("Bảng Nhóm nhận tin Zalo: %s. Loại tin chỉ nhận: %s. Chủ đề chỉ nhận: %s. Để trống là nhận tất."
			% ("; ".join(loi), ", ".join(LOAI), ", ".join(CHU_DE)))
	if la_tin:
		ra.append("Bảng Nhóm nhận tin Zalo: %s. Mở nhóm, bấm Chọn tin nhận, tích lại các tin cần nhận rồi lưu."
			% "; ".join(la_tin))
	return " ".join(ra)


def gio_hop_le(s):
	"""THUẦN: "HH:MM" đúng 00:00 đến 23:59 thì trả số phút, sai thì None."""
	m = __import__("re").fullmatch(r"(\d{2}):(\d{2})", str(s or "").strip())
	if not m or int(m.group(1)) > 23 or int(m.group(2)) > 59:
		return None
	return int(m.group(1)) * 60 + int(m.group(2))


def kiem_gio_im(ds):
	"""THUẦN: lỗi nếu giờ im của một dòng gõ sai, thiếu một đầu, hoặc hai đầu trùng nhau.

	Codex #423: "22h", "24:00", "07:99" hay chỉ điền một đầu trước đây được lưu,
	trong_gio_im coi như không im và tin thường bắn cả đêm. Chặn ngay lúc lưu."""
	loi = []
	for i, r in enumerate(ds or [], 1):
		tu, den = str(r.get("im_tu") or "").strip(), str(r.get("im_den") or "").strip()
		if not tu and not den:
			continue
		if not tu or not den:
			loi.append("dòng %s phải điền đủ Giờ im từ và Giờ im đến" % i)
			continue
		sai = [ten for ten, v in (("Giờ im từ", tu), ("Giờ im đến", den)) if gio_hop_le(v) is None]
		if sai:
			loi.append("dòng %s %s phải dạng HH:MM từ 00:00 đến 23:59" % (i, " và ".join(sai)))
		elif gio_hop_le(tu) == gio_hop_le(den):
			loi.append("dòng %s Giờ im từ và đến trùng nhau" % i)
	return ("Bảng Nhóm nhận tin Zalo: " + "; ".join(loi) + ".") if loi else ""


def kiem_bot(toi):
	"""THUẦN: lỗi nếu getMe báo bot không được vào nhóm (can_join_groups = false).

	Codex #425: bot loại này vẫn nối webhook được nên trông như đã xong, nhưng
	không vào nhóm được, không bao giờ có mã nhóm. Thiếu trường thì không chặn."""
	if isinstance(toi, dict) and toi.get("can_join_groups") is False:
		return ("Bot Zalo này chưa được phép vào nhóm (can_join_groups = false). Vào bot.zaloplatforms.com "
			"bật quyền tham gia nhóm cho bot (hoặc nâng loại bot), rồi bấm Nối Zalo Bot lại.")
	return ""


def kiem_ma_chat(ds, cu, chat_moi):
	"""THUẦN: mã chat mới thêm phải là NHÓM đã nhắn bot (có trong Chat vừa nhắn bot).

	Codex #425: ô mã chat gõ tự do thì gõ nhầm hoặc dán nhầm mã chat riêng
	vẫn lưu được, tin việc đi sai chỗ. Dòng đã lưu từ trước (cu) giữ nguyên,
	không bắt kiểm lại vì danh sách Chat vừa nhắn bot chỉ giữ 20 chat gần nhất."""
	da_co = {str(x or "").strip() for x in (cu or [])}
	biet = {str(x.get("chat_id") or "").strip(): x for x in (chat_moi or []) if isinstance(x, dict)}
	loi = []
	for i, r in enumerate(ds or [], 1):
		c = str(r.get("chat_id") or "").strip()
		if not c or c in da_co:
			continue
		x = biet.get(c)
		if not x:
			loi.append("dòng %s mã chat chưa thấy trong Chat vừa nhắn bot (thêm bot vào nhóm, @nhắc bot rồi chọn lại)" % i)
		elif str(x.get("loai") or "").upper() != "GROUP":
			loi.append("dòng %s là chat riêng của %s, không phải nhóm" % (i, x.get("ten") or x.get("nguoi") or "một người"))
	return ("Bảng Nhóm nhận tin Zalo: " + "; ".join(loi) + ".") if loi else ""


def kiem_bang_nhom(ds):
	"""THUẦN: mọi lỗi của bảng Nhóm nhận tin (trùng, mã ngoài danh mục, giờ im sai), rỗng là hợp lệ."""
	return " ".join(x for x in (kiem_nhom_trung(ds), kiem_bo_loc(ds), kiem_gio_im(ds)) if x)


def doc_xac_minh(kq):
	"""THUẦN: đọc kết quả xác minh đường nhận Zalo -> ("ok" | "loi" | "chua_ro", gợi ý).

	Codex #413: setWebhook trả ok:true ở ngoài kể cả khi Zalo gọi thử đường
	nhận thất bại (URL vẫn được lưu). Kết quả thật nằm ở result.verification
	(setWebhook) hoặc chính result (testWebhook). Thiếu thì là chưa rõ."""
	v = kq if isinstance(kq, dict) else {}
	if isinstance(v.get("verification"), dict):
		v = v["verification"]
	if "ok" not in v:
		return "chua_ro", "Zalo không trả kết quả xác minh."
	goi_y = str(v.get("hint") or v.get("outcome") or "")[:200]
	return ("ok" if v.get("ok") is True else "loi"), goi_y


def dong_gop(noi_dung):
	"""THUẦN: một dòng của tin gộp từ nội dung tin gốc: dòng đầu + đường mở."""
	ds = [x.strip() for x in str(noi_dung or "").split("\n") if x.strip()]
	if not ds:
		return ""
	d = ds[0]
	mo = next((x for x in ds[1:] if x.startswith("Mở: ")), "")
	if mo:
		d += " | " + mo
	return d[:TOI_DA_DONG_GOP]


def chia_lo_gop(dong, tieu_de="Tin trong giờ im"):
	"""THUẦN: chia các dòng tin gộp thành nhiều tin, mỗi tin <= TOI_DA_KY_TU.

	Codex #413 P1: trước đây gộp hết vào MỘT tin rồi cắt ở 2.000 ký tự, việc
	sau điểm cắt mất mà vẫn bị đánh dấu đã gửi. Giờ mỗi dòng nằm trọn trong
	đúng một tin; trả [(nội dung, [chỉ số dòng trong tin đó])]. Không dòng nào
	bị cắt giữa chừng, không dòng nào bị bỏ."""
	nhom, cur, dai = [], [], 0
	chua = TOI_DA_KY_TU - 120  # chừa dòng đầu "📊 BẢN TIN: ... (phần i/k, n tin)"
	for i, d in enumerate(dong):
		them = len(d) + 3  # "\n- "
		if cur and dai + them > chua:
			nhom.append(cur)
			cur, dai = [], 0
		cur.append(i)
		dai += them
	if cur:
		nhom.append(cur)
	ra, k = [], len(nhom)
	for j, idx in enumerate(nhom):
		tieu = "%s (%s tin%s)" % (tieu_de, len(idx), (", phần %s/%s" % (j + 1, k)) if k > 1 else "")
		ra.append((soan_tin("ban_tin", tieu, [dong[i] for i in idx]), idx))
	return ra


def con_can_lam(kiem, nguon, ham):
	"""THUẦN: tin còn cần gửi không. kiem rỗng là tin không gắn việc nào.

	ham(nguon) do bên chạm hệ cấp; ném lỗi thì vẫn gửi (thà nhắc thừa còn hơn
	mất việc) và để người gọi ghi log."""
	if not kiem:
		return True
	return bool(ham(nguon))


def ghi_chat_moi(ds, cap_nhat, luc, bot=None):
	"""THUẦN: thêm cuộc chat vừa nhắn bot vào đầu danh sách, bỏ trùng, giữ 20.

	v606: bot là số bot nhận cập nhật ("1" bot chính, "2", "3"... bot thêm); ghi
	kèm để biết gửi tin vào nhóm này bằng bot nào.

	v591: giữ mốc "chao" (lần cuối bot trả lời mã nhóm) của dòng cũ, để không
	trả lời nhóm mỗi lần có người @nhắc bot."""
	msg = (cap_nhat or {}).get("message") or (cap_nhat or {}).get("result", {}).get("message") or {}
	chat = msg.get("chat") or {}
	cid = str(chat.get("id") or "").strip()
	if not cid:
		return ds or [], None
	nguoi = (msg.get("from") or {}).get("display_name") or ""
	moi = {"chat_id": cid, "loai": chat.get("chat_type") or chat.get("type") or "",
		"ten": chat.get("title") or chat.get("display_name") or nguoi, "nguoi": nguoi, "luc": str(luc)[:16]}
	if bot is not None:
		moi["bot"] = ma_bot(bot)
	cu = [x for x in (ds or []) if x.get("chat_id") == cid]
	if cu and cu[0].get("chao"):
		moi["chao"] = cu[0]["chao"]
	con = [x for x in (ds or []) if x.get("chat_id") != cid]
	return ([moi] + con)[:GIU_CHAT_MOI], moi


# v591: anh Việt 12/10/2026 nối nhóm thứ hai không được. Zalo không gửi tên nhóm
# trong cập nhật (chỉ có tên người nhắn), nên hai nhóm cùng hiện "Viet Nguyen" và
# không phân biệt được. Cách gỡ: mỗi nhóm có một MÃ NGẮN (4 ký tự cuối mã chat);
# bot trả lời mã đó ngay trong nhóm, và hộp chọn trong ERP hiện đúng mã đó.
CHAO_PHUT = 60


def ma_ngan(chat_id):
	"""THUẦN: 4 ký tự cuối của mã chat, viết hoa, để đối chiếu giữa nhóm Zalo và ERP."""
	c = str(chat_id or "").strip()
	if c.lower().startswith("zgr-"):
		c = c[4:]
	return c[-4:].upper()


def can_chao(ds_cu, chat_id, luc, phut=CHAO_PHUT):
	"""THUẦN: bot có nên trả lời mã nhóm không. Lần đầu nhóm nhắc bot thì có; đã trả
	lời trong `phut` phút gần đây thì không (tránh trả lời mỗi lần có người @nhắc)."""
	from datetime import datetime
	cid = str(chat_id or "").strip()
	cu = [x for x in (ds_cu or []) if isinstance(x, dict) and str(x.get("chat_id") or "").strip() == cid]
	moc = (cu[0].get("chao") if cu else "") or ""
	if not moc:
		return True
	try:
		a = datetime.strptime(str(moc)[:16], "%Y-%m-%d %H:%M")
		b = datetime.strptime(str(luc)[:16], "%Y-%m-%d %H:%M")
	except Exception:
		return True
	return (b - a).total_seconds() >= phut * 60


def soan_chao(ma):
	"""THUẦN: tin bot trả lời trong nhóm vừa @nhắc bot."""
	return ("✅ ERP Vagabond đã nhận nhóm Zalo này. Mã nhóm: %s\n"
		"Để nhóm nhận tin từ ERP: vào app ERP > Cài đặt > Zalo bắn tin nhóm, mở hoặc thêm dòng của nhóm, "
		"bấm \"Chọn nhóm đã nhắn bot\" rồi chọn dòng \"Nhóm Zalo mã %s\".\n"
		"Không cần trả lời tin này." % (ma, ma))


def ds_nhom_chon(chat_moi, bang):
	"""THUẦN: danh sách NHÓM đã @nhắc bot cho hộp chọn, mới nhất trước, kèm mã ngắn và
	dòng nào trong bảng đang dùng nhóm đó. Chat riêng không bao giờ vào danh sách."""
	gan = {}
	for r in bang or []:
		c = str(r.get("chat_id") or "").strip()
		if c:
			gan.setdefault(c, []).append(str(r.get("ten_nhom") or "").strip() or "dòng chưa đặt tên")
	ra = []
	for x in chat_moi or []:
		if not isinstance(x, dict) or str(x.get("loai") or "").upper() != "GROUP":
			continue
		c = str(x.get("chat_id") or "").strip()
		if not c:
			continue
		ra.append({"chat_id": c, "ma": ma_ngan(c), "luc": str(x.get("luc") or ""), "nguoi": x.get("nguoi") or "",
			"dang_gan": gan.get(c, [])})
	ra.sort(key=lambda r: r["luc"], reverse=True)
	return ra


# ------------------------------------------------------- NHIỀU BOT (v606)
# Anh Việt 19/10/2026: thêm bot vào nhóm thứ ba thì Zalo báo "Bot đã vượt quá số
# lượng nhóm có thể tham gia". Mỗi bot Zalo chỉ vào được một số nhóm giới hạn
# (tài liệu bot.zaloplatforms.com không ghi con số; thực tế bot chính đứng ở hai
# nhóm thì bị chặn). Anh chốt 20/10: thêm được NHIỀU bot, không chỉ hai. Mỗi
# nhóm gửi bằng bot đang ở trong nhóm đó.
#
# Bot chính là số "1" (giữ nguyên ba ô cũ của Cài đặt). Bot thêm nằm ở bảng
# "Bot thêm" (Vagabond Bot Zalo), mỗi dòng một số "2", "3"... máy cấp, KHÔNG
# BAO GIỜ cấp lại số đã dùng (ô zalo_bot_ma_cuoi), để nhóm đang trỏ vào một bot
# đã xoá không vô tình sang bot mới. Token và khoá bí mật của bot thêm cất mã
# hoá trong kho mật khẩu của Frappe dưới tên ô có đuôi số bot, không nằm trong
# bảng, nên không lộ ra lưới hay API đọc bảng.
BOT_CHINH = "1"


def ma_bot(x):
	"""THUẦN: số bot dạng chữ ("1", "2"...). Trống, lạ, nhỏ hơn 1 thì là bot chính."""
	s = str(x if x is not None else "").strip()
	try:
		n = int(s)
	except (TypeError, ValueError):
		return BOT_CHINH
	return str(n) if n >= 1 else BOT_CHINH


def cac_bot(bot_them):
	"""THUẦN: danh sách số bot đang có: bot chính rồi các dòng bảng Bot thêm đã có số."""
	ra = [BOT_CHINH]
	for r in bot_them or []:
		m = str((r or {}).get("ma_bot") or "").strip()
		if m and ma_bot(m) == m and m not in ra:
			ra.append(m)
	return ra


def ma_bot_moi(cac, ma_cuoi):
	"""THUẦN: số cho bot thêm mới: lớn hơn mọi số đang có VÀ mọi số từng cấp."""
	try:
		cuoi = int(ma_cuoi or 1)
	except (TypeError, ValueError):
		cuoi = 1
	return str(max([int(ma_bot(x)) for x in (cac or [])] + [cuoi, 1]) + 1)


def gan_ma_bot(bot_them, ma_cuoi):
	"""THUẦN: dòng Bot thêm chưa có số (thêm tay ở lưới) thì cấp số. Trả
	([(chỉ số dòng, số)], số cuối mới)."""
	cac = cac_bot(bot_them)
	ra = []
	for i, r in enumerate(bot_them or []):
		if not str((r or {}).get("ma_bot") or "").strip():
			m = ma_bot_moi(cac, ma_cuoi)
			cac.append(m)
			ma_cuoi = int(m)
			ra.append((i, m))
	try:
		ma_cuoi = max(int(ma_cuoi or 1), max(int(x) for x in cac))
	except (TypeError, ValueError):
		pass
	return ra, ma_cuoi


def o_mat(loai, ma):
	"""THUẦN: tên ô trong kho mật khẩu: bot chính dùng ô cũ ("zalo_bot_token",
	"zalo_bi_mat"), bot thêm thêm đuôi số ("zalo_bot_token_3")."""
	m = ma_bot(ma)
	return loai if m == BOT_CHINH else "%s_%s" % (loai, m)


def ten_cua_bot(ma, bot_them):
	"""THUẦN: tên đọc được của bot cho lời báo và thẻ nhóm."""
	m = ma_bot(ma)
	if m == BOT_CHINH:
		return "bot chính"
	for r in bot_them or []:
		if str((r or {}).get("ma_bot") or "").strip() == m:
			return str((r or {}).get("ten_bot") or "").strip() or "bot số %s" % m
	return "bot số %s" % m


def bot_cua_chat(chat_id, nhom, chat_moi, cac=None):
	"""THUẦN, NGUỒN DUY NHẤT: gửi vào chat này bằng bot nào.

	Dòng Nhóm nhận tin có ô bot thì theo ô đó (Cài đặt tự điền khi lưu, xem
	dien_bot); chat chưa có dòng (gửi thử, trả lời mã nhóm) thì theo bot đã nhận
	cập nhật của chat đó; không biết, hoặc bot đó đã bị xoá khỏi bảng, thì bot chính."""
	cac = cac or [BOT_CHINH]
	c = str(chat_id or "").strip()
	for r in nhom or []:
		if isinstance(r, dict) and str(r.get("chat_id") or "").strip() == c and str(r.get("bot") or "").strip():
			m = ma_bot(r.get("bot"))
			return m if m in cac else BOT_CHINH
	for x in chat_moi or []:
		if isinstance(x, dict) and str(x.get("chat_id") or "").strip() == c and x.get("bot") is not None:
			m = ma_bot(x.get("bot"))
			return m if m in cac else BOT_CHINH
	return BOT_CHINH


def dien_bot(ds, chat_moi):
	"""THUẦN: [(chỉ số dòng, số bot)] cần ghi vào ô bot của bảng Nhóm nhận tin.

	Bằng chứng là bot đã nhận cập nhật của nhóm (Chat vừa nhắn bot). Dòng không
	còn trong danh sách đó (chỉ giữ 20 chat) thì giữ nguyên; ô trống thì về bot chính."""
	biet = {}
	for x in chat_moi or []:
		if isinstance(x, dict) and x.get("bot") is not None:
			biet.setdefault(str(x.get("chat_id") or "").strip(), ma_bot(x.get("bot")))
	ra = []
	for i, r in enumerate(ds or []):
		c = str((r or {}).get("chat_id") or "").strip()
		cu = str((r or {}).get("bot") or "").strip()
		moi = biet.get(c) if c in biet else (ma_bot(cu) if cu else BOT_CHINH)
		if cu != moi:
			ra.append((i, moi))
	return ra


def bot_theo_bi_mat(gui_len, bi_mat):
	"""THUẦN: số bot có khoá bí mật trùng header Zalo gửi lên, None nếu không bot nào.

	bi_mat: {số bot: khoá}. So bằng compare_digest với MỌI khoá (không dừng sớm),
	khoá rỗng hay quá ngắn bỏ qua."""
	g = str(gui_len or "")
	trung = None
	for b in sorted((bi_mat or {}), key=lambda x: int(ma_bot(x))):
		k = str((bi_mat or {}).get(b) or "")
		if len(k) >= 16 and hmac.compare_digest(g, k) and trung is None:
			trung = ma_bot(b)
	return trung


# --------------------------------------------------------------- CHẠM HỆ

def _bot_them():
	"""Dòng bảng Bot thêm. Lỗi đọc thì để lỗi đi lên (Codex #492): đoán bừa bot
	chính là gửi bằng một bot không ở trong nhóm, Zalo từ chối và tin mất."""
	return [r.as_dict() for r in (frappe.get_single("Vagabond Settings").get("zalo_bot_phu") or [])]


def _mat(loai, bot=BOT_CHINH):
	"""Đọc token hay khoá bí mật của một bot từ kho mật khẩu. Không ghi ra đâu.

	Chưa khai thì trả rỗng. Codex #492 (P2, 4324386326): ĐỌC LỖI (kho mật khẩu,
	cơ sở dữ liệu, giải mã) thì để lỗi đi lên, không đổi thành rỗng: rỗng là "chưa
	điền token", tin ghi Lỗi và mất, trong khi lỗi đọc chỉ là tạm thời."""
	if ma_bot(bot) == BOT_CHINH:
		return frappe.get_single("Vagabond Settings").get_password(loai, raise_exception=False) or ""
	from frappe.utils.password import get_decrypted_password
	return get_decrypted_password("Vagabond Settings", "Vagabond Settings", o_mat(loai, bot), raise_exception=False) or ""


def _token(bot=BOT_CHINH):
	return _mat("zalo_bot_token", bot)


def _doc_chat_moi():
	"""Đọc thẳng bảng (không qua bộ nhớ đệm) danh sách Chat vừa nhắn bot. Lỗi đọc
	thì để lỗi đi lên, xem _bot_chat."""
	v = frappe.db.sql("select value from `tabSingles` where doctype='Vagabond Settings' and field='zalo_chat_moi'")
	ds = json.loads((v[0][0] if v else None) or "[]")
	return ds if isinstance(ds, list) else []


def _bot_chat(chat_id):
	"""Bot gửi vào chat này. Codex #492 (P2): KHÔNG nuốt lỗi đọc Cài đặt rồi đoán
	bot chính; lỗi đi lên để _gui_zalo dừng trước khi gọi Zalo và trả về gửi lại."""
	return bot_cua_chat(chat_id, _cac_nhom(), _doc_chat_moi(), cac_bot(_bot_them()))


def _bat():
	return cint(frappe.db.get_single_value("Vagabond Settings", "zalo_bot_bat"))


def _cac_nhom():
	return [r.as_dict() for r in (frappe.get_single("Vagabond Settings").get("zalo_nhom") or [])]


def _goi(method, body, bot=BOT_CHINH, token=None):
	"""Gọi Zalo Bot API. Trả (trạng thái, lỗi, kết quả). Không ghi token ra đâu.

	Codex #423: mọi đường ra Zalo (gửi ngay, xả giờ im, gửi thử, nối bot) đi
	qua đây, nên chặn chế độ kiểm thử ngay tại cửa này. Tin đã gửi không rút
	lại được, ca bench quên giả lập cũng không được bắn vào nhóm thật.

	v606: bot là số bot gửi; token chỉ truyền khi kiểm một token vừa dán, chưa lưu."""
	if getattr(frappe.flags, "vagabond_kiem_that", False):
		return "Lỗi", "Đang chạy kiểm thử trên site: không gọi Zalo.", None
	try:
		tk = token or _token(bot)
	except Exception as e:
		# Codex #492 (P2): đọc token lỗi tạm thời thì chưa gửi gì, trả MANG_LOI để
		# hàng đợi gửi lại; lỗi chết giao dịch vẫn đi lên.
		if chet_giao_dich(e):
			raise
		return MANG_LOI, "Chưa đọc được token bot (%s), máy sẽ gửi lại." % type(e).__name__, None
	if not tk:
		return "Lỗi", ("Chưa điền token Zalo Bot trong Cài đặt." if ma_bot(bot) == BOT_CHINH
			else "Chưa có token của bot số %s trong Cài đặt." % ma_bot(bot)), None
	try:
		import requests
	except Exception:
		return "Lỗi", "Máy chủ thiếu thư viện gọi mạng.", None
	try:
		r = requests.post("%s/bot%s/%s" % (API, tk, method), json=body, timeout=TIMEOUT)
		if (getattr(r, "status_code", 200) or 200) >= 500:
			# Codex #428 vòng 13: cổng trung gian lỗi (502, 504) kể cả khi thân là JSON hợp
			# lệ: Zalo có thể đã nhận tin trước đó, nên không rõ, không phải bị từ chối.
			return "Chưa rõ", "Zalo trả HTTP %s, không rõ tin đã tới chưa." % r.status_code, None
		try:
			goi = r.json()
		except Exception:
			# Codex #428 vòng 12: Zalo có thể đã nhận tin rồi trả trang lỗi (502, 504) hoặc
			# bị cắt giữa chừng: không rõ đã tới chưa.
			return "Chưa rõ", "Zalo trả HTTP %s không đọc được, không rõ tin đã tới chưa." % r.status_code, None
		tt, loi = doc_ket_qua(goi)
		return tt, loi, (goi.get("result") if isinstance(goi, dict) else None)
	except Exception as e:
		# Codex #425 vòng 11: chưa mở được kết nối thì chắc chắn chưa gửi, trả về để gửi
		# lại. Mọi lỗi khác (hết giờ chờ trả lời, đứt giữa chừng) thì tin có thể đã tới:
		# ghi Chưa rõ để người đối chiếu, không gửi lại tự động.
		if chua_gui_di(e):
			return MANG_LOI, "Chưa kết nối được Zalo (%s), máy sẽ gửi lại." % type(e).__name__, None
		if "Timeout" in type(e).__name__:
			return "Chưa rõ", "Zalo không trả lời trong %s giây." % TIMEOUT, None
		return "Chưa rõ", "Đứt kết nối với Zalo (%s), không rõ tin đã tới chưa." % type(e).__name__, None


# Codex #428 vòng 12: lỗi làm chết cả giao dịch (MariaDB đã tự rollback hết, kể cả
# savepoint). Không được nuốt: chứng từ phải báo lỗi chứ không được báo thành công.
# v577 (Codex #444 vòng 5): dời sang vagabond/loi_csdl.py để phiếu thu dùng chung.
from vagabond.loi_csdl import LOI_CHET_GIAO_DICH, MA_CHET_GIAO_DICH, chet_giao_dich  # noqa: E402,F401


def loi_get_me(tt, loi):
	"""THUẦN: câu báo cho quản trị sau khi gọi getMe, rỗng là token dùng được.

	Codex #428 vòng 14: Zalo trục trặc tạm thời (hết giờ, 5xx, chưa kết nối được)
	không có nghĩa token sai; báo thử lại sau, đừng bảo người ta đổi token đúng."""
	if tt == "Đã gửi":
		return ""
	if tt in ("Chưa rõ", MANG_LOI):
		return ("Chưa kiểm được token vì Zalo đang không trả lời ổn định (%s). Token CHƯA bị coi là sai, "
			"đừng đổi token; bấm Nối Zalo Bot lại sau ít phút." % loi)
	return "Token Zalo Bot chưa đúng. %s" % loi


def chua_gui_di(e):
	"""THUẦN: True nếu lỗi xảy ra trước khi gửi được gì tới Zalo (DNS, không mở được
	kết nối, proxy từ chối). Dò cả chuỗi lỗi bọc nhau của requests và urllib3."""
	thay, hang = set(), [e]
	while hang:
		x = hang.pop()
		if not isinstance(x, BaseException) or id(x) in thay:
			continue
		thay.add(id(x))
		if type(x).__name__ in LOI_CHUA_GUI:
			return True
		hang += [x.__cause__, x.__context__, getattr(x, "reason", None)] + list(getattr(x, "args", ()) or ())
	return False


def goi_gui(chat_id, tin, anh=None):
	"""THUẦN (v613): (method, body) cho Zalo Bot API. Có ảnh thì sendPhoto, chữ thành
	chú thích (tối đa 2.000 ký tự, đúng giới hạn sendPhoto); không thì sendMessage."""
	anh = str(anh or "").strip()
	if anh:
		return "sendPhoto", {"chat_id": str(chat_id), "photo": anh, "caption": tin_soan_san(tin)}
	return "sendMessage", {"chat_id": str(chat_id), "text": tin}


def _gui_zalo(chat_id, tin, anh=None):
	# v606: mọi đường gửi (gửi ngay, xả giờ im, trả lời mã nhóm, gửi thử) đi qua
	# đây, nên chọn bot ở đây theo một nguồn duy nhất bot_cua_chat.
	# Codex #492 (P2): chưa đọc được bot của nhóm thì chưa gửi gì, trả MANG_LOI để
	# hàng đợi gửi lại sau, không gửi bằng bot khác (bot không ở trong nhóm thì Zalo
	# từ chối, tin ghi Lỗi và mất). Lỗi làm chết giao dịch vẫn đi lên như mọi chỗ khác.
	try:
		bot = _bot_chat(chat_id)
	except Exception as e:
		if chet_giao_dich(e):
			raise
		return MANG_LOI, "Chưa đọc được bot gửi của nhóm (%s), máy sẽ gửi lại." % type(e).__name__
	method, body = goi_gui(chat_id, tin, anh)
	tt, loi, _ = _goi(method, body, bot)
	return tt, loi


def cat_dong(ds, toi_da=12, don_vi="đơn"):
	"""THUẦN: tối đa toi_da dòng chi tiết, phần còn lại gom thành "... và N đơn nữa".

	v604: thư cũ kê hết danh sách; tin Zalo chỉ có 2.000 ký tự và đọc trên điện
	thoại, nên chỉ kê vài dòng đầu rồi chỉ màn có đủ danh sách."""
	ds = [str(x) for x in (ds or []) if str(x or "").strip()]
	if len(ds) <= toi_da:
		return ds
	return ds[:toi_da] + ["... và %d %s nữa" % (len(ds) - toi_da, don_vi)]


def bao(loai, chu_de, tieu_de, dong=None, link=None, khoa=None, nguoi=None, han=None, kiem=None, nguon=None,
		ma_tin=None, noi_dung=None, anh=None):
	"""Điểm gọi DUY NHẤT cho mọi nơi trong app. Không ném lỗi ra ngoài, TRỪ lỗi làm chết
	cả giao dịch (deadlock, chờ khoá quá hạn): khi đó chứng từ phải dừng, không được báo
	thành công trong khi cơ sở dữ liệu đã rollback (Codex #428 vòng 12).

	khoa: mã sự kiện để chống trùng (ví dụ "cho_duyet:PKT-2026-00067").
	Thiếu khoa thì không chống trùng (chỉ dùng cho tin một lần).
	kiem, nguon: mã trong DIEU_KIEN và tên chứng từ; trước khi gửi (kể cả sau
	giờ im) máy hỏi lại việc còn mở không, hết việc thì bỏ, không nhắc thừa.
	ma_tin: mã trong TIN (v604); nhóm đã tích Tin nhận chỉ nhận tin có mã khớp.
	noi_dung: tin đã soạn sẵn theo mẫu riêng (v606, báo cáo cuối ngày); có thì
	dùng nguyên văn (cắt ở TOI_DA_KY_TU) thay cho khuôn soan_tin.
	anh: đường dẫn công khai của một ảnh (v613, bảng tồn, sản lượng); có thì gửi
	ảnh, chữ của tin thành chú thích ảnh. Zalo tự tải ảnh từ đường dẫn này.

	Codex #425: ghi tin vào sổ ("Chờ gửi") NGAY TRONG giao dịch của chứng từ,
	rồi mới xếp hàng đợi sau commit. Chứng từ rollback thì tin cũng mất theo;
	Redis hỏng lúc xếp hàng thì tin vẫn nằm trong sổ, nhịp quet_cho_gui gửi bù."""
	try:
		if getattr(frappe.flags, "vagabond_kiem_that", False) or not _bat():
			return
		tin = {"loai": loai, "chu_de": chu_de, "tieu_de": tieu_de, "dong": list(dong or []),
			"link": link, "khoa": khoa, "nguoi": nguoi, "han": han, "kiem": kiem, "nguon": nguon,
			"ma_tin": ma_tin, "noi_dung": noi_dung, "anh": anh}
		ten = _ghi_hop_thu(tin)
		if ten:
			frappe.db.after_commit.add(lambda: _xep(ten))
		return ten
	except Exception as e:
		if chet_giao_dich(e):
			raise
		frappe.log_error("Chưa ghi được tin Zalo loại %s." % loai, "kenh_zalo: bao loi")


def bao_hoac_ghi_loi(loai, chu_de, tieu_de, dong=None, **kw):
	"""Như bao(), cho tin chỉ có MỘT dịp báo (hook lúc tạo phiếu, nhịp lịch): không
	nhóm nào nhận thì để lại Error Log hành động được, nêu tên tin và chứng từ
	(v597 Codex #481, v604). Trả tên các dòng như bao()."""
	ten = bao(loai, chu_de, tieu_de, dong, **kw)
	if not ten and not getattr(frappe.flags, "vagabond_kiem_that", False):
		# v604: nhịp lặp (23:55, 2h, 8h25) gọi lại cùng khoá thì bao() trả rỗng vì tin
		# đã nằm trong sổ, không phải vì thiếu nhóm. Chỉ ghi lỗi khi thật sự không có
		# nhóm nào nhận; đọc cài đặt hỏng thì coi như chưa có nhóm (thà báo thừa).
		try:
			co_nhom = bool(_bat()) and bool(chon_nhom(_cac_nhom(), loai, chu_de, kw.get("ma_tin")))
		except Exception:
			co_nhom = False
		if co_nhom:
			return ten
		t, loi = chu_chua_nhom(loai, chu_de, kw.get("nguon"), kw.get("ma_tin"))
		try:
			frappe.log_error(title=t, message=loi)
		except Exception:
			pass
	return ten


def _ghi_hop_thu(tin):
	"""Ghi mỗi nhóm khớp một dòng "Chờ gửi" trong giao dịch hiện tại. Trả tên các dòng mới.

	Mỗi dòng có savepoint riêng: trùng khoá (sự kiện đã ghi) hay lỗi lẻ thì lùi
	đúng dòng đó, không đụng tới chứng từ đang lưu."""
	noi_dung = tin_soan_san(tin.get("noi_dung")) or soan_tin(tin.get("loai"), tin.get("tieu_de"),
		tin.get("dong"), tin.get("link"), tin.get("nguoi"), tin.get("han"))
	if khong_duoc_tien(tin.get("ma_tin")):
		noi_dung, bo = bo_dong_tien(noi_dung)
		if bo:
			# Nơi phát soạn lọt số tiền: tin vẫn đi (đã lọc), kỹ thuật biết để sửa nơi phát.
			frappe.log_error("Tin %s mang số tiền, đã bỏ %s chỗ trước khi gửi." % (tin.get("ma_tin"), bo),
				"kenh_zalo: tin don hang lot tien")
	ra = []
	for n in chon_nhom(_cac_nhom(), tin.get("loai"), tin.get("chu_de"), tin.get("ma_tin")):
		ten = khoa_tin(tin.get("khoa") or frappe.generate_hash(length=12), n.get("chat_id"))
		sp = "zl_" + frappe.generate_hash(length=8)
		frappe.db.savepoint(sp)
		try:
			frappe.get_doc({"doctype": "Vagabond Tin Kenh", "name": ten, "khoa": ten,
				"nhom": n.get("ten_nhom"), "chat_id": str(n.get("chat_id")).strip(), "loai": tin.get("loai"),
				"chu_de": tin.get("chu_de"), "noi_dung": noi_dung,
				"kiem": tin.get("kiem") or "", "nguon": tin.get("nguon") or "",
				"ma_tin": tin.get("ma_tin") or "", "anh": tin.get("anh") or "",
				"trang_thai": CHO_GUI}).insert(ignore_permissions=True)
			ra.append(ten)
		except frappe.DuplicateEntryError:
			frappe.db.rollback(save_point=sp)
		except Exception as e:
			if chet_giao_dich(e):
				raise
			frappe.db.rollback(save_point=sp)
			frappe.log_error("Chưa ghi được một dòng tin Zalo loại %s." % tin.get("loai"), "kenh_zalo: ghi tin loi")
	return ra


def _xep(ten):
	try:
		frappe.enqueue("vagabond.kenh_zalo.gui_hang_doi", queue="short", ten=list(ten))
	except Exception:
		# Dòng đã nằm trong sổ ở trạng thái Chờ gửi; quet_cho_gui sẽ gửi bù.
		frappe.log_error("Chưa xếp được %s tin Zalo vào hàng đợi, sẽ gửi bù." % len(ten), "kenh_zalo: hang doi loi")


def _ham_kiem(kiem):
	def ham(nguon):
		return frappe.get_attr(DIEU_KIEN[kiem])(nguon)
	return ham


def _con_can(kiem, nguon):
	"""Hỏi lại việc còn mở không. Mã lạ hoặc hàm lỗi: vẫn gửi, có log không lộ nội dung."""
	if kiem and kiem not in DIEU_KIEN:
		frappe.log_error("Mã kiểm tin Zalo lạ: %s" % kiem, "kenh_zalo: ma kiem la")
		return True
	try:
		return con_can_lam(kiem, nguon, _ham_kiem(kiem) if kiem else None)
	except Exception:
		frappe.log_error("Không kiểm lại được việc của tin Zalo (%s)." % kiem, "kenh_zalo: kiem lai loi")
		return True


def gui_hang_doi(ten):
	"""Chạy trong worker: gửi các dòng Chờ gửi theo tên. Mỗi dòng claim nguyên tử."""
	if not _bat():
		return
	gio = now_datetime().strftime("%H:%M")
	theo_chat = {str(n.get("chat_id") or "").strip(): n for n in _cac_nhom()}
	for t in ten or []:
		_gui_mot(t, theo_chat, gio)


def _nhan_mot(ten):
	"""Claim một dòng Chờ gửi bằng UPDATE có điều kiện; trả dòng nếu lượt này nhận được."""
	ma = frappe.generate_hash(length=20)
	frappe.db.sql("""update `tabVagabond Tin Kenh` set trang_thai='Đang gửi', ma_lo=%s, modified=%s
		where name=%s and trang_thai=%s""", (ma, now_datetime(), ten, CHO_GUI))
	frappe.db.commit()
	r = frappe.db.get_value("Vagabond Tin Kenh", ten, ["name", "chat_id", "loai", "noi_dung", "kiem", "nguon", "ma_lo", "anh"],
		as_dict=True)
	return r if r and r.get("ma_lo") == ma else None


def _gui_mot(ten, theo_chat, gio):
	r = _nhan_mot(ten)
	if not r:
		return
	n = theo_chat.get(str(r.get("chat_id") or "").strip())
	if not n or not cint(n.get("bat")):
		frappe.db.set_value("Vagabond Tin Kenh", ten, {"trang_thai": BO_QUA, "loi": NHOM_TAT,
			"luc_gui": now_datetime()})
		frappe.db.commit()
		return
	if r.get("loai") != "canh_bao" and trong_gio_im(gio, n.get("im_tu"), n.get("im_den")):
		frappe.db.set_value("Vagabond Tin Kenh", ten, {"trang_thai": "Hoãn giờ im"})
		frappe.db.commit()
		return
	# Codex #413 P2: hỏi lại ngay trước HTTP, không tin ảnh chụp lúc tạo tin.
	if not _con_can(r.get("kiem"), r.get("nguon")):
		frappe.db.set_value("Vagabond Tin Kenh", ten, {"trang_thai": BO_QUA, "luc_gui": now_datetime()})
		frappe.db.commit()
		return
	# Codex #425 vòng 9: đổi sang "Chưa rõ" và commit NGAY TRƯỚC khi gọi Zalo, có
	# điều kiện theo mã lô. Nhờ vậy dòng kẹt "Đang gửi" chắc chắn chưa gọi Zalo
	# (quet_cho_gui trả nó về Chờ gửi), còn dòng kẹt "Chưa rõ" thì không tự gửi lại.
	# Lượt đã bị trả về Chờ gửi (mất mã lô) thì dừng, không gửi trùng.
	frappe.db.sql("""update `tabVagabond Tin Kenh` set trang_thai=%s, modified=%s
		where name=%s and ma_lo=%s and trang_thai=%s""", (CHUA_RO, now_datetime(), ten, r.get("ma_lo"), DANG_GUI))
	frappe.db.commit()
	if (frappe.db.get_value("Vagabond Tin Kenh", ten, ["trang_thai", "ma_lo"], as_dict=True) or {}).get("ma_lo") != r.get("ma_lo"):
		return
	tt, loi = _gui_zalo(r.get("chat_id"), r.get("noi_dung"), r.get("anh"))
	if tt == MANG_LOI:
		# Chưa gửi được gì: về Chờ gửi, nhịp quet_cho_gui gửi lại.
		frappe.db.set_value("Vagabond Tin Kenh", ten, {"trang_thai": CHO_GUI, "ma_lo": None, "loi": loi})
	else:
		frappe.db.set_value("Vagabond Tin Kenh", ten, {"trang_thai": tt, "loi": loi, "luc_gui": now_datetime()})
	frappe.db.commit()


def quet_cho_gui():
	"""5 phút một lần: gửi bù các dòng còn Chờ gửi quá 2 phút (hàng đợi hỏng, worker
	chưa chạy). Claim trong _gui_mot nên chạy chồng với worker thường vẫn chỉ gửi một lần."""
	if not _bat():
		return
	from frappe.utils import add_to_date
	# Codex #425 vòng 9: worker chết sau khi nhận mà trước khi gọi Zalo thì dòng kẹt
	# "Đang gửi"; quá KET_PHUT phút thì trả về Chờ gửi, xoá mã lô để lượt cũ (nếu
	# còn sống) không gửi được nữa.
	han = add_to_date(now_datetime(), minutes=-KET_PHUT)
	for cu, moi in ((DANG_GUI, CHO_GUI), ("Đang gửi gộp", "Hoãn giờ im")):
		# Vòng 10: dòng gộp kẹt cũng chưa gọi Zalo (có mốc Chưa rõ), trả về Hoãn giờ im
		# để lượt xả sau gửi lại.
		frappe.db.sql("""update `tabVagabond Tin Kenh` set trang_thai=%s, ma_lo=null, modified=%s
			where trang_thai=%s and modified < %s""", (moi, now_datetime(), cu, han))
	frappe.db.commit()
	ds = frappe.get_all("Vagabond Tin Kenh", filters={"trang_thai": CHO_GUI,
		"creation": ["<", add_to_date(now_datetime(), minutes=-2)]}, pluck="name", order_by="creation asc",
		limit_page_length=100)
	if ds:
		gui_hang_doi(ds)


def _nhan_lo(chat_id, ma_lo):
	"""Claim NGUYÊN TỬ các tin hoãn của một nhóm bằng một câu UPDATE có điều kiện.

	Codex #413 P2: hai lượt xả chạy chồng thì mỗi dòng chỉ đổi được trạng thái
	một lần (khoá dòng của MariaDB), lượt sau đọc theo ma_lo của chính mình nên
	không thấy dòng của lượt trước. Commit TRƯỚC khi gọi Zalo.
	Codex #417: nhận theo mã chat, đổi tên nhóm không làm kẹt tin hoãn."""
	frappe.db.sql("""update `tabVagabond Tin Kenh` set trang_thai='Đang gửi gộp', ma_lo=%s, modified=%s
		where chat_id=%s and trang_thai='Hoãn giờ im' order by creation limit %s""", (ma_lo, now_datetime(), chat_id, LO_GOP))
	frappe.db.commit()
	return frappe.get_all("Vagabond Tin Kenh", filters={"ma_lo": ma_lo},
		fields=["name", "noi_dung", "kiem", "nguon"], order_by="creation asc", limit_page_length=LO_GOP)


def _moc_chua_ro(ten_ds, ma_lo):
	"""Codex #425 vòng 10: đổi đúng các dòng của MỘT phần gộp sang "Chưa rõ" và commit
	ngay trước lời gọi Zalo. Trả True nếu lượt này còn giữ các dòng đó.

	Các dòng một phần được nhận cùng lúc nên bị trả về Hoãn giờ im cùng lúc: hoặc
	còn giữ đủ, hoặc mất hết. Mất thì lượt này dừng, lượt khác đã gửi."""
	frappe.db.sql("update `tabVagabond Tin Kenh` set trang_thai=%s, modified=%s where ma_lo=%s and trang_thai='Đang gửi gộp'"
		" and name in (" + ", ".join(["%s"] * len(ten_ds)) + ")", tuple([CHUA_RO, now_datetime(), ma_lo] + list(ten_ds)))
	frappe.db.commit()
	return all((frappe.db.get_value("Vagabond Tin Kenh", t, ["trang_thai", "ma_lo"], as_dict=True) or {}).get("ma_lo") == ma_lo
		for t in ten_ds)


def _bo_hoan_nhom_tat(dang_bat):
	"""Codex #425 vòng 9: tin hoãn của nhóm đã tắt hoặc bị gỡ khỏi bảng thì ghi Bỏ qua,
	để bật lại nhóm sau này không bắn ra tin cũ."""
	# Giờ lấy từ máy chủ ứng dụng (múi giờ của site), không lấy giờ của MariaDB
	# vì múi giờ cơ sở dữ liệu có thể khác.
	q = "update `tabVagabond Tin Kenh` set trang_thai=%s, loi=%s, luc_gui=%s where trang_thai='Hoãn giờ im'"
	if dang_bat:
		q += " and chat_id not in (" + ", ".join(["%s"] * len(dang_bat)) + ")"
	frappe.db.sql(q, tuple([BO_QUA, NHOM_TAT, now_datetime()] + list(dang_bat)))
	frappe.db.commit()


def xa_gio_im():
	"""Mỗi giờ: nhóm nào hết giờ im mà còn tin hoãn thì gửi tin tổng hợp.

	Codex #413: chia theo độ dài thật, mỗi việc nằm trọn trong một tin và chỉ
	việc nằm trong tin đã gửi mới được ghi "Đã gửi gộp".
	Codex #425 vòng 10: ngay trước mỗi lời gọi Zalo, đúng các dòng của phần đó đổi
	sang "Chưa rõ". Worker chết thì dòng kẹt "Đang gửi gộp" chắc chắn chưa gọi Zalo
	(quet_cho_gui trả về Hoãn giờ im để gửi lại), dòng "Chưa rõ" thì không tự gửi lại."""
	if not _bat():
		return
	gio = now_datetime().strftime("%H:%M")
	nhom = _cac_nhom()
	_bo_hoan_nhom_tat([str(n.get("chat_id") or "").strip() for n in nhom if cint(n.get("bat")) and str(n.get("chat_id") or "").strip()])
	for n in nhom:
		chat = str(n.get("chat_id") or "").strip()
		if not cint(n.get("bat")) or not chat or trong_gio_im(gio, n.get("im_tu"), n.get("im_den")):
			continue
		ma = frappe.generate_hash(length=20)
		ds = _nhan_lo(chat, ma)
		con = []
		for r in ds:
			if _con_can(r.get("kiem"), r.get("nguon")):
				con.append(r)
			else:
				frappe.db.set_value("Vagabond Tin Kenh", r.name, {"trang_thai": BO_QUA, "luc_gui": now_datetime()})
		frappe.db.commit()
		if not con:
			continue
		for tin, idx in chia_lo_gop([dong_gop(r.noi_dung) for r in con]):
			if not _moc_chua_ro([con[i].name for i in idx], ma):
				break
			tt, loi = _gui_zalo(chat, tin)
			if tt == MANG_LOI:
				# Mạng hỏng trước khi gửi: phần này và mọi phần chưa gọi của lô về Hoãn
				# giờ im để lượt xả sau gửi lại; dừng nhóm này.
				for i in idx:
					frappe.db.set_value("Vagabond Tin Kenh", con[i].name, {"trang_thai": "Hoãn giờ im", "ma_lo": None, "loi": loi})
				frappe.db.sql("""update `tabVagabond Tin Kenh` set trang_thai='Hoãn giờ im', ma_lo=null, modified=%s
					where ma_lo=%s and trang_thai='Đang gửi gộp'""", (now_datetime(), ma))
				frappe.db.commit()
				break
			for i in idx:
				frappe.db.set_value("Vagabond Tin Kenh", con[i].name, {
					"trang_thai": "Đã gửi gộp" if tt == "Đã gửi" else tt, "loi": loi, "luc_gui": now_datetime()})
			frappe.db.commit()


# ------------------------------------------------------------ CỬA NGÕ

def _chi_quan_tri():
	if "System Manager" not in frappe.get_roles():
		frappe.throw("Chỉ quản trị được cài kênh Zalo.", frappe.PermissionError)


@frappe.whitelist(allow_guest=True, methods=["POST"])
def nhan():
	"""Zalo gọi khi có người nhắn hoặc @nhắc bot. Chỉ ghi lại mã chat để
	quản trị gán vào nhóm; không lưu nội dung tin nhắn."""
	bi_mat = {}
	try:
		bi_mat[BOT_CHINH] = _mat("zalo_bi_mat", BOT_CHINH)
	except Exception:
		pass
	try:
		# Đọc bảng Bot thêm lỗi thì chỉ bot thêm không vào được lượt này (401, Zalo gọi
		# lại sau); bot chính vẫn nhận như trước v606.
		for b in cac_bot(_bot_them())[1:]:
			bi_mat[b] = _mat("zalo_bi_mat", b)
	except Exception:
		pass
	gui_len = (frappe.get_request_header("X-Bot-Api-Secret-Token") or "") if frappe.request else ""
	# v606: mỗi bot một khoá bí mật; khoá khớp cho biết cập nhật đến từ bot nào. Bot
	# đã xoá khỏi bảng Bot thêm thì khoá của nó không còn được nhận.
	bot = bot_theo_bi_mat(gui_len, bi_mat)
	if not bot:
		frappe.local.response["http_status_code"] = 401
		return {"ok": False}
	try:
		goi = json.loads(frappe.request.data or b"{}")
	except Exception:
		goi = {}
	# Codex #425: hai nhóm nhắn cùng lúc thì hai yêu cầu cùng đọc danh sách cũ rồi
	# ghi đè nhau. Khoá các dòng Cài đặt trước khi đọc, đọc thẳng từ bảng (không
	# qua bộ nhớ đệm), ghi xong commit mới nhả khoá.
	frappe.db.sql("select field from `tabSingles` where doctype='Vagabond Settings' for update")
	cu = []
	try:
		v = frappe.db.sql("select value from `tabSingles` where doctype='Vagabond Settings' and field='zalo_chat_moi'")
		cu = json.loads((v[0][0] if v else None) or "[]")
	except Exception:
		cu = []
	ds, moi = ghi_chat_moi(cu, goi, now_datetime(), bot)
	chao = False
	if moi:
		# v591: nhóm nhắc bot lần đầu (hoặc lâu rồi chưa được trả lời) thì bot trả lời
		# mã nhóm ngay trong nhóm. Ghi mốc trước khi commit để hai lần nhắc liền nhau
		# không cùng trả lời (đã khoá dòng Cài đặt ở trên).
		if str(moi.get("loai") or "").upper() == "GROUP" and can_chao(cu, moi["chat_id"], moi["luc"]):
			moi["chao"] = moi["luc"]
			chao = True
		frappe.db.set_single_value("Vagabond Settings", "zalo_chat_moi", json.dumps(ds, ensure_ascii=False))
		frappe.db.commit()
	if chao:
		try:
			frappe.enqueue("vagabond.kenh_zalo.chao_nhom", queue="short", chat_id=moi["chat_id"])
		except Exception:
			frappe.log_error("Chưa xếp được tin trả lời mã nhóm Zalo %s." % ma_ngan(moi["chat_id"]), "kenh_zalo: chao loi")
	return {"ok": True}


def chao_nhom(chat_id):
	"""Worker (v591): trả lời nhóm vừa @nhắc bot bằng mã nhóm. Lỗi chỉ ghi mã ngắn,
	không ghi mã chat đầy đủ hay token."""
	tt, loi = _gui_zalo(chat_id, soan_chao(ma_ngan(chat_id)))
	if tt != "Đã gửi":
		frappe.log_error("Chưa gửi được tin trả lời mã nhóm Zalo %s: %s" % (ma_ngan(chat_id), loi), "kenh_zalo: chao loi")


@frappe.whitelist()
def nhom_da_nhan_bot():
	"""v591: hộp chọn nhóm trong Cài đặt đọc danh sách MỚI từ máy chủ mỗi lần mở,
	không dùng bản tải lúc mở màn (nhóm vừa nhắc bot sau đó sẽ không hiện)."""
	_chi_quan_tri()
	v = frappe.db.sql("select value from `tabSingles` where doctype='Vagabond Settings' and field='zalo_chat_moi'")
	try:
		cm = json.loads((v[0][0] if v else None) or "[]")
	except Exception:
		cm = []
	return ds_nhom_chon(cm, _cac_nhom())


def _ghi_noi(tt, goi_y, bot=BOT_CHINH):
	"""Ghi kết quả xác minh đường nhận vào Cài đặt để quản trị xem lại: bot chính
	ở ô cũ, bot thêm ở cột Kết quả nối của dòng bot đó."""
	nhan = {"ok": "Đã xác minh", "loi": "Xác minh THẤT BẠI", "chua_ro": "Chưa rõ"}.get(tt, tt)
	chu = "%s lúc %s. %s" % (nhan, str(now_datetime())[:16], goi_y or "")
	if ma_bot(bot) == BOT_CHINH:
		frappe.db.set_single_value("Vagabond Settings", "zalo_noi_trang_thai", chu)
	else:
		frappe.db.set_value("Vagabond Bot Zalo", {"parent": "Vagabond Settings", "ma_bot": ma_bot(bot)}, "trang_thai", chu)
	frappe.db.commit()


def _bao_noi(tt, goi_y, ten_bot="", bot=BOT_CHINH):
	if tt == "ok":
		if ma_bot(bot) != BOT_CHINH:
			return {"ok": 1, "xac_minh": tt, "bot": ten_bot, "ma_bot": ma_bot(bot),
				"loi_nhan": "Đã nối bot số %s (%s) và Zalo đã gọi thử đường nhận thành công. Thêm bot này vào nhóm Zalo mới (nhóm mà bot khác không vào được nữa) rồi @nhắc bot một lần; khi chọn nhóm đó trong Nhóm nhận tin, ERP tự gửi tin bằng bot này." % (ma_bot(bot), ten_bot)}
		return {"ok": 1, "xac_minh": tt, "bot": ten_bot,
			"loi_nhan": "Đã nối bot %s và Zalo đã gọi thử đường nhận thành công. Thêm bot vào nhóm Zalo rồi @nhắc bot một lần, mã nhóm sẽ hiện trong ô Chat vừa nhắn bot." % ten_bot}
	if tt == "loi":
		return {"ok": 0, "xac_minh": tt, "bot": ten_bot,
			"loi_nhan": "Zalo đã lưu đường nhận nhưng gọi thử THẤT BẠI (%s). Chưa dùng được. Kiểm tên miền site rồi bấm Zalo > Kiểm lại đường nhận." % (goi_y or "không rõ lý do")}
	return {"ok": 0, "xac_minh": tt, "bot": ten_bot,
		"loi_nhan": "Chưa biết Zalo có gọi được đường nhận không (%s). Bấm Zalo > Kiểm lại đường nhận sau ít phút." % (goi_y or "chưa rõ")}


def _bot_co_that(bot):
	"""Số bot quản trị bấm phải là bot đang có (bot chính hoặc một dòng Bot thêm)."""
	m = ma_bot(bot)
	if m == BOT_CHINH:
		return m
	if m not in cac_bot(_bot_them()):
		frappe.throw("Không thấy bot số %s trong bảng Bot thêm. Tải lại trang rồi thử lại." % m)
	return m


def _cat_mat(loai, bot, gia_tri):
	"""Cất token hay khoá bí mật của bot thêm vào kho mật khẩu (mã hoá)."""
	from frappe.utils.password import set_encrypted_password
	set_encrypted_password("Vagabond Settings", "Vagabond Settings", gia_tri, o_mat(loai, bot))


@frappe.whitelist(methods=["POST"])
def luu_bot(ma="", ten="", token=""):
	"""v606: thêm một bot (ma trống) hoặc đổi token, tên của bot thêm đã có.

	Kiểm token với Zalo (getMe) TRƯỚC khi lưu, nên token sai không vào được bảng.
	Không nhận token trùng bot khác: hai dòng cùng một bot thì không biết nhóm nào
	gửi bằng dòng nào. Trả số bot để Desk bấm Nối ngay sau đó."""
	_chi_quan_tri()
	token = str(token or "").strip()
	ten = str(ten or "").strip()[:60]
	s = frappe.get_single("Vagabond Settings")
	dong = s.get("zalo_bot_phu") or []
	ma = str(ma or "").strip()
	if ma:
		ma = _bot_co_that(ma)
		if ma == BOT_CHINH:
			frappe.throw("Token bot chính sửa ở ô Token Zalo Bot.")
	elif not token:
		frappe.throw("Dán token của bot mới (Zalo Bot Manager > bot > Token).")
	ten_zalo = ""
	if token:
		tt, loi, toi = _goi("getMe", {}, token=token)
		bao_loi = loi_get_me(tt, loi)
		if bao_loi:
			frappe.throw(bao_loi)
		loi_bot = kiem_bot(toi)
		if loi_bot:
			frappe.throw(loi_bot)
		ten_zalo = (toi or {}).get("account_name") or (toi or {}).get("display_name") or ""
		for m in cac_bot([r.as_dict() for r in dong]):
			if m != ma and hmac.compare_digest(_mat("zalo_bot_token", m), token):
				frappe.throw("Token này đang là của %s. Mỗi bot chỉ khai một lần." % ten_cua_bot(m, [r.as_dict() for r in dong]))
	if not ma:
		ma = ma_bot_moi(cac_bot([r.as_dict() for r in dong]), s.get("zalo_bot_ma_cuoi"))
		s.append("zalo_bot_phu", {"ma_bot": ma, "ten_bot": ten or ten_zalo or "Bot số %s" % ma, "co_token": 1})
		s.zalo_bot_ma_cuoi = int(ma)
	else:
		for r in dong:
			if str(r.ma_bot or "").strip() == ma:
				if ten:
					r.ten_bot = ten
				if token:
					r.co_token = 1
					r.trang_thai = ""
	s.flags.ignore_permissions = True
	s.save(ignore_permissions=True)
	if token:
		_cat_mat("zalo_bot_token", ma, token)
	frappe.db.commit()
	return {"ma_bot": ma, "ten": ten_cua_bot(ma, [r.as_dict() for r in (s.get("zalo_bot_phu") or [])])}


@frappe.whitelist(methods=["POST"])
def dang_ky_webhook(bot=BOT_CHINH):
	"""Quản trị bấm một lần: kiểm token, sinh khoá bí mật, đăng ký đường nhận.

	Codex #413 P1: khoá bí mật mới phải COMMIT trước khi gọi setWebhook, vì
	Zalo gọi thử đường nhận ngay lúc đăng ký từ một yêu cầu khác; và phải đọc
	result.verification chứ không tin ok:true ở ngoài."""
	_chi_quan_tri()
	bot = _bot_co_that(bot)
	tt, loi, toi = _goi("getMe", {}, bot)
	bao_loi = loi_get_me(tt, loi)
	if bao_loi:
		frappe.throw(bao_loi)
	loi_bot = kiem_bot(toi)
	if loi_bot:
		frappe.throw(loi_bot)
	ten_bot = (toi or {}).get("account_name") or (toi or {}).get("display_name") or ""
	bi_mat = _mat("zalo_bi_mat", bot)
	if len(bi_mat) < 16:
		bi_mat = secrets.token_urlsafe(32)
		if bot == BOT_CHINH:
			s = frappe.get_single("Vagabond Settings")
			s.zalo_bi_mat = bi_mat
			s.flags.ignore_permissions = True
			s.save(ignore_permissions=True)
		else:
			_cat_mat("zalo_bi_mat", bot, bi_mat)
	frappe.db.commit()
	duong = get_url("/api/method/vagabond.kenh_zalo.nhan")
	tt, loi, kq = _goi("setWebhook", {"url": duong, "secret_token": bi_mat}, bot)
	if tt != "Đã gửi":
		frappe.throw("Chưa đăng ký được đường nhận. %s" % loi)
	xm, goi_y = doc_xac_minh(kq)
	if xm == "chua_ro":
		tt2, _, kq2 = _goi("testWebhook", {}, bot)
		if tt2 == "Đã gửi":
			xm, goi_y = doc_xac_minh(kq2)
	_ghi_noi(xm, goi_y, bot)
	return dict(_bao_noi(xm, goi_y, ten_bot, bot), duong=duong)


@frappe.whitelist(methods=["POST"])
def kiem_webhook(bot=BOT_CHINH):
	"""Quản trị bấm để Zalo gọi thử lại đường nhận (testWebhook)."""
	_chi_quan_tri()
	bot = _bot_co_that(bot)
	tt, loi, kq = _goi("testWebhook", {}, bot)
	if tt != "Đã gửi":
		xm, goi_y = ("chua_ro", loi) if tt == "Chưa rõ" else ("loi", loi)
	else:
		xm, goi_y = doc_xac_minh(kq)
	_ghi_noi(xm, goi_y, bot)
	return _bao_noi(xm, goi_y, bot=bot)


@frappe.whitelist(methods=["POST"])
def gui_thu(chat_id, loai="thong_bao"):
	"""Gửi một tin mẫu tới đúng một mã chat; không chống trùng, không ghi sổ."""
	_chi_quan_tri()
	if loai not in LOAI:
		loai = "thong_bao"
	tin = soan_tin(loai, "Tin thử từ ERP Vagabond", ["Nếu nhóm thấy tin này là kênh đã nối đúng."],
		get_url("/bep"))
	tt, loi = _gui_zalo(chat_id, tin)
	if tt != "Đã gửi":
		frappe.throw("Gửi thử chưa được (%s). %s" % (tt, loi))
	return {"ok": 1, "loi_nhan": "Đã gửi tin thử."}


@frappe.whitelist()
def xem_truoc(loai="viec"):
	"""Xem trước nội dung một tin mẫu, KHÔNG gửi (Codex #410: tách xem trước với gửi thử)."""
	_chi_quan_tri()
	return {"tin": soan_tin(loai if loai in LOAI else "viec", "Khoản trả trước ERP chờ duyệt: PKT-2026-00000",
		["HĐ 8 của Công ty mẫu, 37.584.000 đ", "Gửi bởi Thu mua lúc 09:30"],
		get_url("/cong-no-phai-tra"), nguoi="Kế toán", han="Trong ngày")}
