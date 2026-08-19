"""Chung tu MUA DICH VU: lay so theo DAU hoa don dien tu, khong cong dong chi tiet.

Vi sao co mo dun nay
--------------------
Hoa don cuoc van chuyen GSM so 57194 ngay 31/07/2026 keo ve 929 dong chi
tiet, moi dong la mot chuyen xe. Cong 929 dong lai ra 26.609.274 trong khi
dau hoa don ghi tien truoc thue 22.068.519. Lech 4.540.755.

Truy ra thi khong phai loi lam tron. Trong phan chi tiet cua m-invoice moi
dong co truong `tchat` (tinh chat):

    tchat = 1   hang hoa, dich vu binh thuong        824 dong  18.474.089
    tchat = 5   dong phi, van tinh tien              104 dong   5.864.815
    tchat = 3   CHIET KHAU THUONG MAI                  1 dong   2.270.370
    tchat = 4   ghi chu, dien giai, khong tinh tien

May dang be nguyen moi dong thanh dong hang duong, khong doc `tchat`. Dong
chiet khau le ra phai TRU thi lai duoc CONG, nen sai so dung bang HAI LAN
dong chiet khau: 2 x 2.270.370 = 4.540.740, cong 15d lam tron tung dong cua
chinh m-invoice, ra dung 4.540.755.

Cach chua tan goc
-----------------
Voi hoa don dich vu thi so ke toan phai lay tu DAU hoa don dien tu
(`tien_truoc_thue`, `tien_thue`, `tong_tien`), khong lay tu tong cong phan
chi tiet. Dau hoa don la con so DA KY va DA GUI co quan thue; phan chi tiet
chi la dien giai, va ban than m-invoice lam tron tung dong nen cong lai gan
nhu luon lech vai dong.

Lay theo dau hoa don thi tong tren ERP luon khop tuyet doi voi hoa don dien
tu, va khong phu thuoc vao viec may hieu dung hay sai tinh chat tung dong.

Chi tiet 929 chuyen khong mat: no van nam nguyen trong `MInvoice Invoice`,
tra luc nao cung co. No chi khong duoc chay vao so nua.

Anh Viet chot 18/08/2026.

Hoa don AM, bo sung 19/08/2026 (v228)
-------------------------------------
Ve di Uc bi huy. Viet Thinh xuat hoa don C26THV so 3 ngay 18/07/2026 hoan
lai hai ve SGN-SYD/MEL-SGN, va giu lai phi huy ve:

    dong ve      -36.700.000     tien truoc thue  -36.700.000
    phi huy ve    17.430.000     tien thue                  0
    ------------------------     tong tien        -19.270.000

Tien ve tai khoan MB dung 19.270.000 luc 10:38 cung ngay. Chi phi that cua
cong ty la 17.430.000, bang 47,5% tien ve.

Quet ca 49.294 ban ghi m-invoice thay 13 hoa don am. Truoc v228 khong cai
nao chay qua duoc mo dun nay vi hai cua vao deu chan bang `goc <= 0`. v228
doi thanh `goc = 0`, va them ba viec:

    1. `so_dong_theo_dau` ghi SO LUONG am thay vi don gia am, vi ERPNext doi
       phieu tra lai phai co it nhat mot dong so luong am.
    2. `_bat_tra_lai` bat o "La Tra lai" khi hoa don am.
    3. `chan_doan_lech` goi ten nguyen nhan lech thay vi chi bao con so.

Phep can THIEU von da khong phu thuoc dau: tong dong -36.700.000 nho hon
goc -19.270.000 nen thieu 17.430.000, dung bang phi ngoai thue. Mot cong
thuc chay dung ca hoa don duong lan hoa don am.

Cai KHONG lam: hoa don am ma luoi ghi duong (hoa don Grab C26THF so 511599,
-56.460.090 tren hoa don ma phieu ghi +52.277.861) thi may khong tu lat dau.
Lat dau ca luoi 56 trieu la viec ke toan quyet, may chi goi ten va chan lai.
"""

import json

import frappe
from frappe.utils import cint, flt

PI = "Purchase Invoice"

LOAI_HANG = "Mua hàng"
LOAI_DICH_VU = "Mua dịch vụ"

# Lech bao nhieu dong thi coi la khac nhau. Mot dong: hoa don dien tu tinh
# tron den dong nen khong bao gio duoc phep lech qua the.
NGUONG_LECH = 1.0

# Tinh chat dong trong chi tiet m-invoice.
TC_CHIET_KHAU = "3"
TC_GHI_CHU = "4"

# Ten dong phi ngoai thue. Dat thanh hang so vi may phai nhan lai duoc dong
# minh da them de khong them lan hai moi lan luu.
TEN_DONG_PHI = "Phí khác theo hoá đơn, không chịu thuế"

# Dong chiet khau suy ra tu tong duoc phep lech bao nhieu so voi dong chiet
# khau ghi tren hoa don. Khoang nay chinh la phan m-invoice lam tron tung
# dong: rieng hoa don GSM 57194 la 15d tren 929 dong. Lech qua nguong nay
# thi khong phai chuyen lam tron nua, ma la co gi khac dang sai - luc do
# KHONG dung vao phieu, de cong chan lech o buoc ghi so no chan.
SAI_LECH_LAM_TRON = 100.0


# Goi y kem theo khi cong chan lech chan phieu lai. Viet san o day chu khong
# noi trong ham, de sua chu cho ke toan doc ma khong dong vao mach tinh.
LOI_KHUYEN = {
	"dau_nguoc": (
		"Hoá đơn điện tử là hoá đơn ÂM (điều chỉnh giảm, trả hàng, hoàn tiền) "
		"nhưng lưới mặt hàng trên phiếu đang ghi số DƯƠNG. Máy không tự lật dấu "
		"hộ vì đây là việc phải do kế toán quyết. Cách làm: tích ô \"Là Trả lại\", "
		"sửa số lượng từng dòng thành số âm, rồi lưu lại."
	),
	"thieu_dong_thue": (
		"Các dòng hàng đã đúng số, phiếu chỉ đang THIẾU DÒNG THUẾ. Thêm một dòng "
		"thuế loại Actual vào tài khoản 1331 bằng đúng số tiền thuế ghi trên hoá "
		"đơn, tổng sẽ khớp."
	),
	"lech_khac": (
		"Nếu là hoá đơn dịch vụ nhiều dòng chi tiết, đổi Loại chứng từ sang "
		"\"%s\" rồi lưu lại, máy sẽ lấy đúng số ở đầu hoá đơn." % LOAI_DICH_VU
	),
}


TRUONG_MOI = {
	PI: [
		{
			"fieldname": "vgb_loai_chung_tu",
			"label": "Loại chứng từ",
			"fieldtype": "Select",
			"options": "%s\n%s" % (LOAI_HANG, LOAI_DICH_VU),
			"default": LOAI_HANG,
			"insert_after": "supplier",
			"in_standard_filter": 1,
			"description": (
				"Mua hàng: giữ lưới mặt hàng chi tiết như cũ. "
				"Mua dịch vụ: gom thành một dòng, số tiền lấy thẳng từ đầu hoá đơn "
				"điện tử nên luôn khớp tuyệt đối, không còn sai số làm tròn."
			),
		},
		{
			"fieldname": "vgb_tk_chi_phi",
			"label": "Tài khoản chi phí",
			"fieldtype": "Link",
			"options": "Account",
			"insert_after": "vgb_loai_chung_tu",
			"depends_on": "eval:doc.vgb_loai_chung_tu=='%s'" % LOAI_DICH_VU,
			"description": (
				"Tài khoản ghi Nợ cho khoản dịch vụ này, ví dụ 6417 cho cước giao hàng "
				"bán, 6277 cho dịch vụ mua ngoài của bếp. Để trống thì máy giữ tài khoản "
				"đang có trên dòng, mà mặc định của hệ là 632 nên thường sai."
			),
		},
	]
}


# ------------------------------------------------------------ phep THUAN
#
# Bon ham duoi day khong cham vao Frappe, nen kiem thu duoc khong can site.


def so_theo_dau_hoa_don(dau):
	"""Doc ba con so tien tu DAU hoa don dien tu. THUAN.

	Tra ve (truoc_thue, thue, tong).

	Hoa don cua HO KINH DOANH khong co thue nen m-invoice de trong o
	`tien_truoc_thue`. Quet 1.500 hoa don gan nhat thay 5 cai nhu vay (Abby
	E33, Trai cay nhap khau, Nguyen Van Tien, Nha van hoa Thanh Nien). Lay
	nguyen o trong do la ghi so 0 dong. Nhom nay lay tong tien lam goc.
	"""
	dau = dau or {}
	tong = flt(dau.get("tong_tien"))
	thue = flt(dau.get("tien_thue"))
	truoc = flt(dau.get("tien_truoc_thue"))
	if not truoc and tong:
		truoc = tong - thue
	if not tong:
		tong = truoc + thue
	return truoc, thue, tong


def goc_dong_hang(dau):
	"""Tong cac dong hang tren phieu PHAI bang bao nhieu. THUAN.

	Day la con so quan trong nhat cua ca mo dun, va cung la cho ban dau lam
	sai. Tren ERPNext, tong phieu = tong dong hang + cac dong thue. Dong
	thue cua minh la loai Actual, so cung bung nguyen tu hoa don. Vay:

	    tong dong hang = tong_tien - tien_thue

	KHONG phai `tien_truoc_thue`. Hai con so do chi trung nhau khi hoa don
	khong co khoan nao nam ngoai co so tinh thue.

	Mot cong thuc nay xu dung ca ba nhom da gap:

	    GSM 57194        23.834.001 - 1.765.482 = 22.068.519, trung tien
	                     truoc thue vi khong co phi.
	    Viet Thinh 752    1.850.000 -   131.320 =  1.718.680, tuc tien truoc
	                     thue 1.641.499 cong 77.181 phi ngoai thue.
	    Ho kinh doanh       320.760 -         0 =    320.760, tron ven.

	Khong can chia nhanh theo loai doi tac, khong can doan.
	"""
	_truoc, thue, tong = so_theo_dau_hoa_don(dau)
	return tong - thue


def phi_ngoai_thue(dau):
	"""Phan tien nam NGOAI co so tinh thue. THUAN.

	Ve may bay cua dai ly co phi xuat ve, phi san bay, phu phi he thong. Cac
	khoan nay khong chiu thue GTGT nen khong nam trong `tien_truoc_thue`,
	nhung van phai tra nen van nam trong `tong_tien`. Tren ban in hoa don
	chung nam o mot bang rieng ten "Ten loai phi".

	Doctype MInvoice Invoice khong co truong nao chua bang phi do - no bi bo
	ngay o buoc keo du lieu ve. Nhung so tien thi suy nguoc duoc chinh xac
	tu hieu ba con so tong, nen khong can keo lai.

	Phi khong duoc khau tru thue dau vao, nen phai vao tai khoan chi phi
	chu khong vao 1331.
	"""
	truoc, _thue, _tong = so_theo_dau_hoa_don(dau)
	return goc_dong_hang(dau) - truoc


def la_hoa_don_am(dau):
	"""Hoa don DIEU CHINH GIAM, tra hang, hoan tien. THUAN.

	Ngay 18/07/2026 Viet Thinh xuat hoa don C26THV so 3 hoan hai ve
	SGN-SYD/MEL-SGN: dong ve -36.700.000, phi huy ve 17.430.000, tong thanh
	toan -19.270.000, va tien ve tai khoan dung 19.270.000.

	Quet 49.294 ban ghi m-invoice thay 13 hoa don am nhu vay. Truoc v228 ca
	13 deu bi bo qua: `goc <= 0` chan het o cua vao. Gio chi chan `goc = 0`,
	con am thi di tiep - moi phep can duoi day von da khong phu thuoc dau.
	"""
	return goc_dong_hang(dau) < 0


def so_dong_theo_dau(tien):
	"""Doi so tien thanh cap (so luong, don gia) ma ERPNext chiu. THUAN.

	ERPNext doi phieu tra lai phai co it nhat mot dong SO LUONG AM, chu
	khong phai don gia am. Xem phieu HDM-2026-00325 do chinh may sinh ra:
	so luong -5, don gia 69.000, thanh tien -345.000.

	Nhan lai van ra dung so tien ban dau, nen ham nay khong lam thay doi gi
	ve gia tri, chi la cach ghi.
	"""
	tien = flt(tien)
	if tien < 0:
		return -1, -tien
	return 1, tien


def chan_doan_lech(dau, tong_phieu, tong_thue_tren_phieu, nguong=NGUONG_LECH):
	"""Vi sao tong phieu khong bang dau hoa don. THUAN.

	Bao cao lech tong khong thi ke toan phai tu mo ra doan. Ba nguyen nhan
	da gap thi may goi ten duoc ngay:

	    dau_nguoc       hoa don am ma phieu ghi duong, hoac nguoc lai. Hoa
	                    don Grab C26THF so 511599 la -56.460.090 ma phieu
	                    ACC-PINV-2026-02399 ghi +52.277.861.
	    thieu_dong_thue phieu dung so hang nhung khong co dong thue Actual.
	                    Phieu tra lai Green Ball HDM-2026-00325 ghi -372.778
	                    trong khi hoa don -402.600, thieu dung phan thue
	                    -29.822.
	    lech_khac       chua xep duoc, de nguoi doc.

	`nguong` mac dinh 1 dong, dung cho cong chan ghi so: hoa don dien tu la
	so da gui co quan thue, lech mot dong cung la sai.

	Bao cao doi soat thi dat nguong cao hon. Quet that ngay 19/08/2026 tren
	47.184 hoa don: 1.569 hoa don DAU RA lech tu 1 den 100 dong, toan bo la
	sai so lam tron giua ERPNext va m-invoice. Bao cao ma keu 1.569 lan vi
	vai dong thi khong ai doc nua, va do dung la ly do khong ai phat hien ra
	11 hoa don am bi nuot.
	"""
	_truoc, thue, tong = so_theo_dau_hoa_don(dau)
	tong_phieu = flt(tong_phieu)
	if not lech_qua_nguong(tong_phieu, tong, nguong):
		return "khop"
	if tong and tong_phieu and (tong < 0) != (tong_phieu < 0):
		return "dau_nguoc"
	if thue and not flt(tong_thue_tren_phieu) and not lech_qua_nguong(
			tong_phieu + flt(thue), tong, nguong):
		return "thieu_dong_thue"
	return "lech_khac"


def gom_dong_theo_tinh_chat(chi_tiet):
	"""Cong phan chi tiet cho DUNG DAU. THUAN.

	Dong chiet khau thuong mai (tchat 3) phai tru ra, dong ghi chu dien giai
	(tchat 4) khong tinh tien. Moi thu con lai cong vao.

	Dung de doi chieu va de vet lai luong mua hang thuong, chu luong mua dich
	vu thi khong dung den phan chi tiet nua.
	"""
	tong = 0.0
	for d in chi_tiet or []:
		tc = str(d.get("tchat"))
		if tc == TC_GHI_CHU:
			continue
		tien = flt(d.get("thtien"))
		tong += -tien if tc == TC_CHIET_KHAU else tien
	return tong


def ten_theo_tinh_chat(chi_tiet):
	"""Tap ten dong chiet khau va tap ten dong ghi chu. THUAN.

	Ghep theo TEN vi dong hang tren phieu khong giu lai `tchat`. Voi hoa don
	dich vu thi ten dong chinh la truong `ten` cua m-invoice, nen ghep duoc.
	Hoa don hang hoa co ma mat hang that thi ten dong la ten cua Mat hang,
	ghep khong ra - luc do ham tra ve tap rong va may khong dung vao phieu.
	"""
	ck = set()
	gc = set()
	for d in chi_tiet or []:
		ten = (d.get("ten") or "").strip()
		if not ten:
			continue
		tc = str(d.get("tchat"))
		if tc == TC_CHIET_KHAU:
			ck.add(ten)
		elif tc == TC_GHI_CHU:
			gc.add(ten)
	return ck, gc


def ke_hoach_sua_chiet_khau(dong, chi_tiet, goc, cho_phep=SAI_LECH_LAM_TRON):
	"""Dung ke hoach chua phieu bi cong nham dong chiet khau. THUAN.

	`dong` la danh sach {"ten": ..., "tien": ...} cua cac dong hang dang co.

	Tra ve {"bo": [chi so can bo], "chiet_khau": so tien} hoac None neu
	khong dung vao phieu. Tra ve None la an toan: cong chan lech o buoc ghi
	so van chan, ke toan doi sang chung tu mua dich vu la xong.

	Vi sao dat chiet khau bang HIEU so chu khong bang dong chiet khau ghi
	tren hoa don: hieu so nuot luon phan m-invoice lam tron tung dong, nen
	tong tren ERP khop tuyet doi voi hoa don. Con so cua rieng dong chiet
	khau chi dung de kiem lai xem hieu so co hop ly khong.
	"""
	ck, gc = ten_theo_tinh_chat(chi_tiet)
	if not ck and not gc:
		return None
	bo = [i for i, d in enumerate(dong or []) if (d.get("ten") or "").strip() in (ck | gc)]
	if not bo:
		return None
	con_lai = sum([flt(d.get("tien")) for i, d in enumerate(dong) if i not in bo])
	chiet_khau = con_lai - flt(goc)
	if chiet_khau < 0:
		return None
	ghi_tren_hoa_don = sum([
		flt(d.get("tien")) for d in dong if (d.get("ten") or "").strip() in ck
	])
	if abs(chiet_khau - ghi_tren_hoa_don) > flt(cho_phep):
		return None
	return {"bo": bo, "chiet_khau": chiet_khau, "con_lai": con_lai}


def lech_qua_nguong(a, b, nguong=NGUONG_LECH):
	"""Hai con so nay co coi la khac nhau khong. THUAN."""
	return abs(flt(a) - flt(b)) > flt(nguong)


def da_khop_roi(tong_dong, goc):
	"""Luoi mat hang da dung so chua. THUAN.

	Xet theo TONG chu khong theo so dong. Nho vay mot ham lo duoc ca hai
	viec: khong gom de len cai vua gom, va khong dung vao phieu ma ke toan
	da tu tach dong theo tai khoan mien la tong van dung.
	"""
	return not lech_qua_nguong(tong_dong, goc)


def dong_dich_vu(ten_ncc, so_hd, truoc_thue, tk_chi_phi=None, trung_tam=None):
	"""Dung mot dong hang gom cho hoa don dich vu. THUAN."""
	mo_ta = "Dịch vụ mua ngoài theo hoá đơn %s" % (so_hd or "")
	if ten_ncc:
		mo_ta = "%s, %s" % (mo_ta.rstrip(", "), ten_ncc)
	sl, gia = so_dong_theo_dau(truoc_thue)
	dong = {
		"item_name": (mo_ta[:140] or "Dịch vụ mua ngoài"),
		"description": mo_ta,
		"qty": sl,
		"uom": "Nos",
		"stock_uom": "Nos",
		"conversion_factor": 1,
		"rate": gia,
		"amount": flt(truoc_thue),
	}
	if tk_chi_phi:
		dong["expense_account"] = tk_chi_phi
	if trung_tam:
		dong["cost_center"] = trung_tam
	return dong


def dong_phi(so_hd, tien, tk_chi_phi=None, trung_tam=None):
	"""Dung dong PHI NGOAI THUE. THUAN.

	De rieng mot dong co ten ro rang chu khong cong gop vao dong hang: luc
	quyet toan nhin ra ngay phan nao co hoa don thue phan nao khong.
	"""
	mo_ta = "%s theo hoá đơn %s" % (TEN_DONG_PHI, so_hd or "")
	sl, gia = so_dong_theo_dau(tien)
	dong = {
		"item_name": TEN_DONG_PHI,
		"description": mo_ta,
		"qty": sl,
		"uom": "Nos",
		"stock_uom": "Nos",
		"conversion_factor": 1,
		"rate": gia,
		"amount": flt(tien),
	}
	if tk_chi_phi:
		dong["expense_account"] = tk_chi_phi
	if trung_tam:
		dong["cost_center"] = trung_tam
	return dong


# ------------------------------------------------------------ cham vao he


def _dau_hoa_don(ma_minvoice):
	"""Doc dau hoa don dien tu. Khong co thi tra ve None."""
	if not ma_minvoice:
		return None
	if not frappe.db.exists("MInvoice Invoice", ma_minvoice):
		return None
	return frappe.db.get_value(
		"MInvoice Invoice",
		ma_minvoice,
		["so_hd", "tien_truoc_thue", "tien_thue", "tong_tien"],
		as_dict=True,
	)


def _trung_tam_mac_dinh(doc):
	"""Trung tam chi phi de dat len dong. Thieu la ERPNext chan ghi so."""
	for d in doc.get("items") or []:
		if d.get("cost_center"):
			return d.get("cost_center")
	if doc.get("cost_center"):
		return doc.get("cost_center")
	return frappe.db.get_value("Company", doc.get("company"), "cost_center")


def _tk_chi_phi_dang_dung(doc):
	"""Tai khoan chi phi dang co tren dong dau, dung khi ke toan chua chon."""
	for d in doc.get("items") or []:
		if d.get("expense_account"):
			return d.get("expense_account")
	return None


def truoc_khi_luu(doc, method=None):
	"""Gom hoa don dich vu thanh mot dong. Goi tu before_validate."""
	dau = _dau_hoa_don(doc.get("custom_minvoice_id"))
	if not dau:
		return
	if (doc.get("vgb_loai_chung_tu") or LOAI_HANG) != LOAI_DICH_VU:
		# Luong mua hang thuong: giu nguyen luoi mat hang, chi chua dong
		# chiet khau bi cong nham dau neu co.
		try:
			_can_theo_dau_hoa_don(doc, dau)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "mua_dich_vu: can theo dau hoa don")
		return
	truoc_thue, _thue, _tong = so_theo_dau_hoa_don(dau)
	goc = goc_dong_hang(dau)
	if not goc:
		return

	dong_hien = doc.get("items") or []
	if da_khop_roi(sum([flt(d.get("amount")) for d in dong_hien]), goc):
		return
	if goc < 0:
		# Phieu tra lai: ERPNext doi co o "La Tra lai" thi moi chiu so luong
		# am. Nhanh dich vu tu dung lai toan bo luoi nen bat o nay o day la
		# an toan, khong lam hong luoi dang co.
		_bat_tra_lai(doc)

	tk = doc.get("vgb_tk_chi_phi") or _tk_chi_phi_dang_dung(doc)
	tt = _trung_tam_mac_dinh(doc)
	so_hd = dau.get("so_hd") or doc.get("bill_no")
	phi = phi_ngoai_thue(dau)

	doc.set("items", [])
	# Dong chiu thue truoc, dong phi sau. Hai dong chu khong mot: dong tren
	# co hoa don thue de khau tru, dong duoi thi khong.
	doc.append("items", dong_dich_vu(
		doc.get("supplier_name") or doc.get("supplier"), so_hd,
		truoc_thue if phi > 0 else goc, tk, tt))
	if phi > 0:
		doc.append("items", dong_phi(so_hd, phi, tk, tt))


def _can_theo_dau_hoa_don(doc, dau):
	"""Can luoi mat hang cua phieu MUA HANG cho khop dau hoa don dien tu.

	Khong dung vao `MInvoice Make Docs`: script do dai, nam trong co so du
	lieu, git khong thay, va no sinh ra MOI hoa don keo tu m-invoice. Can o
	day thi viec nam trong ma nguon, co kiem thu, va go ra duoc bang mot dot
	deploy neu sai.

	Hai chieu lech, hai cach can:

	THUA tien, tuc chi tiet co dong chiet khau thuong mai bi cong thay vi
	tru (hoa don GSM). Bo dong chiet khau va dong ghi chu ra khoi luoi, dat
	so tien do vao o Chiet khau cua ca phieu.

	THIEU tien, tuc hoa don co khoan nam ngoai co so tinh thue ma m-invoice
	khong day vao chi tiet (ve may bay Viet Thinh). Them mot dong phi bang
	dung phan thieu.

	Lam gi cung chi de dat toi mot dich: tong dong hang bang `goc_dong_hang`.
	"""
	if cint(doc.get("docstatus")) != 0:
		return
	goc = goc_dong_hang(dau)
	if not goc:
		return
	dong_hien = doc.get("items") or []
	if not dong_hien:
		return
	tong_dong = sum([flt(d.get("amount")) for d in dong_hien])
	if da_khop_roi(tong_dong, goc):
		return

	if goc < 0 and tong_dong > 0:
		# Hoa don am ma luoi lai ghi duong: khong phai chuyen lam tron ma la
		# ca luoi bi dung nguoc dau (hoa don Grab C26THF so 511599). Tu lat
		# dau ho la lam thay ke toan tren mot con so 56 trieu, khong lam.
		# De cong chan lech o buoc ghi so goi ten va chan lai.
		return
	if goc < 0:
		_bat_tra_lai(doc)

	if tong_dong > goc:
		_can_phan_thua(doc, dau, goc)
	else:
		_can_phan_thieu(doc, dau, goc, tong_dong)


def _bat_tra_lai(doc):
	"""Bat o La Tra lai cho phieu am, neu chua bat."""
	if not cint(doc.get("is_return")):
		doc.is_return = 1


def _can_phan_thua(doc, dau, goc):
	"""Thua tien thi bo dong chiet khau ra, dat vao o Chiet khau cua phieu."""
	if flt(goc) < 0:
		# O Chiet khau cua ERPNext tinh tren Net Total duong. Tren phieu tra
		# lai no chay nguoc, nen khong dung vao. Chua gap ca nao that, va
		# neu gap thi de cong chan lech chan chu khong doan.
		return
	if flt(doc.get("discount_amount")):
		return
	ct = frappe.db.get_value("MInvoice Invoice", doc.get("custom_minvoice_id"), "chi_tiet")
	if not ct:
		return
	dong = [
		{"ten": (d.get("item_name") or "").strip(), "tien": flt(d.get("amount"))}
		for d in doc.get("items")
	]
	kh = ke_hoach_sua_chiet_khau(dong, json.loads(ct or "[]"), goc)
	if not kh:
		return
	giu = [d for i, d in enumerate(doc.get("items")) if i not in kh["bo"]]
	if not giu:
		return
	doc.set("items", giu)
	doc.apply_discount_on = "Net Total"
	doc.discount_amount = kh["chiet_khau"]


def _can_phan_thieu(doc, dau, goc, tong_dong):
	"""Thieu tien thi them mot dong phi bang dung phan thieu.

	Chi them khi phan thieu dung bang phi ngoai thue suy ra tu dau hoa don.
	Lech chut it la chuyen lam tron nen van cho; lech nhieu la co gi khac
	dang sai, khong tu y them - de cong chan lech o buoc ghi so no chan.

	v228 bo chot cu `thieu >= goc`. Chot do von da chet tren hoa don duong:
	da doi `thieu` bang dung `goc - truoc`, muon `thieu >= goc` thi phai co
	`truoc <= 0`, ma `so_theo_dau_hoa_don` da dung tong bu vao o trong roi
	nen luc do `thieu` bang 0 va ham thoat tu dong tren. Tren hoa don AM thi
	chot do lai chan nham that: hoan ve Viet Thinh co `thieu` 17.430.000 con
	`goc` la -19.270.000, thieu lon hon goc nen bi chan oan.
	"""
	thieu = goc - tong_dong
	if thieu <= 0:
		return
	if lech_qua_nguong(thieu, phi_ngoai_thue(dau), SAI_LECH_LAM_TRON):
		return
	if [d for d in doc.get("items") if (d.get("item_name") or "").strip() == TEN_DONG_PHI]:
		return
	doc.append("items", dong_phi(
		dau.get("so_hd") or doc.get("bill_no"),
		thieu,
		doc.get("vgb_tk_chi_phi") or _tk_chi_phi_dang_dung(doc),
		_trung_tam_mac_dinh(doc),
	))


def chan_lech_tong(doc, method=None):
	"""Khong cho ghi so khi tong tien lech voi hoa don dien tu.

	Truoc day cho nay chi CANH BAO do tren man. Canh bao thi bam qua duoc,
	nen phieu sai van vao so duoc. Hoa don dien tu la con so da gui co quan
	thue, lech mot dong cung la sai.
	"""
	dau = _dau_hoa_don(doc.get("custom_minvoice_id"))
	if not dau:
		return
	_truoc, _thue, tong = so_theo_dau_hoa_don(dau)
	if not tong:
		return
	tong_phieu = flt(doc.get("base_grand_total"))
	if not lech_qua_nguong(tong_phieu, tong):
		return
	ly_do = chan_doan_lech(dau, tong_phieu, doc.get("base_total_taxes_and_charges"))
	frappe.throw(
		"Tổng tiền phiếu %s đ không khớp hoá đơn điện tử %s đ (lệch %s đ). "
		"Hoá đơn điện tử là con số đã gửi cơ quan thuế, không được ghi sổ khi lệch.\n\n%s"
		% (
			tong_phieu,
			flt(tong),
			tong_phieu - flt(tong),
			LOI_KHUYEN.get(ly_do) or LOI_KHUYEN["lech_khac"],
		)
	)
