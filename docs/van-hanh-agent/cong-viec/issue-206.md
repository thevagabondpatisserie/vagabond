# Issue 206: kiểm chứng lô và giá vốn theo ý Khải

**Cập nhật theo trao đổi mới:** [bản đề xuất để anh Việt duyệt](issue-206-duyet.md) thay hướng bỏ Batch/FIFO bên dưới. Nhánh đã có code thử cảnh báo cho Stock Entry nhập/xuất/chuyển, version dự kiến489. Không đổi cấu hình site.

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

Bench34744299841 trên15706c56 đã SUCCESS, ba ca Khải đạt cả hai lượt. F1 Claude dựa trí nhớ được đối chứng bằng source de591661 và bench. F2 thêm cờ từng Batch sau xuất, qty=-4 và SLE giữ bundle; F3 bỏ save/reload thừa. SHA mới cần bench lại.

## Sửa review F4-F7 ngày 13/09

Giữ ngoại lệ core cho Material Issue/Transfer khi bật chặn HSD; Material Receipt vẫn chặn khi bật. Lô disabled luôn bị chặn, câu lỗi trung tính. Ma trận 24 tổ hợp qua cả hai wrapper; thêm ca bench xuất/chuyển khi công tắc bật, kiểm SLE số lượng/giá trị/gói lô và huỷ trả tồn. Ca nhận bổ sung cảnh báo đúng một lần và SLE 2/2000. FEFO chỉ được khẳng định cho dòng chưa gán lô qua lo_hang.gan_lo, không cho mọi bundle Desk.

Local 2950/2950, kiem_truoc_deploy.sh rc0. Bench 34748648065 trên8827 startup_failure trước tạo job; chưa xác định nguyên nhân, chưa có bằng chứng tích hợp bản này. Giữ Draft, chưa merge/deploy.

Theo chỉ dẫn mới anh Việt, AGENTS.md và CLAUDE.md yêu cầu mọi comment làm việc tag @claude và nhắc tag @codex khi trả lời. Tag không thay biên nhận worker và không cấp phép code trùng với Codex local. Phạm vi nhận mua/Purchase Receipt vẫn chưa được thay đổi trong PR này.

## Bản thay chính sách theo spec 5653018176

Phần này thay các kết luận lịch sử về công tắc/disabled/phạm vi ở trên.

- Bỏ công tắc HSD bằng patch lặp được. Bảy purpose Stock Entry và bốn controller mua/bán có cập nhật kho chỉ ghi cảnh báo hạn/lô tắt, vẫn giữ kiểm serial thuộc lô. Không thay StockController chung.
- Vòng vét đọc cả lô tắt/quá hạn và trừ giữ POS/SRE. Lô tốt vẫn ưu tiên. Chọn lô tay thiếu thì bù cùng mã/kho; gói nháp cập nhật tại chỗ, kiểm mã/kho/chứng từ/dòng, không sửa gói đã ghi sổ. Tồn thật thiếu vẫn chặn.
- Cửa nhận mua tạo Batch mới với đúng HSD nhận được hoặc để trống. Batch không tự suy HSD từ shelf life và không ép nhập hạn. Không sửa ngày trên lô cũ. Câu nhắc giao diện không còn nói phải điền mới nhận được.
- Thêm ca hành vi UOM/tay/gói/nhiều dòng/thiếu tồn/sai kho và bốn controller; ca bench tay/gói 100+50 cần130, thiếu200, hủy; API nhận mua thiếu HSD/quá hạn.
- APPVER 489. Chưa deploy. Ca bench mới cần kết quả thực tế trước kết luận; cần tiếp tục nghiệm thu đủ bốn loại chứng từ mua/bán trên bench và thao tác thật. Stock Reconciliation chưa đổi.
