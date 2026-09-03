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


@ca("nhan dieu chuyen: TUYET DOI khong dung toi so kho")
def _khong_dung_so_kho():
	# Cho de hieu nham nhat cua ca man. Chot bang ma nguon de mot lan sua
	# sau nay khong lam no thanh mot man nan ton kho.
	import re as _re

	m = _py("nhan_dieu_chuyen.py")
	than = m.split("def xac_nhan(")[1].split("\ndef _ghi_vet")[0]
	# BO GHI CHU truoc khi soi. Chinh doan ghi chu trong ham do co giai
	# thich vi sao KHONG goi doc.save(), nen ca kiem tu khop vao ghi chu cua
	# minh va bao hong. Da vap dung cai bay nay o v352 va v354.
	than = _re.sub(r"#.*", "", than)
	than = _re.sub(r'"""[\s\S]*?"""', "", than)
	la("khong sinh Stock Entry moi", "frappe.new_doc" in than, False)
	la("khong ghi so", ".submit()" in than, False)
	la("khong sua qty", '"qty"' in than, False)
	dung("chi ghi o ghi vet", "frappe.db.set_value(" in than)
	# Phieu da ghi so thi goi doc.save() la Frappe nem loi hoac de ra mot
	# ban sua doi khong ai muon.
	la("khong goi doc.save", "doc.save(" in than, False)


@ca("nhan dieu chuyen: chi kho NHAN moi xac nhan duoc, va chi mot lan")
def _chan_nguoi_la():
	m = _py("nhan_dieu_chuyen.py")
	chan = m.split("def _chan_khong_phai_kho_nhan(")[1].split("\n@frappe.whitelist()")[0]
	dung("chan phieu khong phai dieu chuyen", 'LOAI["chuyen"]' in chan)
	dung("chan phieu chua ghi so", "cint(doc.docstatus) != 1" in chan)
	dung("chan kho khong phai cua minh", "doc.to_warehouse not in cua_toi" in chan)
	than = m.split("def xac_nhan(")[1].split("\ndef _ghi_vet")[0]
	dung("chan xac nhan de len", 'doc.get("vgb_nhan_tt") or ""' in than)


@ca("nhan dieu chuyen: man hinh noi ro la khong sua ton kho")
def _man_noi_ro():
	# Nguoi nhan phai doc duoc dieu nay NGAY TREN MAN, khong phai chi trong
	# ma nguon. Khong noi thi ho tuong bam vao day la ton kho tu nan lai.
	j = _js("45-xuat-kho-them.js")
	than = j.split("async function scrNhanDcXacNhan(")[1]
	dung("co cau khong sua ton kho", "không sửa tồn kho" in than)
	dung("noi ro so kho giu nguyen", "Sổ kho vẫn giữ nguyên" in than)
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
