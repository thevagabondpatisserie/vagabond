"""Ca kiểm cho thu tiền hợp đồng, xuất hoá đơn, và đổi ruột hộp mùa vụ.

Anh Việt 28/08/2026 duyệt ba việc:

  1. Nút Tạo phiếu thanh toán trên hợp đồng đã ký, có mã QR và nội dung
     chuyển khoản theo cú pháp anh chốt.
  2. Nút Ghi sổ và xuất hoá đơn, hai kiểu nhập hàng hoá.
  3. Bảng đổi ruột hộp trên màn kiểm bánh mùa, sửa chỗ máy đang đếm sai.

Năm nhóm ca. Mọi ca chạy trên phép THUẦN hoặc đọc mã nguồn: không cần
Frappe, không cần site, không cần mạng, không cần thư viện requests.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")

MOC_FRAPPE = "# ------------------------------------------------------- phần cần Frappe"


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


def _js(ten):
	with io.open(os.path.join(BEP, ten), encoding="utf-8") as f:
		return f.read()


def _than_ham(s, dau):
	"""Cắt từ dòng def tới hết tệp. KHÔNG cắt ở dòng trống đầu tiên."""
	i = s.find(dau)
	return s[i:] if i >= 0 else ""


# --------------------------------- 1. Nội dung chuyển khoản và mức thu


@ca("phieu HD: noi dung chuyen khoan dung cu phap anh Viet chot")
def _nd_ck():
	from vagabond import thu_hop_dong as t

	la(
		"muc 50",
		t.noi_dung_ck(50, "HD-26-08-012"),
		"THANH TOAN 50PT GIA TRI HOP DONG HD2608012",
	)
	la(
		"muc 100",
		t.noi_dung_ck(100, "HD-26-08-012"),
		"THANH TOAN 100PT GIA TRI HOP DONG HD2608012",
	)
	la("so thuc lam tron", t.noi_dung_ck(50.0, "HD-1"), "THANH TOAN 50PT GIA TRI HOP DONG HD1")
	la("chuoi rac thanh 0", t.noi_dung_ck("x", "HD-1"), "THANH TOAN 0PT GIA TRI HOP DONG HD1")


@ca("phieu HD: ma hop dong bo dau va bo ky tu la")
def _sach_ma():
	from vagabond import thu_hop_dong as t

	la("bo gach ngang", t.sach_ma_hd("HD-26-08-012"), "HD2608012")
	la("viet hoa", t.sach_ma_hd("hd/26.08"), "HD2608")
	la("bo dau tieng Viet", t.sach_ma_hd("HĐ-26"), "HD26")
	la("rong thi rong", t.sach_ma_hd(None), "")


@ca("phieu HD: noi dung khong con dau tieng Viet nao")
def _khong_dau():
	from vagabond import thu_hop_dong as t

	nd = t.noi_dung_ck(50, "HỢP ĐỒNG số 12")
	for c in nd:
		dung("ky tu %r nam trong bang ASCII" % c, ord(c) < 128)


@ca("phieu HD: tien theo muc lam tron ve dong")
def _tien():
	from vagabond import thu_hop_dong as t

	la("50 phan tram", t.tien_theo_muc(17578800, 50), 8789400)
	la("100 phan tram", t.tien_theo_muc(17578800, 100), 17578800)
	la("lam tron le", t.tien_theo_muc(1001, 50), 501)
	la("gia tri 0", t.tien_theo_muc(0, 50), 0)
	la("muc 0", t.tien_theo_muc(1000, 0), 0)
	la("chuoi rac", t.tien_theo_muc("x", "y"), 0)


@ca("phieu HD: muc hop le chan so am va so qua 100")
def _muc():
	from vagabond import thu_hop_dong as t

	la("50 duoc", t.muc_hop_le(50), True)
	la("100 duoc", t.muc_hop_le(100), True)
	la("101 khong duoc", t.muc_hop_le(101), False)
	la("0 khong duoc", t.muc_hop_le(0), False)
	la("am khong duoc", t.muc_hop_le(-10), False)
	dung("nhan 100 doc duoc", "Toàn bộ" in t.nhan_muc(100))
	dung("nhan 50 co con so", "50%" in t.nhan_muc(50))


@ca("phieu HD: cau chan khi hop dong chua chot noi ra viec phai lam")
def _cau_chan():
	from vagabond import thu_hop_dong as t

	c = t.loi_chua_chot("Đang thương thảo")
	dung("noi trang thai", "Đang thương thảo" in c)
	dung("chi buoc phai lam", "Đang thực hiện" in c)
	for cam in ("trang_thai", "docstatus", "TT_HD_THU_DUOC"):
		dung("khong lo ten ky thuat %s" % cam, cam not in c)


@ca("tep thu_hop_dong: phan thuan KHONG cham Frappe")
def _thuan_thu():
	s = _doc("thu_hop_dong.py")
	dung("co moc chia hai phan", MOC_FRAPPE in s)
	than = s.split(MOC_FRAPPE)[0]
	for cam in ("import frappe", "frappe.", "requests"):
		dung("phan thuan khong co %s" % cam, cam not in than)


@ca("phieu HD: tien to ma rieng, han QR bang phieu cong no")
def _tien_to():
	from vagabond import thu_hop_dong as t

	la("tien to rieng", t.TIEN_TO, "PTHD")
	# KHONG import `cong_no` o day: no keo `ban_hang`, ma `ban_hang` import
	# `requests` ngay dau tep. May chay CI cua GitHub tay khong, nap vao la
	# ca ca kiem no. Doc thang ma nguon thay vi nap mo dun (bai hoc 20/08).
	s = _doc("cong_no.py")
	dung("tien to cong no van la DNTT", 'TIEN_TO_DNTT = "DNTT"' in s)
	dung("han QR bang nhau", "QR_SO_NGAY = %d" % t.QR_SO_NGAY in s)


@ca("phieu HD: chi thu tien khi hop dong da chot con so")
def _thu_duoc():
	from vagabond import thu_hop_dong as t

	for tt in ("Nhap", "Da gui khach", "Dang thuong thao", "Huy"):
		dung("%s KHONG thu duoc" % tt, tt not in t.TT_HD_THU_DUOC)
	for tt in ("Dang thuc hien", "Hoan tat", "Da thanh ly"):
		dung("%s thu duoc" % tt, tt in t.TT_HD_THU_DUOC)


@ca("phieu HD: to in dung chung khuon voi phieu cong no")
def _to_in():
	s = _doc("thu_hop_dong.py")
	than = _than_ham(s, "def _phieu_html(")
	dung("goi lai ba ham dinh dang cua cong_no", "from vagabond.cong_no import" in than)
	dung("dung ma QR cua cong_no", "_qr_data_uri(" in than)
	dung("so tien bang chu", "_chu_so_tien(" in than)
	dung("khong ve khuon thu hai", "PHIẾU THANH TOÁN HỢP ĐỒNG" in than)


@ca("phieu HD: thu gui tu hop sales, ban sao ve ke toan")
def _hop_thu():
	s = _doc("thu_hop_dong.py")
	dung("khai hop sales", 'EMAIL_SALES = "sales@thevagabondpatisserie.com"' in s)
	dung("khai hop ke toan", 'EMAIL_KE_TOAN = "account@thevagabondpatisserie.com"' in s)
	than = _than_ham(s, "def gui_email(")
	dung("gui tu sales", "sender=EMAIL_SALES" in than)
	dung("ban sao ke toan", "cc=[EMAIL_KE_TOAN]" in than)
	dung("dinh kem PDF", "attachments=" in than)
	dung("gan thu vao phieu", "reference_doctype=DT" in than)


# ----------------------------------- 2. Ghi sổ và xuất hoá đơn


@ca("ghi so HD: cong tien hang tinh lai tu so luong va don gia")
def _cong_tien():
	from vagabond import hop_dong_hoa_don as g

	dong = [
		{"so_luong": 60, "don_gia": 185000},
		{"so_luong": 40, "don_gia": 95000},
	]
	la("cong hai dong", g.cong_tien(dong), 11100000 + 3800000)
	la("co chiet khau", g.cong_tien([{"so_luong": 2, "don_gia": 100, "chiet_khau": 10}]), 180.0)
	la("bo dong so luong 0", g.cong_tien([{"so_luong": 0, "don_gia": 999}]), 0.0)
	la("rong", g.cong_tien([]), 0.0)
	la("chuoi rac khong lam vo", g.cong_tien([{"so_luong": "x", "don_gia": "y"}]), 0.0)


@ca("ghi so HD: lech qua nguong mot nghin dong thi phai hoi lai")
def _lech():
	from vagabond import hop_dong_hoa_don as g

	la("nguong dung 1000", g.NGUONG_LECH, 1000)
	la("lech 999 thi thoi", g.lech_qua_nguong(100999, 100000), False)
	la("lech 1000 thi thoi", g.lech_qua_nguong(101000, 100000), False)
	la("lech 1001 thi hoi", g.lech_qua_nguong(101001, 100000), True)
	la("lech am cung hoi", g.lech_qua_nguong(98000, 100000), True)

	c = g.loi_lech(17880000, 17578800)
	dung("noi cao hon", "cao hơn" in c)
	dung("co con so lech", "301.200" in c)
	c2 = g.loi_lech(17000000, 17578800)
	dung("noi thap hon", "thấp hơn" in c2)


@ca("ghi so HD: loc dong hang va ke ra dong bi bo vi sao")
def _loc_dong():
	from vagabond import hop_dong_hoa_don as g

	ok, nhac = g.dong_hop_le([
		{"ten_mon": "Set A", "so_luong": 2},
		{"ten_mon": "", "so_luong": 5},
		{"ten_mon": "Set B", "so_luong": 0},
	])
	la("giu mot dong", len(ok), 1)
	la("hai cau nhac", len(nhac), 2)
	dung("noi dong nao thieu ten", "chưa có tên món" in nhac[0])
	dung("noi dong nao so luong 0", "số lượng bằng 0" in nhac[1])
	dung("cau nhac co ten mon", "Set B" in nhac[1])


@ca("ghi so HD: chi ke toan moi ghi so, sales chi lap nhap")
def _quyen_ghi_so():
	s = _doc("hop_dong_hoa_don.py")
	than = _than_ham(s, "def ghi_so(")
	dung("co hang rao quyen", "loi_chua_ghi_so_duoc()" in than)
	i_chan = than.find("loi_chua_ghi_so_duoc()")
	i_lap = than.find('frappe.new_doc("Sales Invoice")')
	dung("chan TRUOC khi lap hoa don", 0 < i_chan < i_lap)
	dung("dung chung bang vai voi mua hang", "from vagabond.doi_chieu_mua import VAI_GHI_SO" in s)

	from vagabond import hop_dong_hoa_don as g

	c = g.loi_chua_ghi_so_duoc()
	dung("chi duong lam duoc", "hoá đơn nháp" in c)
	for cam in ("docstatus", "submit", "VAI_GHI_SO"):
		dung("khong lo ten ky thuat %s" % cam, cam not in c)


@ca("ghi so HD: lech thi chan truoc khi lap, khong lap roi moi bao")
def _chan_lech_truoc():
	s = _doc("hop_dong_hoa_don.py")
	than = _than_ham(s, "def ghi_so(")
	i_lech = than.find("loi_lech(tong, hd.gia_tri)")
	i_lap = than.find('frappe.new_doc("Sales Invoice")')
	dung("hoi lech truoc khi lap", 0 < i_lech < i_lap)
	dung("co duong xac nhan de di tiep", "xac_nhan_lech" in than)


@ca("ghi so HD: mon khong co ma thi KHONG tu de ma moi")
def _khong_de_ma():
	s = _doc("hop_dong_hoa_don.py")
	than = _than_ham(s, "def _dong_si(")
	khuc = than[: than.find("def _la_phi_giao")]
	dung("khong tao Item", "new_doc(\"Item\"" not in khuc and "insert" not in khuc)
	dung("roi ve ma dich vu dung chung", "_item_dich_vu()" in khuc)
	dung("giu nguyen ten nguoi go", "item_name" in khuc)


@ca("ghi so HD: hoa don gan so hop dong va day HDDT o trang thai cho ky")
def _gan_va_hddt():
	s = _doc("hop_dong_hoa_don.py")
	than = _than_ham(s, "def ghi_so(")
	dung("gan hop dong vao hoa don", "si.custom_hop_dong = hd.name" in than)
	dung("day HDDT qua duong da co", "_tu_xuat_hddt" in than)
	dung("khong tu ky", "ky_hoa_don" not in than and "sign" not in than)
	dung("hong HDDT khong lam hong ghi so", "except Exception" in than)


# ------------------------------------- 3. Đổi ruột hộp mùa vụ


@ca("doi ruot: gom mot don thanh muc chenh theo tung ma banh")
def _gom():
	from vagabond import mua_vu as m

	dong = [{
		"ngay": "2026-09-04", "ma_hop": "BASS00012", "so_hop": 25,
		"ma_banh_bot": "BASS00002", "sl_bot": 1,
		"ma_banh_them": "BASS00005", "sl_them": 1,
	}]
	la("bot thi am", m.gom_doi_ruot(dong).get("BASS00002"), -25)
	la("them thi duong", m.gom_doi_ruot(dong).get("BASS00005"), 25)
	la("loc dung ngay", m.gom_doi_ruot(dong, "2026-09-04").get("BASS00002"), -25)
	la("ngay khac thi rong", m.gom_doi_ruot(dong, "2026-09-05"), {})
	la("so hop 0 thi bo qua", m.gom_doi_ruot([dict(dong[0], so_hop=0)]), {})
	la("rong", m.gom_doi_ruot([]), {})


@ca("doi ruot: khai mot ben cung duoc")
def _mot_ben():
	from vagabond import mua_vu as m

	chi_bot = [{"ma_hop": "H", "so_hop": 10, "ma_banh_bot": "A", "sl_bot": 2}]
	la("chi bot", m.gom_doi_ruot(chi_bot), {"A": -20})
	chi_them = [{"ma_hop": "H", "so_hop": 10, "ma_banh_them": "B", "sl_them": 3}]
	la("chi them", m.gom_doi_ruot(chi_them), {"B": 30})


@ca("doi ruot: ap len so banh le bi hop an, KHONG sua ban goc")
def _ap():
	from vagabond import mua_vu as m

	goc = {"A": 100, "B": 50}
	ra = m.ap_doi_ruot(goc, {"A": -25, "B": 25})
	la("A giam", ra["A"], 75)
	la("B tang", ra["B"], 75)
	la("ban goc khong doi", goc, {"A": 100, "B": 50})
	la("ma moi duoc them vao", m.ap_doi_ruot({}, {"C": 7}), {"C": 7})


@ca("doi ruot: kep san o 0, banh khong tu moc ra")
def _kep_san():
	from vagabond import mua_vu as m

	la("am thi ve 0", m.ap_doi_ruot({"A": 10}, {"A": -50}), {"A": 0})
	la("dung 0 thi giu", m.ap_doi_ruot({"A": 10}, {"A": -10}), {"A": 0})


@ca("doi ruot: soat va ke ra dong khai lo so hop da ban")
def _soat():
	from vagabond import mua_vu as m

	dong = [{"ma_hop": "BASS00012", "so_hop": 40}]
	nhac = m.soat_doi_ruot(dong, [], {"BASS00012": 25})
	la("mot cau nhac", len(nhac), 1)
	dung("noi so da khai", "40" in nhac[0])
	dung("noi so da ban", "25" in nhac[0])
	la("khai trong so ban thi im", m.soat_doi_ruot(dong, [], {"BASS00012": 40}), [])
	la("khai it hon cung im", m.soat_doi_ruot(dong, [], {"BASS00012": 99}), [])


@ca("doi ruot: ap vao CA BA cho dem, khong sot cho nao")
def _ba_cho():
	s = _doc("mua_vu.py")

	tren = _than_ham(s, "def con_sau_khi_them(")
	khuc = tren[: tren.find("def cuon_ton_theo_ngay")]
	dung("chot chan ban lo co ap", "ap_doi_ruot(" in khuc)
	dung("ap len ca hai moc", khuc.count("ap_doi_ruot(") == 2)

	duoi = _than_ham(s, "def cuon_ton_theo_ngay(")
	khuc2 = duoi[: duoi.find("def ghep_theo_ngay")]
	dung("bang theo ngay co ap", "ap_doi_ruot(" in khuc2)
	dung("loc dung ngay do", "gom_doi_ruot(doi_ruot, ng)" in khuc2)

	ctl = _doc(os.path.join("vagabond", "doctype", "vagabond_mua_vu", "vagabond_mua_vu.py"))
	dung("bang san pham co ap", "ap_doi_ruot(" in ctl)
	dung("bang san pham goi phep gom", "gom_doi_ruot(" in ctl)


@ca("doi ruot: xoa theo TEN DONG chu khong theo noi dung")
def _xoa_theo_ten():
	s = _doc("mua_vu.py")
	than = _than_ham(s, "def xoa_doi_ruot(")
	khuc = than[: than.find("# ===================================================================")]
	dung("so theo x.name", "x.name != ten" in khuc)
	dung("khong so theo ma hop", "ma_hop ==" not in khuc)


@ca("doi ruot: chan khai thieu ca hai ben va khai cung mot ma")
def _chan_khai():
	s = _doc("mua_vu.py")
	than = _than_ham(s, "def them_doi_ruot(")
	khuc = than[: than.find("def xoa_doi_ruot")]
	dung("chan so hop 0", "Số hộp phải lớn hơn 0" in khuc)
	dung("chan thieu ca hai ben", "ít nhất một bên" in khuc)
	dung("chan bot va them cung ma", "cùng một mã" in khuc)


# ------------------------------------------ 4. Chip màn danh sách


@ca("chip HD: dem du bay trang thai va nam chip viec ton")
def _dem_chip():
	from vagabond.hop_dong import dem_chip

	rows = [
		{"trang_thai": "Dang thuc hien", "con_no": 500, "so_hd_chot": 1, "so_hd_nhap": 0,
		 "con_ngay": 3, "co_nguoi_ky": 1, "co_ban_chot": 1},
		{"trang_thai": "Da gui khach", "con_no": 0, "so_hd_chot": 0, "so_hd_nhap": 0,
		 "con_ngay": 30, "co_nguoi_ky": 0, "co_ban_chot": 0},
		{"trang_thai": "Hoan tat", "con_no": 900, "so_hd_chot": 0, "so_hd_nhap": 0,
		 "con_ngay": None, "co_nguoi_ky": 0, "co_ban_chot": 0},
	]
	d = dem_chip(rows)
	la("tong", d["tat_ca"], 3)
	la("dem theo trang thai", d["Dang thuc hien"], 1)
	# To da Hoan tat khong con la viec ton, du no con no va chua co nguoi ky.
	la("con no chi dem to con song", d["con_no"], 1)
	la("chua hoa don", d["chua_hoa_don"], 1)
	la("su kien sap toi", d["sap_toi"], 1)
	la("chua nguoi ky", d["chua_nguoi_ky"], 1)
	la("chua ban chot", d["chua_ban_chot"], 1)


@ca("chip HD: rong thi moi con so deu 0, khong vo")
def _dem_rong():
	from vagabond.hop_dong import dem_chip

	d = dem_chip([])
	la("tong 0", d["tat_ca"], 0)
	for k in ("con_no", "chua_hoa_don", "sap_toi", "chua_nguoi_ky", "chua_ban_chot"):
		la("%s bang 0" % k, d[k], 0)


@ca("chip HD: bang nhan trang thai nam o may chu, khong o man hinh")
def _nhan_o_may_chu():
	from vagabond.hop_dong import NHAN_TT

	la("du bay trang thai", len(NHAN_TT), 7)
	la("nhan tieng Viet", NHAN_TT["Dang thuong thao"], "Đang thương thảo")


# --------------------------------------------- 5. Màn hình


@ca("man HD: hai nut moi va hai man moi da co tren app")
def _man_hd():
	j = _js("11-khach-ca-hop-dong.js")
	dung("nut tao phieu", "id=\"hdThuTien\"" in j)
	dung("nut ghi so", "id=\"hdGhiSo\"" in j)
	dung("man tao phieu", "function scrHdThuTien(" in j)
	dung("man mot phieu", "function scrHdPhieu(" in j)
	dung("man ghi so", "function scrHdGhiSo(" in j)
	for cua in ("thu_hop_dong.tao_phieu", "thu_hop_dong.xuat_pdf",
			"thu_hop_dong.gui_email", "hop_dong_hoa_don.dong_tu_hop_dong",
			"hop_dong_hoa_don.ghi_so"):
		dung("goi dung cua ngo %s" % cua, cua in j)


@ca("man HD: hai nut an di khi hop dong chua chot con so")
def _an_nut():
	j = _js("11-khach-ca-hop-dong.js")
	dung("co phep kiem trang thai", "function hdThuDuoc(" in j)
	dung("bang trang thai o man khop voi may chu", "HD_TT_THU_DUOC" in j)
	dung("chua chot thi bay cau nhac", "chưa thu tiền và chưa xuất hoá đơn" in j)


@ca("man HD: hai hang chip loc, chip nao dem 0 thi tu an")
def _chip_man():
	j = _js("11-khach-ca-hop-dong.js")
	dung("ham ve chip", "function hdChip(" in j)
	dung("chip tren tung dong", "function hdChipDong(" in j)
	dung("chip viec ton tu an khi 0", "return Number(o[2] || 0) > 0;" in j)
	dung("toi da ba chip mot dong", "o.slice(0, 3)" in j)
	dung("khong con nut tha xuong cu", "Lọc trạng thái" not in j)


@ca("man mua vu: co tab Doi ruot va ba ham cua no")
def _tab_doi_ruot():
	j = _js("11-khach-ca-hop-dong.js")
	dung("co tab", "['dr', 'Đổi ruột']" in j)
	dung("ham ve tab", "function mvVeDoiRuot(" in j)
	dung("ham khai", "function mvKhaiDoiRuot(" in j)
	dung("ham xoa", "function mvXoaDoiRuot(" in j)
	dung("goi cua ngo them", "vagabond.mua_vu.them_doi_ruot" in j)
	dung("goi cua ngo xoa", "vagabond.mua_vu.xoa_doi_ruot" in j)
	dung("bay cau nhac khai lo", "nhac_doi_ruot" in j)


@ca("man mua vu: o bot ra chi bay banh CO trong hop do")
def _bot_dung_hop():
	j = _js("11-khach-ca-hop-dong.js")
	than = j[j.find("async function mvKhaiDoiRuot()"):]
	khuc = than[: than.find("async function mvXoaDoiRuot")]
	dung("loc theo dinh muc cua chinh hop do", "m.ma_hop === hop.value" in khuc)
	dung("chan khi chua khai dinh muc", "Chưa có định mức" in khuc)


@ca("cua ngo: cac ham mo ra ngoai cua hai tep moi deu da ghi danh")
def _cua_ngo():
	from vagabond.khung.kiem_thu.thu_cua_ngo import CUA_NGO

	la(
		"thu_hop_dong",
		sorted(CUA_NGO.get("thu_hop_dong.py") or []),
		["ds_phieu", "ghi_da_thu", "gui_email", "huy_phieu", "kiem_sepay",
		 "muc_goi_y", "tao_phieu", "xem_phieu", "xem_truoc", "xuat_pdf"],
	)
	la(
		"hop_dong_hoa_don",
		sorted(CUA_NGO.get("hop_dong_hoa_don.py") or []),
		["dong_tu_hop_dong", "ghi_so"],
	)
