"""Ca kiểm nội dung chuyển khoản của phiếu hoàn tiền, và luồng khớp SePay.

Mọi ca ở đây chạy trên phép THUẦN, không cần Frappe, không cần site, không
cần mạng.

VÌ SAO TỆP NÀY RA ĐỜI (anh Việt 24/08/2026)
--------------------------------------------
*"Phiếu hoàn tiền đã thống nhất là hoàn theo đơn huỷ thì nội dung sẽ hoàn
theo mã đơn Pancake, nhưng ở nội dung chuyển khoản của phiếu thì không thấy
để mã đơn. Bên ngoài có mã, mà bên trong thì không có mã."*

Nguyên nhân không phải quên ghi mã, mà là một câu SỬA CHỮA đặt quá rộng. Câu
đó sinh ra để đổi cú pháp cũ "HT <mã tờ trả hàng>" của trước 16/08/2026 sang
mã hoá đơn gốc, nhưng nó không hỏi phiếu có hoá đơn hay không:

    if not da_doi_soat and not khop_giao_dich(nd, hoa_don):
            nd = noi_dung_ck(hoa_don)

Phiếu hoàn của đơn Pancake đã huỷ KHÔNG có hoá đơn nào, nên `khop_giao_dich`
trả False ngay dòng đầu, điều kiện thành thật, và máy ghi đè chuỗi đúng bằng
một chuỗi cụt rồi ghi luôn xuống cơ sở dữ liệu.

Hỏng này không dừng ở chỗ mất một dòng chữ: chuỗi nội dung chính là thứ DUY
NHẤT `ma_do_soat` đem dò trên sao kê cho phiếu Pancake, nên phiếu bị xoá mã
thì không bao giờ tự khớp được nữa.
"""

from vagabond import hoan_tien as ht
from vagabond.khung.kiem_thu.nen import ca, dung, la

# Chuoi dung phai cua mot phieu hoan don Pancake 92156, y het chuoi
# don_huy.noi_dung_chuyen_khoan sinh ra luc lap phieu.
ND_PANCAKE = "THE VAGABOND HOAN TIEN 92156"


@ca("hoàn tiền: phiếu đơn Pancake giữ nguyên mã đơn, KHÔNG bị xoá cụt")
def _():
	ra = ht.noi_dung_dung(
		ht.LOAI_HUY_PANCAKE, "", ND_PANCAKE, 0, noi_dung_pancake=ND_PANCAKE)
	la("giữ nguyên chuỗi mang mã đơn", ra, ND_PANCAKE)
	dung("chuỗi trả về có mã đơn", "92156" in ra)


@ca("hoàn tiền: HÀNG RÀO có cắn không - dựng lại đúng lỗi cũ")
def _():
	"""Hàng rào không cắn còn tệ hơn không có hàng rào.

	Ca này chạy lại chính câu sửa chữa cũ trên đúng dữ liệu đã làm nó hỏng,
	rồi đòi bản mới phải cho kết quả khác.
	"""
	# Phep cu: `noi_dung_ck(hoa_don)` voi hoa_don rong.
	cu = ht.noi_dung_ck("")
	# Con thua ca mot dau cach o cuoi, vi ham ghep "%s %s" voi ve sau rong.
	# Ghi dung chuoi that chu khong lam tron, de ai doc ca kiem nay cung thay
	# ngay thu da bi ghi xuong co so du lieu la mot chuoi nhu the nao.
	la("phép cũ cho ra chuỗi cụt", cu, "THE VAGABOND HOAN TIEN ")
	dung("phép cũ MẤT mã đơn", "92156" not in cu)
	# Phep moi tren cung dau vao.
	moi = ht.noi_dung_dung(
		ht.LOAI_HUY_PANCAKE, "", ND_PANCAKE, 0, noi_dung_pancake=ND_PANCAKE)
	dung("phép mới GIỮ mã đơn", "92156" in moi)
	dung("hai phép cho kết quả khác nhau", cu != moi)


@ca("hoàn tiền: phiếu Pancake đã bị xoá mã thì được dựng lại từ đơn huỷ")
def _():
	"""Phiếu đã trót mở ra một lần trước v292 thì trong ô chỉ còn chuỗi cụt.

	Dựng lại được là vì mã đơn còn nguyên ở ô `ma_don_pancake` và ở bản ghi
	Đơn đã huỷ, hai nơi câu sửa chữa cũ không đụng tới.
	"""
	ra = ht.noi_dung_dung(
		ht.LOAI_HUY_PANCAKE, "", "THE VAGABOND HOAN TIEN", 0,
		noi_dung_pancake=ND_PANCAKE)
	la("dựng lại đúng chuỗi ban đầu", ra, ND_PANCAKE)


@ca("hoàn tiền: không dựng lại được thì GIỮ NGUYÊN, không bịa chuỗi mới")
def _():
	"""Đơn huỷ đã bị xoá khỏi hệ thì `_noi_dung_pancake` trả về rỗng.

	Lúc đó thà giữ chuỗi cụt còn hơn ghi đè bằng chuỗi cụt LẦN NỮA, và tuyệt
	đối không được bịa ra một mã đơn nào.
	"""
	ra = ht.noi_dung_dung(ht.LOAI_HUY_PANCAKE, "", ND_PANCAKE, 0, noi_dung_pancake="")
	la("giữ nguyên chuỗi đang có", ra, ND_PANCAKE)
	ra2 = ht.noi_dung_dung(ht.LOAI_HUY_PANCAKE, "", "", 0, noi_dung_pancake="")
	la("rỗng vào thì rỗng ra, không bịa", ra2, "")


@ca("hoàn tiền: phiếu ĐÃ ĐỐI SOÁT thì không ai được sửa nội dung nữa")
def _():
	"""Chuỗi trên phiếu đã đối soát là thứ kế toán đã gõ vào ngân hàng thật.

	Sửa nó là sửa lại quá khứ. Anh Việt chốt 13/08/2026: phát hiện sai sót
	trong dữ liệu cũ thì liệt kê ra, không tự sửa.
	"""
	la("phiếu Pancake đã đối soát giữ nguyên",
		ht.noi_dung_dung(ht.LOAI_HUY_PANCAKE, "", "NOI DUNG KE TOAN DA GO", 1,
			noi_dung_pancake=ND_PANCAKE),
		"NOI DUNG KE TOAN DA GO")
	la("phiếu trả hàng đã đối soát cũng giữ nguyên",
		ht.noi_dung_dung("Tra hang", "HDB-2026-01593", "HT HDB-26-08-00341", 1),
		"HT HDB-26-08-00341")


@ca("hoàn tiền: câu sửa chữa cũ vẫn phải chạy đúng cho phiếu CÓ hoá đơn")
def _():
	"""Sửa cái sai không được làm mất cái đúng.

	Phiếu lập trước 16/08/2026 mang cú pháp "HT <mã tờ trả hàng>", và đường
	đối soát mới dò theo mã hoá đơn gốc, nên chuỗi cũ phải được đổi.
	"""
	la("cú pháp cũ được đổi sang mã hoá đơn gốc",
		ht.noi_dung_dung("Tra hang", "HDB-2026-01593", "HT HDB-26-08-00341", 0),
		"THE VAGABOND HOAN TIEN HDB-2026-01593")
	la("chuỗi đã đúng thì không đụng vào",
		ht.noi_dung_dung("Tra hang", "HDB-2026-01593",
			"THE VAGABOND HOAN TIEN HDB-2026-01593", 0),
		"THE VAGABOND HOAN TIEN HDB-2026-01593")
	# Ngan hang lam mat dau gach thi van phai coi la khop, khong duoc ghi de.
	la("ngân hàng làm mất dấu gạch vẫn coi là khớp",
		ht.noi_dung_dung("Tra hang", "HDB-2026-01593",
			"THE VAGABOND HOAN TIEN HDB 2026 01593", 0),
		"THE VAGABOND HOAN TIEN HDB 2026 01593")


@ca("hoàn tiền: phiếu KHÔNG hoá đơn và KHÔNG phải Pancake thì để yên")
def _():
	"""Không có gì để dò thì cũng không có gì để sửa.

	Trước v292 chính nhóm này bị ghi đè thành chuỗi cụt, y như nhóm Pancake.
	"""
	la("giữ nguyên", ht.noi_dung_dung("Tien nop thua", "", "MOT CHUOI NAO DO", 0),
		"MOT CHUOI NAO DO")


@ca("hoàn tiền: mã dò của phiếu Pancake là CẢ CÂU, không phải mã đơn trần")
def _():
	"""Mã đơn Pancake chỉ năm chữ số nên dò trần là dính nhầm.

	`khop_giao_dich` chặn chữ số ở phía SAU chứ không chặn phía trước, nên dò
	"92252" sẽ ăn vào một dòng chứa "192252".
	"""
	ho_so = {"hoa_don": "", "loai_hoan": ht.LOAI_HUY_PANCAKE,
		"noi_dung_ck": "THE VAGABOND HOAN TIEN 92252"}
	la("dò theo cả câu", ht.ma_do_soat(ho_so), "THE VAGABOND HOAN TIEN 92252")
	dung("cả câu KHÔNG dính vào dòng chứa 192252",
		not ht.khop_giao_dich("CHUYEN KHOAN 192252 ABC", ht.ma_do_soat(ho_so)))
	# Chung minh cai bay la that chu khong phai lo lang suong: ma tran DINH
	# vao dong 192252. Bo dong nay di thi khong ai biet vi sao phai do ca cau.
	dung("mã trần thì DÍNH nhầm vào 192252 - đây là lý do phải dò cả câu",
		ht.khop_giao_dich("CHUYEN KHOAN 192252 ABC", "92252"))
	dung("dòng đúng thì vẫn khớp",
		ht.khop_giao_dich("MB THE VAGABOND HOAN TIEN 92252 REF9", ht.ma_do_soat(ho_so)))


@ca("hoàn tiền: phiếu Pancake mất nội dung thì KHÔNG dò được, phải bỏ qua")
def _():
	"""Đây là hậu quả thật của lỗi cũ, ghi lại để không ai coi nhẹ nó.

	`doi_soat` lọc bỏ mọi hồ sơ không dò được. Phiếu bị xoá mã rơi vào đúng
	nhóm đó, nên nó nằm mãi ở "Chờ chi" mà không dòng nhật ký nào giải thích.
	"""
	mat_ma = {"hoa_don": "", "loai_hoan": ht.LOAI_HUY_PANCAKE,
		"noi_dung_ck": ""}
	la("không dò được", ht.ma_do_soat(mat_ma), "")
	con_ma = {"hoa_don": "", "loai_hoan": ht.LOAI_HUY_PANCAKE,
		"noi_dung_ck": ND_PANCAKE}
	la("còn mã thì dò được", ht.ma_do_soat(con_ma), ND_PANCAKE)
