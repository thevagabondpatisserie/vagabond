---
name: vagabond-uxui-giao-viec
description: Dẫn phần giao diện khi viết issue hoặc PR giao việc cho Codex, khi tự sửa màn app /bep, và khi rà soát PR có đổi màn hình. Dùng mỗi khi việc chạm tới tệp trong vagabond/public/js/bep/, tới danh sách, hàng chip, bộ lọc, nhãn, trạng thái rỗng, hoặc khi anh Việt gửi ảnh chụp màn hình chê giao diện.
---

# Dẫn giao diện khi giao việc cho Codex

## Vì sao có skill này

Hai lần trong tháng 9/2026 anh Việt gửi ảnh chụp màn hình và nói y hệt một ý.
Ngày 13/09 với portal thành viên: "giao diện xấu quá không đúng với web".
Ngày 15/09 với màn Khớp SePay thủ công ở bản v495: "danh sách kinh khủng quá,
không phải dạng chip chọn đẹp theo giao diện, mà cũng không chọn được luôn để
mà khớp".

Cả hai lần Codex làm ĐÚNG phần logic được viết trong issue, và làm THÔ phần
giao diện KHÔNG được viết. Rút ra một luật, không phải lời chê:

**Codex dựng đúng cái được mô tả. Phần nào bên giao việc không mô tả thì ra
bản thô nhất chạy được.** Vì vậy viết phần giao diện là việc của bên giao
việc. Không được trông chờ Codex tự nghĩ ra, và cũng không được đổ lỗi cho
Codex khi issue không có một dòng nào nói về màn hình.

## Nguồn chuẩn, skill này không thay thế

AGENTS.md mục 2b là các điều bắt buộc về thiết kế màn hình app, anh Việt đã
duyệt 03/09/2026. Skill này là cách ÁP các điều đó vào một issue cụ thể, đọc
kèm chứ không đọc thay.

## Khối bắt buộc trong mọi issue hoặc PR có đổi màn hình

Chưa có khối này thì chưa được gửi issue đi. Khuôn:

    ### Giao diện

    Thứ tự khối từ trên xuống: 1 ... 2 ... 3 ...
    Khung dùng lại: frame, card, chips, sheet, confirmSheet, anhMon
    Nhãn chính xác: từng nút, từng chip, câu lúc rỗng, câu lúc lỗi
    Ba trạng thái: 0 dòng thì ..., 1 dòng thì ..., 60 dòng thì ...
    Giới hạn: khối chỉ đọc tối đa N dòng, nhãn chip tối đa N ký tự
    Phép đo phải đạt: ở 390x844, thứ người dùng cần bấm nằm trong màn đầu
    Bằng chứng: ảnh chụp site thật 390px, một ảnh trước và một ảnh sau

## Bảy câu hỏi trước khi gửi spec đi

1. Danh sách này lấy từ bảng nào, bảng đó có chứa dòng của bên khác không?
   Bank Account chứa tài khoản nhà cung cấp và khách. Contact và Address chứa
   khách. Item chứa cả nguyên liệu lẫn thành phẩm. Nếu có, viết rõ điều kiện
   lọc ngay trong issue, đừng để Codex đoán.
2. Danh sách dài nhất có thể là bao nhiêu dòng? Trả lời bằng phép đếm thật
   trên site, không đoán. Số này quyết định cách bày.
3. Người dùng đến màn này để BẤM cái gì? Cái đó có nằm trong màn đầu không?
4. Khối nào chỉ để đọc? Đã thu về một dòng đếm số, bấm mới mở chưa?
5. Nhãn dài nhất bao nhiêu ký tự? Có bị cắt ở mép khi cuộn ngang không?
6. Không có dòng nào thì màn nói gì, người đọc biết làm gì tiếp?
7. Mạng hỏng hoặc máy chủ trả lỗi thì màn nói gì bằng tiếng người?

## Bốn điều tuyệt đối không làm

1. Nối một danh sách không rõ độ dài bằng join rồi in thẳng ra màn. Luôn là:
   đếm số, vài mục đầu, rồi "và N nữa". Đây chính là lỗi v495.
2. Đổ nguyên tên dài của bản ghi vào chip. Chip là nhãn, không phải câu văn.
3. Để một khối chỉ đọc đứng trên khối để bấm.
4. Nhận "code đúng logic" là màn hình đạt.

## Khi rà soát PR có đổi màn hình

Dò chuỗi trong mã nguồn không phải là kiểm giao diện. Phải mở màn thật ở bề
rộng 390px, đếm số dòng thật, chụp ảnh. Nếu không mở được site thật thì nói
thẳng là chưa kiểm được phần giao diện, liệt kê ra cái gì chưa kiểm, không
kết luận đạt.

Bộ giả lập node không tính CSS nên không bao giờ thay được ảnh chụp. Ngược
lại ảnh chụp cũng không thay được ca kiểm chạy thật.

## Khi anh Việt gửi ảnh chê giao diện

Không sửa ngay chỗ nhìn thấy. Tìm tầng gốc trước. Ở v495, thứ nhìn thấy là
một đoạn chữ dài, nhưng gốc rễ nằm ở máy chủ: hàm dựng danh sách duyệt cả
bảng dùng chung nên gom luôn tài khoản của nhà cung cấp. Sửa mỗi phần hiển
thị thì lần sau dữ liệu đổi là hỏng lại.
