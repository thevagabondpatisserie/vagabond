# Quy ước viết sổ tay cho trợ lý

Tệp nào trong thư mục này bắt đầu bằng dấu gạch dưới (như tệp này) thì trợ lý
và màn Sổ tay KHÔNG nạp. Mọi tệp `.md` khác là một chương.

Anh Việt giao 02/10/2026: nhân viên hỏi trợ lý hoặc mở màn Sổ tay thay vì
nhắn anh. Bản đầu nhiều chữ, nhìn đơn điệu. Từ vòng 3, mỗi mục viết theo
khuôn dưới: ít chữ, có bảng, nút hiện như nút thật trên app.

## Khuôn một mục

    ## Tạo phiếu nhập kho khi nhà cung cấp giao hàng
    Từ khoá: nhập kho, phiếu nhập, nhận hàng, PNK, purchase receipt

    | Ai dùng | Màn hình | Nút chính |
    |---|---|---|
    | Thủ kho | Nhập kho (/nhap-kho) | [[Xác nhận nhập kho]] |

    Một câu nói việc này là gì, khi nào làm.

    **Các bước**
    1. Mở màn Nhập kho, chọn thẻ [[Chờ nhận]].
    2. Sửa ô Số lượng thực nhận cho từng món.
    3. Bấm [[Xác nhận nhập kho]], rồi [[Nhập kho]] ở hộp xác nhận.

    **Vì sao bị chặn**
    | Máy báo | Cách gỡ |
    |---|---|
    | Đang có phiếu kiểm kê mở | Ghi sổ hoặc huỷ phiếu kiểm kê trước |

    **Hạch toán**
    | Nợ | Có | Khi nào |
    |---|---|---|
    | 152 | 3311 | Khi bấm Xác nhận nhập kho |

    **Lưu ý**
    - Xác nhận xong là phiếu khoá, muốn sửa phải báo kế toán.

Bỏ khối nào không có nội dung. Không viết đoạn văn dài: mỗi bước một dòng,
mỗi dòng một thao tác.

## Ký hiệu đặc biệt

| Viết | Hiện ra |
|---|---|
| `[[Tên nút]]` | Nút vẽ đúng kiểu nút của app, có mũi tên chỉ vào |
| `[[desk:Tên nút]]` | Nút vẽ theo kiểu nút trên Desk (trang quản trị ERPNext) |
| `(/dia-chi)` trong cột Màn hình | Đường dẫn bấm mở thẳng màn đó |

Chữ trong `[[ ]]` phải ĐÚNG từng chữ như trên nút thật, kể cả hoa thường.
Thẻ (tab) và mục chọn cũng dùng `[[ ]]`.

## Thuật ngữ: 100% tiếng Việt như trên màn hình

- Màn trong app: dùng đúng chữ trên nút, tiêu đề, ô nhập trong mã giao diện.
- Màn trên Desk: dùng đúng bản dịch tiếng Việt site đang hiện (bảng dịch
  tren_man_hinh), ví dụ Bill of Materials là "Công thức", Item Alternative
  là "Mặt hàng thay thế", Journal Entry là "Bút toán", Allow Alternative Item
  là "Cho phép mặt hàng thay thế".
- Tiếng Anh chỉ được nằm ở dòng `Từ khoá` để người gõ tiếng Anh vẫn tìm ra.

## Dòng Từ khoá

Là chỗ quan trọng nhất cho việc tìm. Ghi mọi cách gọi khác: tiếng Việt đời
thường, viết tắt, tên tiếng Anh. Thiếu chữ nào thì câu hỏi dùng chữ đó có thể
không ra mục.

## Chỉ viết cái có thật

- Tên nút, ô, câu báo lỗi lấy từ mã nguồn hoặc bản dịch site, không đặt theo
  trí nhớ.
- Chỗ chưa chắc thì để chú thích HTML `<!-- kiểm: ... -->` ngay cạnh câu chưa
  chắc. Bộ nạp đổi nó thành dấu `[CHƯA XÁC MINH: ...]` gửi kèm cho trợ lý, và
  trợ lý phải nói với người hỏi rằng điểm đó chưa được xác minh. Kiểm xong thì
  XOÁ chú thích đó. Chú thích HTML khác bị bỏ khi nạp.
- Không ghi tên hàm, tên tệp, tên trường máy.
- Câu thuộc về CHÍNH SÁCH (giá, giảm giá, thưởng phạt, có được làm không) thì
  ghi "Việc này do anh Việt quyết".
- Không hướng dẫn sửa, huỷ chứng từ quá khứ đã ghi sổ hay hoá đơn điện tử đã
  phát hành. Ghi "liên hệ kế toán trưởng".
- Không dùng dấu gạch dài, chỉ dùng dấu gạch ngang thường. Không dùng emoji.

## Độ dài

Phần chữ người soạn viết (không tính dấu chưa xác minh) dưới 1600 ký tự một
mục. Dài hơn thì tách thành hai việc.
