# Luật riêng của bộ kiểm thử tích hợp (bench)

## Không đụng dữ liệu thật (#592, 22/11/2026)

- Ca bench có thể chạy trên site thật. Ca không được đọc, cập nhật hay ghi sổ bản ghi thật.
- Cách ly khoá bản ghi tháng bằng hậu tố riêng (xem `_cach_ly` trong `thu_chi_phi_674.py`) và lọc nguồn dữ liệu về đúng bản ghi của ca.
- Hàm lịch gọi trong ca phải nhận danh sách bản ghi của ca (ví dụ `noi_sao_ke_con_thieu(chi_phieu=...)`).
- Có phép kiểm chứng minh bản ghi thật giữ nguyên trạng thái ban đầu.
- Mô tả, tên, số tài khoản trong ca là dữ liệu GIẢ cùng dạng.
- Đổi thuế, giá vốn, thanh toán: theo cổng kế toán [H10.5](/docs/van-hanh-agent/nghiem-thu-va-ra.md).

<!-- Chuyển nguyên văn ngày 22/11/2026 (PR luật gọn), từ AGENTS.md dòng 538 tới 586. Luật gốc: [AGENTS.md](/AGENTS.md). -->

### Tầng hai: KIỂM THỬ TÍCH HỢP, bắt buộc với sổ cái và tồn kho

**Tầng một không bao giờ chứng minh được rằng hệ lõi chấp thuận việc mình
làm.** Ngày 21/08/2026 nó trả về 0 trong khi cả tiệm không nhập được hàng:
hàm `gan_doi_tac` chạy đúng răm rắp, chỉ có điều ERPNext từ chối cái nó
vừa điền. Mock và unit test thuần mù trước loại lỗi đó.

Nên: **mọi thay đổi chạm tới GL Entry hoặc Stock Ledger Entry tuyệt đối
không được chỉ có unit test.** Bắt buộc có ca kiểm tích hợp trong
`vagabond/khung/kiem_that/`, và ca đó phải:

1. Dựng chứng từ thật (Purchase Receipt, Stock Entry, Sales Invoice...).
2. Gọi `insert()` rồi `submit()` **ghi thẳng xuống cơ sở dữ liệu**, để
   ERPNext chạy trọn chuỗi validation của nó.
3. **Frappe hay ERPNext ném lỗi thì ca kiểm ĐỎ**, kèm nguyên văn câu lỗi.
4. Đọc lại sổ cái vừa sinh ra và chốt từng điều kiện mình cần.

Chạy nó trên site thật:

```
bench --site <site> execute vagabond.khung.kiem_that.cua.chay
```

hoặc gọi cửa `vagabond.khung.kiem_that.cua.chay` từ Desk. Chỉ giám đốc và
System Manager mở được.

**Ba lớp bảo vệ dữ liệu thật, không được gỡ cái nào:**

- **Điểm lưu.** Mỗi ca chạy trong một `frappe.db.savepoint`, xong thì
  `frappe.db.rollback(save_point=...)`. Chứng từ ảo tồn tại thật lúc chạy
  rồi biến mất hoàn toàn.
- **Khoá tay lái giao dịch.** `frappe.db._disable_transaction_control` bật
  suốt lúc chạy, để một lời gọi `commit()` lạc trong hook nào đó không ghi
  chứng từ ảo vào sổ thật. Ca kiểm tự gọi `commit` là phá hỏng cả tầng
  này, và có ca kiểm tầng khung dò bằng AST để chặn.
- **Cấm gửi ra ngoài.** Cờ `frappe.flags.vagabond_kiem_that` bật suốt lúc
  chạy; `thong_bao.gui` đọc cờ đó rồi im lặng. Điểm lưu lùi được một dòng
  cơ sở dữ liệu, không lùi được một cái chuông đã kêu trên điện thoại
  người thật.

Kết quả trả về có hai khoá **phải luôn rỗng**: `chung_tu_con_sot` và
`so_luong_lech`. Không rỗng nghĩa là có chứng từ thử nằm lại trong sổ
thật, phải đi dọn ngay và báo anh Việt, không được bỏ qua.

**Không ca kiểm tích hợp nào được chạm tới hoá đơn điện tử đã gửi cơ quan
thuế, và không ca nào được sửa dữ liệu quá khứ.**

---
