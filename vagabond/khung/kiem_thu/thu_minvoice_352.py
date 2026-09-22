"""PR #352 (Claude tiếp nhận 22/09/2026): dịch vụ không ghi đơn vị, nhóm việc
cho tờ đầu vào chưa thành phiếu mua, và cửa chỉ đọc nuôi thanh báo trên Desk.

Phần chạy trên trình duyệt kiểm ở hanh_vi/cho_dung_352.js (thanh báo) và
hanh_vi/qr_xhd_bill_352.js (mã QR xuất hoá đơn trên bill)."""
import ast
from pathlib import Path
from types import SimpleNamespace

from vagabond.khung.kiem_thu.nen import ca, dung, la
from vagabond.minvoice_chung_tu import dich_vu_khong_ghi_don_vi, nhom_cho_dung, NHOM_CHO_DUNG

MA = (Path(__file__).resolve().parents[2] / "minvoice_chung_tu.py").read_text()


@ca("#352 dịch vụ không ghi đơn vị: lấy đơn vị của Món; hàng tồn kho hoặc đơn vị có tên vẫn phải khai")
def _dich_vu_trong_dvt():
	la("cước Mobifone trống đơn vị, món không tồn kho", dich_vu_khong_ghi_don_vi("", 0), True)
	la("khoảng trắng cũng là trống", dich_vu_khong_ghi_don_vi("  ", 0), True)
	la("hàng tồn kho trống đơn vị vẫn chặn", dich_vu_khong_ghi_don_vi("", 1), False)
	la("dịch vụ ghi 'Lần' vẫn phải khai quy đổi", dich_vu_khong_ghi_don_vi("Lần", 0), False)
	# Chốt vị trí: luật này đứng TRƯỚC vòng tìm quy đổi và trước câu chặn,
	# và chỉ trong don_vi_theo_ma (một chỗ tính, QT-19).
	than = MA.split("def don_vi_theo_ma(")[1].split("\ndef ")[0]
	dung("gọi luật trước vòng tìm quy đổi", 0 < than.index("dich_vu_khong_ghi_don_vi(") < than.index("ung_vien = ["))
	la("chỉ một chỗ gọi", MA.count("dich_vu_khong_ghi_don_vi(nguon"), 1)


@ca("#352 nhóm việc cho tờ chưa thành phiếu mua đọc theo sự thật của bản ghi")
def _nhom():
	la("chưa có số là chờ nguồn", nhom_cho_dung("", "lỗi gì đó", 0)[0], "thieu_nguon")
	la("lỗi quy đổi", nhom_cho_dung("1", "Món X: chưa xác định được quy đổi đơn vị nhà cung cấp 'BOX'", 0)[0], "quy_cach")
	la("nghi trùng", nhom_cho_dung("1", "Đã có chứng từ HDM-1 cùng nhà cung cấp và cùng số hoá đơn", 0)[0], "trung")
	la("đóng dấu mà không có phiếu", nhom_cho_dung("1", "", 1)[0], "dong_dau")
	la("chưa tới lượt", nhom_cho_dung("1", None, 0)[0], "cho_luot")
	la("lỗi khác", nhom_cho_dung("1", "Đối với mặt hàng None, số lượng phải là số âm", 0), ("khac", "Cần xem lý do"))
	la("mọi nhóm đều có tên", all(t for _, t in NHOM_CHO_DUNG), True)


def _nap_cua(hd, pi, vo=()):
	ham = [n for n in ast.parse(MA).body if isinstance(n, ast.FunctionDef) and n.name == "cho_dung_phieu_mua"]
	goi = []
	def get_all(dt, filters=None, pluck=None, **k):
		goi.append((dt, filters, k.get("limit_page_length")))
		if dt == "MInvoice Invoice":
			# Như SQL thật: BETWEEN không bao giờ khớp ngày trống; tờ chưa có
			# ngày chỉ ra ở truy vấn "is not set".
			if filters.get("ngay_lap") == ["is", "not set"]:
				return [dict(x) for x in vo]
			return [dict(x) for x in hd if x.get("ngay_lap")]
		return [x for x in pi if x in filters["custom_minvoice_id"][1]]
	f = SimpleNamespace(get_all=get_all, whitelist=lambda: (lambda h: h), utils=SimpleNamespace(add_days=lambda d, n: "2026-03-26"))
	env = dict(frappe=f, _kiem_quyen=lambda: None, nowdate=lambda: "2026-09-22", cint=lambda n: int(n or 0),
		flt=lambda n: float(n or 0), DT_HD="MInvoice Invoice", PI="Purchase Invoice", LOAI_VAO="Đầu vào",
		TT_KHOI_DUNG=("Bị thay thế", "Đã huỷ"), nhom_cho_dung=nhom_cho_dung, NHOM_CHO_DUNG=NHOM_CHO_DUNG,
		rut_gon_loi=lambda s: s)
	exec(compile(ast.Module(body=ham, type_ignores=[]), "minvoice_chung_tu.py", "exec"), env)
	return env["cho_dung_phieu_mua"], goi


@ca("#352 cửa thanh báo: chỉ tờ đầu vào chưa có phiếu mua, dò phiếu một truy vấn cho cả lô, tổng và nhóm đúng")
def _cua_cho_dung():
	hd = [
		{"name": "A", "so_hd": "1", "ngay_lap": "2026-09-10", "nguoi_mua_ban": "MOBIFONE", "tong_tien": 159000,
			"ly_do_bo_qua": "chưa xác định được quy đổi đơn vị nhà cung cấp '(trống)'", "da_tao_chung_tu": 0},
		{"name": "B", "so_hd": "2", "ngay_lap": "2026-09-11", "nguoi_mua_ban": "Duy Lợi", "tong_tien": 500000,
			"ly_do_bo_qua": "", "da_tao_chung_tu": 1},
		{"name": "C", "so_hd": "", "ngay_lap": "2026-09-12", "nguoi_mua_ban": "X", "tong_tien": -99000,
			"ly_do_bo_qua": "", "da_tao_chung_tu": 0},
	]
	cua, goi = _nap_cua(hd, pi=["B"])
	kq = cua()
	la("bỏ tờ đã có phiếu mua", [h["ma"] for h in kq["ds"]], ["A", "C"])
	la("tổng tiền theo trị tuyệt đối", kq["tong_tien"], 258000.0)
	la("nhóm theo thứ tự việc", [(o["nhom"], o["so_to"]) for o in kq["theo_nhom"]], [("thieu_nguon", 1), ("quy_cach", 1)])
	la("dò phiếu mua đúng một lần cho cả lô", [g[0] for g in goi], ["MInvoice Invoice", "MInvoice Invoice", "Purchase Invoice"])
	loc = goi[0][1]
	la("chỉ đầu vào, bỏ tờ đã huỷ hoặc bị thay thế", (loc["loai"], loc["trang_thai"]), ("Đầu vào", ["not in", ["Bị thay thế", "Đã huỷ"]]))


@ca("#357 Codex: tờ nguồn rút gọn lưu với ngày trống vẫn vào thanh báo, nhóm chờ nguồn; không đếm trùng")
def _vo_khong_ngay():
	vo = [{"name": "V", "so_hd": None, "ngay_lap": None, "nguoi_mua_ban": "", "tong_tien": 0, "ly_do_bo_qua": "", "da_tao_chung_tu": 0},
		{"name": "A", "so_hd": "1", "ngay_lap": "2026-09-10", "nguoi_mua_ban": "X", "tong_tien": 5, "ly_do_bo_qua": "", "da_tao_chung_tu": 0}]
	hd = [vo[1]]
	cua, goi = _nap_cua(hd, pi=[], vo=vo)
	kq = cua()
	la("tờ chưa có ngày có trong danh sách, không trùng tờ A", sorted(h["ma"] for h in kq["ds"]), ["A", "V"])
	la("đếm vào nhóm chờ nguồn", [(o["nhom"], o["so_to"]) for o in kq["theo_nhom"]][0], ("thieu_nguon", 1))
	loc = [g[1] for g in goi if g[0] == "MInvoice Invoice"][1]
	la("tờ chưa có ngày giới hạn theo ngày tạo cùng cửa sổ", loc["creation"], [">=", "2026-03-26"])
