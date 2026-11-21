# -*- coding: utf-8 -*-
"""v681 (BẢN 2, anh Việt duyệt 21/11/2026): lời chúc, cờ, thiệp theo TỪNG CHIẾC
bánh và ghi chú chọn nhanh của đơn web.

Pancake gộp dòng cùng mã món, nên nội dung từng chiếc đi qua ghi chú in (trang
khách dựng, ca ở hanh_vi/web_vue_banh.mjs) và ảnh chụp đơn web (khoá chiec).
Ở đây: máy chủ CHỐT số thiệp ép kim BAPK00002 bằng đúng số chiếc chọn ép kim
(không tin số trình duyệt gửi), chỉ nhận chiếc của món có trong giỏ, ghi ảnh
chụp, và mã viên ghi chú trùng trang khách. tao_don là hàm THẬT nạp từ mã
nguồn bằng bộ khung của ca #367.
"""

import json
import re
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la

gia_lap()

from vagabond import chiec_banh as cb  # noqa: E402

GOC = Path(__file__).resolve().parents[3]
BANH = {"variation_id": "BAWC00139", "quantity": 2}


@ca("v681 chiếc bánh: chỉ nhận chiếc của món có trong giỏ, tối đa đúng số lượng; cắt lời chúc 60, lời thiệp 80; Không cần cờ thì không lời chúc")
def _():
	ds = [{"ma": "BAWC00139", "co": True, "loi_chuc": "  Chúc   mừng  ", "thiep": "ep_kim", "loi_thiep": "x" * 200, "ten": "Epi · Ø 12cm"},
		{"ma": "BAWC00139", "co": False, "loi_chuc": "không được giữ", "thiep": "la", "loi_thiep": "bỏ"},
		{"ma": "BAWC00139", "co": True, "loi_chuc": "chiếc thứ ba, giỏ chỉ có hai"},
		{"ma": "KHONG_CO", "co": True, "loi_chuc": "món lạ"}, {"ma": "BAPK00002"}, "rac"]
	ra = cb.chuan_chiec(ds, [BANH])
	la("hai chiếc", len(ra), 2)
	la("chiếc 1", (ra[0]["loi_chuc"], ra[0]["thiep"], len(ra[0]["loi_thiep"]), ra[0]["ten_web"]), ("Chúc mừng", "ep_kim", 80, "Epi · Ø 12cm"))
	la("chiếc 2 không cờ, loại thiệp lạ về không thiệp", (ra[1]["co"], ra[1]["loi_chuc"], ra[1]["thiep"], ra[1]["loi_thiep"]), (False, "", "khong", ""))
	la("lời chúc dài cắt 60", len(cb.chuan_chiec([{"ma": "BAWC00139", "loi_chuc": "a" * 99}], [BANH])[0]["loi_chuc"]), 60)
	la("trang cũ không gửi khoá chiec", cb.chuan_chiec(None, [BANH]), None)
	la("gửi sai kiểu", cb.chuan_chiec("x", [BANH]), [])


@ca("v681 thiệp ép kim: máy chủ chốt BAPK00002 bằng đúng số chiếc ép kim, kể cả khi trình duyệt gửi số khác; không chiếc nào thì bỏ dòng; trang cũ giữ nguyên")
def _():
	hang = [BANH, {"variation_id": "BAPK00002", "quantity": 5}, {"variation_id": "BAPK00005", "quantity": 2}]
	mot = [{"thiep": "ep_kim"}, {"thiep": "nho"}]
	la("đúng một", cb.chot_thiep_ep_kim(hang, mot), [BANH, {"variation_id": "BAPK00005", "quantity": 2}, {"variation_id": "BAPK00002", "quantity": 1}])
	la("không chiếc nào ép kim: bỏ dòng", cb.chot_thiep_ep_kim(hang, [{"thiep": "nho"}]), [BANH, {"variation_id": "BAPK00005", "quantity": 2}])
	la("trang cũ không gửi chiếc: giữ như trình duyệt gửi", cb.chot_thiep_ep_kim(hang, None), hang)
	la("đếm thiệp nhỏ", cb.so_thiep_nho(mot), 1)


@ca("v681 ghi chú chọn nhanh: mã cố định trùng trang khách; Tự lấy bỏ viên giao hàng; giờ trễ nhất chỉ nhận HH:MM khi chọn viên đó")
def _():
	js = (GOC / "vagabond/public/web_vue/banh/du-lieu.js").read_text(encoding="utf-8")
	la("cùng mã, cùng thứ tự", tuple(re.findall(r"\{ma: '([a-z_]+)', k: 'gc_", js)), cb.MA_GHI_CHU_NHANH)
	giao = tuple(m for m in re.findall(r"\{ma: '([a-z_]+)', k: 'gc_[a-z_]+', n: '[^']*', giao: true", js))
	la("viên giao hàng trùng", giao, cb.MA_GHI_CHU_GIAO)
	la("giữ thứ tự cố định, bỏ mã lạ", cb.chuan_ghi_chu_nhanh(["di_ung", "la", "goi_truoc"], False), ["goi_truoc", "di_ung"])
	la("tự lấy chỉ còn dị ứng", cb.chuan_ghi_chu_nhanh(["goi_truoc", "chup_hinh", "di_ung"], True), ["di_ung"])
	la("giờ hợp lệ", cb.chuan_gio_tre("15:30", ["gio_tre_nhat"]), "15:30")
	la("không chọn viên thì bỏ giờ", cb.chuan_gio_tre("15:30", ["goi_truoc"]), "")
	la("giờ lạ", (cb.chuan_gio_tre("25:00", ["gio_tre_nhat"]), cb.chuan_gio_tre("<b>", ["gio_tre_nhat"])), ("", ""))


@ca("v681 tao_don THẬT: trình duyệt gửi 3 thiệp ép kim mà chỉ một chiếc chọn ép kim thì Pancake và ảnh chụp nhận một; ảnh chụp có từng chiếc với tên web lúc đặt và mã viên ghi chú")
def _():
	from vagabond.khung.kiem_thu.thu_don_web_367 import _Tra, _don, _moi_truong_tao_don
	vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "1"}}))
	kq = tao_don(_don(items=[BANH, {"variation_id": "BAPK00002", "quantity": 3}],
		chiec=[{"ma": "BAWC00139", "co": True, "loi_chuc": "Happy 30", "thiep": "ep_kim", "loi_thiep": "Thương em", "ten": "CANDLE · Ø 12cm"},
			{"ma": "BAWC00139", "co": False, "thiep": "nho"}],
		ghi_chu_nhanh=["goi_truoc", "gio_tre_nhat"], gio_tre_nhat="15:30"))
	la("đơn thành", kq.get("ok"), 1)
	la("Pancake nhận đúng một thiệp", [x["quantity"] for x in vet.body["items"] if x["variation_id"] == "uuid-BAPK00002"], [1])
	sn = json.loads(vet.truong["snapshot"])
	la("món chốt một thiệp", [m["sl"] for m in sn["mon"] if m["ma"] == "BAPK00002"], [1])
	la("từng chiếc", [(c["ma"], c["co"], c["loi_chuc"], c["thiep"], c["loi_thiep"], c["ten"]) for c in sn["chiec"]],
		[("BAWC00139", True, "Happy 30", "ep_kim", "Thương em", "CANDLE · Ø 12cm"), ("BAWC00139", False, "", "nho", "", "Bánh BAWC00139")])
	la("viên ghi chú", (sn["ghi_chu_nhanh"], sn["gio_tre_nhat"]), (["goi_truoc", "gio_tre_nhat"], "15:30"))


@ca("v681 tao_don THẬT: trang cũ (không gửi chiếc) giữ thiệp như cũ, ảnh chụp không có khoá chiec")
def _():
	from vagabond.khung.kiem_thu.thu_don_web_367 import _Tra, _don, _moi_truong_tao_don
	vet, tao_don = _moi_truong_tao_don(lambda v: _Tra(200, {"data": {"id": "1"}}))
	kq = tao_don(_don(items=[BANH, {"variation_id": "BAPK00002", "quantity": 2}]))
	la("đơn thành", kq.get("ok"), 1)
	la("giữ hai thiệp", [x["quantity"] for x in vet.body["items"] if x["variation_id"] == "uuid-BAPK00002"], [2])
	sn = json.loads(vet.truong["snapshot"])
	dung("không có khoá chiec", "chiec" not in sn)
	la("không viên ghi chú", sn["ghi_chu_nhanh"], [])


@ca("v681 cấu hình trang khách trả giá hiện hành của thiệp ép kim từ món BAPK00002; chưa có món thì None (trang dùng số tạm)")
def _():
	import frappe
	from vagabond import don_web
	cu = frappe.db.get_value
	try:
		frappe.db.get_value = lambda dt, ten, truong: 19000.0 if (dt, ten, truong) == ("Item", "BAPK00002", "standard_rate") else None
		la("giá", don_web.gia_thiep_ep_kim(), 19000)
		frappe.db.get_value = lambda *a: None
		la("chưa có món", don_web.gia_thiep_ep_kim(), None)
	finally:
		frappe.db.get_value = cu


@ca("v681 ô ảnh trong sổ nhãn: chỉ nhận ảnh /files/ PNG, JPG, WebP đã tải lên; để trống là về ảnh có sẵn; ô chữ không bị luật ảnh ảnh hưởng; lưu qua luu_nhan và chuan_hoa đều chặn")
def _():
	from vagabond import noi_dung_web as ndw
	o_anh = sorted(k for k, v in ndw.NHAN.items() if v.get("anh"))
	la("25 ô ảnh, nhóm Ảnh trên trang", (len(o_anh), {ndw.NHAN[k]["nhom"] for k in o_anh}, ndw._nhom_nhan()["anh"]), (25, {"anh"}, "Ảnh trên trang"))
	nd = {"khoi": [], "nhan": {}}
	moi = ndw.ap_nhan(nd, {"anh_co_mau": ["", "/files/web-1a2b3c.webp"], "anh_thiep_nho": ["", "/files/thiep.JPG".lower()]})
	la("nhận ảnh đã tải lên", (moi["nhan"]["anh_co_mau"], moi["nhan"]["anh_thiep_nho"]), ("/files/web-1a2b3c.webp", "/files/thiep.jpg"))
	ve = ndw.ap_nhan(moi, {"anh_co_mau": ["/files/web-1a2b3c.webp", ""]})
	dung("để trống là về ảnh có sẵn", "anh_co_mau" not in ve["nhan"] and ndw.nhan_day_du(ve)["anh_co_mau"] == "")
	for xau in ["https://evil.example/a.png", "/files/a.svg", "/files/../private/files/x.png", "/private/files/x.png", "javascript:alert(1)", "/files/a.png?x=1", "/files/ a.png", "/files/" + "a" * 200 + ".png"]:
		for cach in ("ap_nhan", "chuan_hoa"):
			try:
				if cach == "ap_nhan":
					ndw.ap_nhan(nd, {"anh_co_mau": ["", xau]})
				else:
					ndw.chuan_hoa({"khoi": [], "nhan": {"anh_co_mau": xau}})
				dung("phải chặn %s qua %s" % (xau, cach), False)
			except ValueError as e:
				dung("câu lỗi nói rõ ảnh", "PNG, JPG hoặc WebP" in str(e))
	# ô chữ thường vẫn như cũ (chữ có dấu cách, không phải đường dẫn)
	dung("ô chữ không bị luật ảnh", ndw.ap_nhan(nd, {"lc_thiep_nho": ["", "Thiệp mini"]})["nhan"]["lc_thiep_nho"] == "Thiệp mini")
