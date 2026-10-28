"""v617: Khách hàng đợt 2 chạy câu SQL thật trên ERPNext.

Bench #510 đỏ ở 878fb55 và 4ac5204 vì ca v614 chưa theo hợp đồng mới (lưu
chiến dịch phải gửi mốc sửa). Bài học đi kèm: các phần mới của đợt 2 cũng
chưa từng chạy trên MariaDB thật, tầng khung chỉ có lớp Frappe giả. Ca này đi
đúng đường của khách, quầy và quản lý:
  1. màn Danh sách khách hàng: xếp chi nhiều nhất lên đầu và cộng trên đủ nhóm
     bằng câu truy vấn thật, ở mọi chip lọc;
  2. khách quan tâm OA rồi chia sẻ số: máy nối khách, ghi đồng ý Zalo nơi
     "Zalo OA"; khách bỏ quan tâm thì không vào danh sách OA;
  3. chiến dịch chỉ có Zalo OA, chương trình "Mã dùng một lần": chốt không cần
     Sales, phát mỗi khách một mã riêng trong lô của chiến dịch;
  4. gửi nền đọc lại đồng ý trước mỗi tin: khách rút đồng ý thì Bỏ qua. Cờ
     kiểm thử chặn gửi ra Zalo, nên dòng còn lại ghi Lỗi kèm câu chặn.

Chạy trong điểm lưu của nen.py; mọi commit bị khoá, mọi thứ lùi sau ca.
"""

import frappe

from vagabond import crm, khach_hang, zalo_oa
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, khong_nem, la


@ca("v617 site: Danh sách khách hàng xếp và cộng trên đủ nhóm bằng câu SQL thật")
def _ds_khach():
	for kw in ({}, {"dang": "si"}, {"dang": "le"}, {"hang": "_chua"}, {"tu_khoa": "Khách"}):
		r = khong_nem("danh sách khách %s" % kw, lambda kw=kw: khach_hang.ds_khach(**kw))
		if not r:
			continue
		tien = [x["tien"] for x in r["khach"]]
		dung("chi nhiều nhất lên đầu %s" % kw, tien == sorted(tien, reverse=True))
		dung("dòng tổng đếm trên đủ nhóm, không ít hơn số đã tải %s" % kw, r["tong_so"] >= r["da_tai"])
		la("số sỉ cộng số lẻ bằng tổng %s" % kw, r["so_si"] + r["so_le"], r["tong_so"])


def _khach(i, so):
	kh = frappe.get_doc({
		"doctype": "Customer", "customer_name": "Khách OA 617 %d %s" % (i, frappe.generate_hash(length=5)),
		"customer_type": "Individual", "mobile_no": so,
		"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
		"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),
	})
	kh.insert(ignore_permissions=True)
	_DA_TAO.append((kh.doctype, kh.name))
	return kh.name


def _ctkm():
	km = frappe.get_doc({
		"doctype": "Vagabond CTKM", "ten": "Kiểm 617 mã riêng", "cach_thuc": "Giam tong hoa don",
		"kieu_giam": "Phan tram", "gia_tri": 10, "pham_vi": "Ca hoa don", "doi_tuong": "Moi khach",
		"cach_ma": "Ma dung mot lan", "bat": 1,
	}).insert(ignore_permissions=True)
	_DA_TAO.append((km.doctype, km.name))
	return km.name


@ca("v617 site: Zalo OA chia sẻ số ghi đồng ý, chiến dịch chỉ OA chốt không cần Sales, mã riêng từng khách, gửi nền đọc lại đồng ý")
def _oa():
	uid = ["kt617%s" % frappe.generate_hash(length=8) for _ in range(3)]
	so = ["09%08d" % (61700000 + i) for i in range(3)]
	# Khách cũ đã có số trong sổ (ca thường gặp nhất ở quầy). Bench không có
	# nhóm khách "Khách lẻ" của site thật nên đường tạo khách mới không chạy ở
	# đây (bench lượt đầu đỏ đúng vì vậy); đường đó đã có ca ở tầng khung.
	kh_cu = [_khach(i, so[i]) for i in range(3)]
	for i, u in enumerate(uid):
		khong_nem("quan tâm OA " + u, lambda u=u: zalo_oa.xu_ly_su_kien({"event_name": "follow", "follower": {"id": u}}))
		khong_nem("chia sẻ số " + u, lambda u=u, i=i: zalo_oa.xu_ly_su_kien({
			"event_name": "user_submit_info", "sender": {"id": u},
			"info": {"name": "Khách OA 617 %d" % i, "phone": so[i]}}))
	qt = {r.name: r for r in frappe.get_all(zalo_oa.DT_QUAN_TAM, filters={"name": ["in", uid]},
		fields=["name", "khach", "trang_thai", "sdt"])}
	for u in qt:
		_DA_TAO.append((zalo_oa.DT_QUAN_TAM, u))
	la("mỗi người quan tâm đúng một dòng", len(qt), 3)
	kh = [qt[u].khach for u in uid if u in qt]
	la("chia sẻ số thì nối đúng khách cũ có số đó", kh, kh_cu)
	if kh != kh_cu:
		return
	la("số chuẩn hoá ghi trên dòng quan tâm", qt[uid[0]].sdt, so[0])
	nk = frappe.get_all(crm.DT_NHAT_KY, filters={"khach": kh[0], "kenh": "Zalo"},
		fields=["trang_thai", "noi_ghi", "cau_hoi"])
	la("nhật ký: khách tự đồng ý qua OA, giữ nguyên câu đã hỏi",
		[(r.trang_thai, r.noi_ghi, r.cau_hoi) for r in nk], [("Đồng ý", "Zalo OA", crm.CAU_HOI_OA)])
	hs = khong_nem("hồ sơ khách đọc trạng thái OA", lambda: crm.ho_so_crm(kh[0]))
	if hs:
		la("hồ sơ thấy khách đang quan tâm OA", int(hs.get("oa") or 0), 1)
	khong_nem("tấm hỏi đồng ý ở quầy", lambda: crm.dong_y_cua(kh[0]))
	khong_nem("bỏ quan tâm OA", lambda: zalo_oa.xu_ly_su_kien({"event_name": "unfollow", "follower": {"id": uid[2]}}))
	la("bỏ quan tâm ghi trên dòng", frappe.db.get_value(zalo_oa.DT_QUAN_TAM, uid[2], "trang_thai"), "Đã bỏ quan tâm")

	ctkm = khong_nem("chương trình Mã dùng một lần", _ctkm)
	dat = {"ten": "Kiểm 617 chỉ Zalo OA", "loc": {"dong_y": ["Zalo"]}, "kenh_goi": 0, "kenh_zalo": 0, "kenh_oa": 1,
		"tieu_de_oa": "Ưu đãi kiểm 617", "noi_dung_zalo": "Chào {ten}, tiệm gửi mã {ma} cho mùa lễ năm nay",
		"ctkm": ctkm, "ty_le_doi_chung": 0, "sales": []}
	cd = khong_nem("lưu chiến dịch chỉ OA", lambda: crm.luu_chien_dich(frappe.as_json(dat)))
	if not cd:
		return
	_DA_TAO.append((crm.DT_CD, cd["name"]))
	la("chỉ OA thì không cần Sales", (int(cd["can_sales"]), cd["ly_do_chua_chot"]),
		(0, "Nội dung chưa được duyệt. Nhờ giám đốc duyệt rồi chốt."))
	cd = khong_nem("duyệt nội dung", lambda: crm.duyet_kich_ban(cd["name"]))
	if not cd:
		return
	la("duyệt xong là chốt được", cd["ly_do_chua_chot"], "")
	cd = khong_nem("chốt danh sách chỉ OA", lambda: crm.chot_chien_dich(cd["name"]))
	if not cd:
		return
	dong = frappe.get_all(crm.DT_CD_KHACH, filters={"chien_dich": cd["name"]},
		fields=["name", "khach", "nhanh", "sales", "kenh_duoc", "ma_uu_dai"], order_by="ten_khach")
	la("chỉ hai khách đang quan tâm vào danh sách", sorted(r.khach for r in dong), sorted(kh[:2]))
	dung("không chia Sales", all(not r.sales for r in dong))
	dung("kênh được liên hệ là Zalo OA", all(r.kenh_duoc == crm.KENH_OA for r in dong))
	if ctkm:
		ma = [r.ma_uu_dai for r in dong]
		dung("mỗi khách một mã riêng, không trùng", all(ma) and len(set(ma)) == len(ma))
		lo = frappe.db.get_value(crm.DT_CD, cd["name"], "lo_voucher")
		dung("mã nằm trong lô riêng của chiến dịch", bool(lo))
		if lo:
			_DA_TAO.append(("Vagabond Lo Voucher", lo))
			vc = frappe.get_all("Vagabond Voucher", filters={"chien_dich": cd["name"]}, fields=["ma", "lo", "danh_cho"])
			la("mã trong kho voucher đúng lô, đúng khách",
				sorted((v.ma, v.lo, v.danh_cho) for v in vc), sorted((r.ma_uu_dai, lo, r.khach) for r in dong))
		hq = khong_nem("hiệu quả đếm mã riêng", lambda: crm.hieu_qua_chien_dich(cd["name"]))
		if hq:
			la("mã riêng đã dùng 0 / 2", (hq["ma_rieng_dung"], hq["ma_rieng"]), (0, 2))

	# Khách thứ hai rút đồng ý Zalo sau lúc chốt, trước khi việc nền gửi.
	rut = [r.khach for r in dong if r.khach == kh[1]]
	if rut:
		khong_nem("khách rút đồng ý Zalo", lambda: crm.ghi_dong_y(rut[0], {"Zalo": "Từ chối"}, "Quầy"))
	khong_nem("gửi nền", lambda: zalo_oa.gui_nen(cd["name"]))
	kq = {r.khach: r for r in frappe.get_all(crm.DT_CD_KHACH, filters={"chien_dich": cd["name"]},
		fields=["khach", "oa_trang_thai", "oa_loi"])}
	if rut:
		la("khách rút đồng ý: Bỏ qua", kq[rut[0]].oa_trang_thai, "Bỏ qua")
	if kh[0] in kq:
		la("khách còn đồng ý: cờ kiểm thử chặn gửi nên ghi Lỗi", kq[kh[0]].oa_trang_thai, "Lỗi")
		dung("câu lỗi nói rõ là đang kiểm thử", "kiểm thử" in (kq[kh[0]].oa_loi or ""))
	la("chiến dịch ghi gửi xong", frappe.db.get_value(crm.DT_CD, cd["name"], "oa_trang_thai"), "Đã gửi xong")
	khong_nem("kết thúc chiến dịch", lambda: crm.ket_thuc_chien_dich(cd["name"]))
