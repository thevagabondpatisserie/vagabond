# -*- coding: utf-8 -*-
"""Kiem thu: phuong thuc thanh toan "Hang tang" va luong giam doc duyet.

Anh Viet dat bai 31/08/2026. Bo ca kiem nay chot NAM quyet dinh, ca nam deu
la loai doc lai se thay "ky ky" va co nguoi sua nguoc lai:

  1. Hook `validate` KHONG chan khi thieu ly do. Chan o do thi khong bao gio
     chon duoc phuong thuc nay, vi chinh cu bam chon la cu luu. Chan nam o
     `duyet()` va `truoc_khi_ghi_so`.
  2. DAU VAN DON. Duyet xong ma sua ruot don thi don tu roi ve Cho duyet.
     Khong co dieu nay thi xin duyet mot cai banh mi roi sua thanh banh kem.
  3. Hang tang la nhom tien thu TU, khong phai cong no. Cong no la tien SE
     ve; hang tang la tien KHONG BAO GIO ve.
  4. Ba chuoi "Hang tang", "Da duyet", "Tu choi" bi CHEP sang
     `ghi_so_dieu_kien.py` vi tep do khong duoc import gi ca. Ca kiem duoi
     day canh ban sao do.
  5. Chuoi cuoi ngay BO QUA don tang chua duyet thay vi de hook nem loi.
     Khong bo qua thi dem nao danh sach loi cung dai bang so don dang cho.

Ca ghi so o day cham GL Entry (but toan gat cong no), nen bo kiem tang
khung nay KHONG DU. Phai thu tren site that sau deploy.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import ghi_so_dieu_kien
from vagabond.hang_tang import (
	CHO_NGAY, LOAI_TANG, NHAN_LOAI, PT_TANG, THIEU,
	TT_CHO, TT_DUYET, TT_TU_CHOI,
	can_duyet_lai, cho_bao_lau, dau_van, dieu_kien_tim, la_don_tang,
	ly_do_chua_ghi_so, thieu_gi, trang_thai_moi,
)

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


def _don(**o):
	d = {"vgb_pt_thanh_toan": PT_TANG}
	d.update(o)
	return d


@ca("hàng tặng: nhận đúng đơn đi đường tặng")
def _():
	dung("đơn trả bằng Hàng tặng", la_don_tang(_don()))
	dung("có khoảng trắng thừa vẫn nhận",
		la_don_tang({"vgb_pt_thanh_toan": " Hàng tặng "}))
	dung("đơn tiền mặt không phải", not la_don_tang({"vgb_pt_thanh_toan": "Tiền mặt"}))
	dung("đơn chưa chọn phương thức không phải", not la_don_tang({}))


@ca("hàng tặng: bắt khai loại tặng và lý do tặng")
def _():
	la("đơn trống thiếu cả hai", thieu_gi(_don()), ["ly_do", "loai"])
	la("lý do quá ngắn vẫn là thiếu",
		thieu_gi(_don(vgb_tang_ly_do="ok", vgb_tang_loai="vip")), ["ly_do"])
	la("loại tặng bịa ra là thiếu",
		thieu_gi(_don(vgb_tang_ly_do="Tặng chị Lan đền bù bánh hỏng",
			vgb_tang_loai="bia_ra")), ["loai"])
	la("khai đủ thì không thiếu gì",
		thieu_gi(_don(vgb_tang_ly_do="Tặng chị Lan đền bù bánh hỏng",
			vgb_tang_loai="den_bu")), [])
	# Cau bao phai noi RO PHAI LAM GI, khong phai chi bao la sai.
	for m in ("ly_do", "loai"):
		dung("câu báo thiếu %s đủ dài để hiểu" % m, len(THIEU[m]) > 40)


@ca("hàng tặng: mọi loại tặng đều có nhãn tiếng Việt")
def _():
	la("số loại tặng", len(LOAI_TANG), len(NHAN_LOAI))
	for k, t in LOAI_TANG:
		dung("khoá %s không dấu" % k, k == k.lower() and " " not in k)
		dung("nhãn của %s có nội dung" % k, len(t) > 3)


@ca("hàng tặng: dấu vân đơn đổi khi ruột đơn đổi, không đổi khi chỉ đảo dòng")
def _():
	a = dau_van(100000, [{"ma": "B1", "so_luong": 1}, {"ma": "B2", "so_luong": 2}])
	b = dau_van(100000, [{"ma": "B2", "so_luong": 2}, {"ma": "B1", "so_luong": 1}])
	la("đảo thứ tự hai dòng thì dấu vẫn y nguyên", a, b)
	dung("đổi số lượng là đổi dấu",
		a != dau_van(100000, [{"ma": "B1", "so_luong": 3}, {"ma": "B2", "so_luong": 2}]))
	dung("đổi mã món là đổi dấu",
		a != dau_van(100000, [{"ma": "B9", "so_luong": 1}, {"ma": "B2", "so_luong": 2}]))
	dung("đổi tổng tiền là đổi dấu",
		a != dau_van(850000, [{"ma": "B1", "so_luong": 1}, {"ma": "B2", "so_luong": 2}]))
	dung("thêm một dòng là đổi dấu",
		a != dau_van(100000, [{"ma": "B1", "so_luong": 1}, {"ma": "B2", "so_luong": 2},
			{"ma": "B3", "so_luong": 1}]))
	dung("dòng không có mã thì bỏ qua, không làm hỏng dấu",
		a == dau_van(100000, [{"ma": "B1", "so_luong": 1}, {"ma": "", "so_luong": 9},
			{"ma": "B2", "so_luong": 2}]))
	dung("số lượng hỏng không làm vỡ hàm",
		isinstance(dau_van(1, [{"ma": "B1", "so_luong": "x"}]), str))


@ca("hàng tặng: sửa ruột sau khi duyệt thì phải xin duyệt lại")
def _():
	a = dau_van(100000, [{"ma": "B1", "so_luong": 1}])
	b = dau_van(850000, [{"ma": "B9", "so_luong": 1}])
	dung("chưa có dấu cũ thì không bắt duyệt lại", not can_duyet_lai("", b))
	dung("dấu y nguyên thì không bắt duyệt lại", not can_duyet_lai(a, a))
	dung("dấu lệch thì bắt duyệt lại", can_duyet_lai(a, b))


@ca("hàng tặng: trạng thái duyệt do một chỗ duy nhất quyết định")
def _():
	a = dau_van(100000, [{"ma": "B1", "so_luong": 1}])
	b = dau_van(850000, [{"ma": "B9", "so_luong": 1}])
	la("đơn mới rơi vào Chờ duyệt", trang_thai_moi("", [], "", a), TT_CHO)
	la("trạng thái lạ cũng về Chờ duyệt", trang_thai_moi("Linh tinh", [], "", a), TT_CHO)
	la("đã duyệt mà không đụng gì thì giữ nguyên",
		trang_thai_moi(TT_DUYET, [], a, a), TT_DUYET)
	la("đã duyệt mà sửa ruột thì về Chờ duyệt",
		trang_thai_moi(TT_DUYET, [], a, b), TT_CHO)
	la("đã duyệt mà lý do bị xoá thì về Chờ duyệt",
		trang_thai_moi(TT_DUYET, ["ly_do"], a, a), TT_CHO)
	# Tu choi PHAI dinh nguyen do, khong duoc tu troi ve Cho duyet: troi ve
	# la don bi tu choi lai lang le nam cho duyet nhu chua co chuyen gi.
	la("từ chối thì đứng nguyên", trang_thai_moi(TT_TU_CHOI, [], "", a), TT_TU_CHOI)


@ca("hàng tặng: chưa duyệt thì chưa ghi sổ được")
def _():
	la("đơn tặng mới lập", ly_do_chua_ghi_so(_don()), "tang_cho_duyet")
	la("đơn tặng chờ duyệt",
		ly_do_chua_ghi_so(_don(vgb_tang_duyet=TT_CHO)), "tang_cho_duyet")
	la("đơn tặng bị từ chối",
		ly_do_chua_ghi_so(_don(vgb_tang_duyet=TT_TU_CHOI)), "tang_tu_choi")
	la("đơn tặng đã duyệt thì thông",
		ly_do_chua_ghi_so(_don(vgb_tang_duyet=TT_DUYET)), "")
	la("đơn không phải hàng tặng thì không dính luật này",
		ly_do_chua_ghi_so({"vgb_pt_thanh_toan": "Tiền mặt"}), "")


@ca("hàng tặng: đếm ngày chờ duyệt")
def _():
	la("chờ hai ngày là quá hạn",
		cho_bao_lau(TT_CHO, "2026-08-29", "2026-08-31"), (2, True))
	la("mới lập trong ngày thì chưa kêu",
		cho_bao_lau(TT_CHO, "2026-08-31", "2026-08-31"), (0, False))
	la("đã duyệt rồi thì không tính",
		cho_bao_lau(TT_DUYET, "2026-08-01", "2026-08-31"), (0, False))
	la("ngày hỏng thì im, không dựng cảnh báo đỏ",
		cho_bao_lau(TT_CHO, "khong-phai-ngay", "2026-08-31"), (0, False))
	la("ngày ở tương lai cũng im",
		cho_bao_lau(TT_CHO, "2026-09-05", "2026-08-31"), (0, False))
	dung("ngưỡng mặc định là một ngày", CHO_NGAY == 1)


@ca("hàng tặng: ô tìm chạy ở máy chủ, không lọc bằng Python")
def _():
	la("ô tìm trống thì không thêm điều kiện", dieu_kien_tim("", ("name",)), None)
	la("chỉ có khoảng trắng cũng vậy", dieu_kien_tim("   ", ("name",)), None)
	la("có chữ thì dựng điều kiện like cho từng cột",
		dieu_kien_tim("Lan", ("name", "customer_name")),
		[["name", "like", "%Lan%"], ["customer_name", "like", "%Lan%"]])


@ca("hàng tặng: bản sao chuỗi bên ghi_so_dieu_kien không được lệch")
def _():
	# `ghi_so_dieu_kien.py` co y KHONG import gi ca de chay duoc tren may CI
	# tay khong, nen ba chuoi duoi day la ban sao. Ca kiem nay la thu duy
	# nhat giu hai ben khop nhau.
	la("tên phương thức", ghi_so_dieu_kien.HANG_TANG, PT_TANG)
	la("trạng thái đã duyệt", ghi_so_dieu_kien.TANG_DA_DUYET, TT_DUYET)
	la("trạng thái từ chối", ghi_so_dieu_kien.TANG_TU_CHOI, TT_TU_CHOI)
	dung("tệp ghi_so_dieu_kien vẫn không import gì",
		"\nimport " not in _doc("vagabond", "ghi_so_dieu_kien.py")
		and "\nfrom " not in _doc("vagabond", "ghi_so_dieu_kien.py"))


@ca("hàng tặng: phép chung ghi_so_dieu_kien nói đúng về đơn tặng")
def _():
	nen = {"docstatus": 0, "vgb_huy": 0, "vgb_tam_tinh": 0,
		"vgb_pt_thanh_toan": PT_TANG}
	la("chưa duyệt", ghi_so_dieu_kien.ly_do(dict(nen)), "tang_cho_duyet")
	la("bị từ chối",
		ghi_so_dieu_kien.ly_do(dict(nen, vgb_tang_duyet=TT_TU_CHOI)), "tang_tu_choi")
	# Day la ca quan trong nhat: da duyet thi THONG, khong doi ma tham chieu
	# va khong doi tien ve. Hang tang khong co dong nao ve nen khong co gi de
	# doi soat - anh Viet: "may se cho ghi so ma khong can doi soat".
	la("đã duyệt thì thông, không đòi mã tham chiếu",
		ghi_so_dieu_kien.ly_do(dict(nen, vgb_tang_duyet=TT_DUYET),
			pt_can_ma={"Thẻ - Payoo"}), "")
	la("đã duyệt thì thông, không đòi tiền về",
		ghi_so_dieu_kien.ly_do(dict(nen, vgb_tang_duyet=TT_DUYET, sepay_du=0), ), "")
	# Thu tu bao ly do phai bam theo cua chan that: thieu phuong thuc thi noi
	# thieu phuong thuc truoc da.
	la("chưa chọn phương thức vẫn nói thiếu phương thức trước",
		ghi_so_dieu_kien.ly_do({"docstatus": 0, "vgb_pt_thanh_toan": ""}), "chua_pt")
	for m in ("tang_cho_duyet", "tang_tu_choi"):
		dung("mã %s có câu tiếng Việt" % m, len(ghi_so_dieu_kien.chu(m)) > 15)
		dung("mã %s nằm trong thứ tự ưu tiên" % m, m in ghi_so_dieu_kien.THU_TU)


@ca("hàng tặng: khai đúng trong danh sách phương thức thanh toán")
def _():
	s = _doc("vagabond", "pt_thanh_toan.py")
	dung("có nhóm tiền thứ tư, không thu tiền", 'TIEN_KHONG_THU = "khong_thu"' in s)
	dung("có phương thức Hàng tặng trong danh sách gốc", '"ten": "Hàng tặng"' in s)
	dung("Hàng tặng xếp vào nhóm không thu tiền",
		'"quay": 1, "online": 1, "tien_ve": TIEN_KHONG_THU' in s)
	dung("tên Hàng tặng bị khoá, không cho đổi hay bỏ",
		'"Hàng tặng": "luồng duyệt đơn tặng' in s)
	dung("có hàm khong_thu để màn Chốt ca tách nhóm", "def khong_thu():" in s)
	# Bat buoc nhap ma tham chieu thi luong tang tac ngay: khong co ma nao de
	# nhap. Neu ai do bat co `bat` len thi ca kiem nay do.
	i = s.find('"ten": "Hàng tặng"')
	khoi = s[i:i + 400]
	dung("Hàng tặng không bắt buộc mã tham chiếu", '"bat": 1' not in khoi)
	dung("Hàng tặng không gửi mã hình thức riêng sang cơ quan thuế",
		'"minvoice": ""' in khoi)
	# Site that da luu cau hinh tu lau, nen them mot dong vao MAC_DINH khong
	# du. Xem `bo_sung_mac_dinh`.
	dung("có đường nhét phương thức mới vào cấu hình đã lưu",
		"def bo_sung_mac_dinh():" in s)
	t = _doc("vagabond", "truong_tu_them.py")
	dung("after_migrate có gọi đường đó", "pt_thanh_toan.bo_sung_mac_dinh()" in t)
	dung("after_migrate có dựng trường mới của hàng tặng",
		"hang_tang.TRUONG_MOI" in t)


@ca("hàng tặng: bốn hook đều được khai, không thiếu cái nào")
def _():
	s = _doc("vagabond", "hooks.py")
	for ten, cho in (
		("truoc_khi_luu", "validate"),
		("truoc_khi_ghi_so", "before_submit"),
		("sau_khi_ghi_so", "on_submit"),
		("khi_huy", "on_cancel"),
	):
		dung("hook %s được khai" % ten, "vagabond.hang_tang.%s" % ten in s)
	# Cua chan THAT phai o before_submit. Chi khai o validate thi don van ghi
	# so duoc bang duong khac (chuoi cuoi ngay, Desk, mot ham noi bo nao do).
	i = s.find('"before_submit": [\n\t\t\t"vagabond.mua_vu.chan_ban_lo"')
	dung("cửa chặn nằm đúng ở before_submit",
		i > 0 and "vagabond.hang_tang.truoc_khi_ghi_so" in s[i:i + 400])


@ca("hàng tặng: cửa chặn ghi sổ đọc đúng trạng thái đã duyệt")
def _():
	s = _doc("vagabond", "hang_tang.py")
	i = s.find("def truoc_khi_ghi_so(")
	j = s.find("\ndef ", i + 10)
	than = s[i:j]
	dung("có chặn khi trạng thái khác Đã duyệt", "if tt != TT_DUYET:" in than)
	dung("có chặn riêng cho đơn đã bị từ chối", "if tt == TT_TU_CHOI:" in than)
	dung("có kiểm dấu vân trước khi cho ghi sổ", "can_duyet_lai(" in than)
	dung("có kiểm tài khoản chi phí biếu tặng trước khi vào sổ",
		"_tk_chi_phi()" in than)
	dung("có nối ghi chú vào từng dòng hàng", "them_ghi_chu(" in than)
	# Hook validate KHONG duoc chan: chan o do la khong bao gio chon duoc
	# phuong thuc nay. Xem ghi chu dai trong ham.
	i = s.find("def truoc_khi_luu(")
	j = s.find("\ndef ", i + 10)
	dung("hook lưu không ném lỗi khi thiếu thông tin",
		"frappe.throw" not in s[i:j])


@ca("hàng tặng: chỉ giám đốc mới duyệt, và từ chối thì phải nêu lý do")
def _():
	s = _doc("vagabond", "hang_tang.py")
	dung("vai duyệt gồm Giám đốc", "VAI_DUYET = {\"System Manager\", ROLE_GIAM_DOC" in s)
	for ham in ("def duyet(", "def tu_choi("):
		i = s.find(ham)
		j = s.find("\n@frappe.whitelist", i + 10)
		than = s[i:j if j > 0 else len(s)]
		dung("%s có chặn quyền" % ham.strip(), "_chan_neu_khong_duyet()" in than)
	i = s.find("def tu_choi(")
	dung("từ chối bắt buộc nêu lý do", "len(ly) < 5" in s[i:i + 900])
	i = s.find("def duyet(")
	dung("không duyệt được tờ còn thiếu thông tin", "thieu_gi(si)" in s[i:i + 900])
	dung("duyệt xong ghi lại dấu vân đơn",
		'"vgb_tang_dau_van": _dau_van_cua_to(si)' in s)


@ca("hàng tặng: danh sách màn duyệt đọc ở máy chủ, không cắt dòng trước khi lọc")
def _():
	s = _doc("vagabond", "hang_tang.py")
	i = s.find("def ds_don(")
	j = s.find("\n@frappe.whitelist", i + 10)
	than = s[i:j]
	dung("lọc bằng or_filters ở tầng cơ sở dữ liệu", "or_filters=hoac" in than)
	dung("đọc hết rồi mới cắt, không cắt trước", "limit_page_length=0" in than)
	dung("cắt dòng ở bước cuối", "ra[:tran]" in than)
	dung("đếm ba họ chip", "dem_diem" in than and "dem_loai" in than and "dem_tt" in than)


@ca("hàng tặng: chuỗi cuối ngày bỏ qua đơn chưa duyệt thay vì nổ lỗi")
def _():
	s = _doc("vagabond", "ban_hang.py")
	i = s.find("def tu_ghi_so_cuoi_ngay(")
	j = s.find("\ndef ", i + 10)
	than = s[i:j]
	dung("có nhánh bỏ qua đơn tặng chưa duyệt",
		'"tang_cho_duyet", "tang_tu_choi"' in than)
	# Man tinh tien phai doc duoc o trang thai duyet, khong thi chip "Khong
	# ghi so duoc" im lang bo qua ca nhom don tang.
	i = s.find("def pos_ds_bill(")
	j = s.find("\ndef ", i + 10)
	dung("danh sách bill đọc trạng thái duyệt", '"vgb_tang_duyet"' in s[i:j])
	# Chot ca phai tach nhom khong thu tien khoi nhom cho ve.
	dung("chốt ca tách nhóm không thu tiền",
		"pt_thanh_toan.khong_thu()" in s and '"khong_thu": khong_thu,' in s)


@ca("hàng tặng: màn duyệt được nối vào phân hệ Kế toán và có đường riêng")
def _():
	d = _doc("vagabond", "duong_app.py")
	dung("có màn trong bảng đường", '("DUYETTANG", "Duyệt đơn hàng tặng"' in d)
	t = _doc("vagabond", "public", "js", "bep", "02-trang-chu.js")
	dung("bảng đường bên JavaScript đã sinh lại",
		"'duyet-don-hang-tang': 'DUYETTANG'" in t)
	dung("vgbGo có nhánh cho khoá mới", "if (k === 'DUYETTANG')" in t)
	dung("khoá nằm trong nhóm Kế toán",
		"'BT', 'DUYETTANG'" in t or "'DUYETTANG', 'BT'" in t)
	dung("có ô trên trang chủ", "card('🎁', 'Duyệt đơn hàng tặng'" in t)
	dung("số badge lấy từ máy chủ, màn không tự đếm",
		"vagabond.hang_tang.dem_cho_duyet" in t)
	m = _doc("vagabond", "public", "js", "bep", "41-duyet-don-tang.js")
	dung("màn duyệt có thật", len(m) > 2000)
	dung("màn duyệt nghe trên root, không nghe trên thân màn",
		"root.addEventListener('click', dtgBam)" in m)
	dung("màn duyệt gọi đúng cửa máy chủ",
		"vagabond.hang_tang.ds_don" in m and "vagabond.hang_tang.duyet" in m
		and "vagabond.hang_tang.tu_choi" in m)
	b = _doc("vagabond", "public", "js", "bep", "10-bill-quay.js")
	dung("màn bill có khối hàng tặng", "function pbKhoiTang(" in b)
	dung("khối hàng tặng bật tắt theo phương thức đang chọn",
		"PB_PT === 'Hàng tặng'" in b)
	dung("màn bill gửi được loại tặng và lý do lên máy chủ",
		"vagabond.hang_tang.luu_thong_tin" in b)
