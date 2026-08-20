# Nguồn thật của app điện thoại nằm ở đây

Đọc file này trước khi sửa bất cứ thứ gì trong thư mục `bep/`.

## Ba câu ngắn

**`app_bep.js` là tệp do máy sinh ra. Đừng sửa tay vào nó.** Sửa trong `bep/` rồi chạy máy ghép.

```
python3 dung_app_bep.py            ghép lại và ghi đè app_bep.js
python3 dung_app_bep.py --kiem     chỉ kiểm, lệch thì trả mã lỗi 1
```

**Thứ tự ghép là thứ tự tên tệp.** Tiền tố hai chữ số giữ đúng thứ tự đó. Đổi chỗ hai phần là đổi thứ tự khai báo trong một hàm, có thể làm vỡ app mà không báo gì.

**Từng phần một mình không đọc được.** Cả 20.216 dòng nằm trong một hàm duy nhất: `00-nen.js` mở vỏ hàm và `99-dong-vo.js` đóng lại. Nên `node --check` trên một phần sẽ báo lỗi cú pháp. Đó là cố ý, không phải thiếu sót. Chỉ tệp ghép lại mới đọc được, và cổng kiểm tra trước deploy chạy `node --check` trên tệp ghép.

## Vì sao tách ra

`app_bep.js` từng là một tệp 20.216 dòng, 1,2 MB. Sửa một chữ là đẩy lại cả tệp, và đã ba lần mất mã vì hai phiên làm việc ghi đè lên nhau. Nay nguồn nằm ở 24 tệp nhỏ: hai phiên sửa hai nghiệp vụ khác nhau thì không còn đụng nhau, và nếu tệp sinh ra bị ghi đè thì chạy lại máy ghép là có lại đủ, không mất dòng nào.

Ngoài ra ngày 15/08/2026 có lỗi thẻ số lớn in ra `[object Object]` do tiền tố `kh` của khuôn danh sách trùng với `khO()` của màn Khách hàng nằm cách đó hàng nghìn dòng. Một tệp 20.216 dòng với 901 tên ở mức ngoài cùng là môi trường đẻ ra kiểu lỗi đó.

## Giai đoạn 1, và điều kiện nghiệm thu

Đây là giai đoạn 1: **tệp ghép ra phải giống hệt tệp cũ tới từng byte**. Không thêm một dòng chú thích nào vào các phần, không đổi một dấu cách nào. Mã băm SHA-256 của bản ghép phải bằng mã băm bản đang chạy thật.

Vì vậy đừng thêm tiêu đề mô tả vào đầu mỗi phần, dù rất muốn. Chỗ để mô tả là chính tệp này.

Giai đoạn 2 (bỏ vỏ hàm, phục vụ thẳng các phần, khỏi đẩy 1,2 MB) chưa làm. Anh Việt chốt để giai đoạn 1 chạy thật vài ngày đã.

## Hai mươi bốn phần

| Tệp | Dòng gốc | Nội dung |
|---|--:|---|
| `00-nen.js` | 1 - 538 | mở vỏ hàm, chuyển hướng erp sang app, khối CSS, các hàm tiện ích |
| `01-khung-app.js` | 539 - 756 | trạng thái, bộ định tuyến, danh mục nền, định tuyến bếp |
| `02-trang-chu.js` | 757 - 1.352 | trang chủ và tám ô nhóm nghiệp vụ |
| `03-kho-chung-tu.js` | 1.353 - 2.319 | xuất kho, danh sách chứng từ, xác nhận nhận hàng |
| `04-tao-phieu.js` | 2.320 - 2.983 | bốn bước tạo phiếu, duyệt phiếu chi |
| `05-san-xuat.js` | 2.984 - 4.104 | tồn kho, bảng bếp, lệnh sản xuất, tem HACCP |
| `06-nhap-kho-kiem-ke.js` | 4.105 - 5.588 | nhập kho từ đơn mua, đăng nhập, kiểm kê, mua hàng R&D |
| `07-hop-thoai.js` | 5.589 - 6.263 | hộp thoại dùng chung, và dòng đặt tiêu đề trang |
| `08-doanh-so-sales.js` | 6.264 - 7.160 | doanh thu Sales, rà soát và chốt lẻ từng đơn |
| `09-tinh-tien-quay.js` | 7.161 - 8.507 | màn tính tiền của ba điểm bán |
| `10-bill-quay.js` | 8.508 - 9.444 | in bill 80mm, bill hôm nay, mã OTP quản lý, báo quầy bar |
| `11-khach-ca-hop-dong.js` | 9.445 - 10.136 | công nợ phải thu, khách hàng, chốt ca, hợp đồng event |
| `12-van-don.js` | 10.137 - 11.541 | vận đơn, chi phí xe, phiếu in, lọc và xếp tuyến. **APPVER nằm ở đây** |
| `13-khuyen-mai.js` | 11.542 - 12.994 | khuyến mãi trên màn tính tiền, chương trình, combo, voucher |
| `14-bao-cao.js` | 12.995 - 13.369 | phân hệ báo cáo |
| `15-khuon-danh-sach.js` | 13.370 - 13.688 | khuôn màn danh sách dùng chung, tiền tố `kg` |
| `16-mua-hang.js` | 13.689 - 13.962 | đơn mua, công nợ phải trả, hai màn hoá đơn |
| `17-cai-dat.js` | 13.963 - 15.700 | điểm bán, nguồn đơn, hạng khách, combo nhóm món |
| `18-doi-chieu-may-in.js` | 15.701 - 16.590 | đối chiếu hoá đơn mua, máy in, hồ sơ khách, đơn treo |
| `19-ho-so-tt.js` | 16.591 - 17.456 | hồ sơ thanh toán nhà cung cấp |
| `20-danh-muc-quyen.js` | 17.457 - 18.065 | danh mục nhà cung cấp, người dùng và quyền |
| `21-ke-toan-khac.js` | 18.066 - 18.977 | tài sản, hạch toán tay, ngân hàng, cảnh báo, bảng giá mua |
| `22-bao-gia.js` | 18.978 - 20.213 | báo giá và hợp đồng mua bán |
| `24-phantom.js` | ... | chuyển bán thành phẩm sang Phantom, dọn chứng từ thử |
| `99-dong-vo.js` | cuối | đóng vỏ hàm. LUÔN là phần cuối cùng, phần mới thêm phải mang số nhỏ hơn 99 |

## Vài chỗ dễ vấp

**Muốn lên phiên bản app** thì sửa `APPVER` trong `12-van-don.js`. Dòng đó nằm cạnh khối khởi động vì lý do lịch sử, giai đoạn 2 sẽ dời ra chỗ tử tế hơn.

**Dòng khởi động** `if (document.readyState === 'complete') { __boot(); } ...` cũng nằm trong `12-van-don.js`. Đừng dời nó khi chưa làm giai đoạn 2.

**Thêm một phần mới** thì đặt tên đúng dạng `NN-ten-khong-dau.js`, số thứ tự chưa ai dùng. Máy ghép chỉ nhận đúng dạng đó, tệp sao lưu để quên trong thư mục sẽ không lọt vào bản ghép.

**Đặt tiền tố hàm mới** thì kiểm va chạm tên trước, đây là QT-28. Cả 24 phần vẫn dùng chung một phạm vi, hàm khai sau đè lên hàm khai trước mà không báo gì.
