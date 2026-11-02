# -*- coding: utf-8 -*-
"""v630: bánh thiết kế riêng đặt và cọc 50% trên web (anh Việt chốt 02/11/2026).

Các ca chạy phép THẬT của thiet_ke_rieng.py, noi_dung_web.py, dat_banh.py,
ca_quay.py trên Frappe giả của nen.py. Chốt bốn finding của Codex:
  1. tiền cọc không thành dòng giảm giá, giá do máy chủ tính từ khối đã xuất bản;
  2. một dòng sao kê chỉ chiếm một lần (sổ đối soát chung), không lập phiếu đôi;
  3. hoá đơn ngày giao chỉ cấn phiếu thu ĐÃ GHI SỔ của đúng phiếu đặt;
  4. ô quầy của phiếu cọc chuyển khoản: phiếu qua đủ bốn hàng rào dat_banh và
     két quầy cửa hàng không bị cộng khoản nó không cầm.
Ca hành vi node của tab Vue và màn app chạy ở cuối tệp.
"""

import copy
import json
import re
import subprocess
import sys
import types
from datetime import date
from pathlib import Path
from unittest import mock

from vagabond.khung.kiem_thu.nen import ca, dung, gia_lap, la, nem

gia_lap()
_fr = sys.modules["frappe"]
if "frappe.rate_limiter" not in sys.modules:
	sys.modules["frappe.rate_limiter"] = types.ModuleType("frappe.rate_limiter")
	sys.modules["frappe.rate_limiter"].rate_limit = lambda **k: (lambda f: f)

from vagabond import noi_dung_web as nw  # noqa: E402
from vagabond import thiet_ke_rieng as tkr  # noqa: E402

GOC = Path(__file__).resolve().parents[3]
TP = nw.chuan_tkr(nw.TKR_MAU)
HOM = "2026-11-02"
DIEM = [{"id": "tcv", "n": "The Vagabond District 1", "a": "9 Trần Cao Vân"}]


def _don(**k):
	d = {"tac_pham": TP["id"], "kich_co": "M", "trang_tri": ["Hoa lan trắng"], "ngay": "2026-11-14", "gio": "17:00",
		"ten": "Nguyễn An", "sdt": "0909 123 456", "ghi_chu": "Tông kem", "diem_nhan": "tcv"}
	d.update(k)
	return d


def _node(js):
	r = subprocess.run(["node", "--input-type=module", "-e", js], cwd=GOC, capture_output=True, text=True, timeout=60)
	if r.returncode:
		raise AssertionError(r.stderr[-800:])
	return json.loads(r.stdout)


# ------------------------------------------------------------ giá và cọc

@ca("v630 giá máy chủ: ba size Croquembouche đúng giá đã gồm VAT anh Việt chốt, cọc 50% làm tròn lên tới nghìn")
def _gia_ba_size():
	ra = {kc["ten"]: tkr.tinh_gia(TP, kc["ten"], ["Hoa lan trắng"]) for kc in TP["kich_co"]}
	la("S", (ra["S"]["tong"], ra["S"]["coc"], ra["S"]["con_lai"]), (5940000, 2970000, 2970000))
	la("M", (ra["M"]["tong"], ra["M"]["coc"], ra["M"]["con_lai"]), (7560000, 3780000, 3780000))
	la("L", (ra["L"]["tong"], ra["L"]["coc"], ra["L"]["con_lai"]), (10800000, 5400000, 5400000))


@ca("v630 cọc làm tròn LÊN tới nghìn, không bao giờ dưới một nửa (5.941.000 cọc 2.971.000)")
def _coc_tron_len():
	for tong, coc in ((5941000, 2971000), (5940500, 2971000), (1, 1000), (0, 0), (-5, 0), (2000, 1000), (2001, 2000)):
		la("cọc của %s" % tong, tkr.tien_coc(tong), coc)
		dung("cọc của %s không dưới nửa" % tong, tong <= 0 or tkr.tien_coc(tong) * 2 >= tong)


@ca("v630 trình duyệt gửi giá, tổng, cọc tuỳ ý: máy chủ bỏ qua, giá lấy từ khối đã xuất bản")
def _khong_nhan_gia():
	don = tkr.chuan_don(_don(tong=1, gia=1, coc=1, gia_kich_co=1), TP, HOM, DIEM)
	la("tổng máy chủ", (don["tong"], don["coc"], don["gia_kich_co"]), (7560000, 3780000, 7560000))
	tp = copy.deepcopy(TP)
	tp["trang_tri"][3]["gia_them"] = 350000
	don = tkr.chuan_don(_don(trang_tri=["Hoa theo màu tiệc", "Thêm bục trắng"]), tp, HOM, DIEM)
	la("cộng trang trí", (don["tong"], don["coc"], don["gia_trang_tri"]), (7910000, 3955000, 350000))


@ca("v630 trang trí: cùng nhóm Hoa chỉ chọn một, trang trí lạ hay size lạ bị chặn bằng câu tiếng Việt")
def _trang_tri():
	nem("hai hoa", lambda: tkr.tinh_gia(TP, "M", ["Hoa lan trắng", "Không hoa"]), ValueError)
	nem("trang trí lạ", lambda: tkr.tinh_gia(TP, "M", ["Kim tuyến"]), ValueError)
	nem("size lạ", lambda: tkr.tinh_gia(TP, "XL", []), ValueError)
	la("không chọn trang trí vẫn tính", tkr.tinh_gia(TP, "S", [])["tong"], 5940000)
	la("bục trắng khác nhóm đi cùng hoa", tkr.tinh_gia(TP, "S", ["Không hoa", "Thêm bục trắng"])["trang_tri"],
		["Không hoa", "Thêm bục trắng"])


@ca("v630 ngày: sớm nhất hôm nay + số ngày đặt trước, không bao giờ dưới 7 dù khối khai ít hơn")
def _ngay():
	la("sớm nhất", tkr.ngay_som_nhat(HOM, TP), date(2026, 11, 9))
	nem("hôm nay + 6 bị chặn", lambda: tkr.chuan_don(_don(ngay="2026-11-08"), TP, HOM, DIEM), ValueError)
	la("hôm nay + 7 nhận", tkr.chuan_don(_don(ngay="2026-11-09"), TP, HOM, DIEM)["ngay"], "2026-11-09")
	tp = dict(TP, so_ngay="3")
	la("khối khai 3 ngày vẫn tính 7", tkr.so_ngay_cua(tp), 7)
	la("khối khai 10 ngày", str(tkr.ngay_som_nhat(HOM, dict(TP, so_ngay="10"))), "2026-11-12")
	nem("ngày sai dạng", lambda: tkr.chuan_don(_don(ngay="14/11/2026"), TP, HOM, DIEM), ValueError)
	nem("quá một năm", lambda: tkr.chuan_don(_don(ngay="2027-12-01"), TP, HOM, DIEM), ValueError)


@ca("v630 đơn: số điện thoại, nơi nhận, tác phẩm ẩn, giờ sai dạng đều bị chặn ở cửa nhập")
def _cua_nhap():
	la("số +84 về 0", tkr.chuan_don(_don(sdt="+84 909 123 456"), TP, HOM, DIEM)["sdt"], "0909123456")
	nem("số bàn", lambda: tkr.chuan_don(_don(sdt="0283 822 9999"), TP, HOM, DIEM), ValueError)
	nem("thiếu tên", lambda: tkr.chuan_don(_don(ten=" "), TP, HOM, DIEM), ValueError)
	nem("nơi nhận lạ", lambda: tkr.chuan_don(_don(diem_nhan="kho-bi-mat"), TP, HOM, DIEM), ValueError)
	nem("giờ sai", lambda: tkr.chuan_don(_don(gio="25:00"), TP, HOM, DIEM), ValueError)
	nem("ghi chú quá dài", lambda: tkr.chuan_don(_don(ghi_chu="x" * 501), TP, HOM, DIEM), ValueError)
	nd = {"khoi": [dict(TP, hien=False)]}
	la("tác phẩm ẩn không đặt được", tkr.tac_pham_hien(nd, TP["id"]), None)
	nem("tác phẩm None", lambda: tkr.chuan_don(_don(), None, HOM, DIEM), ValueError)


# ------------------------------------------------------------ danh mục

def _bi_chan(k, chu=None):
	nd = copy.deepcopy(nw.MAC_DINH)
	nd["khoi"].append(k)
	try:
		nw.chuan_hoa(nd)
	except (ValueError, TypeError) as e:
		return chu is None or chu in str(e)
	return False


@ca("v630 danh mục: khối mẫu Croquembouche qua chuan_hoa, giá chuẩn hoá thành số nguyên")
def _mau_hop_le():
	nd = copy.deepcopy(nw.MAC_DINH)
	nd["khoi"].append(dict(nw.TKR_MAU, kich_co=[{"ten": "S", "mo_ta": "", "gia": "5.940.000"}]))
	ra = nw.chuan_hoa(nd)
	k = [x for x in ra["khoi"] if x["loai"] == "thiet_ke_rieng"][0]
	la("giá chuỗi có chấm thành số", k["kich_co"][0]["gia"], 5940000)
	la("trang trí giữ nhóm", [x["nhom"] for x in nw.chuan_tkr(nw.TKR_MAU)["trang_tri"]], ["Hoa", "Hoa", "Hoa", ""])
	la("trạng thái trên trình biên tập", nw.trang_thai_muc(k, HOM), ("dang", "Đang nhận đặt"))
	la("thêm mẫu một lần", len([x for x in nw.them_tkr_mau(nw.them_tkr_mau(nw.MAC_DINH))["khoi"] if x["loai"] == "thiet_ke_rieng"]), 1)


@ca("v630 danh mục: giá âm, 0, quá trần, có chữ; size trùng; quá 8 size; số ngày dưới 7; trường lạ đều bị chặn")
def _danh_muc_chan():
	m = nw.TKR_MAU
	for gia in (-1, 0, "0", "5,9tr", "abc", 10 ** 12, True, None):
		dung("chặn giá %r" % (gia,), _bi_chan(dict(m, kich_co=[{"ten": "S", "mo_ta": "", "gia": gia}])))
	dung("size trùng (khác hoa thường)", _bi_chan(dict(m, kich_co=[{"ten": "S", "gia": 1}, {"ten": "s", "gia": 2}]), "trùng"))
	dung("quá 8 size", _bi_chan(dict(m, kich_co=[{"ten": str(i), "gia": 1} for i in range(9)])))
	dung("không size", _bi_chan(dict(m, kich_co=[])))
	dung("số ngày 6", _bi_chan(dict(m, so_ngay="6"), "tối thiểu là 7"))
	dung("trường lạ trong size", _bi_chan(dict(m, kich_co=[{"ten": "S", "gia": 1, "giam": 1}])))
	dung("trang trí âm", _bi_chan(dict(m, trang_tri=[{"ten": "Hoa", "gia_them": -5}])))
	dung("trang trí trùng", _bi_chan(dict(m, trang_tri=[{"ten": "Hoa", "gia_them": 0}, {"ten": "hoa", "gia_them": 0}])))
	dung("ảnh riêng tư", _bi_chan(dict(m, anh="/private/files/x.jpg")))
	dung("ảnh svg", _bi_chan(dict(m, anh="/files/x.svg")))
	dung("ảnh http", _bi_chan(dict(m, anh="http://la.vn/x.jpg")))
	dung("khối thường không mang danh sách size", _bi_chan({"id": "x", "loai": "thong_bao", "hien": True, "kich_co": []}))


# ------------------------------------------------------------ QR

@ca("v630 QR: một phép dựng VietQR dùng chung; nội dung đúng mã đơn, số tiền đúng tiền cọc")
def _qr():
	from vagabond import qr_chuyen_khoan as q
	s = q.ma_qr({"bin": "970422", "stk": "VQRQ00033k5p6"}, 3780000, "TKR26110001")
	dung("mã đơn trong trường 62/08", "0811TKR26110001" in s)
	dung("số tiền trong trường 54", "54073780000" in s)
	la("cùng kết quả phép gốc", s, q.chuoi("970422", "VQRQ00033k5p6", 3780000, "TKR26110001"))
	with mock.patch.object(q, "anh", side_effect=lambda x: "data:" + x):
		la("ảnh từ cùng chuỗi", q.anh_qr({"bin": "970422", "stk": "VQRQ00033k5p6"}, 3780000, "TKR26110001"), "data:" + s)
	la("BIN sai trả rỗng", q.anh_qr({"bin": "12", "stk": "1"}, 1, "x"), "")
	dung("câu lỗi nói rõ BIN", "BIN" in q.cau_loi_qr({"bin": "12", "stk": "1"}, 1, "x"))


@ca("v630 QR: không mô đun nào tự dựng VietQR (công nợ, thu hợp đồng, báo giá, thiết kế riêng cùng gọi một phép)")
def _qr_mot_nguon():
	sai = []
	for p in sorted((GOC / "vagabond").rglob("*.py")):
		r = p.relative_to(GOC).as_posix()
		if r == "vagabond/qr_chuyen_khoan.py" or "/khung/kiem_thu/" in r or "/khung/bench_thu/" in r:
			continue
		s = p.read_text(encoding="utf-8")
		if (re.search(r"from vagabond\.qr_chuyen_khoan import[^\n]*\b(chuoi|anh)\b(?!_)", s)
				or "qr_chuyen_khoan.chuoi(" in s or "A000000727" in s):
			sai.append(r)
	la("mô đun tự dựng VietQR", sai, [])
	for ten in ("cong_no.py", "thu_hop_dong.py", "bao_gia.py", "thiet_ke_rieng.py"):
		dung(ten + " gọi phép chung", "anh_qr" in (GOC / "vagabond" / ten).read_text(encoding="utf-8"))


# ------------------------------------------------------------ phiếu thu và két

def _diem():
	from vagabond import diem_ban
	return [diem_ban._chuan(d, i) for i, d in enumerate(diem_ban.MAC_DINH)]


@ca("v630 phiếu cọc chuyển khoản qua đủ bốn hàng rào dat_banh: quầy Sales Online, chỉ trỏ phiếu đặt, đúng phiếu đặt")
def _rao():
	q = tkr.quay_chuyen_khoan(_diem())
	la("quầy chuyển khoản là điểm không két", q, "SALES")
	p = tkr.phieu_thu("SO-1", "KH-1", 7560000, 3780000, q, tkr.PT_CK, "2026-11-03",
		{"name": "BT-9", "ma_tham_chieu": "FT123"}, "cọc")
	la("qua hàng rào", tkr.loi_phieu(p), None)
	la("ô của phiếu", (p["vgb_quay"], p["vgb_phieu_dat"], p["vgb_gd_tkr"], p["mode_of_payment"], p["reference_no"], p["paid_amount"]),
		("SALES", "SO-1", "BT-9", "Chuyển khoản", "FT123", 3780000.0))
	la("chỉ một dòng tham chiếu phiếu đặt", [(r["reference_doctype"], r["reference_name"], r["allocated_amount"]) for r in p["references"]],
		[("Sales Order", "SO-1", 3780000.0)])
	# Bốn đường hỏng: bỏ quầy, trỏ thêm hoá đơn, trỏ phiếu đặt khác, hai phiếu đặt.
	dung("thiếu quầy bị chặn", tkr.loi_phieu(dict(p, vgb_quay="")))
	dung("trỏ thêm hoá đơn bị chặn", tkr.loi_phieu(dict(p, references=p["references"] + [{"reference_doctype": "Sales Invoice", "reference_name": "SI-1"}])))
	dung("trỏ phiếu đặt khác bị chặn", tkr.loi_phieu(dict(p, references=[{"reference_doctype": "Sales Order", "reference_name": "SO-2"}])))
	dung("hai phiếu đặt bị chặn", tkr.loi_phieu(dict(p, references=[{"reference_doctype": "Sales Order", "reference_name": "SO-1"},
		{"reference_doctype": "Sales Order", "reference_name": "SO-2"}])))
	dung("điểm có két không bao giờ thành quầy chuyển khoản", tkr.quay_chuyen_khoan([{"ma": "TCV", "quay": "TCV", "bat": 1}]) == "SALES")


def _pe_gia(ds):
	"""frappe.get_all giả lọc đúng ô vgb_quay như cơ sở dữ liệu."""
	def get_all(dt, filters=None, **k):
		if dt != "Payment Entry":
			return []
		f = filters or {}
		return [_fr._dict(r) for r in ds if r["vgb_quay"] == f.get("vgb_quay") and r["docstatus"] == f.get("docstatus")]
	return get_all


@ca("v630 két: cọc chuyển khoản (quầy SALES) không vào két cửa hàng, tiền mặt phần còn lại vào đúng két quầy thu, hoá đơn Trả trước rơi khỏi đối soát")
def _ket():
	from vagabond import ca_quay, dat_banh
	ds = [
		{"name": "PE-COC", "vgb_quay": "SALES", "docstatus": 1, "mode_of_payment": "Chuyển khoản", "received_amount": 3780000, "paid_amount": 3780000},
		{"name": "PE-TM", "vgb_quay": "TCV", "docstatus": 1, "mode_of_payment": "Tiền mặt", "received_amount": 3780000, "paid_amount": 3780000},
	]
	with mock.patch.object(_fr, "get_all", _pe_gia(ds)):
		tcv = dat_banh.thu_ung_truoc("TCV", "2026-11-14 08:00:00", "2026-11-14 22:00:00")
		sales = dat_banh.thu_ung_truoc("SALES", "2026-11-03", "2026-11-03", theo_ngay=True)
	la("két TCV chỉ có tiền mặt thu tại quầy", tcv, {"Tiền mặt": 3780000.0})
	la("Sales Online chỉ có chuyển khoản", sales, {"Chuyển khoản": 3780000.0})
	# Ngày giao ở TCV: hoá đơn 7.560.000 mang "Trả trước" + tiền mặt 3.780.000 thu trong ca.
	ngoai = set(["Trả trước", "Số dư trả trước", "Công nợ", "Grab Dine-Out", "Hàng tặng"])
	trong, ngoai_ket = ca_quay.loc_trong_ket({"Trả trước": 7560000.0, "Tiền mặt": tcv["Tiền mặt"]}, ngoai)
	la("hoá đơn Trả trước ngoài két", ngoai_ket, {"Trả trước": 7560000.0})
	bang = ca_quay.ghep_chi_tien_mat(trong, 3780000 + 500000, 500000)
	tm = [d for d in bang if d["phuong_thuc"] == "Tiền mặt"]
	la("máy đòi đúng tiền mặt thu tại quầy", [d["may"] for d in tm], [3780000.0])
	la("thu ngân đếm đúng thì không lệch", sum(float(d.get("lech") or 0) for d in bang), 0.0)
	dung("không dòng Chuyển khoản nào ở két quầy", not [d for d in bang if d["phuong_thuc"] == "Chuyển khoản"])
	# Sales Online: dòng chuyển khoản đếm = máy, không đòi lý do.
	bang2 = ca_quay.ghep_chi_tien_mat(sales, 0, 0)
	la("Sales Online không lệch vì cọc chuyển khoản", sum(float(d.get("lech") or 0) for d in bang2), 0.0)


@ca("v630 'Trả trước' thuộc nhóm tiền về ngày khác, nằm trong _ngoai_ket của Chốt ca (đọc cấu hình mặc định)")
def _tra_truoc_ngoai_ket():
	from vagabond import pt_thanh_toan, ca_quay
	dung("Trả trước ngày khác", "Trả trước" in pt_thanh_toan.thu_ngay_khac())
	dung("Chuyển khoản không bị loại khỏi két (là dòng đếm bằng máy)", "Chuyển khoản" not in ca_quay._ngoai_ket())
	dung("Trả trước bị loại khỏi két", "Trả trước" in ca_quay._ngoai_ket())


# ------------------------------------------------------------ còn phải thu, trạng thái

@ca("v630 còn phải thu tính ở máy chủ: phiếu nháp đã chiếm sao kê vẫn tính, phiếu huỷ không tính, không âm")
def _con_lai():
	tong = 7560000
	la("chưa có gì", tkr.con_phai_thu(tong, []), 7560000.0)
	la("cọc nháp", tkr.con_phai_thu(tong, [{"so_tien": 3780000, "docstatus": 0}]), 3780000.0)
	la("cọc huỷ không tính", tkr.con_phai_thu(tong, [{"so_tien": 3780000, "docstatus": 2}]), 7560000.0)
	la("thu đủ", tkr.con_phai_thu(tong, [{"so_tien": 3780000, "docstatus": 1}, {"so_tien": 3780000, "docstatus": 1}]), 0.0)
	la("thu dư không âm", tkr.con_phai_thu(tong, [{"so_tien": 9000000, "docstatus": 1}]), 0.0)
	la("chờ cọc", tkr.trang_thai(tong, [], False, False)[0], "cho_coc")
	la("đã cọc", tkr.trang_thai(tong, [{"so_tien": 3780000, "docstatus": 0}], False, False)[0], "da_coc")
	la("thu đủ", tkr.trang_thai(tong, [{"so_tien": 7560000, "docstatus": 1}], False, False)[0], "du_tien")
	la("đã giao", tkr.trang_thai(tong, [{"so_tien": 7560000, "docstatus": 1}], True, False)[0], "da_giao")
	la("đã huỷ", tkr.trang_thai(tong, [], False, True)[0], "da_huy")
	la("phiếu huỷ không thành đã cọc", tkr.trang_thai(tong, [{"so_tien": 3780000, "docstatus": 2}], False, False)[0], "cho_coc")


# ------------------------------------------------------------ chiếm sao kê

def _gd(ten, tien, mo, ngay="2026-11-03"):
	return {"name": ten, "tien": tien, "mo_ta": mo, "date": ngay}


@ca("v630 chiếm sao kê: dòng đã có chủ ở luồng khác bị bỏ qua, không lập phiếu thứ hai cho cùng một lần chuyển")
def _chiem():
	ds = [_gd("BT-1", 3780000, "MBVCB.123 TKR26110001 coc")]
	nhan, xem = tkr.chon_giao_dich(ds, "TKR26110001", {}, 3780000, 7560000, 0)
	la("dòng chưa chủ được nhận", [(x["gd"]["name"], x["so_tien"]) for x in nhan], [("BT-1", 3780000.0)])
	nhan, xem = tkr.chon_giao_dich(ds, "TKR26110001", {"BT-1": "phiếu công nợ DNTT-1"}, 3780000, 7560000, 0)
	la("dòng đã có chủ bỏ qua", (nhan, xem), ([], []))


@ca("v630 chiếm sao kê: mã dính số (TKR261100012), dòng mang hai mã, chuyển thiếu cọc, chuyển dư đều KHÔNG tự lập phiếu")
def _chiem_chan():
	ma, coc, tong = "TKR26110001", 3780000, 7560000
	la("mã dính số", tkr.chon_giao_dich([_gd("A", 3780000, "TKR261100012")], ma, {}, coc, tong, 0), ([], []))
	n, x = tkr.chon_giao_dich([_gd("B", 7560000, "TKR26110001 TKR26110002")], ma, {}, coc, tong, 0)
	la("hai mã để khớp tay", (n, [y["gd"] for y in x]), ([], ["B"]))
	n, x = tkr.chon_giao_dich([_gd("C", 3000000, "TKR26110001")], ma, {}, coc, tong, 0)
	la("thiếu cọc", (n, [y["gd"] for y in x]), ([], ["C"]))
	n, x = tkr.chon_giao_dich([_gd("D", 9000000, "TKR26110001")], ma, {}, coc, tong, 0)
	la("dư tổng", (n, [y["gd"] for y in x]), ([], ["D"]))
	n, x = tkr.chon_giao_dich([_gd("E", 7560000, "tkr 2611 0001")], ma, {}, coc, tong, 0)
	la("trả đủ một lần, mã có cách", [(y["gd"]["name"], y["so_tien"]) for y in n], [("E", 7560000.0)])


@ca("v630 chiếm sao kê: hai lần chuyển (cọc rồi phần còn lại qua QR) nhận đủ; lần ba vượt tổng thì để người nhìn")
def _hai_lan():
	ma, coc, tong = "TKR26110001", 3780000, 7560000
	ds = [_gd("B1", 3780000, ma, "2026-11-03"), _gd("B2", 3780000, ma, "2026-11-14"), _gd("B3", 100000, ma, "2026-11-15")]
	n, x = tkr.chon_giao_dich(ds, ma, {}, coc, tong, 0)
	la("hai phiếu", [(y["gd"]["name"], y["so_tien"]) for y in n], [("B1", 3780000.0), ("B2", 3780000.0)])
	la("lần ba xem lại", [y["gd"] for y in x], ["B3"])
	n, x = tkr.chon_giao_dich(ds[1:], ma, {}, coc, tong, 3780000)
	la("đã cọc thì phần còn lại nhận dưới mức cọc", [y["gd"]["name"] for y in n], ["B2"])


class _Lap(object):
	"""Frappe giả cho khop_mot: một phiếu đặt, các dòng sao kê, phiếu thu lập ra."""

	def __init__(self, gds, chu=None, phieu=None):
		self.gds, self.chu, self.phieu, self.lap, self.tin = gds, dict(chu or {}), list(phieu or []), [], []

	def sql(self, q, a=None, as_dict=False):
		if "from `tabSales Order`" in q:
			return [_fr._dict(name="SO-1", docstatus=1, status="To Deliver and Bill", vgb_tkr_ma="TKR26110001",
				vgb_tkr_coc=3780000, customer="KH-1", grand_total=7560000, rounded_total=7560000, per_billed=0)]
		if "from `tabBank Transaction`" in q:
			return [_fr._dict(g) for g in self.gds]
		return []

	def get_all(self, dt, filters=None, **k):
		if dt == "Payment Entry":
			return [_fr._dict(p) for p in self.phieu]
		return []

	def get_doc(self, d):
		lap = self
		class Doc(_fr._dict):
			def setup_party_account_field(self):
				pass

			def set_missing_values(self):
				pass

			def insert(self, **k):
				self.name = "PE-%d" % (len(lap.lap) + 1)
				lap.lap.append(dict(self))
				lap.phieu.append({"name": self.name, "docstatus": 0, "paid_amount": self.paid_amount,
					"received_amount": self.received_amount, "vgb_gd_tkr": self.vgb_gd_tkr})
				lap.chu[self.vgb_gd_tkr] = "phiếu thu thiết kế riêng " + self.name
		doc = Doc(d)
		doc.flags = _fr._dict()
		return doc


def _chay_khop(l):
	from vagabond import doi_soat_sepay as dss
	from vagabond import thu_tien
	import contextlib
	ps = [mock.patch.object(_fr.db, "sql", l.sql), mock.patch.object(_fr, "get_all", l.get_all),
		mock.patch.object(_fr, "get_doc", l.get_doc),
		mock.patch.object(_fr.db, "get_value", lambda dt, ten, f=None, **k: "1121 - MB" if dt == "Bank Account" else "{}"),
		mock.patch.object(_fr.db, "exists", lambda *a, **k: True),
		mock.patch.object(dss, "chu_cua_giao_dich", lambda ds, **k: {g: c for g, c in l.chu.items() if g in ds}),
		mock.patch.object(dss, "tai_khoan_duoc_khop", lambda: {"BA-MB"}),
		mock.patch.object(thu_tien, "nang_quyen_lap_phieu", contextlib.nullcontext),
		mock.patch.object(tkr, "_ds_diem", _diem), mock.patch.object(tkr, "_cong_ty", lambda: "Vagabond"),
		mock.patch.object(tkr, "_bao_sales_coc", lambda *a, **k: l.tin.append("sales")),
		mock.patch.object(tkr, "_bao_bep_coc", lambda *a, **k: l.tin.append("bep"))]
	for p in ps:
		p.start()
	try:
		return tkr.khop_mot("SO-1")
	finally:
		for p in reversed(ps):
			p.stop()


@ca("v630 khop_mot chạy thật: lập MỘT phiếu thu nháp trỏ phiếu đặt, chiếm đúng dòng; chạy lại (nhịp 5 phút, khách hỏi) không lập đôi")
def _khop_mot():
	g = {"name": "BT-7", "date": "2026-11-03", "deposit": 3780000, "withdrawal": 0, "description": "TKR26110001 coc",
		"reference_number": "FT26307", "bank_account": "BA-MB", "transaction_id": "x"}
	l = _Lap([g])
	la("lần đầu lập một phiếu", _chay_khop(l), 1)
	p = l.lap[0]
	la("phiếu đúng ô", (p["vgb_gd_tkr"], p["vgb_quay"], p["vgb_phieu_dat"], p["paid_to"], p["bank_account"], p["paid_amount"], p["company"]),
		("BT-7", "SALES", "SO-1", "1121 - MB", "BA-MB", 3780000.0, "Vagabond"))
	la("tham chiếu ngân hàng", p["reference_no"], "FT26307")
	la("chạy lại không lập thêm", _chay_khop(l), 0)
	la("tổng phiếu", len(l.lap), 1)
	la("báo Sales và bếp đúng một lần", l.tin, ["sales", "bep"])
	l2 = _Lap([dict(g, bank_account="BA-LA")])
	la("tài khoản chưa nối SePay không lập", _chay_khop(l2), 0)


@ca("v630 hoá đơn ngày giao chỉ cấn phiếu ĐÃ GHI SỔ của đúng phiếu đặt, không vơ tiền nạp số dư; thiếu thì chặn")
def _ung_truoc():
	ung = [
		{"reference_type": "Payment Entry", "reference_name": "PE-NAP", "amount": 5000000},
		{"reference_type": "Payment Entry", "reference_name": "PE-COC", "amount": 3780000},
		{"reference_type": "Payment Entry", "reference_name": "PE-TM", "amount": 3780000},
		{"reference_type": "Journal Entry", "reference_name": "JE-1", "amount": 100},
	]
	ra, loi = tkr.chon_ung_truoc(ung, ["PE-COC", "PE-TM"], 7560000)
	la("chỉ hai phiếu của đơn", [(r["reference_name"], r["allocated_amount"]) for r in ra], [("PE-COC", 3780000.0), ("PE-TM", 3780000.0)])
	la("không lỗi", loi, "")
	ra, loi = tkr.chon_ung_truoc(ung, ["PE-COC"], 7560000)
	dung("thiếu thì báo lỗi", "3.780.000" in loi)


@ca("v630 hoá đơn Trả trước lập từ phiếu đặt không bị phép so nguồn đơn chặn; hoá đơn tay mang Trả trước vẫn bị chặn")
def _tra_truoc_nguon():
	from vagabond.dat_banh import la_hoa_don_tra_truoc as la_tt
	dung("từ phiếu đặt", la_tt("Trả trước", ["SO-1"]))
	dung("một dòng không trỏ phiếu đặt", not la_tt("Trả trước", ["SO-1", ""]))
	dung("không có dòng", not la_tt("Trả trước", []))
	dung("phương thức khác", not la_tt("Tiền mặt", ["SO-1"]))
	s = (GOC / "vagabond/ban_hang.py").read_text(encoding="utf-8")
	i = s.index("def kiem_truoc_khi_luu(")
	than = s[i:s.index("\ndef ", i + 10)]
	dung("hook lưu hoá đơn gọi phép miễn trước phép so nguồn", 0 < than.find("la_hoa_don_tra_truoc(") < than.find("_pt_cho_nguon(nguon)"))


# ------------------------------------------------------------ sổ đối soát, quyền, tin

@ca("v630 sổ đối soát SePay chung có luồng thiết kế riêng: ô vgb_gd_tkr trên phiếu thu, phiếu huỷ nhả dòng, ba cửa chung bị chặn")
def _so_doi_soat():
	from vagabond import doi_soat_sepay as dss
	dung("có trong danh sách nạp", "thiet_ke_rieng" in dss.MO_DUN_KHAI)
	b = dss._SO.get("thiet_ke_rieng")
	dung("đã khai", bool(b))
	la("ô và doctype", (b["doctype"], b["truong_gd"], b["loc_chiem"], b["chieu"]), ("Payment Entry", "vgb_gd_tkr", {"docstatus": ["<", 2]}, dss.VAO))
	nem("cửa chung đọc bị chặn", b["quyen_doc"])
	nem("cửa chung ghi bị chặn", b["quyen_ghi"])
	la("trường mới có insert_after", [f["fieldname"] for d in tkr.TRUONG_MOI.values() for f in d if not f.get("insert_after")], [])


@ca("v630 quyền màn Đơn đặt trước: bản JS trùng tuyệt đối bản máy chủ")
def _quyen():
	s = (GOC / "vagabond/public/js/bep/63-don-dat-truoc.js").read_text(encoding="utf-8")
	m = re.search(r"var QUYEN_TKR = \[(.*?)\];", s, re.S)
	la("hai bản", re.findall(r"'([^']+)'", m.group(1)), list(tkr.QUYEN_TKR))


@ca("v630 tin Zalo: bốn mã tin có trong danh mục, bản JS trùng từng chữ, tin Sales và bếp không mang số tiền")
def _tin():
	ut = sys.modules["frappe.utils"]
	if not hasattr(ut, "get_url"):
		ut.get_url = lambda *a, **k: "https://erp.vagabond.test"
	from vagabond import kenh_zalo as kz
	js = (GOC / "vagabond/public/js/cai_dat_loi_chung.js").read_text(encoding="utf-8")
	for ma in ("bh_tkr_moi", "bh_tkr_da_coc", "bh_tkr_tu_van", "bep_tkr_da_coc"):
		dung(ma + " có trong TIN", ma in kz.TIN)
		bp, ten, gt = kz.TIN[ma][:3]
		dung(ma + " bản JS", "%s: ['%s', '%s', '%s']" % (ma, bp, ten, gt) in js)
		dung(ma + " nhóm không nhận tiền", kz.khong_duoc_tien(ma))
	don = tkr.chuan_don(_don(), TP, HOM, DIEM)
	for loai in ("moi", "coc", "tu_van"):
		chu = tkr.tin_don(don, "TKR26110001", loai)
		la("tin %s không có số tiền" % loai, kz.MAU_TIEN.findall(chu), [])
		dung("tin %s có mã đơn hoặc tác phẩm" % loai, "Croquembouche" in chu)


@ca("v630 cửa ngõ: bốn hàm khách vãng lai có trần lượt, sáu hàm màn app kiểm vai trước khi chạm dữ liệu")
def _cua_ngo():
	import ast
	cay = ast.parse((GOC / "vagabond/thiet_ke_rieng.py").read_text(encoding="utf-8"))
	for f in cay.body:
		if not isinstance(f, ast.FunctionDef):
			continue
		trang = [ast.unparse(d) for d in f.decorator_list]
		if not any("whitelist" in d for d in trang):
			continue
		if any("allow_guest=True" in d for d in trang):
			dung(f.name + " khách có rate_limit", any(d.startswith("rate_limit") for d in trang))
			dung(f.name + " khách chỉ POST", any("methods=['POST']" in d for d in trang))
		else:
			than = [x for x in f.body if not (isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant) and isinstance(x.value.value, str))]
			dau = ast.unparse(than[0])
			dung(f.name + " kiểm vai đầu tiên", "_kiem_quyen()" in dau)


@ca("v630 dat chạy thật: giá gửi xuống phiếu đặt là giá máy chủ; gửi lại cùng mã lần trả đơn cũ")
def _dat_that():
	nd = copy.deepcopy(nw.MAC_DINH)
	nd["khoi"].append(dict(TP))
	goi = {}

	def lap(don, lan):
		goi["don"], goi["lan"] = don, lan
		return _fr._dict(name="SO-9", vgb_tkr_ma="TKR26110009")
	ps = [mock.patch("vagabond.noi_dung_web._ban_cong_khai", lambda khoa=False: copy.deepcopy(nd)),
		mock.patch.object(tkr, "_diem_nhan", lambda ban: DIEM), mock.patch.object(tkr, "_hom_nay", lambda: HOM),
		mock.patch.object(tkr, "_da_gui", lambda lan, dau: None), mock.patch.object(tkr, "_lap_phieu_dat", lap),
		mock.patch.object(tkr, "_bao_moi", lambda *a, **k: None), mock.patch.object(tkr, "_ket_qua", lambda ten: {"ok": 1, "ma": ten})]
	for p in ps:
		p.start()
	try:
		kq = tkr.dat(json.dumps(_don(tong=1, coc=1)), "123e4567-e89b-42d3-a456-426614174000")
	finally:
		for p in reversed(ps):
			p.stop()
	la("trả đơn", kq, {"ok": 1, "ma": "SO-9"})
	la("giá máy chủ", (goi["don"]["tong"], goi["don"]["coc"]), (7560000, 3780000))
	la("mã lần băm, không lưu thô", len(goi["lan"]), 40)
	nem("mã lần sai dạng", lambda: tkr.dat("{}", "abc"))


# ------------------------------------------------------------ JS cùng luật

BANG = [("M", ["Hoa lan trắng"]), ("S", []), ("L", ["Không hoa", "Thêm bục trắng"]), ("M", ["Hoa lan trắng", "Không hoa"]),
	("XL", []), ("S", ["Kim tuyến"])]


@ca("v630 bản JS tkrTinh, tkrCoc, ngày sớm nhất chạy trên CÙNG bảng ca với máy chủ và ra cùng số")
def _js_cung_luat():
	tp = copy.deepcopy(TP)
	tp["trang_tri"][3]["gia_them"] = 350000
	js = ("import {tkrTinh, tkrCoc, tkrNgaySomNhat} from './vagabond/public/web_vue/kho/thuan.js';"
		"const tp = %s, bang = %s;"
		"console.log(JSON.stringify({tinh: bang.map(([k, t]) => tkrTinh(tp, k, t)), coc: [5941000, 1, 0, 2001].map(tkrCoc),"
		"ngay: [tkrNgaySomNhat('2026-11-02', tp), tkrNgaySomNhat('2026-12-28', Object.assign({}, tp, {so_ngay: '3'}))]}));"
		% (json.dumps(tp, ensure_ascii=False), json.dumps(BANG, ensure_ascii=False)))
	ra = _node(js)
	for (kc, tt), j in zip(BANG, ra["tinh"]):
		try:
			p = tkr.tinh_gia(tp, kc, tt)
			la("JS %s %s" % (kc, tt), (j.get("tong"), j.get("coc"), j.get("con_lai")), (p["tong"], p["coc"], p["con_lai"]))
		except ValueError as e:
			la("JS lỗi %s %s" % (kc, tt), j.get("loi"), str(e))
	la("cọc JS", ra["coc"], [tkr.tien_coc(x) for x in (5941000, 1, 0, 2001)])
	la("ngày JS", ra["ngay"], [str(tkr.ngay_som_nhat("2026-11-02", tp)), str(tkr.ngay_som_nhat("2026-12-28", dict(tp, so_ngay="3")))])


# ------------------------------------------------------------ hành vi node

def _hanh_vi(tep, toi_thieu):
	r = subprocess.run(["node", "vagabond/khung/kiem_thu/hanh_vi/" + tep], cwd=GOC, capture_output=True, text=True, timeout=120)
	la(r.stdout[-1500:] + r.stderr[-1500:], r.returncode, 0)
	m = re.search(r"(\d+) ca dat, 0 ca hong", r.stdout)
	dung("đủ số ca " + tep, m and int(m.group(1)) >= toi_thieu)


@ca("v630 tab Thiết kế riêng chạy Vue thật: danh sách, trang tác phẩm, đặt cọc, QR, hỏi trạng thái (hanh_vi/thiet_ke_rieng_630.mjs)")
def _vue():
	_hanh_vi("thiet_ke_rieng_630.mjs", 10)


@ca("v630 màn Đơn đặt trước nạp thật phần 62: thu tiền mặt, QR, giao bánh, huỷ, ghi sổ (hanh_vi/don_dat_truoc_630.js)")
def _app():
	_hanh_vi("don_dat_truoc_630.js", 8)
