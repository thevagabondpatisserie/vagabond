"""v598 (16/10/2026): nút "Gửi yêu cầu đặt bánh" bị co thành viên tròn khi có dòng báo lỗi.

Kiểm THẬT nằm ở cong_cu/ra_nut_web.py (Chromium, 390 px và 1440 px, chạy trong
job ra-nut của workflow Anh giao dien web): dựng đúng chuỗi khách bấm gửi rồi
nhận "Chưa gửi được đơn", đo mọi nút. Trên main 597 công cụ báo nút gửi rộng
58 px, cao 110 px (đủ rộng thì cao 58 px), và dòng báo lỗi đặt bàn nằm ngoài
khung nhìn (cách 969 px). Sau sửa: 0 vi phạm trên 60 cảnh.

Tệp này chỉ CHỐT các điểm sửa để không ai lỡ xoá (điều 16: dò chuỗi chỉ để chốt,
không thay cho phép đo trên trình duyệt).
"""
import ast
import re
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent


@ca("v598 chốt: hàng nút .cta cho dòng báo xuống hàng riêng, ở cả trang cũ và bản Vue")
def _():
	for tep in ("trang/banh.html", "public/web_vue/banh/banh.css"):
		s = (GOC / tep).read_text()
		m = re.search(r"\.cta\{position:sticky;[^}]*\}", s)
		dung(tep + " có .cta", bool(m))
		dung(tep + " .cta cho xuống dòng", m and "flex-wrap:wrap" in m.group(0))
		dung(tep + " phần tử không phải nút chiếm trọn hàng", ".cta>:not(.btn):not(.tel){flex:1 0 100%}" in s)
		for chon, cao in ((".slot{", "min-height:44px"), (".close{", "height:44px"), (".co-top .bk{", "height:44px")):
			m = re.search(re.escape(chon) + r"[^}]*\}", s)
			dung(tep + " " + chon + " vùng bấm 44", m and cao in m.group(0))


@ca("v598 chốt: lỗi đặt bàn, thành viên cuộn tới dòng báo; trang trỏ đúng mã băm tệp mới")
def _():
	import hashlib
	for js, html in (("dat-ban.js", "www/dat-ban.html"), ("thanh-vien.js", "www/thanh-vien.html")):
		s = (GOC / "public/web_order" / js).read_text()
		dung(js + " cuộn tới dòng báo khi lỗi", "scrollIntoView" in s)
		bam = hashlib.sha256((GOC / "public/web_order" / js).read_bytes()).hexdigest()[:12]
		dung(html + " trỏ " + js + "?v=" + bam, ("%s?v=%s" % (js, bam)) in (GOC / html).read_text())


@ca("v598 chốt: công cụ rà nút có trong CI và có đúng cảnh khách gửi đơn lỗi")
def _():
	wf = (REPO / ".github/workflows/anh-web.yml").read_text()
	dung("job ra-nut chạy công cụ", "python3 cong_cu/ra_nut_web.py" in wf)
	cay = ast.parse((REPO / "cong_cu/ra_nut_web.py").read_text())
	canh = next(ast.literal_eval(n.value) for n in cay.body if isinstance(n, ast.Assign) and any(getattr(t, "id", "") == "CANH" for t in n.targets))
	for c in ("cu:gui-loi", "www:/dat-ban#loi", "vue:gio-giao", "vue:gui-loi", "vue:huong-size"):
		dung("có cảnh " + c, c in canh)
	nguon = (REPO / "cong_cu/ra_nut_web.py").read_text()
	dung("cảnh gửi lỗi chọn ngày theo vị trí, không theo chữ ngày (CI chạy ngày nào cũng mở được)", "has_text='19/10'" not in nguon)
	dung("job dom-khach chạy thao tác DOM trang cũ và Vue", "dom-khach:" in wf and "node cong_cu/kiem_web_vue_dom.cjs" in wf)
	dung("không cho job DOM được phép lỗi", "continue-on-error" not in wf)
