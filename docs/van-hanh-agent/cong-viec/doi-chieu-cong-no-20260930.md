# Đối chiếu công nợ và kỳ thu/chi - phương án chờ Claude rà

## Phạm vi và trạng thái
Yêu cầu anh Việt 30/09/2026: khớp báo cáo kế toán/thu mua, xét các khoản đã
trả trên phần mềm cũ, thêm mã đối tác và số hóa đơn, tham vấn Claude trước
khi triển khai. Codex khảo sát; đề nghị Claude nhận triển khai sau khi xác
nhận phạm vi trên PR theo yêu cầu riêng của anh trong việc này.

Nền: `ea02cd0288fb38c41a7223592a5a06e1a5c7afd4`.
Nhánh: `codex/doi-chieu-cong-no`. Đây là thiết kế và ca nghiệm thu,
chưa sửa runtime, không tăng APPVER/patch, không đủ điều kiện deploy.
Dữ liệu và chứng từ thật giữ local, không đưa lên repo công khai.

## Những gì đã xác minh
- Ba file cùng đợt: outstanding từng Purchase Invoice trong Accounts
  Payable (AP) khớp Purchase Register. Tổng AP còn chứa các Payment Entry
  âm chưa phân bổ. Không coi số đã trả trong tập hóa đơn còn nợ là tổng
  thanh toán của cả kỳ.
- Sổ NCC có nhiều đối tác đã thanh toán. Chênh GL với AP được truy chỉ đọc
  tới một Purchase Receipt có dòng Có chi phí phải trả và Party Supplier,
  không có Payment Ledger Entry (PLE). Đây là chênh phạm vi cần giải thích,
  chưa phải bằng chứng sai GL. Sổ NCC lõi gom GL theo party, không chỉ 331.
- Purchase Register có ngày hóa đơn, không có ngày thanh toán trong file
  nhận được. Không suy ngày trả từ bill_date hay trạng thái Unpaid/Paid.
- `mua_hang.cong_no_phai_tra` cộng PI đã ghi sổ, outstanding dương, không
  lọc company/ngày chốt; không chứa credit chưa phân bổ. Ảnh, file, site
  được lấy khác thời điểm. Chưa xác định số công nợ đúng sau chuyển phần
  mềm vì thiếu bảng thanh toán nguồn cũ và ngày chuyển sổ được chốt.
- Core kiểm tại SHA ERPNext `de591661b9ba0bd3f62ac25b99b5c85c723515f6`
  (pin CI, chưa xác minh SHA production):
  `accounts/report/payment_period_based_on_invoice_date/` chọn Incoming
  là Customer/Sales Invoice, Outgoing là Supplier/Purchase Invoice.
  JS gửi giá trị đã dịch; đổi nhãn không được làm backend rơi nhánh else.
  `get_entries` lấy ABS(ple.amount), chưa loại dòng phát sinh hóa đơn tự
  trỏ mình. Báo cáo này không thể mặc định mọi dòng đều là tiền đã thanh toán.
- `accounts/report/customer_ledger_summary/customer_ledger_summary.py`
  dùng GL, Supplier Ledger Summary gọi cùng lớp; paid_amount có thể gồm
  điều chỉnh/cấn trừ, không mặc nhiên là tiền ngân hàng thực trả.

## Hợp đồng báo cáo đề nghị
Tái dùng báo cáo lõi và chứng từ chuẩn. Không tạo DocType công nợ mới,
không sửa outstanding trực tiếp, không sao chép một sổ kế toán thứ hai.

| Chỉ tiêu | Nguồn và ý nghĩa |
|---|---|
| Nợ hóa đơn chưa tất toán | PI/SI + phân bổ PLE tại ngày chốt, kể cả thanh toán từng phần |
| Trả trước/thu trước chưa phân bổ | PLE riêng, đúng party, tài khoản và tiền tệ |
| Công nợ thuần trong phạm vi AP/AR | Kết quả core AP/AR với cùng bộ lọc; không gọi là lệnh chi |
| Hàng nhận chưa có hóa đơn | Dư tài khoản chờ hóa đơn, drill-down PR và bút toán bù; tách khỏi 331 |
| Sổ đối tác GL | Đầu kỳ + phát sinh tăng - giảm = cuối kỳ, theo từng tài khoản |
| Tiền thực thu/chi trong kỳ | PE/JE đã ghi sổ với nguồn tiền được xác minh; tách cấn trừ, đảo, chênh tỷ giá |
| Tiền đã về/đã đi, chờ ghi sổ | Bằng chứng nghiệp vụ; giữ hợp đồng #380, không tự trừ GL |

Chỉ so khi cùng company, ngày chốt, tài khoản, currency, finance book,
chiều phân tích và quyền xem. Số tiền gốc và tiền công ty phải có nhãn riêng.
Không trừ credit của NCC A vào số cần chuyển NCC B; không cộng nhiều tiền tệ.
Snapshot quá khứ phải lấy core as-of, không lọc ngày trên outstanding hiện tại.
Nợ đầu kỳ trước from_date vẫn phải có trong báo cáo số dư tại ngày chốt.

Mỗi chênh có dòng giải thích và liên kết chứng từ; không có thì báo
"Chưa xác định nguyên nhân", không chỉnh cho tổng bằng nhau.

## Cột và kỳ thu/chi
- Cả app, Desk và Excel: mã ERP đối tác, mã kế toán, tên, mã chứng từ ERP,
  số hóa đơn gốc, ký hiệu, ngày hóa đơn, ngày hạch toán, hạn trả, tiền gốc,
  đã phân bổ, còn nợ, currency. Không đổi khóa liên kết để thay tên hiển thị.
- Tái dùng mã kế toán/quan hệ HĐĐT trong #389, không sinh mã song song.
  NCC chưa có mã kế toán thì hiện "Chưa có mã", không suy từ tên/MST.
  PI đọc bill_no/bill_date; số bán ra từ quan hệ HĐĐT có xác minh. Tờ gộp
  nhiều đơn hoặc một đơn nhiều tờ phải drill-down, không chọn phần tử đầu.
  Chứng từ không có hóa đơn hợp lệ để trống số, không lấy APP làm số thuế.
- Bộ lọc kỳ thanh toán: "Thu từ khách" / "Chi cho NCC"; giá trị nội bộ
  ổn định, adapter về core phải hoạt động cả tiếng Việt lẫn tiếng Anh.
  Không đảo SI thành PI vì hiểu Incoming là hóa đơn đầu vào.
- Một ngày trả không diễn tả được nhiều đợt. Hiện ngày trả gần nhất, số
  đợt và bảng lịch sử từng phân bổ: PE/JE, ngày hạch toán thanh toán, ngày
  ngân hàng (nếu có), số tiền. Khoản bù trừ phải mang nhãn riêng.
- Không vá bằng loại toàn bộ SI/PI hay chỉ lấy Payment Entry: POS, return,
  JE, write-off và tiền trả trước được phân bổ sau cần phân loại theo
  chứng từ/PLE/GL thật. Claude xác nhận thuật toán trước khi code.

## Khoản từ phần mềm cũ
1. Kế toán xác nhận ngày chuyển sổ, danh sách hóa đơn và từng khoản đã trả:
   mã đối tác cũ, MST nếu có, số/ký hiệu/ngày hóa đơn, currency, tiền trả,
   ngày trả, chứng từ nguồn, số còn nợ tại ngày chuyển sổ.
2. Đối chiếu mã trước, dùng tổng tiền chỉ để kiểm; không khớp bằng tên/số
   tiền đơn lẻ. Trùng số khác NCC/ký hiệu/năm phải đưa vào nhóm cần xác nhận.
3. Có PE/JE hợp lệ nhưng chưa phân bổ: dùng Payment Reconciliation chuẩn,
   không tạo lần chi thứ hai. Bank Transaction/UNC chưa ghi sổ không tự
   chứng minh đã có payment. Đã phân bổ đúng thì bỏ qua, chạy lại không đổi.
4. Chưa có chứng từ: kiểm số dư đầu kỳ đã nhập và phạm vi lịch sử đã chuyển
   trước khi đề xuất chứng từ bổ sung. Không nhập cả lịch sử đã trả rồi
   cộng thêm số dư đầu kỳ; không chuyển tiền thật để sửa sổ.
5. Trình bảng trước/sau từng chứng từ cho kế toán và anh Việt chốt. Không
   tự sửa/hủy hóa đơn đã ghi sổ, không chạy batch chỉnh công nợ trong migrate.

## Giao diện
Thứ tự: company/ngày chốt -> thẻ tổng có nhãn nguồn -> tìm mã/tên/số hóa đơn
-> chip trạng thái/nguồn/khoảng ngày -> danh sách -> khối chênh thu gọn.
Dùng frame/card/chips/sheet hiện có. Chip "Nợ hóa đơn", "Trả trước",
"Chờ ghi sổ"; nút "Xem đối chiếu", "Xuất Excel". Cảnh báo không cản thao tác.
0 dòng: "Không có công nợ trong phạm vi đang chọn"; lỗi: "Chưa tải được
công nợ. Thử lại". 1 dòng vẫn đủ mã/số/ngày; nhiều dòng phân trang và tổng
toàn bộ tập lọc, Excel không cắt theo trang. Không render toàn bộ giải thích.
Ở 390x844 ô tìm và dòng đầu nằm trong màn đầu; khối chỉ đọc tối đa hai dòng.
Phải kiểm ảnh site thật trước/sau, tiếng Việt/Anh; Node không thay CSS thật.

## Cổng nghiệm thu và phân công
- Fixture: nợ đầu kỳ, PI trả một phần/nhiều đợt, PE chưa phân bổ, JE cấn,
  return, hủy/đảo, PR trên tài khoản chờ hóa đơn có party nhưng không PLE,
  payment sau ngày chốt, đa công ty/tiền tệ, một bên nhiều mã/số hóa đơn trùng.
- Kiểm UI/API/export dùng cùng bộ lọc; quyền kế toán, thu mua, người không
  được xem; tổng theo party/account khớp core, không bỏ chứng từ do giới hạn.
- Payment Period: chứng minh dòng tự phát sinh hóa đơn không bị gọi là tiền
  thực trả; giữ thu/chi đúng cả hai ngôn ngữ; ngày/số tiền từng đợt đúng.
- Luồng nguồn cũ trên bench: trước/sau GL/PLE/outstanding, retry và hủy,
  không tạo chi trùng; production chỉ chạy sau bảng dữ liệu đã được duyệt.
- Claude: rà hợp đồng số, quyết định phân loại kỳ thu/chi và nhận phạm vi
  sửa trên PR. Codex không sửa chồng. Chưa có biên nhận Claude nhận việc.
- PR hiện chỉ tài liệu: preflight đạt, kiểm diff/link; chưa có kiểm runtime,
  bench, CI, review, merge, deploy. Thiếu nguồn cũ không cản sửa báo cáo,
  nhưng cản kết luận công nợ lịch sử đã được tất toán.
