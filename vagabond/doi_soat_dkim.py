# -*- coding: utf-8 -*-
"""v641: kiểm chữ ký số DKIM của thư đối soát. THUẦN, không cần thư viện ngoài.

Anh Việt 06/11/2026 duyệt luồng "đối soát tự động qua hộp thư doisoat@": số
liệu chỉ được vào ERP từ thư có chữ ký số của đúng tên miền đối tác (OnePay ký
bằng onepay.vn...). Ô "người gửi" của thư ai cũng ghi giả được; chữ ký DKIM thì
không, vì sửa một byte của phần đã ký là chữ ký hỏng.

Vì sao tự viết chứ không dùng dkimpy: dkimpy chỉ phát hành dạng mã nguồn, dựng
gói hỏng trên setuptools mới (thử 06/11/2026), mà một gói dựng hỏng là cả lần
deploy Frappe Cloud hỏng. Phần cần dùng lại hẹp và có chuẩn rõ (RFC 6376):
  - chuẩn hoá tiêu đề và thân thư kiểu simple, relaxed;
  - băm SHA-256, kiểm chữ ký RSA PKCS#1 v1.5 bằng phép luỹ thừa mô-đun của
    Python (chỉ KIỂM, không ký, không giữ khoá bí mật nào);
  - đọc khoá công khai DER (SubjectPublicKeyInfo hoặc RSAPublicKey).
Ca kiểm dùng thư do dkimpy KÝ THẬT (bộ ký độc lập với bộ kiểm này) làm mẫu.

Siết chặt hơn mức tối thiểu của chuẩn, vì đây là cửa nhận tiền:
  - chỉ nhận a=rsa-sha256 (rsa-sha1 đã bị RFC 8301 bỏ); ed25519 chưa hỗ trợ
    thì coi như chữ ký đó không kiểm được (thư thường ký kèm RSA);
  - thẻ l= (chỉ ký một phần thân thư) mà thân thư dài hơn phần đã ký thì KHÔNG
    nhận: kẻ gian có thể nối thêm tệp vào sau phần đã ký;
  - h= phải có From; khoá dưới 1024 bit không nhận; khoá đã thu hồi (p= rỗng)
    không nhận; x= quá hạn không nhận;
  - so khớp chữ ký byte với byte sau khi dựng lại khối mã hoá chuẩn, không
    "đọc mềm" phần đệm (chặn kiểu giả chữ ký Bleichenbacher với e nhỏ).
"""

import base64
import hashlib
import re
import time

TOI_THIEU_BIT = 1024
# DigestInfo của SHA-256 (RFC 8017 mục 9.2, ghi chú 1).
DIGEST_SHA256 = bytes.fromhex("3031300d060960864801650304020105000420")
_WSP = re.compile(rb"[\t ]+")


class LoiChuKy(Exception):
	"""Chữ ký không hợp lệ hoặc không kiểm được; thông điệp viết cho kế toán."""


class LoiDnsTam(Exception):
	"""Codex #544 vòng 2: tra khoá công khai lỗi TẠM (hết giờ, máy chủ DNS lỗi,
	mất mạng). Khác hẳn "không có khoá": thư phải được đọc lại sau, không được
	kết luận là thư giả. Không kế thừa LoiChuKy hay ValueError để không bị các
	nhánh bắt lỗi chữ ký nuốt mất."""


# ------------------------------------------------------------ tách thư

def tach_thu(tho):
	"""(danh sách tiêu đề [(tên, giá trị kể cả CRLF)], thân thư CRLF). THUẦN.

	Thư lấy qua IMAP luôn dùng CRLF; thư chỉ có LF (ca kiểm, tệp lưu lại) được
	đổi sang CRLF trước khi tách."""
	if not isinstance(tho, (bytes, bytearray)):
		raise LoiChuKy("Thư gốc không phải dạng byte.")
	tho = bytes(tho)
	if b"\r\n" not in tho:
		tho = tho.replace(b"\n", b"\r\n")
	dong = tho.split(b"\r\n")
	tieu_de, i = [], 0
	while i < len(dong):
		d = dong[i]
		if d == b"":
			i += 1
			break
		if d[:1] in (b" ", b"\t") and tieu_de:
			tieu_de[-1][1] += d + b"\r\n"
		else:
			m = re.match(rb"([\x21-\x39\x3b-\x7e]+)[ \t]*:", d)
			if m:
				tieu_de.append([m.group(1), d[m.end(1):] + b"\r\n"])
		i += 1
	# Giá trị giữ cả dấu hai chấm ở đầu để dựng lại đúng byte kiểu simple.
	tieu_de = [(t, v[v.index(b":") + 1:], v[:v.index(b":")]) for t, v in tieu_de]
	than = b"\r\n".join(dong[i:])
	return tieu_de, than


# ------------------------------------------------------------ chuẩn hoá

def chuan_tieu_de(ten, gia_tri, kieu, khoang=b""):
	"""Một trường tiêu đề đã chuẩn hoá, kết thúc bằng CRLF. THUẦN.

	khoang: khoảng trắng giữa tên và dấu hai chấm của thư gốc (kiểu simple
	giữ nguyên từng byte)."""
	if kieu == "simple":
		return ten + khoang + b":" + gia_tri
	v = re.sub(rb"\r\n", b"", gia_tri)
	v = _WSP.sub(b" ", v).strip(b" ")
	return ten.lower() + b":" + v + b"\r\n"


def chuan_than(than, kieu):
	"""Thân thư đã chuẩn hoá. THUẦN."""
	if kieu == "relaxed":
		than = re.sub(rb"[\t ]+\r\n", b"\r\n", than)
		than = _WSP.sub(b" ", than)
	while than.endswith(b"\r\n\r\n"):
		than = than[:-2]
	if than == b"\r\n":
		than = b""
	if than and not than.endswith(b"\r\n"):
		than += b"\r\n"
	if not than and kieu == "simple":
		than = b"\r\n"
	return than


def chon_tieu_de(tieu_de, h):
	"""Các trường được ký theo danh sách h= (đọc từ dưới lên, mỗi tên dùng
	lần lượt). THUẦN. tieu_de: [(tên, giá trị, khoảng)]."""
	ra, cuoi = [], {}
	for ten in h:
		i = cuoi.get(ten, len(tieu_de))
		while i > 0:
			i -= 1
			if tieu_de[i][0].lower() == ten:
				ra.append(tieu_de[i])
				break
		cuoi[ten] = i
	return ra


# ------------------------------------------------------------ thẻ

def doc_the(gia_tri):
	"""Danh sách thẻ tag=value của DKIM-Signature hay bản ghi khoá. THUẦN."""
	v = re.sub(rb"\r\n", b"", gia_tri if isinstance(gia_tri, bytes) else gia_tri.encode("latin-1"))
	ra = {}
	for phan in v.strip().split(b";"):
		if not phan.strip():
			continue
		if b"=" not in phan:
			raise LoiChuKy("Chữ ký số viết sai cú pháp.")
		k, x = phan.split(b"=", 1)
		k = k.strip().decode("latin-1")
		if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", k):
			raise LoiChuKy("Chữ ký số viết sai cú pháp.")
		if k in ra:
			raise LoiChuKy("Chữ ký số lặp thẻ %s." % k)
		ra[k] = x.strip()
	return ra


def bo_gia_tri_b(gia_tri):
	"""Giá trị DKIM-Signature với thẻ b= để rỗng (giữ nguyên mọi byte khác). THUẦN."""
	phan = gia_tri.split(b";")
	ra = []
	for p in phan:
		m = re.match(rb"^([\t \r\n]*b[\t \r\n]*=)", p)
		ra.append(m.group(1) if m else p)
	return b";".join(ra)


def _b64(x):
	return base64.b64decode(re.sub(rb"[\t \r\n]", b"", x) + b"===", validate=False)


# ------------------------------------------------------------ khoá công khai

def _der_doc(b, i):
	"""(thẻ, nội dung, vị trí sau) của một phần tử DER tại i."""
	if i + 2 > len(b):
		raise LoiChuKy("Khoá công khai hỏng.")
	the, dai = b[i], b[i + 1]
	i += 2
	if dai & 0x80:
		so = dai & 0x7F
		if not 0 < so <= 4 or i + so > len(b):
			raise LoiChuKy("Khoá công khai hỏng.")
		dai = int.from_bytes(b[i:i + so], "big")
		i += so
	if i + dai > len(b):
		raise LoiChuKy("Khoá công khai hỏng.")
	return the, b[i:i + dai], i + dai


def khoa_rsa(der):
	"""(n, e) từ SubjectPublicKeyInfo hoặc RSAPublicKey dạng DER. THUẦN."""
	the, nd, _ = _der_doc(der, 0)
	if the != 0x30:
		raise LoiChuKy("Khoá công khai hỏng.")
	t1, n1, sau = _der_doc(nd, 0)
	if t1 == 0x30:
		# SubjectPublicKeyInfo: thuật toán rồi BIT STRING chứa RSAPublicKey.
		t2, bit, _ = _der_doc(nd, sau)
		if t2 != 0x03 or not bit or bit[0] != 0:
			raise LoiChuKy("Khoá công khai hỏng.")
		if b"\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01" not in n1:
			raise LoiChuKy("Khoá công khai không phải RSA.")
		return khoa_rsa(bit[1:])
	if t1 != 0x02:
		raise LoiChuKy("Khoá công khai hỏng.")
	t2, e, _ = _der_doc(nd, sau)
	if t2 != 0x02:
		raise LoiChuKy("Khoá công khai hỏng.")
	return int.from_bytes(n1, "big"), int.from_bytes(e, "big")


def kiem_rsa(n, e, chu_ky, du_lieu):
	"""RSASSA-PKCS1-v1_5 với SHA-256, so khớp khối mã hoá byte với byte. THUẦN."""
	k = (n.bit_length() + 7) // 8
	if n.bit_length() < TOI_THIEU_BIT:
		raise LoiChuKy("Khoá chữ ký quá ngắn (%s bit), không đủ tin cậy." % n.bit_length())
	if len(chu_ky) != k:
		return False
	s = int.from_bytes(chu_ky, "big")
	if s >= n:
		return False
	em = pow(s, e, n).to_bytes(k, "big")
	t = DIGEST_SHA256 + hashlib.sha256(du_lieu).digest()
	if k < len(t) + 11:
		return False
	mong = b"\x00\x01" + b"\xff" * (k - len(t) - 3) + b"\x00" + t
	return em == mong


# ------------------------------------------------------------ thư qua bộ lọc chuyển tiếp

def o_sender_bu(tieu_de, h, kieu):
	"""THUẦN (v643). Ô Sender dựng lại cho thư đã đi qua bộ lọc chuyển tiếp của
	máy chủ thư của tiệm (Roundcube/Sieve chuyển account@ sang doisoat@).

	Thư GreenSM 06/11/2026 gửi qua Mailgun có "Sender: no-reply@greensm.com" và
	ký cả ô đó; khi bộ lọc chuyển thư sang hộp doisoat@, máy chủ (Exim, gửi lại
	như thư nội bộ) gỡ ô Sender nên chữ ký không còn khớp, dù SpamAssassin lúc
	thư vào account@ ghi DKIM_VALID. Cách bù hẹp nhất có thể:
	  - chỉ khi h= có ký Sender mà thư KHÔNG còn ô Sender nào;
	  - chỉ kiểu chuẩn hoá relaxed (kiểu simple cần đúng từng byte gốc);
	  - chỉ thử đúng địa chỉ trong ô From (bản trơn và nguyên văn ô From).
	Ô bù vẫn phải qua phép kiểm RSA với khoá của đối tác cùng mọi ô khác, nên
	không ai dựng được thư giả bằng cách này: khớp nghĩa là đối tác đã ký đúng
	thư này cùng ô Sender đó."""
	if kieu != "relaxed" or b"sender" not in h or any(x[0].lower() == b"sender" for x in tieu_de):
		return []
	tu = [x for x in tieu_de if x[0].lower() == b"from"]
	if len(tu) != 1:
		return []
	v = re.sub(rb"\r\n", b"", tu[0][1])
	v = _WSP.sub(b" ", v).strip(b" ")
	m = re.search(rb"<([^<>\s]+@[^<>\s]+)>", v)
	dc = m.group(1) if m else (v if re.fullmatch(rb"[^<>\s]+@[^<>\s]+", v) else b"")
	ung = []
	for x in (dc, v):
		if x and x not in ung:
			ung.append(x)
	return [(b"Sender", b" " + x + b"\r\n", b"") for x in ung]


def luc_nhan(tho):
	"""THUẦN (v643). Giờ máy chủ thư của tiệm nhận thư (epoch giây), đọc từ ô
	Received TRÊN CÙNG: ô này do máy chủ của tiệm thêm sau cùng, người gửi không
	viết được. Không đọc được thì None.

	Dùng làm mốc kiểm hạn x= của chữ ký: Mailgun ký hạn 2 giờ, nên bấm Kiểm lại
	thư sau đó mà so với giờ hiện tại là thư thật thành "hết hạn"."""
	from email.utils import parsedate_to_datetime

	try:
		tieu_de, _than = tach_thu(tho)
	except LoiChuKy:
		return None
	for ten, gia_tri, _k in tieu_de:
		if ten.lower() != b"received":
			continue
		v = re.sub(rb"\r\n", b"", gia_tri).decode("latin-1")
		if ";" not in v:
			return None
		try:
			return int(parsedate_to_datetime(v.rsplit(";", 1)[1].strip()).timestamp())
		except (TypeError, ValueError, IndexError):
			return None
	return None


# ------------------------------------------------------------ kiểm một chữ ký

def kiem_mot(tieu_de, than, chi_so, lay_khoa, bay_gio=None):
	"""Kiểm chữ ký DKIM thứ chi_so (theo thứ tự xuất hiện). THUẦN với lay_khoa.

	lay_khoa(ten_dns) trả chuỗi bản ghi TXT (bytes) hoặc None.
	Trả dict(d=tên miền ký, s=selector, dat=True/False, ly_do=câu tiếng Việt,
	tam=True khi chưa kết luận được vì tra khoá lỗi tạm: lay_khoa ném LoiDnsTam)."""
	sig = [x for x in tieu_de if x[0].lower() == b"dkim-signature"]
	ten, gia_tri, khoang = sig[chi_so]
	ra = dict(d="", s="", dat=False, ly_do="")
	try:
		t = doc_the(gia_tri)
		ra["d"] = t.get("d", b"").decode("latin-1").lower()
		ra["s"] = t.get("s", b"").decode("latin-1")
		for can in ("v", "a", "b", "bh", "d", "h", "s"):
			if can not in t:
				raise LoiChuKy("Chữ ký số thiếu thẻ %s=." % can)
		if t["v"] != b"1":
			raise LoiChuKy("Chữ ký số khác phiên bản 1.")
		if t["a"].lower() != b"rsa-sha256":
			raise LoiChuKy("Chữ ký số dùng thuật toán %s, máy chỉ nhận rsa-sha256." % t["a"].decode("latin-1"))
		h = [x.strip().lower() for x in re.sub(rb"[\t \r\n]", b"", t["h"]).split(b":") if x.strip()]
		if b"from" not in h:
			raise LoiChuKy("Chữ ký số không ký ô người gửi (From).")
		c = (t.get("c") or b"simple/simple").lower().split(b"/")
		kh, kt = (c + [b"simple"])[:2]
		if kh not in (b"simple", b"relaxed") or kt not in (b"simple", b"relaxed"):
			raise LoiChuKy("Chữ ký số dùng kiểu chuẩn hoá lạ.")
		kh, kt = kh.decode(), kt.decode()
		if "i" in t:
			i_mien = t["i"].split(b"@")[-1].lower().decode("latin-1")
			if not (i_mien == ra["d"] or i_mien.endswith("." + ra["d"])):
				raise LoiChuKy("Thẻ i= không thuộc tên miền ký.")
		bay = int(bay_gio if bay_gio is not None else time.time())
		if "x" in t:
			try:
				het = int(t["x"])
			except ValueError:
				raise LoiChuKy("Thẻ hết hạn x= sai.") from None
			if het < bay:
				raise LoiChuKy("Chữ ký số đã hết hạn.")
		# Thân thư.
		cb = chuan_than(than, kt)
		if "l" in t:
			try:
				l_ = int(t["l"])
			except ValueError:
				raise LoiChuKy("Thẻ độ dài l= sai.") from None
			if l_ != len(cb):
				raise LoiChuKy("Chữ ký chỉ ký một phần thân thư (l=); phần sau có thể bị thêm vào.")
		if base64.b64encode(hashlib.sha256(cb).digest()) != re.sub(rb"[\t \r\n]", b"", t["bh"]):
			raise LoiChuKy("Thân thư hoặc tệp đính kèm đã bị sửa sau khi đối tác ký.")
		# Khoá.
		txt = lay_khoa("%s._domainkey.%s" % (ra["s"], ra["d"]))
		if not txt:
			raise LoiChuKy("Không tìm thấy khoá công khai của %s (bản ghi %s._domainkey)." % (ra["d"], ra["s"]))
		k = doc_the(txt if isinstance(txt, bytes) else txt.encode("latin-1"))
		if k.get("v", b"DKIM1") != b"DKIM1":
			raise LoiChuKy("Bản ghi khoá sai phiên bản.")
		if k.get("k", b"rsa").lower() != b"rsa":
			raise LoiChuKy("Khoá không phải RSA.")
		if not k.get("p"):
			raise LoiChuKy("Khoá chữ ký đã bị đối tác thu hồi.")
		if b"s" in [x.strip() for x in k.get("t", b"").split(b":")] and "i" in t:
			i_mien = t["i"].split(b"@")[-1].lower().decode("latin-1")
			if i_mien != ra["d"]:
				raise LoiChuKy("Khoá chỉ cho phép ký đúng tên miền.")
		n, e = khoa_rsa(_b64(k["p"]))
		# Tiêu đề.
		chu_ky_b = _b64(t["b"])
		dong_ky = chuan_tieu_de(ten, bo_gia_tri_b(gia_tri), kh, khoang).rstrip(b"\r\n")

		def _khop(ds):
			du_lieu = b"".join(chuan_tieu_de(a, b, kh, kk) for a, b, kk in chon_tieu_de(ds, h)) + dong_ky
			return kiem_rsa(n, e, chu_ky_b, du_lieu)
		if not _khop(tieu_de):
			bu = [x for x in o_sender_bu(tieu_de, h, kh) if _khop(tieu_de + [x])]
			if not bu:
				raise LoiChuKy("Chữ ký không khớp: tiêu đề thư đã bị sửa hoặc thư không phải do %s ký." % ra["d"])
			ra["ghi_chu"] = ("Máy chủ thư của tiệm đã gỡ ô Sender khi chuyển tiếp từ hộp khác sang; "
				"thêm lại ô đó bằng đúng địa chỉ người gửi thì chữ ký khớp.")
		ra["dat"] = True
	except LoiChuKy as er:
		ra["ly_do"] = str(er)
	except LoiDnsTam as er:
		ra["tam"] = True
		ra["ly_do"] = "Chưa tra được khoá công khai của %s (mạng hoặc DNS lỗi tạm: %s), máy sẽ thử lại." % (
			ra["d"] or "đối tác", str(er)[:120])
	except (ValueError, TypeError, IndexError, UnicodeDecodeError):
		ra["ly_do"] = "Chữ ký số viết sai cú pháp."
	return ra


def kiem_thu(tho, lay_khoa, bay_gio=None):
	"""Kiểm MỌI chữ ký DKIM trong thư. THUẦN với lay_khoa. Trả danh sách kết
	quả (rỗng khi thư không có chữ ký nào)."""
	tieu_de, than = tach_thu(tho)
	so = len([x for x in tieu_de if x[0].lower() == b"dkim-signature"])
	return [kiem_mot(tieu_de, than, i, lay_khoa, bay_gio) for i in range(min(so, 8))]


# ------------------------------------------------------------ ARC (v651, thư chuyển qua Gmail)

# Anh Việt 12/11/2026 (hướng B): thư Shinhan ký DKIM hỏng ngay từ phía Shinhan
# (Gmail ghi "body hash did not verify") nhưng Gmail của tiệm xác nhận máy chủ
# Shinhan được phép gửi (SPF đạt). Gmail ghi kết quả đó vào ARC-Authentication-
# Results và KÝ bằng khoá google.com (ARC-Seal, RFC 8617). Chỉ tin chuỗi ARC
# mà MỌI bộ do google.com niêm phong và mx.google.com ghi.
ARC_TIN = "google.com"
ARC_MAY_GHI = "mx.google.com"
ARC_TOI_DA = 50


def _arc_bo(tieu_de):
	"""{i: {"aar": (tên, giá trị, khoảng), "ams": ..., "as": ...}} và thẻ đã đọc.
	Ném LoiChuKy khi bộ ARC sai cấu trúc (thiếu, lặp, i lạ). THUẦN."""
	ten_kieu = {b"arc-authentication-results": "aar", b"arc-message-signature": "ams", b"arc-seal": "as"}
	bo = {}
	for x in tieu_de:
		k = ten_kieu.get(x[0].lower())
		if not k:
			continue
		if k == "aar":
			m = re.match(rb"\s*i\s*=\s*(\d+)\s*;", re.sub(rb"\r\n", b"", x[1]))
			i = int(m.group(1)) if m else 0
		else:
			try:
				i = int(doc_the(x[1]).get("i", b"0"))
			except ValueError:
				i = 0
		if not 1 <= i <= ARC_TOI_DA:
			raise LoiChuKy("Chuỗi ARC có số thứ tự i= sai.")
		if k in bo.setdefault(i, {}):
			raise LoiChuKy("Chuỗi ARC lặp bộ i=%s." % i)
		bo[i][k] = x
	if not bo:
		return {}
	n = max(bo)
	if sorted(bo) != list(range(1, n + 1)) or any(len(bo[i]) != 3 for i in bo):
		raise LoiChuKy("Chuỗi ARC thiếu bộ hoặc thiếu ô.")
	return bo


def _khoa_arc(t, lay_khoa):
	d = t.get("d", b"").decode("latin-1").lower()
	s = t.get("s", b"").decode("latin-1")
	txt = lay_khoa("%s._domainkey.%s" % (s, d))
	if not txt:
		raise LoiChuKy("Không tìm thấy khoá công khai ARC của %s." % d)
	k = doc_the(txt if isinstance(txt, bytes) else txt.encode("latin-1"))
	if k.get("k", b"rsa").lower() != b"rsa" or not k.get("p"):
		raise LoiChuKy("Khoá ARC của %s không dùng được." % d)
	return khoa_rsa(_b64(k["p"]))


def spf_dat_aar(gia_tri):
	"""THUẦN. Tên miền smtp.mailfrom khi ô ARC-Authentication-Results ghi đúng MỘT
	kết quả spf và kết quả đó là pass; còn lại trả "". Bỏ phần chú thích trong
	ngoặc trước khi tách theo dấu chấm phẩy (chú thích là chữ tự do)."""
	v = gia_tri.decode("latin-1") if isinstance(gia_tri, bytes) else str(gia_tri)
	v = re.sub(r"\r\n", "", v)
	for _ in range(3):
		v = re.sub(r"\([^()]*\)", " ", v)
	spf = [p.strip() for p in v.split(";") if re.match(r"\s*spf\s*=", p, re.I)]
	if len(spf) != 1:
		return ""
	m = re.match(r"spf\s*=\s*pass\s+smtp\.mailfrom\s*=\s*\"?([^\s\"]+)\"?\s*$", spf[0], re.I)
	if not m:
		return ""
	return m.group(1).split("@")[-1].strip().lower().rstrip(".")


def kiem_arc(tho, lay_khoa):
	"""Kiểm chuỗi ARC của thư. THUẦN với lay_khoa. Trả dict(dat, spf_mien,
	ly_do, tam). dat=True chỉ khi:
	  - mọi bộ ARC do google.com niêm phong, mx.google.com ghi;
	  - ARC-Seal mọi bộ khớp chữ ký (cv=none ở bộ 1, pass ở các bộ sau);
	  - ARC-Message-Signature của bộ cuối khớp (thân thư và các ô đã ký, có From);
	  - bộ 1 (lúc thư vào Gmail từ ngoài) ghi spf=pass, lấy tên miền smtp.mailfrom.
	"""
	ra = dict(dat=False, spf_mien="", ly_do="", tam=False)
	try:
		tieu_de, than = tach_thu(tho)
		bo = _arc_bo(tieu_de)
		if not bo:
			raise LoiChuKy("Thư không có chuỗi ARC.")
		n = max(bo)
		the = {}
		for i in bo:
			for k in ("ams", "as"):
				t = doc_the(bo[i][k][1])
				for can in ("a", "b", "d", "s"):
					if can not in t:
						raise LoiChuKy("Chuỗi ARC thiếu thẻ %s=." % can)
				if t["a"].lower() != b"rsa-sha256":
					raise LoiChuKy("Chuỗi ARC dùng thuật toán lạ.")
				if t["d"].lower().decode("latin-1") != ARC_TIN:
					raise LoiChuKy("Chuỗi ARC có bộ không do %s niêm phong." % ARC_TIN)
				the[(i, k)] = t
			aar = re.sub(rb"\r\n", b"", bo[i]["aar"][1]).decode("latin-1")
			m = re.match(r"\s*i\s*=\s*\d+\s*;\s*([^;\s]+)", aar)
			if not m or m.group(1).lower() != ARC_MAY_GHI:
				raise LoiChuKy("Chuỗi ARC có bộ không do %s ghi." % ARC_MAY_GHI)
			cv = the[(i, "as")].get("cv", b"").lower()
			if cv != (b"none" if i == 1 else b"pass"):
				raise LoiChuKy("Chuỗi ARC hỏng ở bộ %s (cv=%s)." % (i, cv.decode("latin-1")))
		# ARC-Message-Signature của bộ cuối.
		t = the[(n, "ams")]
		for can in ("bh", "h"):
			if can not in t:
				raise LoiChuKy("Chuỗi ARC thiếu thẻ %s=." % can)
		h = [x.strip().lower() for x in re.sub(rb"[\t \r\n]", b"", t["h"]).split(b":") if x.strip()]
		if b"from" not in h or any(x.startswith(b"arc-") for x in h):
			raise LoiChuKy("Chữ ký ARC không ký ô người gửi (From).")
		c = (t.get("c") or b"simple/simple").lower().split(b"/")
		kh, kt = [x.decode() for x in (c + [b"simple"])[:2]]
		if kh not in ("simple", "relaxed") or kt not in ("simple", "relaxed"):
			raise LoiChuKy("Chữ ký ARC dùng kiểu chuẩn hoá lạ.")
		if base64.b64encode(hashlib.sha256(chuan_than(than, kt)).digest()) != re.sub(rb"[\t \r\n]", b"", t["bh"]):
			raise LoiChuKy("Thân thư đã bị sửa sau khi Gmail ghi nhận.")
		ten, gt, kk = bo[n]["ams"]
		khong_arc = [x for x in tieu_de if not x[0].lower().startswith(b"arc-")]
		du = b"".join(chuan_tieu_de(a, b, kh, k2) for a, b, k2 in chon_tieu_de(khong_arc, h))
		du += chuan_tieu_de(ten, bo_gia_tri_b(gt), kh, kk).rstrip(b"\r\n")
		nn, ee = _khoa_arc(t, lay_khoa)
		if not kiem_rsa(nn, ee, _b64(t["b"]), du):
			raise LoiChuKy("Chữ ký ARC của Gmail không khớp: tiêu đề thư đã bị sửa.")
		# ARC-Seal từng bộ: ký các ô ARC của bộ 1..i theo thứ tự, kiểu relaxed.
		for i in range(1, n + 1):
			du = b""
			for j in range(1, i + 1):
				for k in ("aar", "ams", "as"):
					a, b, k2 = bo[j][k]
					v = bo_gia_tri_b(b) if (j == i and k == "as") else b
					du += chuan_tieu_de(a, v, "relaxed", k2)
			du = du.rstrip(b"\r\n")
			ta = the[(i, "as")]
			nn, ee = _khoa_arc(ta, lay_khoa)
			if not kiem_rsa(nn, ee, _b64(ta["b"]), du):
				raise LoiChuKy("Dấu niêm phong ARC bộ %s không khớp." % i)
		ra["spf_mien"] = spf_dat_aar(bo[1]["aar"][1])
		if not ra["spf_mien"]:
			raise LoiChuKy("Gmail không ghi SPF đạt cho người gửi.")
		ra["dat"] = True
	except LoiChuKy as er:
		ra["ly_do"] = str(er)
	except LoiDnsTam as er:
		ra["tam"] = True
		ra["ly_do"] = "Chưa tra được khoá ARC của Gmail (mạng hoặc DNS lỗi tạm: %s), máy sẽ thử lại." % str(er)[:120]
	except (ValueError, TypeError, IndexError, UnicodeDecodeError):
		ra["ly_do"] = "Chuỗi ARC viết sai cú pháp."
	return ra


# ------------------------------------------------------------ DNS (chạm mạng)

def lay_khoa_dns(ten):
	"""Bản ghi TXT của khoá. Dùng dnspython nếu có, không thì DNS qua HTTPS.

	Codex #544 vòng 2: chỉ trả None khi DNS TRẢ LỜI CHẮC CHẮN là không có bản
	ghi (NXDOMAIN, có tên mà không có TXT). Hết giờ, máy chủ lỗi (SERVFAIL),
	mất mạng, trả lời hỏng thì ném LoiDnsTam để thư được đọc lại sau."""
	try:
		import dns.resolver
		import dns.exception
	except ImportError:
		dns = None
	if dns is not None:
		try:
			tra = dns.resolver.resolve(ten, "TXT", lifetime=8)
			return b"".join(b"".join(r.strings) for r in tra[:1])
		except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
			return None
		except Exception as e:
			raise LoiDnsTam("%s: %s" % (type(e).__name__, str(e)[:100])) from None
	try:
		import requests
	except ImportError:
		raise LoiDnsTam("máy chủ thiếu thư viện tra DNS") from None
	try:
		r = requests.get("https://cloudflare-dns.com/dns-query", params={"name": ten, "type": "TXT"},
			headers={"accept": "application/dns-json"}, timeout=8)
		r.raise_for_status()
		d = r.json()
	except Exception as e:
		raise LoiDnsTam("%s: %s" % (type(e).__name__, str(e)[:100])) from None
	return txt_doh(d)


def txt_doh(d):
	"""THUẦN. Đọc trả lời DNS-qua-HTTPS (dạng JSON). Status 0 (NOERROR) mà không
	có TXT, hoặc 3 (NXDOMAIN): chắc chắn không có khoá, trả None. Mọi mã khác
	(2 SERVFAIL, 5 REFUSED...) hay trả lời hỏng: lỗi tạm, ném LoiDnsTam."""
	if not isinstance(d, dict) or not isinstance(d.get("Status"), int):
		raise LoiDnsTam("trả lời DNS không đọc được")
	if d["Status"] == 3:
		return None
	if d["Status"] != 0:
		raise LoiDnsTam("máy chủ DNS trả mã %s" % d["Status"])
	for a in (d.get("Answer") or []):
		if a.get("type") == 16:
			v = a.get("data") or ""
			return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', v) or [v]).encode("latin-1")
	return None
