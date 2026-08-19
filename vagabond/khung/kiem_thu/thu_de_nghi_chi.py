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


def _phieu(**k):
	"""Dựng một phiếu hợp lệ tối thiểu, rồi cho ca kiểm sửa đúng phần nó soi."""
	p = {
		"ten_khoan_chi": "Mua đá cho quầy",
		"loai_nghiep_vu": dn.NV_CHI_PHI,
		"phan_loai": "Mua đồ cúng",
		"so_tien": 150000,
		"ngay_can_tt": "2026-08-20",
		"hinh_thuc": dn.HT_NHAN_VIEN,
		"chung_tu_thue": dn.CT_KHONG_VAT,
		"phuong_thuc": dn.PT_TIEN_MAT,
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
		loai_nghiep_vu=dn.NV_TAM_UNG, phan_loai=None,
		chung_tu_thue=dn.CT_CO_VAT))
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
	ly_do = dn.ly_do_chan(_phieu(phan_loai="Mua máy móc-tài sản cố định"))
	dung("phải chặn lại", bool(ly_do))
	dung("và chỉ sang luồng mua hàng", "Đơn mua hàng" in (ly_do or ""))


@ca("chặn: các phân loại khác thì không chặn oan")
def _():
	for x in ("Mua đồ cúng", "Tiền điện", "Phí in ấn", "Vận chuyển"):
		dung("%s phải đi qua được" % x, dn.ly_do_chan(_phieu(phan_loai=x)) is None)


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
	thieu = dn.thieu_gi(_phieu(chung_tu_thue=dn.CT_CO_VAT, so_hoa_don="123",
		ngay_hoa_don="2026-08-19", mst="0301340144"))
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
	thieu = dn.thieu_gi({"loai_nghiep_vu": dn.NV_CHI_PHI})
	dung("báo từ bốn thứ trở lên trong một lần", len(thieu) >= 4)
	for x in ("Tên khoản chi", "Ngày cần thanh toán", "Phân loại chi tiêu"):
		dung("có nhắc %s" % x, any(x in t for t in thieu))


@ca("soát thiếu: số tiền phải lớn hơn không")
def _():
	dung("số không thì chặn",
		any("lớn hơn 0" in x for x in dn.thieu_gi(_phieu(so_tien=0))))
	dung("số âm cũng chặn",
		any("lớn hơn 0" in x for x in dn.thieu_gi(_phieu(so_tien=-5000))))


@ca("soát thiếu: có hoá đơn VAT thì đòi đủ số, ngày và mã số thuế")
def _():
	thieu = dn.thieu_gi(_phieu(chung_tu_thue=dn.CT_CO_VAT, nha_cung_cap="NCC-001"))
	for x in ("Số hoá đơn", "Ngày hoá đơn", "Mã số thuế"):
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
		dn.thieu_gi(_phieu(loai_nghiep_vu=dn.NV_TAM_UNG, phan_loai=None)), [])


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
