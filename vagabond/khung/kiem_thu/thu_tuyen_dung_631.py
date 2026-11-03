# -*- coding: utf-8 -*-
"""v631: Tuyển dụng, nút Loại ứng viên và đường mở thẳng hồ sơ (anh Việt 02/11/2026).

Anh duyệt mẫu "Tuyển dụng: lọc, loại ứng viên, trang chi tiết":
  - Loại bắt buộc chọn một lý do trong danh sách; "Khác" thì phải ghi thêm
    (_ly_do_thuan, _loai).
  - Hồ sơ loại không xoá, lưu "Dừng" như cũ (app hiện "Đã loại"), mở lại được
    bằng Cập nhật (_mo_lai).
  - Bật Nhắn cảm ơn thì nhật ký ghi lần nhắn Zalo mẫu cảm ơn (_loai).
  - Tin Zalo hồ sơ mới, hồ sơ quá 24 giờ mở thẳng trang chi tiết (_link).

Chạy hàm THẬT trên site giả của thu_tuyen_dung_622 (cùng lớp Frappe giả).
"""

import datetime as dt
import sys
import types
import unittest.mock as um

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu import thu_tuyen_dung_622 as t622
from vagabond import tuyen_dung as td

_Site, _chay, _loi, _hs, _vt, BAY_GIO = t622._Site, t622._chay, t622._loi, t622._hs, t622._vt, t622.BAY_GIO


def _uv(**k):
	d = dict(_hs(ca_ranh="Tối, Cuối tuần"), name="UV-1", sdt="0909123456", trang_thai=td.MOI, da_an_danh=0, nhat_ky="")
	d.update(k)
	return d


@ca("v631 lý do loại (thuần): đủ 8 lý do đã duyệt, Khác bắt ghi thêm, ghi thêm nối sau lý do, lý do lạ bị chặn")
def _ly_do_thuan():
	la("danh sách lý do theo mẫu đã duyệt", list(td.LY_DO_DUNG), ["Thiếu kinh nghiệm", "Lương mong muốn cao", "Ca làm không khớp", "Ở xa",
		"Không liên lạc được", "Ứng viên rút", "Không đạt làm thử", "Khác"])
	la("nhãn hiện trên app", td.TEN_DUNG, "Đã loại")
	la("lý do trơn", td.cau_ly_do_loai("Ở xa"), ("Ở xa", ""))
	la("lý do kèm ghi thêm, gom khoảng trắng", td.cau_ly_do_loai("Lương mong muốn cao", "  muốn   15 triệu "), ("Lương mong muốn cao. muốn 15 triệu", ""))
	dung("Khác chưa ghi thêm bị chặn", "ghi thêm" in td.cau_ly_do_loai("Khác", " ")[1])
	la("Khác có ghi thêm: lưu đúng chữ ghi", td.cau_ly_do_loai("Khác", "Đã nhận việc nơi khác"), ("Đã nhận việc nơi khác", ""))
	dung("lý do lạ bị chặn", "trong danh sách" in td.cau_ly_do_loai("Không phù hợp")[1])
	dung("lý do rỗng bị chặn", td.cau_ly_do_loai("")[1] != "")
	la("câu lưu tối đa 140 ký tự", len(td.cau_ly_do_loai("Ở xa", "x" * 300)[0]), 140)
	dung("câu lỗi máy chủ nói Loại, không nói Dừng", "loại" in td.kiem_chuyen(td.MOI, td.DUNG, ly_do=""))


@ca("v631 Loại: hồ sơ sang Dừng, lưu lý do, nhớ bước trước khi loại; bật cảm ơn thì nhật ký ghi nhắn Zalo mẫu cảm ơn, trạng thái giữ Dừng")
def _loai():
	site = _Site(vt=[_vt()], uv=[_uv(trang_thai=td.HEN_PV, lich_hen="2026-08-16 14:00:00")])
	_chay(site, lambda: td.loai("UV-1", "Lương mong muốn cao", "muốn 15 triệu", 1))
	r = site.lay(td.UV, "UV-1")
	la("trạng thái, lý do, bước trước khi loại", (r["trang_thai"], r["ly_do_dung"], r["dung_tu"]),
		(td.DUNG, "Lương mong muốn cao. muốn 15 triệu", td.HEN_PV))
	dung("nhật ký ghi lần loại kèm lý do", "Hẹn phỏng vấn -> Dừng (Lương mong muốn cao. muốn 15 triệu)" in r["nhat_ky"])
	dung("nhật ký ghi lần nhắn cảm ơn", "Nhắn Zalo mẫu Cảm ơn, chưa phù hợp" in r["nhat_ky"])
	la("trạng thái không bị lần nhắn kéo đi", r["trang_thai"], td.DUNG)
	site2 = _Site(vt=[_vt()], uv=[_uv()])
	_chay(site2, lambda: td.loai("UV-1", "Không liên lạc được", "", "0"))
	r2 = site2.lay(td.UV, "UV-1")
	dung("tắt cảm ơn: không ghi lần nhắn", "Nhắn Zalo" not in r2["nhat_ky"])
	la("Mới nhận bị loại: ghi lần liên hệ đầu như Cập nhật", r2["lien_he_luc"], BAY_GIO)
	site3 = _Site(vt=[_vt()], uv=[_uv()])
	dung("Khác chưa ghi thêm bị chặn ở máy chủ", "ghi thêm" in _loi(lambda: _chay(site3, lambda: td.loai("UV-1", "Khác", ""))))
	dung("lý do lạ bị chặn ở máy chủ", "trong danh sách" in _loi(lambda: _chay(site3, lambda: td.loai("UV-1", "Hết chỗ"))))
	r3 = site3.lay(td.UV, "UV-1")
	la("bị chặn thì hồ sơ không đổi", (r3["trang_thai"], r3["nhat_ky"]), (td.MOI, ""))
	site4 = _Site(vt=[_vt()], uv=[_uv(trang_thai=td.NHAN_VIEC)])
	dung("người đã nhận việc không loại được", "đã nhận việc" in _loi(lambda: _chay(site4, lambda: td.loai("UV-1", "Ở xa"))))
	dung("người không có quyền bị chặn", _loi(lambda: _chay(site3, lambda: td.loai("UV-1", "Ở xa"), vai=("Sales User",))) != "")
	la("hồ sơ người không quyền gọi vẫn nguyên", site3.lay(td.UV, "UV-1")["trang_thai"], td.MOI)


@ca("v631 Mở lại hồ sơ đã loại: Cập nhật về bước trước, lý do và bước dừng được xoá")
def _mo_lai():
	site = _Site(vt=[_vt()], uv=[_uv(trang_thai=td.LIEN_HE)])
	_chay(site, lambda: td.loai("UV-1", "Ứng viên rút"))
	_chay(site, lambda: td.cap_nhat("UV-1", td.LIEN_HE))
	r = site.lay(td.UV, "UV-1")
	la("mở lại", (r["trang_thai"], r["ly_do_dung"], r["dung_tu"]), (td.LIEN_HE, "", ""))
	dung("nhật ký ghi lần mở lại", "Dừng -> Đã liên hệ" in r["nhat_ky"])


@ca("v631 tin Zalo hồ sơ mới và hồ sơ quá 24 giờ mở thẳng trang chi tiết hồ sơ (/tuyen-dung?mo=<mã>)")
def _link():
	la("đường mở thẳng (thuần)", td.link_ho_so("UV-2026-00012"), "/tuyen-dung?mo=UV-2026-00012")
	la("mã lạ được mã hoá, không chen tham số", td.link_ho_so("A&b=1"), "/tuyen-dung?mo=A%26b%3D1")
	goi = []
	zalo = types.SimpleNamespace(
		bao=lambda loai, chu_de, tieu_de, dong=None, **kw: goi.append(kw),
		bao_hoac_ghi_loi=lambda loai, chu_de, tieu_de, dong=None, **kw: goi.append(kw))
	cu = _uv(name="UV-1", ten_vi_tri="Thu ngân ca tối", creation=dt.datetime(2026, 8, 14, 8, 0))
	moi = _uv(name="UV-2", ten_vi_tri="Thu ngân ca tối", creation=dt.datetime(2026, 8, 15, 8, 0))
	site = _Site(uv=[cu, moi])
	with um.patch.dict(sys.modules, {"vagabond.kenh_zalo": zalo}), um.patch.object(td.frappe.utils, "now_datetime", lambda: BAY_GIO):
		import vagabond
		with um.patch.object(vagabond, "kenh_zalo", zalo, create=True):
			_chay(site, td.nhac_qua_han)
			_chay(site, lambda: td.bao_moi(site.lay(td.UV, "UV-2")))
	la("tin quá 24 giờ và tin hồ sơ mới trỏ đúng hồ sơ", [g["link"] for g in goi],
		["https://vagabond.test/tuyen-dung?mo=UV-1", "https://vagabond.test/tuyen-dung?mo=UV-2"])


@ca("v631 tong_quan gửi app lý do loại, nhãn Đã loại và lý do Khác (app không tự giữ danh sách)")
def _tong_quan():
	site = _Site(vt=[_vt()], uv=[_uv(creation=dt.datetime(2026, 8, 14, 8, 0))])
	with um.patch.object(td.frappe.utils, "now_datetime", lambda: BAY_GIO):
		kq = _chay(site, td.tong_quan)
	la("gửi đủ", (kq["ly_do_dung"], kq["ten_dung"], kq["ly_do_khac"]), (list(td.LY_DO_DUNG), "Đã loại", "Khác"))
