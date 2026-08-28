# -*- coding: utf-8 -*-
"""Hàng rào tài khoản kho cho phiếu nhập kho.

VÌ SAO CÓ TỆP NÀY, ngày 28/08/2026
--------------------------------------------------------------------
Chị Dung soi sổ cái phiếu PNK-2026-00224 và báo:

    *"Phiếu nhập kho phải vào 152 chứ không phải vào 155 á em, 155 là
    thành phẩm khi mình xuất bán thôi."*

Tờ đó nhập 1 thùng khay giấy kraft 2.080.000 đ, một món công cụ dụng
cụ mua của Eco Pro, mà sổ cái ghi:

    Nợ  1551 - Sản phẩm nhập kho      2.080.000
        Có   3311 - Phải trả người bán    2.080.000

Trong khi tờ PNK-2026-00168 cùng một nhà cung cấp, cùng loại hàng, lại
ghi đúng vào 152.

VÌ SAO LỆCH
--------------------------------------------------------------------
Không phải do món, cũng không phải do người nhập gõ sai. Với tồn kho
vĩnh viễn, phiếu nhập kho ghi Nợ vào TÀI KHOẢN CỦA KHO nhận hàng, đọc
từ ô `account` của Warehouse. Hai tờ đi vào hai kho khác nhau:

    PNK-2026-00168  ->  Kho tổng 307   ->  152   đúng
    PNK-2026-00224  ->  Kho D1         ->  1551  sai

Ô `account` của Kho D1 đang trỏ vào 1551. Nghĩa là MỌI thứ mua về nhập
Kho D1 đều rơi vào tài khoản thành phẩm, không riêng tờ này.

CÁI KHÓ THẬT SỰ
--------------------------------------------------------------------
Kho D1 là kho của một điểm bán, nó chứa CẢ HAI thứ: vật tư mua về
(nguyên liệu, bao bì, công cụ) và bánh thành phẩm chuyển từ bếp sang
để bán. Mà ERPNext chỉ cho MỘT tài khoản cho một kho. Chọn 152 thì
bánh thành phẩm nằm sai, chọn 1551 thì vật tư nằm sai. Đổi ô đó sang
152 không phải là chữa, chỉ là dời chỗ sai.

Cách chữa tận gốc là tách kho theo bản chất hàng, việc đó đụng tới vận
hành nên phải để anh Việt và chị Dung quyết, không phải việc của một
phiên code. Xem `soat_kho()` ở cuối tệp, nó liệt kê ra để hai anh chị
nhìn số mà quyết.

HÀNG RÀO NÀY LÀM GÌ
--------------------------------------------------------------------
Chốt đúng một luật kế toán, luật này không phụ thuộc cấu hình kho:

    Phiếu nhập kho KHÔNG BAO GIỜ được ghi Nợ vào 155x.

Vì 155 theo TT200 là thành phẩm DO CHÍNH DOANH NGHIỆP SẢN XUẤT RA. Thứ
mình mua của người khác thì là 152 nguyên vật liệu, 153 công cụ dụng
cụ, hay 156 hàng hoá - không có đường nào thành 155 cả. Đúng câu chị
Dung nói.

Luật này không cần danh sách nhóm món, nên nhóm món mới sinh ra sau
này cũng được canh. Và nó chỉ chặn chiều MUA VÀO: bánh từ bếp chuyển
sang Kho D1 đi bằng phiếu chuyển kho, không qua hàng rào này, nên vẫn
vào 1551 đúng như phải thế.

Phần thuần nằm trên vạch, phần chạm Frappe nằm dưới, để bộ kiểm chạy
được trên máy CI tay không.
"""

# Đầu số tài khoản thành phẩm theo TT200. 155 là thành phẩm tự sản
# xuất, 1551 và 1557 là hai tài khoản con của nó.
DAU_THANH_PHAM = "155"

# Ba kết luận của phép soi một dòng.
TK_OK = "ok"                    # tài khoản kho dùng được cho hàng mua về
TK_TRONG = "trong"              # kho chưa khai tài khoản, ERPNext lấy mặc định công ty
TK_THANH_PHAM = "thanh_pham"    # kho trỏ vào 155x, hàng mua về không được vào đây


def so_hieu(tk):
	"""Số hiệu tài khoản, cắt khỏi tên đầy đủ. THUẦN.

	Tên tài khoản của Frappe có dạng "1551 - Sản phẩm nhập kho - TV".
	Chỉ lấy phần trước dấu gạch đầu tiên, và bỏ khoảng trắng hai đầu.
	"""
	return str(tk or "").split("-")[0].strip()


def la_tk_thanh_pham(tk):
	"""Tài khoản này có phải tài khoản thành phẩm không. THUẦN."""
	return so_hieu(tk).startswith(DAU_THANH_PHAM)


def soi_dong(tk_kho):
	"""Kho có tài khoản này thì nhận hàng mua về được không. THUẦN."""
	if not str(tk_kho or "").strip():
		return TK_TRONG
	if la_tk_thanh_pham(tk_kho):
		return TK_THANH_PHAM
	return TK_OK


def loi_thanh_pham(idx, ten_mon, ten_kho, tk_kho):
	"""Câu báo cho người đang đứng nhập kho. THUẦN.

	Người đọc câu này là bạn thủ kho lúc xe hàng vừa tới, nên câu phải
	nói RÕ phải làm gì tiếp, và nói ai là người sửa được.
	"""
	return (
		"Dòng %s, món %s đang nhập vào kho %s. Kho này đang ghi sổ vào "
		"tài khoản %s, là tài khoản THÀNH PHẨM dành cho bánh do bếp làm ra. "
		"Hàng mua của nhà cung cấp không được vào tài khoản này.<br><br>"
		"Cách xử lý: chọn một kho vật tư để nhận hàng, ví dụ Kho tổng 307. "
		"Nếu hàng bắt buộc phải nhập đúng kho này thì nhờ chị Dung sửa ô "
		"Tài khoản của kho %s sang tài khoản 152 hoặc 153 rồi nhập lại."
		% (idx, ten_mon, ten_kho, tk_kho, ten_kho)
	)


# ------------------------------------------------------- phần cần Frappe

import frappe


def _tk_cua_kho(ten_kho):
	"""Tài khoản ghi sổ của một kho, đọc từ Warehouse."""
	if not ten_kho:
		return ""
	return frappe.db.get_value("Warehouse", ten_kho, "account") or ""


def chan_nhap_vao_thanh_pham(doc, method=None):
	"""Chặn ghi sổ phiếu nhập kho khi kho nhận trỏ vào tài khoản 155x.

	Gắn ở `before_submit` chứ không phải `validate`: lưu nháp thì cứ cho
	lưu, người ta còn đang gõ dở. Chỉ chặn đúng lúc sắp ghi vào sổ cái,
	vì đó mới là lúc con số chạm tài khoản.

	Phiếu trả hàng thì bỏ qua. Trả hàng là đảo ngược một tờ cũ, chặn ở
	đây thì tờ nhập sai ngày trước không sửa được nữa.
	"""
	if doc.get("is_return"):
		return
	loi = []
	da_soi = {}
	for r in doc.get("items") or []:
		kho = r.get("warehouse")
		if not kho:
			continue
		if kho not in da_soi:
			da_soi[kho] = _tk_cua_kho(kho)
		tk = da_soi[kho]
		if soi_dong(tk) != TK_THANH_PHAM:
			continue
		loi.append(loi_thanh_pham(
			r.idx, r.get("item_name") or r.get("item_code"), kho, tk
		))
	if loi:
		frappe.throw(
			"Phiếu nhập kho đang ghi vào tài khoản thành phẩm:<br><br>"
			+ "<br><br>".join(loi),
			title="Sai tài khoản kho",
		)


@frappe.whitelist()
def soat_kho():
	"""Soi mọi kho: kho nào trỏ sai tài khoản, kho nào lẫn hai loại hàng.

	Chỉ ĐỌC, không sửa gì. Dựng cho anh Việt và chị Dung nhìn số mà quyết
	có tách kho hay không - đây là quyết định vận hành, không phải việc
	một phiên code tự làm.

	Hai cột đáng nhìn nhất:
	  `nhan_mua_vao`  số dòng phiếu nhập kho đã vào kho này
	  `lan_lon`       kho vừa chứa vật tư mua về vừa chứa thành phẩm
	"""
	if not ({"System Manager", "Accounts Manager", "Accounts User", "Stock Manager"}
	        & set(frappe.get_roles())):
		frappe.throw("Chỉ kế toán hoặc quản lý kho mới xem được bản soát kho.")

	ra = []
	for k in frappe.get_all(
		"Warehouse",
		filters={"is_group": 0, "disabled": 0},
		fields=["name", "account", "company"],
		limit_page_length=0,
	):
		tk = k.get("account") or ""
		ket = soi_dong(tk)
		so_mua = frappe.db.count(
			"Purchase Receipt Item",
			{"warehouse": k["name"], "docstatus": 1},
		)
		ra.append({
			"kho": k["name"],
			"tai_khoan": tk,
			"ket_luan": ket,
			"nhan_mua_vao": so_mua,
			# Kho tro vao 155x MA VAN nhan hang mua ve la kho dang ghi sai
			# tung ngay, khong phai nguy co xa xoi.
			"dang_ghi_sai": 1 if (ket == TK_THANH_PHAM and so_mua) else 0,
		})
	ra.sort(key=lambda x: (-x["dang_ghi_sai"], -x["nhan_mua_vao"], x["kho"]))
	return {
		"kho": ra,
		"so_kho_ghi_sai": sum(1 for x in ra if x["dang_ghi_sai"]),
	}
