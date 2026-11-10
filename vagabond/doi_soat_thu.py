# -*- coding: utf-8 -*-
"""v641: đối soát tự động qua hộp thư doisoat@ (anh Việt duyệt 06/11/2026).

Anh Việt 06/11/2026: "anh không muốn tải thủ công lên erp vì có khả năng bị gian
lận". Anh duyệt 8 ảnh mẫu và 10 tin Zalo, chốt hộp thư nhận là
doisoat@thevagabondpatisserie.com trên Mắt Bão, và "tệp tải tay có duyệt, đưa vào
mục việc cần làm của giám đốc là được để anh duyệt, nhưng vẫn ưu tiên luồng tự
động trên hết".

Luồng một thư:
  bộ lọc Roundcube gửi BẢN SAO nguyên vẹn -> hộp doisoat@ -> máy chủ ERP đọc mỗi
  15 phút qua IMAP (chỉ đọc, không đánh dấu, không xoá) -> lưu nguyên bản .eml chỉ
  đọc -> kiểm chữ ký số DKIM (doi_soat_dkim) -> đối tác đúng tên miền và chữ ký
  hợp lệ thì đọc tệp đính kèm qua ĐÚNG MỘT lối doi_soat_vendor._nhan_byte như tải
  tay -> khớp tiền, nối chứng từ -> kế toán xác nhận.

Sáu bước trên app (buoc_nguon) chính là sáu bước của luồng: 1 Nhận thư, 2 Xác
thực, 3 Đọc tệp, 4 Khớp tiền, 5 Nối chứng từ, 6 Kế toán xác nhận.

Đường vào của một nguồn (trường duong_vao):
  Từ thư     thư có chữ ký số đúng tên miền đối tác;
  Chờ duyệt  tải tay, hoặc thư đối tác không chữ ký mà Cài đặt cho nhận có duyệt;
  Đã duyệt   giám đốc đã duyệt (người tải không tự duyệt được);
  Từ chối    giám đốc từ chối: dòng thôi tính, giữ để tra;
  (trống)    nguồn tải tay trước bản này: giữ nguyên, không sửa, gọi "Trước khi có thư".
Không có gì ở đây tạo chứng từ kế toán (giữ đúng luật của doi_soat_vendor).

Phần THUẦN đứng trước, phần chạm Frappe đứng sau.
"""

import base64
import hashlib
import json
import re
from datetime import date, datetime, timedelta

DT_THU = "Vagabond Doi Soat Thu"
DT_NGUON = "Vagabond Doi Soat Nguon"
CAI_DAT = "Vagabond Settings"
KENH = "Hộp thư đối soát"
KENH_TAY = ("Tải tay", "Email")
DV_THU, DV_CHO, DV_DA, DV_TU_CHOI = "Từ thư", "Chờ duyệt", "Đã duyệt", "Từ chối"
KQ_XAC_THUC, KQ_CHO, KQ_CHAN, KQ_KHONG_TEP = "Đã xác thực", "Chờ duyệt", "Bị chặn", "Không có tệp"
KQ_LOI = "Lỗi xử lý"
# Codex #544 F1: một thư xử lý lỗi thì giữ mốc ở trước nó để lượt sau thử lại;
# lỗi tới lần thứ SO_THU_LAI thì ghi sổ thư "Lỗi xử lý" (giữ bản gốc) rồi đi tiếp,
# để một thư hỏng không chặn mãi các thư sau.
SO_THU_LAI = 3
# Codex #544 vòng 2: tra khoá chữ ký lỗi tạm (DNS, mạng) thì thử lại tới ngần
# này giờ tính từ lần lỗi đầu, không tính theo số lần (cả hộp thư cùng chờ vì
# mọi thư đều cần tra khoá). Quá hạn mới ghi "Lỗi xử lý" (đọc lại được bằng tay).
GIO_THU_LAI_DNS = 24
DUOI = (".csv", ".txt", ".xlsx", ".xlsm", ".xls", ".pdf", ".zip")
TOI_DA_MOI_LUOT = 40
TOI_DA_BYTE_THU = 30 * 1024 * 1024
HOP = "doisoat@"
DUONG_APP = "/doi-soat-nha-cung-cap"
NGUONG_LECH_MAC_DINH = 1000.0
NGUONG_PHI_MAC_DINH = 0.1
BIEU_NOI_DIA_MAC_DINH = 1.44
SO_LOI_BAO = 2
# v643: hộp thư nội bộ được chuyển tiếp mặc định (anh Việt 07/11/2026 "đồng ý luôn
# thư forward tự động"). Gieo vào Cài đặt một lần; anh sửa trên trang Cài đặt.
NOI_BO_MAC_DINH = ("account@thevagabondpatisserie.com", "thevagabondbakery@gmail.com")
NGUON_NOI_BO = "Chuyển tiếp nội bộ"

# Người gửi tin cậy mặc định (tên hiện, tên miền, bắt buộc chữ ký). Gieo vào bảng
# Cài đặt một lần khi bảng còn trống; anh sửa trên app.
NGUOI_GUI_MAC_DINH = (
	("OnePay", "onepay.vn", 1),
	("Payoo", "payoo.com.vn", 1),
	("Shinhan (POS và thẻ tín dụng)", "shinhan.com.vn", 1),
	("Grab", "grab.com, grabtaxi.com", 1),
	("ShopeeFood", "shopeefood.vn, shopee.vn", 1),
	("GreenSM (Xanh SM)", "greensm.com, xanhsm.com", 1),
	("Be", "be.com.vn", 1),
	("Meta (biên lai quảng cáo)", "facebookmail.com, facebook.com", 1),
)
TAN_SUAT = ("Hằng ngày", "Hằng tháng", "Không theo lịch")
# Lịch thư dự kiến mặc định: (nguồn như tên trên báo cáo, tần suất, hạn giờ,
# hạn ngày trong tháng, chỉ ngày làm việc).
LICH_MAC_DINH = (
	("OnePay", "Hằng ngày", 12, 0, 1),
	("Shinhan POS", "Hằng ngày", 12, 0, 1),
	("Payoo", "Hằng ngày", 12, 0, 1),
	("GrabFood", "Hằng ngày", 12, 0, 0),
	("ShopeeFood", "Hằng ngày", 12, 0, 0),
	("Thẻ tín dụng Shinhan", "Hằng tháng", 0, 5, 0),
	("Grab for Business", "Hằng tháng", 0, 5, 0),
	("Xanh SM doanh nghiệp", "Hằng tháng", 0, 5, 0),
	("Be for Business", "Hằng tháng", 0, 5, 0),
)

TEN_BUOC = ("Nhận thư", "Xác thực", "Đọc tệp", "Khớp tiền", "Nối chứng từ", "Kế toán xác nhận")
DUONG = (
	("thu", "Từ thư ✓"), ("cho_duyet", "Chờ duyệt"), ("da_duyet", "Tải tay đã duyệt"),
	("tu_choi", "Bị từ chối"), ("cu", "Trước khi có thư"),
)


# ------------------------------------------------------------ THUẦN: tên miền

def xu_ly_loi(lan, dns_tu=None, bay=None):
	"""THUẦN. Thư xử lý lỗi lần thứ `lan`: "thu_lai" (giữ mốc, lượt sau đọc lại)
	hay "ghi_loi" (ghi sổ thư lỗi, đi tiếp).

	dns_tu: lỗi là tra khoá chữ ký lỗi tạm, lỗi đầu tiên lúc dns_tu (chuỗi
	"YYYY-MM-DD HH:MM:SS"); thử lại tới GIO_THU_LAI_DNS giờ, không tính số lần."""
	if dns_tu:
		try:
			dau = datetime.strptime(str(dns_tu)[:19], "%Y-%m-%d %H:%M:%S")
			nay = datetime.strptime(str(bay)[:19], "%Y-%m-%d %H:%M:%S")
		except ValueError:
			return "ghi_loi"
		return "thu_lai" if nay - dau < timedelta(hours=GIO_THU_LAI_DNS) else "ghi_loi"
	return "thu_lai" if int(lan or 0) < SO_THU_LAI else "ghi_loi"


def phai_doc_lai_dns(ket_qua, chu_ky):
	"""THUẦN. Codex #544 vòng 2: thư chưa được nhận là thư có chữ ký đúng mà có
	chữ ký chưa kiểm được vì tra khoá lỗi TẠM thì chưa được kết luận (chặn hay
	chờ duyệt): phải đọc lại khi mạng ổn."""
	return ket_qua != KQ_XAC_THUC and any(c.get("tam") for c in (chu_ky or []))


def danh_hop(may, cong, dia_chi, thu_muc):
	"""THUẦN. Danh tính thư mục đang đọc: máy chủ, cổng, tài khoản, thư mục.
	Codex #544 vòng 3: UIDVALIDITY chỉ có nghĩa TRONG một thư mục của một máy
	chủ; hộp thư khác có thể trùng số. Tên máy chủ, tài khoản không phân biệt
	hoa thường; tên thư mục giữ nguyên (IMAP phân biệt), trừ INBOX."""
	tm = (thu_muc or "").strip() or "INBOX"
	if tm.upper() == "INBOX":
		tm = "INBOX"
	return "%s:%s|%s|%s" % ((may or "").strip().lower().rstrip("."), int(cong or 0) or 993, (dia_chi or "").strip().lower(), tm)


def moc_doc(tt, uv, danh=None):
	"""THUẦN. Mốc đọc (UID cuối, các thư đang thử lại) của thư mục có
	UIDVALIDITY uv. Codex #544 vòng 2: UIDVALIDITY đổi (hộp thư làm lại, chuyển
	máy chủ) thì UID cũ vô nghĩa: mốc về 0, bỏ mọi đếm lỗi cũ; trả thêm
	doi=True để nơi gọi ghi ngay mốc mới TRƯỚC khi đọc thư nào.

	Codex #544 vòng 3: mốc gắn với danh tính thư mục (danh_hop). Quản trị đổi
	máy chủ, tài khoản hay thư mục thì mốc về 0 dù UIDVALIDITY trùng số. Mốc
	cũ chưa ghi danh tính (chưa có) thì nhận danh tính hiện tại, không đọc lại."""
	cung = int(tt.get("uidvalidity") or 0) == int(uv or 0)
	if cung and danh is not None and tt.get("hop") and tt.get("hop") != danh:
		cung = False
	if not cung:
		return dict(uid=0, loi_uid={}, dns_tu={}, doi=True)
	return dict(uid=int(tt.get("uid") or 0), loi_uid=dict(tt.get("loi_uid") or {}), dns_tu=dict(tt.get("dns_tu") or {}),
		doi=False)


def mien_cua(dia_chi):
	"""THUẦN. "OnePay <no-reply@OnePay.vn>" -> "onepay.vn"."""
	s = (dia_chi or "").strip().lower()
	if "<" in s and ">" in s:
		s = s[s.rindex("<") + 1:s.rindex(">")]
	return s.rsplit("@", 1)[-1].strip().rstrip(".") if "@" in s else ""


def tach_mien(s):
	"""THUẦN. "grab.com, Grabtaxi.com; x" -> ["grab.com", "grabtaxi.com", "x"]."""
	return [x.strip().lower().lstrip("@").rstrip(".") for x in re.split(r"[,;\s]+", s or "") if x.strip()]


def thuoc(mien, ds):
	"""THUẦN. mien là ds[i] hoặc tên miền con của ds[i]."""
	mien = (mien or "").lower()
	return bool(mien) and any(mien == x or mien.endswith("." + x) for x in ds if x)


def dong_cua(mien, nguoi_gui):
	"""THUẦN. Dòng người gửi tin cậy ứng với tên miền thư (tên miền dài khớp trước)."""
	cap = [(len(x), d) for d in nguoi_gui for x in d["mien"] if thuoc(mien, [x])]
	return max(cap, key=lambda c: c[0])[1] if cap else None


def tach_dia_chi(s):
	"""THUẦN (v643). Ô Cài đặt nhiều địa chỉ (xuống dòng, dấu phẩy, chấm phẩy,
	có thể kèm tên "Kế toán <a@b>") thành danh sách địa chỉ viết thường."""
	ra = []
	for x in re.split(r"[,;\n]+", s or ""):
		x = x.strip()
		if "<" in x and ">" in x:
			x = x[x.rindex("<") + 1:x.rindex(">")]
		x = x.strip().strip("<>").strip().lower().rstrip(".")
		if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", x) and x not in ra:
			ra.append(x)
	return ra


def _received(tieu_de):
	return [(re.sub(r"\s+", " ", v.replace("\r\n", " ")).strip()) for t, v in tieu_de if t.lower() == "received"]


def qua_may_chu_dang_nhap(tieu_de, dia_chi):
	"""THUẦN (v643). Thư do chính hộp dia_chi gửi qua máy chủ thư của tiệm CÓ
	đăng nhập (SMTP AUTH), như account@ gửi từ Outlook qua Mắt Bão.

	tieu_de: [(tên, giá trị)] theo thứ tự trong thư (chữ thường hay hoa đều được).
	Chỉ tin các ô Received do máy chủ của tiệm thêm: ô TRÊN CÙNG là của máy chủ
	tiệm (người gửi không viết lên trên được), lấy tên máy ở "by". Đi xuống, bỏ
	qua các chặng nội bộ (with LMTP, with local); chặng SMTP ĐẦU TIÊN gặp được
	là lúc thư vào máy chủ tiệm, phải do đúng máy đó nhận và ghi "with esmtpa"
	hoặc "esmtpsa" (có đăng nhập). Ô Received người gửi tự chèn nằm dưới chặng
	đó nên không đổi được kết luận. Thêm: Return-Path phải đúng dia_chi."""
	rec = _received(tieu_de)
	if not rec:
		return False
	m = re.search(r"\bby ([^\s;()]+)", rec[0], re.I)
	if not m:
		return False
	may = m.group(1).lower().rstrip(".")
	rp = [v for t, v in tieu_de if t.lower() == "return-path"]
	if not rp or tach_dia_chi(rp[0]) != [dia_chi.lower()]:
		return False
	for r in rec:
		w = re.search(r"\bwith ([A-Za-z0-9]+)", r, re.I)
		by = re.search(r"\bby ([^\s;()]+)", r, re.I)
		giao = (w.group(1).lower() if w else "")
		if giao in ("lmtp", "local"):
			continue
		return bool(by) and by.group(1).lower().rstrip(".") == may and giao in ("esmtpa", "esmtpsa")
	return False


def quyet_noi_bo(dia_chi, so_from, chu_ky, dang_nhap):
	"""THUẦN (v643). Thư từ hộp thư nội bộ được chuyển tiếp (Cài đặt).

	Nhận ngay (đường Từ thư, không chờ duyệt, anh Việt 07/11/2026) khi thư đúng
	là của hộp đó: có chữ ký số hợp lệ của chính tên miền địa chỉ (Gmail ký
	gmail.com), hoặc gửi qua máy chủ thư của tiệm có đăng nhập. Không có bằng
	chứng nào thì là thư mạo danh hộp nội bộ: chặn và báo Zalo."""
	ra = dict(ket_qua=KQ_CHAN, nguon=NGUON_NOI_BO, ly_do="", ky_boi="", bao_zalo=0, bat_buoc=1, noi_bo=1)
	if so_from != 1:
		ra["ly_do"] = "Thư có %s địa chỉ người gửi; thư hợp lệ chỉ có đúng một." % so_from
		return ra
	mien = mien_cua(dia_chi)
	sau = (" Tệp chuyển tiếp không còn chữ ký gốc của đối tác; máy nhận vì địa chỉ này nằm trong "
		"Hộp thư nội bộ được chuyển tiếp ở Cài đặt, và vẫn đối chiếu tiền về ngân hàng như thư đối tác.")
	dat = [c for c in chu_ky or [] if c.get("dat") and thuoc(c.get("d"), [mien])]
	if dat:
		ra.update(ket_qua=KQ_XAC_THUC, ky_boi=dat[0]["d"],
			ly_do="Thư chuyển tiếp từ hộp nội bộ %s, chữ ký số %s hợp lệ.%s" % (dia_chi, dat[0]["d"], sau))
		return ra
	if dang_nhap:
		ra.update(ket_qua=KQ_XAC_THUC,
			ly_do="Thư chuyển tiếp từ hộp nội bộ %s, không có chữ ký số nhưng gửi qua máy chủ thư của tiệm có "
			"đăng nhập.%s" % (dia_chi, sau))
		return ra
	ra.update(bao_zalo=1, ly_do="Thư ghi người gửi là hộp nội bộ %s nhưng không có chữ ký số của %s và không gửi qua "
		"máy chủ thư của tiệm có đăng nhập: có thể là thư mạo danh." % (dia_chi, mien))
	return ra


def quyet_dinh(mien, so_from, chu_ky, nguoi_gui):
	"""THUẦN. Quyết một thư: nhận, chờ duyệt hay chặn.

	chu_ky: kết quả doi_soat_dkim.kiem_thu ([{d, dat, ly_do}]).
	Nhận khi có MỘT chữ ký hợp lệ mà tên miền ký thuộc danh sách tên miền của
	chính đối tác đó (thư From merchant.grab.com ký d=grab.com là hợp lệ; thư
	From onepay.vn mà chỉ có chữ ký của dịch vụ gửi thư hộ thì không)."""
	ra = dict(ket_qua=KQ_CHAN, nguon="", ly_do="", ky_boi="", bao_zalo=0, bat_buoc=1)
	if so_from != 1:
		ra["ly_do"] = "Thư có %s địa chỉ người gửi; thư hợp lệ chỉ có đúng một." % so_from
		return ra
	d = dong_cua(mien, nguoi_gui)
	if not d:
		ra["ly_do"] = "Người gửi (%s) không nằm trong danh sách đối tác tin cậy ở Cài đặt." % (mien or "không rõ")
		return ra
	ra["nguon"], ra["bat_buoc"] = d["ten"], 1 if d.get("bat_buoc") else 0
	dat = [c for c in chu_ky or [] if c.get("dat") and thuoc(c.get("d"), d["mien"])]
	if dat:
		ra.update(ket_qua=KQ_XAC_THUC, ky_boi=dat[0]["d"], ly_do="Chữ ký số %s hợp lệ." % dat[0]["d"])
		if dat[0].get("ghi_chu"):
			ra["ly_do"] += " " + dat[0]["ghi_chu"]
		return ra
	cua_minh = [c for c in chu_ky or [] if thuoc(c.get("d"), d["mien"])]
	if cua_minh:
		ly = cua_minh[0].get("ly_do") or "Chữ ký số không hợp lệ."
	elif chu_ky:
		ly = "Thư chỉ có chữ ký của %s, không có chữ ký của %s." % (
			", ".join(sorted({c.get("d") or "?" for c in chu_ky})), d["mien"][0])
	else:
		ly = "Thư không có chữ ký số của %s." % d["mien"][0]
	if d.get("bat_buoc"):
		ra.update(ly_do=ly, bao_zalo=1)
	else:
		ra.update(ket_qua=KQ_CHO, ly_do=ly + " Cài đặt cho nhận thư không chữ ký của %s: chờ Giám đốc duyệt." % d["ten"])
	return ra


# ------------------------------------------------------------ THUẦN: đọc thư

def _phan_tep(msg, vao_long=False):
	"""Các phần lá của thư, KHÔNG đi vào thư lồng (message/rfc822): tệp nằm trong
	thư được chuyển tiếp không còn chữ ký của đối tác. v643: thư từ hộp nội bộ
	được chuyển tiếp (vao_long) thì có đi vào, vì Outlook chuyển tiếp dạng đính
	kèm cả thư gốc."""
	if msg.get_content_maintype() == "message":
		if not vao_long:
			return
		for p in (msg.get_payload() if isinstance(msg.get_payload(), list) else [msg.get_payload()]):
			if hasattr(p, "get_content_maintype"):
				yield from _phan_tep(p, vao_long)
		return
	if msg.is_multipart():
		for p in msg.get_payload():
			yield from _phan_tep(p, vao_long)
	else:
		yield msg


def doc_thu(tho, vao_long=False):
	"""THUẦN. Tách những gì cần từ thư gốc (bytes)."""
	import email
	from email import policy
	from email.utils import getaddresses, parsedate_to_datetime

	msg = email.message_from_bytes(tho, policy=policy.default)
	tu = [str(x) for x in (msg.get_all("From") or [])]
	dia = [a for _n, a in getaddresses(tu) if a]
	try:
		gui = parsedate_to_datetime(str(msg.get("Date") or "")).strftime("%Y-%m-%d %H:%M:%S")
	except Exception:
		gui = ""
	tep, chu = [], ""
	for p in _phan_tep(msg, vao_long):
		ten = p.get_filename()
		if ten and ten.lower().endswith(DUOI):
			b = p.get_payload(decode=True) or b""
			if b:
				tep.append((ten.replace("/", "_").replace("\\", "_")[:140], b))
		elif not chu and p.get_content_type() in ("text/plain", "text/html"):
			try:
				chu = p.get_content()
			except Exception:
				chu = ""
	return dict(nguoi_gui=(tu[0] if tu else "")[:140], dia_chi=dia[0] if len(dia) == 1 else "",
		mien=mien_cua(dia[0]) if len(dia) == 1 else "", so_from=len(dia) if len(tu) <= 1 else len(tu),
		tieu_de=" ".join(str(msg.get("Subject") or "").split())[:140], message_id=str(msg.get("Message-ID") or "")[:140],
		gui_luc=gui, than=re.sub(r"<[^>]+>", " ", chu or "")[:5000], tep=tep)


# ------------------------------------------------------------ THUẦN: sáu bước

def duong_vao(n):
	"""THUẦN. Khoá đường vào của một nguồn (xem docstring đầu tệp)."""
	dv, kenh = n.get("duong_vao") or "", n.get("kenh_nhan") or ""
	if dv == DV_CHO:
		return "cho_duyet"
	if dv == DV_TU_CHOI:
		return "tu_choi"
	if kenh == KENH:
		return "thu"
	if dv == DV_DA:
		return "da_duyet"
	return "cu"


def loc_duong(k):
	"""THUẦN. Bộ lọc kiểu Frappe của một chip Đường vào, cùng nghĩa với duong_vao."""
	return {
		"thu": {"kenh_nhan": KENH, "duong_vao": ["in", [DV_THU, DV_DA]]},
		"cho_duyet": {"duong_vao": DV_CHO},
		"da_duyet": {"kenh_nhan": ["in", list(KENH_TAY)], "duong_vao": DV_DA},
		"tu_choi": {"duong_vao": DV_TU_CHOI},
		"cu": {"kenh_nhan": ["in", list(KENH_TAY)], "duong_vao": ["is", "not set"]},
	}.get(k or "", {})


def buoc_nguon(n):
	"""THUẦN. Sáu bước của một nguồn: tt là chuỗi 6 ký tự (x xong, v đang chờ,
	d có sự cố, n chưa tới / chưa áp dụng), hien là bước đang kẹt (1..6, 7 là
	đã khép), ghi là một dòng nói kẹt gì, nhan là ghi chú từng bước."""
	tt, nhan = [], []
	kenh, dv = n.get("kenh_nhan") or "", n.get("duong_vao") or ""
	# 1. Nhận.
	tt.append("x")
	nhan.append("Từ hộp thư đối soát" if kenh == KENH else ("Tải tay" if kenh == "Tải tay" else "Email cũ (chưa xác thực)"))
	# 2. Xác thực.
	if dv == DV_TU_CHOI:
		tt.append("d"), nhan.append("Giám đốc đã từ chối" + (": " + n["ly_do_duyet"] if n.get("ly_do_duyet") else ""))
	elif dv == DV_CHO:
		tt.append("v"), nhan.append("Thư không chữ ký, chờ Giám đốc duyệt" if kenh == KENH else "Tải tay, chờ Giám đốc duyệt")
	elif dv == DV_DA:
		tt.append("x"), nhan.append("Giám đốc đã duyệt")
	elif kenh == KENH:
		tt.append("x"), nhan.append("Chữ ký số của đối tác hợp lệ")
	else:
		tt.append("n"), nhan.append("Tải tay trước khi có duyệt, chưa xác thực")
	# 3. Đọc tệp.
	st = n.get("trang_thai") or ""
	if st == "Đã nhận":
		tt.append("x"), nhan.append("Đọc đủ dòng, khớp tổng trên tệp")
	elif st == "Lỗi tệp":
		tt.append("d"), nhan.append("Tệp không đọc được")
	else:
		tt.append("d"), nhan.append("Còn dòng hoặc tổng cần xem")
	# 4. Khớp tiền.
	nhom, tien = n.get("nhom") or "", n.get("trang_thai_tien") or ""
	if float(n.get("phi_vuot") or 0) > 0:
		tt.append("d"), nhan.append("Phí thu cao hơn biểu phí hợp đồng")
	elif nhom == "Tiền bán":
		if tien in ("Đã thấy tiền về", "Không áp dụng"):
			tt.append("x"), nhan.append("Tiền về ngân hàng khớp" if tien == "Đã thấy tiền về" else "Không cần khớp tiền")
		elif tien in ("Lệch tiền về", "Chưa thấy tiền về"):
			tt.append("d"), nhan.append(tien)
		elif st != "Đã nhận":
			tt.append("n"), nhan.append("Khớp tiền sau khi đọc đủ dòng")
		else:
			tt.append("v"), nhan.append("Trùng số tiền, kế toán chọn" if tien == "Cần chọn tiền về" else "Chưa đối chiếu tiền về")
	elif nhom == "Thẻ tín dụng":
		ks = n.get("kiem_so_du") or ""
		if ks == "Khớp":
			tt.append("x"), nhan.append("Phương trình dư nợ khớp")
		elif ks == "Lệch":
			tt.append("d"), nhan.append("Phương trình dư nợ lệch")
		else:
			tt.append("v"), nhan.append("Chưa dựng được dư nợ (thiếu sao kê kỳ trước hoặc bảng gõ tay)")
	else:
		tt.append("x"), nhan.append("Không cần khớp tiền")
	# 5. Nối chứng từ.
	chua = int(n.get("so_chua_noi") or 0)
	if chua:
		tt.append("v"), nhan.append("%s/%s dòng đã nối" % (int(n.get("so_da_noi") or 0), int(n.get("so_da_noi") or 0) + chua))
	else:
		tt.append("x"), nhan.append("Đủ chứng từ")
	# 6. Xác nhận: chỉ khi năm bước trước xanh.
	truoc = all(c == "x" for c in tt)
	if n.get("xac_nhan_luc"):
		tt.append("x" if truoc else "d")
		nhan.append(("Kế toán đã xác nhận" if truoc else "Đã xác nhận nhưng số đổi sau đó, cần xác nhận lại"))
	elif truoc:
		tt.append("v"), nhan.append("Chờ kế toán xác nhận")
	else:
		tt.append("n"), nhan.append("Mở khi năm bước trước xanh")
	# Bước đang kẹt: bỏ qua bước 2 xám của nguồn cũ để nguồn cũ vẫn lọc được
	# theo bước 3, 4, 5.
	hien = 7
	for i, c in enumerate(tt):
		if c == "x" or (i == 1 and c == "n"):
			continue
		hien = i + 1
		break
	ghi = "Đã khép" if hien == 7 else nhan[hien - 1]
	return dict(tt="".join(tt), hien=hien, ghi=ghi, nhan=nhan, xac_nhan_duoc=1 if (truoc and not n.get("xac_nhan_luc")) else 0)


def dem_buoc(rows):
	"""THUẦN. Số nguồn ĐANG KẸT (vàng hoặc đỏ) ở từng bước 1..6."""
	dem = {}
	for r in rows:
		b = buoc_nguon(r)
		if b["hien"] <= 6 and b["tt"][b["hien"] - 1] in ("v", "d"):
			dem[b["hien"]] = dem.get(b["hien"], 0) + 1
	return dem


# ------------------------------------------------------------ THUẦN: thư dự kiến

def _d(x):
	if isinstance(x, datetime):
		return x.date()
	if isinstance(x, date):
		return x
	s = str(x or "")[:10]
	return date.fromisoformat(s) if len(s) == 10 else None


def thu_thieu(lich, hom_nay, gio, nguon, ngay_bat):
	"""THUẦN. Thư dự kiến đã quá hạn mà chưa về qua hộp thư.

	lich: [{vendor, tan_suat, han_gio, han_ngay, ngay_lam_viec}]
	nguon: [{vendor, tai_khoan, tu_ngay, den_ngay, kenh_nhan}] trong 40 ngày.
	ngay_bat: ngày hộp thư bắt đầu đọc được (trước đó không xét).
	Trả [{vendor, tai_khoan, ngay (ISO, ngày giao dịch hay tháng), han, khoa}].
	Một nguồn có nhiều tài khoản (OnePay thẻ và VietQR) thì xét từng tài khoản đã
	thấy trong 14 ngày qua."""
	hom_nay, ngay_bat = _d(hom_nay), _d(ngay_bat)
	if not ngay_bat:
		return []
	ra = []
	for l in lich or []:
		v = l.get("vendor") or ""
		ts = l.get("tan_suat") or ""
		cua = [x for x in nguon if x.get("vendor") == v]
		tu_thu = [x for x in cua if x.get("kenh_nhan") == KENH]
		if ts == "Hằng ngày":
			han = int(l.get("han_gio") or 12)
			if gio < han:
				continue
			if l.get("ngay_lam_viec") and hom_nay.weekday() >= 5:
				continue
			d = hom_nay - timedelta(days=1)
			if d < ngay_bat:
				continue
			khoa_tk = sorted({x.get("tai_khoan") or "" for x in cua if (_d(x.get("den_ngay")) or date.min) >= hom_nay - timedelta(days=14)}) or [""]
			for tk in khoa_tk:
				co = any((not tk or (x.get("tai_khoan") or "") == tk) and _d(x.get("tu_ngay") or x.get("den_ngay"))
					and _d(x.get("tu_ngay") or x.get("den_ngay")) <= d <= _d(x.get("den_ngay") or x.get("tu_ngay")) for x in tu_thu)
				if not co:
					ra.append(dict(vendor=v, tai_khoan=tk, ngay=d.isoformat(), han="%02d:00" % han,
						khoa="%s|%s|%s" % (d.isoformat(), v, tk)))
		elif ts == "Hằng tháng":
			han = int(l.get("han_ngay") or 5)
			if hom_nay.day < han:
				continue
			cuoi = hom_nay.replace(day=1) - timedelta(days=1)
			dau = cuoi.replace(day=1)
			if ngay_bat > cuoi:
				continue
			co = any(dau <= (_d(x.get("den_ngay")) or date.min) <= cuoi for x in tu_thu)
			if not co:
				ra.append(dict(vendor=v, tai_khoan="", ngay=dau.isoformat()[:7], han="ngày %02d" % han,
					khoa="%s|%s|" % (dau.isoformat()[:7], v)))
	return ra


# ------------------------------------------------------------ THUẦN: biểu phí

def so_bieu(v):
	"""THUẦN. "1,44", "1.44%", 1.44 -> 1.44; rỗng hay sai -> 0.0."""
	if v in (None, ""):
		return 0.0
	try:
		return max(0.0, float(str(v).replace("%", "").replace(",", ".").strip()))
	except ValueError:
		return 0.0


def bieu_cho(the, vung, bieu):
	"""THUẦN. Biểu phí hợp đồng của một nhóm giao dịch; 0 là chưa khai (không kiểm)."""
	the, vung = (the or "").upper(), (vung or "").upper()
	if "NAPAS" in the:
		return so_bieu(bieu.get("napas"))
	if vung.startswith("DOMESTIC"):
		return so_bieu(bieu.get("noi_dia"))
	if vung.startswith("INTERNATIONAL"):
		return so_bieu(bieu.get("quoc_te"))
	return 0.0


def phi_vuot(phi_the, bieu, nguong=NGUONG_PHI_MAC_DINH):
	"""THUẦN. Phí thu dư so với biểu phí hợp đồng. Trả (tổng dư, chi tiết)."""
	ct, tong = [], 0
	for g in phi_the or []:
		muc = bieu_cho(g.get("the"), g.get("vung"), bieu)
		if not muc:
			continue
		if float(g.get("mdr") or 0) - muc < nguong - 1e-9:
			continue
		dung = int(round(int(g.get("gop") or 0) * muc / 100.0))
		du = int(g.get("phi") or 0) - dung
		if du <= 0:
			continue
		tong += du
		ct.append(dict(the=g.get("the"), vung=g.get("vung"), mdr=g.get("mdr"), bieu=muc,
			gop=int(g.get("gop") or 0), phi=int(g.get("phi") or 0), du=du))
	return tong, ct


# ------------------------------------------------------------ THUẦN: tin Zalo

def _tien(x):
	from vagabond.tin_tai_chinh import tien
	return tien(x)


def _dm(x):
	s = str(x or "")
	if len(s) == 7:
		return "tháng %s/%s" % (s[5:7], s[:4])
	return "%s/%s" % (s[8:10], s[5:7]) if len(s) >= 10 else s


def _gio(x):
	s = str(x or "")
	return "%s %s" % (s[11:16], _dm(s)) if len(s) >= 16 else _dm(s)


def _vung(v):
	return {"DOMESTIC": "nội địa", "INTERNATIONAL": "quốc tế"}.get((v or "").upper(), (v or "").lower())


def tin_gia_danh(nguon, nguoi_gui, luc, ly_do):
	"""THUẦN. Tin 1: thư giả danh bị chặn."""
	return ("Chặn 1 thư tự xưng %s" % nguon, [
		"Người gửi ghi: %s, %s" % (nguoi_gui, _gio(luc)),
		"%s KHÔNG nhận số liệu." % ly_do,
		"Có thể là thư giả. Đừng mở tệp đính kèm, đừng làm theo nội dung thư."])


def tin_thieu_thu(ds, lan):
	"""THUẦN. Tin 2: thư dự kiến chưa về. lan 1 lúc 12:30, lan 2 lúc 17:00."""
	dong = ["%s%s, %s" % (x["vendor"], (" (tài khoản %s)" % x["tai_khoan"]) if x.get("tai_khoan") else "",
		("ngày " + _dm(x["ngay"])) if len(x["ngay"]) > 7 else _dm(x["ngay"])) for x in ds[:8]]
	if len(ds) > 8:
		dong.append("và %s thư nữa" % (len(ds) - 8))
	dong.append("Thư về muộn thì máy tự nhận. Quá 17:00 vẫn chưa về: hỏi đối tác hoặc tải tay (chờ Giám đốc duyệt)."
		if lan == 1 else "Vẫn chưa về sau 17:00: hỏi đối tác, hoặc tải tay tệp gốc (chờ Giám đốc duyệt).")
	return ("Còn %s thư đối soát chưa về" % len(ds), dong)


def tin_hop_thu_loi(tu_luc, ly_do):
	"""THUẦN. Tin 3: không đọc được hộp thư."""
	return ("ERP không đọc được hộp thư %s từ %s" % (HOP, _gio(tu_luc)), [
		"Lý do: %s" % ly_do,
		"Trong lúc này thư đối soát vẫn nằm trong hộp thư, không mất. Giám đốc mở Cài đặt lõi để khai lại mật khẩu."])


def tin_tep_loi(vendor, ky, ly_do):
	"""THUẦN. Tin 4: tệp đối soát từ thư đọc không được."""
	return ("Tệp đối soát %s %s không đọc được" % (vendor, ky), [
		(ly_do or "Tệp lỗi.")[:300], "Có thể đối tác đổi mẫu báo cáo. Kế toán mở nguồn để xem dòng lỗi."])


def tin_lech_tien(vendor, ky, bao, nhan):
	"""THUẦN. Tin 5: lệch tiền về."""
	lech = int(nhan) - int(bao)
	return ("Lệch tiền về: %s, %s" % (vendor, ky), [
		"%s báo chuyển: %s" % (vendor, _tien(bao)),
		"Ngân hàng nhận thật (SePay): %s" % _tien(nhan),
		("Thiếu: %s" % _tien(-lech)) if lech < 0 else ("Dư: %s" % _tien(lech))])


def tin_chua_thay_tien(ds):
	"""THUẦN. Tin 6: đợt đối tác báo đã chuyển mà ngân hàng chưa thấy tiền."""
	dong = ["%s, %s: %s" % (x["vendor"], x["ky"], _tien(x["tien"])) for x in ds[:8]]
	if len(ds) > 8:
		dong.append("và %s đợt nữa" % (len(ds) - 8))
	dong.append("Tổng chưa về: %s. Hỏi đối tác hoặc xem sao kê." % _tien(sum(x["tien"] for x in ds)))
	return ("Chưa thấy tiền về: %s đợt đối tác báo đã chuyển" % len(ds), dong)


def tin_phi_cao(vendor, ky, ct, thang):
	"""THUẦN. Tin 7: phí thu cao hơn biểu phí hợp đồng."""
	dong = ["Thẻ %s %s: thu %s%%, hợp đồng %s%%, dư %s trên %s" % (
		x["the"].title(), _vung(x["vung"]), _so(x["mdr"]), _so(x["bieu"]), _tien(x["du"]), _tien(x["gop"])) for x in ct[:6]]
	dong.append("Tháng này đã dư %s." % _tien(thang))
	return ("%s thu phí cao hơn hợp đồng, %s" % (vendor, ky), dong)


def _so(x):
	s = ("%.3f" % float(x or 0)).rstrip("0").rstrip(".")
	return s.replace(".", ",")


def tin_don_thieu_erp(ds):
	"""THUẦN. Tin 8: giao dịch đối tác đã thu mà ERP chưa có đơn."""
	dong = ["%s %s%s: %s" % (x["vendor"], _dm(x["ngay"]), (" " + str(x["gio"])[:5]) if x.get("gio") else "",
		_tien(x["tien"])) for x in ds[:8]]
	if len(ds) > 8:
		dong.append("và %s giao dịch nữa" % (len(ds) - 8))
	dong.append("Cửa hàng kiểm đơn của các giờ này; có đơn thì kế toán bấm Đối chiếu lại.")
	return ("%s giao dịch đối tác đã thu mà ERP chưa có đơn" % len(ds), dong)


def tin_tai_tay(nguoi, vendor, ky, so_dong, tien, ly_do, tu_thu=False):
	"""THUẦN. Tin 10: tệp tải tay (hoặc thư không chữ ký) chờ giám đốc duyệt."""
	dau = ("Thư %s không có chữ ký số, chờ Giám đốc duyệt" % vendor) if tu_thu else (
		"%s vừa tải tay 1 tệp đối soát, chờ Giám đốc duyệt" % (nguoi or "Kế toán"))
	return (dau, ["%s %s, %s dòng, %s" % (vendor, ky, so_dong, _tien(tien)),
		"Lý do: %s" % (ly_do or "không ghi")])


# ------------------------------------------------------------ THUẦN: máy chủ IMAP

def chon_may_chu(dia_chi, may_chu, cong, hop_co):
	"""THUẦN. (máy chủ, cổng). Ô Máy chủ để trống thì lấy máy chủ nhận thư của
	một hộp thư cùng tên miền đã khai trong ERP (erp@, sales@...)."""
	m = (may_chu or "").strip()
	m = re.sub(r"^(imaps?://)", "", m, flags=re.I).strip("/ ")
	if ":" in m and not cong:
		m, c = m.rsplit(":", 1)
		cong = int(c) if c.isdigit() else 0
	cong = int(cong or 0) or 993
	if m:
		return m, cong
	mien = mien_cua(dia_chi)
	for h in hop_co or []:
		if mien and mien_cua(h.get("email_id")) == mien and (h.get("email_server") or "").strip():
			return h["email_server"].strip(), int(h.get("incoming_port") or 0) or cong
	return "", cong


def ly_do_imap(e):
	"""THUẦN. Câu lỗi IMAP viết cho người dùng."""
	s = str(e or "")
	k = s.lower()
	if "authenticationfailed" in k or "login" in k and ("fail" in k or "invalid" in k) or "auth" in k and "fail" in k:
		return "sai mật khẩu hoặc tên đăng nhập hộp thư."
	if "timed out" in k or "timeout" in k:
		return "máy chủ thư không trả lời (quá giờ chờ)."
	if "name or service not known" in k or "nodename" in k or "getaddrinfo" in k:
		return "sai tên máy chủ thư."
	if "quota" in k or "over" in k and "limit" in k:
		return "hộp thư đầy."
	if "select" in k or "mailbox" in k and "exist" in k:
		return "không thấy thư mục cần đọc trong hộp thư."
	return "mất kết nối tới máy chủ thư (%s)." % s[:120]


# ============================================================ PHẦN CHẠM FRAPPE

def _frappe():
	import frappe

	return frappe


def _bang(doc, fn):
	return [r.as_dict() if hasattr(r, "as_dict") else dict(r) for r in (doc.get(fn) or [])]


def cau_hinh():
	"""Cấu hình đọc từ Cài đặt lõi (Vagabond Settings). Bảng trống dùng mặc định."""
	frappe = _frappe()
	s = frappe.get_cached_doc(CAI_DAT)
	ng = [dict(ten=(r.get("ten") or "").strip(), mien=tach_mien(r.get("ten_mien")), bat_buoc=1 if r.get("bat_buoc_chu_ky") else 0)
		for r in _bang(s, "ds_nguoi_gui") if r.get("ten_mien")]
	if not ng:
		ng = [dict(ten=t, mien=tach_mien(m), bat_buoc=b) for t, m, b in NGUOI_GUI_MAC_DINH]
	lich = [dict(vendor=(r.get("nguon") or "").strip(), tan_suat=r.get("tan_suat") or "", han_gio=r.get("han_gio") or 12,
		han_ngay=r.get("han_ngay") or 5, ngay_lam_viec=r.get("ngay_lam_viec") or 0) for r in _bang(s, "ds_lich_thu")
		if r.get("nguon")]
	if not lich:
		lich = [dict(vendor=v, tan_suat=t, han_gio=g, han_ngay=n, ngay_lam_viec=l) for v, t, g, n, l in LICH_MAC_DINH]
	return dict(
		bat=1 if s.get("ds_thu_bat") else 0, dia_chi=(s.get("ds_thu_dia_chi") or "").strip(),
		may_chu=s.get("ds_thu_may_chu") or "", cong=s.get("ds_thu_cong") or 0,
		thu_muc=(s.get("ds_thu_thu_muc") or "").strip() or "INBOX", nguoi_gui=ng, lich=lich,
		noi_bo=tach_dia_chi(s.get("ds_thu_noi_bo")),
		nguong_lech=float(s.get("ds_nguong_lech") or 0) or NGUONG_LECH_MAC_DINH,
		nguong_phi=so_bieu(s.get("ds_nguong_phi")) or NGUONG_PHI_MAC_DINH,
		bieu=dict(noi_dia=s.get("ds_bieu_noi_dia"), quoc_te=s.get("ds_bieu_quoc_te"), napas=s.get("ds_bieu_napas")),
	)


KHOA_TRANG_THAI = "vgb_ds_hop_thu"


def trang_thai():
	frappe = _frappe()
	try:
		return json.loads(frappe.db.get_global(KHOA_TRANG_THAI) or "{}")
	except ValueError:
		return {}


def _ghi_trang_thai(**k):
	frappe = _frappe()
	d = trang_thai()
	d.update(k)
	frappe.db.set_global(KHOA_TRANG_THAI, json.dumps(d, default=str))
	return d


def gieo_mac_dinh():
	"""after_migrate: gieo bảng Người gửi tin cậy và Lịch thư MỘT lần khi còn
	trống (ghi thẳng dòng con, không lưu cả trang Cài đặt để không chạy kiểm tra
	của các ô khác). Anh đã xoá hết dòng thì không gieo lại."""
	frappe = _frappe()
	gieo_noi_bo()
	try:
		# v642: Cài đặt lõi là doctype Single, KHÔNG có bảng riêng: db.has_column
		# trên nó ném TableMissingError trên ERPNext thật (site 06/11 không gieo
		# được dòng nào). Chỉ hỏi meta và bảng của hai doctype con.
		if not frappe.get_meta(CAI_DAT).has_field("ds_nguoi_gui"):
			return
		if not (frappe.db.table_exists("Vagabond Doi Soat Nguoi Gui") and frappe.db.table_exists("Vagabond Doi Soat Lich Thu")):
			return
		if frappe.db.get_global("vgb_ds_thu_gieo"):
			return
		for fn, dt, dong in (
			("ds_nguoi_gui", "Vagabond Doi Soat Nguoi Gui",
				[dict(ten=t, ten_mien=m, bat_buoc_chu_ky=b) for t, m, b in NGUOI_GUI_MAC_DINH]),
			("ds_lich_thu", "Vagabond Doi Soat Lich Thu",
				[dict(nguon=v, tan_suat=t, han_gio=g, han_ngay=n, ngay_lam_viec=l) for v, t, g, n, l in LICH_MAC_DINH])):
			if frappe.db.count(dt, {"parent": CAI_DAT, "parentfield": fn}):
				continue
			for i, r in enumerate(dong, 1):
				frappe.get_doc(dict(doctype=dt, parent=CAI_DAT, parenttype=CAI_DAT, parentfield=fn, idx=i, **r)).db_insert()
		frappe.db.set_global("vgb_ds_thu_gieo", "1")
		frappe.clear_document_cache(CAI_DAT, CAI_DAT)
	except Exception:
		frappe.log_error(title="Đối soát hộp thư: gieo cài đặt mặc định")


def gieo_noi_bo():
	"""v643: gieo ô Hộp thư nội bộ được chuyển tiếp MỘT lần khi ô còn trống. Anh
	xoá trắng sau đó thì không gieo lại (để trống là không nhận thư chuyển tiếp)."""
	frappe = _frappe()
	try:
		if not frappe.get_meta(CAI_DAT).has_field("ds_thu_noi_bo") or frappe.db.get_global("vgb_ds_noi_bo_gieo"):
			return
		if not (frappe.db.get_single_value(CAI_DAT, "ds_thu_noi_bo") or "").strip():
			frappe.db.set_single_value(CAI_DAT, "ds_thu_noi_bo", "\n".join(NOI_BO_MAC_DINH))
		frappe.db.set_global("vgb_ds_noi_bo_gieo", "1")
		frappe.clear_document_cache(CAI_DAT, CAI_DAT)
	except Exception:
		frappe.log_error(title="Đối soát hộp thư: gieo hộp thư nội bộ")


# ------------------------------------------------------------ đọc hộp thư

def _mat_khau():
	frappe = _frappe()
	try:
		return frappe.get_doc(CAI_DAT).get_password("ds_thu_mat_khau", raise_exception=False) or ""
	except Exception:
		return ""


def _ket_noi(ch):
	import imaplib

	frappe = _frappe()
	hop = frappe.get_all("Email Account", fields=["email_id", "email_server", "incoming_port"], limit_page_length=50)
	may, cong = chon_may_chu(ch["dia_chi"], ch["may_chu"], ch["cong"], hop)
	if not may:
		raise RuntimeError("Chưa khai máy chủ thư (IMAP) cho hộp thư đối soát.")
	mk = _mat_khau()
	if not ch["dia_chi"] or not mk:
		raise RuntimeError("Chưa khai địa chỉ hoặc mật khẩu hộp thư đối soát.")
	m = imaplib.IMAP4_SSL(may, cong, timeout=30)
	m.login(ch["dia_chi"], mk)
	# Codex #544 vòng 3: máy chủ thật đã dùng (kể cả khi lấy từ hộp erp@) làm
	# danh tính của mốc đọc.
	m.vgb_may, m.vgb_cong = may, cong
	return m


def _chon_thu_muc(m, thu_muc):
	kq, du = m.select('"%s"' % thu_muc.replace('"', ""), readonly=True)
	if kq != "OK":
		raise RuntimeError("select %s: %s" % (thu_muc, du))
	kq, du = m.response("UIDVALIDITY")
	try:
		return int((du or [b"0"])[0])
	except (TypeError, ValueError):
		return 0


def doc_dinh_ky():
	"""Lịch mỗi 15 phút. Hộp thư chưa bật thì không làm gì."""
	frappe = _frappe()
	ch = cau_hinh()
	if not ch["bat"]:
		return
	frappe.set_user("Administrator")
	doc_hop_thu(ch)


def doc_hop_thu(ch=None):
	"""Đọc thư mới (UID lớn hơn lần trước). Một lượt tối đa TOI_DA_MOI_LUOT thư,
	khoá có tên để nút "Đọc hộp thư ngay" và lịch không chạy chồng."""
	frappe = _frappe()
	ch = ch or cau_hinh()
	r = frappe.db.sql("select get_lock('vgb_ds_hop_thu', 0)")
	if not r or r[0][0] != 1:
		return dict(so_thu=0, dang_chay=1)
	so = 0
	loi_thu = ""
	try:
		tt = trang_thai()
		try:
			m = _ket_noi(ch)
			try:
				uv = _chon_thu_muc(m, ch["thu_muc"])
				danh = danh_hop(getattr(m, "vgb_may", ""), getattr(m, "vgb_cong", 0), ch.get("dia_chi"), ch["thu_muc"])
				moc = moc_doc(tt, uv, danh)
				cuoi, loi_uid, dns_tu = moc["uid"], moc["loi_uid"], moc["dns_tu"]
				if moc["doi"]:
					# Codex #544 vòng 2, 3: ghi mốc của thư mục mới NGAY, để lượt sau
					# không lấy UID của thư mục cũ áp cho thư mục mới.
					_ghi_trang_thai(uidvalidity=uv, hop=danh, uid=0, loi_uid={}, dns_tu={})
					frappe.db.commit()
				elif tt.get("hop") != danh:
					_ghi_trang_thai(hop=danh)
					frappe.db.commit()
				kq, du = m.uid("search", None, "UID %s:*" % (cuoi + 1))
				uids = sorted(int(x) for x in (du[0] or b"").split() if int(x) > cuoi) if kq == "OK" else []
				for uid in uids[:TOI_DA_MOI_LUOT]:
					# Lỗi kết nối khi lấy thư đi ra nhánh lỗi cả lượt (không vượt mốc).
					kq, du = m.uid("fetch", str(uid), "(BODY.PEEK[])")
					tho = next((x[1] for x in (du or []) if isinstance(x, tuple) and len(x) > 1), None)
					try:
						if not tho:
							# Trước đây thư không lấy được nội dung bị vượt qua im lặng.
							raise RuntimeError("Máy chủ thư không trả nội dung thư (%s)." % kq)
						_xu_ly(tho, uid, ch)
						frappe.db.commit()
					except Exception as e:
						frappe.db.rollback()
						frappe.log_error(title="Đối soát hộp thư: xử lý thư UID %s" % uid)
						from vagabond.doi_soat_dkim import LoiDnsTam

						bay = str(frappe.utils.now_datetime())[:19]
						lan = int(loi_uid.get(str(uid)) or 0) + 1
						dns = isinstance(e, LoiDnsTam)
						if dns:
							dns_tu.setdefault(str(uid), bay)
						if xu_ly_loi(lan, dns_tu.get(str(uid)) if dns else None, bay) == "thu_lai":
							# Codex #544 F1: KHÔNG vượt mốc; dừng lượt, lượt sau đọc lại thư này.
							loi_uid[str(uid)] = lan
							loi_thu = ("Thư UID %s chưa kiểm được chữ ký vì tra khoá lỗi tạm (%s), sẽ thử lại." if dns else
								"Thư UID %s xử lý lỗi lần %s (%s), sẽ thử lại.") % ((uid, str(e)[:120]) if dns else (uid, lan, str(e)[:120]))
							_ghi_trang_thai(uidvalidity=uv, uid=cuoi, loi_uid=loi_uid, dns_tu=dns_tu, loi=loi_thu)
							frappe.db.commit()
							break
						_ghi_thu_loi(tho or ("X-Vagabond: thu UID %s UIDVALIDITY %s khong lay duoc noi dung\r\n\r\n" % (
							uid, uv)).encode(), uid, ch, str(e)[:500], dns=dns)
					so += 1
					cuoi = uid
					loi_uid.pop(str(uid), None)
					dns_tu.pop(str(uid), None)
					_ghi_trang_thai(uidvalidity=uv, uid=uid, loi_uid=loi_uid, dns_tu=dns_tu)
					frappe.db.commit()
			finally:
				try:
					m.logout()
				except Exception:
					pass
		except Exception as e:
			frappe.db.rollback()
			_loi_hop_thu(tt, e)
			return dict(so_thu=so, loi=str(e) if isinstance(e, RuntimeError) else ly_do_imap(e))
		bay = str(frappe.utils.now_datetime())[:19]
		con_loi = trang_thai().get("loi") if loi_thu else ""
		_ghi_trang_thai(doc_luc=bay, loi=con_loi or "", so_loi=0, loi_tu="", ngay_bat=tt.get("ngay_bat") or bay[:10])
		frappe.db.commit()
		return dict(so_thu=so)
	finally:
		frappe.db.sql("select release_lock('vgb_ds_hop_thu')")


def _loi_hop_thu(tt, e):
	frappe = _frappe()
	ly = str(e) if isinstance(e, RuntimeError) else ly_do_imap(e)
	so = int(tt.get("so_loi") or 0) + 1
	tu = tt.get("loi_tu") or str(frappe.utils.now_datetime())[:19]
	_ghi_trang_thai(loi=ly, so_loi=so, loi_tu=tu, loi_luc=str(frappe.utils.now_datetime())[:19])
	if so == SO_LOI_BAO:
		from vagabond import kenh_zalo

		t, d = tin_hop_thu_loi(tu, ly)
		kenh_zalo.bao_hoac_ghi_loi("canh_bao", "he_thong", t, d, link=_link(), khoa="ds_hop_thu_loi:%s" % tu,
			ma_tin="ht_ds_hop_thu_loi")
	frappe.db.commit()


def _link(duong=DUONG_APP):
	from vagabond import lien_ket_app

	return lien_ket_app.link(duong)


def _luu_tep(ten, byte, thu):
	frappe = _frappe()
	f = frappe.get_doc({"doctype": "File", "file_name": ten, "content": byte, "is_private": 1,
		"attached_to_doctype": DT_THU, "attached_to_name": thu})
	f.flags.ignore_permissions = True
	f.insert(ignore_permissions=True)
	return f.file_url


def _luu_tep_an_toan(ten, byte, thu):
	"""Cất tệp; lỗi cất (đuôi tệp bị Cài đặt hệ thống chặn, PDF hỏng) không làm
	mất cả thư: ghi Error Log, trả None, số liệu vẫn đọc từ byte trong bộ nhớ."""
	frappe = _frappe()
	frappe.db.savepoint("ds_luu_tep")
	try:
		return _luu_tep(ten, byte, thu)
	except Exception:
		frappe.db.rollback(save_point="ds_luu_tep")
		frappe.log_error(title="Đối soát hộp thư: chưa cất được tệp %s của thư %s" % (ten, thu))
		return None


def _ly_do_loi(ly, dns=False):
	if dns:
		return "Chưa kiểm được chữ ký số vì tra khoá lỗi suốt %s giờ: %s. Bấm Đọc lại thư khi mạng ổn." % (GIO_THU_LAI_DNS, ly)
	return "Máy xử lý lỗi %s lần: %s. Bấm Đọc lại thư sau khi kỹ thuật sửa." % (SO_THU_LAI, ly)


def _ghi_thu_loi(tho, uid, ch, ly, dns=False):
	"""Codex #544 F1: thư lỗi SO_THU_LAI lần: ghi sổ thư "Lỗi xử lý" kèm bản gốc
	để kỹ thuật đọc lại, rồi mới cho lượt đọc đi tiếp. Ghi hỏng nữa thì chỉ để
	Error Log (không chặn mãi các thư sau)."""
	frappe = _frappe()
	try:
		sha = hashlib.sha256(tho).hexdigest()
		cu = frappe.db.get_value(DT_THU, {"sha256": sha}, "name")
		if cu:
			frappe.db.set_value(DT_THU, cu, {"ket_qua": KQ_LOI, "ly_do": _ly_do_loi(ly, dns)[:1000], "xong": 0},
				update_modified=False)
		else:
			try:
				t = doc_thu(tho)
			except Exception:
				t = dict(nguoi_gui="", mien="", tieu_de="", message_id="")
			from vagabond import doi_soat_vendor as dsv

			thu = frappe.get_doc(dict(doctype=DT_THU, sha256=sha, uid=str(uid), message_id=t.get("message_id") or "",
				nhan_luc=frappe.utils.now_datetime(), nguoi_gui=t.get("nguoi_gui") or "", ten_mien=(t.get("mien") or "")[:140],
				tieu_de=t.get("tieu_de") or "", ket_qua=KQ_LOI, ly_do=_ly_do_loi(ly, dns)[:1000],
				company=dsv._cong_ty()))
			thu.insert(ignore_permissions=True)
			if len(tho) <= TOI_DA_BYTE_THU:
				thu.db_set("tep_goc", _luu_tep_an_toan("thu-%s.eml" % thu.name, tho, thu.name))
		frappe.db.commit()
	except Exception:
		frappe.db.rollback()
		frappe.log_error(title="Đối soát hộp thư: chưa ghi được sổ thư lỗi UID %s" % uid)


def _quyet(tho, t, ch):
	"""(quyết định, chữ ký) cho một thư: đối tác (theo tên miền) trước, rồi hộp
	nội bộ được chuyển tiếp (theo đúng địa chỉ), còn lại là chặn.

	v643: hạn x= của chữ ký so với giờ máy chủ tiệm nhận thư, không phải giờ
	bấm Kiểm lại thư (doi_soat_dkim.luc_nhan)."""
	import time as _time

	from vagabond import doi_soat_dkim

	bay = doi_soat_dkim.luc_nhan(tho)
	bay = min(bay, int(_time.time())) if bay else None
	dong = dong_cua(t["mien"], ch["nguoi_gui"])
	noi_bo = (t.get("dia_chi") or "").lower() in (ch.get("noi_bo") or [])
	chu_ky = doi_soat_dkim.kiem_thu(tho, doi_soat_dkim.lay_khoa_dns, bay) if (dong or noi_bo) and t["so_from"] == 1 else []
	if dong or not noi_bo:
		return quyet_dinh(t["mien"], t["so_from"], chu_ky, ch["nguoi_gui"]), chu_ky
	td = [(a.decode("latin-1"), b.decode("latin-1")) for a, b, _k in doi_soat_dkim.tach_thu(tho)[0]]
	return quyet_noi_bo(t["dia_chi"].lower(), t["so_from"], chu_ky, qua_may_chu_dang_nhap(td, t["dia_chi"])), chu_ky


def _xu_ly(tho, uid, ch, kiem_lai=False, giu_xac_thuc=False):
	"""Một thư: ghi sổ thư, lưu bản gốc, kiểm chữ ký, nhận tệp hợp lệ.

	Codex #544 F1: lượt nhận tệp commit giữa chừng (khoá đối chiếu), nên thư lỗi
	giữa chừng có thể đã có dòng sổ thư. Lượt thử lại dùng tiếp dòng đó (chưa
	"xong") thay vì coi là đã xử lý; mọi bước nhận tệp chống trùng theo mã băm."""
	frappe = _frappe()
	from vagabond import doi_soat_dkim
	from vagabond import doi_soat_vendor as dsv

	sha = hashlib.sha256(tho).hexdigest()
	cu = frappe.db.get_value(DT_THU, {"sha256": sha}, ["name", "xong", "tep_goc"], as_dict=True)
	if cu and cu.xong and not kiem_lai:
		return None
	t = doc_thu(tho)
	qd, chu_ky = _quyet(tho, t, ch)
	if qd.get("noi_bo") and qd["ket_qua"] == KQ_XAC_THUC:
		t = doc_thu(tho, vao_long=True)
	if phai_doc_lai_dns(qd["ket_qua"], chu_ky):
		# Codex #544 vòng 2: chưa kết luận khi tra khoá lỗi tạm; không ghi sổ
		# thư, không đánh dấu xong, để lượt sau (hoặc nút Đọc lại thư) kiểm lại.
		raise doi_soat_dkim.LoiDnsTam("; ".join(c["ly_do"] for c in chu_ky if c.get("tam"))[:300])
	if giu_xac_thuc and qd["ket_qua"] != KQ_XAC_THUC:
		# Đọc lại thư ĐÃ xác thực (để đọc lại tệp sau khi sửa mẫu): đối tác có thể
		# đã đổi khoá DKIM từ đó, kiểm lại không đạt. Không hạ thư thật thành
		# "Bị chặn" và không báo thư giả; dừng trước mọi lần ghi, giữ kết quả cũ.
		frappe.throw("Chữ ký số của thư này nay không kiểm lại được (%s). Máy giữ nguyên kết quả cũ và không đọc lại "
			"tệp; tải tay tệp gốc (chờ Giám đốc duyệt) nếu cần đọc lại." % (qd["ly_do"] or "đối tác có thể đã đổi khoá")[:300],
			title="Không đọc lại được thư")
	cong_ty = dsv._cong_ty()
	truong = dict(sha256=sha, uid=str(uid), message_id=t["message_id"],
		gui_luc=t["gui_luc"] or None, nguoi_gui=t["nguoi_gui"],
		ten_mien=t["mien"][:140], tieu_de=t["tieu_de"], doi_tac=qd["nguon"], ket_qua=qd["ket_qua"],
		ly_do=qd["ly_do"][:1000], chu_ky=json.dumps(chu_ky, ensure_ascii=False)[:2000], ky_boi=qd["ky_boi"],
		so_tep=len(t["tep"]), company=cong_ty)
	if cu:
		thu = frappe.get_doc(DT_THU, cu.name)
		thu.db_set(truong)
	else:
		thu = frappe.get_doc(dict(doctype=DT_THU, nhan_luc=frappe.utils.now_datetime(), **truong))
		thu.insert(ignore_permissions=True)
	if len(tho) <= TOI_DA_BYTE_THU and not (cu and cu.tep_goc):
		thu.db_set("tep_goc", _luu_tep_an_toan("thu-%s.eml" % thu.name, tho, thu.name))
	if qd["ket_qua"] == KQ_CHAN:
		if qd["bao_zalo"]:
			from vagabond import kenh_zalo

			ten_nguon = ("hộp thư nội bộ %s" % t["dia_chi"]) if qd.get("noi_bo") else qd["nguon"]
			tieu, d = tin_gia_danh(ten_nguon, t["dia_chi"] or t["nguoi_gui"], t["gui_luc"] or thu.nhan_luc, qd["ly_do"])
			kenh_zalo.bao_hoac_ghi_loi("canh_bao", "cong_no", tieu, d, link=_link(), khoa="ds_gia_danh:%s" % thu.name,
				ma_tin="kt_ds_thu_gia_danh")
			thu.db_set("bao_zalo", frappe.utils.now_datetime())
		thu.db_set("xong", 1)
		return thu.name
	dv = DV_THU if qd["ket_qua"] == KQ_XAC_THUC else DV_CHO
	them = dict(thu=thu.name, duong_vao=dv)
	ket, sot = [], []
	for ten, byte in t["tep"]:
		url = _luu_tep_an_toan(ten, byte, thu.name)
		bo_qua = []
		ket.extend(dsv._nhan_byte(ten, byte, KENH, file_url=url, chi_mau_quen=True, bo_qua=bo_qua, cong_ty=cong_ty,
			them=them))
		if bo_qua:
			sot.append((ten, byte, url, set(bo_qua)))
	# Giống lối email cũ (Codex #450): thư đã chắc là thư báo cáo thì tệp con
	# chưa có mẫu hay đọc lỗi vẫn hiện ở Cần xử lý; thư quảng cáo thì bỏ qua.
	# v643: thư nội bộ không có tệp đọc được thì không dựng nguồn "thư không tệp"
	# (thư nội bộ không phải thư báo cáo của một đối tác cụ thể).
	la_bao_cao = bool(ket) or (not qd.get("noi_bo") and dsv.thu_co_bao_cao(t["tieu_de"], t["than"]))
	if sot and la_bao_cao:
		for ten, byte, url, ten_bo in sot:
			ket.extend(r for r in dsv._nhan_byte(ten, byte, KENH, file_url=url, doc_lai=False, cong_ty=cong_ty, them=them)
				if r.get("ten_tep") in ten_bo)
	if not ket and la_bao_cao:
		ket.extend(_ghi_thu_khong_tep(thu, t, cong_ty, them))
	ten_nguon = [r["name"] for r in ket if r.get("name")]
	if not ten_nguon:
		thu.db_set({"ket_qua": KQ_KHONG_TEP if qd["ket_qua"] == KQ_XAC_THUC else qd["ket_qua"],
			"ly_do": (qd["ly_do"] + " Thư không có tệp báo cáo đọc được.")[:1000]})
	thu.db_set({"nguon": "\n".join(ten_nguon)[:1000], "xong": 1})
	return thu.name


def _ghi_thu_khong_tep(thu, t, cong_ty, them):
	from vagabond import doi_soat_doc as tep_doc
	from vagabond import doi_soat_khop as khop
	from vagabond import doi_soat_mau as mau_bc
	from vagabond import doi_soat_vendor as dsv

	frappe = _frappe()
	with dsv.khoa_doi_chieu():
		sha = tep_doc.bam(("than-thu:" + thu.sha256).encode("utf-8"))
		if frappe.db.exists(DT_NGUON, {"sha256": sha}):
			return []
		kq = mau_bc.ket_qua("", "", dsv.vendor_theo_thu(t["dia_chi"]) or thu.doi_tac, "")
		kq["loi"].append("Thư báo cáo của đối tác không có tệp đọc được (báo cáo nằm trong thân thư hoặc tệp chưa có mẫu). "
			"Báo kỹ thuật viết mẫu đọc mới.")
		tt = dict(ten=(t["tieu_de"] or "Thư đối tác không có tệp")[:140], sha256=sha, loai="")
		return [dsv._ghi_nguon(cong_ty, tt, kq, khop.xem_truoc(kq, cong_ty), KENH, None, None, them=them)]


# ------------------------------------------------------------ sau khi ghi, sau khi đối chiếu

def ky_hien(n):
	a, b = str(n.get("tu_ngay") or "")[:10], str(n.get("den_ngay") or "")[:10]
	if a and b and a != b:
		return "%s-%s" % (_dm(a), _dm(b))
	return ("ngày " + _dm(a or b)) if (a or b) else "chưa rõ kỳ"


def sau_khi_ghi(name, moi=True):
	"""Gọi từ doi_soat_vendor._ghi_nguon. Không bao giờ làm hỏng lượt nhận."""
	frappe = _frappe()
	try:
		n = frappe.db.get_value(DT_NGUON, name, ["name", "vendor", "tu_ngay", "den_ngay", "so_dong", "thuc_nhan",
			"trang_thai", "ly_do", "kenh_nhan", "duong_vao", "ly_do_tai_tay", "owner"], as_dict=True)
		if not n or not moi:
			return
		from vagabond import kenh_zalo

		if n.duong_vao == DV_CHO:
			ten = frappe.utils.get_fullname(n.owner) if n.kenh_nhan != KENH else ""
			t, d = tin_tai_tay(ten, n.vendor, ky_hien(n), n.so_dong, n.thuc_nhan, n.ly_do_tai_tay or (
				"thư không có chữ ký số" if n.kenh_nhan == KENH else ""), tu_thu=n.kenh_nhan == KENH)
			kenh_zalo.bao_hoac_ghi_loi("viec", "cong_no", t, d, link=_link(), khoa="ds_tai_tay:%s" % name,
				ma_tin="bgd_ds_tai_tay")
		if n.kenh_nhan == KENH and n.trang_thai in ("Lỗi tệp", "Cần xử lý"):
			t, d = tin_tep_loi(n.vendor, ky_hien(n), n.ly_do)
			kenh_zalo.bao_hoac_ghi_loi("viec", "cong_no", t, d, link=_link(), khoa="ds_tep_loi:%s" % name,
				ma_tin="kt_ds_tep_loi")
	except Exception:
		frappe.log_error(title="Đối soát hộp thư: báo sau khi nhận %s" % name)


def sau_doi_chieu(name, tien_cu):
	"""Gọi từ doi_soat_vendor._doi_chieu. Ghi phí vượt biểu, số dư thẻ, báo lệch tiền."""
	frappe = _frappe()
	try:
		n = frappe.db.get_value(DT_NGUON, name, ["name", "vendor", "mau", "nhom", "tu_ngay", "den_ngay", "thuc_nhan",
			"trang_thai_tien", "du_lieu", "company"], as_dict=True)
		if not n:
			return
		d = json.loads(n.du_lieu or "{}")
		ch = cau_hinh()
		from vagabond import kenh_zalo

		cap = {}
		if n.nhom == "Thẻ tín dụng":
			k = d.get("ky_the") or {}
			cap["kiem_so_du"] = "Khớp" if k.get("du") is True else ("Lệch" if k.get("du") is False else "Gõ tay")
		phi_the = (d.get("them") or {}).get("phi_the")
		if phi_the is not None:
			tong, ct = phi_vuot(phi_the, ch["bieu"], ch["nguong_phi"])
			cu = float(frappe.db.get_value(DT_NGUON, name, "phi_vuot") or 0)
			cap["phi_vuot"] = tong
			if tong and int(tong) != int(cu):
				thang = _phi_vuot_thang(n, tong - cu)
				t, dd = tin_phi_cao(n.vendor, ky_hien(n), ct, thang)
				kenh_zalo.bao_hoac_ghi_loi("canh_bao", "cong_no", t, dd, link=_link(), khoa="ds_phi:%s:%s" % (name, int(tong)),
					ma_tin="kt_ds_phi_cao")
		if cap:
			frappe.db.set_value(DT_NGUON, name, cap, update_modified=False)
		_bao_lech(n, d, tien_cu, ch)
	except Exception:
		frappe.log_error(title="Đối soát hộp thư: sau đối chiếu %s" % name)


def khoa_lech(name):
	"""THUẦN. v647: một nguồn chỉ một tin "Lệch tiền về" (khoá theo nguồn, không
	theo số giao dịch gần nhất), lượt dò lại mỗi giờ không gửi lặp."""
	return "ds_lech:%s" % name


def _bao_lech(n, d, tien_cu, ch):
	if n.trang_thai_tien == "Lệch tiền về" and tien_cu != "Lệch tiền về":
		l = d.get("lech_tien") or {}
		if l and abs(int(l.get("nhan") or 0) - int(l.get("bao") or 0)) >= ch["nguong_lech"]:
			from vagabond import kenh_zalo

			t, dd = tin_lech_tien(n.vendor, ky_hien(n), l.get("bao"), l.get("nhan"))
			kenh_zalo.bao_hoac_ghi_loi("canh_bao", "cong_no", t, dd, link=_link(),
				khoa=khoa_lech(n.name), ma_tin="kt_ds_lech_tien")


def bao_lech_tien(name, tien_cu):
	"""Gọi từ doi_soat_vendor.do_lai_tien_ve: chỉ báo lệch tiền thật (không ghi
	phí, không đổi số dư thẻ như sau_doi_chieu)."""
	frappe = _frappe()
	try:
		n = frappe.db.get_value(DT_NGUON, name, ["name", "vendor", "mau", "nhom", "tu_ngay", "den_ngay", "thuc_nhan",
			"trang_thai_tien", "du_lieu", "company"], as_dict=True)
		if n:
			_bao_lech(n, json.loads(n.du_lieu or "{}"), tien_cu, cau_hinh())
	except Exception:
		frappe.log_error(title="Đối soát hộp thư: báo lệch tiền %s" % name)


def _phi_vuot_thang(n, them):
	frappe = _frappe()
	dau = str(n.den_ngay or frappe.utils.nowdate())[:8] + "01"
	r = frappe.db.sql("""select coalesce(sum(phi_vuot),0) from `tab%s` where vendor=%%s and company=%%s
		and den_ngay>=%%s and name!=%%s""" % DT_NGUON, (n.vendor, n.company, dau, n.name))
	return float(r[0][0] or 0) + float(them or 0) + float(frappe.db.get_value(DT_NGUON, n.name, "phi_vuot") or 0)


# ------------------------------------------------------------ duyệt, xác nhận

def _vai():
	return set(_frappe().get_roles())


def la_giam_doc():
	from vagabond.viec_can_lam import la_giam_doc as lg

	return lg(_vai())


TRUONG_DAU_NGUON = ("trang_thai", "duong_vao", "thuc_nhan", "so_dong", "trang_thai_tien", "giao_dich_ngan_hang",
	"kiem_so_du", "phi_vuot")
TRUONG_DAU_DONG = ("name", "trang_thai_khop", "sales_invoice", "purchase_invoice", "van_don", "thuc_nhan", "phi")


def dau_doi_chieu(n, dong):
	"""THUẦN. Codex #544 vòng 4: dấu của kết quả đối chiếu mà kế toán xác nhận:
	trạng thái, tiền, tiền về của nguồn và từng dòng nối với chứng từ nào. Đối
	chiếu lại ra kết quả khác (hoá đơn huỷ rồi nối hoá đơn thay, đổi giao dịch
	tiền về) thì dấu khác, xác nhận cũ hết hiệu lực."""
	lay = n.get if hasattr(n, "get") else (lambda k: getattr(n, k, None))

	def chuan(v):
		if isinstance(v, (int, float)):
			return int(round(float(v)))
		return "" if v is None else str(v)
	nguon = [chuan(lay(k)) for k in TRUONG_DAU_NGUON]
	ds = sorted([chuan((d.get if hasattr(d, "get") else (lambda k, d=d: getattr(d, k, None)))(k)) for k in TRUONG_DAU_DONG]
		for d in (dong or []))
	return hashlib.sha256(json.dumps([nguon, ds], ensure_ascii=False).encode("utf-8")).hexdigest()


def _dau_hien(name):
	frappe = _frappe()
	from vagabond import doi_soat_vendor as dsv

	n = frappe.db.get_value(DT_NGUON, name, list(TRUONG_DAU_NGUON), as_dict=True) or {}
	dong = frappe.get_all(dsv.DT_DONG, filters={"nguon": name}, fields=list(TRUONG_DAU_DONG), limit_page_length=0)
	return dau_doi_chieu(n, dong)


def kiem_xac_nhan(name):
	"""Codex #544 vòng 4: sau mỗi lần đối chiếu hay nối tay, xác nhận của kế toán
	chỉ còn hiệu lực khi kết quả đối chiếu đúng như lúc xác nhận. Khác thì gỡ
	xác nhận (ghi lại một dòng nhận xét trên nguồn để tra), nút Xác nhận mở lại
	khi năm bước xanh. Trả True khi đã gỡ."""
	frappe = _frappe()
	x = frappe.db.get_value(DT_NGUON, name, ["xac_nhan_luc", "xac_nhan_boi", "xac_nhan_dau"], as_dict=True)
	if not x or not x.xac_nhan_luc:
		return False
	if x.xac_nhan_dau and x.xac_nhan_dau == _dau_hien(name):
		return False
	frappe.db.set_value(DT_NGUON, name, {"xac_nhan_luc": None, "xac_nhan_boi": None, "xac_nhan_dau": ""}, update_modified=False)
	try:
		frappe.get_doc(dict(doctype="Comment", comment_type="Info", reference_doctype=DT_NGUON, reference_name=name,
			content="Xác nhận của %s lúc %s hết hiệu lực vì kết quả đối chiếu đã đổi. Kế toán xác nhận lại." % (
				x.xac_nhan_boi or "", str(x.xac_nhan_luc)[:16]))).insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(title="Đối soát: chưa ghi được nhận xét gỡ xác nhận %s" % name)
	return True


def con_cho_duyet(n):
	"""THUẦN. Nguồn còn ở trạng thái giám đốc duyệt hay từ chối được: Chờ duyệt,
	hoặc nguồn cũ chưa có đường vào mà không phải từ hộp thư."""
	lay = n.get if hasattr(n, "get") else (lambda k: getattr(n, k, None))
	if lay("duong_vao") not in (DV_CHO, None, ""):
		return False
	return not (lay("kenh_nhan") == KENH and not lay("duong_vao"))


def _doc_lai_trong_khoa(name):
	"""Codex #544 vòng 3: đọc lại nguồn SAU khi giữ khoá đối chiếu. Lượt đọc
	hộp thư có thể vừa nâng nguồn lên Từ thư (thư có chữ ký về đúng lúc giám
	đốc bấm), nên kết luận đọc trước khi chờ khoá là cũ."""
	frappe = _frappe()
	n = frappe.db.get_value(DT_NGUON, name, ["name", "duong_vao", "kenh_nhan", "thu"], as_dict=True)
	if not n or not con_cho_duyet(n):
		frappe.throw("Nguồn này vừa đổi (có thể thư có chữ ký số của đối tác đã về), không còn chờ duyệt. Tải lại màn hình.")
	return n


def _nguon_cho(name):
	frappe = _frappe()
	from vagabond import doi_soat_vendor as dsv

	dsv._chan()
	n = frappe.db.get_value(DT_NGUON, name, ["name", "company", "owner", "duong_vao", "kenh_nhan", "thu"], as_dict=True)
	if not n:
		frappe.throw("Không thấy nguồn đối soát này. Tải lại màn hình.")
	dsv._chan_cong_ty(n.company)
	return n


def duyet(name):
	frappe = _frappe()
	n = _nguon_cho(name)
	if not la_giam_doc():
		frappe.throw("Chỉ Giám đốc duyệt được tệp tải tay.", frappe.PermissionError)
	if n.owner == frappe.session.user and n.kenh_nhan != KENH:
		frappe.throw("Người tải tệp không tự duyệt được tệp của mình. Nhờ giám đốc còn lại duyệt.", frappe.PermissionError)
	if n.duong_vao not in (DV_CHO, None, ""):
		frappe.throw("Nguồn này không còn chờ duyệt. Tải lại màn hình.")
	if n.kenh_nhan == KENH and not n.duong_vao:
		frappe.throw("Nguồn này đã có chữ ký số của đối tác, không cần duyệt.")
	from vagabond import doi_soat_vendor as dsv

	with dsv.khoa_doi_chieu():
		n = _doc_lai_trong_khoa(name)
		frappe.db.set_value(DT_NGUON, name, {"duong_vao": DV_DA, "duyet_boi": frappe.session.user,
			"duyet_luc": frappe.utils.now_datetime(), "ly_do_duyet": ""}, update_modified=False)
		if n.thu:
			frappe.db.set_value(DT_THU, n.thu, "ket_qua", "Đã duyệt", update_modified=False)
	return dict(ok=1)


def tu_choi(name, ly_do=None):
	frappe = _frappe()
	from vagabond import doi_soat_vendor as dsv

	n = _nguon_cho(name)
	if not la_giam_doc():
		frappe.throw("Chỉ Giám đốc từ chối được tệp tải tay.", frappe.PermissionError)
	ly_do = (ly_do or "").strip()
	if len(ly_do) < 3:
		frappe.throw("Ghi lý do từ chối để người tải biết.")
	if n.duong_vao not in (DV_CHO, None, "") or (n.kenh_nhan == KENH and not n.duong_vao):
		frappe.throw("Nguồn này không còn chờ duyệt. Tải lại màn hình.")
	with dsv.khoa_doi_chieu():
		n = _doc_lai_trong_khoa(name)
		# Dòng của nguồn bị từ chối thôi tính (giữ để tra), để thư thật về sau
		# nhận được đúng các giao dịch đó.
		dsv._bo_dong_cu(name)
		frappe.db.set_value(DT_NGUON, name, {"duong_vao": DV_TU_CHOI, "duyet_boi": frappe.session.user,
			"duyet_luc": frappe.utils.now_datetime(), "ly_do_duyet": ly_do[:500], "so_da_noi": 0, "so_chua_noi": 0,
			"trang_thai_tien": "Không áp dụng", "giao_dich_ngan_hang": ""}, update_modified=False)
		if n.thu:
			frappe.db.set_value(DT_THU, n.thu, "ket_qua", "Từ chối", update_modified=False)
	return dict(ok=1)


def xac_nhan(name):
	frappe = _frappe()
	from vagabond.viec_can_lam import VAI_KE_TOAN

	_nguon_cho(name)
	if not (_vai() & VAI_KE_TOAN) and not la_giam_doc():
		frappe.throw("Chỉ Kế toán xác nhận được nguồn đối soát.", frappe.PermissionError)
	from vagabond import doi_soat_vendor as dsv

	with dsv.khoa_doi_chieu():
		# Codex #544 vòng 3: đọc các bước TRONG khoá, để giám đốc vừa từ chối
		# hay lượt đọc hộp thư vừa ghi lại thì không xác nhận trên số cũ.
		r = frappe.db.get_value(DT_NGUON, name, ["kenh_nhan", "duong_vao", "trang_thai", "nhom", "trang_thai_tien",
			"so_chua_noi", "so_da_noi", "kiem_so_du", "phi_vuot", "xac_nhan_luc"], as_dict=True)
		b = buoc_nguon(r)
		if not b["xac_nhan_duoc"]:
			frappe.throw("Chưa xác nhận được: %s." % b["ghi"])
		frappe.db.set_value(DT_NGUON, name, {"xac_nhan_boi": frappe.session.user, "xac_nhan_luc": frappe.utils.now_datetime(),
			"xac_nhan_dau": _dau_hien(name)}, update_modified=False)
	return dict(ok=1)


def viec_duyet():
	"""Việc cần làm của giám đốc: nguồn chờ duyệt (tải tay, thư không chữ ký)."""
	frappe = _frappe()
	from vagabond import doi_soat_vendor as dsv

	ra = []
	for x in frappe.get_all(DT_NGUON, filters=_pham_vi({"duong_vao": DV_CHO}, dsv._cong_ty_xem()), fields=["name", "vendor", "tu_ngay", "den_ngay",
			"thuc_nhan", "kenh_nhan", "owner", "creation"], order_by="creation asc", limit_page_length=60):
		cho = (frappe.utils.now_datetime() - x.creation).days if x.creation else 0
		ra.append({"loai": "doi_soat_duyet", "ma": x.name, "nhom": "Chờ giám đốc duyệt",
			"phu": "%s · %s · %s" % (x.vendor, ky_hien(x), "thư không chữ ký" if x.kenh_nhan == KENH else
				"tải tay bởi " + (frappe.utils.get_fullname(x.owner) or "")),
			"tien": float(x.thuc_nhan or 0), "ngay": str(x.den_ngay or x.tu_ngay or "")[:10],
			"tt": "tre_hen" if cho > 2 else "cho_duyet"})
	return ra


# ------------------------------------------------------------ màn hình

def _pham_vi(loc, cong_ty):
	"""Codex #544 F2: thêm lọc pháp nhân (danh sách pháp nhân người xem được).
	cong_ty None là lịch chạy ngầm (mọi pháp nhân)."""
	if cong_ty is not None:
		loc = dict(loc, company=["in", list(cong_ty) or [""]])
	return loc


def hop_thu_tom_tat(cong_ty=None):
	"""Khối Hộp thư trên màn chính: trạng thái và đếm hôm nay."""
	frappe = _frappe()
	ch = cau_hinh()
	tt = trang_thai()
	thieu = _thieu_hien(cong_ty)
	hom = frappe.utils.nowdate()
	ve = frappe.db.count(DT_THU, _pham_vi({"nhan_luc": [">=", hom], "ket_qua": ["in", [KQ_XAC_THUC, KQ_CHO, "Đã duyệt"]]}, cong_ty))
	chan = frappe.db.count(DT_THU, _pham_vi({"nhan_luc": [">=", frappe.utils.add_days(hom, -7)],
		"ket_qua": ["in", [KQ_CHAN, KQ_LOI]]}, cong_ty))
	cho = frappe.db.count(DT_NGUON, _pham_vi({"duong_vao": DV_CHO}, cong_ty))
	if not ch["bat"]:
		trang = "tat"
	elif tt.get("loi"):
		trang = "loi"
	elif not tt.get("doc_luc"):
		trang = "chua"
	else:
		trang = "chay"
	return dict(trang=trang, dia_chi=ch["dia_chi"], doc_luc=tt.get("doc_luc") or "", loi=tt.get("loi") or "",
		ve_hom_nay=ve, chua_ve=len(thieu), bi_chan=chan, cho_duyet=cho, thieu=thieu[:20],
		quan_tri=1 if "System Manager" in _vai() else 0, giam_doc=1 if la_giam_doc() else 0)


def _nguon_gan_day(so_ngay=40, cong_ty=None):
	frappe = _frappe()
	return frappe.get_all(DT_NGUON, filters=_pham_vi({"den_ngay": [">=", frappe.utils.add_days(frappe.utils.nowdate(), -so_ngay)],
		"duong_vao": ["!=", DV_TU_CHOI]}, cong_ty), fields=["vendor", "tai_khoan", "tu_ngay", "den_ngay", "kenh_nhan"],
		limit_page_length=0)


def _thieu_hien(cong_ty=None):
	frappe = _frappe()
	ch = cau_hinh()
	if not ch["bat"]:
		return []
	bay = frappe.utils.now_datetime()
	return thu_thieu(ch["lich"], bay.date(), bay.hour, _nguon_gan_day(cong_ty=cong_ty), trang_thai().get("ngay_bat"))


def ds_thu(loai="chan", cong_ty=None):
	"""Ba thẻ của màn Thư bị chặn / Chưa về / Tải tay, trong phạm vi pháp nhân."""
	frappe = _frappe()
	if loai == "chua_ve":
		return dict(ds=_thieu_hien(cong_ty))
	if loai == "tai_tay":
		return dict(ds=frappe.get_all(DT_NGUON, filters=_pham_vi({"duong_vao": DV_CHO}, cong_ty), fields=["name", "vendor", "tu_ngay",
			"den_ngay", "so_dong", "thuc_nhan", "kenh_nhan", "ly_do_tai_tay", "owner", "creation", "trang_thai",
			"trang_thai_tien", "nhom", "so_chua_noi", "so_da_noi", "duong_vao"], order_by="creation desc", limit_page_length=100))
	return dict(ds=frappe.get_all(DT_THU, filters=_pham_vi({"ket_qua": ["in", [KQ_CHAN, KQ_LOI]], "nhan_luc": [">=", frappe.utils.add_days(
		frappe.utils.nowdate(), -30)]}, cong_ty), fields=["name", "nguoi_gui", "ten_mien", "tieu_de", "nhan_luc", "gui_luc", "doi_tac",
		"ly_do", "so_tep", "bao_zalo", "ket_qua"], order_by="nhan_luc desc", limit_page_length=100))


def thu_goc(name):
	frappe = _frappe()
	url = frappe.db.get_value(DT_THU, name, "tep_goc")
	if not url:
		frappe.throw("Thư này không lưu bản gốc (quá 30 MB).")
	f = frappe.get_doc("File", {"file_url": url, "attached_to_doctype": DT_THU, "attached_to_name": name})
	b = f.get_content()
	b = b if isinstance(b, bytes) else b.encode("utf-8")
	return dict(ten=f.file_name, noi_dung=base64.b64encode(b).decode())


def khop_doc_lai(trang_thai):
	from vagabond import doi_soat_khop

	return doi_soat_khop.doc_lai_duoc(trang_thai)


def doc_lai_thu(name):
	"""Nút "Đọc lại thư" trên thư "Lỗi xử lý" (Codex #544 vòng 2): chạy lại đúng
	đường của lượt đọc hộp thư trên bản gốc .eml đã cất (cùng mã băm nên dùng
	tiếp dòng sổ thư, không tạo bản trùng; tệp đã nhận dừng ở mã băm). Quyền và
	pháp nhân kiểm ở cổng gọi. Khoá chung với lượt đọc hộp thư.

	v643: thư "Bị chặn" cũng kiểm lại được (nút Kiểm lại thư), vì chặn có thể do
	Cài đặt lúc đó (chưa khai hộp nội bộ) hay do lỗi kiểm chữ ký đã sửa (GreenSM
	06/11/2026). Kiểm lại chạy ĐÚNG đường của thư mới: chữ ký, người gửi theo
	Cài đặt hiện tại; vẫn không đạt thì vẫn bị chặn. Thư đã xác thực mà còn
	nguồn đang lỗi hay cần xử lý (mẫu đọc vừa sửa, như ShopeeFood 06/11/2026) thì
	đọc lại được để đọc lại tệp; nguồn đã đúng dừng ở mã băm như cũ."""
	frappe = _frappe()
	from vagabond.doi_soat_dkim import LoiDnsTam

	t = frappe.db.get_value(DT_THU, name, ["name", "ket_qua", "xong", "tep_goc", "uid"], as_dict=True)
	if not t:
		frappe.throw("Không thấy thư này. Tải lại màn hình.")
	if not ((t.ket_qua == KQ_LOI and not t.xong) or t.ket_qua == KQ_CHAN or (t.ket_qua == KQ_XAC_THUC
			and any(khop_doc_lai(x) for x in frappe.get_all(DT_NGUON, filters={"thu": name}, pluck="trang_thai")))):
		frappe.throw("Thư này đã xử lý xong, không cần đọc lại.")
	if not t.tep_goc:
		frappe.throw("Thư này không lưu được bản gốc nên không đọc lại được. Nhờ đối tác gửi lại thư.")
	f = frappe.get_doc("File", {"file_url": t.tep_goc, "attached_to_doctype": DT_THU, "attached_to_name": name})
	tho = f.get_content()
	tho = tho if isinstance(tho, bytes) else tho.encode("utf-8")
	if hashlib.sha256(tho).hexdigest() != frappe.db.get_value(DT_THU, name, "sha256"):
		frappe.throw("Bản gốc của thư này không còn khớp, không đọc lại được. Nhờ đối tác gửi lại thư.")
	r = frappe.db.sql("select get_lock('vgb_ds_hop_thu', 30)")
	if not r or r[0][0] != 1:
		frappe.throw("Máy đang đọc hộp thư. Đợi một phút rồi bấm lại.")
	try:
		try:
			_xu_ly(tho, t.uid, cau_hinh(), kiem_lai=t.ket_qua != KQ_LOI, giu_xac_thuc=t.ket_qua == KQ_XAC_THUC)
			frappe.db.commit()
		except LoiDnsTam:
			frappe.db.rollback()
			frappe.throw("Vẫn chưa tra được khoá chữ ký số của đối tác (mạng hoặc DNS lỗi tạm). Thử lại sau ít phút.")
		except Exception as e:
			if isinstance(e, frappe.ValidationError):
				raise
			frappe.db.rollback()
			frappe.log_error(title="Đối soát hộp thư: đọc lại thư %s" % name)
			frappe.throw("Đọc lại vẫn lỗi: %s. Báo kỹ thuật kèm tên thư %s." % (str(e)[:200], name))
	finally:
		frappe.db.sql("select release_lock('vgb_ds_hop_thu')")
	return frappe.db.get_value(DT_THU, name, ["ket_qua", "ly_do"], as_dict=True)


def can_cu(n):
	"""Khối Căn cứ thư gốc của một nguồn."""
	frappe = _frappe()
	if not n.get("thu"):
		return None
	t = frappe.db.get_value(DT_THU, n["thu"], ["name", "nguoi_gui", "nhan_luc", "gui_luc", "ky_boi", "ket_qua", "ly_do",
		"sha256", "tieu_de"], as_dict=True)
	return dict(t) if t else None


# ------------------------------------------------------------ lịch nhắc

def con_thieu_thu(nguon=None):
	"""DIEU_KIEN "ds_thieu_thu": tin thiếu thư còn đúng lúc gửi không. Tin bị
	giữ qua giờ im mà lúc gửi mọi thư đã về thì bỏ. (Ô nguồn của sổ tin chỉ 140
	ký tự nên không mang danh sách khoá; xét lại toàn bộ thư chưa về.)"""
	return bool(_thieu_hien())


def nhac_thieu_thu():
	"""12:30 và 17:00 mỗi ngày."""
	frappe = _frappe()
	try:
		ds = _thieu_hien()
		if not ds:
			return
		bay = frappe.utils.now_datetime()
		lan = 1 if bay.hour < 15 else 2
		from vagabond import kenh_zalo

		t, d = tin_thieu_thu(ds, lan)
		kenh_zalo.bao_hoac_ghi_loi("viec", "cong_no", t, d, link=_link(), khoa="ds_thieu:%s:%s" % (bay.date(), lan),
			kiem="ds_thieu_thu", nguon=str(bay.date()), ma_tin="kt_ds_thieu_thu")
	except Exception:
		frappe.log_error(title="Đối soát hộp thư: nhắc thư chưa về")


def nhac_sang():
	"""08:30 mỗi sáng: tiền chưa về quá hạn, giao dịch đối tác chưa có đơn."""
	frappe = _frappe()
	from vagabond import kenh_zalo

	hom = frappe.utils.nowdate()
	try:
		ds = [dict(vendor=x.vendor, ky=ky_hien(x), tien=float(x.thuc_nhan or 0)) for x in frappe.get_all(DT_NGUON,
			filters={"trang_thai_tien": "Chưa thấy tiền về", "ngay_tien_ve": ["<", hom], "duong_vao": ["!=", DV_TU_CHOI],
				"den_ngay": [">=", frappe.utils.add_days(hom, -45)]},
			fields=["vendor", "tu_ngay", "den_ngay", "thuc_nhan"], order_by="den_ngay asc", limit_page_length=50)]
		if ds:
			t, d = tin_chua_thay_tien(ds)
			kenh_zalo.bao_hoac_ghi_loi("viec", "cong_no", t, d, link=_link(), khoa="ds_chua_tien:%s" % hom,
				ma_tin="kt_ds_chua_thay_tien")
	except Exception:
		frappe.log_error(title="Đối soát hộp thư: nhắc tiền chưa về")
	try:
		hqua = frappe.utils.add_days(hom, -1)
		ds = [dict(vendor=x.vendor, ngay=str(x.ngay), gio=str(x.gio or ""), tien=float(x.tien_hang or 0))
			for x in frappe.get_all("Vagabond Doi Soat Dong", filters={"ngay": hqua, "nhom": "Tiền bán", "loai": "ban",
				"trang_thai_khop": "Không thấy chứng từ", "nguon": ["is", "set"]},
				fields=["vendor", "ngay", "gio", "tien_hang"], order_by="gio asc", limit_page_length=200)]
		if ds:
			t, d = tin_don_thieu_erp(ds)
			kenh_zalo.bao_hoac_ghi_loi("viec", "cong_no", t, d, link=_link(), khoa="ds_thieu_erp:%s" % hqua,
				ma_tin="kt_ds_don_thieu_erp")
	except Exception:
		frappe.log_error(title="Đối soát hộp thư: nhắc giao dịch chưa có đơn")


def thu_ket_noi():
	"""Nút Thử kết nối (quản trị): đăng nhập, mở thư mục, đếm thư. Không đọc thư."""
	frappe = _frappe()
	if "System Manager" not in _vai():
		frappe.throw("Chỉ quản trị thử kết nối hộp thư.", frappe.PermissionError)
	ch = cau_hinh()
	try:
		m = _ket_noi(ch)
		try:
			_chon_thu_muc(m, ch["thu_muc"])
			kq, du = m.uid("search", None, "ALL")
			so = len((du[0] or b"").split()) if kq == "OK" else 0
		finally:
			try:
				m.logout()
			except Exception:
				pass
	except Exception as e:
		return dict(ok=0, loi=ly_do_imap(e) if not isinstance(e, RuntimeError) else str(e))
	return dict(ok=1, so_thu=so)
