"""Ca kiểm cho luồng thu tiền hoá đơn bán và màn công nợ phải thu.

Anh Việt chuyển phản ánh của bên Loan Anh ngày 04/09/2026, kèm ảnh chụp:
hoá đơn 92523 trị giá 43.978.500 đã chuyển khoản một nửa mà màn công nợ
vẫn đòi cả tờ; hoá đơn Ms.Amber 21.000.000 đã thu đủ mà vẫn nằm trong danh
sách khách đang nợ.

Anh chốt chín kịch bản phải kiểm: thu 100% tiền mặt, ATM, OnePay, chuyển
khoản; thu hỗn hợp; một phần đã thu phần còn lại công nợ; giao dịch bị huỷ
hoặc thất bại; bấm thanh toán hai lần hoặc webhook lặp; hoá đơn đã thanh
toán hoàn toàn không được xuất hiện trong công nợ.

Số liệu dùng trong các ca là số THẬT đo trên site ngày 04/09/2026, không
phải số bịa ra cho tròn.

Mọi ca chạy trên phép THUẦN và trên văn bản tệp: không cần Frappe, không
cần site, không cần mạng, không cần thư viện requests.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.thu_tien import (
	con_no_cua, da_thu_that, da_thu_theo_pt, khoa_chong_trung,
	khong_sinh_phieu, la_cong_no, trang_thai_thu,
)

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


TT = _doc("thu_tien.py")
CN = _doc("cong_no.py")
TTN = _doc("thanh_toan_nhieu.py")
HD = _doc("hop_dong.py")
HOOKS = _doc("hooks.py")

# Ba con so that cua to 92523 (HDB-26-09-00508).
TONG_92523 = 43978500.0
DA_CK_92523 = 21989250.0


# ------------------------------------------- Công nợ không phải phương thức


@ca("cong no la NHAN cua phan chua thu, khong phai mot duong tien vao")
def _cong_no_khong_phai_thu():
	for x in ("Công nợ", "Chưa thu", "Ghi nợ"):
		dung("%r la nhan chua thu" % x, la_cong_no(x))
	for x in ("Tiền mặt", "Chuyển khoản", "OnePay", "Thẻ - ShinhanBank", ""):
		dung("%r la duong tien vao that" % x, not la_cong_no(x))


@ca("da thu that: cong dong tien vao, BO dong cong no")
def _da_thu_bo_cong_no():
	dong = [{"pt": "Chuyển khoản", "so_tien": DA_CK_92523},
		{"pt": "Công nợ", "so_tien": DA_CK_92523}]
	la("chi cong phan da vao", da_thu_that(dong), DA_CK_92523)
	# Cong ca dong cong no vao la tu xoa so no cua minh.
	dung("khong cong ca to", da_thu_that(dong) != TONG_92523)


@ca("da thu that: bo dong am va dong khong")
def _bo_dong_am():
	# Dong am la dau hieu go nham. Cong vao la tu giam so phai doi.
	la("dong am khong duoc tru", da_thu_that([
		{"pt": "Tiền mặt", "so_tien": 1000000}, {"pt": "Tiền mặt", "so_tien": -400000}]), 1000000)
	la("dong khong thi bo", da_thu_that([{"pt": "OnePay", "so_tien": 0}]), 0)


@ca("da thu theo tung phuong thuc: gom cung ten, giu thu tu gap dau")
def _theo_pt():
	ra = da_thu_theo_pt([
		{"pt": "Chuyển khoản", "so_tien": 1000000},
		{"pt": "Tiền mặt", "so_tien": 500000},
		{"pt": "Chuyển khoản", "so_tien": 200000},
		{"pt": "Công nợ", "so_tien": 300000},
	])
	la("gom hai dong chuyen khoan lam mot", ra, [("Chuyển khoản", 1200000.0), ("Tiền mặt", 500000.0)])
	dung("khong bay dong cong no", "Công nợ" not in [p for p, _ in ra])


# --------------------------------------- Chín kịch bản anh Việt liệt kê


@ca("kich ban 1-4: thu 100 phan tram bang mot phuong thuc thi het no")
def _thu_du_mot_duong():
	for pt in ("Tiền mặt", "ATM", "OnePay", "Chuyển khoản"):
		dong = [{"pt": pt, "so_tien": TONG_92523}]
		# Da co chung tu thu tien thi du no so cai ve 0.
		la("%s: het no" % pt, con_no_cua(TONG_92523, 0, dong, pt), 0.0)
		la("%s: trang thai" % pt, trang_thai_thu(TONG_92523, 0), "Đã thanh toán")


@ca("kich ban 5: thu hon hop hai duong, cong du thi het no")
def _hon_hop():
	dong = [{"pt": "Chuyển khoản", "so_tien": 2000000},
		{"pt": "Thẻ - ShinhanBank", "so_tien": 225000}]
	la("cong du la het no", con_no_cua(2225000, 0, dong, "Chuyển khoản"), 0.0)


@ca("kich ban 6: mot phan da thu, phan con lai cong no - dung ca to 92523")
def _mot_phan():
	dong = [{"pt": "Chuyển khoản", "so_tien": DA_CK_92523},
		{"pt": "Công nợ", "so_tien": DA_CK_92523}]
	# So cai chua ghi nhan gi nen van dang la ca to.
	no = con_no_cua(TONG_92523, TONG_92523, dong, "Chuyển khoản")
	la("con no dung mot nua", no, DA_CK_92523)
	la("trang thai la thu mot phan", trang_thai_thu(TONG_92523, no), "Thu một phần")
	# Day chinh la con so Loan Anh can thay tren man cong no.
	la("khong con doi ca to", no != TONG_92523, True)


@ca("kich ban 7: giao dich huy hoac that bai thi khong duoc tru vao no")
def _giao_dich_hong():
	# Giao dich hong nghia la KHONG co dong nao duoc ghi. To van no nguyen.
	la("khong dong nao thi no ca to", con_no_cua(TONG_92523, TONG_92523, [], "Công nợ"), TONG_92523)
	# Dong ghi 0 dong cung khong tinh la da thu.
	la("dong 0 dong khong tru no",
		con_no_cua(TONG_92523, TONG_92523, [{"pt": "OnePay", "so_tien": 0}], "Công nợ"), TONG_92523)


@ca("kich ban 8: bam hai lan hay webhook lap deu dung MOT khoa")
def _chong_trung():
	a = khoa_chong_trung("HDB-26-09-00508", "ghi_so|Chuyển khoản")
	b = khoa_chong_trung("HDB-26-09-00508", "ghi_so|Chuyển khoản")
	la("hai lan bam ra cung mot khoa", a, b)
	dung("khoa mang so hoa don", "HDB-26-09-00508" in a)
	# Khac to hoac khac phuong thuc thi phai la khoan khac.
	dung("khac to la khoa khac", khoa_chong_trung("HDB-26-09-00509", "ghi_so|Chuyển khoản") != a)
	dung("khac phuong thuc la khoa khac", khoa_chong_trung("HDB-26-09-00508", "ghi_so|Tiền mặt") != a)
	la("khong dai qua o reference_no", len(khoa_chong_trung("X" * 300, "Y" * 300)) <= 140, True)
	# Phep chan nam o DU LIEU chu khong o nut bam.
	dung("do khoa tren chung tu da co", '"reference_no": khoa' in TT)


@ca("kich ban 9: to da thanh toan het KHONG duoc nam trong cong no")
def _het_no_thi_bien():
	la("so cai ve 0 la het no", con_no_cua(TONG_92523, 0, [], "Công nợ"), 0.0)
	dung("man cong no bo qua to het no", 'if r["con_no"] <= 0:' in CN)


# ------------------------------------ Cửa giữ cho 2.183 tờ cũ nằm yên


@ca("2.183 to cu da thu ma chua co chung tu KHONG duoc nhay vao cong no")
def _to_cu_nam_yen():
	# Do that 04/09/2026: 2.210 to du no 1,31 ty, chi 27 to (115 trieu) la
	# no that. Doc thang outstanding_amount la man cong no nhay len 1,31 ty
	# trong mot dem.
	la("to cu co chuyen khoan, khong dong nao",
		con_no_cua(2000000, 2000000, [], "Chuyển khoản"), 0.0)
	la("to cu tien mat", con_no_cua(500000, 500000, [], "Tiền mặt"), 0.0)
	la("to cu Grab", con_no_cua(300000, 300000, [], "GrabFood"), 0.0)
	# Con to mang co Cong no thi van la no that.
	la("to co Cong no van la no", con_no_cua(2000000, 2000000, [], "Công nợ"), 2000000.0)


@ca("so cai luon duoc ton trong: khong bao gio doi lai tien khach da tra")
def _ton_trong_so_cai():
	# Dong ghi con no 10 trieu ma so cai da ghi nhan thu gan het, thi lay
	# so cai. Phep min o `con_no_cua` chinh la cho nay.
	la("so cai thap hon thi lay so cai",
		con_no_cua(20000000, 3000000, [{"pt": "Công nợ", "so_tien": 20000000}], "Công nợ"), 3000000.0)
	la("khong bao gio ra so am", con_no_cua(1000000, -5, [], "Công nợ"), 0.0)


@ca("trang thai thanh toan noi dung mot chu")
def _trang_thai():
	la("het no", trang_thai_thu(1000000, 0), "Đã thanh toán")
	la("chua thu dong nao", trang_thai_thu(1000000, 1000000), "Chưa thu")
	la("tra mot phan", trang_thai_thu(1000000, 400000), "Thu một phần")


# ------------------------------------------------ Phiếu đòi nợ sinh chứng từ


@ca("phieu doi no thu duoc tien thi PHAI sinh chung tu thu tien")
def _phieu_sinh_chung_tu():
	# Ca Ms.Amber: phieu DNTT-26-09-00001 ghi da thu du 21.000.000 ma hoa
	# don HDB-26-08-02800 van du no 21.000.000, va quay lai danh sach no.
	dung("co ham sinh chung tu", "def ghi_thu_cho_phieu(doc" in CN)
	dung("duong SePay co goi", 'ghi_thu_cho_phieu(doc, "Chuyển khoản", "Đối chiếu SePay.")' in CN)
	dung("duong khop tay co goi", 'ghi_thu_cho_phieu(doc, "Chuyển khoản", "Kế toán khớp tay.")' in CN)
	dung("phan bo to cu truoc", 'order_by="posting_date asc"' in CN)
	# Loi sinh chung tu khong duoc lam rot viec danh dau phieu: tien da ve
	# that roi, khong the bat ke toan lam lai tu dau.
	dung("loi thi ghi nhat ky chu khong nem", "cong_no: sinh chung tu thu tien" in CN)


@ca("ghi so hoa don co bang dong thi sinh chung tu thu tien")
def _ghi_so_sinh_chung_tu():
	dung("co ham", "def sau_khi_ghi_so(doc, method=None):" in TTN)
	dung("dat o on_submit", "vagabond.thanh_toan_nhieu.sau_khi_ghi_so" in HOOKS)
	# Phai dat CUOI day on_submit: hai ham hang tang gat cong no sang chi
	# phi bieu tang, chay truoc chung la ghi thu roi bi gat di ngay sau.
	i_tang = HOOKS.find("vagabond.hang_tang.sau_khi_ghi_so")
	i_thu = HOOKS.find("vagabond.thanh_toan_nhieu.sau_khi_ghi_so")
	dung("dat sau ham hang tang", i_tang > 0 and i_thu > i_tang)
	# To mot phuong thuc di nguyen duong cu - do la cua giu 2.183 to cu.
	dung("khong co dong thi thoi", "if not dong:" in TTN)


@ca("cong no khong duoc lam phuong thuc chinh khi to da thu duoc dong nao")
def _pt_chinh_bo_cong_no():
	from vagabond.thanh_toan_nhieu import chinh_cua

	# O chinh di thang vao ma hinh thuc thanh toan gui co quan thue.
	la("lay duong tien vao lon nhat",
		chinh_cua([{"pt": "Công nợ", "so_tien": 30000000},
			{"pt": "Chuyển khoản", "so_tien": 10000000}]), "Chuyển khoản")
	# Ca to deu la cong no thi moi lay chinh no, vi luc do khong con gi khac.
	la("ca to cong no thi lay cong no",
		chinh_cua([{"pt": "Công nợ", "so_tien": 30000000}]), "Công nợ")


@ca("ma hinh thuc thanh toan gui co quan thue bo qua dong cong no")
def _ma_thue_bo_cong_no():
	from vagabond.thanh_toan_nhieu import ma_thue_cua

	bang = {"Tiền mặt": "TM", "Chuyển khoản": "CK"}
	# De dong cong no lot vao la phep tra ma tra rong, va ca to di sang co
	# quan thue khong mang ma nao.
	la("bo dong cong no roi moi tra ma",
		ma_thue_cua([{"pt": "Chuyển khoản"}, {"pt": "Công nợ"}], bang), "CK")
	la("tron tien mat voi chuyen khoan van ra TM/CK",
		ma_thue_cua([{"pt": "Tiền mặt"}, {"pt": "Chuyển khoản"}, {"pt": "Công nợ"}], bang), "TM/CK")


# ------------------------------------------------ Màn công nợ đọc đúng nguồn


@ca("man cong no doc so no that, khong cong grand_total")
def _man_cong_no():
	dung("goi phep tinh no", "tt.con_no_cua(" in CN)
	dung("cong so con no", 'o["tien"] += flt(r["con_no"])' in CN)
	dung("khong cong ca to nua", 'o["tien"] += flt(r.grand_total)' not in CN)
	# Man phai bay ca tong to va phan da tra, khong bat ai tru tay.
	dung("bay tong to", '"tong_don": flt(r.grand_total)' in CN)
	dung("bay phan da thu", '"da_thu": flt(r.grand_total) - flt(r["con_no"])' in CN)


@ca("man cong no quet ca to tra hon hop ma o chinh ghi phuong thuc khac")
def _quet_duong_thu_hai():
	# To nao phan da thu lon hon phan no thi o chinh ghi ten phuong thuc
	# kia, va ca khoan no bien mat khoi man neu chi quet theo o do.
	dung("co duong quet thu hai", "def si_co_dong_cong_no():" in TT)
	dung("man cong no dung no", "tt.si_co_dong_cong_no()" in CN)


@ca("bang liet ke to thieu chung tu chi DOC, khong sua gi - dieu 11")
def _bang_liet_ke():
	i = TT.find("def soat_thieu_chung_tu")
	than = TT[i:]
	dung("co bang liet ke", i > 0)
	dung("khong sinh chung tu trong do", "ghi_thu_tien(" not in than)
	dung("khong ghi gi", "set_value" not in than and "insert(" not in than)
	dung("chi ke toan truong xem duoc", "Accounts Manager" in than)


# ------------------------------------------ Gắn hoá đơn vào hợp đồng


@ca("gan hop dong: khong loc cung theo khach nua, chi xep uu tien")
def _khong_loc_cung_khach():
	i = HD.find("def hoa_don_chua_gan")
	than = HD[i:HD.find("\ndef ", i + 10) if HD.find("\ndef ", i + 10) > 0 else len(HD)]
	dung("co ham", i > 0)
	# Hop dong HDBH-2026-1838 mang ten cong ty Dentsu, con hoa don
	# HDB-26-09-00508 mang customer KL042003 (Ms.Linh dat hang). Loc theo
	# customer la loai thang to do ra.
	dung("khong dat customer vao bo loc", 'loc["customer"]' not in than)
	dung("co phep xep uu tien", "def _uu_tien(r):" in than)
	dung("uu tien theo ma so thue tren hoa don VAT", "vgb_xhd_mst" in than)


@ca("gan hop dong: o tim chay tren may chu, tim duoc ca ten VAT")
def _tim_tren_may_chu():
	i = HD.find("def hoa_don_chua_gan")
	than = HD[i:]
	dung("nhan tu khoa", "tu_khoa=\"\"" in HD[i:i + 200])
	for cot in ("name", "customer_name", "vgb_xhd_ten", "vgb_xhd_mst"):
		dung("tim duoc theo %s" % cot, '"%s"' % cot in than)
	# 18.711 to chua gan trong 90 ngay: cat con 60 to roi de o tim loc
	# trong 60 to do la khong bao gio tim ra.
	dung("noi ro con bao nhieu to nua", '"con_lai": con' in than)
	dung("man hinh bay so con lai", "cg.con_lai > 0" in _doc("public/js/bep/11-khach-ca-hop-dong.js"))


@ca("gan hop dong: chan gan trung va ghi vet")
def _chan_trung_ghi_vet():
	i = HD.find("def gan_hoa_don")
	than = HD[i:HD.find("def _ghi_vet_gan")]
	dung("chan to dang gan o hop dong khac", "đang gắn ở hợp đồng" in than)
	dung("bam lai cung hop dong khong phai loi", "if dang_gan == hop_dong:" in than)
	dung("co ghi vet", "def _ghi_vet_gan(" in HD)
	dung("ghi ca hai phia", '("Sales Invoice", si_name), ("Hop Dong Ban Hang", hop_dong)' in HD)
	dung("ghi ai lam", "frappe.session.user" in HD[HD.find("def _ghi_vet_gan"):])
	# Gan hop dong KHONG duoc dung vao so tien, thue hay du no cua to:
	# chi duoc ghi dung mot o `custom_hop_dong`, khong o nao khac.
	ma = [d for d in than.split("\n") if "frappe.db.set_value" in d]
	dung("co ghi that", bool(ma))
	dung("moi lenh ghi deu chi cham o custom_hop_dong",
		all('"custom_hop_dong"' in d for d in ma))
	dung("khong dung toi so tien hay thue", "grand_total" not in than and "outstanding" not in than)


@ca("quy uoc trinh bay: phan viet moi khong co dau gach dai")
def _khong_gach_dai():
	for ten, x in (("thu_tien", TT),):
		dung("%s khong em dash" % ten, "—" not in x)
		dung("%s khong en dash" % ten, "–" not in x)


@ca("tien thu KHONG duoc doan tai khoan, chua khai thi khong ghi")
def _khong_doan_tai_khoan():
	i = TT.find("def tk_tien_thu")
	than = TT[i:TT.find("def loi_chua_khai_tk")]
	dung("co phep tra rieng cho chieu thu", i > 0)
	# Do 04/09/2026: ca 18 hinh thuc thanh toan deu chua khai tai khoan.
	# Phep tra cua luong CHI co bon duong lui, duong cuoi la tai khoan ngan
	# hang mac dinh cua cong ty. Dung no cho chieu thu thi tien mat trong
	# ket cung chay vao MB Bank.
	dung("chi doc tai khoan khai rieng cho phuong thuc",
		'"Mode of Payment Account"' in than)
	dung("khong lui ve tai khoan cong ty", "default_bank_account" not in than)
	dung("khong lui ve tien mat cong ty", "default_cash_account" not in than)
	# Ten `tk_tien_chi` chi con duoc nhac trong ghi chu de nguoi doc biet vi
	# sao khong dung no; khong duoc GOI o dau trong tep nay.
	ma = [d for d in TT.split("\n") if "tk_tien_chi" in d and not d.strip().startswith("#")]
	dung("khong goi phep tra cua luong chi",
		all("tra_tien_app" in d or d.strip().startswith("Phép tra") for d in ma))
	dung("khong import phep tra cua luong chi", "import tk_tien_chi" not in TT)
	dung("chua khai thi tra rong", "return None, None" in than)


@ca("cau bao khi chua khai tai khoan noi du ba dieu")
def _cau_bao_chua_khai():
	i = TT.find("def loi_chua_khai_tk")
	than = TT[i:TT.find("@frappe.whitelist()", i)]
	dung("noi hong o dau", "chưa khai tài khoản tiền" in than)
	dung("noi phai lam gi", "thêm dòng công ty và chọn tài khoản tiền" in than)
	dung("noi to hoa don ra sao trong luc cho", "hoá đơn vẫn đúng số tiền" in than)


@ca("co bang soat hinh thuc chua khai tai khoan, chi DOC")
def _bang_soat_hinh_thuc():
	i = TT.find("def soat_hinh_thuc_chua_khai")
	than = TT[i:TT.find("def _da_ghi_roi")]
	dung("co bang", i > 0)
	dung("bo qua nhan cong no", "la_cong_no(m[\"name\"])" in than)
	dung("khong ghi gi", "set_value" not in than and "insert(" not in than)


@ca("hang tang khong sinh phieu thu, cung khong bi tinh la no")
def _hang_tang():
	"""Anh Viet duyet danh sach tai khoan 05/09/2026: chin kenh thu ho va
	cong the vao 113 Tien dang chuyen, rieng Hang tang KHONG khai tai khoan
	tien vi no khong phai tien. To da tat toan bang chi phi bieu tang, co
	duong ghi so rieng o hang_tang.py vao 64181 va 64182."""
	dung("hang tang khong sinh phieu", khong_sinh_phieu("Hàng tặng"))
	for x in ("Tiền mặt", "Chuyển khoản", "OnePay", "Công nợ", ""):
		dung("%r van di duong thuong" % x, not khong_sinh_phieu(x))
	# KHONG duoc nam trong danh sach cong no, khong thi man cong no se di
	# doi khach mot hop banh minh tang.
	dung("hang tang khong phai cong no", not la_cong_no("Hàng tặng"))
	dong = [{"pt": "Hàng tặng", "so_tien": 500000}]
	la("khong con no dong nao", con_no_cua(500000, 500000, dong, "Hàng tặng"), 0)
	# Va vong sinh phieu phai bo qua no.
	i = TT.find("def ghi_thu_tien(")
	than = TT[i:TT.find("def tom_tat(", i)]
	dung("vong sinh phieu bo qua hang tang", "if khong_sinh_phieu(pt):" in than)
