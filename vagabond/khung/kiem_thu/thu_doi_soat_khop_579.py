"""#420 v579: lớp đối chiếu thuần của đối soát vendor.

Ba lớp tách riêng: xem trước (đủ nguồn), nối hoá đơn (đủ chứng từ), tiền về
(khớp tiền). Anh Việt 06/10/2026 chốt chỉ lưu và đối chiếu, nên mọi hàm ở
đây chỉ trả kết quả; ca kiểm chốt luôn điều đó: không hàm nào trả bút toán.
"""
from vagabond import doi_soat_khop as K
from vagabond import doi_soat_mau as M
from vagabond import doi_soat_nguon as N
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _kq(nhom="ban", dong=(), loi=(), mau="grabfood", vendor="GrabFood", tk="GRABFOOD:X"):
	kq = M.ket_qua(mau, nhom, vendor, tk)
	kq["dong"] = [M.dong_moi(**d) for d in dong]
	kq["loi"] = list(loi)
	return M.khep_ky(kq)


def _ban(ma, tien=100000, phi=20000, ngay="2026-07-17", **k):
	return dict(dict(ma_su_kien=ma, ma_don=ma, ma_tham_chieu=ma, ngay=ngay, tien_hang=tien, phi=phi,
		thuc_nhan=tien - phi), **k)


# ------------------------------------------------------------ xem trước

@ca("v579 khoá dòng trùng công thức Codex chuan_dong: báo cáo ngày và tháng không cộng hai lần")
def _():
	nguon = dict(cong_ty="C", vendor="GrabFood", merchant="GRABFOOD:X", tien_te="VND",
		tu_ngay="2026-07-01", den_ngay="2026-07-31", dinh_dang="chuan")
	ra = N.chuan_dong(nguon, dict(cong_ty="C", vendor="GrabFood", merchant="GRABFOOD:X", tien_te="VND",
		ma_su_kien="GF-1", ma_don="GF-1", loai="ban", ngay="2026-07-17", tien_hang=100, phi=20, dieu_chinh=0,
		thuc_nhan=80))
	la("cùng khoá", K.khoa("C", "GrabFood", "GRABFOOD:X", "GF-1"), ra["khoa"])
	ngay = K.xem_truoc(_kq(dong=[_ban("GF-1")]), "C")
	thang = _kq(dong=[_ban("GF-1")])
	thang["tu_ngay"], thang["den_ngay"] = "2026-07-01", "2026-07-31"
	la("kỳ khác, khoá như nhau", K.xem_truoc(thang, "C")["dong"][0]["dong"]["khoa"], ngay["dong"][0]["dong"]["khoa"])


@ca("v579 xem trước: mới, đã nhận cùng nội dung, đã nhận khác nội dung, lặp trong tệp")
def _():
	kq = _kq(dong=[_ban("GF-1"), _ban("GF-2"), _ban("GF-3"), _ban("GF-4"), _ban("GF-4", tien=50000)])
	k = lambda m: K.khoa("C", "GrabFood", "GRABFOOD:X", m)
	d2 = K.dau_noi_dung(M.dong_moi(**_ban("GF-2")))
	xt = K.xem_truoc(kq, "C", {k("GF-2"): d2, k("GF-3"): "noi-dung-cu"})
	la("trạng thái từng dòng", [x["trang_thai"] for x in xt["dong"]], ["moi", "trung", "loi", "loi", "loi"])
	dung("khác nội dung nói bản điều chỉnh", "nội dung khác" in xt["dong"][2]["ly_do"])
	dung("lặp giữ cả nhóm", all("lặp" in xt["dong"][i]["ly_do"] for i in (3, 4)))
	la("đếm", xt["so"], dict(moi=1, trung=1, loi=3))
	la("tổng chỉ cộng dòng không lỗi", xt["tong"]["thuc_nhan"], 160000)
	la("có lỗi là cần xử lý", xt["trang_thai"], "Cần xử lý")


@ca("v579 xem trước: tệp sạch là Đã nhận; lỗi cấp tệp là Cần xử lý; không nhận ra mẫu là Lỗi tệp")
def _():
	la("sạch", K.xem_truoc(_kq(dong=[_ban("GF-1")]), "C")["trang_thai"], "Đã nhận")
	la("lệch tổng", K.xem_truoc(_kq(dong=[_ban("GF-1")], loi=["Tổng lệch"]), "C")["trang_thai"], "Cần xử lý")
	la("không mẫu", K.xem_truoc(_kq(mau=""), "C")["trang_thai"], "Lỗi tệp")


@ca("v579 xem trước: dòng tiền bán đi qua luật Codex, phương trình sai và điều chỉnh thiếu căn cứ đều chặn")
def _():
	sai = _ban("GF-1")
	sai["thuc_nhan"] = 1
	xt = K.xem_truoc(_kq(dong=[sai]), "C")
	la("phương trình", xt["dong"][0]["trang_thai"], "loi")
	dc = dict(ma_su_kien="MPA-1", loai="dieu_chinh", ngay="2026-07-17", dieu_chinh=5000, thuc_nhan=5000)
	la("điều chỉnh thiếu căn cứ", K.xem_truoc(_kq(dong=[dc]), "C")["dong"][0]["trang_thai"], "loi")
	la("điều chỉnh có căn cứ", K.xem_truoc(_kq(dong=[dict(dc, ma_can_cu="MPA-1 GF-1")]), "C")["dong"][0]["trang_thai"], "moi")


@ca("v579 xem trước nhóm chuyến đi và thẻ: phí và lãi phải có căn cứ, chuyến thường thì không")
def _():
	chuyen = [dict(ma_su_kien="B1", loai="ban", ngay="2026-06-01", tien_hang=65000, thuc_nhan=65000),
		dict(ma_su_kien="PQL", loai="phi_quan_ly", ngay="2026-06-30", phi=5000, thuc_nhan=5000)]
	xt = K.xem_truoc(_kq(nhom="chuyen", dong=chuyen, mau="be", vendor="Be", tk="BE"), "C")
	la("phí quản lý thiếu căn cứ", [x["trang_thai"] for x in xt["dong"]], ["moi", "loi"])
	chuyen[1]["ma_can_cu"] = "Admin Fee 2606"
	xt = K.xem_truoc(_kq(nhom="chuyen", dong=chuyen, mau="be", vendor="Be", tk="BE"), "C")
	la("có căn cứ", [x["trang_thai"] for x in xt["dong"]], ["moi", "moi"])


@ca("v579 dòng lỗi của bộ đọc vẫn hiện trong xem trước, không lặng lẽ biến mất")
def _():
	kq = _kq(dong=[_ban("GF-1")])
	kq["dong_loi"] = [dict(vi_tri=7, ly_do="Không đọc được", tho=[])]
	xt = K.xem_truoc(kq, "C")
	la("hai dòng", (len(xt["dong"]), xt["so"]["loi"], xt["dong"][1]["vi_tri"]), (2, 1, 7))


# ------------------------------------------------------------ nối hoá đơn bán

def _uv(name, ma, tien=100000, ngay="2026-07-17", tien_to=""):
	return dict(name=name, ngay=ngay, tien=tien, ma=[ma], tien_to=tien_to)


def _d(ma, tien=100000, giam=0, ngay="2026-07-17", loai="ban"):
	return dict(loai=loai, ngay=ngay, ma_tham_chieu=ma, tien_hang=tien, giam_gia=giam)


@ca("v579 luật mã từng nguồn: Grab bỏ F cuối, Shopee 4 số cuối, Xanh SM XSM-, Payoo đuôi, Shinhan đúng 6 ký tự")
def _():
	la("grab", [K._ma_khop("grab", "GF-398F", "GF-398"), K._ma_khop("grab", "GF-398", "GF-39"),
		K._ma_khop("grab", "GD-ABC", "GF-ABC"), K._ma_khop("grab", "GF-F", "GF-")], [True, False, False, False])
	la("shopee", [K._ma_khop("shopee", "2607170001066529", "6529"), K._ma_khop("shopee", "1066529", "529")], [True, False])
	la("greensm", [K._ma_khop("greensm", "0010", "XSM-0010"), K._ma_khop("greensm", "0010", "XSM-10")], [True, False])
	la("payoo", [K._ma_khop("payoo", "611800000001", "000001"), K._ma_khop("payoo", "611800000001", "001")], [True, False])
	la("shinhan giữ số 0", [K._ma_khop("shinhan", "046327", "046327"), K._ma_khop("shinhan", "046327", "46327")], [True, False])
	la("thiếu mã", K._ma_khop("grab", "", "GF-1"), False)


@ca("v579 nối hoá đơn: theo mã trước, lệch tiền vẫn nối nhưng báo, không bao giờ một hoá đơn cho hai dòng")
def _():
	dong = [_d("GF-1"), _d("GF-2", tien=90000), _d("GF-1", ngay="2026-07-17")]
	uv = [_uv("SI-1", "GF-1"), _uv("SI-2", "GF-2")]
	kq = K.khop_hoa_don("grab", dong, uv)
	la("dòng 1", (kq[0]["trang_thai"], kq[0]["hoa_don"]), ("Đã nối", "SI-1"))
	la("dòng 2 lệch tiền", (kq[1]["trang_thai"], kq[1]["hoa_don"]), ("Lệch tiền", "SI-2"))
	dung("ghi chú có hai số", "100.000" in kq[1]["ghi_chu"] and "90.000" in kq[1]["ghi_chu"])
	la("dòng 3 không lấy lại SI-1", (kq[2]["trang_thai"], kq[2]["hoa_don"]), ("Không thấy chứng từ", ""))


@ca("v579 nối hoá đơn sàn: so với giá trước khuyến mại quán chịu, vì hoá đơn ghi giá menu")
def _():
	kq = K.khop_hoa_don("greensm", [_d("0010", tien=63000, giam=52000)], [_uv("SI-9", "XSM-0010", tien=115000)])
	la("đã nối", kq[0]["trang_thai"], "Đã nối")
	kq = K.khop_hoa_don("payoo", [_d("611800000001", tien=100000, giam=5000)], [_uv("SI-9", "000001", tien=100000)])
	la("cổng thẻ so số quẹt", kq[0]["trang_thai"], "Đã nối")


@ca("v579 nối theo tiền chỉ khi đúng một hoá đơn trống; hai hoá đơn cùng tiền là Nhiều chứng từ")
def _():
	kq = K.khop_hoa_don("shopee", [_d("2607170001066529")], [_uv("SI-1", "", tien=100000)])
	la("một ứng viên", (kq[0]["trang_thai"], kq[0]["hoa_don"]), ("Nối theo tiền", "SI-1"))
	kq = K.khop_hoa_don("shopee", [_d("2607170001066529")], [_uv("SI-1", ""), _uv("SI-2", "")])
	la("hai ứng viên", (kq[0]["trang_thai"], kq[0]["hoa_don"]), ("Nhiều chứng từ", ""))
	kq = K.khop_hoa_don("shopee", [_d("2607170001066529")], [_uv("SI-1", "", ngay="2026-07-18")])
	la("lệch ngày sàn là 0", kq[0]["trang_thai"], "Không thấy chứng từ")
	kq = K.khop_hoa_don("payoo", [_d("6118")], [_uv("SI-1", "", ngay="2026-07-18")])
	la("cổng thẻ cho lệch 1 ngày", kq[0]["trang_thai"], "Nối theo tiền")


@ca("v579 Grab Dine-Out GD- không nối theo tiền vào bill giao hàng GF- trùng số tiền")
def _():
	uv = [_uv("SI-GF", "GF-7", tien_to="GF-"), _uv("SI-GD", "", tien_to="GD-")]
	kq = K.khop_hoa_don("grab", [_d("GD-AAAA1111")], uv)
	la("chỉ lấy bill Dine-Out", (kq[0]["trang_thai"], kq[0]["hoa_don"]), ("Nối theo tiền", "SI-GD"))
	kq = K.khop_hoa_don("grab", [_d("GD-AAAA1111")], uv[:1])
	la("không có bill Dine-Out thì không ghép bừa", kq[0]["trang_thai"], "Không thấy chứng từ")


@ca("v579 nối hoá đơn: quảng cáo, điều chỉnh là Không áp dụng; OnePay chưa có mã chung nên chỉ nối theo tiền")
def _():
	kq = K.khop_hoa_don("grab", [_d("ADS-1", loai="phi_ky"), _d("GF-1")], [_uv("SI-1", "GF-1")])
	la("không áp dụng", kq[0]["trang_thai"], "Không áp dụng")
	kq = K.khop_hoa_don("onepay", [_d("PL_1")], [_uv("SI-1", "PL_1")])
	la("onepay", kq[0]["trang_thai"], "Nối theo tiền")


# ------------------------------------------------------------ tiền về

def _gd(name, tien, mo_ta, ngay="2026-07-18"):
	return dict(name=name, ngay=ngay, tien=tien, mo_ta=mo_ta)


@ca("v579 tiền về: đúng nội dung vendor và đúng số; số gần nhất là lệch; khác vendor không tính")
def _():
	gd = [_gd("BT-1", 668915, "Grab TT 118203316 Tran Cao Van"), _gd("BT-2", 668915, "Khach chuyen khoan"),
		_gd("BT-3", 500000, "SHOPEEPAY CHUYEN TIEN ShopeeFood thanh toan tu dong")]
	la("grab đúng", K.khop_ngan_hang("grabfood", 668915, "2026-07-17", "2026-07-24", gd)[:2], ("Đã thấy tiền về", ["BT-1"]))
	tt, ds, ghi = K.khop_ngan_hang("shopeefood", 501000, "2026-07-17", "2026-07-24", gd)
	la("shopee lệch", (tt, ds), ("Lệch tiền về", ["BT-3"]))
	dung("ghi chú có độ lệch", "1.000" in ghi)
	la("ngoài khoảng ngày", K.khop_ngan_hang("grabfood", 668915, "2026-07-19", "2026-07-24", gd)[0], "Chưa thấy tiền về")
	la("đã dùng cho tệp khác", K.khop_ngan_hang("grabfood", 668915, "2026-07-17", "2026-07-24", gd, {"BT-1"})[0],
		"Chưa thấy tiền về")
	la("không có tiền phải về", K.khop_ngan_hang("be", 0, "2026-07-17", "2026-07-24", gd)[0], "Không áp dụng")


@ca("v579 tiền về: mẫu nội dung thật của OnePay, Payoo trên sao kê MB")
def _():
	gd = [_gd("BT-O", 1000, "PVS1447922 OnePay tam ung VAGABOND QT"),
		_gd("BT-P", 2000, "Payoo TT TD ngay 02.10 04.10.2026.VAGABOND TONG")]
	la("onepay", K.khop_ngan_hang("onepay_ngay", 1000, "2026-07-17", "2026-07-24", gd)[1], ["BT-O"])
	la("payoo", K.khop_ngan_hang("payoo_the", 2000, "2026-07-17", "2026-07-24", gd)[1], ["BT-P"])


# ------------------------------------------------------------ thẻ tín dụng

@ca("v579 thẻ tín dụng: đầu kỳ lấy từ kỳ trước, thiếu kỳ trước thì nói rõ, không đặt bằng 0")
def _():
	r = K.ky_the(dict(den_han=0), None)
	dung("thiếu kỳ trước", not r["du"] and "kỳ trước" in r["ghi_chu"])
	r = K.ky_the(dict(spend=3000000, fees=100000, chua_tra_truoc=0, den_han=3100000), dict(den_han=2000000))
	la("đủ phương trình", (r["du"], r["dau_ky"], r["da_tra"]), (True, 2000000, 2000000))
	r = K.ky_the(dict(spend=3000000, fees=0, chua_tra_truoc=0, den_han=3100000), dict(den_han=2000000))
	dung("lệch có số", not r["du"] and "100.000" in r["ghi_chu"])


# ------------------------------------------------------------ chỉ lưu và đối chiếu

@ca("v579 chỉ lưu và đối chiếu: lớp đối chiếu không có hàm nào tạo phiếu hay bút toán")
def _():
	import inspect
	import re
	from vagabond import doi_soat_vendor as V
	nguon = inspect.getsource(V)
	# Mọi chứng từ module tự tạo: chỉ tệp đính kèm và hai doctype đối soát.
	tao = set(re.findall(r"""(?<![\w"'])["']?doctype["']?\s*[:=]\s*("[^"]+"|\w+)""", nguon))
	la("chỉ tạo File và hai doctype đối soát", tao, {'"File"', "DT_NGUON", "DT_DONG"})
	la("không trình ký chứng từ", ".submit(" in nguon, False)
	la("không gạch giao dịch ngân hàng", "allocated_amount" in nguon or "unallocated" in nguon, False)


@ca("v579 nhận thư tự động chỉ từ tên miền vendor đã khai")
def _():
	from vagabond.doi_soat_vendor import la_thu_vendor
	la("đúng", [la_thu_vendor("Grab <no-reply@grab.com>"), la_thu_vendor("bao-cao@mail.payoo.com.vn"),
		la_thu_vendor("x@xanhsm.com")], [True, True, True])
	la("sai", [la_thu_vendor("ke-toan@thevagabondpatisserie.com"), la_thu_vendor("x@notgrab.com"),
		la_thu_vendor("grab.com@lua-dao.vn"), la_thu_vendor("")], [False, False, False, False])


@ca("v579 tóm tắt gửi màn hình: tên mẫu tiếng Việt, tối đa 30 dòng mẫu, không mang cột người đi")
def _():
	from vagabond.doi_soat_vendor import tom_tat
	kq = _kq(dong=[dict(_ban("GF-%s" % i), nguoi="STAFF_A") for i in range(40)])
	t = tom_tat(kq, K.xem_truoc(kq, "C"))
	la("tên mẫu", t["ten_mau"], M.TEN_MAU["grabfood"])
	la("nhóm", t["nhom"], "Tiền bán")
	la("30 dòng mẫu", len(t["mau_dong"]), 30)
	la("không lộ người", any("nguoi" in d for d in t["mau_dong"]), False)


# ------------------------------------------------------------ Codex #446 (e19d3edfc)

@ca("Codex #446 F3: tệp lẫn nhiều tài khoản Payoo thì giữ nguồn để xem, KHÔNG ghi dòng nào")
def _():
	from vagabond.khung.kiem_thu import thu_doi_soat_mau_579 as T
	hai_tk = T.PAYOO_THE.replace("VAGABOND_TONG,VAGABOND_TONG,VAGABOND_307NVT", "VAGABOND_KHAC,VAGABOND_KHAC,VAGABOND_307NVT")
	kq = M.doc(T._csv(T.TEN_PAYOO, hai_tk))
	la("bộ đọc để trống tài khoản và báo lỗi", (kq["tai_khoan"], any("nhiều tài khoản" in l for l in kq["loi"])), ("", True))
	xt = K.xem_truoc(kq, "C")
	la("không dòng nào được nhận", xt["so"]["moi"], 0)
	dung("lý do nói tách tệp", all("tách tệp" in x["ly_do"] for x in xt["dong"]))
	# Tải lại bản đã tách: cùng sự kiện, khoá theo đúng tài khoản; không có
	# dòng cũ khoá "-" nào nằm sẵn để bị nhận lần hai.
	mot = M.doc(T._csv(T.TEN_PAYOO, T.PAYOO_THE))
	la("bản tách nhận đủ", K.xem_truoc(mot, "C")["so"]["moi"], 3)


@ca("Codex #446 F3: phạm vi khoá Xanh SM không đổi theo số cửa hàng trong tệp")
def _():
	from vagabond.khung.kiem_thu import thu_doi_soat_mau_579 as T
	from vagabond import doi_soat_doc as D
	o = D.doc_csv(T.XANH_CT.encode())[0]["o"]
	mot = M.doc(T._luoi("Revenue_Report_x_20260124", ("Detail Transactions", o), ("Summary", T.XANH_TH)))
	hai = [r[:] for r in o]
	hai[-1][3] = "01K23YRC3K35J07ZYBVADZZSYK"
	gop = M.doc(T._luoi("Revenue_Report_y_20260124", ("Detail Transactions", hai)))
	la("cùng phạm vi", (mot["tai_khoan"], gop["tai_khoan"]), ("GREENSM", "GREENSM"))
	k1 = {x["dong"]["khoa"] for x in K.xem_truoc(mot, "C")["dong"]}
	k2 = {x["dong"]["khoa"] for x in K.xem_truoc(gop, "C")["dong"] if x["dong"]}
	la("cùng khoá cho cùng đơn", k1 & k2 == k1, True)


@ca("Codex #446 F1: hai doctype đối soát người chỉ đọc, controller chặn lưu tay")
def _():
	import json
	import os
	goc = os.path.join(os.path.dirname(__file__), "..", "..", "vagabond", "doctype")
	for ten in ("vagabond_doi_soat_nguon", "vagabond_doi_soat_dong"):
		d = json.load(open(os.path.join(goc, ten, ten + ".json"), encoding="utf-8"))
		la(ten + ": không vai nào được tạo hay sửa",
			[p["role"] for p in d["permissions"] if p.get("write") or p.get("create") or p.get("delete")], [])
		src = open(os.path.join(goc, ten, ten + ".py"), encoding="utf-8").read()
		dung(ten + ": validate chặn khi không đi qua cửa máy", "def validate" in src and "ignore_permissions" in src)


@ca("Codex #446 vòng 2: khoá đối chiếu: lấy khoá, commit mở ảnh mới, làm, commit, nhả; lỗi vẫn nhả")
def _():
	from vagabond.doi_soat_vendor import khoa_doi_chieu

	class Db:
		def __init__(self, duoc=1):
			self.goi, self.duoc = [], duoc

		def sql(self, q, a=None):
			self.goi.append(q.split("(")[0].replace("select ", ""))
			return [[self.duoc]] if "get_lock" in q else [[1]]

		def commit(self):
			self.goi.append("commit")

	db = Db()
	with khoa_doi_chieu(db):
		db.goi.append("lam")
	la("thứ tự", db.goi, ["get_lock", "commit", "lam", "commit", "release_lock"])
	db = Db()
	try:
		with khoa_doi_chieu(db):
			raise ValueError("hong")
	except ValueError:
		pass
	la("lỗi giữa chừng: không commit lần hai, vẫn nhả", db.goi, ["get_lock", "commit", "release_lock"])
	db = Db(duoc=0)
	try:
		with khoa_doi_chieu(db):
			db.goi.append("lam")
		bi_chan = False
	except Exception:
		bi_chan = True
	la("không lấy được khoá thì không làm", (bi_chan, "lam" in db.goi), (True, False))


@ca("Codex #446 vòng 2: mọi lối ghi nối và tiền về đều đi qua khoá đối chiếu (một nguồn)")
def _():
	import ast
	import inspect
	from vagabond import doi_soat_vendor as V
	cay = ast.parse(inspect.getsource(V))
	ham = {f.name: f for f in cay.body if isinstance(f, ast.FunctionDef)}

	def goi(f, ten):
		return any(isinstance(n, ast.Call) and getattr(n.func, "id", None) == ten for n in ast.walk(f))

	def co_khoa(f):
		return any(isinstance(n, ast.With) and any(getattr(getattr(i.context_expr, "func", None), "id", None) == "khoa_doi_chieu"
			for i in n.items) for n in ast.walk(f))
	la("ai gọi _doi_chieu", sorted(k for k, f in ham.items() if goi(f, "_doi_chieu")), ["_ghi_nguon", "doi_chieu_lai"])
	la("ai gọi _ghi_nguon", sorted(k for k, f in ham.items() if goi(f, "_ghi_nguon")), ["_ghi_thu_khong_tep", "_nhan_byte"])
	la("mọi cửa đều giữ khoá", [co_khoa(ham[k]) for k in ("_nhan_byte", "doi_chieu_lai", "_ghi_thu_khong_tep")], [True, True, True])


@ca("Codex #446 H1: phạm vi pháp nhân: không cấp quyền là xem tất cả, có cấp là chỉ pháp nhân đó")
def _():
	from vagabond.doi_soat_vendor import chon_cong_ty
	la("không giới hạn", chon_cong_ty(["A", "B"], set()), ["A", "B"])
	la("chỉ B", chon_cong_ty(["A", "B"], {"B"}), ["B"])
	la("cấp pháp nhân không tồn tại thì rỗng an toàn", chon_cong_ty(["A"], {"Z"}), [""])


@ca("Codex #446 H1: mọi truy vấn chứng từ để nối đều lọc đúng pháp nhân nguồn (chốt không còn chỗ quên)")
def _():
	import inspect
	from vagabond import doi_soat_vendor as V
	src = inspect.getsource(V)
	for ham, can in (("_dk_hd", '"s.company=%(ct)s"'),
			("_tien_ve", '{"company": nguon.company}'), ("_noi_chuyen", '"company": nguon.company'),
			("_ky_the", '"company": nguon.company'), ("_tong_hop", "company=%%s"), ("ds", '"company": ["in", ct]'),
			("chi_tiet", "_chan_cong_ty(n.company)"), ("suc_khoe", "company in %%(ct)s"), ("cua_hoa_don", '"company": ["in", _cong_ty_xem()]'),
			("doi_chieu_lai", "_chan_cong_ty("), ("nhan", "_chan_cong_ty(_cong_ty())")):
		than = inspect.getsource(getattr(V, ham))
		dung("%s lọc pháp nhân (%s)" % (ham, can), can in than)


@ca("Codex #446 H2: thư báo cáo không có tệp đọc được thì hiện ở Cần xử lý; thư quảng cáo thì không")
def _():
	from vagabond.doi_soat_vendor import thu_co_bao_cao, vendor_theo_thu
	la("báo cáo tháng Payoo trong thân thư", thu_co_bao_cao("Payoo - Báo cáo đối soát tháng 09/2026", "<p>Tổng tiền...</p>"), True)
	la("sao kê", thu_co_bao_cao("Thong bao", "Sao ke giao dich ngay 05/10"), True)
	la("quảng cáo", thu_co_bao_cao("Ưu đãi tháng 10 cho đối tác", "Giảm 20% phí quảng cáo"), False)
	la("vendor từ tên miền", [vendor_theo_thu("Payoo <noreply@payoo.com.vn>"), vendor_theo_thu("a@mail.grab.com"),
		vendor_theo_thu("x@khac.vn")], ["Payoo", "Grab", ""])


@ca("Codex #446 H4: nguồn lỗi hay cần xử lý được đọc lại; nguồn đã nhận thì dừng ở mã băm")
def _():
	la("đọc lại", [K.doc_lai_duoc(t) for t in ("Lỗi tệp", "Cần xử lý", "Đã nhận", "")], [True, True, False, False])
	import inspect
	from vagabond import doi_soat_vendor as V
	than = inspect.getsource(V._nhan_byte)
	dung("cửa nhận dùng đúng luật đọc lại", "khop.doc_lai_duoc(da.trang_thai)" in than and "co_san=da.name" in than)


@ca("Codex #446 H5: đối chiếu lại chuyến xoá liên kết cũ trước khi gán liên kết mới")
def _():
	import inspect
	from vagabond import doi_soat_vendor as V
	dung("mỗi dòng bắt đầu với van_don và purchase_invoice rỗng",
		'cap = {"van_don": None, "purchase_invoice": None}' in inspect.getsource(V._noi_chuyen))


def _chay_thu(tep, tieu_de, da_co=None):
	"""Chạy xu_ly_thu THẬT (cả _nhan_byte thật) với tầng chạm hệ được thay:
	tep = {tên đính kèm: [(tên tệp con, có mẫu?)]}. Trả (ket, các nguồn đã ghi)."""
	from contextlib import nullcontext
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V
	da_co = dict(da_co or {})
	ghi = []

	def doc_va_xem(ten, byte, cong_ty):
		ra = []
		for con, co_mau in tep[ten]:
			kq = dict(mau="payoo_the" if co_mau else "", loi=[] if co_mau else ["Chưa nhận ra mẫu"])
			ra.append((dict(ten=con, sha256="sha-" + con, loai="csv"), kq, dict(trang_thai="Đã nhận" if co_mau else "Lỗi tệp")))
		return ra

	def get_value(dt, loc, truong=None, as_dict=False):
		if dt == "Communication":
			return NS(subject=tieu_de, content="", sender="noreply@payoo.com.vn")
		sha = loc.get("sha256") if isinstance(loc, dict) else None
		return NS(name=da_co[sha][0], trang_thai=da_co[sha][1]) if sha in da_co else None

	def ghi_nguon(cong_ty, t, kq, xt, kenh, file_url, comm, co_san=None):
		ghi.append((t["ten"], co_san))
		da_co[t["sha256"]] = ("N-" + t["ten"], xt["trang_thai"])
		return dict(name="N-" + t["ten"], trang_thai=xt["trang_thai"], da_co=0, ten_tep=t["ten"])

	tep_dinh = [NS(name="F-" + k, file_name=k, file_url="/private/files/" + k) for k in tep]
	with patch.object(V, "khoa_doi_chieu", lambda *a, **k: nullcontext()), \
			patch.object(V, "_cong_ty", lambda: "CT"), \
			patch.object(V, "_doc_va_xem", doc_va_xem), \
			patch.object(V, "_ghi_nguon", ghi_nguon), \
			patch.object(V, "_byte_tep", lambda ten: b"x", create=True), \
			patch.object(V.frappe, "get_doc", lambda *a, **k: NS(get_content=lambda: b"x"), create=True), \
			patch.object(V.frappe, "get_all", lambda *a, **k: tep_dinh, create=True), \
			patch.object(V.frappe.db, "get_value", get_value, create=True), \
			patch.object(V, "_ghi_thu_khong_tep", lambda comm, c: ghi.append(("THAN_THU", None)) or [dict(name="N-than")]):
		ket = V.xu_ly_thu("COMM-1")
	return ket, ghi


@ca("Codex #450: thư có báo cáo đọc được kèm một tệp hỏng hoặc chưa có mẫu thì tệp đó vẫn hiện ở Cần xử lý")
def _():
	ket, ghi = _chay_thu({"bao-cao.csv": [("bao-cao.csv", True)], "hong.xlsx": [("hong.xlsx", False)]}, "Thong bao")
	la("ghi cả báo cáo lẫn tệp hỏng, mỗi tệp một lần", sorted(ghi), [("bao-cao.csv", None), ("hong.xlsx", None)])
	la("kết quả không lặp", sorted(r["name"] for r in ket), ["N-bao-cao.csv", "N-hong.xlsx"])
	# Gói zip có tệp con tốt và tệp con chưa có mẫu: chỉ ghi thêm tệp con bị bỏ qua.
	ket, ghi = _chay_thu({"goi.zip": [("a.csv", True), ("b.pdf", False)]}, "Thong bao")
	la("zip: tệp con tốt ghi một lần, tệp con lỗi được ghi", sorted(ghi), [("a.csv", None), ("b.pdf", None)])
	la("zip: kết quả không lặp tệp con tốt", sorted(r["ten_tep"] for r in ket), ["a.csv", "b.pdf"])


@ca("Codex #450: thư quảng cáo không có tệp nhận ra mẫu vẫn bỏ qua; quét lại không ghi lại hay sinh nguồn thân thư")
def _():
	ket, ghi = _chay_thu({"brochure.pdf": [("brochure.pdf", False)]}, "Ưu đãi tháng 10 cho đối tác")
	la("quảng cáo: không ghi gì", (ghi, ket), ([], []))
	ket, ghi = _chay_thu({"bang-ke.xlsx": [("bang-ke.xlsx", False)]}, "Payoo - Báo cáo đối soát tháng 09/2026")
	la("thư báo cáo chỉ có tệp chưa có mẫu: ghi đúng tệp đó, không thêm nguồn thân thư", ghi, [("bang-ke.xlsx", None)])
	# Lượt quét giờ sau: tệp đó đã có nguồn "Lỗi tệp".
	ket, ghi = _chay_thu({"bang-ke.xlsx": [("bang-ke.xlsx", False)]}, "Payoo - Báo cáo đối soát tháng 09/2026",
		da_co={"sha-bang-ke.xlsx": ("N-bang-ke.xlsx", "Lỗi tệp")})
	la("quét lại: không ghi lại, không sinh nguồn thân thư", (ghi, [r["name"] for r in ket]), ([], ["N-bang-ke.xlsx"]))


@ca("Codex #450: nhiều giao dịch cùng số tiền thì không tự chọn; chỉ khớp đúng một mới giữ giao dịch")
def _():
	gd = [_gd("BT-1", 900000, "Shinhan POS"), _gd("BT-2", 900000, "Khach chuyen khoan"), _gd("BT-3", 455000, "x")]
	tt, ds, ghi = K.khop_ngan_hang("shinhan_ngay", 900000, "2026-07-17", "2026-07-24", gd)
	la("Shinhan hai giao dịch cùng tiền: cần chọn, không gắn", (tt, ds), ("Cần chọn tiền về", []))
	dung("ghi chú nêu đủ các giao dịch ứng viên", "BT-1" in ghi and "BT-2" in ghi)
	la("một giao dịch đã dùng thì còn đúng một: khớp", K.khop_ngan_hang("shinhan_ngay", 900000, "2026-07-17",
		"2026-07-24", gd, {"BT-1"})[:2], ("Đã thấy tiền về", ["BT-2"]))
	la("trạng thái chờ gồm cả Cần chọn", "Cần chọn tiền về" in K.CHO_TIEN_VE, True)


def _tien_ve_that(tra_ve, gd_bank, mau="shinhan_ngay", trang_thai="Đã nhận", tien_mat=0):
	"""Chạy _tien_ve THẬT với tầng chạm hệ được thay; trả các trường đã ghi."""
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V
	ghi = {}
	nguon = NS(name="N1", thuc_nhan=900000, mau=mau, ngay_tien_ve="2026-07-18", den_ngay="2026-07-18", trang_thai=trang_thai,
		company="CT", db_set=lambda d, *a, **k: ghi.update(d if isinstance(d, dict) else {d: a[0]}))

	def get_all(dt, **k):
		if dt == "Bank Transaction":
			return [NS(name=n, date="2026-07-18", deposit=t, description=m, reference_number="") for n, t, m in gd_bank]
		return []
	import datetime
	from contextlib import ExitStack
	with ExitStack() as st:
		st.enter_context(patch.object(V.frappe, "get_all", get_all, create=True))
		st.enter_context(patch.object(V.frappe, "get_meta", lambda dt: NS(has_field=lambda f: False), create=True))
		st.enter_context(patch.object(V.frappe.utils, "add_days",
			lambda d, n: str(datetime.date.fromisoformat(str(d)) + datetime.timedelta(days=n)), create=True))
		st.enter_context(patch.object(V, "_ghi_them", lambda name, **k: ghi.update(_ghi_chu=k.get("tien_ve"))))
		st.enter_context(patch.object(V.frappe.db, "count", lambda dt, f=None: tien_mat, create=True))
		if tra_ve:
			st.enter_context(patch.object(V.khop, "khop_ngan_hang", tra_ve))
		V._tien_ve(nguon)
	return ghi


@ca("Codex #450: _tien_ve chỉ ghi giao dịch đã dùng khi khớp đúng một; trùng tiền hay lệch tiền không giữ giao dịch")
def _():
	trung = _tien_ve_that(None, [("BT-1", 900000, "a"), ("BT-2", 900000, "b")])
	la("trùng tiền: cần chọn, không giữ giao dịch", (trung["trang_thai_tien"], trung["giao_dich_ngan_hang"]), ("Cần chọn tiền về", ""))
	mot = _tien_ve_that(None, [("BT-1", 900000, "Grab TT 1182 Tran Cao Van"), ("BT-2", 100, "b")], mau="grabfood")
	la("đúng một (nguồn có nội dung CK): giữ giao dịch", (mot["trang_thai_tien"], mot["giao_dich_ngan_hang"]), ("Đã thấy tiền về", "BT-1"))
	lech = _tien_ve_that(lambda *a, **k: ("Lệch tiền về", ["BT-9"], "Gần nhất BT-9"), [("BT-9", 899000, "a")])
	la("lệch tiền: gợi ý ở ghi chú, không giữ giao dịch", (lech["trang_thai_tien"], lech["giao_dich_ngan_hang"], "BT-9" in lech["_ghi_chu"]),
		("Lệch tiền về", "", True))


@ca("Codex #450: đọc lại nguồn lỗi chuyển dòng bản cũ thành Đã thay (không xoá) TRƯỚC khi xem trước và ghi bản mới")
def _():
	# Vòng 7: bản trước XOÁ dòng cũ và chỉ chụp 2.000 dòng vào du_lieu (Codex:
	# mất tới 18.000 sự kiện cũ). Nay giữ đủ dòng, chỉ đổi trạng thái/khoá.
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V
	from vagabond import doi_soat_mau as Mau
	viec = []
	kho = {"A": "dau-A", "B": "dau-B"}  # dòng bản cũ của nguồn N1 đang nằm trong DB

	def sql(cau, tham=None, *a, **k):
		if cau.lstrip().startswith("update"):
			viec.append(("sql", " ".join(cau.split()), tham)); kho.clear()
		return []

	def xoa(*a, **k):
		viec.append(("xoa",))

	def da_nhan(ct, kq):
		viec.append(("da_nhan", dict(kho))); return dict(kho)

	def xem_truoc(kq, ct, dn=None):
		viec.append(("xem_truoc", dict(dn or {})))
		return dict(so=dict(moi=1, trung=0, loi=0), loi=[], canh_bao=[], trang_thai="Đã nhận",
			tong=dict(tien_hang=1, phi=0, thuc_nhan=1), dong=[])
	nguon = NS(name="N1", trang_thai="Đã nhận", db_set=lambda d: viec.append(("db_set", d)), reload=lambda: None)
	kq = Mau.ket_qua("payoo_the", "tien_ban", "Payoo", "TK")
	with patch.object(V.frappe.db, "sql", sql, create=True), \
			patch.object(V.frappe.db, "count", lambda dt, f=None: len(kho), create=True), \
			patch.object(V.frappe.db, "get_value", lambda *a, **k: {"du_lieu": "{}", "so_dong": 2, "thuc_nhan": 2}, create=True), \
			patch.object(V.frappe.db, "delete", xoa, create=True), \
			patch.object(V.frappe.db, "savepoint", lambda n: None, create=True), \
			patch.object(V.frappe, "get_doc", lambda *a, **k: nguon, create=True), \
			patch.object(V.frappe.utils, "now", lambda: "2026-10-07 09:00:00", create=True), \
			patch.object(V, "_da_nhan", da_nhan), patch.object(V.khop, "xem_truoc", xem_truoc), \
			patch.object(V, "_doi_chieu", lambda n: viec.append(("doi_chieu", n))):
		V._ghi_nguon("CT", dict(ten="t.csv", sha256="s"), kq, dict(so=dict(moi=0, trung=2, loi=0)), "Tải tay", None, None, co_san="N1")
	thu_tu = [v[0] for v in viec]
	la("chuyển dòng cũ trước khi đọc ảnh dữ liệu và xem trước", thu_tu[:3], ["sql", "da_nhan", "xem_truoc"])
	dung("không xoá dòng nào", "xoa" not in thu_tu)
	cau, tham = viec[0][1], viec[0][2]
	dung("giữ khoá gốc, đổi khoá, giữ nguồn gốc, tách khỏi nguồn",
		all(x in cau for x in ("khoa_cu=khoa", "khoa=concat('thay:', name)", "nguon_cu=nguon", "nguon=NULL")))
	dung("không đụng liên kết hoá đơn/vận đơn (giữ làm vết)", "sales_invoice" not in cau and "van_don" not in cau)
	la("trạng thái Đã thay, đúng nguồn", (tham[0], tham[2]), (K.DA_THAY, "N1"))
	la("xem trước lại không còn thấy dòng bản cũ", viec[2][1], {})
	import json
	ghi_db = next(v for v in viec if v[0] == "db_set")[1]
	ls = json.loads(ghi_db["du_lieu"])["lan_doc_truoc"]
	la("lịch sử số dòng lần đọc trước", (len(ls), ls[0]["so_dong"]), (1, 2))
	la("đối chiếu lại sau khi ghi", thu_tu[-1], "doi_chieu")


@ca("Codex #450: dòng Đã thay không còn giữ hoá đơn, không vào khối trên hoá đơn, không cộng vào biên bản OnePay")
def _():
	import inspect
	from vagabond import doi_soat_vendor as V
	la("trạng thái giữ hoá đơn không gồm Đã thay", K.DA_THAY in K.GIU_HOA_DON, False)
	for ham, can in (("_noi_hoa_don_ban", '"trang_thai_khop": ["in", list(khop.GIU_HOA_DON)]'),
			("cua_hoa_don", '"trang_thai_khop": ["!=", khop.DA_THAY]'), ("_tong_hop", "trang_thai_khop!=%%s")):
		dung("%s bỏ qua dòng Đã thay" % ham, can in inspect.getsource(getattr(V, ham)))
	# Mọi truy vấn bảng dòng không theo nguồn đều phải có điều kiện Đã thay.
	src = inspect.getsource(V)
	import re
	theo = [m.group(0) for m in re.finditer(r"get_all\(DT_DONG, filters=\{[^}]*\}", src)]
	ngoai = [x for x in theo if '"nguon": name' not in x and '"nguon": nguon.name' not in x and "khoa" not in x
		and "DA_THAY" not in x and "GIU_HOA_DON" not in x and "filters=f" not in x]
	la("không còn truy vấn dòng nào quên Đã thay", ngoai, [])


@ca("Codex #450: máy chủ đếm và lọc 'Chờ tiền về' cùng một tập ba trạng thái")
def _():
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V
	goi = []
	nguon = [dict(nhom="Tiền bán", vendor="GrabFood", trang_thai="Đã nhận", trang_thai_tien=t, so_chua_noi=0)
		for t in ("Chưa thấy tiền về", "Lệch tiền về", "Lệch tiền về", "Cần chọn tiền về", "Cần chọn tiền về",
			"Cần chọn tiền về", "Đã thấy tiền về")]

	def get_all(dt, filters=None, **k):
		goi.append(dict(filters))
		return nguon if k.get("limit_page_length") == 0 else []
	with patch.object(V, "_chan", lambda *a, **k: None), patch.object(V, "_cong_ty_xem", lambda: ["CT"]), \
			patch.object(V.frappe, "get_all", get_all, create=True), \
			patch.object(V.frappe.utils, "nowdate", lambda: "2026-10-07", create=True):
		kq = V.ds(nhom="Tiền bán", trang_thai="Chờ tiền về")
	la("số gộp bằng tổng ba trạng thái chờ", kq["dem"]["Chờ tiền về"], 6)
	la("danh sách lọc đúng ba trạng thái đó", sorted(goi[0]["trang_thai_tien"][1]), sorted(K.CHO_TIEN_VE))
	la("lượt đếm dùng phạm vi chung, không kèm nhóm/nguồn/trạng thái", sorted(goi[1]), ["company"])


def _khop_loc(r, loc):
	"""Áp bộ lọc kiểu Frappe (các dạng ds dùng) lên một dòng, để so số trên thẻ với danh sách."""
	for k, v in loc.items():
		x = r.get(k)
		if isinstance(v, list):
			if v[0] == "in" and x not in v[1]:
				return False
			if v[0] == ">" and not ((x or 0) > v[1]):
				return False
		elif x != v:
			return False
	return True


@ca("Codex #450: số trên mỗi thẻ và chip bằng đúng số dòng danh sách khi bấm vào (cùng nhóm, cùng nguồn)")
def _():
	from vagabond import doi_soat_vendor as V
	rows = [
		dict(nhom="Tiền bán", vendor="GrabFood", trang_thai="Lỗi tệp", trang_thai_tien="Chưa đối chiếu", so_chua_noi=0),
		dict(nhom="Tiền bán", vendor="GrabFood", trang_thai="Đã nhận", trang_thai_tien="Lệch tiền về", so_chua_noi=2),
		dict(nhom="Tiền bán", vendor="Payoo", trang_thai="Cần xử lý", trang_thai_tien="Chưa thấy tiền về", so_chua_noi=0),
		dict(nhom="Chuyến đi", vendor="Be", trang_thai="Cần xử lý", trang_thai_tien="Không áp dụng", so_chua_noi=5),
		dict(nhom="Thẻ tín dụng", vendor="Shinhan", trang_thai="Lỗi tệp", trang_thai_tien="Không áp dụng", so_chua_noi=0)]
	for nhom, vendor in (("Tiền bán", ""), ("Tiền bán", "GrabFood"), ("Chuyến đi", ""), ("", "")):
		dem, dem_vendor = V.dem_nguon(rows, nhom, vendor)
		for khoa in ("Cần xử lý", "Chờ tiền về", "Lệch tiền về", "Chưa thấy tiền về", "Chưa nối đủ"):
			loc = dict(V.loc_trang_thai(khoa))
			if nhom:
				loc["nhom"] = nhom
			if vendor:
				loc["vendor"] = vendor
			la("%s/%s/%s: thẻ = danh sách" % (nhom or "mọi nhóm", vendor or "mọi nguồn", khoa), dem.get(khoa, 0),
				sum(1 for r in rows if _khop_loc(r, loc)))
	dem, dem_vendor = V.dem_nguon(rows, "Tiền bán", "GrabFood")
	la("chip nhóm vẫn đếm mọi nhóm", (dem["nhom:Tiền bán"], dem["nhom:Chuyến đi"], dem["nhom:Thẻ tín dụng"]), (3, 1, 1))
	la("chip nguồn đếm trong nhóm đang chọn, bỏ chọn nguồn", (dem_vendor.get("GrabFood"), dem_vendor.get("Payoo"), dem_vendor.get("Be")), (2, 1, None))


@ca("Codex #450: ứng viên hoá đơn chọn theo NGÀY BÁN (vgb_ngay_ban), không theo ngày ghi sổ")
def _():
	import sqlite3
	from vagabond import doi_soat_vendor as V
	dk, bieu = V._dk_hd(True, True)
	c = sqlite3.connect(":memory:")
	c.execute("create table s (name, posting_date, vgb_ngay_ban, docstatus, company, vgb_huy)")
	c.executemany("insert into s values (?,?,?,?,?,?)", [
		("HD-DUYET-SAU", "2026-10-02", "2026-10-01", 1, "CT", 0),  # bán 01/10, duyệt ghi sổ 02/10
		("HD-THUONG", "2026-10-01", None, 1, "CT", 0),
		("HD-BAN-HOM-TRUOC", "2026-10-01", "2026-09-30", 1, "CT", 0),
		("HD-KHAC-PN", "2026-10-01", None, 1, "CT2", 0), ("HD-HUY", "2026-10-01", None, 1, "CT", 1)])
	cau = "select name, %s from s where %s order by name" % (bieu, dk)
	cau = cau.replace("%(tu)s", ":tu").replace("%(den)s", ":den").replace("%(ct)s", ":ct")
	ra = c.execute(cau, dict(tu="2026-10-01", den="2026-10-01", ct="CT")).fetchall()
	la("báo cáo ngày 01/10 gặp đúng bill bán ngày 01/10, trả ngày bán", ra,
		[("HD-DUYET-SAU", "2026-10-01"), ("HD-THUONG", "2026-10-01")])
	dk0, bieu0 = V._dk_hd(False, False)
	dung("site chưa có ô ngày bán: giữ cách cũ", "s.posting_date between %(tu)s and %(den)s" in dk0 and bieu0 == "s.posting_date")


@ca("Codex #450: cả ba truy vấn ứng viên hoá đơn dùng chung điều kiện ngày bán và pháp nhân")
def _():
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V
	cau_ds = []

	class Hang(dict):
		__getattr__ = dict.get

	def sql(cau, tham=None, as_dict=False, **k):
		cau_ds.append((" ".join(cau.split()), dict(tham or {})))
		if "Dong Thanh Toan" in cau:
			return [Hang(parent="HD-2", so_tien=50000, ma_tham_chieu="GD-1", ngay="2026-10-01")]
		return [Hang(name="HD-1", ngay="2026-10-01", grand_total=1, rounded_total=1, vgb_ma_tham_chieu="GF-1")]
	with patch.object(V.frappe, "get_meta", lambda dt: NS(has_field=lambda f: True), create=True), \
			patch.object(V.frappe.db, "sql", sql, create=True), \
			patch.object(V.frappe.db, "table_exists", lambda dt: True, create=True), \
			patch.object(V, "_ma_dong_tt", lambda si: []):
		ra = V._ung_vien_hd("grab", "2026-10-01", "2026-10-01", "CT")
	la("ba truy vấn", len(cau_ds), 3)
	dung("mọi truy vấn lọc theo ngày bán và đúng pháp nhân",
		all("s.vgb_ngay_ban between %(tu)s and %(den)s" in c and "s.company=%(ct)s" in c and t.get("ct") == "CT" for c, t in cau_ds))
	la("ngày trả về là ngày bán", sorted({u["ngay"] for u in ra}), ["2026-10-01"])


@ca("Codex #450: chuyến đi chỉ Đã nối khi đủ mọi chứng từ cần có, thiếu thì nói thiếu gì")
def _():
	f = K.chung_tu_chuyen
	la("giao hàng có vận đơn", f(1, "", "VD-1", None)[0], "Đã nối")
	tt, gc = f(1, "C26TGB#123", "VD-1", None)
	la("giao hàng có hoá đơn riêng: có vận đơn, thiếu hoá đơn mua", tt, "Không thấy chứng từ")
	dung("ghi chú nói có vận đơn và thiếu hoá đơn mua", "Vận đơn VD-1" in gc and "thiếu hoá đơn mua C26TGB số 123" in gc)
	tt, gc = f(1, "C26TGB#123", None, "PI-1")
	la("có hoá đơn mua, thiếu vận đơn", (tt, "thiếu vận đơn" in gc), ("Không thấy chứng từ", True))
	la("đủ cả hai", f(1, "C26TGB#123", "VD-1", "PI-1")[0], "Đã nối")
	la("chuyến thường không cần chứng từ", f(0, "", None, None), ("Chưa nối", ""))
	la("số hoá đơn không kèm ký hiệu (Be, hoá đơn gộp kỳ) không bắt hoá đơn mua từng chuyến", f(0, "0001234", None, None)[0], "Chưa nối")


def _noi_chuyen_that(ncc, pi_ds, dong_ds, mau="grab_business", thuc_nhan=0, den_ngay=None):
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V
	bat = {"pi": [], "ghi": {}}

	class Hang(dict):
		__getattr__ = dict.get

	def get_all(dt, filters=None, **k):
		if dt == "Supplier":
			bat["mst"] = filters.get("tax_id")
			return ncc
		if dt == "Purchase Invoice":
			bat["pi"].append(dict(filters))
			return [Hang(p) for p in pi_ds if p["supplier"] in filters["supplier"][1]]
		return []
	with patch.object(V.frappe, "get_all", get_all, create=True), \
			patch.object(V.frappe.db, "table_exists", lambda dt: False, create=True), \
			patch.object(V.frappe, "get_meta", lambda dt: NS(has_field=lambda f: True), create=True), \
			patch.object(V.frappe.utils, "add_days", lambda d, n: d, create=True), \
			patch.object(V, "_ghi_them", lambda name, **k: bat.update(them=k)), \
			patch.object(V.frappe.db, "set_value", lambda dt, n, v, **k: bat["ghi"].__setitem__(n, v), create=True):
		V._noi_chuyen(NS(mau=mau, company="CT", den_ngay=den_ngay, thuc_nhan=thuc_nhan, tu_ngay=den_ngay, name="N1"),
			[Hang(d) for d in dong_ds])
	return bat


@ca("Codex #450: hoá đơn mua của chuyến chỉ tìm trong nhà cung cấp mang đúng MST người bán")
def _():
	dong = [dict(name="R1", loai="chuyen", ma_su_kien="B1", ma_don="B1", giao_hang=0, hoa_don_nguon="C26TGB#00123")]
	pi = [dict(name="PI-GRAB", supplier="NCC-GRAB", grand_total=1, custom_hddt_ky_hieu="C26TGB"),
		dict(name="PI-KHAC", supplier="NCC-KHAC", grand_total=1, custom_hddt_ky_hieu="C26TGB")]
	bat = _noi_chuyen_that(["NCC-GRAB"], pi, dong)
	la("tra MST Grab", bat["mst"], "0312650437")
	la("lọc theo nhà cung cấp", bat["pi"][0]["supplier"], ["in", ["NCC-GRAB"]])
	la("nối đúng hoá đơn của Grab, không lẫn người bán khác cùng số", bat["ghi"]["R1"]["purchase_invoice"], "PI-GRAB")
	bat = _noi_chuyen_that([], pi, dong)
	la("chưa có nhà cung cấp mang MST: không đoán", (bat["ghi"]["R1"]["purchase_invoice"], bat["ghi"]["R1"]["trang_thai_khop"]),
		(None, "Không thấy chứng từ"))


@ca("Codex #450: Nối theo tiền tính là chưa nối; lọc Cần xem và Đã nối dùng cùng nguồn")
def _():
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V
	bat = {}

	def sql(cau, tham=None, *a, **k):
		bat["tham"] = tham
		return [(3, 2)]
	n = NS(name="N1", db_set=lambda d: bat.update(ghi=d))
	with patch.object(V.frappe.db, "sql", sql, create=True):
		V._dem_noi(n)
	la("chỉ Đã nối là đã nối", bat["tham"]["da"], ("Đã nối",))
	dung("Nối theo tiền nằm trong chưa nối", "Nối theo tiền" not in bat["tham"]["khong"])
	la("ghi số", bat["ghi"], {"so_da_noi": 3, "so_chua_noi": 2})


@ca("Codex #450: kế toán xác nhận gợi ý nối theo tiền; dòng đã xác nhận giữ nguyên khi đối chiếu lại")
def _():
	from contextlib import nullcontext
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V

	class Hang(dict):
		__getattr__ = dict.get
	ghi = {}
	trang = {"tt": "Nối theo tiền"}
	with patch.object(V, "_chan", lambda *a, **k: None), patch.object(V, "_chan_cong_ty", lambda ct: None), \
			patch.object(V, "khoa_doi_chieu", lambda *a, **k: nullcontext()), \
			patch.object(V.frappe.db, "get_value", lambda dt, n, f=None, **k: None if isinstance(n, dict) else Hang(name=n,
				nguon="N1", company="CT", trang_thai_khop=trang["tt"], sales_invoice="SI-9"), create=True), \
			patch.object(V.frappe.db, "set_value", lambda dt, n, v, **k: ghi.__setitem__(n, v), create=True), \
			patch.object(V.frappe, "session", NS(user="ketoan@x"), create=True), \
			patch.object(V.frappe.utils, "now", lambda: "2026-10-07 10:00:00", create=True), \
			patch.object(V.frappe, "get_doc", lambda *a, **k: NS(name="N1"), create=True), \
			patch.object(V, "_goi_y_con_dung", lambda n: True), \
			patch.object(V, "_dem_noi", lambda n: ghi.__setitem__("_dem", n.name)):
		V.xac_nhan_noi(name="R9")
		la("xác nhận: Đã nối, ghi người và lúc", (ghi["R9"]["trang_thai_khop"], ghi["R9"]["xac_nhan_boi"], ghi["R9"]["xac_nhan_luc"]),
			("Đã nối", "ketoan@x", "2026-10-07 10:00:00"))
		la("đếm lại nguồn", ghi["_dem"], "N1")
		trang["tt"] = "Đã nối"
		loi = ""
		try:
			V.xac_nhan_noi(name="R9")
		except Exception as e:
			loi = str(e)
		dung("dòng không còn là gợi ý thì từ chối", "không còn là gợi ý" in loi)
	# Đối chiếu lại: dòng R1 đã xác nhận với SI-1 giữ nguyên; SI-1 không gợi ý cho dòng R2 cùng tiền.
	dong = [Hang(name="R1", loai="ban", ngay="2026-07-17", ma_tham_chieu="", tien_hang=100000, giam_gia=0,
			trang_thai_khop="Đã nối", sales_invoice="SI-1", xac_nhan_boi="ketoan@x"),
		Hang(name="R2", loai="ban", ngay="2026-07-17", ma_tham_chieu="", tien_hang=100000, giam_gia=0,
			trang_thai_khop="Chưa nối", sales_invoice=None, xac_nhan_boi=None)]
	ghi = {}
	with patch.object(V, "_ung_vien_hd", lambda *a: [dict(name="SI-1", ngay="2026-07-17", tien=100000, ma=[""], tien_to="")]), \
			patch.object(V.frappe, "get_all", lambda *a, **k: [], create=True), \
			patch.object(V.frappe.utils, "add_days", lambda d, n: d, create=True), \
			patch.object(V.frappe.db, "set_value", lambda dt, n, v, **k: ghi.__setitem__(n, v), create=True):
		V._noi_hoa_don_ban(NS(mau="grabfood", company="CT", name="N1"), dong)
	dung("dòng đã xác nhận không bị ghi đè", "R1" not in ghi)
	la("hoá đơn đã xác nhận không gợi ý cho dòng khác", (ghi.get("R2") or {}).get("sales_invoice"), None)


@ca("Codex #450: nguồn một hoá đơn cả kỳ (Be, Xanh SM): mọi chuyến cần hoá đơn kỳ; có thì Đã nối, thiếu hay nhiều thì nói rõ")
def _():
	f = K.chung_tu_chuyen
	la("chuyến thường, có hoá đơn kỳ", f(0, "0001234", None, None, dict(pi="PI-KY", nhieu=["PI-KY"]))[0], "Đã nối")
	tt, gc = f(0, "", None, None, dict(pi=None, nhieu=[]))
	la("chuyến thường, chưa có hoá đơn kỳ", (tt, "thiếu hoá đơn mua cả kỳ" in gc), ("Không thấy chứng từ", True))
	la("nhiều hoá đơn cùng tổng tiền", f(0, "", None, None, dict(pi=None, nhieu=["PI-1", "PI-2"]))[0], "Nhiều chứng từ")
	tt, gc = f(1, "", "VD-1", None, dict(pi=None, nhieu=[]))
	la("giao hàng có vận đơn nhưng thiếu hoá đơn kỳ", (tt, "Vận đơn VD-1" in gc), ("Không thấy chứng từ", True))
	la("giao hàng đủ vận đơn và hoá đơn kỳ", f(1, "", "VD-1", None, dict(pi="PI-KY", nhieu=["PI-KY"]))[0], "Đã nối")
	dong = [dict(name="R1", loai="chuyen", ma_su_kien="B1", ma_don="B1", giao_hang=0, hoa_don_nguon="0001234"),
		dict(name="R2", loai="chuyen", ma_su_kien="B2", ma_don="B2", giao_hang=0, hoa_don_nguon="0001234")]
	pi = [dict(name="PI-BE", supplier="NCC-BE", grand_total=500000), dict(name="PI-BE-KHAC", supplier="NCC-BE", grand_total=1)]
	bat = _noi_chuyen_that(["NCC-BE"], pi, dong, mau="be", thuc_nhan=500000, den_ngay="2026-09-30")
	la("_noi_chuyen thật: hoá đơn kỳ đúng tổng làm mọi chuyến Đã nối",
		[bat["ghi"][r]["trang_thai_khop"] for r in ("R1", "R2")], ["Đã nối", "Đã nối"])
	bat = _noi_chuyen_that(["NCC-BE"], pi, dong, mau="be", thuc_nhan=400000, den_ngay="2026-09-30")
	la("_noi_chuyen thật: không có hoá đơn kỳ thì chuyến thiếu chứng từ", bat["ghi"]["R1"]["trang_thai_khop"], "Không thấy chứng từ")


@ca("Codex #450: xác nhận chỉ giữ khi hoá đơn còn hợp lệ và còn đúng tiền; không còn thì quay về xem lại")
def _():
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V
	uv = [dict(name="SI-1", tien=100000)]
	la("còn đúng", K.xac_nhan_con_dung("grab", dict(sales_invoice="SI-1", tien_hang=100000, giam_gia=0), uv), True)
	la("hoá đơn đã huỷ (không còn trong ứng viên)", K.xac_nhan_con_dung("grab", dict(sales_invoice="SI-2", tien_hang=100000, giam_gia=0), uv), False)
	la("hoá đơn đổi tiền", K.xac_nhan_con_dung("grab", dict(sales_invoice="SI-1", tien_hang=90000, giam_gia=0), uv), False)

	class Hang(dict):
		__getattr__ = dict.get
	dong = [Hang(name="R1", loai="ban", ngay="2026-07-17", ma_tham_chieu="", tien_hang=100000, giam_gia=0,
		trang_thai_khop="Đã nối", sales_invoice="SI-HUY", xac_nhan_boi="ketoan@x")]
	ghi = {}
	with patch.object(V, "_ung_vien_hd", lambda *a: [dict(name="SI-1", ngay="2026-07-17", tien=100000, ma=[""], tien_to="")]), \
			patch.object(V.frappe, "get_all", lambda *a, **k: [], create=True), \
			patch.object(V.frappe.utils, "add_days", lambda d, n: d, create=True), \
			patch.object(V.frappe.db, "set_value", lambda dt, n, v, **k: ghi.__setitem__(n, v), create=True):
		V._noi_hoa_don_ban(NS(mau="grabfood", company="CT", name="N1"), dong)
	la("bỏ xác nhận, đối chiếu lại", (ghi["R1"]["xac_nhan_boi"], ghi["R1"]["trang_thai_khop"]), (None, "Nối theo tiền"))
	dung("ghi chú nói hoá đơn cũ không còn hợp lệ", "SI-HUY" in ghi["R1"]["ghi_chu_khop"] and "không còn" in ghi["R1"]["ghi_chu_khop"])


@ca("Codex #450: gợi ý nối theo tiền chưa xác nhận không giữ hoá đơn khỏi dòng có đúng mã ở nguồn khác")
def _():
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V

	class Hang(dict):
		__getattr__ = dict.get
	khac = [dict(sales_invoice="SI-1", trang_thai_khop="Nối theo tiền", nguon="N2")]

	def get_all(dt, filters=None, **k):
		tt = filters.get("trang_thai_khop")
		ra = [r for r in khac if r["nguon"] != filters["nguon"][1] and (tt is None or
			(tt[0] == "in" and r["trang_thai_khop"] in tt[1]) or (tt[0] == "!=" and r["trang_thai_khop"] != tt[1]))]
		return [r["sales_invoice"] for r in ra]
	dong = [Hang(name="R1", loai="ban", ngay="2026-07-17", ma_tham_chieu="GF-1", tien_hang=100000, giam_gia=0,
		trang_thai_khop="Chưa nối", sales_invoice=None, xac_nhan_boi=None)]
	ghi = {}
	with patch.object(V, "_ung_vien_hd", lambda *a: [dict(name="SI-1", ngay="2026-07-17", tien=100000, ma=["GF-1"], tien_to="")]), \
			patch.object(V.frappe, "get_all", get_all, create=True), \
			patch.object(V.frappe.utils, "add_days", lambda d, n: d, create=True), \
			patch.object(V.frappe.db, "set_value", lambda dt, n, v, **k: ghi.__setitem__(n, v), create=True):
		V._noi_hoa_don_ban(NS(mau="grabfood", company="CT", name="N1"), dong)
	la("dòng đúng mã vẫn nối được hoá đơn đang là gợi ý ở nguồn khác", (ghi["R1"]["trang_thai_khop"], ghi["R1"]["sales_invoice"]),
		("Đã nối", "SI-1"))
	khac[0]["trang_thai_khop"] = "Đã nối"
	ghi.clear()
	with patch.object(V, "_ung_vien_hd", lambda *a: [dict(name="SI-1", ngay="2026-07-17", tien=100000, ma=["GF-1"], tien_to="")]), \
			patch.object(V.frappe, "get_all", get_all, create=True), \
			patch.object(V.frappe.utils, "add_days", lambda d, n: d, create=True), \
			patch.object(V.frappe.db, "set_value", lambda dt, n, v, **k: ghi.__setitem__(n, v), create=True):
		V._noi_hoa_don_ban(NS(mau="grabfood", company="CT", name="N1"), dong)
	la("hoá đơn đã nối chắc ở nguồn khác thì không dùng lại", ghi["R1"]["sales_invoice"], None)


@ca("Codex #450: không xác nhận gợi ý khi hoá đơn đó đã nối chắc với dòng khác")
def _():
	from contextlib import nullcontext
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V

	class Hang(dict):
		__getattr__ = dict.get
	ghi = {}
	with patch.object(V, "_chan", lambda *a, **k: None), patch.object(V, "_chan_cong_ty", lambda ct: None), \
			patch.object(V, "khoa_doi_chieu", lambda *a, **k: nullcontext()), \
			patch.object(V.frappe.db, "get_value", lambda dt, n, f=None, **k: "N-KHAC" if isinstance(n, dict) else Hang(name=n,
				nguon="N1", company="CT", trang_thai_khop="Nối theo tiền", sales_invoice="SI-9"), create=True), \
			patch.object(V, "_goi_y_con_dung", lambda n: True), \
			patch.object(V.frappe.db, "set_value", lambda dt, n, v, **k: ghi.__setitem__(n, v), create=True):
		loi = ""
		try:
			V.xac_nhan_noi(name="R9")
		except Exception as e:
			loi = str(e)
	dung("từ chối, nói hoá đơn đã nối ở nguồn khác", "đã nối chắc" in loi and "N-KHAC" in loi)
	la("không ghi gì", ghi, {})


@ca("Codex #450: không tự nhận tiền về khi nguồn chưa đủ dòng, nguồn không có nội dung CK, hay Grab có đơn tiền mặt")
def _():
	la("lý do: Shinhan", bool(K.ly_do_khong_tu_nhan("shinhan_ngay")), True)
	la("lý do: Grab có đơn tiền mặt", bool(K.ly_do_khong_tu_nhan("grabfood", True)), True)
	la("Grab không có tiền mặt, Payoo: được tự nhận", (K.ly_do_khong_tu_nhan("grabfood"), K.ly_do_khong_tu_nhan("payoo_the")), ("", ""))
	tt, ds, ghi = K.khop_ngan_hang("shinhan_ngay", 900000, "2026-07-17", "2026-07-24", [_gd("BT-1", 900000, "x")],
		ly_do_tay=K.ly_do_khong_tu_nhan("shinhan_ngay"))
	la("một giao dịch cùng tiền nhưng phải xem tay", (tt, ds, "BT-1" in ghi), ("Cần chọn tiền về", [], True))
	sh = _tien_ve_that(None, [("BT-1", 900000, "a")])
	la("_tien_ve thật: Shinhan một giao dịch không tự giữ", (sh["trang_thai_tien"], sh["giao_dich_ngan_hang"]), ("Cần chọn tiền về", ""))
	gr = _tien_ve_that(None, [("BT-1", 900000, "Grab TT 1182")], mau="grabfood", tien_mat=1)
	la("_tien_ve thật: Grab có đơn tiền mặt không tự giữ", (gr["trang_thai_tien"], gr["giao_dich_ngan_hang"]), ("Cần chọn tiền về", ""))
	thieu = _tien_ve_that(None, [("BT-1", 900000, "Grab TT 1182")], mau="grabfood", trang_thai="Cần xử lý")
	la("_tien_ve thật: nguồn còn dòng lỗi thì chưa dò tiền về", (thieu["trang_thai_tien"], thieu["giao_dich_ngan_hang"]), ("Chưa đối chiếu", ""))


@ca("Codex #450: hoá đơn mua huỷ mềm không được tính là chứng từ của chuyến")
def _():
	dong = [dict(name="R1", loai="chuyen", ma_su_kien="B1", ma_don="B1", giao_hang=0, hoa_don_nguon="C26TGB#00123")]
	pi = [dict(name="PI-GRAB", supplier="NCC-GRAB", grand_total=1, custom_hddt_ky_hieu="C26TGB")]
	bat = _noi_chuyen_that(["NCC-GRAB"], pi, dong)
	la("tìm theo chuyến lọc vgb_huy", bat["pi"][0].get("vgb_huy"), 0)
	dong_be = [dict(name="R1", loai="chuyen", ma_su_kien="B1", ma_don="B1", giao_hang=0, hoa_don_nguon="")]
	bat = _noi_chuyen_that(["NCC-BE"], [dict(name="PI-BE", supplier="NCC-BE", grand_total=5)], dong_be, mau="be", thuc_nhan=5,
		den_ngay="2026-09-30")
	la("tìm hoá đơn cả kỳ lọc vgb_huy", bat["pi"][0].get("vgb_huy"), 0)


@ca("Codex #450: dòng đã xác nhận không vào lượt khớp, không chiếm hoá đơn cùng tiền của dòng khác")
def _():
	from types import SimpleNamespace as NS
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V

	class Hang(dict):
		__getattr__ = dict.get
	dong = [Hang(name="R1", loai="ban", ngay="2026-07-17", ma_tham_chieu="", tien_hang=100000, giam_gia=0,
			trang_thai_khop="Đã nối", sales_invoice="SI-1", xac_nhan_boi="ketoan@x"),
		Hang(name="R2", loai="ban", ngay="2026-07-17", ma_tham_chieu="", tien_hang=100000, giam_gia=0,
			trang_thai_khop="Chưa nối", sales_invoice=None, xac_nhan_boi=None)]
	ghi = {}
	uv = [dict(name="SI-1", ngay="2026-07-17", tien=100000, ma=[""], tien_to=""),
		dict(name="SI-2", ngay="2026-07-17", tien=100000, ma=[""], tien_to="")]
	with patch.object(V, "_ung_vien_hd", lambda *a: [dict(u) for u in uv]), \
			patch.object(V.frappe, "get_all", lambda *a, **k: [], create=True), \
			patch.object(V.frappe.utils, "add_days", lambda d, n: d, create=True), \
			patch.object(V.frappe.db, "set_value", lambda dt, n, v, **k: ghi.__setitem__(n, v), create=True):
		V._noi_hoa_don_ban(NS(mau="grabfood", company="CT", name="N1"), dong)
	la("dòng chưa nối nhận gợi ý hoá đơn còn lại", ((ghi.get("R2") or {}).get("trang_thai_khop"), (ghi.get("R2") or {}).get("sales_invoice")),
		("Nối theo tiền", "SI-2"))


@ca("Codex #450: bấm xác nhận khi hoá đơn gợi ý không còn hợp lệ thì từ chối")
def _():
	from contextlib import nullcontext
	from unittest.mock import patch
	from vagabond import doi_soat_vendor as V

	class Hang(dict):
		__getattr__ = dict.get
	ghi = {}
	with patch.object(V, "_chan", lambda *a, **k: None), patch.object(V, "_chan_cong_ty", lambda ct: None), \
			patch.object(V, "khoa_doi_chieu", lambda *a, **k: nullcontext()), \
			patch.object(V.frappe.db, "get_value", lambda dt, n, f=None, **k: None if isinstance(n, dict) else Hang(name=n,
				nguon="N1", company="CT", trang_thai_khop="Nối theo tiền", sales_invoice="SI-9"), create=True), \
			patch.object(V, "_goi_y_con_dung", lambda n: False), \
			patch.object(V.frappe.db, "set_value", lambda dt, n, v, **k: ghi.__setitem__(n, v), create=True):
		loi = ""
		try:
			V.xac_nhan_noi(name="R9")
		except Exception as e:
			loi = str(e)
	dung("từ chối, nói hoá đơn không còn hợp lệ", "không còn hợp lệ" in loi)
	la("không ghi gì", ghi, {})
	# _goi_y_con_dung dùng đúng phép kiểm của lượt đối chiếu
	with patch.object(V.frappe.db, "get_value", lambda dt, n, f=None, **k: Hang(nguon="N1", ngay="2026-07-17", tien_hang=100000,
				giam_gia=0, sales_invoice="SI-1") if dt == V.DT_DONG else Hang(mau="grabfood", company="CT"), create=True), \
			patch.object(V.frappe.utils, "add_days", lambda d, n: d, create=True), \
			patch.object(V, "_ung_vien_hd", lambda *a: [dict(name="SI-1", tien=90000)]):
		la("hoá đơn đổi tiền thì gợi ý không còn đúng", V._goi_y_con_dung("R9"), False)
