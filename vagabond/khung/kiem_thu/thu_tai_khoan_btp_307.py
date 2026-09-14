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
	# Anh Việt chốt 14/09 chiều: chỉ xoá giá trị MÁY điền; khác giá trị máy
	# sẽ điền là người điền tay, giữ.
	k = tkb.quyet_dinh("BTPB-1", 1, "", "BTP sơ cấp", "1551 - Thành phẩm - TV", CH)
	la("xoá chặng nhưng tài khoản do người điền tay: giữ", k["hanh_dong"], tkb.GIU)
	dung("ghi chú nói giữ điền tay", "điền tay" in k["ghi_chu"])
	k = tkb.quyet_dinh("BTPB-1", 1, "", "BTP sơ cấp", CH["tk_ton_btp_cap1"], TRONG)
	la("cấu hình trống thì máy chưa từng điền, giữ", k["hanh_dong"], tkb.GIU)


@ca("#307 ô điền tay: người đổi thì thắng dòng, không đổi thì dòng là sự thật")
def _o_tay():
	la("không đổi, đọc dòng", tkb.doc_o_tay(None, None, "1551 - TP"), ("1551 - TP", False))
	la("không đổi, cả hai rỗng", tkb.doc_o_tay("", None, None), (None, False))
	la("người điền mới", tkb.doc_o_tay("1561 - HH", None, None), ("1561 - HH", True))
	la("người sửa khác dòng", tkb.doc_o_tay("1561 - HH", "1551 - TP", "1551 - TP"), ("1561 - HH", True))
	la("người xoá trắng để bỏ", tkb.doc_o_tay("", "1551 - TP", "1551 - TP"), (None, True))
	la("ghi theo máy", tkb.gia_tri_cuoi(tkb.GHI, "1552 - BTP", "1551 - TP"), "1552 - BTP")
	la("xoá theo máy", tkb.gia_tri_cuoi(tkb.XOA, None, "1552 - BTP"), None)
	la("giữ tay", tkb.gia_tri_cuoi(tkb.GIU, "1552 - BTP", "1551 - TP"), "1551 - TP")
	la("ngoài phạm vi vẫn nhận điền tay", tkb.gia_tri_cuoi(tkb.BO_QUA, None, "1561 - HH"), "1561 - HH")
	la("nhắc thì không đụng", tkb.gia_tri_cuoi(tkb.NHAC, None, None), None)
	# Chuỗi thao tác kế toán: món NVL (ngoài phạm vi BTP) điền tay tài khoản.
	tk, doi = tkb.doc_o_tay("1561 - HH", None, None)
	k = tkb.quyet_dinh("NVLT-1", 1, "", "", tk, CH)
	la("NVL không thuộc luật chặng", k["hanh_dong"], tkb.BO_QUA)
	la("nhưng giá trị cuối là ô tay", tkb.gia_tri_cuoi(k["hanh_dong"], k["tai_khoan"], tk), "1561 - HH")
	# Đổi chặng cùng lúc điền tay: chặng đổi thì máy thắng.
	tk, doi = tkb.doc_o_tay("1561 - HH", "1551 - TP", "1551 - TP")
	k = tkb.quyet_dinh("BTPB-1", 1, "BTP sẵn sàng", "BTP sơ cấp", tk, CH)
	la("đổi chặng: máy ghi đè", tkb.gia_tri_cuoi(k["hanh_dong"], k["tai_khoan"], tk), CH["tk_ton_btp_cap2"])
	dung("ô Item có gương và nhãn", tkb.TRUONG_MOI["Item"][0]["fieldname"] == tkb.O_TAY
		and tkb.TRUONG_MOI["Item"][0]["insert_after"] == "custom_chang_btp"
		and tkb.TRUONG_MOI["Item"][0]["label"] == "Tài khoản tồn kho (điền tay)")
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


@ca("#316 validator cấu hình chặn tài khoản khác công ty qua cửa thật")
def _cong_ty_cau_hinh():
	from types import SimpleNamespace
	from unittest.mock import patch
	class LoiCauHinh(Exception):
		pass
	def bao(loi):
		raise LoiCauHinh(loi)
	ct_tai_khoan = ["Demo"]
	gia = SimpleNamespace(
		db=SimpleNamespace(
			get_single_value=lambda *a: "Vagabond",
			get_value=lambda *a, **k: dict(company=ct_tai_khoan[0], is_group=0,
				disabled=0, account_type="Stock", account_currency="VND")),
		throw=bao)
	with patch.object(tkb, "frappe", gia):
		loi = ""
		try:
			tkb.kiem_o_cau_hinh(CHUNG)
		except LoiCauHinh as e:
			loi = str(e)
		dung("cửa validate phải báo đúng hai công ty", "Demo" in loi and "Vagabond" in loi)
		ct_tai_khoan[0] = "Vagabond"
		tkb.kiem_o_cau_hinh(CHUNG)
		la("công ty đích không suy từ tài khoản", tkb.cong_ty_ap_dung(CHUNG), "Vagabond")


@ca('#307 lưu Settings gọi nạp nhóm và món đúng cấu hình mới, lỗi thì không đi tiếp')
def _luu_settings():
	from unittest.mock import patch
	from types import SimpleNamespace
	from vagabond import luoi_do_nhom as ldn
	class CauHinh(dict):
		def has_value_changed(self, o):
			return self.doi
	for doi, loi in ((True, 0), (False, 0), (True, 1)):
		doc = CauHinh({o: '1552-THU' for o in tkb.O_CAU_HINH.values()}); doc.doi = doi
		mon = SimpleNamespace(name='BTP-DA-KHAI')
		def bao(cau):
			raise ValueError(cau)
		with patch.object(tkb, 'cong_ty_ap_dung', return_value='CONG-TY-THU'), \
			patch.object(ldn, 'ap_dung', return_value={'dem': {'loi': loi}}) as nhom, \
			patch.object(tkb.frappe, 'get_all', return_value=[mon.name]) as ds, \
			patch.object(tkb.frappe, 'get_doc', return_value=mon), \
			patch.object(tkb.frappe, 'clear_cache', create=True), \
			patch.object(tkb.frappe, 'throw', side_effect=bao), \
			patch.object(tkb, 'ap_dung') as gan:
			bi_chan = False
			try:
				tkb.khi_luu_cau_hinh(doc)
			except ValueError:
				bi_chan = True
			la('lỗi nhóm phải chặn', bi_chan, bool(doi and loi))
			la('chỉ chạy khi đổi cấu hình', nhom.call_count, int(doi))
			if doi:
				la('nạp riêng BTP với giá trị mới', nhom.call_args.kwargs,
					{'chi_btp': True, 'cau_hinh': dict(doc)})
			if doi and not loi:
				la('chỉ món đã chọn chặng', ds.call_args.kwargs['filters'],
					{'is_stock_item': 1, 'custom_chang_btp': ['!=', '']})
				la('ghi món xuống DB', gan.call_args.args, (mon, dict(doc)))
				la('chế độ ghi', gan.call_args.kwargs, {'ghi_db': True})
			else:
				la('không ghi món khi không đổi hoặc nhóm lỗi', gan.call_count, 0)


@ca('#307 Settings mới cả hai ô trống không chặn cài app khi chưa có công ty')
def _settings_moi_trong():
	from unittest.mock import patch
	from types import SimpleNamespace
	doc = SimpleNamespace(has_value_changed=lambda o: True, get=lambda o: None)
	with patch.object(tkb, 'cong_ty_ap_dung', side_effect=AssertionError('không được hỏi công ty')) as cty:
		tkb.khi_luu_cau_hinh(doc)
		la('không có tài khoản để nạp', cty.call_count, 0)
