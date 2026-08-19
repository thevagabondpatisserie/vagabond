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
		],
		"*/30 * * * *": ["vagabond.ban_hang.dong_bo_doanh_so_tu_dong"],
		# Moi gio: don da ghi so ma chua co hoa don dien tu thi xuat bu.
		"15 * * * *": ["vagabond.ban_hang.xuat_hddt_con_thieu_tu_dong"],
		# Moi gio: doi soat lenh chi hoan tien voi sao ke SePay.
		"35 * * * *": ["vagabond.hoan_tien.doi_soat_tu_dong"],
		# Gio chay chuoi cuoi ngay khai trong Vagabond Settings, sua duoc
		# ngay tren app (mac dinh 23:00, ca ba buoc xong truoc 23h30). Chi
		# Dung so xuat hoa don sat 24h, lo nghen mang la to hoa don lot
		# sang ngay hom sau, sai luat ke toan (anh Viet 12/08/2026).
		# 23h55: chuoi cuoi ngay va cac nhip vet da xong. Con don nao chua ghi
		# so duoc thi gui thu bao ngay trong dem. Truoc 13/08/2026 loi chi rot
		# vao Error Log ma khong ai mo, nen 149 don nam nhap nua thang (114
		# trieu) khong ai hay.
		"55 23 * * *": ["vagabond.ban_hang.canh_bao_don_treo"],
		# 2h sang: ra don bi lap hai hoa don, co thi gui thu bao.
		"0 2 * * *": ["vagabond.ban_hang.ra_trung_hang_dem"],
		# Xet lai hang thanh vien theo chi tieu ky. Chay sau nua dem, truoc
		# gio mo cua, de sang ra quay da thay dung hang cua khach.
		"30 4 * * *": ["vagabond.khach_hang.xet_lai_tu_dong"],
		# 5h sang: dot diem qua han theo chu ky khai trong Cai dat.
		#
		# Chay SAU xet lai hang: xet hang doc chi tieu tu hoa don chu khong
		# doc so diem, nen thu tu khong doi ket qua - nhung neu sau nay ai
		# gan hai viec vao nhau thi thu tu dung la xet hang truoc, dot diem
		# sau. Ham tu kiem cau hinh va thoat ngay khi dang Tat (mac dinh).
		"0 5 * * *": ["vagabond.diem_han.het_han_tu_dong"],
		# 3h sang: xoa anh giao hang cua van don qua 30 ngay cho nhe he thong
		"0 3 * * *": [
			"vagabond.van_don.don_dep_anh_giao",
			"vagabond.dang_nhap.don_dep_phien",
			# Nhat ky dong bo la vet ky thuat, khong phai chung tu ke toan,
			# nen don sau 90 ngay. Cac dong dang cho nguoi xem thi giu lai.
			"vagabond.nhat_ky_dong_bo.don_cu",
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
	# Ma khach hang sinh theo nhom (KL, SI, DN, SA, NB). Dat o autoname chu
	# khong o before_insert: before_insert chay SAU khi Frappe da chot ten,
	# doi ten o do la khong an.
	"Customer": {"autoname": "vagabond.ma_khach.dat_ma"},
	# Chan don mua dat qua so thu mua da duyet tren phieu yeu cau. App khong
	# tao don mua tu phieu yeu cau, nhung nut "Create > Purchase Order" cua
	# ERPNext tren Desk thi co, va no doc `qty` chu khong biet gi ve
	# `sl_duyet`. Khong chan o day thi mot dong da tu choi van len duoc don,
	# va ca man Duyet yeu cau mua thanh vo nghia.
	"Purchase Order": {"validate": "vagabond.duyet_ycmh.chan_don_mua_trai_duyet"},
	# Hoa don mua DICH VU: gom ve mot dong, so lay tu DAU hoa don dien tu.
	#
	# Dat o before_validate chu khong o validate: ERPNext tinh lai tong tien
	# SAU buoc nay, dat o validate thi con so khong an - cung ly do voi hang
	# OWNER ben Sales Invoice.
	#
	# Chan lech tong dat o before_submit: ban nhap con dang go thi cu de go,
	# ghi so moi la luc so that su vao sach.
	"Purchase Invoice": {
		"before_validate": "vagabond.mua_dich_vu.truoc_khi_luu",
		"before_submit": "vagabond.mua_dich_vu.chan_lech_tong",
	},
	# De nghi chi noi bo: dien ho tai khoan hach toan va tai khoan nhan tien,
	# chan thang phan loai tai san co dinh. Luat nam o de_nghi_chi.py.
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
		],
		"before_save": "vagabond.ban_hang.chan_trung_ma_pancake",
		# Chan sai NGAY LUC LUU: thieu nguon don, thieu phuong thuc thanh
		# toan, hay phuong thuc khong dung duoc cho nguon do (anh Viet
		# 13/08/2026). Nhip dong bo Pancake duoc mien - xem ghi chu trong
		# vagabond.ban_hang.kiem_truoc_khi_luu.
		"validate": "vagabond.ban_hang.kiem_truoc_khi_luu",
		# Chan ban lo han muc mua vu (anh Viet chot 18/08/2026: "tuyet doi
		# khong cho phep ban lo").
		#
		# Dat o before_submit chu khong o validate: bill con nhap la sales
		# dang go, chan giua luc go la lam ho ket khong luu duoc gi. Ghi so
		# moi la luc so that su vao sach.
		"before_submit": "vagabond.mua_vu.chan_ban_lo",
		# Tich diem cho khach theo hang. Dat o on_submit chu khong o
		# before_submit: chi cong diem khi hoa don da that su vao so.
		"on_submit": "vagabond.khach_hang.cong_diem_hoa_don",
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
		],
	},
}

# app.thevagabondpatisserie.com va order.thevagabondpatisserie.com tro chung
# mot site nen mac dinh dung chung mot anh xem truoc. Hook nay doi bo the og
# rieng cho ten mien app.*, xem vagabond/lib.py.
update_website_context = ["vagabond.lib.og_theo_ten_mien"]

# Thu moi nhan vien: thay thu chao mung mac dinh cua Frappe (dan vao ban quan
# tri tren may tinh) bang thu chi huong dan mo app dien thoai.
override_doctype_class = {
	"User": "vagabond.nhan_su.NguoiDung",
}


# Dung lai cac truong tu them do ma nguon khai, sau moi lan deploy. Thao tac
# lap lai duoc: khai lai lan hai khong doi gi.
after_migrate = ["vagabond.truong_tu_them.dung"]
