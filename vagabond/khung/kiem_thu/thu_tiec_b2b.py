"""Kiem thu: mang B2B va Tiec, lam theo don khong dinh muc.

Anh Viet duyet ban thiet ke 25/08/2026. Ban day du o project doc
`claude/thiet-ke-b2b-tiec-lam-theo-don.md`.

Bo ca kiem nay chot BON quyet dinh kien truc, vi ca bon deu la loai sau
nay doc lai code se thay "ky ky" va co nguoi sua nguoc lai:

  1. Neo bang Project chu khong phai Sales Order.
  2. `project` dat o DAU PHIEU, khong dat vao tung dong.
  3. `expense_account` ghi THANG tren dong, khong dua vao cai dat chung.
  4. Ty le lai tra None khi chua co doanh thu, khong tra 0.

Ca ba phep ghi so o day deu cham GL Entry va Stock Ledger Entry, nen bo
kiem tang khung nay KHONG DU. Doc muc 8 cua ban thiet ke.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def chi_phan_ma(nguon):
	"""Bo chu thich va docstring khoi mot tep Python. THUAN.

	Vi sao can ham nay
	------------------
	Cac ca kiem duoi day soi xem ma nguon co dung mot thu bi cam khong,
	vi du `sales_order` hay `stock_adjustment_account`. Neu soi ca chu
	thich thi chinh doan GIAI THICH VI SAO khong dung thu do lai bi cham
	la vi pham, va nguoi viet se bi ep phai xoa loi giai thich di.

	Da vap dung loi nay hai lan trong ngay 25/08/2026. Nen lam han mot
	ham, dung `tokenize` chu khong dung phep thay chuoi: chuoi co dau
	thang trong long no la chuyen thuong.
	"""
	import tokenize

	ra = []
	# Docstring la mot chuoi dung MOT MINH lam cau lenh, tuc token truoc
	# no la dau dong hoac dau khoi. Bam vao dau hieu do de tach docstring
	# ra khoi cac chuoi that su la du lieu.
	dau_khoi = {tokenize.NEWLINE, tokenize.NL, tokenize.INDENT,
		tokenize.DEDENT, tokenize.ENCODING}
	truoc = tokenize.NEWLINE
	for tk in tokenize.generate_tokens(io.StringIO(nguon).readline):
		if tk.type == tokenize.COMMENT:
			continue
		if tk.type == tokenize.STRING and truoc in dau_khoi:
			truoc = tokenize.STRING
			continue
		if tk.type not in (tokenize.NL, tokenize.INDENT, tokenize.DEDENT):
			truoc = tk.type
		ra.append(tk.string)
	return "\n".join(ra)


def _thuan(tep, ten_hien):
	ma = _doc(tep)
	moc = "# ------------------------------------------------------- phan can Frappe"
	assert moc in ma, "%s doi cau truc, khong tim thay moc phan thuan" % ten_hien
	ns = {}
	exec(compile(ma.split(moc)[0], ten_hien, "exec"), ns)
	return ns


T = _thuan("tiec.py", "tiec_thuan")
MA = _doc("tiec.py")
MA_CODE = chi_phan_ma(MA)   # chi phan MA, da bo chu thich va docstring
MA_CUA = _doc("khung", "kiem_thu", "thu_cua_ngo.py")
MA_TRUONG = _doc("truong_tu_them.py")


# ------------------------------------------------------ mã dự án


@ca("mã dự án dựng từ một chỗ duy nhất")
def _():
	# Neu hai noi tu ghep chuoi thi som muon co mot noi ghep khac, va luc
	# do but toan doanh thu voi but toan gia von roi vao hai du an khac
	# nhau. Boc gia von ra se thieu mot ve ma khong ai biet.
	la("hợp đồng thường", T["ma_du_an"]("HD-2026-00042"), "TIEC-HD-2026-00042")
	la("có khoảng trắng thừa", T["ma_du_an"]("  HD-2026-00042  "), "TIEC-HD-2026-00042")


@ca("mã dự án trả rỗng khi chưa có hợp đồng, không trả tiền tố trơ trọi")
def _():
	# Tra "TIEC-" thi tat ca hop dong rong se dung chung MOT du an, va gia
	# von cua chung tron vao nhau.
	for xau in ("", None, "   "):
		la("hợp đồng %r" % (xau,), T["ma_du_an"](xau), "")


# ------------------------------------------------------ gộp dòng xuất


@ca("gõ cùng một mặt hàng nhiều lần thì cộng dồn lại")
def _():
	# Bo dot 1, bo dot 2 la chuyen thuong ngay o bep.
	ra = T["gom_dong_xuat"]([
		{"ma": "NVLT00001", "sl": 4500, "ghi_chu": "đợt 1"},
		{"ma": "NVLT00002", "sl": 12000},
		{"ma": "NVLT00001", "sl": 2000, "ghi_chu": "đợt 2"},
	])
	la("còn 2 dòng", len(ra), 2)
	la("bơ cộng dồn", ra[0]["sl"], 6500.0)
	la("giữ đúng thứ tự gõ", [x["ma"] for x in ra], ["NVLT00001", "NVLT00002"])


@ca("ghi chú các lần gõ được NỐI lại chứ không bỏ đi")
def _():
	# "dot 1" va "dot 2" la thong tin that cua bep, mat di thi khong lay
	# lai duoc tu dau ca.
	ra = T["gom_dong_xuat"]([
		{"ma": "NVLT00001", "sl": 4500, "ghi_chu": "đợt 1"},
		{"ma": "NVLT00001", "sl": 2000, "ghi_chu": "đợt 2"},
	])
	la("nối hai ghi chú", ra[0]["ghi_chu"], "đợt 1, đợt 2")


@ca("ghi chú trùng nhau không lặp lại hai lần")
def _():
	ra = T["gom_dong_xuat"]([
		{"ma": "NVLT00001", "sl": 1, "ghi_chu": "cân tay"},
		{"ma": "NVLT00001", "sl": 2, "ghi_chu": "cân tay"},
	])
	la("chỉ một lần", ra[0]["ghi_chu"], "cân tay")


@ca("dòng không có số lượng hoặc số âm bị loại trước khi dựng phiếu")
def _():
	# Dong so 0 lot vao phieu thi ERPNext bao loi luc ghi so, va bep khong
	# hieu vi sao. Loai tu day.
	ra = T["gom_dong_xuat"]([
		{"ma": "NVLT00001", "sl": 0},
		{"ma": "NVLT00002", "sl": -5},
		{"ma": "", "sl": 100},
		{"ma": "NVLT00003", "sl": 3},
	])
	la("chỉ còn dòng hợp lệ", [x["ma"] for x in ra], ["NVLT00003"])


@ca("số lượng gõ dạng chữ không làm đổ hàm")
def _():
	ra = T["gom_dong_xuat"]([{"ma": "NVLT00001", "sl": "abc"}])
	la("bỏ qua dòng hỏng", ra, [])


# ------------------------------------------------------ kiểm trước khi xuất


@ca("kiểm trước khi xuất bắt đủ ba thứ còn thiếu")
def _():
	# Kiem o tang thuan de man hinh bao loi NGAY, khong phai cho mot vong
	# xuong may chu roi moi biet minh quen chon kho.
	loi = T["kiem_truoc_khi_xuat"]("", "", [])
	dung("bắt thiếu hợp đồng", any("hợp đồng" in x for x in loi))
	dung("bắt thiếu kho", any("kho" in x for x in loi))
	dung("bắt thiếu dòng", any("nguyên liệu" in x for x in loi))


@ca("đủ ba thứ thì kiểm trả rỗng")
def _():
	loi = T["kiem_truoc_khi_xuat"](
		"HD-2026-00042", "Kho tổng 307 - TV",
		[{"ma": "NVLT00001", "sl": 100}])
	la("không lỗi nào", loi, [])


@ca("có dòng nhưng số lượng đều bằng 0 vẫn bị chặn")
def _():
	# Day la cho de lot: man hinh co ba dong, nhin thi tuong day, ma
	# thuc ra khong dong nao co so.
	loi = T["kiem_truoc_khi_xuat"](
		"HD-2026-00042", "Kho tổng 307 - TV",
		[{"ma": "NVLT00001", "sl": 0}, {"ma": "NVLT00002", "sl": 0}])
	dung("vẫn bắt được", any("nguyên liệu" in x for x in loi))


# ------------------------------------------------------ mô tả gói tiệc


@ca("mô tả thực đơn dựng đúng một dòng một món")
def _():
	ra = T["mo_ta_goi_tiec"]([
		{"ten": "Bánh su kem", "sl": 50, "dvt": "cái"},
		{"ten": "Tart chanh", "sl": 30, "dvt": "cái", "ghi_chu": "ít ngọt"},
	])
	la("đúng nội dung", ra,
		"- Bánh su kem x 50 cái\n- Tart chanh x 30 cái (ít ngọt)")


@ca("số lượng tròn không kéo theo đuôi chấm không")
def _():
	# "x 50.0 cái" nhin la biet may viet, khong phai nguoi viet.
	ra = T["mo_ta_goi_tiec"]([{"ten": "Bánh su kem", "sl": 50.0, "dvt": "cái"}])
	la("không có đuôi .0", ra, "- Bánh su kem x 50 cái")


@ca("món không có tên bị bỏ qua chứ không in ra dòng trống")
def _():
	ra = T["mo_ta_goi_tiec"]([{"ten": "", "sl": 5}, {"ten": "Tart chanh", "sl": 3}])
	la("chỉ còn món có tên", ra, "- Tart chanh x 3")


# ------------------------------------------------------ lãi lỗ


@ca("tỷ lệ lãi trả None khi chưa có doanh thu, KHÔNG trả 0")
def _():
	# Bao "lai 0 phan tram" khi chua xuat hoa don la noi sai: chua biet
	# chu khong phai bang khong. Bep va ke toan doc con so do se tuong
	# hop dong nay hoa von.
	r = T["tinh_lai_lo"](0, 3_000_000)
	la("lỗ đúng bằng giá vốn", r["lai_gop"], -3_000_000.0)
	la("tỷ lệ là None", r["ty_le"], None)


@ca("lãi lỗ tính đúng trên số thật")
def _():
	r = T["tinh_lai_lo"](45_000_000, 6_240_000)
	la("lãi gộp", r["lai_gop"], 38_760_000.0)
	la("tỷ lệ", r["ty_le"], 86.13)


# ------------------------------------------------------ neo bằng Project


@ca("neo bằng Project chứ không phải Sales Order")
def _():
	# GL Entry KHONG co cot sales_order. Neo vao Sales Order thi o tang so
	# cai, but toan gia von khong mang mot dau vet nao cua hop dong.
	dung("có đặt project lên phiếu", "se.project = du_an" in MA)
	dung("không đặt sales_order", "sales_order" not in MA_CODE)


@ca("project đặt ở ĐẦU PHIẾU, không đặt vào từng dòng")
def _():
	# `Stock Entry Detail` khong co truong `project`. Dat vao tung dong
	# thi Frappe bo IM LANG, va minh tuong da neo trong khi chua neo gi.
	i = MA.find('se.append("items"')
	dung("tìm thấy chỗ dựng dòng", i > 0)
	j = MA.find("se.flags.ignore_permissions", i)
	dong = MA[i:j]
	dung("dòng KHÔNG mang project", '"project"' not in dong)
	dung("đầu phiếu có mang project", "se.project = du_an" in MA[:i])


@ca("phiếu vẫn giữ đường tắt về hợp đồng cho người đọc")
def _():
	# Neo that de boc gia von la Project. O nay chi de ai mo phieu ra la
	# biet no thuoc tiec nao, khong phai tra nguoc qua Project.
	dung("có đặt ô hợp đồng", "se.vgb_hop_dong = hd.name" in MA)
	dung("ô khai read_only", '"fieldname": "vgb_hop_dong"' in MA)


# ------------------------------------------------------ tài khoản giá vốn


@ca("tài khoản giá vốn ghi THẲNG trên dòng, không dựa cài đặt chung")
def _():
	# Tiem dang de `stock_adjustment_account` la 632, o luong tiec thi cai
	# mac dinh do TINH CO dung chieu. Nhung hom nao co nguoi doi cai dat
	# chung thi luong tiec se am tham doi theo ma khong ai hay.
	dung("có hằng số riêng", 'TK_GIA_VON = "632' in MA)
	dung("đặt thẳng trên dòng", '"expense_account": TK_GIA_VON' in MA)
	dung("không đọc cài đặt chung",
		"stock_adjustment_account" not in MA_CODE)


# ------------------------------------------------------ quyền và an toàn


@ca("dùng lại vai xuất kho sẵn có, không bịa vai mới")
def _():
	# Xuat NVL cho tiec VAN LA mot lan xuat kho. Cung mot hanh vi ma hai
	# cua doi hai quyen khac nhau la mot cho de tuot. Va ten vai tu bia ra
	# co the khong ton tai trong he, luc do phep kiem im lang cho khong ai
	# vao duoc.
	dung("import từ xuat_kho", "from vagabond.xuat_kho import VAI_XUAT" in MA)
	dung("không tự khai vai xuất", "VAI_XUAT = {" not in MA)


@ca("huỷ phiếu là HUỶ chứ không XOÁ, và bắt buộc ghi lý do")
def _():
	# QT-20: khong bao gio xoa han mot chung tu.
	i = MA.find("def huy_xuat_nvl(")
	doan = MA[i:i + 1400]
	dung("gọi cancel", "se.cancel()" in doan)
	dung("không gọi delete", "delete" not in doan)
	dung("bắt ghi lý do", "Phải ghi lý do huỷ" in doan)


@ca("huỷ chặn phiếu không phải của tiệc")
def _():
	# Huy nham mot phieu xuat kho thuong tu man tiec la sua mot chung tu
	# cua bo phan khac ma ho khong biet.
	i = MA.find("def huy_xuat_nvl(")
	doan = MA[i:i + 1400]
	dung("có kiểm ô hợp đồng", 'if not se.get("vgb_hop_dong")' in doan)
	dung("nói rõ phải huỷ ở đâu", "màn Xuất kho" in doan or "Xuất kho" in doan)


@ca("huỷ chặn phiếu chưa ghi sổ hoặc đã huỷ rồi")
def _():
	i = MA.find("def huy_xuat_nvl(")
	doan = MA[i:i + 1400]
	dung("có kiểm docstatus", "int(se.docstatus or 0) != 1" in doan)


@ca("dự án tạo MUỘN, tại lần xuất đầu tiên")
def _():
	# Phan lon hop dong khong bao gio phat sinh xuat kho rieng. Tao du an
	# cho tat ca chi lam ban danh muc Project.
	dung("hàm dựng dự án là nội bộ", "def _dung_du_an(hd):" in MA)
	dung("không whitelist hàm đó",
		"@frappe.whitelist()\ndef _dung_du_an" not in MA)
	i = MA.find("def xuat_nvl(")
	dung("gọi từ trong luồng xuất", "_dung_du_an(hd)" in MA[i:i + 2000])


@ca("lãi lỗ đọc THẲNG từ sổ cái chứ không cộng tay hai đầu")
def _():
	# So cai la noi ke toan nhin. Neu Sales Invoice va Stock Entry lech
	# nhau thi CAI LECH DO CHINH LA THU CAN BIET, cong tay se giau no di.
	i = MA.find("def lai_lo(")
	doan = MA[i:]
	dung("đọc GL Entry", "tabGL Entry" in doan)
	dung("lọc theo dự án", "g.project = %(da)s" in doan)
	dung("bỏ bút toán đã huỷ", "g.is_cancelled = 0" in doan)
	dung("tách hai vế bằng root_type", "a.root_type" in doan)


@ca("lãi lỗ nói rõ khi hợp đồng chưa có dự án")
def _():
	# Chua xuat NVL lan nao thi chua co du an. Tra ve so 0 tron tru se lam
	# nguoi doc tuong da tinh xong.
	dung("có cờ báo", '"chua_co_du_an": 1' in MA or "chua_co_du_an=1" in MA)


# ------------------------------------------------------ khai báo và cửa ngõ


@ca("năm cửa của tiệc đều đã chốt trong thu_cua_ngo")
def _():
	dung("có mục tiec.py", '"tiec.py": [' in MA_CUA)
	for cua in ("chi_tiet_tiec", "don_tiec", "huy_xuat_nvl", "lai_lo", "xuat_nvl"):
		dung("chốt %s" % cua, '"%s"' % cua in MA_CUA)


@ca("ba trường mới do mã nguồn khai, dựng lại sau mỗi lần deploy")
def _():
	for o in ("vgb_hop_dong", "vgb_ghi_chu", "vgb_du_an"):
		dung("có khai %s" % o, '"fieldname": "%s"' % o in MA)
	dung("gọi từ after_migrate", "_dung_nhom(tiec.TRUONG_MOI" in MA_TRUONG)


@ca("ô ghi chú của bếp KHÔNG chèn vào chỗ trường không tồn tại")
def _():
	# Ngay 25/08 da mot lan dat insert_after la "project" tren
	# `Stock Entry Detail`, ma bang do KHONG co truong project. Frappe
	# khong bao, o roi xuong cuoi bang.
	i = MA.find('"fieldname": "vgb_ghi_chu"')
	doan = MA[i:i + 300]
	dung("chèn sau expense_account", '"insert_after": "expense_account"' in doan)
	dung("không chèn sau project", '"insert_after": "project"' not in doan)


# ------------------------------------------------------ màn hình


@ca("màn tiệc KHÔNG chép lại danh sách vai của máy chủ")
def _():
	# Chep danh sach vai sang JavaScript la dung mot ban sao thu hai cua
	# `xuat_kho.VAI_XUAT`. Hom nao ben Python them hay bot mot vai thi ban
	# sao nay lech, va man hinh se hien nut cho nguoi khong bam duoc, hoac
	# giau nut khoi nguoi bam duoc.
	man = _doc("public", "js", "bep", "33-don-tiec.js")
	dung("có màn", len(man) > 500)
	dung("không có hàm kiểm vai riêng", "function tcXuatDuoc()" not in man)
	dung("nghe cờ của máy chủ", "d.duoc_xuat" in man)
	dung("máy chủ có trả cờ đó", '"duoc_xuat": bool(_co_vai_xuat())' in MA)


@ca("màn tiệc cảnh báo khi gõ nhiều hơn tồn, vì đó thường là lệch đơn vị")
def _():
	# Bep can bang gam. Mat hang nao khai don vi kho la Kg ma bep go 12000
	# thi thanh 12 tan, va phieu van ghi so binh thuong.
	man = _doc("public", "js", "bep", "33-don-tiec.js")
	dung("có so tồn", "m.sl > m.ton" in man)
	dung("nhắc kiểm đơn vị", "Kiểm lại đơn vị" in man)
	dung("hỏi lại trước khi ghi sổ", "Vẫn ghi sổ" in man)


@ca("màn tiệc hỏi lại trước khi ghi sổ và nói rõ hậu quả")
def _():
	man = _doc("public", "js", "bep", "33-don-tiec.js")
	dung("có hỏi lại", "Ghi sổ phiếu xuất?" in man)
	dung("nói rõ ghi vào sổ nào", "sổ kho và sổ cái" in man)
	dung("nói rõ không sửa được", "không sửa được" in man)


@ca("màn tiệc bắt gõ lý do khi huỷ phiếu")
def _():
	man = _doc("public", "js", "bep", "33-don-tiec.js")
	dung("dùng ô gõ chứ không chỉ hỏi có không", "promptSheet('Huỷ phiếu" in man)
	dung("chặn khi bỏ trống", "Phải ghi lý do huỷ." in man)


@ca("đổi kho thì bỏ hết dòng đã thêm")
def _():
	# Ton kho cua cac dong da them la ton cua kho CU. De lai con so do thi
	# bep tuong la ton that cua kho moi.
	man = _doc("public", "js", "bep", "33-don-tiec.js")
	i = man.find("kho.onchange = function ()")
	doan = man[i:i + 400]
	dung("có xoá dòng cũ", "d.dong = []" in doan)
	dung("có xoá kết quả tìm", "d.ket = []" in doan)


@ca("ô tìm nguyên liệu dùng lại cửa của xuất kho")
def _():
	# `xuat_kho.tim_hang` CHI liet ke ma con ton that trong kho do va tra
	# kem gia von. Viet cua tim thu hai chi de hai cho lech nhau.
	man = _doc("public", "js", "bep", "33-don-tiec.js")
	dung("gọi tim_hang", "vagabond.xuat_kho.tim_hang" in man)
	dung("không có cửa tìm riêng", "tim_nvl" not in MA)


@ca("mặt hàng TIEC-CUSTOM không bị mã nguồn tự tạo")
def _():
	# Ban thiet ke chot: tao MOT LAN tren Desk, co anh Viet nhin thay cac
	# o. Mot mat hang ban ra sinh ra lang le trong luc migrate thi khong
	# ai biet tai khoan doanh thu cua no dat dung chua.
	dung("không tự dựng Item", 'doctype": "Item"' not in MA)
