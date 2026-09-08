"""Kiem banh ngay: thay bang Lark ghi tay bang so dem tu Pancake.

Nguyen tac cot loi (chot voi anh Viet 01/08/2026):
- KHONG co cot sua tay "phat sinh". Chot khach nao la tao don Pancake ngay
  cho khach do - don chinh la "giu cho". May dem, khong ai phai nho.
- "Da dat"    = don giao hom nay, tao TRUOC hom nay.
- "Phat sinh" = don giao hom nay, tao TRONG hom nay.
- "Cho chot"   = don giao hom nay con trang thai Moi (0) - khach dang nhan
  tin tu van, sales tao don giu cho mem, TRU AO vao co the ban (y Loan Anh
  01/08). Khach huy thi huy don, so tu tra lai; chot xong thi don doi trang
  thai, tu nhay sang Da dat / Phat sinh - tru that.
- "Kenh khac" = banh ban qua Grab, Shopee, Be, GreenSM, khach si, quay -
  nhung kenh khong di qua Pancake nen khong co don Pancake de dem. Dem
  thang tu hoa don ban ra trong ngay (08/08/2026, y Loan Anh: truoc day
  phai tao mot don Pancake gia de tru so, thanh ra mot khach hai bill).
- Co the ban  = ton dau + bep san xuat - da dat - phat sinh - cho chot
                - kenh khac.

Ky thuat da do that:
- Loc don theo ngay giao: updateStatus=estimate_delivery_date kem
  startDateTime/endDateTime la UNIX GIAY (truyen ISO thi Pancake tra 0 don
  ma khong bao loi - nga o day mot lan roi).
- Trang thai loai khoi phep dem: 6 canceled, 7 removed.
"""

import json
import re
from datetime import datetime, timedelta

import frappe
from frappe.utils import add_days, getdate, now_datetime

from vagabond import pancake_nhip, tat_ban_web
from vagabond.lib import PANCAKE, TIMEOUT, cache_get, cache_set, cfg, giau_khoa, key


def _mang():
	"""Nap requests luc DUNG, khong nap luc import tep.

	Ly do: bo kiem thu tang khung chay tren may CI tay khong, khong co
	requests. Cac phep THUAN trong tep nay (TIEN_TO_MA, TIEN_TO_THEM_TAY,
	_dang_ma_dung) phai kiem thu duoc ma khong keo theo thu vien mang.
	Ngay 23/08/2026 CI do 2 ca vi dung dong "import requests" o dau tep nay.
	Cung mot le do voi "import erpnext nam TRONG ham" o duong tra truoc.
	"""
	import requests

	return requests

BO_QUA_TT = {6, 7}  # da huy, da xoa
MAX_TRANG = 10

# Theo doi banh o (BAWC) va banh si (BAWS) - anh Viet mo them BAWS 02/08.
# Phu kien, phi giao, hop nen... khong thuoc bang kiem banh.
#
# BANG NAY CHI QUYET DINH "MAY TU DUA VAO BANG".
# Doi no la doi thu may tu nhat ve tu don Pancake, va bang kiem banh se ngap
# nhung dong khong ai muon dem. Muon cho bep THEM TAY mot ma thi mo
# TIEN_TO_THEM_TAY ben duoi, dung dong vao day.
TIEN_TO_MA = ("BAWC", "BAWS")

# Ma bep duoc TIM va THEM TAY vao bang kiem banh, va bang se GIU lai qua moi
# lan dong bo.
#
# Anh Viet 23/08/2026: *"sua lai logic filter de Bep co the tim va them cac
# mon banh le, banh man (nhu Patechaud) va cac BTP can kiem dem trong ngay"*.
#
#   BAWC  banh o sinh nhat        BAEN  banh lanh (banh le)
#   BAWS  banh si                 BACF  banh kho (banh le)
#   BANU  banh nuong - Patechaud nam o day, day la "banh man" anh Viet noi
#   BASS  hop banh theo mua       BTPB  ban thanh pham banh
#                                 BTPN  ban thanh pham nuoc
#
# CO Y BO RA: BAPK phu kien, BATP topping, BPKG bao bi, DVBH/DVTI dich vu,
# NU** do uong, NVLT nguyen lieu tho, CCDC cong cu, VVPP van phong pham,
# KMCB combo khuyen mai, SLOP khoa hoc. Nhung thu do khong ai kiem dem o bang
# banh, de vao chi lam danh sach tim kiem dai them ma khong dung duoc.
TIEN_TO_THEM_TAY = TIEN_TO_MA + ("BANU", "BAEN", "BACF", "BASS", "BTPB", "BTPN")

# Man hinh tu goi dong bo lien tuc; chan doi lai Pancake day hon muc nay.
#
# NANG TU 12 LEN 45 GIAY (26/08/2026). Ly do: moi man hinh dang mo tu goi
# dong_bo 30 giay mot lan, va MOI lan dong bo la hai luot keo don, moi luot
# den muoi trang. Ba may sales mo cung luc la Pancake nhan hon hai chuc luot
# hoi mot phut, ca ngay, chua ke man mua vu va man van don cung goi. Pancake
# tra ve 403 la phai. Bon muoi lam giay van du tuoi cho mot bang kiem banh.
GIAN_CACH_DONG_BO = 45  # giay

# Pancake tu choi thi NGHI HAN, khong thu lai ngay.
#
# Vi sao phai co: khi bi tu choi vi goi qua day, cach lam sai nhat la goi
# lai ngay - no keo dai dung cai tinh trang minh dang muon thoat ra. Nghi
# ba phut roi hay thu, va trong ba phut do man hinh van bay so cua lan dong
# bo gan nhat, co ghi ro la so cu.
NGHI_SAU_TU_CHOI = 180  # giay
# So lan thu lai mot luot keo don truoc khi chiu thua, va gian cach giua cac
# lan. Tang dan chu khong deu nhau: bi chan ma dap cua deu tay thi khong bao
# gio duoc mo.
THU_LAI = (2, 5)  # giay


def _khoang_unix(ngay):
	"""Nua dem den nua dem cua mot ngay theo gio Viet Nam, ra unix giay."""
	from zoneinfo import ZoneInfo

	d = getdate(ngay)
	dau = datetime(d.year, d.month, d.day, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh"))
	return int(dau.timestamp()), int((dau + timedelta(days=1)).timestamp()) - 1


class LoiPancake(Exception):
	"""Pancake khong tra loi duoc. Mang theo ma HTTP de ben goi xu ly khac nhau."""

	def __init__(self, ma, loi_nguoi_doc):
		self.ma = ma
		self.loi_nguoi_doc = loi_nguoi_doc
		super().__init__(loi_nguoi_doc)


# Giau khoa API truoc khi bat ky chuoi nao di ra man hinh. Ban goc va ly do
# nam trong vagabond/lib.py - dat o do vi Pancake khong phai mo dun duy nhat
# gui khoa di trong duong dan.
_giau_khoa = giau_khoa


def _keo_don(c, k, update_status, dau, cuoi):
	"""Keo het don trong khoang thoi gian, lat qua tung trang.

	Ba dieu tep cu khong lam, va ca ba deu da can tro Sales that:

	  1. Ban cu nem thang loi cua thu vien mang len man hinh,
	     KEM CA KHOA API. Nay doi thanh mot cau tieng Viet, va khoa bi giau
	     o `_giau_khoa` truoc khi bat ky ai doc duoc.
	  2. Bi tu choi mot cai la chiu thua ngay. Nay thu lai hai lan, gian
	     cach tang dan.
	  3. Het muoi trang thi lang le dung, bo phan con lai. Ngay dong don thi
	     dung la "banh da ban ma cot Da dat khong nhuc nhich" - dung cai loi
	     Sales bao 26/08. Nay noi ra bang mot ngoai le, khong nuot.
	"""
	import time

	ra = []
	for trang in range(1, MAX_TRANG + 1):
		ds = None
		for lan in range(len(THU_LAI) + 1):
			try:
				r = _mang().get(
					"%s/shops/%s/orders" % (PANCAKE, c.pancake_shop_id),
					params={
						"api_key": k,
						"updateStatus": update_status,
						"startDateTime": dau,
						"endDateTime": cuoi,
						"page_size": 100,
						"page_number": trang,
					},
					timeout=TIMEOUT,
				)
			except Exception as e:
				if lan < len(THU_LAI):
					time.sleep(THU_LAI[lan])
					continue
				raise LoiPancake(0, "Không nối được Pancake: %s" % _giau_khoa(e))
			if r.status_code == 200:
				body = r.json()
				if (not isinstance(body, dict) or body.get("success") is False
					or not isinstance(body.get("data"), list)):
					raise LoiPancake(0, "Pancake trả phản hồi không đầy đủ; chưa thể kết luận danh sách đơn.")
				ds = body["data"]
				break
			# 403 va 429 la "goi qua day" hoac "khoa sai"; 5xx la ben ho tro
			# tro. Ca ba deu dang thu lai. 4xx con lai thi thu lai vo ich.
			if r.status_code not in (403, 408, 429, 500, 502, 503, 504):
				raise LoiPancake(r.status_code, _loi_theo_ma(r.status_code))
			if lan < len(THU_LAI):
				time.sleep(THU_LAI[lan])
				continue
			raise LoiPancake(r.status_code, _loi_theo_ma(r.status_code))
		ra.extend(ds or [])
		if len(ds or []) < 100:
			return ra
	# Ra khoi vong for nghia la trang thu MAX_TRANG van con day 100 don.
	raise LoiPancake(
		0,
		"Ngày này có hơn %d đơn, nhiều hơn mức máy kéo về một lượt. "
		"Số trên bảng sẽ thiếu. Báo anh Việt để nới mức kéo."
		% (MAX_TRANG * 100),
	)


def _loi_theo_ma(ma):
	"""Cau tieng Viet cho tung ma HTTP, viet cho Sales doc chu khong cho lap trinh."""
	if ma in (403, 429):
		return (
			"Pancake đang từ chối lượt gọi (mã %s). Thường là do nhiều máy cùng "
			"mở màn kiểm bánh nên gọi quá dày, đợi vài phút là hết. Nếu vài "
			"tiếng vẫn vậy thì khoá API Pancake trong Cài đặt đã hết hạn."
			% ma
		)
	if ma == 401:
		return "Pancake không nhận khoá API. Vào Cài đặt dán lại khoá Pancake."
	if ma >= 500:
		return "Máy chủ Pancake đang trục trặc (mã %s). Lát nữa thử lại." % ma
	return "Pancake trả về mã %s, chưa kéo được đơn." % ma


def _dem_banh(dons, dang_theo_doi=None):
	"""Gop so luong theo ma hang.

	dang_theo_doi: tap ma DA CO tren bang kiem banh hom do. Nhung ma nay duoc
	dem du tien to cua chung khong nam trong TIEN_TO_MA - de bep them tay mot
	dong Patechaud thi cot "Da dat" cua no cung chay chu khong dung im o 0.
	Mot dong chi dem duoc ton va bep lam, con don thi khong, la mot dong noi
	nua su that.

	May van chi TU dua vao bang cac ma thuoc TIEN_TO_MA - xem cho goi ham.

	Tra ve (dem, ten, hinh, khach) - ten, anh va TEN KHACH lay ngay tu don,
	khoi ton them luot goi nao. Ten khach de sales ban giao ca cho nhau.
	"""
	theo_doi = {str(x).upper() for x in (dang_theo_doi or set())}
	dem, ten, hinh, khach = {}, {}, {}, {}
	for o in dons:
		if o.get("status") in BO_QUA_TT:
			continue
		ten_khach = (o.get("bill_full_name") or "").strip()
		for it in o.get("items") or []:
			vi = it.get("variation_info") or {}
			ma = str(vi.get("display_id") or it.get("variation_id") or "").strip()
			if not ma.upper().startswith(TIEN_TO_MA) and ma.upper() not in theo_doi:
				continue
			dem[ma] = dem.get(ma, 0) + int(it.get("quantity") or 0)
			if vi.get("name"):
				ten[ma] = vi["name"]
			anh = vi.get("images") or []
			if anh and anh[0]:
				hinh[ma] = anh[0]
			if ten_khach and ten_khach not in khach.setdefault(ma, []):
				khach[ma].append(ten_khach)
	return dem, ten, hinh, khach


def _tra_anh_ten(c, k, ma):
	"""Tra anh + ten cua mot ma tu danh muc Pancake, thieu thi lay ben Next.

	Nhieu ma (vi du BAWC00053) co anh o cap SAN PHAM nhung variation nam
	trong don hang lai KHONG nhung anh - dem tu don thi thieu. Ham nay tra
	thang danh muc: uu tien anh cua variation, thieu thi lay anh san pham.

	Ma khong co tren Pancake thi lui ve danh muc Hang hoa ben Next. Han bao
	03/08/2026: BAWC00025 hien tren man kiem banh khong co ten - ly do la
	ma do CHI ton tai ben Next (Banh O Hokkaido, size 16cm), Pancake khong
	co variation nao mang ma nay nen ham tra ve rong, man hinh in ra trong.
	"""
	try:
		r = _mang().get(
			"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": ma, "page_size": 5},
			timeout=TIMEOUT,
		)
		for v in (r.json() or {}).get("data") or []:
			if str(v.get("display_id") or "").strip().lower() == ma.lower():
				ten = ((v.get("product") or {}).get("name")) or v.get("name") or ""
				ds = v.get("images") or ((v.get("product") or {}).get("images")) or []
				return ten, (ds[0] if ds else "")
	except Exception:
		pass
	return _tra_ben_next(ma)


def _tra_ben_next(ma):
	"""Lui ve danh muc Hang hoa ben Next khi Pancake khong co ma."""
	it = frappe.db.get_value("Item", ma, ["item_name", "image"], as_dict=True)
	if not it:
		return "", ""
	anh = it.image or ""
	if anh.startswith("/private"):
		anh = ""
	return it.item_name or "", anh


def _dang_ma_dung(ma):
	"""Mã có dạng dùng được ở bảng kiểm bánh: tiền tố hợp lệ + ít nhất 5 chữ số.

	Chặn mã cụt kiểu "BAWC" gõ nhầm. Vẫn cho hậu tố size cũ
	(BAWC00114MINI12CM) vì đơn cũ còn mang mã đó.

	Dùng TIEN_TO_THEM_TAY chứ không phải TIEN_TO_MA: hàm này gác cái mà NGƯỜI
	gõ hoặc chọn vào, còn TIEN_TO_MA gác cái MÁY tự nhặt từ đơn Pancake. Hai
	việc khác nhau, trộn làm một thì mở cái này là vỡ cái kia.
	"""
	return bool(
		re.match(r"^(%s)\d{5}" % "|".join(TIEN_TO_THEM_TAY), str(ma or "").strip().upper())
	)


def so_ban_ra(da_dat=0, phat_sinh=0, don_khac=0):
	"""Số bánh BÁN RA trong ngày. Phép THUẦN.

	Ba cột máy đếm: đơn Pancake tạo trước hôm nay, đơn tạo trong ngày, và
	bánh bán qua kênh không đi qua Pancake. `cho_chot` và `giu_cho` KHÔNG
	nằm ở đây: hai cột đó là giữ chỗ, bánh còn nguyên trong tủ.
	"""
	return max(0, int(da_dat or 0) + int(phat_sinh or 0) + int(don_khac or 0))


def so_roi_tu(da_dat=0, phat_sinh=0, don_khac=0, huy=0):
	"""Số bánh RỜI KHỎI TỦ trong ngày: bán ra cộng huỷ. Phép THUẦN.

	Vì sao huỷ phải nằm ở đây: bánh huỷ đã rời khỏi tủ thật, không được phép
	chạy sang tồn đầu ngày mai. Không tính là mỗi ngày huỷ bao nhiêu thì tồn
	ảo cộng dồn bấy nhiêu.

	HAI HÀM CHỨ KHÔNG MỘT (Codex chốt trên PR #218, 06/09/2026). Bản đầu gộp
	cả hai thành một hàm `so_da_tieu` rồi dùng chung cho cả phép trừ lô hàng
	lẫn phép trừ vỏ BTP. Làm vậy là lặng lẽ đổi luôn quy tắc trừ BTP, mà anh
	Việt chỉ mới duyệt "thêm cột huỷ để theo dõi" chứ chưa duyệt cho huỷ ăn
	vào vỏ BTP. Gom về một nguồn KHÔNG có nghĩa là ép hai đại lượng nghiệp vụ
	bằng nhau: `so_ban_ra` là nền chung, `so_roi_tu` cộng thêm phần huỷ, và
	mỗi nơi gọi đúng đại lượng của mình.
	"""
	return so_ban_ra(da_dat, phat_sinh, don_khac) + max(0, int(huy or 0))


def tru_theo_lo(lo, so_tieu):
	"""Trừ số đã tiêu vào các lô, LÔ CŨ TRƯỚC. Phép THUẦN, sửa tại chỗ `lo`.

	`lo` là danh sách các cặp `[số lượng, NSX]` xếp từ cũ tới mới. Bán trước
	lấy hàng cũ trước (đúng như sales tư vấn clear hàng tồn), nên phép trừ
	cũng ăn vào lô cũ trước.

	Trả về phần KHÔNG trừ được, tức là đã tiêu nhiều hơn tồn có ghi nhận.
	Bên gọi hiện bỏ qua số dư này; tách ra để sau còn dựng cảnh báo lệch mà
	không phải sờ lại vòng lặp.

	Tách khỏi `chot_ngay` ngày 06/09/2026 để kiểm thử được không cần site:
	trước đó vòng này nằm lọt trong một hàm phải có `frappe.get_doc` mới
	chạy, nên chưa từng có ca kiểm nào chạm tới.
	"""
	con = int(so_tieu or 0)
	for cap in lo:
		an = min(int(cap[0] or 0), con)
		cap[0] = int(cap[0] or 0) - an
		con -= an
	return con


# ------------------------------------------------- nguồn của từng ô tồn
#
# Issue #216, Codex chốt theo uỷ quyền của anh Việt (07/09/2026): ô tồn ngày
# mai có HAI nguồn ghi, máy chuyển lúc chốt ngày hôm trước và người đếm tay,
# mà bảng không phân biệt được, nên chốt ngày ĐÈ MẤT số đếm tay khi hôm nay
# còn tồn, còn khi hôm nay về 0 thì lại bỏ mặc số cũ. Đo thật trong bàn giao
# PR #223. Nay mỗi ô tồn mang một NGUỒN:
#
#   Tu chuyen    máy ghi lúc chốt ngày hôm trước; chốt lại được đè, kể cả về 0
#   Da kiem dem  người gõ trên màn Kiểm bánh; chốt KHÔNG đụng, chỉ ghi số máy
#                bên cạnh để đối chiếu. Đếm ra 0 cũng là một số đếm hợp lệ.
#   (trống)      số có từ trước khi có ô nguồn. Khác 0 thì "Cần xác nhận": máy
#                không đè, không cộng; bằng 0 thì coi như ô trống, máy ghi được.
#
# Chốt ngày ghi SỐ TUYỆT ĐỐI, không cộng dồn: chạy lại cho cùng kết quả.

NGUON_MAY = "Tu chuyen"
NGUON_TAY = "Da kiem dem"
# Ô MỚI thật sự: dòng vừa được dựng (them_dong, dong_bo, chốt ngày đẻ dòng
# ngày mai), chưa ai ghi số. Máy được ghi vào. Khác hẳn ô nguồn TRỐNG: đó là
# dữ liệu có từ trước khi có cột nguồn, KHÔNG suy được là máy hay tay, kể cả
# khi giá trị là 0 (0 có thể chính là số người đã đếm). Codex P1 vòng 4 trên
# PR #224: không được đoán nguồn từ giá trị.
NGUON_TRONG = "Chua ghi"
O_TON = ("ton_cu", "ton_d2", "ton_d1")
NSX_CUA = {"ton_cu": "nsx_cu", "ton_d2": "nsx_d2", "ton_d1": "nsx_d1"}
NHAN_NGUON = {NGUON_MAY: "Tự chuyển", NGUON_TAY: "Đã kiểm đếm", NGUON_TRONG: ""}


def trang_thai_o(nguon, gia_tri=None):
	"""Nhãn người đọc của một ô tồn. THUẦN. KHÔNG nhìn giá trị.

	Tự chuyển / Đã kiểm đếm theo nguồn; ô mới chưa ghi thì trống; nguồn
	trống (dữ liệu cũ) thì Cần xác nhận, dù là 0 hay dương."""
	if nguon in NHAN_NGUON:
		return NHAN_NGUON[nguon]
	return "Cần xác nhận"


def may_duoc_ghi(nguon, gia_tri=None):
	"""Chốt ngày có được ghi vào ô này không. THUẦN. KHÔNG nhìn giá trị.

	Chỉ ô do máy chuyển và ô mới chưa ai ghi. Ô đã đếm tay và ô không rõ
	nguồn (dữ liệu cũ, kể cả 0) thì máy đứng ngoài."""
	return nguon in (NGUON_MAY, NGUON_TRONG)


def dong_moi(**kw):
	"""Khai một dòng MỚI cho bảng: ba ô tồn mang nguồn Chua ghi. THUẦN.

	Mọi chỗ đẻ dòng (them_dong, dong_bo, chốt ngày) đều đi qua đây, để máy
	phân biệt được dòng mới với dòng cũ không rõ nguồn mà không cần nhìn số."""
	d = {"nguon_" + o: NGUON_TRONG for o in O_TON}
	d.update(kw)
	return d


def co_dau_vet(d):
	"""Dòng có dấu vết nghiệp vụ không xoá được: đã đếm tay ô nào, có ai đếm
	lúc nào, hay máy đã chuyển số vào (kể cả 0). THUẦN. Codex P1 vòng 4:
	đếm ra 0 rồi vẫn xoá được dòng là mất luôn ai đếm lúc nào."""
	for o in O_TON:
		if d.get("nguon_" + o) == NGUON_TAY:
			return True
		if int(d.get("may_chuyen_" + o) or 0):
			return True
	return bool((d.get("kiem_dem_ghi") or "").strip() not in ("", "{}"))


def dong_duoc_xoa(d):
	"""Cùng điều kiện cho bảng, API xoá và lưu Document từ Desk."""
	return not co_dau_vet(d) and not any(int(d.get(t) or 0) for t in SO_PHAI_RONG)


def ghi_o_chuyen(m, o, so, nsx):
	"""Máy ghi một ô tồn của dòng ngày mai lúc chốt. THUẦN với dòng có get/set.

	Luôn ghi `may_chuyen_<o>` để màn hình bày số máy bên cạnh số người, dù ô
	có được đè hay không. Trả về True nếu đã ghi vào ô."""
	m.set("may_chuyen_" + o, int(so or 0))
	if not may_duoc_ghi(m.get("nguon_" + o)):
		return False
	m.set(o, int(so or 0))
	m.set(NSX_CUA[o], nsx if so else None)
	m.set("nguon_" + o, NGUON_MAY)
	return True


def ghi_dem_tay(d, o, so, ai, luc):
	"""Người đếm một ô tồn: ghi số, đánh dấu nguồn tay, ghi ai và lúc nào. THUẦN."""
	d.set(o, int(so or 0))
	d.set("nguon_" + o, NGUON_TAY)
	try:
		ghi = json.loads(d.get("kiem_dem_ghi") or "{}")
	except Exception:
		ghi = {}
	if not isinstance(ghi, dict):
		ghi = {}
	ghi[o] = {"ai": ai or "", "luc": str(luc or "")}
	d.set("kiem_dem_ghi", json.dumps(ghi, ensure_ascii=False))


def _doc_kiem_dem_ghi(d):
	try:
		ghi = json.loads(d.get("kiem_dem_ghi") or "{}")
		return ghi if isinstance(ghi, dict) else {}
	except Exception:
		return {}


def _co_that(c, k, ma):
	"""Ma co that: co tren Pancake, hoac co trong danh muc Hang hoa ben Next."""
	if frappe.db.exists("Item", ma):
		return True
	ten, _anh = _tra_anh_ten(c, k, ma)
	return bool(ten)


def _lay_hoac_tao(ngay):
	ma = "KB-%s" % getdate(ngay)
	if frappe.db.exists("Kiem Banh Ngay", ma):
		return frappe.get_doc("Kiem Banh Ngay", ma)
	doc = frappe.new_doc("Kiem Banh Ngay")
	doc.ngay = getdate(ngay)
	doc.insert(ignore_permissions=True)
	return doc


def _bat_dau_nghi(ngay):
	"""Bao ca he nghi goi Pancake mot lat.

	Nghi CHUNG chu khong phai rieng man kiem banh: chinh cai canh moi mo dun
	tu dem gio rieng roi thay nhau dap cua la thu da nuoi cai loi 403 hai ngay
	26 va 27/08. Xem vagabond/pancake_nhip.py.
	"""
	pancake_nhip.bat_dau_nghi()


def _con_nghi(ngay):
	"""Con bao nhieu giay nua ca he moi duoc goi Pancake. 0 la goi duoc ngay."""
	return pancake_nhip.con_nghi()


def _bang_kem_loi(ngay, loi, cho_giay=0):
	"""Bang cua lan dong bo gan nhat, kem mot cau noi ro vi sao chua moi.

	Man hinh doc `loi` de bay mot dong canh bao, va doc `cho_giay` de biet
	bao lau nua hay goi lai - khong thi no cu goi ba muoi giay mot lan vao
	dung cai cua dang dong.
	"""
	ra = bang(ngay)
	ra["loi"] = loi
	ra["cho_giay"] = int(cho_giay or 0)
	return ra


@frappe.whitelist()
def dong_bo(ngay=None):
	"""Dem lai "da dat" va "phat sinh" cua mot ngay tu Pancake.

	Chay tay bang nut tren man hinh, va tu dong 5 phut mot lan.
	"""
	c = cfg()
	k = key(c, "pancake_api_key")
	if not k or not c.pancake_shop_id:
		frappe.throw("Chua dien khoa Pancake trong Vagabond Settings")

	ngay = getdate(ngay) if ngay else getdate()

	# Man hinh cua moi nhan vien tu goi ham nay lien tuc. Vua dong bo xong
	# trong vong GIAN_CACH_DONG_BO giay thi tra bang luon, khong goi lai
	# Pancake - vua nhanh vua khoi lam phien API cua nguoi ta.
	ma_doc = "KB-%s" % ngay
	if frappe.db.exists("Kiem Banh Ngay", ma_doc):
		luc = frappe.db.get_value("Kiem Banh Ngay", ma_doc, "dong_bo_luc")
		if luc and (now_datetime() - luc).total_seconds() < GIAN_CACH_DONG_BO:
			return bang(ngay)

	# Dang trong ky nghi sau khi bi Pancake tu choi: tra bang cu kem loi.
	con = _con_nghi(ngay)
	if con:
		return _bang_kem_loi(
			ngay,
			"Pancake vừa từ chối nên máy đang nghỉ %d giây rồi thử lại. "
			"Số dưới đây là của lần đồng bộ gần nhất." % con,
			con,
		)

	dau, cuoi = _khoang_unix(ngay)

	# Keo don. Pancake tu choi thi KHONG lam do ca man hinh: ghi nho de nghi
	# mot lat, roi tra ve bang cua lan dong bo gan nhat kem mot cau noi ro so
	# do la so cu. Sales van lam viec duoc, va van biet minh dang nhin so cu.
	#
	# Truoc 26/08/2026 cho nay nem thang ngoai le cua thu vien mang len man,
	# nen Sales doc duoc mot dong do dai loang ngoang co ca khoa API trong
	# do, va khong biet phai lam gi.
	try:
		giao_hom_nay = _keo_don(c, k, "estimate_delivery_date", dau, cuoi)
		tao_hom_nay = _keo_don(c, k, "inserted_at", dau, cuoi)
	except LoiPancake as e:
		pancake_nhip.ghi_hong(
			e.loi_nguoi_doc, nghi=(e.ma in (403, 408, 429) or e.ma >= 500)
		)
		frappe.log_error(_giau_khoa(frappe.get_traceback()), "kiem_banh: keo don Pancake")
		return _bang_kem_loi(ngay, e.loi_nguoi_doc, _con_nghi(ngay))
	pancake_nhip.ghi_ok()
	ma_tao_hom_nay = {o.get("id") for o in tao_hom_nay}

	# Chia ba ro (y Loan Anh 01/08):
	# - CHO CHOT: don con trang thai Moi (0) - sales dang tu van, giu cho mem.
	# - DA DAT / PHAT SINH: don DA CHOT (khac Moi), chia theo tao truoc hay
	#   tao trong ngay giao. Chot xong don tu nhay tu Cho chot sang day.
	moi_don = [o for o in giao_hom_nay if o.get("status") == 0]
	chot_don = [o for o in giao_hom_nay if o.get("status") != 0]
	ps_don = [o for o in chot_don if o.get("id") in ma_tao_hom_nay]
	dd_don = [o for o in chot_don if o.get("id") not in ma_tao_hom_nay]
	# Mo so TRUOC khi dem: phep dem can biet bang dang theo doi nhung ma nao,
	# de dem ca don cua dong bep them tay (Patechaud, banh le, BTP).
	doc = _lay_hoac_tao(ngay)
	dang_theo_doi = {str(d.ma_hang or "").upper() for d in doc.dong if d.ma_hang}

	dem_dd, ten1, hinh1, _k1 = _dem_banh(dd_don, dang_theo_doi)
	dem_ps, ten2, hinh2, khach_ps = _dem_banh(ps_don, dang_theo_doi)
	dem_cho, ten3, hinh3, khach_cho = _dem_banh(moi_don, dang_theo_doi)
	ten1.update(ten2)
	ten1.update(ten3)
	hinh1.update(hinh2)
	hinh1.update(hinh3)

	# Don dong khong phai hang kiem banh (phi giao, phu kien) lot vao tu ban
	# truoc. Loc theo TIEN_TO_THEM_TAY chu KHONG phai TIEN_TO_MA:
	#
	# Bep them tay mot dong Patechaud vao bang, den lan dong bo sau (5 phut
	# mot lan, chay ngam) dong do bien mat khong dau vet - vi bo loc cu chi
	# giu BAWC/BAWS. Bep se tuong minh bam hut hoac may nuot mat so vua dem.
	# Cho bep THEM ma khong cho bang GIU thi tinh nang do khong ton tai.
	# Dòng gõ trên Desk có thể mang mã lạ. Chỉ dọn dòng trắng, không làm
	# mất số hoặc audit rồi khiến validate chặn cả ngày kiểm bánh.
	giu_la = [d for d in doc.dong
		if not str(d.ma_hang or "").upper().startswith(TIEN_TO_THEM_TAY)
		and not dong_duoc_xoa(d)]
	if giu_la:
		frappe.log_error(title="Kiểm bánh: giữ dòng mã cần đối chiếu",
			message="Ngày %s, mã: %s. Dòng có số hoặc dấu kiểm đếm nên được giữ lại."
			% (ngay, ", ".join(str(d.ma_hang or "") for d in giu_la)))
	doc.dong = [
		d for d in doc.dong
		if str(d.ma_hang or "").upper().startswith(TIEN_TO_THEM_TAY) or not dong_duoc_xoa(d)
	]
	co = {d.ma_hang: d for d in doc.dong}
	for ma in set(list(dem_dd) + list(dem_ps) + list(dem_cho)):
		if ma not in co:
			d = doc.append("dong", dong_moi(ma_hang=ma, ten_banh=ten1.get(ma, "")))
			co[ma] = d
		elif ten1.get(ma) and not co[ma].ten_banh:
			co[ma].ten_banh = ten1[ma]
	# Don kenh khac (Grab, Shopee, quay...) khong nam trong Pancake, dem
	# rieng tu hoa don ban ra. Chay o day de moi lan dong bo la so dung.
	_ghi_don_khac(doc, ngay)
	# Giữ chỗ của khách đặt bánh ổ. Nhịp đồng bộ phải đo lại cột này để TỰ
	# CHỮA nếu một lần hook phiếu đặt bị lỗi: không có dòng này thì một
	# hook hỏng là số giữ chỗ sai vĩnh viễn cho tới khi có người sờ tay.
	# Codex bắt ở PR #197.
	_ghi_giu_cho(doc, ngay)
	co = {d.ma_hang: d for d in doc.dong}

	for ma, d in co.items():
		d.da_dat = dem_dd.get(ma, 0)
		d.phat_sinh = dem_ps.get(ma, 0)
		d.cho_chot = dem_cho.get(ma, 0)
		d.ten_khach_ps = ", ".join(khach_ps.get(ma, []))
		d.ten_khach_cho = ", ".join(khach_cho.get(ma, []))
		# Anh moi ben Pancake phai de len anh cu. Truoc day chi nhan khi o
		# anh con trong nen doi anh ben Pancake xong web van anh cu
		# (Minh Vu bao 10/08/2026).
		if hinh1.get(ma) and hinh1[ma] != d.hinh:
			d.hinh = hinh1[ma]

	# Bu anh cho dong con thieu: don khong nhung anh thi tra danh muc.
	# Moi ma toi da mot lan moi 6 tieng (cache) de khoi goi Pancake vo ich
	# voi ma that su khong co anh; anh da luu thi khong bao gio tra lai.
	nho = frappe.cache()
	for ma, d in co.items():
		if d.hinh:
			continue
		khoa = "kb_tra_anh:%s" % ma
		if nho.get_value(khoa):
			continue
		nho.set_value(khoa, "1", expires_in_sec=6 * 3600)
		ten_p, anh_p = _tra_anh_ten(c, k, ma)
		if anh_p:
			d.hinh = anh_p
		if ten_p and not d.ten_banh:
			d.ten_banh = ten_p

	doc.dong_bo_luc = now_datetime()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return bang(ngay)




# Nguon don KHONG di qua Pancake: don ban tay cua sales (Grab, Shopee, Be,
# GreenSM, khach si) va don tinh tien tai quay. Don Pancake da duoc dem tu
# API o tren roi, dem lai o day la tru hai lan.
NGUON_PANCAKE = ("", "pancake")


def _dem_don_khac(ngay, dang_theo_doi=None):
	"""Dem banh da ban qua kenh khac Pancake trong ngay, tu hoa don ban ra.

	dang_theo_doi: tap ma da co tren bang, de dong bep them tay (Patechaud,
	banh le, BTP) cung duoc tru khi ban tai quay - giong het ly do o _dem_banh.

	Loan Anh 08/08/2026: khach dat gap qua Grab thi sales bam don tay ben
	Doanh thu Sales; truoc day phai tao them mot don Pancake gia chi de tru
	so tren bang kiem banh, thanh ra mot khach hai bill. Nay dem thang.

	Tra ve (dem, mo_ta): dem[ma hang] = so luong, mo_ta[ma hang] = danh sach
	"GrabFood #GF-441" de sales biet so do tu don nao ra.
	"""
	ngay = getdate(ngay)
	sis = frappe.get_all(
		"Sales Invoice",
		# vgb_huy 0: bill da huy khong con la hang ban ra nen khong duoc tru
		# so tren bang kiem banh, khong thi sales dem thieu banh trong kho.
		filters={"posting_date": str(ngay), "docstatus": ["<", 2], "vgb_huy": 0},
		fields=["name", "custom_nguon", "custom_pancake_display_id"],
		limit_page_length=0,
	)
	theo_ten = {}
	for si in sis:
		if str(si.custom_nguon or "").strip().lower() in NGUON_PANCAKE:
			continue
		theo_ten[si.name] = si
	if not theo_ten:
		return {}, {}

	dong = frappe.get_all(
		"Sales Invoice Item",
		filters={"parent": ["in", sorted(theo_ten)]},
		fields=["parent", "item_code", "qty"],
		limit_page_length=0,
	)
	dem, mo_ta = {}, {}
	theo_doi = {str(x).upper() for x in (dang_theo_doi or set())}
	for r in dong:
		ma = str(r.item_code or "").strip()
		if not ma.upper().startswith(TIEN_TO_MA) and ma.upper() not in theo_doi:
			continue
		sl = int(r.qty or 0)
		if sl <= 0:
			continue
		dem[ma] = dem.get(ma, 0) + sl
		si = theo_ten[r.parent]
		nhan = "%s%s" % (
			si.custom_nguon or "Kenh khac",
			" #" + str(si.custom_pancake_display_id) if si.custom_pancake_display_id else "",
		)
		if sl > 1:
			nhan += " (%d)" % sl
		ds = mo_ta.setdefault(ma, [])
		if nhan not in ds:
			ds.append(nhan)
	return dem, mo_ta


def _them_dong_thieu(doc, co, thieu):
	"""Thêm các mã chưa có dòng trên bảng, lấy tên và ảnh từ danh mục Hàng hoá.

	Dùng chung cho cột Kênh khác và cột Giữ chỗ. Trước đây chỉ cột Kênh khác
	có đường thêm dòng, nên một loại bánh mới chỉ có khách đặt trước mà chưa
	bán buổi nào thì không bao giờ hiện trên bảng, và số giữ chỗ của nó không
	trừ vào khả năng bán. Codex bắt ở PR #197.
	"""
	if not thieu:
		return
	ten_moi = {}
	for it in frappe.get_all(
		"Item",
		filters={"name": ["in", sorted(thieu)]},
		fields=["name", "item_name", "image"],
		limit_page_length=0,
	):
		ten_moi[it.name] = it
	for ma in thieu:
		x = ten_moi.get(ma) or {}
		anh = x.get("image") or ""
		d = doc.append(
			"dong",
			dong_moi(
				ma_hang=ma,
				ten_banh=x.get("item_name") or ma,
				hinh=anh if not str(anh).startswith("/private") else "",
			),
		)
		co[ma] = d


def _ghi_giu_cho(doc, ngay):
	"""Đo cột "Giữ chỗ" từ phiếu đặt bánh ổ. KHÔNG tự save.

	Ngày đã chốt số thì không đụng vào nữa, giống hệt cột Kênh khác: số của
	ngày đó đã khoá, tồn còn lại đã chạy sang ngày mai theo con số lúc chốt.

	Trả về None khi ĐỌC HỎNG, và khi đó không sửa một ô nào. Bản đầu ghi 0
	vào mọi dòng trong trường hợp này, tức là một trục trặc cơ sở dữ liệu
	vài giây sẽ nhả toàn bộ bánh đã giữ của khách ra bán tiếp. Codex bắt
	đúng ở PR #197.
	"""
	if doc.tinh_trang == "Da chot":
		return {}
	from vagabond import dat_banh

	try:
		dem = dat_banh.dem_giu_cho(ngay)
	except Exception:
		frappe.log_error(
			title="Vagabond: doc so giu cho that bai, giu nguyen so cu",
			message=frappe.get_traceback(),
		)
		return None
	co = {d.ma_hang: d for d in doc.dong}
	_them_dong_thieu(doc, co, [ma for ma in dem if ma not in co])
	for ma, d in co.items():
		d.giu_cho = int(dem.get(str(ma or "").upper()) or 0)
	return dem


def _ghi_don_khac(doc, ngay):
	"""Do cot "Kenh khac" vao mot ban ghi kiem banh. KHONG tu save.

	Ngay da chot so thi khong dung vao nua - so cua ngay do da khoa, ton
	con lai da chay sang ngay mai theo con so luc chot.
	"""
	if doc.tinh_trang == "Da chot":
		return {}
	dem, mo_ta = _dem_don_khac(
		ngay, {str(d.ma_hang or "").upper() for d in doc.dong if d.ma_hang}
	)
	co = {d.ma_hang: d for d in doc.dong}
	_them_dong_thieu(doc, co, [ma for ma in dem if ma not in co])
	for ma, d in co.items():
		d.don_khac = dem.get(ma, 0)
		d.ten_khach_khac = ", ".join(mo_ta.get(ma, []))
	return dem


@frappe.whitelist()
def cap_nhat_don_khac(ngay=None):
	"""Do lai rieng cot "Kenh khac" cho mot ngay, khong dung den Pancake.

	Goi ngay sau khi sales bam xong mot don tay, de so tren man kiem banh
	tru lien chu khong doi lich 5 phut.
	"""
	ngay = getdate(ngay) if ngay else getdate()
	ma = "KB-%s" % ngay
	dem, _ = _dem_don_khac(ngay)
	if not frappe.db.exists("Kiem Banh Ngay", ma):
		if not dem:
			return {"ok": 1, "bo_qua": 1}
	doc = _lay_hoac_tao(ngay)
	if doc.tinh_trang == "Da chot":
		return {"ok": 1, "da_chot": 1}
	_ghi_don_khac(doc, ngay)
	_ghi_giu_cho(doc, ngay)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ma_hang": len(dem)}


def cap_nhat_giu_cho(ngay=None):
	"""Đo lại riêng cột "Giữ chỗ" cho một ngày nhận.

	KHÔNG tự commit: hàm này chạy bên trong lượt lưu phiếu đặt của người
	dùng, commit ở giữa là cắt đôi giao dịch của họ. Khung tự commit khi
	lượt lưu xong.
	"""
	ngay = getdate(ngay) if ngay else getdate()
	ma = "KB-%s" % ngay
	if not frappe.db.exists("Kiem Banh Ngay", ma):
		from vagabond import dat_banh

		if not dat_banh.dem_giu_cho(ngay):
			return {"ok": 1, "bo_qua": 1}
	doc = _lay_hoac_tao(ngay)
	if doc.tinh_trang == "Da chot":
		return {"ok": 1, "da_chot": 1}
	if _ghi_giu_cho(doc, ngay) is None:
		return {"ok": 0, "doc_hong": 1}
	doc.save(ignore_permissions=True)
	return {"ok": 1}


def khi_doi_phieu_dat(doc, method=None):
	"""Hook Sales Order: phiếu đặt đổi thì đo lại cột Giữ chỗ.

	Codex bắt ở PR #197: bản đầu chỉ đo cột này bên trong đường của hoá
	đơn, mà không móc vào sự kiện nào của phiếu đặt. Nghĩa là lập một phiếu
	đặt hợp lệ xong, cột giữ chỗ vẫn bằng 0 cho tới khi tình cờ có một hoá
	đơn khác chạy qua, và bánh đã bán cho khách đặt vẫn hiện là bán được.

	Đo CẢ ngày cũ lẫn ngày mới, vì dời ngày nhận thì ngày cũ phải nhả số
	ra. Nuốt lỗi vì hook này chạy giữa lượt lưu của người dùng: bảng kiểm
	bánh sai một nhịp thì nhịp đồng bộ 5 phút chữa được, còn chặn không cho
	sales lưu phiếu đặt của khách thì không chữa được bằng gì.
	"""
	try:
		from vagabond import dat_banh

		cu = doc.get_doc_before_save() if hasattr(doc, "get_doc_before_save") else None
		ngay = dat_banh.gop_ngay(
			dat_banh.ngay_nhan_cua(doc), dat_banh.ngay_nhan_cua(cu)
		)
		for n in ngay:
			try:
				cap_nhat_giu_cho(n)
			except Exception:
				frappe.log_error(
					title="Vagabond: cap nhat giu cho mot ngay that bai",
					message=frappe.get_traceback(),
				)
	except Exception:
		frappe.log_error(
			title="Vagabond: hook phieu dat banh",
			message=frappe.get_traceback(),
		)


def khi_doi_hoa_don(doc, method=None):
	"""Hook Sales Invoice: huy hoac xoa hoa don thi tra so lai bang kiem banh.

	Do lai CA NGAY CU LAN NGAY MOI (sua 05/09/2026, Codex bat duoc o issue
	#195). Ban cu chi goi voi `doc.posting_date`, tuc ngay MOI. Ai doi ngay
	chung tu tu 20 sang 22 thi ngay 20 van tru mot cai banh cua to hoa don
	da khong con o do nua, va sales tu choi khach oan. Loi im lang: khong
	cau bao nao keu len, chi lo ra khi co nguoi ngoi doi tay hai bang.
	"""
	try:
		if str(doc.get("custom_nguon") or "").strip().lower() in NGUON_PANCAKE:
			return
		if not any(
			str(r.item_code or "").upper().startswith(TIEN_TO_MA) for r in (doc.get("items") or [])
		):
			return
		from vagabond.dat_banh import hai_ngay_phai_do

		cu = (doc.get_doc_before_save() or {}) if hasattr(doc, "get_doc_before_save") else {}
		for ngay in hai_ngay_phai_do(
			(cu or {}).get("posting_date") if cu else None, doc.posting_date
		):
			cap_nhat_don_khac(ngay)
	except Exception:
		frappe.log_error(title="Vagabond: cap nhat kiem banh khi doi hoa don", message=frappe.get_traceback())


def dong_bo_tu_dong():
	"""Cho scheduler goi. Nuot loi de khong lam ban nhat ky he thong moi 5 phut."""
	try:
		dong_bo()
	except Exception:
		frappe.log_error(title="Vagabond: dong bo kiem banh loi", message=frappe.get_traceback())


@frappe.whitelist()
def bang(ngay=None):
	"""Du lieu cho man hinh dien thoai."""
	ngay = getdate(ngay) if ngay else getdate()
	ma = "KB-%s" % ngay
	if not frappe.db.exists("Kiem Banh Ngay", ma):
		return {"ngay": str(ngay), "co_so": 0, "dong": []}
	doc = frappe.get_doc("Kiem Banh Ngay", ma)
	tat = tat_ban_web.bang([d.ma_hang for d in doc.dong], ngay)
	return {
		"ngay": str(ngay),
		"co_so": 1,
		"tinh_trang": doc.tinh_trang,
		"dong_bo_luc": str(doc.dong_bo_luc or ""),
		"chot_luc": str(doc.chot_luc or ""),
		"dong": [
			{
				"ma_hang": d.ma_hang, "ten_banh": d.ten_banh, "hinh": d.hinh or "",
				"ton_cu": d.ton_cu or 0, "nsx_cu": str(d.nsx_cu or ""),
				"ton_d2": d.ton_d2 or 0, "nsx_d2": str(d.nsx_d2 or ""),
				"ton_d1": d.ton_d1 or 0, "nsx_d1": str(d.nsx_d1 or ""),
				"sx": d.sx or 0, "huy": d.huy or 0, "da_dat": d.da_dat or 0,
				"phat_sinh": d.phat_sinh or 0, "ten_khach_ps": d.ten_khach_ps or "",
				"cho_chot": d.cho_chot or 0, "ten_khach_cho": d.ten_khach_cho or "",
				"don_khac": d.don_khac or 0, "ten_khach_khac": d.ten_khach_khac or "",
				"co_the_ban": d.co_the_ban or 0,
				# Cong tac tam ngung ban tren web. Bay len man de nguoi bam
				# nhin thay ngay minh vua tat cai gi, va den bao gio ban lai.
				"tat_web": (tat.get(d.ma_hang) or {}).get("tat", 0),
				"tat_web_den": (tat.get(d.ma_hang) or {}).get("den_ngay", ""),
				# Nguồn từng ô tồn (#216): nhãn, số máy chuyển, ai đếm lúc nào.
				"nguon": {
					o: {
						"trang_thai": trang_thai_o(d.get("nguon_" + o)),
						"may_chuyen": int(d.get("may_chuyen_" + o) or 0),
						"ai": (_doc_kiem_dem_ghi(d).get(o) or {}).get("ai", ""),
						"luc": (_doc_kiem_dem_ghi(d).get(o) or {}).get("luc", ""),
					}
					for o in O_TON
				},
				# Máy chủ quyết dòng có xoá được không; màn hình chỉ bày nút theo
				# khoá này, không tự suy từ số (Codex P1 vòng 4).
				"xoa_duoc": int(dong_duoc_xoa(d)),
			}
			for d in doc.dong
		],
	}


# Cot nguoi go tay. "huy" vao day tu 06/09/2026: cua hang go so banh hong,
# het han, roi vo, nem thu ngay tren bang nay (anh Viet chot huong A cua
# issue #216). Cac cot may dem thi khong ai sua duoc.
SUA_DUOC = {"ton_cu", "ton_d2", "ton_d1", "sx", "huy"}


@frappe.whitelist()
def luu_o(ngay, ma_hang, truong, gia_tri):
	"""Sua mot o tu dien thoai: ton dau (sales kiem tu) hoac san xuat (bep).

	Cac cot may dem (da dat, phat sinh, co the ban) KHONG sua duoc tu day -
	do la ca ly do phan he nay ton tai.
	"""
	if truong not in SUA_DUOC:
		frappe.throw("Cot nay may tu dem, khong sua tay duoc")
	doc = frappe.get_doc("Kiem Banh Ngay", "KB-%s" % getdate(ngay))
	if doc.tinh_trang == "Da chot":
		frappe.throw("Ngay nay da chot so, khong sua nua")
	for d in doc.dong:
		if d.ma_hang == ma_hang:
			so = doc_so_o(truong, gia_tri, ma_hang)
			if truong in O_TON:
				# Ô tồn người đếm: đánh dấu nguồn tay để chốt ngày hôm trước
				# (hay chốt lại) không đè mất. Đếm ra 0 cũng là số đếm. #216.
				ghi_dem_tay(d, truong, so, frappe.session.user, now_datetime())
			else:
				d.set(truong, so)
			# Cửa này đã tự ghi nguồn; báo cho lớp doctype khỏi đánh dấu lại.
			frappe.flags.vgb_ton_da_co_nguon = True
			try:
				doc.save()  # giu quyen that cua nguoi dang sua, de con vet ai sua gi
			finally:
				frappe.flags.vgb_ton_da_co_nguon = False
			frappe.db.commit()
			return {"ok": 1, "co_the_ban": d.co_the_ban}
	frappe.throw("Khong thay ma hang %s" % ma_hang)


def doc_so_o(truong, gia_tri, ma_hang=None):
	"""Đọc số người gõ cho một ô, theo đúng chính sách của TỪNG cột. THUẦN.

	Cột "huy" (Codex trên PR #218, vòng 4, 06/09/2026): kiểm GIÁ TRỊ GỐC
	trước khi ép kiểu, dùng CHUNG một quy tắc với lớp doctype
	(`KiemBanhNgay._doc_so_huy`): rỗng là 0, số nguyên không âm thì nhận,
	còn lại NÉM LỖI có kèm mã hàng. Bản trước `luu_o` làm `max(0, int(...))`
	nên 1.9 thành 1 và -0.5 thành 0 ngay ở cửa này, lớp doctype không bao
	giờ thấy giá trị gốc, và người gõ không được báo gì. Một quy tắc ở hai
	chỗ thì sớm muộn lệch nhau, nên cửa này gọi thẳng hàm của doctype chứ
	không chép lại (điều 18).

	Các cột khác (ton_cu, ton_d2, ton_d1, sx) GIỮ NGUYÊN cách đọc cũ
	`max(0, int(...))`. Codex dặn rõ: chỉ sửa trường huy, không tự đổi
	chính sách các cột khác khi chưa ai duyệt.
	"""
	if truong == "huy":
		from vagabond.vagabond.doctype.kiem_banh_ngay.kiem_banh_ngay import KiemBanhNgay

		return KiemBanhNgay._doc_so_huy(gia_tri, ma_hang)
	return max(0, int(gia_tri or 0))


@frappe.whitelist()
def them_dong(ngay, ma_hang):
	"""Bep them banh se lam hom nay ma chua co don nao."""
	c = cfg()
	k = key(c, "pancake_api_key")
	ma_hang = str(ma_hang or "").strip()
	if not ma_hang:
		frappe.throw("Thieu ma hang")
	if not _dang_ma_dung(ma_hang):
		frappe.throw(
			"Mã %s không đúng dạng. Bảng này nhận bánh ổ, bánh sỉ, bánh nướng, "
			"bánh lạnh, bánh khô, hộp bánh theo mùa và bán thành phẩm - mã phải "
			"bắt đầu bằng %s kèm 5 chữ số, ví dụ BAWC00098 hay BANU00065."
			% (ma_hang, ", ".join(TIEN_TO_THEM_TAY))
		)
	doc = _lay_hoac_tao(ngay)
	if any(d.ma_hang == ma_hang for d in doc.dong):
		frappe.throw("Ma nay da co trong bang")
	if not _co_that(c, k, ma_hang):
		frappe.throw(
			"Không tìm thấy mã %s ở cả Pancake lẫn danh mục Hàng hoá bên Next. "
			"Anh chị kiểm tra lại mã, hoặc tạo mã đó trước rồi thêm sau." % ma_hang
		)
	ten, anh = _tra_anh_ten(c, k, ma_hang)
	doc.append("dong", dong_moi(ma_hang=ma_hang, ten_banh=ten, hinh=anh))
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ten_banh": ten}


SO_PHAI_RONG = (
	"ton_cu", "ton_d2", "ton_d1", "sx", "huy",
	"da_dat", "phat_sinh", "cho_chot", "don_khac", "giu_cho",
)


@frappe.whitelist()
def xoa_dong(ngay, ma_hang):
	"""Go mot dong go nham khoi bang - chi khi dong do trang tron.

	Han bao 03/08/2026 co hai dong rac trong so: BAWC00025 va mot dong ten
	dung "BAWC". Truoc day khong co duong nao go ra, phai vao Desk. Gio man
	hinh co dau x tren the nao chua co so nao.
	"""
	doc = frappe.get_doc("Kiem Banh Ngay", "KB-%s" % getdate(ngay))
	if doc.tinh_trang == "Da chot":
		frappe.throw("Ngày này đã chốt sổ, không xoá dòng được nữa")
	for d in doc.dong:
		if d.ma_hang != ma_hang:
			continue
		if not dong_duoc_xoa(d):
			frappe.throw("Mã %s đang có số hoặc dấu kiểm đếm. Giữ dòng để đối chiếu, không xoá được." % ma_hang)
		doc.remove(d)
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return {"ok": 1}
	frappe.throw("Khong thay ma hang %s" % ma_hang)


@frappe.whitelist()
def tat_ban_web_dat(ma_hang=None, tat=1, den_ngay=None):
	"""Bat hoac tat ban mot ma tren web, bam tu man Kiem banh.

	Chi la mot cua vao: phep that nam trong vagabond/tat_ban_web.py, dung
	chung voi man Kiem mua vu. Co cua rieng o day vi trang /kiem-banh goi API
	bang tien to `vagabond.kiem_banh.`, khong goi thang mo dun khac duoc.
	"""
	return tat_ban_web.dat(ma_hang=ma_hang, tat=tat, den_ngay=den_ngay)


@frappe.whitelist()
def chot_ngay(ngay=None):
	"""Chot so cuoi ngay: so con lai chay sang ton dau ngay mai, theo lo cu truoc.

	Ban truoc lay hang cu truoc (dung nhu sales tu van clear hang ton), nen
	phep tru cung an vao lo cu truoc: ton_cu -> ton_d2 -> ton_d1 -> sx.
	Phan con du doi sang ngay mai lui mot bac tuoi.
	"""
	ngay = getdate(ngay) if ngay else getdate()
	doc = frappe.get_doc("Kiem Banh Ngay", "KB-%s" % ngay)
	if doc.tinh_trang == "Da chot":
		frappe.throw("Ngay %s da chot roi" % ngay)

	# Dong bo lan cuoi cho so moi nhat truoc khi khoa.
	dong_bo(ngay)
	doc.reload()

	mai = _lay_hoac_tao(add_days(ngay, 1))
	co_mai = {d.ma_hang: d for d in mai.dong}

	for d in doc.dong:
		# Trừ lô hàng dùng SỐ RỜI TỦ: bánh huỷ cũng phải biến khỏi tồn ngày mai.
		ban = so_roi_tu(d.da_dat, d.phat_sinh, d.don_khac, d.huy)
		lo = [
			[d.ton_cu or 0, d.nsx_cu],
			[d.ton_d2 or 0, d.nsx_d2],
			[d.ton_d1 or 0, d.nsx_d1],
			[d.sx or 0, ngay],
		]
		tru_theo_lo(lo, ban)
		# lo[0]+lo[1] don thanh "cu hon" cua ngay mai, lay NSX cu nhat lam moc
		cu = lo[0][0] + lo[1][0]
		nsx_cu = lo[0][1] if lo[0][0] else (lo[1][1] if lo[1][0] else None)
		m = co_mai.get(d.ma_hang)
		if not m:
			# Khong con gi va ngay mai chua co dong thi khong de dong trong.
			if not (cu or lo[2][0] or lo[3][0]):
				continue
			m = mai.append("dong", dong_moi(ma_hang=d.ma_hang, ten_banh=d.ten_banh))
			co_mai[d.ma_hang] = m
		# Tung o theo NGUON cua no (#216): o may chuyen thi ghi de, ke ca ve 0
		# (truoc day con 0 la bo qua, so cu nam lai); o nguoi da dem thi giu,
		# chi ghi so may ben canh; o chua ro nguon ma co so thi giu de xac nhan.
		ghi_o_chuyen(m, "ton_cu", cu, nsx_cu)
		ghi_o_chuyen(m, "ton_d2", lo[2][0], lo[2][1])
		ghi_o_chuyen(m, "ton_d1", lo[3][0], ngay)

	# Chốt là đường của MÁY: lớp doctype không được coi các ô vừa ghi là
	# người sửa tay (xem KiemBanhNgay._giu_nguon_ton).
	frappe.flags.vgb_ton_da_co_nguon = True
	try:
		mai.save(ignore_permissions=True)
	finally:
		frappe.flags.vgb_ton_da_co_nguon = False

	# Tru kho BTP cap 2: moi banh giao xong hom nay von da an mot vo BTP
	# luc bep lay ra trang tri toi hom truoc (quy trinh Han 01/08). Tru
	# TAP TRUNG luc chot so de bep khong bao gio phai tru tay - trong ngay,
	# phan da lay ra van duoc "don dang giu" tru ho nen CON NHAN luon dung.
	try:
		kho = frappe.get_single("BTP Banh O")
		co_btp = {b.ma_hang: b for b in kho.dong}
		doi = False
		for d in doc.dong:
			b = co_btp.get(d.ma_hang)
			if not b:
				continue
			# Trừ vỏ BTP giữ NGUYÊN quy tắc cũ: chỉ theo số BÁN RA, không cộng
			# huỷ. Quy tắc này chưa ai duyệt sửa, và một cái bánh huỷ chưa chắc
			# đã ăn một vỏ mới - có thể là hàng tồn cũ vốn đã trừ vỏ hôm trước.
			# Muốn đưa huỷ vào đây thì phải trình bảng ví dụ cho anh Việt chốt.
			an = so_ban_ra(d.da_dat, d.phat_sinh, d.don_khac)
			if an and ((b.so_btp or 0) or (b.so_decor or 0)):
				b.so_btp = max(0, (b.so_btp or 0) - an)
				# Banh ban ra la banh DA du decor - tru luon so du decor
				b.so_decor = max(0, (b.so_decor or 0) - an)
				doi = True
		if doi:
			kho.cap_nhat_luc = now_datetime()
			kho.save(ignore_permissions=True)
	except Exception:
		frappe.log_error(title="Vagabond: tru BTP khi chot ngay loi", message=frappe.get_traceback())

	doc.tinh_trang = "Da chot"
	doc.chot_luc = now_datetime()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": 1, "ngay_mai": str(add_days(ngay, 1))}


RE_SIZE = re.compile(r"^(.*?)[,\s]*\bsize\b\s*(\d+)\s*cm\b.*$", re.IGNORECASE)
# Ten ben Next deu bat dau bang "Banh O ..."; trang ban hang goi ten ngan.
RE_TIEN_TO = re.compile(r"^b[áa]nh\s+[ổo]\s+", re.IGNORECASE)


def _tach_ten_size(ten):
	"""Bánh Ổ Kankin, size 12cm  ->  ("Kankin", 12).

	Ten khong co size thi tra size 0, trang ban hang tu hieu la banh mot co.
	"""
	t = str(ten or "").strip()
	m = RE_SIZE.match(t)
	if not m:
		return RE_TIEN_TO.sub("", t).strip(), 0
	goc = (m.group(1) or "").replace(",", " ").strip()
	return RE_TIEN_TO.sub("", goc).strip(), int(m.group(2))


# Anh va mo ta tren web phai bam theo danh muc Pancake. Sales thay anh
# hay sua mo ta ben do thi web doi theo trong vong nua tieng (Minh Vu bao
# 10/08/2026: anh banh Hannari doi roi ma web van anh cu).
CACHE_SP_GIAY = 1800


def _sach_html(s):
	"""Mo ta Pancake la HTML. Doi <br>, </p>, <li> thanh xuong dong roi bo
	het the, de web hien duoc thanh tung dong tang huong lop vi."""
	s = str(s or "")
	if not s:
		return ""
	s = re.sub(r"(?i)<\s*br\s*/?>", "\n", s)
	s = re.sub(r"(?i)</\s*(p|div|li|tr|h[1-6])\s*>", "\n", s)
	s = re.sub(r"(?i)<\s*li[^>]*>", "\n", s)
	s = re.sub(r"<[^>]+>", " ", s)
	s = (
		s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<")
		.replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
	)
	dong = [re.sub(r"[ \t]+", " ", d).strip() for d in s.split("\n")]
	return "\n".join([d for d in dong if d])


def _mo_ta_san_pham(c, k, sp_id):
	"""Mo ta cua mot SAN PHAM ben Pancake theo id.

	Endpoint bien the chi tra ban rut gon nen phai hoi rieng trang san pham
	moi lay duoc mo ta sales viet.
	"""
	if not sp_id:
		return ""
	try:
		r = _mang().get(
			"%s/shops/%s/products/%s" % (PANCAKE, c.pancake_shop_id, sp_id),
			params={"api_key": k},
			timeout=TIMEOUT,
		)
		d = (r.json() or {})
		d = d.get("data") if isinstance(d.get("data"), dict) else d
		for truong in (
			"description", "note_product", "note", "content", "detail", "summary",
		):
			gt = _sach_html(d.get(truong) or "")
			if gt:
				return gt
	except Exception:
		pass
	return ""


def _sp_pancake(c, k, ma):
	"""Anh + mo ta cua mot ma ben Pancake. Tra {"anhs": [...], "mo_ta": "..."}.

	Trang dat banh co day 5 o anh (anh chinh, can canh, mat cat, chi tiet,
	dong goi) va khoi mo ta - tat ca lay tu danh muc Pancake, sales sua ben
	do la web tu doi, khong phai sua ma. Nho cache nua tieng vi ham nay chay
	trong endpoint khach vang lai goi.
	"""
	ck = "vgb:sp:" + str(ma)
	hit = cache_get(ck)
	if hit is not None:
		try:
			return json.loads(hit) if isinstance(hit, str) else hit
		except Exception:
			pass
	ra = {"anhs": [], "mo_ta": "", "khoa_bt": [], "khoa_sp": []}
	try:
		r = _mang().get(
			"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": ma, "page_size": 5},
			timeout=TIMEOUT,
		)
		for v in (r.json() or {}).get("data") or []:
			if str(v.get("display_id") or "").strip().lower() != str(ma).lower():
				continue
			sp = v.get("product") or {}
			ra["khoa_bt"] = sorted(list(v.keys()))
			ra["khoa_sp"] = sorted(list(sp.keys()))
			for u in (v.get("images") or []) + (sp.get("images") or []):
				u = str(u or "").strip()
				if u and u not in ra["anhs"]:
					ra["anhs"].append(u)
			ra["mo_ta"] = _sach_html(
				sp.get("description")
			or v.get("description")
			or sp.get("note_product")
			or sp.get("note")
			or ""
			)
			# API bien the tra ban RUT GON cua san pham, thuong khong kem mo
			# ta. Chua co mo ta thi hoi thang trang san pham (Minh Vu bao
			# 10/08/2026: sua mo ta ben Pancake ma web khong doi).
			if not ra["mo_ta"]:
				ra["mo_ta"] = _mo_ta_san_pham(c, k, sp.get("id") or v.get("product_id"))
			break
	except Exception:
		return {"anhs": [], "mo_ta": ""}
	ra["anhs"] = ra["anhs"][:5]
	cache_set(ck, json.dumps(ra), CACHE_SP_GIAY)
	return ra


def _anh_pancake(c, k, ma):
	"""Danh sach anh cua mot ma - giu ten cu cho cac cho dang goi."""
	return (_sp_pancake(c, k, ma) or {}).get("anhs") or []


@frappe.whitelist()
def tra_sp_pancake(ma=None, moi=0, soi=0):
	"""Xem Pancake dang giu anh va mo ta gi cho mot ma hang.

	Dung khi trang dat banh hien sai anh hay sai mo ta: goi ham nay ra la
	biet ngay loi o Pancake (sales chua sua) hay o he thong minh. Truyen
	moi=1 de bo qua bo nho dem, hoi thang Pancake.
	"""
	if frappe.session.user == "Guest":
		frappe.throw("Cần đăng nhập.")
	ma = (ma or "").strip()
	if not ma:
		frappe.throw("Thiếu mã hàng.")
	c = cfg()
	k = key(c, "pancake_api_key")
	if not (k and c.pancake_shop_id):
		frappe.throw("Chưa điền khoá Pancake trong Vagabond Settings.")
	if frappe.utils.cint(moi):
		try:
			frappe.cache().delete_value("vgb:sp:" + ma)
		except Exception:
			pass
	sp = _sp_pancake(c, k, ma) or {}
	dong = [d for d in (sp.get("mo_ta") or "").split("\n") if d.strip()]
	return {
		"ma": ma,
		"anhs": sp.get("anhs") or [],
		"mo_ta": dong[0] if dong else "",
		"tang": dong[1:][:12],
		"khoa_bien_the": sp.get("khoa_bt") or [],
		"khoa_san_pham": sp.get("khoa_sp") or [],
		"soi": _soi_pancake(c, k, ma) if frappe.utils.cint(soi) else {},
	}


def _soi_pancake(c, k, ma):
	"""Do het cac truong CHU cua mot ma ben Pancake ra de tim xem mo ta nam o
	dau. Chi dung khi go loi, khong goi trong luong chay thuong."""
	def chu(d, tien):
		ra = {}
		for k2, v2 in (d or {}).items():
			if isinstance(v2, str) and v2.strip():
				ra[tien + k2] = v2.strip()[:400]
		return ra
	ra = {}
	try:
		r = _mang().get(
			"%s/shops/%s/products/variations" % (PANCAKE, c.pancake_shop_id),
			params={"api_key": k, "search": ma, "page_size": 5},
			timeout=TIMEOUT,
		)
		for v in (r.json() or {}).get("data") or []:
			if str(v.get("display_id") or "").strip().lower() != str(ma).lower():
				continue
			sp = v.get("product") or {}
			ra.update(chu(v, "bt."))
			ra.update(chu(sp, "sp."))
			sp_id = sp.get("id") or v.get("product_id")
			ra["_sp_id"] = str(sp_id or "")
			if sp_id:
				r2 = _mang().get(
					"%s/shops/%s/products/%s" % (PANCAKE, c.pancake_shop_id, sp_id),
					params={"api_key": k},
					timeout=TIMEOUT,
				)
				ra["_http"] = str(r2.status_code)
				d2 = (r2.json() or {})
				d2 = d2.get("data") if isinstance(d2.get("data"), dict) else d2
				ra.update(chu(d2, "ep."))
				ra["_khoa_ep"] = ", ".join(sorted(list((d2 or {}).keys())))
			break
	except Exception:
		# Giau khoa: o chan doan nay in thang ra man hinh cho nguoi dung xem.
		ra["_loi"] = _giau_khoa(frappe.get_traceback()[-400:])
	return ra


@frappe.whitelist(allow_guest=True)
def co_the_ban_hom_nay():
	"""Cho trang dat banh order.thevagabondpatisserie.com.

	Truoc 06/08/2026 ham nay chi tra cap ma - so luong, con ten, anh, gia thi
	trang ban hang giu cung trong bien CAKES. Hau qua do that: hom 06/08 tu co
	4 ma con ban (6 banh) nhung web chi hien duoc 1 ma, vi 3 ma kia khong nam
	trong CAKES. Rieng Roman De La Rose trong CAKES con mang ma tu bia
	BAWC00901-903 - ma khong ton tai o dau ca, nen mai mai khong bao gio khop.

	Nay tra ve luon ten - gia - anh, de bat ky ma nao bep them tay o man kiem
	banh (khach bom hang, bep du do) cung tu len web, khong phai sua code.
	"""
	ngay = getdate()
	ma = "KB-%s" % ngay
	rong = {"ngay": str(ngay), "banh": {}, "mon": [], "nhom": [], "dat_truoc": _dat_truoc_theo_decor()}
	if not frappe.db.exists("Kiem Banh Ngay", ma):
		return rong
	doc = frappe.get_doc("Kiem Banh Ngay", ma)
	# Trang nay ban LE. Ma BAWS la banh si, chi bep va sales nam voi nhau
	# ben man kiem banh, khong duoc bay len web (anh Viet 10/08/2026).
	dong = [
		d for d in doc.dong
		if (d.co_the_ban or 0) > 0
		and not str(d.ma_hang or "").upper().startswith("BAWS")
	]
	# Cong tac tay: con ton ma van phai tat, vi mot ly do bat kha khang nao do
	# ma may khong biet duoc (anh Viet 27/08/2026). Loc SAU phep dem chu khong
	# truoc: bang kiem banh van phai hien du so that cho bep va sales, chi rieng
	# WEB la khong bay ma do.
	tat = tat_ban_web.bang([d.ma_hang for d in dong], ngay)
	dong = [d for d in dong if not (tat.get(d.ma_hang) or {}).get("tat")]
	if not dong:
		return rong

	ds = frappe.get_all(
		"Item",
		filters={"item_code": ["in", [d.ma_hang for d in dong]]},
		fields=["item_code", "item_name", "image", "standard_rate"],
		limit_page_length=0,
	)
	it = {x["item_code"]: x for x in ds}

	mon = []
	for d in dong:
		x = it.get(d.ma_hang) or {}
		ten_day = x.get("item_name") or d.ten_banh or d.ma_hang
		goc, cm = _tach_ten_size(ten_day)
		anh = d.hinh or x.get("image") or ""
		if str(anh).startswith("/private"):
			anh = ""
		mon.append(
			{
				"ma": d.ma_hang,
				"ten": goc,
				"ten_day": ten_day,
				"cm": cm,
				"gia": int(x.get("standard_rate") or 0),
				"anh": anh,
				"con": int(d.co_the_ban or 0),
			}
		)

	# Gom cac size cua cung mot banh lai cho web khoi phai tu doan.
	nhom, thu_tu = {}, []
	for m in mon:
		k = m["ten"].lower()
		if k not in nhom:
			nhom[k] = {"ten": m["ten"], "anh": m["anh"], "anhs": [], "sizes": []}
			thu_tu.append(k)
		g = nhom[k]
		if not g["anh"] and m["anh"]:
			g["anh"] = m["anh"]
		g["sizes"].append({"ma": m["ma"], "cm": m["cm"], "gia": m["gia"], "con": m["con"]})
	for k in nhom:
		nhom[k]["sizes"].sort(key=lambda s: (s["cm"] or 999))

	_bo_anh_mo_ta([nhom[k] for k in thu_tu])

	return {
		"ngay": str(ngay),
		"banh": {d.ma_hang: d.co_the_ban for d in dong},
		"mon": mon,
		"nhom": [nhom[k] for k in thu_tu],
		"dat_truoc": _dat_truoc_theo_decor(),
	}


def _bo_anh_mo_ta(ds_nhom):
	"""Bo anh, mo ta va tang huong lop vi cho tung nhom banh, lay tu danh
	muc Pancake theo size nho nhat tro di.

	Mo ta o Pancake nam trong truong note_product: dong dau la gioi thieu,
	cac dong sau la tang huong lop vi. Sales sua ben Pancake la web doi
	theo trong nua tieng (Minh Vu bao 10/08/2026). Dung chung cho ca tab
	banh trong ngay lan tab dat banh truoc - truoc day chi tab trong ngay
	co anh va mo ta, tab dat truoc thi khong.
	"""
	c = cfg()
	khoa = key(c, "pancake_api_key")
	if not (khoa and c.pancake_shop_id):
		return
	for g in ds_nhom or []:
		anhs, mo_ta = [], ""
		for s in g.get("sizes") or []:
			sp = _sp_pancake(c, khoa, s["ma"]) or {}
			for u in sp.get("anhs") or []:
				if u not in anhs:
					anhs.append(u)
			if not mo_ta and (sp.get("mo_ta") or "").strip():
				mo_ta = sp["mo_ta"].strip()
			if len(anhs) >= 5 and mo_ta:
				break
		# Anh dau tien cua Pancake la anh dang dung; anh luu trong dong
		# kiem banh chi de lui ve khi Pancake khong tra gi.
		if not anhs and g.get("anh"):
			anhs = [g["anh"]]
		if anhs:
			g["anh"] = anhs[0]
		g["anhs"] = anhs[:5]
		dong_mo_ta = [d for d in (mo_ta or "").split("\n") if d.strip()]
		g["mo_ta"] = dong_mo_ta[0] if dong_mo_ta else ""
		g["tang"] = [d.strip() for d in dong_mo_ta[1:]][:12]


def _dat_truoc_theo_decor():
	"""Danh muc tab DAT BANH TRUOC cua trang order, lay theo o DU DECOR
	ma bep dien trong /kiem-banh (kho BTP Banh O). Chot voi anh Viet
	07/08/2026: so decor la so banh con nhieu, nhan don duoc cho 3 ngay,
	nen tab dat truoc chi hien dung nhung banh nay kem so luong con nhan.
	"""
	try:
		kho = frappe.get_single("BTP Banh O")
	except Exception:
		return {"cap_nhat_luc": None, "nhom": []}
	# Trang order ban LE: ma BAWS la banh si, khong duoc bay len (anh Viet
	# 10/08/2026).
	dong = [
		b for b in (kho.dong or [])
		if (b.so_decor or 0) > 0
		and not str(b.ma_hang or "").upper().startswith("BAWS")
	]
	if not dong:
		return {"cap_nhat_luc": str(kho.cap_nhat_luc or "") or None, "nhom": []}

	# Tru don DA DAT trong 3 ngay toi (da_dat cua phieu kiem banh ngay mai,
	# mot va hai ngay sau) de so "con nhan" tren web khong nhan lo.
	ngay = getdate()
	da_dat = {}
	for i in (1, 2, 3):
		ma_kb = "KB-%s" % add_days(ngay, i)
		if not frappe.db.exists("Kiem Banh Ngay", ma_kb):
			continue
		for d in frappe.get_doc("Kiem Banh Ngay", ma_kb).dong:
			da_dat[d.ma_hang] = da_dat.get(d.ma_hang, 0) + int(d.da_dat or 0)

	ds = frappe.get_all(
		"Item",
		filters={"item_code": ["in", [b.ma_hang for b in dong]]},
		fields=["item_code", "item_name", "image", "standard_rate"],
		limit_page_length=0,
	)
	it = {x["item_code"]: x for x in ds}

	nhom, thu_tu = {}, []
	for b in dong:
		x = it.get(b.ma_hang)
		if not x:
			# Ma trong kho BTP khong co Item ben Next (vd go nham ma):
			# khong dua len trang khach keo hien nguyen cuc ma va gia 0.
			continue
		con = int(b.so_decor or 0) - int(da_dat.get(b.ma_hang, 0))
		if con <= 0:
			continue
		ten_day = x.get("item_name") or b.ten_banh or b.ma_hang
		goc, cm = _tach_ten_size(ten_day)
		anh = b.hinh or x.get("image") or ""
		if str(anh).startswith("/private"):
			anh = ""
		k = goc.lower()
		if k not in nhom:
			nhom[k] = {"ten": goc, "anh": anh, "sizes": []}
			thu_tu.append(k)
		g = nhom[k]
		if not g["anh"] and anh:
			g["anh"] = anh
		g["sizes"].append(
			{
				"ma": b.ma_hang,
				"cm": cm,
				"gia": int(x.get("standard_rate") or 0),
				"con": con,
			}
		)
	for k in nhom:
		nhom[k]["sizes"].sort(key=lambda s: (s["cm"] or 999))
	ra = [nhom[k] for k in thu_tu]
	_bo_anh_mo_ta(ra)
	return {
		"cap_nhat_luc": str(kho.cap_nhat_luc or "") or None,
		"nhom": ra,
	}


@frappe.whitelist()
def tim_mon(tu_khoa="", ngay=None):
	"""Bang tim mon cho nut "Them ma" - tra ve ma, ten, anh, da co trong bang chua.

	Anh Viet 03/08/2026: nut Them ma dang bat go tay vao window.prompt, sales
	tren dien thoai go nham hoai. Doi thanh bang tim co ten, ma va anh giong
	bang chon mon luc chot doanh thu.
	"""
	q = str(tu_khoa or "").strip()

	# Vi sao viet thang SQL o day thay vi frappe.get_all
	# ---------------------------------------------------
	# Dieu kien that la:  (tien to nam trong danh sach)  VA  (khop tu khoa).
	# Phep "like" cua get_all chi nhan MOT gia tri, con or_filters thi chi co
	# mot nhom OR duy nhat - khong dien duoc mot AND long mot OR. Ghep tay
	# bang chuoi thi ro rang va di dung mot luot hoi.
	#
	# Moi gia tri deu di qua tham so %s, khong noi chuoi vao cau lenh.
	dieu = " OR ".join(["item_code LIKE %s"] * len(TIEN_TO_THEM_TAY))
	tham = ["%s%%" % t for t in TIEN_TO_THEM_TAY]
	cau = """select item_code, item_name, image from `tabItem`
		where ifnull(disabled, 0) = 0 and (%s)""" % dieu
	if q:
		cau += " and (item_code like %s or item_name like %s)"
		tham += ["%" + q + "%", "%" + q + "%"]
	cau += " order by item_code limit 80"
	ds = frappe.db.sql(cau, tuple(tham), as_dict=True)
	da_co = set()
	if ngay:
		ten_bang = "KB-%s" % getdate(ngay)
		if frappe.db.exists("Kiem Banh Ngay", ten_bang):
			da_co = {
				r.ma_hang
				for r in frappe.get_doc("Kiem Banh Ngay", ten_bang).dong
			}
	ra = []
	for it in ds:
		ma = it.get("item_code") or ""
		if not _dang_ma_dung(ma):
			continue
		anh = it.get("image") or ""
		if anh.startswith("/private"):
			anh = ""
		ra.append(
			{
				"ma": ma,
				"ten": it.get("item_name") or "",
				"anh": anh,
				"da_co": 1 if ma in da_co else 0,
			}
		)
	return ra
