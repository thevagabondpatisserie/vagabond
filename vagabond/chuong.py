# -*- coding: utf-8 -*-
"""v619: chuông thông báo trong app (anh Việt chọn 28/10/2026: "một chuông gộp cả hai").

Chuông ở góc trên trang chủ. Số đỏ = việc đang chờ mình (màn Việc cần làm, đã có
từ v243) + tin chưa đọc. Bấm vào mở màn có hai thẻ: Thông báo và Việc cần làm.

Thông báo là CHÍNH các tin Zalo đã gửi (sổ "Vagabond Tin Kenh"), để nhân viên xem
lại trong app mà không phải lục Zalo, bấm tin là mở đúng màn. Không gửi gì mới.

Ai thấy tin nào
---------------
Máy chưa biết ai ở nhóm Zalo nào, nên chia theo BỘ PHẬN của người dùng (ô Phòng ban
trên tài khoản) khớp với bộ phận của từng tin trong kenh_zalo.TIN. Giám đốc và
quản trị thấy mọi tin. Người chưa gắn phòng ban thì không thấy tin nào (màn nói rõ).
Lọc ở MÁY CHỦ, máy khách chỉ vẽ.

Một tin gửi vào hai nhóm thì sổ có hai dòng cùng nội dung: gộp lại thành một.
"Đã đọc" là mốc thời gian lưu riêng từng người (giá trị mặc định của người dùng),
mở thẻ Thông báo là cập nhật mốc.

Codex 4404477923: mốc là MỘT thời điểm, nên tin chưa đọc phải luôn được trả về HẾT (không
cắt ở TOI_DA), mốc chỉ đẩy tới tin mới nhất đã hiện chứ không tới "bây giờ". Tin đã đọc thì
mỗi lượt TOI_DA tin, có nút xem tin cũ hơn.
"""

import re

SO_NGAY = 14
TOI_DA = 60
# Codex 4404477900: chỉ tin ĐÃ GỬI THẬT (gửi riêng hay gửi gộp giờ im). Tin chờ, đang gửi,
# hoãn, lỗi, chưa rõ, và tin "Bỏ qua (đã xử lý)" vì việc đã xong trước giờ gửi: không hiện.
DA_GUI = ("Đã gửi", "Đã gửi gộp")
KHOA_DA_XEM = "vgb_chuong_xem"
TAT_CA = "*"

# Phòng ban (tên trên site, đã bỏ đuôi " - TV") -> bộ phận của tin (kenh_zalo.BO_PHAN).
BO_PHAN_TIN = {
	"Bếp Baker": ("Bếp",),
	"Bếp Pastry": ("Bếp",),
	"Sonneto Lab": ("Bếp",),
	"Kế toán": ("Hoá đơn, kế toán",),
	"Thu mua": ("Thu mua", "Kho"),
	"Kho": ("Kho", "Thu mua"),
	"Sales": ("Bán hàng, cửa hàng",),
	"Thu ngân": ("Bán hàng, cửa hàng",),
	"Pha chế": ("Bán hàng, cửa hàng",),
	"Marketing": ("Bán hàng, cửa hàng",),
	"Vận hành": ("Bán hàng, cửa hàng", "Kho"),
	"Ban Giám đốc": TAT_CA,
	"Ban giám đốc": TAT_CA,
}
VAI_XEM_HET = ("System Manager", "AP Giám đốc")
RE_MO = re.compile(r"^Mở:\s*(\S+)\s*$", re.M)


# ------------------------------------------------------------------ THUẦN

def ten_phong_ban(pb):
	"""THUẦN: "Bếp Baker - TV" -> "Bếp Baker"."""
	t = str(pb or "").strip()
	return t[:-5].strip() if t.endswith(" - TV") else t


def bo_phan_cua(phong_ban, vai=()):
	"""THUẦN: tập bộ phận tin người này được xem, hoặc TAT_CA."""
	if set(vai or ()) & set(VAI_XEM_HET):
		return TAT_CA
	ra = BO_PHAN_TIN.get(ten_phong_ban(phong_ban))
	if ra == TAT_CA:
		return TAT_CA
	return tuple(ra or ())


def ma_tin_duoc_xem(bo_phan, danh_muc):
	"""THUẦN: các mã tin trong danh_muc (kenh_zalo.TIN) thuộc các bộ phận được xem."""
	if bo_phan == TAT_CA:
		return sorted(danh_muc or {})
	return sorted(m for m, v in (danh_muc or {}).items() if v and v[0] in (bo_phan or ()))


def tach_tin(noi_dung):
	"""THUẦN: (tiêu đề, thân, đường mở) từ một tin đã soạn. Dòng "Mở: <url>" tách riêng."""
	t = str(noi_dung or "").strip()
	m = RE_MO.search(t)
	link = m.group(1) if m else ""
	if m:
		t = (t[:m.start()] + t[m.end():]).strip()
	dong = t.split("\n")
	return dong[0].strip(), "\n".join(dong[1:]).strip(), link


def gop_tin(dong, da_xem=None):
	"""THUẦN: gộp các dòng sổ tin cùng mã và cùng nội dung (một tin gửi nhiều nhóm).

	dong: [{"name","ma_tin","noi_dung","luc"}] mới nhất trước. Trả danh sách tin
	{"ten","ma_tin","tieu_de","than","link","luc","moi"}; moi = 1 khi luc > da_xem."""
	thay, ra = set(), []
	for d in dong or []:
		k = (d.get("ma_tin") or "", str(d.get("noi_dung") or "").strip())
		if not k[1] or k in thay:
			continue
		thay.add(k)
		tieu_de, than, link = tach_tin(k[1])
		luc = str(d.get("luc") or "")
		ra.append({"ten": d.get("name"), "ma_tin": k[0], "tieu_de": tieu_de, "than": than, "link": link,
			"luc": luc, "moi": 1 if (not da_xem or luc > str(da_xem)) else 0})
	return ra


# ------------------------------------------------------------- phần chạm Frappe

import frappe
from frappe.utils import add_days, now_datetime


def _phong_ban(user):
	from vagabond import nguoi_dung

	return nguoi_dung._bo_phan_cua(user)


def _ma_tin_cua_toi():
	from vagabond import kenh_zalo

	bp = bo_phan_cua(_phong_ban(frappe.session.user), frappe.get_roles())
	return bp, ma_tin_duoc_xem(bp, kenh_zalo.TIN)


def _doc_tin(ma, gioi_han=0, sau=None, truoc=None, den=None):
	"""Dòng sổ tin đã gửi thật, mới gửi nhất trước. Mọi mốc so theo LÚC GỬI (luc_gui), không
	theo lúc tạo dòng (Codex 4407978621: tin tạo 07:00 hoãn giờ im, gửi 08:30, mà mốc đã đọc là
	08:00 thì so theo lúc tạo sẽ thành đã đọc dù chưa từng hiện). Cả hai đường gửi đều ghi luc_gui.
	sau: gửi SAU mốc (chưa đọc); den: gửi tới mốc (đã đọc); truoc: gửi trước mốc (trang cũ hơn).
	gioi_han 0 là không cắt."""
	if not ma:
		return []
	moc = str(add_days(now_datetime(), -SO_NGAY))
	dk = [["ma_tin", "in", ma], ["trang_thai", "in", list(DA_GUI)], ["luc_gui", ">=", moc]]
	if sau:
		dk.append(["luc_gui", ">", str(sau)])
	if truoc:
		dk.append(["luc_gui", "<", str(truoc)])
	if den:
		dk.append(["luc_gui", "<=", str(den)])
	return frappe.get_all("Vagabond Tin Kenh", filters=dk,
		fields=["name", "ma_tin", "noi_dung", "luc_gui as luc"], order_by="luc_gui desc",
		limit_page_length=gioi_han)


def _da_xem():
	return frappe.defaults.get_user_default(KHOA_DA_XEM, frappe.session.user) or ""


@frappe.whitelist()
def dem():
	"""CHỈ ĐỌC: số đỏ của chuông = việc đang chờ + tin chưa đọc. Lỗi phần nào thì phần đó tính 0."""
	viec = 0
	try:
		from vagabond import viec_can_lam

		viec = int((viec_can_lam.dem() or {}).get("tong") or 0)
	except Exception:
		viec = 0
	tin = 0
	try:
		_, ma = _ma_tin_cua_toi()
		moc = _da_xem()
		tin = sum(1 for x in gop_tin(_doc_tin(ma, sau=moc or None), moc) if x["moi"])
	except Exception:
		tin = 0
	return {"viec": viec, "tin": tin, "tong": viec + tin}


def chia_trang(moi, cu, toi_da=TOI_DA):
	"""THUẦN: một trang của màn. moi: mọi tin chưa đọc (đã gộp), hiện HẾT; cu: tin đã đọc
	(đã gộp, mới nhất trước), hiện tới toi_da. Trả (ds, còn tin cũ hơn không)."""
	thay = {(x["ma_tin"], x["tieu_de"], x["than"], x["link"]) for x in moi}
	cu = [x for x in cu if (x["ma_tin"], x["tieu_de"], x["than"], x["link"]) not in thay]
	return list(moi) + cu[:toi_da], len(cu) > toi_da


@frappe.whitelist()
def thong_bao(truoc=None):
	"""CHỈ ĐỌC: tin Zalo đã gửi 14 ngày gần nhất của bộ phận mình, mới nhất trước, đã gộp.

	Lượt đầu (truoc trống): MỌI tin chưa đọc, rồi tới TOI_DA tin đã đọc. Lượt sau (truoc =
	thời điểm tin cuối đang hiện): TOI_DA tin cũ hơn nữa. moc_moi là thời điểm tin mới
	nhất đã hiện, để da_xem chỉ đánh dấu tới đó."""
	bp, ma = _ma_tin_cua_toi()
	moc = _da_xem()
	gioi_han = TOI_DA * 4 + 1
	if truoc:
		dong = _doc_tin(ma, gioi_han, truoc=truoc)
		ds, con = chia_trang([], gop_tin(dong, moc))
	elif moc:
		dong = _doc_tin(ma, gioi_han, den=moc)
		ds, con = chia_trang(gop_tin(_doc_tin(ma, sau=moc), moc), gop_tin(dong, moc))
	else:
		# Chưa đọc lần nào: mọi tin là chưa đọc, hiện hết.
		dong = []
		ds, con = chia_trang(gop_tin(_doc_tin(ma), moc), [])
	con = con or len(dong) >= gioi_han
	moc_moi = max([x["luc"] for x in ds] or [""])
	return {"ds": ds, "co_phong_ban": 1 if bp else 0, "so_ngay": SO_NGAY, "con_nua": 1 if con else 0,
		"moc_moi": moc_moi}


@frappe.whitelist()
def da_xem(den=None):
	"""Đánh dấu đã đọc tới tin mới nhất ĐÃ HIỆN (den, do thong_bao trả về). Không lùi mốc,
	không vượt quá bây giờ. Thiếu den (bản app cũ) thì giữ cách cũ: tới bây giờ."""
	bay_gio = str(now_datetime())
	luc = str(den or "").strip() or bay_gio
	luc = min(luc, bay_gio)
	cu = _da_xem()
	if cu and cu >= luc:
		return {"luc": cu}
	frappe.defaults.set_user_default(KHOA_DA_XEM, luc, user=frappe.session.user)
	return {"luc": luc}
