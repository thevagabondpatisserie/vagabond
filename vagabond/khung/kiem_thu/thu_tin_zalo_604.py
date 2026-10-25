"""v604: danh mục Tin nhận cho nhóm Zalo, bỏ thư cảnh báo nội bộ.

Anh Việt 18/10/2026: mọi tin nhắc việc, báo sự cố cho nhân viên đi qua nhóm
Zalo, KHÔNG còn email cảnh báo nội bộ. Mỗi nhóm trong Cài đặt có ô Tin nhận,
anh tích đúng tin nhóm đó cần. Bẫy của kiểu thiết kế này:

  - Một nơi gọi bao() quên truyền ma_tin thì nhóm đã tích Tin nhận KHÔNG BAO
    GIỜ nhận tin đó, mà không lớp nào kêu (bao() vẫn trả rỗng như khi chưa có
    nhóm). Ca dò mã nguồn chốt: mọi lời gọi có ma_tin, mã có trong danh mục,
    và mọi mã trong danh mục có ít nhất một nơi phát thật (bài học #452: loại
    tin hiện cho chọn mà không nơi nào phát).
  - Bản JS (hộp chọn trên Desk và app, đường báo của còi thư) lệch bản Python
    thì màn hình nói một đằng, máy chủ gửi một nẻo. Ca so từng chữ và chạy hai
    bản trên cùng ma trận nhóm.
  - Chuyển thư sang Zalo mà sót một frappe.sendmail là tin đi hai đường; ca soi
    AST từng hàm đã chuyển.

Các ca chạy hàm THẬT (nạp từ mã nguồn bằng nap), chỉ thay tầng Frappe và kênh
Zalo giả ghi lại lời gọi; không gọi thêm hàm nào ngoài chuỗi máy chạy (điều 15).
"""
import ast
import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.khung.kiem_thu.thu_su_co_290 import D, nap

# Bản Frappe giả chung chưa có get_url khi chạy lẻ tệp này (cùng cách thu_zalo_khong_nhom_597).
if not hasattr(sys.modules["frappe"].utils, "get_url"):
	sys.modules["frappe"].utils.get_url = lambda *a, **k: "https://vagabond.test"

import vagabond  # noqa: E402
from vagabond import kenh_zalo as kz  # noqa: E402

GOI = Path(__file__).resolve().parents[2]
REPO = GOI.parent

# Mỗi nơi phát -> mã tin phải truyền. Nguồn: danh sách anh Việt duyệt 18/10/2026
# (20 tin) cộng hai tin Zalo đã có sẵn mà danh sách chưa ghi (lệch tổng Pancake,
# phí giao Ahamove), để nhóm đã tích Tin nhận không mất hai tin đó.
NOI_PHAT = {
	("ban_hang.py", "bao_dong_ghi_so"): "hd_ket_ghi_so",
	("ban_hang.py", "canh_bao_don_treo"): "hd_don_chua_ghi_so",
	("ban_hang.py", "canh_bao_hddt_sot"): "hd_hddt_sot",
	("ban_hang.py", "_bao_hoan_phat_hanh"): "hd_giu_ngay_cu",
	("ban_hang.py", "ra_trung_hang_dem"): "hd_trung",
	("minvoice_chung_tu.py", "canh_bao_tac_nhip"): "hd_dau_vao",
	("cong_no_ncc.py", "lap_truoc_erp"): "kt_tra_truoc_erp",
	("hoan_tien.py", "_bao_ke_toan"): "kt_hoan_tien",
	("de_nghi_chi.py", "_bao_zalo"): "kt_de_nghi_chi",
	("tra_truoc.py", "_bao_ke_toan"): "kt_tra_truoc_kiem",
	("diem_han.py", "_bao_nguoi"): "kt_diem_het_han",
	("hop_dong_dieu_chinh.py", "_bao_giam_doc"): "kt_hop_dong_dc",
	("don_web.py", "_bao_sales"): "bh_don_web_treo",
	("ton_don_web.py", "bao_loi"): "bh_ton_web_loi",
	("van_don.py", "_bao_tai_xe_huy"): "bh_ahamove_huy",
	("dat_ban.py", "bao_dat_ban_moi"): "bh_dat_ban",
	("tiec_web.py", "bao_moi"): "bh_tiec",
	("don_hang.py", "_bao_lech_tong_pancake"): "bh_pancake_lech_tong",
	("giao_hang.py", "_ghi_canh_bao_ahamove"): "bh_ahamove_phi",
	("ke_hoach_sx.py", "nhac_bep_sang"): "bep_ke_hoach_sx",
	("gui_thu.py", "_bao_zalo"): "ht_email_loi",
	("zalo_phat_hanh.py", "quet"): "ht_phat_hanh",
	# v606: báo cáo cuối ngày cho chủ (anh Việt duyệt mẫu 20/10/2026).
	("bao_cao_chu.py", "gui_cuoi_ngay"): "bgd_bao_cao_ngay",
	# v609: kho, thu mua, sản xuất, đơn web (anh Việt duyệt mẫu 22/10/2026). Mỗi hàm
	# đúng một tin; khi_ghi_so_phieu_kho chỉ điều phối, không tự gọi bao().
	("tin_kho.py", "khi_co_yeu_cau_mua"): "tm_yeu_cau_mua",
	("tin_kho.py", "khi_ghi_so_don_mua"): "tm_don_mua_moi",
	("tin_kho.py", "nhac_don_mua_tre_hen"): "tm_don_mua_tre_hen",
	("tin_kho.py", "nhac_hang_ve_chua_hoa_don"): "tm_hang_ve_chua_hoa_don",
	("tin_kho.py", "khi_lap_phieu_nhap"): "kho_nhap_cho_kiem",
	("tin_kho.py", "khi_ghi_so_phieu_nhap"): "kho_da_nhap",
	("tin_kho.py", "khi_lap_phieu_kho"): "kho_huy_cho_ghi_so",
	("tin_kho.py", "_bao_da_chuyen"): "kho_da_chuyen",
	("tin_kho.py", "_bao_da_huy"): "kho_da_huy",
	("tin_kho.py", "_bao_ke_toan_gia_von_huy"): "kt_xuat_huy_gia_von",
	("tin_kho.py", "_bao_xuat_noi_bo"): "kho_xuat_noi_bo",
	("tin_kho.py", "_bao_bep_xuat_nvl"): "bep_lenh_sx_xuat_nvl",
	("tin_kho.py", "bao_da_nhan_chuyen"): "kho_da_nhan_chuyen",
	("tin_kho.py", "nhac_chuyen_chua_nhan"): "kho_chuyen_chua_nhan",
	("tin_kho.py", "khi_ghi_so_giao_si"): "kho_giao_si",
	("tin_kho.py", "khi_doi_phieu_kiem_ke"): "kho_kiem_ke_cho_duyet",
	("tin_kho.py", "bao_kiem_ke_da_ghi_so"): "kho_kiem_ke_da_ghi_so",
	("tin_kho.py", "bao_ke_toan_kiem_ke_lech"): "kt_kiem_ke_lech",
	("tin_kho.py", "nhac_lo_sap_het_han"): "kho_lo_sap_het_han",
	("tin_kho.py", "nhac_ton_duoi_muc"): "kho_ton_duoi_muc",
	("tin_kho.py", "bao_don_web_moi"): "bh_don_web_moi",
	# v611: đặt bàn, hoá đơn sai, tiền chưa gắn, sản xuất và điều chuyển (anh Việt
	# duyệt 25/10/2026, cùng lúc tắt thư báo YCSX, YCDC, YCMH nội bộ).
	("dat_ban.py", "_bao_xac_nhan"): "bh_dat_ban_xac_nhan",
	("dat_ban.py", "_bao_huy"): "bh_dat_ban_huy",
	("dat_ban.py", "nhac_sap_toi"): "bh_dat_ban_sap_toi",
	("tin_ban_hang.py", "bao_thong_tin_hd_sai"): "bh_thong_tin_hd_sai",
	("tin_ban_hang.py", "nhac_tien_chua_gan"): "kt_tien_chua_gan",
	("tin_kho.py", "khi_co_yeu_cau_sx"): "bep_ycsx_moi",
	("tin_kho.py", "khi_huy_yeu_cau_sx"): "bep_ycsx_huy",
	("tin_kho.py", "nhac_ycsx_ngay_mai"): "bep_ycsx_ngay_mai",
	("tin_kho.py", "khi_co_yeu_cau_chuyen"): "kho_ycdc_moi",
	("tin_kho.py", "nhac_ycdc_treo"): "kho_ycdc_treo",
	("tin_kho.py", "bao_nhan_thieu_ton"): "kho_nhan_thieu_ton",
}
# Các hàm từng gửi thư nội bộ, nay chỉ được báo Zalo.
DA_BO_THU = [
	("ban_hang.py", "ra_trung_hang_dem"), ("ban_hang.py", "_bao_hoan_phat_hanh"),
	("ban_hang.py", "canh_bao_hddt_sot"), ("ban_hang.py", "canh_bao_don_treo"),
	("minvoice_chung_tu.py", "canh_bao_tac_nhip"), ("hoan_tien.py", "_bao_ke_toan"),
	("diem_han.py", "_bao_nguoi"), ("van_don.py", "_bao_tai_xe_huy"),
	("gui_thu.py", "canh_bao_email_loi"), ("gui_thu.py", "_bao_zalo"),
	# v611: thư "Đơn giao mới" cho shipper đã gỡ hẳn (ca dưới), hàm gán vẫn không gửi thư.
	("van_don.py", "gan_shipper"),
]


def _cay(tep):
	return ast.parse((GOI / tep).read_text(encoding="utf-8"))


def _ham(cay, ten):
	return [n for n in ast.walk(cay) if isinstance(n, ast.FunctionDef) and n.name == ten]


def _goi_zalo(tep, cay):
	"""Các lời gọi kenh_zalo.bao / bao_hoac_ghi_loi trong một tệp (kể cả `from ... import bao`)."""
	nhap_bao = any(isinstance(n, ast.ImportFrom) and n.module == "vagabond.kenh_zalo"
		and any(a.name in ("bao", "bao_hoac_ghi_loi") for a in n.names) for n in ast.walk(cay))
	ra = []
	for n in ast.walk(cay):
		if not isinstance(n, ast.Call):
			continue
		f = n.func
		if isinstance(f, ast.Attribute) and f.attr in ("bao", "bao_hoac_ghi_loi") and isinstance(f.value, ast.Name) \
				and f.value.id in ("kenh_zalo", "kz"):
			ra.append(n)
		elif isinstance(f, ast.Name) and f.id in ("bao", "bao_hoac_ghi_loi") and nhap_bao:
			ra.append(n)
	return ra


def _ma_tin(goi):
	k = [x for x in goi.keywords if x.arg == "ma_tin"]
	if not k or not isinstance(k[0].value, ast.Constant):
		return None
	return k[0].value.value


def _tep_nghiep_vu():
	for p in sorted(GOI.rglob("*.py")):
		r = p.relative_to(GOI).as_posix()
		if r.startswith("khung/") or r == "kenh_zalo.py":
			continue
		yield r


@ca("v604 danh mục tin: mã không trùng, đủ bộ phận, tên và giải thích tiếng Việt một dòng, loại và chủ đề có thật")
def _danh_muc():
	# dict literal trùng khoá thì Python lặng lẽ giữ bản sau: dò khoá ngay trong mã nguồn.
	cay = _cay("kenh_zalo.py")
	gan = [n for n in cay.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "TIN"]
	la("có đúng một bảng TIN", len(gan), 1)
	khoa = [k.value for k in gan[0].value.keys]
	la("không mã nào trùng", sorted(x for x in set(khoa) if khoa.count(x) > 1), [])
	# v606: thêm "Báo cáo cuối ngày" của Ban giám đốc (anh Việt duyệt 20/10/2026).
	# v609: thêm 21 tin kho, thu mua, sản xuất, đơn web (anh Việt duyệt 22/10/2026).
	# v611: thêm 11 tin đặt bàn, hoá đơn sai, tiền chưa gắn, sản xuất, điều chuyển (25/10/2026).
	la("đủ 55 tin (23 tới v606, 21 tin kho và thu mua v609, 11 tin v611)", len(kz.TIN), 55)
	la("bảy bộ phận đúng thứ tự", kz.BO_PHAN, ("Ban giám đốc", "Hoá đơn, kế toán", "Bán hàng, cửa hàng", "Bếp", "Thu mua", "Kho", "Hệ thống"))
	# Luật tiền (anh Việt 22/10/2026): tin Kho, Bếp không nói tiền; chỉ Thu mua, Kế toán.
	for ma, v in kz.TIN.items():
		if v[0] in ("Kho", "Bếp"):
			dung("%s: giải thích không hứa tiền" % ma, "tiền" not in v[2] and "giá vốn" not in v[2])
	for ma, (bp, ten, gt, loai, cd) in kz.TIN.items():
		dung("%s: bộ phận có trong danh mục" % ma, bp in kz.BO_PHAN)
		dung("%s: loại có thật" % ma, loai in kz.LOAI)
		dung("%s: chủ đề có thật" % ma, cd in kz.CHU_DE)
		dung("%s: tên tiếng Việt có dấu" % ma, len(ten) >= 6 and any(ord(c) > 127 for c in ten))
		dung("%s: giải thích tiếng Việt có dấu, một dòng" % ma, len(gt) >= 20 and "\n" not in gt and any(ord(c) > 127 for c in gt))
		dung("%s: giải thích ngắn (một dòng trên điện thoại)" % ma, len(gt) <= 110)
		dung("%s: không dấu gạch dài" % ma, not any(c in ten + gt for c in (chr(0x2013), chr(0x2014))))
		dung("%s: tên không lộ mã" % ma, "_" not in ten and "_" not in gt)
	# Các mục cùng bộ phận đứng liền nhau để hộp chọn gom đúng thứ tự.
	bp = [v[0] for v in kz.TIN.values()]
	la("mục cùng bộ phận đứng liền nhau", [b for i, b in enumerate(bp) if i == 0 or bp[i - 1] != b], list(kz.BO_PHAN))


@ca("v604 nơi phát: MỌI lời gọi bao() có ma_tin trong danh mục, mỗi tin có ít nhất một nơi phát, đúng hàm đúng mã")
def _noi_phat():
	dung_ma, thieu, la_ma = {}, [], []
	for tep in _tep_nghiep_vu():
		cay = _cay(tep)
		for g in _goi_zalo(tep, cay):
			m = _ma_tin(g)
			if m is None:
				thieu.append("%s:%s" % (tep, g.lineno))
			elif m not in kz.TIN:
				la_ma.append("%s:%s %s" % (tep, g.lineno, m))
			else:
				dung_ma.setdefault(m, []).append("%s:%s" % (tep, g.lineno))
	la("không lời gọi nào thiếu ma_tin", thieu, [])
	la("không mã lạ", la_ma, [])
	la("mỗi tin có nơi phát thật", sorted(set(kz.TIN) - set(dung_ma)), [])
	for (tep, ham), ma in NOI_PHAT.items():
		cay = _cay(tep)
		h = _ham(cay, ham)
		dung("%s %s có thật" % (tep, ham), len(h) == 1)
		ds = [_ma_tin(g) for g in _goi_zalo(tep, h[0])] if h else []
		la("%s %s báo đúng tin" % (tep, ham), ds, [ma])


@ca("v604 bỏ email: các hàm từng gửi thư cảnh báo nội bộ không còn frappe.sendmail, thư dự phòng còi thư đã gỡ")
def _bo_thu():
	for tep, ham in DA_BO_THU:
		h = _ham(_cay(tep), ham)
		dung("%s %s có thật" % (tep, ham), len(h) == 1)
		goi = [n for n in ast.walk(h[0]) if isinstance(n, ast.Call) and getattr(n.func, "attr", "") == "sendmail"] if h else [1]
		la("%s %s không gửi thư" % (tep, ham), len(goi), 0)
	for tep, ham in (("gui_thu.py", "_bao_bang_thu"), ("gui_thu.py", "_khung_bao_dong"), ("ban_hang.py", "_nguoi_nhan_don_treo"),
			("ban_hang.py", "_nguoi_nhan_canh_bao"), ("minvoice_chung_tu.py", "_khung_chuong"), ("nhan_su.py", "thu_tai_xe_huy_html"),
			("van_don.py", "_mail_phan_cong"), ("nhan_su.py", "thu_phan_cong_html")):
		la("%s %s đã gỡ (không còn ai dùng)" % (tep, ham), len(_ham(_cay(tep), ham)), 0)


def _js_cd():
	r = subprocess.run(["node", "-e", "var V=require(process.argv[1]);process.stdout.write(JSON.stringify("
		"{tin:V.ZALO_TIN,thu_tu:Object.keys(V.ZALO_TIN),bp:V.ZALO_BO_PHAN,nhom:V.tinTheoBoPhan()}))",
		str(GOI / "public/js/cai_dat_loi_chung.js")], capture_output=True, text=True, timeout=30)
	if r.returncode:
		raise AssertionError(r.stderr[-800:])
	return json.loads(r.stdout)


@ca("v604 bản JS VGB_ZALO_TIN trùng từng chữ kenh_zalo.TIN, cùng thứ tự, cùng bộ phận")
def _js_trung():
	j = _js_cd()
	la("cùng thứ tự mã", j["thu_tu"], list(kz.TIN))
	la("cùng bộ phận, tên, giải thích", j["tin"], {m: list(v[:3]) for m, v in kz.TIN.items()})
	la("cùng danh mục bộ phận", j["bp"], list(kz.BO_PHAN))
	la("hộp chọn gom theo bộ phận", [(x["bo_phan"], [t["ma"] for t in x["tin"]]) for x in j["nhom"]],
		[(b, [m for m, v in kz.TIN.items() if v[0] == b]) for b in kz.BO_PHAN])


def _nhom(**k):
	r = {"ten_nhom": "N", "chat_id": "c1", "bat": 1, "loai_tin": "", "chu_de": "", "tin_nhan": ""}
	r.update(k)
	return r


MA_TRAN = [
	# (tên ca, nhóm, loại, chủ đề, mã tin, nhận không)
	("tích tin, đúng mã", _nhom(tin_nhan="hd_trung, kt_hoan_tien"), "canh_bao", "hoa_don", "hd_trung", True),
	("tích tin, sai mã", _nhom(tin_nhan="hd_trung"), "canh_bao", "hoa_don", "hd_hddt_sot", False),
	("tích tin, tin không mã", _nhom(tin_nhan="hd_trung"), "canh_bao", "hoa_don", None, False),
	("tích tin thì bỏ qua loại, chủ đề", _nhom(tin_nhan="bh_dat_ban", loai_tin="canh_bao", chu_de="kho"), "viec", "dat_ban", "bh_dat_ban", True),
	("tích tin, loại khớp nhưng tin không tích", _nhom(tin_nhan="bh_dat_ban", loai_tin="canh_bao"), "canh_bao", "hoa_don", "hd_trung", False),
	("chưa tích tin, luật cũ khớp", _nhom(loai_tin="canh_bao", chu_de="hoa_don"), "canh_bao", "hoa_don", "hd_trung", True),
	("chưa tích tin, luật cũ lệch chủ đề", _nhom(loai_tin="canh_bao", chu_de="kho"), "canh_bao", "hoa_don", "hd_trung", False),
	("chưa tích tin, để trống là nhận tất", _nhom(), "viec", "cong_no", None, True),
	("chưa tích tin, có mã vẫn theo luật cũ", _nhom(loai_tin="viec"), "canh_bao", "he_thong", "ht_email_loi", False),
	("nhóm tắt", _nhom(tin_nhan="hd_trung", bat=0), "canh_bao", "hoa_don", "hd_trung", False),
	("thiếu mã chat", _nhom(tin_nhan="hd_trung", chat_id=" "), "canh_bao", "hoa_don", "hd_trung", False),
	("dấu chấm phẩy, khoảng trắng", _nhom(tin_nhan=" kt_hoan_tien ;hd_trung "), "viec", "cong_no", "hd_trung", True),
]


@ca("v604 chon_nhom: nhóm đã tích Tin nhận chỉ nhận đúng tin đã tích; chưa tích giữ luật Loại tin, Chủ đề cũ")
def _chon_nhom():
	for ten, r, loai, cd, ma, mong in MA_TRAN:
		la(ten, bool(kz.chon_nhom([r], loai, cd, ma)), mong)
	# Tham số thứ tư mặc định None: lời gọi cũ ba tham số giữ nguyên hành vi.
	la("lời gọi cũ ba tham số", [x["ten_nhom"] for x in kz.chon_nhom([_nhom(ten_nhom="A"), _nhom(ten_nhom="B", tin_nhan="hd_trung")],
		"viec", "cong_no")], ["A"])


@ca("v604 coNhomZalo (JS) cho cùng kết quả với chon_nhom (Python) trên cùng ma trận nhóm")
def _js_cung_luat():
	ds = [{"doc": {"zalo_nhom": [r]}, "loai": loai, "cd": cd, "ma": ma} for _, r, loai, cd, ma, _ in MA_TRAN]
	r = subprocess.run(["node", "-e", "var V=require(process.argv[1]);var ds=JSON.parse(process.argv[2]);"
		"process.stdout.write(JSON.stringify(ds.map(function(x){return V.coNhomZalo(x.doc,x.loai,x.cd,x.ma);})))",
		str(GOI / "public/js/cai_dat_loi_chung.js"), json.dumps(ds)], capture_output=True, text=True, timeout=30)
	dung("node chạy được", r.returncode == 0)
	js = json.loads(r.stdout or "[]")
	la("hai bản cùng luật", js, [bool(kz.chon_nhom([x["doc"]["zalo_nhom"][0]], x["loai"], x["cd"], x["ma"])) for x in ds])


@ca("v604 kiem_bo_loc chặn mã tin lạ trong Tin nhận, câu báo tiếng Việt nêu tên nhóm; mã đúng thì qua")
def _kiem_bo_loc():
	la("mã đúng", kz.kiem_bo_loc([_nhom(tin_nhan="hd_trung, ht_email_loi")]), "")
	loi = kz.kiem_bo_loc([_nhom(ten_nhom="Kế toán", tin_nhan="hd_trung, tin_cu_da_bo")])
	dung("chặn mã lạ", "tin_cu_da_bo" in loi)
	dung("nêu tên nhóm", "Kế toán" in loi)
	dung("chỉ cách sửa", "Chọn tin nhận" in loi)
	dung("câu tiếng Việt có dấu", "không còn trong danh mục" in loi)
	dung("kiem_bang_nhom cũng chặn (lúc lưu Cài đặt)", "tin_cu_da_bo" in kz.kiem_bang_nhom([_nhom(tin_nhan="tin_cu_da_bo")]))
	loi2 = kz.kiem_bo_loc([_nhom(loai_tin="viecc", tin_nhan="x_y")])
	dung("lỗi loại tin và lỗi tin cùng báo", "viecc" in loi2 and "x_y" in loi2)


@ca("v604 chu_chua_nhom: tin có mã thì Error Log gọi đúng tên tin và chỉ chỗ tích")
def _chu_chua_nhom():
	t, m = kz.chu_chua_nhom("canh_bao", "hoa_don", "SINV-1", "hd_don_chua_ghi_so")
	dung("tiêu đề có tên tin", "Đơn chưa ghi sổ còn sót lúc 23:55" in t)
	dung("lời chỉ chỗ tích", "Tin nhận" in m and "Cài đặt lõi" in m)
	dung("nêu chứng từ", "SINV-1" in m)
	dung("không lộ mã tin", "hd_don_chua_ghi_so" not in t + m)
	dung("tiêu đề vừa ô Error Log", len(t) <= 140)
	t2, _ = kz.chu_chua_nhom("viec", "dat_ban")
	dung("không mã thì giữ câu cũ", "Việc cần làm" in t2 and "Đặt bàn" in t2)


@ca("v604 bao_hoac_ghi_loi: tin đã nằm trong sổ (khoá trùng) thì không ghi lỗi giả; không nhóm nhận thì ghi lỗi nêu tên tin")
def _bao_hoac():
	for nhom, mong in (([_nhom(tin_nhan="hd_trung")], 0), ([_nhom(tin_nhan="kt_hoan_tien")], 1), ([], 1)):
		log = []
		fr = NS(flags=NS(), log_error=lambda title=None, message=None, *a, **k: log.append((title, message)))
		with patch.object(kz, "frappe", fr), patch.object(kz, "bao", lambda *a, **k: []), \
				patch.object(kz, "_bat", lambda: 1), patch.object(kz, "_cac_nhom", lambda: nhom):
			kz.bao_hoac_ghi_loi("canh_bao", "hoa_don", "x", [], khoa="k", ma_tin="hd_trung")
		la("số Error Log (nhóm=%r)" % [r["tin_nhan"] for r in nhom], len(log), mong)
		if log:
			dung("Error Log nêu tên tin", "Đơn có hoá đơn trùng" in log[0][0])


@ca("v604 _ghi_hop_thu ghi mã tin vào sổ và chỉ ghi cho nhóm đã tích đúng tin")
def _ghi_so():
	ghi = []

	class Doc(dict):
		def insert(self, **k):
			ghi.append(dict(self))
	fr = NS(get_doc=lambda d: Doc(d), generate_hash=lambda length=8: "h" * length,
		db=NS(savepoint=lambda *a: None, rollback=lambda **k: None), DuplicateEntryError=KeyError,
		log_error=lambda *a, **k: None)
	nhom = [_nhom(ten_nhom="KT", chat_id="c1", tin_nhan="hd_trung"), _nhom(ten_nhom="Sales", chat_id="c2", tin_nhan="bh_tiec")]
	with patch.object(kz, "frappe", fr), patch.object(kz, "_cac_nhom", lambda: nhom):
		ten = kz._ghi_hop_thu({"loai": "canh_bao", "chu_de": "hoa_don", "tieu_de": "T", "dong": [], "khoa": "k", "ma_tin": "hd_trung"})
	la("một dòng cho đúng nhóm", [(g["nhom"], g["ma_tin"]) for g in ghi], [("KT", "hd_trung")])
	la("trả tên dòng", len(ten), 1)


@ca("v604 doctype: ô Tin nhận nằm ngay sau Chủ đề, chỉ đọc trên Desk, app ghi được qua hộp chọn; sổ tin có ô mã tin")
def _doctype():
	d = json.loads((GOI / "vagabond/doctype/vagabond_kenh_zalo/vagabond_kenh_zalo.json").read_text(encoding="utf-8"))
	fo = d["field_order"]
	la("đứng ngay sau chu_de", fo[fo.index("chu_de") + 1], "tin_nhan")
	f = [x for x in d["fields"] if x["fieldname"] == "tin_nhan"]
	la("một ô", len(f), 1)
	la("kiểu, nhãn, chỉ đọc", (f[0]["fieldtype"], f[0]["label"], f[0].get("read_only")), ("Small Text", "Tin nhận", 1))
	dung("đã tăng modified", d["modified"] >= "2026-10-18")
	t = json.loads((GOI / "vagabond/doctype/vagabond_tin_kenh/vagabond_tin_kenh.json").read_text(encoding="utf-8"))
	dung("sổ tin có ô ma_tin", "ma_tin" in t["field_order"] and any(x["fieldname"] == "ma_tin" for x in t["fields"]))
	dung("sổ tin đã tăng modified", t["modified"] >= "2026-10-18")
	from vagabond import cai_dat_loi
	dung("app ghi được Tin nhận qua hộp chọn", "tin_nhan" in cai_dat_loi.GHI_QUA_HOP_CHON["zalo_nhom"])


# ------------------------------------------------------------ chạy hàm thật

@contextmanager
def _zalo_gia(ket=("ZL-1",)):
	"""Kênh Zalo giả: ghi lại mọi lời gọi; cat_dong là hàm thật."""
	goi = []

	def ghi(loai, chu_de, tieu_de, dong=None, **kw):
		goi.append(dict(kw, loai=loai, chu_de=chu_de, tieu_de=tieu_de, dong=list(dong or [])))
		return list(ket)
	gia = NS(bao=ghi, bao_hoac_ghi_loi=ghi, cat_dong=kz.cat_dong, tach_tin=kz.tach_tin)
	with patch.dict(sys.modules, {"vagabond.kenh_zalo": gia}), patch.object(vagabond, "kenh_zalo", gia):
		yield goi


def _fr(**k):
	log = []
	f = NS(log_error=lambda *a, **kw: log.append(a), get_traceback=lambda: "TB", set_user=lambda *a: None,
		db=NS(commit=lambda: None), utils=NS(get_url=lambda p="": "https://erp.test" + p, nowdate=lambda: "2026-10-18"))
	for a, b in k.items():
		setattr(f, a, b)
	f._log = log
	return f


@ca("v604 chuông 23:55 đơn treo báo Zalo: mỗi lý do một dòng đếm, tối đa 12 đơn rồi 'và N đơn nữa', mở màn Đơn còn treo")
def _don_treo():
	ds = [D(ly_do="chua_pt", hom_nay=0, posting_date="2026-10-17", custom_pancake_display_id="P%d" % i, name="SI-%d" % i,
		grand_total=100000) for i in range(15)] + [D(ly_do="san_sang", hom_nay=1, posting_date="2026-10-18",
		custom_pancake_display_id="HN", name="SI-HN", grand_total=1)]
	f = _fr()
	g = dict(frappe=f, _quet_don_treo=lambda n: ds, LY_DO_TREO={"chua_pt": "Chưa có phương thức thanh toán"},
		_tien=lambda n: "{:,.0f}".format(float(n)).replace(",", "."), flt=float, nowdate=lambda: "2026-10-18")
	with _zalo_gia() as goi:
		nap("ban_hang.py", "canh_bao_don_treo", g)()
	la("báo một tin", len(goi), 1)
	t = goi[0]
	la("đúng tin và loại", (t["ma_tin"], t["loai"], t["chu_de"]), ("hd_don_chua_ghi_so", "canh_bao", "hoa_don"))
	dung("tiêu đề đếm đúng 15 đơn (bỏ đơn hôm nay đã sẵn sàng)", "15 đơn" in t["tieu_de"])
	la("dòng đầu là đếm theo lý do", t["dong"][0], "Chưa có phương thức thanh toán: 15 đơn, 1.500.000 đ")
	la("12 đơn rồi gom phần còn lại", t["dong"][13], "... và 3 đơn nữa")
	dung("chỉ đường màn Đơn còn treo", t["link"].endswith("/don-con-treo") and "Đơn còn treo" in t["dong"][-1])
	la("khoá theo ngày", t["khoa"], "don-treo:2026-10-18")
	with _zalo_gia() as goi:
		nap("ban_hang.py", "canh_bao_don_treo", dict(g, _quet_don_treo=lambda n: []))()
	la("không còn đơn thì im", goi, [])


@ca("v604 chuông 2h hoá đơn trùng báo Zalo đúng tin, kê đơn, chỉ cách gỡ")
def _trung():
	nhom = [{"don": "P1", "ngay": "2026-10-17", "so_tien": 200000, "giu": "SI-1", "go": ["SI-2"], "ket": []}]
	f = _fr(db=NS(get_all=lambda *a, **k: [1], commit=lambda: None))
	g = dict(frappe=f, _nhom_trung=lambda s: nhom, TRUONG_TRUNG=[], _tien=lambda n: "200.000", nowdate=lambda: "2026-10-18")
	with _zalo_gia() as goi:
		nap("ban_hang.py", "ra_trung_hang_dem", g)()
	la("đúng tin", [x["ma_tin"] for x in goi], ["hd_trung"])
	dung("kê đơn và phiếu gỡ được", "Đơn P1" in goi[0]["dong"][0] and "SI-2" in goi[0]["dong"][0])
	dung("chỉ cách gỡ", "Rà và gỡ phiếu trùng" in goi[0]["dong"][-1])


@ca("v604 chuông 8h25 hoá đơn đầu vào báo Zalo khi tắc hoặc trùng, im khi ổn")
def _dau_vao():
	for cho, trung, mong in ((5, 0, 1), (0, 2, 1), (0, 0, 0)):
		f = _fr(db=NS(exists=lambda *a: True, count=lambda *a: cho, get_value=lambda *a, **k: None, commit=lambda: None))
		f.utils.now_datetime = lambda: None
		g = dict(frappe=f, DT_HD="MInvoice Invoice", LOAI_VAO="Đầu vào", PI="Purchase Invoice", cint=lambda x: int(x or 0),
			_dem_trung=lambda: {"so_to_thua": trung, "so_nhom": 1, "ds": [{"ten": ["PI-1", "PI-2"]}]},
			nhip_da_tac=lambda c, h: c > 0)
		with _zalo_gia() as goi:
			nap("minvoice_chung_tu.py", "canh_bao_tac_nhip", g)()
		la("số tin (chờ=%s, trùng=%s)" % (cho, trung), len(goi), mong)
		if goi:
			la("đúng tin", goi[0]["ma_tin"], "hd_dau_vao")
			if trung:
				dung("có câu cấm ghi sổ và tên tờ trùng", any("ĐỪNG GHI SỔ" in d for d in goi[0]["dong"])
					and any("PI-1 và PI-2" in d for d in goi[0]["dong"]))


@ca("v604 hoàn tiền báo nhóm kế toán qua Zalo, trả đã báo; không đưa số tài khoản khách vào nhóm chat")
def _hoan_tien():
	ho_so = D(name="HT-1", so_tien=50000, ly_do="Hỏng", dien_giai="", nguoi_duyet="Sales A", ten_tk="NGUYEN A",
		so_tk="0123456789", ngan_hang="MB", noi_dung_ck="HT1 HOAN")
	si = D(name="SI-1", grand_total=100000)
	g = dict(frappe=_fr(), flt=float)
	for ket, mong in ((["ZL-1"], 1), ([], 0)):
		with _zalo_gia(ket) as goi:
			kq = nap("hoan_tien.py", "_bao_ke_toan", g)(ho_so, si)
		la("trả đã báo (ket=%r)" % (ket,), kq, (mong, []))
	la("đúng tin", goi[0]["ma_tin"], "kt_hoan_tien")
	dung("có nội dung chuyển khoản", any("HT1 HOAN" in d for d in goi[0]["dong"]))
	dung("không có số tài khoản khách", not any("0123456789" in d for d in goi[0]["dong"] + [goi[0]["tieu_de"]]))
	la("khoá theo hồ sơ", goi[0]["khoa"], "hoan-tien:HT-1")


@ca("v604 đề nghị chi: chuyển bước báo Zalo kèm giữ việc giao; xong hoặc huỷ thì không báo; trả lại cũng báo")
def _de_nghi_chi():
	src = (GOI / "de_nghi_chi.py").read_text(encoding="utf-8")
	giao = []
	gv = NS(giao_vai=lambda *a: giao.append(("vai",) + a), go_giao=lambda *a: giao.append(("go",) + a))
	g = dict(frappe=_fr(), VAI_BUOC={"Cho giam doc": {"AP Giám đốc"}}, NHAN_TRANG_THAI={"Cho giam doc": "Chờ giám đốc duyệt"},
		DT="Vagabond De Nghi Chi", tien_phieu=lambda d: 1500000, _tien=lambda v: "1.500.000")
	nap("de_nghi_chi.py", "_bao_zalo", g)
	doc = D(name="DNC-1", trang_thai="Cho giam doc", ten_khoan_chi="Mua bơ", modified="2026-10-18 09:00:00")
	doc.as_dict = lambda: dict(doc)
	with _zalo_gia() as goi, patch.dict(sys.modules, {"vagabond.giao_viec": gv}), patch.object(vagabond, "giao_viec", gv, create=True):
		nap("de_nghi_chi.py", "_bao_buoc_ke_tiep", g)(doc)
		la("báo đúng tin", [x["ma_tin"] for x in goi], ["kt_de_nghi_chi"])
		dung("tiêu đề nói bước", "chờ giám đốc duyệt" in goi[0]["tieu_de"])
		la("vẫn giao việc theo vai", [x[0] for x in giao], ["vai"])
		doc.trang_thai = "Hoan tat"
		nap("de_nghi_chi.py", "_bao_buoc_ke_tiep", g)(doc)
		la("xong thì không báo thêm", len(goi), 1)
		la("xong thì gỡ việc", giao[-1][0], "go")
	dung("trả lại có báo Zalo", '_bao_zalo(doc, "Đề nghị chi bị trả lại' in src.split("def tra_lai")[1].split("\ndef ")[0])


@ca("v604 trả trước: chờ kế toán kiểm thì báo Zalo và giữ việc giao; phiếu còn Nháp giao thu mua thì không báo nhóm")
def _tra_truoc():
	giao = []
	gv = NS(_nguoi_theo_vai=lambda v: ["kt@x"], giao=lambda *a: giao.append(a))
	g = dict(frappe=_fr(), VAI_FIN={"Accounts User"}, PE="Payment Entry", tien_vn=lambda t: "2.000.000")
	d = D(name="PO-1", supplier="NCC", supplier_name="Bơ Sữa")
	with _zalo_gia() as goi, patch.dict(sys.modules, {"vagabond.giao_viec": gv}), patch.object(vagabond, "giao_viec", gv, create=True):
		f = nap("tra_truoc.py", "_bao_ke_toan", g)
		f("PE-1", d, 2000000)
		la("báo đúng tin", [x["ma_tin"] for x in goi], ["kt_tra_truoc_kiem"])
		f("PE-2", d, 2000000, "AP Officer")
		la("phiếu nháp không báo nhóm", len(goi), 1)
	la("cả hai vẫn giao việc", len(giao), 2)


@ca("v604 điểm hết hạn, hợp đồng điều chỉnh, tài xế huỷ, kế hoạch bếp: mỗi chỗ báo đúng tin")
def _con_lai():
	with _zalo_gia() as goi:
		nap("diem_han.py", "_bao_nguoi", dict(frappe=_fr()))("Điểm hết hạn: máy đã dừng lại", "Đêm nay 300 khách...")
	la("điểm hết hạn", [x["ma_tin"] for x in goi], ["kt_diem_het_han"])

	chuong = []
	tb = NS(bao_cho_vai=lambda *a: chuong.append(a))
	with _zalo_gia() as goi, patch.dict(sys.modules, {"vagabond.thong_bao": tb, "vagabond.viec_can_lam": NS(VAI_GIAM_DOC={"GD"})}), \
			patch.object(vagabond, "thong_bao", tb, create=True):
		nap("hop_dong_dieu_chinh.py", "_bao_giam_doc", dict(frappe=_fr()))(D(name="HDG-1"), D(nhan="Bản 2"), [{"nhan": "Giá"}])
	la("hợp đồng điều chỉnh", [x["ma_tin"] for x in goi], ["kt_hop_dong_dc"])
	la("vẫn rung chuông giám đốc", len(chuong), 1)

	doc = D(name="VD-1", ma_don="P9", khach="Chị B", tag_gio="9-11h", modified="2026-10-18 10:00:00")
	g = dict(frappe=_fr(), flt=lambda x: float(x or 0),
		_noi_giao=lambda d: {"dia_chi": "9 Trần Cao Vân", "cod": 0.0})
	g["frappe"].utils.get_url = lambda p="": "https://erp.test" + p
	with _zalo_gia() as goi:
		nap("van_don.py", "_bao_tai_xe_huy", g)(doc)
	la("tài xế huỷ", [x["ma_tin"] for x in goi], ["bh_ahamove_huy"])
	dung("đơn pickup báo nơi giao là quầy", "Giao tới: 9 Trần Cao Vân" in goi[0]["dong"])
	dung("đơn COD 0 thì không dòng thu hộ", not any("Thu hộ" in x for x in goi[0]["dong"]))

	chuong = []
	tb = NS(bao_cho_vai=lambda *a, **k: chuong.append(a))
	f = _fr(db=NS(count=lambda *a: 3, commit=lambda: None))
	with _zalo_gia() as goi, patch.dict(sys.modules, {"vagabond.thong_bao": tb}), patch.object(vagabond, "thong_bao", tb, create=True):
		nap("ke_hoach_sx.py", "nhac_bep_sang", dict(frappe=f, nowdate=lambda: "2026-10-18", _phieu_cua_ngay=lambda n: "KHSX-1",
			VAI_NHAC={"Bếp trưởng"}))()
	la("kế hoạch bếp", [x["ma_tin"] for x in goi], ["bep_ke_hoach_sx"])
	la("vẫn rung chuông bếp trưởng", len(chuong), 1)
	dung("mở đúng màn Lập kế hoạch sản xuất", goi[0]["link"].endswith("/lap-ke-hoach-san-xuat"))


@ca("v604 cat_dong: tối đa 12 dòng rồi 'và N đơn nữa', bỏ dòng trống, ít hơn thì giữ nguyên")
def _cat_dong():
	la("ít hơn trần", kz.cat_dong(["a", "", "b"]), ["a", "b"])
	ra = kz.cat_dong([str(i) for i in range(20)])
	la("12 dòng và một dòng gom", (len(ra), ra[-1]), (13, "... và 8 đơn nữa"))
	la("đổi đơn vị", kz.cat_dong(list("abcd"), 2, "nhóm")[-1], "... và 2 nhóm nữa")


# ------------------------------------------------------------ bản vá điền sẵn

def _patch():
	from vagabond.patches import v604_tin_nhan_zalo as p
	return p


@ca("v604 bản vá: nhóm Kế toán nhận 12 tin kế toán, thư hỏng, phát hành; nhóm Sales nhận tin bán hàng và phát hành")
def _patch_map():
	p = _patch()
	# Bản vá v604 đã chạy trên site, điền danh mục TẠI THỜI ĐIỂM ĐÓ. Tin thêm sau
	# (v609) không thuộc bản vá: anh Việt tích tay trong Cài đặt cho nhóm cần.
	v609 = {"kt_xuat_huy_gia_von", "kt_kiem_ke_lech", "bh_don_web_moi",
		# v611: bản vá riêng v611_tat_thu_noi_bo tích tin đặt bàn và hoá đơn sai.
		"kt_tien_chua_gan", "bh_dat_ban_xac_nhan", "bh_dat_ban_huy", "bh_dat_ban_sap_toi", "bh_thong_tin_hd_sai"}
	kt = [m for m, v in kz.TIN.items() if v[0] == "Hoá đơn, kế toán" and m not in v609] + ["ht_email_loi", "ht_phat_hanh"]
	bh = [m for m, v in kz.TIN.items() if v[0] == "Bán hàng, cửa hàng" and m not in v609] + ["ht_phat_hanh"]
	la("nhóm văn phòng kế toán", p.tin_cho_nhom("ERP Văn Phòng - Kế Toán - Thu Mua"), kt)
	la("nhóm Sales", p.tin_cho_nhom("Sales Vagabond - Nhóm Bán hàng"), bh)
	la("không dấu, hoa thường vẫn khớp", p.tin_cho_nhom("ke toan"), kt)
	la("KẾ TOÁN viết hoa", p.tin_cho_nhom("NHÓM KẾ TOÁN"), kt)
	la("chỉ chữ Bán hàng", p.tin_cho_nhom("Quầy bán hàng Q1"), bh)
	la("tên khác không đụng", p.tin_cho_nhom("Bếp Baker"), [])
	la("mọi mã có trong danh mục", sorted(set(p.TIN_KE_TOAN + p.TIN_SALES) - set(kz.TIN)), [])
	la("không tin Bếp nào bị gán nhầm", [m for m in p.TIN_KE_TOAN + p.TIN_SALES if kz.TIN[m][0] == "Bếp"], [])


@ca("v604 bản vá lũy đẳng: chỉ điền nhóm có Tin nhận trống, chạy lại không đổi gì, nhóm đã tích tay giữ nguyên")
def _patch_lap():
	p = _patch()
	rows = [{"name": "r1", "ten_nhom": "ERP Văn Phòng - Kế Toán - Thu Mua", "tin_nhan": ""},
		{"name": "r2", "ten_nhom": "Sales Vagabond - Nhóm Bán hàng", "tin_nhan": "bh_tiec"},
		{"name": "r3", "ten_nhom": "Bếp", "tin_nhan": None}]
	ghi = []
	fr = NS(db=NS(has_column=lambda dt, c: True, set_value=lambda dt, ten, f, v, **k: ghi.append((ten, f, v)),
		commit=lambda: None), get_all=lambda *a, **k: [dict(r) for r in rows], clear_cache=lambda **k: None)
	with patch.dict(sys.modules, {"frappe": fr}):
		p.execute()
	la("chỉ ghi nhóm Kế toán còn trống", [(t, f) for t, f, _ in ghi], [("r1", "tin_nhan")])
	la("chuỗi mã đúng định dạng lưu", ghi[0][2], ", ".join(p.TIN_KE_TOAN))
	for t, _, v in ghi:
		next(r for r in rows if r["name"] == t)["tin_nhan"] = v
	ghi.clear()
	with patch.dict(sys.modules, {"frappe": fr}):
		p.execute()
	la("chạy lại không ghi gì", ghi, [])
	ghi.clear()
	fr.db.has_column = lambda dt, c: False
	with patch.dict(sys.modules, {"frappe": fr}):
		p.execute()
	la("chưa có cột thì không làm gì", ghi, [])
	la("dien_san thuần", p.dien_san([{"ten_nhom": "Kế toán", "tin_nhan": " "}, {"ten_nhom": "X"}]), [(0, ", ".join(p.TIN_KE_TOAN))])

