# #266: tách ghi sổ khỏi hàng rào phát hành

## Lỗi và bản sửa

Trên main01dc0ae, cả tu_ghi_so_cuoi_ngay và xuat_rai_trong_ngay return trước vòng ghi sổ nếu hàng rào trảFalse. Tái hiện gọi chính hàm với một SI đủ điều kiện:0lần tới ghi sổ; đối chứng chỉ bỏ return trong AST:1lần cho mỗi nhịp.

Hai nhịp nay vẫn ghi sổ nhưng truyền cho_xuat=False để không gọi phát hành sau submit. Sau vòng ghi sổ, ghi cảnh báo riêng trên Cài đặt, xếp thư cho nhóm nhận cảnh báo hiện có và hoãn phần phát hành hàng loạt. Cửa chung kiem_goi vẫn giữ nguyên. Không mở rộng ngay_cu_dang_cho, không đổi ngày hóa đơn, không gỡ cờ đối chiếu.

F3: đọc tập nợ còn lại trước _ghi_moc_loi. Ca mới trên main trảmốc[False] dù còn chặn; sau sửa [True].

## Core và giới hạn

- Frappe16.27.1 f33ac3f: document.py run_post_save_methods gọi on_submit; run_method gọi run_server_script_for_doc_event sau hook. Lỗi script có thể thoát khỏi submit.
- ERPNext16.28.0 de591661: sales_invoice.py on_submit469 gọi update_stock_ledger khi update_stock và make_gl_entries510. Không thay đường core đó.
- Đây là core theo phiên bản live đã kiểm gần nhất, phải đối chiếu lại trước phát hành.
- Chưa đọc được After Submit hiện hành trên production vì CUA timeout. Bản sửa này CHƯA đủ để merge/deploy. Nếu script đó ném lỗi thì phải bổ sung sửa đúng script, không nhận đây là đã chữa xong mọi đường ghi sổ.

## Kiểm

- Ca hành vi nạp chính hai scheduler: vẫn gọi ghi sổ1tờ với cho_xuatFalse và báo hoãn.
- Cửa ghi sổ: submit rồi commit, không gọi _tu_xuat_hddt khi hoãn.
- Cảnh báo: ghi Cài đặt, gọi xếp thư giả; không nhận là đã gửi SMTP thật.
- Bench bổ sung SI thật/GL khi hoãn, không POST. _chuan_bi_ghi_so được thay trong riêng ca để cô lập ranh giới submit; không nhận là UAT điều kiện thanh toán hoặc script production. Commit nằm trong khung rollback, không phải chứng minh durability.
- Local2870/0; cổng toàn repo RC0. CI/bench chưa chạy trên nhánh này lúc soạn.

## Phiên bản

v482 dành sau PR210/v481, deploy chung. Giữ nguyên patch cũ. Phát hiện dat_phien_ban.py xóa lịch sử dù docstring nói giữ; đã sửa công cụ giữ đủ dòng, không nhân dòng và chặn hạ APPVER. Bộ kiểm bắt được bản cũ xóa patch; không push trạng thái mất lịch sử.

## Review C1-C5

C1 xác nhận bằng email_queue.json của Frappe16.27.1: không có subject. Bỏ truy vấn đó; dùng mốc Redis theo ngày sau khi xếp thư/commit để giảm lặp, không nhận là bảo đảm thư đã gửi hoặc chống trùng bền khi mất Redis. Thư dùng khung và nút mở app hiện có.

C2 giữ kết quả cũ khi nhịp mới 0/0; log chỉ một mốc trong ngày. Cảnh báo sót so chính câu của nó, không chặn bằng từ CẢNH BÁO chung; đặt cảnh báo mới trước để không bị cắt mất khi nhật ký đã dài500ký tự. Nhật ký vẫn giới hạn500như trường cũ.

C3 cờ tu_ghi_so_lan_cuoi vốn đặt sau ghi sổ, trước phát hành. Nay nhánh hoãn cũng đặt cờ ở đúng tầng đó, giữ ngoại lệ bấm tay trước giờ. Nợ phát hành không được xóa, cờ không phải bằng chứng đã xuất đủ. Tránh đồng bộ Pancake toàn bộ mỗi5phút.

C4 tờ hoãn có thể tăng nợ mỗi ngày nếu không có người xử lý. Không tự mở rộng tập phát hành hoặc đổi ngày. Ca bench mới gọi màn xử lý ngày cũ ở ngày kế tiếp, kiểm tờ nằm trong phạm vi màn và tập nợ rộng nhưng chưa vào tập tự gửi.

C5 còn chặn merge/deploy: Mac khóa, chưa đọc được After Submit production. Không dùng bench không có script đó làm bằng chứng đã sửa hết.

## Review D1-D6

- Phép đếm lỗi hoặc thiếu cấu trúc trả về nay ném; chuông23h55 gửi cảnh báo chưa đếm được, không coi là0. Chưa đọc script production để xác định nhánh thử có chạm hàng rào, gộp với C5 trước phát hành.
- Mốc cảnh báo phân biệt nhịp rải và cuối ngày. Danh sách lỗi ghi sổ được giữ trong Error Log (qua giau_khoa), không chỉ giữ số lỗi.
- Redis lỗi vẫn đi tới log/thư; mất mốc có thể báo lặp, không giữ im. Mốc chỉ đặt sau queue/commit, không nhận SMTP đã gửi.
- Nhả khóa đồng bộ trước khi báo hoãn ở cả hai caller. Câu hoãn cùng ngày/caller thay dòng cũ, không xếp chồng.
- Bench chốt thêm tập ngày thực sự dùng để rút cạn. Chưa chạy lượt này.
