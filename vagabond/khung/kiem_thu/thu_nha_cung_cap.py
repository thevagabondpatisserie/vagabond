"""Kiem thu man Tao nha cung cap tren app.

Uyen vap hai chuyen hom 21/08/2026: khong co quyen Tao, va form chi co bon
o. Sua xong thi anh Viet bao them: email KHONG duoc bat buoc, vi co nha
cung cap chi ban qua app hoac san thuong mai dien tu; va can them ba o
email phu de CC cho ke toan va kho cua ho.
"""

from vagabond import nha_cung_cap as ncc
from vagabond.khung.kiem_thu.nen import ca, dung, la


@ca("nhà cung cấp: thiếu tên hoặc thiếu nhóm thì phải chặn, nói rõ thiếu ô nào")
def _():
	la("trống trơn", ncc.thieu_o_nao({}), ["Tên nhà cung cấp", "Nhóm nhà cung cấp"])
	la("có tên thiếu nhóm", ncc.thieu_o_nao({"ten": "Cacao Bến Tre"}),
		["Nhóm nhà cung cấp"])
	la("đủ hai ô", ncc.thieu_o_nao({"ten": "A", "nhom": "Nguyên liệu"}), [])


@ca("nhà cung cấp: KHÔNG có email vẫn lưu được, vì có bên chỉ bán qua app và sàn")
def _():
	la("không email", ncc.thieu_o_nao({"ten": "A", "nhom": "N"}), [])
	la("email rỗng", ncc.thieu_o_nao({"ten": "A", "nhom": "N", "email": "   "}), [])


@ca("email CC: gom ba ô lại, bỏ ô trống và bỏ trùng, giữ nguyên thứ tự người gõ")
def _():
	la("ba ô đủ", ncc.loc_email_cc(["a@v.com", "b@v.com", "c@v.com"]),
		["a@v.com", "b@v.com", "c@v.com"])
	la("bỏ ô trống", ncc.loc_email_cc(["a@v.com", "", None, "  "]), ["a@v.com"])
	la("bỏ trùng khác hoa thường", ncc.loc_email_cc(["A@v.com", "a@v.com"]),
		["A@v.com"])
	la("không có gì", ncc.loc_email_cc([]), [])
	la("None", ncc.loc_email_cc(None), [])


@ca("email CC: gõ liền một chuỗi ngăn bằng dấu phẩy hay chấm phẩy cũng tách được")
def _():
	la("dấu phẩy", ncc.loc_email_cc("a@v.com, b@v.com"), ["a@v.com", "b@v.com"])
	la("chấm phẩy", ncc.loc_email_cc("a@v.com; b@v.com"), ["a@v.com", "b@v.com"])


@ca("mã số thuế: chuẩn hoá về dạng gõ vào bảng, giữ dấu gạch của chi nhánh")
def _():
	la("khoảng trắng", ncc.chuan_mst("  0301234567  "), "0301234567")
	la("chi nhánh 13 số", ncc.chuan_mst("0301234567-001"), "0301234567-001")
	la("rỗng", ncc.chuan_mst(None), "")


@ca("email: bắt được địa chỉ gõ thiếu đuôi, không nới tay nuốt luôn")
def _():
	dung("đúng", ncc.email_hop_le("mua@vagabond.com"))
	dung("thiếu chấm com", not ncc.email_hop_le("mua@vagabond"))
	dung("thiếu a còng", not ncc.email_hop_le("mua.vagabond.com"))


@ca("nhà cung cấp: ô email phụ CC phải được khai trong mã nguồn, không bấm tay Desk")
def _():
	khai = ncc.TRUONG_MOI.get("Supplier") or []
	ten = [x.get("fieldname") for x in khai]
	dung("có ô email_cc", "email_cc" in ten)
	o = [x for x in khai if x.get("fieldname") == "email_cc"][0]
	la("đặt ngay sau ô email", o.get("insert_after"), "email_id")
