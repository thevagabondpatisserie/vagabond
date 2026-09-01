# -*- coding: utf-8 -*-
"""Kiem thu: cong tai tep dung chung cho moi man.

Anh Viet 01/09/2026, khi xem man De nghi chi tren dien thoai: *"bi thieu
phan tai len tep dinh kem de tai hinh anh cua chung tu di kem va hang hoa da
mua (cho dinh kem nhieu file, hien dang thumbnail, tu nen file nho de do ton
database,...) nhung cai nay la cai em phai ghi vao backend moi khi dung man
nao co nut tai tep len"*.

MOT LOI NANG PHAT HIEN CUNG LUC

Man De nghi chi tren app CHUA BAO GIO gui duyet duoc. `gui_duyet` chan phieu
khong co tep dinh kem, con man app thi khong co cho nao dinh tep. Nut "Lap va
gui duyet" vi the luon nem loi, kem theo cau chi duong toi nut dinh kem tren
Desk - ma nguoi lap phieu la ban bep cam dien thoai, ca doi khong mo Desk.

Hang rao `bat_buoc_tep` tren danh muc Loai chung tu cung nam do tu dau, va
cung chua bao gio bat duoc gi, vi co `_co_tep` truoc nay dem CHUNG ca phieu.

BO CA KIEM NAY CHOT NAM DIEU

1. Duoi tep: chi nhan anh va PDF, doc duoc dung ten va dung nhan.
2. Doc va ghi danh sach tep: sai kieu du lieu la mat sach tep mot dong.
3. Dau nhan mat tep, hang rao cuoi cung giua nhip don rac va chu ky khach.
4. `gui_duyet` dem tep THEO TUNG DONG, khong dem chung ca phieu nua.
5. Man hinh khong duoc chep lai doan nen anh, phai goi cong chung.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond import tep_dinh_kem as td

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
	os.path.abspath(__file__)))))


def _doc(*duong):
	p = os.path.join(GOI, *duong)
	return io.open(p, encoding="utf-8").read() if os.path.exists(p) else ""


# ------------------------------------------------------------- 1. duoi tep

@ca("Tệp đính kèm: đọc đuôi tệp và nhãn hiển thị")
def _duoi():
	la("ảnh thường", td.duoi_tep("bill.JPG"), ".jpg")
	la("ảnh iPhone", td.duoi_tep("IMG_1234.HEIC"), ".heic")
	la("tệp PDF", td.duoi_tep("hoa-don.pdf"), ".pdf")
	la("tên có nhiều dấu chấm", td.duoi_tep("hoa.don.thang.8.pdf"), ".pdf")
	la("không có đuôi", td.duoi_tep("bill"), "")
	# Đuôi dài quá năm chữ gần như chắc chắn không phải đuôi mà là một dấu
	# chấm nằm giữa tên. Đoán bừa ở đây là vẽ ra một ô vuông mang chữ vô nghĩa.
	la("dấu chấm giữa tên", td.duoi_tep("cong ty A.chi nhanh 3"), "")
	dung("jpg là ảnh", td.la_anh("a.jpg"))
	dung("pdf KHÔNG phải ảnh", not td.la_anh("a.pdf"))
	la("nhãn của pdf", td.nhan_duoi("a.pdf"), "PDF")
	la("nhãn khi không rõ", td.nhan_duoi("a"), "TỆP")


@ca("Tệp đính kèm: chỉ nhận ảnh và PDF, và có trần dung lượng")
def _nhan():
	la("ảnh thì nhận", td.loi_tu_choi("bill.jpg"), "")
	la("pdf thì nhận", td.loi_tu_choi("hd.pdf"), "")
	dung("video thì từ chối", "không nhận được" in td.loi_tu_choi("clip.mov"))
	dung("tệp nén thì từ chối", "không nhận được" in td.loi_tu_choi("goi.zip"))
	dung("tệp chạy thì từ chối", "không nhận được" in td.loi_tu_choi("x.exe"))
	dung("không tên thì từ chối", td.loi_tu_choi("") != "")
	# Câu từ chối phải NÓI RA nhận những gì. Người cầm điện thoại không đoán
	# được mình sai chỗ nào nếu chỉ đọc "tệp không hợp lệ".
	dung("câu từ chối chỉ ra loại nhận được", "PDF" in td.loi_tu_choi("clip.mov"))
	la("dưới trần thì nhận", td.loi_tu_choi("a.jpg", 1000), "")
	dung("quá trần thì từ chối", "quá mức" in td.loi_tu_choi("a.jpg", td.CAP_MOT_TEP + 1))


# ----------------------------------------------- 2. doc va ghi danh sach tep

@ca("Tệp đính kèm: đọc danh sách tệp từ ô, mọi kiểu dữ liệu đều không vỡ")
def _doc_ds():
	la("ô trống", td.doc_ds(None), [])
	la("chuỗi rỗng", td.doc_ds(""), [])
	la("chuỗi JSON", td.doc_ds('["/files/a.jpg","/files/b.pdf"]'),
	   ["/files/a.jpg", "/files/b.pdf"])
	la("danh sách thật", td.doc_ds(["/files/a.jpg"]), ["/files/a.jpg"])
	la("danh sách các ô", td.doc_ds([{"url": "/files/a.jpg"}]), ["/files/a.jpg"])
	# Chuỗi hỏng thì trả rỗng chứ KHÔNG nổ. Một dòng hỏng không được làm chết
	# cả phiếu, vì phiếu còn chứa tiền.
	la("chuỗi hỏng", td.doc_ds("{khong phai json"), [])
	la("không phải danh sách", td.doc_ds('{"a":1}'), [])
	la("bỏ trùng", td.doc_ds('["/a.jpg","/a.jpg","/b.jpg"]'), ["/a.jpg", "/b.jpg"])


@ca("Tệp đính kèm: ghi danh sách xuống ô, rỗng thì để ô trống")
def _ghi_ds():
	la("rỗng thì None", td.ghi_ds([]), None)
	la("toàn chuỗi trắng cũng là None", td.ghi_ds(["", "  "]), None)
	la("đọc lại được đúng cái vừa ghi",
	   td.doc_ds(td.ghi_ds(["/a.jpg", "/b.pdf"])), ["/a.jpg", "/b.pdf"])
	la("ghi rồi đọc thì hết trùng",
	   td.doc_ds(td.ghi_ds(["/a.jpg", "/a.jpg"])), ["/a.jpg"])


# --------------------------------------------------------- 3. dau nhan mat

@ca("Tệp đính kèm: dấu nhận mặt tệp, hàng rào cuối của nhịp dọn rác")
def _dau():
	t = td.ten_luu("Hoá đơn tháng 8.pdf", "dnc-k1")
	dung("có dấu nhận mặt", t.startswith(td.DAU_TEP + "-"))
	dung("giữ đúng đuôi gốc", t.endswith(".pdf"))
	dung("bỏ hết dấu tiếng Việt và khoảng trắng",
	     all(c.isalnum() or c in "-." for c in t))
	dung("tệp của cổng thì nhận ra", td.la_tep_cua_cong(t))
	dung("nhận ra cả khi có đường dẫn", td.la_tep_cua_cong("/private/files/" + t))
	# Ba thứ dưới đây KHÔNG do cổng này sinh ra. Nhịp dọn rác chạm vào một
	# trong ba là mất chứng cứ giao nhận. Xem thu_don_rac_tep.py.
	dung("chữ ký khách thì không", not td.la_tep_cua_cong("chu-ky-VD-2026-001.png"))
	dung("uỷ nhiệm chi thì không", not td.la_tep_cua_cong("unc-PE-00123.pdf"))
	dung("tệp Frappe tự sinh thì không", not td.la_tep_cua_cong("a1b2c3.jpg"))
	# Tên rỗng cũng phải trả về False. Trả True là nhịp dọn rác được phép
	# đụng vào một dòng File không rõ lai lịch.
	dung("tên rỗng thì không", not td.la_tep_cua_cong(""))
	dung("tên None thì không", not td.la_tep_cua_cong(None))


@ca("Tệp đính kèm: gom dữ liệu cho màn hình vẽ hình thu nhỏ")
def _gom():
	r = td.gom_hien('["/files/a.jpg","/files/b.pdf"]',
	                {"/files/a.jpg": "bill quầy.jpg", "/files/b.pdf": "hoa-don.pdf"})
	la("đủ hai ô", len(r), 2)
	la("ảnh mang cờ ảnh", r[0]["anh"], 1)
	la("ảnh giữ tên thật", r[0]["ten"], "bill quầy.jpg")
	la("pdf không mang cờ ảnh", r[1]["anh"], 0)
	la("pdf mang nhãn đuôi", r[1]["duoi"], "PDF")
	# Không tra được tên thì lấy tên trong đường dẫn, KHÔNG bịa một cái tên
	# nghe cho xuôi. Bài học nút "Tải uỷ nhiệm chi" ngày 31/08/2026.
	r2 = td.gom_hien('["/files/x.png"]')
	la("không tra được thì lấy tên trong đường dẫn", r2[0]["ten"], "x.png")


# ------------------------------------------------- 4. de_nghi_chi dem theo dong

@ca("Đề nghị chi: đếm tệp THEO TỪNG DÒNG, không đếm chung cả phiếu")
def _theo_dong():
	m = _doc("vagabond", "de_nghi_chi.py")
	i = m.find("def gui_duyet(")
	than = m[i:m.find("\n@frappe.whitelist()", i)]
	dung("đọc tệp riêng của dòng", 'tep_dinh_kem.doc_ds(d.get("tep"))' in than)
	dung("dòng có tệp riêng thì tính tệp của nó", "bool(rieng) or co_tep_phieu" in than)
	# Câu chặn cuối cũng phải nhìn cả tệp theo dòng, nếu không thì phiếu đính
	# đủ tệp ở từng khoản vẫn bị chặn vì cấp phiếu trống.
	dung("câu chặn cuối nhìn cả hai nơi", "co_tep_phieu or any(" in than)
	# Và câu nhắc phải chỉ đúng chỗ bấm trên app, không chỉ sang Desk.
	dung("không còn chỉ đường sang Desk", "nút đính kèm ở góc phải" not in m)
	dung("chỉ đúng ô trên app", "ô đính kèm nằm ngay trong từng khoản chi" in than)


@ca("Đề nghị chi: tệp đi qua đúng một cổng, không tự sửa bảng File")
def _mot_cong():
	m = _doc("vagabond", "de_nghi_chi.py")
	i = m.find("def tao(")
	than = m[i:m.find("\ndef _ds_chung_tu(", i)]
	dung("lưu tệp của từng khoản", '"tep": tep_dinh_kem.ghi_ds(' in than)
	dung("buộc tệp qua cổng chung", "tep_dinh_kem.gan_vao(DT, doc.name, O_TEP" in than)
	# Buộc tệp phải làm SAU khi phiếu có mã. Làm trước thì không có gì để buộc.
	dung("buộc sau khi phiếu đã lưu",
	     than.find("doc.insert(") < than.find("tep_dinh_kem.gan_vao("))
	# Không nơi nào ngoài cổng được tự đặt attached_to_*. Mỗi nơi tự đặt là
	# mỗi nơi tự có một bộ luật, mà chỉ cần một bộ sai là mất tệp.
	dung("không tự đặt attached_to trong de_nghi_chi",
	     "attached_to_doctype\":" not in than)


@ca("Tệp đính kèm: cổng ra ngoài đúng ba cửa, hai hàm nguy hiểm phải kín")
def _cua():
	m = _doc("vagabond", "tep_dinh_kem.py")
	# gan_vao buộc tệp vào chứng từ. Mở ra ngoài là cho bất kỳ ai buộc tệp
	# bất kỳ vào chứng từ bất kỳ.
	i = m.find("def gan_vao(")
	dung("gan_vao KHÔNG mở ra ngoài",
	     "@frappe.whitelist()" not in m[max(0, i - 120):i])
	# don_rac xoá tệp thật. Mở ra ngoài là cho gọi một nhịp xoá từ trình duyệt.
	j = m.find("def don_rac(")
	dung("don_rac KHÔNG mở ra ngoài",
	     "@frappe.whitelist()" not in m[max(0, j - 120):j])
	dung("nhịp đêm có khai trong hooks",
	     "vagabond.tep_dinh_kem.don_rac" in _doc("vagabond", "hooks.py"))


@ca("Tệp đính kèm: nhịp dọn rác hỏi đủ ba câu trước khi xoá")
def _don_rac_ba_cau():
	m = _doc("vagabond", "tep_dinh_kem.py")
	i = m.find("def don_rac(")
	than = m[i:]
	dung("câu 1 và 2: chưa thuộc chứng từ nào, chưa ở ô nào",
	     '"attached_to_doctype": ["in", ["", None]]' in than
	     and '"attached_to_name": ["in", ["", None]]' in than)
	dung("câu 3: không còn dòng File nào khác cùng đường dẫn",
	     'frappe.db.count("File", {"file_url": r.file_url}) > 1' in than)
	dung("chỉ đụng tệp mang dấu của cổng", "la_tep_cua_cong(r.file_name)" in than)


# ------------------------------------------------------------ 5. man hinh

@ca("Màn hình: ô tải tệp dùng chung, không màn nào chép lại phép nén")
def _man_chung():
	js = _doc("vagabond", "public", "js", "bep", "43-tep-dinh-kem.js")
	for ten in ("function tdkKhoi(", "function tdkNoi(", "function tdkDs(",
	            "function tdkNen(", "function tdkNap(", "function tdkXoaHet("):
		dung("có " + ten, ten in js)
	# Ảnh iPhone chụp dọc mang cờ xoay trong EXIF. Vẽ thẳng lên canvas là mất
	# cờ đó và tấm ảnh nằm ngang, kế toán soi chứng từ phải nghiêng đầu.
	dung("xoay ảnh về đúng chiều", "imageOrientation: 'from-image'" in js)
	dung("máy cũ vẫn có đường đi", "function tdkVeThuong(" in js)
	# Nén PDF bằng canvas là biến nó thành ảnh, mất chữ.
	dung("PDF thì không đụng tới", "if (!tdkLaAnh(f.name)) return xong(f, f.name);" in js)
	dung("gửi từng tệp một", "for (var j = 0; j < cac.length; j++)" in js)


@ca("Màn Đề nghị chi: mỗi khoản chi một ô tệp riêng")
def _man_dnc():
	js = _doc("vagabond", "public", "js", "bep", "16-mua-hang.js")
	dung("ô tệp lấy mã theo id của khoản", "function dncOTep(k)" in js)
	dung("vẽ ô tệp trong thẻ khoản chi", "tdkKhoi(dncOTep(k)" in js)
	dung("nối sự kiện cho từng khoản", "tdkNoi(b, dncOTep(k)" in js)
	dung("gom tệp về form khi lưu", "k.tep = tdkDs(dncOTep(k));" in js)
	# Lập xong một phiếu phải dọn kho tệp. Giữ lại thì phiếu sau mở ra đã
	# thấy sẵn ảnh của phiếu trước, mà ảnh đó đã thuộc phiếu trước rồi.
	dung("lập xong thì dọn kho tệp", "tdkXoaHet();" in js)
	# Cờ bắt buộc tệp phải chặn NGAY trên màn, không đợi máy chủ: máy chủ chặn
	# sau khi phiếu đã lưu, nên mỗi lần quên ảnh là đẻ ra một phiếu nháp thừa.
	dung("màn tự chặn khi thiếu tệp bắt buộc",
	     "loại chứng từ này bắt buộc đính kèm tệp" in js)
	dung("gửi duyệt mà chưa có ảnh nào thì chặn", "Chưa có chứng từ" in js)
	# Màn xem phiếu phải vẽ tệp của khoản nào ngay dưới khoản đó.
	dung("màn xem phiếu vẽ tệp theo khoản", "k.tep_hien" in js)
	dung("máy chủ gửi tệp theo khoản",
	     'd["tep_hien"] = tep_dinh_kem.hien(' in _doc("vagabond", "de_nghi_chi.py"))
