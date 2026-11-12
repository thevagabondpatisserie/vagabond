# -*- coding: utf-8 -*-
"""Bánh sỉ trên web cho quán cà phê, khách sạn, nhà hàng (v630).

Anh Việt chốt 02/11/2026 (Phần 2 đề xuất "Thiết kế riêng và Bánh sỉ", hướng
sau góp ý Codex vòng 1):

  - Trang công khai /banh-si KHÔNG hiện giá. Quán đăng ký (tên, MST, số Zalo,
    loại hình, lượng mỗi tuần) vào phiếu "Vagabond Dang Ky Si", tin Zalo cho
    nhóm Bán hàng. Sales gọi lại.
  - Sales duyệt trên app: gắn vào khách có sẵn hoặc tạo khách mới ở nhóm
    "Khách sỉ B2B", bật "Đặt sỉ trên web", bật hay tắt "Trả cuối kỳ 15 ngày".
  - Giá RIÊNG từng khách, Sales khai một lần mỗi món. Món chưa có giá riêng
    thì khách đó không thấy. Máy không bao giờ nhận giá từ trình duyệt.
  - Khách đăng nhập bằng mã OTP qua Zalo như trang thành viên, cookie riêng
    `vgb_khach_si`. Phiên là Guest: mọi hàm dùng chung mà trang gọi KHÔNG được
    có cổng quyền nhân viên (bài học Codex #517 vòng 8).
  - Ngày giao sớm nhất = ngày đặt + 3 (giờ Việt Nam). Có "Đặt lại như đơn trước".

NƠI LƯU GIÁ RIÊNG (vì sao không để chung bảng giá bán mặc định)
==============================================================
Item Price có ô `customer`, lõi ERPNext lọc đúng theo khách. Nhưng ba chỗ cũ
của app đọc bảng giá bán mặc định mà KHÔNG lọc khách: chon_mon._gia_ban (giá
hiện trên web), pancake_sp._gia_niem_yet (giá đẩy sang Pancake), doi_soat
(ghi đè giá theo mã). Để giá riêng chung bảng đó là giá sỉ của một quán có
thể thành giá công khai trên web hay trên Pancake. Nên giá riêng nằm ở MỘT
bảng giá bán RIÊNG "Giá sỉ theo khách" (BANG_GIA), mỗi dòng mang `customer`.
Đọc qua MỘT hàm `gia_cua_khach`, dùng cho trang khách, lúc lập đơn và màn
Sales. Đổi giá sửa tại chỗ (Item Price bật track_changes nên có vết ai đổi,
lúc nào, từ bao nhiêu); bỏ món thì khoá hạn `valid_upto`, không xoá.

DÒNG TIỀN, TỪNG BƯỚC
====================
1. Khách đặt: Sales Order đã ghi sổ (bước "nhận đơn"), giá = giá riêng ĐÃ GỒM
   VAT đọc ở máy chủ, mẫu thuế "đã gồm trong giá" như mọi phiếu bán của app
   (hoa_don_thue_vnd.nap_mau_thue). Chưa có bút toán, chưa trừ kho.
2a. Khách "Trả cuối kỳ 15 ngày": không thu gì lúc đặt.
2b. Khách trả trước: QR mang mã đơn BSIyymmNNNN, số = cả đơn. Tiền về thì bộ
   máy chung ung_truoc_don.khop chiếm dòng sao kê (sổ đối soát chung, ô
   `vgb_gd_tkr`) và lập phiếu thu ứng trước NHÁP trỏ đúng phiếu đặt; kế toán
   đính giấy báo Có rồi ghi sổ.
3. Ngày giao (màn Đơn sỉ web): Phiếu giao hàng lập TỪ phiếu đặt (trừ kho, ghi
   giá vốn như đường xuất bán sỉ xuat_ban), rồi Hoá đơn lập TỪ phiếu giao
   (update_stock = 0; hach_toan_kho.du_dieu_kien_ban bỏ qua tờ có phiếu giao,
   nên không trừ kho hai lần).
     - Công nợ: phương thức "Công nợ", hạn = ngày hoá đơn + 15, hiện ở màn
       Công nợ phải thu và QR gộp phiếu đòi nợ như khách sỉ hiện nay.
     - Trả trước: phương thức "Trả trước", tắt tự cấn, CHỈ cấn phiếu thu đã
       ghi sổ của đúng phiếu đặt; cấn thiếu thì chặn.

KHÔNG ĐẾM HAI LẦN
=================
  - Một dòng sao kê chỉ được chiếm một lần cho toàn hệ (sổ đối soát chung).
  - Một đơn một hoá đơn: `custom_pancake_id = BSI-<mã>` vướng
    ban_hang.chan_trung_ma_pancake và khoá duy nhất dưới cơ sở dữ liệu.
  - Phiếu giao lập từ phiếu đặt: phiếu đặt đã giao đủ thì lõi không cho lập
    thêm; hoá đơn lập từ phiếu giao: phiếu giao đã lập hoá đơn thì lõi chặn.
  - Còn phải thu tính ở máy chủ, không nhận số từ màn hình.
"""

# ------------------------------------------------------------ phần thuần
#
# Không chạm Frappe để bộ kiểm tầng khung chạy được ở CI tay không.

import hashlib
import json
import re
from datetime import date, timedelta

NHOM_KHACH = "Khách sỉ B2B"
BANG_GIA = "Giá sỉ theo khách"
DT_DK = "Vagabond Dang Ky Si"
SO = "Sales Order"
SI = "Sales Invoice"
DN = "Delivery Note"
PE = "Payment Entry"
TIEN_TO_MA = "BSI"
RE_MA = re.compile(r"BSI[0-9]{8}")
SO_NGAY_GIAO = 3
KY_NO = 15
NGAY_DAT_TOI_DA = 60
SL_TOI_DA = 5000
DONG_TOI_DA = 60
GIA_TOI_DA = 20000000
GHI_CHU_TOI_DA = 500
PT_CONG_NO = "Công nợ"
PT_TRA_TRUOC = "Trả trước"
NGUON = "Khách sỉ"
COOKIE = "vgb_khach_si"
LECH = 1.0

LOAI_HINH = (("cafe", "Quán cà phê"), ("khach_san", "Khách sạn"), ("nha_hang", "Nhà hàng"), ("khac", "Khác"))
LUONG = (("duoi_50", "Dưới 50 cái"), ("50_200", "50 - 200 cái"), ("tren_200", "Trên 200 cái"))
TT_DK = ("Chờ duyệt", "Đã duyệt", "Từ chối")

# Duyệt khách, bật công nợ, khai giá: Sales (anh Việt 06/10: "Sales giữ quyền
# sửa bảng giá, khách hàng") và giám đốc.
QUYEN_SALES_SI = ("Sales User", "Sales Manager", "System Manager", "Giám đốc")
# Giao hàng, kiểm tiền về: như màn Đơn đặt trước, thêm kho (đường xuất bán sỉ
# xuat_ban.QUYEN_BAN cho kho lập phiếu giao).
QUYEN_GIAO_SI = ("Sales User", "Sales Manager", "System Manager", "VGB - Quản lý cửa hàng",
	"Accounts User", "Accounts Manager", "Giám đốc", "Stock User", "Stock Manager")
# Bếp xem danh sách theo ngày giao để lên kế hoạch, KHÔNG thấy tiền.
QUYEN_XEM_SI = QUYEN_GIAO_SI + ("Manufacturing User", "Manufacturing Manager")

# Trạng thái đơn. (mã, nhãn). Thứ tự là thứ tự chip.
TRANG_THAI = (
	("cho_tt", "Chờ chuyển khoản"),
	("cho_giao", "Chờ giao"),
	("da_giao", "Đã giao"),
	("da_huy", "Đã huỷ"),
)


def so_tien(x):
	try:
		return float(x or 0)
	except (TypeError, ValueError):
		return 0.0


def tron(x):
	return float(round(so_tien(x)))


def vnd(x):
	return "{:,.0f}".format(tron(x)).replace(",", ".") + " đ"


def ngay_iso(x):
	"""Chuỗi YYYY-MM-DD hợp lệ thành date, sai thì None. THUẦN."""
	if isinstance(x, date):
		return x
	s = str(x or "")
	try:
		return date.fromisoformat(s[:10]) if len(s) >= 10 else None
	except ValueError:
		return None


def chuan_sdt(s):
	"""Số di động Việt Nam về dạng 0xxxxxxxxx, sai thì rỗng.

	MỘT nguồn với `lib.sdt` (bench #531): bản cũ nhận mọi số 0[35789]xxxxxxxx,
	nên số đầu 095, 080... qua được form trong khi tra khách, gửi Zalo và
	tạo khách đọc theo lib.sdt; hai phép phải là một."""
	from vagabond.lib import sdt

	return sdt(s)


def logo_khach(u):
	"""Logo khách (Customer.image) được hiện trên màn app. THUẦN.

	AGENTS 2b.4: khách có logo thì hiện logo. Chỉ nhận ảnh CÔNG KHAI dạng
	/files/... : ảnh /private cần đăng nhập, đường ngoài hay có ký tự lạ thì
	bỏ, màn hiện ô biểu tượng nhóm 🏢."""
	u = str(u or "").strip()
	if not u.startswith("/files/") or ".." in u or re.search(r"[\s\\\"'<>]", u):
		return ""
	return u


def chuan_mst(s):
	"""Mã số thuế: rỗng, 10 số, 12 số (hộ kinh doanh theo CCCD) hoặc 10 số
	kèm mã chi nhánh 3 số. THUẦN. Sai dạng thì ValueError."""
	t = re.sub(r"[\s.]", "", str(s or ""))
	if not t:
		return ""
	if re.fullmatch(r"[0-9]{10}", t) or re.fullmatch(r"[0-9]{12}", t):
		return t
	m = re.fullmatch(r"([0-9]{10})-?([0-9]{3})", t)
	if m:
		return m.group(1) + "-" + m.group(2)
	raise ValueError("Mã số thuế gồm 10 số (hoặc 10 số kèm mã chi nhánh 3 số). Để trống nếu chưa có.")


def _lua_chon(bang, ma):
	return next((n for k, n in bang if k == ma), None)


def chuan_dang_ky(raw):
	"""Kiểm một phiếu đăng ký khách gửi. THUẦN. Trả bản sạch, lỗi thì ValueError."""
	if not isinstance(raw, dict):
		raise ValueError("Kiểm tra lại thông tin đăng ký.")
	ten = re.sub(r"\s+", " ", str(raw.get("ten_quan") or "")).strip()
	if len(ten) < 2 or len(ten) > 140:
		raise ValueError("Điền tên quán hoặc tên công ty.")
	sdt = chuan_sdt(raw.get("sdt"))
	if not sdt:
		raise ValueError("Điền số điện thoại di động có Zalo, dùng để đăng nhập sau này.")
	mst = chuan_mst(raw.get("mst"))
	loai = str(raw.get("loai_hinh") or "")
	if not _lua_chon(LOAI_HINH, loai):
		raise ValueError("Chọn loại hình: quán cà phê, khách sạn, nhà hàng hoặc khác.")
	luong = str(raw.get("luong") or "")
	if not _lua_chon(LUONG, luong):
		raise ValueError("Chọn lượng bánh dự kiến mỗi tuần.")
	ghi_chu = re.sub(r"\s+", " ", str(raw.get("ghi_chu") or "")).strip()
	if len(ghi_chu) > GHI_CHU_TOI_DA:
		raise ValueError("Ghi chú tối đa %d ký tự." % GHI_CHU_TOI_DA)
	return {"ten_quan": ten, "sdt": sdt, "mst": mst, "loai_hinh": _lua_chon(LOAI_HINH, loai),
		"luong_tuan": _lua_chon(LUONG, luong), "ghi_chu": ghi_chu}


def ngay_som_nhat(hom_nay):
	"""Ngày giao sớm nhất: ngày đặt + 3 (anh Việt chốt 02/11/2026). THUẦN."""
	return ngay_iso(hom_nay) + timedelta(days=SO_NGAY_GIAO)


def han_no(ngay_hoa_don):
	"""Hạn trả của hoá đơn công nợ: ngày hoá đơn + 15. THUẦN."""
	return ngay_iso(ngay_hoa_don) + timedelta(days=KY_NO)


def cach_tra(cuoi_ky):
	"""Khách bật "Trả cuối kỳ 15 ngày" thì Công nợ, không thì Trả trước. THUẦN."""
	return PT_CONG_NO if int(cuoi_ky or 0) else PT_TRA_TRUOC


def chuan_gia(x):
	"""Giá Sales gõ cho một món (ĐÃ GỒM VAT). Số nguyên dương có trần. THUẦN."""
	s = re.sub(r"[\s.,đ]", "", str(x if x is not None else ""))
	if not re.fullmatch(r"[0-9]{1,9}", s or "x"):
		raise ValueError("Giá là số tiền đồng, ví dụ 28000.")
	g = int(s)
	if g <= 0 or g > GIA_TOI_DA:
		raise ValueError("Giá phải lớn hơn 0 và không quá %s." % vnd(GIA_TOI_DA))
	return g


def chon_gia(rows, ngay):
	"""Từ các dòng Item Price riêng của MỘT khách, ra {mã món: dòng} đang áp
	ngày `ngay`. THUẦN. Nhiều dòng cùng hiệu lực thì lấy dòng có ngày bắt đầu
	muộn nhất, rồi dòng sửa sau cùng. Giá không dương thì bỏ (không bán 0 đồng)."""
	n = ngay_iso(ngay)
	ra = {}
	for r in rows or []:
		tu, den = ngay_iso(r.get("valid_from")), ngay_iso(r.get("valid_upto"))
		if (tu and tu > n) or (den and den < n) or so_tien(r.get("price_list_rate")) <= 0:
			continue
		ma = r.get("item_code")
		cu = ra.get(ma)
		khoa = (str(tu or ""), str(r.get("modified") or ""))
		if not cu or khoa > (str(ngay_iso(cu.get("valid_from")) or ""), str(cu.get("modified") or "")):
			ra[ma] = r
	return ra


def chuan_dong(dong, bang_gia):
	"""Các dòng khách gửi -> dòng sạch, GIÁ LẤY TỪ `bang_gia` của máy chủ. THUẦN.

	Món không có giá riêng của khách thì chặn (khách không thấy món đó, gửi
	thẳng mã lạ là đường vòng). Cùng món hai dòng thì cộng số lượng. Giá,
	thành tiền, tổng trình duyệt gửi đều bị bỏ qua.
	"""
	if not isinstance(dong, list) or not dong:
		raise ValueError("Chọn ít nhất một món với số lượng lớn hơn 0.")
	if len(dong) > DONG_TOI_DA:
		raise ValueError("Một đơn tối đa %d món." % DONG_TOI_DA)
	gop, thu_tu = {}, []
	for d in dong:
		if not isinstance(d, dict):
			raise ValueError("Kiểm tra lại các món trong đơn.")
		ma = str(d.get("ma") or "")
		try:
			sl = int(str(d.get("sl") if d.get("sl") is not None else ""))
		except ValueError:
			raise ValueError("Số lượng là số nguyên.")
		if sl == 0:
			continue
		if sl < 0 or sl > SL_TOI_DA:
			raise ValueError("Số lượng mỗi món từ 1 tới %d." % SL_TOI_DA)
		if ma not in (bang_gia or {}):
			raise ValueError("Có món chưa mở giá cho quý khách. Tải lại trang để xem danh sách mới.")
		if ma not in gop:
			thu_tu.append(ma)
			gop[ma] = 0
		gop[ma] += sl
	ra = []
	for ma in thu_tu:
		sl = gop[ma]
		if sl > SL_TOI_DA:
			raise ValueError("Số lượng mỗi món từ 1 tới %d." % SL_TOI_DA)
		g = tron(bang_gia[ma]["gia"])
		ra.append({"ma": ma, "ten": bang_gia[ma].get("ten") or ma, "sl": sl, "gia": g, "tien": g * sl})
	if not ra:
		raise ValueError("Chọn ít nhất một món với số lượng lớn hơn 0.")
	return ra


def chuan_don(raw, bang_gia, hom_nay):
	"""Kiểm một đơn sỉ khách gửi. THUẦN. Trả {ngay, dong, ghi_chu, tong}."""
	if not isinstance(raw, dict):
		raise ValueError("Kiểm tra lại đơn hàng.")
	ngay = ngay_iso(raw.get("ngay"))
	som = ngay_som_nhat(hom_nay)
	if not ngay:
		raise ValueError("Chọn ngày giao.")
	if ngay < som:
		raise ValueError("Ngày giao sớm nhất là %s (đặt trước %d ngày)." % (som.strftime("%d/%m/%Y"), SO_NGAY_GIAO))
	if ngay > som + timedelta(days=NGAY_DAT_TOI_DA):
		raise ValueError("Chỉ nhận đặt trong vòng %d ngày tới." % NGAY_DAT_TOI_DA)
	ghi_chu = re.sub(r"\s+", " ", str(raw.get("ghi_chu") or "")).strip()
	if len(ghi_chu) > GHI_CHU_TOI_DA:
		raise ValueError("Ghi chú tối đa %d ký tự." % GHI_CHU_TOI_DA)
	dong = chuan_dong(raw.get("dong"), bang_gia)
	return {"ngay": ngay.isoformat(), "dong": dong, "ghi_chu": ghi_chu, "tong": sum(d["tien"] for d in dong)}


def dat_lai(dong_cu, bang_gia):
	""""Đặt lại như đơn trước": số lượng đơn cũ, GIÁ HÔM NAY. THUẦN.

	Trả (các dòng {ma, sl} còn đặt được, các mã đã thôi bán cho khách). Không
	mang giá cũ sang: giá luôn đọc lại ở máy chủ lúc gửi.
	"""
	con, bo = [], []
	for d in dong_cu or []:
		ma, sl = d.get("ma"), int(so_tien(d.get("sl")))
		if sl <= 0:
			continue
		if ma in (bang_gia or {}):
			con.append({"ma": ma, "sl": sl})
		else:
			bo.append(ma)
	return con, bo


def goi_y_gia(lich_su, anh_xa, da_co):
	"""Gợi ý giá cho Sales: giá khách đã trả gần nhất cho từng mã bánh gốc. THUẦN.

	`lich_su`: dòng hoá đơn của khách {item_code, rate, ngay, hoa_don};
	`anh_xa`: {mã sỉ BAWS: mã gốc} (Anh Xa Ma Si, kể cả dòng chưa bật, vì chỉ
	để gợi ý); `da_co`: mã đã có giá riêng thì không gợi ý lại. Giá gợi ý là
	`rate` của dòng hoá đơn (đơn giá đã gồm VAT, cách app ghi mọi hoá đơn bán).
	"""
	ra = {}
	for r in lich_su or []:
		goc = (anh_xa or {}).get(r.get("item_code")) or r.get("item_code")
		if not goc or goc in (da_co or ()) or so_tien(r.get("rate")) <= 0:
			continue
		cu = ra.get(goc)
		if not cu or (str(r.get("ngay") or ""), str(r.get("hoa_don") or "")) > (cu["ngay"], cu["hoa_don"]):
			ra[goc] = {"ma": goc, "gia": tron(r.get("rate")), "ngay": str(r.get("ngay") or ""),
				"hoa_don": str(r.get("hoa_don") or ""), "tu_ma": r.get("item_code") if r.get("item_code") != goc else ""}
	return sorted(ra.values(), key=lambda x: (x["ngay"], x["ma"]), reverse=True)


def ma_tiep_theo(ma_cuoi, hom_nay):
	"""Mã đơn kế tiếp theo tháng: BSI + yymm + 4 số. THUẦN."""
	hn = ngay_iso(hom_nay)
	dau = "%s%02d%02d" % (TIEN_TO_MA, hn.year % 100, hn.month)
	so = 0
	if ma_cuoi and str(ma_cuoi).startswith(dau) and str(ma_cuoi)[len(dau):].isdigit():
		so = int(str(ma_cuoi)[len(dau):])
	return "%s%04d" % (dau, so + 1)


def bam(du_lieu):
	"""Dấu nội dung một lần gửi để nhận ra gửi lại cùng nội dung. THUẦN."""
	return hashlib.sha256(json.dumps(du_lieu, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def xet_trang_thai(tra_truoc, tong, ds_phieu, co_hoa_don, da_huy):
	"""Trạng thái đơn sỉ. THUẦN. Trả (mã, nhãn)."""
	from vagabond.ung_truoc_don import con_phai_thu

	nhan = dict(TRANG_THAI)
	if da_huy:
		return ("da_huy", nhan["da_huy"])
	if co_hoa_don:
		return ("da_giao", nhan["da_giao"])
	if tra_truoc and con_phai_thu(tong, ds_phieu) > 0:
		return ("cho_tt", nhan["cho_tt"])
	return ("cho_giao", nhan["cho_giao"])


def loi_giao(tra_truoc, con_lai, ds_phieu):
	"""Đơn này giao được chưa. THUẦN. Rỗng là giao được.

	Trả trước: phải đủ tiền VÀ mọi phiếu thu đã ghi sổ (hoá đơn chỉ cấn phiếu
	đã ghi sổ). Công nợ: giao được ngay, hoá đơn ghi nợ hạn 15 ngày.
	"""
	if not tra_truoc:
		return ""
	if so_tien(con_lai) > 0:
		return "Đơn trả trước còn phải thu %s. Chờ khách chuyển đủ rồi giao." % vnd(con_lai)
	nhap = [p.get("name") for p in ds_phieu or [] if int(p.get("docstatus") or 0) == 0]
	if nhap:
		return ("Phiếu thu %s (chuyển khoản) chờ kế toán đính giấy báo Có và ghi sổ. Nhờ kế toán ghi sổ rồi bấm lại."
			% ", ".join(nhap))
	return ""


def la_hoa_don_si_web(pt, ma_don_hd, ds_so, ma_cua_so):
	"""Hoá đơn ngày giao của ĐÚNG một đơn sỉ web. THUẦN.

	Nguồn "Khách sỉ" chỉ cho phương thức Chuyển khoản, Tiền mặt ở quầy
	(ban_hang.NGUON_META), nên phép so phương thức với nguồn chặn nhầm hoá đơn
	Công nợ, Trả trước của đơn sỉ web do MÁY lập. Chỉ miễn khi: phương thức là
	một trong hai, mã hoá đơn là BSI-<mã>, MỌI dòng trỏ phiếu đặt, và phiếu đặt
	đó mang đúng mã ấy (`ma_cua_so`: {phiếu đặt: vgb_si_ma} đọc từ cơ sở dữ liệu).
	"""
	if str(pt or "").strip() not in (PT_CONG_NO, PT_TRA_TRUOC):
		return False
	m = str(ma_don_hd or "")
	if not m.startswith(TIEN_TO_MA + "-") or not RE_MA.fullmatch(m[len(TIEN_TO_MA) + 1:]):
		return False
	ds = [str(x or "").strip() for x in ds_so or []]
	if not ds or not all(ds):
		return False
	return all((ma_cua_so or {}).get(x) == m[len(TIEN_TO_MA) + 1:] for x in ds)


def tom_tat_no(hd, phieu, han, hom_nay):
	"""Khối Công nợ trên trang khách. THUẦN.

	`hd`: tờ chưa gom {name, ngay, tien}; `phieu`: phiếu đòi nợ còn mở
	{ma_phieu, con_thieu, hoa_don}; `han`: {tờ: hạn}. Trả tổng còn phải trả,
	hạn gần nhất, số tờ quá hạn, danh sách tờ kèm hạn (gần nhất lên đầu).
	"""
	hn = ngay_iso(hom_nay)
	dong = [{"hoa_don": h["name"], "ngay": str(h.get("ngay") or ""), "tien": tron(h.get("tien")),
		"han": str((han or {}).get(h["name"]) or "")} for h in hd or []]
	for p in phieu or []:
		for x in p.get("hoa_don") or []:
			dong.append({"hoa_don": x, "ngay": "", "tien": 0.0, "han": str((han or {}).get(x) or ""), "phieu": p.get("ma_phieu")})
	tong = sum(d["tien"] for d in dong) + sum(tron(p.get("con_thieu")) for p in phieu or [])
	cac_han = sorted(d["han"] for d in dong if d["han"])
	qua = [d for d in dong if d["han"] and ngay_iso(d["han"]) and ngay_iso(d["han"]) < hn]
	dong.sort(key=lambda d: (d["han"] or "9999", d["hoa_don"]))
	return {"tong": tong, "han_gan": cac_han[0] if cac_han else "", "so_qua_han": len(qua), "dong": dong}


def tin_dang_ky(dk):
	"""Tin Zalo nhóm Bán hàng khi có quán đăng ký. Không mang số tiền. THUẦN."""
	dong = ["QUÁN ĐĂNG KÝ ĐẶT BÁNH SỈ", "Tên: %s" % dk.get("ten_quan", ""),
		"Loại hình: %s · Mỗi tuần: %s" % (dk.get("loai_hinh", ""), dk.get("luong_tuan", "")),
		"Số Zalo: %s" % dk.get("sdt", "")]
	if dk.get("mst"):
		dong.append("MST: %s" % dk["mst"])
	if dk.get("ghi_chu"):
		dong.append("Ghi chú: %s" % dk["ghi_chu"])
	dong.append("Sales gọi lại, duyệt ở app: Bán hàng > Khách sỉ web.")
	return "\n".join(dong)


def tin_don(don, loai):
	"""Tin Zalo đơn sỉ cho Sales và bếp. KHÔNG ghi số tiền (nhóm Bán hàng, Bếp
	không nhận tiền, luật 22/10/2026). THUẦN."""
	ngay = ngay_iso(don.get("ngay"))
	dau = {"moi_no": "ĐƠN SỈ WEB MỚI, TRẢ CUỐI KỲ", "moi_tt": "ĐƠN SỈ WEB MỚI, CHỜ CHUYỂN KHOẢN",
		"da_tt": "ĐƠN SỈ WEB ĐÃ NHẬN TIỀN", "bep": "ĐƠN SỈ WEB CẦN LÀM"}[loai]
	dong = [dau, "Mã đơn: %s" % don.get("ma", ""), "Khách: %s" % don.get("khach", "")]
	if ngay:
		dong.append("Ngày giao: %s" % ngay.strftime("%d/%m/%Y"))
	for d in (don.get("dong") or [])[:30]:
		dong.append("%s x %s" % (d.get("ten") or d.get("ma"), int(so_tien(d.get("sl")))))
	if len(don.get("dong") or []) > 30:
		dong.append("và %d món nữa" % (len(don["dong"]) - 30))
	if don.get("ghi_chu"):
		dong.append("Ghi chú: %s" % don["ghi_chu"])
	return "\n".join(dong)


# ------------------------------------------------------------- chạm Frappe

import frappe  # noqa: E402
from frappe.rate_limiter import rate_limit  # noqa: E402
from frappe.utils import flt, nowdate  # noqa: E402

TRUONG_MOI = {
	"Customer": [
		{"fieldname": "vgb_si_web", "label": "Đặt sỉ trên web", "fieldtype": "Check", "insert_after": "customer_group",
			"description": "Bật thì khách đăng nhập trang Bánh sỉ bằng số Zalo bên dưới và đặt theo giá riêng."},
		{"fieldname": "vgb_si_cuoi_ky", "label": "Trả cuối kỳ 15 ngày", "fieldtype": "Check", "insert_after": "vgb_si_web",
			"description": "Sales duyệt từng khách. Bật: hoá đơn ghi công nợ, hạn 15 ngày. Tắt: khách chuyển khoản trước khi giao."},
		{"fieldname": "vgb_si_sdt", "label": "Số Zalo đặt sỉ", "fieldtype": "Data", "insert_after": "vgb_si_cuoi_ky",
			"description": "Số di động khách dùng đăng nhập trang Bánh sỉ (nhận mã qua Zalo)."},
	],
	SO: [
		{"fieldname": "vgb_si_ma", "label": "Mã đơn sỉ web", "fieldtype": "Data", "insert_after": "vgb_tkr_lan",
			"read_only": 1, "no_copy": 1, "in_standard_filter": 1,
			"description": "Mã khách ghi khi chuyển khoản. Máy điền khi khách sỉ đặt trên web."},
		{"fieldname": "vgb_si_tt", "label": "Cách trả đơn sỉ", "fieldtype": "Data", "insert_after": "vgb_si_ma",
			"read_only": 1, "no_copy": 1, "description": "Công nợ (trả cuối kỳ 15 ngày) hoặc Trả trước."},
		{"fieldname": "vgb_si_du_lieu", "label": "Dữ liệu đơn sỉ web", "fieldtype": "Long Text", "insert_after": "vgb_si_tt",
			"read_only": 1, "hidden": 1, "no_copy": 1},
		# DUY NHẤT (Codex #531 f2): hàng rào cuối dưới khoá hàng khách và phép
		# tra lại mã lần gửi có khoá trong `dat`. Chuỗi rỗng thành NULL nên các
		# phiếu đặt không phải đơn sỉ web không đụng nhau.
		{"fieldname": "vgb_si_lan", "label": "Mã lần gửi đơn sỉ", "fieldtype": "Data", "insert_after": "vgb_si_du_lieu",
			"read_only": 1, "hidden": 1, "no_copy": 1, "unique": 1},
	],
}


def dam_bao():
	"""Bảng giá riêng và nhóm khách sỉ phải có (gọi sau migrate, không ghi đè)."""
	if not frappe.db.exists("Price List", BANG_GIA):
		frappe.get_doc({"doctype": "Price List", "price_list_name": BANG_GIA, "selling": 1, "buying": 0,
			"currency": "VND", "enabled": 1}).insert(ignore_permissions=True)
	if not frappe.db.exists("Customer Group", NHOM_KHACH):
		goc = frappe.db.get_value("Customer Group", {"is_group": 1, "parent_customer_group": ["in", ["", None]]}, "name") \
			or "All Customer Groups"
		frappe.get_doc({"doctype": "Customer Group", "customer_group_name": NHOM_KHACH, "parent_customer_group": goc,
			"is_group": 0}).insert(ignore_permissions=True)


def _cong_ty():
	return frappe.db.get_single_value("Global Defaults", "default_company")


def _hom_nay():
	return str(nowdate())


def _vai():
	return set(frappe.get_roles())


def _kiem_quyen_sales():
	if not set(QUYEN_SALES_SI) & _vai():
		frappe.throw("Duyệt khách sỉ, bật công nợ và khai giá riêng mở cho Sales và giám đốc.")


def _kiem_quyen_giao():
	if not set(QUYEN_GIAO_SI) & _vai():
		frappe.throw("Giao đơn sỉ web mở cho Sales, quản lý cửa hàng, kho, kế toán và giám đốc.")


def _kiem_quyen_xem():
	if not set(QUYEN_XEM_SI) & _vai():
		frappe.throw("Màn Đơn sỉ web mở cho Sales, cửa hàng, kho, bếp, kế toán và giám đốc.")


def _co_tien():
	"""Người xem được thấy số tiền (bếp chỉ thấy món và số lượng)."""
	return bool(set(QUYEN_GIAO_SI) & _vai())


def _ds_diem():
	from vagabond import diem_ban

	return diem_ban.ds(chi_bat=True)


def _quay():
	from vagabond.ung_truoc_don import quay_chuyen_khoan

	return quay_chuyen_khoan(_ds_diem())


def _nuot_loi_tin(e, ten):
	from vagabond.loi_csdl import chet_giao_dich

	if chet_giao_dich(e):
		raise e
	frappe.log_error(frappe.get_traceback(), "banh_si: tin Zalo %s" % ten)


def _tat_tin():
	return getattr(frappe.flags, "vagabond_kiem_that", False)


def _bao_dang_ky(dk, ten):
	"""Quán vừa đăng ký: nhóm Bán hàng gọi lại."""
	if _tat_tin():
		return
	try:
		from vagabond import kenh_zalo

		tieu_de, dong = kenh_zalo.tach_tin(tin_dang_ky(dk))
		kenh_zalo.bao_hoac_ghi_loi("viec", "don_web", tieu_de, dong, khoa="si_dk:%s" % ten, nguon=ten,
			ma_tin="bh_si_dang_ky")
	except Exception as e:
		_nuot_loi_tin(e, "bh_si_dang_ky")


def _bao_don_moi(don, so_name, tra_truoc):
	"""Đơn mới: Sales biết; đơn công nợ là đơn chắc chắn nên bếp biết ngay."""
	if _tat_tin():
		return
	try:
		from vagabond import kenh_zalo

		tieu_de, dong = kenh_zalo.tach_tin(tin_don(don, "moi_tt" if tra_truoc else "moi_no"))
		kenh_zalo.bao_hoac_ghi_loi("viec", "don_web", tieu_de, dong, khoa="si_moi:%s" % so_name, nguon=so_name,
			ma_tin="bh_si_don_moi")
	except Exception as e:
		_nuot_loi_tin(e, "bh_si_don_moi")
	if not tra_truoc:
		_bao_bep(don, so_name)


def _bao_da_tt(don, so_name):
	"""Đơn trả trước nhận tiền: Sales xác nhận, bếp lên kế hoạch."""
	if _tat_tin():
		return
	try:
		from vagabond import kenh_zalo

		tieu_de, dong = kenh_zalo.tach_tin(tin_don(don, "da_tt"))
		kenh_zalo.bao_hoac_ghi_loi("viec", "don_web", tieu_de, dong, khoa="si_tt:%s" % so_name, nguon=so_name,
			ma_tin="bh_si_da_tt")
	except Exception as e:
		_nuot_loi_tin(e, "bh_si_da_tt")
	_bao_bep(don, so_name)


def _bao_bep(don, so_name):
	"""Bếp nhận đơn CHẮC CHẮN làm: công nợ ngay lúc đặt, trả trước khi tiền về."""
	if _tat_tin():
		return
	try:
		from vagabond import kenh_zalo

		tieu_de, dong = kenh_zalo.tach_tin(tin_don(don, "bep"))
		kenh_zalo.bao_hoac_ghi_loi("thong_bao", "san_xuat", tieu_de, dong, khoa="si_bep:%s" % so_name, nguon=so_name,
			ma_tin="bep_si_don")
	except Exception as e:
		_nuot_loi_tin(e, "bep_si_don")


# ----------------------------------------------------------- giá riêng

def _dong_gia(khach):
	return frappe.get_all("Item Price", filters={"price_list": BANG_GIA, "customer": khach, "selling": 1},
		fields=["name", "item_code", "price_list_rate", "valid_from", "valid_upto", "modified", "uom"],
		limit_page_length=0)


def gia_cua_khach(khach, ngay=None):
	"""MỘT nguồn giá riêng của khách: {mã: {gia, ten, anh, dvt, ip}} của món
	đang bán ngày `ngay`. Trang khách, lúc lập đơn và màn Sales đều đọc đây.
	Không cổng quyền (trang khách là Guest); cửa gọi tự kiểm."""
	if not khach:
		return {}
	dang = chon_gia(_dong_gia(khach), ngay or _hom_nay())
	if not dang:
		return {}
	mon = {r.name: r for r in frappe.get_all("Item", filters={"name": ["in", list(dang)], "disabled": 0,
		"is_sales_item": 1, "has_variants": 0}, fields=["name", "item_name", "image", "stock_uom", "item_group"],
		limit_page_length=0)}
	return {ma: {"gia": tron(r.price_list_rate), "ten": mon[ma].item_name or ma, "anh": mon[ma].image or "",
		"dvt": mon[ma].stock_uom or "", "nhom": mon[ma].item_group or "", "ip": r.name, "tu": str(r.valid_from or "")}
		for ma, r in dang.items() if ma in mon}


# ------------------------------------------------------------- phiên khách

def _dn():
	"""dang_nhap kéo requests: nạp trong thân hàm (CI tay không)."""
	from vagabond import dang_nhap

	return dang_nhap


def _khong_cache():
	frappe.local.response_headers["Cache-Control"] = "private, no-store"


def _khach_cua_sdt(noi_dia):
	"""Khách sỉ đã mở web mang số Zalo này. Trả (dict, lý do). Nhiều khách cùng
	số thì không đoán, để Sales đối chiếu."""
	if not noi_dia:
		return None, "chua_mo_si"
	ds = frappe.get_all("Customer", filters={"vgb_si_web": 1, "disabled": 0, "vgb_si_sdt": noi_dia},
		fields=["name", "customer_name", "vgb_si_cuoi_ky", "tax_id"], limit_page_length=2)
	if len(ds) > 1:
		return None, "can_doi_chieu"
	if not ds:
		return None, "chua_mo_si"
	return ds[0], ""


def _khach_phien():
	"""Khách của phiên cookie `vgb_khach_si`. Trả (dict, lý do)."""
	so = _dn()._phien(frappe.request.cookies.get(COOKIE))
	if not so:
		return None, "chua_dang_nhap"
	return _khach_cua_sdt(_dn()._sdt_noi_dia(so))


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=600)
def san_sang():
	"""Trang hỏi có gửi mã OTP được không (chưa khai mẫu ZNS thì ẩn đăng nhập)."""
	from vagabond.lib import cfg

	return {"otp": 1 if cfg().get("zns_template_otp") else 0, "so_ngay": SO_NGAY_GIAO}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=12, seconds=600)
def gui_ma(sdt):
	"""Gửi mã OTP CHỈ cho số đã được Sales mở đặt sỉ: số lạ không tốn tin ZNS."""
	from vagabond.lib import cfg

	if not cfg().get("zns_template_otp"):
		return {"ok": 0, "ly_do": "chua_mo"}
	kh, ly = _khach_cua_sdt(chuan_sdt(sdt))
	if not kh:
		return {"ok": 0, "ly_do": ly}
	r = _dn().gui_ma(sdt)
	# v653: kênh đã gửi (zalo, whatsapp) để màn nói đúng kênh.
	return {"ok": r.get("ok", 0), "ly_do": r.get("ly_do", ""), "song_giay": r.get("song_giay", 0), "kenh": r.get("kenh", ""), "so": r.get("so", "")}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=600)
def xac_thuc(sdt, ma):
	kh, ly = _khach_cua_sdt(chuan_sdt(sdt))
	if not kh:
		return {"ok": 0, "ly_do": ly}
	r = _dn().xac_thuc(sdt, ma)
	if not r.get("ok"):
		return {"ok": 0, "ly_do": r.get("ly_do", "ma_khong_dung")}
	# Cookie riêng, như thanh_vien: không đặt domain, chỉ đúng tên miền khách.
	frappe.local.cookie_manager.set_cookie(COOKIE, r["token"], httponly=True, secure=True, samesite="Strict",
		max_age=_dn().PHIEN_SONG_NGAY * 86400)
	_khong_cache()
	return {"ok": 1}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=600)
def thoat():
	_dn().thoat(frappe.request.cookies.get(COOKIE))
	frappe.local.cookie_manager.delete_cookie(COOKIE)
	_khong_cache()
	return {"ok": 1}


def _don_cua_khach(khach, gioi_han=30):
	"""Đơn của một khách cho trang Tài khoản: MỌI đơn đang mở (chờ chuyển
	khoản, chờ giao) cộng `gioi_han` đơn mới nhất (lịch sử). Codex #531 vòng 8:
	câu cũ cắt 30 đơn mới nhất TRƯỚC khi chia đang mở và lịch sử, nên khách có
	một đơn chờ chuyển khoản rồi đặt thêm 30 đơn thì đơn đó biến mất khỏi "Đơn
	sắp giao" cùng nút mở lại QR."""
	from vagabond.ung_truoc_don import dk_don_mo, gop_ten_don

	dk = dk_don_mo("vgb_si_ma", TIEN_TO_MA)
	mo = frappe.db.sql("""select so.name, so.creation from `tabSales Order` so where so.customer = %s
		and ifnull(so.vgb_si_ma, '') != '' and """ + dk + " order by so.creation desc", (khach,), as_dict=True)
	gan = frappe.db.sql("""select so.name, so.creation from `tabSales Order` so where so.customer = %s
		and ifnull(so.vgb_si_ma, '') != '' and so.docstatus in (1, 2) order by so.creation desc limit %s""",
		(khach, int(gioi_han)), as_dict=True)
	ds = sorted(gop_ten_don(mo, gan), key=lambda r: str(r.get("creation") or ""), reverse=True)
	return [tom_tat(r["name"]) for r in ds]


def _hang_don(so_name, khoa=False):
	if khoa:
		# Đọc hiện tại các dòng (ô parent có chỉ mục): phiếu đặt của giao dịch
		# khác vừa commit thì ảnh chụp không có dòng nào.
		ds = frappe.db.sql("""select item_code, item_name, qty, rate, amount, idx from `tabSales Order Item`
			where parent = %s and parenttype = 'Sales Order' order by idx asc for update""", (so_name,), as_dict=True)
	else:
		ds = frappe.get_all("Sales Order Item", filters={"parent": so_name}, fields=["item_code", "item_name", "qty",
			"rate", "amount", "idx"], order_by="idx asc", limit_page_length=0)
	anh = {r.name: r.image or "" for r in frappe.get_all("Item", filters={"name": ["in", [d.item_code for d in ds] or ["__"]]},
		fields=["name", "image"], limit_page_length=0)}
	return [{"ma": d.item_code, "ten": d.item_name, "sl": flt(d.qty), "gia": tron(d.rate), "tien": tron(d.amount),
		"anh": anh.get(d.item_code, "")} for d in ds]


@frappe.whitelist(allow_guest=True)
@rate_limit(limit=60, seconds=600)
def toi():
	"""Mọi thứ trang khách sỉ cần sau khi đăng nhập: bảng giá riêng, đơn sắp
	giao, lịch sử, công nợ. Khách luôn lấy từ số đã xác thực, không nhận mã
	khách từ trình duyệt."""
	_khong_cache()
	kh, ly = _khach_phien()
	if not kh:
		return {"ok": 0, "ly_do": ly}
	hn = _hom_nay()
	bang = gia_cua_khach(kh.name, hn)
	don = _don_cua_khach(kh.name)
	cu = next((d for d in don if d["trang_thai"] != "da_huy"), None)
	lai, bo = dat_lai(cu["dong"], bang) if cu else ([], [])
	ra = {"ok": 1, "ten": kh.customer_name or kh.name, "cuoi_ky": 1 if kh.vgb_si_cuoi_ky else 0,
		"ky_no": KY_NO, "hom_nay": hn, "ngay_som": str(ngay_som_nhat(hn)), "so_ngay": SO_NGAY_GIAO,
		"mon": [{"ma": k, "ten": v["ten"], "gia": v["gia"], "anh": v["anh"], "dvt": v["dvt"], "nhom": v["nhom"]} for k, v in sorted(bang.items(), key=lambda x: (x[1]["nhom"], x[1]["ten"]))],
		"sap_giao": [d for d in don if d["trang_thai"] in ("cho_tt", "cho_giao")],
		"lich_su": [d for d in don if d["trang_thai"] in ("da_giao", "da_huy")][:20],
		"don_truoc": {"ma": cu["ma"], "ngay": cu["ngay"], "dong": lai, "bo": len(bo)} if cu else None,
		"no": None}
	if kh.vgb_si_cuoi_ky:
		from vagabond import cong_no

		n = cong_no.no_cua_khach(kh.name)
		ra["no"] = tom_tat_no(n["hd"], n["phieu"], n["han"], hn)
	return ra


def _ma_moi():
	dau = ma_tiep_theo("", _hom_nay())[:-4]
	cuoi = frappe.db.sql(
		"select vgb_si_ma from `tabSales Order` where vgb_si_ma like %s order by vgb_si_ma desc limit 1 for update",
		(dau + "%",))
	ma = ma_tiep_theo(cuoi[0][0] if cuoi else "", _hom_nay())
	for _ in range(50):
		if not frappe.db.exists(SO, {"vgb_si_ma": ma}):
			return ma
		ma = ma_tiep_theo(ma, _hom_nay())
	frappe.throw("Chưa sinh được mã đơn. Bấm gửi lại.")


def _da_gui(khach, lan, dau, khoa=False):
	"""Đơn cùng mã lần gửi đã có thì trả đơn đó. khoa=True: đọc HIỆN TẠI (for
	update) sau khi đã chờ khoá hàng khách; đọc thường lúc đó vẫn là ảnh chụp
	REPEATABLE READ từ lần đọc phiên khách, không thấy đơn lần bấm trước vừa
	lập (Codex #531 f2)."""
	r = frappe.db.get_value(SO, {"vgb_si_lan": lan}, ["name", "customer", "vgb_si_du_lieu"], as_dict=True,
		for_update=khoa)
	if not r:
		return None
	if r.customer != khach or json.loads(r.vgb_si_du_lieu or "{}").get("bam") != dau:
		frappe.throw("Đơn này đã được gửi. Tải lại trang để đặt đơn mới.")
	return _ket_qua(r.name, khoa=khoa)


def _kho_mac_dinh(ma, cty):
	if not frappe.db.get_value("Item", ma, "is_stock_item"):
		return None
	return (frappe.db.get_value("Item Default", {"parent": ma, "company": cty}, "default_warehouse")
		or frappe.db.get_single_value("Stock Settings", "default_warehouse"))


def _lap_don(kh, don, lan):
	"""Sales Order đã ghi sổ, giá = giá riêng máy chủ (gồm VAT)."""
	from vagabond.hoa_don_thue_vnd import nap_mau_thue
	from vagabond.thu_tien import nang_quyen_lap_phieu

	cty = _cong_ty()
	tt = cach_tra(kh.vgb_si_cuoi_ky)
	with nang_quyen_lap_phieu():
		so = frappe.new_doc(SO)
		so.company = cty
		so.customer = kh.name
		so.order_type = "Sales"
		so.transaction_date = _hom_nay()
		so.delivery_date = don["ngay"]
		so.currency = "VND"
		so.conversion_rate = 1
		so.selling_price_list = BANG_GIA
		so.ignore_pricing_rule = 1
		so.vgb_si_ma = _ma_moi()
		so.vgb_si_tt = tt
		so.vgb_si_lan = lan
		so.vgb_si_du_lieu = json.dumps(dict(don, ma=so.vgb_si_ma, khach=kh.customer_name or kh.name), ensure_ascii=False)
		for d in don["dong"]:
			dong = {"item_code": d["ma"], "qty": d["sl"], "rate": d["gia"], "price_list_rate": d["gia"],
				"delivery_date": don["ngay"]}
			kho = _kho_mac_dinh(d["ma"], cty)
			if kho:
				dong["warehouse"] = kho
			so.append("items", dong)
		# Giá riêng ĐÃ GỒM VAT: nạp mẫu thuế "đã gồm trong giá" như hoá đơn bán
		# của app, để tổng phiếu đặt đúng bằng tổng tiền khách thấy.
		nap_mau_thue(so)
		so.flags.ignore_permissions = True
		so.insert(ignore_permissions=True)
		tong = flt(so.rounded_total) or flt(so.grand_total)
		if abs(tong - don["tong"]) > LECH:
			frappe.log_error("Đơn sỉ %s tổng %s khác tổng giá riêng %s" % (so.name, tong, don["tong"]),
				"banh_si: tổng phiếu đặt lệch giá")
			frappe.throw("Chưa nhận đơn được lúc này. Quý khách gọi Sales để đặt.")
		so.submit()
	return so


def _qr(ma, so):
	from vagabond import qr_chuyen_khoan, tai_khoan

	tk = tai_khoan.tk_cho(NGUON, _quay())
	return {"ngan_hang": tk.get("bank") or "", "stk": tk.get("stk") or "", "ten_tk": tk.get("ten") or "",
		"so_tien": tron(so), "noi_dung": ma, "anh": qr_chuyen_khoan.anh_qr(tk, so, ma)}


def _ket_qua(so_name, khoa=False):
	"""khoa=True: dựng phản hồi bằng phép đọc hiện tại, dùng khi phiếu đặt vừa
	được tìm thấy sau khi chờ khoá (lần gửi lại). Đọc thường lúc đó là ảnh chụp
	cũ, không thấy phiếu đặt lần trước vừa commit (Codex #531 vòng 3)."""
	t = tom_tat(so_name, khoa=khoa)
	if t["tra_truoc"] and t["con_lai"] > 0 and t["trang_thai"] == "cho_tt":
		t["qr"] = _qr(t["ma"], t["con_lai"])
	return dict(t, ok=1)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=600)
def dat(du_lieu, ma_lan_gui):
	"""Khách sỉ gửi đơn. Gửi lại cùng mã lần gửi thì trả đơn cũ."""
	if not isinstance(ma_lan_gui, str) or not re.fullmatch(r"[a-f0-9-]{36}", ma_lan_gui):
		frappe.throw("Tải lại trang để bắt đầu đặt hàng.")
	kh, ly = _khach_phien()
	if not kh:
		frappe.throw("Phiên đăng nhập đã hết. Đăng nhập lại bằng số Zalo rồi gửi đơn.")
	try:
		raw = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
		if not isinstance(raw, dict) or len(json.dumps(raw, ensure_ascii=False)) > 20000:
			raise ValueError("Đơn quá dài hoặc không hợp lệ.")
	except (TypeError, ValueError) as e:
		frappe.throw(str(e))
	dau = bam(raw)
	lan = hashlib.sha256(("bsi:" + ma_lan_gui).encode()).hexdigest()[:40]
	# Khoá hàng khách: hai lần bấm gửi cùng lúc xếp hàng, lần sau thấy đơn lần trước.
	frappe.db.sql("select name from `tabCustomer` where name=%s for update", (kh.name,))
	cu = _da_gui(kh.name, lan, dau, khoa=True)
	if cu:
		return cu
	try:
		don = chuan_don(raw, gia_cua_khach(kh.name, _hom_nay()), _hom_nay())
	except (TypeError, ValueError) as e:
		frappe.throw(str(e))
	don["bam"] = dau
	so = _lap_don(kh, don, lan)
	_bao_don_moi(dict(don, ma=so.vgb_si_ma, khach=kh.customer_name or kh.name), so.name, so.vgb_si_tt == PT_TRA_TRUOC)
	frappe.db.commit()
	return _ket_qua(so.name)


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=60, seconds=600)
def trang_thai_don(ma):
	"""Trang khách hỏi đơn trả trước đã nhận tiền chưa. Chỉ đơn CỦA khách phiên
	này; hỏi xong máy thử khớp sao kê của đúng đơn đó."""
	kh, ly = _khach_phien()
	if not kh or not (isinstance(ma, str) and RE_MA.fullmatch(ma)):
		frappe.throw("Không tìm thấy đơn.")
	ten = frappe.db.get_value(SO, {"vgb_si_ma": ma, "customer": kh.name, "docstatus": 1}, "name")
	if not ten:
		frappe.throw("Không tìm thấy đơn.")
	try:
		khop_don(ten)
		frappe.db.commit()
	except Exception as e:
		frappe.db.rollback()
		from vagabond.loi_csdl import chet_giao_dich

		if chet_giao_dich(e):
			raise
		frappe.log_error(frappe.get_traceback(), "banh_si: khớp khi khách hỏi")
	t = tom_tat(ten)
	return {"trang_thai": t["trang_thai"], "nhan": t["nhan"], "con_lai": t["con_lai"]}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=10, seconds=600)
def qr_no():
	"""Khách công nợ bấm "Thanh toán qua QR": QR gộp phiếu đòi nợ (cong_no)."""
	kh, ly = _khach_phien()
	if not kh:
		return {"ok": 0, "ly_do": ly}
	if not kh.vgb_si_cuoi_ky:
		return {"ok": 0, "ly_do": "khong_cong_no"}
	from vagabond import cong_no

	n = cong_no.qr_no_cua_khach(kh.name)
	frappe.db.commit()
	return {"ok": 1, "phieu": n["phieu"], "no": tom_tat_no(n["hd"], n["phieu"], n["han"], _hom_nay())}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=30, seconds=600)
def qr_don(ma):
	"""Khách sỉ trả trước mở lại QR của MỘT đơn chưa chuyển tiền (Codex #531 f4).

	QR trước đây chỉ nằm trong bộ nhớ trang ngay sau lúc đặt: khách tải lại
	trang hoặc sang Tài khoản là mất, không chuyển tiền được. Chỉ đơn CỦA khách
	phiên này (khách lấy từ cookie, không nhận mã khách từ trình duyệt). Số
	tiền là phần còn phải thu máy chủ tính (`tom_tat`); đơn đã nhận đủ tiền, đơn
	công nợ, đơn huỷ không có QR (cùng luật `_ket_qua` lúc đặt)."""
	_khong_cache()
	kh, ly = _khach_phien()
	if not kh or not (isinstance(ma, str) and RE_MA.fullmatch(ma)):
		frappe.throw("Không tìm thấy đơn.")
	ten = frappe.db.get_value(SO, {"vgb_si_ma": ma, "customer": kh.name, "docstatus": 1}, "name")
	if not ten:
		frappe.throw("Không tìm thấy đơn.")
	return _ket_qua(ten)


# ---------------------------------------------------- đăng ký (khách vãng lai)

def _da_nhan_dk(ten, dau, khoa=False):
	cu = frappe.db.get_value(DT_DK, ten, ["name", "bam_noi_dung"], as_dict=True, for_update=khoa)
	if not cu:
		return None
	if cu.bam_noi_dung != dau:
		frappe.throw("Đăng ký trước đã được nhận. Tải lại trang để gửi thêm.")
	return {"ok": 1, "ma": cu.name[:8].upper()}


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=5, seconds=600)
def dang_ky(du_lieu, ma_lan_gui):
	"""Quán gửi đăng ký đặt bánh sỉ. Gửi lại cùng mã lần gửi thì trả kết quả cũ."""
	if not isinstance(ma_lan_gui, str) or not re.fullmatch(r"[a-f0-9-]{36}", ma_lan_gui):
		frappe.throw("Tải lại trang để bắt đầu đăng ký.")
	try:
		raw = json.loads(du_lieu) if isinstance(du_lieu, str) else du_lieu
		chuoi = json.dumps(raw, sort_keys=True, ensure_ascii=False)
		if not isinstance(raw, dict) or len(chuoi) > 3000:
			raise ValueError("Đăng ký quá dài hoặc không hợp lệ.")
		dk = chuan_dang_ky(raw)
	except (TypeError, ValueError) as e:
		frappe.throw(str(e))
	dau = hashlib.sha256(chuoi.encode()).hexdigest()
	ten = hashlib.sha256(("bsi_dk:" + ma_lan_gui).encode()).hexdigest()[:40]
	cu = _da_nhan_dk(ten, dau)
	if cu:
		return cu
	d = frappe.get_doc(dict(dk, doctype=DT_DK, name=ten, bam_noi_dung=dau, trang_thai="Chờ duyệt"))
	d.flags.dang_ky_web = True
	moc = "dang_ky_si_" + frappe.generate_hash(length=12)
	frappe.db.savepoint(moc)
	so_thong_bao = len(frappe.local.message_log or [])
	try:
		d.insert(ignore_permissions=True)
	except frappe.DuplicateEntryError:
		frappe.db.rollback(save_point=moc)
		cu = _da_nhan_dk(ten, dau, khoa=True)
		if not cu:
			raise
		del frappe.local.message_log[so_thong_bao:]
		return cu
	_bao_dang_ky(dk, d.name)
	return {"ok": 1, "ma": d.name[:8].upper()}


def kiem_phieu_dang_ky(doc):
	"""Hook validate của Vagabond Dang Ky Si: chỉ nhận từ trang web; Sales chỉ
	đổi trạng thái, khách gắn, ghi chú xử lý, không sửa chữ khách đã gửi."""
	if doc.is_new():
		if not doc.flags.dang_ky_web:
			frappe.throw("Đăng ký bánh sỉ chỉ nhận từ trang Bánh sỉ.")
		return
	cu = doc.get_doc_before_save()
	if cu:
		for ten in ("ten_quan", "mst", "sdt", "loai_hinh", "luong_tuan", "ghi_chu", "bam_noi_dung"):
			if str(cu.get(ten) or "") != str(doc.get(ten) or ""):
				frappe.throw("Giữ nguyên đăng ký khách đã gửi. Ghi thay đổi vào ghi chú xử lý.")
		if cu.trang_thai != "Chờ duyệt" and doc.trang_thai != cu.trang_thai:
			frappe.throw("Đăng ký đã %s, không đổi trạng thái lại được." % cu.trang_thai.lower())
	if doc.trang_thai not in TT_DK:
		frappe.throw("Chọn trạng thái đăng ký hợp lệ.")


# ------------------------------------------------------------ màn Sales (app)

@frappe.whitelist()
def ds_dang_ky(trang_thai=""):
	_kiem_quyen_sales()
	truong = ["name", "ten_quan", "mst", "sdt", "loai_hinh", "luong_tuan", "ghi_chu", "trang_thai", "khach", "xu_ly",
		"creation", "luc_duyet"]
	cho = TT_DK[0]
	# Codex #531 v8: đăng ký CHỜ DUYỆT là việc đang chờ, đọc đủ; chỉ phần đã xử
	# lý (đã duyệt, từ chối) mới cắt 300 dòng mới nhất.
	rows = []
	if trang_thai in ("", cho) or trang_thai not in TT_DK:
		rows += frappe.get_all(DT_DK, filters={"trang_thai": cho}, fields=truong, order_by="creation desc",
			limit_page_length=0)
	if trang_thai != cho:
		loc = {"trang_thai": trang_thai} if trang_thai in TT_DK else {"trang_thai": ["!=", cho]}
		rows += frappe.get_all(DT_DK, filters=loc, fields=truong, order_by="creation desc", limit_page_length=300)
	rows.sort(key=lambda r: str(r.get("creation") or ""), reverse=True)
	dem = {t: 0 for t in TT_DK}
	for r in frappe.db.sql("select trang_thai, count(*) from `tab%s` group by trang_thai" % DT_DK):
		dem[r[0]] = r[1]
	ten = {r.name: r.customer_name for r in frappe.get_all("Customer", filters={"name": ["in", [x.khach for x in rows
		if x.khach] or ["__"]]}, fields=["name", "customer_name"], limit_page_length=0)}
	for r in rows:
		r["ten_khach"] = ten.get(r.khach, "")
		r["luc"] = str(r.creation or "")[:16]
	return {"rows": rows, "dem": dem, "trang_thai": list(TT_DK)}


@frappe.whitelist()
def tim_khach(tu_khoa=""):
	"""Tìm khách có sẵn để gắn đăng ký (tên, mã, số điện thoại, MST)."""
	_kiem_quyen_sales()
	tu = str(tu_khoa or "").strip()
	loc = {"disabled": 0}
	if tu:
		from vagabond import tim_kiem

		loc = tim_kiem.them_loc(loc, "Customer", tu, ["name", "customer_name", "mobile_no", "tax_id"])
	ds = frappe.get_all("Customer", filters=loc, fields=["name", "customer_name", "customer_group", "mobile_no",
		"tax_id", "vgb_si_web", "vgb_si_cuoi_ky", "vgb_si_sdt", "image"], order_by="modified desc", limit_page_length=30)
	for r in ds:
		r["logo"] = logo_khach(r.pop("image", None))
	return ds


def _chan_trung_sdt(sdt, khach):
	khac = frappe.get_all("Customer", filters={"vgb_si_web": 1, "vgb_si_sdt": sdt, "name": ["!=", khach]},
		fields=["name", "customer_name"], limit_page_length=1)
	if khac:
		frappe.throw("Số %s đang là số đặt sỉ của %s. Một số Zalo chỉ đăng nhập cho một khách." % (
			sdt, khac[0].customer_name or khac[0].name))


@frappe.whitelist(methods=["POST"])
def duyet(name, khach="", ten_khach="", mst="", dat_web=1, cuoi_ky=0):
	"""Duyệt một đăng ký: gắn vào khách có sẵn (`khach`) hoặc tạo khách mới ở
	nhóm Khách sỉ B2B, bật đặt sỉ web, bật hay tắt trả cuối kỳ 15 ngày."""
	_kiem_quyen_sales()
	dk = frappe.get_doc(DT_DK, name)
	if dk.trang_thai != "Chờ duyệt":
		frappe.throw("Đăng ký này đã %s." % dk.trang_thai.lower())
	khach = str(khach or "").strip()
	if khach:
		if not frappe.db.exists("Customer", {"name": khach, "disabled": 0}):
			frappe.throw("Không tìm thấy khách %s." % khach)
	else:
		ten = re.sub(r"\s+", " ", str(ten_khach or dk.ten_quan or "")).strip()
		if len(ten) < 2:
			frappe.throw("Điền tên khách để tạo hồ sơ.")
		try:
			ma_so = chuan_mst(mst if mst else dk.mst)
		except ValueError as e:
			frappe.throw(str(e))
		dam_bao()
		c = frappe.get_doc({"doctype": "Customer", "customer_name": ten, "customer_group": NHOM_KHACH,
			"customer_type": "Company" if ma_so else "Individual", "tax_id": ma_so or None, "mobile_no": dk.sdt})
		c.flags.ignore_permissions = True
		c.insert(ignore_permissions=True)
		khach = c.name
	_chan_trung_sdt(dk.sdt, khach)
	frappe.db.set_value("Customer", khach, {"vgb_si_web": 1 if int(dat_web or 0) else 0,
		"vgb_si_cuoi_ky": 1 if int(cuoi_ky or 0) else 0, "vgb_si_sdt": dk.sdt})
	dk.trang_thai = "Đã duyệt"
	dk.khach = khach
	dk.nguoi_duyet = frappe.session.user
	dk.luc_duyet = frappe.utils.now_datetime()
	dk.flags.ignore_permissions = True
	dk.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "khach": khach}


@frappe.whitelist(methods=["POST"])
def tu_choi(name, ly_do=""):
	_kiem_quyen_sales()
	ly_do = re.sub(r"\s+", " ", str(ly_do or "")).strip()
	if len(ly_do) < 5:
		frappe.throw("Ghi lý do từ chối.")
	dk = frappe.get_doc(DT_DK, name)
	if dk.trang_thai != "Chờ duyệt":
		frappe.throw("Đăng ký này đã %s." % dk.trang_thai.lower())
	dk.trang_thai = "Từ chối"
	dk.xu_ly = ly_do[:500]
	dk.nguoi_duyet = frappe.session.user
	dk.luc_duyet = frappe.utils.now_datetime()
	dk.flags.ignore_permissions = True
	dk.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1}


@frappe.whitelist()
def ds_khach(tim=""):
	"""Khách đã mở đặt sỉ trên web, kèm số món có giá riêng."""
	_kiem_quyen_sales()
	loc = {"vgb_si_web": 1}
	tu = str(tim or "").strip()
	if tu:
		from vagabond import tim_kiem

		loc = tim_kiem.them_loc(loc, "Customer", tu, ["name", "customer_name", "vgb_si_sdt", "tax_id"])
	rows = frappe.get_all("Customer", filters=loc, fields=["name", "customer_name", "tax_id", "vgb_si_sdt",
		"vgb_si_cuoi_ky", "disabled", "image"], order_by="customer_name asc", limit_page_length=300)
	hn = _hom_nay()
	for r in rows:
		r["so_mon"] = len(chon_gia(_dong_gia(r.name), hn))
		r["logo"] = logo_khach(r.pop("image", None))
	return {"rows": rows}


@frappe.whitelist(methods=["POST"])
def luu_khach(khach, dat_web=None, cuoi_ky=None, sdt=None):
	"""Bật tắt đặt sỉ web, trả cuối kỳ, đổi số Zalo đăng nhập của một khách."""
	_kiem_quyen_sales()
	if not frappe.db.exists("Customer", khach):
		frappe.throw("Không tìm thấy khách %s." % khach)
	doi = {}
	if dat_web is not None:
		doi["vgb_si_web"] = 1 if int(dat_web or 0) else 0
	if cuoi_ky is not None:
		doi["vgb_si_cuoi_ky"] = 1 if int(cuoi_ky or 0) else 0
	if sdt is not None:
		s = chuan_sdt(sdt)
		if not s:
			frappe.throw("Số Zalo đặt sỉ là số di động Việt Nam, ví dụ 0909123456.")
		_chan_trung_sdt(s, khach)
		doi["vgb_si_sdt"] = s
	if doi:
		frappe.db.set_value("Customer", khach, doi)
		frappe.get_doc("Customer", khach).add_comment("Info", "Khách sỉ web: %s" % ", ".join(
			"%s = %s" % (k, v) for k, v in doi.items()))
		frappe.db.commit()
	return {"ok": 1}


def _anh_xa_si():
	"""{mã sỉ BAWS: mã gốc} từ Anh Xa Ma Si, CẢ dòng chưa bật (chỉ để gợi ý giá)."""
	if not frappe.db.table_exists("Anh Xa Ma Si"):
		return {}
	return {r.ma_si: r.ma_goc for r in frappe.get_all("Anh Xa Ma Si", filters={"ma_goc": ["is", "set"]},
		fields=["ma_si", "ma_goc"], limit_page_length=0)}


def _lich_su_gia(khach, so_ngay=180):
	return frappe.db.sql(
		"""select i.item_code, i.rate, s.posting_date as ngay, s.name as hoa_don
		from `tabSales Invoice Item` i join `tabSales Invoice` s on s.name = i.parent
		where s.docstatus = 1 and s.is_return = 0 and (s.customer = %s or s.vgb_khach_no = %s)
		and s.posting_date >= %s and i.rate > 0""",
		(khach, khach, frappe.utils.add_days(_hom_nay(), -so_ngay)), as_dict=True)


@frappe.whitelist()
def bang_gia(khach):
	"""Màn Giá riêng của một khách: giá đang áp và gợi ý giá đã trả gần nhất
	(hoá đơn 180 ngày, mã sỉ BAWS gộp về mã gốc qua Anh Xa Ma Si)."""
	_kiem_quyen_sales()
	kh = frappe.db.get_value("Customer", khach, ["name", "customer_name", "vgb_si_web", "vgb_si_cuoi_ky",
		"vgb_si_sdt", "tax_id", "image"], as_dict=True)
	if not kh:
		frappe.throw("Không tìm thấy khách %s." % khach)
	kh["logo"] = logo_khach(kh.pop("image", None))
	gia = gia_cua_khach(khach)
	goi_y = goi_y_gia(_lich_su_gia(khach), _anh_xa_si(), set(gia))
	ten = {r.name: r for r in frappe.get_all("Item", filters={"name": ["in", [g["ma"] for g in goi_y] or ["__"]],
		"disabled": 0, "is_sales_item": 1, "has_variants": 0}, fields=["name", "item_name", "image", "stock_uom"],
		limit_page_length=0)}
	goi_y = [dict(g, ten=ten[g["ma"]].item_name, anh=ten[g["ma"]].image or "", dvt=ten[g["ma"]].stock_uom or "")
		for g in goi_y if g["ma"] in ten][:60]
	return {"khach": kh, "gia": [dict(v, ma=k) for k, v in sorted(gia.items(), key=lambda x: x[1]["ten"])],
		"goi_y": goi_y}


@frappe.whitelist()
def tim_mon(tu_khoa=""):
	"""Tìm món bán (không mẫu biến thể) để thêm giá riêng."""
	_kiem_quyen_sales()
	tu = str(tu_khoa or "").strip()
	loc = {"disabled": 0, "is_sales_item": 1, "has_variants": 0}
	if tu:
		from vagabond import tim_kiem

		loc = tim_kiem.them_loc(loc, "Item", tu, ["name", "item_name"])
	return frappe.get_all("Item", filters=loc, fields=["name", "item_name", "image", "stock_uom", "item_group"],
		order_by="modified desc", limit_page_length=40)


@frappe.whitelist(methods=["POST"])
def luu_gia(khach, ma, gia):
	"""Khai hoặc đổi giá riêng (ĐÃ GỒM VAT) của một món cho một khách. Dòng
	đang áp thì sửa tại chỗ (Item Price có vết thay đổi), chưa có thì thêm dòng
	bắt đầu từ hôm nay. Không bao giờ chạm bảng giá bán mặc định."""
	_kiem_quyen_sales()
	try:
		g = chuan_gia(gia)
	except ValueError as e:
		frappe.throw(str(e))
	if not frappe.db.exists("Customer", khach):
		frappe.throw("Không tìm thấy khách %s." % khach)
	mon = frappe.db.get_value("Item", ma, ["name", "stock_uom", "disabled", "is_sales_item", "has_variants"], as_dict=True)
	if not mon or mon.disabled or not mon.is_sales_item or mon.has_variants:
		frappe.throw("Món %s không phải món đang bán." % ma)
	dam_bao()
	hn = _hom_nay()
	dang = chon_gia([r for r in _dong_gia(khach) if r.item_code == ma], hn).get(ma)
	if dang:
		ip = frappe.get_doc("Item Price", dang.name)
		ip.price_list_rate = g
	else:
		ip = frappe.get_doc({"doctype": "Item Price", "price_list": BANG_GIA, "item_code": ma, "customer": khach,
			"selling": 1, "currency": "VND", "uom": mon.stock_uom, "price_list_rate": g, "valid_from": hn,
			"note": "Giá riêng khách sỉ web, đã gồm VAT."})
	ip.flags.ignore_permissions = True
	ip.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "gia": gia_cua_khach(khach).get(ma)}


@frappe.whitelist(methods=["POST"])
def bo_gia(khach, ma):
	"""Thôi bán một món cho khách: khoá hạn dòng giá tới hôm qua, không xoá."""
	_kiem_quyen_sales()
	hn = _hom_nay()
	dang = chon_gia([r for r in _dong_gia(khach) if r.item_code == ma], hn).get(ma)
	if not dang:
		frappe.throw("Món %s chưa có giá riêng cho khách này." % ma)
	hom_qua = str(ngay_iso(hn) - timedelta(days=1))
	ip = frappe.get_doc("Item Price", dang.name)
	if str(ip.valid_from or "") > hom_qua:
		# Dòng khai hôm nay rồi bỏ hôm nay: lùi ngày bắt đầu để hạn hợp lệ.
		ip.valid_from = hom_qua
	ip.valid_upto = hom_qua
	ip.flags.ignore_permissions = True
	ip.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1}


# --------------------------------------------------- đơn sỉ: khớp tiền, giao

def _bao_tt_dau(so_name, ma):
	don = json.loads(frappe.db.get_value(SO, so_name, "vgb_si_du_lieu") or "{}")
	_bao_da_tt(don, so_name)


def khop_don(so_name):
	"""Tìm tiền về cho MỘT đơn sỉ trả trước (bộ máy chung ung_truoc_don.khop).
	Lần đầu phải chuyển đủ cả đơn. Trả số phiếu thu nháp đã lập."""
	from vagabond import ung_truoc_don as utd

	if frappe.db.get_value(SO, so_name, "vgb_si_tt") != PT_TRA_TRUOC:
		return 0
	return utd.khop(so_name, "vgb_si_ma", RE_MA, lambda so, tong: tong, _quay, _cong_ty,
		lambda ma, g: "Tiền chuyển khoản đơn sỉ web %s, dòng sao kê %s." % (ma, g.get("name")),
		_bao_tt_dau, "số tiền đơn", TIEN_TO_MA, "banh_si")


def quet():
	"""Nhịp 5 phút: khớp tiền về cho mọi đơn sỉ trả trước còn phải thu."""
	ds = frappe.get_all(SO, filters={"vgb_si_ma": ["is", "set"], "vgb_si_tt": PT_TRA_TRUOC, "docstatus": 1,
		"status": ["not in", ["Closed", "Cancelled", "Completed"]], "per_billed": ["<", 100]},
		pluck="name", limit_page_length=0)  # Codex #531 v8: mọi đơn còn chờ tiền, không cắt
	for ten in ds:
		try:
			khop_don(ten)
			frappe.db.commit()
		except Exception as e:
			frappe.db.rollback()
			from vagabond.loi_csdl import chet_giao_dich

			if chet_giao_dich(e):
				continue
			frappe.log_error(frappe.get_traceback(), "banh_si: quét %s" % ten)


def _hoa_don_cua(ma, khoa=False):
	return frappe.db.get_value(SI, {"custom_pancake_id": "%s-%s" % (TIEN_TO_MA, ma), "docstatus": ["<", 2]},
		["name", "docstatus", "due_date", "outstanding_amount"], as_dict=True, for_update=khoa)


def _phieu_giao_cua(so_name, khoa=False):
	"""Phiếu giao đã ghi sổ của phiếu đặt. khoa=True: đọc hiện tại sau khoá
	(against_sales_order có chỉ mục trong ERPNext nên chỉ khoá đúng các dòng đó)."""
	if khoa:
		ds = frappe.db.sql("""select p.name from `tabDelivery Note` p join `tabDelivery Note Item` i
			on i.parent = p.name where i.against_sales_order = %s and p.docstatus = 1 for update""", (so_name,))
		return tuple({r[0]: r for r in ds}.values())
	return frappe.db.sql("""select distinct p.name from `tabDelivery Note` p join `tabDelivery Note Item` i
		on i.parent = p.name where i.against_sales_order = %s and p.docstatus = 1""", (so_name,))


def tom_tat(so_name, khoa=False):
	"""Một đơn sỉ cho trang khách và màn app. Mọi con số tính ở đây.

	khoa=True: mọi phép đọc (phiếu đặt, phiếu thu, hoá đơn, dòng hàng) là đọc
	hiện tại, dùng khi dựng phản hồi cho lần gửi lại sau khoá (Codex #531 vòng 3)."""
	from vagabond.ung_truoc_don import con_phai_thu, ds_phieu

	so = frappe.db.get_value(SO, so_name, ["name", "docstatus", "customer", "customer_name", "delivery_date",
		"transaction_date", "grand_total", "rounded_total", "net_total", "total_taxes_and_charges", "vgb_si_ma",
		"vgb_si_tt", "vgb_si_du_lieu", "creation"], as_dict=True, for_update=khoa)
	tong = flt(so.rounded_total) or flt(so.grand_total)
	tra_truoc = so.vgb_si_tt == PT_TRA_TRUOC
	cac_phieu = ds_phieu(so_name, khoa) if tra_truoc else []
	hd = _hoa_don_cua(so.vgb_si_ma, khoa)
	ma, nhan = xet_trang_thai(tra_truoc, tong, cac_phieu, bool(hd and int(hd.docstatus) == 1), int(so.docstatus) == 2)
	don = json.loads(so.vgb_si_du_lieu or "{}")
	dong = _hang_don(so_name, khoa)
	return {
		"name": so.name, "ma": so.vgb_si_ma, "trang_thai": ma, "nhan": nhan, "khach": so.customer_name or so.customer,
		"ma_khach": so.customer, "ngay": str(so.delivery_date or ""), "dat_luc": str(so.creation or "")[:16],
		"tra_truoc": 1 if tra_truoc else 0, "cach_tra": so.vgb_si_tt or "",
		"tong": tron(tong), "chua_vat": tron(so.net_total), "vat": tron(so.total_taxes_and_charges),
		"con_lai": con_phai_thu(tong, cac_phieu) if tra_truoc else 0.0,
		"so_cai": int(sum(d["sl"] for d in dong)), "dong": dong,
		"ghi_chu": don.get("ghi_chu", ""), "hoa_don": hd.name if hd and int(hd.docstatus) == 1 else "",
		"han_no": str(hd.due_date or "") if hd and not tra_truoc else "",
		"phieu": [{"name": p["name"], "so_tien": tron(p["so_tien"]), "docstatus": int(p["docstatus"]),
			"ngay": str(p.get("posting_date") or ""), "gd": p.get("vgb_gd_tkr") or ""} for p in cac_phieu],
	}


def _an_tien(t):
	"""Bếp xem đơn: bỏ mọi số tiền."""
	for k in ("tong", "chua_vat", "vat", "con_lai"):
		t[k] = None
	t["phieu"] = []
	t["dong"] = [dict(d, gia=None, tien=None) for d in t["dong"]]
	return t


def _logo_cac_khach(ds_khach):
	"""{mã khách: logo} đọc MỘT lượt cho cả danh sách, không đọc từng khách."""
	ten = sorted({str(x) for x in ds_khach or [] if x})
	if not ten:
		return {}
	return {r.name: logo_khach(r.image) for r in frappe.get_all("Customer", filters={"name": ["in", ten]},
		fields=["name", "image"], limit_page_length=0)}


@frappe.whitelist()
def ds_don(trang_thai_loc="", tim=""):
	"""Đơn sỉ web theo ngày giao (30 ngày qua tới mọi ngày tới)."""
	_kiem_quyen_xem()
	tu = str(frappe.utils.add_days(_hom_nay(), -30))
	from vagabond.ung_truoc_don import ten_don_man

	ten = ten_don_man("vgb_si_ma", TIEN_TO_MA, tu)
	co_tien = _co_tien()
	rows = [tom_tat(t) if co_tien else _an_tien(tom_tat(t)) for t in ten]
	logo = _logo_cac_khach([r.get("ma_khach") for r in rows])
	for r in rows:
		r["logo"] = logo.get(r.get("ma_khach"), "")
	dem = {k: 0 for k, _ in TRANG_THAI}
	for r in rows:
		dem[r["trang_thai"]] = dem.get(r["trang_thai"], 0) + 1
	from vagabond import xuat_kho

	return {"rows": rows, "dem": dem, "hom_nay": _hom_nay(), "trang_thai": [{"k": k, "ten": t} for k, t in TRANG_THAI],
		"co_tien": 1 if co_tien else 0, "giao_duoc": 1 if co_tien else 0,
		"kho": [{"ma": k.name, "ten": k.warehouse_name or k.name} for k in xuat_kho._kho_that(_cong_ty())] if co_tien else [],
		"la_ke_toan": 1 if _la_ke_toan() else 0}


def _la_ke_toan():
	from vagabond.thu_tien import la_ke_toan

	return la_ke_toan()


@frappe.whitelist()
def xem_don(name):
	_kiem_quyen_xem()
	t = tom_tat(name)
	t["logo"] = _logo_cac_khach([t.get("ma_khach")]).get(t.get("ma_khach"), "")
	if not _co_tien():
		return _an_tien(t)
	if t["tra_truoc"] and t["con_lai"] > 0 and t["trang_thai"] == "cho_tt":
		t["qr"] = _qr(t["ma"], t["con_lai"])
	from vagabond import xuat_kho

	t["kho"] = [{"ma": k.name, "ten": k.warehouse_name or k.name} for k in xuat_kho._kho_that(_cong_ty())]
	t["la_ke_toan"] = 1 if _la_ke_toan() else 0
	t["loi_giao"] = loi_giao(t["tra_truoc"], t["con_lai"], t["phieu"]) if t["trang_thai"] in ("cho_tt", "cho_giao") else ""
	return t


def _khoa_don(name):
	r = frappe.db.sql("select name from `tabSales Order` where name=%s and ifnull(vgb_si_ma,'')!='' for update", (name,))
	if not r:
		frappe.throw("Không có đơn sỉ web %s." % name)


@frappe.whitelist(methods=["POST"])
def kiem_tien_ve(name):
	_kiem_quyen_giao()
	_khoa_don(name)
	lap = khop_don(name)
	frappe.db.commit()
	return {"ok": 1, "lap": lap, "don": tom_tat(name)}


@frappe.whitelist(methods=["POST"])
def ghi_so_phieu(name, phieu, anh=None):
	"""Kế toán đính giấy báo Có rồi ghi sổ phiếu thu chuyển khoản nháp của đơn."""
	_kiem_quyen_giao()
	if not _la_ke_toan():
		frappe.throw("Chỉ kế toán ghi sổ phiếu thu chuyển khoản, sau khi đính giấy báo Có.")
	_khoa_don(name)
	from vagabond.ung_truoc_don import ghi_so_nhap

	ghi_so_nhap(name, phieu, anh)
	frappe.db.commit()
	return {"ok": 1, "don": tom_tat(name)}


def _nguoi_mua(khach):
	"""Bốn ô người mua của hoá đơn: theo MST của khách sỉ; chưa có MST thì
	"Bán cho người tiêu dùng" như hoá đơn ngày giao của đơn đặt trước."""
	from vagabond.ban_hang import XHD_MAC_DINH

	c = frappe.db.get_value("Customer", khach, ["customer_name", "tax_id", "customer_primary_address",
		"customer_primary_contact"], as_dict=True) or {}
	mst = str(c.get("tax_id") or "").strip()
	if not mst:
		return {"vgb_xhd_ten": XHD_MAC_DINH, "vgb_xhd_mst": "", "vgb_xhd_dia_chi": "", "vgb_xhd_email": ""}
	dia_chi, email = "", ""
	if c.get("customer_primary_address"):
		a = frappe.db.get_value("Address", c["customer_primary_address"], ["address_line1", "address_line2", "city",
			"state"], as_dict=True) or {}
		dia_chi = ", ".join(x for x in [a.get("address_line1"), a.get("address_line2"), a.get("city"), a.get("state")] if x)
	if c.get("customer_primary_contact"):
		email = frappe.db.get_value("Contact", c["customer_primary_contact"], "email_id") or ""
	return {"vgb_xhd_ten": c.get("customer_name") or khach, "vgb_xhd_mst": mst, "vgb_xhd_dia_chi": dia_chi,
		"vgb_xhd_email": email}


@frappe.whitelist(methods=["POST"])
def giao_hang(name, kho, nguoi_nhan=""):
	"""Giao đơn sỉ và xuất hoá đơn. Phiếu giao hàng lập TỪ phiếu đặt (trừ kho,
	giá vốn), hoá đơn lập TỪ phiếu giao (không trừ kho lần hai). Công nợ: hạn
	+15 ngày. Trả trước: cấn ĐÚNG các phiếu thu đã ghi sổ của đơn."""
	_kiem_quyen_giao()
	from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note
	from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice
	from vagabond import xuat_ban, xuat_kho
	from vagabond.thu_tien import _giu_chu, nang_quyen_lap_phieu
	from vagabond.ung_truoc_don import cap_ung_truoc

	# Codex #531 vòng 6: sau khoá, quyết định bằng đọc hiện tại.
	_khoa_don(name)
	t = tom_tat(name, khoa=True)
	if t["trang_thai"] == "da_giao":
		frappe.throw("Đơn %s đã giao, hoá đơn %s." % (t["ma"], t["hoa_don"]))
	if t["trang_thai"] == "da_huy":
		frappe.throw("Đơn %s đã huỷ." % t["ma"])
	loi = loi_giao(t["tra_truoc"], t["con_lai"], t["phieu"])
	if loi:
		frappe.throw(loi)
	if _phieu_giao_cua(name, khoa=True):
		frappe.throw("Đơn %s đã có phiếu giao hàng nhưng chưa có hoá đơn. Nhờ kế toán lập hoá đơn từ phiếu giao đó."
			% t["ma"])
	cty = _cong_ty()
	if not any(k.name == kho for k in xuat_kho._kho_that(cty)):
		frappe.throw("Chọn kho xuất hàng.")
	ton = [{"ma": d["ma"], "sl": d["sl"]} for d in t["dong"] if frappe.db.get_value("Item", d["ma"], "is_stock_item")]
	if ton:
		xuat_kho._chan_qua_ton(kho, ton)
	so = frappe.get_doc(SO, name)
	hn = _hom_nay()
	nguoi_nhan = re.sub(r"\s+", " ", str(nguoi_nhan or "")).strip()[:140]
	moc = "bsi_giao_" + frappe.generate_hash(length=8)
	frappe.db.savepoint(moc)
	try:
		with nang_quyen_lap_phieu() as goc:
			dn = make_delivery_note(name)
			dn.posting_date = hn
			dn.set_warehouse = kho
			for it in dn.items:
				it.warehouse = kho
			dn.vgb_nguoi_nhan = nguoi_nhan
			dn.set(xuat_ban.O_DIEN_GIAI, xuat_ban.dien_giai(t["khach"], nguoi_nhan, "Đơn sỉ web %s" % t["ma"]))
			dn.flags.ignore_permissions = True
			dn.insert(ignore_permissions=True)
			dn.submit()
			_giu_chu(dn, goc)
			si = make_sales_invoice(dn.name)
			si.posting_date = hn
			si.set_posting_time = 1
			si.update_stock = 0
			si.vgb_quay = _quay()
			si.custom_nguon = NGUON
			si.vgb_ma_tham_chieu = t["ma"]
			si.custom_pancake_id = "%s-%s" % (TIEN_TO_MA, t["ma"])
			si.custom_pancake_display_id = t["ma"]
			for k, v in _nguoi_mua(so.customer).items():
				si.set(k, v)
			si.remarks = ("Đơn sỉ web %s, phiếu đặt %s, phiếu giao %s." % (t["ma"], so.name, dn.name)
				+ ((" Ghi chú: " + t["ghi_chu"]) if t["ghi_chu"] else ""))[:1000]
			# Hạn công nợ đặt thẳng ở ô due_date (site chưa có Payment Terms
			# Template); bỏ mẫu điều khoản của khách nếu có, không thì lõi
			# validate_due_date_with_template chặn hạn dài hơn mẫu.
			si.payment_terms_template = None
			si.set("payment_schedule", [])
			si.allocate_advances_automatically = 0
			si.set("advances", [])
			if t["tra_truoc"]:
				si.vgb_pt_thanh_toan = PT_TRA_TRUOC
				si.due_date = hn
				cap_ung_truoc(si, [p["name"] for p in t["phieu"] if p["docstatus"] == 1])
			else:
				si.vgb_pt_thanh_toan = PT_CONG_NO
				si.due_date = str(han_no(hn))
			si.flags.ignore_permissions = True
			si.insert(ignore_permissions=True)
			si.submit()
			_giu_chu(si, goc)
	except Exception as e:
		frappe.db.rollback(save_point=moc)
		frappe.log_error(frappe.get_traceback(), "banh_si: giao hàng %s" % name)
		frappe.throw("Chưa giao được đơn %s: %s. Chưa có phiếu giao hay hoá đơn nào được lập, bấm lại sau khi xử lý."
			% (t["ma"], frappe.utils.strip_html(str(e))[:300]))
	frappe.db.commit()
	return {"ok": 1, "phieu_giao": dn.name, "hoa_don": si.name, "don": tom_tat(name)}


@frappe.whitelist(methods=["POST"])
def huy_don(name, ly_do=""):
	"""Huỷ đơn khi CHƯA giao và CHƯA nhận đồng nào (kể cả phiếu nháp đã chiếm
	sao kê). Đơn có tiền đi đường hoàn tiền, không huỷ ở đây."""
	_kiem_quyen_giao()
	from vagabond.thu_tien import nang_quyen_lap_phieu

	ly_do = re.sub(r"\s+", " ", str(ly_do or "")).strip()
	if len(ly_do) < 5:
		frappe.throw("Ghi lý do huỷ.")
	# Codex #531 vòng 6: sau khoá, quyết định bằng đọc hiện tại.
	_khoa_don(name)
	t = tom_tat(name, khoa=True)
	if t["trang_thai"] in ("da_giao", "da_huy"):
		frappe.throw("Đơn %s đã %s." % (t["ma"], t["nhan"].lower()))
	if t["phieu"]:
		frappe.throw("Đơn %s đã có tiền chuyển về. Huỷ đơn có tiền phải lập phiếu hoàn tiền ở màn Hoàn tiền." % t["ma"])
	if _phieu_giao_cua(name, khoa=True):
		frappe.throw("Đơn %s đã có phiếu giao hàng, không huỷ ở đây." % t["ma"])
	so = frappe.get_doc(SO, name)
	with nang_quyen_lap_phieu():
		so.add_comment("Comment", "Huỷ đơn sỉ web: %s" % ly_do)
		so.flags.ignore_permissions = True
		so.cancel()
	frappe.db.commit()
	return {"ok": 1, "don": tom_tat(name)}


def mien_so_nguon(doc):
	"""Gọi từ ban_hang.kiem_truoc_khi_luu: hoá đơn này có phải hoá đơn ngày
	giao của đúng một đơn sỉ web (máy lập) không. Đọc mã đơn từ phiếu đặt."""
	pt = (doc.get("vgb_pt_thanh_toan") or "").strip()
	ma = str(doc.get("custom_pancake_id") or "")
	if pt not in (PT_CONG_NO, PT_TRA_TRUOC) or not ma.startswith(TIEN_TO_MA + "-"):
		return False
	ds = [d.get("sales_order") for d in (doc.get("items") or [])]
	co = [x for x in set(ds) if x]
	ma_cua_so = {r.name: r.vgb_si_ma for r in frappe.get_all(SO, filters={"name": ["in", co or ["__"]]},
		fields=["name", "vgb_si_ma"], limit_page_length=0)} if co else {}
	return la_hoa_don_si_web(pt, ma, ds, ma_cua_so)
