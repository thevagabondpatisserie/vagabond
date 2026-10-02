"""v533: tự lưu phiếu đang soạn trên máy (48-ban-soan-do.js).

Loan Anh báo anh Việt 27/09/2026: soạn báo giá trên app, lỡ thoát ra hoặc
máy sập nguồn là mất hết. Anh Việt chốt: mọi màn lập phiếu đều phải có bản
nháp tự lưu.

Hành vi chạy thật (gõ, lùi, sập nguồn, mở lại, lưu) nằm ở
hanh_vi/ban_soan_do_533.js. Các ca ở đây chốt những thứ KHÔNG chạy được
trong node mà sai là lặng lẽ mất tính năng:
  - màn lập phiếu nào cũng được bọc, không màn nào bị bỏ quên;
  - tên hàm máy chủ khai là "lưu thành công" có thật trong mã (gõ sai một
    chữ là bản nháp không bao giờ tự xoá sau khi lưu);
  - mọi màn dựng trạng thái ngay trong hàm của nó đều có móc ghép bản nháp;
  - phần 48 nằm sau mọi phần có màn lập phiếu và trước phần đóng vỏ."""
import re
from pathlib import Path

from vagabond.khung.kiem_thu.nen import ca, dung, la

GOC = Path(__file__).resolve().parents[3]
BEP = GOC / "vagabond" / "public" / "js" / "bep"
MA48 = (BEP / "48-ban-soan-do.js").read_text(encoding="utf-8")
CAC_PHAN = {p.name: p.read_text(encoding="utf-8") for p in sorted(BEP.glob("*.js")) if p.name != "48-ban-soan-do.js"}
TAT_CA = "\n".join(CAC_PHAN.values())

# Moi man lap phieu phai co ban nhap. Them man lap phieu moi thi them vao day
# VA khai trong 48; bo mot man khoi day phai ghi ly do vao MIEN duoi.
MAN_LAP_PHIEU = [
	"scrBgSua", "scrTvSua", "scrStep1", "scrStep2", "scrStep3", "scrStep4",
	"scrXkHuyNew", "scrXkCkNew", "scrRndNew", "scrDsNhapTay", "scrHdTao",
	"scrHdSuaSoLieu", "scrHdGhiSo", "scrVdTao", "scrVdChiPhi", "scrKgTao",
	"scrNccTao", "scrDeNghiChi", "scrHoSoTTTao", "scrHoanUngTao", "scrChiCongTyTao",
	"scrBtLap", "scrNopQuyTao", "scrNopQuySua", "scrCongThucSua", "scrTraTruocTao",
	"scrTiecXuat", "scrTqSua", "scrTqLapDot", "scrBntTao", "scrKPITuKhai",
	"scrXkNbNew", "scrXkTraNew", "scrXkSiNew", "scrXkPvNew", "scrRecvDoc",
	"scrNhpDon", "scrMfgDeclare", "scrCntTruocErp",
	"hoanMoForm", "hoanMoFormDu", "hoanMoFormHuy", "dhMo", "kmSheetCtkm",
]
# Man ten giong man lap phieu nhung CO Y khong boc, kem ly do.
MIEN = {
	"scrKkNew": "kiểm kê đã tự lưu lên máy chủ mỗi 3 giây",
	"scrMfgNew": "danh sách lệnh do máy tính từ nhu cầu, mở lại là tính lại; bấm tạo là tạo lệnh ngay",
	"scrPhLap": "chỉ là màn chọn loại việc và chọn đơn, form hoàn tiền phía sau đã có bản nháp",
	"scrNhapSaoKe": "nhập tệp sao kê, không có ô gõ tay",
	"scrHuongDanSoan": "soạn hướng dẫn, không phải lập phiếu",
	"scrDiemBanSua": "màn cài đặt", "scrHangSua": "màn cài đặt", "scrMayInSua": "màn cài đặt",
	"scrPtSua": "màn cài đặt", "scrTaiKhoanSua": "màn cài đặt",
}


def _boc():
	ra = {}
	for m in re.finditer(r"^(\w+) = sdBoc(Hop)?\('(\w+)', '(\w+)', (\w+)\);$", MA48, re.M):
		ra[m.group(1)] = (m.group(3), m.group(4), m.group(5), bool(m.group(2)))
	return ra


def _khai():
	ra = {}
	for m in re.finditer(r"^sdKhai\('(\w+)', '(\w+)', \{", MA48, re.M):
		ra[m.group(1)] = m.group(2)
	# ba form hoan tien khai trong mot vong lap
	for m in re.finditer(r"'(\w+):(\w+):[^']+'", MA48):
		ra[m.group(1)] = m.group(2)
	return ra


def _than_khai(loai):
	i = MA48.find("sdKhai('%s'," % loai)
	if i < 0:
		i = MA48.find("'%s:" % loai)
		i = MA48.find("sdKhai(p[0]", i)
	j = MA48.find("\n});", i)
	return MA48[i:j]


@ca("v533 mọi màn lập phiếu đều được bọc tự lưu nháp, đúng tên, đúng loại")
def _du_man():
	boc = _boc()
	khai = _khai()
	for t in MAN_LAP_PHIEU:
		dung("%s được bọc" % t, t in boc)
		if t not in boc:
			continue
		loai, ten, goc, _ = boc[t]
		la("%s bọc đúng tên" % t, (ten, goc), (t, t))
		dung("%s có khai loại %s" % (t, loai), loai in khai)
	la("không bọc thừa màn ngoài danh sách", sorted(set(boc) - set(MAN_LAP_PHIEU)), [])


@ca("v533 màn tên giống lập phiếu mà không bọc thì phải nằm trong danh sách miễn, kèm lý do")
def _khong_sot():
	boc = _boc()
	ten = re.findall(r"^(?:async )?function (scr\w*(?:Tao|New|Lap|Moi|Sua|Soan|Nhap)\w*)\(", TAT_CA, re.M)
	sot = sorted(t for t in set(ten) if t not in boc and t not in MIEN)
	la("màn lập phiếu chưa có bản nháp", sot, [])
	for t, ly in MIEN.items():
		dung("miễn %s có lý do" % t, bool(ly.strip()))


@ca("v533 hàm được bọc có thật và khai đúng một lần ở các phần khác")
def _ham_that():
	for t in _boc():
		n = len(re.findall(r"^(?:async )?function %s\(" % t, TAT_CA, re.M))
		la("hàm %s khai một lần" % t, n, 1)


@ca("v533 hàm máy chủ khai là 'lưu thành công' có thật trong mã các màn")
def _ham_luu_that():
	cac_luu = re.findall(r"luu: \[([^\]]*)\]", MA48)
	dung("có khai hàm lưu", len(cac_luu) >= 30)
	for nhom in cac_luu:
		for m in re.findall(r"'(vagabond\.[\w.]+|frappe\.[\w.]+)'", nhom):
			dung("hàm lưu %s có trong mã" % m, ("'%s'" % m) in TAT_CA)
		for dt in re.findall(r"sdChen\('([^']+)'\)", nhom):
			dung("doctype %s có insert trong mã" % dt, ("doctype: '%s'" % dt) in TAT_CA)


@ca("v533 mỗi loại khai đều có hàm lưu, loại không đọc được trạng thái thì phải đọc ô nhập")
def _moi_loai_co_luu():
	for loai in _khai():
		than = _than_khai(loai)
		dung("loại %s có khai luu" % loai, "luu: [" in than)
		dung("loại %s có lay hoặc chạy theo ô nhập" % loai, ("lay:" in than) or ("phat: 1" in than))


@ca("v533 màn dựng trạng thái trong hàm của nó đều có móc ghép bản nháp")
def _moc_ghep():
	can = {"nhap_kho": "06-nhap-kho-kiem-ke.js", "nhan_hang": "06-nhap-kho-kiem-ke.js",
		"hoan_tien": "11-khach-ca-hop-dong.js", "hoan_du": "11-khach-ca-hop-dong.js",
		"hoan_huy": "11-khach-ca-hop-dong.js", "don_huy_hoan": "29-don-huy.js", "ctkm": "13-khuyen-mai.js"}
	for loai, tep in can.items():
		la("móc ghép %s nằm trong %s" % (loai, tep), CAC_PHAN[tep].count("sdGhep('%s'," % loai), 1)
	moc = set(re.findall(r"sdGhep\('(\w+)'", TAT_CA))
	la("không có móc ghép thừa", sorted(moc - set(can)), [])
	# hai form hoan tien mo bang then(): phai tra promise thi ban boc moi cho
	# duoc toi luc form ve xong (khong thi khong dang ky duoc hop).
	for ham, m in (("hoanMoFormDu", "xem_tien_du"), ("hoanMoFormHuy", "xem_huy_nhap")):
		dung("%s trả promise" % ham, ("return api('vagabond.hoan_tien.%s'" % m) in CAC_PHAN["11-khach-ca-hop-dong.js"])


@ca("v533 phần 48 ghép sau mọi màn lập phiếu, trước phần đóng vỏ")
def _thu_tu():
	ten = sorted(p.name for p in BEP.glob("*.js"))
	i = ten.index("48-ban-soan-do.js")
	# v550: phần 49-tru-kho-bu.js đứng sau 48 vì số 00-48 đã hết chỗ. Được
	# phép vì nó không có màn lập phiếu nào (không định nghĩa hàm nào trong
	# MAN_LAP_PHIEU, không có móc sdGhep) và không gán lại frame/api, tức là
	# không có gì 48 cần bọc hay bị nó đè. Phần mới đứng sau 48 phải qua đủ
	# ba điều kiện dưới, không thì đỏ.
	sau = ten[i + 1:]
	la("99 đứng cuối, sau 48", sau[-1:], ["99-dong-vo.js"])
	for f in sau[:-1]:
		m = CAC_PHAN[f]
		dinh = set(re.findall(r"^(?:async )?function (\w+)\(", m, re.M))
		la("%s sau 48 không có màn lập phiếu" % f, sorted(dinh & set(MAN_LAP_PHIEU)), [])
		dung("%s sau 48 không có móc ghép bản nháp" % f, "sdGhep(" not in m)
		dung("%s sau 48 không gán lại frame/api" % f,
			not re.search(r"^\s*(frame|api)\s*=", m, re.M))
	la("chỉ phần được duyệt đứng giữa 48 và 99", sau[:-1], ["49-tru-kho-bu.js"])
	for t in _boc():
		tep = [n for n, ma in CAC_PHAN.items() if re.search(r"^(?:async )?function %s\(" % t, ma, re.M)]
		dung("%s nằm ở phần trước 48" % t, bool(tep) and tep[0] < "48-ban-soan-do.js")


@ca("v533 bản nháp không lưu ảnh base64 và tệp, có hạn 14 ngày, khoá theo tài khoản")
def _chot_luat():
	dung("khoá có tài khoản", "SD_TIEN_TO + sdNguoi() + ':' + loai" in MA48)
	dung("hạn 14 ngày", "var SD_HAN_NGAY = 14;" in MA48)
	dung("bỏ Blob", "v instanceof Blob" in MA48)
	dung("bỏ data: base64", "base64," in MA48)
	# Chot o day vi da tung hong: khong goi ham doc o nhap cua man khi tu luu
	# (vai ham gan '' cho o khong co, xoa trang trang thai luc man dang tai).
	dung("không gọi hàm đọc ô nhập của màn", "cfg.doc(" not in MA48)


@ca("v533 ca hành vi chạy trong cổng trước deploy")
def _cong():
	sh = (GOC / "kiem_truoc_deploy.sh").read_text(encoding="utf-8")
	dung("cổng chạy ban_soan_do_533.js", "node vagabond/khung/kiem_thu/hanh_vi/ban_soan_do_533.js" in sh)
