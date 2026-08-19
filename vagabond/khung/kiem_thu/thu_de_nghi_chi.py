"""Kiểm thử Đề nghị chi nội bộ.

Bốn điểm anh Việt chốt 19/08/2026 đều có ca kiểm riêng chốt lại, vì đây là
những chỗ mà nếu lặng lẽ hỏng thì tiền đi sai đường mà không ai biết:

    1. Ngưỡng 2.000.000đ thêm cấp giám đốc.
    2. Tạm ứng tách khỏi chi phí.
    3. Chặn trùng số hoá đơn.
    4. Chặn phân loại tài sản cố định.

Con số và tên vai trong bộ ca này lấy từ site thật ngày 19/08/2026: Uyên giữ
vai AP Officer, chị Dung giữ AP Kiểm soát (FIN), anh Việt và Dễ giữ AP Giám
đốc, và cây tài khoản có sẵn 6429 dành cho chi phí không hoá đơn.
"""

from vagabond import de_nghi_chi as dn
from vagabond.khung.kiem_thu.nen import ca, dung, la


# Danh mục loại chứng từ giả lập, đủ hai cờ mà các hàm THUẦN cần.
#
# Vì sao truyền vào chứ không đọc cơ sở dữ liệu: `thieu_gi` và `ly_do_chan`
# phải kiểm thử được mà không cần site, nên chúng nhận danh mục qua khoá
# `_dm_chung_tu` thay vì tự đi hỏi. Bộ ca này là chỗ chứng minh điều đó.
CT_VAT = "Hoá đơn VAT"
CT_KHONG = "Bảng kê không hoá đơn"
DM_GIA = {
	CT_VAT: {"la_hoa_don_vat": 1, "bat_buoc_tep": 1},
	CT_KHONG: {"la_hoa_don_vat": 0, "bat_buoc_tep": 0},
}


def _khoan(**k):
	"""Một dòng bảng kê hợp lệ tối thiểu."""
	d = {
		"noi_dung": "Mua đá cho quầy",
		"so_tien": 150000,
		"phan_loai": "Mua đồ cúng",
		"loai_chung_tu": CT_KHONG,
		"_co_tep": 1,
	}
	d.update(k)
	return d


def _phieu(**k):
	"""Dựng một phiếu hợp lệ tối thiểu, rồi cho ca kiểm sửa đúng phần nó soi.

	Đổi 20/08/2026 sang bảng kê nhiều dòng: nội dung, số tiền, phân loại và
	hoá đơn nay nằm ở `cac_khoan`. Các ca kiểm bên dưới sửa dòng qua tham số
	`khoan=`, hoặc truyền thẳng `cac_khoan=` khi cần nhiều dòng.
	"""
	khoan = k.pop("khoan", None)
	p = {
		"loai_nghiep_vu": dn.NV_CHI_PHI,
		"ngay_can_tt": "2026-08-20",
		"hinh_thuc": dn.HT_NHAN_VIEN,
		"phuong_thuc": dn.PT_TIEN_MAT,
		"cac_khoan": [_khoan(**(khoan or {}))],
		"_dm_chung_tu": DM_GIA,
	}
	p.update(k)
	return p


# ------------------------------------------------ 1. ngưỡng thêm cấp duyệt

@ca("ngưỡng: dưới 2 triệu thì Uyên duyệt xong là sang thẳng kế toán")
def _():
	dung("một trăm năm mươi nghìn thì không cần giám đốc",
		not dn.can_giam_doc_duyet(150000))
	la("sang thẳng kế toán", dn.buoc_ke_tiep(150000), dn.TT_CHO_KE_TOAN)


@ca("ngưỡng: đúng 2 triệu chẵn vẫn phải lên giám đốc")
def _():
	# Moc tron la moc nguoi ta hay bam vao de lach: mot phieu 1.999.000 va
	# mot phieu 2.000.000 khong khac gi nhau ve ban chat, nen de moc nam
	# TRONG phan bi kiem chu khong nam ngoai.
	dung("đúng ngưỡng là phải duyệt", dn.can_giam_doc_duyet(2000000))
	la("rơi vào bước giám đốc", dn.buoc_ke_tiep(2000000), dn.TT_CHO_GIAM_DOC)
	dung("thiếu một nghìn thì chưa cần", not dn.can_giam_doc_duyet(1999000))


@ca("ngưỡng: đổi ngưỡng thì mọi phép đổi theo, không có số nào viết cứng")
def _():
	dung("ngưỡng năm trăm nghìn thì hai trăm nghìn vẫn dưới",
		not dn.can_giam_doc_duyet(200000, 500000))
	dung("ngưỡng năm trăm nghìn thì sáu trăm nghìn đã trên",
		dn.can_giam_doc_duyet(600000, 500000))
	la("ngưỡng mặc định đúng hai triệu", dn.NGUONG_GIAM_DOC, 2000000)


# --------------------------------------------- 2. tạm ứng tách khỏi chi phí

@ca("tạm ứng: nhận ra đúng loại nghiệp vụ")
def _():
	dung("tạm ứng là tạm ứng", dn.la_tam_ung(dn.NV_TAM_UNG))
	dung("chi phí không phải tạm ứng", not dn.la_tam_ung(dn.NV_CHI_PHI))
	dung("để trống thì không phải tạm ứng", not dn.la_tam_ung(""))


@ca("tạm ứng: ứng lương và cash back không còn nằm trong danh sách chi phí")
def _():
	# Day la ly do ton tai cua truong Loai nghiep vu. De chung mot danh sach
	# thi chi Dung phai tu nho ma dinh khoan khac di cho hai dong do.
	for x in dn.PL_TAM_UNG:
		dung("%s phải nằm ngoài danh sách chi phí" % x,
			x not in dn.TK_THEO_PHAN_LOAI)
	la("danh sách chi phí còn đúng 31 mục", len(dn.PHAN_LOAI), 31)
	la("có đúng hai loại tạm ứng", len(dn.PL_TAM_UNG), 2)


@ca("tạm ứng: đã có hoá đơn VAT thì không còn là tạm ứng nữa")
def _():
	# Tam ung la tien dua TRUOC, chua tieu nen chua the co hoa don. Co hoa
	# don roi tuc la da tieu, do la hoan ung.
	ly_do = dn.ly_do_chan(_phieu(
		loai_nghiep_vu=dn.NV_TAM_UNG,
		khoan={"phan_loai": None, "loai_chung_tu": CT_VAT}))
	dung("phải chặn lại", bool(ly_do))
	dung("và nói rõ nên đổi sang hoàn ứng", "hoàn ứng" in (ly_do or ""))


# ------------------------------------------------ 3. chặn trùng số hoá đơn

@ca("trùng hoá đơn: cùng mã số thuế, cùng số, cùng ngày là cùng một tờ")
def _():
	a = dn.khoa_trung_hoa_don("0318561568", "0000123", "2026-08-19")
	b = dn.khoa_trung_hoa_don("0318561568", "0000123", "2026-08-19")
	la("hai lần đọc ra cùng một khoá", a, b)


@ca("trùng hoá đơn: khoảng trắng và chữ hoa thường không đẻ ra tờ thứ hai")
def _():
	# Hai ban cung chup mot to bill, mot ban go "HD 0123", ban kia go
	# "hd0123". Neu so chuoi tho thi lot thanh hai to khac nhau.
	a = dn.khoa_trung_hoa_don("0318561568", "HD 0123", "2026-08-19")
	b = dn.khoa_trung_hoa_don("0318561568", "hd0123", "2026-08-19")
	la("vẫn là một tờ", a, b)


@ca("trùng hoá đơn: khác ngày hoặc khác người bán thì là tờ khác")
def _():
	goc = dn.khoa_trung_hoa_don("0318561568", "0000123", "2026-08-19")
	dung("khác ngày là tờ khác",
		dn.khoa_trung_hoa_don("0318561568", "0000123", "2026-08-20") != goc)
	dung("khác mã số thuế là tờ khác",
		dn.khoa_trung_hoa_don("0309251922", "0000123", "2026-08-19") != goc)


@ca("trùng hoá đơn: không có số hoá đơn thì không dựng khoá, khỏi bắt oan")
def _():
	dung("để trống thì không có khoá",
		dn.khoa_trung_hoa_don("0318561568", "", "2026-08-19") is None)
	dung("None cũng vậy", dn.khoa_trung_hoa_don(None, None, None) is None)


# --------------------------------------------- 4. chặn tài sản cố định

@ca("chặn: mua máy móc tài sản cố định không đi đường chi lặt vặt")
def _():
	ly_do = dn.ly_do_chan(_phieu(khoan={"phan_loai": "Mua máy móc-tài sản cố định"}))
	dung("phải chặn lại", bool(ly_do))
	dung("và chỉ sang luồng mua hàng", "Đơn mua hàng" in (ly_do or ""))


@ca("chặn: các phân loại khác thì không chặn oan")
def _():
	for x in ("Mua đồ cúng", "Tiền điện", "Phí in ấn", "Vận chuyển"):
		dung("%s phải đi qua được" % x, dn.ly_do_chan(_phieu(khoan={"phan_loai": x})) is None)


# ----------------------------------------- tài khoản gợi ý theo phân loại

@ca("tài khoản: không có hoá đơn VAT thì gợi ý 6429 bất kể phân loại")
def _():
	# Cay tai khoan da co san 6429 "Chi phi khong co hoa don (loai khi quyet
	# toan thue)". Dung luon thay vi de lan vao chi phi thuong roi cuoi nam
	# ngoi boc tach lai.
	for x in ("Mua đồ cúng", "Tiền điện", "Phí ngân hàng"):
		la("phân loại %s không hoá đơn" % x,
			dn.tk_goi_y(x, dn.CT_KHONG_VAT), "6429")


@ca("tài khoản: có hoá đơn VAT thì gợi ý theo đúng phân loại")
def _():
	la("tiền điện", dn.tk_goi_y("Tiền điện", dn.CT_CO_VAT), "6427")
	la("phí ngân hàng", dn.tk_goi_y("Phí ngân hàng", dn.CT_CO_VAT), "635")
	la("nộp thuế", dn.tk_goi_y("Nộp thuế", dn.CT_CO_VAT), "6425")
	la("mua công cụ dụng cụ", dn.tk_goi_y("Mua công cụ dụng cụ", dn.CT_CO_VAT), "6423")


@ca("tài khoản: phân loại lạ thì không đoán bừa")
def _():
	dung("phân loại không có trong danh mục thì trả về rỗng",
		dn.tk_goi_y("Mua tàu vũ trụ", dn.CT_CO_VAT) is None)
	dung("để trống cũng vậy", dn.tk_goi_y("", dn.CT_CO_VAT) is None)


@ca("tài khoản: mọi phân loại chi phí đều có chỗ hạch toán, trừ tài sản cố định")
def _():
	# Bo sot mot phan loai thi phieu do rot xuong khong co tai khoan, va chi
	# Dung phai tu chon lai tung to. Ca kiem nay chot khong bo sot cai nao.
	thieu = [x for x, tk in dn.TK_THEO_PHAN_LOAI.items() if not tk]
	la("chỉ đúng một phân loại không có tài khoản", len(thieu), 1)
	la("và đó là tài sản cố định", thieu[0], "Mua máy móc-tài sản cố định")
	dung("phân loại đó nằm trong danh sách chặn", thieu[0] in dn.CHAN_TSCD)


# ------------------------------- hoá đơn VAT thì phải có nhà cung cấp

@ca("nhà cung cấp: trả cho nhà cung cấp thì đương nhiên phải chọn")
def _():
	dung("bắt buộc", dn.can_chon_ncc(dn.HT_NCC, dn.CT_KHONG_VAT))


@ca("nhà cung cấp: hoàn tiền nhân viên mà CÓ hoá đơn VAT thì vẫn phải chọn")
def _():
	# Day la cho ban mo ta ban dau ho. Ban nhan vien bo tien tui mua va lay
	# hoa don VAT mang ten Vagabond: hoa don la cua NGUOI BAN, con tien tra
	# lai cho NHAN VIEN. Thieu nguoi ban thi khong lap duoc hoa don mua, ma
	# khong co hoa don mua thi khoan do khong len bang ke mua vao 01-2/GTGT
	# va thue dau vao khong khau tru duoc.
	dung("vẫn bắt buộc", dn.can_chon_ncc(dn.HT_NHAN_VIEN, dn.CT_CO_VAT))
	thieu = dn.thieu_gi(_phieu(
		hinh_thuc=dn.HT_NCC,
		khoan={"loai_chung_tu": CT_VAT, "so_hoa_don": "123",
		       "ngay_hoa_don": "2026-08-19", "mst": "0301340144"}))
	dung("và báo thiếu nhà cung cấp",
		any("Nhà cung cấp" in x for x in thieu))


@ca("nhà cung cấp: hoàn tiền nhân viên không hoá đơn thì khỏi chọn")
def _():
	dung("không bắt buộc", not dn.can_chon_ncc(dn.HT_NHAN_VIEN, dn.CT_KHONG_VAT))
	la("và phiếu đủ điều kiện gửi duyệt", dn.thieu_gi(_phieu()), [])


# ------------------------------------------------- soát thiếu trước khi gửi

@ca("soát thiếu: báo một lượt cả danh sách chứ không bắt sửa từng cái")
def _():
	# Nguoi lap sua mot cai roi bam lai moi biet con thieu cai nua la kieu
	# lam nguoi ta bo cuoc giua chung.
	thieu = dn.thieu_gi({
		"loai_nghiep_vu": dn.NV_CHI_PHI,
		"cac_khoan": [{"_co_tep": 1}],
		"_dm_chung_tu": DM_GIA,
	})
	dung("báo từ bốn thứ trở lên trong một lần", len(thieu) >= 4)
	for x in ("nội dung chi", "Ngày cần thanh toán", "phân loại chi phí"):
		dung("có nhắc %s" % x, any(x in t for t in thieu))


@ca("soát thiếu: số tiền phải lớn hơn không")
def _():
	dung("số không thì chặn",
		any("lớn hơn 0" in x for x in dn.thieu_gi(_phieu(khoan={"so_tien": 0}))))
	dung("số âm cũng chặn",
		any("lớn hơn 0" in x for x in dn.thieu_gi(_phieu(khoan={"so_tien": -5000}))))


@ca("soát thiếu: có hoá đơn VAT thì đòi đủ số, ngày và mã số thuế")
def _():
	thieu = dn.thieu_gi(_phieu(nha_cung_cap="NCC-001",
		khoan={"loai_chung_tu": CT_VAT}))
	for x in ("số hoá đơn", "ngày hoá đơn", "mã số thuế"):
		dung("đòi %s" % x, any(x in t for t in thieu))


@ca("soát thiếu: chuyển khoản thì đòi đủ tên, số tài khoản, ngân hàng")
def _():
	thieu = dn.thieu_gi(_phieu(phuong_thuc=dn.PT_CHUYEN_KHOAN))
	for x in ("Tên chủ tài khoản", "Số tài khoản", "Ngân hàng"):
		dung("đòi %s" % x, any(x in t for t in thieu))
	la("trả tiền mặt thì không đòi gì thêm", dn.thieu_gi(_phieu()), [])


@ca("soát thiếu: tạm ứng không đòi phân loại chi tiêu")
def _():
	la("tạm ứng đủ điều kiện dù bỏ trống phân loại",
		dn.thieu_gi(_phieu(loai_nghiep_vu=dn.NV_TAM_UNG,
			khoan={"phan_loai": "Ứng lương"})), [])


# ------------------------------------------------------- ai được bấm duyệt

@ca("duyệt: đúng vai ở đúng bước mới bấm được")
def _():
	duoc, _ = dn.duoc_duyet_khong(dn.TT_CHO_DUYET, ["AP Officer"], False)
	dung("Uyên duyệt bước một", duoc)
	duoc, _ = dn.duoc_duyet_khong(dn.TT_CHO_KE_TOAN, ["AP Kiểm soát (FIN)"], False)
	dung("chị Dung hạch toán bước cuối", duoc)
	duoc, _ = dn.duoc_duyet_khong(dn.TT_CHO_GIAM_DOC, ["AP Giám đốc"], False)
	dung("giám đốc duyệt bước giữa", duoc)


@ca("duyệt: sai vai thì chặn, và nói rõ cần vai gì")
def _():
	duoc, vi_sao = dn.duoc_duyet_khong(dn.TT_CHO_KE_TOAN, ["AP Officer"], False)
	dung("Uyên không hạch toán thay kế toán được", not duoc)
	dung("và câu chặn nói rõ cần vai nào", "vai" in vi_sao)


@ca("duyệt: người lập không tự duyệt phiếu của chính mình")
def _():
	# Luat nay lay nguyen tu ho_so_tt.py vi no da dung o do. Bo di thi hai
	# cap duyet coi nhu khong con.
	duoc, vi_sao = dn.duoc_duyet_khong(dn.TT_CHO_DUYET, ["AP Officer"], True)
	dung("chặn lại", not duoc)
	dung("và nói đúng lý do", "chính mình" in vi_sao)


@ca("duyệt: anh Việt thì tự duyệt được vì không còn ai trên nữa")
def _():
	duoc, _ = dn.duoc_duyet_khong(dn.TT_CHO_DUYET, ["System Manager"], True)
	dung("System Manager tự duyệt được", duoc)


@ca("duyệt: phiếu đã hoàn tất hoặc bị trả lại thì không có gì để bấm")
def _():
	for tt in (dn.TT_HOAN_TAT, dn.TT_TRA_LAI, dn.TT_NHAP):
		duoc, _ = dn.duoc_duyet_khong(tt, ["System Manager"], False)
		dung("trạng thái %s không duyệt được" % tt, not duoc)


# ------------------------------------------- đổ sang Hồ sơ thanh toán loại nào

@ca("hồ sơ: trả thẳng cho nhà cung cấp thì là loại NCC")
def _():
	la("có hoá đơn", dn.loai_ho_so_tt(dn.HT_NCC, dn.CT_CO_VAT), "NCC")
	la("không hoá đơn", dn.loai_ho_so_tt(dn.HT_NCC, dn.CT_KHONG_VAT), "NCC")


@ca("hồ sơ: hoàn tiền nhân viên tách theo có hoá đơn hay không")
def _():
	# Dung ba loai co san cua ho_so_tt.py, khong de ra loai thu tu.
	la("có hoá đơn thì hoàn ứng HĐ",
		dn.loai_ho_so_tt(dn.HT_NHAN_VIEN, dn.CT_CO_VAT), "Hoan ung HD")
	la("không hoá đơn thì hoàn ứng",
		dn.loai_ho_so_tt(dn.HT_NHAN_VIEN, dn.CT_KHONG_VAT), "Hoan ung")


@ca("hồ sơ: mọi trạng thái đều có nhãn tiếng Việt cho người đọc")
def _():
	for tt in (dn.TT_NHAP, dn.TT_CHO_DUYET, dn.TT_CHO_GIAM_DOC,
			dn.TT_CHO_KE_TOAN, dn.TT_HOAN_TAT, dn.TT_TRA_LAI):
		dung("trạng thái %s có nhãn" % tt, len(dn.NHAN_TRANG_THAI.get(tt) or "") > 3)


# ================================= bảng kê nhiều dòng (20/08/2026)
#
# Anh Việt 19/08/2026: *"Hiện tại hệ thống đang là 1 phiếu = 1 khoản chi. Việc
# này quá mất thời gian. Em hãy cấu trúc lại theo dạng Master-Detail."*


@ca("bảng kê: tổng tiền là tổng các dòng, không phải số ai đó gõ vào")
def _():
	p = _phieu(cac_khoan=[_khoan(so_tien=30000), _khoan(so_tien=12500),
		_khoan(so_tien=7500)])
	la("cộng đủ ba dòng", dn.cong_bang_ke(p), 50000)
	# Số trên phiếu cha có thể là bất kỳ thứ gì; nó KHÔNG được thắng bảng kê.
	p["tong_tien"] = 999999999
	p["so_tien"] = 1
	la("bảng kê thắng mọi số ghi sẵn", dn.tien_phieu(p), 50000)


@ca("bảng kê: phiếu rỗng thì chặn, không cho gửi một phiếu không có gì")
def _():
	thieu = dn.thieu_gi(_phieu(cac_khoan=[]))
	dung("có báo bảng kê rỗng", any("chưa có khoản chi nào" in x for x in thieu))


@ca("bảng kê: phiếu một dòng cũ vẫn đọc ra đúng số tiền")
def _():
	# QT-20 cấm xoá, nên trường `so_tien` cũ vẫn nằm đó. Phiếu lập trước
	# 20/08/2026 chưa có dòng nào, tiền vẫn nằm ở trường ấy.
	la("đọc được từ trường cũ", dn.tien_phieu({"so_tien": 750000, "cac_khoan": []}), 750000)
	la("phiếu trống trơn thì bằng không", dn.tien_phieu({}), 0)


@ca("CÁI BẪY: phiếu nhiều dòng vượt ngưỡng VẪN phải qua giám đốc")
def _():
	# Đây là chỗ nguy nhất của cả lần đổi cấu trúc.
	#
	# `so_tien` trên phiếu cha nay bằng 0 với mọi phiếu mới. Chỗ nào còn đọc
	# nó sẽ thấy 0, và `buoc_ke_tiep(0)` trả về "chờ kế toán" - tức là MỌI
	# phiếu mới, dù năm mươi triệu, đi thẳng xuống kế toán và không bao giờ
	# qua tay giám đốc. Không báo lỗi gì cả, phiếu vẫn chạy trơn tru, cấp
	# duyệt biến mất trong im lặng.
	to = _phieu(cac_khoan=[_khoan(so_tien=30000000), _khoan(so_tien=20000000)])
	la("số tiền thật là năm mươi triệu", dn.tien_phieu(to), 50000000)
	la("và phiếu rơi vào bước giám đốc",
		dn.buoc_ke_tiep(dn.tien_phieu(to)), dn.TT_CHO_GIAM_DOC)
	nho = _phieu(cac_khoan=[_khoan(so_tien=50000)])
	la("phiếu nhỏ vẫn đi thẳng xuống kế toán",
		dn.buoc_ke_tiep(dn.tien_phieu(nho)), dn.TT_CHO_KE_TOAN)


@ca("hoá đơn VAT: đọc theo CỜ của danh mục chứ không so tên")
def _():
	# Đổi tên dòng danh mục thành "Hoá đơn GTGT" thì ba ô hoá đơn KHÔNG được
	# im lặng biến mất. Ca này chứng minh điều đó bằng một danh mục đặt tên
	# khác hẳn.
	dm = {"Hoá đơn GTGT bản thể mới": {"la_hoa_don_vat": 1, "bat_buoc_tep": 1}}
	p = _phieu(khoan={"loai_chung_tu": "Hoá đơn GTGT bản thể mới"})
	p["_dm_chung_tu"] = dm
	dung("vẫn nhận ra là hoá đơn VAT", dn.co_hoa_don_vat(p))
	thieu = dn.thieu_gi(p)
	for x in ("số hoá đơn", "ngày hoá đơn", "mã số thuế"):
		dung("vẫn đòi %s" % x, any(x in t for t in thieu))


@ca("hoá đơn VAT: dòng không phải hoá đơn thì không đòi gì thêm")
def _():
	la("phiếu chỉ có bảng kê không hoá đơn thì đủ điều kiện",
		dn.thieu_gi(_phieu()), [])
	dung("và không tính là có hoá đơn VAT", not dn.co_hoa_don_vat(_phieu()))


@ca("chặn tài sản cố định: soi TỪNG DÒNG chứ không soi cả phiếu")
def _():
	# Một phiếu mười dòng mà dòng thứ hai là cái máy đánh trứng thì vẫn phải
	# chặn. Soi cả phiếu thì lọt.
	p = _phieu(cac_khoan=[
		_khoan(noi_dung="Nước đá"),
		_khoan(noi_dung="Máy đánh trứng", phan_loai="Mua máy móc-tài sản cố định"),
		_khoan(noi_dung="Giấy lau"),
	])
	ly_do = dn.ly_do_chan(p)
	dung("phải chặn lại", bool(ly_do))
	dung("và nói rõ là khoản số mấy", "Khoản 2" in (ly_do or ""))


@ca("bắt buộc tệp: loại chứng từ nào đòi tệp thì thiếu tệp là chặn")
def _():
	p = _phieu(khoan={"loai_chung_tu": CT_VAT, "so_hoa_don": "123",
		"ngay_hoa_don": "2026-08-19", "mst": "0301340144", "_co_tep": 0},
		hinh_thuc=dn.HT_NCC, nha_cung_cap="NCC-001")
	thieu = dn.thieu_gi(p)
	dung("có báo thiếu tệp", any("đính kèm tệp" in x for x in thieu))
	p2 = _phieu(khoan={"loai_chung_tu": CT_VAT, "so_hoa_don": "123",
		"ngay_hoa_don": "2026-08-19", "mst": "0301340144", "_co_tep": 1},
		hinh_thuc=dn.HT_NCC, nha_cung_cap="NCC-001")
	la("có tệp rồi thì hết thiếu", dn.thieu_gi(p2), [])


@ca("cấn trừ hoàn ứng: còn nợ, hoàn đủ, và tiêu vượt")
def _():
	con, cty, _ = dn.can_tru_tam_ung(2000000, 1500000)
	la("ứng 2 triệu hoàn 1 triệu rưỡi thì còn nợ nửa triệu", con, 500000)
	la("và công ty không nợ lại gì", cty, 0)
	con, cty, _ = dn.can_tru_tam_ung(2000000, 2000000)
	la("hoàn đủ thì hết nợ", con, 0)
	# CỐ Ý không chặn: nhân viên ứng 2 triệu rồi tiêu 2 triệu 3 là chuyện
	# bình thường, và lúc đó công ty nợ lại họ 300 nghìn. Chặn ở đây là bắt
	# người ta khai gian cho khớp con số.
	con, cty, nhac = dn.can_tru_tam_ung(2000000, 2300000)
	la("tiêu vượt thì không còn nợ", con, 0)
	la("mà công ty nợ lại ba trăm nghìn", cty, 300000)
	dung("và nói rõ ra cho người đọc", "vượt" in nhac)


@ca("hoàn ứng: phải chỉ rõ hoàn cho lần tạm ứng nào")
def _():
	ly_do = dn.ly_do_chan(_phieu(loai_nghiep_vu=dn.NV_HOAN_UNG))
	dung("thiếu mã tạm ứng thì chặn", bool(ly_do))
	dung("và chỉ đúng ô cần bấm", "Thuộc mã Tạm ứng" in (ly_do or ""))
	dung("có mã rồi thì đi qua được",
		dn.ly_do_chan(_phieu(loai_nghiep_vu=dn.NV_HOAN_UNG,
			thuoc_tam_ung="DNC-2026-00001")) is None)


@ca("hoàn ứng: phiếu chi phí thường thì không được gắn mã tạm ứng")
def _():
	ly_do = dn.ly_do_chan(_phieu(thuoc_tam_ung="DNC-2026-00001"))
	dung("chặn lại", bool(ly_do))
	dung("và bảo đổi loại nghiệp vụ", "Loại nghiệp vụ" in (ly_do or ""))
