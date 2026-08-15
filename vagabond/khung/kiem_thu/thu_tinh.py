"""Kiem thu tang thuan khung/tinh.py: doc so, tim chu, dem chip, cong, cat.

Khong nap Frappe. Cac ca o day chay duoc ngay ca khi ca he thong sap.
"""

from vagabond.khung import tinh
from vagabond.khung.kiem_thu.nen import ca, dung, la

CHIP = [
	{"k": "", "ten": "Tất cả", "ic": "📋"},
	{"k": "cho", "ten": "Chờ", "ic": "🚚"},
	{"k": "xong", "ten": "Xong", "ic": "✅"},
	{"k": "huy", "ten": "Đã huỷ", "ic": "✖️"},
	{"k": "da_sua", "ten": "Đã sửa", "ic": "✏️", "phu": 1},
]

COT = [
	{"k": "ma", "nhan": "Mã", "kieu": "chu"},
	{"k": "_chip", "nhan": "Trạng thái", "kieu": "chip"},
	{"k": "tien", "nhan": "Thành tiền", "kieu": "tien"},
	{"k": "gia", "nhan": "Đơn giá", "kieu": "tien", "kc": 1},
]


def _dong(n, chip="cho", tien=1000.0, huy=0, da_sua=0, ten="Hùng Phát"):
	return {
		"ma": "M%03d" % n, "_chip": chip, "tien": tien, "gia": 7.0,
		"vgb_huy": huy, "da_sua": da_sua, "ten": ten,
	}


# ------------------------------------------------------------- doc so hoc

@ca("so() đọc được mọi thứ cơ sở dữ liệu trả về, đọc không ra thì bằng 0")
def _():
	from decimal import Decimal
	la("None", tinh.so(None), 0.0)
	la("chuỗi rỗng", tinh.so(""), 0.0)
	la("Decimal", tinh.so(Decimal("99.99")), 99.99)
	la("chuỗi số", tinh.so("1234.5"), 1234.5)
	la("chuỗi có dấu phẩy", tinh.so("1,234"), 1234.0)
	la("chuỗi rác không làm sập", tinh.so("abc"), 0.0)
	la("số nguyên", tinh.so(7), 7.0)
	la("đúng sai", tinh.so(True), 1.0)


@ca("co() hiểu đúng cờ bật tắt của Frappe")
def _():
	la("None", tinh.co(None), 0)
	la("số 0", tinh.co(0), 0)
	la("chuỗi '0'", tinh.co("0"), 0)
	la("số 1", tinh.co(1), 1)
	la("chuỗi '1'", tinh.co("1"), 1)
	la("chuỗi rỗng", tinh.co(""), 0)


@ca("ngay_chu() cắt đúng ngày dù Frappe trả về kiểu gì")
def _():
	import datetime
	la("kiểu date", tinh.ngay_chu(datetime.date(2026, 8, 15)), "2026-08-15")
	la("chuỗi có giờ", tinh.ngay_chu("2026-08-15 23:59:00"), "2026-08-15")
	la("chuỗi ngày", tinh.ngay_chu("2026-08-15"), "2026-08-15")
	la("None", tinh.ngay_chu(None), "")
	dung("so sánh chuỗi cho đúng thứ tự ngày",
		tinh.ngay_chu("2026-07-31") < tinh.ngay_chu("2026-08-01"))


# ---------------------------------------------------------------- tim chu

@ca("tìm chữ khớp theo từ, không đòi đúng nguyên cụm")
def _():
	ds = [_dong(1, ten="Hùng Phát"), _dong(21, ten="Hùng Phát"), _dong(3, ten="Anh Đào")]
	la("gõ hai từ khác thứ tự vẫn ra",
		len(tinh.tim(ds, "phát hùng", ["ma", "ten"])), 2)
	la("gõ tên kèm số đơn ra đúng một dòng",
		len(tinh.tim(ds, "hùng 021", ["ma", "ten"])), 1)
	la("không gõ gì thì giữ hết", len(tinh.tim(ds, "", ["ma", "ten"])), 3)
	la("gõ chữ không có thì ra rỗng", len(tinh.tim(ds, "xyz", ["ma", "ten"])), 0)
	la("không khai ô tìm thì giữ hết", len(tinh.tim(ds, "hùng", [])), 3)


# --------------------------------------------------------- dem va loc chip

@ca("đếm chip trên TOÀN BỘ tập, đếm rồi mới lọc")
def _():
	ds = ([_dong(i, "cho") for i in range(5)]
		+ [_dong(i, "xong") for i in range(3)]
		+ [_dong(i, "huy") for i in range(2)])
	kq = tinh.dung_bang(ds, COT, ds_chip=CHIP, chon="cho", tran=600)
	dem = kq["chip"]["dem"]
	la("chip đang chọn", dem["cho"], 5)
	la("chip KHÁC vẫn còn số, không bị lọc về 0", dem["xong"], 3)
	la("chip huỷ vẫn còn số", dem["huy"], 2)
	la("khoá rỗng là tổng cả tập", dem[""], 10)
	la("chỉ hiện dòng của chip đang chọn", len(kq["dong"]), 5)


@ca("chip phụ đếm riêng, không loại trừ với chip chính")
def _():
	ds = [_dong(1, "cho", da_sua=1), _dong(2, "cho"), _dong(3, "xong", da_sua=1)]
	kq = tinh.dung_bang(ds, COT, ds_chip=CHIP, chon="", tran=600)
	la("một tờ vừa Chờ vừa Đã sửa được đếm ở cả hai", kq["chip"]["dem"]["cho"], 2)
	la("chip phụ đếm đủ cả hai tờ", kq["chip"]["dem"]["da_sua"], 2)
	k2 = tinh.dung_bang(ds, COT, ds_chip=CHIP, chon="da_sua", tran=600)
	la("bấm chip phụ ra đúng các tờ đã sửa", len(k2["dong"]), 2)
	la("bấm chip phụ không làm sai số đếm chip chính",
		k2["chip"]["dem"]["cho"], 2)


@ca("đổi bộ lọc thì số đếm chip đổi theo tập mới")
def _():
	ds = [_dong(1, "cho", ten="Hùng Phát"), _dong(2, "cho", ten="Anh Đào"),
		_dong(3, "xong", ten="Anh Đào")]
	loc = tinh.tim(ds, "anh đào", ["ten"])
	kq = tinh.dung_bang(loc, COT, ds_chip=CHIP, chon="", tran=600)
	la("đếm trên tập đã lọc chữ, không phải tập gốc", kq["chip"]["dem"][""], 2)
	la("chip Chờ chỉ còn một", kq["chip"]["dem"]["cho"], 1)


# -------------------------------------------------------------- cat dong

@ca("cắt đúng ở mốc trần, không lệch một dòng")
def _():
	for so, hien, cat in [(299, 299, 0), (300, 300, 0), (301, 300, 1), (600, 300, 300)]:
		ds = [_dong(i) for i in range(so)]
		kq = tinh.dung_bang(ds, COT, tran=300)
		la("%d dòng thì hiện" % so, len(kq["dong"]), hien)
		la("%d dòng thì giấu" % so, kq["bi_cat"], cat)
		la("%d dòng thì tổng dòng vẫn đủ" % so, kq["tong_dong"], so)


@ca("đường xuất đầy đủ không bao giờ bị trần chặn")
def _():
	ds = [_dong(i) for i in range(1000)]
	kq = tinh.dung_bang(ds, COT, tran=300, day_du=1)
	la("lấy đủ cả nghìn dòng", len(kq["dong"]), 1000)
	la("không báo cắt", kq["bi_cat"], 0)


@ca("trần bằng 0 nghĩa là không cắt")
def _():
	kq = tinh.dung_bang([_dong(i) for i in range(50)], COT, tran=0)
	la("giữ nguyên", len(kq["dong"]), 50)
	la("không báo cắt", kq["bi_cat"], 0)


# ----------------------------------------------------------------- cong

@ca("cộng TRƯỚC khi cắt dòng, không bao giờ cộng trên phần đang hiện")
def _():
	ds = [_dong(i, tien=1000.0) for i in range(1000)]
	kq = tinh.dung_bang(ds, COT, tran=300,
		tom_tat_khai=[("tien", "Tổng tiền", "tien")])
	la("thẻ tóm tắt cộng đủ 1000 dòng", kq["tom_tat"][0]["gt"], 1000000.0)
	la("màn chỉ hiện 300", len(kq["dong"]), 300)
	la("dòng TỔNG cộng đủ phần đã lọc, không phải phần đang hiện",
		kq["cong"]["tien"], 1000000.0)


@ca("cột đánh dấu không cộng thì không xuất hiện ở dòng TỔNG")
def _():
	kq = tinh.dung_bang([_dong(i) for i in range(3)], COT, tran=600)
	dung("cột Thành tiền có cộng", "tien" in kq["cong"])
	dung("cột Đơn giá KHÔNG cộng", "gia" not in kq["cong"])


@ca("đơn huỷ không được cộng vào tiền thật, nhưng vẫn nằm trong dòng TỔNG")
def _():
	ds = [_dong(1, tien=100.0), _dong(2, tien=200.0), _dong(3, "huy", tien=500.0, huy=1)]
	kq = tinh.dung_bang(ds, COT, ds_chip=CHIP, tran=600,
		tinh_dong=lambda r: not tinh.co(r.get("vgb_huy")),
		tom_tat_khai=[("_dong", "Số đơn", "so"), ("tien", "Tiền thật", "tien")])
	la("tiền thật loại đơn huỷ", kq["tom_tat"][1]["gt"], 300.0)
	la("đếm số đơn cũng loại đơn huỷ", kq["tom_tat"][0]["gt"], 2)
	la("dòng TỔNG là phép cộng của đúng những dòng đang hiện", kq["cong"]["tien"], 800.0)
	la("cả ba dòng vẫn hiện trên màn", len(kq["dong"]), 3)


@ca("thẻ tóm tắt không đổi khi bấm chip, đúng như đường cũ")
def _():
	ds = [_dong(1, "cho", tien=100.0), _dong(2, "xong", tien=200.0)]
	the = [("tien", "Tiền thật", "tien")]
	a = tinh.dung_bang(ds, COT, ds_chip=CHIP, chon="", tran=600, tom_tat_khai=the)
	b = tinh.dung_bang(ds, COT, ds_chip=CHIP, chon="cho", tran=600, tom_tat_khai=the)
	la("bấm chip xong thẻ vẫn là tổng cả tập",
		b["tom_tat"][0]["gt"], a["tom_tat"][0]["gt"])
	la("nhưng dòng TỔNG thì đổi theo chip", b["cong"]["tien"], 100.0)


@ca("bật công tắc tính theo chip thì thẻ mới đổi theo chip")
def _():
	ds = [_dong(1, "cho", tien=100.0), _dong(2, "xong", tien=200.0)]
	kq = tinh.dung_bang(ds, COT, ds_chip=CHIP, chon="cho", tran=600,
		tom_tat_khai=[("tien", "Tiền thật", "tien")], tom_tat_theo_chip=1)
	la("thẻ chạy theo chip đang bấm", kq["tom_tat"][0]["gt"], 100.0)


# ----------------------------------------------------------- truong hop bien

@ca("tập rỗng không làm sập màn, mọi con số về 0")
def _():
	kq = tinh.dung_bang([], COT, ds_chip=CHIP, tran=300,
		tom_tat_khai=[("tien", "Tiền", "tien")])
	la("không dòng nào", len(kq["dong"]), 0)
	la("tổng dòng bằng 0", kq["tong_dong"], 0)
	la("không báo cắt", kq["bi_cat"], 0)
	la("thẻ bằng 0", kq["tom_tat"][0]["gt"], 0.0)
	la("chip Tất cả bằng 0", kq["chip"]["dem"][""], 0)


@ca("bấm chip không có dòng nào thì ra rỗng chứ không ra cả tập")
def _():
	ds = [_dong(1, "cho"), _dong(2, "cho")]
	kq = tinh.dung_bang(ds, COT, ds_chip=CHIP, chon="huy", tran=600)
	la("không dòng nào", len(kq["dong"]), 0)
	la("nhưng chip Chờ vẫn báo còn hai", kq["chip"]["dem"]["cho"], 2)


@ca("ô tiền để trống được đọc là 0 chứ không làm sập phép cộng")
def _():
	ds = [_dong(1, tien=100.0), _dong(2, tien=None), _dong(3, tien="")]
	kq = tinh.dung_bang(ds, COT, tran=600)
	la("cộng bỏ qua ô trống", kq["cong"]["tien"], 100.0)


@ca("màn không khai chip vẫn chạy bình thường")
def _():
	kq = tinh.dung_bang([_dong(i) for i in range(4)], COT, tran=600)
	la("hiện đủ dòng", len(kq["dong"]), 4)
	la("vẫn có khoá rỗng để biết tổng", kq["chip"]["dem"][""], 4)
