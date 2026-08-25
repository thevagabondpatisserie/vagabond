"""Kiem thu v299: giam gia Pancake, chiem dung sao ke, may in va diem ban.

Bon khoi anh Viet chot ngay 24/08/2026, ghi lai o day de doi sau con doi
chieu duoc voi ly do.

1. GIAM GIA PHAI HIEN RA LA GIAM GIA
   *"dong bo nhu vay ve phan gia cua pancake thi no thieu ban chat, tuc la
   minh khong thay duoc don nay la don giam gia cho khach"*.

2. MOT DONG SAO KE CHI DUOC GACH CHO MOT CHUNG TU
   Bill quay va phieu cong no deu chua co cho chiem dung nao, nen mot lan
   khach chuyen tien co the duoc tinh cho hai chung tu khac nhau.

3. MAY IN THEO DIEM BAN
   *"click vao diem ban nao thi se do QZ Tray cua may diem ban do va co danh
   sach may in rieng cua tung diem ban, chu khong he dung chung"*.

4. NGHIEP VU DAY DU O MOI DIEM BAN
   *"co ban chi la khac diem ban thoi chu con cac nghiep vu ben trong deu
   phai day du het"*. Diem Sales Online truoc day khong co man tinh tien.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

from vagabond import chiem_sao_ke, gia_pancake

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")


def _doc(ten, thu_muc=GOI):
	p = os.path.join(thu_muc, ten)
	if not os.path.exists(p):
		return ""
	return io.open(p, encoding="utf-8").read()


# ---------------------------------------------- 1. giam gia hien ra la giam gia

@ca("đơn 91853 thật: ba số của một dòng hàng, không nuốt giảm vào giá bán")
def _():
	lapis = gia_pancake.dong_gia(2200000, {"discount_each_product": 5, "is_discount_percent": True})
	la("giá gốc giữ nguyên", lapis["gia_goc"], 2200000.0)
	la("phần trăm giảm đọc ra được", lapis["giam_pt"], 5.0)
	la("số tiền giảm mỗi hộp", lapis["giam_tien"], 110000.0)
	la("giá bán", lapis["gia_ban"], 2090000.0)
	dung("có cờ đây là dòng giảm giá", lapis["co_giam"])


@ca("giảm theo SỐ TIỀN thì không được ghi thành phần trăm")
def _():
	# Giam 110.000 tren 2.200.000 dung bang 5 phan tram. Nhung "giam 5%" va
	# "giam 110.000 dong" la hai cach ghi khac nhau tren to hoa don VAT, va
	# suy nguoc tu so tien ra phan tram la bia.
	d = gia_pancake.dong_gia(2200000, {"discount_each_product": 110000})
	la("giá bán vẫn đúng", d["gia_ban"], 2090000.0)
	la("KHÔNG bịa ra phần trăm", d["giam_pt"], 0.0)
	la("số tiền giảm giữ nguyên", d["giam_tien"], 110000.0)


@ca("dòng không giảm gì thì không khai giá gốc, để ERPNext lấy bảng giá")
def _():
	d = gia_pancake.dong_gia(30000, {})
	la("không có giảm", d["co_giam"], 0)
	la("giá bán bằng giá gốc", d["gia_ban"], 30000.0)


# ------------------------------------------ 2. mot dong sao ke, mot chung tu

@ca("cùng một mã nằm hai chỗ trong một dòng chỉ tính là một lần")
def _():
	# Ngan hang doi khi vua de ma trong noi dung vua de trong o tham chieu.
	# `findall` khong gop trung nen truoc day so tien bi cong hai lan.
	ds = chiem_sao_ke.ma_trong_dong("CK VGBK7M2P noi dung VGBK7M2P", ["VGBK7M2P"], r"VGB[A-Z0-9]{5}")
	la("chỉ ra một mã", ds, ["VGBK7M2P"])
	dong = [{"ten": "BT-1", "mo_ta": "CK VGBK7M2P VGBK7M2P", "tien": 200000}]
	theo, bo = chiem_sao_ke.cong_tien(dong, ["VGBK7M2P"], r"VGB[A-Z0-9]{5}")
	la("tiền chỉ cộng một lần", theo["VGBK7M2P"]["nhan"], 200000.0)
	la("và chỉ tính một dòng sao kê", theo["VGBK7M2P"]["so_gd"], 1)


@ca("một dòng mang HAI mã bill thì không gạch cho ai cả")
def _():
	# Khach tra hai bill trong mot lan chuyen. Cong du cho ca hai la nhan doi
	# tien; chia doi la doan bua. Duong dung la de nguoi khop tay.
	dong = [{"ten": "BT-9", "mo_ta": "CK VGBAAAAA VGBBBBBB", "tien": 400000}]
	theo, bo = chiem_sao_ke.cong_tien(dong, ["VGBAAAAA", "VGBBBBBB"], r"VGB[A-Z0-9]{5}")
	la("không bill nào được cộng tiền", theo, {})
	la("dòng đó được nêu ra cho người xử lý", len(bo), 1)
	la("và nêu đủ cả hai mã", bo[0]["ma"], ["VGBAAAAA", "VGBBBBBB"])


@ca("giữ lại mã dòng sao kê thì mới chặn được gạch hai lần")
def _():
	dong = [
		{"ten": "BT-1", "mo_ta": "CK VGBAAAAA", "tien": 100000},
		{"ten": "BT-2", "mo_ta": "CK VGBAAAAA", "tien": 50000},
	]
	theo, _bo = chiem_sao_ke.cong_tien(dong, ["VGBAAAAA"], r"VGB[A-Z0-9]{5}")
	la("cộng đủ hai lần chuyển", theo["VGBAAAAA"]["nhan"], 150000.0)
	la("và nhớ CẢ HAI dòng sao kê", theo["VGBAAAAA"]["gd"], ["BT-1", "BT-2"])


@ca("dòng đã có chủ thì chỉ ra đúng ai đang giữ")
def _():
	chu = {"BT-1": "phiếu công nợ CN-26-08-00007"}
	la("bắt được", chiem_sao_ke.gd_dung_hai_lan(["BT-1", "BT-2"], chu),
		[("BT-1", "phiếu công nợ CN-26-08-00007")])
	la("không ai giữ thì im", chiem_sao_ke.gd_dung_hai_lan(["BT-2"], chu), [])


@ca("ô văn bản nhiều dòng đọc và ghi lại được nguyên vẹn")
def _():
	la("tách", chiem_sao_ke.tach_gd("BT-1\nBT-2\nBT-1"), ["BT-1", "BT-2"])
	la("ghép", chiem_sao_ke.gom_gd(["BT-2", "BT-2", "BT-1"]), "BT-2\nBT-1")
	la("rỗng", chiem_sao_ke.tach_gd(""), [])


@ca("bốn cửa tiền vào đều đi qua phép chiếm dụng")
def _():
	bh = _doc("ban_hang.py")
	cn = _doc("cong_no.py")
	dss = _doc("doi_soat_sepay.py")
	# Bill quay: phai giu lai ma dong sao ke va hoi truoc khi ghi so.
	dung("bill quầy có cửa chiếm dụng", "def _chiem_gd_bill(" in bh)
	khuc = bh.split("def pos_ghi_so(")[1].split("\n@frappe.whitelist()")[0]
	dung("ghi sổ có gọi cửa đó", "_chiem_gd_bill(si, g.get(\"gd\") or [])" in khuc)
	dung("bill quầy có ô ghi dòng sao kê", '"fieldname": "vgb_gd_sepay"' in bh)
	# Cong no: phai co truong ma_gd va cua chiem dung.
	dung("công nợ có cửa chiếm dụng", "def _giu_gd(" in cn)
	dung("công nợ có ô ghi dòng sao kê", '"fieldname": "ma_gd"' in cn)
	dung("công nợ vào sổ đối soát chung", "dss.khai(" in cn)
	khai = cn.split("dss.khai(")[1].split("\t)")[0]
	dung("khai đúng tên luồng", '\tloai="cong_no",' in khai)
	dung("khai là luồng tiền VÀO", "chieu=dss.VAO," in khai)
	dung("khai ô giữ dòng sao kê", 'truong_gd="ma_gd",' in khai)
	dung("phiếu đã huỷ thì nhả dòng sao kê ra", 'loc_chiem={"trang_thai": ["!=", "Huy"]},' in khai)
	dung("sổ chung có gọi khai lúc nạp mô đun", "\n_khai_doi_soat()" in cn)
	# Phep hoi phai la phep hoi TOAN HE, khong chi trong luong cua minh.
	dung("có phép hỏi toàn hệ", "def chu_cua_giao_dich(" in dss)
	dung("phép hỏi có soi cả hoá đơn bán", 'HD_BAN = {"doctype": "Sales Invoice"' in dss)
	dung("sổ chung có kê tên luồng công nợ", '"cong_no", "de_nghi_chi", "hoan_tien"' in dss)


@ca("phép cộng tiền theo mã bill không còn tự cộng tay nữa")
def _():
	# Cho de tuot: mot phien sau thay vong lap goi ham la, sua ve `findall`
	# cho gon, va ca ba lo hong quay lai nguyen ven.
	bh = _doc("ban_hang.py")
	khuc = bh.split("def _sepay_theo_ma_bill(")[1].split("\n\n\ndef ")[0]
	dung("đi qua phép thuần", "chiem_sao_ke.cong_tien(" in khuc)
	dung("có lấy mã dòng sao kê", "select name, description" in khuc)
	dung("có cửa sổ ngày", "date >= %s" in khuc)
	dung("không còn vòng lặp findall cũ", "RE_MA_BILL.findall(" not in khuc)


@ca("phép cộng tiền theo mã công nợ bỏ qua dòng nhập nhằng")
def _():
	cn = _doc("cong_no.py")
	khuc = cn.split("def _sepay_theo_ma_cn(")[1].split("\n\n\ndef ")[0]
	dung("có lấy mã dòng sao kê", "select name, description" in khuc)
	dung("có bỏ qua dòng nhiều mã", "chiem_sao_ke.dong_nhap_nhang(" in khuc)


# ------------------------------------------------------- 3. may in theo diem

@ca("màn tính tiền dò máy in SAU khi biết đứng ở điểm nào")
def _():
	js = _doc("09-tinh-tien-quay.js", BEP)
	dung("có truyền điểm bán vào phép dò", "inNgamDo(0, posQuay.ma)" in js)
	# Do TRUOC buoc chon quay la moi may deu nhan ve hop chung manh ten may
	# in cua ca ba diem, va quay nay in nham sang may quay kia.
	vt_do = js.find("inNgamDo(0, posQuay.ma)")
	vt_chon = js.find("if (!posQuay) return go(scrPosChonQuay, true);")
	dung("phép dò nằm SAU cửa chọn điểm", 0 <= vt_chon < vt_do)


@ca("đổi điểm bán là dò lại danh sách máy in")
def _():
	js = _doc("27-in-ngam.js", BEP)
	dung("phép dò nhận điểm bán", "function inNgamDo(ep, diem)" in js)
	dung("có nhớ điểm đã dò", "IN_QZ.diem" in js)
	dung("đổi điểm thì ép dò lại", "if (IN_QZ.do_roi && diem !== String(IN_QZ.diem || '')) ep = 1;" in js)
	dung("gửi điểm sang máy chủ", "dinh_tuyen', { diem: diem }" in js)


@ca("khổ giấy đọc theo đúng điểm bán")
def _():
	mi = _doc("may_in.py")
	bh = _doc("ban_hang.py")
	js = _doc("10-bill-quay.js", BEP)
	dung("bảng khổ giấy lọc theo điểm", "def kho_theo_vai_tro(diem=\"\"):" in mi)
	khuc = mi.split("def kho_theo_vai_tro(")[1].split("\n\n\ndef ")[0]
	dung("có bỏ qua máy của điểm khác", 'if diem and m.get("diem") and m["diem"] != diem:' in khuc)
	dung("cấu hình bán hàng gửi bảng theo điểm", '"kho_in_diem"' in bh)
	dung("màn bill đọc bảng theo điểm", "kho_in_diem" in js)


@ca("lưu danh sách máy in là TRỘN theo từng máy, không đè cả mảng")
def _():
	# Hai nguoi cung mo man Cai dat, moi nguoi sua mot may khac nhau roi bam
	# Luu: truoc day nguoi bam sau xoa sach viec cua nguoi bam truoc.
	mi = _doc("may_in.py")
	dung("có phép trộn", "def _tron(may):" in mi)
	khuc = mi.split("def luu(may=None):")[1].split("\n\n\n")[0]
	dung("cửa lưu gọi phép trộn", "ra = _tron(may)" in khuc)
	dung("không còn dựng lại cả mảng", "[_chuan(d, i) for i, d in enumerate(may or [])]" not in khuc)
	js = _doc("18-doi-chieu-may-in.js", BEP)
	dung("nút Bỏ đánh dấu xoá thay vì cắt mảng", "miDs[miMo].xoa = 1;" in js)
	dung("máy chủ đọc cờ xoá", 'cint((d or {}).get("xoa"))' in mi)


@ca("danh sách máy in nhóm theo điểm bán")
def _():
	js = _doc("18-doi-chieu-may-in.js", BEP)
	dung("có tiêu đề nhóm", "Máy in theo điểm bán" in js)
	dung("có nhóm chưa gán điểm", "Chưa gán điểm bán" in js)
	dung("có chỉ ra loại phiếu còn thiếu", "chưa có máy cho: " in js)


# --------------------------------------------- 4. nghiep vu day du moi diem

@ca("màn chọn điểm bán đọc từ danh sách điểm bán, hết thẻ gõ cứng")
def _():
	js = _doc("09-tinh-tien-quay.js", BEP)
	dung("không còn thẻ Sales gõ cứng", "CARD_SALES" not in js)
	dung("không còn đường rẽ sang màn Doanh số", "if (q && q.sales)" not in js)
	dung("đọc từ danh sách điểm bán", "((CFGBH || {}).diem)" in js)


@ca("điểm không có quầy vẫn bán được: chế độ là nguồn đơn của chính nó")
def _():
	js = _doc("09-tinh-tien-quay.js", BEP)
	dung("có phép hỏi điểm có quầy không", "function posCoQuay()" in js)
	dung("chế độ lấy từ nguồn của điểm", "return nguon.map(bay);" in js)
	# Truoc day che_do mac dinh luon la 'Tai cho', ma diem Sales khong ban
	# tai cho: may chu tu choi don voi cau "Nguon don (trong) khong co trong
	# danh muc", tuc diem do khong ban duoc gi ca.
	dung("chế độ mặc định lấy từ điểm", "var mac = (ds0[0] && ds0[0].v) || 'Tại chỗ';" in js)
	dung("nguồn thực trả thẳng chế độ khi không có quầy", "if (!posCoQuay()) return posDon.che_do;" in js)


@ca("điểm không có quầy thì không có ca làm việc")
def _():
	# Diem Sales khong giu ket. Ve khoi ca ra la bat nguoi ban chot mot cai
	# ca khong ton tai, va ban doi soat se bao TOAN BO doanh thu la tien thua
	# khong giai trinh duoc.
	js = _doc("09-tinh-tien-quay.js", BEP)
	neo = "if (posCoQuay()) html += "
	dung("khối ca chỉ vẽ khi có quầy", neo in js)
	dung("đúng khối thẻ ca", "posCaKhoi" in js.split(neo)[1][:200])
	dung("phép đọc ca thoát sớm khi không có quầy",
		"async function posCaVe() {\n  if (!posCoQuay()) return;" in js)


@ca("máy chủ nhận bill của điểm không có quầy")
def _():
	bh = _doc("ban_hang.py")
	dung("có phép lọc theo điểm bán", "def _loc_diem_ban(" in bh)
	dung("có phép đọc điểm của một bill", "def _diem_cua_bill(" in bh)
	khuc = bh.split("def _pos_lay(name):")[1].split("\n\n\n")[0]
	dung("cửa lấy bill nhận cả bill không mang mã quầy", "if _diem_cua_bill(si):" in khuc)
	dung("không còn từ chối thẳng", 'frappe.throw("Phiếu này không phải bill quầy.")' not in bh)
	# Hai man danh sach phai loc theo diem chu khong theo ma quay, khong thi
	# diem Sales mo ra thay rong va cai chan trung bill khong bao gio no.
	la("hai màn danh sách đều lọc theo điểm", bh.count("loc = _loc_diem_ban(quay)"), 2)


# ------------------------------------------- 5. so doi soat phai nap DU luong

@ca("sổ đối soát KHÔNG bỏ sót luồng khi sổ đã có sẵn một luồng")
def _():
	# Ca nay CHAY THAT chu khong soi ma nguon, vi day dung la cho bo kiem cu
	# lot luoi: ma nguon co du ba dong nhap, chay len thi thieu.
	#
	# Ban v295 thoat som khi so da co phan tu. Frappe nap mo dun theo hooks,
	# nen mo dun nao duoc nap truoc la tu khai luong cua no, so thanh khac
	# rong, roi moi lan goi sau do deu thoat ngay o dong dau va cac luong con
	# lai KHONG BAO GIO duoc nhap.
	#
	# Doc duoc tren site that ngay 25/08/2026 ngay sau khi deploy v299: so chi
	# co `hoan_tien`, thieu `cong_no`. Phep hoi mot dong sao ke da co chu vi
	# the mu mot phan, va mot lan khach chuyen tien co the duoc gach cho hai
	# chung tu o hai luong khac nhau ma khong ai chan.
	#
	# Ca nay chi dung `de_nghi_chi` va `hoan_tien` de dung lai canh do. KHONG
	# dung `cong_no`: mo dun do keo theo thu vien mang, ma may chay CI thi tay
	# khong. Ca kiem nao keo theo thu vien mang la ca kiem dat sai cho.
	import sys

	import vagabond as goi
	from vagabond import doi_soat_sepay as dss

	dss.nap_so()
	giu_so = dict(dss._SO)
	ten_mo = ("de_nghi_chi", "hoan_tien")
	giu_mo = {t: sys.modules["vagabond." + t] for t in ten_mo
		if "vagabond." + t in sys.modules}
	dung("dựng lại được cảnh thật", len(giu_mo) == 2)
	try:
		# So KHAC RONG san, dung canh tren site that.
		dss._SO.clear()
		dss._SO["mot_luong_da_khai"] = {"chieu": dss.RA, "truong_gd": "ma_gd"}
		# Phai go CA hai cho: `sys.modules` VA thuoc tinh tren goi. Chi go
		# `sys.modules` thi phep nhap van doc duoc thuoc tinh cu, khong nhap
		# lai, va phep dung lai sai canh.
		for t in ten_mo:
			sys.modules.pop("vagabond." + t, None)
			if hasattr(goi, t):
				delattr(goi, t)
		dss.nap_so()
		dung("sổ đã có luồng vẫn nạp tiếp luồng thanh toán nội bộ", "ttnb" in dss._SO)
		dung("sổ đã có luồng vẫn nạp tiếp luồng hoàn tiền", "hoan_tien" in dss._SO)
	finally:
		for t, m in giu_mo.items():
			sys.modules["vagabond." + t] = m
			setattr(goi, t, m)
		dss._SO.clear()
		dss._SO.update(giu_so)


@ca("một luồng hỏng không được kéo sập cả sổ đối soát")
def _():
	# Ngay 25/08/2026 may CI tay khong khong nhap noi `cong_no` vi mo dun do
	# keo theo thu vien mang. Neu gom ca ba phep nhap vao MOT khoi thi mot mo
	# dun hong la hai luong con lai bien mat lang le.
	import sys

	import vagabond as goi
	from vagabond import doi_soat_sepay as dss

	la("sổ khai đủ ba mô đun", sorted(dss.MO_DUN_KHAI),
		["cong_no", "de_nghi_chi", "hoan_tien"])

	dss.nap_so()
	giu_so = dict(dss._SO)
	giu_mo = {t: sys.modules["vagabond." + t] for t in dss.MO_DUN_KHAI
		if "vagabond." + t in sys.modules}
	hong = "vagabond.de_nghi_chi"
	try:
		dss._SO.clear()
		for t in dss.MO_DUN_KHAI:
			sys.modules.pop("vagabond." + t, None)
			if hasattr(goi, t):
				delattr(goi, t)
		# Dung mot mo dun HONG: nhap la no no.
		class _No(object):
			def __getattr__(self, _):
				raise ImportError("dựng lại mô đun hỏng")
		sys.modules[hong] = _No()
		dss.nap_so()
		dung("luồng hoàn tiền vẫn vào sổ dù một mô đun hỏng", "hoan_tien" in dss._SO)
	finally:
		sys.modules.pop(hong, None)
		for t, m in giu_mo.items():
			sys.modules["vagabond." + t] = m
			setattr(goi, t, m)
		dss._SO.clear()
		dss._SO.update(giu_so)


@ca("cửa hỏi chủ của một dòng sao kê soi ĐỦ mọi luồng đang có")
def _():
	from vagabond import doi_soat_sepay as dss

	dss.nap_so()
	dung("sổ có luồng hoàn tiền", "hoan_tien" in dss._SO)
	dung("sổ có luồng thanh toán nội bộ", "ttnb" in dss._SO)
	dung("cửa hỏi có soi riêng hoá đơn bán", dss.HD_BAN["doctype"] == "Sales Invoice")
