"""Ca kiểm cho việc siết hồ sơ hoàn ứng không hoá đơn (v278).

Anh Việt 22/08/2026: luồng này rủi ro gian lận cao, kế toán trưởng yêu cầu
bắt buộc có chứng từ đính kèm và quy hoạch lại bản in PDF.

Ba khối được chốt ở đây:
  1. Chứng từ theo TỪNG DÒNG: loại chứng từ, tệp, nối phiếu nội bộ.
  2. Bản in dàn 4 ảnh một trang A4, mỗi ảnh ghi rõ thuộc khoản nào.
  3. Khuôn song ngữ và block chữ ký dùng chung cho mọi hồ sơ thanh toán.

Mọi ca chạy trên phép THUẦN: không cần Frappe thật, không cần site, không
cần mạng, không cần thư viện requests.
"""

import io
import json
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BEP = os.path.join(GOI, "public", "js", "bep")


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


def _doc_js(ten):
	with io.open(os.path.join(BEP, ten), encoding="utf-8") as f:
		return f.read()


# ------------------------------------------------- Khối 1: chứng từ từng dòng


@ca("hoan ung: dong hang co du ba truong chung tu moi")
def _dong_co_truong_moi():
	p = os.path.join(GOI, "vagabond", "doctype", "vagabond_ho_so_tt_dong",
	                 "vagabond_ho_so_tt_dong.json")
	with io.open(p, encoding="utf-8") as f:
		d = json.load(f)
	ten = {x["fieldname"]: x for x in d["fields"]}
	dung("co o loai chung tu", "loai_chung_tu" in ten)
	dung("co o tep", "tep" in ten)
	dung("co o phieu noi bo", "de_nghi_chi" in ten)
	# Loai chung tu tro vao DANH MUC chu khong phai o Select go tay: danh muc
	# ke toan tu them bot duoc, con Select thi phai deploy moi doi duoc.
	la("loai chung tu tro vao danh muc", ten["loai_chung_tu"]["options"],
	   "Vagabond Loai Chung Tu")
	la("phieu noi bo tro vao phieu that", ten["de_nghi_chi"]["options"],
	   "Vagabond De Nghi Chi")


@ca("hoan ung: dung chung MOT danh muc chung tu voi phieu noi bo")
def _mot_danh_muc():
	s = _doc("ho_so_tt.py")
	# Hai man khai hai bo ten khac nhau thi den luc doi chieu khong ai ghep
	# duoc. Nen ho_so_tt goi thang bo khoi tao cua de_nghi_chi.
	dung("goi bo khoi tao cua de_nghi_chi", "from vagabond.de_nghi_chi import dung_danh_muc_chung_tu" in s)
	dung("khong tu dung danh sach rieng", "DM_CT_MAC_DINH" not in s)


@ca("noi phieu noi bo: CHI nhan phieu da qua cua duyet")
def _chi_phieu_da_duyet():
	from vagabond import ho_so_tt as hs

	# Phieu con nhap ma noi duoc thi nguoi lap ho so tu viet phieu roi tu
	# noi, cua duyet thanh vo nghia.
	dung("nhan phieu Hoan tat", "Hoan tat" in hs.TT_PHIEU_NOI_BO)
	dung("nhan phieu Da chi", "Da chi" in hs.TT_PHIEU_NOI_BO)
	dung("KHONG nhan phieu Nhap", "Nhap" not in hs.TT_PHIEU_NOI_BO)
	dung("KHONG nhan phieu Cho duyet", "Cho duyet" not in hs.TT_PHIEU_NOI_BO)
	dung("KHONG nhan phieu Bi tra lai", "Bi tra lai" not in hs.TT_PHIEU_NOI_BO)


@ca("noi phieu noi bo: mot phieu KHONG duoc noi hai lan")
def _khong_noi_hai_lan():
	s = _doc("ho_so_tt.py")
	# Rui ro nang nhat cua ca tinh nang: noi mot phieu vao hai ho so la cong
	# ty tra tien hai lan cho cung mot khoan. Phai chan o CA BA cho.
	i = s.find("def ds_phieu_noi_bo(")
	dung("liet ke da loc phieu chua noi", '"ho_so_tt": ["in", ["", None]]' in s[i:i + 1800])
	j = s.find("def xem_phieu_noi_bo(")
	dung("luc xem con chan lan nua", "đã nối vào hồ sơ" in s[j:j + 2200])
	dung("luc ghi con khoa lai", "def _khoa_phieu_noi_bo(" in s)
	k = s.find("def _khoa_phieu_noi_bo(")
	dung("ghi de len phieu nguoi khac thi ghi nhat ky", "bi noi hai lan" in s[k:k + 1200])


@ca("tep chung tu: chi giu ma tep con that tren may chu")
def _tep_phai_that():
	s = _doc("ho_so_tt.py")
	i = s.find("def _tep_hop_le(")
	than = s[i:i + 1400]
	# Ma tep ma se lam ban in im lang bo qua: ke toan tuong co anh, mo ra
	# khong thay gi.
	dung("kiem tep con ton tai", 'frappe.db.exists("File", ma)' in than)
	dung("bo trung", "if not ma or ma in ra:" in than)
	# Nhan ca ba dang man hinh co the gui: chuoi, mang ma, mang {ma:...}
	dung("nhan dang chuoi", "isinstance(tep, str)" in than)
	dung("nhan dang mot cai le", "isinstance(tep, dict)" in than)


@ca("tep chung tu: luon dat che do RIENG TU")
def _tep_rieng_tu():
	s = _doc("ho_so_tt.py")
	i = s.find("def _gan_tep_ve_ho_so(")
	than = s[i:i + 1200]
	# Ho so thanh toan la giay to tien bac. De cong khai thi ai co duong dan
	# cung mo duoc.
	dung("dat is_private", '"is_private": 1' in than)
	dung("tro ve dung ho so", '"attached_to_doctype": "Vagabond Ho So TT"' in than)


@ca("dinh tep cho mot dong: STT dem tu 1 cho khop man hinh va ban in")
def _stt_dem_tu_mot():
	s = _doc("ho_so_tt.py")
	i = s.find("def dinh_tep_dong(")
	than = s[i:i + 2200]
	dung("chan so nho hon 1", "if i < 1 or i > len(doc.dong):" in than)
	dung("lay dung dong theo STT", "doc.dong[i - 1]" in than)
	# Dinh them KHONG duoc xoa tep da co cua dong do.
	dung("giu lai tep da co", "da_co + [m for m in ma_moi if m not in da_co]" in than)


# ------------------------------------------------ Khối 2: dàn trang PDF 2x2


@ca("ban in: bon anh mot trang A4, xep hai cot hai dong")
def _bon_anh_mot_trang():
	from vagabond import ho_so_tt as hs

	la("bon anh moi trang", hs.ANH_MOI_TRANG, 4)
	anh = [{"b64": "X", "kieu": "jpeg", "nhan": "Khoản %d" % i} for i in range(1, 10)]
	ra = hs.luoi_anh(anh)
	# 9 anh thi 4+4+1 = ba trang. Dem bang SO BANG chu khong dem so dau ngat
	# trang: tu 23/08/2026 trang DAU khong con dau ngat rieng nua, no nam
	# chung trang voi dong tieu de "CHUNG TU DINH KEM" de khoi ton mot mat
	# giay chi de in mot dong chu (anh Viet: "qua nhieu khoang trong gay phi
	# giay"). Nen dung ngat trang la hai, ma trang van la ba.
	la("chin anh ra ba trang", ra.count("<table"), 3)
	la("hai dau ngat giua ba trang", ra.count("page-break-before:always"), 2)
	la("chin o anh", ra.count("<img"), 9)
	# Trang cuoi le mot anh: cho no chiem CA HANG (colspan) thay vi de mot o
	# trong ben canh. Ban cu chen mot <td> rong, tuc mot nua mat giay khong in
	# gi ma anh thi be lai - dung cai lang phi anh Viet chi ra 23/08/2026.
	dung("anh le chiem ca hang", 'colspan="2"' in ra)
	dung("khong con o trong bo di", 'style="width:50%;border:none"' not in ra)


@ca("ban in: khong anh nao thi khong sinh trang rong")
def _khong_anh_thi_thoi():
	from vagabond import ho_so_tt as hs

	la("danh sach rong ra chuoi rong", hs.luoi_anh([]), "")
	la("None cung vay", hs.luoi_anh(None), "")


@ca("ban in: anh tu co vua khung, KHONG bi meo va khong tran vien")
def _anh_khong_meo():
	from vagabond import ho_so_tt as hs

	ra = hs.luoi_anh([{"b64": "X", "kieu": "jpeg", "nhan": "Khoản 1"}])
	dung("gioi han be ngang", "max-width:100%" in ra)
	dung("gioi han chieu cao", "max-height:" in ra)
	# object-fit contain moi la thu giu dung ti le. cover se cat mat mep anh,
	# ma mep chung tu thuong chinh la cho co con dau.
	dung("giu ti le bang contain", "object-fit:contain" in ra)
	dung("khong dung cover", "object-fit:cover" not in ra)


@ca("ban in: duoi moi anh ghi ro thuoc khoan chi nao")
def _nhan_ghi_nguon_goc():
	from vagabond import ho_so_tt as hs

	ra = hs.luoi_anh([{"b64": "X", "kieu": "jpeg", "nhan": "Khoản 3: bill điện · anh.jpg"}])
	dung("in ra nhan", "Khoản 3" in ra)
	dung("kem ten tep", "anh.jpg" in ra)
	# Nhan phai la text nho duoi anh, khong phai title an trong the.
	dung("nhan nam ngoai the img", ra.index("Khoản 3") > ra.index("<img"))


@ca("ban in: nhan cua moi anh mang STT dong, do la ly do no ton tai")
def _nhan_mang_stt():
	s = _doc("ho_so_tt.py")
	i = s.find("def _gom_anh_ho_so(")
	than = s[i:i + 2600]
	dung("dem dong tu 1", 'enumerate(d["dong"], 1)' in than)
	dung("nhan ghi Khoan + so", '"Khoản %d" % i' in than)
	dung("kem loai chung tu neu co", 'x.get("loai_chung_tu")' in than)
	dung("kem so phieu noi bo neu co", 'x.get("de_nghi_chi")' in than)
	# Anh trung chi lay mot lan, khong thi noi phieu xong la anh in hai lan.
	dung("chan anh trung", "if not ma or ma in da_lay:" in than)


@ca("ban in: tep khong phai anh van giu MA File that de con ghep PDF")
def _giu_ma_file_that():
	s = _doc("ho_so_tt.py")
	i = s.find("def _gom_anh_ho_so(")
	than = s[i:i + 2600]
	# Khuc ghep PDF o duoi doc noi dung bang ma File. Chi giu ten hien thi la
	# ghep hong ma khong ai biet vi sao.
	dung("bo qua mang theo ma file", '"file": ma' in than)
	j = s.find("pdf_rieng.append({")
	dung("ghep PDF dung ma file", 'f.get("file")' in s[j:j + 200])


@ca("ban in: khong con moi anh mot trang nhu truoc")
def _khong_con_mot_anh_mot_trang():
	s = _doc("ho_so_tt.py")
	i = s.find("def xuat_ho_so(")
	j = s.find("def _to_app_html(")
	than = s[i:j if j > i else i + 6000]
	dung("goi luoi anh", "luoi_anh(anh)" in than)
	dung("gom anh kem nhan", "_gom_anh_ho_so(d)" in than)
	# Vong lap cu tu doc tung tep roi tu dung the img ngay trong xuat_ho_so
	# phai bien mat, khong thi hai duong ve anh song song nhau.
	dung("bo vong lap dung the img tai cho", '<img src="data:image/' not in than)
	dung("bo bo dem tep cu", "da_lay = set()" not in than)


# ------------------------------- Khối 3: khuôn song ngữ và chữ ký dùng chung


@ca("khuon chuan: tieng Anh xuong dong rieng, in nghieng, KHONG gach cheo")
def _song_ngu_dung_quy_uoc():
	from vagabond import mau_chuan as mc

	ra = mc.sn("Số chứng từ:", "Voucher no.")
	dung("co tieng Viet", "Số chứng từ:" in ra)
	dung("co tieng Anh", "Voucher no." in ra)
	dung("tieng Anh xuong dong rieng", "display:block" in ra)
	dung("tieng Anh in nghieng", "font-style:italic" in ra)
	# Gach cheo la dung cai anh Viet bao bo (22/08/2026).
	dung("khong co gach cheo ngan cach", " / " not in ra)
	# Dau hai cham chi nam o dong tieng Viet, ban tieng Anh khong duoc mang
	# theo. In "Voucher no.:" la sai quy uoc.
	dung("tieng Anh khong keo theo dau hai cham", "Voucher no.:" not in ra)


@ca("khuon chuan: khong co tieng Anh thi khong sinh dong rong")
def _khong_en_thi_thoi():
	from vagabond import mau_chuan as mc

	ra = mc.sn("Ghi chú", "")
	dung("van co tieng Viet", "Ghi chú" in ra)
	dung("khong sinh khoi nghieng rong", "font-style:italic" not in ra)


@ca("khuon chuan: block chu ky dung ba chuc danh ke toan truong yeu cau")
def _ba_chu_ky():
	from vagabond import mau_chuan as mc

	vi = [x[0] for x in mc.CHU_KY_CHUAN]
	la("dung ba o", len(vi), 3)
	la("thu tu dung luong duyet", vi,
	   ["NGƯỜI ĐỀ NGHỊ", "KẾ TOÁN TRƯỞNG", "GIÁM ĐỐC"])
	ra = mc.khoi_chu_ky({"NGƯỜI ĐỀ NGHỊ": "Nguyễn Văn A"})
	dung("in ten da co", "Nguyễn Văn A" in ra)
	dung("co ban tieng Anh", "Chief Accountant" in ra)
	dung("co dong ky ghi ro ho ten", "Ký, ghi rõ họ tên" in ra)
	# Chuc danh chua co nguoi thi de TRONG cho nguoi ta ky tay, khong bia ten.
	la("ba o deu ra", ra.count("<td"), 3)


@ca("khuon chuan: phong co du dau tieng Viet dung truoc Arial")
def _phong_dejavu():
	from vagabond import mau_chuan as mc
	from vagabond.phong_chu import NGAN_XEP

	# Doi 31/08/2026: xau phong khong con viet tay o mau_chuan nua ma lay
	# tu MOT nguon duy nhat la phong_chu.NGAN_XEP, sau khi phat hien to
	# Bien ban ban giao tien mat khai Times New Roman va vo het dau.
	#
	# Rang buoc KHONG doi: phong co du dau tieng Viet phai dung TRUOC Arial.
	# Dat Arial len truoc la ra ban in mat dau, da gap mot lan.
	la("khuon chuan dung dung xau phong chung", mc.PHONG, NGAN_XEP)
	dung("Vagabond Sans dung dau", mc.PHONG.startswith("'Vagabond Sans'"))
	dung("van con DejaVu lam luoi do", "'DejaVu Sans'" in mc.PHONG)
	dung("hai phong do deu dung truoc Arial",
		mc.PHONG.index("DejaVu Sans") < mc.PHONG.index("Arial"))


@ca("to de nghi: da chuyen sang dung khuon chuan, khong tu dung nua")
def _to_de_nghi_dung_khuon():
	s = _doc("ho_so_tt.py")
	i = s.find("def _to_app_html(")
	j = s.find("def xuat_excel(")
	than = s[i:j if j > i else i + 9000]
	dung("nap khuon chuan", "from vagabond import mau_chuan as mc" in than)
	dung("dung dai logo chung", "mc.dai_logo()" in than)
	dung("dung block chu ky chung", "mc.khoi_chu_ky(" in than)
	dung("cot bang song ngu", 'mc.o_th("STT", "No.")' in than)
	# Ham tu dung o chu ky cu phai bo han, khong thi hai duong song song roi
	# sua mot duong quen duong kia.
	dung("bo ham chu ky cu", "def _o_ky(" not in s)



# ------------------------------------- Bẫy định dạng % làm chết Xuất bộ hồ sơ


@ca("khuon chuan: moi manh HTML deu CO dau % nen khong duoc ghep vao khuon %")
def _html_co_dau_phan_tram():
	from vagabond import mau_chuan as mc

	# Day la SU THAT gay ra loi 500 ngay 22/08/2026, chot lai de phien sau
	# doc ca kiem nay la hieu ngay vi sao khong duoc ghep thang.
	dung("dai_logo co dau %", "%" in mc.dai_logo())
	dung("khoi_chu_ky co dau %", "%" in mc.khoi_chu_ky())
	# Ghep thang vao mot khuon dinh dang la no ngay. Chung minh bang cach
	# thu that chu khong noi suong.
	no = False
	try:
		_ = ("<div>" + mc.dai_logo() + "%s</div>") % "x"
	except (ValueError, TypeError):
		no = True
	dung("ghep thang vao khuon thi NO that", no)


@ca("khuon chuan: an_phan_tram cuu duoc chuoi phai ghep thang")
def _an_phan_tram():
	from vagabond import mau_chuan as mc

	ra = ("<div>" + mc.an_phan_tram(mc.dai_logo()) + "%s</div>") % "x"
	dung("khong con no", ra.endswith("x</div>"))
	# Sau khi dinh dang xong thi dau % phai tro lai nguyen ven, khong duoc
	# de lai %% trong ban in.
	dung("dau % tro lai binh thuong", "width:45%;" in ra)
	dung("khong con %% sot lai", "%%" not in ra)


@ca("to de nghi: KHONG ghep ham mau_chuan vao giua khuon dinh dang")
def _to_de_nghi_khong_ghep_vao_khuon():
	s = _doc("ho_so_tt.py")
	i = s.find("def _to_app_html(")
	j = s.find("def xuat_excel(")
	than = s[i:j if j > i else i + 9000]
	# Cai da lam chet nut Xuat bo ho so: `+ mc.dai_logo()` nam trong mot
	# bieu thuc ket thuc bang `) % (`.
	for dong in than.split("\n"):
		# Bo qua dong chu thich: chinh doan giai thich cai bay nay cung nhac
		# ten ham, ma no khong phai ma chay.
		if dong.lstrip().startswith("#"):
			continue
		if "mc.dai_logo()" in dong:
			dung("dai_logo chi noi chuoi, khong nam trong khuon %",
			     "+ mc.dai_logo()" in dong)
	# Khuon cua tieu de va cua bang phai dinh dang XONG truoc khi noi.
	dung("tieu de dinh dang truoc", "dau_trang = (" in than)
	dung("bang dinh dang truoc", "bang = (" in than)
	dung("chu ky dung san truoc", "chu_ky = mc.khoi_chu_ky(" in than)
	# Cau lenh return cuoi chi con phep NOI chuoi, khong con phep %.
	k = than.rfind("\treturn (")
	dung("return cuoi khong con dinh dang %", ") % (" not in than[k:])


@ca("ban in: dong nhan phai nam CHUNG khoi chong ngat trang voi anh cua no")
def _():
	# Ca chan cho dung loi anh Viet bao ngay 23/08/2026. Trong ban xuat that
	# cua ho so APP.26.08.011: anh IMG_2710 nam o trang 6, dong nhan cua no
	# roi sang trang 7 mot minh. Ly do: anh va nhan la HAI khoi anh em, moi
	# khoi tu chong ngat trang ben trong no, nhung khong gi cam ngat trang
	# GIUA hai khoi.
	#
	# LUU Y cho ai sua ca kiem nay: ban dau em viet no bang cach so vi tri
	# chuoi, kieu "dong nhan phai dung sau the img". Sai. Da co y tra lai
	# dung loi cu de thu, va ca kiem VAN XANH, vi dong nhan van dung sau the
	# img ke ca khi no da bi day ra NGOAI khoi. Muon biet mot the co nam
	# trong mot the khac khong thi phai DEM DO SAU, khong co duong tat.
	from vagabond import ho_so_tt as t

	o = t._o_anh({"b64": "AAA", "kieu": "jpeg", "nhan": "Khoản 7 · bill điện"}, "90mm")
	dung("chỉ có ĐÚNG MỘT khối chống ngắt trang", o.count("page-break-inside:avoid") == 1)

	mo = o.index('<div style="page-break-inside:avoid">')
	sau, k, het = 0, mo, -1
	while k < len(o):
		if o.startswith("<div", k):
			sau += 1
			k += 4
		elif o.startswith("</div>", k):
			sau -= 1
			k += 6
			if sau == 0:
				het = k
				break
		else:
			k += 1
	dung("khối chống ngắt trang có đóng đúng chỗ", het > 0)

	vi_anh = o.index("<img")
	vi_nhan = o.index("Khoản 7")
	dung("thẻ ảnh nằm TRONG khối", mo < vi_anh < het)
	dung("dòng nhãn nằm TRONG khối, không bị đẩy ra ngoài", mo < vi_nhan < het)


@ca("ban in: KHONG dung display:table-cell cho div ben trong o bang")
def _():
	# Div mang display:table-cell ma khong nam trong mot table la cau truc
	# khong hop le; trinh duyet phai tu dung mot bang an bao quanh. WebKit
	# doi cu trong wkhtmltopdf tinh chieu cao bang an do theo co THAT cua
	# anh chu khong theo co da co, nen anh chup dien thoai 4032px bien thanh
	# mot khoi cao vo ly va day hang thu hai sang trang moi.
	from vagabond import ho_so_tt as t

	o = t._o_anh({"b64": "AAA", "kieu": "jpeg", "nhan": "x"}, "90mm")
	dung("không còn display:table-cell", "display:table-cell" not in o)
	dung("canh giữa dọc bằng line-height", "line-height:90mm" in o)


@ca("ban in: hai hang anh cong tieu de phai LOT vao vung in A4, con du rong rai")
def _():
	# Day la phep tinh da SAI o v281 va lam ca bo ho so tran giay.
	# Ban v281: o anh 104mm, nhan tu do, dem 6mm => mot hang 120mm, hai hang
	# 240mm, cong tieu de 14mm la 254mm => con 13mm tren 267mm. Sat qua.
	#
	# Bai hoc: bo cuc in KHONG duoc vua khit. Moi ban wkhtmltopdf tinh le
	# mot kieu, phai chua du rong rai thi moi may deu ra dung.
	from vagabond import ho_so_tt as t
	from vagabond.mau_in.le_in import CAO_TRONG_MM

	def mm(chuoi):
		return float(str(chuoi).replace("mm", ""))

	DEM_MM = 6.0        # padding 3mm tren va 3mm duoi cua moi o
	TIEU_DE_MM = 14.0   # khoi "CHUNG TU DINH KEM" o trang dau
	DU_TOI_THIEU = 25.0

	mot_hang = mm(t.CAO_O_ANH) + DEM_MM + mm(t.CAO_NHAN)
	can = mot_hang * 2 + TIEU_DE_MM
	du = CAO_TRONG_MM - can
	dung("hai hàng cộng tiêu đề lọt vùng in 267mm: cần %.0fmm" % can, du > 0)
	dung("còn dư ít nhất %.0fmm cho chắc, đang dư %.0fmm" % (DU_TOI_THIEU, du),
		du >= DU_TOI_THIEU)

	mot = mm(t.CAO_O_1_HANG) + DEM_MM + mm(t.CAO_NHAN)
	dung("trang một hàng cũng phải lọt vùng in", mot <= CAO_TRONG_MM)


@ca("le in: chi ap 15mm cho ban in kho A4/A5, tuyet doi chua mau Tem ra")
def _():
	from vagabond.mau_in.le_in import duoc_ap_le_chung, kho_giay_trong_mau

	TEM = "@page { size: 62mm 45mm; margin: 0; }"
	A4 = "<style>@page{size:A4 portrait;margin:15mm}</style>"

	dung("đọc đúng khổ giấy mẫu tự khai", kho_giay_trong_mau(TEM) == "62mm 45mm")
	dung("mẫu A4 thì được áp", duoc_ap_le_chung("Vagabond - Phiếu nhập kho", "Purchase Receipt", A4))
	dung("mẫu A5 thì được áp", duoc_ap_le_chung("Vagabond - Phiếu nhỏ", "X", "@page{size:A5}"))
	dung("mẫu không khai gì thì được áp", duoc_ap_le_chung("Vagabond - Đơn đặt hàng", "Purchase Order", ""))
	dung("Tem HACCP bị chừa ra", not duoc_ap_le_chung("Vagabond - Tem HACCP", "Batch", TEM))
	dung("Tem nhãn hàng bị chừa ra dù không đọc được HTML",
		not duoc_ap_le_chung("Vagabond - Tem nhan hang", "Batch", ""))
	dung("mẫu khổ tem mà tên không có chữ Tem vẫn bị chừa ra",
		not duoc_ap_le_chung("Vagabond - Nhan lo hang", "Batch", TEM))
