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
