"""v651 (anh Việt 12/11/2026): giờ nhắc thư đối soát và chữ ký thư Shinhan.

1. Grab NVHTN gửi báo cáo GrabFood ngày hôm trước lúc 17:00. Hạn cũ 12:00 và
   lượt nhắc 17:00 làm bot báo "GrabFood chưa về" đúng lúc thư đang tới. Anh
   chốt lùi hạn GrabFood sang 18:00. Lượt nhắc buổi chiều phải chạy SAU hạn đó,
   không thì GrabFood không bao giờ được nhắc (17:00 < 18:00).
2. Thư Shinhan do BC Card Việt Nam ký (d=bccardvn.com). Anh chốt tin chữ ký đó
   là của Shinhan. Chữ ký vẫn phải HỢP LỆ: thư 09/11 đến 12/11 có chữ ký
   bccardvn.com nhưng thân thư không khớp (Gmail cũng báo "body hash did not
   verify"), nên vẫn bị chặn.
"""
from datetime import date

from vagabond import doi_soat_thu as T
from vagabond import hooks
from vagabond.khung.kiem_thu.nen import ca, la

LICH = [dict(vendor=v, tan_suat=t, han_gio=g, han_ngay=n, ngay_lam_viec=l) for v, t, g, n, l in T.LICH_MAC_DINH]
NG = [dict(ten=t, mien=T.tach_mien(m), bat_buoc=b) for t, m, b in T.NGUOI_GUI_MAC_DINH]
HOM = date(2026, 11, 12)  # thứ Năm
BAT = "2026-11-01"


def _gio_nhac():
	ra = []
	for k, v in hooks.scheduler_events["cron"].items():
		if "vagabond.doi_soat_thu.nhac_thieu_thu" in v:
			phut, gio = k.split()[:2]
			ra.append((int(gio), int(phut)))
	return sorted(ra)


def _thieu(gio):
	# Mọi nguồn khác đã về đủ hôm qua, chỉ GrabFood chưa về.
	nguon = [dict(vendor=l["vendor"], tai_khoan="", tu_ngay="2026-11-11", den_ngay="2026-11-11", kenh_nhan=T.KENH)
		for l in LICH if l["vendor"] != "GrabFood"]
	return [x["vendor"] for x in T.thu_thieu(LICH, HOM, gio, nguon, BAT)]


@ca("v651 lịch thư: GrabFood hạn 18:00, lúc 17:00 chưa báo thiếu, sau 18:00 mới báo")
def _():
	la("hạn GrabFood", [l["han_gio"] for l in LICH if l["vendor"] == "GrabFood"], [18])
	la("17:00 chưa báo", _thieu(17), [])
	la("18:00 báo GrabFood", _thieu(18), ["GrabFood"])


@ca("v651 lịch thư: mọi nguồn hằng ngày đều có ít nhất một lượt nhắc chạy sau hạn của nó")
def _():
	nhac = _gio_nhac()
	la("hai lượt 12:30 và 18:30", nhac, [(12, 30), (18, 30)])
	sot = [l["vendor"] for l in LICH if l["tan_suat"] == "Hằng ngày" and not any(g >= l["han_gio"] for g, _ in nhac)]
	la("không nguồn nào không bao giờ được nhắc", sot, [])
	t, d = T.tin_thieu_thu([dict(vendor="GrabFood", tai_khoan="", ngay="2026-11-11")], 2)
	la("tin lượt chiều nói đúng giờ", d[-1].startswith("Vẫn chưa về sau 18:30"), True)


@ca("v651 Shinhan: chữ ký hợp lệ của bccardvn.com được nhận, chữ ký hỏng vẫn chặn")
def _():
	ok = T.quyet_dinh("shinhan.com.vn", 1, [dict(d="bccardvn.com", dat=True, ly_do="")], NG)
	la("ký hợp lệ: nhận", (ok["ket_qua"], ok["ky_boi"], ok["nguon"]),
		(T.KQ_XAC_THUC, "bccardvn.com", "Shinhan (POS và thẻ tín dụng)"))
	hong = T.quyet_dinh("shinhan.com.vn", 1, [dict(d="bccardvn.com", dat=False,
		ly_do="Thân thư hoặc tệp đính kèm đã bị sửa sau khi đối tác ký.")], NG)
	la("thư 09/11 (thân không khớp chữ ký): vẫn chặn, báo đúng lý do", (hong["ket_qua"], hong["ly_do"]),
		(T.KQ_CHAN, "Thân thư hoặc tệp đính kèm đã bị sửa sau khi đối tác ký."))
	la("bccardvn.com không mở cửa cho người gửi khác", T.quyet_dinh("onepay.vn", 1,
		[dict(d="bccardvn.com", dat=True, ly_do="")], NG)["ket_qua"], T.KQ_CHAN)


def _site_da_gieo(lich_grab=12, mien_shinhan="shinhan.com.vn", da_nang=False):
	"""Frappe giả của một site ĐÃ gieo Cài đặt bằng mặc định cũ (trước v651)."""
	from types import SimpleNamespace as NS

	bang = {
		"Vagabond Doi Soat Nguoi Gui": [dict(name="NG%s" % i, parent=T.CAI_DAT, parentfield="ds_nguoi_gui", idx=i,
			ten=t, ten_mien=(mien_shinhan if t.startswith("Shinhan") else m), bat_buoc_chu_ky=b)
			for i, (t, m, b) in enumerate(T.NGUOI_GUI_MAC_DINH, 1)],
		"Vagabond Doi Soat Lich Thu": [dict(name="LT%s" % i, parent=T.CAI_DAT, parentfield="ds_lich_thu", idx=i,
			nguon=v, tan_suat=t, han_gio=(lich_grab if v == "GrabFood" else g), han_ngay=n, ngay_lam_viec=l)
			for i, (v, t, g, n, l) in enumerate(T.LICH_MAC_DINH, 1)],
	}
	toan_cuc = {"vgb_ds_thu_gieo": "1", "vgb_ds_noi_bo_gieo": "1"}
	if da_nang:
		toan_cuc["vgb_ds_thu_v651"] = "1"

	def get_all(dt, filters=None, fields=None, **k):
		return [dict(r) for r in bang.get(dt, []) if all(r.get(a) == b for a, b in (filters or {}).items())]

	def set_value(dt, name, f, v=None, **k):
		for r in bang[dt]:
			if r["name"] == name:
				r[f] = v

	def get_cached_doc(dt):
		o = {"ds_thu_bat": 1, "ds_nguoi_gui": bang["Vagabond Doi Soat Nguoi Gui"], "ds_lich_thu": bang["Vagabond Doi Soat Lich Thu"]}
		return NS(get=lambda key, d=None: o.get(key, d))
	fr = NS(db=NS(table_exists=lambda dt: True, get_global=lambda key: toan_cuc.get(key),
		set_global=lambda key, v: toan_cuc.__setitem__(key, v), count=lambda dt, f=None: len(bang.get(dt, [])),
		set_value=set_value, get_single_value=lambda dt, f: "x"),
		get_all=get_all, get_meta=lambda dt: NS(has_field=lambda f: True), get_cached_doc=get_cached_doc,
		clear_document_cache=lambda *a: None, log_error=lambda *a, **k: (_ for _ in ()).throw(AssertionError(k)))
	return fr, bang, toan_cuc


@ca("Codex #554: site đã gieo Cài đặt cũ (GrabFood hạn 12, Shinhan chỉ shinhan.com.vn): lượt migrate nâng lên mặc định mới, cấu hình đọc ra đúng")
def _():
	from unittest.mock import patch
	fr, bang, tc = _site_da_gieo()
	with patch.object(T, "_frappe", lambda: fr):
		T.gieo_mac_dinh()
		ch = T.cau_hinh()
	la("GrabFood hạn 18", [l["han_gio"] for l in ch["lich"] if l["vendor"] == "GrabFood"], [18])
	la("Shinhan tin bccardvn.com", [g["mien"] for g in ch["nguoi_gui"] if g["ten"].startswith("Shinhan")],
		[["shinhan.com.vn", "bccardvn.com"]])
	la("lúc 12:30 không còn báo GrabFood", [x["vendor"] for x in T.thu_thieu(ch["lich"], HOM, 12,
		[dict(vendor=l["vendor"], tai_khoan="", tu_ngay="2026-11-11", den_ngay="2026-11-11", kenh_nhan=T.KENH)
		for l in ch["lich"] if l["vendor"] != "GrabFood"], BAT)], [])
	la("đánh dấu đã nâng", tc.get("vgb_ds_thu_v651"), "1")


@ca("Codex #554: giá trị quản trị đã tự sửa thì giữ nguyên; nâng một lần, quản trị đặt lại sau đó cũng không bị đè")
def _():
	from unittest.mock import patch
	fr, bang, tc = _site_da_gieo(lich_grab=20, mien_shinhan="shinhan.com.vn, shinhanbank.vn")
	with patch.object(T, "_frappe", lambda: fr):
		T.gieo_mac_dinh()
		ch = T.cau_hinh()
	la("GrabFood 20 giữ", [l["han_gio"] for l in ch["lich"] if l["vendor"] == "GrabFood"], [20])
	la("Shinhan tự khai giữ", [g["mien"] for g in ch["nguoi_gui"] if g["ten"].startswith("Shinhan")],
		[["shinhan.com.vn", "shinhanbank.vn"]])
	fr, bang, tc = _site_da_gieo(da_nang=True)
	with patch.object(T, "_frappe", lambda: fr):
		T.gieo_mac_dinh()
	la("đã nâng rồi, quản trị đặt lại 12 thì giữ 12", [r["han_gio"] for r in bang["Vagabond Doi Soat Lich Thu"]
		if r["nguon"] == "GrabFood"], [12])
