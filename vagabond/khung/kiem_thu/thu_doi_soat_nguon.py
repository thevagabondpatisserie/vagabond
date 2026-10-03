"""#420: tiền sai không thành 0, nguồn nhận lại không mất lỗi hoặc cộng trùng.

Fixture giả, không chép báo cáo vendor, người nhận thư hay dữ liệu khách.
Đây là ca phần thuần, không thay ca tích hợp lưu nguồn và phân bổ sao kê.
"""
from copy import deepcopy
from decimal import Decimal, localcontext

from vagabond.doi_soat_nguon import LoiNguon, chuan_dong, doc_tien, xem_truoc
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem


def _nguon(**doi):
	ra = dict(cong_ty="Cong ty thu", vendor="Vendor thu", merchant="M-001",
		tien_te="VND", tu_ngay="2026-09-01", den_ngay="2026-09-30",
		dinh_dang="chuan", so_dong=1, tong_thuc_nhan="216000")
	ra.update(doi)
	return ra


def _dong(**doi):
	ra = dict(cong_ty="Cong ty thu", vendor="Vendor thu", merchant="M-001",
		tien_te="VND", ma_su_kien="E-001", ma_don="0001", loai="ban",
		ngay="2026-09-03", tien_hang="270000", phi="54000",
		dieu_chinh="0", thuc_nhan="216000")
	ra.update(doi)
	return ra


for _gia, _mau, _mong in [("1.234,56", "vi", "1234.56"),
	("1,234.56", "en", "1234.56"), ("1234.56", "chuan", "1234.56"),
	("-1.234,56", "vi", "-1234.56"), ("0", "vi", "0"),
	(Decimal("1234.56"), "vi", "1234.56"), (1234, "en", "1234")]:
	@ca("Đối soát nguồn: đọc đúng %r theo %s" % (_gia, _mau))
	def _(gia=_gia, mau=_mau, mong=_mong):
		la("tiền gốc", doc_tien(gia, mau), Decimal(mong))


for _gia in (None, "", "NaN", "Infinity", "1e3", "abc", True, 0.1,
	"1,2,3", "1.000.00", "1 000", "1.234", "1,234", "100 đ",
	"1000000000000000", "-Infinity", Decimal("NaN")):
	@ca("Đối soát nguồn: chặn tiền sai %r" % (_gia,))
	def _(gia=_gia):
		nem("không đoán hoặc thay bằng 0", lambda: doc_tien(gia, "chuan"), LoiNguon)


@ca("Đối soát nguồn: không tự chọn locale hoặc nhân nghìn")
def _():
	nem("thiếu định dạng", lambda: doc_tien("1000", None), LoiNguon)
	la("140 vẫn là 140 đồng", doc_tien("140", "vi"), Decimal(140))
	la("68.216 vi là 68216", doc_tien("68.216", "vi"), Decimal(68216))
	nem("68.216 en vượt số lẻ cho phép", lambda: doc_tien("68.216", "en"), LoiNguon)
	nem("phân nhóm nghìn sai", lambda: doc_tien("1.00,00", "vi"), LoiNguon)


@ca("Đối soát nguồn: giữ mã đơn có số 0 đầu và không thay input")
def _():
	nguon, dong = _nguon(), _dong()
	cu = deepcopy((nguon, dong))
	ra = xem_truoc(nguon, [dong])
	la("mã đơn", ra["dong"][0]["dong"]["ma_don"], "0001")
	la("đủ nguồn", ra["du_nguon"], True)
	la("đầu vào không đổi", (nguon, dong), cu)


@ca("Đối soát nguồn: cùng sự kiện ở kỳ ngày và tháng có cùng khóa")
def _():
	a = chuan_dong(_nguon(), _dong())
	b = chuan_dong(_nguon(tu_ngay="2026-09-03", den_ngay="2026-09-03"), _dong())
	la("khóa", a["khoa"], b["khoa"])
	la("dấu nội dung", a["dau_noi_dung"], b["dau_noi_dung"])
	la("tiền viết khác vẫn cùng nội dung", a["dau_noi_dung"],
		chuan_dong(_nguon(), _dong(tien_hang="270000.00"))["dau_noi_dung"])


@ca("Đối soát nguồn: nhận lại toàn bộ hoặc một phần không cộng thành dòng mới")
def _():
	dong = chuan_dong(_nguon(), _dong())
	da_nhan = {dong["khoa"]: dong["dau_noi_dung"]}
	ra = xem_truoc(_nguon(), [_dong()], da_nhan)
	la("nhận lại", ra["dem"], dict(moi=0, trung=1, loi=0))
	la("tổng nguồn vẫn giữ", ra["tong_doc_duoc"], "216000.00")
	ra = xem_truoc(_nguon(so_dong=2, tong_thuc_nhan="432000"),
		[_dong(), _dong(ma_su_kien="E-002")], da_nhan)
	la("nhận tiếp", ra["dem"], dict(moi=1, trung=1, loi=0))
	la("đủ nguồn", ra["du_nguon"], True)
	la("snapshot không đổi", len(da_nhan), 1)


@ca("Đối soát nguồn: file sửa cùng ID phải hiện lỗi, không ghi đè")
def _():
	dong = chuan_dong(_nguon(), _dong())
	ra = xem_truoc(_nguon(tong_thuc_nhan="215000"), [_dong(phi="55000", thuc_nhan="215000")],
		{dong["khoa"]: dong["dau_noi_dung"]})
	la("giữ dòng lỗi", ra["dem"]["loi"], 1)
	la("không khép", ra["du_nguon"], False)


@ca("Đối soát nguồn: trùng sự kiện trong một file không được chốt dù tổng khớp")
def _():
	ra = xem_truoc(_nguon(so_dong=2, tong_thuc_nhan="432000"), [_dong(), _dong()])
	la("số dòng đầu vào giữ đủ", len(ra["dong"]), 2)
	la("cả nhóm trùng phải chờ", ra["dem"], dict(moi=0, trung=0, loi=2))
	la("không khép", ra["du_nguon"], False)


for _ten, _gia in [("merchant", "M-002"), ("cong_ty", "Cong ty khac"),
	("vendor", "Vendor khac"), ("tien_te", "USD"), ("ma_su_kien", ""),
	("ma_don", ""), ("ngay", "2026-10-01"), ("ngay", "2026-09-31"),
	("ngay", "03/09/2026"), ("loai", "khong_biet"), ("thuc_nhan", "216001")]:
	@ca("Đối soát nguồn: giữ lỗi dòng %s=%s" % (_ten, _gia))
	def _(ten=_ten, gia=_gia):
		ra = xem_truoc(_nguon(so_dong=2, tong_thuc_nhan="432000"),
			[_dong(**{ten: gia}), _dong(ma_su_kien="E-002")])
		la("vẫn thấy hai dòng", len(ra["dong"]), 2)
		la("dòng kế vẫn chạy", ra["dem"], dict(moi=1, trung=0, loi=1))
		la("giữ số dòng lỗi", ra["dong"][0]["vi_tri"], 1)
		dung("câu hướng dẫn", bool(ra["dong"][0]["ly_do"]))
		la("không khép", ra["du_nguon"], False)


@ca("Đối soát nguồn: merchant khác không dùng chung khóa sự kiện")
def _():
	a = chuan_dong(_nguon(), _dong())
	b = chuan_dong(_nguon(merchant="M-002"), _dong(merchant="M-002"))
	dung("khóa tách merchant", a["khoa"] != b["khoa"])


@ca("Đối soát nguồn: hoàn âm và phí đảo không bị biến thành doanh thu dương")
def _():
	ra = xem_truoc(_nguon(tong_thuc_nhan="-216000"),
		[_dong(loai="hoan", tien_hang="-270000", phi="-54000", thuc_nhan="-216000")])
	la("đủ nguồn hoàn", ra["du_nguon"], True)
	la("giữ dấu", ra["tong_doc_duoc"], "-216000.00")
	nem("hoàn không được dương", lambda: chuan_dong(_nguon(), _dong(loai="hoan")), LoiNguon)
	nem("bán không âm", lambda: chuan_dong(_nguon(),
		_dong(tien_hang="-270000", phi="-54000", thuc_nhan="-216000")), LoiNguon)


@ca("Đối soát nguồn: thiếu dòng hoặc tổng khác phải giữ chờ")
def _():
	for nguon in (_nguon(so_dong=2), _nguon(tong_thuc_nhan="216001")):
		la("không khép", xem_truoc(nguon, [_dong()])["du_nguon"], False)
	la("file rỗng", xem_truoc(_nguon(so_dong=0, tong_thuc_nhan="0"), [])["du_nguon"], False)
	for nguon in (_nguon(so_dong=None), _nguon(so_dong=True), _nguon(tong_thuc_nhan=None),
		_nguon(tien_te="USD"), _nguon(tu_ngay="2026-10-01")):
		nem("nguồn không rõ", lambda: xem_truoc(nguon, [_dong()]), LoiNguon)


@ca("Đối soát nguồn: tính tiền không phụ thuộc Decimal context của caller")
def _():
	with localcontext() as canh:
		canh.prec = 6
		ra = xem_truoc(_nguon(tong_thuc_nhan="123456789.12"),
			[_dong(tien_hang="123456789.13", phi="0.01", thuc_nhan="123456789.12")])
	la("giữ số lẻ", ra["tong_doc_duoc"], "123456789.12")
	la("đủ", ra["du_nguon"], True)
	with localcontext() as canh:
		canh.prec = 6
		la("sát trần không bị làm tròn", doc_tien("999999999999999.99", "chuan"),
			Decimal("999999999999999.99"))


@ca("Đối soát nguồn: nhiều bản mâu thuẫn trong file đều phải chờ, không chọn bản đầu")
def _():
	ra = xem_truoc(_nguon(so_dong=3, tong_thuc_nhan="650000"),
		[_dong(), _dong(thuc_nhan="217000", phi="53000"), _dong(thuc_nhan="217000", phi="53000")])
	la("giữ ba lỗi", ra["dem"], dict(moi=0, trung=0, loi=3))
	la("không khép dù tổng khớp", ra["du_nguon"], False)
