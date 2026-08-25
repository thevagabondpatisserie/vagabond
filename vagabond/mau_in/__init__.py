"""Các mẫu in của tiệm, do MÃ NGUỒN giữ chứ không để trôi nổi trong cơ sở dữ liệu.

  thuong_hieu.py  font va logo theo bo nhan dien, nhung dang data URI
  khuon/          cac khuon Jinja cua phan he bao gia: The Executive,
                  The Lookbook, The Legal Addendum, The Heritage
  *.html          cac mau in khai trong MAU_IN ben duoi, may tu day xuong
                  co so du lieu moi lan Migrate

VÌ SAO MẪU IN PHẢI NẰM Ở ĐÂY
----------------------------
Print Format sửa thẳng trên Desk nằm trong bảng `tabPrint Format` của cơ sở
dữ liệu. Git không quản, không có lịch sử, không ai kiểm chéo được, và nếu
lỡ tay xoá thì không khôi phục được - đúng cái rủi ro đã ghi trong AGENTS.md
với Server Script.

Ngày 21/08/2026 anh Việt in thử Chứng từ thanh toán và thấy ô Mã NCC ra tên
công ty, bảng Nội dung để trống. Lúc đi tìm thì mẫu in không có trong repo,
phải mở Desk mới đọc được. Từ nay mẫu in nằm ở đây, mỗi lần Migrate thì máy
tự đồng bộ xuống cơ sở dữ liệu.

CÁCH DÙNG
---------
Thêm một mẫu: bỏ tệp .html vào thư mục này rồi khai vào MAU_IN bên dưới.
Sửa một mẫu: sửa tệp .html, deploy, patch tự cập nhật.

Máy chỉ ghi đè khi nội dung THỰC SỰ khác, để khỏi đụng vào `modified` của
bản ghi mỗi lần migrate.
"""

import os

import frappe

# ten ban ghi Print Format  ->  (tep .html, doctype)
MAU_IN = {
	"Vagabond - Chứng từ thanh toán": ("chung_tu_thanh_toan.html", "Payment Entry"),
	# Keo ve repo 23/08/2026 khi sua ma vach. Truoc do mau nay chi song trong
	# co so du lieu, khong ai doc duoc neu khong mo Desk.
	"Vagabond - Phiếu nhập kho": ("phieu_nhap_kho.html", "Purchase Receipt"),
	# Ban in A4 dan tuong bep, them 25/08/2026. Ban ghi Print Format duoc
	# tao lan dau boi `huong_dan_che_bien.dung_mau_in()`, con noi dung HTML
	# thi nhip nay giu dong bo nhu moi mau in khac.
	"Vagabond - Hướng dẫn chế biến": ("huong_dan_che_bien.html",
		"Vagabond Huong Dan Che Bien"),
}

# Le giay cua tung ban ghi Print Format. Bon o margin nam trong co so du lieu
# chu khong trong HTML, nen phai dat rieng - xem le_in.py de biet vi sao 15mm.
LE_BAN_GHI = ("margin_top", "margin_bottom", "margin_left", "margin_right")

GOC = os.path.dirname(os.path.abspath(__file__))


def doc_mau(ten_tep):
	"""Đọc một tệp mẫu in trong repo. Dùng chung cho patch và cho ca kiểm."""
	with open(os.path.join(GOC, ten_tep), encoding="utf-8") as f:
		return f.read()


def dong_bo():
	"""Đẩy mẫu in từ repo xuống cơ sở dữ liệu. Lặp lại được không giới hạn."""
	ra = {"da_sua": [], "giu_nguyen": [], "chua_co": []}
	for ten, (tep, doctype) in MAU_IN.items():
		try:
			moi = doc_mau(tep)
		except OSError:
			ra["chua_co"].append(ten)
			continue
		if not frappe.db.exists("Print Format", ten):
			# KHÔNG tự tạo mẫu mới ở đây. Tạo mẫu in là việc có chủ đích, và
			# một bản ghi sinh ra lặng lẽ trong lúc migrate thì không ai biết
			# nó từ đâu ra. Ghi nhận rồi thôi.
			ra["chua_co"].append(ten)
			continue
		cu = frappe.db.get_value("Print Format", ten, "html") or ""
		if cu.strip() == moi.strip():
			ra["giu_nguyen"].append(ten)
			continue
		frappe.db.set_value("Print Format", ten, "html", moi, update_modified=False)
		ra["da_sua"].append(ten)

	# Le giay: dat cho MOI mau in cua tiem, ke ca mau chua keo ve repo. Bon o
	# nay nam trong ban ghi chu khong trong HTML nen ha CSS xuong khong toi.
	from vagabond.mau_in.le_in import LE_MM, duoc_ap_le_chung

	for r in frappe.get_all(
		"Print Format",
		filters={"standard": "No", "name": ["like", "Vagabond%"]},
		fields=["name", "doc_type", "html"] + list(LE_BAN_GHI),
	):
		# Khong ap le chung cho ban in khac kho A4/A5, dien hinh la tem
		# 62x45mm. Xem duoc_ap_le_chung() trong le_in.py de biet vi sao.
		if not duoc_ap_le_chung(r.get("name"), r.get("doc_type"), r.get("html")):
			ra.setdefault("bo_qua_le", []).append(r.get("name"))
			continue
		if all(int(r.get(o) or 0) == LE_MM for o in LE_BAN_GHI):
			continue
		for o in LE_BAN_GHI:
			frappe.db.set_value("Print Format", r["name"], o, LE_MM, update_modified=False)
		ra.setdefault("da_dat_le", []).append(r["name"])
	return ra


# ---------------------------------------------------- soi lech bang tay
#
# Muc dich: lam cho chuyen "co nguoi sua tay tren Desk" HIEN RA, thay vi am
# tham.
#
# TU v288 Web Page KHONG con chi la anh chup nua: `vagabond/trang/dong_bo()`
# day chung xuong co so du lieu moi lan Migrate, y het mau in. Nen lech o day
# khong con nghia la "quen chup lai" ma la "co nguoi vua sua tay tren Desk
# SAU lan deploy gan nhat, va lan deploy toi se ghi de mat".
#
# CHAY HAM NAY TRUOC MOI LAN DEPLOY. Co lech thi keo ban tren site ve git
# truoc da, dung deploy de len.


def _bam(s):
	import hashlib

	return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:12]


@frappe.whitelist()
def soi_lech():
	"""So bản trên site với bản trong repo. Chỉ ĐỌC, không ghi gì.

	Trả về danh sách những chỗ lệch. Rỗng nghĩa là site và repo khớp nhau.
	"""
	from vagabond import trang
	from vagabond.mau_in.le_in import LE_MM

	lech = []

	# 1. Mau in: repo la nguon that, dong_bo() day xuong moi lan Migrate. Lech
	#    o day nghia la co nguoi sua tay SAU lan Migrate gan nhat.
	for ten, (tep, _dt) in MAU_IN.items():
		if not frappe.db.exists("Print Format", ten):
			lech.append({"loai": "Mẫu in", "ten": ten, "vi_sao": "chưa có trên site"})
			continue
		try:
			goc = doc_mau(tep)
		except OSError:
			lech.append({"loai": "Mẫu in", "ten": ten, "vi_sao": "thiếu tệp trong repo"})
			continue
		tren_site = frappe.db.get_value("Print Format", ten, "html") or ""
		if tren_site.strip() != goc.strip():
			lech.append({
				"loai": "Mẫu in", "ten": ten,
				"vi_sao": "nội dung lệch (site %s, repo %s)"
					% (_bam(tren_site.strip()), _bam(goc.strip())),
			})

	# 2. Web Page: tu v288 repo la nguon that. Lech o day la CANH BAO SAP MAT
	#    CODE cua nguoi vua sua tay, khong phai loi nhac chup lai.
	for route in sorted(trang.TRANG):
		ten = frappe.db.get_value("Web Page", {"route": route}, "name")
		if not ten:
			lech.append({"loai": "Trang web", "ten": route,
				"vi_sao": "chưa có bản ghi trên site"})
			continue
		moi = trang.doc_mot(route)
		if not moi:
			lech.append({"loai": "Trang web", "ten": route,
				"vi_sao": "thiếu tệp trong repo"})
			continue
		doc = frappe.get_doc("Web Page", ten)
		for truong in sorted(moi):
			tren_site = doc.get(truong)
			trong_repo = moi[truong]
			if isinstance(trong_repo, str) or isinstance(tren_site, str):
				a, b = (tren_site or "").strip(), (trong_repo or "").strip()
				if a == b:
					continue
				vi_sao = ("site %s, repo %s. Ai sửa tay trên Desk thì kéo về "
					"git TRƯỚC khi deploy, không thì deploy ghi đè mất."
					% (_bam(a), _bam(b)))
			else:
				if tren_site == trong_repo:
					continue
				vi_sao = "site %r, repo %r" % (tren_site, trong_repo)
			lech.append({
				"loai": "Trang web", "ten": "%s (%s)" % (route, truong),
				"vi_sao": vi_sao,
			})

	return {"lech": lech, "le_mm": LE_MM, "so_mau_in": len(MAU_IN),
		"so_trang": len(trang.TRANG)}
