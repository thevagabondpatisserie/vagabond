# Issue 283: lý do combo chưa áp dụng

Màn chọn món tại quầy giữ cả combo chưa áp dụng. Thẻ hiện lý do từ máy chủ; bấm thẻ hoặc mã KMCB đều báo cùng lý do và không thêm món. Combo thiếu cấu hình thật vẫn báo thiếu cấu hình. Combo hợp lệ vẫn rã món như cũ. Màn cấu hình nhắc khi combo bật mà chưa gắn mã KMCB.

Ca DOM nạp toàn tệp 09, mở sheet và gọi handler bấm thật: hết giờ, sai quầy, thiếu cấu hình, hợp lệ. Trước sửa, ca đỏ tại khẳng định lý do phải hiện trong sheet; sau sửa đạt. Cổng local 2914/0, kiem_truoc_deploy.sh rc0. Bản ghép được dựng bằng dung_app_bep.py. Chưa có ảnh CSS trên site thật ở 390px; chưa deploy.

APPVER 485 dành sau PR 291 v484. Khi tích hợp giữ cả dòng patch 484 và 485, dựng lại bundle và chạy cổng trên SHA tích hợp. PR này không chứa mã của PR 291, không đóng toàn bộ issue 283.
