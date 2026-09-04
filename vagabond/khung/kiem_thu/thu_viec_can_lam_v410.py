# -*- coding: utf-8 -*-
"""Bấm vào việc trả trước NCC thì phải mở đúng màn (v410, 04/09/2026).

Ngày 04/09/2026 anh Việt vào duyệt hai việc APP-26-08-534 và APP-26-09-050
trên màn Việc cần làm, cả hai đều báo "Không tìm thấy Vagabond Ho So TT
APP-26-08-534".

Nguyên nhân: `_viec_tra_truoc` đẩy phiếu TRẢ TRƯỚC vào hàng đợi dưới nhãn
`loai = "ho_so_tt"` cho đúng nhóm, nhưng `ma` của nó là tên một Payment
Entry chứ không phải mã một Hồ sơ TT. Màn Hồ sơ thanh toán đã chia đúng hai
đường từ v408 bằng ô `data-hspc`, riêng màn Việc cần làm thì chưa, nên nó
mở mọi dòng bằng màn Hồ sơ TT và máy chủ trả về không tìm thấy.

Hai mã khác nhau ở dấu, và đó là điều không đổi được: Hồ sơ TT tự sinh mã
dạng APP.26.08.027 (dấu CHẤM) trong `ho_so_tt._sinh_ma`, còn Payment Entry
đi theo bộ mã của ERPNext nên dùng dấu GẠCH.
"""

import io
import os

from vagabond.khung.kiem_thu.nen import ca, dung, la


GOI = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _py(ten):
	return io.open(os.path.join(GOI, ten), encoding="utf-8").read()


def _js(ten):
	return io.open(os.path.join(GOI, "public", "js", "bep", ten), encoding="utf-8").read()


def _goc(ten):
	return io.open(os.path.join(os.path.dirname(GOI), ten), encoding="utf-8").read()


# ------------------------------------------------------ ô máy chủ gửi xuống


@ca("v410 dòng trả trước mang ô phieu_chi để app biết đó là phiếu chi")
def _o_phieu_chi():
	src = _py("viec_can_lam.py")
	i = src.index("def _viec_tra_truoc(")
	j = src.index("def _viec_nop_quy(", i)
	than = src[i:j]
	dung("có ô phieu_chi", '"phieu_chi": 1,' in than)
	dung("vẫn giữ nhãn ho_so_tt để nằm đúng nhóm", '"loai": "ho_so_tt"' in than)
	# Ô phải nằm trong CÙNG một dòng ra, không phải một nhánh khác.
	i_o = than.index('"phieu_chi": 1,')
	i_ma = than.index('"loai": "ho_so_tt", "ma": o["name"]')
	dung("cùng một dòng ra", 0 < i_ma - i_o < 200)


@ca("v410 dòng hồ sơ thật KHÔNG mang ô phieu_chi")
def _ho_so_that_khong_co():
	src = _py("viec_can_lam.py")
	i = src.index("def _viec_ho_so_tt(")
	j = src.index("def _viec_tra_truoc(", i)
	dung("không dính vào nhánh hồ sơ thật", '"phieu_chi"' not in src[i:j])


# ------------------------------------------------------------ phép thuần app


@ca("v410 phép nhận dạng phiếu chi đọc ô máy chủ gửi trước")
def _doc_o_truoc():
	src = _js("02-trang-chu.js")
	i = src.index("function vclLaPhieuChi(")
	j = src.index("function vclMo(", i)
	than = src[i:j]
	dung("đọc x.phieu_chi", "if (x.phieu_chi) return true;" in than)
	dung("chặn dòng rỗng", "if (!x) return false;" in than)


@ca("v410 mất ô thì còn đường nhận dạng theo dấu của mã")
def _duong_thu_hai():
	src = _js("02-trang-chu.js")
	i = src.index("function vclLaPhieuChi(")
	j = src.index("function vclMo(", i)
	than = src[i:j]
	dung("mã có gạch mà không có chấm là phiếu chi",
		"ma.indexOf('-') >= 0 && ma.indexOf('.') < 0" in than)
	# Doc o truoc, do dau sau: neu do dau truoc thi ho so nao lo mang gach
	# se bi mo nham man ngay ca khi may chu da noi ro no la ho so.
	dung("đọc ô trước rồi mới dò dấu",
		than.index("x.phieu_chi") < than.index("ma.indexOf('-')"))


@ca("v410 phép thuần khai TRƯỚC chỗ dùng")
def _khai_truoc():
	src = _js("02-trang-chu.js")
	dung("khai trước vclMo",
		src.index("function vclLaPhieuChi(") < src.index("function vclMo("))


# ----------------------------------------------------------- đường mở màn


@ca("v410 màn Việc cần làm chia hai đường, không mở mọi dòng bằng màn Hồ sơ TT")
def _chia_hai_duong():
	src = _js("02-trang-chu.js")
	i = src.index("function vclMo(")
	j = src.index("\n}", src.index("if (l === 'ho_so_tt')", i))
	than = src[i:j]
	dung("có chia nhánh", "vclLaPhieuChi(x) ? scrPayView(x.ma) : scrHoSoTTView(x.ma)" in than)
	dung("hết mở thẳng bằng màn hồ sơ",
		"if (l === 'ho_so_tt') return go(function () { scrHoSoTTView(x.ma); });" not in than)


@ca("v410 màn Hồ sơ thanh toán giữ nguyên đường chia của v408")
def _giu_nep_v408():
	src = _js("19-ho-so-tt.js")
	dung("còn ô data-hspc", "data-hspc" in src)
	dung("còn mở bằng scrPayView", "scrPayView(nm)" in src)


@ca("v410 hai bộ mã khác nhau ở dấu, không lẫn được")
def _hai_bo_ma():
	src = _py("ho_so_tt.py")
	i = src.index("def _sinh_ma(")
	j = src.index("\ndef ", i + 10)
	dung("hồ sơ TT sinh mã dấu chấm", 'tien_to = "APP.%02d.%02d."' in src[i:j])


@ca("v410 patches.txt có dòng đợt này")
def _dang_ky():
	dong = [d.strip() for d in _goc("vagabond/patches.txt").splitlines()]
	dung("có dòng v410", "vagabond.patches.dong_bo_cau_truc #v410" in dong)
	dung("giữ nguyên dòng v409", "vagabond.patches.dong_bo_cau_truc #v409" in dong)
