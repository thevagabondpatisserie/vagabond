# -*- coding: utf-8 -*-
"""Kiem thu: che do giam doc, va ba sua giao dien anh Viet bao 31/08/2026.

BON VIEC TRONG BO CA KIEM NAY

1. CHE DO GIAM DOC. Anh Viet: *"hien 2 anh giam doc dang co rat nhieu phieu
   can lam tu kho, thu mua,... em don het dum anh. Anh va anh Son chi co nhu
   cau xem phieu duyet APP, duyet phieu nop quy tien mat, duyet hang tang,...
   nhung viec he trong thoi."*

2. CHIP DOI MAU. *"Anh thay cai chip deu dang mau xanh het ca, chang co
   nhung mau khac nen nhin cung roi."*

3. TEP DINH KEM THANH HINH THU NHO. *"Cac nut tai thi ca 3 nut deu ghi la
   tai uy nhiem chi nhung nhan vao lai ra anh bang chung, anh don hang...
   moi tep dinh kem phai trinh bay dang thumbnail, khong de nut tai nhu the."*

4. MAN LAP BIEN NHAN NOP TIEN: anh bat buoc, cau noi dung goi san day du,
   noi giao nhan la danh sach chon, va them o "Nop cho ai".
"""

import io
import json
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import viec_can_lam as vcl

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


# ------------------------------------------------------- 1. che do giam doc


@ca("giám đốc: nhận đúng vai giám đốc, không nhận nhầm vai kỹ thuật")
def _():
	dung("AP Giám đốc là giám đốc", vcl.la_giam_doc({"AP Giám đốc"}))
	dung("Giám đốc là giám đốc", vcl.la_giam_doc({"Giám đốc"}))
	# System Manager la vai KY THUAT. Nguoi giu no co the dang can nhin toan
	# bo de do loi; siet luon ca ho la tu bit mat minh.
	dung("System Manager không bị siết", not vcl.la_giam_doc({"System Manager"}))
	dung("nhân viên thường không phải", not vcl.la_giam_doc({"Stock User"}))
	dung("rỗng không phải", not vcl.la_giam_doc(set()))
	dung("None không làm vỡ hàm", not vcl.la_giam_doc(None))


@ca("giám đốc: chỉ thấy ba việc hệ trọng, mọi việc kho và thu mua đều dọn sạch")
def _():
	gd = {"AP Giám đốc"}
	for k in vcl.VIEC_HE_TRONG:
		dung("giám đốc vẫn thấy %s" % k, vcl.thay_duoc(k, gd))
	for k in ("chuyen_kho", "san_xuat", "nhap_kho", "xuat_kho", "kiem_ke",
			"ycmh", "don_mua", "tang_qua", "de_nghi_chi", "hoan_tien"):
		dung("giám đốc KHÔNG còn thấy %s" % k, not vcl.thay_duoc(k, gd))
	la("đúng ba việc hệ trọng", sorted(vcl.VIEC_HE_TRONG),
		["hang_tang", "ho_so_tt", "nop_quy"])


@ca("giám đốc: vai cộng dồn cũng không mở lại đường vòng")
def _():
	# Day la ly do phai siet o DAU RA chu khong phai sua tung dong ma tran.
	# Anh Viet mang ca vai Giam doc lan cac vai khac; go Giam doc khoi tung
	# dong thi ho van thay viec kho qua vai kia.
	gd_kho = {"AP Giám đốc", "Stock Manager"}
	dung("giám đốc kiêm thủ kho vẫn không thấy việc kho",
		not vcl.thay_duoc("nhap_kho", gd_kho))
	gd_kt = {"AP Giám đốc", "Accounts Manager"}
	dung("giám đốc kiêm kế toán vẫn không thấy hoàn tiền",
		not vcl.thay_duoc("hoan_tien", gd_kt))
	dung("nhưng vẫn thấy hồ sơ thanh toán", vcl.thay_duoc("ho_so_tt", gd_kt))
	# Nguoi KHONG phai giam doc thi khong bi anh huong gi.
	dung("thủ kho vẫn thấy việc kho", vcl.thay_duoc("nhap_kho", {"Stock Manager"}))
	dung("kế toán vẫn thấy hoàn tiền", vcl.thay_duoc("hoan_tien", {"Accounts Manager"}))


@ca("giám đốc: hai loại việc mới khai đủ, và ai được thấy thì rõ ràng")
def _():
	khoa = [k for k, _t, _i in vcl.LOAI_PHIEU]
	for k in ("nop_quy", "hang_tang"):
		dung("%s có trong danh sách loại" % k, k in khoa)
		dung("%s có trong ma trận" % k, k in vcl.MA_TRAN)
	# Don hang tang CHI giam doc, vi ca hang rao sinh ra de tach nguoi tang
	# khoi nguoi duyet. Ke toan thay duoc la mo lai dung cai vua bit.
	dung("kế toán KHÔNG duyệt được đơn tặng",
		not vcl.thay_duoc("hang_tang", {"Accounts Manager"}))
	dung("nộp quỹ thì kế toán thấy", vcl.thay_duoc("nop_quy", {"Accounts Manager"}))
	s = _doc("vagabond", "viec_can_lam.py")
	dung("có nguồn việc nộp quỹ", "def _viec_nop_quy(" in s)
	dung("có nguồn việc hàng tặng", "def _viec_hang_tang(" in s)
	dung("hai nguồn đã nối vào danh sách", '("nop_quy", lambda' in s
		and '("hang_tang", lambda' in s)
	t = _doc("vagabond", "public", "js", "bep", "02-trang-chu.js")
	# Man Viec can lam ma day nguoi ta sang may tinh thi coi nhu khong co man.
	dung("bấm vào phiếu nộp quỹ mở được", "l === 'nop_quy'" in t)
	dung("bấm vào đơn tặng mở được", "l === 'hang_tang'" in t)
	dung("hai loại mới có icon", "nop_quy: '" in t and "hang_tang: '" in t)


# ------------------------------------------------- 2 và 3. màn phiếu hoàn


@ca("giao diện: ba họ chip ba màu, không còn xanh hết cả")
def _():
	s = _doc("vagabond", "public", "js", "bep", "09-tinh-tien-quay.js")
	dung("chip nhận tham số màu", "function posChipNut(attr, chu, dangChon, laXoa, mau)" in s)
	dung("không truyền màu thì vẫn xanh như cũ", "mau || '#0d9488'" in s)
	m = _doc("vagabond", "public", "js", "bep", "40-phieu-hoan-huy.js")
	dung("có bảng màu ba họ chip", "PH_MAU_CHIP" in m)
	for k in ("diem:", "loai:", "tt:"):
		dung("bảng màu có khoá %s" % k, k in m)
	# Ba mau phai KHAC nhau, khong thi sua cung nhu khong.
	i = m.find("var PH_MAU_CHIP")
	khoi = m[i:m.find("\n", i + 60) + 1]
	mau = [x for x in khoi.split("'") if x.startswith("#")]
	la("ba màu khác nhau", len(set(mau)), 3)
	dung("cả ba hàng chip đều truyền màu vào", m.count("PH_MAU_CHIP.") == 3)


@ca("giao diện: tệp đính kèm vẽ thành hình thu nhỏ, không còn nút tải nói sai")
def _():
	m = _doc("vagabond", "public", "js", "bep", "40-phieu-hoan-huy.js")
	dung("có hàm vẽ ô tệp", "function phOTep(" in m)
	dung("ảnh vẽ thành hình", "<img src=" in m and "object-fit:cover" in m)
	dung("tệp khác hiện đuôi tệp thật", "t.duoi" in m)
	dung("mỗi ô mang tên tệp thật", "t.ten" in m)
	# Cai nut noi doi da bien mat.
	dung("không còn nút Tải uỷ nhiệm chi", "Tải uỷ nhiệm chi" not in m)
	# Hai nguon tep ve rieng, khong tron.
	dung("vẽ riêng chứng từ kế toán", "r.unc" in m)
	dung("vẽ riêng ảnh bằng chứng", "r.bang_chung" in m)
	# Bo cuc dong: nhan khoa cung, gia tri an het phan con lai.
	dung("có hàm vẽ một dòng", "function phDong(" in m)
	dung("nhãn khoá chiều rộng", "flex:0 0 118px" in m)
	dung("giá trị ngắt dòng thông minh", "word-break:break-word" in m)
	dung("có nét đứt phân dòng", "border-bottom:1px dashed" in m)


@ca("giao diện: máy chủ trả tên tệp thật, không tự xưng là uỷ nhiệm chi")
def _():
	s = _doc("vagabond", "don_huy.py")
	dung("đã đổi tên hàm cho đúng việc", "def _tep_dinh_kem(" in s)
	dung("hàm cũ nói sai đã bỏ", "def _unc_theo_phieu_chi(" not in s)
	dung("đọc được cả tệp trên hồ sơ hoàn tiền", '_tep_dinh_kem(HT,' in s)
	from vagabond.don_huy import duoi_tep, la_anh

	la("đuôi jpg", duoi_tep("a.jpg"), "JPG")
	la("đuôi pdf", duoi_tep("uy-nhiem-chi.pdf"), "PDF")
	la("không có đuôi", duoi_tep("khongduoi"), "TỆP")
	la("đuôi quá dài thì thôi", duoi_tep("a.khongphaiduoi"), "TỆP")
	la("tên rỗng", duoi_tep(""), "TỆP")
	dung("nhận ảnh", la_anh("a.PNG"))
	dung("pdf không phải ảnh", not la_anh("a.pdf"))


# ------------------------------------------- 4. màn lập biên nhận nộp tiền


@ca("biên nhận: ảnh cọc tiền là bắt buộc, chặn ở máy chủ chứ không chỉ đổi chữ")
def _():
	s = _doc("vagabond", "nop_quy.py")
	i = s.find("def tao_theo_ngay(")
	j = s.find("\n@frappe.whitelist", i + 10)
	than = s[i:j]
	dung("máy chủ chặn khi thiếu ảnh", 'if not (anh_minh_chung or "").strip():' in than)
	dung("câu chặn nói rõ vì sao", "chứng từ gốc" in than)
	m = _doc("vagabond", "public", "js", "bep", "39-bien-nhan-tien.js")
	dung("màn hình ghi rõ bắt buộc", "bắt buộc" in m)
	dung("không còn câu không bắt buộc cho ô ảnh",
		"Không bắt buộc, nhưng có ảnh thì đỡ tranh cãi" not in m)
	dung("màn nhắc trước khi gọi máy chủ", "Chụp ảnh cọc tiền trước đã" in m)


@ca("biên nhận: nơi giao nhận chọn trong danh sách, và có ô Nộp cho ai")
def _():
	m = _doc("vagabond", "public", "js", "bep", "39-bien-nhan-tien.js")
	# Go tay thi mot cho ra nam cach viet, va bao cao gom theo noi giao nhan
	# la vo dung.
	dung("nơi giao nhận là ô chọn", "<select class=\"vfs\" id=\"bntNoi\"" in m)
	dung("ô chọn dựng từ danh sách điểm bán", "dsDiem.map" in m)
	dung("có ô Nộp cho ai", "bntNhan" in m and "Nộp cho ai" in m)
	dung("ô đó gọi cửa tìm người của máy chủ",
		"vagabond.nop_quy.tim_nguoi_nhan" in m)
	dung("gửi người nhận dự kiến lên máy chủ", "nguoi_nhan_du_kien: BNT.nhan" in m)

	s = _doc("vagabond", "nop_quy.py")
	i = s.find("def tim_nguoi_nhan(")
	j = s.find("\n@frappe.whitelist", i + 10)
	than = s[i:j]
	# Chi tra nguoi MANG VAI ky nhan: to bien ban ghi ten mot nguoi khong co
	# quyen nhan tien thi to do sai ngay tu luc in ra.
	dung("chỉ tìm trong người có quyền ký nhận", "VAI_KY_NHAN" in than)
	dung("chỉ lấy tài khoản còn bật", '"enabled": 1' in than)
	# Tim o MAY CHU (QT-19), khong doc ca bang nguoi dung ve roi loc.
	dung("lọc ở tầng cơ sở dữ liệu", "or_filters=hoac" in than)


@ca("biên nhận: hai ô người nhận dự kiến đã khai trong doctype")
def _():
	p = os.path.join(GOI, "vagabond", "vagabond", "doctype",
		"vagabond_nop_quy", "vagabond_nop_quy.json")
	d = json.load(io.open(p, encoding="utf-8"))
	ten = [f["fieldname"] for f in d["fields"]]
	for k in ("nguoi_nhan_du_kien", "ten_nguoi_nhan_du_kien"):
		dung("doctype có ô %s" % k, k in ten)
		dung("ô %s có trong thứ tự hiển thị" % k, k in d.get("field_order", []))
	o = [f for f in d["fields"] if f["fieldname"] == "nguoi_nhan_du_kien"][0]
	la("ô người nhận dự kiến trỏ vào User", o.get("options"), "User")
	s = _doc("vagabond", "nop_quy.py")
	# Chua ai ky nhan thi to in ra phai mang ten nguoi DU KIEN kem chu "(du
	# kien)", khong duoc doc nham thanh da nhan.
	dung("tờ in dùng tên dự kiến khi chưa ký", "ten_nguoi_nhan_du_kien" in s)
	dung("có ghi rõ là dự kiến", "(dự kiến)" in s)


@ca("biên nhận: câu nội dung do máy chủ dựng, màn hình không tự ghép")
def _():
	m = _doc("vagabond", "public", "js", "bep", "39-bien-nhan-tien.js")
	# Ghep o hai noi thi som muon hai noi viet khac nhau, ma cau nay di thang
	# len to bien ban va len so quy.
	dung("màn hình không tự ghép câu",
		"Nộp quỹ tiền mặt doanh thu" not in m)
	dung("màn hình lấy câu từ máy chủ", "k.noi_dung" in m)
	s = _doc("vagabond", "nop_quy.py")
	dung("máy chủ truyền khoảng ngày vào câu",
		"noi_dung_mac_dinh(d[\"ten_ngan\"], tu, den)" in s)
