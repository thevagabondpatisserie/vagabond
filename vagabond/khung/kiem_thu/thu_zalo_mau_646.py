# -*- coding: utf-8 -*-
"""v646 (Minh Vũ báo 09/11/2026): gửi thử tin "Cảm ơn khi khách nhận đơn, báo điểm"
bị Zalo từ chối "tong_tien has invalid format (mã -1124)"; thẻ kịch bản báo hôm nay
gửi 0, lỗi 20.

Nguyên nhân: ô tong_tien của mẫu 659376 có kiểu CURRENCY (Tiền tệ VNĐ, dài 12), Zalo
chỉ nhận chữ số trơn. Máy chỉ đổi sang số trơn cho kiểu NUMBER, nên gửi "450.000đ".
Bộ kiểm cũ (thu_zalo_kich_ban_621 TS_SAU_MUA) tự đặt kiểu NUMBER cho tong_tien và
STRING cho ngay_mua, khác mẫu thật, nên xanh mà lỗi vẫn lên site.

Bộ này dùng NGUYÊN VĂN bộ tham số máy đã đọc từ Zalo và lưu trên site (ô "Tham số
mẫu" của từng kịch bản, chép 09/11/2026), rồi soát mọi giá trị gửi đi bằng luật kiểu
của Zalo: NUMBER và CURRENCY chỉ chữ số, DATE dạng dd/mm/yyyy, không dài quá ô.

Mỗi ca chốt một đường lỗi có thật:
  - tiền gửi kèm dấu chấm và chữ đ (gửi thật và gửi thử);
  - lỗi dữ liệu không khớp mẫu loại vĩnh viễn từng khách (20 khách mất tin cảm ơn)
    thay vì dừng lượt và để tin chờ;
  - không ai được báo khi cả kịch bản đang hỏng;
  - ô điều kiện cho gõ 40 chữ trong khi mẫu chỉ nhận 30 (bị cắt cụt lúc gửi).
"""

import datetime as dt
import io
import json
import os
import re
import sys
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

# Bản Frappe giả chung chưa có get_url khi chạy lẻ tệp này (cùng cách thu_tin_zalo_604).
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test"

from vagabond import zalo_kich_ban as zk  # noqa: E402
from vagabond.khung.kiem_thu.thu_zalo_kich_ban_621 import BAY_GIO, D, Moi, _cau, _hs  # noqa: E402

D8 = dt.date
fr = zk.frappe

# Chép nguyên văn ô "Tham số mẫu" trên site ngày 09/11/2026 (máy đọc từ Zalo template/info/v2).
TS_659376 = json.loads('[{"name": "ten_khach", "type": "STRING", "maxLength": 30, "require": true}, '
	'{"name": "ma_hoa_don", "type": "STRING", "maxLength": 30, "require": true}, '
	'{"name": "ngay_mua", "type": "DATE", "maxLength": 20, "require": true}, '
	'{"name": "tong_tien", "type": "CURRENCY", "maxLength": 12, "require": true}, '
	'{"name": "diem_tich", "type": "NUMBER", "maxLength": 20, "require": true}, '
	'{"name": "tong_diem", "type": "NUMBER", "maxLength": 20, "require": true}, '
	'{"name": "hang", "type": "STRING", "maxLength": 30, "require": true}]')
# Mẫu voucher 659377, 659378, 663776, 663796, 663808, 663814, 663833: cùng bộ năm ô.
TS_VOUCHER = json.loads('[{"name": "ten_khach", "type": "STRING", "maxLength": 30, "require": true}, '
	'{"name": "ten_uu_dai", "type": "STRING", "maxLength": 30, "require": true}, '
	'{"name": "dieu_kien", "type": "STRING", "maxLength": 30, "require": true}, '
	'{"name": "han_dung", "type": "DATE", "maxLength": 20, "require": true}, '
	'{"name": "ma_voucher", "type": "STRING", "maxLength": 30, "require": true}]')


def loi_kieu(data, tham_so):
	"""Luật kiểu của Zalo cho từng ô: trả danh sách ô Zalo sẽ từ chối."""
	sai = []
	for p in tham_so:
		v = data.get(p["name"])
		if v is None:
			sai.append(p["name"] + ": thiếu")
			continue
		v = str(v)
		k = p["type"]
		if k in ("NUMBER", "CURRENCY") and not re.fullmatch(r"\d+", v):
			sai.append("%s: %r không phải số trơn" % (p["name"], v))
		elif k == "DATE" and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", v):
			sai.append("%s: %r không phải dd/mm/yyyy" % (p["name"], v))
		if len(v) > int(p["maxLength"]):
			sai.append("%s: dài %d quá %s" % (p["name"], len(v), p["maxLength"]))
	return sai


# ------------------------------------------------------------ phần thuần

@ca("v646 Zalo -1124: ô Tiền tệ (CURRENCY) gửi số trơn, không kèm dấu chấm và chữ đ")
def _currency():
	la("450.000đ", zk.chuan_tham_so("450.000đ", "CURRENCY", 12), "450000")
	la("số thật", zk.chuan_tham_so(1450000.0, "CURRENCY", 12), "1450000")
	la("kiểu chữ thường", zk.chuan_tham_so("90.000đ", "currency", 12), "90000")
	la("NUMBER vẫn như cũ", zk.chuan_tham_so("25.400", "NUMBER", 20), "25400")
	la("STRING không đụng", zk.chuan_tham_so("450.000đ", "STRING", 30), "450.000đ")


@ca("v646 gửi thử đúng mẫu thật 659376: mọi ô đạt luật kiểu Zalo (trước: tong_tien '450.000đ')")
def _gui_thu_mau_that():
	data, thieu = zk.du_lieu_mau(zk.MAU_THU, TS_659376)
	la("không thiếu", thieu, [])
	la("không ô nào Zalo từ chối", loi_kieu(data, TS_659376), [])
	la("tiền", data["tong_tien"], "450000")
	la("ngày", data["ngay_mua"], "29/10/2026")
	data, thieu = zk.du_lieu_mau(zk.MAU_THU, TS_VOUCHER)
	la("mẫu voucher: không thiếu", thieu, [])
	la("mẫu voucher: không ô nào Zalo từ chối", loi_kieu(data, TS_VOUCHER), [])


@ca("v646 gửi thật cảm ơn sau mua theo mẫu thật: tiền 1.450.000đ, điểm 14.500 ra số trơn, ngày dd/mm/yyyy")
def _gui_that():
	si = {"HDB-9": D(docstatus=1, posting_date=D8(2026, 11, 9), posting_time="15:36:00", grand_total=1450000)}
	rows = [D(name="T9", khach="K9", hoa_don="HDB-9", diem=14500, khoa="sau_mua:HDB-9", trang_thai="Chờ gửi")]
	m = Moi(_cau("sau_mua", mau_tham_so=json.dumps(TS_659376)), rows, {"K9": _hs()}, [], si=si)
	m.diem = {"HDB-9": (14500, True)}
	m.chay(zk.gui_hang_doi)
	la("gọi Zalo một lần", len(m.goi), 1)
	data = m.goi[0][2]
	la("không ô nào Zalo từ chối", loi_kieu(data, TS_659376), [])
	la("tiền, điểm, ngày", (data["tong_tien"], data["diem_tich"], data["tong_diem"], data["ngay_mua"]),
		("1450000", "14500", "25400", "09/11/2026"))


@ca("v646 Zalo trả -1124: dừng lượt kịch bản, tin để chờ (không loại khách), câu lỗi giữ tên ô; báo Marketing một lần mỗi ngày")
def _loi_mau():
	from vagabond import kenh_zalo

	si = {"HDB-%d" % i: D(docstatus=1, posting_date=D8(2026, 11, 9), posting_time="15:36:00", grand_total=450000) for i in (1, 2, 3)}
	rows = [D(name="T%d" % i, khach="K%d" % i, hoa_don="HDB-%d" % i, diem=4500, khoa="sau_mua:HDB-%d" % i, trang_thai="Chờ gửi")
		for i in (1, 2, 3)]
	tra = [{"error": -1124, "message": "tong_tien has invalid format"}]
	m = Moi(_cau("sau_mua", mau_tham_so=json.dumps(TS_659376)), rows, {"K%d" % i: _hs() for i in (1, 2, 3)}, tra, si=si)
	bao = []
	with um.patch.object(kenh_zalo, "bao_hoac_ghi_loi", lambda *a, **k: bao.append((a, k)) or ["Z1"]):
		tom = m.chay(zk.gui_hang_doi)
		# Lượt thứ hai cùng ngày, Zalo vẫn từ chối: không báo lần hai (khoá trùng ngày).
		m.tra = [{"error": -1124, "message": "tong_tien has invalid format"}]
		m.chay(zk.gui_hang_doi)
	la("chỉ thử một khách mỗi lượt rồi dừng", [g[3] for g in m.goi], ["sau_mua:HDB-1", "sau_mua:HDB-1"])
	la("không ai bị loại, cả ba còn chờ", m.tt(), {"T1": "Chờ gửi", "T2": "Chờ gửi", "T3": "Chờ gửi"})
	cau = [v.get("loi") for d, n, v in m.sv if n == "T1" and "loi" in v][0]
	dung("câu lỗi nói lỗi dữ liệu và giữ tên ô", "sai định dạng" in cau and "tong_tien" in cau and cau.endswith("(mã -1124)"))
	dung("tóm tắt lượt có chữ dừng lượt", "Dừng lượt" in tom["sau_mua"])
	la("báo hai lần gọi, cùng một khoá trong ngày", [k["khoa"] for a, k in bao], ["zalo_mau_loi:sau_mua:%s" % BAY_GIO.date().isoformat()] * 2)
	la("đúng tin Marketing", (bao[0][1]["ma_tin"], bao[0][0][0], bao[0][0][1]), ("mkt_zalo_mau_loi", "canh_bao", "ban_hang"))
	la("mã tin thuộc nhóm Marketing", kenh_zalo.TIN["mkt_zalo_mau_loi"][0], "Marketing")
	for ma in (-1121, -1122, -1124):
		dung("%s dừng lượt" % ma, ma in zk.LOI_DUNG_LUOT)


@ca("v646 lỗi của riêng một khách (-118) vẫn loại riêng khách đó và KHÔNG báo Marketing")
def _loi_khach():
	from vagabond import kenh_zalo

	si = {"HDB-1": D(docstatus=1, posting_date=D8(2026, 11, 9), posting_time="10:00:00", grand_total=90000)}
	rows = [D(name="T1", khach="K1", hoa_don="HDB-1", diem=900, khoa="sau_mua:HDB-1", trang_thai="Chờ gửi")]
	m = Moi(_cau("sau_mua", mau_tham_so=json.dumps(TS_659376)), rows, {"K1": _hs()}, [{"error": -118, "message": "x"}], si=si)
	bao = []
	with um.patch.object(kenh_zalo, "bao_hoac_ghi_loi", lambda *a, **k: bao.append(k) or []):
		m.chay(zk.gui_hang_doi)
	la("khách lỗi", m.tt(), {"T1": "Lỗi"})
	la("không báo", bao, [])


@ca("v646 ô Điều kiện trên tin: tối đa 30 chữ như mẫu thật (trước cho gõ 40, gửi bị cắt cụt)")
def _dieu_kien_30():
	_, dk = zk.mo_ta_uu_dai({}, "", "x" * 60)
	la("máy cắt 30", len(dk), 30)
	tran = {p["name"]: p["maxLength"] for p in TS_VOUCHER}
	_, dk = zk.mo_ta_uu_dai({"hd_toi_thieu": 1500000})
	dung("chữ máy tự viết vừa ô mẫu", len(dk) <= tran["dieu_kien"])
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	js = io.open(os.path.join(goc, "public", "js", "bep", "58-crm.js"), encoding="utf-8").read()
	dung("màn app giới hạn ô 30", "ĐIỀU KIỆN TRÊN TIN (TỐI ĐA 30 CHỮ)" in js and "TỐI ĐA 40" not in js)
	cu = {"ma": "sinh_nhat", "dieu_kien": ""}
	ghi = {}
	with um.patch.object(zk, "_quyen", lambda **k: None), um.patch.object(zk, "_dam_bao", lambda: None), \
			um.patch.object(zk, "_cau_hinh", lambda ma: dict(cu)), \
			um.patch.object(fr.db, "set_value", lambda dt_, n, v, *a, **k: ghi.update(v)), \
			um.patch.object(fr.db, "commit", lambda: None):
		try:
			zk.luu_kich_ban("sinh_nhat", json.dumps({"dieu_kien": "y" * 45}))
		except Exception:
			pass
	la("lưu cắt 30", len(ghi.get("dieu_kien") or ""), 30)


@ca("v646 bản vá tích tin lệch mẫu cho nhóm Marketing: theo mốc tin báo cáo ưu đãi, nhóm khác và nhóm nhận tất cả không đổi, chạy lại không đổi")
def _ban_va():
	from vagabond.patches import v646_tin_zalo_mau_loi as p
	from vagabond import kenh_zalo

	la("tích theo mốc", p.tin_them("mkt_banh_cho_anh, mkt_bao_cao_uu_dai"), "mkt_banh_cho_anh, mkt_bao_cao_uu_dai, mkt_zalo_mau_loi")
	la("chỉ tích báo cáo ưu đãi", p.tin_them("mkt_bao_cao_uu_dai"), "mkt_bao_cao_uu_dai, mkt_zalo_mau_loi")
	la("nhóm chỉ nhận tin ảnh bánh: không đổi", p.tin_them("mkt_banh_cho_anh"), None)
	la("nhóm khác, nhóm nhận tất cả", (p.tin_them("hd_dau_vao"), p.tin_them("")), (None, None))
	la("chạy lại không đổi", p.tin_them("mkt_bao_cao_uu_dai, mkt_zalo_mau_loi"), None)
	dung("mã tin có thật", all(ma in kenh_zalo.TIN for _, ma in p.THEO_MOC))
	goc = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	pt = io.open(os.path.join(goc, "patches.txt"), encoding="utf-8").read()
	dung("bản vá có trong patches.txt", "vagabond.patches.v646_tin_zalo_mau_loi" in pt.split("[post_model_sync]")[1])
