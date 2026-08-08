app_name = "vagabond"
app_title = "Vagabond"
app_publisher = "Cong ty TNHH Patisserie Vagabond"
app_description = "Cong dat banh online: noi Frappe voi Pancake POS, Goong va Ahamove"
app_email = "thevagabondbakery@gmail.com"
app_license = "MIT"

# Cac endpoint deu nam o vagabond/api.py va da co @frappe.whitelist,
# khong can khai bao them o day.

# Kiem banh ngay: 5 phut keo don Pancake mot lan de cot "da dat" va
# "phat sinh" tu chay, sales khoi dem tay.
scheduler_events = {
	"cron": {
		"*/5 * * * *": ["vagabond.kiem_banh.dong_bo_tu_dong"],
		"*/30 * * * *": ["vagabond.ban_hang.dong_bo_doanh_so_tu_dong"],
		# Moi gio: don da ghi so ma chua co hoa don dien tu thi xuat bu.
		"15 * * * *": ["vagabond.ban_hang.xuat_hddt_con_thieu_tu_dong"],
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
	"Sales Invoice": {
		"before_save": "vagabond.ban_hang.chan_trung_ma_pancake",
		# Huy hoac xoa hoa don kenh khac thi tra so lai cho bang kiem banh.
		"on_cancel": "vagabond.kiem_banh.khi_doi_hoa_don",
		"on_trash": "vagabond.kiem_banh.khi_doi_hoa_don",
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
