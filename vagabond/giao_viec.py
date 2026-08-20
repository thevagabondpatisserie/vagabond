# -*- coding: utf-8 -*-
"""Gắn Assignee thật vào phiếu ngay lúc phiếu sinh ra.

Anh Việt 20/08/2026: *"Đảm bảo mỗi phiếu sinh ra phải được gắn cho đúng
một/một nhóm Assignee cụ thể"*, và 21/08/2026 xếp việc này thứ hai trong
danh sách còn nợ.

Vì sao cần lớp này khi đã có màn Việc cần làm
---------------------------------------------
`viec_can_lam.py` LỌC phiếu theo vai lúc người ta mở màn. Nó trả lời được
"việc này ai làm", nhưng chỉ trả lời khi có người hỏi. Ba thứ nó không làm
được, và đó đúng là ba thứ anh Việt đang thiếu:

  - Trên Desk và trong ERPNext, ô Assigned To vẫn trống. Chị Dung lọc theo
    Assigned To thì không ra gì.
  - Không có dấu vết ai được giao lúc nào. Phiếu tắc ba ngày thì không tra
    được nó tắc ở tay ai.
  - Không có cái để bắn thông báo theo. Chuông phải bám vào một việc được
    giao, chứ không bám vào một câu truy vấn.

Nên tệp này ghi việc giao xuống ToDo thật của Frappe (đúng bảng mà ô
Assigned To đọc), rồi mới bắn chuông.

Giao cho MỘT NHÓM chứ không cho một cái tên
-------------------------------------------
Cùng lý do đã ghi trong `de_nghi_chi.py`: viết cứng tên người duyệt thì ai
nghỉ phép là cả chuỗi tắc. Nên giao theo VAI, và mọi người đang giữ vai đó
đều nhận. Ai xử lý trước thì bước sau tự gỡ việc của cả nhóm.

KHÔNG BAO GIỜ ném lỗi ra ngoài
------------------------------
Mọi hàm ở đây được gọi từ giữa luồng lưu phiếu. Phiếu đã lưu xong rồi mà lời
gọi giao việc ném lỗi thì cả thao tác lưu bị cuốn theo - mất một việc thật
vì một cái nhãn. Nên tất cả đều nuốt lỗi và chỉ ghi log.
"""

import frappe

# Trần người nhận cho một phiếu. Một vai có 20 người mà giao hết thì hộp
# việc của ai cũng đầy rác và không ai coi là việc của mình nữa.
TRAN_NGUOI = 8


def _nguoi_theo_vai(vai):
	"""Những tài khoản CÒN BẬT đang giữ một trong các vai này.

	Đọc qua Has Role chứ không qua frappe.get_roles: get_roles hỏi ngược từ
	một người ra vai, ở đây cần hỏi xuôi từ vai ra người.
	"""
	ra = set()
	for v in sorted(vai or []):
		for r in frappe.get_all(
			"Has Role",
			filters={"role": v, "parenttype": "User"},
			fields=["parent"],
			limit_page_length=0,
		):
			ra.add(r["parent"])
	loc = set()
	for u in ra:
		if u in ("Administrator", "Guest"):
			continue
		if frappe.db.get_value("User", u, "enabled"):
			loc.add(u)
	return sorted(loc)


def _dang_giao(doctype, name):
	"""Ai đang được giao phiếu này và việc còn mở. Trả về tập email."""
	return {
		t["allocated_to"]
		for t in frappe.get_all(
			"ToDo",
			filters={
				"reference_type": doctype,
				"reference_name": name,
				"status": "Open",
			},
			fields=["allocated_to"],
			limit_page_length=0,
		)
		if t["allocated_to"]
	}


def go_giao(doctype, name, tru=None):
	"""Đóng việc đang mở của phiếu này, trừ những người trong `tru`.

	Gọi khi phiếu sang bước khác: người của bước cũ không còn phải làm gì.
	ĐÓNG chứ không xoá, theo QT-20 - dấu vết ai từng giữ phiếu phải còn.
	"""
	try:
		for t in frappe.get_all(
			"ToDo",
			filters={
				"reference_type": doctype,
				"reference_name": name,
				"status": "Open",
			},
			fields=["name", "allocated_to"],
			limit_page_length=0,
		):
			if tru and t["allocated_to"] in tru:
				continue
			frappe.db.set_value("ToDo", t["name"], "status", "Closed")
		_dong_bo_nhan(doctype, name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "giao_viec: go giao loi")


def _dong_bo_nhan(doctype, name):
	"""Viết lại ô _assign của phiếu cho khớp các việc còn mở.

	Ô _assign là thứ Desk và ERPNext đọc để hiện Assigned To. Nó là bản sao,
	nên phải chép lại mỗi lần đổi, không thì Desk hiện một đằng ToDo một nẻo.
	"""
	try:
		import json

		con = sorted(_dang_giao(doctype, name))
		frappe.db.set_value(
			doctype, name, "_assign", json.dumps(con) if con else None,
			update_modified=False,
		)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "giao_viec: dong bo _assign loi")


def giao(doctype, name, nguoi, mo_ta, han=None, doc_lap=1, bao=1):
	"""Giao phiếu cho một danh sách người. KHÔNG BAO GIỜ ném lỗi.

	doc_lap=1 nghĩa là đóng việc của người ngoài danh sách này trước, để
	phiếu chỉ nằm ở đúng một bước. Đó là mặc định, vì một phiếu vừa chờ kế
	toán vừa chờ giám đốc là một phiếu không ai biết đang chờ ai.
	"""
	try:
		nguoi = [u for u in dict.fromkeys(nguoi or []) if u]
		if not nguoi:
			return {"giao": 0, "vi_sao": "khong tim ra nguoi nao giu vai nay"}
		if len(nguoi) > TRAN_NGUOI:
			nguoi = nguoi[:TRAN_NGUOI]
		if doc_lap:
			go_giao(doctype, name, tru=set(nguoi))
		da_co = _dang_giao(doctype, name)
		them = [u for u in nguoi if u not in da_co]
		if them:
			from frappe.desk.form.assign_to import add

			add({
				"doctype": doctype,
				"name": name,
				"assign_to": them,
				"description": mo_ta,
				"date": han,
				"notify": 0,
				"assigned_by": frappe.session.user,
			})
		_dong_bo_nhan(doctype, name)
		if bao:
			_bao(nguoi, doctype, name, mo_ta)
		return {"giao": len(nguoi), "moi": len(them)}
	except Exception:
		frappe.log_error(frappe.get_traceback(), "giao_viec: giao loi")
		return {"giao": 0}


def giao_vai(doctype, name, vai, mo_ta, han=None, doc_lap=1, bao=1):
	"""Giao phiếu cho mọi người đang giữ một trong các vai này."""
	try:
		return giao(doctype, name, _nguoi_theo_vai(vai), mo_ta, han, doc_lap, bao)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "giao_viec: giao vai loi")
		return {"giao": 0}


def _bao(nguoi, doctype, name, mo_ta):
	"""Bắn chuông cho từng người vừa được giao."""
	try:
		from vagabond import thong_bao

		for u in nguoi:
			if u == frappe.session.user:
				# Không tự báo cho chính mình: mình vừa bấm xong, biết rồi.
				continue
			thong_bao.gui(
				u,
				"Có phiếu chờ bạn",
				mo_ta,
				"/bep",
				"%s:%s" % (doctype, name),
			)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "giao_viec: bao loi")


# ------------------------------------------------------------------ tra cứu
@frappe.whitelist()
def cua_toi(gioi_han=50):
	"""Việc đang giao cho chính người đang đăng nhập.

	Màn Việc cần làm dùng để đánh dấu dòng nào là việc ĐÍCH DANH của mình,
	tách khỏi những dòng chỉ hiện ra vì mình có vai đó.
	"""
	from vagabond.ban_hang import _kiem_quyen

	_kiem_quyen()
	ds = frappe.get_all(
		"ToDo",
		filters={"allocated_to": frappe.session.user, "status": "Open"},
		fields=["reference_type", "reference_name", "description", "date"],
		order_by="modified desc",
		limit_page_length=int(gioi_han or 50),
	)
	return {
		"dong": ds,
		"khoa": ["%s|%s" % (d["reference_type"], d["reference_name"]) for d in ds if d["reference_name"]],
	}


# ===================================================================
# GIAO TỰ ĐỘNG LÚC PHIẾU SINH RA
# ===================================================================
#
# Anh Việt 21/08/2026: *"gắn Assignee thật vào từng phiếu lúc sinh phiếu"*.
#
# Luật ở đây soi đúng vào các bộ lọc của `viec_can_lam.py`. Đó là cố ý: màn
# Việc cần làm và ô Assigned To phải nói CÙNG một câu. Hai nơi cùng trả lời
# "phiếu này của ai" mà trả lời khác nhau thì cả hai đều mất tin cậy.
#
# Giao cho ĐÚNG người giữ kho hoặc đúng bộ phận bếp khi biết được, chỉ khi
# không biết mới lùi về giao theo vai. Giao cả nhóm Kho cho một phiếu của
# một kho là làm phiền bảy người để một người làm.

# Trạng thái coi như hết việc: giao rồi thì phải biết đường gỡ ra.
XONG_MR = {"Ordered", "Transferred", "Received", "Issued", "Stopped", "Cancelled"}


def _nguoi_giu_kho(kho):
	"""Ai khai đang phụ trách kho này.

	Đọc `custom_kho_phu_trach` trên User - ĐÚNG trường mà viec_can_lam.py
	đọc, để không đẻ ra luật thứ hai về cùng một chuyện.
	"""
	if not kho:
		return []
	ra = []
	try:
		for u in frappe.get_all(
			"User",
			filters={"enabled": 1, "custom_kho_phu_trach": ("like", "%" + kho + "%")},
			fields=["name", "custom_kho_phu_trach"],
			limit_page_length=0,
		):
			ds = [k.strip() for k in (u.get("custom_kho_phu_trach") or "").split(",")]
			if kho in ds:
				ra.append(u["name"])
	except Exception:
		return []
	return ra


def _nguoi_bo_phan(bp):
	"""Ai thuộc bộ phận này. Dùng cho yêu cầu sản xuất gửi về một bếp."""
	if not bp:
		return []
	ra = []
	for truong in ("custom_phong_ban", "custom_bo_phan"):
		try:
			for u in frappe.get_all(
				"User", filters={"enabled": 1, truong: bp},
				fields=["name"], limit_page_length=0,
			):
				ra.append(u["name"])
		except Exception:
			continue
		if ra:
			break
	return ra


def _vai_kho():
	from vagabond.viec_can_lam import VAI_KHO

	return VAI_KHO


def khi_sinh_phieu(doc, method=None):
	"""Hook chung: phiếu vừa sinh ra thì giao ngay cho người phải xử lý.

	Đặt ở hooks.py cho từng doctype thay vì sửa mười chỗ tạo phiếu: phiếu
	sinh ra từ app, từ Desk, từ nút Create của ERPNext và từ đồng bộ - sửa
	chỗ tạo thì luôn sót một đường.

	KHÔNG BAO GIỜ ném lỗi.
	"""
	try:
		if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
			return
		# Hết việc thì GỠ, và gỡ trước khi tính giao. Nếu chỉ "không giao
		# thêm" thì phiếu kiểm kê đã chốt sổ vẫn nằm mãi trong hộp của kế
		# toán, và hộp việc đầy rác thì không ai coi nó là việc nữa.
		if _het_viec_chua(doc):
			go_giao(doc.doctype, doc.name)
			return
		nguoi, mo_ta = _ai_phai_lam(doc)
		if not nguoi:
			return
		giao(doc.doctype, doc.name, nguoi, mo_ta)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "giao_viec: khi sinh phieu loi")


def _het_viec_chua(doc):
	"""Phiếu này đã hết việc chưa. THUẦN theo nghĩa chỉ đọc trường của doc.

	Khai TỪNG doctype một, cố ý không viết luật chung "không tìm ra người
	nhận thì gỡ": luật chung đó sẽ xoá cả những lần người thật tự tay gán
	Assignee trên Desk, mà máy thì không biết là mình vừa xoá việc của ai.
	"""
	dt = doc.doctype
	if int(doc.get("docstatus") or 0) == 2:
		return True
	if dt == "Material Request":
		return (doc.get("status") or "") in XONG_MR
	if dt == "Purchase Receipt":
		return int(doc.get("docstatus") or 0) == 1
	if dt == "Phieu Kiem Ke":
		return (doc.get("trang_thai") or "") != "Chờ duyệt"
	return False


def khi_xong(doc, method=None):
	"""Hook chung: phiếu tới trạng thái hết việc thì gỡ khỏi hộp mọi người."""
	try:
		if int(doc.get("docstatus") or 0) == 2 or (doc.get("status") or "") in XONG_MR:
			go_giao(doc.doctype, doc.name)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "giao_viec: khi xong loi")


def _ai_phai_lam(doc):
	"""Trả về (danh sách người, mô tả việc) cho một phiếu. Rỗng thì không giao."""
	dt = doc.doctype

	if dt == "Material Request":
		loai = doc.get("material_request_type")
		if loai == "Purchase":
			from vagabond.viec_can_lam import VAI_GIAM_DOC, VAI_THU_MUA

			return (
				_nguoi_theo_vai(VAI_THU_MUA | VAI_GIAM_DOC),
				"%s: yêu cầu mua hàng chờ duyệt" % doc.name,
			)
		if loai == "Material Transfer":
			kho = doc.get("set_from_warehouse")
			nguoi = _nguoi_giu_kho(kho) or _nguoi_theo_vai(_vai_kho())
			return (
				nguoi,
				"%s: chờ soạn hàng từ %s" % (doc.name, kho or "kho gửi"),
			)
		if loai == "Manufacture":
			bep = doc.get("custom_bep_nhan")
			nguoi = _nguoi_bo_phan(bep)
			# Không đoán bừa khi không biết bếp nào: giao cả nhóm Kho cho một
			# phiếu sản xuất là giao nhầm người.
			return (nguoi, "%s: yêu cầu sản xuất cho %s" % (doc.name, bep or ""))
		return ([], "")

	if dt == "Purchase Receipt":
		kho = doc.get("set_warehouse")
		nguoi = _nguoi_giu_kho(kho) or _nguoi_theo_vai(_vai_kho())
		return (
			nguoi,
			"%s: phiếu nhập kho chờ đếm hàng (%s)" % (doc.name, doc.get("supplier_name") or ""),
		)

	if dt == "Phieu Kiem Ke":
		if (doc.get("trang_thai") or "") != "Chờ duyệt":
			return ([], "")
		from vagabond.viec_can_lam import VAI_GIAM_DOC, VAI_KE_TOAN

		return (
			_nguoi_theo_vai(VAI_KE_TOAN | VAI_GIAM_DOC),
			"%s: phiếu kiểm kê chờ chốt sổ (%s)" % (doc.name, doc.get("kho") or ""),
		)

	return ([], "")
