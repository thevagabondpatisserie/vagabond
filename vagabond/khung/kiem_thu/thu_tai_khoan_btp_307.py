"""Ca kiểm THUẦN cho #307: ô Chặng bán thành phẩm quyết tài khoản tồn kho.

Giữ đúng đặc tả mục 3: điều kiện áp và không áp, xếp chặng sang ô cấu
hình, đổi chặng thì ghi đè, xoá chặng thì xoá, cấu hình trống thì chỉ
nhắc, và kế toán khai tay thì giữ khi chặng không đổi. Không cần site.
"""

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import tai_khoan_btp as tkb
from vagabond.kho_san_xuat import BTP_SO_CAP, BTP_SAN_SANG

CH = {"tk_ton_btp_cap1": "15521 - BTP cấp 1 - TV", "tk_ton_btp_cap2": "15522 - BTP cấp 2 - TV"}
CHUNG = {"tk_ton_btp_cap1": "1552 - BTP - TV", "tk_ton_btp_cap2": "1552 - BTP - TV"}
TRONG = {"tk_ton_btp_cap1": None, "tk_ton_btp_cap2": ""}


@ca("#307 điều kiện áp: theo tồn, tiền tố BTP, chặng sơ cấp hoặc sẵn sàng")
def _ap():
	la("BTPB sơ cấp", tkb.chang_ap_dung("BTPB-001", 1, "BTP sơ cấp"), BTP_SO_CAP)
	la("NBTP sẵn sàng", tkb.chang_ap_dung("NBTP-9", 1, "BTP sẵn sàng"), BTP_SAN_SANG)
	la("mã cũ dạng máy vẫn đọc", tkb.chang_ap_dung("BTPN-1", 1, "btp_san_sang"), BTP_SAN_SANG)
	la("chữ hoa thường, khoảng trắng", tkb.chang_ap_dung("BTPB-1", True, "  btp  SƠ CẤP "), BTP_SO_CAP)


@ca("#307 không áp: phantom, thành phẩm, nguyên liệu, không theo tồn, chưa khai")
def _khong_ap():
	la("BTP thành phần không áp dù theo tồn", tkb.chang_ap_dung("BTPB-1", 1, "BTP thành phần"), None)
	la("không theo tồn", tkb.chang_ap_dung("BTPB-1", 0, "BTP sơ cấp"), None)
	la("thành phẩm", tkb.chang_ap_dung("BAWC-1", 1, "BTP sơ cấp"), None)
	la("nguyên liệu", tkb.chang_ap_dung("NVLT-1", 1, "BTP sẵn sàng"), None)
	la("chưa khai chặng", tkb.chang_ap_dung("BTPB-1", 1, ""), None)
	la("chữ lạ không đoán", tkb.chang_ap_dung("BTPB-1", 1, "cấp 1"), None)


@ca("#307 mỗi cấp về đúng ô cấu hình, chung một tài khoản cũng chạy")
def _o():
	la("cấp 1", tkb.tai_khoan_theo_chang(BTP_SO_CAP, CH), CH["tk_ton_btp_cap1"])
	la("cấp 2", tkb.tai_khoan_theo_chang(BTP_SAN_SANG, CH), CH["tk_ton_btp_cap2"])
	la("1552 chung", tkb.tai_khoan_theo_chang(BTP_SAN_SANG, CHUNG), "1552 - BTP - TV")
	la("chặng lạ", tkb.tai_khoan_theo_chang("thanh_pham", CH), None)


@ca("#307 món mới hoặc chưa có tài khoản: ghi theo chặng")
def _ghi():
	k = tkb.quyet_dinh("BTPB-1", 1, "BTP sơ cấp", None, None, CH)
	la("hành động", k["hanh_dong"], tkb.GHI)
	la("tài khoản", k["tai_khoan"], CH["tk_ton_btp_cap1"])
	k = tkb.quyet_dinh("BTPB-1", 1, "BTP sơ cấp", "BTP sơ cấp", None, CH)
	la("patch nạp lần đầu cũng ghi", k["hanh_dong"], tkb.GHI)
	k = tkb.quyet_dinh("BTPB-1", 1, "BTP sơ cấp", "BTP sơ cấp", CH["tk_ton_btp_cap1"], CH)
	la("đã đúng thì bỏ qua (idempotent)", k["hanh_dong"], tkb.BO_QUA)


@ca("#307 đổi chặng: ghi đè tài khoản khai tay và có ghi chú")
def _doi():
	k = tkb.quyet_dinh("BTPB-1", 1, "BTP sẵn sàng", "BTP sơ cấp", "1551 - Thành phẩm - TV", CH)
	la("ghi đè", k["hanh_dong"], tkb.GHI)
	la("sang cấp 2", k["tai_khoan"], CH["tk_ton_btp_cap2"])
	dung("ghi chú nói ghi đè", "ghi đè" in k["ghi_chu"] and "1551" in k["ghi_chu"])


@ca("#307 chặng không đổi mà kế toán khai tay khác: giữ")
def _giu():
	k = tkb.quyet_dinh("BTPB-1", 1, "BTP sơ cấp", "BTP sơ cấp", "1551 - Thành phẩm - TV", CH)
	la("giữ", k["hanh_dong"], tkb.GIU)
	la("không đề xuất ghi", k["tai_khoan"], CH["tk_ton_btp_cap1"])


@ca("#307 xoá chặng hoặc đổi sang thành phần: xoá tài khoản khai riêng")
def _xoa():
	k = tkb.quyet_dinh("BTPB-1", 1, "", "BTP sơ cấp", CH["tk_ton_btp_cap1"], CH)
	la("xoá", k["hanh_dong"], tkb.XOA)
	k = tkb.quyet_dinh("BTPB-1", 1, "BTP thành phần", "BTP sẵn sàng", CH["tk_ton_btp_cap2"], CH)
	la("sang thành phần cũng xoá", k["hanh_dong"], tkb.XOA)
	k = tkb.quyet_dinh("BTPB-1", 1, "", "", "1551 - Thành phẩm - TV", CH)
	la("trước không áp thì không đụng tài khoản khai tay", k["hanh_dong"], tkb.BO_QUA)
	k = tkb.quyet_dinh("BAWC-1", 1, "", "BTP sơ cấp", "1551 - Thành phẩm - TV", CH)
	la("thành phẩm ngoài phạm vi", k["hanh_dong"], tkb.BO_QUA)


@ca("#307 cấu hình trống: chỉ nhắc, không ghi, không xoá")
def _trong():
	k = tkb.quyet_dinh("BTPB-1", 1, "BTP sơ cấp", None, None, TRONG)
	la("nhắc", k["hanh_dong"], tkb.NHAC)
	la("không tài khoản", k["tai_khoan"], None)
	dung("nói tên ô cần khai", "tk_ton_btp_cap1" in k["ghi_chu"])
	k = tkb.quyet_dinh("BTPB-1", 1, "BTP sẵn sàng", "BTP sẵn sàng", "1551 - TP", {})
	la("cấu hình rỗng cũng chỉ nhắc", k["hanh_dong"], tkb.NHAC)


@ca("#307 ô cấu hình chỉ nhận tài khoản kho chi tiết còn dùng, VND, đúng công ty")
def _loi_tk():
	tot = dict(company="Vagabond", is_group=0, disabled=0, account_type="Stock", account_currency="VND")
	la("tài khoản tốt", tkb.loi_tai_khoan(tot, "Vagabond"), "")
	dung("không tồn tại", tkb.loi_tai_khoan(None, "Vagabond"))
	dung("nhóm", tkb.loi_tai_khoan(dict(tot, is_group=1), "Vagabond"))
	dung("đã tắt", tkb.loi_tai_khoan(dict(tot, disabled=1), "Vagabond"))
	dung("không phải Stock", tkb.loi_tai_khoan(dict(tot, account_type="Payable"), "Vagabond"))
	dung("USD", tkb.loi_tai_khoan(dict(tot, account_currency="USD"), "Vagabond"))
	dung("khác công ty", tkb.loi_tai_khoan(dict(tot, company="Khác"), "Vagabond"))


@ca("#307 mặc định 1552 chỉ khi site có đúng một tài khoản con còn dùng")
def _mac_dinh():
	mot = [dict(name="1552 - BTP - TV", account_number="1552", is_group=0, disabled=0)]
	la("đúng một", tkb.chon_mac_dinh(mot), "1552 - BTP - TV")
	hai = mot + [dict(name="15521 - C1 - TV", account_number="15521", is_group=0, disabled=0)]
	la("đã tách thì để kế toán khai", tkb.chon_mac_dinh(hai), None)
	nhom = [dict(name="1552 - BTP - TV", account_number="1552", is_group=1, disabled=0),
		dict(name="15522 - C2 - TV", account_number="15522", is_group=0, disabled=1)]
	la("nhóm và tắt không tính", tkb.chon_mac_dinh(nhom), None)
	la("không có", tkb.chon_mac_dinh([]), None)


@ca("#307 hook đăng ký trên Item validate và không nới gac_tk_kho")
def _hook():
	import io
	import os
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	with io.open(os.path.join(goc, "hooks.py"), encoding="utf-8") as f:
		h = f.read()
	dung("hook Item validate", "vagabond.tai_khoan_btp.khi_luu_mon" in h)
	with io.open(os.path.join(goc, "gac_tk_kho.py"), encoding="utf-8") as f:
		g = f.read()
	dung("gac_tk_kho vẫn chặn 155", 'DAU_THANH_PHAM = "155"' in g)
	dung("gac_tk_kho không nhắc tới tai_khoan_btp", "tai_khoan_btp" not in g)
