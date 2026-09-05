"""Ca kiểm cho hai lỗi im lặng của màn Quản lý người dùng (05/09/2026).

Cả hai đều cùng một họ: MÀN HÌNH NÓI MỘT ĐẰNG, HỆ THỐNG LÀM MỘT NẺO, và
không câu báo nào kêu lên.

LỖI MỘT: xếp gói xong quyền không vào.
  Khung dựng lại danh sách vai từ bộ vai mẫu mỗi lần lưu tài khoản, nên vai
  vừa ghi bị xoá ngay trong cùng lượt lưu. Màn hình vẫn báo thành công. Đo
  ra 22 trên 35 tài khoản đang bị buộc bộ vai mẫu, tức là màn này vô hiệu
  với hai phần ba số người. Anh Việt gặp ngày 05/09; lần 21/08 hỏng cùng lý
  do mà lúc đó chỉ ghi được triệu chứng.

LỖI HAI: người có tài khoản mà màn hình bảo chưa có.
  Danh sách chỉ lấy tài khoản nội bộ, còn đường mời tài khoản mới lại chặn
  theo MỌI loại. Bốn shipper của tiệm là tài khoản web nên không hiện, mà
  tạo mới thì báo đã có rồi. Không có đường nào đi tiếp.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _doc(ten):
	with io.open(os.path.join(GOI, ten), encoding="utf-8") as f:
		return f.read()


ND = _doc("nguoi_dung.py")
JS = _doc(os.path.join("public", "js", "bep", "20-danh-muc-quyen.js"))


@ca("ghi vai phai go bo vai mau truoc, khong thi ghi xong bi xoa ngay")
def _go_bo_vai_mau():
	i = ND.find("def _dat_vai(")
	than = ND[i:ND.find("@frappe.whitelist()", i)]
	dung("co goi ham go bo vai mau", "_go_bo_vai_mau(doc)" in than)
	# Phai go TRUOC khi ghi vai, khong thi vo nghia.
	dung("go truoc khi ghi vai",
		than.find("_go_bo_vai_mau(doc)") < than.find('doc.set("roles", [])'))
	h = ND.find("def _go_bo_vai_mau(")
	thh = ND[h:ND.find("def _dat_vai(", h)]
	dung("go ca o mot bo lan bang nhieu bo", "role_profile_name" in thh
		and "role_profiles" in thh)
	dung("noi ro vi sao trong ghi chu", "dựng LẠI" in thh or "dựng lại" in thh)


@ca("ghi vai xong phai DOC LAI de chac quyen da vao that")
def _doc_lai_sau_khi_ghi():
	"""Nuot mot lan im lang la mat niem tin vao ca man hinh. Ghi xong phai
	doc lai tu co so du lieu chu khong tin bien trong bo nho."""
	i = ND.find("def _dat_vai(")
	than = ND[i:ND.find("@frappe.whitelist()", i)]
	dung("doc lai sau khi luu", "_vai_cua(email)" in than.split("doc.save")[-1])
	dung("keu len khi chua vao", "frappe.throw" in than.split("doc.save")[-1])
	dung("cau bao noi phai lam gi tiep", "báo" in than.split("doc.save")[-1])


@ca("danh sach nguoi dung khong duoc loc theo loai tai khoan nua")
def _khong_loc_theo_loai():
	i = ND.find("def danh_sach(")
	than = ND[i:ND.find("def danh_sach_goi(", i)]
	dung("khong con loc cung theo System User",
		'filters={"user_type": "System User"}' not in than)
	dung("van doc ra loai de con phan biet", '"user_type"' in than)
	dung("noi ro ly do trong ghi chu", "shipper" in than)


@ca("tai khoan web CO quyen nghiep vu thi hien, khong quyen thi bo qua")
def _loc_theo_quyen_nghiep_vu():
	"""Hien tai khoan web la de thay shipper. Nhung mai nay khach co tai khoan
	cong thong tin thi man nay khong duoc do day ten khach."""
	i = ND.find("def danh_sach(")
	than = ND[i:ND.find("def danh_sach_goi(", i)]
	dung("co chan tai khoan ngoai pham vi",
		'u.user_type != "System User"' in than)
	dung("chan theo viec co quyen nghiep vu hay khong",
		"(vai & co_that) - VAI_NEN" in than)


@ca("cau bao email trung phai noi ro loai gi va lam gi tiep")
def _bao_trung_ro_rang():
	i = ND.find("def moi(")
	than = ND[i:]
	dung("khong con cau cut ngan cu", 'đã có tài khoản rồi." % email' not in than)
	dung("noi ten nguoi dang giu email", "full_name" in than)
	dung("noi loai tai khoan", "tài khoản web" in than)
	dung("noi dang bat hay tat", "đang %s" in than)
	dung("chi duong di tiep khi tai khoan dang bat", "xếp gói chức vụ" in than)
	dung("chi duong di tiep khi tai khoan da tat", "bật lại rồi xếp gói" in than)


@ca("man hinh phai hien nhan tai khoan web de khong ai nhin nham")
def _nhan_tren_man():
	dung("may chu tra ve co nhan", '"la_tk_web"' in ND)
	dung("man hinh co dung nhan do", "r.la_tk_web" in JS)
	dung("chu hien ra la tieng Viet co dau", "tài khoản web" in JS)
