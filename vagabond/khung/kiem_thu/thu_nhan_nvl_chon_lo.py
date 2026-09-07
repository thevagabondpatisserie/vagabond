# -*- coding: utf-8 -*-
"""Nhận nguyên liệu: máy chủ chọn lô, không đổi mã hàng (06/09/2026, #206).

Vì sao có tệp này
-----------------
Màn "Nhận hàng" của phiếu điều chuyển nội bộ TỰ chọn lô ở phía trình duyệt,
gọi `get_batch_qty` không kèm cờ `for_stock_levels`. Không có cờ đó thì
ERPNext lọc bỏ mọi lô quá hạn. Đo thật trên site ngày 06/09/2026:

    Bin: NVLT00109 còn 330.000 gram ở Kho Lab - TV
    get_batch_qty cho đúng mã, đúng kho: chỉ 50.000 ở lô NVLT00109-006
    280.000 còn lại nằm ở ba lô quá hạn (120.000 + 100.000 + 60.000)

Bếp xin nhận quá 50.000 là màn hình báo "không đủ lô hàng" trong khi kho còn
330.000. Ô "Chặn xuất lô quá hạn" đang TẮT và bản vá v406 vẫn nguyên tác
dụng, nhưng nó chỉ nới phần máy chủ; màn hình chặn trước khi phiếu kịp tới.

Nay màn hình gửi dòng phiếu KHÔNG kèm lô, `lo_hang.gan_lo` chọn. Một nguồn.

Ba điều Codex chốt kèm theo, mỗi điều một nhóm ca dưới đây:
1. KHÔNG tự đổi sang mã thay thế trên luồng nhận. Kho giao mã nào ghi sổ mã
   đó, không thì người nhận cầm một thứ mà sổ ghi một thứ khác.
2. Hai dòng cùng mã cùng kho trong một phiếu phải chung MỘT túi lô, không
   thì cả hai cùng ăn một phần tồn và phiếu ghi nhiều hơn kho thật có.
3. Lô đang TẮT không được tính vào khả dụng.

CHƯA kiểm được ở đây: `insert` và `submit` thật trên Frappe, sổ kho sau ghi
sổ, và số "đã nhận" trên phiếu yêu cầu. Ba thứ đó cần site thật. Xem phần
VIỆC CHƯA LÀM trong bàn giao, em không lấy ca kiểm thuần thay cho chúng.
"""

from vagabond import lo_hang as lh
from vagabond.khung.kiem_thu.nen import ca, dung, la


# ------------------------------------------------------------ bộ dựng phiếu


class Dong(object):
	"""Dòng phiếu kho giả, đủ những gì `gan_lo` đụng tới."""

	def __init__(self, **kw):
		object.__setattr__(self, "_d", dict(kw))

	def __getattr__(self, k):
		d = object.__getattribute__(self, "_d")
		if k in d:
			return d[k]
		raise AttributeError(k)

	def get(self, k, mac_dinh=None):
		return object.__getattribute__(self, "_d").get(k, mac_dinh)

	def as_dict(self):
		return dict(object.__getattribute__(self, "_d"))


class Phieu(object):
	"""Phiếu kho giả. `set` và `append` bắt chước đúng Document của Frappe."""

	def __init__(self, purpose, dong):
		self.purpose = purpose
		self.docstatus = 0
		self.items = list(dong)

	def set(self, ten, gt):
		if ten == "items":
			self.items = list(gt)

	def append(self, ten, x):
		if ten == "items":
			self.items.append(Dong(**x))


def dong(ma, kho, qty, he_so=1, uom=None, lo=None, goi=None, **them):
	"""Một dòng bị trừ. `lo`/`goi` là lô người đã chọn tay."""
	d = {
		"item_code": ma, "s_warehouse": kho, "qty": qty,
		"conversion_factor": he_so, "uom": uom or "Gram",
		"stock_uom": "Gram", "name": "dong-%s-%s" % (ma, kho),
		"batch_no": lo, "serial_and_batch_bundle": goi,
	}
	d.update(them)
	return Dong(**d)


_CUA = ("_theo_lo", "_ton_tung_lo", "_ton_lo_qua_han", "_xep_het_han_truoc",
	"_cac_ma_thay_the", "_kho_khac_con", "_ten_hang", "_lo_trong_goi")


def chay_gan_lo(purpose, dong, ton, qua_han=None, thay_the=None, chan=0, goi=None):
	"""Chạy THẬT `lo_hang.gan_lo`, chỉ thay các cửa chạm hệ.

	`goi`: {tên gói Serial and Batch Bundle: {lô: số gốc}} thay cho bảng con
	thật của ERPNext. Trả về danh sách dòng của phiếu sau khi chạy. Ném lỗi
	thì để ném, ca kiểm bắt lấy.
	"""
	qua_han = qua_han or {}
	thay_the = thay_the or {}
	goi = goi or {}
	that = {t: getattr(lh, t) for t in _CUA}
	chan_that = lh.lo_het_han.dang_chan
	# Ban Frappe gia khong co get_cached_value. Dong thay the goi no de lay
	# don vi goc cua ma moi; thieu no thi gan_lo nem AttributeError roi tu
	# NUOT, va ca kiem thay phieu y nguyen ma khong biet vi sao.
	gcv_that = getattr(lh.frappe, "get_cached_value", None)
	try:
		lh.frappe.get_cached_value = lambda dt, ten, o=None, **k: "Gram"
		lh._theo_lo = lambda ma: 1
		lh._ton_tung_lo = lambda ma, kho, ke_ca_qua_han=False: dict(
			ton.get((ma, kho), {}))
		lh._ton_lo_qua_han = lambda ma, kho, da_tinh=None: {
			k: v for k, v in (qua_han.get((ma, kho), {}) or {}).items()
			if k not in (da_tinh or {})
		}
		# Giu dung thu tu ca kiem dua vao, de ca kiem chu dong thu tu uu tien.
		# Thu tu that theo han dung co ca rieng ben duoi, chay ham that.
		lh._xep_het_han_truoc = lambda cl: [(k, v) for k, v in (cl or {}).items()]
		lh._cac_ma_thay_the = lambda ma: list(thay_the.get(ma, []))
		lh._kho_khac_con = lambda ma, kho: []
		lh._ten_hang = lambda d, ma: ma
		lh._lo_trong_goi = lambda ten: dict(goi.get(ten, {}))
		lh.lo_het_han.dang_chan = lambda: chan
		p = Phieu(purpose, dong)
		lh.gan_lo(p)
		return [d.as_dict() for d in p.items]
	finally:
		for t, h in that.items():
			setattr(lh, t, h)
		lh.lo_het_han.dang_chan = chan_that
		if gcv_that is None:
			try:
				del lh.frappe.get_cached_value
			except Exception:
				pass
		else:
			lh.frappe.get_cached_value = gcv_that


def _gon(ra):
	return [(d.get("item_code"), d.get("batch_no"), d.get("qty")) for d in ra]


# ------------------------------------------------------------ chính sách mã


@ca("mã thay thế CHỈ cho luồng sản xuất, không cho luồng nhận nguyên liệu")
def _chinh_sach():
	la("làm bánh", lh.duoc_thay_ma("Manufacture"), True)
	la("đóng gói lại", lh.duoc_thay_ma("Repack"), True)
	la("chuyển sang xưởng", lh.duoc_thay_ma("Material Transfer for Manufacture"), True)
	la("gửi gia công", lh.duoc_thay_ma("Send to Subcontractor"), True)
	la("NHẬN nguyên liệu", lh.duoc_thay_ma("Material Transfer"), False)
	la("không ghi loại", lh.duoc_thay_ma(None), False)
	la("loại lạ", lh.duoc_thay_ma("Material Issue"), False)


@ca("luồng NHẬN thiếu hàng thì CHẶN, tuyệt đối không tự giao mã khác")
def _nhan_khong_thay_ma():
	# Kho giao ma A, may ghi so ma B, nguoi nhan cam mot thu so ghi mot thu
	# khac. Khong ai biet cho toi luc kiem ke.
	try:
		ra = chay_gan_lo(
			purpose="Material Transfer",
			dong=[dong("NVL1", "Kho A", 100)],
			ton={("NVL1", "Kho A"): {"L1": 40}, ("NVL2", "Kho A"): {"L9": 999}},
			thay_the={"NVL1": ["NVL2"]},
		)
		dung("phải chặn vì thiếu, chứ không lấy mã thay thế", False)
	except Exception as e:
		dung("nói đúng là thiếu hàng", "không đủ" in str(e))
		dung("không nhắc tới mã thay thế", "NVL2" not in str(e))


@ca("luồng SẢN XUẤT vẫn lấy mã thay thế như cũ, không nới cũng không siết")
def _san_xuat_van_thay_ma():
	ra = chay_gan_lo(
		purpose="Manufacture",
		dong=[dong("NVL1", "Kho A", 100)],
		ton={("NVL1", "Kho A"): {"L1": 40}, ("NVL2", "Kho A"): {"L9": 60}},
		thay_the={"NVL1": ["NVL2"]},
	)
	la("một dòng chính, một dòng thay", _gon(ra),
		[("NVL1", "L1", 40.0), ("NVL2", "L9", 60.0)])
	dung("dòng thay có ghi lý do",
		"Dùng thay NVL1" in (ra[1].get("description") or ""))


# ------------------------------------------------------------ một túi lô


@ca("hai dòng cùng mã cùng kho chung MỘT túi lô, không cùng ăn một phần tồn")
def _mot_tui():
	# Mot phieu yeu cau tach hai dong cho hai bep. Truoc 06/09 moi dong tu
	# hoi ton rieng, ca hai cung thay 60 va cung lay 60, phieu ghi ra 120
	# trong khi kho chi co 60.
	try:
		chay_gan_lo(
			purpose="Material Transfer",
			dong=[dong("NVL1", "Kho A", 40, name_goi="a"),
				dong("NVL1", "Kho A", 40, name_goi="b")],
			ton={("NVL1", "Kho A"): {"L1": 60}},
		)
		dung("tổng 80 vượt tồn 60 thì phải chặn", False)
	except Exception as e:
		dung("chặn ở dòng thứ hai", "không đủ" in str(e))


@ca("một túi lô: hai dòng vừa đủ tồn thì cả hai đi lọt, chia đúng phần")
def _mot_tui_du():
	ra = chay_gan_lo(
		purpose="Material Transfer",
		dong=[dong("NVL1", "Kho A", 40), dong("NVL1", "Kho A", 20)],
		ton={("NVL1", "Kho A"): {"L1": 50, "L2": 10}},
	)
	la("dòng đầu ăn hết L1, dòng sau ăn nốt", _gon(ra),
		[("NVL1", "L1", 40.0), ("NVL1", "L1", 10.0), ("NVL1", "L2", 10.0)])


@ca("rút khỏi túi thì TRỪ LUÔN, rút lần hai không thấy phần đã rút")
def _rut_tu_kho():
	muc = {"con": [("L1", 50), ("L2", 10)]}
	phan, thieu = lh.rut_tu_kho(muc, 40)
	la("lần đầu", phan, [("L1", 40.0)])
	la("không thiếu", thieu, 0.0)
	la("túi còn lại", muc["con"], [("L1", 10.0), ("L2", 10)])
	phan2, thieu2 = lh.rut_tu_kho(muc, 30)
	la("lần hai chỉ còn 20", phan2, [("L1", 10.0), ("L2", 10.0)])
	la("thiếu 10", thieu2, 10.0)
	la("túi cạn", muc["con"], [])


# ------------------------------------------------------------ lô quá hạn


@ca("bỏ chặn HSD: nhận 60.000 khi còn hạn 50.000 vẫn đi được, phần thiếu lấy lô quá hạn")
def _dung_so_that():
	# Dung dung con so do duoc tren site 06/09/2026.
	ra = chay_gan_lo(
		purpose="Material Transfer",
		dong=[dong("NVLT00109", "Kho Lab - TV", 60000)],
		ton={("NVLT00109", "Kho Lab - TV"): {"NVLT00109-006": 50000}},
		qua_han={("NVLT00109", "Kho Lab - TV"): {"NVLT00109-004": 120000}},
	)
	la("lô còn hạn trước, lô quá hạn sau", _gon(ra),
		[("NVLT00109", "NVLT00109-006", 50000.0),
		("NVLT00109", "NVLT00109-004", 10000.0)])


@ca("lô còn hạn luôn ưu tiên trước, lô quá hạn chỉ là vòng vét")
def _con_han_truoc():
	ra = chay_gan_lo(
		purpose="Material Transfer",
		dong=[dong("NVL1", "Kho A", 30)],
		ton={("NVL1", "Kho A"): {"CON-HAN": 100}},
		qua_han={("NVL1", "Kho A"): {"QUA-HAN": 100}},
	)
	la("không đụng lô quá hạn", _gon(ra), [("NVL1", "CON-HAN", 30.0)])


@ca("tích lại ô Chặn xuất lô quá hạn thì KHÔNG vét, chặn như trước")
def _bat_chot_lai():
	try:
		chay_gan_lo(
			purpose="Material Transfer",
			dong=[dong("NVL1", "Kho A", 60)],
			ton={("NVL1", "Kho A"): {"CON-HAN": 50}},
			qua_han={("NVL1", "Kho A"): {"QUA-HAN": 999}},
			chan=1,
		)
		dung("bật ô chặn thì phải chặn", False)
	except Exception as e:
		dung("báo thiếu", "không đủ" in str(e))


@ca("vòng vét chỉ đổ thêm MỘT LẦN cho mỗi cặp mã và kho")
def _vet_mot_lan():
	# Hai dong cung ma cung kho, ca hai deu phai vet. Do them lan hai la
	# cung mot lo qua han duoc dem hai lan.
	ra = chay_gan_lo(
		purpose="Material Transfer",
		dong=[dong("NVL1", "Kho A", 30), dong("NVL1", "Kho A", 30)],
		ton={("NVL1", "Kho A"): {"CON-HAN": 10}},
		qua_han={("NVL1", "Kho A"): {"QUA-HAN": 50}},
	)
	tong = sum(d.get("qty") or 0 for d in ra)
	la("tổng lấy ra đúng 60", tong, 60.0)
	lay_qh = sum(d.get("qty") or 0 for d in ra if d.get("batch_no") == "QUA-HAN")
	la("lô quá hạn chỉ góp 50", lay_qh, 50.0)


@ca("vòng vét đổ thêm lần thứ hai là đếm lô quá hạn HAI LẦN, phải chặn")
def _vet_lan_hai():
	# Ca nay sinh ra tu ket qua dot bien: go chot "vet dung mot lan" ma
	# khong ca nao do. Ly do la bo ca kiem YEU (truong hop (a) cua dieu 17),
	# khong phai vi co lop bao ve du. Con so cu chon kheo qua: dong sau da
	# duoc no du tu phan vet cua dong truoc nen khong bao gio vet lan hai.
	#
	# Day la con so bat duoc: kho co 10 con han + 50 qua han = 60, phieu
	# xin 80. Go chot thi may vet them 50 nua va ghi so ra 80.
	try:
		ra = chay_gan_lo(
			purpose="Material Transfer",
			dong=[dong("NVL1", "Kho A", 40), dong("NVL1", "Kho A", 40)],
			ton={("NVL1", "Kho A"): {"CON-HAN": 10}},
			qua_han={("NVL1", "Kho A"): {"QUA-HAN": 50}},
		)
		tong = sum(d.get("qty") or 0 for d in ra)
		dung("kho chỉ có 60 mà lấy ra %s" % tong, False)
	except Exception as e:
		dung("chặn và nói còn thiếu 20", "20" in str(e))


@ca("dòng người chọn lô TAY vẫn ăn tồn: túi chung phải trừ phần đó trước")
def _tru_phan_chon_tay():
	# Codex neu tren #219: dong chon tay khong di qua tui, nhung no van lay
	# hang cua lo do. Khong tru thi dong may chon sau lai thay du lo ay.
	# Kho co L1 = 50. Nguoi da chon tay 30 tu L1, may can them 30 nua.
	try:
		ra = chay_gan_lo(
			purpose="Material Transfer",
			dong=[dong("NVL1", "Kho A", 30, lo="L1"), dong("NVL1", "Kho A", 30)],
			ton={("NVL1", "Kho A"): {"L1": 50}},
		)
		tong = sum(d.get("qty") or 0 for d in ra)
		dung("kho có 50 mà phiếu ghi ra %s" % tong, False)
	except Exception as e:
		dung("chặn và nói còn thiếu 10", "10" in str(e))


@ca("trừ phần chọn tay: đủ tồn thì dòng máy chỉ lấy phần CÒN LẠI của lô")
def _tru_phan_chon_tay_du():
	ra = chay_gan_lo(
		purpose="Material Transfer",
		dong=[dong("NVL1", "Kho A", 30, lo="L1"), dong("NVL1", "Kho A", 30)],
		ton={("NVL1", "Kho A"): {"L1": 50, "L2": 40}},
	)
	la("dòng tay giữ nguyên, dòng máy lấy 20 L1 rồi 10 L2", _gon(ra),
		[("NVL1", "L1", 30), ("NVL1", "L1", 20.0), ("NVL1", "L2", 10.0)])


@ca("trừ phần chọn tay: lô QUÁ HẠN người đã chọn cũng bị trừ ở vòng vét")
def _tru_phan_chon_tay_qua_han():
	# Ban dau ca nay cho may can 20 trong khi QH con 10 hay 50 deu du, nen
	# go phep tru o vong vet ma ca van xanh (dot bien DB12 song sot, truong
	# hop (a) dieu 17). Nay cho may can 30: CON-HAN 10 + QH con lai 10 = 20,
	# thieu 10 thi phai chan. Khong tru la may thay QH con 50 va cho qua.
	try:
		ra = chay_gan_lo(
			purpose="Material Transfer",
			dong=[dong("NVL1", "Kho A", 40, lo="QH"), dong("NVL1", "Kho A", 30)],
			ton={("NVL1", "Kho A"): {"CON-HAN": 10}},
			qua_han={("NVL1", "Kho A"): {"QH": 50}},
		)
		tong = sum(d.get("qty") or 0 for d in ra)
		dung("kho có 60 mà phiếu ghi ra %s" % tong, False)
	except Exception as e:
		dung("chặn và nói còn thiếu 10", "10" in str(e))
	# Va khi du thi vet chi lay dung phan con lai cua QH.
	ra = chay_gan_lo(
		purpose="Material Transfer",
		dong=[dong("NVL1", "Kho A", 40, lo="QH"), dong("NVL1", "Kho A", 20)],
		ton={("NVL1", "Kho A"): {"CON-HAN": 10}},
		qua_han={("NVL1", "Kho A"): {"QH": 50}},
	)
	la("vét chỉ còn 10 của QH", _gon(ra),
		[("NVL1", "QH", 40), ("NVL1", "CON-HAN", 10.0), ("NVL1", "QH", 10.0)])


@ca("phan_da_chon_tay gom theo mã và kho, quy về số gốc, bỏ dòng không có lô")
def _gom_chon_tay():
	ds = [dong("A", "K", 2, he_so=1000, lo="L1"), dong("A", "K", 5, lo="L1"),
		dong("A", "K", 7), dong("B", "K", 1, lo="L9"), dong("A", "K2", 3, lo="L1")]
	ra = lh.phan_da_chon_tay(ds)
	la("A tại K: L1 = 2000 + 5", ra[("A", "K")], {"L1": 2005.0})
	la("B tại K", ra[("B", "K")], {"L9": 1.0})
	la("A tại K2 tách riêng", ra[("A", "K2")], {"L1": 3.0})
	la("trừ về 0 thì bỏ hẳn lô", lh.tru_da_dung({"L1": 5, "L2": 3}, {"L1": 5}), {"L2": 3})


@ca("gói Serial and Batch Bundle cũng bị trừ khỏi túi: lô A 60, gói lấy 40, máy xin 30 chỉ còn 20")
def _tru_ca_goi_bundle():
	"""Codex tái hiện trên #222 bằng giả lập. Bản trước chỉ đọc `batch_no`,
	nên dòng chọn tay bằng gói làm dòng máy chọn thấy lô A còn nguyên 60."""
	ds = [dong("NVL1", "Kho A", 40, goi="SABB-0001"), dong("NVL1", "Kho A", 30)]
	da = lh.phan_da_chon_tay(ds, lo_trong_goi=lambda ten: {"SABB-0001": {"LO-A": -40}}.get(ten))
	la("gói xuất ghi âm vẫn đọc ra 40 của LO-A", da[("NVL1", "Kho A")], {"LO-A": 40.0})
	# Khong dua ham doc goi vao thi khong doc duoc, dung nhu phan thuan cu.
	la("không có cửa đọc gói thì không đoán", lh.phan_da_chon_tay(ds), {})

	ra = chay_gan_lo(
		purpose="Material Transfer",
		dong=ds,
		ton={("NVL1", "Kho A"): {"LO-A": 60, "LO-B": 100}},
		goi={"SABB-0001": {"LO-A": -40}},
	)
	la("dòng gói giữ nguyên, dòng máy chỉ lấy 20 từ LO-A rồi sang LO-B",
		_gon(ra), [("NVL1", None, 40), ("NVL1", "LO-A", 20.0), ("NVL1", "LO-B", 10.0)])
	tong_a = sum(float(d.get("qty") or 0) for d in ra if d.get("batch_no") == "LO-A") + 40
	dung("tổng ghi trên LO-A không vượt 60", tong_a <= 60)

	# Lo A chi co 60 va khong con lo khac: dong may xin 30 phai bi CHAN, khong
	# duoc ghi 70 len mot lo 60.
	try:
		chay_gan_lo(
			purpose="Material Transfer",
			dong=[dong("NVL1", "Kho A", 40, goi="SABB-0001"), dong("NVL1", "Kho A", 30)],
			ton={("NVL1", "Kho A"): {"LO-A": 60}},
			goi={"SABB-0001": {"LO-A": -40}},
		)
	except Exception as e:
		dung("chặn và nói còn thiếu 10", "10" in str(e))
	else:
		dung("phải chặn khi lô A chỉ còn 20", False)

	# Dong co CA batch_no lan goi: tin batch_no, khong dem hai lan.
	da2 = lh.phan_da_chon_tay(
		[dong("NVL1", "Kho A", 5, lo="LO-A", goi="SABB-0001")],
		lo_trong_goi=lambda ten: {"LO-A": -40})
	la("có cả hai thì chỉ đếm batch_no", da2[("NVL1", "Kho A")], {"LO-A": 5.0})


# ------------------------------------------------------------ giữ nguyên


@ca("dòng người đã chọn lô hoặc đã có gói lô thì máy KHÔNG chọn lại")
def _giu_lo_nguoi_chon():
	ra = chay_gan_lo(
		purpose="Material Transfer",
		dong=[dong("NVL1", "Kho A", 10, lo="LO-TAY"),
			dong("NVL2", "Kho A", 10, goi="SBB-001")],
		ton={("NVL1", "Kho A"): {"L1": 999}, ("NVL2", "Kho A"): {"L2": 999}},
	)
	la("giữ nguyên hai dòng", _gon(ra),
		[("NVL1", "LO-TAY", 10), ("NVL2", None, 10)])


@ca("tách lô xong vẫn giữ phiếu yêu cầu, dòng yêu cầu và hệ số quy đổi")
def _giu_moi_noi():
	# Mat material_request_item la phieu yeu cau khong bao gio tu dong lai,
	# dung cai dong 233 phieu ton dong dang co tren he.
	ra = chay_gan_lo(
		purpose="Material Transfer",
		dong=[dong("NVL1", "Kho A", 2, he_so=1000, uom="Túi",
			material_request="MAT-MR-001", material_request_item="dong-1")],
		ton={("NVL1", "Kho A"): {"L1": 1500, "L2": 500}},
	)
	la("hai dòng theo TÚI, không phải gram",
		[(d.get("batch_no"), d.get("qty"), d.get("uom")) for d in ra],
		[("L1", 1.5, "Túi"), ("L2", 0.5, "Túi")])
	dung("dòng nào cũng giữ phiếu yêu cầu",
		all(d.get("material_request") == "MAT-MR-001" for d in ra))
	dung("dòng nào cũng giữ dòng yêu cầu",
		all(d.get("material_request_item") == "dong-1" for d in ra))
	dung("giữ hệ số quy đổi",
		all(d.get("conversion_factor") == 1000 for d in ra))


@ca("thiếu hàng thật thì vẫn chặn, câu lỗi nói đúng số còn thiếu")
def _van_chan_khi_thieu():
	try:
		chay_gan_lo(
			purpose="Material Transfer",
			dong=[dong("NVL1", "Kho A", 100)],
			ton={("NVL1", "Kho A"): {"L1": 30}},
			qua_han={("NVL1", "Kho A"): {"QH": 20}},
		)
		dung("phải chặn", False)
	except Exception as e:
		dung("nói còn thiếu 50", "50" in str(e))


# ------------------------------------------------------------ lô TẮT


@ca("đường dự phòng: lô đang TẮT không được tính vào khả dụng")
def _bo_lo_tat():
	# Duong du phong cong thang so kho, khong qua bo loc cua ERPNext, nen
	# no thay ca lo TAT. Lay phai lo TAT thi validate_batch chan cung ngay
	# sau do, va cau loi noi ve mot lo khong ai chon.
	ho = {
		"L-TAT": {"name": "L-TAT", "disabled": 1, "expiry_date": None},
		"L-OK": {"name": "L-OK", "disabled": 0, "expiry_date": "2027-01-01"},
		"L-CU": {"name": "L-CU", "disabled": 0, "expiry_date": "2020-01-01"},
	}
	that = lh.frappe.get_all
	try:
		lh.frappe.get_all = lambda dt, **k: [
			ho[t] for t in k.get("filters", {}).get("name", ["in", []])[1] if t in ho]
		ra = lh._bo_lo_khong_dung(
			{"L-TAT": 10, "L-OK": 20, "L-CU": 30, "L-LA": 40}, False)
		la("vòng thường chỉ còn lô còn hạn", ra, {"L-OK": 20})
		ra2 = lh._bo_lo_khong_dung(
			{"L-TAT": 10, "L-OK": 20, "L-CU": 30}, True)
		la("vòng vét giữ lô quá hạn, vẫn bỏ lô TẮT", ra2, {"L-OK": 20, "L-CU": 30})
	finally:
		lh.frappe.get_all = that


@ca("đường dự phòng: đọc hồ sơ lô hỏng thì bỏ hết, thà báo thiếu còn hơn ghi bừa")
def _ho_so_hong():
	that = lh.frappe.get_all

	def no(dt, **k):
		raise RuntimeError("gia lap DB hong")

	try:
		lh.frappe.get_all = no
		la("trả rỗng", lh._bo_lo_khong_dung({"L1": 10}, False), {})
	finally:
		lh.frappe.get_all = that


@ca("_ton_tung_lo có gọi bộ lọc lô TẮT trên đường dự phòng")
def _duong_du_phong_co_loc():
	import inspect

	nguon = inspect.getsource(lh._ton_tung_lo)
	dung("có gọi bộ lọc", "_bo_lo_khong_dung(ra, ke_ca_qua_han)" in nguon)


# ------------------------------------------------------------ thứ tự thật


@ca("xếp lô: hết hạn gần nhất lên trước, lô không ghi hạn xếp sau cùng")
def _xep_that():
	# Ca nay chay ham THAT `_xep_het_han_truoc`, khong dung ban thay the
	# cua `chay_gan_lo`.
	bang = [
		{"name": "B", "expiry_date": "2026-12-01", "creation": "2026-01-02"},
		{"name": "A", "expiry_date": "2026-09-01", "creation": "2026-01-03"},
		{"name": "C", "expiry_date": None, "creation": "2026-01-01"},
	]
	that = lh.frappe.get_all
	try:
		lh.frappe.get_all = lambda dt, **k: list(bang)
		ra = lh._xep_het_han_truoc({"B": 1, "A": 2, "C": 3})
		la("A trước B, C sau cùng", [t for t, _ in ra], ["A", "B", "C"])
	finally:
		lh.frappe.get_all = that
