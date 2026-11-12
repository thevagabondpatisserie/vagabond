# -*- coding: utf-8 -*-
"""v613: vẽ bảng thành ảnh PNG để Zalo Bot gửi vào nhóm (tồn cuối ngày, sản lượng).

Anh Việt 27/10/2026: "tồn kho cuối ngày (cuối ngày hôm đó còn tồn bao nhiêu bánh ở
chi nhánh nào), mà làm kiểu gửi ảnh chụp (bảng liệt kê) được không vì zalo có cho
gửi ảnh từ bot?". Zalo Bot API có sendPhoto (bot.zapps.me/docs/apis/sendPhoto, đọc
27/10/2026): nhận chat_id, photo là ĐƯỜNG DẪN ảnh, caption 1 đến 2.000 ký tự. Bot
không tải tệp lên trực tiếp, nên ảnh phải nằm ở một đường dẫn công khai Zalo tải
được: lưu thành File công khai tên ngẫu nhiên 24 ký tự, xoá sau SO_NGAY_GIU ngày.

Tách làm ba lớp:
  - THUẦN: chuẩn bảng, đo cột, cắt chữ (kiểm thử không cần Pillow, không cần site).
  - Vẽ: Pillow nạp trong thân hàm (máy CI không có Pillow; site Frappe luôn có vì
    Frappe cần nó để nén ảnh). Phông Vagabond Sans đi kèm app, đủ dấu tiếng Việt.
  - Chạm hệ: lưu File công khai, dọn ảnh cũ.
Vẽ hỏng thì nơi gọi vẫn gửi tin chữ (chú thích đã tự đủ ý), không mất tin.
"""

import os
import secrets

RONG = 1080
LE = 36
CO_TIEU_DE = 40
CO_PHU = 26
CO_CHU = 26
CAO_DONG = 46
TOI_DA_DONG = 70
SO_NGAY_GIU = 2
TIEN_TO_TEP = "zalo-"

MAU_NEN = (255, 255, 255)
MAU_CHU = (34, 34, 34)
MAU_PHU = (110, 110, 110)
MAU_DAU_BANG = (220, 239, 237)
MAU_SOC = (247, 249, 249)
MAU_KE = (214, 222, 222)
MAU_DO = (180, 35, 24)
MAU_XANH = (14, 110, 104)


def chuan_bang(cot, hang, toi_da=TOI_DA_DONG):
	"""THUẦN: mọi ô thành chữ, đủ số cột; quá toi_da dòng thì giữ toi_da - 1 dòng đầu và
	thêm một dòng "... và N dòng nữa". Mỗi hàng là list ô hoặc dict {"o": [...], "nhan": "do"|"dam"}.
	Trả (cot, [(o, nhan)])."""
	cot = [str(c) for c in cot]
	ra = []
	for h in hang or []:
		o, nhan = (h.get("o"), h.get("nhan")) if isinstance(h, dict) else (h, None)
		o = ["" if x is None else str(x) for x in (o or [])][:len(cot)]
		o += [""] * (len(cot) - len(o))
		ra.append((o, nhan))
	if len(ra) > toi_da:
		con = len(ra) - (toi_da - 1)
		ra = ra[:toi_da - 1] + [(["... và %d dòng nữa" % con] + [""] * (len(cot) - 1), "phu")]
	return cot, ra


def la_so(chu):
	"""THUẦN: ô có phải con số không (căn phải)."""
	t = str(chu or "").strip().replace(".", "").replace(",", "").lstrip("-+")
	return bool(t) and t.isdigit()


def do_cot(cot, hang, do_chu, rong=RONG, le=LE, dem=28):
	"""THUẦN: bề rộng từng cột theo chữ dài nhất (do_chu(chu, dam) trả số điểm ảnh).
	Cột đầu (tên món) nhận phần còn lại; cột số không hẹp hơn tiêu đề của nó.
	Trả list bề rộng, tổng đúng bằng rong - 2*le."""
	tong = rong - 2 * le
	cac = [do_chu(c, True) + dem for c in cot]
	for o, _ in hang:
		for i, x in enumerate(o):
			if i:
				cac[i] = max(cac[i], do_chu(x, False) + dem)
	sau = sum(cac[1:])
	dau = tong - sau
	nho_nhat = int(tong * 0.34)
	if dau < nho_nhat and sau:
		# Cột số quá rộng: co đều các cột số, giữ cột tên tối thiểu 34%.
		he = (tong - nho_nhat) / float(sau)
		cac = [cac[0]] + [max(40, int(w * he)) for w in cac[1:]]
		dau = tong - sum(cac[1:])
	return [dau] + cac[1:]


def cot_so(cot, hang):
	"""THUẦN: chỉ số các cột (trừ cột đầu) mà mọi ô có chữ đều là số; căn phải cả tiêu đề."""
	ra = set()
	for i in range(1, len(cot)):
		o = [h[0][i] for h in hang if h[1] != "phu" and str(h[0][i]).strip()]
		if o and all(la_so(x) for x in o):
			ra.add(i)
	return ra


def cat_chu(chu, rong, do_chu, dam=False):
	"""THUẦN: cắt chữ cho vừa rong điểm ảnh, thêm dấu … khi phải cắt."""
	chu = str(chu or "")
	if do_chu(chu, dam) <= rong:
		return chu
	while chu and do_chu(chu + "…", dam) > rong:
		chu = chu[:-1]
	return chu.rstrip() + "…"


def _phong():
	goc = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
	return os.path.join(goc, "VagabondSans-Regular.ttf"), os.path.join(goc, "VagabondSans-Bold.ttf")


def ve_bang(tieu_de, phu_de, cot, hang, chu_thich=""):
	"""Vẽ bảng, trả bytes PNG. Ném lỗi nếu thiếu Pillow hoặc phông: nơi gọi gửi tin chữ."""
	from io import BytesIO

	from PIL import Image, ImageDraw, ImageFont

	thuong, dam = _phong()
	f_td = ImageFont.truetype(dam, CO_TIEU_DE)
	f_phu = ImageFont.truetype(thuong, CO_PHU)
	f_chu = ImageFont.truetype(thuong, CO_CHU)
	f_dam = ImageFont.truetype(dam, CO_CHU)

	def do_chu(chu, d=False):
		return int((f_dam if d else f_chu).getlength(str(chu)))

	cot, hang = chuan_bang(cot, hang)
	rong_cot = do_cot(cot, hang, do_chu)
	phai = cot_so(cot, hang)
	cao = LE + CO_TIEU_DE + 14 + (CO_PHU + 18 if phu_de else 0) + 12 + CAO_DONG * (len(hang) + 1) \
		+ (CO_PHU + 30 if chu_thich else 0) + LE
	anh = Image.new("RGB", (RONG, cao), MAU_NEN)
	v = ImageDraw.Draw(anh)
	y = LE
	v.text((LE, y), cat_chu(tieu_de, RONG - 2 * LE, lambda c, d: int(f_td.getlength(c))), font=f_td, fill=MAU_CHU)
	y += CO_TIEU_DE + 14
	if phu_de:
		v.text((LE, y), cat_chu(phu_de, RONG - 2 * LE, lambda c, d: int(f_phu.getlength(c))), font=f_phu, fill=MAU_PHU)
		y += CO_PHU + 18
	y += 12

	def dong(o, y, nen, font, mau_o=None):
		if nen:
			v.rectangle([LE, y, RONG - LE, y + CAO_DONG], fill=nen)
		x = LE
		for i, (chu, w) in enumerate(zip(o, rong_cot)):
			chu = cat_chu(chu, w - 20, lambda c, d: int(font.getlength(c)))
			mau = (mau_o or {}).get(i, MAU_CHU)
			ty = y + (CAO_DONG - CO_CHU) // 2 - 3
			if i in phai or (i and la_so(chu)):
				v.text((x + w - 12 - font.getlength(chu), ty), chu, font=font, fill=mau)
			else:
				v.text((x + 12, ty), chu, font=font, fill=mau)
			x += w
		v.line([LE, y + CAO_DONG, RONG - LE, y + CAO_DONG], fill=MAU_KE, width=1)

	dong(cot, y, MAU_DAU_BANG, f_dam)
	y += CAO_DONG
	for k, (o, nhan) in enumerate(hang):
		font = f_dam if nhan == "dam" else f_chu
		mau = None
		if nhan == "do":
			mau = {i: MAU_DO for i in range(len(o))}
		elif nhan in ("phu", "xam"):
			mau = {i: MAU_PHU for i in range(len(o))}
		elif nhan == "xanh":
			mau = {i: MAU_XANH for i in range(len(o))}
		dong(o, y, MAU_SOC if k % 2 else None, font, mau)
		y += CAO_DONG
	if chu_thich:
		v.text((LE, y + 16), cat_chu(chu_thich, RONG - 2 * LE, lambda c, d: int(f_phu.getlength(c))),
			font=f_phu, fill=MAU_PHU)
	ra = BytesIO()
	anh.save(ra, format="PNG", optimize=True)
	return ra.getvalue()


# ---------------------------------------------- v653: lưới ảnh bánh và số lượng

COT_LUOI = 3
O_LUOI = 312
CAO_CHU_LUOI = 84
TOI_DA_O = 30


def xep_luoi(o, toi_da=TOI_DA_O):
	"""THUẦN: các ô cần vẽ và số ô còn lại không vẽ (quá toi_da). Mỗi ô {ten, so, anh}."""
	o = list(o or [])
	return o[:toi_da], max(0, len(o) - toi_da)


def chia_hai_dong(chu, rong, do_chu):
	"""THUẦN: tên bánh thành tối đa hai dòng vừa `rong`, ngắt theo từ; dòng hai còn
	dài thì cắt có dấu …"""
	tu = str(chu or "").split()
	d1 = ""
	while tu and do_chu((d1 + " " + tu[0]).strip()) <= rong:
		d1 = (d1 + " " + tu.pop(0)).strip()
	if not d1 and tu:
		return [cat_chu(" ".join(tu), rong, lambda c, d: do_chu(c))]
	if not tu:
		return [d1]
	return [d1, cat_chu(" ".join(tu), rong, lambda c, d: do_chu(c))]


def ve_luoi(tieu_de, phu_de, o, anh_cua=None, chu_thich=""):
	"""Vẽ lưới ảnh bánh: mỗi ô một ảnh vuông, tên bánh hai dòng, số lượng to.
	anh_cua(url) trả ảnh PIL hoặc None (tải hỏng thì ô xám có chữ "Chưa có ảnh").
	Trả bytes PNG; ném lỗi nếu thiếu Pillow hoặc phông (nơi gọi gửi tin chữ)."""
	from io import BytesIO

	from PIL import Image, ImageDraw, ImageFont

	thuong, dam = _phong()
	f_td = ImageFont.truetype(dam, CO_TIEU_DE)
	f_phu = ImageFont.truetype(thuong, CO_PHU)
	f_ten = ImageFont.truetype(dam, 24)
	f_so = ImageFont.truetype(dam, 44)
	ve, con = xep_luoi(o)
	khe = (RONG - 2 * LE - COT_LUOI * O_LUOI) // (COT_LUOI - 1)
	so_hang = (len(ve) + COT_LUOI - 1) // COT_LUOI
	cao = LE + CO_TIEU_DE + 14 + (CO_PHU + 18 if phu_de else 0) + 12 + so_hang * (O_LUOI + CAO_CHU_LUOI + 24) \
		+ (CO_PHU + 30 if (chu_thich or con) else 0) + LE
	anh = Image.new("RGB", (RONG, max(cao, 300)), MAU_NEN)
	v = ImageDraw.Draw(anh)
	y = LE
	v.text((LE, y), cat_chu(tieu_de, RONG - 2 * LE, lambda c, d: int(f_td.getlength(c))), font=f_td, fill=MAU_CHU)
	y += CO_TIEU_DE + 14
	if phu_de:
		v.text((LE, y), cat_chu(phu_de, RONG - 2 * LE, lambda c, d: int(f_phu.getlength(c))), font=f_phu, fill=MAU_PHU)
		y += CO_PHU + 18
	y += 12
	for i, x in enumerate(ve):
		cot, hang = i % COT_LUOI, i // COT_LUOI
		x0 = LE + cot * (O_LUOI + khe)
		y0 = y + hang * (O_LUOI + CAO_CHU_LUOI + 24)
		hinh = None
		try:
			hinh = anh_cua(x.get("anh")) if (anh_cua and x.get("anh")) else None
		except Exception:
			hinh = None
		if hinh is not None:
			w, h = hinh.size
			c = min(w, h)
			hinh = hinh.convert("RGB").crop(((w - c) // 2, (h - c) // 2, (w - c) // 2 + c, (h - c) // 2 + c)).resize((O_LUOI, O_LUOI))
			anh.paste(hinh, (x0, y0))
		else:
			v.rectangle([x0, y0, x0 + O_LUOI, y0 + O_LUOI], fill=MAU_SOC, outline=MAU_KE)
			v.text((x0 + 20, y0 + O_LUOI // 2 - 14), "Chưa có ảnh", font=f_phu, fill=MAU_PHU)
		# Số lượng nổi trên góc ảnh: nhìn một giây thấy còn bao nhiêu.
		so = str(x.get("so"))
		w_so = int(f_so.getlength(so)) + 28
		v.rounded_rectangle([x0 + O_LUOI - w_so - 10, y0 + 10, x0 + O_LUOI - 10, y0 + 70], radius=14, fill=MAU_XANH)
		v.text((x0 + O_LUOI - w_so + 4, y0 + 13), so, font=f_so, fill=MAU_NEN)
		for k, dong in enumerate(chia_hai_dong(x.get("ten"), O_LUOI, lambda c: int(f_ten.getlength(c)))):
			v.text((x0, y0 + O_LUOI + 10 + k * 34), dong, font=f_ten, fill=MAU_CHU)
	if chu_thich or con:
		y_ct = y + so_hang * (O_LUOI + CAO_CHU_LUOI + 24) + 8
		ct = (chu_thich + ("  " if chu_thich and con else "") + ("... và %d loại nữa trong danh sách chữ." % con if con else ""))
		v.text((LE, y_ct), cat_chu(ct, RONG - 2 * LE, lambda c, d: int(f_phu.getlength(c))), font=f_phu, fill=MAU_PHU)
	ra = BytesIO()
	anh.save(ra, format="PNG", optimize=True)
	return ra.getvalue()


def tai_anh(url, toi_da=3 * 1024 * 1024):
	"""Tải ảnh bánh (Pancake, web) cho ô lưới; hỏng hay quá nặng thì None."""
	from io import BytesIO

	try:
		import requests
		from PIL import Image

		r = requests.get(str(url), timeout=5, stream=True)
		if r.status_code != 200:
			return None
		b = r.raw.read(toi_da + 1, decode_content=True)
		if len(b) > toi_da:
			return None
		return Image.open(BytesIO(b))
	except Exception:
		return None


def anh_luoi(nhom, tieu_de, phu_de, o, chu_thich=""):
	"""Vẽ lưới ảnh bánh và lưu; trả đường dẫn hoặc None (đã ghi Error Log)."""
	import frappe

	try:
		return luu_anh(ve_luoi(tieu_de, phu_de, o, tai_anh, chu_thich), nhom)
	except Exception as e:
		from vagabond.loi_csdl import chet_giao_dich

		if chet_giao_dich(e):
			raise
		frappe.log_error(frappe.get_traceback(), "anh_bang: chua ve duoc luoi %s" % nhom)
		return None


def ten_tep(nhom):
	"""THUẦN (gần): tên tệp ảnh khó đoán, 24 ký tự ngẫu nhiên, có nhóm để dọn theo tiền tố."""
	nhom = "".join(c for c in str(nhom or "bang").lower() if c.isalnum() or c == "-")[:24] or "bang"
	return "%s%s-%s.png" % (TIEN_TO_TEP, nhom, secrets.token_hex(12))


def luu_anh(png, nhom):
	"""Lưu PNG thành File công khai, trả đường dẫn đầy đủ để Zalo tải. Không gắn chứng từ
	nào; không đi qua bước nén ảnh của Frappe (giữ nguyên byte)."""
	import frappe

	f = frappe.get_doc({"doctype": "File", "file_name": ten_tep(nhom), "content": png, "is_private": 0,
		"folder": "Home"})
	f.flags.ignore_permissions = True
	f.insert(ignore_permissions=True)
	return frappe.utils.get_url(f.file_url)


def anh_bang(nhom, tieu_de, phu_de, cot, hang, chu_thich=""):
	"""Vẽ và lưu; trả đường dẫn, hoặc None khi vẽ hay lưu hỏng (đã ghi Error Log).
	Lỗi làm chết giao dịch thì vẫn ném lên như mọi chỗ khác."""
	import frappe

	try:
		return luu_anh(ve_bang(tieu_de, phu_de, cot, hang, chu_thich), nhom)
	except Exception as e:
		from vagabond.loi_csdl import chet_giao_dich

		if chet_giao_dich(e):
			raise
		frappe.log_error(frappe.get_traceback(), "anh_bang: chua ve duoc anh %s" % nhom)
		return None


def don_anh_cu():
	"""Lịch 03:10: xoá ảnh bảng Zalo cũ hơn SO_NGAY_GIU ngày (chỉ tệp do máy sinh, đúng tiền tố,
	công khai, không gắn chứng từ). Zalo đã tải ảnh lúc gửi nên tin trong nhóm không mất."""
	import frappe
	from frappe.utils import add_days, now_datetime

	han = add_days(now_datetime(), -SO_NGAY_GIU)
	ds = frappe.get_all("File", filters={"file_name": ["like", TIEN_TO_TEP + "%"], "is_private": 0,
		"attached_to_doctype": ["is", "not set"], "creation": ["<", han]}, pluck="name", limit_page_length=500)
	for ten in ds:
		try:
			frappe.delete_doc("File", ten, ignore_permissions=True, force=1)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "anh_bang: chua xoa duoc anh cu")
	if ds:
		frappe.db.commit()
	return len(ds)
