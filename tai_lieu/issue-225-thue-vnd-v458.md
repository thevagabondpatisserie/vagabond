# Bàn giao #225: tính tiền VND và VAT từng dòng

## Trạng thái

- Owner code: Codex. Owner review/bench/merge/deploy: Claude.
- Branch: codex/225-thue-tung-dong, nền main 4e95e2a (v457).
- PR phải giữ Draft cho tới khi có bằng chứng bench và chốt đường tạo đơn thật.
- Không đóng #225 hoặc #237 bằng PR này.

## Đã làm

SI VND nháp có một dòng tài khoản VAT `On Net Total`, tiền tệ công ty VND,
tỷ giá 1: tính tiền từng dòng nguyên đồng, theo Item Tax Template của từng
món. Giá và số lượng giữ số lẻ. VAT đã gồm giá là phần còn lại sau net;
VAT ngoài giá làm tròn theo từng dòng. Chiết khấu đầu phiếu phân bổ phần
dư theo phần lẻ lớn nhất, hoà thì theo thứ tự dòng.

Dùng engine con của ERPNext de59166; giữ validation mẫu thuế, tính tổng,
công nợ, commission/contribution và ghi sổ chuẩn. Cache precision chỉ nằm
trong lần tính, trả lại sau đó. Không sửa precision Currency hoặc metadata.

Cửa chung trước M-Invoice đọc net và Item Wise Tax Detail đã lưu, nối theo
item_row/tax_row, không theo item_code. Hai dòng trùng mã vẫn có thể mang
8% và 10%. So tổng SI, tổng VAT, từng dòng và payload trước khi cho gửi.
Hàng tặng có dấu mới dùng VAT này cho 64182/33311, không đọc lại một suất
Settings để ghi sổ. Giá vốn tiếp tục chờ quyết định và chứng từ kho.

Patch `thue_vnd_v458` tạo trường dấu riêng cho SI. Không backfill, không
sửa chứng từ cũ. Hai Server Script đã có cửa gọi chung từ v449/v454;
PR này đổi Python ở cửa chung, không đổi nội dung script trên site.

## Còn mở, chặn phát hành

1. **Đường tạo đơn app chưa có bằng chứng bảng VAT.** `ban_hang.py` tạo
   SI không truyền bảng thuế trực tiếp. Cần chạy đúng hàm tạo đơn trên bench
   với cấu hình sao từ site, đọc SI sau insert. Nếu không có đúng một dòng
   VAT thì chính sách mới chưa áp dụng. Không lấy ca thử tự thêm bảng thuế
   làm bằng chứng cho đường này. Trả kết quả cho Codex để bổ sung cách lấy
   bảng thuế đúng cấu hình; không tự đoán mọi đơn trống bảng đều chịu 8%.
2. Ngoài phạm vi hiện tại: SI đã ghi sổ, phiếu không có bảng thuế hoặc có
   nhiều dòng thuế/phí, Actual, thuế trừ/valuation, trả hàng, tiền tệ khác,
   cash/non-trade discount, shipping rule, khách nội bộ. Các phiếu này đi
   core và cách xuất cũ. Cần thống kê chỉ đọc những dạng đang thực sự dùng,
   đặc biệt SI cũ chưa xuất HĐĐT; không coi chúng đã được sửa.
3. Chưa chạy core trên bench tại workspace Codex. Bắt buộc chạy bộ tích
   hợp mới và các ca #225/#227 cũ trên bench trước merge. Không gửi ra
   M-Invoice hoặc dùng hoá đơn đã phát hành làm fixture.

## Kiểm bắt buộc cho Claude

- Cài nhánh trên bench riêng, chạy migrate thật; Patch Log có
  `thue_vnd_v458` và SI có trường `vgb_thue_vnd`, không chỉ APPVER tăng.
- Chạy `vagabond.khung.kiem_that.cua.chay`; các ca mới ở
  `thu_thue_vnd_225.py` dựng SI, save/submit/reload và đọc GL thật.
  Hai khoá chứng từ còn sót và số lượng lệch phải rỗng.
- Ca mới: tổng 10.420.000 ra net 9.648.148, VAT 771.852; trùng mã 8/10
  qua sửa giá và thêm dòng 0%; năm dòng net 6, VAT 8%; giảm net/gross;
  chiết khấu mỗi đơn vị 0,25 với qty 3; tặng hỗn hợp; cache cùng object.
- Bổ sung đường xuất tay và safe_exec script xuất rải, chặn HTTP bằng stub,
  đối chiếu payload từng dòng với SI/GL đã reload. Thử giảm theo phần trăm,
  phân số qty, trường hợp 99.999 và các ca 0,15/0,33/0,55 đã tái hiện.
- Kiểm JE 0,01/0,15, PO/PI nhiều VAT và SI cũ giữ nguyên. Không cập nhật
  chứng từ quá khứ để đưa số về chuẩn mới.
- Chỉ sau khi đóng các điểm chặn trên mới đổi Ready, merge/deploy theo
  phân công của anh Việt. Fetch main trước đẩy, chốt lại số phiên bản nếu
  phiên khác đã dùng 458. Sau deploy xác minh migrate và màn thật riêng.

## Lệnh kiểm local

```sh
python3 dung_app_bep.py --kiem
sh kiem_truoc_deploy.sh
```

Đây là tầng thuần. Kết quả xanh không thay bằng chứng bench hoặc site.
