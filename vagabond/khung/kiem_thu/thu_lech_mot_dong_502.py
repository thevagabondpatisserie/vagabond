# -*- coding: utf-8 -*-
"""v502: tờ ALOIN số 1144 vào sổ thiếu đúng một đồng.

Ngày 16/09/2026 anh Việt báo hoá đơn ALOIN lại lệch một đồng. Đây là lần
thứ ba cùng một họ lỗi, nên ca kiểm này dựng lại ĐÚNG con số của tờ đó và
chốt cả hai chỗ đã để nó lọt.

SỐ LIỆU LẤY TỪ SITE THẬT, không bịa
------------------------------------
Bản gốc `MInvoice Invoice` 226324cd-eea7-4519-9050-f2358931e620:

    so_hd 1144, ky_hieu C26TAA
    tong_tien 442.800, tien_thue 32.800, tien_truoc_thue 410.000
    chi_tiet: một dòng "In ấn", sluong 260, dgia 1.576,92, thtien 410.000

Chứng từ đã dựng ra `HDM-26-09-00040`:

    một dòng qty 260, rate 1.576,92, amount 409.999
    net_total 409.999, grand_total 442.799, discount_amount 0

Từ hai bảng đó suy ra số lẻ máy đang dùng: đơn giá 2, thành tiền 0, số
lượng 3. Nếu ô thành tiền giữ 2 số lẻ thì amount đã là 409.999,20 chứ
không phải 409.999.

HAI CHỖ ĐỂ LỌT, PHẢI SỬA CẢ HAI MỚI HẾT
----------------------------------------
1. `dung_hoa_don_mua` cân tổng bằng cách nhân thẳng `qty * rate`, ra
   409.999,2. So với 410.000 thì chênh -0,8, dưới ngưỡng, nên không nắn.
   Phần hụt chỉ thành 1 đồng SAU KHI máy lưu. Đường dựng lại đã học bài
   này từ 27/08/2026 và dùng `tien_dong_may_ghi`, còn đường dựng mới thì
   chưa, nên hai đường cùng một việc mà hai cách tính.

2. Kể cả đã dùng `tien_dong_may_ghi`, chênh ra đúng -1,0 và phép nắn cũ so
   bằng `chenh < -NGUONG_KHOP` với NGUONG_KHOP = 1.0, mà -1,0 < -1,0 là
   sai, nên vẫn gọi là khớp. Ngưỡng phải HỞ.

Sửa một trong hai thì tờ 1144 vẫn sai. Ca `_moi_mot_minh_no_khong_du`
dưới đây chốt đúng điều đó, để người sau đừng gỡ bớt một nửa.
"""

from types import SimpleNamespace
from unittest.mock import patch

from vagabond import dung_lai_hddt as dl
from vagabond import minvoice_chung_tu as mc
from vagabond.khung.kiem_thu.nen import ca, dung, la

# So le may dang dung, doc nguoc tu chinh HDM-26-09-00040.
DP_GIA, DP_TIEN, DP_SL = 2, 0, 3

TO_1144 = {
	"name": "226324cd-eea7-4519-9050-f2358931e620",
	"so_hd": "1144",
	"ky_hieu": "C26TAA",
	"ngay_lap": "2026-09-15",
	"tong_tien": 442800,
	"tien_thue": 32800,
	"tien_truoc_thue": 410000,
	"mst_doi_tac": "0301234567",
	"nguoi_mua_ban": "ALOIN",
	"chi_tiet": ('[{"ten": "In \\u1ea5n", "sluong": 260, "dgia": 1576.92, '
		'"thtien": 410000, "dvtinh": "C\\u00e1i", "tsuat": 0.08, "tchat": 1}]'),
}


def _dong_goc():
	from vagabond.minvoice_chung_tu import dong_hang_hoa

	return dong_hang_hoa(dl.doc_chi_tiet(TO_1144["chi_tiet"]))


def _tong_dong_may_ghi():
	"""Tổng dòng hàng của tờ 1144 theo đúng con số máy SẼ ghi."""
	dau = mc.dau_cua_to(TO_1144["tong_tien"])
	return sum(
		mc.tien_dong_may_ghi(x["sl"], x["gia"], DP_GIA, DP_TIEN, DP_SL)
		for x in (mc.dong_tu_hoa_don(it, dau) for it in _dong_goc())
	)


# --------------------------------------------------- con so cua to 1144


@ca("v502: to 1144 dung ra dong hang 409.999 trong khi hoa don ghi 410.000")
def _so_goc():
	la("một dòng hàng", len(_dong_goc()), 1)
	x = mc.dong_tu_hoa_don(_dong_goc()[0], 1)
	la("số lượng 260", x["sl"], 260)
	la("đơn giá 1.576,92", x["gia"], 1576.92)
	la("máy sẽ ghi 409.999", _tong_dong_may_ghi(), 409999.0)
	la("nhân thô ra 409.999,2", 260 * 1576.92, 409999.2)
	la("mục tiêu trước thuế 410.000", mc.muc_tieu_truoc_thue(TO_1144), 410000.0)


@ca("v502: lech dung mot dong thi PHAI nan, khong duoc goi la khop")
def _nguong_ho():
	la("thiếu một đồng", mc.can_theo_truoc_thue(409999, 410000), ("phi", 1.0))
	la("thừa một đồng", mc.can_theo_truoc_thue(410001, 410000), ("giam", 1.0))
	# Phan le nho hon mot dong van bo qua nhu cu: dong bac khong chia nho hon.
	la("thiếu nửa đồng vẫn khớp",
		mc.can_theo_truoc_thue(409999.5, 410000), ("khop", 0))
	la("thừa nửa đồng vẫn khớp",
		mc.can_theo_truoc_thue(410000.5, 410000), ("khop", 0))
	la("đúng số là khớp", mc.can_theo_truoc_thue(410000, 410000), ("khop", 0))


@ca("v502: to 1144 duoc nan bang mot dong bu, ten goi dung la lam tron")
def _nan_ra_dung():
	viec, so_tien = mc.can_theo_truoc_thue(
		_tong_dong_may_ghi(), mc.muc_tieu_truoc_thue(TO_1144))
	la("phải thêm dòng bù", viec, "phi")
	la("đúng một đồng", so_tien, 1.0)
	la("gọi đúng tên", mc.ten_dong_bu(so_tien),
		"Chênh lệch làm tròn theo hoá đơn điện tử")
	net = _tong_dong_may_ghi() + so_tien
	la("tiền hàng về đúng 410.000", net, 410000.0)
	la("tổng tờ về đúng 442.800", net + TO_1144["tien_thue"], 442800.0)


@ca("v502: sua mot trong hai cho thi to 1144 VAN sai")
def _moi_mot_minh_no_khong_du():
	# Chi sua nguong ma van nhan tho: chenh -0,8, duoi nguong, khong nan.
	tho = 260 * 1576.92
	la("nhân thô vẫn bảo khớp",
		mc.can_theo_truoc_thue(tho, 410000), ("khop", 0))
	# Chi dung tien_dong_may_ghi ma giu nguong dong cu: -1,0 van lot.
	chenh = _tong_dong_may_ghi() - 410000
	la("chênh đúng âm một đồng", chenh, -1.0)
	dung("ngưỡng đóng cũ sẽ nuốt mất", not (chenh < -mc.NGUONG_KHOP))
	dung("ngưỡng hở mới thì bắt", abs(chenh) >= mc.NGUONG_KHOP)


# ------------------------------------------- duong dung lai, chay that


@ca("v502: du_kien_tong chay that tren to 1144 ra dung 442.800")
def _du_kien_tong_that():
	# Chay chinh `du_kien_tong`, chi gia lap DUY NHAT phep doc so le cua
	# may. Truoc ban nay ham nay tra ve 442.799.
	doc = SimpleNamespace(get=lambda *a, **k: None)
	with patch.object(dl, "_do_chinh_xac", lambda d=None, g=None: (DP_GIA, DP_TIEN, DP_SL)):
		la("tổng dự kiến", dl.du_kien_tong(doc, TO_1144), 442800.0)


@ca("v502: du_kien_tong khop tuyet doi voi tong tren hoa don dien tu")
def _khong_con_lech():
	from vagabond import mua_dich_vu as md

	doc = SimpleNamespace(get=lambda *a, **k: None)
	with patch.object(dl, "_do_chinh_xac", lambda d=None, g=None: (DP_GIA, DP_TIEN, DP_SL)):
		du_kien = dl.du_kien_tong(doc, TO_1144)
	dung("cổng chặn ghi sổ không còn gì để chặn",
		not md.lech_qua_nguong(du_kien, TO_1144["tong_tien"]))
	la("lệch đúng bằng không", du_kien - TO_1144["tong_tien"], 0.0)


# ------------------------------------------------ chot nhung thu khong chay duoc


@ca("v502: mot nguon duy nhat cho phep lam tron, khong con nhan tho")
def _mot_nguon():
	# Phep do chuoi o day chi dung de chot mot su VANG MAT, thu ma chay
	# thi khong chung minh duoc. Phan hanh vi da co sau ca o tren.
	import inspect

	than = inspect.getsource(mc.dung_hoa_don_mua)
	dung("không còn nhân thô qty * rate",
		'flt(d.get("qty")) * flt(d.get("rate"))' not in than)
	dung("dùng chung hàm làm tròn", "tien_dong_may_ghi(" in than)
	dung("neo vào mục tiêu đáng tin", "muc_tieu_truoc_thue(r)" in than)
	dung("hàng rào cuối lấy ngưỡng hở", ">= NGUONG_KHOP" in than)
	dung("vẫn còn ném lỗi khi lệch", "frappe.throw" in than)


@ca("v502: hai duong dung chung mot ham, khong ai co ban sao rieng")
def _khong_ban_sao():
	import inspect

	la("dựng lại lấy đúng hàm của dựng mới",
		dl.tien_dong_may_ghi is mc.tien_dong_may_ghi, True)
	la("mục tiêu trước thuế cũng vậy",
		dl.muc_tieu_truoc_thue is mc.muc_tieu_truoc_thue, True)
	la("tên dòng bù cũng vậy", dl.ten_dong_bu is mc.ten_dong_bu, True)
	nguon_dl = inspect.getsource(dl)
	dung("tệp dựng lại không còn định nghĩa riêng",
		"\ndef tien_dong_may_ghi(" not in nguon_dl
		and "\ndef muc_tieu_truoc_thue(" not in nguon_dl)


# ------------------------------- duong DUNG MOI, chay that qua dung_hoa_don_mua


class ToGia(SimpleNamespace):
	"""Phiếu giả, làm tròn Y HỆT ERPNext lúc lưu.

	VÌ SAO DÁM GIẢ LẬP PHÉP LÀM TRÒN: cả bản sửa này đứng trên đúng một
	mệnh đề, rằng ERPNext ghi thành tiền bằng
	`làm_tròn(làm_tròn(sl, dp_sl) * làm_tròn(giá, dp_giá), dp_tiền)`. Mệnh
	đề đó đã đối chiếu với ba tờ thật: ACC-PINV-2026-01427, HDM-2026-00398
	và HDM-26-09-00040. Nếu nó sai thì `tien_dong_may_ghi` cũng sai và cả
	hai cùng lộ. Ca này chốt phần LOGIC; phần chạy trên site thật vẫn phải
	kiểm tay sau khi deploy.
	"""

	def __getattr__(self, ten):
		return None

	def get(self, ten, mac_dinh=None):
		return getattr(self, ten, mac_dinh)

	def set(self, ten, so):
		setattr(self, ten, so)

	def append(self, ten, du):
		if getattr(self, ten, None) is None:
			setattr(self, ten, [])
		d = ToGia(**du)
		getattr(self, ten).append(d)
		return d

	def insert(self, ignore_permissions=False):
		from frappe.utils import flt

		tong = 0.0
		for d in self.items or []:
			d.amount = flt(flt(d.qty, DP_SL) * flt(d.rate, DP_GIA), DP_TIEN)
			tong += d.amount
		self.total = tong
		self.net_total = tong - flt(self.discount_amount)
		self.grand_total = self.net_total + sum(
			flt(t.tax_amount) for t in (self.taxes or []))
		self.name = "HDM-GIA-LAP"
		return self


def _chay_dung_moi(to):
	"""Chạy chính `dung_hoa_don_mua`, chỉ chặn phần chạm cơ sở dữ liệu."""
	dung_duoc = {}

	def _get_doc(du):
		t = ToGia(**du)
		t.items = [ToGia(**d) for d in du.get("items") or []]
		t.taxes = []
		dung_duoc["to"] = t
		return t

	def _get_value(dt, *a, **k):
		if dt == "Company":
			return "642 - Chi phí" if a[1] == "default_expense_account" else "TTCP"
		return "1331 - Thuế GTGT được khấu trừ"

	gia_frappe = SimpleNamespace(
		db=SimpleNamespace(get_value=_get_value),
		get_doc=_get_doc,
		throw=lambda *a, **k: (_ for _ in ()).throw(AssertionError(a[0])),
	)
	with patch.object(mc, "frappe", gia_frappe), \
			patch.object(mc, "_cty", lambda: "CTY"), \
			patch.object(mc, "_tim_ncc", lambda *a: ("ALOIN", "0301234567")), \
			patch.object(mc, "_tra_ma_hang", lambda *a: (None, None, 1)), \
			patch.object(mc, "bo_mau_thue_mat_hang", lambda d: None), \
			patch.object(mc, "do_chinh_xac_pi", lambda: (DP_GIA, DP_TIEN, DP_SL)):
		mc.dung_hoa_don_mua(to)
	return dung_duoc["to"]


@ca("v502: dung_hoa_don_mua chay that tren to 1144 ra dung 442.800")
def _dung_moi_that():
	t = _chay_dung_moi(dict(TO_1144))
	la("tổng tờ khớp hoá đơn", t.grand_total, 442800.0)
	la("tiền hàng khớp", t.net_total, 410000.0)
	la("có thêm một dòng bù", len(t.items), 2)
	la("dòng bù đúng một đồng", t.items[1].amount, 1.0)
	la("gọi đúng tên dòng bù", t.items[1].item_name,
		"Chênh lệch làm tròn theo hoá đơn điện tử")


@ca("v502: to khong khai tach tien truoc thue van dung ra dung tong")
def _khong_khai_tach():
	# Ca that HDM-26-08-00096 Nha Sen 27/08/2026: o `tien_truoc_thue` de 0
	# trong khi to co tong 3.650.000. Neo vao o do la to ve 0 dong.
	to = dict(TO_1144)
	to["tong_tien"] = 3650000
	to["tien_thue"] = 0
	to["tien_truoc_thue"] = 0
	to["chi_tiet"] = ('[{"ten": "D\\u1ecbch v\\u1ee5", "sluong": 1, '
		'"dgia": 3650000, "thtien": 3650000, "tchat": 1}]')
	t = _chay_dung_moi(to)
	la("tổng tờ vẫn đúng", t.grand_total, 3650000.0)
	la("không bị đặt giảm giá cả tờ", t.discount_amount, 0)


@ca("v502: to khong co dong hang nao van neo vao so dang tin")
def _khong_co_dong_hang():
	to = dict(TO_1144)
	to["tong_tien"] = 3650000
	to["tien_thue"] = 0
	to["tien_truoc_thue"] = 0
	to["chi_tiet"] = "[]"
	t = _chay_dung_moi(to)
	la("dòng dự phòng mang đúng số tiền", t.items[0].rate, 3650000.0)
	la("tổng tờ vẫn đúng", t.grand_total, 3650000.0)


@ca("v502: con lech mot dong thi nem loi chu khong cho vao so lang le")
def _lech_thi_nem():
	# Khi phep nan chay dung thi hang rao cuoi khong con gi de bat, nen phai
	# TAT phep nan di moi soi duoc chinh cai hang rao. Tat bang cach cho no
	# luon bao "khop" - dung con so that cua to 1144: dong hang 409.999 cong
	# thue 32.800 ra 442.799, hoa don ghi 442.800, lech dung mot dong.
	#
	# Truoc 16/09/2026 hang rao so bang `>` nen to nhu vay vao so lang le.
	loi = ""
	try:
		with patch.object(mc, "can_theo_truoc_thue", lambda *a: ("khop", 0)):
			_chay_dung_moi(dict(TO_1144))
	except AssertionError as e:
		loi = str(e)
	dung("có ném lỗi", "Không nhận" in loi)
	dung("nói rõ lệch bao nhiêu", "442,799" in loi and "442,800" in loi)


@ca("v502: to dung so thi hang rao cuoi khong chan oan")
def _dung_so_thi_khong_chan():
	t = _chay_dung_moi(dict(TO_1144))
	la("dựng ra được và đúng tổng", t.grand_total, 442800.0)
