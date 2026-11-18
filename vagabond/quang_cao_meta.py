# -*- coding: utf-8 -*-
"""v674: đọc số Meta ĐÃ TIÊU mỗi ngày cho Marketing (chỉ đọc, quyền ads_read).

Vì sao có tệp này
--------------------------------------------------------------------
Anh Việt 17/11/2026 muốn ERP tự lấy chi phí quảng cáo Meta thay nhập tay, để
Marketing xem hiệu quả theo ngày và để sau này tính KPI. Anh Việt và chị Dung
chốt 18/11/2026 (prompt anh dán, mục 1):
  - Hằng ngày đọc số Meta ĐÃ TIÊU theo tài khoản quảng cáo và chiến dịch.
  - Đây KHÔNG phải số đã thanh toán: tiền thật trừ thẻ lấy từ sao kê thẻ
    Shinhan (chi_phi_meta.py). Màn Marketing ghi rõ là số tham khảo.
  - Múi giờ: đọc timezone_name của từng tài khoản quảng cáo, cắt ngày theo đó.
  - Mã truy cập: giám đốc tự tạo (người dùng hệ thống trong Business Manager)
    và tự dán vào ô Password trong Cài đặt. Mã chỉ đọc ở máy chủ lúc chạy, không
    đi vào nhật ký lỗi, comment, URL lưu lại hay tin Zalo.

Luật đọc (mục 3 của prompt)
--------------------------------------------------------------------
- Chỉ đọc ngày ĐÃ KẾT THÚC theo múi giờ tài khoản. Đọc lại một khoảng gần đây vì
  Meta còn điều chỉnh số; đọc lại thì ghi THAY số cũ, không cộng dồn.
- Đọc hết mọi trang, có hạn thời gian và thử lại có giới hạn. Trang nào lỗi thì
  cả cửa sổ ngày đó không nhận: giữ số cũ, báo thiếu. Một tài khoản lỗi không làm
  mất số của tài khoản khác. Số 0 thật được lưu; lỗi mạng không thành số 0.
- Chỉ theo trang ở đúng máy chủ Meta (graph.facebook.com).
- Không cộng hai tiền tệ khác nhau.

Nguồn chính thức đã đối chiếu 18/11/2026:
  Insights edge của ad account (level campaign, time_increment, time_range
  YYYY-MM-DD, paging.next): developers.facebook.com/documentation/ads-commerce/
  marketing-api/reference/ad-account/insights
  Ad Account (timezone_name, currency): developers.facebook.com/docs/graph-api/
  reference/ad-account/
"""

import json
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib.parse import urlparse

try:  # CI không có requests: nạp mềm, phần thuần vẫn chạy.
	import requests
except Exception:  # pragma: no cover
	requests = None

DT = "Vagabond Chi Phi Quang Cao Ngay"
CAI_DAT = "Vagabond Settings"
HOST = "graph.facebook.com"
TRUONG = "campaign_id,campaign_name,spend,account_currency,date_start,date_stop"
GIOI_HAN_TRANG = 500
TOI_DA_TRANG = 200
CUA_SO_NGAY = 31
SO_LAN_THU = 3
HAN_GIO = 25
DOC_LAI_TOI_DA = 28
MA_TIN = "mkt_meta_loi"

LOI_HET_HAN = "het_han"
LOI_QUYEN = "thieu_quyen"
LOI_GIOI_HAN = "gioi_han"
LOI_MANG = "mang"
LOI_MAY_CHU = "may_chu"
LOI_TU_CHOI = "tu_choi"
LOI_DU_LIEU = "du_lieu"
CAU_LOI = {
	LOI_HET_HAN: "Mã truy cập Meta đã hết hạn hoặc bị thu hồi. Giám đốc tạo mã mới trong Business Manager rồi dán lại vào Cài đặt.",
	LOI_QUYEN: "Mã truy cập Meta thiếu quyền xem tài khoản quảng cáo. Giám đốc cấp quyền ads_read cho người dùng hệ thống rồi tạo mã lại.",
	LOI_GIOI_HAN: "Meta đang giới hạn số lần gọi. Hệ thống tự thử lại lượt sau, chưa cần làm gì.",
	LOI_MANG: "Chưa kết nối được tới Meta. Hệ thống tự thử lại lượt sau.",
	LOI_MAY_CHU: "Máy chủ Meta đang lỗi. Hệ thống tự thử lại lượt sau.",
	LOI_TU_CHOI: "Meta từ chối yêu cầu đọc số. Quản trị hệ thống kiểm mã tài khoản quảng cáo trong Cài đặt.",
	LOI_DU_LIEU: "Meta trả dữ liệu không đúng dạng nên hệ thống không nhận lượt này. Quản trị hệ thống xem lại.",
}
LOI_TU_THU_LAI = (LOI_GIOI_HAN, LOI_MANG, LOI_MAY_CHU)


class LoiMeta(Exception):
	"""Lỗi khi đọc Meta. loai trong CAU_LOI; chu đã che bí mật."""

	def __init__(self, loai, chu=""):
		super().__init__(chu or loai)
		self.loai = loai
		self.chu = chu


# ------------------------------------------------------------- phần thuần


def chuan_tai_khoan(chu):
	"""Ô tài khoản quảng cáo: mỗi dòng (hoặc dấu phẩy) một mã. THUẦN.

	Nhận "act_123", "123", có dấu cách. Trả (danh sách act_<số> không trùng, giữ
	thứ tự; danh sách mục sai)."""
	dung, sai = [], []
	for x in re.split(r"[\n,;]+", str(chu or "")):
		x = x.strip()
		if not x:
			continue
		m = re.fullmatch(r"(?:act_)?(\d{5,20})", x, re.I)
		if not m:
			sai.append(x)
			continue
		ma = "act_" + m.group(1)
		if ma not in dung:
			dung.append(ma)
	return dung, sai


def doc_cai_dat(c):
	"""Đọc ô Cài đặt đúng nghĩa từng ô. THUẦN. Trả (cấu hình, danh sách câu lỗi).

	Không dùng "or mặc định" (H8 loại 14): 0 ở ô Đọc lại là đọc đúng hôm qua; ô
	trống là chưa điền và báo rõ."""
	bat = 1 if str(c.get("bat") or "0").strip() in ("1", "True", "true") else 0
	cfg = {"bat": bat, "tai_khoan": [], "tu_ngay": None, "doc_lai": None}
	if not bat:
		return cfg, []
	loi = []
	if not c.get("co_ma"):
		loi.append("Chưa dán mã truy cập Meta.")
	tks, sai = chuan_tai_khoan(c.get("tai_khoan"))
	if sai:
		loi.append("Mã tài khoản quảng cáo không đúng dạng: %s. Mỗi dòng một mã dạng act_ và dãy số." % ", ".join(sai[:5]))
	if not tks and not sai:
		loi.append("Chưa điền tài khoản quảng cáo.")
	cfg["tai_khoan"] = tks
	tn = c.get("tu_ngay")
	if tn in (None, ""):
		loi.append("Chưa chọn ngày bắt đầu đọc.")
	else:
		try:
			cfg["tu_ngay"] = date.fromisoformat(str(tn)[:10])
		except ValueError:
			loi.append("Ngày bắt đầu đọc không đúng dạng.")
	dl = c.get("doc_lai")
	if dl is None or str(dl).strip() == "":
		loi.append("Chưa điền số ngày đọc lại.")
	else:
		try:
			n = int(str(dl).strip())
		except ValueError:
			n = -1
		if n < 0 or n > DOC_LAI_TOI_DA:
			loi.append("Số ngày đọc lại phải từ 0 tới %d." % DOC_LAI_TOI_DA)
		else:
			cfg["doc_lai"] = n
	return cfg, loi


def ngay_da_xong(bay_gio, mui_gio):
	"""Ngày cuối cùng đã kết thúc theo múi giờ tài khoản. THUẦN.

	bay_gio: datetime có múi giờ (UTC). mui_gio sai thì ném ValueError: không
	đoán múi giờ thay Meta."""
	from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

	if bay_gio.tzinfo is None:
		raise ValueError("Giờ hệ thống thiếu múi giờ.")
	try:
		tz = ZoneInfo(str(mui_gio or ""))
	except (ZoneInfoNotFoundError, ValueError):
		raise ValueError("Múi giờ tài khoản quảng cáo không hợp lệ: %r" % mui_gio) from None
	return bay_gio.astimezone(tz).date() - timedelta(days=1)


def khoang_doc(ngay_cuoi, tu_ngay, doc_lai, moc_cu):
	"""Khoảng ngày cần đọc lượt này. THUẦN. None là chưa có gì để đọc.

	moc_cu: ngày cuối đã đọc trọn ở lượt trước (None nếu chưa từng đọc). Luôn đọc
	lại doc_lai ngày gần nhất; ngày lỡ chưa đọc (máy tắt mấy hôm) thì đọc bù từ
	sau mốc cũ. Không bao giờ đọc trước ngày bắt đầu."""
	if ngay_cuoi < tu_ngay:
		return None
	dau = ngay_cuoi - timedelta(days=int(doc_lai))
	if moc_cu is None:
		dau = tu_ngay
	elif moc_cu + timedelta(days=1) < dau:
		dau = moc_cu + timedelta(days=1)
	return max(dau, tu_ngay), ngay_cuoi


def chia_cua_so(tu, den, n=CUA_SO_NGAY):
	"""Chia khoảng ngày thành các cửa sổ tối đa n ngày. THUẦN."""
	ra = []
	a = tu
	while a <= den:
		b = min(den, a + timedelta(days=n - 1))
		ra.append((a, b))
		a = b + timedelta(days=1)
	return ra


def url_ke_hop_le(url):
	"""Đường trang kế tiếp chỉ đi theo khi đúng https://graph.facebook.com. THUẦN."""
	try:
		u = urlparse(str(url or ""))
	except ValueError:
		return False
	return u.scheme == "https" and (u.hostname or "").lower() == HOST and not u.username and not u.password


def che(chu, bi_mat=None):
	"""Che mã truy cập trong mọi chuỗi trước khi ghi nhật ký hay báo. THUẦN."""
	s = str(chu or "")
	if bi_mat:
		s = s.replace(str(bi_mat), "***")
	s = re.sub(r"(access_token=)[^&\s\"']+", r"\1***", s, flags=re.I)
	s = re.sub(r"(appsecret_proof=)[^&\s\"']+", r"\1***", s, flags=re.I)
	s = re.sub(r"\bEAA[A-Za-z0-9]{20,}", "***", s)
	return s


def so_tien(chu):
	"""Chuỗi spend của Meta thành Decimal 2 số lẻ. THUẦN. Sai dạng thì None."""
	if chu is None or isinstance(chu, bool):
		return None
	try:
		d = Decimal(str(chu).strip())
	except (InvalidOperation, ValueError):
		return None
	if d.is_nan() or d < 0:
		return None
	return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def doc_dong(item):
	"""Một dòng insights (level campaign, time_increment=1). THUẦN.

	Ném LoiMeta(du_lieu) nếu thiếu ngày, ngày bắt đầu khác ngày kết thúc, thiếu
	mã chiến dịch hay số tiền sai dạng: không đoán số."""
	if not isinstance(item, dict):
		raise LoiMeta(LOI_DU_LIEU, "Dòng không phải đối tượng.")
	a, b = item.get("date_start"), item.get("date_stop")
	if not a or a != b:
		raise LoiMeta(LOI_DU_LIEU, "Dòng không đúng một ngày (%s, %s)." % (a, b))
	try:
		ngay = date.fromisoformat(str(a)[:10])
	except ValueError:
		raise LoiMeta(LOI_DU_LIEU, "Ngày sai dạng.") from None
	cd = str(item.get("campaign_id") or "").strip()
	if not cd:
		raise LoiMeta(LOI_DU_LIEU, "Thiếu mã chiến dịch.")
	tien = so_tien(item.get("spend"))
	if tien is None:
		raise LoiMeta(LOI_DU_LIEU, "Số tiền sai dạng ở chiến dịch %s." % cd)
	return {"ngay": ngay, "chien_dich": cd, "ten_chien_dich": str(item.get("campaign_name") or "")[:140],
		"so_tien": float(tien), "tien_te": str(item.get("account_currency") or "").upper()[:3]}


def khoa_dong(tai_khoan, ngay, chien_dich):
	return "%s:%s:%s" % (tai_khoan, str(ngay)[:10], chien_dich)


def ke_hoach_ghi(cu, moi, tai_khoan, tu, den):
	"""Việc ghi sau khi đọc TRỌN một cửa sổ ngày. THUẦN.

	cu: {khoá: (số tiền, tiền tệ)} các dòng đang có trong [tu, den]. moi: các dòng
	vừa đọc. Trả (ghi, ve_khong): ghi là dòng mới hoặc đổi số, ve_khong là khoá cũ
	Meta không còn trả trong cửa sổ (Meta điều chỉnh về 0). Chỉ gọi khi đã đọc
	đủ mọi trang; đọc lỗi thì không gọi, số cũ giữ nguyên."""
	ghi = []
	thay = set()
	gop = {}
	for d in moi:
		if d["ngay"] < tu or d["ngay"] > den:
			continue
		k = khoa_dong(tai_khoan, d["ngay"], d["chien_dich"])
		if k in gop:
			# Meta trả hai dòng một chiến dịch một ngày: cộng, cùng tiền tệ mới cộng.
			if gop[k]["tien_te"] != d["tien_te"]:
				raise LoiMeta(LOI_DU_LIEU, "Một chiến dịch hai tiền tệ trong cùng ngày.")
			gop[k] = dict(gop[k], so_tien=round(gop[k]["so_tien"] + d["so_tien"], 2))
		else:
			gop[k] = dict(d, khoa=k)
	for k, d in gop.items():
		thay.add(k)
		c = cu.get(k)
		if c is None or abs(float(c[0]) - d["so_tien"]) > 0.004 or (c[1] or "") != d["tien_te"]:
			ghi.append(d)
	ve_khong = sorted(k for k, c in cu.items() if k not in thay and abs(float(c[0] or 0)) > 0.004)
	return ghi, ve_khong


def phan_loai_loi(ma, ma_phu=None, http=None):
	"""Loại lỗi Meta theo mã lỗi Graph API. THUẦN."""
	try:
		ma = int(ma)
	except (TypeError, ValueError):
		ma = None
	if ma == 190:
		return LOI_HET_HAN
	if ma in (10, 102, 104) or (ma is not None and 200 <= ma <= 299):
		return LOI_QUYEN
	if ma in (4, 17, 32, 613, 80000, 80004):
		return LOI_GIOI_HAN
	if ma in (1, 2):
		return LOI_MAY_CHU
	if ma is None and http is not None and int(http) >= 500:
		return LOI_MAY_CHU
	return LOI_TU_CHOI


def gop_theo_ngay(dong, tu, den):
	"""Gộp số tiêu theo ngày và tiền tệ, đủ mọi ngày trong khoảng. THUẦN.

	Không bao giờ cộng hai tiền tệ: mỗi ngày giữ một bảng {tiền tệ: số}."""
	ngay = {}
	a = tu
	while a <= den:
		ngay[a.isoformat()] = {}
		a += timedelta(days=1)
	for d in dong:
		k = str(d["ngay"])[:10]
		if k not in ngay:
			continue
		tt = d.get("tien_te") or ""
		ngay[k][tt] = round(ngay[k].get(tt, 0.0) + float(d.get("so_tien") or 0), 2)
	return ngay


def trang_thai_ngay(ngay_iso, da_doc_toi, doc_lai, co_so):
	"""Chip trạng thái của một ngày trên màn Marketing. THUẦN.

	da_doc_toi: ngày cuối đã đọc trọn (chuỗi ISO hoặc None)."""
	if not da_doc_toi or ngay_iso > da_doc_toi:
		return "Chưa đọc"
	moc = (date.fromisoformat(da_doc_toi) - timedelta(days=int(doc_lai or 0))).isoformat()
	if ngay_iso > moc:
		return "Meta còn điều chỉnh"
	return "Đã chốt" if co_so else "Không chi"


# ------------------------------------------------ phần chạm Frappe

import frappe  # noqa: E402
from frappe.utils import getdate, now_datetime, nowdate  # noqa: E402

QUYEN_XEM = {"System Manager", "Marketing", "Giám đốc", "AP Giám đốc", "Accounts Manager", "Accounts User",
	"AP Kiểm soát (FIN)", "Vagabond Bao cao"}
QUYEN_DOC_LAI = {"System Manager", "Giám đốc", "AP Giám đốc", "Marketing"}


def _o(ten):
	return frappe.db.get_single_value(CAI_DAT, ten)


def _ma():
	from frappe.utils.password import get_decrypted_password

	try:
		return get_decrypted_password(CAI_DAT, CAI_DAT, "meta_ads_ma", raise_exception=False) or ""
	except Exception:
		return ""


def _cau_hinh():
	return doc_cai_dat({
		"bat": _o("meta_ads_bat"),
		"co_ma": bool(_ma()),
		"tai_khoan": _o("meta_ads_tai_khoan"),
		"tu_ngay": _o("meta_ads_tu_ngay"),
		"doc_lai": _o("meta_ads_doc_lai"),
	})


def _phien_ban():
	from vagabond.don_web import GRAPH_MAC_DINH

	return str(_o("meta_graph_phien_ban") or "").strip() or GRAPH_MAC_DINH


def _trang_thai():
	try:
		return json.loads(_o("meta_ads_trang_thai") or "{}") or {}
	except Exception:
		return {}


def _luu_trang_thai(tk, **gt):
	tt = _trang_thai()
	tt.setdefault(tk, {}).update(gt)
	frappe.db.set_single_value(CAI_DAT, "meta_ads_trang_thai", json.dumps(tt, ensure_ascii=False, default=str))


def _goi(url, params, ma):
	"""Một lời gọi GET tới Meta, thử lại có giới hạn với lỗi tạm. Ném LoiMeta đã
	che bí mật. Không ghi nguyên phản hồi lỗi hay đường dẫn có mã ra đâu cả."""
	import time

	if requests is None:
		raise LoiMeta(LOI_MANG, "Máy chủ thiếu thư viện requests.")
	if not url_ke_hop_le(url):
		raise LoiMeta(LOI_TU_CHOI, "Đường dẫn không thuộc máy chủ Meta.")
	cuoi = None
	for lan in range(SO_LAN_THU):
		try:
			r = requests.get(url, params=params, timeout=HAN_GIO, allow_redirects=False)
		except Exception as e:
			cuoi = LoiMeta(LOI_MANG, che(type(e).__name__, ma))
			time.sleep(1 + lan * 2)
			continue
		try:
			j = r.json()
		except Exception:
			j = None
		if r.status_code == 200 and isinstance(j, dict) and "error" not in j:
			return j
		e = (j or {}).get("error") if isinstance(j, dict) else None
		loai = phan_loai_loi((e or {}).get("code"), (e or {}).get("error_subcode"), r.status_code)
		cuoi = LoiMeta(loai, che("HTTP %s mã %s: %s" % (r.status_code, (e or {}).get("code"), (e or {}).get("message") or ""), ma)[:300])
		if loai not in LOI_TU_THU_LAI:
			raise cuoi
		time.sleep(1 + lan * 2)
	raise cuoi


def _thong_tin_tk(tk, ma, phien):
	j = _goi("https://%s/%s/%s" % (HOST, phien, tk), {"fields": "timezone_name,currency,name", "access_token": ma}, ma)
	if not j.get("timezone_name"):
		raise LoiMeta(LOI_DU_LIEU, "Meta không trả múi giờ của tài khoản.")
	return {"mui_gio": j.get("timezone_name"), "tien_te": str(j.get("currency") or "").upper(), "ten": str(j.get("name") or "")[:140]}


def doc_insights(tk, ma, phien, tu, den):
	"""Đọc TRỌN một cửa sổ ngày, mọi trang. Lỗi ở bất kỳ trang nào thì ném ra:
	nơi gọi không nhận số một phần."""
	url = "https://%s/%s/%s/insights" % (HOST, phien, tk)
	params = {"level": "campaign", "time_increment": 1, "fields": TRUONG, "limit": GIOI_HAN_TRANG,
		"time_range": json.dumps({"since": tu.isoformat(), "until": den.isoformat()}), "access_token": ma}
	dong = []
	for _ in range(TOI_DA_TRANG):
		j = _goi(url, params, ma)
		for it in j.get("data") or []:
			dong.append(doc_dong(it))
		nxt = ((j.get("paging") or {}).get("next") or "")
		if not nxt:
			return dong
		if not url_ke_hop_le(nxt):
			raise LoiMeta(LOI_TU_CHOI, "Trang kế tiếp không thuộc máy chủ Meta.")
		url, params = nxt, None
	raise LoiMeta(LOI_DU_LIEU, "Quá %d trang trong một cửa sổ ngày." % TOI_DA_TRANG)


def _ghi_cua_so(tk, info, dong, tu, den):
	"""Ghi một cửa sổ đã đọc trọn: thay số cũ, ngày Meta không còn trả về 0."""
	cu = {}
	for r in frappe.db.sql(
			"select name, so_tien, tien_te from `tabVagabond Chi Phi Quang Cao Ngay` where tai_khoan=%s and ngay between %s and %s for update",
			(tk, tu, den), as_dict=True):
		cu[r.name] = (r.so_tien, r.tien_te)
	ghi, ve_khong = ke_hoach_ghi(cu, dong, tk, tu, den)
	luc = now_datetime()
	nguon = "Meta Insights %s" % _phien_ban()
	for d in ghi:
		if d["khoa"] in cu:
			frappe.db.set_value(DT, d["khoa"], {"so_tien": d["so_tien"], "tien_te": d["tien_te"],
				"ten_chien_dich": d["ten_chien_dich"], "dong_bo_luc": luc, "nguon": nguon}, update_modified=False)
			continue
		x = frappe.new_doc(DT)
		x.update({"khoa": d["khoa"], "ngay": d["ngay"], "tai_khoan": tk, "ten_tai_khoan": info.get("ten"),
			"chien_dich": d["chien_dich"], "ten_chien_dich": d["ten_chien_dich"], "so_tien": d["so_tien"],
			"tien_te": d["tien_te"], "mui_gio": info.get("mui_gio"), "dong_bo_luc": luc, "nguon": nguon})
		x.flags.vgb_meta = True
		x.flags.ignore_permissions = True
		x.insert(ignore_permissions=True)
	for k in ve_khong:
		frappe.db.set_value(DT, k, {"so_tien": 0, "dong_bo_luc": luc}, update_modified=False)
	return len(ghi), len(ve_khong)


def dong_bo_tai_khoan(tk, cfg, ma, phien, bay_gio=None):
	"""Đọc một tài khoản quảng cáo. Mỗi cửa sổ đọc trọn thì ghi và commit ngay,
	nên lỗi ở cửa sổ sau không làm mất cửa sổ trước."""
	bay_gio = bay_gio or datetime.now(timezone.utc)
	khoa = "vgb_meta_%s" % tk
	if not frappe.db.sql("select get_lock(%s, 0)", (khoa,))[0][0]:
		return {"bo_qua": "Đang có lượt đọc khác của tài khoản này."}
	try:
		info = _thong_tin_tk(tk, ma, phien)
		try:
			cuoi = ngay_da_xong(bay_gio, info["mui_gio"])
		except ValueError as e:
			raise LoiMeta(LOI_DU_LIEU, str(e)) from None
		tt = _trang_thai().get(tk) or {}
		moc = date.fromisoformat(tt["moc"]) if tt.get("moc") else None
		khoang = khoang_doc(cuoi, cfg["tu_ngay"], cfg["doc_lai"], moc)
		so = 0
		if khoang:
			for a, b in chia_cua_so(*khoang):
				dong = doc_insights(tk, ma, phien, a, b)
				g, v = _ghi_cua_so(tk, info, dong, a, b)
				so += g + v
				moc_moi = max(b, moc) if moc else b
				_luu_trang_thai(tk, moc=moc_moi.isoformat(), lan_cuoi=str(now_datetime()), mui_gio=info["mui_gio"],
					tien_te=info["tien_te"], ten=info["ten"], loi="", loai_loi="")
				moc = moc_moi
				frappe.db.commit()
		return {"so_dong": so, "moc": moc.isoformat() if moc else None}
	finally:
		frappe.db.sql("select release_lock(%s)", (khoa,))


def co_nhom_nhan():
	"""Có nhóm Zalo nào đang nhận tin Meta lỗi không. Không có thì màn hiện cảnh
	báo cấu hình, không coi là đã báo."""
	from vagabond import kenh_zalo

	try:
		if not kenh_zalo._bat():
			return False
		loai, chu_de = kenh_zalo.TIN[MA_TIN][3], kenh_zalo.TIN[MA_TIN][4]
		return bool(kenh_zalo.chon_nhom(kenh_zalo._cac_nhom(), loai, chu_de, MA_TIN))
	except Exception:
		return False


def _bao_loi(tk, loi):
	from vagabond import kenh_zalo

	_luu_trang_thai(tk, loi=CAU_LOI.get(loi.loai, ""), loai_loi=loi.loai, luc_loi=str(now_datetime()))
	if loi.loai in LOI_TU_THU_LAI:
		return
	kenh_zalo.bao(
		"canh_bao", "he_thong", "Đọc chi phí quảng cáo Meta bị dừng",
		dong=["Tài khoản quảng cáo %s" % tk, CAU_LOI.get(loi.loai, "")],
		link="/chi-phi-quang-cao-meta", khoa="meta_loi:%s:%s:%s" % (tk, loi.loai, nowdate()), ma_tin="mkt_meta_loi")


def dong_bo_tu_dong():
	"""Nhịp hằng ngày. Công tắc tắt thì không làm gì. Một tài khoản lỗi thì báo và
	đi tiếp tài khoản sau."""
	cfg, loi = _cau_hinh()
	if not cfg["bat"]:
		return {"bat": 0}
	if loi:
		_luu_trang_thai("_cau_hinh", loi=" ".join(loi), luc_loi=str(now_datetime()))
		frappe.db.commit()
		return {"loi": loi}
	_luu_trang_thai("_cau_hinh", loi="")
	ma = _ma()
	phien = _phien_ban()
	kq = {}
	for tk in cfg["tai_khoan"]:
		try:
			kq[tk] = dong_bo_tai_khoan(tk, cfg, ma, phien)
		except LoiMeta as e:
			frappe.db.rollback()
			_bao_loi(tk, e)
			frappe.log_error(che("%s: %s" % (e.loai, e.chu), ma), "Đọc chi phí Meta lỗi %s" % tk)
			kq[tk] = {"loi": e.loai}
		except Exception:
			frappe.db.rollback()
			_bao_loi(tk, LoiMeta(LOI_DU_LIEU))
			frappe.log_error(che(frappe.get_traceback(), ma), "Đọc chi phí Meta lỗi %s" % tk)
			kq[tk] = {"loi": LOI_DU_LIEU}
		frappe.db.commit()
	return kq


def _kiem_xem():
	if not (set(frappe.get_roles()) & QUYEN_XEM):
		frappe.throw("Bạn chưa có quyền xem chi phí quảng cáo.", frappe.PermissionError)


def doanh_thu_web_theo_ngay(tu, den):
	"""Doanh thu web: đơn web đã ghi sổ, theo ngày khách đặt (tham khảo)."""
	ra = {}
	for r in frappe.db.sql(
			"""select date(creation) d, sum(gia_tri_ghi_so) t from `tabVagabond Don Web`
			where trang_thai='Da ghi so' and date(creation) between %s and %s group by date(creation)""",
			(tu, den)):
		ra[str(r[0])] = round(float(r[1] or 0))
	return ra


@frappe.whitelist()
def tong_quan(tu=None, den=None, tai_khoan=None, trang_thai=None):
	"""Màn Chi phí quảng cáo Meta (Marketing): chi theo ngày cạnh doanh thu web."""
	_kiem_xem()
	den = getdate(den or (getdate(nowdate()) - timedelta(days=1)))
	tu = getdate(tu or (den - timedelta(days=29)))
	if tu > den:
		tu, den = den, tu
	cfg, loi = _cau_hinh()
	tt = _trang_thai()
	tks_cfg = cfg["tai_khoan"] or sorted(k for k in tt if k.startswith("act_"))
	f = {"ngay": ["between", [tu, den]]}
	if tai_khoan:
		f["tai_khoan"] = tai_khoan
	dong = frappe.get_all(DT, filters=f, fields=["ngay", "tai_khoan", "chien_dich", "ten_chien_dich", "so_tien", "tien_te"],
		limit_page_length=0)
	ngay = gop_theo_ngay(dong, tu, den)
	dt_web = doanh_thu_web_theo_ngay(tu, den)
	chon = [k for k in ([tai_khoan] if tai_khoan else tks_cfg)]
	moc = [tt.get(k, {}).get("moc") for k in chon if tt.get(k, {}).get("moc")]
	# Ngày chỉ coi là đã đọc khi MỌI tài khoản đang xem đã đọc tới đó.
	da_doc_toi = min(moc) if moc and len(moc) == len(chon) else None
	rows = []
	dem = {"": 0}
	for k in sorted(ngay, reverse=True):
		ct = ngay[k]
		trang = trang_thai_ngay(k, da_doc_toi, cfg.get("doc_lai") if cfg.get("doc_lai") is not None else 0, any(v for v in ct.values()))
		dem[""] += 1
		dem[trang] = dem.get(trang, 0) + 1
		if trang_thai and trang != trang_thai:
			continue
		rows.append({"ngay": k, "chi": ct, "doanh_thu_web": dt_web.get(k, 0), "trang_thai": trang})
	tong = {}
	for k, ct in ngay.items():
		for t, v in ct.items():
			tong[t] = round(tong.get(t, 0) + v, 2)
	return {
		"tu": str(tu), "den": str(den), "rows": rows, "dem": dem, "tong_chi": tong,
		"tong_doanh_thu_web": sum(dt_web.values()),
		"tai_khoan": [{"ma": k, "ten": (tt.get(k) or {}).get("ten") or k, "mui_gio": (tt.get(k) or {}).get("mui_gio") or "",
			"tien_te": (tt.get(k) or {}).get("tien_te") or "", "moc": (tt.get(k) or {}).get("moc") or "",
			"lan_cuoi": (tt.get(k) or {}).get("lan_cuoi") or "", "loi": (tt.get(k) or {}).get("loi") or ""} for k in tks_cfg],
		"cau_hinh": {"bat": cfg["bat"], "loi": loi + ([(tt.get("_cau_hinh") or {}).get("loi")] if (tt.get("_cau_hinh") or {}).get("loi") and not loi else []),
			"doc_lai": cfg.get("doc_lai")},
		"co_nhom_nhan": 1 if co_nhom_nhan() else 0,
		"duoc_doc_lai": 1 if set(frappe.get_roles()) & QUYEN_DOC_LAI else 0,
	}


@frappe.whitelist()
def chi_tiet_ngay(ngay, tai_khoan=None):
	"""Các chiến dịch của một ngày."""
	_kiem_xem()
	f = {"ngay": getdate(ngay)}
	if tai_khoan:
		f["tai_khoan"] = tai_khoan
	return frappe.get_all(DT, filters=f, fields=["tai_khoan", "ten_tai_khoan", "chien_dich", "ten_chien_dich", "so_tien", "tien_te", "dong_bo_luc"],
		order_by="so_tien desc", limit_page_length=0)


@frappe.whitelist(methods=["POST"])
def doc_lai_ngay():
	"""Bấm Đọc lại từ Meta: xếp một lượt đọc chạy nền (không chạy trong yêu cầu web)."""
	if not (set(frappe.get_roles()) & QUYEN_DOC_LAI):
		frappe.throw("Bạn chưa có quyền yêu cầu đọc lại số Meta.", frappe.PermissionError)
	cfg, loi = _cau_hinh()
	if not cfg["bat"]:
		frappe.throw("Đọc chi phí Meta đang tắt. Quản trị hệ thống bật ở Cài đặt, mục Chi phí quảng cáo Meta.")
	if loi:
		frappe.throw(" ".join(loi))
	frappe.enqueue("vagabond.quang_cao_meta.dong_bo_tu_dong", queue="long", timeout=1500,
		job_id="vgb_meta_doc_lai", deduplicate=True, enqueue_after_commit=True)
	return {"ok": 1, "loi_nhan": "Đã xếp lượt đọc lại. Vài phút sau mở lại màn để xem số mới."}


TRUONG_MOI = {
	"Vagabond Settings": [
		{"fieldname": "sec_meta_chi_phi", "fieldtype": "Section Break", "insert_after": "meta_graph_phien_ban",
			"label": "Chi phí quảng cáo Meta (đọc số đã tiêu)"},
		{"fieldname": "meta_ads_bat", "fieldtype": "Check", "insert_after": "sec_meta_chi_phi",
			"label": "Bật đọc chi phí quảng cáo Meta hằng ngày",
			"description": "Mỗi sáng hệ thống đọc số Meta đã tiêu hôm qua theo tài khoản quảng cáo và chiến dịch. "
				"Đây là số tham khảo cho Marketing, chưa phải số trừ thẻ."},
		{"fieldname": "meta_ads_ma", "fieldtype": "Password", "insert_after": "meta_ads_bat",
			"label": "Mã truy cập người dùng hệ thống Meta (quyền ads_read)",
			"description": "Giám đốc tự tạo trong Business Manager rồi tự dán vào đây. Hệ thống chỉ dùng ở máy chủ, không hiện lại."},
		{"fieldname": "meta_ads_tai_khoan", "fieldtype": "Small Text", "insert_after": "meta_ads_ma",
			"label": "Tài khoản quảng cáo, mỗi dòng một mã",
			"description": "Mã dạng act_ và dãy số, lấy ở Trình quản lý quảng cáo. Có thể bỏ chữ act_."},
		{"fieldname": "col_meta_chi_phi", "fieldtype": "Column Break", "insert_after": "meta_ads_tai_khoan"},
		{"fieldname": "meta_ads_tu_ngay", "fieldtype": "Date", "insert_after": "col_meta_chi_phi",
			"label": "Đọc từ ngày",
			"description": "Ngày đầu tiên hệ thống đọc số. Không đọc ngày trước mốc này."},
		{"fieldname": "meta_ads_doc_lai", "fieldtype": "Int", "insert_after": "meta_ads_tu_ngay",
			"label": "Đọc lại bao nhiêu ngày gần nhất",
			"description": "Meta còn điều chỉnh số vài ngày sau; mỗi lần đọc ghi thay số của các ngày này. 0 là chỉ đọc hôm qua. Tối đa 28."},
		{"fieldname": "meta_ads_trang_thai", "fieldtype": "Long Text", "insert_after": "meta_ads_doc_lai",
			"label": "Trạng thái đọc chi phí Meta (hệ thống ghi)", "read_only": 1, "hidden": 1},
	],
}
