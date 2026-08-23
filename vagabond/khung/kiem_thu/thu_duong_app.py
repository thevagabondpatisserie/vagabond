"""Kiểm thử bảng đường dẫn app Bếp và nội dung chuyển khoản (23/08/2026)."""

import io
import os
import re

from vagabond.khung.kiem_thu.nen import ca, dung, la

# .../vagabond/khung/kiem_thu/tep -> len BON bac moi toi goc repo.
GOC = os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.dirname(os.path.abspath(__file__)))))


def _js_bang_duong():
	"""Đọc bảng VGB_DUONG trong 02-trang-chu.js ra dict, không cần trình duyệt."""
	p = os.path.join(GOC, "vagabond", "public", "js", "bep", "02-trang-chu.js")
	src = io.open(p, encoding="utf-8").read()
	i = src.index("var VGB_DUONG = {")
	j = src.index("};", i)
	ra = {}
	for m in re.finditer(r"'([a-z0-9\-]+)'\s*:\s*'([A-Z0-9]+)'", src[i:j]):
		ra[m.group(1)] = m.group(2)
	return ra


@ca("duong app: bang ben Python va ben JavaScript phai khop TUNG DONG")
def _():
	# Hai ban nay o hai ngon ngu khac nhau nen khong the dung chung mot bien.
	# Lech mot dong thi hong LANG LE: may khach doi dia chi sang mot duong ma
	# may chu khong biet, nguoi dung bam thi khong sao, F5 mot cai la 404.
	# Khong ai kiem thu bang cach F5 tung man, nen phai co ca kiem nay.
	from vagabond.duong_app import DUONG

	js = _js_bang_duong()
	dung("đọc được bảng bên JavaScript", len(js) > 0)
	thieu = sorted(set(DUONG) - set(js))
	thua = sorted(set(js) - set(DUONG))
	dung("JavaScript không thiếu đường nào: " + (", ".join(thieu) or "đủ"), not thieu)
	dung("JavaScript không thừa đường nào: " + (", ".join(thua) or "đủ"), not thua)
	lech = sorted(s for s in DUONG if js.get(s) != DUONG[s])
	dung("khoá màn hình khớp nhau: " + (", ".join(lech) or "khớp"), not lech)


@ca("duong app: khong slug nao trung route cua Web Page dang co")
def _():
	# Trung route thi Frappe tra ve trang kia chu khong tra ve app, va loi do
	# chi lo khi co nguoi F5 dung duong do.
	from vagabond.duong_app import DUONG, ROUTE_DA_CO, TRANG_APP

	trung = sorted(set(DUONG) & set(ROUTE_DA_CO))
	dung("không trùng: " + (", ".join(trung) or "sạch"), not trung)
	dung("trang chứa app nằm trong danh sách Web Page đang có", TRANG_APP in ROUTE_DA_CO)


@ca("duong app: moi khoa man hinh phai co that trong vgbGo")
def _():
	# Khai mot khoa khong co trong vgbGo thi bam vao ra man trang.
	from vagabond.duong_app import DUONG

	p = os.path.join(GOC, "vagabond", "public", "js", "bep", "02-trang-chu.js")
	src = io.open(p, encoding="utf-8").read()
	i = src.index("function vgbGo(k) {")
	than = src[i:i + 6000]
	co = set(re.findall(r"k === '([A-Z0-9]+)'", than))
	thieu = sorted(k for k in DUONG.values() if k not in co)
	dung("khoá nào cũng có nhánh trong vgbGo: " + (", ".join(thieu) or "đủ"), not thieu)


@ca("duong app: luat dinh tuyen tro dung ve trang chua app")
def _():
	from vagabond.duong_app import DUONG, TRANG_APP, luat_dinh_tuyen

	luat = luat_dinh_tuyen()
	la("số luật bằng số đường", len(luat), len(DUONG))
	dung("mọi luật đều trỏ về trang app", all(r["to_route"] == TRANG_APP for r in luat))
	dung("mọi luật đều bắt đầu bằng gạch chéo", all(r["from_route"].startswith("/") for r in luat))
	# KHONG duoc co luat bat tat: bat tat thi moi dia chi la tren site deu
	# roi vao app Bep, ke ca trang khach. Dung quy tac 6 cua repo.
	dung("không có luật bắt tất kiểu <path:...>",
		not any("<" in r["from_route"] for r in luat))


@ca("noi dung chuyen khoan: ma ho so phai dung DAU chuoi")
def _():
	# Anh Viet 23/08/2026 de nghi dat MA PHIEU o CUOI. Da doi lai va day la
	# ly do, dung dao lai: ngan hang cat noi dung o DUOI khi vuot han muc
	# (quanh 90 ky tu). Dat ma o cuoi thi ho so nhieu hoa don la mat ma, ma
	# ma chinh la thu _sepay_theo_ma_app do de tu khop tien da chi. Mat ma
	# thi nut "Do SePay" im lang bao chua chuyen trong khi tien da di.
	import types

	from vagabond import ho_so_tt as t

	D = types.SimpleNamespace
	doc = D(name="APP.26.08.011", loai=t.LOAI_NCC,
		ten_nhan="CONG TY CO PHAN GOURMET PARTNER VIET NAM", ten_ncc="", nha_cung_cap="",
		dong=[D(so_hd_ncc="26957", hoa_don=None), D(so_hd_ncc="26958", hoa_don=None)])
	nd = t._noi_dung_ck(doc)
	dung("mã hồ sơ nằm ngay đầu chuỗi", nd.startswith("VAGABOND APP.26.08.011"))
	dung("có số hoá đơn nhà cung cấp", "HD26957" in nd and "HD26958" in nd)
	dung("không vượt trần %d ký tự" % t.DAI_ND_CK, len(nd) <= t.DAI_ND_CK)
	dung("không còn dấu tiếng Việt", not re.search(r"[^\x00-\x7f]", nd))

	# Ca thuc te: ho so nhieu hoa don, ten nha cung cap dai. Ma VAN phai con.
	doc2 = D(name="APP.26.08.099", loai=t.LOAI_NCC,
		ten_nhan="CONG TY TNHH MOT THANH VIEN THUONG MAI DICH VU XUAT NHAP KHAU ABC",
		ten_ncc="", nha_cung_cap="",
		dong=[D(so_hd_ncc=str(90000 + i), hoa_don=None) for i in range(12)])
	nd2 = t._noi_dung_ck(doc2)
	dung("hồ sơ 12 hoá đơn vẫn giữ được mã ở đầu", nd2.startswith("VAGABOND APP.26.08.099"))
	dung("hồ sơ 12 hoá đơn vẫn không vượt trần", len(nd2) <= t.DAI_ND_CK)
	# Chinh la phep thu chung minh vi sao khong dat ma o cuoi: chuoi DAI hon
	# tran nen phan duoi bi cat. Neu ma nam duoi thi chinh ma la phan mat.
	day_du = "VAGABOND APP.26.08.099 THANH TOAN " + " ".join(
		"HD%d" % (90000 + i) for i in range(12))
	dung("chuỗi đầy đủ dài hơn trần, tức là có bị cắt thật",
		len(day_du) > t.DAI_ND_CK)
	dung("tên nhà cung cấp là phần bị cắt, không phải mã", "ABC" not in nd2)


@ca("ho so: chi keo chung tu DA GHI SO, bo nhap va bo da huy")
def _():
	from vagabond import ho_so_tt as t

	src = io.open(os.path.join(GOC, "vagabond", "ho_so_tt.py"), encoding="utf-8").read()
	dung("có hàm lọc theo docstatus", "def _da_ghi_so(" in src)
	dung("lọc đúng docstatus 1", '"docstatus": 1' in src)
	# Phai ap cho CA don mua lan phieu nhap kho.
	than = src[src.index("def _ho_so_chung_tu("):]
	than = than[:than.index("def _dinh_kem(")]
	dung("áp cho phiếu nhập kho", '_da_ghi_so("Purchase Receipt"' in than)
	dung("áp cho đơn mua hàng", '_da_ghi_so("Purchase Order"' in than)
	# Ham giu nguyen thu tu, va rong vao thi rong ra.
	la("rỗng vào thì rỗng ra", t._da_ghi_so("Purchase Receipt", []), [])


@ca("ten mien: chi ba mien duoc khai moi bi ap luat, con lai di duong cu")
def _():
	# DAY LA CHOT AN TOAN QUAN TRONG NHAT cua tep ten_mien.py. Dat luat rong
	# roi chan nham la KHOA CUA CHINH MINH: khong vao duoc Desk de sua lai.
	# Ten mien mac dinh cua Frappe Cloud phai luon di duoc, vi do la duong
	# duy nhat con lai khi ten mien that hong.
	from vagabond.duong_app import DUONG
	from vagabond.ten_mien import dich_chuyen_huong

	for host in ("vagabond.s.frappe.cloud", "erpnext-qwy-acq.s.frappe.cloud",
			"localhost", "127.0.0.1", "", None, "thevagabondpatisserie.com"):
		for d in ("/app", "/bep", "/banh", "/app/user", "/"):
			la("miền lạ %r đường %s không bị đụng" % (host, d),
				dich_chuyen_huong(host, d, tuple(DUONG)), "")


@ca("ten mien: khong bao gio chan api, assets, files, dang nhap")
def _():
	# Chan may duong nay la app TRANG MAN: no goi API va tai tai nguyen qua
	# chinh ten mien cua no.
	#
	# TRUNG THUC VE CA KIEM NAY: da thu xoa "/api/" khoi CHUA_RA va ca kiem
	# VAN XANH. Ly do la luat mac dinh cua dich_chuyen_huong() da la CHO DI
	# TIEP khi duong khong thuoc nhom nao. Nghia la hom nay CHUA_RA chua ganh
	# viec gi, cai dang bao ve la luat mac dinh do.
	#
	# Van giu ca hai, va van giu ca kiem nay: ngay nao co nguoi doi luat mac
	# dinh thanh CHAN (vi du "mien app chi cho di /bep va cac slug"), thi
	# CHUA_RA thanh hang rao that va ca kiem nay bat dau can. Do dung la kieu
	# sua de gay ra su co lon nhat o day.
	from vagabond.duong_app import DUONG
	from vagabond.ten_mien import MIEN_APP, MIEN_DESK, MIEN_KHACH, dich_chuyen_huong

	duong = ("/api/method/x", "/assets/vagabond/js/app_bep.js", "/files/a.png",
		"/private/files/b.pdf", "/login", "/favicon.ico", "/manifest.json",
		"/sw.js", "/socket.io/x")
	for m in (MIEN_APP, MIEN_DESK, MIEN_KHACH):
		for d in duong:
			la("%s không chặn %s" % (m, d), dich_chuyen_huong(m, d, tuple(DUONG)), "")


@ca("ten mien: moi mien vao dung cua cua minh thi di tiep, vao nham thi da sang")
def _():
	from vagabond.duong_app import DUONG
	from vagabond.ten_mien import MIEN_APP, MIEN_DESK, MIEN_KHACH, dich_chuyen_huong

	D = tuple(DUONG)
	# Dung cua.
	la("app vào /bep", dich_chuyen_huong(MIEN_APP, "/bep", D), "")
	la("app vào màn con", dich_chuyen_huong(MIEN_APP, "/don-da-huy", D), "")
	la("erp vào Desk", dich_chuyen_huong(MIEN_DESK, "/app/user", D), "")
	la("order vào trang bánh", dich_chuyen_huong(MIEN_KHACH, "/banh", D), "")
	la("order vào trang thanh toán đơn", dich_chuyen_huong(MIEN_KHACH, "/tt", D), "")
	# Nham cua.
	la("app vào Desk thì về app", dich_chuyen_huong(MIEN_APP, "/app", D), "/bep")
	la("app vào trang khách thì về app", dich_chuyen_huong(MIEN_APP, "/banh", D), "/bep")
	la("erp vào app thì về Desk", dich_chuyen_huong(MIEN_DESK, "/bep", D), "/app")
	la("order vào app thì về trang bánh", dich_chuyen_huong(MIEN_KHACH, "/bep", D), "/banh")
	la("order vào Desk thì về trang bánh", dich_chuyen_huong(MIEN_KHACH, "/app", D), "/banh")
	# Goc cua tung mien.
	la("app vào gốc", dich_chuyen_huong(MIEN_APP, "/", D), "/bep")
	la("erp vào gốc", dich_chuyen_huong(MIEN_DESK, "/", D), "/app")
	la("order vào gốc", dich_chuyen_huong(MIEN_KHACH, "/", D), "/banh")


@ca("ten mien: chi co MOT khai bao update_website_context trong hooks")
def _():
	# Khai hai lan trong cung mot tep thi lan sau DE lan truoc va hook kia im
	# lang khong chay. Python khong bao gi ca, ca kiem khong bao gi ca, chi lo
	# khi co nguoi vao nham cua ma khong bi da sang.
	src = io.open(os.path.join(GOC, "vagabond", "hooks.py"), encoding="utf-8").read()
	la("số lần khai update_website_context", src.count("\nupdate_website_context = "), 1)
	dung("định tuyến tên miền nằm trong danh sách đó",
		"vagabond.hooks._dinh_tuyen_ten_mien" in src)
	dung("hook cũ og_theo_ten_mien vẫn còn, không bị gạt ra",
		"vagabond.lib.og_theo_ten_mien" in src)


@ca("ho so: mot hoa don khong duoc nam trong hai ho so con song")
def _():
	# Hai ho so cung chua mot hoa don thi cung di qua hai cap duyet va cung
	# duoc chuyen tien, vi moi ho so nhin rieng ra deu hop le. Khong ai doi
	# chieu cheo giua cac ho so bang mat.
	from vagabond import ho_so_tt as t

	src = io.open(os.path.join(GOC, "vagabond", "ho_so_tt.py"), encoding="utf-8").read()
	dung("có hàm chặn", "def _chan_hoa_don_trung(" in src)
	# Phai chan o CA BA luong lap ho so, thieu mot luong la thung mot lo.
	la("số luồng có gọi chốt chặn", src.count("\t_chan_hoa_don_trung("), 3)

	# Ho so Tu choi va Huy KHONG duoc chan: hoa don trong do phai dung lai
	# duoc, neu khong thi mot lan lap nham la hoa don ket vinh vien.
	dung("trạng thái còn sống không gồm Từ chối", t.TT_TU_CHOI not in t.TT_CON_SONG)
	dung("trạng thái còn sống không gồm Huỷ", t.TT_HUY not in t.TT_CON_SONG)
	dung("trạng thái còn sống có Đã thanh toán", t.TT_DA_TRA in t.TT_CON_SONG)
	dung("trạng thái còn sống có Nháp", t.TT_NHAP in t.TT_CON_SONG)


@ca("duong app: phai CHO trang chu ve xong roi moi mo man theo dia chi")
def _():
	# Loi that, do tren site sau khi deploy v284 ngay 23/08/2026: F5 tai
	# /don-da-huy van ra trang chu.
	#
	# Nguyen nhan: scrHome la ham `async`. No ve tam mot cai dong ho cat, roi
	# `await` du lieu, xong moi ve that. __boot goi reset(scrHome) roi mo
	# NGAY man theo dia chi, nhung scrHome ve that MUON hon va de len man vua
	# mo. Dia chi dung, man hinh sai.
	#
	# Cach sua: render() tra ve promise cua ham man hinh thay vi nuot di, va
	# __boot `await` no truoc khi goi vgbMoTheoDiaChi.
	#
	# Bai hoc chung: trong app nay ham man hinh phan lon la async, nen bat cu
	# cho nao ve hai man lien tiep deu phai cho man truoc ve xong.
	khung = io.open(os.path.join(GOC, "vagabond", "public", "js", "bep",
		"01-khung-app.js"), encoding="utf-8").read()
	vd = io.open(os.path.join(GOC, "vagabond", "public", "js", "bep",
		"12-van-don.js"), encoding="utf-8").read()

	dung("render trả về promise của hàm màn hình, không nuốt đi",
		"if (f) return f();" in khung)
	dung("reset trả lại kết quả của render", "return render();" in khung)
	# CA HAI nhanh vao man chinh deu phai cho, bo mot nhanh la nguoi dang
	# nhap kieu do van bi vang ve trang chu.
	la("số nhánh có await reset(scrHome)", vd.count("await reset(scrHome)"), 2)
	dung("không còn nhánh nào gọi reset(scrHome) mà không chờ",
		"adopt(real); reset(scrHome);" not in vd)
	# vgbMoTheoDiaChi phai nam SAU await, khong nam truoc.
	i = vd.index("async function __boot()")
	than = vd[i:vd.index("window.addEventListener('popstate'")]
	for k in range(than.count("vgbMoTheoDiaChi()")):
		vi = [m for m in range(len(than)) if than.startswith("vgbMoTheoDiaChi()", m)][k]
		truoc = than[:vi]
		dung("lần gọi thứ %d nằm sau một await reset(scrHome)" % (k + 1),
			"await reset(scrHome)" in truoc)
