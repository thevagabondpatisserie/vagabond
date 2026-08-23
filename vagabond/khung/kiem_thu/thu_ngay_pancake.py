"""Kiểm thử phép đọc ngày Pancake (23/08/2026).

Ca kiểm này sinh ra từ một lỗi đã xảy ra HAI LẦN:

  19/08  75 vận đơn lùi một ngày vì `van_don.py` cắt thẳng chuỗi ISO.
  23/08  đơn trung thu giao 24/08 hiện ở tab 23/08 vì `mua_vu.py` có hàm
         đọc ngày RIÊNG và vẫn cắt thẳng.

Nên ở đây có hai loại ca: ca đọc đúng, và một HÀNG RÀO quét mã nguồn để tệp
thứ ba không thể lặng lẽ viết lại hàm đọc ngày lần nữa.
"""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__)))))
THU_MUC = os.path.join(GOC, "vagabond")


@ca("ngày Pancake: chuỗi UTC không khai múi giờ phải cộng bảy tiếng")
def _():
	from vagabond.ngay_pancake import ngay_tu_iso

	# Doi that, don 92194 hom 19/08: Pancake ghi 2026-08-18T17:00:00 cho mot
	# don giao ngay 19/08. Cat thang ra 18/08, lui mot ngay.
	la("đơn giao 19/08 Pancake ghi 18/08T17:00", ngay_tu_iso("2026-08-18T17:00:00"), "2026-08-19")
	# Ca cua anh Viet sang 23/08: don trung thu dat cho 24/08.
	la("đơn giao 24/08 Pancake ghi 23/08T17:00", ngay_tu_iso("2026-08-23T17:00:00"), "2026-08-24")
	# Giua ngay thi khong lech, va do chinh la ly do loi nay song lau: phan
	# lon don khong doi ngay nen nhin qua thay binh thuong.
	la("đơn giao giữa ngày không lệch", ngay_tu_iso("2026-08-24T03:00:00"), "2026-08-24")


@ca("ngày Pancake: chuỗi CÓ khai múi giờ thì tôn trọng phần khai")
def _():
	from vagabond.ngay_pancake import ngay_tu_iso

	la("khai +07:00", ngay_tu_iso("2026-08-24T00:00:00+07:00"), "2026-08-24")
	la("khai Z", ngay_tu_iso("2026-08-23T17:00:00Z"), "2026-08-24")
	la("khai -05:00", ngay_tu_iso("2026-08-23T12:00:00-05:00"), "2026-08-24")


@ca("ngày Pancake: mốc unix giây và mili giây đều đọc được")
def _():
	from vagabond.ngay_pancake import ngay_tu_iso

	# 1787504400 = 2026-08-23 17:00:00 UTC = 00:00 ngay 24/08 gio Viet Nam.
	la("mốc unix giây", ngay_tu_iso(1787504400), "2026-08-24")
	la("mốc unix mili giây", ngay_tu_iso(1787504400000), "2026-08-24")
	la("mốc unix gửi dạng chuỗi", ngay_tu_iso("1787504400"), "2026-08-24")


@ca("ngày Pancake: đọc không được thì trả RỖNG, không được đoán là hôm nay")
def _():
	from vagabond.ngay_pancake import ngay_giao, ngay_tu_iso

	# Bo qua rong la dieu quan trong nhat cua tep nay. Neu tra ve hom nay thi
	# moi don khong ro ngay se don het vao hom nay va bang bao thua hang.
	for x in ("", None, "rac", "24/08/2026", "0000-00-00", 0, False, True, 12):
		la("giá trị không đọc được: %r" % (x,), ngay_tu_iso(x), "")
	la("đơn không có trường ngày nào", ngay_giao({}), "")
	la("đơn có trường nhưng rỗng", ngay_giao({"estimate_delivery_date": ""}), "")


@ca("ngày Pancake: chuỗi chỉ có phần ngày thì lấy thẳng, không đoán bừa")
def _():
	from vagabond.ngay_pancake import ngay_tu_iso

	la("chỉ có ngày", ngay_tu_iso("2026-08-24"), "2026-08-24")
	la("ngày ngoài khoảng hợp lệ", ngay_tu_iso("1899-08-24"), "")


@ca("ngày Pancake: thứ tự trường, có estimate thì không đụng tới inserted")
def _():
	from vagabond.ngay_pancake import ngay_giao

	don = {
		"estimate_delivery_date": "2026-08-23T17:00:00",
		"inserted_at": "2026-08-20T04:00:00",
	}
	la("lấy ngày giao chứ không lấy ngày tạo", ngay_giao(don), "2026-08-24")
	# Khong co ngay giao thi moi lui ve ngay tao. Day la nuoc cuoi, va no lam
	# don khong khai ngay giao roi vao ngay tao chu khong bien mat.
	la("không có ngày giao thì lùi về ngày tạo",
		ngay_giao({"inserted_at": "2026-08-20T04:00:00"}), "2026-08-20")


@ca("ngày Pancake: van_don và mua_vu phải cho CÙNG một kết quả")
def _():
	# Day dung la cho da hong. Hai mo dun cung doc mot chuoi ma moi ben ra
	# mot ngay khac nhau, va khong ai biet vi khong ca kiem nao doi chieu hai
	# ben voi nhau.
	from vagabond import mua_vu, van_don

	for chuoi in ("2026-08-23T17:00:00", "2026-08-18T17:00:00",
			"2026-08-24T03:00:00", "2026-08-24T00:00:00+07:00"):
		a = van_don._ngay_tu_iso(chuoi)
		b = mua_vu._ngay_giao({"estimate_delivery_date": chuoi})
		la("hai module cùng đọc %s" % chuoi, b, a)


def _tep_nghiep_vu():
	for goc, _thu, tep in os.walk(THU_MUC):
		if os.sep + "kiem_thu" in goc or os.sep + "patches" in goc:
			continue
		for t in tep:
			if t.endswith(".py"):
				yield os.path.join(goc, t)


@ca("HÀNG RÀO: không tệp nào được tự cắt chuỗi ngày Pancake")
def _():
	"""Quét mã nguồn, chặn `[:10]` áp lên một trường ngày của Pancake.

	Hàng rào này KHÔNG chứng minh code đúng. Nó chỉ chặn đúng một cách sai
	đã gây lỗi hai lần: lấy trường ngày của Pancake rồi cắt mười ký tự đầu.

	ĐO THẬT 23/08/2026: dựng lại lỗi cũ nhưng TÁCH LÀM HAI DÒNG thì hàng rào
	này IM, chỉ ca "van_don và mua_vu phải cho cùng một kết quả" ở trên mới
	đỏ. Nghĩa là ca so hành vi mới là hàng rào thật, còn ca quét mã nguồn này
	chỉ là lớp chặn thêm cho trường hợp gõ một dòng. Đừng tin nó một mình.
	"""
	TRUONG = ("estimate_delivery_date", "time_delivery_at", "inserted_at")
	pham = []
	for d in _tep_nghiep_vu():
		if os.path.basename(d) == "ngay_pancake.py":
			continue
		src = io.open(d, encoding="utf-8").read()
		# Bo dong chu thich ra, vi tai lieu duoc phep NHAC den cach sai.
		than = "\n".join(
			dong for dong in src.split("\n")
			if not dong.lstrip().startswith("#")
		)
		for m in re.finditer(r"[^\n]*\[:10\][^\n]*", than):
			dong = m.group(0)
			if any(t in dong for t in TRUONG):
				pham.append("%s: %s" % (os.path.basename(d), dong.strip()[:90]))
	dung("không tệp nào cắt thẳng ngày Pancake:\n      " + ("\n      ".join(pham) or "sạch"),
		not pham)


@ca("HÀNG RÀO: hàng rào trên có thật sự cắn không")
def _():
	"""Tự thử lại chính hàng rào, vì một hàng rào không cắn còn tệ hơn không có.

	Ngày 23/08 đã có một ca kiểm so vị trí chuỗi mà không bắt được lỗi thật,
	nên từ nay hàng rào nào cũng phải tự chứng minh nó đỏ khi lỗi quay lại.
	"""
	TRUONG = ("estimate_delivery_date", "time_delivery_at", "inserted_at")
	xau = 'ngay = str(o.get("estimate_delivery_date"))[:10]'
	than = "\n".join(d for d in xau.split("\n") if not d.lstrip().startswith("#"))
	bat = [m.group(0) for m in re.finditer(r"[^\n]*\[:10\][^\n]*", than)
		if any(t in m.group(0) for t in TRUONG)]
	dung("dựng lại đúng dòng code cũ thì hàng rào đỏ", len(bat) == 1)
	sach = 'ngay = ngay_giao(o)'
	bat2 = [m.group(0) for m in re.finditer(r"[^\n]*\[:10\][^\n]*", sach)
		if any(t in m.group(0) for t in TRUONG)]
	dung("dòng code đúng thì hàng rào im", not bat2)
