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
	},
}
