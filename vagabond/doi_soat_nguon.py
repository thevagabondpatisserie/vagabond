"""#420: kiểm báo cáo tiền bán trước khi đưa vào hàng đợi đối soát.

File email và tải tay có thể trùng nhau, sai đơn vị tiền hoặc chỉ đọc được
một phần. Không biến lỗi thành số 0 hoặc gọi tổng phần đã đọc là cả báo cáo.
Đây là phần thuần, CHƯA có API, adapter vendor, lưu DB hay ghi nhận tiền về.
Caller tương lai phải lấy phạm vi từ cấu hình đã kiểm quyền ở máy chủ.
"""

# phần thuần
import hashlib
import json
import re
from datetime import date
from decimal import Decimal, localcontext


class LoiNguon(ValueError):
	"""Lỗi dữ liệu phải được giữ cùng dòng để kế toán có thể xử lý lại."""


def doc_tien(gia_tri, dinh_dang):
	"""VND theo schema đã xác nhận: chuan=1234.56, vi=1.234,56, en=1,234.56.

	Không đoán locale hoặc nhân nghìn theo độ lớn. Float bị chặn để adapter
	chủ động đọc số gốc, không đưa sai số nhị phân vào chứng cứ đối soát.
	"""
	if dinh_dang not in ("chuan", "vi", "en"):
		raise LoiNguon("Chưa khai định dạng tiền của nguồn; chọn đúng mẫu báo cáo.")
	if isinstance(gia_tri, bool) or not isinstance(gia_tri, (str, int, Decimal)):
		raise LoiNguon("Tiền không hợp lệ; đọc lại ô gốc, không thay bằng 0.")
	chuoi = str(gia_tri).strip()
	if not chuoi or len(chuoi) > 40:
		raise LoiNguon("Thiếu tiền hoặc tiền quá dài; kiểm tra ô gốc.")
	# Số đã đọc bằng Decimal/int không còn dấu phân nhóm theo locale.
	if not isinstance(gia_tri, str):
		dinh_dang = "chuan"
	mau = {
		"chuan": r"-?[0-9]+(?:\.[0-9]{1,2})?",
		"vi": r"-?(?:[0-9]+|[0-9]{1,3}(?:\.[0-9]{3})+)(?:,[0-9]{1,2})?",
		"en": r"-?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]{1,2})?",
	}[dinh_dang]
	if not re.fullmatch(mau, chuoi):
		raise LoiNguon("Tiền sai định dạng đã khai; kiểm tra dấu nghìn, dấu lẻ và đơn vị nguồn.")
	if dinh_dang == "vi":
		chuoi = chuoi.replace(".", "").replace(",", ".")
	elif dinh_dang == "en":
		chuoi = chuoi.replace(",", "")
	so = Decimal(chuoi)
	if so.copy_abs() > Decimal("999999999999999.99"):
		raise LoiNguon("Tiền vượt giới hạn đọc; kiểm tra đơn vị trên báo cáo gốc.")
	return so


def _chu(du_lieu, ten):
	gia_tri = du_lieu.get(ten)
	if not isinstance(gia_tri, str) or not gia_tri.strip() or len(gia_tri) > 200:
		raise LoiNguon("Thiếu hoặc sai %s; đối chiếu lại nguồn trước khi nhận." % ten)
	return gia_tri.strip()


def _bam(du_lieu):
	return hashlib.sha256(json.dumps(du_lieu, ensure_ascii=False, sort_keys=True,
		separators=(",", ":")).encode("utf-8")).hexdigest()


def _ngay(gia_tri):
	if not isinstance(gia_tri, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", gia_tri):
		raise LoiNguon("Ngày sai; adapter phải trả ngày ISO đã xác minh theo kỳ nguồn.")
	try:
		return date.fromisoformat(gia_tri)
	except ValueError:
		raise LoiNguon("Ngày không tồn tại; kiểm tra báo cáo gốc.") from None


def _pham_vi(nguon):
	pham_vi = {ten: _chu(nguon, ten) for ten in ("cong_ty", "vendor", "merchant", "tien_te")}
	if pham_vi["tien_te"] != "VND":
		raise LoiNguon("Nguồn chưa hỗ trợ tiền tệ này; không tự đổi sang VND.")
	return pham_vi


def chuan_dong(nguon, dong):
	"""Một sự kiện vendor, không phải một Bank Transaction hoặc một hóa đơn.

	ma_su_kien phải là ID ổn định từ adapter (không lấy số thứ tự dòng).
	ID ngắn lặp theo ngày phải được adapter bổ sung phạm vi gốc. Kỳ báo cáo
	và tên file không nằm trong khóa để báo cáo ngày/tháng không cộng hai lần.
	"""
	if not isinstance(dong, dict):
		raise LoiNguon("Dòng không đúng cấu trúc; kiểm lại mẫu báo cáo.")
	pham_vi = _pham_vi(nguon)
	for ten, gia_tri in pham_vi.items():
		if _chu(dong, ten) != gia_tri:
			raise LoiNguon("Dòng khác %s; tách đúng phạm vi, không đoán theo tên file." % ten)
	ngay = _ngay(dong.get("ngay"))
	if not _ngay(nguon.get("tu_ngay")) <= ngay <= _ngay(nguon.get("den_ngay")):
		raise LoiNguon("Dòng ngoài kỳ báo cáo; kiểm tra ngày và loại kỳ.")
	loai = _chu(dong, "loai")
	if loai not in ("ban", "hoan", "dieu_chinh"):
		raise LoiNguon("Chưa hỗ trợ loại sự kiện này; giữ dòng để kiểm lại.")
	ma = _chu(dong, "ma_su_kien")
	tien = {ten: doc_tien(dong.get(ten), nguon.get("dinh_dang"))
		for ten in ("tien_hang", "phi", "dieu_chinh", "thuc_nhan")}
	with localcontext() as canh:
		canh.prec = 40
		if tien["tien_hang"] - tien["phi"] + tien["dieu_chinh"] != tien["thuc_nhan"]:
			raise LoiNguon("Tiền hàng trừ phí cộng điều chỉnh không bằng thực nhận; kiểm lại dòng.")
	if (loai == "ban" and tien["tien_hang"] < 0) or (loai == "hoan" and tien["tien_hang"] > 0):
		raise LoiNguon("Dấu tiền không khớp bán/hoàn; kiểm loại sự kiện gốc.")
	ma_don = _chu(dong, "ma_don")
	ra = dict(pham_vi, ma_su_kien=ma, ma_don=ma_don, loai=loai, ngay=ngay.isoformat())
	# Chuẩn 2 chữ số để 100 và 100.00 có cùng dấu vết nội dung.
	ra.update({ten: format(so, ".2f") if so else "0.00" for ten, so in tien.items()})
	ra["khoa"] = _bam(dict(pham_vi, ma_su_kien=ma))
	ra["dau_noi_dung"] = _bam(ra)
	return ra


def xem_truoc(nguon, cac_dong, da_nhan=None):
	"""Trả kết quả mọi dòng; không sửa input, không nhận/ghi/chốt chứng từ.

	da_nhan là snapshot {khóa: dấu nội dung} do máy chủ đọc. Chỉ dùng xem
	trước; chưa phải khóa DB chống hai worker cùng nhận. Dòng sửa lại cùng ID
	được giữ Cần xem thay vì âm thầm ghi đè. Dòng trùng vẫn tính vào tổng nguồn
	để tổng file đã nhận một phần có thể kiểm lại được.
	"""
	_pham_vi(nguon)
	if _ngay(nguon.get("tu_ngay")) > _ngay(nguon.get("den_ngay")):
		raise LoiNguon("Kỳ bị đảo ngày; kiểm lại ngày đầu và cuối báo cáo.")
	if not isinstance(cac_dong, list) or len(cac_dong) > 10000:
		raise LoiNguon("Mỗi lượt tối đa 10.000 dòng; chia đúng báo cáo trước khi nhận.")
	so_dong = nguon.get("so_dong")
	if type(so_dong) is not int or not 0 <= so_dong <= 10000:
		raise LoiNguon("Chưa có số dòng nguồn đã kiểm; không tự chốt đủ báo cáo.")
	tong_nguon = doc_tien(nguon.get("tong_thuc_nhan"), nguon.get("dinh_dang"))
	ket_qua, trong_file = [], {}
	da_nhan = dict(da_nhan or {})
	dem = {"moi": 0, "trung": 0, "loi": 0}
	tong = Decimal(0)
	with localcontext() as canh:
		canh.prec = 40
		for vi_tri, dong in enumerate(cac_dong, 1):
			chuan = None
			try:
				dong = chuan_dong(nguon, dong)
				chuan = dong
				tong += Decimal(dong["thuc_nhan"])
				khoa, dau = dong["khoa"], dong["dau_noi_dung"]
				if khoa in trong_file:
					# Không để bản đầu còn mang nhãn Mới khi cùng ID có hai
					# dòng. Người dùng nhận phần hợp lệ sẽ vô tình chọn nó.
					cu = ket_qua[trong_file[khoa]]
					cu.update(trang_thai="loi", ly_do="Sự kiện có nhiều dòng trong báo cáo; kiểm cả nhóm.")
					raise LoiNguon("Một sự kiện lặp trong cùng báo cáo; kiểm dòng gốc trước khi nhận.")
				trong_file[khoa] = len(ket_qua)
				if khoa in da_nhan and da_nhan[khoa] != dau:
					raise LoiNguon("Sự kiện đã nhận có nội dung khác; cần đối chiếu bản điều chỉnh.")
				trang_thai = "trung" if khoa in da_nhan else "moi"
				ket_qua.append(dict(vi_tri=vi_tri, trang_thai=trang_thai, dong=dong))
			except LoiNguon as loi:
				trang_thai = "loi"
				ra = dict(vi_tri=vi_tri, trang_thai=trang_thai, ly_do=str(loi))
				if chuan is not None:
					ra["dong"] = chuan
				ket_qua.append(ra)
	for dong in ket_qua:
		dem[dong["trang_thai"]] += 1
	loi_nguon = []
	if not cac_dong:
		loi_nguon.append("Báo cáo chưa có dòng; giữ nguồn chờ kiểm tra.")
	if so_dong != len(cac_dong):
		loi_nguon.append("Số dòng đã đọc khác số dòng nguồn; chưa được khép báo cáo.")
	if dem["loi"]:
		loi_nguon.append("Còn dòng cần xử lý; tổng đọc được chưa chứng minh toàn báo cáo.")
	if tong != tong_nguon:
		loi_nguon.append("Tổng thực nhận đã đọc khác tổng nguồn; kiểm đơn vị và dòng còn thiếu.")
	return dict(dong=ket_qua, dem=dem, tong_doc_duoc=format(tong, ".2f"),
		tong_nguon=format(tong_nguon, ".2f"), loi_nguon=loi_nguon,
		du_nguon=not loi_nguon)
