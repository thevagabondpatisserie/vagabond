# Quy ước viết sổ tay cho trợ lý

Tệp nào trong thư mục này bắt đầu bằng dấu gạch dưới (như tệp này) thì trợ lý
KHÔNG nạp. Mọi tệp `.md` khác là một chương của sổ tay.

Anh Việt giao 02/10/2026: nhân viên hỏi trợ lý trong app thay vì nhắn anh.
Trước bản này trợ lý chỉ có đoạn mô tả đầu tệp mã nguồn làm tư liệu. Đó là
ghi chép của lập trình viên, kể vì sao làm, không kể bấm nút nào. Cả ba câu
hỏi thật đầu tiên trong nhật ký (cấn trừ công nợ, tạo phiếu nhập kho, đặt lại
mật khẩu) đều nhận câu "chưa có tài liệu".

## Một mục là một việc

Mỗi mục mở bằng một dòng `## ` và là MỘT việc người ta muốn làm hoặc MỘT câu
người ta hay hỏi. Tên mục viết như câu người dùng gõ: "Tạo phiếu nhập kho",
"Vì sao không hoàn tất được lệnh sản xuất". Trợ lý chấm điểm tên mục nặng
nhất, nên tên mục phải chứa đúng chữ người ta sẽ dùng.

Ngay dưới tên mục là các dòng khai, mỗi dòng một khoá:

    Từ khoá: các cách gọi khác, tên tiếng Anh, viết tắt, cách gọi đời thường
    Ai dùng: bộ phận hoặc vai
    Màn hình: tên màn (địa chỉ), hoặc "Desk: tên chứng từ" nếu làm trên Desk

Dòng `Từ khoá` là chỗ quan trọng nhất cho việc tìm. Người ta hỏi "cấn trừ",
"bù trừ", "đối trừ", "clearing" cho cùng một việc. Thiếu chữ nào trong dòng
này thì câu hỏi dùng chữ đó có thể không tìm ra mục.

Sau đó là thân mục, theo thứ tự nếu có:

1. Một hai câu: việc này là gì, khi nào làm.
2. `Các bước:` đánh số, mỗi bước một thao tác, ghi ĐÚNG tên nút, tên ô như trên
   màn hình.
3. `Vì sao bị chặn:` các câu báo lỗi hay gặp và cách gỡ.
4. `Lưu ý:` điều dễ sai.
5. `Hạch toán:` nếu chứng từ sinh bút toán, ghi Nợ/Có.

## Chỉ viết cái có thật

- Tên nút, tên ô, câu báo lỗi lấy từ mã nguồn, không đặt theo trí nhớ.
- Chỗ nào chưa chắc thì để chú thích HTML `<!-- kiểm: ... -->`. Trợ lý bỏ qua
  chú thích này khi nạp, người rà soát đọc được.
- Không ghi tên hàm, tên tệp, tên trường máy. Người đọc là nhân viên.
- Câu thuộc về CHÍNH SÁCH (giá, giảm giá, thưởng phạt, có được làm không) thì
  không trả lời, ghi "Việc này do anh Việt quyết".
- Không hướng dẫn sửa, huỷ chứng từ quá khứ đã ghi sổ hay hoá đơn điện tử đã
  phát hành. Ghi "liên hệ kế toán trưởng".
- Không dùng dấu gạch dài, chỉ dùng dấu gạch ngang thường.

## Độ dài

Một mục dưới 1500 ký tự. Dài hơn thì tách thành hai việc. Trợ lý chỉ gửi kèm
khoảng 9000 ký tự tư liệu mỗi câu hỏi.
