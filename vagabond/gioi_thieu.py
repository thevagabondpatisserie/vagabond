# -*- coding: utf-8 -*-
"""Mã giới thiệu và hoa hồng giới thiệu (v638, anh Việt duyệt 04/11/2026).

Nhân viên mời người quen đặt bánh trên web hoặc gọi món tại bàn. Khách gõ
SỐ ĐIỆN THOẠI của nhân viên đó vào ô "Mã giới thiệu". Đơn ghi sổ hoá đơn xong
thì nhân viên được hoa hồng, cuối tháng cộng vào phiếu KPI tháng có sẵn rồi đi
Đề nghị chi như hoa hồng doanh số.

Những điều anh Việt chốt, và chỗ mỗi điều được giữ trong tệp này:

  - Ai được giới thiệu: tài khoản nhân viên ĐANG HOẠT ĐỘNG (User enabled,
    System User) có số ở ô mobile_no. So theo chữ số, chịu +84, khoảng trắng,
    dấu chấm. Hai người cùng một số thì KHÔNG nhận ai cả: đoán một trong hai
    là trả tiền nhầm người. `chon_nhan_vien`.
  - Trên web khách chỉ thấy TÊN GỌI (chữ cuối của họ tên), không thấy số đầy
    đủ, email hay họ tên. `ten_goi`, cửa `kiem`.
  - Khách đặt bằng chính số của nhân viên được giới thiệu (tự giới thiệu
    mình) thì không tính; nhân viên đặt bằng số khác vẫn tính. `tu_gioi_thieu`.
  - % chốt LÚC ĐẶT đơn: đơn web chép % vào bản ghi Don Web khi khách gửi đơn,
    đơn tại bàn chép % lúc thu ngân gắn người giới thiệu. Đổi % trong Cài đặt
    chỉ áp cho đơn từ lúc đổi.
  - Tính trên tiền hàng SAU ưu đãi, KHÔNG gồm phí giao (dòng món DVBH00001,
    xem phi_giao.py), chỉ khi hoá đơn đã ghi sổ. Huỷ hoá đơn hoặc hoàn tiền
    (tờ trả hàng ghi sổ) thì hoa hồng về 0. `tien_tinh`, `khi_ghi_so`,
    `khi_huy`.
  - Đơn tại bàn: hoa hồng giới thiệu CỘNG THÊM, kể cả khi người giới thiệu
    cũng là người bán có hoa hồng doanh số. Hai ô khác nhau, hai phép tính
    khác nhau, phép này không đọc ô người bán.
  - Mỗi đơn MỘT người giới thiệu. Thu ngân không sửa được; muốn đổi phải là
    quản lý (VAI_DOI) trên app, máy ghi ai đổi, lúc nào. `doi_nguoi`.
  - Trả tiền: cuối tháng "Đưa vào phiếu KPI tháng" ghi số vào một ô riêng
    trên phiếu KPI của từng người (không đụng phép luỹ tiến doanh số), chạy
    lại bao nhiêu lần cũng không cộng hai lần. `ke_hoach_kpi`, `dua_vao_kpi`.

Không ném lỗi làm hỏng việc bán: mọi đường gắn và tính đều bọc lại, lỗi ghi
Error Log. Mất một khoản hoa hồng sửa được, mất một tờ hoá đơn thì không.
"""

import json
import re

# ------------------------------------------------------------ phần thuần
# Trên mốc này KHÔNG chạm Frappe, để kiểm thử được mà không cần site.

DT_HD = "Sales Invoice"
DT_DW = "Vagabond Don Web"
DT_KPI = "Vagabond KPI Phieu"

# Ô trên Cài đặt (mục Bán hàng & thanh toán).
O_BAT = "vgb_gt_bat"
O_PT_WEB = "vgb_gt_pt_web"
O_PT_TAI_BAN = "vgb_gt_pt_tai_ban"
PT_MAC_DINH = 2.0

# Ô trên hoá đơn.
O_NGUOI = "vgb_nguoi_gioi_thieu"
O_LOAI = "vgb_gt_loai"
O_PT = "vgb_gt_pt"
O_HH = "vgb_hh_gioi_thieu"
O_GHI_CHU = "vgb_gt_ghi_chu"
O_DOI_BOI = "vgb_gt_doi_boi"
O_DOI_LUC = "vgb_gt_doi_luc"
O_HD = (O_NGUOI, O_LOAI, O_PT)

# Ô trên Don Web: người và % chốt lúc khách gửi đơn.
O_DW_NGUOI = "vgb_nguoi_gioi_thieu"
O_DW_PT = "vgb_pt_gioi_thieu"

# Ô trên phiếu KPI tháng: một khoản CỘNG THÊM, không vào phép luỹ tiến.
O_KPI_HH = "vgb_hh_gioi_thieu"
O_KPI_DON = "vgb_hh_gioi_thieu_don"
O_KPI_LUC = "vgb_hh_gioi_thieu_luc"
BO_KPI = "gioi_thieu"

LOAI = {"web": "Đặt bánh web", "tai_ban": "Tại bàn"}
NHAN_TT = {"ghi_so": "Đã ghi sổ", "cho": "Chờ", "huy": "Đơn huỷ", "hoan": "Đã hoàn tiền"}

MA_PHI_GIAO = "DVBH00001"  # trùng phi_giao.MA_PHI_GIAO, ca kiểm chốt

# Ai thấy bảng toàn tiệm và đưa vào phiếu KPI: đúng bộ vai mở phân hệ KPI
# (kpi.VAI_XEM, ca kiểm chốt hai bên bằng nhau).
# Codex PR #541 vòng 5: vai quản lý cửa hàng THẬT trên site là "VGB - Quản lý
# cửa hàng" (vai_cua_hang.VAI_QLCH, đọc lại trên site 05/11/2026: không có vai
# tên "Quản lý cửa hàng"). Ca kiểm chốt trùng hằng bên vai_cua_hang.
VAI_QLCH = "VGB - Quản lý cửa hàng"
VAI_XEM = {
	"System Manager", "Giám đốc", "AP Giám đốc",
	"Accounts Manager", "Accounts User", "Kế toán",
	"Sales Manager", "Quản lý cửa hàng", "Bếp trưởng", VAI_QLCH,
}
# Ai đổi được người giới thiệu của một đơn: Giám đốc và quản lý bán hàng.
# Không có thu ngân, không có kế toán: ô này quyết tiền rơi vào tay ai.
VAI_DOI = {"System Manager", "Giám đốc", "AP Giám đốc", "Sales Manager", VAI_QLCH}

MAY = {"Administrator", "Guest", ""}

TRUONG_MOI = {
	"Vagabond Settings": [
		{"fieldname": "vgb_sec_gioi_thieu", "label": "Hoa hồng giới thiệu", "fieldtype": "Section Break",
			"insert_after": "hang_tang_xuat_kho_that",
			"description": "Khách gõ số điện thoại nhân viên đã mời mình vào ô Mã giới thiệu (đặt bánh web, gọi món tại bàn). "
				"Hoá đơn ghi sổ xong thì nhân viên được hoa hồng, cuối tháng cộng vào phiếu KPI."},
		{"fieldname": O_BAT, "label": "Hoa hồng giới thiệu", "fieldtype": "Check", "default": "1",
			"insert_after": "vgb_sec_gioi_thieu",
			"description": "Tắt thì ô Mã giới thiệu ẩn khỏi trang đặt bánh và máy không nhận người giới thiệu cho đơn mới. "
				"Đơn đã nhận trước lúc tắt vẫn được tính."},
		{"fieldname": "vgb_cb_gioi_thieu", "fieldtype": "Column Break", "insert_after": O_BAT},
		{"fieldname": O_PT_WEB, "label": "% hoa hồng đơn đặt bánh web", "fieldtype": "Percent", "default": "2",
			"insert_after": "vgb_cb_gioi_thieu",
			"description": "Tính trên tiền bánh sau ưu đãi, không gồm phí giao. Từ 0 tới 100. Đổi số chỉ áp cho đơn đặt từ lúc đổi."},
		{"fieldname": O_PT_TAI_BAN, "label": "% hoa hồng đơn gọi món tại bàn", "fieldtype": "Percent", "default": "2",
			"insert_after": O_PT_WEB,
			"description": "Cộng thêm cho người giới thiệu, kể cả khi người đó cũng là người bán. Từ 0 tới 100. "
				"Đổi số chỉ áp cho đơn gắn người giới thiệu từ lúc đổi."},
	],
	DT_HD: [
		{"fieldname": O_NGUOI, "label": "Người giới thiệu", "fieldtype": "Link", "options": "User",
			"insert_after": "vgb_nguoi_ban", "read_only": 1, "no_copy": 1, "in_standard_filter": 1,
			"description": "Nhân viên khách đã gõ số vào ô Mã giới thiệu. Thu ngân không sửa được; quản lý đổi trên app, "
				"màn Hoa hồng giới thiệu."},
		{"fieldname": O_LOAI, "label": "Loại đơn giới thiệu", "fieldtype": "Select", "options": "\nweb\ntai_ban",
			"insert_after": O_NGUOI, "read_only": 1, "no_copy": 1,
			"description": "web: đặt bánh trên web. tai_ban: gọi món tại bàn."},
		{"fieldname": O_PT, "label": "% hoa hồng giới thiệu", "fieldtype": "Percent",
			"insert_after": O_LOAI, "read_only": 1, "no_copy": 1,
			"description": "Chốt lúc khách đặt đơn, đổi % trong Cài đặt sau đó không đổi số này."},
		{"fieldname": O_HH, "label": "Hoa hồng giới thiệu", "fieldtype": "Currency",
			"insert_after": O_PT, "read_only": 1, "no_copy": 1,
			"description": "Máy tính khi hoá đơn ghi sổ: tiền hàng sau ưu đãi, không gồm phí giao, nhân %. "
				"Huỷ hoá đơn hoặc hoàn tiền thì về 0."},
		{"fieldname": O_GHI_CHU, "label": "Ghi chú hoa hồng giới thiệu", "fieldtype": "Small Text",
			"insert_after": O_HH, "read_only": 1, "no_copy": 1},
		{"fieldname": O_DOI_BOI, "label": "Người giới thiệu đổi bởi", "fieldtype": "Link", "options": "User",
			"insert_after": O_GHI_CHU, "read_only": 1, "no_copy": 1},
		{"fieldname": O_DOI_LUC, "label": "Người giới thiệu đổi lúc", "fieldtype": "Datetime",
			"insert_after": O_DOI_BOI, "read_only": 1, "no_copy": 1},
	],
	DT_DW: [
		{"fieldname": "vgb_sec_gioi_thieu", "label": "Giới thiệu", "fieldtype": "Section Break",
			"insert_after": "vgb_onepay_gd"},
		{"fieldname": O_DW_NGUOI, "label": "Người giới thiệu", "fieldtype": "Link", "options": "User",
			"insert_after": "vgb_sec_gioi_thieu", "read_only": 1, "no_copy": 1,
			"description": "Máy gắn lúc khách gửi đơn từ số khách gõ vào ô Mã giới thiệu."},
		{"fieldname": O_DW_PT, "label": "% hoa hồng giới thiệu", "fieldtype": "Percent",
			"insert_after": O_DW_NGUOI, "read_only": 1, "no_copy": 1,
			"description": "Chốt lúc khách gửi đơn, chép sang hoá đơn khi hoá đơn ghi sổ."},
	],
	DT_KPI: [
		{"fieldname": O_KPI_HH, "label": "Hoa hồng giới thiệu (cộng thêm)", "fieldtype": "Currency",
			"insert_after": "bi_tran", "read_only": 1,
			"description": "Tổng hoa hồng giới thiệu của các hoá đơn đã ghi sổ trong tháng. Không nhân hệ số xếp loại, "
				"không tính vào trần. Đẩy chi cùng hoa hồng doanh số."},
		{"fieldname": O_KPI_LUC, "label": "Đưa hoa hồng giới thiệu vào lúc", "fieldtype": "Datetime",
			"insert_after": O_KPI_HH, "read_only": 1},
		{"fieldname": O_KPI_DON, "label": "Hoá đơn tính hoa hồng giới thiệu (JSON)", "fieldtype": "Long Text",
			"insert_after": "so_lieu", "read_only": 1, "hidden": 1},
	],
}


def _so(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def chu_so(v):
	return "".join(ch for ch in str(v or "") if ch.isdigit())


def chuan_sdt(v):
	"""Số điện thoại về một dạng để so: 0 + chín chữ số. THUẦN.

	"+84 909 123 456", "84909123456", "0909.123.456", "909123456" đều ra
	"0909123456". Số không đủ dài thì rỗng: rỗng không bao giờ khớp ai.
	"""
	s = chu_so(v)
	if s.startswith("0084"):
		s = "0" + s[4:]
	elif s.startswith("84") and len(s) in (11, 12):
		s = "0" + s[2:]
	elif len(s) == 9 and not s.startswith("0"):
		s = "0" + s
	return s if 9 <= len(s) <= 12 else ""


def ten_goi(ho_ten, ten_dau=""):
	"""Tên gọi: chữ cuối của họ tên. "Nguyễn Thị Ngân" ra "Ngân". THUẦN."""
	chu = str(ho_ten or "").split() or str(ten_dau or "").split()
	return chu[-1] if chu else ""


def la_nhan_vien(u):
	"""Tài khoản này được làm người giới thiệu không. THUẦN."""
	u = u or {}
	return (int(_so(u.get("enabled"))) == 1 and (u.get("user_type") or "") == "System User"
		and str(u.get("name") or "") not in MAY)


def chon_nhan_vien(sdt, ds):
	"""Nhân viên duy nhất có số này, hoặc None. THUẦN.

	Tài khoản khoá, tài khoản không phải System User (khách web, Website User)
	không được tính. Trùng số hai người thì không nhận ai cả.
	"""
	so = chuan_sdt(sdt)
	if not so:
		return None
	trung = [u for u in (ds or []) if la_nhan_vien(u) and chuan_sdt(u.get("mobile_no")) == so]
	return trung[0] if len(trung) == 1 else None


def tu_gioi_thieu(sdt_nhan_vien, cac_sdt_khach):
	"""Khách đặt bằng chính số của nhân viên được giới thiệu. THUẦN."""
	nv = chuan_sdt(sdt_nhan_vien)
	if not nv:
		return False
	return any(chuan_sdt(x) == nv for x in (cac_sdt_khach or []) if chuan_sdt(x))


def chuan_pt(v, mac=PT_MAC_DINH):
	"""% hoa hồng đọc từ Cài đặt. Rỗng thì mặc định, kẹp trong 0 tới 100. THUẦN."""
	if v is None or v == "":
		return float(mac)
	try:
		x = float(v)
	except (TypeError, ValueError):
		return float(mac)
	return round(min(max(x, 0.0), 100.0), 2)


def loi_pt(v):
	"""Câu báo khi % ngoài khoảng 0 tới 100, hoặc rỗng nếu hợp lệ. THUẦN."""
	if v is None or v == "":
		return ""
	try:
		x = float(v)
	except (TypeError, ValueError):
		return "Gõ một con số từ 0 tới 100."
	if x < 0 or x > 100:
		return "Phần trăm hoa hồng phải từ 0 tới 100, đang là %s." % v
	return ""


def tien_tinh(dong, giam_tong=0):
	"""Tiền hàng tính hoa hồng: tổng dòng món trừ phí giao, rồi trừ giảm cả đơn. THUẦN.

	`dong` là các dòng hoá đơn {item_code, amount}: amount đã trừ giảm theo
	dòng. `giam_tong` là discount_amount cả đơn (ưu đãi, điểm thành viên),
	cả khoản giảm tính vào tiền hàng vì ưu đãi áp cho bánh chứ không cho phí
	giao. Không bao giờ âm.
	"""
	tong = 0.0
	for d in dong or []:
		if str((d or {}).get("item_code") or "").strip().upper() == MA_PHI_GIAO:
			continue
		tong += _so((d or {}).get("amount"))
	return int(round(max(0.0, tong - _so(giam_tong))))


def hoa_hong(tien, pt):
	"""Số hoa hồng, làm tròn đồng. THUẦN."""
	return int(round(max(0.0, _so(tien)) * chuan_pt(pt, 0) / 100.0))


def trang_thai(docstatus, huy_mem=0, da_hoan=False):
	"""Trạng thái hoa hồng của một hoá đơn. THUẦN."""
	ds = int(_so(docstatus))
	if ds == 2 or int(_so(huy_mem)):
		return "huy"
	if ds == 1:
		return "hoan" if da_hoan else "ghi_so"
	return "cho"


def ky_thang(ky, hom_nay):
	"""Mã kỳ dạng 2026-11 ra (mã, ngày đầu, ngày cuối). Sai dạng thì tháng hiện tại. THUẦN."""
	import datetime

	m = re.fullmatch(r"(\d{4})-(\d{2})", str(ky or "").strip())
	if m and 1 <= int(m.group(2)) <= 12:
		n, t = int(m.group(1)), int(m.group(2))
	else:
		hn = hom_nay if isinstance(hom_nay, datetime.date) else datetime.date(*[int(x) for x in str(hom_nay)[:10].split("-")])
		n, t = hn.year, hn.month
	dau = datetime.date(n, t, 1)
	sau = datetime.date(n + 1, 1, 1) if t == 12 else datetime.date(n, t + 1, 1)
	return "%04d-%02d" % (n, t), dau, sau - datetime.timedelta(days=1)


def dong_hoa_don(r, dong, da_hoan=False):
	"""Một dòng màn hình từ một hoá đơn có người giới thiệu. THUẦN.

	Hoá đơn đã ghi sổ: số hoa hồng là số máy CHỐT lúc ghi sổ (ô vgb_hh_gioi_thieu),
	không tính lại theo % hôm nay. Hoá đơn còn nháp: số tạm tính để nhân viên
	thấy trước, chưa phải tiền.
	"""
	r = r or {}
	tt = trang_thai(r.get("docstatus"), r.get("vgb_huy"), da_hoan)
	tien = tien_tinh(dong, r.get("discount_amount"))
	if tt == "ghi_so":
		hh = int(round(_so(r.get(O_HH))))
	elif tt == "cho":
		hh = hoa_hong(tien, r.get(O_PT))
	else:
		hh = 0
	pc = str(r.get("custom_pancake_display_id") or "").strip()
	return {
		"ma": r.get("name"), "nguon": "hd", "hien": ("Đơn #" + pc) if pc else str(r.get("name") or ""),
		"ngay": str(r.get("posting_date") or "")[:10], "loai": r.get(O_LOAI) or "tai_ban",
		"nguoi": r.get(O_NGUOI) or "", "tien_hang": tien, "pt": chuan_pt(r.get(O_PT), 0),
		"hoa_hong": hh, "tt": tt, "ghi_chu": r.get(O_GHI_CHU) or "",
		"doi_boi": r.get(O_DOI_BOI) or "", "doi_luc": str(r.get(O_DOI_LUC) or "")[:16],
	}


def dong_don_web(r, tien_hang):
	"""Một dòng màn hình từ đơn web CHƯA có hoá đơn (đang chờ hoặc đã huỷ). THUẦN."""
	r = r or {}
	tt = "huy" if (r.get("trang_thai") or "") == "Da huy" else "cho"
	pc = str(r.get("pancake_display_id") or "").strip()
	return {
		"ma": r.get("name"), "nguon": "dw", "hien": ("Đơn #" + pc) if pc else str(r.get("name") or ""),
		"ngay": str(r.get("ngay_nhan") or r.get("creation") or "")[:10], "loai": "web",
		"nguoi": r.get(O_DW_NGUOI) or "", "tien_hang": int(round(_so(tien_hang))), "pt": chuan_pt(r.get(O_DW_PT), 0),
		"hoa_hong": 0 if tt == "huy" else hoa_hong(tien_hang, r.get(O_DW_PT)), "tt": tt, "ghi_chu": "",
		"doi_boi": "", "doi_luc": "",
	}


def tong_hop(rows):
	"""Dòng tạm tính tháng: đã ghi sổ, đang chờ, đơn huỷ. THUẦN."""
	ra = {k: {"so_don": 0, "tien_hang": 0, "hoa_hong": 0} for k in ("ghi_so", "cho", "huy")}
	for r in rows or []:
		k = "huy" if r.get("tt") in ("huy", "hoan") else r.get("tt")
		if k not in ra:
			continue
		ra[k]["so_don"] += 1
		if k != "huy":
			ra[k]["tien_hang"] += int(r.get("tien_hang") or 0)
			ra[k]["hoa_hong"] += int(r.get("hoa_hong") or 0)
	return ra


def theo_nhan_vien(rows):
	"""Bảng toàn tiệm: một dòng một nhân viên, nhiều hoa hồng đứng trước. THUẦN."""
	gom = {}
	for r in rows or []:
		ng = r.get("nguoi") or ""
		if not ng:
			continue
		o = gom.setdefault(ng, {"nguoi": ng, "so_don": 0, "so_cho": 0, "tien_hang": 0, "hoa_hong": 0, "hoa_hong_cho": 0})
		if r.get("tt") == "ghi_so":
			o["so_don"] += 1
			o["tien_hang"] += int(r.get("tien_hang") or 0)
			o["hoa_hong"] += int(r.get("hoa_hong") or 0)
		elif r.get("tt") == "cho":
			o["so_cho"] += 1
			o["hoa_hong_cho"] += int(r.get("hoa_hong") or 0)
	return sorted(gom.values(), key=lambda o: (-o["hoa_hong"], -o["hoa_hong_cho"], o["nguoi"]))


def phieu_da_chot(p):
	"""Phiếu KPI đã chốt (đóng băng, đã đẩy chi, đã huỷ): không ghi đè. THUẦN,
	một phép cho cả bước lập kế hoạch lẫn bước ghi trong khoá."""
	p = p or {}
	return bool(int(_so(p.get("dong_bang")))) or p.get("trang_thai") in ("Da day chi", "Da huy")


def ke_hoach_kpi(rows, phieu):
	"""Đưa hoa hồng giới thiệu vào phiếu KPI: việc cần làm cho từng người. THUẦN.

	`rows` là các dòng của tháng (chỉ dòng Đã ghi sổ được tính). `phieu` là
	{nguoi: {name, hh, dong_bang, trang_thai}} các phiếu KPI đã có của tháng.

	Ô trên phiếu được GHI ĐÈ bằng tổng của tháng chứ không cộng thêm, nên chạy
	lại bao nhiêu lần cũng ra một số. Người từng có số mà nay về 0 (hoá đơn
	bị huỷ, hoàn tiền) thì ghi 0. Phiếu đã chốt (đóng băng, đã đẩy chi, đã
	huỷ) thì không đụng: sai sót kỳ cũ điều chỉnh ở kỳ mới.
	"""
	tong, don = {}, {}
	for r in rows or []:
		if r.get("tt") != "ghi_so" or not r.get("nguoi"):
			continue
		tong[r["nguoi"]] = tong.get(r["nguoi"], 0) + int(r.get("hoa_hong") or 0)
		don.setdefault(r["nguoi"], []).append([r.get("ma"), int(r.get("hoa_hong") or 0)])
	viec = []
	for ng in sorted(set(tong) | {k for k, v in (phieu or {}).items() if _so(v.get("hh"))}):
		so = tong.get(ng, 0)
		p = (phieu or {}).get(ng)
		if p is None:
			viec.append({"nguoi": ng, "viec": "tao" if so > 0 else "bo_qua", "so": so, "don": don.get(ng, [])})
			continue
		if phieu_da_chot(p):
			viec.append({"nguoi": ng, "viec": "da_chot", "so": so, "cu": int(round(_so(p.get("hh")))),
				"phieu": p.get("name"), "don": don.get(ng, [])})
			continue
		cu = int(round(_so(p.get("hh"))))
		viec.append({"nguoi": ng, "viec": "giu" if cu == so else "cap_nhat", "so": so, "cu": cu,
			"phieu": p.get("name"), "don": don.get(ng, [])})
	return viec


# ------------------------------------------------------- phần cần Frappe

import frappe  # noqa: E402
from frappe.utils import cint, flt, getdate, now_datetime, nowdate  # noqa: E402

try:
	from frappe.rate_limiter import rate_limit  # noqa: E402
except ImportError:  # Frappe giả của bộ kiểm tầng khung
	def rate_limit(**_kw):
		return lambda f: f


def _doc_o(ten):
	"""Giá trị một ô Cài đặt ĐÚNG như đang lưu; chưa từng lưu thì None.

	Không dùng `lib.cfg_o`: nó trả "" cho cả 0 lẫn chưa lưu, mà ở đây 0% là
	một lựa chọn thật còn chưa lưu thì phải về mặc định.
	"""
	try:
		r = frappe.db.sql("select value from `tabSingles` where doctype='Vagabond Settings' and field=%s", (ten,))
	except Exception:
		return None
	return r[0][0] if r else None


def bat():
	v = _doc_o(O_BAT)
	return True if v is None or v == "" else bool(cint(v))


def pt_cho(loai):
	return chuan_pt(_doc_o(O_PT_WEB if loai == "web" else O_PT_TAI_BAN))


def gieo_mac_dinh():
	"""Site chưa từng lưu ba ô thì ghi mặc định xuống (công tắc bật, 2%, 2%).

	Không gieo thì lần đầu ai đó bấm Lưu trang Cài đặt, Frappe ghi 0 cho ô
	Check và ô Percent chưa có giá trị: công tắc tự tắt, % về 0 mà không ai
	bấm gì. Chạy lại không đổi gì vì chỉ ghi ô CHƯA có dòng.
	"""
	for o, v in ((O_BAT, 1), (O_PT_WEB, PT_MAC_DINH), (O_PT_TAI_BAN, PT_MAC_DINH)):
		if _doc_o(o) is None:
			frappe.db.set_single_value("Vagabond Settings", o, v)


def kiem_cai_dat(doc, method=None):
	"""Hook validate của Vagabond Settings: % phải từ 0 tới 100."""
	for o, nhan in ((O_PT_WEB, "% hoa hồng đơn đặt bánh web"), (O_PT_TAI_BAN, "% hoa hồng đơn gọi món tại bàn")):
		loi = loi_pt(doc.get(o))
		if loi:
			frappe.throw("%s: %s" % (nhan, loi))


def _ds_nhan_vien():
	return frappe.get_all(
		"User", filters={"enabled": 1, "user_type": "System User"},
		fields=["name", "full_name", "first_name", "mobile_no", "enabled", "user_type"],
		limit_page_length=0,
	)


def tim_nhan_vien(sdt):
	return chon_nhan_vien(sdt, _ds_nhan_vien())


def ten_theo_sdt(sdt):
	"""Tên gọi nhân viên có số này, cho máy chủ gọi (gọi món tại bàn). Công tắc
	tắt hay không thấy thì rỗng. Không qua rate_limit của cửa khách `kiem`."""
	try:
		if not bat():
			return ""
		u = tim_nhan_vien(sdt)
		return ten_goi(u.get("full_name"), u.get("first_name")) if u else ""
	except Exception:
		return ""


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=20, seconds=600)
def kiem(sdt=None):
	"""Trang đặt bánh hỏi: số này là nhân viên nào. Chỉ trả TÊN GỌI.

	Không trả số, email, họ tên đầy đủ hay mã tài khoản: cửa này mở cho khách
	vãng lai, người lạ dò số không được biết gì hơn một chữ tên.
	"""
	if not bat():
		return {"ok": 0, "tat": 1}
	try:
		u = tim_nhan_vien(sdt)
	except Exception:
		frappe.log_error(title="Gioi thieu: kiem so", message=frappe.get_traceback())
		return {"ok": 0}
	if not u:
		return {"ok": 0}
	return {"ok": 1, "ten": ten_goi(u.get("full_name"), u.get("first_name"))}


def _sdt_khach_hd(si, sdt_khach=None):
	ra = [sdt_khach, si.get("contact_mobile")]
	kh = si.get("customer")
	if kh:
		try:
			ra.append(frappe.db.get_value("Customer", kh, "mobile_no"))
		except Exception:
			pass
	return [x for x in ra if x]


def _ghi(si, gt):
	"""Đặt các ô lên doc; doc đã có trong cơ sở dữ liệu thì ghi luôn xuống.

	Không bật cờ miễn chặn trên doc: doc đã có thì giá trị nằm sẵn trong cơ sở
	dữ liệu nên lần lưu sau so khớp; bật cờ thì cờ dính trên doc đó và một lần
	đổi tay sau này lọt qua (bench v638 bắt được)."""
	for k, v in gt.items():
		si.set(k, v)
	ten = si.get("name")
	moi = True
	try:
		moi = bool(si.get("__islocal")) or si.is_new()
	except Exception:
		moi = not ten
	if ten and not moi:
		frappe.db.set_value(DT_HD, ten, gt, update_modified=False)
	elif moi:
		_tin_cho_doc_moi(si, gt)


# Codex PR #541: tờ MỚI không tin các ô giới thiệu gửi lên từ bên ngoài (API
# tạo Sales Invoice gửi kèm người tự chọn và % 100 thì ghi sổ ra hoa hồng
# 100%). Giá trị máy chủ đặt cho doc chưa lưu được ghi vào sổ riêng của lượt
# gọi (frappe.flags, client không với tới được), giữ chính đối tượng doc để
# không nhầm sang doc khác trùng id.
_SO_TIN = "vgb_gioi_thieu_tin"


def _tin_cho_doc_moi(doc, gt):
	so = frappe.flags.get(_SO_TIN)
	if not isinstance(so, dict):
		so = {}
		frappe.flags[_SO_TIN] = so
	cu = so.get(id(doc))
	gop = dict(cu[1]) if cu and cu[0] is doc else {}
	gop.update(gt)
	so[id(doc)] = (doc, gop)


def _lay_tin(doc):
	so = frappe.flags.get(_SO_TIN)
	if not isinstance(so, dict):
		return None
	cu = so.pop(id(doc), None)
	return cu[1] if cu and cu[0] is doc else None


def don_o_moi(tin, amended=None, la_tra=False):
	"""Các ô giới thiệu của tờ MỚI, chỉ từ nguồn máy chủ. THUẦN.

	tin: giá trị chính máy chủ vừa gắn cho doc này (gan_cho_hoa_don);
	amended: ô của tờ gốc đã huỷ khi tờ này là bản sửa lại. Mọi ô khác
	(kể cả số hoa hồng, ai đổi, lúc nào) về rỗng, không lấy từ dữ liệu gửi lên."""
	ra = {o: None for o in O_HD + (O_HH, O_GHI_CHU, O_DOI_BOI, O_DOI_LUC)}
	if la_tra:
		return ra
	if tin:
		for o in O_HD:
			if o in tin:
				ra[o] = tin[o]
	elif amended:
		for o in O_HD:
			ra[o] = amended.get(o) or None
	return ra


def gan_cho_hoa_don(si, sdt, loai="tai_ban", sdt_khach=None):
	"""Gắn người giới thiệu cho một hoá đơn (doc chưa lưu hoặc đã lưu, hoặc tên).

	Gọi từ đơn gọi món tại bàn (bọc try ở bên gọi, ở đây cũng tự bọc). % chốt
	ngay lúc gọi. Đơn đã có người giới thiệu thì không đè: mỗi đơn một người,
	đổi người là việc của quản lý (`doi_nguoi`). Trả dict, không bao giờ ném.
	"""
	try:
		if isinstance(si, str):
			si = frappe.get_doc(DT_HD, si)
		if not bat():
			return {"ok": 0, "ly_do": "tat"}
		if si.get("docstatus") and int(si.get("docstatus")) != 0:
			return {"ok": 0, "ly_do": "da_ghi_so"}
		if (si.get(O_NGUOI) or "").strip():
			return {"ok": 0, "ly_do": "da_co", "nguoi": si.get(O_NGUOI)}
		loai = loai if loai in LOAI else "tai_ban"
		u = tim_nhan_vien(sdt)
		if not u:
			return {"ok": 0, "ly_do": "khong_thay"}
		if tu_gioi_thieu(u.get("mobile_no"), _sdt_khach_hd(si, sdt_khach)):
			return {"ok": 0, "ly_do": "tu_gioi_thieu"}
		_ghi(si, {O_NGUOI: u["name"], O_LOAI: loai, O_PT: pt_cho(loai)})
		return {"ok": 1, "nguoi": u["name"], "ten": ten_goi(u.get("full_name"), u.get("first_name"))}
	except Exception:
		frappe.log_error(title="Gioi thieu: gan cho hoa don", message=frappe.get_traceback())
		return {"ok": 0, "ly_do": "loi"}


def gan_cho_don_web(d):
	"""Gọi trong don_web.tao_ban_ghi TRƯỚC insert: đọc số khách gõ trong ảnh chụp,
	gắn người giới thiệu và % chốt lúc đặt lên bản ghi. Không bao giờ ném."""
	try:
		if not bat():
			return
		snap = json.loads(d.get("snapshot") or "{}")
		sdt = snap.get("gioi_thieu_sdt") or ""
		if not chu_so(sdt):
			return
		u = tim_nhan_vien(sdt)
		if not u:
			return
		nguoi_dat = (snap.get("nguoi_dat") or {}).get("dien_thoai")
		if tu_gioi_thieu(u.get("mobile_no"), [d.get("dien_thoai"), nguoi_dat]):
			return
		d.set(O_DW_NGUOI, u["name"])
		d.set(O_DW_PT, pt_cho("web"))
	except Exception:
		frappe.log_error(title="Gioi thieu: gan cho don web", message=frappe.get_traceback())


def _don_web_cua(si):
	ma = [str(x).strip() for x in (si.get("custom_pancake_display_id"), si.get("custom_pancake_id")) if str(x or "").strip()]
	if not ma:
		return None
	ten = (frappe.db.get_value(DT_DW, {"pancake_display_id": ["in", ma]}, "name")
		or frappe.db.get_value(DT_DW, {"pancake_id": ["in", ma]}, "name"))
	if not ten:
		return None
	return frappe.db.get_value(DT_DW, ten, ["name", O_DW_NGUOI, O_DW_PT], as_dict=True)


def _chep_tu_don_web(si):
	"""Hoá đơn của đơn web chưa có người giới thiệu: chép từ bản ghi Don Web."""
	if si.get(O_NGUOI) or si.get("is_return"):
		return False
	dw = _don_web_cua(si)
	if not dw or not dw.get(O_DW_NGUOI):
		return False
	si.set(O_NGUOI, dw.get(O_DW_NGUOI))
	si.set(O_LOAI, "web")
	si.set(O_PT, chuan_pt(dw.get(O_DW_PT), 0))
	return True


def truoc_khi_luu(doc, method=None):
	"""Hook before_validate Sales Invoice.

	Tờ MỚI: không tin ô giới thiệu gửi lên (Codex PR #541). Chỉ nhận giá trị
	máy chủ vừa gắn (gan_cho_hoa_don), tờ sửa lại mang người của tờ gốc ĐÃ HUỶ,
	tờ của đơn web lấy từ bản ghi Don Web; tờ trả hàng để trống.
	Tờ ĐÃ CÓ: thu ngân (hay bất kỳ đường lưu nào không qua cửa của tệp này)
	đổi ô người giới thiệu thì máy trả lại giá trị cũ, không ném lỗi để không
	chặn việc bán.
	"""
	try:
		if doc.is_new():
			tin = _lay_tin(doc)
			goc = None
			if not tin and doc.get("amended_from"):
				goc = frappe.db.get_value(DT_HD, doc.amended_from, list(O_HD) + ["docstatus"], as_dict=True) or {}
				if int(goc.get("docstatus") or 0) != 2:
					goc = None
			for o, v in don_o_moi(tin, goc, bool(doc.get("is_return"))).items():
				doc.set(o, v)
			if not tin and not goc and not doc.get("is_return") and not doc.get("amended_from"):
				_chep_tu_don_web(doc)
			return
		if doc.flags.get("vgb_gioi_thieu_may"):
			return
		cu = doc.get_doc_before_save()
		if not cu:
			return
		for o in O_HD + (O_HH, O_DOI_BOI, O_DOI_LUC):
			if (cu.get(o) or None) != (doc.get(o) or None):
				doc.set(o, cu.get(o))
	except Exception:
		frappe.log_error(title="Gioi thieu: truoc khi luu hoa don", message=frappe.get_traceback())


def _da_hoan(ten):
	return bool(frappe.db.exists(DT_HD, {"is_return": 1, "return_against": ten, "docstatus": 1}))


def tinh_cho_hoa_don(si):
	"""Tính và ghi số hoa hồng của một hoá đơn ĐÃ GHI SỔ. Trả số đã ghi."""
	if not si.get(O_NGUOI):
		# Quản lý vừa gỡ người giới thiệu: số cũ phải về 0, không được treo lại.
		if flt(si.get(O_HH)):
			si.db_set({O_HH: 0, O_GHI_CHU: "Đã gỡ người giới thiệu."}, update_modified=False)
		return 0
	ghi_chu = ""
	so = 0
	if int(si.get("docstatus") or 0) != 1 or cint(si.get("vgb_huy")):
		ghi_chu = "Hoá đơn không còn hiệu lực."
	elif _da_hoan(si.name):
		ghi_chu = "Đơn đã hoàn tiền, hoa hồng về 0."
	else:
		sdt_nv = frappe.db.get_value("User", si.get(O_NGUOI), "mobile_no")
		if tu_gioi_thieu(sdt_nv, _sdt_khach_hd(si)):
			ghi_chu = "Khách đặt bằng chính số của người giới thiệu, không tính."
		else:
			dong = [{"item_code": d.get("item_code"), "amount": d.get("amount")} for d in (si.get("items") or [])]
			so = hoa_hong(tien_tinh(dong, si.get("discount_amount")), si.get(O_PT))
	si.db_set({O_HH: so, O_GHI_CHU: ghi_chu}, update_modified=False)
	return so


def khi_ghi_so(doc, method=None):
	"""Hook on_submit Sales Invoice. Tờ trả hàng: hoa hồng của tờ gốc về 0."""
	try:
		if doc.get("is_return"):
			goc = doc.get("return_against")
			if goc and frappe.db.get_value(DT_HD, goc, O_NGUOI):
				g = frappe.get_doc(DT_HD, goc)
				tinh_cho_hoa_don(g)
			return
		if not doc.get(O_NGUOI) and _chep_tu_don_web(doc):
			doc.db_set({o: doc.get(o) for o in O_HD}, update_modified=False)
		if doc.get(O_NGUOI):
			tinh_cho_hoa_don(doc)
	except Exception:
		frappe.log_error(title="Gioi thieu: tinh hoa hong khi ghi so", message=frappe.get_traceback())


def khi_huy(doc, method=None):
	"""Hook on_cancel Sales Invoice: huỷ thì về 0; huỷ tờ trả hàng thì tính lại tờ gốc."""
	try:
		if doc.get("is_return"):
			goc = doc.get("return_against")
			if goc and frappe.db.get_value(DT_HD, goc, O_NGUOI):
				tinh_cho_hoa_don(frappe.get_doc(DT_HD, goc))
			return
		if doc.get(O_NGUOI):
			doc.db_set({O_HH: 0, O_GHI_CHU: "Hoá đơn đã huỷ, hoa hồng về 0."}, update_modified=False)
	except Exception:
		frappe.log_error(title="Gioi thieu: huy hoa hong", message=frappe.get_traceback())


# --------------------------------------------------------- màn hình app

def _vai():
	return set(frappe.get_roles())


def _kiem_xem():
	if not (_vai() & VAI_XEM):
		frappe.throw("Bảng hoa hồng toàn tiệm chỉ mở cho quản lý, kế toán và ban giám đốc.")


def _dong_thang(ky, nguoi=None):
	"""Mọi dòng hoa hồng giới thiệu của một tháng (của một người nếu truyền)."""
	ky, tu, den = ky_thang(ky, getdate(nowdate()))
	loc = {"posting_date": ["between", [str(tu), str(den)]], "is_return": 0}
	loc[O_NGUOI] = nguoi if nguoi else ["is", "set"]
	hd = frappe.get_all(DT_HD, filters=loc, fields=[
		"name", "posting_date", "docstatus", "vgb_huy", "discount_amount",
		"custom_pancake_display_id", "custom_pancake_id",
		O_NGUOI, O_LOAI, O_PT, O_HH, O_GHI_CHU, O_DOI_BOI, O_DOI_LUC,
	], limit_page_length=0)
	ten = [r["name"] for r in hd]
	dong, hoan = {}, set()
	if ten:
		for d in frappe.get_all("Sales Invoice Item", filters={"parent": ["in", ten], "parenttype": DT_HD},
				fields=["parent", "item_code", "amount"], limit_page_length=0):
			dong.setdefault(d["parent"], []).append(d)
		for r in frappe.get_all(DT_HD, filters={"is_return": 1, "docstatus": 1, "return_against": ["in", ten]},
				fields=["return_against"], limit_page_length=0):
			hoan.add(r["return_against"])
	rows = [dong_hoa_don(r, dong.get(r["name"], []), r["name"] in hoan) for r in hd]

	# Đơn web chưa có hoá đơn: tiền đang chờ của nhân viên. Bỏ đơn đã có hoá
	# đơn (đã nằm ở trên) để một đơn không hiện hai lần.
	da = {str(r.get(k) or "").strip() for r in hd for k in ("custom_pancake_display_id", "custom_pancake_id")}
	da.discard("")
	loc_dw = {"trang_thai": ["!=", "Da ghi so"], O_DW_NGUOI: nguoi if nguoi else ["is", "set"]}
	from vagabond import thanh_toan_web_thuan as ttt

	for r in frappe.get_all(DT_DW, filters=loc_dw, fields=[
			"name", "trang_thai", "tien_banh", "trang_thai_phi", "snapshot", "ngay_nhan", "creation",
			"sales_invoice", "pancake_id", "pancake_display_id", O_DW_NGUOI, O_DW_PT], limit_page_length=0):
		if r.get("sales_invoice") or str(r.get("pancake_display_id") or "") in da or str(r.get("pancake_id") or "") in da:
			continue
		ngay = getdate(r.get("ngay_nhan") or r.get("creation"))
		if not (tu <= ngay <= den):
			continue
		try:
			snap = json.loads(r.get("snapshot") or "{}")
		except (TypeError, ValueError):
			snap = {}
		rows.append(dong_don_web(r, ttt.tien_ban_ghi(r, snap)["sau_giam"]))
	from vagabond import ten_nguoi

	for r in rows:
		r["ten_nguoi"] = ten_nguoi.ten(r["nguoi"]) if r["nguoi"] else ""
		r["nhan_tt"] = NHAN_TT.get(r["tt"], "")
		r["nhan_loai"] = LOAI.get(r["loai"], "")
	rows.sort(key=lambda r: (r["ngay"], r["ma"]), reverse=True)
	return ky, rows


@frappe.whitelist()
def cua_toi(ky=None):
	"""Nhân viên xem hoa hồng giới thiệu của chính mình theo tháng."""
	ky, rows = _dong_thang(ky, frappe.session.user)
	return {"ky": ky, "ds": rows, "tong": tong_hop(rows), "bat": 1 if bat() else 0,
		"xem_toan_tiem": 1 if (_vai() & VAI_XEM) else 0, "pt_web": pt_cho("web"), "pt_tai_ban": pt_cho("tai_ban")}


@frappe.whitelist()
def toan_tiem(ky=None):
	"""Quản lý xem bảng toàn tiệm theo tháng."""
	_kiem_xem()
	ky, rows = _dong_thang(ky)
	bang = theo_nhan_vien(rows)
	from vagabond import ten_nguoi

	for o in bang:
		o["ten_nguoi"] = ten_nguoi.ten(o["nguoi"])
	return {"ky": ky, "bang": bang, "ds": rows, "tong": tong_hop(rows),
		"doi_duoc": 1 if (_vai() & VAI_DOI) else 0, "bat": 1 if bat() else 0}


@frappe.whitelist()
def nhan_vien():
	"""Danh sách nhân viên để quản lý chọn khi đổi người giới thiệu.

	Chỉ mở cho người đổi được. Hiện tên và bốn số cuối để phân biệt hai
	người trùng tên, không hiện cả số.
	"""
	if not (_vai() & VAI_DOI):
		frappe.throw("Chỉ quản lý mới đổi được người giới thiệu.")
	ra = []
	for u in _ds_nhan_vien():
		if not la_nhan_vien(u):
			continue
		so = chuan_sdt(u.get("mobile_no"))
		ra.append({"ma": u["name"], "ten": u.get("full_name") or u["name"], "duoi": so[-4:] if so else ""})
	return {"ds": sorted(ra, key=lambda x: x["ten"])}


def _vet(dt, ten, chu):
	try:
		frappe.get_doc({"doctype": "Comment", "comment_type": "Info", "reference_doctype": dt,
			"reference_name": ten, "content": chu}).insert(ignore_permissions=True)
	except Exception:
		pass


@frappe.whitelist(methods=["POST"])
def doi_nguoi(ma=None, nguoi=None, ly_do=None):
	"""Quản lý đổi (hoặc gỡ) người giới thiệu của một đơn. Ghi ai đổi, lúc nào.

	Hoá đơn đã ghi sổ thì tính lại hoa hồng ngay theo người mới. Phiếu KPI
	tháng đã chốt thì không đổi theo: sai sót kỳ cũ điều chỉnh ở kỳ mới.
	"""
	from vagabond import ten_nguoi

	if not (_vai() & VAI_DOI):
		frappe.throw("Chỉ quản lý cửa hàng, Sales quản lý hoặc giám đốc mới đổi được người giới thiệu.")
	ma = (ma or "").strip()
	nguoi = (nguoi or "").strip()
	ly_do = (ly_do or "").strip()[:300]
	if not ly_do:
		frappe.throw("Ghi lý do đổi người giới thiệu để người sau đọc lại hiểu vì sao.")
	if nguoi:
		u = frappe.db.get_value("User", nguoi, ["name", "enabled", "user_type", "mobile_no", "full_name"], as_dict=True)
		if not u or not la_nhan_vien(u):
			frappe.throw("Người được chọn không phải nhân viên đang làm việc.")
	toi, luc = frappe.session.user, now_datetime()
	if frappe.db.exists(DT_HD, ma):
		si = frappe.get_doc(DT_HD, ma)
		if si.get("is_return"):
			frappe.throw("Tờ trả hàng không có người giới thiệu. Mở hoá đơn gốc để đổi.")
		cu = si.get(O_NGUOI) or ""
		if nguoi and tu_gioi_thieu(u.get("mobile_no"), _sdt_khach_hd(si)):
			frappe.throw("Khách của đơn này đặt bằng chính số của %s, không tính là giới thiệu." % ten_nguoi.ten(nguoi))
		gt = {O_NGUOI: nguoi or None, O_DOI_BOI: toi, O_DOI_LUC: luc}
		if nguoi and not si.get(O_LOAI):
			loai = "web" if (si.get("custom_pancake_display_id") or si.get("custom_pancake_id")) else "tai_ban"
			gt[O_LOAI] = loai
			gt[O_PT] = pt_cho(loai)
		frappe.db.set_value(DT_HD, ma, gt, update_modified=False)
		si.reload()
		so = tinh_cho_hoa_don(si) if si.docstatus == 1 else None
		_vet(DT_HD, ma, "Người giới thiệu: %s (trước đó %s). Lý do: %s." % (
			ten_nguoi.ten(nguoi) if nguoi else "gỡ bỏ", ten_nguoi.ten(cu) if cu else "chưa có", ly_do))
		frappe.db.commit()
		return {"ok": 1, "ma": ma, "nguoi": nguoi, "ten": ten_nguoi.ten(nguoi) if nguoi else "", "hoa_hong": so}
	if not frappe.db.exists(DT_DW, ma):
		frappe.throw("Không tìm thấy đơn %s." % ma)
	dw = frappe.db.get_value(DT_DW, ma, ["name", "dien_thoai", "sales_invoice", O_DW_NGUOI, O_DW_PT], as_dict=True)
	if dw.get("sales_invoice"):
		frappe.throw("Đơn này đã có hoá đơn %s. Đổi người giới thiệu trên dòng hoá đơn." % dw.get("sales_invoice"))
	if nguoi and tu_gioi_thieu(u.get("mobile_no"), [dw.get("dien_thoai")]):
		frappe.throw("Khách của đơn này đặt bằng chính số của %s, không tính là giới thiệu." % ten_nguoi.ten(nguoi))
	gt = {O_DW_NGUOI: nguoi or None}
	if nguoi and not dw.get(O_DW_NGUOI):
		gt[O_DW_PT] = pt_cho("web")
	frappe.db.set_value(DT_DW, ma, gt, update_modified=False)
	cu = dw.get(O_DW_NGUOI) or ""
	_vet(DT_DW, ma, "Người giới thiệu: %s (trước đó %s), đổi bởi %s lúc %s. Lý do: %s." % (
		ten_nguoi.ten(nguoi) if nguoi else "gỡ bỏ", ten_nguoi.ten(cu) if cu else "chưa có",
		ten_nguoi.ten(toi), str(luc)[:16], ly_do))
	frappe.db.commit()
	return {"ok": 1, "ma": ma, "nguoi": nguoi, "ten": ten_nguoi.ten(nguoi) if nguoi else ""}


def _phieu_thang(ky):
	ra = {}
	for r in frappe.get_all(DT_KPI, filters={"ky": ky}, fields=["name", "nguoi", "dong_bang", "trang_thai", O_KPI_HH],
			limit_page_length=0, ignore_permissions=True):
		ra[r["nguoi"]] = {"name": r["name"], "hh": r.get(O_KPI_HH), "dong_bang": r.get("dong_bang"),
			"trang_thai": r.get("trang_thai")}
	return ra


@frappe.whitelist(methods=["POST"])
def dua_vao_kpi(ky=None):
	"""Ghi tổng hoa hồng giới thiệu đã ghi sổ của tháng vào phiếu KPI của từng người.

	Ghi ĐÈ chứ không cộng, nên bấm lại bao nhiêu lần cũng một số. Người chưa
	có phiếu tháng đó thì máy lập một phiếu chỉ có khoản giới thiệu, bước đầu
	chờ quản lý xác nhận như mọi phiếu KPI. Phiếu đã chốt thì để nguyên.
	"""
	from vagabond import kpi, ten_nguoi

	kpi._kiem_quyen()
	ky, rows = _dong_thang(ky)
	viec = ke_hoach_kpi(rows, _phieu_thang(ky))
	luc = now_datetime()
	ra = {"tao": [], "cap_nhat": [], "giu": [], "da_chot": []}
	for v in viec:
		if v["viec"] == "bo_qua":
			continue
		if v["viec"] in ("giu", "da_chot"):
			ra[v["viec"]].append({"nguoi": v["nguoi"], "ten": ten_nguoi.ten(v["nguoi"]), "so": v["so"], "cu": v.get("cu")})
			continue
		if v["viec"] == "tao":
			_, tu, den = kpi.khoang_ky(ky)
			doc = frappe.new_doc(DT_KPI)
			doc.update({"ky": ky, "tu_ngay": tu, "den_ngay": den, "nguoi": v["nguoi"],
				"ten_nguoi": ten_nguoi.ten(v["nguoi"]), "bo": BO_KPI, "trang_thai": kpi.TT_QUAN_LY,
				"xep_loai": "Chỉ giới thiệu", "he_so": 1, "con_thieu": 0, "diem_tong": 0,
				"doanh_thu": 0, "hoa_hong": 0, "hoa_hong_tho": 0})
			doc.set(O_KPI_HH, v["so"])
			doc.set(O_KPI_DON, json.dumps(v["don"], ensure_ascii=False))
			doc.set(O_KPI_LUC, luc)
			doc.flags.ignore_permissions = True
			doc.insert(ignore_permissions=True)
			ra["tao"].append({"nguoi": v["nguoi"], "ten": doc.ten_nguoi, "so": v["so"], "phieu": doc.name})
			continue
		# Codex PR #541 vòng 6: giám đốc có thể vừa duyệt (đóng băng) phiếu sau lúc
		# đọc danh sách. Khoá hàng phiếu, đọc lại trạng thái hiện tại rồi mới ghi.
		hien = frappe.db.get_value(DT_KPI, v["phieu"], ["dong_bang", "trang_thai", O_KPI_HH], as_dict=True, for_update=True)
		if not hien or phieu_da_chot(hien):
			ra["da_chot"].append({"nguoi": v["nguoi"], "ten": ten_nguoi.ten(v["nguoi"]), "so": v["so"],
				"cu": int(round(_so((hien or {}).get(O_KPI_HH)))), "phieu": v["phieu"]})
			v["viec"] = "da_chot"
			continue
		frappe.db.set_value(DT_KPI, v["phieu"], {O_KPI_HH: v["so"], O_KPI_DON: json.dumps(v["don"], ensure_ascii=False),
			O_KPI_LUC: luc})
		ra["cap_nhat"].append({"nguoi": v["nguoi"], "ten": ten_nguoi.ten(v["nguoi"]), "so": v["so"], "cu": v.get("cu"),
			"phieu": v["phieu"]})
	frappe.db.commit()
	ra["ky"] = ky
	ra["tong"] = sum(v["so"] for v in viec if v["viec"] in ("tao", "cap_nhat", "giu"))
	return ra


def hh_theo_phieu(ten_phieu):
	"""{phiếu: hoa hồng giới thiệu} cho màn danh sách KPI. Thiếu cột thì rỗng."""
	if not ten_phieu:
		return {}
	try:
		return {r["name"]: flt(r.get(O_KPI_HH)) for r in frappe.get_all(
			DT_KPI, filters={"name": ["in", list(ten_phieu)]}, fields=["name", O_KPI_HH],
			limit_page_length=0, ignore_permissions=True)}
	except Exception:
		return {}


def xuat_ds(ky=None, **khac):
	"""Adapter Xuất Excel (khung/cong_cu_ds.MAN_XUAT): mỗi đơn một dòng của tháng."""
	_kiem_xem()
	ky, rows = _dong_thang(ky)
	cot = [{"k": "ten_nguoi", "nhan": "Nhân viên"}, {"k": "hien", "nhan": "Mã đơn"},
		{"k": "ngay", "nhan": "Ngày", "kieu": "ngay"}, {"k": "nhan_loai", "nhan": "Loại đơn"},
		{"k": "tien_hang", "nhan": "Tiền hàng", "kieu": "tien"}, {"k": "pt", "nhan": "% hoa hồng", "kieu": "so"},
		{"k": "hoa_hong", "nhan": "Hoa hồng", "kieu": "tien"}, {"k": "nhan_tt", "nhan": "Trạng thái"},
		{"k": "ghi_chu", "nhan": "Ghi chú"}]
	return "Hoa hong gioi thieu " + ky, cot, rows
