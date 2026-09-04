"""Ca kiểm cho MÀN DANH SÁCH vận đơn: tab trạng thái, ô tìm, chip dấu hiệu.

Anh Việt 04/09/2026, lấy mẫu màn đơn hàng bên Pancake: *"Màn đó hiện tại anh
cần chia ra các tab trạng thái... nguyên lý là tránh rối danh sách, các đơn tự
chuyển theo trạng thái được gắn để dễ thao tác."* Anh chốt sáu tab: Cần phân
công, Đang giao, Đã giao, Không giao được, Đã huỷ, Tất cả.

Trước bản này màn chỉ có ba hàng chip, và hàng đầu trộn chung hai loại khác
hẳn nhau: chip TRẠNG THÁI loại trừ lẫn nhau (chờ giao, đã giao, huỷ) và chip
DẤU HIỆU cắt ngang mọi trạng thái (có COD, thiếu thẻ giờ). Người dùng phải tự
nhớ cái nào loại trừ cái nào.

Hai bẫy phải chặn bằng ca kiểm, vì cả hai đều IM LẶNG khi hỏng:

  * Gõ ô tìm mà số trên tab không tính lại thì người ta gõ đúng tên khách, ra
    màn trống, và kết luận là mất đơn - trong khi đơn nằm ở tab bên cạnh.
  * Ô tìm vẽ lại cả màn sau mỗi nhịp gõ, mà màn này mỗi lần vẽ là gọi hai lần
    API danh sách. Gõ một tên khách mất mười nhịp là mười lần kéo cả ngày đơn
    về. Không ai thấy lỗi, chỉ thấy app chậm.

Mọi ca chạy trên văn bản tệp: không cần Frappe, không cần site, không cần mạng.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")


def _js(ten):
	with io.open(os.path.join(BEP, ten), encoding="utf-8") as f:
		return f.read()


VD = _js("12-van-don.js")
NEN = _js("00-nen.js")
BG = _js("22-bao-gia.js")


def _than(ma, tu, den):
	i = ma.find(tu)
	j = ma.find(den, i + 1) if i >= 0 else -1
	return ma[i:j] if i >= 0 and j > i else ""


# ----------------------------------------------------------- Sáu tab trạng thái


@ca("man van don: du sau tab anh Viet chot, khong thieu khong du")
def _du_sau_tab():
	than = _than(VD, "function vdNhomTab()", "function vdTabTim")
	dung("co ham sinh tab", bool(than))
	for k in ("cho_gan", "dang_giao", "da_giao", "hong", "huy", "tat_ca"):
		dung("co tab %s" % k, "k: '%s'" % k in than)
	la("dung sau tab, khong hon", than.count("k: '"), 6)
	# Tab phai deo mau rieng, khong thi sau tab xanh y het nhau nhu vu ba hang
	# chip ngay 31/08/2026.
	la("moi tab mot mau", than.count("mau: '"), 6)


@ca("man van don: don cho giao DA CO shipper nam o tab Dang giao")
def _cho_giao_co_shipper():
	than = _than(VD, "function vdNhomTab()", "function vdTabTim")
	# Tab dau chi lay don CHUA ai nhan. Neu bo dieu kien !r.shipper thi hang
	# viec phai lam cua Sales phinh ra ca nhung don da giao cho nguoi roi.
	dung("tab dau doi chua co shipper", "r.trang_thai === 'Chờ giao' && !r.shipper" in than)
	dung("tab Dang giao om luon cho giao da co shipper",
		"r.trang_thai === 'Chờ giao' && !!r.shipper" in than)


@ca("man van don: khong trang thai nao bi bo roi ra ngoai het thay tab")
def _khong_bo_sot_trang_thai():
	than = _than(VD, "function vdNhomTab()", "function vdTabTim")
	# VD_TT_MAU la danh sach trang thai that cua doctype Van Don. Them mot
	# trang thai moi ma quen them tab thi don mang trang thai do bien mat
	# khoi moi tab tru "Tat ca" - va khong mot cau bao nao keu len.
	i = VD.find("var VD_TT_MAU = {")
	bang = VD[i:VD.find("}", i)]
	tt = [x for x in bang.split("'")[1::4] if x.strip()]
	dung("doc duoc bang mau trang thai", len(tt) >= 5)
	for x in tt:
		dung("trang thai %r co tab nhan no" % x, ("'%s'" % x) in than)


@ca("man van don: khoa tab la thi ve Tat ca, khong ve tab dau")
def _khoa_la_ve_tat_ca():
	than = _than(VD, "function vdTabTim(k)", "function vdTabMacDinh")
	# Ve tab dau la giau bot don ma khong noi gi. Tha thay du con hon tuong
	# la mat don.
	dung("tra ve phan tu cuoi", "return A[A.length - 1];" in than)


@ca("man van don: mo ra dung ngay tab con viec phai lam")
def _tab_mac_dinh():
	than = _than(VD, "function vdTabMacDinh(ds)", "/* Tab RỖNG")
	dung("uu tien can phan cong truoc", "'cho_gan', 'dang_giao', 'da_giao'" in than)
	# Shipper khong bao gio thay don chua phan cong (may chu da loc), nen mo
	# ra dung o tab do la mo ra thay man trong.
	dung("shipper bo qua tab can phan cong", "'dang_giao', 'da_giao'" in than)
	dung("khong con tab nao co don thi ve Tat ca", "return 'tat_ca';" in than)


@ca("man van don: tab rong VAN HIEN, khac han chip rong")
def _tab_rong_van_hien():
	than = _than(VD, "function vdTabHtml(ds)", "/* ---------- Ô tìm nhanh")
	dung("khong co nhanh an tab rong", "return '';" not in than)
	dung("tab nao cung deo so", "ds.filter(t.loc).length" in than)


# --------------------------------------------------------------------- Ô tìm


@ca("man van don: o tim cat ngang moi tab, so tren tab tinh lai theo ket qua")
def _o_tim_cat_ngang():
	than = _than(VD, "async function scrVanDon()", "async function scrVdCod")
	i_tim = than.find("var dsTim = vdLocTim(dsTho);")
	i_tab = than.find("html += vdTabHtml(dsTim);")
	i_loc = than.find("var dsTab = dsTim.filter(vdTabTim(vdTab).loc);")
	dung("co loc theo tu khoa", i_tim > 0)
	dung("hang tab dem tren tap DA TIM", i_tab > i_tim)
	dung("vao tab sau khi da tim", i_loc > i_tab)


@ca("man van don: go ra rong thi chi thang sang tab dang giu don do")
def _goi_y_nhay_tab():
	than = _than(VD, "async function scrVanDon()", "async function scrVdCod")
	dung("co tim tab khac con don", "vdNhomTab().filter(function (t) {" in than)
	dung("bo qua chinh tab dang dung va tab Tat ca",
		"t.k !== vdTab && t.k !== 'tat_ca'" in than)
	dung("chip goi y bam duoc sang tab do", "posChipNut('data-vdtab=\"' + t.k + '\"'" in than)


@ca("man van don: o tim doc du moi cho nguoi ta hay go")
def _o_tim_du_truong():
	than = _than(VD, "var VD_TIM_O = [", "function vdLocTim")
	for o in ("ma_don", "khach", "sdt", "sdt_nhan", "dia_chi", "phuong",
		"chuyen", "chung_tu_goc", "mon_tat", "mon_chinh"):
		dung("tim duoc theo %s" % o, "'%s'" % o in than)
	# Ten shipper tren van don la dia chi email, nguoi ta go TEN nguoi.
	dung("tim duoc ca ten shipper", "vdTen(r.shipper)" in than)


@ca("phep bo dau chi con MOT cho tinh trong ca app")
def _bo_dau_mot_cho():
	# Ghi chu cua chinh no noi "dung cho MOI o tim trong app", ma no lai nam
	# trong man Bao gia. Man Van don can dung thi phai chuyen xuong tep nen.
	dung("nam o tep nen", "function vgbChuan(s)" in NEN and "function vgbKhop(kho, tim)" in NEN)
	dung("khong con ban chep trong man Bao gia", "function vgbChuan(s)" not in BG)
	dung("man Van don goi ham chung", "vgbKhop(vdKhoTim(r), q)" in VD)


# ----------------------------------------------- Không gọi lại máy chủ khi gõ


@ca("man van don: doi cach nhin thi ve suong, KHONG goi lai may chu")
def _ve_suong():
	dung("co co ve suong", "var vdDs = null, vdDsNgay = null, vdVeSuong = 0;" in VD)
	than = _than(VD, "async function scrVanDon()", "async function scrVdCod")
	dung("dung lai du lieu dang cam",
		"if (vdVeSuong && vdDs && vdDsNgay === vdNgay) {" in than)
	# Ngay khac thi PHAI tai lai, khong duoc lay du lieu ngay cu ra ve.
	dung("chan lay nham du lieu ngay khac", "vdDsNgay === vdNgay" in than)
	dung("tai xong thi nho lai", "vdDs = ds; vdDsNgay = vdNgay;" in than)
	# Bon viec doi cach nhin: go tim, doi tab, doi chip, doi kieu sap xep.
	la("du bon cho dat co", VD.count("vdVeSuong = 1;"), 4)


@ca("man van don: viec doi DU LIEU khong duoc ve suong")
def _doi_du_lieu_phai_tai_lai():
	than = _than(VD, "async function scrVanDon()", "async function scrVdCod")
	for viec, moc in (
		("dong bo Pancake", "dong_bo_pancake"),
		("gop chuyen", "gop_chuyen"),
	):
		i = than.find(moc)
		dung("co duong %s" % viec, i > 0)
		# Doan ngay sau moi viec do khong duoc dat co ve suong.
		dung("%s khong ve suong" % viec, "vdVeSuong = 1" not in than[i:i + 400])


@ca("man van don: o tim tra con tro ve dung cho sau khi ve lai")
def _o_tim_giu_con_tro():
	than = _than(VD, "var oq = document.getElementById('vdQ');", "var btq =")
	dung("co cho mot nhip roi moi ve", "}, 220);" in than)
	dung("focus lai o tim", "i2.focus();" in than)
	dung("dat lai vi tri con tro", "i2.setSelectionRange(vt, vt);" in than)


# ------------------------------------------------ Chip dấu hiệu, cắt ngang tab


@ca("hang chip khong con chip trang thai nao nua")
def _chip_khong_con_trang_thai():
	than = _than(VD, "function vdNhomDau()", "function vdNhomKenh(ds)")
	dung("co ham chip dau hieu", bool(than))
	# Trang thai da len tab. De lai duoi chip la hai cho cung lam mot viec,
	# va nguoi dung phai tu doan cai nao loai tru cai nao. Soi theo KHOA chip:
	# khoa cua chip dau hieu deu bat dau bang @, khong khoa nao la ten mot
	# trang thai. (Dieu kien trang thai nam BEN TRONG mot chip dau hieu thi
	# van duoc - chip "COD chua doi soat" chi co nghia voi don da giao.)
	for x in ("Chờ giao", "Đang giao", "Đã giao", "Không giao được", "Huỷ"):
		dung("khong con chip trang thai %s" % x, ("k: '%s'" % x) not in than)
	for d in than.split("{ k: '")[1:]:
		k = d.split("'")[0]
		dung("khoa chip %r la dau hieu chu khong phai trang thai" % k,
			k == "" or k.startswith("@"))
	dung("khong con ham chip trang thai cu", "function vdNhomTrangThai" not in VD)


@ca("hang chip giu du cac dau hieu ve tien va hang lanh")
def _chip_dau_hieu():
	than = _than(VD, "function vdNhomDau()", "function vdNhomKenh(ds)")
	for k in ("@cod_chua", "@cod", "@goc_huy", "@tre", "@chua_gio",
		"@goi", "@anh", "@dc", "@lanh"):
		dung("con chip %s" % k, "k: '%s'" % k in than)
	# COD da thu ma chua doi soat la tien dang nam ngoai tiem, phai loc ra
	# duoc bang mot cai bam.
	dung("chip COD chua doi soat soi dung dieu kien",
		"r.trang_thai === 'Đã giao' && Number(r.tien_thu_ho || 0) > 0 && !r.da_doi_soat" in than)


@ca("khoi tong bay them so COD da thu ma chua doi soat")
def _khoi_tong_cod_chua():
	than = _than(VD, "function vdKhoiTong(ds, nhan)", "function vdChipsHtml")
	dung("co cong rieng phan chua doi soat", "codChua +=" in than)
	dung("chi cong don DA GIAO va chua doi soat", "if (!r.da_doi_soat) codChua" in than)
	dung("khong co so thi khong bay dong do", "(codChua ?" in than)


@ca("nut Bo het bo loc khong dung toi kieu sap xep")
def _nut_xoa_loc():
	than = _than(VD, "function vdCoLoc()", "function vdLocRa(ds)")
	dung("sap xep khong tinh la loc", "vdSap" not in than)
	i = VD.find("if (bx) bx.onclick")
	dung("nut xoa co that", i > 0)
	dung("nut xoa khong keo sap xep ve mac dinh", "vdSap = ''" not in VD[i:i + 220])


@ca("bam Gop chuyen thi nhay ve dung tab Can phan cong")
def _gop_chuyen_nhay_tab():
	i = VD.find("var gp = document.getElementById('vdGop');")
	dung("co nut gop chuyen", i > 0)
	# Dung o tab Da giao ma bam Gop chuyen thi bam vao don nao cung bi tu choi.
	dung("nhay ve tab can phan cong", "vdTab = 'cho_gan';" in VD[i:i + 400])


@ca("quy uoc trinh bay: phan viet moi khong co dau gach dai")
def _khong_gach_dai():
	than = _than(VD, "/* ================= TAB TRẠNG THÁI", "function vdNhomKenh(ds)")
	dung("khong em dash", "—" not in than)
	dung("khong en dash", "–" not in than)


@ca("man van don: khong dung o select, dung chip theo luat repo")
def _khong_select():
	than = _than(VD, "/* ================= TAB TRẠNG THÁI", "function vdNhomKenh(ds)")
	dung("khong co the select", "<select" not in than)
	dung("nut sap xep mo bang chon kieu chip", "sheet('Sắp xếp danh sách theo'" in VD)
