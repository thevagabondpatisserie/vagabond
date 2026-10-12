# Issue 351 - một PR cho toàn bộ phân hệ báo cáo

## Quyết định ngày 12/10/2026

Anh Việt duyệt thiết kế bản 2 và yêu cầu **một PR duy nhất**. Các mốc dưới
đây là commit/checklist trong cùng nhánh `codex/351-he-bao-cao`, không phải
PR con. Codex triển khai; Claude review độc lập. Giữ Draft tới khi đủ phạm
vi và cổng phát hành. Ý tưởng AI trong issue cũ không thuộc đợt này.

Nền khởi đầu: `46f651ac5e3e27fa9661dfc4f29806fae95ae15e` (v588).
Không chiếm số phiên bản khi mới dựng Draft; tích hợp cuối phải tăng phiên
bản/patch trên main mới nhất và dựng lại bundle.

## Ràng buộc đã chốt

- Dùng nghiệp vụ, chứng từ, sổ và báo cáo lõi ERPNext trước. Không thêm
  DocType tùy tiện, hệ thanh toán/kế toán hay lớp tính chỉ tiêu song song.
- PrimeVue 4.5.5 và Chart.js cho giao diện; khóa phụ thuộc, đóng gói có thể
  tái lập, không bắt Frappe Cloud build thêm, không đụng Vue của storefront.
- Giá trị hóa đơn khác tiền thực thu. Thanh toán/phân bổ/công nợ đọc đúng
  nguồn lõi. Nháp hiện riêng, không cộng số chính hoặc đối chiếu GL.
- Chị Dung ghi sổ lương; báo cáo đọc sổ, không có màn nhập lương riêng.
- Quyền dữ liệu áp tại máy chủ, cả API, Excel, drilldown và cache. Giám đốc,
  kế toán xem tài chính; quản lý sản xuất xem chi phí/lãi gộp thuộc phạm vi
  sản xuất; cửa hàng/thu ngân xem doanh thu đúng điểm. Không lộ lương hay
  lãi công ty qua dữ liệu trả về cho người không có quyền.
- Ngưỡng NVL 30%/35%, hao hụt không lý do 2%/5% là cảnh báo, có cấu hình;
  không dùng để chặn thao tác nghiệp vụ.
- Không sửa chứng từ thật để làm báo cáo khớp. UI cũ giữ tới khi mẫu đạt.

## Checklist toàn bộ PR

### Mốc 1a - nền và mẫu (chưa nghiệm thu)

- [x] Claim issue, đồng bộ nền, lập checklist duy nhất.
- [x] Hàm nội bộ mẫu BC08 đọc `base_net_amount`, `stock_qty`, `stock_uom`
  lõi đã tính; giữ số âm phiếu trả, tách Nháp; sáu ca kiểm hành vi.
- [ ] Khóa dependency và dựng PrimeVue/Chart.js, tải riêng và cô lập CSS.
- [ ] Tổng quan và Cần theo dõi; bộ lọc, mobile, trạng thái tải/lỗi/rỗng.
- [ ] BC08 mới: cửa API có quyền/phạm vi công ty/điểm, bảng/thẻ/Excel/
  drilldown chung kết quả. BC08 thuộc bộ 17, không tính thành báo cáo 18.
- [ ] Đối chiếu chứng từ core trên bench, cùng bộ lọc cho mọi cách xem.
- [ ] Ảnh mẫu và nghiệm thu mốc 1a trước khi nhân rộng giao diện.

### Mốc 1b - hoàn tất đợt 1

- [ ] Chuyển 16 báo cáo còn lại: BC01-07, BC09-17; rà nhãn/nguồn từng báo
  cáo, đặc biệt BC04/15/16 không biến giá trị hóa đơn thành tiền thực thu.
- [ ] Top món doanh thu/lãi gộp; giá vốn thật, độ bao phủ và phần còn thiếu.
- [ ] Tỷ lệ NVL tháng, phân loại chuyển kho/trả/hủy/kiểm kê khỏi tiêu hao.
- [ ] Biến động giá mua, phân biệt đơn giá/% biến động/tác động thành tiền.

### Đợt 2 - phân tích vận hành

- [ ] Thực tế so định mức (AvT); ghi mốc BOM/giá và phạm vi đủ dữ liệu.
- [ ] Ma trận món; lãi theo kênh sau phí, tránh đếm phí hai lần.
- [ ] Kế hoạch sản xuất so thực tế; hao hụt theo lý do; tồn kho chuyên sâu.

### Đợt 3 - tài chính và sử dụng hằng ngày

- [ ] Tuổi nợ phải thu/phải trả theo ngày chốt, tái dùng báo cáo lõi.
- [ ] Bản đồ giờ cao điểm, khách quay lại, lương/doanh thu từ sổ.
- [ ] Bản tin sáng, lưu/chia sẻ bộ lọc theo quyền, nút đi báo cáo từ chứng từ.

### Năm điểm Claude yêu cầu và cổng chung

- [ ] Giá vốn: đối chiếu SLE đúng dòng SI hoặc DN; `update_stock=1` nhưng
  không có SLE phải là thiếu giá vốn, không phải lãi 100%. Kiểm combo thường
  và thêm tay, SI từ DN không đếm hai lần; không lẫn giá bình quân ước tính.
- [ ] Trả khác kỳ: kiểm bằng chứng từ thật ngày phiếu trả, doanh thu và giá
  vốn cùng tập; không coi sáu ca giả lập hiện tại là chứng minh sổ cái.
- [ ] Quyền: gọi API/Excel trực tiếp từng vai trò, đăng ký cửa mới trong
  `thu_cua_ngo.py`; thay người dùng/bộ lọc không rò cache.
- [ ] Đo thời gian một tháng/một quý; không quét SLE toàn lịch sử vô hạn.
- [ ] Nháp: số riêng, không lọt số đã ghi sổ hoặc đối chiếu sổ cái.
- [ ] Xác minh core SHA/site, ngày bật trừ kho trong Settings; trống là tắt.
- [ ] Lương: xác minh tài khoản và trung tâm chi phí. Chứng từ có Có 334
  chưa chứng minh mọi chân Nợ là lương; không cộng lại lương đã vào giá vốn.
- [ ] Local gate, CI/bench SHA cuối, review, mẫu mobile, phiên bản/patch,
  merge, deploy, migrate và kiểm live - ghi bằng chứng riêng từng bước.

## Code hiện tại và giới hạn

`bao_cao._bc_mon_thuan` là hàm riêng chưa nối API/UI. Đây là phần đầu của
mốc 1a, chưa phải một báo cáo sử dụng được. Caller tương lai phải cung cấp
tập hóa đơn được phép đọc, cùng công ty/tiền tệ, có `is_return` và
`base_grand_total`; `_hoa_don` cũ chưa đáp ứng hợp đồng này.

Đã đọc `accounts/report/item_wise_sales_register/item_wise_sales_register.py`
nhánh ERPNext version-16: core dùng `base_net_amount`, `stock_qty`,
`stock_uom`, `docstatus=1`. Đây là tham chiếu mã nguồn, **chưa xác minh SHA
core site**. Tùy chỉnh hiện tại chỉ nhóm dữ liệu core theo món/đơn vị, không
tự tính thuế, giảm giá hay giá vốn. Không lấy BC12 cũ làm chuẩn.

Sáu ca mới giả cửa đọc dòng, gọi hàm thật: giảm giá không trừ hai lần, trả
khác kỳ giữ âm, tách Nháp/hủy/tạm tính, rỗng không quét, đơn vị tồn, hơn 400
hóa đơn không cắt tổng. Chưa có bench, UI hoặc kết luận đủ phát hành.

Owner tiếp: Codex nối mốc 1a theo checklist; Claude review phần đã có trên
SHA được đăng ở PR. Mọi bổ sung tiếp tục đúng PR này.

## Bổ sung desktop 12/10: đưa sửa cloud lên GitHub

Đã lấy nguyên diff task_e_6accc73e59b0832e83221128c68e37a6
(commit cloud 4a97c37), tích hợp trên main 8161a4021 chứa #462.
Cửa đọc xin đủ trường trả hàng/Nháp và lọc công ty mặc định;
hàm mẫu nhận tham số chuẩn của báo cáo. Bảy ca BC08 đạt.
Đột biến bỏ trường trả/Nháp bị bắt 4 assertion; bỏ bộ lọc công ty
làm ca cửa đọc đỏ KeyError company. Chỉ đột biến trong tiến trình tạm.
Kết quả cổng tổng và SHA cuối ghi trên comment PR. Toàn phân hệ vẫn Draft,
chưa nối mẫu vào API/UI, chưa kiểm bench chứng từ thật; không merge/deploy.
