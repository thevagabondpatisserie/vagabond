"""Đọc CSV/TAB để xem nguồn; chưa ánh xạ tiền, ghi sổ hoặc xác nhận đủ báo cáo.

Giữ nguyên chữ, số 0 đầu mã và tọa độ dòng. Encoding/dấu phân cách phải do
mẫu nguồn xác định, không suy luận đơn vị tiền từ tên file hoặc độ lớn.
"""
import csv
import hashlib
import io

from vagabond.doi_soat_nguon import LoiNguon


def doc_bang(noi_dung, *, encoding, dau, dong_tieu_de=1):
	"""Nhận bytes, trả bảng chữ và dấu vết; lỗi cấu trúc giữ cả nguồn chờ.

	dong_tieu_de là số dòng vật lý bắt đầu header (có thể có preamble).
	Giới hạn 8 MiB, 10.000 bản ghi sau header, 100 cột, 20.000 ký tự/ô.
	Ô công thức chỉ là chữ: caller không được đưa vào Excel dưới dạng formula.
	"""
	if not isinstance(noi_dung, bytes) or not noi_dung or len(noi_dung) > 8 * 1024 * 1024:
		raise LoiNguon("File trống hoặc quá 8 MiB; chia theo kỳ báo cáo.")
	if encoding not in ("utf-8-sig", "utf-16") or dau not in (",", "\t", ";"):
		raise LoiNguon("Chọn encoding và dấu phân cách theo mẫu nguồn đã kiểm.")
	if type(dong_tieu_de) is not int or not 1 <= dong_tieu_de <= 100:
		raise LoiNguon("Dòng tiêu đề phải từ 1 đến 100.")
	try:
		chu = noi_dung.decode(encoding, errors="strict")
	except UnicodeError:
		raise LoiNguon("Không đọc được encoding đã chọn; giữ file gốc để kiểm.") from None
	if "\x00" in chu:
		raise LoiNguon("File có ký tự NUL; kiểm lại định dạng và encoding.")
	reader = csv.reader(io.StringIO(chu, newline=""), delimiter=dau, strict=True)
	cot, dong, truoc = None, [], 0
	try:
		for hang in reader:
			# line_num là cuối bản ghi CSV, không phải STT nghiệp vụ.
			cuoi = reader.line_num
			dau_dong = truoc + 1
			truoc = cuoi
			if dau_dong < dong_tieu_de:
				if cuoi >= dong_tieu_de:
					raise LoiNguon("Dòng tiêu đề nằm giữa một ô nhiều dòng.")
				continue
			if len(hang) > 100 or any(len(o) > 20000 for o in hang):
				raise LoiNguon("Nguồn vượt giới hạn cột hoặc độ dài ô.")
			if cot is None:
				# Lưu theo vị trí, không dùng dict tên cột: mẫu có cột
				# rỗng/trùng vẫn giữ đủ ô cho adapter xác minh schema.
				cot = [o.strip() for o in hang]
				if not cot or not any(cot):
					raise LoiNguon("Cả hàng tiêu đề trống; chọn lại dòng tiêu đề.")
				continue
			if not hang or all(not o.strip() for o in hang):
				# Dòng trống cũng giữ để adapter phân loại; không coi đã đủ nguồn.
				dong.append(dict(dong_dau=dau_dong, dong_cuoi=cuoi, o=hang, trong=True))
			else:
				if len(hang) != len(cot):
					raise LoiNguon("Dòng %s có %s cột, cần %s; không đọc bỏ phần lệch." % (dau_dong, len(hang), len(cot)))
				dong.append(dict(dong_dau=dau_dong, dong_cuoi=cuoi, o=hang, trong=False))
			if len(dong) > 10000:
				raise LoiNguon("Nguồn quá 10.000 bản ghi; chia đúng kỳ.")
	except csv.Error:
		raise LoiNguon("CSV/TAB lỗi cấu trúc; giữ file gốc, không nhận phần đã đọc.") from None
	if cot is None:
		raise LoiNguon("Không tìm thấy tiêu đề tại dòng đã chọn.")
	return dict(sha256=hashlib.sha256(noi_dung).hexdigest(), cot=cot, dong=dong,
		encoding=encoding, dau=dau, parser="bang-chu-2", du_nguon=False)
