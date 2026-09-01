# -*- coding: utf-8 -*-
"""Cổng vào duy nhất cho MỌI nút tải tệp lên trong app.

Anh Việt 01/09/2026, khi xem màn Đề nghị chi trên điện thoại: *"bị thiếu
phần tải lên tệp đính kèm để tải hình ảnh của chứng từ đi kèm và hàng hoá đã
mua (cho đính kèm nhiều file, hiện dạng thumbnail, tự nén file nhỏ để đỡ tốn
database,...) những cái này là cái em phải ghi vào backend mỗi khi dựng màn
nào có nút tải tệp lên"*.

VÌ SAO PHẢI CÓ MỘT CỔNG CHUNG, KHÔNG PHẢI MỖI MÀN MỘT KIỂU

Trước tệp này, sáu màn có nút tải tệp và mỗi màn tự chép lại một đoạn nén ảnh
riêng, tự gọi thẳng `upload_file` theo một cách riêng. Hệ quả:

- Mỗi nơi một mức nén, có nơi không nén gì cả. Ảnh điện thoại giờ 4 tới 8 MB
  một tấm, chụp cọc tiền ba tấm là 24 MB nằm trong cơ sở dữ liệu, mà nhìn
  trên màn hình 400px thì không hơn tấm 200 KB một chút nào.
- Có nơi để tệp ở dạng công khai, tức là ai có đường dẫn cũng xem được. Ảnh
  bill có tên khách, có số tiền, có chữ ký.
- Không nơi nào hỏi đủ ba câu trước khi gỡ tệp, mà đó chính là bài học đã
  ghi ở `khung/kiem_thu/thu_don_rac_tep.py`.

Nay mọi màn đi qua đây. Thêm màn mới thì gọi lại ba hàm dưới, không chép.

BA CÂU HỎI BẮT BUỘC TRƯỚC KHI GỠ MỘT TỆP, giữ nguyên từ bài học 24/08/2026:

  1. Tệp này thuộc CHỨNG TỪ nào    -> attached_to_doctype + attached_to_name
  2. Tệp này nằm ở Ô nào           -> attached_to_field
  3. Còn AI KHÁC đang dùng tệp này -> đếm các dòng File cùng file_url

THỨ TỰ ĐỜI CỦA MỘT TỆP

  nap_tam()   người lập chọn tệp lúc chứng từ CHƯA có mã, tệp nằm treo và
              chỉ mình người đó thấy
  gan_vao()   chứng từ được lập xong, tệp mới được buộc vào chứng từ
  go_ra()     người lập đổi ý, gỡ tệp còn treo
  don_rac()   nhịp đêm, xoá tệp treo quá lâu mà không ai buộc vào đâu

Tệp đã buộc vào chứng từ thì nhịp đêm KHÔNG bao giờ đụng tới.
"""

import json
import os
import re

# ------------------------------------------------------------ phần thuần
# Phần trên mốc này KHÔNG chạm Frappe, để kiểm thử được mà không cần site.

# Đuôi tệp cho phép. Cố ý hẹp: đây là chỗ nhận chứng từ, không phải ổ chứa
# tệp. Mở rộng cho .zip hay .exe là mở một đường đưa tệp lạ vào máy chủ.
DUOI_ANH = (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".gif", ".bmp")
DUOI_KHAC = (".pdf",)
DUOI_CHO = DUOI_ANH + DUOI_KHAC

# Trần một tệp. Ảnh đã nén ở máy người dùng thường dưới 400 KB; 15 MB là chỗ
# thoáng cho tờ PDF nhiều trang, đồng thời chặn được người lỡ chọn video.
CAP_MOT_TEP = 15 * 1024 * 1024
# Trần số tệp một ô. Mười hai tấm là quá đủ cho một khoản chi.
CAP_SO_TEP = 12
# Tệp treo quá số ngày này mà chưa buộc vào chứng từ nào thì nhịp đêm dọn.
NGAY_GIU_TEP_TREO = 3

# Dấu nhận mặt tệp do cổng này nhận, đặt vào đầu tên tệp lưu trên máy chủ.
# Nhịp dọn rác CHỈ đụng tệp mang dấu này, để không bao giờ chạm vào tệp do
# người khác hoặc do Frappe tự sinh.
DAU_TEP = "vgbtep"


def duoi_tep(ten):
	"""Đuôi tệp viết thường, có dấu chấm. Không có đuôi thì trả về rỗng."""
	ten = (ten or "").strip()
	if "." not in ten:
		return ""
	d = "." + ten.rsplit(".", 1)[1].lower()
	# Đuôi dài quá năm chữ thì gần như chắc chắn không phải đuôi mà là một
	# dấu chấm nằm giữa tên tệp.
	return d if len(d) <= 6 else ""


def la_anh(ten):
	return duoi_tep(ten) in DUOI_ANH


def nhan_duoi(ten):
	"""Chữ in trên ô vuông khi tệp không phải ảnh. Không biết thì ghi TỆP."""
	d = duoi_tep(ten)
	return d[1:].upper() if d else "TỆP"


def duoc_nhan(ten):
	return duoi_tep(ten) in DUOI_CHO


def loi_tu_choi(ten, so_byte=None):
	"""Câu từ chối cho một tệp, rỗng nghĩa là nhận được.

	Nói rõ nhận những đuôi nào chứ không chỉ nói "tệp không hợp lệ": người
	cầm điện thoại không đoán được mình sai ở đâu.
	"""
	if not (ten or "").strip():
		return "Tệp không có tên."
	if not duoc_nhan(ten):
		return (
			"Tệp %s không nhận được. Chỉ nhận ảnh (jpg, png, webp, heic) và "
			"tệp PDF." % ten
		)
	if so_byte is not None and so_byte > CAP_MOT_TEP:
		return (
			"Tệp %s nặng %s MB, quá mức %s MB cho một tệp."
			% (ten, round(so_byte / 1048576.0, 1), CAP_MOT_TEP // 1048576)
		)
	return ""


def doc_ds(gt):
	"""Đọc danh sách đường dẫn tệp từ một ô Small Text.

	Ô có thể đang giữ chuỗi JSON, đang giữ danh sách thật, hoặc đang trống.
	Đọc sai kiểu ở đây là mất sạch tệp của một dòng mà không ai báo.
	"""
	if not gt:
		return []
	if isinstance(gt, (list, tuple)):
		ds = list(gt)
	else:
		try:
			ds = json.loads(gt)
		except Exception:
			return []
	if not isinstance(ds, list):
		return []
	ra = []
	for x in ds:
		if isinstance(x, dict):
			x = x.get("url") or x.get("file_url") or ""
		x = str(x or "").strip()
		if x and x not in ra:
			ra.append(x)
	return ra


def ghi_ds(ds):
	"""Ngược lại của doc_ds. Rỗng thì trả None để ô trong cơ sở dữ liệu trống."""
	ds = [str(x).strip() for x in (ds or []) if str(x or "").strip()]
	kd = []
	for x in ds:
		if x not in kd:
			kd.append(x)
	return json.dumps(kd, ensure_ascii=False) if kd else None


def ten_luu(ten_goc, ma_phien=""):
	"""Tên tệp lưu trên máy chủ: có dấu nhận mặt, bỏ ký tự lạ.

	Giữ lại đuôi gốc để trình duyệt mở đúng ứng dụng. Bỏ dấu tiếng Việt và
	khoảng trắng: đường dẫn tệp đi qua nhiều tầng, có tầng không chịu.
	"""
	d = duoi_tep(ten_goc) or ".jpg"
	goc = (ten_goc or "")[: -len(d)] if d and (ten_goc or "").lower().endswith(d) else (ten_goc or "")
	goc = re.sub(r"[^A-Za-z0-9]+", "-", goc).strip("-")[:40] or "tep"
	ma_phien = re.sub(r"[^A-Za-z0-9]+", "", str(ma_phien or ""))[:24]
	return "%s-%s%s%s" % (DAU_TEP, goc, ("-" + ma_phien) if ma_phien else "", d)


def la_tep_cua_cong(ten_luu_tren_may):
	"""Tệp này có phải do cổng này nhận vào không.

	Nhịp dọn rác chỉ được đụng tệp trả về True. Đây là hàng rào cuối cùng
	giữa nhịp dọn rác và chữ ký khách, ảnh bằng chứng, uỷ nhiệm chi của kế
	toán - những thứ không sinh ra từ đây.
	"""
	ten = os.path.basename(str(ten_luu_tren_may or ""))
	return ten.startswith(DAU_TEP + "-")


def gom_hien(ds_url, ten_theo_url=None):
	"""Đổi danh sách đường dẫn thành danh sách ô để màn hình vẽ thumbnail.

	Mỗi ô: url, ten, anh (0/1), duoi. Màn hình không phải đoán gì thêm.
	"""
	ten_theo_url = ten_theo_url or {}
	ra = []
	for u in doc_ds(ds_url):
		ten = ten_theo_url.get(u) or os.path.basename(u.split("?")[0])
		ra.append({
			"url": u,
			"ten": ten,
			"anh": 1 if la_anh(ten) else 0,
			"duoi": nhan_duoi(ten),
		})
	return ra


# ------------------------------------------------------- phần cần Frappe

import frappe  # noqa: E402
from frappe.utils import cint, now_datetime  # noqa: E402


def _vai():
	return set(frappe.get_roles())


def _tep_theo_url(ds_url):
	"""Bảng tra tên gốc theo đường dẫn, đọc một lần cho cả danh sách."""
	ds_url = [u for u in (ds_url or []) if u]
	if not ds_url:
		return {}
	ra = {}
	for r in frappe.get_all(
		"File",
		filters={"file_url": ["in", ds_url]},
		fields=["file_url", "file_name"],
		limit_page_length=0,
	):
		ra.setdefault(r.file_url, r.file_name)
	return ra


def hien(ds_url):
	"""Danh sách ô thumbnail cho màn hình, đã tra tên thật của từng tệp."""
	ds = doc_ds(ds_url)
	return gom_hien(ds, _tep_theo_url(ds))


@frappe.whitelist()
def nap_tam(ten=None, noi_dung=None, phien=None):
	"""Nhận MỘT tệp lúc chứng từ chưa có mã. Tệp nằm treo, riêng tư.

	Màn hình gửi lên nội dung đã nén dạng base64. Nén ở máy người dùng chứ
	không ở máy chủ là có chủ đích: nén ở máy chủ thì tấm ảnh 8 MB vẫn phải
	đi hết đường mạng 4G của bạn nhân viên đứng trong bếp.

	Trả về đủ để màn hình vẽ ngay một ô thumbnail, không phải hỏi lại.
	"""
	ten = (ten or "").strip()
	loi = loi_tu_choi(ten)
	if loi:
		frappe.throw(loi)

	import base64

	raw = noi_dung or ""
	if "," in raw[:64] and raw[:5] == "data:":
		raw = raw.split(",", 1)[1]
	try:
		byte = base64.b64decode(raw)
	except Exception:
		frappe.throw("Không đọc được nội dung tệp %s, vui lòng chọn lại." % ten)
	if not byte:
		frappe.throw("Tệp %s rỗng." % ten)
	loi = loi_tu_choi(ten, len(byte))
	if loi:
		frappe.throw(loi)

	doc = frappe.get_doc({
		"doctype": "File",
		"file_name": ten_luu(ten, phien),
		"is_private": 1,
		"content": byte,
		"decode": False,
	})
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	return {
		"ok": 1,
		"url": doc.file_url,
		"ten": ten,
		"anh": 1 if la_anh(ten) else 0,
		"duoi": nhan_duoi(ten),
		"byte": len(byte),
	}


@frappe.whitelist()
def go_ra(url=None):
	"""Người lập gỡ một tệp CÒN TREO ra khỏi màn hình đang soạn.

	Chỉ gỡ được tệp treo và của chính mình. Tệp đã buộc vào chứng từ thì
	không gỡ ở đây: gỡ chứng cứ khỏi một phiếu đã nộp là việc khác, phải đi
	qua màn của phiếu đó.
	"""
	url = (url or "").strip()
	if not url:
		return {"ok": 0}
	for r in frappe.get_all(
		"File",
		filters={"file_url": url},
		fields=["name", "owner", "attached_to_doctype", "attached_to_name", "file_name"],
		limit_page_length=0,
	):
		if r.attached_to_doctype or r.attached_to_name:
			frappe.throw("Tệp này đã gắn vào chứng từ rồi, không gỡ ở đây được.")
		if r.owner != frappe.session.user and "System Manager" not in _vai():
			frappe.throw("Chỉ người tải tệp lên mới gỡ được tệp đó.")
		if not la_tep_cua_cong(r.file_name):
			frappe.throw("Tệp này không do màn tải tệp sinh ra, không gỡ ở đây được.")
		frappe.delete_doc("File", r.name, ignore_permissions=True, force=True)
	return {"ok": 1}


def gan_vao(doctype, ten_chung_tu, o="tep_dinh_kem", ds_url=None):
	"""Buộc các tệp còn treo vào một chứng từ đã có mã.

	KHÔNG phải hàm mở ra ngoài: chỉ mô đun nghiệp vụ gọi, ngay sau khi lập
	xong chứng từ. Mở ra ngoài thì bất cứ ai cũng buộc được tệp bất kỳ vào
	chứng từ bất kỳ.

	Trả về danh sách đường dẫn đã buộc thành công, theo đúng thứ tự người
	lập đã chọn.
	"""
	ds = doc_ds(ds_url)
	if not ds:
		return []
	if len(ds) > CAP_SO_TEP:
		frappe.throw("Một ô chỉ đính tối đa %s tệp." % CAP_SO_TEP)

	xong = []
	for u in ds:
		r = frappe.db.get_value(
			"File", {"file_url": u},
			["name", "owner", "file_name", "attached_to_doctype", "attached_to_name"],
			as_dict=True,
		)
		if not r:
			continue
		# Tệp đã thuộc về đúng chứng từ này rồi thì coi như xong, không làm
		# lại. Lưu phiếu lần hai không được sinh ra một bản sao.
		if r.attached_to_doctype == doctype and r.attached_to_name == ten_chung_tu:
			xong.append(u)
			continue
		if r.attached_to_doctype or r.attached_to_name:
			# Tệp của chứng từ khác. Không cướp, cũng không im lặng bỏ qua.
			frappe.throw(
				"Tệp %s đang thuộc chứng từ %s rồi." % (r.file_name, r.attached_to_name)
			)
		if r.owner != frappe.session.user and "System Manager" not in _vai():
			frappe.throw("Chỉ người tải tệp lên mới gắn tệp đó vào chứng từ được.")
		frappe.db.set_value("File", r.name, {
			"attached_to_doctype": doctype,
			"attached_to_name": ten_chung_tu,
			"attached_to_field": o,
			"is_private": 1,
		}, update_modified=False)
		xong.append(u)
	return xong


def don_rac(so_ngay=None):
	"""Nhịp đêm: xoá tệp do cổng này nhận mà treo quá lâu không ai dùng.

	Ba câu hỏi của bài học 24/08/2026 đều phải trả lời được thì mới xoá:
	tệp chưa thuộc chứng từ nào, chưa nằm ở ô nào, và không có dòng File nào
	khác cùng đường dẫn. Thiếu một câu là đủ để xoá nhầm.
	"""
	from frappe.utils import add_days, nowdate

	moc = add_days(nowdate(), -cint(so_ngay or NGAY_GIU_TEP_TREO))
	da_xoa = 0
	for r in frappe.get_all(
		"File",
		filters={
			"attached_to_doctype": ["in", ["", None]],
			"attached_to_name": ["in", ["", None]],
			"creation": ["<", moc],
		},
		fields=["name", "file_name", "file_url"],
		limit_page_length=500,
	):
		if not la_tep_cua_cong(r.file_name):
			continue
		# Câu 3: còn dòng File nào khác trỏ cùng đường dẫn thì để yên.
		if frappe.db.count("File", {"file_url": r.file_url}) > 1:
			continue
		try:
			frappe.delete_doc("File", r.name, ignore_permissions=True, force=True)
			da_xoa += 1
		except Exception:
			frappe.log_error(frappe.get_traceback(), "tep_dinh_kem: don rac loi")
	if da_xoa:
		frappe.db.commit()
	return {"da_xoa": da_xoa, "moc": str(moc), "luc": str(now_datetime())}


@frappe.whitelist()
def cai_dat():
	"""Luật của cổng, gửi xuống màn hình để hai bên không nói khác nhau."""
	return {
		"cap_mot_tep": CAP_MOT_TEP,
		"cap_so_tep": CAP_SO_TEP,
		"duoi_cho": list(DUOI_CHO),
		"duoi_anh": list(DUOI_ANH),
		"canh_dai_nen": 1600,
		"chat_luong_nen": 0.72,
	}
