# -*- coding: utf-8 -*-
"""Phép THUẦN cho việc phát hành hoá đơn điện tử theo lô và lưới đỡ mỗi giờ.

Không kéo Frappe, không kéo thư viện mạng. Mọi quyết định "được làm ngày
nào, gọi lô tiếp không, gộp kết quả ra sao" nằm ở đây để kiểm thử được
trên máy CI tay không. Phần chạm hệ (gọi Server Script m-invoice, ghi nhật
ký, gửi thư) nằm bên `ban_hang`.

Bối cảnh, 03/09/2026. Chuỗi cuối ngày 23h00 làm mọi việc trong MỘT lượt
chạy nền, mà hàng đợi mặc định của máy chủ cắt lượt chạy ở 300 giây. Kéo
Pancake mất 3 phút, ghi sổ 50 bill mất 1 phút, tới lúc phát hành thì chỉ
còn hơn một phút cho hơn 140 tờ, mỗi tờ hơn một giây. Ngày 01/09 bị cắt sau
90 tờ, ngày 02/09 sau 99 tờ. Phần đuôi 46 và 49 tờ nằm lại, không lớp nào
kêu: nhịp bù mỗi giờ bị một công tắc khác tắt từ 11/08, nhịp vét bỏ qua
bước phát hành, và nhật ký chuỗi bị nhịp vét ghi đè thành "xuất hoá đơn 0".

Bài học thứ hai, đắt hơn: m-invoice đánh số hoá đơn tăng liên tục theo
NGÀY LẬP. Đã có tờ mang ngày 02/09 thì không chen thêm tờ ngày 01/09 được
nữa (mã lỗi 296). Nên lưới đỡ phải chạy sớm, và chỉ được thử những ngày
còn mở cửa.
"""

import datetime


def _ngay(v):
	"""Nhận date, datetime hay chuỗi YYYY-MM-DD, trả về date. None giữ None."""
	if v is None or v == "":
		return None
	if isinstance(v, datetime.datetime):
		return v.date()
	if isinstance(v, datetime.date):
		return v
	return datetime.date.fromisoformat(str(v)[:10])


def ngay_duoc_bu(hom_nay, ngay_so_moi_nhat=None, chuoi_da_chay_hom_nay=False):
	"""Những ngày mà nhịp bù mỗi giờ ĐƯỢC phép gọi phát hành.

	Chỉ xét hôm qua và hôm nay, cũ hơn thì cửa đã đóng chắc chắn.

	- Ngày nào nhỏ hơn ngày của tờ mang số mới nhất thì bỏ: m-invoice sẽ
	  từ chối bằng mã 296, gọi chỉ tốn một vòng đăng nhập và một dòng lỗi.
	- Hôm nay chỉ bù SAU khi chuỗi cuối ngày đã chạy. Bill quầy theo thiết
	  kế nằm nháp cả ngày để khách quét QR điền công ty, chuỗi 23h mới ghi
	  sổ và xuất; lưới đỡ không được xuất trước giờ đó.
	- Hôm qua thì luôn được, vì chuỗi của hôm qua đã qua rồi.

	Trả về danh sách date, cũ trước mới sau.
	"""
	hom_nay = _ngay(hom_nay)
	moi_nhat = _ngay(ngay_so_moi_nhat)
	ra = []
	for d in (hom_nay - datetime.timedelta(days=1), hom_nay):
		if moi_nhat and d < moi_nhat:
			continue
		if d == hom_nay and not chuoi_da_chay_hom_nay:
			continue
		ra.append(d)
	return ra


def con_goi_lo_tiep(ket_qua_lo, so_lo_da_goi, toi_da_lo):
	"""Sau một lô phát hành, có gọi lô tiếp không.

	Dừng khi: không còn tờ nào để làm; lô vừa rồi không tạo được tờ nào
	(lỗi lặp lại thì gọi thêm chỉ lặp lại lỗi); hoặc đã đủ số lô tối đa
	(hàng rào cuối, phòng vòng lặp vô tận khi m-invoice trả về lạ).
	"""
	if so_lo_da_goi >= toi_da_lo:
		return False
	r = ket_qua_lo if isinstance(ket_qua_lo, dict) else {}
	tim = int(r.get("tim_thay") or 0)
	tao = int(r.get("tao_ok") or 0)
	if tim <= 0:
		return False
	if tao <= 0:
		return False
	return True


def con_to_chua_ra(ph, ky):
	"""Sau một lượt phát hành và ký, còn tờ nào chưa ra không. THUẦN.

	ph/ky là dict gom_lo/gom_ky, hoặc chuỗi "bỏ qua" khi công tắc tắt (khi
	đó không có gì để nói). Còn tờ tìm thấy mà chưa tạo, hoặc còn tờ cần ký
	mà chưa ký, là còn.
	"""
	con = False
	if isinstance(ph, dict):
		con = int(ph.get("tim_thay") or 0) > int(ph.get("tao_ok") or 0)
	if isinstance(ky, dict):
		con = con or int(ky.get("can_ky") or 0) > int(ky.get("da_ky") or 0)
	return con


def gom_lo(ds_ket_qua):
	"""Gộp kết quả nhiều lô phát hành thành một bộ số.

	`tim_thay` lấy của lô ĐẦU (số tờ đứng chờ lúc bắt đầu), vì các lô sau
	đếm lại phần còn lại nên cộng dồn sẽ đếm trùng. `tao_ok` cộng dồn. Lỗi
	gom lại, bỏ dòng trùng, giữ thứ tự.
	"""
	tim, tao, loi = 0, 0, []
	for i, r in enumerate(ds_ket_qua or []):
		if not isinstance(r, dict):
			continue
		if i == 0:
			tim = int(r.get("tim_thay") or 0)
		tao += int(r.get("tao_ok") or 0)
		for x in r.get("loi") or []:
			x = str(x)
			if x and x not in loi:
				loi.append(x)
	return {"tim_thay": tim, "tao_ok": tao, "loi": loi}


def gom_ky(ds_ket_qua):
	"""Gộp kết quả nhiều lô ký, cùng quy tắc với gom_lo."""
	can, ky, loi = 0, 0, []
	for i, r in enumerate(ds_ket_qua or []):
		if not isinstance(r, dict):
			continue
		if i == 0:
			can = int(r.get("can_ky") or 0)
		ky += int(r.get("da_ky") or 0)
		for x in r.get("loi") or []:
			x = str(x)
			if x and x not in loi:
				loi.append(x)
	return {"can_ky": can, "da_ky": ky, "loi": loi}


def con_ky_lo_tiep(ket_qua_lo, so_lo_da_goi, toi_da_lo):
	"""Sau một lô ký, có gọi lô tiếp không. Cùng luật với con_goi_lo_tiep."""
	if so_lo_da_goi >= toi_da_lo:
		return False
	r = ket_qua_lo if isinstance(ket_qua_lo, dict) else {}
	return int(r.get("can_ky") or 0) > 0 and int(r.get("da_ky") or 0) > 0


def dong_nhat_ky(ngay, gio, xong, ph, ky, so_loi=0):
	"""Câu nhật ký của chuỗi cuối ngày sau khi phát hành và ký xong.

	ph, ky là dict đã gộp (gom_lo, gom_ky) hoặc chuỗi "bỏ qua (...)".
	"""
	def _ph(v):
		if isinstance(v, dict):
			return "%d/%d tờ" % (int(v.get("tao_ok") or 0), int(v.get("tim_thay") or 0))
		return str(v or "không rõ")

	def _ky(v):
		if isinstance(v, dict):
			return "%d/%d tờ" % (int(v.get("da_ky") or 0), int(v.get("can_ky") or 0))
		return str(v or "không rõ")

	return "%s lúc %s: ghi sổ %d đơn. Phát hành %s. Ký %s.%s" % (
		ngay, gio, int(xong or 0), _ph(ph), _ky(ky),
		(" Còn %d đơn cần xem lại." % int(so_loi)) if so_loi else "",
	)


def vet_co_gi_de_ghi(xong, hddt, so_loi):
	"""Nhịp vét 5 phút có được ghi đè nhật ký không.

	Trước 03/09/2026 nhịp vét ghi đè mỗi 5 phút, kể cả khi không làm gì,
	nên câu "ghi sổ thêm 0 đơn, xuất hoá đơn 0" đè mất câu của chuỗi chính
	và màn Cài đặt nhìn như mọi thứ ổn trong khi 49 tờ chưa có hoá đơn.
	Không làm gì thì im, để câu của chuỗi chính còn đó cho người đọc.
	"""
	return bool(int(xong or 0) or int(hddt or 0) or int(so_loi or 0))


def cau_canh_bao_sot(ngay, so_to, tong_tien):
	"""Câu cảnh báo tờ đã ghi sổ mà chưa có hoá đơn điện tử, dùng chung cho
	nhật ký, thư kế toán và màn Cài đặt."""
	if tong_tien is None:
		return "CẢNH BÁO: ngày %s còn %d hoá đơn đã ghi sổ mà chưa có hoá đơn điện tử; chưa đọc được tổng tiền." % (ngay, int(so_to))
	return "CẢNH BÁO: ngày %s còn %d hoá đơn đã ghi sổ mà chưa có hoá đơn điện tử, tổng %s đ." % (
		ngay, int(so_to), "{:,.0f}".format(float(tong_tien or 0)).replace(",", "."),
	)


# ------------------------------------------------- xuat rai trong ngay (v395)
#
# Anh Viet 03/09/2026: "Xuat hoa don rai trong ngay thi anh dong y nhung can
# nang len 4 tieng, nhung don cuoi ngay thi don lai xuat 1 lan luc 23h."
#
# Bill quay chot xong van nam nhap mot quang de khach quet QR dien cong ty.
# Qua quang do thi ghi so va xuat luon, khong doi 23h. Nho vay luot 23h chi
# con phan duoi cua ngay, khong con hon 140 to dan vao mot luc.

GIO_CHO_TRUOC_KHI_XUAT = 4


def duoc_rai(bay_gio_hhmm, gio_chuoi_hhmm, chuoi_da_chay_hom_nay):
	"""Nhip rai co duoc chay luc nay khong.

	Khong chay tu gio chuoi cuoi ngay tro di (23h la viec cua chuoi), va
	khong chay nua khi chuoi hom nay da xong (phan con lai chuoi da lo).
	"""
	if chuoi_da_chay_hom_nay:
		return False
	return str(bay_gio_hhmm or "") < str(gio_chuoi_hhmm or "23:00")


def moc_bill_du_gio(bay_gio, so_gio=GIO_CHO_TRUOC_KHI_XUAT):
	"""Bill sua lan cuoi TRUOC moc nay la da cho du so_gio, duoc xuat.

	Lay theo "sua lan cuoi" chu khong theo "tao": khach quet QR dien cong ty
	hay thu ngan doi phuong thuc deu dat lai dong ho, de to hoa don luon
	mang thong tin moi nhat.
	"""
	return bay_gio - datetime.timedelta(hours=float(so_gio))


LY_DO_BO_QUA_RAI = {
	"chua_pt", "pt_sai_nguon", "thieu_ma", "thieu_khach_no",
	"tang_cho_duyet", "tang_tu_choi", "ngoai_chuoi",
}


def rai_bo_qua(ma_ly_do):
	"""Nhip rai co bo qua bill mang ma ly do nay khong.

	Bo qua nhung ly do can NGUOI xu (thieu phuong thuc, thieu khach no, cho
	duyet tang...). "chua_ve_tien" thi KHONG bo qua: cho phep ghi so tu hoi
	SePay, tien ve roi thi qua, chua ve thi bill nam lai cho luot sau.
	"""
	return str(ma_ly_do or "") in LY_DO_BO_QUA_RAI


# ------------------------------------------------- ghi sổ TỪNG ĐƠN (v602)
#
# Đêm 17/10/2026: chuỗi 23h ghi sổ và xuất xong 4 đơn lúc 23:03, rồi đứng yên
# gần một giờ mà vẫn giữ khoá đơn Sales, tới khi hàng đợi dài cắt ở 3600 giây.
# 62 đơn Sales đủ điều kiện và 28 bill quầy nằm nháp sang ngày hôm sau. Đây
# là lần thứ năm chuỗi này hỏng, lần nào cũng chung một gốc: MỘT lượt chạy làm
# lần lượt mọi đơn dưới MỘT khoá, một đơn kẹt là cả lô kẹt, mà không lớp nào
# kêu trước 23h55.
#
# Từ v602 mọi đường ghi sổ tự động (chuỗi 23h, nhịp vét, xuất rải trong ngày,
# kéo đơn treo) đều xếp MỖI ĐƠN thành một lượt chạy riêng có trần thời gian
# riêng. Một đơn kẹt chỉ kẹt chính nó: hàng đợi cắt lượt đó, hệ điều hành
# nhả khoá tệp, đơn sau chạy tiếp, nhịp vét 5 phút xếp lại đơn còn nháp.

JOB_GHI_SO = "vgb-ghi-so-%s"
# Trần cho MỘT đơn: chuẩn bị + ghi sổ + gọi m-invoice (30 giây) còn dư nhiều.
GIAY_MOI_DON = 180
# Chờ khoá dòng trong cơ sở dữ liệu tối đa chừng này rồi bỏ đơn đó, thay vì
# 50 giây mặc định nhân với cả trăm đơn.
GIAY_CHO_KHOA_DONG = 20
# Đơn Sales đã giao xong chừng này giờ thì xuất rải, không đợi 23h (anh Việt
# 18/10/2026: "Có thể xuất hoá đơn của sales rải trong ngày như D1 cũng được").
GIO_CHO_SALES_DA_GIAO = 2
VAN_DON_DA_GIAO = "Đã giao"
# Lượt chờ trước khi phát hành (Codex #488 vòng 2): đợi các lượt ghi sổ riêng
# xong tối đa chừng này giây, nghỉ GIAY_NGHI_CHO giữa hai lần đếm, và luôn
# dừng chờ trước MOC_CUOI_CHO để còn giờ phát hành, ký trước nửa đêm.
GIAY_CHO_LO = 1500
GIAY_NGHI_CHO = 15
MOC_CUOI_CHO = 23 * 3600 + 45 * 60


def job_ghi_so(ten):
	"""Mã lượt chạy ghi sổ của MỘT đơn. Cố định theo tên đơn để chống xếp trùng:
	đơn đang chờ hoặc đang chạy thì nhịp sau không xếp thêm."""
	return JOB_GHI_SO % str(ten or "").strip()


def chon_de_xep(rows, ly_do_cua):
	"""Tên các đơn được xếp ghi sổ. THUẦN.

	rows: các dòng đơn nháp (dict). ly_do_cua(row) -> mã lý do của
	ghi_so_dieu_kien. Bỏ những đơn cần NGƯỜI xử (rai_bo_qua): xếp chúng chỉ
	sinh lỗi lặp mỗi 5 phút. Giữ thứ tự, bỏ trùng."""
	ra, da = [], set()
	for r in rows or []:
		ten = str((r or {}).get("name") or "").strip()
		if not ten or ten in da:
			continue
		ma = ly_do_cua(r)
		# Tạm tính: khách chưa trả, không bao giờ ghi sổ được; xếp vào chỉ sinh
		# lượt bị từ chối lặp mỗi 5 phút (Codex #488 vòng 3).
		if rai_bo_qua(ma) or ma == "tam_tinh":
			continue
		da.add(ten)
		ra.append(ten)
	return ra


def con_duoc_ghi_so(si, ngay):
	"""Đơn này còn nên ghi sổ ở lượt chạy riêng không. THUẦN.

	Lượt chạy có thể tới muộn hơn lúc xếp: người khác đã ghi sổ tay, đã huỷ,
	đã chuyển thành tạm tính, hay đã kéo sang ngày khác. Khi đó bỏ, im lặng."""
	si = si or {}
	if int(si.get("docstatus") or 0) != 0:
		return False
	if int(si.get("vgb_huy") or 0) or int(si.get("vgb_tam_tinh") or 0):
		return False
	return str(si.get("posting_date") or "")[:10] == str(ngay or "")[:10]


def soan_bao_dong(ngay, gio, dem, tien, ten_ly_do):
	"""Tin cảnh báo còn đơn chưa ghi sổ. THUẦN. Không còn đơn thì trả None.

	dem, tien: mã lý do -> số đơn, số tiền. ten_ly_do: mã -> câu tiếng Việt.
	Đơn đủ điều kiện mà còn nháp là MÁY chưa làm xong, nói trước; đơn cần
	người xử nói sau, kèm việc phải làm."""
	tong = sum(int(v or 0) for v in (dem or {}).values())
	if not tong:
		return None
	tong_tien = sum(float(v or 0) for v in (tien or {}).values())
	tieu_de = "Ngày %s lúc %s còn %d đơn chưa ghi sổ, %s đ" % (
		_dmy(ngay), gio, tong, _tien_vn(tong_tien))
	dong = []
	san = int((dem or {}).get("san_sang") or 0)
	if san:
		dong.append("%d đơn đủ điều kiện mà máy chưa ghi sổ xong (%s đ). Mở Cài đặt, mục Cuối ngày, bấm Chạy ngay; "
			"vẫn còn thì báo kỹ thuật." % (san, _tien_vn((tien or {}).get("san_sang"))))
	for ma, so in sorted((dem or {}).items(), key=lambda x: -int(x[1] or 0)):
		if ma == "san_sang" or not so:
			continue
		dong.append("%d đơn: %s (%s đ)" % (int(so), (ten_ly_do or {}).get(ma, ma), _tien_vn((tien or {}).get(ma))))
	dong.append("Xem từng đơn ở Bán hàng, mục Đơn còn treo.")
	return tieu_de, dong


def _dmy(ngay):
	s = str(ngay or "")[:10]
	p = s.split("-")
	return "%s/%s/%s" % (p[2], p[1], p[0]) if len(p) == 3 else s


def _tien_vn(v):
	return "{:,.0f}".format(float(v or 0)).replace(",", ".")


def giay_cho_toi_da(giay_trong_ngay):
	"""Số giây tối đa lượt chờ được đợi, tính từ lúc bắt đầu. THUẦN.

	Không quá GIAY_CHO_LO, và không vượt MOC_CUOI_CHO: chạy tay lúc 23:40 thì
	chỉ chờ 5 phút, quá mốc thì không chờ, phát hành ngay phần đã ghi sổ."""
	con = MOC_CUOI_CHO - int(giay_trong_ngay or 0)
	return max(0, min(GIAY_CHO_LO, con))


def con_cho(ds, trang_thai, dang_chay):
	"""Các đơn của lô còn phải chờ. THUẦN.

	trang_thai: tên -> docstatus đọc lại từ cơ sở dữ liệu (thiếu tên là đơn đã
	bị xoá, không chờ). dang_chay(tên) -> True, False, hoặc None khi không
	hỏi được hàng đợi. Còn chờ khi đơn còn nháp và lượt của nó chưa chắc đã
	xong (True hoặc None). Lượt đã xong mà đơn còn nháp là lượt đó bỏ hay lỗi,
	chờ thêm vô ích."""
	ra = []
	for ten in ds or []:
		if ten not in (trang_thai or {}) or int(trang_thai[ten] or 0) != 0:
			continue
		if dang_chay(ten) is False:
			continue
		ra.append(ten)
	return ra


def ket_qua_lo(ds, trang_thai):
	"""(số đơn ĐÃ ghi sổ, danh sách đơn còn nháp) của lô sau khi chờ. THUẦN.
	Đếm theo cơ sở dữ liệu, không theo số đã xếp."""
	da = sum(1 for t in ds or [] if int((trang_thai or {}).get(t, -1)) == 1)
	con = [t for t in ds or [] if int((trang_thai or {}).get(t, -1)) == 0]
	return da, con
