# -*- coding: utf-8 -*-
"""Tai khoan nhan chuyen khoan, khai theo NGUON DON (anh Viet 12/08/2026).

Truoc day so tai khoan nhan tien nam cung trong ma nguon (ban_hang.QR_QUAY):
mot tai khoan ao MBBank duy nhat cho ca ba diem ban va moi nguon don. Ke
toan nhin sao ke ngan hang thi moi giao dich deu do ve mot cho, muon biet
tien nay cua quay nao thi phai doc noi dung chuyen khoan.

Anh Viet dang xin MB Bank cap them nhieu tai khoan ao. Moi nguon don mot
tai khoan rieng thi sao ke tu no da tach san, khong con phu thuoc vao viec
thu ngan co go dung noi dung hay khong.

Hai lop cung chay:

  1. Noi dung chuyen khoan mang ma diem ban (posNoiDungCk ben app).
  2. Tai khoan ao rieng theo nguon - man nay.

Nguon nao chua khai tai khoan rieng thi roi ve TAI KHOAN MAC DINH, tuc
dung y nguyen cai dang chay. Deploy khong lam doi hanh vi cua he thong.
"""

import json

import frappe
from frappe.utils import cint

from vagabond.lib import cfg

TRUONG = "vgb_tai_khoan_nhan"

# Muc dich dac biet, khong phai nguon don. Khai chung mot bang cho gon,
# nhung tach ra day de man Cai dat hien thanh mot khoi rieng va de cho
# nao goi cung biet ma ma tra.
#
# Phieu doi no la cho tien khach si THUC SU chay ve: don ghi Cong no thi
# luc ban khach chua tra dong nao nen khong co ma QR nao ca, tien chi ve
# khi minh gom hoa don thanh phieu de nghi thanh toan roi gui ho.
CN_PHIEU_NO = "@phieu_cong_no"

# Tien to khoa cho tai khoan khai theo DIEM BAN: "@diem:TCV".
#
# Tu 12/08/2026 hai quay dung chung nguon "Tại chỗ" va "Mang về" (anh Viet:
# ban chat la mot, da quan ly tu buoc diem ban roi), nen khoa theo ten nguon
# khong con tach duoc dong tien cua Tran Cao Van voi Nha Van Hoa Thanh Nien.
# Khoa theo diem ban thi tach duoc, va dung y anh Viet muon: moi diem mot
# tai khoan ao, sao ke tu no da chia san.
#
# Thu tu tra: tai khoan cua NGUON truoc (vi du "Khách sỉ" co tai khoan rieng
# du don do thuoc diem nao), roi den tai khoan cua DIEM, cuoi cung la mac
# dinh. Nguon cu the bao gio cung cu the hon diem.
CN_DIEM = "@diem:"
MUC_DICH = [
	{
		"k": CN_PHIEU_NO,
		"ten": "Phiếu đòi nợ khách sỉ",
		"mo": "Mã QR trên phiếu đề nghị thanh toán công nợ gửi cho khách sỉ.",
		"ic": "📒",
	},
]

QUYEN_SUA = {"System Manager", "Accounts Manager", "Sales Manager"}

# Tai khoan dang chay tu truoc: tai khoan ao MBBank ma Fabi dung (chup man
# hinh cau hinh Fabi 08/08). Vua la gia tri khoi tao, vua la luoi do khi
# cau hinh tren Settings trong hoac hong dinh dang.
MAC_DINH = {
	"bank": "MB",
	"stk": "VQRQ00033k5p6",
	"ten": "PATISSERIE VAGABOND COMPANY LIMITED",
}

# Ngan hang thanh vien Napas co the sinh VietQR. Ma "bank" gui cho
# img.vietqr.io la ma BIN 6 so - dung BIN chu khong dung ten viet tat, vi
# ten viet tat co ngan hang doi (VietinBank tung la ICB roi CTG), con BIN
# la so co quan quan ly cap, khong doi.
NGAN_HANG = [
	{"bin": "970422", "ten": "MB Bank", "ma": "MB"},
	{"bin": "970436", "ten": "Vietcombank", "ma": "VCB"},
	{"bin": "970415", "ten": "VietinBank", "ma": "ICB"},
	{"bin": "970418", "ten": "BIDV", "ma": "BIDV"},
	{"bin": "970405", "ten": "Agribank", "ma": "VBA"},
	{"bin": "970407", "ten": "Techcombank", "ma": "TCB"},
	{"bin": "970416", "ten": "ACB", "ma": "ACB"},
	{"bin": "970432", "ten": "VPBank", "ma": "VPB"},
	{"bin": "970423", "ten": "TPBank", "ma": "TPB"},
	{"bin": "970403", "ten": "Sacombank", "ma": "STB"},
	{"bin": "970437", "ten": "HDBank", "ma": "HDB"},
	{"bin": "970443", "ten": "SHB", "ma": "SHB"},
	{"bin": "970431", "ten": "Eximbank", "ma": "EIB"},
	{"bin": "970441", "ten": "VIB", "ma": "VIB"},
	{"bin": "970448", "ten": "OCB", "ma": "OCB"},
	{"bin": "970426", "ten": "MSB", "ma": "MSB"},
	{"bin": "970429", "ten": "SCB", "ma": "SCB"},
	{"bin": "970454", "ten": "VietCapital Bank", "ma": "VCCB"},
	{"bin": "970400", "ten": "SaigonBank", "ma": "SGICB"},
	{"bin": "970406", "ten": "DongA Bank", "ma": "DOB"},
	{"bin": "970409", "ten": "BacA Bank", "ma": "BAB"},
	{"bin": "970412", "ten": "PVcomBank", "ma": "PVCB"},
	{"bin": "970414", "ten": "Oceanbank", "ma": "OCEANBANK"},
	{"bin": "970419", "ten": "NCB", "ma": "NCB"},
	{"bin": "970424", "ten": "Shinhan Bank", "ma": "SHBVN"},
	{"bin": "970425", "ten": "ABBANK", "ma": "ABB"},
	{"bin": "970427", "ten": "VietABank", "ma": "VAB"},
	{"bin": "970428", "ten": "NamA Bank", "ma": "NAB"},
	{"bin": "970430", "ten": "PGBank", "ma": "PGB"},
	{"bin": "970433", "ten": "VietBank", "ma": "VIETBANK"},
	{"bin": "970438", "ten": "BaoViet Bank", "ma": "BVB"},
	{"bin": "970440", "ten": "SeABank", "ma": "SEAB"},
	{"bin": "970446", "ten": "Co-opBank", "ma": "COOPBANK"},
	{"bin": "970449", "ten": "LPBank", "ma": "LPB"},
	{"bin": "970452", "ten": "KienLongBank", "ma": "KLB"},
	{"bin": "970458", "ten": "United Overseas Bank", "ma": "UOB"},
	{"bin": "970442", "ten": "Hong Leong Bank", "ma": "HLBVN"},
	{"bin": "970457", "ten": "Woori Bank", "ma": "WVN"},
	{"bin": "546034", "ten": "CAKE by VPBank", "ma": "CAKE"},
	{"bin": "546035", "ten": "Ubank by VPBank", "ma": "UBANK"},
	{"bin": "963388", "ten": "Timo by BVBank", "ma": "TIMO"},
	{"bin": "971011", "ten": "Viettel Money", "ma": "VIETTELMONEY"},
	{"bin": "971005", "ten": "VNPT Money", "ma": "VNPTMONEY"},
]


def _ten_ngan_hang(ma):
	m = str(ma or "").strip()
	for nh in NGAN_HANG:
		if m in (nh["bin"], nh["ma"]):
			return nh["ten"]
	return m


def _chuan_tk(d):
	"""Mot tai khoan bat ky ve dung khuon."""
	return {
		"bank": str((d or {}).get("bank") or "").strip(),
		"stk": str((d or {}).get("stk") or "").strip(),
		"ten": str((d or {}).get("ten") or "").strip(),
	}


def _du(tk):
	"""Tai khoan co du de sinh QR khong."""
	return bool(tk.get("bank") and tk.get("stk"))


def cai():
	"""Toan bo cau hinh: tai khoan mac dinh va cac tai khoan theo nguon."""
	try:
		tho = json.loads((cfg().get(TRUONG) or "").strip() or "{}")
	except Exception:
		frappe.log_error(frappe.get_traceback(), "tai_khoan: cau hinh hong dinh dang")
		tho = {}
	if not isinstance(tho, dict):
		tho = {}
	md = _chuan_tk(tho.get("mac_dinh") or {})
	if not _du(md):
		md = dict(MAC_DINH)
	ra = []
	da_co = {}
	for d in tho.get("theo_nguon") or []:
		n = str((d or {}).get("nguon") or "").strip()
		if not n or n in da_co:
			continue
		tk = _chuan_tk(d)
		tk["nguon"] = n
		tk["dung"] = 1 if cint(d.get("dung") if d.get("dung") is not None else 1) else 0
		da_co[n] = 1
		ra.append(tk)
	return {"mac_dinh": md, "theo_nguon": ra}


def tk_cho(nguon=None, diem=None):
	"""Tai khoan nhan tien cua mot nguon don tai mot diem ban.

	Nguon chua khai rieng, khai thieu so tai khoan, hoac dang tat thi thu
	tiep tai khoan cua diem ban, roi moi roi ve tai khoan mac dinh - khong
	bao gio tra ve tai khoan rong, vi tra rong la man tinh tien khong sinh
	duoc QR ma thu ngan khong hieu vi sao.
	"""
	c = cai()
	n = str(nguon or "").strip()
	d = str(diem or "").strip().upper()
	rieng = {t["nguon"]: t for t in c["theo_nguon"] if t["dung"] and _du(t)}
	for khoa in ([n] if n else []) + ([CN_DIEM + d] if d else []):
		tk = rieng.get(khoa)
		if tk:
			return {
				"bank": tk["bank"],
				"stk": tk["stk"],
				"ten": tk["ten"] or c["mac_dinh"]["ten"],
				"nguon": n or khoa,
				"diem": d,
				"rieng": 1,
			}
	md = dict(c["mac_dinh"])
	md["nguon"] = n
	md["diem"] = d
	md["rieng"] = 0
	return md


def tk_phieu_no():
	"""Tai khoan nhan tien cua phieu de nghi thanh toan cong no."""
	return tk_cho(CN_PHIEU_NO)


def bang_theo_nguon(nguon=None):
	"""Bang tra tai khoan, gui cho app mot lan cung cau hinh.

	Hai kieu khoa nam chung mot bang:
	  "<nguồn>"             - tra khi app khong biet minh dang o diem nao
	  "<MÃ ĐIỂM>|<nguồn>"   - tra khi app biet, vi du man tinh tien quay
	App tra khoa co diem truoc. Co hai khoa la vi mot nguon dung chung cho
	nhieu diem thi cung mot ten nguon lai ra hai tai khoan khac nhau.
	"""
	from vagabond import diem_ban

	if nguon is None:
		from vagabond.ban_hang import _nguon_don

		nguon = _nguon_don()
	ra = {}
	for n in nguon:
		ten = n["v"]
		ra[ten] = tk_cho(ten)
		for ma in (n.get("diem_ds") or ([n["diem"]] if n.get("diem") else [])):
			ra["%s|%s" % (ma, ten)] = tk_cho(ten, ma)
	# Diem chua co nguon nao khai o day van phai tra duoc tai khoan, de man
	# nao chi biet minh o quay nao (chua chon nguon) van sinh duoc QR.
	for d in diem_ban.ds(chi_bat=True):
		ra["%s|" % d["ma"]] = tk_cho("", d["ma"])
	return ra


# ------------------------------------------------------------------ man app


@frappe.whitelist()
def danh_sach():
	from vagabond.ban_hang import _kiem_quyen, _nguon_don

	from vagabond import diem_ban

	_kiem_quyen()
	c = cai()
	da_co = {t["nguon"]: 1 for t in c["theo_nguon"]}
	nguon = []
	for m in MUC_DICH:
		nguon.append({
			"v": m["k"], "lg": "", "ic": m.get("ic") or "🏦",
			"nhan": m["ten"], "mo": m.get("mo") or "",
			"da_khai": da_co.get(m["k"], 0),
		})
	# Diem ban len truoc nguon don: day moi la cach anh Viet chia dong tien
	# (moi diem mot tai khoan ao MB), con tai khoan theo nguon chi de xu ly
	# vai truong hop le nhu khach si.
	for d in diem_ban.ds(chi_bat=True):
		k = CN_DIEM + d["ma"]
		nguon.append({
			"v": k, "lg": "", "ic": "🏪",
			"nhan": "Điểm bán: " + d["ten"],
			"mo": "Áp cho mọi nguồn đơn của điểm này, trừ nguồn đã khai riêng.",
			"da_khai": da_co.get(k, 0),
		})
	for n in _nguon_don():
		ds_diem = n.get("diem_ds") or []
		nguon.append({
			"v": n["v"], "lg": n.get("lg") or "", "ic": n.get("ic") or "",
			"nhan": n["v"],
			"mo": (
				"Dùng chung cho %s - khai ở đây là cả hai điểm về một tài khoản."
				% ", ".join(ds_diem)
			) if len(ds_diem) > 1 else "",
			"da_khai": da_co.get(n["v"], 0),
		})
	# CANH BAO DIEM CHUA KHAI TAI KHOAN RIENG.
	#
	# Anh Viet 01/09/2026: *"truoc do anh da cai roi nhung sao gio vao phan
	# cai dat thay bien mat"*. Dung vay: `theo_nguon` rong tron, ca ba diem
	# ban do chung vao mot tai khoan ao, nen sao ke ngan hang khong con tach
	# duoc tien cua Tran Cao Van voi tien cua Nha Van Hoa Thanh Nien.
	#
	# Cai hong that su la no bien mat MA KHONG AI HAY. Nen tu nay man Cai dat
	# noi thang ra diem nao dang thieu, ngay tren dau man.
	thieu_diem = [
		{"ma": d["ma"], "ten": d["ten"]}
		for d in diem_ban.ds(chi_bat=True)
		if not da_co.get(CN_DIEM + d["ma"])
	]
	return {
		"mac_dinh": c["mac_dinh"],
		"theo_nguon": c["theo_nguon"],
		"thieu_diem": thieu_diem,
		"nguon": nguon,
		"muc_dich": MUC_DICH,
		"ngan_hang": NGAN_HANG,
		"sua_duoc": 1 if QUYEN_SUA & set(frappe.get_roles()) else 0,
	}


def _kiem(md, ds):
	if not _du(md):
		frappe.throw(
			"Tài khoản mặc định phải có cả ngân hàng và số tài khoản. Bỏ trống "
			"là mọi màn tính tiền ngừng sinh mã QR chuyển khoản."
		)
	if not md["ten"]:
		frappe.throw(
			"Tài khoản mặc định phải ghi tên chủ tài khoản. Khách quét mã mà "
			"không thấy tên người nhận thì không ai dám chuyển."
		)
	hop_le = {nh["bin"] for nh in NGAN_HANG} | {nh["ma"] for nh in NGAN_HANG}
	da_co = {}
	for tk in ds:
		n = tk["nguon"]
		if n in da_co:
			frappe.throw("Nguồn \"%s\" bị khai hai lần." % n)
		da_co[n] = 1
		if tk["bank"] and tk["bank"] not in hop_le:
			frappe.throw(
				"Ngân hàng của nguồn \"%s\" không nằm trong danh sách Napas. "
				"Chọn lại trong danh sách thay vì gõ tay." % n
			)
		# Khai nua voi con te hon khong khai: man Cai dat nhin nhu da tach
		# tai khoan cho nguon do, ma tien thuc te van do ve tai khoan chung.
		if tk["dung"] and not _du(tk):
			frappe.throw(
				"Nguồn \"%s\" đang bật mà chưa điền đủ ngân hàng và số tài "
				"khoản. Điền nốt, hoặc tắt dòng đó đi để nguồn này dùng tài "
				"khoản mặc định." % n
			)
	if md["bank"] and md["bank"] not in hop_le:
		frappe.throw("Ngân hàng của tài khoản mặc định không nằm trong danh sách Napas.")


@frappe.whitelist()
def luu(mac_dinh=None, theo_nguon=None):
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	if not QUYEN_SUA & set(frappe.get_roles()):
		frappe.throw("Chỉ quản lý hoặc kế toán mới sửa được tài khoản nhận tiền.")
	if isinstance(mac_dinh, str):
		mac_dinh = frappe.parse_json(mac_dinh or "{}")
	if isinstance(theo_nguon, str):
		theo_nguon = frappe.parse_json(theo_nguon or "[]")
	md = _chuan_tk(mac_dinh or {})
	ds = []
	for d in theo_nguon or []:
		n = str((d or {}).get("nguon") or "").strip()
		if not n:
			continue
		tk = _chuan_tk(d)
		tk["nguon"] = n
		tk["dung"] = 1 if cint(d.get("dung") if d.get("dung") is not None else 1) else 0
		ds.append(tk)
	_kiem(md, ds)
	frappe.db.set_single_value(
		"Vagabond Settings",
		TRUONG,
		json.dumps({"mac_dinh": md, "theo_nguon": ds}, ensure_ascii=False, indent=1),
	)
	frappe.db.commit()
	_ghi_vet(
		"Sửa tài khoản nhận chuyển khoản: mặc định %s %s%s"
		% (
			_ten_ngan_hang(md["bank"]),
			md["stk"],
			"".join(
				"; %s %s %s%s" % (t["nguon"], _ten_ngan_hang(t["bank"]), t["stk"], "" if t["dung"] else " (tắt)")
				for t in ds
			),
		)
	)
	return danh_sach()


def _ghi_vet(viec):
	"""Doi tai khoan nhan tien la doi noi tien chay vao. Phai co dau vet."""
	try:
		frappe.get_doc(
			{
				"doctype": "Comment",
				"comment_type": "Info",
				"reference_doctype": "Vagabond Settings",
				"reference_name": "Vagabond Settings",
				"content": "%s - %s" % (viec, frappe.session.user),
			}
		).insert(ignore_permissions=True)
	except Exception:
		pass
