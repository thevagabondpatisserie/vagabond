# -*- coding: utf-8 -*-
"""Ca kiểm: duyệt chi và ghi sổ là HAI bước (anh Việt 03/09/2026).

Anh Việt, kèm ảnh phiếu APP-26-09-050 đang mang trạng thái "Đã thanh toán"
ngay sau khi giám đốc ký:

    *"Giám đốc duyệt là mới duyệt chi thôi, kế toán chi tiền rồi đính kèm
    UNC, khớp giao dịch SePay vào thì mới ghi sổ và chuyển trạng thái đã
    thanh toán chứ."*

Ca kiểm ở đây giữ đúng ranh giới đó, và giữ ba hàng rào lúc ghi sổ. Toàn
phép thuần và phép soi chuỗi, không cần Frappe.
"""

import io
import os

from vagabond import duyet_chi
from vagabond.khung.kiem_thu.nen import ca, dung, la


def _doc(duong):
	goc = os.path.dirname(os.path.dirname(os.path.abspath(duyet_chi.__file__)))
	return io.open(os.path.join(goc, duong), encoding="utf-8").read()


@ca("duyệt chi: chữ ký giám đốc KHÔNG còn ghi sổ")
def _tach_buoc():
	states, trans = duyet_chi.khuon_workflow()
	buoc = {s["state"]: s for s in states}
	dung("có bước đã duyệt chi", duyet_chi.TT_DA_DUYET_CHI in buoc)
	la(
		"bước đã duyệt chi KHÔNG ghi sổ",
		buoc[duyet_chi.TT_DA_DUYET_CHI]["doc_status"],
		"0",
	)
	la("chỉ đúng một bước ghi sổ", len([s for s in states if s["doc_status"] == "1"]), 1)
	la("bước ghi sổ là bước cuối", buoc[duyet_chi.TT_DA_GHI_SO]["doc_status"], "1")

	di = {(t["state"], t["action"]): t for t in trans}
	gd = di[(duyet_chi.TT_CHO_GD, "Duyệt chi")]
	la("giám đốc ký thì phiếu sang bước chờ chuyển tiền", gd["next_state"], duyet_chi.TT_DA_DUYET_CHI)
	dung("giám đốc KHÔNG đi thẳng tới bước ghi sổ", gd["next_state"] != duyet_chi.TT_DA_GHI_SO)
	xn = di[(duyet_chi.TT_DA_DUYET_CHI, "Xác nhận đã chuyển tiền")]
	la("kế toán mới là người đưa phiếu vào sổ", xn["next_state"], duyet_chi.TT_DA_GHI_SO)
	dung("và bước đó thuộc vai kế toán", "FIN" in xn["allowed"])
	dung(
		"bước chờ chuyển tiền vẫn trả lại được",
		(duyet_chi.TT_DA_DUYET_CHI, "Trả lại") in di,
	)


@ca("duyệt chi: giữ nguyên tên các bước cũ để phiếu cũ không mồ côi")
def _giu_ten_cu():
	states, _ = duyet_chi.khuon_workflow()
	ten = [s["state"] for s in states]
	for cu in ("Nháp", "Chờ FIN kiểm tra", "Chờ giám đốc duyệt",
			"Đã duyệt - Đã ghi sổ", "Bị trả lại"):
		dung("bước %s còn nguyên tên" % cu, cu in ten)


@ca("duyệt chi: ba hàng rào, thiếu cái nào cũng chặn")
def _ba_hang_rao():
	du = duyet_chi.soat_ghi_so(duyet_chi.TT_DA_DUYET_CHI, 1, 1000000, 1000000)
	la("đủ cả ba thì cho ghi sổ", du["ok"], 1)

	chua_ky = duyet_chi.soat_ghi_so(duyet_chi.TT_CHO_GD, 1, 1000000, 1000000)
	la("chưa qua chữ ký giám đốc thì chặn", chua_ky["ok"], 0)
	dung("nói rõ vì sao", "chua_duyet" in chua_ky["thieu"])

	thieu_unc = duyet_chi.soat_ghi_so(duyet_chi.TT_DA_DUYET_CHI, 0, 1000000, 1000000)
	la("chưa có uỷ nhiệm chi thì chặn", thieu_unc["ok"], 0)
	dung("nói rõ vì sao", "thieu_unc" in thieu_unc["thieu"])

	chua_ve = duyet_chi.soat_ghi_so(duyet_chi.TT_DA_DUYET_CHI, 1, 1000000, 0)
	la("tiền chưa ra khỏi tài khoản thì chặn", chua_ve["ok"], 0)
	dung("nói rõ vì sao", "chua_ve_tien" in chua_ve["thieu"])


@ca("duyệt chi: sai lệch nhỏ vẫn tính là đã về đủ")
def _sai_lech():
	la("về đúng đủ", duyet_chi.sepay_du(1000000, 1000000), 1)
	la("thiếu nửa đồng do làm tròn thì vẫn nhận", duyet_chi.sepay_du(1000000, 999999.5), 1)
	la("thiếu một nghìn thì không", duyet_chi.sepay_du(1000000, 999000), 0)
	la("về dư thì vẫn đủ", duyet_chi.sepay_du(1000000, 1200000), 1)
	la("chưa về đồng nào", duyet_chi.sepay_du(1000000, 0), 0)


@ca("duyệt chi: đường thoát khi tiền đã đi mà sao kê chưa về")
def _duong_thoat():
	co_ly_do = duyet_chi.soat_ghi_so(
		duyet_chi.TT_DA_DUYET_CHI, 1, 1000000, 0, "Chuyển liên ngân hàng lúc 22h", 1
	)
	la("kế toán trưởng ghi lý do thì đi tiếp được", co_ly_do["ok"], 1)
	khong_quyen = duyet_chi.soat_ghi_so(
		duyet_chi.TT_DA_DUYET_CHI, 1, 1000000, 0, "Chuyển liên ngân hàng lúc 22h", 0
	)
	la("người không đủ quyền thì vẫn chặn", khong_quyen["ok"], 0)
	rong = duyet_chi.soat_ghi_so(duyet_chi.TT_DA_DUYET_CHI, 1, 1000000, 0, "   ", 1)
	la("lý do để trống thì không tính là có lý do", rong["ok"], 0)
	# Duong thoat CHI mo cho hang rao SePay, khong mo cho hai hang rao kia.
	van_chan = duyet_chi.soat_ghi_so(
		duyet_chi.TT_CHO_GD, 0, 1000000, 0, "Tiền đã đi rồi", 1
	)
	la("lý do không mở được chữ ký và uỷ nhiệm chi", van_chan["ok"], 0)
	dung("vẫn giữ cả hai lỗi kia", set(van_chan["thieu"]) >= {"chua_duyet", "thieu_unc"})


@ca("duyệt chi: câu nói cho người dùng nói đủ việc phải làm")
def _cau_noi():
	c = duyet_chi.cau_thieu(["chua_duyet", "thieu_unc", "chua_ve_tien"], 1000000, 300000)
	dung("nhắc chữ ký giám đốc", "giám đốc" in c)
	dung("nhắc uỷ nhiệm chi", "uỷ nhiệm chi" in c)
	dung("nói rõ đã về bao nhiêu trên bao nhiêu", "300.000 đ" in c and "1.000.000 đ" in c)
	dung("không có dấu gạch dài", "—" not in c and "–" not in c)
	la("nhãn bước đọc được", duyet_chi.nhan_buoc(duyet_chi.TT_DA_DUYET_CHI),
		"Đã duyệt chi, chờ chuyển tiền")
	la("bước cuối nói đúng nghĩa mới", duyet_chi.nhan_buoc(duyet_chi.TT_DA_GHI_SO),
		"Đã chuyển tiền, đã ghi sổ")


@ca("duyệt chi: bước nào tiền chưa ra khỏi sổ")
def _chua_ghi_so():
	for b in (duyet_chi.TT_NHAP, duyet_chi.TT_CHO_FIN, duyet_chi.TT_CHO_GD,
			duyet_chi.TT_DA_DUYET_CHI, duyet_chi.TT_TRA_LAI):
		la("%s: tiền chưa ra" % b, duyet_chi.chua_ghi_so(b), True)
	la("bước ghi sổ thì tiền đã ra", duyet_chi.chua_ghi_so(duyet_chi.TT_DA_GHI_SO), False)


@ca("duyệt chi: hàng rào được nối vào hệ và không chạm luồng khác")
def _noi_vao_he():
	h = _doc("vagabond/hooks.py")
	dung("chặn ghi sổ sớm đặt ở phiếu thanh toán", "vagabond.duyet_chi.chan_ghi_so_som" in h)
	d = _doc("vagabond/duyet_chi.py")
	# Nhan dien theo NEO VAO DON MUA: but toan cua man Ho so thanh toan neo
	# vao hoa don mua nen khong bao gio dinh phai hang rao nay.
	than = d[d.index("def la_phieu_chi_app("):d.index("def _so_unc(")]
	dung("nhận diện bằng neo vào đơn mua", "== PO" in than)
	dung("đếm uỷ nhiệm chi ở ô riêng", 'doc.get("vgb_chi_unc")' in d)
	dung("hàng rào hỏng không được chặn cả đường tiền", "frappe.log_error" in d)
	t = _doc("vagabond/truong_tu_them.py")
	dung("ô ghi vết dựng lại mỗi lần deploy", "duyet_chi.TRUONG_MOI" in t)
	dung("đường duyệt dựng lại mỗi lần deploy", "duyet_chi.dung_workflow()" in t)

	# Man Ho so thanh toan doc buoc moi ra dung o "Da duyet", khong phai
	# "Da thanh toan".
	r = _doc("vagabond/tra_truoc.py")
	dung("bước mới có trong bảng dịch", "TT_DA_DUYET_CHI" in r)
	dung("và dịch sang Đã duyệt", '\tTT_DA_DUYET_CHI: "Da duyet",' in r)
	dung("bước mới vẫn tính là còn treo", "TT_DA_DUYET_CHI, TT_TRA_LAI" in r)


@ca("duyệt chi: luồng hồ sơ thanh toán cũng phải thấy tiền mới ghi sổ")
def _ho_so_tt():
	s = _doc("vagabond/ho_so_tt.py")
	than = s[s.index("def danh_dau_da_tra("):s.index("def _tu_gui_thu_bao(")]
	dung("vẫn bắt uỷ nhiệm chi", "du_unc(dem_unc(doc.name))" in than)
	dung("thêm hàng rào giao dịch ngân hàng", "duyet_chi.sepay_du(" in than)
	dung("dùng chung câu nói của một nguồn", "duyet_chi.cau_thieu(" in than)
	dung("có đường thoát cho kế toán trưởng", "VAI_BO_QUA_SEPAY" in than)
	dung("và đường thoát để lại vết", "vgb_tt_ly_do_som" in than)


@ca("duyệt chi: màn hình đi đúng đường mới")
def _man_hinh():
	j = _doc("vagabond/public/js/bep/04-tao-phieu.js")
	dung(
		"giám đốc ký thì sang bước chờ chuyển tiền",
		"action: 'Duyệt chi', next: 'Đã duyệt chi - chờ chuyển tiền'" in j,
	)
	dung(
		"không còn nút nào đi thẳng từ chữ ký sang ghi sổ",
		"action: 'Duyệt chi', next: 'Đã duyệt - Đã ghi sổ'" not in j,
	)
	dung("có bước xác nhận đã chuyển tiền", "'Xác nhận đã chuyển tiền'" in j)
	dung("bước đó đi qua cửa riêng", "cua_rieng: 1" in j)
	dung("cửa riêng gọi đúng hàm máy chủ", "vagabond.duyet_chi.xac_nhan_da_chuyen" in j)
	dung("màn đọc tình hình trước khi bấm", "vagabond.duyet_chi.tinh_hinh" in j)
	dung("có ô đính uỷ nhiệm chi ngay tại bước đó", "tdkKhoi('pvunc'" in j)
	dung("nhãn bước nói đúng nghĩa mới", "'Đã duyệt chi, chờ chuyển tiền'" in j)
	dung("bước cuối đọc là đã chuyển tiền", "'Đã chuyển tiền, đã ghi sổ'" in j)
	dung("không dùng dấu gạch dài", "—" not in j.split("var PAYFLOW")[1][:4000])


@ca("duyệt chi: dựng sẵn tên bước và tên nút trước khi lưu đường duyệt")
def _dung_san_ten_buoc():
	"""Ngay 04/09/2026: deploy v414 xong, đường duyệt vẫn nằm nguyên bản cũ.

	Frappe soi liên kết khi lưu Workflow: tên bước phải có sẵn một bản ghi
	trong Workflow State, tên nút phải có sẵn trong Workflow Action Master.
	Bước mới và nút mới chưa có bản ghi nào nên lệnh lưu bị chối, mà chỗ gọi
	lại nuốt lỗi, nên máy báo deploy thành công trong khi đường duyệt không
	đổi. Hàng rào mới thì đã chạy, thành ra giám đốc bấm Duyệt chi là bị
	chặn: cả đường chi tiền tắc. Ca kiểm này giữ phần dựng sẵn đó.
	"""
	s = _doc("vagabond/duyet_chi.py")
	dung("có phần dựng sẵn tên", "def _dung_san_ten(" in s)
	dung("dựng bản ghi tên bước", '"doctype": "Workflow State",' in s)
	dung("dựng bản ghi tên nút", '"doctype": "Workflow Action Master",' in s)
	than = s[s.index("def dung_workflow("):]
	dung("và gọi nó trước khi lưu", "_dung_san_ten(states, trans)" in than)
	dung(
		"gọi trước chứ không phải sau",
		than.index("_dung_san_ten(states, trans)") < than.index("w.save("),
	)
