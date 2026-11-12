# -*- coding: utf-8 -*-
"""v645 đợt 4 (anh Việt 08/11/2026): ưu đãi tự động qua Zalo theo hành trình khách.

Anh chốt:
  - Tin cảm ơn, báo điểm gửi khi đơn chuyển "đã nhận", không gửi sau 8PM.
  - Mỗi khách tối đa một tin ưu đãi mỗi tuần (trừ đền bù), giờ gửi 8:00 tới 20:00.
  - Gom các ưu đãi đã duyệt: đền bù ba mức, nhắc dịp năm sau, đơn thứ hai, khách
    giới thiệu bạn, mời khách vắng mốc hai, nhắc mã sắp hết hạn; báo cáo thứ Hai
    cho Marketing; thu ngân bấm mã có sẵn của khách thay vì gõ.

Mỗi ca chốt một đường lỗi có thật:
  - đơn giao đã nhận mà chờ ghi sổ cuối ngày mới cảm ơn (khách nhận trưa, tin sáng mai);
  - tin cảm ơn báo tổng điểm thiếu phần của đơn chưa ghi sổ;
  - một khách nhận dồn nhiều tin ưu đãi trong một tuần (khách phiền, báo xấu, Zalo hạ hạn mức);
  - nhóm đối chứng đổi phía mỗi lượt (so sánh hỏng);
  - nhắc hạn gửi mã đã dùng, hay phát thêm mã mới;
  - đền bù cấp hai mã cho một đơn, hay cấp cho khách lẻ;
  - nhắc dịp người sinh 29/02.
Phần chạm hệ chạy trên lớp Frappe giả, vá đúng lời gọi hàm thật dùng.
"""

import datetime as dt
import json
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()

from vagabond import den_bu as db  # noqa: E402
from vagabond import zalo_kich_ban as zk  # noqa: E402
from vagabond.khung.kiem_thu.thu_crm_614 import _nen_ban  # noqa: E402
from vagabond.khung.kiem_thu.thu_zalo_kich_ban_621 import BAY_GIO, D, Moi, _cau, _gd, _gop, _hs  # noqa: E402

D8 = dt.date
fr = zk.frappe


# ------------------------------------------------------------ phần thuần

@ca("v645 giờ gửi: không bao giờ sau 20:00 dù người cài gõ 22 (anh Việt: không gửi giờ khách đi ngủ)")
def _gio_20():
	la("trần 20", zk.GIO_TOI_DA, 20)
	la("gõ 8 tới 22 thành 8 tới 20", zk.gio_hop_le(8, 22), (8, 20))
	dung("19:59 trong giờ", zk.trong_gio(dt.datetime(2026, 11, 8, 19, 59), 8, 22))
	dung("20:00 ngoài giờ", not zk.trong_gio(dt.datetime(2026, 11, 8, 20, 0), 8, 22))


@ca("v645 đơn đã nhận: bill quầy phải ghi sổ; đơn giao nháp có mã Pancake là đã nhận; huỷ, trả hàng thì không")
def _da_nhan():
	dung("bill quầy đã ghi sổ", zk.hoa_don_con_nhan(1))
	dung("đơn giao nháp có mã Pancake", zk.hoa_don_con_nhan(0, "P1"))
	dung("nháp không mã Pancake (Sales nhập tay chưa ghi)", not zk.hoa_don_con_nhan(0, ""))
	dung("đã huỷ", not zk.hoa_don_con_nhan(2, "P1"))
	dung("huỷ mềm", not zk.hoa_don_con_nhan(1, "", huy=1))
	dung("trả hàng", not zk.hoa_don_con_nhan(1, "", tra=1))
	dung("điều kiện SQL cùng ý", "si.docstatus = 0 and ifnull(si.custom_pancake_id, '') != ''" in zk.DK_DA_NHAN
		and "is_return" in zk.DK_DA_NHAN and "vgb_huy" in zk.DK_DA_NHAN and "custom_nguon" in zk.DK_DA_NHAN)
	la("mã đơn khách nhận ra", (zk.ma_don_cho_khach("ACC-SINV-9", "97077"), zk.ma_don_cho_khach("HDB-1", "")), ("97077", "HDB-1"))


@ca("v645 nhóm đối chứng: cố định theo khách, đúng khoảng tỉ lệ, 0% không ai, trần 50%")
def _doi_chung():
	ds = ["KH-%05d" % i for i in range(4000)]
	trong = [k for k in ds if zk.trong_doi_chung(k, 10)]
	dung("khoảng 10%% (%d/4000)" % len(trong), 320 <= len(trong) <= 480)
	la("chạy lại cùng phía", [k for k in ds if zk.trong_doi_chung(k, 10)], trong)
	la("0% không ai", sum(1 for k in ds if zk.trong_doi_chung(k, 0)), 0)
	dung("gõ 90 chỉ tính 50", sum(1 for k in ds if zk.trong_doi_chung(k, 90)) < 2300)
	dung("khách rỗng không vào", not zk.trong_doi_chung("", 10))


@ca("v645 khoá sổ tin: giới thiệu và cảm ơn theo hoá đơn; đền bù mọi mức chung một khoá theo đơn gốc; nhắc hạn theo mã")
def _khoa():
	la("giới thiệu", zk.khoa_tin("gioi_thieu", hoa_don="HD1"), "gioi_thieu:HD1")
	la("đền bù nhẹ và nặng cùng khoá", (zk.khoa_tin("den_bu_nhe", hoa_don="HD1"), zk.khoa_tin("den_bu_nang", hoa_don="HD1")),
		("den_bu:HD1", "den_bu:HD1"))
	la("nhắc hạn", zk.khoa_tin("nhac_han", moc="VC9"), "nhac_han:VC9")
	la("đơn thứ hai một lần mỗi khách", zk.khoa_tin("don_thu_hai", "K1"), "don_thu_hai:K1:")


@ca("v645 nhắc dịp: ngày năm ngoái của ngày đích; 29/02 lùi về 28/02")
def _dip():
	la("thường", zk.ngay_dip_nam_truoc(D8(2026, 11, 18)), D8(2025, 11, 18))
	la("29/02/2028 về 28/02/2027", zk.ngay_dip_nam_truoc(D8(2028, 2, 29)), D8(2027, 2, 28))
	la("rỗng", zk.ngay_dip_nam_truoc(None), None)


@ca("v645 thứ tự ưu tiên: cảm ơn, đền bù, sinh nhật, nhắc dịp, đơn thứ hai, giới thiệu, mời quay lại, nhắc hạn; đền bù không tính trần tuần")
def _uu_tien():
	# v652: báo hoàn điểm đơn web ngay sau cảm ơn (tin giao dịch), nhắc điểm sắp hết hạn sau cùng.
	la("thứ tự", [k["ma"] for k in zk.KICH_BAN], ["sau_mua", "hoan_diem", "den_bu_nhe", "den_bu_vua", "den_bu_nang", "sinh_nhat", "nhac_dip",
		"don_thu_hai", "gioi_thieu", "quay_lai", "quay_lai_2", "nhac_han", "nhac_diem"])
	la("tính trần tuần", [k["ma"] for k in zk.KICH_BAN if k.get("tran_tuan")],
		["sinh_nhat", "nhac_dip", "don_thu_hai", "gioi_thieu", "quay_lai", "quay_lai_2", "nhac_han"])
	la("đo hiệu quả (có đối chứng)", zk.KB_DO_HIEU_QUA, ("don_thu_hai", "quay_lai", "quay_lai_2"))
	la("mã có sẵn", [k["ma"] for k in zk.KICH_BAN if k.get("kieu") == "co_san"], ["den_bu_nhe", "den_bu_vua", "den_bu_nang", "nhac_han"])
	for k in zk.KICH_BAN:
		dung("%s: tên và giải thích tiếng Việt, không mã máy" % k["ma"], k["ten"] and k["giai_thich"] and "_" not in k["ten"] + k["giai_thich"])
		dung("%s: quét theo ngày có hàm thật" % k["ma"], k["ma"] not in zk.QUET_THEO_NGAY or callable(getattr(zk, zk.QUET_THEO_NGAY[k["ma"]], None)))


@ca("v645 sẵn sàng: nhắc hạn không cần chương trình (dùng mã có sẵn); thẻ đền bù chưa chọn chương trình thì nói rõ")
def _san_sang():
	c = {"ma": "nhac_han", "bat": 1, "ma_mau": "700001", "mau_trang_thai": "ENABLE", "ctkm": ""}
	la("nhắc hạn sẵn sàng", zk.mau_san_sang(c), (True, ""))
	cd = dict(c, ma="den_bu_vua")
	with um.patch.object(zk, "_doc_ctkm", lambda ten: None):
		t = zk._the(cd, {}, D8(2026, 11, 8))
	la("đền bù chưa sẵn sàng", t["san_sang"], 0)
	dung("nói thiếu chương trình", "chương trình" in t["ly_do"])
	tq = zk._the({"ma": "quay_lai_2", "bat": 0, "doi_chung": None}, {}, None)
	la("thẻ có chữ ô số ngày và % đối chứng mặc định", (tq["nhan_ngay"], tq["nhan_nhac"], tq["do_hieu_qua"], tq["doi_chung"]),
		("KHÁCH CHƯA MUA BAO NHIÊU NGÀY THÌ GỬI", "KHÔNG GỬI LẠI TRONG (NGÀY)", 1, 10))


@ca("v645 báo cáo tuần: câu đọc được, có so nhóm đối chứng, thiếu dữ liệu thì nói chưa đủ, có lỗi thì chỉ chỗ xem")
def _bao_cao_cau():
	tin = zk.soan_bao_cao_tuan({"gui": {"sau_mua": 120, "sinh_nhat": 5, "den_bu_vua": 1}, "loi": 3, "ma_phat": 30, "ma_dung": 12,
		"giam": 1200000, "doanh_thu": 9800000, "hq": {"nhan": [9, 50], "dc": [1, 10]}}, D8(2026, 11, 9))
	dung("tiêu đề ngày", tin.startswith("Ưu đãi qua Zalo, 7 ngày tới 09/11/2026"))
	dung("tin theo tên kịch bản, theo thứ tự ưu tiên", "Cảm ơn khi khách nhận đơn, báo điểm 120; Đền bù sự cố mức vừa 1; Chúc mừng sinh nhật kèm voucher 5" in tin)
	dung("mã và tiền", "phát 30, khách đã dùng 12, giảm 1.200.000đ, doanh thu các đơn có mã 9.800.000đ" in tin)
	dung("so đối chứng", "quay lại mua 18% (9/50)" in tin and "không nhận tin 10% (1/10)" in tin)
	dung("lỗi chỉ chỗ xem", "Lỗi gửi: 3 tin. Xem Chăm sóc khách, Tin Zalo tự động." in tin)
	trong = zk.soan_bao_cao_tuan({}, D8(2026, 11, 9))
	dung("tuần trống", "chưa có tin nào" in trong and "chưa đủ dữ liệu" in trong and "Lỗi gửi" not in trong)
	dung("không gạch dài", "\u2014" not in tin and "\u2013" not in tin)


@ca("v645 báo cáo tuần: gửi qua kênh Zalo nội bộ đúng mã tin Marketing, khoá theo ngày; có trong lịch thứ Hai")
def _bao_cao_gui():
	from vagabond import kenh_zalo

	goi = []
	with um.patch.object(zk, "_bay_gio", lambda: dt.datetime(2026, 11, 9, 9, 7)), \
			um.patch.object(zk, "_so_bao_cao_tuan", lambda luc: {"gui": {"sau_mua": 2}}), \
			um.patch.object(kenh_zalo, "bao_hoac_ghi_loi", lambda *a, **k: goi.append((a, k)) or ["x"]), \
			um.patch.object(fr.db, "commit", lambda: None, create=True):
		zk.bao_cao_tuan()
	la("mã tin, khoá", (goi[0][1]["ma_tin"], goi[0][1]["khoa"]), ("mkt_bao_cao_uu_dai", "bao_cao_uu_dai:2026-11-09"))
	dung("tin là câu đã soạn", "Cảm ơn khi khách nhận đơn, báo điểm 2" in goi[0][1]["noi_dung"])
	la("mã tin thuộc Marketing", kenh_zalo.TIN["mkt_bao_cao_uu_dai"][0], "Marketing")
	import io
	import os
	src = io.open(os.path.join(os.path.dirname(zk.__file__), "hooks.py"), encoding="utf-8").read()
	dung("lịch 09:07 thứ Hai", '"7 9 * * 1", []).append("vagabond.zalo_kich_ban.bao_cao_tuan")' in src)


# ------------------------------------------------------------ gửi một dòng

class MoiV(Moi):
	"""Moi của v621 thêm bảng mã (Vagabond Voucher) cho kịch bản mã có sẵn."""

	def __init__(self, *a, voucher=None, **k):
		Moi.__init__(self, *a, **k)
		self.voucher = voucher or {}

	def get_value(self, dt_, n, cot=None, as_dict=False, **k):
		if dt_ == "Vagabond Voucher":
			return self.voucher.get(n)
		return Moi.get_value(self, dt_, n, cot, as_dict, **k)


@ca("v645 cảm ơn đơn giao vừa Đã nhận (hoá đơn nháp có mã Pancake): gửi ngay, mã đơn Pancake, điểm SẼ tích cộng vào tổng; nháp đã huỷ thì bỏ")
def _sau_mua_nhap():
	si = {"HD-1": D(docstatus=0, posting_date=D8(2026, 10, 29), posting_time="12:05:00", grand_total=450000,
			custom_pancake_id="P1", custom_pancake_display_id="97077"),
		"HD-2": D(docstatus=2, posting_date=D8(2026, 10, 29), posting_time="12:10:00", grand_total=90000, custom_pancake_id="P2")}
	rows = [D(name="T1", khach="K1", hoa_don="HD-1", diem=0, khoa="sau_mua:HD-1", trang_thai="Chờ gửi"),
		D(name="T2", khach="K1", hoa_don="HD-2", diem=0, khoa="sau_mua:HD-2", trang_thai="Chờ gửi")]
	m = MoiV(_cau("sau_mua"), rows, {"K1": _hs()}, [], si=si)
	m.diem = {"HD-1": (4500, False)}
	m.chay(zk.gui_hang_doi)
	la("gọi Zalo một lần", [g[3] for g in m.goi], ["sau_mua:HD-1"])
	g = m.goi[0][2]
	la("mã đơn, điểm, tổng điểm", (g["ma_hoa_don"], g["diem_tich"], g["tong_diem"]), ("97077", "4500", "29900"))
	la("trạng thái", m.tt(), {"T1": "Đã gửi", "T2": "Bỏ qua"})


@ca("v645 trần tuần: khách đã nhận tin ưu đãi 7 ngày qua thì mời quay lại bị bỏ, không phát mã, không gọi Zalo; đền bù vẫn gửi")
def _tran_tuan():
	rows = [D(name="T1", khach="K1", khoa="quay_lai:K1:2026-08-01", trang_thai="Chờ gửi")]
	m = MoiV(_cau("quay_lai", ctkm="KM-SN"), rows, {"K1": _hs()}, [])
	m.km_tuan = {"K1"}
	m.sql_tra = [[None]]
	m.chay(zk.gui_hang_doi)
	la("bỏ", m.tt(), {"T1": "Bỏ qua"})
	la("không phát mã, không gọi", (m.voucher_moi(), m.goi), ([], []))
	ly = [v for d, n, v in m.sv if n == "T1" and v.get("trang_thai") == "Bỏ qua"][0]["loi"]
	dung("lý do nói trần tuần", "tối đa một tin mỗi tuần" in ly)
	rows = [D(name="T2", khach="K1", khoa="den_bu:HD9", trang_thai="Chờ gửi", voucher="DB1")]
	m = MoiV(_cau("den_bu_vua", ctkm="KM-SN", ten_uu_dai="Giảm 15% đơn sau"), rows, {"K1": _hs()}, [],
		voucher={"DB1": D(ma="DB1", ctkm="KM-SN", trang_thai="Chua dung", han_dung=D8(2026, 12, 28), danh_cho="K1")})
	m.km_tuan = {"K1"}
	m.chay(zk.gui_hang_doi)
	la("đền bù gửi dù đã nhận tin tuần này", m.tt(), {"T2": "Đã gửi"})
	la("gửi đúng mã đã cấp, chữ ưu đãi theo mức", (m.goi[0][2]["ma_voucher"], m.goi[0][2]["ten_uu_dai"]), ("DB1", "Giảm 15% đơn sau"))
	la("không phát mã mới", m.voucher_moi(), [])


@ca("v645 nhóm đối chứng: khách trong nhóm bị bỏ có ghi lý do đối chứng, khách ngoài nhóm vẫn nhận; doi_chung 0 thì ai cũng nhận")
def _doi_chung_gui():
	ds = ["KH-%05d" % i for i in range(400)]
	trong = next(k for k in ds if zk.trong_doi_chung(k, 10))
	ngoai = next(k for k in ds if not zk.trong_doi_chung(k, 10))
	rows = [D(name="T1", khach=trong, khoa="don_thu_hai:%s:" % trong, trang_thai="Chờ gửi"),
		D(name="T2", khach=ngoai, khoa="don_thu_hai:%s:" % ngoai, trang_thai="Chờ gửi")]
	m = MoiV(_cau("don_thu_hai", ctkm="KM-SN", doi_chung=10), rows, {trong: _hs(), ngoai: _hs(ten="Bình")}, [])
	m.chay(zk.gui_hang_doi)
	la("phía", m.tt(), {"T1": "Bỏ qua", "T2": "Đã gửi"})
	ly = [v for d, n, v in m.sv if n == "T1" and v.get("trang_thai") == "Bỏ qua"][0]["loi"]
	dung("lý do bắt đầu bằng nhóm đối chứng (báo cáo đếm theo)", ly.startswith(zk.LY_DO_DOI_CHUNG))
	la("chỉ một mã", m.voucher_moi(), ["VC1"])
	rows = [D(name="T3", khach=trong, khoa="don_thu_hai:%s:" % trong, trang_thai="Chờ gửi")]
	m = MoiV(_cau("don_thu_hai", ctkm="KM-SN", doi_chung=0), rows, {trong: _hs()}, [])
	m.chay(zk.gui_hang_doi)
	la("0% thì gửi", m.tt(), {"T3": "Đã gửi"})


@ca("v645 Codex 548 c02f2be: nhóm đối chứng chỉ chia SAU các điều kiện loại chung (đối tượng chương trình, trần tuần); khách không đủ điều kiện không bao giờ bị ghi là đối chứng")
def _doi_chung_sau_dieu_kien():
	# Tái hiện Codex: CTKM chỉ định riêng K-OK; hai khách ngoài danh sách, một
	# rơi vào nhóm đối chứng, một không. Trước bản sửa người thứ nhất bị ghi
	# "Nhóm đối chứng" (vào mẫu số đối chứng của báo cáo) còn người thứ hai bị
	# loại vì đối tượng: hai nhóm không cùng phạm vi.
	ds = ["KH-%05d" % i for i in range(400)]
	trong = [k for k in ds if zk.trong_doi_chung(k, 10)]
	ngoai = next(k for k in ds if not zk.trong_doi_chung(k, 10))
	dc_sai, dc_tuan, dc_dung = trong[0], trong[1], trong[2]
	km = D(name="KM-SN", ten="Quà đơn thứ hai", cach_ma="Ma dung mot lan", bat=1, kieu_giam="Phan tram", gia_tri=10,
		hd_toi_thieu=0, doi_tuong="Khach chi dinh")
	chi_dinh = {dc_tuan, dc_dung}
	rows = [D(name="T%d" % i, khach=k, khoa="don_thu_hai:%s:" % k, trang_thai="Chờ gửi")
		for i, k in enumerate([dc_sai, ngoai, dc_tuan, dc_dung], 1)]
	m = MoiV(_cau("don_thu_hai", ctkm="KM-SN", doi_chung=10), rows, {k: _hs() for k in (dc_sai, ngoai, dc_tuan, dc_dung)}, [], ctkm=km)
	m.km_tuan = {dc_tuan}

	def co(dt_, dk=None, *a, **k):
		return isinstance(dk, dict) and dt_ == "Vagabond CTKM Khach" and dk.get("khach") in chi_dinh
	with um.patch.object(fr.db, "exists", co):
		m.chay(zk.gui_hang_doi)
	ly = {n: v.get("loi") for d, n, v in m.sv if v.get("trang_thai") == "Bỏ qua"}
	dung("khách ngoài đối tượng trong nhóm đối chứng: bỏ vì đối tượng, KHÔNG ghi đối chứng",
		"đối tượng" in ly.get("T1", "") and not ly.get("T1", "").startswith(zk.LY_DO_DOI_CHUNG))
	dung("khách ngoài đối tượng ngoài nhóm đối chứng: bỏ vì đối tượng", "đối tượng" in ly.get("T2", ""))
	dung("khách đã nhận tin tuần này trong nhóm đối chứng: bỏ vì trần tuần, KHÔNG ghi đối chứng",
		"mỗi tuần" in ly.get("T3", "") and not ly.get("T3", "").startswith(zk.LY_DO_DOI_CHUNG))
	dung("khách đủ điều kiện trong nhóm đối chứng: ghi đối chứng", ly.get("T4", "").startswith(zk.LY_DO_DOI_CHUNG))
	la("không phát mã, không gọi Zalo", (m.voucher_moi(), m.goi), ([], []))


@ca("v645 đơn thứ hai: khách đã mua đơn thứ hai trước giờ gửi thì bỏ; nhắc dịp: khách vừa mua lại thì bỏ")
def _kiem_lai():
	rows = [D(name="T1", khach="K1", khoa="don_thu_hai:K1:", trang_thai="Chờ gửi")]
	m = MoiV(_cau("don_thu_hai", ctkm="KM-SN"), rows, {"K1": _hs()}, [])
	m.so_don = {"K1": 2}
	m.chay(zk.gui_hang_doi)
	la("bỏ đơn thứ hai", (m.tt(), m.goi, m.voucher_moi()), ({"T1": "Bỏ qua"}, [], []))
	rows = [D(name="T2", khach="K1", khoa="nhac_dip:K1:2026-11-08", trang_thai="Chờ gửi")]
	m = MoiV(_cau("nhac_dip", ctkm="KM-SN"), rows, {"K1": _hs()}, [])
	m.mua_gan = {"K1"}
	m.chay(zk.gui_hang_doi)
	la("bỏ nhắc dịp", (m.tt(), m.goi), ({"T2": "Bỏ qua"}, []))


@ca("v645 nhắc hạn: gửi đúng mã khách đang giữ, ưu đãi lấy từ chương trình của mã (không theo ô chữ của kịch bản); mã đã dùng hay hết hạn thì bỏ; không phát mã mới")
def _nhac_han():
	vc = {"V1": D(ma="V1", ctkm="KM-SN", trang_thai="Chua dung", han_dung=D8(2026, 11, 1), danh_cho="K1"),
		"V2": D(ma="V2", ctkm="KM-SN", trang_thai="Da dung", han_dung=D8(2026, 11, 1), danh_cho="K2"),
		"V3": D(ma="V3", ctkm="KM-SN", trang_thai="Chua dung", han_dung=D8(2026, 10, 28), danh_cho="K3")}
	rows = [D(name="T%d" % i, khach="K%d" % i, khoa="nhac_han:V%d" % i, voucher="V%d" % i, trang_thai="Chờ gửi") for i in (1, 2, 3)]
	m = MoiV(_cau("nhac_han", ctkm="", ten_uu_dai="CHỮ SAI"), rows, {"K1": _hs(), "K2": _hs(), "K3": _hs()}, [], voucher=vc)
	m.chay(zk.gui_hang_doi)
	la("trạng thái", m.tt(), {"T1": "Đã gửi", "T2": "Bỏ qua", "T3": "Bỏ qua"})
	la("đúng mã, hạn của mã", (m.goi[0][2]["ma_voucher"], m.goi[0][2]["han_dung"]), ("V1", "01/11/2026"))
	dung("ưu đãi theo chương trình của mã", m.goi[0][2]["ten_uu_dai"] != "CHỮ SAI" and "10%" in m.goi[0][2]["ten_uu_dai"])
	la("không phát mã mới", m.voucher_moi(), [])


@ca("v645 giờ: dữ liệu cũ đặt giờ đóng 22 thì 20:30 vẫn không gửi, dòng để chờ sáng mai")
def _sau_20():
	rows = [D(name="T1", khach="K1", hoa_don="HD-1", diem=1, khoa="sau_mua:HD-1", trang_thai="Chờ gửi")]
	m = MoiV(_cau("sau_mua", gio_den=22), rows, {"K1": _hs()}, [], si={"HD-1": D(docstatus=1, posting_date=D8(2026, 10, 29), grand_total=1)})
	m.dong_ho = lambda: dt.datetime(2026, 10, 29, 20, 30)
	kq = m.chay(zk.gui_hang_doi)
	la("không gọi Zalo", m.goi, [])
	la("dòng vẫn chờ", m.tt(), {"T1": "Chờ gửi"})
	la("tóm tắt", kq.get("sau_mua"), "Ngoài giờ gửi.")


# ------------------------------------------------------------ quét

def _doc_gia(chen):
	class Doc(D):
		def insert(self, **k):
			chen.append(dict(self))
			return self
	return lambda d, *a, **k: Doc(d)


@ca("v645 quét giới thiệu: số gõ ở ô Mã giới thiệu là của một khách khác thì người đó nhận dòng chờ; tự giới thiệu, khách lẻ, số lạ bỏ; quá 5 lượt tháng thì ghi Bỏ qua")
def _quet_gt():
	from vagabond import nhap_khach

	chen, co = [], set()
	don = [D(name="HD-1", khach="K1"), D(name="HD-2", khach="K2"), D(name="HD-3", khach="K3"), D(name="HD-4", khach="K4"), D(name="HD-5", khach="K5")]
	sdt = {"HD-1": "0901000009", "HD-2": "0902000002", "HD-3": "0909999999", "HD-4": "0901000009", "HD-5": "0905555555"}
	ai = {"0901000009": "K9", "0902000002": "K2", "0905555555": "Khách bán lẻ"}
	dem = {"K9": 0}

	def count(dt_, f=None, *a, **k):
		return dem.get((f or {}).get("khach"), 0)

	def ghi(d, *a, **k):
		class Doc(D):
			def insert(self, **kk):
				chen.append(dict(self))
				co.add(self["khoa"])
				if self.get("trang_thai") == zk.TT_CHO:
					dem[self["khach"]] = dem.get(self["khach"], 0) + 1
				return self
		return Doc(d)
	with um.patch.object(zk, "_tu_luc", lambda ma: BAY_GIO), um.patch.object(zk, "_bay_gio", lambda: BAY_GIO), \
			um.patch.object(zk, "_don_da_nhan", lambda tu, ma, *a, **k: list(don)), \
			um.patch.object(zk, "_so_dien_thoai_gioi_thieu", lambda hd: sdt.get(hd, "")), \
			um.patch.object(nhap_khach, "tim_theo_sdt", lambda s: ai.get(s, "")), \
			um.patch.object(zk, "GIOI_THIEU_TOI_DA_THANG", 1), um.patch.object(zk, "_la_khach_gop", _gop), \
			um.patch.object(fr.db, "count", count, create=True), \
			um.patch.object(fr.db, "exists", lambda dt_, f=None, *a, **k: (f or {}).get("khoa") in co), \
			um.patch.object(fr, "get_doc", ghi):
		n = zk.quet_gioi_thieu()
	la("số dòng", n, 2)
	la("dòng", [(x["khoa"], x["khach"], x["trang_thai"]) for x in chen],
		[("gioi_thieu:HD-1", "K9", "Chờ gửi"), ("gioi_thieu:HD-4", "K9", "Bỏ qua")])
	dung("lý do trần tháng", "đủ 1 mã giới thiệu trong tháng" in chen[1]["loi"])
	dung("khách lẻ không nhận", all(x["khach"] != "Khách bán lẻ" for x in chen))


@ca("v645 quét nhắc hạn, nhắc dịp, đơn thứ hai: đúng ngày, đúng điều kiện, khoá đúng")
def _quet_ngay():
	chen = []
	with um.patch.object(zk, "_cau_hinh", lambda ma: {"ma": ma, "bat": 1, "so_ngay": 3}), \
			um.patch.object(fr.db, "exists", lambda *a, **k: False), um.patch.object(fr, "get_doc", _doc_gia(chen)), \
			um.patch.object(fr, "get_all", lambda dt_, filters=None, **k: [D(name="V1", danh_cho="K1")] if filters.get("han_dung") == D8(2026, 11, 11) else []):
		la("nhắc hạn một dòng", zk.quet_nhac_han(D8(2026, 11, 8)), 1)
	la("dòng nhắc hạn", [(x["khoa"], x["khach"], x["voucher"]) for x in chen], [("nhac_han:V1", "K1", "V1")])
	cau = []

	def sql(q, ts=None, *a, **k):
		cau.append((q, ts))
		return [D(khach="K7", lan_cuoi=D8(2026, 11, 5))]
	chen = []
	with um.patch.object(zk, "_cau_hinh", lambda ma: {"ma": ma, "bat": 1, "so_ngay": 10 if ma == "nhac_dip" else 3}), \
			um.patch.object(fr.db, "sql", sql), um.patch.object(fr.db, "exists", lambda *a, **k: False), \
			um.patch.object(fr, "get_doc", _doc_gia(chen)):
		zk.quet_nhac_dip(D8(2028, 2, 19))
		zk.quet_don_thu_hai(D8(2026, 11, 8))
	q, ts = cau[0]
	la("nhắc dịp: ngày năm ngoái của 29/02/2028 là 28/02/2027, từ 300.000đ", ts[:2], (D8(2027, 2, 28), zk.NGUONG_DIP))
	dung("chỉ đơn giao, đã đồng ý, chưa mua lại gần đây", "custom_pancake_id" in q and "dy_zalo" in q and "h.lan_cuoi <" in q)
	q2, ts2 = cau[1]
	dung("đơn thứ hai: đúng một đơn, đã đồng ý", "so_don, 0) = 1" in q2 and "dy_zalo" in q2)
	la("cửa sổ ngày", ts2, (D8(2026, 11, 3), D8(2026, 11, 5)))
	la("khoá", [x["khoa"] for x in chen], ["nhac_dip:K7:2028-02-29", "don_thu_hai:K7:"])


# ------------------------------------------------------------ đền bù

@ca("v645 đền bù phép thuần: ba mức có tên và giải thích; lý do lạ thành Khác; Khác phải có ghi chú; che số")
def _db_thuan():
	la("ba mức", db.MA_MUC, ("nhe", "vua", "nang"))
	for m in db.MUC:
		dung("mức %s có tên, giải thích" % m[0], m[1] and m[2])
	la("kịch bản của mức", (db.kich_ban_cua("vua"), db.kich_ban_cua("x")), ("den_bu_vua", ""))
	dung("kịch bản có thật", all(zk.kich_ban(db.kich_ban_cua(m)) for m in db.MA_MUC))
	la("lý do có ghi chú", db.chuan_ly_do("Sai trang trí", "  chữ  bị lệch "), ("Sai trang trí: chữ bị lệch", ""))
	la("lý do lạ có ghi chú", db.chuan_ly_do("abc", "x")[0], "Khác: x")
	dung("Khác trống thì lỗi", db.chuan_ly_do("Khác", " ")[0] is None)
	la("che số", db.che_sdt("84901486556"), "849***6556")


def _db_moi(dong_y=True, khach="K1", da_cap=None, ctkm="KM-DB", mau_duyet=True):
	from vagabond import khuyen_mai

	chen, co = [], set(da_cap or [])
	hd = D(name="ACC-SINV-1", customer=khach, customer_name="Lan Anh", posting_date=D8(2026, 11, 8), grand_total=450000,
		docstatus=1, is_return=0, custom_pancake_display_id="97077", custom_pancake_id="P1")
	km = D(name="KM-DB", ten="Đền bù vừa", cach_ma="Ma dung mot lan", bat=1, kieu_giam="Phan tram", gia_tri=15) if ctkm else None
	c = _cau("den_bu_vua", ctkm=ctkm, ma_mau="700002" if mau_duyet else "", han_ngay=60)

	def ghi(d, *a, **k):
		class Doc(D):
			def insert(self, **kk):
				chen.append(dict(self))
				if self.get("khoa"):
					co.add(self["khoa"])
				return self
		return Doc(d)
	vas = [um.patch.object(khuyen_mai, "_kiem_quyen_sua", lambda: None), um.patch.object(zk, "_dam_bao", lambda: None),
		um.patch.object(db, "_hoa_don", lambda q: hd if q in ("97077", "ACC-SINV-1") else None),
		um.patch.object(db, "_ma_da_cap", lambda h: {"voucher": "OLD1", "kich_ban": "den_bu_nhe"} if ("den_bu:" + h) in co else None),
		um.patch.object(zk, "_cau_hinh", lambda ma: dict(c, ma=ma)), um.patch.object(zk, "_doc_ctkm", lambda ten: km if ten else None),
		um.patch.object(zk, "_ho_so", lambda kh: _hs(dong_y=dong_y)), um.patch.object(zk, "_bay_gio", lambda: dt.datetime(2026, 11, 8, 10, 0)),
		um.patch.object(zk, "_sinh_ma", lambda: "DB7788"), um.patch.object(zk, "_la_khach_gop", _gop),
		um.patch.object(fr.db, "sql", lambda *a, **k: []), um.patch.object(fr.db, "commit", lambda: None, create=True),
		um.patch.object(fr.db, "exists", lambda dt_, f=None, *a, **k: (f or {}).get("khoa") in co), um.patch.object(fr, "get_doc", ghi),
		um.patch.object(fr.session, "user", "quanly@vagabond.vn", create=True)]
	return chen, vas


def _voi(vas, ham):
	import contextlib

	with contextlib.ExitStack() as st:
		for v in vas:
			st.enter_context(v)
		return ham()


@ca("v645 cấp mã đền bù: một mã dùng một lần chỉ cho khách đó, hạn 60 ngày, ghi mức, lý do, đơn gốc, người cấp; xếp gửi Zalo khi khách đã đồng ý và mẫu sẵn sàng")
def _db_cap():
	chen, vas = _db_moi()
	kq = _voi(vas, lambda: db.cap_ma("97077", "vua", "Sai trang trí", "chữ lệch"))
	la("kết quả", (kq["ma"], kq["han"], kq["zalo"]), ("DB7788", "07/01/2027", 1))
	vc = [x for x in chen if x.get("doctype") == "Vagabond Voucher"][0]
	la("mã chỉ cho khách", (vc["danh_cho"], vc["chi_nguoi_nhan"], vc["trang_thai"], str(vc["han_dung"])), ("K1", 1, "Chua dung", "2027-01-07"))
	dung("ghi đủ vết", all(x in vc["ghi_chu"] for x in ("mức Vừa", "Sai trang trí: chữ lệch", "Đơn gốc 97077", "quanly@vagabond.vn")))
	tin = [x for x in chen if x.get("doctype") == zk.DT_TIN][0]
	la("dòng tin", (tin["kich_ban"], tin["khoa"], tin["voucher"], tin["trang_thai"]), ("den_bu_vua", "den_bu:ACC-SINV-1", "DB7788", "Chờ gửi"))


@ca("v645 cấp mã đền bù: khách chưa đồng ý hay mẫu chưa sẵn sàng thì vẫn cấp mã, dòng tin Bỏ qua kèm câu bảo quản lý đọc mã")
def _db_khong_zalo():
	chen, vas = _db_moi(dong_y=False)
	kq = _voi(vas, lambda: db.cap_ma("97077", "vua", "Giao trễ"))
	la("có mã, không Zalo", (kq["ma"], kq["zalo"]), ("DB7788", 0))
	tin = [x for x in chen if x.get("doctype") == zk.DT_TIN][0]
	dung("Bỏ qua kèm câu đọc mã", tin["trang_thai"] == "Bỏ qua" and "đọc mã" in tin["loi"])
	chen, vas = _db_moi(mau_duyet=False)
	kq = _voi(vas, lambda: db.cap_ma("97077", "vua", "Giao trễ"))
	dung("mẫu chưa gắn: nói lý do", kq["zalo"] == 0 and "mẫu" in kq["ly_do"].lower())


@ca("v645 cấp mã đền bù bị chặn: đơn đã có mã (mọi mức), khách lẻ, mức lạ, Khác không ghi chú, mức chưa chọn chương trình, đơn không có")
def _db_chan():
	chen, vas = _db_moi(da_cap=["den_bu:ACC-SINV-1"])
	nem("đơn đã cấp", lambda: _voi(vas, lambda: db.cap_ma("97077", "nang", "Bánh hỏng")))
	la("không phát mã", [x for x in chen if x.get("doctype") == "Vagabond Voucher"], [])
	chen, vas = _db_moi(khach="Khách bán lẻ")
	nem("khách lẻ", lambda: _voi(vas, lambda: db.cap_ma("97077", "nhe", "Giao trễ")))
	chen, vas = _db_moi()
	nem("mức lạ", lambda: _voi(vas, lambda: db.cap_ma("97077", "rat_nang", "Giao trễ")))
	nem("Khác không ghi chú", lambda: _voi(vas, lambda: db.cap_ma("97077", "nhe", "Khác", "")))
	nem("đơn không có", lambda: _voi(vas, lambda: db.cap_ma("00000", "nhe", "Giao trễ")))
	chen, vas = _db_moi(ctkm="")
	nem("mức chưa chọn chương trình", lambda: _voi(vas, lambda: db.cap_ma("97077", "vua", "Giao trễ")))
	la("không phát mã khi bị chặn", [x for x in chen if x.get("doctype") == "Vagabond Voucher"], [])


@ca("v645 Codex 548 c02f2be: cấp mã đền bù kiểm đối tượng của chương trình trước khi phát mã; gửi mã đền bù có sẵn cũng kiểm")
def _db_doi_tuong():
	# Tái hiện Codex: mức đền bù gắn chương trình chỉ cho hạng VOYAGER, khách
	# hạng EXPLORER. Trước bản sửa cap_ma vẫn phát mã và zalo=1, quầy sẽ từ chối.
	chen, vas = _db_moi()
	km_vip = D(name="KM-DB", ten="Đền bù VIP", cach_ma="Ma dung mot lan", bat=1, kieu_giam="Phan tram", gia_tri=15,
		doi_tuong="Theo hang khach", hang_khach="VOYAGER")
	hang = {"K1": "EXPLORER"}

	def gv(dt_, n=None, cot=None, *a, **k):
		return hang.get(n) if dt_ == "Customer" and cot == "vgb_hang" else None
	vas2 = vas + [um.patch.object(zk, "_doc_ctkm", lambda ten: km_vip if ten else None), um.patch.object(fr.db, "get_value", gv)]
	nem("khách ngoài hạng của chương trình", lambda: _voi(vas2, lambda: db.cap_ma("97077", "vua", "Giao trễ")))
	la("không phát mã, không xếp tin", [x.get("doctype") for x in chen], [])
	hang["K1"] = "VOYAGER"
	chen, vas = _db_moi()
	vas2 = vas + [um.patch.object(zk, "_doc_ctkm", lambda ten: km_vip if ten else None), um.patch.object(fr.db, "get_value", gv)]
	kq = _voi(vas2, lambda: db.cap_ma("97077", "vua", "Giao trễ"))
	la("đúng hạng thì cấp", kq["ma"], "DB7788")
	# Gửi mã có sẵn: chương trình của mã đổi đối tượng sau lúc cấp.
	km = D(name="KM-SN", ten="Đền bù", cach_ma="Ma dung mot lan", bat=1, kieu_giam="Phan tram", gia_tri=15,
		hd_toi_thieu=0, doi_tuong="Khach chi dinh")
	rows = [D(name="T1", khach="K1", khoa="den_bu:HD9", trang_thai="Chờ gửi", voucher="DB1")]
	m = MoiV(_cau("den_bu_vua", ctkm="KM-SN"), rows, {"K1": _hs()}, [], ctkm=km,
		voucher={"DB1": D(ma="DB1", ctkm="KM-SN", trang_thai="Chua dung", han_dung=D8(2026, 12, 28), danh_cho="K1")})
	with um.patch.object(fr.db, "exists", lambda *a, **k: False):
		m.chay(zk.gui_hang_doi)
	la("không gọi Zalo", m.goi, [])
	ly = [v.get("loi") for d, n, v in m.sv if n == "T1" and v.get("trang_thai") == "Bỏ qua"]
	dung("bỏ, lý do đối tượng", bool(ly) and "đối tượng" in ly[0])


# ------------------------------------------------------------ điểm, mã của khách, bản vá

@ca("v645 điểm của đơn: đã vào sổ thì đọc sổ; chưa ghi sổ thì tính bằng đúng phép cộng điểm theo hạng; khách lẻ 0")
def _diem():
	# khach_hang kéo ban_hang và requests: CI không có requests thì mượn mô đun
	# rỗng trong ca này rồi gỡ sạch (thu_crm_614 _nen_ban).
	with _nen_ban():
		_diem_chay()


def _diem_chay():
	from vagabond import khach_hang as kh

	with um.patch.object(fr.db, "sql", lambda *a, **k: [[500.0]]):
		la("đã vào sổ", kh.diem_cua_don("HD1"), (500.0, True))
	with um.patch.object(fr.db, "sql", lambda *a, **k: [[None]]), \
			um.patch.object(fr.db, "get_value", lambda *a, **k: {"customer": "K1", "grand_total": 450000}), \
			um.patch.object(kh, "_hang_cua", lambda k: {"tich_diem": 2}):
		la("chưa ghi sổ", kh.diem_cua_don("HD1"), (kh.diem_cho_don(450000, 2), False))
	with um.patch.object(fr.db, "sql", lambda *a, **k: [[None]]), \
			um.patch.object(fr.db, "get_value", lambda *a, **k: {"customer": "Khách bán lẻ", "grand_total": 450000}):
		la("khách lẻ", kh.diem_cua_don("HD1"), (0, False))


@ca("v645 hai cửa zk tới khach_hang: khách gộp và điểm của đơn đi đúng hàm thật (bộ kiểm khác vá hai cửa này)")
def _cua_khach():
	with _nen_ban():
		from vagabond import khach_hang as kh

		la("giỏ chung", [zk._la_khach_gop(m) for m in ("Khách bán lẻ", "Khách lẻ Online", " ", "K1")], [True, True, True, False])
		la("bản giả trùng hàm thật", [_gop(m) for m in ("Khách bán lẻ", "Khách lẻ Online", " ", "K1")],
			[kh.la_khach_gop(m) for m in ("Khách bán lẻ", "Khách lẻ Online", " ", "K1")])
		with um.patch.object(kh, "diem_cua_don", lambda hd: (77, hd == "HD9")):
			la("điểm qua cửa", zk._diem_cua_don("HD9"), (77, True))


@ca("v645 mã của khách tại quầy: chỉ mã chưa dùng, còn hạn, chương trình đang bật; khách trống thì rỗng")
def _ma_khach():
	from vagabond import khuyen_mai as km

	loc = []

	def get_all(dt_, filters=None, **k):
		loc.append(filters)
		return [D(ma="A1", ctkm="KM-ON", ten_ctkm="Quà", han_dung=D8(2026, 11, 30)), D(ma="A2", ctkm="KM-OFF", ten_ctkm="Cũ", han_dung=D8(2026, 12, 1))]
	with um.patch.object(km, "_kiem_quyen", lambda: None), um.patch.object(fr, "get_all", get_all), \
			um.patch.object(km, "_doc_ctkm", lambda t: {"bat": 1 if t == "KM-ON" else 0, "ten": t}):
		r = km.ma_cua_khach("K1")
		la("rỗng", km.ma_cua_khach(" "), {"ds": []})
	la("chỉ mã chương trình bật", [x["ma"] for x in r["ds"]], ["A1"])
	la("lọc", (loc[0]["danh_cho"], loc[0]["trang_thai"], loc[0]["han_dung"][0]), ("K1", "Chua dung", ">="))


@ca("v645 bản vá bật tin cảm ơn: tắt thì bật và ghi lúc bật; giờ 22 kẹp về 20; đã đúng thì không đổi; tích tin báo cáo cho nhóm Marketing")
def _ban_va():
	from vagabond.patches import v645_tin_khach_zalo as p

	luc = dt.datetime(2026, 11, 9, 0, 1)
	la("tắt -> bật", p.gia_tri_bat({"bat": 0, "gio_tu": 8, "gio_den": 20}, luc), {"bat": 1, "bat_luc": luc})
	la("đang bật, giờ 22", p.gia_tri_bat({"bat": 1, "gio_tu": 8, "gio_den": 22}, luc), {"gio_tu": 8, "gio_den": 20})
	la("đã đúng", p.gia_tri_bat({"bat": 1, "gio_tu": 8, "gio_den": 20}, luc), {})
	la("tích theo mốc", p.tin_them("mkt_banh_cho_anh"), "mkt_banh_cho_anh, mkt_bao_cao_uu_dai")
	la("nhóm khác không đổi", (p.tin_them("hd_dau_vao"), p.tin_them("")), (None, None))
	la("chạy lại không đổi", p.tin_them("mkt_banh_cho_anh, mkt_bao_cao_uu_dai"), None)
	import io
	import os
	pt = io.open(os.path.join(os.path.dirname(zk.__file__), "patches.txt"), encoding="utf-8").read()
	dung("bản vá có trong patches.txt", "vagabond.patches.v645_tin_khach_zalo" in pt.split("[post_model_sync]")[1])
