"""v530: nối hoá đơn đến sau NHIỀU-NHIỀU ở mức hồ sơ. Toàn phép THUẦN.

Vì sao có tệp này (chị Dung và anh Việt, 25/09/2026)
-----------------------------------------------------
Bản v526 nối MỘT tờ hoá đơn vào MỘT khoản chi, và chỉ nhận tờ còn nháp. Ba
hồ sơ thật không nối được:

  - APP.26.09.009 Adecco: chị Dung tách một hoá đơn 686.810.159 đ thành ba
    khoản theo bộ phận (Bếp, KD, VP). Một tờ phải phủ ba khoản.
  - APP.26.09.102 Mobifone: nhà cung cấp xuất hoá đơn theo từng số thuê bao,
    sáu tờ cộng đúng 778.784 đ mà chị trả một lần. Sáu tờ phải phủ một khoản.
    Sáu tờ lại mang mã số thuế chi nhánh đuôi -096, hồ sơ chọn chi nhánh
    đuôi -002: lọc đúng tên nhà cung cấp thì không ra tờ nào.
  - APP.26.08.016 Văn An: tờ số 262 đã ghi sổ trước khi nối.

Cả ba hồ sơ đều có tờ đúng ĐÃ GHI SỔ và còn nguyên công nợ, trong khi hồ sơ
đã ghi Nợ chi phí qua bút toán của nó: chi phí vào sổ hai lần và một khoản
nợ không bao giờ trả. Ô chọn cũ giấu tờ đã ghi sổ nên người dùng không thấy
tờ đúng.

Cách làm từ v530
----------------
1. Nối ở mức HỒ SƠ: chọn nhiều tờ, so TỔNG tờ với tổng các khoản chờ hoá đơn.
   Khoản tách theo bộ phận giữ nguyên để hạch toán.
2. Nhóm nhà cung cấp theo MÃ SỐ THUẾ GỐC 10 số: các chi nhánh về chung một
   nhóm. Tờ ngoài nhóm vẫn nối được khi người dùng xác nhận (đường tay).
3. Tờ nháp: như v526, nối làm chứng từ và không được ghi sổ nữa.
   Tờ ĐÃ ghi sổ còn nợ (hồ sơ chi từ TK công ty): máy lập MỘT bút toán bù trừ
   Nợ 331 (trả đúng tờ đó) / Có đúng các tài khoản chi phí hồ sơ đã ghi. Chi
   phí còn lại đúng một lần, theo tài khoản và thuế GTGT của tờ hoá đơn; công
   nợ về 0; dòng tiền ngân hàng không đổi.
4. Máy gợi ý: số hoá đơn ghi trên khoản, rồi một tờ khớp tiền, rồi tổ hợp ít
   tờ nhất cộng đúng số còn thiếu. Người dùng bấm một lần, hoặc tự tích tay.
5. Không chặn vì lệch tiền: nối được, hồ sơ chỉ chưa thành Hợp lệ tính thuế.
"""

NGUONG = 1000.0


def _tien(v):
	try:
		return float(v or 0)
	except (TypeError, ValueError):
		return 0.0


def _so(v):
	try:
		return int(v or 0)
	except (TypeError, ValueError):
		return 0


def dd(v):
	return "{:,.0f}".format(_tien(v)).replace(",", ".")


def mst_goc(ma_so_thue):
	"""10 chữ số đầu của mã số thuế: chi nhánh (đuôi -002, -096) về chung gốc.
	Thiếu hoặc ngắn hơn 10 số thì trả rỗng, nghĩa là không nhóm theo MST."""
	so = "".join(c for c in str(ma_so_thue or "") if c.isdigit())
	return so[:10] if len(so) >= 10 else ""


def cung_nhom(ncc_ho_so, mst_ho_so, ncc_to, mst_to):
	"""Tờ có thuộc nhóm nhà cung cấp của hồ sơ không: cùng tên, hoặc cùng MST gốc."""
	if (ncc_ho_so or "") == (ncc_to or ""):
		return True
	a, b = mst_goc(mst_ho_so), mst_goc(mst_to)
	return bool(a) and a == b


def da_ghi_so(to):
	return _so((to or {}).get("docstatus")) == 1


def tien_khop(to):
	"""Số tiền tờ này đem ra khớp với khoản chi: tờ đã ghi sổ lấy số CÒN NỢ
	(phần đã trả ở chỗ khác không được tính lại), tờ nháp lấy tổng tờ."""
	to = to or {}
	if da_ghi_so(to):
		return max(_tien(to.get("outstanding_amount")), 0.0)
	return _tien(to.get("grand_total"))


def nhan_to(to):
	"""Nhãn trạng thái tờ cho người dùng, không mã kỹ thuật."""
	to = to or {}
	if _so(to.get("docstatus")) == 2:
		return "Đã huỷ"
	if da_ghi_so(to):
		con = _tien(to.get("outstanding_amount"))
		return ("Đã ghi sổ, còn nợ %s đ" % dd(con)) if con > 0.5 else "Đã ghi sổ, đã trả hết"
	return "Nháp, chưa ghi sổ"


def loi_noi_to(to, ho_so_khac="", tkct=True, trong_nhom=True, cho_ngoai_nhom=False, dung_cong_ty=True):
	"""Tờ này nối vào hồ sơ được không. Trả câu lỗi, rỗng là được. THUẦN.

	to: {docstatus, vgb_huy, outstanding_amount}. tkct: hồ sơ Chi từ TK công ty.
	Không còn luật "chỉ nối tờ nháp": tờ đã ghi sổ còn nợ thì máy bù trừ.
	Tờ đã ghi sổ mà ĐÃ TRẢ HẾT ở chỗ khác thì hồ sơ TK công ty không nối được:
	khoản đó đã có người trả, nối vào là trả hai lần."""
	to = to or {}
	if _so(to.get("docstatus")) == 2:
		return "đã huỷ"
	if _so(to.get("vgb_huy")):
		return "đã đánh dấu huỷ (bản nháp bỏ đi), không làm chứng từ được"
	if not dung_cong_ty:
		return "thuộc công ty khác"
	if ho_so_khac:
		return "đã nối vào hồ sơ %s rồi" % ho_so_khac
	if not trong_nhom and not cho_ngoai_nhom:
		return ("của nhà cung cấp khác (khác mã số thuế). Kiểm lại tờ, nếu đúng thì xác nhận "
			"nối ngoài nhà cung cấp")
	if tkct and da_ghi_so(to) and tien_khop(to) <= 0.5:
		return ("đã ghi sổ và đã trả hết ở chỗ khác. Khoản chi này nối vào nữa là trả hai lần. "
			"Kiểm lại phiếu đã trả tờ đó")
	return ""


def _chuan_so_hd(v):
	s = "".join(c for c in str(v or "") if c.isalnum()).upper()
	return s.lstrip("0") or ("0" if s else "")


def _tim_to_hop(ds, can, nguong, gioi_han):
	"""Tổ hợp ÍT TỜ NHẤT cộng trong [can - nguong, can + nguong].

	ds: [(tiền, chỉ số)] đã xếp giảm dần. Trả (lời giải, có lời giải thứ hai
	cùng số tờ không, hết ngân sách không). Duyệt theo số tờ tăng dần, cắt
	nhánh khi tổng vượt, hoặc khi cộng hết phần còn lại vẫn không tới."""
	n = len(ds)
	buoc = [0]
	cong_duoi = [0.0] * (n + 1)
	for i in range(n - 1, -1, -1):
		cong_duoi[i] = cong_duoi[i + 1] + ds[i][0]

	def dfs(bat_dau, con_lai, tong, chon, gap):
		buoc[0] += 1
		if buoc[0] > gioi_han:
			return
		if con_lai == 0:
			if abs(tong - can) <= nguong:
				gap.append(list(chon))
			return
		for i in range(bat_dau, n - con_lai + 1):
			if len(gap) >= 2 or buoc[0] > gioi_han:
				return
			t = tong + ds[i][0]
			if t > can + nguong:
				continue
			# Lấy con_lai tờ lớn nhất kể từ i mà vẫn không tới thì dừng hẳn.
			if tong + sum(x[0] for x in ds[i:i + con_lai]) < can - nguong:
				return
			chon.append(ds[i][1])
			dfs(i + 1, con_lai - 1, t, chon, gap)
			chon.pop()

	for k in range(2, n + 1):
		if cong_duoi[0] < can - nguong:
			break
		gap = []
		dfs(0, k, 0.0, [], gap)
		if gap:
			return gap[0], len(gap) > 1, False
		if buoc[0] > gioi_han:
			return None, False, True
	return None, False, False


def goi_y(ung_vien, can, so_hd_khoan=(), nguong=NGUONG, toi_da=22, gioi_han=200000):
	"""Máy gợi ý tờ cần nối. THUẦN.

	ung_vien: [{"name", "bill_no", "tien"}] đã xếp theo ưu tiên (gần ngày hồ
	sơ trước). can: số còn thiếu. so_hd_khoan: số hoá đơn ghi trên các khoản.
	Trả None hoặc {"hoa_don": [...], "tong", "ly_do", "con_cach_khac"}.

	Tìm KHỚP ĐÚNG TỪNG ĐỒNG trước, hết cách mới nới ra ngưỡng: với ngưỡng
	1.000 đ ngay từ đầu, ca Mobifone ra tổ hợp 5 tờ lệch 609 đ trước tổ hợp
	6 tờ khớp đúng (đo thật khi viết, 25/09/2026).
	con_cach_khac=True: có lựa chọn khác cùng số tờ khớp tiền, người dùng nên
	kiểm số hoá đơn trước khi bấm (ví dụ hai tháng cùng một số tiền cước)."""
	for nguong_thu in (0.5, nguong):
		kq = _goi_y_mot_nguong(ung_vien, can, so_hd_khoan, nguong_thu, toi_da, gioi_han)
		if kq:
			lech = kq["tong"] - _tien(can)
			if abs(lech) > 0.5:
				kq["ly_do"] += ", lệch %s đ" % dd(abs(lech))
			return kq
	return None


def _goi_y_mot_nguong(ung_vien, can, so_hd_khoan, nguong, toi_da, gioi_han):
	can = _tien(can)
	ds = [u for u in (ung_vien or []) if _tien(u.get("tien")) > 0.5]
	if can <= NGUONG or not ds:
		return None

	def ra(cac, ly_do, khac=False):
		return {"hoa_don": [u["name"] for u in cac], "tong": sum(_tien(u["tien"]) for u in cac),
			"ly_do": ly_do, "con_cach_khac": bool(khac)}

	so = {_chuan_so_hd(x) for x in (so_hd_khoan or ()) if _chuan_so_hd(x)}
	if so:
		theo_so = [u for u in ds if _chuan_so_hd(u.get("bill_no")) in so]
		if theo_so and abs(sum(_tien(u["tien"]) for u in theo_so) - can) <= nguong:
			return ra(theo_so, "Khớp số hoá đơn ghi trên khoản chi")

	mot = [u for u in ds if abs(_tien(u["tien"]) - can) <= nguong]
	if mot:
		mot.sort(key=lambda u: abs(_tien(u["tien"]) - can))
		return ra([mot[0]], "Một hoá đơn đúng số tiền còn thiếu", len(mot) > 1)

	kho = [u for u in ds if _tien(u["tien"]) <= can + nguong][:toi_da]
	xep = sorted(((_tien(u["tien"]), i) for i, u in enumerate(kho)), reverse=True)
	loi_giai, khac, _het = _tim_to_hop(xep, can, nguong, gioi_han)
	if not loi_giai:
		return None
	cac = [kho[i] for i in sorted(loi_giai)]
	return ra(cac, "%d hoá đơn cộng lại %s đ" % (len(cac), dd(sum(_tien(u["tien"]) for u in cac))), khac)


def la_khoan_cong_no(tk_no, loai_tk):
	"""Khoản ghi Nợ thẳng vào tài khoản công nợ (331, 131) không phải chi phí:
	không có gì để bù trừ."""
	return (loai_tk or "") in ("Payable", "Receivable")


def ke_hoach_bu_tru(khoan, da_dung, can_bu):
	"""Tờ đã ghi sổ còn nợ `can_bu`: Có những tài khoản chi phí nào của hồ sơ.

	khoan: [{"idx", "tk_no", "so_tien", "cong_no"}] đúng thứ tự khoản. Chỉ
	khoản chi phí (cong_no False) mới đem bù. da_dung: phần chi phí hồ sơ đã
	được các tờ nối TRƯỚC dùng (tờ nháp và các lần bù trừ trước), đi theo cùng
	thứ tự khoản nên kết quả cố định. Trả (số bù, [(tài khoản, tiền)]); số bù
	= min(can_bu, phần chi phí còn lại). THUẦN."""
	bo_qua = max(_tien(da_dung), 0.0)
	con = max(_tien(can_bu), 0.0)
	ra, thu_tu = {}, []
	for k in khoan or []:
		if k.get("cong_no") or not k.get("tk_no"):
			continue
		st = max(_tien(k.get("so_tien")), 0.0)
		if bo_qua >= st:
			bo_qua -= st
			continue
		st -= bo_qua
		bo_qua = 0.0
		lay = min(st, con)
		if lay > 0.004:
			if k["tk_no"] not in ra:
				thu_tu.append(k["tk_no"])
				ra[k["tk_no"]] = 0.0
			ra[k["tk_no"]] += lay
			con -= lay
		if con <= 0.004:
			break
	dong = [(tk, round(ra[tk], 2)) for tk in thu_tu]
	return round(sum(t for _tk, t in dong), 2), dong


def dong_but_toan_bu_tru(to, so_bu, ke_hoach, ttcp):
	"""Các dòng Journal Entry bù trừ. THUẦN.

	to: {"name", "supplier", "credit_to"}. Nợ 331 đúng tờ (tham chiếu tờ để
	công nợ tờ giảm), Có từng tài khoản chi phí theo kế hoạch."""
	dong = [{
		"account": to["credit_to"], "party_type": "Supplier", "party": to["supplier"],
		"debit_in_account_currency": round(_tien(so_bu), 2),
		"reference_type": "Purchase Invoice", "reference_name": to["name"],
		"cost_center": ttcp,
	}]
	for tk, tien in ke_hoach:
		dong.append({"account": tk, "credit_in_account_currency": round(_tien(tien), 2), "cost_center": ttcp})
	return dong


def ngay_bu_tru(ngay_thanh_toan, ngay_to):
	"""Ngày bút toán bù trừ: ngày hồ sơ đã chi, nhưng không trước ngày tờ vào
	sổ (trả trước khi tờ tồn tại là vô lý). Chuỗi yyyy-mm-dd so được thẳng."""
	a, b = str(ngay_thanh_toan or "")[:10], str(ngay_to or "")[:10]
	return max(a, b) if a and b else (a or b)


def do_phu(khoan, lien_ket, nguong=NGUONG):
	"""Mức phủ của hồ sơ. THUẦN.

	khoan: [{"so_tien", "hoa_don", "hoa_don_bo_sung"}]. Khoản đã có hoá đơn
	gốc hoặc đã nối kiểu cũ (một tờ một khoản) thì đã có chứng từ riêng, không
	tính vào số cần. lien_ket: [{"tien_khop"}] các tờ nối kiểu v530."""
	# Khoản ghi Nợ thẳng công nợ (cong_no) là trả nợ, không phải chi phí chờ
	# hoá đơn: không tính vào số cần.
	can = sum(_tien(k.get("so_tien")) for k in (khoan or [])
		if not (k.get("hoa_don") or "").strip() and not (k.get("hoa_don_bo_sung") or "").strip()
		and not k.get("cong_no"))
	da = sum(_tien(x.get("tien_khop")) for x in (lien_ket or []))
	return {"can": round(can, 2), "da_noi": round(da, 2), "con_thieu": round(max(can - da, 0.0), 2),
		"thua": round(max(da - can, 0.0), 2), "du": abs(can - da) <= nguong}


def co_hoa_don(k):
	"""Khoản có đường tới hoá đơn: mang hoá đơn gốc, hoặc là hoá đơn đến sau."""
	k = k or {}
	return bool((k.get("hoa_don") or "").strip()) or bool(_so(k.get("cho_hoa_don")))


def du_dieu_kien(khoan):
	"""Nhãn hợp lệ của hồ sơ có dựa vào hoá đơn không: MỌI khoản đều mang
	hoá đơn gốc hoặc chờ hoá đơn đến sau. Còn khoản không hoá đơn thật thì
	nhãn là do người lập chọn theo chứng từ khác, luật hoá đơn không đụng."""
	ds = list(khoan or [])
	return bool(ds) and all(co_hoa_don(k) for k in ds)


def nen_hop_le(khoan, lien_ket, lech_cu=(), nguong=NGUONG):
	"""Hồ sơ TK công ty là Hợp lệ tính thuế khi: mọi khoản có đường tới hoá
	đơn (gốc hoặc đến sau), các tờ nối kiểu cũ không lệch tiền, và các tờ nối
	kiểu v530 phủ ĐÚNG phần khoản chưa có hoá đơn gốc (không thiếu, không
	thừa quá ngưỡng). THUẦN.

	Codex #373 vòng 4 (05c3866): bản trước đòi MỌI khoản chờ hoá đơn, nên hồ
	sơ lẫn khoản có hoá đơn gốc không bao giờ được xét theo mức phủ, nối thừa
	vẫn giữ nhãn hợp lệ. Khoản có hoá đơn gốc tự có chứng từ; mức phủ chỉ tính
	phần còn lại (do_phu đã loại khoản có hoá đơn gốc)."""
	ds = list(khoan or [])
	if not du_dieu_kien(ds):
		return False
	if list(lech_cu or []):
		return False
	p = do_phu(ds, lien_ket, nguong)
	if not lien_ket and p["can"] > nguong:
		return False
	return p["du"]


# Mọi ô lưu của một dòng tờ nối. Codex #373 vòng 1 (33fb7d5): bản đầu chỉ so
# bốn ô, sửa tay tong_hd làm yếu luật chặn đổi tổng tờ, sửa da_ghi_so làm
# lệch phần chi phí đã dùng của lần bù trừ sau. Ô nào đã lưu đều không sửa tay.
TRUONG_HD_SAU = ("hoa_don", "so_hd_ncc", "ncc", "tong_hd", "tien_khop", "da_ghi_so", "bu_tru",
	"but_toan", "ngoai_ncc", "noi_boi", "noi_luc")
_SO = ("tong_hd", "tien_khop", "bu_tru")
_CO = ("da_ghi_so", "ngoai_ncc")


def khoa_dong(r):
	r = r or {}
	ra = []
	for k in TRUONG_HD_SAU:
		v = r.get(k)
		if k in _SO:
			ra.append(round(_tien(v), 2))
		elif k in _CO:
			ra.append(_so(v))
		else:
			ra.append(str(v or "").strip()[:19] if k == "noi_luc" else str(v or "").strip())
	return tuple(ra)


def loi_sua_hd_sau(cu, moi, cho_phep=False):
	"""Bảng tờ nối kiểu v530 chỉ đổi qua nút Nối / Gỡ (cờ cho_phep). Sửa trên
	Desk hay API thẳng thì dừng: mỗi dòng gắn với một bút toán bù trừ, xoá
	dòng mà không huỷ bút toán là chi phí lệch sổ. THUẦN."""
	if cho_phep:
		return ""
	if sorted(khoa_dong(r) for r in (cu or [])) != sorted(khoa_dong(r) for r in (moi or [])):
		return ("Hoá đơn đến sau chỉ nối hoặc gỡ bằng nút trên hồ sơ (app), không sửa thẳng. "
			"Mỗi tờ nối có thể kèm một bút toán bù trừ, sửa tay là sổ lệch.")
	return ""


def loi_bo_thanh_toan(tt_cu, tt_moi, lien_ket, tt_da_tra="Da thanh toan"):
	"""Hồ sơ đang có bút toán bù trừ thì không rời trạng thái Đã thanh toán
	(bỏ đối chiếu, mở lại). Bù trừ dựa trên việc hồ sơ ĐÃ chi: bút toán chi
	bị huỷ mà bù trừ còn thì công nợ tờ về 0 mà không ai trả. THUẦN."""
	if tt_cu != tt_da_tra or tt_moi == tt_da_tra:
		return ""
	co = [r for r in (lien_ket or []) if (r.get("but_toan") or "").strip()]
	if not co:
		return ""
	return ("Hồ sơ đang có bút toán bù trừ hoá đơn đến sau (%s). Gỡ nối các tờ đó trước rồi mới bỏ "
		"đối chiếu hay mở lại hồ sơ." % ", ".join(r["hoa_don"] for r in co))


def _khoa_khoan(r):
	r = r or {}
	return (str(r.get("name") or ""), round(_tien(r.get("so_tien")), 2), str(r.get("tk_no") or "").strip(),
		str(r.get("hoa_don") or "").strip(), _so(r.get("cho_hoa_don")))


def loi_sua_khoan_khi_noi(cu, moi, co_noi, cho_phep=False):
	"""Hồ sơ đã có tờ nối mức hồ sơ thì khoản chi đứng yên. THUẦN.

	Codex #373 vòng 3 (05c3866): lưu Desk/API đổi số tiền hay tài khoản Nợ
	của khoản mà không đụng bảng tờ nối thì luật bảng tờ nối vẫn qua, trong
	khi mức phủ, nhãn hợp lệ và kế hoạch bù trừ của lần nối sau đều tính từ
	khoản. Thêm, xoá, đổi số tiền, tài khoản Nợ, hoá đơn gốc hay cờ chờ hoá
	đơn đều dừng; chỉ nút Nối/Gỡ (cờ) được đổi cờ chờ hoá đơn. Ô khác (tệp
	đính, ghi chú) vẫn sửa được."""
	if not co_noi or cho_phep:
		return ""
	if sorted(_khoa_khoan(r) for r in (cu or [])) != sorted(_khoa_khoan(r) for r in (moi or [])):
		return ("Hồ sơ đang có hoá đơn đến sau nối ở mức hồ sơ, nên không thêm, xoá hay sửa số tiền, tài khoản, "
			"hoá đơn gốc của khoản chi được. Gỡ các tờ nối trên hồ sơ trước rồi mới sửa khoản.")
	return ""

