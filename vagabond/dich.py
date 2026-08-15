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

GEMINI = (
	"https://generativelanguage.googleapis.com/v1beta/models/"
	"gemini-2.0-flash:generateContent"
)

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
	try:
		r = requests.post(
			GEMINI,
			params={"key": khoa},
			json=than,
			timeout=max(TIMEOUT, 25),
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "Vagabond: Gemini khong goi duoc")
		return {"ok": 0, "ly_do": "khong_goi_duoc_dich_vu_dich", "ra": ds}

	if r.status_code != 200:
		frappe.log_error(r.text[:2000], "Vagabond: Gemini tra loi %s" % r.status_code)
		return {
			"ok": 0,
			"ly_do": "dich_vu_tra_loi_%s" % r.status_code,
			"ra": ds,
		}

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
