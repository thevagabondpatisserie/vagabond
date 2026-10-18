"""v603 (anh Việt 18/10/2026: "làm vụ web bản Vue cho xong"): phần còn lại của
việc chuyển /banh sang bản Vue.

- F32: biên nhận /banh/xong[/<token>] đi theo cùng công tắc với /banh. Trước v603
  khách đặt ở bản Vue lại rơi về biên nhận trang cũ.
- Biên nhận, chính sách Vue có logo ở đầu trang như trang cũ; nút về trang đặt
  bánh và chân trang chính sách trỏ /banh khi đã tráo, /web_moi khi đang chạy thử.
- F30: Editor xem trước (/banh?bien_tap=1) đi theo công tắc, Marketing xem đúng
  bản khách đang thấy. Phần trình duyệt kiểm ở cong_cu/kiem_web_vue_dom.cjs F39.
- Ba trang chính sách KHÔNG tráo: trang cũ dựng chữ trên máy chủ, bộ kiểm Meta
  và máy tìm kiếm đọc được không cần chạy JS.

Ca kiểm gọi get_context THẬT của trang biên nhận, chỉ thay tầng Frappe.
"""
import json
import re
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[2]
CS = [{"khoa": "chinh_sach_bao_mat", "ten": "Bảo mật", "duong": "/chinh-sach-bao-mat"},
	{"khoa": "dieu_khoan", "ten": "Điều khoản", "duong": "/dieu-khoan"}]


def _xong(duong, token="T"):
	"""get_context thật của www/web_moi/xong.py tại một đường request."""
	from vagabond.khung.kiem_thu.thu_su_co_290 import nap, D
	from vagabond import trang_khach, web_vue
	from vagabond.www.banh.xong import TIEU_DE
	fr = D(local=D(response_headers={}, request=D(path=duong)), sessions=D(get_csrf_token=lambda: "c"),
		form_dict={"token": token} if token else {}, PageDoesNotExistError=ValueError)
	dw = D(PHAP_NHAN={"ten": "X"}, lien_he=lambda: {}, pixel_id=lambda: "",
		bien_nhan_theo_token=lambda t: {"ma": "DW-1"})
	nd = D(chinh_sach_dang_hien=lambda: [dict(c) for c in CS], cong_khai=lambda: {"nhan": {}})
	g = {"frappe": fr, "don_web": dw, "trang_khach": trang_khach, "noi_dung_web": nd,
		"TIEU_DE": TIEU_DE, "web_vue": web_vue}
	c = nap("www/web_moi/xong.py", "get_context", g)(D())
	return c, json.loads(c.du_lieu.replace("\\u003c", "<"))


def _href_chan_trang(html):
	m = re.search(r'<nav class="ct-chinh-sach".*?</nav>', html)
	return re.findall(r'href="([^"]+)"', m.group(0)) if m else []


@ca("v603 tráo Vue: bảng đường tráo đúng hai trang, ba trang chính sách giữ trang cũ")
def _():
	from vagabond.web_vue import TEP_VUE, tep_ban_vue
	la("bảng", TEP_VUE, {"banh": "web_moi/banh", "banh/xong": "web_moi/xong"})
	for d in ("chinh-sach", "chinh-sach-bao-mat", "dieu-khoan", "giao-hang-doi-tra", "dat-ban", "thanh-vien"):
		la("%s không tráo" % d, tep_ban_vue(d, 1, {}), "")
	la("biên nhận", tep_ban_vue("banh/xong", 1, {}), "web_moi/xong")
	la("Editor xem trước", tep_ban_vue("banh", 1, {"bien_tap": "1"}), "web_moi/banh")


@ca("v603 tráo Vue: nút về trang đặt bánh theo đường đang phát")
def _():
	from vagabond.web_vue import trang_chu_dat_banh
	for d, mong in (("/banh/xong/T", "/banh"), ("/banh/xong", "/banh"), ("/banh", "/banh"),
		("/web_moi/banh/xong/T", "/web_moi/banh"), ("/web_moi/dieu-khoan", "/web_moi/banh"),
		("/banhx", "/web_moi/banh"), ("", "/web_moi/banh"), (None, "/web_moi/banh")):
		la(repr(d), trang_chu_dat_banh(d), mong)


@ca("v603 tráo Vue: biên nhận phát tại /banh/xong về /banh, chân trang trỏ chính sách công khai; ở /web_moi giữ đường thử")
def _():
	for duong, ve, cs in (("/banh/xong/T", "/banh", ["/chinh-sach-bao-mat", "/dieu-khoan"]),
		("/web_moi/banh/xong/T", "/web_moi/banh", ["/web_moi/chinh-sach-bao-mat", "/web_moi/dieu-khoan"])):
		for token in ("T", ""):
			c, d = _xong(duong if token else duong.rsplit("/", 1)[0], token)
			la("%s token=%r: trang_chu" % (duong, token), c.trang_chu, ve)
			la("%s token=%r: dữ liệu cho JS" % (duong, token), d["trang_chu"], ve)
			la("%s token=%r: chân trang" % (duong, token), _href_chan_trang(c.chan_trang), cs)


@ca("v603 tráo Vue: biên nhận, chính sách Vue có logo trỏ trang đặt bánh; JS không còn gõ cứng /web_moi/banh trần")
def _():
	logo = '<a href="{{ trang_chu }}" class="tk-logo"><img src="/assets/vagabond/web_order/logo-trang.png?v='
	for tep in ("xong.html", "chinh-sach.html"):
		s = (GOC / "www/web_moi" / tep).read_text()
		la(tep + " có logo", s.count(logo), 1)
		dung(tep + " bỏ chữ thay logo", "THE VAGABOND PÂTISSERIE</a>" not in s)
	js = (GOC / "public/web_vue/trang/app.js").read_text()
	la("hai nút về đặt bánh đọc trang_chu", js.count("href:D.trang_chu || '/web_moi/banh'"), 2)
	la("không còn đường gõ cứng", js.count("href:'/web_moi/banh'"), 0)
	cs = (GOC / "www/web_moi/chinh_sach.py").read_text()
	dung("chính sách Vue đặt trang_chu", "context.trang_chu = web_vue.trang_chu_dat_banh(duong)" in cs)


@ca("v603 tráo Vue: Editor vẫn mở khung xem trước tại /banh?bien_tap=1 (đi theo công tắc)")
def _():
	s = (GOC / "public/web_order/bien-tap.js").read_text()
	la("đường khung xem trước", re.findall(r"preview'\)\.src = '([^']+)'", s), ["/banh?bien_tap=1"])


@ca("v603 Codex #489 P2: lời giải thích công tắc nói đúng phạm vi mới (biên nhận, Editor xem trước theo công tắc; chính sách giữ cũ)")
def _():
	d = json.loads((GOC / "vagabond/doctype/vagabond_settings/vagabond_settings.json").read_text())
	mo = next(x for x in d["fields"] if x["fieldname"] == "web_ban_vue")["description"]
	dung("không còn câu cũ về Editor", "Editor vẫn mở trang cũ" not in mo)
	dung("không còn câu cũ về biên nhận", "vẫn là trang cũ" not in mo)
	dung("nói biên nhận và Editor cũng là bản mới", "biên nhận" in mo and "xem trước của Editor" in mo)
	dung("nói chính sách giữ bản cũ", "chính sách giữ bản cũ" in mo)
	dung("vẫn nói cách quay lại", "không cần deploy" in mo and "?ban=cu" in mo)
	la("đẩy mốc modified để site nạp lại", d["modified"] >= "2026-10-18", True)


def _chay_bien_nhan_cu(du_lieu, bo_nho=None, duong="/banh/xong/" + "a" * 43, tim=""):
	"""Chạy bien-nhan.js THẬT (biên nhận trang cũ) trong node với location có search và replace."""
	import subprocess
	ma = r"""
const vm=require('vm'); const fs=require('fs');
const src=fs.readFileSync(process.argv[1],'utf8');
const vet=[]; const kho=new Map(JSON.parse(process.argv[3]));
const window={ VGB_BIEN_NHAN: JSON.parse(process.argv[2]),
  location:{pathname:process.argv[4], search:process.argv[5], replace:u=>vet.push('chuyen:'+u)},
  history:{replaceState:(a,b,u)=>{ vet.push('replace:'+u); window.location.pathname=u.split('?')[0]; }},
  sessionStorage:{getItem:k=>kho.has(k)?kho.get(k):null, setItem:(k,v)=>{kho.set(k,String(v));}},
};
const el={innerHTML:''};
const document={ getElementById:()=>el, getElementsByTagName:()=>[{parentNode:{insertBefore:()=>0}}], createElement:()=>({}) };
const htmlChuWeb=(k,d)=>d;
vm.runInNewContext(src, {window, document, console, htmlChuWeb});
console.log(JSON.stringify({vet, html:el.innerHTML}));
"""
	p = str(GOC / "public" / "web_order" / "bien-nhan.js")
	r = subprocess.run(["node", "-e", ma, p, json.dumps(du_lieu), json.dumps(bo_nho or []), duong, tim],
		capture_output=True, text=True, timeout=30)
	if r.returncode != 0:
		raise AssertionError("bien-nhan.js lỗi: " + r.stderr[:400])
	return json.loads(r.stdout.strip().splitlines()[-1])


@ca("v603 Codex #489 P2 (L141): biên nhận trang cũ mở từ ?ban=cu giữ ?ban=cu khi gỡ token, tải lại vẫn là bản cũ")
def _():
	d = {"pixel_id": "", "than": "<main>cu</main>", "su_kien": {}}
	la("có ?ban=cu", _chay_bien_nhan_cu(d, tim="?ban=cu")["vet"][0], "replace:/banh/xong?ban=cu")
	la("không có thì như trước", _chay_bien_nhan_cu(d)["vet"][0], "replace:/banh/xong")
	s = (GOC / "trang/banh.html").read_text()
	dung("trang cũ gửi đơn từ ?ban=cu thì sang biên nhận kèm ?ban=cu",
		"location.assign(m.duong_dan + (/(^|[?&])ban=cu(&|$)/i.test(location.search || '') ? '?ban=cu' : ''));" in s)


@ca("v603 Codex #489 P2 (L118): đổi công tắc giữa chừng, tải lại /banh/xong không token vẫn ra biên nhận của khách")
def _():
	cu = [["vgb_bien_nhan", "<main>bien nhan cu</main>"]]
	moi = [["vgb_bien_nhan_vue", json.dumps({"ma": "DW-1"})]]
	r = _chay_bien_nhan_cu({"khong_token": 1}, bo_nho=moi, duong="/banh/xong")
	la("trang cũ, tab chỉ có bản Vue: chuyển sang biên nhận Vue", [x for x in r["vet"] if x.startswith("chuyen:")], ["chuyen:/web_moi/banh/xong"])
	r = _chay_bien_nhan_cu({"khong_token": 1}, bo_nho=cu + moi, duong="/banh/xong")
	la("có bản của chính mình: không chuyển", [x for x in r["vet"] if x.startswith("chuyen:")], [])
	la("và hiện đúng bản cũ", r["html"], "<main>bien nhan cu</main>")
	r = _chay_bien_nhan_cu({"khong_token": 1}, bo_nho=[], duong="/banh/xong")
	la("không có bản nào: không chuyển", [x for x in r["vet"] if x.startswith("chuyen:")], [])
	dung("không có bản nào: câu mời xem tin nhắn", "Biên nhận chỉ mở được" in r["html"])
