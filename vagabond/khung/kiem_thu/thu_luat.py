"""Kiem thu luat xep trang thai cua hai man mau.

Day la phan de sai nhat trong ca hai man: mot to xep nham chip la ke toan
cuoi ngay bam chip do se bo sot dung may to dang nghi nhat. Bai hoc that:
37 hoa don thay the hom 10/08 sinh ra tu mot kieu nham nhu vay.

Hai ham _xep_po va _xep_mua da tach thuan nen kiem duoc o day, khong can
site. Ca kiem thu goi THANG ham that trong mo dun nghiep vu, khong chep
lai luat - chep lai la kiem thu chinh ban chep chu khong kiem cai dang
chay.
"""

from vagabond import ke_toan, mua_hang
from vagabond.khung.kiem_thu.nen import HOM_NAY, ca, don_mua, hoa_don_mua, la

BC = {"hom_nay": HOM_NAY}


# ------------------------------------------------------- don mua hang

def _xp(**doi):
	return mua_hang._xep_po(don_mua(1, **doi), BC)


@ca("đơn mua: huỷ mềm xét trước mọi thứ khác")
def _():
	# Don da bo ma van hien "Cho nhan hang" thi thu mua ngoi doi mot chuyen
	# hang khong bao gio ve.
	la("cờ huỷ mềm thắng tất cả", _xp(vgb_huy=1, per_received=100, per_billed=100), "huy")
	la("huỷ mềm thắng cả trạng thái đóng",
		_xp(vgb_huy=1, status="Closed"), "huy")
	la("huỷ cứng docstatus 2", _xp(docstatus=2), "huy")


@ca("đơn mua: bản nháp không bao giờ bị xếp vào nhóm đang chờ hàng")
def _():
	la("nháp", _xp(docstatus=0), "nhap")


@ca("đơn mua: trễ hẹn tính đúng ở mốc ngày, không lệch một ngày")
def _():
	la("hẹn hôm qua là trễ", _xp(schedule_date="2026-08-14"), "tre_hen")
	la("hẹn đúng hôm nay CHƯA trễ", _xp(schedule_date="2026-08-15"), "cho_nhan")
	la("hẹn ngày mai chưa trễ", _xp(schedule_date="2026-08-16"), "cho_nhan")
	la("không có ngày hẹn thì không trễ", _xp(schedule_date=None), "cho_nhan")


@ca("đơn mua: nhận một phần khác chờ nhận, và chỉ khi chưa trễ")
def _():
	la("nhận 45%", _xp(per_received=45.5), "nhan_mot_phan")
	la("nhận 0% là chờ nhận", _xp(per_received=0), "cho_nhan")
	la("nhận một phần mà trễ hẹn thì trễ hẹn thắng",
		_xp(per_received=45.5, schedule_date="2026-08-01"), "tre_hen")


@ca("đơn mua: nhận đủ rồi thì chuyển sang đợi hoá đơn, xong khi đủ cả hai")
def _():
	la("nhận đủ chưa có hoá đơn", _xp(per_received=100, per_billed=0), "cho_hoa_don")
	la("nhận đủ có hoá đơn đủ", _xp(per_received=100, per_billed=100), "xong")
	# 99.99 la nguong co y: ERPNext hay tra ve 99.995 do lam tron tung dong.
	la("nhận 99.995 coi như đủ", _xp(per_received=99.995, per_billed=100), "xong")
	la("nhận 99.98 vẫn là chưa đủ", _xp(per_received=99.98), "nhan_mot_phan")


@ca("đơn mua: đơn đã đóng không đòi hàng nữa")
def _():
	la("Closed", _xp(status="Closed"), "dong")
	la("Completed", _xp(status="Completed"), "dong")


@ca("đơn mua: hàm cũ và hàm thuần cho cùng kết quả")
def _():
	# _nhom_po cu doc ngay he thong, _xep_po nhan ngay tu boi canh. Ngay he
	# thong trong ban gia lap dat dung bang HOM_NAY nen hai ben phai khop.
	for doi in [{}, {"vgb_huy": 1}, {"docstatus": 0}, {"per_received": 100},
			{"per_received": 100, "per_billed": 100}, {"status": "Closed"},
			{"schedule_date": "2026-08-01"}]:
		d = don_mua(1, **doi)
		la("cùng kết quả với %r" % (doi or "mặc định",),
			mua_hang._nhom_po(d), mua_hang._xep_po(d, BC))


@ca("đơn mua: số ngày trễ đếm đúng, và không âm")
def _():
	la("trễ 5 ngày", mua_hang._tre_ngay("2026-08-10", BC), 5)
	la("hẹn hôm nay là 0", mua_hang._tre_ngay("2026-08-15", BC), 0)
	la("hẹn tương lai là 0 chứ không âm", mua_hang._tre_ngay("2026-09-01", BC), 0)
	la("không có ngày hẹn là 0", mua_hang._tre_ngay(None, BC), 0)


# ------------------------------------------------------ hoa don mua vao

def _xm(**doi):
	return ke_toan._xep_mua(hoa_don_mua(1, **doi), BC)


@ca("hoá đơn mua: huỷ xét trước, rồi mới tới nháp")
def _():
	la("cờ huỷ mềm", _xm(vgb_huy=1, outstanding_amount=0), "huy")
	la("huỷ cứng", _xm(docstatus=2), "huy")
	la("nháp", _xm(docstatus=0), "nhap")


@ca("hoá đơn mua: trả xong xét trước quá hạn, khỏi đòi tiền đã trả")
def _():
	la("còn nợ 0 dù quá hạn là ĐÃ TRẢ",
		_xm(outstanding_amount=0, due_date="2026-01-01"), "da_tra")
	la("còn nợ âm cũng là đã trả", _xm(outstanding_amount=-5), "da_tra")


@ca("hoá đơn mua: quá hạn tính đúng ở mốc ngày")
def _():
	la("hạn hôm qua là quá hạn", _xm(due_date="2026-08-14"), "qua_han")
	la("hạn đúng hôm nay CHƯA quá hạn", _xm(due_date="2026-08-15"), "con_no")
	la("hạn ngày mai chưa quá hạn", _xm(due_date="2026-08-16"), "con_no")
	la("không có hạn thì chỉ là còn nợ", _xm(due_date=None), "con_no")


@ca("hoá đơn mua: hàm cũ và hàm thuần cho cùng kết quả")
def _():
	for doi in [{}, {"vgb_huy": 1}, {"docstatus": 0}, {"outstanding_amount": 0},
			{"due_date": "2026-01-01"}, {"due_date": "2026-08-15"}]:
		r = hoa_don_mua(1, **doi)
		la("cùng kết quả với %r" % (doi or "mặc định",),
			ke_toan._nhom_mua(r, HOM_NAY), ke_toan._xep_mua(r, BC))


@ca("hoá đơn mua: cờ đã sửa là cờ phụ, bắt đủ ba đường")
def _():
	la("bản sửa từ tờ khác", ke_toan._da_sua({"amended_from": "HDM-2026-00001"}), 1)
	la("đếm lần sửa", ke_toan._da_sua({"vgb_lan_sua": 2}), 1)
	la("tờ này đã có bản thay thế",
		ke_toan._da_sua({"name": "A"}, {"A"}), 1)
	la("tờ sạch", ke_toan._da_sua({"name": "B", "amended_from": ""}, {"A"}), 0)


@ca("hoá đơn mua: ô dẫn xuất tính đúng số ngày trễ và chỉ khi còn nợ")
def _():
	o = ke_toan._them_hdm(hoa_don_mua(1, due_date="2026-08-10"), BC)
	la("quá hạn 5 ngày", o["tre_ngay"], 5)
	o2 = ke_toan._them_hdm(
		hoa_don_mua(1, due_date="2026-08-10", outstanding_amount=0), BC)
	la("đã trả xong thì không tính trễ nữa", o2["tre_ngay"], 0)
	o3 = ke_toan._them_hdm(hoa_don_mua(1, due_date="2026-08-20"), BC)
	la("chưa tới hạn thì 0", o3["tre_ngay"], 0)
