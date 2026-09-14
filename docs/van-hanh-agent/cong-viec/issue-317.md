# Issue317: thanh toán nội bộ và YCPS

Owner Codex local, Claude review. Nhánh `codex/317-thanh-toan-noi-bo` từ main 6886899d. Anh Việt yêu cầu PR A lấy v492. Không deploy hoặc sửa dữ liệu production.

## Phạm vi PR A
- Ngưỡng 500.000, một chứng từ hoặc biên nhận một phiếu; hoàn ứng kế thừa YCPS từ tạm ứng đã chi.
- Chi phí và hoàn ứng đi thẳng từ người phụ trách tới kế toán; chỉ tạm ứng lớn qua giám đốc. Patch chuyển riêng phiếu Chi phí và Hoàn ứng đang Chờ giám đốc sang Chờ kế toán, có ghi chú, không chạm phiếu đã chi hoặc đã huỷ.
- Uỷ nhiệm chi chỉ bắt buộc khi trả nhà cung cấp bằng chuyển khoản. Kế toán thấy nút Duyệt và chi. Nút Quay lại mở đúng danh sách và giữ bộ lọc trong `ttnbLoc`.
- Danh sách có người lập, tổng theo bộ lọc, quá hạn, nút tạm ứng và Excel.

## Tách sang PR B
Toàn bộ gộp chuyển và khớp sao kê theo lô được giữ ở nhánh `codex/317b-lo-gop-chuyen`, không nằm trong PR A và nút đã ẩn. PR B phải chứng minh fail-closed, khoá dùng chung khi hai luồng tranh cùng Bank Transaction, retry lỗi giữa lô và có đường gỡ lô có dấu vết trước khi khớp.

## Cổng còn phải chốt
- Chạy tầng thuần, kiểm bundle, cổng trước deploy và kịch bản DOM giả cho danh sách, nút quay lại.
- Bench hai lượt trên SHA cuối phải trả `chung_tu_con_sot=[]`, `so_luong_lech={}`. Chưa kiểm site thật, chưa deploy.
- Xác minh `autoname` của RnD Purchase Request trên site trước phát hành. F2 quyền đọc YCPS cho nhân viên ngoài R&D cần anh Việt chốt nếu site chưa cấp.

## Delta sau053fa009

F4 đã đọc site: autoname naming_series:, series RND-.YY.-, patch đổi series phù hợp. Quyền đọc hiện chỉ System Manager và Mua hàng R&D; đã hỏi anh phạm vi vai, chưa mở quyền. F5 sửa lọc Người lập cho vai mua hàng đã được xem toàn bộ; F6 từ nấc gốc push danh sách để còn Home. Bench053fa009 đỏ215/217 cảhai lượt, sạchrollback; cùng nguyên nhân fixture SePay không có biên nhận theo luật317. Bổ sung File thử thật trước insert, không tắt validator. ChờbenchSHA mới.

## Lượt nền sau3a541850

Bench3a541850 đạt217/217 hai lượt, sạchrollback; Claude chốt F5/F6/fixture. Đang sửa inlineP2: patchgiaoToDo sangkếtoán khôngchuông; nhiềuảnh cùngbiênnhận; hướngdẫnduyệt theoloại; tênngườilập/quáhạn trêncảlịchsử/danhsách. Local2994/2994 vàcổngđạt trướcpush. Chưađóng F2hoànứngcũ/quyềnYCPS, khôngmerge/deploynền.


Anh Việt duyệt hai phương án 14/09 (comment5667507862). Codex đã triển khai: nguồn tạm ứng đã chi/cùng người/quy tắc cũ/thiếu YCPS được hoàn ứng; kế toán bắt buộc nhập lý do và lưu Comment. Picker riêng trả mã/mục đích YCPS owner hiện tại; validate kiểm quyền người lập từ DB. Không mở toàn DocType. Ca thuần và bench mới đang kiểm; chưa merge/deploy.

F7/F8: thêm ngoại lệ cho nguồn tạm ứng mới không YCPS nhưng số ứng thực <=500.000 (đọc bảng kê từ Document nguồn). Không mở ngoại lệ cho nguồn mới trên trần thiếu YCPS. Nguồn cũ theo duyệt của anh giữ nguyên. YCPS mất được coi không hợp lệ thay vì DoesNotExistError; nguồn có tham chiếu mất cho chọn phiếu thay thế, vẫn kiểm quyền. Thêm bench nguồn400k/hoàn600k và mở chi tiết YCPS đã mất. Chờ bench/reviewSHA mới.
