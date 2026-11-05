"""Ca kiem cho ba man moi cua phan he Xuat kho va buoc xac nhan nhan hang.

Anh Viet chot 02/09/2026. Toan phep thuan cong voi vai phep doc ma nguon,
chay duoc khong can Frappe, khong can site, khong can thu vien mang.
"""

import io
import os

from vagabond import bo_phan, nhan_dieu_chuyen as ndc, tra_ncc, xuat_ban, xuat_noi_bo
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _goc():
	return os.path.dirname(
		os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	)


def _py(ten):
	return io.open(os.path.join(_goc(), "vagabond", ten), encoding="utf-8").read()


def _js(ten):
	return io.open(
		os.path.join(_goc(), "vagabond", "public", "js", "bep", ten), encoding="utf-8"
	).read()


# ==================================================================== cây bộ phận


@ca("bo phan: ten that ghep dung viet tat cong ty")
def _ten_that():
	la("ghep", bo_phan.ten_that("Marketing", "TV"), "Marketing - TV")
	# Ghep hai lan KHONG duoc ra "Marketing - TV - TV". Ham dung() tra cuu
	# theo ten day du, ghep chong len la moi phep tra cuu deu truot va may
	# tao them mot ban ghi nua moi lan deploy.
	la("khong ghep chong", bo_phan.ten_that("Marketing - TV", "TV"), "Marketing - TV")
	la("khong co viet tat", bo_phan.ten_that("Marketing", ""), "Marketing")
	la("ten rong", bo_phan.ten_that("", "TV"), "")


@ca("bo phan: cay co du ba khoi va khong ten nao trung")
def _cay():
	la("so khoi", len(bo_phan.cac_nhom()), 3)
	dung("khong ten nao trung trong ca cay", bo_phan.khong_trung())
	dung("co Marketing", "Marketing" in bo_phan.cac_la())
	dung("co Bep Baker", "Bếp Baker" in bo_phan.cac_la())
	dung("co Cua hang D1", "Cửa hàng D1" in bo_phan.cac_la())


@ca("bo phan: nhom khong phai la bo phan chiu chi phi")
def _nhom_khong_phai_la():
	# Gan chi phi vao mot NHOM thi ERPNext bao "khong ghi vao trung tam chi
	# phi nhom duoc", ma loi do bung ra luc ghi so chu khong luc go.
	dung("Marketing la la", bo_phan.la_bo_phan_hop_le("Marketing"))
	la("Khoi kinh doanh KHONG hop le", bo_phan.la_bo_phan_hop_le("Khối kinh doanh"), False)
	la("ten bia KHONG hop le", bo_phan.la_bo_phan_hop_le("Phòng abc"), False)
	la("rong KHONG hop le", bo_phan.la_bo_phan_hop_le(""), False)


@ca("bo phan: doc nguoc mot bo phan ra khoi cua no")
def _nhom_cua():
	la("marketing", bo_phan.nhom_cua("Marketing"), "Khối kinh doanh")
	la("bep baker", bo_phan.nhom_cua("Bếp Baker"), "Khối sản xuất")
	la("ke toan", bo_phan.nhom_cua("Kế toán"), "Khối hỗ trợ")
	la("khong biet", bo_phan.nhom_cua("Phòng abc"), None)


@ca("bo phan: dung() KHONG bo qua la khi nhom da co san")
def _dung_khong_bo_qua_la():
	# Lan deploy thu hai tro di, moi nhom deu da co nen `_tao_mot` tra None.
	# Ban dau viet `continue` ngay sau do, va the la moi bo phan LA khong
	# bao gio duoc dung. Chot bang ma nguon vi phep nay cham Frappe.
	m = _py("bo_phan.py")
	than = m.split("def dung(")[1].split("\ndef ")[0]
	dung("co ghi chu canh bao cai bay", "KHONG duoc `continue`" in than)
	dung(
		"chi continue khi cha THAT SU chua co",
		'if not frappe.db.exists("Cost Center", cha):' in than,
	)


# ======================================================= xuất dùng nội bộ


@ca("xuat noi bo: doc muc dich theo ma")
def _muc_dich():
	m = xuat_noi_bo.muc_dich_theo_ma("marketing")
	dung("tim ra marketing", m is not None)
	la("ten", m["ten"], "Marketing chụp ảnh, quay phim")
	la("ma la", xuat_noi_bo.muc_dich_theo_ma("khong-co"), None)
	la("rong", xuat_noi_bo.muc_dich_theo_ma(""), None)
	dung("hop le", xuat_noi_bo.la_muc_dich_hop_le("rnd"))
	la("khong hop le", xuat_noi_bo.la_muc_dich_hop_le("bia"), False)


@ca("xuat noi bo: moi muc dich mot bo tai khoan RIENG")
def _tk_rieng():
	# Day la ly do ton tai cua ca man. Banh Marketing mang di chup phai vao
	# chi phi ban hang, khong duoc vao cung cho voi hang hong.
	mk = xuat_noi_bo.muc_dich_theo_ma("marketing")
	rnd = xuat_noi_bo.muc_dich_theo_ma("rnd")
	dung("marketing uu tien 641", mk["tk"][0].startswith("641"))
	dung("rnd KHONG uu tien 641", not rnd["tk"][0].startswith("641"))
	dung("hai bo tai khoan khac nhau", mk["tk"] != rnd["tk"])
	# Moi muc dich phai co it nhat hai tai khoan de tut xuong. Cay tai khoan
	# cua tiem con dang hoan thien, khai mot so duy nhat la co ngay ca man
	# chet vi ke toan chua tao tai khoan do.
	for m in xuat_noi_bo.MUC_DICH:
		dung("%s co day du tru" % m["ma"], len(m["tk"]) >= 2)


@ca("xuat noi bo: goi y bo phan chi tra ten CO THAT trong cay")
def _goi_y():
	la("marketing", xuat_noi_bo.bo_phan_goi_y("marketing"), "Marketing")
	la("rnd", xuat_noi_bo.bo_phan_goi_y("rnd"), "Sonneto Lab")
	la("nhan vien khong doan", xuat_noi_bo.bo_phan_goi_y("nhan_vien"), "")
	la("ma la", xuat_noi_bo.bo_phan_goi_y("khong-co"), "")
	# Moi goi y phai la mot bo phan THAT. Goi y mot ten khong co trong cay
	# la dien san mot gia tri ma may chu se tu choi luc luu.
	for m in xuat_noi_bo.MUC_DICH:
		goi = xuat_noi_bo.bo_phan_goi_y(m["ma"])
		if goi:
			dung("goi y %s co that" % goi, bo_phan.la_bo_phan_hop_le(goi))


@ca("xuat noi bo: thieu gi bao du ba cau, khong bao thua")
def _thieu_gi():
	la("du het", xuat_noi_bo.thieu_gi("marketing", "Marketing", 2), [])
	la("thieu muc dich", len(xuat_noi_bo.thieu_gi("", "Marketing", 2)), 1)
	la("thieu bo phan", len(xuat_noi_bo.thieu_gi("marketing", "", 2)), 1)
	la("khong co dong", len(xuat_noi_bo.thieu_gi("marketing", "Marketing", 0)), 1)
	la("thieu ca ba", len(xuat_noi_bo.thieu_gi("", "", 0)), 3)
	# Nhom KHONG duoc coi la bo phan hop le, ke ca khi go dung ten nhom.
	la("nhom khong qua", len(xuat_noi_bo.thieu_gi("marketing", "Khối kinh doanh", 2)), 1)


@ca("xuat noi bo: dien giai phieu doc duoc tren ban may tinh")
def _dien_giai_nb():
	la(
		"day du",
		xuat_noi_bo.ghi_chu_phieu("Marketing chụp ảnh", "Marketing", "bộ ảnh Trung thu"),
		"Xuất dùng nội bộ - Marketing chụp ảnh - Bộ phận: Marketing. bộ ảnh Trung thu",
	)
	la(
		"khong ghi chu",
		xuat_noi_bo.ghi_chu_phieu("Marketing chụp ảnh", "Marketing", ""),
		"Xuất dùng nội bộ - Marketing chụp ảnh - Bộ phận: Marketing",
	)
	la("trong tron", xuat_noi_bo.ghi_chu_phieu("", "", ""), "Xuất dùng nội bộ")


@ca("xuat noi bo: danh sach Xuat huy KHONG con lan phieu noi bo")
def _khong_lan_danh_sach():
	# Ca hai deu la Material Issue. Khong loc thi banh Marketing mang di
	# chup nam lan trong danh sach hang huy - dung cai loi ma man moi sinh
	# ra de chua.
	m = _py("xuat_kho.py")
	than = m.split("def ds_phieu(")[1].split("\n@frappe.whitelist()")[0]
	dung("co loc theo muc dich", 'dieu_kien["vgb_muc_dich_xuat"]' in than)
	dung("chi loc khi la phieu huy", 'if loai == "huy":' in than)


@ca("xuat noi bo: phieu ghi bo phan vao TUNG DONG chu khong chi dau phieu")
def _cost_center_tung_dong():
	# ERPNext lay `cost_center` cua TUNG DONG khi len but toan. Dat o dau
	# phieu thoi thi so cai van vao trung tam chi phi mac dinh, va ca man
	# nay thanh vo nghia ma khong bao gi.
	m = _py("xuat_noi_bo.py")
	than = m.split("def luu(")[1].split("\n@frappe.whitelist()")[0]
	dung("moi dong mang cost_center", '"cost_center": ma_tt,' in than)
	dung("chan bo phan khong co that", 'frappe.db.exists("Cost Center", ma_tt)' in than)


# ================================================= trả lại nhà cung cấp


@ca("tra ncc: con tra duoc khong bao gio am")
def _con_tra():
	la("chua tra gi", tra_ncc.con_tra_duoc(10, 0), 10.0)
	la("da tra mot phan", tra_ncc.con_tra_duoc(10, 4), 6.0)
	la("da tra het", tra_ncc.con_tra_duoc(10, 10), 0.0)
	# Tra vuot la vo nghia, va so am lot xuong duoi se thanh mot dong tra
	# NGUOC CHIEU ma khong ai ngo toi.
	la("tra vuot van la 0", tra_ncc.con_tra_duoc(10, 12), 0.0)


@ca("tra ncc: gop so da tra doi dau AM sang duong")
def _gop_da_tra():
	# ERPNext ghi dong tra bang so AM. Quen doi dau la con lai tinh thanh
	# da_nhan cong da_tra, tuc la cang tra cang duoc tra nhieu hon.
	g = tra_ncc.gop_da_tra([{"ma": "A", "sl": -3}, {"ma": "A", "sl": -2}, {"ma": "B", "sl": -1}])
	la("gop A", g["A"], 5.0)
	la("gop B", g["B"], 1.0)
	la("rong", tra_ncc.gop_da_tra([]), {})


@ca("tra ncc: loc dong chan so vuot, bo dong 0 im lang")
def _loc_dong():
	con = {"A": 5.0, "B": 2.0}
	sach, loi = tra_ncc.loc_dong_tra([{"ma": "A", "sl": 3}, {"ma": "B", "sl": 0}], con)
	la("giu mot dong", len(sach), 1)
	la("khong loi", loi, [])
	la("dong 0 bi bo", sach[0]["ma"], "A")

	sach2, loi2 = tra_ncc.loc_dong_tra([{"ma": "A", "sl": 9}], con)
	la("dong vuot khong duoc giu", len(sach2), 0)
	la("va co bao loi", len(loi2), 1)
	dung("cau loi noi ro con bao nhieu", "chỉ còn 5" in loi2[0])


@ca("tra ncc: ly do phai nam trong danh muc")
def _ly_do():
	dung("hang loi", tra_ncc.la_ly_do_hop_le("Hàng lỗi, hư hỏng"))
	la("ly do bia", tra_ncc.la_ly_do_hop_le("Tự nghĩ ra"), False)
	la("rong", tra_ncc.la_ly_do_hop_le(""), False)
	la("du sau ly do", len(tra_ncc.LY_DO), 6)


@ca("tra ncc: phieu tra ghi SO AM va neo ve phieu goc")
def _so_am_va_neo():
	# Hai cai bay lon nhat cua nghiep vu nay, chot bang ma nguon.
	m = _py("tra_ncc.py")
	than = m.split("def luu(")[1].split("\n@frappe.whitelist()")[0]
	dung("qty la so am", '"qty": -abs(d["sl"]),' in than)
	dung("co neo return_against", "tra.return_against = goc.name" in than)
	dung("co bat co is_return", "tra.is_return = 1" in than)
	# Khong neo phieu goc thi ERPNext khong biet hoan gia nao: mot ma bot
	# mua thang truoc 80 nghin mot ky, thang nay 95 nghin.
	dung("co neo tung dong ve dong goc", '"purchase_receipt_item"' in than)


@ca("tra ncc: man xem hien SO DUONG cho nguoi doc")
def _hien_so_duong():
	# Trong so ERPNext no la so am, nhung mot dong "tra ve -3 cai" doc len
	# nghe nhu tra nguoc chieu.
	m = _py("tra_ncc.py")
	than = m.split("def chi_tiet(")[1]
	dung("so luong lay tri tuyet doi", '"sl": abs(flt(d.qty)),' in than)
	dung("tien cung lay tri tuyet doi", '"tien": abs(flt(d.amount)),' in than)


@ca("tra ncc: doc so da tra loc bang parenttype, KHONG dung parent=")
def _khong_dung_parent():
	# Ban Frappe cua site nem thang TypeError "execute() got an unexpected
	# keyword argument 'parent'". Da lam chet man Lenh san xuat o v353.
	m = _py("tra_ncc.py")
	import re as _re

	khong_ghi_chu = _re.sub(r"#.*", "", m)
	la("khong co parent= lam doi so rieng", "parent=" in khong_ghi_chu, False)
	dung("co loc bang parenttype", '"parenttype": "Purchase Receipt"' in m)


# ========================================================= xuất bán sỉ


@ca("xuat ban si: thieu gi bao du")
def _thieu_si():
	la("du het", xuat_ban.thieu_gi("KH-001", "Kho tổng", 2), [])
	la("thieu khach", len(xuat_ban.thieu_gi("", "Kho tổng", 2)), 1)
	la("thieu kho", len(xuat_ban.thieu_gi("KH-001", "", 2)), 1)
	la("khong co dong", len(xuat_ban.thieu_gi("KH-001", "Kho tổng", 0)), 1)
	la("thieu ca ba", len(xuat_ban.thieu_gi("", "", 0)), 3)


@ca("xuat ban si: cau canh bao tru kho hai lan VAN CON")
def _canh_bao():
	# Bo cau nay di la nguoi lap khong con biet vi sao ton kho cua don si
	# di khac ban le tai quay. Hoa don ban hien deu update_stock = 0.
	c = xuat_ban.canh_bao_trung_kho()
	dung("noi ro la tru kho that", "TRỪ KHO" in c)
	dung("nhac ke toan dung bat Cap nhat kho", "Cập nhật kho" in c)
	dung("noi ro hau qua", "hai lần" in c)
	# Man hinh phai do cau nay tu may chu, khong go cung mot ban thu hai.
	j = _js("45-xuat-kho-them.js")
	dung("man hinh do tu may chu", "h(b.canh_bao || '')" in j)


@ca("xuat ban si: dien giai phieu giao")
def _dien_giai_si():
	la(
		"day du",
		xuat_ban.dien_giai("Cty ABC", "chị Lan", "giao đợt 1"),
		"Xuất bán sỉ - Cty ABC - Người nhận: chị Lan. giao đợt 1",
	)
	la("toi thieu", xuat_ban.dien_giai("", "", ""), "Xuất bán sỉ")


# ============================================ xác nhận nhận hàng điều chuyển


@ca("nhan dieu chuyen: lech duong la thieu, am la thua")
def _lech():
	la("nhan thieu", ndc.lech_mot_dong(10, 8), 2.0)
	la("nhan du", ndc.lech_mot_dong(10, 10), 0.0)
	# Nhan thua nghe la doi nhung co that: kho xuat soan du mot goi ma
	# khong sua phieu.
	la("nhan thua", ndc.lech_mot_dong(10, 11), -1.0)


@ca("nhan dieu chuyen: so gan bang nhau coi nhu bang nhau")
def _eps():
	# So bang dau bang tran la sai: 1.9999999 va 2.0 la cung mot so trong
	# doi that, nhat la voi don vi gram va ml.
	la("gan bang", ndc.co_lech(2.0, 1.9999999), False)
	la("lech that", ndc.co_lech(2.0, 1.9), True)


@ca("nhan dieu chuyen: mot dong lech la ca phieu mang nhan Nhan thieu")
def _trang_thai():
	du = [{"giao": 10, "nhan": 10}, {"giao": 5, "nhan": 5}]
	la("du het", ndc.trang_thai_tu_cac_dong(du), ndc.DU)
	mot = [{"giao": 10, "nhan": 10}, {"giao": 5, "nhan": 4}]
	la("mot dong lech", ndc.trang_thai_tu_cac_dong(mot), ndc.THIEU)
	la("phieu rong", ndc.trang_thai_tu_cac_dong([]), ndc.DU)


@ca("nhan dieu chuyen: chi liet ke dong CO lech")
def _cac_dong_lech():
	ds = ndc.cac_dong_lech(
		[
			{"ma": "A", "giao": 10, "nhan": 8},
			{"ma": "B", "giao": 5, "nhan": 5},
			{"ma": "C", "giao": 2, "nhan": 3},
		]
	)
	la("chi hai dong", len(ds), 2)
	la("dong dau la A", ds[0]["ma"], "A")
	la("lech cua A", ds[0]["lech"], 2.0)
	la("lech cua C am", ds[1]["lech"], -1.0)


@ca("nhan dieu chuyen: doc so nhan chan so am, bo ma la")
def _doc_so_nhan():
	giao = {"A": 10.0, "B": 5.0}
	so, loi = ndc.doc_so_nhan([{"ma": "A", "nhan": 8}, {"ma": "B", "nhan": 5}], giao)
	la("doc du hai ma", len(so), 2)
	la("khong loi", loi, [])
	la("so cua A", so["A"], 8.0)

	# Ma khong co trong phieu thi BO QUA, khong nem loi: may khach cu cach
	# mot ban co the gui len ma da bi go khoi phieu.
	so2, loi2 = ndc.doc_so_nhan([{"ma": "Z", "nhan": 3}], giao)
	la("ma la bi bo", len(so2), 0)
	la("va khong bao loi", loi2, [])

	so3, loi3 = ndc.doc_so_nhan([{"ma": "A", "nhan": -1}], giao)
	la("so am bi chan", len(so3), 0)
	la("va co bao loi", len(loi3), 1)

	# Nhan NHIEU hon so giao thi cho qua, co y. Chan lai chi khien nguoi ta
	# go bua mot con so cho qua man.
	so4, loi4 = ndc.doc_so_nhan([{"ma": "A", "nhan": 12}], giao)
	la("nhan thua duoc chap nhan", so4["A"], 12.0)
	la("khong bao loi", loi4, [])


@ca("nhan dieu chuyen: cau bao lech doc duoc va cat khi qua dai")
def _cau_lech():
	la("khong lech thi rong", ndc.cau_bao_lech([]), "")
	c = ndc.cau_bao_lech([{"ma": "A", "lech": 2}, {"ma": "B", "lech": -1}])
	la("hai dong", c, "thiếu 2 A, thừa 1 B")
	nhieu = [{"ma": "M%d" % i, "lech": 1} for i in range(7)]
	c2 = ndc.cau_bao_lech(nhieu)
	dung("cat bot va noi ro con may dong", "và 3 dòng nữa" in c2)


@ca("nhan dieu chuyen: khong sua phieu goc; phan thieu tra bang PHIEU MOI (v639, anh Viet chon cach 1)")
def _khong_dung_so_kho():
	# v352 toi v638: man nay tuyet doi khong dung so kho. v639 anh Viet chon
	# cach 1: phan THIEU tu tra ve kho di bang mot phieu dieu chuyen MOI, con
	# phieu goc van khong bi sua. Chot bang ma nguon: xac_nhan khong goi
	# doc.save(), khong sua qty phieu goc; phieu moi chi lap trong
	# _lap_phieu_tra_thieu va chi sau khi loi khai da commit.
	import re as _re

	m = _py("nhan_dieu_chuyen.py")
	than = m.split("def xac_nhan(")[1].split("\ndef _tra_phan_thieu")[0]
	than = _re.sub(r"#.*", "", than)
	than = _re.sub(r'"""[\s\S]*?"""', "", than)
	la("xac_nhan khong tu sinh Stock Entry", "_phieu_moi" in than or "frappe.new_doc" in than, False)
	la("xac_nhan khong ghi so gi", ".submit()" in than, False)
	la("khong sua qty phieu goc", '"qty"' in than, False)
	la("khong goi doc.save", "doc.save(" in than, False)
	dung("loi khai commit TRUOC khi tra phan thieu", than.index("frappe.db.commit()") < than.index("_tra_phan_thieu(doc, thieu, thua)"))
	lap = m.split("def _lap_phieu_tra_thieu(")[1].split("\ndef _cong_ty_cua")[0]
	dung("phieu tra di tu kho NHAN ve kho DI", "moi.from_warehouse = kho_nhan" in lap and "moi.to_warehouse = kho_di" in lap)
	dung("phieu tra chan qua ton kho nhan", "_chan_qua_ton(kho_nhan, sach)" in lap)
	dung("phieu tra noi ve phieu goc", "moi.vgb_tra_thieu_cua = doc.name" in lap)
	tra = m.split("def _tra_phan_thieu(")[1].split("\ndef _lap_phieu_tra_thieu")[0]
	dung("lap hong thi rollback va giu cach cu", "frappe.db.rollback()" in tra and "treo việc cho thủ kho" in tra)
	# Codex PR #542 vong 2 (AGENTS.md muc 6): doi so kho that phai co ca tich hop
	# chay tren bench, dang ky trong cua.py.
	goc = os.path.join(_goc(), "vagabond", "khung", "kiem_that")
	with io.open(os.path.join(goc, "cua.py"), encoding="utf-8") as f:
		cua = f.read()
	dung("ca tich hop phieu tra dang ky trong cua.py", "thu_tra_thieu_639" in cua and os.path.exists(os.path.join(goc, "thu_tra_thieu_639.py")))
	with io.open(os.path.join(goc, "thu_tra_thieu_639.py"), encoding="utf-8") as f:
		ti = f.read()
	dung("ca tich hop goi dung cua xac_nhan, ghi so that, doc lai so kho", "ndc.xac_nhan(" in ti and ".submit()" in ti and "Stock Ledger Entry" in ti and ti.count("@ca(") >= 3)


@ca("nhan dieu chuyen v639: phan thieu -> dong tra (thua khong tra), cau bao; chay that xac_nhan voi Frappe gia: phieu tra dung kho, dung so, noi hai chieu, danh dau da xu ly, bao bep; tra hong thi treo viec va noi ro")
def _tra_phan_thieu():
	import json as _json
	from unittest.mock import patch

	import frappe as _fr

	from vagabond import tin_kho, xuat_kho

	lech = [{"ma": "BAWC00001", "ten": "Shiopan", "giao": 10, "nhan": 9, "lech": 1.0},
		{"ma": "BAWC00002", "ten": "Croissant", "giao": 5, "nhan": 6, "lech": -1.0},
		{"ma": "BAWC00003", "ten": "Canelé", "giao": 4, "nhan": 1.5, "lech": 2.5}]
	la("chi dong thieu", ndc.dong_tra_thieu(lech), [{"ma": "BAWC00001", "ten": "Shiopan", "sl": 1.0}, {"ma": "BAWC00003", "ten": "Canelé", "sl": 2.5}])
	la("cau bao", ndc.cau_tra_thieu("MAT-STE-2026-00700", ndc.dong_tra_thieu(lech)), "Đã lập phiếu MAT-STE-2026-00700 trả 1 Shiopan, 2.5 Canelé về kho đi")
	la("khong thieu thi khong cau", ndc.cau_tra_thieu("", []), "")

	class Dong(dict):
		def __getattr__(self, k):
			return self.get(k)

	class Goc:
		"""Phieu goc gia: thuoc tinh nhu Document that (co .items la danh sach, khong
		phai dict.items), co .get nhu Document."""
		def __init__(self, **o):
			self.__dict__.update(o)

		def get(self, k, mac_dinh=None):
			return self.__dict__.get(k, mac_dinh)

		def __getattr__(self, k):
			return self.__dict__.get(k)

	class PhieuMoi:
		def __init__(self):
			self.items = []
			self.flags = __import__("types").SimpleNamespace()
			self.name = ""
			self.da_ghi_so = 0

		def append(self, bang, d):
			self.items.append(d)

		def insert(self, **k):
			self.name = "MAT-STE-2026-00700"

		def submit(self):
			self.da_ghi_so = 1

	goc = Goc(name="MAT-STE-2026-00661", purpose="Material Transfer", docstatus=1, company="Vagabond",
		from_warehouse="Kho Baker - VGB", to_warehouse="Kho D1 - VGB", vgb_nhan_tt="",
		items=[Dong(name="r1", item_code="BAWC00001", item_name="Shiopan", uom="Cái", qty=10),
			Dong(name="r2", item_code="BAWC00002", item_name="Croissant", uom="Cái", qty=5)])
	ghi, moi, tin, ton = [], [], [], {"BAWC00001": 10}
	ps = PhieuMoi()

	def set_value(dt, ten, truong, gt=None, **k):
		ghi.append((dt, ten, truong if isinstance(truong, dict) else {truong: gt}))

	def get_value(dt, loc, truong=None, **k):
		if dt == "Bin":
			return ton.get(loc.get("item_code"), 0)
		return None

	def sql(cau, ts=None, **k):
		# Khoá tên MariaDB giả: luôn lấy được (ca đua riêng ở _tra_thieu_dua).
		return [[1]] if "lock(" in cau else []
	with patch.object(xuat_kho, "LOAI", {"chuyen": "Material Transfer"}), \
			patch.object(xuat_kho, "_duoc_xuat", lambda: True), patch.object(xuat_kho, "_kho_phu_trach", lambda *a, **k: ["Kho D1 - VGB"]), \
			patch.object(xuat_kho, "_phieu_moi", lambda loai, ct: moi.append((loai, ct)) or ps), \
			patch.object(xuat_kho, "_tk_chi_phi", lambda ct: "632 - VGB"), \
			patch.object(_fr, "get_doc", lambda dt, ten=None, *a, **k: goc if dt == "Stock Entry" else Dong(insert=lambda **kk: None)), \
			patch.object(_fr.db, "exists", lambda *a, **k: True), patch.object(_fr.db, "set_value", set_value), \
			patch.object(_fr.db, "get_value", get_value), patch.object(_fr.db, "sql", sql), \
			patch.object(tin_kho, "bao_da_nhan_chuyen", lambda *a, **k: None), \
			patch.object(tin_kho.kenh_zalo, "bao", lambda *a, **k: tin.append((a, k))):
		r = ndc.xac_nhan("MAT-STE-2026-00661", _json.dumps([{"ma": "BAWC00001", "nhan": 9}, {"ma": "BAWC00002", "nhan": 5}]), "thùng rách")
	la("trang thai", (r["trang_thai"], r["phieu_tra"], r["loi_tra"], r["con_thua"]), ("Nhận thiếu", "MAT-STE-2026-00700", "", ""))
	la("cau tra", r["cau_tra"], "Đã lập phiếu MAT-STE-2026-00700 trả 1 Shiopan về kho đi")
	la("phieu tra: dieu chuyen, tu kho nhan ve kho di, dung dong thieu", (moi, ps.from_warehouse, ps.to_warehouse, ps.da_ghi_so, ps.vgb_tra_thieu_cua,
		[(x["item_code"], x["qty"], x["s_warehouse"], x["t_warehouse"]) for x in ps.items]),
		([("chuyen", "Vagabond")], "Kho D1 - VGB", "Kho Baker - VGB", 1, "MAT-STE-2026-00661", [("BAWC00001", 1.0, "Kho D1 - VGB", "Kho Baker - VGB")]))
	goc_ghi = [g for g in ghi if g[0] == "Stock Entry" and g[1] == "MAT-STE-2026-00661"]
	dung("phieu goc noi sang phieu tra va danh dau da xu ly", any(g[2].get("vgb_phieu_tra_thieu") == "MAT-STE-2026-00700" and g[2].get("vgb_nhan_da_xu_ly") == 1 for g in goc_ghi))
	dung("loi khai van ghi", any(g[2].get("vgb_nhan_tt") == "Nhận thiếu" for g in goc_ghi))
	la("tin Zalo bep", [(a[0], a[1], k["ma_tin"], k["khoa"]) for a, k in tin], [("canh_bao", "san_xuat", "bep_hang_tra_thieu", "dc-tra-thieu:MAT-STE-2026-00661")])
	a, k = tin[0]
	dung("tin noi phieu tra, so thieu, viec bep can lam", any("MAT-STE-2026-00700" in x for x in a[3]) and any("Shiopan" in x and "1" in x for x in a[3]) and any("lập phiếu xuất huỷ" in x for x in a[3]))

	# Tra hong: kho nhan da ban mat phan do (ton 0) -> giu cach cu, treo viec, noi ro.
	goc2 = Goc(**goc.__dict__); goc2.vgb_nhan_tt = ""
	ghi.clear(); tin.clear(); ton["BAWC00001"] = 0
	with patch.object(xuat_kho, "LOAI", {"chuyen": "Material Transfer"}), \
			patch.object(xuat_kho, "_duoc_xuat", lambda: True), patch.object(xuat_kho, "_kho_phu_trach", lambda *a, **k: ["Kho D1 - VGB"]), \
			patch.object(xuat_kho, "_phieu_moi", lambda loai, ct: PhieuMoi()), patch.object(xuat_kho, "_tk_chi_phi", lambda ct: "632 - VGB"), \
			patch.object(_fr, "get_doc", lambda dt, ten=None, *a, **k: goc2 if dt == "Stock Entry" else Dong(insert=lambda **kk: None)), \
			patch.object(_fr.db, "exists", lambda *a, **k: True), patch.object(_fr.db, "set_value", set_value), \
			patch.object(_fr.db, "get_value", get_value), patch.object(_fr.db, "sql", sql), \
			patch.object(tin_kho, "bao_da_nhan_chuyen", lambda *a, **k: None), \
			patch.object(tin_kho.kenh_zalo, "bao", lambda *a, **k: tin.append((a, k))):
		r = ndc.xac_nhan("MAT-STE-2026-00661", _json.dumps([{"ma": "BAWC00001", "nhan": 9}]), "")
	dung("tra hong: khong phieu tra, co cau loi vuot ton", r["phieu_tra"] == "" and "vượt quá tồn" in r["loi_tra"])
	dung("van ghi loi khai, KHONG danh dau da xu ly", any(g[2].get("vgb_nhan_tt") == "Nhận thiếu" for g in ghi) and not any(g[2].get("vgb_nhan_da_xu_ly") == 1 for g in ghi))
	la("khong bao bep", tin, [])
	# Nhan thua: khong lap phieu gi.
	goc3 = Goc(**goc.__dict__); goc3.vgb_nhan_tt = ""
	ghi.clear(); moi.clear()
	with patch.object(xuat_kho, "LOAI", {"chuyen": "Material Transfer"}), \
			patch.object(xuat_kho, "_duoc_xuat", lambda: True), patch.object(xuat_kho, "_kho_phu_trach", lambda *a, **k: ["Kho D1 - VGB"]), \
			patch.object(xuat_kho, "_phieu_moi", lambda loai, ct: moi.append(1) or PhieuMoi()), \
			patch.object(_fr, "get_doc", lambda dt, ten=None, *a, **k: goc3 if dt == "Stock Entry" else Dong(insert=lambda **kk: None)), \
			patch.object(_fr.db, "exists", lambda *a, **k: True), patch.object(_fr.db, "set_value", set_value), patch.object(_fr.db, "sql", sql), \
			patch.object(tin_kho, "bao_da_nhan_chuyen", lambda *a, **k: None), patch.object(tin_kho.kenh_zalo, "bao", lambda *a, **k: None):
		r = ndc.xac_nhan("MAT-STE-2026-00661", _json.dumps([{"ma": "BAWC00002", "nhan": 6}]), "")
	la("thua: nhan thieu (lech) nhung khong lap phieu tra", (r["trang_thai"], r["phieu_tra"], moi), ("Nhận thiếu", "", []))
	# Codex PR #542 vong 2: vua THIEU A vua THUA B: tra A nhung KHONG dong viec, vi
	# phan thua B thu kho van phai doi chieu; man nguoi bam duoc bao con thua.
	la("dong con thua (thuan)", ndc.dong_con_thua(lech), [{"ma": "BAWC00002", "ten": "Croissant", "giao": 5, "nhan": 6, "lech": -1.0}])
	goc4 = Goc(**goc.__dict__); goc4.vgb_nhan_tt = ""
	ghi.clear(); moi.clear(); tin.clear(); ton["BAWC00001"] = 10
	ps4 = PhieuMoi()
	with patch.object(xuat_kho, "LOAI", {"chuyen": "Material Transfer"}), \
			patch.object(xuat_kho, "_duoc_xuat", lambda: True), patch.object(xuat_kho, "_kho_phu_trach", lambda *a, **k: ["Kho D1 - VGB"]), \
			patch.object(xuat_kho, "_phieu_moi", lambda loai, ct: moi.append(1) or ps4), patch.object(xuat_kho, "_tk_chi_phi", lambda ct: "632 - VGB"), \
			patch.object(_fr, "get_doc", lambda dt, ten=None, *a, **k: goc4 if dt == "Stock Entry" else Dong(insert=lambda **kk: None)), \
			patch.object(_fr.db, "exists", lambda *a, **k: True), patch.object(_fr.db, "set_value", set_value), \
			patch.object(_fr.db, "get_value", get_value), patch.object(_fr.db, "sql", sql), \
			patch.object(tin_kho, "bao_da_nhan_chuyen", lambda *a, **k: None), patch.object(tin_kho.kenh_zalo, "bao", lambda *a, **k: tin.append((a, k))):
		r = ndc.xac_nhan("MAT-STE-2026-00661", _json.dumps([{"ma": "BAWC00001", "nhan": 9}, {"ma": "BAWC00002", "nhan": 6}]), "")
	la("thieu A thua B: tra A", (r["phieu_tra"], ps4.da_ghi_so, [(x["item_code"], x["qty"]) for x in ps4.items], r["con_thua"]),
		("MAT-STE-2026-00700", 1, [("BAWC00001", 1.0)], "thừa 1 BAWC00002"))
	goc4_ghi = [g for g in ghi if g[0] == "Stock Entry" and g[1] == "MAT-STE-2026-00661"]
	dung("noi phieu tra nhung KHONG danh dau da xu ly (con phan thua)", any(g[2].get("vgb_phieu_tra_thieu") == "MAT-STE-2026-00700" for g in goc4_ghi)
		and not any(g[2].get("vgb_nhan_da_xu_ly") == 1 for g in goc4_ghi))
	la("van bao bep", len(tin), 1)


@ca("nhan dieu chuyen v639 Codex PR #542 vong 2: hai nguoi cung xac nhan mot phieu cung luc: khoa theo phieu, doc lai trang thai trong khoa, chi MOT phieu tra, nguoi sau nghe 'da duoc xac nhan roi'")
def _tra_thieu_dua():
	import json as _json
	import threading
	from unittest.mock import patch

	import frappe as _fr

	from vagabond import tin_kho, xuat_kho

	class Dong(dict):
		def __getattr__(self, k):
			return self.get(k)

	class Goc:
		def __init__(self, **o):
			self.__dict__.update(o)

		def get(self, k, mac_dinh=None):
			return self.__dict__.get(k, mac_dinh)

		def __getattr__(self, k):
			return self.__dict__.get(k)

	class PhieuMoi:
		def __init__(self, ten):
			self.items, self.flags, self.name, self.da_ghi_so = [], __import__("types").SimpleNamespace(), ten, 0

		def append(self, bang, d):
			self.items.append(d)

		def insert(self, **k):
			pass

		def submit(self):
			self.da_ghi_so = 1

	# Co so du lieu gia: cac o ghi vet cua phieu goc. get_doc tra ANH CHUP CU (vgb_nhan_tt
	# trong) cho ca hai luot, nhu doc duoc doc truoc khi luot kia commit; chi
	# get_value(for_update) moi thay so moi.
	db = {"vgb_nhan_tt": "", "vgb_nhan_boi": "", "vgb_phieu_tra_thieu": ""}
	mu = threading.Lock()
	khoa_ten = {}
	goi_khoa = []
	moi = []
	cho = threading.Barrier(2)
	da_cho = set()

	def goc():
		return Goc(name="MAT-STE-2026-00661", purpose="Material Transfer", docstatus=1, company="Vagabond",
			from_warehouse="Kho Baker - VGB", to_warehouse="Kho D1 - VGB", vgb_nhan_tt="",
			items=[Dong(name="r1", item_code="BAWC00001", item_name="Shiopan", uom="Cái", qty=10)])

	def set_value(dt, ten, truong, gt=None, **k):
		if dt == "Stock Entry":
			with mu:
				db.update(truong if isinstance(truong, dict) else {truong: gt})

	def get_value(dt, loc, truong=None, **k):
		if dt == "Bin":
			return 10
		if dt == "Stock Entry" and k.get("for_update"):
			# Hai luot cung toi day thi cho nhau (khong khoa thi ca hai cung doc trong).
			t = threading.get_ident()
			if t not in da_cho:
				da_cho.add(t)
				try:
					cho.wait(timeout=1.0)
				except threading.BrokenBarrierError:
					pass
			with mu:
				return _fr._dict(db)
		return None

	def sql(cau, ts=None, **k):
		if "get_lock(" in cau:
			with mu:
				kt = khoa_ten.setdefault(ts[0], threading.Lock())
			ok = kt.acquire(timeout=float(ts[1]))
			goi_khoa.append(("lay", ts[0], ok))
			return [[1 if ok else 0]]
		if "release_lock(" in cau:
			kt = khoa_ten.get(ts[0])
			if kt and kt.locked():
				kt.release()
			goi_khoa.append(("nha", ts[0]))
			return [[1]]
		return []

	def phieu_moi(loai, ct):
		with mu:
			p = PhieuMoi("MAT-STE-2026-0070%d" % (len(moi) + 1))
			moi.append(p)
		return p

	kq = {}

	def chay(ai):
		try:
			kq[ai] = ndc.xac_nhan("MAT-STE-2026-00661", _json.dumps([{"ma": "BAWC00001", "nhan": 9}]), "")
		except Exception as e:
			kq[ai] = {"loi": str(e)}
	with patch.object(xuat_kho, "LOAI", {"chuyen": "Material Transfer"}), \
			patch.object(xuat_kho, "_duoc_xuat", lambda: True), patch.object(xuat_kho, "_kho_phu_trach", lambda *a, **k: ["Kho D1 - VGB"]), \
			patch.object(xuat_kho, "_phieu_moi", phieu_moi), patch.object(xuat_kho, "_tk_chi_phi", lambda ct: "632 - VGB"), \
			patch.object(_fr, "get_doc", lambda dt, ten=None, *a, **k: goc() if dt == "Stock Entry" else Dong(insert=lambda **kk: None)), \
			patch.object(_fr.db, "exists", lambda *a, **k: True), patch.object(_fr.db, "set_value", set_value), \
			patch.object(_fr.db, "get_value", get_value), patch.object(_fr.db, "sql", sql), \
			patch.object(_fr.db, "commit", lambda *a, **k: None), patch.object(_fr.db, "rollback", lambda *a, **k: None), \
			patch.object(tin_kho, "bao_da_nhan_chuyen", lambda *a, **k: None), patch.object(tin_kho.kenh_zalo, "bao", lambda *a, **k: None):
		ts = [threading.Thread(target=chay, args=("A",)), threading.Thread(target=chay, args=("B",))]
		for x in ts:
			x.start()
		for x in ts:
			x.join(20)
	ok = [r for r in kq.values() if r.get("ok")]
	loi = [r for r in kq.values() if r.get("loi")]
	la("dung MOT luot qua, MOT phieu tra ghi so", (len(ok), len(moi), sum(p.da_ghi_so for p in moi)), (1, 1, 1))
	dung("luot kia nghe 'da duoc ... xac nhan roi'", len(loi) == 1 and "xác nhận rồi" in loi[0]["loi"])
	la("phieu goc noi dung mot phieu tra, loi khai ghi mot lan", (db["vgb_phieu_tra_thieu"], db["vgb_nhan_tt"]), ("MAT-STE-2026-00701", "Nhận thiếu"))
	lay = [x for x in goi_khoa if x[0] == "lay"]
	nha = [x for x in goi_khoa if x[0] == "nha"]
	la("khoa theo phieu, lay 2 nha 2", ({x[1] for x in lay}, len(lay), len(nha)), ({"vgb_nhan_dc:MAT-STE-2026-00661"}, 2, 2))
	dung("khoa khong con bi giu", not any(k.locked() for k in khoa_ten.values()))
	# Lop bao ve thu hai: phieu goc da co phieu tra thi _tra_phan_thieu khong lap them.
	with patch.object(xuat_kho, "_phieu_moi", phieu_moi), patch.object(xuat_kho, "_tk_chi_phi", lambda ct: "632 - VGB"), \
			patch.object(_fr.db, "get_value", get_value), patch.object(_fr.db, "set_value", set_value), patch.object(_fr.db, "commit", lambda *a, **k: None), \
			patch.object(tin_kho.kenh_zalo, "bao", lambda *a, **k: None):
		ten, loi_tra = ndc._tra_phan_thieu(goc(), [{"ma": "BAWC00001", "ten": "Shiopan", "sl": 1.0}])
	la("da co phieu tra thi tra lai phieu cu, khong lap phieu thu hai", (ten, loi_tra, len(moi)), ("MAT-STE-2026-00701", "", 1))


@ca("nhan dieu chuyen: chi kho NHAN moi xac nhan duoc, va chi mot lan")
def _chan_nguoi_la():
	m = _py("nhan_dieu_chuyen.py")
	chan = m.split("def _chan_khong_phai_kho_nhan(")[1].split("\n@frappe.whitelist()")[0]
	dung("chan phieu khong phai dieu chuyen", 'LOAI["chuyen"]' in chan)
	dung("chan phieu chua ghi so", "cint(doc.docstatus) != 1" in chan)
	dung("chan kho khong phai cua minh", "doc.to_warehouse not in cua_toi" in chan)
	than = m.split("def xac_nhan(")[1].split("\ndef _ghi_vet")[0]
	# Codex PR #542 vong 2: doc trang thai bang locking read trong khoa, khong
	# tin anh chup cua doc.
	dung("chan xac nhan de len bang trang thai hien hanh", "_trang_thai_hien_hanh(phieu)" in than and "if tt_cu:" in than)
	dung("doc lai bang for_update", "for_update=True" in m.split("def _trang_thai_hien_hanh(")[1].split("\ndef ")[0])


@ca("nhan dieu chuyen: man hinh noi ro la khong sua ton kho")
def _man_noi_ro():
	# Nguoi nhan phai doc duoc dieu nay NGAY TREN MAN, khong phai chi trong
	# ma nguon. Khong noi thi ho tuong bam vao day la ton kho tu nan lai.
	j = _js("45-xuat-kho-them.js")
	than = j.split("async function scrNhanDcXacNhan(")[1]
	# v639: man noi ro so giao da vao so, thieu thi may tu tra ve kho di.
	dung("noi ro so giao da vao so kho", "đã vào sổ kho của bạn" in than)
	dung("noi ro thieu thi may tu lap phieu tra", "tự lập phiếu trả phần thiếu" in than)
	dung("ket qua noi phieu tra hoac treo viec", "r.phieu_tra" in than and "r.loi_tra" in than)
	# Dien san so giao de nguoi nhan chi phai sua dong nao thuc su lech.
	# Bat go lai ca bang la cach chac chan nhat de khong ai dung man nay.
	dung("dien san theo so giao", "nhan: x.giao" in than)


@ca("xuat kho them: ba man moi deu co trong bang duong dan")
def _co_duong():
	j = _js("02-trang-chu.js")
	for khoa in ("XKNB", "XKTRA", "XKSI"):
		dung("%s co trong nhom Xuat kho" % khoa, "'%s'" % khoa in j)
	dung("XKNB co dinh tuyen", "if (k === 'XKNB') return go(scrXkNbList);" in j)
	dung("XKTRA co dinh tuyen", "if (k === 'XKTRA') return go(scrXkTraList);" in j)
	dung("XKSI co dinh tuyen", "if (k === 'XKSI') return go(scrXkSiList);" in j)
	dung("duong dan xuat dung noi bo", "'xuat-dung-noi-bo': 'XKNB'" in j)
	dung("duong dan xuat tra ncc", "'xuat-tra-nha-cung-cap': 'XKTRA'" in j)
	dung("duong dan xuat ban si", "'xuat-ban-si': 'XKSI'" in j)


@ca("xuat kho them: ba man deu co ham dung o phan 45")
def _co_ham():
	j = _js("45-xuat-kho-them.js")
	for ten in (
		"scrXkNbList", "scrXkNbNew", "scrXkNbView",
		"scrXkTraList", "scrXkTraNew", "scrXkTraView",
		"scrXkSiList", "scrXkSiNew", "scrXkSiView",
		"scrNhanDcXacNhan",
	):
		dung("co %s" % ten, "function %s(" % ten in j)


@ca("xuat kho them: man chon hang dung chung KHONG bi doi chu ky")
def _khong_doi_chu_ky():
	# `vxDongHtml` dang duoc Xuat huy va Dieu chuyen goi o bon cho trong
	# 03-kho-chung-tu.js. Doi chu ky cua no la sua bon cho trong mot tep ma
	# cac phien khac hay dong vao. Phan 45 chep mot ban rieng thay vi sua.
	c = _js("03-kho-chung-tu.js")
	dung("ham cu con nguyen chu ky", "function vxDongHtml() {" in c)
	j = _js("45-xuat-kho-them.js")
	dung("phan 45 co ban rieng", "function xktDongHtml(gio, opt) {" in j)
	# Muon tam XK.gio de dung lai man chon hang cua 03 ma khong sua no.
	dung("co muon tam roi keo ve", "XK.gio = st.gio.slice();" in j)
	# v399: man chon hang cua 03 goi back() chu khong goi ham quay ve, nen
	# man lap phieu phai tu keo XK.gio ve o dau ham. Loi v397 tren site that:
	# chon mon xong ve man van "Chua co mon nao".
	dung("hai man lap phieu deu keo gio ve o dau ham", j.count("xktKeoGioVe(st);") == 2)
	dung("cam co dang chon truoc khi mo man chon hang", j.count("st.dangChon = true;") == 2)
	dung("khong con tin vao ham quay ve cua man chon hang", "return scrXkNbNew(); });" not in j and "return scrXkSiNew(); });" not in j)
	# Man chon hang: mon chua co anh thi o 🍰 giu hang, khong o chu cai
	# (nguyen tac 4, AGENTS.md muc 2b).
	dung("man chon hang khong ve o chu cai thay anh", "charAt(0).toUpperCase()" not in c[c.find("function scrXkChonHang"):c.find("function scrXkChonHang") + 12000])


@ca("xuat kho them: nut xac nhan chan noi len the cha")
def _chan_noi_len():
	# The cha co onclick dong lai phan dang mo. Bam nut xac nhan ma the cha
	# nghe duoc thi man tu sap lai truoc khi di sang man moi.
	c = _js("03-kho-chung-tu.js")
	# Cat tu chinh khoi bat su kien, KHONG cat tu "data-hvx" cuoi cung:
	# chuoi do xuat hien hai lan, va lan cuoi nam SAU dong stopPropagation
	# nen phep soi truot.
	than = c.split("b.querySelectorAll('[data-hvx]')")[1]
	dung("co stopPropagation", "ev.stopPropagation();" in than)
	dung("va mo dung man xac nhan", "scrNhanDcXacNhan(m)" in than)


@ca("xuat kho them: moi cua moi deu khai trong thu_cua_ngo")
def _khai_cua_ngo():
	# Chen mot ham moi vao giua dong @frappe.whitelist() va dong def cua ham
	# cu se lam ham cu mat quyen goi. Python khong bao, ca kiem khong bao,
	# cong tra ve 0, chi lo khi co nguoi bam vao man hinh.
	from vagabond.khung.kiem_thu import thu_cua_ngo

	for tep in ("bo_phan.py", "xuat_noi_bo.py", "tra_ncc.py", "xuat_ban.py",
			"nhan_dieu_chuyen.py"):
		dung("%s da khai" % tep, tep in thu_cua_ngo.CUA_NGO)


@ca("xuat kho them: truong tu them co goi du bon nhom moi")
def _khai_truong():
	m = _py("truong_tu_them.py")
	# Cay bo phan phai dung TRUOC: man Xuat dung noi bo bat buoc chon bo
	# phan, ma cay chua co thi o chon rong va khong ai luu duoc phieu nao.
	dung("co dung cay bo phan", "bo_phan.dung()" in m)
	for nhom in ("xuat_noi_bo", "tra_ncc", "xuat_ban", "nhan_dieu_chuyen"):
		dung("co dung nhom %s" % nhom, '"%s")' % nhom in m)
	i_bp = m.index("bo_phan.dung()")
	i_nb = m.index('_dung_nhom(xuat_noi_bo.TRUONG_MOI')
	dung("cay bo phan dung truoc o muc dich", i_bp < i_nb)
