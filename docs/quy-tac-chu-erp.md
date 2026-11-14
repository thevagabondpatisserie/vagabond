# Quy tắc chữ trên ERP Vagabond

Anh Việt duyệt 14/11/2026 (v657). Áp cho mọi chữ người dùng nhìn thấy: nút, nhãn, trạng thái, thông báo, câu lỗi, tin Zalo, sổ tay, mẫu in.

Bản này nối tiếp những gì đã có, không thay: 18 điều thiết kế màn hình (AGENTS 2b), quy ước sổ tay, skill thiết kế tiện lợi.

---

## Phần A. Bảy điểm anh Việt đã chốt (14/11/2026)

| # | Điểm | Đã chốt |
|---|---|---|
| 1 | Chữ trên app gọi người bằng gì | Gọi theo **bộ phận hoặc chức danh**, không gọi tên người (bảng B1). |
| 2 | Chủ tiệm xuất hiện trên app với tên gì | **Giám đốc** cho việc chính sách (giá, giảm giá, ai được làm gì). **Quản trị hệ thống** cho cấp quyền, cài đặt, lỗi kỹ thuật. |
| 3 | Gọi phần mềm là gì | **Hệ thống**. Giữ "máy" cho đồ vật thật: máy in, máy cà thẻ, máy chủ. |
| 4 | Xưng hô | **Không xưng hô** khi viết được dạng việc cần làm. Cần chủ ngữ thì dùng **"bạn"**. Bỏ "anh chị", bỏ "vui lòng" chồng chất. |
| 5 | Nút gửi phiếu sang bộ phận khác | **"Gửi" + bộ phận nhận** (Gửi Kế toán). Trạng thái tương ứng **Chờ + bộ phận** (Chờ Kế toán). |
| 6 | Chính tả | Giữ kiểu **hoá, huỷ, xoá, thuỷ**. Tên mẫu chứng từ in ra chép đúng tên trong thông tư. |
| 7 | Viết tắt | **Không viết tắt** NCC, BTP, BOM, PNK trên nhãn, nút, tiêu đề, câu thông báo. Chỉ cho phép trong mã chứng từ và chip dưới 16 ký tự (AGENTS 2b.18). "BOM" không bao giờ hiện, luôn là "Công thức". |

Câu chữ cũ chưa đúng các điểm 3, 4, 7 được sửa dần khi đụng tới màn đó; câu MỚI phải đúng ngay. Điểm 1 có ca kiểm chặn (`thu_quy_tac_chu_657.py`), số chỗ "BOM", "NCC" trên giao diện chỉ được giảm.

---

## Phần B. Quy tắc

### B1. Không tên người, chỉ tên vai

Người nghỉ, người đổi việc thì chữ trên app sai ngay. Odoo bản tiếng Việt cũng làm vậy: nút gửi duyệt của Odoo ghi "Gửi cho quản lý", không ghi tên ai.

| Đang ghi | Ghi thành | Dùng khi |
|---|---|---|
| anh Việt (chính sách) | Giám đốc | Giá, giảm giá, hoàn tiền, ai được nhận gì |
| anh Việt (kỹ thuật) | Quản trị hệ thống | Cấp chức vụ, khai kho phụ trách, lỗi cài đặt, deploy |
| chị Dung | Kế toán trưởng | Tài khoản kế toán, duyệt chứng từ, hoá đơn điện tử |
| Khải | Kế toán (trên nút, chip) / Kế toán giá thành (trong câu giải thích) | Công thức, giá vốn, kiểm kê |
| Uyên | Thu mua | Đơn mua, công nợ nhà cung cấp |
| Hân, Linh | Bếp, hoặc Bếp Pastry, Bếp Baker | Lệnh sản xuất, công thức nháp |

Cách viết hoa:
- **Bộ phận** viết hoa chữ đầu như tên riêng: Kế toán, Thu mua, Bếp, Kho, Kho tổng, Quầy, Marketing.
- **Chức danh** viết thường trong câu: "báo kế toán trưởng", "chỉ giám đốc được duyệt". Đứng đầu nhãn thì viết hoa chữ đầu như mọi nhãn.

Ngoại lệ được giữ tên người: tên người lập, người duyệt, người ghi sổ trong dấu vết phiếu (AGENTS 2b.11), vì đó là dữ liệu chứ không phải câu chữ của app.

### B2. Thứ tự chọn chữ

Khi phân vân giữa nhiều cách gọi một thứ, chọn theo thứ tự:

1. **Tên trên mẫu chứng từ của Thông tư 99/2025** nếu thứ đó là chứng từ kế toán: Phiếu nhập kho (01-VT), Phiếu xuất kho (02-VT), Phiếu thu (01-TT), Phiếu chi (02-TT), Giấy đề nghị tạm ứng (03-TT), Giấy đề nghị thanh toán (05-TT).
2. **Chữ tiệm đang nói hằng ngày** và đã có trên app: Món, Bếp, Kho tổng, Bán thành phẩm, Lệnh sản xuất, Xuất điều chuyển.
3. **Chữ của Odoo và MISA bản tiếng Việt** (bảng B4).
4. **Không bao giờ lấy bản dịch máy của ERPNext.** Bản tiếng Việt gốc của ERPNext dịch sai nhiều chữ nghiệp vụ, ví dụ Bill of Materials thành "Hóa đơn vật liệu", Credit Note thành "Ghi chú tín dụng", On Hand thành "Trong tay", Work Order thành "Đơn hàng công việc".

### B3. Một việc một chữ

Cùng một việc mà mỗi màn gọi một kiểu thì người dùng nghĩ là hai việc khác nhau.

**Nút (động từ, nói đúng việc sẽ xảy ra):**

| Chữ | Nghĩa | Không dùng |
|---|---|---|
| Tạo, Thêm | Tạo phiếu mới; thêm dòng vào phiếu | Mới, Tạo mới |
| Lưu nháp | Lưu, chưa ai nhận, chưa vào sổ | Lưu tạm, Cất |
| Gửi + bộ phận | Chuyển phiếu cho bộ phận khác xử lý | Gửi Khải, Trình, Submit |
| Duyệt | Người có quyền đồng ý | Phê duyệt (dài), OK |
| Trả lại | Trả phiếu về người lập, bắt buộc kèm câu hỏi hoặc lý do | Từ chối (khi người lập còn sửa được) |
| Từ chối | Không làm việc này nữa, phiếu dừng | Huỷ (khi chưa vào sổ) |
| Ghi sổ | Chứng từ chính thức vào sổ kho, sổ tiền; sau đó không sửa | Xác nhận, Đăng, Vào sổ, Submit |
| Hoàn tất | Lệnh sản xuất xong: trừ nguyên liệu, nhập thành phẩm | Hoàn thành |
| Huỷ chứng từ | Huỷ phiếu đã ghi sổ (ERPNext Cancel) | Xoá |
| Xoá | Chỉ cho phiếu nháp hoặc một dòng chưa lưu | Huỷ |

MISA dùng cặp **Ghi sổ / Bỏ ghi**, Odoo dùng **Vào sổ**. App mình đã dùng **Ghi sổ** ở hơn 100 chỗ, giữ nguyên.

Nút trong hộp hỏi lại phải **nhắc lại động từ và số lượng**: "Ghi sổ 3 phiếu", "Huỷ phiếu PDC-26-11-0012". Không dùng "OK", "Đồng ý", "Có".

**Trạng thái (đã xảy ra hoặc đang chờ), dùng chung mọi loại phiếu:**

Màu giữ đúng bốn màu của AGENTS 2b.3: xanh xong, vàng chờ, đỏ cần xử lý, xám dừng.

| Trạng thái | Màu chip | Ghi chú |
|---|---|---|
| Nháp | Xám | Chưa gửi ai |
| Chờ + bộ phận | Vàng | Chờ Kế toán, Chờ Thu mua, Chờ Kho tổng giao |
| Trả lại | Đỏ | Người lập phải sửa; kèm câu hỏi của người trả |
| Đã duyệt | Xanh | Loại phiếu duyệt xong mới ghi sổ |
| Đã ghi sổ | Xanh | Không sửa được nữa |
| Đã hoàn tất | Xanh | Riêng lệnh sản xuất |
| Từ chối | Xám | Phiếu dừng |
| Đã huỷ | Xám | |

Nút và trạng thái không dùng chung một chữ trần: nút "Ghi sổ" thì trạng thái "Đã ghi sổ".

### B4. Từ điển thuật ngữ

Cột "Odoo" là chữ trong bản dịch tiếng Việt chính thức của Odoo 18. Cột "ERPNext gốc" là bản dịch tiếng Việt kèm ERPNext v16. Cột cuối là chữ app mình dùng.

| Tiếng Anh | Odoo | ERPNext gốc | App Vagabond dùng |
|---|---|---|---|
| Item | Sản phẩm | Mặt hàng | **Món** (bán ra), **Nguyên liệu** (mua vào), **Mặt hàng** (nói chung cả hai) |
| Bill of Materials | Định mức nguyên liệu | Hóa đơn vật liệu ❌ | **Công thức** |
| Component | Thành phần | Thành phần | **Thành phần** |
| Work Order | Lệnh sản xuất (Odoo gọi là Manufacturing Order) | Đơn hàng công việc ❌ | **Lệnh sản xuất** |
| Material Request | | Yêu cầu vật tư | **Phiếu xin nguyên liệu** (bếp xin kho), **Phiếu yêu cầu mua hàng** (gửi Thu mua) |
| Purchase Order | Đơn mua hàng | Đơn mua hàng | **Đơn mua hàng** |
| Purchase Receipt | Phiếu nhập kho (Odoo gọi là Receipt) | Biên nhận mua hàng ❌ | **Phiếu nhập kho** |
| Purchase Invoice | Hóa đơn mua hàng (Vendor Bill) | | **Hoá đơn mua vào** |
| Sales Invoice | Hóa đơn bán hàng | | **Hoá đơn bán ra** |
| Stock Entry (chuyển kho) | Luân chuyển nội bộ | Bút toán tồn kho ❌ | **Phiếu xuất điều chuyển** |
| Stock Reconciliation | Điều chỉnh tồn kho (Inventory Adjustment) | Đối soát tồn kho | **Phiếu kiểm kê** |
| Journal Entry | Bút toán | Bút toán nhật ký | **Bút toán** |
| Chart of Accounts | Hệ thống tài khoản | | **Hệ thống tài khoản** (đúng chữ Thông tư 99) |
| Supplier | Nhà cung cấp | Nhà cung cấp | **Nhà cung cấp** (không NCC) |
| Unit of Measure | Đơn vị tính | Đơn vị đo | **Đơn vị tính** (đúng cột trên phiếu nhập kho) |
| Batch, Lot | Lô | Lô | **Lô** |
| On Hand | Hiện có | Trong tay ❌ | **Tồn** |
| Cost of Goods Sold | Giá vốn hàng bán | Giá vốn hàng bán | **Giá vốn** |
| Credit Note | Giấy báo có | Ghi chú tín dụng ❌ | **Hoá đơn điều chỉnh giảm** |
| Bank Statement | Sao kê ngân hàng | Sao kê ngân hàng | **Sao kê** |
| Reconcile (ngân hàng, cổng thanh toán) | Đối chiếu | Đối soát | **Đối soát** |
| Reconcile (công nợ đối tác) | | | **Đối chiếu công nợ** (đúng tên biên bản) |
| To Do | Việc cần làm | Việc cần làm | **Việc cần làm** |
| Settings | Cài đặt | Thiết lập | **Cài đặt** |
| Attachment | Tệp đính kèm | Tệp đính kèm | **Ảnh chứng từ** (khi là ảnh), **Tệp đính kèm** |

Chữ tiếng Anh đã thành tên riêng thì giữ: Pancake, Ahamove, OnePay, m-invoice, Zalo, Desk.

Không dùng tiếng lóng nội bộ trên app: "bên Next" ghi thành "trên Desk"; "Bank Account" ghi thành "tài khoản ngân hàng".

### B5. Câu thông báo và câu lỗi

Khuôn ba vế, tối đa hai câu:

**Chuyện gì không được** + **làm gì để gỡ** + (nếu người dùng không tự gỡ được) **bộ phận nào giúp**.

- Không "Đã xảy ra lỗi" trơn, không mã lỗi, không tên trường máy.
- Không đổ lỗi người dùng ("Bạn nhập sai"). Nói thứ cần sửa: "Số lượng phải lớn hơn 0".
- Không viết hoa cả chữ để doạ ("KHÔNG", "PHẢI"). Cần nhấn thì in đậm.
- Câu hỏi lại trước việc không quay lại được phải nói hậu quả: "Ghi sổ rồi thì không sửa được. Ghi sổ 3 phiếu?"
- Báo thành công ngắn, nói kết quả: "Đã ghi sổ PNK-26-11-0042", không "Thành công!".
- Câu lỗi lõi ERPNext (bản dịch máy) dịch lại thành việc cần làm, giữ lớp lỗi gốc (đã có ở quy tắc dự án mục F).

### B6. Số, ngày, tiền

Giữ như AGENTS 2b.14: tiền có dấu chấm nghìn và chữ đ (120.000 đ), ngày dd/mm, giờ HH:MM, khối lượng qua hàm chung. Không dấu gạch dài.

---

## Phần C. Ví dụ đã sửa ở v657 (chữ thật trên app)

| Đang có | Sửa thành |
|---|---|
| 📤 Gửi Khải | 📤 Gửi Kế toán |
| Chờ Khải | Chờ Kế toán |
| Khải hỏi lại phiếu đề xuất công thức | Kế toán trả lại phiếu đề xuất công thức |
| Chỉ Khải (quản lý công thức), bếp trưởng hoặc giám đốc làm bước này. | Chỉ kế toán giá thành, bếp trưởng hoặc giám đốc làm được bước này. |
| Nhờ chị Dung tạo Bank Account cho họ bên Next rồi quay lại chọn. | Người này chưa có tài khoản ngân hàng. Nhờ Kế toán tạo trên Desk rồi chọn lại. |
| Cần dùng thì báo anh Việt cấp thêm chức vụ trong màn Quản lý người dùng. | Tài khoản của bạn chưa có chức vụ dùng màn này. Báo quản trị hệ thống cấp thêm. |
| Bản build trên máy chủ chưa có thư viện gửi. Báo anh Việt deploy bản mới nhất. | Hệ thống chưa gửi được thông báo. Báo quản trị hệ thống cập nhật phiên bản. |
| Máy KHÔNG tự động xử lý bên m-invoice, chị Dung phải làm tay. | Hệ thống không tự xử lý bên m-invoice. Kế toán làm tay trên m-invoice. |
| Màn Sản xuất: nút "Hoàn tất", hộp mở ra ghi "Hoàn thành phiếu", nút "✅ Hoàn thành" | Cả ba thống nhất "Hoàn tất" |
| Sổ tay: "Việc này do anh Việt quyết." | "Việc này do giám đốc quyết." |

---

## Phần D. Cách giữ quy tắc

1. Skill "Thiết kế tiện lợi" của Claude chứa bộ quy tắc này; Codex đọc tệp này qua AGENTS.md mục 2b.
2. Ca kiểm `vagabond/khung/kiem_thu/thu_quy_tac_chu_657.py` đỏ khi chuỗi hiển thị (Python, JS, doctype JSON, sổ tay) gọi tên người, và khi số chỗ "BOM", "NCC" trong chuỗi giao diện tăng so với mốc.
3. Công cụ sửa một lần đã chạy xong (bản vá cũ, công cụ #225, #252) giữ nguyên chữ vì chuỗi nằm trong mã xác nhận hoặc nhật ký đã ghi; ca kiểm liệt kê chúng kèm lý do.

---

## Nguồn đã đối chiếu

- Bản dịch tiếng Việt chính thức của Odoo 18 (các phân hệ kho, mua, bán, sản xuất, kế toán, chi phí, POS, giao diện chung): github.com/odoo/odoo, thư mục `addons/*/i18n/vi.po`.
- Bản dịch tiếng Việt kèm ERPNext và Frappe v16: github.com/frappe/erpnext `erpnext/locale/vi.po`, github.com/frappe/frappe `frappe/locale/vi.po`.
- MISA AMIS Kế toán, ý nghĩa nút Ghi sổ, Bỏ ghi: https://helpact.misa.vn/?p=79481
- Danh mục mẫu chứng từ theo Thông tư 99/2025/TT-BTC: https://luatvietnam.vn/thue-phi-le-phi/huong-dan-tai-toan-bo-bieu-mau-tai-thong-tu-99-ve-che-do-ke-toan-565-105800-article.html và https://amis.misa.vn/251419/mau-chung-tu-ke-toan-theo-thong-tu-99-2025-btc/
- SAP: có gói tiếng Việt cho SAP ERP nhưng doanh nghiệp ở Việt Nam chủ yếu chạy giao diện tiếng Anh, nên SAP chỉ dùng để tham khảo cách chia vai và luồng duyệt, không lấy chữ.
