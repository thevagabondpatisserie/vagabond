"""/google-merchant.xml (luật định tuyến trong hooks.py trỏ về đây): tệp bánh
Đặc biệt tuần này và bánh theo mùa cho Google Merchant Center tìm nạp theo lịch.
Xem vagabond/google_merchant.py."""

from vagabond import google_merchant

no_cache = 1
base_template_path = "www/vgb-google-merchant.xml"


def get_context(context):
	context.no_cache = 1
	context.tep = google_merchant.xml_tep(google_merchant.mon_dua_google())
