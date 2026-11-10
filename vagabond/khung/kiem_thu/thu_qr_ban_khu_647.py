# -*- coding: utf-8 -*-
"""v647 (anh Việt 10/11/2026): tên bàn theo khu (A1, B1, VIP1) và in QR bàn
đúng branding.

Anh chốt: mỗi điểm khai sơ đồ bàn một lần (khu + khoảng số), màn In QR tại bàn
và màn Tính tiền dùng chung; QR bàn số đã in trước đây vẫn quét được; đổi tên
khu thì QR cũ của khu đó hết dùng và máy báo trước khi lưu. Tờ in: mã đậm trên
ô trắng, nhãn "BÀN A1", quản lý nhập kích thước standee, máy dàn lên A4.

Ca dưới chạy THẬT so_do_ban (thuần), goi_mon_ban.mo_ban / goi / to_qr /
luu_so_do_ban / diem_in_qr và diem_ban (_chuan, giu_truong_rieng, dat_truong)
trên site giả của bộ v638. Màn hình chạy bằng node: hanh_vi/qr_ban_khu_647.js.
"""
import ast
import copy
import hashlib
import hmac
import json
import subprocess
from pathlib import Path
from unittest.mock import patch

from vagabond import diem_ban, so_do_ban as S
from vagabond import goi_mon_ban as g
from vagabond.khung.kiem_thu import thu_goi_mon_ban_638 as T
from vagabond.khung.kiem_thu.nen import ca, dung, la, nem

GOC = Path(__file__).resolve().parents[3]
KHOA = T.KHOA
SO_DO = [{"khu": "A", "tu": 1, "den": 12}, {"khu": "B", "tu": 1, "den": 8}, {"khu": "VIP", "tu": 1, "den": 2}]


def _cfg(so_do=None, dia_chi_qr=""):
	"""Cấu hình điểm bán đã lưu: TCV có sơ đồ bàn theo khu."""
	ds = copy.deepcopy(diem_ban.MAC_DINH)
	for d in ds:
		if d["ma"] == "TCV":
			d["so_do_ban"] = SO_DO if so_do is None else so_do
			d["dia_chi_qr"] = dia_chi_qr
	return json.dumps(ds, ensure_ascii=False)


# ------------------------------------------------------------ phần thuần

@ca("v647 tên bàn chuẩn: A1, a01, 'A 1', VIP-2, 'Bàn A1', bàn số giữ '5'; '-1', 100, A100, khu 5 chữ đều sai")
def _ten():
	la("chuẩn", [S.chuan_ten_ban(x) for x in ("5", " 05 ", 5, "a01", "A 1", "VIP-2", "Bàn A1", "bàn 12", "Sân3")],
		["5", "5", "5", "A1", "A1", "VIP2", "A1", "12", "SAN3"])
	la("sai", [S.chuan_ten_ban(x) for x in ("-1", "5a", "100", "0", "A100", "ABCDE1", "A0", None, "", " ", "A-")],
		[None] * 11)
	la("goi_mon_ban dùng cùng một luật", [g.chuan_ban(x) for x in ("a01", 7, "VIP 2")], ["A1", "7", "VIP2"])


@ca("v647 khai sơ đồ: chuẩn hoá khu có dấu, đảo khoảng gõ ngược, bỏ dòng trống; báo lỗi khu có số, số ngoài 1..99, bàn trùng, quá 99 bàn")
def _kiem():
	ra, loi = S.kiem_so_do([{"khu": "a", "tu": "12", "den": "1"}, {"khu": "", "tu": "", "den": ""}, {"khu": "Sân", "tu": 1, "den": 3},
		{"khu": "", "tu": 1, "den": 2}])
	la("chuẩn", (ra, loi), ([{"khu": "A", "tu": 1, "den": 12}, {"khu": "SAN", "tu": 1, "den": 3}, {"khu": "", "tu": 1, "den": 2}], []))
	la("khu có chữ số", S.kiem_so_do([{"khu": "A1", "tu": 1, "den": 2}])[1], ["Dòng 1: tên khu chỉ gồm chữ không dấu, tối đa 4 ký tự (ví dụ A, B, VIP)."])
	la("số ngoài khoảng", S.kiem_so_do([{"khu": "A", "tu": 0, "den": 2}])[1], ["Dòng 1: số bàn từ 1 tới 99."])
	la("trùng bàn", S.kiem_so_do([{"khu": "A", "tu": 1, "den": 5}, {"khu": "a", "tu": 5, "den": 9}])[1], ["Dòng 2: bàn A5 đã có ở dòng 1."])
	dung("quá 99 bàn", S.kiem_so_do([{"khu": "A", "tu": 1, "den": 99}, {"khu": "B", "tu": 1, "den": 1}])[1][-1].startswith("Tối đa 99 bàn"))
	la("cấu hình hỏng đọc ra rỗng, không nổ", S.chuan_so_do([{"khu": "A1", "tu": 1, "den": 2}]), [])


@ca("v647 nhóm bàn: chưa khai thì Bàn 1 tới 20; QR bàn số luôn dùng được, bàn theo khu chỉ khi còn trong sơ đồ; đổi sơ đồ liệt kê bàn mất")
def _nhom():
	la("mặc định", S.nhom_ban([]), [{"khu": "", "ban": [str(i) for i in range(1, 21)]}])
	la("theo khu", [(x["khu"], len(x["ban"]), x["ban"][-1]) for x in S.nhom_ban(SO_DO)], [("A", 12, "A12"), ("B", 8, "B8"), ("VIP", 2, "VIP2")])
	la("hai dòng cùng khu gộp một nhóm", S.nhom_ban([{"khu": "A", "tu": 1, "den": 2}, {"khu": "A", "tu": 5, "den": 5}]),
		[{"khu": "A", "ban": ["A1", "A2", "A5"]}])
	dung("bàn số cũ ở điểm đã khai khu", S.co_ban(SO_DO, "5"))
	dung("bàn trong sơ đồ", S.co_ban(SO_DO, "vip2"))
	dung("bàn khu không có", not S.co_ban(SO_DO, "C1") and not S.co_ban(SO_DO, "A13"))
	la("bỏ khu VIP, thu A còn 10", S.mat_khi_doi(SO_DO, [{"khu": "A", "tu": 1, "den": 10}, {"khu": "B", "tu": 1, "den": 8}]),
		["A11", "A12", "VIP1", "VIP2"])
	la("từ mặc định sang khu không mất gì (bàn số vẫn quét được)", S.mat_khi_doi([], SO_DO), [])
	la("nhãn in", [S.nhan_in(x) for x in ("a1", "5")], ["BÀN A1", "BÀN 5"])
	la("dòng giải thích", [S.mo_ta_dong(x) for x in SO_DO], ["A1 đến A12 · 12 bàn", "B1 đến B8 · 8 bàn", "VIP1, VIP2 · 2 bàn"])


@ca("v647 QR bàn số in trước v647 vẫn đúng: khoá và đường QR của bàn 5 trùng từng ký tự với công thức cũ")
def _tuong_thich():
	cu = hmac.new(KHOA.encode(), b"goi-mon-ban:TCV:5", hashlib.sha256).hexdigest()[:16]
	la("khoá bàn 5", g.khoa_ban(KHOA, "TCV", 5), cu)
	la("khoá bàn ' 05 '", g.khoa_ban(KHOA, "TCV", " 05 "), cu)
	la("đường QR", g.duong_qr("TCV", 5, cu), "/banh?diem=TCV&ban=5&k=%s#/in-store" % cu)
	k = g.khoa_ban(KHOA, "TCV", "A1")
	dung("bàn A1 khác bàn 1", k != g.khoa_ban(KHOA, "TCV", 1))
	la("đường QR theo khu", g.duong_qr("tcv", "a01", k), "/banh?diem=TCV&ban=A1&k=%s#/in-store" % k)
	dung("khoá A1 không mở được A2", not g.dung_khoa(KHOA, "TCV", "A2", k))


@ca("v647 chọn bàn in: theo thứ tự sơ đồ, bỏ trùng, bàn ngoài sơ đồ báo tên")
def _chon():
	la("thứ tự", g.ds_ban_chon(["VIP2", "a2", "A1", "A2", "B8"], SO_DO), (["A1", "A2", "B8", "VIP2"], []))
	la("chuỗi phẩy", g.ds_ban_chon("A1, B2", SO_DO)[0], ["A1", "B2"])
	la("ngoài sơ đồ", g.ds_ban_chon(["A1", "C1", "zz"], SO_DO), (["A1"], ["C1", "zz"]))


# ------------------------------------------------------------ trên site giả

@ca("v647 mở link QR: bàn theo khu trong sơ đồ mở được; khu không còn trong sơ đồ thì không; bàn số cũ vẫn mở")
def _mo():
	kho = T.Kho()
	with T._he(kho), patch.object(diem_ban, "cfg_o", return_value=_cfg()):
		r = g.mo_ban("TCV", "A1", g.khoa_ban(KHOA, "TCV", "A1"))
		la("A1", (r["ok"], r["ban"]), (1, "A1"))
		la("a01 gõ thường", g.mo_ban("TCV", "a01", g.khoa_ban(KHOA, "TCV", "A1"))["ban"], "A1")
		la("C1 ký đúng nhưng không có trong sơ đồ", g.mo_ban("TCV", "C1", g.khoa_ban(KHOA, "TCV", "C1")), {"ok": 0})
		la("bàn 5 in trước v647", g.mo_ban("TCV", "5", g.khoa_ban(KHOA, "TCV", 5))["ban"], "5")
	with T._he(kho), patch.object(diem_ban, "cfg_o", return_value=_cfg([{"khu": "B", "tu": 1, "den": 8}])):
		la("đổi sơ đồ bỏ khu A: QR A1 hết dùng", g.mo_ban("TCV", "A1", g.khoa_ban(KHOA, "TCV", "A1")), {"ok": 0})


@ca("v647 khách bàn A5 gọi món: đơn ghi bàn A5, thẻ quầy ghi A5; đơn cũ lưu số nguyên 5 vẫn đọc ra '5' và chống bấm hai lần đúng")
def _goi():
	kho = T.Kho()
	with T._he(kho), patch.object(diem_ban, "cfg_o", return_value=_cfg()):
		r = T._gui(nonce="A" * 32, ban="A5", k=g.khoa_ban(KHOA, "TCV", "A5"))
		la("gọi được", r["ok"], 1)
		d = kho.dong[r["ma"]]
		la("lưu tên bàn", d["ban"], "A5")
		la("thẻ quầy", g.the_quay(d, T.BAY, "District 1")["ban"], "A5")
		lai = T._gui(nonce="A" * 32, ban="a05", k=g.khoa_ban(KHOA, "TCV", "A5"))
		la("bấm lại cùng lần gửi, gõ khác kiểu: trả đơn cũ", (lai.get("lap_lai"), lai.get("ma")), (1, r["ma"]))
		d["ban"] = 5
		la("bản ghi cũ kiểu số", g.the_quay(d, T.BAY, "District 1")["ban"], "5")
		la("trạng thái cho khách", g.cho_khach(d, T.BAY)["ban"], "5")


@ca("v647 lưu sơ đồ bàn: lỗi khai thì báo đủ dòng; làm mất bàn đã in thì trả danh sách, đồng ý mới ghi; ghi giữ nguyên điểm và trường khác")
def _luu():
	ghi = []
	fr = T._fr
	with patch.object(fr, "get_roles", return_value=["VGB - Quản lý cửa hàng"], create=True), \
			patch.object(diem_ban, "cfg_o", side_effect=lambda k: ghi[-1] if ghi else _cfg()), \
			patch.object(fr.db, "set_single_value", side_effect=lambda dt, f, v: ghi.append(v), create=True), \
			patch.object(fr.db, "commit", lambda *a, **k: None, create=True), \
			patch.object(diem_ban, "_ghi_vet", lambda v: None):
		nem("khai sai", lambda: g.luu_so_do_ban("TCV", [{"khu": "A1", "tu": 1, "den": 2}]), Exception)
		r = g.luu_so_do_ban("TCV", json.dumps([{"khu": "A", "tu": 1, "den": 10}]), "9 Tran Cao Van, Sai Gon Ward")
		la("mất bàn: chưa ghi, trả danh sách", (r, ghi), ({"ok": 0, "mat": ["A11", "A12", "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "VIP1", "VIP2"]}, []))
		r = g.luu_so_do_ban("TCV", [{"khu": "a", "tu": 1, "den": 10}], "9 Tran Cao Van, Sai Gon Ward", dong_y_mat=1)
		la("đồng ý: ghi một lần", (r["ok"], len(ghi)), (1, 1))
		moi = {d["ma"]: d for d in json.loads(ghi[-1])}
		la("sơ đồ mới của TCV", (moi["TCV"]["so_do_ban"], moi["TCV"]["dia_chi_qr"]),
			([{"khu": "A", "tu": 1, "den": 10}], "9 Tran Cao Van, Sai Gon Ward"))
		cu = {d["ma"]: diem_ban._chuan(d) for d in diem_ban.MAC_DINH}
		la("điểm khác giữ nguyên", [moi[m] == dict(cu[m], so_do_ban=[], dia_chi_qr="") for m in cu if m != "TCV"], [True] * (len(cu) - 1))
		la("trường khác của TCV giữ nguyên", {k: v for k, v in moi["TCV"].items() if k not in ("so_do_ban", "dia_chi_qr")},
			{k: v for k, v in cu["TCV"].items() if k not in ("so_do_ban", "dia_chi_qr")})
		la("trả lại điểm cho màn", r["diem"]["nhom"], [{"khu": "A", "ban": ["A%d" % i for i in range(1, 11)]}])
	with patch.object(fr, "get_roles", return_value=["Sales User"], create=True):
		nem("nhân viên không có quyền", lambda: g.luu_so_do_ban("TCV", []), Exception)


@ca("v647 lưu danh sách điểm bán ở Cài đặt không xoá sơ đồ bàn: dòng không gửi trường riêng thì giữ của điểm đó")
def _giu():
	cu = [diem_ban._chuan(dict(diem_ban.MAC_DINH[0], so_do_ban=SO_DO, dia_chi_qr="9 TCV"))]
	ma = cu[0]["ma"]
	moi = diem_ban.giu_truong_rieng([{"ma": ma.lower(), "ten": "Đổi tên"}, {"ma": "MOI"}], cu)
	la("giữ sơ đồ và địa chỉ", (moi[0]["so_do_ban"], moi[0]["dia_chi_qr"], moi[0]["ten"]), (SO_DO, "9 TCV", "Đổi tên"))
	dung("điểm mới không có gì để giữ", "so_do_ban" not in moi[1])
	la("gửi rõ sơ đồ rỗng thì xoá", diem_ban.giu_truong_rieng([{"ma": ma, "so_do_ban": []}], cu)[0]["so_do_ban"], [])
	la("_chuan giữ sơ đồ đã chuẩn", diem_ban._chuan({"ma": "x", "so_do_ban": [{"khu": "vip", "tu": 2, "den": 1}]})["so_do_ban"],
		[{"khu": "VIP", "tu": 1, "den": 2}])
	src = (GOC / "vagabond/diem_ban.py").read_text(encoding="utf-8")
	ham = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "luu")
	dung("luu() gọi giu_truong_rieng trước khi chuẩn hoá", "diem = giu_truong_rieng(diem, ds())" in ast.unparse(ham))


@ca("v647 tờ QR theo bàn đã tích: nhãn BÀN A1, link ký đúng bàn, địa chỉ in; bàn ngoài sơ đồ thì chặn; không tích bàn vẫn in khoảng số như cũ")
def _to():
	ve = []
	fr = T._fr
	with patch.object(fr, "get_roles", return_value=["Giám đốc"], create=True), patch.object(g, "_bi_mat", return_value=KHOA), \
			patch.object(diem_ban, "cfg_o", return_value=_cfg(dia_chi_qr="9 Tran Cao Van, Sai Gon Ward")), \
			patch("vagabond.qr_chuyen_khoan.anh_lien_ket", side_effect=lambda u: ve.append(u) or "data:x"):
		kq = g.to_qr("TCV", ban=["VIP2", "A1"])
		la("thứ tự sơ đồ", [(t["ban"], t["nhan"]) for t in kq["to"]], [("A1", "BÀN A1"), ("VIP2", "BÀN VIP2")])
		dung("link ký đúng bàn", all(("ban=%s&k=%s" % (t["ban"], g.khoa_ban(KHOA, "TCV", t["ban"]))) in t["link"] for t in kq["to"]))
		la("địa chỉ in", kq["dia_chi_qr"], "9 Tran Cao Van, Sai Gon Ward")
		la("chuỗi JSON từ màn", [t["ban"] for t in g.to_qr("TCV", ban='["B2"]')["to"]], ["B2"])
		nem("bàn ngoài sơ đồ", lambda: g.to_qr("TCV", ban=["C1"]), Exception)
		nem("lẫn một bàn ngoài sơ đồ thì chặn cả lần in, không in thiếu", lambda: g.to_qr("TCV", ban=["A1", "C1"]), Exception)
		la("khoảng số như cũ", [t["ban"] for t in g.to_qr("TCV", 1, 3)["to"]], ["1", "2", "3"])
		d = next(x for x in g.diem_in_qr() if x["ma"] == "TCV")
		la("màn In QR nhận sơ đồ", (d["da_khai"], d["so_do"], [x["khu"] for x in d["nhom"]], d["dia_chi_qr"]),
			(1, SO_DO, ["A", "B", "VIP"], "9 Tran Cao Van, Sai Gon Ward"))


@ca("v647 cấu hình màn Tính tiền gửi nhóm bàn theo khu của từng điểm (cùng sơ đồ màn In QR)")
def _cau_hinh():
	# ban_hang kéo requests ở đầu tệp nên bộ kiểm tầng khung không nạp được cả
	# mô đun (xem _nap_bh của v638); đọc cây cú pháp của đúng hàm.
	src = (GOC / "vagabond/ban_hang.py").read_text(encoding="utf-8")
	ham = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "cau_hinh_ban_hang")
	dung("diem_ds có nhom_ban từ so_do_ban.nhom_ban", "'nhom_ban': so_do_ban.nhom_ban(d.get('so_do_ban'))" in ast.unparse(ham))
	la("điểm chưa khai ra 20 bàn số", len(S.nhom_ban(diem_ban._chuan(diem_ban.MAC_DINH[0]).get("so_do_ban"))[0]["ban"]), 20)


@ca("v647 trường bàn của hai doctype đổi Số nguyên sang Chữ (chứa A1), đẩy mốc modified")
def _doctype():
	for ten in ("vagabond_goi_mon_ban", "vagabond_goi_nhan_vien"):
		d = json.loads((GOC / ("vagabond/vagabond/doctype/%s/%s.json" % (ten, ten))).read_text())
		f = next(x for x in d["fields"] if x["fieldname"] == "ban")
		la(ten, (f["fieldtype"], f.get("length"), d["modified"] >= "2026-11-10"), ("Data", 10, True))


@ca("v647 màn In QR, chip Số bàn, link trang khách (node, mã nguồn thật): hanh_vi/qr_ban_khu_647.js")
def _node():
	r = subprocess.run(["node", str(GOC / "vagabond/khung/kiem_thu/hanh_vi/qr_ban_khu_647.js")], capture_output=True, text=True, timeout=180)
	la("qr_ban_khu_647.js", (r.returncode, r.stdout[-600:] if r.returncode else ""), (0, ""))
