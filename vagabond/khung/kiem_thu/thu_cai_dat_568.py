# -*- coding: utf-8 -*-
"""v568: bố cục trang Cài đặt Vagabond.

Anh Việt 04/10/2026, kèm hai ảnh trang Cài đặt: *"những phần mã code ở đầu
này có ẩn đi hay thu gọn lại được không? Chữ hướng dẫn thì không có dấu
tiếng Việt. Quy hoạch lại ... sao cho khoa học nhất, logic nhất"*.

Vì sao mười một ô mã nằm chình ình ở ĐẦU trang: chúng là trường tự thêm
(Custom Field) khai trong mã nguồn mà không có `insert_after`, và Frappe đặt
mọi trường tự thêm không có neo lên đầu form. Cái bẫy thứ hai nằm ngay trong
cách Frappe xếp: một MỤC tự thêm neo vào mục cuối của một tab sẽ trôi sang
ĐẦU tab kế tiếp, vì phép dò điểm chèn của Frappe đi qua Tab Break mà không
dừng. Nhìn danh sách trường trong tệp JSON thì không thấy được hai lỗi này.

Nên ca kiểm ở đây CHẠY LẠI đúng phép xếp `Meta.sort_fields` của Frappe v16
(frappe/model/meta.py) trên tệp JSON thật cộng mọi khai `TRUONG_MOI` của
Vagabond Settings trong repo, rồi kiểm từng trường rơi vào đúng tab, đúng mục.
"""

import io
import json
import os
import re
import subprocess

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSON_CD = os.path.join(GOI, "vagabond", "doctype", "vagabond_settings", "vagabond_settings.json")
JS_CD = os.path.join(GOI, "vagabond", "doctype", "vagabond_settings", "vagabond_settings.js")

TAB = [
	("tab_ban_hang", "Bán hàng & thanh toán"),
	("tab_ke_toan", "Hoá đơn & kế toán"),
	("tab_giao_hang", "Giao hàng"),
	("tab_khach_hang", "Khách hàng & điểm"),
	("tab_tin_nhan", "Tin nhắn & cảnh báo"),
	("tab_web", "Web & quảng cáo"),
	("tab_thiet_bi", "Thiết bị & trợ lý"),
	("tab_du_lieu_app", "Dữ liệu app tự ghi"),
]

# Mười một ô mã máy tự ghi (cộng ô xác nhận HĐĐT quá hạn vốn ẩn sẵn) phải nằm
# trong mục thu gọn "Xem dữ liệu gốc", không bao giờ lộ ở đầu trang nữa.
O_MA = [
	"vgb_tai_khoan_nhan", "vgb_diem_ban", "vgb_pt_thanh_toan_ds", "vgb_quyen_bo_mon",
	"vgb_mau_in_quay", "vgb_may_in", "vgb_can_tem", "vgb_pancake_nhip", "vgb_hddt_quay",
	"vgb_kpi_cau_hinh", "vgb_kho_sap", "vgb_nhap_khach_tien_do", "vgb_hddt_xac_nhan_qua_han",
]


def _json():
	return json.load(io.open(JSON_CD, encoding="utf-8"))


def _truong_tu_them():
	"""Mọi trường tự thêm của Vagabond Settings khai trong repo."""
	from vagabond import hach_toan_kho, minvoice_tep, o_cai_dat, qua_tang_hoa_don, sepay, tai_khoan

	ra = []
	for m in (o_cai_dat, tai_khoan, hach_toan_kho, minvoice_tep, sepay, qua_tang_hoa_don):
		for f in m.TRUONG_MOI.get("Vagabond Settings", []):
			ra.append(dict(f))
	return ra


def _xep(chuan, tu_them):
	"""Chép lại Meta.sort_fields của Frappe v16 khi KHÔNG có field_order tuỳ chỉnh."""
	kieu = {f["fieldname"]: f["fieldtype"] for f in chuan + tu_them}
	thu_tu = [f["fieldname"] for f in chuan]
	chen = {}
	for f in tu_them:
		dich = f.get("insert_after")
		if not dich:
			thu_tu.insert(0, f["fieldname"])
			continue
		goc = dich
		if f["fieldtype"] in ("Section Break", "Column Break") and dich in thu_tu:
			for x in thu_tu[thu_tu.index(dich) + 1:]:
				if kieu[x] == "Section Break" or kieu[x] == kieu[goc]:
					break
				dich = x
		elif f["fieldtype"] == "Tab Break" and dich in thu_tu:
			for x in thu_tu[thu_tu.index(dich) + 1:]:
				if kieu[x] == "Tab Break":
					break
				dich = x
		chen.setdefault(dich, []).append(f["fieldname"])
	lai = True
	while lai:
		lai = False
		for k in list(chen):
			if k not in thu_tu:
				continue
			i = thu_tu.index(k)
			for ten in chen.pop(k):
				i += 1
				thu_tu.insert(i, ten)
			lai = True
	for v in chen.values():
		thu_tu.extend(v)
	return thu_tu, kieu


def _vi_tri():
	"""fieldname -> (tab, mục) sau khi Frappe xếp xong."""
	d = _json()
	thu_tu, kieu = _xep(d["fields"], _truong_tu_them())
	ra, tab, muc = {}, None, None
	for fn in thu_tu:
		if kieu[fn] == "Tab Break":
			tab, muc = fn, None
		elif kieu[fn] == "Section Break":
			muc = fn
		ra[fn] = (tab, muc)
	return ra, thu_tu


@ca("cài đặt v568: trang mở đầu bằng tab, đủ tám tab đúng thứ tự")
def _():
	d = _json()
	la("trường đầu là tab", d["fields"][0]["fieldtype"], "Tab Break")
	tabs = [(f["fieldname"], f["label"]) for f in d["fields"] if f["fieldtype"] == "Tab Break"]
	la("tám tab", tabs, TAB)
	la("field_order khớp danh sách trường", d["field_order"], [f["fieldname"] for f in d["fields"]])
	dung("mốc modified đã đẩy lên để site nạp lại bố cục", d["modified"] >= "2026-10-04")


@ca("cài đặt v568: KHÔNG trường nào, kể cả trường tự thêm, nằm trên tab đầu tiên")
def _():
	vt, thu_tu = _vi_tri()
	la("trường đầu sau khi Frappe xếp", thu_tu[0], "tab_ban_hang")
	lot = [fn for fn, (t, _m) in vt.items() if t is None]
	la("trường lọt lên đầu trang", lot, [])


@ca("cài đặt v568: mười ba ô mã máy tự ghi nằm trong mục thu gọn Xem dữ liệu gốc")
def _():
	vt, _ = _vi_tri()
	for fn in O_MA:
		la(fn, vt.get(fn), ("tab_du_lieu_app", "sec_du_lieu_goc"))
	muc = {f["fieldname"]: f for f in _json()["fields"]}
	la("mục dữ liệu gốc thu gọn sẵn", muc["sec_du_lieu_goc"].get("collapsible"), 1)
	la("ô tóm tắt nằm ở tab Dữ liệu app tự ghi", vt["html_du_lieu_app"], ("tab_du_lieu_app", "sec_tom_tat_app"))


@ca("cài đặt v568: mục tự thêm về đúng tab, không trôi sang đầu tab kế tiếp")
def _():
	vt, _ = _vi_tri()
	mong = {
		"khoa_so_ngay": ("tab_ke_toan", "sec_khoa_so"),
		"khoa_so_den": ("tab_ke_toan", "sec_khoa_so"),
		"sepay_bat": ("tab_ke_toan", "sec_sepay"),
		"sepay_chua_map": ("tab_ke_toan", "sec_sepay"),
		"minvoice_pdf_bat": ("tab_ke_toan", "sec_minvoice_pdf"),
		"vgb_ban_tru_kho_tu": ("tab_ke_toan", "vgb_sec_hach_toan_kho"),
		"vgb_sx_621_tu": ("tab_ke_toan", "vgb_sec_hach_toan_kho"),
		"tk_chi_phi_qua_tang": ("tab_ke_toan", "sec_qua_tang"),
		"tu_ghi_so_bat": ("tab_ban_hang", "sec_vgb_tu_dong"),
		"tu_ghi_so_nhat_ky": ("tab_ban_hang", "sec_vgb_tu_dong"),
		# Ô cũ từng bị mục Hạch toán kho chen ngang và kéo đi:
		"hang_tang_xuat_kho_that": ("tab_ban_hang", "sec_vgb_tu_dong"),
		"email_canh_bao": ("tab_tin_nhan", "sec_gui_thu"),
		"minvoice_mau_lien_ket": ("tab_ke_toan", "sec_minvoice"),
		"tk_hoan_tien": ("tab_ke_toan", "sec_hoan_tien"),
		# Mục cuối tab Hoá đơn & kế toán phải còn là của nó, không bị mục tự thêm đè lên.
		"tk_ton_btp_cap1": ("tab_ke_toan", "sec_btp_1552"),
	}
	for fn, v in mong.items():
		la(fn, vt.get(fn), v)


@ca("cài đặt v568: mọi neo insert_after của trường tự thêm đều trỏ vào trường có thật")
def _():
	co = {f["fieldname"] for f in _json()["fields"]} | {f["fieldname"] for f in _truong_tu_them()}
	for f in _truong_tu_them():
		dung("%s neo vào %s" % (f["fieldname"], f.get("insert_after")), f.get("insert_after") in co)


@ca("cài đặt v568: bảng trường tự thêm của ca kiểm không sót module nào trong repo")
def _():
	# Ai thêm khai TRUONG_MOI cho Vagabond Settings ở module mới mà quên thêm vào
	# _truong_tu_them thì ca này đỏ, để phép xếp ở trên không kiểm thiếu.
	co = set()
	for ten in os.listdir(GOI):
		if not ten.endswith(".py"):
			continue
		s = io.open(os.path.join(GOI, ten), encoding="utf-8").read()
		if re.search(r"""["']Vagabond Settings["']\s*:\s*\[""", s):
			co.add(ten[:-3])
	la("các module khai trường tự thêm", sorted(co),
		sorted(["o_cai_dat", "tai_khoan", "hach_toan_kho", "minvoice_tep", "sepay", "qua_tang_hoa_don"]))


@ca("cài đặt v568: mọi nhãn và mô tả là tiếng Việt có dấu, không còn số issue trong nhãn")
def _():
	# Dò những từ tiếng Việt hay gặp nhất mà viết thiếu dấu. Tên riêng như
	# Pancake, Ahamove, WhatsApp thì không có dấu là đúng nên không nằm trong danh sách.
	khong_dau = re.compile(
		r"\b(Dia chi|So dien thoai|khong|duoc|cua|tai khoan|ngan hang|thanh toan|hoa don|bao nhieu|"
		r"de trong|Ban kinh|Toc do|Phut|Diem|nguoi|Ten chu|Ma mau|chuyen khoan|may chu|may tu|tu sinh|"
		r"Vi do|Kinh do|cua hang|Thong bao|Han diem|Lan hu|Da chay|Manh ten|Do phan giai|Khoa rieng)\b",
		re.I)
	for f in _json()["fields"]:
		for o in ("label", "description"):
			v = f.get(o) or ""
			dung("%s.%s còn chữ không dấu: %r" % (f["fieldname"], o, v[:60]), not khong_dau.search(v))
			dung("%s.%s không mang số issue/phiên bản" % (f["fieldname"], o), not re.search(r"\((#\d+|v\d+)\)", v))
	for f in _truong_tu_them():
		dung("%s: nhãn không mang số phiên bản" % f["fieldname"], not re.search(r"\((#\d+|v\d+)\)", f.get("label") or ""))


@ca("cài đặt v568: chip chọn Cách tính hạn điểm lưu đúng giá trị cũ của ô Chọn")
def _():
	d = {f["fieldname"]: f for f in _json()["fields"]}
	cu = [x for x in d["diem_chu_ky"]["options"].split("\n") if x]
	ra = subprocess.check_output(
		["node", "-e",
		 "global.frappe={ui:{form:{on(){}}}};var V=require(process.argv[1]);"
		 "console.log(JSON.stringify({chon:V.NHAN_CHON.diem_chu_ky.map(p=>p[0]),kn:V.KET_NOI}))", JS_CD],
		universal_newlines=True)
	v = json.loads(ra)
	la("giá trị chip trùng tuyệt đối giá trị ô Chọn", v["chon"], cu)
	# Chip tình trạng nhảy tới ô và mục có thật trên trang.
	vt, _ = _vi_tri()
	for k in v["kn"]:
		dung("%s: ô nhảy tới có thật" % k["ten"], k["toi"] in vt)
		dung("%s: mục có thật" % k["ten"], k["muc"] in vt)
		for f in (k.get("can") or []) + sum(k.get("canMot") or [], []) + ([k["bat"]] if k.get("bat") else []):
			dung("%s: ô %s có thật" % (k["ten"], f), f in vt)


@ca("cài đặt v568: không đổi tên trường nào, giá trị đang lưu giữ nguyên")
def _():
	# Bố cục mới chỉ thêm tab, mục và một ô tóm tắt; không bỏ, không đổi tên ô
	# nào đang chứa dữ liệu.
	d = _json()
	ten = {f["fieldname"] for f in d["fields"]}
	can_co = {
		"goong_api_key", "minvoice_password", "zalo_nhom", "zalo_chat_moi", "diem_chu_ky", "ngan_hang_bin",
		"email_da_cuu_su_co_1608", "qz_chung_thu", "tk_ton_btp_cap2", "webhook_don_web", "meta_capi_token",
		"push_khoa_rieng", "minvoice_mau_lien_ket", "kho_hang_huy", "tro_ly_luot_thang", "link_app",
	}
	la("ô cũ còn đủ", sorted(can_co - ten), [])
	moi = {f["fieldname"] for f in d["fields"] if f["fieldtype"] not in ("Tab Break", "Section Break", "Column Break")}
	la("ô có giá trị mới thêm", sorted(moi - can_co - _o_cu()), ["html_du_lieu_app"])


def _o_cu():
	# Danh sách ô có giá trị của bản v567 (trước khi quy hoạch), chép cứng để
	# chốt rằng v568 không đổi tên ô nào.
	return set("""
goong_api_key suggest_radius_km kitchen_lat kitchen_lng kitchen_address store_lat store_lng store_address
ban_kinh_giao_km ahamove_api_key ahamove_mobile ahamove_base ma_dich_vu dung_dich_vu_de_vo phu_thu
pancake_api_key pancake_shop_id pancake_order_source_id minvoice_host minvoice_username minvoice_password
minvoice_ma_dvcs minvoice_series minvoice_ma_thue greensm_client_id greensm_client_secret greensm_token_url
greensm_sandbox be_base be_token so_don_toi_da_chuyen toc_do_km_h phut_moi_diem he_so_duong_thuc
dung_goong_xep_tuyen link_app zalo_app_id zalo_app_secret zalo_refresh_token zalo_access_token
zalo_token_het_han zns_template_otp pancake_qr_provider pancake_qr_account_id ngan_hang_bin ngan_hang_stk
ngan_hang_ten ngan_hang_hien_thi trang_thanh_toan zns_template_thanh_toan wa_phone_id wa_token
wa_template_thanh_toan wa_ngon_ngu tu_xuat_hddt hang_tang_xuat_kho_that email_canh_bao gemini_api_key
diem_quy_doi diem_tran_pt diem_bill_toi_thieu diem_otp_giay zns_template_diem diem_zns_gia_lap diem_chu_ky
diem_han_thang diem_ngay_chot ha_hang_tung_bac kho_hang_huy tk_hoan_tien minvoice_mau_lien_ket
push_khoa_cong_khai push_khoa_rieng webhook_bao_dong webhook_dat_ban email_bao_dong_lan_cuoi
email_da_cuu_su_co_1608 qz_chung_thu qz_khoa_rieng qz_may_in_hoa_don qz_may_in_tem qz_dpi tro_ly_bat
tro_ly_khoa tro_ly_mo_hinh tro_ly_luot_ngay tro_ly_luot_thang tk_ton_btp_cap1 tk_ton_btp_cap2
mien_phi_giao_tu web_dien_thoai web_email web_zalo web_messenger web_facebook web_instagram web_tiktok
webhook_don_web meta_pixel_id meta_capi_token meta_test_event_code meta_graph_phien_ban zalo_bot_bat
zalo_bot_token zalo_bi_mat zalo_noi_trang_thai zalo_chat_moi zalo_nhom
""".split())


@ca("cài đặt v568: tên và biểu tượng loại tin Zalo trên hộp chọn trùng tuyệt đối kenh_zalo.LOAI")
def _():
	from vagabond import kenh_zalo as kz

	ra = subprocess.check_output(
		["node", "-e",
		 "global.frappe={ui:{form:{on(){}}}};var V=require(process.argv[1]);console.log(JSON.stringify(V.ZALO_NHAN))", JS_CD],
		universal_newlines=True)
	v = json.loads(ra)
	for ma, (ic, ten) in kz.LOAI.items():
		la("loại %s: biểu tượng" % ma, v["loai_tin"][ma][0], ic)
		la("loại %s: tên" % ma, v["loai_tin"][ma][1], ten)
	la("chủ đề trùng CHU_DE", sorted(v["chu_de"]), sorted(kz.CHU_DE))
