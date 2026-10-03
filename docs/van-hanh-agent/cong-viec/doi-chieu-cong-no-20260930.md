# Đối chiếu công nợ và kỳ thu/chi - phương án chờ Claude rà

## Phạm vi và trạng thái
Yêu cầu anh Việt 30/09/2026: khớp báo cáo kế toán/thu mua, xét các khoản đã
trả trên phần mềm cũ, thêm mã đối tác và số hóa đơn, tham vấn Claude trước
khi triển khai. Codex triển khai từng đợt và mở PR code; Claude rà logic, rà từng vòng
và tái hiện finding, không viết vào nhánh Codex.

Nền: `c0ec18e264a4babeba865cda7af9b392fe83b296`.
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
  (pin CI; Claude xác minh trùng production ERPNext v16.28.0 ngày 30/09,
  Frappe v16.27.1, tại [review vòng 2](https://github.com/thevagabondpatisserie/vagabond/pull/392#issuecomment-5905851021)).
  Đây là bằng chứng Claude báo từ Frappe Cloud, Codex chưa đo lại live trong
  lượt sửa tài liệu này. Nâng ERPNext phải kiểm lại phân loại PLE:
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
| Công nợ ngoài hóa đơn (đầu kỳ, JE có party) | PLE còn dư của JE; giữ account, party, dấu và cờ is_opening, không coi mọi JE là trả trước |
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
- Giao diện đã có trên main sau tích hợp #389 qua #394 (mốc f4a1558):
  đọc `ma_ke_toan.O_MA[party_type]` trên chính party của dòng, tức
  `Customer.custom_ma_khach` / `Supplier.custom_ma_ncc`. Chưa có thì hiện
  "Chưa có mã"; không suy tên/MST, không cấp mã từ báo cáo.
  Không gọi `cap_ma`, `ma_theo_mst`, `nap_danh_muc_fast`: các hàm này có
  đường ghi. `bang_ma_theo_mst` chỉ phủ Customer nên không dùng cho phải trả.
  Mã kế toán trên SI đọc `Sales Invoice.vgb_ma_khach_ke_toan` riêng, không
  thay mã người đặt bằng mã công ty nhận hóa đơn.
- PI đọc `bill_no` / `bill_date`. SI đọc `custom_hddt_so` và
  `custom_hddt_ky_hieu`; đọc các tờ có `MInvoice Invoice.vgb_don_erp` nối đơn.
  Nhiều tờ thì drill-down, không chọn phần tử đầu; dùng nguyên tắc duy nhất
  của `doi_soat_hddt_ra.chon_don_duy_nhat`. Chưa nối rõ thì báo cần kiểm.
  Không lấy mã APP làm số hóa đơn thuế.
- Báo cáo kỳ thu/chi riêng, chỉ đọc PLE, không sửa/adapter vào Payment Period
  lõi. Bộ lọc "Thu từ khách" / "Chi cho NCC" có giá trị nội bộ `thu` / `chi`,
  độc lập bản dịch Incoming/Outgoing. Không đảo SI thành PI theo nhãn dịch.
- Một ngày trả không diễn tả được nhiều đợt. Hiện ngày trả gần nhất, số
  đợt và bảng lịch sử từng phân bổ: PE/JE, ngày hạch toán thanh toán, ngày
  ngân hàng (nếu có), số tiền. Khoản bù trừ phải mang nhãn riêng.
- Không vá bằng loại toàn bộ SI/PI hay chỉ lấy Payment Entry: POS, return,
  JE, write-off và tiền trả trước được phân bổ sau cần phân loại theo
  chứng từ/PLE/GL thật, theo hợp đồng phân loại dưới đây.

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
5. Công cụ chỉ đề xuất bảng trước/sau để kế toán và anh Việt chốt; không có
   nút/API ghi hàng loạt ở bất kỳ đâu, không chạy trong migrate/patch.
   Chứng từ nguồn cũ đã ghi sổ hoặc đã có HĐĐT chỉ được liệt kê, không sửa/hủy.
   Với khoản đủ điều kiện được duyệt riêng, người dùng thực hiện từng dòng
   bằng Payment Reconciliation chuẩn; công cụ không tự tạo lần chi thứ hai.

## Giao diện
Mỗi thẻ tự ghi nguồn và ngày chốt, ví dụ "Nợ hóa đơn · PLE tại 30/09";
không chỉ dựa vào bộ lọc đầu màn. Excel ghi nguồn, ngày chốt và company ở
đầu mỗi sheet, phân biệt tiền gốc/tiền công ty.
Thứ tự: company/ngày chốt -> thẻ tổng có nguồn/ngày -> tìm mã/tên/số hóa đơn
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
- Codex là owner triển khai; Claude review, tái hiện finding. Review vòng 2
  đã chốt đợt A; phiên này chỉ sửa thiết kế, chưa nhận đã có code runtime.
- PR tài liệu không tăng APPVER/patch, không deploy. Kiểm diff/link và
  mâu thuẫn hướng dẫn; CI chạy tự động không chứng minh có chức năng mới.
  Thiếu nguồn cũ không cản sửa báo cáo nhưng cản chốt công nợ lịch sử.

## Snapshot dùng chung và thứ tự triển khai
- Đợt A: một hàm snapshot PLE/core as-of nhận company, ngày chốt, account,
  party/currency và các bộ lọc ở trên. Báo cáo mới, Excel và
  `mua_hang.cong_no_phai_tra` phải gọi cùng hàm; bỏ cách tự cộng outstanding
  hiện tại của PI trong đường báo cáo này. Ca hành vi gọi cả hai cửa với
  cùng bộ lọc và so tổng với Accounts Payable lõi; dò chuỗi là kiểm bổ sung.
- Nhóm dư tại ngày chốt theo voucher gốc của khoản còn dư: PI/SI là nợ hóa
  đơn; PE là trả/thu trước chưa phân bổ; JE là công nợ ngoài hóa đơn. Giữ
  return/credit và dấu, không biến khoản âm thành nợ dương bằng ABS.
  Payable dư Có là phải trả, dư Nợ là trả trước; Receivable dư Nợ là phải
  thu, dư Có là thu trước. Hiển thị `is_opening` riêng cho JE. Các loại
  khác chưa phân loại phải hiện ra để đối chiếu, không âm thầm bỏ.
- Đợt B: mã và số HĐĐT đã có giao diện trên main, có thể gộp A nếu phạm vi
  vừa đủ; chưa tự nhận A/B đã triển khai. Phải giữ hợp đồng tab Đang nợ /
  Tiền đã về của #380/#382, không tự trừ tiền chờ ghi sổ vào GL.
- Đợt C chờ kế toán xác nhận ngày chuyển sổ và bảng nguồn; chỉ đề xuất.
- PR code riêng đọc APPVER từ main ngay trước khi đặt, tăng số và thêm
  `dong_bo_cau_truc #vNNN`; không đặt cứng 542 vì main đã tiến tới v543.

## Phân loại kỳ thu/chi: một dòng PLE, đúng một nhóm
Bộ lọc: `delinked=0`, company đã chọn, ngày hạch toán trong kỳ, quyền xem;
`thu` là Customer/Receivable, `chi` là Supplier/Payable. Đọc metadata voucher
đã ghi sổ để phân loại; thiếu metadata trả "Chưa phân loại", không đoán.
Hàm thuần nhận dòng PLE và metadata. Thứ tự đầu tiên khớp thì dừng:

| Ưu tiên | Điều kiện | Nhóm / ca thuần bắt buộc |
|---|---|---|
| 1 | PI/SI không return và voucher_no = against_voucher_no | Phát sinh hóa đơn, không phải tiền thu/chi; SI POS tự tham chiếu cũng không tính lần nữa |
| 2 | PI/SI is_return=1 | Trả hàng / giảm trừ, giữ dấu |
| 3 | SI is_pos=1 còn lại sau 1/2 | Thu tại quầy; kiểm PLE phần thanh toán thực, không cộng lại doanh thu |
| 4 | PE; tài khoản nguồn paid_from khi Chi / đích paid_to khi Thu có account_type Bank/Cash | Tiền thực thu/chi; PE đối ứng khác là cấn trừ |
| 5 | JE is_opening=Yes | Số dư đầu kỳ, không tính tiền kỳ hoặc cấn trừ |
| 6 | JE không đầu kỳ | Exchange Gain Or Loss ưu tiên chênh tỷ giá; còn lại Bank/Cash là tiền thực, không có là cấn trừ/điều chỉnh |
| 7 | Còn lại / write-off / metadata thiếu | Chưa phân loại, hiện riêng |

Phải giữ dấu và tách hoàn/đảo, không lấy ABS mọi PLE. Một PE phân bổ nhiều
hóa đơn: cộng phần phân bổ từng hóa đơn và phần chưa phân bổ đúng một lần,
không lặp tổng PE trên mỗi dòng. JE hỗn hợp tiền và cấn trừ không được lấy
sự có mặt của một dòng Bank/Cash làm bằng chứng toàn bộ tiền của mọi party;
phải chứng minh phần tiền đối ứng, chưa tách được thì "Chưa phân loại".

Bảng bảy nhánh là đầu vào ca thuần trước khi code, không phải kết quả test.
Bench phải xác minh cách core tạo PLE POS/tự tham chiếu thực tế; nếu khác
hợp đồng thì báo lại bằng chứng, không bẻ fixture để ép đạt.

## Ca bổ sung từ review vòng 2
- JE đầu kỳ phải trả và đầu kỳ trả trước: chốt dấu, account, voucher,
  is_opening; không gộp vào dòng tiền trong kỳ.
- PE trả nhiều PI cùng NCC; hai PE của hai NCC cùng số tiền/ngày không lẫn
  party. Đề nghị "một PE hai NCC" không là fixture hợp lệ vì PE chuẩn có
  một party; JE nhiều party dùng để kiểm phân bổ chéo. Nhờ Claude xác nhận
  cách thay fixture này, không nới core để tạo một PE sai cấu trúc.
- JE cấn phải thu với phải trả: tách party_type/account, không biến thành
  tiền thực; JE hỗn hợp Bank/Cash + cấn trừ và JE tỷ giá có tài khoản tiền.
- Thanh toán sau ngày chốt không giảm snapshot cũ; tổng nợ hóa đơn bằng
  phần hóa đơn trong AP/AR lõi cùng bộ lọc, đối chiếu thêm tổng thuần gồm
  credit/JE để không so tổng khác phạm vi.
- Không gọi các helper ghi mã từ báo cáo (dò chuỗi bổ sung và ca chặn mọi
  DB write khi chạy báo cáo); party thiếu mã vẫn xem/xuất được "Chưa có mã".
- Nhiều tờ HĐĐT trên cùng đơn: drill-down đủ tờ, không chọn bản ghi đầu.

## Bằng chứng và bàn giao vòng này
Tám mục F1-F8 từ [Claude vòng 2](https://github.com/thevagabondpatisserie/vagabond/pull/392#issuecomment-5905851021)
đã đưa vào thiết kế. Đồng bộ main bằng merge giữ lịch sử nhánh đã công bố,
không force-push để rebase. Phiên bản core/live nêu trên có nguồn Claude;
không đưa số liệu đối tác thật vào repo. Claude cần rà SHA mới, đặc biệt
fixture PE nhiều NCC và JE hỗn hợp. Chưa merge/deploy, không sửa dữ liệu thật.
