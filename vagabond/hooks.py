# Ham dung duoc trong MOI mau in Jinja cua tiem. Khai o day thi mau in goi
# thang code39_img(...) chu khong phai viet duong dan module dai loong ngoong.
#
# Vi sao ma vach phai la HAM chu khong phai font: xem vagabond/ma_vach.py.
# Dia chi that cho tung man cua app Bep, de F5 dung nguyen man do thay vi
# vang ve trang chu. Xem vagabond/duong_app.py de biet vi sao liet ke tung
# duong chu khong bat tat bang <path:...>.
from vagabond.duong_app import luat_dinh_tuyen

website_route_rules = luat_dinh_tuyen()

# Moi subdomain mot viec: app / erp / order. Xem vagabond/ten_mien.py, doc
# ba dieu can than o dau tep truoc khi sua.
def _dinh_tuyen_ten_mien(context=None):
	from vagabond.ten_mien import ap_luat

	ap_luat()
	return context


jinja = {
	"methods": [
		"vagabond.ma_vach.code39_img",
		"vagabond.ma_vach.code39_svg",
	]
}

app_name = "vagabond"
app_title = "Vagabond"
app_publisher = "Cong ty TNHH Patisserie Vagabond"
app_description = "Cong dat banh online: noi Frappe voi Pancake POS, Goong va Ahamove"
app_email = "thevagabondbakery@gmail.com"
app_license = "MIT"

# Cac endpoint deu nam o vagabond/api.py va da co @frappe.whitelist,
# khong can khai bao them o day.

# Ban quan tri tren may tinh: bo nut Xoa khoi cac man chung tu va thay bang
# nut Huy phieu. Chan that nam o hook on_trash duoi day, file js chi lo phan
# nguoi dung nhin thay.
app_include_js = "/assets/vagabond/js/vgb_khoa_xoa.js"

# Danh sach Cong thuc tren Desk: chip trang thai co kem SO PHIEN BAN, vi
# cot ten dang bi cat mat duoi so (ban Khai xin 25/08/2026). Doc ly do
# day du o dau tep bom_list.js.
#
# `doctype_list_js` chi nap dung mot man danh sach do, khong phai hook
# rong tren "*". Dat hep nhu the la co y: quy tac 6 cua repo.
# Man Hoa don mua: bo nut "Lay mat hang tu" tren nhung to sinh tu hoa don
# dien tu. Nut do chep de dong hang cua phieu nhap len dong hang cua hoa don,
# lam mat cac dong khong di qua kho (phi dich vu, phi giao hang). Xem dau tep
# purchase_invoice.js de biet ca that cua Kamereo 271846.
#
# Dat HEP tren dung mot doctype, khong phai hook rong tren "*" (quy tac 6).
doctype_js = {
	"Purchase Invoice": "public/js/purchase_invoice.js",
	# An o don gia khoi man phieu nhap voi nguoi thuan lam kho, va noi ro gia
	# von cuoi cung lay theo hoa don (anh Viet hoi 31/08/2026: "PNK anh tuong
	# chi quan so luong, HSD?"). Xem dau tep purchase_receipt.js.
	"Purchase Receipt": "public/js/purchase_receipt.js",
}

# Nut "Dong bo M-Invoice" tren ba man danh sach (anh Viet xin 31/08/2026).
# Cung MOT tep dung chung cho ca ba, xem dau tep minvoice_list.js.
doctype_list_js = {
	"BOM": "public/js/bom_list.js",
	"Purchase Invoice": "public/js/minvoice_list.js",
	"Sales Invoice": "public/js/minvoice_list.js",
	"MInvoice Invoice": "public/js/minvoice_list.js",
}

# Kiem banh ngay: 5 phut keo don Pancake mot lan de cot "da dat" va
# "phat sinh" tu chay, sales khoi dem tay.
scheduler_events = {
	"cron": {
		# Moi phut: keo don Pancake ve cho cac mua vu DANG BAN. Anh Viet
		# 18/08/2026: "de kip thoi bat don moi (va nhung don bi chinh sua,
		# them san pham...) cung kip thoi day ve de khong bi lech so".
		# Mua vu la hang co han muc cung, mot don ve muon la mot lan sales
		# hua nham voi khach, nen nhip nay dat sat hon 5 phut cua kiem banh
		# theo ngay. Ham tu bo qua khi khong co mua nao dang ban.
		"* * * * *": ["vagabond.mua_vu.dong_bo_tu_dong"],
		# Khach sua don ben Pancake (dia chi, mon, tien) luc nao cung duoc,
		# nen ca kiem banh lan van don phai tu bam theo, khong doi ai bam nut.
		"*/5 * * * *": [
			"vagabond.kiem_banh.dong_bo_tu_dong",
			"vagabond.van_don.dong_bo_tu_dong",
			# Chuoi cuoi ngay go cua o day. Ham tu kiem gio va moi ngay chi
			# lam mot lan, nen de chung nhip 5 phut la du.
			"vagabond.ban_hang.tu_ghi_so_cuoi_ngay",
			# Trang thai gui email tren don mua hang va phieu yeu cau vat tu:
			# chi doi sang "Da gui" khi hang doi that su bao Sent. Nhip 5 phut
			# la du sat, vi bo lap lich cua Frappe cung nhat thu theo nhip do.
			"vagabond.trang_thai_thu.soat_tu_dong",
		],
		"*/30 * * * *": [
			"vagabond.ban_hang.dong_bo_doanh_so_tu_dong",
			# Don khach HUY ben Pancake: tien khach van nam o minh nen khong
			# duoc cho ai bam nut. Truoc 31/08/2026 mo dun nay khong co nhip
			# tu dong nao, va nut bam tay o chan man lai chua bao gio bam
			# duoc, nen lan dong bo cuoi cung la 21/08 - muoi ngay khong mot
			# don huy nao ve he.
			"vagabond.don_huy.dong_bo_tu_dong",
		],
		# KHONG CON NHIP 06:00 CHO TANG QUA VIP.
		#
		# Truoc 26/08/2026 o day chay `tang_qua.quet_dem_tu_dong`: moi sang
		# ra phieu chua ai lien he roi nhac nguoi phu trach. Go bo cung lan
		# tat giao viec tu dong, vi nhip do nhac bang cach goi
		# `giao_viec.giao`, tuc la no khong chi ban mot cai chuong ma con de
		# ra phan cong cho ca bo phan. Xem ghi chu o muc doc_events cua
		# "Vagabond Tang Qua VIP".
		# Keo hoa don M-Invoice, ban trong ma nguon (truoc 20/08/2026 nam
		# trong Server Script tren site va da sot hoa don dau vao tu 14/08,
		# xem dau tep minvoice_dong_bo.py). Cung nhip 15 phut voi kich ban
		# cu; hai duong idempotent nen chay song song mot thoi gian de doi
		# chieu roi tat kich ban cu.
		"7,22,37,52 * * * *": ["vagabond.minvoice_dong_bo.dong_bo_tu_dong"],
		# BUOC HAI, va no da tung bi quen mat (them 31/08/2026).
		#
		# Keo ve moi la nua viec: hoa don nam trong bang MInvoice Invoice
		# van chua phai la chung tu trong so. Buoc bien no thanh Hoa don
		# mua hang truoc day do mot Server Script tren site chay moi 5 phut.
		# Ngay 26/08/2026 luc 16h28 Server Script do bi tat de nhuong cho
		# ban trong ma nguon, nhung ban trong ma nguon KHONG AI KHAI VAO DAY.
		#
		# Ket qua: suot nam ngay buoc keo van chay deu moi 15 phut nen nhin
		# vao dau cung thay "dang chay", trong khi 69 to hoa don mua dung
		# ngoai so. Chi lo ra khi anh Viet ngoi so tay mot to cua Tac Khi
		# Viet tren trang m-invoice voi man Hoa don mua hang.
		#
		# Dat LECH 5 phut sau nhip keo, de to vua keo ve la co luot dung ngay.
		"12,27,42,57 * * * *": ["vagabond.minvoice_chung_tu.chay_tu_dong"],
		# BO NHIP KEO PDF (21/08/2026). Duong tai ban the hien cua API
		# qlhd tra 400 o moi bien the ten tep da thu, va tai lieu cong khai
		# cua M-Invoice khong noi dinh dang dung. Anh Viet chot: *"Phan ban
		# the hien hoa don chac thoi khoi keo api... Em cho nut tai len luc
		# lam APP la duoc roi"*. Nut do nam o man Ho so APP, xem
		# ho_so_tt.dinh_tep. Ham keo_pdf_thieu giu lai trong ma nguon de
		# ngay nao co duong dung thi bat lai bang mot dong.
		# 1h10 dem: quet lui 30 ngay de lanh not "vo ruot" va vet sot cu.
		"10 1 * * *": ["vagabond.minvoice_dong_bo.tu_lanh_hang_dem"],
		# 8h25 sang: nhip dung chung tu ma tac thi gui thu cho ke toan.
		# Lop con thieu cua vu 26/08: khong lop nao keu len, vi khong lop
		# nao co viec keu. Xem canh_bao_tac_nhip.
		"25 8 * * *": ["vagabond.minvoice_chung_tu.canh_bao_tac_nhip"],
		# 01:40 moi dem: tinh lai bang Nguyen lieu thay the. Ton kho, gia von
		# va so cong thuc doi hang ngay ma khong ai mo lai cap thay the de luu,
		# nen khong co nhip nay thi cac o do dung im o con so ngay khai.
		"40 1 * * *": ["vagabond.nvl_thay_the.quet_tu_dong"],
		# Moi 15 phut: duong thu di co dang hong khong. Tu 16/08/2026 ca tiem
		# khong gui duoc mot email nao suot nhieu ngay, va minh chi biet vi
		# Uyen di hoi. Khong co nhip nay thi lan sau cung the.
		"*/15 * * * *": ["vagabond.gui_thu.canh_bao_email_loi"],
		# Moi gio: don da ghi so ma chua co hoa don dien tu thi xuat bu. Tu
		# 03/09/2026 di cung duong kich ban m-invoice voi chuoi cuoi ngay,
		# cung mot cong tac, cung mot khoa. Xem xuat_hddt_con_thieu_tu_dong.
		"15 * * * *": ["vagabond.ban_hang.xuat_hddt_con_thieu_tu_dong"],
		# Moi gio: doi soat lenh chi hoan tien voi sao ke SePay.
		"35 * * * *": ["vagabond.hoan_tien.doi_soat_tu_dong"],
		# Doi soat phieu thanh toan noi bo voi dong tien ra (OCB, MB...).
		# Lech 20 phut so voi nhip hoan tien de hai nhip khong cung luc quet
		# ca bang Bank Transaction.
		"55 * * * *": ["vagabond.de_nghi_chi.doi_soat_tu_dong"],
		# Gio chay chuoi cuoi ngay khai trong Vagabond Settings, sua duoc
		# ngay tren app (mac dinh 23:00, ca ba buoc xong truoc 23h30). Chi
		# Dung so xuat hoa don sat 24h, lo nghen mang la to hoa don lot
		# sang ngay hom sau, sai luat ke toan (anh Viet 12/08/2026).
		# 23h55: chuoi cuoi ngay va cac nhip vet da xong. Con don nao chua ghi
		# so duoc thi gui thu bao ngay trong dem. Truoc 13/08/2026 loi chi rot
		# vao Error Log ma khong ai mo, nen 149 don nam nhap nua thang (114
		# trieu) khong ai hay.
		# 23h55 con mot chuong nua: to DA GHI SO ma CHUA CO hoa don dien tu.
		# Vu 01-02/09/2026: chuoi bi cat o 300 giay giua luc phat hanh, 95 to
		# nam lai hai ngay, khong lop nao keu vi chuong don treo chi dem don
		# con nhap. Xem canh_bao_hddt_sot.
		"55 23 * * *": [
			"vagabond.ban_hang.canh_bao_don_treo",
			"vagabond.ban_hang.canh_bao_hddt_sot",
		],
		# 2h sang: ra don bi lap hai hoa don, co thi gui thu bao.
		"0 2 * * *": ["vagabond.ban_hang.ra_trung_hang_dem"],
		# 2h20 sang: don tep TREO cua cong tai tep dinh kem. Tep treo la tep
		# nguoi lap da chon len nhung roi bo man giua chung, khong buoc vao
		# chung tu nao. Khong don thi moi lan ai do mo man roi thoat la mot
		# tam anh nam lai vinh vien.
		#
		# Nhip nay CHI dung tep mang dau rieng cua cong do, va chi khi tra
		# loi duoc ca ba cau hoi cua bai hoc 24/08/2026. Xem tep_dinh_kem.py
		# va khung/kiem_thu/thu_don_rac_tep.py.
		"20 2 * * *": ["vagabond.tep_dinh_kem.don_rac"],
		# Xet lai hang thanh vien theo chi tieu ky. Chay sau nua dem, truoc
		# gio mo cua, de sang ra quay da thay dung hang cua khach.
		"30 4 * * *": ["vagabond.khach_hang.xet_lai_tu_dong"],
		# 5h sang: dot diem qua han theo chu ky khai trong Cai dat.
		#
		# Chay SAU xet lai hang: xet hang doc chi tieu tu hoa don chu khong
		# doc so diem, nen thu tu khong doi ket qua - nhung neu sau nay ai
		# gan hai viec vao nhau thi thu tu dung la xet hang truoc, dot diem
		# sau. Ham tu kiem cau hinh va thoat ngay khi dang Tat (mac dinh).
		"0 5 * * *": [
			"vagabond.diem_han.het_han_tu_dong",
			# 5h sang bep vao ca: rung dien thoai bep truong bao ke hoach
			# hom nay da san. Ham tu thoat khi ngay do chua co phieu.
			"vagabond.ke_hoach_sx.nhac_bep_sang",
		],
		# 0h00: lap san phieu ke hoach san xuat cho ngay vua sang, gom moi
		# phieu YCSX cac ben da gui. Phieu de dang NHAP, 5h sang bep doc roi
		# tu bam Chot. Ham tu bo qua khi ngay do da co phieu, nen chay lai
		# khong sinh phieu thu hai.
		"0 0 * * *": ["vagabond.ke_hoach_sx.tu_lap_nua_dem"],
		# 3h sang: xoa anh giao hang cua van don qua 30 ngay cho nhe he thong
		"0 3 * * *": [
			"vagabond.van_don.don_dep_anh_giao",
			"vagabond.dang_nhap.don_dep_phien",
			# Nhat ky dong bo la vet ky thuat, khong phai chung tu ke toan,
			# nen don sau 90 ngay. Cac dong dang cho nguoi xem thi giu lai.
			"vagabond.nhat_ky_dong_bo.don_cu",
			# PDF ban the hien hoa don qua 60 ngay: xoa cho nhe he thong.
			# La ban cache, ban goc van nam ben M-Invoice (anh Viet duyet
			# 20/08/2026).
			"vagabond.minvoice_tep.don_dep_pdf",
		],
	},
}

# Mot don Pancake chi duoc mot hoa don ban hang. Kiem o day de bat duoc moi
# duong tao hoa don, khong rieng man Doanh thu Sales.
doc_events = {
	# Khoa xoa vinh vien chung tu, dat o "*" chu khong liet ke tung doctype:
	# liet ke thi hom nao them mot loai chung tu moi la lai quen, ma quen o
	# day thi khong ai biet cho den luc mat chung tu. Ham tu kiem doctype va
	# thoat ngay neu khong phai chung tu, xem vagabond/chung_tu.py.
	"*": {
		"on_trash": "vagabond.chung_tu.chan_xoa",
		# Huy mem ma khong chan ghi so thi chi la mot cai nhan: phieu da huy
		# van submit duoc, van vao so cai, van phat hanh hoa don dien tu.
		"before_submit": [
			"vagabond.chung_tu.chan_ghi_so",
			"vagabond.chung_tu.chan_ngay_khoa",
		],
		# Khoa so theo ngay: khong ghi so, khong huy, khong sua duoc chung tu
		# cua ky da chot. Chi bat ba cua nay chu khong bat before_save: ban
		# nhap cu sua lai khong dung den so sach, ma bat before_save la dinh
		# ca nhung lan he thong tu cap nhat hoa don cu.
		"before_cancel": "vagabond.chung_tu.chan_ngay_khoa",
		# before_update_after_submit chu KHONG phai on_update_after_submit:
		# cai sau chay SAU khi Frappe da ghi xuong co so du lieu roi, nem loi
		# luc do van kip rollback ca yeu cau nhung cho nao boc try/except roi
		# tu commit thi ban sua lau van nam lai ma may van bao la da chan.
		"before_update_after_submit": "vagabond.chung_tu.chan_ngay_khoa",
		# MOT O EMAIL GO SAI KHONG DUOC LAM ROT CHUNG TU.
		#
		# Ngay 16/08/2026 mot khach go "...@gmail" thieu ".com", Frappe nem
		# InvalidEmailAddressError va CA DON HANG khong vao duoc he - tien
		# thu that ma doanh thu khong co. Dat o "*" chu khong liet ke tung
		# doctype: co it nhat bon duong dat email vao mot hoa don, cong
		# them Contact sinh tu nhap khach, va liet ke thi hom nao them
		# duong thu sau la quen.
		"before_validate": "vagabond.email_sach.don",
		"after_insert": "vagabond.email_sach.ghi_vet",
	},
	# O NGUOI GUI RONG LAM CHET CA DUONG THU DI.
	#
	# Tu 16/08/2026, 117 tren 118 email cua ca tiem mat o `sender`,
	# `smtplib.quoteaddr(None)` no, va 26 don mua hang cua Uyen khong toi tay
	# nha cung cap. Goc la hook `email_sach.don` ngay tren, da va.
	#
	# `bu_nguoi_gui` la luoi hung, cho moi ly do khac lam o do rong: ai do
	# goi `frappe.sendmail` quen truyen `sender`, hop thu mac dinh bi tat,
	# hoac mot hook nao do sau nay lai dung vao.
	#
	# `danh_dau_cho_gui` la nhip MOT trong ba nhip cua trang thai gui thu:
	# dat "Dang cho gui" ngay luc thu vao hang doi. Hai nhip sau do
	# `trang_thai_thu.soat_tu_dong` lo, vi Frappe doi trang thai hang doi
	# bang db.set_value nen khong no hook.
	#
	# Ca hai deu o `after_insert` chu khong `before_insert`: ghi o
	# `before_insert` thi tang `validate` chay sau do xoa lai duoc, va do
	# dung la chuyen da xay ra hom 17/08.
	"Email Queue": {
		"after_insert": [
			"vagabond.gui_thu.bu_nguoi_gui",
			"vagabond.trang_thai_thu.danh_dau_cho_gui",
		]
	},
	# Ma khach hang sinh theo nhom (KL, SI, DN, SA, NB). Dat o autoname chu
	# khong o before_insert: before_insert chay SAU khi Frappe da chot ten,
	# doi ten o do la khong an.
	"Customer": {"autoname": "vagabond.ma_khach.dat_ma"},
	# Chan don mua dat qua so thu mua da duyet tren phieu yeu cau. App khong
	# tao don mua tu phieu yeu cau, nhung nut "Create > Purchase Order" cua
	# ERPNext tren Desk thi co, va no doc `qty` chu khong biet gi ve
	# `sl_duyet`. Khong chan o day thi mot dong da tu choi van len duoc don,
	# va ca man Duyet yeu cau mua thanh vo nghia.
	# Don mua hang: PHAI theo so thu mua da duyet, bam tu dau cung vay.
	#
	# before_validate ha so va bo dong bi tu choi roi KE RA cho nguoi bam
	# nhin thay; validate la hang rao cuoi, con lech thi nem loi. Hai lop
	# chu khong mot: lop tren lo cho nguoi dung khoi phai tu sua tay, lop
	# duoi lo cho khong duong nao lot qua. Doc dau ham
	# `dong_bo_don_mua_theo_duyet` de biet ca that ngay 27/08/2026.
	"Purchase Order": {
		"before_validate": "vagabond.duyet_ycmh.dong_bo_don_mua_theo_duyet",
		"validate": [
			"vagabond.duyet_ycmh.chan_don_mua_trai_duyet",
			# HANG RAO DON VI, them 27/08/2026 sau khi ra 43 mau lenh Desk.
			# Mau "Goi y gia mua" ghi thang don vi vao dong don mua, ke ca
			# don vi ma danh muc Mon chua khai. Da co that: DMH-2026-00127
			# ghi 1 "Box" he so 1 trong khi mon chi khai Gram/Kg/Lon, tuc
			# mot thung hang vao kho thanh mot gram.
			#
			# Chan o tang duoi chu khong di sua mau lenh: mau lenh nam trong
			# co so du lieu, git khong quan, khong ca kiem nao soi. Chan o
			# day thi ca nut ben app lan nut ben Desk deu chiu chung mot luat,
			# va nhung duong minh chua biet cung bi chan luon.
			"vagabond.gac_don_vi.chan_don_vi_la",
		],
	},
	# Tu chon lo cho nguyen lieu bi tru. Xem dau tep lo_hang.py: bep khong
	# the go so lo tren dien thoai, va ba luong khac nhau cua app cung sinh
	# ra phieu san xuat nen phai va o mot cho duy nhat.
	"Stock Entry": {"before_validate": "vagabond.lo_hang.gan_lo"},
	# Co "Lam tuoi" chi danh cho chang BTP thanh phan. Ngay 28/08/2026 do
	# duoc 23 tren 23 ma Banh khuon C2 mang co nay, tuc ca lo bi bat chu
	# khong phai lo tay mot lan. Xem dau muc trong phantom.py.
	"Item": {"validate": "vagabond.phantom.chan_lam_tuoi_sai_chang"},
	# Nguyen lieu thay the: may soat cap va dien cac o cot ngay luc luu.
	# Chi la o tro giup, hong thi ghi Error Log chu KHONG chan ai luu.
	"Item Alternative": {"validate": "vagabond.nvl_thay_the.khi_luu"},
	# GAN ASSIGNEE THAT vao phieu luc phieu sinh ra (anh Viet 21/08/2026).
	#
	# Dat o hook chu khong sua muoi cho tao phieu: phieu sinh ra tu app, tu
	# Desk, tu nut Create cua ERPNext va tu dong bo - sua cho tao thi luon
	# sot mot duong. Luat ai phai lam nam trong vagabond/giao_viec.py va soi
	# dung vao bo loc cua man Viec can lam.
	#
	# on_update_after_submit chu khong on_update: yeu cau mua doi status
	# (Pending -> Ordered) SAU khi da ghi so, va do la luc phai go viec ra
	# khoi hop cua thu mua.
	"Material Request": {
		"after_insert": "vagabond.giao_viec.khi_sinh_phieu",
		"on_submit": "vagabond.giao_viec.khi_sinh_phieu",
		"on_update_after_submit": "vagabond.giao_viec.khi_xong",
		"on_cancel": "vagabond.giao_viec.khi_xong",
	},
	"Purchase Receipt": {
		"after_insert": "vagabond.giao_viec.khi_sinh_phieu",
		# HAI PHIEN CUNG THEM VAO DAY trong ngay 27/08/2026, giu CA HAI theo
		# quy tac 8: cung them vao mot cho thi khong ai duoc chon bo ai.
		"before_validate": [
			# Cung hang rao don vi nhu ben don mua. Phieu nhap la cho hang THAT
			# vao kho, sai don vi o day la sai ton kho va sai gia von ngay lap tuc.
			"vagabond.gac_don_vi.chan_don_vi_la",
			# Cau bao tieng Viet khi ngay don mua muon hon ngay phieu nhap. Dat o
			# before_validate vi `validate_posting_date_with_po` cua ERPNext nam
			# ngay dong dau `validate()`, nen minh phai noi truoc no. KHONG noi
			# chot nao, chi doi cau chu. Xem dau tep ngay_don_mua.py.
			"vagabond.ngay_don_mua.bao_ngay_don_mua",
		],
		# Ghi lai gia va so luong da doi so voi don mua hang. CHI GHI CHU,
		# khong chan ai - doc `vagabond/gia_khi_nhan.py` de biet vi sao noi
		# hai cai chan cua ERPNext ra ma van con kiem soat.
		"validate": "vagabond.gia_khi_nhan.ghi_vet",
		# Chan ghi so khi kho nhan hang tro vao tai khoan thanh pham 155x.
		# Chi Dung 28/08/2026: "phieu nhap kho phai vao 152 chu khong phai
		# vao 155, 155 la thanh pham khi minh xuat ban thoi". Dat o
		# before_submit chu khong phai validate: luu nhap thi cu cho luu,
		# chi chan dung luc con so sap cham so cai. Doc dau tep gac_tk_kho.py.
		"before_submit": "vagabond.gac_tk_kho.chan_nhap_vao_thanh_pham",
		"on_submit": "vagabond.giao_viec.khi_xong",
		"on_cancel": "vagabond.giao_viec.khi_xong",
	},
	"Phieu Kiem Ke": {
		"after_insert": "vagabond.giao_viec.khi_sinh_phieu",
		"on_update": "vagabond.giao_viec.khi_sinh_phieu",
	},
	# Tang qua khach VIP: KHONG CON HOOK GIAO VIEC TU DONG.
	#
	# Anh Viet chot 26/08/2026 sau khi chi Dung nhan duoc phan cong mot phieu
	# tang qua khong lien quan gi toi chi. Nguyen nhan: `_ai_phai_lam` giao
	# cho MOI nguoi giu mot trong ba vai Sales User, Sales Manager, Bo phan
	# dat hang - ma ba vai do phu rat rong, cham ca ke toan va bep. Nhap mot
	# lo 34 phieu la ban ra hang tram phan cong cung mot luc.
	#
	# Nay chi con phan cong TAY: ai can thi bam nut Phan cong tren Desk.
	# Dung them lai hook o day. Bo phan lam la Sales hay Marketing van la mot
	# o de LOC va de biet ai lo, khong phai lenh giao viec cho ca bo phan.
	# Cay kho bon chang cua bep (Khai chot 21/08/2026): moi dong nguyen lieu
	# cua lenh san xuat lay dung kho cua chang no.
	#
	# Dat o hook chu khong o cho tao lenh tren app: lenh san xuat sinh ra tu
	# it nhat bon duong - man Tao lenh, man Ban thanh pham can lam, mo dun
	# phantom, va tay nguoi tren Desk. Sua mot duong la ba duong kia van lay
	# sai kho, ma sai kho thi tru nham ton cua bep khac, khong ai thay cho
	# toi luc kiem ke.
	"Work Order": {
		# Dien san ba o kho theo mon va bep, chi dien o dang TRONG. Dat o
		# before_validate vi ERPNext dung ba o do de dung bang nguyen lieu
		# NGAY TRONG validate; dien muon hon la bang do da dung xong.
		"before_validate": "vagabond.kho_san_xuat.gan_kho_lenh",
		"validate": "vagabond.kho_san_xuat.gan_kho_nguon",
	},
	# Hoa don mua DICH VU: gom ve mot dong, so lay tu DAU hoa don dien tu.
	#
	# Dat o before_validate chu khong o validate: ERPNext tinh lai tong tien
	# SAU buoc nay, dat o validate thi con so khong an - cung ly do voi hang
	# OWNER ben Sales Invoice.
	#
	# Chan lech tong dat o before_submit: ban nhap con dang go thi cu de go,
	# ghi so moi la luc so that su vao sach.
	#
	# giu_tk_theo_phieu_nhap dat o "validate" chu khong "before_validate":
	# no phai chay SAU set_expense_account cua ERPNext de sua lai con so ham
	# do vua dien. Frappe chay phuong thuc cua lop truoc roi moi toi cac hook
	# cung ten, nen "validate" la dung nhip. Dat truoc la bi ghi de lai ngay.
	"Purchase Invoice": {
		"before_validate": [
			"vagabond.mua_dich_vu.truoc_khi_luu",
			# DONG BO HAI MAN VE MOT BAN CHAT (anh Viet 26/08/2026): to sinh
			# tu hoa don dien tu ma dong hang bi de lech di - du do nut "Noi
			# phieu nhap kho" ben Desk, nut "Lay mat hang tu", hay tay go -
			# thi may dung lai dung ban goc NGAY TRONG LAN LUU va giu lien
			# ket phieu nhap. Ban v318 chi canh bao roi dan mieng "dung bam
			# nut ben Desk", anh Viet bac: va bang loi dan khong phai va he
			# thong. Dat o before_validate vi ERPNext tinh lai tong tien SAU
			# buoc nay - cung ly do voi hook ngay tren.
			"vagabond.dung_lai_hddt.dong_bo_luc_luu",
			# Cau bao tieng Viet khi ngay don mua muon hon ngay hoa don. Xem
			# ghi chu cung ten o khoi Purchase Receipt phia tren.
			"vagabond.ngay_don_mua.bao_ngay_don_mua",
		],
		"validate": [
			"vagabond.ke_toan_mua.giu_tk_theo_phieu_nhap",
			# To may dung thi tai khoan chi phi cua dong DICH VU di theo khai
			# bao cua danh muc Mon (tiep khach di 64183, chi Dung chot
			# 26/08/2026). Chi cham dong khong quan kho va chua noi phieu
			# nhap, de khong dam len luat tai khoan cho 3311 cua hang kho.
			"vagabond.dung_lai_hddt.tk_theo_mon",
		],
		"before_submit": "vagabond.mua_dich_vu.chan_lech_tong",
		# BANG GIA NHAP DUOI THEO GIA THAT (anh Viet duyet 31/08/2026).
		#
		# Truoc ban nay bang gia dong bang o gia lan mua dau: thiet lap kho
		# dat "chi ghi khi thieu, khong cap nhat lai". Don mua keo gia tu bang
		# gia xuong, phieu nhap ke thua tu don mua, nen ca day chuyen chay
		# bang mot con so khong ai soat. Ca that: mon NVLT00116 trai cherry,
		# bang gia 420.000 mot Kg dat 30/07, hoa don thuc 19/08 la 480.000.
		#
		# Chi nghe HOA DON luc ghi so, va chi nhan dong co don vi sach. Doc
		# dau tep bang_gia_nhap.py de biet vi sao khong bat thang o cua
		# ERPNext.
		"on_submit": "vagabond.bang_gia_nhap.cap_nhat_tu_hoa_don",
	},
	# De nghi chi noi bo: dien ho tai khoan hach toan va tai khoan nhan tien,
	# chan thang phan loai tai san co dinh. Luat nam o de_nghi_chi.py.
	# Thu gui nha cung cap tu don mua hang. CHI dong vao thu co chung tu goc
	# dung la Don mua hang va dang gui DI; moi thu khac di qua khong sut me
	# gi. Doc dau tep gac_thu_ncc.py truoc khi sua: ngay 16/08/2026 mot hook
	# dat tren "*" da lam ca tiem khong gui duoc thu nao suot bon ngay.
	"Communication": {
		"before_insert": "vagabond.gac_thu_ncc.chan_thu_don_hong",
	},
	"Vagabond De Nghi Chi": {
		"before_validate": "vagabond.de_nghi_chi.truoc_khi_luu",
	},
	# Phieu chi hoan tien khach: chua dinh kem uy nhiem chi thi khong ghi so
	# duoc. Chan o backend chu khong chi nhac tren man - day la chung tu goc
	# de giai trinh, nhac tren man thi bo qua duoc.
	"Payment Entry": {
		# Ten goi dung theo tai khoan tien: 111 la Phieu thu/Phieu chi, 112
		# la Giay bao Co / Uy nhiem chi (chi Dung chot 16/08/2026).
		"validate": "vagabond.chung_tu_tien.dat_ten",
		"before_submit": [
			# Chung tu qua NGAN HANG phai co Uy nhiem chi dinh kem. Chi Dung
			# KHONG cong nhan dong sao ke SePay thay cho tep nay.
			"vagabond.chung_tu_tien.chan_thieu_dinh_kem",
			"vagabond.hoan_tien.chan_thieu_uy_nhiem_chi",
		],
		"on_submit": "vagabond.hoan_tien.khi_ghi_so_phieu_chi",
	},
	"Sales Invoice": {
		# Hang OWNER: tu ap giam 100%, bat co don noi bo. Dat o
		# before_validate vi ERPNext tinh lai tong tien SAU buoc nay; dat o
		# validate thi con so khong an. Va dat o hook chu khong o tung ham
		# cua POS, vi co it nhat nam duong tao hoac sua mot hoa don.
		# Hai viec, chay theo thu tu: don o email sai truoc (de chung tu con
		# luu duoc), roi moi ap giam gia noi bo.
		"before_validate": [
			"vagabond.email_sach.don",
			"vagabond.noi_bo.truoc_khi_luu",
			# Nguoi ban: dien tai khoan dang dang nhap luc TAO to hoa don.
			# May dong bo ve thi de trong chu khong dien bua, xem dau tep
			# vagabond/nguoi_ban.py.
			"vagabond.nguoi_ban.truoc_khi_luu",
		],
		"before_save": "vagabond.ban_hang.chan_trung_ma_pancake",
		# Chan sai NGAY LUC LUU: thieu nguon don, thieu phuong thuc thanh
		# toan, hay phuong thuc khong dung duoc cho nguon do (anh Viet
		# 13/08/2026). Nhip dong bo Pancake duoc mien - xem ghi chu trong
		# vagabond.ban_hang.kiem_truoc_khi_luu.
		# Hai viec o validate, chay theo thu tu:
		#   1. Luat ban hang cu: nguon don, phuong thuc thanh toan.
		#   2. Hang rao qua tang VIP: to co gan phieu qua thi phieu phai co
		#      that, dot phai Dang chay, dung khach, chua tang lan nao, va moi
		#      dong hang phai nam trong danh sach qua da duyet.
		#
		# Dat o validate chu khong o before_submit vi anh Viet yeu cau "vang
		# loi chan cung khong cho xuat" - chan ngay luc luu thi nhan vien biet
		# sai trong luc con dang go.
		#   3. Hang tang khong thu tien: bat khai loai tang va ly do tang,
		#      xoa moi khoan giam de giu nguyen gia va thue, va dat trang thai
		#      duyet. Sua ruot don sau khi da duyet thi don tu roi ve Cho
		#      duyet - xem dau van don trong vagabond/hang_tang.py.
		#   4. Mot don tra bang NHIEU phuong thuc (anh Viet 01/09/2026): o
		#      `vgb_pt_thanh_toan` luon mang dong LON NHAT cua bang con.
		#      Dat CUOI cung trong day validate, sau `kiem_truoc_khi_luu`:
		#      dat truoc thi luat cu doc o phuong thuc luc no con la gia tri
		#      nguoi go, roi bang con doi no ngay sau, thanh ra to di vao so
		#      mang mot phuong thuc chua qua phep kiem nao.
		"validate": [
			"vagabond.ban_hang.kiem_truoc_khi_luu",
			"vagabond.qua_tang_hoa_don.truoc_khi_luu",
			"vagabond.hang_tang.truoc_khi_luu",
			"vagabond.thanh_toan_nhieu.dat_pt_chinh",
		],
		# Chan ban lo han muc mua vu (anh Viet chot 18/08/2026: "tuyet doi
		# khong cho phep ban lo").
		#
		# Dat o before_submit chu khong o validate: bill con nhap la sales
		# dang go, chan giua luc go la lam ho ket khong luu duoc gi. Ghi so
		# moi la luc so that su vao sach.
		# Hai viec o before_submit:
		#   1. Chan ban le han muc mua vu.
		#   2. Noi ghi chu "(Hang tang khong thu tien)" vao dien giai tung
		#      dong cua hoa don qua, va kiem tai khoan chi phi bieu tang da
		#      khai chua TRUOC khi to vao so.
		#   3. Don hang tang chua duoc Giam doc duyet thi KHONG cho ghi so.
		#      Day la cua chan that cua luong duyet; giau nut tren man hinh
		#      khong phai la chan.
		#   4. Cac dong thanh toan phai cong du tong don. Cho qua mot to
		#      lech thi dung cai sai cu quay lai, ma lan nay con kho thay
		#      hon vi nhin vao tuong da tach roi.
		"before_submit": [
			"vagabond.mua_vu.chan_ban_lo",
			"vagabond.qua_tang_hoa_don.truoc_khi_ghi_so",
			"vagabond.hang_tang.truoc_khi_ghi_so",
			"vagabond.thanh_toan_nhieu.kiem_truoc_ghi_so",
		],
		# Tich diem cho khach theo hang. Dat o on_submit chu khong o
		# before_submit: chi cong diem khi hoa don da that su vao so.
		"on_submit": [
			"vagabond.khach_hang.cong_diem_hoa_don",
			# Hoa don qua: dong dau Da tang len phieu (chong nhan hai lan) va
			# gat cong no sang chi phi bieu tang de khach tra 0 dong.
			"vagabond.qua_tang_hoa_don.sau_khi_ghi_so",
			# Don tra bang Hang tang: gat cong no sang chi phi bieu tang de
			# khach tra 0 dong, con hoa don van giu nguyen gia va thue.
			"vagabond.hang_tang.sau_khi_ghi_so",
		],
		# Huy hoa don kenh khac thi tra so lai cho bang kiem banh. Truoc day
		# co ca after_delete o day, nay bo di: khong ai xoa duoc hoa don nua
		# nen no la ma chet, de lai chi lam nguoi doc tuong con duong xoa.
		"on_cancel": [
			"vagabond.kiem_banh.khi_doi_hoa_don",
			# Huy hoa don thi rut lai dung so diem da cong cho hoa don do.
			"vagabond.khach_hang.hoan_diem_hoa_don",
			# ... va tra lai dung so diem khach DA TIEU tren hoa don do.
			#
			# Hai viec nguoc chieu nhau nen phai la hai ham: mot cai rut ve
			# diem quan da tang, mot cai tra lai diem khach da mat. Day chi la
			# MOT trong ba duong mot don co the chet - duong huy mem vgb_huy
			# KHONG di qua day, xem chung_tu.danh_dau_huy.
			"vagabond.diem_otp.hoan_khi_huy_hoa_don",
			# Huy hoa don qua thi tra phieu ve Chua tang va HUY (khong xoa)
			# but toan gat cong no. Khong tra lai thi phieu ket vinh vien o
			# Da tang ma khach chua he nhan duoc gi.
			"vagabond.qua_tang_hoa_don.khi_huy",
			# Huy don hang tang thi HUY (khong xoa) but toan gat cong no.
			"vagabond.hang_tang.khi_huy",
		],
	},
}

# app.thevagabondpatisserie.com va order.thevagabondpatisserie.com tro chung
# mot site nen mac dinh dung chung mot anh xem truoc. Hook nay doi bo the og
# rieng cho ten mien app.*, xem vagabond/lib.py.
# MOT khai bao duy nhat cho update_website_context. Khai hai lan trong cung
# mot tep thi lan sau DE lan truoc va hook kia im lang khong chay - Python
# khong bao gi ca. Da suyt dinh dung bay nay ngay 23/08/2026.
#
# Dinh tuyen ten mien dat TRUOC: no co the chuyen huong, chay xong viec khac
# roi moi chuyen huong la phi cong.
update_website_context = [
	"vagabond.hooks._dinh_tuyen_ten_mien",
	"vagabond.lib.og_theo_ten_mien",
]

# Thu moi nhan vien: thay thu chao mung mac dinh cua Frappe (dan vao ban quan
# tri tren may tinh) bang thu chi huong dan mo app dien thoai.
override_doctype_class = {
	"User": "vagabond.nhan_su.NguoiDung",
	# 21/08/2026: DA GO hai lop PhieuNhapKho va HoaDonMua o day. Chung dinh
	# doi tac vao dong so cai cua tai khoan cho hoa don, ma ERPNext chi cho
	# dinh doi tac len tai khoan loai Receivable/Payable/Equity, nen moi
	# lan Xac nhan nhap kho deu bi chan cung va CA TIEM khong nhap duoc
	# hang. DUNG DUNG LAI. Chi tiet theo nha cung cap lay tu chung tu, xem
	# cua `vagabond.ke_toan_mua.so_chi_tiet_ncc`. Ly do day du o dau tep
	# vagabond/ke_toan_mua.py.
}


# Dung lai cac truong tu them do ma nguon khai, sau moi lan deploy. Thao tac
# lap lai duoc: khai lai lan hai khong doi gi.
after_migrate = ["vagabond.truong_tu_them.dung"]
