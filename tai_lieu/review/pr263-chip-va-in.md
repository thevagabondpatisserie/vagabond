# PR263 - chip nghiệp vụ và hàng rào bản in

Danh sách APP trước đây chỉ có bước duyệt và vài dòng nhắc rời. Hồ sơ đã chi
vẫn có thể thiếu hóa đơn đến sau. Máy chủ nay trả các chip công việc riêng:
cần kiểm tra đối chiếu, quá hạn, thiếu UNC, chưa nối sao kê, chờ hóa đơn,
đã nối hóa đơn bổ sung, đã chi theo hồ sơ và trả trước chờ quá 7 ngày.

Chip đếm theo tập đang xem, kết hợp với bước duyệt; nhóm đang chọn còn hiện
kể cả khi số đếm về 0, luôn có nút bỏ lọc. Một hồ sơ có thể thuộc nhiều nhóm.
Các chip không khẳng định đã cấn nợ. Phiếu trả trước không suy ra thiếu UNC
từ trường mà nguồn dữ liệu đang gán mặc định. Không thêm bút toán hay sửa
chứng từ production trong thay đổi này.

Review 5614360921: bỏ CAO_O_ANH không còn sử dụng. Hàng ảnh dùng duy nhất
CAO_O_1_HANG=130mm, cộng đệm 6mm, nhãn 14mm và cách nhãn 2mm trên vùng in
A4 ngang 180mm, còn 28mm dự phòng. Ca kiểm đo đúng hằng số render và giữ
ngưỡng dự phòng 25mm. Thử tăng lên 200mm/220mm đều bị bắt. Sửa tên ca chín
ảnh/năm trang; thư viện PDF ImportError không làm mất toàn bộ bộ kiểm.

Kiểm: ca thuần chip, chuỗi DOM bấm/lọc/giao/bỏ lọc, ca bench đọc danh_sach
sau save/nối hóa đơn/cập nhật UNC. CI bổ sung render wkhtmltopdf có hash
gói cố định, đếm 1/2/9 ảnh, khổ A4 ngang, PDF 100 trang và giới hạn, HTTP
multipart upload rồi gọi RPC nén trên bench dùng một lần.

Phân bổ thanh toán từng đợt, cọc/cấn nợ và điều kiện đủ hóa đơn là phạm vi
trước đã duyệt nhưng chưa được triển khai trong cây này. Không ghi các mục
đó vào thông báo phát hành như tính năng đã có. Chờ kết quả CI/bench SHA
cuối trước merge/deploy theo yêu cầu mới của anh Việt.
