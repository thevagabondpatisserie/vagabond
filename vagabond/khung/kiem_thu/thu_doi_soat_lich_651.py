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
