"""v638 (anh Việt 04/11/2026): bấm "Nhắn Zalo" ở biên nhận đặt bánh ra trang Zalo
"Trang này không tìm thấy hoặc không hợp lệ".

Tái hiện trên site thật trước khi sửa: lien_he().zalo = https://zalo.me/0931224334
(ô Zalo trong Settings), mở link đó Zalo trả "This account does not exist or does
not allow searching". Link OA của khối "Zalo OA" trên web
(https://zalo.me/thevagabondsaigon) mở đúng trang The Vagabond Pâtisserie.

Sửa: một nguồn chọn link Zalo (don_web.chon_link_zalo) bỏ link số điện thoại khi
có link OA; cửa nhập thẻ Liên hệ ở Editor chặn link số điện thoại.
Ca kiểm gọi lien_he() THẬT, chỉ thay Settings và bản web công khai.
"""
from unittest import mock

from vagabond.khung.kiem_thu.nen import ca, dung, la

OA = "https://zalo.me/thevagabondsaigon"
SO = "https://zalo.me/0931224334"


def _khoi(lien_ket=OA, hien=True, loai="zalo_oa"):
	return [{"id": "kenh-zalo", "loai": loai, "hien": hien, "lien_ket": lien_ket}]


def _lien_he(settings, khoi):
	from vagabond import don_web, noi_dung_web

	with mock.patch.object(don_web, "cfg_o", lambda k: settings.get(k)), \
			mock.patch.object(noi_dung_web, "_ban_cong_khai", lambda khoa=False: {"khoi": khoi}):
		return don_web.lien_he()


@ca("v638: nhận ra link Zalo theo số điện thoại, không nhầm link OA hay mã OA")
def _():
	from vagabond.don_web import la_zalo_so_dien_thoai as f

	la("số điện thoại", [f(SO), f("https://zalo.me/+84931224334/"), f("https://www.zalo.me/0931224334")], [True, True, True])
	la("OA và mã OA 19 số", [f(OA), f("https://zalo.me/1671517125356353279"), f(""), f("khong phai link")], [False, False, False, False])


@ca("v638: Settings để link số điện thoại, web có khối Zalo OA: nút Nhắn Zalo đi link OA (đúng chuỗi trên site thật)")
def _():
	lh = _lien_he({"web_zalo": SO, "web_dien_thoai": "0931 224 334"}, _khoi())
	la("link zalo", lh["zalo"], OA)
	la("số gọi giữ nguyên", lh["dien_thoai_so"], "0931224334")


@ca("v638: Settings trống: dùng link OA trước, chỉ khi không có OA mới dựng từ số điện thoại")
def _():
	la("có OA", _lien_he({"web_dien_thoai": "0931 224 334"}, _khoi())["zalo"], OA)
	la("OA ẩn", _lien_he({"web_dien_thoai": "0931 224 334"}, _khoi(hien=False))["zalo"], SO)
	la("không có gì", _lien_he({}, [])["zalo"], "")


@ca("v638: link Zalo trong Settings không phải số điện thoại thì giữ nguyên, kể cả khi có OA")
def _():
	la("link riêng", _lien_he({"web_zalo": "https://zalo.me/g/abcxyz"}, _khoi())["zalo"], "https://zalo.me/g/abcxyz")


@ca("v638: khối Zalo OA mang link lạ hoặc số điện thoại thì không được dùng thay")
def _():
	la("link không phải zalo", _lien_he({"web_zalo": SO}, _khoi("https://example.com/x"))["zalo"], SO)
	la("OA cũng là số", _lien_he({"web_zalo": SO}, _khoi(SO))["zalo"], SO)
	# Khối OA mang số khác: không được coi là OA, rơi về số của tiệm trong Settings.
	la("OA là số khác", _lien_he({"web_dien_thoai": "0909 000 111"}, _khoi(SO))["zalo"], "https://zalo.me/0909000111")


@ca("v638: đọc bản web lỗi thì nút Zalo vẫn ra, không làm hỏng trang")
def _():
	from vagabond import don_web, noi_dung_web

	def _hong(khoa=False):
		raise RuntimeError("db")

	with mock.patch.object(don_web, "cfg_o", lambda k: {"web_zalo": SO}.get(k)), \
			mock.patch.object(noi_dung_web, "_ban_cong_khai", _hong):
		la("vẫn có link", don_web.lien_he()["zalo"], SO)


@ca("v638: cong_khai truyền sẵn các khối cho lien_he, chọn đúng OA")
def _():
	from vagabond import don_web

	with mock.patch.object(don_web, "cfg_o", lambda k: {"web_zalo": SO}.get(k)):
		la("khối truyền vào", don_web.lien_he(_khoi())["zalo"], OA)


@ca("v638: thẻ Liên hệ ở Editor chặn link Zalo theo số điện thoại, chỉ cách sửa")
def _():
	from vagabond import noi_dung_web as nw

	tot = {k: "" for k in nw.TRUONG_LIEN_HE}
	la("link OA qua", nw.kiem_lien_he(dict(tot, zalo=OA))["zalo"], OA)
	try:
		nw.kiem_lien_he(dict(tot, zalo=SO))
		dung("phải chặn link số điện thoại", False)
	except ValueError as e:
		dung("câu chỉ đúng link OA", "zalo.me/thevagabondsaigon" in str(e))
