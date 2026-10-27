"""v614: phân hệ Khách hàng (CRM) đợt 1 chạy câu SQL thật trên ERPNext.

Tầng khung dùng lớp Frappe giả nên không thấy câu SQL sai cột, sai cú pháp
MariaDB hay sai quan hệ giữa bảng. Ca này đi đúng đường của quầy, Sales và
giám đốc trên bench thật:
  1. lượt tính nhóm đêm ghi hồ sơ cho mọi khách, lượt thứ hai KHÔNG ghi đè
     đồng ý và Danh sách không quảng cáo;
  2. ghi đồng ý ở quầy, đọc hồ sơ, nhóm khách, bộ lọc, sổ đồng ý;
  3. lập chiến dịch, duyệt kịch bản, sửa kịch bản là mất duyệt, chốt danh sách:
     chỉ khách đã đồng ý và ngoài Danh sách không quảng cáo, đối chứng giữ
     đúng số, không chia Sales;
  4. sửa chiến dịch đã chốt trên Desk bị chặn; Sales gọi, khách xin ngừng thì
     sổ đồng ý ghi Từ chối; đo hiệu quả chạy được.

Bench có thể có sẵn khách của bộ dữ liệu nền, nên các phép so ở đây là BẤT
BIẾN trên cả danh sách (mọi dòng đã chốt đều đồng ý, không ai trong Danh sách
không quảng cáo) cộng số đếm trên đúng các khách ca này dựng.

Chạy trong điểm lưu của nen.py: tinh_nhom_dem(luu=False) không commit.
"""

import json

import frappe

from vagabond import crm
from vagabond.khung.kiem_that.nen import _DA_TAO, ca, dung, khong_nem, la


def _khach(i):
	kh = frappe.get_doc({
		"doctype": "Customer", "customer_name": "Khách CRM 614 %02d %s" % (i, frappe.generate_hash(length=5)),
		"customer_type": "Individual", "mobile_no": "09%08d" % (61400000 + i),
		"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
		"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),
	})
	kh.insert(ignore_permissions=True)
	_DA_TAO.append((kh.doctype, kh.name))
	return kh.name


def _sales():
	u = frappe.get_doc({"doctype": "User", "email": "kt614-sales-%s@example.invalid" % frappe.generate_hash(length=8),
		"first_name": "Sales CRM 614", "enabled": 1, "send_welcome_email": 0,
		"roles": [{"role": "Sales User"}]}).insert(ignore_permissions=True)
	_DA_TAO.append((u.doctype, u.name))
	return u.name


def _hs(khach, cot):
	return frappe.db.get_value(crm.DT_HO_SO, khach, cot)


@ca("v614 site: nhóm đêm giữ đồng ý, chốt chiến dịch chỉ khách đã đồng ý, đối chứng không chia Sales, Sales gọi ghi sổ đồng ý")
def _crm():
	kh = [_khach(i) for i in range(14)]
	sales = _sales()

	# 1. Lượt đêm đầu: mọi khách có hồ sơ.
	kq = khong_nem("tính nhóm đêm lần 1", lambda: crm.tinh_nhom_dem(luu=False))
	if not kq:
		return
	dung("đếm đủ khách", kq["so_khach"] >= 14)
	la("khách chưa mua có hồ sơ nhóm Chưa mua", [_hs(k, "nhom") for k in kh[:2]], ["Chưa mua", "Chưa mua"])
	la("số điện thoại chuẩn", _hs(kh[0], "sdt"), "0961400000")

	# 2. Quầy ghi đồng ý: 12 khách đồng ý gọi điện, 1 từ chối, 1 chưa hỏi.
	for k in kh[:12]:
		khong_nem("ghi đồng ý " + k, lambda k=k: crm.ghi_dong_y(k, json.dumps({"Gọi điện": "Đồng ý"}), "Quầy"))
	khong_nem("ghi từ chối", lambda: crm.ghi_dong_y(kh[12], {"Gọi điện": "Từ chối", "Zalo": "Từ chối"}, "Quầy"))
	khong_nem("đưa một số vào Danh sách không quảng cáo",
		lambda: crm.dat_khong_quang_cao(kh[11], 1, "Khách gọi lên xin không nhận"))
	la("nhật ký đồng ý: mỗi lần đổi một dòng",
		frappe.db.count(crm.DT_NHAT_KY, {"khach": ["in", kh]}), 12 + 2)
	nk = frappe.get_all(crm.DT_NHAT_KY, filters={"khach": kh[0]}, fields=["kenh", "trang_thai", "noi_ghi", "cau_hoi"])
	la("dòng quầy giữ câu đã đọc", [(r.kenh, r.trang_thai, r.noi_ghi, r.cau_hoi) for r in nk],
		[("Gọi điện", "Đồng ý", "Quầy", crm.CAU_HOI_DONG_Y)])
	la("quầy không hỏi lại khách đã đồng ý", crm.dong_y_cua(kh[0])["can_hoi"], 0)
	la("quầy hỏi khách chưa hỏi", crm.dong_y_cua(kh[13])["can_hoi"], 1)

	# 3. Lượt đêm thứ hai KHÔNG được ghi đè lời khách đã nói.
	khong_nem("tính nhóm đêm lần 2", lambda: crm.tinh_nhom_dem(luu=False))
	la("đồng ý còn nguyên sau lượt đêm", [_hs(k, "dy_goi") for k in (kh[0], kh[12], kh[13])],
		["Đồng ý", "Từ chối", "Chưa hỏi"])
	la("Danh sách không quảng cáo còn nguyên", int(_hs(kh[11], "khong_quang_cao") or 0), 1)
	la("nơi ghi còn nguyên", _hs(kh[0], "dy_noi"), "Quầy")

	# 4. Các màn đọc chạy được câu SQL thật.
	hs = khong_nem("hồ sơ khách", lambda: crm.ho_so_crm(kh[0]))
	if hs:
		la("hồ sơ: nhóm và đồng ý", (hs["nhom"], hs["dong_y"]["Gọi điện"], hs["dong_y"]["Zalo"]), ("Chưa mua", "Đồng ý", "Chưa hỏi"))
		la("hồ sơ: chưa có món, chưa có liên hệ", (hs["mon"], hs["lien_he"]), ([], []))
	nh = khong_nem("nhóm khách", lambda: crm.nhom_khach())
	if nh:
		chua = [n for n in nh["nhom"] if n["nhom"] == "Chưa mua"][0]
		dung("nhóm Chưa mua đếm đủ khách ca dựng", chua["so"] >= 14 and chua["goi"] >= 11)
		la("đủ sáu nhóm theo thứ tự", [n["nhom"] for n in nh["nhom"]], list(crm.NHOM))
	loc = {"nhom": ["Chưa mua"], "dong_y": ["Gọi điện"]}
	dl = khong_nem("xem khách theo bộ lọc", lambda: crm.ds_khach_loc(json.dumps(loc), 200))
	if dl:
		ma = {r.khach for r in dl["dong"]}
		dung("bộ lọc đồng ý gọi điện: có khách đồng ý", set(kh[:12]) <= ma)
		dung("bộ lọc đồng ý gọi điện: không có khách từ chối hay chưa hỏi", not ({kh[12], kh[13]} & ma))
	bl = khong_nem("lưu bộ lọc", lambda: crm.luu_bo_loc("Khách chưa mua đồng ý gọi", json.dumps(loc)))
	if bl:
		dung("bộ lọc đã lưu hiện ở Nhóm khách", any(b["name"] == bl["name"] for b in crm.nhom_khach()["bo_loc"]))
	sd = khong_nem("sổ đồng ý", lambda: crm.so_dong_y(trang_thai="Từ chối"))
	if sd:
		dung("sổ đồng ý lọc Từ chối có khách ca dựng", any(r.khach == kh[12] for r in sd["dong"]))
		dung("tổng gọi điện đồng ý", sd["tong"]["Gọi điện"].get("Đồng ý", 0) >= 12)
	# Codex #505 vòng 2: tìm khách cũ trong sổ và lấy tiếp trang sau, câu SQL thật.
	ten0 = frappe.db.get_value("Customer", kh[0], "customer_name")
	t1 = khong_nem("sổ đồng ý tìm theo tên", lambda: crm.so_dong_y(tim=ten0))
	if t1:
		dung("tìm tên ra đúng khách", any(r.khach == kh[0] for r in t1["dong"]))
	t2 = khong_nem("sổ đồng ý tìm theo số", lambda: crm.so_dong_y(tim="096 140 0000"))
	if t2:
		dung("tìm số có dấu cách ra đúng khách", any(r.khach == kh[0] for r in t2["dong"]))
		dung("tìm số không lẫn khách từ chối", not any(r.khach == kh[12] for r in t2["dong"]))
	t3 = khong_nem("sổ đồng ý trang sau", lambda: crm.so_dong_y(so_dong=1, bat_dau=1))
	if t3:
		la("trang sau đúng một dòng, còn nữa", (len(t3["dong"]), t3["bat_dau"], t3["con_nua"]), (1, 1, 1))

	# 5. Lập, duyệt, sửa kịch bản là mất duyệt.
	dat = {"ten": "Giáng sinh 2026 kiểm 614", "loc": {"nhom": ["Chưa mua"]}, "kenh_goi": 1, "kenh_zalo": 0,
		"kich_ban": "Dạ chào anh chị, tiệm có món mới mùa Giáng sinh", "noi_dung_zalo": "Chào {ten}",
		"ty_le_doi_chung": 10, "sales": [sales]}
	cd = khong_nem("lưu chiến dịch", lambda: crm.luu_chien_dich(json.dumps(dat)))
	if not cd:
		return
	_DA_TAO.append((crm.DT_CD, cd["name"]))
	la("chưa duyệt thì chưa chốt được", cd["ly_do_chua_chot"], "Kịch bản gọi chưa được duyệt. Nhờ giám đốc duyệt rồi chốt.")
	dc = cd["dong_chay"]
	dung("khung số: loại chưa đồng ý và Danh sách không quảng cáo",
		dc["chua_dong_y"] >= 2 and dc["khong_quang_cao"] >= 1 and dc["nhan"] + dc["doi_chung"] == dc["du_dieu_kien"])
	cd = crm.duyet_kich_ban(cd["name"])
	la("duyệt xong", (int(cd["kich_ban_duyet"]), cd["ly_do_chua_chot"]), (1, ""))
	dat["name"] = cd["name"]
	cd = crm.luu_chien_dich(json.dumps(dat))
	la("lưu lại y kịch bản: còn duyệt", int(cd["kich_ban_duyet"]), 1)
	dat["kich_ban"] += ", nhắc mã ưu đãi"
	cd = crm.luu_chien_dich(json.dumps(dat))
	la("sửa kịch bản: mất duyệt", int(cd["kich_ban_duyet"]), 0)
	cd = crm.duyet_kich_ban(cd["name"])
	# Codex PR #505: sửa kịch bản thẳng trên Desk cũng mất duyệt.
	desk = frappe.get_doc(crm.DT_CD, cd["name"])
	desk.kich_ban = (desk.kich_ban or "") + " (sửa trên Desk)"
	khong_nem("Desk sửa kịch bản bản nháp", lambda: desk.save(ignore_permissions=True))
	la("Desk sửa kịch bản: mất duyệt", int(frappe.db.get_value(crm.DT_CD, cd["name"], "kich_ban_duyet") or 0), 0)
	cd = crm.duyet_kich_ban(cd["name"])
	du_kien = cd["dong_chay"]

	# 6. Chốt.
	cd = khong_nem("chốt danh sách", lambda: crm.chot_chien_dich(cd["name"]))
	if not cd:
		return
	dong = frappe.get_all(crm.DT_CD_KHACH, filters={"chien_dich": cd["name"]}, fields=["name", "khach", "nhanh", "sales", "kenh_duoc", "trang_thai"])
	ma = {r.khach for r in dong}
	la("trạng thái", cd["trang_thai"], "Đang chạy")
	dung("khách đồng ý, ngoài danh sách cấm đều có mặt", set(kh[:11]) <= ma)
	dung("không có khách từ chối, chưa hỏi, trong Danh sách không quảng cáo", not ({kh[11], kh[12], kh[13]} & ma))
	hs_dong = {r.name: r for r in frappe.get_all(crm.DT_HO_SO, filters={"name": ["in", list(ma)]}, fields=["name", "dy_goi", "khong_quang_cao"])}
	dung("BẤT BIẾN: mọi khách đã chốt đều đồng ý gọi điện và ngoài danh sách cấm",
		all(hs_dong[k].dy_goi == "Đồng ý" and not int(hs_dong[k].khong_quang_cao or 0) for k in ma))
	dcs = [r for r in dong if r.nhanh == "Đối chứng"]
	nhan = [r for r in dong if r.nhanh == "Nhận"]
	la("đối chứng đúng số", len(dcs), crm.so_doi_chung(len(dong), 10))
	la("khớp số đã hiện trước khi chốt", (len(nhan), len(dcs)), (du_kien["nhan"], du_kien["doi_chung"]))
	dung("đối chứng không chia Sales", all(not r.sales for r in dcs))
	dung("nhóm nhận chia cho Sales", nhan and all(r.sales == sales for r in nhan))
	dung("kênh được liên hệ ghi trên dòng", all(r.kenh_duoc == "Gọi điện" for r in nhan))
	try:
		crm.chot_chien_dich(cd["name"])
		dung("chốt lần hai phải bị chặn", False)
	except frappe.ValidationError:
		pass

	# 7. Sửa trên Desk sau khi chốt bị chặn.
	doc = frappe.get_doc(crm.DT_CD, cd["name"])
	doc.ty_le_doi_chung = 30
	try:
		doc.save(ignore_permissions=True)
		dung("Desk sửa chiến dịch đã chốt phải bị chặn", False)
	except frappe.ValidationError as e:
		dung("câu chặn chỉ đường: " + str(e), "Mở app" in str(e))

	# 8. Sales gọi.
	goc = frappe.session.user
	frappe.set_user(sales)
	try:
		ds = khong_nem("danh sách gọi của Sales", lambda: crm.ds_goi_cua_toi(cd["name"]))
		if ds:
			la("Sales thấy đúng phần mình", len(ds["dong"]), len(nhan))
			la("tóm tắt số việc", crm.tong_quan()["viec_toi"] >= len(nhan), True)
		mot = [r for r in nhan if r.khach == kh[0]] or nhan[:1]
		khong_nem("ghi khách xin ngừng", lambda: crm.ghi_ket_qua(mot[0].name, "Không muốn nhận tin nữa", "đừng gọi nữa"))
		# Codex PR #505: mở lại danh sách thì dòng đó hết kênh liên hệ.
		lai = {r["name"]: r for r in crm.ds_goi_cua_toi(cd["name"])["dong"]}
		la("khách vừa từ chối: hết nút liên hệ", (lai[mot[0].name]["kenh_duoc"], lai[mot[0].name]["ngung"]), ("", 1))
		if dcs:
			try:
				crm.ghi_ket_qua(dcs[0].name, "Quan tâm")
				dung("đối chứng không được ghi kết quả", False)
			except frappe.ValidationError:
				pass
	finally:
		frappe.set_user(goc)
	k0 = frappe.db.get_value(crm.DT_CD_KHACH, mot[0].name, ["trang_thai", "so_lan"], as_dict=True)
	la("dòng gọi xong", (k0.trang_thai, int(k0.so_lan)), ("Đã xong", 1))
	la("sổ đồng ý ghi Từ chối cả hai kênh", (_hs(mot[0].khach, "dy_goi"), _hs(mot[0].khach, "dy_zalo")), ("Từ chối", "Từ chối"))
	la("có dòng nhật ký Sales gọi",
		frappe.db.count(crm.DT_NHAT_KY, {"khach": mot[0].khach, "noi_ghi": "Sales gọi", "chien_dich": cd["name"]}), 2)
	la("nhật ký liên hệ trên hồ sơ", len(crm.ho_so_crm(mot[0].khach)["lien_he"]), 1)

	# 9. Đo hiệu quả và danh sách chiến dịch.
	hq = khong_nem("hiệu quả chiến dịch", lambda: crm.hieu_qua_chien_dich(cd["name"]))
	if hq:
		la("hai nhóm đúng số khách", (hq["nhan"]["so_khach"], hq["doi_chung"]["so_khach"]), (len(nhan), len(dcs)))
		la("khách xin ngừng", hq["khach_tu_choi"], 1)
		la("có đối chứng", hq["co_doi_chung"], 1 if dcs else 0)
		la("theo Sales: đã gọi xong một khách", [(r.sales, int(r.da_xong)) for r in hq["theo_sales"]], [(sales, 1)])
	dsc = khong_nem("danh sách chiến dịch", lambda: crm.ds_chien_dich())
	if dsc:
		c = [x for x in dsc["ds"] if x.name == cd["name"]][0]
		la("tiến độ gọi", c["tien_do"].get("Đã xong"), 1)
	khong_nem("kết thúc chiến dịch", lambda: crm.ket_thuc_chien_dich(cd["name"]))
	la("đã kết thúc", frappe.db.get_value(crm.DT_CD, cd["name"], "trang_thai"), "Đã kết thúc")
