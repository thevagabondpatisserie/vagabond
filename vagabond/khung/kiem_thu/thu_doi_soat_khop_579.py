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
	la("ai gọi _ghi_nguon", sorted(k for k, f in ham.items() if goi(f, "_ghi_nguon")), ["_nhan_byte"])
	la("hai cửa đều giữ khoá", (co_khoa(ham["_nhan_byte"]), co_khoa(ham["doi_chieu_lai"])), (True, True))
