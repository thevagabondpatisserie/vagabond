"""Kiem thu: cot Note tren BOM, chip phien ban tren Desk, nut Huong dan.

Ba viec anh Viet giao 25/08/2026, deu xuat phat tu y kien cua ban Khai va
tu mot cho anh Viet nhin ra con thieu:

  1. *"Trong BOM customize them 1 cot giup em, tieu de Note: de ghi chu a"*
  2. *"Anh chinh keo rong cai nay giup em de em xem cai phien ban BOM"*
  3. *"Anh chua thay nut huong dan che bien cua app"*

Viec 2 khong lam duoc bang cach noi cot (be rong cot nam trong user
settings cua tung nguoi, khong co API dat ho), nen chuyen sang gan so
phien ban vao CHIP trang thai. Chip khong bao gio bi cat. Bo ca kiem nay
chot ca cach lam do, de sau nay khong ai lang le doi nguoc lai.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def _khong_chu_thich(ma):
	"""Bo chu thich khoi mot tep JavaScript. THUAN.

	Ca kiem ben duoi soi xem ma nguon co dung vao bang noi bo cua Frappe
	khong. Neu soi ca chu thich thi chinh doan GIAI THICH vi sao khong dung
	vao bang do lai bi cham la vi pham. Tep bom_list.js co dung doan nhu
	vay that, va no dung o do la co ich.
	"""
	ra, i, n = [], 0, len(ma)
	while i < n:
		if ma.startswith("/*", i):
			j = ma.find("*/", i + 2)
			i = n if j < 0 else j + 2
			continue
		if ma.startswith("//", i):
			j = ma.find("\n", i)
			i = n if j < 0 else j
			continue
		ra.append(ma[i])
		i += 1
	return "".join(ra)


def _thuan(tep, ten_hien):
	ma = _doc(tep)
	moc = "# ------------------------------------------------------- phần cần Frappe"
	assert moc in ma, "%s doi cau truc, khong tim thay moc phan thuan" % ten_hien
	ns = {}
	exec(compile(ma.split(moc)[0], ten_hien, "exec"), ns)
	return ns


CT = _thuan("cong_thuc.py", "cong_thuc_thuan")
MA_CT = _doc("cong_thuc.py")
MA_LIST = _doc("public", "js", "bom_list.js")
MA_HOOK = _doc("hooks.py")
MA_MAN = _doc("public", "js", "bep", "32-huong-dan.js")
MA_BOM = _doc("public", "js", "bep", "26-cong-thuc.js")
MA_DUONG = _doc("duong_app.py")
MA_NEN = _doc("public", "js", "bep", "00-nen.js")


# ------------------------------------------------ phep thuan: phien ban


@ca("đuôi số phiên bản rút đúng khỏi mã BOM thật")
def _():
	# Cac ma that doc tren site 25/08/2026.
	la("bản 002", CT["duoi_phien_ban"]("BOM-BTPB00007-002"), "002")
	la("bản 001", CT["duoi_phien_ban"]("BOM-BTPB00001-001"), "001")
	la("mã dài", CT["duoi_phien_ban"]("BOM-BTPB00087-001-1"), "1")


@ca("đuôi phiên bản trả rỗng chứ không trả số giả khi mã không có đuôi số")
def _():
	# Hien so 0 gia con te hon khong hien gi: nguoi doc tuong day la ban
	# dau tien, trong khi that ra may khong biet.
	for xau in ("", None, "BOM", "BOM-BTPB00007-abc", "BOM-"):
		la("mã %r" % (xau,), CT["duoi_phien_ban"](xau), "")


@ca("đuôi phiên bản chịu được khoảng trắng thừa hai đầu")
def _():
	la("có khoảng trắng", CT["duoi_phien_ban"]("  BOM-BTPB00007-002  "), "002")


# ------------------------------------------------ ô Note trên dòng BOM


@ca("ô Note khai trên BOM Item chứ không phải trên đầu phiếu BOM")
def _():
	# Khai nham len BOM la ca cong thuc chi co MOT o ghi chu, trong khi
	# ban Khai can ghi cho TUNG nguyen lieu.
	dung("có khai BOM Item", '"BOM Item": [{' in MA_CT)
	dung("tên ô đúng", '"fieldname": "custom_note"' in MA_CT)
	dung("nhãn đúng như bạn Khải xin", '"label": "Note"' in MA_CT)


@ca("ô Note hiện thẳng trong lưới, không phải mở từng dòng mới thấy")
def _():
	dung("có in_list_view", '"in_list_view": 1' in MA_CT)
	dung("có đặt bề rộng cột", '"columns": 2' in MA_CT)


@ca("ô Note là Small Text chứ không phải Data")
def _():
	# Data cat o 140 ky tu ma khong bao gi. Ghi chu che bien hay dai hon
	# mot dong.
	i = MA_CT.find('"fieldname": "custom_note"')
	dung("tìm thấy khai báo", i > 0)
	doan = MA_CT[i:i + 400]
	dung("dùng Small Text", '"fieldtype": "Small Text"' in doan)
	dung("không dùng Data", '"fieldtype": "Data"' not in doan)


@ca("chữ trong ô Note chảy được sang màn app và bản in")
def _():
	dung("cửa chi_tiet kéo ô ra", 'd.get("custom_note")' in MA_CT)
	dung("màn app hiện Note trên dòng nguyên liệu", "m.note" in MA_BOM)
	dung("nạp từ công thức mang Note sang ghi chú", "ghi_chu: m.note" in MA_MAN)


# ------------------------------------------------ danh sách trên Desk


@ca("danh sách BOM trên Desk gộp chứ không đè lên phần của ERPNext")
def _():
	# ERPNext co san mot bom_list.js. Gan de la xoa trang add_fields ma
	# cac phan khac cua ERPNext dang dua vao.
	dung("có đọc bản cũ ra trước", "frappe.listview_settings['BOM'] || {}" in MA_LIST)
	dung("gộp bằng Object.assign", "Object.assign({}, CU" in MA_LIST)
	dung("giữ add_fields cũ", "(CU.add_fields || []).concat" in MA_LIST)
	dung("gọi lại onload cũ", "CU.onload(lv)" in MA_LIST)


@ca("chip trạng thái BOM có kèm số phiên bản")
def _():
	dung("có dựng tiền tố v", "'v' + v + ' · '" in MA_LIST)
	for nhan in ("Đang dùng", "Nháp", "Bản cũ", "Đã huỷ"):
		dung("có nhãn %s" % nhan, nhan in MA_LIST)


@ca("chip BOM xét đã huỷ và nháp TRƯỚC khi xét bản mặc định")
def _():
	# Mot ban da huy van co the con giu co is_default tu luc no con song.
	# Xet is_default truoc thi ban da huy hien thanh "Dang dung".
	i_huy = MA_LIST.find("docstatus,=,2")
	i_nhap = MA_LIST.find("docstatus,=,0")
	i_md = MA_LIST.find("is_default,=,1")
	dung("tìm thấy cả ba nhánh", min(i_huy, i_nhap, i_md) > 0)
	dung("đã huỷ xét trước mặc định", i_huy < i_md)
	dung("nháp xét trước mặc định", i_nhap < i_md)


@ca("phép rút phiên bản bên JS ra cùng kết quả với bên Python")
def _():
	# Hai ben cung mot phep, viet hai lan bang hai ngon ngu. Ca kiem nay
	# chot rang chung con giong nhau ve CACH LAM.
	dung("bên JS có hàm riêng", "function duoiPhienBan(" in MA_LIST)
	dung("cùng cách cắt theo dấu gạch", ".split('-').pop()" in MA_LIST)
	dung("cùng đòi toàn chữ số", "/^[0-9]+$/.test(duoi)" in MA_LIST)
	dung("không có đuôi số thì trả rỗng", "? duoi : ''" in MA_LIST)


@ca("hook nạp danh sách BOM đặt hẹp trên đúng một doctype")
def _():
	# Quy tac 6: hook rong tren "*" ap len moi doctype ke ca ha tang
	# Frappe. Ngay 16/08 mot hook nhu vay lam ca tiem khong gui duoc email
	# suot bon ngay.
	dung("có khai hook", 'doctype_list_js = {"BOM": "public/js/bom_list.js"}' in MA_HOOK)
	dung("không bắt tất bằng sao", 'doctype_list_js = {"*"' not in MA_HOOK)


@ca("phần nới cột chỉ là khuyến mãi, hỏng cũng không kéo đổ màn hình")
def _():
	# CSS khong khop selector thi nam im. Nhung neu ai do doi sang sua DOM
	# hay ghi vao user settings cua nguoi khac thi phai bat lai.
	ma = _khong_chu_thich(MA_LIST)
	dung("nới bằng CSS", "document.createElement('style')" in ma)
	dung("không đụng vào user settings", "user_settings" not in ma)
	dung("không ghi thẳng vào bảng nội bộ", "__UserSettings" not in ma)
	dung("không sửa DOM của danh sách", "innerHTML" not in ma)
	dung("có chặn chèn hai lần", "getElementById('vgbBomCot')" in ma)


# ------------------------------------------------ nút Hướng dẫn chế biến


@ca("nút Hướng dẫn chế biến nằm ngay trên thẻ công thức")
def _():
	# Anh Viet ve o vuong o dung cho nay: canh ten mon tren the.
	dung("có hàm dựng nút", "function ctNutHd(" in MA_BOM)
	dung("nút gắn vào thẻ", "ctNutHd(x)" in MA_BOM)
	dung("mở đúng món của thẻ đó", "scrHuongDanSoan(mm, mt)" in MA_BOM)


@ca("bấm nút Hướng dẫn không rơi nhầm vào thẻ công thức")
def _():
	# Nut nam LONG trong the. Xet the truoc thi khong bao gio toi luot nut,
	# bam vao nut se mo man Cong thuc chu khong mo Huong dan.
	i_nut = MA_BOM.find("closest('[data-hdm]')")
	i_the = MA_BOM.find("closest('[data-n]')")
	dung("tìm thấy cả hai nhánh", min(i_nut, i_the) > 0)
	dung("nút xét trước thẻ", i_nut < i_the)


@ca("công thức đã huỷ không mời soạn hướng dẫn")
def _():
	# Soan huong dan cho mot cong thuc da huy la dan nguoi ta lam theo ban
	# sai.
	i = MA_BOM.find("function ctNutHd(")
	doan = MA_BOM[i:i + 400]
	dung("có chặn bản đã huỷ", "da_huy" in doan and "return ''" in doan)


@ca("màu nút nói ngay tình trạng, không phải bấm vào mới biết")
def _():
	for lop in (".ct-hd", ".ct-hd.chua", ".ct-hd.lech"):
		dung("có lớp %s" % lop, lop + "{" in MA_NEN)
	dung("cảnh báo soát lại khi công thức đã đổi", "Soát lại HD" in MA_BOM)


@ca("chip lọc bắt được hai câu hỏi nguy hiểm nhất")
def _():
	# "Chua soan" la bep dang lam theo tri nho. "Cong thuc da doi" nguy hon
	# vi nhin vao thi thay du, khong ai nghi la thieu.
	dung("có chip chưa soạn", "'chua', '📋 Chưa soạn'" in MA_BOM)
	dung("có chip công thức đã đổi", "'lech', '⚠️ Công thức đã đổi'" in MA_BOM)
	dung("lọc tại máy chủ chứ không lọc tại máy khách",
		"huong_dan: ctD.hd || null" in MA_BOM)


@ca("cửa danh sách công thức lọc được theo tình trạng hướng dẫn")
def _():
	dung("có tham số lọc", "def danh_sach(tab=None, trang_thai=None, tim=None, huong_dan=None)" in MA_CT)
	dung("lệch lọc riêng chứ không so bằng", 'if huong_dan == "lech":' in MA_CT)
	dung("lọc theo cờ lệch", 'x.get("hd_lech")' in MA_CT)


@ca("gắn tình trạng hướng dẫn bằng MỘT truy vấn cho cả danh sách")
def _():
	# 378 cong thuc ma hoi tung mon la 378 lan chay vong xuong co so du
	# lieu. Man hinh se treo tren dien thoai.
	dung("có hàm gắn theo lô", "def _gan_huong_dan(ra):" in MA_CT)
	dung("hỏi theo lô bằng in", '"ma_mon": ["in", cac_ma[i:i + 300]]' in MA_CT)
	dung("không hỏi từng món", "for x in ra:\n\t\td = co.get" in MA_CT)


@ca("màn hướng dẫn có địa chỉ riêng để lưu dấu trang")
def _():
	dung("có trong danh mục màn", '("HDCB", "Hướng dẫn chế biến", None)' in MA_DUONG)
	dung("có nhánh mở màn", "if (k === 'HDCB') return go(scrHuongDan);" in _doc(
		"public", "js", "bep", "02-trang-chu.js"))


# ------------------------------------------------ trình soạn trên điện thoại


@ca("trình soạn không vẽ lại sau mỗi phím gõ")
def _():
	# Ve lai giua chung la mat con tro va mat ca dong dang go do. Bep
	# truong go mot tay tren dien thoai, mat cho la phai go lai tu dau.
	i = MA_MAN.find("o.oninput = function ()")
	dung("tìm thấy chỗ bắt phím", i > 0)
	# Cat dung den het than ham, khong lay mot cua so co dinh: cua so co
	# dinh se thom sang ham khac va bat nham hdVe() cua ham do.
	j = MA_MAN.find("b.onclick = function", i)
	dung("tìm thấy chỗ kết thúc", j > i)
	doan = MA_MAN[i:j]
	dung("ghi thẳng vào bản đang soạn", "hdE[khoa] = o.value" in doan)
	dung("ghi được cả dòng con", "hdE[bang][vt][khoa] = o.value" in doan)
	dung("không vẽ lại trong lúc gõ", "hdVe()" not in doan)


@ca("trình soạn vẽ lại khi cấu trúc đổi, tức thêm hay bớt dòng")
def _():
	for viec in ("data-xoa", "data-them"):
		i = MA_MAN.find("closest('[%s]')" % viec)
		dung("có nhánh %s" % viec, i > 0)
		dung("nhánh %s có vẽ lại" % viec, "hdVe()" in MA_MAN[i:i + 400])


@ca("ô nhập có nhãn nằm trên, không chỉ dựa vào chữ mờ")
def _():
	# Chu mo bien mat ngay khi go chu dau tien, luc do khong con biet o do
	# la o gi nua.
	dung("có hàm dựng ô có nhãn", "function hdO(nhan, khoa" in MA_MAN)
	dung("nhãn dựng thành thẻ riêng", "'<label class=\"hd-o\"><span>'" in MA_MAN)
	dung("có kiểu cho nhãn", ".hd-o>span{" in MA_NEN)


@ca("chưa lưu thì chưa cho in và chưa cho đính ảnh")
def _():
	# Ca hai deu can ban ghi da co ten tren he. Bam vao luc chua luu ma
	# khong bao gi thi nguoi dung tuong may hong.
	for ham in ("function hdIn()", "function hdChupAnhDat()"):
		i = MA_MAN.find(ham)
		dung("tìm thấy %s" % ham, i > 0)
		dung("%s có chặn khi chưa lưu" % ham, "if (!hdE.name) return toast" in MA_MAN[i:i + 300])


@ca("nút in gọi đúng bản in A4 đã dựng ở v301")
def _():
	dung("gọi printview của máy chủ", "'/printview?doctype='" in MA_MAN)
	dung("đúng tên bản in", "'Vagabond - Hướng dẫn chế biến'" in MA_MAN)
	dung("đúng doctype", "'Vagabond Huong Dan Che Bien'" in MA_MAN)


@ca("nạp định lượng từ công thức có hỏi lại trước khi thay")
def _():
	# Nap de len toan bo phan dinh luong. Lam am tham la xoa mat cong bep
	# truong da go.
	i = MA_MAN.find("function hdNapTuBom()")
	doan = MA_MAN[i:i + 1600]
	dung("có hỏi lại", "confirmSheet(" in doan)
	dung("nói rõ sẽ thay bao nhiêu dòng", "ct.dong.length" in doan)
	dung("nói rõ phần nào KHÔNG bị đụng", "không bị đụng tới" in doan)


@ca("nạp định lượng ghi lại đã soạn theo bản công thức nào")
def _():
	# Khong ghi lai thi sau nay khong may nao biet huong dan da lech khoi
	# cong thuc, va co canh bao "cong thuc da doi" khong bao gio bat len.
	dung("có ghi bản đã soạn theo", "hdE.bom_soan_theo = ct.bom" in MA_MAN)


@ca("bếp phó mở được trình soạn trên điện thoại")
def _():
	# Quyet dinh 3 cua anh Viet ngay 25/08/2026.
	i = MA_MAN.find("function hdSuaDuoc()")
	doan = MA_MAN[i:i + 300]
	dung("có bếp phó", "Bếp phó" in doan)
	dung("có bếp trưởng", "Manufacturing Manager" in doan)


@ca("cảnh báo công thức đã đổi hiện ngay đầu trình soạn")
def _():
	dung("có khối cảnh báo", "Công thức của món này đã đổi" in MA_MAN)
	dung("chỉ hiện khi có cờ", "if (d.cong_thuc_da_doi) {" in MA_MAN)
