# -*- coding: utf-8 -*-
"""v560: tem HACCP không cần lô (anh Việt chốt 03/10/2026, việc số 1).

Tắt lô từ 30/09 nên tem cũ (mẫu in trên Batch) không in được. Tem mới dựng
từ hồ sơ Món, dòng lô đổi thành "Ngày: ..." để nhân viên điền tay. Các ca
dưới chạy phép THUẦN của tem_lenh.py; giao diện chạy thật ở
hanh_vi/tem_khong_lo_559.js.
"""

import datetime

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()
from vagabond import tem_lenh as T  # noqa: E402

LUC = datetime.datetime(2026, 10, 3, 9, 30)
MON = {"name": "TP-0001", "item_name": "Bánh Su Kem", "custom_han_dung_gio": 48,
	"custom_dieu_kien_bao_quan": "Chill", "custom_khoi_luong_tinh": "80g",
	"custom_chat_gay_di_ung": "Sữa, trứng"}


@ca("v560: số tem kẹp trong 1..200, chữ rác thành 1")
def _so_tem():
	la("0 thanh 1", T.so_tem(0), 1)
	la("am thanh 1", T.so_tem(-5), 1)
	la("chu thanh 1", T.so_tem("abc"), 1)
	la("so le lam tron xuong", T.so_tem("3.7"), 3)
	la("tran 200", T.so_tem(5000), 200)


@ca("v560: hạn dùng cùng luật màn xem trước: giờ trước, ngày sau, không khai thì không có")
def _han_dung():
	la("theo gio", T.han_dung(LUC, 48, 3), datetime.datetime(2026, 10, 5, 9, 30))
	la("theo ngay", T.han_dung(LUC, 0, 3), datetime.datetime(2026, 10, 6, 9, 30))
	la("khong khai", T.han_dung(LUC, None, None), None)
	d = T.du_lieu_tem(dict(MON, custom_han_dung_gio=0, shelf_life_in_days=2), LUC)
	la("theo ngay thi khong in gio HSD", d["hsd_gio"], "")
	la("ngay HSD", d["hsd_ngay"], "05/10/2026")


@ca("v560: tem có dòng Ngày để điền tay, không còn mã lô, in đủ N tem")
def _html():
	h = T.html_tem(T.du_lieu_tem(MON, LUC, "MFG-WO-2026-00001", 3))
	la("du 3 tem", h.count('<div class="tem">'), 3)
	dung("dong Ngay dien tay", h.count("Ngày: ....") == 3)
	dung("co NSX", "09:30 03/10/2026" in h)
	dung("co HSD theo gio", "09:30 05/10/2026" in h)
	dung("bao quan", "BẢO QUẢN MÁT 0 - 5°C" in h)
	dung("di ung", "Sữa, trứng" in h)
	dung("ma lenh o chan tem", "MFG-WO-2026-00001" in h)
	dung("so thu tu tem", "3/3" in h)
	dung("ma vach", h.count("<svg class=\"b39s\"") == 3)


@ca("v560: chữ từ hồ sơ món được thoát, không chèn được thẻ vào tem")
def _thoat():
	h = T.html_tem(T.du_lieu_tem(dict(MON, item_name='<img src=x onerror=alert(1)>'), LUC))
	dung("khong co the img that", "<img" not in h)
	dung("con chu da thoat", "&lt;img" in h)


@ca("v560: mã vạch Code 39 chỉ lấy ký tự hợp lệ, luôn có dấu sao hai đầu")
def _ma_vach():
	a = T.ma_vach_svg("TP-0001")
	b = T.ma_vach_svg("tp-0001")
	la("khong phan biet hoa thuong", a, b)
	# 9 ky tu (*TP-0001*), moi ky tu 5 vach den
	la("so vach", a.count("<rect"), 9 * 5)
	la("bo ky tu la", T.ma_vach_svg("TP_0001").count("<rect"), 8 * 5)


@ca("Codex #421: chỉ đọc ô tự thêm khi site có, thiếu ô thì tem vẫn in")
def _truong_thieu():
	co = {"custom_han_dung_gio", "custom_dieu_kien_bao_quan"}
	ds = T.truong_doc_duoc(lambda f: f in co)
	dung("khong doc o site chua co", "custom_khoi_luong_tinh" not in ds and "custom_chat_gay_di_ung" not in ds)
	dung("van doc o chuan va o co that", {"name", "item_name", "shelf_life_in_days", "custom_han_dung_gio"} <= set(ds))
	la("site du o thi doc het", T.truong_doc_duoc(lambda f: True), T.TRUONG_MON)
	h = T.html_tem(T.du_lieu_tem({"name": "TP-1", "item_name": "X"}, LUC))
	dung("thieu ca KL va di ung van ra tem", h.count('<div class="tem">') == 1 and "Dị ứng" not in h)
