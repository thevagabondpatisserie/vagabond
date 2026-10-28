# -*- coding: utf-8 -*-
"""v617: phân hệ Khách hàng đợt 2 và màn Danh sách khách hàng.

Anh Việt 28/10/2026: "Làm luôn đi em. Và triển khai luôn đợt 2. OA Tăng
trưởng bên anh có rồi." Bốn việc anh chọn, mỗi việc chốt bằng hàm THẬT:
  1. Zalo OA "Mời quan tâm": chữ ký sự kiện, nối người quan tâm với hồ sơ,
     ghi đồng ý nơi ghi Zalo OA kèm câu đã hỏi; chiến dịch có kênh OA thì máy
     gửi tin Truyền thông, chỉ khách còn đồng ý VÀ còn quan tâm OA;
  2. mỗi khách một mã ưu đãi riêng, phát lúc chốt, đối chứng không có mã;
  3. so phiên bản khi lưu chiến dịch (hai người cùng sửa);
  4. ô nhận ưu đãi trên web: khách TỰ tích mới ghi, lỗi không hỏng đơn.
Cùng với đó màn Danh sách khách hàng xếp và cộng tiền trên ĐỦ nhóm đang lọc
(khach_thuan.py), không còn lấy 400 khách đầu bảng chữ cái.

Phần chạm hệ chạy trên lớp Frappe giả của nen.py, mỗi ca vá đúng lời gọi mà
hàm thật dùng, không gọi thêm hàm nội bộ nào "cho chắc" (điều 15).
"""

import hashlib
import json
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import crm, khach_thuan, zalo_oa  # noqa: E402


class D(dict):
	__getattr__ = dict.get

	def __setattr__(self, k, v):
		self[k] = v

	def as_dict(self):
		return dict(self)


# ------------------------------------------------------------ 1. Zalo OA, phần thuần

def _ky(app, than, ts, khoa):
	return "mac=" + hashlib.sha256((app + than + ts + khoa).encode("utf-8")).hexdigest()


@ca("v617 Zalo OA: chữ ký sự kiện đúng mới nhận; thiếu khoá, sai một chữ, thiếu chữ ký đều từ chối")
def _ky_su_kien():
	than = '{"event_name":"follow","timestamp":"1730000000000","follower":{"id":"U1"}}'
	ky = _ky("app1", than, "1730000000000", "bi-mat")
	dung("đúng", zalo_oa.chu_ky_dung("app1", than, "1730000000000", "bi-mat", ky))
	dung("thiếu mac= vẫn nhận", zalo_oa.chu_ky_dung("app1", than, "1730000000000", "bi-mat", ky[4:]))
	dung("thân dạng bytes", zalo_oa.chu_ky_dung("app1", than.encode("utf-8"), "1730000000000", "bi-mat", ky))
	dung("sửa một chữ trong thân", not zalo_oa.chu_ky_dung("app1", than.replace("U1", "U2"), "1730000000000", "bi-mat", ky))
	dung("khoá khác", not zalo_oa.chu_ky_dung("app1", than, "1730000000000", "khac", ky))
	dung("chưa khai khoá: không ai giả được", not zalo_oa.chu_ky_dung("app1", than, "1730000000000", "", _ky("app1", than, "1730000000000", "")))
	dung("thiếu chữ ký", not zalo_oa.chu_ky_dung("app1", than, "1730000000000", "bi-mat", ""))


@ca("v617 Zalo OA: đọc ba sự kiện quan tâm, bỏ quan tâm, chia sẻ số; sự kiện khác bỏ qua")
def _su_kien():
	la("quan tâm", zalo_oa.doc_su_kien({"event_name": "follow", "follower": {"id": "U1"}}), ("quan_tam", "U1", {}))
	la("bỏ quan tâm", zalo_oa.doc_su_kien({"event_name": "unfollow", "follower": {"id": "U1"}}), ("bo_quan_tam", "U1", {}))
	la("chia sẻ", zalo_oa.doc_su_kien({"event_name": "user_submit_info", "sender": {"id": "U2"},
		"info": {"name": " Lan ", "phone": "84909123456"}}), ("chia_se", "U2", {"ten": "Lan", "sdt": "84909123456"}))
	la("tin nhắn thường", zalo_oa.doc_su_kien({"event_name": "user_send_text"}), ("", "", {}))
	la("rác", zalo_oa.doc_su_kien("x"), ("", "", {}))


@ca("v617 Zalo OA: thân tin Truyền thông có tiêu đề, tin, bảng mã và hạn, nút Đặt bánh; không mã thì không có bảng")
def _than_tin():
	t = zalo_oa.than_truyen_thong("U1", "Quà Giáng sinh", "Chào Lan, mã XMAS1", "XMAS1", "24/12/2026", "https://a/b.jpg", "https://web")
	p = t["message"]["attachment"]["payload"]
	la("người nhận", t["recipient"], {"user_id": "U1"})
	la("mẫu", (p["template_type"], p["language"]), ("promotion", "VI"))
	la("các khối", [e["type"] for e in p["elements"]], ["banner", "header", "text", "table"])
	la("bảng mã", p["elements"][3]["content"], [{"key": "Mã ưu đãi", "value": "XMAS1"}, {"key": "Dùng đến", "value": "24/12/2026"}])
	la("nút", p["buttons"], [{"title": "Đặt bánh", "type": "oa.open.url", "payload": {"url": "https://web"}}])
	p2 = zalo_oa.than_truyen_thong("U1", "", "Chào Lan")["message"]["attachment"]["payload"]
	la("không ảnh, không mã, không nút", ([e["type"] for e in p2["elements"]], "buttons" in p2), (["header", "text"], False))
	la("tiêu đề trống dùng mặc định", p2["elements"][0]["content"], zalo_oa.TIEU_DE_MAC_DINH)
	h = zalo_oa.than_hoi_sdt("U9", "Nhận ưu đãi", crm.CAU_HOI_OA)
	la("tin hỏi số", h["message"]["attachment"]["payload"]["template_type"], "request_user_info")
	la("tin hỏi số mang nguyên câu đã hỏi", h["message"]["attachment"]["payload"]["elements"][0]["subtitle"], crm.CAU_HOI_OA)
	la("Zalo nhận", zalo_oa.ket_qua_zalo({"error": 0}), (True, ""))
	dung("Zalo từ chối kèm mã", zalo_oa.ket_qua_zalo({"error": -213, "message": "User has not followed OA"})[1].endswith("(mã -213)"))
	la("trả lời lạ", zalo_oa.ket_qua_zalo({}), (False, "Zalo không trả lời rõ ràng"))
	la("link mời", zalo_oa.link_oa(" 123 "), "https://zalo.me/123")
	la("chưa khai OA", zalo_oa.link_oa(""), "")
	la("ngày", zalo_oa.ngay_vn("2026-12-24"), "24/12/2026")


# ------------------------------------------------------------ 1b. CRM, phần thuần

@ca("v617 kênh Zalo OA: chỉ khách đồng ý Zalo VÀ đang quan tâm OA; bỏ quan tâm hay rút đồng ý thì không còn kênh")
def _kenh_oa():
	cd = {"kenh_oa": 1}
	la("kênh của chiến dịch", crm.kenh_cua_chien_dich(cd), ["Zalo OA"])
	la("đủ hai điều kiện", crm.kenh_lien_he_luc_nay({"dy_zalo": "Đồng ý", "oa": 1}, cd), ["Zalo OA"])
	la("đồng ý mà chưa quan tâm OA", crm.kenh_lien_he_luc_nay({"dy_zalo": "Đồng ý", "oa": 0}, cd), [])
	la("quan tâm mà từ chối Zalo", crm.kenh_lien_he_luc_nay({"dy_zalo": "Từ chối", "oa": 1}, cd), [])
	la("Danh sách không quảng cáo", crm.kenh_lien_he_luc_nay({"dy_zalo": "Đồng ý", "oa": 1, "kqc": 1}, cd), [])
	m = crm.menh_de_dong_y(["Zalo OA"])
	dung("mệnh đề SQL đòi đồng ý Zalo", "h.dy_zalo, '') = 'Đồng ý'" in m)
	dung("mệnh đề SQL đòi đang quan tâm, đúng bảng người quan tâm", "`tabVagabond Zalo Quan Tam`" in m and "'Đang quan tâm'" in m)
	la("kênh lạ không mở cửa", crm.menh_de_dong_y(["Fax"]), "1 = 0")


@ca("v617 chốt: chỉ Zalo OA thì không cần Sales; kênh nào cũng phải có chữ; duyệt bao cả tin Zalo")
def _ly_do_oa():
	tin = "Chào {ten}, The Vagabond tặng anh chị mã {ma} mùa Giáng sinh"
	cd = {"trang_thai": "Nháp", "kenh_oa": 1, "loc": {"nhom": ["Mới"]}, "kich_ban_duyet": 1, "noi_dung_zalo": tin}
	la("OA không Sales: chốt được", crm.ly_do_chua_chot(cd, 0), "")
	dung("OA thiếu tin Zalo", "tin Zalo" in crm.ly_do_chua_chot(dict(cd, noi_dung_zalo="ngắn"), 0))
	dung("thêm gọi điện thì cần kịch bản", "kịch bản gọi" in crm.ly_do_chua_chot(dict(cd, kenh_goi=1), 2))
	dung("gọi điện có kịch bản mà thiếu Sales", "Sales" in crm.ly_do_chua_chot(dict(cd, kenh_goi=1, kich_ban="Dạ chào anh chị, tiệm có món mới"), 0))
	la("cần Sales", (crm.can_sales({"kenh_oa": 1}), crm.can_sales({"kenh_oa": 1, "kenh_zalo": 1})), (False, True))
	a = crm.noi_dung_duyet({"kich_ban": "KB", "noi_dung_zalo": "Tin 1"})
	b = crm.noi_dung_duyet({"kich_ban": "KB", "noi_dung_zalo": "Tin 2"})
	la("sửa tin Zalo là mất duyệt", crm.duyet_sau_sua(a, 1, b, 1, False), 0)
	la("khoảng trắng đầu cuối không tính", crm.duyet_sau_sua(a, 1, crm.noi_dung_duyet({"kich_ban": " KB ", "noi_dung_zalo": "Tin 1 "}), 1, False), 1)
	la("tin có mã", crm.tin_zalo_khach(tin, "Lan", "AB12CD"), "Chào Lan, The Vagabond tặng anh chị mã AB12CD mùa Giáng sinh")
	dung("không mã thì không lộ chữ {ma}", "{ma}" not in crm.tin_zalo_khach(tin, "Lan", ""))


@ca("v617 thanh 5 bước: Soạn, Duyệt, Chốt, Đang liên hệ, Kết thúc đúng theo trạng thái chiến dịch")
def _buoc():
	tin = "Dạ chào anh chị, tiệm có món mới mùa Giáng sinh"
	b = crm.buoc_chien_dich
	la("nháp trống", b({"trang_thai": "Nháp"}), 0)
	la("đủ kênh, nhóm, chữ: chờ duyệt", b({"trang_thai": "Nháp", "kenh_goi": 1, "loc": {"nhom": ["Mới"]}, "kich_ban": tin}), 1)
	la("thiếu nhóm vẫn là soạn", b({"trang_thai": "Nháp", "kenh_goi": 1, "kich_ban": tin}), 0)
	la("đã duyệt: chờ chốt", b({"trang_thai": "Nháp", "kich_ban_duyet": 1}), 2)
	la("đang chạy", b({"trang_thai": "Đang chạy"}), 3)
	la("kết thúc: xong cả 5", b({"trang_thai": "Đã kết thúc"}), 5)
	la("năm bước", len(crm.BUOC_CD), 5)


@ca("v617 so phiên bản: cùng mốc mới cho lưu; khác mốc, thiếu mốc là bản cũ; chữ T và cách ghi ngày không làm lệch")
def _phien_ban():
	f = crm.cung_phien_ban
	dung("cùng", f("2026-10-28 10:00:00.123456", "2026-10-28 10:00:00.123456"))
	dung("chữ T", f("2026-10-28T10:00:00.123456", "2026-10-28 10:00:00.123456"))
	dung("datetime ở máy chủ", f("2026-10-28 10:00:00.123456", __import__("datetime").datetime(2026, 10, 28, 10, 0, 0, 123456)))
	dung("khác một phần triệu giây", not f("2026-10-28 10:00:00.123456", "2026-10-28 10:00:00.123457"))
	dung("thiếu mốc", not f("", "2026-10-28 10:00:00.123456"))
	dung("None", not f(None, "2026-10-28 10:00:00"))


# ------------------------------------------------------------ 2. chạm hệ: lưu, chốt, mã riêng

def _cd(**k):
	doc = D(name="CD-26-0009", ten="Tết 2027", trang_thai="Nháp", loc=json.dumps({"nhom": ["Đã ngủ"]}),
		kenh_goi=0, kenh_zalo=0, kenh_oa=1, kich_ban="", noi_dung_zalo="Chào {ten}, mã của anh chị là {ma} dùng tới Tết",
		kich_ban_duyet=1, ty_le_doi_chung=10, ctkm="CTKM-7", han="2027-02-10", modified="2026-10-28 09:00:00.000001",
		modified_by="loan@x", tieu_de_oa="")
	doc.update(k)
	doc["sales"] = []
	doc["mon"] = []
	doc.get = lambda key, mac=None: dict.get(doc, key, mac)
	doc.as_dict = lambda: dict(doc)
	doc.set = lambda kk, v: dict.__setitem__(doc, kk, v)
	doc.append = lambda kk, v: doc[kk].append(D(v))
	return doc


@ca("v617 lưu chiến dịch: người khác vừa lưu (khác mốc) thì chặn và không ghi; cùng mốc thì lưu; sửa tin Zalo là mất duyệt")
def _luu_phien_ban():
	fr = crm.frappe
	doc = _cd()
	luu = []
	with um.patch.object(fr, "get_roles", lambda *a: ["Sales Manager"]), \
			um.patch.object(crm, "_cd", lambda n, khoa=False: doc), \
			um.patch.object(crm, "_luu_cd", lambda d: luu.append(dict(d))), \
			um.patch.object(crm, "doc_chien_dich", lambda n: {"name": n}), \
			um.patch.object(fr.db, "exists", lambda *a, **k: True), \
			um.patch.object(fr.db, "get_value", lambda *a, **k: D(cach_ma="Ma dung mot lan", ma_co_dinh="") if a and a[0] == "Vagabond CTKM" else "Loan"):
		dat = {"name": doc.name, "ten": doc.ten, "loc": {"nhom": ["Đã ngủ"]}, "kenh_oa": 1, "ctkm": "CTKM-7",
			"noi_dung_zalo": doc.noi_dung_zalo, "modified": "2026-10-28 08:59:00.000000"}
		nem("khác mốc: chặn", lambda: crm.luu_chien_dich(json.dumps(dat)))
		la("khác mốc: không ghi gì", luu, [])
		crm.luu_chien_dich(json.dumps(dict(dat, modified=doc.modified)))
		la("cùng mốc: lưu, giữ duyệt", (len(luu), doc.kich_ban_duyet), (1, 1))
		la("lưu kênh OA", doc.kenh_oa, 1)
		la("mã dùng một lần: chiến dịch không có mã chung", doc.ma_uu_dai, "")
		crm.luu_chien_dich(json.dumps(dict(dat, modified=doc.modified, noi_dung_zalo=doc.noi_dung_zalo + " nhé")))
		la("sửa tin Zalo: mất duyệt", doc.kich_ban_duyet, 0)
		nem("chiến dịch có sẵn mà màn không gửi mốc", lambda: crm.luu_chien_dich(json.dumps(dict(dat, modified=""))))


def _chot_moi_truong(doc, rows, km=None):
	fr = crm.frappe
	ghi = types.SimpleNamespace(bulk={}, lo=[], luu=[])

	class Lo(D):
		def insert(self, **k):
			# Chạy đúng validate của doctype thật (trần số mã một lô), không
			# để lớp giả nhận một lô mà site thật từ chối (Codex PR #510 vòng 3).
			from vagabond.vagabond.doctype.vagabond_lo_voucher.vagabond_lo_voucher import VagabondLoVoucher

			VagabondLoVoucher.validate(self)
			self["name"] = "LOV-26-%04d" % (len(ghi.lo) + 1)
			ghi.lo.append(dict(self))
			return self

	def bulk(dt_, cot, dong, **k):
		ghi.bulk.setdefault(dt_, []).extend(dict(zip(cot, d)) for d in dong)

	def gv(dt_, *a, **k):
		if dt_ == "Vagabond CTKM":
			return km
		if dt_ == "User":
			return "loan@x"
		return None

	ma = iter("M%05d" % i for i in range(20000))
	from vagabond import khuyen_mai  # noqa: F401  (đảm bảo nạp được trước khi vá)

	vas = [
		um.patch.object(fr, "get_roles", lambda *a: ["Sales Manager"]),
		um.patch.object(crm, "_cd", lambda n, khoa=False: doc),
		um.patch.object(crm, "_luu_cd", lambda d: ghi.luu.append(dict(d))),
		um.patch.object(crm, "doc_chien_dich", lambda n: {"name": n}),
		um.patch.object(fr.db, "sql", lambda q, *a, **k: rows),
		um.patch.object(fr.db, "get_value", gv),
		um.patch.object(fr.db, "bulk_insert", bulk, create=True),
		um.patch.object(fr, "generate_hash", lambda length=10: "h", create=True),
		um.patch.object(fr, "get_doc", lambda d, *a, **k: Lo(d)),
		um.patch("vagabond.khuyen_mai._sinh_ma_moi", lambda n: [next(ma) for _ in range(n)]),
	]
	return ghi, vas


def _rows(n=30):
	ra = []
	for i in range(n):
		ra.append(D(khach="K%02d" % i, ten="Khách %d" % i, sdt="09%08d" % i, dy_zalo="Đồng ý", dy_goi="", dy_email="",
			kqc=0, du=1, oa=1))
	return ra


def _khach_ca(ghi):
	"""crm nạp khach_hang (la_khach_gop) kéo requests; CI chạy tay không."""
	from vagabond.khung.kiem_thu import thu_crm_614

	return thu_crm_614._nen_ban()


@ca("v617 chốt chiến dịch OA với CTKM mã dùng một lần: mỗi khách nhóm Nhận một mã riêng, đối chứng không có mã, không chia Sales")
def _chot_ma_rieng():
	doc = _cd()
	ghi, vas = _chot_moi_truong(doc, _rows(), D(ten="Tết mã riêng", cach_ma="Ma dung mot lan", han_ma="2027-03-01", bat=1))
	with _khach_ca(ghi):
		for v in vas:
			v.start()
		try:
			crm.chot_chien_dich(doc.name)
		finally:
			for v in vas:
				v.stop()
	dong = ghi.bulk[crm.DT_CD_KHACH]
	nhan = [r for r in dong if r["nhanh"] == "Nhận"]
	dc = [r for r in dong if r["nhanh"] == "Đối chứng"]
	la("27 nhận, 3 đối chứng", (len(nhan), len(dc)), (27, 3))
	dung("không chia Sales khi chỉ có OA", all(not r["sales"] for r in dong))
	dung("mỗi khách nhận một mã", all(r["ma_uu_dai"] for r in nhan))
	la("mã không trùng", len({r["ma_uu_dai"] for r in nhan}), 27)
	dung("đối chứng không có mã", all(not r["ma_uu_dai"] for r in dc))
	v = ghi.bulk["Vagabond Voucher"]
	la("27 mã trong kho voucher", len(v), 27)
	la("mã gắn đúng khách", {r["danh_cho"]: r["ma"] for r in v}, {r["khach"]: r["ma_uu_dai"] for r in nhan})
	dung("mã gắn chiến dịch, lô, chưa dùng, hạn theo chiến dịch",
		all((r["chien_dich"], r["lo"], r["trang_thai"], r["han_dung"]) == (doc.name, "LOV-26-0001", "Chua dung", "2027-02-10") for r in v))
	la("một lô của chiến dịch", (len(ghi.lo), ghi.lo[0]["so_luong"], ghi.lo[0]["ctkm"]), (1, 27, "CTKM-7"))
	la("phiếu ghi lô", doc.lo_voucher, "LOV-26-0001")
	la("kênh ghi trên dòng", {r["kenh_duoc"] for r in dong}, {"Zalo OA"})


@ca("Codex PR #510 vòng 3: hơn 5.000 khách nhận mã riêng thì chia nhiều lô, chốt không bị chặn, mỗi mã ghi đúng lô của nó")
def _chot_nhieu_lo():
	doc = _cd()
	ghi, vas = _chot_moi_truong(doc, _rows(5600), D(ten="Tết đông khách", cach_ma="Ma dung mot lan", han_ma=None, bat=1))
	with _khach_ca(ghi):
		for v in vas:
			v.start()
		try:
			crm.chot_chien_dich(doc.name)
		finally:
			for v in vas:
				v.stop()
	nhan = [r for r in ghi.bulk.get(crm.DT_CD_KHACH, []) if r["nhanh"] == "Nhận"]
	la("5.040 khách nhận (10% đối chứng)", len(nhan), 5040)
	la("hai lô, lô nào cũng không quá 5.000 mã", [x["so_luong"] for x in ghi.lo], [5000, 40])
	v = ghi.bulk.get("Vagabond Voucher", [])
	la("đủ 5.040 mã, không trùng", (len(v), len({r["ma"] for r in v})), (5040, 5040))
	la("mỗi lô chứa đúng số mã đã khai", {lo: sum(1 for r in v if r["lo"] == lo) for lo in ("LOV-26-0001", "LOV-26-0002")},
		{"LOV-26-0001": 5000, "LOV-26-0002": 40})
	la("mã gắn đúng khách", {r["danh_cho"]: r["ma"] for r in v}, {r["khach"]: r["ma_uu_dai"] for r in nhan})
	la("phiếu ghi lô đầu", doc.lo_voucher, "LOV-26-0001")
	dung("ghi chú lô nói rõ lô mấy trên mấy", "lô 2/2" in ghi.lo[1]["ghi_chu"])


@ca("v617 chốt: CTKM mã cố định thì không phát mã riêng; CTKM đang tắt thì không chốt (mã phát ra sẽ không dùng được)")
def _chot_ma_co_dinh():
	doc = _cd()
	ghi, vas = _chot_moi_truong(doc, _rows(), D(ten="Mã chung", cach_ma="Ma co dinh", han_ma=None, bat=1))
	with _khach_ca(ghi):
		for v in vas:
			v.start()
		try:
			crm.chot_chien_dich(doc.name)
		finally:
			for v in vas:
				v.stop()
	dung("không có voucher", "Vagabond Voucher" not in ghi.bulk)
	dung("dòng không mang mã riêng", all(not r["ma_uu_dai"] for r in ghi.bulk[crm.DT_CD_KHACH]))
	doc2 = _cd()
	ghi2, vas2 = _chot_moi_truong(doc2, _rows(), D(ten="Tắt", cach_ma="Ma dung mot lan", bat=0))
	with _khach_ca(ghi2):
		for v in vas2:
			v.start()
		try:
			nem("CTKM tắt", lambda: crm.chot_chien_dich(doc2.name))
		finally:
			for v in vas2:
				v.stop()
	la("CTKM tắt: không ghi dòng nào", ghi2.bulk, {})


# ------------------------------------------------------------ 3. đồng ý: web và OA

def _gia_ho_so():
	ho_so, ghi = {}, []

	def get_value(dt_, name, cot=None, as_dict=False, **k):
		if dt_ == crm.DT_HO_SO:
			r = ho_so.get(name)
			return D(r) if r else None
		if dt_ == "Customer":
			return "Tên " + name
		return None

	def set_value(dt_, name, v, *a, **k):
		if dt_ == crm.DT_HO_SO and isinstance(v, dict):
			ho_so.setdefault(name, {}).update(v)

	class Doc(D):
		def insert(self, **k):
			ghi.append(dict(self))
			if self.get("doctype") == crm.DT_HO_SO:
				ho_so[self["khach"]] = dict(self)
			return self

	return ho_so, ghi, get_value, set_value, Doc


@ca("v617 nhân viên không ghi hộ được nơi ghi Web hay Zalo OA (chỉ máy ghi khi khách tự bấm)")
def _noi_ghi_may():
	fr = crm.frappe
	ho_so, ghi, gv, sv, Doc = _gia_ho_so()
	with _khach_ca(None), um.patch.object(fr, "get_roles", lambda *a: ["Sales User"]), \
			um.patch.object(fr.db, "get_value", gv), um.patch.object(fr.db, "set_value", sv), \
			um.patch.object(fr, "get_doc", lambda d, *a, **k: Doc(d)):
		crm.ghi_dong_y("KH-1", {"Zalo": "Đồng ý"}, "Web")
		crm.ghi_dong_y("KH-2", {"Zalo": "Đồng ý"}, "Zalo OA")
	nk = [d for d in ghi if d["doctype"] == crm.DT_NHAT_KY]
	la("đổi về Hồ sơ khách", [d["noi_ghi"] for d in nk], ["Hồ sơ khách", "Hồ sơ khách"])
	dung("người ghi là nhân viên", all(d["nguoi"] == "kiemthu@vagabond" for d in nk))


@ca("v617 web: khách tích ô nhận ưu đãi thì tìm hoặc dựng khách theo số, ghi Zalo và gọi điện Đồng ý, nơi ghi Web, kèm câu đã tích")
def _web_dong_y():
	fr = crm.frappe
	ho_so, ghi, gv, sv, Doc = _gia_ho_so()
	goi = []
	with _khach_ca(None), um.patch.object(fr.db, "get_value", gv), um.patch.object(fr.db, "set_value", sv), \
			um.patch.object(fr, "get_doc", lambda d, *a, **k: Doc(d)), \
			um.patch("vagabond.nhap_khach.khach_cho_don", lambda sdt, ten="", nguon="": (goi.append((sdt, ten)), "KH-77")[1]):
		kq = crm.ghi_dong_y_web("0909123456", "Lan", "DW-2610-00001")
	la("tìm theo đúng số và tên", goi, [("0909123456", "Lan")])
	la("trả mã khách", (kq["ok"], kq["doi"], kq["khach"]), (1, 2, "KH-77"))
	nk = [d for d in ghi if d["doctype"] == crm.DT_NHAT_KY]
	la("hai dòng nhật ký", sorted((d["kenh"], d["trang_thai"], d["noi_ghi"], d["nguoi"]) for d in nk),
		[("Gọi điện", "Đồng ý", "Web", "Guest"), ("Zalo", "Đồng ý", "Web", "Guest")])
	dung("câu đã tích kèm mã đơn", all(d["cau_hoi"].startswith(crm.CAU_HOI_WEB) and "DW-2610-00001" in d["cau_hoi"] for d in nk))
	with _khach_ca(None), um.patch("vagabond.nhap_khach.khach_cho_don", lambda *a, **k: ""):
		la("số lạ không gắn được khách: không ghi", crm.ghi_dong_y_web("12", "X"), {"ok": 0, "ly_do": "khong_gan_duoc_khach"})


@ca("v617 web: câu trên trang đặt bánh trùng tuyệt đối câu lưu làm bằng chứng; ô để trống sẵn")
def _web_cau():
	import io
	import os

	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	chu = json.load(io.open(os.path.join(goc, "public", "web_order", "chu-mac-dinh.json"), encoding="utf-8"))
	la("câu mặc định trên web", chu["uu_dai_nhan_tin"]["mac_dinh"], crm.CAU_HOI_WEB)
	kho = io.open(os.path.join(goc, "public", "web_vue", "banh", "kho-banh.js"), encoding="utf-8").read()
	dung("ô mặc định chưa tích", "uudai: false" in kho)
	dung("chỉ gửi true khi khách tích", "nhan_uu_dai: S.CO.uudai === true" in kho)


@ca("v617 đơn web: tích ô thì ghi đồng ý SAU khi đơn đã lưu; không tích hay gửi chữ 'true' thì không ghi; lỗi ghi không hỏng đơn")
def _web_tao_don():
	from vagabond.khung.kiem_thu import thu_don_web_367 as t367

	def chay(**them):
		vet, tao_don = t367._moi_truong_tao_don(lambda v: t367._Tra(200, {"data": {"id": "91500"}}))
		goi = []

		def ghi(sdt, ten, ma):
			vet.su.append("dong_y")
			goi.append((sdt, ten, ma))
			if them.pop("_loi", None):
				raise RuntimeError("hỏng sổ")
			return {"ok": 1}

		with _khach_ca(None), um.patch.object(crm, "ghi_dong_y_web", ghi):
			r = tao_don(t367._don(**them))
		return vet, goi, r

	vet, goi, r = chay(nhan_uu_dai=True)
	la("ghi đúng số, tên, mã đơn", goi, [("0931224334", "Nguyễn Văn An", "DW-2609-00001")])
	dung("ghi sau khi bản ghi đơn đã commit", vet.su.index("dong_y") > vet.su.index("commit") > vet.su.index("ghi"))
	la("đơn vẫn có biên nhận", r.get("ok"), 1)
	_, goi, _ = chay()
	la("không tích: không ghi", goi, [])
	_, goi, _ = chay(nhan_uu_dai="true")
	la("chữ 'true' không phải tích", goi, [])
	vet, goi, r = chay(nhan_uu_dai=True, _loi=True)
	la("lỗi sổ: đơn vẫn xong", r.get("ok"), 1)
	dung("lỗi sổ: lùi phần ghi, ghi Error Log", "rollback" in vet.su[vet.su.index("dong_y"):] and
		"Vagabond: ghi đồng ý nhận tin từ web" in vet.log)
	dung("vẫn gọi Pancake", "post" in vet.su)


@ca("v617 sự kiện OA: quan tâm thì ghi người quan tâm và hỏi số; chia sẻ số thì nối hồ sơ và ghi đồng ý Zalo OA; bỏ quan tâm thì đổi trạng thái")
def _xu_ly():
	fr = zalo_oa.frappe
	bang, xep, dy = {}, [], []

	def exists(dt_, name=None, *a, **k):
		return name in bang

	def get_value(dt_, name, cot=None, *a, **k):
		return (bang.get(name) or {}).get(cot)

	def set_value(dt_, name, v, *a, **k):
		bang[name].update(v)

	class Doc(D):
		def insert(self, **k):
			bang[self["uid"]] = dict(self)
			return self

	with um.patch.object(fr.db, "exists", exists), um.patch.object(fr.db, "get_value", get_value), \
			um.patch.object(fr.db, "set_value", set_value), um.patch.object(fr, "get_doc", lambda d, *a, **k: Doc(d)), \
			um.patch.object(fr, "enqueue", lambda m, **k: xep.append((m, k.get("uid"))), create=True), \
			um.patch.object(zalo_oa, "oa_dang_bat", lambda: True), \
			um.patch.object(crm, "ghi_dong_y_noi", lambda *a, **k: dy.append((a, k))), \
			um.patch("vagabond.nhap_khach.khach_cho_don", lambda sdt, ten="", nguon="": "KH-5" if sdt == "0909123456" else ""):
		la("quan tâm", zalo_oa.xu_ly_su_kien({"event_name": "follow", "follower": {"id": "U1"}}), "quan_tam")
		la("ghi người quan tâm", bang["U1"]["trang_thai"], "Đang quan tâm")
		la("xếp tin hỏi số", xep, [("vagabond.zalo_oa.hoi_sdt", "U1")])
		zalo_oa.xu_ly_su_kien({"event_name": "user_submit_info", "sender": {"id": "U1"}, "info": {"name": "Lan", "phone": "84909123456"}})
		la("nối hồ sơ theo số đã chuẩn", (bang["U1"]["khach"], bang["U1"]["sdt"]), ("KH-5", "0909123456"))
		la("ghi đồng ý Zalo, nơi ghi Zalo OA", dy[0][0][:3], ("KH-5", {"Zalo": "Đồng ý"}, "Zalo OA"))
		la("kèm câu đã hỏi, người ghi là khách", (dy[0][1]["cau_hoi"], dy[0][1]["nguoi"]), (crm.CAU_HOI_OA, "Guest"))
		zalo_oa.xu_ly_su_kien({"event_name": "follow", "follower": {"id": "U1"}})
		la("đã nối hồ sơ: quan tâm lại không hỏi số nữa", len(xep), 1)
		zalo_oa.xu_ly_su_kien({"event_name": "unfollow", "follower": {"id": "U1"}})
		la("bỏ quan tâm", bang["U1"]["trang_thai"], "Đã bỏ quan tâm")
		la("bỏ quan tâm UID lạ: không tạo dòng", (zalo_oa.xu_ly_su_kien({"event_name": "unfollow", "follower": {"id": "U9"}}), "U9" in bang), ("bo_quan_tam", False))
		zalo_oa.xu_ly_su_kien({"event_name": "user_submit_info", "sender": {"id": "U2"}, "info": {"name": "X", "phone": "abc"}})
		la("số rác: không ghi đồng ý", len(dy), 1)


@ca("v617 điểm nhận OA: chữ ký sai thì 401, không xử lý gì; đúng thì xử lý và commit")
def _diem_nhan():
	fr = zalo_oa.frappe
	than = '{"event_name":"follow","timestamp":"17","follower":{"id":"U1"}}'
	xl, cm = [], []
	cfg = D(zalo_app_id="app1")
	req = types.SimpleNamespace(get_data=lambda as_text=False: than)
	for ky, mong in (("mac=sai", 401), (_ky("app1", than, "17", "bi-mat"), None)):
		xl.clear()
		fr.local.response = {}
		with um.patch.object(fr, "request", req, create=True), \
				um.patch.object(fr, "get_request_header", lambda k, ky=ky: ky if k == "X-ZEvent-Signature" else "", create=True), \
				um.patch.object(zalo_oa, "_cfg", lambda: cfg), \
				um.patch("vagabond.lib.key", lambda c, f: "bi-mat" if f == "zalo_oa_khoa_webhook" else ""), \
				um.patch.object(zalo_oa, "xu_ly_su_kien", lambda g: xl.append(g) or "quan_tam"), \
				um.patch.object(fr.db, "commit", lambda: cm.append(1)):
			kq = zalo_oa.nhan_su_kien()
		if mong == 401:
			la("sai chữ ký: 401", (fr.local.response.get("http_status_code"), kq, xl), (401, {"ok": 0}, []))
		else:
			la("đúng chữ ký: xử lý", (kq, len(xl)), ({"ok": 1, "loai": "quan_tam"}, 1))
	dung("đã commit", cm)


@ca("v617 gửi OA nền: khách đủ điều kiện thì gửi và ghi Đã gửi kèm nhật ký liên hệ; khách rút đồng ý thì Bỏ qua không gọi Zalo; Zalo lỗi thì ghi Lỗi kèm câu")
def _gui_nen():
	fr = zalo_oa.frappe
	doc = D(name="CD-26-0009", owner="loan@x", kenh_oa=1, noi_dung_zalo="Chào {ten}, mã {ma}", tieu_de_oa="", han="2027-02-10")
	doc.as_dict = lambda: dict(doc)
	rows = [D(name="R1", khach="K1", ten_khach="An", ma_uu_dai="M1", dy_zalo="Đồng ý", kqc=0, uid="U1"),
		D(name="R2", khach="K2", ten_khach="Bình", ma_uu_dai="M2", dy_zalo="Từ chối", kqc=0, uid="U2"),
		D(name="R3", khach="K3", ten_khach="Chi", ma_uu_dai="M3", dy_zalo="Đồng ý", kqc=0, uid=None),
		D(name="R4", khach="K4", ten_khach="Dũng", ma_uu_dai="", dy_zalo="Đồng ý", kqc=0, uid="U4")]
	post, sv, lh = [], [], []

	def gia_post(duong, than):
		post.append((duong, than))
		uid = than["recipient"]["user_id"]
		return (True, "", {}) if uid == "U1" else (False, "Hết lượt tin tháng này (mã -32)", {})

	class Doc(D):
		def insert(self, **k):
			lh.append(dict(self))
			return self

	# Codex PR #510: việc nền đọc lại hồ sơ từng khách và trạng thái chiến dịch
	# ngay trước mỗi tin, nên lớp giả trả hồ sơ theo đúng câu truy vấn đó.
	ho_so = {r.khach: r for r in rows}

	def sql(q, ts=None, *a, **k):
		if "`tabVagabond Ho So CRM` h where h.name = %s" in q:
			return [ho_so[ts[0]]]
		return rows

	with um.patch.object(fr, "get_doc", lambda *a, **k: doc if a and a[0] == crm.DT_CD else Doc(a[0])), \
			um.patch.object(fr.db, "sql", sql), \
			um.patch.object(fr.db, "get_value", lambda dt_, n, cot=None, *a, **k: "Đang chạy" if cot == "trang_thai" else None), \
			um.patch.object(fr.db, "set_value", lambda dt_, n, v, *a, **k: sv.append((dt_, n, v))), \
			um.patch.object(zalo_oa, "_post", gia_post), \
			um.patch.object(zalo_oa, "_cfg", lambda: D(web_ten_mien_chinh="thevagabondpatisserie.com")), \
			um.patch.object(zalo_oa, "NGHI_GIUA_TIN", 0):
		dem = zalo_oa.gui_nen("CD-26-0009")
	la("đếm", dem, {"Đã gửi": 1, "Lỗi": 1, "Bỏ qua": 2})
	la("chỉ gọi Zalo cho khách đủ điều kiện", [p[1]["recipient"]["user_id"] for p in post], ["U1", "U4"])
	p0 = post[0][1]["message"]["attachment"]["payload"]
	la("tin mang tên và mã riêng của đúng khách", p0["elements"][1]["content"], "Chào An, mã M1")
	la("nút mở trang web", p0["buttons"][0]["payload"]["url"], "https://thevagabondpatisserie.com")
	tt = {n: v["oa_trang_thai"] for d, n, v in sv if d == crm.DT_CD_KHACH}
	la("trạng thái từng dòng", tt, {"R1": "Đã gửi", "R2": "Bỏ qua", "R3": "Bỏ qua", "R4": "Lỗi"})
	la("lỗi ghi câu Zalo", [v["oa_loi"] for d, n, v in sv if n == "R4"], ["Hết lượt tin tháng này (mã -32)"])
	la("nhật ký liên hệ chỉ cho tin đã gửi", [(r["khach"], r["kenh"]) for r in lh], [("K1", "Zalo OA")])
	cuoi = [v for d, n, v in sv if d == crm.DT_CD][-1]
	la("chiến dịch: gửi xong kèm tóm tắt", (cuoi["oa_trang_thai"], cuoi["oa_ket_qua"]), ("Đã gửi xong", "Đã gửi 1 khách, lỗi 1, bỏ qua 2."))


@ca("v617 gửi OA: kênh OA tắt trong Cài đặt, chiến dịch chưa chạy hay không chọn OA thì không xếp việc; đang gửi thì không xếp lần hai")
def _gui_chan():
	fr = zalo_oa.frappe
	xep = []
	for bat, tt, oa, dang, chan in ((False, "Đang chạy", 1, "", True), (True, "Nháp", 1, "", True),
			(True, "Đang chạy", 0, "", True), (True, "Đang chạy", 1, "Đang gửi", False), (True, "Đang chạy", 1, "", False)):
		doc = D(name="CD-1", trang_thai=tt, kenh_oa=oa, oa_trang_thai=dang)
		doc.get = lambda k, m=None, d=doc: dict.get(d, k, m)
		xep.clear()
		with um.patch.object(fr, "get_roles", lambda *a: ["Sales Manager"]), \
				um.patch.object(zalo_oa, "oa_dang_bat", lambda b=bat: b), \
				um.patch.object(crm, "_cd", lambda n, khoa=False, d=doc: d), \
				um.patch.object(fr, "enqueue", lambda m, **k: xep.append(m), create=True):
			if chan:
				nem("chặn %s %s %s" % (bat, tt, oa), lambda: zalo_oa.gui_chien_dich_oa("CD-1"))
				la("không xếp", xep, [])
			else:
				kq = zalo_oa.gui_chien_dich_oa("CD-1")
				la("đã gửi dở: không xếp thêm" if dang else "xếp một việc", (kq["dang_gui"], len(xep)), (1, 0 if dang else 1))
	with um.patch.object(fr, "get_roles", lambda *a: ["Sales User"]):
		nem("Sales thường không gửi được", lambda: zalo_oa.gui_chien_dich_oa("CD-1"))


# ------------------------------------------------------------ 4. Danh sách khách hàng

@ca("v617 Danh sách khách hàng: lọc sỉ, lẻ, hạng, chữ tìm ra đúng mệnh đề; chắc chắn rỗng thì không hỏi máy chủ")
def _ds_khach_dk():
	f = khach_thuan.dk_ds_khach
	w, ts = f(("Sỉ",), "si")
	dung("sỉ", "c.customer_group in %(nhom_si)s" in w and ts["nhom_si"] == ("Sỉ",))
	w, ts = f(("Sỉ",), "le")
	dung("lẻ gồm cả khách chưa có nhóm", "ifnull(c.customer_group, '') not in %(nhom_si)s" in w)
	la("chưa khai nhóm sỉ mà lọc sỉ", f((), "si"), None)
	w, ts = f((), "", "_chua")
	dung("chưa xếp hạng", "ifnull(c.vgb_hang, '') = ''" in w)
	la("lọc hạng khi site chưa có cột hạng", f((), "", "Vàng", co_hang=False), None)
	la("tìm không khớp ai", f((), "", "", []), None)
	w, ts = f((), "", "", ["K1", "", "K2"])
	la("tìm khớp", ts["ten"], ("K1", "K2"))
	dung("luôn bỏ khách đã tắt", "ifnull(c.disabled, 0) = 0" in f(())[0])


@ca("v617 Danh sách khách hàng: xếp và cộng tiền trong CÂU TRUY VẤN trên đủ nhóm (không còn lấy 400 khách đầu bảng chữ cái)")
def _ds_khach_cau():
	ds, tong = khach_thuan.cau_ds_khach("X = 1", dem_si=True)
	dung("xếp theo chi tiêu giảm dần, cộng chi tiêu cũ Fabi", "order by (ifnull(s.tien, 0) + ifnull(c.vgb_chi_tieu_cu, 0)) desc" in ds)
	dung("trần 200 dòng", ds.rstrip().endswith("limit 200"))
	dung("không xếp theo tên trước", "order by c.customer_name" not in ds)
	dung("dòng tổng không có limit: cộng đủ nhóm", "limit" not in tong and "sum(ifnull(s.tien, 0) + ifnull(c.vgb_chi_tieu_cu, 0))" in tong)
	dung("đếm sỉ", "sum(c.customer_group in %(nhom_si_dem)s)" in tong)
	dung("12 tháng, bỏ hoá đơn huỷ", "posting_date >= %(tu)s" in khach_thuan.CHI_TIEU_12_THANG and "vgb_huy" in khach_thuan.CHI_TIEU_12_THANG)
	ds2, tong2 = khach_thuan.cau_ds_khach("X = 1", co_hang=False, co_tieu_cu=False)
	dung("site chưa có cột: không gọi cột không có", "vgb_hang" not in ds2 and "vgb_chi_tieu_cu" not in ds2 + tong2)
	r = khach_thuan.dong_khach(D(name="K1", customer_name="", customer_group="Sỉ", hang="Vàng", tieu_cu=300000, tien_erp=200000, so_don=3,
		gan_nhat="2026-10-01"), lambda n: n == "Sỉ", {"Vàng": 5})
	la("dòng", (r["ten"], r["si"], r["tien"], r["giam"], r["so_don"]), ("K1", 1, 500000.0, 5.0, 3))


# ------------------------------------------------------------ Codex PR #510 vòng 1 (rà 878fb55f39)

def _gui_moi_truong(rows, ho_so, trang_thai_cd, sau_moi_tin=None, ma_cd=""):
	"""Dựng gửi nền với cơ sở dữ liệu giả có TRẠNG THÁI: hồ sơ khách và trạng thái
	chiến dịch đọc từ hai bảng giả, sau_moi_tin(lần) đổi chúng giữa chừng (khách
	rút đồng ý, quản lý kết thúc chiến dịch) đúng như ngoài đời."""
	fr = zalo_oa.frappe
	doc = D(name="CD-26-0009", owner="loan@x", kenh_oa=1, noi_dung_zalo="Chào {ten}, mã {ma}", tieu_de_oa="",
		han="2027-02-10", ma_uu_dai=ma_cd, trang_thai="Đang chạy")
	doc.as_dict = lambda: dict(doc)
	post, sv, lh = [], [], []

	def sql(q, ts=None, *a, **k):
		if "k.chien_dich = %s" in q:
			return [D(r) for r in rows]
		if "`tabVagabond Ho So CRM` h where h.name = %s" in q:
			h = ho_so.get(ts[0]) or {}
			return [D(dy_zalo=h.get("dy_zalo"), kqc=h.get("kqc", 0), uid=h.get("uid"))]
		return []

	def gv(dt_, name, cot=None, *a, **k):
		if dt_ == crm.DT_CD and cot == "trang_thai":
			return trang_thai_cd[0]
		return None

	def gia_post(duong, than):
		post.append(than)
		if sau_moi_tin:
			sau_moi_tin(len(post))
		return True, "", {}

	class Doc(D):
		def insert(self, **k):
			lh.append(dict(self))
			return self

	vas = [um.patch.object(fr, "get_doc", lambda *a, **k: doc if a and a[0] == crm.DT_CD else Doc(a[0])),
		um.patch.object(fr.db, "sql", sql), um.patch.object(fr.db, "get_value", gv),
		um.patch.object(fr.db, "set_value", lambda dt_, n, v, *a, **k: sv.append((dt_, n, v))),
		um.patch.object(zalo_oa, "_post", gia_post), um.patch.object(zalo_oa, "_cfg", lambda: D()),
		um.patch.object(zalo_oa, "NGHI_GIUA_TIN", 0)]
	return post, sv, lh, vas


def _chay(vas, fn):
	for v in vas:
		v.start()
	try:
		return fn()
	finally:
		for v in vas:
			v.stop()


@ca("v617 Codex #510 4396957327: khách rút đồng ý hay vào Danh sách không quảng cáo GIỮA lượt gửi thì tin sau không tới khách đó")
def _gui_doc_lai_dong_y():
	rows = [D(name="R%d" % i, khach="K%d" % i, ten_khach="Khách %d" % i, ma_uu_dai="", dy_zalo="Đồng ý", kqc=0, uid="U%d" % i)
		for i in (1, 2, 3)]
	ho_so = {"K%d" % i: {"dy_zalo": "Đồng ý", "kqc": 0, "uid": "U%d" % i} for i in (1, 2, 3)}

	def doi(lan):
		# Gửi xong tin đầu thì khách 2 rút đồng ý Zalo, khách 3 vào Danh sách không quảng cáo.
		if lan == 1:
			ho_so["K2"]["dy_zalo"] = "Từ chối"
			ho_so["K3"]["kqc"] = 1

	post, sv, lh, vas = _gui_moi_truong(rows, ho_so, ["Đang chạy"], doi)
	dem = _chay(vas, lambda: zalo_oa.gui_nen("CD-26-0009"))
	la("chỉ gửi khách 1", [p["recipient"]["user_id"] for p in post], ["U1"])
	la("hai khách sau bỏ qua", {n: v["oa_trang_thai"] for d, n, v in sv if d == crm.DT_CD_KHACH}, {"R1": "Đã gửi", "R2": "Bỏ qua", "R3": "Bỏ qua"})
	la("đếm", dem, {"Đã gửi": 1, "Lỗi": 0, "Bỏ qua": 2})
	# Bỏ quan tâm OA giữa chừng: UID hiện tại rỗng thì cũng không gửi.
	ho_so2 = {"K%d" % i: {"dy_zalo": "Đồng ý", "kqc": 0, "uid": "U%d" % i} for i in (1, 2, 3)}
	post2, sv2, _, vas2 = _gui_moi_truong(rows, ho_so2, ["Đang chạy"], lambda lan: ho_so2["K2"].update(uid=None) if lan == 1 else None)
	_chay(vas2, lambda: zalo_oa.gui_nen("CD-26-0009"))
	la("bỏ quan tâm giữa chừng: không gửi khách 2", [p["recipient"]["user_id"] for p in post2], ["U1", "U3"])


@ca("v617 Codex #510 4396957339: chiến dịch kết thúc trước hay trong lượt gửi thì việc nền dừng, không gửi tiếp")
def _gui_dung_khi_ket_thuc():
	rows = [D(name="R%d" % i, khach="K%d" % i, ten_khach="Khách %d" % i, ma_uu_dai="", dy_zalo="Đồng ý", kqc=0, uid="U%d" % i)
		for i in (1, 2, 3)]
	ho_so = {"K%d" % i: {"dy_zalo": "Đồng ý", "kqc": 0, "uid": "U%d" % i} for i in (1, 2, 3)}
	tt = ["Đã kết thúc"]
	post, sv, lh, vas = _gui_moi_truong(rows, ho_so, tt)
	_chay(vas, lambda: zalo_oa.gui_nen("CD-26-0009"))
	la("kết thúc trước khi việc nền chạy: không gửi tin nào", len(post), 0)
	cuoi = [v for d, n, v in sv if d == crm.DT_CD][-1]
	la("ghi rõ đã dừng", (cuoi["oa_trang_thai"], "kết thúc" in cuoi["oa_ket_qua"]), ("Đã dừng", True))
	tt2 = ["Đang chạy"]
	post2, sv2, _, vas2 = _gui_moi_truong(rows, ho_so, tt2, lambda lan: tt2.__setitem__(0, "Đã kết thúc") if lan == 1 else None)
	_chay(vas2, lambda: zalo_oa.gui_nen("CD-26-0009"))
	la("kết thúc giữa chừng: dừng sau tin đang gửi", len(post2), 1)
	la("dòng chưa gửi để nguyên", sorted(n for d, n, v in sv2 if d == crm.DT_CD_KHACH), ["R1"])


@ca("v617 Codex #510 4396957331: chiến dịch mã cố định thì tin Zalo và tin OA hiện mã chung của chiến dịch, OA có bảng mã")
def _ma_co_dinh_trong_tin():
	rows = [D(name="R1", khach="K1", ten_khach="An", ma_uu_dai="", dy_zalo="Đồng ý", kqc=0, uid="U1")]
	ho_so = {"K1": {"dy_zalo": "Đồng ý", "kqc": 0, "uid": "U1"}}
	post, sv, lh, vas = _gui_moi_truong(rows, ho_so, ["Đang chạy"], ma_cd="XMAS10")
	_chay(vas, lambda: zalo_oa.gui_nen("CD-26-0009"))
	p = post[0]["message"]["attachment"]["payload"]
	la("tin OA có mã chung", p["elements"][1]["content"], "Chào An, mã XMAS10")
	la("tin OA có bảng mã", [e["type"] for e in p["elements"]][-1], "table")
	fr = crm.frappe
	dong = [D(name="L1", chien_dich="CD-1", ten_chien_dich="Noel", khach="K1", ten_khach="An", sdt="0909", trang_thai="Chưa gọi",
		kenh_duoc="Zalo", noi_dung_zalo="Chào {ten}, dùng mã {ma}", kich_ban="", mua_cuoi=None, nhom="Mới", hang="",
		dy_goi="", dy_zalo="Đồng ý", kqc=0, kenh_goi=0, kenh_zalo=1, ma_uu_dai="", ma_cd="XMAS10")]
	meta = types.SimpleNamespace(get_valid_columns=lambda: [])
	with um.patch.object(fr, "get_roles", lambda *a: ["Sales User"]), um.patch.object(fr.db, "sql", lambda *a, **k: [D(r) for r in dong]), \
			um.patch.object(fr, "get_meta", lambda dt_: meta, create=True):
		kq = crm.ds_goi_cua_toi()
	la("tin Zalo cá nhân có mã chung", kq["dong"][0]["tin_zalo"], "Chào An, dùng mã XMAS10")
	dong[0]["ma_uu_dai"] = "RIENG1"
	with um.patch.object(fr, "get_roles", lambda *a: ["Sales User"]), um.patch.object(fr.db, "sql", lambda *a, **k: [D(r) for r in dong]), \
			um.patch.object(fr, "get_meta", lambda dt_: meta, create=True):
		kq = crm.ds_goi_cua_toi()
	la("có mã riêng thì mã riêng đứng trước", kq["dong"][0]["tin_zalo"], "Chào An, dùng mã RIENG1")
