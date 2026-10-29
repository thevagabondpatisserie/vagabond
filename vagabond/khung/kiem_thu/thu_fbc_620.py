# -*- coding: utf-8 -*-
"""v620: khách bấm quảng cáo Facebook vào web thì vẫn đặt được bánh.

Sự cố 29/10/2026: Facebook gắn mã fbclid dài vào đường dẫn. Web ghép thành
cookie _fbc dài khoảng 180 đến 222 ký tự, máy chủ coi là đúng dạng Meta, cắt ở
250 rồi ghi vào bản ghi đơn web. Hai ô Cookie _fbp và _fbc lại là ô Data, chỉ
chứa 140 ký tự. Frappe ném lỗi độ dài, cả giao dịch lùi, khách thấy "Không gửi
được đơn lúc này". Tái hiện trên site thật: _fbc 184 ký tự trả mã 417, bỏ _fbc
thì đơn đi được. Số đơn từ 05714 tới 05737 bị nhảy là các lần gửi hỏng.

Ca kiểm đọc đúng tệp doctype mà Frappe nạp lên site, tính sức chứa của ô theo
đúng luật Frappe (Data mặc định 140, các ô chữ dài thì không giới hạn 140), rồi
cho đi giá trị dài nhất mà bộ lọc đúng dạng chấp nhận. Không dò chuỗi.
"""

import json
from pathlib import Path

from vagabond import don_web
from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[2]
TEP = GOC / "vagabond" / "doctype" / "vagabond_don_web" / "vagabond_don_web.json"

# Sức chứa theo cách Frappe dựng cột: Data là varchar(length hoặc 140);
# Small Text, Text, Long Text, Code là cột chữ dài.
CHU_DAI = {"Small Text": 65535, "Text": 65535, "Long Text": 2 ** 32 - 1, "Code": 2 ** 32 - 1}

# Máy chủ cắt ở 250 trước khi ghi (don_hang.tao_don).
CAT = 250


def suc_chua(o):
	if o.get("fieldtype") in ("Data", "Link", "Dynamic Link", "Select"):
		return int(o.get("length") or 140)
	return CHU_DAI.get(o.get("fieldtype"), 0)


def _o():
	d = json.loads(TEP.read_text(encoding="utf-8"))
	return {o["fieldname"]: o for o in d["fields"]}


def dai_nhat():
	"""Giá trị _fbc dài nhất mà bộ lọc đúng dạng còn nhận."""
	return "fb.1." + "1" * 16 + "." + "A" * 200


@ca("v620 cookie Facebook: giá trị dài nhất còn đúng dạng vẫn vừa ô của bản ghi đơn web")
def _vua_o():
	o = _o()
	v = dai_nhat()
	la("giá trị dài nhất đúng dạng có 222 ký tự", len(v), 222)
	dung("bộ lọc nhận giá trị 222 ký tự", don_web.fb_hop_le(v))
	dung("dài thêm một ký tự thì bộ lọc bỏ", not don_web.fb_hop_le(v + "A"))
	for ten in ("fbp", "fbc"):
		dung("ô %s chứa được mọi giá trị máy chủ có thể ghi (%d ký tự)" % (ten, CAT), suc_chua(o[ten]) >= CAT)
		dung("ô %s vẫn chỉ đọc" % ten, o[ten].get("read_only") == 1)


@ca("v620 cookie Facebook: mẫu fbclid thật 184 ký tự (sự cố 29/10) ghi được")
def _ca_that():
	o = _o()
	v = "fb.1.1761720000000." + "IwZXh0bgNhZW0CMTEAAR" + "x" * 145
	la("độ dài đúng như ca site thật", len(v), 184)
	dung("bộ lọc nhận", don_web.fb_hop_le(v))
	dung("ô fbc chứa được", suc_chua(o["fbc"]) >= len(v))
	# Ô Data cũ 140 ký tự chính là chỗ hỏng: ca này phải hỏng trên tệp cũ.
	dung("ô Data 140 ký tự cũ không chứa được (chứng minh ca bắt lỗi)",
		suc_chua({"fieldtype": "Data"}) < len(v))
