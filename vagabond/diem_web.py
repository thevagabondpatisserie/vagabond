"""Điểm thành viên trên web, nhân điểm theo chương trình, thể lệ (v652).

Anh Việt chốt 12/11/2026:
  - Khách online được dùng điểm ở bước thanh toán, xác thực số qua mã Zalo
    (cùng phiên Thành viên với ưu đãi đơn đầu tiên: thanh_vien.gui_ma, xac_thuc).
    Cùng luật với quầy (diem_otp): 1 điểm = 1 đồng, tối đa 50% tiền, bill còn
    lại không dưới mức tối thiểu, hạng AMBASSADOR, FAMILY, OWNER không dùng.
  - Điểm chỉ trừ vào TIỀN BÁNH, không trừ phí giao; cộng chung được với mã ưu
    đãi và ưu đãi đơn đầu tiên, điểm trừ SAU CÙNG trên số tiền bánh còn lại.
  - Đơn không thành (Pancake từ chối, đơn chuyển Đã huỷ) thì máy tự hoàn điểm
    và báo khách qua Zalo.
  - Nhân điểm là một chương trình khuyến mãi do Marketing cài ở màn Khuyến mãi
    (cách thức "Nhan diem", hệ số ở ô gia_tri), không mặc định trên web. Ví dụ
    thứ Năm hằng tuần, đặt trên web được x2.
  - Hạn điểm cuốn chiếu (diem_han): trang thành viên báo số điểm sắp hết hạn.

Sợi dây giữa sổ điểm và đơn web là ghi chú "Đơn web <mã>" (don_web.GHI_CHU_DON_WEB),
giống lượt chương trình khuyến mãi: bút trừ và bút hoàn cùng ghi chú đó.

Phần THUẦN ở đầu tệp (không chạm Frappe) để bộ kiểm tầng khung gọi thẳng.
"""

from datetime import date, datetime, timedelta

CACH_NHAN = "Nhan diem"
NGUON_WEB = "Website"
HANG_CAM_TIEU = {"AMBASSADOR", "FAMILY", "OWNER"}
# Hạng gán tay được hiện trên thể lệ (The Vagabond Club, anh Việt 14/11/2026).
HANG_MOI_HIEN = {"AMBASSADOR"}
KB_SINH_NHAT = "sinh_nhat"
NHAC_TRUOC_NGAY = 30
HE_SO_TOI_DA = 10

THU = ("thu_2", "thu_3", "thu_4", "thu_5", "thu_6", "thu_7", "thu_cn")
TEN_THU = ("thứ Hai", "thứ Ba", "thứ Tư", "thứ Năm", "thứ Sáu", "thứ Bảy", "Chủ nhật")


# ------------------------------------------------------------ phép tính THUẦN


def _so(v, md=0.0):
	try:
		return float(v)
	except (TypeError, ValueError):
		return md


def _ngay(v):
	if isinstance(v, datetime):
		return v.date()
	if isinstance(v, date):
		return v
	try:
		return datetime.strptime(str(v)[:10], "%Y-%m-%d").date()
	except (TypeError, ValueError):
		return None


def cong_thang(d, so_thang):
	"""Cộng số tháng, ngày cuối tháng thì kẹp về ngày cuối của tháng đích. THUẦN."""
	import calendar

	th = d.month - 1 + int(so_thang)
	nam, th = d.year + th // 12, th % 12 + 1
	return date(nam, th, min(d.day, calendar.monthrange(nam, th)[1]))


def he_so(gia_tri):
	"""Hệ số nhân điểm của một chương trình. Ô người điền tay: "2", "x2", "2,5",
	trống hay số lạ đều phải ra một số hợp lý. Dưới 1 coi như 1 (không bao giờ
	làm khách MẤT điểm vì một ô điền nhầm), trên HE_SO_TOI_DA thì kẹp. THUẦN."""
	s = str(gia_tri if gia_tri is not None else "").strip().lower().lstrip("x").replace(",", ".")
	h = _so(s, 1.0)
	if h != h or h < 1:  # NaN hoặc dưới 1
		return 1.0
	return min(h, float(HE_SO_TOI_DA))


def chon_he_so(ds_hop):
	"""Nhiều chương trình nhân điểm cùng khớp thì lấy hệ số LỚN NHẤT, không nhân
	chồng (x2 và x3 cùng ngày là x3, không phải x6). Trả (hệ số, tên). THUẦN."""
	tot, ten = 1.0, ""
	for km in ds_hop or []:
		h = he_so(km.get("gia_tri"))
		if h > tot:
			tot, ten = h, str(km.get("ten") or "")
	return tot, ten


def diem_nhan(diem_goc, hs):
	"""Điểm sau khi nhân, làm tròn như diem_cho_don. THUẦN."""
	d = _so(diem_goc)
	if d <= 0:
		return 0
	return int(round(d * he_so(hs)))


def chuoi_he_so(hs):
	h = he_so(hs)
	return "x%d" % h if h == int(h) else ("x%s" % ("%.1f" % h).replace(".", ","))


def cau_nhan_diem(km):
	"""Câu cho khách đọc trên thể lệ, ví dụ "Thứ Năm hằng tuần, đặt bánh trên
	web được x2 điểm." Đọc từ đúng các ô của chương trình. THUẦN."""
	thu = [TEN_THU[i] for i, t in enumerate(THU) if int(_so(km.get(t)))]
	kenh = [k.strip() for k in str(km.get("kenh") or "").splitlines() if k.strip()]
	phan = []
	if thu and len(thu) < 7:
		phan.append(("%s hằng tuần" % ", ".join(thu)))
	if km.get("tu_ngay") and km.get("den_ngay"):
		phan.append("từ %s tới %s" % (ngay_vn(km["tu_ngay"]), ngay_vn(km["den_ngay"])))
	elif km.get("den_ngay"):
		phan.append("tới hết %s" % ngay_vn(km["den_ngay"]))
	if kenh == [NGUON_WEB]:
		viec = "đặt bánh trên web"
	elif kenh:
		viec = "mua qua %s" % ", ".join(kenh)
	else:
		viec = "mua bánh"
	dau = ", ".join(phan)
	cau = "%s, %s được %s điểm." % (dau, viec, chuoi_he_so(km.get("gia_tri"))) if dau else \
		"%s được %s điểm." % (viec[0].upper() + viec[1:], chuoi_he_so(km.get("gia_tri")))
	return cau[0].upper() + cau[1:]


def ngay_vn(v):
	d = _ngay(v)
	return d.strftime("%d/%m/%Y") if d else ""


def moc_han(d, han_thang):
	"""Mốc của việc hết hạn định kỳ vào ngày d: bút tích TRƯỚC mốc này là đã quá
	hạn (diem_han.qua_han_cuon_chieu). Một phép cho mọi chỗ cần mốc. THUẦN."""
	return str(cong_thang(d, -int(_so(han_thang))))


def ngay_het_lan_tich(ngay_tich, han_thang):
	"""Ngày ĐẦU TIÊN việc định kỳ coi bút tích ngày ngay_tich là quá hạn, tức ngày
	điểm của lần tích đó mất. Cùng luật sap_het_han: dò quanh ngay_tich cộng
	han_thang tháng, vì lùi tháng có kẹp ngày cuối tháng không nghịch đảo được
	phép cộng tháng (bút 28/02, 31/01). THUẦN."""
	e = _ngay(ngay_tich)
	if not e or int(_so(han_thang)) <= 0:
		return None
	d = cong_thang(e, int(_so(han_thang))) - timedelta(days=4)
	while moc_han(d, han_thang) <= str(e):
		d += timedelta(days=1)
	while moc_han(d - timedelta(days=1), han_thang) > str(e):
		d -= timedelta(days=1)
	return d


def cac_lan_tich_con_han(but, hom_nay, han_thang):
	"""Các lần tích còn điểm và còn hạn, lần sắp hết hạn đứng đầu. THUẦN.

	Khối "Dùng điểm thế nào" (U3, anh Việt chốt 14/11/2026) vẽ dòng thời gian
	này. Cùng luật diem_han.qua_han_cuon_chieu: mọi bút âm (đã tiêu, đã hết
	hạn, đã trừ) trừ vào lần tích CŨ nhất trước. Lần tích có ngày mất đã tới
	(việc định kỳ đêm nay sẽ ghi bút hết hạn) không còn tính là còn hạn.
	Trả [{"diem", "ngay_tich", "ngay_het", "het"}], het là date để sắp.
	"""
	hn = _ngay(hom_nay)
	if not hn or int(_so(han_thang)) <= 0:
		return []
	lo = []
	da_ra = 0.0
	so_du = 0.0
	for ngay, diem in sorted(but or [], key=lambda x: str(x[0] or "")):
		d = _so(diem)
		so_du += d
		if d > 0:
			lo.append([str(ngay or "")[:10], d])
		elif d < 0:
			da_ra += -d
	ra = []
	for ngay, d in lo:
		tru = min(d, da_ra)
		da_ra -= tru
		con = d - tru
		if con < 1:
			continue
		het = ngay_het_lan_tich(ngay, han_thang)
		if het and het > hn:
			ra.append({"diem": int(con), "ngay_tich": ngay_vn(ngay), "ngay_het": ngay_vn(het), "het": het})
	ra.sort(key=lambda x: x["het"])
	# Không bao giờ hiện quá số dư đang có (cùng luật qua_han_cuon_chieu).
	tran = max(0, int(so_du))
	tong = sum(x["diem"] for x in ra)
	while ra and tong > tran:
		bot = min(ra[-1]["diem"], tong - tran)
		ra[-1]["diem"] -= bot
		tong -= bot
		if ra[-1]["diem"] <= 0:
			ra.pop()
	return ra


def tom_tat_lan_tich(ds, so_hien=3):
	"""Ba lần sắp hết hạn nhất hiện riêng, phần còn lại gộp một dòng. THUẦN."""
	ds = list(ds or [])
	dau = [{k: x[k] for k in ("diem", "ngay_tich", "ngay_het")} for x in ds[:so_hien]]
	con = ds[so_hien:]
	return {"ds": dau, "khac": {"diem": sum(x["diem"] for x in con), "so": len(con)},
		"tong": sum(x["diem"] for x in ds)}


def sap_het_han(but, hom_nay, han_thang, so_ngay=NHAC_TRUOC_NGAY):
	"""Điểm sẽ hết hạn trong `so_ngay` tới theo cách cuốn chiếu, và ngày mất đầu
	tiên. Trả {"diem", "ngay"} hoặc None. THUẦN.

	Cùng luật diem_han.qua_han_cuon_chieu (vào trước ra trước, trừ phần đã tiêu,
	không quá số dư). Bút tích ngày e hết hạn ở ngày đầu tiên mà mốc của job
	(hôm đó lùi han_thang tháng, kẹp cuối tháng) đã vượt e.
	"""
	from vagabond.diem_han import qua_han_cuon_chieu

	hn = _ngay(hom_nay)
	if not hn or int(_so(han_thang)) <= 0:
		return None

	def moc(d):
		return moc_han(d, han_thang)

	da_mat = qua_han_cuon_chieu(but, moc(hn))
	cuoi = hn + timedelta(days=int(so_ngay))
	tong = qua_han_cuon_chieu(but, moc(cuoi)) - da_mat
	if tong <= 0:
		return None
	# Codex #557 vòng 3: ngày mất là ngày ĐẦU TIÊN mà mốc của việc định kỳ (hôm đó
	# lùi han_thang tháng) vượt qua bút tích. Dò từng ngày trong khung nhắc, không
	# cộng tháng xuôi từ ngày tích: bút cuối tháng (28/02 cộng 1 tháng là 28/03)
	# không nghịch đảo được phép lùi tháng có kẹp ngày cuối tháng của việc định kỳ.
	ngay_mat = None
	for i in range(1, int(so_ngay) + 1):
		d = hn + timedelta(days=i)
		if qua_han_cuon_chieu(but, moc(d)) - da_mat > 0:
			ngay_mat = d
			break
	if ngay_mat:
		# Codex #557: chỉ số điểm mất ĐÚNG ngày đầu tiên đó, không cộng các đợt
		# mất ngày sau trong 30 ngày (câu nhắc ghi "X điểm hết hạn ngày D").
		tong = qua_han_cuon_chieu(but, moc(ngay_mat)) - da_mat
	return {"diem": int(tong), "ngay": ngay_vn(ngay_mat or cuoi)}


def xet_web(co_phien, khach, hang, so_du, tien_banh, dung, quy_doi, tran_pt, toi_thieu):
	"""Khách web dùng điểm được không, bao nhiêu. THUẦN.

	tien_banh: tiền bánh SAU mọi ưu đãi khác, chưa có phí giao. Trả dict:
	trang_thai (can_xac_thuc | khong_co | cam | chua_du | dung_duoc), so_du,
	toi_da (điểm dùng được), dung (điểm áp vào đơn), tien (đồng giảm).
	Chưa xác thực số thì KHÔNG trả số dư: không cho người gõ số người khác đọc
	điểm của họ.
	"""
	from vagabond.diem_otp import tien_tu_diem, tran_dung_duoc

	ra = {"trang_thai": "can_xac_thuc", "so_du": 0, "toi_da": 0, "tien_toi_da": 0, "dung": 0, "tien": 0}
	if not co_phien:
		return ra
	if not khach:
		ra["trang_thai"] = "khong_co"
		return ra
	ra["so_du"] = int(_so(so_du))
	if str(hang or "").strip().upper() in HANG_CAM_TIEU:
		ra["trang_thai"] = "cam"
		return ra
	toi_da = tran_dung_duoc(tien_banh, so_du, quy_doi, tran_pt, toi_thieu)
	ra["toi_da"] = int(toi_da)
	if toi_da <= 0:
		ra["trang_thai"] = "chua_du"
		return ra
	ra["trang_thai"] = "dung_duoc"
	ra["tien_toi_da"] = int(tien_tu_diem(toi_da, quy_doi))
	if dung:
		ra["dung"] = int(toi_da)
		ra["tien"] = int(tien_tu_diem(toi_da, quy_doi))
	return ra


def dac_quyen_tu_ctkm(ten_hang, ds_ctkm):
	"""Quyền lợi của một hạng: tên các chương trình đang bật, đặt theo hạng
	khách, có hạng đó và đang hiện trên website. THUẦN."""
	ra = []
	h = str(ten_hang or "").strip().upper()
	for km in ds_ctkm or []:
		if (km.get("doi_tuong") or "") != "Theo hang khach" or not int(_so(km.get("hien_web"))):
			continue
		if km.get("cach_thuc") == CACH_NHAN:
			continue
		ds = [x.strip().upper() for x in str(km.get("hang_khach") or "").splitlines() if x.strip()]
		ten = str(km.get("ten") or "").strip()
		if h in ds and ten and ten not in ra:
			ra.append(ten)
	return ra


def bang_the_le(hang_ds, ctkm_ds):
	"""Các hạng hiện trên thể lệ: hạng theo chi tiêu đang bật, theo thứ tự. THUẦN."""
	ra = []
	for h in sorted(hang_ds or [], key=lambda x: (int(_so(x.get("thu_tu"))), str(x.get("ten_hang") or ""))):
		if (h.get("loai") or "Theo chi tieu") != "Theo chi tieu" or not int(_so(h.get("bat"), 1)):
			continue
		ten = h.get("ten_hang") or h.get("name")
		ra.append({"ten_hang": ten, "chi_tieu_tu": _so(h.get("chi_tieu_tu")),
			"so_thang_xet": int(_so(h.get("so_thang_xet"))) or 12, "tich_diem": _so(h.get("tich_diem")),
			"giam_gia": _so(h.get("giam_gia")), "dac_quyen": dac_quyen_tu_ctkm(ten, ctkm_ds)})
	return ra


def bang_hang_moi(hang_ds, ctkm_ds):
	"""Hạng gán tay hiện trên thể lệ: chỉ hạng trong HANG_MOI_HIEN đang bật (anh
	Việt 14/11/2026: AMBASSADOR do Vagabond mời; FAMILY, OWNER không hiện). Số
	giảm, số tích đọc từ hạng trên site, không cứng trong mã. THUẦN."""
	ra = []
	for h in sorted(hang_ds or [], key=lambda x: (int(_so(x.get("thu_tu"))), str(x.get("ten_hang") or ""))):
		ten = h.get("ten_hang") or h.get("name")
		if (h.get("loai") or "Theo chi tieu") == "Theo chi tieu" or not int(_so(h.get("bat"), 1)):
			continue
		if str(ten or "").strip().upper() not in HANG_MOI_HIEN:
			continue
		ra.append({"ten_hang": ten, "chi_tieu_tu": 0, "so_thang_xet": int(_so(h.get("so_thang_xet"))) or 12,
			"tich_diem": _so(h.get("tich_diem")), "giam_gia": _so(h.get("giam_gia")), "moi": 1,
			"dac_quyen": dac_quyen_tu_ctkm(ten, ctkm_ds)})
	return ra


def ctkm_trong_han(km, hom_nay):
	"""Chương trình đã tới ngày bắt đầu và chưa qua ngày kết thúc. THUẦN.

	Cùng luật ngày với cửa quầy (khuyen_mai._hop_thoi_gian): trang không kể
	đặc quyền mà quầy sẽ từ chối (Codex PR #566)."""
	hn = _ngay(hom_nay)
	tu, den = _ngay(km.get("tu_ngay")), _ngay(km.get("den_ngay"))
	if hn and tu and hn < tu:
		return False
	if hn and den and hn > den:
		return False
	return True


def qua_sinh_nhat_tu_ctkm(km, hom_nay, kb):
	"""Quà sinh nhật đọc từ chương trình kịch bản Zalo Sinh nhật đang dùng. THUẦN.

	Trả {"ten", "nhom", "toi_da", "hang", "truoc", "han"} khi kịch bản Zalo Sinh
	nhật đang BẬT (quà chỉ tới tay khách qua tin này), chương trình bật, hiện
	web, đặt theo hạng VÀ hôm nay còn phát được mã; "nhom", "toi_da" chỉ có khi
	là tặng trọn một bánh trong một nhóm món (giảm 100% món, có trần). "truoc"
	là số ngày gửi trước sinh nhật, "han" là số ngày mã dùng được, đọc từ kịch
	bản và kẹp theo chương trình bằng đúng cửa cấp mã. Không đủ thì None:
	trang không hứa quà.

	Có phát được hay không hỏi đúng MỘT cửa: zalo_kich_ban.ctkm_phat_duoc, cửa
	mà tin sinh nhật và Ví quà (thanh_vien) dùng để cấp mã. Chương trình chưa
	bắt đầu, đã qua ngày kết thúc, hạn mã đã qua hay không phải mã dùng một lần
	thì không cấp được, nên trang cũng không hứa (Codex PR #566)."""
	if not kb or not int(_so(kb.get("bat"))):
		return None
	if not km or not int(_so(km.get("bat"))) or not int(_so(km.get("hien_web"))):
		return None
	from vagabond.zalo_kich_ban import ctkm_phat_duoc

	hn = _ngay(hom_nay)
	han, _ = ctkm_phat_duoc(km, hn, kb.get("han_ngay"))
	if not han:
		return None
	if (km.get("doi_tuong") or "") != "Theo hang khach":
		return None
	hang = [x.strip().upper() for x in str(km.get("hang_khach") or "").splitlines() if x.strip()]
	if not hang:
		return None
	ra = {"ten": str(km.get("ten") or "").strip(), "nhom": "", "toi_da": 0, "hang": hang,
		"truoc": max(0, int(_so(kb.get("so_ngay")))), "han": max(1, (han - hn).days)}
	if (km.get("kieu_giam") == "Phan tram" and _so(km.get("gia_tri")) >= 100
			and km.get("pham_vi") == "Nhom mon chi dinh" and str(km.get("nhom_mon") or "").strip()):
		ra["nhom"] = str(km.get("nhom_mon")).strip()
		ra["toi_da"] = int(_so(km.get("giam_toi_da")))
	return ra


# ------------------------------------------------------------------ chạm hệ


def _ghi_chu(ten_don):
	from vagabond.don_web import GHI_CHU_DON_WEB

	return GHI_CHU_DON_WEB % ten_don


def _cd():
	from vagabond import diem_otp

	return diem_otp._cd()


def khach_cua_sdt(sdt):
	"""Khách thành viên của một số (một hồ sơ duy nhất), rỗng khi không có hoặc
	nhiều hồ sơ trùng số (không đoán, cùng luật trang thành viên)."""
	from vagabond import don_dau_web, thanh_vien

	cs = don_dau_web.chin_so(sdt)
	if not cs:
		return None
	kh, ly = thanh_vien._khach_cua_so("0" + cs)
	return None if ly else kh


def phien_dung_so(sdt):
	"""Số đơn trùng số của phiên Thành viên đã xác thực qua Zalo trên trình duyệt này."""
	from vagabond import don_dau_web

	cs = don_dau_web.chin_so(sdt)
	return bool(cs) and don_dau_web.chin_so(don_dau_web.sdt_phien()) == cs


def thong_tin(sdt, tien_banh, dung=False):
	"""Phần "diem" của xem_uu_dai và tao_don. Lỗi phụ không chặn đơn: hỏng
	thì coi như chưa dùng được điểm, không bao giờ giảm oan."""
	import frappe

	try:
		co = phien_dung_so(sdt)
		kh = khach_cua_sdt(sdt) if co else None
		so_du = 0
		if kh:
			from vagabond.diem_otp import _so_du

			so_du = _so_du(kh["name"])
		c = _cd()
		ra = xet_web(co, kh and kh["name"], kh and kh.get("vgb_hang"), so_du, tien_banh, dung,
			c["quy_doi"], c["tran_pt"], c["bill_toi_thieu"])
		ra["khach"] = kh["name"] if kh else ""
		if kh:
			try:
				from vagabond import thanh_vien

				ra["len_hang"] = thanh_vien._tien_do(kh["name"])
			except Exception:
				ra["len_hang"] = None
		return ra
	except Exception:
		frappe.log_error(title="Vagabond: điểm thành viên trên web", message=frappe.get_traceback())
		return {"trang_thai": "loi", "so_du": 0, "toi_da": 0, "dung": 0, "tien": 0, "khach": ""}


def giu_diem(ten_don, khach, diem, tien_banh):
	"""Trừ điểm cho đơn web, TRONG giao dịch tạo đơn (bên gọi commit). Khoá dòng
	khách, đọc lại số dư và trần ngay dưới khoá: hai đơn cùng lúc của một khách
	không cùng tiêu một số dư. Trả số điểm đã trừ, 0 nếu không còn đủ."""
	import frappe

	from vagabond import diem_otp
	from vagabond.khach_hang import _ghi_so_diem

	frappe.db.sql("select name from `tabCustomer` where name = %s for update", khach)
	c = _cd()
	so_du = _so_du_khoa(khach)
	toi_da = diem_otp.tran_dung_duoc(tien_banh, so_du, c["quy_doi"], c["tran_pt"], c["bill_toi_thieu"])
	if int(diem) <= 0 or int(toi_da) < int(diem):
		return 0
	_ghi_so_diem(khach, -abs(int(diem)), diem_otp.LOAI_TRU, None, _ghi_chu(ten_don))
	return int(diem)


def _so_du_khoa(khach):
	"""Số dư cộng lại từ sổ bằng phép đọc CÓ KHOÁ (Codex #557). MariaDB
	REPEATABLE READ: đọc thường trả ảnh chụp từ lần đọc đầu giao dịch (tao_don đã
	đọc số dư trước khi khoá khách), nên không thấy phần đơn khác vừa trừ và
	commit. FOR UPDATE đọc bản đã commit mới nhất."""
	import frappe

	from vagabond.diem_otp import SO_DIEM

	r = frappe.db.sql("select sum(diem) from `tab%s` where khach = %%s for update" % SO_DIEM, (khach,))
	return _so((r or [[0]])[0][0])


def _da_tru_cua_don(ten_don):
	import frappe

	from vagabond.diem_otp import LOAI_TRU

	# Đọc có khoá (Codex #557 vòng 2): bên gọi đã khoá đơn, phải thấy bản đã commit.
	r = frappe.db.sql("select khach, sum(diem) from `tabVagabond So Diem` where loai = %s and ghi_chu = %s"
		" group by khach for update", (LOAI_TRU, _ghi_chu(ten_don)))
	return [(k, abs(_so(d))) for k, d in (r or []) if _so(d) < 0]


def _da_hoan_cua_don(ten_don):
	import frappe

	from vagabond.diem_otp import LOAI_HOAN

	# Codex #557 vòng 2: lượt quét định kỳ đã đọc sổ (ảnh chụp REPEATABLE READ) trước
	# khi khoá đơn; đọc thường ở đây không thấy bút hoàn mà lượt hoàn ngay vừa
	# commit, hoàn hai lần. Đọc có khoá thấy bản đã commit.
	r = frappe.db.sql("select count(*) from `tabVagabond So Diem` where loai = %s and ghi_chu = %s for update",
		(LOAI_HOAN, _ghi_chu(ten_don)))
	return bool(r and r[0][0])


def hoan_don_web(ten_don, ly_do=""):
	"""Đơn web không thành: hoàn đúng số điểm đã trừ, một lần (bút ngược, không
	sửa bút cũ). Báo khách qua Zalo nếu kịch bản đang bật. Bên gọi commit."""
	import frappe

	from vagabond.diem_otp import LOAI_HOAN
	from vagabond.khach_hang import _ghi_so_diem

	frappe.db.sql("select name from `tabVagabond Don Web` where name = %s for update", ten_don)
	if _da_hoan_cua_don(ten_don):
		return 0
	n = 0
	for khach, diem in _da_tru_cua_don(ten_don):
		_ghi_so_diem(khach, int(diem), LOAI_HOAN, None, _ghi_chu(ten_don))
		n += int(diem)
		try:
			from vagabond import zalo_kich_ban

			zalo_kich_ban.cho_hoan_diem(khach, ten_don, int(diem))
		except Exception:
			frappe.log_error(title="Vagabond: xếp tin Zalo hoàn điểm", message=frappe.get_traceback())
	return n


def don_huy_con_giu_diem(gioi_han=200):
	"""Đơn web Đã huỷ còn bút trừ điểm chưa hoàn: lưới an toàn của việc định kỳ."""
	import frappe

	return [r[0] for r in frappe.db.sql(
		"select d.name from `tabVagabond Don Web` d where d.trang_thai='Da huy' and exists ("
		" select 1 from `tabVagabond So Diem` s where s.loai='Dung diem tru vao don'"
		" and s.ghi_chu=concat('Đơn web ', d.name)) and not exists ("
		" select 1 from `tabVagabond So Diem` h where h.loai='Hoan lai diem da dung'"
		" and h.ghi_chu=concat('Đơn web ', d.name)) limit %s", (int(gioi_han),))]


# ------------------------------------------------------------- nhân điểm


def ctkm_nhan_dang_bat():
	import frappe

	from vagabond.khuyen_mai import THU_TRONG_TUAN

	return frappe.get_all("Vagabond CTKM", filters={"bat": 1, "cach_thuc": CACH_NHAN},
		fields=["name", "ten", "gia_tri", "tu_ngay", "den_ngay", "gio_tu", "gio_den", "kenh", "quay",
			"doi_tuong", "hang_khach", "nhom_khach", "hien_web"] + THU_TRONG_TUAN, limit_page_length=0)


def he_so_luc(luc, nguon, quay, khach, sdt=None):
	"""Hệ số nhân điểm cho một lần mua: lúc mua, kênh, quầy, khách. Dùng đúng
	bộ lọc của khuyến mãi (thời gian, kênh, đối tượng). Trả (hệ số, tên)."""
	from vagabond import khuyen_mai as km_

	hop = []
	for km in ctkm_nhan_dang_bat():
		ok, _ = km_._hop_thoi_gian(km, luc)
		if ok:
			ok, _ = km_._hop_kenh(km, nguon, quay)
		if ok and not sdt and khach and km.get("doi_tuong") == "Nhan vien":
			# Codex #557 vòng 4: đối tượng Nhân viên xét theo SỐ ĐIỆN THOẠI; hoá đơn chỉ
			# có mã khách nên lấy số trên hồ sơ khách (cùng nguồn số nhận mã điểm).
			from vagabond.diem_otp import _sdt_khach

			sdt = _sdt_khach(khach) or None
		if ok:
			ok, _ = km_._hop_doi_tuong(km, khach, sdt)
		if ok:
			hop.append(km)
	return chon_he_so(hop)


def boi_canh_hoa_don(si):
	"""(lúc mua, nguồn, quầy) của một hoá đơn để xét nhân điểm. Đơn web lấy lúc
	khách ĐẶT (bản ghi Don Web), kênh Website; hoá đơn khác lấy ngày giờ hoá đơn."""
	import frappe

	ma = [str(x).strip() for x in (si.get("custom_pancake_id"), si.get("custom_pancake_display_id")) if str(x or "").strip()]
	if ma:
		dw = (frappe.db.get_value("Vagabond Don Web", {"pancake_display_id": ["in", ma]}, ["name", "creation"], as_dict=True)
			or frappe.db.get_value("Vagabond Don Web", {"pancake_id": ["in", ma]}, ["name", "creation"], as_dict=True))
		if dw:
			return dw.creation, NGUON_WEB, ""
	luc = "%s %s" % (si.get("posting_date") or "", str(si.get("posting_time") or "00:00:00")[:8])
	return luc.strip() or None, (si.get("custom_nguon") or ""), (si.get("vgb_quay") or "")


def diem_hoa_don(si, ty_le):
	"""MỘT NGUỒN cho số điểm một hoá đơn được tích: hook cộng điểm và tin cảm
	ơn (diem_cua_don) cùng gọi. Trả (điểm, hệ số, tên chương trình nhân)."""
	import frappe

	from vagabond.khach_hang import diem_cho_don

	goc = diem_cho_don(si.get("grand_total"), ty_le)
	if goc <= 0:
		return 0, 1.0, ""
	try:
		luc, nguon, quay = boi_canh_hoa_don(si)
		hs, ten = he_so_luc(luc, nguon, quay, si.get("customer"))
	except Exception:
		frappe.log_error(title="Vagabond: xét nhân điểm", message=frappe.get_traceback())
		hs, ten = 1.0, ""
	return diem_nhan(goc, hs), hs, ten


def cau_nhan_dang_chay(hom_nay=None):
	"""Câu mô tả các chương trình nhân điểm đang bật, hiện trên web, chưa hết
	hạn. Cho ô Tích của thể lệ."""
	hn = _ngay(hom_nay) or date.today()
	ra = []
	for km in ctkm_nhan_dang_bat():
		if not int(_so(km.get("hien_web"))):
			continue
		if km.get("den_ngay") and _ngay(km["den_ngay"]) and _ngay(km["den_ngay"]) < hn:
			continue
		if he_so(km.get("gia_tri")) <= 1:
			continue
		ra.append(cau_nhan_diem(km))
	return ra


# ------------------------------------------------------------------ thể lệ


def the_le(khach=None):
	"""Dữ liệu khối Thể lệ trên trang thành viên. Không có số riêng của khách
	trừ phần sap_het (chỉ khi có khach đã xác thực)."""
	import frappe
	from frappe.utils import nowdate

	from vagabond import diem_han

	hang = frappe.get_all("Vagabond Hang Khach", fields=["name", "ten_hang", "thu_tu", "loai", "giam_gia",
		"tich_diem", "chi_tieu_tu", "so_thang_xet", "bat"], limit_page_length=0)
	ctkm = frappe.get_all("Vagabond CTKM", filters={"bat": 1, "doi_tuong": "Theo hang khach", "hien_web": 1},
		fields=["name", "ten", "cach_thuc", "doi_tuong", "hang_khach", "hien_web", "tu_ngay", "den_ngay"], limit_page_length=0)
	hn = _ngay(nowdate())
	ctkm = [k for k in ctkm if ctkm_trong_han(k, hn)]
	c = _cd()
	cd_han = diem_han._cd()
	bang = bang_the_le(hang, ctkm)
	ra = {"hang": bang, "hang_moi": bang_hang_moi(hang, ctkm), "qua_sn": _qua_sn(hn), "lan_tich": None, "luat": {
		"tran_pt": c["tran_pt"], "toi_thieu": c["bill_toi_thieu"],
		"han_thang": cd_han["han_thang"] if cd_han["cach"] == "Cuon chieu" else 0,
		"cach_han": cd_han["cach"], "nhac_ngay": NHAC_TRUOC_NGAY,
		"so_thang_hang": max([h["so_thang_xet"] for h in bang] or [12]),
		"nhan_diem": cau_nhan_dang_chay(hn)}, "sap_het": None}
	if khach and cd_han["cach"] == "Cuon chieu":
		# Chỉ đọc bút của MỘT khách (diem_han._but_theo_khach đọc cả sổ cho job đêm).
		but = [(str(r[0]), _so(r[1])) for r in frappe.db.sql(
			"select date(ngay), diem from `tabVagabond So Diem` where khach = %s order by ngay", (khach,))]
		ra["sap_het"] = sap_het_han(but, hn, cd_han["han_thang"])
		# v658: dòng thời gian các lần tích còn hạn (khối Dùng điểm thế nào).
		ra["lan_tich"] = tom_tat_lan_tich(cac_lan_tich_con_han(but, hn, cd_han["han_thang"]))
	return ra


def _qua_sn(hn):
	"""Chương trình quà sinh nhật là chương trình gắn ở kịch bản Zalo Sinh nhật
	(một nguồn với tin gửi quà). Lỗi đọc thì không hiện quà, trang vẫn chạy."""
	import frappe

	try:
		kb = frappe.db.get_value("Vagabond Kich Ban Zalo", KB_SINH_NHAT, ["ctkm", "bat", "so_ngay", "han_ngay"], as_dict=True)
		ten = kb and kb.get("ctkm")
		if not ten:
			return None
		km = frappe.db.get_value("Vagabond CTKM", ten, ["name", "ten", "bat", "hien_web", "doi_tuong", "hang_khach",
			"kieu_giam", "gia_tri", "pham_vi", "nhom_mon", "giam_toi_da", "cach_ma", "tu_ngay", "den_ngay", "han_ma"],
			as_dict=True)
		return qua_sinh_nhat_tu_ctkm(km, hn, kb)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "diem_web: đọc quà sinh nhật")
		return None
