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
	return "CẢNH BÁO: ngày %s còn %d hoá đơn đã ghi sổ mà chưa có hoá đơn điện tử, tổng %s đ." % (
		ngay, int(so_to), "{:,.0f}".format(float(tong_tien or 0)).replace(",", "."),
	)
