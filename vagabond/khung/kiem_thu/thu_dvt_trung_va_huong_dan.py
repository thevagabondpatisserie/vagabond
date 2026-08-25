"""Kiem thu: doi don vi trung sang Qua, va Huong dan che bien.

Hai viec anh Viet giao 25/08/2026, nam chung mot bo vi chung tra loi cung
mot cau hoi: cong thuc ghi TRUNG theo QUA thi nguoi dung lam sao biet so
gram cua long trang va long do.

  doi_dvt_bom.py          doi don vi ma khong lam lech mot dong nao
  huong_dan_che_bien.py   cho ghi so gram that, tach ro long trang long do

Ca kiem chot bang chinh so lieu THAT do tren site ngay 25/08/2026, de neu
sau nay ai sua phep tinh thi con so that se to cao ngay.
"""

import io
import json
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	p = os.path.join(GOI, ten)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def _json(*duong):
	p = os.path.join(GOI, *duong)
	return json.load(io.open(p, encoding="utf-8"))


def _thuan(tep, ten_hien):
	ma = _doc(tep)
	moc = "# ------------------------------------------------------- phan can Frappe"
	assert moc in ma, "%s doi cau truc, khong tim thay moc phan thuan" % ten_hien
	ns = {}
	exec(compile(ma.split(moc)[0], ten_hien, "exec"), ns)
	return ns


D = _thuan("doi_dvt_bom.py", "doi_dvt_bom_thuan")
H = _thuan("huong_dan_che_bien.py", "huong_dan_thuan")
MA_D = _doc("doi_dvt_bom.py")
MA_H = _doc("huong_dan_che_bien.py")
MAU = _doc(os.path.join("mau_in", "huong_dan_che_bien.html"))

# So lieu THAT cua dong trung trong BTP White Sponge, doc tren site
# 25/08/2026. Me 1050 gram, cac dong khac cong lai 550 gram.
WS_QTY = 8.3333335
WS_HE_SO = 0.016666667
WS_RATE = 36.399580854
WS_STOCK_QTY = 0.1389
WS_ME = 1050
WS_KHAC = 550


# --------------------------------------------------- doi mot dong BOM

@ca("đổi đơn vị giữ nguyên lượng thật, sai số làm tròn không trôi sang sổ")
def _():
	qty, hs, rate = D["doi_mot_dong"](WS_QTY, WS_HE_SO, WS_RATE, WS_STOCK_QTY)
	la("số lượng mới đúng bằng lượng kho cũ", round(qty, 4), WS_STOCK_QTY)
	la("hệ số về 1", hs, 1.0)
	# 36,3996 / 0,016667 = 2184 dong mot qua. Do la gia trung that.
	la("đơn giá quy về mỗi quả", round(rate), 2184)
	# Cho tinh te: lay `stock_qty` lam so luong moi la co y, vi do la con
	# so ERPNext da chot va no phai KHONG DOI. Doi lai, 0,1389 la ban da
	# lam tron cua 0,13888889, nen nhan lai voi don gia se lech vai xu.
	lech = abs(WS_QTY * WS_RATE - qty * rate)
	dung("sai số làm tròn dưới 5 xu", lech < 0.05)
	dung("nên thành tiền phải được bê nguyên sang, không tính lại",
		 '"amount": k["amount_giu_nguyen"]' in MA_D)


@ca("đổi đơn vị: hệ số hỏng thì trả về nguyên trạng, không chia cho 0")
def _():
	qty, hs, rate = D["doi_mot_dong"](100, 0, 25)
	la("giữ nguyên số lượng", qty, 100.0)
	la("giữ nguyên đơn giá", rate, 25.0)


@ca("đổi đơn vị: tin số lượng kho hơn là nhân lại")
def _():
	qty, _hs, _r = D["doi_mot_dong"](WS_QTY, WS_HE_SO, WS_RATE, WS_STOCK_QTY)
	la("lấy đúng con số kho đã chốt", qty, WS_STOCK_QTY)
	qty2, _h2, _r2 = D["doi_mot_dong"](WS_QTY, WS_HE_SO, WS_RATE, None)
	dung("không có số kho thì tự nhân ra", abs(qty2 - 0.1388889) < 1e-6)


@ca("dòng đã đúng đơn vị kho thì không đụng vào")
def _():
	dung("Gram khác PCS thì đổi", D["can_doi"]("Gram", "PCS"))
	dung("PCS trùng PCS thì thôi", not D["can_doi"]("PCS", "PCS"))
	dung("thiếu đơn vị thì thôi", not D["can_doi"]("", "PCS"))


# ------------------------------------------- soi cong thuc ghi nham

@ca("bắt được đúng ca White Sponge ghi số quả vào ô gram")
def _():
	"""Ca that. Me 1050 gram, cac dong khac 550 gram, con thieu 500 gram.

	O trung dang ghi 8,3333 Gram, tuc 0,1389 qua cho ca me 1050 gram. Nhan
	8,3333 voi 60 ra dung 500 gram con thieu. Nguoi nhap go SO QUA vao o
	GRAM, hut sau muoi lan.
	"""
	co_nghi, thieu, nhu_qua = D["nghi_ghi_nham"](WS_ME, WS_KHAC, WS_QTY)
	dung("có nghi", co_nghi)
	la("còn thiếu gần 500 gram", round(thieu), 492)
	la("hiểu là quả thì ra đúng 500 gram", round(nhu_qua), 500)


@ca("không kêu oan công thức ghi gram đúng")
def _():
	# BTP Pistachio cheesecake: me 526, cac dong khac 471, trung 55 gram.
	# 471 + 55 = 526, khop chan. Day la gram that.
	co_nghi, _t, _q = D["nghi_ghi_nham"](526, 471, 55)
	dung("không nghi", not co_nghi)


@ca("không kêu oan mẻ nhỏ có sai số làm tròn")
def _():
	# BTP VGB Feulletine: me 200, cac dong khac 150, trung 53,33 gram.
	co_nghi, _t, _q = D["nghi_ghi_nham"](200, 150, 53.33)
	dung("không nghi", not co_nghi)


@ca("phép đổi hàng loạt vẫn chặn khi còn công thức nghi ghi nhầm")
def _():
	"""Anh Viet 25/08/2026 cho phep go chan. CO Y GIU LAI.

	Khai sua sau cong thuc do trong ERP, roi moi doi don vi. Khi Khai sua
	xong thi phep soi tu tra ve rong va cai chan tu mo. No khong phai hang
	rao can duong, no la cach may TU BIET Khai da sua xong hay chua.

	Go chan di thi neu Khai chua sua ma minh lo chay, con so sai se khoac
	ao "Qua" nhin rat that, va sai so 60 lan do se nam im trong gia von.
	"""
	than = MA_D.split("def doi_het(")[1]
	dung("có soi trước khi đổi", "soi_ghi_nham(" in than)
	dung("có chặn", "frappe.throw(" in than)
	dung("muốn bỏ qua phải cố ý", "bo_qua_nghi" in than)


@ca("phép đổi hàng loạt mặc định KHÔNG ghi gì")
def _():
	than = MA_D.split("def doi_het(")[1]
	dung("mặc định chạy thử", "def doi_het(chay_that=0" in MA_D)
	dung("phải truyền chay_that mới ghi", "if not chay_that:" in than)


@ca("ghi thẳng nhưng giữ nguyên hai con số sổ sách dựa vào")
def _():
	than = MA_D.split("def doi_het(")[1]
	dung("đặt lại stock_qty đúng bằng cũ", '"stock_qty": k["sau"]["stock_qty"]' in than)
	dung("giữ nguyên thành tiền", '"amount": k["amount_giu_nguyen"]' in than)
	dung("không đụng cột modified", "update_modified=False" in than)


@ca("hàm soi chỉ đọc, không ghi một chữ nào")
def _():
	than = MA_D.split("def soi_ghi_nham(")[1].split("\n@")[0]
	for cam in ("set_value", "db.commit", ".save(", ".insert(", "delete_doc"):
		dung("không có %s" % cam, cam not in than)


# ------------------------------------------------ huong dan che bien

@ca("tổng thời gian cộng cả chặng nghỉ, không chỉ chặng làm")
def _():
	la("cộng đủ ba chặng", H["tong_thoi_gian"](20, 45, 120), 185)
	la("ô trống tính là 0", H["tong_thoi_gian"](None, 45, ""), 45)
	la("gõ chữ thì bỏ qua chứ không nổ", H["tong_thoi_gian"]("hai mươi", 10, 5), 15)


@ca("nhắc đủ bốn thứ còn thiếu của một hướng dẫn trống")
def _():
	nhac = H["thieu_gi"]({})
	la("nhắc bốn chỗ", len(nhac), 4)
	txt = " ".join(nhac)
	for can in ("bước làm", "định lượng", "ảnh món đạt", "dị ứng"):
		dung("nhắc %s" % can, can in txt)


@ca("hướng dẫn đã đủ thì không nhắc gì")
def _():
	la("không nhắc gì", H["thieu_gi"]({
		"buoc": [{"cong_doan": "Đánh trứng"}],
		"dinh_luong": [{"ten": "Lòng trắng", "so_luong": 300, "dvt": "Gram"}],
		"anh_dat_chinh": "/files/ws.jpg",
		"di_ung": "Trứng, gluten",
		"trang_thai": "Nháp",
	}), [])


@ca("đang dùng mà chưa có người duyệt thì bị nhắc")
def _():
	nhac = H["thieu_gi"]({
		"buoc": [{"cong_doan": "x"}], "dinh_luong": [{"ten": "y"}],
		"anh_dat_chinh": "/files/a.jpg", "di_ung": "Trứng",
		"trang_thai": "Đang dùng",
	})
	la("nhắc đúng một chỗ", len(nhac), 1)
	dung("nhắc người duyệt", "người duyệt" in nhac[0])


@ca("nhặt đúng các bước có điểm tới hạn, giữ số thứ tự thật")
def _():
	ra = H["buoc_toi_han"]([
		{"cong_doan": "Nguyên liệu đầu vào", "diem_toi_han": "OPRP", "bieu_mau": "BM - NVL"},
		{"cong_doan": "Đánh trứng"},
		{"cong_doan": "Rây", "diem_toi_han": ""},
		{"cong_doan": "Cân nguyên liệu", "diem_toi_han": "OPRP"},
	])
	la("nhặt được hai bước", len(ra), 2)
	la("số thứ tự đúng của bước cân", ra[1]["stt"], 4)
	la("giữ tên biểu mẫu", ra[0]["bieu_mau"], "BM - NVL")


@ca("bảng định lượng có ô nói rõ tách từ đâu ra")
def _():
	# Day chinh la cho tra loi cau hoi cua anh Viet: cong thuc ghi Qua thi
	# lam sao biet so gram cua long trang.
	d = _json("vagabond", "doctype", "vagabond_hdcb_dinh_luong",
			  "vagabond_hdcb_dinh_luong.json")
	o = {f["fieldname"]: f for f in d["fields"]}
	for can in ("ten", "so_luong", "dvt", "tach_tu", "ghi_chu"):
		dung("có ô %s" % can, can in o)
	# Ma hang KHONG duoc bat buoc: long trang va long do khong co ma rieng.
	dung("mã hàng không bắt buộc", not o["ma_hang"].get("reqd"))


@ca("hướng dẫn gắn vào MÓN, không gắn vào công thức")
def _():
	d = _json("vagabond", "doctype", "vagabond_huong_dan_che_bien",
			  "vagabond_huong_dan_che_bien.json")
	o = {f["fieldname"]: f for f in d["fields"]}
	la("khoá chính là món", o["ma_mon"]["options"], "Item")
	dung("món là bắt buộc", o["ma_mon"].get("reqd"))
	dung("có ô ghi soạn theo bản nào", "bom_soan_theo" in o)
	dung("cờ báo công thức đã đổi do máy đặt", o["cong_thuc_da_doi"].get("read_only"))
	dung("đặt tên theo mã món", d.get("autoname") == "format:HDCB-{ma_mon}")


@ca("hướng dẫn không phải chứng từ: không ghi sổ, không duyệt nhiều cấp")
def _():
	d = _json("vagabond", "doctype", "vagabond_huong_dan_che_bien",
			  "vagabond_huong_dan_che_bien.json")
	dung("không ghi sổ", not d.get("is_submittable"))
	dung("có ghi lịch sử sửa", d.get("track_changes"))
	tt = [f for f in d["fields"] if f["fieldname"] == "trang_thai"][0]
	la("đúng ba trạng thái", tt["options"].split("\n"),
	   ["Nháp", "Đang dùng", "Ngừng dùng"])


@ca("chỉ chặn khi chuyển sang Đang dùng, không chặn lúc lưu nháp")
def _():
	# Bep truong go dan tren dien thoai. Chan luu la ho bo cuoc.
	than = MA_H.split("def luu(")[1]
	dung("chỉ soi khi Đang dùng", 'if str(doc.trang_thai or "") == TT_DUNG:' in than)


@ca("BẾP PHÓ tạo và sửa được hướng dẫn")
def _():
	"""Anh Viet chot 25/08/2026: dong y mo quyen cho Bep pho.

	Bep pho la nguoi dung bep hang ngay, chinh ho moi biet buoc nao thuc te
	lam khac voi ban soan. Bat ho phai nho bep truong sua tung chu la huong
	dan se khong bao gio duoc cap nhat.
	"""
	dung("có trong bộ vai được sửa", '"Bếp phó"' in MA_H.split("VAI_SUA = {")[1][:200])
	# Va phai co ca trong quyen cua doctype, khong chi trong ham kiem.
	d = _json("vagabond", "doctype", "vagabond_huong_dan_che_bien",
			  "vagabond_huong_dan_che_bien.json")
	bp = [p for p in d["permissions"] if p["role"] == "Bếp phó"]
	la("có đúng một dòng quyền cho bếp phó", len(bp), 1)
	dung("bếp phó tạo được", bp[0].get("create"))
	dung("bếp phó sửa được", bp[0].get("write"))
	# Nhung KHONG duoc xoa: xoa mot huong dan la mat ca lich su sua doi.
	dung("bếp phó KHÔNG xoá được", not bp[0].get("delete"))


# --------------------------------------------------------- mau in A4

@ca("mẫu in A4 có đủ định lượng và các bước")
def _():
	dung("có tệp mẫu", bool(MAU))
	dung("in khổ A4 dọc", "size: A4 portrait" in MAU)
	dung("lề 15mm dùng chung", "margin: 15mm" in MAU)
	for can in ("dinh_luong", "buoc", "tieu_chi", "di_ung"):
		dung("có phần %s" % can, "doc." + can in MAU)


@ca("mẫu in dán tường: chữ đủ to và không cắt bước làm giữa hai trang")
def _():
	# To nay DAN TUONG, nguoi dung cach mot met van phai doc duoc.
	dung("cỡ chữ nền từ 13pt", "font-size: 13pt" in MAU)
	dung("số lượng để 17pt", "font-size: 17pt" in MAU)
	# Tay bep dinh bot, khong lat trang. Dung cat mot buoc ra lam doi.
	dung("không cắt bước làm giữa hai trang", "page-break-inside: avoid" in MAU)


@ca("mẫu in đọc đúng cả khi in đen trắng")
def _():
	# Bep in may laser van phong, khong in mau. Diem toi han danh dau bang
	# khung dam va CHU, khong dua vao mau do.
	dung("điểm tới hạn có chữ chứ không chỉ màu", "ĐIỂM TỚI HẠN" in MAU)
	dung("đánh dấu bằng viền đậm", "border-left-width: 9pt" in MAU)


@ca("mẫu in cảnh báo khi công thức đã đổi")
def _():
	dung("có khối cảnh báo", "cong_thuc_da_doi" in MAU)
	dung("nói rõ tờ này có thể đã cũ", "CÓ THỂ ĐÃ CŨ" in MAU)


@ca("mẫu in được khai trong repo, không trôi nổi trong cơ sở dữ liệu")
def _():
	# Print Format sua thang tren Desk nam trong co so du lieu, git khong
	# quan, lo tay xoa la khong khoi phuc duoc.
	mi = _doc(os.path.join("mau_in", "__init__.py"))
	dung("có khai trong MAU_IN", '"huong_dan_che_bien.html"' in mi)
	dung("gắn đúng doctype", '"Vagabond Huong Dan Che Bien"' in mi)
	# Ban ghi tao lan dau o ham co ten ro rang, khong nup trong nhip dong bo.
	dung("có hàm dựng mẫu in", "def dung_mau_in(" in MA_H)
	dung("được gọi từ after_migrate", "dung_mau_in()" in _doc("truong_tu_them.py"))
	dung("không tự tạo nếu đã có", 'exists("Print Format", MAU_IN)' in MA_H)


# ------------------------------------------------------------ cua ngo

@ca("mọi cửa mở ra ngoài của hai mô đun đều đã chốt trong thu_cua_ngo")
def _():
	import re

	chot = _doc(os.path.join("khung", "kiem_thu", "thu_cua_ngo.py"))
	thieu = []
	for ma in (MA_D, MA_H):
		for c in sorted(set(re.findall(
				r"@frappe\.whitelist\([^)]*\)\s*\ndef\s+([A-Za-z_0-9]+)", ma))):
			if '"%s"' % c not in chot:
				thieu.append(c)
	la("không cửa nào chưa chốt", thieu, [])


@ca("vai quản lý công thức khai một chỗ và mở đúng màn công thức")
def _():
	vai = _doc("vai_cua_hang.py")
	ct = _doc("cong_thuc.py")
	dung("có khai vai", 'VAI_QLCT = "VGB - Quản lý công thức"' in vai)
	dung("có trong bảng vai", '"vai": VAI_QLCT' in vai)
	dung("gắn vào hồ sơ kế toán giá thành", '"VGB - Kế toán giá thành"' in vai)
	dung("màn công thức nhận vai mới", "VAI_QLCT" in ct)
	dung("import chứ không chép chuỗi", "from vagabond.vai_cua_hang import VAI_QLCT" in ct)
	dung("không chép chuỗi tên vai", '"VGB - Quản lý công thức"' not in ct)
