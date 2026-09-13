# Issue 206: kiểm chứng lô và giá vốn theo ý Khải

- Nguồn: [file và câu hỏi mới](https://github.com/thevagabondpatisserie/vagabond/issues/206#issuecomment-5651545788), [claim và bằng chứng site](https://github.com/thevagabondpatisserie/vagabond/issues/206#issuecomment-5651811587).
- Owner Codex, nhánh `codex/206-san-xuat-khai`, nền main `372b8d87b2631c4ded8a7cf7e8afd7185a6c3721` (v488), kiểm GitHub 13/09/2026.
- Anh Việt yêu cầu đọc ý Khải và lên PR cho Claude review. Phần này thêm ca tích hợp, chưa đổi cấu hình kho/dữ liệu/mã hàng. Không đóng toàn bộ #206 bằng PR này.

## Bằng chứng mới

Đã đọc cả ba Excel, hai ảnh mới và năm ảnh nhúng trong Pick LOT. File Pick LOT yêu cầu lấy hết lô cũ rồi bù lô mới: 704 g nhập cũ, 2000 g nhập mới, xuất 403.431 g hai lượt. Ảnh PSX-2026-00061 báo âm lô cũ 102.862 g.

Đọc site 13/09: chính PSX-2026-00061 vẫn nháp, sửa lần cuối 11/09 13:59, đã có hai dòng 300.569 g lô cũ và 102.862 g lô mới. Không submit hoặc save phiếu thật. Ảnh cũ không chứng minh lỗi chia lô còn tồn tại trên main hôm nay.

Claude nói cần tắt Batch mới có giá bình quân mã hàng. Mã nguồn ERPNext v16.28.0 `de591661b9ba0bd3f62ac25b99b5c85c723515f6`, `stock/serial_batch_bundle.py:prepare_batches` có nhánh Moving Average + `do_not_use_batchwise_valuation`. Cờ site đang 0. Nhánh đó giữ quản lý số lượng theo lô, tách khỏi định giá. Chưa bật cấu hình thật.

## Code và kiểm

Thêm ba ca trong `khung/kiem_that/thu_san_xuat_206.py`:

- Dựng Work Order, Batch và Stock Entry mới; xuất hai lượt theo đúng số Khải; đọc tồn lô từ SLE/gói, tiêu hao WO và giá trị kho/GL; huỷ ngược hai lượt, kiểm trả lại lô và sản lượng.
- Đối chứng giá lô: hai lô 10 x 1000 và 10 x 3000, xuất 4 từ lô cũ, giá vốn 4000 khi cờ tắt.
- Cùng nền Batch có định giá riêng, bật cờ sau nhập trong savepoint, xuất 4 vẫn từ lô cũ nhưng giá vốn bình quân 8000. Không dùng 0=0 làm bằng chứng giá vốn.

Local: preflight PASS; 2947/2947 tầng khung. CI và bench phải đọc từ PR trên SHA cuối, chưa coi code ca kiểm là bằng chứng đã chạy. Không sửa runtime hoặc bundle nên không tăng APPVER/patch cho phần kiểm này. Chưa merge/deploy.

## Nội dung Excel cần quyết định riêng

`Cau truc ma tien to...`, sheet SKU Mua vào: 58 mã NBTP00001..NBTP00058 (cấp 1/cấp 2). Sheet chú thích hỏi tách tiền tố hai cấp, BTPB dùng chung bánh/nước, BTPN là nền nước giữ tồn. Đây là câu hỏi/mapping đề xuất, không phải lệnh đổi mã hàng loạt.

Khải đề xuất HSD nội bộ tính từ ngày nhận + số ngày, HSD bao bì chỉ tham chiếu. Chưa đồng nhất đề xuất này với FEFO theo hạn thực tế. Không tự đổi luật hạn dùng.

Còn chờ anh Việt chốt phạm vi bỏ Batch (NVLT trước hay toàn bộ), chặn cận hạn hay chỉ lưu tham khảo. Tem BTP/TP hiện phụ thuộc Batch. Chưa đủ căn cứ migration cờ has_batch_no khi có tồn/SLE; không ghi DB trực tiếp để vượt validation core. Thay Elle/Pauls theo bếp, đổi mã Gelatine Mass, cấu trúc prefix cần phạm vi riêng đã duyệt. Không đổi Gelatine Powder thành Mass chỉ dựa trên ảnh.

Claude review ba ca mới và cách diễn giải bằng chứng, Codex sửa finding rồi đọc bench hai lượt. Ca bench không thay UAT sản xuất bằng tài khoản Khải, không xác nhận mọi phần tồn đọng #206 đã xong.
