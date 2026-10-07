# -*- coding: utf-8 -*-
"""#420 v579: phần thuần của đối soát vendor: xem trước, nối hoá đơn, tiền về.

Ba lớp không gộp làm một (thiết kế đã duyệt 03/10/2026):
  đủ nguồn   tệp đọc đủ dòng, khớp tổng in trên tệp (xem_truoc)
  khớp tiền  tiền vendor trả đã thấy trên sao kê ngân hàng (khop_ngan_hang)
  đủ chứng từ từng đơn của vendor đã nối đúng hoá đơn bán / chuyến đã nối
             hoá đơn mua (khop_hoa_don)
Anh Việt 06/10/2026 chốt: kế toán bấm nhận thì CHỈ LƯU VÀ ĐỐI CHIẾU. Không
lập phiếu, không bút toán phí. Mọi hàm ở đây chỉ trả kết quả để hiển thị.
"""

# phần thuần
import hashlib
import json
import re
from datetime import date

from vagabond.doi_soat_nguon import LoiNguon, chuan_dong

NHOM_TEN = {"ban": "Tiền bán", "chuyen": "Chuyến đi", "the": "Thẻ tín dụng", "tong_hop": "Tổng hợp"}
TEN_NHOM = {v: k for k, v in NHOM_TEN.items()}


def _bam(du_lieu):
	return hashlib.sha256(json.dumps(du_lieu, ensure_ascii=False, sort_keys=True,
		separators=(",", ":")).encode("utf-8")).hexdigest()


def khoa(cong_ty, vendor, tai_khoan, ma_su_kien):
	"""Cùng công thức với doi_soat_nguon.chuan_dong để hai lớp không lệch nhau."""
	return _bam(dict(cong_ty=cong_ty, vendor=vendor, merchant=tai_khoan, tien_te="VND", ma_su_kien=ma_su_kien))


# Codex #450: mọi trường làm đổi kết quả đối chiếu (số hoá đơn, chuyến giao hàng,
# ngày tiền về, thuế) đều nằm trong dấu nội dung; vendor sửa một trong số đó thì
# là "nội dung khác", không bị coi là trùng rồi bỏ qua.
_TRUONG_NOI_DUNG = ("ma_su_kien", "loai", "ngay", "ma_don", "ma_can_cu", "tien_hang", "giam_gia", "phi",
	"dieu_chinh", "thuc_nhan", "hoa_don", "giao_hang", "ngay_tien_ve", "thue", "mo_ta")
# Codex #450 vòng 13: mo_ta mang phân loại thanh toán (Grab "tiền mặt" hay
# "thẻ/ví"), _tien_ve đọc nó để chặn tự nhận tiền về. Vendor sửa phân loại mà
# dấu không đổi thì bản sửa bị coi là trùng, giữ dòng cũ sai.


def doc_lai_duoc(trang_thai):
	"""Codex #446 H4: tải lại đúng tệp đã nhận thì dừng ở mã băm, TRỪ nguồn
	đang lỗi hoặc cần xử lý: cho đọc lại để gỡ được sau khi sửa mẫu."""
	return trang_thai in ("Lỗi tệp", "Cần xử lý")


def dau_noi_dung(dong):
	# giao_hang: False và thiếu khoá là như nhau, để dòng cũ không chuyến giao hàng
	# không đổi dấu chỉ vì bộ đọc thêm khoá.
	return _bam({k: (bool(dong.get(k)) if k == "giao_hang" else dong.get(k, "")) for k in _TRUONG_NOI_DUNG})


def xem_truoc(kq, cong_ty, da_nhan=None):
	"""Phân mọi dòng của một tệp thành mới / đã có / lỗi. Không ghi gì.

	da_nhan là {khoá: dấu nội dung} máy chủ đọc từ cơ sở dữ liệu. Dòng tiền
	bán còn đi qua hợp đồng chuan_dong của Codex (#422) để giữ đúng các luật
	đã review: phương trình tiền, dấu bán/hoàn, căn cứ điều chỉnh, trong kỳ.
	Một mã sự kiện xuất hiện hai lần trong cùng tệp thì cả nhóm thành lỗi.
	"""
	da_nhan = dict(da_nhan or {})
	vendor, tk = kq["vendor"], kq["tai_khoan"]
	nguon_codex = dict(cong_ty=cong_ty, vendor=vendor, merchant=tk or "-", tien_te="VND",
		tu_ngay=kq["tu_ngay"], den_ngay=kq["den_ngay"], dinh_dang="chuan")
	dem = {}
	for d in kq["dong"]:
		dem[d["ma_su_kien"]] = dem.get(d["ma_su_kien"], 0) + 1
	ra = []
	for vi_tri, d in enumerate(kq["dong"], 1):
		d = dict(d)
		d["khoa"] = khoa(cong_ty, vendor, tk or "-", d["ma_su_kien"])
		d["dau_noi_dung"] = dau_noi_dung(d)
		try:
			if not d["ma_su_kien"]:
				raise LoiNguon("Thiếu mã sự kiện.")
			if not tk:
				# Codex #446 F3: khoá sự kiện gồm tài khoản nguồn. Chưa rõ tài
				# khoản (một tệp lẫn nhiều tài khoản) mà vẫn ghi thì lúc tải lại
				# tệp đã tách, cùng sự kiện ra khoá khác và bị nhận hai lần.
				raise LoiNguon("Chưa xác định tài khoản nguồn của tệp; tách tệp theo tài khoản rồi tải lại.")
			if dem[d["ma_su_kien"]] > 1:
				raise LoiNguon("Mã sự kiện lặp trong cùng tệp; giữ cả nhóm để kế toán xem.")
			if kq["nhom"] == "ban":
				chuan_dong(nguon_codex, dict(cong_ty=cong_ty, vendor=vendor, merchant=tk or "-", tien_te="VND",
					ma_su_kien=d["ma_su_kien"], ma_don=d["ma_don"] or d["ma_su_kien"], loai=d["loai"],
					ngay=d["ngay"], tien_hang=d["tien_hang"], phi=d["phi"], dieu_chinh=d["dieu_chinh"],
					thuc_nhan=d["thuc_nhan"], ma_can_cu=d.get("ma_can_cu") or None))
			elif d["loai"] in ("dieu_chinh", "phi", "lai", "phi_quan_ly") and not d.get("ma_can_cu"):
				raise LoiNguon("Dòng %s thiếu căn cứ; giữ để kế toán xem." % d["loai"])
			if d["khoa"] in da_nhan:
				if da_nhan[d["khoa"]] != d["dau_noi_dung"]:
					raise LoiNguon("Sự kiện đã nhận trước đó nhưng nội dung khác; cần đối chiếu bản điều chỉnh.")
				ra.append(dict(vi_tri=vi_tri, trang_thai="trung", dong=d))
			else:
				ra.append(dict(vi_tri=vi_tri, trang_thai="moi", dong=d))
		except LoiNguon as e:
			ra.append(dict(vi_tri=vi_tri, trang_thai="loi", dong=d, ly_do=str(e)))
	for l in kq["dong_loi"]:
		ra.append(dict(vi_tri=l["vi_tri"], trang_thai="loi", ly_do=l["ly_do"], dong=None))
	tong = {k: sum(x["dong"][k] for x in ra if x["dong"] and x["trang_thai"] != "loi")
		for k in ("tien_hang", "phi", "thuc_nhan")}
	so = {t: sum(1 for x in ra if x["trang_thai"] == t) for t in ("moi", "trung", "loi")}
	loi = list(kq["loi"])
	if not kq["mau"]:
		trang_thai = "Lỗi tệp"
	elif loi or so["loi"]:
		trang_thai = "Cần xử lý"
	else:
		trang_thai = "Đã nhận"
	return dict(dong=ra, so=so, tong=tong, trang_thai=trang_thai, loi=loi, canh_bao=list(kq["canh_bao"]))


# ------------------------------------------------------------ nối hoá đơn bán

def _so(s):
	return re.sub(r"\D", "", s or "")


def _ma_khop(kieu, ma_nguon, ma_hd):
	"""Mã của vendor (trên báo cáo) có trùng mã thu ngân gõ trên hoá đơn không.

	Mỗi nguồn một luật vì thu ngân chỉ gõ phần ngắn (pt_thanh_toan.MAC_DINH):
	GrabFood GF-<số>, ShopeeFood 4 số cuối, Xanh SM XSM-<mã rút gọn>, Payoo số
	tham chiếu trên bill, Shinhan mã chuẩn chi 6 ký tự.
	"""
	a = (ma_nguon or "").upper().replace(" ", "")
	b = (ma_hd or "").upper().replace(" ", "")
	if not a or not b:
		return False
	if kieu == "grab":
		pa, pb = a[:3], b[:3]
		if pa != pb:
			return False
		ra, rb = a[3:], b[3:]
		# PDF có khi thêm "F" cuối mã (GF-398F); thu ngân gõ 398.
		return ra == rb or (ra.rstrip("F") == rb.rstrip("F") and ra.rstrip("F") != "")
	if kieu == "shopee":
		sa, sb = _so(a), _so(b)
		return len(sb) >= 4 and sa.endswith(sb)
	if kieu == "greensm":
		return _so(b.replace("XSM-", "")) == _so(a) and _so(a) != "" or b.replace("XSM-", "") == a
	if kieu == "payoo":
		return a == b or (len(b) >= 4 and a.endswith(b))
	if kieu == "shinhan":
		return a == b.lstrip("'")
	return False


KIEU_THEO_MAU = {"grabfood": "grab", "shopeefood": "shopee", "greensm_ngon": "greensm",
	"payoo_the": "payoo", "payoo_qr": "payoo", "shinhan_ngay": "shinhan", "shinhan_thang": "shinhan",
	"onepay_ngay": "onepay", "onepay_thang": "onepay"}

# Số ngày lệch tối đa giữa ngày trên báo cáo vendor và ngày hoá đơn.
LECH_NGAY = {"grab": 0, "shopee": 0, "greensm": 0, "payoo": 1, "shinhan": 1, "onepay": 3}


def tien_so_sanh(kieu, dong):
	"""Tiền trên hoá đơn tương ứng với dòng vendor: sàn thì trị giá trước
	khuyến mại quán chịu (hoá đơn ghi giá menu), cổng thẻ thì số quẹt."""
	if kieu in ("grab", "shopee", "greensm"):
		return dong["tien_hang"] + dong["giam_gia"]
	return dong["tien_hang"]


def _lech_ngay(a, b):
	return abs(date.fromisoformat(a).toordinal() - date.fromisoformat(b).toordinal())


def khop_hoa_don(kieu, dong_ds, ung_vien):
	"""Nối từng dòng bán của vendor với một hoá đơn bán, một đối một.

	ung_vien: [{name, ngay, tien, ma: [mã tham chiếu trên hoá đơn]}], máy chủ
	đã lọc đúng nguồn/phương thức và khoảng ngày. Trả {chỉ số dòng: kết quả}.
	Lượt 1 nối theo mã (cùng tiền là Đã nối, khác tiền là Lệch tiền). Lượt 2
	chỉ cho dòng chưa nối: nối theo tiền khi đúng một hoá đơn còn trống cùng
	tiền trong khoảng ngày; hai hoá đơn trở lên là Nhiều chứng từ. Không bao
	giờ nối một hoá đơn cho hai dòng.
	"""
	kq = {}
	da_dung = set()
	ban = [(i, d) for i, d in enumerate(dong_ds) if d["loai"] in ("ban", "hoan")]
	cho_lech = LECH_NGAY.get(kieu, 0)
	for i, d in enumerate(dong_ds):
		if d["loai"] not in ("ban", "hoan"):
			kq[i] = dict(trang_thai="Không áp dụng", hoa_don="", ghi_chu="")
	for i, d in ban:
		if kieu == "onepay":
			continue
		tien = tien_so_sanh(kieu, d)
		hop = [u for u in ung_vien if u["name"] not in da_dung and _lech_ngay(u["ngay"], d["ngay"]) <= cho_lech
			and any(_ma_khop(kieu, d["ma_tham_chieu"], m) for m in u["ma"])]
		if len(hop) > 1:
			dung_tien = [u for u in hop if u["tien"] == tien]
			hop = dung_tien if len(dung_tien) == 1 else hop
		if len(hop) == 1:
			u = hop[0]
			da_dung.add(u["name"])
			if u["tien"] == tien:
				kq[i] = dict(trang_thai="Đã nối", hoa_don=u["name"], ghi_chu="")
			else:
				kq[i] = dict(trang_thai="Lệch tiền", hoa_don=u["name"],
					ghi_chu="Hoá đơn %s, báo cáo %s." % (_vn(u["tien"]), _vn(tien)))
		elif len(hop) > 1:
			kq[i] = dict(trang_thai="Nhiều chứng từ", hoa_don="",
				ghi_chu="Trùng mã: " + ", ".join(u["name"] for u in hop[:5]))
	for i, d in ban:
		if i in kq:
			continue
		tien = tien_so_sanh(kieu, d)
		hop = [u for u in ung_vien if u["name"] not in da_dung and u["tien"] == tien
			and _lech_ngay(u["ngay"], d["ngay"]) <= cho_lech and _cung_tien_to(d, u)]
		if len(hop) == 1:
			da_dung.add(hop[0]["name"])
			kq[i] = dict(trang_thai="Nối theo tiền", hoa_don=hop[0]["name"],
				ghi_chu="Không có mã chung; chỉ khớp số tiền và ngày, kế toán xem lại.")
		elif len(hop) > 1:
			kq[i] = dict(trang_thai="Nhiều chứng từ", hoa_don="",
				ghi_chu="Cùng tiền, cùng ngày: " + ", ".join(u["name"] for u in hop[:5]))
		else:
			kq[i] = dict(trang_thai="Không thấy chứng từ", hoa_don="",
				ghi_chu="Không có hoá đơn bán cùng mã hoặc cùng tiền trong khoảng ngày.")
	return kq


def _cung_tien_to(d, u):
	"""Ứng viên có tiền tố mã riêng (Grab: GF- giao hàng, GD- Dine-Out) thì
	chỉ nối theo tiền với dòng cùng tiền tố. Không có tiền tố thì không chặn."""
	tt = u.get("tien_to") or ""
	ma = (d.get("ma_tham_chieu") or "").upper()
	return not tt or not ma or ma.startswith(tt)


def _vn(n):
	return "{:,}".format(int(n)).replace(",", ".")


# ------------------------------------------------------------ tiền về ngân hàng

# Mẫu nội dung giao dịch tiền về của từng nguồn, rút từ sao kê MB thật
# (06/10/2026): "PVS1447922 OnePay tam ung VAGABOND QT ...", "Payoo TT TD
# ngay 02.10 04.10.2026.VAGABOND TONG", "Grab TT 118203316 ... Tran Cao Van",
# "SHOPEEPAY CHUYEN TIEN ... ShopeeFood thanh toan tu dong 04 10 2026".
MAU_TIEN_VE = {
	"onepay": r"onepay tam ung",
	"payoo": r"payoo tt",
	"grabfood": r"^grab tt",
	"shopeefood": r"shopeefood thanh toan",
	"greensm_ngon": r"xanh ?sm|gsm|green ?sm",
	"shinhan": r"",
}


def nhom_tien_ve(mau):
	if mau.startswith("onepay"):
		return "onepay"
	if mau.startswith("payoo"):
		return "payoo"
	if mau.startswith("shinhan"):
		return "shinhan"
	return mau


# Trạng thái tiền về còn chờ kế toán xem (đếm ở thẻ Việc cần làm, lọc Chờ tiền về).
CHO_TIEN_VE = ("Chưa thấy tiền về", "Lệch tiền về", "Cần chọn tiền về")
# Khoá lọc gộp cả ba trạng thái chờ (thẻ Việc cần làm và chip "Chờ tiền về").
NHOM_CHO_TIEN = "Chờ tiền về"
# Dòng của bản đọc cũ đã được bản đọc lại thay (giữ làm vết, không tính nữa).
DA_THAY = "Đã thay"
# Codex #450: chỉ "Đã nối" mới là đủ chứng từ. "Nối theo tiền" là GỢI Ý, còn
# chờ kế toán xác nhận nên vẫn tính là chưa nối. Một nguồn cho đếm và lọc.
DA_NOI = ("Đã nối",)
KHONG_TINH_CHUA_NOI = ("Đã nối", "Không áp dụng")
# Trạng thái GIỮ hoá đơn (nguồn khác không được dùng lại): nối theo mã hoặc đã
# xác nhận. Gợi ý "Nối theo tiền" chưa xác nhận không giữ, để dòng mang đúng
# mã của hoá đơn đó (ở nguồn khác) vẫn nối được.
GIU_HOA_DON = ("Đã nối", "Lệch tiền")
# Mã số thuế người bán của từng nguồn chuyến đi: hoá đơn mua chỉ tìm trong nhà
# cung cấp mang đúng mã này (số và ký hiệu hoá đơn không duy nhất giữa người bán).
MST_NCC = {"be": "0108269207", "xanh_taxi": "0110269067", "grab_business": "0312650437",
	"grab_business_cu": "0312650437"}


def chung_tu_chuyen(giao_hang, hoa_don_nguon, van_don, purchase_invoice, ky=None):
	"""Trạng thái nối của một dòng chuyến đi. THUẦN.

	Codex #450: chuyến giao hàng cần vận đơn; chuyến có số hoá đơn riêng
	(ký hiệu#số) cần hoá đơn mua; nguồn xuất MỘT hoá đơn cả kỳ (Be, Xanh SM)
	thì mọi chuyến cần hoá đơn kỳ đó. ky=None là nguồn không có hoá đơn kỳ,
	còn lại là dict(pi=tên hoá đơn kỳ hoặc None, nhieu=[các hoá đơn cùng tiền]).
	Chỉ "Đã nối" khi ĐỦ mọi chứng từ cần có; thiếu thì nói rõ thiếu gì.
	Trả (trạng thái, ghi chú)."""
	can = []
	if giao_hang:
		can.append(("van_don", "vận đơn"))
	if hoa_don_nguon and "#" in hoa_don_nguon:
		can.append(("purchase_invoice", "hoá đơn mua " + hoa_don_nguon.replace("#", " số ")))
	pi_ky = (ky or {}).get("pi")
	if ky is not None:
		can.append(("ky", "hoá đơn mua cả kỳ"))
	co = {"van_don": van_don, "purchase_invoice": purchase_invoice, "ky": pi_ky}
	da_co = ", ".join(x for x in (("Vận đơn " + van_don) if van_don else "",
		("Hoá đơn mua " + purchase_invoice) if purchase_invoice else "",
		("Hoá đơn mua cả kỳ " + pi_ky) if pi_ky else "") if x)
	thieu = [ten for k, ten in can if not co[k]]
	if can:
		if not thieu:
			return "Đã nối", da_co
		if ky is not None and not pi_ky and len((ky or {}).get("nhieu") or []) > 1:
			return "Nhiều chứng từ", ((da_co + "; ") if da_co else "") + "nhiều hoá đơn mua cùng tổng tiền kỳ: " + \
				", ".join(ky["nhieu"][:5]) + "."
		return "Không thấy chứng từ", ((da_co + "; ") if da_co else "") + "thiếu " + ", ".join(thieu) + "."
	if van_don or purchase_invoice:
		return "Đã nối", da_co
	return "Chưa nối", ""


def xac_nhan_con_dung(kieu, dong, ung_vien):
	"""Dòng kế toán đã xác nhận còn đúng không. THUẦN. Codex #450: hoá đơn
	phải còn trong ứng viên hợp lệ (đã ghi sổ, chưa huỷ, đúng pháp nhân, trong
	khoảng ngày bán) và còn đúng số tiền đối chiếu như lúc xác nhận."""
	u = next((u for u in ung_vien if u["name"] == dong.get("sales_invoice")), None)
	return bool(u) and u["tien"] == tien_so_sanh(kieu, dong)
# Chỉ trạng thái này mới GIỮ giao dịch: giao dịch gợi ý của "Lệch tiền về" không
# chặn nguồn khác dùng đúng số tiền đó.
GIU_GIAO_DICH = "Đã thấy tiền về"


def ly_do_khong_tu_nhan(mau, co_tien_mat=False):
	"""Vì sao KHÔNG được tự nhận một giao dịch cùng số tiền. THUẦN. Rỗng là được.

	Codex #450: nguồn không có mẫu nội dung chuyển khoản (Shinhan) thì mọi
	tiền vào cùng số đều thành ứng viên; báo cáo GrabFood có đơn tiền mặt thì
	chưa rõ Grab có trừ tiền tài xế thu hộ khỏi tiền chuyển (đặc tả nguồn)."""
	if not MAU_TIEN_VE.get(nhom_tien_ve(mau), ""):
		return "nguồn này không có nội dung chuyển khoản để nhận diện"
	if co_tien_mat and mau.startswith("grab"):
		return "báo cáo có đơn tiền mặt, chưa rõ Grab có trừ khỏi tiền chuyển"
	return ""


def khop_ngan_hang(mau, can_ve, ngay_tu, ngay_den, giao_dich, da_dung=(), ly_do_tay=""):
	"""Tìm giao dịch tiền vào đúng số tiền vendor phải trả.

	giao_dich: [{name, ngay, tien, mo_ta}] tiền VÀO trong khoảng ngày máy chủ
	đã lọc. Chỉ đọc; không gạch, không giữ giao dịch (đối chiếu chứ không ghi
	sổ). Trả (trạng thái, [tên giao dịch], ghi chú).
	"""
	if can_ve <= 0:
		return "Không áp dụng", [], "Không có tiền vendor phải trả trong tệp này."
	mau_nd = MAU_TIEN_VE.get(nhom_tien_ve(mau), "")
	cung = [g for g in giao_dich if g["name"] not in da_dung and ngay_tu <= g["ngay"] <= ngay_den
		and (not mau_nd or re.search(mau_nd, (g["mo_ta"] or "").lower()))]
	dung = [g for g in cung if g["tien"] == can_ve]
	if len(dung) == 1:
		if ly_do_tay:
			return "Cần chọn tiền về", [], "Có giao dịch %s cùng %s đồng nhưng %s; kế toán xem sao kê rồi xác nhận." % (
				dung[0]["name"], _vn(can_ve), ly_do_tay)
		return "Đã thấy tiền về", [dung[0]["name"]], ""
	if len(dung) > 1:
		# Codex #450: nhiều giao dịch cùng số tiền thì KHÔNG tự chọn. Chọn bừa
		# (nhất là Shinhan không có mẫu nội dung) sẽ gắn nhầm tiền của khoản
		# khác và chặn nguồn đúng dùng giao dịch đó về sau.
		return "Cần chọn tiền về", [], "Có %s giao dịch cùng %s đồng (%s); máy không tự chọn. Xem sao kê để biết giao dịch nào của đợt này." % (
			len(dung), _vn(can_ve), ", ".join(g["name"] for g in dung[:10]))
	if cung and mau_nd:
		gan = min(cung, key=lambda g: abs(g["tien"] - can_ve))
		return "Lệch tiền về", [gan["name"]], "Gần nhất %s (%s), báo cáo %s (lệch %s)." % (
			gan["name"], _vn(gan["tien"]), _vn(can_ve), _vn(gan["tien"] - can_ve))
	return "Chưa thấy tiền về", [], "Chưa thấy giao dịch %s đồng từ %s đến %s." % (_vn(can_ve), ngay_tu, ngay_den)


# ------------------------------------------------------------ thẻ tín dụng

def ky_the(hien_tai, truoc):
	"""Dựng phương trình số dư thẻ: đầu kỳ + phát sinh + phí - đã trả = cuối kỳ.

	Sao kê Shinhan không in đầu kỳ và khoản đã trả. Đầu kỳ = "Đến hạn thanh
	toán" của sao kê kỳ trước; đã trả = đầu kỳ - "Khoản tiền chưa thanh toán
	tháng trước". Thiếu sao kê kỳ trước thì nói rõ, không đặt đầu kỳ bằng 0.
	"""
	t = hien_tai or {}
	if not truoc:
		return dict(du=False, ghi_chu="Chưa có sao kê kỳ trước; tải sao kê kỳ trước để dựng đầu kỳ.",
			cuoi_ky=t.get("den_han"))
	dau_ky = truoc.get("den_han") or 0
	da_tra = dau_ky - (t.get("chua_tra_truoc") or 0)
	cuoi = dau_ky + (t.get("spend") or 0) + (t.get("fees") or 0) + (t.get("phi_cham") or 0) - da_tra
	return dict(du=cuoi == t.get("den_han"), dau_ky=dau_ky, da_tra=da_tra, phat_sinh=t.get("spend") or 0,
		phi=(t.get("fees") or 0) + (t.get("phi_cham") or 0), cuoi_ky=t.get("den_han"),
		ghi_chu="" if cuoi == t.get("den_han") else "Phương trình số dư thẻ lệch %s." % _vn(cuoi - (t.get("den_han") or 0)))
