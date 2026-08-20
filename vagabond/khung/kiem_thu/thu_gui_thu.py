"""Kiem thu duong thu di, va bo ca canh cho su co email 16/08/2026.

Ca dau tien trong tep nay la ca DAT NHAT trong ca bo kiem thu. No chot rang
`email_sach.hop_le` phai chap nhan dang `Ten <dia chi>`.

Neu ca do do, tuc la ai do vua lam song lai dung cai loi da lam ca tiem
khong gui duoc mot email nao suot nhieu ngay: 117 tren 118 ban ghi mat o
nguoi gui, 26 don mua hang cua Uyen khong toi tay nha cung cap, va khong ai
biet cho toi khi Uyen di hoi.

Chuoi that lay tu Email Account tren site:

    Purchasing The Vagabond <purchasing@thevagabondpatisserie.com>
"""

from vagabond import email_sach as es
from vagabond import gui_thu as gt
from vagabond import trang_thai_thu as tt
from vagabond.khung.kiem_thu.nen import ca, dung, la

# Chuoi that. Frappe dien dang nay vao o `sender` cua Email Queue.
NGUOI_GUI_MUA = "Purchasing The Vagabond <purchasing@thevagabondpatisserie.com>"
NGUOI_GUI_BAN = "Sales The Vagabond <sales@thevagabondpatisserie.com>"

# Dia chi khach go sai da lam rot mot don hom 16/08. Ca nay phai VAN bi
# danh truot, khong duoc noi tay ma nuot luon no.
KHACH_GO_SAI = "nguyenhongthientruc1610@gmail"

# Traceback that, cat tu Error Log.
VET_QUOTEADDR = (
	'File "/usr/lib/python3.14/smtplib.py", line 152, in quoteaddr\n'
	"    if addrstring.strip().startswith('<'):\n"
	"AttributeError: 'NoneType' object has no attribute 'strip'"
)

THAN_THU = (
	"MIME-Version: 1.0\r\n"
	"Content-Type: text/html; charset=utf-8\r\n"
	"Subject: Don mua hang PUR-ORD-2026-00123\r\n"
	"To: ncc@example.com\r\n"
	"\r\n"
	"<p>Kinh gui quy nha cung cap,</p>\r\n"
	"<p>From: day la chu trong than thu, khong duoc dung vao.</p>"
)


# ==================================================== lop 0: va tan goc


@ca("email sạch: dạng Tên <địa chỉ> phải hợp lệ, đây là ca làm sập hệ 16/08")
def _():
	la("người gửi mua", es.hop_le(NGUOI_GUI_MUA), True)
	la("người gửi bán", es.hop_le(NGUOI_GUI_BAN), True)
	la("có nháy kép", es.hop_le('"Sales" <s@v.com>'), True)
	la("chỉ ngoặc nhọn", es.hop_le("<s@v.com>"), True)


@ca("email sạch: vẫn bắt được địa chỉ khách gõ sai, không nới tay quá đà")
def _():
	la("thiếu .com", es.hop_le(KHACH_GO_SAI), False)
	la("thiếu @", es.hop_le("abc"), False)
	la("miền không có chấm", es.hop_le("a@b"), False)
	la("tên bọc địa chỉ hỏng", es.hop_le("Tên <s@v>"), False)
	la("hai địa chỉ một ô", es.hop_le("a@b.com, c@d.com"), False)


@ca("email sạch: bóc đúng phần trong ngoặc nhọn")
def _():
	la("bóc ra", es.boc_dia_chi(NGUOI_GUI_MUA), "purchasing@thevagabondpatisserie.com")
	la("không có ngoặc thì giữ nguyên", es.boc_dia_chi("a@b.com"), "a@b.com")
	la("rỗng", es.boc_dia_chi(None), "")


@ca("email sạch: Email Queue nằm ngoài tầm với của hàm dọn")
def _():
	dung("Email Queue phải được chừa ra", "Email Queue" in es.BO_QUA)
	dung("Communication phải được chừa ra", "Communication" in es.BO_QUA)
	dung("Email Account phải được chừa ra", "Email Account" in es.BO_QUA)
	# Chung tu nghiep vu thi VAN phai bi don, khong duoc chua nham.
	dung("hoá đơn bán vẫn bị dọn", "Sales Invoice" not in es.BO_QUA)
	dung("khách hàng vẫn bị dọn", "Customer" not in es.BO_QUA)


# =============================================== chọn hộp thư theo chứng từ


@ca("gửi thư: đơn mua hàng đi từ hộp thư thu mua, không dùng hộp mặc định")
def _():
	la("đơn mua", gt.chon_hop_thu(None, "Purchase Order"), gt.HOP_THU_MUA)
	la("yêu cầu vật tư", gt.chon_hop_thu("", "Material Request"), gt.HOP_THU_MUA)
	la("hoá đơn bán", gt.chon_hop_thu(None, "Sales Invoice"), gt.HOP_THU_BAN)
	la("báo giá", gt.chon_hop_thu(None, "Quotation"), gt.HOP_THU_BAN)


@ca("gửi thư: hộp thư bản ghi đã mang thì tôn trọng, không đè lên")
def _():
	la("giữ nguyên", gt.chon_hop_thu("Ke Toan", "Purchase Order"), "Ke Toan")


@ca("gửi thư: loại chứng từ lạ thì trả None để phần chạm hệ lấy hộp mặc định")
def _():
	la("lạ", gt.chon_hop_thu(None, "Stock Entry"), None)
	la("không có chứng từ", gt.chon_hop_thu(None, None), None)


# ======================================================= xếp loại lỗi


@ca("xếp loại lỗi: traceback quoteaddr phải ra đúng lỗi người gửi rỗng")
def _():
	la("vết thật", gt.xep_loai_loi(VET_QUOTEADDR), gt.LOI_NGUOI_GUI)


@ca("xếp loại lỗi: hẹp trước rộng sau, không để nhánh mạng nuốt mất")
def _():
	la("sai mật khẩu", gt.xep_loai_loi("535 Authentication failed"), gt.LOI_DANG_NHAP)
	la("địa chỉ nhận", gt.xep_loai_loi("550 Recipient address rejected"),
		gt.LOI_DIA_CHI_NHAN)
	la("hạn mức", gt.xep_loai_loi("552 over quota"), gt.LOI_HAN_MUC)
	la("mạng", gt.xep_loai_loi("socket timed out"), gt.LOI_MANG)
	la("rỗng", gt.xep_loai_loi(""), gt.LOI_KHAC)
	la("không đoán được", gt.xep_loai_loi("chuyện gì đó lạ"), gt.LOI_KHAC)


@ca("xếp loại lỗi: mọi mã lỗi đều có một câu tiếng Việt nói rõ ai phải làm gì")
def _():
	for ma in (gt.LOI_NGUOI_GUI, gt.LOI_DANG_NHAP, gt.LOI_DIA_CHI_NHAN,
			gt.LOI_MANG, gt.LOI_HAN_MUC, gt.LOI_KHAC):
		dung("mã %s phải có câu" % ma, bool(gt.CAU_CHO_NGUOI_DUNG.get(ma)))
	dung("câu cho lỗi thật phải nói là lỗi hệ thống",
		"cấu hình" in gt.cau_loi(VET_QUOTEADDR))


# ======================================================= gửi lại hay không


@ca("gửi lại: bản ghi đã gửi rồi thì tuyệt đối không xếp lại hàng")
def _():
	la("đã gửi", gt.nen_gui_lai("Sent", VET_QUOTEADDR), False)
	la("đang chờ", gt.nen_gui_lai("Not Sent", VET_QUOTEADDR), False)


@ca("gửi lại: lỗi phía mình thì gửi lại, lỗi địa chỉ khách thì phải sửa trước")
def _():
	la("người gửi rỗng", gt.nen_gui_lai("Error", VET_QUOTEADDR), True)
	la("mạng", gt.nen_gui_lai("Error", "socket timed out"), True)
	la("địa chỉ nhận sai", gt.nen_gui_lai("Error", "550 Recipient address rejected"),
		False)
	la("hạn mức", gt.nen_gui_lai("Error", "552 over quota"), False)


# ========================================================= vá dòng From


@ca("vá From: chỉ đụng khối tiêu đề, không đụng chữ From trong thân thư")
def _():
	ra = gt.va_dong_from(THAN_THU, "purchasing@thevagabondpatisserie.com")
	dung("phải thêm dòng From vào tiêu đề",
		ra.startswith("From: purchasing@thevagabondpatisserie.com"))
	dung("chữ From trong thân phải còn nguyên",
		"<p>From: day la chu trong than thu, khong duoc dung vao.</p>" in ra)
	la("chỉ thêm đúng một dòng From", ra.count("From: "), 2)


@ca("vá From: đã có dòng From tử tế rồi thì không đụng vào")
def _():
	co_san = "Subject: x\r\nFrom: a@b.com\r\n\r\nthan thu"
	la("giữ nguyên", gt.va_dong_from(co_san, "c@d.com"), co_san)


@ca("vá From: thiếu đầu vào thì trả nguyên vẹn, không bao giờ làm hỏng thư")
def _():
	la("không có địa chỉ", gt.va_dong_from(THAN_THU, ""), THAN_THU)
	la("thân rỗng", gt.va_dong_from("", "a@b.com"), "")
	la("không có dòng trống ngăn tiêu đề", gt.va_dong_from("chi mot dong", "a@b.com"),
		"chi mot dong")


# =========================================================== báo động


@ca("báo động: gom lỗi theo loại để câu báo nói được cái gì đang hỏng")
def _():
	bang = gt.gom_theo_loai([VET_QUOTEADDR, VET_QUOTEADDR, "550 rejected"])
	la("người gửi rỗng", bang.get(gt.LOI_NGUOI_GUI), 2)
	la("địa chỉ nhận", bang.get(gt.LOI_DIA_CHI_NHAN), 1)


@ca("báo động: câu đầu phải nói ngay chuyện gì, đọc trên điện thoại lúc bận")
def _():
	cau = gt.cau_bao_dong(117, gt.gom_theo_loai([VET_QUOTEADDR] * 117),
		"18:00 16/08", "10:00 20/08")
	dung("dòng đầu là báo động đỏ", cau.split("\n")[0].startswith("BAO DONG DO"))
	dung("phải có con số", "117" in cau)
	dung("phải có mốc giờ", "18:00 16/08" in cau)


@ca("báo động: ngưỡng anh Việt chốt là 5")
def _():
	la("ngưỡng", gt.NGUONG_BAO_DONG, 5)


# ============================== trạng thái hiển thị trên chứng từ


@ca("trạng thái thư: chỉ hàng đợi báo Sent thì màn hình mới được nói Đã gửi")
def _():
	la("Sent", tt.theo_hang_doi("Sent"), tt.DA_GUI)
	la("Not Sent", tt.theo_hang_doi("Not Sent"), tt.DANG_CHO)
	la("Sending", tt.theo_hang_doi("Sending"), tt.DANG_CHO)
	la("Error", tt.theo_hang_doi("Error"), tt.GUI_LOI)
	la("Expired", tt.theo_hang_doi("Expired"), tt.GUI_LOI)


@ca("trạng thái thư: trạng thái lạ thì trả None chứ không đoán bừa là đã gửi")
def _():
	la("lạ", tt.theo_hang_doi("Chuyen La"), None)
	la("rỗng", tt.theo_hang_doi(""), None)
	la("None", tt.theo_hang_doi(None), None)


@ca("trạng thái thư: một đơn hai thư, một thư hỏng thì cột phải hiện Gửi lỗi")
def _():
	la("hỏng lẫn xong", tt.gop_nhieu_thu(["Sent", "Error"]), tt.GUI_LOI)
	la("hỏng lẫn chờ", tt.gop_nhieu_thu(["Not Sent", "Error"]), tt.GUI_LOI)
	la("chờ lẫn xong", tt.gop_nhieu_thu(["Sent", "Not Sent"]), tt.DANG_CHO)
	la("xong hết", tt.gop_nhieu_thu(["Sent", "Sent"]), tt.DA_GUI)
	la("chưa có thư nào", tt.gop_nhieu_thu([]), None)
	la("toàn trạng thái lạ", tt.gop_nhieu_thu(["Chuyen La"]), None)


@ca("trạng thái thư: câu nhắc phải nói việc phải làm, không chỉ mô tả")
def _():
	dung("đang chờ thì bảo đừng bấm lại",
		"bấm lại" in tt.cau_nhac(tt.DANG_CHO))
	dung("gửi lỗi thì mượn đúng câu đã dịch từ mã lỗi",
		tt.cau_nhac(tt.GUI_LOI, VET_QUOTEADDR) == gt.cau_loi(VET_QUOTEADDR))
	dung("chưa gửi thì nói rõ là chưa gửi lần nào",
		"lần nào" in tt.cau_nhac(tt.CHUA_GUI))


@ca("trạng thái thư: chỉ đơn mua hàng và yêu cầu vật tư mang cột này")
def _():
	la("hai loại", sorted(tt.CHUNG_TU_CO_GUI), ["Material Request", "Purchase Order"])


@ca("cứu sự cố: khoảng chốt cứng đúng mấy ngày hỏng, không nhận tham số ngày")
def _():
	dung("bắt đầu 16/08", gt.SU_CO_TU.startswith("2026-08-16"))
	dung("kết thúc 20/08", gt.SU_CO_DEN.startswith("2026-08-20"))
	la("đúng hai nhóm", sorted(gt.SU_CO_NHOM),
		["Material Request", "Purchase Order"])


# ============================ thư gộp nhiều đơn (anh Việt báo 20/08/2026)
#
# Uyên gộp ba đơn vào một lá thư, chỉ đơn đầu hiện "Đã gửi", hai đơn kia
# nằm nguyên ở "Chưa gửi" nên Uyên bấm gửi lại và nhà cung cấp nhận hai
# lần. Đúng lỗi đã chữa hôm 03/08 rồi tái phát khi luồng thư dọn vào mã
# nguồn: bản trong app gom theo ô `reference_name`, mà ô đó chỉ chứa được
# một đơn.


THAN_THU_GOP = (
	"Kính gửi quý nhà cung cấp, đính kèm 3 đơn mua hàng"
	"<table><tr><td>DMH-2026-00134</td><td>1.200.000</td></tr>"
	"<tr><td>DMH-2026-00139</td><td>850.000</td></tr>"
	"<tr><td>DMH-2026-00146</td><td>430.000</td></tr></table>"
)


@ca("thư gộp: dò đủ ba mã đơn nằm trong thân thư, không sót đơn nào")
def _():
	ra = tt.tim_ma_trong_thu(THAN_THU_GOP)
	la("đủ ba mã", sorted(ra),
		["DMH-2026-00134", "DMH-2026-00139", "DMH-2026-00146"])


@ca("thư gộp: mã dài phải đứng trước, nếu không bản sửa đổi bị nuốt")
def _():
	ra = tt.tim_ma_trong_thu("DMH-2026-00133 và DMH-2026-00133-1")
	dung("có cả hai", len(ra) == 2)
	dung("bản sửa đổi đứng trước", ra[0] == "DMH-2026-00133-1")


@ca("thư gộp: nhận cả mã phiếu yêu cầu vật tư, không riêng đơn mua hàng")
def _():
	ra = tt.tim_ma_trong_thu("Phiếu MAT-MR-2026-00007 kèm DMH-2026-00146")
	la("hai mã", sorted(ra), ["DMH-2026-00146", "MAT-MR-2026-00007"])


@ca("thư gộp: mỗi mã chỉ kể một lần dù thân thư nhắc nhiều lần")
def _():
	ra = tt.tim_ma_trong_thu("DMH-2026-00146 ... DMH-2026-00146 ... DMH-2026-00146")
	la("một mã", ra, ["DMH-2026-00146"])


@ca("thư gộp: thư thường không có mã thì trả về danh sách rỗng")
def _():
	la("rỗng", tt.tim_ma_trong_thu("Kính gửi quý khách, xin cảm ơn."), [])
	la("chuỗi None", tt.tim_ma_trong_thu(None), [])


@ca("thư gộp: dò xong vẫn phải hỏi hệ xem mã có thật, hàm thuần chỉ nhặt")
def _():
	import inspect

	nguon = inspect.getsource(tt._cac_chung_tu_cua_thu)
	dung("có kiểm tồn tại", "frappe.db.exists" in nguon)
	dung("có gọi hàm dò", "tim_ma_trong_thu" in nguon)


@ca("thư gộp: nhịp soát gom theo chứng từ chứ không gom theo ô tham chiếu")
def _():
	import inspect

	nguon = inspect.getsource(tt.soat_tu_dong)
	dung("không còn gom theo ô tham chiếu",
		"(x.reference_doctype, x.reference_name)" not in nguon)
	dung("gom qua hàm dò thân thư", "_cac_chung_tu_cua_thu" in nguon)


@ca("thư gộp: hook lúc vào hàng đợi cũng đóng dấu cho mọi đơn trong thư")
def _():
	import inspect

	nguon = inspect.getsource(tt.danh_dau_cho_gui)
	dung("dùng hàm dò thân thư", "_cac_chung_tu_cua_thu" in nguon)


@ca("thư gộp: có đường soát lại quãng dài để vá các đơn đã bị sót")
def _():
	import inspect

	dung("có hàm soát lại", hasattr(tt, "soat_lai"))
	nguon = inspect.getsource(tt.soat_lai)
	dung("chặn người không có quyền sửa đơn", "has_permission" in nguon)
	dung("chặn trần số ngày, không cho quét cả bảng", "min(" in nguon)
	dung("gom qua hàm dò thân thư", "_cac_chung_tu_cua_thu" in nguon)
