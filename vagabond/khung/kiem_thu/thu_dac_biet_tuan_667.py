# -*- coding: utf-8 -*-
"""v667 (anh Việt duyệt 17/11/2026): tab "Đặc biệt tuần này" trên trang /banh.

Ca dưới chạy THẬT dac_biet_tuan (phép thuần), noi_dung_web.chuan_hoa với khối
đợt, và don_hang.tao_don THẬT trên môi trường giả của bộ ca #367 để chứng minh
máy chủ chặn đơn có món của đợt: chưa mở, đã chốt, sai ngày giao, quá số lượng
(đếm SAU khoá đợt, sau khi kết thúc giao dịch đọc cũ). Phần trang khách (lịch,
nút, băng chuyền) kiểm bằng node: hanh_vi/dac_biet_tuan_667.mjs, cùng bảng mẫu
trạng thái ở ca _cung_luat_js.
"""
import contextlib
import copy
import json
import os
import subprocess
import unittest.mock as um

from vagabond import dac_biet_tuan as dbt
from vagabond import noi_dung_web as nw
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _dot(**k):
	d = {"id": "dbt-1", "loai": "dac_biet_tuan", "vi_tri": "dac_biet_tuan", "hien": True, "nhan": "CHỈ CUỐI TUẦN",
		"tieu_de": "CUỐI TUẦN\n21 · 22/11", "noi_dung": "Món đặc biệt của tuần này.", "bat_dau": "2026-11-15", "ket_thuc": "2026-11-22",
		"mo_don": "2026-11-16T08:00", "chot_don": "2026-11-20T20:00", "ngay_giao": ["2026-11-22", "2026-11-21"],
		"dem_nguoc": "1", "dem_chu_1": "còn lại để đặt", "dem_chu_2": "Chốt hết thứ sáu 20/11",
		"moc": [{"nhan": "MỞ ĐƠN", "chu_ngay": "T2 16/11", "luc": "2026-11-16T08:00"},
			{"nhan": "CHỐT ĐƠN", "chu_ngay": "T6 20/11", "luc": "2026-11-20T20:00"},
			{"nhan": "GIAO NHẬN", "chu_ngay": "T7 · CN", "luc": "2026-11-21T08:00"}],
		"mon_dt": [{"khoa": "Candle", "mo_ta": "Vani", "anh": "", "nhan_goc": "", "toi_da": "2"}]}
	d.update(k)
	return d


def _loi(ham, *a):
	try:
		ham(*a)
	except ValueError as e:
		return str(e)
	return ""


@ca("v667 đợt cuối tuần: chuẩn hoá đúng (khoá bánh thường, ngày giao xếp, giờ bỏ giây) và chặn từng ô nhập sai bằng câu nói việc cần sửa")
def _chuan():
	k = dbt.chuan_dot(_dot(mo_don="2026-11-16 08:00:59"))
	la("khoá bánh viết thường", k["mon_dt"][0]["khoa"], "candle")
	la("ngày giao xếp tăng", k["ngay_giao"], ["2026-11-21", "2026-11-22"])
	la("giờ mở bỏ giây, chuẩn chữ T", k["mo_don"], "2026-11-16T08:00")
	sai = {
		"chốt trước mở": _dot(chot_don="2026-11-16T08:00"),
		"giờ không có thật 30/02": _dot(chot_don="2026-02-30T20:00"),
		"thiếu giờ mở": _dot(mo_don=""),
		"một mốc": _dot(moc=[_dot()["moc"][0]]),
		"sáu mốc": _dot(moc=_dot()["moc"] * 2),
		"mốc ngược giờ": _dot(moc=list(reversed(_dot()["moc"]))),
		"mốc thiếu nhãn": _dot(moc=[dict(_dot()["moc"][0], nhan=""), _dot()["moc"][1]]),
		"không ngày giao": _dot(ngay_giao=[]),
		"ngày giao trước ngày mở": _dot(ngay_giao=["2026-11-15"]),
		"không món": _dot(mon_dt=[]),
		"bánh chọn hai lần": _dot(mon_dt=[{"khoa": "candle"}, {"khoa": "CANDLE"}]),
		"số tối đa có chữ": _dot(mon_dt=[{"khoa": "candle", "toi_da": "30 cái"}]),
		"số tối đa 0": _dot(mon_dt=[{"khoa": "candle", "toi_da": "0"}]),
		"ảnh svg": _dot(mon_dt=[{"khoa": "candle", "anh": "/files/a.svg"}]),
		"ảnh riêng tư": _dot(mon_dt=[{"khoa": "candle", "anh": "/private/files/a.jpg"}]),
		"ảnh http": _dot(mon_dt=[{"khoa": "candle", "anh": "http://x.vn/a.jpg"}]),
		"trường lạ trong món": _dot(mon_dt=[{"khoa": "candle", "gia": "1"}]),
		"tiêu đề ba dòng": _dot(tieu_de="A\nB\nC"),
		"đếm ngược giá trị lạ": _dot(dem_nguoc="co"),
	}
	for ten, d in sai.items():
		dung("chặn: " + ten, _loi(dbt.chuan_dot, d) != "")
	la("câu lỗi nói việc cần sửa", _loi(dbt.chuan_dot, _dot(chot_don="2026-11-16T07:00")), "Giờ chốt đơn phải sau giờ mở đơn.")
	la("số tối đa trống là không giới hạn, có dấu chấm nghìn vẫn nhận", [dbt.chuan_dot(_dot(mon_dt=[{"khoa": "a", "toi_da": ""}]))["mon_dt"][0]["toi_da"],
		dbt.chuan_dot(_dot(mon_dt=[{"khoa": "a", "toi_da": "1.000"}]))["mon_dt"][0]["toi_da"]], ["", "1000"])


@ca("v667 đợt cuối tuần đi qua cửa lưu nội dung web (chuan_hoa): nhận khối đợt, chặn trường đợt ở khối khác và trường thiết kế riêng ở khối đợt")
def _cua_luu():
	nd = copy.deepcopy(nw.MAC_DINH)
	nd["khoi"].append(_dot())
	ra = nw.chuan_hoa(json.dumps(nd))
	k = [x for x in ra["khoi"] if x["loai"] == "dac_biet_tuan"][0]
	la("đã chuẩn hoá qua chuan_dot", (k["mon_dt"][0]["khoa"], k["ngay_giao"][0]), ("candle", "2026-11-21"))
	nd2 = copy.deepcopy(nw.MAC_DINH)
	nd2["khoi"].append({"id": "bn", "loai": "banner", "vi_tri": "gio_hang", "hien": False, "tieu_de": "x", "moc": []})
	dung("banner mang trường mốc: chặn", _loi(nw.chuan_hoa, nd2) != "")
	nd3 = copy.deepcopy(nw.MAC_DINH)
	nd3["khoi"].append(_dot(kich_co=[]))
	dung("đợt mang trường size: chặn", _loi(nw.chuan_hoa, nd3) != "")
	nd4 = copy.deepcopy(nw.MAC_DINH)
	nd4["khoi"].append(_dot(tieu_de=""))
	dung("đợt không tên: chặn", _loi(nw.chuan_hoa, nd4) != "")
	la("nhãn trạng thái trình biên tập", [nw.trang_thai_muc(_dot(), d)[1] for d in ("2026-11-14", "2026-11-17", "2026-11-23")],
		["Chưa tới ngày hiện", "Đang hiện", "Đã hết hạn"])


@ca("v667 đợt cuối tuần: trạng thái đúng mốc (đúng giờ mở là mở, đúng giờ chốt là chốt), đợt đang hiện, luật đơn và số lượng")
def _luat():
	d = dbt.chuan_dot(_dot())
	la("trạng thái", [dbt.trang_thai(d, x) for x in ("2026-11-16T07:59", "2026-11-16T08:00", "2026-11-20T19:59", "2026-11-20T20:00")],
		["chua_mo", "mo", "mo", "da_chot"])
	la("đợt đang hiện: bỏ đợt tắt, chưa tới ngày, qua ngày; lấy đợt đầu còn hiện",
		[dbt.dot_dang_hien([_dot(hien=False)], "2026-11-17"), dbt.dot_dang_hien([_dot(bat_dau="2026-11-18")], "2026-11-17"),
		dbt.dot_dang_hien([_dot(ket_thuc="2026-11-16")], "2026-11-17"), dbt.dot_dang_hien([_dot(hien=False), _dot(id="b")], "2026-11-17")["id"]],
		[None, None, None, "b"])
	mk = {"candle": {"C12", "C16"}}
	hang = [{"ma": "C12", "sl": 1}, {"ma": "KHAC", "sl": 3}]
	la("không có đợt hay không có món của đợt: không chặn", [dbt.kiem_don(None, hang, mk, "2026-11-21T10:00", "2026-11-17T10:00"),
		dbt.kiem_don(d, [{"ma": "KHAC", "sl": 1}], mk, "2026-11-19T10:00", "2026-11-21T10:00")], [None, None])
	la("chưa mở, đã chốt, sai ngày, đúng", [dbt.kiem_don(d, hang, mk, "2026-11-21T10:00:00", "2026-11-16T07:00"),
		dbt.kiem_don(d, hang, mk, "2026-11-21T10:00:00", "2026-11-20T20:00"), dbt.kiem_don(d, hang, mk, "2026-11-19T10:00:00", "2026-11-17T10:00"),
		dbt.kiem_don(d, hang, mk, "2026-11-22T10:00:00", "2026-11-17T10:00"), dbt.kiem_don(d, hang, mk, None, "2026-11-17T10:00")],
		[dbt.CHUA_MO, dbt.DA_CHOT, dbt.SAI_NGAY, None, dbt.SAI_NGAY])
	snap = [json.dumps({"mon": [{"ma": "C12", "sl": 1}, {"ma": "KHAC", "sl": 5}]}), {"mon": [{"ma": "C16", "sl": 1}]}, "{hỏng", None]
	la("đếm đã đặt cộng mọi size của bánh, bỏ ảnh chụp hỏng", dbt.dem_da_dat(snap, mk), {"candle": 2})
	la("đã đặt 1/2: thêm 1 được, thêm 2 vượt (còn 1)", [dbt.vuot_suat(d, [{"ma": "C12", "sl": 1}], mk, {"candle": 1}),
		dbt.vuot_suat(d, [{"ma": "C16", "sl": 2}], mk, {"candle": 1})], [[], [{"khoa": "candle", "con": 1}]])
	la("không giới hạn thì không vượt", dbt.vuot_suat(dbt.chuan_dot(_dot(mon_dt=[{"khoa": "candle"}])), [{"ma": "C12", "sl": 99}], mk, {"candle": 99}), [])


@ca("v667 đợt cuối tuần: luật trang khách (dbt-thuan.js) trùng luật máy chủ trên cùng bảng mẫu giờ và ngày")
def _cung_luat_js():
	luc = ["2026-11-16T07:59", "2026-11-16T08:00", "2026-11-20T19:59", "2026-11-20T20:00", "2026-11-21T00:00"]
	ngay = ["2026-11-17", "2026-11-14", "2026-11-23"]
	d = dbt.chuan_dot(_dot())
	may = {"tt": [dbt.trang_thai(d, x) for x in luc], "hien": [bool(dbt.dot_dang_hien([d], n)) for n in ngay]}
	js = """import * as D from %s;
const d = JSON.parse(process.argv[process.argv.length - 1]);
console.log(JSON.stringify({tt: %s.map(x => D.trangThaiDot(d, x)), hien: %s.map(n => !!D.dotDangHien([d], n))}));""" % (
		json.dumps("file://" + os.path.join(GOC, "vagabond/public/web_vue/banh/dbt-thuan.js")), json.dumps(luc), json.dumps(ngay))
	r = subprocess.run(["node", "--input-type=module", "-e", js, json.dumps(d)], capture_output=True, text=True, timeout=60)
	la("node chạy được", (r.returncode, r.stderr[-300:]), (0, ""))
	la("trang khách trùng máy chủ", json.loads(r.stdout), may)


@ca("v667 đợt cuối tuần: chạy thật hanh_vi/dac_biet_tuan_667.mjs (lịch, nút, số lượng, băng chuyền) đều đạt")
def _node():
	r = subprocess.run(["node", os.path.join(GOC, "vagabond/khung/kiem_thu/hanh_vi/dac_biet_tuan_667.mjs")],
		capture_output=True, text=True, timeout=120)
	la("dac_biet_tuan_667.mjs", (r.returncode, (r.stdout or "")[-600:] if r.returncode else ""), (0, ""))
	dung("đủ 14 ca", "14 đạt, 0 hỏng" in r.stdout)


@ca("v667 Robin egg tới máy khách: mọi ?v= trên mọi trang www và trang cũ khớp nội dung tệp (trang /banh từng trỏ nen.css, khoi.css cũ nên khách vẫn thấy teal)")
def _ma_bam_moi_trang():
	import glob
	import hashlib
	import re
	so = 0
	for f in sorted(glob.glob(os.path.join(GOC, "vagabond/www/**/*.html"), recursive=True) + glob.glob(os.path.join(GOC, "vagabond/trang/*.html"))):
		s = open(f, encoding="utf-8").read()
		for duong, ma in re.findall(r"/assets/vagabond/([\w./-]+\.(?:css|js|png|jpe?g|webp|svg|woff2?))\?v=([0-9a-f]+)", s):
			p = os.path.join(GOC, "vagabond/public", duong)
			if not os.path.isfile(p):
				continue
			so += 1
			la(os.path.relpath(f, GOC) + ": " + duong, ma, hashlib.sha256(open(p, "rb").read()).hexdigest()[:12])
	dung("dò được nhiều tệp", so > 60)
	r = subprocess.run(["python3", "cong_cu/ma_bam_web_vue.py", "--kiem"], cwd=GOC, capture_output=True, text=True, timeout=60)
	m = re.search(r"(\d+) trang", r.stdout)
	la("công cụ đóng dấu khớp và soát cả trang www ngoài web_moi", (r.returncode, bool(m) and int(m.group(1)) > 4), (0, True))


# ------------------------------------------------------------ tao_don THẬT

def _tao(dot, luc, ngay, da_dat=None, hang=None, luc_sau=None, dot_sau=None):
	"""luc_sau, dot_sau: giờ và nội dung đợt ĐỔI trong lúc đơn chờ khoá đợt
	(khách bấm 19:59, lấy được khoá lúc 20:01; Marketing sửa đợt giữa chừng)."""
	from vagabond.khung.kiem_thu import thu_don_web_367 as t367

	vet, tao_don = t367._moi_truong_tao_don(lambda v: t367._Tra(200, {"data": {"id": "91500"}}))
	thu_tu = []
	bay_gio = {"luc": luc, "dot": dot}

	@contextlib.contextmanager
	def khoa_suat(d):
		thu_tu.append("khoa_dot")
		vet.su.append("khoa_dot")
		if luc_sau:
			bay_gio["luc"] = luc_sau
		if dot_sau:
			bay_gio["dot"] = dot_sau
		yield
		thu_tu.append("mo_khoa_dot")
		vet.su.append("mo_khoa_dot")

	def dem(d, mk):
		# Đếm phải chạy SAU khoá đợt và SAU khi kết thúc giao dịch đọc cũ.
		thu_tu.append(("dem", "commit" in vet.su))
		return dict(da_dat or {})

	don = t367._don(ngay_nhan=ngay)
	if hang is not None:
		don["items"] = hang
	with um.patch.object(dbt, "dot_cong_khai", lambda: bay_gio["dot"]), \
			um.patch.object(dbt, "ma_theo_khoa", lambda d: {"candle": {"BAWC00139", "BAWC00140"}}), \
			um.patch.object(dbt, "luc_vn", lambda: bay_gio["luc"]), um.patch.object(dbt, "khoa_suat", khoa_suat), \
			um.patch.object(dbt, "da_dat", dem):
		r = tao_don(json.dumps(don))
	return r, vet, thu_tu


@ca("v667 cửa tạo đơn THẬT: món của đợt bị chặn khi chưa mở, đã chốt, sai ngày giao, không ghi đơn; đúng ngày thì ghi; bánh khác không bị đợt chặn")
def _cua_tao_don():
	from vagabond.khung.kiem_thu import thu_don_web_367 as t367
	d = dbt.chuan_dot(_dot(mon_dt=[{"khoa": "candle"}]))
	co = [{"variation_id": "BAWC00139", "quantity": 1}]
	for luc, ngay, ly in (("2026-11-16T07:00", "2026-11-21T10:00:00", dbt.CHUA_MO), ("2026-11-20T20:00", "2026-11-21T10:00:00", dbt.DA_CHOT),
			("2026-11-17T10:00", "2026-11-19T10:00:00", dbt.SAI_NGAY)):
		r, vet, _ = _tao(d, luc, ngay, hang=co)
		la("từ chối " + ly, (r.get("ok"), r.get("ly_do")), (0, ly))
		dung(ly + ": không ghi đơn, không gửi Pancake", "ghi" not in vet.su and "post" not in vet.su)
	la("sai ngày: trả các ngày giao để trang nhắc", _tao(d, "2026-11-17T10:00", "2026-11-19T10:00:00", hang=co)[0].get("ngay_giao"), ["2026-11-21", "2026-11-22"])
	r, vet, _ = _tao(d, "2026-11-17T10:00", "2026-11-21T10:00:00", hang=co)
	la("đúng ngày giao: ghi đơn", (r.get("ok"), "ghi" in vet.su), (1, True))
	r, vet, thu = _tao(d, "2026-11-20T21:00", "2026-11-19T10:00:00", hang=[{"variation_id": "BAWC00135", "quantity": 1}])
	la("bánh khác sau giờ chốt, ngày thường: vẫn ghi, không khoá đợt", (r.get("ok"), thu), (1, []))
	dung("bộ ca gốc #367 vẫn dùng được", hasattr(t367, "_moi_truong_tao_don"))


@ca("v667 cửa tạo đơn THẬT: số lượng tối đa đếm dưới khoá đợt, sau commit đọc cũ; đủ suất thì từ chối, không ghi; còn suất thì ghi trong khoá")
def _suat_duoi_khoa():
	d = dbt.chuan_dot(_dot(mon_dt=[{"khoa": "candle", "toi_da": "2"}]))
	co = [{"variation_id": "BAWC00140", "quantity": 1}]
	r, vet, thu = _tao(d, "2026-11-17T10:00", "2026-11-21T10:00:00", da_dat={"candle": 2}, hang=co)
	la("đủ 2/2: từ chối hết suất", (r.get("ok"), r.get("ly_do"), r.get("nhac")), (0, dbt.HET_SUAT, [{"khoa": "candle", "con": 0}]))
	dung("không ghi đơn", "ghi" not in vet.su)
	la("đếm sau khi khoá đợt và đã commit kết thúc giao dịch đọc cũ", thu[:2], ["khoa_dot", ("dem", True)])
	r, vet, thu = _tao(d, "2026-11-17T10:00", "2026-11-21T10:00:00", da_dat={"candle": 1}, hang=co)
	la("1/2: ghi đơn", r.get("ok"), 1)
	su = [x for x in vet.su if x in ("khoa_dot", "ghi", "commit", "mo_khoa_dot", "post")]
	dung("ghi đơn và commit nằm TRONG khoá đợt, gửi Pancake sau khi mở khoá: " + str(su),
		su.index("khoa_dot") < su.index("ghi") < su.index("commit", su.index("ghi")) < su.index("mo_khoa_dot") < su.index("post"))
	r, vet, thu = _tao(dbt.chuan_dot(_dot(mon_dt=[{"khoa": "candle"}])), "2026-11-17T10:00", "2026-11-21T10:00:00", hang=co)
	la("không giới hạn: vẫn khoá đợt (xét lại giờ chốt), không đếm", (r.get("ok"), thu), (1, ["khoa_dot", "mo_khoa_dot"]))


@ca("v667 cửa tạo đơn THẬT (Codex #579): bấm 19:59, chờ khoá tới 20:01 thì từ chối Đã chốt, không ghi, không gửi; có hay không số lượng tối đa; Marketing sửa giờ chốt giữa chừng cũng áp")
def _xet_lai_duoi_khoa():
	co = [{"variation_id": "BAWC00139", "quantity": 1}]
	for ten, mon in (("không giới hạn", [{"khoa": "candle"}]), ("có số tối đa", [{"khoa": "candle", "toi_da": "5"}])):
		d = dbt.chuan_dot(_dot(mon_dt=mon))
		r, vet, thu = _tao(d, "2026-11-20T19:59", "2026-11-21T10:00:00", da_dat={"candle": 0}, hang=co, luc_sau="2026-11-20T20:01")
		la(ten + ": qua giờ chốt lúc lấy được khoá thì từ chối", (r.get("ok"), r.get("ly_do"), r.get("ngay_giao")),
			(0, dbt.DA_CHOT, ["2026-11-21", "2026-11-22"]))
		dung(ten + ": không ghi đơn, không gửi Pancake", "ghi" not in vet.su and "post" not in vet.su)
		dung(ten + ": không đếm suất khi đã chốt", not [x for x in thu if isinstance(x, tuple)])
		r, vet, _ = _tao(d, "2026-11-20T19:58", "2026-11-21T10:00:00", da_dat={"candle": 0}, hang=co, luc_sau="2026-11-20T19:59")
		la(ten + ": vẫn trong giờ lúc lấy khoá thì ghi", (r.get("ok"), "ghi" in vet.su), (1, True))
	d = dbt.chuan_dot(_dot(mon_dt=[{"khoa": "candle"}]))
	sua = dict(d, chot_don="2026-11-18T12:00")
	r, vet, _ = _tao(d, "2026-11-18T12:30", "2026-11-21T10:00:00", hang=co, dot_sau=sua)
	la("Marketing dời giờ chốt sớm hơn giữa chừng: đọc lại đợt dưới khoá, từ chối", (r.get("ok"), r.get("ly_do"), "ghi" in vet.su), (0, dbt.DA_CHOT, False))
	r, vet, _ = _tao(d, "2026-11-18T12:30", "2026-11-21T10:00:00", hang=co, dot_sau=None)
	la("đợt không đổi: ghi", (r.get("ok"), "ghi" in vet.su), (1, True))
	r, vet, _ = _tao(d, "2026-11-20T19:59", "2026-11-21T10:00:00", hang=co, luc_sau="2026-11-20T20:01", dot_sau=dict(d, id="dot-khac", chot_don="2026-11-27T20:00", ngay_giao=["2026-11-28"]))
	la("đợt bị thay bằng đợt khác giữa chừng: vẫn xét theo đợt khách đã đặt", (r.get("ok"), r.get("ly_do")), (0, dbt.DA_CHOT))
