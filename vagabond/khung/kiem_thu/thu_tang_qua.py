# -*- coding: utf-8 -*-
"""Kiem thu luong Tang qua khach VIP (v304).

Mau loi chuc va cau chan gui tin deu chep NGUYEN VAN tu bang tinh cua chi
Loan Anh, khong bia.

Ba thu duoc chot cung o day, moi thu la mot lan suyt hong:
  1. Xung ho ba nac. Thieu nac nao la thiep in ra goi khach sai vai ve.
  2. Bien thieu du lieu thi bo CA DONG. Thay bang rong thi in ra "Gui toi ."
  3. Cong gui tin ZNS. Nam cua, du ca nam moi cho gui.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.tang_qua import (
	BIEN_MAU, bien_con_thieu, cau_chan_zns, duoc_gui_zns, rap_loi_chuc,
	xung_ho_cua,
)

# Chep nguyen van tu o merge trong sheet Tet Binh Ngo 2026.
MAU_TET = """CUNG CHÚC TÂN XUÂN

Mến gửi {xung_ho} {ten_khach},

Chút phong vị ngọt lành cho ngày khởi xuân Bính Ngọ {nam}.
Cầu chúc {xung_ho} cùng gia đình một năm mới An Nhiên - Tự Tại - Cát Tường.
Mong những khoảnh khắc sum vầy thêm phần thi vị!

Tâm ý,
The Vagabond Patisserie"""


@ca("tang qua: xung ho ba nac theo dung ghi chu cua Loan Anh")
def _xung_ho():
	# Ghi chu nguyen van trong bang tinh: nhom nghe sy thay Anh/Chi bang
	# Nghe sy, nhom hoa hau thay bang Hoa Hau, cac nhom khac tuy title.
	la("title riêng thắng nhóm", xung_ho_cua("Đạo diễn", "Nghệ sỹ"), "Đạo diễn")
	la("không có title thì lấy theo nhóm", xung_ho_cua("", "Hoa Hậu"), "Hoa Hậu")
	la("không có cả hai thì rơi về Anh/Chị", xung_ho_cua("", ""), "Anh/Chị")
	la("khoảng trắng không tính là có", xung_ho_cua("   ", "  "), "Anh/Chị")
	la("None không làm nổ", xung_ho_cua(None, None), "Anh/Chị")


@ca("tang qua: rap mau Tet Binh Ngo ra cau that")
def _rap_tet():
	ra = rap_loi_chuc(MAU_TET, xung_ho="Nghệ sỹ",
		ten_khach="Nguyễn Văn Chung", nam="2026")
	dung("có xưng hô đúng nhóm", "Mến gửi Nghệ sỹ Nguyễn Văn Chung," in ra)
	dung("thay được cả biến lặp lại", "Cầu chúc Nghệ sỹ cùng gia đình" in ra)
	dung("thay được năm", "khởi xuân Bính Ngọ 2026" in ra)
	dung("không còn dấu ngoặc nhọn nào sót", "{" not in ra and "}" not in ra)


@ca("tang qua: bien thieu du lieu thi bo CA DONG, khong de cho trong")
def _bo_ca_dong():
	# Qua nua so dong trong bang tinh bo trong o Don vi. Thay bang chuoi
	# rong thi in ra "Gui toi ." tren thiep gui khach VIP.
	mau = "Kính gửi {ten_khach},\nGửi tới {don_vi}.\nTrân trọng."
	co = rap_loi_chuc(mau, ten_khach="Chị Thảo", don_vi="ELLE Tạp Chí")
	dung("có đơn vị thì giữ dòng", "Gửi tới ELLE Tạp Chí." in co)

	khong = rap_loi_chuc(mau, ten_khach="Chị Thảo", don_vi="")
	dung("thiếu đơn vị thì bỏ hẳn dòng", "Gửi tới" not in khong)
	dung("không để lại dấu chấm cụt", "Gửi tới ." not in khong)
	dung("các dòng khác vẫn còn", "Kính gửi Chị Thảo," in khong)
	dung("vẫn còn dòng cuối", "Trân trọng." in khong)


@ca("tang qua: mau rong hoac None thi tra rong, khong no")
def _mau_rong():
	for x in ("", "   ", None):
		la("mẫu %r" % x, rap_loi_chuc(x, ten_khach="A"), "")


@ca("tang qua: chan bien la ngay luc soan mau")
def _bien_la():
	# Nguoi soan go {ten} thay vi {ten_khach} thi ca dot qua in ra thiep
	# con nguyen dau ngoac nhon, ma thiep thi da gui khach roi.
	la("mẫu đúng thì không báo gì", bien_con_thieu(MAU_TET), [])
	la("bắt được biến lạ", bien_con_thieu("Kính gửi {ten},"), ["ten"])
	la("bắt được nhiều biến lạ",
		bien_con_thieu("{ho_ten} ơi, {loi_chuc} nhé"), ["ho_ten", "loi_chuc"])
	la("bốn biến hợp lệ vẫn là bốn",
		sorted(BIEN_MAU), ["don_vi", "nam", "ten_khach", "xung_ho"])


@ca("tang qua: cong gui tin ZNS, du nam cua moi cho gui")
def _cong_zns():
	sach = {"sdt_khach": "0908255045", "sdt_khach_loai": "di_dong",
		"chinh_chu": 1, "huy": 0, "zns_da_gui": None}

	# Cua 0: co bat. Anh Viet chot 25/08/2026 TAT cho dot dau.
	la("mặc định tắt thì không gửi", duoc_gui_zns(sach, 0)[0], 0)
	la("bật lên thì phiếu sạch đi qua", duoc_gui_zns(sach, 1)[0], 1)

	def hong(**doi):
		x = dict(sach)
		x.update(doi)
		return duoc_gui_zns(x, 1)

	la("phiếu đã huỷ", hong(huy=1)[0], 0)
	la("chưa có số khách", hong(sdt_khach="")[0], 0)
	la("số bàn", hong(sdt_khach_loai="co_dinh")[0], 0)
	# Cua quan trong nhat: so boc ra co the hoan toan dung ma van la so cua
	# tro ly. Xem sdt_boc.py.
	la("số không chính chủ", hong(chinh_chu=0)[0], 0)
	la("đã gửi rồi thì không gửi lại",
		hong(zns_da_gui="2026-08-25 10:00:00")[0], 0)


@ca("tang qua: cau chan gui tin phai noi viec lam tiep (QT-24)")
def _cau_chan():
	for _duoc, vi_sao in (
		duoc_gui_zns({"sdt_khach": "", "huy": 0}, 1),
		duoc_gui_zns({"sdt_khach": "0908255045", "sdt_khach_loai": "co_dinh",
			"huy": 0}, 1),
		duoc_gui_zns({"sdt_khach": "0908255045", "sdt_khach_loai": "di_dong",
			"chinh_chu": 0, "huy": 0}, 1),
	):
		cau = cau_chan_zns(vi_sao)
		dung("câu nói rõ chưa gửi được: %s" % vi_sao, cau.startswith("Chưa gửi tin được"))
		dung("câu bảo việc phải làm: %s" % vi_sao, "Nhờ anh chị" in cau)
	la("không có lý do thì không có câu", cau_chan_zns(""), "")


@ca("tang qua: hai truc trang thai KHONG rang buoc nhau")
def _hai_truc():
	# Du lieu that: dong "Nam Le" co Da lien he dong thoi Da tang; dong
	# "Anh Quan" co Da lien he, ghi chu hen lai sau Tet, chua tang. Neu co
	# ai them luat "phai lien he xong moi duoc tang" thi hai dong nay het
	# nhap duoc.
	from vagabond.tang_qua import TT_LIEN_HE, TT_TANG

	la("trục tặng đúng ba giá trị anh Việt chốt",
		list(TT_TANG), ["Chua tang", "Dang xu ly", "Da tang"])
	la("trục liên hệ đúng hai giá trị",
		list(TT_LIEN_HE), ["Chua lien he", "Da lien he"])
