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
		# Gio chay chuoi cuoi ngay khai trong Vagabond Settings, sua duoc
		# ngay tren app (mac dinh 23:00, ca ba buoc xong truoc 23h30). Chi
		# Dung so xuat hoa don sat 24h, lo nghen mang la to hoa don lot
		# sang ngay hom sau, sai luat ke toan (anh Viet 12/08/2026).
		# 2h sang: ra don bi lap hai hoa don, co thi gui thu bao.
		"0 2 * * *": ["vagabond.ban_hang.ra_trung_hang_dem"],
		# 3h sang: xoa anh giao hang cua van don qua 30 ngay cho nhe he thong
		"0 3 * * *": [
			"vagabond.van_don.don_dep_anh_giao",
			"vagabond.dang_nhap.don_dep_phien",
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
	},
	"Sales Invoice": {
		"before_save": "vagabond.ban_hang.chan_trung_ma_pancake",
		# Huy hoa don kenh khac thi tra so lai cho bang kiem banh. Truoc day
		# co ca after_delete o day, nay bo di: khong ai xoa duoc hoa don nua
		# nen no la ma chet, de lai chi lam nguoi doc tuong con duong xoa.
		"on_cancel": "vagabond.kiem_banh.khi_doi_hoa_don",
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
