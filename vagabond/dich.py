"""Dich tieng Viet sang tieng Anh cho to bao gia, goi Google Gemini.

Anh Viet 15/08/2026: *"'Name in English' các phần này có thể nối với API
google translate hay tool gì đó (AI?) để tự động dịch cho Loan Anh được
không?"* - anh chon Gemini vi no hieu ngu canh banh trai, dich ten mon va
bang nguyen lieu ra cau chu tu nhien hon Google Translate.

Khoa dat o Cai dat Vagabond, o "gemini_api_key". Anh Viet tu dan khoa vao,
KHONG ai nhap ho.
"""

import json

import frappe
import requests

from vagabond.lib import TIMEOUT, cfg, key

GOC = "https://generativelanguage.googleapis.com/v1beta/models"

# Vi sao KHONG chon mot ten model cu the
# --------------------------------------
# Ngay 15/08/2026 nut dich chet, Google tra 404 nguyen van: "This model
# models/gemini-2.0-flash is no longer available". Khoa cua anh Viet van
# tot - goi thu danh sach model bang chinh khoa do ra 38 model dang song.
# Tuc day khong phai loi cau hinh ma la Google GO model di.
#
# Dong ten cu the nao roi cung den ngay bi go. "gemini-flash-latest" la bi
# danh do Google tu doi sang ban flash moi nhat, nen no khong chet vi bi
# go. De sau no mot day du phong: gap dung 404 thi tu roi xuong ten ke
# tiep va thu lai, chu khong nem loi vao mat Loan Anh giua luc lam viec.
# Day nay da duoc GOI THU THAT ngay 16/08/2026 bang chinh khoa cua anh Viet,
# khong phai doan tu tai lieu:
#   gemini-flash-latest       200
#   gemini-2.5-flash          404  <- da bi go, tung nam trong day nay
#   gemini-flash-lite-latest  200
#   gemini-3.5-flash          503
# Bai hoc: mot ten cu the co the da chet ma minh khong biet, nen day du
# phong chi giu cac BI DANH "-latest" do Google tu doi.
MODEL = (
	"gemini-flash-latest",
	"gemini-flash-lite-latest",
)

# Ma nao thi doi sang model khac se cuu duoc
# -------------------------------------------
# 404: Google go model do. Doi la cach duy nhat.
# 503: model do dang qua tai. Day la QUA TAI THEO TUNG MODEL, khong phai
#      Google sap - da do thay 16/08/2026: gemini-3.5-flash tra 503 trong
#      khi gemini-flash-latest tra 200 cung luc. Nen 503 cung phai doi.
# Con 401, 403 (khoa) va 429 (het luot) thi doi model khong cuu duoc gi,
# thu tiep chi ton them thoi gian cua nguoi dang ngoi doi.
MA_DOI_MODEL = (404, 503)


def _url(model):
	return "%s/%s:generateContent" % (GOC, model)

# Nhac may dich dung giong mot tiem banh Phap chu khong phai may dich thuat.
LOI_NHAC = (
	"You translate Vietnamese pastry-shop text into natural English for a "
	"French-style artisan patisserie in Vietnam. Rules:\n"
	"- Keep the tone of a premium bakery menu, not a machine translation.\n"
	"- Keep proper nouns, brand names and Vietnamese specialty names that have "
	"no English equivalent (for example: banh trung thu -> Mooncake, "
	"xi muoi -> salted preserved plum, tran bi -> dried tangerine peel).\n"
	"- Ingredient lists stay as ingredient lists, same order, same structure.\n"
	"- Keep line breaks exactly as in the input.\n"
	"- Do not add anything that is not in the source. Do not explain.\n"
	"Return ONLY a JSON array of translated strings, same length and same "
	"order as the input array. No markdown fence, no commentary."
)


def _khoa():
	c = cfg()
	k = key(c, "gemini_api_key")
	if not k:
		frappe.throw(
			"Chưa khai khoá Gemini. Vào Cài đặt Vagabond, ô Gemini API key, "
			"dán khoá vào rồi thử lại."
		)
	return k


def _cau_loi(ma):
	"""Cau bao loi noi NGUOI DUNG PHAI LAM GI TIEP, khong in ma may (QT-24).

	THUAN: so vao, cau chu ra. Truoc day ham dich nem thang ra chuoi
	"dich_vu_tra_loi_404" - dung voi ky thuat nhung Loan Anh doc xong khong
	biet lam gi, va that ra chinh anh Viet cung phai hoi em moi biet.
	"""
	if ma == 404:
		return (
			"Google đã đổi tên các máy dịch nên bản cũ không còn dùng được. "
			"Anh chị gõ tay phần tiếng Anh giúp em lần này, và báo kỹ thuật "
			"để cập nhật lại."
		)
	if ma in (401, 403):
		return (
			"Khoá Gemini bị từ chối. Vào Cài đặt Vagabond, ô Gemini API key, "
			"dán lại khoá mới lấy từ Google AI Studio rồi thử lại."
		)
	if ma == 429:
		return (
			"Hôm nay đã dịch hết lượt miễn phí của Google. Anh chị chờ sang "
			"ngày mai, hoặc gõ tay phần tiếng Anh cho tờ này."
		)
	if ma == 503:
		return (
			"Máy dịch của Google đang quá tải. Anh chị bấm dịch lại sau một "
			"hai phút giúp em, tờ báo giá vẫn lưu bình thường."
		)
	if 500 <= int(ma or 0) < 600:
		return (
			"Máy dịch của Google đang lỗi. Anh chị bấm dịch lại sau vài phút "
			"giúp em, tờ báo giá vẫn lưu bình thường."
		)
	return (
		"Chưa dịch được, máy dịch trả lỗi %s. Anh chị gõ tay phần tiếng Anh "
		"giúp em rồi báo kỹ thuật." % ma
	)


@frappe.whitelist()
def xem_model():
	"""Cac model Gemini con song, de chan doan khi nut dich chet.

	CHI DOC, khong dich gi. Tra ve DUY NHAT ten model - khong bao gio tra
	khoa ra ngoai.
	"""
	if not (set(frappe.get_roles()) & {"System Manager"}):
		frappe.throw("Chỉ quản trị hệ thống xem được danh sách máy dịch.")
	try:
		r = requests.get(GOC, params={"key": _khoa()}, timeout=max(TIMEOUT, 15))
	except Exception:
		return {"ok": 0, "loi": "Không gọi được Google."}
	if r.status_code != 200:
		return {"ok": 0, "loi": _cau_loi(r.status_code)}
	ds = [
		str(m.get("name") or "").replace("models/", "")
		for m in (r.json().get("models") or [])
		if "generateContent" in (m.get("supportedGenerationMethods") or [])
	]
	return {
		"ok": 1,
		"dang_dung": list(MODEL),
		"con_song": [x for x in ds if any(y in x for y in ("flash", "pro"))],
		"tong": len(ds),
	}


@frappe.whitelist()
def dich(chuoi=None):
	"""Dich mot hoac nhieu doan tieng Viet sang tieng Anh.

	Nhan mot chuoi, hoac mot mang chuoi (dich mot lan cho ca dong - nhanh va
	dong nhat cau chu hon dich le tung o).
	"""
	if not chuoi:
		return {"ok": 0, "ly_do": "khong_co_gi_de_dich", "ra": []}
	if isinstance(chuoi, str):
		try:
			ds = json.loads(chuoi)
			if not isinstance(ds, list):
				ds = [chuoi]
		except Exception:
			ds = [chuoi]
	else:
		ds = list(chuoi)

	ds = [str(x or "") for x in ds]
	co = [i for i, x in enumerate(ds) if x.strip()]
	if not co:
		return {"ok": 0, "ly_do": "khong_co_gi_de_dich", "ra": ds}

	# Lay khoa NGOAI khoi khoi try duoi: neu de trong do, cau nhac "chua khai
	# khoa Gemini" bi khoi except nuot mat, nguoi dung chi thay "khong goi
	# duoc dich vu dich" va khong biet phai lam gi (quy tac QT-24).
	khoa = _khoa()
	gui = [ds[i] for i in co]
	than = {
		"system_instruction": {"parts": [{"text": LOI_NHAC}]},
		"contents": [{"parts": [{"text": json.dumps(gui, ensure_ascii=False)}]}],
		"generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
	}
	r = None
	for i, model in enumerate(MODEL):
		try:
			r = requests.post(
				_url(model),
				params={"key": khoa},
				json=than,
				timeout=max(TIMEOUT, 25),
			)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Vagabond: Gemini khong goi duoc")
			return {
				"ok": 0,
				"ly_do": "khong_goi_duoc_dich_vu_dich",
				"loi": (
					"Không gọi được dịch vụ dịch. Mạng của máy chủ đang trục "
					"trặc, anh chị thử lại sau ít phút; nếu vẫn vậy thì gõ tay "
					"phần tiếng Anh rồi báo kỹ thuật giúp em."
				),
				"ra": ds,
			}
		if r.status_code in MA_DOI_MODEL and i < len(MODEL) - 1:
			frappe.log_error(
				r.text[:2000],
				"Vagabond: Gemini %s o %s, thu ten ke tiep" % (r.status_code, model),
			)
			continue
		break

	if r.status_code != 200:
		frappe.log_error(r.text[:2000], "Vagabond: Gemini tra loi %s" % r.status_code)
		return {"ok": 0, "ly_do": "dich_vu_tra_loi_%s" % r.status_code,
				"loi": _cau_loi(r.status_code), "ra": ds}

	try:
		j = r.json()
		chu = j["candidates"][0]["content"]["parts"][0]["text"]
		ket = json.loads(chu)
		if not isinstance(ket, list):
			raise ValueError("khong phai mang")
	except Exception:
		frappe.log_error(r.text[:2000], "Vagabond: Gemini tra ve dang la")
		return {"ok": 0, "ly_do": "ket_qua_khong_doc_duoc", "ra": ds}

	ra = list(ds)
	for n, i in enumerate(co):
		if n < len(ket) and str(ket[n] or "").strip():
			ra[i] = str(ket[n]).strip()
	return {"ok": 1, "ra": ra}
