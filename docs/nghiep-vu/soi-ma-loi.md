# Soi mã nguồn gốc ERPNext, Frappe trước khi can thiệp

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 447 tới 511. Luật gốc: [AGENTS.md](/AGENTS.md). -->

## 5. Soi mã nguồn gốc trước khi can thiệp vào lõi

**Không có tài liệu nào tốt bằng chính mã nguồn.** Quy tắc này sinh ra ngày
21/08/2026, sau khi cả tiệm không nhập được hàng vì một hook đúng đề bài
nhưng sai với luật của ERPNext.

Trước khi viết bất kỳ hook, lớp thay thế hay bản vá nào can thiệp vào các
doctype lõi của ERPNext - **Kế toán (GL Entry, Journal Entry, Payment
Entry), Tồn kho (Stock Ledger Entry, Bin, Stock Entry), Mua (Purchase
Receipt, Purchase Invoice, Purchase Order), Bán (Sales Invoice, Delivery
Note, Sales Order)** - bắt buộc làm hai bước sau, không được bỏ:

**Bước 1. Kéo mã nguồn gốc về máy.** Đúng nhánh mà site đang chạy:

```
mkdir -p /tmp/reference_repos
git clone --depth 1 -b version-16 https://github.com/frappe/frappe.git   /tmp/reference_repos/frappe
git clone --depth 1 -b version-16 https://github.com/frappe/erpnext.git  /tmp/reference_repos/erpnext
```

Đây là repo công khai, `--depth 1` nên chỉ mất chừng nửa phút. Số nhánh
phải khớp với phiên bản đang chạy, đọc ở Frappe Cloud, đừng đoán.

**Bước 2. Đọc thẳng vào hàm kiểm tra, trước khi đề xuất giải pháp.** Các
tệp phải soi tuỳ chỗ mình định chạm:

| Chạm vào | Đọc tệp |
|---|---|
| Bút toán, sổ cái | `erpnext/accounts/general_ledger.py`, `erpnext/accounts/doctype/gl_entry/gl_entry.py`, `erpnext/accounts/party.py` |
| Công nợ, cấn trừ | `erpnext/accounts/utils.py` (`get_payment_ledger_entries`), `erpnext/accounts/doctype/payment_entry/` |
| Chứng từ mua, bán | `erpnext/controllers/accounts_controller.py`, `erpnext/controllers/buying_controller.py`, `erpnext/controllers/selling_controller.py` |
| Tồn kho | `erpnext/stock/stock_ledger.py`, `erpnext/controllers/stock_controller.py` |
| Cơ chế nền | `frappe/model/document.py`, `frappe/database/database.py` |

Cách dò nhanh một câu báo lỗi thật đã gặp trên màn hình:

```
grep -rn "Receivable / Payable" --include=*.py /tmp/reference_repos/erpnext
grep -rn "def validate_" -A 12 /tmp/reference_repos/erpnext/accounts/doctype/gl_entry/gl_entry.py
```

**Câu phải tự hỏi và phải trả lời được bằng trích dẫn mã nguồn:** không
phải "code của mình có đúng không", mà **"hệ lõi có CHO PHÉP làm việc này
không"**. Hai câu đó khác nhau, và ngày 21/08/2026 mình chỉ hỏi câu thứ
nhất.

Ví dụ thật, chép nguyên từ `erpnext/accounts/party.py`:

```python
def validate_account_party_type(self):
	if self.party_type and self.party:
		account_type = frappe.get_cached_value("Account", self.account, "account_type")
		if account_type and (account_type not in ["Receivable", "Payable", "Equity"]):
			frappe.throw(_("Party Type and Party can only be set for Receivable / Payable account..."))
```

Mười một dòng này, đọc mất ba mươi giây, đáng lẽ đã tiết kiệm được một
buổi chiều cả tiệm không nhập được hàng.

Đọc xong thì **chép đoạn điều kiện vào chú thích đầu hàm của mình**, kèm
đường dẫn tệp. Sáu tháng nữa ERPNext đổi luật thì người sau còn biết chỗ
mà đối chiếu.

---
